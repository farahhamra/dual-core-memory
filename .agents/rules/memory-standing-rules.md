# Standing Rule: Dual-Core Agent Memory Contract

This rule establishes the operational protocol for memory retrieval, immediate invariant preservation, and empirical learning in this workspace.

---

## 1. Pre-Task Relevance Check (Vector Memory)

Before planning or modifying non-trivial code involving database models, architectural components, API contracts, or domain business rules:
1. **Always query `vector-memory`** to check for established patterns, existing schemas, and architectural invariants:
   ```powershell
   python .agents/skills/vector-memory/cli.py search "<query_topic>" --table project_memory
   ```
2. For universal coding conventions or tooling techniques, query:
   ```powershell
   python .agents/skills/vector-memory/cli.py search "<query_topic>"
   ```
3. **Standing Authorization**: Do not ask the user for permission to query memory. Execute queries autonomously and apply relevant findings to your plan or solution.

---

## 2. In-Task Learning & The Dual-Bridge Protocol

Operating environments determine observation mechanisms:
- **Unix / macOS (Claude Code)**: Operates as a System 1 reflex via deterministic lifecycle hooks (`observe.sh`).
- **Native Windows (Antigravity IDE)**: Windows Job Objects terminate detached child processes when hooks exit, and Claude CLI is absent. Learning operates as a **milestone/post-hoc batch mining pipeline (System 2)**.

To ensure zero knowledge loss on Windows, agents must adhere to the **Dual-Bridge Protocol**:

### Bridge 1: Immediate Invariants (Direct Ground Truth)
When a developer confirms a non-negotiable architectural rule, library choice, or project invariant (e.g. *"Never commit .env files"*, *"Use kebab-case for plugin names"*):
- **Do not wait for post-hoc mining.** Save it immediately to permanent declarative memory:
  ```powershell
  python .agents/skills/vector-memory/cli.py save "<title>" "<content>" --table project_memory --category declarative
  ```
- Immediate saves represent 100% intentional ground truth and bypass staging gates.

### Bridge 2: Empirical Habit Mining (Milestone / Task Completion)
At major task milestones, upon invoking `/learn`, or prior to concluding non-trivial sessions:
- Mine freeform chat transcript directives and tool error recoveries:
  ```powershell
  python .agents/skills/continuous-learning-v2/scripts/observe.py
  ```
- Evaluates transcript entries, validates schemas, rejects conversational stop-phrases, and stages candidate instincts in the homunculus.

---

## 3. The Unified Two-Sighting Trust Gate

To protect permanent vector memory from single-aside pollution and unverified guesses:
1. **Symmetric Two-Sighting Discipline**:
   - **Procedural Habits (`observe.py`)**: First sighting of an imperative directive is scored at **`0.65`** (held below the `0.70` gate). Only upon a second sighting/reinforcement does it boost to **`0.85`** and qualify for promotion.
   - **Technical Workarounds (`record-candidate`)**: Staged provisionally as `unconfirmed` on 1st sighting. Promoted to LanceDB as `confirmed` episodic memory only on 2nd sighting.
2. **Promoting Qualified Memories**:
   - Sync all reinforced instincts clearing the 0.70 threshold into LanceDB:
     ```powershell
     python .agents/skills/vector-memory/cli.py sync-instincts
     ```
