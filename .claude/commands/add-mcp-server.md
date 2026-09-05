---
description: Guided setup to activate an MCP server in this project
allowed-tools: ["Bash", "Read", "Edit"]
argument-hint: "<server-name from plugin-catalog.yaml>"
---

Activate an MCP server for this project. $ARGUMENTS

1. Read `.agent-meta/config/plugin-catalog.yaml` (mcp-server entries) and `.meta-config/project.yaml`.
2. If $ARGUMENTS empty/invalid, list available servers and ask.
3. Show required secrets; wait until `.meta-config/secrets.local.yaml` is updated.
4. Add the server to `mcp-servers:` in `.meta-config/project.yaml`.
5. Run `python .agent-meta/scripts/sync.py` and report generated files.

Finish with: "MCP server '<name>' is now active. Restart your AI provider to pick up the new tools."
