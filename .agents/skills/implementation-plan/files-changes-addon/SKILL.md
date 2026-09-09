---
name: implementation-plan-files-changes-addon
description: "Use it when creating or updating an implementation plan to include a structured summary table of all planned file changes with estimated line counts"
license: MIT
metadata:
  author: Farah
  project: Electro ERP
---

# Context
This skill acts as an add-on and enhancer for the Antigravity implementation planning workflow. It ensures that every generated implementation plan includes an executive summary table detailing all planned file operations (creation, modification, deletion) and their estimated line impact before presenting the detailed file-by-file breakdown.

# Instructions
1. **Embed the Summary Table:** When drafting or updating an `implementation_plan.md` artifact, always include a dedicated section titled `## Planned File Changes` right before the detailed `## Proposed Changes` section.
2. **Table Schema:** Structure the table with the following columns:
   | Action | File Path | Estimated Impact | Description / Scope |
   | :--- | :--- | :--- | :--- |
   | `[CREATE]` / `[MODIFY]` / `[DELETE]` | `[basename](file:///path/to/file)` | e.g. `+190 lines`, `~45 lines`, `-30 lines` | Brief explanation of changes |

3. **Realistic Estimation & Constraint Adherence:**
   - Base line count estimates on project modularity rules (files should not exceed 250–300 lines).
   - If a file modification causes it to approach or exceed 300 lines, split the estimation across extracted sub-components or helpers.
4. **Comprehensive Coverage:** Ensure every file mentioned in subsequent sections is represented in this summary table so the user can gauge change scope at a glance.
