# Blast-Radius-Analyse: Strangler-Refactor Phase 4c (#481/#482/#483)

| | |
|---|---|
| **Date** | 2026-09-06 |
| **Status** | ANALYSIS (READ-ONLY, kein Code geändert, kein Commit) |
| **Scope** | Phase 4c des Plans `docs/plans/2026-09-05-issue-674-roadmap.md` — Issues #481, #482, #483 |
| **Branch** | `feat/issue-674-roadmap` (Working Tree, HEAD `03e0b583`) |
| **Basis** | Aktuelle Issue-Texte (GitHub, 2026-09-06 abgerufen) vs. aktueller Code; Issue-Zeilenangaben vom 2026-08-11 sind **alle obsolete** |

---

## 0. Executive Summary — Zentrale Reconciliation

**Alle drei Issues sind im aktuellen Working Tree bereits weitgehend oder vollständig umgesetzt** —
durch drei unabhängige frühere Stränge:

| Issue | Issue-Scope (2026-08-11) | Aktueller Stand im Working Tree | Restscope |
|---|---|---|---|
| **#481** sync.py::main zerlegen | 886 Zeilen main(), 3 Responsibilities | `main()` = 16 Zeilen; argparse in `_build_arg_parser()`; 17 Mode-Handler via `_MODE_HANDLERS`-Tabelle + `_dispatch()`; Sync-Logik → `lib/sync_pipeline.py` (12 Stages, NEU/ungestaged) | CLI-Handler (`_handle_*`, `_SyncContext`, `_build_context`, `_run_common_tail`, validate-Helper ≈ 900 Zeilen) leben **noch in sync.py** statt `lib/cli_commands.py` |
| **#482** build_variables zerlegen | 454 Zeilen God-Function, 5 Blöcke, 5 lokale Imports | `build_variables()` = 30 Zeilen pure Orchestrierung; 8 `_build_*_variables()`-Helfer (#566); **alle Imports top-level** | **Kein Code-Restscope** — nur Abschlusshandlungen (Verifikation + Issue schließen) |
| **483** agents.py transform/sync | 2 God-Functions (245 + 274 Zeilen) in agents.py | agents.py = 176 Zeilen Hint-Builder; transform → `lib/provider_transform.py` (Daten-getrieben, #629); sync → `lib/agent_sync.py` (50 Zeilen Orchestrator, 9 Helper) — **#561/#565 hat das Issue vorweggenommen** | `transform_agent_content_for_provider` ist 52 statt "<50" Zeilen (kosmetisch); stale Docstring provider_transform.py:6-7 |

**Konsequenz für die Implementation:** Phase 4c ist kein "implementiere 3 Refactors"-Task mehr,
sondern: **(1) #481-Restscope extrahieren (der einzige echte Code-Aufwand), (2) #482 als erledigt verifizieren/schließen, (3) #483 als durch #561/#565/#629 übererfüllt schließen, (4) ungestagede Arbeitsstände sichern.** Ohne diese Reconciliation besteht Doppel-Refactor-Gefahr.

---

## 1. Issue #481 — sync.py::main (aktueller Stand)

### 1.1 Struktur von scripts/sync.py (1315 Zeilen)

| Zeilen | Block | Rolle |
|---|---|---|
| 1–52 | Docstring + UTF-8-Force + sys.path-Setup | Entrypoint-Infrastruktur |
| 54–121 | 20 Top-level lib-Imports (inkl. `lib.sync_pipeline`) | Import-Hub |
| 123–138 | Entrypoint-Konstanten (`EXT_SUFFIX`, `MANAGED_BEGIN/END`, `LOGFILE`, `EXTERNAL_SKILLS_CONFIG`, `_CONFIG_CANDIDATES`) | CLI-Konstanten |
| 149–184 | `resolve_test_repo_path()` | --validate-Helper |
| 187–211 | `_run_consistency_checks()` (importlib auf consistency-check.py) | --validate-Helper |
| 214–311 | `validate_test_repo()` (Voll-Sync ins Test-Repo) | --validate-Helper |
| 318–324 | `_normalize_check_dry_run()` | --check-Semantik |
| 327–350 | `_SyncContext` (11 Felder, 2 Write-backs: `mode`, `config`) | Shared State |
| 354–487 | `_build_arg_parser()` — **pure argparse, keine Side-Effects** ✓ (Issue-Kriterium 1 erfüllt) | CLI-Kontrakt |
| 490–505 | `_run_test_plugin()` | Early-Return-Mode |
| 508–661 | `_build_context()` — 7 Early-Return-Modes + Setup-Fallthrough + Config-Autodetect + `build_variables` | Pre-Dispatch |
| 664–1165 | **17 `_handle_*`-Funktionen** (502 Zeilen) | Dispatch-Handler |
| 1167–1199 | `_MODE_HANDLERS`-Tabelle (19 Prädikate) + `_dispatch()` | Dispatcher ✓ (Issue-Kriterium: Registry-Dispatch) |
| 1202–1293 | `_run_common_tail()` (env scripts, viz, AST, log.write, --check exit, --admin, Restart-Notice) | Common Tail |
| 1296–1311 | `main()` — parse → normalize → build_context → dispatch → tail (16 Zeilen) | ✓ Issue-Kriterium "<50 Zeilen" erfüllt |

### 1.2 Vollständige Mode-Liste (aktuell)

**A) Early-Return-Modes in `_build_context` (vor Config-Load, Zeilen 508–661):**

| Flag | Funktion | Rückkehr |
|---|---|---|
| `--clear-cache` | `lib.cache.invalidate` | early return None |
| `--test-plugin ID` | `_run_test_plugin` | `sys.exit(code)` |
| `--update-models` | `lib.model_discovery.discover_models` | early return None |
| `--render-standalone` (+`--check`) | `lib.standalone.write_standalone_files` | early return / `sys.exit(1)` bei Drift |
| `--admin-only` (+`--admin-port`) | `subprocess.run(admin-server.py)` | early return None |
| `--add-skill URL` (+`--skill-name --source --role [--entry]`) | `lib.skill_admin.add_skill` | `sys.exit(1)` bei fehlenden Pflichtflags; sonst return |
| `--setup` | `lib.setup.run_setup_wizard` → fällt durch zu `--init`-Sync | Durchgang |

**B) `_MODE_HANDLERS`-Tabelle (Zeilen 1170–1190) — Reihenfolge = Flag-Präzedenz:**

| # | Prädikat | Handler | Flag(s) |
|---|---|---|---|
| 1 | `a.fill_defaults` | `_handle_fill_defaults` | `--fill-defaults` |
| 2 | `a.audit_config` | `_handle_audit_config` | `--audit-config` (+`--apply`) |
| 3 | `a.only_variables` | `_handle_only_variables` | `--only-variables` |
| 4 | `a.create_ext` | `_handle_create_ext` | `--create-ext ROLE` ('all' unterstützt) |
| 5 | `a.update_ext` | `_handle_update_ext` | `--update-ext` |
| 6 | `a.create_rule` | `_handle_create_rule` | `--create-rule NAME` |
| 7 | `a.create_hook` | `_handle_create_hook` | `--create-hook NAME` |
| 8 | `a.create_command` | `_handle_create_command` | `--create-command NAME` |
| 9 | `a.viz_only` | `_handle_viz_only` | `--viz-only` |
| 10 | `a.viz_cleanup` | `_handle_viz_cleanup` | `--viz-cleanup` |
| 11 | `a.deactivation_status` | `_handle_deactivation_status` | `--deactivation-status` |
| 12 | `a.deactivate_providers is not None` | `_handle_deactivate_providers` | `--deactivate-providers [P…]` |
| 13 | `a.activate_providers is not None` | `_handle_activate_providers` | `--activate-providers [P…]` |
| 14 | `a.backup is not None` | `_handle_backup` | `--backup [P…]` (+`--label`) |
| 15 | `a.restore` | `_handle_restore` | `--restore ARCHIVE` (+`--restore-providers`, `--force`) |
| 16 | `a.list_backups` | `_handle_list_backups` | `--list-backups` |
| 17 | `a.delete_backup` | `_handle_delete_backup` | `--delete-backup ARCHIVE` |
| 18 | `a.prune_backups` | `_handle_prune_backups` | `--prune-backups` |
| 19 | `a.validate` | `_handle_validate` | `--validate` |
| – | Default | `_handle_sync` | plain sync / `--init` / `--viz` / `--viz-mode` / `--admin` / `--check` |

Hinweis: Der alte 40-Branch-If/elif-Char (Issue-Text) existiert nicht mehr — heute sind es
19 Tabellen-Einträge + 7 Early-Returns; einige Modi (Admin-UI, Model-Discovery, Standalone)
sind neu hinzugekommen, andere (#481-zeitgemäß) in lib gewandert.

### 1.3 Reconciliation Ziellayout — `cli_commands.py` vs. `commands/` vs. existierendes `commands.py`

**Namenskonflikt bestätigt:** `scripts/lib/commands.py` existiert (230 Zeilen) und ist **kein**
CLI-Modul, sondern die Projekt-Commands-Sync-Schicht (analog `rules.py`):

| Funktion in `lib/commands.py` | Zeilen | Rolle |
|---|---|---|
| `collect_command_sources()` | 16–45 | 0-external/1-generic/2-platform-Layer-Sammlung |
| `_add_frontmatter_field()` | 48–57 | Continue: `invokable: true`-Injection |
| `_md_to_toml()` | 60–93 | Claude-.md → Gemini-.toml-Konvertierung |
| `sync_commands_for_provider()` | 96–194 | Provider-Write-out + Managed-Index + Stale-Cleanup |
| `create_command()` | 197–230 | Template für `--create-command` (CLI-Handler aufruft) |

Ein Package `lib/commands/` **kann nicht parallel zum Modul `lib/commands.py` existieren**
(Python-Namenskollision im selben Package). Optionen:

| Option | Beschreibung | Bewertung |
|---|---|---|
| **A) `lib/cli_commands.py` (Einzelmodul)** — Issue-Vorschlag | Alle `_handle_*` + `_SyncContext` + `_build_context` + `_run_common_tail` + validate-Helper dorthin (~900–1000 Zeilen); `sync.py` behält Parser, Konstanten, main() | **Empfohlen.** 0 Konflikt, 0 Rename, Issue-konform, reine Moves möglich. Nachteil: zweites ~1000-Zeilen-Modul; Package-Split später möglich |
| **B) `lib/cli_commands/` Package** | `parser.py`, `context.py`, `handlers/<gruppe>.py`, `tail.py` | Sauberer, aber mehr Move-Aufwand; erst bei >1000 Zeilen gerechtfertigt |
| **C) Rename `commands.py` → `command_files.py` + Package `commands/`** (User-Anweisung wörtlich) | Erfüllt "scripts/lib/commands/", kostet aber: 4 Import-Sites (`sync.py:61,235`, `sync_pipeline.py:34`, Tests `test_platform_hacs_preset.py:83`, `test_frontmatter_canonical.py:17`) + 2 Kommentar-Referenzen (`external_tools_drift.py:139,145`) + **kein Kompatibilitäts-Shim möglich** (Name wird vom Package belegt) = Breaking Change für interne/Downstream-Importer | Nicht empfohlen für 4c — nur wenn der User den Pfad wörtlich will; dann als eigener Commit "refactor: rename commands module to command_files" vor der Extraktion |

**Empfehlung:** Option A. Falls Option C gewünscht: Rename zuerst als separater Commit,
danach Extraktion — nie in einem Zug (Byte-Identitäts-Isolation).

### 1.4 Shared State, das Command-Funktionen brauchen (Parametrisierungs-Vertrag)

`_SyncContext` (sync.py:327–350) ist der etablierte Vertrag und **muss mitwandern**:

- `args` (Namespace; `--dry-run` und `--check` sind die einzigen globalen Verhaltens-Flags —
  es gibt **kein quiet-Flag**)
- `log` (SyncLog-Instanz; Reihenfolge der `log.*`-Aufrufe definiert stdout/sync.log — **byte-identisch zu halten**)
- `agent_meta_root`, `project_root`, `config_path` (readonly pro Run)
- `config` (dict; **mutabel mit Write-back**: `_handle_deactivate_providers`/`_handle_activate_providers`
  reloaden Config via `load_config` + `build_variables` und schreiben `ctx.config` zurück; auch `_handle_sync` schreibt den reloadeten Config zurück)
- `variables` (built in `_build_context`), `platforms`, `source_version`, `viz_cfg`
- `mode` (string, Write-back an den Tail für `log.write(...)`)

Zusätzlich brauchen die Handler aus sync.py (müssen mitwandern oder re-exportiert werden):
`_CONFIG_CANDIDATES`, `LOGFILE`, `EXTERNAL_SKILLS_CONFIG` und die validate-Helper
(`resolve_test_repo_path`, `_run_consistency_checks`, `validate_test_repo`).

**Exit-Semantik nicht umbauen:** `_handle_validate` ruft `sys.exit(1/0)` (sync.py:1098, 1101);
`_run_common_tail` exit bei `--check` (1270, 1272) und startet admin via `subprocess.run` —
diese Pfade byte-identisch transportieren, keine Rückgabewerte-Refactorings.

### 1.5 Sync-Logik-Extraktion (bereits erledigt)

`_handle_sync` (sync.py:1107–1164) ist bereits Thin-Orchestrator über `lib/sync_pipeline.py`
(NEU, ungestaged, 582 Zeilen, 12 Stages):
`_sync_stage_config_and_presets` (101) → `_sync_stage_claude_base` (145) →
`_sync_stage_contexts` (184) → `_sync_stage_legacy_cleanup` (225) → `_sync_stage_per_provider` (289,
ruft `sync_agents_for_provider` bei 343) → `_sync_stage_drift_and_plugins` (406) →
`_sync_stage_knowledge_and_isolation` (433) → `_sync_stage_external_skills_check` (452) →
`_sync_stage_gitignore` (477) → `_sync_stage_config_audit` (530).
Stage-6-Akkumulatoren (`mcp_gitignore_extras`, `base_gitignore_entries`) kreuzen Stage-Grenzen **by reference** — beim Move von `_handle_sync` nicht kopieren, weiter delegieren.

---

## 2. Issue #482 — build_variables in scripts/lib/config.py (aktueller Stand)

### 2.1 Position + Umfang

`scripts/lib/config.py` = 1228 Zeilen. `build_variables()` (Z. 1199–1228, **30 Zeilen**, Signatur
`build_variables(config: dict, agent_meta_root: Path, project_root: Path | None = None) -> tuple[dict, list[str]]`)
ist reine Orchestrierung (Issue-Kriterium "<100 Zeilen" ✓ erfüllt, Issue-Restscope = 0).

### 2.2 Block-Liste (8 Sub-Builder statt der 5 aus dem Issue)

| Zeilen | Funktion | Issue-Block-Äquivalent | Umfang |
|---|---|---|---|
| 535–651 | `_build_core_variables(variables, config, agent_meta_root, project_root) -> list[str]` (unmapped) | Base | 117 |
| 652–717 | `_build_provider_variables(variables, config, agent_meta_root) -> None` | Provider | 66 |
| 718–839 | `_build_orch_variables(variables, unmapped, config, agent_meta_root) -> None` | Orchestrator | 122 |
| 840–922 | `_build_platform_variables(variables, unmapped, config, agent_meta_root) -> None` | Base (platform) | 83 |
| 923–970 | `_build_dod_variables(variables, config, agent_meta_root) -> dict` (resolved DoD) | DoD | 48 |
| 971–1076 | `_build_pipeline_variables(variables, unmapped, config, agent_meta_root, dod_resolved) -> dict` (effective) | Pipeline | 106 |
| 1077–1142 | `_build_snippet_variables(variables, agent_meta_root) -> None` | (neu seit #566) | 66 |
| 1143–1197 | `_build_convention_variables(variables, config, agent_meta_root) -> None` (incl. `ISSUE_LANGUAGE`, #579) | (neu seit #566) | 55 |

Orchestrierung in `build_variables()` (Reihenfolge ist kontraktrechtisch):
core → provider → orch → platform → dod → pipeline → `INTENT_ROUTING_TABLE` via
`get_intent_routing_table(..., pipelines=effective)` → snippet → convention → `return variables, unmapped`.
`unmapped` und `dod_resolved` fließen zwischen den Blöcken — ein Issue-Zerlegungs-Schema
(`vars.update(...)` je Block) ist hier bewusst NICHT verwendet (Mutation-Vertrag, siehe
`_build_convention_variables`-Docstring Z. 1146–1166).

### 2.3 Import-Analyse / Zyklen-Risiko

- **Lokale Imports in config.py: nur noch 2, und beide sind optionale-Dependency-Guards**
  (`try: import yaml as _yaml` Z. 43–47, `try: import jsonschema` Z. 49–53) — **absichtlich**
  lazy/optional (Soft-Dependency-Feature-Flags), keine Zyklen. Das Issue-Kriterium
  "All local imports moved to top-level" ist damit **erledigt**; nichts weiter ziehen.
- config.py ist Top-level-Import-Hub für 14 lib-Module: `agents`, `io`, `log`, `variables`
  (Re-Export-Compat #565), `pipelines`, `analysis`, `consistency.placeholders`,
  `context_templates.builder`, `conventions`, `delegation_table`, `dod`, `providers`,
  `reflection`, `roles`.
- **Bekannte agents↔config↔viz-Achse (#478):** aktuell Einbahn — `config → agents → frontmatter`
  (+lazy `roles`); `agents.py` importiert **kein** config (nur frontmatter + lazy roles Z. 82/149).
  `viz.py` hängt an frontmatter/io/log/providers/roles. `provider_transform` importiert viz
  **nicht** top-level; der lazy viz-Import lebt in `agent_sync.py:646`
  (`_finalize_agent_content` → `from .viz import inject_viz_prompt_block`).
- **Guard:** `tests/test_import_acyclicity.py` (Tarjan-SCC über Top-level-Relative-Imports)
  lief aktuell grün (35/35 Tests inkl. build_variables- und agent_sync-Helper-Tests).
- **Empfehlung:** Keine zusätzlichen top-level Imports in #482 nötig — Helfer existieren
  bereits. Für zukünftige Moves gilt: Jede neue top-level-Kante in config.py sofort mit
  `pytest tests/test_import_acyclicity.py` verifizieren; `agents`/`viz`/`commands`-Richtung
  aus config.py heraus meiden (würde die #478-Dissolution rückgängig machen).

---

## 3. Issue #483 — transform/sync (aktueller Stand)

### 3.1 Transformation — `transform_agent_content_for_provider` (provider_transform.py:357–408)

**Signatur (STABIL, 12 Parameter — externe Caller!):**
```python
transform_agent_content_for_provider(content, provider, role, name, description,
    generated_from, config, agent_meta_root, project_root, target_path,
    provider_config, log) -> str
```
- 52 Zeilen (Issue-Kriterium "<50 pure dispatch": ~2 Zeilen drüber — kosmetisch).
- **Dispatch ist seit #629 DATENgetrieben**: kein Python-Dispatch-Dict und kein if/elif mehr;
  pro-Provider-Verhalten kommt aus dem `agent-transform:`-Block in `config/ai-providers.yaml`,
  angewandt von `_apply_agent_transform()` (Z. 151–356, Spec-Engine).
  Fehlt der Spec: Warnung nach sync.log ("add an agent-transform: spec for {provider}") statt
  Silent-Skip (Verhaltensänderung von #629, bewusst).
- Frontmatter-Strip-Felder (#505): `provider-options.<provider>.frontmatter-strip-fields`
  (Projekt) > `frontmatter_strip_fields` (ai-providers.yaml) > `[]`.

**Provider-Pfade (als Python-Helfer, von `_apply_agent_transform`/Specs aufgerufen):**
`_validate_tools_against_whitelist` (28), `wrap_sections_in_xml` (67),
`_make_xml_tag_name` (126), `_reassemble_body` (139), `_map_claude_tools_to_gemini_tools` (445),
`_map_claude_tools_to_opencode_permissions` (463), `_transform_frontmatter_for_opencode` (513),
`_strip_claude_specific_lines` (629), `_make_slim_body` (645), `inject_debug_block` (432),
`build_agent_toml_document` (agent_toml).

### 3.2 Sync — `sync_agents_for_provider` (agent_sync.py:808–858)

**Signatur (STABIL — externe Caller!):**
```python
sync_agents_for_provider(agent_meta_root, project_root, config, variables, log,
    dry_run, provider, provider_config, platform_vars: dict | None = None,
    debug_mode: bool = False) -> None
```
50 Zeilen, pure Orchestrierung (Issue-Kriterium "<60" ✓). Die 5 Issue-Concerns sind als
9 Helper extrahiert (Unit-Tests: `tests/test_agent_sync_helpers.py`, NEU):

1. **Targets auflösen** — `_resolve_sync_targets` (391): pc/role_map/overrides/target_dir
2. **Rollen iterieren** — Loop über `overrides.items()` mit Skip-Gates `_should_skip_role` (444: ROLE_MAP, `config['roles']`, role-enabled, MAIN-CHAT-Orchestrator; Claude-gated log.skip-Messages byte-identisch zum Pre-Split-Monolith)
3. **Content erzeugen/transformieren** — `_compose_role_content` (502) → `_build_provider_vars` (422) → `_apply_content_pipeline` (539; per-Rolle `resolve_dod` + `inject_pipeline_blocks`, V1-Semantik, siehe Review-Iteration MAJOR-1) → `_finalize_agent_content` (586; ruft `transform_agent_content_for_provider` bei Z. 613, debug/viz-Injection)
4. **Schreiben** — `_write_agent_file` (689, `write_checked`)
5. **Aufräumen/Bootstrap** — `_collect_claude_external_skill_filenames` (708, Claude-only) → `_cleanup_stale_agents` (724, ext-aware, Managed-Index-Contract) → `_run_provider_bootstrap` (774)

`_apply_content_pipeline` (539) wurde in der laufenden Phase-4c-Session als V1-Wiederherstellung
(Review-MAJOR-1) gebaut: `resolve_dod` läuft **pro Rolle** (1×/Rolle-stderr-Warnungen,
217 Zeilen wie V1-HEAD) — nicht hoisten.

### 3.3 agents.py heute (Restzweck)

`agents.py` = 176 Zeilen Hint-Builder (`build_knowledge_engine_hints`, `build_agent_hints`,
`build_agent_table`), konsumiert von `config.py:13`. Nicht Teil des #483-Restscopes.

---

## 4. Caller-Map (Öffentliche Signaturen, die sich NICHT ändern dürfen)

### `sync_agents_for_provider` (agent_sync.py:808)
| Caller | Ort | Art |
|---|---|---|
| `lib/sync_pipeline.py:343` | `_sync_stage_per_provider` | Production (mit `platform_vars`/`debug_mode` kwargs) |
| `scripts/sync.py:268` | `validate_test_repo` | Production (--validate) |
| `tests/test_platform_hacs_preset.py` (Z. 624, 704, 753) | 3 Call-Sites | Tests |
| `tests/test_context_compact_mode.py:334` | Compact-Mode | Test |

### `transform_agent_content_for_provider` (provider_transform.py:357)
| Caller | Ort | Art |
|---|---|---|
| `lib/agent_sync.py:613` | `_finalize_agent_content` | Production (Hauptpfad) |
| `lib/skills.py:493–494` | Skill-Wrapper-Agenten | Production (lazy import) |
| `tests/test_provider_toml_transform.py` (71, 135) | 2 Call-Sites | Tests |
| `tests/test_agents_frontmatter.py:164` | | Test |
| `tests/test_model_inherit.py:117` | Continue-Generation | Test |

### `build_variables` (config.py:1199)
| Caller | Ort | Art |
|---|---|---|
| `scripts/sync.py` Z. 63 (Import), 236, 639, 873, 912 | `_build_context`, validate, de/activate-Handler | Production |
| 12 Testdateien | u. a. `test_build_variables_decomposition.py`, `test_knowledge_engine.py`, `test_context_compact_mode.py`, `test_config_variable_fallbacks.py`, `test_native_extensions_whitelist.py`, `test_optional_snippets_path_conditional.py`, `test_issue_language.py`, `test_pipelines.py` (Z. 101, 763), `test_platform_hacs_preset.py` (748), `test_context_user_notes_preserved.py`, `test_conventions_migration_invariant.py`, `test_context_agents_md_idempotency.py` | Tests |

**Vertrag:** `(config, agent_meta_root, project_root=None) -> (variables, unmapped-list)`.
Die 2-Tuple-Rückgabe darf nicht zu 1-Wert werden; `unmapped` fließt in `_build_orch/_build_platform`.

### `lib.commands` (falls Rename erwogen wird)
`sync.py:61` (`create_command`), `sync.py:235` (`sync_commands_for_provider`),
`lib/sync_pipeline.py:34`, Tests: `test_platform_hacs_preset.py:83` (`collect_command_sources`),
`test_frontmatter_canonical.py:17` (`_add_frontmatter_field`); Kommentar-Referenzen:
`external_tools_drift.py:139,145`.

---

## 5. Test-Inventar

### Import-Zyklus-Guard (exakt)
`tests/test_import_acyclicity.py`
- `test_top_level_import_graph_is_acyclic` (Z. 142) — Tarjan-SCC, **der** Guard
- `test_guard_covers_the_lib_tree` (Z. 153) — Sanity: Guard sieht >40 Module
- `test_known_edges_are_resolved` (Z. 164) — Sanity gegen vacuous pass

### sync.py-Abdeckung
`test_sync_check_flag.py` (3: `_normalize_check_dry_run`), `test_sync_test_plugin_cli.py`
(4: `_build_arg_parser`/`_run_test_plugin`), `test_sync_log.py` (3), `test_lifecycle_check_args.py`,
`test_admin_server.py` (92 KB, Admin-Lifecycle). **Kein** vollständiger CLI-Output-Snapshot-Test.

### config.py-Abdeckung
`test_build_variables_decomposition.py` (15 Tests, #566 — Unit-Tests aller 8 `_build_*`-Helfer
+ `test_build_variables_self_hosting_config_is_stable` als Dict-Regression),
`test_config_variable_fallbacks.py`, `test_config_audit.py`, `test_knowledge_engine.py`,
`test_context_compact_mode.py`, `test_native_extensions_whitelist.py`, `test_optional_snippets_path_conditional.py`,
`test_issue_language.py`, `test_pipelines.py`, `test_platform_hacs_preset.py`, `test_context_user_notes_preserved.py`,
`test_conventions_migration_invariant.py`, `test_context_agents_md_idempotency.py`.

### agent_sync/provider_transform-Abdeckung
`test_agent_sync_helpers.py` (NEU, 18 Tests: `_should_skip_role` 11 + `_cleanup_stale_agents` 7,
mit `_LogRecorder`-Byte-Identitäts-Pattern), `test_agents_frontmatter.py`, `test_provider_toml_transform.py`,
`test_model_inherit.py`, `test_frontmatter_canonical.py`, `test_frontmatter_parity.py`,
`test_opencode_agents.py`, `test_antigravity_hooks_registration.py`, `test_pipelines.py:561`
(Call-Site-Wiring: `_apply_content_pipeline` muss `resolve_dod(` enthalten).

### Byte-identische CLI-Output-Verifikation (Lücke + Empfehlung)
Es existiert **kein** automatisierter CLI-Stdout/sync.log-Snapshot-Test. Bestehende Proxy-Signale:
(a) `_LogRecorder`-Fixtures in `test_agent_sync_helpers.py` (skip-Message-Byte-Identität),
(b) `test_build_variables_self_hosting_config_is_stable` (Variables-Dict-Stabilität),
(c) `test_context_agents_md_idempotency.py` (Kontext-Files idempotent).
**Empfehlung für Phase 4c:** Vor/nach-Vergleich manuell + als Goldmaster:
`python scripts/sync.py --dry-run > /tmp/after.txt` auf sauberem Tree vor jedem Move-Schritt;
`diff` gegen Basis-Capture (stdout + `sync.log`-Zeilenfolge). Muster existiert:
`test_substitution_engines_golden.py`. Mindest-Flagmatrix für den Vergleich:
plain sync, `--dry-run`, `--check --dry-run`, `--only-variables --dry-run`,
`--create-rule x --dry-run`, `--create-hook x --dry-run`, `--create-command x --dry-run`,
`--create-ext developer --dry-run`, `--update-ext --dry-run`, `--fill-defaults --dry-run`,
`--audit-config`, `--deactivation-status`, `--list-backups`, `--viz-only --dry-run`,
`--render-standalone --dry-run`, `--validate`.

---

## 6. Risiken

| # | Risiko | Schwere | Mitigation |
|---|---|---|---|
| R1 | **Ungestagede Interdependenz:** `sync.py` importiert `lib.sync_pipeline` hart, aber `sync_pipeline.py` ist untracked (`??`) — ein `git checkout/stash` bricht sync.py | Hoch | Vor weiterer Arbeit Arbeitsstand committen (Feature-Branch) — aber User-Constraint "keine Commits" → als erstes Orchestrator-Delegation erwähnen |
| R2 | Output-Byte-Identität der 17 Handler (log-Sequenz) beim Move nach `lib/cli_commands.py` | Hoch | Reine Module-Moves (kein Umschreiben), Dry-Run-Goldmaster-Matrix aus §5 |
| R3 | `_MODE_HANDLERS`-Prädikatreihenfolge = Flag-Präzedenz (z. B. `--backup` vor `--restore`); Registry-Extraktion darf Reihenfolge nicht ändern | Mittel | Liste 1:1 transportieren; Vergleichstest `_MODE_HANDLERS == expected_list` |
| R4 | sys.exit-Pfade (validate Z. 1098/1101, check Z. 1270/1272) beim Extrahieren umbauen | Mittel | Exits unverändert lassen (kein Return-Code-Refactoring in 4c) |
| R5 | Import-Zyklus bei neuen Modulen: `cli_commands` braucht `config`/`agent_sync`/`sync_pipeline`…; falsche Importrichtung reaktiviert #478 | Mittel | Guard-Test nach jedem Commit; `cli_commands` als Top-Orchestrierungsmodul modellieren (importiert lib-Module, nie umgekehrt) |
| R6 | Doppel-Refactor: Dev liest Issue-Texte (2026-08-11) und implementiert alte Ziele erneut | Hoch | Issue-Reconciliation-Kommentare (§7), Issue-Texte als superseded markieren |
| R7 | provider_transform.py:6–7 Docstring ist stale (besagt lazy viz-Import in `transform_agent_content_for_provider`; lebt real in `agent_sync.py:646`) | Niedrig | 1-Zeilen-Docstring-Fix im #483-Abschluss |
| R8 | `transform_agent_content_for_provider` 52 statt <50 Zeilen — Issue-Acceptance literal nicht erfüllt | Niedrig | Entweder Issue-Text mit Kommentar "superseded by data-driven #629 dispatch" schließen oder 2 Zeilen umstrukturieren (nur wenn kostenfrei) |
| R9 | `sync.py --validate`/--check als CI-Gates: Admin-Subprocess-Aufrufe im Tail dürfen beim Move nicht ihre stderr/stdout-Reihenfolge ändern | Niedrig | Nur Moves, keine printf-Änderungen |
| R10 | Test-Deckungslücke: kein CLI-Snapshot-Test | Mittel | Goldmaster-Matrix einführen (§5) bevor der Handler-Move startet |

---

## 7. Implementierungs-Reihenfolge (empfohlen) + Checklisten

**Vorbemerkung:** Alles auf `feat/issue-674-roadmap` (Branch-Guard); User-Constraint "keine
Commits" beachten — Reihenfolge unten listet Commits als optionale Marker, ausführbar sobald
freigegeben.

### Schritt 0 — Reconciliation & Basis (vor jeder Code-Änderung)
- [ ] GitHub-Issue-Kommentare: #482 "durch #566 umgesetzt, verifiziert am 2026-09-06 (Working Tree)" ; #483 "durch #561/#565/#629 übererfüllt, Rest = docstring fix" ; #481 "Teilumsetzung: main()<50 + Registry-Dispatch + lib/sync_pipeline (Stand 2026-09-06), Rest = Handler-Extraktion"
- [ ] Für alle drei: Issue-Kontext-Baselines prüfen (keine weiteren Open-Subtasks)
- [ ] R1 klären: Commit-Freigabe für ungestageden Stand einholen

### Schritt 1 — #483 abschließen (kleinstes Restscope, risikoarm)
- [ ] Docstring-Fix `provider_transform.py:6–7` (viz lazy import → agent_sync._finalize_agent_content)
- [ ] Entscheiden: Issue-Kriterium "<50 Zeilen" literal erfüllen (2 Zeilen kürzen) ODER via Issue-Kommentar legitimieren (Empfehlung: legitimieren, #629-Dispatch ist datengetrieben und das Kriterium war für das alte elif-Chain-Design geschrieben)
- [ ] Verifikation: `pytest tests/test_provider_toml_transform.py tests/test_agents_frontmatter.py tests/test_model_inherit.py tests/test_agent_sync_helpers.py tests/test_import_acyclicity.py`
- [ ] Issue #483 schließen (`Fixes`-Keyword im nachfolgenden PR/Commit)

### Schritt 2 — #482 abschließen (kein Code, nur Verifikation)
- [ ] `pytest tests/test_build_variables_decomposition.py tests/test_import_acyclicity.py tests/test_config_variable_fallbacks.py` — grün bestätigen
- [ ] Dry-Run-Goldmaster: `python scripts/sync.py --dry-run` output + sync.log-Sequenz unverändert
- [ ] Issue #482 schließen mit Verifikations-Kommentar (Akzeptanzkriterien: build_variables 30<100 Zeilen ✓, Helfer mit Focused-Responsibility ✓, lokale Imports top-level ✓ — ausgenommen bewusste optionale-Dep-Guards yaml/jsonschema, Tests ✓)

### Schritt 3 — #481 Restscope (der eigentliche Code-Aufwand)
- [ ] **3a Goldmaster zuerst** (R10): Basis-Capture der Flagmatrix aus §5 + sync.log erzeugen; als `tests/test_sync_cli_golden.py`-Muster oder als manuelle Referenzdatei ablegen
- [ ] **3b Move 1 — validate-Helper:** `resolve_test_repo_path`, `_run_consistency_checks`, `validate_test_repo` → `lib/cli_commands.py` (3 Module-Moves)
- [ ] **3c Move 2 — CLI-Kern:** `_SyncContext`, `_build_arg_parser`, `_normalize_check_dry_run`, `_run_test_plugin`, `_build_context` (7 Early-Return-Modes) → `lib/cli_commands.py`
- [ ] **3d Move 3 — Handler:** 17 `_handle_*` + `_MODE_HANDLERS` + `_dispatch` + `_run_common_tail` → `lib/cli_commands.py` (Liste 1:1, R3); sync.py-Konstanten (`LOGFILE`, `EXTERNAL_SKILLS_CONFIG`, `EXT_SUFFIX`, `MANAGED_BEGIN/END`, `_CONFIG_CANDIDATES`) mitziehen
- [ ] **3e sync.py schrumpfen:** Import-Sektion reduzieren (viele Imports wandern zu cli_commands), `main()` bleibt Entry-Shell; Re-Exports nur wo Tests sie lesen (`sync_module.sync_knowledge_engine` — siehe Kommentar sync.py:87–89, `# noqa: F401`)
- [ ] **3f Verifikation pro Move:** `pytest tests/test_import_acyclicity.py` + Goldmaster-Diff; erst weiter, wenn byte-identisch
- [ ] **3g Voll-Suite:** `python3 -m pytest tests/ -q` (Erwartung: 1333+ passed, 0 failed — Vorbild: Vorbereitungs-Session) + `python3 scripts/sync.py --validate` (EXIT 0, 3 warnings ok)
- [ ] Issue #481 schließen (Akzeptanzkriterien: build_arg_parser standalone ✓ schon, Commands in cli_commands ✓ jetzt, main <50 ✓ schon, Tests ✓, Verhalten unverändert ✓ via Goldmaster)

### Schritt 4 — Optional (nach User-Entscheidung)
- [ ] Falls `lib/commands/`-Package gewünscht (User-Anweisung wörtlich): separater Rename-Commit `commands.py → command_files.py` VOR Schritt 3b (R6-Kosten aus §1.3 Option C), danach `lib/commands/` für CLI-Schicht. Ohne Rename: `lib/cli_commands.py` (Empfehlung).

---

## 8. Offene Fragen an User/Orchestrator

1. **Ziellayout #481:** Issue-Vorschlag `lib/cli_commands.py` vs. User-Anweisung `lib/commands/` —
   letzteres erfordert Rename des existierenden `lib/commands.py` (kein Shim möglich). Empfehlung:
   `lib/cli_commands.py`. Entscheidung braucht Freigabe (laut §1.3).
2. **Commit-Freigabe:** R1 — ungestagede `sync_pipeline.py` + 9 modifizierte Dateien sichern,
   bevor der #481-Move beginnt (User sagte "keine Commits" — der Status muss aber vor
   weiterer Mutation gesichert werden, sonst Blast-Radius-Inkonsistenz).
3. **#483 "<50 Zeilen"-Kriterium:** literal erfüllen (2 Zeilen umstrukturieren) oder per
   Issue-Kommentar als superseded-by-#629 legitimieren? (Empfehlung: legitimieren.)
