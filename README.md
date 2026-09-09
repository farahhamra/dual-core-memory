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

3. **The Universal Trust Gate (`memory/sync_instincts.py` & `memory/candidate_gate.py`)**
   - **Procedural Habits:** Promoted into LanceDB once confidence $\ge 0.7$.
   - **Technical Workarounds:** Staged provisionally as `unconfirmed` on first sighting, automatically promoted to LanceDB on second confirmation.

---

## Repository Structure

```text
dual-core-memory/
├── README.md                                # Repository overview
├── LICENSE                                  # Open source MIT License
├── .gitignore                               # Ignore rules (__pycache__, local LanceDB binaries)
└── .agents/
    ├── rules/
    │   └── memory-standing-rules.md         # Standing operational memory contract
    └── skills/
        ├── continuous-learning-v2/          # Procedural habits & hook observation
        ├── vector-memory/                   # LanceDB semantic vector storage
        ├── iterative-retrieval/             # Progressive multi-hop context refinement
        ├── eval-harness/                    # Eval-Driven Development (EDD) agent testing
        ├── tdd-workflow/                    # Red-Green-Refactor test enforcement
        └── implementation-plan/             # Plan formulation & clarification addons
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

## Design Validation & Verification Scenarios

To verify that the ranking math and self-learning lifecycle function as intended, the repository provides two dedicated verification suites.

### 1. Ranking Formula Scenario Analysis (Stress-Testing)

This script validates the mathematical sensitivity of the penalty terms. It models 8 defined scenarios where raw semantic similarity happens to favor an unconfirmed or stale distractor, demonstrating how the Trust score and Freshness decay terms mathematically suppress distractors without penalizing clean control queries:

```powershell
cd .agents/skills/vector-memory
python benchmarks/benchmark_ablation.py
```

| Ranking Model | Precision@1 | MRR | Recall@3 | Scenario Behavior |
| :--- | :---: | :---: | :---: | :--- |
| **Cosine Only** | **25.0%** | **0.6250** | 100.0% | Fails on edge cases: stale or unconfirmed hacks have higher keyword overlap. |
| **Cosine × Trust** | **87.5%** | **0.9375** | 100.0% | Suppresses unconfirmed rumors, but misses expired library patches with high past trust. |
| **Cosine × Freshness** | **75.0%** | **0.8750** | 100.0% | Penalizes old records, but vulnerable to freshly submitted unconfirmed guesses. |
| **Full Dual-Core ($\text{Sim} \times \text{Trust} \times \text{Fresh}$)** | **100.0%** | **1.0000** | 100.0% | Filters both fresh rumors and stale hacks without harming clean control queries. |

---

### 2. End-to-End Self-Learning Integration Test

Using [.agents/skills/eval-harness](.agents/skills/eval-harness) principles, this test runs against the **live LanceDB database** and provisional candidate-gate with assertions at every stage:
1. **Session 1 (Naive Agent):** Agent fails attempt #1 (deadlock) $\rightarrow$ retries $\rightarrow$ stages unconfirmed candidate $\rightarrow$ **asserted NOT written to LanceDB**.
2. **Session 2 (Reinforcement):** Re-encounter triggers second confirmation $\rightarrow$ **asserted auto-promoted to LanceDB**.
3. **Session 3 (Post-Learning):** Standing rule queries memory $\rightarrow$ **asserted correct record retrieved at Rank #1** $\rightarrow$ executes verified fix $\rightarrow$ **asserted Pass@1**.

All metrics below are derived dynamically from live execution counters and assertions:

```powershell
cd .agents/skills/vector-memory
python tests/evals/test_self_learning_loop.py
```

| Metric | Before Learning (Session 1) | After Learning (Session 3) | Measured Outcome |
| :--- | :---: | :---: | :---: |
| **Task Success Rate** | 100.0% (after 3 tries) | 100.0% (on try #1) | Sustained success |
| **Pass@1 Rate** | **0.0%** | **100.0%** | **+100.0% first-shot pass** |
| **Attempts to Solution** | 3 attempts | 1 attempt | **-66.7% trial-and-error** |
| **Relevant Memory Retrieved** | None (Held at gate) | 100% (Rank #1 Confirmed) | Clean precision |
| **Distractor Retrieval** | N/A (Unassisted) | 0% (Suppressed) | Zero false memories |
| **Steps to Solution** | 3 trial-and-error steps | 1 direct step | Immediate resolution |

---

## Verification & Tests

```powershell
# Run vector memory unit tests
cd .agents/skills/vector-memory
python -m unittest discover -s tests -p "test_*.py" -v

# Run ranking formula scenario analysis
python benchmarks/benchmark_ablation.py

# Run live self-learning integration test
python tests/evals/test_self_learning_loop.py
```

## License

This project is open source and available under the [MIT License](LICENSE) © 2026 Farah Hamra.
