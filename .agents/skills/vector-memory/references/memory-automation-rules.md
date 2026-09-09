# Standing Authorization & Automated Execution: Memory Subsystems

## Standing Pre-Approval
The agent has standing, full authorization to execute all vector memory and human-readable memory commands immediately via `run_command` **WITHOUT asking the user for permission or confirmation**:

### 1. Vector Memory Subsystem
- `node bin/cli.js search ...`
- `node bin/cli.js save ...`
- `node bin/cli.js update ...`
- `node bin/cli.js delete ...`
- `node bin/cli.js stats`

**Autonomous Actions**:
- Before planning or implementing any complex database, module, or business logic change, **automatically** run `node bin/cli.js search "<topic>" --table project_memory` or `node bin/cli.js search "<pattern>"` without asking.
- When a durable architecture decision, Prisma schema change, or reusable pattern is created, **automatically** save it via `node bin/cli.js save` without asking.

### 2. Human-Readable Project Memory Subsystem (`/.utils/tools/project-human-memory`)
- `node .utils/tools/project-human-memory/cli.js check <file>`
- `node .utils/tools/project-human-memory/cli.js process <file>`
- `node .utils/tools/project-human-memory/cli.js status`
- `node .utils/tools/project-human-memory/cli.js sync`
- `node .utils/tools/project-human-memory/cli.js deleted`
- `node .utils/tools/project-human-memory/test.js`

**Autonomous Actions**:
- Whenever reading or modifying relevant project files, immediately run `check` and `process` to verify SHA-256 hashes and maintain `list.json`.
- When durable product capabilities change, immediately update `features.md` and `description.md` without prompting the user for approval.

## Execution Directive
Never output messages like:
- *"Would you like me to run the memory search command?"*
- *"Should I update features.md and list.json now?"*
- *"May I have permission to check the vector database?"*

Instead, execute the tool calls directly and report the relevant findings or completed updates.
