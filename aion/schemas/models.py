"""
AION: Pydantic Schemas
=======================
Data models for federated learning, differential privacy, IPFS persistence,
and continuous evolution events.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────


class SiteStatus(str, Enum):
    ONLINE = "online"
    TRAINING = "training"
    AGGREGATING = "aggregating"
    OFFLINE = "offline"


class RoundStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class EventType(str, Enum):
    FAILURE_CONFIRMED = "failure_confirmed"
    NEAR_MISS = "near_miss"
    PREVENTION_APPLIED = "prevention_applied"
    ALERT_DISMISSED = "alert_dismissed"
    NEW_PROJECT = "new_project"


class PrivacyMechanism(str, Enum):
    GAUSSIAN = "gaussian"
    LAPLACE = "laplace"
    NONE = "none"


# ─── Federated Site Models ────────────────────────────────────────────────────


class SiteConfig(BaseModel):
    """Configuration for a federated learning site (construction project site)."""
    site_id: str
    site_name: str
    location: str
    project_type: str = "bridge"
    data_size: int = Field(default=100, ge=1, description="Local training samples")
    status: SiteStatus = SiteStatus.ONLINE
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LocalGradient(BaseModel):
    """Encrypted gradient update from a single site (FedAvg-style)."""
    site_id: str
    round_id: int
    gradient_norm: float = Field(ge=0)
    clipped: bool = False                   # True if gradient was clipped for DP
    noise_scale: float = Field(default=0.0, ge=0)
    layer_updates: Dict[str, List[float]]   # layer_name → flattened delta weights
    data_size: int = Field(ge=1)            # samples used — for weighted averaging
    epsilon_spent: float = Field(default=0.0, ge=0)
    training_loss: float = Field(default=0.0, ge=0)


class AggregatedModel(BaseModel):
    """Result of a single federated aggregation round."""
    round_id: int
    participating_sites: List[str]
    aggregation_method: str = "fedavg"     # "fedavg" | "fedprox"
    total_samples: int
    global_weights: Dict[str, List[float]]  # Federated-averaged weights
    round_loss: float
    epsilon_total: float = Field(description="Cumulative privacy budget spent")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FederatedRound(BaseModel):
    """Metadata for one global training round."""
    round_id: int
    status: RoundStatus = RoundStatus.PENDING
    target_sites: List[str]
    min_sites_required: int = Field(default=2, ge=2)
    gradients_received: int = 0
    completed_at: Optional[datetime] = None
    model_snapshot: Optional[AggregatedModel] = None


# ─── Differential Privacy Models ─────────────────────────────────────────────


class PrivacyBudget(BaseModel):
    """Tracks DP epsilon consumption across rounds."""
    site_id: str
    total_epsilon: float = Field(default=0.0, ge=0)
    total_delta: float = Field(default=1e-5, ge=0)
    rounds_participated: int = 0
    max_epsilon: float = Field(default=5.0, description="Hard budget limit (ε ≤ 5)")

    @property
    def is_exhausted(self) -> bool:
        return self.total_epsilon >= self.max_epsilon

    @property
    def remaining_epsilon(self) -> float:
        return max(0.0, self.max_epsilon - self.total_epsilon)


class PrivacyReport(BaseModel):
    """DP audit report for a training session."""
    mechanism: PrivacyMechanism
    noise_multiplier: float
    clipping_threshold: float
    epsilon_per_round: float
    delta: float
    rounds_until_exhaustion: int
    privacy_guarantee: str


# ─── IPFS / Persistence Models ────────────────────────────────────────────────


class KnowledgeRecord(BaseModel):
    """An immutable knowledge record — a prevented failure or near-miss."""
    record_id: str
    event_type: EventType
    project_id: str
    site_id: str
    risk_name: str
    description: str
    risk_score: float = Field(ge=0, le=1)
    prevention_applied: Optional[str] = None
    outcome: str = ""                       # what actually happened

    # Anchoring
    ipfs_cid: Optional[str] = None          # Content-addressed IPFS hash
    ethereum_tx: Optional[str] = None       # Simulated Ethereum tx hash
    anchored: bool = False

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PersistenceReceipt(BaseModel):
    """Receipt returned after anchoring a record."""
    record_id: str
    ipfs_cid: str
    ethereum_tx: str
    anchored_at: datetime
    content_hash: str                       # SHA-256 of record JSON


# ─── Continuous Evolution Models ─────────────────────────────────────────────


class EvolutionEvent(BaseModel):
    """Triggered when the global model should be updated."""
    event_id: str
    event_type: EventType
    site_id: str
    knowledge_record: KnowledgeRecord
    triggered_retraining: bool = False
    improvement_delta: float = 0.0          # Δ accuracy after retraining


class FederationStatus(BaseModel):
    """Overall AION federation health snapshot."""
    total_sites: int
    online_sites: int
    rounds_completed: int
    total_knowledge_records: int
    total_epsilon_spent: float              # worst-case across all sites
    last_round_id: int
    last_aggregation: Optional[datetime]


# ─── API Request / Response ───────────────────────────────────────────────────


class RegisterSiteRequest(BaseModel):
    site_id: str
    site_name: str
    location: str
    project_type: str = "bridge"
    data_size: int = 100


class SubmitGradientRequest(BaseModel):
    site_id: str
    round_id: int
    layer_updates: Dict[str, List[float]]
    data_size: int
    training_loss: float = 0.0


class AnchorRequest(BaseModel):
    event_type: EventType
    project_id: str
    site_id: str
    risk_name: str
    description: str
    risk_score: float
    prevention_applied: Optional[str] = None
    outcome: str = ""


class AionHealthResponse(BaseModel):
    status: str
    version: str
    federation_status: FederationStatus
    uptime_seconds: float
