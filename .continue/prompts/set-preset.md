---
description: Change the DoD preset or speech mode of this project
allowed-tools: ["Read", "Edit", "Bash"]
argument-hint: "<preset> or speech:<mode>"
invokable: true
---

Change the project DoD preset or speech mode. $ARGUMENTS

Valid DoD presets: see `config/dod-presets.yaml` under `presets:`.
Valid speech modes: see `config/project-config.schema.json` under `speech-mode`.

Read `.meta-config/project.yaml`, confirm the change, update `dod-preset` or `speech-mode`, then run sync (project: `python .agent-meta/scripts/sync.py`; agent-meta itself: `python scripts/sync.py`).
