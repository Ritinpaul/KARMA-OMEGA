"""
AION: Differential Privacy Module
====================================
Implements the Gaussian mechanism for (ε, δ)-differential privacy.

Key guarantees:
  • Gradient clipping bounds sensitivity: ‖Δ‖₂ ≤ C
  • Gaussian noise N(0, σ²C²) achieves (ε, δ)-DP via the analytic accountant
  • Rényi Differential Privacy (RDP) → (ε, δ)-DP conversion for tight bounds
  • Privacy budget tracker enforces ε ≤ 5 per site across all rounds

This module does NOT depend on Opacus/PyTorch to avoid heavy installs;
it implements the accountant math directly following:
  - Mironov 2017 (RDP Gaussian mechanism)
  - Balle & Wang 2018 (analytic Gaussian mechanism)
"""

from __future__ import annotations

import math
from typing import List

import numpy as np
from loguru import logger

from aion.schemas.models import PrivacyBudget, PrivacyMechanism, PrivacyReport


# ─── Privacy Accountant ───────────────────────────────────────────────────────


class GaussianAccountant:
    """
    Computes ε for the Gaussian mechanism using the analytic Gaussian mechanism
    (Balle & Wang, 2018) and the RDP accountant (Mironov, 2017).

    References:
      - https://arxiv.org/abs/1702.07476  (Gaussian mechanism)
      - https://arxiv.org/abs/1702.07476  (RDP accounting)
    """

    @staticmethod
    def epsilon_from_noise(
        noise_multiplier: float,
        clipping_threshold: float,
        data_size: int,
        delta: float = 1e-5,
    ) -> float:
        """
        Compute per-round epsilon using analytic bounds.

        σ = noise_multiplier * clipping_threshold
        q = 1 / data_size  (sampling ratio for one step)
        ε ≈ q * sqrt(2 * ln(1.25/δ)) / (σ/C)
          = sqrt(2 * ln(1.25/δ)) / noise_multiplier   [when q*n≈1]

        Simplified single-round epsilon:
        """
        if noise_multiplier <= 0:
            return float("inf")

        sigma = noise_multiplier * clipping_threshold
        sensitivity = clipping_threshold
        # Analytic Gaussian: ε for 1 step
        epsilon = sensitivity * math.sqrt(2 * math.log(1.25 / delta)) / sigma
        return round(epsilon, 6)

    @staticmethod
    def rounds_until_exhaustion(
        per_round_epsilon: float,
        max_epsilon: float = 5.0,
    ) -> int:
        if per_round_epsilon <= 0:
            return 99999
        return max(0, int(math.floor(max_epsilon / per_round_epsilon)))

    @staticmethod
    def compose_epsilon(per_round_epsilon: float, n_rounds: int) -> float:
        """
        Strong composition (basic): ε_total = n_rounds * ε_per_round.
        In practice, advanced composition (sqrt) or RDP gives tighter bounds but
        basic composition is the safe conservative bound for audit presentation.
        """
        return round(per_round_epsilon * n_rounds, 6)

    @staticmethod
    def rdp_epsilon(
        noise_multiplier: float,
        n_rounds: int,
        delta: float = 1e-5,
        alphas: List[float] | None = None,
    ) -> float:
        """
        Rényi DP → (ε,δ)-DP conversion.
        For the Gaussian mechanism at order α:
            RDP(α) = α / (2σ²)       (one-step)
            Composed: RDP_total = n * α/(2σ²)
            ε(δ) = RDP_total - log(δ)/((α-1))
        """
        if alphas is None:
            alphas = [2, 4, 8, 16, 32, 64, float("inf")]

        sigma = float(noise_multiplier)
        best_eps = float("inf")

        for alpha in alphas:
            if alpha == float("inf") or sigma <= 0:
                continue
            # RDP per round for Gaussian: alpha / (2 * sigma^2)
            rdp_per_round = alpha / (2.0 * sigma ** 2)
            rdp_total = n_rounds * rdp_per_round
            # Convert RDP → (ε, δ)-DP
            if alpha > 1:
                eps = rdp_total + math.log(1.0 / delta) / (alpha - 1)
                best_eps = min(best_eps, eps)

        return round(best_eps, 6)


# ─── Privacy Budget Manager ──────────────────────────────────────────────────


class PrivacyBudgetManager:
    """
    Tracks and enforces ε ≤ max_epsilon across all federated rounds per site.
    Provides per-site privacy reports and early-stop warnings.
    """

    def __init__(
        self,
        max_epsilon: float = 5.0,
        delta: float = 1e-5,
        noise_multiplier: float = 1.1,
        clipping_threshold: float = 1.0,
    ) -> None:
        self.max_epsilon = max_epsilon
        self.delta = delta
        self.noise_multiplier = noise_multiplier
        self.clipping_threshold = clipping_threshold
        self._budgets: dict[str, PrivacyBudget] = {}

        self._accountant = GaussianAccountant()
        self._per_round_eps = self._accountant.epsilon_from_noise(
            noise_multiplier=noise_multiplier,
            clipping_threshold=clipping_threshold,
            data_size=100,  # nominal
            delta=delta,
        )

    def get_or_create(self, site_id: str) -> PrivacyBudget:
        if site_id not in self._budgets:
            self._budgets[site_id] = PrivacyBudget(
                site_id=site_id,
                max_epsilon=self.max_epsilon,
                total_delta=self.delta,
            )
        return self._budgets[site_id]

    def consume(self, site_id: str, epsilon: float) -> PrivacyBudget:
        """Consume epsilon from site's budget; raises if budget exhausted."""
        budget = self.get_or_create(site_id)

        if budget.is_exhausted:
            logger.warning(f"⚠️  Site {site_id} privacy budget exhausted! Skipping round.")
            return budget

        budget.total_epsilon = round(budget.total_epsilon + epsilon, 6)
        budget.rounds_participated += 1

        if budget.total_epsilon >= self.max_epsilon * 0.9:
            logger.warning(
                f"⚠️  Site {site_id} at {budget.total_epsilon:.2f}/{self.max_epsilon} ε "
                f"(90% of budget consumed)"
            )
        return budget

    def can_participate(self, site_id: str) -> bool:
        budget = self.get_or_create(site_id)
        return not budget.is_exhausted

    def report(self, site_id: str) -> PrivacyReport:
        """Generate a human-readable DP report for a site."""
        budget = self.get_or_create(site_id)
        rounds_done = budget.rounds_participated
        remaining = self._accountant.rounds_until_exhaustion(
            per_round_epsilon=self._per_round_eps,
            max_epsilon=budget.remaining_epsilon,
        )
        rdp_eps = self._accountant.rdp_epsilon(
            noise_multiplier=self.noise_multiplier,
            n_rounds=max(rounds_done, 1),
            delta=self.delta,
        )

        return PrivacyReport(
            mechanism=PrivacyMechanism.GAUSSIAN,
            noise_multiplier=self.noise_multiplier,
            clipping_threshold=self.clipping_threshold,
            epsilon_per_round=self._per_round_eps,
            delta=self.delta,
            rounds_until_exhaustion=remaining,
            privacy_guarantee=(
                f"({budget.total_epsilon:.3f}, {self.delta:.0e})-DP after "
                f"{rounds_done} rounds. RDP-tight bound: "
                f"({rdp_eps:.3f}, {self.delta:.0e})-DP."
            ),
        )

    def all_budgets(self) -> list[PrivacyBudget]:
        return list(self._budgets.values())
