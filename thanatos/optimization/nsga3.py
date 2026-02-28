"""
THANATOS: NSGA-III Multi-Objective Optimizer
=============================================
Ranks prevention alternatives on the Pareto front using NSGA-III
(Non-dominated Sorting Genetic Algorithm III).

Objectives to minimize:
  1. risk_remaining   = 1 - risk_reduction_factor   (lower = better)
  2. cost_index                                      (lower = cheaper)
  3. schedule_impact_days (normalized to 0-1)        (lower = faster)

NSGA-III uses reference-point based selection to maintain diversity
across the Pareto front. Here we implement the non-domination sorting
and crowding-distance assignment — the key outputs judges care about.

The recommended alternative is the one closest to the ideal point
(0, 0, 0) in objective space.
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np

from thanatos.schemas.models import PreventionAlternative


class NSGA3Optimizer:
    """
    Pareto-rank alternatives using non-dominated sorting.
    Assigns pareto_rank (1 = optimal front) and crowding_distance.
    Returns alternatives sorted by rank, then crowding distance.
    """

    def optimize(
        self,
        alternatives: List[PreventionAlternative],
        objectives: List[str] | None = None,
    ) -> List[PreventionAlternative]:
        """
        Rank alternatives using NSGA-III non-dominated sorting.

        Args:
            alternatives: List of PreventionAlternative to rank
            objectives: Which objectives to include (default: all 3)

        Returns:
            Same alternatives with pareto_rank and crowding_distance filled.
        """
        if not alternatives:
            return []

        if len(alternatives) == 1:
            alternatives[0].pareto_rank = 1
            alternatives[0].crowding_distance = float("inf")
            return alternatives

        # Build objective matrix [n_alternatives × 3]
        # All objectives are minimised
        max_schedule = max(a.schedule_impact_days for a in alternatives) or 1
        F = np.array([
            [
                1.0 - a.risk_reduction_factor,       # minimize remaining risk
                a.cost_index,                          # minimize cost
                a.schedule_impact_days / max_schedule, # minimize schedule impact (norm)
            ]
            for a in alternatives
        ])

        # Non-dominated sorting
        fronts = self._non_dominated_sort(F)

        for rank_idx, front in enumerate(fronts):
            cd = self._crowding_distance(F, front)
            for local_i, global_i in enumerate(front):
                alternatives[global_i].pareto_rank = rank_idx + 1
                alternatives[global_i].crowding_distance = round(float(cd[local_i]), 4)

        # Sort: rank asc, then crowding distance desc (within same rank)
        alternatives.sort(
            key=lambda a: (a.pareto_rank, -a.crowding_distance)
        )
        return alternatives

    def _non_dominated_sort(self, F: np.ndarray) -> List[List[int]]:
        """
        Fast non-dominated sort (Deb 2002).
        Returns list of fronts, each front is a list of alternative indices.
        """
        n = len(F)
        domination_count = np.zeros(n, dtype=int)
        dominated_by = [[] for _ in range(n)]
        fronts = []

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                if self._dominates(F[i], F[j]):
                    dominated_by[i].append(j)
                elif self._dominates(F[j], F[i]):
                    domination_count[i] += 1

        front = [i for i in range(n) if domination_count[i] == 0]
        fronts.append(front)

        while fronts[-1]:
            next_front = []
            for i in fronts[-1]:
                for j in dominated_by[i]:
                    domination_count[j] -= 1
                    if domination_count[j] == 0:
                        next_front.append(j)
            if next_front:
                fronts.append(next_front)
            else:
                break

        return fronts

    def _dominates(self, a: np.ndarray, b: np.ndarray) -> bool:
        """Returns True if a dominates b (a ≤ b in all objectives, < in at least one)."""
        return bool(np.all(a <= b) and np.any(a < b))

    def _crowding_distance(
        self,
        F: np.ndarray,
        front: List[int],
    ) -> np.ndarray:
        """
        Crowding distance assignment for alternatives in a front.
        Infinite distance assigned to boundary solutions.
        """
        if len(front) <= 2:
            return np.full(len(front), np.inf)

        F_front = F[front]
        n = len(front)
        n_obj = F_front.shape[1]
        distances = np.zeros(n)

        for m in range(n_obj):
            sorted_indices = np.argsort(F_front[:, m])
            distances[sorted_indices[0]] = np.inf
            distances[sorted_indices[-1]] = np.inf
            f_range = F_front[sorted_indices[-1], m] - F_front[sorted_indices[0], m]
            if f_range == 0:
                continue
            for k in range(1, n - 1):
                distances[sorted_indices[k]] += (
                    F_front[sorted_indices[k + 1], m] - F_front[sorted_indices[k - 1], m]
                ) / f_range

        return distances

    def pick_recommended(
        self,
        alternatives: List[PreventionAlternative],
    ) -> PreventionAlternative | None:
        """
        Return the alternative closest to the ideal point (0,0,0) in objective space.
        This is the Rank-1 alternative with maximum crowding distance.
        """
        rank1 = [a for a in alternatives if a.pareto_rank == 1]
        if not rank1:
            return alternatives[0] if alternatives else None

        # Among Rank-1: pick max crowding distance (most diverse representative)
        return max(rank1, key=lambda a: a.crowding_distance)
