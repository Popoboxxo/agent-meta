---
description: Re-sync all agents without upgrading agent-meta version
allowed-tools: ["Bash", "Bash("]
argument-hint: "[empty]"
---

Run a full agent re-sync for this project. $ARGUMENTS

Run: `python scripts/sync.py`

Then report:
- Action count and warnings from sync.log
- Changed/new/removed agents
- Stage and commit: `git add .claude/ .opencode/ .continue/ .gemini/ CLAUDE.md AGENTS.md docs/agent-graph.html docs/agent-mindmap.md` with message `chore: regenerate agents`
