# Tmp-Sink-Injektion Implementation Plan
> Status: APPROVED (2026-10-24)
>
> **Revision 3 (2026-10-24):** Nutzerentscheidungen Q3 (Toolchain-Cache-Opt-in), Q6 (Allowlist-Schema), Q10 (Antigravity `args.FilePath` → `file_path`), Q11 (§5.5 verweist auf `PYTEST_BASETEMP`) eingearbeitet. Neue Tasks 19–22; bestehende Task-IDs 1–18 unverändert (nur `Depends on`-Ergänzungen bei Task 15/18); `pipeline_stages` unverändert.

**Goal:** `repo_containment.tmp-sink.path` als einzige Quelle der Wahrheit durchsetzen: ein Resolver (`resolve_tmp_paths`), Injektion des aufgelösten Pfads an allen 14 Inventar-Punkten (Punkt 14 = §5.5-Regeltext) der Spec, fail-closed Hook ohne Adelung des Arbeitsverzeichnisses, literal-freies `pytest --basetemp` über Config-Key und Token, keine zweite Config-Auslegung in `.gitignore`-Block und Doctor-Check.
**Architecture:** Neue Bibliothek `scripts/lib/tmp_paths.py` liefert ein unveränderliches `TmpPaths` (relative Form für Templates, absolute Form für Env/Backup/Diagnose, `pytest_basetemp`, `env`, `system_temp_exception`). Alle Konsumenten (Builder, Hook, Backup, Provider-Transform, Gitignore, Doctor, Standalone-Export, Consistency-Check) lesen dieses Ergebnis oder leiten daraus ab; der Hook spiegelt den Vertrag in Bash/Python und wird über einen Shared-Contract-Test an `TmpPaths` gebunden.
**Tech Stack:** Python 3 Stdlib (dataclasses, pathlib, tempfile, subprocess, re, unittest-artiges pytest), POSIX-sh (PreToolUse-Hooks, Shell-Quoting), PyYAML-Config, Markdown-Templates mit `{{VARIABLE}}`-Platzhaltern, pytest-Goldens.
**Spec:** docs/specs/2026-10-24-tmp-sink-injection-spec.md

## Global Constraints

- **Keine zweite Auflösung.** `resolve_tmp_paths` ist der einzige Ort, der `repo_containment.tmp-sink` in Pfade überführt (ADR-01). Bestehende Aufrufer von `resolve_effective_repo_containment` bleiben unverändert, neue Konsumenten lesen `TmpPaths` (IC-16).
- **Resolver wirft nicht bei deaktiviertem Sink** (ADR-07, IC-01): `enabled=False`, `absolute=None`, `env={}`, `relative` gesetzt und validiert. Werfend sind nur die Schreib-/Verbrauchs-APIs `resolve_output_dir`, `resolve_work_dir`, `resolve_out_path`, `tmp_env`, `tmp_sink_env_pin_block` sowie Config-Fehler (`tmp-sink.invalid-path`, `tmp-sink.system-temp-exception`).
- **Formtrennung** (ADR-02, ADR-12, IC-13): `{{TMP_SINK_PATH}}` bleibt relativ und ist die einzige Form in `agents/**` und `standalone/**`; `TMP_SINK_ABS_PATH` und `TMP_SINK_ENV_PIN_BLOCK` tragen absolute Werte und dürfen nicht in Templates gerendert werden. Der Env-Pin-Block ist die einzige dokumentierte Ausnahme.
- **Kein Provider-Namens-Branching.** Durchsetzung nur über Config-Keys, Capability-Flags (`has_hooks`) und Daten (`config/provider-tools.yaml`); kein `if provider == "Name"` (Skill `provider-agnostic`).
- **Kein neuer Hard-Exit für Literale.** Der Temp-Literal-Check meldet WARNING mit Allowlist (ADR-06, AC-21); Hard-Exit bleibt der Config-Validierung vorbehalten.
- **Keine Test-only-Bypässe im Produktionscode.** Fail-closed-Hook-Tests bauen ihre Fixture per `tempfile.mkdtemp(dir=tempfile.gettempdir())` außerhalb des Repo-Baums und prüfen per Assertion, dass kein Ancestor `.meta-config/` trägt (R12, Q8).
- **Keine Änderung an `orchestrator-guard` / `branch-guard`**, kein OS-Sandboxing, keine Migration bestehender `.tmp`-Inhalte, `cleanup: manual` bleibt Default.
- **Toolchain-Caches: Default aus, Opt-in Teil dieses Plans (Q3/ADR-13).** Default bleibt `system-temp-exception.toolchain-caches: false` (System-Temp-Cache außerhalb, damit Toolchains nicht brechen). Das Opt-in ist Task 19: nur bei `system-temp-exception.enabled: true` wirksam, `tmp_env` bleibt cache-neutral, `docker` wird nie umgeleitet, und die WARNING `temp-literal.toolchain-cache-in-repo` bleibt bestehen.
- **Allowlist-Schema ist strikt (Q6/ADR-14).** `.meta-config/temp-literal-allowlist.yaml` verlangt die Pflichtfelder `path`, `pattern` und `reason`, optional `owner`; `expires` ist **kein** Schema-Teil. Ein Eintrag ohne `reason` oder mit einem nicht unterstützten Feld unterdrückt die WARNING nicht (Task 22, AC-39).
- **Antigravity-Adapter-Vertrag (Q10/ADR-15).** `ARG_KEY_MAP` mappt `FilePath` → `file_path`, damit `args.FilePath` als `tool_input.file_path` beim Hook ankommt. Ein separater PascalCase-Contract-Test ist **nicht** Pflicht; der Regressionsfall liegt im bestehenden Adapter-Test (Task 20, AC-40).
- **§5.5-Doku verweist auf `PYTEST_BASETEMP` (Q11/ADR-16).** Der Abschnitt nennt `PYTEST_BASETEMP`/`system-temp-exception` als Quelle und enthält kein `/tmp`-Literal in der Vorschrift; die Pflichtregel „Der pytest-Basetemp darf NIE im Arbeitsbaum liegen" bleibt wörtlich erhalten (Task 21, AC-41).
- **Verifizierte Belege:** alle Pfade, Symbole und Zeilennummern sind gegen Branch `docs/tmp-sink-injection-spec` (Stand 2026-10-24) geprüft; maßgeblich sind die Symbole, die Zeilen sind Belege. Abweichungen von der Vorgabe sind im Abschnitt „Verifizierte Korrekturen" begründet.
- **Approval.** Spec und Plan sind am 2026-10-24 durch den Nutzer freigegeben (`Status: APPROVED (2026-10-24)`).

## File Structure

### Neue Dateien

- Create: `scripts/lib/tmp_paths.py` — Resolver, Datenklassen `TmpPaths`/`SystemTempException`, `tmp_env`, `tmp_sink_env_pin_block`, `resolve_pytest_basetemp`; Task 19 erweitert `tmp_sink_env_pin_block` um die opt-in Cache-Keys
- Create: `scripts/lib/consistency/temp_literals.py` — `check_temp_literals`, Muster `SYSTEM_TEMP_LITERAL_RE`, Codes `temp-literal.*`; Task 19 meldet dort `temp-literal.toolchain-cache-in-repo`, Task 22 ergänzt die Allowlist-Schema-Prüfung
- Create: `.meta-config/temp-literal-allowlist.yaml` — Allowlist `{path, pattern, reason}` (optional `owner`), Start leer; Task 22 erzwingt die Pflichtfelder und lehnt `expires` ab
- Create: `.meta-config/temp-env-allowlist.yaml` — Allowlist `{path, symbol, reason}` für Subprozesse ohne Env-Pin
- Create: `tests/test_temp_literals.py` — Guard gegen System-Temp- und Sink-Literale (AC-01, AC-26)
- Create: `tests/test_tmp_paths_builder.py` — Builder-Variablen, Token-Ersetzung, Sync-Verhalten (AC-14, AC-16, AC-25); Task 19 ergänzt den Default-aus-Fall (AC-38)
- Create: `tests/test_tmp_sink_env_coverage.py` — Subprozess-Env-Pin und Allowlist (AC-11)
- Create: `tests/test_consistency_temp_literals.py` — WARNING, Allowlist, Scope (AC-21); Task 22 ergänzt `reason`/`expires` (AC-39)
- Create: `tests/test_tmp_sink_injection.py` — Aggregations-Guard über alle vier Guard-Klassen (AC-01, AC-09, AC-11, AC-28-Fall)
- Create: `tests/test_standalone_render.py` — Standalone-Fallback `.tmp` und keine Platzhalter-Notiz (AC-27)
- Create: `tests/test_docs_tmp_sink_injection.py` — Doku-/Beispiel-Konsistenz (§5.5-Verweis, Beispiel-Config, CHANGELOG); Task 17 legt die Datei an, Task 21 ergänzt AC-41

### Geänderte Dateien

- Modify: `.meta-config/project.yaml` — `TEST_COMMANDS`/`CODE_QUALITY_RULES` auf `{{PYTEST_BASETEMP}}`, `system-temp-exception`-Block explizit; Task 19 setzt `toolchain-caches: false` explizit
- Modify: `scripts/lib/config.py` — `_build_orch_variables` (`TMP_SINK_ABS_PATH`, `PYTEST_BASETEMP`, `TMP_SINK_ENV_PIN_BLOCK`, Token-Ersetzung, `tmp-sink.pytest-token`), `_validate_repo_containment` (Ausnahme-Matrix); Task 19 ergänzt `toolchain-caches`
- Modify: `scripts/lib/consistency/placeholders.py` — drei neue Builtin-Variablen
- Modify: `scripts/lib/sync_pipeline.py` — `_sync_tmp_sink` liest `resolve_tmp_paths`
- Modify: `scripts/lib/repo_containment.py` — `work_dir_env` nur noch über `tmp_env` aufgerufen (Dokumentation des Aufrufpfads, Verhalten unverändert)
- Modify: `scripts/lib/context_report.py` — `tmp_env(paths)` statt lokalem `work_dir_env(work_dir)`
- Modify: `scripts/lib/meta_optimizer.py` — dito
- Modify: `scripts/lib/backup.py` — Staging `TemporaryDirectory(dir=<absolute>/backup-staging)`, Fallback nur bei `tmp-sink.disabled`
- Modify: `scripts/lib/gitignore.py` — `_tmp_sink_gitignore_entry(paths: TmpPaths)`, kein eigener Resolver-Aufruf
- Modify: `scripts/lib/doctor_detectors.py` — `_sink_hits` nutzt `TmpPaths` und dessen `reason`
- Modify: `scripts/lib/standalone.py` — `_standalone_variables` setzt `TMP_SINK_PATH = ".tmp"` und `TMP_SINK_ENV_PIN_BLOCK = ""`
- Modify: `scripts/lib/provider_transform.py` — `edit_allow_paths` aus `TmpPaths.relative`
- Modify: `scripts/lib/cli_commands.py` — `check_temp_literals` im `_strict_findings`-Block
- Modify: `hooks/1-generic/repo-containment-impl.sh` — Anker-Regel, kein `$PWD`-Adeln, absolute Meldungen
- Modify: `hooks/1-generic/repo-containment.sh` — nur Wrapper-Version/Header, falls dort eine Bindung an die Impl steht
- Modify: `hooks/1-generic/antigravity-json-adapter.sh` — Task 20: `ARG_KEY_MAP` mappt `FilePath` → `file_path` (Q10/ADR-15)
- Modify: `scripts/admin-server.py` — Env-Pin an den acht Subprozess-Stellen bzw. Allowlist-Begründung
- Modify: `scripts/consistency-check.py` — Env-Pin an drei Stellen, Registrierung von `check_temp_literals`
- Modify: `scripts/run_role_routing_eval.py` — Env-Pin an einer Stelle
- Modify: `config/provider-tools.yaml` — `opencode_primary_edit_allow` auf `.meta-viz/**` reduziert (Sink kommt aus `TmpPaths`)
- Modify: `config/routing/reviewers.yaml` — `notes:`-Satz ohne `.tmp/`-Literal (Test-Fixture, kein Renderer)
- Modify: `agents/1-generic/developer.md`, `code-reviewer.md`, `tester.md`, `validator.md`, `docker.md`, `devops-engineer.md`, `e2e-tester.md` — 18 System-Temp-Literale ersetzt
- Modify: `agents/1-generic/ai-security-guardian.md`, `app-lifecycle-governor.md`, `prompt-governor.md`, `security-auditor.md` — 4 Sink-Literale auf Platzhalter
- Modify: `agents/1-generic/se-validator.md`, `se-developer.md`, `se-verifier.md`, `se-integration-and-test-manager.md`, `se-interface-mgr.md`, `se-junior-developer.md`, `se-termination.md`, `se-requirements.md`, `se-critic.md`, `se-architect.md`, `se-senior-developer.md`, `se-component-requirements.md`, `test-executor.md` — vage Temp-Anweisungen benennen den Sink
- Modify: `rules/1-generic/plan-ledger.md` — Inventar 13, `.tmp/`-Literal ersetzt (Q9 entschieden)
- Modify: `standalone/agents/` — Regeneration aller betroffenen Rollen (Render-Ergebnis, siehe Task 7)
- Modify: `tests/test_tmp_sink_output_dirs.py` — Resolver, Env-Pin, Basetemp, Quoting; Task 19 ergänzt das Cache-Opt-in
- Modify: `tests/test_repo_containment_validate.py` — Ausnahme-Matrix, deaktivierter Sink; Task 19 ergänzt `toolchain-caches` ohne `enabled`
- Modify: `tests/test_repo_containment_schema.py` — Schema-Keys `system-temp-exception`
- Modify: `tests/test_repo_containment_hook.py` — Anker-Regel, bewusste Inversion, Meldungen
- Modify: `tests/test_antigravity_hooks_registration.py` — Adapter-`mktemp`-Aufräumen; Task 20 ergänzt den `FilePath`-Regressionsfall
- Modify: `tests/test_backup_round_trip_804.py` — Staging im Sink
- Modify: `tests/test_backup_robustness.py` — Fallback + WARNING
- Modify: `tests/test_tmp_sink_default_on.py` — Gitignore-Eintrag aus `TmpPaths`
- Modify: `tests/test_doctor_runner.py` — Doctor-Finding nutzt Resolver-`reason`
- Modify: `tests/test_opencode_primary_edit_lock.py` — Scope-Ableitung aus dem Sink
- Modify: `tests/test_repo_containment_consistency.py` — `no-hook-support`-WARNING bleibt
- Modify: `tests/test_template_report_paths.py` — Auditor-Guard auf Platzhalter, Atomic-Write-Guard
- Modify: `tests/test_template_slimming_equivalence.py` — Goldens ohne Temp-Literal
- Modify: `tests/test_knowledge_engine.py` — Hinweistext ohne `/tmp`-Literal
- Modify: `tests/test_basetemp_guard.py` — Hinweistext-Assertion ohne Literal
- Modify: `tests/conftest.py` — `_EXTERNAL_BASETEMP_HINT` ohne Literal, Verweis auf `PYTEST_BASETEMP`
- Modify: `tests/fixtures/slimming-golden/tester.md`, `test-executor.md`, `e2e-tester.md`, `documenter.md` — eingefrorene Basetemp-Literale rebased
- Modify: `tests/test_spec_plan_validate_cli.py` — Gate-Test: genau ein `spec_plan_approval_marker`-ERROR
- Modify: `docs/concepts/repo-containment-prison-mode.md` — §5.5 Konfigurationsverweis, Hook-Verhalten; Ownership: Task 17 (Konfigurationsabschnitt), Task 21 (§5.5-Regeltext/AC-41)
- Modify: `templates/configs/project.yaml.example` — `system-temp-exception`-Block im Beispiel; Task 19 ergänzt `toolchain-caches`
- Modify: `templates/configs/agent-meta.config.example.yaml` — Kommentar zum Token `{{PYTEST_BASETEMP}}`
- Modify: `CHANGELOG.md` — Eintrag zur Tmp-Sink-Injektion
- Modify: `docs/plans/2026-10-24-tmp-sink-injection-plan.md` — Ledger-Abschluss (Checkboxen)

---
pipeline_stages:
  implement: 3
---

## DAG

Kanten (jede Kante ist eine harte Vorbedingung; Nummern sind Task-IDs):

```
T1 --> T2 --> T3
T3 --> T4
T3 --> T5
T5 --> T6
T4 --> T7
T5 --> T7
T6 --> T7
T2 --> T8 --> T9
T2 --> T10
T1 --> T11
T2 --> T11
T10 --> T11
T1 --> T12
T2 --> T12
T10 --> T12
T2 --> T13
T2 --> T14
T4 --> T15
T7 --> T15
T9 --> T15
T10 --> T15
T11 --> T15
T12 --> T15
T13 --> T15
T14 --> T15
T3 --> T16
T4 --> T16
T6 --> T16
T7 --> T16
T3 --> T17
T8 --> T17
T9 --> T17
T13 --> T17
T15 --> T18
T16 --> T18
T17 --> T18
T4 --> T22
T14 --> T22
T22 --> T15
T3 --> T19
T17 --> T19
T22 --> T19
T9 --> T20
T17 --> T21
T19 --> T18
T20 --> T18
T21 --> T18
T22 --> T18
```

IDs und Reihenfolge der Tasks 1–18 bleiben stabil; geändert sind nur die `Depends on`-Zeilen von Task 15 (`+22`) und Task 18 (`+19, 20, 21, 22`), 19–22 sind angehängt (Rev. 3). Die Kanten
`T19 --> T18`, `T20 --> T18`, `T21 --> T18` und `T22 --> T18` bedeuten, dass Task 18 trotz kleinerer ID
**zuletzt** läuft: er ist das Abschluss-Gate über alle Tasks und wird von 15, 16, 17 und 19–22 getragen.

Lesbare Form derselben Kanten:

```
P0:  T1 -> T2 -> T3
P1:  T3 -> {T4, T5};  T5 -> T6;  {T4, T5, T6} -> T7
P2:  T2 -> T8 -> T9
P3:  T2 -> T10;  {T1, T2, T10} -> {T11, T12}
P4:  T2 -> T13;  T2 -> T14
P5:  {T4, T7, T9, T10, T11, T12, T13, T14, T22} -> T15
     {T3, T4, T6, T7} -> T16
     {T3, T8, T9, T13} -> T17
P6:  T14 -> T22 -> T15;  {T3, T17, T22} -> T19;  T9 -> T20;  T17 -> T21;
     {T19, T20, T21, T22} -> T18
```

Kritischer Pfad: T1 -> T2 -> T3 -> T5 -> T6 -> T7 -> T15 -> T18.

Der kritische Pfad ist gegenüber Revision 2 **unverändert**: die neuen Kanten hängen Seitenzweige an
(`T4`/`T14` -> `T22`, `T17` -> `T19`/`T21`, `T9` -> `T20`) und verlängern keine der bestehenden Ketten;
`T22` ist über `T4` (nach `T3`) und über `T14` (nach `T2`) erreichbar, beides kürzer als die Kette über
`T5` -> `T6` -> `T7`.

## Parallel-Gruppen

`max-parallel-agents: 4` (`.meta-config/project.yaml:299`). Nach der Validator-Korrektur bleiben zwei Gruppen; keine überschreitet zwei Mitglieder. Alle übrigen Tasks laufen sequenziell in der im DAG genannten Reihenfolge.

Die Rev.-3-Tasks 19–22 bilden **keine dritte Gruppe** und laufen sequenziell: sie teilen Dateien mit
bereits existierenden Tasks (T19/T22 `scripts/lib/consistency/temp_literals.py`, T17/T19
`templates/configs/project.yaml.example`, T17/T21 `docs/concepts/repo-containment-prison-mode.md` plus
`tests/test_docs_tmp_sink_injection.py`, T9/T20 `tests/test_antigravity_hooks_registration.py`) und sind
über `T22 --> T19` zusätzlich direkt verkettet. PG-A `{4,5}` und PG-B `{11,12}` bleiben unverändert.

Kopplungsbegriff: `check_plan_file_overlap` (`scripts/lib/orchestration.py`) bewertet nicht nur harte Datei-Schnittmengen, sondern auch Import-/Doku-Referenzkanten fail-closed. Für beide Gruppen gilt daher: harte Datei-Schnittmenge leer; Kopplung über Import-/Doku-Kanten erkannt und durch Sequenzialisierung aufgelöst (PG-B `{11,12}`, Task 10 davor; Task 13 → 17 sequenziell).

### parallel_group: PG-A — Task 4, Task 5

- Disjunktheit: Task 4 besitzt sieben Bash-Beispiel-Templates (`developer`, `code-reviewer`, `tester`, `validator`, `docker`, `devops-engineer`, `e2e-tester`) plus `tests/test_temp_literals.py` und `.meta-config/temp-literal-allowlist.yaml`. Task 5 besitzt vier Auditor-Templates (`ai-security-guardian`, `app-lifecycle-governor`, `prompt-governor`, `security-auditor`) plus `config/routing/reviewers.yaml` und `tests/test_template_report_paths.py`. Harte Datei-Schnittmenge: leer (Validator `OVERLAP_PG_A {4,5}`: `{"safe": ["task-4","task-5"], "conflict": []}`).
- Warum Task 6 **nicht** in PG-A ist (Korrektur der Vorgabe): Task 5 und Task 6 teilen `tests/test_template_report_paths.py` — AC-02 ersetzt `test_writable_auditor_reports_into_repo_tmp` (`:68-71`) in derselben Datei, in der AC-22 `test_atomic_write_names_tmp_sink` ergänzt. Zwei parallele Schreiber auf eine Testdatei verletzen die Ownership-Barriere, deshalb `Task 6: Depends on 5` und sequenziell.

### parallel_group: PG-B — Task 11, Task 12

- Disjunktheit: Task 11 schreibt `scripts/lib/backup.py`, `scripts/admin-server.py`, `scripts/consistency-check.py`, `scripts/run_role_routing_eval.py`, `.meta-config/temp-env-allowlist.yaml`, `tests/test_tmp_sink_env_coverage.py`, `tests/test_backup_round_trip_804.py`, `tests/test_backup_robustness.py`; Task 12 schreibt `scripts/lib/gitignore.py`, `scripts/lib/doctor_detectors.py`, `tests/test_tmp_sink_default_on.py`, `tests/test_doctor_runner.py`. Harte Datei-Schnittmenge: leer; der Validator belegt für die Zweiergruppe `OVERLAP_PG_B {11,12}`: `{"safe": ["task-11","task-12"], "conflict": []}`.
- Warum Task 10 **nicht** in PG-B ist: die Dreiergruppe `{10,11,12}` wird über Import-Kanten verkoppelt — `scripts/lib/context_report.py` (Task 10) ↔ `scripts/run_role_routing_eval.py` (Task 11) sowie `scripts/lib/context_report.py` ↔ `scripts/lib/doctor_detectors.py` und `tests/test_doctor_runner.py` (Task 12); der Validator meldet dafür zwei ERRORs. Deshalb läuft Task 10 davor und `Task 11`/`Task 12` hängen an `1, 2, 10` (Task 10 hängt an 2, Task 11 zusätzlich an 1). Kanten bleiben vorwärts gerichtet: kein Zyklus.
- Eine Aufnahme in eine Allowlist des Overlap-Checks ist nicht Teil dieses Plans.

### Warum es keine dritte Gruppe gibt (Task 13 → Task 17)

Die frühere Gruppe PG-C `{13,17}` ist aufgelöst; Task 13 und Task 17 laufen sequenziell (`T13 --> T17`, `Task 17: Depends on 3, 8, 9, 13`). Der Validator meldet für `{13,17}` eine Kopplung über die Doku-Referenzkanten `CHANGELOG.md` ↔ `config/provider-tools.yaml` und `docs/concepts/repo-containment-prison-mode.md` ↔ `tests/test_repo_containment_consistency.py`; die harten Dateimengen sind disjunkt, der Kanal bewertet die Referenzkanten jedoch fail-closed. Inhaltlich dokumentiert Task 17 (CHANGELOG, §5.5, Beispiel-Config), was Task 13 in der Provider-Ableitung umsetzt; die Reihenfolge Doku nach Code ist daher ohnehin korrekt. Keine Allowlist-Umgehung.

## Phase P0 — Fundament

### Task 1: Zentraler Tmp-Paths-Resolver

**Agent:** senior-developer
**Depends on:** —
**Files:**
- Create: `scripts/lib/tmp_paths.py`
- Modify: `tests/test_tmp_sink_output_dirs.py`

**Interfaces:** Produces: `resolve_tmp_paths(project_root: Path, config: dict | None) -> TmpPaths`, `TmpPaths(relative: str, absolute: Path | None, enabled: bool, system_temp_exception: SystemTempException, pytest_basetemp: str, env: dict[str, str])`, `SystemTempException(enabled: bool, reason: str, pytest_basetemp: bool, toolchain_cache: bool)`, `tmp_env(paths: TmpPaths, base: dict | None = None) -> dict[str, str]`, `tmp_sink_env_pin_block(paths: TmpPaths) -> str`, `resolve_pytest_basetemp(project_root: Path, paths: TmpPaths) -> str`. Consumes: `repo_containment.tmp_sink_path_error`, `tmp_sink_location_error`, `_resolve_sink_dir`, `work_dir_env`, `resolve_effective_repo_containment`, `TmpSinkError` (`tmp-sink.disabled`, `tmp-sink.invalid-path`, `tmp-sink.system-temp-exception`).

**Rot zuerst:** `tests/test_tmp_sink_output_dirs.py::test_resolver_does_not_raise_when_sink_disabled` scheitert mit `ImportError`/`AttributeError`, weil `lib.tmp_paths` noch fehlt — der Rot-Zustand beweist, dass der Resolver wirklich neu ist.

- [x] Step 1: Tests ergänzen (rot): AC-23 (`enabled=False` ⇒ `relative == ".tmp"`, `absolute is None`, `env == {}`, keine Exception), AC-24 (`resolve_output_dir`, `resolve_work_dir`, `resolve_out_path`, `tmp_env` werfen `tmp-sink.disabled`; `Tool.tmp-sink.disabled`-Präfix geprüft), AC-12 (alle drei Env-Keys `os.path.isabs()`, existieren als Verzeichnis, liegen unter `project_root`), AC-35 (Block setzt `TMPDIR`/`TEMP`/`TMP` auf denselben absoluten Wert, identisch zu `TMP_SINK_ABS_PATH`, relativer Wert erscheint nicht), AC-36 (Block in `posix-sh` mit fehlendem Verzeichnis: Variablen unverändert, stderr nennt `python scripts/sync.py`), AC-16-Teil (`relative` vs. `absolute`), AC-15-Randfall (`gettempdir()` im Projekt ⇒ `TmpSinkError`). Assertions mit `pytest.raises(TmpSinkError)` und `match=r"tmp-sink\."`, Shell-Fälle über `subprocess.run(["sh", "-c", block], capture_output=True, text=True)`.
- [x] Step 2: `scripts/lib/tmp_paths.py` implementieren: Validierung über `tmp_sink_path_error` + `tmp_sink_location_error` auch bei `enabled=False`; `absolute` über `_resolve_sink_dir`; `env` über `work_dir_env(absolute)`; `pytest_basetemp` nach IC-04 (`<absolute>/pytest` bzw. `<tempfile.gettempdir()>/<user>/pytest-agent-meta`), `"` im Wert ⇒ `TmpSinkError`; kein `sys.exit`.
- [x] Step 3: `python3 -m pytest tests/test_tmp_sink_output_dirs.py -q` grün; `python3 scripts/sync.py --validate` ohne neue Findings.
- [x] Step 4: Commit `feat: add central tmp-sink resolver with absolute env pin`.

## Phase P1 — Builder und Templates

### Task 2: Builder-Variablen und Ausnahme-Validierung

**Agent:** senior-developer
**Depends on:** 1
**Files:**
- Modify: `scripts/lib/config.py`
- Modify: `scripts/lib/consistency/placeholders.py`
- Modify: `scripts/lib/sync_pipeline.py`
- Create: `tests/test_tmp_paths_builder.py`
- Modify: `tests/test_repo_containment_validate.py`
- Modify: `tests/test_repo_containment_schema.py`

**Interfaces:** Produces: `_build_orch_variables` setzt `TMP_SINK_ABS_PATH`, `PYTEST_BASETEMP`, `TMP_SINK_ENV_PIN_BLOCK` und ersetzt `{{PYTEST_BASETEMP}}` in `TEST_COMMANDS`/`CODE_QUALITY_RULES`; `_validate_repo_containment` prüft `system-temp-exception`; `_sync_tmp_sink` konsumiert `TmpPaths`. Consumes: `resolve_tmp_paths`, `tmp_sink_env_pin_block` (Task 1), `_fail` (`config.py:496`).

**Rot zuerst:** `tests/test_tmp_paths_builder.py::test_builder_sets_absolute_and_relative_sink` scheitert mit `KeyError: 'TMP_SINK_ABS_PATH'`; `::test_unresolved_pytest_token_fails_sync` scheitert, weil der Sync heute mit unersetztem Token durchläuft.

- [x] Step 1: Tests schreiben (rot): AC-16 (`TMP_SINK_PATH == ".tmp"`, `TMP_SINK_ABS_PATH == <repo>/.tmp`, absolut, kein Symlink-Endsegment), AC-14 (Token bleibt stehen ⇒ Exit 1, Code `tmp-sink.pytest-token`), AC-25 (`enabled: false` ⇒ Sync-`--dry-run` Exit 0, `TMP_SINK_PATH` gesetzt, `TMP_SINK_ABS_PATH`/`TMP_SINK_ENV_PIN_BLOCK` fehlen, `log.skip` enthalten), AC-35 (Block absolut, ein Wert), AC-15 (vier parametrisierte Fälle: kein Mapping, `pytest-basetemp: true` ohne `enabled`, fehlender `reason`, `gettempdir()` im Projekt — je eigene Assertion auf den dokumentierten Fehlertext). Assertions: `capsys`/`subprocess` auf Exit-Code 1, `match=r"tmp-sink\.system-temp-exception"`, `match=r"'pytest-basetemp: true' requires 'enabled: true'"`.
- [x] Step 2: `config.py` erweitern: Variablen nach `:1542` setzen, Token-Ersetzung in beiden Werten, `_fail("tmp-sink.pytest-token", ...)` bei Rest-Token; `_validate_repo_containment` um die vier Fälle. `consistency/placeholders.py:136` um drei Namen ergänzen. `sync_pipeline._sync_tmp_sink` auf `resolve_tmp_paths` umstellen, `log.skip` beibehalten.
- [x] Step 3: `python3 -m pytest tests/test_tmp_paths_builder.py tests/test_repo_containment_validate.py tests/test_repo_containment_schema.py -q` grün.
- [x] Step 4: Commit `feat: build tmp-sink variables and validate temp exception`.

### Task 3: Suite-Kommando literal-frei rendern

**Agent:** developer
**Depends on:** 2
**Files:**
- Modify: `.meta-config/project.yaml`
- Modify: `templates/configs/agent-meta.config.example.yaml`
- Modify: `tests/test_tmp_sink_output_dirs.py`

**Interfaces:** Produces: `TEST_COMMANDS` und `CODE_QUALITY_RULES` als gerenderte Werte mit `--basetemp="<absolut>"`; `system-temp-exception`-Block im Repo-Config. Consumes: Token `{{PYTEST_BASETEMP}}` und Validierung (Task 2).

**Rot zuerst:** `tests/test_tmp_sink_output_dirs.py::test_test_commands_have_no_system_temp_literal` scheitert, weil `project.yaml:194` und `:249` noch `/tmp/$USER/pytest-agent-meta` tragen.

- [x] Step 1: Tests schreiben (rot): AC-13 (`TEST_COMMANDS`/`CODE_QUALITY_RULES` ohne `/tmp`, `%TEMP%`, `C:\Temp`, ohne `$USER`; `--basetemp=` shell-gequotet mit `"`), AC-34 (`tempfile.gettempdir()` per Monkeypatch mit Leerzeichen ⇒ `shlex.split` liefert genau ein `--basetemp`-Argument). Assertions: `assert "/tmp" not in rendered`, `assert "--basetemp=\"" in rendered`, `assert len([a for a in shlex.split(cmd) if a.startswith("--basetemp=")]) == 1`.
- [x] Step 2: `.meta-config/project.yaml:194` und `:249` auf `{{PYTEST_BASETEMP}}` umstellen und den Block `system-temp-exception: {enabled: true, reason: "pytest basetemp must stay outside the repo (ancestor collision, 13 failures 2026-09-20)", pytest-basetemp: true, toolchain-caches: false}` explizit nach `:402` aufnehmen; im Beispiel `templates/configs/agent-meta.config.example.yaml` (nahe `:158`/`:168`) das Token als Kommentar dokumentieren (der Beispielwert selbst bleibt projektspezifisch).
- [x] Step 3: `python3 -m pytest tests/test_tmp_sink_output_dirs.py -q` und `python3 scripts/sync.py --dry-run` grün, danach `python3 scripts/sync.py --validate`.
- [x] Step 4: Commit `refactor: replace basetemp literal with pytest token`.

### Task 4: Achtzehn System-Temp-Literale in sieben Templates ersetzen

**Agent:** developer
**Depends on:** 3
**Files:**
- Create: `tests/test_temp_literals.py`
- Create: `.meta-config/temp-literal-allowlist.yaml`
- Modify: `agents/1-generic/developer.md`
- Modify: `agents/1-generic/code-reviewer.md`
- Modify: `agents/1-generic/tester.md`
- Modify: `agents/1-generic/validator.md`
- Modify: `agents/1-generic/docker.md`
- Modify: `agents/1-generic/devops-engineer.md`
- Modify: `agents/1-generic/e2e-tester.md`

**Interfaces:** Produces: Guard `test_no_system_temp_literal_in_agents` mit dem exakten AC-01-Muster `(^|[^A-Za-z0-9_.-])(/tmp/|%TEMP%|[A-Za-z]:\\\\Temp\\\\)`; Allowlist-Datei mit `entries: []`. Consumes: Platzhalter `{{TMP_SINK_PATH}}` (`config.py:1542`, `placeholders.py:136`).

**Rot zuerst:** `tests/test_temp_literals.py::test_no_system_temp_literal_in_agents` listet 18 Treffer in sieben Dateien (`developer.md:47,50,154,163`; `code-reviewer.md:221,229`; `tester.md:71,74,141,143`; `validator.md:76,79`; `docker.md:128,130`; `devops-engineer.md:202,204`; `e2e-tester.md:154,156`) und schlägt fehl.

- [x] Step 1: Guard-Test schreiben (rot), Muster wörtlich aus AC-01, Treffer mit Datei und Zeile als Assertion-Meldung; Allowlist-Datei mit Kopfkommentar und leerer `entries`-Liste anlegen.
- [x] Step 2: Alle 18 Literale auf `{{TMP_SINK_PATH}}/…` umstellen, Pfadform beibehalten: `docker logs "$NAME" > {{TMP_SINK_PATH}}/"$NAME".log 2>&1`, `tee {{TMP_SINK_PATH}}/run-$RANDOM.log`, `npm run e2e > {{TMP_SINK_PATH}}/e2e.log 2>&1 &`, `tail -50 {{TMP_SINK_PATH}}/e2e.log`, analog `lint.log`.
- [x] Step 3: `python3 -m pytest tests/test_temp_literals.py -q` grün; `python3 scripts/sync.py --validate` ohne `temp-literal.system-temp` für `agents/**`.
- [x] Step 4: Commit `refactor: inject tmp sink into generic bash examples`.

### Task 5: Vier Sink-Literale in Auditor-Templates

**Agent:** developer
**Depends on:** 3
**Files:**
- Modify: `agents/1-generic/ai-security-guardian.md`
- Modify: `agents/1-generic/app-lifecycle-governor.md`
- Modify: `agents/1-generic/prompt-governor.md`
- Modify: `agents/1-generic/security-auditor.md`
- Modify: `config/routing/reviewers.yaml`
- Modify: `tests/test_template_report_paths.py`

**Interfaces:** Produces: Auditor-Report-Ziel als `{{TMP_SINK_PATH}}/<role>-<topic>.md`; `test_writable_auditor_reports_into_configured_sink` ersetzt `test_writable_auditor_reports_into_repo_tmp` (`:68-71`). Consumes: `WRITABLE_AUDITORS`-Liste im selben Testmodul; ADR-10 (kein Renderer für `reviewers.yaml`).

**Rot zuerst:** der neue Test `test_writable_auditor_reports_into_configured_sink` schlägt fehl, weil die vier Templates `\.tmp/` fest schreiben (`ai-security-guardian.md:111`, `app-lifecycle-governor.md:100`, `prompt-governor.md:120`, `security-auditor.md:217`).

- [x] Step 1: Test umschreiben (rot): Assertion `assert "{{TMP_SINK_PATH}}/" in text` und `assert not re.search(r"`\.tmp/[a-z0-9-]+-<topic>\.md`", text)`; Testname und Docstring nennen AC-02.
- [x] Step 2: Vier Templates auf den Platzhalter umstellen; `config/routing/reviewers.yaml:28` auf einen generischen Satz ohne `.tmp/` ändern (Test-Fixture, kein Injektionspunkt, nur damit der neue Check in `config/**` nicht anschlägt).
- [x] Step 3: `python3 -m pytest tests/test_template_report_paths.py -q` grün.
- [x] Step 4: Commit `refactor: route auditor reports through tmp sink placeholder`.

### Task 6: Vage Temp-Anweisungen präzisieren

**Agent:** developer
**Depends on:** 5
**Files:**
- Modify: `agents/1-generic/se-validator.md`
- Modify: `agents/1-generic/se-developer.md`
- Modify: `agents/1-generic/se-verifier.md`
- Modify: `agents/1-generic/se-integration-and-test-manager.md`
- Modify: `agents/1-generic/se-interface-mgr.md`
- Modify: `agents/1-generic/se-junior-developer.md`
- Modify: `agents/1-generic/se-termination.md`
- Modify: `agents/1-generic/se-requirements.md`
- Modify: `agents/1-generic/se-critic.md`
- Modify: `agents/1-generic/se-architect.md`
- Modify: `agents/1-generic/se-senior-developer.md`
- Modify: `agents/1-generic/se-component-requirements.md`
- Modify: `agents/1-generic/test-executor.md`
- Modify: `rules/1-generic/plan-ledger.md`
- Modify: `tests/test_template_report_paths.py`

**Interfaces:** Produces: `test_atomic_write_names_tmp_sink` (AC-22); jede der 13 Rollen nennt `{{TMP_SINK_PATH}}` als Schreibort des Zwischenartefakts. Consumes: Platzhalter-Vertrag (Task 4/5), `rules/1-generic/plan-ledger.md:67` Inventar 13.

**Rot zuerst:** `test_atomic_write_names_tmp_sink` schlägt fehl, weil die 13 Rollen (12 SE-Rollen + `test-executor`) heute „to a temporary file" bzw. „temp → rename" ohne Ort sagen (`se-validator.md:192-193` u. a.) und `plan-ledger.md:67` `.tmp/` literal nennt.

- [x] Step 1: Test schreiben (rot), parametrisiert über die 13 Rollen: `assert "{{TMP_SINK_PATH}}" in text`; zusätzlich Negativ-Assertion `assert not re.search(r"to a temporary file|temp \u2192 rename", text)` für die betroffenen Absätze.
- [x] Step 2: Wortlaut vereinheitlichen, z. B. „Write the full output to `{{TMP_SINK_PATH}}/<role>-<topic>.json`, then rename to the target path (atomic write)"; `test-executor.md:30,87` auf „under `{{TMP_SINK_PATH}}/runs/`"; `plan-ledger.md:67` auf „im konfigurierten Scratch-Sink (`{{TMP_SINK_PATH}}/`)".
- [x] Step 3: `python3 -m pytest tests/test_template_report_paths.py -q` grün.
- [x] Step 4: Commit `refactor: name the configured sink in scratch instructions`.

### Task 7: Standalone-Export regenerieren

**Agent:** developer
**Depends on:** 4, 5, 6
**Files:**
- Modify: `scripts/lib/standalone.py`
- Modify: `standalone/agents/`
- Create: `tests/test_standalone_render.py`
- Modify: `tests/test_temp_literals.py`

**Interfaces:** Produces: `_standalone_variables` setzt `TMP_SINK_PATH = ".tmp"` und `TMP_SINK_ENV_PIN_BLOCK = ""`; `test_tmp_sink_path_uses_framework_default` (AC-27) und `test_no_system_temp_literal_in_standalone` (AC-26). Consumes: Template-Korrekturen aus Task 4/5/6, `render_standalone_agent` (`standalone.py:289-337`), Drift-Gate `sync.py --render-standalone --check` (`cli_commands.py:496-508`).

Der `standalone/agents/`-Eintrag ist Verzeichnis-Ownership: `--render-standalone` schreibt alle betroffenen Rollen aus einer Quelle neu (namentlich mindestens `meta-doctor.md`, `meta-optimizer.md`, `agent-meta-manager.md`, die elf Literal-Rollen und die dreizehn Rollen aus Task 6); der Render-Diff ist die Prüfgrundlage.

**Rot zuerst:** `test_tmp_sink_path_uses_framework_default` schlägt fehl, weil `standalone/agents/meta-doctor.md` die Notiz `[TMP_SINK_PATH — not available outside a full agent-meta install]` trägt (12 Vorkommen in drei Dateien); `test_no_system_temp_literal_in_standalone` listet 18 `/tmp`- und 4 `.tmp/`-Treffer.

- [x] Step 1: Beide Tests schreiben (rot); Assertions: kein Vorkommen von `not available outside a full agent-meta install` in `standalone/**`, `.tmp/` in `meta-doctor.md`, `meta-optimizer.md`, `agent-meta-manager.md` vorhanden, kein AC-01-Muster in `standalone/**`.
- [x] Step 2: `_standalone_variables` um beide Keys erweitern; `python scripts/sync.py --render-standalone` ausführen und den Diff gegen die erwarteten Rollen prüfen.
- [x] Step 3: `python3 -m pytest tests/test_standalone_render.py tests/test_temp_literals.py -q` grün; `python3 scripts/sync.py --render-standalone --check` Exit 0.
- [x] Step 4: Commit `chore: regenerate standalone agents from tmp-sink templates`.

## Phase P2 — Hook fail-closed

### Task 8: Hook-Anker und fail-closed Root-Auflösung

**Agent:** senior-developer
**Depends on:** 2
**Files:**
- Modify: `hooks/1-generic/repo-containment-impl.sh`
- Modify: `hooks/1-generic/repo-containment.sh`
- Modify: `tests/test_repo_containment_hook.py`

**Interfaces:** Produces: Anker-Regel (`cwd` nicht leer ⇒ realpath; sonst absolutes Ziel ⇒ `realpath(dirname(ziel))`; sonst Exit 2 `repo-containment.no-root`), `resolve_repo_root(dir)` ohne `$PWD`-Fallback, Meldungen mit absolutem Root und Sink, Shared-Contract-Parität Hook-Sink ↔ `TmpPaths.relative`. Consumes: `IC-07`/`IC-08`, `tmp_sink_path_error`-Spiegel im Inline-Python (`repo-containment-impl.sh:186-301`).

**Rot zuerst:** `test_cwd_outside_project_cannot_be_adopted` (`cwd=/tmp`, Ziel `/tmp/x.py`, kein `.meta-config/` oberhalb) schlägt fehl: der Hook adelt `$PWD` (`:151-154`, `:175-180`) und liefert Exit 0 statt 2.

- [x] Step 1: Tests schreiben (rot): AC-05 (Exit 2, `repo-containment.no-root`), AC-33 (relatives `../../x` bei `cwd=<fixture>/a/b` ⇒ Exit 0; `../../../../etc/passwd` ⇒ Exit 2), Paritätstest `test_hook_sink_matches_tmp_paths` (Hook-stderr-Sink == `str(resolve_tmp_paths(...).absolute)`), Fixture-Helfer `_external_fixture()` mit `tempfile.mkdtemp(dir=tempfile.gettempdir())` und Assertion „kein `.meta-config/` im Ancestor-Pfad".
- [x] Step 2: `repo-containment-impl.sh` umbauen: `WORKDIR` nur aus nicht-leerem `cwd`, sonst Anker aus absolutem Ziel, sonst Block; `resolve_repo_root` ohne Fallback; Meldungstexte nach Spec-Vertrag mit `target`, `anchor`, `repair`, `opt-out`; Sink in der Block-Meldung absolut (`allowed: paths under <abs root> and under <abs sink>`). `repo-containment.sh` nur anfassen, wenn dort eine Versions-/Hash-Bindung an die Impl steht.
- [x] Step 3: `python3 -m pytest tests/test_repo_containment_hook.py -q` grün (die bewusste Inversion folgt in Task 9).
- [x] Step 4: Commit `fix: fail closed in repo containment hook without project root`.

### Task 9: Hook-Testmatrix und bewusste Inversion

**Agent:** developer
**Depends on:** 8
**Files:**
- Modify: `tests/test_repo_containment_hook.py`
- Modify: `tests/test_antigravity_hooks_registration.py`

**Interfaces:** Produces: vollständige AC-03/04/06/07/08/18/28/29/30/37-Abdeckung; `test_missing_config_fails_closed` ersetzt `test_missing_config_defaults_to_containment_on` (`:213-218`). Consumes: Anker-Regel und Meldungen (Task 8), Adapter-Verhalten (`antigravity-json-adapter.sh:122-127,167-168`).

**Rot zuerst:** `test_relative_target_without_cwd_fails_closed` (AC-04) und `test_empty_cwd_anchors_on_absolute_target` (AC-28) schlagen fehl, weil `cwd=""` heute wie „fehlt" behandelt wird und `$PWD` als Basis nimmt.

- [x] Step 1: Tests schreiben/umbauen (rot): AC-03 (`test_missing_config_fails_closed`, Fixture ohne `.meta-config/`, Ziel **innerhalb** der Fixture ⇒ Exit 2 mit Code — die bewusste Inversion der alten Erwartung), AC-04 (relatives Ziel ohne `cwd` ⇒ Exit 2, stderr nennt „relative target without `cwd`"), AC-06 (`cwd=<fixture>/.tmp/sub`, `notes.md` ⇒ Exit 0), AC-07 (Symlink-`cwd` ⇒ Exit 2, stderr nennt realpath), AC-08 (bestehender Outside-Write-Test bleibt), AC-18 (`test_block_message_uses_absolute_sink`), AC-28 (`cwd=""`, absolutes Ziel im Root ⇒ Exit 0), AC-29 (`cwd=""`, Ziel im System-Temp ⇒ Exit 2), AC-33 (aus Task 8 gehalten), AC-37 (`cwd=""`, fremdes Projekt mit `.meta-config/` ⇒ Exit 0, dokumentierte Annahme), AC-30 (`test_adapter_temp_file_is_cleaned_up`: keine neue Datei im Repo-Baum, `mktemp`-Datei nach Prozessende weg, Deny-Vertrag unverändert).
- [x] Step 2: Testdatei konsolidieren: gemeinsamer `_write_payload()`-/`_external_fixture()`-Helfer, Docstrings mit AC-ID; alte Erwartung als Kommentar „bewusst invertiert (Fail-open-Fall cwd=/tmp, Ziel /tmp/x)" dokumentieren.
- [x] Step 3: `python3 -m pytest tests/test_repo_containment_hook.py tests/test_antigravity_hooks_registration.py -q` grün.
- [x] Step 4: Commit `test: cover hook anchor rule and invert fail-open test`.

## Phase P3 — Env-Pin, Backup, Zweitparser

### Task 10: Env-Pin für Framework-Subprozesse ausweiten

**Agent:** senior-developer
**Depends on:** 2
**Files:**
- Modify: `scripts/lib/repo_containment.py`
- Modify: `scripts/lib/context_report.py`
- Modify: `scripts/lib/meta_optimizer.py`
- Modify: `tests/test_tmp_sink_output_dirs.py`

**Interfaces:** Produces: `context_report.py:340` und `meta_optimizer.py:1508` rufen `tmp_env(paths)` statt `work_dir_env(work_dir)`; `work_dir_env` ist nur noch über `tmp_env` erreichbar. Consumes: `tmp_env` (Task 1), `TmpPaths` (Task 2).

**Rot zuerst:** `test_context_report_passes_absolute_tmp_env` schlägt fehl, weil der Subprozess heute nur `work_dir_env(work_dir)` erhält und der Aufruf `tmp_env` nicht kennt.

- [x] Step 1: Tests schreiben (rot): drei Env-Keys absolut und identisch zu `TmpPaths.env`; `tmp_env` bei `enabled=False` wirft `tmp-sink.disabled`; Aufrufpfad-Assertion (`ast`-Scan: `work_dir_env` wird in `scripts/**` nur aus `tmp_paths.py` aufgerufen).
- [x] Step 2: Beide Aufrufstellen umstellen, `work_dir_env`-Docstring auf „nur über `tmp_env`" präzisieren (Verhalten unverändert).
- [x] Step 3: `python3 -m pytest tests/test_tmp_sink_output_dirs.py -q` grün.
- [x] Step 4: Commit `refactor: pin tmp env for framework subprocesses`. *(offen: Commit gehört dem `git`-Agenten; dieser Subagent hatte keinen Commit-Auftrag — siehe `…-status.md`, Evidence Task 10)*

### Task 11: Subprozess-Klassifikation und Backup-Staging

**Agent:** developer
**Depends on:** 1, 2, 10
**Files:**
- Modify: `scripts/lib/backup.py`
- Modify: `scripts/admin-server.py`
- Modify: `scripts/consistency-check.py`
- Modify: `scripts/run_role_routing_eval.py`
- Create: `.meta-config/temp-env-allowlist.yaml`
- Create: `tests/test_tmp_sink_env_coverage.py`
- Modify: `tests/test_backup_round_trip_804.py`
- Modify: `tests/test_backup_robustness.py`

**Interfaces:** Produces: `create_backup` nutzt `TemporaryDirectory(dir=<absolute>/backup-staging)` über `resolve_output_dir`, Fallback nur bei `tmp-sink.disabled` mit WARNING `backup.staging-system-temp`, sonst Abbruch `backup.tmp-sink.invalid-path`; `test_subprocess_calls_pin_temp_env` prüft `scripts/**` (47 `subprocess`-Treffer, davon 12 in `scripts/*.py`). Consumes: `tmp_env`, `resolve_output_dir` (Task 1), Allowlist-Schema `{path, symbol, reason}`.

**Rot zuerst:** `test_staging_dir_is_inside_tmp_sink` schlägt fehl, weil `backup.py:340` `TemporaryDirectory()` ohne `dir=` im System-Temp anlegt; `test_subprocess_calls_pin_temp_env` listet die 12 ungeschützten Aufrufe in `scripts/*.py` (`admin-server.py:609,618,644,1243,1625,5799,5805,5830`, `consistency-check.py:79,83,98`, `run_role_routing_eval.py:727`).

- [x] Step 1: Tests schreiben (rot): AC-09 (Staging unter `<repo>/.tmp/`, `tempfile.gettempdir()` nicht Basis), AC-10 (`enabled: false` ⇒ System-Temp **mit** WARNING, Backup erfolgreich), AC-11 (AST-Scan über `scripts/**`, Kriterium „kein `git`-Plumbing, kein reiner Lese-Befehl, keine nachweislich temp-freie Ausführung"; jeder Ausreißer braucht einen Allowlist-Eintrag).
- [x] Step 2: `backup.py` umbauen; die zwölf Aufrufe klassifizieren: `env=tmp_env(...)` setzen oder mit `{path, symbol, reason}` in `.meta-config/temp-env-allowlist.yaml` begründen (z. B. reine `git diff`/`ls-files`-Aufrufe).
- [x] Step 3: `python3 -m pytest tests/test_tmp_sink_env_coverage.py tests/test_backup_round_trip_804.py tests/test_backup_robustness.py -q` grün.
- [x] Step 4: Commit `refactor: stage backups inside the tmp sink`. *(offen: Commit gehört dem `git`-Agenten; dieser Subagent hatte keinen Commit-Auftrag — siehe `…-status.md`, Evidence Task 11)*

### Task 12: Gitignore- und Doctor-Zweitparser entfernen

**Agent:** developer
**Depends on:** 1, 2, 10
**Files:**
- Modify: `scripts/lib/gitignore.py`
- Modify: `scripts/lib/doctor_detectors.py`
- Modify: `tests/test_tmp_sink_default_on.py`
- Modify: `tests/test_doctor_runner.py`

**Interfaces:** Produces: `_tmp_sink_gitignore_entry(paths: TmpPaths) -> str | None`; `_sink_hits` nutzt `TmpPaths` und übernimmt den `reason` des Resolvers. Consumes: `resolve_tmp_paths` (Task 1/2), `CHECK_TMP_SINK` (`doctor_detectors.py:44,414`).

**Rot zuerst:** `test_tmp_sink_entry_uses_resolved_path` schlägt fehl, weil `_tmp_sink_gitignore_entry` noch `resolve_effective_repo_containment` selbst aufruft (`gitignore.py:317-339`); `test_tmp_sink_check_uses_resolver_reason` schlägt fehl, weil `_sink_hits` (`:403-411`) die Config erneut parst.

- [x] Step 1: Tests schreiben (rot): AC-31 (`scratch/out` ⇒ Eintrag `scratch/out/`; `enabled: false` ⇒ kein Eintrag), AC-32 (`path: ../out` ⇒ Finding `CHECK_TMP_SINK` mit `reason == "must not contain '..' segments"`), plus AST-Assertion: in `gitignore.py` und `doctor_detectors.py` kommt kein `resolve_effective_repo_containment` und kein `get_path(...tmp-sink.path...)` mehr vor.
- [x] Step 2: Beide Stellen auf `TmpPaths` umstellen, Doctor-Meldung (`Finding`, Schwere `ERROR`) beibehalten.
- [x] Step 3: `python3 -m pytest tests/test_tmp_sink_default_on.py tests/test_doctor_runner.py -q` grün.
- [x] Step 4: Commit `refactor: derive gitignore and doctor sink from resolver` — offen: kein Commit-Auftrag für diesen Subagenten (Konvention wie Tasks 1–11; Status führt `— (pending)`).

## Phase P4 — Provider-Agnostik und Consistency

### Task 13: Opencode-Schreibscope aus dem Sink ableiten

**Agent:** senior-developer
**Depends on:** 2
**Files:**
- Modify: `config/provider-tools.yaml`
- Modify: `scripts/lib/provider_transform.py`
- Modify: `tests/test_opencode_primary_edit_lock.py`
- Modify: `tests/test_repo_containment_consistency.py`

**Interfaces:** Produces: `_transform_frontmatter_for_opencode(..., edit_allow_paths=...)` erhält die Liste aus `TmpPaths.relative`; statische Liste in `config/provider-tools.yaml` nur noch `.meta-viz/**`; leere Ableitung ⇒ `edit: deny`. Consumes: `TmpPaths` (Task 2), `provider_transform.py:477-484,985-998`, `has_hooks: false` (`config/ai-providers.yaml:252`).

**Rot zuerst:** `test_edit_allow_derived_from_tmp_sink` schlägt fehl: bei `path: scratch/out` erzeugt der Transform noch `.tmp/**` aus der statischen Liste (`config/provider-tools.yaml:64-66`).

- [x] Step 1: Tests schreiben (rot): AC-17 (`permission.edit == {"*": "deny", "scratch/out/**": "allow", ".meta-viz/**": "allow"}`, kein `.tmp/**`), AC-20 (`repo-containment.no-hook-support` bleibt WARNING, Exit 0).
- [x] Step 2: Ableitung implementieren (Capability-getrieben, kein Provider-Name); statische Liste auf `.meta-viz/**` reduzieren; Fallback ohne Config-Kontext bleibt `edit: deny` bzw. nur `.meta-viz/**`.
- [x] Step 3: `python3 -m pytest tests/test_opencode_primary_edit_lock.py tests/test_repo_containment_consistency.py -q` grün.
- [x] Step 4: Commit `refactor: derive opencode edit scope from tmp sink`. — offen: kein Commit-Auftrag für diesen Subagenten.

### Task 14: Consistency-Check für Temp-Literale

**Agent:** developer
**Depends on:** 2
**Files:**
- Create: `scripts/lib/consistency/temp_literals.py`
- Modify: `scripts/consistency-check.py`
- Modify: `scripts/lib/cli_commands.py`
- Create: `tests/test_consistency_temp_literals.py`

**Interfaces:** Produces: `check_temp_literals(agent_meta_root: Path, project_root: Path, config: dict | None) -> list[Finding]` mit `SYSTEM_TEMP_LITERAL_RE`, Scope `agents/**`, `standalone/**`, `rules/1-generic/**`, `config/**`, `tests/fixtures/slimming-golden/**`, `tests/conftest.py`; Codes `temp-literal.system-temp`, `temp-literal.sink-relative`, `temp-literal.subprocess-env`, `temp-literal.toolchain-cache-in-repo`, `temp-literal.provider-advisory`. Consumes: `.meta-config/temp-literal-allowlist.yaml` (Task 4), `_strict_findings`-Block (`cli_commands.py:1411-1426`).

Modulname korrigiert gegen die Vorgabe: die Spec nennt `scripts/lib/consistency/temp_literals.py` (IC-11). Ein zweiter Modulname (`tmp_sink_injection.py`) würde eine Parallelimplementierung anlegen; der Testname bleibt `tests/test_consistency_temp_literals.py` (AC-21).

**Rot zuerst:** `test_warning_and_allowlist` scheitert mit `ImportError`, weil `lib.consistency.temp_literals` fehlt.

- [x] Step 1: Tests schreiben (rot): AC-21 (Template mit `/tmp/x` ⇒ WARNING `temp-literal.system-temp` mit Datei und Zeile, Exit 0; Allowlist-Eintrag `{path, pattern, reason}` ⇒ keine Meldung), Scope-Test (jede der sechs Wurzeln wird geprüft), Fixture-Vollständigkeits-Check (der Fixture-Eintrag enthält `path`, `pattern` und `reason`). Schema-Erzwingung (fehlendes `reason`, `expires`) ist Task 22 (AC-39).
- [x] Step 2: Modul implementieren, in `scripts/consistency-check.py` und im `_strict_findings`-Block registrieren (WARNING, kein Exit).
- [x] Step 3: `python3 -m pytest tests/test_consistency_temp_literals.py -q` grün; `python3 scripts/sync.py --validate` zeigt keine neuen ERROR.
- [x] Step 4: Commit `feat: warn on system temp literals in shipped text` — offen: der Auftrag für Task 14 lautet ausdrücklich „do not commit/push"; Commit-Authority bleibt beim `git`-Agenten.

## Phase P5 — Guards, Goldens, Doku

### Task 15: Aggregations-Guard über alle Schreibpfade

**Agent:** developer
**Depends on:** 4, 7, 9, 10, 11, 12, 13, 14, 22
**Files:**
- Create: `tests/test_tmp_sink_injection.py`
- Modify: `tests/test_temp_literals.py`

**Interfaces:** Produces: vier Guard-Klassen in einer Datei (siehe Abschnitt „Guard-Tests") plus den Einzelquellen-Nachweis `test_temp_literal_pattern_has_single_source_of_truth`; `test_temp_literals.py` importiert das Muster aus `lib.consistency.temp_literals` statt es zu duplizieren. Consumes: `check_temp_literals` (Task 14), das gehärtete Allowlist-Schema `{path, pattern, reason}`/`owner` ohne `expires` (Task 22, AC-39), Hook-Verhalten (Task 8/9), `backup.py`-Stand (Task 11), Env-Pin-Abdeckung (Task 10/11).

**Rot zuerst:** `tests/test_tmp_sink_injection.py::test_temp_literal_pattern_has_single_source_of_truth` scheitert reproduzierbar: die Assertion `assert definitions == ["scripts/lib/consistency/temp_literals.py"]` liefert als Ist-Wert `["scripts/lib/consistency/temp_literals.py", "tests/test_temp_literals.py"]`, weil `tests/test_temp_literals.py` das AC-01-Muster bis Step 2 selbst deklariert (`SYSTEM_TEMP_LITERAL_RE = re.compile(r"(^|[^A-Za-z0-9_.-])(/tmp/|%TEMP%|[A-Za-z]:\\\\Temp\\\\)")`). Die Template- und `backup.py`-Hälften der Aggregation sind zu diesem Zeitpunkt bereits grün, weil Tasks 4, 7 und 11 Vorbedingung dieses Tasks sind; der Rot-Beleg kommt aus der noch fehlenden gemeinsamen Musterquelle. Eine „temporär zurückgedrehte lokale Kopie" ist kein zulässiger Rot-Beleg und entfällt.

- [x] Step 1: `tests/test_tmp_sink_injection.py` schreiben, der Lauf ist rot (Beleg oben): (a) kein AC-01-Muster in `agents/**` außer Allowlist, (b) Hook mit `cwd` außerhalb jedes Projekts ⇒ Exit 2 (Subprozess, Fixture extern), (c) `backup.py` ohne `TemporaryDirectory()`-Aufruf ohne `dir=` und ohne `gettempdir()` als Staging-Basis (AST-Scan), (d) jeder `subprocess`-Aufruf in `scripts/**` mit `env=` oder Allowlist-Eintrag (AST-Scan), (e) genau eine Definition des Musters im Repo (`scripts/lib/consistency/temp_literals.py`), Assertion `definitions == ["scripts/lib/consistency/temp_literals.py"]` mit Ist-Wert in der Meldung.
- [x] Step 2: `tests/test_temp_literals.py` auf `from lib.consistency.temp_literals import SYSTEM_TEMP_LITERAL_RE` umstellen und die Gleichheit zur AC-01-Musterdefinition assertieren.
- [x] Step 3: `python3 -m pytest tests/test_tmp_sink_injection.py tests/test_temp_literals.py -q` grün.
- [x] Step 4: Commit `test: guard tmp-sink injection across all write paths`. — Offen: dieser Subagent hat keinen Commit-/Push-Auftrag; Nachweis in `…-status.md` „Evidence — Task 15".

### Task 16: Goldens rebaselinen

**Agent:** developer
**Depends on:** 3, 4, 6, 7
**Files:**
- Modify: `tests/test_template_slimming_equivalence.py`
- Modify: `tests/test_knowledge_engine.py`
- Modify: `tests/conftest.py`
- Modify: `tests/test_basetemp_guard.py`
- Modify: `tests/fixtures/slimming-golden/tester.md`
- Modify: `tests/fixtures/slimming-golden/test-executor.md`
- Modify: `tests/fixtures/slimming-golden/e2e-tester.md`
- Modify: `tests/fixtures/slimming-golden/documenter.md`

**Interfaces:** Produces: Goldens ohne `/tmp`-Literal für `OG-TAIL-DOCKER` (`:890`), `OG-TAIL-DEV` (`:931`), `OG-PASS-CODE-REVIEWER` (`:1023`); `_EXTERNAL_BASETEMP_HINT` ohne Literal. Consumes: gerenderte `TEST_COMMANDS` (Task 3), Template-Texte (Task 4/6), Standalone-Regeneration (Task 7).

**Rot zuerst:** Step 1 ist ein echter fehlschlagender Lauf der bestehenden Tests: `python3 -m pytest tests/test_template_slimming_equivalence.py tests/test_basetemp_guard.py tests/test_knowledge_engine.py -q` schlägt nach Task 3/4/6/7 fehl. Konkret: `test_template_slimming_equivalence.py` vergleicht die Goldens byte-genau gegen den gerenderten Text und findet in `tests/fixtures/slimming-golden/tester.md:51` (`--basetemp=/tmp/$USER/pytest-agent-meta`) den neuen Wert `--basetemp="<absolut>/pytest"`; ebenso für `OG-TAIL-DEV`, `OG-TAIL-DOCKER` und `OG-PASS-CODE-REVIEWER` in `test-executor.md:33,41`, `e2e-tester.md:73`, `documenter.md:68`. `tests/test_basetemp_guard.py` schlägt fehl, weil der erwartete Hinweistext das Literal `/tmp` enthält, `tests/test_knowledge_engine.py:81` aus demselben Grund.

- [x] Step 1: Rot-Lauf ausführen und Fehlschläge protokollieren (je Fehlschlag: Testname, Assertion, erwarteter Golden-Wert, tatsächlich gerenderter Wert). Kein Test wird vor diesem Lauf angepasst.
- [x] Step 2: Golden-Diff bewusst prüfen: nur die erwarteten Zeilen (`docker logs`, `tee`, `tail`, `npm run …`, `--basetemp=`) dürfen sich ändern; jede andere Abweichung ist ein Befund und blockiert den Schritt.
- [x] Step 3: `tests/fixtures/slimming-golden/{tester,test-executor,e2e-tester,documenter}.md` auf den gerenderten `TEST_COMMANDS`-Wert aktualisieren; `tests/conftest.py:28` auf einen Verweis ohne Literal umstellen; `tests/test_basetemp_guard.py` und `tests/test_knowledge_engine.py` auf denselben Verweis.
- [x] Step 4: `python3 -m pytest tests/test_template_slimming_equivalence.py tests/test_basetemp_guard.py tests/test_knowledge_engine.py -q` grün.
- [x] Step 5: Commit `test: rebaseline slimming goldens without temp literals`. — Offen: der Auftrag untersagt Commit/Push für diesen Subagenten-Lauf; Nachweis in `…-status.md` „Evidence — Task 16".

### Task 17: Doku und Beispiel-Config

**Agent:** developer
**Depends on:** 3, 8, 9, 13
**Files:**
- Modify: `docs/concepts/repo-containment-prison-mode.md`
- Modify: `templates/configs/project.yaml.example`
- Modify: `CHANGELOG.md`
- Create: `tests/test_docs_tmp_sink_injection.py`

**Interfaces:** Produces: §5.5-Absatz „Konfiguration" mit Verweis auf `system-temp-exception`/`PYTEST_BASETEMP`; Beispiel-Block in `project.yaml.example`; CHANGELOG-Eintrag. Consumes: Config-Keys (Task 3), Hook-Verhalten (Task 8/9).

Pfad korrigiert gegen die Vorgabe: der Repo-Containment-Beispielblock liegt in `templates/configs/project.yaml.example:166-172`; `templates/configs/agent-meta.config.example.yaml` trägt nur `variables` und ist in Task 3 bereits für den Token-Kommentar vorgesehen. Q11 ist mit Revision 3 entschieden (ADR-16, AC-41): den Verweis im Regeltext selbst setzt Task 21; Task 17 ergänzt den Konfigurationsabschnitt und lässt die Pflichtregel wörtlich stehen.

**Rot zuerst:** `test_prison_mode_documents_temp_exception` schlägt fehl, weil §5.5 (`:404-439`) den Config-Key und den Token nicht nennt.

- [x] Step 1: Test schreiben (rot): §5.5 enthält `system-temp-exception` und `PYTEST_BASETEMP`; `templates/configs/project.yaml.example` enthält `system-temp-exception:` mit `reason`; `CHANGELOG.md` enthält einen Eintrag mit `tmp-sink` und `PYTEST_BASETEMP`.
- [x] Step 2: Doku und Beispiel ergänzen; CHANGELOG-Eintrag unter „Unreleased" mit Verweis auf `SPEC-tmp-sink-injection`.
- [x] Step 3: `python3 -m pytest tests/test_docs_tmp_sink_injection.py -q` grün.
- [x] Step 4: Commit `docs: document tmp-sink injection and env pin`. — Offen: der Auftrag untersagt Commit/Push für diesen Subagenten-Lauf; Nachweis in `…-status.md` „Evidence — Task 17".

**Phase P6 (Rev. 3) — Tasks 19–22, sequenziell.** Die vier Tasks setzen die Nutzerentscheidungen
Q3/Q6/Q10/Q11 um; sie liegen in P5, weil sie Guards, Goldens/Doku und den Adapter berühren, laufen aber
vollständig vor dem Abschluss-Gate Task 18.

### Task 19: Toolchain-Cache-Opt-in (Q3)

**Agent:** developer
**Depends on:** 3, 17, 22
**Files:**
- Modify: `scripts/lib/tmp_paths.py`
- Modify: `scripts/lib/config.py`
- Modify: `scripts/lib/consistency/temp_literals.py`
- Modify: `.meta-config/project.yaml`
- Modify: `templates/configs/project.yaml.example`
- Modify: `tests/test_tmp_paths_builder.py`
- Modify: `tests/test_tmp_sink_output_dirs.py`
- Modify: `tests/test_repo_containment_validate.py`

**Interfaces:** Produces: `tmp_sink_env_pin_block(paths: TmpPaths) -> str` ergänzt `PIP_CACHE_DIR=<abs>/cache/pip` und `npm_config_cache=<abs>/cache/npm` genau dann, wenn `paths.system_temp_exception.toolchain_cache` (YAML `toolchain-caches`) aktiv **und** der Sink enabled ist; `_validate_repo_containment` weist `toolchain-caches: true` bei `enabled: false` mit `_fail`/Exit 1 ab; `check_temp_literals` meldet bei aktivem Opt-in die WARNING `temp-literal.toolchain-cache-in-repo`. Consumes: `TmpPaths`/`SystemTempException.toolchain_cache` (Task 1), `_fail` (`config.py:496`) und die Ausnahme-Matrix (Task 2), Config-Key `system-temp-exception` (Task 17), Check-Familie `temp-literal.*` (Task 22).

**Rot zuerst:** `tests/test_tmp_sink_output_dirs.py::test_toolchain_cache_opt_in_pins_cache_dirs` schlägt fehl, weil `tmp_sink_env_pin_block` heute nur `TMPDIR`/`TEMP`/`TMP` kennt und keinen Cache-Key setzt; `tests/test_repo_containment_validate.py::test_toolchain_cache_requires_enabled_exception` schlägt fehl, weil der Validator den Widerspruch `toolchain-caches: true` bei `enabled: false` heute widerspruchsfrei durchlässt.

- [x] Step 1: Tests schreiben (rot): AC-38 in drei Fällen — Default aus (`toolchain-caches` nicht gesetzt ⇒ Block enthält weder `PIP_CACHE_DIR` noch `npm_config_cache`, `TmpPaths.env` bleibt cache-neutral), Opt-in aktiv (`enabled: true` **und** `toolchain-caches: true` ⇒ beide Keys absolut unter `<absolute>/cache/…`, dieselbe absolute Basis wie `TMPDIR`), Widerspruch (`toolchain-caches: true` bei `enabled: false` ⇒ `_fail`, Exit 1, dokumentierter Fehlertext). Zusatz-Assertions: jeder Cache-Wert ist absolut (`os.path.isabs`) und enthält kein `"`; `docker` taucht in keinem Cache-Key auf.
- [x] Step 2: `tmp_sink_env_pin_block` um die zwei Cache-Keys erweitern (rein datengetrieben aus `TmpPaths.system_temp_exception.toolchain_cache`, kein Provider-Name, kein `docker`-Zweig); `_validate_repo_containment` um den Widerspruchsfall ergänzen; `.meta-config/project.yaml` und `templates/configs/project.yaml.example` tragen `toolchain-caches: false` explizit.
- [x] Step 3: `python3 -m pytest tests/test_tmp_paths_builder.py tests/test_tmp_sink_output_dirs.py tests/test_repo_containment_validate.py -q` grün; `python3 scripts/sync.py --validate` ohne neues Finding.
- [x] Step 4: Commit `feat: add opt-in toolchain cache pin for tmp sink` — offen: der Auftrag lautet ausdrücklich „Do NOT commit/push“; Commit-Authority bleibt beim `git`-Agenten.

### Task 20: Antigravity `args.FilePath` → `file_path` (Q10)

**Agent:** developer
**Depends on:** 9
**Files:**
- Modify: `hooks/1-generic/antigravity-json-adapter.sh`
- Modify: `tests/test_antigravity_hooks_registration.py`

**Interfaces:** Produces: `ARG_KEY_MAP` (`antigravity-json-adapter.sh:111`) enthält `'FilePath': 'file_path'`, sodass `args.FilePath` als `tool_input.file_path` beim Ziel-Hook ankommt; der bestehende Test `test_adapter_normalizes_edit_tool_names` erhält die Assertion `received["tool_input"]["file_path"] == "/ws/a.md"`. Ein separater PascalCase-Contract-Test ist **nicht** gefordert (AC-40). Consumes: Hook-`file_path`-Lookup (`repo-containment-impl.sh:391-397`), `ARG_KEY_MAP`-Normalisierung (`antigravity-json-adapter.sh:111`), Task 9 (gleiche Testdatei, deshalb sequenziell).

**Rot zuerst:** nach Ergänzung der Assertion schlägt `tests/test_antigravity_hooks_registration.py::test_adapter_normalizes_edit_tool_names` fehl, weil `tool_input` heute `FilePath` statt `file_path` trägt.

- [x] Step 1: Assertion `received["tool_input"]["file_path"] == "/ws/a.md"` im bestehenden Test ergänzen (rot).
- [x] Step 2: `ARG_KEY_MAP` um die eine Zeile `'FilePath': 'file_path'` erweitern; kein Provider-Name im Code, Deny/Allow-Vertrag und `mktemp`-Ausnahme (`:167-168`) unverändert.
- [x] Step 3: `python3 -m pytest tests/test_antigravity_hooks_registration.py tests/test_repo_containment_hook.py -q` grün.
- [x] Step 4: Commit `fix: map antigravity FilePath to file_path in adapter`.

### Task 21: §5.5 verweist auf `PYTEST_BASETEMP` (Q11)

**Agent:** developer
**Depends on:** 17
**Files:**
- Modify: `docs/concepts/repo-containment-prison-mode.md`
- Modify: `tests/test_docs_tmp_sink_injection.py`

**Interfaces:** Produces: §5.5 nennt `PYTEST_BASETEMP` und den Config-Key `system-temp-exception` als Quelle des Basetemp-Werts und enthält kein `--basetemp=/tmp`-Literal; die Pflichtregel „Der pytest-Basetemp darf NIE im Arbeitsbaum liegen" bleibt wörtlich erhalten (AC-41). Consumes: Token/Config-Key aus Task 3, Doku-Testdatei aus Task 17 (gleiche Datei, deshalb sequenziell).

**Rot zuerst:** `tests/test_docs_tmp_sink_injection.py::test_prison_mode_section_uses_basetemp_variable` schlägt fehl, weil §5.5 (`:404-439`) heute `--basetemp=/tmp/<user>` literal als Beispiel und im kanonischen Aufruf nennt (`:410-411`, `:428-429`) und `PYTEST_BASETEMP` nicht erwähnt.

- [x] Step 1: Test schreiben (rot): §5.5 enthält `PYTEST_BASETEMP` und `system-temp-exception`, nicht aber `--basetemp=/tmp`; der Pflichtsatz „Der pytest-Basetemp darf NIE im Arbeitsbaum liegen" ist wörtlich enthalten.
- [x] Step 2: Doku anpassen: Beispiel und kanonischer Aufruf verweisen auf `PYTEST_BASETEMP` bzw. den Config-Key `system-temp-exception`; der Pflichtsatz bleibt unverändert.
- [x] Step 3: `python3 -m pytest tests/test_docs_tmp_sink_injection.py -q` grün.
- [x] Step 4: Commit `docs: point prison-mode section 5.5 at PYTEST_BASETEMP` — offen: der Auftrag für Task 21 lautet ausdrücklich „Do NOT commit/push“; Commit-Authority bleibt beim `git`-Agenten.

### Task 22: Allowlist-Schema-Härtung (Q6)

**Agent:** developer
**Depends on:** 4, 14
**Files:**
- Modify: `scripts/lib/consistency/temp_literals.py`
- Modify: `.meta-config/temp-literal-allowlist.yaml`
- Modify: `tests/test_consistency_temp_literals.py`

**Interfaces:** Produces: Schema-Prüfung in `check_temp_literals` — Pflichtfelder `path`, `pattern`, `reason`; optional `owner`; `expires` wird nicht unterstützt. Ein vollständiger Eintrag unterdrückt den Verstoß; fehlendes `reason` oder ein nicht unterstütztes Feld ⇒ der Verstoß bleibt WARNING **und** der ungültige Eintrag wird als WARNING derselben Check-Familie gemeldet (AC-39). Consumes: Allowlist-Datei (Task 4), Modul und Codes `temp-literal.*` (Task 14).

**Rot zuerst:** `tests/test_consistency_temp_literals.py::test_allowlist_requires_reason` und `::test_allowlist_rejects_expires_field` schlagen fehl, weil heute ein Eintrag ohne `reason` unterdrückt und `expires` ignoriert wird.

- [x] Step 1: Tests schreiben (rot): AC-39 in drei Fällen — vollständiger Eintrag unterdrückt, fehlendes `reason` unterdrückt nicht und erzeugt zusätzlich eine WARNING für den ungültigen Eintrag, `expires` wird wie ein nicht unterstütztes Feld behandelt; `owner` bleibt optional und ändert das Ergebnis nicht.
- [x] Step 2: Schema-Prüfung implementieren (Feld-Whitelist, `reason`-Pflicht), `.meta-config/temp-literal-allowlist.yaml` mit begründetem Kopfkommentar und unverändert leerer `entries`-Liste; kein Hard-Exit, die WARNING bleibt.
- [x] Step 3: `python3 -m pytest tests/test_consistency_temp_literals.py -q` grün.
- [x] Step 4: Commit `feat: enforce temp-literal allowlist schema` — offen: der Auftrag für Task 22 lautet ausdrücklich „Do NOT commit/push“; Commit-Authority bleibt beim `git`-Agenten.

### Task 18: Abschluss-Validierung und Ledger

**Agent:** validator
**Depends on:** 15, 16, 17, 19, 20, 21, 22
**Files:**
- Modify: `docs/plans/2026-10-24-tmp-sink-injection-plan.md`
- Modify: `tests/test_spec_plan_validate_cli.py`

**Interfaces:** Produces: Gate-Test „Plan mit Tasks + nicht freigegebene Spec ⇒ genau ein `spec_plan_approval_marker`-ERROR"; abgeschlossener Ledger (alle Checkboxen `- [x]`). Consumes: alle vorherigen Tasks; `_check_approval_markers` (`scripts/lib/consistency/spec_plan.py:479-507`).

Task 18 ist das Abschluss-Gate und läuft **zuletzt**, obwohl seine ID kleiner ist als 19–22: die IDs sind stabil, keine Umnummerierung (Rev. 3). Er hängt deshalb zusätzlich an den Rev.-3-Tasks 19, 20, 21 und 22.

**Rot zuerst:** `test_unapproved_spec_yields_exactly_one_approval_error` schlägt fehl, solange der Test die Anzahl der ERRORs nicht isoliert (heute prüft die Datei nur, dass ein Fehler auftritt).

- [x] Step 1: Test schreiben (rot): synthetische Fixture mit `spec` (ohne Approval) plus `plan` mit Tasks und `**Spec:**`-Verweis; Assertion `[f for f in findings if f.check == "spec_plan_approval_marker"]` hat Länge 1 und alle übrigen `check`-Werte sind nicht `spec_plan_approval_marker`.
- [x] Step 2: Grün-Lauf der bestehenden Suite und des Sync-Gates: `python3 -m pytest tests/test_spec_plan_validate_cli.py -q` grün und `python3 scripts/sync.py --validate` grün (kein neues Finding). Beide Ausgaben mit Exit 0 protokollieren.
- [x] Step 3: Erwartungs-Schritt (bewusst rot, kein Defekt): `python3 scripts/sync.py --validate-spec-plan` gegen dieses Repo ausführen. Erwartet wird Exit 1 mit genau einem ERROR `spec_plan_approval_marker` für `docs/plans/2026-10-24-tmp-sink-injection-plan.md` und 0 WARNINGS; Ausgabe wörtlich im Abschnitt „Gate-Status" festhalten. Weicht die Anzahl ab, ist das ein Befund und blockiert den Abschluss. — **Ausgeführt 2026-10-25:** Nach der Freigabe (Spec `APPROVED`) meldet der Lauf **0 Findings, Exit 0** (Lauf A/B im Abschnitt „Gate-Status"); die Vor-Freigabe-Erwartung „Exit 1, genau ein ERROR" ist damit überholt und wird durch `test_unapproved_spec_yields_exactly_one_approval_error` belegt.
- [x] Step 4: Alle Checkboxen dieses Plans auf `- [x]` setzen; Ergebnis aus Step 2 und Step 3 im Abschnitt „Gate-Status“ nachtragen (kein Approval-Marker). — **abgeschlossen (2026-10-25):** 90 abgehakte Checkboxen, 0 offene; die finalen Gate-Zahlen stehen unter „Abschluss-Gate (Task 18) — finale Verifikation (2026-10-25)“. Der frühere Stand („blockiert, Full-Suite-Gate rot 17 > 16“) ist überholt: der Ratchet steht wieder auf 16 Zeilen / 165 Vorkommen.
- [x] Step 5: Commit `chore: close plan ledger after validator run`. — **Ledger geschlossen (2026-10-25); Commit delegiert:** dieser Validator-Lauf committet nicht. Die Commit-Ausführung liegt beim Orchestrator → `git`-Agenten (Commit-Authority); die Statuszeile bleibt bis dahin `— (pending)`.

## Guard-Tests

Vier Guards, jede mit eigenem Rot-Beleg und ohne Test-only-Bypass im Produktionscode:

| # | Guard | Datei | Rote Phase | Grüne Phase |
|---|---|---|---|---|
| a | Kein System-Temp-Literal in `agents/**` außer dokumentierter Allowlist | `tests/test_temp_literals.py::test_no_system_temp_literal_in_agents` (+ `test_no_system_temp_literal_in_standalone`) | 18 Literale in 7 Templates, 18 + 4 in `standalone/**` | Task 4 (Templates), Task 7 (Standalone) |
| b | Hook fail-closed bei `cwd` außerhalb jedes Projekts | `tests/test_repo_containment_hook.py::test_cwd_outside_project_cannot_be_adopted`, `tests/test_tmp_sink_injection.py::test_hook_blocks_cwd_outside_project` | `$PWD`-Adelung liefert Exit 0 | Task 8 (Logik), Task 9 (Matrix) |
| c | `backup.py` ohne System-Temp-Rest | `tests/test_tmp_sink_injection.py::test_backup_module_has_no_system_temp_remainder` | `TemporaryDirectory()` ohne `dir=` (`backup.py:340`) | Task 11 |
| d | `TMPDIR`-Pinning für alle Subprozess-Starts | `tests/test_tmp_sink_injection.py::test_every_subprocess_start_pins_tmp_env`, `tests/test_tmp_sink_env_coverage.py::test_subprocess_calls_pin_temp_env` | 12 ungeschützte Aufrufe in `scripts/*.py`, 47 Treffer in `scripts/**` | Task 10, Task 11 |

`tests/test_tmp_sink_injection.py::test_temp_literal_pattern_has_single_source_of_truth` ergänzt die vier Guards um den Einzelquellen-Nachweis des AC-01-Musters; der Rot-Beleg ist in Task 15 Step 1 benannt (Ist-Wert: zwei Definitionsdateien).

Zusatz-Guards (bereits vorhanden, werden mitgeführt): `tests/test_template_report_paths.py::test_no_provider_tmp_path_in_agents` (`:42-48`) bleibt unverändert; `test_read_only_reviewer_has_no_write_tools` bleibt unverändert.

## Goldens- und AC-01-Rebaseline

- **Betroffene Golden-Varianten:** `OG-TAIL-DOCKER` (`tests/test_template_slimming_equivalence.py:890`, deckt `devops-engineer`, `docker`, `e2e-tester`, `tester`), `OG-TAIL-DEV` (`:931`, `developer`), `OG-PASS-CODE-REVIEWER` (`:1023`, `code-reviewer`). Maßgeblich sind die Bezeichner, nicht die Zeilennummern.
- **Betroffene Fixture-Dateien:** `tests/fixtures/slimming-golden/tester.md:51`, `test-executor.md:33,41`, `e2e-tester.md:73`, `documenter.md:68` — alle vier frieren `--basetemp=/tmp/$USER/pytest-agent-meta` ein.
- **Weitere Guards mit Literal-Bezug:** `tests/test_template_report_paths.py:68-71` (ersetzt in Task 5, AC-02), `tests/conftest.py:28` (`_EXTERNAL_BASETEMP_HINT`, Task 16), `tests/test_knowledge_engine.py:81`, `tests/test_basetemp_guard.py`-Hinweistexte (Task 16), `tests/test_provider_reactivation_artifacts.py:16,65` (nicht im Check-Scope, wird beim Rebase mitgeführt).
- **AC-01 und Rebaseline:** AC-01 ist auf Dateiebene nach Task 4 grün, aber die Guard-Suite aus AC-01 und AC-19 ist erst nach der Rebaseline wieder vollständig grün — `tests/test_template_slimming_equivalence.py` friert die alten Literale byte-genau ein und wird durch jede Template-Änderung rot. Deshalb gilt: kein Merge zwischen Task 4 und Task 16.
- **Reihenfolge (verbindlich):** Template-Änderung → Golden-Diff bewusst prüfen (nur erwartete Zeilen) → Golden aktualisieren → Guard-Test grün. Ein umgekehrter Ablauf (Golden zuerst anpassen) würde den Guard entwerten.
- **Drift-Gate:** `python3 scripts/sync.py --render-standalone --check` muss nach Task 7 und nach Task 16 Exit 0 liefern.

## Rollback

- **Sink abschalten (erster Hebel):** `repo_containment.tmp-sink.enabled: false` in `.meta-config/project.yaml`, danach `python scripts/sync.py`. Ergebnis: Sync bleibt ok (`log.skip`), `TMP_SINK_PATH` bleibt relativ gesetzt, `TMP_SINK_ABS_PATH` und `TMP_SINK_ENV_PIN_BLOCK` entfallen, Schreib-APIs werfen `tmp-sink.disabled` erst bei Bedarf. Kein Datenverlust: `ensure_tmp_sink` löscht nie, `cleanup: manual` ist Default.
- **Hook abschalten (zweiter Hebel):** `repo_containment.enabled: false` (projektlokal, optional pro Provider über `provider-overrides`), danach `python scripts/sync.py`. Die Deregistrierung läuft über die Config und den Re-Sync — kein manuelles Editieren von `.claude/settings.json`, keine Handänderung an `hooks/**`. `orchestrator-guard` und `branch-guard` bleiben unberührt.
- **`system-temp-exception` ist kein Rollback-Hebel:** `enabled: false` würde den Basetemp unter `<sink>/pytest` legen und damit §5.5 inhaltlich umkehren. Wer das will, braucht einen eigenen Änderungsantrag (Nicht-Ziel der Spec), nicht diesen Plan.
- **Template-Rollback:** ein Revert der Platzhalter-Ersetzung geht nur zusammen mit einer Golden-Rebaseline zurück; ohne sie bleibt `tests/test_template_slimming_equivalence.py` rot. Empfohlene Reihenfolge beim Revert: Templates zurück → Goldens aus dem Revert-Stand neu einfrieren → `tests/test_temp_literals.py`-Ausnahmen begründen (oder Guard mitrevertieren).
- **Env-Pin zurücknehmen:** nach `tmp-sink.enabled: false` erneut syncen; in einer laufenden Shell zusätzlich `unset TMPDIR TEMP TMP`, sonst zeigen Kindprozesse weiter auf den alten Sink.
- **Backup-Staging:** Fallback auf System-Temp greift automatisch bei `tmp-sink.disabled` (mit WARNING `backup.staging-system-temp`); kein Rollback-Schritt nötig.
- **Datenverlust-Risiko:** keiner der Schritte löscht Inhalte. `cleanup: on-sync` ist nicht Teil dieses Plans.

## Risiko- und Nebenwirkungsanalyse

| Risiko | Wirkung | Gegenmaßnahme | Restrisiko |
|---|---|---|---|
| Verhaltenswechsel bei Bestandsprojekten: Hook blockt Writes, die vorher durchgingen (Arbeit aus `/tmp` oder `$HOME`) | Arbeitsstopp, Nutzer schaltet Containment ab (schlimmer als vorher) | Meldung mit `target`, `anchor`, `repair`, `opt-out`; §5.5-Doku in Task 17; Rollout-Hinweis mit `sync.py --validate`; Opt-out projektlokal | Projekte, die den Opt-out pauschal setzen, verlieren den Guard vollständig |
| Golden-Rebaseline ist aufwendig und wird „weggefixt" | Guard verliert Beweiskraft, Suite dauerhaft rot | Rebaseline als eigener Task (16) mit bewusster Diff-Prüfung; kein Merge zwischen Task 4 und 16; Drift-Gate `--render-standalone --check` | Künftige Template-Änderungen brechen die Goldens erneut (bekannte Betriebslast) |
| 47 `subprocess`-Treffer in `scripts/**` gegen 12 namentlich bekannte Aufrufe in `scripts/*.py` | Klassifikation wird unvollständig, neue Aufrufe bleiben ungepinnt | AST-Scan im Guard (Task 15), Allowlist mit `{path, symbol, reason}`, Test schlägt bei neuem Ausreißer fehl | Aufrufe über Indirektion (`getattr(subprocess, ...)`) werden nicht erkannt |
| `standalone/agents/`-Drift-Gate schlägt fehl oder wird umgangen | Ausgelieferte Personas behalten Literale und Platzhalter-Notiz | `--render-standalone --check` als Gate in Task 7 und 16; Temp-Literal-Check deckt `standalone/**` ab | Regeneration muss bei jeder künftigen Template-Änderung mitlaufen |
| Ancestor-Kollision in den neuen Hook-Tests (Fixture unter dem echten Repo) | Tests grün/rot je nach Basetemp, Guard ohne Beweiskraft | Fixture per `tempfile.mkdtemp(dir=tempfile.gettempdir())` plus Assertion „kein `.meta-config/` im Ancestor-Pfad" (Task 8/9, R12) | Basetemp-Wechsel in CI kann die Assertion selbst brechen, wenn `gettempdir()` im Repo liegt (dann lauter Fehlschlag, kein stiller) |
| Opencode bleibt advisory (kein Runtime-Gate, `has_hooks: false`) | Nutzer hält den Edit-Scope für eine Garantie | WARNING `repo-containment.no-hook-support` bleibt (AC-20), WARNING `temp-literal.provider-advisory` neu, Doku nennt die Grenze | Pro-Rolle-`edit: allow` hebt die globale Deny-Regel weiterhin faktisch auf |
| Windows-Pfadfälle (`C:\Temp`, Laufwerksbuchstaben, UNC, Leerzeichen) | Fehlblockade oder kaputtes `--basetemp`-Argument | AC-01-Muster enthält `%TEMP%` und `[A-Za-z]:\\Temp\\`; Basetemp shell-gequotet, `"` im Wert verboten (AC-34); Pfadvalidierung unverändert | Pfade mit `$` oder Zeilenumbruch sind bewusst abgelehnt |
| Env-Pin zeigt nach Umzug auf einen toten Pfad | Tool-Fehler, die wie Guard-Fehler aussehen | Existenzprüfung **vor** dem Export mit Reparaturzeile (AC-36); Standalone setzt den Block leer | Ohne Re-Sync bleibt der Block bis zum nächsten Sync veraltet (dokumentiert) |
| Symlink/TOCTOU im Sink | Prüfung sagt „innen", Write landet „außen" | `realpath` vor Ancestor-Suche und im Verdict; `_ensure_inside_sink` | Kein `O_NOFOLLOW`-Write im Hook möglich (bekannte Grenze) |
| Zwei Fehlerzeitpunkte (Config-Validierung vs. Schreibzugriff) | Verwirrung, welcher Fehler wann greift | Fehlermatrix der Spec, AC-24/AC-25, Doku in Task 17 | Aufrufer, die `TmpSinkError` nicht fangen, brechen hart (gewollt) |
| Doppelter Check-Name (`temp_literals` vs. `tmp_sink_injection`) | Zwei Implementierungen driften | Modulname auf `temp_literals.py` fixiert (IC-11), Test importiert das Muster (Task 15) | Keine |
| Antigravity-`FilePath`-Zuordnung (Q10 entschieden, ADR-15) | ohne Mapping scheitern Antigravity-Writes am `file_path`-Check fail-closed | `ARG_KEY_MAP` mappt `FilePath` → `file_path` (Task 20, AC-40); der Regressionsfall im bestehenden Adapter-Test hält das Mapping fest | Weitere, heute unbekannte PascalCase-Argumente bleiben unmapped und damit fail-closed |
| `toolchain-caches: true` bläht Sink/Backup und wird bei `cleanup: on-sync` gelöscht | größerer Arbeitsbaum, mehr Backup-/CI-Volumen, nach einem Umzug toter Cache-Pfad | Default `false`; Opt-in nur bei `enabled: true`; WARNING `temp-literal.toolchain-cache-in-repo` (Task 19/22); Doku in §5.5 und im Config-Beispiel; `docker` wird nie umgeleitet | Ein bewusstes Opt-in kann den Arbeitsbaum vergrößern und bei `cleanup: on-sync` den Cache verlieren |

## Aufwand

Schätzung `effort-estimator`, 2026-10-24 (Textreferenz; nicht neu berechnet).

| Phase | Tasks | Schätzung | Spanne |
|---|---|---|---|
| P0 Fundament (Resolver, Builder, Token) | 1–3 | 13 h | 8–22 h |
| P1 Templates (Literale, Sink, vage Stellen, Standalone) | 4–7 | 6 h | 4–10 h |
| P2 Hook fail-closed (Logik, Testmatrix) | 8–9 | 10 h | 6–17 h |
| P3 Env-Pin, Backup, Zweitparser | 10–12 | 10 h | 6–17 h |
| P4 Provider-Agnostik, Consistency | 13–14 | 4 h | 2,5–7 h |
| P5 Guards, Goldens, Doku, Abschluss | 15–18 | 11 h | 7–19 h |
| P6 — Rev.-3-Entscheidungen (Toolchain-Opt-in, Allowlist-Schema, Adapter-Mapping, §5.5-Doku) | 19–22 | 6,5 h | 3,5–12 h |
| **Summe** | 22 | **60,5 h** | **36,5–104 h** |

P6 ist ein Textreferenz-Nachtrag (Rev. 3), keine neue `effort-estimator`-Ausführung; die übrigen Zeilen sind unverändert.

- **Lead Time:** 8–10 Arbeitstage inklusive Gates bei einem Entwickler.
- **Slack:** 20 % (rund 11 h) getrennt vom Schätzpuffer — für Review-Runden, Golden-Diff-Prüfung und Hook-Debugging.
- **Top-Posten:** P0-Resolverbau, P5-Guards/Goldens, P2 und P3 mit je 10 h; P6 kommt als Rev.-3-Nachtrag mit 6,5 h hinzu.
- **Vergleichsanker:** eine reine Literal-Ersetzung ohne zentrale Schicht liegt bei 14–16 h, deckt aber nur 4 der 14 Injektionspunkte ab und lässt Resolver, Hook, Backup, Provider-Scope und Zweitparser offen.
- **Zentrale Annahme:** ein Entwickler, keine Parallelisierung (die Gruppen PG-A/PG-B sind optional), Tests zu Beginn grün.

## Traceability (AC → Task)

| AC | Prüfaussage (gekürzt) | Task | Test |
|---|---|---|---|
| AC-01 | kein System-Temp-Literal in `agents/**` außer Allowlist | 4, 15 | `tests/test_temp_literals.py` |
| AC-02 | vier Auditor-Templates nutzen den Platzhalter | 5 | `tests/test_template_report_paths.py` |
| AC-03 | Hook fail-closed ohne Projekt-Root | 9 | `tests/test_repo_containment_hook.py` |
| AC-04 | relatives Ziel ohne `cwd` blockt | 9 | `tests/test_repo_containment_hook.py` |
| AC-05 | echter Fail-open-Fall (`cwd=/tmp`, Ziel `/tmp/x`) blockt | 8, 9 | `tests/test_repo_containment_hook.py` |
| AC-06 | relatives Ziel wird gegen `cwd` geprüft | 9 | `tests/test_repo_containment_hook.py` |
| AC-07 | Symlink-`cwd` wird aufgelöst | 9 | `tests/test_repo_containment_hook.py` |
| AC-08 | `enabled: false` bleibt projektlokal wirksam | 9 | `tests/test_repo_containment_hook.py` |
| AC-09 | Backup-Staging liegt im Sink | 11 | `tests/test_backup_round_trip_804.py` |
| AC-10 | Backup ohne Sink bleibt laut und funktionsfähig | 11 | `tests/test_backup_robustness.py` |
| AC-11 | alle Subprozesse erhalten Env-Pinning | 11 | `tests/test_tmp_sink_env_coverage.py` |
| AC-12 | `TMPDIR`/`TEMP`/`TMP` absolut unter dem Root | 1, 10 | `tests/test_tmp_sink_output_dirs.py` |
| AC-13 | `TEST_COMMANDS`/`CODE_QUALITY_RULES` literal-frei | 3 | `tests/test_tmp_sink_output_dirs.py` |
| AC-14 | unersetztes Token bricht den Sync hart | 2 | `tests/test_tmp_paths_builder.py` |
| AC-15 | `system-temp-exception` ist validiert (vier Fälle) | 2 | `tests/test_repo_containment_validate.py` |
| AC-16 | `TMP_SINK_PATH` relativ, `TMP_SINK_ABS_PATH` absolut | 2 | `tests/test_tmp_paths_builder.py` |
| AC-17 | Opencode-Edit-Scope folgt dem Sink | 13 | `tests/test_opencode_primary_edit_lock.py` |
| AC-18 | Hook-Meldungen nennen absolute Pfade | 9 | `tests/test_repo_containment_hook.py` |
| AC-19 | Goldens sind rebased | 16 | `tests/test_template_slimming_equivalence.py` |
| AC-20 | hook-lose Provider bleiben advisory, aber sichtbar | 13 | `tests/test_repo_containment_consistency.py` |
| AC-21 | Temp-Literal-Check wirkt und blockiert nicht | 14 | `tests/test_consistency_temp_literals.py` |
| AC-22 | vage Temp-Anweisungen sind ersetzt | 6 | `tests/test_template_report_paths.py` |
| AC-23 | Resolver wirft nicht bei deaktiviertem Sink | 1 | `tests/test_tmp_sink_output_dirs.py` |
| AC-24 | Schreib-APIs werfen weiterhin `tmp-sink.disabled` | 1 | `tests/test_tmp_sink_output_dirs.py` |
| AC-25 | Sync mit deaktiviertem Sink ist erfolgreich | 2 | `tests/test_tmp_paths_builder.py` |
| AC-26 | Standalone literal-frei und drift-frei | 7, 15 | `tests/test_temp_literals.py` |
| AC-27 | Standalone nennt den Framework-Default-Sink | 7 | `tests/test_standalone_render.py` |
| AC-28 | leerer `cwd` ankert am Zielverzeichnis | 9 | `tests/test_repo_containment_hook.py` |
| AC-29 | leerer `cwd` plus System-Temp-Ziel blockt | 9 | `tests/test_repo_containment_hook.py` |
| AC-30 | Adapter-Ausnahme bleibt lokal und wird aufgeräumt | 9 | `tests/test_antigravity_hooks_registration.py` |
| AC-31 | Gitignore-Eintrag folgt dem Sink | 12 | `tests/test_tmp_sink_default_on.py` |
| AC-32 | Doctor-Finding nutzt dieselbe Auflösung | 12 | `tests/test_doctor_runner.py` |
| AC-33 | relatives Ziel mit `cwd`-Tiefe am realen Ort geprüft | 8, 9 | `tests/test_repo_containment_hook.py` |
| AC-34 | Basetemp mit Leerzeichen bricht den Aufruf nicht | 3 | `tests/test_tmp_sink_output_dirs.py` |
| AC-35 | `TMP_SINK_ENV_PIN_BLOCK` setzt nur absolute Werte | 1, 2 | `tests/test_tmp_sink_output_dirs.py` |
| AC-36 | Env-Pin exportiert keinen toten Pfad | 1, 2 | `tests/test_tmp_sink_output_dirs.py` |
| AC-37 | Anker aus dem Ziel wählt das Projekt des Ziels | 9 | `tests/test_repo_containment_hook.py` |
| AC-38 | Toolchain-Caches sind Opt-in, Default aus | 19 | `tests/test_tmp_sink_output_dirs.py`, `tests/test_repo_containment_validate.py` |
| AC-39 | Allowlist-Schema: `reason` Pflicht, `expires` nicht unterstützt | 4, 14, 22 | `tests/test_consistency_temp_literals.py` |
| AC-40 | Antigravity-Adapter mappt `FilePath` → `file_path` | 20 | `tests/test_antigravity_hooks_registration.py`, `tests/test_repo_containment_hook.py` |
| AC-41 | §5.5 verweist auf `PYTEST_BASETEMP` statt auf ein `/tmp`-Literal | 17, 21 | `tests/test_docs_tmp_sink_injection.py` |

Tasks ohne eigenen AC (begründet): **Task 18** (Gate- und Ledger-Abschluss, prüft den Validator, nicht ein AC der Spec). **Task 17** bleibt Doku-Grundlage und trägt AC-41 anteilig (Konfigurationsabschnitt, `system-temp-exception`); den Regeltext-Verweis selbst setzt Task 21. **Task 7** trägt AC-26/AC-27, **Task 15** aggregiert AC-01/AC-09/AC-11/AC-28-Fälle ohne eigene Spec-AC. Die Rev.-3-Tasks tragen je genau einen AC: Task 19 → AC-38, Task 20 → AC-40, Task 21 → AC-41, Task 22 → AC-39 (Task 22 setzt zusätzlich die Allowlist-Basis aus Task 4/14 durch).

## Self-Review

| Prüfpunkt | Ergebnis | Beleg |
|---|---|---|
| (a) alle 41 ACs abgedeckt | bestanden | Traceability-Tabelle hat 41 Zeilen (AC-01 bis AC-41), keine Lücke, keine Doppelzuordnung ohne Task; die vier Rev.-3-ACs (AC-38…AC-41) sind je mindestens einem Task zugeordnet |
| (b) jeder Task hat einen Test | bestanden | 22 Tasks, jeder `**Files:**`-Block enthält mindestens eine `tests/`-Datei; Task 15/18 erzeugen bzw. erweitern Tests statt Produktionscode |
| (c) keine Dangling-`Depends on` | bestanden | alle referenzierten IDs liegen in 1–22; T1 ohne Vorbedingung, kein Verweis auf fremde Pläne; Task 18 hängt zusätzlich an 19–22 (kleinere ID, aber Abschluss-Gate — IDs bleiben stabil, keine Umnummerierung) |
| (d) keine Zyklen | bestanden | Kanten laufen vorwärts bis auf die dokumentierte Rückwärtskante `T22 --> T15` (Task 15 hängt an 22) und die Abschlusskanten auf T18; kein Zyklus, weil T15 nicht auf T22 zurückwirkt und T18 keine Nachfolger hat; kritischer Pfad unverändert T1→T2→T3→T5→T6→T7→T15→T18 |
| (e) `Files:`-Disjunktheit in den Parallel-Gruppen | korrigiert; Rev. 3 unverändert, Re-Run ausgeführt — Ergebnis im Abschnitt „Rev. 3 — Re-Validierung" belegt | PG-A {4,5}, PG-B {11,12}: harte Datei-Schnittmenge leer; Kopplung über Import-/Doku-Kanten erkannt und durch Sequenzialisierung aufgelöst (PG-B `{11,12}`, Task 10 davor; Task 13 → 17 sequenziell). Task 6 aus PG-A entfernt, weil es `tests/test_template_report_paths.py` mit Task 5 teilt; PG-C `{13,17}` aufgelöst. Rev. 3 ändert weder `Files:` noch `Depends on` von Task 4/5/11/12; Tasks 19–22 laufen sequenziell und bilden keine Gruppe. Der Re-Run ist ausgeführt und im Abschnitt „Rev. 3 — Re-Validierung" belegt: PG-A `{4,5}` und PG-B `{11,12}` liefern `conflict: []`, der Gesamtgraph ohne Fehler |
| (f) Traceability Spec ↔ Task ↔ Test vollständig | bestanden | Tabelle unten; jede Zeile nennt `task-<n>` und die zugehörige Testdatei, jede AC-Zeile nennt mindestens einen Task |
| (g) keine Platzhalter | bestanden | keine Platzhalter-Marker, keine alleinstehende Ellipse-Zeile, kein leeres `Interfaces:`; alle 22 `**Files:**`-Blöcke enthalten nur `Create:`/`Modify:`-Zeilen |
| (h) Q3/Q6/Q10/Q11 sind je durch Task + AC abgedeckt | bestanden | Q3 → Task 19 + AC-38 (`test_toolchain_cache_opt_in_pins_cache_dirs`, `test_toolchain_cache_requires_enabled_exception`); Q6 → Task 22 + AC-39 (`test_allowlist_requires_reason`, `test_allowlist_rejects_expires_field`); Q10 → Task 20 + AC-40 (`test_adapter_normalizes_edit_tool_names` mit `file_path`-Assertion); Q11 → Task 21 (Regeltext) mit Task 17 als Basis + AC-41 (`test_prison_mode_section_uses_basetemp_variable`) |

### Traceability Spec ↔ Task ↔ Test

| Task | Testdatei | ACs |
|---|---|---|
| task-1 | `tests/test_tmp_sink_output_dirs.py` | AC-12, AC-23, AC-24, AC-35, AC-36 |
| task-2 | `tests/test_tmp_paths_builder.py`, `tests/test_repo_containment_validate.py`, `tests/test_repo_containment_schema.py` | AC-14, AC-15, AC-16, AC-25, AC-35, AC-36 |
| task-3 | `tests/test_tmp_sink_output_dirs.py` | AC-13, AC-34 |
| task-4 | `tests/test_temp_literals.py` | AC-01 |
| task-5 | `tests/test_template_report_paths.py` | AC-02 |
| task-6 | `tests/test_template_report_paths.py` | AC-22 |
| task-7 | `tests/test_standalone_render.py`, `tests/test_temp_literals.py` | AC-26, AC-27 |
| task-8 | `tests/test_repo_containment_hook.py` | AC-05, AC-33 |
| task-9 | `tests/test_repo_containment_hook.py`, `tests/test_antigravity_hooks_registration.py` | AC-03, AC-04, AC-05, AC-06, AC-07, AC-08, AC-18, AC-28, AC-29, AC-30, AC-33, AC-37 |
| task-10 | `tests/test_tmp_sink_output_dirs.py` | AC-12 |
| task-11 | `tests/test_tmp_sink_env_coverage.py`, `tests/test_backup_round_trip_804.py`, `tests/test_backup_robustness.py` | AC-09, AC-10, AC-11 |
| task-12 | `tests/test_tmp_sink_default_on.py`, `tests/test_doctor_runner.py` | AC-31, AC-32 |
| task-13 | `tests/test_opencode_primary_edit_lock.py`, `tests/test_repo_containment_consistency.py` | AC-17, AC-20 |
| task-14 | `tests/test_consistency_temp_literals.py` | AC-21 |
| task-15 | `tests/test_tmp_sink_injection.py`, `tests/test_temp_literals.py` | AC-01, AC-26 |
| task-16 | `tests/test_template_slimming_equivalence.py`, `tests/test_basetemp_guard.py` | AC-19 |
| task-17 | `tests/test_docs_tmp_sink_injection.py` | AC-41 (anteilig: Konfigurationsabschnitt/`system-temp-exception`) |
| task-18 | `tests/test_spec_plan_validate_cli.py` | kein AC (Gate) |
| task-19 | `tests/test_tmp_paths_builder.py`, `tests/test_tmp_sink_output_dirs.py`, `tests/test_repo_containment_validate.py` | AC-38 |
| task-20 | `tests/test_antigravity_hooks_registration.py`, `tests/test_repo_containment_hook.py` | AC-40 |
| task-21 | `tests/test_docs_tmp_sink_injection.py` | AC-41 |
| task-22 | `tests/test_consistency_temp_literals.py` | AC-39 |

### Verifizierte Korrekturen gegenüber der Vorgabe

- `tests/test_tmp_paths.py` existiert nicht als Zieldatei dieses Plans: die AC-namensgebende Datei ist `tests/test_tmp_sink_output_dirs.py` (bereits vorhanden, testet `resolve_output_dir`/`resolve_work_dir`) — dort liegen die Resolver-Tests.
- `scripts/lib/consistency/tmp_sink_injection.py` heißt in der Spec `scripts/lib/consistency/temp_literals.py` (IC-11); nur ein Modul, um Parallelimplementierungen zu vermeiden.
- `agent-meta.config.example.yaml` liegt unter `templates/configs/agent-meta.config.example.yaml` und trägt keinen System-Temp-Wert; der Repo-Containment-Beispielblock steht in `templates/configs/project.yaml.example:166-172` (Task 17).
- `tests/test_gitignore_managed_block.py` und `tests/test_doctor.py` existieren nicht; genutzt werden `tests/test_tmp_sink_default_on.py` (AC-31, testet `_tmp_sink_gitignore_entry`) und `tests/test_doctor_runner.py` (AC-32, prüft `doctor.tmp-sink-location`).
- `rules/1-generic/plan-ledger.md:67` (Inventar 13, Q9 entschieden) ist Task 6 zugeordnet, obwohl die Vorgabe dort nur 13 Rollen (12 SE-Rollen + `test-executor`) nennt.
- Task 6 ist nicht Teil von PG-A (geteilte Testdatei mit Task 5), siehe „Parallel-Gruppen".
- PG-B ist von `{10,11,12}` auf `{11,12}` reduziert; Task 10 läuft davor, `Task 11`/`Task 12` hängen an `1, 2, 10`. Grund: die Dreiergruppe wird über Import-Kanten um `scripts/lib/context_report.py` verkoppelt (Validator: zwei ERRORs).
- PG-C `{13,17}` ist aufgelöst; Task 17 hängt zusätzlich an 13. Grund: Doku-Referenzkanten `CHANGELOG.md` ↔ `config/provider-tools.yaml` und `docs/concepts/repo-containment-prison-mode.md` ↔ `tests/test_repo_containment_consistency.py` (Validator: ein ERROR).
- Rev. 3: Die Kante `T22 --> T15` aus der Vorgabe ist als echte Vorbedingung eingetragen, deshalb steht `22` zusätzlich in `Task 15: Depends on`. Ohne diese Zeile wäre die dokumentierte Kante im maschinenlesbaren Graphen nicht vorhanden (Task-Nummern bleiben unverändert).
- Rev. 3: Task 19 besitzt zusätzlich `scripts/lib/consistency/temp_literals.py`, weil die WARNING `temp-literal.toolchain-cache-in-repo` in diesem Modul entsteht (Task 14 legt es an, Task 22 härtet es). Damit ist die Datei-Ownership der sequenziellen Task-Kette 14 → 22 → 19 explizit statt implizit.

## Maschinelle Validierung (Validator, 2026-10-24)

Herkunft: Der Validator-Bericht beschreibt den Stand **vor** dieser Korrektur. Die Befunde unten sind wörtlich übernommen; alles, was erst nach der Korrektur gilt, ist als „im Re-Run zu bestätigen" markiert und **nicht** als bestanden.

### Befund vor der Korrektur (wörtlich)

- `OVERLAP_PG_A {4,5}`: `{"safe": ["task-4","task-5"], "conflict": []}` — unverändert übernommen.
- `OVERLAP_PG_B {10,11,12}`: `{"safe": [], "conflict": [["task-10","task-11",["scripts/lib/context_report.py","scripts/run_role_routing_eval.py"]], ["task-10","task-12",["scripts/lib/context_report.py","scripts/lib/doctor_detectors.py","tests/test_doctor_runner.py"]]]}` — 2 ERRORs.
- `OVERLAP_PG_B {11,12}`: `{"safe": ["task-11","task-12"], "conflict": []}` — die Zweiergruppe ist konfliktfrei; Grundlage der Korrektur.
- `OVERLAP_PG_C {13,17}`: `{"safe": [], "conflict": [["task-13","task-17",["CHANGELOG.md","config/provider-tools.yaml","docs/concepts/repo-containment-prison-mode.md","tests/test_repo_containment_consistency.py"]]]}` — 1 ERROR.
- Ursache: die harten Datei-Schnittmengen sind leer; die Konflikte entstehen über Import-/Doku-Referenzkanten (fail-closed-Kopplungsbegriff von `validate_plan` + `check_plan_file_overlap`), nicht über gemeinsame Schreiber.
- Graph: 18 Tasks, 0 dangling, 0 Zyklen, Task-IDs `task-1`…`task-18` lückenlos, Gesamtplan als `sequential` ⇒ `validate_plan == []`.
- Format: 15/18 Tasks vollständig ok. Abweichungen: Task 15 (Rot-Phase nur in Prosa, zusätzlich als „temporär zurückgedrehter Aufruf in einer lokalen Kopie" abgeschwächt), Task 16 (Step 1 war eine Golden-Diff-Prüfung statt eines fehlschlagenden Tests), Task 18 (kein Grün-Step; Step 2 ließ bewusst Exit 1 zu).
- Traceability 37/37 ok. Keine verbotenen Marker/Platzhalter. Secret-Scan clean.

### Korrektur und erwartetes Ergebnis

| Gruppe | Vorher | Nachher | Erwartetes Ergebnis im Re-Run |
|---|---|---|---|
| PG-A | `{4,5}` | `{4,5}` (unverändert) | erwartet: `safe`, `conflict` leer — im Re-Run zu bestätigen |
| PG-B | `{10,11,12}` | `{11,12}`, Task 10 davor (`Task 11`/`Task 12: Depends on 1, 2, 10`) | erwartet: `safe`, `conflict` leer — im Re-Run zu bestätigen |
| PG-C | `{13,17}` | aufgelöst, sequenziell (`Task 17: Depends on 3, 8, 9, 13`, Kante `T13 --> T17`) | keine Gruppe mehr zu prüfen; Graph im Re-Run zu bestätigen |

Begründung PG-C: `CHANGELOG.md` ↔ `config/provider-tools.yaml` und `docs/concepts/repo-containment-prison-mode.md` ↔ `tests/test_repo_containment_consistency.py` sind Doku-Referenzkanten; Task 17 dokumentiert, was Task 13 umsetzt. Sequenzialisierung statt Aufnahme in eine Allowlist.

Format-Korrekturen: Task 15 hat einen echten Rot-Beleg (fehlschlagende Assertion in Step 1, Ist-Wert benannt), Task 16 hat den fehlschlagenden Testlauf als Step 1 und die bewusste Golden-Diff-Prüfung als Step 2, Task 18 hat einen Grün-Step (Pytest + `--validate`) und einen separat benannten Erwartungs-Schritt (`--validate-spec-plan`, genau 1 ERROR). Ergebnis im Re-Run zu bestätigen.

### Gate- und Umfangs-Belege (Stand vor der Korrektur)

- `python3 scripts/sync.py --validate-spec-plan`: Exit 1, genau 1 ERROR `spec_plan_approval_marker`, 0 WARNINGS — erwartetes Gate (Spec ohne Approval), kein Defekt; im Re-Run zu bestätigen.
- Traceability: 37/37 ACs zugeordnet. Keine verbotenen Marker, keine Platzhalter. Secret-Scan clean.
- Der Bericht belegt: keine Datei außer den drei neuen Dokumenten ist geändert — `docs/specs/2026-10-24-tmp-sink-injection-spec.md`, das Review-Dokument und dieser Plan. Code, Templates, Tests und Config sind unberührt; kein Approval-Marker.

### Rev. 3 — Re-Validierung (2026-10-24)

Historischer Abschnitt oben beschreibt den Stand vor Rev. 3 und bleibt als Beleg erhalten.

**Statisch am Dokument geprüft** (Regeln von `_parse_plan_tasks`: `### Task <n>`-Kopf, `**Depends on:**`-Feld, `**Files:**`-Block):

- **Tasks: 22** (`task-1` … `task-22`, lückenlos, keine Doppel-ID); **ACs: 41** (AC-01 … AC-41).
- **Abhängigkeiten:** 1–18 unverändert bis auf `Task 15` (`+22`) und `Task 18` (`15, 16, 17, 19, 20, 21, 22`); neu: Task 19 ← 3, 17, 22; Task 20 ← 9; Task 21 ← 17; Task 22 ← 4, 14.
- **Dangling:** keine — alle referenzierten IDs liegen in 1–22. **Duplikate:** keine.
- **Zyklen:** keine — Kahn-Peeling über alle 22 Tasks läuft vollständig durch; die einzige Rückwärtskante `T22 --> T15` (Task 15 hängt an 22) schließt keinen Kreis, `T18` hat keine Nachfolger.
- **Kritischer Pfad:** unverändert `T1 → T2 → T3 → T5 → T6 → T7 → T15 → T18` (Länge 8; längste Alternativen: über `T16` 7, über `T19`/`T21` 6, über `T22` 5).
- **Parallel-Gruppen:** PG-A `{4,5}` und PG-B `{11,12}` unverändert; Tasks 19–22 laufen sequenziell und bilden keine dritte Gruppe.

**Ausführungsstatus: ausgeführt (2026-10-24).** Beide Läufe wurden aus dem Repo-Root
(`/home/hermes/repos/agent-meta`, Branch `docs/tmp-sink-injection-spec`) mit den vorgegebenen
Kommandos ausgeführt; die Ausgaben unten sind **wörtlich** übernommen.

#### Lauf 1 — Plan-Graph und Parallel-Gruppen (Inline-Python)

```
tasks: 22 ['task-1', 'task-2', 'task-3', 'task-4', 'task-5', 'task-6', 'task-7', 'task-8', 'task-9', 'task-10', 'task-11', 'task-12', 'task-13', 'task-14', 'task-15', 'task-16', 'task-17', 'task-19', 'task-20', 'task-21', 'task-22', 'task-18']
sequential errors: []
PG-A {'safe': ['task-4', 'task-5'], 'conflict': []}
PG-A errors: ["deadlock: task 'task-4' depends on unknown task_id 'task-3' (not part of this plan) — unresolvable wait", "deadlock: task 'task-5' depends on unknown task_id 'task-3' (not part of this plan) — unresolvable wait"]
PG-B {'safe': ['task-11', 'task-12'], 'conflict': []}
PG-B errors: ["deadlock: task 'task-11' depends on unknown task_id 'task-1' (not part of this plan) — unresolvable wait", "deadlock: task 'task-11' depends on unknown task_id 'task-2' (not part of this plan) — unresolvable wait", "deadlock: task 'task-11' depends on unknown task_id 'task-10' (not part of this plan) — unresolvable wait", "deadlock: task 'task-12' depends on unknown task_id 'task-1' (not part of this plan) — unresolvable wait", "deadlock: task 'task-12' depends on unknown task_id 'task-2' (not part of this plan) — unresolvable wait", "deadlock: task 'task-12' depends on unknown task_id 'task-10' (not part of this plan) — unresolvable wait"]
```

- Erwartung „`validate_plan` über den Gesamtplan ⇒ `[]`" **bestätigt**: 22 Tasks geparst, `sequential errors: []` — keine Duplikate, keine Dangling-ID, kein Zyklus.
- Erwartung „PG-A/PG-B-Overlap `conflict` leer" **bestätigt**: beide Gruppen liefern `'conflict': []`.
- Erwartung „`validate_plan` je Gruppe ohne ERROR" **nicht bestätigt**: PG-A meldet 2, PG-B meldet 6 ERRORs, sämtlich `deadlock: ... depends on unknown task_id ... (not part of this plan)`.
- **Ursache außerhalb des Plans — keine Plan-Korrektur, keine Abschwächung.** Die vorgegebene Prüfung baut die `FanoutPlan`-Teilpläne ausschließlich aus den Gruppentasks; `find_dependency_errors` wertet jede Vorbedingung außerhalb des Teilplans als Dangling-Dependency (Deadlock by construction). Betroffen sind reale, gruppenfremde Vorbedingungen: PG-A `task-4`/`task-5` ← `task-3`; PG-B `task-11`/`task-12` ← `task-1`, `task-2`, `task-10`. Diese Kanten sind im Gesamtplan korrekt und werden **nicht** entfernt — sie nur für den Teilplan-Lauf zu streichen, würde den Check entwerten. Es wurde **keine** `Depends on`-Zeile und keine `Files:`-Angabe geändert.
- **Gegenprobe** (zusätzlicher, rein lesender Lauf, nur zur Ursachenbelegung): identische Teilpläne mit auf die Gruppe projizierten `dependencies` (`dataclasses.replace`, gruppenfremde Vorbedingungen entfernt) ⇒ `PG-A errors: []`, `PG-B errors: []`, Overlap-Dicts unverändert `{'safe': ['task-4', 'task-5'], 'conflict': []}` bzw. `{'safe': ['task-11', 'task-12'], 'conflict': []}`. Die 8 Deadlock-Meldungen stammen damit nachweislich aus der Teilplan-Projektion, nicht aus dem Plan-Graph.
- Parse-Reihenfolge: `task-18` wird als letzter Block gelesen (Dokumentzeile ab 649), konsistent mit seinen Vorbedingungen 15, 16, 17, 19, 20, 21, 22. IDs bleiben `task-1` … `task-22` lückenlos, keine Doppel-ID.

#### Lauf 2 — Approval-Gate

`python3 scripts/sync.py --validate-spec-plan` ⇒ `exit=1`:

```
  >>>  docs/plans/2026-10-24-tmp-sink-injection-plan.md
  [ERR] [spec_plan_approval_marker] spec 'docs/specs/2026-10-24-tmp-sink-injection-spec.md' is not APPROVED although the plan has tasks
      -> approve the spec ('Status: APPROVED') before scheduling plan tasks

----------------------------------------------------------------
  [FAIL]  1 error(s) found  (1 total findings)
```

- Erwartung „genau ein ERROR `spec_plan_approval_marker`, 0 WARNINGS" **bestätigt**: 1 ERROR, 0 WARNINGs, 1 Finding, Exit 1 — Gate greift, kein Defekt.
- Die vorangestellte Zeile `! active-set.gate-dropped: 'se-component-requirements' dropped by group 'se' (requires systems-engineering.enabled to be enabled)` ist eine Config-Loader-Logzeile vor dem Bericht und **kein** Finding dieses Plans.

**Fazit Rev. 3:** Der Plan-Graph reagiert wie erwartet (vollständiger 22-Task-Graph sauber; PG-A/PG-B datei-overlap-frei, die gruppenbezogenen Deadlock-Meldungen sind reine Artefakte der Teilplan-Prüfung) und das Approval-Gate blockiert wie spezifiziert mit genau einem ERROR. Die Zählung wird gestützt: **41 ACs** (AC-01 … AC-41, lückenlos, in Plan und Spec) und **22 Tasks**.

## Gate-Status

- **Spec:** APPROVED (2026-10-24), Revision 3, `spec-id: SPEC-tmp-sink-injection`; **dieser Plan:** APPROVED (2026-10-24).
- **Erwartete Validator-Ausgabe:** `python3 scripts/sync.py --validate-spec-plan` meldet **0 Findings, Exit 0** — die Spec ist `APPROVED (2026-10-24)`, damit greift `_check_approval_markers` (`scripts/lib/consistency/spec_plan.py:479-507`) nicht mehr. Das Gate-Verhalten vor der Freigabe (**genau ein** ERROR `spec_plan_approval_marker` für `docs/plans/2026-10-24-tmp-sink-injection-plan.md`) belegt der synthetische Fixture-Test aus Task 18. Alle übrigen Prüfungen (Pflichtabschnitte, Platzhalter, Traceability, Ledger-Format, Plan-Graph) müssen ohne Befund bleiben.
- **Plan-Graph:** `validate_plan` läuft für Plandokumente als `kind="sequential"`; geprüft werden Duplikate, Dangling-Dependencies und Zyklen (keine Datei-Overlap-Prüfung, weil Ownership-Konflikte nur in `parallel_group`-Fanouts gelten).
- **Freigabe:** erteilt am 2026-10-24. Alle Nutzerfragen der Spec sind entschieden: Q1/Q2/Q4/Q5/Q7/Q8/Q9 in Revision 2; Q3 (Toolchain-Cache-Opt-in, Task 19/AC-38), Q6 (Allowlist-Schema, Task 22/AC-39), Q10 (Antigravity `FilePath` → `file_path`, Task 20/AC-40) und Q11 (§5.5-Verweis auf `PYTEST_BASETEMP`, Task 21/AC-41) in Revision 3. Keine offene Frage mehr.
- **Nicht Teil dieses Plans:** Worktree-Isolation und Migration bestehender `.tmp`-Inhalte.

### Abschluss-Gate (Task 18), Beobachtungen (2026-10-25)

**Step 2 — Grün-Lauf (beides Exit 0):**

```
$ python3 -m pytest tests/test_spec_plan_validate_cli.py -q
.......                                                                  [100%]
7 passed in 0.49s
```

```
$ python3 scripts/sync.py --validate
0 action(s)  |  382 skipped  |  2 warning(s)
```

- `--validate` Exit 0, **`temp-literal.*` = 0** (kein neues Finding, kein neues ERROR).
- Die 2 WARNINGs sind vorbestehend und liegen außerhalb dieses Plans: `active-set.gate-dropped: 'se-component-requirements' …` (Config-Loader) und der fehlgeschlagene Checkout `3d8bde25…` in `external/awesome-claude-code` (Submodul-Zustand, kein Plan-Artefakt).

**Step 3 — Gate-Beobachtung, wörtlich.**

Lauf A (Arbeitsbaum enthält zu diesem Zeitpunkt nur `tests/test_spec_plan_validate_cli.py`; die Plan-/Ledger-Datei ist unverändert, `scan.changed-files-only: true` nimmt sie daher nicht in den Scope) ⇒ **Exit 0**:

```
  !  active-set.gate-dropped: 'se-component-requirements' dropped by group 'se' (requires systems-engineering.enabled to be enabled)
  i  auto-detected config: .meta-config/project.yaml

  i  validate-spec-plan: no spec/plan-workflow findings — nothing to check (exit 0)
```

Lauf B (nach der Plan-Bearbeitung; der Plan ist jetzt im Scope) ⇒ **Exit 0** — dieselbe Ausgabe wie Lauf A, deshalb hier nur der Scope-Nachweis, der belegt, dass tatsächlich geprüft wurde (die Meldung „nothing to check" erscheint auch für „gescannt und sauber"):

```
changed: ['docs/plans/2026-10-24-tmp-sink-injection-plan.md', 'tests/test_spec_plan_validate_cli.py']
artifacts in scope: [('2026-10-24-tmp-sink-injection-plan.md', 'plan')]
findings: 0 []
```

- Der Plan ist das **einzige** Artefakt im Scope; `_check_required_sections`, `_check_placeholders`, `_check_traceability`, `_check_approval_markers`, `_check_ledger_format`, `_check_ledger_drift` und `_check_plan_graph` liefern zusammen `[]`. `_parse_plan_tasks` liest **22 Tasks, 22 unique** (keine Doppel-ID, kein Cycle).


**Full-Suite-Gate — damals ROT (historischer Befund, überholt am 2026-10-25).**

- Lauf 1 (ein Prozess): `/usr/bin/python3 -m pytest tests -q` — nach 2 400 s (Tool-Zeitlimit) bei **17 %** abgebrochen (≈ 1 290 von 6 569 Tests), bis dahin 0 Failures. Kein Exit-Code, weil der Prozess beendet wurde.
- Lauf 2 (vollständige Abdeckung, dateiweise, 8-fach parallel): **alle 361 Testdateien** ausgeführt, 6 569 Tests: **6 555 passed, 13 skipped, 1 failed** (Summe der Einzel-Laufzeiten 9 300 s; ein einzelner Prozess wäre nach dieser Messung ≈ 100–155 min lang, deshalb die Aufteilung).
- Einziger Failure, wörtlich:

```
=================================== FAILURES ===================================
________________________ test_line_duplication_ratchet _________________________
>       assert len(duplicates) <= MAX_DUPLICATE_LINES, (
            f"duplicate source lines grew: {len(duplicates)} > {MAX_DUPLICATE_LINES} ({hint})"
        )
E       AssertionError: duplicate source lines grew: 17 > 16 (61x '**Project context:** {{PROJECT_CONTEXT}}'; 10x 'On `correction_hints` from a critic → fix ONLY the named fin'; 10x 'RESULT: <1 Satz Ergebnis-Zusammenfassung>'; 10x 'ARTIFACTS: <persistierte Step-/Report-Dateien (siehe Step Pe'; 8x '**Worker role:** Never re-delegate to `orchestrator`.')
E       assert 17 <= 16
FAILED tests/test_template_line_duplication.py::test_line_duplication_ratchet
1 failed, 3 passed in 0.29s
```

- Ursache (messbar, nicht spekulativ): Die Ratchet zählt Zeilen ≥ 40 Zeichen in ≥ 5 Dateien unter `agents/1-generic`, `agents/2-platform`, `rules/**`, `commands/**`. Gegen `merge-base` `14c0ad14` = **16 Zeilen / 165 Vorkommen** (identisch mit den Ceilings `MAX_DUPLICATE_LINES=16`, `MAX_DUPLICATE_OCCURRENCES=165`), an `HEAD` `f86abb2f` = **17 Zeilen / 172 Vorkommen**. Neu ist `2. Rename the file from the sink to the target path (atomic write)` in 7 `se-*`-Templates (`se-termination`, `se-developer`, `se-verifier`, `se-validator`, `se-junior-developer`, `se-interface-mgr`, `se-integration-and-test-manager`) — entstanden durch die Temp-Literal-Ersetzung (Task 5/6/21): die vormals unterschiedlichen Pfadangaben sind jetzt wortgleich.
- **Kein Test-only-Bypass, keine Abschwächung:** Die Datei `tests/test_template_line_duplication.py` liegt nicht im Task-18-Files-Scope; eine Anhebung der Ceilings ohne strukturell zwingenden Grund wäre genau die Abschwächung, die der Ratchet-Kommentar verbietet. Der Befund geht als Blocker an den Orchestrator (Fix-Optionen: Snippet/Umformulierung in den 7 `se-*`-Templates, oder dokumentierte, vom Nutzer entschiedene Ratchet-Anhebung).
- **Gate-Beobachtung zur Statusdatei (Lauf C):** Sobald der Ledger selbst geändert ist, nimmt `scan.changed-files-only: true` ihn in den Scope und `_classify` behandelt `docs/plans/2026-10-24-tmp-sink-injection-status.md` als `plan` (Muster `YYYY-MM-DD-*.md`). Ergebnis: **Exit 1, 1 ERROR + 7 WARNINGs** — 1× `spec_plan_no_placeholder` (`'...'` in historischen Evidence-Blöcken), 6× `spec_plan_required_sections`, 1× `spec_plan_traceability` (Backtick-/Klammerzusatz im `**Spec:**`-Kopf wird als Pfad gelesen). Nachdem dieser Bericht wörtlich in den Ledger geschrieben war, meldete der Folgelauf nur noch **Exit 1, 1 ERROR + 1 WARNING**, weil `_check_required_sections` nur Substrings prüft und der zitierte Bericht die Abschnittsnamen selbst enthält (selbstreferenzieller Artefakt, kein inhaltlicher Fix; beide Läufe wörtlich im Ledger). Kein In-Scope-Fix ohne Verfälschung historischer Evidenz bzw. ohne Produktionsänderung an `spec_plan.py`; die Findings stehen wörtlich im Ledger (`## Evidence — Task 18`, Lauf C).
- **Kein Approval-Marker** ergänzt: Spec und Plan bleiben unverändert `APPROVED (2026-10-24)`; das Gate-Verhalten vor der Freigabe belegt ausschließlich der synthetische Test `test_unapproved_spec_yields_exactly_one_approval_error`.

### Abschluss-Gate (Task 18) — finale Verifikation (2026-10-25)

Der vorstehende Befund „Full-Suite-Gate — ROT“ ist der **historische Erstlauf-Stand** und bleibt als
Evidenz stehen; er ist **überholt**. Maßgeblich ist der Nachlauf auf `fix/tmp-sink-injection`
(HEAD `f86abb2f` plus Arbeitsbaum), der die Gates erneut ausgeführt hat:

| Kommando | Ergebnis | Exit |
|---|---|---|
| `python3 scripts/sync.py --validate` | `0 action(s)  \|  382 skipped  \|  2 warning(s)`, **0** Treffer `temp-literal.*` | 0 |
| `python3 scripts/sync.py --validate-spec-plan` | **0 Findings** — `no spec/plan-workflow findings — nothing to check` | 0 |
| `python3 -m pytest tests/test_spec_plan_validate_cli.py tests/test_template_line_duplication.py -q` | `11 passed` (7 + 4) | 0 |

Zusätzlich geprüft: `python3 scripts/sync.py --render-standalone --check` ⇒
`OK standalone/ is up to date (91 file(s))`, Exit 0 (nur die zwei vorbestehenden `OUTPUT_GUARD_BLOCK`-Notizen,
kein Drift); `tests/test_ac01_render_identity.py` ⇒ `5 passed`, `tests/fixtures/ac01-baseline/hashes.json`
ohne Diff. Die 2 `--validate`-WARNINGs sind vorbestehend und plan-extern (`active-set.gate-dropped` aus dem
Config-Loader, fehlgeschlagener `external/awesome-claude-code`-Checkout).

**Ratchet (unabhängig nachgemessen, nicht nur „Test grün“):** `_duplicate_lines()` über 182
gescannte Quelldateien ⇒ **16 distinkte Zeilen / 165 Vorkommen**; die Ceilings `MAX_DUPLICATE_LINES=16`
und `MAX_DUPLICATE_OCCURRENCES=165` wurden **nicht** angehoben. Die 7 `se-*`-Schritt-2-Zeilen nennen jetzt je
ihr eigenes Zwischenartefakt (Nachweis: `## Blocker-Auflösung (2026-10-25)` in
`docs/plans/2026-10-24-tmp-sink-injection-status.md`).

**Full-Suite (im Task-18-Lauf gemessen, in diesem Nachlauf nicht erneut):** 361/361 Testdateien,
6 569 gesammelte Tests ⇒ **6 555 passed, 13 skipped, 1 failed**. Der einzige Failure war
`tests/test_template_line_duplication.py::test_line_duplication_ratchet` (17 > 16) und ist durch den
Ratchet-Fix behoben — in der Einzelverifikation oben grün. **Einschränkung, ehrlich benannt:** die Suite
wurde als dateiweiser Sweep (8-fach parallel) gemessen, **nicht** als einzelner Prozess; ein
Einzelprozess-Lauf traf nach 2 400 s das Tool-Zeitlimit (Abbruch bei 17 %, bis dahin 0 Failures).

**Kein Approval-Marker ergänzt:** Spec und Plan bleiben `APPROVED (2026-10-24)`; das Vor-Freigabe-Verhalten
belegt ausschließlich der synthetische Fixture-Test `test_unapproved_spec_yields_exactly_one_approval_error`.

Die frühere Task-18-Statuszeile `partial (Gate rot)` in der Statusdatei ist damit **überholt** und steht
jetzt auf `done` mit `Commit = — (pending)`.
