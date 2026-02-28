"""
MNEMOS: Document Ingestion Service
====================================
Orchestrates the full pipeline:
  PDF/Text input → NER → FailureRecord → Neo4j → Pinecone

Supports:
  - Plain text ingestion
  - PDF ingestion (local file or URL) via pdfplumber + PyMuPDF
  - Gemini multimodal for engineering drawings/image-rich PDFs
  - Synthetic data seeding from known failures
"""

from __future__ import annotations

import io
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from mnemos.ner.engine import NEREngine
from mnemos.schemas.models import (
    FailureRecord,
    FailureType,
    IngestResponse,
    Severity,
)


def _try_import_pdfplumber():
    try:
        import pdfplumber
        return pdfplumber
    except ImportError:
        return None


def _try_import_fitz():
    try:
        import fitz
        return fitz
    except ImportError:
        return None


class DocumentIngestionService:
    """
    Main ingestion orchestrator for MNEMOS.
    Accepts raw text, PDF paths, or structured dicts and
    drives them through the full NER → Graph → Embedding pipeline.
    """

    def __init__(
        self,
        graph_client=None,
        embedding_pipeline=None,
        use_gemini: bool = False,
    ) -> None:
        self._ner = NEREngine(use_spacy=True)
        self._graph = graph_client
        self._embeddings = embedding_pipeline
        self._use_gemini = use_gemini
        self._gemini_client = None

        if use_gemini:
            self._init_gemini()

    # ─── Gemini Integration ───────────────────────────────────────────────────

    def _init_gemini(self) -> None:
        """Initialize Gemini multimodal client for image-rich PDFs."""
        try:
            import google.generativeai as genai
            from mnemos.config import get_settings
            settings = get_settings()
            if settings.gemini_api_key:
                genai.configure(api_key=settings.gemini_api_key)
                self._gemini_client = genai.GenerativeModel(settings.gemini_model)
                logger.info(f"✅ Gemini initialized: {settings.gemini_model}")
            else:
                logger.warning("Gemini API key not set — multimodal PDF analysis disabled")
        except ImportError:
            logger.warning("google-generativeai not installed — Gemini disabled")

    # ─── PDF Extraction ───────────────────────────────────────────────────────

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file using pdfplumber, fallback to PyMuPDF."""
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        pdfplumber = _try_import_pdfplumber()
        if pdfplumber:
            try:
                with pdfplumber.open(str(path)) as pdf:
                    pages = [page.extract_text() or "" for page in pdf.pages]
                text = "\n".join(pages)
                logger.info(f"pdfplumber extracted {len(text)} chars from {path.name}")
                return text
            except Exception as e:
                logger.warning(f"pdfplumber failed: {e} — trying PyMuPDF")

        fitz = _try_import_fitz()
        if fitz:
            try:
                doc = fitz.open(str(path))
                text = "\n".join(page.get_text() for page in doc)
                logger.info(f"PyMuPDF extracted {len(text)} chars from {path.name}")
                return text
            except Exception as e:
                logger.warning(f"PyMuPDF failed: {e}")

        raise RuntimeError(f"Could not extract text from PDF: {pdf_path}")

    def _extract_text_gemini(self, pdf_path: str) -> str:
        """Use Gemini to extract structured information from image-heavy PDFs."""
        if not self._gemini_client:
            raise RuntimeError("Gemini client not initialized")

        try:
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()

            prompt = (
                "You are analyzing a construction failure forensic report. "
                "Extract all key information: failure mode, root causes, contributing conditions, "
                "materials used, location, date, fatalities, economic loss, causal chains. "
                "Return as structured text with clear sections. Be comprehensive."
            )
            # Gemini 1.5 Pro supports PDF inline data
            import google.generativeai as genai
            response = self._gemini_client.generate_content(
                [
                    {"mime_type": "application/pdf", "data": pdf_data},
                    prompt,
                ]
            )
            return response.text
        except Exception as e:
            logger.warning(f"Gemini PDF extraction failed: {e}")
            return self._extract_text_from_pdf(pdf_path)

    # ─── NER Processing ───────────────────────────────────────────────────────

    def _process_text(
        self,
        text: str,
        metadata: Dict[str, Any],
        source_doc: str = "",
    ) -> FailureRecord:
        """
        Run NER on extracted text and build a FailureRecord.
        metadata can pre-populate location, date, failure_type, etc.
        """
        entities = self._ner.extract_entities(text, source_doc)
        root_causes = self._ner.extract_root_causes(text)
        conditions = self._ner.extract_environmental_conditions(text)
        causal_chains = self._ner.extract_causal_chains(text, source_doc)

        # Extract materials from NER entities
        materials = [
            e.text for e in entities if e.label == "MATERIAL"
        ]

        # Determine failure type from entities
        failure_type = FailureType.UNKNOWN
        failure_modes = {e.text.lower() for e in entities if e.label == "FAILURE_MODE"}
        if any(t in failure_modes for t in ["scour", "settlement", "foundation"]):
            failure_type = FailureType.GEOTECHNICAL
        elif any(t in failure_modes for t in ["flood", "monsoon", "waterlogging"]):
            failure_type = FailureType.HYDROLOGICAL
        elif any(t in failure_modes for t in ["thermal", "heat", "temperature"]):
            failure_type = FailureType.THERMAL
        elif failure_modes:
            failure_type = FailureType.STRUCTURAL

        # Build description from text (first 1000 chars)
        description = text[:1000].strip().replace("\n", " ")

        record = FailureRecord(
            id=metadata.get("id", str(uuid.uuid4())),
            title=metadata.get("title", "Unnamed Failure"),
            date=metadata.get("date"),
            location=metadata.get("location", "Unknown"),
            country=metadata.get("country", "India"),
            failure_type=metadata.get("failure_type", failure_type),
            severity=metadata.get("severity", Severity.HIGH),
            fatalities=metadata.get("fatalities", 0),
            economic_loss_crore=metadata.get("economic_loss_crore"),
            description=description,
            root_causes=root_causes or metadata.get("root_causes", []),
            contributing_conditions=conditions or metadata.get("contributing_conditions", []),
            materials_involved=list(set(materials)) or metadata.get("materials_involved", []),
            causal_chains=causal_chains,
            entities=entities,
            source_document=source_doc,
        )

        return record

    # ─── Public Ingestion API ─────────────────────────────────────────────────

    def ingest_text(
        self,
        text: str,
        metadata: Dict[str, Any],
    ) -> IngestResponse:
        """Ingest raw text and store in graph + embedding index."""
        start = time.time()
        source_doc = metadata.get("source_document", "raw_text")

        logger.info(f"Ingesting text: {metadata.get('title', 'untitled')}")

        failure = self._process_text(text, metadata, source_doc)

        nodes_created = 0
        edges_created = 0
        embedding_stored = False

        if self._graph:
            failure_id = self._graph.create_failure_node(failure)
            failure.id = failure_id
            # rough estimate: 1 failure + N causes + N conditions + N materials
            nodes_created = 1 + len(failure.root_causes) + len(failure.contributing_conditions) + len(failure.materials_involved)
            edges_created = nodes_created - 1

        if self._embeddings:
            embedding_stored = self._embeddings.upsert_failure(failure)

        elapsed_ms = (time.time() - start) * 1000

        return IngestResponse(
            status="success",
            document_id=failure.id,
            failure_record=failure,
            nodes_created=nodes_created,
            edges_created=edges_created,
            embedding_stored=embedding_stored,
            processing_time_ms=round(elapsed_ms, 2),
        )

    def ingest_pdf(
        self,
        pdf_path: str,
        metadata: Dict[str, Any],
        use_gemini: bool = False,
    ) -> IngestResponse:
        """Ingest a PDF file from a local path."""
        start = time.time()
        logger.info(f"Ingesting PDF: {pdf_path}")

        if use_gemini and self._gemini_client:
            text = self._extract_text_gemini(pdf_path)
        else:
            text = self._extract_text_from_pdf(pdf_path)

        metadata.setdefault("source_document", Path(pdf_path).name)
        return self.ingest_text(text, metadata)

    def ingest_structured(self, record: FailureRecord) -> IngestResponse:
        """
        Directly ingest a pre-structured FailureRecord.
        Skips NER — useful for seeding synthetic/curated data.
        """
        start = time.time()
        logger.info(f"Ingesting structured record: {record.title}")

        if not record.id:
            record.id = str(uuid.uuid4())

        nodes_created = 0
        edges_created = 0
        embedding_stored = False

        if self._graph:
            self._graph.create_failure_node(record)
            nodes_created = 1 + len(record.root_causes) + len(record.contributing_conditions) + len(record.materials_involved)
            edges_created = max(0, nodes_created - 1)

        if self._embeddings:
            embedding_stored = self._embeddings.upsert_failure(record)

        elapsed_ms = (time.time() - start) * 1000

        return IngestResponse(
            status="success",
            document_id=record.id,
            failure_record=record,
            nodes_created=nodes_created,
            edges_created=edges_created,
            embedding_stored=embedding_stored,
            processing_time_ms=round(elapsed_ms, 2),
        )

    def batch_ingest(
        self,
        records: List[Dict[str, Any]],
        compute_similarities: bool = True,
    ) -> List[IngestResponse]:
        """
        Batch ingest multiple structured records.
        Optionally computes pairwise similarity edges.
        """
        responses = []
        ingested_ids = []

        for item in records:
            record = FailureRecord(**item)
            resp = self.ingest_structured(record)
            responses.append(resp)
            ingested_ids.append(resp.document_id)

        if compute_similarities and self._embeddings and self._graph and len(ingested_ids) > 1:
            logger.info("Computing pairwise similarity edges...")
            pairs = self._embeddings.compute_pairwise_similarity(ingested_ids)
            for id_a, id_b, score in pairs:
                self._graph.create_similarity_edge(id_a, id_b, score)
            logger.info(f"✅ Created {len(pairs)} SIMILAR_TO edges")

        return responses
