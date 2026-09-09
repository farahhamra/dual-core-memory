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

## Quick Start: Vector Memory CLI

From `.agents/skills/vector-memory/`:

```powershell
# Semantic Search across project memory
node bin/cli.js search "authentication token validation" --table project_memory

# Sync qualified CLv2 instincts (confidence >= 0.7) through the Trust Gate
node bin/cli.js sync-instincts

# View provisional candidates staged at the gate
node bin/cli.js candidates

# View LanceDB table statistics
node bin/cli.js stats
```

---

## Verification & Tests

```powershell
# Run vector memory tests
cd .agents/skills/vector-memory
npm test
```

## License

MIT
