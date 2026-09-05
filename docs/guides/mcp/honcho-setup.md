# Honcho MCP Setup

Honcho is a local memory and context server that provides persistent, cross-session
memory for agents. This guide shows how to activate the `honcho` MCP server that ships
in agent-meta's registry (`config/plugin-catalog.yaml`).

> Honcho is **not** enabled by default (`enabled-by-default: false`). Activation is a
> deliberate, per-project opt-in.

## 1. Run Honcho locally

Start a local Honcho server. Refer to the official Honcho documentation for the current
run instructions:

- Docs: https://docs.honcho.dev
- Repository: https://github.com/plastic-labs/honcho

By default a local Honcho server listens on `http://localhost:8000`.

## 2. Set `MCP_HONCHO_URL`

Point agent-meta at your running Honcho instance. Add the value to your local secrets
file (never committed — it is gitignored):

```yaml
# .meta-config/secrets.local.yaml
MCP_HONCHO_URL: "http://localhost:8000"
```

Alternatively export it as an environment variable in your shell before starting the
provider:

```bash
export MCP_HONCHO_URL="http://localhost:8000"
```

The committed provider configs reference the variable (`${MCP_HONCHO_URL}` /
`{env:MCP_HONCHO_URL}`) — the real value stays local.

## 3. Activate in `project.yaml`

Add `honcho` to the explicit server list:

```yaml
# .meta-config/project.yaml
mcp-servers:
  - honcho
```

## 4. Run sync.py

```bash
python .agent-meta/scripts/sync.py
```

sync.py generates:

- `mcp-honcho.md` rule file in each rules-capable provider directory
- Provider MCP configs (committed with env-var refs + gitignored local with real values)
- `.gitignore` entries for all secrets files

## Tools

| Tool | Purpose |
|------|---------|
| `get_context` | Fetch the current session context |
| `search` | Search the knowledge base and previous sessions |
| `create_conclusion` | Persist an insight permanently |
| `list_conclusions` | List stored insights |
| `chat` | Direct interaction with the Honcho store |
| `get_representation` | Fetch a personalized user representation |

Destructive tools (`delete_conclusion`, `set_config`) are blocked in the registry.

## Notes

- No dedicated `honcho:config` / `honcho:setup` skill files exist yet. If external Honcho
  skills are added to `config/skills-registry.yaml` later, link them here.
- See `howto/mcp-setup.md` for the general MCP concept, secrets handling, and provider
  config layout.
