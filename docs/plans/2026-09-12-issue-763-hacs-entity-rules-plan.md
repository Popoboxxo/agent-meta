# Plan — Issue #763: HACS-Preset — englische Entity-Namen via `translation_key` + Entity-Registry-Migration bei Rename

## STATUS

- **Datum:** 2026-09-12
- **Branch:** `docs/issue-763-hacs-entity-rules-plan` (base `main` @ `e2b15aa3`)
- **Mode:** Plan-only — dieser Branch enthält ausschließlich dieses Dokument.
  Keine Code-/Agent-/Rule-/Test-Änderung; Implementierung ist explizit out of scope.
- **Quelle:** GitHub Issue #763 (`improvement`, P2) — „HACS preset — enforce English entity names
  via translation_key and entity-registry migration on rename".
- **Methode:** direkte Datei-Reads auf Verifikations-Basis. `ripgrep`/`grep` ist in dieser
  Umgebung defekt (`ripgrep execution failed`), `glob` ebenfalls ripgrep-gestützt — jede
  Aussage unten stammt daher aus `read`-Aufrufen, nicht aus Suchläufen.
- **Effort:** Referenz auf `effort-estimator` (Text-Referenz, keine Tool-Delegation) —
  reine Doku-/Test-Artefakte ohne Runtime-Logik; Schätzung nach `effort-estimator`
  (Task-Typ „docs/rule change + 1 scenario") liegt typisch im Bereich **XS–S pro Datei**,
  Summe unten als Größe M.

> **Tooling-Hinweis / nicht verifizierbar:** Dieser Plan konnte `async_migrate_entries`,
> das `strings.json`-`entity`-Schema und den tatsächlichen Skill-Channel-Output eines
> Szenarios **nicht ausführen** (kein HA-Install, kein Sync-Lauf, `grep` defekt).
> Die Draft-Snippets in Abschnitt 2 sind gegen die HA-API dokumentiertes Wissen und
> müssen bei der Implementierung gegen die Ziel-HA-Minimalversion validiert werden
> (siehe Offene Fragen 4/5).

---

## 1. Triage

### Verdikt

**partially-valid.** Die Issue-Diagnose ist nicht falsch, aber gegen einen **älteren
Stand** formuliert: Die Sektion „Sprache, Namen & Identität" (`rules/2-platform/hacs-integration-development.md:94–150`)
wurde erst durch PR #742 (Commit `56da703e`, 2026-09-11) ergänzt — einen Tag **vor**
Filing des Issues. Die Behauptung „`translation_key` kommt 0× vor" ist damit **FALSE /
stale**. Reale Restlücken bleiben bei L2 (vollständig) und L3/L4 (Residuen).

### Verifizierte Evidenz-Tabelle

| Issue-Behauptung / Lücke | Verifikation (direkter Read) | Verdikt |
|---|---|---|
| `translation_key` 0× | **PRÄSENT:** `rules/2-platform/hacs-integration-development.md:67` (Regel), `:128` („`has_entity_name = True` + `_attr_translation_key`") | FALSE / stale |
| `_attr_has_entity_name` (exakter Token) | **0×**; nur `has_entity_name` an `:67`, `:128`. `_attr_`-Präfix fehlt; ein explizites Verbot von hartcodiertem `_attr_name` fehlt | **L1-Residuum valide** |
| `async_migrate_entries` 0× | **0× in den betroffenen Dateien.** Nur Singular `async_migrate_entry` an Rule `:59`, `:216`, `:229` und `agents/2-platform/hacs-release.md:16` | **L2 valide (Haupt-Lücke)** |
| `original_name` 0× | **0×**, `new_entity_id` ebenfalls absent | **L2 valide** |
| L3 (Rename = Breaking) | Teilweise: Rule `:139` „spätere Umbenennung ist ein Breaking Change"; `hacs-release.md:23` „`unique_id`-/Entity-Änderungen sind IMMER breaking → MAJOR". **Fehlt:** explizite 💥-Breaking-Entry-Pflicht + Bindung an Post-Release-Orphan-Cleanup (Rule `:45–49`) | **L3-Residuum valide** |
| L4 (`strings.json` = English Master) | Prinzip an Rule `:132` vorhanden („`strings.json` ist der englische Master; `translations/{de,en}.json` sind abgeleitet"). **ABER:** Das Skelett im Meta-Dateien-Abschnitt `:245–270` ist **deutsch** („Verbindung einrichten", „Host oder IP-Adresse", „Verbindung fehlgeschlagen", „Aktualisierungsintervall (Sekunden)") und widerspricht damit der eigenen Regel | **L4-Residuum valide** |
| „4 Terme 0×" als Sammel-Claim | Mind. `translation_key` ist präsent → Claim pauschal falsch | FALSE / stale |
| Zitierte Zeile `:107–108` (Breaking/SemVer) | **STALE:** `:107–108` ist heute ein Python-Docstring im `suggested_object_id`-Block; Breaking/SemVer-Inhalt liegt jetzt `:160–167` + `hacs-release.md:23` | Zitierfehler |
| Zitierte Zeilen `:65–66`, `:59`, reviewer `:19`/`:26`, `rules/1-generic/language.md:3–9` | OK (alle direkt bestätigt) | OK |

### Severity

**P2 bestätigt** (Issue-Label). Kein Sicherheits-/Datenverlust-Vektor: die Lücke
erzeugt potenziell instabile `entity_id`s und verwaiste Entities bei Sprachwechsel/
Rename — schädlich, aber nicht akut, und der wichtigste Teil (Object-ID-Pinning +
`translation_key`) ist bereits seit PR #742 abgedeckt.

### Größe

**M (S–M, aufgerundet).** Begründung: 1 Regeldatei mit 4 inhaltlichen Deltas
(einige davon mit Referenz-Code/JSON-Skelett), 2 Plattform-Agenten (Gate + Release-Regel,
inkl. Versions-/`based-on`-Pflicht), 3 Test-Artefakte (Config, Assert, Registry-Zeile)
sowie dieses Plandokument. Kein Runtime-Code, kein Sync-Logik-Eingriff → Risiko niedrig,
aber mehrere Artefaktklassen mit Composition-/Versionsdisziplin.

---

## 2. Zielbild — die 4 Regeln

Alle vier Regeln landen in **`rules/2-platform/hacs-integration-development.md`**
(keine Frontmatter-Version, da Rule-Body; Auslieferung via `config/rules-presets.yaml`
→ Eintrag `integration-development` mit `channel: skill`, Build-Time-Präfix-Strip
`hacs-` in `scripts/lib/rules.py`).

| # | Anker in `rules/2-platform/hacs-integration-development.md` | Delta |
|---|---|---|
| **R1** | § „Sprache, Namen & Identität" `:94–150`, direkt nach der Sentence `:128–130` | Expliziter `_attr_has_entity_name = True` + `_attr_translation_key`-Referenz-Code; hartes Verbot von hartcodiertem, nicht-lokalisierbarem `_attr_name` |
| **R2** | Neue Subsections nach `:150`, vor `## Release-Naming-Best-Practice` (`:152`) | `### Entity-Registry-Migration bei Umbenennung` mit `async_migrate_entries` + `async_migrate_entry`/VERSION-Bump, stabile `unique_id` → `new_entity_id`/`original_name` |
| **R3** | „Erstregistrierungs-Regel" `:136–139` erweitern + Workflow-Schritt-7-Bezug `:45–49` | Rename (entity_id/original_name/translation_key) explizit als Breaking + 💥-Entry-Pflicht + Post-Release-Orphan-Cleanup-Verweis |
| **R4** | § „Meta-Dateien-Skelett" → Subsection `strings.json` `:243–273` | Skelett von deutschem Master auf **English-Master** umstellen + abgeleitetes `translations/de.json` + `entity`-Block |

### R1 — Namens-/Lokalisierungs-Contract (Draft)

Anknüpfung an die vorhandene `suggested_object_id`-Referenz (`:99–130`). Ergänzung nach
`:130`:

```python
# custom_components/<domain>/sensor.py
class HealthOMatPowerSensor(HealthOMatEntity):
    # Anzeigename folgt der Systemsprache, object_id/entity_id bleibt englisch
    # gepinnt (siehe suggested_object_id-Referenz oben).
    _attr_has_entity_name = True
    _attr_translation_key = "power"

    # VERBOTEN (nicht lokalisierbar, bricht den Sprachwechsel):
    # _attr_name = "Leistung"
    # name = "Leistung"  # Property-Override mit Literal
```

Verbots-Regel (explizit, mit Begründung/Fehlerklasse):

| Regel | Begründung | Fehlerklasse |
|---|---|---|
| `_attr_has_entity_name = True` + `_attr_translation_key` statt hartcodiertem `_attr_name`/`name`-Literal | Nur dann zieht HA den Anzeigenamen aus `strings.json`/`translations` und respektiert die Systemsprache; ein Literal friert eine Sprache ein | `friendly_name` wechselt nicht mit der Sprache; identische Schadensklasse wie das Object-ID-Pinning (`unique_id` ≠ object_id) |

> **Scope-Hinweis:** Das Verbot gilt für Entities, die lokalisierbar sein sollen
> (`has_entity_name = True`). Device-Level-Entities mit `has_entity_name = False`
> dürfen legitimerweise einen Literal-Namen tragen — siehe Offene Frage 1.

### R2 — Entity-Registry-Migration bei Rename (Draft)

Neue Subsection, klar getrennt vom vorhandenen `entry.data → entry.options`-Rezept
(`:213–241`), das den **Handler für Entry-Daten** zeigt:

````markdown
### Entity-Registry-Migration bei Umbenennung

Renames ändern NIE die `unique_id` (eiserne Regel Entities). Umbenannt werden nur
`entity_id` und `original_name` — über den HA-Entity-Registry-Helper, innerhalb des
registrierten `async_migrate_entry`-Handlers, zusammen mit einem `manifest.VERSION`-Bump
(Breaking → MAJOR, siehe Release-Naming).

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

`manifest.json`: `"version": "2.0.0"` (Breaking), GitHub-Release mit 💥-Entry.
````

### R3 — Rename als Breaking + Orphan-Cleanup (Draft)

Erweiterung von `:139` und Querverweis auf Workflow-Schritt 7 (`:45–49`):

> **Rename = Breaking Change:** Jede Änderung, die eine `entity_id`-Erzeugung
> verschiebt (`entity_id`, `original_name`, `translation_key`, Object-ID-Pinning),
> ist ein Breaking Change → **MAJOR** + 💥-Eintrag mit Migrationshinweis
> (siehe `hacs-release`). Verwaiste Alt-Entities werden im **Post-Release-Cleanup**
> (Workflow-Schritt 7) entfernt — nicht vor dem Release, und niemals durch
> Ändern der `unique_id`.

### R4 — `strings.json` als English-Master (Draft)

Ersetzt das deutsche Skelett `:245–270`. Master `strings.json` **englisch**, inkl.
Entity-Translations für den `translation_key` aus R1:

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

Abgeleitet `translations/de.json` (nur Anzeige-Werte, Identität bleibt im Master):

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

Der Prosa-Satz `:272–273` („Master ist `strings.json` …") bleibt; ergänzt wird die
explizite Aussage, dass der **Master englisch** ist und `entity.<platform>.<translation_key>.name`
den Anzeigenamen trägt.

---

## 3. Change-Liste pro Datei (in/out of scope)

### In scope

| Datei | Änderung | Version | `based-on` |
|---|---|---|---|
| `rules/2-platform/hacs-integration-development.md` | R1–R4 (Abschnitt 2). Keine Frontmatter vorhanden → kein Versionsfeld | n/a | n/a |
| `agents/2-platform/hacs-code-reviewer.md` | Gate 11 ergänzen (Abschnitt 4); bestehenden `append-after`-Patch auf `<persona>` um Gate-Row + Fail-Predicate erweitern | **1.0.0 → 2.0.0** (neuer harter Pflicht-Gate = Verhaltensänderung/Major per `conventions`) | `code-reviewer.md@1.2.2` → **`@1.7.0`** (aktueller Basis-Stand; siehe Offene Frage 3) |
| `agents/2-platform/hacs-release.md` | SemVer-Bullet `:23` + Release-Notes-Bullet `:24` um expliziten Rename-Breaking-Trigger + 💥-Pflicht ergänzen (Abschnitt 5) | **1.0.1 → 1.1.0** (Scope-Erweiterung/MINOR) | `release.md@1.5.0` → **`@1.11.0`** |
| `tests/scenarios/configs/49-hacs-entity-naming.project.yaml` | Neues Szenario | n/a | n/a |
| `tests/scenarios/asserts/49-hacs-entity-naming.sh` | Content-Assertions | n/a | n/a |
| `tests/scenarios/registry.md` | Katalog-Zeile `49-hacs-entity-naming` | n/a | n/a |

**Composition-Folgen:** Alle HACS-Agenten nutzen Composition (`extends` + `patches`,
`append-after`, Anker `<persona>`). Die Änderungen werden **additiv in die bestehenden
`<persona>`-Patch-Blöcke** geschrieben — **kein neuer Anker** und kein `replace`, damit
kein Instruction-Bleed-Risiko (`.opencode/skills/conventions/SKILL.md:27–38`).
`frontmatter.version-bump` (`scripts/lib/consistency/frontmatter.py:49–56`) erzwingt
den Versions-Bump bei geänderten 2-platform-Agenten. `based-on` wird vom Consistency-Check
nur auf **Präsenz** geprüft (`:91–98`), nicht auf Aktualität — die Korrektur ist
Konventionspflicht, kein CI-Gate.

### Optional / nicht erforderlich

| Datei | Bewertung |
|---|---|
| `agents/2-platform/hacs-developer.md` | Die Entities-Zeile `:90` nennt `suggested_object_id`-Pinning. Ein always-on-Anker für `_attr_has_entity_name`/`_attr_translation_key` wäre konsistent, ist für die 4 Regeln aber **nicht erforderlich**. Nur aufnehmen, wenn Offene Frage 6 = ja. Sonst out of scope. |

### Out of scope

- `scripts/**`, `sync.py`, `rules.py`, `config/rules-presets.yaml` — `integration-development`
  ist bereits als `channel: skill` gemappt (`config/rules-presets.yaml:157–161`), kein
  Sync-Eingriff nötig.
- `agents/1-generic/**` — rein HACS-spezifische Thematik.
- Pre-existing `based-on`-Drift (`hacs-developer.md` 4.0.2 vs. Generic 4.5.0; siehe Offene Frage 3).
- Jegliche Implementierung (Abschnitt „STATUS").

---

## 4. Reviewer-Gate-Design

**Ziel:** `agents/2-platform/hacs-code-reviewer.md` — die Gate-Tabelle (`:13–26`) wird
um **Gate 11** erweitert; Gate 3 (`Entity-Identität`) bleibt unverändert und wird nur
per Cross-Reference ergänzt.

**Neue Zeile:**

```
| 11 | **Entity-Namenslokalisierung & Rename-Migration** | Jede Entity: `_attr_has_entity_name = True` + `_attr_translation_key` (Key existiert in `strings.json` → `entity.<platform>.<key>.name`); kein hartcodiertes `_attr_name`/`name`-Literal; bei Rename bleibt `unique_id` stabil, Rename via `async_migrate_entries` (`new_entity_id`/`original_name`) + `manifest.VERSION`-Bump |
```

**Exakte Fail-Bedingung** (harter Fail → Reviewer-Verdikt `CHANGES_REQUESTED`),
formuliert als prüfbare Prädikate, damit der Gate nicht nur Prosa ist:

- **F1** — In `custom_components/<domain>/**/*.py` setzt eine Entity-Klasse ein
  Literal `_attr_name = "..."` (oder ein `name`-Property-Literal), **ohne**
  `_attr_has_entity_name = True` **und** `_attr_translation_key`.
- **F2** — Ein im Code verwendeter `_attr_translation_key`/`translation_key` hat
  keinen korrespondierenden Key unter `entity.<platform>.<key>.name` in `strings.json`.
- **F3** — `strings.json` (Master) enthält nicht-englische Strings (Master MUSS englisch
  sein; Übersetzungen nur in `translations/*.json`).
- **F4** — Ein Rename ändert `unique_id`/`new_unique_id` statt `async_migrate_entries(...)`
  mit `new_entity_id`/`original_name` und `manifest.VERSION`-Bump.
- **F5** — `manifest.VERSION` wurde gebumpt (Rename = Breaking), aber kein
  `async_migrate_entry`-Handler vorhanden (verstärkt Gate 10, `hacs-release.md:16`).

**Bleed-/Redundanz-Hinweis:** Gate 11 referenziert die Regel R1/R2/R4, dupliziert sie
aber nicht wörtlich (konventionskonform: Gate = Prüfaussage, Skill = Referenz).

---

## 5. Release-Regel-Anpassung

`agents/2-platform/hacs-release.md`, bestehender `<persona>`-Patch, Bullet `:23`
(SemVer) und `:24` (Release-Notes):

- **`:23` erweitern:** „MAJOR = Breaking. **Entity-Rename (`entity_id`, `original_name`,
  `translation_key`), Object-ID-/Pinning-Änderungen und `unique_id`-Änderungen sind IMMER
  breaking → MAJOR**; MINOR = Feature, PATCH = Fix."
- **`:24` erweitern:** „💥 Breaking changes — **bei MAJOR Pflicht** — je mit
  Migration-Hinweis (Verweis auf `async_migrate_entries`-Rezept) **und** Verweis auf den
  Post-Release-Orphan-Cleanup (Workflow-Schritt 7 der Integration-Development-Regel)."
- Damit ist R3 auch im Release-Agenten sichtbar (always-on `<persona>`-Patch), nicht nur
  im lazy-geladenen Skill.
- Version `1.0.1 → 1.1.0`.

---

## 6. Test-Strategie

**Szenario-ID:** `49-hacs-entity-naming` (nächste freie ID nach `48-progress-provider-neutral-path`).

Gemäß `tests/scenarios/registry.md:14–25` (Feature + Szenario im **selben** PR, konkrete
Assertions, Katalog-Entry, `run.sh` vor Commit) und `conventions`-Change-Checklist
(`.opencode/skills/conventions/SKILL.md:74`).

**Config:** `tests/scenarios/configs/49-hacs-entity-naming.project.yaml`

```yaml
agent-meta-version: 0.101.0
ai-providers:
- Claude
platforms:
- hacs
roles:
- orchestrator
- developer
- code-reviewer
- release
- git
project:
  name: scenario-hacs-entity-naming
  prefix: s49
  short: hacs-entity-naming
variables:
  PROJECT_NAME: scenario-hacs-entity-naming
  PROJECT_DESCRIPTION: HACS entity naming + rename-migration rule test.
  PROJECT_GOAL: Verify entity-naming contract, rename migration and reviewer gate render.
  GIT_PLATFORM: GitHub
  GIT_REMOTE_URL: https://github.com/example/scenario-hacs-entity-naming
  GIT_MAIN_BRANCH: main
rules-preset: lazy      # aktiviert channel:skill für integration-development
speech-mode: full
tier-preset: Normal
se-focus: false
max-parallel-agents: 2
conventions-preset: default
debug-mode: false
allow-committed-secrets: false
```

> **Wichtig:** `rules-preset: lazy` ist nötig, weil der `channel: skill`-Eintrag für
> `integration-development` **nur** im `lazy`-Preset steht (`config/rules-presets.yaml:157–161`).
> Bei `default` würde die Regel nicht als `.claude/skills/integration-development/SKILL.md`
> gerendert. Output-Pfad bestätigt: `PROVIDERS = {"Claude"}` + `<skills_dir>/<rule-stem>/SKILL.md`
> (`scripts/lib/skill_channel.py:35,96`).

**Assert:** `tests/scenarios/asserts/49-hacs-entity-naming.sh` (ausführbar). Prüft gegen
den Sync-Output (`cwd` = Temp-Dir):

1. `.claude/skills/integration-development/SKILL.md` existiert.
2. Skill-Body enthält die exakten Token: `_attr_has_entity_name`, `_attr_translation_key`,
   `async_migrate_entries`, `new_entity_id`, `original_name`.
3. Master-Skelett ist englisch: enthält `"Set up connection"`; enthält **nicht** mehr
   `Verbindung einrichten` (Negativ-Assertion gegen den alten deutschen Master).
4. `.claude/agents/code-reviewer.md` enthält den Gate-11-Marker
   (`Namenslokalisierung` o. ä. stabiler String).
5. `.claude/agents/release.md` enthält `Umbenennung` und `💥`.

**Registry-Zeile:** in `tests/scenarios/registry.md` Katalog-Tabelle ergänzen:
`| `49-hacs-entity-naming` | Claude | strict (default) | HACS entity-naming: `_attr_has_entity_name`+`_attr_translation_key`, English-master `strings.json`, `async_migrate_entries`-Rename, reviewer Gate 11 |`

**Lokale DoD:** `tests/scenarios/run.sh 49` → `PASS`; zusätzlich `python3 scripts/sync.py --validate`.
Hinweis: Der Assert nutzt `grep` (im Szenario-Harness/CI verfügbar; in der
Plan-Umgebung defekt — daher hier nicht ausgeführt).

---

## 7. Acceptance-Criteria-Mapping, Abhängigkeiten, Risiken, offene Fragen

### Acceptance-Mapping (Issue-Claim → Work Item)

| Issue-Claim | Verifizierter Status | Work Item |
|---|---|---|
| `translation_key` 0× / 4 Terme 0× | FALSE / stale (präsent `:67`,`:128`) | Triage-Notiz; keine Regeländerung nötig |
| L1 `_attr_has_entity_name`-Token + `_attr_name`-Verbot | valides Residuum | R1 |
| L2 `async_migrate_entries`-Rename | valid (Haupt-Lücke) | R2 |
| L3 Rename = Breaking + 💥 + Cleanup | teilweise | R3 + Abschnitt 5 |
| L4 `strings.json` English-Master | teilweise (Skelett widerspricht Regel) | R4 |
| Reviewer-Enforcement | fehlt | Gate 11 (Abschnitt 4) |
| Testabdeckung | fehlt | Szenario 49 (Abschnitt 6) |
| Zitierte Zeile `:107–108` | stale | Triage-Notiz |

### Abhängigkeiten

1. **R4 ← R1:** der `entity.sensor.power.name`-Key im Master muss exakt zum
   `_attr_translation_key = "power"` im R1-Beispiel passen (Cross-Consistency).
2. **Gate 11 (Abschnitt 4) ← R1/R2/R4:** Gate-Text darf erst formuliert werden, wenn die
   Referenz-Token stabil sind.
3. **Szenario 49 ← alle Regel-/Agent-Änderungen:** Assert prüft gerenderten Output.
4. **Versions-Bumps Pflicht:** `frontmatter.version-bump` blockt geänderte
   2-platform-Agenten ohne Bump (`scripts/lib/consistency/frontmatter.py:49–56`).
5. **Sync-Konsumenten:** `rules/`-Änderung → Consumer müssen `sync.py` erneut laufen
   lassen (conventions-Checkliste).

### Risiken

| Risiko | Eintritt | Mitigation |
|---|---|---|
| Instruction Bleed durch neuen Patch | niedrig | Nur additive Erweiterung **bestehender** `<persona>`-Patches, kein neuer Anker/kein `replace` |
| Über-breites `_attr_name`-Verbot | mittel | Scope auf lokalisierbare Entities begrenzen (Offene Frage 1) |
| Falsche HA-API-Annahme (`async_migrate_entries` / `new_entity_id`) | mittel | Bei Implementierung gegen Ziel-HA-Version validieren (Offene Frage 4) |
| Szenario rendert Skill nicht (Preset/Provider) | niedrig–mittel | `rules-preset: lazy` + Claude im Szenario; im Assert zuerst Datei-Existenz prüfen |
| Doppelte Regelprosa (Gate vs. Skill) driften auseinander | niedrig | Gate nur als Prüfaussage, Skill als Referenz (kein Wort-Duplikat) |
| `based-on`-Drift bleibt unbemerkt | niedrig | In Change-Liste adressiert bzw. als eigenes Chore (Offene Frage 3) |

### Offene Fragen

1. **Scope des `_attr_name`-Verbots:** absolut, oder nur für Entities mit
   `has_entity_name=True`? Device-Level-Entities (`has_entity_name=False`) dürfen
   legitimerweise Literale tragen — der Draft schlägt die eingeschränkte Variante vor.
2. **Versions-Magnitude `hacs-code-reviewer`:** 2.0.0 (neuer harter Gate = Major per
   `conventions`) vs. 1.1.0 (additiv/MINOR)? Der Plan schlägt 2.0.0 vor.
3. **`based-on`-Refresh:** im selben PR oder separates `chore:`? Pre-existing Drift:
   `hacs-developer` 4.0.2 vs. Generic 4.5.0, `hacs-code-reviewer` 1.2.2 vs. 1.7.0,
   `hacs-release` 1.5.0 vs. 1.11.0 (nur Präsenz wird geprüft, keine Aktualität).
4. **HA-API-Verifikation:** Bestätigt die Ziel-HA-Minimalversion `er.async_migrate_entries`
   mit `new_entity_id`/`original_name` im Callback-Return? Nicht in dieser Umgebung prüfbar.
5. **`strings.json`-`entity`-Schema:** Entspricht `entity.<platform>.<translation_key>.name`
   dem hassfest-Stand? Nicht in dieser Umgebung prüfbar.
6. **`hacs-developer.md`-Anker:** Soll die always-on-Entities-Zeile `:90` um
   `_attr_has_entity_name`/`_attr_translation_key` ergänzt werden (Konsistenz) oder bleibt
   es beim lazy Skill + Reviewer-Gate?

### Branch-/PR-Cut

- **Dieser Branch** `docs/issue-763-hacs-entity-rules-plan` (base `main @ e2b15aa3`
  bereits ausgecheckt): enthält ausschließlich dieses Plandokument. Kein Commit/Push
  durch diesen Task.
- **Implementierungs-Follow-up:** neuer Feature-Branch off `main`, z. B.
  `feat/763-hacs-entity-naming`, mit R1–R4 + Gate 11 + Release-Regel + Szenario 49.
  Branch-Guard verbietet direkte `main`-Commits; PR gegen `main`, Conventional Commits
  (Englisch), DoD `rapid-prototyping`.
- **Empfohlene Reihenfolge:** R1/R2/R4 → Gate 11 + Release-Regel → Szenario 49
  (im selben PR, `registry.md:16–19`) → `tests/scenarios/run.sh 49` + `sync.py --validate`.
- **Nicht Teil dieses Plans:** Pre-existing `based-on`-Drift (ggf. eigenes Issue),
  `hacs-developer`-Anker (Offene Frage 6).

---

## Nicht verifiziert / Transparenz

- Kein `grep`/`glob` (beide defekt) — alle Befunde aus `read`; keine Volltext-Suche über
  das gesamte Repo, daher kann eine parallele zweite Erwähnung eines Tokens außerhalb
  der gelesenen Dateien nicht 100 % ausgeschlossen werden. Gelesen wurden die
  maßgeblichen Dateien vollständig.
- Issue-Body-L1–L4-Wortlaut nicht direkt gelesen (kein Issue-File in `docs/issues/`;
  Task-Kontext als verifizierte Baseline übernommen).
- `async_migrate_entries`-Callback-Contract, `strings.json`-`entity`-Schema und der
  tatsächliche Skill-Channel-Output eines HACS-Szenarios wurden **nicht ausgeführt** —
  siehe Offene Fragen 4/5 und Risiken.
