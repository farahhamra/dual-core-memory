---
name: antigravity-vector-memory
description: "Vector-based memory subsystem guide for Antigravity agents to search, save, and delete semantic knowledge using local Ollama nomic-embed-text and LanceDB in /.memory"
license: MIT
metadata:
  author: Farah Hamra
  version: 1.0.0
  triggers:
    - vector memory
    - recall memory
    - save memory
    - project db structure
    - feature tree
    - default_memory
    - project_memory
---

# Antigravity Vector Memory Subsystem

The workspace maintains a high-speed, local embedded vector memory located in `data/` powered by:
- **LanceDB**: Local serverless vector database (stored in `data/`).
- **Ollama**: `nomic-embed-text` generating 768-dimensional embeddings.

For standing authorization and automated execution rules, see [references/memory-automation-rules.md](references/memory-automation-rules.md).

---

## 1. When to Search Memory

Antigravity agents must search memory dynamically to avoid reinventing established patterns or violating architectural decisions:

### Before Planning or Modifying Code
Search `project_memory` whenever:
- Working with database models, relations, or queries (e.g., query for `"prisma schema for <model>"`).
- Working on a specific business module (e.g., query for `"feature tree for <module>"` or `"chart of accounts structure"`).
- Implementing multi-tenant or authorization logic.

### During Debugging & Troubleshooting
Search across memory (`--table all` or `default_memory`) when:
- Encountering cryptic runtime errors, build issues, or database migration errors.
- Wondering if an edge case or workaround was previously identified.

---

## 2.A. When to Save Memory

Agents should proactively persist valuable knowledge to prevent context loss across sessions:

### Save to `project_memory` when:
1. **Database Schema or Structure Changes**:
   - New Prisma models, modified relations, or non-trivial foreign key constraints.
   - Category: `db-schema` or `db-structure`
2. **Feature Tree or Module Architecture**:
   - Creating or modifying hierarchical feature routes (e.g. Sales -> Orders -> Invoices).
   - Category: `feature-tree` or `architecture`
3. **Domain Business Rules**:
   - Critical domain constraints (e.g., recursive account balances, tax calculation logic, inventory valuation methods).
   - Category: `domain-rule` or `convention`

### Save to `default_memory` when:
1. **Reusable Coding Patterns**:
   - Generic patterns (e.g. Fastify/NestJS Zod validation pipe, TanStack table virtualization, clean error envelopes).
   - Category: `best-practice` or `pattern`
2. **Tooling & Agent Optimization Techniques**:
   - Useful shell commands, linting workarounds, or workflow optimizations.
   - Category: `agent-tip`
3. **Error Handling Patterns**:
   - Patterns for handling errors and exceptions.
   - Category: `error-handling`
4. **Security Patterns**:
   - Patterns for handling security concerns.
   - Category: `security`
5. **Performance Patterns**:
   - Patterns for handling performance concerns.
   - Category: `performance`

---

## 2.B. Mandatory Memory Workflow

For every non-trivial coding task:

1. Identify whether existing project knowledge may be relevant.
2. Search `project_memory` before planning if the task involves:
   - database/schema
   - business rules
   - existing features/modules
   - architecture
   - authentication/authorization
   - previously solved problems
3. Search `default_memory` when the problem is a general coding/tooling problem.
4. Use retrieved memories as context, but verify them against current source files when correctness matters.
5. After completing the task, determine whether durable knowledge was created or changed.
6. Save or update memory only when the knowledge is useful beyond the current interaction.

Do not search or save memory for trivial changes such as:
- renaming a local variable
- formatting
- simple CSS adjustments
- typo fixes
- temporary debugging output

---

## 3. Command-Line Reference

Agents can execute these commands directly via `run_command` from the `vector-memory` skill directory:

### Searching Memory
```powershell
# Search default_memory (default)
python cli.py search "Zod request validation pattern"

# Search project_memory (project-specific schemas, feature trees, domain rules)
python cli.py search "chart of accounts schema" --table project_memory

# Search with specific limit and category filter
python cli.py search "Prisma relations" --table project_memory --category "db-schema" --limit 3

# Search across all tables simultaneously
python cli.py search "database indexing strategy" --table all

# Output pure JSON for programmatic parsing
python cli.py search "suppliers query" --table project_memory --json
```

### Saving / Upserting Memory
```powershell
# Save to default_memory
python cli.py save "RFC 7807 Error Envelope" "API errors should return type, title, status, and detail with field errors." --table default_memory --category "best-practice"

# Save project schema memory (defaults to project_memory)
python cli.py save "Account Model Hierarchy" "Account has self-relation parentId -> Account.id. Sub-accounts inherit parent currency." --category "db-schema"

# Save feature tree node
python cli.py save "Sales Module Feature Tree" "Sales Root: Quotations -> Sales Orders -> Delivery Notes -> Sales Invoices." --category "feature-tree"

# Save with custom ID and structured JSON metadata
python cli.py save "Chart of Accounts Hierarchy" "Hierarchical accounts with CTE balance aggregation." --id "coa-schema-v1" --category "db-schema" --meta '{"module":"accounting","orm":"prisma"}'
```

### Provisional Candidate Gate (Error Workarounds & Technical Fixes)
```powershell
# List staged candidates
python cli.py candidates

# Record a technical candidate (1st sighting = staged unconfirmed; 2nd sighting = auto-promoted)
python cli.py record-candidate "Prisma transaction deadlock workaround" "Use interactive transactions with explicit timeout 10000ms."

# Manually confirm and promote a staged candidate
python cli.py confirm-candidate "cand-prisma-transaction-deadlock-workaround"
```

### Syncing Instincts from Continuous Learning v2
```powershell
# Promote CLv2 instincts with confidence >= 0.70 into LanceDB
python cli.py sync-instincts
```

### Inspecting Table Statistics
```powershell
# Display table row counts
python cli.py stats
```

---

## 4. Programmatic Python Usage

Agents or internal automation scripts can also import functions directly:

```python
from memory import search, save, record_candidate, sync_instincts, PROJECT_TABLE

# Semantic Search with Trust and Freshness ranking
results = search("inventory warehouse transfer rules", table=PROJECT_TABLE, limit=5)

# Save/upsert
save(
    title="Inventory Transfer Rules",
    content="Stock transfer requires source warehouse stock lock before destination credit.",
    category="domain-rule",
    metadata={"module": "inventory"},
    table=PROJECT_TABLE,
)

# Stage technical candidate
record_candidate(
    title="Prisma Connection Timeout",
    content="Set pool_timeout = 20 in datasource config.",
)
```
