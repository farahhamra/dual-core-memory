---
name: implementation-plan-clarification-addon
description: "Use it when you need to create an implementation plan"
license: MIT
metadata:
  author: Farah
  project: Electro ERP
---

# Context
This skill acts as a direct follow-up and modifier to the default Antigravity implementation plan skill. It ensures that the agent actively surfaces missing information, technical ambiguities, and design choices directly inside the implementation plan artifact before proceeding to execution.

# Instructions
1. **Analyze with Skepticism:** When generating or updating an implementation plan, proactively identify areas lacking clarity (e.g., edge cases, exact API contracts, environment-specific constraints, or design trade-offs).
2. **Embed a Clarification Section:** In the generated implementation plan, explicitly include a section titled `## Questions & Clarifications`.
3. **Draft Target Questions:** Inside this section, write explicit, high-signal questions for the user. Focus on blocking items that prevent perfect execution.
4. **Pause for Review:** Do not skip directly to the execution phase. Wait for user answers or a direct approval confirmation.