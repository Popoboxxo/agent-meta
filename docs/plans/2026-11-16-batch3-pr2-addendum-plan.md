---
pipeline_stages:
  implement: 1
status: DRAFT
date: 2026-11-16
base-commit: b0e4638f
branches:
  - fix/batch3-pr2-guard-sync
trace:
  - bugfix-batch-3
---

# Batch 3 PR 2 (Guard/Sync) — Addendum Implementation Plan

> Status: DRAFT (2026-11-16). Dieser Plan implementiert nichts, committet nichts, ändert keine Issues. Freigabe (`Status: APPROVED`) nur durch den Nutzer.
> Basis: `origin/main b0e4638f` (PR 1 gemergt). Zeilenanker gelten für diesen Stand und veralten.
> Merge: ausschließlich der Nutzer. Keine Closing-Keywords, nur `Refs #N`.

**Spec:** docs/plans/2026-11-14-bugfix-batch-3-plan.md
Parent-Plan (PR-2-Abschnitt); dieser Nachtrag korrigiert dessen PR-2-Tasks und ergänzt #1241/#1266. Kein eigenes Spec-Artefakt (Bugfix-Klasse). Grundlage: Scope-Analyse `.tmp/audit/batch3-pr2-scope.md`.
**Goal:** Sieben Issues (#1258, #1252, #1142 P3, #1270, #1249 Teil, #1241, #1266) in einem PR beheben; Parent-Plan-Fehler (#1142, #1252, AC-01-Rebaseline) korrigieren.
**Architecture:** Keine Architekturänderung, kein Schema-/Config-Contract-Change, kein neues Modul. Lokale Ursachenbehebung; Provider-Unterschiede nur über Config/Capability-Flags.
**Tech Stack:** Python 3.9 (stdlib + PyYAML), Bash-Hook mit Python-Heredoc, pytest, YAML/JSON.

## Klassifikation

PR gesamt **M** (7 Issues, ~12 Code/Doku-Dateien, ~10 Testdateien, AC-01-Rebaseline); je Task S bzw. S+ (#1142, #1270). Wegen M braucht die Umsetzung diesen Plan mit `Status: APPROVED`.

## Korrekturen gegenüber dem Parent-Plan

- #1142: `log.warning`→`log.error` behebt den Befund nicht (Summary stammt aus `scripts/lib/consistency/report.py:114`). Korrekt: `Finding(ERROR)` in `_strict_findings`.
- #1252: »Fallback unerreichbar« ist falsch; `hook_protocol is None` ist Normalpfad (Unit-Tests, #630-Cleanup).
- AC-01: »kein Rebaseline« ist falsch; Guard-Änderung bewegt Baseline, AC-T4-Digest und 2 Hash-Einträge (nicht 16).
- #1249: Verweis `isolation.py:828-831` falsch; relevant ist `reconcile_opencode_surface_gate` (`isolation.py:2066-2083`).
- #1241 und #1266 fehlten im Parent-Plan.

## Global Constraints

- Python 3.9, nur stdlib + PyYAML, kein `print()` in `lib/`, `SyncLog` verwenden, Module ≤ 600 Zeilen.
- Hook-Datei: `# version:`/`# changelog:` (Zeile 2-3) bumpen.
- Commits: Conventional Commits, Englisch, ≤ 72 Zeichen, Imperativ, nur `Refs #N`. Trailer im Brief an `git`-Agent wortgleich: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Alle Sync-/Validate-/ac01-Läufe mit `--config <worktree>/.meta-config/project.yaml`; nach jedem Lauf `git status --short` prüfen (Ausgabe-Drift sofort sichtbar).
- Pro Task: roter Test → Implementierung → grün → Commit. Genau ein Rebaseline-Commit am Ende (Task 9).
- CI-only: volle Szenario-Suiten (nicht lokal erzwingen); lokal nur betroffene Testdateien.

## File Structure

- Modify: `hooks/1-generic/orchestrator-guard-impl.sh` (`:2-3`, `:1035-1038`) (#1258)
- Modify: `tests/test_orchestrator_guard_hook.py` (`:342-366`, Temp-Entkopplung) (#1258, Task 8)
- Modify: `scripts/lib/hooks.py` (`:682-684`, Kommentar `:430-438`) (#1252)
- Modify: `tests/test_provider_hooks_config.py`; Gegenprobe `tests/test_newline_normalization.py:455` (#1252)
- Modify: `scripts/lib/cli_commands.py` (`:1469/1480/1490/1498`, `_strict_findings` `:1514-1546`) (#1142)
- Modify: `tests/test_auto_commit_invalid_sync.py:58`, `tests/test_commit_trailers.py:137,151` (#1142)
- Modify: `scripts/lib/sync_pipeline.py` (`_managed_dirs_for_prune` `:983-1031`, Kommentar `:966-968`) (#1270)
- Modify: `scripts/lib/generated_file_drift.py` (`select_prunable_sync_backups` `:151-233`, `prune_sync_backups` `:236-275`) (#1270)
- Modify: `scripts/sync.py` (`:650`) (#1270)
- Modify: `tests/test_sync_backup_retention.py`, `tests/test_generated_file_drift.py:712-750`, `tests/test_cleanup_preview_cli.py:200-230` (#1270, Task 8)
- Modify: `docs/providers/opencode.md` (`:63`, `:361`) (#1249)
- Modify: `scripts/lib/agent_sync.py` (`:433-437`); Create/Modify Test in `tests/test_agent_sync_composition*.py` (#1241)
- Modify: `config/plugin-catalog.yaml` (`:106-131`), `README.md:361`, `docs/CODEBASE_OVERVIEW.md:1085,1661`, `tests/test_plugin_catalog_migration_invariant.py:32-60`; Create `tests/test_plugin_catalog_lint.py` (#1266)
- Modify: `CHANGELOG.md` (`### Fixed`)
- Rebaseline: `tests/fixtures/ac01-baseline/hashes.json:108,:530`, `tests/test_opencode_v2_surface.py:5512` (+Log-Kommentare `:5440-5500`), `.meta-config/generated-file-hashes.json:91,:227`

Ownership: ein Entwickler-Agent, strikt sequentiell Task 1 → 9; Tester-Rolle nur für Review der neuen Tests; kein paralleler Schreibzugriff auf `generated-file-hashes.json`/`hashes.json`.

### Task 1: #1142 P3 Config-Audit-Fehler als Finding(ERROR) (S+)

- Red: `tests/test_auto_commit_invalid_sync.py:53-58` Assert erweitern auf `"config-audit.auto_commit"` und `"1 error(s)"`; läuft rot gegen aktuelles `[WARN] 3 warning(s)`. Repro: `python3 -m pytest tests/test_auto_commit_invalid_sync.py::test_validate_reports_error_summary -p no:cacheprovider --basetemp=<worktree>/.tmp/pytest-pr2`.
- Green: `cli_commands.py:1469` (context-profile.invalid), `:1480` (unpaired-closing-tag), `:1490` (auto_commit), `:1498` (commit, E-19) als `Finding(Severity.ERROR, check="config-audit.<kind>", file=<config rel>, message=…)` sammeln und an `_strict_findings` anhängen (nach `:1515`) statt `log.error`/`log.warning`. `[WARN] commit:` (`:1500-1501`) bleibt `log.warning`. `consistency_errors` darf bleiben.
- Betroffene Asserts: `test_auto_commit_invalid_sync.py:58`, `test_commit_trailers.py:137,151` (neues Format `config-audit.commit`); `test_context_profile_schema.py:184-208` (Substring `context-profile.invalid`) bleibt grün.
- Ausgabeänderung: Summary `[FAIL] 1 error(s), 3 warning(s)`, Exit 1 über `_strict_exit_code`; CI-Grepper auf `config-audit [ERROR]` brechen → CHANGELOG nennen.
- Commit: `fix: report config-audit errors as findings in --validate`

### Task 2: #1252 unbekanntes hook_protocol warnt, None bleibt Legacy (S)

- Red: `tests/test_provider_hooks_config.py`: (a) `set(hooks._HOOK_REGISTRATION_WRITERS) == providers.SUPPORTED_HOOK_PROTOCOLS`; (b) `monkeypatch.setattr(providers, "SUPPORTED_HOOK_PROTOCOLS", {..., "fake-proto"})` + `sync_hooks(..., provider="Fake", provider_config={"Fake": {"has_hooks": True, "hook_protocol": "fake-proto", "hooks_dir": ".fake/hooks", "settings_file": ".fake/settings.json"}})` → `.fake/settings.json` fehlt, Warnung `unknown hook_protocol 'fake-proto'`. Repro: `python3 -m pytest tests/test_provider_hooks_config.py -k "fake_proto or parity" -p no:cacheprovider --basetemp=<worktree>/.tmp/pytest-pr2`.
- Green: `hooks.py:682-684`: `proto = pc.get("hook_protocol")`; `writer = _HOOK_REGISTRATION_WRITERS.get(proto)`; `if writer is None and proto: log.warning(...); return`; `if writer is None: writer = _update_settings_hooks` (Legacy für `proto is None`). Kommentar `:430-438` anpassen. `proto is None` NICHT abweisen (bricht #630-Cleanup und `provider_config=None`-Aufrufer). `consistency/hook_drift.py:213-225` unverändert.
- Gegenprobe grün: `tests/test_newline_normalization.py:455` (`test_hook_managed_index_rewritten_empty_after_revocation`).
- Commit: `fix: warn on unknown hook_protocol instead of claude writer fallback`

### Task 3: #1258 read-only `git branch`-Flags (S)

- Red: `tests/test_orchestrator_guard_hook.py` `MUTATION_CASES` (`:342-366`): `git branch -a --contains abc123`, `--merged main`, `--list 'feat/*'`, `--points-at HEAD`, `--contains=abc`, Issue-Kette mit Schleife → False; `git branch -a -D old`, `git branch new-branch` → True. Pytest-freie Repro: Hook direkt mit Payload `git branch -a --contains abc123`, cwd außerhalb Repo → heute rc=2.
- Green: `orchestrator-guard-impl.sh:1035-1038` `is_mutation('branch')`: `if set(args) & mutating_flags: return True`; `if {a.split('=',1)[0] for a in args} & LIST_FLAGS: return False` mit `LIST_FLAGS = {'--list','-l','--contains','--no-contains','--merged','--no-merged','--points-at','-a','--all','-r','--remotes','--show-current'}`; sonst `bool(positional)`. `-v/--format/--sort/--color/--column` NICHT aufnehmen (fail-closed). Modifizierende Flags bleiben blockiert.
- Hook-Version `:2-3`: 1.11.0 → 1.12.0, Changelog »1.12.0: issue #1258 …«.
- Commit: `fix: allow read-only git branch list flags in orchestrator guard`

### Task 4: #1270 Root in Prune + 30-Tage-Regel (S+, E-09)

- Red: `tests/test_sync_backup_retention.py`: (a) `_managed_dirs_for_prune` enthält `project_root`; (b) einzelnes Backup 31 d alt → selektiert, 29 d → nicht (`max_age_days=30`). `tests/test_generated_file_drift.py::test_prune_single_old_backup_survives` (`:735-750`) **invertieren** (bewusste Verhaltensänderung E-09). Repro: `python3 -m pytest tests/test_sync_backup_retention.py tests/test_generated_file_drift.py -k "prune or managed_dirs" -p no:cacheprovider --basetemp=<worktree>/.tmp/pytest-pr2`.
- Green: `sync_pipeline.py:983-1031` `_managed_dirs_for_prune`: `project_root` einmal vorn (nur direkte Kinder, `_is_sync_backup_name` filtert). `generated_file_drift.py` `select_prunable_sync_backups`: Param `max_age_days: Optional[int] = None`; Regel `newer >= keep OR stamp < cutoff` (`cutoff = datetime.now() - timedelta(days=max_age_days)`, Modul-`datetime`, damit `_Clock`-Monkeypatches greifen); Docstrings `:159-176`, `:247-261` korrigieren. `prune_sync_backups` (`:268`) reicht `max_age_days` durch, Signatur unverändert (Spies `test_managed_index_alignment.py:137,171`). `scripts/sync.py:650` `max_age_days=max_age_days` an Selektion (Preview-Parität). Kommentar `sync_pipeline.py:966-968` aktualisieren. `.bak` wird NICHT geprunt.
- Zeitbomben (Teil von Task 8): feste Stempel entfernen/parametrisieren (siehe dort).
- Commit: `fix: prune stale sync backups by age and include project root`

### Task 5: #1249 (Teil) Doku-Satz (S)

- `docs/providers/opencode.md` nahe `:63`/`:361`: ein Satz »Tier `plugin` + `topology: subagent` → kein Deny, Gate effektiv advisory (Warnung `orchestrator-topology.gate-inactive`); Tier-Fold → #1257«. Kein Code; Beleg-Test existiert: `tests/test_isolation_v2_topology_reconcile.py::test_v2_subagent_emits_exactly_one_log_warning` (`:149`). Tier-Fold gehört zu #1257, nicht in diesen PR.
- Commit: `docs: note advisory opencode gate under subagent topology`

### Task 6: #1241 compose_agent ohne PyYAML (S)

- Red: `tests/test_agent_sync_composition*.py`: `monkeypatch.setattr(agent_sync, "_YAML_AVAILABLE", False)` → `pytest.raises(SyncError)` bei `compose_agent`. Repro: `python3 -m pytest tests/<datei>::test_compose_agent_without_pyyaml_raises -p no:cacheprovider --basetemp=<worktree>/.tmp/pytest-pr2`.
- Green: `agent_sync.py:433-437` `raise SyncError("PyYAML is required … pip install pyyaml")` statt Rückgabe von `override_content`. Sauberer Exit ohne Traceback in `sync.py:main` entfällt (YAGNI).
- Commit: `fix: raise SyncError in compose_agent when PyYAML is missing`

### Task 7: #1266 toten Katalogeintrag a2a-handoff entfernen (S)

- Red: neu `tests/test_plugin_catalog_lint.py`: je `connection.type: stdio`-Eintrag mit `scripts/*`-Arg: Datei existiert und jedes `--flag` kommt als Literal im Skript vor; `tools.allowed ∩ tools.blocked = ∅`; URL-/Header-Variablen ⊆ `secrets`; Negativfall über Fixture-Dict (Funktion, nicht Datei). Heute rot wegen `--mode` (`scripts/viz-logger.py:598`, argparse `:614-632`).
- Green: Eintrag `a2a-handoff` aus `config/plugin-catalog.yaml:106-131` löschen; `README.md:361`, `docs/CODEBASE_OVERVIEW.md:1085,1661` bereinigen; `tests/test_plugin_catalog_migration_invariant.py:32-60` (»seven«) mit `_RETIRED = {"a2a-handoff"}` anpassen (Fixture `tests/fixtures/legacy-registries/mcp-registry.yaml:97-121` bleibt Legacy-Beleg).
- Kein Render-Diff (nicht aktiv, nicht im Bundle, 0 Treffer in `ac01-baseline`). Consumer mit `plugins.a2a-handoff.enabled: true` verlieren den Eintrag still (`registry_query.py:151`) → CHANGELOG.
- Commit: `fix: remove non-functional a2a-handoff plugin catalog entry`

### Task 8: Test-Entkopplung vom Repo-`.tmp` und Zeitbomben (S+)

Nutzerentscheidung: entkoppeln, KEINE Sonderausnahme für basetemp; Basetemp unter `.tmp` bleibt Regel.

- `tests/test_orchestrator_guard_hook.py`: Hook-Läufe nutzen ein eigenes temporäres Projekt/Repo (eigenes nicht-striktes `project.yaml`) statt das Repo-`project.yaml` (strict) zu finden; sonst rc=2 für alles bei `tmp_path` unter `.tmp/`.
- `tests/test_sync_backup_retention.py::test_total_cap_never_selects_unignored_or_without_git` (`:88`): eigenes `git init`-Repo im temp-Projekt, damit `git check-ignore` nicht auf das agent-meta-Repo (`.tmp/` ignoriert) durchgreift.
- Zeitbomben mit festen Daten: `test_sync_backup_retention.py` `_BASE` (`:21`, 2026-01-01) auf `datetime.now()`-relativ (sonst prunt `test_cli_prune_dry_run_lists_and_cli_prunes_with_parity` alle 36); `test_generated_file_drift.py::test_prune_keeps_three_newest_regardless_of_age` (`:712-730`, Stempel `20261031`) auf `_stamp(days)`; `tests/test_cleanup_preview_cli.py:200-230` ebenso (Zeitbombe ab 2026-11-30).
- Verifikation: Lauf beider Testdateien mit `--basetemp=<worktree>/.tmp/pytest-pr2` grün.
- Commit: `test: decouple guard and backup tests from repo tmp and fixed dates`

### Task 9: AC-01-Rebaseline (EIN finaler Commit)

Erst nach Tasks 1-8 (Hook final).

- `tests/fixtures/ac01-baseline/hashes.json:108` (`Claude/.claude/hooks/orchestrator-guard-impl.sh`) und `:530` (`Gemini/.agents/hooks/orchestrator-guard-impl.sh`): `ac01 --write` mit Diff-Gate (nur diese 2 Einträge dürfen sich ändern), sonst abbrechen.
- AC-T4-Digest `tests/test_opencode_v2_surface.py:5512` (`"ac01-baseline"`) plus Log-Kommentare `:5440-5500` und Docstring-Log `tests/test_ac01_render_identity.py` (~`:700-760`).
- `--render-standalone`, dann `python3 scripts/sync.py --config <worktree>/.meta-config/project.yaml` → `.meta-config/generated-file-hashes.json:91` (`.claude/hooks/…`) und `:227` (`.agents/hooks/…`): genau 2 Einträge.
- Goldens (slimming/compact/Topology), `hook_drift`, `dod_push_check`, `schema-property-paths.json`, Context-Ceilings: unverändert (keine Template-/Schema-Änderung).
- Nach jedem sync/validate/ac01-Lauf: `git status --short` — nur erwartete Dateien.
- Danach: `sync.py --check`, `sync.py --validate`, betroffene Testdateien, `tests/test_context_budgets.py`.
- Commit: `chore: rebaseline ac01 hashes after guard 1.12.0`

## CHANGELOG

`### Fixed` (ein Eintrag je Issue, Refs #N): #1258, #1252, #1142 (Ausgabeformat-Änderung `--validate` nennen), #1270 (Verhaltensänderung: Alleinüberlebende > 30 d werden gepruned, Root einbezogen), #1241, #1266 (Katalogeintrag entfernt; `plugins.a2a-handoff.enabled` wirkungslos), #1249 (Doku).

## Offene Punkte / Koordination (für den Nutzer)

- **Hook-Versionskollision:** `1.12.0` kollidiert mit Commit-Authority-Grant-Plan T16 (`docs/plans/2026-11-09-commit-authority-grant-plan.md:289`, ebenfalls 1.11.0 → 1.12.0). T16 müsste auf 1.13.0 wechseln. Dieser Plan ändert jenen Plan NICHT; Entscheidung/Anpassung durch den Nutzer.
- Plan-Freigabe (`APPROVED`) steht aus (M-Klasse).

## Risiken

- R1 #1142: sichtbare Formatänderung in `--validate` (CI-Grepper).
- R2 #1252: naiver Fix bricht #630-Cleanup — durch `proto is None`-Pfad vermieden.
- R3 #1270: Verlust der einzigen Kopie einer Hand-Edit-Vorversion nach 30 d (E-09 akzeptiert); Root-Prune nur auf `*.sync-backup-<ts>`-Namen; `.github/`-Backups bleiben außerhalb.
- R4 #1266: Consumer mit aktivem `a2a-handoff` verlieren Eintrag still; Eintrag war nie funktionsfähig.
- R5 Task 8: Entkopplung darf Guard-Testabdeckung nicht schwächen (gleiche Fälle, nur anderes Projekt-Setup).
- R6 Hook-Version 1.12.0 doppelt geplant (siehe Offene Punkte).

## PR-Body-Hinweise

- Nur `Related #1258 #1252 #1142 #1270 #1249 #1241 #1266`, keine Closing-Keywords; Issue-Schließen nach Merge mit Beleg-Kommentar.
- #1249 nur Doku-Satz; Tier-Fold in #1257. #1142: Plan-Korrektur erwähnen.
- Volle Szenario-Suiten laufen nur in CI; lokal betroffene Testdateien + `--check`/`--validate`.
- Klasse M, keine Architekturänderung.
