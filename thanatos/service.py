"""
THANATOS: Orchestrator Service
================================
Wires together the full Phase 3 pipeline:

  RiskAlert + StructuralParameters + SiteConditions
       │
       ▼  1. PINN Physics Validation (Beam + Heat + Curing)
  PINNEvaluator.evaluate_all()
       │
       ▼  2. ValidationReport (safety factors, failure mechanisms)
  ConstrainedRedesigner.generate()
       │
       ▼  3. Prevention Alternatives (5 types, physics-validated)
  NSGA3Optimizer.optimize()
       │
       ▼  4. Pareto-ranked alternatives + recommended pick
  PreventionReport
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from loguru import logger

from thanatos.optimization.nsga3 import NSGA3Optimizer
from thanatos.physics.pinn import PINNEvaluator, _safety_status
from thanatos.redesign.generator import ConstrainedRedesigner
from thanatos.schemas.models import (
    PhysicsModel,
    PreventRequest,
    PreventionReport,
    SafetyStatus,
    SiteConditions,
    StructuralParameters,
    ValidateRequest,
    ValidationReport,
)


class ThanatosService:
    """
    THANATOS orchestrator — the Physics Validation and Prevention Oracle.
    Stateless: all components are re-instantiated per call.
    """

    def __init__(self) -> None:
        self._pinn = PINNEvaluator()
        self._optimizer = NSGA3Optimizer()

    # ─── Validation Only ──────────────────────────────────────────────────────

    def validate(self, request: ValidateRequest) -> ValidationReport:
        """
        Run PINN physics validation for a risk scenario.
        Returns safety factors, failure mechanisms, and overall status.
        """
        start = time.time()

        models = request.physics_models
        if PhysicsModel.COMBINED in models:
            models = [PhysicsModel.BEAM, PhysicsModel.HEAT, PhysicsModel.CURING]

        results = self._pinn.evaluate_all(
            structural=request.structural,
            site=request.site,
            models=models,
            curing_days=request.curing_days,
        )

        mechanisms = self._pinn.identify_failure_mechanisms(
            results, request.structural, request.site
        )

        # Overall status = worst of all models
        worst_sf = min((r.safety_factor for r in results), default=1.0)
        worst_status = _safety_status(worst_sf)

        # Critical parameters
        critical_params = {
            "humidity_percent": request.site.humidity_percent,
            "thermal_delta_c": request.site.thermal_delta_c,
            "scour_depth_m": request.structural.scour_depth_m,
            "concrete_grade": request.structural.concrete_grade,
        }

        avg_confidence = sum(r.confidence for r in results) / max(len(results), 1)

        logger.info(
            f"THANATOS validate: {request.risk_name} → {worst_status} (SF={worst_sf:.2f})"
        )

        return ValidationReport(
            alert_id=request.alert_id,
            risk_name=request.risk_name,
            overall_safety_status=worst_status,
            worst_case_safety_factor=round(worst_sf, 3),
            pinn_results=results,
            failure_mechanisms=mechanisms,
            critical_parameters=critical_params,
            validation_confidence=round(avg_confidence, 3),
            processing_time_ms=round((time.time() - start) * 1000, 2),
        )

    # ─── Prevention Pipeline ──────────────────────────────────────────────────

    def prevent(self, request: PreventRequest) -> PreventionReport:
        """
        Full THANATOS pipeline: validate → generate alternatives → NSGA-III rank.
        Returns a ranked prevention report with a recommended alternative.
        """
        start = time.time()

        # ── Baseline validation ────────────────────────────────────────────────
        baseline_results = self._pinn.evaluate_all(
            structural=request.structural,
            site=request.site,
            models=[PhysicsModel.BEAM, PhysicsModel.CURING],
        )
        baseline_sf = min((r.safety_factor for r in baseline_results), default=1.0)
        baseline_status = _safety_status(baseline_sf)

        logger.info(
            f"🔬 THANATOS preventing: '{request.risk_name}' "
            f"(baseline SF={baseline_sf:.2f}, P30={request.failure_probability_30d:.2f})"
        )

        # ── Generate alternatives ──────────────────────────────────────────────
        redesigner = ConstrainedRedesigner(pinn=self._pinn)
        alternatives = redesigner.generate(
            structural=request.structural,
            site=request.site,
            risk_name=request.risk_name,
            max_alternatives=request.max_alternatives + 3,  # oversample for optimizer
        )

        logger.info(f"  Generated {len(alternatives)} alternatives before NSGA-III")

        # ── NSGA-III optimization ──────────────────────────────────────────────
        ranked = self._optimizer.optimize(alternatives)
        ranked = ranked[:request.max_alternatives]

        recommended = self._optimizer.pick_recommended(ranked)

        total_ms = max(1.0, (time.time() - start) * 1000)
        logger.info(
            f"✅ THANATOS complete: {len(ranked)} alternatives, "
            f"recommended='{recommended.name if recommended else None}' "
            f"in {total_ms:.0f}ms"
        )

        return PreventionReport(
            alert_id=request.alert_id,
            risk_name=request.risk_name,
            baseline_safety_factor=round(baseline_sf, 3),
            baseline_status=baseline_status,
            alternatives=ranked,
            recommended=recommended,
            optimization_objectives=request.optimization_objectives,
            processing_time_ms=round(total_ms, 2),
        )

    # ─── Kerala Demo ──────────────────────────────────────────────────────────

    def prevent_kerala_demo(self) -> PreventionReport:
        """
        Flagship demo: THANATOS prevention for Kerala Compound Hydro-Thermal-Foundation risk.
        """
        structural = StructuralParameters(
            span_length_m=45.0,
            cross_section_width_m=0.6,
            cross_section_height_m=1.5,
            concrete_grade="M40",
            design_compressive_strength_mpa=40.0,
            elastic_modulus_gpa=31.6,
            dead_load_kn_per_m=80.0,
            live_load_kn_per_m=50.0,
            bearing_capacity_kpa=280.0,
            scour_depth_m=1.2,   # tidal scour
        )
        site = SiteConditions(
            humidity_percent=88.0,
            ambient_temperature_c=39.0,
            thermal_delta_c=26.0,
            rainfall_mm_per_day=12.0,
            coastal=True,
            seismic_zone="III",
        )
        req = PreventRequest(
            risk_name="Compound Hydro-Thermal-Foundation Failure",
            risk_description=(
                "Simultaneous high humidity (strength retardation), thermal cracking "
                "(ΔT=26°C), and tidal scour (1.2m depth loss) at Kerala coastal viaduct."
            ),
            alert_id="kerala-demo-alert-001",
            failure_probability_30d=0.42,
            structural=structural,
            site=site,
            max_alternatives=5,
        )
        return self.prevent(req)
