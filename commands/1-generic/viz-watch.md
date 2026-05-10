---
description: Start live monitoring of the current agent visualization session
allowed-tools: ["Bash"]
argument-hint: "[--agent <name>]"
---

Start live monitoring of the active visualization session. Updates every 5 seconds.

```bash
FLAGS="$ARGUMENTS"

# Default: open live dashboard in browser
if [ -z "$FLAGS" ]; then
    python scripts/viz-server.py toggle
else
    python scripts/viz-report.py --watch $FLAGS
fi
```

**Examples:**
- `$ARGUMENTS = "--agent orchestrator"` — Terminal watch, filter by agent
- `$ARGUMENTS = "--session <session-id>"` — Terminal watch, specific session
- No arguments — Opens browser dashboard with real-time graph

Press `Ctrl+C` to stop terminal monitoring. The browser dashboard auto-refreshes via API.
