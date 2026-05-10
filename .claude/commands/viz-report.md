---
description: Generate a session report for the latest agent visualization session
allowed-tools: ["Bash"]
argument-hint: "[--html | --terminal | --json] [--output path]"
---

Generate a report for the most recent visualization session.

**Default (terminal output):**
```bash
python .agent-meta/scripts/viz-report.py --format terminal
```

**HTML report:**
```bash
python .agent-meta/scripts/viz-report.py --format html --output session-report.html
```

**JSON export:**
```bash
python .agent-meta/scripts/viz-report.py --format json
```

**For a specific session:**
```bash
python .agent-meta/scripts/viz-report.py --session <session-id> --format terminal
```

Reports include:
- Session name and duration
- Agent status bars with progress
- Delegation timeline
- Mermaid Gantt chart (HTML only)
- Mermaid sequence diagram (HTML only)
