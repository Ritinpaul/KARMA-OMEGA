"""
SYNAPSE: Monte Carlo Stressor Simulation
==========================================
Estimates the probability of failure for each SynthesisPattern
via repeated Monte Carlo sampling from probability distributions
over the contributing stressor values.

Each stressor (humidity, thermal delta, foundation proximity, etc.)
is modelled as a parametric distribution calibrated against:
  1. Historical failure threshold data in GENE_THRESHOLDS
  2. Current project's measured condition values
  3. Gene intensity from the analogical retrieval

Output: P(failure) over {30, 90} day windows for each pattern.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

from synapse.schemas.models import ProjectConditions, SynthesisPattern


# ─── Stressor Thresholds (from historical failure data) ───────────────────────
# Each entry: {mean_failure_threshold, std_dev, distribution}

STRESSOR_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    "humidity": {
        "threshold_mean": 87.0,   # % — above this, cure retardation begins
        "threshold_std": 5.0,
        "unit": "%",
        "distribution": "normal",
    },
    "temperature": {
        "threshold_mean": 40.0,    # °C
        "threshold_std": 4.0,
        "unit": "°C",
        "distribution": "normal",
    },
    "thermal_delta": {
        "threshold_mean": 22.0,    # °C daily ΔT above which micro-cracks accumulate
        "threshold_std": 3.5,
        "unit": "°C",
        "distribution": "normal",
    },
    "scour_depth_factor": {
        "threshold_mean": 1.2,     # factor above design scour depth
        "threshold_std": 0.2,
        "unit": "factor",
        "distribution": "lognormal",
    },
    "storage_duration_months": {
        "threshold_mean": 3.0,     # months of outdoor exposure
        "threshold_std": 1.0,
        "unit": "months",
        "distribution": "lognormal",
    },
}

# Gene type → relevant stressor keys from STRESSOR_THRESHOLDS
GENE_TO_STRESSORS = {
    "humidity_sensitivity": ["humidity"],
    "thermal_cracking": ["thermal_delta", "temperature"],
    "foundation_scour": ["scour_depth_factor"],
    "premature_loading": ["humidity"],
    "chloride_corrosion": ["humidity"],
    "seismic_amplification": ["scour_depth_factor"],
    "construction_sequence": ["thermal_delta"],
    "inspection_gap": [],
    "design_error": [],
    "material_degradation": ["storage_duration_months"],
}


class MonteCarloSimulator:
    """
    Monte Carlo simulator for failure probability estimation.

    For each SynthesisPattern, samples N times from stressor distributions
    and counts how often conditions exceed failure thresholds.
    """

    def __init__(self, n_iterations: int = 1000, random_seed: int = 42) -> None:
        self.n_iterations = n_iterations
        self.rng = np.random.default_rng(random_seed)

    def simulate_pattern(
        self,
        pattern: SynthesisPattern,
        project: ProjectConditions,
        window_days: int = 30,
    ) -> float:
        """
        Estimate P(failure | pattern, project) over a time window.

        Args:
            pattern: The synthesis pattern to evaluate
            project: Current project conditions
            window_days: Time horizon for the estimate

        Returns:
            Probability of failure in [0, 1]
        """
        # Collect relevant stressors for this pattern's genes
        stressor_keys = set()
        for gene in pattern.source_genes:
            stressor_keys.update(GENE_TO_STRESSORS.get(gene.gene_type, []))

        if not stressor_keys:
            # No stator data — return baseline from pattern confidence
            return round(pattern.confidence * 0.6, 4)

        failure_count = 0

        for _ in range(self.n_iterations):
            any_threshold_exceeded = False

            for stressor_key in stressor_keys:
                stressor_cfg = STRESSOR_THRESHOLDS.get(stressor_key)
                if stressor_cfg is None:
                    continue

                # Get project's current value for this stressor
                project_value = self._get_project_stressor_value(
                    stressor_key, project
                )

                if project_value is None:
                    continue

                # Sample the failure threshold from its distribution
                threshold = self._sample_threshold(stressor_cfg)

                # Time-scaling: longer window = higher cumulative exceedance probability
                time_factor = min(window_days / 30, 3.0)
                effective_threshold = threshold / (1 + 0.1 * (time_factor - 1))

                if project_value >= effective_threshold:
                    any_threshold_exceeded = True
                    break

            if any_threshold_exceeded:
                failure_count += 1

        base_prob = failure_count / self.n_iterations

        # Adjust by pattern confidence and novelty (novel patterns → less certain)
        adjusted = base_prob * pattern.confidence * (1 - 0.2 * pattern.novelty_score)
        return round(min(max(adjusted, 0.01), 0.99), 4)

    def _get_project_stressor_value(
        self,
        stressor_key: str,
        project: ProjectConditions,
    ) -> Optional[float]:
        """Extract the project's current measured value for a stressor."""
        conditions = project.conditions

        # Direct key match
        for k, v in conditions.items():
            if stressor_key.lower() in k.lower().replace(" ", "_"):
                try:
                    return float(str(v).replace("%", "").replace("°C", "").strip())
                except (ValueError, TypeError):
                    pass

        # Specific mappings
        mappings = {
            "humidity": ["humidity", "relative_humidity", "rh"],
            "temperature": ["temperature", "ambient_temp", "temp"],
            "thermal_delta": ["thermal_delta", "delta_t", "temp_cycling", "thermal_cycling"],
            "scour_depth_factor": ["scour", "foundation_proximity", "water_table"],
            "storage_duration_months": ["storage_duration", "storage_months", "storage"],
        }

        for alt_key in mappings.get(stressor_key, []):
            for k, v in conditions.items():
                if alt_key in k.lower():
                    try:
                        raw = str(v).split(":")[1] if ":" in str(v) else str(v)
                        return float(raw.replace("%", "").replace("°C", "").strip())
                    except (ValueError, TypeError, IndexError):
                        pass

        return None

    def _sample_threshold(self, stressor_cfg: Dict[str, Any]) -> float:
        """Sample a failure threshold from its parametric distribution."""
        dist = stressor_cfg.get("distribution", "normal")
        mean = stressor_cfg["threshold_mean"]
        std = stressor_cfg["threshold_std"]

        if dist == "lognormal":
            # Convert mean/std to log-space params
            sigma = np.sqrt(np.log(1 + (std / mean) ** 2))
            mu = np.log(mean) - sigma ** 2 / 2
            return float(self.rng.lognormal(mu, sigma))
        else:
            return float(self.rng.normal(mean, std))

    def run_all(
        self,
        patterns: List[SynthesisPattern],
        project: ProjectConditions,
        iterations: int = 1000,
    ) -> List[SynthesisPattern]:
        """
        Run Monte Carlo for all patterns, filling in their probabilities.
        Returns patterns sorted by 30-day failure probability (descending).
        """
        self.n_iterations = iterations

        for pattern in patterns:
            p30 = self.simulate_pattern(pattern, project, window_days=30)
            p90 = self.simulate_pattern(pattern, project, window_days=90)
            # Store on the pattern
            pattern.monte_carlo_probability = p30
            # We'll attach 90-day in the risk alert layer
            pattern.__dict__["_p90"] = p90

        return sorted(
            patterns,
            key=lambda p: p.monte_carlo_probability or 0,
            reverse=True,
        )
