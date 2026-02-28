"""
SYNAPSE: Pydantic Schemas
==========================
Data models for the SYNAPSE pattern synthesis engine.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class NoveltyCategory(str, Enum):
    KNOWN = "known"              # Exact match in history
    VARIANT = "variant"          # Seen with slight differences
    SYNTHESIZED = "synthesized"  # Cross-domain combination
    UNPRECEDENTED = "unprecedented"  # Never seen in any form


# ─── Analogical Retrieval ──────────────────────────────────────────────────────


class AnalogueMatch(BaseModel):
    """A single historical failure retrieved as an analogue."""

    failure_id: str
    title: str
    location: str
    date: Optional[str] = None
    failure_type: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    matching_conditions: List[str] = Field(default_factory=list)
    causal_overlap: float = Field(default=0.0, ge=0.0, le=1.0)
    description_snippet: str = ""


class ProjectConditions(BaseModel):
    """Current state of a project — input to SYNAPSE analysis."""

    project_id: str
    project_name: str
    location: str
    conditions: Dict[str, Any] = Field(
        description="Environmental and material conditions",
        examples=[{"humidity": 88, "temperature": 39, "thermal_delta": 26}],
    )
    materials: List[str] = Field(default_factory=list)
    design_parameters: Dict[str, Any] = Field(default_factory=dict)
    days_until_critical_operation: Optional[int] = None
    notes: Optional[str] = None


# ─── Combinatorial Synthesis ──────────────────────────────────────────────────


class FailureGene(BaseModel):
    """A 'gene' extracted from a single historical failure."""

    source_failure_id: str
    source_title: str
    gene_type: str  # "humidity_sensitivity", "foundation_scour", "thermal_cracking", ...
    gene_value: float  # normalised 0–1 intensity
    description: str
    conditions: List[str] = Field(default_factory=list)


class SynthesisPattern(BaseModel):
    """A synthesised failure pattern from combining ≥2 failure genes."""

    pattern_id: str
    name: str
    description: str
    source_genes: List[FailureGene]
    combined_conditions: List[str]
    predicted_failure_mode: str
    confidence: float = Field(ge=0.0, le=1.0)
    novelty_score: float = Field(ge=0.0, le=1.0)
    novelty_category: NoveltyCategory = NoveltyCategory.SYNTHESIZED
    risk_level: RiskLevel = RiskLevel.HIGH
    monte_carlo_probability: Optional[float] = None  # P(failure) from simulation


class NoveltyReport(BaseModel):
    """Novelty assessment for a synthesis pattern."""

    pattern_id: str
    isolation_forest_score: float  # Anomaly score from Isolation Forest
    novelty_score: float           # Calibrated 0–1 (1 = fully unprecedented)
    novelty_category: NoveltyCategory
    nearest_historical_distance: float
    explanation: str


# ─── Risk Alert ───────────────────────────────────────────────────────────────


class CausalAttribution(BaseModel):
    """SHAP-style causal attribution for a risk alert."""

    feature: str
    attribution_value: float  # contribution to risk (signed)
    direction: str            # "increases_risk" | "decreases_risk"
    source_failure: Optional[str] = None


class RiskAlert(BaseModel):
    """The primary output of SYNAPSE — a novel risk alert for a project."""

    alert_id: str
    project_id: str
    project_name: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Risk summary
    risk_name: str
    risk_description: str
    risk_level: RiskLevel
    overall_confidence: float = Field(ge=0.0, le=1.0)

    # Novelty
    novelty_score: float = Field(ge=0.0, le=1.0)
    novelty_category: NoveltyCategory

    # Evidence
    analogues: List[AnalogueMatch]
    synthesis_pattern: SynthesisPattern
    novelty_report: NoveltyReport

    # Predictions
    predicted_failure_mode: str
    failure_probability_30_days: Optional[float] = None
    failure_probability_90_days: Optional[float] = None

    # Explainability
    causal_attributions: List[CausalAttribution] = Field(default_factory=list)
    key_risk_factors: List[str] = Field(default_factory=list)
    intervention_points: List[str] = Field(default_factory=list)

    # Metadata
    processing_time_ms: float = 0.0


# ─── API Schemas ──────────────────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    """Request to SYNAPSE: analyze a project for novel risks."""

    project: ProjectConditions
    top_k_analogues: int = Field(default=5, ge=1, le=20)
    min_analogue_similarity: float = Field(default=0.3, ge=0.0, le=1.0)
    monte_carlo_iterations: int = Field(default=1000, ge=100, le=10000)
    include_known_risks: bool = True  # include non-novel matching patterns too


class AnalyzeResponse(BaseModel):
    """SYNAPSE response — ranked risk alerts for a project."""

    project_id: str
    project_name: str
    total_alerts: int
    novel_alerts: int
    alerts: List[RiskAlert]
    processing_time_ms: float
    knowledge_base_size: int  # total failures in MNEMOS


class SynapseHealthResponse(BaseModel):
    """SYNAPSE health response."""

    status: str
    version: str
    mnemos_connected: bool
    knowledge_base_size: int
    model_loaded: bool
    uptime_seconds: float
