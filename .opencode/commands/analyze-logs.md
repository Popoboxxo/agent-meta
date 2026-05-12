---
description: Analyze log files for errors, patterns, and issues with severity classification (RFC 5424)
allowed-tools: ["Agent"]
argument-hint: "[path/to/logfile | --deep | --quick]"
requires-agent: log-analyzer
---

Delegate to the `log-analyzer` agent with this task:

Analyze logs. $ARGUMENTS

**Argument interpretation:**
- No arguments → auto-discover log files, run in `--quick` mode
- Path provided (file or directory) → analyze that path, `--quick` mode
- `--deep` flag → run in deep mode (codebase search + online lookup for unknown errors)
- `--quick` flag → explicit quick mode (default)
- Path + `--deep` → analyze given path in deep mode

Pass the path and mode to the agent exactly as given in $ARGUMENTS.
