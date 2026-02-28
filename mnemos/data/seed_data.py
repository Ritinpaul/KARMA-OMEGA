"""
MNEMOS: Synthetic Seed Data
============================
Pre-structured failure records based on the three core incidents
described in KARMA-OMEGA's info1.md, plus 2 international analogues.

These seed 500+ nodes in the knowledge graph for immediate demo capability.
Run via:  python -m mnemos.data.seed
"""

from __future__ import annotations

from mnemos.schemas.models import (
    CausalChain,
    FailureRecord,
    FailureType,
    Severity,
)

# ─────────────────────────────────────────────────────────────────────────────
# Core L&T / India Failures (from info1.md)
# ─────────────────────────────────────────────────────────────────────────────

GUJARAT_BRIDGE_2019 = FailureRecord(
    id="failure-gujarat-bridge-2019",
    title="Gujarat Bridge Collapse 2019",
    date="2019-04-15",
    location="Gujarat",
    country="India",
    failure_type=FailureType.STRUCTURAL,
    severity=Severity.CRITICAL,
    fatalities=3,
    economic_loss_crore=200.0,
    description=(
        "A newly constructed bridge in Gujarat collapsed during post-cast operations. "
        "The failure occurred due to premature removal of formwork under high humidity "
        "conditions that delayed concrete curing, resulting in insufficient early strength. "
        "The structure was loaded before the concrete achieved the minimum compressive "
        "strength of 15 MPa. Investigation revealed that ambient humidity exceeded 92% "
        "during the curing period, significantly retarding cement hydration kinetics. "
        "The decision to remove formwork was based on elapsed calendar days rather "
        "than maturity-based strength testing."
    ),
    root_causes=[
        "Premature formwork removal — concrete had not achieved design strength",
        "High ambient humidity (>92%) retarding cement hydration",
        "Reliance on calendar time rather than strength maturity index for curing decisions",
        "Absence of in-situ cube testing before critical loading",
    ],
    contributing_conditions=[
        "humidity: 92%",
        "monsoon pre-season elevated moisture",
        "temperature: 38°C",
        "premature loading",
        "inadequate curing supervision",
    ],
    materials_involved=[
        "M30 concrete",
        "Fe500 TMT rebar",
        "OPC cement",
        "river sand fine aggregate",
    ],
    causal_chains=[
        CausalChain(
            steps=[
                "Ambient humidity >92%",
                "Delayed cement hydration → slow strength gain",
                "Premature formwork removal at Day 7",
                "Live load applied at 40% design strength",
                "Shear failure at critical section",
                "Progressive collapse",
            ],
            root_cause="Ambient humidity >92%",
            failure_mode="Progressive collapse",
            source_doc="gujarat_bridge_2019_forensic.pdf",
        )
    ],
    source_document="gujarat_bridge_2019_forensic.pdf",
)

MEDIGADDA_BARRAGE_2021 = FailureRecord(
    id="failure-medigadda-barrage-2021",
    title="Medigadda Barrage Foundation Failure 2021",
    date="2021-10-08",
    location="Medigadda, Telangana",
    country="India",
    failure_type=FailureType.GEOTECHNICAL,
    severity=Severity.CRITICAL,
    fatalities=0,
    economic_loss_crore=1800.0,
    description=(
        "The Medigadda Barrage on the Godavari River in Telangana experienced catastrophic "
        "foundation failure causing differential settlement exceeding 600mm. Pier 7 sank "
        "nearly 1.7 meters. The primary cause was foundation scour exacerbated by "
        "unprecedented monsoon-induced flood intensity (Q100 event). "
        "The original foundation design did not adequately account for scour depth "
        "under extreme flood conditions. Additionally, soil investigation data "
        "underestimated the erodibility of the alluvial strata. "
        "The structure remains closed to traffic pending remediation."
    ),
    root_causes=[
        "Foundation scour exceeding design assumptions under extreme flood",
        "Underestimation of alluvial soil erodibility in site investigation",
        "Inadequate scour protection (rip-rap depth insufficient)",
        "Q100 flood event not adequately represented in hydrological study",
    ],
    contributing_conditions=[
        "monsoon intensity: extreme (Q100 flood event)",
        "foundation proximity to water table: high",
        "alluvial soil erodibility: high",
        "scour depth: >3m below design level",
        "differential settlement: 600mm+",
    ],
    materials_involved=[
        "M35 concrete",
        "Fe415 TMT rebar",
        "fly ash blended cement",
        "alluvial foundation strata",
    ],
    causal_chains=[
        CausalChain(
            steps=[
                "Q100 monsoon flood event (unexpected intensity)",
                "Scour at pier foundations exceeded design scour depth",
                "Loss of bearing capacity in alluvial strata",
                "Differential settlement of Pier 7 (1.7m)",
                "Structural distress in superstructure sections",
                "Barrage closure — functional failure",
            ],
            root_cause="Q100 monsoon flood event (unexpected intensity)",
            failure_mode="Functional failure from differential settlement",
            source_doc="medigadda_barrage_2021_inquiry.pdf",
        )
    ],
    source_document="medigadda_barrage_2021_inquiry.pdf",
)

CHENNAI_GIRDER_2024 = FailureRecord(
    id="failure-chennai-girder-2024",
    title="Chennai Elevated Corridor Girder Collapse 2024",
    date="2024-02-20",
    location="Chennai, Tamil Nadu",
    country="India",
    failure_type=FailureType.STRUCTURAL,
    severity=Severity.CRITICAL,
    fatalities=0,
    economic_loss_crore=450.0,
    description=(
        "A precast prestressed concrete girder collapsed during erection at an "
        "elevated road corridor project in Chennai. The girder fell during a "
        "launching sequence due to a thermal stress-induced crack that propagated "
        "catastrophically. The girder had been stored horizontally for 6 months, "
        "experiencing significant day-night thermal cycling (ΔT = 28°C daily). "
        "Investigation revealed that the erection sequence error placed the "
        "launching nose at an eccentricity that induced torsional stress, "
        "which combined with existing thermal micro-cracks led to fracture. "
        "No pre-erection non-destructive testing was conducted."
    ),
    root_causes=[
        "Thermal stress micro-cracking from 6-month storage with ΔT=28°C daily cycling",
        "Erection sequence error — launching nose eccentricity induced torsional stress",
        "No pre-erection NDT to detect existing thermal micro-cracks",
        "Prestress losses not recomputed after extended storage period",
    ],
    contributing_conditions=[
        "thermal cycling: ΔT=28°C daily",
        "storage duration: 6 months",
        "temperature: 42°C max",
        "erection sequence error",
        "torsional eccentricity",
        "prestress loss underestimation",
    ],
    materials_involved=[
        "M45 high-strength concrete",
        "high-tensile prestressing strands",
        "Fe500 TMT stirrups",
        "epoxy resin grout",
        "HDPE prestress ducts",
    ],
    causal_chains=[
        CausalChain(
            steps=[
                "6-month storage with ΔT=28°C daily thermal cycling",
                "Thermal micro-cracking along prestress duct lines",
                "Erection sequence error → torsional eccentricity at nose",
                "Torsional stress superimposed on thermal micro-cracks",
                "Crack propagation exceeds fracture toughness",
                "Brittle fracture and girder collapse",
            ],
            root_cause="Thermal micro-cracking from extended storage",
            failure_mode="Brittle fracture and collapse during erection",
            source_doc="chennai_girder_2024_forensic.pdf",
        )
    ],
    source_document="chennai_girder_2024_forensic.pdf",
)

# ─────────────────────────────────────────────────────────────────────────────
# International Analogue Failures (for cross-domain pattern synthesis)
# ─────────────────────────────────────────────────────────────────────────────

FIU_BRIDGE_USA_2018 = FailureRecord(
    id="failure-fiu-bridge-usa-2018",
    title="FIU Pedestrian Bridge Collapse, Miami 2018",
    date="2018-03-15",
    location="Miami, Florida",
    country="USA",
    failure_type=FailureType.STRUCTURAL,
    severity=Severity.CRITICAL,
    fatalities=6,
    economic_loss_crore=350.0,
    description=(
        "A 950-ton pedestrian bridge being installed over Southwest 8th Street "
        "at Florida International University collapsed, killing 6 people. "
        "The NTSB investigation found that cracks observed in a critical diagonal "
        "member were misidentified as non-structural. Tensioning of post-tensioning "
        "rods to repair the member actually increased stress in the cracked section, "
        "leading to shear-compression failure and progressive collapse. "
        "The Accelerated Bridge Construction (ABC) method's rapid timeline "
        "contributed to inadequate time for crack investigation."
    ),
    root_causes=[
        "Misidentification of critical shear crack as non-structural cosmetic crack",
        "Post-tensioning rod re-tensioning increased stress at cracked section",
        "ABC method timeline pressure reduced time for proper crack investigation",
        "Design error: node geometry produced stress concentration at diagonal member",
    ],
    contributing_conditions=[
        "accelerated construction timeline: high pressure",
        "crack width: 5.8mm (misidentified as non-critical)",
        "post-tensioning eccentricity",
        "temperature: 30°C",
        "high traffic zone — active road below",
    ],
    materials_involved=[
        "Self-consolidating concrete (SCC)",
        "post-tensioning strands",
        "high-strength grout",
        "CFRP external tendons",
    ],
    causal_chains=[
        CausalChain(
            steps=[
                "Design error: stress concentration at diagonal node",
                "Shear crack develops during installation",
                "Crack misidentified as cosmetic",
                "Re-tensioning of PT rod increases stress at cracked section",
                "Shear-compression failure of diagonal member",
                "Progressive collapse of entire span",
            ],
            root_cause="Design error causing stress concentration",
            failure_mode="Progressive collapse from diagonal member failure",
            source_doc="ntsb_fiu_bridge_2018.pdf",
        )
    ],
    source_document="ntsb_fiu_bridge_2018.pdf",
)

GENOA_MORANDI_2018 = FailureRecord(
    id="failure-genoa-morandi-italy-2018",
    title="Genoa Morandi Bridge Collapse 2018",
    date="2018-08-14",
    location="Genoa",
    country="Italy",
    failure_type=FailureType.STRUCTURAL,
    severity=Severity.CRITICAL,
    fatalities=43,
    economic_loss_crore=6000.0,
    description=(
        "The Ponte Morandi viaduct in Genoa, Italy, collapsed during heavy rain, "
        "sending 45 vehicles into a 45-metre deep ravine. The failure was caused by "
        "corrosion of the hybrid stay cable system — an unusual design where "
        "prestressed concrete encased the steel stays, making inspection impossible. "
        "Decades of deferred maintenance, combined with corrosive coastal environment "
        "(chloride-laden sea air), had severely degraded the steel stays inside the "
        "concrete casing. The failure of one pylon's stays triggered progressive collapse."
    ),
    root_causes=[
        "Hidden corrosion of steel stays inside concrete encasement — not inspectable",
        "Deferred maintenance over 50+ years",
        "Chloride-induced corrosion from coastal sea air",
        "Unique hybrid design (Riccardo Morandi system) not compatible with standard inspection",
        "Inadequate structural health monitoring on aging infrastructure",
    ],
    contributing_conditions=[
        "coastal chloride environment: high",
        "structure age: 51 years",
        "rainfall: heavy during failure",
        "traffic load: high (A10 motorway)",
        "corrosion rate: severe",
        "deferred maintenance: chronic",
    ],
    materials_involved=[
        "prestressed concrete stays",
        "encased steel tendons",
        "OPC concrete (1967 era)",
        "carbon steel high-tensile wires",
    ],
    causal_chains=[
        CausalChain(
            steps=[
                "Coastal chloride environment over 50+ years",
                "Chloride penetration through concrete into encased steel stays",
                "Corrosion of steel stays — invisible due to concrete encasement",
                "Progressive strength reduction of stay cables",
                "Failure of one pylon's stay system under rain-increased load",
                "Progressive collapse — span destruction",
            ],
            root_cause="Long-term chloride-induced corrosion of hidden steel stays",
            failure_mode="Progressive collapse from stay system failure",
            source_doc="genoa_morandi_mit_report_2018.pdf",
        )
    ],
    source_document="genoa_morandi_mit_report_2018.pdf",
)

# ─────────────────────────────────────────────────────────────────────────────
# Kerala Site — The Demo Scenario (current project at risk)
# ─────────────────────────────────────────────────────────────────────────────

KERALA_DEMO_PROJECT = FailureRecord(
    id="project-kerala-bridge-2025",
    title="Kerala Coastal Viaduct — Active Project (2025)",
    date="2025-01-10",
    location="Kochi, Kerala",
    country="India",
    failure_type=FailureType.COMPOUND,
    severity=Severity.MEDIUM,
    fatalities=0,
    description=(
        "Active L&T project: coastal viaduct construction in Kochi. "
        "Current environmental readings: humidity 88%, temperature field 39°C, "
        "day-night ΔT 26°C. Foundation proximity to tidal water table: HIGH. "
        "Prestressed girders stored on-site for 4 months. "
        "Monsoon season begins in 6 weeks. No SYNAPSE risk assessment conducted yet."
    ),
    root_causes=[],
    contributing_conditions=[
        "humidity: 88%",
        "temperature: 39°C",
        "thermal cycling: ΔT=26°C",
        "foundation proximity to water table: high (tidal)",
        "prestressed storage duration: 4 months",
        "monsoon onset: 6 weeks"
    ],
    materials_involved=[
        "M40 concrete",
        "high-tensile prestressing strands",
        "Fe500 TMT rebar",
        "fly ash blended cement",
    ],
    source_document="kerala_viaduct_current_status.json",
)

# ─────────────────────────────────────────────────────────────────────────────
# All seed records
# ─────────────────────────────────────────────────────────────────────────────

ALL_SEED_RECORDS = [
    GUJARAT_BRIDGE_2019,
    MEDIGADDA_BARRAGE_2021,
    CHENNAI_GIRDER_2024,
    FIU_BRIDGE_USA_2018,
    GENOA_MORANDI_2018,
    KERALA_DEMO_PROJECT,
]
