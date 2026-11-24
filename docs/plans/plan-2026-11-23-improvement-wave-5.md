---
pipeline_stages:
  implement: 1
status: APPROVED
date: 2026-11-23
spec: docs/specs/2026-11-23-provider-agnostic-sync-hooks-wave-5-spec.md
---

# Provider-agnostic Sync/Hooks/MCP — Wave 5 Implementation Plan

> Status: APPROVED (2026-11-23, Freigabe: User)
> **Spec:** `docs/specs/2026-11-23-provider-agnostic-sync-hooks-wave-5-spec.md` (Status APPROVED, 2026-11-23, SPEC-provider-agnostic-sync-hooks-wave-5)

**Goal:** 20 Issues (Cluster A scripts/lib, B Hooks, C MCP/Config/Tests) provider-agnostisch abarbeiten; ein Branch, ein PR, >= 1 Commit je Item, Rebaseline separat.
**Architecture:** Keine neue Architektur ausser `scripts/lib/managed_block.py` (A6), Dispatch-Tabellen (A4), flache Hook-Python-Module in `hooks/1-generic/lib/` (B3), `schemas/provider-entry.schema.json` (C3). Provider-Unterschiede nur über Config-Keys/Capabilities (Skill `provider-agnostic`).
**Tech Stack:** Python 3.9 stdlib (+PyYAML-Ausnahme, `jsonschema` optional), Bash-Hooks, pytest, YAML/Markdown. Neue Module: `from __future__ import annotations`, kein `match`, kein `X | Y` zur Laufzeit (R7).
**Effort:** siehe `effort-estimator` (Text-Referenz; Spec-Grössen: 11 S, 9 M-Items, hier zerlegt in 46 Tasks <= 8 Dateien; T24/T25 je in a/b gesplittet).

## Global Constraints

- Ein Branch `feat/provider-agnostic-sync-hooks-wave-5` von `main`; **kein** Worktree (`no-worktree-isolation`); alle Tasks sequentiell (Spec: sequentielle Ausführung). `parallel_group` wird **nicht** vergeben (kein Task-Paar ist beweisbar ownership-disjunkt UND baseline-unabhängig).
- >= 1 Commit je Item; Rebaseline-Commits eigene Tasks direkt nach dem auslösenden Commit (Helfer `python3 scripts/rebaseline.py`, Spec `docs/specs/2026-11-15-rebaseline-helper-spec.md`; Aufruf vorher mit `--help` prüfen).
- Commits: Conventional Commits, Englisch, <= 72 Zeichen, Imperativ, kein BOM; Trailer laut Projekt-Config verbatim im Footer. Commit-Anwendung durch Caller/Orchestrator, Push/PR nur `git`-Agent.
- Jeder Commit grün: `python3 scripts/sync.py --validate` (exit 0) + die genannten pytest-Dateien. Hash-/Golden-Pin-Tests (`test_hook_drift`, `test_managed_index_alignment`, `test_generated_file_drift`, `test_ac01_render_identity`) stehen in Trigger-Commits **nicht** in der genannten Liste (siehe Pin-Tabelle); Rebaseline-Aufruf immer `python3 scripts/rebaseline.py --reason "<issue>"` (Write-Modus erzwingt `--reason`), vorab `--check-only`. Rote A-Refactor-Goldens (#1254/#1253/#1255/#1268) stoppen den Branch (BAC-4); Rebaseline dort ist ein Befund, kein Schritt.
- Swap-Regel (Spec): bei > 8 Dateien, nicht byte-identischem Refactor-Diff, 2 erfolglosen Fix-Iterationen -> Item zurückstellen, Reserve einwechseln, PR-Body + Spec-Changelog ergänzen.
- Keine neue Dependency (BAC-7); `pyproject.toml`/`requirements.txt` unverändert.
- Rebase auf `main` nach Cluster A (Task 18) und nach Cluster B (Task 32); Merge-Konflikte an Baselines -> Rebaseline neu, nicht von Hand mergen.
- Zwei-Stufen-Review je Task laut `plan-ledger` (review-req dann review-quality); Checkboxen werden vom Ledger-Writer gesetzt.

## Task-0-Preconditions (Befunde der Code-Verifikation, 2026-11-23)

1. **#1238 Deploy-Pfad (verifiziert):** `scripts/lib/hook_plugins.py::sync_hook_lib` (`HOOK_LIB_SUBDIR = "lib"`) kopiert über `hooks.py::collect_hook_sources(..., subdir="lib", include_py=True)` per **nicht-rekursivem** Glob nur `hooks/1-generic/lib/*.sh` und `*.py` nach `<hooks_dir>/lib/` des Zielprojekts (getrackt in `<hooks_dir>/lib/.agent-meta-managed`, gleiche Layer-Priorität 2-platform > 1-generic > 0-external). Folgen:
   - Neue Extraktions-Module MÜSSEN **flach** in `hooks/1-generic/lib/<name>.py` liegen (Präzedenz: `hook_json_many.py`, geladen über `$module_dir/hook_json_many.py` in `hook_common.sh:129`); sie landen dann ohne Syncer-Änderung als `<hooks_dir>/lib/<name>.py` im Zielprojekt. Kein Unterpaket.
   - `hooks/1-generic/lib/kernel/` (Unterverzeichnis) wird von diesem Glob **nicht** erfasst und ist im Zielprojekt nicht deployt; Kernel-Code wird derzeit nur von Tests (`tests/test_hook_kernel.py`) genutzt. Konsequenz für #1275: die Schutzpfad-Prüfung muss im **deployten** Pfad (`repo-containment-impl.sh` bzw. flaches `lib/*.py`) leben, `kernel/containment.py` nur spiegeln. Falls Kernel-Deploy gewünscht ist -> Befund an User (Scope-Erweiterung `sync_hook_lib` rekursiv), nicht stillschweigend ändern.
2. **Inline-Python-Inventar weicht ab (Stand 2026-11-23):** Ein vollständiger Regex (`INLINE_PY_RX`, unten) liefert in `hooks/1-generic/*.sh` + `lib/hook_common.sh` 24 Zeilen-Treffer (1 davon Kommentar `hook_common.sh:59`). Formen: Heredoc `<<'PYEOF'`/`<<'PY'` (`repo-containment-impl.sh:521/771/886`, `dod-push-check.sh:170/285`, `artifact-freshness.sh:68`, `orchestrator-guard-impl.sh:586`, `viz-log.sh:19`, `artifact-path-guard.sh:79`, `hook_common.sh:495/985/1161` als `cat <<'PY'`-Fragmente, in `dod-push-check.sh:285` gesplict), stdin-Form `"$_PY" -`/`python3 -` (`repo-containment-impl.sh:521/771`, `dod-push-check.sh:170/1508`), `-c`-Einzeiler (`dod-push-check.sh:106`, `viz-log.sh:56`, `repo-containment-impl.sh:274/1379`, `orchestrator-guard-impl.sh:345/502/517/1390/1479`). Zusätzlich `auto-github-release.sh:47` (`"$_PY" -c`, `sys.path.insert`). T23–T25b gleichen ab.
   - `INLINE_PY_RX` (ERE für `grep -E`; Kommentarzeilen `^\s*#` vorher ausfiltern): `<<-?[[:space:]]*["']?PY(EOF)?["']?|(python3?|"?\$_PY"?)[[:space:]]+-([[:space:]]|c[[:space:]])`
   - **Scope (entschieden, User 2026-11-23):** Regex gilt für `hooks/1-generic/*.sh` und `hooks/1-generic/lib/hook_common.sh`. Explizite Ausnahmen (Allowlist mit Begründung im Test) bleiben: `auto-github-release.sh:47` (ausserhalb Scope) und triviale `-c`-Einzeiler ohne Logik (z.B. `repo-containment-impl.sh:274` realpath). Nicht-triviale `-c`-Blöcke (`dod-push-check.sh:106`, `viz-log.sh:56`, `orchestrator-guard-impl.sh:345/502/517/1390/1479`, `repo-containment-impl.sh:1379`) werden extrahiert oder per Allowlist begründet.
3. **Task 3 (#1254)/Task 15 (#1198):** Issue-Beschreibungen veraltet (Spec R8); Tasks dürfen auf Test-/Check-Commits schrumpfen.
4. Q1–Q6 sind entschieden (Spec „Entscheidungen"). Zusätzlich entschieden (User, 2026-11-23): (1) `INLINE_PY_RX` bleibt bei den Allowlist-Ausnahmen (`auto-github-release.sh:47` und triviale `-c`-Einzeiler bleiben ausgenommen); (2) die Optionen (a)/(b)/(d) bleiben in Issue #1337, kein separates Issue. Keine offenen Punkte.
5. **Spec-Abweichung B4 (#1275, verifiziert):** Spec B4 behauptet, `repo-containment-impl.sh` rufe `kernel/containment.py::check_containment` auf. Grep `kernel` in `repo-containment-impl.sh` = 0 Treffer; `check_containment(event: NormEvent)` wird nur von Tests genutzt. Folge: Hook-Logik und Kernel-Spiegel sind zwei Implementierungen -> T27 liefert Paritätstest. Abweichung im PR-Body (T41) vermerken.

## Pin-Tabelle (Rebaseline-Timing; „jeder Commit grün" bleibt wahr)

Hash-/Golden-Pins werden im Trigger-Commit rot und sind bis zum R-Task **nicht** in der Pflicht-pytest-Liste; `--validate` und alle genannten Funktionstests bleiben grün. Wird `--validate` selbst an einem Pin rot (Gegenprobe `rebaseline.py --check-only` im Trigger-Commit), wird die R-Änderung in denselben Trigger-Commit gezogen (R-Task entfällt, im Ledger markieren).

| Gruppe | Trigger-Commits (Pins rot ab) | R-Task (Pins wieder grün) | Pins |
|---|---|---|---|
| #1269 | T10, T11 | T12 | `generated-file-hashes`, Extension-/Managed-Block-Goldens, `test_managed_index_alignment` |
| #1248 | T19 | T20 | `test_hook_drift`, Hook-Hashes |
| #1251 | T21 (bedingt) | T22 | `test_hook_drift` |
| #1238 | T23, T24a, T24b, T25a, T25b | T26 (`test_hook_drift` läuft erst nach T26, nicht in T25a/b) | `test_hook_drift`, `test_hook_registration_invariant`, `test_managed_index_alignment` |
| #1275 | T27, T28 | T29 | Hook-Hashes, Schema-/Default-Goldens |
| #1263 | T30, T31 | T32 | Settings-/Rule-Hashes |

## File Structure (Cluster, Ownership)

- **A** `scripts/lib/{topology,sync_pipeline,opencode_v2_config,isolation,mcp,mcp_provider_config,repo_containment,provider_transform,context,extensions,managed_block(neu),cli_commands,release_scaffold,hooks,log}.py`, `scripts/lib/context_templates/builder.py`, `scripts/lib/consistency/{placeholders,context_budget}.py`, `scripts/sync.py`, `config/{ai-providers.yaml,project-config.schema.json}`, `templates/managed-block.md`, `commands/1-generic/update-extensions.md`, `tests/`.
- **B** `hooks/1-generic/{dod-push-check,lifecycle-check,sync-on-config-change,artifact-path-guard,orchestrator-guard-impl,repo-containment-impl,viz-log}.sh`, `hooks/1-generic/release-gates/artifact-freshness.sh`, `hooks/1-generic/lib/{hook_common.sh,hook_*.py (neue flache Module, Namen je Task)}`, `hooks/1-generic/lib/kernel/{containment,model}.py`, `scripts/lib/{mcp,mcp_deny,repo_containment}.py`, `rules/1-generic/mcp-guardrails.md`, `.claude/skills/submodule-protection/SKILL.md`, Baselines.
- **C** `scripts/lib/{mcp_health,config,providers,context_report,pipelines}.py`, `schemas/provider-entry.schema.json`, `docs/howto/new-mcp-server.md`, `tests/{conftest.py,test_mcp_health.py,test_mcp_server_checklist.py,test_context_budgets.py,...}`, `scripts/measure_context_repin.py`, `.claude/skills/conventions/SKILL.md`.
- **F6 (Datei-Overlap):** Overlap-Map der Spec ist Reihenfolgevertrag; Hot-Files: `sync_pipeline.py` (T2->T3->T5), `provider_transform.py` + `ai-providers.yaml` (nur T6; T35 liest die YAML nur als Schema-Ziel, T7/T9/T15 fassen sie laut Files-Blöcken nicht an), `context.py` (T7->T9->T17 bedingt), `extensions.py` (T8->T10), `cli_commands.py`/`sync.py` (T9->T11->T13), `repo_containment.py` (T4->T28), `config/project-config.schema.json` (T1->T28), `mcp*.py` (T5->T30->T31), `hook_common.sh` + Hooks (T19->T21->T23->T24a->T24b->T25a->T25b->T27->T31).

## Traceability (BAC-6): AC -> Task

| Item | ACs (Spec) | Task(s) | Verifikation |
|---|---|---|---|
| #1243 | AC-1, AC-2 | T1 | `test_orchestrator_topology_schema.py`, `test_context_topology_schema.py`, neu `test_topology_naming.py` |
| #1242 | AC-1, AC-2 | T2 | neu `test_migration_stage_gate.py`, `test_migration_paths.py` |
| #1254 | AC-1, AC-2, AC-3 | T3 | `test_opencode_v2_schema.py`, `test_isolation_v2_topology_reconcile.py`, neu `test_opencode_gate_call_site.py` |
| #1253 | AC-1, AC-2, AC-3, AC-4 | T4, T5 | `test_secrets_and_isolation.py`, neu `test_dispatch_tables.py`, Golden-Diff leer |
| #1255 | AC-1, AC-2, AC-3, AC-4 | T6, T7 | `test_provider_transform_topology*.py`, neu `test_extension_hook_path.py`, Golden-Diff leer |
| #1268 | AC-1, AC-2, AC-3 | T8, T9 | neu `test_managed_block.py`, `test_context_managed_block_shrink.py`, Golden-Diff leer |
| #1269 | AC-1..AC-5 | T10, T11, T12(R) | neu `tests/test_extensions_drift.py`, `test_cli_smoke_multi_provider.py` |
| #1203 | AC-1, AC-2, AC-3 | T13, T14(R, bedingt) | neu `test_backup_label_flag.py`, `test_backup_robustness.py` |
| #1198 | AC-1, AC-2, AC-3 | T15 | `test_placeholder_grace_and_derivation.py`, neu `test_single_brace_known_var.py` |
| #1086 | AC-1 (a–f), AC-2, AC-3 | T16, T17 | `test_sync_log.py`, `test_sync_log_output.py`, neu `test_sync_ux_consistency.py` |
| #1248 | AC-1, AC-2 | T19, T20(R) | `test_hook_drift.py`, `test_hook_registration_invariant.py` |
| #1251 | AC-1, AC-2 | T21, T22(R, bedingt) | `test_hook_kernel.py`, `test_repo_containment_hook.py`, `test_orchestrator_guard_hook.py` |
| #1238 | AC-1, AC-2, AC-3 | T23, T24a, T24b, T25a, T25b, T26(R) | neu `test_hook_mod_common.py`, `test_hook_mod_containment.py`, `test_hook_mod_guards.py`, `test_hook_mod_dod_push.py`, `test_hook_mod_gates.py`; `test_hook_common_lib.py`, `test_hook_lib_sync.py`, `test_hook_single_parse.py` |
| #1275 | AC-1..AC-4 | T27, T28, T29(R) | `test_repo_containment_hook.py`, `test_repo_containment_schema.py`, neu `test_protected_paths.py` (inkl. Kernel-Paritätstest) |
| #1263 | AC-1, AC-2, AC-3 | T30, T31, T32(R) | `test_mcp_deny.py`, neu `test_mcp_guardrails_sync.py` |
| #1262 | AC-1, AC-2, AC-3 | T33 | `test_mcp_health.py` |
| #1274 | AC-1, AC-2 | T34 | neu `test_mcp_server_checklist.py` |
| #1239 | AC-1..AC-4 | T35, T36 | neu `test_provider_entry_schema.py`, `test_pipelines.py` |
| #1240 | AC-1, AC-2 | T37 | volle Collect-Count-Prüfung vor/nachher |
| #1115 | AC-1, AC-2, AC-3 | T38 | `test_context_repin_helper.py` |
| Bundle | BAC-1..BAC-8 | T39–T43 | `--validate`, voller pytest, Grep BAC-5, Secret-Scan |

(R) = Rebaseline-Task. Task-Nummern der Tabelle entsprechen der Reihenfolge unten (Nummerierung final in der Ausführung per Ledger fortschreiben; bei Swap Nummern nicht umnummerieren).

---

## Cluster A — scripts/lib Sync

### Task 0: Branch + Inventar (Rolle: git, dann developer)
**Files:** Add (nur Commit, keine Inhaltsänderung): `docs/plans/plan-2026-11-23-improvement-wave-5.md`, `docs/specs/2026-11-23-provider-agnostic-sync-hooks-wave-5-spec.md` (beide bereits vorhanden/untracked). **Interfaces:** Produces Branch `feat/provider-agnostic-sync-hooks-wave-5`, Inventar-Notiz im PR-Body-Entwurf.
- [ ] Step 1: `git` legt Branch von `main` an (Arbeitsbaum: `opencode.json` ist modifiziert -> nicht committen, vorher klären/stashen lassen durch git-Agent; nur die zwei Doku-Dateien oben werden committed).
- [ ] Step 2: Baseline-Messung `python3 scripts/sync.py --validate` + `pytest --collect-only -q | tail -1` (Testanzahl-Ausgangsstand für BAC-2/#1240 notieren).
- [ ] Step 3: `INLINE_PY_RX`-/Provider-Namens-Greps (Precondition 2, BAC-5) als Ausgangsstand protokollieren.
- Commit: `docs: add wave 5 spec and plan`

### Task 1: #1243 Topologie-Naming (developer, S)
**Files:** Modify `config/project-config.schema.json`, `scripts/lib/topology.py`; Test: Create `tests/test_topology_naming.py`.
**Interfaces:** Consumes `orchestrator.topology`/`context_file.topology`; Produces unterscheidbare Schema-`description`, Docstring-Abgrenzung, Alias+Deprecation nur falls Rename.
- [ ] Step 1: Test schreiben (fail): beide Keys gesetzt -> `--validate` exit 0, `description`-Texte der zwei Schema-Keys verschieden.
- [ ] Step 2: Schema-Descriptions + Docstring ändern; Rename nur mit lesbarem Alt-Key + Deprecation-Hinweis.
- [ ] Step 3: `python3 scripts/sync.py --validate`; `pytest tests/test_topology_naming.py tests/test_orchestrator_topology_schema.py tests/test_context_topology_schema.py`.
- [ ] Step 4: Commit `refactor: disambiguate topology config key naming`
- AC: Spec A1 AC-1/AC-2.

### Task 2: #1242 One-time-Migrationsstages gaten (developer, S)
**Files:** Modify `scripts/lib/sync_pipeline.py`; Test: Create `tests/test_migration_stage_gate.py`.
**Interfaces:** Consumes `config/provider-migrations.yaml`; Produces Gate-Prädikat (Alt-Pfad existiert) vor `apply_discovery_migration`, `apply_provider_migrations`, `migrate_provider_paths`; fail-open + Warnung bei Prüffehler.
- [ ] Step 1: Test (fail): migriertes Fixture, 2. sync ruft `migrate_managed_artifact` nicht auf (Spy), Ausgabe byte-identisch; Fixture mit Alt-Pfaden migriert genau einmal.
- [ ] Step 2: Gate implementieren.
- [ ] Step 3: `--validate`; `pytest tests/test_migration_stage_gate.py tests/test_migration_paths.py tests/test_progress_file_migration.py`.
- [ ] Step 4: Commit `refactor: gate one-time migration stages on legacy paths`
- AC: A2 AC-1/AC-2.

### Task 3: #1254 opencode_v2 am Aufrufort gaten (developer, S, byte-identisch)
**Files:** Modify `scripts/lib/sync_pipeline.py`, `scripts/lib/opencode_v2_config.py`; Test: Create `tests/test_opencode_gate_call_site.py`.
**Interfaces:** Consumes `owns_opencode_surface(provider_config, provider)`, `v2_active`; Produces Gate am Aufruf (`sync_opencode_v2_managed_keys`, `sync_opencode_cli_file`): `owns surface OR State-Datei vorhanden` (Q2, Rollback bleibt erreichbar).
- [ ] Step 1: Test (fail): Nicht-Owner ohne State -> Spy-Writer nicht aufgerufen; Nicht-Owner MIT State -> Rollback-Pfad läuft; Grep-Test auf Provider-Namensvergleiche in `sync_pipeline.py` = 0.
- [ ] Step 2: Gate sichtbar am Aufrufort; Writer-Interna unverändert.
- [ ] Step 3: Golden-Diff leer (Sync über alle Provider-Fixtures, `git diff` auf Goldens leer); `--validate`; `pytest tests/test_opencode_gate_call_site.py tests/test_opencode_v2_schema.py tests/test_isolation_v2_topology_reconcile.py`.
- [ ] Step 4: Commit `refactor: gate opencode v2 writers at call site by capability`
- AC: A3 AC-1..3, BAC-4.

### Task 4: #1253a Isolation-Writer Dispatch (senior-developer, M-Teil 1)
**Files:** Modify `scripts/lib/isolation.py`, `scripts/lib/repo_containment.py`; Test: Create `tests/test_dispatch_tables.py` (Teil Isolation).
**Interfaces:** Produces Tabelle `format_key -> writer` für Isolation (Schlüssel aus Provider-Config); unbekannter Key -> Fehler mit Liste gültiger Keys (exit 1). Consumes `_opencode_v2_gate_permissions`, `_sync_opencode_v2_gate_permissions`.
- [ ] Step 1: Test (fail): unbekannter Key -> Fehlermeldung mit Key-Liste; Isolation-Output pro Provider unverändert.
- [ ] Step 2: Dispatch-Tabelle einführen, bestehende if/elif ersetzen.
- [ ] Step 3: Golden-Diff leer; `--validate`; `pytest tests/test_dispatch_tables.py tests/test_secrets_and_isolation.py tests/test_isolation_v2_topology_reconcile.py tests/test_repo_containment_schema.py`.
- [ ] Step 4: Commit `refactor: dispatch isolation writers via format-key table`
- AC: A4 AC-1, AC-3 (Teil), BAC-4.

### Task 5: #1253b MCP-Format-Writer Dispatch (senior-developer, M-Teil 2)
**Files:** Modify `scripts/lib/mcp_provider_config.py`, `scripts/lib/mcp.py`, `scripts/lib/opencode_v2_config.py`, `scripts/lib/sync_pipeline.py`; Test: Modify `tests/test_dispatch_tables.py`.
**Interfaces:** Produces Tabelle für `fmt ==`-Ketten (~L88-90, ~L222-227, ~L247, ~L960-984) nutzend `V2_MCP_FORMAT`-Muster; Consumes Task 4.
- [ ] Step 1: Test (fail): unbekannter MCP-Format-Key -> Fehler mit Key-Liste; Grep `\bfmt\s*(==|in)\b` nur Tabellen-Lookup.
- [ ] Step 2: Tabelle einführen, Ketten entfernen.
- [ ] Step 3: Golden-Diff leer; BAC-5-Regex über die 6 In-Scope-Module + `sync_pipeline.py`: 0 Treffer (Nachweis fürs PR); `--validate`; `pytest tests/test_dispatch_tables.py tests/test_mcp_health.py tests/test_mcp_deny.py`.
- [ ] Step 4: Commit `refactor: dispatch mcp format writers via format-key table`
- AC: A4 AC-1..AC-4, BAC-4/5.

### Task 6: #1255a Capability `extension_hook_path` + Strip-Hilfsfunktion (senior-developer, M-Teil 1)
**Files:** Modify `config/ai-providers.yaml`, `scripts/lib/provider_transform.py`; Test: Create `tests/test_extension_hook_path.py`.
**Interfaces:** Produces neuer optionaler String-Key `extension_hook_path` (nur beim Claude-Provider, `.claude/3-project/`), Funktion `_strip_extension_hook_lines` (ersetzt `_strip_claude_specific_lines`), eine gemeinsame Prüfhilfe `should_strip_extension_hook(spec)`; Flag `strip-claude-lines` entfällt (7 Stellen in YAML). Leer = fehlend. Consumes bestehende Aufrufe ~L640, ~L783, ~L1042, ~L1304.
- [ ] Step 1: Test (fail): je Provider-Typ (Opencode, ein Flag-Provider, Claude) Extension-Zeile fehlt bzw. ist vorhanden; Opencode-Verhalten (unbedingte Stellen) reproduziert heutiges Ergebnis.
- [ ] Step 2: YAML + Funktion + 4 Aufrufstellen in `provider_transform.py` umstellen (Verhalten je Provider identisch).
- [ ] Step 3: Golden-Diff leer; `--validate`; `pytest tests/test_extension_hook_path.py tests/test_provider_transform_topology.py tests/test_provider_transform_topology_generic.py`.
- [ ] Step 4: Commit `refactor: replace strip-claude-lines flag with extension_hook_path`
- AC: A5 AC-1, AC-3 (Teil), BAC-4.

### Task 7: #1255b `context.py`-Aufrufstelle + Rest-Grep (senior-developer, M-Teil 2)
**Files:** Modify `scripts/lib/context.py`; Test: Modify `tests/test_extension_hook_path.py`.
**Interfaces:** Consumes Task-6-Hilfsfunktion; Produces 5. Aufrufstelle (Import ~L3670, Nutzung ~L3730) über dieselbe Hilfsfunktion.
- [ ] Step 1: Test (fail): AC-4 (alle fünf Aufrufstellen -> gleiche Funktion, Grep-Test) + AC-2 (0 Treffer `strip-claude-lines`/`_strip_claude_specific_lines` in `config/`, `scripts/`).
- [ ] Step 2: `context.py` umstellen.
- [ ] Step 3: Golden-Diff leer; `--validate`; `pytest tests/test_extension_hook_path.py tests/test_context_managed_block_shrink.py tests/test_context_budgets.py`.
- [ ] Step 4: Commit `refactor: route context extension-line stripping through capability`
- AC: A5 AC-2, AC-4, BAC-4.

### Task 8: #1268a Modul `managed_block.py` + `extensions.py` (senior-developer, M-Teil 1)
**Files:** Create `scripts/lib/managed_block.py`; Modify `scripts/lib/extensions.py`; Test: Create `tests/test_managed_block.py`.
**Interfaces:** Produces `render_block(marker_id: str, body: str) -> str`, `replace_block(text: str, body: str, marker_id: str = "agent-meta") -> str`, `ManagedBlockError` (fehlender/doppelter End-Marker, Datei unverändert); Marker-Syntax unverändert. Consumes Inventar (Spec A6).
- [ ] Step 0: Inventar gegen Issue (6 Implementierungen) abgleichen; Abweichung -> Befund an User.
- [ ] Step 1: Test (fail): Fixtures der migrierten Anwendungsfälle byte-identisch; kaputter Marker -> `ManagedBlockError`, Datei unverändert.
- [ ] Step 2: Modul schreiben; `extensions.py` (`update_managed_block:90`, `render_managed_block:51`) darauf umstellen.
- [ ] Step 3: Golden-Diff leer; `--validate`; `pytest tests/test_managed_block.py tests/test_context_managed_block_shrink.py tests/test_native_extensions_whitelist.py`.
- [ ] Step 4: Commit `refactor: add managed_block module and adopt it in extensions`
- AC: A6 AC-1, AC-2 (Teil), BAC-4.

### Task 9: #1268b Übrige Managed-Block-Ersetzer migrieren (senior-developer, M-Teil 2)
**Files:** Modify `scripts/lib/context.py` (~L49, ~L679, ~L1070, Continue-Form L2032), `scripts/lib/context_templates/builder.py`, `scripts/lib/cli_commands.py` (`MANAGED_BEGIN:109`), `scripts/lib/release_scaffold.py` (`_MANAGED_BEGIN:25`); Test: Modify `tests/test_managed_block.py`.
**Interfaces:** Consumes `managed_block`; Detektoren (`generated_file_drift.py`, `consistency/context_size.py`, `external_tools_drift.py`) unberührt. Continue-Sonderform muss byte-identisch bleiben.
- [ ] Step 1: Test (fail): Grep-Test `managed-begin\s*-->\.\*\?` in den Inventar-Dateien = 0 ausserhalb `managed_block.py`.
- [ ] Step 2: Regex-Ersetzer entfernen/umstellen.
- [ ] Step 3: Golden-Diff leer; `--validate`; `pytest tests/test_managed_block.py tests/test_context_managed_block_shrink.py tests/test_cli_smoke_multi_provider.py tests/test_release_checklist_schema.py`.
- [ ] Step 4: Commit `refactor: unify managed block writers on managed_block module`
- AC: A6 AC-1..AC-3, BAC-4.

### Task 10: #1269a Marker-Hash + Drift-Logik (senior-developer, M-Teil 1)
**Files:** Modify `scripts/lib/extensions.py`, `scripts/lib/managed_block.py`, `templates/managed-block.md`; Test: Create `tests/test_extensions_drift.py`.
**Interfaces:** Produces Marker `<!-- agent-meta:managed-begin v=<hash> -->` (Hash über Body; Altform ohne `v=` lesbar), Hash-Mismatch -> WARN + Skip ausser `--force`, fehlender Marker -> Warnung statt Prepend (`extensions.py:101-102`), Orphan-Rolle -> Warnung (Q5: Drift = Warnung+Skip, Fehler nur mit `--strict`).
- [ ] Step 1: Tests (fail): happy, drift, missing marker, orphan role, Altform-Kompatibilität (AC-1..3, AC-5).
- [ ] Step 2: implementieren.
- [ ] Step 3: `--validate`; `pytest tests/test_extensions_drift.py tests/test_managed_block.py`.
- [ ] Step 4: Commit `feat: add hash-based drift protection for extension blocks`
- AC: A7 AC-1, AC-2, AC-3, AC-5.

### Task 11: #1269b CLI `--check`/`--role`/`--force` + Command-Text (developer, M-Teil 2)
**Files:** Modify `scripts/lib/cli_commands.py`, `scripts/sync.py`, `commands/1-generic/update-extensions.md`; Test: Modify `tests/test_extensions_drift.py`, `tests/test_cli_smoke_multi_provider.py`.
**Interfaces:** Produces `update-extensions --check` (kein Schreiben, exit != 0 bei Drift), `--role <name>`, `--force`; `--validate` exit 1 bei Drift nur mit `--strict`.
- [ ] Step 1: Tests (fail): AC-4, `--strict`-Verhalten, argparse akzeptiert Flags.
- [ ] Step 2: implementieren; Command-Text und Sync-Pfad angleichen.
- [ ] Step 3: `--validate`; `pytest tests/test_extensions_drift.py tests/test_cli_smoke_multi_provider.py`.
- [ ] Step 4: Commit `feat: add check, role and force flags to update-extensions`
- AC: A7 AC-4, (6).

### Task 12: Rebaseline #1269 (developer)
**Files:** Modify betroffene Baselines (Hash-/Golden-Dateien laut Helfer-Ausgabe; erwartet `generated-file-hashes.json`, Extension-/Managed-Block-Goldens).
- [ ] Step 1: Rebaseline: `python3 scripts/rebaseline.py --check-only` (Diff prüfen), dann `python3 scripts/rebaseline.py --reason "#1269: extension marker hash"`; Diff prüfen: nur Marker-`v=<hash>`-Änderungen.
- [ ] Step 2: `--validate` + `pytest tests/test_extensions_drift.py tests/test_managed_index_alignment.py`.
- [ ] Step 3: Commit `chore: rebaseline hashes for extension marker hash (#1269)`

### Task 13: #1203 `--backup-label` mit Alias (developer, S)
**Files:** Modify `scripts/sync.py` (`--label` ~L494), `scripts/lib/cli_commands.py`; Test: Create `tests/test_backup_label_flag.py`.
**Interfaces:** Produces kanonisch `--backup-label`, `--label` deprecated Alias (Hinweis stderr), Help nennt beide.
- [ ] Step 1: Test (fail): beide Namen gleiches Backup, Deprecation auf stderr, `--help` nennt `--backup-label`.
- [ ] Step 2: implementieren.
- [ ] Step 3: `--validate`; `pytest tests/test_backup_label_flag.py tests/test_backup_robustness.py tests/test_backup_round_trip_804.py`.
- [ ] Step 4: Commit `feat: add --backup-label and deprecate --label alias`
- AC: A9 AC-1..AC-3.

### Task 14: Rebaseline #1203 (bedingt, developer)
- [ ] Nur wenn Help-Text gepinnt ist und Pin-Test rot wird: `python3 scripts/rebaseline.py --check-only`, dann `python3 scripts/rebaseline.py --reason "#1203: help-text pin for --backup-label"`, sonst Task entfällt (im Ledger als „entfällt" markieren).
- Commit (falls nötig): `chore: rebaseline help-text pin for --backup-label`

### Task 15: #1198 Single-Brace Regressionsschutz (developer, S, verify-first)
**Files:** Modify `scripts/lib/consistency/placeholders.py`; Test: Create `tests/test_single_brace_known_var.py`.
**Interfaces:** Produces Check: Single-Brace `{<bekannte Variable>}` in `agents/`, `rules/`, `templates/` -> WARN -> `--validate`-Fehler; Laufzeit-Platzhalter (`{parent_path}`, `{FolderName}`) lösen nichts aus (Q1: nur Regressions-Check + Issue-Kommentar, kein Template-Umbau).
- [ ] Step 1: Test (fail): künstlich eingefügtes `{SE_BASE_DIR}` -> `--validate` exit 1; `{parent_path}` -> kein Fehler; Grep `{SE_BASE_DIR}` single in `agents/ rules/ templates/` = 0.
- [ ] Step 2: Check implementieren (nutzt Variablenliste ~L106/L201); `provider_transform.py`/`ai-providers.yaml` NICHT anfassen.
- [ ] Step 3: `--validate` (exit 0 auf dem Repo); `pytest tests/test_single_brace_known_var.py tests/test_placeholder_grace_and_derivation.py tests/test_project_context_placeholder_ratchet.py`.
- [ ] Step 4: Commit `feat: warn on single-brace known placeholders (#1198)` (neuer Check in `placeholders.py` = Produktcode; nur falls der Check bereits existiert und nur Tests fehlen: `test:`)
- AC: A10 AC-1..AC-3. Kein Rebaseline.

### Task 16: #1086 a–d Tests + `hooks.py` settings-Label (developer, S)
**Files:** Modify `scripts/lib/hooks.py` (~L216, ~L732, ~L748 -> `hooks_config_file`); Test: Create `tests/test_sync_ux_consistency.py`; Modify `tests/test_sync_log.py` (nur falls Pin passt).
**Interfaces:** (a) `_config_rel_label` Test (alle fünf Aufrufer `project_root`), (b) hartkodiertes `settings.json` aus `hooks_config_file`, (c) `skip` vs `note_unchanged` pinnen, (d) `SyncLog.warn`-Dedup pinnen. Nicht-Ziele g, h, i unberührt.
- [ ] Step 1: Tests (a)(c)(d) (grün, Pin) + (b) (fail).
- [ ] Step 2: (b) fixen.
- [ ] Step 3: `--validate`; `pytest tests/test_sync_ux_consistency.py tests/test_sync_log.py tests/test_sync_log_output.py tests/test_antigravity_hooks_registration.py`; Exit-Codes unverändert.
- [ ] Step 4: Commit `fix: derive hook config label from provider config key`
- AC: A8 a–d, AC-2, AC-3.

### Task 17: #1086 e–f Context-Budget-Meldung + Personal-Legacy-Pin (developer, S)
**Files:** Modify `scripts/lib/consistency/context_budget.py` (`check_over_hard_cap` ~L240); Modify `tests/test_sync_ux_consistency.py`; `scripts/lib/context.py` nur falls Pin-Test rot (`CLAUDE_PERSONAL_LEGACY_FILE:3192`, `init_claude_personal`).
**Interfaces:** (e) Hard-Cap-Meldung nennt geteilte Datei wie die Soft-Cap-Variante (`others`), (f) Migrationsverhalten per Test gepinnt.
- [ ] Step 1: Tests (e) fail, (f) Pin.
- [ ] Step 2: (e) angleichen; (f) nur bei rotem Test ändern.
- [ ] Step 3: `--validate`; `pytest tests/test_sync_ux_consistency.py tests/test_context_budgets.py`.
- [ ] Step 4: Commit `fix: name shared context file in hard-cap message`
- AC: A8 e–f, AC-2, AC-3. Ist ein Teilproblem schon korrekt: nur Test-Commit (`test: pin ...`).

### Task 18: Cluster-A-Abschluss: Rebase + Gesamtprüfung (git, tester)
- [ ] Step 1: `--validate` + voller `pytest`; BAC-5-Grep-Nachweis für Cluster A notieren.
- [ ] Step 2: `git` rebased Branch auf `main`; bei Baseline-Konflikt: Rebaseline-Helfer neu (kein Hand-Merge); Ergebnis erneut `--validate`.
- Kein eigener Commit (ausser Konfliktauflösung: `chore: rebaseline after rebase on main`).

---

## Cluster B — Hooks

### Task 19: #1248 Protokoll-Header (developer, S)
**Files:** Modify `hooks/1-generic/dod-push-check.sh`, `hooks/1-generic/lifecycle-check.sh`, `hooks/1-generic/sync-on-config-change.sh`; Test: Modify `tests/test_hook_drift.py`.
**Interfaces:** Produces `# protocol: tool-hook-v1` statt `# provider: …`; Consumes `hooks.py::parse_hook_metadata` (liest `provider`-Key als Filter ~L584 — Header-Wert darf nicht mehr als Provider-Schalter wirken; Grep-Nachweis, dass kein Hook `provider:` als Schalter nutzt, und dass `hook_protocol`-Semantik (`# hook_protocol:`) nicht kollidiert -> ggf. Key `protocol` gegen `hook_protocol` abgrenzen).
- [ ] Step 1: Test (fail): Grep `^# provider:` in `hooks/` = 0; Registrierung für Claude unverändert; für andere hook-fähige Provider ändert sie sich bewusst (spec Ziel L11; Hooks bleiben `enabled_by_default: false`).
- [ ] Step 2: Header ersetzen.
- [ ] Step 3: `--validate`; `pytest tests/test_hook_registration_invariant.py tests/test_antigravity_hooks_registration.py`.
- [ ] Step 4: Commit `refactor: replace provider hook header with protocol header`
- AC: B1 AC-1, AC-2.

### Task 20: Rebaseline #1248 (developer)
- [ ] Rebaseline: `python3 scripts/rebaseline.py --check-only` (Diff prüfen), dann `python3 scripts/rebaseline.py --reason "#1248: hook protocol header"` (Hook-Hashes); `--validate`; `pytest tests/test_hook_drift.py`.
- Commit: `chore: rebaseline hook hashes for protocol header (#1248)`

### Task 21: #1251 `AM_PROJECT_DIR` Adapter-Variable (senior-developer, S)
**Files:** Modify `hooks/1-generic/lib/hook_common.sh`, `hooks/1-generic/artifact-path-guard.sh`, `hooks/1-generic/orchestrator-guard-impl.sh`, `hooks/1-generic/repo-containment-impl.sh`, `hooks/1-generic/lib/kernel/containment.py`, `hooks/1-generic/lib/kernel/model.py`; Test: Modify `tests/test_hook_kernel.py`, `tests/test_repo_containment_hook.py`.
**Interfaces:** Produces genau eine Variable `AM_PROJECT_DIR` (Adapter setzt sie; `CLAUDE_PROJECT_DIR` nur im Claude-Adapter gelesen); ungesetzt -> bisherige Auflösung (cwd/git root), kein Abbruch. Fixed-Anchor-Tests (`test_fixed_anchor_*`, `test_payload_cwd_cannot_redefine*`) bleiben grün.
- [ ] Step 1: Test (fail): Grep `CLAUDE_PROJECT_DIR` in `hooks/1-generic/` nur im Adapter-Pfad; `AM_PROJECT_DIR` gesetzt/ungesetzt.
- [ ] Step 2: umstellen.
- [ ] Step 3: `--validate`; `pytest tests/test_hook_kernel.py tests/test_repo_containment_hook.py tests/test_orchestrator_guard_hook.py tests/test_artifact_path_guard_hook.py tests/test_hook_common_lib.py`.
- [ ] Step 4: Commit `refactor: read project dir from adapter variable in hooks`
- AC: B2 AC-1, AC-2. Hinweis: Adapter-Stelle (wo `AM_PROJECT_DIR` aus `CLAUDE_PROJECT_DIR` gesetzt wird) im Inventar benennen; bei > 8 Dateien Swap-Regel.

### Task 22: Rebaseline #1251 (bedingt, developer)
- [ ] Nur wenn `python3 scripts/rebaseline.py --check-only` Hook-Hash-Pins rot meldet: `python3 scripts/rebaseline.py --reason "#1251: AM_PROJECT_DIR"`; sonst entfällt.
- Commit (falls nötig): `chore: rebaseline hook hashes for AM_PROJECT_DIR (#1251)`

### Task 23: #1238a Heredocs in `hook_common.sh` -> Module (senior-developer, M-Teil 1)
**Files:** Modify `hooks/1-generic/lib/hook_common.sh`; Create `hooks/1-generic/lib/hook_*.py` (je Heredoc ein flaches Modul, `main(argv: list[str], stdin: str) -> int`); Test: Create `tests/test_hook_mod_common.py`; Modify `tests/test_hook_common_lib.py`.
**Interfaces:** Precondition 1 (flach, Präzedenz `hook_json_many.py`); Aufruf `python3 "$module_dir/<modul>.py"`; Exit-Codes/Verhalten identisch; Fail-closed ohne `python3` (#595) bleibt.
- [ ] Step 0: Precondition 1+2 verifizieren (Deploy-Test: `tests/test_hook_lib_sync.py` deckt neues `lib/*.py` ab; Zielprojekt-Kopie unter `<hooks_dir>/lib/`).
- [ ] Step 1: Unit-Tests je Modul (fail), inkl. Test fail-closed ohne `python3`.
- [ ] Step 2: 4 Heredocs extrahieren.
- [ ] Step 3: `--validate`; `pytest tests/test_hook_mod_common.py tests/test_hook_common_lib.py tests/test_hook_lib_sync.py tests/test_hook_single_parse.py`.
- [ ] Step 4: Commit `refactor: extract hook_common heredocs into python modules`
- AC: B3 AC-1, AC-2.

### Task 24a: #1238b1 `repo-containment-impl.sh` (senior-developer, M-Teil 2a)
**Files:** Modify `hooks/1-generic/repo-containment-impl.sh` (Heredocs 521/771/886, `-c` 1379; 274 trivial -> Allowlist); Create `hooks/1-generic/lib/hook_containment_*.py` (<= 3 flache Module); Test: Create `tests/test_hook_mod_containment.py`. (<= 5 Dateien)
- [ ] Step 1: Unit-Tests je Modul (fail), Fail-closed (#595) per Test. Step 2: extrahieren. Step 3: `--validate`; `pytest tests/test_hook_mod_containment.py tests/test_repo_containment_hook.py tests/test_hook_lib_sync.py` (kein `test_hook_drift`, siehe Pin-Tabelle).
- [ ] Step 4: Commit `refactor: extract repo-containment hook python into modules`
- AC: B3 AC-1, AC-2.

### Task 24b: #1238b2 `artifact-path-guard.sh` + `orchestrator-guard-impl.sh` (senior-developer, M-Teil 2b)
**Files:** Modify `hooks/1-generic/artifact-path-guard.sh` (:79), `hooks/1-generic/orchestrator-guard-impl.sh` (:586 Heredoc; `-c` 345/502/517/1390/1479 extrahieren oder per Allowlist begründen); Create `hooks/1-generic/lib/hook_guard_*.py` (<= 3 flache Module); Test: Create `tests/test_hook_mod_guards.py`. (<= 7 Dateien)
- [ ] Step 1: Unit-Tests je Modul (fail), Fail-closed (#595) je Hook. Step 2: extrahieren. Step 3: `--validate`; `pytest tests/test_hook_mod_guards.py tests/test_orchestrator_guard_hook.py tests/test_artifact_path_guard_hook.py tests/test_hook_notebook_multiedit.py`.
- [ ] Step 4: Commit `refactor: extract guard hook python into modules`
- AC: B3 AC-1, AC-2.

### Task 25a: #1238c1 `dod-push-check.sh` (senior-developer, M-Teil 3a)
**Files:** Modify `hooks/1-generic/dod-push-check.sh` (:106, :170, :285, :1508); Create `hooks/1-generic/lib/hook_dod_push_*.py` (<= 4 flache Module); Test: Create `tests/test_hook_mod_dod_push.py`. (<= 6 Dateien)
**Interfaces:** Consumes T23 (`hook_push_arg_parser_py`/`hook_shell_scan_py` aus `hook_common.sh` sind in :285 gesplict — Modul-Aufruf muss denselben Code laden, Verhalten byte-identisch).
- [ ] Step 1: Unit-Tests (fail), Fail-closed ohne `python3` (#595). Step 2: extrahieren. Step 3: `--validate`; `pytest tests/test_hook_mod_dod_push.py tests/test_hook_lib_sync.py tests/test_hook_common_lib.py` (kein `test_hook_drift`).
- [ ] Step 4: Commit `refactor: extract dod-push-check python into modules`
- AC: B3 AC-1, AC-2.

### Task 25b: #1238c2 `artifact-freshness.sh` + `viz-log.sh` + Regex-Nachweis (senior-developer, M-Teil 3b)
**Files:** Modify `hooks/1-generic/release-gates/artifact-freshness.sh` (:68), `hooks/1-generic/viz-log.sh` (:19, :56); Create `hooks/1-generic/lib/hook_gate_*.py` (<= 2 flache Module); Test: Create `tests/test_hook_mod_gates.py`. (<= 5 Dateien)
**Interfaces:** `artifact-freshness.sh` liegt in `release-gates/` (separater Deploy via `sync_release_gates`); Modul-Pfad relativ zum deployten `lib/`-Ordner des Hook-Dirs auflösen (nicht relativ zum Gate-Skript) — Test mit Zielprojekt-Layout.
- [ ] Step 1: Unit-Tests (fail). Step 2: extrahieren. Step 3: Abschluss-Check AC-3: `INLINE_PY_RX` (Precondition 2) über `hooks/1-generic/*.sh` + `lib/hook_common.sh` (ohne Kommentarzeilen) = 0 Treffer ausser der Allowlist (`tests/test_hook_mod_gates.py::test_inline_py_allowlist`, je Eintrag Begründung); `--validate`; `pytest tests/test_hook_mod_gates.py tests/test_hook_lib_sync.py`.
- [ ] Step 4: Commit `refactor: extract gate hook python into modules`
- AC: B3 AC-1..AC-3.

### Task 26: Rebaseline #1238 (developer)
- [ ] Rebaseline: `python3 scripts/rebaseline.py --check-only` (Diff prüfen), dann `python3 scripts/rebaseline.py --reason "#1238: extracted hook modules"`; `--validate`; `pytest tests/test_hook_drift.py tests/test_hook_registration_invariant.py tests/test_managed_index_alignment.py`.
- Commit: `chore: rebaseline hook hashes for extracted modules (#1238)`

### Task 27: #1275a Schutzpfad-Prüfung im deployten Hook (senior-developer, S/M-Teil 1)
**Files:** Modify `hooks/1-generic/repo-containment-impl.sh`, `hooks/1-generic/lib/kernel/containment.py` (Spiegel, Precondition 1+5: nicht deployt, vom Hook nicht aufgerufen); evtl. Modul aus T24a; Test: Create `tests/test_protected_paths.py` (inkl. Paritätstest).
**Interfaces:** Produces Block (exit 2) für Edit/Write/NotebookEdit und Bash-Redirect-Ziele unter `repo_containment.protected_paths` (Default `external/`, `.agent-meta/`, plus `path =` aus vorhandener `.gitmodules`); Override `AM_ALLOW_PROTECTED_WRITE=1`; `_META_SUBMODULE`-Ausnahme bleibt für Lesen; Convention boundary.
- [ ] Step 1: Tests (fail): Write `external/foo` -> Block mit Meldung; `docs/foo` -> erlaubt; Override -> erlaubt; `.gitmodules` `path = foo` -> `foo/a` blockt (AC-1..4).
- [ ] Step 1b: Paritätstest (fail ohne Spiegel): gleiche Pfad-/Redirect-Eingaben ergeben im Hook (Subprozess) und in `kernel/containment.py::check_containment` dieselbe Block/Allow-Entscheidung (zwei Implementierungen -> Drift-Schutz; Alternative: Spiegel weglassen und in PR dokumentieren).
- [ ] Step 2: implementieren. Step 3: `--validate`; `pytest tests/test_protected_paths.py tests/test_repo_containment_hook.py tests/test_hook_kernel.py`.
- [ ] Step 4: Commit `feat: block writes to protected submodule paths in hooks`
- AC: B4 AC-1..AC-4.

### Task 28: #1275b Config-Auflösung + Skill-Text (developer, S)
**Files:** Modify `scripts/lib/repo_containment.py`, `config/project-config.schema.json`, `.claude/skills/submodule-protection/SKILL.md`; Test: Modify `tests/test_repo_containment_schema.py`.
**Interfaces:** Produces Schema-Key `repo_containment.protected_paths` (Liste), Syncer-Auflösung in den Hook (gleiche Präzedenz wie bestehende Config-Auflösung); Skill-Text „`.gitmodules` falls vorhanden". Konsumiert Task 27.
- [ ] Step 1: Test (fail): Schema akzeptiert Liste, Default greift. Step 2: implementieren. Step 3: `--validate`; `pytest tests/test_repo_containment_schema.py tests/test_protected_paths.py`.
- [ ] Step 4: Commit `feat: add repo_containment.protected_paths config key`
- AC: B4 AC-1 (Default-Liste greift), AC-3 (Override-Config), AC-4 (`.gitmodules`-Pfade ergänzt); Schema validiert Liste von Strings.

### Task 29: Rebaseline #1275 (developer)
- [ ] Rebaseline: `python3 scripts/rebaseline.py --check-only` (Diff prüfen), dann `python3 scripts/rebaseline.py --reason "#1275: protected paths"`; `--validate`; Commit: `chore: rebaseline hashes for protected paths (#1275)`

### Task 30: #1263a MCP-Deny-Liste aus Registry (senior-developer, S/M-Teil 1)
**Files:** Modify `scripts/lib/mcp.py`, `scripts/lib/mcp_deny.py`, `rules/1-generic/mcp-guardrails.md`; Test: Create `tests/test_mcp_guardrails_sync.py`; Modify `tests/test_mcp_deny.py`.
**Interfaces:** Produces maschinenlesbare Deny-Liste (Quelle: MCP-Registry-Verbotsliste, z.B. `playwright`) -> `permissions.deny` (Provider mit Capability), Prosa in `mcp-guardrails.md` aus derselben Quelle (ADR-3, Rule wird generiert/geprüft, nicht manuell editiert); leere Liste -> kein Eintrag.
- [ ] Step 1: Tests (fail): Settings enthalten genau die Tools; Prosa == Deny-Liste; leere Liste. Step 2: implementieren. Step 3: `--validate`; `pytest tests/test_mcp_guardrails_sync.py tests/test_mcp_deny.py`.
- [ ] Step 4: Commit `feat: derive mcp deny list from registry for settings and rule`
- AC: B5 AC-1, AC-2.

### Task 31: #1263b Hook-Fallback-Check (senior-developer, S)
**Files:** Modify `hooks/1-generic/lib/hook_common.sh` (+ evtl. Modul aus T23), `scripts/lib/mcp_deny.py`; Test: Modify `tests/test_hook_common_lib.py`.
**Interfaces:** Provider ohne `permissions.deny`-Capability: Hook blockt verbotenen Tool-Aufruf (Block-Pfad, nicht neue Provider-Namenslogik).
- [ ] Step 1: Test (fail): AC-3 (Aufruf eines verbotenen Tools geblockt). Step 2: implementieren. Step 3: `--validate`; `pytest tests/test_hook_common_lib.py tests/test_mcp_deny.py`.
- [ ] Step 4: Commit `feat: block denied mcp tools in hook fallback path`
- Hinweis PR (R3): Deny-Semantik wirkt erst nach Sync/Neustart.

### Task 32: Rebaseline #1263 + Rebase auf main (developer, git)
- [ ] Rebaseline: `python3 scripts/rebaseline.py --check-only` (Diff prüfen), dann `python3 scripts/rebaseline.py --reason "#1263: mcp deny list"`; `--validate`; Commit: `chore: rebaseline settings and rule hashes for mcp deny (#1263)`
- [ ] `git` rebased auf `main` (Cluster-B-Ende); Konflikte -> Rebaseline neu. BAC-5-Grep-Nachweis (`# provider:` in `hooks/` = 0).

---

## Cluster C — MCP / Config / Tests

### Task 33: #1262 MCP-URL/Secret-Validate (developer, S)
**Files:** Modify `scripts/lib/mcp_health.py`, Validate-Aufrufstelle (Importer von `mcp_health`: `grep -rn "mcp_health" scripts/lib` zu Task-Beginn ausführen, Fundort im Ledger notieren; höchstens 1 zusätzliche Datei); Test: Modify `tests/test_mcp_health.py`.
**Interfaces:** Produces `list[tuple[server, severity, message]]`; URL via `urllib.parse` (http/https/ws/wss); Secrets nur `${VAR}`, Klartext -> Fehler (Wert NICHT in Meldung); ungesetzte Env-Var -> Warnung; kein Netzwerk; Fehler -> `--validate` exit 1.
- [ ] Step 1: Tests (fail): AC-1..3. Step 2: implementieren. Step 3: `--validate` (Repo-Config exit 0); `pytest tests/test_mcp_health.py`.
- [ ] Step 4: Commit `feat: validate mcp urls and secret references in validate`
- AC: C1 AC-1..AC-3. Rebaseline: nein.

### Task 34: #1274 Scaffold + Checklisten-Test (developer, S)
**Files:** Create `docs/howto/new-mcp-server.md`, `tests/test_mcp_server_checklist.py`.
**Interfaces:** Consumes Task 33; parametrisiert über alle Registry-Server: Eintrag vollständig, `mcp-<server>/SKILL.md`, Guardrail-Eintrag (falls Verbotsliste), #1262-Check besteht.
- [ ] Step 1: Test (fail bei künstlichem Server ohne Skill, Servername in Meldung). Step 2: Doc + Test. Step 3: `pytest tests/test_mcp_server_checklist.py`; `--validate`.
- [ ] Step 4: Commit `test: add mcp server checklist test and howto`
- AC: C2 AC-1, AC-2.

### Task 35: #1239a Provider-Entry-Schema + Validate (senior-developer, M-Teil 1)
**Files:** Create `schemas/provider-entry.schema.json`; Modify `scripts/lib/config.py` (Muster L130, `jsonschema` optional mit Fallback), `scripts/lib/providers.py`; Test: Create `tests/test_provider_entry_schema.py`.
**Interfaces:** Schema enthält neue Keys aus T3–T7 (`extension_hook_path`, Format-Keys); Nicht-Ziele: `update_providers_enum` (`schema.py`), Defaults-Tabelle `external_tools_drift.py:192-194`; keine neue Dependency.
- [ ] Step 1: Tests (fail): AC-1 (alle Einträge valide), AC-2 (unbekannter Key/Typfehler -> exit 1 mit Eintrag+Feld). Step 2: implementieren. Step 3: `--validate`; `pytest tests/test_provider_entry_schema.py tests/test_provider_options_schema.py`.
- [ ] Step 4: Commit `feat: add json schema for provider registry entries`
- AC: C3 AC-1, AC-2, BAC-7.

### Task 36: #1239b Capability-Quellen mergen + `pipelines.py` (senior-developer, M-Teil 2)
**Files:** Modify `scripts/lib/context_report.py` (`merge_provider_mappings:205`), `scripts/lib/providers.py` (`load_providers_config:313`, `load_provider_capabilities:422`), `scripts/lib/pipelines.py` (~L56); Test: Modify `tests/test_provider_entry_schema.py`, `tests/test_pipelines.py`.
**Interfaces:** Führende Quelle `config/ai-providers.yaml` (Q6); Konflikt -> Fehler mit beiden Fundorten; Provider-Literalliste aus Registry abgeleitet.
- [ ] Step 1: Tests (fail): AC-3 (Konflikt), AC-4 (keine Provider-Literalliste in `pipelines.py`). Step 2: implementieren. Step 3: `--validate`; `pytest tests/test_provider_entry_schema.py tests/test_pipelines.py tests/test_topology_capability_invariant.py`.
- [ ] Step 4: Commit `refactor: merge capability sources and derive pipeline providers`
- AC: C3 AC-3, AC-4. Falls ein Rebaseline nötig wird: eigener Task direkt danach.

### Task 37: #1240 Provider-Enumeration zentralisieren (developer, M)
**Files:** Modify `tests/conftest.py`, `tests/test_context_budgets.py` und weitere per Grep (`("Claude", "Gemini"`, `_PROVIDERS =`) gefundene Tests (<= 8 Dateien; sonst Swap/Split nach Test-Verzeichnis).
**Interfaces:** Produces `ALL_PROVIDERS` (Konstante/Fixture aus Registry via C3-Loader); leere Registry -> laut fehlschlagen; Consumes Task 36.
- [ ] Step 1: Collect-Count vorher notieren; Test (fail): leere Registry -> Fixture-Fehler. Step 2: umstellen. Step 3: Collect-Count gleich (AC-2); Grep hartkodierte Tupel = 0 ausser Zentraldatei; `--validate`; voller `pytest`.
- [ ] Step 4: Commit `test: centralize provider enumeration in conftest`
- AC: C4 AC-1, AC-2.

### Task 38: #1115 Re-Pin-Helfer `--profile compact` (developer, S)
**Files:** Modify `scripts/measure_context_repin.py`, `.claude/skills/conventions/SKILL.md`; Test: Modify `tests/test_context_repin_helper.py`.
**Interfaces:** `--profile {full,compact}` (Default `full`); `compact` druckt Block gegen `_IST_COMPACT` (`tests/test_context_budgets.py:609`); Idempotenz: zweiter Lauf -> kein Block, exit 0; `TOLERANCE_MAX_BYTES = 4096` unverändert.
- [ ] Step 1: Tests (fail): AC-1 (exit 1 bei Abweichung, sonst 0/leer), AC-3 (Skill nennt Befehl wörtlich). Step 2: implementieren. Step 3: `pytest tests/test_context_repin_helper.py tests/test_context_budgets.py`; `--validate`.
- [ ] Step 4: Commit `feat: support compact profile in context repin helper`
- AC: C5 AC-1..AC-3.

---

## Abschluss

### Task 39: Volle Verifikation (tester)
- [ ] Step 1: `python3 scripts/sync.py --validate` exit 0 (BAC-1).
- [ ] Step 2: voller `pytest`; Testanzahl >= Ausgangsstand aus Task 0 (BAC-2).
- [ ] Step 3: BAC-5-Greps (beide Regex, 6 A4-Module + `sync_pipeline.py`; `# provider:` in `hooks/`) mit Ausnahme-Nachweis; B3-AC-3: `INLINE_PY_RX` (Precondition 2) = 0 Treffer ausser dokumentierter Allowlist; BAC-7: `git diff main -- pyproject.toml requirements.txt` leer.
- [ ] Step 4: Commit-Zählung: je Item >= 1 Commit (BAC-3), Rebaseline-Commits separat.

### Task 40: Secret-Scan (security-reviewer)
- [ ] Projekt-Secret-Scan über alle geänderten Dateien (`git diff --name-only main...HEAD`); Fund blockiert (BAC-8), manuelle Eskalation.

### Task 41: PR-Body-Entwurf (documenter)
**Files:** Create `.tmp/pr-body-wave-5.md` (Scratch-Sink, nicht committen).
- [ ] Gliederung nach Cluster A/B/C + Commit-Bereichen; Hinweise R3 (Deny wirkt nach Sync/Neustart), R4 (`AM_ALLOW_PROTECTED_WRITE=1`), R6 (`--label`-Alias); BAC-5-Ausnahmeliste; Swaps (falls vorhanden); `#1238`-Befund (Deploy flach, kernel nicht deployt); Abweichung Spec B4: `repo-containment-impl.sh` ruft `kernel/containment.py` nicht auf (Grep 0), daher zwei Implementierungen + Paritätstest (T27); `INLINE_PY_RX`-Scope-Entscheid und Allowlist; Verweis: Optionen (a)/(b)/(d) bleiben in Issue #1337.
- [ ] Footer: je Issue **eine eigene Zeile** (nur das erste `#N` pro Zeile schliesst zuverlässig):
```
Resolves #1243
Resolves #1242
Resolves #1254
Resolves #1253
Resolves #1255
Resolves #1268
Resolves #1269
Resolves #1203
Resolves #1198
Resolves #1086
Resolves #1248
Resolves #1251
Resolves #1238
Resolves #1275
Resolves #1263
Resolves #1262
Resolves #1274
Resolves #1239
Resolves #1240
Resolves #1115
```
- Attribution-Zeile laut Harness-Vorgabe am Ende.

### Task 42: Push + PR (git — ausschliesslich git-Agent)
- [ ] Push `feat/provider-agnostic-sync-hooks-wave-5`, PR gegen `main` mit Body aus Task 41. Kein Worktree, kein Merge ohne User-OK.

### Task 43: Kommentar an #1198 (git)
- [ ] `/home/hermes/.local/bin/gh issue comment 1198`: 0 Single-Brace-Treffer in `agents/ rules/ scripts/ config/` (Stand 2026-11-23), Regressions-Check in Task 15 hinzugefügt, Verweis auf PR.

## Re-Planning

Nach Cluster A (Task 18), Cluster B (Task 32) und vor dem PR: Annahmen prüfen (Items noch offen? Golden-Diffs byte-identisch? Preconditions 1+2 unverändert?), Plan aktualisieren, nicht einfrieren.

## Self-Review

- Jeder Task mappt auf genau eine Rolle (Mehrrollen-Tasks 0/18/32 sind Gate-Tasks ohne Dateiänderung; vor Ausführung je auf eine Rolle festlegen: 0 git, 18 tester, 32 developer + separater git-Schritt).
- Tasks <= 8 Dateien: ja, geprüft (grösster: T21 mit 8 inkl. 2 Tests, danach T24b <= 7, T25a <= 6; T24/T25 der Erstfassung (9 bzw. >= 11 Dateien) in a/b gesplittet); Spec-M-Items #1253/#1255/#1268/#1269/#1238/#1275/#1263/#1239 in 2–3 Tasks zerlegt, #1240 per Grep-Ergebnis (Split-Regel).
- Keine Dateiüberlappung innerhalb einer Parallel-Gruppe: es gibt keine `parallel_group`.
- `pipeline_stages` deckt die `plan-driven`-Stage `implement` ab (Task 1 = erster Implementierungs-Task; Task 0 ist Gate).
