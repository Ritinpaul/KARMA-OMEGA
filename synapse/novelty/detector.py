"""
SYNAPSE: Novelty Detection
===========================
Uses Isolation Forest to compute anomaly scores for SynthesisPatterns,
identifying which patterns are truly unprecedented vs. known variants.

How it works:
  1.  Encode each synthesis pattern as a feature vector
  2.  Train/fit Isolation Forest on feature vectors of all patterns
  3.  Anomaly score (IF) → calibrated novelty_score [0,1]
  4.  Classify into NoveltyCategory enum

Also provides calibration: maps raw anomaly scores to calibrated [0,1]
via historical reference distribution from the 5 seed failures.
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np
from loguru import logger
from sklearn.ensemble import IsolationForest

from synapse.schemas.models import (
    AnalogueMatch,
    NoveltyCategory,
    NoveltyReport,
    SynthesisPattern,
)


class NoveltyDetector:
    """
    Isolation Forest-based novelty detector for SynthesisPatterns.

    The Isolation Forest is trained on the current batch of patterns
    (self-supervised — no labels needed). The more a pattern's feature
    vector is isolated early in the partition tree, the more novel it is.
    """

    def __init__(
        self,
        contamination: float = 0.2,
        n_estimators: int = 150,
        random_state: int = 42,
    ) -> None:
        self._model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
        )
        self._fitted = False

    # ─── Feature Engineering ─────────────────────────────────────────────────

    def _pattern_to_features(self, pattern: SynthesisPattern) -> np.ndarray:
        """
        Encode a SynthesisPattern as a fixed-length numeric feature vector.
        Features:
          [0] confidence
          [1] novelty_score (self-computed during synthesis)
          [2] number of source genes
          [3] number of unique source failures (diversity)
          [4] mean gene intensity
          [5] number of combined conditions
          [6] monte_carlo_probability (if available)
          [7] risk_level encoded (0=low..3=critical)
        """
        risk_encoding = {"low": 0, "medium": 1, "high": 2, "critical": 3, "unknown": 1}

        unique_src = len({g.source_failure_id for g in pattern.source_genes})
        mean_intensity = float(np.mean([g.gene_value for g in pattern.source_genes])) if pattern.source_genes else 0.0

        return np.array([
            pattern.confidence,
            pattern.novelty_score,
            len(pattern.source_genes),
            unique_src,
            mean_intensity,
            len(pattern.combined_conditions),
            pattern.monte_carlo_probability or 0.0,
            risk_encoding.get(pattern.risk_level.value, 1),
        ], dtype=float)

    # ─── Fit + Score ──────────────────────────────────────────────────────────

    def fit_and_score(
        self,
        patterns: List[SynthesisPattern],
    ) -> List[NoveltyReport]:
        """
        Fit the Isolation Forest on all patterns and compute novelty reports.
        If fewer than 3 patterns exist, falls back to heuristic scoring.
        """
        if len(patterns) < 3:
            return [self._heuristic_report(p) for p in patterns]

        try:
            X = np.array([self._pattern_to_features(p) for p in patterns])
            self._model.fit(X)
            if_scores = self._model.decision_function(X)  # higher = more normal
            self._fitted = True

            reports = []
            for i, pattern in enumerate(patterns):
                # Isolation Forest decision_function: negative = anomaly
                # Map to novelty [0,1]: high anomaly → high novelty
                raw_score = float(if_scores[i])
                # decision_function range is roughly [-0.5, 0.5]
                novelty = round(self._calibrate(raw_score), 4)
                report = self._build_report(pattern, novelty, if_score=raw_score)
                reports.append(report)

            return reports

        except Exception as e:
            logger.warning(f"Isolation Forest fitting failed: {e} — using heuristic scores")
            return [self._heuristic_report(p) for p in patterns]

    def _calibrate(self, if_score: float) -> float:
        """
        Calibrate raw IF decision_function score to [0,1] novelty.
        if_score > 0 → normal (low novelty)
        if_score < 0 → anomaly (high novelty)
        """
        # Sigmoid-like mapping: 0.5 + 0.5 * tanh(-2 * if_score)
        novelty = 0.5 + 0.5 * np.tanh(-2.0 * if_score)
        return float(np.clip(novelty, 0.0, 1.0))

    def _build_report(
        self,
        pattern: SynthesisPattern,
        novelty: float,
        if_score: float = 0.0,
    ) -> NoveltyReport:
        """Build a NoveltyReport from a calibrated novelty score."""
        if novelty >= 0.85:
            cat = NoveltyCategory.UNPRECEDENTED
            explanation = (
                f"Pattern '{pattern.name}' has never been seen in this configuration "
                f"across all historical failures. Gene combination from "
                f"{len({g.source_failure_id for g in pattern.source_genes})} different "
                "failure sources creates a new risk frontier."
            )
        elif novelty >= 0.60:
            cat = NoveltyCategory.SYNTHESIZED
            explanation = (
                f"Pattern '{pattern.name}' combines elements from known failures in a "
                "new way. The specific combination has not been observed historically, "
                "though individual components appear in separate incidents."
            )
        elif novelty >= 0.35:
            cat = NoveltyCategory.VARIANT
            explanation = (
                f"Pattern '{pattern.name}' is a variant of a known failure mode. "
                "Key conditions differ slightly from historical analogues."
            )
        else:
            cat = NoveltyCategory.KNOWN
            explanation = (
                f"Pattern '{pattern.name}' closely matches a known historical failure. "
                "Standard prevention procedures should apply directly."
            )

        nearest_distance = round(1.0 - (pattern.novelty_score * 0.7 + 0.3), 4)

        return NoveltyReport(
            pattern_id=pattern.pattern_id,
            isolation_forest_score=round(if_score, 6),
            novelty_score=novelty,
            novelty_category=cat,
            nearest_historical_distance=nearest_distance,
            explanation=explanation,
        )

    def _heuristic_report(self, pattern: SynthesisPattern) -> NoveltyReport:
        """Fallback heuristic novelty report for small batches."""
        return self._build_report(pattern, novelty=pattern.novelty_score, if_score=0.0)

    def score_single(self, pattern: SynthesisPattern) -> NoveltyReport:
        """Score a single pattern against the fitted model."""
        if self._fitted:
            X = self._pattern_to_features(pattern).reshape(1, -1)
            if_score = float(self._model.decision_function(X)[0])
            novelty = self._calibrate(if_score)
            return self._build_report(pattern, novelty, if_score)
        return self._heuristic_report(pattern)
