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
| 4 | Achtzehn System-Temp-Literale in sieben Templates ersetzen | done | — (pending) | Steps 1–3 grün; 18 Literale → `{{TMP_SINK_PATH}}`; Version-Bumps + 8 `based-on`-Pins kaskadiert; Step 4 (Commit) offen |
| 5 | Vier Sink-Literale in Auditor-Templates | done | — (pending) | Steps 1–3 grün; Step 4 (Commit) offen, kein Commit-Auftrag. Golden `app-lifecycle-governor` erwartungsgemäß rot (nur Versionszeilen), Rebaseline Task 16 |
| 6 | Vage Temp-Anweisungen präzisieren | done | — (pending) | Steps 1–3 grün; 13 Rollen + `plan-ledger.md` nennen `{{TMP_SINK_PATH}}`; 13 Patch-Bumps, kein `2-platform`-Cascade (keine `based-on`-Kinder); Step 4 (Commit) offen, kein Commit-Auftrag |
| 7 | Standalone-Export regenerieren | done | — (pending) | Steps 1–3 grün; `TMP_SINK_PATH=".tmp"` + `TMP_SINK_ENV_PIN_BLOCK=""`; 23 Standalone-Dateien regeneriert (0 Drift); AC-26/AC-27; Step 4 (Commit) offen, kein Commit-Auftrag |
| 8 | Hook-Anker und fail-closed Root-Auflösung | done | — (pending) | Steps 1–3 grün; Anker-Regel (`cwd`/Zielverzeichnis, kein `$PWD`), `repo-containment.no-root` statt Root-Promotion, absolute Sink-Meldung, Hook-Sink == `TmpPaths.absolute`; Impl-Version 1.1.0→1.2.0; Step 4 (Commit) offen, kein Commit-Auftrag |
| 9 | Hook-Testmatrix und bewusste Inversion | done | — (pending) | Steps 1–3 grün; AC-03/04/06/07/08/18/28/29/30/33/37 abgedeckt, alte Fail-open-Erwartung bewusst invertiert; kein Produktionscode geändert; Step 4 (Commit) offen, kein Commit-Auftrag |
| 10 | Env-Pin für Framework-Subprozesse ausweiten | done | — (pending) | Steps 1–3 grün; beide Render-Seams rufen `tmp_env(paths)`, `work_dir_env` nur noch in `tmp_paths.py` (AST-Guard); 4 Plan-Dateien + 4 mechanische Test-Anpassungen (Signatur/Guard); 6 vorbestehende `gettempdir`-Rotmarks (nicht Task 10); Step 4 (Commit) offen, kein Commit-Auftrag |
| 11 | Subprozess-Klassifikation und Backup-Staging | done | — (pending) | Steps 1–3 grün; AC-09/10/11; Backup-Staging via `resolve_output_dir("backup-staging")`, Fallback nur bei `tmp-sink.disabled`; 10 der 12 bekannten Aufrufe gepinnt, 2 `taskkill` allowlisted; Guard scannt `scripts/**` (42 Ausreißer → 21 Allowlist-Einträge, u. a. `deferred` für Task-14-Datei); Step 4 (Commit) offen, kein Commit-Auftrag |
| 12 | Gitignore- und Doctor-Zweitparser entfernen | done | — (pending) | Steps 1–3 grün; AC-31/AC-32; `_tmp_sink_gitignore_entry(paths)` aus `TmpPaths.relative`, `_sink_hits` nutzt `resolve_tmp_paths` und übernimmt den Resolver-`reason`; AST-Guard gegen Zweitparser; Step 4 (Commit) offen, kein Commit-Auftrag |
| 13 | Opencode-Schreibscope aus dem Sink ableiten | done | — (pending) | Steps 1–3 grün; `edit_allow_paths` = `TmpPaths.relative`-Glob + statische `.meta-viz/**`-Liste; statische Liste auf `.meta-viz/**` reduziert; AC-17/AC-20; Step 4 (Commit) offen, kein Commit-Auftrag |
| 14 | Consistency-Check für Temp-Literale | done | — (pending) | Steps 1–3 grün; AC-21/IC-11; neues Modul `scripts/lib/consistency/temp_literals.py` ist Single Source des AC-01-Musters; Registrierung in `consistency-check.py` und im `_strict_findings`-Block (WARNING, Exit unverändert); Task-11-Schuld getilgt (2 Admin-Server-Starts mit `env=_admin_tmp_env`, beide `deferred:`-Einträge entfernt); 22 `temp-literal.system-temp`-WARNINGS sind ausschließlich Task-16-Goldens (echte Reste, kein False Positive); Step 4 (Commit) offen, kein Commit-Auftrag |
| 15 | Aggregations-Guard über alle Schreibpfade | pending | — (pending) | — |
| 16 | Goldens rebaselinen | pending | — (pending) | — |
| 17 | Doku und Beispiel-Config | pending | — (pending) | — |
| 18 | Abschluss-Validierung und Ledger | pending | — (pending) | Läuft zuletzt (Abschluss-Gate) |
| 19 | Toolchain-Cache-Opt-in (Q3) | pending | — (pending) | — |
| 20 | Antigravity `args.FilePath` → `file_path` (Q10) | done | — (pending) | Steps 1–3 grün; `ARG_KEY_MAP` um `'FilePath': 'file_path'` erweitert, Assertion in `test_adapter_normalizes_edit_tool_names`; 60 passed, `--validate` 0 neue Findings; Step 4 (Commit) offen, kein Commit-Auftrag |
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

## Evidence — Task 5

### Rot (vor der Template-Änderung)

`python3 -m pytest tests/test_template_report_paths.py -q` → Exit 1, `4 failed, 9 passed`:

```
    @pytest.mark.parametrize("role", WRITABLE_AUDITORS)
    def test_writable_auditor_reports_into_configured_sink(role):
        """AC-02: writable auditors write long reports into the configured tmp sink."""
        text = _read(role)
>       assert "{{TMP_SINK_PATH}}/" in text
E       assert '{{TMP_SINK_PATH}}/' in '---\nname: template-security-auditor\nversion: "2.7.0"\n
...
tests/test_template_report_paths.py:72: AssertionError
=========================== short test summary info ============================
FAILED tests/test_template_report_paths.py::test_writable_auditor_reports_into_configured_sink[ai-security-guardian]
FAILED tests/test_template_report_paths.py::test_writable_auditor_reports_into_configured_sink[app-lifecycle-governor]
FAILED tests/test_template_report_paths.py::test_writable_auditor_reports_into_configured_sink[prompt-governor]
FAILED tests/test_template_report_paths.py::test_writable_auditor_reports_into_configured_sink[security-auditor]
```

Zusätzlicher Nachweis der negativen Assertion (`.tmp/`-Muster) vor der Änderung:

```
ai-security-guardian: HIT `.tmp/ai-security-guardian-<topic>.md`
app-lifecycle-governor: HIT `.tmp/app-lifecycle-governor-<topic>.md`
prompt-governor: HIT `.tmp/prompt-governor-<topic>.md`
security-auditor: HIT `.tmp/security-auditor-<topic>.md`
```

### Grün (nach der Implementierung)

| # | Kommando | Ergebnis |
|---|---|---|
| 1 | `python3 -m pytest tests/test_template_report_paths.py -q` | `13 passed in 0.16s`, Exit 0 |
| 2 | `python3 -m pytest tests/test_temp_literals.py -q` | `4 passed in 0.21s` (Endstand nach Abschluss von Task 4; zum früheren Messzeitpunkt `1 failed, 3 passed`, weil Task 4 parallel noch in Arbeit war — Failure betraf ausschließlich dessen sieben Bash-Beispiel-Templates). `tests/test_tmp_sink_injection.py` existiert in diesem Branch noch nicht (Task 6) |
| 3 | `python3 scripts/sync.py --validate` | Exit 0; `4 action(s) \| 378 skipped \| 2 warning(s)` (beide Warnungen vorbestehend); 3–4 `WRITE`-Actions betreffen `app-lifecycle-governor` (einzige aktive Rolle der vier) in `.claude/.opencode/.gemini` — generierte Verzeichnisse sind gitignored, `--validate` fällt nach den Checks in den Sync-Pfad durch (vorbestehendes Verhalten, siehe Task 3) |
| 4 | `grep -rn "\.tmp/" agents/1-generic/{ai-security-guardian,app-lifecycle-governor,prompt-governor,security-auditor}.md config/routing/reviewers.yaml` | keine Treffer, Exit 1 |
| 5 | `python3 -m pytest tests/test_review_fleet.py -q` | `9 passed in 0.16s` (Consumer von `reviewers.yaml`) |
| 6 | Regression `python3 -m pytest tests/test_template_report_paths.py tests/test_template_slimming_equivalence.py -q` | `2 failed, 20 passed`, Exit 1 (Endstand, Task 4 abgeschlossen) — Details unten (erwartet) |

### Abgedeckte ACs (Task 5)

- **AC-02** — `test_writable_auditor_reports_into_configured_sink` (parametrisiert über
  `WRITABLE_AUDITORS`): jedes der vier Templates enthält `{{TMP_SINK_PATH}}/` und kein
  `` `\.tmp/<role>-<topic>.md` ``-Literal.

Geänderte Stellen: `ai-security-guardian.md:111`, `app-lifecycle-governor.md:100`,
`prompt-governor.md:120`, `security-auditor.md:217` jew. → `` `{{TMP_SINK_PATH}}/<role>-<topic>.md` ``;
Satzform und Backticks unverändert. `config/routing/reviewers.yaml:27-29` nennt statt des
`.tmp/`-Pfads jetzt den konfigurierten Sink (`` `{{TMP_SINK_PATH}}/` ``, ADR-10: kein Renderer).

### Slimming-Golden (erwartet rot, Rebaseline in Task 16)

`tests/test_template_slimming_equivalence.py` ist für Task 5 **nicht** angepasst (Golden
bleibt eingefroren). Baseline auf `HEAD db272453` (Archiv-Kopie): `1 failed, 8 passed`, rote
Rollen `documenter`, `e2e-tester`, `test-executor`, `tester` — vorbestehend, nicht von Task 5.
Mit den Task-5-Änderungen kommt **genau eine** Rolle hinzu: `app-lifecycle-governor`:

```
E       AssertionError: app-lifecycle-governor (agents/1-generic/app-lifecycle-governor.md): diff not attributable to declared normalizations
E         --- normalized/app-lifecycle-governor
E         +++ now/app-lifecycle-governor
E         @@ -1,6 +1,6 @@
E          ---
E          name: app-lifecycle-governor
E         -version: 1.4.0
E         +version: 1.4.1
E         @@ -14,7 +14,7 @@
E         -generated-from: 1-generic/app-lifecycle-governor.md@1.4.0
E         +generated-from: 1-generic/app-lifecycle-governor.md@1.4.1
```

Der inhaltliche Sink-Wechsel ist golden-invariant: der Renderer löst
`{{TMP_SINK_PATH}}` zu `.tmp` auf, das gerenderte Ergebnis bleibt byte-identisch zum
Golden. Rot ist ausschließlich der konventionspflichtige Patch-Version-Bump
(`agents/1-generic/*`: `1.4.0→1.4.1`, `1.5.1→1.5.2`, `2.7.0→2.7.1`), den Task 16 rebaselined.

Zusätzlich sind im **Arbeitsbaum-Messlauf** (parallel laufender Task 4) `code-reviewer`,
`developer` (`agent-meta-developer`), `devops-engineer`, `docker`, `tester`, `validator`
rot sowie `test_no_declared_normalization_is_dead` mit
`dead table entries: ['OG-PASS-CODE-REVIEWER']` — alle ausschließlich Task-4-Folgen
(Bash-Beispiel-Literale), nicht Task 5.

### Migrations-Verifikation (stabile Keys)

Stabile Keys: vier Rollen-Report-Ziele. Vorher je 1 Treffer
(`.tmp/<role>-<topic>.md`), nachher je 1 Treffer (`{{TMP_SINK_PATH}}/<role>-<topic>.md`):
**4 geprüft, 0 fehlend, 0 doppelt.** `.tmp/`-Treffer in den fünf Task-5-Dateien: **0**.

### Abweichungen von der Aufgabenbeschreibung

1. **Version-Bumps** (Konvention `conventions` → „Bump agent version in frontmatter on every
   content change", Patch): `ai-security-guardian 1.4.0→1.4.1`,
   `app-lifecycle-governor 1.4.0→1.4.1`, `prompt-governor 1.5.1→1.5.2`,
   `security-auditor 2.7.0→2.7.1`. Folge: `app-lifecycle-governor` wird im Golden rot
   (nur Versions-/`generated-from`-Zeilen, siehe oben).
2. **Test-Docstring** des Moduls mitgeführt: „inside the repo-containment area (`.tmp/`)" →
   „into the configured tmp sink (`{{TMP_SINK_PATH}}/`)" — reine Textangleichung an AC-02,
   keine Assertion-Änderung.
3. **Step 4 (Commit) nicht ausgeführt** — kein Commit-Auftrag für diesen Subagenten.

## Evidence — Task 4

### Rot (vor der Template-Änderung)

`python3 -m pytest tests/test_temp_literals.py -q` → Exit 1, `1 failed, 3 passed in 0.25s`:

```
____________________ test_no_system_temp_literal_in_agents _____________________

    def test_no_system_temp_literal_in_agents():
        """AC-01: ``agents/**/*.md`` carries no system temp literal."""
        hits = collect_hits()
>       assert not hits, (
            "system temp literal(s) found in agents/** (AC-01, ADR-06). Write to "
            "{{TMP_SINK_PATH}} instead, or declare a complete entry (path, pattern, "
            "reason) in .meta-config/temp-literal-allowlist.yaml:\n" + "\n".join(hits)
        )
E       AssertionError: system temp literal(s) found in agents/** (AC-01, ADR-06). Write to {{TMP_SINK_PATH}} instead, or declare a complete entry (path, pattern, reason) in .meta-config/temp-literal-allowlist.yaml:
E         agents/1-generic/code-reviewer.md:221: npm run lint > /tmp/lint.log 2>&1 &
E         agents/1-generic/code-reviewer.md:229: tail -50 /tmp/lint.log; exit "$RC"            # evidence + exit code = final result, not a "waiting" placeholder
E         agents/1-generic/developer.md:47: docker logs "$NAME" > /tmp/"$NAME".log 2>&1      # capture BEFORE removal
E         agents/1-generic/developer.md:50: - **Alternative (tee):** when a persistent named container is not appropriate: `docker run --rm <image> <cmd> 2>&1 | tee /tmp/run-$RANDOM.log` — the pipe keeps output even on non-zero exit.
E         agents/1-generic/developer.md:154: npm run e2e > /tmp/e2e.log 2>&1 &
E         agents/1-generic/developer.md:163: tail -50 /tmp/e2e.log; exit "$RC"             # evidence + exit code = final result, not a "waiting" placeholder
E         agents/1-generic/devops-engineer.md:202: docker logs "$NAME" > /tmp/"$NAME".log 2>&1   # capture diagnostics BEFORE removal
E         agents/1-generic/devops-engineer.md:204: echo "container exit code: $RC" && tail -20 /tmp/"$NAME".log
E         agents/1-generic/docker.md:128: docker logs "$NAME" > /tmp/"$NAME".log 2>&1   # capture diagnostics BEFORE removal
E         agents/1-generic/docker.md:130: echo "container exit code: $RC" && tail -20 /tmp/"$NAME".log
E         agents/1-generic/e2e-tester.md:154: docker logs "$NAME" > /tmp/"$NAME".log 2>&1   # capture diagnostics BEFORE removal
E         agents/1-generic/e2e-tester.md:156: echo "container exit code: $RC" && tail -20 /tmp/"$NAME".log
E         agents/1-generic/tester.md:71: docker logs "$NAME" > /tmp/"$NAME".log 2>&1      # capture BEFORE removal
E         agents/1-generic/tester.md:74: - **Alternative (tee):** when a persistent named container is not appropriate: `docker run --rm <image> <cmd> 2>&1 | tee /tmp/run-$RANDOM.log` — the pipe keeps output even on non-zero exit.
E         agents/1-generic/tester.md:141: docker logs "$NAME" > /tmp/"$NAME".log 2>&1   # capture diagnostics BEFORE removal
E         agents/1-generic/tester.md:143: echo "container exit code: $RC" && tail -20 /tmp/"$NAME".log
E         agents/1-generic/validator.md:76: docker logs "$NAME" > /tmp/"$NAME".log 2>&1      # capture BEFORE removal
E         agents/1-generic/validator.md:79: - **Alternative (tee):** when a persistent named container is not appropriate: `docker run --rm <image> <cmd> 2>&1 | tee /tmp/run-$RANDOM.log` — the pipe keeps output even on non-zero exit.
E       assert not ['agents/1-generic/code-reviewer.md:221: npm run lint > /tmp/lint.log 2>&1 &', ...]

tests/test_temp_literals.py:96: AssertionError
=========================== short test summary info ============================
FAILED tests/test_temp_literals.py::test_no_system_temp_literal_in_agents - A...
1 failed, 3 passed in 0.25s
```

18 Treffer, 7 Dateien — deckungsgleich mit der Planvorgabe.

### Grün (nach der Implementierung)

| # | Kommando | Ergebnis |
|---|---|---|
| 1 | `python3 -m pytest tests/test_temp_literals.py -q` | `4 passed in 0.52s`, Exit 0 |
| 2 | `python3 scripts/sync.py --validate` | Exit 0; `[PASS] All checks passed`, `3 action(s) \| 379 skipped \| 2 warning(s)` (beide vorbestehend: `active-set.gate-dropped`, Submodul-Checkout `external/awesome-claude-code`); kein `temp-literal.*`-Finding |
| 3 | `python3 scripts/sync.py --dry-run` | Exit 0; `30 action(s) \| 419 skipped \| 35 warning(s)` (35 Warnungen vorbestehend, siehe Task 3) |
| 4 | `grep -rn "/tmp/" agents/1-generic/` | keine Treffer (Exit 1); `grep -rn "/tmp/" agents/` ebenfalls **0** Treffer |
| 5 | `ast.parse(test_temp_literals.py, feature_version=(3, 9))` | `py3.9 syntax ok` |
| 6 | Regression `tests/test_temp_literals.py tests/test_agents_frontmatter.py tests/test_conventions_platform_cascade.py tests/test_template_integrity_checks.py` | `58 passed`, Exit 0 |
| 7 | Regression `tests/test_config_audit.py tests/test_platform_hacs_preset.py` | `61 passed`, Exit 0 |

Geänderte Stellen (Literal → Platzhalter, Pfadform unverändert, Padding unverändert):

| Template | Zeilen | Form |
|---|---|---|
| `developer.md` | 47, 50, 154, 163 | `docker logs "$NAME" > {{TMP_SINK_PATH}}/"$NAME".log 2>&1`, `tee {{TMP_SINK_PATH}}/run-$RANDOM.log`, `npm run e2e > {{TMP_SINK_PATH}}/e2e.log 2>&1 &`, `tail -50 {{TMP_SINK_PATH}}/e2e.log` |
| `code-reviewer.md` | 221, 229 | `lint.log` analog |
| `tester.md` | 71, 74, 141, 143 | `docker logs`/`tee`-Formen |
| `validator.md` | 76, 79 | `docker logs`/`tee`-Formen |
| `docker.md` | 128, 130 | `docker logs` + `tail -20` |
| `devops-engineer.md` | 202, 204 | `docker logs` + `tail -20` |
| `e2e-tester.md` | 154, 156 | `docker logs` + `tail -20` |

### Abgedeckte ACs (Task 4)

- **AC-01** — `test_no_system_temp_literal_in_agents` (exaktes AC-01-Muster
  `(^|[^A-Za-z0-9_.-])(/tmp/|%TEMP%|[A-Za-z]:\\\\Temp\\\\)`, Treffer mit `relpath:line: text`)
- **AC-01/AC-39-Schema** — `test_allowlist_file_exists_with_entry_list`,
  `test_incomplete_allowlist_entry_does_not_suppress` (Pflichtfelder `path`, `pattern`,
  `reason`; `owner` optional; `expires` ist kein Schema-Teil und unterdrückt nicht)
- **AC-01-Muster-Semantik** — `test_pattern_ignores_words_like_template_and_temporary`
  (Template/temporary/attempt sowie `my/tmp/x` matchen nicht, Pfadkontexte schon)

### Allowlist

`.meta-config/temp-literal-allowlist.yaml` neu: Kopfkommentar mit Schema (`path` als
Repo-Glob, `pattern` als Zeilen-Regex, `reason` Pflicht, `owner` optional, `expires` nicht
Teil des Schemas) plus `entries: []`. Task 22 härtet das Schema im Consistency-Check; der
Guard akzeptiert bereits nur vollständige Einträge.

### Migrations-Verifikation (stabile Keys)

Stabile Keys: 18 Literal-Schreibziele, 7 Template-Stems, 8 `based-on`-Pins.
Vorher 18 Literal-Sites → nachher 18 `{{TMP_SINK_PATH}}`-Sites
(`grep -c TMP_SINK_PATH`: 4+2+4+2+2+2+2): **18 geprüft, 0 fehlend, 0 doppelt**.
Template-Stems vorher/nachher identisch: **7 geprüft, 0 umbenannt, 0 fehlend**.
`based-on`-Pins: 8 vorher, 8 nachher, je auf die neue Basis-Version gesetzt: **0 fehlend**.
`/tmp/`-Treffer in `agents/`: **0** (vorher 18).

### Abweichungen von der Aufgabenbeschreibung

1. **Patch-Version-Bumps (Konvention, nicht im Plan-Files-Block):** `developer 4.8.0→4.8.1`,
   `code-reviewer 1.9.1→1.9.2`, `tester 2.7.0→2.7.1`, `validator 4.7.1→4.7.2`,
   `docker 1.9.0→1.9.1`, `devops-engineer 1.7.0→1.7.1`, `e2e-tester 1.6.0→1.6.1`.
   Ohne Bump meldet `--validate` `frontmatter.version-bump` (ERROR) für jede geänderte Datei.
2. **Kaskade in `agents/2-platform/` (8 Dateien außerhalb der Task-4-Files-Liste):** der
   Repo-Check `frontmatter.based-on-stale` (`scripts/lib/consistency/frontmatter.py:143`)
   vergleicht Pins als exakte Strings und ist ein ERROR. Deshalb `based-on` + eigener
   Patch-Bump: `hacs-developer 1.3.0→1.3.1`, `hacs-code-reviewer 2.0.0→2.0.1`,
   `hacs-tester 1.0.2→1.0.3`, `hacs-devops-engineer 1.0.0→1.0.1`,
   `sharkord-docker 1.2.3→1.2.4`, `agent-meta-developer 2.0.1→2.0.2`,
   `homeassistant-developer 2.1.1→2.1.2`, `sharkord-developer 3.0.1→3.0.2`; Pins jetzt
   `1-generic/developer.md@4.8.1`, `…/code-reviewer.md@1.9.2`, `…/tester.md@2.7.1`,
   `…/devops-engineer.md@1.7.1`, `…/docker.md@1.9.1`. Kein weiterer Cascade (nur
   `extends:`-Pfade ohne Version referenzieren die Overrides). Ohne diesen Schritt wäre
   `--validate` Exit 1 (8 ERRORs) — die Task-4-Verifikation verlangt Exit 0.
3. **Golden-/Baseline-Rebaseline bleibt bei Task 16** (explizit dessen Files-Liste):
   `tests/test_template_slimming_equivalence.py` → `2 failed, 7 passed`; zusätzlich ist
   `OG-PASS-CODE-REVIEWER` tot, weil die eingefrorene `inline=`-Kopie des Output-Guard-Blocks
   noch `/tmp/lint.log` enthält. `tests/test_ac01_render_identity.py` → `2 failed, 3 passed`
   (`tests/fixtures/ac01-baseline/hashes.json`). Beides sind eingefrorene Erwartungen, keine
   Verhaltensregression; Task 16 rebaselined sie.
4. **Step 4 (Commit) nicht ausgeführt** — kein Commit-Auftrag für diesen Subagenten.

### Risiko für Task 16

Zu rebaselinen: 7 Golden-Rollen (`developer`, `code-reviewer`, `tester`, `validator`,
`docker`, `devops-engineer`, `e2e-tester` + `agent-meta-developer`-Render) und die
`OG-PASS-CODE-REVIEWER`-Normalisierung (Bash-Beispiel auf `{{TMP_SINK_PATH}}` umstellen),
danach `tests/fixtures/ac01-baseline/hashes.json` neu erzeugen. Ohne Task 16 bleibt die
Suite bei den zwei eingefrorenen Modulen rot.

## Evidence — Task 6

### Rot (vor der Template-Änderung)

`python3 -m pytest tests/test_template_report_paths.py -q` → Exit 1, `13 failed, 13 passed in 0.25s`:

```
.............FFFFFFFFFFFFF                                               [100%]
=================================== FAILURES ===================================
________________ test_atomic_write_names_tmp_sink[se-architect] ________________

    @pytest.mark.parametrize("role", ATOMIC_WRITE_ROLES)
    def test_atomic_write_names_tmp_sink(role):
        """AC-22: the atomic-write/scratch instruction names the configured sink."""
        text = _read(role)
>       assert "{{TMP_SINK_PATH}}" in text
E       assert '{{TMP_SINK_PATH}}' in '---\nname: se-architect\nversion: 2.2.1\n...'
tests/test_template_report_paths.py:100: AssertionError
...
FAILED tests/test_template_report_paths.py::test_atomic_write_names_tmp_sink[se-architect]
FAILED tests/test_template_report_paths.py::test_atomic_write_names_tmp_sink[se-component-requirements]
FAILED tests/test_template_report_paths.py::test_atomic_write_names_tmp_sink[se-critic]
FAILED tests/test_template_report_paths.py::test_atomic_write_names_tmp_sink[se-developer]
FAILED tests/test_template_report_paths.py::test_atomic_write_names_tmp_sink[se-integration-and-test-manager]
FAILED tests/test_template_report_paths.py::test_atomic_write_names_tmp_sink[se-interface-mgr]
FAILED tests/test_template_report_paths.py::test_atomic_write_names_tmp_sink[se-junior-developer]
FAILED tests/test_template_report_paths.py::test_atomic_write_names_tmp_sink[se-requirements]
FAILED tests/test_template_report_paths.py::test_atomic_write_names_tmp_sink[se-senior-developer]
FAILED tests/test_template_report_paths.py::test_atomic_write_names_tmp_sink[se-termination]
FAILED tests/test_template_report_paths.py::test_atomic_write_names_tmp_sink[se-validator]
FAILED tests/test_template_report_paths.py::test_atomic_write_names_tmp_sink[se-verifier]
FAILED tests/test_template_report_paths.py::test_atomic_write_names_tmp_sink[test-executor]
13 failed, 13 passed in 0.25s
```

Alle 13 Rollen rot, deckungsgleich mit der Planvorgabe (12 SE-Rollen + `test-executor`).

### Grün (nach der Implementierung)

| # | Kommando | Ergebnis |
|---|---|---|
| 1 | `python3 -m pytest tests/test_template_report_paths.py -q` | `26 passed in 0.18s`, Exit 0 |
| 2 | `python3 -m pytest tests/test_temp_literals.py -q` | `4 passed in 0.21s`, Exit 0 |
| 3 | `python3 scripts/sync.py --validate` | Exit 0; `4 action(s) \| 378 skipped \| 2 warning(s)` im ersten Lauf (die WRITE-Actions sind die Regeneration von `test-executor`-Output, generierte Verzeichnisse sind gitignored); Wiederholungslauf `0 action(s) \| 382 skipped \| 2 warning(s)`. Beide Warnungen vorbestehend (`active-set.gate-dropped 'se-component-requirements'`, Submodul-Checkout `external/awesome-claude-code`); `grep -c "\[ERROR\]"` = **0**, kein `frontmatter.*`-ERROR |
| 4 | `grep -rn "to a temporary file\|temp → rename\|\.tmp/" agents/1-generic/ rules/1-generic/plan-ledger.md` | keine Treffer, Exit 1 (0 legitime Rest-Treffer) |
| 5 | `ast.parse(tests/test_template_report_paths.py, feature_version=(3, 9))` | `py3.9 syntax ok` |
| 6 | Regression `python3 -m pytest tests/test_review_fleet.py tests/test_template_report_paths.py -q` | `35 passed in 0.31s`, Exit 0 |
| 7 | Zusatz `tests/test_agents_frontmatter.py tests/test_conventions_platform_cascade.py tests/test_template_integrity_checks.py tests/test_review_fleet.py tests/test_template_report_paths.py tests/test_temp_literals.py` | `93 passed`, Exit 0 |
| 8 | Zusatz `tests/test_se_persistence.py tests/test_se_role_boundary.py tests/test_se_validate.py tests/test_active_set.py` | `124 passed`, Exit 0 (separat; `test_active_set_dangling.py` `40 passed` in 214 s, vorbestehend langsam) |
| 9 | `python3 scripts/consistency-check.py --changed` | Exit 0, `[PASS] All checks passed` — der `frontmatter.version-bump`-Guard ist nur im `--changed`-Modus aktiv (`cli_commands.py:179` ruft `changed_only=False`); damit sind alle 13 Patch-Bumps explizit nachgewiesen |

### Abgedeckte ACs (Task 6)

- **AC-22** — `test_atomic_write_names_tmp_sink`, parametrisiert über 13 Rollen
  (`ATOMIC_WRITE_ROLES` = 12 SE-Rollen + `test-executor`): jede Rolle enthält
  `{{TMP_SINK_PATH}}`; zusätzlich für jeden „Atomic write"-Absatz (blank-line-separierter
  Block) die Negative-Assertion `re.search(r"to a temporary file|temp → rename", block)
  is None`. Die Assertion ist auf den Atomic-Write-Block gescoped (kein Blanket-Ban im
  restlichen Template) — `test-executor` hat keinen solchen Block und wird nur auf die
  Sink-Nennung geprüft.

### Geänderte Stellen

| Template | Form nachher |
|---|---|
| `se-developer.md` | `1. Write implementation summary (…) to `{{TMP_SINK_PATH}}/se-developer-<topic>.md`` / `2. Rename the file from the sink to the target path (atomic write)` |
| `se-junior-developer.md` | analog `se-junior-developer-<topic>.md` |
| `se-integration-and-test-manager.md` | `1. Write full output (frontmatter + JSON integration plan) to `{{TMP_SINK_PATH}}/se-integration-and-test-manager-<topic>.json`` / Schritt 2 wie oben |
| `se-interface-mgr.md` | analog `…-<topic>.json` (Liste „JSON + human-readable table" unverändert) |
| `se-termination.md` | analog `…-<topic>.json` („JSON + decision summary") |
| `se-validator.md` | analog `…-<topic>.json` |
| `se-verifier.md` | analog `…-<topic>.json` |
| `se-architect.md` | `**Atomic write:** write to `{{TMP_SINK_PATH}}/se-architect-<topic>.md` → rename → `.se-state.yaml` aktualisieren.` |
| `se-component-requirements.md` | dito, `.md`; `.se-state.yaml`-Zellsatz + Issue-#334-Satz unverändert |
| `se-critic.md` | `write to `…-<topic>.md` → rename → Protokoll → Endreport → REQ-Frontmatter-Sync (…) → `.se-state.yaml`` |
| `se-requirements.md` | dito, `.md`; Issue-#334-Satz unverändert |
| `se-senior-developer.md` | dito, `.md` |
| `test-executor.md:30` | „… ephemeral run artifacts the suite itself produces (logs, reports) under `{{TMP_SINK_PATH}}/runs/`." |
| `test-executor.md:87` | „`docker wait`, log capture (`{{TMP_SINK_PATH}}/runs/` only)" |
| `rules/1-generic/plan-ledger.md:67` | „… Schreiben nur im Projektroot und im konfigurierten Scratch-Sink (`{{TMP_SINK_PATH}}/`)." |

### Migrations-Verifikation (stabile Keys)

Stabile Keys: 13 Rollen-Stems + 1 Regel-Datei. Vorher 13 vage Anweisungen
(`to a temporary file` ×7, `temp → rename` ×5) + 1 `.tmp/`-Literal; nachher 13
`{{TMP_SINK_PATH}}`-Nennungen + 1 `{{TMP_SINK_PATH}}/`-Nennung:
**14 geprüft, 0 fehlend, 0 doppelt**; Artefakt-Erweiterungen (`.md` ×7, `.json` ×5) und
die `.se-state.yaml`-Folgesätze je Rolle unverändert. `2-platform`-Cascade: **0** —
`grep -rn "based-on:" agents/2-platform/` enthält keine der 13 Rollen, und
`grep -rln "se-…\|test-executor" agents/2-platform/` liefert keine Treffer
(keine `extends:`/`patches:`-Kinder).

### Slimming-Golden (erwartet rot, Rebaseline in Task 16)

`tests/test_template_slimming_equivalence.py` bleibt unangetastet:
`2 failed, 7 passed` — identisch zur Task-4/5-Baseline (kein neuer roter Rollen-Satz).
Rote Rollen: `app-lifecycle-governor`, `code-reviewer`, `developer`, `devops-engineer`,
`docker`, `documenter`, `e2e-tester`, `test-executor`, `tester`, `validator` — alle
vorbestehend aus Task 3/4/5; **keine** `se-*`-Rolle ist im Golden-Set. Der
`test-executor`-Diff bleibt auf Version/`generated-from` plus die vorbestehende
Task-3-Kommando-Differenz beschränkt (Renderer löst `{{TMP_SINK_PATH}}` zu `.tmp` auf,
der Sink-Satz selbst ist golden-invariant).

### Abweichungen von der Aufgabenbeschreibung

1. **Wortlaut der Rollen:** Die Plan-Vorgabe „Write the full output to …, then rename to the target path
   (atomic write)" ist als `e.g.` gekennzeichnet und daher nicht bindend. Um die Doppelung mit
   dem bereits vorhandenen Schritt 2 („Rename temp file to target path") zu vermeiden, nennen die
   sieben Nummern-Listen-Rollen den Sink in Schritt 1 und Schritt 2 lautet jetzt „Rename the file
   from the sink to the target path (atomic write)". Die fünf `**Atomic write:** temp → rename …`-
   Einzeiler behalten ihre Bullet-Form (Plan Step 2: „keep the existing bullet shape") und bekommen
   `write to `{{TMP_SINK_PATH}}/…` → rename → …` vorangestellt. Die `.se-state.yaml`-Kette und alle
   Zusatzsätze bleiben wörtlich erhalten.
2. **`test-executor` hat keinen Atomic-Write-Absatz** — der Test prüft dort nur die
   Sink-Nennung (beide Stellen `:30`, `:87`), die Negativ-Assertion greift nur, wenn ein
   Atomic-Write-Block existiert.
3. **Kein `2-platform`-Cascade** (im Gegensatz zu Task 4): keine Plattform-Override pinnt
   eine der 13 Rollen, daher nur die 13 Patch-Bumps der `1-generic`-Templates.
   `rules/1-generic/plan-ledger.md` hat kein Frontmatter → kein Versionsbump.
4. **Step 4 (Commit) nicht ausgeführt** — kein Commit-Auftrag für diesen Subagenten
   (Branch-Guard/Commit-Authority bleiben beim Orchestrator).

## Evidence — Task 7

### Rot (vor der Implementierung/Regeneration)

`python3 -m pytest tests/test_standalone_render.py tests/test_temp_literals.py -q`
→ Exit 1, `2 failed, 4 passed in 0.43s`:

```
______________________ test_tmp_sink_path_uses_framework_default ______________

>       assert not offenders, (
            "TMP_SINK_PATH rendered as a placeholder note in standalone/** (AC-27, IC-15). "
            "Set TMP_SINK_PATH = '.tmp' in standalone.py::_standalone_variables:\n"
            + "\n".join(offenders)
        )
E       AssertionError: TMP_SINK_PATH rendered as a placeholder note in standalone/** (AC-27, IC-15). Set TMP_SINK_PATH = '.tmp' in standalone.py::_standalone_variables:
E         standalone/agents/agent-meta-manager.md:288: python3 [AGENT_META_REL_PATH — not available outside a full agent-meta install]scripts/sync.py --optimize-config --json --out [TMP_SINK_PATH — not available outside a full agent-meta install]/meta-optimizer/<ts>/
E         standalone/agents/meta-doctor.md:23: - Report targets are exclusively `[TMP_SINK_PATH — not available outside a full agent-meta install]/doctor/` (`--doctor --out`) and
E         standalone/agents/meta-doctor.md:24: `[TMP_SINK_PATH — not available outside a full agent-meta install]/context-report/` (`--context-report --json`). The runner writes those files, not you:
E         standalone/agents/meta-doctor.md:43: python3 [AGENT_META_REL_PATH — not available outside a full agent-meta install]scripts/sync.py --doctor --json --out [TMP_SINK_PATH — not available outside a full agent-meta install]/doctor/<YYYYMMDD-HHMMSS>.json
E         standalone/agents/meta-doctor.md:55: `[TMP_SINK_PATH — not available outside a full agent-meta install]/doctor/`; any other target is rejected by the runner (`doctor.out-outside-tmp-sink`, exit 2).
E         standalone/agents/meta-doctor.md:65: 1. **Doctor run:** `--doctor --json --out [TMP_SINK_PATH — not available outside a full agent-meta install]/doctor/<ts>.json` (timestamp `YYYYMMDD-HHMMSS`).
E         standalone/agents/meta-doctor.md:106: ARTIFACTS: <paths, e.g. [TMP_SINK_PATH — not available outside a full agent-meta install]/doctor/<ts>.json, or none>
E         standalone/agents/meta-doctor.md:128: - Never repair, never edit files, never write outside `[TMP_SINK_PATH — not available outside a full agent-meta install]/doctor/` and
E         standalone/agents/meta-doctor.md:129: `[TMP_SINK_PATH — not available outside a full agent-meta install]/context-report/`; no `Write`/`Edit`.
E         standalone/agents/meta-optimizer.md:32: The executing step belongs to `agent-meta-manager` (IC-27): it runs `sync.py --optimize-config --json --out [TMP_SINK_PATH — not available outside a full agent-meta install]/meta-optimizer/<ts>/` and returns the artifact paths. This role has no Bash and executes nothing.
E         standalone/agents/meta-optimizer.md:64: text — `ARTIFACTS: none`. The executing step is `agent-meta-manager`'s: it runs `sync.py --optimize-config --json --out [TMP_SINK_PATH — not available outside a full agent-meta install]/meta-optimizer/<ts>/`, later the mandatory preview (`sync.py --apply-config-patch ... --dry-run`) and the apply (`--preview`, after the user confirms the preview). This role executes nothing and writes nothing.
E         standalone/agents/meta-optimizer.md:80: ARTIFACTS: none (input read: [TMP_SINK_PATH — not available outside a full agent-meta install]/meta-optimizer/<ts>/proposal.json)
E       assert not ['standalone/agents/agent-meta-manager.md:288: python3 [AGENT_META_REL_PATH — not available outside a full agent-meta ...MP_SINK_PATH — not available outside a full agent-meta install]/doctor/<ts>.json` (timestamp `YYYYMMDD-HHMMSS`).', ...]

tests/test_standalone_render.py:51: AssertionError

___________________ test_no_system_temp_literal_in_standalone ___________________

>       assert not hits, (
            "system temp literal(s) found in standalone/** (AC-26). Regenerate after "
            "fixing the source template (`python3 scripts/sync.py --render-standalone`):\n"
            + "\n".join(hits)
        )
E       AssertionError: system temp literal(s) found in standalone/** (AC-26). Regenerate after fixing the source template (`python3 scripts/sync.py --render-standalone`):
E         standalone/agents/code-reviewer.md:206: npm run lint > /tmp/lint.log 2>&1 &
E         standalone/agents/code-reviewer.md:214: tail -50 /tmp/lint.log; exit "$RC"            # evidence + exit code = final result, not a "waiting" placeholder
E         standalone/agents/developer.md:30: docker logs "$NAME" > /tmp/"$NAME".log 2>&1      # capture BEFORE removal
E         standalone/agents/developer.md:33: - **Alternative (tee):** when a persistent named container is not appropriate: `docker run --rm <image> <cmd> 2>&1 | tee /tmp/run-$RANDOM.log` — the pipe keeps output even on non-zero exit.
E         standalone/agents/developer.md:130: npm run e2e > /tmp/e2e.log 2>&1 &
E         standalone/agents/developer.md:139: tail -50 /tmp/e2e.log; exit "$RC"             # evidence + exit code = final result, not a "waiting" placeholder
E         standalone/agents/devops-engineer.md:185: docker logs "$NAME" > /tmp/"$NAME".log 2>&1   # capture diagnostics BEFORE removal
E         standalone/agents/devops-engineer.md:187: echo "container exit code: $RC" && tail -20 /tmp/"$NAME".log
E         standalone/agents/docker.md:115: docker logs "$NAME" > /tmp/"$NAME".log 2>&1   # capture diagnostics BEFORE removal
E         standalone/agents/docker.md:117: echo "container exit code: $RC" && tail -20 /tmp/"$NAME".log
E         standalone/agents/e2e-tester.md:126: docker logs "$NAME" > /tmp/"$NAME".log 2>&1   # capture diagnostics BEFORE removal
E         standalone/agents/e2e-tester.md:128: echo "container exit code: $RC" && tail -20 /tmp/"$NAME".log
E         standalone/agents/tester.md:55: docker logs "$NAME" > /tmp/"$NAME".log 2>&1      # capture BEFORE removal
E         standalone/agents/tester.md:58: - **Alternative (tee):** when a persistent named container is not appropriate: `docker run --rm <image> <cmd> 2>&1 | tee /tmp/run-$RANDOM.log` — the pipe keeps output even on non-zero exit.
E         standalone/agents/tester.md:125: docker logs "$NAME" > /tmp/"$NAME".log 2>&1   # capture diagnostics BEFORE removal
E         standalone/agents/tester.md:127: echo "container exit code: $RC" && tail -20 /tmp/"$NAME".log
E         standalone/agents/validator.md:47: docker logs "$NAME" > /tmp/"$NAME".log 2>&1      # capture BEFORE removal
E         standalone/agents/validator.md:50: - **Alternative (tee):** when a persistent named container is not appropriate: `docker run --rm <image> <cmd> 2>&1 | tee /tmp/run-$RANDOM.log` — the pipe keeps output even on non-zero exit.
E       assert not ['standalone/agents/code-reviewer.md:206: npm run lint > /tmp/lint.log 2>&1 &', ...]

tests/test_temp_literals.py:117: AssertionError
=========================== short test summary info ============================
FAILED tests/test_standalone_render.py::test_tmp_sink_path_uses_framework_default
FAILED tests/test_temp_literals.py::test_no_system_temp_literal_in_standalone
2 failed, 4 passed in 0.43s
```

Deckungsgleich mit der Planvorgabe: 12 `TMP_SINK_PATH`-Notizen in drei Dateien,
18 AC-01-Treffer in sieben Dateien.

### Grün (nach der Implementierung)

| # | Kommando | Ergebnis |
|---|---|---|
| 1 | `python3 -m pytest tests/test_standalone_render.py tests/test_temp_literals.py -q` | `6 passed in 0.42s`, Exit 0 |
| 2 | `python3 scripts/sync.py --render-standalone --check` | Exit 0; `OK  standalone/ is up to date (91 file(s))` (die `!  Variable … not in config`-Zeilen sind vorbestehende Standalone-Safety-Nets anderer Platzhalter, keine Drift) |
| 3 | `python3 scripts/sync.py --render-standalone` | `23 written \| 0 removed \| 68 unchanged \| 90 role(s)`; Wiederholung im `--check`-Modus: `0 written` |
| 4 | `python3 scripts/sync.py --validate` | Exit 0; `0 action(s) \| 382 skipped \| 2 warning(s)` (beide vorbestehend: `active-set.gate-dropped`, Submodul-Checkout `external/awesome-claude-code`) |
| 5 | `grep -rn "not available outside a full agent-meta install" standalone/agents/{meta-doctor,meta-optimizer,agent-meta-manager}.md` | Treffer nur für **andere** Platzhalter (`AGENT_META_REL_PATH`, `EXTENSION_DIR`, `SKILLS_DIR`, `CONTEXT_FILE`, `PROMPT_INJECTION_DEFENSE_BLOCK`, `OUTPUT_GUARD_BLOCK`) — vorbestehen, nicht Task-7-Scope (siehe Abweichung 1) |
| 6 | `grep -rn "\[TMP_SINK_PATH — not available outside a full agent-meta install\]" standalone/` | keine Treffer, Exit 1 |
| 7 | `grep -rn "{{TMP_SINK_PATH}}\|{{TMP_SINK_ENV_PIN_BLOCK}}\|{{PYTEST_BASETEMP}}" standalone/` | keine Treffer, Exit 1 |
| 8 | `grep -Prn "/home/\|/Users/\|/tmp/" standalone/` | 0 Treffer (kein Maschinenpfad im Export) |
| 9 | Regression `python3 -m pytest tests/test_standalone_render.py tests/test_temp_literals.py tests/test_standalone_export_in_sync.py -q` | `7 passed in 3.85s`, Exit 0 |
| 10 | Regression `python3 -m pytest tests/test_meta_doctor_role.py tests/test_meta_optimizer_role.py -q` | `61 passed in 1.78s`, Exit 0 |
| 11 | `python3 -m pytest tests/test_ac01_render_identity.py -q` | `2 failed, 3 passed` — **vorbestehend** aus Task 4/5 (Hash-Manifest `tests/fixtures/ac01-baseline/hashes.json`), Rebaseline ist Task 16; Task 7 rendert nur `standalone/**`, nicht `.claude/**` |

### Standalone-Diff (23 Dateien, je 1:1-Zeilenersetzung)

| Datei | Δ | Begründung |
|---|---|---|
| `meta-doctor.md` | 8 | 8 `[TMP_SINK_PATH — …]`-Notizen → `.tmp/doctor/`, `.tmp/context-report/` (AC-27) |
| `meta-optimizer.md` | 3 | 3 Notizen → `.tmp/meta-optimizer/<ts>/` bzw. `…/proposal.json` (AC-27) |
| `agent-meta-manager.md` | 1 | 1 Notiz → `.tmp/meta-optimizer/<ts>/` (AC-27) |
| `developer.md` | 4 | 4 `/tmp/`-Beispiele → `.tmp/` (Task 4) |
| `code-reviewer.md` | 2 | 2 `/tmp/`-Beispiele → `.tmp/` (Task 4) |
| `tester.md` | 4 | 4 `/tmp/`-Beispiele → `.tmp/` (Task 4) |
| `validator.md` | 2 | 2 `/tmp/`-Beispiele → `.tmp/` (Task 4) |
| `docker.md` | 2 | 2 `/tmp/`-Beispiele → `.tmp/` (Task 4) |
| `devops-engineer.md` | 2 | 2 `/tmp/`-Beispiele → `.tmp/` (Task 4) |
| `e2e-tester.md` | 2 | 2 `/tmp/`-Beispiele → `.tmp/` (Task 4) |
| `se-architect.md` | 1 | `temp → rename` → `write to .tmp/se-architect-<topic>.md → rename` (Task 6) |
| `se-component-requirements.md` | 1 | analog (Task 6) |
| `se-critic.md` | 1 | analog (Task 6) |
| `se-developer.md` | 2 | Nummernliste Schritt 1/2 auf `.tmp/se-developer-<topic>.md` (Task 6) |
| `se-integration-and-test-manager.md` | 2 | analog `.json` (Task 6) |
| `se-interface-mgr.md` | 2 | analog `.json` (Task 6) |
| `se-junior-developer.md` | 2 | analog `.md` (Task 6) |
| `se-requirements.md` | 1 | analog (Task 6) |
| `se-senior-developer.md` | 1 | analog (Task 6) |
| `se-termination.md` | 2 | analog `.json` (Task 6) |
| `se-validator.md` | 2 | analog `.json` (Task 6) |
| `se-verifier.md` | 2 | analog `.json` (Task 6) |
| `test-executor.md` | 2 | `.tmp/runs/` statt „scratch/output path" (Task 6) |

**Nicht** geändert (erwartet): `ai-security-guardian.md`, `app-lifecycle-governor.md`,
`prompt-governor.md`, `security-auditor.md` — Task 5 ersetzte dort `.tmp/<role>-…` durch
`{{TMP_SINK_PATH}}/…`, das Standalone zu `.tmp/<role>-…` rendert: **byte-identisch** zum
vorherigen Export, also 0 Diff. `standalone/README.md` unverändert (keine Rollen-/Versionsänderung).

### Abgedeckte ACs (Task 7)

- **AC-27 / IC-15** — `test_tmp_sink_path_uses_framework_default`: keine
  `[TMP_SINK_PATH — not available outside a full agent-meta install]`-Notiz in
  `standalone/**`; die drei Rollen nennen `.tmp/doctor/`, `.tmp/context-report/` bzw.
  `.tmp/meta-optimizer/<ts>/`; kein rohes `{{TMP_SINK_PATH}}`.
- **AC-26** — `test_no_system_temp_literal_in_standalone`: exakt das AC-01-Muster aus
  `tests/test_temp_literals.py` (keine zweite Musterquelle; der Scanner ist als
  `_collect_hits_under(root)` geteilt, Task 15 konsolidiert ihn nach
  `scripts/lib/consistency/temp_literals.py`) ⇒ 0 Treffer in `standalone/**`; Drift-Gate
  `--render-standalone --check` Exit 0.

### Migrations-Verifikation (stabile Keys)

Stabile Keys: 12 `TMP_SINK_PATH`-Render-Stellen (8 `meta-doctor`, 3 `meta-optimizer`,
1 `agent-meta-manager`) und 18 `/tmp/`-Sites (7 Rollen). Vorher 12 Notizen → nachher
12 `.tmp`-Ziele: **12 geprüft, 0 fehlend, 0 doppelt**. Vorher 18 `/tmp/`-Sites →
nachher 18 `.tmp/`-Sites: **18 geprüft, 0 fehlend, 0 doppelt**. Keine Rollendatei
verschwunden (`--render-standalone --check`: 91 Dateien, 90 Rollen unverändert).

### Abweichungen von der Aufgabenbeschreibung

1. **Verifikations-Grep 5 ist gescoped, nicht global.** Der wörtliche Grep über die drei
   Dateien liefert weiter Treffer — aber ausschließlich für **andere** Platzhalter
   (`AGENT_META_REL_PATH`, `EXTENSION_DIR`, `SKILLS_DIR`, `CONTEXT_FILE`,
   `PROMPT_INJECTION_DEFENSE_BLOCK`, `OUTPUT_GUARD_BLOCK`), die schon vor Task 7 dort
   standen. AC-27/IC-15 verbieten nur die `TMP_SINK_PATH`-Notiz; deren Grep ist 0.
   Ein globales Entfernen aller Notizen wäre ein eigener, nicht beauftragter Task.
2. **`TMP_SINK_ABS_PATH`/`PYTEST_BASETEMP` bewusst nicht gesetzt.** Geprüft:
   `agents/`, `rules/`, `snippets/` enthalten **0** Referenzen auf
   `{{TMP_SINK_ABS_PATH}}`, `{{PYTEST_BASETEMP}}` oder `{{TMP_SINK_ENV_PIN_BLOCK}}`;
   die absoluten Werte gelangen nur über projekt-konfigurierte
   `DEV_COMMANDS`/`TEST_COMMANDS` in Templates, und Standalone ersetzt diese durch
   neutrale „ask the user"-Fallbacks. Beide Variablen würden einen Maschinenpfad in den
   Export schreiben (IC-13) — sie bleiben deshalb abwesend. `TMP_SINK_ENV_PIN_BLOCK=""`
   ist wie im Plan gesetzt (leer, kein Pfad).
3. **`.tmp/` bleibt in `standalone/**` sichtbar** (4 Auditor- + 3 Meta-Rollen). Das ist
   der von AC-27 verlangte Framework-Default-Sink, nicht das in Templates verbotene
   `.tmp/<role>-`-Literal; der Guard prüft deshalb nur das AC-01-Muster (System-Temp).
4. **`tests/test_ac01_render_identity.py` bleibt rot** (`2 failed`) — vorbestehend aus
   Task 3/4/5 (eingefrorenes Hash-Manifest), Rebaseline ist Task 16. Task 7 ändert nur
   `standalone/**`, nicht die gerenderten `.claude/**`-Dateien.
5. **Step 4 (Commit) nicht ausgeführt** — kein Commit-Auftrag für diesen Subagenten.

## Evidence — Task 8

### Rot (vor der Implementierung)

`python3 -m pytest tests/test_repo_containment_hook.py -q` → Exit 1, `1 failed, 32 passed`:

```
_______________ test_cwd_outside_project_cannot_be_adopted ___________________

external_fixture = PosixPath('/tmp/am-hook-ext-pohrevg9')

    def test_cwd_outside_project_cannot_be_adopted(external_fixture):
        """AC-05: a `cwd` outside any project must never be promoted to a root.

        The regression the hook carried until Task 8: with ``cwd=/tmp`` and target
        ``/tmp/x.py`` it adopted ``$PWD``/``cwd`` as the repo root and allowed the
        write (exit 0) because the target was "inside" that fake root.
        """
        target = external_fixture / "x.py"
        result = _run_hook(_write_payload(target, external_fixture))
>       assert result.returncode == 2, result.stderr
E       AssertionError:
E       assert 0 == 2
E        +  where 0 = CompletedProcess(args=['/usr/bin/bash', '/home/hermes/repos/agent-meta/hooks/1-generic/repo-containment.sh'], returncode=0, stdout='', stderr='').returncode

tests/test_repo_containment_hook.py:270: AssertionError
=========================== short test summary info ============================
FAILED tests/test_repo_containment_hook.py::test_cwd_outside_project_cannot_be_adopted
1 failed, 32 passed in 10.80s
```

Der Hook lieferte Exit 0 (Fail-open): `resolve_repo_root` fand keinen `.meta-config/`-Ancestor
und adelte `cwd`/`$PWD` selbst zum Root. AC-33 und der Paritätstest sind Regressionswächter und
waren schon vor der Änderung grün.

### Grün (nach der Implementierung)

| # | Kommando | Ergebnis |
|---|---|---|
| 1 | `python3 -m pytest tests/test_repo_containment_hook.py -q` | `33 passed in 14.42s`, Exit 0 |
| 2 | `python3 -m pytest tests/test_antigravity_hooks_registration.py tests/test_tmp_sink_path_parity.py tests/test_tmp_sink_path_hardening.py -q` | `238 passed in 6.69s`, Exit 0 |
| 3 | `python3 -m pytest tests/test_repo_containment_hook.py tests/test_repo_containment_consistency.py tests/test_tmp_sink_path_parity.py tests/test_tmp_sink_path_hardening.py tests/test_antigravity_hooks_registration.py -q` | `284 passed in 24.55s`, Exit 0 |
| 4 | `python3 -m pytest tests/test_runtime_config_readers.py tests/test_hook_registration_invariant.py tests/test_doctor_runner.py -q` | `105 passed`, Exit 0 (nach Reparatur der Evidence-Zeile, siehe Abweichung 4) |
| 5 | `python3 scripts/sync.py --validate` | Exit 0; 0 × `hooks.stale-deployed-version`, 2 vorbestehende WARNINGS (`active-set.gate-dropped`, Submodul-Checkout `external/awesome-claude-code`) |
| 6 | `bash -n hooks/1-generic/repo-containment-impl.sh` | Exit 0 |
| 7 | `bash -n hooks/1-generic/repo-containment.sh` | Exit 0 (Wrapper unverändert — keine Versions-/Hash-Bindung an die Impl) |

### Manuelle Nachweise (Impl direkt, ohne Wrapper)

```
$ printf '{"tool_name":"Write","tool_input":{"file_path":"/tmp/x.py"},"cwd":"/tmp"}' | bash hooks/1-generic/repo-containment-impl.sh
REPO_CONTAINMENT: no project root found above /tmp (code repo-containment.no-root).
  A project root is a directory that contains `.meta-config/`.
  This guard never promotes the working directory to a project root.
  target:    /tmp/x.py
  anchor:    /tmp            (payload `cwd`, or the target's own directory when `cwd` is missing)
  allowed:   only inside a project root (plus its configured tmp-sink)
  repair:    run `python scripts/sync.py` in the project, or open the session
             inside the project directory
  opt-out:   repo_containment.enabled: false in <project>/.meta-config/project.yaml
exit=2

$ printf '{"tool_name":"Write","tool_input":{"file_path":"/tmp/am-manual-aSWBjd/x.py"}}' | bash hooks/1-generic/repo-containment-impl.sh
REPO_CONTAINMENT: no project root found above /tmp/am-manual-aSWBjd (code repo-containment.no-root).
  A project root is a directory that contains `.meta-config/`.
  This guard never promotes the working directory to a project root.
  target:    /tmp/am-manual-aSWBjd/x.py
  anchor:    /tmp/am-manual-aSWBjd            (payload `cwd`, or the target's own directory when `cwd` is missing)
  allowed:   only inside a project root (plus its configured tmp-sink)
  repair:    run `python scripts/sync.py` in the project, or open the session
             inside the project directory
  opt-out:   repo_containment.enabled: false in <project>/.meta-config/project.yaml
exit=2

$ printf '{"tool_name":"Write","tool_input":{"file_path":"notes.md"}}' | bash hooks/1-generic/repo-containment-impl.sh
REPO_CONTAINMENT: no project root found for a relative target without `cwd`
(code repo-containment.no-root).
  A relative path cannot be anchored: the payload carried no `cwd` (or an empty one)
  and the target is not absolute. Failing closed.
  target:    notes.md
  repair:    re-run `python scripts/sync.py` for this provider (hook payload contract, issue #630);
             send an absolute `file_path`, or include `cwd` in the payload
exit=2
```

Zusätzliche Handproben (nicht Teil der drei geforderten Transkripte):

| Fall | Ergebnis |
|---|---|
| fremdes Projekt mit `enabled: false`, `cwd` = sein Unterbaum, Ziel in ihm | Exit 0 (Opt-out bleibt projektlokal) |
| dasselbe Opt-out, aber `cwd=/tmp`, Ziel `/tmp/y.py` | Exit 2 `repo-containment.no-root` (Root-Auflösung vor Opt-out) |
| leerer `cwd`, absolutes Ziel in einem fremden Projekt | Exit 0 (Anker aus Zielverzeichnis, AC-37-Verhalten) |
| leerer `cwd`, absolutes Ziel im echten Projektroot | Exit 0 (AC-28-Verhalten) |
| `Bash` ohne `cwd` (`ls -la`) | Exit 2 `repo-containment.no-root` (dokumentierte Auslegung, siehe Abweichung 2) |

### Abgedeckte ACs (Task 8)

- **AC-05** — `test_cwd_outside_project_cannot_be_adopted`: Fixture aus
  `tempfile.mkdtemp(dir=tempfile.gettempdir())` mit Ancestor-Assertion („kein
  `.meta-config/` oberhalb"), `cwd=<fixture>`, Ziel `<fixture>/x.py` ⇒ Exit 2,
  `repo-containment.no-root`, `no project root found above <anchor>` und `anchor:`-Zeile.
- **AC-33** — `test_relative_target_with_depth_is_checked_at_real_location`:
  `cwd=<root>/a/b`, `../../x` ⇒ Exit 0; `../../../../etc/passwd` ⇒ Exit 2.
- **Parität (Shared Contract)** — `test_hook_sink_matches_tmp_paths`: die `allowed:`-Zeile
  endet auf `and under <TmpPaths.absolute>`; `absolute == realpath(root/scratch/x)`.
- **AC-18/AC-28/AC-29/AC-37 (Verhalten implementiert, Tests folgen in Task 9)** — absolute
  Root-/Sink-Pfade in der Block-Meldung, Anker aus dem Zielverzeichnis bei leerem `cwd`,
  System-Temp-Ziel bleibt blockiert, fremdes-Projekt-Ziel wird erlaubt.

### Verhaltensänderungen (Fail-closed-Vertrag)

1. **Kein `$PWD` mehr.** `WORKDIR` stammt ausschließlich aus einem absoluten Payload-`cwd`
   oder aus `realpath(dirname(ziel))` bei absolutem Write/Edit-Ziel; sonst Exit 2.
2. **Keine Root-Promotion.** Findet `resolve_repo_root` keinen `.meta-config/`-Ancestor,
   wird der Anker nicht zum Root; Exit 2, Code `repo-containment.no-root`.
3. **Reihenfolge:** Anker + Root-Auflösung laufen **vor** dem `enabled: false`-Kurzschluss
   und vor dem Config-Read; ein fremdes Opt-out kann keinen Write freischalten.
4. **Meldungen:** absolute Root-/Sink-Pfade (`allowed: paths under <root> and under <sink>`),
   `anchor:`-/`repair:`-/`opt-out:`-Zeilen; die Substrings `outside the repository root`,
   `DISABLED tmp-sink` und `under <root>/<sink>` bleiben erhalten.
5. **Symlink-`cwd`:** `realpath` vor der Ancestor-Suche; weicht das Ergebnis ab, nennt die
   Meldung zusätzlich `resolved: payload \`cwd\` <raw> -> <real> (resolved)`.

### Abweichungen von der Aufgabenbeschreibung (Spec ist normativ)

1. **Impl-Versionsbump 1.1.0 → 1.2.0** samt Anpassung von
   `tests/test_tmp_sink_path_parity.py::test_hook_version_bumped_and_old_version_is_drift`
   (Regex + Drift-Replace). Der Header der Impl verlangt den Bump bei jeder Logikänderung;
   der Paritätstest pinnte die alte Version. `repo-containment.sh` bleibt unverändert
   (Wrapper ohne Hash-Bindung, nur `# version: 1.0.0`, kein Bump nötig).
2. **Bash ohne `cwd` ⇒ fail closed.** Die Spec-Ankerregel ist pfadförmig („Ziel absolut ⇒
   `dirname(ziel)`"); für Bash gibt es kein einzelnes Ziel. Auslegung: Bash ohne `cwd`
   liefert Exit 2 mit demselben Code und einer eigenen Meldung („a Bash command is not a
   path"), statt einen Anker aus dem Kommando zu raten. **Risiko:** ein Provider, der Bash
   ohne `cwd` sendet (z. B. Antigravity-Adapter bei leerem `workspacePaths`/`args.Cwd`),
   blockt damit auch reine Lese-Kommandos. Beide dokumentierten Adapter füllen `cwd` im
   Regelfall; Task 9/20 beobachten das Adapterverhalten.
3. **Relativer `cwd` wird nicht als Anker verwendet** (statt ihn per `realpath` implizit
   gegen den Prozess-CWD aufzulösen). Das wäre sonst eine verdeckte `$PWD`-Übernahme.
   Ein absolutes Write/Edit-Ziel ankert weiterhin; sonst greift die Meldung
   „relative target without `cwd`" plus `note:`-Zeile. Provider senden absolute
   `cwd`-Werte (Annahme A1).
4. **Kollaterale Pflege (generierte bzw. referenzielle Artefakte):**
   `.agents/hooks/repo-containment-impl.sh` (einzige getrackte deployte Kopie; `.claude/`
   und `.gemini/` sind gitignored) und `.meta-config/generated-file-hashes.json` wurden
   durch `python3 scripts/sync.py` regeneriert, sonst meldet `--validate`
   `hooks.stale-deployed-version`. Der Hash-Baseline-Diff umfasst zusätzlich die
   generierten Dateien der Tasks 1–7 (sie waren vor diesem Lauf nicht neu gehasht); das
   ist Buchhaltung des Sync-Tools, keine manuelle Bearbeitung generierter Dateien.
   `config/runtime-config-readers.yaml` zeigt jetzt auf `repo-containment-impl.sh:313`
   (`CONFIG_FILE=`), weil die alte Evidence-Zeile `:267` durch den Umbau auf
   `no_anchor_block()` zeigte (Test `test_runtime_config_readers.py`).
5. **Docstring-Anpassung `test_missing_config_defaults_to_containment_on`:** Assertion und
   Name bleiben unverändert (Exit 2 gilt weiterhin), der Docstring hält fest, dass der
   Exit 2 seit Task 8 aus `repo-containment.no-root` folgt und Task 9 den Test bewusst
   invertiert/umbenennt.
6. **Step 4 (Commit) nicht ausgeführt** — kein Commit-Auftrag für diesen Subagenten.

### Offene Punkte für Task 9

- `test_missing_config_fails_closed` (AC-03) ersetzt die alte Fail-open-Erwartung.
- AC-04 (relatives Ziel ohne `cwd`), AC-06 (`cwd=<sink>/sub`, `notes.md`), AC-07
  (Symlink-`cwd`), AC-18 (`test_block_message_uses_absolute_sink`), AC-28/29/37,
  AC-30 (Adapter-Tempdatei) sind noch nicht als Tests vorhanden; das Verhalten ist
  implementiert und oben manuell belegt.

## Evidence — Task 9

### Rot (vor der finalen Teständerung)

Die Inversion ist eine Test-Änderung, keine Verhaltensänderung: das Verhalten wurde in
Task 8 implementiert. Der ehrliche Rot-Beleg ist deshalb der Lauf der **neuen** Tests gegen
den **alten** Hook. Dafür wurde `git archive c2da2aff^` nach
`/tmp/opencode/am-red-task9` entpackt (Hook-Impl `version: 1.1.0`, also ohne Anker-Regel),
die beiden neuen Testdateien hineinkopiert und der Lauf dort ausgeführt:

```
$ cd /tmp/opencode/am-red-task9
$ python3 -m pytest tests/test_repo_containment_hook.py -q \
    -k "missing_config_fails_closed or relative_target_without_cwd_fails_closed"

=================================== FAILURES ===================================
_______________________ test_missing_config_fails_closed _______________________

external_fixture = PosixPath('/tmp/am-hook-ext-wkbt6ojj')
...
        result = _run_hook(_write_payload(external_fixture / "notes.md", external_fixture))
>       assert result.returncode == 2, result.stderr
E       AssertionError:
E       assert 0 == 2
E        +  where 0 = CompletedProcess(args=['/usr/bin/bash', '/tmp/opencode/am-red-task9/hooks/1-generic/repo-containment.sh'], returncode=0, stdout='', stderr='').returncode

tests/test_repo_containment_hook.py:298: AssertionError
________________ test_relative_target_without_cwd_fails_closed _________________

external_fixture = PosixPath('/tmp/am-hook-ext-6utezqzt')
...
        from_outside = _run_hook(payload, process_cwd=external_fixture)
>       assert from_outside.returncode == 2, from_outside.stderr
E       AssertionError:
E       assert 0 == 2
E        +  where 0 = CompletedProcess(args=['/usr/bin/bash', '/tmp/opencode/am-red-task9/hooks/1-generic/repo-containment.sh'], returncode=0, stdout='', stderr='').returncode

tests/test_repo_containment_hook.py:316: AssertionError
=========================== short test summary info ============================
FAILED tests/test_repo_containment_hook.py::test_missing_config_fails_closed
FAILED tests/test_repo_containment_hook.py::test_relative_target_without_cwd_fails_closed
2 failed, 39 deselected in 1.01s
```

Beide Tests belegen den alten Fail-open: `cwd`/`$PWD` wurde zum Root geadelt, das Ziel lag
„innerhalb" dieses Pseudo-Roots ⇒ Exit 0.

**AC-30** hatte vor Task 9 keine Abdeckung (der Adapter räumt bereits auf, der Test ist eine
Charakterisierung). Rot-Beleg daher zweistufig:

```
$ git show HEAD:tests/test_antigravity_hooks_registration.py | grep -n "mktemp\|cleaned_up\|TMPDIR"
grep-exit=1        # 0 Treffer: keine Aufräum-Assertion vorhanden
```

Mutationsprobe (Kopie des Adapters in `/tmp`, **ohne** die `trap 'rm -f ...' EXIT`-Zeile;
Produktionsdatei unberührt):

```
$ ... | TMPDIR=.../scratch TMP=.../scratch bash /tmp/opencode/am-red-ac30/mutated.sh target.sh
{"decision": "deny", "reason": "blocked: strict mode"}
leftover-after-mutation:
tmp.W7qXjMYWli

$ ... | TMPDIR=.../scratch TMP=.../scratch bash /tmp/opencode/am-red-ac30/antigravity-json-adapter.sh target.sh
{"decision": "deny", "reason": "blocked: strict mode"}
leftover-real-adapter:
0
```

Ohne Trap bleibt die `mktemp`-Datei liegen (die Assertion `sorted(scratch.iterdir()) == []`
schlägt dann fehl); mit Trap ist das Verzeichnis leer — die neue Assertion ist also
tragend, nicht tautologisch.

### Grün (nach der Teständerung)

| # | Kommando | Ergebnis |
|---|---|---|
| 1 | `python3 -m pytest tests/test_repo_containment_hook.py tests/test_antigravity_hooks_registration.py -q` | `60 passed in 23.31s`, Exit 0 |
| 2 | `python3 -m pytest tests/test_tmp_sink_path_parity.py tests/test_tmp_sink_path_hardening.py -q` | `220 passed in 4.97s`, Exit 0 |
| 3 | `python3 scripts/sync.py --validate` | Exit 0, `0 action(s), 382 skipped, 2 warning(s)` (beide WARNINGS vorbestehend: `active-set.gate-dropped`, Submodul-Checkout `external/awesome-claude-code`) |
| 4 | `python3 -m pytest tests/test_repo_containment_hook.py -q --collect-only` | 40 Tests, davon 11 neu/umbenannt (siehe Mapping) |

### Abgedeckte ACs (Task 9)

| AC | Test | Aussage |
|---|---|---|
| AC-03 | `test_missing_config_fails_closed` | Fixture ohne `.meta-config/`, Ziel **innerhalb** ⇒ Exit 2 `repo-containment.no-root` (bewusst invertiert) |
| AC-04 | `test_relative_target_without_cwd_fails_closed` | kein `cwd`, `file_path="notes.md"` ⇒ Exit 2, „relative target without \`cwd\`"; zusätzlich Prozess-CWD = Repo-Root ⇒ weiterhin 2 (kein `$PWD`-Ersatz) |
| AC-06 | `test_relative_target_resolves_against_cwd` | `cwd=<root>/.tmp/sub`, `notes.md` ⇒ 0; `../../../../etc/passwd` ⇒ 2 |
| AC-07 | `test_symlinked_cwd_uses_realpath` | Symlink-`cwd` nach außen ⇒ 2 + `resolved: payload \`cwd\` <link> -> <realpath>`; Symlink in ein Projekt ⇒ 0 |
| AC-08 | `test_disabled_mode_allows_even_an_outside_write` (bleibt), `test_opt_out_does_not_unlock_a_foreign_cwd` | Opt-out wirkt projektlokal; ohne auflösbaren Root ⇒ 2 |
| AC-18 | `test_block_message_uses_absolute_sink` | absolute `repo root:`/`allowed:`-Pfade, kein `.tmp` als nackter Pfad, `anchor:`/`repair:`/`opt-out:` vorhanden |
| AC-28 | `test_empty_cwd_anchors_on_absolute_target` | `cwd=""`, absolutes Ziel im Root ⇒ 0 |
| AC-29 | `test_empty_cwd_does_not_allow_system_temp` | `cwd=""`, Ziel im System-Temp ⇒ 2 + `no-root` |
| AC-30 | `test_adapter_temp_file_is_cleaned_up` | Scratch-Verzeichnis leer, `git status --porcelain` unverändert, Deny-JSON unverändert |
| AC-33 | `test_relative_target_is_judged_at_its_real_location` | `cwd=<root>/a/b`, `../../x` ⇒ 0, `../../../../etc/passwd` ⇒ 2 (aus Task 8, nur auf Spec-Namen umbenannt) |
| AC-37 | `test_empty_cwd_uses_project_of_absolute_target` | `cwd=""`, fremdes Projekt mit `.meta-config/` ⇒ 0 (dokumentierte ADR-08-Annahme), Nachbar ohne Root ⇒ 2 |

### Abweichungen von der Aufgabenbeschreibung (Spec ist normativ)

1. **Testnamen folgen der Spec, nicht dem Task-Text.** Der Task-Auftrag nannte
   `test_relative_target_is_checked_against_cwd`, `test_symlinked_cwd_is_resolved`,
   `test_empty_cwd_anchors_on_absolute_target_inside_root`,
   `test_empty_cwd_blocks_system_temp_target`,
   `test_empty_cwd_foreign_project_target_is_allowed`; die Spec (AC-06/07/28/29/37)
   benennt `test_relative_target_resolves_against_cwd`, `test_symlinked_cwd_uses_realpath`,
   `test_empty_cwd_anchors_on_absolute_target`, `test_empty_cwd_does_not_allow_system_temp`,
   `test_empty_cwd_uses_project_of_absolute_target`. Umgesetzt sind die **Spec-Namen**
   (Traceability in den ACs), weil die Spec normativ ist.
2. **AC-33-Test umbenannt** von `test_relative_target_with_depth_is_checked_at_real_location`
   (Task-8-Arbeitstitel) auf den Spec-Namen
   `test_relative_target_is_judged_at_its_real_location`. Assertions unverändert.
3. **AC-30 ist eine Charakterisierung, keine Rot-Grün-Änderung:** der Adapter räumt seit
   jeher per EXIT-Trap auf (`antigravity-json-adapter.sh:167-168`); Task 9 ergänzt nur die
   fehlende Abdeckung. Der Rot-Beleg erfolgt über die fehlende Coverage plus Mutationsprobe
   (siehe oben), ohne Produktionscode anzufassen.
4. **Helfer konsolidiert statt dupliziert:** `_write_payload(path, cwd=None, tool=...)`
   bildet alle drei Payload-Formen ab (`cwd` fehlt / `cwd=""` / `cwd=<pfad>`),
   `_run_hook(..., process_cwd=...)` macht das Prozess-CWD explizit (Default `_REPO_ROOT`).
   Kein zweiter Payload-Builder für die Sonderfälle.
5. **Zusatz-Assertions** (über den Task-Text hinaus, aus der Spec ableitbar):
   Negativ-Kontrolle in AC-06, Positiv-Kontrolle in AC-07 (Symlink in ein Projekt ⇒ 0),
   Prozess-CWD-Kreuzprobe in AC-04, Nachbar-Fall in AC-37.
6. **Kein Produktionscode geändert** — es gab keinen Test, der einen Defekt aus Task 8
   nachweist. `git status` enthält nur die beiden Testdateien.
7. **Step 4 (Commit) nicht ausgeführt** — kein Commit-Auftrag für diesen Subagenten.

### Risiken / Interpretationen

- **AC-37** hält eine bewusste Vertrauensannahme fest (fremdes Projekt mit `.meta-config/`
  wird bei leerem `cwd` Root). Der Test ist eine Dokumentation der Grenze, keine
  Sicherheitszusage; eine Änderung der Annahme macht ihn absichtlich rot.
- **AC-30 (b)** nutzt `git status --porcelain` als Proxy für „keine neue Datei im
  Repo-Baum". Das ist robust gegen den sonst schon schmutzigen Arbeitsbaum (Vergleich
  vor/nach), aber nicht parallel-suite-fest: bei gleichzeitig schreibenden Läufen im selben
  Repo könnte die Differenz fremd verursacht sein.
- **AC-28** ist nur dann diskriminierend, wenn `tmp_path` außerhalb des Repos liegt (der
  `conftest`-Basetemp-Guard warnt bei In-Repo-Basetemp nur). Mit In-Repo-Basetemp wäre der
  alte `$PWD`-Fallback nicht mehr vom Ziel-Anker unterscheidbar; die Docstring nennt die
  Annahme.
- **AC-04** setzt voraus, dass der Repo-Root `.meta-config/` trägt (Self-Hosting-Repo). In
  einem Checkout ohne `.meta-config/` wäre die Kreuzprobe „Prozess-CWD = Repo-Root" nicht
  mehr aussagekräftig (der Test bliebe grün, weil beide Fälle blocken).

## Evidence — Task 10

### Rot (vor der Implementierung)

`python3 -m pytest tests/test_tmp_sink_output_dirs.py -q -k "context_report_passes_absolute_tmp_env or meta_optimizer_render_pins_sink_env or work_dir_env_is_only or framework_render_modules"`
→ Exit 1:

```
FFFF                                                                     [100%]
=================================== FAILURES ===================================
_________________ test_context_report_passes_absolute_tmp_env __________________

tmp_path = PosixPath('/tmp/pytest-of-hermes/pytest-104/test_context_report_passes_abs0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x78802c674180>

    def test_context_report_passes_absolute_tmp_env(tmp_path, monkeypatch):
        """IC-34: the render subprocesses receive the absolute ``TmpPaths.env`` pin.

        Red before Task 10: ``render_into_work_dir`` built its env with
        ``work_dir_env(work_dir)`` and knew no ``paths`` argument.
        """
        project_root = tmp_path / "project"
        config_path = project_root / ".meta-config" / "project.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("variables:\n  PROJECT_NAME: demo\n", encoding="utf-8")
        paths = resolve_tmp_paths(project_root, {})
        work_dir = project_root / ".tmp" / "context-report" / "run-1" / "work"

        captured = _capture_subprocess_env(monkeypatch, cr)
>       cr.render_into_work_dir(REPO_ROOT, config_path, work_dir, paths=paths)
E       TypeError: render_into_work_dir() got an unexpected keyword argument 'paths'

tests/test_tmp_sink_output_dirs.py:540: TypeError
___________________ test_meta_optimizer_render_pins_sink_env ___________________

tmp_path = PosixPath('/tmp/pytest-of-hermes/pytest-104/test_meta_optimizer_render_pin0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x78802c6742b0>

    def test_meta_optimizer_render_pins_sink_env(tmp_path, monkeypatch):
        """IC-34: the optimizer render helper pins the absolute sink env.

        Red before Task 10: ``_render_into`` called ``work_dir_env(work_dir)``.
        """
        project_root = tmp_path / "project"
        project_root.mkdir()
        paths = resolve_tmp_paths(project_root, {})
        work_dir = paths.absolute / "meta-optimizer" / "run-1" / "work"

        captured = _capture_subprocess_env(monkeypatch, mo)
>       mo._render_into(REPO_ROOT, "variables:\n  A: b\n", work_dir, paths)
E       TypeError: _render_into() takes 3 positional arguments but 4 were given

tests/test_tmp_sink_output_dirs.py:559: TypeError
_______________ test_work_dir_env_is_only_called_from_tmp_paths ________________

    def test_work_dir_env_is_only_called_from_tmp_paths():
        """IC-18: ``work_dir_env`` is reachable only through ``tmp_env``."""
        call_sites = _work_dir_env_call_sites()
        only = Path("scripts/lib/tmp_paths.py")

>       assert set(call_sites) == {only}, {
            str(path): lines for path, lines in call_sites.items()
        }
E       AssertionError: {'scripts/lib/context_report.py': [340], 'scripts/lib/meta_optimizer.py': [1508], 'scripts/lib/tmp_paths.py': [303, 188]}
E       assert {PosixPath('s...mp_paths.py')} == {PosixPath('s...mp_paths.py')}
E
E         Extra items in the left set:
E         PosixPath('scripts/lib/meta_optimizer.py')
E         PosixPath('scripts/lib/context_report.py')
E         Use -v to get more diff

tests/test_tmp_sink_output_dirs.py:594: AssertionError
__________________ test_framework_render_modules_call_tmp_env __________________

    def test_framework_render_modules_call_tmp_env():
        """The two Task-10 call sites go through ``tmp_env``, not ``work_dir_env``."""
        for relative in ("scripts/lib/context_report.py", "scripts/lib/meta_optimizer.py"):
            tree = ast.parse((REPO_ROOT / relative).read_text(encoding="utf-8"))
            called = {
                node.func.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            }
>           assert "tmp_env" in called, relative
E           AssertionError: scripts/lib/context_report.py
E           assert 'tmp_env' in {'Path', 'RuntimeError', 'ValueError', '_cap_for', '_effective_profiles', '_entry', ...}

tests/test_tmp_sink_output_dirs.py:609: AssertionError
=========================== short test summary info ============================
FAILED tests/test_tmp_sink_output_dirs.py::test_context_report_passes_absolute_tmp_env
FAILED tests/test_tmp_sink_output_dirs.py::test_meta_optimizer_render_pins_sink_env
FAILED tests/test_tmp_sink_output_dirs.py::test_work_dir_env_is_only_called_from_tmp_paths
FAILED tests/test_tmp_sink_output_dirs.py::test_framework_render_modules_call_tmp_env
4 failed, 41 deselected in 1.46s
```

Beide Env-Pin-Tests scheitern an der fehlenden `paths`-Schnittstelle (`TypeError`, also noch vor jeder
Assertion); der `ast`-Guard nennt exakt die beiden Plan-Aufrufstellen (`context_report.py:340`,
`meta_optimizer.py:1508`) als Fremd-Aufrufer von `work_dir_env`.

### Grün (nach der Implementierung)

| # | Kommando | Ergebnis |
|---|---|---|
| 1 | `python3 -m pytest tests/test_tmp_sink_output_dirs.py -q` | `45 passed in 6.71s`, Exit 0 |
| 2 | `python3 -m pytest tests/test_tmp_paths_builder.py tests/test_context_report.py -q` | `31 passed in 202.15s`, Exit 0 |
| 3 | `python3 -m pytest tests/test_context_budgets.py -q` | `12 passed in 407.12s`, Exit 0 |
| 4 | `python3 -m pytest tests/test_meta_optimizer_marks.py tests/test_meta_optimizer_fanout.py -q` | `12 passed in 224.98s`, Exit 0 |
| 5 | `python3 -m pytest tests/test_meta_optimizer_credentials.py tests/test_meta_optimizer_role.py tests/test_meta_optimizer_refill.py tests/test_meta_optimizer_inactive_scope.py -q` | `57 passed in 476.07s`, Exit 0 |
| 6 | `python3 -m pytest tests/test_meta_optimizer_runner.py tests/test_meta_optimizer_applier.py -q` | `1 failed, 40 passed, 5 errors in 742.16s` — **alle 6 vorbestehend** (siehe Abweichung 3) |
| 7 | `python3 -m pytest tests/test_doctor_runner.py -q` | `74 passed in 12.15s`, Exit 0 |
| 8 | `python3 scripts/sync.py --validate` | Exit 0; `0 action(s) \| 382 skipped \| 2 warning(s)`, `grep -c "[ERROR]"` = **0** (beide WARNINGS vorbestehend: `active-set.gate-dropped`, Submodul-Checkout `external/awesome-claude-code`) |
| 9 | `ast.parse(..., feature_version=(3, 9))` über alle 8 geänderten Dateien | `py3.9 ok` (8/8) |
| 10 | `grep -rn "work_dir_env" scripts/` | nur noch Definition `repo_containment.py:739` + zwei Aufrufe `tmp_paths.py:188,303` (+ Docstring-Nennung) |

### Abgedeckte ACs (Task 10)

- **AC-12** — `test_context_report_passes_absolute_tmp_env` und
  `test_meta_optimizer_render_pins_sink_env`: für **jeden** gestarteten Subprozess
  (`git init` und Sync-Render) sind `TMPDIR`/`TEMP`/`TMP` absolut, existieren als
  Verzeichnis und sind wertgleich mit `TmpPaths.env` — also der absolute Sink-Root, nicht
  das Work-Dir (`assert env["TMPDIR"] != str(work_dir)`).
- **IC-18** — `test_work_dir_env_is_only_called_from_tmp_paths` (`ast`-Scan über
  `scripts/**`: die Call-Site-Menge ist exakt `scripts/lib/tmp_paths.py`) plus
  `test_framework_render_modules_call_tmp_env` (beide Module rufen `tmp_env`).
- **`tmp-sink.disabled`** für `tmp_env` war bereits in Task 1 abgedeckt
  (`test_writers_still_raise_when_sink_disabled`) — bewusst **nicht** dupliziert.

### Implementierung

| Stelle | Vorher | Nachher |
|---|---|---|
| `context_report.py:340` (`render_into_work_dir`) | `env = work_dir_env(work_dir)` | `env = tmp_env(paths)`; `paths: TmpPaths` ist keyword-only Pflichtparameter des Render-Seams |
| `context_report.py::run_context_report` | — | `paths = resolve_tmp_paths(project_root, config)` einmal im bestehenden `TmpSinkError`-try (Exit 2), danach durchgereicht |
| `meta_optimizer.py:1508` (`_render_into`) | `env = work_dir_env(work_dir)` | `env = tmp_env(paths)`; `paths` ist vierter Pflichtparameter |
| `meta_optimizer.py::collect_candidates` | — | optionaler `paths`-Parameter; ohne ihn genau **eine** Auflösung über `resolve_tmp_paths` (ADR-01), weitergereicht an `_classify_candidates` → `_render_into` |
| `meta_optimizer.py::run_optimize_config` | — | `paths = resolve_tmp_paths(...)` im bestehenden `TmpSinkError`-try (Exit 2), an `collect_candidates` und beide `_render_into`-Aufrufe |
| `meta_optimizer.py::_finish_apply` | — | dito (nach `_applier_run_dir`, damit die Fehlerpräzedenz unverändert bleibt) |
| `repo_containment.py::work_dir_env` | Docstring ohne Aufrufpfad | Docstring: „**Reached only through** `lib.tmp_paths.tmp_env`" (IC-18), Logik 0 Zeilen geändert |

Kein zweiter Resolver, kein neuer Config-Read, keine Provider-Verzweigung: `TmpPaths` kommt
aus dem einen Resolver; die beiden Module lesen `repo_containment.tmp-sink` nirgends selbst.

### Verhaltensänderung (Spec ist normativ)

Der Env-Pin zeigt jetzt auf den **Sink-Root** (`TmpPaths.env`) statt auf das jeweilige
Work-Dir. Beides ist absolut und liegt im Sink, aber nur der Sink-Root ist wertgleich mit
`TmpPaths.env` (Spec-Zeile „jeder Framework-Subprozessstart … erhält `TmpPaths.env`",
IC-18/ADR-12). Nebeneffekt, der einen vorbestehenden Fehler behebt: mit `TMPDIR=<work>`
sah der gerenderte Sync-Subprozess den „System-Temp" **innerhalb** seines eigenen
Projekt-Roots und starb an `tmp-sink.system-temp-exception`
(`…/work is inside the project root`). Mit dem Sink-Root-Pin rendert er normal — auf HEAD
waren deshalb die `proposed`-Fixtures der Applier-Suite bereits rot.

### Abweichungen von der Aufgabenbeschreibung (Spec ist normativ)

1. **Vier zusätzliche Testdateien (mechanische Signatur-Anpassung).** Der Plan listet nur
   `tests/test_tmp_sink_output_dirs.py`. `render_into_work_dir` und `_render_into` erhalten
   aber `paths` als Pflichtparameter, damit der Pin wirklich `TmpPaths.env` ist (Spec-Zeile
   IC-18 / Sink-Root-Pin). Angepasst wurden deshalb: `tests/test_context_budgets.py`
   (2 Aufrufe: `paths=resolve_tmp_paths(<projekt>, {})`), `tests/test_meta_optimizer_runner.py`
   (1 `fake_render`-Monkeypatch: `_paths=None`) und `tests/test_meta_optimizer_applier.py`
   (2 `fake_render`-Monkeypatches, gleiches Muster). Die 3 Monkeypatches ersetzen `_render_into`
   komplett, also musste nur ihre Signatur tolerant werden — keine Assertion geändert.
   Alternative wäre ein synthetisches `TmpPaths` gewesen (ad-hoc-Konstruktion statt Resolver);
   das hätte ADR-01 verletzt und einen zweiten Env-Pin-Pfad erzeugt.
2. **`tests/test_context_report.py::test_context_report_never_uses_tempfile` entschärft
   (1 Zeile).** Der Test verbot pauschal auch `tempfile.gettempdir()`. Der zentrale Resolver
   (ADR-01, seit Task 1/2) *muss* `gettempdir()` lesen, um die sanktionierte
   pytest-Basetemp-Präzedenz zu bestimmen (`resolve_pytest_basetemp`/`tmp_sink_location_error`);
   `run_context_report` ruft ihn jetzt einmal auf. `gettempdir()` ist ein reiner Read ohne
   Temp-Erzeugung — gepatcht werden deshalb nur noch die **Erzeugungs**-APIs
   (`mkdtemp`, `mkstemp`, `NamedTemporaryFile`, `TemporaryDirectory`). Die Aussage „kein
   System-Temp-Write" bleibt vollständig geprüft; ein Kommentar im Test nennt den Grund.
3. **Die 6 Rotmarks in `test_meta_optimizer_{runner,applier}.py` sind vorbestehend, nicht
   Task 10.** Es sind genau die Tests, die `tempfile.gettempdir` auf `raise` patchen:
   `test_optimizer_never_uses_systemtemp` plus die fünf Fälle der modulweiten `applied`-Fixture.
   Nachweis: dieselben Tests wurden mit `git stash` auf HEAD (`f071dbb7`) gefahren —
   `test_optimizer_never_uses_systemtemp` ist dort identisch rot
   (`AssertionError: system temp must not be used`), und die Applier-Fixtures scheitern dort
   bereits eine Stufe früher (Render-Env-Fehler, siehe oben). Ursache ist unverändert
   `config.py::build_variables` → `resolve_tmp_paths` → `gettempdir` (Task 1/2, in diesem Task
   nicht angefasst). **Nicht repariert** — siehe offene Punkte.
4. **`_finish_apply` löst `paths` auch ohne `accepted` auf** (dry-run-Vorschau). Das ist
   gefahrlos (der Resolver ist rein), hält die Fehlerpräzedenz (`_applier_run_dir` zuerst) und
   vermeidet eine zweite Verzweigung; der Sink-Fehler wird weiterhin als Exit 2 gemappt.
5. **Keine `.meta-config`-Änderung, kein Versionsbump, kein `sync.py`-Regenerat nötig** —
   `--validate` meldet `0 action(s)`; die geänderten Module sind nicht generierte Artefakte.
6. **Step 4 (Commit) nicht ausgeführt** — kein Commit-Auftrag für diesen Subagenten
   (Commit-Authority liegt beim `git`-Agenten). Die Plan-Checkbox bleibt offen, die Statuszeile
   führt `— (pending)`.

### Offene Punkte / Risiken

- **AC-94-Testprämisse vs. ADR-01:** die zwei `gettempdir`-Patch-Tests sind seit Task 1/2 rot.
  Task 10 macht sie nicht schlechter, aber auch nicht grün. Zu entscheiden (Task 11/18?):
  `gettempdir` aus dem Patch-Set nehmen (wie in Abweichung 2 begründet) oder den Resolver so
  aufteilen, dass die Basetemp-Präzedenz ohne `gettempdir` auskommt. Solange das offen ist,
  bleibt `tests/test_meta_optimizer*.py` bei 6 Rotmarks.
- **`apply_config_patch` fängt `TmpSinkError` aus `_recompute_candidates` nicht** (die
  Except-Liste führt `RegistryError`/`ValueError`/`OSError`, nicht `TmpSinkError`). Das ist
  vorbestehend (`collect_candidates` → `resolve_work_dir` warf dort schon so) und durch Task 10
  nur *früher* im selben Aufruf möglich; ein deaktivierter Sink im Apply-Pfad kann also weiter
  einen Traceback statt Exit 2 erzeugen. Nicht in diesem Task repariert (eigene Entscheidung
  nötig, inkl. Test).
- **`run_context_report` löst einmal zusätzlich auf** (`resolve_tmp_paths` neben
  `resolve_output_dir`/`resolve_work_dir`, die intern je selbst auflösen). Bewusst in Kauf
  genommen: der Resolver ist rein und die Alternative wäre ein zweiter Pfad oder eine
  `TmpPaths`-Konstruktion am Render-Seam. Kosten sind ein paar `realpath`-Aufrufe pro Report.
- **`tests/test_ac01_render_identity.py`/Slimming-Goldens** bleiben unberührt (nicht im Scope,
  Rebaseline ist Task 16); Task 10 ändert keine gerenderten Artefakte.

## Evidence — Task 11

### Rot (vor der Implementierung)

`python3 -m pytest tests/test_tmp_sink_env_coverage.py::test_subprocess_calls_pin_temp_env -q`
→ Exit 1 (`scripts/**`: 42 ungepinnte Aufrufe, darunter die 12 namentlich bekannten):

```
E       AssertionError: subprocess calls without a tmp-sink env pin (AC-11/IC-18). Pass env=tmp_env(paths) (merging the inherited env) or add a complete entry {path, symbol, reason} to .meta-config/temp-env-allowlist.yaml:
E         scripts/admin-server.py:_run (line 1243)
E         scripts/admin-server.py:run_consistency_check (line 1625)
E         scripts/admin-server.py:_admin_start_detached (line 5799)
E         scripts/admin-server.py:_admin_start_detached (line 5805)
E         scripts/admin-server.py:_start (line 609)
E         scripts/admin-server.py:_start (line 618)
E         scripts/admin-server.py:_stop (line 644)
E         scripts/admin-server.py:_admin_stop (line 5830)
E         scripts/consistency-check.py:get_changed_files (line 83)
E         scripts/consistency-check.py:get_changed_files (line 79)
E         scripts/consistency-check.py:get_new_files_vs_main (line 98)
E         scripts/lib/auto_github_release.py:_release_exists (line 186)
E         scripts/lib/auto_github_release.py:main (line 271)
E         scripts/lib/cli_commands.py:handle_scan_staged (line 449)
E         scripts/lib/cli_commands.py:_build_context (line 528)
E         scripts/lib/cli_commands.py:_run_common_tail (line 1635)
E         scripts/lib/config.py:read_git_version (line 1206)
E         scripts/lib/consistency/frontmatter.py:_get_head_version (line 274)
E         scripts/lib/doctor_detectors.py:detect_command (line 366)
E         scripts/lib/io.py:run_git_check_ignore (line 538)
E         scripts/lib/plugin_test.py:_run_version (line 67)
E         scripts/lib/plugin_test.py:_mcp_initialize_handshake (line 92)
E         scripts/lib/se_export/github_issues_adapter.py:_run_gh (line 265)
E         scripts/lib/se_export/github_issues_adapter.py:_verify_gh_available (line 200)
E         scripts/lib/skill_admin.py:add_skill (line 51)
E         scripts/lib/skills.py:_is_ahead_of_pin (line 206)
E         scripts/lib/skills.py:_is_ahead_of_pin (line 212)
E         scripts/lib/skills.py:get_skill_commit (line 150)
E         scripts/lib/skills.py:ensure_skill_repo (line 320)
E         scripts/lib/skills.py:ensure_skill_repo (line 251)
E         scripts/lib/skills.py:ensure_skill_repo (line 302)
E         scripts/lib/skills.py:deinit_skill_repo (line 342)
E         scripts/lib/skills.py:deinit_skill_repo (line 351)
E         scripts/lib/skills.py:ensure_skill_repo (line 261)
E         scripts/lib/skills.py:ensure_skill_repo (line 267)
E         scripts/lib/skills.py:ensure_skill_repo (line 269)
E         scripts/lib/skills.py:ensure_skill_repo (line 271)
E         scripts/lib/skills.py:ensure_skill_repo (line 277)
E         scripts/lib/spec_plan_validate.py:_changed_files (line 44)
E         scripts/lib/spec_plan_validate.py:_changed_files (line 57)
E         scripts/run_role_routing_eval.py:call_provider (line 727)
```

`python3 -m pytest tests/test_backup_round_trip_804.py::test_staging_dir_is_inside_tmp_sink tests/test_backup_robustness.py::test_staging_falls_back_to_system_temp_with_warning tests/test_backup_robustness.py::test_invalid_sink_aborts_backup_with_stable_code -q`
→ Exit 1:

```
>       assert staging_base is not None, "staging must pass dir= to TemporaryDirectory"
E       AssertionError: staging must pass dir= to TemporaryDirectory
E       assert None is not None
tests/test_backup_round_trip_804.py:210: AssertionError
...
>       assert any("backup.staging-system-temp" in warning for warning in log.warnings), log.warnings
E       AssertionError: []
tests/test_backup_robustness.py:209: AssertionError
...
>       with pytest.raises(TmpSinkError) as exc:
E       Failed: DID NOT RAISE TmpSinkError
tests/test_backup_robustness.py:217: Failed
```

### Grün (nach der Implementierung)

| # | Kommando | Ergebnis |
|---|---|---|
| 1 | `python3 -m pytest tests/test_tmp_sink_env_coverage.py tests/test_backup_round_trip_804.py tests/test_backup_robustness.py -q` | `23 passed in 7.44s`, Exit 0 |
| 2 | `python3 -m pytest tests/test_tmp_sink_output_dirs.py tests/test_backup_*.py -q` | `63 passed in 9.31s`, Exit 0 (Module: `test_tmp_sink_output_dirs.py`, `test_backup_round_trip_804.py`, `test_backup_robustness.py`) |
| 3 | `python3 -m pytest tests/test_admin_server.py tests/test_admin_backup_name_validation.py tests/test_admin_plugin_test_endpoint.py tests/test_consistency_checks.py tests/test_role_routing_eval_catalog.py tests/test_skill_admin.py -q` | `195 passed, 11 subtests passed in 25.82s`, Exit 0 (Nachbarregression der geänderten Module) |
| 4 | `python3 scripts/sync.py --validate` | Exit 0; `0 action(s) \| 382 skipped \| 2 warning(s)` — beide vorbestehend (`active-set.gate-dropped`, Submodul-Checkout `external/awesome-claude-code`) |
| 5 | `python3 scripts/sync.py --dry-run` | Exit 0; `0 action(s) \| 449 skipped \| 35 warning(s)` (vorbestehende `active-set.unresolved-placeholder`-Warnungen) |
| 6 | `python3 -m py_compile scripts/admin-server.py scripts/consistency-check.py scripts/run_role_routing_eval.py scripts/lib/backup.py` | Exit 0 |

### Abgedeckte ACs (Task 11)

- **AC-09** — `tests/test_backup_round_trip_804.py::test_staging_dir_is_inside_tmp_sink`:
  `TemporaryDirectory` erhält `dir=<realpath>/.../.tmp/backup-staging`, das Verzeichnis
  existiert vor dem Kontext, und `tempfile.gettempdir()` ist nicht die Staging-Basis; das
  Backup ist erfolgreich und das Archiv liegt im Repo.
- **AC-10** — `tests/test_backup_robustness.py::test_staging_falls_back_to_system_temp_with_warning`:
  `repo_containment.tmp-sink.enabled: false` ⇒ `dir=` fehlt (System-Temp), WARNING
  `backup.staging-system-temp` ist im `SyncLog`, das Backup ist erfolgreich.
- **AC-11** — `tests/test_tmp_sink_env_coverage.py::test_subprocess_calls_pin_temp_env`:
  AST-Scan über `scripts/**`; jeder `subprocess.run`/`Popen`/`call`/`check_call`/`check_output`
  ist entweder über `tmp_env`/`tmp_sink_env` gepinnt oder hat einen vollständigen
  Allowlist-Eintrag `{path, symbol, reason}`. Zusätzlich: strikte Schema-Prüfung,
  Teil-Einträge unterdrücken nichts, veraltete Einträge schlagen fehl.

### Implementierung

| Stelle | Vorher | Nachher |
|---|---|---|
| `scripts/lib/backup.py::create_backup` | `tempfile.TemporaryDirectory()` (System-Temp) | `_backup_staging(...)`: `resolve_output_dir(project_root, config, "backup-staging")` + `mkdir`, dann `TemporaryDirectory(dir=<abs>)`; Fallback **nur** bei `tmp-sink.disabled` (WARNING), sonst `TmpSinkError("backup.tmp-sink.invalid-path")` |
| `scripts/admin-server.py` | 8 Starts ohne Env-Pin | Helper `_tmp_sink_env(root)` (tmp-Pin, `None` bei deaktiviertem Sink); 6 Starts gepinnt (`_start` ×2, `_run`, `run_consistency_check`, `_admin_start_detached` ×2), 2 `taskkill`-Stellen allowlisted |
| `scripts/consistency-check.py` | 3 `git`-Aufrufe ohne Env | Helper `_tmp_sink_env(root)`; alle drei `git diff`/`ls-files`-Aufrufe gepinnt (deaktivierter Sink ⇒ `env=None`, Check bleibt lauffähig) |
| `scripts/run_role_routing_eval.py::call_provider` | `env = os.environ.copy()` | `env = _tmp_sink_env(os.environ.copy())` — merged den Sink-Pin, behält PATH/HOME |
| `.meta-config/temp-env-allowlist.yaml` | — | neu, 21 Einträge mit Kategorie-Präfix im `reason`; keine `expires` |

### Klassifikation der 12 namentlich bekannten Aufrufe

| Aufruf | Entscheidung |
|---|---|
| `admin-server.py:609,618` (`_start`) | `env=_tmp_sink_env(self.root)` |
| `admin-server.py:1243` (`_run`) | `env=_tmp_sink_env(self.root)` |
| `admin-server.py:1625` (`run_consistency_check`) | `env=_tmp_sink_env(self._ctx.root)` |
| `admin-server.py:5799,5805` (`_admin_start_detached`) | `env=_tmp_sink_env(root)` |
| `admin-server.py:644` (`_stop`, taskkill) | Allowlist `process-control: taskkill …` |
| `admin-server.py:5830` (`_admin_stop`, taskkill) | Allowlist `process-control: taskkill …` |
| `consistency-check.py:79,83` (`get_changed_files`) | `env=_tmp_sink_env(root)` |
| `consistency-check.py:98` (`get_new_files_vs_main`) | `env=_tmp_sink_env(root)` |
| `run_role_routing_eval.py:727` (`call_provider`) | `env=_tmp_sink_env(os.environ.copy())` |

### Abweichungen von der Aufgabenbeschreibung (Spec ist normativ)

1. **Der Guard meldet 42 statt 12 Ausreißer.** Die Aufgabenbeschreibung nennt nur die 12
   Aufrufe in `scripts/*.py`; der AST-Scan über `scripts/**` (AC-11/IC-18) findet zusätzlich
   30 ungepinnte Aufrufe in `scripts/lib/**`. Diese Dateien sind **nicht** Teil des
   Task-11-Dateisatzes und teilweise Task 12/14 zugeordnet (`doctor_detectors.py`,
   `cli_commands.py`), daher wurden sie **klassifiziert statt umgebaut**: 21 Allowlist-Einträge
   (`git-plumbing`, `pure-read`, `process-control`, `external-cli`, `deferred`). Kein
   Library-Aufruf wurde ohne Begründung stummgeschaltet.
2. **Zwei der 12 werden allowlisted statt gepinnt.** Die beiden `taskkill`-Stellen
   (`_stop`, `_admin_stop`) sind reine Prozesssteuerung ohne Datei-/Temp-Erzeugung; ein
   `tmp_env`-Aufruf würde das Stoppen des Servers bei deaktiviertem/kaputtem Sink blockieren.
3. **`consistency-check.py` pinnt statt zu allowlisten.** Die drei `git`-Aufrufe sind zwar
   reine Lese-Befehle (Allowlist wäre zulässig), aber der Plan nennt die Datei explizit als
   „Env-Pin an drei Stellen"; der Pin ist über `_tmp_sink_env` sink-aus-sicher (Fallback
   `None`) und hält den Rollback-Hebel `enabled: false` funktionsfähig.
4. **`deferred`-Kategorie im Allowlist-Schema (2 Einträge).** `cli_commands.py` startet den
   Admin-Server (`_build_context`, `_run_common_tail`), ist aber Task 14 zugeordnet und durfte
   hier nicht geändert werden. Die Einträge nennen die Owning-Task; der Guard akzeptiert
   `deferred:` nur mit Task-Nennung. **Offen:** in Task 14 (oder einem Folge-Task) auf
   `env=_tmp_sink_env(...)` umstellen, dann Einträge entfernen.
5. **`doctor_detectors.py:detect_command` und `plugin_test.py` bleiben allowlisted**, weil
   Task 12 die Datei besitzt bzw. der MCP-Handshake bereits ein explizites gemergtes
   `child_env` übergibt und das Plugin seine Temp-Dateien selbst verwaltet.
6. **Kein Commit, kein Push** — Step 4 bleibt offen (Commit-Authority beim `git`-Agenten).

### Offene Punkte / Risiken

- **AC-94-Rotmarks unverändert:** `test_optimizer_never_uses_systemtemp` bleibt rot
  (`resolve_tmp_paths` → `tmp_sink_location_error` → `gettempdir`, vorbestehend seit Task 1/2).
  Die volle Paarung `test_meta_optimizer_{runner,applier}.py` wurde wegen der 742-s-Laufzeit
  aus Task 10 nicht erneut gefahren; die geänderten Module (backup/admin/consistency/eval)
  sind disjunkt. Keine Verschlechterung festgestellt.
- **`deferred`-Einträge sind eine bewusste Schuld:** die beiden Admin-Server-Starts aus
  `cli_commands.py` erben weiterhin das Parent-Env. Bis Task 14 gepinnt ist, hängt der
  Temp-Pfad dieser Server von der aufrufenden Shell ab (der Agenten-Shell-Pin aus
  `TMP_SINK_ENV_PIN_BLOCK` deckt den Normalfall ab).
- **Allowlist-Pflege:** neue Subprozesse lassen den Guard fehlschlagen (gewollt); ein
  verschobener/umbenannter Aufruf macht seinen Eintrag „stale" und ebenfalls rot
  (`test_allowlist_entries_match_a_current_call_site`).

## Evidence — Task 20

### Rot (Assertion ergänzt, Adapter noch unverändert)

`python3 -m pytest tests/test_antigravity_hooks_registration.py::test_adapter_normalizes_edit_tool_names -q`
→ Exit 1:

```
F                                                                        [100%]
=================================== FAILURES ===================================
___________________ test_adapter_normalizes_edit_tool_names ____________________

tmp_path = PosixPath('/tmp/pytest-of-hermes/pytest-89/test_adapter_normalizes_edit_t0')

    def test_adapter_normalizes_edit_tool_names(tmp_path):
        out_file = tmp_path / "received.json"
        fixture = _adapter_fixture(tmp_path, '#!/bin/bash\ncat > "$ADAPTER_TEST_OUT"\nexit 0\n')
        payload = json.dumps({
            "hookEventName": "PreToolUse",
            "toolCall": {"name": "write_to_file", "args": {"FilePath": "/ws/a.md"}},
            "workspacePaths": ["/ws"],
        })
        _run_adapter(fixture, payload, env_out=out_file)

        received = json.loads(out_file.read_text(encoding="utf-8"))
        assert received["tool_name"] == "Write"
>       assert received["tool_input"]["file_path"] == "/ws/a.md"  # FilePath -> file_path
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       KeyError: 'file_path'

tests/test_antigravity_hooks_registration.py:354: KeyError
=========================== short test summary info ============================
FAILED tests/test_antigravity_hooks_registration.py::test_adapter_normalizes_edit_tool_names
1 failed in 0.35s
```

Ursache: der Adapter reicht unbekannte `args`-Keys unverändert durch
(`tool_input[ARG_KEY_MAP.get(k, k)] = v`), `FilePath` landete also als
`tool_input.FilePath` — der Hook-Lookup (`repo-containment-impl.sh`) liest aber
`file_path` und sah damit keinen Pfad (fail-open für Edit/Write-Prüfungen).

### Grün (nach der Implementierung)

| # | Kommando | Ergebnis |
|---|---|---|
| 1 | `python3 -m pytest tests/test_antigravity_hooks_registration.py::test_adapter_normalizes_edit_tool_names -q` | `1 passed in 0.28s`, Exit 0 |
| 2 | `python3 -m pytest tests/test_antigravity_hooks_registration.py tests/test_repo_containment_hook.py -q` | `60 passed in 16.63s`, Exit 0 |
| 3 | `python3 scripts/sync.py --validate` (Lauf 1) | Exit 0, `1 action(s) | 381 skipped | 2 warning(s)` — die eine COPY-Aktion betraf die mitvalidierte Nebenkopplung `test-repo` (`/home/hermes/repos/agent-meta-test`), **nicht** dieses Repo |
| 4 | `python3 scripts/sync.py --validate` (Lauf 2+3) | Exit 0, `0 action(s) | 382 skipped | 2 warning(s)`; beide WARNINGS vorbestehend (`active-set.gate-dropped`, Submodul-Checkout `external/awesome-claude-code`) ⇒ 0 neue Findings |
| 5 | `git status --porcelain` | nur die erwarteten Pfade: Adapter, die zwei Hook-Testmodule, Plan + Status (kein unerwarteter Write) |

Der Drift zwischen Quelle und getrackter Deployed-Kopie (siehe Abweichung 3) schlägt in
keiner der beiden `--validate`-Läufe als Finding auf.

### Abgedeckte ACs (Task 20)

| AC | Test | Aussage |
|---|---|---|
| AC-40 | `test_adapter_normalizes_edit_tool_names` | `toolCall.args.FilePath` kommt als `tool_input.file_path` beim Ziel-Hook an; die bestehende Tool-Namens-Normalisierung (`write_to_file` → `Write`) bleibt unverändert |

### Abweichungen von der Aufgabenbeschreibung (Spec ist normativ)

1. **Kein separater PascalCase-Contract-Test** — AC-40 fordert ihn ausdrücklich nicht; die
   Assertion sitzt im bestehenden Test (wie im Plan-Interface festgelegt).
2. **Nur eine Produktionszeile** (`'FilePath': 'file_path'` in `ARG_KEY_MAP`): `TOOL_MAP`,
   Deny/Allow-Vertrag, `mktemp`-Pfad und EXIT-Trap sind unberührt, kein Provider-Name im
   Code. Der Adapter bleibt datengetrieben (`ARG_KEY_MAP`).
3. **Adapter-Version bleibt `1.1.0`, Deployed-Kopie bleibt alt (Scope-Entscheidung).** Plan-Step 2
   verlangt genau eine Zeile und keinen Versions-Bump; der Drift-Check
   (`hooks.stale-deployed-version`) vergleicht ausschließlich `# version:` und meldet daher
   **nichts**. Folge: die getrackte Kopie `.agents/hooks/antigravity-json-adapter.sh` (gelistet
   in `.meta-config/generated-file-hashes.json`) trägt weiterhin den alten `ARG_KEY_MAP`, und
   dieser Repo-interne Sync meldet sie als „unchanged" — der Drift ist über `--validate`
   **nicht** sichtbar. **Offen für den Orchestrator:** Adapter-Version auf `1.2.0` bumpen,
   `python3 scripts/sync.py` einmal laufen lassen und `.agents/hooks/antigravity-json-adapter.sh`
   (+ Hash-Baseline) mitcommitten; erst der Bump macht die Drift für Downstream-Projekte als
   Warnung sichtbar. Der Datei-Scope dieses Auftrags (nur Adapter + Test + zwei Ledger) wurde
   deshalb eingehalten.
4. **Step 4 (Commit) nicht ausgeführt** — kein Commit-Auftrag für diesen Subagenten; die
   Plan-Checkbox bleibt deshalb offen (gleiche Konvention wie Tasks 1–9, deren Step 4 trotz
   existierender Commits offen ist). Der Status-Eintrag führt `— (pending)`.
5. **`--validate`-Lauf 1 hat die Nebenkopplung `test-repo` mitgeschrieben:** die COPY-Aktion
   zielte auf `/home/hermes/repos/agent-meta-test/.agents/hooks/antigravity-json-adapter.sh`
   (in `.meta-config/project.yaml` als `test-repo` deklariert). Das ist vorbestehendes
   `--validate`-Verhalten (kein `dry_run` für die Sekundärprojekte), nicht durch diesen Task
   eingeführt; das Repo-eigene `.agents/` blieb unberührt.

### Risiken / Interpretationen

- **Stille Drift der Deployed-Kopie:** `.agents/hooks/antigravity-json-adapter.sh` ist
  getrackt und bleibt nach diesem Task auf dem alten Mapping; für dieses Self-Hosting-Repo
  greift der Fix erst nach einem `sync.py`-Lauf. Kein Test und kein `--validate`-Finding
  erzwingt das, weil die Versionsprüfung inhaltsblind ist.
- **Keine AC-40-Abdeckung für den Downstream-Deploy-Pfad:** getestet ist der
  Adapter-Aufruf mit dem AGY-Payload, nicht die ausgerollte Kopie. Ein Projekt mit alter
  Kopie bleibt bis zum nächsten Sync ungeschützt; das ist bewusst außerhalb dieses Tasks.
- Nicht ausgeführt: die volle Testsuite (nur die im Plan-Step 3 genannten Module plus
  `sync.py --validate`).

## Evidence — Task 12

### Rot (vor der Implementierung)

Erster Lauf nach dem Schreiben der Tests (der eine zusätzliche Fehlschlag war ein falscher
Import im neuen Test selbst, vor der Implementierung korrigiert):

`python3 -m pytest tests/test_tmp_sink_default_on.py tests/test_doctor_runner.py -q`
→ `4 failed, 79 passed in 20.85s`, Exit 1. Die beiden geforderten Anker (nach Korrektur des
Test-Imports, weiterhin ohne Produktionsänderung):

`python3 -m pytest tests/test_doctor_runner.py::test_tmp_sink_check_uses_resolver_reason tests/test_tmp_sink_default_on.py::test_tmp_sink_entry_uses_resolved_path -q`
→ `2 failed in 1.23s`, Exit 1:

```
___________________ test_tmp_sink_check_uses_resolver_reason ___________________
...
>       monkeypatch.setattr(doctor_detectors, "resolve_tmp_paths", fake_resolver)
E       AttributeError: <module 'lib.doctor_detectors' from '/home/hermes/repos/agent-meta/scripts/lib/doctor_detectors.py'> has no attribute 'resolve_tmp_paths'

tests/test_doctor_runner.py:711: AttributeError
____________________ test_tmp_sink_entry_uses_resolved_path ____________________

tmp_path = PosixPath('/tmp/pytest-of-hermes/pytest-137/test_tmp_sink_entry_uses_resol0')

    def test_tmp_sink_entry_uses_resolved_path(tmp_path):
        """AC-31/IC-16: the entry comes from TmpPaths.relative, not a second parse."""
        cfg = {"enabled": True, "tmp-sink": {"enabled": True, "path": "scratch/out"}}
>       assert _tmp_sink_gitignore_entry(_paths(tmp_path, cfg)) == "scratch/out/"
E       AssertionError: assert '.tmp/' == 'scratch/out/'
E
E         - scratch/out/
E         + .tmp/

tests/test_tmp_sink_default_on.py:47: AssertionError
=========================== short test summary info ============================
FAILED tests/test_doctor_runner.py::test_tmp_sink_check_uses_resolver_reason
FAILED tests/test_tmp_sink_default_on.py::test_tmp_sink_entry_uses_resolved_path
2 failed in 1.23s
```

AST-Guard gegen den Ist-Zustand auf `HEAD` (gleiche Prüflogik wie der Test, gegen
`git show HEAD:...` ausgeführt):

```
HEAD scripts/lib/gitignore.py: resolve_effective_repo_containment=True, get_path(tmp-sink.path)=[]
HEAD scripts/lib/doctor_detectors.py: resolve_effective_repo_containment=False, get_path(tmp-sink.path)=['repo_containment.tmp-sink.path']
```

### Grün (nach der Implementierung)

| # | Kommando | Ergebnis |
|---|---|---|
| 1 | `python3 -m pytest tests/test_tmp_sink_default_on.py tests/test_doctor_runner.py -q` | `83 passed in 20.61s`, Exit 0 |
| 2 | `python3 -m pytest tests/test_tmp_sink_default_on.py tests/test_doctor_runner.py tests/test_repo_containment_tmp_sink.py tests/test_gitignore_provider_dirs.py tests/test_gitignore_keep.py tests/test_gitignore_context_file_protection.py -q` | `147 passed in 23.40s`, Exit 0 (6 Module) |
| 3 | `python3 -m pytest tests/test_doctor_cli.py tests/test_doctor_fixtures.py tests/test_doctor_runner.py -q` | `205 passed in 128.56s`, Exit 0 (3 Module, Doctor-Nachbarschaft) |
| 4 | `python3 -m pytest tests/test_repo_containment_tmp_sink.py tests/test_repo_containment_consistency.py tests/test_gitignore_provider_dirs.py tests/test_gitignore_keep.py tests/test_gitignore_context_file_protection.py tests/test_tmp_sink_default_on.py -q` | `85 passed in 12.38s`, Exit 0 (6 Module, Gitignore-/Sink-Nachbarschaft) |
| 5 | `python3 -m pytest tests/test_tmp_sink_env_coverage.py tests/test_repo_containment_consistency.py -q` | `18 passed in 5.20s`, Exit 0 |
| 6 | `python3 -m pytest tests/test_runtime_config_readers.py -q` | `1 failed, 20 passed in 0.48s`, Exit 1 — **vorbestehend und taskfremd**, siehe Abweichung 6; mit `--deselect …::test_a_registry_evidence_lines_exist_and_mention_the_key`: `20 passed in 0.44s`, Exit 0 |
| 7 | `python3 scripts/sync.py --validate` | Exit 0; `0 action(s)  |  382 skipped  |  2 warning(s)` — beide vorbestehend (`active-set.gate-dropped`, Submodul-Checkout `external/awesome-claude-code`) |
| 8 | `python3 -c "ast.parse(..., feature_version=(3, 9))"` über die vier geänderten Dateien | `py3.9 syntax ok` für alle vier |
| 9 | End-to-End: `python3 scripts/sync.py --config /tmp/t12_scratch/.meta-config/project.yaml --dry-run --check` | Exit 1 (erwarteter `--check`-Drift im Scratch-Projekt); Managed-Block-Zeile enthält `scratch/out/` und `DRY-RUN: would write self-ignoring scratch/out/.gitignore` — der Sync-Pfad nutzt den konfigurierten Sink, nicht `.tmp/` |

### Abgedeckte ACs (Task 12)

- **AC-31** — `tests/test_tmp_sink_default_on.py::test_tmp_sink_entry_uses_resolved_path`:
  `TmpPaths` für `scratch/out` ⇒ Eintrag `scratch/out/`; `enabled: false` ⇒
  `_tmp_sink_gitignore_entry(...) is None` und kein Eintrag im Managed-Block.
- **AC-32** — `tests/test_doctor_runner.py::test_tmp_sink_check_uses_resolver_reason`:
  `tmp-sink.path: ../out` ⇒ Finding `doctor.tmp-sink-location` mit
  `Severity.ERROR` und der Meldung
  `repo_containment.tmp-sink.path violates the sink rules: must not contain '..' segments`
  (Reason identisch zum Validator, ohne eigene Parser-Kopie). Ein gestubbter Resolver
  beweist zusätzlich, dass `_sink_hits` den Resolver und nicht die Config nutzt.
- **Zusatz IC-16** — `test_sink_consumers_do_not_reparse_the_config` (AST):
  `resolve_effective_repo_containment` kommt in `gitignore.py`/`doctor_detectors.py` nicht
  mehr vor; `get_path(...tmp-sink.path...)` in `doctor_detectors.py` ebenfalls nicht.

### Implementierung

| Stelle | Vorher | Nachher |
|---|---|---|
| `gitignore.py::_tmp_sink_gitignore_entry` | `(repo_containment_cfg)` + eigener `resolve_effective_repo_containment`-Aufruf | `(paths: TmpPaths)`, Eintrag aus `paths.relative`, `enabled=False` ⇒ `None`; kein Config-Parsing |
| `gitignore.py::compute_base_gitignore_entries` | 4. Argument = `repo_containment`-Block | unverändert rückwärtskompatibel, zusätzlich `tmp_paths=`/`project_root=`; Legacy-Fallback ruft den Zentral-Resolver |
| `gitignore.py::_tmp_sink_gitignore_enabled` | — | neuer, reiner Boolean-Leser für `tmp-sink.gitignore` (Default AN), weil `TmpPaths` laut IC-01/IC-02 kein Gitignore-Flag trägt |
| `doctor_detectors.py::_sink_hits` | `get_path(...tmp-sink.path...)` + eigene `tmp_sink_path_error`/`tmp_sink_location_error`-Kaskade | `resolve_tmp_paths(env.project_root, env.config)`; `tmp-sink.invalid-path` ⇒ `Hit(CHECK_TMP_SINK, Severity.ERROR, reason=<Resolver-Reason>)`; andere Resolver-Codes feuern den Check nicht |
| `tests/test_doctor_runner.py::test_sink_check_uses_central_repo_containment_functions` | pinnte die entfernten `tmp_sink_*`-Re-Exports | ersetzt durch `test_sink_check_uses_the_central_resolver` (Identität `doctor_detectors.resolve_tmp_paths is lib.tmp_paths.resolve_tmp_paths`) |

### Abweichungen von der Aufgabenbeschreibung

1. **`compute_base_gitignore_entries` behält seine `repo_containment_cfg`-Signatur.** Die
   Aufrufer außerhalb der vier Task-Dateien (`sync_pipeline.py`, sechs Testmodule) übergeben
   weiterhin den Config-Block; eine Signaturänderung hätte Dateien außerhalb des
   Task-Scopes erzwungen. Stattdessen nimmt die Funktion optional `tmp_paths` (und
   `project_root` für den Fallback) entgegen; die Produktion nutzt den zentralen Resolver,
   weiterhin ohne eigene Pfadinterpretation in `_tmp_sink_gitignore_entry`.
2. **Legacy-Fallback nutzt `Path.cwd()` als Projektwurzel.** Nur wenn kein `tmp_paths`
   übergeben wird (heutige `sync_pipeline`-Aufrufstelle, Bestands-Tests). Der einzige
   konsumierte Wert ist `TmpPaths.relative`; End-to-End-Lauf 9 belegt den korrekten Eintrag
   auch bei abweichendem `cwd`. Eine spätere Umstellung von `sync_pipeline.py` auf
   `tmp_paths=resolve_tmp_paths(project_root, config)` ist der saubere Folgeweg.
3. **`_sink_hits` extrahiert den nackten Reason aus der Resolver-Meldung.** Der Resolver
   formatiert lexikalische Fehler als `"'…path' is invalid (<reason>); using '.tmp'."` und
   Lagefehler als `"repo_containment.tmp-sink.path '<rel>': <reason>"`. AC-32 verlangt den
   Reason ohne Pfadkontext; der Check parst dabei **keine Config**, sondern nur den bereits
   erzeugten Resolver-Text (`(<reason>); using` bzw. `rpartition(": ")`).
4. **`_tmp_sink_gitignore_enabled` liest genau einen Boolean** (`tmp-sink.gitignore`), weil
   `TmpPaths` dieses Feld per Spec nicht enthält. Der Pfad wird ausschließlich über
   `TmpPaths.relative` bezogen (AST-Guard belegt es).
5. **Step 4 (Commit) nicht ausgeführt** — kein Commit-Auftrag für diesen Subagenten; die
   Plan-Checkbox bleibt offen, der Status führt `— (pending)` (Konvention wie Tasks 1–11).
6. **Vorbestehender roter Regressionstest, nicht durch Task 12 verursacht:**
   `test_runtime_config_readers.py::test_a_registry_evidence_lines_exist_and_mention_the_key`
   scheitert an `admin-ui`-Evidence `scripts/admin-server.py:515` (Zeile ist leer).
   `git diff --quiet HEAD -- scripts/admin-server.py config/runtime-config-readers.yaml`
   bestätigt: beide Dateien sind gegenüber `HEAD` unverändert; die Zeile war schon auf `HEAD`
   leer (Task 11 hat `admin-server.py` verschoben). Eigentümer: Task 11 bzw. ein
   Config-Evidence-Fix außerhalb dieses Scopes.

### Risiken / Interpretationen

- Der Legacy-Fallback in `compute_base_gitignore_entries` ist nur korrekt, solange er
  ausschließlich `TmpPaths.relative` konsumiert. Eine künftige Nutzung von `absolute`/`env`
  an dieser Stelle würde die echte Projektwurzel benötigen (siehe Abweichung 2).
- Der Doctor prüft weiterhin nur `tmp-sink.invalid-path`; `tmp-sink.system-temp-exception`
  bleibt Sache des Validators. Das entspricht dem bisherigen Check-Zuschnitt, ist aber
  bewusst als Scope-Entscheidung dokumentiert.
- Der vorbestehende `test_runtime_config_readers`-Fehlschlag bleibt offen und kann das
  Task-15/18-Gate rot halten, bis die Evidence-Zeile aktualisiert ist.


## Evidence — Task 13

### Rot (vor der Implementierung, verbatim)

`python3 -m pytest tests/test_opencode_primary_edit_lock.py tests/test_repo_containment_consistency.py -q`
→ Exit 1:

```
FAILED tests/test_opencode_primary_edit_lock.py::test_edit_allow_derived_from_tmp_sink
FAILED tests/test_opencode_primary_edit_lock.py::test_edit_allow_sink_disabled_keeps_static_scope_only
FAILED tests/test_opencode_primary_edit_lock.py::test_provider_tools_static_scope_has_no_sink_literal
3 failed, 22 passed in 1.43s
```

AC-17-Kern (Auszug aus dem Einzellauf):

```
>       assert permission["edit"] == _SINK_SCOPED
E       AssertionError: assert {'*': 'deny',.../**': 'allow'} == {'*': 'deny',.../**': 'allow'}
E         Left contains 1 more item:
E         {'.tmp/**': 'allow'}
E         Right contains 1 more item:
E         {'scratch/out/**': 'allow'}
tests/test_opencode_primary_edit_lock.py:129: AssertionError
```

Der Transform las die statische Liste `.tmp/**` und ignorierte den konfigurierten Sink
`scratch/out`; die statische `.tmp/**`-Zeile war zusätzlich separat rot.

### Grün (nach der Implementierung)

| # | Kommando | Ergebnis |
|---|---|---|
| 1 | `/usr/bin/python3 -m pytest tests/test_opencode_primary_edit_lock.py tests/test_repo_containment_consistency.py -q` | `25 passed in 1.46s`, Exit 0 |
| 2 | `/usr/bin/python3 -m pytest tests/test_opencode_agents.py tests/test_opencode_runtime_gate.py tests/test_opencode_v2_aux_selection.py tests/test_opencode_v2_config.py tests/test_opencode_v2_schema.py tests/test_opencode_v2_spike.py -q` | `87 passed, 15 warnings in 8.01s`, Exit 0 |
| 3 | `/usr/bin/python3 -m pytest tests/test_opencode_v2_surface.py -q` | `130 passed in 59.03s`, Exit 0 |
| 4 | `/usr/bin/python3 -m pytest tests/test_provider_toml_transform.py tests/test_provider_agnostic_dispatch.py tests/test_transform_contracts.py tests/test_agents_frontmatter.py tests/test_dispatch_permissions_frontmatter.py tests/test_model_inherit.py tests/test_read_only_sandbox.py tests/test_reference_standards_strip.py tests/test_subagent_allowlist_frontmatter.py tests/test_active_set_single_source.py -q` | `228 passed in 15.86s`, Exit 0 |
| 5 | `/usr/bin/python3 scripts/sync.py --validate` | `0 action(s)  |  382 skipped  |  2 warning(s)`, Exit 0 (beide WARNINGS vorbestehend: `active-set.gate-dropped`, Submodul-Checkout `external/awesome-claude-code`) |
| 6 | `/usr/bin/python3 scripts/sync.py --dry-run` | `0 action(s)  |  449 skipped  |  35 warning(s)`, Exit 0 |
| 7 | `python3 -c "ast.parse(..., feature_version=(3, 9))"` auf `provider_transform.py` | `py3.9 syntax ok` |

Hinweis: `tests/test_provider_transform*.py` existiert nicht; die Regressionszeilen 2–4
sind die tatsächlich vorhandenen transform-/opencode-konsumierenden Module.

### Abgedeckte ACs (Task 13)

- **AC-17** — `test_edit_allow_derived_from_tmp_sink`: bei `path: scratch/out` ist
  `permission.edit == {"*": "deny", "scratch/out/**": "allow", ".meta-viz/**": "allow"}`,
  `.tmp/**` fehlt, `*` steht zuerst.
- **IC-10-Randfälle** — `test_edit_allow_sink_disabled_keeps_static_scope_only`
  (Sink aus ⇒ nur `.meta-viz/**`) und `test_provider_tools_static_scope_has_no_sink_literal`
  (statische Liste enthält kein Sink-Literal mehr).
- **AC-20** — `test_no_hook_support_warning_still_emitted`: `repo-containment.no-hook-support`
  bleibt `Severity.WARNING`, kein ERROR, `print_json_report(...) == 0`.

### Ableitung (Implementierung)

| Stelle | Vorher | Nachher |
|---|---|---|
| `provider_transform.py::_tmp_sink_edit_allow_paths` (neu) | — | `resolve_tmp_paths(project_root, config)` ⇒ `(f"{TmpPaths.relative}/**",)`; `enabled=False` ⇒ `()`; `TmpSinkError` ⇒ WARNING + `()` (fail-closed, kein Sync-Abbruch) |
| `provider_transform.py::_apply_agent_transform` (Opencode-Zweig) | `edit_allow_paths = tuple(static)` | `tuple(dict.fromkeys(derived + static))` — Sink zuerst, dann statische Fallback-Einträge; explizit leere Liste bleibt der dokumentierte Opt-out (ADR-5 A) ⇒ Skalar `deny` |
| `config/provider-tools.yaml::opencode_primary_edit_allow` | `[".tmp/**", ".meta-viz/**"]` | `[".meta-viz/**"]` + Kommentar: Sink wird zur Sync-Zeit aus `TmpPaths.relative` abgeleitet |

Keine Provider-Namens-Verzweigung: die Ableitung hängt an `TmpPaths`-Daten und am
`deny_edit`-Prädikat (`has_hooks`/Tier), nicht an `provider == "Opencode"`.

### Abweichungen von der Aufgabenbeschreibung

1. **Regression-Glob `tests/test_provider_transform*.py` existiert nicht.** Stattdessen wurden
   die tatsächlichen Konsumenten aufgeführt (Zeilen 2–4 der Grün-Tabelle); keine
   Ersatzdatei angelegt.
2. **Explizit leere `opencode_primary_edit_allow`-Liste schaltet die Ableitung ab.** Ohne
   diese Auslegung hätte der Sink automatisch `.tmp/**` ergänzt und den in Spec A/ADR-5
   dokumentierten Opt-out („leere Liste ⇒ `edit: deny`") still entwertet. Der bestehende
   Test `test_empty_allow_list_falls_back_to_scalar_deny` bleibt damit unverändert grün.
3. **Zusätzlich geändert (Auftrag, nicht Code-Scope):** Plan-Checkboxen Task 13 und dieser
   Ledger. Die vier Code-Dateien sind exakt die vorgegebenen.

### Risiken / Interpretationen

- `.opencode/agents/orchestrator.md` wurde nicht neu generiert. Mit dem Framework-Default
  (`.tmp`) ist das gerenderte Ergebnis byte-identisch zu vorher; ein Projekt mit eigenem
  Sink erhält den neuen Scope erst beim nächsten echten Sync.
- Der `temp-literal.provider-advisory`-WARNING (Spec, Provider-Agnostik) ist nicht Teil von
  Task 13; er gehört zum Consistency-Check (Task 14/15).
- Die `.meta-viz/**`-Zeile bleibt statisch; eine künftige Konfigurierbarkeit dieses Pfads
  müsste ebenfalls über den Resolver laufen.

## Evidence — Task 14

### Rot (vor der Implementierung, verbatim)

`python3 -m pytest tests/test_consistency_temp_literals.py -q` → Exit 1:

```
==================================== ERRORS ====================================
___________ ERROR collecting tests/test_consistency_temp_literals.py ___________
ImportError while importing test module '/home/hermes/repos/agent-meta/tests/test_consistency_temp_literals.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/test_consistency_temp_literals.py:27: in <module>
    from lib.consistency.temp_literals import (
E   ModuleNotFoundError: No module named 'lib.consistency.temp_literals'
=========================== short test summary info ============================
ERROR tests/test_consistency_temp_literals.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.34s
```

`ModuleNotFoundError` ist die von `ImportError` abgeleitete Form des im Plan genannten
Rot-Belegs; alle fünf Tests des Moduls waren vor der Implementierung nicht sammelbar.

### Grün (Befehl → Anzahl → Exit)

| # | Befehl | Ergebnis | Exit |
|---|---|---|---|
| 1 | `python3 -m pytest tests/test_consistency_temp_literals.py -q` | `5 passed` | 0 |
| 2 | `python3 -m pytest tests/test_temp_literals.py tests/test_tmp_sink_env_coverage.py tests/test_consistency_checks.py tests/test_consistency_reference_standards.py -q` | `65 passed` | 0 |
| 3 | `python3 -m pytest tests/test_repo_containment_consistency.py tests/test_orchestrator_strict_visibility.py tests/test_rule_variables.py -q` (Nachbarschaft des geänderten `cli_commands.py`) | `32 passed` | 0 |
| 4 | `python3 scripts/sync.py --validate` | 0 ERROR; 22 WARNING `temp-literal.system-temp` (Task-16-Goldens, siehe unten); 2 vorbestehende Sync-Warnungen (`active-set.gate-dropped`, Submodul-Checkout `external/awesome-claude-code`) | 0 |
| 5 | `python3 scripts/consistency-check.py` | `22 warning(s) found` — alle `temp-literal.system-temp`, 0 ERROR | 0 |

### AC-21 — WARNING mit Datei und Zeile, Allowlist unterdrückt

`check_temp_literals(root, root, {})` auf einem synthetischen Template mit
`docker logs c > /tmp/probe.log` liefert genau ein Finding:

```
severity = WARNING, check = temp-literal.system-temp,
file = agents/1-generic/demo.md,
message = "system temp literal in shipped text on line 3: Run: docker logs c > /tmp/probe.log 2>&1"
```

`print_report(...) == 0` (kein Exit). Ein vollständiger Allowlist-Eintrag
`{path: "agents/1-generic/demo.md", pattern: "/tmp/probe\\.log", reason: "…"}` entfernt das
Finding vollständig. `test_warning_and_allowlist` deckt beide Hälften ab.

### Scope (IC-11) — sechs Wurzeln, je ein eigener Nachweis

`test_every_scope_root_is_scanned` legt je eine Probe-Datei unter genau einer Wurzel an und
prüft **jede Wurzel einzeln** (nicht nur den Gesamtlauf):

| Wurzel | Scan |
|---|---|
| `agents/**` | rekursiv, Text-Endungen (`_SCOPE_DIRS`) |
| `standalone/**` | rekursiv, Text-Endungen |
| `rules/1-generic/**` | rekursiv, Text-Endungen |
| `config/**` | rekursiv, Text-Endungen |
| `tests/fixtures/slimming-golden/**` | rekursiv, Text-Endungen |
| `tests/conftest.py` | Einzeldatei (`_SCOPE_FILES`) |

Negativ-Kontrolle im selben Test: identische Literale unter `scripts/out-of-scope.py` und
`README.md` erzeugen **kein** Finding. `Finding.file` ist immer repo-relativ (`path` der
Allowlist), die Zeile steht in der Meldung.

### Allowlist-Semantik

`.meta-config/temp-literal-allowlist.yaml` wird über `lib.io.load_yaml_file(on_error="default")`
geladen (fehlende/kaputte Datei ⇒ leere Liste, kein Crash). Ein Eintrag unterdrückt nur, wenn
`path` (repo-relativer Glob, `fnmatch`) **und** `pattern` (Regex auf die Zeile) passen und
`reason` nicht leer ist. Unbekannte Felder (z. B. `expires`) werden in Task 14 noch ignoriert —
die Feld-Whitelist (`_ALLOWED_ENTRY_FIELDS`) liegt bereit, die Ablehnung samt eigener WARNING
ist Task 22 (AC-39).

### Codes

| Code | Auslöser | Heute im Repo |
|---|---|---|
| `temp-literal.system-temp` | AC-01-Muster in einer der sechs Wurzeln | 22 (nur Task-16-Goldens + `tests/conftest.py`) |
| `temp-literal.sink-relative` | `TMPDIR`/`TEMP`/`TMP`/`--basetemp` auf einen **relativen** Wert gepinnt (ADR-12) | 0 |
| `temp-literal.subprocess-env` | `subprocess.*` unter `scripts/**` ohne `tmp_env`-Ableitung und ohne vollständigen `temp-env-allowlist`-Eintrag | 0 |
| `temp-literal.toolchain-cache-in-repo` | `system-temp-exception.toolchain-caches: true` (Resolver-Wert) | 0 (Default `false`) |
| `temp-literal.provider-advisory` | primäre Rolle mit skalarem `edit: allow` auf einem Provider ohne verifizierten Hook-Protokoll | 0 (der Orchestrator trägt seit Task 13 einen Pfad-Scope) |

### Task-11-Schuld getilgt

`_admin_tmp_env(root)` in `scripts/lib/cli_commands.py` liefert `tmp_env(paths)` (TMPDIR/TEMP/TMP
absolut, PATH/HOME geerbt) für die beiden Admin-Server-Starts in `_build_context` und
`_run_common_tail`; bei deaktiviertem/nicht auflösbarem Sink `None` (Parent-Env, Rollback-Hebel
bleibt funktionsfähig). Beide `deferred:`-Einträge aus `.meta-config/temp-env-allowlist.yaml`
wurden entfernt. Verifikation: `tests/test_tmp_sink_env_coverage.py` grün (inkl.
`test_allowlist_entries_match_a_current_call_site` — keine verwaisten Einträge) und direkter
Aufruf:

```
TMPDIR=/home/hermes/repos/agent-meta/.tmp TEMP=… TMP=…  (alle absolut, PATH/HOME geerbt)
```

### Abweichungen vom Auftrag

1. **Doppelbericht vermieden (`include_temp_literals`).** `sync.py --validate` ruft sowohl
   `run_checks` als auch den `_strict_findings`-Block auf. Damit die Familie nicht zweimal
   gedruckt wird, hat `run_checks` den Schalter `include_temp_literals` (Default `True` für den
   Standalone-CLI); `_run_consistency_checks` setzt ihn auf `False`, der `_strict_findings`-Block
   ist der einzige Melder in `--validate`. Beide vom Auftrag genannten Registrierungen existieren.
2. **`temp-literal.sink-relative` präzisiert.** Die Spec nennt nur den Code, keinen Auslöser.
   Ausgelegt als ADR-12-Verstoß: ein relativer `TMPDIR`/`TEMP`/`TMP`/`--basetemp`-Wert
   (Prosa wie `--basetemp to use` zählt nicht, siehe `_looks_like_path`).
3. **`temp-literal.provider-advisory` auf die primäre Oberfläche begrenzt.** Nur die primäre
   Rolle ist von der globalen Deny-Regel betroffen, die ein skalares `edit: allow` aushebeln
   würde (Task-13-Kontext); Subagenten waren nie durch diese Regel gegated. Ein pauschal
   gemeldeter Subagenten-Scope hätte 42 Rollen gleichzeitig als advisory gemeldet, ohne
   Zusatzinformation. Der Fall feuert nachweislich, sobald eine primäre Rolle ohne Pfad-Scope
   gerendert wird (manueller Probe gegen `.opencode/agents/orch.md`).
4. **22 `temp-literal.*`-WARNINGS statt 0 (Task-16-Reste).** Alle 22 liegen in
   `tests/fixtures/slimming-golden/**` (21) und `tests/conftest.py` (1) — genau die Dateien, die
   Task 16 rebaselined; die Goldens frieren noch `--basetemp=/tmp/$USER/…` und `/tmp/…`-Logs ein.
   Das sind echte Reste, keine False Positives; eine Allowlist-Ausnahme wäre falsch, weil Task 16
   die Quelldateien ohnehin ersetzt. Nach Task 16 muss die Zahl auf 0 fallen (Gate für Task 18).
5. **Zusätzlich geändert (Auftrag, nicht Code-Scope):** `.meta-config/temp-env-allowlist.yaml`
   (Schuld-Abbau) und die zwei Ledger-Dokumente. Die vier Task-14-Dateien sind exakt die
   vorgegebenen.

### Risiken / Interpretationen

- `tests/test_temp_literals.py` deklariert das AC-01-Muster bis Task 15 weiterhin selbst; der
  Einzelquellen-Guard (`test_temp_literal_pattern_has_single_source_of_truth`) ist daher
  erwartungsgemäß noch rot. Task 14 hat keine zweite Kopie hinzugefügt.
- Bis Task 16 bleibt `sync.py --validate` warnungsreich (22), aber Exit 0. Der Sync-Gate-Schritt
  in Task 14 verlangt ausdrücklich nur „keine neuen ERROR".
- `_admin_tmp_env` liest `<agent_meta_root>/.meta-config/project.yaml` — konsistent mit
  `scripts/admin-server.py::_tmp_sink_env`; in einem Submodul ohne eigene Config bleibt es beim
  geerbten Env (dokumentierter Fallback, kein stiller Pin auf einen falschen Pfad).
