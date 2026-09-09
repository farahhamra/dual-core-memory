# Antigravity Vector Memory Subsystem (Python)

Local vector-based semantic memory for Antigravity agents powered by Ollama and LanceDB in Python.

## Technology Stack
- **Runtime**: Python 3.10+
- **Database**: [LanceDB](https://lancedb.com/) (`lancedb>=0.17.0`) - serverless, zero-daemon, embedded vector database.
- **Embedding Model**: Ollama `nomic-embed-text` (768-dimensional float embeddings, running locally on `http://localhost:11434`).
- **Data Format**: Apache Arrow (`pyarrow>=14.0.0`).

## Tables
1. **`project_memory`**: Stores project-specific knowledge (DB schema structures, feature trees, domain business rules, architectural constraints).
2. **`default_memory`**: Stores global cross-project knowledge (agent guidelines, reusable code patterns, troubleshooting tips).

## Directory Structure
```text
vector-memory/
├── SKILL.md                          # Antigravity skill specification
├── README.md                         # Subsystem documentation
├── requirements.txt                  # Python dependencies (lancedb, pyarrow, requests)
├── cli.py                            # Unified CLI executable
├── memory/                           # Core Python package
│   ├── __init__.py
│   ├── config.py                     # Local storage paths & Ollama configuration
│   ├── db.py                         # LanceDB connection & PyArrow schema
│   ├── embedder.py                   # Ollama embedding client
│   ├── search.py                     # Semantic search + Trust & Freshness ranking
│   ├── save.py                       # Memory record upserting with embeddings
│   ├── candidate_gate.py             # Provisional candidate staging & 2nd-sighting promotion
│   └── sync_instincts.py             # CLv2 instinct Trust Gate sync
├── tests/
│   └── test_memory.py                # Unit test suite
├── references/
│   └── memory-automation-rules.md    # Standing memory rules
└── data/                             # Local LanceDB storage (git-ignored)
    ├── default_memory.lance/
    ├── project_memory.lance/
    └── provisional-candidates.json
```

## Setup & Installation

```powershell
pip install -r requirements.txt
```

Ensure Ollama is running:
```powershell
ollama pull nomic-embed-text
```

## CLI Commands

```powershell
# Semantic Search (Rank = Similarity * Trust * Freshness)
python cli.py search "authentication token validation" --table project_memory

# Save / Upsert Record
python cli.py save "Database Table: users" "CREATE TABLE users (id INT PRIMARY KEY...)" --category "db-schema"

# Stage Provisional Technical Candidate
python cli.py record-candidate "Prisma transaction deadlock" "Use interactive transactions with explicit timeout."

# List Staged Candidates
python cli.py candidates

# Sync Qualified CLv2 Instincts (Confidence >= 0.70)
python cli.py sync-instincts

# View Database Table Statistics
python cli.py stats
```

## Running Tests

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```
