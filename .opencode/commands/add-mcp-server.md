---
description: Guided setup to activate an MCP server in this project
allowed-tools: ["Bash", "Read", "Edit"]
argument-hint: "<server-name from mcp-registry.yaml>"
---

Activate an MCP server for this project. $ARGUMENTS

**Step 0 — Check for missing input**

Read `.agent-meta/config/mcp-registry.yaml` and extract all server names (top-level keys under `servers:`).
Read `.meta-config/project.yaml` and extract currently active `mcp-servers:` entries.

Show the user:
- Already active MCP servers (skip these)
- Available servers from the registry with a one-line description each

If $ARGUMENTS is empty or does not match any registry entry:
> "Which MCP server would you like to activate? Available servers:"
> [list available servers with descriptions]
> "Please type the server name to continue."
Stop here and wait for the user to respond. Do not proceed until a valid server name is provided.

**Step 1 — Validate selection**

Confirm the chosen server name exists in the registry. If not:
> "Server '<name>' is not in the registry. Available: [list]. Did you mean one of these?"
Stop and wait for correction.

**Step 2 — Check secrets**

Read the `secrets:` block for the chosen server in `mcp-registry.yaml`.
If secrets are required:
- Check if `.meta-config/secrets.local.yaml` exists
- Show the user which environment variables or secrets need to be set:
  > "This server requires the following secrets. Add them to `.meta-config/secrets.local.yaml`:"
  > [list each secret key and its description]
  > "Have you added the secrets? (yes/no)"
- If no: stop and wait. Remind that `.meta-config/secrets.local.yaml` is gitignored and safe for credentials.
- If yes: continue.

**Step 3 — Activate**

Add the server name to `mcp-servers:` in `.meta-config/project.yaml`.
Run: `python .agent-meta/scripts/sync.py`

**Step 4 — Report**

Show which files were generated per active provider:
- Rule files (e.g. `.claude/rules/mcp-<server>.md`)
- Provider config updates (e.g. `mcpServers` entries in `.claude/settings.json`)
- Any warnings from the sync log

Finish with:
> "MCP server '<name>' is now active. Restart your AI provider to pick up the new tools."
