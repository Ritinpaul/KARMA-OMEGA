"""
MNEMOS: Sentence-BERT Embedding Pipeline
=========================================
Generates dense vector embeddings for failure records and queries.
Uses sentence-transformers/all-mpnet-base-v2 (768-dim).

Also manages Pinecone vector index for similarity retrieval.
Falls back gracefully to in-memory cosine search when Pinecone unavailable.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple

import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from tenacity import retry, stop_after_attempt, wait_exponential

from mnemos.config import get_settings
from mnemos.schemas.models import FailureRecord


class EmbeddingPipeline:
    """
    Dual-mode embedding pipeline:
      - **Primary**: Pinecone for production-scale vector similarity
      - **Fallback**: In-memory numpy index for dev / offline mode
    """

    _instance: Optional["EmbeddingPipeline"] = None

    def __init__(self) -> None:
        self.settings = get_settings()
        self._model: Optional[SentenceTransformer] = None
        self._pinecone_index = None
        self._memory_index: Dict[str, Tuple[np.ndarray, Dict]] = {}
        self._pinecone_available = False

        self._load_model()
        self._init_pinecone()

    @classmethod
    def get_instance(cls) -> "EmbeddingPipeline":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ─── Model Loading ────────────────────────────────────────────────────────

    def _load_model(self) -> None:
        """Load Sentence-BERT model (downloads on first run)."""
        try:
            logger.info(f"Loading embedding model: {self.settings.hf_model_name}")
            self._model = SentenceTransformer(
                self.settings.hf_model_name,
                cache_folder=self.settings.hf_cache_dir,
            )
            logger.info("✅ Embedding model loaded")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    # ─── Pinecone Initialization ──────────────────────────────────────────────

    def _init_pinecone(self) -> None:
        """Initialize Pinecone index (graceful fallback if unavailable)."""
        if not self.settings.pinecone_api_key:
            logger.warning("Pinecone API key not set — using in-memory fallback index")
            return

        try:
            from pinecone import Pinecone, ServerlessSpec

            pc = Pinecone(api_key=self.settings.pinecone_api_key)
            index_name = self.settings.pinecone_index_name

            existing = [idx.name for idx in pc.list_indexes()]
            if index_name not in existing:
                logger.info(f"Creating Pinecone index: {index_name}")
                pc.create_index(
                    name=index_name,
                    dimension=self.settings.embedding_dim,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region=self.settings.pinecone_environment),
                )

            self._pinecone_index = pc.Index(index_name)
            self._pinecone_available = True
            logger.info(f"✅ Pinecone index ready: {index_name}")
        except ImportError:
            logger.warning("pinecone-client not installed — using in-memory fallback index")
        except Exception as e:
            logger.warning(f"Pinecone init failed: {e} — using in-memory fallback index")

    # ─── Embedding Generation ─────────────────────────────────────────────────

    def encode(self, text: str) -> np.ndarray:
        """Encode a single text string into a dense vector."""
        if not self._model:
            raise RuntimeError("Embedding model not loaded")
        return self._model.encode(text, normalize_embeddings=True)

    def encode_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Encode a list of texts into a matrix of embeddings."""
        if not self._model:
            raise RuntimeError("Embedding model not loaded")
        return self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 10,
        )

    def build_failure_text(self, failure: FailureRecord) -> str:
        """
        Build a single enriched text representation of a failure record
        for embedding. Combines title, location, description, causes, conditions.
        """
        parts = [
            f"Failure: {failure.title}",
            f"Location: {failure.location}, {failure.country}",
            f"Type: {failure.failure_type.value}",
            f"Description: {failure.description}",
        ]
        if failure.root_causes:
            parts.append("Root causes: " + "; ".join(failure.root_causes))
        if failure.contributing_conditions:
            parts.append("Conditions: " + "; ".join(failure.contributing_conditions))
        if failure.materials_involved:
            parts.append("Materials: " + "; ".join(failure.materials_involved))
        return " | ".join(parts)

    # ─── Index Operations ─────────────────────────────────────────────────────

    def upsert_failure(self, failure: FailureRecord) -> bool:
        """
        Generate embedding for a failure record and store in Pinecone or memory.
        Returns True if successfully stored.
        """
        if not failure.id:
            raise ValueError("Failure must have an ID before upserting")

        text = self.build_failure_text(failure)
        vector = self.encode(text)
        failure.embedding = vector.tolist()

        metadata = {
            "title": failure.title,
            "location": failure.location,
            "failure_type": failure.failure_type.value,
            "severity": failure.severity.value,
            "date": failure.date or "unknown",
            "fatalities": failure.fatalities,
        }

        if self._pinecone_available and self._pinecone_index:
            try:
                self._pinecone_index.upsert(
                    vectors=[
                        {
                            "id": failure.id,
                            "values": failure.embedding,
                            "metadata": metadata,
                        }
                    ]
                )
                logger.debug(f"📌 Upserted to Pinecone: {failure.id}")
                return True
            except Exception as e:
                logger.warning(f"Pinecone upsert failed: {e} — storing in memory")

        # Memory fallback
        self._memory_index[failure.id] = (vector, {"id": failure.id, **metadata})
        logger.debug(f"📌 Upserted to memory index: {failure.id}")
        return True

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Semantic search for similar failures.
        Returns list of dicts with id, score, and metadata.
        """
        query_vector = self.encode(query)

        if self._pinecone_available and self._pinecone_index:
            return self._pinecone_search(query_vector, top_k, filters)

        return self._memory_search(query_vector, top_k)

    def _pinecone_search(
        self,
        query_vector: np.ndarray,
        top_k: int,
        filters: Optional[Dict],
    ) -> List[Dict]:
        """Search via Pinecone."""
        try:
            response = self._pinecone_index.query(
                vector=query_vector.tolist(),
                top_k=top_k,
                include_metadata=True,
                filter=filters,
            )
            results = []
            for match in response.matches:
                results.append(
                    {
                        "id": match.id,
                        "score": match.score,
                        "metadata": match.metadata,
                    }
                )
            return results
        except Exception as e:
            logger.warning(f"Pinecone search failed: {e} — falling back to memory")
            return self._memory_search(query_vector, top_k)

    def _memory_search(
        self,
        query_vector: np.ndarray,
        top_k: int,
    ) -> List[Dict]:
        """Search via in-memory cosine similarity."""
        if not self._memory_index:
            return []

        ids = list(self._memory_index.keys())
        vectors = np.array([self._memory_index[i][0] for i in ids])
        scores = cosine_similarity([query_vector], vectors)[0]

        ranked = sorted(zip(ids, scores), key=lambda x: x[1], reverse=True)[:top_k]
        return [
            {
                "id": rid,
                "score": float(score),
                "metadata": self._memory_index[rid][1],
            }
            for rid, score in ranked
        ]

    def compute_pairwise_similarity(
        self,
        failure_ids: List[str],
    ) -> List[Tuple[str, str, float]]:
        """
        Compute pairwise cosine similarity for a list of failure IDs.
        Returns list of (id_a, id_b, score) tuples above 0.5 threshold.
        """
        indexed = {
            fid: data[0]
            for fid, data in self._memory_index.items()
            if fid in failure_ids
        }
        if not indexed:
            return []

        ids = list(indexed.keys())
        vectors = np.array([indexed[i] for i in ids])
        sim_matrix = cosine_similarity(vectors)

        pairs = []
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                score = float(sim_matrix[i][j])
                if score >= 0.5:
                    pairs.append((ids[i], ids[j], score))
        return sorted(pairs, key=lambda x: x[2], reverse=True)

    @property
    def is_pinecone_active(self) -> bool:
        return self._pinecone_available
