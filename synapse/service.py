"""
SYNAPSE: Orchestrator Service
================================
The main SYNAPSE service that orchestrates the full Phase 2 pipeline:

  ProjectConditions
       │
       ▼
  AnalogyEngine.retrieve_analogues()
       │
       ▼
  AnalogyEngine.extract_all_genes()
       │
       ▼
  CombinatorialSynthesizer.synthesize()
       │
       ▼
  MonteCarloSimulator.run_all()
       │
       ▼
  NoveltyDetector.fit_and_score()
       │
       ▼
  ExplainabilityEngine.generate_attributions()
       │
       ▼
  List[RiskAlert] — sorted by risk
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from loguru import logger

from synapse.explainability.attributor import ExplainabilityEngine
from synapse.novelty.detector import NoveltyDetector
from synapse.retrieval.engine import AnalogyEngine
from synapse.schemas.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    NoveltyCategory,
    ProjectConditions,
    RiskAlert,
    RiskLevel,
    SynthesisPattern,
)
from synapse.synthesis.combinatorial import CombinatorialSynthesizer
from synapse.synthesis.monte_carlo import MonteCarloSimulator


class SynapseService:
    """
    SYNAPSE orchestrator — connects all Phase 2 components.

    Stateless: all components are stateless except Isolation Forest
    fitting, which is done per-request over the generated patterns.
    """

    def __init__(
        self,
        embedding_pipeline=None,
        graph_client=None,
    ) -> None:
        self._analogy_engine = AnalogyEngine(
            embedding_pipeline=embedding_pipeline,
            graph_client=graph_client,
        )
        self._synthesizer = CombinatorialSynthesizer()
        self._monte_carlo = MonteCarloSimulator()
        self._novelty_detector = NoveltyDetector()
        self._explainer = ExplainabilityEngine()
        self._graph = graph_client
        self._embeddings = embedding_pipeline

    # ─── Core Analysis Pipeline ───────────────────────────────────────────────

    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        """
        Full SYNAPSE analysis pipeline for a given project.

        Returns a ranked list of RiskAlerts including novel patterns,
        their Monte Carlo probabilities, novelty reports, and causal attributions.
        """
        start = time.time()
        project = request.project

        logger.info(f"🔬 SYNAPSE analyzing: {project.project_name} [{project.location}]")

        # ── Step 1: Analogical Retrieval ──────────────────────────────────────
        analogues = self._analogy_engine.retrieve_analogues(
            project=project,
            top_k=request.top_k_analogues,
            min_similarity=request.min_analogue_similarity,
        )
        logger.info(f"  Retrieved {len(analogues)} analogues")

        if not analogues:
            logger.warning("No analogues found — returning empty alerts")
            total_ms = (time.time() - start) * 1000
            return AnalyzeResponse(
                project_id=project.project_id,
                project_name=project.project_name,
                total_alerts=0,
                novel_alerts=0,
                alerts=[],
                processing_time_ms=round(total_ms, 2),
                knowledge_base_size=self._get_kb_size(),
            )

        # ── Step 2: Gene Extraction ───────────────────────────────────────────
        gene_pool = self._analogy_engine.extract_all_genes(analogues, self._graph)
        total_genes = sum(len(v) for v in gene_pool.values())
        logger.info(f"  Extracted {total_genes} failure genes from {len(gene_pool)} sources")

        # ── Step 3: Combinatorial Synthesis ───────────────────────────────────
        patterns = self._synthesizer.synthesize(
            gene_pool=gene_pool,
            project=project,
            include_known=request.include_known_risks,
        )
        logger.info(f"  Synthesised {len(patterns)} risk patterns")

        if not patterns:
            logger.info("No synthesis patterns found for this project state")
            total_ms = (time.time() - start) * 1000
            return AnalyzeResponse(
                project_id=project.project_id,
                project_name=project.project_name,
                total_alerts=0,
                novel_alerts=0,
                alerts=[],
                processing_time_ms=round(total_ms, 2),
                knowledge_base_size=self._get_kb_size(),
            )

        # ── Step 4: Monte Carlo Simulation ────────────────────────────────────
        patterns = self._monte_carlo.run_all(
            patterns=patterns,
            project=project,
            iterations=request.monte_carlo_iterations,
        )

        # ── Step 5: Novelty Detection ─────────────────────────────────────────
        novelty_reports = self._novelty_detector.fit_and_score(patterns)
        # Update pattern novelty scores from detector
        novelty_map = {r.pattern_id: r for r in novelty_reports}

        # ── Step 6: Build RiskAlerts with Explainability ──────────────────────
        base_probability = float(
            sum(p.monte_carlo_probability or 0 for p in patterns) / max(len(patterns), 1)
        )

        alerts = []
        for i, pattern in enumerate(patterns):
            novelty_report = novelty_map.get(pattern.pattern_id)
            if novelty_report:
                # Sync novelty score from detector
                pattern.novelty_score = novelty_report.novelty_score
                pattern.novelty_category = novelty_report.novelty_category

            attributions = self._explainer.generate_attributions(
                pattern=pattern,
                project=project,
                base_probability=base_probability,
            )
            key_factors = self._explainer.extract_key_factors(attributions)
            interventions = self._explainer.extract_interventions(attributions, pattern)

            p90 = getattr(pattern, "__dict__", {}).get("_p90", None)

            alert = RiskAlert(
                alert_id=str(uuid.uuid4()),
                project_id=project.project_id,
                project_name=project.project_name,
                risk_name=pattern.name,
                risk_description=pattern.description,
                risk_level=pattern.risk_level,
                overall_confidence=pattern.confidence,
                novelty_score=pattern.novelty_score,
                novelty_category=pattern.novelty_category,
                analogues=analogues[:3],  # top 3 as evidence
                synthesis_pattern=pattern,
                novelty_report=novelty_report or self._novelty_detector._heuristic_report(pattern),
                predicted_failure_mode=pattern.predicted_failure_mode,
                failure_probability_30_days=pattern.monte_carlo_probability,
                failure_probability_90_days=p90,
                causal_attributions=attributions,
                key_risk_factors=key_factors,
                intervention_points=interventions,
                processing_time_ms=0.0,
            )
            alerts.append(alert)

        # Sort: critical > high > novelty score
        alerts.sort(
            key=lambda a: (
                {"critical": 4, "high": 3, "medium": 2, "low": 1, "unknown": 0}[a.risk_level.value],
                a.novelty_score,
                a.overall_confidence,
            ),
            reverse=True,
        )

        novel_count = sum(
            1 for a in alerts
            if a.novelty_category != NoveltyCategory.KNOWN
        )

        total_ms = (time.time() - start) * 1000
        for alert in alerts:
            alert.processing_time_ms = round(total_ms / len(alerts), 2)

        logger.info(
            f"✅ SYNAPSE complete: {len(alerts)} alerts ({novel_count} novel) "
            f"in {total_ms:.0f}ms"
        )

        return AnalyzeResponse(
            project_id=project.project_id,
            project_name=project.project_name,
            total_alerts=len(alerts),
            novel_alerts=novel_count,
            alerts=alerts,
            processing_time_ms=round(total_ms, 2),
            knowledge_base_size=self._get_kb_size(),
        )

    # ─── Kerala Demo ──────────────────────────────────────────────────────────

    def analyze_kerala_demo(self) -> AnalyzeResponse:
        """
        Runs the flagship demo scenario from info1.md:
        Kerala coastal viaduct — synthesising Gujarat + Medigadda + Chennai.
        """
        kerala = ProjectConditions(
            project_id="project-kerala-bridge-2025",
            project_name="Kerala Coastal Viaduct (Kochi)",
            location="Kochi, Kerala, India",
            conditions={
                "humidity": 88,
                "temperature": 39,
                "thermal_delta": 26,
                "foundation_proximity_to_water_table": "high (tidal)",
                "prestressed_storage_duration_months": 4,
                "monsoon_onset_weeks": 6,
            },
            materials=["M40 concrete", "high-tensile prestressing strands", "Fe500 TMT rebar"],
            design_parameters={"structure_type": "coastal viaduct", "span_length_m": 45},
            days_until_critical_operation=42,
            notes=(
                "Coastal site. High tidal water table. Prestressed girders stored 4 months. "
                "Monsoon season in 6 weeks. No pre-erection NDT conducted yet."
            ),
        )
        request = AnalyzeRequest(
            project=kerala,
            top_k_analogues=5,
            min_analogue_similarity=0.2,
            monte_carlo_iterations=2000,
            include_known_risks=True,
        )
        return self.analyze(request)

    def _get_kb_size(self) -> int:
        """Get total failure count from MNEMOS graph."""
        if self._graph and self._graph.is_connected:
            try:
                failures = self._graph.get_all_failures(limit=1000)
                return len(failures)
            except Exception:
                pass
        return 6  # default: 6 seed records
