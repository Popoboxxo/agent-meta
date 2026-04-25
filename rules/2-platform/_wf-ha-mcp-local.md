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
- **Datenstruktur**: Measurements basieren auf Einheit (z.B. "W"), nicht "state"
- **Entity-IDs**: Ohne "sensor."-Prefix, können vom HA-Namen abweichen

**Erlaubt:** Flux-Queries lesen, Wertebereich-Analysen, Pattern-Erkennung, Vergleiche.
**VERBOTEN:** Schreiboperationen, Bucket-Verwaltung, Retention-Policy-Änderungen.

## Lokale / Projektspezifische MCP-Server

Konfiguration in `settings.local.json` (gitignored — nie committen).
Dokumentation in `.claude/platform-config.yaml`:

```yaml
mcp_servers:
  - name: mempalace
    purpose: >-
      Persistent memory for HA configuration context across sessions.
    tools_allowed:
      - remember
      - recall
    tools_blocked: []
```

**Struktur:**
```
.claude/
  platform-config.yaml      ← gittracked: Beschreibung (kein Secret)
  settings.local.json       ← gitignored: Verbindungsparameter (mit Secrets)
```

## Fehler-Handling wenn MCP nicht verfügbar

- Developer Console Templates für Statusabfragen
- User auffordern, Werte manuell zu prüfen
- CSV aus `{{platform.homeassistant.entities_csv_path}}` nutzen
- Code mit sicheren Defaults: `| float(0)`, `default='unknown'`
