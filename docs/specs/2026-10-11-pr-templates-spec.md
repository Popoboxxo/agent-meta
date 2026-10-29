---
spec-id: SPEC-PR-TEMPLATES-2026-10-11
title: PR-Templates (generic / platform / project, mit Variablen) — Feature-Spezifikation
status: DRAFT
related-spec: SPEC-CONTEXT-FILE-MODES-2026-09-13
related-issue: "#957"
---

# PR-Templates für agent-meta — Spec

> Status: **DRAFT (2026-10-11)** — Entwurf zur Freigabe. Der Approval-Marker (`Status: APPROVED`)
> wird ausschließlich nach Review durch den Nutzer bzw. `concept-reviewer` gesetzt, nie vom
> Autor. Diese Datei ist eine Spezifikation: sie definiert Interface-Contracts und
> Akzeptanzkriterien, enthält keine Implementierung und keinen Plan.
> Trace-Anker: `spec-id: SPEC-PR-TEMPLATES-2026-10-11`.
>
> Provider-/Host-agnostisch ist Pflicht: Unterschiede (GitHub, GitLab, …) werden über
> Config-Keys ausgedrückt (`config/pr-template-hosts.yaml`), nie über
> `if host == "GitHub"` im Code (vgl. Skill `provider-agnostic`).

## 1. Problem / Ziel / Nicht-Ziele

### 1.1 Problem

- Agent-generierte Pull Requests haben keine einheitliche Struktur. Jeder Lauf des `git`-/`release`-Agenten
  formuliert den PR-Body frei (`gh pr create --title … --body …`, `agents/1-generic/git.md`).
  Reviewer bekommen mal Test-Plan, mal nicht; DoD-Gates (`dod-presets`), REQ-Traceability und
  Issue-Verknüpfung (`Closes #n`) hängen von der Tagesform des Agenten ab.
- Projekte, die ein PR-Template brauchen, pflegen es von Hand in `.github/` — ohne Anbindung an
  `project.yaml`, DoD-Preset, Plattform-Preset oder Sprache. Neue Projekte starten ohne Template.
- Gute Projekt-Templates bleiben im Projekt hängen. Es gibt keinen definierten Weg, ein Template
  als Vorschlag ins Framework zurückzugeben (analog zu `new-agent` / `new-platform-agent`).

### 1.2 Ziel

1. agent-meta liefert **PR-Templates in drei Schichten**, die denselben Vorrang haben wie Agenten und Rules:
   `1-generic` < `2-platform` < **Projekt-Override** (Projekt gewinnt).
2. Templates sind **parametrisierbar**: `{{VARIABLE}}`, `{{platform.<p>.<key>}}` und
   `{{#if FLAG}}…{{/if}}` werden zur Sync-Zeit aufgelöst (bestehende Substitution, kein neuer Dialekt).
3. `sync.py` schreibt das **wirksame** Template in den host-nativen Pfad (GitHub:
   `.github/pull_request_template.md` und `.github/PULL_REQUEST_TEMPLATE/<name>.md`), sodass Web-UI,
   `gh pr create` und Agenten dasselbe Template sehen.
4. Der **`agent-meta-manager`** kann Projekt-Templates als **globale (generic) oder Plattform-Vorschläge**
   zurückmelden und den Abstand zwischen Projekt-Override und Framework-Template anzeigen.
5. Default **aus**: ohne `pr-templates:`-Block ist die Ausgabe byte-identisch zum Ist-Zustand.

### 1.3 Nicht-Ziele

- Keine automatische PR-Erstellung, kein Review-Bot, keine GitHub-Actions-Generierung.
- Keine Issue-Templates in dieser Spec (gleiche Schichtung, eigener Folge-Request, siehe §9 Phase 3).
- Kein eigener Template-Dialekt: es gibt keine Schleifen/Includes jenseits der bestehenden
  `{{VAR}}` / `{{#if}}`-Substitution.
- Kein Überschreiben nutzereigener Dateien (siehe IC-06).

## 2. Ist-Zustand (verifiziert am Repo-Stand `main`)

| Baustein | Fundort | Relevanz |
|---|---|---|
| 3-Ebenen-Vorrang Agents/Rules | `docs/architecture/01-layer-model.md`, `agents/1-generic` → `agents/2-platform` → Extension | Vorbild für die Schichtung |
| Plattform-Variablen | `platform-configs/<platform>.defaults.yaml`, Override `.claude/platform-config.yaml`, Substitution `{{platform.<p>.<key>}}` | Quelle der Plattform-Variablen |
| Substitution + Conditionals | `scripts/lib/config.py::substitute`, `strip_inactive_conditional_blocks`, `build_variables` | wird wiederverwendet |
| Scaffold-Analogon | `scripts/lib/release_scaffold.py` (`templates/docs/RELEASE_PROCESS.<distribution>.md` → `docs/RELEASE_PROCESS.md`, Managed-Block) | nächstes Implementierungsvorbild |
| Preset-Muster | `config/rules-presets.yaml`, `config/dod-presets.yaml`, `config/conventions-presets.yaml` | Config-Vorbild (Default-Verhalten, Overrides) |
| Generierte-Dateien-Drift | `scripts/lib/generated_file_drift.py`, `.meta-config/generated-file-hashes.json` | Grundlage für Besitz/Divergenz-Erkennung |
| Rückmeldeweg ins Framework | `agents/1-generic/meta-feedback.md` (Labels `new-agent`, `new-platform-agent`, …), Manager §7 | Vorbild für Template-Vorschläge |
| PR-Erstellung heute | `agents/1-generic/git.md` (`gh pr create --title … --body …`) | Konsument des Templates |
| Git-Host-Variablen | `GIT_PLATFORM`, `GIT_REMOTE_URL`, `GIT_MAIN_BRANCH` | Host-Auswahl |

Nicht vorhanden: jegliche Referenz auf `pull_request_template` im Framework (Suche über Code, Config und Templates).

## 3. Konzept

### 3.1 Schichten und Auflösung

```
pr-templates/1-generic/<name>.md                 # Framework, für alle Projekte
pr-templates/2-platform/<platform>-<name>.md     # Framework, nur für aktive Plattform(en)
<projekt>/.meta-config/pr-templates/<name>.md    # Projekt-Override, vom Projekt besessen
```

Auflösung je Name `N`: **Projekt** > **Plattform** (wenn eine Plattform in `platforms:` aktiv ist und
`<platform>-N.md` existiert; bei mehreren aktiven Plattformen gewinnt die Reihenfolge in `platforms:`) >
**Generic**. Ein Name ohne Datei in irgendeiner Schicht ist ein Konfigurationsfehler (IC-02).

Mitgelieferte Generic-Namen (MVP): `default` (Standard-PR), `bugfix`, `release`, `docs`.

### 3.2 Variablen

Auflösung zur Sync-Zeit mit der bestehenden Substitution. Verfügbar (alle bereits in `build_variables`,
neu markiert):

| Variable | Quelle |
|---|---|
| `{{PROJECT_NAME}}`, `{{GIT_MAIN_BRANCH}}`, `{{CODE_LANGUAGE}}`, `{{DOCS_LANGUAGE}}` | vorhanden |
| `{{platform.<p>.<key>}}` | vorhanden (Platform-Config, Projekt-Override gewinnt) |
| `{{DOD_*}}`-Flags (`DOD_REQ_TRACEABILITY`, `DOD_TESTS_REQUIRED`, …) für `{{#if}}` | vorhanden |
| `{{PR_TEMPLATE_NAME}}` | **neu**: Name des gerade gerenderten Templates |
| `{{DOD_CHECKLIST_BLOCK}}` | **neu**: Checkbox-Liste der aktiven DoD-Gates aus dem `dod-preset` |
| `{{PR_VARS.<key>}}` | **neu**: projektlokale Werte aus `pr-templates.variables` |

Zwei Phasen, strikt getrennt:

- **Sync-Zeit** (`{{…}}`): wird beim Sync ersetzt. Ein nicht auflösbarer Platzhalter bleibt stehen und
  erzeugt eine Warnung (bestehendes Verhalten); `--validate` meldet ihn als Fehler für PR-Templates (AC-11).
- **PR-Zeit** (`<!-- fill: … -->`): Hinweis-Kommentare für den PR-Autor bzw. den `git`-Agenten, bleiben
  unverändert im Template und werden beim Erstellen des PR ausgefüllt.

> **Superseded (2026-10-27, M7, `63b12bde`).** "A non-resolvable placeholder stays and warns" is the grace behaviour up to `2.1.0` only; from `2.1.0` the sync aborts with `SyncError` (`variables._placeholder_keep`). Only tokens that survive the conditional strip are evaluated — a token in an inactive `{{#if}}`/`{{#unless}}` branch neither warns nor aborts. The same applies to the `{{PR_VARS.<key>}}` sentence in IC-04: a missing key warns during the grace window and aborts afterwards.

### 3.3 Konfiguration (`project.yaml`)

```yaml
pr-templates:
  enabled: true                 # Default: false -> keine Ausgabe, byte-stabil
  host: auto                    # auto = aus GIT_PLATFORM; sonst Schlüssel aus config/pr-template-hosts.yaml
  default: default              # Name des Templates für pull_request_template.md
  templates: [default, bugfix]  # welche benannten Templates zusätzlich geschrieben werden
  variables:                    # -> {{PR_VARS.<key>}}
    ticket_prefix: "PROJ"
    reviewers_hint: "@team-backend"
```

`config/project-config.schema.json` erhält den Block (`additionalProperties: false`, Typen, Enum für `host`).

### 3.4 Host-Mapping (Key-getrieben)

`config/pr-template-hosts.yaml` (neu), z. B.:

```yaml
hosts:
  github:
    default_path: .github/pull_request_template.md
    named_dir: .github/PULL_REQUEST_TEMPLATE      # <name>.md, Auswahl via ?template=<name>.md
  gitlab:                                           # Phase 3
    default_path: .gitlab/merge_request_templates/Default.md
    named_dir: .gitlab/merge_request_templates
```

Code liest nur diese Keys; ein neuer Host ist eine Config-Änderung.

## 4. Interface-Contracts

### IC-01 Dateilayout und Quellen
- Neues Verzeichnis `pr-templates/1-generic/` (Pflicht ab MVP) und `pr-templates/2-platform/` (ab Phase 1).
- Jede Template-Datei hat YAML-Frontmatter: `name`, `version`, `description`, `required-sections` (Liste von
  Überschriften), optional `platform`, `based-on` (bei Plattform-Varianten, wie bei Agents). Frontmatter wird
  **nicht** in die Ausgabe übernommen.
- Version-Bump bei Inhaltsänderung gemäß `rules/2-platform/agent-meta-conventions.md`.

### IC-02 Modul `scripts/lib/pr_templates.py`
```python
@dataclass(frozen=True)
class ResolvedPrTemplate:
    name: str
    layer: Literal["generic", "platform", "project"]
    source: Path
    required_sections: tuple[str, ...]

def resolve_pr_templates(agent_meta_root: Path, project_root: Path, config: dict) -> dict[str, ResolvedPrTemplate]
def render_pr_template(resolved: ResolvedPrTemplate, variables: dict, log: SyncLog) -> str
def sync_pr_templates(agent_meta_root, project_root, config, variables, log, dry_run) -> None
def pr_template_status(agent_meta_root, project_root, config) -> list[PrTemplateStatus]   # Phase 2
```
- `resolve_*`: unbekannter Name in `templates:`/`default:` → `SyncError` mit Liste verfügbarer Namen.
- `sync_pr_templates` ist ein Schritt in `sync_pipeline` direkt nach dem Kontext-/Regel-Sync, vor dem
  Gitignore-Schritt; `enabled: false` oder fehlender Block → `log.skip`, kein Schreibzugriff.
- Schreiben ausschließlich über `write_checked` (atomar, Secret-Scan, `--dry-run`/`--check`-fähig).

### IC-03 Host-Auflösung
`host: auto` liest `GIT_PLATFORM`. Unbekannter oder leerer Host → Warnung `pr-templates.unknown-host`, kein Schreiben.
Pfade ausschließlich aus `config/pr-template-hosts.yaml`; Pfade laufen durch `safe_path` (kein Traversal).

### IC-04 Variablen
Neue Variablen werden in `build_variables` ergänzt und in `scripts/lib/consistency/placeholders.py` als Built-ins
registriert (sonst entstehen Fehlalarme in `--validate`). `{{PR_VARS.<key>}}` ist eine dynamische Familie
(Prefix-Regel analog `PAL_*`). Fehlender `PR_VARS`-Key → Warnung, Platzhalter bleibt stehen.

### IC-05 CLI
| Flag | Verhalten |
|---|---|
| `--create-pr-template NAME` | kopiert das **wirksame** Template (aktuelle Auflösung) als Projekt-Override nach `.meta-config/pr-templates/NAME.md`; überschreibt nie |
| `--pr-template-status` | Tabelle: Name, wirksame Schicht, Quelle, Version, Divergenz (Phase 2) |
| `--pr-template-diff NAME` | Unified-Diff Projekt-Override gegen Framework-Template (Phase 2) |

Alle Flags in `docs/api/cli-reference.md` und im Admin-UI-Referenzdokument.

### IC-06 Besitz, Adoption, Konflikte
- Eine bereits vorhandene Zieldatei **ohne** Eintrag in `.meta-config/generated-file-hashes.json` ist
  nutzereigen: nicht überschreiben, Warnung `pr-templates.foreign-file` mit Hinweis auf
  `--create-pr-template` bzw. manuelle Übernahme.
- Eine von agent-meta geschriebene Datei, die seit dem letzten Sync lokal geändert wurde (Hash-Abweichung):
  nicht überschreiben, Warnung `pr-templates.diverged`; mit `--force` überschreiben.
- Löschen aus `templates:` entfernt die zuvor geschriebene, unveränderte Named-Datei (Stale-Cleanup wie bei Agents).

### IC-07 Rule und Agenten
- Neue Rule `rules/1-generic/pr-template.md` (Master-Rule): Vor `gh pr create`/`glab mr create` das
  wirksame Template lesen, **jeden** Abschnitt ausfüllen, Checkboxen nicht löschen, Issue mit `Closes #n`
  verknüpfen, Body per `--body-file` übergeben (Heredoc-Bodies sind im `dod-push-check`-Hook unproblematisch,
  aber `--body-file` ist robuster).
- `agents/1-generic/git.md` (Zeile PR) und `release.md` verweisen auf die Rule statt auf einen freien Body
  (Version-Bump, `based-on`-Ketten prüfen).
- Rule ist an `pr-templates.enabled` gekoppelt (`rule-gates`), sonst nicht im Kontext.

### IC-08 Manager-Workflow (Vorschläge ins Framework)
Neuer Abschnitt im `agent-meta-manager` (neben §7 „Propose a new agent“):

| Scope | Aktion |
|---|---|
| Template ist projektübergreifend nützlich | `meta-feedback`, Label `new-pr-template` |
| Nur für eine Plattform | `meta-feedback`, Label `new-platform-pr-template` |
| Nur dieses Projekt | bleibt Projekt-Override |

Pflichtschritte des Managers: (1) `--pr-template-status`/`--pr-template-diff` auslesen, (2) Projektbezüge
(Namen, URLs, Ticket-Präfixe) durch Variablen ersetzen (`{{PROJECT_NAME}}`, `{{PR_VARS.…}}`), (3) **Nutzerbestätigung
vor dem Anlegen des Issues** (bestehende Manager-Regel §3), (4) Issue enthält Template-Text, benutzte Variablen,
Begründung, Plattform-Bezug. Umgekehrt: weicht das Framework-Template von einem unveränderten Projekt-Override ab,
schlägt der Manager `adopt framework version` vor. `meta-feedback.md`: ISSUE_TYPE-Enum und Label-Tabelle um die zwei Labels erweitern.

### IC-09 Validierung / Consistency-Check
Neue Checks (`scripts/lib/consistency/pr_templates.py`):
`pr-templates.missing-required-section` (Error), `pr-templates.unknown-placeholder` (Error),
`pr-templates.unknown-host` (Warning), `pr-templates.foreign-file` / `.diverged` (Warning),
`pr-templates.frontmatter` (Error: fehlende `name`/`version`/`required-sections`).
Nur aktiv, wenn `pr-templates.enabled`.

### IC-10 Gitignore / Standalone / Provider
- Zieldateien sind **versioniert** (nicht gitignoriert); kein Eintrag im Managed-Block.
- Der Schritt ist provider-unabhängig (hängt am Git-Host, nicht am KI-Provider).
- `--render-standalone` ist nicht betroffen.

### IC-11 Doku und Szenarien
`docs/api/cli-reference.md`, `docs/guides/` (neuer Guide „PR-Templates“), `docs/architecture/01-layer-model.md`
(Abschnitt „PR-Templates“), `config/project-config.schema.json`, `templates/configs/project.yaml.example`,
`tests/scenarios/registry.md` (neues Szenario `NN-pr-templates`, Asserts siehe AC), `CHANGELOG.md`.

## 5. Datenfluss

```
project.yaml pr-templates ─┐
platforms: [p]            ─┤
pr-templates/1-generic    ─┼─ resolve (Vorrang Projekt > Plattform > Generic)
pr-templates/2-platform   ─┤
.meta-config/pr-templates ─┘
          │
          ▼  build_variables (+ PR_TEMPLATE_NAME, DOD_CHECKLIST_BLOCK, PR_VARS)
     substitute + strip_inactive_conditional_blocks
          │
          ▼  Host-Mapping (config/pr-template-hosts.yaml)
 write_checked -> .github/pull_request_template.md + .github/PULL_REQUEST_TEMPLATE/<name>.md
          │
          ├─► GitHub-Web-UI / gh pr create (nativ)
          └─► git-/release-Agent via Rule pr-template (Body ausfüllen, --body-file)
```

## 6. Akzeptanzkriterien

Phase 0 (MVP: Generic + Projekt, GitHub, Sync, Rule):
1. **AC-01** Ohne `pr-templates:` oder mit `enabled: false` ist die Sync-Ausgabe byte-identisch zum Stand vor dem Feature (Test: Vorher/Nachher-Vergleich über alle Provider-Matrix-Projekte).
2. **AC-02** Mit `enabled: true` und `default: default` entsteht `.github/pull_request_template.md` mit aufgelösten Variablen; `sync.py --check` ist danach grün (idempotent).
3. **AC-03** `templates: [default, bugfix]` erzeugt zusätzlich `.github/PULL_REQUEST_TEMPLATE/default.md` und `bugfix.md`.
4. **AC-04** Ein Projekt-Override `.meta-config/pr-templates/default.md` gewinnt gegen die Generic-Variante; die Ausgabe enthält den Override-Inhalt.
5. **AC-05** Eine vorhandene, nicht von agent-meta stammende `pull_request_template.md` wird nicht überschrieben; Warnung `pr-templates.foreign-file` erscheint in `sync.log`.
6. **AC-06** Eine lokal geänderte, von agent-meta geschriebene Datei wird nicht überschrieben (`pr-templates.diverged`); mit `--force` wird sie überschrieben.
7. **AC-07** `--create-pr-template NAME` legt den Override aus dem wirksamen Template an und überschreibt nie eine vorhandene Datei (Exit 0 mit Hinweis).
8. **AC-08** `{{#if DOD_REQ_TRACEABILITY}}` / `{{#if DOD_TESTS_REQUIRED}}` schalten Abschnitte korrekt; `{{DOD_CHECKLIST_BLOCK}}` listet genau die im `dod-preset` aktiven Gates.
9. **AC-09** Unbekannter Name in `default:`/`templates:` bricht den Sync mit `SyncError` und Liste der verfügbaren Namen ab.
10. **AC-10** Rule `pr-template` ist nur bei `enabled: true` im Kontext aller Provider enthalten; `git.md` verweist darauf.

Phase 1 (Plattform + Variablen + Validierung):
11. **AC-11** Platzhalter ohne Wert in einem PR-Template → `--validate` Fehler `pr-templates.unknown-placeholder`; `{{PR_VARS.x}}` ohne Wert → Warnung.
12. **AC-12** Aktive Plattform mit `pr-templates/2-platform/<platform>-default.md` überschreibt Generic; `{{platform.<p>.<key>}}` wird mit Projekt-Override-Wert substituiert.
13. **AC-13** Fehlender Pflicht-Abschnitt aus `required-sections` im Projekt-Override → Fehler `pr-templates.missing-required-section`.
14. **AC-14** Unbekannter Host (`GIT_PLATFORM` leer/unbekannt) → Warnung, kein Schreiben, Sync-Exit 0.

Phase 2 (Manager):
15. **AC-15** `--pr-template-status` zeigt je Name Schicht, Quelle, Version und Divergenz; `--pr-template-diff NAME` liefert einen Diff Override↔Framework.
16. **AC-16** `meta-feedback` kennt die Labels `new-pr-template` und `new-platform-pr-template` (ISSUE_TYPE-Enum, Label-Tabelle); Manager-Template enthält den Abschnitt inklusive Pflicht zur Nutzerbestätigung und zur Variablisierung von Projektbezügen.
17. **AC-17** Szenario `NN-pr-templates` in `tests/scenarios/registry.md` mit ≥ 6 Asserts; `consistency-check.py` ist grün.

Quer:
18. **AC-18** Kein Provider-/Host-Literal im neuen Code (Guard `test_no_provider_literal_usage_in_lib` bleibt grün; neuer Test: kein Host-Name-Literal in `pr_templates.py`).
19. **AC-19** Python 3.9-kompatibel (CI-Matrix), nur Stdlib + PyYAML.

## 7. Offene Fragen und Risiken

| # | Frage / Risiko | Empfehlung |
|---|---|---|
| Q1 | Ownership über `generated-file-hashes.json` oder eigener Index? Muss im Plan gegen `generated_file_drift.py` verifiziert werden. | Bestehenden Hash-Mechanismus nutzen, nur bei Lücke neuen Index |
| Q2 | Ein Template für GitHub-Default plus Named Templates — oder nur Named? | Beides (MVP wie in §3.3), `default` immer als `pull_request_template.md` |
| Q3 | Sprache: Template-Text deutsch oder englisch? | Framework-Templates englisch mit `{{DOCS_LANGUAGE}}`-Hinweis; Projekt-Override frei (Sprachregel: Doku deutsch, README englisch gilt für agent-meta selbst, nicht für ausgelieferte Templates) |
| Q4 | Schichtreihenfolge bei mehreren aktiven Plattformen | Reihenfolge in `platforms:`; Konflikt → Warnung |
| Q5 | Soll `release`-Template an `release.distribution` gekoppelt werden (Analogon `release_scaffold`)? | Phase 1 prüfen, nicht MVP |
| R1 | Template-Drift durch manuelle Edits | IC-06 (Divergenz-Erkennung) |
| R2 | Vertrauliche Projektinhalte im Upstream-Vorschlag | IC-08 Schritt 2+3 (Variablisierung, Nutzerbestätigung) |
| R3 | Zusätzliche Sync-Laufzeit | vernachlässigbar (Textdateien); AC-01 beweist Null-Effekt im Default |

## 8. Betroffene Dateien (Schätzung)

Neu: `pr-templates/1-generic/*.md`, `pr-templates/2-platform/*.md` (Phase 1), `scripts/lib/pr_templates.py`,
`scripts/lib/consistency/pr_templates.py`, `config/pr-template-hosts.yaml`, `rules/1-generic/pr-template.md`,
`tests/test_pr_templates*.py`, Szenario, Guide.
Geändert: `scripts/lib/sync_pipeline.py`, `scripts/lib/config.py` (Variablen), `scripts/lib/consistency/placeholders.py`,
`scripts/lib/cli_commands.py` + `scripts/sync.py` (Flags), `config/project-config.schema.json`, `config/rules-presets.yaml`,
`agents/1-generic/{git,release,agent-meta-manager,meta-feedback}.md`, Doku, `CHANGELOG.md`.

## 9. Phasen

| Phase | Inhalt | Ergebnis |
|---|---|---|
| 0 | Generic + Projekt-Override, GitHub-Host, Sync, `--create-pr-template`, Rule, ACs 01–10 | nutzbares MVP, Default aus |
| 1 | Plattform-Schicht, Variablen/`PR_VARS`, Validierung/Consistency, ACs 11–14 | volle Schichtung |
| 2 | Manager-Workflow (Status/Diff/Vorschlag), Labels, Szenario, ACs 15–17 | Rückfluss ins Framework |
| 3 | Weitere Hosts (GitLab), Admin-UI-Bereich, Issue-Templates als Folge-Request | Ausbau |

## 10. Revisionen

| Datum | Änderung |
|---|---|
| 2026-10-11 | Erstentwurf |
