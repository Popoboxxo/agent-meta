---
description: Start live monitoring of the current agent visualization session
allowed-tools: ["Bash"]
argument-hint: "[--agent <name>]"
---

Start live monitoring of the active visualization session. Updates every 5 seconds.

**Monitor all agents:**
```bash
python .agent-meta/scripts/viz-report.py --watch
```

**Filter by agent name:**
```bash
python .agent-meta/scripts/viz-report.py --watch --agent orchestrator
```

**For a specific session:**
```bash
python .agent-meta/scripts/viz-report.py --session <session-id> --watch
```

Press `Ctrl+C` to stop monitoring.

The terminal view shows:
- Real-time agent status (idle / running / done / error)
- Progress bars relative to session duration
- Live delegation timeline
