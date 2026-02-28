"""
THANATOS: Pydantic Schemas
============================
Data models for input/output of the physics validation and
generative redesign pipeline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────


class PhysicsModel(str, Enum):
    BEAM = "beam"                  # Euler-Bernoulli beam PDE
    HEAT = "heat"                  # Transient heat equation (curing)
    CURING = "curing"              # Cement hydration + strength gain
    COMBINED = "combined"          # All three simultaneously


class SafetyStatus(str, Enum):
    SAFE = "safe"
    MARGINAL = "marginal"
    UNSAFE = "unsafe"
    CRITICAL = "critical"


class AlternativeType(str, Enum):
    MATERIAL = "material_upgrade"
    SEQUENCE = "sequence_change"
    ENVIRONMENTAL = "environmental_control"
    STRUCTURAL = "structural_redesign"
    MONITORING = "enhanced_monitoring"


# ─── Physics Input ────────────────────────────────────────────────────────────


class StructuralParameters(BaseModel):
    """Structural geometry and material parameters for PINN analysis."""

    # Geometry
    span_length_m: float = Field(default=30.0, gt=0, description="Span length in metres")
    cross_section_width_m: float = Field(default=0.5, gt=0)
    cross_section_height_m: float = Field(default=1.2, gt=0)
    thickness_m: Optional[float] = None

    # Material
    concrete_grade: str = Field(default="M30", description="e.g. M30, M40")
    rebar_grade: str = Field(default="Fe500", description="e.g. Fe415, Fe500")
    design_compressive_strength_mpa: float = Field(default=30.0, gt=0)
    design_tensile_strength_mpa: float = Field(default=3.0, gt=0)
    elastic_modulus_gpa: float = Field(default=27.4, gt=0)

    # Loading
    dead_load_kn_per_m: float = Field(default=50.0, gt=0)
    live_load_kn_per_m: float = Field(default=30.0, gt=0)
    wind_load_kn_per_m2: float = Field(default=1.5, ge=0)

    # Foundation
    bearing_capacity_kpa: float = Field(default=300.0, gt=0)
    scour_depth_m: float = Field(default=0.0, ge=0)


class SiteConditions(BaseModel):
    """Environmental conditions at the site."""

    humidity_percent: float = Field(default=70.0, ge=0, le=100)
    ambient_temperature_c: float = Field(default=28.0)
    thermal_delta_c: float = Field(default=15.0, ge=0, description="Daily temperature range")
    rainfall_mm_per_day: float = Field(default=0.0, ge=0)
    wind_speed_ms: float = Field(default=10.0, ge=0)
    coastal: bool = False
    seismic_zone: str = Field(default="II", description="IS:1893 zone")


class ValidateRequest(BaseModel):
    """Request to THANATOS: validate a specific risk under physics."""

    risk_name: str
    risk_description: str
    alert_id: Optional[str] = None

    structural: StructuralParameters = Field(default_factory=StructuralParameters)
    site: SiteConditions = Field(default_factory=SiteConditions)

    physics_models: List[PhysicsModel] = Field(
        default=[PhysicsModel.BEAM, PhysicsModel.CURING],
        description="Which PDE models to run",
    )
    curing_days: int = Field(default=28, ge=1, le=90)


class PreventRequest(BaseModel):
    """Request to THANATOS: generate prevention alternatives for a risk alert."""

    risk_name: str
    risk_description: str
    alert_id: Optional[str] = None
    failure_probability_30d: float = Field(default=0.3, ge=0, le=1)

    structural: StructuralParameters = Field(default_factory=StructuralParameters)
    site: SiteConditions = Field(default_factory=SiteConditions)

    max_alternatives: int = Field(default=5, ge=1, le=10)
    optimization_objectives: List[str] = Field(
        default=["minimize_risk", "minimize_cost", "minimize_schedule_impact"]
    )


# ─── Physics Output ───────────────────────────────────────────────────────────


class PINNResult(BaseModel):
    """Output from a single PINN model evaluation."""

    model: PhysicsModel
    safety_status: SafetyStatus
    safety_factor: float = Field(description="Ratio of capacity to demand")
    utilization_ratio: float = Field(ge=0, description="Demand/capacity; >1.0 = failure")

    # Model-specific outputs
    max_deflection_mm: Optional[float] = None
    max_stress_mpa: Optional[float] = None
    predicted_strength_mpa: Optional[float] = None  # curing model
    time_to_design_strength_days: Optional[float] = None  # curing model
    critical_temperature_zone: Optional[str] = None  # heat model

    residual: float = Field(default=0.0, description="PINN PDE residual (lower = better fit)")
    confidence: float = Field(default=0.85, ge=0, le=1)
    explanation: str = ""


class ValidationReport(BaseModel):
    """THANATOS physics validation report for a risk scenario."""

    alert_id: Optional[str]
    risk_name: str
    overall_safety_status: SafetyStatus
    worst_case_safety_factor: float
    pinn_results: List[PINNResult]
    failure_mechanisms: List[str]
    critical_parameters: Dict[str, Any]
    validation_confidence: float
    processing_time_ms: float = 0.0


# ─── Prevention Alternatives ──────────────────────────────────────────────────


class PreventionAlternative(BaseModel):
    """A single physics-validated prevention alternative."""

    alternative_id: str
    name: str
    type: AlternativeType
    description: str

    # NSGA-III Pareto objectives
    risk_reduction_factor: float = Field(ge=0, le=1, description="Fractional risk reduction")
    cost_index: float = Field(ge=0, le=1, description="0=free, 1=maximum cost")
    schedule_impact_days: int = Field(ge=0, description="Additional days required")

    # Physics validation
    predicted_safety_factor: float
    safety_status_after: SafetyStatus
    physics_validated: bool = True

    # Implementation
    actions: List[str] = Field(default_factory=list)
    monitoring_requirements: List[str] = Field(default_factory=list)

    # NSGA-III ranking
    pareto_rank: int = Field(default=1, description="1 = Pareto-optimal front")
    crowding_distance: float = Field(default=0.0)


class PreventionReport(BaseModel):
    """THANATOS full prevention report with ranked alternatives."""

    alert_id: Optional[str]
    risk_name: str
    baseline_safety_factor: float
    baseline_status: SafetyStatus

    alternatives: List[PreventionAlternative]
    recommended: Optional[PreventionAlternative] = None
    kerala_scenario: bool = False

    optimization_objectives: List[str]
    processing_time_ms: float = 0.0
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─── API Schemas ──────────────────────────────────────────────────────────────


class ThanatosHealthResponse(BaseModel):
    status: str
    version: str
    physics_models_loaded: List[str]
    uptime_seconds: float
