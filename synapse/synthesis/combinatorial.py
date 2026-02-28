"""
SYNAPSE: Combinatorial Synthesis Engine
=========================================
The core innovation of KARMA-OMEGA.

Takes failure genes from multiple historical analogues and synthesises
novel failure patterns by combining them — predicting failure modes
that have never occurred in L&T's history.

Algorithm:
  1.  Group genes by type across all analogues
  2.  Identify which gene-types are co-present in the current project
  3.  Generate all valid combinations (constraint-satisfied)
  4.  For each combination, build a SynthesisPattern
  5.  Run Monte Carlo simulation to estimate P(failure)

This is what enables "Compound Hydro-Thermal-Foundation Failure" alerts.
"""

from __future__ import annotations

import itertools
import uuid
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

from synapse.schemas.models import (
    AnalogueMatch,
    FailureGene,
    NoveltyCategory,
    ProjectConditions,
    RiskLevel,
    SynthesisPattern,
)


# ─── Pattern Templates ────────────────────────────────────────────────────────
# Defines which gene-type combinations form meaningful failure patterns.
# Each template specifies: required genes + predicted failure mode + name template.

SYNTHESIS_TEMPLATES = [
    {
        "id": "compound-hydro-thermal-foundation",
        "name": "Compound Hydro-Thermal-Foundation Failure",
        "required_genes": ["humidity_sensitivity", "thermal_cracking", "foundation_scour"],
        "predicted_mode": "Multi-mechanism progressive collapse — humidity-delayed strength + thermal cracking + foundation loss",
        "base_confidence": 0.73,
        "base_severity": RiskLevel.CRITICAL,
        "description": (
            "Simultaneous high humidity (reducing concrete strength gain), "
            "significant thermal cycling (inducing micro-cracks), and "
            "proximity to water table / scour risk combine into a novel "
            "multi-barrier failure mode with no historical precedent in this configuration."
        ),
    },
    {
        "id": "thermal-prestress-sequence",
        "name": "Thermal Prestress Loss + Sequence Error Cascade",
        "required_genes": ["thermal_cracking", "construction_sequence", "premature_loading"],
        "predicted_mode": "Brittle fracture of prestressed element during critical construction operation",
        "base_confidence": 0.68,
        "base_severity": RiskLevel.CRITICAL,
        "description": (
            "Thermal micro-cracking from extended exposure + construction sequence "
            "pressure leading to eccentricity during critical operation, combined with "
            "undetected prestress losses. Creates brittle failure without ductile warning."
        ),
    },
    {
        "id": "chloride-humidity-aging",
        "name": "Accelerated Chloride-Humidity Corrosion",
        "required_genes": ["chloride_corrosion", "humidity_sensitivity", "material_degradation"],
        "predicted_mode": "Rapid steel reinforcement corrosion and concrete delamination",
        "base_confidence": 0.61,
        "base_severity": RiskLevel.HIGH,
        "description": (
            "High humidity environment near coastal chloride sources accelerates "
            "chloride ingress beyond designed service life. Combined with aging "
            "concrete, creates accelerated corrosion beyond code assumptions."
        ),
    },
    {
        "id": "inspection-gap-design-error",
        "name": "Hidden Failure — Inspection Gap + Latent Design Defect",
        "required_genes": ["inspection_gap", "design_error"],
        "predicted_mode": "Sudden structural failure from undetected latent defect crossing stress threshold",
        "base_confidence": 0.55,
        "base_severity": RiskLevel.HIGH,
        "description": (
            "Latent design defect (stress concentration, geometric inadequacy) "
            "remains undetected due to inadequate inspection. Under cumulative loading, "
            "the defect crosses its critical stress threshold without warning."
        ),
    },
    {
        "id": "seismic-foundation-scour",
        "name": "Seismic + Foundation Scour Compounding",
        "required_genes": ["seismic_amplification", "foundation_scour"],
        "predicted_mode": "Liquefaction-enhanced bearing fail under seismic excitation",
        "base_confidence": 0.59,
        "base_severity": RiskLevel.CRITICAL,
        "description": (
            "Weakened foundation from hydrodynamic scour reduces seismic resistance. "
            "A moderate seismic event (M5+) triggers bearing failure at load levels "
            "well below design seismic demand."
        ),
    },
    {
        "id": "humidity-premature-loading",
        "name": "Humidity-Induced Premature Strength Loss",
        "required_genes": ["humidity_sensitivity", "premature_loading"],
        "predicted_mode": "Shear or flexural failure from insufficient concrete strength at time of loading",
        "base_confidence": 0.82,
        "base_severity": RiskLevel.CRITICAL,
        "description": (
            "High ambient humidity retards cement hydration, delaying strength gain. "
            "If construction schedule pressure leads to premature loading before "
            "minimum design strength is reached, structural failure is highly probable."
        ),
    },
]


class CombinatorialSynthesizer:
    """
    Synthesises novel failure patterns by combining failure genes.

    The synthesizer:
      1. Takes all extracted genes per analogue
      2. Pools them across all analogues
      3. Matches against predefined synthesis templates
      4. Generates SynthesisPattern objects for each match
      5. Runs Monte Carlo to estimate probabilistic failure risk
    """

    def synthesize(
        self,
        gene_pool: Dict[str, List[FailureGene]],
        project: ProjectConditions,
        include_known: bool = True,
    ) -> List[SynthesisPattern]:
        """
        Main synthesis method.

        Args:
            gene_pool: {failure_id: [FailureGene]} from all analogues
            project: current project conditions
            include_known: also return known (non-novel) patterns

        Returns:
            List of SynthesisPattern sorted by confidence (desc)
        """
        # Flatten all genes with max intensity per type
        active_genes: Dict[str, FailureGene] = {}
        for failure_id, genes in gene_pool.items():
            for gene in genes:
                existing = active_genes.get(gene.gene_type)
                if existing is None or gene.gene_value > existing.gene_value:
                    active_genes[gene.gene_type] = gene

        active_types = set(active_genes.keys())
        patterns: List[SynthesisPattern] = []

        for template in SYNTHESIS_TEMPLATES:
            required = set(template["required_genes"])
            matched = required & active_types

            if not matched:
                continue

            coverage = len(matched) / len(required)
            if coverage < 0.5:
                continue

            # Collect source genes for this pattern
            source_genes = [
                active_genes[gene_type]
                for gene_type in template["required_genes"]
                if gene_type in active_genes
            ]

            # Adjust confidence by coverage and gene values
            avg_gene_value = np.mean([g.gene_value for g in source_genes]) if source_genes else 0.5
            confidence = round(
                template["base_confidence"] * coverage * (0.5 + avg_gene_value * 0.5),
                3,
            )

            # Combined conditions from all source genes
            combined_conditions = list({
                cond
                for g in source_genes
                for cond in g.conditions
            })

            # Novelty: full template match = more novel; partial = variant
            if coverage >= 1.0:
                novelty_score = self._compute_novelty_score(source_genes, active_genes)
                novelty_cat = (
                    NoveltyCategory.UNPRECEDENTED
                    if novelty_score > 0.75
                    else NoveltyCategory.SYNTHESIZED
                )
            else:
                novelty_score = round(coverage * 0.6, 3)
                novelty_cat = NoveltyCategory.VARIANT

            if not include_known and novelty_cat == NoveltyCategory.KNOWN:
                continue

            patterns.append(
                SynthesisPattern(
                    pattern_id=f"{template['id']}-{str(uuid.uuid4())[:8]}",
                    name=template["name"],
                    description=template["description"],
                    source_genes=source_genes,
                    combined_conditions=combined_conditions,
                    predicted_failure_mode=template["predicted_mode"],
                    confidence=confidence,
                    novelty_score=novelty_score,
                    novelty_category=novelty_cat,
                    risk_level=template["base_severity"],
                    monte_carlo_probability=None,  # filled by MonteCarloSimulator
                )
            )

        # Sort by confidence descending
        patterns.sort(key=lambda p: p.confidence, reverse=True)
        return patterns

    def _compute_novelty_score(
        self,
        source_genes: List[FailureGene],
        all_active_genes: Dict[str, FailureGene],
    ) -> float:
        """
        Novelty = how unprecedented the combination is.
        Cross-source genes (from DIFFERENT historical failures) = more novel.
        """
        unique_sources = {g.source_failure_id for g in source_genes}
        source_diversity = len(unique_sources) / max(len(source_genes), 1)

        avg_intensity = np.mean([g.gene_value for g in source_genes])
        gene_count_bonus = min(len(all_active_genes) / 10, 0.3)

        novelty = round(
            source_diversity * 0.6 + avg_intensity * 0.3 + gene_count_bonus * 0.1,
            4,
        )
        return min(novelty, 1.0)
