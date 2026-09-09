# Autonomous Agent Directives & Standing Authorizations

This workspace employs the `dual-core-memory` architecture combining procedural continuous learning and declarative vector memory.

## Pre-Approved Autonomous Operations

Agents working in this repository have standing pre-authorization to execute the following memory operations without prompting the user for confirmation:

1. **Memory Invariant Queries**:
   - Querying `project_memory` for database schemas, architectural contracts, and established design patterns:
     ```powershell
     python .agents/skills/vector-memory/cli.py search "<topic>" --table project_memory
     ```
   - Querying universal coding conventions:
     ```powershell
     python .agents/skills/vector-memory/cli.py search "<topic>"
     ```

2. **Immediate Invariant Preservation (Bridge 1)**:
   - Persisting confirmed developer rules, architectural constraints, and schema invariants directly to LanceDB:
     ```powershell
     python .agents/skills/vector-memory/cli.py save "<title>" "<content>" --table project_memory --category declarative
     ```

3. **Continuous Learning Observation Mining (Bridge 2)**:
   - Running the Native Windows observation and transcript mining pipeline at task completion, upon `/learn`, or at major milestones:
     ```powershell
     python .agents/skills/continuous-learning-v2/scripts/observe.py
     ```

4. **Instinct Trust Gate Sync**:
   - Synchronizing qualified instincts (confidence $\ge 0.70$) into permanent vector memory:
     ```powershell
     python .agents/skills/vector-memory/cli.py sync-instincts
     ```

5. **Provisional Workaround Staging**:
   - Reviewing staged candidates: `python .agents/skills/vector-memory/cli.py candidates`
   - Staging technical workaround candidates: `python .agents/skills/vector-memory/cli.py record-candidate "<title>" "<content>"`

## Trust & Safety Guardrails

- **Do not write speculative or unverified fixes directly to `project_memory`**. Follow the Two-Sighting Trust Gate.
- **Do not commit credentials or environment secrets** to version control.
- **Maintain schema and contract validation** across all subsystem boundaries.
