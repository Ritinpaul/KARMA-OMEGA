"""
SYNAPSE: Analogical Retrieval Engine
======================================
Encodes current project conditions as a vector and retrieves
the top-K most similar historical failures from MNEMOS.

Also extracts 'failure genes' — the atomic risk contributions
from each analogue that are used by the combinatorial synthesizer.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

from synapse.schemas.models import AnalogueMatch, FailureGene, ProjectConditions


# ─── Condition → Gene Mappings ────────────────────────────────────────────────

GENE_DEFINITIONS = {
    "humidity_sensitivity": {
        "keywords": ["humidity", "moisture", "damp", "wet", "condensation"],
        "description": "Concrete strength degradation under high ambient humidity",
    },
    "foundation_scour": {
        "keywords": ["scour", "erosion", "foundation", "settlement", "bearing capacity", "bedrock"],
        "description": "Sub-foundation material loss under hydrodynamic action",
    },
    "thermal_cracking": {
        "keywords": ["thermal", "temperature", "heat", "cycling", "delta", "shrinkage"],
        "description": "Thermally induced micro-cracking from temperature differentials",
    },
    "premature_loading": {
        "keywords": ["premature loading", "early loading", "formwork removal", "curing"],
        "description": "Loading before design strength is achieved",
    },
    "chloride_corrosion": {
        "keywords": ["chloride", "corrosion", "coastal", "salt", "carbonation"],
        "description": "Steel reinforcement corrosion via chloride ingress",
    },
    "seismic_amplification": {
        "keywords": ["seismic", "earthquake", "vibration", "resonance", "dynamic"],
        "description": "Seismic demand amplification in soft soil layers",
    },
    "design_error": {
        "keywords": ["design error", "stress concentration", "inadequate", "not accounted", "underestimated"],
        "description": "Systematic error in structural design or analysis",
    },
    "inspection_gap": {
        "keywords": ["inspection", "maintenance", "monitoring", "ndt", "non-destructive"],
        "description": "Failure to detect deterioration through inadequate inspection",
    },
    "construction_sequence": {
        "keywords": ["sequence", "erection", "launching", "installation", "sequence error"],
        "description": "Incorrect construction sequencing creating unintended load paths",
    },
    "material_degradation": {
        "keywords": ["degradation", "aging", "deterioration", "fatigue", "creep", "stress relaxation"],
        "description": "Time-dependent material property loss",
    },
}


class AnalogyEngine:
    """
    Retrieves historical failure analogues for a given project state.
    Uses the MNEMOS embedding pipeline for vector similarity retrieval.
    Then extracts domain-specific 'failure genes' from each analogue.
    """

    def __init__(self, embedding_pipeline=None, graph_client=None) -> None:
        self._embeddings = embedding_pipeline
        self._graph = graph_client

    # ─── Project State → Text ─────────────────────────────────────────────────

    def _project_to_text(self, project: ProjectConditions) -> str:
        """Convert project conditions into a rich text representation for embedding."""
        parts = [
            f"Project: {project.project_name}",
            f"Location: {project.location}",
        ]
        for key, value in project.conditions.items():
            parts.append(f"{key}: {value}")
        if project.materials:
            parts.append("Materials: " + ", ".join(project.materials))
        for key, val in project.design_parameters.items():
            parts.append(f"{key}: {val}")
        if project.notes:
            parts.append(f"Notes: {project.notes}")
        return " | ".join(parts)

    # ─── Analogue Retrieval ───────────────────────────────────────────────────

    def retrieve_analogues(
        self,
        project: ProjectConditions,
        top_k: int = 5,
        min_similarity: float = 0.3,
    ) -> List[AnalogueMatch]:
        """
        Retrieve top-K historical failures most similar to the project state.
        Falls back to mock data if MNEMOS is unavailable.
        """
        if self._embeddings is None:
            logger.warning("Embedding pipeline not available — using fallback analogues")
            return self._fallback_analogues(project, top_k)

        query_text = self._project_to_text(project)

        try:
            raw_results = self._embeddings.search(query=query_text, top_k=top_k)
        except Exception as e:
            logger.warning(f"Vector search failed: {e} — using fallback analogues")
            return self._fallback_analogues(project, top_k)

        analogues = []
        for r in raw_results:
            if r["score"] < min_similarity:
                continue

            meta = r.get("metadata", {})
            failure_id = r["id"]

            # Try to enrich with full node from graph
            description_snippet = ""
            if self._graph and self._graph.is_connected:
                try:
                    node = self._graph.get_failure_by_id(failure_id)
                    if node:
                        description_snippet = node.get("description", "")[:200]
                except Exception:
                    pass

            # Compute condition overlap
            matching_conditions = self._match_conditions(
                project.conditions, meta.get("conditions", {})
            )

            analogues.append(
                AnalogueMatch(
                    failure_id=failure_id,
                    title=meta.get("title", "Unknown Failure"),
                    location=meta.get("location", "Unknown"),
                    date=meta.get("date"),
                    failure_type=meta.get("failure_type", "unknown"),
                    similarity_score=round(r["score"], 4),
                    matching_conditions=matching_conditions,
                    causal_overlap=min(r["score"] * 0.8, 0.95),
                    description_snippet=description_snippet,
                )
            )

        return sorted(analogues, key=lambda a: a.similarity_score, reverse=True)

    def _match_conditions(
        self,
        project_conditions: Dict[str, Any],
        historical_conditions: Dict[str, Any],
    ) -> List[str]:
        """Identify overlapping condition keys between project and historical failure."""
        if not historical_conditions:
            return []
        proj_keys = {k.lower() for k in project_conditions}
        hist_keys = {k.lower() for k in historical_conditions}
        return list(proj_keys & hist_keys)

    def _fallback_analogues(
        self,
        project: ProjectConditions,
        top_k: int,
    ) -> List[AnalogueMatch]:
        """
        Returns curated analogues from the 5 seed failures when MNEMOS is offline.
        Scores are based on heuristic condition matching.
        """
        from synapse.retrieval._seed_analogues import get_seed_analogues
        return get_seed_analogues(project, top_k)

    # ─── Gene Extraction ──────────────────────────────────────────────────────

    def extract_genes(
        self,
        analogue: AnalogueMatch,
        description: str = "",
    ) -> List[FailureGene]:
        """
        Extract 'failure genes' from a historical analogue.
        Each gene represents an atomic, transferable risk contribution.
        """
        combined_text = (
            f"{analogue.title} {analogue.failure_type} "
            f"{' '.join(analogue.matching_conditions)} {description}"
        ).lower()

        genes = []
        for gene_type, gene_def in GENE_DEFINITIONS.items():
            matches = [kw for kw in gene_def["keywords"] if kw in combined_text]
            if matches:
                # Gene intensity ∝ similarity_score × keyword density
                intensity = min(
                    analogue.similarity_score * (len(matches) / len(gene_def["keywords"])) * 2,
                    1.0,
                )
                genes.append(
                    FailureGene(
                        source_failure_id=analogue.failure_id,
                        source_title=analogue.title,
                        gene_type=gene_type,
                        gene_value=round(intensity, 4),
                        description=gene_def["description"],
                        conditions=analogue.matching_conditions + matches,
                    )
                )

        # Always include at least one gene from the failure type
        if not genes:
            genes.append(
                FailureGene(
                    source_failure_id=analogue.failure_id,
                    source_title=analogue.title,
                    gene_type="material_degradation",
                    gene_value=round(analogue.similarity_score * 0.5, 4),
                    description="General structural/material degradation risk",
                    conditions=analogue.matching_conditions,
                )
            )

        return genes

    def extract_all_genes(
        self,
        analogues: List[AnalogueMatch],
        graph_client=None,
    ) -> Dict[str, List[FailureGene]]:
        """
        Extract genes from all analogues.
        Returns a dict keyed by failure_id → List[FailureGene].
        """
        all_genes: Dict[str, List[FailureGene]] = {}
        for analogue in analogues:
            description = ""
            if graph_client and graph_client.is_connected:
                try:
                    node = graph_client.get_failure_by_id(analogue.failure_id)
                    if node:
                        description = node.get("description", "")
                except Exception:
                    pass
            all_genes[analogue.failure_id] = self.extract_genes(analogue, description)
        return all_genes
