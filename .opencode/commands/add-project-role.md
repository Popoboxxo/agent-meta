---
description: Add a project-specific agent role (override or extension) to this project
allowed-tools: ["Bash", "Read", "Edit"]
argument-hint: "[role name, e.g. security-auditor]"
---

Add a project-specific agent role to this project. $ARGUMENTS

**Step 1 — Identify the role**

If $ARGUMENTS provides a role name, use it. Otherwise ask the user which role they want to add.

Check which roles are already available:
- Run `python .agent-meta/scripts/sync.py --dry-run` and look at generated agent files
- Read `.meta-config/project.yaml` → `roles:` block to see active roles

**Step 2 — Choose the mode**

Ask the user:

> Two modes are available:
>
> **Extension** (recommended): Adds project-specific content ON TOP of the generic agent.
> The generic agent is still generated and updated by sync. Your additions live in
> `.claude/3-project/<role>-ext.md` and are loaded automatically.
> Use this for: adding project context, domain knowledge, additional instructions.
>
> **Override**: Replaces the generic agent entirely with your own version.
> sync.py will NOT touch the file after creation. You own it fully.
> Use this for: completely custom roles, or when the generic agent doesn't fit at all.

**Step 3 — Create the file**

For **Extension**:
Run: `python .agent-meta/scripts/sync.py --create-ext <role>`
This generates `.claude/3-project/<role>-ext.md` with a managed block showing what the base agent provides, and a free section for project additions.

For **Override**:
Run: `python .agent-meta/scripts/sync.py --create-ext <role>` first to see the base content,
then create `.claude/3-project/<role>.md` (without `-ext`) with the full custom content.
Inform the user: "This file is yours — sync.py will never overwrite it."

**Step 4 — If the role doesn't exist in agent-meta at all**

If the role name is not found in the generic agents:
- Inform the user: "This role has no generic base in agent-meta."
- For Override: create `.claude/3-project/<role>.md` with a starter template:
  ```
  ---
  name: <role>
  description: "<brief description>"
  ---
  # <Role>

  <Instructions for this agent>
  ```
- For Extension: explain that an extension without a base agent has no effect — suggest Override instead or filing a feature request via `/meta-feedback`.

**Step 5 — Sync and confirm**

Run `python .agent-meta/scripts/sync.py` and confirm the new file is active.
Show the user the file path and remind them: "Edit this file directly — it's yours to customize."
