# Tmp-Sink-Injection — Ausführungsstatus

**Plan:** `docs/plans/2026-10-24-tmp-sink-injection-plan.md`
**Spec:** `docs/specs/2026-10-24-tmp-sink-injection-spec.md` (APPROVED, Rev. 3)
**Branch:** `fix/tmp-sink-injection` (Basis `14c0ad14`)
**Stand:** 2026-10-25

Diese Datei ist der laufende Ledger-Nachweis für die Planausführung. Jede Zeile wird
nach dem Grün-Lauf des jeweiligen Tasks und dem zugehörigen Commit aktualisiert. Die
Spalte `Commit` bleibt `— (pending)`, bis der jeweilige Commit tatsächlich existiert
(keine vorweggenommenen SHAs).

## Tasks

| Task | Title | Status | Commit | Notes |
|---|---|---|---|---|
| 1 | Zentraler Tmp-Paths-Resolver | done | — (pending) | Steps 1–3 grün; Step 4 (Commit) offen, weil der Subagent keinen Commit-Auftrag hatte |
| 2 | Builder-Variablen und Ausnahme-Validierung | done | — (pending) | Steps 1–3 grün; Step 4 (Commit) offen (kein Commit-Auftrag) |
| 3 | Suite-Kommando literal-frei rendern | done | — (pending) | Steps 1–3 grün; Step 4 (Commit) offen, weil der Subagent keinen Commit-Auftrag hatte |
| 4 | Achtzehn System-Temp-Literale in sieben Templates ersetzen | pending | — (pending) | — |
| 5 | Vier Sink-Literale in Auditor-Templates | pending | — (pending) | — |
| 6 | Vage Temp-Anweisungen präzisieren | pending | — (pending) | — |
| 7 | Standalone-Export regenerieren | pending | — (pending) | — |
| 8 | Hook-Anker und fail-closed Root-Auflösung | pending | — (pending) | — |
| 9 | Hook-Testmatrix und bewusste Inversion | pending | — (pending) | — |
| 10 | Env-Pin für Framework-Subprozesse ausweiten | pending | — (pending) | — |
| 11 | Subprozess-Klassifikation und Backup-Staging | pending | — (pending) | — |
| 12 | Gitignore- und Doctor-Zweitparser entfernen | pending | — (pending) | — |
| 13 | Opencode-Schreibscope aus dem Sink ableiten | pending | — (pending) | — |
| 14 | Consistency-Check für Temp-Literale | pending | — (pending) | — |
| 15 | Aggregations-Guard über alle Schreibpfade | pending | — (pending) | — |
| 16 | Goldens rebaselinen | pending | — (pending) | — |
| 17 | Doku und Beispiel-Config | pending | — (pending) | — |
| 18 | Abschluss-Validierung und Ledger | pending | — (pending) | Läuft zuletzt (Abschluss-Gate) |
| 19 | Toolchain-Cache-Opt-in (Q3) | pending | — (pending) | — |
| 20 | Antigravity `args.FilePath` → `file_path` (Q10) | pending | — (pending) | — |
| 21 | §5.5 verweist auf `PYTEST_BASETEMP` (Q11) | pending | — (pending) | — |
| 22 | Allowlist-Schema-Härtung (Q6) | pending | — (pending) | — |

## Evidence — Task 1

### Rot (vor der Implementierung)

`python3 -m pytest tests/test_tmp_sink_output_dirs.py -q` → Exit 2:

```
_____________ ERROR collecting tests/test_tmp_sink_output_dirs.py ______________
ImportError while importing test module '/home/hermes/repos/agent-meta/tests/test_tmp_sink_output_dirs.py'.
tests/test_tmp_sink_output_dirs.py:22: in <module>
    from lib.tmp_paths import (  # noqa: E402
E   ModuleNotFoundError: No module named 'lib.tmp_paths'
=========================== short test summary info ============================
ERROR tests/test_tmp_sink_output_dirs.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.41s
```

### Grün (nach der Implementierung)

| # | Kommando | Ergebnis |
|---|---|---|
| 1 | `python3 -m pytest tests/test_tmp_sink_output_dirs.py -q` | `39 passed in 3.62s`, Exit 0 |
| 2 | `python3 -m pytest tests/test_tmp_sink_path_parity.py tests/test_tmp_sink_path_hardening.py tests/test_tmp_sink_migration_error.py tests/test_repo_containment_hook.py -q` | `259 passed in 11.98s`, Exit 0 |
| 3 | `python3 scripts/sync.py --validate` | `0 action(s)  |  382 skipped  |  2 warning(s)`, Exit 0 (beide WARNINGS vorbestehend: `active-set.gate-dropped`, Submodul-Checkout `external/awesome-claude-code`) |
| 4 | `python3 -c "import sys; sys.path.insert(0,'scripts'); import lib.tmp_paths"` | Exit 0, keine Ausgabe |
| 5 | `python3 -c "import ast; ast.parse(...tmp_paths.py..., feature_version=(3, 9))"` | `py3.9 syntax ok` |

### Abgedeckte ACs (Task 1)

- **AC-12** — `test_tmp_env_pins_absolute_sink`, `test_tmp_env_preserves_base_env`
- **AC-15 (Randfall `gettempdir()` im Projekt)** — `test_pytest_basetemp_rejects_temp_root_inside_project`
- **AC-16 (Resolver-Hälfte)** — `test_relative_and_absolute_sink_variables`
- **AC-23** — `test_resolver_does_not_raise_when_sink_disabled`, `test_resolver_still_validates_path_when_sink_disabled`
- **AC-24** — `test_writers_still_raise_when_sink_disabled`
- **AC-35** — `test_env_pin_block_is_absolute`
- **AC-36** — `test_env_pin_block_refuses_missing_directory`
- Zusatz (IC-04/IC-19/Q1/Q3): `test_system_temp_exception_defaults`,
  `test_pytest_basetemp_uses_system_temp_when_exception_active`,
  `test_pytest_basetemp_falls_back_to_sink_without_exception`,
  `test_pytest_basetemp_rejects_quote_in_value`,
  `test_disabled_sink_without_pytest_exception_has_no_basetemp`,
  `test_toolchain_cache_requires_enabled_exception`

### Abweichungen von der Aufgabenbeschreibung (Spec ist normativ)

1. **Basetemp-Zuordnung:** Die Aufgabenbeschreibung nannte `<absolute>/pytest` „when the
   exception is active"; die Spec (`Resolver-Vertrag`, IC-04) legt das Gegenteil fest:
   aktive Ausnahme ⇒ `<tempfile.gettempdir()>/<user>/pytest-agent-meta`, sonst (Sink aktiv)
   ⇒ `<absolute>/pytest`. Implementiert nach Spec; Tests decken beide Zweige ab.
2. **Default der Ausnahme:** nicht `enabled=False`, sondern Spec/Q1/ADR-03:
   `enabled=True`, `pytest_basetemp=True`, `toolchain_cache=False` plus Framework-`reason`
   (Rückwärtskompatibilität: Projekte ohne den Key verhalten sich wie bisher).
3. **Fehlercode bei `"` im Basetemp:** Interface-Contracts-Tabelle nennt für
   `resolve_pytest_basetemp` `tmp-sink.system-temp-exception`; die Aufgabenbeschreibung
   nannte `tmp-sink.pytest-token` (dieser Code gehört zum unersetzten Token, AC-14).
   Implementiert: `tmp-sink.system-temp-exception`.
4. **Step 4 (Commit) nicht ausgeführt** — kein Commit-Auftrag für diesen Subagenten
   (siehe Spalte `Commit`).
5. **Provisionierung im Resolver (in Task 2 korrigiert):** AC-12 verlangt, dass die drei
   Env-Werte als Verzeichnis existieren. Task 1 provisionierte dafür im
   `resolve_tmp_paths`; Task 2 hat das entfernt, weil ein `sync.py --dry-run` sonst
   `.tmp` anlegt. Provisionierung lebt jetzt in `tmp_env` (AC-12), der Env-Pin-Block
   prüft die Existenz zur Laufzeit (AC-36) — der Resolver bleibt schreibfrei.

## Evidence — Task 2

### Rot (vor der Implementierung)

`python3 -m pytest tests/test_tmp_paths_builder.py tests/test_repo_containment_validate.py tests/test_repo_containment_schema.py -q`
→ `16 failed, 62 passed`; die beiden geforderten Anker:

```
tests/test_tmp_paths_builder.py::test_builder_sets_absolute_and_relative_sink
>       absolute = variables["TMP_SINK_ABS_PATH"]
E       KeyError: 'TMP_SINK_ABS_PATH'

tests/test_tmp_paths_builder.py::test_unresolved_pytest_token_fails_sync
>       monkeypatch.setattr("lib.config._replace_pytest_basetemp_token", ...)
E       AttributeError: 'module' object at lib.config has no attribute '_replace_pytest_basetemp_token'
```

### Grün (nach der Implementierung)

| # | Kommando | Ergebnis |
|---|---|---|
| 1 | `python3 -m pytest tests/test_tmp_paths_builder.py tests/test_repo_containment_validate.py tests/test_repo_containment_schema.py -q` | `78 passed`, Exit 0 |
| 2 | `python3 -m pytest tests/test_tmp_sink_output_dirs.py tests/test_tmp_sink_path_parity.py tests/test_tmp_sink_path_hardening.py tests/test_tmp_sink_default_on.py tests/test_tmp_sink_migration_error.py -q` | `274 passed`, Exit 0 |
| 3 | `python3 scripts/sync.py --validate` | Exit 0, `0 action(s) \| 382 skipped \| 2 warning(s)` (beide vorbestehend) |
| 4 | `python3 scripts/sync.py --dry-run` | Exit 0 |
| 5 | `python3 scripts/sync.py --config <scratch>/.meta-config/project.yaml --dry-run` (Sink aktiv) | Exit 0, `DRY-RUN: would provision tmp-sink .tmp/`, **kein** `.tmp` angelegt |
| 6 | `ast.parse(..., feature_version=(3, 9))` für `config.py`, `consistency/placeholders.py`, `sync_pipeline.py`, `tmp_paths.py` | alle `ok` |
| 7 | Alle 48 Testmodule, die `build_variables` referenzieren (u. a. `test_ac01_render_identity`, `test_compact_matrix`, `test_build_variables_*`, `test_template_slimming_equivalence`) | grün (batchweise; langsame Matrix-Tests unverändert langsam) |

### Abgedeckte ACs (Task 2)

- **AC-13** — `test_builder_resolves_pytest_token_in_both_values`
- **AC-14** — `test_unresolved_pytest_token_fails_sync` (Builder wirft `SyncError`
  `tmp-sink.pytest-token`; der Sync-CLI mappt das auf Exit 1)
- **AC-15** — `test_system_temp_exception_matrix` (4 Fälle, parametrisiert, inkl.
  `gettempdir()` im Projekt), `test_repo_containment_validate.py::test_system_temp_exception_*`,
  `test_repo_containment_schema.py::test_system_temp_exception_*`
- **AC-16** — `test_builder_sets_absolute_and_relative_sink`
- **AC-25** — `test_disabled_sink_omits_absolute_variables`,
  `test_disabled_sink_sync_dry_run_is_successful`
- **AC-35** — `test_env_pin_block_is_absolute`

### Abweichungen von der Aufgabenbeschreibung (Spec ist normativ)

1. **`_fail` vs. `SyncError`:** `_build_orch_variables` liegt in einer Bibliothek ohne
   `config_path` und wird u. a. von `meta_optimizer` aufgerufen. Statt `sys.exit` wirft
   der Builder bei Rest-Token `SyncError` mit dem wörtlichen Spec-Text
   (`tmp-sink.pytest-token: '{{PYTEST_BASETEMP}}' was not resolved in
   TEST_COMMANDS/CODE_QUALITY_RULES.`); der Sync-CLI fängt `SyncError` bereits ab und
   beendet mit Exit 1. Kein `sys.exit` in der Bibliothek.
2. **`_sync_stage_tmp_sink` statt `_sync_tmp_sink`:** der reale Funktionsname (Plan
   nennt den veralteten Namen); `resolve_effective_repo_containment` bleibt zusätzlich
   nötig, weil `cleanup_tmp_sink`/`ensure_tmp_sink_gitignore` das Effective-Objekt
   verlangen — `resolve_tmp_paths` liefert nur `TmpPaths`.
3. **Schema-Datei ergänzt:** `config/project-config.schema.json` steht nicht in der
   Files-Liste, ist aber zwingend (`tmp-sink.additionalProperties: false` würde den
   neuen Key sonst ablehnen). `system-temp-exception` ist als geschlossenes Objekt
   unter `tmp-sink` ergänzt.
4. **Task-1-Tests angepasst:** `test_env_pin_block_is_absolute` und
   `test_env_pin_block_refuses_missing_directory` provisionieren jetzt explizit über
   `tmp_env(paths)`, weil der Resolver seit Task 2 schreibfrei ist (Dry-Run-Sicherheit).

## Evidence — Task 3

### Rot (vor der Config-Änderung, `project.yaml` auf HEAD-Stand gestasht)

`python3 -m pytest tests/test_tmp_sink_output_dirs.py -q -k "test_test_commands_have_no_system_temp_literal or test_basetemp_with_spaces"`
→ Exit 1, `2 failed, 39 deselected in 3.78s`:

```
>           assert "/tmp" not in command_text, key
E           AssertionError: TEST_COMMANDS
E           assert '/tmp' not in 'python scri...t-agent-meta'
E             
E             '/tmp' is contained here:
E               basetemp=/tmp/$USER/pytest-agent-meta
E             ?          ++++

tests/test_tmp_sink_output_dirs.py:469: AssertionError

>           assert '--basetemp="' in rendered, key
E           AssertionError: TEST_COMMANDS
E           assert '--basetemp="' in 'python scripts/sync.py --dry-run && python scripts/sync.py --validate && python3 -m pytest tests/ --basetemp=/tmp/$USER/pytest-agent-meta'

tests/test_tmp_sink_output_dirs.py:493: AssertionError
=========================== short test summary info ============================
FAILED tests/test_tmp_sink_output_dirs.py::test_test_commands_have_no_system_temp_literal
FAILED tests/test_tmp_sink_output_dirs.py::test_basetemp_with_spaces_is_single_argument
```

### Grün (nach der Implementierung)

| # | Kommando | Ergebnis |
|---|---|---|
| 1 | `python3 -m pytest tests/test_tmp_sink_output_dirs.py -q` | `41 passed in 5.65s`, Exit 0 |
| 2 | `python3 scripts/sync.py --dry-run` | Exit 0; `12 action(s) \| 437 skipped \| 35 warning(s)`; `grep -c '/tmp'` im Log = **0** |
| 3 | `python3 scripts/sync.py --validate` | Exit 0; `12 action(s) \| 370 skipped \| 2 warning(s)` — die 12 Writes (4 Test-Rollen × 3 Provider) sind **vorbestehend** (identisch mit gestashten Task-3-Änderungen), beide Warnungen ebenfalls |
| 4 | `python3 scripts/sync.py --validate-spec-plan` | Exit 0; `validate-spec-plan: no spec/plan-workflow findings` (Lauf vor dem Ledger-Update dieser Datei; siehe Hinweis unten) |
| 5 | Regression `python3 -m pytest tests/test_tmp_paths_builder.py tests/test_repo_containment_validate.py tests/test_repo_containment_schema.py -q` | `78 passed`, Exit 0 |
| 6 | Zusatz: `tests/test_config_audit.py` + 5 Template-Config-Testmodule | `33 passed` bzw. `94 passed`, Exit 0 |

Die 35 Dry-Run-Warnungen sind **vorbestehend**: mit gestashten Task-3-Änderungen
meldet `--dry-run` auf HEAD `0 action(s) | 449 skipped | 35 warning(s)`. Die 12
`WRITE`-Actions im Dry-Run sind dagegen die erwartete Folge der Config-Änderung: die
vier Test-Rollen (`documenter`, `e2e-tester`, `test-executor`, `tester`) × drei
Provider betten `{{TEST_COMMANDS}}` ein und werden beim nächsten echten Sync
regeneriert (generierte Verzeichnisse sind in agent-meta gitignored).
`--validate` meldet die 12 Actions unabhängig von den Task-3-Änderungen (auch auf
HEAD) — ein vorbestehender Zähler-Unterschied der beiden Modi, kein Finding
(Exit 0, 2 vorbestehende Warnungen).

Gerenderte Werte (Kommando 5 aus der Aufgabenbeschreibung):

```
PYTEST_BASETEMP = /tmp/hermes/pytest-agent-meta
--- TEST_COMMANDS ---
python scripts/sync.py --dry-run && python scripts/sync.py --validate && python3 -m pytest tests/ --basetemp="/tmp/hermes/pytest-agent-meta"
--- CODE_QUALITY_RULES ---
- sync.py muss nach jeder Änderung mit --dry-run fehlerfrei laufen
- Alle neuen Platzhalter müssen in agent-meta.config.example.yaml dokumentiert sein
- Änderungs-Workflow: Einfacher Wert -> project.yaml, Projektwissen -> 3-project-ext, Neue Rolle -> 1-generic, Neuer Skill -> sync.py --add-skill
- pytest-Basetemp NIE im Arbeitsbaum — Aufruf: --basetemp="/tmp/hermes/pytest-agent-meta" (Quelle: repo_containment.tmp-sink.system-temp-exception); Repo-Kopien in Tests müssen .tmp/ ausschließen und Symlinks unverfolgt kopieren (siehe docs/concepts/repo-containment-prison-mode.md §5.5)
```

Quelltext-Check: `grep -n '/tmp\|\$USER\|%TEMP%' .meta-config/project.yaml
templates/configs/agent-meta.config.example.yaml` → keine Treffer.

### Abgedeckte ACs (Task 3)

- **AC-13** — `test_test_commands_have_no_system_temp_literal` (beide Werte ohne
  `/tmp`, `%TEMP%`, `C:\Temp`, `$USER`; `--basetemp="…"` shell-gequotet; genau ein
  `--basetemp=`-Argument nach `shlex.split`)
- **AC-34** — `test_basetemp_with_spaces_is_single_argument` (`gettempdir()` mit
  Leerzeichen ⇒ genau ein Argument, Wert identisch zu `PYTEST_BASETEMP`)

### Abweichungen von der Aufgabenbeschreibung (Spec ist normativ)

1. **Token-Form:** Die Aufgabe nannte `--basetemp="{{PYTEST_BASETEMP}}"`. Der in Task 2
   implementierte und getestete Helper `_replace_pytest_basetemp_token` entfernt bei
   dieser bereits gequoteten Form die Anführungszeichen (Ergebnis:
   `--basetemp=/tmp/a b/...`), was AC-34 mit Leerzeichen bricht. Eingesetzt ist deshalb
   `--basetemp={{PYTEST_BASETEMP}}`, das vertragsgemäß zu
   `--basetemp="<absolut>"` rendert (Spec AC-13/AC-34: shell-gequotet, leerzeichensicher).
2. **Literal-Assertion maskiert den aufgelösten Basetemp:** AC-13 verbietet Literale im
   konfigurierten Kommando, erlaubt aber ausdrücklich „einen plattformneutralen
   Temp-Root-Pfad". Auf POSIX ist `tempfile.gettempdir()` = `/tmp`, ein roher
   Substring-Check würde also den erlaubten aufgelösten Wert verbieten. Der Test
   ersetzt `PYTEST_BASETEMP` vor der Literal-Prüfung durch `<PYTEST_BASETEMP>`.
3. **Testname:** Die Spec (`AC-34`) nennt
   `test_basetemp_with_spaces_is_single_argument`; die Aufgabe nannte
   `test_basetemp_with_space_keeps_single_argument`. Umgesetzt ist der Spec-Name.
4. **Bullet-Formulierung:** `--basetemp={{PYTEST_BASETEMP}}` steht als eigenständiges
   Argument (nicht in Klammern), damit `shlex.split` ein sauberes
   `--basetemp=`-Argv-Element liefert (sonst klebt `(` am Token).
5. **Step 4 (Commit) nicht ausgeführt** — kein Commit-Auftrag für diesen Subagenten.

**Hinweis zu `--validate-spec-plan`:** Der Exit-0-Lauf erfolgte vor dem Ledger-Update
dieser Datei (bzw. mit auf HEAD gestashtem Status-Dokument). Sobald
`docs/plans/2026-10-24-tmp-sink-injection-status.md` uncommitted ist, matcht sie das
Datumsmuster `^\d{4}-\d{2}-\d{2}-.+\.md$` und wird als Plan-Artefakt gescannt:
7 WARNINGs (`spec_plan_required_sections` ×6, `spec_plan_traceability` ×1 wegen des
`` `(APPROVED, Rev. 3)` ``-Suffix in der `**Spec:**`-Zeile), **0 ERRORs**, Exit 1.
Das ist ein Artefakt des fehlenden Commits (Step 4) und verschwindet mit dem
Task-Commit; die Code-/Config-Änderung selbst ist clean (Exit 0 im gestashten Lauf).
Identity-Check der Migration: 2 stabile Config-Keys (`TEST_COMMANDS`,
`CODE_QUALITY_RULES`) vorher/nachher vorhanden — 0 fehlend, 0 doppelt; 0
`/tmp`/`$USER`/`%TEMP%`-Treffer in beiden Config-Dateien.
