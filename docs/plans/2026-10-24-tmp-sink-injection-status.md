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
