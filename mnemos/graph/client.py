"""
MNEMOS: Neo4j Knowledge Graph Client
=====================================
Provides the GraphClient that manages all interactions with Neo4j.
Handles schema initialization, CRUD operations, and traversal queries.

Graph Ontology
--------------
Nodes:
  - Failure       (name, date, location, failure_type, severity, fatalities, description)
  - Condition     (name, type, value, unit)
  - Cause         (name, description, category)
  - Consequence   (name, severity, description)
  - Material      (name, grade, specification)
  - Project       (name, location, start_date, end_date, type)
  - Prevention    (name, description, cost_impact, schedule_impact)

Edges:
  - CAUSES          (Condition/Cause → Failure)
  - PRECEDED_BY     (Failure → Failure)
  - SIMILAR_TO      (Failure ↔ Failure, weight)
  - PREVENTED_BY    (Failure → Prevention)
  - OCCURRED_IN     (Failure → Project)
  - AFFECTED        (Failure → Consequence)
  - CONTRIBUTED_TO  (Condition → Cause)
"""

from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional

from loguru import logger
from neo4j import GraphDatabase, Driver, Session
from tenacity import retry, stop_after_attempt, wait_exponential

from mnemos.config import get_settings
from mnemos.schemas.models import (
    CausalChain,
    EdgeType,
    ExtractedEntity,
    FailureRecord,
    GraphEdge,
    GraphNode,
    GraphSubgraph,
    NodeLabel,
)


class GraphClient:
    """
    Thread-safe Neo4j client for the MNEMOS knowledge graph.
    Uses the official neo4j Python driver with connection pooling.
    """

    _instance: Optional["GraphClient"] = None

    def __init__(self) -> None:
        self.settings = get_settings()
        self._driver: Optional[Driver] = None
        self._connected = False
        self._connect()

    # ─── Singleton ────────────────────────────────────────────────────────────

    @classmethod
    def get_instance(cls) -> "GraphClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ─── Connection ───────────────────────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _connect(self) -> None:
        """Establish connection to Neo4j with retry logic."""
        try:
            self._driver = GraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=(self.settings.neo4j_user, self.settings.neo4j_password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
            )
            self._driver.verify_connectivity()
            self._connected = True
            logger.info(f"✅ Connected to Neo4j at {self.settings.neo4j_uri}")
            self._initialize_schema()
        except Exception as e:
            logger.warning(f"⚠️  Neo4j connection failed: {e}. Retrying…")
            self._connected = False
            raise

    @contextmanager
    def _session(self) -> Generator[Session, None, None]:
        """Context manager for a Neo4j session."""
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized")
        with self._driver.session(database=self.settings.neo4j_database) as session:
            yield session

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self._driver:
            self._driver.close()
            self._connected = False
            logger.info("Neo4j connection closed")

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ─── Schema Initialization ────────────────────────────────────────────────

    def _initialize_schema(self) -> None:
        """Create constraints and indexes on first run."""
        constraints = [
            "CREATE CONSTRAINT failure_id IF NOT EXISTS FOR (f:Failure) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT condition_id IF NOT EXISTS FOR (c:Condition) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT cause_id IF NOT EXISTS FOR (c:Cause) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT material_id IF NOT EXISTS FOR (m:Material) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT prevention_id IF NOT EXISTS FOR (pv:Prevention) REQUIRE pv.id IS UNIQUE",
        ]
        indexes = [
            "CREATE INDEX failure_location IF NOT EXISTS FOR (f:Failure) ON (f.location)",
            "CREATE INDEX failure_type IF NOT EXISTS FOR (f:Failure) ON (f.failure_type)",
            "CREATE INDEX failure_date IF NOT EXISTS FOR (f:Failure) ON (f.date)",
            "CREATE FULLTEXT INDEX failure_description IF NOT EXISTS FOR (f:Failure) ON EACH [f.description, f.title]",
        ]
        with self._session() as session:
            for stmt in constraints + indexes:
                try:
                    session.run(stmt)
                except Exception as e:
                    logger.debug(f"Schema stmt skipped (likely exists): {e}")
        logger.info("✅ Neo4j schema initialized")

    # ─── Node Operations ──────────────────────────────────────────────────────

    def create_failure_node(self, failure: FailureRecord) -> str:
        """
        Persist a FailureRecord as a Failure node + related Condition/Cause/Material nodes.
        Returns the failure node ID.
        """
        failure_id = failure.id or str(uuid.uuid4())
        failure.id = failure_id

        with self._session() as session:
            # Upsert the Failure node
            session.run(
                """
                MERGE (f:Failure {id: $id})
                SET f.title = $title,
                    f.date = $date,
                    f.location = $location,
                    f.country = $country,
                    f.failure_type = $failure_type,
                    f.severity = $severity,
                    f.fatalities = $fatalities,
                    f.economic_loss_crore = $economic_loss,
                    f.description = $description,
                    f.source_document = $source_document
                """,
                id=failure_id,
                title=failure.title,
                date=failure.date or "unknown",
                location=failure.location,
                country=failure.country,
                failure_type=failure.failure_type.value,
                severity=failure.severity.value,
                fatalities=failure.fatalities,
                economic_loss=failure.economic_loss_crore,
                description=failure.description,
                source_document=failure.source_document,
            )

            # Create root cause nodes and CAUSES edges
            for cause_text in failure.root_causes:
                cause_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, cause_text))
                session.run(
                    """
                    MERGE (c:Cause {id: $cause_id})
                    SET c.name = $cause_name
                    WITH c
                    MATCH (f:Failure {id: $failure_id})
                    MERGE (c)-[:CAUSES {created: timestamp()}]->(f)
                    """,
                    cause_id=cause_id,
                    cause_name=cause_text,
                    failure_id=failure_id,
                )

            # Create environmental condition nodes
            for condition_text in failure.contributing_conditions:
                cond_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, condition_text))
                session.run(
                    """
                    MERGE (cond:Condition {id: $cond_id})
                    SET cond.name = $cond_name
                    WITH cond
                    MATCH (f:Failure {id: $failure_id})
                    MERGE (cond)-[:CONTRIBUTED_TO {created: timestamp()}]->(f)
                    """,
                    cond_id=cond_id,
                    cond_name=condition_text,
                    failure_id=failure_id,
                )

            # Create material nodes
            for material_text in failure.materials_involved:
                mat_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, material_text))
                session.run(
                    """
                    MERGE (m:Material {id: $mat_id})
                    SET m.name = $mat_name
                    WITH m
                    MATCH (f:Failure {id: $failure_id})
                    MERGE (f)-[:USED_MATERIAL {created: timestamp()}]->(m)
                    """,
                    mat_id=mat_id,
                    mat_name=material_text,
                    failure_id=failure_id,
                )

        logger.info(f"✅ Failure node created: {failure.title} [{failure_id}]")
        return failure_id

    def create_similarity_edge(
        self,
        failure_id_a: str,
        failure_id_b: str,
        similarity_score: float,
    ) -> None:
        """Create or update a SIMILAR_TO edge between two failure nodes."""
        with self._session() as session:
            session.run(
                """
                MATCH (a:Failure {id: $id_a}), (b:Failure {id: $id_b})
                MERGE (a)-[r:SIMILAR_TO]-(b)
                SET r.score = $score, r.updated = timestamp()
                """,
                id_a=failure_id_a,
                id_b=failure_id_b,
                score=similarity_score,
            )

    # ─── Query Operations ─────────────────────────────────────────────────────

    def get_all_failures(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve all failure nodes with their properties."""
        with self._session() as session:
            result = session.run(
                "MATCH (f:Failure) RETURN f ORDER BY f.date DESC LIMIT $limit",
                limit=limit,
            )
            return [dict(record["f"]) for record in result]

    def get_failure_by_id(self, failure_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single failure node by ID."""
        with self._session() as session:
            result = session.run(
                "MATCH (f:Failure {id: $id}) RETURN f",
                id=failure_id,
            )
            record = result.single()
            return dict(record["f"]) if record else None

    def search_failures_by_text(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Full-text search over failure descriptions and titles."""
        with self._session() as session:
            result = session.run(
                """
                CALL db.index.fulltext.queryNodes("failure_description", $query)
                YIELD node, score
                RETURN node AS f, score
                ORDER BY score DESC
                LIMIT $limit
                """,
                query=query,
                limit=limit,
            )
            return [{"node": dict(r["f"]), "score": r["score"]} for r in result]

    def traverse_causal_chain(
        self,
        start_node_id: str,
        max_depth: int = 3,
        edge_types: Optional[List[str]] = None,
        direction: str = "outgoing",
    ) -> GraphSubgraph:
        """
        Traverse the causal chain starting from a given failure node.
        Returns a GraphSubgraph with nodes and edges.
        """
        edge_filter = "|".join(edge_types) if edge_types else "CAUSES|CONTRIBUTED_TO|PRECEDED_BY"

        if direction == "outgoing":
            pattern = f"-[r:{edge_filter}*1..{max_depth}]->"
        elif direction == "incoming":
            pattern = f"<-[r:{edge_filter}*1..{max_depth}]-"
        else:
            pattern = f"-[r:{edge_filter}*1..{max_depth}]-"

        cypher = f"""
        MATCH path = (start {{id: $start_id}}){pattern}(end)
        RETURN nodes(path) AS nodes, relationships(path) AS rels
        LIMIT 500
        """

        nodes: Dict[str, GraphNode] = {}
        edges: List[GraphEdge] = []
        paths: List[List[str]] = []

        with self._session() as session:
            result = session.run(cypher, start_id=start_node_id)
            for record in result:
                path_ids = []
                for node in record["nodes"]:
                    node_id = node.element_id
                    if node_id not in nodes:
                        label = list(node.labels)[0] if node.labels else "Unknown"
                        nodes[node_id] = GraphNode(
                            id=node_id,
                            label=NodeLabel(label) if label in NodeLabel.__members__.values() else NodeLabel.FAILURE,
                            properties=dict(node),
                        )
                    path_ids.append(node_id)
                paths.append(path_ids)

                for rel in record["rels"]:
                    edges.append(
                        GraphEdge(
                            from_id=rel.start_node.element_id,
                            to_id=rel.end_node.element_id,
                            edge_type=EdgeType(rel.type) if rel.type in EdgeType.__members__ else EdgeType.CAUSES,
                            properties=dict(rel),
                        )
                    )

        return GraphSubgraph(
            nodes=list(nodes.values()),
            edges=edges,
            query=f"traverse:{start_node_id}",
            traversal_depth=max_depth,
        )

    def get_node_count(self) -> int:
        """Return total node count in the graph."""
        with self._session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS count")
            record = result.single()
            return record["count"] if record else 0

    def get_edge_count(self) -> int:
        """Return total relationship count in the graph."""
        with self._session() as session:
            result = session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            record = result.single()
            return record["count"] if record else 0

    def find_similar_failures(
        self,
        failure_id: str,
        min_score: float = 0.5,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find failures connected by SIMILAR_TO edges above a score threshold."""
        with self._session() as session:
            result = session.run(
                """
                MATCH (f:Failure {id: $id})-[r:SIMILAR_TO]-(similar:Failure)
                WHERE r.score >= $min_score
                RETURN similar, r.score AS score
                ORDER BY score DESC
                LIMIT $limit
                """,
                id=failure_id,
                min_score=min_score,
                limit=limit,
            )
            return [
                {"failure": dict(r["similar"]), "score": r["score"]}
                for r in result
            ]
