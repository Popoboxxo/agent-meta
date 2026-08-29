# HACS Integration Development

Verbindlicher Ablauf für die Entwicklung von Home-Assistant-Custom-Components, die über
**HACS** (Home Assistant Community Store) distribuiert werden. Der `hacs-developer` trägt
die kompakten Always-on-Anker; dieser Skill ist die vollständige Referenz (Workflow,
eiserne Regeln mit Begründung/Fehlerklasse, Meta-Datei-Skelett, Test-Trick, Debugging).

## Live-Referenzen dieses Projekts

| Bezug | Wert |
|---|---|
| Integrations-Repo (dieses Projekt) | `{{platform.hacs.integration_repo_url}}` |
| Referenz-Repo (z.B. home-assistant/core) | `{{platform.hacs.reference_repo_url}}` |
| Projekt-Skills (Entwicklung + Review-Gegenstück) | `{{platform.hacs.project_skills}}` |
| Dev-Instanz (Home Assistant) | `{{platform.hacs.dev_instance_url}}` |
| Components-Pfad im Integrations-Repo | `{{platform.hacs.custom_components_path}}` |

**Wenn die Werte oben leer sind oder noch unaufgelöste `platform.hacs.*`-Platzhalter
enthalten:** die Werte fehlen bzw. sind in `.claude/platform-config.yaml` des Projekts
nicht gesetzt (sync.py warnt dazu in `sync.log`). Fallback: Repo-URLs via `git remote -v`
prüfen, Dev-Instanz und Skills beim User erfragen — und die Werte in
`.claude/platform-config.yaml` nachtragen, damit der nächste Sync sie einarbeitet.

## 7-Schritte-Workflow (Reihenfolge zwingend)

1. **Ist-Analyse live per API** — Recherche gegen die Live-Referenzen (Integrations-Repo,
   Referenz-Repo, Projekt-Skills), inkl. Live-Abfrage der Dev-Instanz. Nie aus
   Erinnerung antizipieren: bestehende Entities, Versionen und Entity-Generationen
   zuerst am echten System prüfen.
2. **Konzept** — Name/Domain nach der Domain-Regel (snake_case, **keine Bindestriche**;
   `iot_class` gehört nur ins `manifest.json`, nie ins `hacs.json`), Entity-Schema
   (`unique_id` + `device_info` ab Entity #1), Migrationspfad falls Bestands-Entries
   existieren.
3. **Logik in HA-freie Module** — Reine Logik (Aggregation, Fenster, Serialisierung)
   ohne `homeassistant`-Import. Das ist die Grundlage der Unit-Tests (Test-Trick unten).
4. **Bauen** — Implementierung im Repo-Layout (siehe `hacs-developer`); Meta-Dateien
   und CI von Tag 1 (Skelett unten).
5. **Tests grün** — HA-freie Unit-Tests komplett grün; danach **Pre-Release-E2E** auf
   der Dev-Instanz (Integration manuell installiert/kopiert: laden, Setup-Flow,
   Entities prüfen).
6. **Release-Dreiklang** — Commit → Tag → echtes GitHub Release mit Changelog.
   Tag ↔ `manifest.version` synchron. HACS verteilt nur echte Releases.
7. **Erst dann: Dev-Test & Alt-Cleanup** — HACS kann nur freigegebene Versionen
   ausliefern: der **HACS-Update-Test** (Update von der Vorgängerversion auf der
   Dev-Instanz) und der **Alt-Entity-Cleanup** (verwaiste Alt-Entities entfernen —
   Device-Ansicht prüfen, nicht nur Entitäten-Liste; entfernen statt umbiegen,
   `unique_id` wird nie geändert) laufen **nach** dem Release-Dreiklang, nie davor.

## Eiserne Regeln (Begründung + Fehlerklasse)

### Releases

| Regel | Begründung | Fehlerklasse bei Verstoß |
|---|---|---|
| Tag allein reicht nicht — Release-Dreiklang (Commit → Tag → echtes GitHub Release mit Changelog) | HACS verteilt ausschließlich echte GitHub Releases, keine bloßen Tags | HACS zeigt kein Update; User bleibt auf Alt-Version |
| Tag ↔ `manifest.version` synchron (z.B. `v1.2.3` ↔ `"version": "1.2.3"`) | Release-Asset und Integrations-Selbstauskunft müssen übereinstimmen | Installierte Version meldet Alt-Stand; Update-Erkennung kaputt |
| `manifest.VERSION` nur mit registriertem `async_migrate_entry`-Handler erhöhen | HA ruft beim Entry-Update den Migrator für die neue VERSION auf | `Migration handler not found` beim User-Update |

### Entities

| Regel | Begründung | Fehlerklasse bei Verstoß |
|---|---|---|
| `unique_id` + `device_info` ab Entity #1 | Nachträglich ergänzen erzeugt bei HA komplett neue Entity-IDs — der Alt-Bestand bleibt verwaist | Entity-Generation-Chaos; verwaiste Duplikat-Entities |
| `unique_id` nie ändern | HA koppelt Automatisierungen, Dashboards und History an die unique_id | Beim Update wird jede betroffene Entity neu angelegt; User-Setup bricht |
| Plattform == Dateiname (`PLATFORMS`-Eintrag `<name>` braucht `<name>.py`) | HA lädt Plattform-Module per Dateinamen | `ModuleNotFoundError: custom_components.<domain>.<platform>` |

### Architektur

| Regel | Begründung | Fehlerklasse bei Verstoß |
|---|---|---|
| Entry-Registry in `hass.data[DOMAIN][entry_id]` | Services und Diagnostics greifen zentral darauf zu | Services finden keine Daten / liefern leere Antworten |
| Dynamische Anzahl (beliebig viele Config-Entries, keine Singleton-Annahme) | HA erlaubt mehrere Entries derselben Integration | Zweiter Entry überschreibt den ersten; Setup bricht bei Reload |
| On-read statt Reset-Job (Fenster/Aggregate beim Lesen berechnen) | Reset-Services/Automations sind Zombies nach Restart und verlieren Zustand | Datenverlust bei Restart; tote Reset-Automations im System |

### Flows

| Regel | Begründung | Fehlerklasse bei Verstoß |
|---|---|---|
| Nie blockierend validieren (kein synchrones I/O im Config-Flow) | Blocking Calls frieren den HA-Event-Loop ein | UI friert ein / Event-Loop blocked |
| Korrigierbares in Options-Flow (nicht `entry.data`) | Einstellungen müssen ohne Neuaufsetzen änderbar sein | User muss Integration löschen + neu anlegen |
| Strukturelle Daten explizit in `entry.data` schreiben | Implizite Abhängigkeiten brechen Reproduzierbarkeit und Migration | Setup-Reproduzierbarkeit kaputt; Migration verliert Daten |

### Datenschutz

| Regel | Begründung | Fehlerklasse bei Verstoß |
|---|---|---|
| Diagnostics ohne Geheimnisse/Gesundheitsdaten | Der Diagnostics-Download geht ins öffentliche GitHub Issue | Secret-Leak im Issue-Tracker |
| Exporte nie nach `/config/www` | `/www` ist über den HA-Webserver öffentlich erreichbar | Datenleck über HTTP |
| Tokens zentral speichern (Storage/Entry-Data, nicht verteilt) | Verteilte Tokens landen in Entity-Attributen und Logs | Token im State-Objekt/Log sichtbar |

## Meta-Dateien-Skelett (händisch anlegen — kein Generator)

Die Skelette sind Vorlagen zum Abtippen und ans Projekt anzupassen. Es gibt keinen
Generator — Dateien nicht blind übernehmen.

### `hacs.json` (Repo-Root)

```json
{
  "name": "Human readable integration name",
  "render_readme": true,
  "homeassistant": "2024.1.0"
}
```

`name` ist Pflicht. `homeassistant` = unterstützte HA-Minimalversion.

### `custom_components/<domain>/manifest.json`

```json
{
  "domain": "snake_case_domain",
  "name": "Human readable name",
  "version": "0.1.0",
  "codeowners": ["@your-github-user"],
  "config_flow": true,
  "documentation": "https://github.com/your-org/your-integration",
  "issue_tracker": "https://github.com/your-org/your-integration/issues",
  "iot_class": "cloud_polling",
  "requirements": []
}
```

`iot_class` gehört **nur hierhin**, nie ins `hacs.json`. `version` muss beim Release
dem Git-Tag entsprechen (eiserne Regel Releases).

### `custom_components/<domain>/strings.json` (Master) + `translations/{de,en}.json`

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Verbindung einrichten",
        "data": {
          "host": "Host oder IP-Adresse"
        }
      }
    },
    "error": {
      "cannot_connect": "Verbindung fehlgeschlagen"
    }
  },
  "options": {
    "step": {
      "init": {
        "data": {
          "scan_interval": "Aktualisierungsintervall (Sekunden)"
        }
      }
    }
  }
}
```

Master ist `strings.json`; `translations/de.json` und `translations/en.json` sind
abgeleitet und bei jeder Änderung mitzupflegen (hassfest prüft die Konsistenz).

### `.github/workflows/validate.yml`

```yaml
name: Validate

on:
  push:
    branches: [main]
  pull_request:
  release:
    types: [published]

jobs:
  validate-hacs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: HACS validation
        uses: hacs/action@main
        with:
          category: integration

  validate-hassfest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: hassfest validation
        uses: home-assistant/actions/hassfest@master
```

CI von Tag 1 (eiserne Regel: `hacs/action` + `hassfest`).

## Test-Trick: pytest ohne Home-Assistant-Installation

Reine Logik-Module importieren kein `homeassistant` (Workflow-Schritt 3). Der
Integrations-Code selbst schon — für seine Tests wird HA via Fake-Package in
`sys.modules` geladen, bevor die Integration importiert wird:

```python
# tests/conftest.py
"""Fake-Home-Assistant-Package: pytest läuft ohne echte HA-Installation."""
import sys
from unittest.mock import MagicMock

# Nur greifen, wenn homeassistant wirklich fehlt (echte Installation -> echter Import)
try:
    import homeassistant  # noqa: F401
except ImportError:
    _FAKE_MODULES = [
        "homeassistant",
        "homeassistant.core",
        "homeassistant.config_entries",
        "homeassistant.const",
        "homeassistant.exceptions",
        "homeassistant.helpers",
        "homeassistant.helpers.entity",
        "homeassistant.helpers.entity_platform",
        "homeassistant.helpers.update_coordinator",
        "homeassistant.helpers.storage",
        "homeassistant.helpers.service",
        "homeassistant.helpers.config_validation",
        "homeassistant.util",
        "homeassistant.util.dt",
    ]
    for _mod in _FAKE_MODULES:
        sys.modules.setdefault(_mod, MagicMock())
```

Wichtig:

- **Jedes in der Integration importierte `homeassistant.*`-Sub-Modul** muss in der
  Liste stehen — ein einzelner Fake für `homeassistant` allein genügt nicht, weil
  `from homeassistant.helpers.entity import Entity` das Sub-Modul als eigenes Modul
  im `sys.modules` erwartet. Liste pflegen, wenn neue Imports dazukommen.
- `voluptuous` ist ein pip-Paket ohne HA-Abhängigkeit → echt installieren
  (z.B. in `tests/requirements.txt`), **nicht** faken.
- Die Tests mocken anschließend gezielt `hass`, `coordinator`, `store`; auf der
  Mock-Struktur kann die HA-freie Logik (Fenster, Serialisierung) echte Assertions
  bekommen statt nur Smoke-Tests.

## Debugging-Checkliste: „Es geht nicht"

In dieser Reihenfolge durchgehen:

1. **Alte Entity-Generation?** Device-Ansicht prüfen (nicht nur Entitäten-Liste) —
   verwaiste Alt-Entities sind Post-Release-Alt-Cleanup (Workflow-Schritt 7).
2. **`ModuleNotFoundError: custom_components.<domain>.<platform>`** → Plattform-Datei
   fehlt oder Plattform-Name ≠ Dateiname (eiserne Regel Entities).
3. **`Migration handler not found`** → `manifest.VERSION` ohne registrierten
   Migrator erhöht (eiserne Regel Releases).
4. **HACS zeigt kein Update?** → Echtes GitHub-Release statt nur Tag vorhanden?
   Tag ↔ `manifest.version` synchron? (eiserne Regel Releases).
5. **Setup bricht sofort ab?** → Syntax-/Import-Fehler in EINER Plattform-Datei
   killt die ganze Integration (alle Plattformen teilen den `__init__`-Import).
6. **Services finden nichts?** → `hass.data[DOMAIN][entry_id]`-Registry gefüllt?
   (eiserne Regel Architektur).
7. **Unit-Tests grün, aber auf der Instanz falsch?** → Reihenfolge respektiert?
   Logik HA-frei testen; E2E vor Release manuell, HACS-Update-Test erst nach dem
   Release-Dreiklang (Workflow-Schritte 5–7).
