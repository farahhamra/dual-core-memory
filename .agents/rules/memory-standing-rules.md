# Standing Rule: Dual-Core Agent Memory Contract

This rule establishes the operational protocol for memory retrieval and passive learning in this workspace.

## 1. Pre-Task Relevance Check (Vector Memory)
Before planning or modifying non-trivial code involving database models, architectural components, API contracts, or domain business rules:
1. **Always query `vector-memory`** to check for established patterns, existing schemas, and architectural invariants:
   ```powershell
   node .agents/skills/vector-memory/bin/cli.js search "<query_topic>" --table project_memory
   ```
2. For universal coding conventions or tooling techniques, query:
   ```powershell
   node .agents/skills/vector-memory/bin/cli.js search "<query_topic>"
   ```
3. **Standing Authorization**: Do not ask the user for permission to query memory. Execute the query autonomously and apply relevant findings to your plan or solution.

## 2. In-Task Passive Observation (Continuous Learning)
1. The deterministic hook `observe.sh` operates passively in the background on every tool execution.
2. User corrections (*"No, use X instead of Y"*) and error resolutions are recorded automatically.
3. The agent does not need to pause or prompt the user for habit learning; habits are tracked automatically.

## 3. The Promotion Gate
1. Temporary workarounds and unconfirmed error fixes must **NOT** be written directly to `project_memory` on first encounter.
2. Only verified, durable schemas and patterns confirmed by the developer or promoted through the Trust Gate (`sync-instincts.js` with confidence $\ge 0.7$) become permanent memories.
