"""
AION: FastAPI Application
"""
import time
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from aion.schemas.models import (
    AionHealthResponse,
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
)

_start_time = time.time()
_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _service
    logger.info("⏳ AION starting up...")
    from aion.service import AionService
    _service = AionService()
    logger.info("✅ AION ready — Federation, Privacy, Persistence online")
    yield
    logger.info("AION shutting down...")


app = FastAPI(
    title="KARMA-OMEGA AION API",
    description=(
        "**AION** — The Immortality Engine\n\n"
        "Phase 4 of KARMA-OMEGA: federated privacy-preserving learning across all L&T sites, "
        "immutable knowledge archival on IPFS+Ethereum, and continuous model evolution.\n\n"
        "Every prevented failure enriches the global model. Every near-miss is permanently archived. "
        "AION ensures KARMA-OMEGA's knowledge outlives projects, engineers, and organisations."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _svc():
    if _service is None:
        raise HTTPException(503, "AION not initialised")
    return _service


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health", response_model=AionHealthResponse, tags=["System"])
async def health():
    svc = _svc()
    return AionHealthResponse(
        status="healthy",
        version="0.1.0",
        federation_status=svc.federation_status(),
        uptime_seconds=svc.uptime(),
    )


@app.get("/", tags=["System"])
async def root():
    return {
        "system": "KARMA-OMEGA",
        "horseman": "AION — The Immortality Engine",
        "phase": 4,
        "status": "operational",
        "docs": "/docs",
        "demo": "POST /demo/kerala",
    }


# ─── Site Management ──────────────────────────────────────────────────────────

@app.post("/sites/register", response_model=SiteConfig, tags=["Federation"])
async def register_site(req: RegisterSiteRequest):
    """Register a new construction site with the AION federation."""
    try:
        return _svc().register_site(req)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/sites", response_model=List[SiteConfig], tags=["Federation"])
async def list_sites():
    """List all registered federated sites."""
    return _svc().list_sites()


# ─── Federated Learning ───────────────────────────────────────────────────────

@app.post("/federation/round", response_model=FederatedRound, tags=["Federation"])
async def run_round():
    """
    Execute one federated learning round across all registered sites.
    Returns round metadata including participating sites and aggregated model loss.
    Each site's privacy budget is updated — rounds stop once ε ≥ 5.0.
    """
    try:
        return _svc().run_round()
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/federation/train", response_model=List[FederatedRound], tags=["Federation"])
async def run_multi_round(n_rounds: int = Query(default=3, ge=1, le=20)):
    """Run `n_rounds` of federated training. Returns results for all rounds."""
    try:
        return _svc().run_multi_round(n_rounds)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/federation/status", response_model=FederationStatus, tags=["Federation"])
async def federation_status():
    """Overall federation health — sites, rounds, epsilon spent, records anchored."""
    return _svc().federation_status()


# ─── Privacy ──────────────────────────────────────────────────────────────────

@app.get("/privacy/report/{site_id}", response_model=PrivacyReport, tags=["Privacy"])
async def privacy_report(site_id: str):
    """
    DP audit report for a site: mechanism, noise multiplier, ε per round,
    rounds until budget exhaustion, and formal (ε, δ)-DP guarantee string.
    """
    try:
        return _svc().privacy_report(site_id)
    except Exception as e:
        raise HTTPException(404, str(e))


@app.get("/privacy/budgets", response_model=List[PrivacyBudget], tags=["Privacy"])
async def all_budgets():
    """List privacy budgets for all sites — total ε consumed vs. max allowed."""
    return _svc().all_budgets()


# ─── Persistence ──────────────────────────────────────────────────────────────

@app.post("/knowledge/anchor", tags=["Persistence"])
async def anchor_event(req: AnchorRequest):
    """
    Immutably anchor a knowledge event (prevention, near-miss, failure confirmation).
    Returns IPFS CID, Ethereum TX hash, and content hash for audit verification.
    """
    try:
        record, receipt = _svc().anchor_event(req)
        return {"record": record, "receipt": receipt}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/knowledge/records", response_model=List[KnowledgeRecord], tags=["Persistence"])
async def list_records(
    event_type: Optional[EventType] = None,
    site_id: Optional[str] = None,
):
    """List all anchored knowledge records, optionally filtered by type or site."""
    return _svc().list_knowledge_records(event_type=event_type, site_id=site_id)


@app.get("/knowledge/verify/{record_id}", tags=["Persistence"])
async def verify_record(record_id: str):
    """Verify a record's IPFS+Ethereum anchor integrity."""
    ok = _svc().verify_record(record_id)
    return {"record_id": record_id, "integrity_ok": ok}


# ─── Evolution ────────────────────────────────────────────────────────────────

@app.post("/evolution/event", tags=["Evolution"])
async def record_evolution_event(
    event_type: EventType,
    site_id: str,
    project_id: str,
    risk_name: str,
    description: str,
    risk_score: float = Query(ge=0, le=1),
    prevention_applied: Optional[str] = None,
    outcome: str = "",
):
    """
    Record a real-world site event. Triggers immutable anchoring and,
    if enough events have accumulated, an automatic federated retraining round.
    """
    try:
        record, receipt, triggered = _svc().record_site_event(
            event_type=event_type,
            site_id=site_id,
            project_id=project_id,
            risk_name=risk_name,
            description=description,
            risk_score=risk_score,
            prevention_applied=prevention_applied,
            outcome=outcome,
        )
        return {
            "record": record,
            "receipt": receipt,
            "retraining_triggered": triggered,
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# ─── Demo ─────────────────────────────────────────────────────────────────────

@app.post("/demo/kerala", tags=["Demo"])
async def kerala_demo():
    """
    Full AION Kerala demo:
    - 4 L&T sites registered (Mumbai, Delhi, Chennai, Kochi)
    - 5 privacy-preserving federated rounds (ε ≤ 5)
    - Prevention event anchored on IPFS+Ethereum
    - Anchor integrity verified
    """
    try:
        return _svc().run_kerala_demo()
    except Exception as e:
        raise HTTPException(500, str(e))
