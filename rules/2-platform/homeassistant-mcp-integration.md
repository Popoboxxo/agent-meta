# MCP Integration (Home Assistant + InfluxDB)

## ABSOLUTE REGEL: NUR LESENDE OPERATIONEN!

**VERBOTEN (ohne Ausnahme):** `HassTurnOn`, `HassTurnOff`, `HassLightSet` und alle schreibenden HA-Operationen, Gerätesteuerung, Zustandsänderungen, Broadcasts, Todo-Einträge ändern.

Gerätesteuerung → HA-App, Dashboard oder Sprachassistent. **Nicht über Claude Code.**

## Erlaubte HA-MCP-Tools

| Tool | Verwendung |
|------|-----------|
| `GetLiveContext` | Echtzeit-Status von Geräten, Sensoren, Areas — primäres Tool |
| `GetDateTime` | Aktuelles Datum/Uhrzeit von HA |
| `todo_get_items` | Todo-Listen nur lesen |

## InfluxDB MCP

- Bucket: `{{platform.homeassistant.influxdb_bucket}}` | Org: `{{platform.homeassistant.influxdb_org}}`
- **Erlaubt:** Flux-Queries lesen, Trends, Ausreißer, Zeitreihen-Vergleiche
- **VERBOTEN:** Schreiben, Bucket-Verwaltung, Retention-Policy

## Diagnose-Hierarchie

MCP GetLiveContext (#1) → InfluxDB Flux (#2) → CSV (#3) → Developer Console (#4)

Vollständige Workflow-Referenz (Konfiguration lokaler MCP-Server, Fehler-Handling):
→ `rules/2-platform/_wf-ha-mcp-local.md` (Read bei Bedarf)
