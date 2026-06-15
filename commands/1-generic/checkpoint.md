---
description: List or resume orchestrator checkpoints from previous sessions
allowed-tools: ["Bash", "Read", "Glob"]
argument-hint: "[list | resume <id> | clear]"
---

Manage orchestrator checkpoints for long-running sessions. $ARGUMENTS

- `list`: Show all available checkpoints in `.meta-viz/`
- `resume <id>`: Resume a specific checkpoint session
- `clear`: Delete all checkpoints

Checkpoints are written automatically when `orchestrator.checkpointing: true` in project.yaml.
