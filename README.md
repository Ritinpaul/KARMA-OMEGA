# KARMA-OMEGA 🔥
### Neural-Symbolic Imagination Engine for Construction Safety

> *"We Don't Just Remember. We Imagine. We Prevent. We Immortalize."*

KARMA-OMEGA is a Hackathon project targeting L&T Construction's institutional knowledge decay crisis. It synthesizes novel failure modes from 80 years of construction failure DNA and generates physics-guaranteed preventions.

---

## Architecture: The Four Horsemen

| Horseman | Role | Status |
|----------|------|--------|
| **MNEMOS** | Neural-Symbolic Memory Palace | ✅ Phase 1 |
| **SYNAPSE** | Cross-Domain Pattern Synthesizer | 🔜 Phase 2 |
| **THANATOS** | Generative Physics Oracle | 🔜 Phase 3 |
| **AION** | Federated Immortality Engine | 🔜 Phase 4 |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (for Neo4j)
- Pinecone API key (or local fallback)

### Setup

```bash
# Clone the repo
git clone <repo-url>
cd karma-omega

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Fill in your API keys in .env

# Start Neo4j via Docker
docker-compose up -d neo4j

# Run the MNEMOS API
uvicorn mnemos.api.main:app --reload --port 8001
```

### Run Tests
```bash
pytest tests/ -v
```

---

## Project Structure

```
karma-omega/
├── mnemos/              # Phase 1: Knowledge Foundation
│   ├── api/             # FastAPI application
│   ├── ingestion/       # Document AI pipeline
│   ├── graph/           # Neo4j knowledge graph
│   ├── embeddings/      # Sentence-BERT pipeline
│   ├── ner/             # Named entity recognition
│   └── schemas/         # Pydantic data models
├── synapse/             # Phase 2: Pattern Synthesis (upcoming)
├── thanatos/            # Phase 3: Physics Oracle (upcoming)
├── aion/                # Phase 4: Federation (upcoming)
├── data/                # Failure reports, raw datasets
│   ├── raw/             # Original PDFs / source docs
│   ├── processed/       # Extracted, cleaned data
│   └── synthetic/       # Augmented synthetic failure data
├── tests/               # Test suite
│   ├── unit/
│   └── integration/
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## API Documentation

Once running, visit: http://localhost:8001/docs

### MNEMOS Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ingest` | Ingest a failure document/PDF |
| `GET` | `/query` | Semantic query over the knowledge base |
| `GET` | `/graph/traverse` | Traverse causal chains in the knowledge graph |
| `GET` | `/graph/nodes` | Retrieve graph nodes with optional filtering |
| `GET` | `/health` | Health check |

---

## The Core Innovation

KARMA-OMEGA goes beyond failure *prevention* to failure *imagination*:

- **Traditional**: "We've seen this before. Here's the fix."  
- **KARMA-OMEGA**: "We've never seen this specific combination — but pattern fusion says it's coming. Here's an unprecedented prevention."
