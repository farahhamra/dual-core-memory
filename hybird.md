# Hybrid Agent Memory Architecture: Continuous Learning & Vector Memory

This document details the architecture of two specialized Antigravity agent memory subsystems—**Continuous Learning v2** and **Antigravity Vector Memory**—and outlines concrete strategies to hybridize them into a unified, dual-core memory system.

---

## 1. Executive Summary: The Dual-Core Brain Model

Humans rely on two distinct memory modes:
1. **Procedural Memory (System 1 - Reflexes & Habits):** Subconscious, auto-adjusted behaviors (e.g., typing style, coding syntax preferences, habitual tool choices).
2. **Declarative Memory (System 2 - Semantic Facts & Knowledge):** Searchable, structured facts (e.g., database schemas, architectural patterns, domain business rules).

By hybridizing both systems:
- **`continuous-learning-v2`** handles **Procedural Memory** (auto-capturing corrections, weighting confidence, tracking coding reflexes).
- **`vector-memory`** handles **Declarative Memory** (sub-millisecond semantic search across schemas, rules, and technical solutions via LanceDB and Ollama).

```
                             Developer Interaction
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
        [Procedural Reflexes]                 [Declarative Knowledge]
       continuous-learning-v2                      vector-memory
   • Deterministic Pre/Post hooks           • LanceDB embedded vector store
   • User correction detection              • Ollama nomic-embed-text (768 dims)
   • Confidence scoring (0.3 - 0.9)         • Semantic similarity search
   • Project isolation by Git hash          • Tables: project_memory, default_memory
                    │                                     ▲
                    │        High-Confidence Sync         │
                    └─────────────────────────────────────┘
```

---

## 2. Deep Dive: Continuous Learning v2 (`continuous-learning-v2`)

- **Location:** [`.agents/skills/continuous-learning-v2`](file:///c:/Backup/WebScout/.agents/skills/continuous-learning-v2)
- **Origin:** Everything Claude Code (ECC) / Homunculus Architecture
- **Purpose:** Automatically observe coding sessions, extract lessons from user corrections and error recoveries, and maintain confidence-scored "instincts".

### Core Components
1. **Deterministic Hooks ([`hooks/observe.sh`](file:///c:/Backup/WebScout/.agents/skills/continuous-learning-v2/hooks/observe.sh)):**
   Fires 100% of the time on `PreToolUse` and `PostToolUse` events, recording prompts, commands, tool outputs, errors, and subsequent user corrections into `observations.jsonl`.
2. **Project Scoper ([`scripts/detect-project.sh`](file:///c:/Backup/WebScout/.agents/skills/continuous-learning-v2/scripts/detect-project.sh)):**
   Hashes the repository's Git remote URL to isolate memories per project (e.g., React conventions stay in React; Python idioms stay in Python).
3. **Background Observer Agent ([`agents/observer.md`](file:///c:/Backup/WebScout/.agents/skills/continuous-learning-v2/agents/observer.md)):**
   Analyzes accumulated observations (e.g., every 20 events / 5 minutes) to detect:
   - User corrections (*"No, use X instead of Y"*)
   - Error resolutions (*Tool failed -> Next tool fixed it*)
   - Repeated workflows (*Grep -> Read -> Edit*)
4. **Instinct Model & CLI ([`scripts/instinct-cli.py`](file:///c:/Backup/WebScout/.agents/skills/continuous-learning-v2/scripts/instinct-cli.py)):**
   Maintains atomic YAML instinct files with confidence dynamics:
   - Initial: `0.3` (tentative) to `0.85` (frequent)
   - Adjustment: `+0.05` on confirm, `-0.10` on contradict, `-0.02` weekly decay
   - Promotion: Automatically promoted from project to global if seen in 2+ repos with $\ge 0.8$ confidence.

### Data Model (`.yaml`)
```yaml
---
id: prefer-functional-style
trigger: "when writing new functions"
confidence: 0.75
domain: "code-style"
source: "session-observation"
scope: project
project_id: "a1b2c3d4e5f6"
project_name: "web-scout"
---
# Prefer Functional Style
## Action
Use functional patterns over classes when appropriate.
## Evidence
- Observed 5 instances of functional preference
- User corrected class-based approach on 2026-09-08
```

### Strengths & Limitations
- **Strengths:** Zero manual effort; adapts automatically to user feedback; prevents cross-project contamination; self-correcting via confidence decay.
- **Limitations:** No semantic vector search (retrieval relies on string/trigger matches); background daemon requires Linux/WSL2 on Windows machines.

---

## 3. Deep Dive: Antigravity Vector Memory (`vector-memory`)

- **Location:** [`.agents/skills/vector-memory`](file:///c:/Backup/WebScout/.agents/skills/vector-memory)
- **Origin:** Electro ERP / Antigravity Subsystem
- **Purpose:** Provide high-speed semantic similarity retrieval over durable technical facts, schemas, API specifications, and reusable architectural patterns.

### Core Components
1. **Vector Database Engine ([`src/db.js`](file:///c:/Backup/WebScout/.agents/skills/vector-memory/src/db.js)):**
   Uses LanceDB (`@lancedb/lancedb`), a serverless, zero-daemon, embedded vector database running on Apache Arrow.
2. **Local Embeddings ([`src/embedder.js`](file:///c:/Backup/WebScout/.agents/skills/vector-memory/src/embedder.js)):**
   Connects to local Ollama (`http://localhost:11434`) using `nomic-embed-text` to generate 768-dimensional dense vectors.
3. **Dedicated Tables:**
   - `project_memory`: Database schemas, feature trees, domain constraints, module relationships.
   - `default_memory`: Universal best practices, error patterns, generic agent guidelines.
4. **Operations Suite:**
   - Search: [`src/search.js`](file:///c:/Backup/WebScout/.agents/skills/vector-memory/src/search.js) (cosine similarity search with category filters and score thresholds)
   - Save: [`src/save.js`](file:///c:/Backup/WebScout/.agents/skills/vector-memory/src/save.js) (upserts records with auto-generated embeddings)
   - Update & Delete: [`src/update.js`](file:///c:/Backup/WebScout/.agents/skills/vector-memory/src/update.js), [`src/delete.js`](file:///c:/Backup/WebScout/.agents/skills/vector-memory/src/delete.js)
5. **Unified CLI ([`bin/cli.js`](file:///c:/Backup/WebScout/.agents/skills/vector-memory/bin/cli.js)):**
   Allows agents and developers to run `node bin/cli.js search "..."` or `npm run stats`.

### Directory Layout
```text
vector-memory/
├── SKILL.md                          # Skill definition & guidelines
├── README.md                         # Command references
├── package.json                      # npm manifest (main: "src/index.js")
├── index.js                          # Root proxy module
├── bin/
│   └── cli.js                        # Unified CLI runner
├── src/
│   ├── index.js                      # Core exports
│   ├── config.js                     # Path & model configuration
│   ├── db.js                         # LanceDB connection & table initialization
│   ├── embedder.js                   # Ollama embedding integration
│   ├── search.js                     # Vector similarity query engine
│   ├── save.js                       # Memory upsert pipeline
│   ├── update.js                     # Record updater
│   └── delete.js                     # Deletion logic
├── scripts/
│   └── test.js                       # Test suite
├── references/
│   └── memory-automation-rules.md    # Autonomous execution directives
└── data/                             # Embedded LanceDB tables
    ├── default_memory.lance/
    └── project_memory.lance/
```

### Strengths & Limitations
- **Strengths:** Instant semantic recall; handles fuzzy, conceptual queries; stores rich structured metadata; runs 100% locally with zero cloud dependencies.
- **Limitations:** Requires explicit save/search actions; lacks passive session observation hooks; records remain static unless manually updated.

---

## 4. Side-by-Side Comparison

| Feature | Continuous Learning v2 | Antigravity Vector Memory |
| :--- | :--- | :--- |
| **Primary Focus** | Behavioral habits & coding style | Technical facts, schemas & architecture |
| **Ingestion** | **Passive & Autonomous** (Hooks log events) | **Explicit** (CLI / API calls) |
| **Storage Technology** | YAML files + JSONL observation logs | LanceDB (Arrow tables) on local disk |
| **Search Mechanism** | Trigger/keyword string matching | **Semantic vector similarity (Cosine / 768 dims)** |
| **Confidence Model** | Dynamic (0.3 – 0.9 with decay & boost) | Static (records are persistent until modified) |
| **Scoping** | Git remote URL hash (`projects/<hash>/`) | Table segregation (`project_memory` vs `default_memory`) |
| **Lifecycle Evolution** | Clusters instincts into skills/agents via `/evolve` | Curated durable knowledge base |

---

## 5. Suggested Hybridization Approaches

### Approach 1: Division of Responsibilities (Workflow Hybrid)
*Zero code modifications required. Establish a clear operational contract for when agents invoke each tool.*

```
Task Lifecycle:
1. Pre-Task Planning   ──► Query vector-memory for schemas & architecture
2. Task Execution      ──► continuous-learning-v2 hooks capture tool calls & corrections
3. Post-Task Evolution ──► High-confidence patterns saved to vector-memory
```

- **Pre-Task Planning:** Before creating plans or touching critical files, the agent queries LanceDB:
  ```powershell
  node bin/cli.js search "authentication token validation" --table project_memory
  ```
- **During Task Execution:** The agent writes code normally. `hooks/observe.sh` monitors tool calls and records any user interventions.
- **Post-Task:** If a new architecture rule or database model was added, the agent persists the schema into `vector-memory`.

#### Responsibility Decision Matrix
| Knowledge Item | Target System | Target Table / Scope |
| :--- | :--- | :--- |
| Database schema, Prisma models, DDL | `vector-memory` | `project_memory` |
| Feature module routing & hierarchy | `vector-memory` | `project_memory` |
| Team architecture decisions & constraints | `vector-memory` | `project_memory` |
| "Always use arrow functions in React" | `continuous-learning-v2` | `project` scope |
| "Use pnpm instead of npm" | `continuous-learning-v2` | `project` scope |
| "Always validate user input with Zod" | `continuous-learning-v2` $\rightarrow$ `vector-memory` | Auto-promoted to `default_memory` |

## 5. The Unified Hybrid Architecture: Trust Gate & Observer Split

The two systems share a clean division of labor:
* **`continuous-learning-v2` owns TRUST** (confidence scoring, reinforcement, decay, human correction tracking).
* **`vector-memory` (LanceDB) owns RELEVANCE** (dense vector embeddings, semantic similarity, high-speed filtering).

Rather than allowing the background observer to write technical facts into `project_memory` on first sight (which risks cementing temporary hacks into permanent rules), **Approach 2 is elevated from "just instinct search" into the Universal Trust Gate for everything entering LanceDB.**

```
                             Developer Interaction
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
        [Behavioral Corrections]               [Pre-Task Relevance Search]
         continuous-learning-v2                   vector-memory (LanceDB)
                    │                                     ▲
                    ▼                                     │
         Observer Behavioral Half                         │
         • "Use X instead of Y"                           │
         • Style / Tool preferences                       │
         • Instinct YAMLs (+0.05 / -0.10)                 │
                    │                                     │
                    │  Confidence ≥ 0.7                   │
                    ▼                                     │
     ┌──────────────────────────────────────────────┐     │
     │      APPROACH 2: THE UNIFIED TRUST GATE      │     │
     │            (sync-instincts.js)               │     │
     │                                              │     │
     │  1. PROCEDURAL: Habits ≥ 0.7 ────────────────┼─────┤
     │  2. DECLARATIVE: Confirmed schemas/rules ────┼─────┤
     │  3. EPISODIC: Gated candidates (unconfirmed) │     │
     │     └──► Requires 2nd sight or confirmation ─┼─────┘
     └──────────────────────────────────────────────┘
                    ▲
                    │ Candidate Solutions
         Observer Technical Half
         • Error fixes, CLI workarounds
         • NOT written directly to LanceDB!
```

---

## 6. The 3-Category Memory Taxonomy & Freshness Dynamics

All memories entering the system are classified into a 3-category taxonomy:

| Category | Description | Source / Trust Mechanism | Freshness Dynamics |
| :--- | :--- | :--- | :--- |
| **`procedural`** | Coding style, tool preferences, habits, workflow sequences. | Managed by CLv2 instincts; promoted to LanceDB when confidence $\ge 0.7$. | **Skip in Vector Search:** CLv2 natively handles weekly decay (`-0.02/wk`) and contradictions (`-0.10`). |
| **`declarative`** | Database models, API schemas, domain rules, architectural invariants. | Verified by developer or established project documentation; saved directly or confirmed. | **Flat Freshness ($\approx 1.0$):** Invariants do not expire over time unless explicitly updated. |
| **`episodic`** | Specific past debugging incidents, error recoveries, tool output workarounds. | Extracted by the observer agent; **gated** as `unconfirmed` on 1st sighting; promoted to trusted on 2nd reinforcement. | **Steep Temporal Decay ($e^{-\lambda t}$):** A workaround for a compiler issue from 4 months ago must not override current code unless reinforced. |

### Confidence-Weighted Retrieval Formula

When searching `vector-memory`, results are ranked dynamically:

$$\text{Final Rank} = \text{Cosine Similarity} \times \text{Trust Score} \times \text{Freshness Weight}$$

* **For `procedural`:** $\text{Trust Score} = \text{confidence}_{\text{CLv2}}$ (0.7 to 0.95), $\text{Freshness} = 1.0$.
* **For `declarative`:** $\text{Trust Score} = 1.0$, $\text{Freshness} = 1.0$.
* **For `episodic`:** $\text{Trust Score} = 0.5$ (*unconfirmed*) or $1.0$ (*confirmed*), $\text{Freshness} = e^{-\lambda \cdot \Delta t_{\text{days}}}$.

---

## 7. Phased Build Order

We build in strict dependency order so each step delivers immediate value with zero risk:

```
[Phase 1] Standing Rule (Approach 1) ──► Ships Today (Zero Code)
    │
    ▼
[Phase 2] Trust Gate Engine (Approach 2) ──► sync-instincts.js (≥0.7 promotion)
    │
    ▼
[Phase 3] Observer Behavioral Routing ──► Live YAML (+0.05 / -0.10 lifecycle)
    │
    ▼
[Phase 4] Gated Technical/Episodic Ingestion ──► Provisional staging (unconfirmed → confirmed)
    │
    ▼
[Phase 5] 3-Category Taxonomy in LanceDB ──► Schema upgrade (procedural / declarative / episodic)
    │
    ▼
[Phase 6] Category-Specific Freshness ──► search.js ranking formula
```

### Phase 1: Operational Contract (Approach 1, Ships Today)
* **Rule:** Before touching code or proposing plans, always search `vector-memory` for schemas and architecture.
* **Passive Capture:** Let `hooks/observe.sh` run silently in the background capturing tool interactions.
* **Risk:** Zero code, zero risk.

### Phase 2: The Trust Gate Engine (`sync-instincts.js`)
* Build `scripts/sync-instincts.js` in `vector-memory`.
* Evaluates instinct YAML files from `~/.local/share/ecc-homunculus/`.
* Any instinct meeting confidence $\ge 0.7$ is embedded into LanceDB under `category: "procedural"`.
* Exposes CLI command: `npm run sync-instincts` or `node bin/cli.js sync-instincts`.

### Phase 3: Live Behavioral Observer Routing
* Activate the background observer for user corrections and style preferences.
* Outputs directly to instinct YAML files.
* Fully governed by CLv2's existing lifecycle—completely safe because it does not touch the factual vector database.

### Phase 4: Gated Technical / Episodic Observer Routing
* Split the observer's technical output path.
* Technical solutions and bug fixes are **NOT** written directly to LanceDB.
* They are flagged as `unconfirmed` in a candidate pool. Only upon a **second confirming observation** or manual user promotion do they enter LanceDB as confirmed episodic memories.

### Phase 5: 3-Category Taxonomy Schema in LanceDB
* Tag every LanceDB record with `memory_type`: `procedural`, `declarative`, or `episodic`.
* Include metadata fields: `trust_state` (`confirmed` | `unconfirmed`), `reinforcement_count`, and `last_confirmed_at`.

### Phase 6: Category-Specific Freshness in `search.js`
* Update `src/search.js` to compute category-specific freshness weights during ranking.

---

## 8. Complementary Guardrail Skills Installed

In addition to the core memory engines, three complementary ECC skills are installed in [`.agents/skills`](file:///c:/Backup/WebScout/.agents/skills) to enhance search quality and enforce behavioral verification:

1. **[`iterative-retrieval`](file:///c:/Backup/WebScout/.agents/skills/iterative-retrieval/SKILL.md)**:
   * Progressive 4-phase context retrieval loop: `Dispatch -> Evaluate -> Refine -> Loop` (max 3 cycles).
   * Upgrades simple 1-shot searches by automatically refining keywords and narrowing down relevance gaps when querying project context.

2. **[`eval-harness`](file:///c:/Backup/WebScout/.agents/skills/eval-harness/SKILL.md)**:
   * Eval-Driven Development (EDD) framework for testing the **AI Agent** itself.
   * Measures reliability with `pass@k` metrics (`pass@1`, `pass@3`).
   * Provides deterministic, model, and human graders to verify that the agent respects memories, follows promoted instincts, and doesn't regress.

3. **[`tdd-workflow`](file:///c:/Backup/WebScout/.agents/skills/tdd-workflow/SKILL.md)**:
   * Enforces strict Test-Driven Development (Red $\rightarrow$ Green $\rightarrow$ Refactor) for all code changes.
   * Requires 80%+ test coverage across unit, integration, and edge-case boundary conditions.

