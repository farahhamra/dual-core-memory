# Standing Authorization & Automated Execution: Dual-Core Memory Subsystems

## Standing Pre-Approval
The agent has standing, full authorization to execute memory commands immediately via `run_command` **WITHOUT asking the user for permission or confirmation**:

### 1. Vector Memory Commands (`.agents/skills/vector-memory/cli.py`)
- `python cli.py search ...`
- `python cli.py save ...`
- `python cli.py candidates`
- `python cli.py record-candidate ...`
- `python cli.py confirm-candidate ...`
- `python cli.py sync-instincts`
- `python cli.py stats`

**Autonomous Actions**:
- Before planning or implementing any non-trivial database, module, or architecture change, **automatically** run `python .agents/skills/vector-memory/cli.py search "<topic>" --table project_memory` without asking.
- When an established architectural constraint, Prisma schema, or durable convention is finalized, **automatically** persist it via `python .agents/skills/vector-memory/cli.py save` without prompting.
- When an error workaround is observed during troubleshooting, route it via `python .agents/skills/vector-memory/cli.py record-candidate` to stage it through the Provisional Gate.

### 2. Continuous Learning Instincts
- The background hook (`hooks/observe.sh`) runs passively on tool execution.
- High-confidence procedural habits ($\ge 0.70$) are synced into LanceDB via `python .agents/skills/vector-memory/cli.py sync-instincts`.

## Execution Directive
Never output messages asking for permission to use memory, such as:
- *"Would you like me to search project memory first?"*
- *"May I check the vector database for existing patterns?"*
- *"Should I save this schema to memory?"*

Instead, execute the memory lookups and saves autonomously and report the relevant findings or completed updates directly in your response.
