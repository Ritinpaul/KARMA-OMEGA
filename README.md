<div align="center">

# KARMA-OMEGA

### Neural-Symbolic Imagination Engine for Construction Safety

*From institutional amnesia to predictive foresight — preserving every hard-won lesson, permanently.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.x-blue.svg)](https://neo4j.com/)

</div>

---

## The Problem

Every major infrastructure collapse — the Gujarat bridge, the Medigadda barrage, the Chennai girder — carries lessons that should prevent the next one. They rarely do.

Engineering knowledge dies with engineers. Each new project team re-learns the same failure modes from scratch. Institutional memory decays faster than concrete.

**KARMA-OMEGA** is the antidote: a system that ingests every failure forensic report, builds a living causal knowledge graph, and synthesises risk patterns that have never been seen before — predicting failures that haven't happened yet.

---

## How It Works — The Four Horsemen

| Horseman | Role | Technology |
|----------|------|------------|
| **MNEMOS** | Ingests failure forensics → knowledge graph + vector memory | Neo4j · Sentence-BERT · Pinecone |
| **SYNAPSE** | Combines failure DNA across domains → novel risk alerts | Isolation Forest · Monte Carlo · SHAP |
| **THANATOS** | Validates risks via physics → generates prevention alternatives | PINNs · NSGA-III · Constrained Diffusion |
| **AION** | Learns across sites without sharing raw data | Federated LoRA · Differential Privacy · IPFS |

---

## Quickstart

### Prerequisites
- Python 3.11+
- Docker (for Neo4j)
- Pinecone account (optional — falls back to in-memory)
- Google Gemini API key (optional — for PDF multimodal analysis)

### Setup

```bash
git clone https://github.com/your-org/karma-omega
cd karma-omega

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start Neo4j
docker-compose up -d

# Seed the knowledge graph with historical failures
python -m mnemos.data.seed
```

### Run the APIs

```bash
# MNEMOS — Knowledge Layer (port 8001)
uvicorn mnemos.api.main:app --reload --port 8001

# SYNAPSE — Pattern Synthesis (port 8002)
uvicorn synapse.api.main:app --reload --port 8002

# THANATOS — Physics Validation (port 8003)
uvicorn thanatos.api.main:app --reload --port 8003
```

Interactive docs available at `http://localhost:{port}/docs`

---

## The Kerala Demo

The flagship demonstration synthesises three real Indian infrastructure failures:

| Incident | Gene Extracted |
|----------|---------------|
| Gujarat Bridge Collapse (2019) | `humidity_sensitivity` — concrete strength retarded at 92% RH |
| Medigadda Barrage Failure (2021) | `foundation_scour` — pier loss at Q100 flood |
| Chennai Girder Collapse (2024) | `thermal_cracking` — ΔT 28°C micro-fracture progression |

Applied to the **Kochi Coastal Viaduct** (humidity 88%, ΔT 26°C, tidal foundation, 4-month prestress storage):

> **UNPRECEDENTED RISK DETECTED:** Compound Hydro-Thermal-Foundation failure — a combination that has never occurred at any single site, but whose components are all present simultaneously. P(failure, 30-day) = 42%.

```bash
# Run it yourself
curl -X POST http://localhost:8002/analyze/demo
```

---

## API Reference

### MNEMOS `/ingest`
```json
POST /ingest
{
  "source_type": "text",
  "content": "Bridge collapse investigation report...",
  "metadata": { "title": "Site X Incident", "location": "Gujarat", "date": "2024-01-15" }
}
```

### SYNAPSE `/analyze`
```json
POST /analyze
{
  "project": {
    "project_id": "proj-001",
    "project_name": "Mumbai Coastal Bridge",
    "location": "Mumbai, Maharashtra",
    "conditions": { "humidity": 85, "thermal_delta": 22 },
    "materials": ["M40 concrete", "prestressing strands"]
  },
  "top_k_analogues": 5,
  "monte_carlo_iterations": 1000
}
```

### THANATOS `/prevent`
```json
POST /prevent
{
  "alert_id": "alert-xyz",
  "risk_description": "Compound hydro-thermal-foundation failure",
  "site_conditions": { "humidity": 88, "thermal_delta": 26 }
}
```

---

## Project Structure

```
karma-omega/
├── mnemos/                  # Knowledge Foundation
│   ├── api/main.py          # REST endpoints
│   ├── graph/client.py      # Neo4j interactions
│   ├── embeddings/          # Sentence-BERT pipeline
│   ├── ner/engine.py        # Domain entity extraction
│   ├── ingestion/service.py # PDF/text ingestion
│   └── data/seed.py         # Knowledge graph seeder
│
├── synapse/                 # Pattern Synthesis
│   ├── api/main.py          # REST endpoints
│   ├── retrieval/engine.py  # Analogical retrieval + gene extraction
│   ├── synthesis/           # Combinatorial patterns + Monte Carlo
│   ├── novelty/detector.py  # Isolation Forest scoring
│   └── explainability/      # SHAP-style causal attribution
│
├── thanatos/                # Physics Validation
│   ├── api/main.py          # REST endpoints
│   ├── physics/             # PINN-based structural analysis
│   ├── redesign/            # Constrained generative alternatives
│   └── optimization/        # NSGA-III multi-objective ranking
│
├── docker-compose.yml       # Infrastructure (Neo4j)
├── requirements.txt
└── .env.example
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `NEO4J_PASSWORD` | Neo4j password | `karma-omega-2024` |
| `PINECONE_API_KEY` | Pinecone vector store key | — (falls back to in-memory) |
| `GEMINI_API_KEY` | Google Gemini API key | — (text-only mode) |
| `EMBEDDING_MODEL` | Sentence-BERT model name | `all-mpnet-base-v2` |

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
<i>Built for the national infrastructure safety challenge.<br>
Every failure remembered. Every future failure imagined.</i>
</div>
