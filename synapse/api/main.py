"""
SYNAPSE: FastAPI Application
==============================
Exposes SYNAPSE pattern synthesis over REST.

Endpoints:
  POST /analyze           — Full risk analysis for a project
  POST /analyze/demo      — Kerala flagship demo scenario
  GET  /patterns          — List available synthesis templates
  GET  /health            — Health check
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from synapse.schemas.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    SynapseHealthResponse,
)

_start_time = time.time()
_synapse_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _synapse_service
    logger.info("🧠 SYNAPSE starting up...")

    # Try to connect to MNEMOS
    graph_client = None
    embedding_pipeline = None

    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from mnemos.graph.client import GraphClient
        graph_client = GraphClient.get_instance()
        logger.info("✅ SYNAPSE connected to MNEMOS graph")
    except Exception as e:
        logger.warning(f"MNEMOS graph unavailable: {e} — using seed fallbacks")

    try:
        from mnemos.embeddings.pipeline import EmbeddingPipeline
        embedding_pipeline = EmbeddingPipeline.get_instance()
        logger.info("✅ SYNAPSE connected to MNEMOS embeddings")
    except Exception as e:
        logger.warning(f"MNEMOS embeddings unavailable: {e} — using seed fallbacks")

    from synapse.service import SynapseService
    _synapse_service = SynapseService(
        embedding_pipeline=embedding_pipeline,
        graph_client=graph_client,
    )
    logger.info("✅ SYNAPSE ready!")
    yield
    logger.info("SYNAPSE shutting down...")


app = FastAPI(
    title="KARMA-OMEGA SYNAPSE API",
    description=(
        "**SYNAPSE** — The Cross-Domain Pattern Synthesis Engine\n\n"
        "Phase 2 of KARMA-OMEGA: synthesises novel failure modes by combining "
        "failure DNA across historical analogues, and predicts risks that have "
        "never occurred before.\n\n"
        "Powered by:\n"
        "- Analogical Retrieval (Sentence-BERT vector search)\n"
        "- Failure Gene Extraction (domain-specific)\n"
        "- Combinatorial Synthesis (6 pattern templates)\n"
        "- Monte Carlo Simulation (stressor threshold sampling)\n"
        "- Isolation Forest Novelty Detection\n"
        "- SHAP-style Causal Attribution"
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_svc():
    if _synapse_service is None:
        raise HTTPException(503, "SYNAPSE service not initialized")
    return _synapse_service


@app.get("/health", response_model=SynapseHealthResponse, tags=["System"])
async def health():
    svc = _get_svc()
    return SynapseHealthResponse(
        status="healthy",
        version="0.1.0",
        mnemos_connected=svc._graph is not None and svc._graph.is_connected,
        knowledge_base_size=svc._get_kb_size(),
        model_loaded=True,
        uptime_seconds=round(time.time() - _start_time, 1),
    )


@app.post("/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
async def analyze(request: AnalyzeRequest):
    """
    Analyse a construction project for novel risk patterns.

    Runs the full SYNAPSE pipeline:
    1. Retrieve analogous historical failures (vector similarity)
    2. Extract failure genes per analogue
    3. Synthesise novel patterns via combinatorial fusion
    4. Monte Carlo simulate failure probabilities
    5. Detect novelty via Isolation Forest
    6. Generate SHAP causal attributions

    Returns ranked RiskAlerts ordered by severity and novelty.
    """
    try:
        return _get_svc().analyze(request)
    except Exception as e:
        logger.error(f"SYNAPSE analysis error: {e}")
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@app.post("/analyze/demo", response_model=AnalyzeResponse, tags=["Analysis"])
async def analyze_demo():
    """
    Run the flagship Kerala coastal viaduct demo scenario from KARMA-OMEGA pitch.

    Synthesises: Gujarat (humidity) + Medigadda (foundation/scour) + Chennai (thermal)
    → UNPRECEDENTED Compound Hydro-Thermal-Foundation Failure risk.
    """
    try:
        return _get_svc().analyze_kerala_demo()
    except Exception as e:
        logger.error(f"Demo analysis error: {e}")
        raise HTTPException(500, f"Demo failed: {str(e)}")


@app.get("/patterns", tags=["Knowledge"])
async def list_patterns():
    """List all available synthesis pattern templates."""
    from synapse.synthesis.combinatorial import SYNTHESIS_TEMPLATES
    return {
        "templates": [
            {
                "id": t["id"],
                "name": t["name"],
                "required_genes": t["required_genes"],
                "predicted_mode": t["predicted_mode"],
                "base_severity": t["base_severity"],
            }
            for t in SYNTHESIS_TEMPLATES
        ],
        "total": len(SYNTHESIS_TEMPLATES),
    }


@app.get("/genes", tags=["Knowledge"])
async def list_genes():
    """List all defined failure gene types."""
    from synapse.retrieval.engine import GENE_DEFINITIONS
    return {
        "genes": [
            {"type": k, "description": v["description"], "keywords": v["keywords"]}
            for k, v in GENE_DEFINITIONS.items()
        ],
        "total": len(GENE_DEFINITIONS),
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "system": "KARMA-OMEGA",
        "horseman": "SYNAPSE — The Pattern Synthesizer",
        "phase": 2,
        "status": "operational",
        "docs": "/docs",
        "demo": "POST /analyze/demo",
    }
