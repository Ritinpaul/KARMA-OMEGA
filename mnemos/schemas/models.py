"""
MNEMOS: Pydantic Schemas
========================
All data models used across MNEMOS ingestion, graph, and API layers.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────


class FailureType(str, Enum):
    STRUCTURAL = "structural"
    GEOTECHNICAL = "geotechnical"
    HYDROLOGICAL = "hydrological"
    THERMAL = "thermal"
    MATERIAL = "material"
    HUMAN = "human"
    COMPOUND = "compound"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NodeLabel(str, Enum):
    FAILURE = "Failure"
    CONDITION = "Condition"
    CAUSE = "Cause"
    CONSEQUENCE = "Consequence"
    MATERIAL = "Material"
    PROJECT = "Project"
    PREVENTION = "Prevention"
    ENGINEER = "Engineer"


class EdgeType(str, Enum):
    CAUSES = "CAUSES"
    PRECEDED_BY = "PRECEDED_BY"
    SIMILAR_TO = "SIMILAR_TO"
    PREVENTED_BY = "PREVENTED_BY"
    OCCURRED_IN = "OCCURRED_IN"
    AFFECTED = "AFFECTED"
    CONTRIBUTED_TO = "CONTRIBUTED_TO"


# ─── Extracted Entities ───────────────────────────────────────────────────────


class ExtractedEntity(BaseModel):
    """Single entity extracted by NER from a document."""

    text: str
    label: str  # e.g. MATERIAL, HUMIDITY_LEVEL, FAILURE_MODE
    start: int
    end: int
    confidence: float = Field(ge=0.0, le=1.0)
    context: Optional[str] = None  # surrounding text snippet


class CausalChain(BaseModel):
    """A causal chain parsed from a failure report."""

    steps: List[str] = Field(description="Ordered causal chain steps")
    root_cause: str
    failure_mode: str
    source_doc: str


class FailureRecord(BaseModel):
    """A structured failure record after document processing."""

    id: Optional[str] = None
    title: str
    date: Optional[str] = None
    location: str
    country: str = "India"
    failure_type: FailureType = FailureType.UNKNOWN
    severity: Severity = Severity.HIGH
    fatalities: int = 0
    economic_loss_crore: Optional[float] = None
    description: str
    root_causes: List[str] = Field(default_factory=list)
    contributing_conditions: List[str] = Field(default_factory=list)
    materials_involved: List[str] = Field(default_factory=list)
    causal_chains: List[CausalChain] = Field(default_factory=list)
    entities: List[ExtractedEntity] = Field(default_factory=list)
    source_document: Optional[str] = None
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Graph Schemas ────────────────────────────────────────────────────────────


class GraphNode(BaseModel):
    """A node in the MNEMOS knowledge graph."""

    id: str
    label: NodeLabel
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """A directed edge in the MNEMOS knowledge graph."""

    from_id: str
    to_id: str
    edge_type: EdgeType
    properties: Dict[str, Any] = Field(default_factory=dict)
    weight: float = 1.0


class GraphSubgraph(BaseModel):
    """A subgraph returned by traversal queries."""

    nodes: List[GraphNode]
    edges: List[GraphEdge]
    query: Optional[str] = None
    traversal_depth: int = 0


# ─── API Request / Response Schemas ───────────────────────────────────────────


class IngestRequest(BaseModel):
    """Request to ingest a failure document from a URL or raw text."""

    source_type: str = Field(
        description="'text', 'pdf_path', 'pdf_url'",
        examples=["text", "pdf_path"],
    )
    content: str = Field(description="Raw text or file path to ingest")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata: location, date, severity, etc.",
    )


class IngestResponse(BaseModel):
    """Response after document ingestion."""

    status: str
    document_id: str
    failure_record: FailureRecord
    nodes_created: int
    edges_created: int
    embedding_stored: bool
    processing_time_ms: float


class QueryRequest(BaseModel):
    """Semantic query request against the knowledge base."""

    query: str = Field(description="Natural language query")
    top_k: int = Field(default=5, ge=1, le=50)
    filters: Dict[str, Any] = Field(default_factory=dict)
    include_graph_context: bool = True


class QueryResult(BaseModel):
    """Single result from a semantic query."""

    failure_id: str
    title: str
    similarity_score: float
    location: str
    failure_type: str
    severity: str
    description: str
    root_causes: List[str]
    graph_context: Optional[GraphSubgraph] = None


class QueryResponse(BaseModel):
    """Response to a semantic query."""

    query: str
    results: List[QueryResult]
    total_found: int
    processing_time_ms: float


class TraverseRequest(BaseModel):
    """Request to traverse causal chains from a starting node."""

    start_node_id: str
    direction: str = Field(default="outgoing", description="'outgoing', 'incoming', 'both'")
    max_depth: int = Field(default=3, ge=1, le=10)
    edge_types: Optional[List[EdgeType]] = None


class TraverseResponse(BaseModel):
    """Response from causal chain traversal."""

    start_node_id: str
    subgraph: GraphSubgraph
    causal_paths: List[List[str]]
    processing_time_ms: float


class HealthResponse(BaseModel):
    """Health-check response."""

    status: str
    version: str
    neo4j_connected: bool
    pinecone_connected: bool
    total_graph_nodes: int
    total_graph_edges: int
    uptime_seconds: float
