"""
SYNAPSE: Seed Analogues Fallback
==================================
Returns heuristically scored analogues from the 5 curated seed failures
when the MNEMOS embedding pipeline is offline.
"""

from __future__ import annotations

from typing import Any, Dict, List

from synapse.schemas.models import AnalogueMatch, ProjectConditions

_SEED_FAILURES = [
    {
        "id": "failure-gujarat-bridge-2019",
        "title": "Gujarat Bridge Collapse 2019",
        "location": "Gujarat, India",
        "date": "2019-04-15",
        "failure_type": "structural",
        "keywords": ["humidity", "curing", "premature loading", "formwork", "concrete", "temperature"],
        "description": "Premature formwork removal under 92% humidity caused low early concrete strength and collapse.",
    },
    {
        "id": "failure-medigadda-barrage-2021",
        "title": "Medigadda Barrage Foundation Failure 2021",
        "location": "Medigadda, Telangana, India",
        "date": "2021-10-08",
        "failure_type": "geotechnical",
        "keywords": ["foundation", "scour", "monsoon", "settlement", "water table", "flood", "alluvial"],
        "description": "Q100 monsoon flood caused scour beyond design depth, collapsing foundation of Pier 7.",
    },
    {
        "id": "failure-chennai-girder-2024",
        "title": "Chennai Elevated Corridor Girder Collapse 2024",
        "location": "Chennai, Tamil Nadu, India",
        "date": "2024-02-20",
        "failure_type": "structural",
        "keywords": ["thermal", "temperature", "cycling", "delta", "prestressed", "erection", "storage", "cracking"],
        "description": "Thermal micro-cracks from ΔT=28°C daily cycling combined with erection sequence error.",
    },
    {
        "id": "failure-fiu-bridge-usa-2018",
        "title": "FIU Pedestrian Bridge Collapse, Miami 2018",
        "location": "Miami, Florida, USA",
        "date": "2018-03-15",
        "failure_type": "structural",
        "keywords": ["design error", "stress concentration", "crack", "post-tensioning", "sequence"],
        "description": "Design error at diagonal node combined with PT re-tensioning caused progressive collapse.",
    },
    {
        "id": "failure-genoa-morandi-italy-2018",
        "title": "Genoa Morandi Bridge Collapse 2018",
        "location": "Genoa, Italy",
        "date": "2018-08-14",
        "failure_type": "structural",
        "keywords": ["corrosion", "chloride", "coastal", "inspection", "maintenance", "aging"],
        "description": "50-year chloride corrosion of hidden steel stays inside concrete casing caused collapse.",
    },
]


def _score_failure(
    failure: Dict,
    project: ProjectConditions,
) -> float:
    """
    Heuristic similarity score for a seed failure against a project.
    Counts keyword hits from project conditions against failure keywords.
    """
    project_text = (
        " ".join(str(v) for v in project.conditions.values()) + " "
        + " ".join(project.materials) + " "
        + " ".join(str(v) for v in project.design_parameters.values()) + " "
        + (project.notes or "")
    ).lower()

    hits = sum(1 for kw in failure["keywords"] if kw in project_text)
    base_score = hits / max(len(failure["keywords"]), 1)

    # Location bonus: same country
    loc_text = project.location.lower()
    if "india" in loc_text or "india" in failure["location"].lower():
        base_score = min(base_score + 0.1, 1.0)

    return round(min(base_score * 1.5 + 0.1, 1.0), 4)


def get_seed_analogues(
    project: ProjectConditions,
    top_k: int = 5,
) -> List[AnalogueMatch]:
    """Return top-K seed analogues scored against the project conditions."""
    # Build a single rich project text for matching
    project_text = (
        project.location.lower() + " "
        + " ".join(str(k) + " " + str(v) for k, v in project.conditions.items()).lower() + " "
        + " ".join(project.materials).lower() + " "
        + " ".join(str(v) for v in project.design_parameters.values()).lower() + " "
        + (project.notes or "").lower()
    )

    scored = [
        (_score_failure(f, project), f)
        for f in _SEED_FAILURES
    ]
    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        AnalogueMatch(
            failure_id=f["id"],
            title=f["title"],
            location=f["location"],
            date=f["date"],
            failure_type=f["failure_type"],
            similarity_score=score,
            matching_conditions=[
                kw for kw in f["keywords"]
                if kw in project_text
            ],
            causal_overlap=round(score * 0.8, 4),
            description_snippet=f["description"],
        )
        for score, f in scored[:top_k]
    ]
