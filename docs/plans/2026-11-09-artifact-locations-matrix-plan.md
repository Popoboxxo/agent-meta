---
pipeline_stages:
  implement: 3
status: APPROVED
approved: 2026-11-09
revision: "4"
date: 2026-11-09
issue: 1186
class: XL
base-commit: aaed14c2
branch: docs/config-wave-plans-1181-1188
spec: docs/specs/2026-11-09-artifact-locations-matrix-spec.md
trace:
  - SPEC-1186-artifact-locations-matrix
  - issue-1186
---

# Artifact-Locations-Matrix für alle Artefakt-Klassen (Issue #1186) — Implementation Plan

> **Status: APPROVED** — Approved: 2026-11-09 (User-Freigabe via main_chat). Dieser Plan ist der
> Ausführungsauftrag für die zugehörige Spec
> `docs/specs/2026-11-09-artifact-locations-matrix-spec.md`, die `Status: APPROVED` trägt
> (approved 2026-11-09). Die Umsetzung ist damit autorisiert (Master-Rule `spec-plan-workflow`).
> **Klasse:** XL (Spec §1: Umfang >20 Dateien, Querschnitt über
> Config-Vertrag + Schreibvertrag + Variablen-Vertrag, nicht umkehrbar ohne
> Migration).
> **Datum:** 2026-11-09 · **Base:** `aaed14c2` · **Branch-Anforderung für die
> Umsetzung:** `feat/1186-artifact-locations-matrix` (Branch-Guard
> `rules/1-generic/branch-guard.md`; der Plan-Branch `docs/…` ist kein
> Implementierungsbranch).
> **Quellen:** Spec (16 ACs, D-6/D-7, Contracts §4), Issue-#1186-Dump,
> Issue-Dumps #1150/#1189/#1141/#1180/#1195, `baseline-validate.txt`,
> `baseline-check.txt`, Ist-Code.
> **Revision:** 2 (Review-Auflösung 2026-11-09) — Runde 2: RVW2-1186-01…05,
> RVW2-X-01, RVW2-X-02 plus zwei formale Blocker (`revision`-Feld,
> AC-Wortlaut/Präzisierungs-Split); siehe §15.
> **Revision 3 (Szenario-Konflikte K1–K8, 2026-11-09):** K1 (`unmanaged` statt
> `project-state`) und K3 (vier Wertequellen + Source-Attribution) sind eingearbeitet,
> K6 ist als `$defs`-Konsistenz notiert. K2/K4/K5/K7/K8 betreffen diesen Plan nicht.
> Auflösungstabelle: §15.2.
> **Revision 4 (Entscheidungsprotokoll D1–D4, 2026-11-09):** OQ-5 (eine Scratch-Quelle,
> Alias-Migration, Containment-Hook liest Matrix), OQ-7 (D-9-Ausnahme bleibt), OQ-3
> (Naming-Token + ADR-Default + Legacy-Formen), OQ-4 (`SE`, Regeltext auf
> `{{ARTIFACT_SE_ROOT}}`). Neue Tasks **T23** (Alias-Migration) und **T24**
> (Containment-Hook auf aufgelösten Pfad). Auflösungstabelle: §16.
> **Voraussetzungen (kanonische Reihenfolge, verbindlich — Review 2026-11-09):**
> `#1187 → #1186 → #1188 → #1181`, danach `#1141`. Die **Whitelist-Ableitung aus dem Schema
> zuletzt** (eigenes Follow-up, T22).
> 1. **#1189** gemergt (Admin-Server-Start testbar; sonst AC-06/07 nur
>    In-Process testbar) — Blocker für M5. Unabhängig von der Wellenreihenfolge, läuft zuerst.
> 2. **#1187** gemergt (gleiche Templates/`config.py`/Schema; `{{PROJECT_CONTEXT}}`).
> 3. **#1181** läuft **nach** #1186: #1181-T9 baut dieselbe **Stage 14** in
>    `scripts/lib/sync_pipeline.py:1893-1924` um, #1186 hängt Stage 14c direkt danach
>    (`cli_commands.py:1613-1616`). Parallel-Edit ist ausgeschlossen.
> 4. **#1188** läuft **nach** #1186: #1186 deklariert `docs/issue-labels.md` bereits als
>    `project-docs.files.issue-labels` (T1), damit der Managed-Tree-Hook die von #1188
>    erzeugte Datei nicht blockt.
> 5. **#1141** läuft **nach** #1181. `se_output` wird in T3 deklariert, damit #1141 es nicht
>    nachträglich bricht. Die Aussage „#1141 vor oder im selben PR" ist **zurückgezogen**:
>    die Wurzel-Regel ist nicht Voraussetzung für die Sektions-Validierung.
> 6. **#1151** verifiziert/geschlossen (Hook-Helfer `hook_common.sh` v1.9.0).
> 7. **#1180** für H-3 (generierte Lazy-Pointer-Tabelle) — blockiert nur Task 13, nicht den Rest.
> 8. Keine Parallel-Edits an `config/project-config.schema.json`,
>    `scripts/admin-server.py`, `docs/ui/admin-ui.html`,
>    `scripts/lib/consistency/placeholders.py`, `agents/1-generic/*.md`
>    (Spec §9). Federführung #1186 für die Artefakt-Matrix, #1187 für
>    `{{PROJECT_CONTEXT}}`, #1188 für `feedback.md`/`meta-feedback.md`/
>    `bug-feature-analyzer.md`; bei den drei Feedback-Rollen läuft #1186
>    **vor** #1188.

**Goal:** Ein konsolidiertes Config-Surface `artifact-locations` (Matrix aus
14 Nicht-SE- + 9 SE-Klassen, `mode` `files|inline|off`, `git`, `naming`,
`legacy[]`, `retention`) ersetzt die 48 `{{TMP_SINK_PATH}}`-Persistenz-Pfade,
die in Spec §2.2/§2.3 inventarisierten Pfad-Literale und den schema-losen
`se_output.base_dir`.
`sync.py` löst die Matrix mit belegter Präzedenz auf (`source` je Klasse),
exportiert `{{ARTIFACT_*_DIR}}`/`{{ARTIFACT_*_MODE}}` einmal pro Provider,
scaffoldet jedes `files`-Verzeichnis idempotent und schreibt die aufgelöste
Matrix als Datendatei für den Hook. Ein PreToolUse-Hook routet Schreibpfade
(Default warnen, `strict` blockt), ein Consistency-Check meldet Literale und
Legacy-Writes, das Admin-UI liest/schreibt die Sektion mit Pfad-Validierung,
und `sync.py --status-artifacts --json` liefert den Maschinen-Vertrag.

**Architecture:** Drei Schichten, eine Wahrheit. (1) **Daten:** Schema +
`config/artifact-locations-presets.yaml` + `project.yaml`. (2) **Auflösung:**
`scripts/lib/artifact_locations.py` ist der **einzige** Ort, der die Matrix
auflöst (vier Wertequellen plus Source-Attribution, feldweise, mit `source`-Reporting); alle
Konsumenten (Variablen, Scaffold, CLI, Hook-Datendatei, Admin-UI-Guard,
Consistency-Check) lesen dieses Ergebnis und duplizieren keine Logik.
(3) **Durchsetzung:** generierte Variablen statt Literale (Rollen),
Consistency-Check (Warnung) und Hook (Konvention, fail-open, `strict`
opt-in). Keine Provider-Verzweigung, keine neuen Admin-Endpunkte, kein
Retention-Daemon, keine SE-Zellstruktur-Änderung.

**Tech Stack:** Python 3 Stdlib (dataclasses, pathlib, json, re), PyYAML
(bestehende Runtime-Ausnahme, `docs/adr/0001-pyyaml-runtime-ausnahme.md`),
POSIX-sh-Hook auf `hooks/1-generic/lib/hook_common.sh` v1.9.0, JSON Schema
draft-07, pytest, Markdown/YAML.

**Spec:** `docs/specs/2026-11-09-artifact-locations-matrix-spec.md`
**Spec-ID:** `SPEC-1186-artifact-locations-matrix`
**Issue:** [#1186](https://github.com/Popoboxxo/agent-meta/issues/1186)
**Aufwand:** 24 Tasks in 6 Meilensteinen (**T1–T21, T23, T24 = 23 im PR**;
**T22 = Follow-up nach #1141**, nicht Teil des #1186-PR), 7 neue Produktionsmodule/Hook,
1 neue Preset-Datei, 1 neue Lazy-Rule, 17 neue Testdateien + 1 Szenario-Assert,
**26 Rollen-Templates** (10 Nicht-SE + 12 SE + 4 Reviewer), 2 Doku-/Changelog-Änderungen.
Eine belastbare Schätzung liefert `effort-estimator` (Textverweis; hier bewusst nicht
berechnet).

## Größe je Task (Übersicht)

| Größe | Tasks |
|---|---|
| S | T3, T7, T9, T12, T17, T24 |
| M | T1, T2, T6, T13, T18, T20, T22 (Follow-up), T23 |
| L | T5, T8, T10, T11, T14, T15, T16, T19, T21 |
| XL | T4 (Resolver-Kern: 4 Wertequellen + Source-Attribution, 23 Klassen, Alias-Projektion, Naming-Auflösung) |

**Revision 4 — betroffene Tasks (D1–D4):** D1 → T4, T5, T9, T15, **T23 (neu)**, **T24 (neu)**;
D2 → T6 (unverändert, Entscheidung bestätigt); D3 → T1, T2, T4, T5, T15, T23; D4 → T2, T20.

## 1. Zielbild in fünf Sätzen

1. Jede Artefakt-Klasse hat genau **einen** konfigurierbaren Ausgabeort, einen
   Modus (`files`, `inline`, `off`), ein Naming und eine Git-Behandlung — und
   diese Werte stehen an genau einer Stelle (`artifact-locations`).
2. Rollen-Templates enthalten **keine** verwalteten Pfad-Literale mehr,
   sondern ausschließlich generierte `{{ARTIFACT_*_DIR}}`/`{{ARTIFACT_*_MODE}}`,
   die `sync.py` einmal pro Provider aus der aufgelösten Matrix rendert.
3. Jede Auflösung ist **belegbar**: `source` nennt `project`,
   `preset:<name>`, `project-preset:<name>` (Attribution), `schema-default`,
   `code-fallback` oder `disabled` — es gibt keinen stillen Default und keinen stillen
   Preset-Sieg. Vier **Wertequellen**, zwei Attributionen (K3).
4. Bestandsprojekte verlieren nichts: `legacy[]` ist additiv und read-only,
   `enabled: false` stellt exakt das heutige Verhalten wieder her, und keine
   Datei wird verschoben, archiviert oder gelöscht. Der Scratch-Bereich hat **eine**
   Quelle (D1): `repo_containment.tmp-sink.path` ist nur noch Migrations-Alias mit
   Gleichheitszwang und Deprecation-Warnung; `--migrate-artifact-aliases --write`
   zieht die Matrix nach, ohne Kommentare zu verlieren.
5. Durchsetzung ist **zweistufig und verhältnismäßig**: der
   Consistency-Check warnt sofort (und immer), der Hook blockt `legacy[]`-Ziele
   und (bei `strict: true`) Fehlrouten — **sobald er aktiviert ist**
   (`enabled_by_default: false`); fehlende Datendatei blockt nie (Routing-
   Konvention, keine Security Boundary). Verzeichnis-Marker (`.gitkeep`) sind in
   beiden Wegen ausgenommen, und die `legacy-write`-Meldung ist **baseline-basiert**
   (`baseline.legacy_files`, kein mtime) — AC-09-Präzisierung.

---

## 2. File-Structure-Map

Alle Pfade relativ zum Repo-Root. „neu" = Datei existiert auf `aaed14c2`
nicht; „ändern" = vorhandene Datei. Die Task-Spalte nennt den **Owner**
(Ownership-Barriere; eine Datei hat genau einen schreibenden Task).

### 2.1 Neue Dateien

Alle Zeilen sind **Create** (Datei existiert auf `aaed14c2` nicht).

| Datei | Status | Zweck | Task |
|---|---|---|---|
| `config/artifact-locations-presets.yaml` | Create | Presets `default`, `minimal`, `flat`, `docs-only`; reine Daten, Vorbild `config/rules-presets.yaml:47` | T2 |
| `scripts/lib/artifact_locations.py` | Create | **Einziger** Matrix-Resolver: `CLASS_REGISTRY`, vier Wertequellen + Source-Attribution (K3), `source`-Reporting, SE-Projektion (D-7), Zell-Pfad, Validierungsfehler | T4 |
| `scripts/lib/artifact_scaffold.py` | Create | Verallgemeinertes Scaffolding: `files`-Verzeichnisse + `.gitkeep`, `legacy`-Zielverzeichnis `docs/conclusions` (D-6), Marker-Ausnahme | T8 |
| `scripts/lib/artifact_status.py` | Create | `--status-artifacts`-Report (Mensch + JSON `schema_version: "1"`), Datei-Zählung ohne `*.sync-backup-*` (#1195), `naming`/`field_sources` additiv (D1/D3) | T15 |
| `scripts/lib/artifact_migration.py` | Create | Alias-Migration (D1): liest `repo_containment.tmp-sink.path`/`se_output.base_dir`/`spec-plan-workflow.paths.*`/`progress.*`/`viz.event_log`, erzeugt den `artifact-locations`-Snippet, `--write` schreibt kommentar-erhaltend (Roundtrip-Guard), idempotent | T23 |
| `scripts/lib/consistency/artifact_locations.py` | Create | 5 Checks: `literal-path`, `legacy-write` (baseline-basiert), `inline-with-path-promise`, `missing-dir`, `alias-divergence` | T14 |
| `hooks/1-generic/artifact-path-guard.sh` | Create | PreToolUse-Routing-Guard auf `.meta-config/artifact-locations.resolved.json`, fail-open, `strict` opt-in | T16 |
| `rules/1-generic/artifact-locations.md` | Create | **Eine** Lazy-Rule (`channel: skill`, H-1) mit Matrix-Tabelle, Modus-Semantik und Rollen-Anleitung | T13 |
| `tests/scenarios/configs/99-artifact-locations-matrix.project.yaml` | Create | Szenario-Config (ID 99; 94–98 sind durch #1181/#1187 belegt) | T21 |
| `tests/scenarios/asserts/99-artifact-locations-matrix.sh` | Create | Content-Assertions für das Szenario 99 | T21 |
| `tests/test_artifact_locations_schema.py` | Create | Schema-Vertrag (16+ Assertions) | T1, T3 |
| `tests/test_artifact_locations_presets.py` | Create | Preset-Daten gegen Schema und Klassen-Registry | T2 |
| `tests/test_artifact_locations_resolver.py` | Create | Präzedenz, `source`, Klassen-Zählung, SE-Zellen, SE-Projektion, D-6/D-7 | T4 |
| `tests/test_artifact_locations_validate.py` | Create | alle 8 harten Fehlercodes, `se-decomposition: off` erlaubt | T5 |
| `tests/test_artifact_locations_variables.py` | Create | `ARTIFACT_*`-Export (54), Alias, Standalone-Fallbacks, `_reference-agent`-Escape | T6 |
| `tests/test_artifact_locations_placeholders.py` | Create | `derive_builder_vars ⊆ _BUILTIN_VARS` + keine unbekannten Platzhalter (§4.7) | T7 |
| `tests/test_artifact_scaffold.py` | Create | Verzeichnis-Anlage, `.gitkeep`, dry-run, `ignored`-Klassen, Marker-Konstante — **ohne** `check_artifact_locations`-Fälle (die leben in T14, RVW2-1186-01) | T8 |
| `tests/test_artifact_locations_aliases.py` | Create | Deprecation-Warnungen, Divergenz-Fälle | T9 |
| `tests/test_artifact_locations_templates.py` | Create | Golden: kein Schreib-Literal, jede Klasse nutzt ihre Variable, F-1-Klammerform, Read-OK-Ratchet | T10, T11, T12 |
| `tests/test_consistency_artifact_locations.py` | Create | 5 Checks, `enabled: false` still, Baseline-/`unmanaged`-Fälle, Abgrenzung zu `temp_literals` | T14 |
| `tests/test_artifact_status_cli.py` | Create | Exit 0/2, JSON-Pflichtfelder, `--status`-Kollision | T15 |
| `tests/test_artifact_path_guard_hook.py` | Create | Entscheidungstabelle §4.5, fail-open, `strict`, Marker-Durchlass | T16 |
| `tests/test_artifact_locations_admin_api.py` | Create | `../x` ⇒ 400, Feldname in Meldung, Guard vor Disk-Write | T18 |
| `tests/test_artifact_locations_admin_ui.py` | Create | statische Pane-/Routing-/Select-Assertions gegen `admin-ui.html` | T19 |
| `tests/test_artifact_locations_scenario.py` | Create | **Ein** voller Szenarientest in `.tmp/scenario-artifacts-1186/` | T21 |
| `tests/test_artifact_locations_migration.py` | Create | Alias-Migration: dry-run schreibt nicht, `--write` idempotent + Roundtrip-Guard, Divergenz verweigert, `enabled: false` verweigert | T23 |
| `tests/test_repo_containment_scratch_resolution.py` | Create | Containment-Hook liest `classes.scratch.path` aus der Datendatei (D1), Fallback-Kette, `tmp-sink.enabled` bleibt Schalter, lexikalische Parität unverändert | T24 |

### 2.2 Geänderte Dateien

Alle Zeilen sind **Modify** (Datei existiert auf `aaed14c2`).

| Datei | Status | Zweck | Task |
|---|---|---|---|
| `config/project-config.schema.json` | Modify | Sektion `artifact-locations` (`:2223`-Umfeld) inkl. `unmanaged[]` + `$defs` (`:2855`); `se_output` deklarieren; `$defs/artifactKind` + `artifactClassName` + `artifactNaming` (D3) | T1, T3 |
| `scripts/lib/config.py` | Modify | `_validate_artifact_locations`, `_build_artifact_variables` (Aufruf bei `:2770-2771`), Alias-Warnungen | T5, T6, T9 |
| `scripts/lib/standalone.py` | Modify | `_standalone_variables` (`:295-336`) liefert die 54 `ARTIFACT_*`-Framework-Defaults (sonst „not available"-Notizen in exportierten Personas); **D2 (DECIDED 2026-11-09): D-9-Ausnahme bleibt**, #1187 ist Datei-Federführer, die Reihenfolge #1187 → #1186 schließt den Parallel-Edit aus (§13 OQ-7) | T6 |
| `scripts/lib/spec_plan_scaffold.py` | Modify | `scaffold_spec_plan_dirs` wird dünner Wrapper (Import bleibt: `sync_pipeline.py:152`, `knowledge.py:12`) | T8 |
| `scripts/lib/sync_pipeline.py` | Modify | Scaffold-Aufruf (`:1699`) + neue Stage **14c** „resolved.json" nach `:1615` (Muster `:1893-1924`; **Kollisionsfläche mit #1181-T9**) | T8, T15 |
| `scripts/lib/consistency/placeholders.py` | Modify | **54** `ARTIFACT_*`-Namen in `_BUILTIN_VARS` (Block ab `:12`); `_UNREGISTERED_BUILDER_RATCHET` bleibt unangetastet (shrink-only) | T7 |
| `scripts/consistency-check.py` | Modify | Import (`:42-69`) + Aufruf (`:238-249`) | T14 |
| `scripts/sync.py` | Modify | `--status-artifacts`/`--json`, `_MODE_HANDLERS` (`:757`), `_STDOUT_CLEAN_MODES` (`:791`) | T15 |
| `scripts/lib/cli_commands.py` | Modify | `_handle_status_artifacts`, Stage-Verdrahtung (`:1613-1616`) | T15 |
| `scripts/admin-server.py` | Modify | `artifact-locations` in `PROJECT_WRITABLE_SECTIONS` (`:234-259`), `_guard_artifact_locations_write` im Guard-Block (`:5305-5308`) | T17, T18 |
| `docs/ui/admin-ui.html` | Modify | Pane „Artifacts" (Muster `:7314-7315`, `:7448`, `:11377`) | T19 |
| `hooks/1-generic/repo-containment{,-impl}.sh` | Modify | Scratch-Pfad kommt aus der **aufgelösten** Matrix (D1): `ARTIFACT_SCRATCH_DIR`-Env → `classes.scratch.path` aus `.meta-config/artifact-locations.resolved.json` → `repo_containment.tmp-sink.path` → `.tmp`; `tmp-sink.enabled` bleibt Schalter; lexikalische Regeln unverändert | T24 |
| `docs/api/cli-reference.md` | Modify | `--status-artifacts` + `--json` dokumentieren (sonst ERROR `docs.cli_reference`, `lib/consistency/docs.py:9-44`); **`--migrate-artifact-aliases` + `--write` sequenziell nach T15** (dokumentierte Kette auf derselben Datei) | T15, T23 |
| `docs/api/admin-ui-reference.md` | Modify | `<!-- help-id: project_instance-artifact_locations -->` (sonst ERROR `docs.ui_help_mappings`, `docs.py:47-97`) | T19 |
| `config/routing/reviewers.yaml` | Modify | `notes:` (`:23-29`) nennt Matrix statt tmp-Sink | T12 |
| `config/rules-presets.yaml` | Modify | `artifact-locations` im `lazy`-Preset (`channel: skill`, Muster `:110-132`) | T13 |
| `rules/1-generic/use-lazy-rules.md` | Modify | Pointer-Tabelle (`:5-21`) um Artefakt-Skill ergänzen/regenerieren (H-3) | T13 |
| `rules/1-generic/se-cascade-artifact-taxonomy.md` | Modify | `:10` Literal `docs/se` → `{{ARTIFACT_SE_ROOT}}` (**D4**); `docs/se/**` als Legacy-Ablage benannt, nicht als Default | T20 |
| `agents/1-generic/agent-meta-manager.md` | Modify | `--status-artifacts` referenzieren (AC-14; Muster `:88`, `:107`, `:112`) | T20 |
| `agents/1-generic/ideation.md` | Modify | `:97` `concept-<topic>.md` → `{{ARTIFACT_CONCEPTS_DIR}}` | T10 |
| `agents/1-generic/planner.md` | Modify | `:75` Root-Fallback → `{{ARTIFACT_PLANS_DIR}}` | T10 |
| `agents/1-generic/requirements.md` | Modify | `:71`, `:75` `docs/REQUIREMENTS.md`/`plan-<topic>.md` → Variablen | T10 |
| `agents/1-generic/documenter.md` | Modify | `:43`, `:131-134` `docs/conclusions`/`docs/CODEBASE_OVERVIEW.md`/`docs/ARCHITECTURE.md` **und `:81` `docs/plans/archive`** (Schreibziel) | T10 |
| `agents/1-generic/knowledge-migrator.md` | Modify | `:39`, `:50` `docs/conclusions/` bleibt Lese-Literal + Ratchet-Marker `<!-- artifact-read-ok -->` | T10 |
| `agents/1-generic/concept-reviewer.md` | Modify | `:92` „e.g. `concept-review-<topic>.md`" → `{{ARTIFACT_REVIEWS_DIR}}` | T10 |
| `agents/1-generic/copyeditor.md`, `proofreader.md` | Modify | `:92`/`:89` „neben der Quelldatei" → `{{ARTIFACT_REVIEWS_DIR}}` (`kind: copyedit`/`proofread`) | T10 |
| `agents/1-generic/effort-estimator.md` | Modify | `:116` undefinierter Pfad → `{{ARTIFACT_ANALYSIS_DIR}}` (`kind: estimate`) | T10 |
| `agents/1-generic/explorer.md` | Modify | `:71` `docs/spikes/…` → `{{ARTIFACT_SPIKES_DIR}}` | T10 |
| `agents/1-generic/{security-auditor,ai-security-guardian,app-lifecycle-governor,prompt-governor}.md` | Modify | Vollreport-Ziel → `{{ARTIFACT_AUDITS_DIR}}`/`{{ARTIFACT_REVIEWS_DIR}}` | T12 |
| `agents/1-generic/se-{requirements,component-requirements,architect,interface-mgr,developer,senior-developer,junior-developer,integration-and-test-manager,validator,verifier,termination,critic}.md` | Modify | 16× `{SE_BASE_DIR}` (einfache Klammer, F-1) → `{{ARTIFACT_SE_*_DIR}}`/`{{ARTIFACT_SE_ROOT}}`; `se-critic` `:110`/`:114` → `{{ARTIFACT_SE_REVIEWS_DIR}}`/`{{ARTIFACT_SE_REPORTS_DIR}}` | T11 |
| `templates/configs/project.yaml.example` | Modify | `artifact-locations`-Beispielblock (vollständiges Beispiel) | T20 |
| `howto/configs/project.yaml.example` | Modify | derselbe Block — beide vollständigen Beispiele müssen synchron bleiben (`docs/guides/project.yaml.example` ist ein Orchestrator-Teilbeispiel und bleibt unverändert) | T20 |
| `tests/scenarios/registry.md` | Modify | Katalogzeile `99-artifact-locations-matrix` (94–98 sind durch #1181/#1187 belegt) | T21 |
| `CHANGELOG.md` | Modify | Feature-Eintrag + Migrationshinweis (`legacy[]`, `enabled: false`, Scratch-Alias → `--migrate-artifact-aliases`, ADR-Naming D3) | T20 |
| `tests/test_spec_plan_scaffold.py` | Modify | Wrapper-Verhalten bleibt; neue Delegation prüfen | T8 |
| `tests/test_admin_server.py` | Modify | `artifact-locations` in der Whitelist (Mengen-Assertion folgt erst in T22) | T17 |

> **Summe:** 27 neue Dateien (8 Produktions-/Daten-/Rule-Dateien + 2 Szenario-Dateien +
> 17 Tests) und **51 geänderte Dateien in 36 Tabellenzeilen** (vier Zeilen bündeln mehrere
> Dateien: `copyeditor`/`proofreader` = 2, Reviewer-Rollen = 4, SE-Rollen = 12,
> `repo-containment{,-impl}.sh` = 2). Damit ist die Spec-Forderung „alle 25+ Dateien"
> über 9 Produktionsbereiche erfüllt.

### 2.3 Konfliktflächen ohne Änderung in #1186

| Datei | Warum gelistet | Warum kein Edit hier |
|---|---|---|
| `scripts/lib/variables.py` | `strip_inactive_conditional_blocks`-Whitelist (`:570-598`) und `_conditional_active` (`:498-508`) entscheiden, ob ein `{{#if}}` renderbar ist — dort würde ein späteres `ARTIFACT_*_MODE`-Gate und jedes Wellen-Conditional kollidieren | #1186 fügt **kein** Conditional hinzu (AC-05-Präzisierung, Spec §6.3); Datei-Federführung **#1187** (Zielmatrix RVW2-X-01), kein Edit hier |
| `scripts/lib/agent_sync.py` | Wird von #1187, #1188 und #1181 geändert (Zielmatrix RVW2-X-01) | **kein** Edit in #1186 — nicht als Konfliktfläche beansprucht |
| `docs/issue-labels.md` | von #1188 erzeugt, von #1186 klassifiziert | #1186 deklariert nur den Pfad (`project-docs.files.issue-labels`, T1), erzeugt die Datei nicht |
| `.meta-config/issue-labels-state.json` | von #1188 erzeugt, von #1186 klassifiziert | #1186 deklariert den Pfad nur als `unmanaged[]` (D-8, §3.2a); kein Scaffold, kein Block, keine Warnung (K1: `project-state` ist gestrichen) |
| `hooks/1-generic/repo-containment{,-impl}.sh` | **Hotspot ohne Parallel-Edit:** die Pfad-Quelle wird auf die aufgelöste Matrix umgestellt (D1, T24); die lexikalischen Regeln und `hook_common.sh` bleiben unangetastet | Kein anderes Welle-Issue editiert den Hook; Historie #1136/#1151 ist abgeschlossen (#1151 wird in T16 nur verifiziert). Der `artifact-path-guard` (T16) ist eine **neue** Datei und teilt nur die Datendatei, nicht den Code |

---

## 3. Klassen-Registry (verbindlich, aus Spec §2.4/§3.2)

### 3.1 14 Nicht-SE-Klassen

**12 persistent** (`artifactClass`/`artifactFileSet`):

| # | Klasse | Default `path` | `naming` | `kind` | `git` |
|---|---|---|---|---|---|
| 1 | `specs` | `docs/specs` | `{date}-{slug}.md` | — | tracked |
| 2 | `plans` | `docs/plans` | `{date}-{slug}.md` | — | tracked |
| 3 | `concepts` | `docs/concepts` | `{date}-{slug}.md` | — | tracked |
| 4 | `spikes` | `docs/spikes` | `{date}-issue-{n}-{topic}-spike.md` | — | tracked |
| 5 | `reviews` | `docs/reviews` | `{kind}-{date}-{slug}.md`; `kind: se` → `REVIEW_{date}_{scope}.md` | code, concept, domain, copyedit, proofread, se | tracked |
| 6 | `audits` | `docs/audits` | `{kind}-{date}-{slug}.md` | security, dependency, a11y, lifecycle, prompt, ai-security | tracked |
| 7 | `analysis` | `docs/analysis` | `{kind}-{date}-{slug}.md` | analysis, triage, perf, log, research, estimate, conclusion | tracked |
| 8 | `reports` | `docs/reports` (SE-Kontext: `{SE_ROOT}/reports/`, abgeleitet) | `{date}-{slug}.md`; `kind: vv` → `{date}-vv-{slug}.md` | vv | tracked |
| 9 | `adr` | `docs/adr` | `ADR-{nnn}_{slug}.md` (D3) | — | tracked |
| 10 | `traceability` | `docs/traceability` | `TRACE_{scope}.md` | — | tracked |
| 11 | `runbooks` | `docs/runbooks` | `{date}-{slug}.md` | — | tracked |
| 12 | `project-docs` | **Datei-Set**: `docs/ARCHITECTURE.md`, `docs/CODEBASE_OVERVIEW.md`, `docs/REQUIREMENTS.md`, `docs/issue-labels.md` | — (kein `naming`) | — | tracked |

`naming`-Werte folgen dem **Token-Kanon** aus Spec §3.2.1 (D3): geschlossene Token-Liste
`{class} {date} {slug} {kind} {n} {topic} {scope} {nnn} {level} {folder}`; ein unbekannter
oder klassen-fremder Token ist `artifact-locations.naming-invalid` (T5). Die Anzeigeform
`<YYYY-MM-DD>` bleibt ausschließlich in Rollen-Prosa (T10) und ist **kein** Konfigurationswert.
`naming` erzeugt **keine** Variable — die 54 Namen aus §3.3 bleiben unverändert.

**2 ephemer** (`artifactEphemeral`/`artifactState`):

| # | Klasse | Default `path` | `git` | `subdirs` | `retention` |
|---|---|---|---|---|---|
| 13 | `scratch` | `.tmp` | ignored | `logs`, `test-output`, `drafts` | manual |
| 14 | `state` | `.meta-viz` (`event-log: .meta-viz/events.jsonl`) | ignored | `progress`, `checkpoints`, `handoffs` | keep |

### 3.2 9 SE-Klassen (alle `path`-Default `SE`, `git: tracked`)

**D4 (DECIDED 2026-11-09):** Default bleibt `SE`, **keine** Migration. Der Regeltext
`rules/1-generic/se-cascade-artifact-taxonomy.md` verweist künftig auf `{{ARTIFACT_SE_ROOT}}`
(T20), und `docs/se/**` ist `legacy[]`-Muster — kein Default, kein zweiter Pfad.

| # | Klasse | Leaf-Muster | `subdir` | Producer (Beleg) |
|---|---|---|---|---|
| 1 | `se-requirements` | `L{level}_{FolderName}_Requirements.md` | `""` | `agents/1-generic/se-requirements.md:43,184`; `se-component-requirements.md:61,281` |
| 2 | `se-architecture` | `L{level}_{FolderName}_Architecture.md` | `""` | `se-architect.md:52,57,114` |
| 3 | `se-decomposition` | `L2_architectural_decomposition_iter-N.md` | `""` | `rules/1-generic/se-cascade-artifact-taxonomy.md:21-22` |
| 4 | `se-interfaces` | `L{level}_{FolderName}_Interfaces.md` | `""` | `se-interface-mgr.md:153` |
| 5 | `se-implementation` | `L{level}_{FolderName}_Impl.md` | `implementation` | `se-developer.md:188`; `se-senior-developer.md:144`; `se-junior-developer.md:171` |
| 6 | `se-testplan` | `L{level}_{FolderName}_TestPlan.md` | `validation` | `se-integration-and-test-manager.md:263` |
| 7 | `se-validation` | `L{level}_{FolderName}_Validation.md` | `validation` | `se-validator.md:177` |
| 8 | `se-verification` | `L{level}_{FolderName}_Verification.md` | `validation` | `se-verifier.md:191` |
| 9 | `se-decisions` | `L{level}_{FolderName}_Decisions.md` | `""` | `se-termination.md:154` |

`se-root` ist **keine** Klasse, sondern der Default-Wert der neun `path`-Felder
und der Träger von `{{ARTIFACT_SE_ROOT}}` (= Alias `{{SE_BASE_DIR}}`).
`reviews`, `adr`, `reports`, `traceability`, `state` sind **SE-global** (keine
eigene Zeile); `vv` ist `reports.kind: vv` (D-7). Die im Bestand belegten
SE-Pfade `{SE_BASE_DIR}/reviews/` und `{SE_BASE_DIR}/reports/`
(`se-critic.md:110,114`) bleiben über **abgeleitete** Projektions-Variablen
(`ARTIFACT_SE_REVIEWS_DIR`, `ARTIFACT_SE_REPORTS_DIR`, `ARTIFACT_SE_ADR_DIR`,
`ARTIFACT_SE_TRACEABILITY_DIR` = `{ARTIFACT_SE_ROOT}/<leaf>`) erhalten — kein
Config-Feld, keine 24. Klasse (RVW-1186-05).

### 3.2a `unmanaged[]` — Negativ-Deklaration, keine Klasse (D-8, RVW2-X-02)

Framework-Liste (read-only, additiv), **kein** Klassen-Eintrag, **keine** Variable, **kein**
Scaffold, **kein** `mode`:

| Pfad | Grund |
|---|---|
| `.meta-config/issue-labels-state.json` | Zustandsdatei, die **#1188** anlegt; #1186 kennt nur `project-docs` und den `.meta-viz`-`state` — ohne Deklaration wäre sie ein unklassifizierter Schreibpfad. Deshalb `unmanaged[]` (K1), **keine** `project-state`-Kategorie |
| `docs/api/**`, `docs/howto/**`, `docs/guides/**`, `docs/testing/**`, `docs/providers/**`, `docs/issues/**`, `docs/se-cascade/**` | bestehende Doku-Unterbäume ohne Artefakt-Klasse (OQ-6, F-3) |

Wirkung: kein `legacy-write`-Fund, kein Hook-Block/-Warn (auch unter `docs/**`, weil der
Hook `unmanaged` aus der Datendatei liest), keine Zählung in AC-1186-12.
**Nicht** unmanaged: `docs/issue-labels.md` (bleibt `project-docs.files.issue-labels`) und
`docs/superpowers/**`, `docs/conclusions/`, `docs/estimates/`, `docs/research/`, `SE/VV/**`
(bleiben `legacy[]`).

### 3.3 Variablen-Vertrag — die vollständige Menge (54 Namen, RVW-1186-02)

`check_builder_known_set` (`scripts/lib/consistency/placeholders.py:314-335`) macht aus jedem
nicht registrierten Builder-Output einen **ERROR**. Deshalb hier die exakte, gezählte Menge
(Vertrag = Spec §3.4; T6/T7 pinnen sie):

| Gruppe | # | Namen (Präfix `ARTIFACT_`) |
|---|---|---|
| `_DIR` Nicht-SE | 13 | `SPECS_DIR`, `PLANS_DIR`, `CONCEPTS_DIR`, `SPIKES_DIR`, `REVIEWS_DIR`, `AUDITS_DIR`, `ANALYSIS_DIR`, `REPORTS_DIR`, `ADR_DIR`, `TRACEABILITY_DIR`, `RUNBOOKS_DIR`, `SCRATCH_DIR`, `STATE_DIR` |
| `_DIR` SE-Klassen | 9 | `SE_REQUIREMENTS_DIR`, `SE_ARCHITECTURE_DIR`, `SE_DECOMPOSITION_DIR`, `SE_INTERFACES_DIR`, `SE_IMPLEMENTATION_DIR`, `SE_TESTPLAN_DIR`, `SE_VALIDATION_DIR`, `SE_VERIFICATION_DIR`, `SE_DECISIONS_DIR` |
| `_DIR` SE-Projektion (abgeleitet) | 4 | `SE_REVIEWS_DIR`, `SE_REPORTS_DIR`, `SE_ADR_DIR`, `SE_TRACEABILITY_DIR` |
| Wurzel | 1 | `SE_ROOT` (= Alias `SE_BASE_DIR`) |
| `_FILE` (`project-docs`) | 4 | `ARCHITECTURE_FILE`, `CODEBASE_OVERVIEW_FILE`, `REQUIREMENTS_FILE`, `ISSUE_LABELS_FILE` |
| `_MODE` (alle 23 Klassen) | 23 | `SPECS_MODE`, `PLANS_MODE`, `CONCEPTS_MODE`, `SPIKES_MODE`, `REVIEWS_MODE`, `AUDITS_MODE`, `ANALYSIS_MODE`, `REPORTS_MODE`, `ADR_MODE`, `TRACEABILITY_MODE`, `RUNBOOKS_MODE`, `SCRATCH_MODE`, `STATE_MODE`, `PROJECT_DOCS_MODE`, `SE_REQUIREMENTS_MODE`, `SE_ARCHITECTURE_MODE`, `SE_DECOMPOSITION_MODE`, `SE_INTERFACES_MODE`, `SE_IMPLEMENTATION_MODE`, `SE_TESTPLAN_MODE`, `SE_VALIDATION_MODE`, `SE_VERIFICATION_MODE`, `SE_DECISIONS_MODE` |
| **Summe** | **54** | 13 + 9 + 4 + 1 + 4 + 23 |

Zusatzregeln: `SE_BASE_DIR` bleibt als Alias registriert (`placeholders.py:89`);
`_UNREGISTERED_BUILDER_RATCHET` (`:275-284`) darf **nicht** wachsen (shrink-only);
`standalone.py` liefert dieselben 54 Namen mit Framework-Defaults (T6);
`unmanaged[]` (D-8) erzeugt **keine** Variable und keinen `_MODE`.
**D1:** `{{TMP_SINK_PATH}}` (`config.py:2046`) wird künftig **aus** `ARTIFACT_SCRATCH_DIR`
gespeist (`TMP_SINK_PATH == ARTIFACT_SCRATCH_DIR`); der Alias-Name `ARTIFACT_SCRATCH_PATH`
aus dem Entscheidungsprotokoll ist die Rollen-Variable `{{ARTIFACT_SCRATCH_DIR}}` — **kein**
55. Name. **D3:** `naming` erzeugt **keine** `_NAMING`-Variable.

---

## 4. Meilensteine (jeder einzeln grün lauffähig)

Jeder Meilenstein endet mit einem **Zwischentest-Gate**; kein Meilenstein
hängt von einem späteren ab.

| MS | Inhalt | Tasks | Gate (Befehl + Erwartung) |
|---|---|---|---|
| **M1** | Vertrag: Schema + Presets + `se_output`-Deklaration | T1–T3 | `pytest tests/test_artifact_locations_schema.py tests/test_artifact_locations_presets.py` grün; `python3 scripts/sync.py --validate` rc 0; `--dry-run` unverändert (keine neue ACTION-Zeile) |
| **M2** | Auflösung: Resolver, Validierung, Variablen, Scaffold, Alias-Warnungen | T4–T9 | `pytest tests/test_artifact_locations_{resolver,validate,variables,aliases}.py tests/test_artifact_scaffold.py` grün; `sync.py --dry-run` listet `{rel}/.gitkeep` je `files`-Klasse. **Schnitt (RVW2-1186-01):** das Scaffold-Gate enthält **nur** scaffold-lokale Assertions (Verzeichnis, `.gitkeep`, Marker-Konstante); alle `check_artifact_locations`-Fälle laufen in M4/T14 — M2 hängt nicht an einem späteren Modul |
| **M3** | Rollen-Contract: 26 Templates, Reviewer-Routing, Lazy-Rule | T10–T13 | `pytest tests/test_artifact_locations_templates.py` grün; `python3 scripts/consistency-check.py` ohne `artifact-locations.literal-path`; `grep -rn "/tmp/opencode" agents/ rules/` leer |
| **M4** | Durchsetzung: Consistency-Check, `--status-artifacts`, Hook, Containment-Hook auf Matrix | T14–T16, T24 | `pytest tests/test_consistency_artifact_locations.py tests/test_artifact_status_cli.py tests/test_artifact_path_guard_hook.py tests/test_repo_containment_scratch_resolution.py` grün (inkl. Baseline-, `unmanaged`- und Marker-Fällen); `sync.py --status-artifacts --json` Exit 0; `--validate` rc 0 |
| **M5** | Admin-UI: Whitelist-Eintrag, Write-Guard, Pane | T17–T19 | `pytest tests/test_admin_server.py tests/test_artifact_locations_admin_api.py tests/test_artifact_locations_admin_ui.py` grün; `PUT` mit `path: "../x"` ⇒ HTTP 400 mit Feldnamen; `consistency-check.py` ohne `docs.ui_help_mappings` |
| **M6** | Doku, Migration, Szenario | T20–T21, T23 | `pytest tests/test_artifact_locations_scenario.py tests/test_artifact_locations_migration.py` grün; `tests/scenarios/run.sh 99` PASS; voller Lauf `pytest -q` 0 failed; `sync.py --validate` rc 0; `sync.py --status-artifacts` Exit 0; `--migrate-artifact-aliases` ohne `--write` verändert keine Datei |

**T22 ist kein Meilenstein dieses PRs.** Die Whitelist-Ableitung (AC-07b) läuft als
Follow-up **nach #1141** (kanonische Reihenfolge, Spec §9) und wird hier nur spezifiziert,
damit die Vertragsform feststeht. In #1186 liefert T17 den handgepflegten Eintrag.

---

## 5. Bite-sized TDD-Tasks

**Einheitliche Abarbeitungs-Spine (gilt für T1–T21, T23, T24, Plan-Ledger-kompatibel):**

```markdown
- [ ] Step 1: Test zuerst schreiben (rot) — siehe „Test zuerst" des Tasks
- [ ] Step 2: Implementierung — siehe „Impl" des Tasks
- [ ] Step 3: Gate (grün) — siehe „Verifikation" des Tasks
- [ ] Step 4: Commit (Conventional Commits; `git`-Rolle bzw. Commit-Authority)
```

Jeder Task ersetzt die vier Platzhalter durch seine konkreten Namen/Assertions;
die Task-Abschnitte unten sind die ausformulierte Fassung dieser Spine.
Kein Task umfasst mehr als eine logische Änderung („bite-sized").

Legende: **Datei** = Ownership; **Test zuerst** = Testname + Assertion;
**Impl** = Signatur/Änderung; **Verifikation** = Befehl + Erwartung;
**Deps** = harte Vorbedingung; **Größe**.

### M1 — Vertrag

#### T1 — Schema-Sektion `artifact-locations` (AC-01)

**Datei:** Modify `config/project-config.schema.json`; Create `tests/test_artifact_locations_schema.py`
**Deps:** — · **Größe:** M

**Test zuerst** (alle `jsonschema`-Fälle mit `pytest.importorskip("jsonschema")`, Muster `tests/test_context_topology_schema.py:23,75`):

- `test_section_accepts_minimal_entry` — `{"artifact-locations": {"enabled": true}}` validiert.
- `test_unknown_section_subkey_rejected` — `{"artifact-locations": {"bogus": 1}}` ⇒ `ValidationError` (`additionalProperties: false`).
- `test_unknown_defaults_subkey_rejected` — `defaults: {"bogus": 1}` ⇒ Fehler.
- `test_unknown_class_subkey_rejected` — `classes.specs.bogus` ⇒ Fehler.
- `test_mode_enum_rejects_unknown_value` — `classes.specs.mode: "both"` ⇒ Fehler; `files`/`inline`/`off` akzeptiert (parametrisiert).
- `test_path_pattern_rejects_absolute_and_dotdot` — `"/abs"`, `"../x"`, `"a/../../b"`, `""` ⇒ Fehler; `"docs/specs"` akzeptiert.
- `test_se_class_subdir_is_single_segment` — `subdir: "a/b"` ⇒ Fehler; `""` und `"validation"` akzeptiert.
- `test_se_class_rejects_nested_subdir_key` — `classes["se-validation"].subdirs` ⇒ Fehler (Sonderformen sind ausgeschrieben, nicht `allOf`).
- `test_project_docs_requires_files` — `classes["project-docs"]: {}` ⇒ Fehler; mit `files.architecture` validiert.
- `test_ephemeral_rejects_mode_key` — `classes.scratch.mode: "off"` ⇒ Fehler (Spec §3.1 Form B hat kein `mode`).
- `test_legacy_is_string_array` — `legacy: [1]` und `legacy: "x"` ⇒ Fehler.
- `test_unmanaged_is_string_array` — `unmanaged: [1]` und `unmanaged: "x"` ⇒ Fehler; `unmanaged: ["docs/api/**"]` validiert (D-8/RVW2-X-02).
- `test_kind_is_closed_enum` — `classes.reviews.kind: ["bogus"]` ⇒ Fehler; `["code","concept"]` akzeptiert; Skalar `kind: "code"` ⇒ Fehler (AC-13-Präzisierung, Spec §3.1).
- `test_fallback_parent_enum_rejects_unknown_class` — `classes.reviews["fallback-parent"]: "bogus"` ⇒ Fehler; `"se-requirements"` akzeptiert (RVW-1186-04).
- `test_fallback_parent_rejected_on_ephemeral` — `classes.scratch["fallback-parent"]` ⇒ Fehler (Form `artifactEphemeral` hat kein `mode`).
- `test_project_docs_accepts_issue_labels` — `files: {"issue-labels": "docs/issue-labels.md"}` validiert; `files.bogus` ⇒ Fehler (OQ-6, #1188).
- `test_naming_accepts_canonical_tokens` — parametrisiert: `"{date}-{slug}.md"`, `"ADR-{nnn}_{slug}.md"`, `"{kind}-{date}-{slug}.md"`, `"{date}-issue-{n}-{topic}-spike.md"` validieren (D3).
- `test_naming_rejects_unknown_token` — `"{bogus}-{slug}.md"` ⇒ `ValidationError` (Schema-`pattern`, D3).
- `test_naming_rejects_path_separator_and_dotdot` — `"sub/{slug}.md"`, `"../{slug}.md"`, `""` ⇒ Fehler.
- `test_naming_rejects_angle_bracket_form` — `"<YYYY-MM-DD>-<slug>.md"` ⇒ Fehler (Anzeigeform ist **kein** Config-Wert; Migrationshinweis im semantischen Validator, T5).
- `test_artifact_naming_def_is_shared` — `$defs.artifactNaming.pattern` enthält alle zehn Token; `classes.specs.naming` und `classes["se-validation"].naming` referenzieren denselben `$defs`-Eintrag.

**Impl:** Neue Property `"artifact-locations"` direkt nach dem
`spec-plan-workflow`-Block (Einfügepunkt `schema.json:2223`-Umfeld, Block endet
`:2380`), vollständig mit `additionalProperties: false` auf **jeder**
Objektebene; `legacy` und `unmanaged` als `array of string` (D-8); **acht** `$defs`
(`artifactKind`, `artifactClassName`, `artifactNaming`, `artifactClass`, `artifactSeClass`,
`artifactFileSet`, `artifactEphemeral`, `artifactState`) am Block `schema.json:2855`.
`kind` ist ein `array` mit `items: {"$ref": "#/$defs/artifactKind"}` + `uniqueItems: true`
(geschlossenes 20-Werte-Enum, **kein** `array of string`); `fallback-parent` referenziert
`$defs/artifactClassName` (23 Klassen) in den drei Formen mit `mode`;
`naming` referenziert `$defs/artifactNaming` (Pattern mit geschlossener Token-Alternation,
D3; `defaults.naming` via `allOf` + `default`, weil draft-07 `$ref`-Geschwister ignoriert).
`path`-Pattern `^(?!/)(?!.*(^|/)\.\.(/|$)).+$`.

**Verifikation:** `python3 -m pytest tests/test_artifact_locations_schema.py -q` → 21 passed. `python3 scripts/sync.py --validate` → rc 0, keine neue Zeile (Sektion ist optional).

#### T2 — Preset-Datei (AC-15, §4.2)

**Datei:** Create `config/artifact-locations-presets.yaml`; Create `tests/test_artifact_locations_presets.py`
**Deps:** T1 · **Größe:** M

**Test zuerst:**

- `test_file_has_exactly_four_presets` — `set(presets) == {"default","minimal","flat","docs-only"}` (kein stiller Fallback; §4.2b).
- `test_default_preset_covers_all_23_classes` — `default.classes` enthält die 9 SE + 13 Verzeichnis-Klassen (project-docs als Datei-Set); Zähl-Assertion `14 + 9`.
- `test_every_preset_field_exists_in_schema` — jedes Feld jeder Klasse ist in `$defs` deklariert (F-2-Vorläufer auf Datenebene).
- `test_preset_does_not_restate_defaults` — `minimal`/`flat`/`docs-only` setzen nur Abweichungen, keine vollständige Kopie (Diff-Größe < `default`).
- `test_legacy_contains_framework_paths` — `docs/superpowers/specs`, `docs/superpowers/plans`, `docs/plans/audit-*.md`, `docs/specs/*-review.md`, `docs/conclusions/`, `docs/estimates/`, `docs/research/`, `.meta-viz/handoffs/**`, `docs/se/**` (**D4**), `docs/adr/[0-9][0-9][0-9][0-9]-*.md`, `docs/adr/ADR-[0-9][0-9][0-9]-*.md` (**D3**).
- `test_default_adr_naming_is_canonical` — `default.classes.adr.naming == "ADR-{nnn}_{slug}.md"`; die zwei Legacy-Formen liegen in `legacy[]`, **nicht** als zweiter Default (D3).
- `test_every_preset_naming_uses_canonical_tokens` — jedes `naming` in jedem Preset besteht ausschließlich aus Tokens der geschlossenen Liste (Spec §3.2.1); die `<TOKEN>`-Form macht den Test rot (D3).
- `test_default_unmanaged_contains_state_file` — `default.unmanaged` enthält `.meta-config/issue-labels-state.json` und die sieben Doku-Unterbäume aus §3.2a; `docs/issue-labels.md` ist **nicht** darin (D-8, RVW2-X-02).
- `test_preset_names_are_loadable_yaml` — `load_yaml_file` (Muster `scripts/lib/io.py`) liefert `version: 1`.

**Impl:** YAML mit Top-Level `version: 1`, `presets:` (Vorbild
`config/rules-presets.yaml:47`). `default` = Matrix aus §3 inkl. `unmanaged[]`
(§3.2a) sowie den beiden ADR-Legacy-Mustern und `docs/se/**` in `legacy[]`; `minimal` = nur
`specs`/`plans`/`reviews`/`audits` `files`, Rest `inline`; `flat` = alles
direkt unter `docs/`; `docs-only` = `scratch`/`state` ohne Pfad (ephemer
deaktiviert). Nur Feldnamen, die das Schema kennt; `naming` im Token-Kanon (D3).

**Verifikation:** `pytest tests/test_artifact_locations_presets.py -q` → 9 passed. Kein Sync-Effekt (Daten noch ungenutzt).

#### T3 — `se_output` im Schema deklarieren (Vorbereitung #1141)

**Datei:** Modify `config/project-config.schema.json`; Modify `tests/test_artifact_locations_schema.py`
**Deps:** T1 · **Größe:** S

**Test zuerst:**

- `test_se_output_is_declared` — `schema["properties"]["se_output"]["properties"]["base_dir"]["default"] == "SE"`; `deprecated is True`.
- `test_se_output_rejects_unknown_subkey` — `{"base_dir": "SE", "bogus": 1}` ⇒ Fehler.
- `test_se_output_base_dir_type` — `base_dir: 1` ⇒ Fehler.

**Impl:** `"se_output": {"type":"object","deprecated":true,"description":"Deprecated alias: use artifact-locations.classes.se-*.path (issue #1186).","properties":{"base_dir":{"type":"string","default":"SE"}},"additionalProperties":false}`.
Grund (belegt): heute schema-los (`grep` ohne Treffer; Wurzel
`additionalProperties: true`, `schema.json:2854`); ohne Deklaration bricht
#1141 Bestandsprojekte.

**Verifikation:** `pytest tests/test_artifact_locations_schema.py -q` → 24 passed; `sync.py --validate` rc 0.

---

### M2 — Auflösung

#### T4 — Resolver-Kern (AC-10, AC-12, AC-15, D-6, D-7) — **kritischster Task**

**Datei:** Create `scripts/lib/artifact_locations.py`; Create `tests/test_artifact_locations_resolver.py`
**Deps:** T1, T2 · **Größe:** XL

**Test zuerst:**

- `test_class_registry_has_23_entries` — `len(CLASS_REGISTRY) == 23`; 14 Nicht-SE (12 persistent + 2 ephemer) + 9 SE (AC-12).
- `test_precedence_project_beats_preset` — Projekt setzt `classes.reviews.path`, Preset etwas anderes ⇒ Projektpfad, `source == "project"`.
- `test_precedence_is_fieldwise` — Projekt setzt nur `path`, Preset `mode`/`git` ⇒ `path.source == "project"`, `mode.source == "preset:default"` (Regel 1).
- `test_project_defaults_beat_preset_defaults` — `defaults.naming` Projekt vs. Preset (Regel 2).
- `test_missing_field_falls_to_schema_default` — leere Sektion ⇒ `docs/specs`, `source == "schema-default"`.
- `test_project_preset_is_attribution_not_a_level` — Projekt setzt `preset: minimal`, Framework-Default ist `default` ⇒ `source == "project-preset:minimal"`; derselbe Datenzugriff ist die **Preset**-Wertequelle, nicht eine fünfte Stufe (K3).
- `test_code_fallback_is_reported` — Klasse ohne Schema-Default (z. B. `audits` vor Schema-Pflege) ⇒ `source == "code-fallback"` (Regel 3, kein stiller Default).
- `test_enabled_false_returns_disabled_source` — alle `source == "disabled"`, Pfade = heutige Werte (Regel 5).
- `test_unknown_preset_raises` — `unknown-preset` mit Code `artifact-locations.unknown-preset`.
- `test_legacy_is_additive` — Projekt ergänzt, Framework-Einträge bleiben; Projekt kann keinen entfernen (Regel 4).
- `test_se_validation_and_se_requirements_resolve_per_cell` — `se-validation.path = external-evidence`, `se-requirements.path = SE`; für dieselbe Zelle (`level=3`, `folder="Steuerung"`, `is_system=False`): `p_val.startswith("external-evidence/")`, `p_val.endswith("/validation/L3_Steuerung_Validation.md")`, `p_req.startswith("SE/")`, `p_req.endswith("/L3_Steuerung_Requirements.md")`; zusätzlich Assertion `p_val != p_req` (AC-10, ohne eine Zell-Hierarchie zu erfinden).
- `test_reports_vv_alias` — `reports.kinds` enthält `vv`; `legacy[]` enthält `SE/VV/**` (D-7).
- `test_reports_path_stays_docs_reports` — `classes.reports.path == "docs/reports"` (AC-04) **und** die SE-Projektion ist abgeleitet: `ARTIFACT_SE_REPORTS_DIR == "SE/reports"`, `ARTIFACT_SE_REVIEWS_DIR == "SE/reviews"`; ein `reports: {"se-path": …}` ist **Schema-Fehler** (kein zweiter Pfad, RVW-1186-05).
- `test_se_projection_is_derived_not_configured` — die vier Projektionen (`SE_REVIEWS`, `SE_REPORTS`, `SE_ADR`, `SE_TRACEABILITY`) folgen ausschließlich `ARTIFACT_SE_ROOT`; Änderung von `se-validation.path` verschiebt sie **nicht**.
- `test_kind_enum_is_class_scoped` — `reviews.kinds == 6 Werte`, `audits.kinds == 6`, `analysis.kinds == 7`, `reports.kinds == ("vv",)`, alle übrigen `kinds == ()`; ein `kind`-Wert außerhalb des Enums wirft `artifact-locations.kind-invalid`.
- `test_fallback_parent_is_exposed` — `classes.reviews.mode = "off"` + `fallback-parent: se-requirements` ⇒ `ResolvedClass.fallback_parent == "se-requirements"`; ohne Feld ⇒ `None` (Validator wirft erst in T5).
- `test_conclusions_is_legacy_not_class` — `"conclusions" not in classes`; `docs/conclusions/` in `legacy[]` (D-6).
- `test_scratch_path_is_single_source` — nur `classes.scratch.path` gesetzt ⇒ dieser Wert, `source == "project"`, `field_sources["path"] == "project"`; `repo_containment.tmp-sink.path` wird nicht gelesen (**D1**).
- `test_scratch_alias_applies_only_when_class_absent` — nur `repo_containment.tmp-sink.path` gesetzt ⇒ `classes.scratch.path` == Alias-Wert, `source == "project"`, `field_sources["path"] == "project-alias:repo_containment.tmp-sink.path"` (Attribution, **keine** fünfte Wertequelle, AC-15).
- `test_scratch_alias_equal_values_are_resolved` — beide Keys gesetzt, gleicher Wert ⇒ kein Fehler, Pfad aufgelöst, Attribution `project-alias:…` bleibt sichtbar.
- `test_se_root_default_is_SE` — alle neun `se-*.path` == `SE`; kein Default enthält `docs/se` (**D4**).
- `test_state_projects_progress_and_event_log` — `subdirs.progress == progress.dir`, `event-log == viz.event_log` (Projektion, kein zweiter Speicher).
- `test_backup_siblings_excluded_from_counts` — `*.sync-backup-*` zählt nicht in `file_count`/`newest` (#1195).
- `test_unmanaged_is_not_a_class` — `"unmanaged" not in matrix.classes`; `len(matrix.classes) == 23` bleibt (AC-12); `matrix.unmanaged` enthält `.meta-config/issue-labels-state.json` und ist additiv wie `legacy` (D-8).
- `test_naming_resolves_per_class` — `resolve_naming(matrix, "specs", date="2026-11-09", slug="x") == "2026-11-09-x.md"`; `adr` mit `n=7` ⇒ `ADR-007_slug.md` (3-stellig, D3); `reviews` mit `kind="code"` ⇒ `code-2026-11-09-x.md`; `se-validation` mit `level=3`, `folder="Steuerung"` ⇒ enthält `L3_Steuerung_Validation.md`.
- `test_naming_unknown_token_raises` — `naming: "{bogus}"` ⇒ `ArtifactLocationsError` mit Code `artifact-locations.naming-invalid` (D3).
- `test_naming_is_reported_per_class` — `ResolvedClass.naming` ist für alle 12 persistenten Klassen gesetzt und entspricht dem Default aus §3.1; `project-docs`/`scratch`/`state` haben `naming is None`.
- `test_legacy_accepts_adr_non_canonical_forms` — `matrix.legacy` enthält beide ADR-Muster (`NNNN-…`, `ADR-NNN-…`) und `docs/se/**` (D3/D4).

**Impl (Signaturen siehe §6):**
`CLASS_REGISTRY` (23 × `ClassSpec(name, form, default_path, naming, kinds, subdir)`),
`resolve_artifact_locations(config, agent_meta_root, project_root) -> ResolvedMatrix`
(mit `ResolvedMatrix.unmanaged: tuple[str, ...]`, D-8),
`ResolvedClass(name, path, mode, git, naming, archive, retention, kinds, subdir, subdirs, event_log, files, source, field_sources, fallback_parent)`,
`resolve_cell_path(name, level, folder, is_system) -> str`,
`resolve_se_projection(name) -> str` (4 abgeleitete Pfade, D-7),
`resolve_naming(matrix, name, *, kind=None, scope=None, **tokens) -> str` (Token-Validierung
+ Padding für `{nnn}`; wirft `artifact-locations.naming-invalid`, D3),
`resolve_scratch_path(config, classes) -> tuple[str, str]` (Pfad + Attribution
`project`/`project-alias:<key>`, D1),
`load_presets(agent_meta_root) -> dict`, `ArtifactLocationsError(code, message)`.
Resolver liest **nur** Config + Presets + Schema-Defaults (kein Dateisystem
außerhalb von `exists()`), wirft nie `sys.exit` (Doktrin wie
`repo_containment.resolve_*`), mutiert keine Eingabe — und ist auf dem **leeren**
Config-Dict total definiert (`derive_builder_vars`, `placeholders.py:299-306`).

**Verifikation:** `pytest tests/test_artifact_locations_resolver.py -q` → 28 passed. Kein Sync-Effekt.

#### T5 — Harte Config-Validierung (AC-11, §4.1)

**Datei:** Modify `scripts/lib/config.py`; Create `tests/test_artifact_locations_validate.py`
**Deps:** T4 · **Größe:** L

**Test zuerst** (Muster `_fail`/`SystemExit` wie `tests/test_repo_containment_validate.py`):

- `test_path_invalid_is_hard_error` — `path: "../x"` ⇒ Exit 1, Meldung enthält `artifact-locations.classes.<x>.path` und `must stay inside the project root`.
- `test_off_without_parent_is_hard_error` — `classes.reviews.mode: "off"` ohne `fallback-parent` und ohne Frontmatter-Senke ⇒ `artifact-locations.mode-parent-missing`, Meldung nennt den Feldnamen `fallback-parent` (RVW-1186-04).
- `test_off_with_fallback_parent_is_accepted` — `classes.reviews: {mode: "off", fallback-parent: "se-requirements"}` ⇒ kein Fehler.
- `test_fallback_parent_unknown_is_hard_error` — `fallback-parent: "bogus"` (am Schema vorbei konstruiert) ⇒ `artifact-locations.fallback-parent-unknown`.
- `test_kind_outside_enum_is_hard_error` — `classes.analysis.kind: ["bogus"]` ⇒ `artifact-locations.kind-invalid` (Validator prüft unabhängig vom `jsonschema`-Pfad, AC-13-Präzisierung).
- `test_off_with_frontmatter_sink_is_accepted` — `se-critic`-Senke (`review_state`) ⇒ kein Fehler.
- `test_se_requirements_off_with_active_cascade_is_hard_error` — `systems-engineering.enabled: true` + `se-requirements.mode: "off"` ⇒ `artifact-locations.se-required-off`, Meldung nennt `se-decomposition` als erlaubte Alternative (AC-11).
- `test_se_requirements_off_without_cascade_is_accepted` — Kaskade aus ⇒ kein Fehler.
- `test_se_decomposition_off_is_accepted` — AC-11 wörtlich.
- `test_subdir_invalid_is_hard_error` — `subdir: "a/b"`, `".."` ⇒ `artifact-locations.subdir-invalid`.
- `test_unknown_preset_is_hard_error` — `preset: "nope"` ⇒ Meldung nennt den Namen.
- `test_legacy_intersect_is_hard_error` — `legacy: ["docs/specs"]` bei aktivem `specs.path = docs/specs` ⇒ `artifact-locations.legacy-intersect`.
- `test_unmanaged_intersect_is_hard_error` — `unmanaged: ["docs/specs"]` bei aktivem `specs.path = docs/specs` ⇒ `artifact-locations.unmanaged-intersect` (D-8, RVW2-X-02).
- `test_validation_runs_even_when_enabled_false` — Strukturprüfung immer (Muster `_validate_repo_containment:798-803`); nur `se-required-off` ist kaskadenabhängig.
- `test_validation_is_called_by_validate_config` — `_validate_config` (`config.py:635`) ruft `_validate_artifact_locations` **nach** `_validate_repo_containment` (`:669`) und **vor** `_validate_subagent_permissions` (`:670`); AST-Assertion auf die Aufrufreihenfolge.
- `test_scratch_sink_divergence_is_hard_error` — `classes.scratch.path: "sink-a"` + `repo_containment.tmp-sink.path: "sink-b"` ⇒ Exit 1, Code `artifact-locations.scratch-sink-divergence`, Meldung nennt **beide** Keys und den Reparaturschritt (D1).
- `test_scratch_alias_equal_values_pass_validation` — beide Keys gleich ⇒ kein Fehler; `repo_containment`-Strukturprüfung (`config.py:888-937`) bleibt unberührt (D1).
- `test_scratch_class_only_passes_validation` — nur `classes.scratch.path` ⇒ kein Fehler (die Warnungsfreiheit prüft T9, nicht der Validator) (D1).
- `test_naming_unknown_token_is_hard_error` — `classes.specs.naming: "{bogus}-{slug}.md"` ⇒ `artifact-locations.naming-invalid`, Meldung listet die erlaubten Tokens (D3).
- `test_naming_token_not_applicable_is_hard_error` — `classes.audits.naming: "{level}-{slug}.md"` ⇒ `naming-invalid`; `classes.adr.naming: "{nnn}-{slug}.md"` ⇒ akzeptiert (D3).

**Impl:** `_validate_artifact_locations(config, config_path, agent_meta_root) -> None`
mit lokalem `_fail` (Muster `config.py:808-810`); Aufruf in `_validate_config`
(`config.py:635`) zwischen `_validate_repo_containment` (`:669`) und
`_validate_subagent_permissions` (`:670`). Fehlercodes exakt aus Spec §4.1
(**11** Codes: inkl. `fallback-parent-unknown`, `kind-invalid`, `unmanaged-intersect`,
`scratch-sink-divergence` und `naming-invalid`).
Reihenfolge: Struktur → `kind` → `naming` (Token + Klassen-Anwendbarkeit) → Modus +
`fallback-parent` → SE-Startkritik → Subdir → Preset → Scratch-Alias-Gleichheit →
Legacy-Schnitt → Unmanaged-Schnitt. Die Scratch-Divergenz ist **hart** (D1) — sie
verhindert zwei Schreibziele für dieselbe Senke und läuft deshalb auch bei
`enabled: false` (Strukturprüfung, Muster `_validate_repo_containment:798-803`).

**Verifikation:** `pytest tests/test_artifact_locations_validate.py -q` → 20 passed; `sync.py --validate` rc 0; `sync.py --dry-run` rc 0.

#### T6 — Variablen-Export (AC-02, AC-14, H-2)

**Datei:** Modify `scripts/lib/config.py`; Modify `scripts/lib/standalone.py`; Create `tests/test_artifact_locations_variables.py`
**Deps:** T4 · **Größe:** M

**Test zuerst:**

- `test_artifact_variable_count_is_54` — `{k for k in variables if k.startswith("ARTIFACT_")}` hat exakt **54** Einträge (13 DIR + 9 `SE_*_DIR` + 4 Projektionen + `SE_ROOT` + 4 `_FILE` + 23 `_MODE`; RVW-1186-02).
- `test_all_dir_variables_exported` — 13 `_DIR` (`SPECS, PLANS, CONCEPTS, SPIKES, REVIEWS, AUDITS, ANALYSIS, REPORTS, ADR, TRACEABILITY, RUNBOOKS, SCRATCH, STATE`) + 9 `SE_*_DIR` + `ARTIFACT_SE_ROOT` vorhanden, ohne Trailing-Slash.
- `test_se_projection_variables_exported` — `ARTIFACT_SE_REVIEWS_DIR`, `ARTIFACT_SE_REPORTS_DIR`, `ARTIFACT_SE_ADR_DIR`, `ARTIFACT_SE_TRACEABILITY_DIR` = `f"{SE_ROOT}/<leaf>"` (D-7).
- `test_mode_variables_exported` — `ARTIFACT_<KLASSE>_MODE` für **alle 23** Klassen; Wert aus der Matrix (`files|inline|off`).
- `test_ephemeral_mode_is_files_constant` — `ARTIFACT_SCRATCH_MODE == ARTIFACT_STATE_MODE == "files"` (Schema-Form hat kein `mode`, K-1).
- `test_file_set_variables_exported` — `ARTIFACT_ARCHITECTURE_FILE`, `ARTIFACT_CODEBASE_OVERVIEW_FILE`, `ARTIFACT_REQUIREMENTS_FILE`, `ARTIFACT_ISSUE_LABELS_FILE` (`docs/issue-labels.md`, OQ-6).
- `test_se_base_dir_is_alias` — `variables["SE_BASE_DIR"] == variables["ARTIFACT_SE_ROOT"]` und beide aus demselben Resolver-Ergebnis (Genau eine Quelle).
- `test_builder_is_total_on_empty_config` — `_build_artifact_variables({}, …)` liefert alle 54 Schlüssel ohne Exception und ohne `project_root` (`derive_builder_vars`-Vertrag, `placeholders.py:299-306`).
- `test_standalone_supplies_artifact_variables` — `render_standalone_agent("developer", …)` enthält **kein** `{{ARTIFACT_` mehr und keine „not available"-Notiz; `standalone._standalone_variables` liefert alle 54 Namen mit Framework-Defaults (`docs/*`, `.tmp`, `.meta-viz`, `files`).
- `test_reference_agent_placeholders_remain_escaped` — `agents/1-generic/_reference-agent.md` enthält nach dem Lauf weiterhin `{{%…%}}`-Formen und keine ungeschützte `ARTIFACT_`-Variable (Kollisionsbehandlung; Escape-Konvention `placeholders.py:294-295`).
- `test_variables_built_once_per_provider` — `build_variables` wird pro Provider einmal aufgerufen; AST-Assertion: `_build_artifact_variables` hat genau **einen** Aufruf in `scripts/lib/config.py`.

**Impl:** `_build_artifact_variables(variables, config, agent_meta_root, project_root) -> None`;
Aufruf **zwischen** `_build_platform_variables` (`config.py:2770`) und
`_build_dod_variables` (`config.py:2771`) — dort ist `SE_ENABLED`
(`:2269`) gesetzt, und `SE_BASE_DIR` (`:2270-2273`) wird aus dem Resolver
überschrieben (Alias, nicht Zweitquelle). Kein Provider-Branch.
`standalone._standalone_variables` (`:295-336`) erhält einen Block
`_ARTIFACT_FALLBACKS` mit denselben 54 Namen und Framework-Defaults
(kein Projekt-Config vorhanden ⇒ Default-Matrix, Modus `files`).

**Verifikation:** `pytest tests/test_artifact_locations_variables.py -q` → 11 passed; `PYTHONPATH=scripts python3 -c "from pathlib import Path; from lib.config import build_variables, load_config; v,_=build_variables(load_config(Path('.meta-config/project.yaml')), Path('.')); print(v['ARTIFACT_SPECS_DIR'], len([k for k in v if k.startswith('ARTIFACT_')]))"` → `docs/specs 54`.

#### T7 — Platzhalter-Allow-List (AC-08-Vorläufer, §4.7)

**Datei:** Modify `scripts/lib/consistency/placeholders.py`; Create `tests/test_artifact_locations_placeholders.py`
**Deps:** T6 · **Größe:** S

**Test zuerst:**

- `test_builder_vars_are_all_registered` — `derive_builder_vars(agent_meta_root) <= _BUILTIN_VARS` (RVW-1186-02: genau der Vertrag, den `check_builder_known_set` erzwingt).
- `test_all_54_artifact_names_registered` — die Menge aus Spec §3.4 steht vollständig in `_BUILTIN_VARS` (Block ab `placeholders.py:12`).
- `test_every_artifact_placeholder_in_templates_is_registered` — jedes im Repo verwendete `{{ARTIFACT_*}}` ist in `_BUILTIN_VARS` (Richtung Template → Allow-List).
- `test_no_entry_added_to_unregistered_ratchet` — `_UNREGISTERED_BUILDER_RATCHET` (`:275-284`) ist unverändert (shrink-only; neue Namen gehören in `_BUILTIN_VARS`).
- `test_check_builder_known_set_is_green` — `check_builder_known_set(agent_meta_root)` liefert kein `placeholders.builder-known-set`-Finding.

**Impl:** **54** Namen explizit in `_BUILTIN_VARS` (nicht als Regex-Familie —
`placeholders.py:274` verlangt Registrierung; Familien sind für dynamische
Mengen reserviert). **Kein** „jedes deklarierte wird verwendet"-Test (Spec §4.7):
die Menge ist der Registry-Vertrag, nicht die Schnittmenge mit den heute
umgestellten Templates.

**Verifikation:** `pytest tests/test_artifact_locations_placeholders.py -q` → 5 passed; `python3 scripts/consistency-check.py` ohne `placeholders.*`-Finding.

#### T8 — Scaffold-Verallgemeinerung (AC-02, AC-04, D-6)

**Datei:** Create `scripts/lib/artifact_scaffold.py`; Modify `scripts/lib/spec_plan_scaffold.py`; Modify `scripts/lib/sync_pipeline.py`; Modify `tests/test_spec_plan_scaffold.py`; Create `tests/test_artifact_scaffold.py`
**Deps:** T4 · **Größe:** L

**Test zuerst:**

- `test_files_mode_creates_directory_and_gitkeep` — für `specs`, `plans`, `concepts`, `spikes`, `reviews`, `audits`, `analysis`, `reports`, `adr`, `traceability`, `runbooks` (11) existiert `<path>/.gitkeep` nach dem Lauf.
- `test_ignored_classes_get_no_gitkeep` — `scratch`, `state` erhalten kein `.gitkeep` (gitignored).
- `test_legacy_conclusions_dir_is_scaffolded_without_class` — `docs/conclusions/.gitkeep` existiert, `classes` enthält **keine** `conclusions` (D-6).
- `test_marker_filenames_constant_covers_scaffold_markers` — `artifact_scaffold.MARKER_FILENAMES == frozenset({".gitkeep", ".gitignore", ".keep"})`; die Konstante ist importierbar, damit T14/T16 **dieselbe** Quelle nutzen (RVW2-1186-01). **Kein** `check_artifact_locations`-Aufruf in dieser Datei — das Modul entsteht erst in T14.
- `test_dry_run_writes_nothing` — `dry_run=True`: keine Datei, aber `log.action("CREATE", …)` je Klasse (AC-02 wörtlich).
- `test_second_run_is_idempotent` — zweiter Lauf meldet `unchanged`, kein doppeltes `.gitkeep`.
- `test_wrapper_keeps_old_behaviour` — `scaffold_spec_plan_dirs` bleibt importierbar und scaffoldet bei `spec-plan-workflow.enabled` dieselben drei Verzeichnisse (Regression `sync_pipeline.py:152`, `knowledge.py:12`).
- `test_disabled_matrix_falls_back_to_legacy_scaffold` — `enabled: false` ⇒ genau das heutige Scaffold (3 Verzeichnisse).

**Impl:** `scaffold_artifact_dirs(agent_meta_root, project_root, config, log, dry_run) -> None`
nutzt `safe_path` (`io.py:663`) + `write_checked` (`io.py:467`) wie
`spec_plan_scaffold.py:54-61`; Aufruf in `_sync_stage_knowledge_and_isolation`
(`sync_pipeline.py:1699`) **zusätzlich** zum Wrapper (Wrapper bleibt für
Rückwärtskompatibilität). `mode: inline|off` ⇒ kein Verzeichnis. Der
Legacy-Marker (`docs/conclusions/.gitkeep`, D-6) wird geschrieben, ist aber über
`MARKER_FILENAMES = frozenset({".gitkeep", ".gitignore", ".keep"})` von der
Legacy-Erkennung ausgenommen (dieselbe Konstante nutzt T14). Die
`legacy-write`-Erkennung selbst lebt in T14 (RVW2-1186-01) — T8 importiert
`consistency.artifact_locations` nicht.

**Verifikation:** `pytest tests/test_artifact_scaffold.py tests/test_spec_plan_scaffold.py -q` → grün; `python3 scripts/sync.py --dry-run | grep -c "artifact scaffolding"` → 12 (11 Klassen + `docs/conclusions`).

#### T9 — Alias-/Deprecation-Warnungen (§3.6)

**Datei:** Modify `scripts/lib/config.py`; Create `tests/test_artifact_locations_aliases.py`
**Deps:** T4, T5 · **Größe:** S

**Test zuerst:**

- `test_spec_plan_paths_divergence_warns_once` — `spec-plan-workflow.paths.specs = "docs/specs-old"` vs. Matrix ⇒ genau **eine** WARN, Text nennt Ziel-Key.
- `test_spec_plan_paths_equal_produces_no_warning` — identische Werte ⇒ still.
- `test_se_output_divergence_warns` — `se_output.base_dir: "docs/se"` vs. `SE` ⇒ WARN mit Ziel-Key.
- `test_scratch_alias_is_attribution_not_a_level` — nur `repo_containment.tmp-sink.path` gesetzt ⇒ `field_sources["path"] == "project-alias:repo_containment.tmp-sink.path"`, `source` bleibt `"project"`; die Zahl der **Wertequellen** bleibt vier (D1, AC-15).
- `test_scratch_deprecation_warning_has_migration_hint` — genau **eine** WARN; Text nennt Ziel-Key `artifact-locations.classes.scratch.path`, das Wort `deprecated` und den Befehl `--migrate-artifact-aliases` (D1).
- `test_scratch_class_only_produces_no_warning` — nur `classes.scratch.path` ⇒ still (Migrationsziel erreicht).
- `test_scratch_both_equal_warns_once_about_removal` — beide Keys gleich ⇒ **eine** WARN („entferne `repo_containment.tmp-sink.path`"), kein Fehler (der Fehlerfall liegt in T5).
- `test_tmp_sink_path_variable_comes_from_matrix` — `variables["TMP_SINK_PATH"] == variables["ARTIFACT_SCRATCH_DIR"]`, beide aus **einem** Resolver-Ergebnis; `config.py:2046` liest keinen zweiten Pfad (D1).
- `test_state_divergence_warns` — `progress.dir` ≠ `state.subdirs.progress` ⇒ WARN.
- `test_disabled_matrix_suppresses_deprecation_warnings` — `enabled: false` ⇒ `paths`/`se_output` bleiben alleinige Quelle, keine Warnung.

**Impl:** `_artifact_deprecation_warnings(config, agent_meta_root, project_root) -> list[Finding]`
in `scripts/lib/config.py` (nutzt `consistency.report.Finding`, `report.py:22-29`);
einmalige Ausgabe über den bestehenden `warn_sink` (`unmapped`/`pre_warnings`)
in `build_variables`. Kein `sys.exit` für Warnungen. **D1:** `TMP_SINK_PATH` wird nach der
Matrix-Auflösung gesetzt (`variables["TMP_SINK_PATH"] = variables["ARTIFACT_SCRATCH_DIR"]`),
nicht mehr aus `REPO_CONTAINMENT_TMP_PATH` (`config.py:2046`) — der Aliasing-Pfad ist damit
einseitig (Matrix → Laufzeitvariable).

**Verifikation:** `pytest tests/test_artifact_locations_aliases.py -q` → 10 passed; `sync.py --dry-run` zeigt bei divergenter Test-Fixture genau eine Warnzeile.

---

### M3 — Rollen-Contract

#### T10 — 11 Nicht-SE-Rollen-Templates (AC-03, AC-13)

**Datei:** Modify `agents/1-generic/{ideation,planner,requirements,documenter,knowledge-migrator,concept-reviewer,copyeditor,proofreader,effort-estimator,explorer}.md` (10 Dateien, 11 Rollen-Fälle); Create `tests/test_artifact_locations_templates.py`
**Deps:** T6, T7 · **Größe:** L

**Test zuerst:**

- `test_no_literal_managed_path_in_write_position` — parametrisiert über die 10 Dateien: kein aktiver Klassenpfad (`docs/specs`, `docs/plans`, `docs/spikes`, `docs/concepts`, `docs/reviews`, `docs/audits`, `docs/analysis`, `docs/reports`, `docs/adr`, `docs/traceability`, `docs/runbooks`), kein `docs/CODEBASE_OVERVIEW.md`, `plan-<topic>.md`, `concept-<topic>.md`, `docs/REQUIREMENTS.md` als Literal **in Schreibposition**; stattdessen `{{ARTIFACT_*}}` (RVW-1186-06).
- `test_read_ok_ratchet_is_exactly_two_lines` — exakt **zwei** Zeilen im Repo tragen `<!-- artifact-read-ok -->` (`knowledge-migrator.md:39`, `:50`); jede weitere Zeile ist rot (shrink-only, Vorbild `placeholders.py:275-284`).
- `test_ideation_uses_concepts_dir` — `ideation.md` (Zeile 97 heute) enthält `{{ARTIFACT_CONCEPTS_DIR}}`.
- `test_planner_uses_plans_dir` — `planner.md` (Zeile 75 heute) enthält `{{ARTIFACT_PLANS_DIR}}`, kein `project root`.
- `test_documenter_uses_analysis_and_project_docs` — Conclusion-Ziel `{{ARTIFACT_ANALYSIS_DIR}}/conclusion-…` (D-6), Datei-Set `{{ARTIFACT_ARCHITECTURE_FILE}}`/`{{ARTIFACT_CODEBASE_OVERVIEW_FILE}}` (`documenter.md:131-132`).
- `test_documenter_archive_target_uses_plans_dir` — `documenter.md:81` enthält `{{ARTIFACT_PLANS_DIR}}/archive`, kein `docs/plans/archive` (RVW-1186-06).
- `test_copyedit_and_proofread_use_reviews_dir` — kein „next to the reviewed file" (`copyeditor.md:92`, `proofreader.md:89`).
- `test_effort_estimator_has_defined_target` — `effort-estimator.md:116` nennt `{{ARTIFACT_ANALYSIS_DIR}}` mit `kind: estimate` (AC-13).
- `test_explorer_uses_spikes_dir` — `explorer.md:71` variablenbasiert.
- `test_fallback_mentions_inline_mode` — jede Rolle mit `_MODE`-Bezug nennt das `inline`-Verhalten (Datei entfällt, Volltext im Rückkanal).

**Impl:** Pfad-Literale durch Variablen ersetzen, Satzbau beibehalten
(keine Instruction-Bleed-Änderung); Naming-Beispiele bleiben als
`<YYYY-MM-DD>-<slug>.md`-Muster erhalten. `knowledge-migrator.md:39,50`
behalten ihre Lese-Literale und bekommen den Ratchet-Marker
`<!-- artifact-read-ok -->` (Spec §4.6).

**Verifikation:** `pytest tests/test_artifact_locations_templates.py -q` → 10 passed;
`grep -rnE "docs/(specs|plans|spikes|concepts|reviews|audits|analysis|reports|adr|traceability|runbooks)" agents/1-generic/*.md | grep -v "artifact-read-ok" | grep -v "_reference-agent"` → 0 Treffer.

#### T11 — 12 SE-Rollen-Templates + F-1-Klammerform (AC-03, AC-10) — **kritisch**

**Datei:** Modify `agents/1-generic/{se-requirements,se-component-requirements,se-architect,se-interface-mgr,se-developer,se-senior-developer,se-junior-developer,se-integration-and-test-manager,se-validator,se-verifier,se-termination,se-critic}.md`
**Deps:** T6 · **Größe:** L

**Test zuerst** (in `tests/test_artifact_locations_templates.py`):

- `test_no_single_brace_se_token` — `grep -rn "{SE_" agents/1-generic` → 0 Treffer (F-1: heute 16 Vorkommen in 12 Dateien; nur `{{SE_BASE_DIR}}` ist substituierbar, `placeholders.py:89`).
- `test_each_se_role_uses_its_class_variable` — parametrisiert: `se-requirements` → `ARTIFACT_SE_REQUIREMENTS_DIR`, `se-validator` → `ARTIFACT_SE_VALIDATION_DIR`, `se-developer`/`se-senior-developer`/`se-junior-developer` → `ARTIFACT_SE_IMPLEMENTATION_DIR` (mit `subdir` `implementation`).
- `test_leaf_naming_preserved` — die Matrix-Naming-Muster (§3.2) stehen in jedem Template (kein Rollen-eigenes Naming).
- `test_protocol_path_uses_se_reviews_projection` — `se-critic.md:110` → `{{ARTIFACT_SE_REVIEWS_DIR}}/REVIEW_<YYYY-MM-DD>_<scope>.md`; kein `docs/reviews` (D-7, RVW-1186-05).
- `test_critic_report_uses_se_reports_projection` — `se-critic.md:114` → `{{ARTIFACT_SE_REPORTS_DIR}}/{FolderName}/L{level}_{FolderName}_{review_target}_critic_report.md`; `reports.path` bleibt `docs/reports`.
- `test_atomic_write_uses_scratch_dir` — `{{TMP_SINK_PATH}}` bleibt für Zwischenstände (`se-architect.md:116`, `se-critic.md:120`), Ziel ist die Klassen-Variable; keine Doppelsenke.

**Impl:** `{SE_BASE_DIR}/{parent_path}/…` → `{{ARTIFACT_SE_<KLASSE>_DIR}}/{parent_path}/…` (bzw. `{{ARTIFACT_SE_ROOT}}` für ADR/Reports/Traceability). Die Zell-Hierarchie (`L{n}`, `System`/`Component`) bleibt unverändert (Spec §3.1 „nicht verhandelbar").

**Verifikation:** `pytest tests/test_artifact_locations_templates.py -q` → grün; `python3 scripts/sync.py --dry-run` ohne unersetzten `{{ARTIFACT_`-Token im gerenderten Output (`--only-variables`-Kontrolle).

#### T12 — Reviewer-Routing (Reviews/Audits) (§3.6, AC-03)

**Datei:** Modify `config/routing/reviewers.yaml`; Modify `agents/1-generic/{security-auditor,ai-security-guardian,app-lifecycle-governor,prompt-governor}.md`
**Deps:** T6 · **Größe:** S

**Test zuerst** (in `tests/test_artifact_locations_templates.py`):

- `test_reviewers_notes_reference_matrix` — `reviewers.yaml:23-29` enthält `{{ARTIFACT_REVIEWS_DIR}}`, kein `{{TMP_SINK_PATH}}`, kein „tmp sink".
- `test_auditor_reports_go_to_audits_dir` — 4 Rollen nennen `{{ARTIFACT_AUDITS_DIR}}` (`kind` je Rolle) statt tmp-Sink; `app-lifecycle-governor.md:100` als Regressionsanker.
- `test_audit_kind_matches_role` — `security-auditor` → `security`, `ai-security-guardian` → `ai-security`, `app-lifecycle-governor` → `lifecycle`, `prompt-governor` → `prompt`.
- `test_ephemeral_evidence_still_uses_scratch` — Roh-Evidenz (Logs, lange Tool-Ausgaben) bleibt `{{TMP_SINK_PATH}}`; nur das **Artefakt** wandert.

**Impl:** `notes`-Satz umschreiben (Test-Fixture, kein Renderer, vgl.
`docs/plans/2026-10-24-tmp-sink-injection-plan.md` Task 5); Rollen-Templates:
Report-Ziel + Rückkanal.

**Verifikation:** `pytest tests/test_artifact_locations_templates.py -q` grün; `grep -n "tmp sink" config/routing/reviewers.yaml` → 0.

#### T13 — Eine Lazy-Rule + Pointer-Tabelle (H-1, H-3, AC-16)

**Datei:** Create `rules/1-generic/artifact-locations.md`; Modify `config/rules-presets.yaml`; Modify `rules/1-generic/use-lazy-rules.md`
**Deps:** T10, T11; **#1180-Mechanik für die generierte Tabelle** · **Größe:** M

**Test zuerst:**

- `test_artifact_rule_is_lazy_in_lazy_preset` — `rules-presets.yaml` `lazy.artifact-locations.channel == "skill"` und `skill-description` gesetzt (Muster `:110-132`).
- `test_no_always_on_rule_added` — im `rules-preset: lazy`-Fixture liefert `resolve_rules(...)` die Rule **nicht** im eingebetteten Set und erzeugt `.claude/rules/artifact-locations.md` **nicht**; Mengen-Assertion „eingebettete Regelnamen ∩ generierte `rules_dir`-Dateien = ∅" (AC-16). Idiom/Imports aus `tests/test_lazy_skills_channel.py:30-36` (`lib.rules.resolve_rules`, `rule_opts_lazy_channel`, `lib.rule_channels.lazy_skill_channel`).
- `test_rule_lists_all_23_classes` — die Tabelle in `artifact-locations.md` enthält 23 Klassennamen + `mode`-Semantik (`files|inline|off`).
- `test_pointer_table_entry_present` — `use-lazy-rules.md:5-21` enthält `artifact-locations`. **Zwei Zustände:** (#1180 gemergt) Eintrag wird generiert und der Test prüft die generierte Quelle; (#1180 offen) Eintrag manuell, Test mit `pytest.mark.skipif` + Begründung „#1180 ersetzt Handpflege durch Generierung" — **kein** stiller `xfail`.
- `test_provider_context_count_does_not_grow` — **relative** Assertion: `count({{PROJECT_CONTEXT}})` über `agents/1-generic/*.md` und Gesamtzahl der Rollen-Templates sind nach der Änderung **unverändert** (H-4). Die absolute Zahl wird bewusst **nicht** gepinnt: das Issue nennt „70/98", HEAD hat **83/98** (84 von 101 Dateien, `docs/specs/2026-11-09-project-context-injection-scope-spec.md:43`) — RVW2-1186-03.

**Impl:** Rule-Body (deutsch, wie `rules/1-generic/*`), Sektion in
`config/rules-presets.yaml` unter `lazy:`; Pointer-Zeile. Der Body enthält
**keine** Pfad-Literale, sondern die Variablen-Tabelle.

**Verifikation:** `pytest tests/test_artifact_locations_templates.py -q` grün; `python3 scripts/sync.py --dry-run` erzeugt `.claude/skills/artifact-locations/SKILL.md` (Hinweiszeile im Log) und keine neue always-on-Rule.

---

### M4 — Durchsetzung

#### T14 — Consistency-Check (AC-08, AC-09, AC-13)

**Datei:** Create `scripts/lib/consistency/artifact_locations.py`; Modify `scripts/consistency-check.py`; Create `tests/test_consistency_artifact_locations.py`
**Deps:** T4, T10, T11 · **Größe:** L

**Test zuerst:**

- `test_literal_path_in_write_position_is_violation` — Template mit `docs/specs/foo.md` in einer Schreibzeile ⇒ Severity ERROR/Violation, Code `artifact-locations.literal-path`, Datei+Zeile.
- `test_read_ok_marker_exempts_scan_line` — `docs/adr/` in einer Zeile **mit** `<!-- artifact-read-ok -->` ⇒ kein Finding; dieselbe Zeile ohne Marker ⇒ Finding (RVW-1186-06).
- `test_read_ok_ratchet_does_not_grow` — die Anzahl markierter Zeilen im Repo ist `<= 2` (Bestand: `knowledge-migrator.md:39,50`); eine dritte ⇒ Finding.
- `test_literal_path_ignores_escaped_reference_agent` — `_reference-agent.md`-Escapes lösen nicht aus.
- `test_legacy_write_is_warning_reported_once` — Datei unter `legacy[]`, die **nicht** in `baseline.legacy_files` steht ⇒ **eine** WARNING, nichts gelöscht, keine zweite Meldung im selben Lauf (AC-09, RVW2-1186-02).
- `test_legacy_write_uses_baseline_not_mtime` — Datei mit **alter** mtime, aber nicht in der Baseline ⇒ Finding; Datei **in** der Baseline, auch mit frischer mtime ⇒ **kein** Finding. Der Test setzt die Baseline-Datei selbst (`tmp_path`), kein mtime-Vergleich (RVW2-1186-02).
- `test_baseline_missing_fails_open` — `.meta-config/artifact-locations.resolved.json` fehlt oder hat keinen `baseline`-Key ⇒ **0** Findings + genau **eine** Warnzeile auf stderr, kein neuer Check-Code.
- `test_unmanaged_is_never_reported` — `.meta-config/issue-labels-state.json` und `docs/api/x.md` lösen keinen der fünf Checks aus (D-8, RVW2-X-02).
- `test_legacy_marker_files_are_never_reported` — `.gitkeep` in `docs/conclusions/` ⇒ kein Finding; eine dort abgelegte `.md` ⇒ WARNING (Scaffold-Ausnahme, §3.5; RVW-1186-01).
- `test_clean_repo_sync_produces_no_legacy_write` — frischer Sync auf leerem Projekt + `check_artifact_locations(...)` ⇒ **0** `legacy-write` (AC-09-Gate, Baseline-basiert).
- `test_legacy_markers_produce_no_legacy_write` — vollständiger Scaffold auf leerem Projekt (inkl. `docs/conclusions/.gitkeep`, aus T8) ⇒ **0** `legacy-write`-Funde (AC-09-Präzisierung, RVW-1186-01) — **hier**, nicht in T8.
- `test_inline_with_path_promise_is_violation` — `mode: inline` + `**Output file:**`/`Persisted to:`/`ARTIFACTS: <path>` im Template ⇒ Violation.
- `test_missing_dir_is_info` — `mode: files` + fehlendes Verzeichnis ⇒ INFO `artifact-locations.missing-dir`.
- `test_alias_divergence_is_warning` — `progress.dir` ≠ `state.subdirs.progress` ⇒ WARNING.
- `test_disabled_matrix_is_silent` — `enabled: false` ⇒ **alle fünf** Checks liefern 0 Findings (§4.6 Issue-Auflage).
- `test_abgrenzung_temp_literals` — `/tmp/x` erzeugt nur `temp-literal.system-temp`, **nicht** `artifact-locations.literal-path` (disjunkte Muster, `temp_literals.py:24-27`).
- `test_project_docs_files_are_not_violations` — `docs/issue-labels.md` (vierter `project-docs`-Eintrag) löst weder `literal-path` noch `missing-dir` aus; die Datei ist als Klassen-Ziel zulässig (OQ-6, #1188).
- `test_registered_in_consistency_check` — `check_artifact_locations` wird in `consistency-check.py:238-249` aufgerufen (AST/Import-Assertion).

**Impl:** `check_artifact_locations(agent_meta_root, project_root, config) -> list[Finding]`;
liest die Baseline aus `.meta-config/artifact-locations.resolved.json` (`baseline.legacy_files`,
Datenquelle wie der Hook — kein zweiter Resolver, kein mtime-Vergleich) und
`unmanaged[]` aus der aufgelösten Matrix. Fehlt die Baseline ⇒ fail-open (0 Findings,
eine stderr-Warnzeile). Registrierung als Import (`consistency-check.py:42-69`) und Aufruf
(`:238-249`) neben `check_temp_literals`. Severity-Mapping:
`literal-path`/`inline-with-path-promise` = ERROR (Exit-Beeinflussung wie
bestehende Violations), `legacy-write`/`alias-divergence` = WARNING,
`missing-dir` = INFO. Schreibposition = jede Zeile mit einem der Cues
`**Output file:**`, `Persisted to:`, `ARTIFACTS:`, `Ziel`, `Schreib`, `write`,
`create`, `erstelle`, `speichere`, `→` **und** jede Tabellenzeile in einer
Sektion mit `File`/`Ziel`/`Output`. Keine Reparatur (Nicht-Ziel 9).

**Verifikation:** `pytest tests/test_consistency_artifact_locations.py -q` → 18 passed; `python3 scripts/consistency-check.py` → `[OK]` auf sauberem Repo (AC-08); `python3 scripts/sync.py --validate` rc 0.

#### T15 — Resolved-Datendatei + `--status-artifacts` (AC-14, IC-H1/H2)

**Datei:** Create `scripts/lib/artifact_status.py`; Modify `scripts/lib/sync_pipeline.py`; Modify `scripts/sync.py`; Modify `scripts/lib/cli_commands.py`; Modify `docs/api/cli-reference.md`; Create `tests/test_artifact_status_cli.py`
**Deps:** T4, T8 · **Größe:** L

**Test zuerst:**

- `test_json_has_schema_version_and_preset` — `schema_version == "1"`, `preset` gesetzt.
- `test_each_class_has_path_mode_source_exists` — AC-14 wörtlich, für alle 23 Klassen (project-docs: `files` statt `path`, inkl. `issue-labels`).
- `test_kinds_key_is_closed_and_additive` — je Klasse `kinds` als Array (leer außer `reviews`/`audits`/`analysis`/`reports`); Werte nur aus dem Enum (§4.1); `kind` (Singular) existiert nicht im JSON.
- `test_json_is_additive_stable` — unbekannte Felder erlaubt, Pflichtfelder stabil (Snapshot-Vergleich der Schlüssel).
- `test_exit_zero_when_all_resolved` — saubere Fixture ⇒ rc 0.
- `test_exit_two_names_key_and_reason_on_stderr` — unauflösbare Klasse ⇒ rc 2, **kein** Default-Druck, `stderr` nennt Klasse + Grund.
- `test_human_table_has_one_row_per_class` — 23 Zeilen.
- `test_status_flag_is_not_abbreviated_to_status` — `--status-artifacts` ist ein eigener Flag; `--status` (`sync.py:406`, Plan-Ledger-Bedeutung) bleibt unverändert (Parser-Assertion).
- `test_resolved_json_written_after_hash_capture` — AST/`inspect.getsource`-Assertion: neue Stage steht nach `_sync_stage_generated_file_hash_capture` (`cli_commands.py:1611`) und nach `_sync_stage_auto_commit_allowlist` (`:1615`), Muster `tests/test_generated_file_drift_pipeline_wiring.py:34-46`.
- `test_resolved_json_skipped_on_dry_run` — `--dry-run` schreibt `.meta-config/artifact-locations.resolved.json` **nicht** (Muster `sync_pipeline.py:1922-1924`).
- `test_backup_siblings_do_not_skew_counts` — `file_count`/`newest` ignorieren `*.sync-backup-*` (#1195).
- `test_violations_array_shape` — `{code, path, expected}`.
- `test_resolved_json_has_unmanaged_and_baseline` — Datendatei enthält `unmanaged[]` und `baseline: {generated_at, legacy_files}`; `legacy_files` listet nur Artefakt-Dateien (keine Marker, §3.5) — RVW2-1186-02 / RVW2-X-02.
- `test_status_json_reports_unmanaged_list` — `--status-artifacts --json` zeigt `unmanaged` als **Top-Level**-Liste, **nie** als Eintrag in `classes` (AC-12 bleibt 14 + 9).
- `test_status_json_reports_naming` — jede Klasse mit `naming` zeigt das Token-Muster (`adr` ⇒ `ADR-{nnn}_{slug}.md`, D3); `project-docs`/`scratch`/`state` haben kein `naming`-Feld.
- `test_status_json_reports_alias_attribution` — `scratch` mit gesetztem Alias zeigt `source: "project"` und `field_sources.path == "project-alias:repo_containment.tmp-sink.path"` (D1).
- `test_cli_flag_is_documented` — `docs/api/cli-reference.md` enthält beide Flags in Backticks (`check_sync_cli_docs`, `docs.py:9-44`); sonst `--validate` ERROR `docs.cli_reference`.

**Impl:**
`sync_pipeline._sync_stage_artifact_locations_resolved(agent_meta_root, project_root, config, args, log) -> None`
schreibt `{"schema_version":"1","enabled","strict","root","classes":[{"name","path","mode","naming","patterns"}],"legacy":[…],"unmanaged":[…],"baseline":{"generated_at","legacy_files":[…]}}`
atomar (`io.write_atomic`, Muster `:1921-1924`), Verdrahtung als **Stage 14c**
in `cli_commands._handle_sync` (nach `:1615`).
`artifact_status.build_report(...) -> dict` + `render_table(...)`;
`cli_commands._handle_status_artifacts(ctx)`; `sync.py`: zwei
`add_argument`-Einträge und ein `_MODE_HANDLERS`-Eintrag (`sync.py:757`)
sowie `"status_artifacts"` in `_STDOUT_CLEAN_MODES` (`:791`).
Die Datendatei ist zugleich Quelle des Containment-Hooks für den Scratch-Pfad (D1, T24) —
`classes[].name == "scratch"` muss deshalb stabil und vollständig sein.

**Verifikation:** `pytest tests/test_artifact_status_cli.py -q` → 17 passed; `python3 scripts/sync.py --status-artifacts --json | jq '.classes.specs'` → enthält `path/mode/source/exists`; `echo ${PIPESTATUS[0]}` → 0.

#### T16 — Hook `artifact-path-guard.sh` + `strict` (AC-09, §4.5) — **kritisch**

**Datei:** Create `hooks/1-generic/artifact-path-guard.sh`; Create `tests/test_artifact_path_guard_hook.py`
**Deps:** T15; #1151 verifiziert · **Größe:** L

**Test zuerst** (Muster `tests/test_repo_containment_hook.py`: `subprocess.run`, Fixture extern via `tempfile.mkdtemp(dir=tempfile.gettempdir())`):

- `test_header_is_opt_in` — `parse_hook_metadata` (`lib.hooks`) liefert `enabled_by_default: false`, `event: PreToolUse`, `matcher: ""`.
- `test_allow_target_in_class_path` — Ziel `docs/reviews/x.md` bei `reviews.path = docs/reviews` ⇒ rc 0.
- `test_warn_target_in_managed_tree_outside_class` — Ziel `docs/spikes/x.md`, Klasse `spikes.path = docs/spikes-2` ⇒ stderr-Warnung, rc 0 (`strict: false`).
- `test_block_same_case_with_strict` — `strict: true` ⇒ rc 2, Meldung nennt erwarteten Pfad.
- `test_block_legacy_target_in_both_modes` — `docs/plans/audit-x.md` (in `legacy[]`) ⇒ rc 2, auch bei `strict: false` (AC-09).
- `test_legacy_pattern_wins_over_class_path` — `docs/adr/0002-neu.md` liegt **im** aktiven Klassenpfad `docs/adr` **und** trifft ein Legacy-Muster ⇒ rc 2 (Auswertungsreihenfolge Marker → `unmanaged` → `legacy` → Klassenpfad, D3); `docs/adr/ADR-002_neu.md` ⇒ rc 0.
- `test_marker_files_are_never_blocked` — `docs/conclusions/.gitkeep` ⇒ rc 0 in **beiden** `strict`-Zuständen (Scaffold-Ausnahme, §3.5).
- `test_allow_src_and_tests_untouched` — `src/app.py`, `tests/test_x.py` ⇒ rc 0, keine Warnung.
- `test_project_docs_file_is_allowed` — `docs/issue-labels.md` ⇒ rc 0 in beiden `strict`-Zuständen (viertes `project-docs`-File, OQ-6/#1188); eine Datei `docs/labels.md` (nicht deklariert) ⇒ warn/block.
- `test_unmanaged_target_is_allowed` — `docs/api/x.md` und `.meta-config/issue-labels-state.json` ⇒ rc 0 in **beiden** `strict`-Zuständen (D-8; der Hook liest `unmanaged` aus der Datendatei, sonst würde `docs/api/**` als „managed tree, fremde Klasse" gewarnt).
- `test_allow_target_outside_managed_trees` — Projekt-Root-Dateien (`README.md`) ⇒ rc 0.
- `test_fail_open_on_missing_datafile` — Datei fehlt ⇒ rc 0 + eine Warnzeile.
- `test_fail_open_on_corrupt_json` — kaputtes JSON ⇒ rc 0 + eine Warnzeile.
- `test_uses_shared_helpers` — Skript sourct `lib/hook_common.sh` und ruft `hook_json_get`/`hook_known_tool_name`; keine Duplikation (statische Assertion über den Dateitext; #1151-Auflage).
- `test_outside_project_root_is_not_this_hooks_job` — Ziel außerhalb Root ⇒ rc 0 (nur `repo-containment` blockt).
- `test_no_content_or_extension_checks` — `.txt`- und `.md`-Ziel verhalten sich identisch (Nicht-Zuständigkeit §4.5).

**Impl:** Kopf nach `hooks/1-generic/repo-containment.sh:1-8`, aber als
**einzelne** Datei ohne Self-Health-Split (Routing-Konvention, fail-open;
Selbstheilungs-Muster `repo-containment.sh:11-34` ist Security-Boundary-
spezifisch und wird hier nicht kopiert). Liest
`.meta-config/artifact-locations.resolved.json` **relativ zu `root`**, kein
Python pro Aufruf, kein YAML. `strict` aus der Datei; `unmanaged` wird **vor** der
Baum-Prüfung ausgewertet (allow, auch unter `docs/**`). Entscheidungstabelle
exakt §4.5. Marker-Dateien (`.gitkeep`, `.gitignore`, `.keep`) werden nie
geblockt — dieselbe Konstante wie T8/T14 (`MARKER_FILENAMES`).

**Warum `enabled_by_default: false` bleibt (RVW-1186-01):** AC-09 wird
zweistufig erfüllt — Meldung immer (T14), Block erst nach Aktivierung. Ein
default-aktiver Hook würde jedes Bestandsprojekt mit `docs/plans/audit-*.md`
beim ersten Schreibversuch blocken, bevor die Migration überhaupt beschrieben
ist; die Aktivierung ist ein bewusster Projekt-Schritt (Spec §4.5).

**Verifikation:** `pytest tests/test_artifact_path_guard_hook.py -q` → 16 passed; `pytest tests/test_hook_metadata.py tests/test_hook_enablement_consistency.py -q` → 0 failed; `python3 scripts/sync.py --dry-run` meldet den Hook als „copied (not enabled)".

#### T24 — Containment-Hook liest den aufgelösten Scratch-Pfad (D1, §3.6)

**Datei:** Modify `hooks/1-generic/repo-containment.sh`, `hooks/1-generic/repo-containment-impl.sh`; Create `tests/test_repo_containment_scratch_resolution.py`
**Deps:** T9, T15, T16 · **Größe:** S

**Kontext (VERIFIED):** heute liest `repo-containment-impl.sh:610-622` den Roh-Key
`repo_containment.tmp-sink.path` (Default `.tmp`) über den Stdlib-YAML-Subset-Reader; die
lexikalischen Regeln liegen in `path_error` (`:520-578`) und sind durch
`tests/test_tmp_sink_path_parity.py` + `tests/fixtures/tmp-sink-path-corpus.json` gegen
`scripts/lib/repo_containment.py::tmp_sink_path_error` gepinnt.

**Test zuerst** (Muster `tests/test_repo_containment_hook.py`: `subprocess.run`, Fixture extern
via `tempfile.mkdtemp(dir=tempfile.gettempdir())`):

- `test_hook_uses_resolved_scratch_path` — Datendatei sagt `classes.scratch.path = "alt-sink"`, `project.yaml` weiterhin `.tmp` ⇒ Schreiben nach `alt-sink/x` ist erlaubt, `.tmp/x` wird geblockt (genau **eine** Quelle, D1).
- `test_hook_falls_back_to_legacy_key_without_datafile` — Datendatei fehlt ⇒ Verhalten wie heute (`repo_containment.tmp-sink.path`), fails **closed**, eine Warnzeile auf stderr; das Gefängnis öffnet sich nie.
- `test_disabled_sink_still_blocks` — `repo_containment.tmp-sink.enabled: false` + `classes.scratch.path: "alt-sink"` ⇒ `alt-sink/x` blockiert (der Schalter bleibt bei `repo_containment`; `scratch` hat kein `enabled`, Spec §4.1).
- `test_exported_variable_wins` — exportiertes `ARTIFACT_SCRATCH_DIR` überschreibt die Datendatei (Präzedenz §3.6).
- `test_lexical_rules_are_unchanged` — `../x`, absoluter Pfad und leerer Wert im Scratch-Pfad werden weiterhin abgelehnt; `tests/test_tmp_sink_path_parity.py` bleibt grün (Korpus unangetastet).
- `test_block_message_names_matrix_key` — die Blockmeldung nennt `artifact-locations.classes.scratch.path` **und** `repo_containment.tmp-sink.enabled` als Reparaturweg.

**Impl:** In `repo-containment-impl.sh` wird die Pfad-Ermittlung (`:610-622`) umgestellt:
(1) `ARTIFACT_SCRATCH_DIR` aus der Umgebung, (2) `classes[].name == "scratch"` → `path` aus
`<root>/.meta-config/artifact-locations.resolved.json` (Parser mit
`hook_json_get`-Äquivalent bzw. `python3 -c` nur als Fallback **innerhalb** des bestehenden
Helfer-Musters; kein YAML-Parsing der Matrix), (3) `repo_containment.tmp-sink.path`,
(4) `.tmp`. `path_error` und die Canonical-Form bleiben unverändert; `sink_enabled` kommt
weiterhin aus `repo_containment`. `repo-containment.sh` (Self-Health-Split-Kopf) wird nur
angepasst, wenn dort der Key im Hilfetext steht — keine Logik-Duplizierung.

**Verifikation:** `pytest tests/test_repo_containment_scratch_resolution.py -q` → 6 passed;
`pytest tests/test_tmp_sink_path_parity.py tests/test_repo_containment_hook.py -q` → 0 failed;
`python3 scripts/sync.py --dry-run` unverändert.

---

### M5 — Admin-UI

#### T17 — `artifact-locations` in die Whitelist aufnehmen (AC-07a)

**Datei:** Modify `scripts/admin-server.py`; Modify `tests/test_admin_server.py`
**Deps:** T1 · **Größe:** S

**Test zuerst:**

- `test_artifact_locations_is_writable` — `"artifact-locations" in PROJECT_WRITABLE_SECTIONS`.
- `test_section_is_accepted_by_put` — `PUT /api/config/project/section` mit `section: "artifact-locations"` läuft **nicht** in `_assert_project_sections_writable` (`:5241-5255`); ohne den Eintrag wäre es HTTP 400.
- `test_whitelist_size_increased_by_one` — die Menge hat genau einen neuen Eintrag gegenüber `aaed14c2` (kein Kollateral-Umbau in diesem Task).
- `test_no_derivation_in_this_task` — AST-Assertion: `_SCHEMA_SECTIONS`/`_RUNTIME_ONLY_SECTIONS` existieren **noch nicht** (die Ableitung ist T22, Follow-up).

**Impl:** eine Zeile in `PROJECT_WRITABLE_SECTIONS` (`admin-server.py:234-259`),
alphabetisch einsortiert. **Keine** Ableitung aus dem Schema — die ist an
#1141 gebunden (kanonische Reihenfolge, Spec §9) und als T22 spezifiziert.

**Verifikation:** `pytest tests/test_admin_server.py -q` → 0 failed; `python3 scripts/sync.py --validate` rc 0.

#### T18 — Write-Guard mit Feldnamen (AC-06, §4.4)

**Datei:** Modify `scripts/admin-server.py`; Create `tests/test_artifact_locations_admin_api.py`
**Deps:** T17, T4 · **Größe:** M

**Test zuerst:**

- `test_put_relative_path_persists` — `PUT /api/config/project/section` mit gültiger Sektion ⇒ 200, Datei enthält Wert.
- `test_put_dotdot_path_rejected_with_field_name` — `classes.specs.path: "../x"` ⇒ HTTP 400, Meldung enthält `artifact-locations.classes.specs.path` (AC-06 wörtlich).
- `test_put_absolute_path_rejected` — `/etc/x` ⇒ 400.
- `test_put_unknown_class_rejected` — `classes.bogus` ⇒ 400 (Schema-Guard **und** eigener Guard).
- `test_put_se_requirements_off_rejected_when_cascade_active` — 400 mit Grund (nutzt T5-Logik).
- `test_put_legacy_intersection_rejected` — 400.
- `test_put_unmanaged_intersection_rejected` — `unmanaged: ["docs/specs"]` bei aktivem `specs.path = docs/specs` ⇒ 400 (D-8, RVW2-X-02).
- `test_guard_runs_before_disk_write` — bei Fehler bleibt die Datei byte-identisch (Muster `test_invalid_partial_section_rejected_without_write`, `tests/test_admin_server.py:1967`).
- `test_guard_is_wired_into_guard_block` — `_guard_artifact_locations_write(section, data)` steht im Block `admin-server.py:5305-5308` **vor** `config_manager.write` (`:5310`).

**Impl:** `_guard_artifact_locations_write(self, section: str, data: Any) -> None`
ruft `artifact_locations.validate_section(data, schema, project_root)` (dieselbe
Logik wie T5) und `io.safe_path(project_root, path)` (`io.py:663`) ohne
`ValueError`; `ValueError` ⇒ 400 (Mapping `do_PUT`/`do_POST`,
`_assert_project_sections_writable:5241-5255`). Keine neuen Endpunkte.

**Verifikation:** `pytest tests/test_artifact_locations_admin_api.py -q` → 9 passed.

#### T19 — UI-Pane „Artifacts" (AC-06)

**Datei:** Modify `docs/ui/admin-ui.html`; Modify `docs/api/admin-ui-reference.md`; Create `tests/test_artifact_locations_admin_ui.py`
**Deps:** T18, T15 · **Größe:** L

**Test zuerst** (statische UI-Assertions gegen den Dateitext; kein Browser-Test, weil #1189 den Serverstart betrifft):

- `test_ui_has_artifact_pane` — `admin-ui.html` enthält einen Bereich mit `artifactId`-Rendering je Klasse und `saveProjectSection("artifact-locations", …)` (Muster `:7448`).
- `test_ui_routes_pane` — Routing-Map (`:11377`-Umfeld) enthält `project/artifacts` → `project_instance-artifact_locations`.
- `test_ui_renders_mode_and_git_selects` — `files|inline|off` und `tracked|ignored`.
- `test_ui_renders_legacy_readonly` — `legacy[]` ohne Schreib-Button.
- `test_ui_preview_uses_status_json` — Vorschau nutzt `--status-artifacts --json` (Server-Endpoint bzw. eingebettete Payload), kein zweiter Resolver im Browser.
- `test_help_id_is_documented` — `docs/api/admin-ui-reference.md` enthält `<!-- help-id: project_instance-artifact_locations -->`; sonst ERROR `docs.ui_help_mappings` (`docs.py:47-97`).

**Impl:** Pane nach dem Muster `repo_containment` (`:7314-7315`): eine Zeile
pro Klasse (Pfad-Text, Modus-Select, git-Select, Naming), `legacy[]` und
`unmanaged[]` read-only, Vorschau „Rolle X schreibt nach Y". Panes klein halten (R9).

**Verifikation:** `pytest tests/test_artifact_locations_admin_ui.py -q` → 6 passed; `pytest tests/test_admin_server.py -q` → 0 failed; `python3 scripts/consistency-check.py` ohne `docs.ui_help_mappings`; nach #1189 liefert `GET /api/config/artifact-locations` die Sektion.

---

### M6 — Doku, Migration, Szenario

#### T20 — Manager-Rolle, Regeltext, Beispiel, Changelog (AC-14, OQ-4)

**Datei:** Modify `agents/1-generic/agent-meta-manager.md`; Modify `rules/1-generic/se-cascade-artifact-taxonomy.md`; Modify `templates/configs/project.yaml.example`; Modify `howto/configs/project.yaml.example`; Modify `CHANGELOG.md`
**Deps:** T11, T15 · **Größe:** M

**Test zuerst:**

- `test_manager_references_status_artifacts` — `agent-meta-manager.md` nennt `sync.py --status-artifacts --json` (AC-14; Einfügepunkt nahe `:107`/`:112`).
- `test_taxonomy_uses_se_root_variable` — `se-cascade-artifact-taxonomy.md` enthält **kein** Literal `docs/se` mehr, sondern `{{ARTIFACT_SE_ROOT}}` (D4); der frühere Satz „Konzept-Default: `docs/se`" ist ersetzt, und die Datei nennt `docs/se/**` als Legacy-Ablage, nicht als Default.
- `test_adr_rule_naming_matches_matrix_default` — `rules/1-generic/se-cascade-adr-standard.md:10` (`ADR-NNN_kurztitel.md`) und der Matrix-Default `ADR-{nnn}_{slug}.md` beschreiben dieselbe Form (`NNN` ↔ `{nnn}`, `kurztitel` ↔ `{slug}`); der Test pinnt die Äquivalenz, damit D3 nicht driftet.
- `test_example_config_has_artifact_block` — **parametrisiert über beide** vollständigen Beispiele (`templates/configs/project.yaml.example`, `howto/configs/project.yaml.example`): enthält `artifact-locations:` mit `enabled`, `preset`, `classes` (`scratch.path` explizit, D1), `legacy`, `unmanaged` (RVW2-1186-04).
- `test_example_configs_stay_in_sync` — der `artifact-locations`-Block ist in beiden Dateien byte-identisch (keine Divergenz der Beispiele).
- `test_example_config_does_not_promote_tmp_sink_alias` — beide Beispiele setzen **nur** `artifact-locations.classes.scratch.path`; `repo_containment.tmp-sink.path` erscheint dort nicht als empfohlene Zweitkonfiguration (D1, Spec §5 Nr. 11). Ein vorhandener `tmp-sink`-Block bleibt unverändert dokumentiert, ohne Pfad-Empfehlung.
- `test_example_config_uses_token_naming` — `classes.adr.naming` steht als `ADR-{nnn}_{slug}.md` in beiden Beispielen; die `<TOKEN>`-Form kommt in Config-Beispielen **nicht** vor (D3).
- `test_changelog_entry_mentions_migration` — CHANGELOG-Eintrag nennt `legacy[]`, `enabled: false` (R1), die Scratch-Alias-Migration (`--migrate-artifact-aliases`, D1) und die ADR-Naming-Umstellung (D3).

**Impl:** Doku-Texte; keine Code-Änderung. **Beide** `project.yaml.example` werden im selben
Task geändert (Spec §9: #1187/#1186/#1188/#1181, je nur eigene Keys, keine Umsortierung);
`docs/guides/project.yaml.example` bleibt unverändert (Orchestrator-Teilbeispiel).
`docs/concepts`-Doku (H-3) bleibt in der Lazy-Rule (T13), kein zweiter Doku-Kanal.

**Verifikation:** `pytest tests/test_artifact_locations_templates.py -q` → 0 failed; `python3 scripts/consistency-check.py` ohne `docs.*`-Finding; `python3 scripts/sync.py --validate` rc 0.

#### T21 — Ein voller Szenarientest + Szenario `99` (AC-02/04/06/09/10/12/13/14)

**Datei:** Create `tests/test_artifact_locations_scenario.py`; Create `tests/scenarios/configs/99-artifact-locations-matrix.project.yaml`; Create `tests/scenarios/asserts/99-artifact-locations-matrix.sh`; Modify `tests/scenarios/registry.md`
**Deps:** T1–T20, T24 · **Größe:** L

**Test zuerst** (ein Test, mehrere Phasen; Fixture-Root `.tmp/scenario-artifacts-1186/`, wird vor dem Lauf geleert):

- **Phase A — Default-Matrix:** Scratch-Konsument (minimales `.meta-config/project.yaml` + `platforms`), `python3 scripts/sync.py --config <fixture>/.meta-config/project.yaml --dry-run` ⇒ listet 12 `.gitkeep`-Aktionen (11 Klassen-Verzeichnisse + `docs/conclusions`); danach echter Lauf ⇒ die 11 Klassenverzeichnisse **plus** `docs/conclusions` existieren; `reviews` und `audits` existieren nach einem frischen Sync in einem Projekt, das sie noch nicht hatte (AC-04 wörtlich; `runbooks` ist die 12. Klasse und in AC-04 nicht aufgezählt, wird aber mitgescaffoldet).
- **Phase B — Preset/Projekt-Override:** `preset: minimal` + `classes.audits.path: compliance/audits` ⇒ `--status-artifacts --json` zeigt `audits.source == "project"`, `reviews.source == "preset:minimal"` (AC-15); Verzeichnis `compliance/audits` existiert, `docs/reviews` **nicht** (Preset `inline`).
- **Phase C — 9 SE-Klassen:** `se-validation.path: external-evidence`, `se-requirements.path: SE` ⇒ beide Zellpfade im Report unterschiedlich (AC-10); `se-requirements: off` bei aktiver Kaskade ⇒ Sync Exit 1 (AC-11), `se-decomposition: off` ⇒ Exit 0.
- **Phase D — Legacy:** Baseline (`baseline.legacy_files`) durch einen Sync setzen; danach Datei in `docs/plans/audit-legacy.md` anlegen, Sync ⇒ `--status-artifacts` zeigt `legacy_hits`; Consistency-Check meldet **einmal** `artifact-locations.legacy-write`; die Datei existiert unverändert (AC-09). Gegenprobe: eine Datei, die **in** der Baseline steht, meldet **nichts** (RVW2-1186-02); das von Phase A erzeugte `docs/conclusions/.gitkeep` erzeugt **keinen** Fund (Scaffold-Ausnahme, RVW-1186-01); `.meta-config/issue-labels-state.json` erzeugt **keinen** Fund (`unmanaged`, D-8); `docs/adr/0002-neu.md` trifft ein D3-Legacy-Muster ⇒ `legacy_hits`, `docs/adr/ADR-002_neu.md` ⇒ **kein** Fund.
- **Phase E — `kind`:** `docs/analysis/estimate-2026-11-09-x.md` mit `kind: estimate` ⇒ `--status-artifacts` validiert; `docs/estimates/new.md` ⇒ `legacy_hits` + Violation (AC-13); `kind: bogus` ⇒ `artifact-locations.kind-invalid`.
- **Phase F — `enabled: false`:** exakt heutiges Verhalten; keine neuen Verzeichnisse außer den drei Spec/Plan/Spike-Pfaden; `source == "disabled"` (AC-02-Escape).
- **Phase G — Hook:** simulierter PreToolUse-Payload für `docs/estimates/new.md` ⇒ rc 2 (legacy); für `docs/audits/x.md` ⇒ rc 0; für `docs/conclusions/.gitkeep` ⇒ rc 0 (Marker).
- **Phase H — Szenario-Katalog:** `tests/scenarios/run.sh 99` ⇒ `PASS`; die Registry-Zeile existiert und die IDs `94–98` bleiben unverändert (#1181/#1187).

**Impl:** Nur Test + Szenario-Daten; nutzt
`subprocess.run([sys.executable, "scripts/sync.py", …])` und `json.loads`;
keine Produktionsänderung. Verzeichnis wird im `try/finally` aufgeräumt (keine
Repo-Verschmutzung; `.tmp/` ist sanktioniert). Die Registry-Zeile
`99-artifact-locations-matrix` folgt der Katalogkonvention
(`tests/scenarios/registry.md:46-132`, Config unter `configs/`, Assertions
unter `asserts/`).

**Verifikation:** `pytest tests/test_artifact_locations_scenario.py -q` → 1 passed (8 Phasen); `tests/scenarios/run.sh 99` → `PASS`; Laufzeit < 120 s.

#### T23 — Alias-Migration `--migrate-artifact-aliases [--write]` (D1)

**Datei:** Create `scripts/lib/artifact_migration.py`; Create `tests/test_artifact_locations_migration.py`; Modify `scripts/sync.py`; Modify `scripts/lib/cli_commands.py`; Modify `docs/api/cli-reference.md` (**sequenziell nach T15**)
**Deps:** T4, T5, T9, T15, T18 · **Größe:** M

**Test zuerst:**

- `test_dry_run_prints_snippet_without_writing` — `--migrate-artifact-aliases` ohne `--write` gibt den fertigen `artifact-locations.classes.scratch.path`-Block auf stdout aus (Wert = aufgelöster Alias), `project.yaml` bleibt **byte-identisch**.
- `test_write_migrates_scratch_alias` — mit `--write` steht der Wert anschließend unter `artifact-locations.classes.scratch.path`; Kommentare und Key-Reihenfolge bleiben erhalten (`yaml_roundtrip.assert_roundtrip_preserved`, `scripts/lib/yaml_roundtrip.py:3-19`), `sync.py --validate` ist danach rc 0.
- `test_write_is_idempotent` — zweiter Lauf meldet „already migrated", schreibt 0 Bytes (Muster `--audit-config --apply`, `sync.py:476-484`).
- `test_write_refuses_on_divergent_values` — `classes.scratch.path != tmp-sink.path` ⇒ Exit 1 mit `artifact-locations.scratch-sink-divergence`, **kein** Schreibvorgang (T5 ist Autorität, nicht die Migration).
- `test_write_refuses_when_matrix_disabled` — `enabled: false` ⇒ Exit 1 mit Hinweis, dass `spec-plan-workflow.paths`/`se_output`/`tmp-sink` alleinige Quelle bleiben (Spec §3.3 Regel 5).
- `test_migration_covers_all_aliases` — Snippets für `spec-plan-workflow.paths.{specs,plans,spikes}`, `se_output.base_dir`, `repo_containment.tmp-sink.path`, `progress.dir`, `progress.checkpoint-dir`, `viz.event_log`; jeder Snippet nennt den Ziel-Key und den Migrationsgrund (D1).
- `test_cli_flag_is_documented` — `docs/api/cli-reference.md` enthält `--migrate-artifact-aliases` und `--write` in Backticks (sonst `docs.cli_reference`-ERROR).

**Impl:** `artifact_migration.build_migration_plan(config, matrix) -> MigrationPlan`
(reine Daten: je Alias `{target_key, value, reason}`); `render_snippets(plan) -> str`;
`apply_migration(project_config_path, plan) -> AppliedReport` schreibt **nur** mit `--write`,
atomar (`io.write_atomic`), nach `yaml_roundtrip`-Guard und nach
`artifact_locations.validate_section` (dieselbe Logik wie T18). `sync.py`: ein
`add_argument`-Paar plus `_MODE_HANDLERS`-Eintrag (`:757`), `"migrate_artifact_aliases"` in
`_STDOUT_CLEAN_MODES` (`:791`); `cli_commands._handle_migrate_artifact_aliases(ctx)`.
Keine automatische Migration im Sync — Schreiben nur auf explizites `--write`.

**Verifikation:** `pytest tests/test_artifact_locations_migration.py -q` → 7 passed;
`python3 scripts/sync.py --migrate-artifact-aliases` (ohne `--write`) verändert
`git diff --stat` nicht; `--validate` rc 0.

---

### Follow-up (nicht Teil dieses PRs)

#### T22 — Whitelist-Ableitung `_SCHEMA_SECTIONS ∪ _RUNTIME_ONLY_SECTIONS` (AC-07b, **nach #1141**)

**Datei:** Modify `scripts/admin-server.py`; Modify `tests/test_admin_server.py`
**Deps:** T17, **#1141 gemergt** · **Größe:** M · **Reihenfolge:** letzte Welle

**Test zuerst:**

- `test_whitelist_equals_schema_union_runtime_only` — `PROJECT_WRITABLE_SECTIONS == _SCHEMA_SECTIONS | _RUNTIME_ONLY_SECTIONS` (Mengengleichheit; AC-07b).
- `test_runtime_only_sections_preserved` — die 7 schema-losen Einträge `agent-prompts`, `steps-overrides`, `rules`, `environments`, `skills-registry`, `backup`, `submodule-protection` sind enthalten (F-2-Regression).
- `test_no_whitelisted_section_without_schema_or_runtime` — keine Waisen.
- `test_schema_is_derived_at_import` — `_SCHEMA_SECTIONS` wird aus dem Wurzel-`properties` gelesen (AST-Assertion: kein literaler Sektionsname in der Menge).
- `test_derivation_requires_strict_root` — Ableitung wirft, wenn das Wurzel-`additionalProperties` nicht `false` ist (Schutz gegen den Vor-#1141-Zustand).

**Impl:** `_RUNTIME_ONLY_SECTIONS: frozenset[str]` (7 Namen) + `_SCHEMA_SECTIONS`
aus dem Wurzel-`properties` (`schema.json:7-2849`); `PROJECT_WRITABLE_SECTIONS`
wird daraus berechnet — Modul-Import bleibt seiteneffektfrei.

**Warum hier und nicht in #1186 (Review 2026-11-09):** die Ableitung liest das
Wurzel-`properties`, das bis #1141 `additionalProperties: true` trägt
(`schema.json:2851-2854`). Vor #1141 würde sie eine unvalidierte Wurzel als
Wahrheit setzen und ohne die Union-Regel 7 Runtime-Sektionen regressieren.
Kanonische Reihenfolge: `#1187 → #1186 → #1188 → #1181`, danach `#1141`,
Whitelist-Ableitung zuletzt (eigenes Follow-up-Issue).

**Verifikation:** `pytest tests/test_admin_server.py -q` → 0 failed; Import-Zeit < 50 ms Zusatz (kein Netzwerk).

---

## 6. Interfaces & Signaturen

### 6.1 Resolver-API (`scripts/lib/artifact_locations.py`)

```python
CLASS_REGISTRY: dict[str, ClassSpec]          # 23 Einträge, Reihenfolge = §3
SOURCE_PROJECT = "project"
SOURCE_PRESET = "preset:{name}"
SOURCE_PROJECT_PRESET = "project-preset:{name}"   # K3: Attribution, keine eigene Stufe
SOURCE_PROJECT_ALIAS = "project-alias:{key}"      # D1: Alias-Attribution, keine eigene Stufe
SOURCE_SCHEMA = "schema-default"
SOURCE_CODE = "code-fallback"
SOURCE_DISABLED = "disabled"

@dataclass(frozen=True)
class ClassSpec:
    name: str
    form: Literal["dir", "file-set", "ephemeral", "state", "se"]
    default_path: str | None        # None für project-docs
    default_naming: str | None
    default_kinds: tuple[str, ...]  # geschlossenes Enum, Spec §4.1
    default_subdir: str
    default_git: Literal["tracked", "ignored"]
    default_retention: Literal["manual", "keep", "prune"]

@dataclass(frozen=True)
class ResolvedClass:
    name: str
    path: str | None                # None für project-docs
    mode: Literal["files", "inline", "off"]
    git: Literal["tracked", "ignored"]
    naming: str | None
    archive: str | None
    retention: Literal["manual", "keep", "prune"]
    kinds: tuple[str, ...]          # class-level allowed set (JSON: "kinds")
    subdir: str                     # "" für Nicht-SE
    subdirs: Mapping[str, str]
    event_log: str | None
    files: Mapping[str, str]        # project-docs (4 Einträge inkl. issue-labels)
    source: str                     # Klasse (Mehrheitsquelle)
    field_sources: Mapping[str, str]  # feldweise Herkunft (Regel 1)
    fallback_parent: str | None     # bei mode: off, Spec §3.1/§4.1

@dataclass(frozen=True)
class ResolvedMatrix:
    enabled: bool
    strict: bool
    preset: str
    classes: Mapping[str, ResolvedClass]
    legacy: tuple[str, ...]         # additiv, Framework zuerst
    unmanaged: tuple[str, ...]      # D-8: Negativ-Deklaration, keine Klasse, keine Variable

def load_presets(agent_meta_root: Path) -> dict: ...
def resolve_artifact_locations(config: dict, agent_meta_root: Path,
                               project_root: Path | None = None) -> ResolvedMatrix: ...
def resolve_cell_path(matrix: ResolvedMatrix, name: str, level: int,
                      folder: str, is_system: bool) -> str: ...
def resolve_se_projection(matrix: ResolvedMatrix, name: str) -> str: ...
def resolve_naming(matrix: ResolvedMatrix, name: str, *, kind: str | None = None,
                   scope: str | None = None, level: int | None = None,
                   folder: str | None = None, date: str | None = None,
                   n: int | None = None, slug: str | None = None) -> str: ...
def resolve_scratch_path(matrix: ResolvedMatrix, config: dict) -> tuple[str, str]: ...
def validate_naming(naming: str, name: str) -> None: ...
def validate_section(section_data: dict, schema: dict, project_root: Path) -> None: ...
class ArtifactLocationsError(ValueError):
    code: str                       # z. B. "artifact-locations.unknown-preset"
```

**Invarianten:** keine `sys.exit`, keine Env-Mutation, keine Schreibvorgänge,
keine Provider-Branch; `enabled: false` ⇒ `source == "disabled"` für alle
Felder und Pfade = heutige Defaults (`spec-plan-workflow.paths.*`,
`se_output.base_dir`, `tmp-sink.path`, `progress.*`, `viz.event_log`);
`resolve_se_projection` liefert für `reviews`/`reports`/`adr`/`traceability`
**immer** `{ARTIFACT_SE_ROOT}/<leaf>` (unabhängig von `classes.<x>.path`,
D-7); `resolve_scratch_path` liefert `("matrix-wert", "project")` wenn die Klasse gesetzt
ist, sonst `(alias-wert, "project-alias:repo_containment.tmp-sink.path")` und **niemals**
einen stillen Vorrang bei divergierenden Werten (Divergenz wirft
`artifact-locations.scratch-sink-divergence`, D1); `resolve_naming`/`validate_naming`
erzwingen die geschlossene Token-Liste (D3); die Funktionen sind auf dem leeren
Config-Dict total definiert.

### 6.2 Schema-Fragmente

Wurzel-Property (Einfügepunkt `schema.json:2223`-Umfeld) und `$defs`
(`schema.json:2855`) exakt nach Spec §4.1 — inklusive der dort begründeten
„ausgeschrieben statt `allOf`"-Regel (draft-07 `additionalProperties` wirkt
nur im selben Subschema). **Acht** `$defs`: `artifactKind` (20 Werte),
`artifactClassName` (23 Klassen, für `fallback-parent`), `artifactNaming` (D3),
`artifactClass`, `artifactSeClass`, `artifactFileSet`, `artifactEphemeral`, `artifactState`.

**`kind` — keine Abweichung mehr (Review 2026-11-09):** `kind` ist ein `array`
mit `items: {"$ref": "#/$defs/artifactKind"}` und `uniqueItems: true`; die
Werte stammen ausschließlich aus dem geschlossenen Enum, nie aus freiem String.
Die frühere Formulierung „je Klasse ein `enum` statt `array of string`" war
mehrdeutig (ein Enum kann keine Menge von 6 Kinds ausdrücken); verbindlich ist
jetzt: **Klassen-Ebene = Menge von Enum-Werten, Artefakt-Ebene = genau ein
Enum-Wert** (Spec §3.1).

**`naming` (D3, DECIDED 2026-11-09):** `artifactClass.naming` und
`artifactSeClass.naming` referenzieren `$defs/artifactNaming`
(`{"type":"string","minLength":1,"pattern":"^(?!.*\\.\\.)(?:[^{}/]|\\{(?:class|date|slug|kind|n|topic|scope|nnn|level|folder)\\})+$"}`).
Acht `$defs` insgesamt (der neue Eintrag ist `artifactNaming`). `defaults.naming`
nutzt `allOf` + `default`, weil draft-07 `$ref`-Geschwister ignoriert. Die
Klassen-Anwendbarkeit der Tokens (z. B. kein `{level}` in `audits`) prüft T5
(`artifact-locations.naming-invalid`) — das Schema prüft nur die Token-Alphabetik.

### 6.3 CLI-Exitcodes (`sync.py --status-artifacts`)

| Exit | Bedeutung | Ausgabe |
|---|---|---|
| 0 | alle 23 Klassen aufgelöst | Tabelle bzw. JSON auf stdout |
| 2 | mindestens eine Klasse nicht auflösbar | `key: reason` auf **stderr**, **kein** Default-Druck, stdout bleibt leer im `--json`-Modus |
| (1) | reserviert für Parser-/Config-Fehler (bestehende `sync.py`-Semantik) | unverändert |

`--json` ist additiv (`schema_version: "1"`), Pflichtfelder je Klasse:
`path` (bzw. `files`), `mode`, `source`, `exists`; optional/additiv
`naming` (D3), `field_sources` (inkl. `project-alias:<key>`, D1),
`file_count`, `newest`, `kinds`, `subdir`, `legacy_hits`, `violations` sowie die
Top-Level-Liste `unmanaged` (D-8, nie in `classes`).
`--status` bleibt unverändert (`sync.py:406`).

### 6.4 Hook-Vertrag (`hooks/1-generic/artifact-path-guard.sh`)

```
# hook: artifact-path-guard
# version: 1.0.0
# event: PreToolUse
# matcher: ""
# description: Route artifact writes into the configured artifact-locations class path.
# enabled_by_default: false      # Opt-in; AC-09 wird zweistufig erfüllt (Meldung immer, Block nach Aktivierung)
```

Eingabe: PreToolUse-JSON auf stdin (`tool_name`, `tool_input.file_path`),
gelesen mit `hook_json_get` (`hooks/1-generic/lib/hook_common.sh:3`, v1.9.0).
Datenquelle: `<root>/.meta-config/artifact-locations.resolved.json`
(Schema `{"schema_version":"1","enabled","strict","root","classes":[{name,path,mode,patterns}],"legacy":[…],"unmanaged":[…],"baseline":{"generated_at","legacy_files":[…]}}`).
`unmanaged` wird vor der Baum-Prüfung ausgewertet (allow); `baseline` ist für den Hook
nicht relevant (nur für `legacy-write` in T14).
Ausgabe: rc 0 (allow/warn), rc 2 (block). Meldung nennt Ziel, erwarteten
Klassenpfad und Reparatur (`add to artifact-locations.classes.<x>.path or a
legacy entry`). **fail-open** bei fehlender/kaputter Datei (eine Warnzeile).
Marker-Dateien (`.gitkeep`, `.gitignore`, `.keep`) werden nie geblockt.
Auswertungsreihenfolge (D3): Marker → `unmanaged` → `legacy` → Klassenpfad → verwalteter
Baum → Root; `legacy` steht bewusst **vor** der Klassen-Freigabe, sonst wären die
ADR-Legacy-Muster innerhalb von `docs/adr` wirkungslos.
Prüft keine Inhalte, Endungen, Branch-Policies; schreibt nichts um.

**Zweiter Konsument derselben Datei (`repo-containment`).** Der bestehende Hook liest
`classes[].name == "scratch"` → `path` als Scratch-Bereich (D1); Präzedenz:
`ARTIFACT_SCRATCH_DIR`-Env → Datendatei → `repo_containment.tmp-sink.path` → `.tmp`.
`sink_enabled` und die lexikalischen Regeln bleiben bei `repo_containment`, damit
fehlende Datendatei das Gefängnis nie öffnet (T24).

### 6.5 UI-API (bestehende Routen, keine neuen)

| Aktion | Route | Handler |
|---|---|---|
| Lesen | `GET /api/config/artifact-locations` | `_route_get_config` (`admin-server.py:3823-3825`) |
| Schreiben | `PUT /api/config/project/section` mit `{"section":"artifact-locations","data":{…}}` | `_write_project_section` (`:5276-5311`) |
| Whitelist | — | `PROJECT_WRITABLE_SECTIONS` (`:234-259`), Eintrag `artifact-locations` handgepflegt (T17); Ableitung `_SCHEMA_SECTIONS ∪ _RUNTIME_ONLY_SECTIONS` = T22 (nach #1141) |
| Validierung | — | `_guard_artifact_locations_write` im Guard-Block (`:5305-5308`) |
| Vorschau | `--status-artifacts --json` (serverseitig eingebettet) | `lib/artifact_status.py` |

---

## 7. Teststrategie

### 7.1 Bestehende Tests (Regressionsanker, unverändert zu halten)

| Bereich | Dateien | Warum relevant |
|---|---|---|
| Schema/Config | `tests/test_spec_plan_config_schema.py`, `tests/test_context_topology_schema.py`, `tests/test_config_null_blocks.py`, `tests/test_config_variable_fallbacks.py`, `tests/test_config_audit.py` | `jsonschema`-Idiom, `additionalProperties`-Muster, `--audit-config` |
| Scaffold | `tests/test_spec_plan_scaffold.py` | Wrapper-Verhalten (`sync_pipeline.py:152`) |
| Consistency | `tests/test_consistency_checks.py`, `tests/test_consistency_temp_literals.py`, `tests/test_consistency_reference_standards.py` | Registrierung, Abgrenzung, Severity |
| Admin | `tests/test_admin_server.py` (u. a. `:1967`, `:2161-2168`, `:2290`, `:2350`) | Whitelist, 400 ohne Teil-Write, Kommentar-erhaltender Write |
| Hooks | `tests/test_hook_metadata.py`, `tests/test_hook_enablement_consistency.py`, `tests/test_hook_common_lib.py`, `tests/test_hook_drift.py`, `tests/test_hook_registration_invariant.py` | Header-Parsing, Opt-in, Helfer |
| Containment-Pfad | `tests/test_tmp_sink_path_parity.py`, `tests/fixtures/tmp-sink-path-corpus.json`, `tests/test_repo_containment_hook.py` | lexikalische Parität Hook ↔ `repo_containment.tmp_sink_path_error`; bleibt bei T24 **unverändert** grün (nur die Pfad-*Quelle* wechselt, nicht die Regeln) |
| Pipeline-Verdrahtung | `tests/test_generated_file_drift_pipeline_wiring.py:34-46` | Stage-Reihenfolge (Hash-Capture zuletzt) |
| Platzhalter | `tests/test_placeholder_grace_and_derivation.py` | Allow-List-Mechanik |
| Templates | `tests/test_template_report_paths.py`, `tests/test_template_slimming_equivalence.py` | kein `/tmp/opencode`, Goldens |

**Baseline:** `baseline-validate.txt` (rc 0, ein `active-set.gate-dropped`-Hinweis) und `baseline-check.txt` (DRY-RUN, `[WARN] 1 warning(s)`, Exit 0). Nach jedem Meilenstein-Gate darf **kein neues** ERROR/WARNING dazukommen (Ausnahme: die in T9 bewusst erzeugten Test-Fixture-Warnungen).

### 7.2 Neue Testdateien (17)

`schema`, `presets`, `resolver`, `validate`, `variables`, `placeholders`,
`artifact_scaffold`, `aliases`, `templates`, `consistency`,
`artifact_status_cli`, `artifact_path_guard_hook`, `artifact_locations_admin_api`,
`artifact_locations_admin_ui`, `artifact_locations_scenario`,
`artifact_locations_migration` (T23), `repo_containment_scratch_resolution` (T24) —
siehe §2.1.

### 7.3 Testmatrix pro Modus (`files | inline | off`)

| Modus | Resolver | Scaffold | Consistency | Hook | Status-JSON |
|---|---|---|---|---|---|
| `files` | Pfad gesetzt, `exists` | Verzeichnis + `.gitkeep` | `missing-dir` nur wenn fehlt | Ziel unter `path` ⇒ allow | `mode: files` |
| `inline` | Pfad bleibt (Doku), `mode: inline` | **kein** Verzeichnis | `inline-with-path-promise` wenn Template Pfad verspricht | Ziel unter Klassenpfad ⇒ allow (Klasse produziert nicht) | `mode: inline` |
| `off` | `mode: off`, `fallback-parent` gesetzt oder Config-Fehler | **kein** Verzeichnis | `inline-with-path-promise` wenn Template Pfad verspricht | Ziel unter Klassenpfad ⇒ allow | `mode: off` |

Jede Zelle wird in `tests/test_artifact_locations_resolver.py`
(parametrisiert) und in `tests/test_artifact_locations_scenario.py` (echter
Lauf) belegt.

**AC-05-Präzisierung (Review 2026-11-09):** getestet werden **Resolver,
Scaffold, Consistency-Check und Status-JSON** je Modus. Ein template-seitiger
`{{#if ARTIFACT_<X>_MODE}}`-Zweig ist **nicht** Teil dieses Plans: der Renderer
aktiviert Conditionals nur bei der Zeichenkette `"true"`
(`scripts/lib/variables.py:498-508`) und strippt nur statisch gewhitelistete
Variablen (`:570-598`) — ein Modus-Gate bräuchte zwei Boolesche Variablen je
Klasse (46 zusätzliche Namen) plus Whitelist-Eintrag. Als Follow-up
ausgelagert (Spec §6.3, §11).

### 7.4 Testmatrix pro Klasse

- 14 Nicht-SE: je ein Resolver-Fall (Default, Override, `source`) und ein
  Scaffold-Fall — 11 Verzeichnis-Klassen × `.gitkeep`, `project-docs`
  (Datei-Set) ohne Verzeichnis, 2 × kein `.gitkeep`.
- 9 SE: je ein `resolve_cell_path`-Fall (Level 1/2/3, `System`/`Component`)
  plus der AC-10-Kontrastfall (`se-validation` vs. `se-requirements`).
- Klassen-Zählung als **eine** Assertion (AC-12) plus Negativ-Assertion
  „kein `legacy[]`-Name ist eine Klasse".

### 7.5 Präzedenztest über alle Auflösungsstufen

`tests/test_artifact_locations_resolver.py` prüft die **vier Wertequellen** aus §3.3
feldweise, plus die beiden Attributionen (`project-preset`, `disabled`) — das ist die
Testmatrix zu AC-1186-15:

1. Projekt-Key (`classes.reviews.path`) → `project`
2. Projekt-Defaults (`defaults.naming`) → `project` (Regel 2, Feld-Vererbung **innerhalb**
   der Quelle „Projekt" — keine fünfte Quelle)
3. Preset (`preset: minimal`) → `preset:minimal`
4. Explizite Projekt-Preset-Wahl (`preset: minimal` im Projekt gesetzt, Framework-Default
   `default`) → `project-preset:minimal` (**Attribution, keine eigene Präzedenzstufe** — K3)
5. Schema-Default (leere Sektion, `docs/specs`) → `schema-default`
6. Code-Fallback (Klasse ohne Schema-Default) → `code-fallback`
7. `enabled: false` → `disabled` (kein Umleiten; Zustandswert, keine Wertequelle)

Die Zahl der **Wertequellen** bleibt damit vier (Projekt, Preset, Schema-Default,
Code-Fallback). `project-preset:<name>` und `disabled` sind Source-Attributionen, keine
Stufen; ein Test pinnt genau diese Unterscheidung
(`test_project_preset_is_attribution_not_a_level`).

**D1-Ergänzung (Rev. 4):** `field_sources[f] == "project-alias:<key>"` ist ebenfalls nur eine
Attribution: wenn `classes.scratch.path` fehlt und `repo_containment.tmp-sink.path` gelesen
wird, bleibt `source == "project"`. Der Test `test_scratch_alias_is_attribution_not_a_level`
pinned das; damit bleibt AC-1186-15 bei vier Quellen, und es gibt keine „fünfte Stufe
Alias". Divergenz ist kein Auflösungsfall, sondern ein harter Fehler (T5).

### 7.6 Zwischentests je Meilenstein

Siehe §4 (Gate-Spalte). Zusätzlich nach **jedem** Task:
`python3 scripts/sync.py --validate` (rc 0) und der Task-eigene pytest-Lauf.

### 7.7 Ein voller Szenarientest (am Ende)

`tests/test_artifact_locations_scenario.py` in
`.tmp/scenario-artifacts-1186/` (sanktioniert, `.gitignore`-Eintrag aus
bestehendem tmp-Sink) mit **echten** `sync.py`-Läufen, Default- und
Preset-Matrix, `--status-artifacts`-Prüfung (Phasen A–G, §T21). Das ist der
einzige End-to-End-Test; alle anderen bleiben Unit-/Integrationsebene.

---

## 8. Migration & Rollback

**Bestandsverzeichnisse bleiben gültig.** Kein Task verschiebt, archiviert
oder löscht eine Datei (Nicht-Ziel 1). Konkret:

| Bestand | Behandlung |
|---|---|
| `docs/superpowers/{specs,plans}` | `legacy[]`-Eintrag, read-only, nie beschrieben |
| `docs/plans/audit-*.md` (4 Dateien: 2 aktiv, 2 in `archive/`) | `legacy[]`-Eintrag; neue Audits gehen nach `docs/audits` |
| `docs/conclusions/` | **Legacy-Zielverzeichnis** (leer, `.gitkeep`, `legacy[]`), keine Klasse (D-6) |
| `docs/estimates/`, `docs/research/`, `.meta-viz/handoffs/**` | `legacy[]` |
| `docs/specs/*-review.md` | `legacy[]` |
| `SE/VV/**`, `SE/reports/**` | `legacy[]`-Alias; `reports.kind: vv` (D-7) |
| `docs/se/**` | `legacy[]`-Muster (**D4**); kein Default, keine zweite SE-Wurzel; neue Ziele ausschließlich `artifact-locations.classes.se-*.path` (`SE`) |
| `docs/adr/[0-9][0-9][0-9][0-9]-*.md`, `docs/adr/ADR-[0-9][0-9][0-9]-*.md` | `legacy[]`-Muster (**D3**); bestehende Dateien (z. B. `0001-pyyaml-runtime-ausnahme.md`) kommen beim ersten Sync in die Baseline und werden **einmal** gemeldet; neue ADRs nur in `ADR-{nnn}_{slug}.md` |
| `repo_containment.tmp-sink.path` | **Migrations-Alias** (**D1**), keine zweite Senke: wird nur gelesen, solange `classes.scratch.path` fehlt; beide gesetzt ⇒ Werte müssen gleich sein; `sync.py --migrate-artifact-aliases [--write]` schreibt die Matrix (T23) |
| `.tmp/`, `.meta-viz/` | unverändert; `scratch`/`state` projizieren nur die bestehenden Keys |

**`legacy[]` erhält keine neuen Writes** (AC-09): Consistency-Warnung
(`artifact-locations.legacy-write`) + Hook-Block (rc 2 in beiden
`strict`-Zuständen). Bestehende Dateien werden **einmal** gemeldet, nie
gelöscht.

**Rollback = Sektion entfernen.** `artifact-locations` aus
`project.yaml` löschen (oder `enabled: false`) ⇒ Resolver liefert
`source: "disabled"` und exakt die heutigen Pfade; Hook findet keine
Datendatei und ist fail-open; Consistency-Check ist still; `--status-artifacts`
zeigt `disabled`. Kein Datenverlust, kein Migrationsschritt rückwärts.
Zusätzlich: `.meta-config/artifact-locations.resolved.json` löschen ist
gefahrlos (wird bei jedem Sync neu geschrieben).

**Sync-Backup-Hinweis:** `sync.py` überschreibt generierte Dateien nur nach
Drift-Erkennung und legt `*.sync-backup-<ts>`-Geschwister an
(`.gitignore:22`, #1195). Bei der Matrix-Umstellung entstehen Backups für alle
26 geänderten Rollen-Templates; sie sind **kein** Rollback-Mechanismus,
sondern Diagnosehilfe. Echter Rollback ist der Git-Revert des PR (bzw.
`enabled: false`). `--status-artifacts` zählt `*.sync-backup-*` bewusst nicht
in `file_count`/`newest` (#1195).

---

## 9. Risiken

| # | Risiko | Gegenmaßnahme im Plan |
|---|---|---|
| R1 | Migration bestehender Ablagen; Altdateien wirken „unerreichbar" | `legacy[]` + `enabled: false` als Escape-Hatch; keine Bewegung; Release-Note (T20); `legacy_hits[]` im Status (T15) |
| R2 | `legacy[]`-Schreibschutz nur konventionell | zweistufig: Consistency-Warnung sofort (T14), Hook-Block in beiden Modi (T16); Test je Legacy-Muster (T21/D) |
| R3 | Harter Fehler `se-requirements: off` trifft Bestandsprojekte | Meldung nennt Key + Alternative (`se-decomposition`), Prüfung nur bei aktiver Kaskade (T5); `--status-artifacts` als Pre-Migration-Check (T15) |
| R4 | Hook-Fehlalarme | `strict: false` Default; nur deklarierte Bäume; `src/`/`tests/`/Root frei; fail-open bei fehlender Datei (T16) |
| R5 | `mode: off` löscht den Audit-Trail | `fallback-parent` Pflichtfeld (§3.1/§4.1), Config-Fehler ohne Elternsenke (T5) |
| R6 | Whitelist-Ableitung regressiert 7 Runtime-Sektionen | Union-Regel + Mengengleichheits-Test — **aber erst T22 (nach #1141)**; in #1186 nur der handgepflegte Eintrag (T17) |
| R7 | Doppelmeldungen mit `temp_literals`/#1180 | disjunkte Muster, dokumentierte Abgrenzung + Test (T14) |
| R8 | Drei Wellen-Issues editieren dieselben Dateien | Serialisierung §Voraussetzungen; ein Task je Datei; Owner-Spalte §2 |
| R9 | Eine große `admin-ui.html` nimmt drei Panes auf | Pane klein, Vorschau serverseitig (T19); kein Parallel-Edit |
| R10 | SE-Default-Widerspruch (`SE` vs. `docs/se`) | **D4 (DECIDED 2026-11-09):** ein Default `SE` (T4); Regeltext auf `{{ARTIFACT_SE_ROOT}}` (T20); `docs/se/**` in `legacy[]` (T2) — kein zweiter Pfad |
| **R11** | **`scratch` vs. `tmp-sink.path` Doppelsenke** — zwei Config-Keys für dasselbe Verzeichnis; eine Rolle schreibt in `.tmp/x`, die andere in `custom-sink/x` | **D1 (DECIDED 2026-11-09): eine Quelle** (`classes.scratch.path`); `tmp-sink.path` nur Migrations-Alias, Gleichheitszwang, Divergenz = harter Fehler (T5), Deprecation-Warnung + Migration (T9/T23); `TMP_SINK_PATH` wird aus der Matrix gespeist; Containment-Hook liest den aufgelösten Wert (T24) |
| **R12** | **`vv`-Klasse** — Issue-YAML nennt `vv`, AC-12 zählt 14+9 | D-7: `reports.kind: vv` + `SE/VV/**` in `legacy[]`; keine 24. Klasse (T4); OQ-1 blockiert nur bei Ablehnung |
| **R13** | **`docs/conclusions`-Kollision** — AC-04 will das Verzeichnis, AC-12 zählt `conclusions` in `analysis` | D-6: Verzeichnis scaffolden (leer, `.gitkeep`, `legacy[]`), **keine** Klasse; Conclusion-Dokumente nach `docs/analysis` mit `kind: conclusion` (T4/T8/T10) |
| **R14** | **F-1 stille Fehlsubstitution** — 16 `{SE_BASE_DIR}` (einfache Klammer) werden nie ersetzt; neue Variablen könnten denselben Fehler erben | T11 mit Golden-Test „kein `{SE_` in `agents/1-generic`"; separate Issue-Erfassung (F-1) |
| **R15** | `--status`-Namenskollision (`sync.py:406`) | eigener, vollständiger Flag-Name; Parser-Test (T15) |
| **R16** | Stage-Reihenfolge bricht den Hash-Baseline-Vertrag | neue Stage **14c** nach `:1611`/`:1615`, AST-Test (T15); Kollisionsfläche mit **#1181-T9** (gleiche Stage 14) in §2.2 markiert |
| **R17** | `_MODE` als Template-Gate missverstanden — `{{#if ARTIFACT_<X>_MODE}}` wird nie entfernt (`variables.py:498-508`) und leckt in jeden Agenten | AC-05 präzisiert (§7.3); Gate als Follow-up F-4; kein `{{#if}}` in T10/T11 |
| **R18** | Scaffold-Marker (`.gitkeep`) verletzt AC-09 in `docs/conclusions` | `MARKER_FILENAMES`-Ausnahme in T8 **und** T14/T16; Null-Fund-Test (T14; die `check_artifact_locations`-Fälle laufen erst dort, RVW2-1186-01) |
| **R19** | **`legacy-write` ohne deterministische Basis** — „mtime > letzter Sync" war nirgends definiert; Folge wäre ein Dauerwarn-Teppich auf Bestandsprojekten | Baseline = `baseline.legacy_files` aus Stage 14c (T15), **kein** mtime-Vergleich; fail-open (0 Findings + eine stderr-Zeile) bei fehlender Baseline; Tests in T14 (RVW2-1186-02) |
| **R20** | **`unmanaged` wird als Klasse missverstanden** — `.meta-config/issue-labels-state.json` (aus #1188) und die Doku-Unterbäume könnten in AC-12 mitgezählt oder vom Hook gewarnt werden | `unmanaged[]` ist Top-Level-Liste ohne `mode`/Variable; Hook wertet sie vor der Baum-Prüfung aus; Zählung bleibt 14 + 9 (T4/T15/T16, D-8) |
| **R21** | **Scratch-Alias bleibt liegen** — Bestandsprojekte setzen nur `tmp-sink.path`, die Deprecation-Warnung wird ignoriert | Alias bleibt lesbar (kein Bruch), Gleichheitszwang verhindert stille Doppelsenke (T5), `--migrate-artifact-aliases [--write]` schreibt idempotent (T23), Warnung nennt Ziel-Key + Befehl (T9) |
| **R22** | **Naming-Token driften** — Rolle schreibt `<YYYY-MM-DD>`, Config erwartet `{date}`; oder Preset nutzt `{level}` in `audits` | geschlossene Token-Liste im Schema (`$defs/artifactNaming`) + Klassen-Anwendbarkeit im Validator (`naming-invalid`); Tests in T1/T2/T4/T5; Beispiele nutzen nur Token-Form (T20) |
| **R23** | **Containment-Hook und Matrix laufen auseinander** (zwei Schreibziele, eines unsichtbar) | T24 stellt den Hook auf die aufgelöste Datendatei um, mit dokumentierter Fallback-Kette; `tmp-sink.enabled` und die lexikalische Parität bleiben unverändert grün |

---

## 10. AC → Task-Traceability

| AC | Kurzforderung | Tasks | Beleg-Test |
|---|---|---|---|
| AC-1186-01 | Schema-Sektion, `additionalProperties: false` je Ebene | T1, T3 | `test_artifact_locations_schema.py` |
| AC-1186-02 | Resolver + `ARTIFACT_*` + Scaffold, dry-run-safe | T4, T6, T8, T15 | `test_artifact_locations_resolver.py`, `test_artifact_scaffold.py` |
| AC-1186-03 | Kein Schreib-Literal; `/tmp/opencode` leer; Lese-Literale = 2-Zeilen-Ratchet | T10, T11, T12, T14, T21 | `test_no_literal_managed_path_in_write_position`, `test_read_ok_ratchet_is_exactly_two_lines`, `grep`-Gate (T10) |
| AC-1186-04 | Defaults erzeugen die AC-04-Liste (11 Pfade inkl. `docs/conclusions`); zusätzlich `docs/runbooks`; `reviews`/`audits` nach frischem Sync | T8, T21/A | `test_files_mode_creates_directory_and_gitkeep`, Phase A |
| AC-1186-05 | `off`/`inline` deterministisch über Resolver/Scaffold/Consistency/Status | T4, T14, T21 | Testmatrix §7.3 (4 Achsen je Modus) |
| AC-1186-06 | UI lesen/editieren/speichern; `../x` ⇒ 400 mit Feldnamen | T18, T19 | `test_put_dotdot_path_rejected_with_field_name` |
| AC-1186-07 | a) `artifact-locations` schreibbar (T17, in #1186); b) Ableitung driftfrei (T22, nach #1141) | T17, T22 | `test_artifact_locations_is_writable`; `test_whitelist_equals_schema_union_runtime_only` (Follow-up) |
| AC-1186-08 | Neuer Check erscheint; `--validate` grün | T14 | `test_literal_path_in_write_position_is_violation`, Gate M4 |
| AC-1186-09 | `legacy[]` erhält keine neuen Artefakt-Inhalte; Marker ausgenommen; Baseline-basiert, einmal gemeldet | T8, T14, T15, T16, T21/D | `test_legacy_write_uses_baseline_not_mtime`, `test_legacy_markers_produce_no_legacy_write`, `test_clean_repo_sync_produces_no_legacy_write`, `test_block_legacy_target_in_both_modes` |
| AC-1186-10 | 9 SE-Klassen einzeln setzbar | T4, T11, T21/C | `test_se_validation_and_se_requirements_resolve_per_cell` |
| AC-1186-11 | `se-requirements: off` hart, `se-decomposition: off` erlaubt | T5, T21/C | `test_se_requirements_off_with_active_cascade_is_hard_error` |
| AC-1186-12 | exakt 14 + 9 Klassen; keine Legacy-Klasse beschrieben; `unmanaged` ist keine Klasse | T4, T8 | `test_class_registry_has_23_entries`, `test_conclusions_is_legacy_not_class`, `test_unmanaged_is_not_a_class` |
| AC-1186-13 | `kind` (Enum) in zusammengelegten Klassen; Legacy-Write gemeldet | T1, T4, T10, T14, T21/E | `test_kind_is_closed_enum`, `test_kind_enum_is_class_scoped`, Phase E |
| AC-1186-14 | `--status-artifacts --json` mit `path/mode/source/exists` plus `unmanaged`-Liste; Manager nennt es | T15, T20 | `test_each_class_has_path_mode_source_exists`, `test_status_json_reports_unmanaged_list`, `test_manager_references_status_artifacts` |
| AC-1186-15 | Präzedenz über **vier Wertequellen** + `source`, plus `disabled`, `project-preset`- und `project-alias`-Attribution (D1) | T4 | §7.5 (4 Quellen + 2 Attributionsfamilien) |
| AC-1186-16 | `rules-preset: lazy` bleibt `CLAUDE.md ∩ .claude/rules = 0` | T13 | `test_no_always_on_rule_added` |

**Hygiene-Vorgaben:** H-1 → T13; H-2 → T6 (`test_variables_built_once_per_provider`); H-3 → T13 (blockiert durch #1180); H-4 → T13 (`test_provider_context_count_does_not_grow`, relative Assertion — RVW2-1186-03).

**AC-Präzisierungen (Review 2026-11-09, Spec §6.3):** AC-03 = Schreibposition +
Ratchet (T10/T14); AC-05 = Resolver/Consistency statt Template-Gate (T4/T14/T21);
AC-07 = geteilt in T17 (jetzt) und T22 (Follow-up nach #1141); AC-09 = Inhalt
statt Marker **plus Baseline `baseline.legacy_files` statt mtime** (T8/T14/T15/T16,
RVW2-1186-02); AC-13 = geschlossenes Enum (T1/T4/T5).

**Entscheidungen D1–D4 → Tasks (Rev. 4):**

| D-Nr | Entscheidung (kurz) | Tasks | Beleg-Test / Gate |
|---|---|---|---|
| **D1** | eine Scratch-Quelle, Alias-Migration, Containment-Hook liest Matrix | T4, T5, T9, T15, T23, T24 | `test_scratch_path_is_single_source`, `test_scratch_alias_applies_only_when_class_absent`, `test_scratch_alias_equal_values_are_resolved` (T4); `test_scratch_sink_divergence_is_hard_error`, `test_scratch_alias_equal_values_pass_validation` (T5); `test_scratch_deprecation_warning_has_migration_hint`, `test_tmp_sink_path_variable_comes_from_matrix` (T9); `test_status_json_reports_alias_attribution` (T15); `test_write_migrates_scratch_alias`, `test_write_refuses_on_divergent_values` (T23); `test_hook_uses_resolved_scratch_path`, `test_hook_falls_back_to_legacy_key_without_datafile` (T24) |
| **D2** | D-9-Ausnahme bleibt (Standalone-Fallback in #1186) | T6 | `test_standalone_supplies_artifact_variables` |
| **D3** | Naming-Token, ADR-Default, zwei Legacy-Formen | T1, T2, T4, T5, T15, T20, T23 | `test_naming_accepts_canonical_tokens`, `test_naming_rejects_unknown_token`, `test_naming_rejects_angle_bracket_form` (T1); `test_default_adr_naming_is_canonical` (T2); `test_naming_resolves_per_class` (T4); `test_naming_token_not_applicable_is_hard_error` (T5); `test_status_json_reports_naming` (T15); `test_adr_rule_naming_matches_matrix_default` (T20) |
| **D4** | `SE` bleibt Default, Regeltext auf `{{ARTIFACT_SE_ROOT}}`, `docs/se/**` legacy | T2, T4, T20 | `test_se_root_default_is_SE`, `test_legacy_accepts_adr_non_canonical_forms` (T4); `test_legacy_contains_framework_paths` (T2); `test_taxonomy_uses_se_root_variable` (T20) |

---

## 11. Backlog-Bugs (gegen die echten Issue-Texte entschieden)

| Nr. | Einordnung | Tasks | Begründung |
|---|---|---|---|
| **#1150** | **Elternproblem / teilweise ersetzt** (keine Federführung in diesem PR) | T4, T8, T20 | #1150 beschreibt „es gibt keine bindende Artefakt→Ort-Konvention" und nennt 5 Probleme. #1186 liefert den **Mechanismus** und übernimmt die Matrix als Default-Werte. **Nicht** abgedeckt bleibt #1150-Problem 2 (`.tmp`-Lifecycle: Promotion + Cleanup) — explizit Nicht-Ziel (Spec §5 Nr. 2). Nach Merge: #1150 auf Punkt 2 reduzieren, nicht schließen. |
| **#1189** | **Blocker, muss zuerst** (Voraussetzung, kein Task hier) | — (Voraussetzung für M5) | Admin-Server-`start` meldet Erfolg, Kind stirbt an `tmp-sink`-Env-Pin vs. `system-temp-exception` (`config.py:888-937`); ohne Fix ist AC-06/07 nur In-Process testbar. Zusätzlich dieselbe Datei (`scripts/lib/config.py`) wie T5/T6/T9 → strikte Serialisierung. Plan `docs/plans/2026-11-09-1189-tmp-sink-pin-plan.md` existiert bereits. |
| **#1141** | **Nachfolger in der kanonischen Reihenfolge** (nicht Voraussetzung) | T3 (Vorbereitung), T22 (nach #1141) | Wurzel hat `additionalProperties: true` (`schema.json:2854`); die **Sektion** `artifact-locations` ist davon unabhängig self-contained (`additionalProperties: false`). `se_output` wird in T3 deklariert, damit #1141 es nicht bricht. Die Ableitung der Whitelist aus dem Schema setzt #1141 voraus und läuft als T22 danach; die Aussage „#1141 vor oder im selben PR" ist **zurückgezogen**. |
| **#1180** | **Direkte Wechselwirkung, Kanal gleich, Mechanik zuerst** | T13 (H-3) | #1180: Regeln emittieren consumer-relative Pointer (`docs/concepts/…`), die der Sync nie erzeugt. #1186-H-3 verlangt eine **generierte** Lazy-Pointer-Tabelle. Beide brauchen denselben generierten Index; ohne #1180 bleibt der Eintrag manuell (`skipif`-Test mit Begründung, T13). **Federführung #1180** für die Index-Mechanik; #1186 konsumiert sie. |
| **#1195** | **Orthogonal, aber Zähl-Nebenbedingung** | T15 | `--status-artifacts` zählt Dateien pro Klasse; 523 `*.sync-backup-*` (116 in `.opencode/agents`) dürfen `file_count`/`newest`/`legacy_hits` nicht verfälschen. Ausschlussmuster im Status-Report + Test. Kein Reihenfolge-Zwang. |
| **#1151** | **Voraussetzung verifizieren, nicht neu lösen** | T16 | `hook_common.sh` v1.9.0 (`:3`) nennt #1151-Findings; der neue Hook nutzt `hook_json_get`/`hook_known_tool_name` und dupliziert nichts. Verifikation vor T16; bei Restlücken blockiert T16, nicht der Rest. |
| **#1181** | **Direkte Datei-Kollision, läuft nach #1186** | T15 (Stage 14c), T21 (Szenario-ID) | #1181-T9 baut dieselbe **Stage 14** (`scripts/lib/sync_pipeline.py:1893-1924`) um, an die #1186 die Stage 14c hängt; zusätzlich belegt #1181 die Szenario-ID `94`, #1187 `95–98` — #1186 nimmt `99`. Kanonische Reihenfolge: `#1187 → #1186 → #1188 → #1181`. |
| **#1188** | **Erzeuger von `docs/issue-labels.md` und `.meta-config/issue-labels-state.json`, läuft nach #1186** | T1, T2, T15, T16 (Klassifikation) | #1188 legt die Label-Datei und ihre Zustandsdatei an. #1186 klassifiziert vorab: `docs/issue-labels.md` als `project-docs.files.issue-labels`, die Zustandsdatei als `unmanaged[]` (D-8, RVW2-X-02, K1) — sonst blockt der Managed-Tree-Hook die Erzeugung. **Federführung #1188** für den Generator, #1186 nur für die Klassifikation. |

**Kanonische Ausführungsreihenfolge (verbindlich):**
`#1187 → #1186 → #1188 → #1181`, danach `#1141`; die Whitelist-Ableitung aus dem
Schema läuft **zuletzt** (T22, eigenes Follow-up).

**Federführungs-Markierung bei Wellen-Überschneidung:**
`#1186` = Artefakt-Matrix (diese Dateien), `#1187` = `{{PROJECT_CONTEXT}}`-Scope,
`#1188` = Feedback-/Triage-Rollen, `#1181` = Nachbarwelle. Bei
`agents/1-generic/{feedback,meta-feedback,bug-feature-analyzer}.md` hat #1186
**vor** #1188 Federführung; bei `{{PROJECT_CONTEXT}}` hat #1187 Federführung
(#1186 fasst diese Variable nicht an, H-4).

---

## 12. Neu gemeldete Findings (separates Issue, Nummer folgt im Wave-Overview)

| # | Finding | Relevanz | Vorgeschlagener Titel | Labels | Task-Bezug |
|---|---|---|---|---|---|
| **F-1** | SE-Templates nutzen `{SE_BASE_DIR}` mit **einfacher** Klammer (16 Vorkommen in 12 Dateien; `se-requirements.md:184`, `se-architect.md:114`, `se-validator.md:177`), die `sync.py` nie substituiert — nur 4 Vorkommen nutzen `{{SE_BASE_DIR}}` (`placeholders.py:89`) | **hoch** — die neuen `{{ARTIFACT_SE_*_DIR}}` müssen doppelte Klammern nutzen; sonst derselbe stille Fehlschlag in 9 Klassen | `bug(agents): SE templates use {SE_BASE_DIR} with single braces — sync never substitutes it` | `bug`, `agents`, `consistency`, `P2` | T11 (Golden-Test), F-1-Issue für die übrigen Nicht-SE-Fälle außerhalb des Artefakt-Scopes |
| **F-2** | Reine Schema-Ableitung von `PROJECT_WRITABLE_SECTIONS` entfernt 7 Runtime-Sektionen (`agent-prompts`, `steps-overrides`, `rules`, `environments`, `skills-registry`, `backup`, `submodule-protection`; `admin-server.py:234-259` vs. `schema.json:7-2849`) | **hoch** — AC-07 fordert Ableitung, würde ohne Union 7 Sektionen regressieren | `bug(admin): deriving PROJECT_WRITABLE_SECTIONS from the schema drops 7 runtime-only sections` | `bug`, `config`, `admin-ui`, `P2` | T17 (Union + Mengengleichheits-Test) |
| **F-3** | Acht `docs/`-Unterbäume ohne Klasse (`superpowers`, `issues`, `testing`, `providers`, `api`, `howto`, `guides`, `se-cascade`) und `docs/plans/audit-*.md` (4 Dateien) in der Plans-Klasse | **mittel** — ohne Entscheidung Dauerwarnungen oder unvollständiges `legacy[]` | `chore(docs): classify the 8 unmanaged docs/ subtrees and the audit-*.md files in docs/plans` | `chore`, `docs`, `config` | T2 (`legacy[]`-Liste), T14 (`missing-dir`), OQ-6 |
| **F-4** | `ARTIFACT_<X>_MODE` ist **kein** renderbares Conditional: `_conditional_active` (`scripts/lib/variables.py:498-508`) aktiviert nur `"true"`, `strip_inactive_conditional_blocks` (`:570-598`) whitelistet statisch — ein `{{#if ARTIFACT_REVIEWS_MODE}}` würde nie entfernt und in jeden generierten Agenten lecken | **mittel** — blockiert ein template-seitiges Modus-Gating; AC-05 wurde deshalb auf Resolver/Consistency verengt (Spec §6.3) | `bug(agents): artifact mode variables cannot gate {{#if}} blocks — no conditional whitelist entry` | `bug`, `agents`, `config`, `P2` | T10/T11 (kein `{{#if}}`), §7.3; Follow-up braucht 2 Boolesche Gate-Variablen × 23 Klassen + Whitelist-Eintrag |

**Follow-up-Issues aus dieser Review-Runde:** **#1198, #1199, #1200** (real angelegt; die
inhaltliche Zuordnung trägt das Wave-Overview nach — hier bewusst keine erfundene
Titel-Zuordnung). Inhaltlich sind es die drei ausgelagerten Punkte: (a) Whitelist-Ableitung
nach #1141 (= T22), (b) template-seitiges Modus-Gating (= F-4), (c) `docs/issue-labels.md`
im `project-docs`-Set statt einer eigenen Klasse (§3.2, OQ-6) — sofern (c) den Rahmen von
#1188 sprengt.

**Keine erfundenen Issue-Nummern.** F-1…F-4 werden als eigene Issues geführt; die
Nummernzuordnung liefert das Wave-Overview. **Kein** Finding für `/tmp/opencode`: der
Zustand ist behoben und durch `tests/test_template_report_paths.py:61` geschützt
(Spec §2.6 STALE).

---

## 13. Offene Entscheidungen

| # | Frage | Empfehlung | Blockadewirkung |
|---|---|---|---|
| **OQ-1** (`vv`) | Eigene Klasse, `reports.kind`, oder 24. Zeile? Issue-YAML nennt `vv`, AC-12 fordert „genau 14 + 9" | **entschieden (D-7):** `reports.kind: vv`; `reports.path` bleibt `docs/reports` (AC-04); SE-Pfade über abgeleitete Projektionen; `SE/VV/**` in `legacy[]`; kein `se-path`-Feld | **keine Blockade mehr** (Review 2026-11-09): die Entscheidung ist im Vertrag, nicht als offene Frage — T4 pinnt `test_reports_path_stays_docs_reports` |
| **OQ-2** (`docs/conclusions`) | AC-04 verlangt das Verzeichnis, AC-12 zählt `conclusions` in `analysis` | **entschieden (D-6):** Verzeichnis scaffolden (leer, `.gitkeep`, `legacy[]`), keine Klasse; Dokumente nach `docs/analysis` (`kind: conclusion`); das `.gitkeep` ist über die Scaffold-Ausnahme von `legacy-write` ausgenommen | **keine Blockade mehr**: T8/T14 pinnen den Null-Fund |
| **OQ-5** (`scratch` ↔ `tmp-sink.path`) | Alias, Vorrang-Regel oder Verbot der Doppelkonfiguration? | **DECIDED 2026-11-09 (D1):** **eine** Quelle (`classes.scratch.path`); `tmp-sink.path` = Migrations-Alias (nur gelesen, solange die Klasse fehlt), Gleichheitszwang bei Doppelsetzung, Divergenz = harter Fehler `scratch-sink-divergence`; `TMP_SINK_PATH` wird aus der Matrix gespeist; Containment-Hook liest den aufgelösten Wert | **keine Blockade mehr**: T4 (Auflösung + Attribution), T5 (Fehler), T9 (Warnung), T23 (Migration), T24 (Hook) sind vertraglich festgelegt |
| OQ-3 (ADR-Naming) | `ADR-<NNN>-<slug>.md` vs. `ADR-NNN_kurztitel.md`; ist Naming konfigurierbar? | **DECIDED 2026-11-09 (D3):** Naming pro Klasse, geschlossene Token-Liste (Spec §3.2.1); ADR-Default `ADR-{nnn}_{slug}.md` (regelkonform, `se-cascade-adr-standard.md:10`); `legacy[]` akzeptiert `NNNN-…` und `ADR-NNN-…`; unbekannte Tokens = `naming-invalid` | **keine Blockade**: T1/T2/T4/T5/T15/T23 |
| OQ-4 (SE-Wurzel) | `SE` (Code `config.py:2273`) vs. `docs/se` (Regeltext `taxonomy:10`) | **DECIDED 2026-11-09 (D4):** Default bleibt `SE`, keine Migration; Regeltext verweist auf `{{ARTIFACT_SE_ROOT}}`; `docs/se/**` in `legacy[]` | **keine Blockade**: T2 (Legacy-Muster), T4 (`test_se_root_default_is_SE`), T20 (Regeltext) |
| OQ-6 (unmanaged `docs/` + `docs/issue-labels.md`) | 8 Unterbäume: `legacy[]` oder „unmanaged"? Und wo lebt die #1188-Datei? | **entschieden (D-8):** `docs/superpowers/*` + `docs/conclusions` in `legacy[]`; die übrigen sieben als **`unmanaged[]`** (kein Block, keine Warnung, keine Klasse, keine Variable). **`docs/issue-labels.md` → `project-docs.files.issue-labels`**; **`.meta-config/issue-labels-state.json` → `unmanaged[]`** (#1188 braucht kein zweites Schema-Update) | kein Blocker (T1/T2-Liste); bei „legacy" entstehen Dauerwarnungen (F-3) |
| **OQ-7** (`standalone.py`) | Zielmatrix RVW2-X-01 nennt `scripts/lib/standalone.py` **nur bei #1187**; T6 braucht dort die 54 Framework-Defaults | **DECIDED 2026-11-09 (D2): die D-9-Ausnahme bleibt.** #1186 behält den additiven Fallback-Block; #1187 bleibt Datei-Federführer; die Reihenfolge #1187 → #1186 verhindert einen Parallel-Edit | **keine Blockade**: T6 bleibt unverändert, kein Reviewer-Vorbehalt, kein Follow-up |

**Zusätzliche Plan-Präzisierung (keine Spec-Änderung):**
`scratch`/`state` haben schema-seitig **kein** `mode`-Feld
(`artifactEphemeral`/`artifactState`, Spec §4.1). Die `_MODE`-Variablen
werden für sie als Konstante `files` exportiert (K-1, T6), damit §3.4
(„`{{ARTIFACT_<KLASSE>_MODE}}`") und das Schema widerspruchsfrei bleiben.

---

## 14. Self-Review

- **Jeder Task mappt auf genau eine Rolle:** T1–T3, T5–T12, T14, T15, T17,
  T18, T23, T24 = `developer`; T4, T16 = `senior-developer`; T19 =
  `frontend-component-engineer`; T13, T20 = `technical-writer`; T21 =
  `tester`; T22 (Follow-up) = `developer`. (T4 ist `senior-developer`, nicht
  `developer`; in §2.2 bündeln T1/T3 bzw. T17/T18 nur eine Datei, nicht eine
  Rolle.)
- **Jede Datei hat genau einen schreibenden Task** (Owner-Spalte §2); keine
  Dateiüberlappung innerhalb eines Meilensteins außer den bewusst
  sequenziellen Ketten `config.py` (T5 → T6 → T9), `admin-server.py`
  (T17 → T18; T22 liegt in einer späteren Welle), `sync_pipeline.py`
  (T8 → T15, Stage 14c nach Stage 13) und `docs/api/cli-reference.md`
  (T15 → T23, dokumentierte Kette). `hooks/1-generic/repo-containment*.sh` hat mit **T24**
  genau einen Owner; T16 legt eine **neue** Datei an und fasst sie nicht an.
- **AC-Präzisierungen sind ausgewiesen:** AC-03/05/07/09/13 sind in §10 und in
  Spec §6.3 (Revision 2: eigene Unterabschnitte mit Ankern) als Neuinterpretation
  markiert, jede mit benanntem Test und Grund; der Issue-Wortlaut bleibt
  unverändert zitiert.
- **Reihenfolge-Schnitt (RVW2-1186-01):** T8 importiert `consistency.artifact_locations`
  **nicht**; die `legacy-write`/Marker-Assertions liegen vollständig in T14. Das M2-Gate
  enthält deshalb nur scaffold-lokale Tests.
- **Baseline statt mtime (RVW2-1186-02):** `legacy-write` vergleicht gegen
  `baseline.legacy_files` aus Stage 14c (T15), nicht gegen mtime; fehlende Baseline ist
  fail-open (0 Findings + eine stderr-Zeile).
- **`unmanaged[]` erzeugt keine Klasse und keine Variable (D-8):** AC-12 bleibt bei 14 + 9;
  `.meta-config/issue-labels-state.json` (#1188) und die sieben Doku-Unterbäume sind
  deklariert, aber weder gesperrt noch gewarnt.
- **Jedes Akzeptanzkriterium ist messbar:** AC-01…AC-16 sind in §10 auf
  benannte Tests abgebildet; jede Zeile nennt Testname oder Gate.
- **`pipeline_stages` vorhanden** (`implement: 3` — Schritt 3 = „Test
  (pass)" je Task, wie im Präzedenzplan
  `docs/plans/2026-10-24-tmp-sink-injection-plan.md:96-98`).
- **D1–D4 sind als Entscheidung eingearbeitet (Rev. 4):** Scratch hat **eine** Quelle mit
  Migrations-Alias, Gleichheitszwang und **einer** Deprecation-Warnung (T4/T5/T9/T23), der
  Containment-Hook liest die aufgelöste Datendatei (T24); D2 bestätigt die
  Standalone-Ausnahme; Naming ist token-validiert (T1/T2/T4/T5); `SE` bleibt Default mit
  `{{ARTIFACT_SE_ROOT}}`-Regeltext und `docs/se/**` in `legacy[]` (T2/T4/T20).
- **Keine Doppelquelle bleibt übrig:** `TMP_SINK_PATH == ARTIFACT_SCRATCH_DIR` (T9),
  `SE_BASE_DIR == ARTIFACT_SE_ROOT` (T6), `state` ist Projektion (T4) — jede Zeile hat
  einen Test, der den zweiten Pfad ausschließt.
- **Naming erzeugt keine 55. Variable:** die Menge aus §3.3 bleibt exakt 54 (T6/T7);
  `naming` erscheint nur im Status-JSON (T15).
- **Keine Platzhalter/TBD:** jede Code-Referenz hat einen auf `aaed14c2`
  verifizierten `datei:zeile`-Anker; OQs sind entschieden oder mit
  Blockadewirkung markiert.
- **Nicht-Ziele respektiert:** kein Verschieben/Löschen, kein Retention-
  Daemon, keine SE-Zellstruktur-Änderung, keine Knowledge-Pfade, keine neuen
  Endpunkte, keine always-on-Rule, keine Provider-Verzweigung, keine
  Per-Rollen-Overrides, keine Auto-Reparatur.
- **Branch-Guard:** Implementierung nur auf `feat/1186-artifact-locations-matrix`;
  dieser Plan liegt auf dem Doku-Branch `docs/config-wave-plans-1181-1188`.

---

## 15. Review-Auflösung (2026-11-09)

Alle Befunde des Reviews vom 2026-11-09 sind eingearbeitet. Damals **DRAFT**, seit 2026-11-09 **APPROVED**.
Drei Punkte sind ausgelagert: **#1198, #1199, #1200** (real angelegt; Zuordnung der
Nummern zu den drei Punkten trägt das Wave-Overview nach — keine erfundene Titel-Zuordnung).

| Befund-ID | Änderung | Stelle |
|---|---|---|
| **RVW-1186-01** (BLOCKER) | `MARKER_FILENAMES`-Ausnahme: Scaffold-Marker sind in `artifact_scaffold`, `legacy-write` und Hook ausgenommen; `docs/conclusions` bleibt `legacy[]`; AC-09 präzisiert (Inhalt vs. Marker, Meldung immer / Block bei Aktivierung); zwei Null-Fund-Tests (`test_legacy_markers_produce_no_legacy_write`, `test_clean_repo_sync_produces_no_legacy_write`); Hook-Begründung für `enabled_by_default: false` explizit | T8, T14, T16, §1 Nr. 5, §9 R2/R18, §10 |
| **RVW-1186-02** (MAJOR) | Variablen-Menge exakt berechnet: **54** Namen (13 DIR + 9 SE-DIR + 4 SE-Projektion + `SE_ROOT` + 4 `_FILE` + 23 `_MODE`), tabelliert in Spec §3.4; Test `derive_builder_vars ⊆ _BUILTIN_VARS`; Builder-Totalität auf `{}`; „26 Namen" ersetzt; `_UNREGISTERED_BUILDER_RATCHET` bleibt unangetastet | T6, T7, §2.2, §6.1 |
| **RVW-1186-03** (MAJOR) | AC-05 verengt: Resolver/Scaffold/Consistency/Status je Modus getestet, **kein** `{{#if}}`-Gate (Renderer-Fakt `variables.py:498-508`, `:570-598`); Tooling-Konsequenz als F-4 dokumentiert | T4, T14, T21, §7.3, §10, §12 |
| **RVW-1186-04** (MAJOR) | `fallback-parent` als Schema-Feld (Enum der 23 Klassen) in T1, Validator-Regel + zweiter Fehlercode in T5; `mode-parent-missing` nennt das Feld | T1, T5, §6.1 (`ResolvedClass.fallback_parent`) |
| **RVW-1186-05** (MAJOR) | `reports.path` bleibt `docs/reports`; SE-Pfade über `resolve_se_projection` (4 abgeleitete Variablen); `se-critic.md:110,114` auf die Projektionen umgestellt; `SE/VV/**` in `legacy[]`; `reports.se-path` als Nicht-Ziel | T4, T6, T11, §3.1, §6.1, §13 (OQ-1) |
| **RVW-1186-06** (MAJOR) | Lese-/Schreib-Literal getrennt: `literal-path` prüft Schreibpositionen (Cue-Liste), Read-OK-Ratchet (2 Zeilen: `knowledge-migrator.md:39,50`, shrink-only, Test); `documenter.md:81` in T10 aufgenommen; Grep-Gate verengt; `docs/codebase_overview.md` → `docs/CODEBASE_OVERVIEW.md` | T10, T14, §2.2 |
| **WARN Header** | `Klasse: XL` steht jetzt auch im Spec-Kopf (die Plan-Kopfzeile hatte sie bereits) | Spec-Kopfblock |
| **WARN `kind`** | Vereinheitlicht: **kein** `array of string` mehr; geschlossenes Enum (`$defs/artifactKind`, 20 Werte), Klassen-Ebene = Menge (`items.enum` + `uniqueItems`), Artefakt-Ebene = Skalar; `kind-invalid` ergänzt; `ResolvedClass.kind` → `kinds` | T1, T4, T5, §6.2 |
| **WARN Create/Modify** | §2.1 trägt eine explizite `Status`-Spalte (alle `Create`), §2.2 ebenso (alle `Modify`); jede `**Datei:**`-Zeile nennt `Create`/`Modify` je Datei; die zwei neuen Szenario-Dateien sind in §2.1 als `Create` gelistet | §2.1, §2.2, T1–T22 |
| **Querschnitt: Reihenfolge** | Kanonisch `#1187 → #1186 → #1188 → #1181`, danach `#1141`; Whitelist-Ableitung als T22 ans Ende; „#1141 vor oder im selben PR" gestrichen | Kopf „Voraussetzungen", §4, §10, §11, §13 |
| **Querschnitt: Konfliktmatrix** | #1181 in die Stage-14-Zeile; neue Zeilen `scripts/lib/variables.py` (§2.3, ohne Edit), `scripts/lib/standalone.py` (T6), `tests/scenarios/registry.md` (T21), beide vollständigen `project.yaml.example` (T20), `docs/issue-labels.md` | §2.2, §2.3, §11 |
| **Querschnitt: Szenario-IDs** | `94` = #1181, `95–98` = #1187; #1186 belegt `99-artifact-locations-matrix` (+ `asserts/99-…sh`), Phase H prüft die Registry | T21, §2.1, §11 |
| **Querschnitt: `docs/issue-labels.md`** | als viertes `project-docs`-File deklariert (`ARTIFACT_ISSUE_LABELS_FILE`), damit der Managed-Tree-Hook die #1188-Datei nicht blockt; OQ-6 erweitert; #1188 läuft nach #1186 | T1, T6, T8, §13 (OQ-6), §11 |
| **AC-Neuinterpretationen** | AC-03 (Schreibposition + Ratchet), AC-05 (Resolver statt Gate), AC-07 (T17 jetzt / T22 Follow-up), AC-09 (Inhalt statt Marker), AC-13 (Enum) — je mit Test und Grund | §10, §7.3 |

### 15.1 Runde 2 — Revision 2 (2026-11-09)

Formale Blocker und fachliche Befunde der zweiten Korrekturrunde. Damals **DRAFT**, seit 2026-11-09 **APPROVED**.

| Befund-ID | Änderung | Stelle |
|---|---|---|
| **Formal `revision`** | Frontmatter `revision: "2"` + Kopfzeile `Revision: 2 (Review-Auflösung 2026-11-09)` ergänzt | Frontmatter, Kopf |
| **RVW2-1186-01** (MAJOR) | T8 rief `check_artifact_locations` auf (Modul entsteht erst in T14); M2-Gate enthielt dadurch nicht-grün-fähige Tests. Fix: nur `MARKER_FILENAMES` in T8 (`test_marker_filenames_constant_covers_scaffold_markers`), alle `legacy-write`/Marker-Fälle nach T14; M2-Gate auf scaffold-lokale Assertions geschnitten | T8, T14, §4 (M2/M4), §9 R18, §14 |
| **RVW2-1186-02** (MAJOR) | AC-09 hatte keine deterministische Basis („mtime > letzter Sync" war undefiniert). Fix: Baseline = `baseline.legacy_files` aus `.meta-config/artifact-locations.resolved.json` (Stage 14c), **kein** mtime-Vergleich, fail-open bei fehlender Baseline; Tests `test_legacy_write_uses_baseline_not_mtime`, `test_baseline_missing_fails_open` | T14, T15, §6.4, §9 R19, §10 |
| **RVW2-1186-03** (MINOR) | „70/98" gepinnt → **relative** Assertion `test_provider_context_count_does_not_grow`; HEAD ist 83/98 (84/101), Zahl als Notiz dokumentiert | T13, §10 (H-4) |
| **RVW2-1186-04** (MINOR) | T20 nennt **beide** vollständigen Beispiele (`templates/…`, `howto/…`); `test_example_config_has_artifact_block` parametrisiert + `test_example_configs_stay_in_sync` | T20, §2.2 |
| **RVW2-1186-05** (INFO) | „Vier Stufen" → „Fünf Stufen" (Spec §3.3; die Liste hatte fünf Einträge) — **durch K3 ersetzt:** vier Wertequellen + Source-Attribution (`project-preset`) + Zustand (`disabled`); §3.3 und §7.5 sind entsprechend umgestellt | Spec §3.3, **§7.5**, §10 (AC-15) |
| **RVW2-X-01** (MAJOR) | Konfliktmatrix auf die Zielmatrix gezogen: `agent_sync.py` (#1187/#1188/#1181), `sync_pipeline.py` (#1186/#1181), `variables.py` (#1187), `standalone.py` (#1187 + begründete Ausnahme D-9), beide `project.yaml.example` (#1187/#1186/#1188/#1181), `registry.md` (#1186/#1181/#1187), `docs/issue-labels.md` + `.meta-config/issue-labels-state.json` (#1188 erzeugt, #1186 klassifiziert) | §2.2, §2.3, §11, §13 (OQ-7) |
| **RVW2-X-02** (MAJOR) | Neue `unmanaged[]`-Liste (D-8): `.meta-config/issue-labels-state.json` und sieben Doku-Unterbäume; T1 (Schema), T2 (Preset), T4 (`ResolvedMatrix.unmanaged`), T5 (`unmanaged-intersect`), T15 (Datendatei + `--status-artifacts`), T16 (Hook allow), T18 (400); `docs/issue-labels.md` bleibt `project-docs`. **K1:** die Kategorie `project-state` ist gestrichen | §3.2a, T1/T2/T4/T5/T15/T16/T18, §9 R20, §10, §11 (#1188) |

### 15.2 Szenario-Konflikte K1–K8 (2026-11-09)

Auflösung der acht Befunde aus `.tmp/scenario-config-wave/RESULT.md`, konsistent über alle vier
Wave-Specs/-Pläne. Damals **DRAFT**, seit 2026-11-09 **APPROVED**.

| Befund | Änderung | Stelle |
|---|---|---|
| **K1** (BLOCKER) | `.meta-config/issue-labels-state.json` ist `unmanaged[]` (Negativ-Deklaration); `project-state` gestrichen, `classes` bleibt 23, AC-1186-12 unverändert | §2.3, §3.2a, §11 (#1188) |
| **K2** | **Nicht betroffen**: kein Separator-Schlüssel im Artefakt-Vertrag | geprüft: §3.1 |
| **K3** (MAJOR) | Vier Wertequellen plus Source-Attribution `project-preset:<name>` und `disabled`; die Projekt-Preset-Wahl ist keine eigene Präzedenzstufe. §7.5 prüft 4 Quellen + 2 Attributionen (`test_project_preset_is_attribution_not_a_level`) | Kopf (Architecture), §1 Nr. 3, §2.1, §6.1 (`SOURCE_PROJECT_PRESET`), **§7.5**, §10 (AC-15), T4 |
| **K4** | **Nicht betroffen**: kein `taxonomyAxis` | geprüft: §3.1 |
| **K5** | **Nicht betroffen**: keine Grant-Präzedenztabelle | geprüft: §6.1 |
| **K6** (NIT) | `$defs` bleibt; das Ist-Schema nutzt es bereits (`schema.json:2` + `:2855`); Plan nennt `$defs/artifactKind`/`artifactClassName` unverändert | §2.2, T1, T3 |
| **K7** | **Nicht betroffen**: alle Schlüssel kebab-case in `artifact-locations` | geprüft: §3.1 |
| **K8** | **Nicht betroffen**: kein bestehender `_KEYS`-Block | geprüft: §6.1 |

## 16. Entscheidungsprotokoll (2026-11-09)

Vom User entschieden; Markierung `DECIDED 2026-11-09` steht zusätzlich am jeweiligen Task.
Diese vier sind **Fach-Entscheidungen** und zu unterscheiden von den internen
Design-Entscheidungen `D-6` (conclusions), `D-7` (`vv`), `D-8` (`unmanaged`) und `D-9`
(Standalone-Ausnahme, hier als **D2** bestätigt).

| D-Nr | Frage | Entscheidung | betroffene Stellen |
|---|---|---|---|
| **D1** | OQ-5 — Kopplung `scratch` ↔ `repo_containment.tmp-sink.path` | **Eine** Quelle: `artifact-locations.classes.scratch.path`. `tmp-sink.path` = Legacy-Alias (nur gelesen, solange die Klasse fehlt); beide gesetzt ⇒ Werte müssen gleich sein, Divergenz = **harter Fehler** `artifact-locations.scratch-sink-divergence`; Deprecation-Warnung mit Migrationshinweis; `TMP_SINK_PATH` bleibt, wird aber **aus der Matrix** gespeist; Containment-Hook liest den **aufgelösten** Wert statt des Roh-Keys. Migration `--migrate-artifact-aliases [--write]`. Die „Vorrang + ERROR"-Formulierung ist ersetzt. | §3.1 (Scratch-Zeile), §3.2, §3.3, §6.1 (`SOURCE_PROJECT_ALIAS`, `resolve_scratch_path`), **T4**, **T5**, T9, T15, **T23 (neu)**, **T24 (neu)**, §8, §9 R11/R21/R23, §10, §13 OQ-5 |
| **D2** | OQ-7 — gilt die Zielmatrix RVW2-X-01 für `scripts/lib/standalone.py` ausnahmslos? | **Nein — die D-9-Ausnahme bleibt.** #1186 behält den additiven Standalone-Fallback (54 Framework-Defaults), #1187 bleibt Datei-Federführer, Reihenfolge #1187 → #1186 verhindert Parallel-Edits. Kein Follow-up. | §2.2 (`standalone.py`), §2.3, **T6**, §10 (D-Tabelle), §13 OQ-7 |
| **D3** | OQ-3 — ADR-Naming und Konfigurierbarkeit von `naming` | Naming ist **pro Klasse** konfigurierbar: String-Pattern mit **geschlossener Token-Liste** `{class} {date} {slug} {kind} {n} {topic} {scope} {nnn} {level} {folder}`. Projekt-Default ADR: `ADR-{nnn}_{slug}.md` (regelkonform, `se-cascade-adr-standard.md:10`). `legacy[]` akzeptiert zusätzlich `NNNN-{slug}.md` und `ADR-{nnn}-{slug}.md`. Unbekannter/nicht anwendbarer Token = `artifact-locations.naming-invalid`. | §3.1 (Tabelle + Token-Kanon), §6.1 (`resolve_naming`/`validate_naming`), §6.2 (`$defs/artifactNaming`), **T1**, **T2**, **T4**, **T5**, T15, T20, §8, §9 R22, §10, §13 OQ-3 |
| **D4** | OQ-4 — `SE` oder `docs/se` als SE-Wurzel-Default | Default bleibt **`SE`**, keine Migration. `rules/1-generic/se-cascade-artifact-taxonomy.md` verweist auf `{{ARTIFACT_SE_ROOT}}` statt auf ein Literal; `docs/se/**` ist `legacy[]`-Muster (kein Default, kein zweiter Pfad). | §3.2 (SE-Absatz), **T2** (Legacy-Muster), **T4** (`test_se_root_default_is_SE`), **T20** (Regeltext), §8, §9 R10, §10, §13 OQ-4 |

**Verbleibende offene Punkte (nicht entschieden, nicht blockierend):**

1. **Leaf-Schreibweise der SE-Projektion** (`ARTIFACT_SE_ADR_DIR` etc.): Spec §3.4 leitet
   `{ARTIFACT_SE_ROOT}/<leaf>` ab; die Taxonomie führt `ADR/` (Großbuchstaben,
   `se-cascade-artifact-taxonomy.md:15,61`), die Klasse `adr` heißt `docs/adr`. Empfehlung:
   Leaf bei der Umsetzung **wörtlich** aus der Taxonomie übernehmen und in T4 pinnen —
   keine Entscheidung in diesem Plan.
2. **Retention/Cleanup für `scratch`** bleibt Deklaration + Report (§8) und gehört zu
   #1150-Problem 2, nicht zu #1186.
3. **Wer den Dateinamen konkret erzeugt** (Rolle vs. CLI) bleibt Rollen-Verantwortung; die
   Matrix liefert nur Muster + Validierung (Spec §3.2.1 e).
