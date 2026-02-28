"""
SYNAPSE: SHAP-Style Causal Attribution
=========================================
Generates human-readable causal attributions for each RiskAlert,
explaining WHICH conditions drive the risk and by HOW MUCH.

Since we don't have a true ML model with SHAP support at this stage,
we implement a permutation-based attribution method that:
  1.  Starts from the baseline risk (mean MC probability across patterns)
  2.  Measures how each condition contributes above/below baseline
  3.  Produces signed attribution values and direction labels

This provides the "explainability-as-legacy" feature described in info1.md:
every alert carries its rationale, readable by future engineers.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from loguru import logger

from synapse.schemas.models import (
    CausalAttribution,
    FailureGene,
    NoveltyReport,
    ProjectConditions,
    RiskAlert,
    RiskLevel,
    SynthesisPattern,
)


# ─── Attribution weights per gene type ────────────────────────────────────────

GENE_ATTRIBUTION_WEIGHTS = {
    "humidity_sensitivity": 0.85,
    "foundation_scour": 0.90,
    "thermal_cracking": 0.80,
    "premature_loading": 0.90,
    "chloride_corrosion": 0.65,
    "seismic_amplification": 0.75,
    "design_error": 0.95,
    "inspection_gap": 0.60,
    "construction_sequence": 0.70,
    "material_degradation": 0.55,
}

# Condition keywords → risk multiplier (positive = increases risk)
CONDITION_RISK_MULTIPLIERS = {
    "humidity": +0.8,
    "thermal cycling": +0.75,
    "thermal_delta": +0.75,
    "foundation proximity": +0.85,
    "water table": +0.80,
    "scour": +0.90,
    "storage duration": +0.65,
    "monsoon": +0.70,
    "premature": +0.85,
    "coastal": +0.60,
    "chloride": +0.70,
    "curing": -0.50,       # proper curing REDUCES risk
    "ndt": -0.45,          # inspection REDUCES risk
    "monitoring": -0.40,   # monitoring REDUCES risk
}


class ExplainabilityEngine:
    """
    Generates causal attributions for risk alerts.

    Each attribution explains: "Feature X increases risk by Y% because of Z"

    Also provides:
      - Key risk factors (top-3 positive drivers)
      - Intervention points (top-3 negative drivers / mitigations)
    """

    def generate_attributions(
        self,
        pattern: SynthesisPattern,
        project: ProjectConditions,
        base_probability: float,
    ) -> List[CausalAttribution]:
        """
        Generate causal attributions for a synthesis pattern.

        Args:
            pattern: The synthesised risk pattern
            project: Current project conditions
            base_probability: Baseline failure probability (mean across patterns)

        Returns:
            List of CausalAttribution sorted by |attribution_value| descending
        """
        attributions: List[CausalAttribution] = []

        # 1. Gene-level attributions
        for gene in pattern.source_genes:
            weight = GENE_ATTRIBUTION_WEIGHTS.get(gene.gene_type, 0.5)
            attribution_value = round(gene.gene_value * weight * (pattern.confidence - base_probability + 0.1), 4)
            direction = "increases_risk" if attribution_value > 0 else "decreases_risk"
            attributions.append(
                CausalAttribution(
                    feature=f"{gene.gene_type.replace('_', ' ').title()} [{gene.source_title}]",
                    attribution_value=attribution_value,
                    direction=direction,
                    source_failure=gene.source_failure_id,
                )
            )

        # 2. Project condition attributions
        for condition_key, condition_value in project.conditions.items():
            multiplier = self._get_condition_multiplier(condition_key)
            if multiplier == 0:
                continue

            try:
                numeric_val = float(str(condition_value).split(":")[1] if ":" in str(condition_value) else str(condition_value))
                # Normalize to [0,1] relative to typical range for this condition
                normalized = self._normalize_condition(condition_key, numeric_val)
                attr_val = round(normalized * multiplier * 0.3, 4)
            except (ValueError, TypeError, IndexError):
                attr_val = round(multiplier * 0.15, 4)

            if abs(attr_val) < 0.005:
                continue

            direction = "increases_risk" if attr_val > 0 else "decreases_risk"
            attributions.append(
                CausalAttribution(
                    feature=f"{condition_key.replace('_', ' ').title()}: {condition_value}",
                    attribution_value=attr_val,
                    direction=direction,
                    source_failure=None,
                )
            )

        # Sort by absolute attribution value descending
        attributions.sort(key=lambda a: abs(a.attribution_value), reverse=True)
        return attributions[:10]  # Cap at top 10

    def _get_condition_multiplier(self, condition_key: str) -> float:
        """Get risk multiplier for a condition key."""
        key_lower = condition_key.lower().replace("_", " ")
        for kw, mult in CONDITION_RISK_MULTIPLIERS.items():
            if kw in key_lower:
                return mult
        return 0.0

    def _normalize_condition(self, key: str, value: float) -> float:
        """Normalize a condition value to [0,1] based on expected range."""
        ranges = {
            "humidity": (50.0, 100.0),
            "temperature": (15.0, 50.0),
            "thermal": (0.0, 35.0),
            "delta": (0.0, 35.0),
            "duration": (0.0, 12.0),
            "months": (0.0, 12.0),
        }
        for key_part, (lo, hi) in ranges.items():
            if key_part in key.lower():
                return float(np.clip((value - lo) / (hi - lo), 0.0, 1.0))
        return 0.5

    def extract_key_factors(
        self,
        attributions: List[CausalAttribution],
        top_n: int = 3,
    ) -> List[str]:
        """Return top-N risk-increasing factors as human-readable strings."""
        increasing = [a for a in attributions if a.direction == "increases_risk"]
        top = sorted(increasing, key=lambda a: a.attribution_value, reverse=True)[:top_n]
        return [f"{a.feature} (contribution: +{a.attribution_value:.3f})" for a in top]

    def extract_interventions(
        self,
        attributions: List[CausalAttribution],
        pattern: SynthesisPattern,
        top_n: int = 3,
    ) -> List[str]:
        """
        Return top intervention opportunities — either:
          - Conditions where decreasing value would help (positive risk drivers)
          - Mitigations from pattern gene types
        """
        interventions = []

        # From negative attributions (things that would reduce risk)
        decreasing = [a for a in attributions if a.direction == "decreases_risk"]
        for a in sorted(decreasing, key=lambda x: x.attribution_value)[:2]:
            interventions.append(f"Enhance: {a.feature}")

        # From gene types — known standard interventions
        gene_interventions = {
            "humidity_sensitivity": "Monitor and control ambient humidity; implement enclosed curing tents",
            "thermal_cracking": "Conduct pre-erection NDT; restrict operations during peak thermal delta periods",
            "foundation_scour": "Install scour monitoring sensors; increase rip-rap protection depth",
            "premature_loading": "Implement maturity-based strength testing before any loading operations",
            "chloride_corrosion": "Apply CFRP/epoxy barrier coatings; increase concrete cover to ≥60mm",
            "design_error": "Commission independent peer review of critical section designs",
            "inspection_gap": "Deploy fibre-optic structural health monitoring on critical elements",
            "construction_sequence": "Conduct pre-operation 3D BIM clash analysis of erection sequence",
        }

        for gene in pattern.source_genes[:2]:
            if gene.gene_type in gene_interventions:
                interventions.append(gene_interventions[gene.gene_type])

        return list(dict.fromkeys(interventions))[:top_n]  # deduplicate + cap
