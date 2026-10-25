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
