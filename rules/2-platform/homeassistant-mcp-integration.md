# MCP Integration (Home Assistant + InfluxDB)

## ABSOLUTE REGEL: NUR LESENDE OPERATIONEN!

Das Home Assistant MCP darf **ausschließlich für lesende Operationen** verwendet werden.

**ABSOLUTE VERBOTE — ohne Ausnahme, auch nicht auf User-Anfrage:**
- **KEINE** schreibenden Operationen (`HassTurnOn`, `HassTurnOff`, `HassLightSet`, etc.)
- **KEINE** Gerätesteuerung (Licht, Klima, Cover, Media, Vakuum, etc.)
- **KEINE** Zustandsänderungen von Entitäten
- **KEINE** Broadcasts oder Nachrichten senden
- **KEINE** Timer abbrechen
- **KEINE** Todo-Listen-Einträge ändern (`HassListAddItem`, `HassListCompleteItem`, `HassListRemoveItem`)

Wenn der User eine Gerätesteuerung anfragt → **Weise darauf hin, dass dies über die HA-App, Dashboard oder Sprachassistent erfolgen muss, nicht über Claude Code.**

## Erlaubte Home Assistant MCP-Tools (Read-Only)

| Tool | Verwendungszweck |
|------|------------------|
| `GetLiveContext` | Echtzeit-Kontext über aktuellen Zustand von Geräten, Sensoren, Areas. **Primäres Tool für Diagnose & Statusabfragen.** |
| `GetDateTime` | Aktuelles Datum und Uhrzeit von Home Assistant |
| `todo_get_items` | Todo-Listen **abfragen** (nur lesen, nicht ändern!) |

## InfluxDB MCP Server

### Konfiguration
- **Server**: `influxdb-mcp-server` (npm-Paket von [idoru/influxdb-mcp-server](https://github.com/idoru/influxdb-mcp-server))
- **Protokoll**: InfluxDB OSS API v2 (Flux-Queries)
- **Bucket**: `{{platform.homeassistant.influxdb_bucket}}`
- **Organisation**: `{{platform.homeassistant.influxdb_org}}`
- **Datenstruktur**: Measurements basieren auf der **Einheit** (z.B. "W" für Watt), nicht "state"
- **Entity-IDs**: Können vom HA-Namen abweichen (ohne "sensor."-Prefix)

### Erlaubte Verwendungen
- Flux-Queries zum **Lesen** von historischen Daten
- Wertebereich-Analysen (Min/Max/Avg über Zeiträume)
- Pattern-Erkennung und Ausreißer-Analyse
- Vergleich von Sensordaten über Tage/Wochen/Monate

### VERBOTEN für InfluxDB
- **KEINE** Schreiboperationen (kein Daten einfügen/ändern/löschen)
- **KEINE** Bucket- oder Organisations-Verwaltung
- **KEINE** Retention-Policy-Änderungen

## Datenquellen-Hierarchie für Diagnose

| Priorität | Quelle | Stärke |
|-----------|--------|--------|
| **#1** | MCP `GetLiveContext` | Echtzeit-Status, Attribute |
| **#2** | InfluxDB MCP (Flux) | Historische Daten, Trends, Ausreißer |
| **#3** | `{{platform.homeassistant.entities_csv_path}}` | Registry-Übersicht (Integration, Platform, Area) |
| **#4** | Developer Console Template | Manueller Fallback durch User |

## Workflow: Diagnose mit beiden MCP-Servern

```
User: "Mein Sensor springt ständig zwischen Werten."

1. GetLiveContext → Aktuellen State + Attribute prüfen
2. InfluxDB Flux-Query → Historische Werte der letzten 24h/7d analysieren
3. CSV (optional) → Integration/Platform bestätigen
4. Lösungsvorschlag generieren basierend auf den Erkenntnissen
```

## Lokale / Projektspezifische MCP-Server

Neben dem HA-MCP und InfluxDB können projektspezifische MCP-Server lokal laufen.
Diese werden in `settings.local.json` konfiguriert (gitignored — nie committen).

### Dokumentation lokaler MCP-Server

Wenn ein lokaler MCP-Server eingesetzt wird, dokumentiere ihn in `.claude/platform-config.yaml`:

```yaml
mcp_servers:
  - name: mempalace           # Name des MCP-Servers (wie in settings.local.json)
    purpose: >-               # Kurzbeschreibung: Wofür wird er genutzt?
      Persistent memory for HA configuration context across sessions.
    tools_allowed:            # Erlaubte Tools (leer = alle erlaubt)
      - remember
      - recall
    tools_blocked: []         # Explizit verbotene Tools
```

### Umgang mit lokalen MCP-Tools

- **Nutzung dokumentieren**: Welche Tools wofür, in `.claude/platform-config.yaml`
- **Keine Secrets**: Keine API-Keys oder Passwörter via MCP-Tools speichern
- **Gitignore prüfen**: `settings.local.json` muss in `.gitignore` stehen
- **Fallback-Plan**: Wenn lokaler MCP nicht verfügbar → was ist die Alternative?

### Empfohlene Struktur für projektspezifische MCP-Konfiguration

```
.claude/
  platform-config.yaml      ← gittracked: MCP-Server-Beschreibung (kein Secret)
  settings.local.json       ← gitignored: MCP-Server-Verbindungsparameter (mit Secrets)
```

## Fehler-Handling

Wenn MCP-Tools nicht verfügbar sind:
- Falle zurück auf **Developer Console Templates** für Statusabfragen
- Fordere User auf, bestimmte Werte manuell zu prüfen
- Nutze die **`{{platform.homeassistant.entities_csv_path}}`** aus dem Entity-Analyzer-Tool
- Generiere Code mit sicheren Defaults (z.B. `| float(0)`, `default='unknown'`)
