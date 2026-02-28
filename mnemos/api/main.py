"""
MNEMOS: FastAPI Application
============================
Exposes the MNEMOS knowledge layer over REST.

Endpoints:
  POST /ingest               — Ingest a failure document (text or PDF)
  GET  /query                — Semantic similarity query
  POST /graph/traverse       — Causal chain traversal
  GET  /graph/nodes          — List all graph nodes
  GET  /graph/failures/{id}  — Get single failure with graph context
  GET  /health               — Health check
"""

import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from mnemos.config import get_settings, Settings
from mnemos.schemas.models import (
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    QueryResult,
    TraverseRequest,
    TraverseResponse,
    HealthResponse,
    GraphSubgraph,
)

# ─── App Lifecycle ────────────────────────────────────────────────────────────

_start_time = time.time()
_graph_client = None
_embedding_pipeline = None
_ingestion_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup, clean up on shutdown."""
    global _graph_client, _embedding_pipeline, _ingestion_service

    logger.info("🚀 MNEMOS starting up...")
    settings = get_settings()

    try:
        from mnemos.graph.client import GraphClient
        _graph_client = GraphClient.get_instance()
        logger.info("✅ Neo4j connected")
    except Exception as e:
        logger.warning(f"Neo4j unavailable (will run without graph): {e}")

    try:
        from mnemos.embeddings.pipeline import EmbeddingPipeline
        _embedding_pipeline = EmbeddingPipeline.get_instance()
        logger.info("✅ Embedding pipeline ready")
    except Exception as e:
        logger.error(f"Embedding pipeline failed (required): {e}")
        raise

    from mnemos.ingestion.service import DocumentIngestionService
    _ingestion_service = DocumentIngestionService(
        graph_client=_graph_client,
        embedding_pipeline=_embedding_pipeline,
        use_gemini=bool(settings.gemini_api_key),
    )
    logger.info("✅ MNEMOS ready!")

    yield

    logger.info("MNEMOS shutting down...")
    if _graph_client:
        _graph_client.close()


# ─── App Instance ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="KARMA-OMEGA MNEMOS API",
    description=(
        "**MNEMOS** — The Neural-Symbolic Memory Palace\n\n"
        "Phase 1 of KARMA-OMEGA: Ingests construction failure documents, builds a "
        "causal knowledge graph, and provides semantic similarity retrieval for "
        "pattern synthesis.\n\n"
        "Part of the **KARMA-OMEGA** project targeting institutional knowledge "
        "preservation and novel failure prediction."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Dependencies ─────────────────────────────────────────────────────────────

def get_ingestion_service():
    if _ingestion_service is None:
        raise HTTPException(503, "Ingestion service not initialized")
    return _ingestion_service


def get_graph():
    if _graph_client is None:
        raise HTTPException(503, "Graph client not connected")
    return _graph_client


def get_embeddings():
    if _embedding_pipeline is None:
        raise HTTPException(503, "Embedding pipeline not ready")
    return _embedding_pipeline


# ─── Routes ───────────────────────────────────────────────────────────────────


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint — verifies connectivity to all subsystems."""
    neo4j_ok = False
    node_count = 0
    edge_count = 0

    if _graph_client and _graph_client.is_connected:
        try:
            node_count = _graph_client.get_node_count()
            edge_count = _graph_client.get_edge_count()
            neo4j_ok = True
        except Exception:
            pass

    pinecone_ok = _embedding_pipeline is not None and _embedding_pipeline.is_pinecone_active

    return HealthResponse(
        status="healthy",
        version=get_settings().app_version,
        neo4j_connected=neo4j_ok,
        pinecone_connected=pinecone_ok,
        total_graph_nodes=node_count,
        total_graph_edges=edge_count,
        uptime_seconds=round(time.time() - _start_time, 1),
    )


@app.post("/ingest", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_document(
    request: IngestRequest,
    svc=Depends(get_ingestion_service),
):
    """
    Ingest a failure document into MNEMOS.

    **source_type** options:
    - `text` — raw text content
    - `pdf_path` — absolute local path to a PDF file

    The system will:
    1. Extract entities (failure modes, materials, conditions)
    2. Build causal chains
    3. Store in Neo4j knowledge graph
    4. Generate and store embedding vector
    """
    try:
        if request.source_type == "text":
            return svc.ingest_text(request.content, request.metadata)
        elif request.source_type == "pdf_path":
            return svc.ingest_pdf(request.content, request.metadata)
        else:
            raise HTTPException(400, f"Unknown source_type: {request.source_type}")
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(500, f"Ingestion failed: {str(e)}")


@app.post("/query", response_model=QueryResponse, tags=["Retrieval"])
async def semantic_query(
    request: QueryRequest,
    embeddings=Depends(get_embeddings),
    graph=Depends(get_graph) if False else None,  # optional graph context
):
    """
    Semantic similarity query over the MNEMOS failure corpus.

    Returns the top-K most similar failures with optional graph context.
    Used by SYNAPSE for analogical retrieval.
    """
    start = time.time()

    if _embedding_pipeline is None:
        raise HTTPException(503, "Embedding pipeline not ready")

    results_raw = _embedding_pipeline.search(
        query=request.query,
        top_k=request.top_k,
        filters=request.filters or None,
    )

    results = []
    for r in results_raw:
        # Enrich from graph if available
        graph_context = None
        failure_node = None

        if _graph_client and _graph_client.is_connected:
            try:
                failure_node = _graph_client.get_failure_by_id(r["id"])
                if request.include_graph_context:
                    graph_context = _graph_client.traverse_causal_chain(
                        start_node_id=r["id"], max_depth=2
                    )
            except Exception:
                pass

        meta = r.get("metadata", {})
        results.append(
            QueryResult(
                failure_id=r["id"],
                title=meta.get("title", failure_node.get("title", "Unknown") if failure_node else "Unknown"),
                similarity_score=round(r["score"], 4),
                location=meta.get("location", failure_node.get("location", "Unknown") if failure_node else "Unknown"),
                failure_type=meta.get("failure_type", "unknown"),
                severity=meta.get("severity", "unknown"),
                description=failure_node.get("description", "")[:300] if failure_node else "",
                root_causes=[],
                graph_context=graph_context,
            )
        )

    return QueryResponse(
        query=request.query,
        results=results,
        total_found=len(results),
        processing_time_ms=round((time.time() - start) * 1000, 2),
    )


@app.post("/graph/traverse", response_model=TraverseResponse, tags=["Graph"])
async def traverse_causal_chain(
    request: TraverseRequest,
    graph=Depends(get_graph),
):
    """
    Traverse the causal chain from a starting failure node.
    Returns the subgraph and all causal paths found.

    Used by SYNAPSE to understand and combine failure patterns.
    """
    start = time.time()

    edge_types = [et.value for et in request.edge_types] if request.edge_types else None

    try:
        subgraph = graph.traverse_causal_chain(
            start_node_id=request.start_node_id,
            max_depth=request.max_depth,
            edge_types=edge_types,
            direction=request.direction,
        )
    except Exception as e:
        logger.error(f"Graph traversal error: {e}")
        raise HTTPException(500, f"Traversal failed: {str(e)}")

    # Extract causal paths as lists of node IDs
    causal_paths = []
    if subgraph.nodes:
        # Simple: each node chain from root
        causal_paths = [[n.id for n in subgraph.nodes[:5]]]

    return TraverseResponse(
        start_node_id=request.start_node_id,
        subgraph=subgraph,
        causal_paths=causal_paths,
        processing_time_ms=round((time.time() - start) * 1000, 2),
    )


@app.get("/graph/failures", tags=["Graph"])
async def list_failures(
    limit: int = Query(default=50, ge=1, le=200),
    graph=Depends(get_graph),
):
    """List all failure nodes in the knowledge graph."""
    try:
        failures = graph.get_all_failures(limit=limit)
        return {"failures": failures, "count": len(failures)}
    except Exception as e:
        raise HTTPException(500, f"Graph query failed: {str(e)}")


@app.get("/graph/failures/{failure_id}", tags=["Graph"])
async def get_failure(failure_id: str, graph=Depends(get_graph)):
    """Retrieve a single failure node with its graph context."""
    try:
        node = graph.get_failure_by_id(failure_id)
        if not node:
            raise HTTPException(404, f"Failure not found: {failure_id}")

        similar = graph.find_similar_failures(failure_id)

        return {
            "failure": node,
            "similar_failures": similar,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/graph/search", tags=["Graph"])
async def fulltext_search(
    q: str = Query(description="Search query for full-text search"),
    limit: int = Query(default=10, ge=1, le=50),
    graph=Depends(get_graph),
):
    """Full-text search over failure titles and descriptions in Neo4j."""
    try:
        results = graph.search_failures_by_text(q, limit=limit)
        return {"query": q, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/", tags=["System"])
async def root():
    """KARMA-OMEGA MNEMOS root."""
    return {
        "system": "KARMA-OMEGA",
        "horseman": "MNEMOS — The Memory Palace",
        "phase": 1,
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
    }
