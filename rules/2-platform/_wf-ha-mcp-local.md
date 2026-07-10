# MCP Integration — Workflow & Config

## Data Hierarchy for Diagnosis

| Priority | Source | Strength |
|---|---|---|
| #1 | MCP `GetLiveContext` | Live state, attributes |
| #2 | InfluxDB MCP (Flux) | Historical data, trends |
| #3 | `{{platform.homeassistant.entities_csv_path}}` | Registry overview |
| #4 | Developer Console Template | Manual fallback |

## Diagnosis Workflow

1. `GetLiveContext` → current state + attributes
2. InfluxDB Flux query → last 24h/7d
3. CSV (optional) → confirm integration/platform
4. Propose solution

## InfluxDB MCP

- Package: `influxdb-mcp-server` (npm: idoru/influxdb-mcp-server)
- Protocol: InfluxDB OSS API v2 (Flux)
- Bucket / Org / Measurement schema / Timezone: see platform variables
  - `by_entity` → measurements = entity names
  - `by_unit` → measurements = units
- Entity IDs: omit `sensor.` prefix
- Allowed: read queries, range analysis, pattern detection, comparisons
- Forbidden: writes, bucket management, retention changes

## Provider Config

MCP secrets never go into committed files. Use env-var references in committed config; put real values in gitignored local config or `.meta-config/secrets.local.yaml`.

| Provider | Committed config | Secrets file |
|---|---|---|
| Claude | `.claude/settings.json` → `mcpServers` | `.claude/settings.local.json` |
| Opencode | `opencode.json` → `mcp` | `.opencode/mcp.local.json` |
| Continue | `.continue/config.yaml` → `mcpServers` | `.continue/config.local.yaml` |
| Gemini | `.gemini/settings.json` → `mcpServers` | `.gemini/settings.local.json` |

Template: `howto/configs/mcp-secrets.local-template.yaml`

## If MCP Is Unavailable

- Developer Console Templates for status checks
- Ask the user to verify values manually
- Use CSV from `{{platform.homeassistant.entities_csv_path}}`
- Use safe defaults: `| float(0)`, `default='unknown'`
