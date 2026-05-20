# MCP Integration — Workflow & Konfigurationsreferenz

## Datenquellen-Hierarchie für Diagnose

| Priorität | Quelle | Stärke |
|-----------|--------|--------|
| **#1** | MCP `GetLiveContext` | Echtzeit-Status, Attribute |
| **#2** | InfluxDB MCP (Flux) | Historische Daten, Trends, Ausreißer |
| **#3** | `{{platform.homeassistant.entities_csv_path}}` | Registry-Übersicht |
| **#4** | Developer Console Template | Manueller Fallback |

## Diagnose-Workflow

```
User: "Mein Sensor springt ständig zwischen Werten."

1. GetLiveContext → Aktuellen State + Attribute prüfen
2. InfluxDB Flux-Query → Historische Werte der letzten 24h/7d
3. CSV (optional) → Integration/Platform bestätigen
4. Lösungsvorschlag generieren
```

## InfluxDB MCP Konfiguration

- **Paket**: `influxdb-mcp-server` (npm: idoru/influxdb-mcp-server)
- **Protokoll**: InfluxDB OSS API v2 (Flux-Queries)
- **Bucket**: `{{platform.homeassistant.influxdb_bucket}}`
- **Organisation**: `{{platform.homeassistant.influxdb_org}}`
- **Measurement-Schema**: `{{platform.homeassistant.influxdb_measurement_schema}}`
  - `by_entity` → Measurements = Entity-Namen (Standard-HA-Verhalten)
  - `by_unit` → Measurements = Einheiten ("W", "°C", "kWh") — unüblich, aber möglich
- **Timezone**: `{{platform.homeassistant.influxdb_timezone}}` — InfluxDB speichert UTC, Abfragefenster entsprechend anpassen
- **Entity-IDs**: Ohne "sensor."-Prefix, können vom HA-Namen abweichen

**Erlaubt:** Flux-Queries lesen, Wertebereich-Analysen, Pattern-Erkennung, Vergleiche.
**VERBOTEN:** Schreiboperationen, Bucket-Verwaltung, Retention-Policy-Änderungen.

## MCP-Konfiguration: Provider-Übersicht

MCP-Secrets gehören **niemals** in committed Dateien. Für jeden Provider:

| Provider | Committed (env-var refs) | Gitignored (echte Secrets) |
|---|---|---|
| Claude | `.claude/settings.json` → `mcpServers` | `.claude/settings.local.json` |
| Opencode | `opencode.json` → `mcp` | `.opencode/mcp.local.json` |
| Continue | `.continue/config.yaml` → `mcpServers` | `.continue/config.local.yaml` |
| Gemini | `.gemini/settings.json` → `mcpServers` | `.gemini/settings.local.json` |

Zentraler Secret-Store: `.meta-config/secrets.local.yaml` (gitignored, einmalig befüllen).

## Konfigurationsbeispiele

### Claude — `.claude/settings.json` (committed, keine Secrets)

```json
{
  "mcpServers": {
    "home-assistant": {
      "type": "sse",
      "url": "${MCP_HA_URL}/api/mcp_server/sse",
      "headers": {
        "Authorization": "Bearer ${MCP_HA_TOKEN}"
      }
    },
    "influxdb": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "influxdb-mcp-server"],
      "env": {
        "INFLUXDB_URL": "${MCP_INFLUXDB_URL}",
        "INFLUXDB_TOKEN": "${MCP_INFLUXDB_TOKEN}",
        "INFLUXDB_ORG": "${MCP_INFLUXDB_ORG}",
        "INFLUXDB_BUCKET": "${MCP_INFLUXDB_BUCKET}"
      }
    }
  }
}
```

### Claude — `.claude/settings.local.json` (gitignored, echte Werte)

```json
{
  "mcpServers": {
    "home-assistant": {
      "env": {
        "MCP_HA_URL": "http://192.168.1.100:8123",
        "MCP_HA_TOKEN": "eyJhbGciOiJIUzI1NiIsInR5..."
      }
    },
    "influxdb": {
      "env": {
        "MCP_INFLUXDB_URL": "http://192.168.1.100:8086",
        "MCP_INFLUXDB_TOKEN": "my-long-influxdb-token==",
        "MCP_INFLUXDB_ORG": "homeassistant",
        "MCP_INFLUXDB_BUCKET": "homeassistentbucket"
      }
    }
  }
}
```

### Opencode — `opencode.json` (committed, keine Secrets)

> **Hinweis:** Opencode verwendet `{env:VARIABLE_NAME}`-Syntax (nicht `${VAR}`) und den Key `"environment"` (nicht `"env"`).
> Das `command`-Feld ist ein Array: `["command", "arg1", "arg2"]`.

```json
{
  "mcp": {
    "home-assistant": {
      "type": "streamable-http",
      "url": "{env:MCP_HA_URL}/api/mcp",
      "headers": { "Authorization": "Bearer {env:MCP_HA_TOKEN}" }
    },
    "influxdb": {
      "type": "stdio",
      "command": ["npx", "-y", "influxdb-mcp-server"],
      "environment": {
        "INFLUXDB_URL": "{env:MCP_INFLUXDB_URL}",
        "INFLUXDB_TOKEN": "{env:MCP_INFLUXDB_TOKEN}",
        "INFLUXDB_ORG": "{env:MCP_INFLUXDB_ORG}",
        "INFLUXDB_BUCKET": "{env:MCP_INFLUXDB_BUCKET}"
      }
    }
  }
}
```

### Opencode — `.opencode/mcp.local.json` (gitignored, echte Werte)

```json
{
  "MCP_HA_URL": "http://192.168.1.100:8123",
  "MCP_HA_TOKEN": "eyJhbGciOiJIUzI1NiIsInR5...",
  "MCP_INFLUXDB_URL": "http://192.168.1.100:8086",
  "MCP_INFLUXDB_TOKEN": "my-long-influxdb-token==",
  "MCP_INFLUXDB_ORG": "homeassistant",
  "MCP_INFLUXDB_BUCKET": "homeassistentbucket"
}
```

## Zentraler Secret-Store: `.meta-config/secrets.local.yaml`

Alle Provider können Werte aus dieser Datei beziehen (gitignored):

```yaml
# .meta-config/secrets.local.yaml — NIEMALS committen
MCP_HA_URL: "http://192.168.1.100:8123"
MCP_HA_TOKEN: "eyJhbGciOiJIUzI1NiIsInR5..."
MCP_INFLUXDB_URL: "http://192.168.1.100:8086"
MCP_INFLUXDB_TOKEN: "my-long-influxdb-token=="
MCP_INFLUXDB_ORG: "homeassistant"
MCP_INFLUXDB_BUCKET: "homeassistentbucket"
```

Template: `howto/configs/mcp-secrets.local-template.yaml`

## Fehler-Handling wenn MCP nicht verfügbar

- Developer Console Templates für Statusabfragen
- User auffordern, Werte manuell zu prüfen
- CSV aus `{{platform.homeassistant.entities_csv_path}}` nutzen
- Code mit sicheren Defaults: `| float(0)`, `default='unknown'`
