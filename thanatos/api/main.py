"""
THANATOS: FastAPI Application
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from thanatos.schemas.models import (
    PreventRequest,
    PreventionReport,
    ThanatosHealthResponse,
    ValidateRequest,
    ValidationReport,
)

_start_time = time.time()
_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _service
    logger.info("💀 THANATOS starting up...")
    from thanatos.service import ThanatosService
    _service = ThanatosService()
    logger.info("✅ THANATOS ready — PINN surrogates loaded")
    yield
    logger.info("THANATOS shutting down...")


app = FastAPI(
    title="KARMA-OMEGA THANATOS API",
    description=(
        "**THANATOS** — The Generative Physics Oracle\n\n"
        "Phase 3 of KARMA-OMEGA: validates risks via surrogate PINNs and generates "
        "physics-valid prevention alternatives ranked by NSGA-III multi-objective optimisation.\n\n"
        "Physics models:\n"
        "- Euler-Bernoulli beam (deflection, flexural stress, scour-reduced bearing)\n"
        "- Transient heat equation (thermal gradient cracking)\n"
        "- Avrami curing model (strength gain vs. humidity/temperature)\n\n"
        "Prevention types: Material · Sequence · Environmental · Structural · Monitoring"
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _svc():
    if _service is None:
        raise HTTPException(503, "THANATOS not initialized")
    return _service


@app.get("/health", response_model=ThanatosHealthResponse, tags=["System"])
async def health():
    return ThanatosHealthResponse(
        status="healthy",
        version="0.1.0",
        physics_models_loaded=["beam", "heat", "curing"],
        uptime_seconds=round(time.time() - _start_time, 1),
    )


@app.post("/validate", response_model=ValidationReport, tags=["Physics"])
async def validate(request: ValidateRequest):
    """
    Validate a risk scenario using PINN physics surrogates.

    Runs the Euler-Bernoulli beam, heat equation, and Avrami curing models
    and returns safety factors, utilization ratios, and failure mechanisms.
    """
    try:
        return _svc().validate(request)
    except Exception as e:
        logger.error(f"THANATOS validate error: {e}")
        raise HTTPException(500, str(e))


@app.post("/prevent", response_model=PreventionReport, tags=["Prevention"])
async def prevent(request: PreventRequest):
    """
    Generate physics-validated prevention alternatives for a risk alert.

    Runs the full pipeline:
    1. Baseline PINN validation
    2. Constrained alternative generation (5 types)
    3. NSGA-III Pareto ranking (risk vs. cost vs. schedule)
    4. Recommended alternative selection (closest to ideal point)
    """
    try:
        return _svc().prevent(request)
    except Exception as e:
        logger.error(f"THANATOS prevent error: {e}")
        raise HTTPException(500, str(e))


@app.post("/prevent/demo", response_model=PreventionReport, tags=["Prevention"])
async def prevent_demo():
    """
    Kerala flagship demo — prevention for Compound Hydro-Thermal-Foundation failure.

    Synthesised from Gujarat (humidity) + Medigadda (scour) + Chennai (thermal).
    Applied to Kochi coastal viaduct with M40, 88% RH, ΔT=26°C, 1.2m scour.
    """
    try:
        return _svc().prevent_kerala_demo()
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/physics/models", tags=["Physics"])
async def list_physics_models():
    """List available PINN physics surrogate models."""
    return {
        "models": [
            {"id": "beam", "name": "Euler-Bernoulli Beam", "outputs": ["deflection", "stress", "safety_factor"]},
            {"id": "heat", "name": "Transient Heat Equation", "outputs": ["thermal_stress", "cracking_risk"]},
            {"id": "curing", "name": "Avrami Curing Model", "outputs": ["fc_at_t", "time_to_design_strength"]},
            {"id": "combined", "name": "All Three Models", "outputs": ["all_above"]},
        ]
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "system": "KARMA-OMEGA",
        "horseman": "THANATOS — The Physics Oracle",
        "phase": 3,
        "status": "operational",
        "docs": "/docs",
        "demo": "POST /prevent/demo",
    }
