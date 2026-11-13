---
pipeline_stages:
  implement: 2
---

# Phase C / #1086 Teil i: `scripts/lib/context.py` aufteilen (Strangler-Refactoring) Implementation Plan

> Status: DRAFT (Ist-Stand neu gemessen auf `origin/main 9aa0e0c0`, 2026-11-11, per `ast`; Phase-C-Tasks #1182/#1183/#1208/#1086a-e aendern `context.py` vorher erneut, daher Neu-Messung in Task 0 Step 2 Pflicht)
> Klasse: **L** (Refactoring, 3750 Zeilen, 47 Import-Stellen in 33 Dateien unter `scripts/`+`tests/`). Roadmap-Phase **C**, Welle 2, **zuletzt in C**.
> Roadmap: `docs/superpowers/plans/2026-11-10-backlog-roadmap.md` (Entscheidung 6, Risiken-Zeile "#1086i").

## Änderungsprotokoll

Stand 2026-11-13: **Nichts umgesetzt.** Status bleibt **DRAFT**, Task 0 (Spec `docs/specs/2026-11-11-context-split-1086i-spec.md`) liegt nicht freigegeben vor. Verifiziert: `scripts/lib/context_sync/` existiert nicht, `scripts/lib/context.py` hat 3838 Zeilen (Plan-Ist-Stand: 3750 auf 9aa0e0c0; gewachsen durch #1225/#1227, Neu-Messung nach Task 0 Step 2 weiter Pflicht). #1225/#1227/#1230 änderten `context.py` inhaltlich, nicht strukturell. #1086 Teil i bleibt OFFEN: offen, nicht in diesem PR.

**Goal:** `scripts/lib/context.py` (3750 Zeilen auf 9aa0e0c0, Konvention <= 600 laut Issue #1086 (i)) in ein Paket aus Modulen <= 600 Zeilen zerlegen, ohne Verhaltens- und Render-Aenderung. Die Importoberflaeche `lib.context.<name>` bleibt waehrend der ganzen Migration erhalten und wird erst am Ende auf den tatsaechlichen Bedarf reduziert.
**Architecture:** Strangler. Neues Paket `scripts/lib/context_sync/`; je Task wird eine Funktionsgruppe wortgleich verschoben, `context.py` re-exportiert sie. Charakterisierung vorab (Fassaden-Oberflaeche, Funktionskoerper-AST-Hashes, ac01-Render-Hash-Manifest). Keine Funktion wird umgeschrieben, nur Importzeilen aendern sich. Nach jedem Task laeuft die volle Suite gruen.
**Tech Stack:** Python 3.9+ (stdlib, PyYAML-Ausnahme), pytest, `ast` fuer die Koerper-Hashes.
**Spec:** keine, siehe Task 0 Spec-Gate (`docs/specs/2026-11-11-context-split-1086i-spec.md` wird dort angelegt). Keine Implementierungs-Task vor `Status: APPROVED`.

Issue-Abdeckung: #1086 Teil **i** (genau einmal). #1086 a-h liegen in anderen Plaenen/Phasen und sind hier nicht enthalten.

## Abhaengigkeiten / Reihenfolge (Roadmap Abschnitt 3)

| Abhaengigkeit | Phase | Warum |
|---|---|---|
| #1194 (Roadmap-Anker `context.py:1710`; auf 9aa0e0c0 `apply_settings_surface_shape` :1815-1873) | B | muss gemergt sein, sonst Rebase in verschobenen Code |
| #1182 (`build_gate_card` :2329), #1183 (Embedded-Rules-Schleife in `_build_managed_block` :2603, `compact_embedded_rule` :2241), #1208 (Roadmap-Anker `context.py:2147`; `_extract_rule_section` :2300), #1085c (`ensure_gitignore_entries` :3288), #1086a-e (Entscheidung 38c: a-e jetzt in C) | C | andere Phase-C-Tasks (Commits im Phase-C-PR oder im Nachfolge-PR `fix/phase-c-sync-config-gated`, Entscheidungen 17, 52); dieser Plan startet erst nach deren Merge |
| #1086f (`init_claude_personal` :3099) | — | zurueckgestellt (Entscheidung 34 C-N4, 38c); keine Abhaengigkeit, spaeter gegen `context_sync/init_files.py` |
| #1161 (Roadmap-Anker `context.py:204` = `_backup_context_file` :197-212; Punkte 2,4,5) | H | laeuft **nach** diesem Split; muss dann gegen `context_sync/*` rebasen (Phase-H-Plan Zeile 42 verweist auf `context_sync/base.py`). Entscheidung 28: #1161 Punkt 5 (`hook_json_get_many`) betrifft nur Hooks (`hooks/1-generic/*`, H-Plan Abweichung 5 und Files-Liste), nicht `context.py`; Punkt 4 (H-Task 7) nur `sync_pipeline.py`. Entscheidung 29: #1161 Punkt 2 (AGENTS.md-Verzeichnis per Capability-Flag) beruehrt `context_sync/managed_block.py` nur, falls die H-Spec (Task 8) eine Variablenaenderung verlangt; dann nach diesem Split |
| #885 (`consistency/placeholders.py:172` Kommentar-Anker `context.py:1761`; `MCP_GUARDRAILS_LIST` steht auf 9aa0e0c0 in `context.py:2893`/`:3071`, also schon vor dem Split veraltet) | A (Tracker) | nur Kommentar-Anker; Task 14 zieht ihn auf `context_sync/managed_block.py` nach |
| #1142, #1195 | C | `sync_pipeline.py`, nur Importzeile `lib.context` betroffen (Task 12) |
| #1086g | — | Entscheidung 24: ohne Tier-Umbau geschlossen (Ist-Stand dokumentiert, Entscheidungskommentar); **keine Abhaengigkeit** |

**Ausnahme zur Regel "ein Phase = ein PR" (Entscheidung 18; Ausnahmen laut Entscheidungen 36, 52, 53: #1086i, #1209, Nachfolge-PR fuer gesperrte Tasks je Phase (max. 2 PRs je Phase), Phase I mit J-Phasen):** Dieser Split laeuft auf eigenem Branch und eigenem PR und zaehlt nicht zu den 2 Phase-C-PRs. Er folgt direkt nach dem **letzten** Phase-C-PR, d.h. nach dem Nachfolge-PR `fix/phase-c-sync-config-gated`, falls es ihn gibt (Tasks 7/8 des C-Plans aendern `context.py` und laufen dort; **Entscheidung 56**: #1086i ist Nachfolge-PR nach dem letzten Phase-C-PR, loest 18 vs. 52). Er wird von frischem `origin/main` gestartet, nachdem der letzte Phase-C-PR gemergt ist. Innerhalb dieses PR ein Commit je Task. Fuer alle anderen Phasen gilt Entscheidung 17 mit Entscheidung 52. Ein offener Phasen-PR gleichzeitig. **#1086 bleibt nach diesem PR offen** (Entscheidung 46: erst schliessen, wenn Punkt f entschieden oder bewusst verworfen ist); der PR referenziert #1086 nur, kein Schliess-Schritt.

## Global Constraints

- Python 3.9 kompatibel: jedes neue Modul beginnt mit `from __future__ import annotations` (die Quelle nutzt `tuple[str, str | None, str]`-Annotationen); kein `match`, kein `X | Y` zur Laufzeit.
- Nur stdlib + PyYAML (ADR 0001). Provider-agnostisch: nur Config-Keys/Capability-Flags, kein `if provider == "Name"`.
- **Kein Verhaltenswechsel:** Funktionskoerper wortgleich, keine Umbenennung, keine Signaturaenderung, keine neuen Features, kein Bugfix. Gefundene Fehler -> eigenes Issue, nicht in diesem PR.
- Neue Module duerfen `lib.context` (Fassade) **nicht** importieren. Import-DAG laut Task 0; `tests/test_import_acyclicity.py` bleibt gruen.
- Kein Worktree-Isolation-Argument, Commits: Conventional Commits, Englisch, <= 72 Zeichen, eine Aenderung pro Task. Commit-/PR-Texte werden spaeter als Datei bereitgestellt (hier nur Subject-Zeilen).
- Tests: `python3 -m pytest <datei>::<test>`; zusaetzlich `python3 scripts/sync.py --validate`. Nach jedem Task: volle Suite `python3 -m pytest tests -q`.
- Golden-/Hash-Fixtures duerfen **nicht** neu eingefroren werden (siehe "Golden-Fixtures"). Ein roter ac01-Test bedeutet: Task zurueckrollen, nicht Manifest neu schreiben.
- Rollen: Spec -> `concept-specifier` + `concept-reviewer`, Tests -> `tester`, Umsetzung -> `senior-developer`.

## Ist-Stand (gemessen auf `origin/main 9aa0e0c0` per `ast`, `scripts/lib/context.py`, 3750 Zeilen)

Kopf: Zeilen 1-37 Imports (`from .agents`, `.frontmatter`, `.gitignore`, `.io`, `.json_persistence`, `.log`, `.plugins`, `.rule_index`, `.variables`, `.context_templates.builder` :37). Viele Funktionen importieren lazy (`from .providers`, `.rules`, `.mcp`, `.agent_sync`, `.context_profile`, `.context_report` ...; eingerueckte `from .`/`import`-Zeilen: 138, 359, 481, 515-517, 600-601, 624-625, 824-825, 1164-1165, 1275, 1458, 1779, 1885, 1953, 1972, 1980, 1989-1990, 2285, 2343, 2429, 2472-2474, 2480, 2560-2561, 2616-2617, 2629, 2678, 2693, 2699, 2742, 2790, 2827-2828, 2890, 2983, 3011, 3064, 3209, 3533, 3566-3567, 3574-3576, 3625, 3698).

Modul-Konstanten: `SNIPPETS_DIR` 39, `_CONTEXT_HASHES_FILE/_DIR` 43-44, `_MANAGED_BLOCK_RE` 47, `USER_NOTES_HEADING` 144, `_UNRESOLVED_PLACEHOLDER_RE` 1236, `_ADAPTER_MANAGED_INDEX` 1405, `_CONTINUE_MANAGED_BEGIN/END` 2031-2032, `_COMPACT_PLATFORM_RULES` 2132, `_GATE_CARD_HEADING_RE` 2276, `CLAUDE_LOCAL_FILE`/`CLAUDE_PERSONAL_LEGACY_FILE` 3095-3096.

### Modul-Schnitt (Zeilen = `def`-Start bis `end_lineno` auf 9aa0e0c0; Kommentare/Dekoratoren davor gehoeren mit)

Zielpaket `scripts/lib/context_sync/` (`__init__.py` leer). Zuordnung per Aufrufgraph (Namensreferenzen je top-level `def`, Skript `.tmp/c1086i/graph3.py` im Plan-Worktree) **zyklenfrei** geprueft; "ca. Zeilen" = Summe der Funktions-/Konstantenzeilen ohne Kopf und Leerzeilen (Plan-Wert, Kopf ~+40).

| Schicht | Modul | Inhalt (Ist-Zeilen 9aa0e0c0) | ca. Zeilen | haengt ab von |
|---|---|---|---|---|
| L0 | `base.py` | Konstanten 43-47, 144; `_has_duplicate_managed_block` 53, `_context_hashes_path` 64, `_load_context_hashes` 68, `_save_context_hashes` 80, `_record_static_hash` 92, `_split_context_file` 101, `_split_injected_footer_tail` 117, `_normalize_static_sig` 136, `_user_notes_span` 147, `_strip_user_notes` 171, `_preserve_user_notes` 179, `_backup_context_file` 197-212; `_has_capability` 332; `_core_context_filename` 412; `_adapter_reference_line` 427, `_inject_adapter_line` 452-464; `_shared_context_users` 2405-2437; `_shared_topology_flags` 2526-2600; `_project_name` 1732-1738 | ~310 | — |
| L0 | `reader.py` | `_context_hard_cap_readers` 467, `enforce_context_hard_cap` 499, `_write_reader_context` 556, `_write_dispatch_depth` 591-606 | ~135 | — |
| L0 | `settings.py` | `apply_settings_surface_shape` 1815, `_project_config_for_init` 1876, `_init_provider_settings_json` 1899-2028, `init_settings_json` 3173, `init_settings_local_json` 3231, `_settings_local_fallback` 3280-3285 | ~320 | — |
| L0 | `init_files.py` | `CLAUDE_*_FILE` 3095-3096, `init_claude_personal` 3099, `init_opencode_personal` 3141, `ensure_gitignore_entries` 3288-3383 | ~170 | — |
| L1 | `static.py` | `_regenerate_static_context` 215, `_apply_platform_context_substitution` 337, `_ensure_context_file` 368, `sync_claude_md_static` 3386, `only_variables` 3438-3534 | ~330 | base, reader |
| L1 | `adapters.py` | `_shares_context_with_embedded_rules` 1378, `_adapter_index_path` 1408, `_record_adapter_managed` 1413, `_record_adapter_hash` 1430, `_expected_adapter_files` 1449, `rollback_context_adapters` 1475, `_adapter_settings_activation` 1572, `_write_adapter_settings_activation` 1611-1658, Konstante 1405 | ~220 | base |
| L1 | `compact.py` | `_extract_rule_compact_from_content` 2084, `_split_compact_rule` 2220, `compact_embedded_rule` 2241, `_load_gate_card_sections` 2279, `_extract_rule_section` 2300, `build_gate_card` 2329, `_enforce_compact_hard_cap` 2376, `sync_compact_reference_skills` 2440-2523, Konstanten 2132, 2276 | ~380 | base, reader |
| L1 | `prompts_snippets.py` | `SNIPPETS_DIR` 39 (einziger Nutzer `sync_snippets_for_provider` :3707), `sync_prompts_for_continue` 3537, `sync_snippets_for_provider` 3683-3750 | ~215 | base |
| L2 | `managed_html.py` | `_managed_notes_as_html_comment` 609, `_update_managed_html_block` 648, `_insert_managed_block_above_foreign_content` 783, `_position_aware_agent_hints` 799, `_sync_managed_block_context` 899-994 | ~380 | base, reader, settings, static |
| L2 | `managed_block.py` | `_build_managed_block` 2603-3091 (489 Zeilen) | ~490 | base, compact, static |
| L3 | `provider_sync.py` | `_sync_opencode_context` 997, `_cleanup_bootstrap_block` 1145, `omit_unresolved_placeholder_lines` 1239, `_sync_continue_context` 1261, `_update_continue_config_managed_block` 2035-2081, Konstanten 1236, 2031-2032 | ~415 | base, reader, settings, init_files, static, managed_html, managed_block |
| bleibt | `context.py` | `_dispatch_context_strategy` 1523, `sync_context_adapters_for_provider` 1661, `_apply_context_filename_settings` 1712, `sync_context_for_provider` 1741-1812 + Re-Exports | ~190 | alle |

Abweichungen zur naiven Positions-Gruppierung (alle per Graph belegt, in Task 0 zu bestaetigen):
- `_project_name` -> `base`: Aufrufer `_ensure_context_file` (static), `_sync_opencode_context` (provider_sync), `sync_prompts_for_continue` (prompts_snippets); in `context.py` belassen ergaebe Zyklen `static -> context -> ...`.
- `_dispatch_context_strategy` und `sync_context_adapters_for_provider` bleiben in `context.py`: der Dispatcher ruft `_sync_managed_block_context`, `_sync_opencode_context`, `_sync_continue_context` (Zeilen 1549-1563); in `adapters.py` ergaebe er den Zyklus `adapters -> managed_html -> adapters`.
- `_adapter_reference_line`/`_inject_adapter_line` -> `base`: `_update_managed_html_block` ruft `_inject_adapter_line`.
- `_shared_context_users` -> `base`: Aufrufer `_managed_notes_as_html_comment` :629, `_position_aware_agent_hints` :832, `sync_compact_reference_skills` :2486, `_build_managed_block` :2640. `_has_capability` -> `base`: Aufrufer `_dispatch_context_strategy` :1549-1563.
- `_shared_topology_flags` (75 Zeilen, nur Aufrufer `_build_managed_block` :2721, keine internen Abhaengigkeiten) -> `base`, damit `managed_block.py` Luft unter 600 behaelt.
- `settings.py`/`init_files.py` sind L0 (keine internen Abhaengigkeiten) und muessen **vor** `managed_html.py` und `provider_sync.py` verschoben werden (siehe Ausfuehrungsreihenfolge).
- **Budget-Risiko `managed_block.py`:** `_build_managed_block` hat auf 9aa0e0c0 489 Zeilen; #1183 (Phase C) aendert genau diese Funktion. Waechst sie ueber ~555 Zeilen, ist AK2 (<= 600) ohne Teilung nicht erreichbar -> Task 0 misst neu; dann User-Entscheidung (siehe "Offene Entscheidungen").

### Aufrufer (gegrept auf 9aa0e0c0: `git grep "lib\.context import\|from \.context import\|import lib\.context as" -- scripts tests` = 47 Stellen in 33 Dateien)

Produktion (`scripts/`):
- `scripts/lib/sync_pipeline.py:49-60` (top-level): `ensure_gitignore_entries`, `init_claude_personal`, `init_settings_json`, `init_settings_local_json`, `omit_unresolved_placeholder_lines`, `rollback_context_adapters`, `sync_claude_md_static`, `sync_context_for_provider`, `sync_prompts_for_continue`, `sync_snippets_for_provider`
- `scripts/lib/cli_commands.py:46` (top-level): `only_variables`; `:236` (lazy): `sync_context_for_provider`, `sync_snippets_for_provider`
- `scripts/lib/extensions.py:82` (lazy, relativ): `omit_unresolved_placeholder_lines`
- `scripts/lib/agent_sync.py:1498` (lazy, relativ): `enforce_context_hard_cap`
- Gegenrichtung (lazy, kein Import-Zeit-Zyklus): `context.py:3566` (`from .agent_sync import compose_agent`, lazy in `sync_prompts_for_continue`), `agent_sync.py:1498` importiert `.context`.
- Nur Text/Kommentar, kein Import: `scripts/lib/config_audit_providers.py:78` (Pfad-String `scripts/lib/context.py`, siehe Abweichung 2), `scripts/lib/consistency/placeholders.py:172`, `scripts/lib/consistency/context_topology.py:21,40,66`, `scripts/lib/consistency/context_size.py:26,28`, `scripts/lib/rules.py:377,509`, `scripts/lib/gitignore.py:34-35`, `scripts/lib/generated_file_drift.py:7,58,471`, `scripts/lib/harnesses.py:12`, `scripts/lib/variables.py:5`, `scripts/lib/config.py:2028,2046,2083`, `scripts/lib/external_tools_drift.py:360`; Doku `docs/CODEBASE_OVERVIEW.md:1506` (Abschnitt 10.7 `scripts/lib/context.py`).
- `scratch/modify_context.py:70`: kein Import (textuelles Skript), ignorieren.
- Hooks/Shell/CI/Config (`*.sh`, `*.yml`, `*.yaml`, `*.json`, `hooks/`, `.github/`): **keine** Treffer auf `lib.context` / `context.py` ausser den Textstellen oben.

Tests (`from lib.context import ...`, Datei:Zeile -> Namen):
- `tests/test_dispatch_depth_and_hard_cap.py:69` `_regenerate_static_context`
- `tests/test_check_ignored_absent.py:30` `_init_provider_settings_json`, `_sync_continue_context`, `init_claude_personal`, `init_opencode_personal`, `init_settings_local_json`
- `tests/test_context_user_notes_preserved.py:47` `sync_claude_md_static`; `:103` `sync_context_for_provider`
- `tests/test_context_agents_md_idempotency.py:47,99,132,166` `sync_context_for_provider`
- `tests/test_settings_depth_and_deny.py:44` `_init_provider_settings_json`, `apply_settings_surface_shape`, `init_settings_json`
- `tests/test_agents_md_shared_context_convergence.py:87,119` `_build_managed_block`; `:152` `sync_context_for_provider`
- `tests/test_context_compact_mode.py:415,670,757` `sync_context_for_provider`
- `tests/test_orchestrator_topology_entrypoint.py:31` `_init_provider_settings_json`
- `tests/test_bootstrap_submarkers.py:32` `_cleanup_bootstrap_block`, `_update_continue_config_managed_block`
- `tests/test_gate_card_compact.py:71` `_build_managed_block`, `_update_managed_html_block`, `build_gate_card`; `:224` `import lib.context as context` + `monkeypatch.setattr(context, "_load_gate_card_sections", ...)` (`:226-228`, Test `test_missing_gate_card_section_raises` :220); `:249` `_shared_context_users`
- `tests/test_context_profile_shared_file.py:42` `import lib.context as context` + `monkeypatch.setattr(context, "TemplateBuilder", _Recorder)` (`:55`); `:60` `_build_managed_block`
- `tests/test_context_file_modes.py:22` `_build_managed_block`; `:560` `sync_context_for_provider`
- `tests/test_opencode_main_chat_entry_point.py:32`, `tests/test_opencode_v2_surface.py:65` `apply_settings_surface_shape`
- `tests/test_context_filename_settings.py:28` `_adapter_settings_activation`
- `tests/test_gitignore_keep.py:29`, `tests/test_gitignore_shadowing.py:12`, `tests/test_gitignore_platform_defaults.py:17` `ensure_gitignore_entries`
- `tests/test_context_platform_substitution_834.py:30` `_apply_platform_context_substitution`, `sync_context_for_provider`
- `tests/test_only_variables_updates_context_806.py:33` `_MANAGED_BLOCK_RE`, `_split_context_file`, `only_variables`
- `tests/test_compact_rule_channels.py:40` `_COMPACT_PLATFORM_RULES`, `_build_managed_block`, `_split_compact_rule`, `compact_embedded_rule`, `sync_context_for_provider`
- `tests/test_context_managed_block_shrink.py:26` `_MANAGED_BLOCK_RE`, `_has_duplicate_managed_block`, `_split_context_file`, `_update_managed_html_block`, `only_variables`
- `tests/test_snippet_copy_contract.py:36` (`scripts.lib.context`) `sync_snippets_for_provider`
- `tests/test_context_adapters.py:41` `_adapter_reference_line`, `enforce_context_hard_cap`, `rollback_context_adapters`, `sync_context_adapters_for_provider`, `sync_context_for_provider`; `:702` `_adapter_settings_activation`, `_write_adapter_settings_activation`
- `tests/test_embed_rules_channel.py:30` `_build_managed_block`
- `tests/test_continue_rule_frontmatter.py:27` `sync_context_for_provider`
- `tests/test_context_prompt_index.py:26` `sync_prompts_for_continue`
- `tests/test_entry_hint_topology.py:32` `_position_aware_agent_hints`
- `tests/test_orchestrator_topology_render_parity.py:47` (`scripts.lib.context`) `_build_managed_block`
- Quelltext-Scan-Tests (lesen `scripts/lib/context.py` als Text/AST, **kein** Import; brechen oder werden leer, sobald der gescannte Code umzieht):
  - `tests/test_compact_rule_channels.py:165-166` `test_classification_stays_provider_agnostic`: `source.split("_COMPACT_PLATFORM_RULES = {", 1)[1]` -> IndexError nach Task 6 (Konstante in `compact.py`).
  - `tests/test_capability_keys_ic09.py:141-143` `test_roster_in_harness_consumers_are_key_driven`: `"roster_in_harness" in source` von `context.py` (Treffer :2765-2783 in `_build_managed_block`) -> rot nach Task 8.
  - `tests/test_context_prompt_index.py:179-184` `test_prompt_fail_open_clause_gone`: `bootstrap_previously_managed`/`write_managed_index` im Text von `context.py` (Import :25-27, Aufrufe :1424-1509, :3666) -> rot, sobald Task 14 ungenutzte Importe entfernt; vorher nur noch ueber die Importzeile gruen (Pin wird hohl).
  - `tests/test_provider_agnostic_dispatch.py:314-317` `_LEGACY_PROVIDER_DEFAULT_SITES` mit `("context.py", "_update_managed_html_block")`, `("context.py", "_extract_rule_compact_from_content")`; Schluessel = `Path(module).name` (:347) -> rot nach Task 6/Task 7. Kommentar :309-312: Allowlist "only ratchets DOWN -- never add". Umschluesseln auf `compact.py`/`managed_html.py` ist Umbenennung, kein Hinzufuegen; die Spec (Task 0) muss das ausdruecklich festhalten.
  - `tests/test_orchestrator_topology_effective_flags.py:53-61` `_RENDER_SEAMS` enthaelt `"context.py"`; Per-Seam-Pin (:314-322) gilt danach nicht mehr fuer `context_sync/*` (bleibt gruen, wird schwaecher). Der globale Pin (nur `config.py` ruft `_effective_topology_flags`, :300-311) deckt die neuen Module weiter ab.
  - `tests/test_provider_agnostic_dispatch.py:407` erwartet `"context.py"` im Lib-Sweep; bleibt gruen, solange `context.py` existiert. Der Sweep ist rekursiv (`_lib_modules` :61), `context_sync/*` wird automatisch erfasst.
- Kein Bezug (Namensaehnlich, anderes Modul): `lib.context_profile`, `lib.context_report`, `lib.context_profile_gate`, `lib.context_templates.builder`.

### Golden-Fixtures / Render-Pins

- `tests/test_ac01_render_identity.py` + `tests/fixtures/ac01-baseline/hashes.json`: SHA-256 jeder generierten Datei je Provider-Matrix-Projekt. **Das ist der Render-Pin.** Der Split darf kein Byte aendern; `--write` (Neu-Einfrieren) ist nur bei dokumentiertem Rebaseline-Grund auf sauberem `main` erlaubt und hier **verboten**. Rot = Task zurueck.
- `tests/test_substitution_engines_golden.py`, `tests/fixtures/slimming-golden/*`, `tests/fixtures/topology-golden/*`, `tests/test_template_slimming_equivalence.py`: betreffen `TemplateBuilder`/Agent-Templates, nicht `context.py`; laufen trotzdem in der vollen Suite mit.
- Neu (Task 1): `tests/fixtures/context-split/function_ast_hashes.json` (Koerper-Hashes) und `tests/fixtures/context-split/public_surface.json`. Diese werden **einmalig vor dem Split** aus dem Ist-Stand erzeugt und danach nicht mehr veraendert; nur Task 14 darf `public_surface.json` auf die dann gueltige Fassade reduzieren (dokumentiert, nicht neu eingefroren).

## File Structure

- Create: `docs/specs/2026-11-11-context-split-1086i-spec.md` — Spec (Task 0).
- Create: `tests/test_context_split_characterization.py` — Fassaden-Oberflaeche, Identitaet, AST-Hashes, Groessen-Budget.
- Create: `tests/fixtures/context-split/function_ast_hashes.json`, `tests/fixtures/context-split/public_surface.json`.
- Create: `scripts/lib/context_sync/__init__.py`, `base.py`, `reader.py`, `static.py`, `adapters.py`, `compact.py`, `managed_html.py`, `managed_block.py`, `provider_sync.py`, `settings.py`, `init_files.py`, `prompts_snippets.py`.
- Modify: `scripts/lib/context.py` — schrumpft auf Entry-Funktionen + Re-Exports.
- Modify: `tests/test_gate_card_compact.py` (Zeile 224-228), `tests/test_context_profile_shared_file.py` (Zeile 42-55) — Patch-Ziel auf neues Modul (Tasks 6/8).
- Modify: Quelltext-Scan-Tests (nur Pfad/Schluessel, Assertion-Inhalt identisch): `tests/test_compact_rule_channels.py:165` (Task 6), `tests/test_provider_agnostic_dispatch.py:316-317` (Tasks 6/7), `tests/test_capability_keys_ic09.py:141` (Task 8), `tests/test_context_prompt_index.py:181` (Task 14).
- Modify (Task 12): `scripts/lib/sync_pipeline.py`, `scripts/lib/cli_commands.py`, `scripts/lib/extensions.py`, `scripts/lib/agent_sync.py` — Importziele.
- Modify (Task 13): die oben gelisteten Test-Dateien — Importziele (mechanisch).
- Modify (Task 14): `docs/CODEBASE_OVERVIEW.md` (Abschnitt 10.7 `scripts/lib/context.py`, :1506) — Verweis auf `context_sync/`; `scripts/lib/consistency/placeholders.py:172` (Kommentar-Anker, #885). Die frueher genannte Architektur-Datei in der `docs/`-Wurzel existiert auf 9aa0e0c0 nicht; `docs/architecture/01-07*.md` enthalten keinen `context.py`-Treffer.

---

### Task 0: Spec schreiben + Freigabe-Gate

**Agent:** `concept-specifier`, Review `concept-reviewer`, Freigabe durch User. **Files:** Create `docs/specs/2026-11-11-context-split-1086i-spec.md`. **Interfaces:** Produces: Spec mit `Status: APPROVED`; Consumes: dieser Plan, `docs/specs/2026-10-11-context-profiles-spec.md` (AC-01 Render-Identitaet).
- [ ] Step 1: Spec mit Modulschnitt (Tabelle oben), Aufrufgraph-Schichten, Fassaden-Strategie, Patch-Ziel-Migration, Nicht-Ziele, Akzeptanzkriterien (AK1 ac01 unveraendert, AK2 alle Module <= 600 Zeilen, AK3 Fassaden-Namen identisch, AK4 Import-DAG, AK5 Py3.9) schreiben.
- [ ] Step 2: Ist-Stand nach Merge des letzten Phase-C-PR neu messen (Zeilen, `def`-Enden, `_build_managed_block`-Laenge) und Aufrufgraph per `ast` ermitteln (Vorlage `.tmp/c1086i/graph3.py` im Plan-Worktree, nicht committen); Erwartung: 0 Zyklen zwischen den Zielmodulen. Abweichungen in die Spec.
- [ ] Step 2b: In der Spec festhalten: Umschluesseln von `_LEGACY_PROVIDER_DEFAULT_SITES` (`tests/test_provider_agnostic_dispatch.py:314-317`) von `context.py` auf `compact.py`/`managed_html.py` ist Umbenennung, kein neuer Eintrag; Quelltext-Scan-Tests (Liste unter "Aufrufer") zeigen nach dem Move auf das neue Modul, Assertion-Inhalt bleibt.
- [ ] Step 2c: Paketname `context_sync` (Alternative: `context.py` -> Paket `context/`) und Schichtung in der Spec festlegen; Entscheidung faellt mit der Spec-Freigabe in Step 3.
- [ ] Step 3: Review, User-Freigabe `Status: APPROVED`.
- **Akzeptanz:** Spec-Datei enthaelt die Zeile `Status: APPROVED`; `python3 scripts/sync.py --validate` meldet keinen neuen Fehler. Ohne diese Zeile ist keine Task >= 1 ausfuehrbar.
- Commit: `docs: add spec for context.py split (#1086i)`

### Task 1: Charakterisierungs-Tests (kein Produktionscode)

**Agent:** `tester`. **Depends on:** 0. **Files:** Create `tests/test_context_split_characterization.py`, `tests/fixtures/context-split/function_ast_hashes.json`, `tests/fixtures/context-split/public_surface.json`. **Interfaces:** Consumes: `lib.context` (Ist-Stand); Produces: Pin fuer alle Folge-Tasks.
- [ ] Step 1: Tests schreiben (muessen auf unveraendertem `context.py` **gruen** sein, da sie den Ist-Stand pinnen; "fail first" entfaellt bewusst, stattdessen Negativprobe in Step 3):
  - `test_public_surface_unchanged`: laedt `public_surface.json` (alle Namen aus der Aufrufer-Liste oben, plus alle top-level `def`/Konstanten des Ist-Stands, plus `TemplateBuilder`) und assertet `hasattr(lib.context, name)` je Name.
  - `test_function_bodies_unchanged`: berechnet je top-level `FunctionDef`/`Assign` in `lib/context.py` **und** `lib/context_sync/*.py` den Hash `sha256(ast.dump(node_ohne_ImportFrom.level))` und vergleicht mit `function_ast_hashes.json`; jeder Name muss in genau einem Modul vorkommen.
  - `test_context_modules_within_budget`: jedes `scripts/lib/context_sync/*.py` <= 600 Zeilen und `context.py` <= 600 (vor dem Split mit `xfail(strict=False)` fuer `context.py`, ab Task 14 hart).
  - `test_moved_names_are_identical_objects`: fuer jedes Paar (Name, Modul) aus `public_surface.json` gilt `getattr(lib.context, n) is getattr(importlib.import_module(modul), n)` (ab Task 2 mit je Task wachsender Map; vorher Map leer).
  - `test_lazy_imports_resolve`: fuer jedes funktionslokale `ImportFrom` in `scripts/lib/context.py` und `scripts/lib/context_sync/*.py` den Modulnamen per `importlib.util.resolve_name` aufloesen, `importlib.import_module` und `hasattr` je importiertem Namen pruefen (faengt falsche `.x`/`..x`-Ebenen, die der AST-Hash wegnormalisiert).
  - Erzeugung der Fixtures: `python3 tests/test_context_split_characterization.py --write` (nur in Task 1, danach verboten).
- [ ] Step 2: `python3 -m pytest tests/test_context_split_characterization.py -q` -> Erwartung: alle gruen (Budget-Test xfail).
- [ ] Step 3: Negativprobe (nicht committen): einen Funktionskoerper in einer Kopie aendern -> `test_function_bodies_unchanged` rot.
- [ ] Step 3b: Patch-Stellen erneut suchen: `git grep -nE "setattr\((context|ctx)\b|['\"](scripts\.)?lib\.context\." -- tests` -> Erwartung (9aa0e0c0): nur `tests/test_context_profile_shared_file.py:55` direkt, plus `tests/test_gate_card_compact.py:226-228` (mehrzeiliger `setattr`); Quelltext-Scan-Tests: `git grep -n '"context.py"' -- tests` -> Erwartung: die 5 Dateien der Liste oben.
- [ ] Step 4: Basislauf `python3 -m pytest tests/test_ac01_render_identity.py tests/test_import_acyclicity.py tests/test_provider_matrix_sync.py -q` und volle Suite gruen; Ergebnis als Ausgangslage in der Task-Notiz festhalten.
- **Akzeptanz:** neue Datei gruen; vollstaendige Suite vor dem Split gruen (sonst Stopp, Ursache klaeren, nicht weitermachen).
- Commit: `test: pin context.py surface and function bodies before split`

### Task 2: `context_sync/base.py` (L0) anlegen

**Agent:** `senior-developer`. **Depends on:** 1. **Files:** Create `scripts/lib/context_sync/__init__.py`, `scripts/lib/context_sync/base.py`; Modify `scripts/lib/context.py`, `tests/test_context_split_characterization.py` (Map). **Interfaces:** Produces: `base` mit den `base.py`-Namen der Tabelle (inkl. `_project_name`, `_adapter_reference_line`, `_inject_adapter_line`, `_shared_context_users`, `_shared_topology_flags`, `_has_capability`, `_core_context_filename`); Consumes: nur Fremdmodule ueber `..` (z.B. `..io`), keine anderen `context_sync`-Module.
- [ ] Step 1: In `test_moved_names_are_identical_objects` die L0-Namen mit Modul `lib.context_sync.base` eintragen -> rot (Modul fehlt).
- [ ] Step 2: Funktionen/Konstanten wortgleich nach `base.py` verschieben; lazy Importe `from .x` -> `from ..x`; in `context.py` `from .context_sync.base import (...)  # noqa: F401` (alle Namen, auch private).
- [ ] Step 3: `python3 -m pytest tests/test_context_split_characterization.py tests/test_import_acyclicity.py tests/test_context_managed_block_shrink.py tests/test_only_variables_updates_context_806.py tests/test_gate_card_compact.py -q` -> gruen; dann volle Suite + `tests/test_ac01_render_identity.py` gruen.
- [ ] Step 4: Commit.
- **Akzeptanz:** `base.py` <= 600 Zeilen; `grep -c "from .context import\|from lib.context import" scripts/lib/context_sync/base.py` = 0; AST-Hash-Test gruen; ac01 unveraendert.
- Commit: `refactor: extract context base helpers into context_sync`

### Task 3: `reader.py` (L0)

**Agent:** `senior-developer`. **Depends on:** 2. **Files:** Create `scripts/lib/context_sync/reader.py`; Modify `scripts/lib/context.py`, Characterization-Map. **Interfaces:** Produces `enforce_context_hard_cap`, `_write_reader_context`, `_write_dispatch_depth`, `_context_hard_cap_readers`; Consumes keine `context_sync`-Module (Graph: keine internen Abhaengigkeiten).
- [ ] Step 1: Map-Eintraege (rot). Step 2: verschieben, Re-Export. Step 3: `python3 -m pytest tests/test_dispatch_depth_and_hard_cap.py tests/test_context_adapters.py tests/test_context_split_characterization.py -q`, volle Suite, ac01 -> gruen. Step 4: Commit.
- **Akzeptanz:** wie Task 2; zusaetzlich `agent_sync.py:1498` (`from .context import enforce_context_hard_cap`) laeuft weiter ueber die Fassade (Test `tests/test_dispatch_depth_and_hard_cap.py` gruen).
- Commit: `refactor: extract reader context hard cap into context_sync`

### Task 4: `static.py` (L1)

**Agent:** `senior-developer`. **Depends on:** 3. **Files:** Create `scripts/lib/context_sync/static.py`; Modify `context.py`, Map. **Interfaces:** Produces `_regenerate_static_context`, `_apply_platform_context_substitution`, `_ensure_context_file`, `sync_claude_md_static`, `only_variables`; Consumes `base`, `reader`.
- [ ] Steps wie Task 3. Tests: `tests/test_context_user_notes_preserved.py tests/test_context_platform_substitution_834.py tests/test_only_variables_updates_context_806.py tests/test_dispatch_depth_and_hard_cap.py`.
- **Akzeptanz:** wie Task 2; `cli_commands.py:46` (`only_variables`) unveraendert gruen.
- Commit: `refactor: extract static context sync into context_sync`

### Task 5: `adapters.py` (L1)

**Agent:** `senior-developer`. **Depends on:** 4. **Files:** Create `scripts/lib/context_sync/adapters.py`; Modify `context.py`, Map. **Interfaces:** Produces Adapter-Gruppe laut Tabelle (ohne `_dispatch_context_strategy`/`sync_context_adapters_for_provider`, die in `context.py` bleiben); Consumes `base`.
- Steps wie Task 3. Tests: `tests/test_context_adapters.py tests/test_context_filename_settings.py tests/test_context_prompt_index.py`.
- **Akzeptanz:** wie Task 2; Rollback-Pfad `rollback_context_adapters` (`sync_pipeline.py:55`) weiter gruen.
- Commit: `refactor: extract context adapters into context_sync`

### Task 6: `compact.py` (L1) inkl. Patch-Ziel-Migration

**Agent:** `senior-developer`. **Depends on:** 5. **Files:** Create `scripts/lib/context_sync/compact.py`; Modify `context.py`, `tests/test_gate_card_compact.py` (Zeile 224-228), `tests/test_compact_rule_channels.py` (:165), `tests/test_provider_agnostic_dispatch.py` (:317), Map. **Interfaces:** Produces `compact_embedded_rule`, `build_gate_card`, `_load_gate_card_sections`, `_split_compact_rule`, `_COMPACT_PLATFORM_RULES`, `sync_compact_reference_skills`, ...; Consumes `base`, `reader`.
- [ ] Step 1: `test_missing_gate_card_section_raises` bleibt unveraendert -> nach dem Verschieben rot erwartet (Patch trifft nur die Fassade, `build_gate_card` loest `_load_gate_card_sections` im neuen Modul auf). Das ist der erwartete Rot-Test.
- [ ] Step 2: verschieben + Re-Export; im Test `import lib.context as context` durch `import lib.context_sync.compact as context` ersetzen (nur Importzeile, Assertion identisch). Scan-Tests: `test_compact_rule_channels.py:165` liest `scripts/lib/context_sync/compact.py`; Allowlist-Eintrag `("context.py", "_extract_rule_compact_from_content")` -> `("compact.py", ...)`.
- [ ] Step 3: `python3 -m pytest tests/test_gate_card_compact.py tests/test_compact_rule_channels.py tests/test_provider_agnostic_dispatch.py tests/test_orchestrator_compact_sections.py tests/test_escalate_card_contract.py -q`, volle Suite, ac01 -> gruen.
- **Akzeptanz:** `python3 -m pytest tests/test_gate_card_compact.py::test_missing_gate_card_section_raises -q` gruen; Diff in den Testdateien besteht nur aus Importzeile, Dateipfad bzw. Allowlist-Schluessel.
- Commit: `refactor: extract compact rules and gate card into context_sync`

### Task 7: `managed_html.py` (L2)

**Agent:** `senior-developer`. **Depends on:** 10 (Ausfuehrungsreihenfolge siehe Task 10). **Files:** Create `scripts/lib/context_sync/managed_html.py`; Modify `context.py`, `tests/test_provider_agnostic_dispatch.py` (:316), Map. **Interfaces:** Produces `_update_managed_html_block`, `_sync_managed_block_context`, `_position_aware_agent_hints`, `_insert_managed_block_above_foreign_content`, `_managed_notes_as_html_comment`; Consumes `base`, `reader`, `settings` (`_init_provider_settings_json`, Aufruf :991), `static` (`_ensure_context_file` :966, `_regenerate_static_context`, `_apply_platform_context_substitution`), `TemplateBuilder` (Ist-Zeile 704).
- Steps wie Task 3; Allowlist-Eintrag `("context.py", "_update_managed_html_block")` -> `("managed_html.py", ...)`. Tests: `tests/test_context_managed_block_shrink.py tests/test_gate_card_compact.py tests/test_context_file_modes.py tests/test_entry_hint_topology.py tests/test_provider_agnostic_dispatch.py`.
- **Akzeptanz:** wie Task 2.
- Commit: `refactor: extract managed html block sync into context_sync`

### Task 8: `managed_block.py` (L2) inkl. Patch-Ziel-Migration

**Agent:** `senior-developer`. **Depends on:** 7. **Files:** Create `scripts/lib/context_sync/managed_block.py`; Modify `context.py`, `tests/test_context_profile_shared_file.py` (Zeile 42-55), `tests/test_capability_keys_ic09.py` (:141), Map. **Interfaces:** Produces `_build_managed_block`; Consumes `base` (`_shared_context_users`, `_core_context_filename`, `_shared_topology_flags`), `compact` (`build_gate_card`, `compact_embedded_rule`, `_split_compact_rule`, `_enforce_compact_hard_cap`, `_COMPACT_PLATFORM_RULES`), `static` (`_apply_platform_context_substitution`), `TemplateBuilder`.
- [ ] Step 1: Fixture `captured` bleibt unveraendert -> nach dem Verschieben rot (Recorder auf Fassade wirkungslos). Step 2: verschieben; in der Fixture `import lib.context as context` -> `import lib.context_sync.managed_block as context`; in `test_capability_keys_ic09.py:141` die Modulliste `("config.py", "context.py")` -> `("config.py", "context_sync/managed_block.py")`. Step 3: `python3 -m pytest tests/test_context_profile_shared_file.py tests/test_capability_keys_ic09.py tests/test_agents_md_shared_context_convergence.py tests/test_embed_rules_channel.py tests/test_context_compact_mode.py tests/test_compact_rule_channels.py tests/test_orchestrator_topology_render_parity.py -q`, volle Suite, ac01 -> gruen.
- **Akzeptanz:** `_build_managed_block` (489 Zeilen auf 9aa0e0c0) bleibt **ungeteilt** (Teilung waere Verhaltensrisiko, Out-of-Scope, siehe Risiken); Datei <= 600.
- Commit: `refactor: extract managed block builder into context_sync`

### Task 9: `provider_sync.py` (L3)

> Consumes `base`, `reader`, `settings`, `init_files` (`init_opencode_personal`), `static`, `managed_html` (`_insert_managed_block_above_foreign_content`, `_position_aware_agent_hints`), `managed_block` (`_build_managed_block`).

**Agent:** `senior-developer`. **Depends on:** 8. **Files:** Create `scripts/lib/context_sync/provider_sync.py`; Modify `context.py`, Map. **Interfaces:** Produces `_sync_opencode_context`, `_cleanup_bootstrap_block`, `omit_unresolved_placeholder_lines`, `_sync_continue_context`, `_update_continue_config_managed_block`, `_UNRESOLVED_PLACEHOLDER_RE`, `_CONTINUE_MANAGED_BEGIN/END`.
- Tests: `tests/test_bootstrap_submarkers.py tests/test_check_ignored_absent.py tests/test_continue_rule_frontmatter.py tests/test_opencode_primary_edit_lock.py`.
- **Akzeptanz:** `extensions.py:82` und `sync_pipeline.py:54` (`omit_unresolved_placeholder_lines`) weiter gruen ueber die Fassade.
- Commit: `refactor: extract opencode and continue context sync`

### Task 10: `settings.py` und `init_files.py` (L0)

**Ausfuehrungsreihenfolge (Graph-Pflicht):** 0, 1, 2, 3, 4, 5, 6, **10**, 7, 8, 9, 11, 12, 13, 14. `managed_html.py` (Task 7) ruft `_init_provider_settings_json`, `provider_sync.py` (Task 9) zusaetzlich `init_opencode_personal`; beide muessen schon in `context_sync` liegen, weil neue Module `lib.context` nicht importieren duerfen.

**Agent:** `senior-developer`. **Depends on:** 6. **Files:** Create `scripts/lib/context_sync/settings.py`, `scripts/lib/context_sync/init_files.py`; Modify `context.py`, Map. **Interfaces:** Produces Settings-Gruppe (inkl. `apply_settings_surface_shape`, `_init_provider_settings_json`, `init_settings_json`, `init_settings_local_json`) und Init-Gruppe (`init_claude_personal`, `init_opencode_personal`, `ensure_gitignore_entries`, `CLAUDE_LOCAL_FILE`, `CLAUDE_PERSONAL_LEGACY_FILE`).
- Tests: `tests/test_settings_depth_and_deny.py tests/test_opencode_v2_surface.py tests/test_opencode_main_chat_entry_point.py tests/test_orchestrator_topology_entrypoint.py tests/test_gitignore_keep.py tests/test_gitignore_shadowing.py tests/test_gitignore_platform_defaults.py tests/test_check_ignored_absent.py`.
- **Akzeptanz:** wie Task 2; `ensure_gitignore_entries` weiter importierbar aus `lib.context` und `lib.gitignore`-Konstanten unveraendert (`GITIGNORE_BLOCK_BEGIN/END`).
- Commit: `refactor: extract settings and init file helpers into context_sync`

### Task 11: `prompts_snippets.py`

**Agent:** `senior-developer`. **Depends on:** 9. **Files:** Create `scripts/lib/context_sync/prompts_snippets.py`; Modify `context.py`, Map. **Interfaces:** Produces `sync_prompts_for_continue`, `sync_snippets_for_provider`, `SNIPPETS_DIR` (Ist-Zeile 39; einziger Nutzer `sync_snippets_for_provider` :3707, die uebrigen `SNIPPETS_DIR`-Treffer in `scripts/` sind Platzhalter-Strings); Consumes `base` (`_project_name`).
- Tests: `tests/test_context_prompt_index.py tests/test_snippet_copy_contract.py`.
- **Akzeptanz:** wie Task 2. `context.py` enthaelt nur noch Re-Exports + `_dispatch_context_strategy`, `sync_context_adapters_for_provider`, `_apply_context_filename_settings`, `sync_context_for_provider`.
- Commit: `refactor: extract prompt and snippet sync into context_sync`

### Task 12: Produktions-Aufrufer auf neue Module umstellen

**Agent:** `senior-developer`. **Depends on:** 11. **Files:** Modify `scripts/lib/sync_pipeline.py` (49-60), `scripts/lib/cli_commands.py` (46, 236), `scripts/lib/extensions.py` (82), `scripts/lib/agent_sync.py` (1498). **Interfaces:** Consumes `context_sync.*`; `sync_context_for_provider` bleibt in `lib.context`.
- [ ] Step 1: Pro Aufrufer Importzeile auf das neue Modul umstellen (absolut `from lib.context_sync.x import ...` in `sync_pipeline.py`/`cli_commands.py`, relativ in `extensions.py`/`agent_sync.py`).
- [ ] Step 2: `python3 -m pytest tests/test_import_acyclicity.py tests/test_cli_smoke_multi_provider.py tests/test_dispatch_depth_and_hard_cap.py -q` (`tests/test_cli_commands*.py` existiert auf 9aa0e0c0 nicht), volle Suite, `python3 scripts/sync.py --validate` -> gruen.
- **Akzeptanz:** `grep -n "lib.context import\|\.context import" scripts/lib/sync_pipeline.py scripts/lib/cli_commands.py scripts/lib/extensions.py scripts/lib/agent_sync.py` zeigt nur noch `sync_context_for_provider`; Import-DAG gruen (kein Zyklus ueber lazy `agent_sync` <-> `context`).
- Commit: `refactor: point sync callers at context_sync modules`

### Task 13: Test-Importe umstellen (mechanisch)

**Agent:** `tester`. **Depends on:** 12. **Files:** Modify die Test-Dateien der Aufrufer-Liste (nur Importzeilen). **Interfaces:** keine Verhaltensaenderung.
- [ ] Step 1: Importziele je Name laut `public_surface.json`-Map umstellen; Tests, die nur `sync_context_for_provider` importieren, bleiben unveraendert.
- [ ] Step 2: volle Suite gruen. Diff darf ausschliesslich `from lib.context import` / `import lib.context as` Zeilen enthalten.
- **Akzeptanz:** `grep -rnE "from (scripts\.)?lib\.context import" tests` listet nur noch Namen, die in `context.py` selbst definiert sind (inkl. `scripts.lib.context` in `test_snippet_copy_contract.py:36`, `test_orchestrator_topology_render_parity.py:47`).
- Commit: `test: import context helpers from context_sync modules`

### Task 14: Fassade reduzieren, Budget scharf, Doku

**Agent:** `senior-developer`. **Depends on:** 13. **Files:** Modify `scripts/lib/context.py`, `tests/test_context_split_characterization.py`, `tests/fixtures/context-split/public_surface.json`, `tests/test_context_prompt_index.py` (:181), `docs/CODEBASE_OVERVIEW.md` (:1506), `scripts/lib/consistency/placeholders.py` (:172, Kommentar). **Interfaces:** Produces schlanke `context.py` (<= 600, Ziel ~200 Zeilen).
- [ ] Step 1: Re-Exports ohne verbliebenen Importeur entfernen (Nachweis per Grep in `scripts/`, `tests/`); Re-Exports mit Importeur bleiben (kein Breaking Change fuer Projekt-Skripte, die `lib.context` nutzen koennten; Nachweis nicht moeglich, daher konservativ).
- [ ] Step 1b: Ungenutzte Importe in `context.py` entfernen; `test_prompt_fail_open_clause_gone` (`tests/test_context_prompt_index.py:179-184`) liest dann die Module, in denen `bootstrap_previously_managed`/`write_managed_index` aufgerufen werden (`context_sync/adapters.py`, `context_sync/prompts_snippets.py`), Assertion-Inhalt identisch.
- [ ] Step 2: `xfail` im Budget-Test entfernen; `public_surface.json` auf die verbleibende Fassade reduzieren (dokumentierte, einmalige Aenderung).
- [ ] Step 3: Volle Suite, ac01, `python3 scripts/sync.py --validate`, `python3 scripts/sync.py --check` (Flag `scripts/sync.py:334`) -> gruen; `wc -l scripts/lib/context.py scripts/lib/context_sync/*.py` alle <= 600.
- **Akzeptanz:** alle Module <= 600 Zeilen; `hashes.json` (ac01) in `git diff` unveraendert; Sync-Selbstlauf erzeugt keinen Diff in gerenderten Dateien.
- Commit: `refactor: slim context.py to entry points after split`

## Risiken

| Risiko | Wirkung | Gegenmassnahme |
|---|---|---|
| Merge-Konflikte: #1194 (B), #1182/#1183/#1208/#1085c/#1086a-e (C), #1161 (H), #1086f (zurueckgestellt), ausserdem jeder Hotfix auf `context.py` | verschobener Code, schwere Rebases | Start erst nach Merge aller C-Teile; Branch von frischem `origin/main`; waehrend der Laufzeit Freeze fuer `context.py`; Tasks klein, je ein Commit, `git diff --color-moved` im Review |
| Import-Zyklen: `context.py` <-> `agent_sync.py` (lazy 3566/1498), Ziel-Schnitt ohne Graph-Korrektur hatte 8 Modulzyklen (z.B. `adapters -> managed_html -> adapters`), `extensions.py:82` lazy auf `context`, `context.py` laedt viele Module lazy | Zyklus erst zur Laufzeit sichtbar; `test_import_acyclicity.py` sieht lazy Importe nicht | Schichten L0-L3 strikt einhalten; Ausfuehrungsreihenfolge (Task 10 vor 7); neue Module importieren `lib.context` nie; Aufrufgraph in Task 0; Fehlerprobe `python3 -c "import lib.context_sync.managed_block"` je Modul isoliert in Tasks 2-11 |
| Monkeypatch-Stellen binden an den Modulnamen (`context.TemplateBuilder`, `context._load_gate_card_sections`) | Tests werden still wirkungslos oder rot | Tasks 6 und 8 migrieren genau diese zwei Stellen (Grep auf 9aa0e0c0 fand keine weiteren, auch keine `patch("lib.context...")`-Strings); Task 1 Step 3b wiederholt den Grep |
| Quelltext-Scan-Tests lesen `context.py` als Text (5 Dateien, Liste unter "Aufrufer") | rot (IndexError, fehlender String, Allowlist) oder hohl | Tasks 6/7/8/14 ziehen Pfad/Schluessel mit; Spec haelt fest, dass das Umschluesseln der Ratchet-Allowlist keine Erweiterung ist |
| Relative Importe `.x` -> `..x` falsch | ImportError nur im Lazy-Pfad | AST-Hash-Test normalisiert `ImportFrom.level`, daher dort nicht gefangen: `test_lazy_imports_resolve` (Task 1) loest jeden lazy Import auf; ac01 deckt die Hauptpfade ab |
| `_build_managed_block` (489 Zeilen auf 9aa0e0c0) bleibt gross; #1183 (Phase C) aendert sie vorher | Datei ~530 Zeilen inkl. Kopf, knapp im Budget; nach #1183 evtl. > 600 | bewusst ungeteilt (Verhaltensrisiko); `_shared_topology_flags` nach `base`; Task 0 misst neu; ueber Budget -> User-Entscheidung (Offene Entscheidungen) |
| Python 3.9 | `tuple[...]`-Annotationen brechen ohne Future-Import | `from __future__ import annotations` in jedem neuen Modul; CI-3.9-Job beobachten |
| Scope-Explosion | Zusatz-Bugfixes im Zug des Moves | Regel "wortgleich"; AST-Hash-Test erzwingt es |

## Abweichung zur Roadmap

1. Issue #1086 nennt "over 2700 lines"; Roadmap (Entscheidung 6) nennt 3495 (Stand a3d65da4); Ist-Stand auf 9aa0e0c0 **3750** (`wc -l`). Beide Zahlen veraltet, Groessenordnung unveraendert.
2. `config_audit_providers.py:78` verweist `PROVIDER_TOUCHPOINTS` auf `scripts/lib/context.py` mit Muster `provider_dirs = {...}`; dieses Muster kommt in `scripts/lib` nicht mehr vor (Grep: nur `ignore_provider_dirs` in `gitignore.py:256`). Das ist dokumentiert und gewollt (`config_audit_providers.py:53-57`, #627: "silently skipped" ... "no touchpoint removal needed"). Der Pfad-String bleibt nach dem Split gueltig (`context.py` existiert weiter). Kein Teil dieses Plans, kein eigenes Issue noetig.
3. Roadmap-Ankerangaben `context.py:204` (#1161), `:1710` (#1194), `:2147` (#1208): auf 9aa0e0c0 liegen die Funktionen bei `_backup_context_file` (197-212, Anker passt), `apply_settings_surface_shape` (1815-1873) bzw. `_extract_rule_section` (2300-2326); `:1710`/`:2147` sind also veraltet. Nach dem Split liegen alle drei in `context_sync/*` (`base.py`, `settings.py`, `compact.py`).
4. Frische-Check: `check_plan_refs.py` liegt nicht in `origin/main`, sondern im Worktree `.tmp/wt-check-plan-refs/scripts/check_plan_refs.py`; Lauf gegen `origin/main` siehe Review-Fragment. Blanke `:NNNN`-Anker prueft es nicht (hier per `ast` von Hand gemessen).
5. Der Issue-Beleg `context.py:2709-2741` (#1086f `init_claude_personal`) ist verschoben auf 3099-3138 (9aa0e0c0).

## Frische-Check-Referenzen

- file: scripts/lib/context.py
- file: scripts/lib/context_sync/__init__.py
- file: scripts/lib/context_sync/base.py
- file: scripts/lib/context_sync/reader.py
- file: scripts/lib/context_sync/static.py
- file: scripts/lib/context_sync/adapters.py
- file: scripts/lib/context_sync/compact.py
- file: scripts/lib/context_sync/managed_html.py
- file: scripts/lib/context_sync/managed_block.py
- file: scripts/lib/context_sync/provider_sync.py
- file: scripts/lib/context_sync/settings.py
- file: scripts/lib/context_sync/init_files.py
- file: scripts/lib/context_sync/prompts_snippets.py
- file: scripts/lib/sync_pipeline.py
- file: scripts/lib/cli_commands.py
- file: scripts/lib/extensions.py
- file: scripts/lib/agent_sync.py
- file: scripts/lib/config_audit_providers.py
- file: scripts/lib/consistency/placeholders.py
- file: tests/test_import_acyclicity.py
- file: tests/test_ac01_render_identity.py
- file: tests/fixtures/ac01-baseline/hashes.json
- file: tests/test_gate_card_compact.py
- file: tests/test_context_profile_shared_file.py
- file: tests/test_context_split_characterization.py
- file: tests/fixtures/context-split/function_ast_hashes.json
- file: tests/fixtures/context-split/public_surface.json
- file: docs/specs/2026-11-11-context-split-1086i-spec.md
- file: docs/specs/2026-10-11-context-profiles-spec.md
- file: docs/superpowers/plans/2026-11-10-backlog-roadmap.md
- file: docs/CODEBASE_OVERVIEW.md
- file: tests/test_compact_rule_channels.py
- file: tests/test_capability_keys_ic09.py
- file: tests/test_context_prompt_index.py
- file: tests/test_provider_agnostic_dispatch.py
- file: tests/test_orchestrator_topology_effective_flags.py
- file: tests/test_entry_hint_topology.py
- file: tests/test_orchestrator_topology_render_parity.py
- symbol: _build_managed_block
- symbol: _update_managed_html_block
- symbol: _write_reader_context
- symbol: _shared_context_users
- symbol: _has_capability
- symbol: _core_context_filename
- symbol: build_gate_card
- symbol: _load_gate_card_sections
- symbol: compact_embedded_rule
- symbol: sync_context_for_provider
- symbol: only_variables
- symbol: omit_unresolved_placeholder_lines
- symbol: enforce_context_hard_cap
- symbol: ensure_gitignore_entries
- symbol: apply_settings_surface_shape
- symbol: TemplateBuilder
- symbol: PROVIDER_TOUCHPOINTS
- symbol: _shared_topology_flags
- symbol: _position_aware_agent_hints
- symbol: _dispatch_context_strategy
- symbol: _project_name
- issue: #1086
- issue: #1194
- issue: #1182
- issue: #1183
- issue: #1208
- issue: #1161
- issue: #1085
- issue: #1142
- issue: #1195
- issue: #885
- issue: #478
- issue: #1169 (Entscheidung 28)
- issue: #1086g (Entscheidung 24)
- pr: #1218 (gemergt, Basiswechsel auf 9aa0e0c0)
- ref: origin/main 9aa0e0c0
- decision: Roadmap-Entscheidungen 6, 17-38 (decisions-part2/-part3, User-beantwortet)

## Entscheidungen (beantwortet)

Der Plan hatte keine offenen Fragen (Original-Abschnitt: "keine"). Bezug zu den Roadmap-Entscheidungen 6 und 17-38 (User-beantwortet):

- Entscheidung 6 (#1086 i in dieser Runde, eigener Plan, L): Grundlage dieses Plans.
- Entscheidung 36 (Ausnahmen nur #1086i und #1209): im Absatz nach der Abhaengigkeitstabelle.
- Entscheidung 34 C-N4 / 38c (#1086 a-e jetzt in C, f zurueckgestellt, i eigener PR): Abhaengigkeitstabelle.

- Entscheidung 18 (#1086i: eigener Branch/PR direkt nach dem Phase-C-PR): Ausnahme zu "ein Phase = ein PR", eingearbeitet im Absatz nach der Abhaengigkeitstabelle.
- Entscheidung 17 (strikt ein PR je Phase, ein Commit je Task): Kontext; Phase-C-Teil-PRs sind Commits im Phase-C-PR.
- Entscheidung 46 (#1086 bleibt offen, bis Punkt f entschieden/verworfen ist): kein Schliess-Schritt fuer #1086 in diesem Plan; Absatz nach der Abhaengigkeitstabelle.
- Entscheidung 52 (Nachfolge-PR fuer gesperrte/spec-gesteuerte Tasks, max. 2 PRs je Phase): #1086i folgt nach dem letzten Phase-C-PR (ggf. `fix/phase-c-sync-config-gated`).
- Entscheidung 56 (#1086i als Nachfolge-PR nach dem letzten Phase-C-PR): beantwortet die fruehere Frage "Reihenfolge 18 vs. 52"; eingearbeitet im Absatz nach der Abhaengigkeitstabelle.
- Entscheidung 24 (#1086g ohne Tier-Umbau geschlossen): keine Abhaengigkeit, Zeile in der Abhaengigkeitstabelle.
- Entscheidung 28 (#1161 Punkt 5, `hook_json_get_many`): nur Hooks, kein Bezug zu `context.py`. Entscheidung 29 (#1161 Punkt 2, Verzeichnis per Capability-Flag): nach dem Split, falls `context_sync` beruehrt wird; Zeile #1161 in der Abhaengigkeitstabelle.
- Entscheidung 25 (Co-Authored-By-Trailer): nicht betroffen, der Plan enthaelt keine entsprechende Constraint.

## Offene Entscheidungen (neu, ungeklaert)

- **C1086i-U1 (bedingt):** Falls `_build_managed_block` nach dem letzten Phase-C-PR (#1183) so gross ist, dass `managed_block.py` > 600 Zeilen wird (Task 0 Step 2 misst): Budget-Ausnahme fuer genau diese Datei (Empfehlung, kein Verhaltensrisiko) oder Teilung der Funktion (Verhaltensrisiko, verletzt "wortgleich")? Nur stellen, wenn die Messung es ausloest.
- Paketname `context_sync` und Schichtung: keine eigene User-Frage, wird mit der Spec-Freigabe in Task 0 entschieden (Step 2c). Empfehlung: Strangler mit `context.py` als Fassade (`git blame` und alle Importe bleiben).

## Nicht verifiziert

- Nichts ausgefuehrt: weder Tests noch `--validate`; Gruenstand der Suite vor dem Split unbekannt (Task 1 Step 4 prueft ihn).
- Modulgroessen "ca. Zeilen" = Summe der `ast`-Spannen ohne Kopf/Leerzeilen (Plan-Wert); echte Dateilaengen erst nach dem Move.
- Aufrufgraph beruht auf Namensreferenzen in top-level-Funktionen (`ast.Name`), nicht auf Laufzeit; dynamische Zugriffe (`getattr`, Strings) erfasst er nicht.
- Ob die `ac01`-Matrix alle Pfade in `provider_sync.py`/`prompts_snippets.py` (z.B. Continue-Prompts) abdeckt: nicht geprueft; ersatzweise AST-Hash-Pin und `test_lazy_imports_resolve`.
- Python-3.9-Kompatibilitaet der Neu-Module: nur durch Regel, nicht durch Lauf.
- Alle Zeilenangaben gelten fuer `origin/main 9aa0e0c0`. Die Phase-C-PRs (#1182, #1183, #1208, #1085c, #1086a-e; Phasen-PR und Nachfolge-PR) aendern `context.py` vorher; Task 0 Step 2 misst neu.
- Projekt-Skripte ausserhalb dieses Repos, die `lib.context` importieren: nicht pruefbar (Task 14 Step 1 bleibt deshalb konservativ).

## Self-Review

- Jeder Task mappt auf genau eine Rolle (0: concept-specifier, 1/13: tester, Rest: senior-developer); Akzeptanzkriterien messbar (Grep, Zeilenzahl, rote/gruene benannte Tests).
- `Files:`/`Interfaces:` je Task; keine Parallelgruppe (strikt sequentiell, da dieselbe Datei `context.py` betroffen).
- `pipeline_stages` deckt die `implement`-Stage (Task 2 = erster Implementierungsschritt).
- #1086i genau einmal abgedeckt; kein TBD/TODO; Zeilen per `ast` (`lineno`/`end_lineno`) auf 9aa0e0c0 gemessen, Abweichungen oben.
- Entscheidungen 6, 17-38 geprueft: 18/36 (Ausnahmen #1086i und #1209) im Absatz nach der Abhaengigkeitstabelle; 17, 24, 28, 29, 34/38c eingearbeitet; eine bedingte offene Frage (C1086i-U1); Paketname/Schichtung im Spec-Gate.
- Basiswechsel `origin/main` a3d65da4 -> 9aa0e0c0 (PR #1218): alle Zeilenangaben neu gemessen; Modulschnitt per Aufrufgraph zyklenfrei korrigiert; Ausfuehrungsreihenfolge (Task 10 vor 7) ergaenzt; Quelltext-Scan-Tests ergaenzt.
- Frische-Check-Liste um #1169, #1086g, PR #1218, `origin/main 9aa0e0c0` und die Roadmap-Entscheidungen ergaenzt.
- Entscheidung 25 nicht zutreffend (kein Co-Authored-By-Constraint im Plan).
- Entscheidungen 39-53 geprueft: 46 und 52 eingearbeitet (kein Schliess-Schritt fuer #1086; Start nach dem letzten Phase-C-PR); 39-45, 47-51, 53 nicht zutreffend.
- Entscheidungen 54-57 geprueft: 56 eingearbeitet (#1086i nach dem letzten Phase-C-PR; Frage 18 vs. 52 beantwortet); 54, 55, 57 nicht zutreffend. Offen bleibt nur C1086i-U1 (bedingt auf Messung).
