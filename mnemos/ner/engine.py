"""
MNEMOS: Named Entity Recognition (NER) Engine
==============================================
Extracts domain-specific entities from construction failure documents.

Uses a rule-based + spaCy hybrid approach for engineering domain NER:
  - FAILURE_MODE     (collapse, scour, failure, crack, buckling...)
  - MATERIAL         (M30 concrete, TMT rebar, prestressed...)
  - CONDITION        (humidity, temperature, load, vibration...)
  - LOCATION         (Gujarat, Chennai, Kerala, Delhi...)
  - DATE_REF         (2019, monsoon season, post-pour...)
  - ROOT_CAUSE       (premature loading, foundation scour...)
  - SEVERITY_MARKER  (critical, fatal, structural, cosmetic...)

Also provides CausalChain extraction via heuristic sentence parsing.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from loguru import logger

from mnemos.schemas.models import CausalChain, ExtractedEntity


# ─── Domain Dictionaries ──────────────────────────────────────────────────────

FAILURE_MODES = [
    "collapse", "failure", "cracking", "buckling", "scour", "settlement",
    "spalling", "corrosion", "delamination", "fracture", "shear failure",
    "torsional failure", "flexural failure", "punching shear", "debonding",
    "honeycombing", "segregation", "plastic shrinkage", "creep failure",
    "fatigue failure", "overloading", "progressive collapse", "liquefaction",
    "sinkhole", "foundation failure", "bearing capacity failure",
]

MATERIALS = [
    "concrete", "reinforced concrete", "prestressed concrete", "M15", "M20",
    "M25", "M30", "M35", "M40", "M45", "HSC", "HPC", "SCC", "UHPC",
    "TMT rebar", "HYSD bar", "Fe415", "Fe500", "Fe550", "structural steel",
    "SAIL", "TATA steel", "Portland cement", "OPC", "PPC", "PSC",
    "fly ash", "silica fume", "slag", "admixture", "superplasticizer",
    "bitumen", "asphalt", "pre-tensioned", "post-tensioned", "GFRP",
]

CONDITIONS = [
    "humidity", "temperature", "heat", "monsoon", "rainfall", "flood",
    "seismic", "earthquake", "vibration", "wind", "corrosive environment",
    "chloride attack", "sulfate attack", "alkali silica reaction",
    "carbonation", "freeze thaw", "thermal cycling", "differential settlement",
    "high groundwater", "scour", "erosion", "overloading", "dynamic loading",
    "fatigue loading", "impact loading",
]

ROOT_CAUSE_PATTERNS = [
    r"root cause[:\s]+(.+?)(?:\.|$)",
    r"caused by[:\s]+(.+?)(?:\.|$)",
    r"due to[:\s]+(.+?)(?:\.|$)",
    r"attributed to[:\s]+(.+?)(?:\.|$)",
    r"primary cause[:\s]+(.+?)(?:\.|$)",
    r"underlying cause[:\s]+(.+?)(?:\.|$)",
    r"investigation found[:\s]+(.+?)(?:\.|$)",
    r"forensic analysis revealed[:\s]+(.+?)(?:\.|$)",
]

CAUSAL_CONNECTORS = [
    "→", "->", "led to", "resulted in", "caused", "triggered",
    "initiated", "propagated to", "culminated in", "followed by",
]

INDIA_LOCATIONS = [
    "Gujarat", "Maharashtra", "Tamil Nadu", "Chennai", "Mumbai", "Delhi",
    "Bengaluru", "Bangalore", "Hyderabad", "Kerala", "Kochi", "Pune",
    "Ahmedabad", "Surat", "Kolkata", "Jaipur", "Lucknow", "Bhopal",
    "Medigadda", "Telangana", "Andhra Pradesh", "Rajasthan", "UP", "Bihar",
    "West Bengal", "Odisha", "Assam", "Punjab", "Haryana",
]


# ─── NER Engine ───────────────────────────────────────────────────────────────


class NEREngine:
    """
    Domain-specific NER for construction engineering failure reports.
    Combines rule-based pattern matching with optional spaCy integration.
    """

    def __init__(self, use_spacy: bool = True) -> None:
        self._nlp = None
        if use_spacy:
            self._load_spacy()

        # Compile patterns for efficiency
        self._failure_pattern = re.compile(
            "|".join(re.escape(f) for f in FAILURE_MODES), re.IGNORECASE
        )
        self._material_pattern = re.compile(
            "|".join(re.escape(m) for m in MATERIALS), re.IGNORECASE
        )
        self._condition_pattern = re.compile(
            "|".join(re.escape(c) for c in CONDITIONS), re.IGNORECASE
        )
        self._location_pattern = re.compile(
            r"\b(" + "|".join(re.escape(l) for l in INDIA_LOCATIONS) + r")\b",
            re.IGNORECASE,
        )
        self._date_pattern = re.compile(
            r"\b(19|20)\d{2}\b|\b(January|February|March|April|May|June|July|August|"
            r"September|October|November|December)\s+\d{4}\b|\bQ[1-4]\s+\d{4}\b",
            re.IGNORECASE,
        )
        self._root_cause_patterns = [
            re.compile(p, re.IGNORECASE) for p in ROOT_CAUSE_PATTERNS
        ]

    def _load_spacy(self) -> None:
        """Load spaCy model if available."""
        try:
            import spacy
            self._nlp = spacy.load("en_core_web_sm")
            logger.info("✅ spaCy model loaded: en_core_web_sm")
        except OSError:
            logger.warning(
                "spaCy 'en_core_web_sm' not found. "
                "Run: python -m spacy download en_core_web_sm\n"
                "Falling back to rule-based NER only."
            )
        except ImportError:
            logger.warning("spaCy not installed. Using rule-based NER only.")

    # ─── Entity Extraction ────────────────────────────────────────────────────

    def extract_entities(self, text: str, source_doc: str = "") -> List[ExtractedEntity]:
        """
        Extract all domain entities from a text block.
        Returns a deduplicated list of ExtractedEntity objects.
        """
        entities: List[ExtractedEntity] = []

        # Rule-based extraction
        entities.extend(self._extract_by_pattern(text, self._failure_pattern, "FAILURE_MODE"))
        entities.extend(self._extract_by_pattern(text, self._material_pattern, "MATERIAL"))
        entities.extend(self._extract_by_pattern(text, self._condition_pattern, "CONDITION"))
        entities.extend(self._extract_by_pattern(text, self._location_pattern, "LOCATION"))
        entities.extend(self._extract_by_pattern(text, self._date_pattern, "DATE_REF"))

        # spaCy-based extraction (person names, org names, etc.)
        if self._nlp:
            entities.extend(self._extract_spacy_entities(text))

        # Deduplicate by (text, label)
        seen = set()
        unique: List[ExtractedEntity] = []
        for e in entities:
            key = (e.text.lower().strip(), e.label)
            if key not in seen:
                seen.add(key)
                unique.append(e)

        return unique

    def _extract_by_pattern(
        self,
        text: str,
        pattern: re.Pattern,
        label: str,
    ) -> List[ExtractedEntity]:
        """Helper: extract entities matching a compiled pattern."""
        entities = []
        for match in pattern.finditer(text):
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            entities.append(
                ExtractedEntity(
                    text=match.group(),
                    label=label,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.85,
                    context=text[start:end],
                )
            )
        return entities

    def _extract_spacy_entities(self, text: str) -> List[ExtractedEntity]:
        """Extract spaCy NER entities (ORG, PERSON, GPE, etc.)."""
        if not self._nlp:
            return []
        doc = self._nlp(text[:100_000])  # cap at 100k chars
        entities = []
        for ent in doc.ents:
            if ent.label_ in {"ORG", "PERSON", "GPE", "LAW", "PRODUCT"}:
                entities.append(
                    ExtractedEntity(
                        text=ent.text,
                        label=f"spacy:{ent.label_}",
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=0.75,
                        context=text[max(0, ent.start_char - 30): ent.end_char + 30],
                    )
                )
        return entities

    # ─── Root Cause Extraction ────────────────────────────────────────────────

    def extract_root_causes(self, text: str) -> List[str]:
        """Extract explicit root cause statements using regex heuristics."""
        causes = []
        for pattern in self._root_cause_patterns:
            for match in pattern.finditer(text):
                cause = match.group(1).strip().strip(".")
                if len(cause) > 5:
                    causes.append(cause)
        return list(dict.fromkeys(causes))  # deduplicate preserving order

    # ─── Causal Chain Extraction ──────────────────────────────────────────────

    def extract_causal_chains(
        self,
        text: str,
        source_doc: str = "",
    ) -> List[CausalChain]:
        """
        Extract causal chains from text.
        Looks for explicit arrow patterns or keyword connectors.
        """
        chains = []
        sentences = re.split(r"[.!?]\s+", text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Check for arrow-style causal chains: "A → B → C"
            if "→" in sentence or "->" in sentence:
                sentence_norm = sentence.replace("->", "→")
                steps = [s.strip() for s in sentence_norm.split("→") if s.strip()]
                if len(steps) >= 2:
                    chains.append(
                        CausalChain(
                            steps=steps,
                            root_cause=steps[0],
                            failure_mode=steps[-1],
                            source_doc=source_doc,
                        )
                    )
                continue

            # Check for keyword-based causal descriptions
            for connector in CAUSAL_CONNECTORS[2:]:  # skip arrows already handled
                if connector in sentence.lower():
                    parts = re.split(
                        re.escape(connector), sentence, flags=re.IGNORECASE, maxsplit=1
                    )
                    if len(parts) == 2:
                        cause = parts[0].strip()
                        effect = parts[1].strip()
                        if len(cause) > 3 and len(effect) > 3:
                            chains.append(
                                CausalChain(
                                    steps=[cause, effect],
                                    root_cause=cause,
                                    failure_mode=effect,
                                    source_doc=source_doc,
                                )
                            )
                    break

        return chains

    # ─── Structured Condition Extraction ─────────────────────────────────────

    def extract_environmental_conditions(self, text: str) -> List[str]:
        """
        Extract environmental and operational conditions from text.
        Returns clean condition description strings.
        """
        conditions = []
        # Numeric values with units (humidity 85%, temp 42°C, etc.)
        numeric_pattern = re.compile(
            r"(humidity|temperature|wind speed|rainfall|groundwater|load|stress|"
            r"pressure|vibration|frequency)[:\s]+([\d.]+\s*[%°℃℉kNm²/s]?)",
            re.IGNORECASE,
        )
        for match in numeric_pattern.finditer(text):
            conditions.append(f"{match.group(1).lower()}: {match.group(2).strip()}")

        # Categorical conditions
        for match in self._condition_pattern.finditer(text):
            val = match.group().lower().strip()
            if val not in [c.lower() for c in conditions]:
                conditions.append(val)

        return list(dict.fromkeys(conditions))
