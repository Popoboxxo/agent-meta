---
description: Add a project-specific agent role (override or extension) to this project
allowed-tools: ["Bash", "Read", "Edit"]
argument-hint: "[role name, e.g. security-auditor]"
---

Add a project-specific agent role to this project. $ARGUMENTS

If $ARGUMENTS is empty, ask for the role name.

Modes:
- **Extension** (recommended): generates `.claude/3-project/<role>-ext.md` via `python .agent-meta/scripts/sync.py --create-ext <role>`. Sync keeps the base generic agent updated; your additions are appended.
- **Override**: create `.claude/3-project/<role>.md` manually. Sync will never overwrite it.

If no generic base exists, recommend override or `/meta-feedback`. Then run `python .agent-meta/scripts/sync.py` and confirm the file path.
