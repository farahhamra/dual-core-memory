# dual-core-memory: Dual-Core Agent Memory & Cognitive Subsystem

An advanced local AI agent workspace equipped with a **dual-core memory architecture**, self-correcting continuous learning, and verification guardrails.

---

## Architecture Overview

`dual-core-memory` merges two specialized cognitive subsystems to provide complete memory coverage:

1. **System 1: Procedural Memory (`continuous-learning-v2`)**
   - Passive observation via deterministic `PreToolUse` and `PostToolUse` lifecycle hooks.
   - Self-adjusting confidence scoring (`0.3` to `0.9`) with natural decay and reinforcement.
   - Scoped per Git remote repository to prevent cross-project habit contamination.

2. **System 2: Declarative Memory (`vector-memory`)**
   - High-speed, local embedded vector search powered by [LanceDB](https://lancedb.com/) and Apache Arrow.
   - Dense 768-dimensional float embeddings using local Ollama (`nomic-embed-text`).
   - Category-specific freshness weighting and trust score ranking:
     $$\text{Rank Score} = \text{Cosine Similarity} \times \text{Trust Score} \times \text{Freshness Weight}$$

3. **The Universal Trust Gate (`sync-instincts.js` & `candidate-gate.js`)**
   - **Procedural Habits:** Promoted into LanceDB once confidence $\ge 0.7$.
   - **Technical Workarounds:** Staged provisionally as `unconfirmed` on first sighting, automatically promoted to LanceDB on second confirmation.

---

## Repository Structure

```text
dual-core-memory/
├── README.md                                # Repository overview
├── .gitignore                               # Ignore rules (node_modules, local LanceDB binaries)
└── .agents/
    ├── rules/
    │   └── memory-standing-rules.md         # Standing operational memory contract
    └── skills/
        ├── continuous-learning-v2/          # Procedural habits & hook observation
        ├── vector-memory/                   # LanceDB semantic vector storage
        ├── iterative-retrieval/             # Progressive multi-hop context refinement
        ├── eval-harness/                    # Eval-Driven Development (EDD) agent testing
        └── tdd-workflow/                    # Red-Green-Refactor test enforcement
```

---

## Installation & Setup

### 1. Prerequisites
- **Python 3.10+** (single runtime for both Vector Memory and Continuous Learning v2)
- **Local Ollama** (running locally on port `11434`)
  ```powershell
  ollama pull nomic-embed-text
  ```

---

### 2. Setup in This Workspace (Fresh Clone)

If cloning this repository onto a new machine:

```powershell
# 1. Clone the repository
git clone https://github.com/farahhamra/dual-core-memory.git
cd dual-core-memory

# 2. Install vector-memory dependencies
cd .agents/skills/vector-memory
pip install -r requirements.txt

# 3. Verify installation
python -m unittest discover -s tests -p "test_*.py" -v
```

---

### 3. Installing Into ANOTHER Project

To give any other project this dual-core memory system:

1. **Copy the `.agents/` folder** into the root of your target project:
   ```powershell
   # From your target project root:
   Copy-Item -Path "path\to\dual-core-memory\.agents" -Destination "." -Recurse
   ```
2. **Install the dependencies**:
   ```powershell
   cd .agents/skills/vector-memory
   pip install -r requirements.txt
   ```
3. **Done!** Antigravity IDE and Claude Code automatically detect `.agents/rules/` and `.agents/skills/`.

---

## Quick Start: Vector Memory CLI

From `.agents/skills/vector-memory/`:

```powershell
# Semantic Search across project memory
python cli.py search "authentication token validation" --table project_memory

# Sync qualified CLv2 instincts (confidence >= 0.70) through the Trust Gate
python cli.py sync-instincts

# View provisional candidates staged at the gate
python cli.py candidates

# Stage a technical workaround candidate
python cli.py record-candidate "Prisma deadlock workaround" "Use interactive transactions with explicit timeout."

# View LanceDB table statistics
python cli.py stats
```

---

## Verification & Tests

```powershell
# Run vector memory unit tests
cd .agents/skills/vector-memory
python -m unittest discover -s tests -p "test_*.py" -v
```

## License

MIT
