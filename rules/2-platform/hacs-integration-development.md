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
   Tag-Format: Stable `v1.2.3`, Beta `v1.3.0b0` als Pre-Release — Details im
   Abschnitt Release-Naming-Best-Practice unten.
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
| `suggested_object_id` auf den englischen Namen pinnen (`has_entity_name` + `translation_key` für den lokalisierten Anzeigenamen) | HA >= 2026.9 erzeugt object_ids für Sprachen in `NATIVE_ENTITY_IDS` (u.a. Deutsch) aus der lokalisierten Übersetzung statt aus dem Englischen — ohne Pinning wechselt object_id/entity_id mit der Systemsprache | entity_id ändert sich/verwaist bei Sprachwechsel — gleiche Schadensklasse wie die `unique_id`-Regel, nur über einen anderen Mechanismus (`unique_id` != object_id) |
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

## Sprache, Namen & Identität

Ergänzt die eiserne Regel `suggested_object_id` (Tabelle Entities oben) um Referenz-Code
und die Etikette für eine geteilte Dev-Instanz.

**Object-ID-Pinning (Referenz-Implementierung):** `Popoboxxo/ha-health-o-mat`,
`custom_components/health_o_mat/entity.py`, Basisklasse `HealthOMatEntity`:

```python
@property
def suggested_object_id(self) -> str | None:
    """Objekt-IDs (Entity-ID-Suffixe) immer aus dem ENGLISCHEN Namen.

    HA >= 2026.9 erzeugt für Sprachen in NATIVE_ENTITY_IDS (u. a. Deutsch)
    Objekt-IDs in der Systemsprache — die IDs würden mit der Sprache
    wechseln (z. B. `melder_sehr_schlecht`). Wir pinnen die Suffixe auf
    Englisch: stabil, lesbar, sprachunabhängig. Der Anzeigename bleibt
    davon unberührt (folgt weiterhin der Systemsprache).
    """
    platform_data = self.platform_data
    if (
        platform_data is not None
        and type.__getattribute__(self.__class__, "name")
        is type.__getattribute__(Entity, "name")
    ):
        name = self._name_internal(
            self._object_id_device_class_name,
            getattr(platform_data, "default_language_platform_translations", None) or {},
        )
        if name is not UNDEFINED:
            return name
    return super().suggested_object_id
```

Kombiniert mit `has_entity_name = True` + `_attr_translation_key`: der **Anzeigename**
bleibt lokalisiert (folgt der Systemsprache), das **object_id/entity_id** ist auf
Englisch gepinnt — stabil und sprachunabhängig.

**Namenslokalisierung (Referenz-Implementierung):** Der Anzeigename kommt ausschließlich
aus den Übersetzungen — der Code trägt **kein** Namens-Literal:

```python
class HealthOMatPowerSensor(HealthOMatEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "power"
    # VERBOTEN (nicht lokalisierbar, bricht den Sprachwechsel):
    # _attr_name = "Leistung"
    # name = "Leistung"  # Property-Override mit Literal
```

| Regel | Begründung | Fehlerklasse |
|---|---|---|
| Jedes hartcodierte `_attr_name`/`name`-Literal ist **absolut verboten** — stattdessen `_attr_has_entity_name = True` + `_attr_translation_key`. Keine Ausnahme für `has_entity_name = False`. | Nur so zieht HA den Anzeigenamen aus `strings.json`/`translations` und respektiert den Sprachwechsel; ein Literal friert eine Sprache dauerhaft ein | `friendly_name` wechselt nicht mit der Systemsprache — identische Schadensklasse wie das Object-ID-Pinning (`unique_id` != object_id) |

**Master/Ableitung:** `strings.json` ist der englische Master; `translations/{de,en}.json`
sind abgeleitet (siehe Meta-Dateien-Skelett unten) — der Master trägt die Identität,
Übersetzungen tragen nur den zur Laufzeit angezeigten `friendly_name`.

**Erstregistrierungs-Regel:** Ohne das Pinning oben (oder auf HA < 2026.9) bestimmt die
zum Zeitpunkt der **Erstregistrierung** aktive Systemsprache das object_id dauerhaft —
Entities in der beabsichtigten Sprache erstregistrieren, eine spätere Umbenennung ist
ein Breaking Change (vgl. `unique_id` nie ändern, Tabelle Entities oben).

**Rename = Breaking Change:** Jede Änderung, die die `entity_id`-Erzeugung verschiebt
(`entity_id`, `original_name`, `translation_key`, Object-ID-Pinning), ist ein Breaking
Change → **MAJOR** + **💥-Eintrag mit Migrationshinweis** (Entity-Registry-Migration
unten, `manifest.VERSION`-Bump; Release-Naming-Best-Practice). Für den Umgang mit dem
Alt-Bestand gilt der Verweis auf den **Post-Release-Orphan-Cleanup** in Workflow-Schritt
7: verwaiste Alt-Entities werden erst **nach** dem Release entfernt, nie durch Ändern der
`unique_id`.

**Etikette auf einer geteilten Dev-Instanz** (mehrere Integrationen/Domains auf derselben
Home-Assistant-Instanz):

| Aspekt | Regel |
|---|---|
| Sync (Neustart, ~10–30s) | Pro-Domain sicher — die Registry der anderen Domains bleibt erhalten |
| Reset | Destruktiv für **alle** Domains auf der Instanz — vorher koordinieren, nicht ungefragt ausführen |
| `unique_id` | Akkumuliert dauerhaft in der geteilten Registry über alle Domains hinweg — nie ändern (Tabelle Entities oben) |
| Systemsprache wechseln | Instanzweiter Blast-Radius: rendert `friendly_name`s **aller** Domains neu und riskiert Erstregistrierungen laufender Arbeiten anderer Domains — vorher koordinieren |
| Tokens/State | Nie committen oder zwischen Domains kopieren |

### Entity-Registry-Migration bei Umbenennung

Ein Rename ändert **nie** die `unique_id` (eiserne Regel Entities oben). Geändert werden
ausschließlich `entity_id` und `original_name` — über den HA-Entity-Registry-Helper
`er.async_migrate_entries`, aufgerufen **innerhalb** des registrierten
`async_migrate_entry`-Handlers, zusammen mit einem `manifest.VERSION`-Bump
(Breaking → MAJOR, siehe Release-Naming-Best-Practice unten). Das ist **nicht** das
`entry.data → entry.options`-Rezept weiter oben: dort wandern Entry-Daten, hier werden
Entity-Registry-Einträge umbenannt.

```python
# custom_components/<domain>/__init__.py
from homeassistant.helpers import entity_registry as er

async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """v1 -> v2: Entity umbenennen, unique_id bleibt stabil."""
    if entry.version < 2:
        def _rename(reg_entry: er.RegistryEntry) -> dict[str, str] | None:
            if reg_entry.unique_id == "health_o_mat_power_old":
                return {
                    "new_entity_id": "sensor.health_o_mat_power",
                    "original_name": "Power",
                }
            return None

        er.async_migrate_entries(hass, entry.entry_id, _rename)
        hass.config_entries.async_update_entry(entry, version=2)
    return True
```

`manifest.json`: `"version": "2.0.0"` (Breaking), GitHub-Release mit 💥-Entry und
Migrationshinweis. Verwaiste Alt-Entities werden erst im **Post-Release-Cleanup**
(Workflow-Schritt 7) entfernt — nie durch Ändern der `unique_id`.

## Release-Naming-Best-Practice

Verbindliches Naming für Tags, `manifest.version` und GitHub-Releases — ergänzt die
eisernen Regeln Releases um Format- und Lifecycle-Details. HACS leitet die Version aus
dem Tag des letzten echten GitHub Releases ab und vergleicht Versionen mit
AwesomeVersion (PEP-440), nicht per String-Parsing — Formatfehler führen zu
`Invalid version` bzw. kaputter Update-Erkennung.

| Regel | Begründung | Fehlerklasse bei Verstoß |
|---|---|---|
| Stable-Tags als `vMAJOR.MINOR.PATCH`; der `v`-Prefix gehört **nur** in den Tag | `v1.2.3` ist Tag-Konvention, keine Semantic Version | `v` in `manifest.version` → `Invalid version` (hassfest/HACS-Validation) |
| `manifest.version` = bare SemVer **ohne** `v`, exakt dem Tag-Suffix entsprechend (`v1.2.3` ↔ `"version": "1.2.3"`) | Release-Asset und Integrations-Selbstauskunft müssen zeichenidentisch sein; Versionsvergleiche laufen über AwesomeVersion (PEP-440) | Abweichung → installierte Version meldet Alt-Stand; Sortier-/Update-Erkennung kaputt |
| Beta-/Pre-Release-Tags als `vX.Y.Zb<N>` (z.B. `v1.3.0b0`) und das GitHub-Release als **pre-release** flaggen; `manifest.version` entspricht exakt dem Tag-Suffix (`v1.3.0b0` ↔ `"version": "1.3.0b0"`) | PEP-440-Beta-Suffix `b<N>` sortiert korrekt vor dem Stable-Release; HACS 2.0 liefert Pre-Releases nur über die `switch.<repo>_pre_release`-Entity (default OFF) aus | Beta ohne pre-release-Flag → alle User bekommen die Beta via Update-Check |
| Promotion beta→stable = neuer Release (`v1.3.0`), nie den Tag mutieren; Tags/Releases sind immutable — nie verschieben, löschen, wiederverwenden | HACS cacht Versionen; verschobene/gelöschte Tags bleiben in bestehenden Installationen referenziert | Tag-Reset/Mutation → User bleiben auf Alt-Stand; Update-Check findet die Version nicht mehr |
| Release-Notes-Mindeststruktur: Summary + ✨ New features + 💥 Breaking changes (je mit Migration-Hinweis; Breaking-Notes sind bei MAJOR Pflicht wegen der Migrator-Regel) + Full-Changelog-Link; optional zusätzlich `CHANGELOG.md` | HACS zeigt die letzten Releases in der Update-Auswahl; User entscheiden anhand der Notes über das Update | Fehlende Breaking-Notes → User aktualisieren ohne Migrationshinweis; Setup bricht beim Update |
| SemVer-Disziplin: MAJOR = Breaking, MINOR = Feature, PATCH = Fix; `unique_id`-/Entity-Änderungen sind **immer** breaking → MAJOR; `v0.x` nicht ohne Hinweis als „stabil" deklarieren | Entity-Änderungen erzeugen bei HA neue Entity-IDs (eiserne Regel Entities) — für Bestands-User zwingend Breaking | Entity-Änderung als MINOR/PATCH → User verlieren stillschweigend Entities und Automatisierungen |

Quellen:

- <https://hacs.xyz/docs/publish/start> — „If the repository uses GitHub releases, the tag name from the latest release is used to set the remote version. Just publishing tags is not enough, you need to publish releases."
- <https://hacs.xyz/docs/use/entities/switch> — HACS 2.0 Pre-Release-Mechanik (GitHub pre-release-Flag → `switch.<repo>_pre_release`, default OFF); Beispiel-Tags `v1.0.0`, `v2.0.0b0`
- <https://developers.home-assistant.io/docs/versioning> — HA nutzt PEP-440-Suffixe (`b<N>` für Betas); Versionsvergleich via AwesomeVersion, kein String-Parsing
- <https://semver.org/#is-v123-a-semantic-version> — FAQ: `v1.2.3` ist keine Semantic Version (der `v`-Prefix ist reine Tag-Konvention)
- <https://github.com/hacs/integration/releases> — Vorbild für die Release-Notes-Struktur (What's Changed / ✨ New features / 💥 Breaking changes / Full Changelog)

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

### Migrations-Rezept: `entry.data` → `entry.options`

Konkretisiert die eiserne Regel „`manifest.VERSION` nur mit registriertem
`async_migrate_entry`-Handler erhöhen" (Tabelle Releases oben) für den häufigsten Fall:
strukturelle Daten bleiben in `entry.data`, editierbare Daten wandern verlustfrei nach
`entry.options`. Worked example: `Popoboxxo/ha-health-o-mat`, `config_flow.py`.

| Version | `entry.data` | `entry.options` |
|---|---|---|
| v1 | alles (inkl. editierbarer Werte) | leer |
| v2 | nur strukturelle Daten (z.B. Host, Domain-Identität) | editierbare Werte (z.B. Schwellwerte, Intervalle) |

```python
# custom_components/<domain>/__init__.py
STRUCTURAL_KEYS = {"host"}  # Beispiel: an das eigene Schema anpassen

async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate an old entry.data layout to the current version."""
    if entry.version == 1:
        new_data = {k: v for k, v in entry.data.items() if k in STRUCTURAL_KEYS}
        new_options = {
            **entry.options,
            **{k: v for k, v in entry.data.items() if k not in STRUCTURAL_KEYS},
        }
        hass.config_entries.async_update_entry(
            entry, data=new_data, options=new_options, version=2
        )
    return True
```

### `custom_components/<domain>/strings.json` (Master) + `translations/{de,en}.json`

Master `strings.json` ist **englisch** (hassfest-Konvention) — der Master trägt die
Identität, allein `translations/*.json` tragen die lokalisierten Anzeigewerte:

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Set up connection",
        "data": { "host": "Host or IP address" }
      }
    },
    "error": { "cannot_connect": "Connection failed" }
  },
  "options": {
    "step": {
      "init": { "data": { "scan_interval": "Update interval (seconds)" } }
    }
  },
  "entity": {
    "sensor": {
      "power": { "name": "Power" }
    }
  }
}
```

Abgeleitet `translations/de.json` (nur Anzeige-Werte; die Identität bleibt im Master).
Der `entity`-Key muss exakt zum `_attr_translation_key` der Entity passen:

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Verbindung einrichten",
        "data": { "host": "Host oder IP-Adresse" }
      }
    },
    "error": { "cannot_connect": "Verbindung fehlgeschlagen" }
  },
  "entity": {
    "sensor": { "power": { "name": "Leistung" } }
  }
}
```

Master ist `strings.json` (englisch); `translations/de.json` und `translations/en.json`
sind abgeleitet und bei jeder Änderung mitzupflegen (hassfest prüft die Konsistenz).
`entity.<platform>.<translation_key>.name` trägt den lokalisierten Anzeigenamen
(z.B. `entity.sensor.power.name` für `_attr_translation_key = "power"`); die
`entity_id` bleibt davon unberührt.

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
