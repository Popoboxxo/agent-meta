# ReqFlow MCP Setup

ReqFlow is a self-hosted requirements-engineering platform (requirements, architecture,
tests, traceability, ADRs, risks, issues, glossary, AI-assisted derivation). This guide
shows how to activate the `reqflow` MCP server that ships in agent-meta's registry
(`config/mcp-registry.yaml`).

> ReqFlow is **not** enabled by default (`enabled-by-default: false`). Activation is a
> deliberate, per-project opt-in.

## 1. Run ReqFlow locally

Start a local, self-hosted ReqFlow instance (backend + MCP server). Refer to the ReqFlow
project documentation for the current setup and run instructions.

By default a local ReqFlow backend listens on `http://localhost:8000` (adjust to your
setup). The MCP endpoint is exposed via SSE at:

```
{ReqFlow base URL}/mcp/sse/
```

## 2. Create an API key and set secrets

ReqFlow's MCP server authenticates via an API key sent in the `X-API-Key` header. Keys
must start with the `rf_` prefix — any other credential format (including a JWT bearer
token) is rejected with `AUTH_FAILED`. Generate a key for the workspace you want to
expose via the ReqFlow admin UI or its REST API.

Add the values to your local secrets file (never committed — it is gitignored):

```yaml
# .meta-config/secrets.local.yaml
MCP_REQFLOW_URL: "http://localhost:8000"
MCP_REQFLOW_API_KEY: "rf_xxxxxxxxxxxxxxxx"
```

Alternatively export them as environment variables in your shell before starting the
provider:

```bash
export MCP_REQFLOW_URL="http://localhost:8000"
export MCP_REQFLOW_API_KEY="rf_xxxxxxxxxxxxxxxx"
```

The committed provider configs reference the variables (`${MCP_REQFLOW_URL}` /
`{env:MCP_REQFLOW_URL}`, same pattern for the API key) — the real values stay local.

## 3. Activate in `project.yaml`

Add `reqflow` to the explicit server list:

```yaml
# .meta-config/project.yaml
mcp-servers:
  - reqflow
```

Or via slash command (where supported): `/add-mcp-server reqflow`

## 4. Run sync.py

```bash
python .agent-meta/scripts/sync.py
```

sync.py generates:

- `mcp-reqflow.md` rule file in each rules-capable provider directory
- Provider MCP configs (committed with env-var refs + gitignored local with real values)
- `.gitignore` entries for all secrets files

## Tools

| Tool | Purpose |
|------|---------|
| `requirement.get` / `requirement.query` | Fetch or search requirements |
| `requirement.create` / `.update` / `.decompose` / `.validate` / `.derive` | Author and evolve requirements (write) |
| `requirement.check_consistency` | Consistency check across the requirement tree |
| `needs.read` / `.create` / `.update` | Stakeholder needs |
| `needs.get_traces` / `.derive_requirements` | Needs traceability and requirement derivation |
| `architecture.get` / `.query` | Fetch or search architecture elements |
| `architecture.create` / `.update` / `.link` / `.decompose` / `.decompose_commit` | Author architecture (write) |
| `test.get` / `.query` | Fetch or search tests |
| `test.create` / `.update` / `.link` / `.run_create` / `.run_report_results` | Author tests and report test runs (write) |
| `test.run_get` / `.derive_from_requirement` | Read a test run / derive tests from a requirement |
| `traceability.query` / `.suggest_links` | Cross-artifact traceability and link suggestions |
| `artifact.search` / `.get_tree` | Full-text search and artifact tree |
| `workspace.get_context` | Read the active workspace context |
| `adr.read` / `.create` / `.update` / `.delete` | Architecture Decision Records (write) |
| `risk.read` / `.create` / `.update` / `.delete` | Risks (write) |
| `issue.read` / `.create` / `.update` / `.delete` | Issues (write) |
| `glossary.read` / `.create` / `.update` / `.delete` | Glossary entries (write) |
| `prompt_template.get` | Read the content of an LLM prompt-template slot |
| `ai_derivation.derive_requirements_from_need` / `.suggest_architecture_for_requirement` / `.decompose_requirement_next_level` | AI-assisted derivation |

Write tools require **Editor** or **Admin** role in the ReqFlow workspace (RBAC) — a
Viewer-only API key receives `PERMISSION_DENIED`.

Administrative/destructive namespaces are blocked in the registry and never reach
ReqFlow via this MCP server: `admin.*`, `user.*`, `permissions.*`, `audit.*`, `events.*`,
`workspace.close` / `.reactivate` / `.delete`.

## Notes

- No dedicated `reqflow:config` / `reqflow:setup` skill files exist yet. If external
  ReqFlow skills are added to `config/skills-registry.yaml` later, link them here.
- See `howto/mcp-setup.md` for the general MCP concept, secrets handling, and provider
  config layout.
