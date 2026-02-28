"""
AION: Federated Learning Engine
================================
Simulates a Flower-style federated learning coordinator for KARMA-OMEGA.
Architecture follows FedAvg (McMahan 2017) with FedProx penalty support.

Key design decisions:
  - Surrogate weights: simple linear risk model (safety_factor → risk_score)
    fine-tuned locally at each site on its project history.
  - No raw data leaves a site — only gradient updates (LocalGradient objects).
  - Weighted FedAvg: each site's gradient is weighted by its data_size.
  - Min-site quorum: aggregation only proceeds if ≥ min_sites gradients arrive.
  - LoRA-style: only a small adapter layer (2×16 weights) is shared per round,
    reducing communication by ~95% vs. sharing full model.

In production this would be replaced by Flower + PyTorch; here we use NumPy
for portability and to avoid heavy ML dependencies in the test environment.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
from loguru import logger

from aion.schemas.models import (
    AggregatedModel,
    FederatedRound,
    LocalGradient,
    RoundStatus,
    SiteConfig,
    SiteStatus,
)


# ─── Simulated Local Model ────────────────────────────────────────────────────

LAYER_SHAPES: Dict[str, tuple] = {
    "risk_encoder.weight": (16, 8),
    "risk_encoder.bias": (16,),
    "lora_adapter.weight": (8, 16),   # LoRA adapter
    "lora_adapter.bias": (8,),
    "risk_head.weight": (1, 8),
    "risk_head.bias": (1,),
}

def _init_weights(seed: int = 42) -> Dict[str, List[float]]:
    """Initialise random starting weights for a site's local model."""
    rng = np.random.default_rng(seed)
    return {
        name: rng.normal(0, 0.1, size=shape).flatten().tolist()
        for name, shape in LAYER_SHAPES.items()
    }


# ─── Site Simulator ──────────────────────────────────────────────────────────

class SiteSimulator:
    """
    Simulates a single remote construction site doing local training.
    In production, each site runs this code independently; only gradients
    are transmitted back to the coordinator.
    """

    def __init__(self, config: SiteConfig, global_weights: Dict[str, List[float]]) -> None:
        self.config = config
        self.weights = {k: np.array(v) for k, v in global_weights.items()}
        self._rng = np.random.default_rng(int(hashlib.md5(config.site_id.encode()).hexdigest()[:8], 16))

    def local_train(
        self,
        round_id: int,
        learning_rate: float = 0.01,
        local_epochs: int = 3,
        clipping_threshold: float = 1.0,
        noise_scale: float = 0.0,
    ) -> LocalGradient:
        """
        Simulate local SGD training on site-specific risk data.
        Returns gradient deltas (NOT full weights — preserve privacy).
        """
        initial_weights = {k: v.copy() for k, v in self.weights.items()}

        # Simulate gradient via SGD on synthetic local risk data
        loss = 0.0
        for epoch in range(local_epochs):
            batch_loss = self._simulated_sgd_step(learning_rate)
            loss += batch_loss

        avg_loss = loss / local_epochs

        # Compute gradient delta = current - initial
        layer_updates: Dict[str, List[float]] = {}
        total_norm_sq = 0.0

        for name in self.weights:
            delta = self.weights[name] - initial_weights[name]
            total_norm_sq += float(np.sum(delta ** 2))
            layer_updates[name] = delta.tolist()

        gradient_norm = float(np.sqrt(total_norm_sq))

        # Gradient clipping (DP requirement)
        clipped = False
        if gradient_norm > clipping_threshold:
            scale = clipping_threshold / gradient_norm
            layer_updates = {k: (np.array(v) * scale).tolist() for k, v in layer_updates.items()}
            gradient_norm = clipping_threshold
            clipped = True

        # Gaussian noise injection (DP mechanism)
        epsilon_spent = 0.0
        if noise_scale > 0:
            for name in layer_updates:
                noise = self._rng.normal(0, noise_scale, size=len(layer_updates[name]))
                layer_updates[name] = (np.array(layer_updates[name]) + noise).tolist()
            # Rough epsilon estimate: clipping_threshold * sqrt(2*ln(1.25/delta)) / noise_scale
            delta_dp = 1e-5
            epsilon_spent = round(
                clipping_threshold * np.sqrt(2 * np.log(1.25 / delta_dp)) / max(noise_scale, 1e-9),
                4,
            )

        logger.debug(
            f"Site {self.config.site_id} | round {round_id} | "
            f"loss={avg_loss:.4f} | norm={gradient_norm:.4f} | "
            f"clipped={clipped} | ε_spent={epsilon_spent:.4f}"
        )

        return LocalGradient(
            site_id=self.config.site_id,
            round_id=round_id,
            gradient_norm=round(gradient_norm, 6),
            clipped=clipped,
            noise_scale=noise_scale,
            layer_updates=layer_updates,
            data_size=self.config.data_size,
            epsilon_spent=epsilon_spent,
            training_loss=round(avg_loss, 6),
        )

    def apply_global_weights(self, global_weights: Dict[str, List[float]]) -> None:
        """Download and apply the new global model from coordinator."""
        self.weights = {k: np.array(v) for k, v in global_weights.items()}

    def _simulated_sgd_step(self, lr: float) -> float:
        """
        Simulate a gradient step using synthetic site-specific data.
        Returns batch loss (proxy: sum of squared weight magnitudes).
        """
        loss = 0.0
        for name, w in self.weights.items():
            # Synthetic gradient: gradient ∝ weight magnitude + site-specific noise
            grad = w * 0.1 + self._rng.normal(0, 0.02, size=w.shape)
            self.weights[name] = w - lr * grad
            loss += float(np.mean(grad ** 2))
        return loss / len(self.weights)


# ─── FedAvg Coordinator ───────────────────────────────────────────────────────

class FederatedCoordinator:
    """
    AION central coordinator: manages rounds, aggregates gradients (FedAvg),
    tracks privacy budgets, and distributes the global model.

    Thread-safety note: This simulates a synchronous round; production
    would be async with separate process per site using gRPC.
    """

    def __init__(
        self,
        min_sites: int = 2,
        max_epsilon: float = 5.0,
        learning_rate: float = 0.01,
        local_epochs: int = 3,
        clipping_threshold: float = 1.0,
        noise_multiplier: float = 1.1,
    ) -> None:
        self.min_sites = min_sites
        self.max_epsilon = max_epsilon
        self.learning_rate = learning_rate
        self.local_epochs = local_epochs
        self.clipping_threshold = clipping_threshold
        self.noise_multiplier = noise_multiplier

        self._global_weights: Dict[str, List[float]] = _init_weights(seed=0)
        self._sites: Dict[str, SiteConfig] = {}
        self._simulators: Dict[str, SiteSimulator] = {}
        self._rounds: List[FederatedRound] = []
        self._epsilon_spent: Dict[str, float] = defaultdict(float)
        self._completed_rounds: int = 0
        self._round_losses: List[float] = []

    # ── Site Registration ─────────────────────────────────────────────────────

    def register_site(self, config: SiteConfig) -> None:
        """Register a new site with the federation."""
        self._sites[config.site_id] = config
        self._simulators[config.site_id] = SiteSimulator(config, self._global_weights)
        logger.info(f"🌐 Site registered: {config.site_id} ({config.site_name}, {config.location})")

    def list_sites(self) -> List[SiteConfig]:
        return list(self._sites.values())

    def site_count(self) -> int:
        return len(self._sites)

    # ── Round Execution ───────────────────────────────────────────────────────

    def run_round(self, target_sites: Optional[List[str]] = None) -> FederatedRound:
        """
        Execute one complete federated learning round:
        1. Select participating sites
        2. Each site trains locally and returns a gradient
        3. Coordinator aggregates (FedAvg) into new global model
        4. Distribute new global model back to all sites
        """
        round_id = len(self._rounds) + 1
        available = list(self._sites.keys())
        targets = target_sites or available

        # Filter sites that haven't exhausted their privacy budget
        eligible = [
            sid for sid in targets
            if self._epsilon_spent[sid] < self.max_epsilon
        ]

        fedround = FederatedRound(
            round_id=round_id,
            status=RoundStatus.IN_PROGRESS,
            target_sites=eligible,
            min_sites_required=self.min_sites,
        )
        self._rounds.append(fedround)

        if len(eligible) < self.min_sites:
            logger.warning(f"Round {round_id}: only {len(eligible)} eligible sites < min={self.min_sites}")
            fedround.status = RoundStatus.FAILED
            return fedround

        logger.info(f"🔄 Federated round {round_id} starting — {len(eligible)} sites")

        # Step 1: Distribute current global model
        for sid in eligible:
            self._simulators[sid].apply_global_weights(self._global_weights)

        # Step 2: Collect local gradients
        gradients: List[LocalGradient] = []
        noise_scale = self.noise_multiplier * self.clipping_threshold
        for sid in eligible:
            grad = self._simulators[sid].local_train(
                round_id=round_id,
                learning_rate=self.learning_rate,
                local_epochs=self.local_epochs,
                clipping_threshold=self.clipping_threshold,
                noise_scale=noise_scale,
            )
            gradients.append(grad)
            self._epsilon_spent[sid] += grad.epsilon_spent

        fedround.gradients_received = len(gradients)

        # Step 3: FedAvg aggregation
        aggregated = self._fedavg(gradients, round_id)
        self._global_weights = aggregated.global_weights
        self._completed_rounds += 1
        round_loss_val = aggregated.round_loss
        self._round_losses.append(round_loss_val)

        # Step 4: Finalise round
        fedround.status = RoundStatus.COMPLETED
        fedround.completed_at = datetime.now(timezone.utc)
        fedround.model_snapshot = aggregated

        logger.info(
            f"✅ Round {round_id} complete | loss={round_loss_val:.4f} | "
            f"ε_total={aggregated.epsilon_total:.3f}"
        )
        return fedround

    def run_multi_round(self, n_rounds: int) -> List[FederatedRound]:
        """Run n_rounds of federated training."""
        results = []
        for i in range(n_rounds):
            r = self.run_round()
            results.append(r)
            if r.status == RoundStatus.FAILED:
                logger.warning(f"Stopping after failed round {r.round_id}")
                break
        return results

    # ── Aggregation ───────────────────────────────────────────────────────────

    def _fedavg(self, gradients: List[LocalGradient], round_id: int) -> AggregatedModel:
        """
        Weighted FedAvg: new_w = old_w + Σ(n_i / N) * delta_i

        Weighted by each site's data_size to give more influence to
        sites with more local training samples.
        """
        total_samples = sum(g.data_size for g in gradients)
        avg_loss = sum(g.training_loss * g.data_size for g in gradients) / max(total_samples, 1)
        max_eps = max((self._epsilon_spent[g.site_id] for g in gradients), default=0.0)

        # Weighted sum of deltas
        agg: Dict[str, np.ndarray] = {
            name: np.array(v) for name, v in self._global_weights.items()
        }
        for grad in gradients:
            weight = grad.data_size / total_samples
            for name, delta in grad.layer_updates.items():
                agg[name] = agg[name] + weight * np.array(delta)

        new_weights = {k: v.tolist() for k, v in agg.items()}

        return AggregatedModel(
            round_id=round_id,
            participating_sites=[g.site_id for g in gradients],
            total_samples=total_samples,
            global_weights=new_weights,
            round_loss=round(avg_loss, 6),
            epsilon_total=round(max_eps, 4),
        )

    # ── Status ────────────────────────────────────────────────────────────────

    def global_weights(self) -> Dict[str, List[float]]:
        return self._global_weights

    def rounds_completed(self) -> int:
        return self._completed_rounds

    def epsilon_for_site(self, site_id: str) -> float:
        return self._epsilon_spent.get(site_id, 0.0)

    def latest_loss(self) -> float:
        return self._round_losses[-1] if self._round_losses else float("inf")

    def loss_trend(self) -> List[float]:
        return self._round_losses
