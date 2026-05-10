---
description: Generate a session report for the latest agent visualization session
allowed-tools: ["Bash"]
argument-hint: "[--html | --terminal | --json] [--output path]"
---

Generate a report for the most recent visualization session. Pass flags via `$ARGUMENTS`.

```bash
FLAGS="$ARGUMENTS"

# Default (terminal output) if no flags given
if [ -z "$FLAGS" ]; then
    python .agent-meta/scripts/viz-report.py --format terminal
else
    python .agent-meta/scripts/viz-report.py $FLAGS
fi
```

**Examples:**
- `$ARGUMENTS = "--format html --output report.html"`
- `$ARGUMENTS = "--session <id> --format terminal"`
- `$ARGUMENTS = "--format json"`

Reports include:
- Session name and duration
- Agent status bars with progress
- Delegation timeline
- Mermaid Gantt chart (HTML only)
- Mermaid sequence diagram (HTML only)
