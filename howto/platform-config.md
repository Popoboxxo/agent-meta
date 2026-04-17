# Platform Config Instantiation

Platform-spezifische Rules und Agenten-Templates können Platzhalter wie
`{{platform.homeassistant.admin_group}}` enthalten. Diese werden beim Sync gegen
Werte aus einer neuen `platform-config.yaml` im Zielprojekt ersetzt — mit sinnvollen
Defaults aus dem Meta-Repo.

---

## Konzept

```
agent-meta/platform-configs/<platform>.defaults.yaml   ← Defaults (im Meta-Repo)
    +
.claude/platform-config.yaml                           ← Overrides (im Zielprojekt)
    ↓  sync.py merged + substituiert
.claude/rules/<platform>-*.md                          ← Generierte Rules (Platzhalter ersetzt)
.claude/agents/<role>.md                               ← Generierte Agenten (Platzhalter ersetzt)
```

**Precedence:** Projekt-Override > Platform-Default

---

## Platzhalter-Syntax

```
{{platform.<plattform>.<schluessel>}}
```

Beispiele:
- `{{platform.homeassistant.notify_group}}`
- `{{platform.homeassistant.influxdb_bucket}}`
- `{{platform.homeassistant.ha_url}}`

**Abgrenzung zu `{{GROSS}}`-Platzhaltern:**

| Typ | Syntax | Quelle | Scope |
|-----|--------|--------|-------|
| Platform-Config | `{{platform.*}}` | `platform-configs/*.defaults.yaml` + `.claude/platform-config.yaml` | Nur für Plattform-Templates |
| Agent-Variables | `{{GROSS_MIT_UNTERSTRICH}}` | `agent-meta.config.yaml` → `variables` | Alle Templates |

Die beiden Namespaces überschneiden sich nie.

---

## Defaults-Datei anlegen (Meta-Repo)

Neue Datei `platform-configs/<platform>.defaults.yaml`:

```yaml
# platform-configs/meine-plattform.defaults.yaml
platform:
  meine-plattform:
    # Leerer String = Pflichtfeld (User muss es überschreiben)
    api_key: ""

    # Gefüllter Wert = sinnvoller Default
    base_url: "http://localhost:8080"
    debug_sensor: "input_boolean.debug_mode"
```

**Konvention:**
- `""` (leerer String) → Pflichtfeld. sync.py emittiert `[WARN]` wenn nicht überschrieben.
- Nicht-leerer Wert → sinnvoller Default, funktioniert ohne Überschreibung.

---

## Projekt-Overrides (Zielprojekt)

Erstelle `.claude/platform-config.yaml` im Zielprojekt — nur was du überschreiben willst:

```yaml
# .claude/platform-config.yaml
# Overrides for agent-meta platform defaults.
# Only set values you want to override — all other defaults remain active.

platform:
  homeassistant:
    notify_group: "mobile_app_all"
    notify_admin_group: "admin_family"
    influxdb_bucket: "homeassistant"
    influxdb_org: "myhome"
    # ha_url und entities_csv_path haben sinnvolle Defaults → keine Überschreibung nötig
```

Die Datei ist **nicht von sync.py verwaltet** — sie liegt vollständig in der Projektkontrolle.

---

## Sync-Verhalten

`sync.py` führt bei jedem normalen Sync folgende Schritte für Platform-Configs aus:

1. Für jede aktive Plattform (aus `platforms` in `agent-meta.config.yaml`):
   - Lade `platform-configs/<platform>.defaults.yaml` aus dem Meta-Repo
   - Lade `.claude/platform-config.yaml` aus dem Zielprojekt (optional)
   - Merge: Projekt-Overrides überschreiben Defaults
2. Substituiere `{{platform.*}}`-Platzhalter in allen generierten Dateien:
   - `.claude/rules/*.md` (Platform-Rules)
   - `.claude/agents/*.md` (Platform-Agenten)
3. Emittiere `[WARN]` wenn ein Pflichtfeld (leerer Default) nicht überschrieben wurde

**Kein Breaking Change:** Bestehende `{{GROSS}}`-Platzhalter aus `agent-meta.config.yaml` bleiben unverändert.

---

## Warnungen verstehen

### Pflichtfeld nicht gesetzt

```
[WARN]  platform-config: required field {{platform.homeassistant.notify_group}} is empty
        — add it to .claude/platform-config.yaml
```

Das Feld hat einen leeren Default und wurde nicht in `.claude/platform-config.yaml` gesetzt.
Der Platzhalter bleibt als leerer String im Output — funktioniert, aber ist wahrscheinlich falsch.

**Lösung:** Wert in `.claude/platform-config.yaml` eintragen.

### Unbekannter Platzhalter

```
[WARN]  platform-config: placeholder {{platform.homeassistant.unknown_key}} not found
        in platform defaults or project overrides — placeholder remains in: ...
```

Ein Template enthält `{{platform.*}}` für einen Key der nicht in den Defaults definiert ist.

**Lösung:** Key in `platform-configs/<platform>.defaults.yaml` mit sinnvollem Default ergänzen.

---

## Verfügbare Platform-Configs

### `homeassistant`

**Datei:** `platform-configs/homeassistant.defaults.yaml`

| Key | Default | Pflichtfeld | Beschreibung |
|-----|---------|:-----------:|--------------|
| `platform.homeassistant.notify_group` | `""` | ✅ | Standard-Notify-Gruppe (alle Bewohner) |
| `platform.homeassistant.notify_admin_group` | `""` | ✅ | Admin/Debug-Notify-Gruppe |
| `platform.homeassistant.debug_sensor` | `input_boolean.automation_debugger` | | Debug-Toggle-Sensor |
| `platform.homeassistant.ha_url` | `http://homeassistant.local:8123` | | HA-Instanz URL |
| `platform.homeassistant.influxdb_bucket` | `""` | ✅ | InfluxDB Bucket-Name |
| `platform.homeassistant.influxdb_org` | `""` | ✅ | InfluxDB Organisation |
| `platform.homeassistant.entities_csv_path` | `hass_entities.csv` | | Pfad zur Entity-CSV |

---

## Neue Platform-Config hinzufügen

1. Neue Datei `platform-configs/<platform>.defaults.yaml` anlegen
2. In allen `rules/2-platform/<platform>-*.md` und `agents/2-platform/<platform>-*.md`
   hartcodierte Werte durch `{{platform.<platform>.<key>}}`-Platzhalter ersetzen
3. In der Dokumentation (diese Datei) die neue Tabelle ergänzen

Keine Änderung an `sync.py` nötig — das System arbeitet automatisch für jede Plattform
die in `agent-meta.config.yaml` → `platforms` aktiv ist und eine Defaults-Datei hat.

---

## Beispiel: Vollständige Einrichtung

**Schritt 1: Zielprojekt konfigurieren** (`agent-meta.config.yaml`):
```json
{
  "platforms": ["homeassistant"],
  ...
}
```

**Schritt 2: Platform-Overrides anlegen** (`.claude/platform-config.yaml`):
```yaml
platform:
  homeassistant:
    notify_group: "mobile_app_alle"
    notify_admin_group: "admin_notifications"
    influxdb_bucket: "homeassistant"
    influxdb_org: "myhome"
```

**Schritt 3: Sync ausführen**:
```bash
python .agent-meta/scripts/sync.py --config agent-meta.config.yaml
```

**Ergebnis:** Alle `{{platform.homeassistant.*}}`-Platzhalter in generierten Rules und
Agenten werden mit den konfigurierten Werten ersetzt.
