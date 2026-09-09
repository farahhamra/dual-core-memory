# Antigravity Vector Memory Subsystem

Local vector-based semantic memory for Antigravity agents powered by Ollama and LanceDB.

## Technology Stack
- **Database**: [LanceDB](https://lancedb.com/) (`@lancedb/lancedb` v0.37.1) - serverless, zero-daemon, embedded vector database.
- **Embedding Model**: Ollama `nomic-embed-text` (768-dimensional float embeddings, running locally on `http://localhost:11434`).
- **Data Format**: Apache Arrow (`apache-arrow` v18.1.0).

## Tables
1. **`project_memory`**: Stores project-specific knowledge (DB schema structures, feature trees, domain business rules, architectural constraints).
2. **`default_memory`**: Stores global cross-project knowledge (agent guidelines, reusable code patterns, troubleshooting tips).

## Directory Structure
```text
vector-memory/
├── SKILL.md                          # Antigravity skill specification
├── README.md                         # Package documentation
├── package.json                      # npm manifest (scripts, main, bin)
├── index.js                          # Root proxy re-exporting src/index.js
├── bin/
│   └── cli.js                        # Unified CLI runner
├── src/
│   ├── index.js                      # Primary library entrypoint
│   ├── config.js                     # Ollama & LanceDB configuration
│   ├── db.js                         # LanceDB connection & schemas
│   ├── embedder.js                   # Ollama embedding generator
│   ├── search.js                     # Vector similarity search logic
│   ├── save.js                       # Memory record upserting
│   ├── update.js                     # In-place memory updates
│   └── delete.js                     # Record & category deletion
├── scripts/
│   └── test.js                       # End-to-end subsystem test suite
├── references/
│   └── memory-automation-rules.md    # Autonomous execution directives
└── data/
    ├── default_memory.lance/
    └── project_memory.lance/
```

## CLI Commands
Run from the `vector-memory` directory (or use `node <path-to-vector-memory>/bin/cli.js`):

```powershell
# Semantic Search
node bin/cli.js search "RFC 7807 error format"
node bin/cli.js search "database structure for suppliers" --table project_memory

# Save / Upsert Record
node bin/cli.js save "Zod Validation Pattern" "Request DTO schema validation" --category "best-practice"
node bin/cli.js save "COA Schema" "Parent-child account hierarchy" --category "db-schema" --table project_memory

# Update Record In-Place
node bin/cli.js update "<record-id>" --content "Updated documentation or schema" --table project_memory
node bin/cli.js update "<record-id>" --title "New Title" --category "db-schema"

# Delete Record
node bin/cli.js delete "<record-id>"

# Database Overview
node bin/cli.js stats

# Dump Records
node bin/cli.js dump --table project_memory

# Approach 2 Promotion / Trust Gate (Sync CLv2 instincts >= 0.7 into LanceDB)
node bin/cli.js sync-instincts
node bin/cli.js sync-instincts --dry-run
node bin/cli.js sync-instincts --min-confidence 0.8
```

## Running Tests
```powershell
node scripts/test.js
# or via npm
npm test
```

