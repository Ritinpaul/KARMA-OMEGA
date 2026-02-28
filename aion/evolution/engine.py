"""
AION: Continuous Evolution Engine
====================================
The engine that drives the self-improving feedback loop in KARMA-OMEGA.

Every time something significant happens on a site — a prevention is applied,
a near-miss is reported, or a failure is confirmed — the Evolution Engine:

  1.  Persists the event to IPFS + Ethereum (immutable record).
  2.  Broadcasts the event to the federated coordinator to trigger retraining.
  3.  Estimates the model improvement from the new data.
  4.  Optionally triggers a new federated round if accumulated events exceed threshold.

This is the "flywheel": every prevented failure makes the model smarter,
which prevents more failures, which makes the model smarter…

"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from loguru import logger

from aion.persistence.ipfs import KnowledgePersistenceManager
from aion.schemas.models import (
    AnchorRequest,
    EvolutionEvent,
    EventType,
    FederationStatus,
    KnowledgeRecord,
    PersistenceReceipt,
)


class ContinuousEvolutionEngine:
    """
    Orchestrates the feedback loop:
    site event → persist → broadcast → trigger retraining.
    """

    def __init__(
        self,
        persistence: KnowledgePersistenceManager,
        retraining_threshold: int = 5,   # events before triggering a new round
    ) -> None:
        self._persistence = persistence
        self._retraining_threshold = retraining_threshold
        self._events: List[EvolutionEvent] = []
        self._events_since_last_round: int = 0
        self._coordinator = None   # injected externally (avoids circular import)

    def set_coordinator(self, coordinator) -> None:
        """Inject the FederatedCoordinator (avoids circular imports)."""
        self._coordinator = coordinator

    def record_event(
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
        """
        Process a real-world event:
          1. Persist it immutably.
          2. Decide whether to trigger federated retraining.
          3. Return (record, receipt, triggered_retraining).
        """
        anchor_req = AnchorRequest(
            event_type=event_type,
            project_id=project_id,
            site_id=site_id,
            risk_name=risk_name,
            description=description,
            risk_score=risk_score,
            prevention_applied=prevention_applied,
            outcome=outcome,
        )

        record, receipt = self._persistence.anchor(anchor_req)

        # Estimate improvement delta (proxy: high-risk events improve model more)
        improvement = round(risk_score * 0.05, 4)  # max 5% per event

        event = EvolutionEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            site_id=site_id,
            knowledge_record=record,
            triggered_retraining=False,
            improvement_delta=improvement,
        )

        self._events.append(event)
        self._events_since_last_round += 1

        triggered = False
        if self._events_since_last_round >= self._retraining_threshold:
            triggered = self._trigger_retraining()
            event.triggered_retraining = triggered
            if triggered:
                self._events_since_last_round = 0

        logger.info(
            f"🔄 Evolution event: {event_type} | site={site_id} | "
            f"Δ_model={improvement:.4f} | retrain={triggered}"
        )

        return record, receipt, triggered

    def _trigger_retraining(self) -> bool:
        if self._coordinator is None:
            logger.warning("No coordinator attached — skipping federated round trigger")
            return False
        try:
            result = self._coordinator.run_round()
            logger.info(f"🧠 Retraining round {result.round_id} triggered by evolution engine")
            return True
        except Exception as e:
            logger.error(f"Retraining failed: {e}")
            return False

    def list_events(self) -> List[EvolutionEvent]:
        return self._events.copy()

    def total_improvement(self) -> float:
        return round(sum(e.improvement_delta for e in self._events), 6)

    def events_by_type(self, event_type: EventType) -> List[EvolutionEvent]:
        return [e for e in self._events if e.event_type == event_type]
