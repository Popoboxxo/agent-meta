# Bug Batch Implementation Plan

> Status: geplant
>
> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox syntax (`- [ ]`) for tracking.

**Goal:** Alle 21 offenen `bug`-Issues (20 distinkte `bug`-Labels + #1074 als Zwilling von #1092; #1042 ist Duplikat von #1041 und wird geschlossen) stehen als 39 kleinste testbare Einheiten (Tasks) in 9 Feature-Branches/PRs und 4 Wellen (0-3) abarbeitbar fest; alle Entscheidungen sind im Abschnitt "Entscheidungen (Calls)" getroffen.
**Architecture / Strategie:** Es gibt KEINE separate Spec; dieser Plan trägt die Entscheidungen (Abschnitt "Entscheidungen (Calls)"). Pro Cluster ein Branch und ein PR; innerhalb eines Branches seriell bei gleicher Datei, ownership-disjunkt parallel nur wo `Files:` sich nicht überlappen. Jeder PR endet mit einem Close-out-Task (Rebaseline nach Rebase auf aktuellen `main`, CHANGELOG, Self-Review durch `code-reviewer`, PR-Vorbereitung durch `git`).
**Tech Stack:** Python >= 3.9 (nur stdlib), pytest, Bash-Hooks mit eingebettetem Python, Markdown-Templates mit `{{VAR}}`/`{{#if}}`, YAML/JSON-Config.
**Spec:** keine (Entscheidungen in diesem Plan; spec-id entfällt; DoD-Preset `rapid-prototyping`). Eingangsquellen: `.tmp/bug-batch-inventory.md`, `.tmp/bug-verify-A.md`, `.tmp/bug-verify-B.md`, `.tmp/bug-verify-C.md` (Stand main `c6d120dc`).

## Global Constraints

- Python-Stdlib only; Python >= 3.9 (kein `X | Y` zur Laufzeit ohne `from __future__ import annotations`, kein `match`).
- Provider-Agnostik: Unterschiede nur über Config-Keys/Capability-Flags, nie `if provider == "Name"` (Skill `provider-agnostic`).
- Neue lib-Module <= 600 Zeilen (`scripts/lib/yaml_patch.py`, `mcp_health.py`, `settings_dirs.py`); Alt-Module über 600 Zeilen (`sync_pipeline.py`, `config.py`, `context.py`, `isolation.py`, `generated_file_drift.py`, `admin-server.py`) wachsen nur um Aufruf-/Guard-Zeilen.
- Conventional Commits, Englisch, erste Zeile <= 72 Zeichen, Imperativ, kein führendes BOM; Betreff VOR dem Commit zählen (`printf '%s' "<subject>" | wc -c` <= 72). Commit-Trailer laut Session-Attribution. Pro Issue im Body eine eigene Zeile `Closes #<n>` (bei Kommaliste schließt nur die erste).
- Dokumente Deutsch, Code/Commits/Identifier Englisch, `README.md` Englisch.
- Kein `/tmp`-Literal. Testkommando: `python3 -m pytest <datei>::<test> --basetemp="$PYTEST_BASETEMP"`. `PYTEST_BASETEMP` ist der Wert des Tokens `{{PYTEST_BASETEMP}}` aus `.meta-config/project.yaml` (`variables.TEST_COMMANDS`, Zeile 194; Quelle `repo_containment.tmp-sink.system-temp-exception`) und wird vor Start einmal in der Shell gesetzt; kein Basetemp im Arbeitsbaum.
- Template-Änderungen (`agents/1-generic/*.md`): `version` bumpen, `based-on`-Pin der betroffenen `agents/2-platform/*`-Overrides nachziehen (Change Checklist, `rules/2-platform/agent-meta-conventions.md` Z.111-123), AC-01-Baseline `tests/fixtures/ac01-baseline/hashes.json` rebaselinen (`python tests/test_ac01_render_identity.py --write`, Rebaseline-Log im Docstring von `tests/test_ac01_render_identity.py` ergänzen), Standalone-Export neu rendern (`python scripts/sync.py --render-standalone`; Gate `tests/test_standalone_export_in_sync.py`), `slimming-golden`/`compact-golden` laufen lassen und nur bei Diff nachziehen.
- Hook-Änderungen (`hooks/1-generic/**`): Header `# version:` bumpen und `# changelog:`-Eintrag VORN ergänzen (Header ist eine einzelne Zeile, siehe `hook_common.sh` Z.3-5); Hash-Nachzug über AC-01-Rebaseline.
- Verifikation an Template-/Config-/Sync-Tasks zusätzlich: `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`.
- Kein `isolation: "worktree"`. Keine Änderungen auf `main`. Push/PR nur durch die Rolle `git`; Merge nur durch den Nutzer. Workers delegieren nie an `orchestrator`.
- Geteilter Arbeitsbaum: Branch-Wechsel nur bei freiem Baum (`git status` ohne eigene Änderungen); die vorhandenen Modifikationen an `.meta-config/context-hashes.json` und `.meta-config/generated-file-hashes.json` sind Sync-Artefakte, werden in keinem Bug-Commit mitgenommen und vor einem Wechsel von der Rolle `git` gestasht/geklärt. Schreibende Agenten und Branch-Wechsel laufen seriell.

## Review Focus

Fünf Fälle, die kein Issue-Text direkt prüft, aber falsch brechen lassen. Jeder hat einen benannten Test.

| # | Eingabe / Fehlerfall | Erwartung | Test (Task) |
|---|---|---|---|
| R1 | #1050: ungeschlossene `{` in langem Funktionskörper und 60000 Wiederholungen von `f(){ x} ` | bleibt fail-closed (Exit 2 / Verdict `1`) und linear (< 1 s); `f(){ echo hi; };f` bleibt erlaubt | `test_fork_bomb_nesting_keeps_fail_closed_and_linear` (A2) |
| R2 | #1041: Config `push.recurseSubmodules=on-demand`, aber CLI `--recurse-submodules=no`; Config `check`/`no` | explizites Flag gewinnt => Exit 0; Config `check`/`no` => Exit 0; ohne Submodule => Exit 0 | `test_1041_cli_flag_overrides_config_and_inert_values` (A3) |
| R3 | #1081: echte manuelle Änderung an generierter Datei vs. stale Baseline; `--dry-run` | echte Änderung wird aus `pre_text` gesichert + WARN; stale Baseline => kein Backup/WARN; `--dry-run` schreibt nichts | `test_real_edit_backed_up_from_pre_text`, `test_dry_run_writes_nothing` (C4) |
| R4 | #1091: schema-invalider `auto_commit` bei `sync` vs. `--validate` | `--validate` rc=1; `sync` rc=0 mit Allowlist `mode=off`, `eligible_roles=[]` + WARN; gültige Config unverändert | `test_sync_rc0_but_allowlist_fail_safe` (D3), `test_valid_config_unchanged` (D2) |
| R5 | #1095: `.agent-meta` -> Symlink, dessen `config` selbst nach außen zeigt; Schreiben über Symlink | Lesen außerhalb `config/`-Unterbaum bleibt `SecurityError` (403); Schreiben verboten; `..`-Traversal unverändert geblockt | `test_symlink_target_outside_config_still_blocked`, `test_write_via_symlink_blocked` (D1) |

---

## Entscheidungen (Calls)

Quellen: Empfehlungen aus den Verify-Reports (A/B/C) übernommen; Widersprüche vom Plan entschieden. Veto-Folge = was sich ändert, wenn der Nutzer die Entscheidung kippt.

| # | Entscheidung | gewählte Option | Begründung | Alternative | Veto-Folge |
|---|---|---|---|---|---|
| D1 | Scope "21 Bugs" | 20 `bug`-Issues + #1074 (Zwilling von #1092, gleiche Defektklasse); #1042 nur schließen; #1085/#1086/#1051 raus | Der Inventar-Zähler nennt 21 distinkte, die Tabelle zeigt aber nur 20 `bug`-Zeilen (+#1042 als Duplikat); #1074 ist der 21. Fix im selben Writer | #1085(a) Tool-Hooks-Auto-Enable mitnehmen | #1085 braucht eigenen Task (M, Verhaltensänderung Bestandsprojekte) |
| D2 | #1042 | als Duplikat von #1041 schließen (Welle 0, Rolle `git`) | Titel/Inhalt identisch | beide behalten | Nur Kommentar-/Close-Aufwand |
| D3 | #1078 Tool-Liste | 17 neue Namen in `hook_known_tool_name`: `ToolSearch, TaskCreate, TaskUpdate, TaskList, TaskGet, Monitor, ScheduleWakeup, CronCreate, CronDelete, CronList, EnterPlanMode, PushNotification, RemoteTrigger, SendUserFile, Artifact, ArtifactComments, ArtifactData`; `EnterWorktree`/`ExitWorktree` bleiben geblockt; kein warn+allow für Unbekannte; kein Konsistenz-Check | Fail-closed bleibt; keine maschinenlesbare Provider-Toolliste im Repo (kein Treffer in `config/`) | Allow-Liste aus `ai-providers.yaml` ableiten | Neue Config-Quelle + Parity-Test; Folge-Issue |
| D4 | #1050 Fork-Bomb | echtes Klammer-Nesting im 512-Zeichen-Fenster | ~12 Zeilen, linear, schließt dokumentierte Lücke 5 | Lücke akzeptieren | Lücke 5 in `branch-guard.md` bleibt, Task A2 entfällt |
| D5 | #1041 | `config_recurses(p)` (effektive Config + `override`-Substring), CLI-Flag gewinnt, Tag-only-Abkürzung nur ohne Config-Recursion; Foreign-Repo bleibt dokumentierte Restlücke | nutzt vorhandenes `git_config()`/`override`, keine Ausführung von Nutzerinput | nur dokumentieren | Bypass `git push` mit globaler on-demand-Config bleibt |
| D6 | #1071 | Templates konditionieren (`ROLE_<R>_ACTIVE`), Checker unverändert, kein `dispatch_allow` | Spec PR D (#993) verlangt "condition prose on the active set"; Header-Heuristik kann Tabellentypen nicht unterscheiden | `dispatch_allow`/Checker-Regel | Fragile Checker-Heuristik, blendet echte Dispatches aus |
| D7 | #1083 | neuer Check `active-set.dangling-mention-frontmatter` (WARNING); `tester`/`data-engineer` description rollen-neutral statt `{{#if}}` im Frontmatter | Frontmatter-Conditionals sind parser-riskant | Conditional im Frontmatter | Parserrisiko, mehr Template-Hunks |
| D8 | #1082 | Code-Span/Fence im Post-Render-Check überspringen; `placeholder_allow` bleibt `[]`; `KEY_PATTERNS`-Prosa in `project.yaml` in Backticks | kleinste Änderung; echte Unresolved fängt `variables.substitute` bereits | Allow-Liste / Check vor Render | Wartungsliste bzw. Doppellogik |
| D9 | #1072 | Warnung entfällt, wenn die matchende Regel im managed-Block liegt; Marker-Konstanten nach `gitignore.py`, `context.py` importiert sie | kein Import-Zyklus, belegt statt vermutet | zweite Absicherung | Weiter FP für `custom_entries` |
| D10 | #1073 | `.meta-config/platform-defaults.resolved.yaml` unbedingt in managed `.gitignore` (beide Zweige); `git rm --cached` dieses Repos nur als Folge-Housekeeping | reiner Snapshot, kein CI-Vertrag | dokumentiert tracken | Datei bleibt im Index, Drift-Rauschen |
| D11 | #1081 | Baseline bleibt tracked; Drift-Entscheidung NACH den Writern (`resolve_drift_findings`); Prune count-only (3 neueste je Quelle, Alter ignoriert, Neuester bleibt immer) | `--check` in CI braucht committed Baseline; AND-Policy erzeugte 409 Backups | Baseline gitignoren | `--check` verliert Baseline-Vergleich im frischen Checkout |
| D12 | #1084 | (a) Konstante `_AGENT_META_RUNTIME_ARTIFACTS={".guard-audit.log"}`; (b) Basenames aus `mcp-config.{committed-file,secrets-file}`; (d) Backup-only-Verzeichnis ist managed; (e) neuer Provider-Key `infra_known_names`; (c) Findings aller Provider ohne `has_rules` in den Report des ersten `has_rules`-Providers mit `[Provider]`-Tag | datengetrieben, Cap 10 bleibt | Managed-Index für (a); hartcodierte Namen für (e) | Cleanup könnte Audit-Log löschen / Namen im Code |
| D13 | #1091 | `--validate` rc=1; `sync` rc=0 mit fail-safe `mode: off` + WARN; kein Zeit-Grace | ungültige Config war schon dokumentiert ungültig; Sync darf Bestandsprojekte nicht neu brechen | alles hart rc=1 | CI-Bruch bei Consumern mit kaputter Config |
| D14 | #1074/#1092 | Top-Level-Segment-Patch `yaml_patch.patch_top_level`; Sync-Auto-Fill materialisiert nur `repo_containment` + `project.short` (+ übrige Strukturfelder), die 7 Preset-/Flag-Defaults nur bei `--fill-defaults`/`--init`; Round-Trip-Guard für `project` nur auf dem Fallback-Pfad (Voll-Dump) | ~120 Zeilen stdlib, selbstverifizierend, kein Parser; das Admin-UI hat keinen `__allow_lossy__`-Dialog | eigener Parser / ruamel; Guard auch für den Patch-Pfad | Hohe Fehlerfläche / Dependency-Verbot; Guard-Variante lässt Section-Edits mit Kommentaren per HTTP 400 scheitern |
| D15 | #1095 | Resolve-Fix nur im Fallback-Zweig für `config/`-Unterbaum des Framework-Links; Schreiben über Symlink verboten | Containment nicht aufweichen | UI-Keys verstecken | Framework-Defaults im Admin-UI unsichtbar |
| D16 | #1090 | zentrale `role_emitted_for_provider` in `active_set.py`; Entry-Point nur bei emittierter Rolle; dangling Nutzerwert nur WARN `opencode.default-agent.dangling`, kein Auto-Delete | eine Stelle, #1077-fähig; D1c "Nutzerwert gewinnt" | Auto-Delete | Zerstört Nutzerwerte |
| D17 | #1080 | Katalog `python3` (viz-logger + a2a-handoff) + Fallback-Tabelle; `mcp_health`-WARNs (`mcp.secret-empty`, `mcp.command-unresolved`); Reqogniloom-Variablen nur dokumentieren; honcho kein Fehler; Skill-Kopplung nicht | `MCP_`-Präfix ist Katalogkonvention, Plugin-Schema gehört Dritten | Umbenennen | `secrets.local.yaml` bestehender Projekte bricht |
| D18 | #1094 | Verzeichnis folgt Name (`roles/agent-meta-<role>/`); Template-description vor role-defaults; Basis-Templates ohne role-defaults-Eintrag => Tier `balanced` ohne Warnung; 8 deutsche Template-Descriptions als Folge-Issue | Namespace gegen Kollisionen; Massen-Template-Risiko vermeiden | Name = Verzeichnis ohne Präfix | Kollisionsrisiko im Hermes-Register |
| D19 | #1093 | `{{#if GIT_REMOTE_URL_SET}}` + `GIT_REMOTE_URL_SET` in `config.py`/`standalone.py`/`placeholders.py` | vorhandener `*_SET`-Mechanismus | Defaulttext "(no remote configured)" | Rauschen in jedem Agent |
| D20 | #1079 | Option C: `additionalDirectories` additiv in `settings.local.json` (gitignored) via Provider-Key `settings-allow-dirs-key`; Option A (`.tmp/pytest`) abgelehnt (ADR-03, 16-GB-Vorfall) | Pfad enthält Username/OS-Temp, gehört nicht in committete `settings.json` | `settings.json` | Pfad leakt in geteilte Datei |
| D21 | #1032 | kein Code-Fix; Docstring + Pin-Test; Issue mit Evidenz-Verweis (`docs/analysis/evidence/2026-09-30-runtime-claude-antigravity.md` §2.1) schließen | AGY-Doku: cwd = Verzeichnis der `hooks.json`; Env-Variable unbekannt | Anker per `git rev-parse` | bricht außerhalb Git/Worktrees |
| D22 | #971 | nur Verifikationslauf + Schließen/Tracking (#977, Plan-Status) | im Code erledigt (AC-11/12/19 getestet) | neues Paket | Bei rotem Lauf wird der rote Fall der Bug |
| D23 | Branches/PRs | 9 PRs: A, B, C1, C2, D1, D2, E, F, G; Merge-Reihenfolge A, B, E, C1, F, D1, G, C2, D2 | P1/Security zuerst; Template-Rebaselines früh, 3 große Write-Pfad-Änderungen zuletzt | ein Mega-PR | Review-Aufwand und Rebaseline-Kollisionen |

---

## Batch-Strategie

**Wellen** (Reihenfolge/Unabhängigkeit; physisch schreibt im geteilten Arbeitsbaum immer nur EIN Branch gleichzeitig, siehe Global Constraints).

| Welle | Inhalt | Warum |
|---|---|---|
| 0 | G0: #1042 als Duplikat schließen (Rolle `git`/`meta-feedback`, nicht ausführen in diesem Plan) | kein Code |
| 1 (Quick-Wins, disjunkte Dateien) | A1-A3 (#1078 -> #1050 -> #1041), C1-C2 (#1072+#1073), D1 (#1095), E5 (#1094), F1 (#1093), G1 (#971), G2 (#1032) | klein, eindeutig, Security-Hooks zuerst |
| 2 (mittel) | B1-B3 (#1071 -> #1083 -> #1082), D2-D3 (#1091), E1-E4 (#1090, #1080), G3-G4 (#1079) | mehrere Dateien, #1090/#1071 sind P1 |
| 3 (Design) | C4-C8 (#1081 -> #1084), D5-D7 (#1074+#1092) | Verhaltens-/Contract-Entscheidungen, größtes Risiko |

**Serielle Abhängigkeiten (gleiche Datei):** `hook_common.sh` #1078 -> #1050; `dod-push-check.sh` #1041 (nach A2 wegen gemeinsamer Rebaseline); `consistency/active_set_refs.py` #1083 -> #1082 (#1071 zuvor, gleiche Template-Dateien nicht); `gitignore.py` #1072 + #1073 in einem PR; `admin-server.py` #1095 -> #1092; `config.py`/YAML-Writer #1074+#1092 -> nach #1091 nicht nötig (andere Dateien), aber nach #1095; Drift #1081 -> #1084 (`sync_pipeline.py`). `sync_pipeline.py` wird von #1080, #1079, #1091, #1081, #1074 berührt (verschiedene Hunks): kein Parallel-Merge, Rebase vor jedem Merge.

**Branch-/PR-Zuordnung**

| PR | Branch | Issues | Welle |
|---|---|---|---|
| A | `fix/hooks-guards` | #1078, #1050, #1041 | 1 |
| B | `fix/consistency-false-positives` | #1071, #1083, #1082 | 2 |
| C1 | `fix/gitignore-managed-block` | #1072, #1073 | 1 |
| C2 | `fix/drift-false-positives` | #1081, #1084 | 3 |
| D1 | `fix/admin-symlink-and-validate` | #1095, #1091 | 1/2 |
| D2 | `fix/yaml-comment-preserving-writer` | #1074, #1092 | 3 |
| E | `fix/provider-mcp-opencode-hermes` | #1090, #1080, #1094 | 1/2 |
| F | `fix/git-template-empty-remote-url` | #1093 | 1 |
| G | `fix/test-basetemp-allowlist` | #1079, #1032, (#971 nur Verifikation) | 1/2 |

**Close-out-Protokoll (jeder PR, letzter Task):**
1. Rebase auf aktuellen `main` (Rolle `git`), Konflikte nur in `CHANGELOG.md [Unreleased]` / `hashes.json` erwartet.
2. Rebaseline NACH dem Rebase: `python tests/test_ac01_render_identity.py --write`, danach `git diff --stat tests/fixtures/ac01-baseline/hashes.json` und manuell prüfen, dass nur die im Task genannten Schlüssel geändert sind (sonst Ursache klären, nicht committen). Entfällt, wenn der Task "kein Rebaseline" festlegt.
3. `CHANGELOG.md` unter `## [Unreleased]` je Issue ein Eintrag (Prefix `Fixed:`; Verhaltensänderungen mit `behavior change:`).
4. Volllauf `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate && python3 -m pytest tests/ --basetemp="$PYTEST_BASETEMP"`.
5. Self-Review durch `code-reviewer` (Requirement-Treue vor Qualität); Findings beheben.
6. `git` bereitet PR vor (Push, `gh pr create`), jedes `Closes #n` in eigener Zeile; KEIN Merge.

**Kollisionen paralleler Branches:** `CHANGELOG.md [Unreleased]` (Merge-Konflikt in der Regel trivial, beide Einträge behalten); `hashes.json` (jeder PR rebaselined erst nach Rebase auf main); Hook-Versionen (`hook_common.sh` nur PR A, `dod-push-check.sh` nur PR A, keine Versionskollision); Template-Versionen (`tester.md` nur PR B, `git.md` nur PR F, `orchestrator.md`/`senior-developer.md`/`meta-feedback.md` nur PR B).

**Merge-Reihenfolge (Empfehlung):** A -> B -> E -> C1 -> F -> D1 -> G -> C2 -> D2. Nach jedem Merge rebased der nächste PR und wiederholt Close-out Schritt 2.

## File Structure

**Cluster A (Hooks):** Modify `hooks/1-generic/lib/hook_common.sh` (Z.3 Version, Z.5 changelog, Z.164-178 `hook_known_tool_name`, Z.771 Fork-Bomb), `hooks/1-generic/dod-push-check.sh` (Z.3, Z.738 `git_config`, Z.811-833 `destination_block`, Z.1069 Tag-only-Pfad), `rules/1-generic/branch-guard.md` (Lücke 5, Z.33), `tests/test_hook_common_lib.py`, `tests/test_orchestrator_guard_hook.py`, `tests/test_dod_push_check_hook.py`, `CHANGELOG.md`, `tests/fixtures/ac01-baseline/hashes.json`.
**Cluster B (Consistency/Templates):** Modify `agents/1-generic/{orchestrator,senior-developer,meta-feedback,tester,data-engineer}.md` (+Version), `agents/2-platform/hacs-tester.md` (`based-on` -> `tester.md@<neu>`), `scripts/lib/consistency/active_set_refs.py` (`_line_hits` :204, `_collect` :233, `check_unresolved_placeholder` :317), `config/known-issues.yaml`, `.meta-config/project.yaml` (`KEY_PATTERNS`-Prosa), `tests/test_active_set_dangling.py`, `CHANGELOG.md`, `tests/fixtures/ac01-baseline/hashes.json`.
**Cluster C (Sync):** C1: Modify `scripts/lib/gitignore.py` (:184 `compute_base_gitignore_entries`, :396 `detect_shadowed_provider_roots`), `scripts/lib/context.py` (:327-328 Marker -> Import), `scripts/lib/sync_pipeline.py` (`framework_baseline` :~1568), `tests/test_gitignore_shadowing.py`, Create `tests/test_gitignore_platform_defaults.py`. C2: Modify `scripts/lib/generated_file_drift.py` (:142 `prune_sync_backups`, :313 `scan_generated_file_drift`, :354 `backup_drifted_files`), `scripts/lib/sync_pipeline.py` (:930-931, :1003-1036, :~1656), `scripts/lib/cli_commands.py` (:~1540), `scripts/lib/external_tools_drift.py`, `config/ai-providers.yaml`, `tests/test_generated_file_drift.py`, `tests/test_external_tools_registry.py`.
**Cluster D (Config/Admin):** D1: Modify `scripts/admin-server.py` (:1065 `resolve_path`, :1117), `scripts/lib/auto_commit.py`, `scripts/lib/sync_pipeline.py` (`_sync_stage_auto_commit_allowlist`), `scripts/lib/cli_commands.py` (`_handle_validate`), Create `tests/test_auto_commit_violations.py`, Modify `tests/test_admin_server.py`. D2: Create `scripts/lib/yaml_patch.py`, `tests/test_yaml_patch.py`, `tests/test_fill_defaults_comments.py`; Modify `scripts/lib/config.py` (`fill_defaults`), `scripts/lib/sync_pipeline.py` (:167), `scripts/lib/cli_commands.py` (:741), `scripts/admin-server.py` (`ConfigManager.write`, `_route_put_config`, `_write_project_section`).
**Cluster E (Provider/MCP/Hermes):** Modify `scripts/lib/active_set.py`, `scripts/lib/isolation.py` (:549, :804, :1299, :1669), `scripts/lib/context.py` (:1655, :1702, :1755), `config/plugin-catalog.yaml` (:101, :127), `scripts/lib/mcp_provider_config.py` (:221), Create `scripts/lib/mcp_health.py`, Modify `scripts/lib/sync_pipeline.py` (Aufruf hinter `sync_secrets_template`), `scripts/hermes_export.py` (:219-250, :290, :528-543), Create `tests/test_opencode_main_chat_entry_point.py`, `tests/test_mcp_health.py`, Modify `tests/test_mcp_config.py`, `tests/test_hermes_export.py`.
**Cluster F (Template):** Modify `agents/1-generic/git.md` (:123, Version 2.1.0 -> 2.1.1), `scripts/lib/config.py` (:~1442), `scripts/lib/standalone.py` (:~134), `scripts/lib/consistency/placeholders.py`, `tests/test_git_section_variables.py`, `CHANGELOG.md`, `tests/fixtures/ac01-baseline/hashes.json`.
**Cluster G (Tests/Containment/Housekeeping):** Create `scripts/lib/settings_dirs.py`, `tests/test_settings_dirs.py`; Modify `config/ai-providers.yaml` (Key `settings-allow-dirs-key`), `scripts/lib/sync_pipeline.py`, Doctor-Modul (per Grep `--doctor` ermitteln), `scripts/lib/hooks.py` (:280 Docstring), `tests/test_antigravity_hooks_registration.py`, `docs/plans/2026-10-11-context-profiles-plan.md` (Task 1.24 Status).

---
pipeline_stages:
  implement: 3
---

## Task-Übersicht

| # | Step | Agent | Depends on | Acceptance |
|---|---|---|---|---|
| G0 | [W0] #1042 als Duplikat von #1041 schließen | git | — | #1042 closed mit Verweis auf #1041 |
| A1 | [W1] #1078 ToolSearch + 16 weitere Built-ins in `hook_known_tool_name` | developer | — | 17 Namen `known`, Worktree-Tools `unknown`, Guard-E2E Exit 0/2 |
| A2 | [W1] #1050 Fork-Bomb mit Klammer-Nesting | developer | A1 | beide Bypass-Beispiele Verdict `1`, R1 grün, Lücke 5 aus Rule entfernt |
| A3 | [W1] #1041 `push.recurseSubmodules` via Config/`-c`/Env | developer | A2 | 4 Blockfälle Exit 2, R2-Negativfälle Exit 0 |
| A4 | [W1] Close-out PR A | developer, code-reviewer, git | A3 | Rebaseline nur hook_common/dod-push-check/branch-guard-Schlüssel, PR offen |
| B1 | [W2] #1071 Templates `orchestrator`/`senior-developer`/`meta-feedback` gaten | developer | — | `check_dangling_dispatch == []` in Rollen-Matrix ohne `principal-developer`/`feedback` |
| B2 | [W2] #1083 Frontmatter-Mention -> WARNING | developer | B1 | genau 1 WARNING + 1 INFO, `tester`/`data-engineer` neutral |
| B3 | [W2] #1082 Code-Span/Fence im Placeholder-Check ignorieren | developer | B2 | Beispiele in Backticks/Fences nicht geflaggt, echtes `{{FOO}}` weiter |
| B4 | [W2] Close-out PR B | developer, code-reviewer, git | B3 | Rebaseline (5 Templates x Provider) + Goldens, PR offen |
| C1 | [W1] #1072 Shadowing-FP für Regeln im managed Block | developer | — | Warnung nur außerhalb des Blocks |
| C2 | [W1] #1073 `platform-defaults.resolved.yaml` in managed `.gitignore` | developer | C1 | Eintrag in beiden Zweigen, `git check-ignore` positiv |
| C3 | [W1] Close-out PR C1 | developer, code-reviewer, git | C2 | Rebaseline nur `*/.gitignore`-Schlüssel, PR offen |
| C4 | [W3] #1081 Drift-Entscheidung nach den Writern (`resolve_drift_findings`) | developer | — | stale Baseline still, echte Änderung gesichert, R3 grün |
| C5 | [W3] #1081 Backup-Prune count-only | developer | C4 | 10 Backups -> 3, Einzelner alter bleibt |
| C6 | [W3] #1084 (a)(b)(d) Excuse-Logik | developer | C5 | `.guard-audit.log`, `mcp.local.json`, Backup-only nicht geflaggt |
| C7 | [W3] #1084 (e) `infra_known_names` je Provider | developer | C6 | `package.json` entschuldigt, `evil.sh` geflaggt |
| C8 | [W3] #1084 (c) Report-Merge in ersten `has_rules`-Provider | developer | C7 | Gemini-Finding erscheint mit `[Gemini]` im Claude-Report |
| C9 | [W3] Close-out PR C2 | developer, code-reviewer, git | C8 | kein Rebaseline-Diff erwartet, PR offen |
| D1 | [W1] #1095 `resolve_path` Symlink-Containment | developer | — | Defaults lesbar, Containment bleibt, R5 grün |
| D2 | [W2] #1091 `auto_commit_violations` + `resolve_auto_commit_config` Fail-safe | developer | D1 | Violations-Liste exakt, Fail-safe `off` |
| D3 | [W2] #1091 `--validate` rc=1, Sync rc=0 + WARN | developer | D2 | R4 grün |
| D4 | [W2] Close-out PR D1 | developer, code-reviewer, git | D3 | kein Rebaseline-Diff erwartet, PR offen |
| D5 | [W3] #1074/#1092 Modul `yaml_patch.patch_top_level` | developer | — | unveränderte Segmente byte-identisch, Selbstcheck |
| D6 | [W3] #1074 `fill_defaults` via `yaml_patch` + `materialize_presets` | developer | D5 | Sync 2x zero diff, Kommentare bleiben |
| D7 | [W3] #1092 Admin-Write `project` via `yaml_patch` + Guard | developer | D6, D4 | Kommentare außerhalb Section erhalten, Lossy -> 400 |
| D8 | [W3] Close-out PR D2 | developer, code-reviewer, git | D7 | Rebaseline nur falls `project.yaml` in Baseline, PR offen |
| E1 | [W2] #1090 `role_emitted_for_provider` + Entry-Point | developer | — | main-chat => kein `default_agent` (v1-Merge) |
| E2 | [W2] #1090 v2-Init `emit_default_agent` + Dangling-WARN | developer | E1 | Init ohne Key, WARN, Nutzerwert bleibt |
| E3 | [W2] #1080 `python3` im Katalog + Interpreter-Fallback | developer | E2 | kein `command == "python"`, Fallback testbar |
| E4 | [W2] #1080 `mcp_health` WARNs | developer | E3 | 1 WARN pro Server, Env zählt als gesetzt |
| E5 | [W1] #1094 Hermes Skillpack (dir=name, description, tier) | developer | — | `skill`-Dir == Frontmatter-`name`, Template-description zuerst |
| E6 | [W2] Close-out PR E | developer, code-reviewer, git | E4, E5 | kein Rebaseline-Diff erwartet, PR offen |
| F1 | [W1] #1093 `GIT_REMOTE_URL_SET` + `git.md` 2.1.1 | developer | — | kein `()` ohne URL, URL mit Klammern |
| F2 | [W1] Close-out PR F | developer, code-reviewer, git | F1 | Rebaseline nur `*/git.md`, PR offen |
| G1 | [W1] #971 Verifikationslauf + Tracking | tester, documenter | — | Matrix-Tests grün, #971 geschlossen, #977 Checkbox, Plan-Status |
| G2 | [W1] #1032 Docstring + Pin-Test, Issue schließen | developer, git | — | Pin-Test grün, Schließen mit Evidenzverweis |
| G3 | [W2] #1079 `settings_dirs.sync_allowed_directories` | developer | E4 | additiv, idempotent, Capability-gesteuert |
| G4 | [W2] #1079 Aufruf in Sync + Doctor-Zeile + Provider-Key | developer | G3 | `settings.local.json` enthält Basetemp, Doctor-Zeile |
| G5 | [W2] Close-out PR G | developer, code-reviewer, git | G2, G4 | kein Rebaseline-Diff erwartet, PR offen |

## Tasks Cluster A

Branch `fix/hooks-guards`. Alle Hook-Tests laufen mit `--basetemp="$PYTEST_BASETEMP"`. Reihenfolge im Branch seriell (A1 -> A2 -> A3).

### Task G0: #1042 als Duplikat schließen (Welle 0)

**Agent:** git
**Depends on:** —
**Files:** keine (nur Issue-Aktion)
**Interfaces:** Consumes: Issue #1041 (Original), #1042 (Duplikat). Produces: #1042 geschlossen.

- [ ] Step 1: Kommentar auf #1042 "Duplicate of #1041" posten und #1042 als `not planned` schließen (Rolle `git`, `gh` unter `/home/hermes/.local/bin/gh`).
- [ ] Step 2: Prüfen: `gh issue view 1042 --json state` liefert `CLOSED`.

### Task A1: #1078 ToolSearch und weitere Built-ins in der Allow-Liste

**Agent:** developer
**Depends on:** —
**Files:**
- Modify: `hooks/1-generic/lib/hook_common.sh` (Z.3 Version, Z.5 changelog vorn, Z.133-163 Header-Kommentar, Z.164-178 `hook_known_tool_name`)
- Modify: `tests/test_hook_common_lib.py` (nach Z.332)
- Modify: `tests/test_orchestrator_guard_hook.py` (neuer Test am Dateiende, nutzt `_run_hook`/`_clean_env`)

**Interfaces:**
- Produces: `hook_known_tool_name <name>` -> return 0 für die 17 neuen Namen (`ToolSearch, TaskCreate, TaskUpdate, TaskList, TaskGet, Monitor, ScheduleWakeup, CronCreate, CronDelete, CronList, EnterPlanMode, PushNotification, RemoteTrigger, SendUserFile, Artifact, ArtifactComments, ArtifactData`); `EnterWorktree`/`ExitWorktree`/Unbekanntes weiter return 1.
- Consumes: bestehende Aufrufer `orchestrator-guard-impl.sh:250`, `repo-containment-impl.sh:216` (unverändert).

- [ ] **Step 1: Failing Tests schreiben**

`tests/test_hook_common_lib.py` (nach `test_hook_known_tool_name_accepts_known_tools`):
```python
@pytest.mark.parametrize("name", [
    "ToolSearch", "TaskCreate", "TaskUpdate", "TaskList", "TaskGet", "Monitor",
    "ScheduleWakeup", "CronCreate", "CronDelete", "CronList", "EnterPlanMode",
    "PushNotification", "RemoteTrigger", "SendUserFile", "Artifact",
    "ArtifactComments", "ArtifactData",
])
def test_hook_known_tool_name_accepts_1078_builtins(name):
    assert _known(name) == "known"
```
`tests/test_orchestrator_guard_hook.py` (am Ende; `_run_hook(payload: dict)`):
```python
def test_toolsearch_is_allowed_and_unknown_tool_still_blocked():
    ok = _run_hook({"tool_name": "ToolSearch", "tool_input": {"query": "x"}})
    assert ok.returncode == 0, ok.stderr
    bad = _run_hook({"tool_name": "Bogus", "tool_input": {}})
    assert bad.returncode == 2
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_hook_common_lib.py::test_hook_known_tool_name_accepts_1078_builtins tests/test_orchestrator_guard_hook.py::test_toolsearch_is_allowed_and_unknown_tool_still_blocked --basetemp="$PYTEST_BASETEMP"` — erwartet: 17 Parametrisierungen `AssertionError: 'unknown' == 'known'` und `returncode == 2` statt 0.

- [ ] **Step 3: Implementierung**
In `hook_known_tool_name` (Z.164-178) vor `Write|AskUserQuestion) return 0 ;;` zwei `case`-Zeilen einfügen, jeweils `return 0 ;;`:
`ArtifactData|Artifact|ArtifactComments|CronCreate|CronDelete|CronList|EnterPlanMode|Monitor) return 0 ;;`
`PushNotification|RemoteTrigger|ScheduleWakeup|SendUserFile|TaskCreate|TaskGet|TaskList|TaskUpdate|ToolSearch) return 0 ;;`
Header-Kommentar Z.133-163 um die Namen ergänzen; `# version: 1.6.1`; `# changelog:` vorn `v1.6.1: hook_known_tool_name also knows ToolSearch and the other current built-ins (ToolSearch blocked the main chat and SendMessage, #1078); EnterWorktree/ExitWorktree stay blocked; ` ergänzen.

- [ ] **Step 4: Run -> PASS**
Dasselbe Kommando plus `python3 -m pytest tests/test_hook_common_lib.py tests/test_orchestrator_guard_hook.py --basetemp="$PYTEST_BASETEMP"` (Regression, der `rejects`-Test für `EnterWorktree`/`ExitWorktree` bleibt grün).

- [ ] **Step 5: Commit**
Betreff zählen: `fix: allow ToolSearch and current built-ins in tool allow-list` (<= 72).
`git add hooks/1-generic/lib/hook_common.sh tests/test_hook_common_lib.py tests/test_orchestrator_guard_hook.py`
`git commit -m "fix: allow ToolSearch and current built-ins in tool allow-list" -m "Closes #1078"`

### Task A2: #1050 Fork-Bomb-Scan mit Klammer-Nesting

**Agent:** developer
**Depends on:** A1
**Files:**
- Modify: `hooks/1-generic/lib/hook_common.sh` (Z.771-777 in `is_fork_bomb`, Kommentar Z.444-447, Header Version 1.6.1 -> 1.7.0, changelog)
- Modify: `rules/1-generic/branch-guard.md` (Z.33 Lücke 5 ersetzen)
- Modify: `tests/test_hook_common_lib.py`, `tests/test_orchestrator_guard_hook.py`

**Interfaces:**
- Produces: `is_fork_bomb(command: str) -> bool` (Python-Teil von `hook_shell_scan_py`), Semantik: der Funktionskörper endet an der ersten `}` bei Tiefe 0 innerhalb von `_MAX_FUNC_BODY = 512` Zeichen; kein schließendes `}` im Fenster => `True` (fail-closed, unverändert).
- Consumes: `_body_calls_itself_piped(body, name)`, `_MAX_FUNC_BODY`.

- [ ] **Step 1: Failing Tests schreiben**

`tests/test_hook_common_lib.py` (Helfer `_fork_bomb_verdict`, `_scan`):
```python
@pytest.mark.parametrize("command", [
    "f(){ : ${x}; f|f& };f",
    "f(){ { :; }; f|f& };f",
])
def test_fork_bomb_detects_bomb_after_nested_braces(command):
    r = _scan(f"print(int(is_fork_bomb({command!r})))")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "1"

def test_fork_bomb_nesting_keeps_fail_closed_and_linear():          # R1
    r = _scan(
        "import time\n"
        "t = time.perf_counter()\n"
        "a = is_fork_bomb('f(){ { :; }; echo hi; };f')\n"
        "b = is_fork_bomb('f(){ ' + 'x ' * 300 + '{ y')\n"
        "c = is_fork_bomb('f(){ x} ' * 60000)\n"
        "print(int(a), int(b), int(c), int((time.perf_counter() - t) < 1.0))"
    )
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "0 1 0 1"
```
`tests/test_orchestrator_guard_hook.py`:
```python
def test_nested_brace_fork_bomb_is_blocked_end_to_end():
    r = _run_hook(_bash_payload("f(){ { :; }; f|f& };f"))
    assert r.returncode == 2
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_hook_common_lib.py -k "nested_braces or nesting_keeps" tests/test_orchestrator_guard_hook.py::test_nested_brace_fork_bomb_is_blocked_end_to_end --basetemp="$PYTEST_BASETEMP"` — erwartet: `'0' == '1'` für beide Bypass-Beispiele, Exit 0 statt 2.

- [ ] **Step 3: Implementierung**
In `hook_common.sh` Z.771 `close = command.find('}', j + 1, j + 1 + _MAX_FUNC_BODY)` ersetzen durch (innerhalb derselben Schleife, selbe Einrückung):
```python
        close = -1
        depth = 1
        for k in range(j + 1, min(n, j + 1 + _MAX_FUNC_BODY)):
            ch = command[k]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    close = k
                    break
```
Der anschließende `if close < 0: return True`-Zweig bleibt (fail-closed). Kommentar Z.444-447 (Lücke) streichen/anpassen; Version `1.7.0`, changelog vorn. `branch-guard.md` Z.33: Lücke 5 ersetzen durch: `5. Der Fork-Bomb-Scan zählt geschweifte Klammern (Nesting innerhalb von 512 Zeichen). Eine ungequotete, unbalancierte `{` im Funktionskörper blockt fail-closed (mögliche Fehlalarme).` (Datei hat kein `version:`-Frontmatter; kein Bump.)

- [ ] **Step 4: Run -> PASS**
Dasselbe Kommando; zusätzlich `python3 -m pytest tests/test_hook_common_lib.py tests/test_orchestrator_guard_hook.py --basetemp="$PYTEST_BASETEMP"` (bestehende Linearitäts- und Window-Tests bleiben grün).

- [ ] **Step 5: Commit**
`git add hooks/1-generic/lib/hook_common.sh rules/1-generic/branch-guard.md tests/test_hook_common_lib.py tests/test_orchestrator_guard_hook.py`
`git commit -m "fix: count braces in fork-bomb function body scan" -m "Closes #1050"`

### Task A3: #1041 push.recurseSubmodules über Config, `-c` und Env

**Agent:** developer
**Depends on:** A2
**Files:**
- Modify: `hooks/1-generic/dod-push-check.sh` (Z.3 Version 2.1.7 -> 2.1.8 + changelog, Header "Known alias/config limits" Z.30-36, `destination_block` Z.811-833, Tag-only-Pfad Z.1069)
- Modify: `tests/test_dod_push_check_hook.py` (nach `test_953_...`, Z.1050 ff.)

**Interfaces:**
- Produces (Python-Teil des Hooks): `config_recurses(p) -> bool` — `True` wenn (a) `git_config()` den letzten Wert von `push.recursesubmodules` (lowercase) als `on-demand`/`only` führt oder (b) ein Token in `p.override` den Substring `push.recursesubmodules` enthält (wert-agnostisch, deckt `-c`, `--config-env`, `GIT_CONFIG_*`); ein explizites `--recurse-submodules`/`--no-recurse-submodules` in `p`'s Optionen mit anderem Wert überspringt (a)/(b).
- Consumes: `git_config()` (Z.738), `Push.override` (Z.352-361), `destination_block(p)`, `stmt_is_tag_only(args)` (Z.517), `has_submodules()`.

- [ ] **Step 1: Failing Tests schreiben**

`tests/test_dod_push_check_hook.py` (Fixtures `repo_on_feature_branch`, `_run_hook(cwd, command)`; Submodule-Erkennung wie `test_953_...` über `.gitmodules`):
```python
def _with_submodule(repo):
    (repo / ".gitmodules").write_text('[submodule "s"]\n\tpath = s\n\turl = ../s\n', encoding="utf-8")

def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)

@pytest.mark.parametrize("command", [
    "git -c push.recurseSubmodules=on-demand push origin feat/x",
    "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=push.recurseSubmodules GIT_CONFIG_VALUE_0=on-demand git push origin feat/x",
])
def test_1041_override_forms_are_blocked(repo_on_feature_branch, command):
    _with_submodule(repo_on_feature_branch)
    r = _run_hook(repo_on_feature_branch, command)
    assert r.returncode == 2, r.stdout
    assert "submodule" in r.stderr

@pytest.mark.parametrize("command", ["git push origin feat/x", "git push --tags origin"])
def test_1041_repo_config_is_blocked(repo_on_feature_branch, command):
    _with_submodule(repo_on_feature_branch)
    _git(repo_on_feature_branch, "config", "push.recurseSubmodules", "on-demand")
    r = _run_hook(repo_on_feature_branch, command)
    assert r.returncode == 2, r.stdout

def test_1041_cli_flag_overrides_config_and_inert_values(repo_on_feature_branch):   # R2
    _with_submodule(repo_on_feature_branch)
    for value in ("check", "no"):
        _git(repo_on_feature_branch, "config", "push.recurseSubmodules", value)
        assert _run_hook(repo_on_feature_branch, "git push origin feat/x").returncode == 0
    _git(repo_on_feature_branch, "config", "push.recurseSubmodules", "on-demand")
    assert _run_hook(repo_on_feature_branch, "git push --recurse-submodules=no origin feat/x").returncode == 0

def test_1041_no_submodules_means_no_block(repo_on_feature_branch):
    _git(repo_on_feature_branch, "config", "push.recurseSubmodules", "on-demand")
    assert _run_hook(repo_on_feature_branch, "git push origin feat/x").returncode == 0
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_dod_push_check_hook.py -k 1041 --basetemp="$PYTEST_BASETEMP"` — erwartet: Blockfälle liefern Exit 0 statt 2; Negativfälle sind schon grün.

- [ ] **Step 3: Implementierung**
In `dod-push-check.sh` (Python-Teil) `config_recurses(p)` oberhalb von `destination_block` definieren (Semantik siehe Interfaces; `opts` nach `--recurse-submodules`/`--no-recurse-submodules` mit Wert `check`/`no`/`false` oder `--no-…` => `return False`). In `destination_block` nach der CLI-Flag-Prüfung (Z.829-833): `if config_recurses(p) and (p.foreign or has_submodules()): return <gleiche Block-Meldung mit "push.recurseSubmodules" statt Flag>`. Z.1069: `not stmt_is_tag_only(p.args)` -> `(not stmt_is_tag_only(p.args) or config_recurses(p))`. Foreign-Repo (`-C`/`GIT_DIR`) unverändert; Restlücke im Header-Abschnitt "Known alias/config limits" dokumentieren. Version `2.1.8` + changelog.

- [ ] **Step 4: Run -> PASS**
Dasselbe Kommando plus `python3 -m pytest tests/test_dod_push_check_hook.py --basetemp="$PYTEST_BASETEMP"`.

- [ ] **Step 5: Commit**
`git add hooks/1-generic/dod-push-check.sh tests/test_dod_push_check_hook.py`
`git commit -m "fix: block push when push.recurseSubmodules config recurses" -m "Closes #1041"`

### Task A4: Close-out PR A

**Agent:** developer (Rebaseline/CHANGELOG) -> code-reviewer -> git
**Depends on:** A3
**Files:** Modify `CHANGELOG.md`, `tests/fixtures/ac01-baseline/hashes.json`, `tests/test_ac01_render_identity.py` (Rebaseline-Log)
**Interfaces:** Consumes: Close-out-Protokoll (Batch-Strategie). Produces: PR `fix/hooks-guards` mit `Closes #1078`, `Closes #1050`, `Closes #1041` (je eigene Zeile; #1042 bereits geschlossen).

- [ ] Step 1: Rebase auf `main` (Rolle `git`).
- [ ] Step 2: `python tests/test_ac01_render_identity.py --write`; `git diff --stat` darf nur diese Schlüssel ändern: `Claude/.claude/hooks/lib/hook_common.sh`, `Gemini/.agents/hooks/lib/hook_common.sh`, `Claude/.claude/hooks/dod-push-check.sh` und die `branch-guard`-Rule-Renders je Provider; Log-Eintrag "hook + rule renders (#1078/#1050/#1041)" in den Docstring.
- [ ] Step 3: CHANGELOG-Einträge (3x `Fixed:`).
- [ ] Step 4: Volllauf (Close-out Schritt 4), `code-reviewer`-Self-Review.
- [ ] Step 5: Commit `git add CHANGELOG.md tests/fixtures/ac01-baseline/hashes.json tests/test_ac01_render_identity.py` / `git commit -m "chore: rebaseline hooks and changelog for guard fixes"`; PR durch `git`, kein Merge.

## Tasks Cluster B

Branch `fix/consistency-false-positives`. Abweichung zu Verify-A: Zeilen in `active_set_refs.py` sind `_line_hits` :204, `_collect` :233 (Kind-Verzweigung :253-278), `check_unresolved_placeholder` :317-334 (nicht :157-185/:263/:310-335). Einziger Platform-Override mit `based-on` auf ein hier geändertes Template ist `agents/2-platform/hacs-tester.md` (`tester.md@2.8.0`).

### Task B1: #1071 Templates auf Rollen-Aktivität konditionieren

**Agent:** developer
**Depends on:** —
**Files:**
- Create: `tests/fixtures/active-set/pt/.meta-config/project.yaml`
- Modify: `agents/1-generic/orchestrator.md` (Z.113, 134-140, 152-153, 165, 167-168; Version 8.8.1 -> 8.8.2)
- Modify: `agents/1-generic/senior-developer.md` (Z.26, 78-83, 136, 152, 154; Version 1.10.0 -> 1.10.1)
- Modify: `agents/1-generic/meta-feedback.md` (Z.80; Version 2.6.1 -> 2.6.2)
- Modify: `tests/test_active_set_dangling.py` (`matrix`-Fixture Z.271, Parametrisierung Z.284)

**Interfaces:**
- Consumes: `ROLE_PRINCIPAL_DEVELOPER_ACTIVE`, `ROLE_FEEDBACK_ACTIVE` (`variables.py:448-450`, `active_set.py`), `DEVELOPER_TIERS_ENABLED`; `asr.check_dangling_dispatch(project, providers, {}, active)`.
- Produces: gerenderte Templates ohne Dispatch auf inaktive `principal-developer`/`feedback`; Checker unverändert.

- [ ] **Step 1: Failing Test schreiben**

Fixture `tests/fixtures/active-set/pt/.meta-config/project.yaml`:
```yaml
# developer tiers ON (junior+senior) but WITHOUT principal-developer and WITHOUT feedback (#1071).
agent-meta-version: "2.0.0-beta.4"
ai-providers:
- Claude
roles:
- orchestrator
- developer
- junior-developer
- senior-developer
- tester
- documenter
- git
- requirements
- planner
- code-reviewer
- explorer
- release
- meta-feedback
```
`tests/test_active_set_dangling.py`: in `matrix` `names = ("p10", "p20", "pall", "ha", "pt")` und beide `parametrize("name", [...])` (Z.284, Z.291) um `"pt"` erweitern; zusätzlich:
```python
def test_1071_inactive_principal_and_feedback_not_dispatched(matrix):
    project, active = matrix["pt"]
    assert "principal-developer" not in active.roles and "feedback" not in active.roles
    found = asr.check_dangling_dispatch(project, _MATRIX_PROVIDERS, {}, active)
    assert found == [], "\n".join(f"{f.file}: {f.message}" for f in found)

def test_1071_active_principal_row_still_rendered(matrix):
    project, _ = matrix["pall"]
    text = (project / ".claude" / "agents" / "orchestrator.md").read_text(encoding="utf-8")
    assert "| `principal-developer` |" in text
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_active_set_dangling.py::test_1071_inactive_principal_and_feedback_not_dispatched --basetemp="$PYTEST_BASETEMP"` — erwartet: Findings mit `dispatch to inactive role 'principal-developer'` (orchestrator.md, senior-developer.md) und `'feedback'` (meta-feedback.md).

- [ ] **Step 3: Implementierung**
  - `orchestrator.md`: Z.113 `{{#if DEVELOPER_TIERS_ENABLED}}` -> `{{#if ROLE_PRINCIPAL_DEVELOPER_ACTIVE}}`; Zeile 140 (`principal-developer`-Tabellenzeile) in eigene Zeilen `{{#if ROLE_PRINCIPAL_DEVELOPER_ACTIVE}}` / `{{/if}}` einrahmen; Z.153 (Satz mit `principal-developer`) und der `principal-developer`-Satz in Z.167-168 gleichermaßen mit `ROLE_PRINCIPAL_DEVELOPER_ACTIVE` gaten (Rest der Tiers-Prosa bleibt unter `DEVELOPER_TIERS_ENABLED`); Z.165 XL-Spalte: `{{#if ROLE_PRINCIPAL_DEVELOPER_ACTIVE}}`principal-developer`{{else}}{{#if DEVELOPER_TIERS_ENABLED}}`senior-developer`{{else}}`developer`{{/if}}{{/if}}`; Z.178 `, inkl. senior-developer → principal-developer` auf `ROLE_PRINCIPAL_DEVELOPER_ACTIVE` stellen.
  - `senior-developer.md`: Z.26 Satz `For last-resort escalations … route to principal-developer …` in `{{#if ROLE_PRINCIPAL_DEVELOPER_ACTIVE}}…{{else}}If blocked after 2+ verified failures, report `STATUS: failed` to the orchestrator.{{/if}}`; die Abschnitte "7. Escalation to principal-developer" (Z.78-83), Z.136 (`RECOMMENDED_TIER`), Z.152 und der Delegations-Tail Z.154 auf dieselbe Bedingung stellen (Absätze in eigene `{{#if}}`-Zeilen).
  - `meta-feedback.md`: Z.80 Tabellenzeile `| feedback | … |` in eigene Zeilen `{{#if ROLE_FEEDBACK_ACTIVE}}` / `{{/if}}`.
  - Versionen bumpen. Jede vom Test gemeldete weitere Fundstelle derselben Dateien nach demselben Muster gaten (Test ist das Orakel); `grep -n "principal-developer" agents/1-generic/{orchestrator,senior-developer}.md` darf danach nur noch Treffer innerhalb eines `ROLE_PRINCIPAL_DEVELOPER_ACTIVE`-Blocks zeigen.

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_active_set_dangling.py --basetemp="$PYTEST_BASETEMP"` (inkl. bestehender Heuristik-Tests, `test_table_heuristic_positive_only_dispatch_columns` bleibt unverändert grün) und `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`.

- [ ] **Step 5: Commit**
`git add agents/1-generic/orchestrator.md agents/1-generic/senior-developer.md agents/1-generic/meta-feedback.md tests/fixtures/active-set/pt tests/test_active_set_dangling.py`
`git commit -m "fix: gate inactive-role dispatch in orchestrator templates" -m "Closes #1071"`

### Task B2: #1083 Frontmatter-Mention als WARNING

**Agent:** developer
**Depends on:** B1
**Files:**
- Modify: `scripts/lib/consistency/active_set_refs.py` (Konstante nach Z.46; `_collect` :233-279; Registrierung der Check-Funktionen/-Namen)
- Modify: `config/known-issues.yaml` (Check-Name registrieren; Grep `dangling-mention` zeigt die Stelle)
- Modify: `agents/1-generic/tester.md` (Z.4 description; Version 2.8.0 -> 2.8.1), `agents/1-generic/data-engineer.md` (Z.4; Version 0.6.1 -> 0.6.2), `agents/2-platform/hacs-tester.md` (Z.4 `based-on: "1-generic/tester.md@2.8.1"`, Version patch bumpen)
- Modify: `tests/test_active_set_dangling.py`

**Interfaces:**
- Produces: `CHECK_DANGLING_MENTION_FM = "active-set.dangling-mention-frontmatter"`; `_frontmatter_end(lines: list) -> int` (Zeilennummer 1-basiert des schließenden `---`, `0` wenn `lines[0].strip() != "---"` oder kein Abschluss); `_collect(..., kind="mention")` liefert pro Rolle ein WARNING (Frontmatter-Treffer) und ein INFO (Body-Treffer).
- Consumes: `_line_hits`, `_read_lines`, `mention_allow`.

- [ ] **Step 1: Failing Tests schreiben** (`tests/test_active_set_dangling.py`, Helfer `_scratch`, `synced`)
```python
def test_1083_frontmatter_mention_is_warning_body_is_info(synced, tmp_path):
    _, active = synced("p10")
    proj = _scratch(tmp_path, '---\ndescription: "see se-test-engineer"\n---\nbody mentions se-test-engineer\n')
    found = asr.check_dangling_mention(proj, _PROVIDERS, {}, active)
    by_check = {f.check: f for f in found}
    assert set(by_check) == {"active-set.dangling-mention-frontmatter", "active-set.dangling-mention"}
    assert by_check["active-set.dangling-mention-frontmatter"].severity == Severity.WARNING
    assert by_check["active-set.dangling-mention"].severity == Severity.INFO

def test_1083_no_frontmatter_only_info(synced, tmp_path):
    _, active = synced("p10")
    proj = _scratch(tmp_path, "body mentions se-test-engineer\n")
    found = asr.check_dangling_mention(proj, _PROVIDERS, {}, active)
    assert [f.severity for f in found] == [Severity.INFO]

def test_1083_frontmatter_dispatch_phrase_stays_error(synced, tmp_path):
    _, active = synced("p10")
    proj = _scratch(tmp_path, '---\ndescription: "x"\n---\nbackground(agent="validator", prompt="x")\n')
    assert [f.severity for f in asr.check_dangling_dispatch(proj, _PROVIDERS, {}, active)] == [Severity.ERROR]

def test_1083_templates_description_names_no_inactive_role():
    import re
    for name in ("tester", "data-engineer"):
        text = (_ROOT / "agents" / "1-generic" / f"{name}.md").read_text(encoding="utf-8")
        desc = re.search(r'^description: "(.*)"$', text, re.M).group(1)
        assert "se-test-engineer" not in desc and "database-engineer" not in desc
```
(`Finding` hat die Felder `severity`, `check`, `file`, `message`, `suggestion` — verifiziert in `scripts/lib/consistency/report.py:29-34`.)

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_active_set_dangling.py -k 1083 --basetemp="$PYTEST_BASETEMP"` — erwartet: nur `active-set.dangling-mention` (INFO) vorhanden; Description-Test schlägt an `se-test-engineer`/`database-engineer` fehl.

- [ ] **Step 3: Implementierung**
`active_set_refs.py`:
```python
CHECK_DANGLING_MENTION_FM = "active-set.dangling-mention-frontmatter"

def _frontmatter_end(lines: list) -> int:
    if not lines or lines[0].strip() != "---":
        return 0
    for i, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            return i
    return 0
```
In `_collect` (Kind `mention`) pro Datei `fm_end = _frontmatter_end(lines)` berechnen (die Zeilenliste einmal lesen, an `_line_hits` übergeben); `per_role` nach (`role`, `in_fm = lineno <= fm_end`) trennen; `in_fm` => `Finding(Severity.WARNING, CHECK_DANGLING_MENTION_FM, rel, f"mention of inactive role '{role}' in frontmatter ({n}x, first line {first})", "Name the role conditionally or neutrally in the description")`, sonst unverändertes INFO. `_dedupe` bleibt. Check-Name in `config/known-issues.yaml` neben `active-set.dangling-mention` eintragen. `tester.md` description: `"Isolated unit tests with mocks/stubs following a TDD workflow. Integration tests belong to a dedicated integration-test role when one is active."`; `data-engineer.md`: den Satz `Distinct from database-engineer query/index work.` durch `Distinct from query/index tuning work.` ersetzen.

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_active_set_dangling.py tests/test_known_issues_registry.py --basetemp="$PYTEST_BASETEMP"` und `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`.

- [ ] **Step 5: Commit**
`git add scripts/lib/consistency/active_set_refs.py config/known-issues.yaml agents/1-generic/tester.md agents/1-generic/data-engineer.md agents/2-platform/hacs-tester.md tests/test_active_set_dangling.py`
`git commit -m "fix: warn on inactive role named in frontmatter description" -m "Closes #1083"`

### Task B3: #1082 Placeholder-Check ignoriert Code-Spans und Fences

**Agent:** developer
**Depends on:** B2
**Files:**
- Modify: `scripts/lib/consistency/active_set_refs.py` (`check_unresolved_placeholder` :317-334, neuer Helfer `_non_code_lines`)
- Modify: `.meta-config/project.yaml` (`variables.KEY_PATTERNS`-Prosa: `{{VARIABLE}}` in Backticks)
- Modify: `tests/test_active_set_dangling.py`

**Interfaces:**
- Produces: `_non_code_lines(lines: list) -> list` — gibt Zeilen ohne Fence-Blöcke (Zeilen, die mit ```` ``` ```` oder `~~~` beginnen, schalten um) und mit entfernten Inline-Code-Spans (`re.sub(r"(`+)[^`\n]*?\1", "", line)`) zurück; Zeilenanzahl bleibt (ausgeblendete Zeilen werden zu `""`).
- Consumes: `_PLACEHOLDER_RE`, `_refs()["placeholder_allow"]` (bleibt `[]`).

- [ ] **Step 1: Failing Tests schreiben**
```python
def test_1082_placeholder_in_inline_code_and_fence_is_not_flagged(synced, tmp_path):
    _, active = synced("p10")
    proj = _scratch(tmp_path, "use `{{VAR}}` as example\n```\n{{FLAG_A}}\n```\n``{{X_Y}}``\n")
    assert asr.check_unresolved_placeholder(proj, _PROVIDERS, {}, active) == []

def test_1082_plain_and_mixed_placeholders_still_flagged(synced, tmp_path):
    _, active = synced("p10")
    proj = _scratch(tmp_path, "plain {{FOO}} text\nmixed `{{BAR}}` and {{BAZ}}\n")
    found = asr.check_unresolved_placeholder(proj, _PROVIDERS, {}, active)
    assert sorted(f.message.split()[2] for f in found) == ["{{BAZ}}", "{{FOO}}"]
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_active_set_dangling.py -k 1082 --basetemp="$PYTEST_BASETEMP"` — erwartet: erster Test liefert 4 Findings statt `[]`.

- [ ] **Step 3: Implementierung**
`_non_code_lines` wie in Interfaces; in `check_unresolved_placeholder` `for line in _read_lines(path):` -> `for line in _non_code_lines(_read_lines(path)):`. `.meta-config/project.yaml`: in `variables.KEY_PATTERNS` die freie Prosa `Platzhalter {{VARIABLE}} werden …` zu ``Platzhalter `{{VARIABLE}}` werden …`` ändern (Grep `Platzhalter {{VARIABLE}}`; Sync-Drift in `CLAUDE.md`/`AGENTS.md` wird NICHT committet).

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_active_set_dangling.py --basetemp="$PYTEST_BASETEMP"` (`test_pall_unresolved_placeholder_extra_donts` und `test_placeholder_allow_suppresses` bleiben grün; sonst Fixture anpassen) und `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`.

- [ ] **Step 5: Commit**
`git add scripts/lib/consistency/active_set_refs.py .meta-config/project.yaml tests/test_active_set_dangling.py`
`git commit -m "fix: skip code spans in unresolved-placeholder check" -m "Closes #1082"`

### Task B4: Close-out PR B

**Agent:** developer -> code-reviewer -> git
**Depends on:** B3
**Files:** Modify `CHANGELOG.md`, `tests/fixtures/ac01-baseline/hashes.json`, `tests/test_ac01_render_identity.py`, `standalone/agents/{orchestrator,senior-developer,meta-feedback,tester,data-engineer}.md` (nur soweit enthalten und geändert), ggf. `tests/fixtures/slimming-golden/*`, `tests/fixtures/compact-golden/*`
**Interfaces:** Consumes: Close-out-Protokoll. Produces: PR `fix/consistency-false-positives` mit `Closes #1071`, `Closes #1083`, `Closes #1082` (je eigene Zeile).

- [ ] Step 1: Rebase auf `main`.
- [ ] Step 2: `python3 -m pytest tests/test_ac01_render_identity.py tests/test_context_budget_checks.py tests/test_standalone_export_in_sync.py --basetemp="$PYTEST_BASETEMP"`; bei Diff `python scripts/sync.py --render-standalone` (Standalone-Export, `test_standalone_export_in_sync.py` ist das Gate) und `--write` für AC-01, danach `git diff --stat`: erlaubt sind nur Renders von `orchestrator`, `senior-developer`, `meta-feedback`, `tester`, `data-engineer`, `hacs-tester` (alle Provider). `slimming-golden`/`compact-golden`/`active-set-prose` nur bei Diff nachziehen, Grund im Rebaseline-Log (#1071/#1083).
- [ ] Step 3: CHANGELOG (`Fixed:` x3; #1083 mit "new check `active-set.dangling-mention-frontmatter` (WARNING)").
- [ ] Step 4: Volllauf, `code-reviewer`-Self-Review, PR durch `git`.
- [ ] Step 5: Commit `git add CHANGELOG.md tests/fixtures tests/test_ac01_render_identity.py` / `git commit -m "chore: rebaseline template renders for consistency fixes"`.

## Tasks Cluster C

Zwei PRs: **C1** (`fix/gitignore-managed-block`, Welle 1: C1+C2+C3) und **C2** (`fix/drift-false-positives`, Welle 3: C4-C9). Task-IDs C1/C2 (Tasks) und PR-Namen C1/C2 sind getrennt zu lesen: PR C1 = Tasks C1-C3, PR C2 = Tasks C4-C9. Abweichung zu Verify-B: der Nicht-Claude-Zweig in `sync_pipeline.py` ist `_sync_stage_gitignore` (:1562-1575, `framework_baseline` :1568), der Claude-Zweig übergibt `exact_entries=all_gitignore_entries` (:1555-1561).

### Task C1: #1072 Shadowing-Warnung nur für Regeln außerhalb des managed Blocks

**Agent:** developer
**Depends on:** —
**Files:**
- Modify: `scripts/lib/gitignore.py` (Marker-Konstanten neu, `detect_shadowed_provider_roots` :396-438)
- Modify: `scripts/lib/context.py` (:327-328 -> `from .gitignore import GITIGNORE_BLOCK_BEGIN, GITIGNORE_BLOCK_END`)
- Modify: `tests/test_gitignore_shadowing.py`

**Interfaces:**
- Produces (`gitignore.py`): `GITIGNORE_BLOCK_BEGIN = "# --- agent-meta managed (do not edit) ---"`, `GITIGNORE_BLOCK_END = "# --- end agent-meta managed ---"` (Werte unverändert von `context.py:327-328`); `_line_in_managed_block(gitignore_text: str, lineno: int) -> bool` (1-basiert, True nur zwischen BEGIN und END).
- Consumes: `run_git_check_ignore(probe, root, "-v")`; Ausgabeformat `<source>:<line>:<pattern>\t<path>`.

- [ ] **Step 1: Failing Tests schreiben** (`tests/test_gitignore_shadowing.py`, Helfer `_init_repo`, `_PROVIDER_CONFIG`)
```python
from lib.gitignore import GITIGNORE_BLOCK_BEGIN, GITIGNORE_BLOCK_END

def test_no_warning_when_rule_inside_managed_block(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(
        f"{GITIGNORE_BLOCK_BEGIN}\n.claude/\n{GITIGNORE_BLOCK_END}\n", encoding="utf-8")
    assert detect_shadowed_provider_roots(
        tmp_path, ["Claude"], _PROVIDER_CONFIG, ignore_provider_dirs=False) == []

def test_warning_when_rule_outside_block_even_if_block_exists(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(
        f".claude/\n{GITIGNORE_BLOCK_BEGIN}\nsync.log\n{GITIGNORE_BLOCK_END}\n", encoding="utf-8")
    warnings = detect_shadowed_provider_roots(
        tmp_path, ["Claude"], _PROVIDER_CONFIG, ignore_provider_dirs=False)
    assert len(warnings) == 1 and ".gitignore:1:.claude/" in warnings[0]
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_gitignore_shadowing.py --basetemp="$PYTEST_BASETEMP"` — erwartet: `ImportError: cannot import name 'GITIGNORE_BLOCK_BEGIN' from 'lib.gitignore'`.

- [ ] **Step 3: Implementierung**
Konstanten und `_line_in_managed_block` in `gitignore.py` definieren; `context.py` importiert sie statt sie zu definieren (kein Zyklus: `gitignore.py` importiert nur `.io`, `.providers`, `.tmp_paths`). In `detect_shadowed_provider_roots` nach `source_rule = ...`: `src, ln, _pat = (source_rule.split(":", 2) + ["", ""])[:3]`; wenn `src == ".gitignore"` und `ln.isdigit()` und `_line_in_managed_block((project_root / ".gitignore").read_text(encoding="utf-8"), int(ln))` => `continue`. Docstring-Aussage "predates" auf "pre-existing rule outside the managed block" korrigieren.

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_gitignore_shadowing.py tests/test_context_gitignore*.py --basetemp="$PYTEST_BASETEMP"` (Glob ggf. leer; dann `-k gitignore`).

- [ ] **Step 5: Commit**
`git add scripts/lib/gitignore.py scripts/lib/context.py tests/test_gitignore_shadowing.py`
`git commit -m "fix: skip shadowing warning for rules inside managed block" -m "Closes #1072"`

### Task C2: #1073 `platform-defaults.resolved.yaml` in den managed Block

**Agent:** developer
**Depends on:** C1
**Files:**
- Modify: `scripts/lib/gitignore.py` (`FRAMEWORK_GENERATED_ENTRIES`, `framework_baseline_entries`, Ende von `compute_base_gitignore_entries` vor tmp-sink :323)
- Modify: `scripts/lib/sync_pipeline.py` (:1568 `framework_baseline = framework_baseline_entries()`, Import :81)
- Create: `tests/test_gitignore_platform_defaults.py`

**Interfaces:**
- Produces: `FRAMEWORK_GENERATED_ENTRIES: tuple[str, ...] = (".meta-config/platform-defaults.resolved.yaml",)`; `framework_baseline_entries() -> list[str]` = `["sync.log", "*.sync-backup-*", *FRAMEWORK_GENERATED_ENTRIES]`.
- Consumes: `compute_base_gitignore_entries(providers, provider_config, gitignore_cfg, ...)`; `generated_file_drift.PLATFORM_DEFAULTS_RESOLVED_REL` (Wert muss gleich sein, per Test gepinnt statt Import wegen Zyklusrisiko).

- [ ] **Step 1: Failing Tests schreiben** (`tests/test_gitignore_platform_defaults.py`)
```python
import subprocess, sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import pytest
from lib.gitignore import (FRAMEWORK_GENERATED_ENTRIES, compute_base_gitignore_entries,
                           framework_baseline_entries)
from lib.generated_file_drift import PLATFORM_DEFAULTS_RESOLVED_REL

_PC = {"Claude": {"has_dedicated_context_file": True, "agents_dir": ".claude/agents",
                  "gitignore_entries": [".claude/settings.local.json"]}}

def test_constant_matches_drift_module():
    assert FRAMEWORK_GENERATED_ENTRIES == (PLATFORM_DEFAULTS_RESOLVED_REL,)

@pytest.mark.parametrize("cfg", [{}, {"generated": True}, {"ignore-provider-dirs": True},
                                 {"ignore-provider-dirs": True, "generated": True}])
def test_platform_defaults_snapshot_in_base_entries(cfg):
    entries = compute_base_gitignore_entries(["Claude"], _PC, cfg)
    assert PLATFORM_DEFAULTS_RESOLVED_REL in entries

def test_non_dedicated_framework_baseline_contains_snapshot():
    assert framework_baseline_entries() == ["sync.log", "*.sync-backup-*", PLATFORM_DEFAULTS_RESOLVED_REL]

def test_git_check_ignore_matches_entry(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text(PLATFORM_DEFAULTS_RESOLVED_REL + "\n", encoding="utf-8")
    r = subprocess.run(["git", "check-ignore", "-q", PLATFORM_DEFAULTS_RESOLVED_REL], cwd=tmp_path)
    assert r.returncode == 0
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_gitignore_platform_defaults.py --basetemp="$PYTEST_BASETEMP"` — erwartet: `ImportError: cannot import name 'FRAMEWORK_GENERATED_ENTRIES'`.

- [ ] **Step 3: Implementierung**
Konstante und Funktion in `gitignore.py` ergänzen; in `compute_base_gitignore_entries` direkt nach dem `custom_entries`-Block (:319-321) `for _e in FRAMEWORK_GENERATED_ENTRIES: if _e not in entries: entries.append(_e)` (unbedingt, unabhängig von Toggles). `sync_pipeline.py:1568` ersetzen durch `framework_baseline = framework_baseline_entries()`; Import ergänzen. `generated_file_drift.PLATFORM_DEFAULTS_RESOLVED_REL` bleibt unverändert (Quelle bleibt der Pin-Test). Kein `git rm --cached` im Fix (Folge-Housekeeping).

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_gitignore_platform_defaults.py tests/test_gitignore_shadowing.py --basetemp="$PYTEST_BASETEMP"` und `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`.

- [ ] **Step 5: Commit**
`git add scripts/lib/gitignore.py scripts/lib/sync_pipeline.py tests/test_gitignore_platform_defaults.py`
`git commit -m "fix: ignore platform-defaults snapshot in managed block" -m "Closes #1073"`

### Task C3: Close-out PR C1

**Agent:** developer -> code-reviewer -> git
**Depends on:** C2
**Files:** Modify `CHANGELOG.md`, `tests/fixtures/ac01-baseline/hashes.json`, `tests/test_ac01_render_identity.py` (Rebaseline-Log), ggf. `.gitignore`-haltige Fixtures (`grep -rn "agent-meta managed (do not edit)" tests/fixtures`)
**Interfaces:** Consumes: Close-out-Protokoll. Produces: PR `fix/gitignore-managed-block` mit `Closes #1072`, `Closes #1073`.

- [ ] Step 1: Rebase auf `main`.
- [ ] Step 2: `python tests/test_ac01_render_identity.py --write`; erlaubt im Diff: nur `<Provider>/.gitignore`-Schlüssel (z. B. `Claude/.gitignore`); Log "only .gitignore hashes (#1073)".
- [ ] Step 3: CHANGELOG (`Fixed:` x2; Hinweis "tracked `platform-defaults.resolved.yaml` in Bestandsprojekten bleibt getrackt").
- [ ] Step 4: Volllauf, `code-reviewer`, PR durch `git`.
- [ ] Step 5: Commit `git add CHANGELOG.md tests/fixtures tests/test_ac01_render_identity.py` / `git commit -m "chore: rebaseline gitignore renders for managed block fixes"`.

### Task C4: #1081 Drift-Entscheidung nach den Writern

**Agent:** developer
**Depends on:** — (Welle 3; Branch `fix/drift-false-positives`)
**Files:**
- Modify: `scripts/lib/generated_file_drift.py` (:313-351 `scan_generated_file_drift` liefert `pre_text`; :354-402 `backup_drifted_files` nutzt `finding["pre_text"]`; neue `resolve_drift_findings`)
- Modify: `scripts/lib/sync_pipeline.py` (:1003-1036 `_sync_stage_generated_file_drift_scan` -> gibt Findings zurück, WARN/Backup-Block wandert in neue `_sync_stage_generated_file_drift_resolve`, vor :1647 Hash-Capture)
- Modify: `scripts/lib/cli_commands.py` (:88 Import, :1540 Rückgabewert aufnehmen, neuer Aufruf zwischen Stage 12 :1570 und Stage 13 :1573)
- Modify: `tests/test_generated_file_drift.py`, `tests/test_generated_file_drift_pipeline_wiring.py` (Erwartungen WARN/Backup wandern von der Scan- in die Resolve-Stage)

**Interfaces:**
- Produces: `scan_generated_file_drift(...) -> list[dict]` mit Findings `{"path": str, "provider": str, "pre_text": str}`; `resolve_drift_findings(findings: list[dict], project_root: Path, log: SyncLog, dry_run: bool) -> list[dict]` (liefert nur echte Änderungen; stale Baseline => `log.note("generated-file-drift", f"{path}: stale hash baseline (disk equals generated) - baseline refreshed")`; `dry_run=True` => alle Findings unverändert zurück); `_sync_stage_generated_file_drift_scan(...) -> list[dict]`; `_sync_stage_generated_file_drift_resolve(project_root, findings, args, log) -> None`.
- Consumes: `backup_drifted_files(findings, project_root, log, dry_run)` (nimmt `finding.get("pre_text")` als Backup-Inhalt, sonst Disk-Inhalt wie bisher).

- [ ] **Step 1: Failing Tests schreiben** (`tests/test_generated_file_drift.py`; Importe `from scripts.lib import generated_file_drift as gfd`, `from scripts.lib.generated_file_drift import resolve_drift_findings, backup_drifted_files`, `from scripts.lib.io import content_hash`, `from scripts.lib.log import SyncLog`)
```python
def _f(rel, pre):
    return {"path": rel, "provider": "Claude", "pre_text": pre}

def _file(tmp_path, rel, text):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p

def test_scan_findings_carry_pre_text(tmp_path, monkeypatch):
    f = _file(tmp_path, ".claude/agents/a.md", "edited")
    gfd._save_hashes(tmp_path, {".claude/agents/a.md": content_hash("orig")}, dry_run=False)
    monkeypatch.setattr(gfd, "_iter_managed_files", lambda *a, **k: [f])
    monkeypatch.setattr(gfd, "get_active_providers", lambda c, p: ["Claude"])
    assert gfd.scan_generated_file_drift(tmp_path / "am", tmp_path, {}, {"Claude": {}}) == [
        {"path": ".claude/agents/a.md", "provider": "Claude", "pre_text": "edited"}]

def test_stale_baseline_no_warning_no_backup(tmp_path):
    _file(tmp_path, ".claude/agents/a.md", "fresh")          # writer produced exactly the pre-sync text
    real = resolve_drift_findings([_f(".claude/agents/a.md", "fresh")], tmp_path, SyncLog(), dry_run=False)
    assert real == [] and list(tmp_path.rglob("*.sync-backup-*")) == []

def test_real_edit_backed_up_from_pre_text(tmp_path):         # R3
    _file(tmp_path, ".claude/agents/a.md", "generated v2")    # writer already overwrote the edit
    real = resolve_drift_findings([_f(".claude/agents/a.md", "user edit")], tmp_path, SyncLog(), dry_run=False)
    assert [r["path"] for r in real] == [".claude/agents/a.md"]
    backups = backup_drifted_files(real, tmp_path, SyncLog(), dry_run=False)
    assert len(backups) == 1 and (tmp_path / backups[0]).read_text(encoding="utf-8") == "user edit"

def test_dry_run_writes_nothing(tmp_path):                    # R3
    _file(tmp_path, ".claude/agents/a.md", "user edit")
    findings = [_f(".claude/agents/a.md", "user edit")]
    assert resolve_drift_findings(findings, tmp_path, SyncLog(), dry_run=True) == findings
    assert len(backup_drifted_files(findings, tmp_path, SyncLog(), dry_run=True)) == 1
    assert list(tmp_path.rglob("*.sync-backup-*")) == []
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_generated_file_drift.py -k "pre_text or stale_baseline or real_edit or dry_run_writes" --basetemp="$PYTEST_BASETEMP"` — erwartet: `ImportError: cannot import name 'resolve_drift_findings'` / Finding ohne `pre_text`.

- [ ] **Step 3: Implementierung**
`scan_generated_file_drift`: Findings um `"pre_text": <gelesener Text>` erweitern (beide Stellen :342 und :349). `backup_drifted_files`: `existing_content = finding["pre_text"] if finding.get("pre_text") is not None else target.read_text(...)` (bestehender Lesepfad bleibt Fallback). `resolve_drift_findings` wie in Interfaces (Disk per `read_text(encoding="utf-8")`, `OSError`/`UnicodeDecodeError` => Finding als echt behandeln). Neue Funktion <= 30 Zeilen (Modul ist Alt-Überschreitung). `_sync_stage_generated_file_drift_scan`: `findings` zurückgeben (`[]` bei disabled), Backup- und `log.warning`-Block entfernen (Prune bleibt unverändert hier). Neue `_sync_stage_generated_file_drift_resolve`: `real = resolve_drift_findings(findings, project_root, log, args.dry_run)`, dann der bisherige Backup+Warn-Block auf `real` (Text der Warnung unverändert). `cli_commands.py`: `drift_findings = _sync_stage_generated_file_drift_scan(...)` und vor Stage 13 `_sync_stage_generated_file_drift_resolve(ctx.project_root, drift_findings, ctx.args, ctx.log)`. `test_generated_file_drift_pipeline_wiring.py`: bestehende Tests, die WARN/Backup aus der Scan-Stage erwarten, rufen zusätzlich die Resolve-Stage auf.

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_generated_file_drift.py tests/test_generated_file_drift_pipeline_wiring.py tests/test_managed_index_alignment.py --basetemp="$PYTEST_BASETEMP"`.

- [ ] **Step 5: Commit**
`git add scripts/lib/generated_file_drift.py scripts/lib/sync_pipeline.py scripts/lib/cli_commands.py tests/test_generated_file_drift.py tests/test_generated_file_drift_pipeline_wiring.py`
`git commit -m "fix: decide generated-file drift after writers ran" -m "Closes #1081"`

### Task C5: #1081 Backup-Prune count-only

**Agent:** developer
**Depends on:** C4
**Files:**
- Modify: `scripts/lib/generated_file_drift.py` (:142-211 `prune_sync_backups`)
- Modify: `scripts/lib/sync_pipeline.py` (:927-931 Kommentar)
- Modify: `tests/test_generated_file_drift.py` (`test_prune_requires_both_thresholds` :579 und `test_prune_default_policy_three_and_thirty` :659 an neue Semantik anpassen)

**Interfaces:**
- Produces: `prune_sync_backups(target_dir, project_root, log, dry_run, max_age_days, max_per_source) -> list[str]` — Signatur unverändert; Semantik: ein Backup wird gelöscht, wenn mindestens `max_per_source` neuere Backups derselben Quelle existieren; `max_age_days` bleibt aus API-Stabilität erhalten und wird ignoriert; das neueste Backup überlebt immer.
- Consumes: `_sync_backup_timestamp`, `_sync_backup_source`.

- [ ] **Step 1: Failing Tests schreiben**
```python
def _backups(d, source, stamps):
    d.mkdir(parents=True, exist_ok=True)
    for s in stamps:
        (d / f"{source}.sync-backup-{s}").write_text("x", encoding="utf-8")

def test_prune_keeps_three_newest_regardless_of_age(tmp_path):
    d = tmp_path / ".claude" / "agents"
    _backups(d, "a.md", [f"20261031-0100{i:02d}" for i in range(10)])
    prune_sync_backups(d, tmp_path, SyncLog(), False, max_age_days=30, max_per_source=3)
    left = sorted(p.name for p in d.iterdir())
    assert left == [f"a.md.sync-backup-20261031-0100{i:02d}" for i in (7, 8, 9)]

def test_prune_single_old_backup_survives(tmp_path):
    d = tmp_path / ".claude" / "agents"
    _backups(d, "a.md", ["20260101-000000"])
    prune_sync_backups(d, tmp_path, SyncLog(), False, max_age_days=30, max_per_source=3)
    assert [p.name for p in d.iterdir()] == ["a.md.sync-backup-20260101-000000"]
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_generated_file_drift.py -k "three_newest_regardless or single_old" --basetemp="$PYTEST_BASETEMP"` — erwartet: erster Test lässt alle 10 Dateien stehen (Alter < 30 Tage).

- [ ] **Step 3: Implementierung**
In `prune_sync_backups` die Altersprüfung (`if (now - stamp).days <= max_age_days: continue`, :191-192) und `now = datetime.now()` entfernen; Löschbedingung `if newer < max_per_source: continue`. Docstring (:150-161) auf die neue Semantik und "age ignored since #1081" ändern; `sync_pipeline.py:927-929` Kommentar angleichen. Die beiden bestehenden Tests, die die AND-Semantik festschreiben, ersetzen (Erwartung: genau die `max_per_source` neuesten bleiben).

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_generated_file_drift.py tests/test_managed_index_alignment.py tests/test_backup_robustness.py --basetemp="$PYTEST_BASETEMP"`.

- [ ] **Step 5: Commit**
`git add scripts/lib/generated_file_drift.py scripts/lib/sync_pipeline.py tests/test_generated_file_drift.py`
`git commit -m "fix: prune sync backups by count, not age" -m "Closes #1081"`
(Der Issue-Body wird von C4 und C5 gemeinsam adressiert; `Closes #1081` steht in beiden, geschlossen wird beim PR-Merge einmal.)

### Task C6: #1084 (a)(b)(d) Excuse-Logik

**Agent:** developer
**Depends on:** C5
**Files:**
- Modify: `scripts/lib/external_tools_drift.py` (Konstante nach :136, Hook-Schleife :331-358, Infra-Root :387-423, `_dir_is_fully_managed` :200-241)
- Modify: `tests/test_external_tools_registry.py`

**Interfaces:**
- Produces: `_AGENT_META_RUNTIME_ARTIFACTS: frozenset[str] = frozenset({".guard-audit.log"})`; Infra-Root `known_names` enthält zusätzlich `Path(v).name` für `pc["mcp-config"]["committed-file"]` und `["secrets-file"]`; `_dir_is_fully_managed` gibt `saw_managed or saw_backup` zurück.
- Consumes: `scan_injection_drift`, `_is_sync_backup_name`.

- [ ] **Step 1: Failing Tests schreiben** (Muster `test_scan_injection_drift_infra_root_excuses_agent_memory_and_provider_settings_local`, `_write_framework_registry`)
```python
def _scan(tmp_path, project_root, provider_config, name):
    from scripts.lib.external_tools import scan_injection_drift
    am = tmp_path / "agent-meta"
    _write_framework_registry(am, {})
    return scan_injection_drift(am, project_root, {"ai-providers": [name]}, provider_config)

def test_guard_audit_log_not_flagged(tmp_path):
    project = tmp_path / "project"
    (project / ".claude" / "hooks").mkdir(parents=True)
    (project / ".claude" / "hooks" / ".guard-audit.log").write_text("x", encoding="utf-8")
    pc = {"Claude": {"skills_dir": ".claude/skills", "agents_dir": ".claude/agents",
                     "has_hooks": True, "hooks_dir": ".claude/hooks"}}
    assert _scan(tmp_path, project, pc, "Claude")["Claude"] == []

def test_mcp_local_json_not_flagged_but_unknown_file_is(tmp_path):
    project = tmp_path / "project"
    (project / ".opencode").mkdir(parents=True)
    (project / ".opencode" / "mcp.local.json").write_text("{}", encoding="utf-8")
    (project / ".opencode" / "evil.sh").write_text("x", encoding="utf-8")
    pc = {"Opencode": {"skills_dir": ".opencode/skills", "agents_dir": ".opencode/agents",
                       "mcp-config": {"committed-file": "opencode.json",
                                      "secrets-file": ".opencode/mcp.local.json"}}}
    paths = [f["path"] for f in _scan(tmp_path, project, pc, "Opencode")["Opencode"]]
    assert paths == [".opencode/evil.sh"]

def test_backup_only_dir_is_managed(tmp_path):
    project = tmp_path / "project"
    d = project / ".claude" / "hooks" / "old-dir"
    d.mkdir(parents=True)
    (d / "a.sh.sync-backup-20261031-000000").write_text("x", encoding="utf-8")
    pc = {"Claude": {"skills_dir": ".claude/skills", "agents_dir": ".claude/agents",
                     "has_hooks": True, "hooks_dir": ".claude/hooks"}}
    assert _scan(tmp_path, project, pc, "Claude")["Claude"] == []
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_external_tools_registry.py -k "guard_audit or mcp_local_json or backup_only" --basetemp="$PYTEST_BASETEMP"` — erwartet: je ein Finding (`.claude/hooks/.guard-audit.log`, `.opencode/mcp.local.json`, `.claude/hooks/old-dir`).

- [ ] **Step 3: Implementierung**
(a) in der Schleife :331 nach den Sidecar-Index-Checks: `if kind == "hook" and child.name in _AGENT_META_RUNTIME_ARTIFACTS: continue`. (b) nach der `_INFRA_ROOT_KNOWN_KEYS`-Schleife (:388-391): `for _k in ("committed-file", "secrets-file"): _v = (pc.get("mcp-config") or {}).get(_k); if _v: known_names.add(Path(_v).name)`. (d) in `_dir_is_fully_managed`: `saw_backup = False` initialisieren, im Zweig `_is_sync_backup_name(name)` `saw_backup = True` setzen, `return saw_managed or saw_backup`. Kommentar zu `.guard-audit.log` (geschrieben von `hooks/1-generic/orchestrator-guard-impl.sh`, Laufzeit-Output, nicht Sync-Output).

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_external_tools_registry.py --basetemp="$PYTEST_BASETEMP"` (bestehendes `test_scan_injection_drift_flags_empty_dir` bleibt grün).

- [ ] **Step 5: Commit**
`git add scripts/lib/external_tools_drift.py tests/test_external_tools_registry.py`
`git commit -m "fix: excuse own runtime artifacts in external-tools drift" -m "Closes #1084"`

### Task C7: #1084 (e) Provider-Key `infra_known_names`

**Agent:** developer
**Depends on:** C6
**Files:**
- Modify: `config/ai-providers.yaml` (Opencode-Block ab :232: `infra_known_names: [.gitignore, package.json, package-lock.json, node_modules, bun.lock]`)
- Modify: `scripts/lib/external_tools_drift.py` (Infra-Root-Schleife :387 ff.)
- Modify: `tests/test_external_tools_registry.py`
- Prüfen (Grep, anpassen nur bei Treffer): Tests/Schemas, die Provider-Keys enumerieren (`provider-capabilities.yaml`-Parität)

**Interfaces:**
- Produces: optionaler Provider-Key `infra_known_names: list[str]`; `known_names.update(Path(n).name for n in pc.get("infra_known_names") or [])`.
- Consumes: C6-Struktur.

- [ ] **Step 1: Failing Test schreiben**
```python
def test_infra_known_names_excused_but_unknown_file_flagged(tmp_path):
    project = tmp_path / "project"
    (project / ".opencode" / "node_modules").mkdir(parents=True)
    (project / ".opencode" / "package.json").write_text("{}", encoding="utf-8")
    (project / ".opencode" / "evil.sh").write_text("x", encoding="utf-8")
    pc = {"Opencode": {"skills_dir": ".opencode/skills", "agents_dir": ".opencode/agents",
                       "infra_known_names": ["package.json", "node_modules"]}}
    paths = [f["path"] for f in _scan(tmp_path, project, pc, "Opencode")["Opencode"]]
    assert paths == [".opencode/evil.sh"]

def test_opencode_declares_runtime_infra_names():
    import yaml
    data = yaml.safe_load((REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))
    assert {"package.json", "package-lock.json", "node_modules", ".gitignore"} <= set(
        data["providers"]["Opencode"]["infra_known_names"])
```
(`REPO_ROOT` im Testmodul definieren, falls nicht vorhanden: `Path(__file__).resolve().parent.parent`.)

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_external_tools_registry.py -k "infra_known_names or runtime_infra" --basetemp="$PYTEST_BASETEMP"` — erwartet: `.opencode/package.json` und `.opencode/node_modules` geflaggt bzw. `KeyError: 'infra_known_names'`.

- [ ] **Step 3: Implementierung**
Key in `ai-providers.yaml` (Kommentar: Opencode-Runtime legt sie an, npm-Plugins); in `external_tools_drift.py` nach dem `mcp-config`-Block aus C6 `known_names.update(Path(n).name for n in (pc.get("infra_known_names") or []))`. Kein Provider-Name im Code.

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_external_tools_registry.py tests/test_provider_matrix_sync.py -k "not matrix_full" --basetemp="$PYTEST_BASETEMP"` (falls `-k` nicht passt: ganze Datei `tests/test_external_tools_registry.py` plus `python3 scripts/sync.py --validate`).

- [ ] **Step 5: Commit**
`git add config/ai-providers.yaml scripts/lib/external_tools_drift.py tests/test_external_tools_registry.py`
`git commit -m "fix: declare opencode runtime files as known infra names" -m "Closes #1084"`

### Task C8: #1084 (c) Report-Merge in den ersten `has_rules`-Provider

**Agent:** developer
**Depends on:** C7
**Files:**
- Modify: `scripts/lib/external_tools_drift.py` (`_generate_drift_content` :45-62, `render_injection_drift_artifacts` :65-113)
- Modify: `tests/test_external_tools_registry.py`

**Interfaces:**
- Produces: `render_injection_drift_artifacts(findings_by_provider, project_root, provider_config, log, dry_run) -> None` (Signatur unverändert) — Findings von Providern ohne `has_rules` werden mit `{"provider": <Name>}` getaggt dem ersten `has_rules`-Provider (Reihenfolge von `findings_by_provider`) zugeschlagen; Zeilenformat bei Tag: `` - `{path}` ({kind}) [{provider}] — {tool_label} ``; ohne `has_rules`-Provider zusätzlich `log.note("external-tools-drift", f"{n} findings only in sync.log (no provider with has_rules)")`.
- Consumes: `_DRIFT_CAP = 10`, `write_checked`.

- [ ] **Step 1: Failing Tests schreiben**
```python
def test_non_rules_provider_findings_in_first_rules_report(tmp_path):
    from scripts.lib.external_tools import render_injection_drift_artifacts
    project = tmp_path / "project"
    (project / ".claude" / "rules").mkdir(parents=True)
    findings = {"Claude": [],
                "Gemini": [{"path": ".gemini/rogue", "kind": "other", "tool": None}]}
    pc = {"Claude": {"has_rules": True, "rules_dir": ".claude/rules"}, "Gemini": {}}
    render_injection_drift_artifacts(findings, project, pc, SyncLog(), dry_run=False)
    text = (project / ".claude" / "rules" / "external-tools-drift.md").read_text(encoding="utf-8")
    assert "`.gemini/rogue` (other) [Gemini]" in text

def test_no_rules_provider_logs_note_only(tmp_path):
    from scripts.lib.external_tools import render_injection_drift_artifacts
    log = SyncLog()
    render_injection_drift_artifacts({"Gemini": [{"path": ".gemini/rogue", "kind": "other", "tool": None}]},
                                     tmp_path, {"Gemini": {}}, log, dry_run=False)
    assert not list(tmp_path.rglob("external-tools-drift.md"))
    assert any("only in sync.log" in i for i in log.infos)      # SyncLog.note() -> log.infos
    assert len(log.warnings) == 1                                # per-finding warning stays
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_external_tools_registry.py -k "first_rules_report or logs_note_only" --basetemp="$PYTEST_BASETEMP"` — erwartet: Claude-Datei existiert nicht bzw. ohne `[Gemini]`.

- [ ] **Step 3: Implementierung**
In `render_injection_drift_artifacts` vor der Schleife: `rules_providers = [p for p in findings_by_provider if provider_config.get(p, {}).get("has_rules")]`; `extras = [{**f, "provider": p} for p, fs in findings_by_provider.items() if p not in rules_providers for f in fs]`; für `p == rules_providers[0]` Findings = eigene + `extras`. Warnungs-Logging je Finding unverändert pro Quell-Provider. `_generate_drift_content`: `tag = f" [{f['provider']}]" if f.get("provider") else ""` in die Zeile einfügen. Cap 10 unverändert.

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_external_tools_registry.py --basetemp="$PYTEST_BASETEMP"`.

- [ ] **Step 5: Commit**
`git add scripts/lib/external_tools_drift.py tests/test_external_tools_registry.py`
`git commit -m "fix: merge non-rules provider drift into rules report" -m "Closes #1084"`

### Task C9: Close-out PR C2

**Agent:** developer -> code-reviewer -> git
**Depends on:** C8
**Files:** Modify `CHANGELOG.md`; kein AC-01-Diff erwartet (`python3 -m pytest tests/test_ac01_render_identity.py --basetemp="$PYTEST_BASETEMP"` muss ohne `--write` grün sein, sonst Ursache klären)
**Interfaces:** Consumes: Close-out-Protokoll. Produces: PR `fix/drift-false-positives` mit `Closes #1081`, `Closes #1084`.

- [ ] Step 1: Rebase auf `main`; `sync_pipeline.py`/`cli_commands.py`-Konflikte mit den zuvor gemergten PRs (D1, E, G) manuell lösen.
- [ ] Step 2: AC-01-Test ohne `--write` laufen lassen.
- [ ] Step 3: CHANGELOG (`Fixed:` #1081 mit "behavior change: prune keeps the 3 newest backups per source regardless of age", #1084).
- [ ] Step 4: Volllauf, `code-reviewer`, PR durch `git`.
- [ ] Step 5: Commit `git add CHANGELOG.md` / `git commit -m "docs: changelog entries for drift false-positive fixes"`.

## Tasks Cluster D

Zwei PRs: **D1** (`fix/admin-symlink-and-validate`, Welle 1/2: Tasks D1-D4) und **D2** (`fix/yaml-comment-preserving-writer`, Welle 3: Tasks D5-D8). Abweichung zu Verify-B: `admin-server.py` `resolve_path` liegt bei :1065-1118 (Containment-Check :1114-1117); `_route_put_config` :3887-3946 und `_write_project_section` :5176-5200 bestätigt; `auto_commit`-Schemaregeln stehen in `config/project-config.schema.json` :1495-1613. Entscheidung D14 präzisiert: der Round-Trip-Guard schützt für `project` nur den Fallback-Pfad (Voll-Dump), weil das Admin-UI keinen `__allow_lossy__`-Dialog besitzt (`grep allow_lossy docs/ui/admin-ui.html` ohne Treffer) und Kommentarverlust innerhalb einer bewusst geänderten Section dokumentiert akzeptiert ist.

### Task D1: #1095 `resolve_path` bei Symlink-`.agent-meta`

**Agent:** developer
**Depends on:** —
**Files:**
- Modify: `scripts/admin-server.py` (`ConfigManager.resolve_path` :1099-1118, `ConfigManager.write` direkt nach :1153)
- Modify: `tests/test_admin_server.py` (neue pytest-Funktionen am Dateiende; `admin_server` ist das Modul-Global, `SecurityError` = `admin_server.SecurityError`)

**Interfaces:**
- Produces: `resolve_path(key) -> Path` erlaubt zusätzlich Pfade im Fallback-Zweig (`rel.startswith("config/")`, primary fehlt), wenn `target` unter `(self.root / ".agent-meta").resolve() / "config"` liegt (`config` selbst NICHT aufgelöst); `write()` wirft `SecurityError("framework symlink is read-only via Admin UI")`, wenn der aufgelöste Pfad außerhalb von `self.root` liegt.
- Consumes: `SUPER_ADMIN_FILES` (:204), `PROJECT_FILES` (:217).

- [ ] **Step 1: Failing Tests schreiben**
```python
import pytest

def _symlinked_root(tmp_path, config_is_link=False):
    fw = tmp_path / "fw"
    if config_is_link:
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "role-defaults.yaml").write_text("secret: 1\n", encoding="utf-8")
        fw.mkdir()
        (fw / "config").symlink_to(outside, target_is_directory=True)
    else:
        (fw / "config").mkdir(parents=True)
        (fw / "config" / "role-defaults.yaml").write_text("roles:\n  x: 1\n", encoding="utf-8")
    root = tmp_path / "proj"
    root.mkdir()
    (root / ".agent-meta").symlink_to(fw, target_is_directory=True)
    return root

def test_symlinked_agent_meta_framework_defaults_readable(tmp_path):
    mgr = admin_server.ConfigManager(_symlinked_root(tmp_path), mode="project_admin")
    assert mgr.read("role-defaults") == {"roles": {"x": 1}}

def test_symlink_target_outside_config_still_blocked(tmp_path):          # R5
    mgr = admin_server.ConfigManager(_symlinked_root(tmp_path, config_is_link=True), mode="project_admin")
    with pytest.raises(admin_server.SecurityError):
        mgr.read("role-defaults")

def test_write_via_symlink_blocked(tmp_path):                            # R5
    root = _symlinked_root(tmp_path)
    mgr = admin_server.ConfigManager(root, mode="super_admin")
    with pytest.raises(admin_server.SecurityError, match="read-only"):
        mgr.write("role-defaults", {"roles": {"y": 2}})
    assert (tmp_path / "fw" / "config" / "role-defaults.yaml").read_text(encoding="utf-8") == "roles:\n  x: 1\n"

def test_dotdot_traversal_still_blocked(tmp_path):
    mgr = admin_server.ConfigManager(_symlinked_root(tmp_path), mode="project_admin")
    with pytest.raises(admin_server.SecurityError):
        mgr.resolve_path("../etc")
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_admin_server.py -k "symlink or dotdot" --basetemp="$PYTEST_BASETEMP"` — erwartet: `SecurityError: resolved path escapes root` im ersten Test, `DID NOT RAISE ... read-only` im dritten.

- [ ] **Step 3: Implementierung**
In `resolve_path`: `used_fallback = False`; im Zweig `if fallback.exists(): target = fallback; used_fallback = True`. Containment-Block (:1113-1117) ersetzen durch:
```python
        try:
            target.relative_to(self.root)
        except ValueError as exc:
            fw_config = (self.root / ".agent-meta").resolve() / "config"
            try:
                inside_fw_config = used_fallback and target.relative_to(fw_config) is not None
            except ValueError:
                inside_fw_config = False
            if not inside_fw_config:
                raise SecurityError(f"resolved path escapes root: {target}") from exc
```
In `write()` direkt nach `path = self.resolve_path(key)`: `try: path.relative_to(self.root)` / `except ValueError: raise SecurityError("framework symlink is read-only via Admin UI")`. Docstring-Hinweis auf die Symlink-Semantik; `# pragma: no cover` am alten Zweig entfernen.

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_admin_server.py --basetemp="$PYTEST_BASETEMP"`.

- [ ] **Step 5: Commit**
`git add scripts/admin-server.py tests/test_admin_server.py`
`git commit -m "fix: allow symlinked framework config in admin path resolve" -m "Closes #1095"`

### Task D2: #1091 `auto_commit_violations` und Fail-safe-Resolver

**Agent:** developer
**Depends on:** D1
**Files:**
- Modify: `scripts/lib/auto_commit.py` (neue Funktion nach `resolve_auto_commit_config` :142; `resolve_auto_commit_config` selbst)
- Create: `tests/test_auto_commit_violations.py`

**Interfaces:**
- Produces: `auto_commit_violations(config: dict) -> list[str]` (stdlib, ohne jsonschema; Nachrichtenpräfix `auto_commit.`): (i) `mode` ∉ `off|suggest|auto|custom`; (ii) `triggers` kein Array oder Wert ∉ `task-boundary|per-edit|context-pressure|file-count-threshold|custom`; (iii) nicht-leeres `triggers` bei `mode != "auto"`; (iv) `mode == "custom"` oder `"custom"` in `triggers` ohne nicht-leeren String `custom_script`; (v) unbekannter Schlüssel; (vi) `file_count_threshold` kein int >= 1 (bool abgelehnt). Block fehlt/`None` => `[]`. `resolve_auto_commit_config(config, active_roles, agent_meta_root, platform=None) -> dict` liefert bei Violations `{"version": ALLOWLIST_VERSION, "mode": "off", "eligible_roles": [], "triggers": [], "file_count_threshold": 5, "custom_script": None, "secret_scan": True}`.
- Consumes: bestehende Konstanten `ALLOWLIST_VERSION`.

- [ ] **Step 1: Failing Tests schreiben** (`tests/test_auto_commit_violations.py`)
```python
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from lib.auto_commit import auto_commit_violations, resolve_auto_commit_config

def test_valid_and_absent_blocks_have_no_violations():
    assert auto_commit_violations({}) == []
    assert auto_commit_violations({"auto_commit": None}) == []
    assert auto_commit_violations({"auto_commit": {"mode": "auto", "triggers": ["task-boundary"]}}) == []
    assert auto_commit_violations({"auto_commit": {"mode": "custom", "custom_script": "x.sh"}}) == []

def test_triggers_with_mode_off_is_violation():
    v = auto_commit_violations({"auto_commit": {"mode": "off", "triggers": ["task-boundary"]}})
    assert v == ["auto_commit.triggers is only valid with mode: auto"]

def test_custom_without_script_is_violation():
    msg = "auto_commit.custom_script is required for mode: custom or trigger: custom"
    assert auto_commit_violations({"auto_commit": {"mode": "custom"}}) == [msg]
    assert auto_commit_violations({"auto_commit": {"mode": "auto", "triggers": ["custom"], "custom_script": " "}}) == [msg]

def test_unknown_values_and_keys():
    v = auto_commit_violations({"auto_commit": {"mode": "loose", "triggers": ["nope"], "bogus": 1,
                                                "file_count_threshold": 0}})
    assert any("auto_commit.mode" in m for m in v)
    assert any("unknown value" in m and "nope" in m for m in v)
    assert any("bogus" in m for m in v)
    assert any("file_count_threshold" in m for m in v)

def test_resolve_fail_safe_on_violation():
    cfg = {"auto_commit": {"mode": "off", "triggers": ["task-boundary"]}}
    out = resolve_auto_commit_config(cfg, ["developer"], REPO_ROOT)
    assert out["mode"] == "off" and out["eligible_roles"] == [] and out["triggers"] == []

def test_valid_config_unchanged():                                       # R4
    cfg = {"auto_commit": {"mode": "auto", "triggers": ["task-boundary"]}}
    out = resolve_auto_commit_config(cfg, ["developer", "git"], REPO_ROOT)
    assert out["mode"] == "auto" and out["eligible_roles"] == ["developer"]
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_auto_commit_violations.py --basetemp="$PYTEST_BASETEMP"` — erwartet: `ImportError: cannot import name 'auto_commit_violations'`.

- [ ] **Step 3: Implementierung**
Modulkonstanten `_MODES`, `_TRIGGERS`, `_KEYS = {"mode","triggers","file_count_threshold","custom_script","secret_scan"}`; `auto_commit_violations` wie in Interfaces, Nachrichtentexte exakt wie die Tests (`"auto_commit.triggers is only valid with mode: auto"`, `"auto_commit.custom_script is required for mode: custom or trigger: custom"`, `f"auto_commit.triggers contains unknown value(s): {', '.join(bad)}"`, `f"auto_commit.mode '{mode}' is not one of off|suggest|auto|custom"`, `f"auto_commit has unknown key(s): {', '.join(unknown)}"`, `"auto_commit.file_count_threshold must be an integer >= 1"`). In `resolve_auto_commit_config` am Anfang: bei `auto_commit_violations(config)` das Fail-safe-Dict zurückgeben.

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_auto_commit_violations.py tests/test_auto_commit_lib.py tests/test_auto_commit_allowlist_pipeline.py tests/test_auto_commit_schema.py --basetemp="$PYTEST_BASETEMP"`.

- [ ] **Step 5: Commit**
`git add scripts/lib/auto_commit.py tests/test_auto_commit_violations.py`
`git commit -m "fix: fail safe on schema-invalid auto_commit blocks" -m "Closes #1091"`

### Task D3: #1091 `--validate` rc=1 und Sync-WARN

**Agent:** developer
**Depends on:** D2
**Files:**
- Modify: `scripts/lib/cli_commands.py` (`_handle_validate` :1378, Block nach den `_unpaired_tags` :1424-1428)
- Modify: `scripts/lib/sync_pipeline.py` (`_sync_stage_auto_commit_allowlist` :1659-1683; Import :38)
- Modify: `tests/test_auto_commit_violations.py`

**Interfaces:**
- Produces: `--validate` zählt jede Violation als `consistency_errors` und loggt `log.warning(f"config-audit [ERROR] auto_commit: {v}")`; die Allowlist-Stage loggt je Violation `log.warn(f"auto_commit is invalid ({v}); commit authority disabled (mode: off)")`.
- Consumes: `auto_commit_violations(config)` (D2).

- [ ] **Step 1: Failing Tests schreiben** (E2E im Muster `tests/test_auto_commit_allowlist_pipeline.py`: `_run_sync`)
```python
import json, subprocess

def _project(tmp_path, ac):
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        "project:\n  name: t\n  prefix: t\nai-providers: [Claude]\n"
        "roles: [orchestrator, developer, git]\n" + ac, encoding="utf-8")
    return tmp_path

def _sync(project, *flags):
    return subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "sync.py"), *flags],
                          cwd=project, capture_output=True, text=True)

def test_validate_rc1_on_triggers_with_mode_off(tmp_path):
    p = _project(tmp_path, "auto_commit:\n  mode: 'off'\n  triggers: [task-boundary]\n")
    r = _sync(p, "--validate")
    assert r.returncode == 1 and "triggers is only valid with mode: auto" in (r.stdout + r.stderr)

def test_validate_rc1_on_custom_without_script(tmp_path):
    p = _project(tmp_path, "auto_commit:\n  mode: custom\n")
    assert _sync(p, "--validate").returncode == 1

def test_sync_rc0_but_allowlist_fail_safe(tmp_path):                     # R4
    p = _project(tmp_path, "auto_commit:\n  mode: auto\n  triggers: [custom]\n")
    r = _sync(p)
    assert r.returncode == 0, r.stderr
    data = json.loads((p / ".meta-config" / "auto-commit-allowlist.json").read_text(encoding="utf-8"))
    assert data["mode"] == "off" and data["eligible_roles"] == []
    assert "commit authority disabled" in r.stderr

def test_validate_rc0_on_valid_config(tmp_path):
    p = _project(tmp_path, "auto_commit:\n  mode: auto\n  triggers: [task-boundary]\n")
    assert _sync(p, "--validate").returncode == 0
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_auto_commit_violations.py -k "validate or fail_safe" --basetemp="$PYTEST_BASETEMP"` — erwartet: `--validate` rc 0 statt 1; Allowlist mit `mode == "auto"`-Rest bzw. fehlende WARN-Zeile (Fail-safe greift ab D2 bereits für `mode`, die WARN-Ausgabe fehlt).

- [ ] **Step 3: Implementierung**
`_handle_validate`: nach dem `_unpaired_tags`-Block `from lib.auto_commit import auto_commit_violations`; `for _v in auto_commit_violations(config): log.warning(f"config-audit [ERROR] auto_commit: {_v}"); consistency_errors += 1`. `_sync_stage_auto_commit_allowlist`: vor `resolve_auto_commit_config` `for v in auto_commit_violations(config): log.warn(...)` (Import neben :38); Exit-Code unverändert. Kein Zeit-Grace.

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_auto_commit_violations.py tests/test_auto_commit_allowlist_pipeline.py --basetemp="$PYTEST_BASETEMP"` und `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate` (Self-Hosting bleibt rc 0).

- [ ] **Step 5: Commit**
`git add scripts/lib/cli_commands.py scripts/lib/sync_pipeline.py tests/test_auto_commit_violations.py`
`git commit -m "fix: fail validate on schema-invalid auto_commit config" -m "Closes #1091"`

### Task D4: Close-out PR D1

**Agent:** developer -> code-reviewer -> git
**Depends on:** D3
**Files:** Modify `CHANGELOG.md`; kein AC-01-Diff erwartet (Basis-Configs haben `auto_commit.mode: off`; `python3 -m pytest tests/test_ac01_render_identity.py --basetemp="$PYTEST_BASETEMP"` ohne `--write` muss grün sein)
**Interfaces:** Consumes: Close-out-Protokoll. Produces: PR `fix/admin-symlink-and-validate` mit `Closes #1095`, `Closes #1091`.

- [ ] Step 1: Rebase auf `main`.
- [ ] Step 2: AC-01-Test ohne `--write`.
- [ ] Step 3: CHANGELOG: `Fixed:` #1095; #1091 mit `behavior change: --validate now exits 1 for schema-invalid auto_commit blocks (sync stays rc 0 and writes mode: off)`.
- [ ] Step 4: Volllauf, `code-reviewer`, PR durch `git`.
- [ ] Step 5: Commit `git add CHANGELOG.md` / `git commit -m "docs: changelog entries for admin and validate fixes"`.

### Task D5: #1074/#1092 Modul `yaml_patch.patch_top_level`

**Agent:** developer
**Depends on:** — (Welle 3; Branch `fix/yaml-comment-preserving-writer`, nach Merge von PR D1 rebasen)
**Files:**
- Create: `scripts/lib/yaml_patch.py` (<= 200 Zeilen)
- Create: `tests/test_yaml_patch.py`

**Interfaces:**
- Produces: `patch_top_level(original_text: str, new_doc: dict, dump_fn: Callable[[dict], str], comments: Optional[dict] = None) -> Optional[str]`. Semantik: Zerlegung in Präfix (Kommentare vor dem ersten Key) und Top-Level-Segmente (Key-Zeile in Spalte 0 + zugehörige Folgezeilen; führende Kommentar-/Leerzeilen gehören zum folgenden Key); unveränderte Keys (`old_doc[k] == new_doc[k]`) bleiben byte-identisch; geänderte Keys: führende Kommentarzeilen des alten Segments + `dump_fn({k: new_doc[k]})`; entfernte Keys: Segment samt führenden Kommentaren entfernt; neue Keys: am Ende angehängt, davor optional `# {comments[k]}\n`; Originalreihenfolge bleibt. Rückgabe `None` bei: Mehrdokument (`^---`/`^...` Zeile), Anker/Alias (`&name`/`*name` in Nicht-Kommentarzeilen), Tab-Einrückung, `old_doc` kein Mapping, YAML-Fehler, oder Selbstcheck `yaml.safe_load(result) != new_doc`.
- Consumes: PyYAML (`yaml`, im Repo bereits Abhängigkeit des Syncers).

- [ ] **Step 1: Failing Tests schreiben** (`tests/test_yaml_patch.py`)
```python
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import yaml
from lib.yaml_patch import patch_top_level

def dump(d):
    return yaml.safe_dump(d, sort_keys=False, default_flow_style=False, allow_unicode=True)

ORIG = ("# header comment\nproject:\n  name: x\n# keep me\nroles:\n- a\n- b\n"
        "\n# about presets\ntier-preset: Normal\n")

def test_unchanged_segments_byte_identical():
    assert patch_top_level(ORIG, yaml.safe_load(ORIG), dump) == ORIG

def test_added_top_level_key_appended_with_comment():
    doc = yaml.safe_load(ORIG); doc["speech-mode"] = "short"
    out = patch_top_level(ORIG, doc, dump, comments={"speech-mode": "Kommunikationsstil"})
    assert out == ORIG + "# Kommunikationsstil\nspeech-mode: short\n"

def test_changed_section_rerendered_other_sections_untouched():
    doc = yaml.safe_load(ORIG); doc["roles"] = ["a", "b", "c"]
    out = patch_top_level(ORIG, doc, dump)
    assert out.startswith("# header comment\nproject:\n  name: x\n# keep me\nroles:\n- a\n- b\n- c\n")
    assert out.endswith("\n# about presets\ntier-preset: Normal\n")

def test_removed_key():
    doc = yaml.safe_load(ORIG); del doc["roles"]
    assert patch_top_level(ORIG, doc, dump) == (
        "# header comment\nproject:\n  name: x\n\n# about presets\ntier-preset: Normal\n")

def test_inline_comment_and_crlf_preserved():
    text = "a: 1  # inline\r\nb: 2\r\n"
    doc = yaml.safe_load(text); doc["b"] = 3
    out = patch_top_level(text, doc, dump)
    assert out.startswith("a: 1  # inline\r\n") and yaml.safe_load(out) == {"a": 1, "b": 3}

def test_anchor_document_returns_none():
    text = "a: &x 1\nb: *x\n"
    assert patch_top_level(text, yaml.safe_load(text), dump) is None

def test_multi_document_and_non_mapping_return_none():
    assert patch_top_level("a: 1\n---\nb: 2\n", {"a": 1}, dump) is None
    assert patch_top_level("- a\n- b\n", {"a": 1}, dump) is None

def test_selfcheck_failure_returns_none():
    doc = yaml.safe_load(ORIG); doc["roles"] = ["z"]
    assert patch_top_level(ORIG, doc, lambda d: "roles: [unclosed\n") is None
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_yaml_patch.py --basetemp="$PYTEST_BASETEMP"` — erwartet: `ModuleNotFoundError: No module named 'lib.yaml_patch'`.

- [ ] **Step 3: Implementierung**
Modul `scripts/lib/yaml_patch.py` (`from __future__ import annotations`, stdlib + `yaml`): Key-Regex `^(?P<key>"[^"]+"|'[^']+'|[A-Za-z0-9_][^\s#:]*):(?:[ \t]|$)`; `_split(text) -> (prefix: str, segments: list[tuple[str, str]])` über `text.splitlines(keepends=True)`; beim Erreichen einer Key-Zeile wandert der maximale Rest-Block aus Leer-/`#`-Spalte-0-Zeilen am Ende des vorigen Segments (bzw. des Präfix) in das neue Segment. `_leading_comments(segment)` = Zeilen vor der Key-Zeile. Beim Anhängen eines Segments, dessen Text nicht auf `\n` endet, ein `\n` ergänzen. Kein Fallback in diesem Modul (der Aufrufer entscheidet).

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_yaml_patch.py --basetemp="$PYTEST_BASETEMP"`; `wc -l scripts/lib/yaml_patch.py` <= 200.

- [ ] **Step 5: Commit**
`git add scripts/lib/yaml_patch.py tests/test_yaml_patch.py`
`git commit -m "feat: add top-level yaml segment patcher" -m "Refs #1074, #1092"`

### Task D6: #1074 `fill_defaults` über `yaml_patch` mit `materialize_presets`

**Agent:** developer
**Depends on:** D5
**Files:**
- Modify: `scripts/lib/config.py` (`fill_defaults` :1027-1169, `_write_yaml_with_comments` :1172-1201; neue Konstante `_SYNC_SKIPPED_DEFAULT_KEYS` nach :161)
- Modify: `scripts/lib/sync_pipeline.py` (:167)
- Create: `tests/test_fill_defaults_comments.py`

**Interfaces:**
- Produces: `fill_defaults(config_path: Path, agent_meta_root: Path, log: SyncLog, dry_run: bool, silent: bool = False, materialize_presets: bool = True) -> None`; `_SYNC_SKIPPED_DEFAULT_KEYS = frozenset({"rules-preset","speech-mode","tier-preset","se-focus","max-parallel-agents","debug-mode","allow-committed-secrets"})` — bei `materialize_presets=False` werden diese Keys im Top-Level-Fill übersprungen (`repo_containment` und `project.short` bleiben); `_write_yaml_with_comments` versucht zuerst `patch_top_level(original, data, dump_fn, comments=descriptions)` und fällt bei `None` auf den bisherigen Voll-Dump zurück (+ `log`-freier Hinweis entfällt, der Aufrufer loggt nicht).
- Consumes: `patch_top_level` (D5), `yaml_dump_preserving_multiline`.

- [ ] **Step 1: Failing Tests schreiben** (`tests/test_fill_defaults_comments.py`; Muster `tests/test_project_yaml_permissions_864.py`)
```python
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from lib.config import fill_defaults
from lib.log import SyncLog

TEXT = ("# my header\nproject:\n  name: t\n  prefix: t\n  short: T\n"
        "ai-providers: [Claude]  # inline\nroles:\n- orchestrator\n- developer\n")

def _cfg(tmp_path):
    p = tmp_path / ".meta-config" / "project.yaml"
    p.parent.mkdir()
    p.write_text(TEXT, encoding="utf-8")
    return p

def test_sync_fill_keeps_comments_and_skips_preset_defaults(tmp_path):
    p = _cfg(tmp_path)
    fill_defaults(p, REPO_ROOT, SyncLog(), False, silent=True, materialize_presets=False)
    out = p.read_text(encoding="utf-8")
    assert out.startswith("# my header\nproject:") and "# inline" in out
    assert "repo_containment:" in out
    for key in ("speech-mode:", "tier-preset:", "rules-preset:", "max-parallel-agents:"):
        assert key not in out

def test_second_run_is_zero_diff(tmp_path):
    p = _cfg(tmp_path)
    fill_defaults(p, REPO_ROOT, SyncLog(), False, silent=True, materialize_presets=False)
    first = p.read_bytes()
    fill_defaults(p, REPO_ROOT, SyncLog(), False, silent=True, materialize_presets=False)
    assert p.read_bytes() == first

def test_explicit_fill_defaults_materializes_presets_and_keeps_comments(tmp_path):
    p = _cfg(tmp_path)
    fill_defaults(p, REPO_ROOT, SyncLog(), False)
    out = p.read_text(encoding="utf-8")
    assert "speech-mode:" in out and "tier-preset:" in out
    assert "# my header" in out and "# inline" in out
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_fill_defaults_comments.py --basetemp="$PYTEST_BASETEMP"` — erwartet: `TypeError: fill_defaults() got an unexpected keyword argument 'materialize_presets'`.

- [ ] **Step 3: Implementierung**
Signatur erweitern; im Top-Level-Fill (:1060-1069) `if not materialize_presets and field in _SYNC_SKIPPED_DEFAULT_KEYS: continue`; den nested-`dod`-Fill (:1091-1103) ebenfalls nur bei `materialize_presets`. `_write_yaml_with_comments` mit `patch_top_level` (Original-Text aus `path.read_text`, `dump_fn` ruft `yaml_dump_preserving_multiline(_yaml, d, buf, allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2)` in einen `io.StringIO`; `comments={name: desc for name, desc in auto_filled if "." not in name}`), bei `None` bestehender Pfad. `sync_pipeline.py:167`: `fill_defaults(config_path, agent_meta_root, log, args.dry_run, silent=True, materialize_presets=False)`. `--fill-defaults`/`--init` (`cli_commands.py:749`) bleiben bei Default `True`. Danach `config = load_config(config_path)` (:169) liest Defaults weiterhin über Laufzeit-Fallbacks (`config_field_defaults`).

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_fill_defaults_comments.py tests/test_version_bookkeeping.py tests/test_config_variable_fallbacks.py tests/test_project_yaml_permissions_864.py tests/test_meta_optimizer_refill.py tests/test_yaml_multiline_roundtrip.py --basetemp="$PYTEST_BASETEMP"` und `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`.

- [ ] **Step 5: Commit**
`git add scripts/lib/config.py scripts/lib/sync_pipeline.py tests/test_fill_defaults_comments.py`
`git commit -m "fix: keep project.yaml comments when auto-filling defaults" -m "Closes #1074"`

### Task D7: #1092 Admin-Write `project` über `yaml_patch`

**Agent:** developer
**Depends on:** D6, D4 (gleiche Datei `admin-server.py`, nach Merge von PR D1)
**Files:**
- Modify: `scripts/admin-server.py` (`ConfigManager.write` :1134-1216; `_route_put_config` :3921-3942; `_write_project_section` :5176-5200)
- Modify: `tests/test_admin_server.py`

**Interfaces:**
- Produces: `ConfigManager.write(key, data, *, allow_lossy=False) -> dict` — für `key == "project"` und existierende Datei: `patch_top_level(original, data, dump_fn)`; bei `None` Voll-Dump + `assert_roundtrip_preserved(original, new_text, context=f"config/{path.name}", allow_lossy=allow_lossy)` (nur Fallback-Pfad, siehe Cluster-Notiz); `_route_put_config("project")` und `_write_project_section` poppen `ALLOW_LOSSY_KEY` aus dem Body und reichen `allow_lossy` durch.
- Consumes: `patch_top_level`, `lib.yaml_roundtrip.ALLOW_LOSSY_KEY`, `assert_roundtrip_preserved`, `YamlRoundTripLoss`.

- [ ] **Step 1: Failing Tests schreiben** (`tests/test_admin_server.py`, pytest-Funktionen)
```python
PROJECT_YAML = "# top\nproject:\n  name: t\n  prefix: t\n# keep\nroles:\n- orchestrator\nspeech-mode: full  # inline\n"

def _project_root(tmp_path, text=PROJECT_YAML):
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(text, encoding="utf-8")
    return tmp_path

def test_project_write_keeps_comments_outside_changed_section(tmp_path):
    root = _project_root(tmp_path)
    mgr = admin_server.ConfigManager(root, mode="project_admin")
    data = mgr.read("project"); data["roles"] = ["orchestrator", "developer"]
    mgr.write("project", data)
    out = (root / ".meta-config" / "project.yaml").read_text(encoding="utf-8")
    assert "# top" in out and "# inline" in out and "- developer" in out

def test_project_write_does_not_materialize_defaults(tmp_path):
    root = _project_root(tmp_path)
    mgr = admin_server.ConfigManager(root, mode="project_admin")
    mgr.write("project", mgr.read("project"))
    assert (root / ".meta-config" / "project.yaml").read_text(encoding="utf-8") == PROJECT_YAML

def test_project_write_fallback_is_guarded_unless_lossy(tmp_path):
    root = _project_root(tmp_path, "# top\na: &x 1\nb: *x\n")
    mgr = admin_server.ConfigManager(root, mode="project_admin")
    from lib.yaml_roundtrip import YamlRoundTripLoss
    data = mgr.read("project"); data["c"] = 3
    with pytest.raises(YamlRoundTripLoss):
        mgr.write("project", data)
    mgr.write("project", data, allow_lossy=True)
    assert yaml.safe_load((root / ".meta-config" / "project.yaml").read_text(encoding="utf-8"))["c"] == 3
```
(`lib` ist in `test_admin_server.py` via `sys.path` auf `scripts` erreichbar — Importzeile des Moduls kopf prüfen, ggf. `sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))` ergänzen.)

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_admin_server.py -k "project_write" --basetemp="$PYTEST_BASETEMP"` — erwartet: Kommentare verschwunden (`# top` nicht in out) bzw. `DID NOT RAISE YamlRoundTripLoss`.

- [ ] **Step 3: Implementierung**
In `write()` (nach `new_text = ...`): 
```python
        if key == "project" and path.exists():
            from lib.yaml_patch import patch_top_level
            original = path.read_text(encoding="utf-8")
            patched = patch_top_level(
                original, data,
                lambda d: yaml_dump_preserving_multiline(
                    yaml, d, default_flow_style=False, allow_unicode=True, sort_keys=False))
            if patched is not None:
                new_text = patched
            else:
                from lib.yaml_roundtrip import assert_roundtrip_preserved
                assert_roundtrip_preserved(original, new_text, context=f"config/{path.name}",
                                           allow_lossy=allow_lossy)
```
(`data` ist bei `project` immer ein Mapping; `list` => `patch_top_level` liefert `None`.) `_route_put_config`: im `key == "project"`-Zweig `body = dict(body)` und `allow_lossy = bool(body.pop(ALLOW_LOSSY_KEY, False))` vor `_assert_project_update_writable`, `write("project", merged, allow_lossy=allow_lossy)`. `_write_project_section`: `allow_lossy = bool(body.pop(ALLOW_LOSSY_KEY, False))` auf einer Kopie von `body`, an `write(...)` durchreichen. Doku: Eintrag in `docs/api/` bzw. Admin-Howto (Grep `__allow_lossy__` in `docs/`) um `project` ergänzen.

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_admin_server.py tests/test_yaml_patch.py --basetemp="$PYTEST_BASETEMP"`.

- [ ] **Step 5: Commit**
`git add scripts/admin-server.py tests/test_admin_server.py docs`
`git commit -m "fix: preserve project.yaml comments on admin save" -m "Closes #1092"`

### Task D8: Close-out PR D2

**Agent:** developer -> code-reviewer -> git
**Depends on:** D7
**Files:** Modify `CHANGELOG.md`; AC-01 prüfen (`grep "project.yaml" tests/fixtures/ac01-baseline/hashes.json`; nur bei Treffer `--write` und nur diese Schlüssel committen)
**Interfaces:** Consumes: Close-out-Protokoll. Produces: PR `fix/yaml-comment-preserving-writer` mit `Closes #1074`, `Closes #1092`.

- [ ] Step 1: Rebase auf `main`.
- [ ] Step 2: Scratch-Sync-Lauf zur Verifikation (Close-out Schritt 4 deckt ab); AC-01-Test ohne `--write`, bei Diff nur `project.yaml`-Schlüssel nachziehen.
- [ ] Step 3: CHANGELOG: `Fixed:` #1074/#1092; `behavior change: auto-sync no longer writes the preset/flag defaults (rules-preset, speech-mode, tier-preset, se-focus, max-parallel-agents, debug-mode, allow-committed-secrets) into project.yaml; use --fill-defaults/--init`.
- [ ] Step 4: Volllauf, `code-reviewer`, PR durch `git`.
- [ ] Step 5: Commit `git add CHANGELOG.md tests/fixtures/ac01-baseline/hashes.json` (nur falls geändert) / `git commit -m "docs: changelog entries for comment-preserving writer"`.

## Tasks Cluster E

Branch `fix/provider-mcp-opencode-hermes`. Innerhalb des Branches seriell (E1 -> E2 -> E3 -> E4 -> E5), weil `sync_pipeline.py` (E4) und gemeinsame Test-Läufe sonst kollidieren; E5 ist inhaltlich unabhängig (Welle 1) und kann zuerst gezogen werden. Abweichung zu Verify-C: `_opencode_entry_point` hat drei Aufrufer (`isolation.py:804`, `:1299`, `:1669`), alle in Funktionen mit `config`-Parameter; die Dangling-Warnung gehört in `_sync_opencode_runtime_gate` (`existing` ist dort ab :762 gelesen) und nicht in `_merge_default_agent` (kennt weder `active_set` noch `config`); `active_set.py` importiert `_resolve_orch_mode` bereits aus `.variables` (Z.31), es entsteht kein neuer Import-Zyklus. In `tests/test_hermes_export.py` kodieren bestehende Tests die alten Pfade `roles/alpha/...` (Z.250-259, 307-308) sowie Beschreibungs- und Tier-Warnungs-Verhalten (Z.269-286, 301, 335-343): sie werden in E5 mitgeändert.

### Task E1: #1090 `role_emitted_for_provider` und Entry-Point

**Agent:** developer
**Depends on:** —
**Files:**
- Modify: `scripts/lib/active_set.py` (neue Funktion nach `compute_active_set`, Import-Zeile 31 vorhanden)
- Modify: `scripts/lib/isolation.py` (`_opencode_entry_point` :549-570 plus Aufrufer :804, :1299, :1669)
- Create: `tests/test_opencode_main_chat_entry_point.py`

**Interfaces:**
- Produces: `role_emitted_for_provider(role: str, active_set, config: dict, provider: str) -> bool` — `True` wenn (`active_set is None` oder `role in active_set.roles`) und NICHT (`role == "orchestrator"` und `_resolve_orch_mode(orch_cfg, override, validate=False) == "main-chat"`), mit `orch_cfg = config.get("orchestrator") or {}` und `override = (orch_cfg.get("provider-overrides") or {}).get(provider)` (nur wenn `dict`); `_opencode_entry_point(provider: str, provider_config: dict, active_set, config: Optional[dict] = None) -> Optional[str]` — mit `config` zusätzlich `role_emitted_for_provider`; `config=None` => bisheriges Verhalten.
- Consumes: `providers.explicit_primary_role`, `variables._resolve_orch_mode`.

- [ ] **Step 1: Failing Tests schreiben** (`tests/test_opencode_main_chat_entry_point.py`)
```python
import json, sys
from pathlib import Path
from types import SimpleNamespace
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from lib import isolation
from lib.active_set import role_emitted_for_provider
from lib.log import SyncLog

AS = SimpleNamespace(roles=frozenset({"orchestrator", "developer"}),
                     known_roles=frozenset({"orchestrator", "developer", "tester"}))
PC = {"Opencode": {"primary-role": "orchestrator"}}
MAIN = {"orchestrator": {"mode": "main-chat"}}
STRICT = {"orchestrator": {"mode": "strict"}}

def test_role_emitted_matrix():
    assert role_emitted_for_provider("orchestrator", AS, STRICT, "Opencode") is True
    assert role_emitted_for_provider("orchestrator", AS, MAIN, "Opencode") is False
    assert role_emitted_for_provider("developer", AS, MAIN, "Opencode") is True
    assert role_emitted_for_provider("tester", AS, STRICT, "Opencode") is False
    assert role_emitted_for_provider("orchestrator", None, STRICT, "Opencode") is True

def test_provider_override_only_for_that_provider():
    cfg = {"orchestrator": {"mode": "strict", "provider-overrides": {"Opencode": {"mode": "main-chat"}}}}
    assert role_emitted_for_provider("orchestrator", AS, cfg, "Opencode") is False
    assert role_emitted_for_provider("orchestrator", AS, cfg, "Gemini") is True

def test_legacy_enabled_false_equals_main_chat():
    assert role_emitted_for_provider("orchestrator", AS, {"orchestrator": {"enabled": False}}, "Opencode") is False

def test_entry_point_none_in_main_chat_and_compat_without_config():
    assert isolation._opencode_entry_point("Opencode", PC, AS, MAIN) is None
    assert isolation._opencode_entry_point("Opencode", PC, AS, STRICT) == "orchestrator"
    assert isolation._opencode_entry_point("Opencode", PC, AS) == "orchestrator"

def _run_gate(tmp_path, config, initial="{}\n"):
    (tmp_path / "opencode.json").write_text(initial, encoding="utf-8")
    log = SyncLog()
    isolation._sync_opencode_runtime_gate(tmp_path, config, "Opencode", PC, REPO_ROOT, log, False, AS)
    return json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8")), log

def test_main_chat_writes_no_default_agent_v1(tmp_path):
    doc, _ = _run_gate(tmp_path, MAIN)
    assert "default_agent" not in doc

def test_strict_unchanged_writes_default_agent(tmp_path):
    doc, _ = _run_gate(tmp_path, STRICT)
    assert doc["default_agent"] == "orchestrator"
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_opencode_main_chat_entry_point.py --basetemp="$PYTEST_BASETEMP"` — erwartet: `ImportError: cannot import name 'role_emitted_for_provider'`.

- [ ] **Step 3: Implementierung**
`active_set.py`: Funktion wie in Interfaces (Docstring: "single source for #1077; `agent_sync.py:617` uses the per-provider `ORCH_MODE_MAIN_CHAT` variable derived from the same resolver"). `isolation.py`: `_opencode_entry_point` um den optionalen vierten Parameter erweitern (`from .active_set import role_emitted_for_provider` function-lokal, falls Zyklus: `active_set` importiert `variables`/`roles`, nicht `isolation`); an allen drei Aufrufstellen `config` als 4. Argument übergeben (`:804`: `config`, `:1299`: `config`, `:1669`: `config`). `agent_sync.py:617` bleibt unverändert (Call D16).

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_opencode_main_chat_entry_point.py tests/test_runtime_gate_wiring.py tests/test_opencode_runtime_gate.py --basetemp="$PYTEST_BASETEMP"`.

- [ ] **Step 5: Commit**
`git add scripts/lib/active_set.py scripts/lib/isolation.py tests/test_opencode_main_chat_entry_point.py`
`git commit -m "fix: skip opencode entry point when orchestrator not emitted" -m "Closes #1090"`

### Task E2: #1090 v2-Init ohne dangling Key und Dangling-Warnung

**Agent:** developer
**Depends on:** E1
**Files:**
- Modify: `scripts/lib/context.py` (`apply_settings_surface_shape` :1655-1703, `_init_provider_settings_json` :1706-1759)
- Modify: `scripts/lib/isolation.py` (`_sync_opencode_runtime_gate` nach der `entry`-Zuweisung :801-805)
- Modify: `tests/test_opencode_main_chat_entry_point.py`

**Interfaces:**
- Produces: `apply_settings_surface_shape(content: str, pc: dict, capabilities: Optional[dict] = None, *, emit_default_agent: bool = True) -> str` (Key `default_agent` nur bei `emit_default_agent`); `_init_provider_settings_json` übergibt `emit_default_agent = not (pc.get("primary-role") == "orchestrator" and variables.get("ORCH_MODE_MAIN_CHAT") == "true")`; Warntext (Log-Level `warning`): `opencode.default-agent.dangling: default_agent '<x>' names role '<x>' which this sync does not generate (orchestrator.mode main-chat?) — remove the key or set orchestrator.mode: strict`, ausgelöst wenn `not rollback_only`, `entry is None`, `active_set is not None`, `existing["default_agent"]` ein `str` in `active_set.known_roles` ist und `not role_emitted_for_provider(<x>, active_set, config, provider)`; der Wert bleibt unangetastet.
- Consumes: `role_emitted_for_provider` (E1), per-Provider-Variable `ORCH_MODE_MAIN_CHAT` (`variables._orch_mode_flags`).

- [ ] **Step 1: Failing Tests schreiben** (anhängen an `tests/test_opencode_main_chat_entry_point.py`)
```python
from lib.context import apply_settings_surface_shape

def test_init_shape_omits_default_agent_when_not_emitted():
    pc = {"mcp-config": {"format": "opencode-json-v2"}, "primary-role": "orchestrator"}
    assert "default_agent" not in json.loads(apply_settings_surface_shape("{}\n", pc, emit_default_agent=False))
    assert json.loads(apply_settings_surface_shape("{}\n", pc))["default_agent"] == "orchestrator"

def test_dangling_user_default_agent_warns_not_deleted(tmp_path):
    doc, log = _run_gate(tmp_path, MAIN, initial='{"default_agent": "orchestrator"}\n')
    assert doc["default_agent"] == "orchestrator"
    assert any("opencode.default-agent.dangling" in w for w in log.warnings)

def test_foreign_default_agent_is_not_flagged(tmp_path):
    doc, log = _run_gate(tmp_path, MAIN, initial='{"default_agent": "build"}\n')
    assert doc["default_agent"] == "build" and not log.warnings

def test_managed_default_agent_removed_after_switch_to_main_chat(tmp_path):
    doc, _ = _run_gate(tmp_path, STRICT)
    assert doc["default_agent"] == "orchestrator"
    log = SyncLog()
    isolation._sync_opencode_runtime_gate(tmp_path, MAIN, "Opencode", PC, REPO_ROOT, log, False, AS)
    assert "default_agent" not in json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8"))

import pytest

@pytest.mark.parametrize("cfg", [MAIN, STRICT])
def test_invariant_default_agent_is_emitted_or_absent(tmp_path, cfg):
    doc, _ = _run_gate(tmp_path, cfg)
    value = doc.get("default_agent")
    assert value is None or role_emitted_for_provider(value, AS, cfg, "Opencode")
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_opencode_main_chat_entry_point.py --basetemp="$PYTEST_BASETEMP"` — erwartet: `TypeError: apply_settings_surface_shape() got an unexpected keyword argument 'emit_default_agent'`; Dangling-Test ohne Warnung.

- [ ] **Step 3: Implementierung**
`context.py:1655`: Keyword-only Parameter `emit_default_agent: bool = True`; `:1700-1702` nur bei `emit_default_agent`. `_init_provider_settings_json:1755`: `apply_settings_surface_shape(content, pc, capabilities, emit_default_agent=emit)` mit `emit` wie oben. `isolation.py`: nach dem `entry = (...)`-Block `if (not rollback_only and entry is None and active_set is not None):` `current = existing.get(_DEFAULT_AGENT_JSON_KEY)`; wenn `isinstance(current, str) and current in active_set.known_roles and not role_emitted_for_provider(current, active_set, config, provider)`: `log.warning(...)` mit dem Text aus den Interfaces. CHANGELOG-Hinweis im Close-out: bereits geschriebene v2-Init-Werte werden nicht automatisch entfernt (nur WARN).

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_opencode_main_chat_entry_point.py tests/test_opencode_v2_surface.py tests/test_runtime_gate_wiring.py --basetemp="$PYTEST_BASETEMP"`; Golden `tests/scenarios/configs/69-opencode-v2-surface.project.yaml` unverändert (strict).

- [ ] **Step 5: Commit**
`git add scripts/lib/context.py scripts/lib/isolation.py tests/test_opencode_main_chat_entry_point.py`
`git commit -m "fix: omit dangling opencode default_agent in main-chat" -m "Closes #1090"`

### Task E3: #1080 `python3` im Katalog und Interpreter-Fallback

**Agent:** developer
**Depends on:** E2
**Files:**
- Modify: `config/plugin-catalog.yaml` (:101 und :127 `command: python` -> `command: python3`)
- Modify: `scripts/lib/mcp_provider_config.py` (Import `shutil`; neue Funktion; stdio-Zweig :220-233)
- Modify: `tests/test_mcp_config.py`
- Prüfen: `grep -rn '"command": "python"' tests/fixtures` (bei Treffern Goldens anpassen)

**Interfaces:**
- Produces: `_INTERPRETER_FALLBACKS: dict[str, tuple[str, ...]] = {"python3": ("python", "py")}`; `_resolve_stdio_command(cmd: str) -> str` — `cmd`, wenn `shutil.which(cmd)` aufgelöst, sonst der erste auflösbare Fallback, sonst `cmd`.
- Consumes: `_build_connection_entry(conn, secrets, fmt=None)` (:156).

- [ ] **Step 1: Failing Tests schreiben** (`tests/test_mcp_config.py`; Importe `import scripts.lib.mcp_provider_config as mpc`, `from scripts.lib.registry_query import load_mcp_registry`)
```python
def test_catalog_stdio_commands_use_python3():
    repo_root = Path(__file__).resolve().parents[1]
    for name, server in load_mcp_registry(repo_root).items():
        conn = server.get("connection") or {}
        if conn.get("type") == "stdio":
            assert conn.get("command") != "python", name

def _entry():
    return {"type": "stdio", "command": "python3", "args": ["a.py"]}

def test_stdio_command_falls_back_when_python3_missing(monkeypatch):
    monkeypatch.setattr(mpc.shutil, "which", lambda c: "/x/python" if c == "python" else None)
    assert mpc._build_connection_entry(_entry(), None)["command"] == "python"

def test_stdio_command_unchanged_when_python3_present(monkeypatch):
    monkeypatch.setattr(mpc.shutil, "which", lambda c: "/x/" + c)
    assert mpc._build_connection_entry(_entry(), None)["command"] == "python3"

def test_stdio_command_unchanged_when_nothing_resolves(monkeypatch):
    monkeypatch.setattr(mpc.shutil, "which", lambda c: None)
    assert mpc._build_connection_entry(_entry(), None)["command"] == "python3"
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_mcp_config.py -k "python3 or falls_back or nothing_resolves" --basetemp="$PYTEST_BASETEMP"` — erwartet: Katalog-Test schlägt für `viz-logger` und `a2a-handoff` fehl; `AttributeError: module ... has no attribute 'shutil'`.

- [ ] **Step 3: Implementierung**
Katalog beide Einträge auf `python3`. In `mcp_provider_config.py`: `import shutil`; `_INTERPRETER_FALLBACKS`/`_resolve_stdio_command` oberhalb von `_build_connection_entry`; im stdio-Zweig `cmd = _resolve_stdio_command(conn.get("command", ""))`. Kommentar: `shortcut: host-local resolution at sync time, .mcp.json is gitignored per host; revisit with #814 (invocation/cwd)`.

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_mcp_config.py tests/test_mcp_stale_servers_key.py --basetemp="$PYTEST_BASETEMP"` und `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`.

- [ ] **Step 5: Commit**
`git add config/plugin-catalog.yaml scripts/lib/mcp_provider_config.py tests/test_mcp_config.py`
`git commit -m "fix: use python3 for repo-owned mcp servers with fallback" -m "Closes #1080"`

### Task E4: #1080 `mcp_health` WARN-Checks

**Agent:** developer
**Depends on:** E3
**Files:**
- Create: `scripts/lib/mcp_health.py` (<= 80 Zeilen)
- Modify: `scripts/lib/sync_pipeline.py` (Import neben :98, Aufruf direkt hinter :363)
- Create: `tests/test_mcp_health.py`
- Modify: `config/plugin-catalog.yaml` (agent-hint des `reqogniloom`-Eintrags: ein Satz zu den zwei Variablennamen)

**Interfaces:**
- Produces: `check_mcp_health(agent_meta_root: Path, project_root: Path, config: dict, log: SyncLog, env: Optional[Mapping[str, str]] = None) -> None` — je aktivem Server mit `secrets:` EINE `log.warn(f"mcp.secret-empty: server '{name}': required secret(s) {', '.join(missing)} empty (secrets.local.yaml / environment) — server will not connect")`, wenn ein Secret weder in `secrets.local.yaml` nicht-leer noch in `env` (Default `os.environ`) gesetzt ist; je aktivem stdio-Server mit `shutil.which(_resolve_stdio_command(cmd)) is None` `log.warn(f"mcp.command-unresolved: server '{name}': command '{cmd}' not found on PATH")`. Wirft nie.
- Consumes: `registry_query.load_mcp_registry`, `registry_query.resolve_active_mcp_servers`, `registry_query.SECRETS_LOCAL_FILE`, `io._load_yaml_or_json`, `mcp_provider_config._resolve_stdio_command`.

- [ ] **Step 1: Failing Tests schreiben** (`tests/test_mcp_health.py`)
```python
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
import scripts.lib.mcp_health as mh
from scripts.lib.log import SyncLog

REG = {
    "reqo": {"connection": {"type": "sse", "url": "{{MCP_REQ_URL}}"}, "secrets": ["MCP_REQ_URL", "MCP_REQ_KEY"]},
    "viz": {"connection": {"type": "stdio", "command": "python3"}, "secrets": []},
}

def _patch(monkeypatch, active, which="/bin/x"):
    monkeypatch.setattr(mh, "load_mcp_registry", lambda *a, **k: REG)
    monkeypatch.setattr(mh, "resolve_active_mcp_servers", lambda *a, **k: active)
    monkeypatch.setattr(mh.shutil, "which", lambda c: which)

def _secrets(tmp_path, text):
    p = tmp_path / ".meta-config" / "secrets.local.yaml"
    p.parent.mkdir(parents=True)
    p.write_text(text, encoding="utf-8")

def test_empty_secret_warns_once_per_server(tmp_path, monkeypatch):
    _patch(monkeypatch, ["reqo"]); _secrets(tmp_path, 'MCP_REQ_URL: ""\nMCP_REQ_KEY: ""\n')
    log = SyncLog()
    mh.check_mcp_health(tmp_path, tmp_path, {}, log, env={})
    assert len(log.warnings) == 1
    assert "mcp.secret-empty" in log.warnings[0] and "MCP_REQ_URL" in log.warnings[0] and "MCP_REQ_KEY" in log.warnings[0]

def test_env_var_counts_as_set(tmp_path, monkeypatch):
    _patch(monkeypatch, ["reqo"]); _secrets(tmp_path, 'MCP_REQ_URL: ""\nMCP_REQ_KEY: ""\n')
    log = SyncLog()
    mh.check_mcp_health(tmp_path, tmp_path, {}, log, env={"MCP_REQ_URL": "u", "MCP_REQ_KEY": "k"})
    assert log.warnings == []

def test_filled_secret_no_warn(tmp_path, monkeypatch):
    _patch(monkeypatch, ["reqo"]); _secrets(tmp_path, "MCP_REQ_URL: u\nMCP_REQ_KEY: k\n")
    log = SyncLog()
    mh.check_mcp_health(tmp_path, tmp_path, {}, log, env={})
    assert log.warnings == []

def test_inactive_server_not_checked(tmp_path, monkeypatch):
    _patch(monkeypatch, []); log = SyncLog()
    mh.check_mcp_health(tmp_path, tmp_path, {}, log, env={})
    assert log.warnings == []

def test_unresolved_command_warns(tmp_path, monkeypatch):
    _patch(monkeypatch, ["viz"], which=None); log = SyncLog()
    mh.check_mcp_health(tmp_path, tmp_path, {}, log, env={})
    assert len(log.warnings) == 1 and "mcp.command-unresolved" in log.warnings[0]
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_mcp_health.py --basetemp="$PYTEST_BASETEMP"` — erwartet: `ModuleNotFoundError: No module named 'scripts.lib.mcp_health'`.

- [ ] **Step 3: Implementierung**
Modul wie in Interfaces (stdlib: `os`, `shutil`, `pathlib`; Fehler in Registry-/Secrets-Lesen mit `try/except Exception` fail-soft, Debug-Log). `sync_pipeline.py`: `from lib.mcp_health import check_mcp_health` neben :98 und direkt nach `sync_secrets_template(...)` (:363) `check_mcp_health(agent_meta_root, project_root, config, log)`. Katalog-Hinweis: im `agent-hint` des Reqogniloom-Servers ergänzen "Wenn das externe Plugin UND dieser Katalog-Server aktiv sind, beide Variablen (`REQOGNILOOM_MCP_URL` und `MCP_REQOGNILOOM_URL`) setzen oder eine Quelle deaktivieren." (kein Umbenennen, Call D17).

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_mcp_health.py tests/test_mcp_config.py --basetemp="$PYTEST_BASETEMP"`; `python3 scripts/sync.py --dry-run` zeigt für dieses Repo keine neue `mcp.command-unresolved`-Warnung für `viz-logger` (python3 auflösbar); `wc -l scripts/lib/mcp_health.py` <= 80.

- [ ] **Step 5: Commit**
`git add scripts/lib/mcp_health.py scripts/lib/sync_pipeline.py tests/test_mcp_health.py config/plugin-catalog.yaml`
`git commit -m "fix: warn on empty mcp secrets and unresolved commands" -m "Closes #1080"`

### Task E5: #1094 Hermes-Skillpack (Verzeichnis = Name, Beschreibung, Tier)

**Agent:** developer
**Depends on:** — (Welle 1; im Branch nach E4 einsortiert)
**Files:**
- Modify: `scripts/hermes_export.py` (Kopfdoku :16, `_role_description` :232-249, `collect_role_meta` :252-276, `export_skill_pack` :528-548)
- Modify: `tests/test_hermes_export.py` (bestehende Pfad-/Beschreibungs-/Warnungs-Assertions anpassen, neue Tests)
- Prüfen: `Grep "roles/<role>" docs/` und Hermes-Howto, Pfade anpassen

**Interfaces:**
- Produces: `_SKILL_DIR = "agent-meta-{role}"`; Manifest `skill` = `roles/agent-meta-<role>/SKILL.md`, `persona` = `roles/agent-meta-<role>/references/persona.md`; `_role_description(role, entry, agent_meta_root) -> str` — Priorität: Template-Frontmatter `description` -> role-defaults `description` -> `short_desc` -> Rollenname; `collect_role_meta(...) -> tuple[dict, Optional[str]]` — Rolle ohne Eintrag in `roles_cfg["roles"]` => Tier `balanced` ohne Warnung; Eintrag mit leerem/unbekanntem `model` warnt weiter.
- Consumes: `resolve_abstract_tier`, `parse_frontmatter_text`, `load_roles_config`.

- [ ] **Step 1: Failing/angepasste Tests** (`tests/test_hermes_export.py`, Klasse `TestExportSkillPackMiniRepo`)
Bestehende Assertions ändern: `test_writes_expected_layout` -> Pfade `roles/agent-meta-alpha/SKILL.md`, `roles/agent-meta-alpha/references/persona.md`, `roles/agent-meta-gamma/...`; `(out / "roles" / "agent-meta-alpha" / ...)`; `test_skill_md_frontmatter...`: Pfad `agent-meta-alpha` und `"Alpha test role." in fm["description"]`; `test_manifest_structure`: `entry["description"] == "Alpha test role."`, `entry["skill"] == "roles/agent-meta-alpha/SKILL.md"`, `entry["persona"] == "roles/agent-meta-alpha/references/persona.md"`; `test_orphan_role_defaults_to_balanced_with_warning` -> umbenennen `test_template_only_role_has_no_tier_warning`: `tier == "balanced"` und `not any(w.startswith("gamma:") for w in summary["warnings"])`. Neue Tests:
```python
    def test_skill_dir_equals_frontmatter_name(self, mini_meta: Path, tmp_path: Path) -> None:
        out = tmp_path / "pack"
        summary = hermes_export.export_skill_pack(mini_meta, out)
        manifest = yaml.safe_load(summary["manifest"])
        for role, entry in manifest["roles"].items():
            text = (out / entry["skill"]).read_text(encoding="utf-8")
            fm = yaml.safe_load(text.split("\n---\n", 1)[0].removeprefix("---\n"))
            assert Path(entry["skill"]).parent.name == fm["name"] == f"agent-meta-{role}"

    def test_description_prefers_template_frontmatter(self, mini_meta: Path, tmp_path: Path) -> None:
        summary = hermes_export.export_skill_pack(mini_meta, tmp_path / "pack")
        assert summary["roles"]["alpha"]["description"] == "Alpha test role."

    def test_entry_without_model_still_warns(self, tmp_path: Path) -> None:
        root = _make_mini_meta(tmp_path)
        _write_template(root / "agents" / "1-generic" / "delta.md", "delta", "Delta test role.")
        with (root / "config" / "role-defaults.yaml").open("a", encoding="utf-8") as fh:
            fh.write("  delta:\n    description: Delta.\n")
        summary = hermes_export.export_skill_pack(root, tmp_path / "pack")
        assert any(w.startswith("delta: no abstract tier") for w in summary["warnings"])
```
`test_frontmatter_description_fallback_for_orphan_template` bleibt unverändert grün.

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_hermes_export.py --basetemp="$PYTEST_BASETEMP"` — erwartet: Pfad-Assertions (`roles/alpha/...` vs. neu), Beschreibung `Alpha role description.` statt `Alpha test role.`, Warnung für `gamma` vorhanden.

- [ ] **Step 3: Implementierung**
`_SKILL_DIR`-Konstante; `rel_skill = f"roles/{_SKILL_DIR.format(role=role)}/SKILL.md"` (analog persona und die zwei `output_dir`-Pfade :542-543). `_role_description`: Template-Block vor den role-defaults-Quellen. `collect_role_meta`: `has_entry = role in (roles_cfg.get("roles") or {})`; `tier, warning = resolve_abstract_tier(...)` nur wenn `has_entry`, sonst `(DEFAULT_TIER, None)`. Kopfdoku :16 und Howto-Pfade angleichen. Die 8 deutschen Template-Descriptions bleiben Folge-Issue (kein Template-Edit hier).

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_hermes_export.py --basetemp="$PYTEST_BASETEMP"`.

- [ ] **Step 5: Commit**
`git add scripts/hermes_export.py tests/test_hermes_export.py docs`
`git commit -m "fix: align hermes skill dir, description and tier handling" -m "Closes #1094"`

### Task E6: Close-out PR E

**Agent:** developer -> code-reviewer -> git
**Depends on:** E4, E5
**Files:** Modify `CHANGELOG.md`; kein AC-01-Diff erwartet (`python3 -m pytest tests/test_ac01_render_identity.py --basetemp="$PYTEST_BASETEMP"` ohne `--write`; Goldens für `.mcp.json` per `grep -rn '"command": "python"' tests/fixtures` prüfen)
**Interfaces:** Consumes: Close-out-Protokoll. Produces: PR `fix/provider-mcp-opencode-hermes` mit `Closes #1090`, `Closes #1080`, `Closes #1094`.

- [ ] Step 1: Rebase auf `main`.
- [ ] Step 2: AC-01-Test ohne `--write`; Scenario-Lauf `tests/scenarios/run.sh` für Opencode-Szenarien.
- [ ] Step 3: CHANGELOG: #1090 mit Bestandsprojekt-Hinweis (v2-Init-Werte nur WARN), #1080 (`python3`, neue WARN `mcp.secret-empty`/`mcp.command-unresolved`), #1094 (`behavior change: skill directories are now roles/agent-meta-<role>/`).
- [ ] Step 4: Volllauf, `code-reviewer`, PR durch `git`.
- [ ] Step 5: Commit `git add CHANGELOG.md` / `git commit -m "docs: changelog entries for provider and mcp fixes"`.

## Tasks Cluster F

Branch `fix/git-template-empty-remote-url`. Es gibt keinen Platform-Override von `git.md` (`grep based-on.*git.md agents/2-platform` ohne Treffer), daher kein Pin-Nachzug.

### Task F1: #1093 `GIT_REMOTE_URL_SET` und Klammern nur bei gesetzter URL

**Agent:** developer
**Depends on:** —
**Files:**
- Modify: `agents/1-generic/git.md` (Z.123; Version `2.1.0` -> `2.1.1`)
- Modify: `scripts/lib/config.py` (:1442 Tupel)
- Modify: `scripts/lib/standalone.py` (`_CONDITIONAL_FALSE_FLAGS` :122-149)
- Modify: `scripts/lib/consistency/placeholders.py` (:40, Git-Zeile)
- Modify: `tests/test_git_section_variables.py`
- Modify: `standalone/agents/git.md` (Export, :113)

**Interfaces:**
- Produces: Variable `GIT_REMOTE_URL_SET` (`"true"`/`"false"`), abgeleitet wie `DEVELOPER_SNIPPETS_PATH_SET`; Template-Zeile `**Git platform:** {{GIT_PLATFORM}}{{#if GIT_REMOTE_URL_SET}} ({{GIT_REMOTE_URL}}){{/if}}`; Standalone-Fallback `"GIT_REMOTE_URL_SET": "false"`.
- Consumes: `strip_inactive_conditional_blocks` (`variables.py:431`, erkennt Schlüssel, die literal im Variablen-Dict stehen), `build_variables(cfg, repo_root, repo_root)`.

- [ ] **Step 1: Failing Tests schreiben** (`tests/test_git_section_variables.py`, Helfer `_vars`, `_load`; für den Render-Test `render_standalone_agent` und die Sync-Pipeline nicht nötig: der Templatetext wird direkt substituiert)
```python
from lib.variables import substitute, strip_inactive_conditional_blocks  # noqa: E402
from lib.log import SyncLog  # noqa: E402

_LINE = "**Git platform:** {{GIT_PLATFORM}}{{#if GIT_REMOTE_URL_SET}} ({{GIT_REMOTE_URL}}){{/if}}"

def _render_line(tmp_path, body):
    variables = _vars(tmp_path, body)
    text = strip_inactive_conditional_blocks(_LINE, variables)
    return substitute(text, variables, "git.md", SyncLog())

def test_git_remote_url_set_flag(tmp_path):
    assert _vars(tmp_path, "")["GIT_REMOTE_URL_SET"] == "false"
    assert _vars(tmp_path, "git:\n  remote-url: https://x/y\n")["GIT_REMOTE_URL_SET"] == "true"

def test_git_agent_has_no_empty_parens_without_remote_url(tmp_path):
    assert _render_line(tmp_path, "git:\n  platform: GitLab\n") == "**Git platform:** GitLab"

def test_git_agent_shows_url_when_set(tmp_path):
    out = _render_line(tmp_path, "git:\n  platform: GitHub\n  remote-url: https://github.com/o/r\n")
    assert out == "**Git platform:** GitHub (https://github.com/o/r)"

def test_template_line_is_the_gated_form():
    text = (_REPO_ROOT / "agents" / "1-generic" / "git.md").read_text(encoding="utf-8")
    assert _LINE in text and 'version: "2.1.1"' in text
```
(Signaturen verifiziert: `strip_inactive_conditional_blocks(text, variables)` `variables.py:417`, `substitute(text, variables, source_label, log)` `variables.py:544`.)

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_git_section_variables.py --basetemp="$PYTEST_BASETEMP"` — erwartet: `KeyError: 'GIT_REMOTE_URL_SET'` und `_LINE not in text`.

- [ ] **Step 3: Implementierung**
`config.py:1442`: Tupel um `"GIT_REMOTE_URL"` erweitern (erzeugt `GIT_REMOTE_URL_SET`; `setdefault("GIT_REMOTE_URL", "")` ist harmlos). `git.md:123` auf die gegatete Zeile, Version `2.1.1`. `standalone.py`: `"GIT_REMOTE_URL_SET": "false",` in `_CONDITIONAL_FALSE_FLAGS`. `placeholders.py:40`: `"GIT_REMOTE_URL_SET"` neben `"GIT_REMOTE_URL"` registrieren (NICHT in `_UNREGISTERED_BUILDER_RATCHET`, Ratchet ist shrink-only). Variablen-Doku `docs/guides/setup/first-steps.md` (Grep `GIT_REMOTE_URL`) um die abgeleitete Variable ergänzen. `python scripts/sync.py --render-standalone` für `standalone/agents/git.md`.

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_git_section_variables.py tests/test_standalone_export_in_sync.py tests/test_standalone_render.py --basetemp="$PYTEST_BASETEMP"` und `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`.

- [ ] **Step 5: Commit**
`git add agents/1-generic/git.md scripts/lib/config.py scripts/lib/standalone.py scripts/lib/consistency/placeholders.py tests/test_git_section_variables.py standalone/agents/git.md docs`
`git commit -m "fix: omit empty remote url parens in git agent template" -m "Closes #1093"`

### Task F2: Close-out PR F

**Agent:** developer -> code-reviewer -> git
**Depends on:** F1
**Files:** Modify `CHANGELOG.md`, `tests/fixtures/ac01-baseline/hashes.json`, `tests/test_ac01_render_identity.py` (Log), ggf. `tests/fixtures/slimming-golden/git.md` (nur bei Diff; Golden hat URL gesetzt, Diff nicht erwartet)
**Interfaces:** Consumes: Close-out-Protokoll. Produces: PR `fix/git-template-empty-remote-url` mit `Closes #1093`.

- [ ] Step 1: Rebase auf `main`.
- [ ] Step 2: `python tests/test_ac01_render_identity.py --write`; erlaubt im Diff: nur `<Provider>/…/git.md`-Schlüssel (9 Provider, nur falls die Baseline-Config keine `remote-url` setzt; sonst kein Diff). Log "git.md only (#1093)".
- [ ] Step 3: CHANGELOG (`Fixed:` #1093, Hinweis "template version 2.1.1 propagates to all projects on next sync; only the empty parentheses disappear").
- [ ] Step 4: Volllauf, `code-reviewer`, PR durch `git`.
- [ ] Step 5: Commit `git add CHANGELOG.md tests/fixtures tests/test_ac01_render_identity.py` / `git commit -m "chore: rebaseline git agent renders for remote url fix"`.

## Tasks Cluster G

Branch `fix/test-basetemp-allowlist` (PR G; Tasks G1/G2 sind ohne Abhängigkeit, G3/G4 nach PR E). G0 (Welle 0) steht in Cluster A. Abweichung zu Verify-C: ein Doctor-Befund für den Basetemp-Pfad entfällt — `--doctor` ist registrydatengetrieben (`config/known-issues.yaml` Detektoren, `scripts/lib/doctor.py:227`), ein statischer Pfad-INFO passt nicht ins Detektor-Modell; stattdessen schreibt der Sync die Information als `log.note` in `sync.log`. Der Plan-Status-Nachzug (G1) betrifft `docs/plans/2026-10-11-context-profiles-plan.md` Z.708 (Item 5 "1.24 teilweise").

### Task G1: #971 Verifikationslauf und Tracking

**Agent:** tester (Lauf), documenter (Tracking), git (Issue-Aktionen)
**Depends on:** —
**Files:**
- Modify: `docs/plans/2026-10-11-context-profiles-plan.md` (Z.708: Status 1.24 von "teilweise" auf "erledigt (AC-11/12/19, Verifikation 2026-10-31)")

**Interfaces:**
- Consumes: bestehende Tests `tests/test_provider_matrix_sync.py` (AC-11 `context.dangling-pointer`, AC-12 `context.rule-unreachable`), `tests/test_unread_channels_removed.py` (AC-19), `tests/test_context_budget_checks.py`. Produces: Verifikationsnachweis (Test-IDs), geschlossenes #971, abgehakte #977-Checkbox.

- [ ] **Step 1: Verifikationslauf (Test, der bestehen muss)**
`python3 -m pytest tests/test_provider_matrix_sync.py -k "dangling or unreachable" tests/test_unread_channels_removed.py tests/test_context_budget_checks.py -q --basetemp="$PYTEST_BASETEMP"` — erwartet: alle grün (Matrix 9 Provider x 4 Presets leer, `_PENDING = {}`).
- [ ] **Step 2: Bei ROT:** genau der rote Fall wird zum eigenen Bug (Ergebnis an den Nutzer melden, G1 bleibt offen, #971 NICHT schließen). Bei GRÜN weiter.
- [ ] **Step 3:** `python3 scripts/sync.py --doctor` auf dem Self-Hosting-Repo: kein `context.dangling-pointer`/`context.rule-unreachable`/`context.unread-channel`-Befund.
- [ ] **Step 4:** Plan-Status-Zeile in `docs/plans/2026-10-11-context-profiles-plan.md` nachziehen.
- [ ] **Step 5:** `git`: #971 mit Evidenz (Test-IDs + Doctor-Ergebnis) schließen, #977-Checkbox abhaken. Commit `git add docs/plans/2026-10-11-context-profiles-plan.md` / `git commit -m "docs: mark context-profile phase 1 checks as verified" -m "Closes #971"`.

### Task G2: #1032 Docstring und Pin-Test, Issue mit Evidenz schließen

**Agent:** developer (Docstring/Test), git (Issue)
**Depends on:** —
**Files:**
- Modify: `scripts/lib/hooks.py` (Docstring `_antigravity_adapter_command` :283-292)
- Modify: `tests/test_antigravity_hooks_registration.py`

**Interfaces:**
- Produces: `_antigravity_adapter_command(target_filename: str, hooks_dir_rel: str, config_path_rel: str) -> str` unverändert; zusätzlicher Pin-Test des Vertrags "relativ zum Verzeichnis der hooks.json".
- Consumes: Evidenz `docs/analysis/evidence/2026-09-30-runtime-claude-antigravity.md` §2.1 (cwd = Verzeichnis der `hooks.json`, statisch/in-binary; Runtime-Beleg offen, #860).

- [ ] **Step 1: Failing Test schreiben** (`tests/test_antigravity_hooks_registration.py`, `lib.hooks` ist über `sys.path` importierbar wie `sync_hooks`)
```python
from lib.hooks import _antigravity_adapter_command  # noqa: E402

def test_command_is_relative_to_hooks_json_dir():
    assert _antigravity_adapter_command("x.sh", ".agents/hooks", ".agents/hooks.json") == (
        "bash ./hooks/antigravity-json-adapter.sh x.sh")

def test_command_follows_hooks_json_location():
    assert _antigravity_adapter_command("x.sh", ".agents/hooks", "hooks.json") == (
        "bash ./.agents/hooks/antigravity-json-adapter.sh x.sh")
```
- [ ] **Step 2: Run -> erwartet PASS bereits** (Pin-Test; kein FAIL erwartet, weil kein Code-Fix beschlossen ist — der Test dokumentiert den Vertrag und bricht bei künftiger Änderung bewusst)
`python3 -m pytest tests/test_antigravity_hooks_registration.py::test_command_is_relative_to_hooks_json_dir tests/test_antigravity_hooks_registration.py::test_command_follows_hooks_json_location --basetemp="$PYTEST_BASETEMP"`.
- [ ] **Step 3: Implementierung (nur Docstring)**
Docstring `hooks.py:283-292`: "verified AGY IDE behavior — third-party empirical report" ersetzen durch "AGY runtime documentation (in-binary, static evidence): the command runs via `sh -c` with the working directory set to the directory containing hooks.json — docs/analysis/evidence/2026-09-30-runtime-claude-antigravity.md §2.1; runtime verification pending (#860). If runtime evidence shows a different cwd, use a provider key analogous to `hook-command-anchor` (config/ai-providers.yaml:34) instead of changing this function." Kein Code- und kein Skript-Edit (Hook-Skript-Änderung würde Hook-Version und AC-01-Hashes auslösen).
- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_antigravity_hooks_registration.py --basetemp="$PYTEST_BASETEMP"`.
- [ ] **Step 5: Commit und Issue**
`git add scripts/lib/hooks.py tests/test_antigravity_hooks_registration.py`
`git commit -m "docs: pin antigravity hook command base to hooks.json dir" -m "Closes #1032"`
`git` schließt #1032 mit Verweis auf die Evidenz (`not reproducible with documented cwd`); Label `needs-runtime-evidence` bleibt am Tracking von #860.

### Task G3: #1079 `settings_dirs.sync_allowed_directories`

**Agent:** developer
**Depends on:** E4 (PR E gemergt; `sync_pipeline.py`-Hunk in G4)
**Files:**
- Create: `scripts/lib/settings_dirs.py` (<= 80 Zeilen)
- Create: `tests/test_settings_dirs.py`

**Interfaces:**
- Produces: `sync_allowed_directories(project_root: Path, pc: dict, directories: list, log: SyncLog, dry_run: bool) -> None` — nur wenn `pc` die Keys `settings-allow-dirs-key` (dotted, z. B. `permissions.additionalDirectories`) UND `settings_local_file` trägt und `directories` nicht leer ist: liest die Datei lenient (`io.read_json_lenient`), legt den Pfad im Key an (fehlende Zwischen-Dicts), fügt jeden Eintrag nur hinzu, wenn nicht vorhanden (Listen-Union, nie entfernen, Nutzerkeys unberührt), schreibt per `io.write_atomic`; ungültiges JSON => Datei unberührt + `log.warn`; `dry_run` => nichts schreiben. `outside_project_dirs(project_root: Path, candidates: list) -> list` — Kandidaten, die NICHT unter `project_root` liegen (resolve), als Strings.
- Consumes: `io.read_json_lenient(path) -> Optional[dict]` (:334), `io.write_atomic(path, content)` (:350), `SyncLog.note/warn`.

- [ ] **Step 1: Failing Tests schreiben** (`tests/test_settings_dirs.py`)
```python
import json, sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from lib.log import SyncLog
from lib.settings_dirs import outside_project_dirs, sync_allowed_directories

PC = {"settings_local_file": ".claude/settings.local.json",
      "settings-allow-dirs-key": "permissions.additionalDirectories"}
BASETEMP = "/var/tmp/u/pytest-agent-meta"

def _read(root):
    return json.loads((root / ".claude" / "settings.local.json").read_text(encoding="utf-8"))

def test_adds_directory_to_new_local_settings(tmp_path):
    sync_allowed_directories(tmp_path, PC, [BASETEMP], SyncLog(), False)
    assert _read(tmp_path) == {"permissions": {"additionalDirectories": [BASETEMP]}}

def test_preserves_user_keys_and_existing_entries(tmp_path):
    p = tmp_path / ".claude" / "settings.local.json"
    p.parent.mkdir()
    p.write_text(json.dumps({"x": 1, "permissions": {"allow": ["Bash(ls)"], "additionalDirectories": ["/a"]}}), encoding="utf-8")
    sync_allowed_directories(tmp_path, PC, [BASETEMP], SyncLog(), False)
    assert _read(tmp_path) == {"x": 1, "permissions": {"allow": ["Bash(ls)"], "additionalDirectories": ["/a", BASETEMP]}}

def test_idempotent_second_run_no_change(tmp_path):
    sync_allowed_directories(tmp_path, PC, [BASETEMP], SyncLog(), False)
    first = (tmp_path / ".claude" / "settings.local.json").read_bytes()
    sync_allowed_directories(tmp_path, PC, [BASETEMP], SyncLog(), False)
    assert (tmp_path / ".claude" / "settings.local.json").read_bytes() == first

def test_no_capability_no_write(tmp_path):
    sync_allowed_directories(tmp_path, {"settings_local_file": ".claude/settings.local.json"}, [BASETEMP], SyncLog(), False)
    assert not (tmp_path / ".claude").exists()

def test_empty_directories_no_write(tmp_path):
    sync_allowed_directories(tmp_path, PC, [], SyncLog(), False)
    assert not (tmp_path / ".claude").exists()

def test_dry_run_writes_nothing(tmp_path):
    sync_allowed_directories(tmp_path, PC, [BASETEMP], SyncLog(), True)
    assert not (tmp_path / ".claude").exists()

def test_invalid_json_untouched_with_warn(tmp_path):
    p = tmp_path / ".claude" / "settings.local.json"
    p.parent.mkdir()
    p.write_text("{not json", encoding="utf-8")
    log = SyncLog()
    sync_allowed_directories(tmp_path, PC, [BASETEMP], log, False)
    assert p.read_text(encoding="utf-8") == "{not json" and len(log.warnings) == 1

def test_outside_project_dirs_filters_inside_paths(tmp_path):
    inside = str(tmp_path / ".tmp" / "pytest")
    assert outside_project_dirs(tmp_path, [inside, BASETEMP]) == [BASETEMP]
```

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_settings_dirs.py --basetemp="$PYTEST_BASETEMP"` — erwartet: `ModuleNotFoundError: No module named 'lib.settings_dirs'`.

- [ ] **Step 3: Implementierung**
Modul gemäß Interfaces (`from __future__ import annotations`; `read_json_lenient` liefert `None` bei Fehler und bei fehlender Datei: Existenz vorab per `path.exists()` unterscheiden; bei existierender, unparsebarer Datei `log.warn("settings-dirs: <rel> is not valid JSON — additionalDirectories not updated")` und return). Ausgabe `json.dumps(doc, indent=2, ensure_ascii=False) + "\n"`.

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_settings_dirs.py --basetemp="$PYTEST_BASETEMP"`; `wc -l scripts/lib/settings_dirs.py` <= 80.

- [ ] **Step 5: Commit**
`git add scripts/lib/settings_dirs.py tests/test_settings_dirs.py`
`git commit -m "feat: add additive settings allowed-directories writer" -m "Refs #1079"`

### Task G4: #1079 Provider-Key, Sync-Aufruf und Hinweis

**Agent:** developer
**Depends on:** G3
**Files:**
- Modify: `config/ai-providers.yaml` (Claude-Block, nach `settings_local_file` :70: `settings-allow-dirs-key: permissions.additionalDirectories`)
- Modify: `scripts/lib/sync_pipeline.py` (Import neben :127; Aufruf in der Provider-Schleife direkt nach dem Hooks-Block :1328-1341)
- Modify: `tests/test_settings_dirs.py`
- Modify: Howto-Absatz (Grep `PYTEST_BASETEMP` in `docs/` und `howto/`, ein Absatz "settings.local.json additionalDirectories")

**Interfaces:**
- Produces: im Sync pro Provider mit Key: `dirs = outside_project_dirs(project_root, [resolve_tmp_paths(project_root, config).pytest_basetemp])` (`TmpSinkError` => `[]`), danach `sync_allowed_directories(project_root, pc, dirs, log, args.dry_run)` und `log.note("settings-dirs", f"pytest basetemp {dir} allowed via {pc['settings_local_file']}")` je Eintrag.
- Consumes: `tmp_paths.resolve_tmp_paths(project_root, config) -> TmpPaths` (`.pytest_basetemp: str`), `repo_containment.TmpSinkError`.

- [ ] **Step 1: Failing Tests schreiben** (`tests/test_settings_dirs.py`)
```python
import yaml

def test_claude_declares_allow_dirs_key_and_others_do_not():
    data = yaml.safe_load((REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))
    assert data["providers"]["Claude"]["settings-allow-dirs-key"] == "permissions.additionalDirectories"
    assert data["providers"]["Claude"]["settings_local_file"] == ".claude/settings.local.json"

def test_basetemp_dirs_for_project_uses_resolved_system_temp(tmp_path):
    from lib.settings_dirs import basetemp_dirs
    cfg = {}   # framework default: system-temp exception active
    out = basetemp_dirs(tmp_path, cfg)
    assert len(out) == 1 and not out[0].startswith(str(tmp_path))

def test_basetemp_dirs_empty_when_sink_used(tmp_path):
    from lib.settings_dirs import basetemp_dirs
    cfg = {"repo_containment": {"tmp-sink": {"system-temp-exception": {"enabled": False, "pytest-basetemp": False}}}}
    assert basetemp_dirs(tmp_path, cfg) == []
```
Zusätzlich in `lib/settings_dirs.py`: `basetemp_dirs(project_root: Path, config: dict) -> list` = `outside_project_dirs(project_root, [resolve_tmp_paths(project_root, config).pytest_basetemp])`, `TmpSinkError` => `[]`.

- [ ] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_settings_dirs.py -k "allow_dirs_key or basetemp_dirs" --basetemp="$PYTEST_BASETEMP"` — erwartet: `KeyError: 'settings-allow-dirs-key'` und `ImportError: cannot import name 'basetemp_dirs'`.

- [ ] **Step 3: Implementierung**
Key in `ai-providers.yaml` (Kommentar: "Claude only; format of other providers' allow-dir keys unverified — add when documented"). `basetemp_dirs` in `settings_dirs.py` (lokaler Import von `lib.tmp_paths`/`lib.repo_containment` gegen Zyklen). In `sync_pipeline.py` nach dem Hooks-Block: `if pc.get("settings-allow-dirs-key"):` `dirs = basetemp_dirs(project_root, config)`; `sync_allowed_directories(...)`; `log.note(...)`. Kein Code in `if provider == ...`. Howto-Absatz: Effekt auf den Claude-Code-Dialog ist laut Issue ungeprüft ("not verified") und wird im PR als Annahme benannt.

- [ ] **Step 4: Run -> PASS**
`python3 -m pytest tests/test_settings_dirs.py tests/test_tmp_paths*.py --basetemp="$PYTEST_BASETEMP"` und `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`; danach `git status`: `.claude/settings.local.json` ist gitignored und wird NICHT committet.

- [ ] **Step 5: Commit**
`git add config/ai-providers.yaml scripts/lib/sync_pipeline.py scripts/lib/settings_dirs.py tests/test_settings_dirs.py docs howto`
`git commit -m "fix: allow pytest basetemp dir in local claude settings" -m "Closes #1079"`

### Task G5: Close-out PR G

**Agent:** developer -> code-reviewer -> git
**Depends on:** G2, G4 (G1 unabhängig)
**Files:** Modify `CHANGELOG.md`; AC-01-Check: `grep settings.local tests/fixtures/ac01-baseline/hashes.json` — nur bei Treffer `--write` (nur diese Schlüssel)
**Interfaces:** Consumes: Close-out-Protokoll. Produces: PR `fix/test-basetemp-allowlist` mit `Closes #1079`, `Closes #1032`, `Closes #971`.

- [ ] Step 1: Rebase auf `main`.
- [ ] Step 2: AC-01-Test ohne `--write` (`python3 -m pytest tests/test_ac01_render_identity.py --basetemp="$PYTEST_BASETEMP"`), bei Diff nur `settings.local`-Schlüssel nachziehen.
- [ ] Step 3: CHANGELOG: #1079 (Option C, Pfad in gitignored `settings.local.json`, Wirkung auf den Claude-Code-Dialog ungeprüft), #1032 (kein Code-Fix, Evidenz), #971 (Verifikation).
- [ ] Step 4: Volllauf, `code-reviewer`, PR durch `git`.
- [ ] Step 5: Commit `git add CHANGELOG.md` / `git commit -m "docs: changelog entries for basetemp allow-list and pins"`.

## Spec Coverage

## Spec Coverage

Es gibt keine Spec; die Abdeckung läuft Issue -> Task -> PR -> Welle. Alle 21 Bug-Issues (20 `bug`-Label-Zeilen + #1074) sowie das Duplikat #1042.

| Issue | Thema | Task(s) | PR (Cluster) | Welle |
|---|---|---|---|---|
| #1042 | Duplikat von #1041 | G0 | — (Issue-Aktion) | 0 |
| #1078 | ToolSearch fail-closed | A1 | A `fix/hooks-guards` | 1 |
| #1050 | Fork-Bomb-Scan Nesting | A2 | A | 1 |
| #1041 | `push.recurseSubmodules` via Config | A3 | A | 1 |
| #1072 | Shadowing-FP managed Block | C1 | C1 `fix/gitignore-managed-block` | 1 |
| #1073 | `platform-defaults.resolved.yaml` ignorieren | C2 | C1 | 1 |
| #1095 | Admin 403 bei Symlink-`.agent-meta` | D1 | D1 `fix/admin-symlink-and-validate` | 1 |
| #1093 | `git.md` leere Klammern | F1 | F `fix/git-template-empty-remote-url` | 1 |
| #1094 | Hermes Skillpack | E5 | E `fix/provider-mcp-opencode-hermes` | 1 |
| #971 | context Phase-1-Checks (Verifikation) | G1 | G `fix/test-basetemp-allowlist` | 1 |
| #1032 | AGY `hooks.json` cwd (Docstring/Pin, kein Code-Fix) | G2 | G | 1 |
| #1071 | dangling-dispatch FP (P1) | B1 | B `fix/consistency-false-positives` | 2 |
| #1083 | Frontmatter-Mention WARNING | B2 | B | 2 |
| #1082 | unresolved-placeholder escaped Beispiele | B3 | B | 2 |
| #1091 | schema-invalide `auto_commit` rc=0 | D2, D3 | D1 | 2 |
| #1090 | dangling `default_agent` (P1) | E1, E2 | E | 2 |
| #1080 | MCP `python`, Secrets, Health | E3, E4 | E | 2 |
| #1079 | pytest basetemp außerhalb Projekt | G3, G4 | G | 2 |
| #1081 | generated-file-drift FP + Backup-Müll | C4, C5 | C2 `fix/drift-false-positives` | 3 |
| #1084 | external-tools-drift (5 Teilprobleme) | C6, C7, C8 | C2 | 3 |
| #1074 | `fill_defaults` strippt Kommentare | D5, D6 | D2 `fix/yaml-comment-preserving-writer` | 3 |
| #1092 | Admin-UI Save strippt Kommentare | D5, D7 | D2 | 3 |

Close-out-Tasks je PR: A4, B4, C3 (PR C1), C9 (PR C2), D4 (PR D1), D8 (PR D2), E6, F2, G5.

## Nicht im Batch / Folge-Issues

| # | Folge-Issue (nicht im Batch) | Herkunft |
|---|---|---|
| 1 | `NotebookEdit` ist in `hook_known_tool_name` bekannt, wird von keinem Guard als Schreibtool abgefangen (`case Write|Edit|Bash`) — Containment-Lücke; gleiches gilt für `CronCreate`, `RemoteTrigger`, `PushNotification` | Verify-A #1078 |
| 2 | #1051: Submodul-Push-Ziele prüfen (Feature, baut auf A3 auf) | Inventar |
| 3 | #1085: (a) aktive Tools aktivieren ihre `hooks:` automatisch (Verhaltensänderung Bestandsprojekte), (b) `--strict`/`--fail-on-p0`, (c) Warntext um `ignore-provider-dirs` | Verify-A |
| 4 | #1086: (a)-(d) Sync-Kosmetik (MCP-Label, Hook-Text, Skip-Zähler, Doppel-Warnungen) eigener PR; (e)-(i) Entscheidungen (Soft-Cap-Hinweis, `CLAUDE.personal.md`-WARN->INFO, Tier `max` bleibt = won't fix, Routing-Priority = Design, `context.py` 3336 Zeilen = Refactoring-Epic) | Verify-B |
| 5 | 8 deutsche Template-`description`s (e2e-*, knowledge-*, …) auf Englisch (8 Template-Edits + Bumps + Rebaseline) | Verify-C #1094 |
| 6 | Hermes-Dry-Run meldet unaufgelöste Standalone-Platzhalter (`PARSE_INPUT_BLOCK`, `PROMPT_INJECTION_DEFENSE_BLOCK`, `OUTPUT_GUARD_BLOCK`) für `code-reviewer`/`provider-expert` — Issue behauptet 0 | Verify-C #1094 |
| 7 | Dieses Repo: `git rm --cached .meta-config/platform-defaults.resolved.yaml` (Housekeeping nach PR C1) | Verify-B #1073 |
| 8 | Admin-UI: `__allow_lossy__`-Bestätigungsdialog für `ai-providers` und `project` (heute nur API) | D7 |
| 9 | Provider-Toolliste maschinenlesbar in `config/ai-providers.yaml` und Parity-Test (#1055-Muster) | Verify-A #1078 |
| 10 | #1041 Restlücke: Config eines Fremd-Repos (`-C`/`GIT_DIR`) ist nicht lesbar | A3 |
| 11 | #1032 Runtime-Evidenz (agy SIGILL, #860); bei Abweichung Provider-Key `hook-command-anchor` | G2 |
| 12 | #1077 Topologie: `role_emitted_for_provider` ist die einzige zu erweiternde Stelle | E1 |
| 13 | Reqogniloom-Doppelregistrierung (Plugin + Katalog-Server) erkennen; `mcp-*`-Skills an Health koppeln | Verify-C #1080 |
| 14 | Bestehende v2-`default_agent`-Werte (Init-Pfad) bei Bestandsprojekten aufräumen (heute nur WARN) | E2 |
| 15 | Zerlegen der Alt-Module über 600 Zeilen (`sync_pipeline.py` 1770, `config.py` 2466, `context.py` 3336, `isolation.py` 1873, `generated_file_drift.py` 740) | Konvention |
| 16 | tmp-sink-Spec-Review (RVW-01..08), `docs/reviews/2026-10-07-system-review.md` Status-Abgleich | Inventar |
| 17 | `dispatch_allow`-Hardening für #1071, falls nach B1 Reste bleiben | Verify-A |

## Risiken

| Risiko | Wirkung | Gegenmaßnahme im Plan |
|---|---|---|
| Security-Hooks (A1-A3): jede Änderung an `hook_common.sh`/`dod-push-check.sh` propagiert in alle Projekte; Tool-Namen aus dem Auftrag, nicht aus einer autoritativen Quelle (`SendUserFile`, `Artifact*`, `RemoteTrigger` Schreibweise) | zu enge Liste blockt weiter fail-closed (kein Sicherheitsverlust), zu weite Liste lässt unbekannte Tools durch | Parametrisierter Accept-Test ist einzige Pflegestelle; Worktree-Tools bleiben geblockt; Namen vor Merge gegen reale Hook-Payloads/Audit-Log prüfen |
| #1050 Nesting: ungequotete `{` ohne Gegenstück in langem Body => Fehlalarm | Blockiert harmlose Inline-Funktionen | R1-Test, Fail-closed-Richtung bleibt, Rule dokumentiert die Fehlalarm-Klasse |
| Template-Propagation (B1/B2/F1): Version-Bumps und Rebaseline betreffen alle Projekte und 9 Provider; `hacs-tester` pinnt `tester.md@2.8.0` | Stale-Override-Warnung, AC-01-/Standalone-Gate rot | `hacs-tester`-Pin in B2, Rebaseline-Task je PR nach Rebase, `--render-standalone` im Close-out, nur erlaubte Schlüssel committen |
| Schema-/Exit-Code-Policy (D2/D3): `--validate` liefert rc=1 für bisher akzeptierte, aber dokumentiert ungültige `auto_commit`-Blöcke | CI bestehender Consumer wird rot | Sync bleibt rc=0 mit Fail-safe `off`; CHANGELOG `behavior change`; kein Zeit-Grace (Beta) |
| Sync-Verhaltensänderung (D6): Auto-Sync schreibt die 7 Preset-/Flag-Defaults nicht mehr in `project.yaml` | Tools, die rohe Keys erwarten, sehen sie nicht | Laufzeit-Fallbacks existieren; Tests `test_version_bookkeeping`, `test_config_variable_fallbacks`, `test_meta_optimizer_*`; Scratch-Sync im Close-out |
| Prune-Policy (C5): nur 3 Backups je Quelle, Alter irrelevant | Ältere Sicherheitskopien verschwinden schneller | Neuestes Backup bleibt immer; Test `test_prune_single_old_backup_survives` |
| OpenCode-Config für Bestandsprojekte (E1/E2): Projekte mit bereits geschriebenem v2-`default_agent` im main-chat-Modus | Dangling Key bleibt bis zur manuellen Entfernung | Nur WARN `opencode.default-agent.dangling` (Nutzerwert gewinnt), CHANGELOG-Hinweis; v1/managed heilt sich per Rollback |
| Pfad-Containment (D1, G3/G4): Symlink-Auflösung im Admin-Server; `additionalDirectories` erweitert die Claude-Code-Zugriffsgrenze | Aufgeweichtes Containment bzw. zu weite Erlaubnis | Ausnahme nur im Fallback-Zweig und nur unter `<.agent-meta>/config`; Schreiben über Symlink verboten; `additionalDirectories` nur der aufgelöste Basetemp, nur additiv, nur in gitignorter `settings.local.json`; Wirkung auf den Claude-Dialog ungeprüft (Issue: "not verified") |
| `.mcp.json` host-lokale Auflösung (E3): `python3` -> `python` Fallback ist host-spezifisch | Falsches Kommando auf anderem Host, falls Datei geteilt wird | `.mcp.json` ist gitignored (`gitignore_entries`); Kommentar `shortcut:` im Code; Abstimmung mit #814 |
| `bun.lock` in `infra_known_names` (C7) nicht gegen die Opencode-Doku verifiziert | Zu viel entschuldigt (harmlos) | Test pinnt nur die vier belegten Namen |
| Physische Parallelität: ein Arbeitsbaum, Branch-Wechsel nur bei freiem Baum; Wellen sind Reihenfolge-Vorschlag, nicht Parallelbetrieb mehrerer Branches | Verlorene/vermischte Änderungen | Global Constraint zum geteilten Baum; pro Branch seriell; vorhandene `.meta-config`-Hash-Änderungen vor Wechsel durch `git` klären |
| `sync_pipeline.py` wird von #1080, #1079, #1091, #1081, #1074 berührt | Rebase-Konflikte | Merge-Reihenfolge A, B, E, C1, F, D1, G, C2, D2; Rebase + Close-out Schritt 2 vor jedem Merge |
| #1081-FP nur über konstruierten Zustand reproduzierbar | Fix ohne echten Repro | Unit-Tests auf `resolve_drift_findings` mit exakten pre/post-Zuständen |

## Self-Review

Gegen die Vorgaben geprüft (Skill `writing-plans`) und direkt behoben:

- **Coverage aller 21 Issues:** Tabelle "Spec Coverage" listet alle 21 (+ #1042) mit Task/PR/Welle; jeder Task hat Tests und Commit mit `Closes #<n>`. Befund: Inventar zählt 21 distinkte, die Bug-Tabelle liefert nur 20 `bug`-Zeilen; #1074 ist als 21. Fix aufgenommen (Entscheidung D1). Befund behoben: Cluster-Dateiliste um `standalone/`-Export (B4, F1) ergänzt, weil `tests/test_standalone_export_in_sync.py` sonst rot wird (stand in keinem Verify-Report).
- **Step-Scan (keine Platzhalter):** Der einzige Test mit offener Bedingung im Entwurf (E2: Pseudotest mit `if False`) wurde entfernt; die Formulierung "Signaturen bestätigen" in F1 wurde durch die verifizierten Zeilen ersetzt (`variables.py:417`, `:544`); C8-Test nutzt `log.infos`/`log.warnings` (verifiziert in `scripts/lib/log.py:14-18`). Verbleibende bewusste Anweisungen "Test ist das Orakel" betreffen B1 (Template-Zeilen, deren genaue Lage im Render nur der Matrix-Test festlegt).
- **Typ-/Namenskonsistenz:** `resolve_drift_findings` (C4) / `backup_drifted_files` (C4) / `prune_sync_backups` (C5) Signaturen identisch zu den Bestandsdefinitionen; `role_emitted_for_provider(role, active_set, config, provider)` einheitlich in E1/E2; `auto_commit_violations(config)` in D2/D3; `patch_top_level(original_text, new_doc, dump_fn, comments=None)` in D5/D6/D7; `FRAMEWORK_GENERATED_ENTRIES`/`framework_baseline_entries` in C2; `sync_allowed_directories`, `outside_project_dirs`, `basetemp_dirs` in G3/G4; Provider-Key `settings-allow-dirs-key` einheitlich (G4 + Test); PR-Namen und Branches identisch in Batch-Strategie, Coverage und Close-out-Tasks.
- **Review Focus je mit Test:** R1 `test_fork_bomb_nesting_keeps_fail_closed_and_linear` (A2), R2 `test_1041_cli_flag_overrides_config_and_inert_values` (A3), R3 `test_real_edit_backed_up_from_pre_text`/`test_dry_run_writes_nothing` (C4), R4 `test_sync_rc0_but_allowlist_fail_safe` (D3) + `test_valid_config_unchanged` (D2), R5 `test_symlink_target_outside_config_still_blocked`/`test_write_via_symlink_blocked` (D1). Befund behoben: R4 verwies ursprünglich beide Tests auf D3; `test_valid_config_unchanged` liegt in D2 und ist korrigiert.
- **Proportion:** 39 Tasks / 9 PRs für 21 Bugs: Bündelung nur bei gleicher Datei oder gleichem Defekt (#1072+#1073, #1074+#1092, #1081, #1084 in Teilschritten). Reine Verifikations-/Doku-Fälle (#971, #1032) sind je ein Task ohne Produktionscode. Bewusst kleiner gehalten: kein Doctor-Befund für #1079, kein Template-Edit der 8 deutschen Descriptions, keine Konsistenz-Check-Quelle für Tool-Namen.
- **Offene Verifikationslücken (nicht per Plan lösbar):** Wirkung von `additionalDirectories` auf den Claude-Code-Dialog (#1079), AGY-Runtime-cwd (#1032), exakte Template-Zeilen im Render (#1071) — jeweils im Task bzw. in den Risiken benannt.
