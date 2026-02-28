"""
AION: Service Orchestrator
============================
Wires together the full Phase 4 pipeline:

  RegisterSite / SubmitGradient / RunRound
       │
       ▼ FederatedCoordinator (FedAvg + LoRA)
       │
       ▼ PrivacyBudgetManager (Gaussian mechanism, ε ≤ 5)
       │
       ▼ KnowledgePersistenceManager (IPFS + Ethereum)
       │
       ▼ ContinuousEvolutionEngine (feedback loop)
       │
       ▼ AionService (facade)

Also provides a full Kerala end-to-end demo that simulates:
  - 4 real L&T sites (Mumbai, Delhi, Chennai, Kochi) federating
  - 5 rounds of privacy-preserving training
  - Prevention event anchored on IPFS+Ethereum after Kerala risk is mitigated
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from loguru import logger

from aion.evolution.engine import ContinuousEvolutionEngine
from aion.federated.engine import FederatedCoordinator
from aion.persistence.ipfs import KnowledgePersistenceManager
from aion.privacy.differential import PrivacyBudgetManager
from aion.schemas.models import (
    AnchorRequest,
    EventType,
    FederatedRound,
    FederationStatus,
    KnowledgeRecord,
    PersistenceReceipt,
    PrivacyBudget,
    PrivacyReport,
    RegisterSiteRequest,
    SiteConfig,
    SiteStatus,
    SubmitGradientRequest,
)


class AionService:
    """
    AION façade — single entry point for Phase 4.
    All subsystems are initialised here and share state through
    dependency injection rather than singletons.
    """

    def __init__(
        self,
        max_epsilon: float = 5.0,
        noise_multiplier: float = 1.1,
        clipping_threshold: float = 1.0,
        min_sites: int = 2,
        retraining_threshold: int = 3,
        ledger_path: Optional[Path] = None,
    ) -> None:
        self._start_time = time.time()

        # Subsystems
        self._coordinator = FederatedCoordinator(
            min_sites=min_sites,
            max_epsilon=max_epsilon,
            learning_rate=0.01,
            local_epochs=3,
            clipping_threshold=clipping_threshold,
            noise_multiplier=noise_multiplier,
        )
        self._privacy = PrivacyBudgetManager(
            max_epsilon=max_epsilon,
            noise_multiplier=noise_multiplier,
            clipping_threshold=clipping_threshold,
        )
        self._persistence = KnowledgePersistenceManager(ledger_path=ledger_path)
        self._evolution = ContinuousEvolutionEngine(
            persistence=self._persistence,
            retraining_threshold=retraining_threshold,
        )
        self._evolution.set_coordinator(self._coordinator)

    # ─── Site Management ──────────────────────────────────────────────────────

    def register_site(self, req: RegisterSiteRequest) -> SiteConfig:
        config = SiteConfig(
            site_id=req.site_id,
            site_name=req.site_name,
            location=req.location,
            project_type=req.project_type,
            data_size=req.data_size,
        )
        self._coordinator.register_site(config)
        self._privacy.get_or_create(req.site_id)
        return config

    def list_sites(self) -> List[SiteConfig]:
        return self._coordinator.list_sites()

    # ─── Federated Learning ───────────────────────────────────────────────────

    def run_round(self, target_sites: Optional[List[str]] = None) -> FederatedRound:
        return self._coordinator.run_round(target_sites)

    def run_multi_round(self, n_rounds: int) -> List[FederatedRound]:
        return self._coordinator.run_multi_round(n_rounds)

    # ─── Privacy ──────────────────────────────────────────────────────────────

    def privacy_report(self, site_id: str) -> PrivacyReport:
        return self._privacy.report(site_id)

    def all_budgets(self) -> List[PrivacyBudget]:
        return self._privacy.all_budgets()

    # ─── Persistence ──────────────────────────────────────────────────────────

    def anchor_event(
        self,
        req: AnchorRequest,
    ) -> tuple[KnowledgeRecord, PersistenceReceipt]:
        return self._persistence.anchor(req)

    def list_knowledge_records(
        self,
        event_type: Optional[EventType] = None,
        site_id: Optional[str] = None,
    ) -> List[KnowledgeRecord]:
        return self._persistence.list_records(event_type=event_type, site_id=site_id)

    def verify_record(self, record_id: str) -> bool:
        return self._persistence.verify(record_id)

    # ─── Evolution ────────────────────────────────────────────────────────────

    def record_site_event(
        self,
        event_type: EventType,
        site_id: str,
        project_id: str,
        risk_name: str,
        description: str,
        risk_score: float,
        prevention_applied: Optional[str] = None,
        outcome: str = "",
    ) -> tuple[KnowledgeRecord, PersistenceReceipt, bool]:
        return self._evolution.record_event(
            event_type=event_type,
            site_id=site_id,
            project_id=project_id,
            risk_name=risk_name,
            description=description,
            risk_score=risk_score,
            prevention_applied=prevention_applied,
            outcome=outcome,
        )

    # ─── Federation Status ────────────────────────────────────────────────────

    def federation_status(self) -> FederationStatus:
        sites = self._coordinator.list_sites()
        online = sum(1 for s in sites if s.status == SiteStatus.ONLINE)
        return FederationStatus(
            total_sites=len(sites),
            online_sites=online,
            rounds_completed=self._coordinator.rounds_completed(),
            total_knowledge_records=self._persistence.total_anchored(),
            total_epsilon_spent=max(
                (b.total_epsilon for b in self._privacy.all_budgets()),
                default=0.0,
            ),
            last_round_id=self._coordinator.rounds_completed(),
            last_aggregation=datetime.now(timezone.utc)
            if self._coordinator.rounds_completed() > 0 else None,
        )

    def uptime(self) -> float:
        return round(time.time() - self._start_time, 1)

    # ─── Kerala End-to-End Demo ───────────────────────────────────────────────

    def run_kerala_demo(self) -> dict:
        """
        Full AION Kerala demo:
          1. Register 4 simulated L&T sites
          2. Run 5 rounds of federated privacy-preserving training
          3. Anchor a 'prevention_applied' event for the Kerala viaduct risk
          4. Verify the anchor integrity
          5. Return a full status snapshot

        This demonstrates:
          - Privacy: ε ≤ 5.0 guaranteed across all rounds
          - Federated learning convergence (loss decreasing)
          - Immutable knowledge archival
          - Continuous evolution trigger
        """
        logger.info("🚀 AION Kerala demo starting...")

        # ── 1. Register sites ─────────────────────────────────────────────────
        sites = [
            RegisterSiteRequest(
                site_id="site-mumbai",
                site_name="Bandra-Worli Sea Link Phase II",
                location="Mumbai, Maharashtra",
                project_type="bridge",
                data_size=320,
            ),
            RegisterSiteRequest(
                site_id="site-delhi",
                site_name="Delhi Metro Phase IV — Aerocity",
                location="Delhi",
                project_type="metro",
                data_size=280,
            ),
            RegisterSiteRequest(
                site_id="site-chennai",
                site_name="Chennai Elevated Corridor Repair",
                location="Chennai, Tamil Nadu",
                project_type="elevated_road",
                data_size=190,
            ),
            RegisterSiteRequest(
                site_id="site-kerala",
                site_name="Kochi Coastal Viaduct",
                location="Kochi, Kerala",
                project_type="bridge",
                data_size=150,
            ),
        ]
        for s in sites:
            self.register_site(s)
        logger.info(f"  ✓ {len(sites)} sites registered")

        # ── 2. 5 federated rounds ─────────────────────────────────────────────
        rounds = self.run_multi_round(5)
        completed = [r for r in rounds if r.status.value == "completed"]
        final_loss = self._coordinator.latest_loss()
        loss_trend = self._coordinator.loss_trend()
        logger.info(f"  ✓ {len(completed)}/5 rounds completed | final loss={final_loss:.6f}")

        # ── 3. Anchor Kerala prevention event ─────────────────────────────────
        record, receipt, triggered = self.record_site_event(
            event_type=EventType.PREVENTION_APPLIED,
            site_id="site-kerala",
            project_id="kochi-viaduct-2025",
            risk_name="Compound Hydro-Thermal-Foundation Failure",
            description=(
                "KARMA-OMEGA detected unprecedented compound risk at Kochi coastal viaduct. "
                "Prevention applied: M40 upgrade + enclosed curing tents (RH < 70%) + "
                "extended cure to 42 days + rip-rap scour protection at all pier bases."
            ),
            risk_score=0.42,
            prevention_applied="M40 upgrade + enclosed curing + scour protection",
            outcome="Failure prevented. Concrete reached fck at day 36. Site safe.",
        )
        logger.info(f"  ✓ Kerala event anchored | CID={receipt.ipfs_cid[:20]}...")

        # ── 4. Verify integrity ───────────────────────────────────────────────
        verified = self.verify_record(record.record_id)
        logger.info(f"  ✓ Anchor integrity: {verified}")

        # ── 5. Status snapshot ─────────────────────────────────────────────────
        status = self.federation_status()
        privacy_reports = {sid: self.privacy_report(sid) for sid in ["site-kerala", "site-mumbai"]}

        logger.info("✅ AION Kerala demo complete")

        return {
            "sites_registered": len(sites),
            "rounds_completed": len(completed),
            "loss_trend": [round(l, 6) for l in loss_trend],
            "final_loss": round(final_loss, 6),
            "loss_converged": len(loss_trend) >= 2 and loss_trend[-1] < loss_trend[0],
            "kerala_record_id": record.record_id,
            "kerala_ipfs_cid": receipt.ipfs_cid,
            "kerala_eth_tx": receipt.ethereum_tx,
            "kerala_anchored": record.anchored,
            "integrity_verified": verified,
            "retraining_triggered": triggered,
            "federation_status": status.model_dump(),
            "privacy_reports": {
                k: v.model_dump() for k, v in privacy_reports.items()
            },
        }
