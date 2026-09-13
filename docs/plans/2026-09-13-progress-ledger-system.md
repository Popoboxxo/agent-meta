---
pipeline_stages:
  implement: 1
---

# Progress / Ledger System Implementation Plan

> Status: geplant

**Goal:** Die vorhandene, aber unverdrahtete Fortschritts-Infrastruktur (Plan-Checkbox-Ledger + `CheckpointStore`) zu einem einen, über Sessions hinweg wiederaufsetzbaren Progress-/Ledger-Loop verdrahten — stabile Identität (`plan_id`/`task_ref`), echter Resume-Pfad, maschineller Ledger-Writer mit Drift-Check, zweistufiges Task-Review mit Runden-Cap und ein Root-Cause-Pflicht-Gate — ohne ein paralleles Format zu erfinden.
**Architecture:** Keine neue Persistenz. `plan_identity` liefert den gemeinsamen Schlüssel für Parser, Writer, Checkpoint-Writer und Validator. `recovery` ist der dokumentierte read-only Caller der bestehenden `CheckpointStore`-Loader; `rehydrate` ist sein CLI-Modus. `plan_ledger` schreibt die Checkboxen exakt nach der Semantik von `consistency.spec_plan.parse_plan_ledger`; `checkpoint_record` ist der stehende Produktions-Writer für Checkpoints. `execute_plan` (IC-06) hängt sich als automatischer Per-Task-Writer in denselben Store. G-09/G-10 werden ausschließlich deklarativ über `config/role-defaults.yaml` (`reflection_pairs` + Pipeline-Stages) und DoD-Flags ausgedrückt — kein Rollen-Literal in `agents/1-generic/*` oder `rules/1-generic/*`.
**Tech Stack:** Python 3.9 (Stdlib only, `from __future__ import annotations`, keine PEP-604-Union-Annotationen in neuen Modulen), YAML/Markdown-Konfiguration (`config/`), pytest, Bash-Szenario-Harness (`tests/scenarios/run.sh`).
**Spec:** `docs/specs/2026-09-13-progress-ledger-system-design.md` (Trace-Anker `spec-id: SPEC-PROGRESS-LEDGER-2026-09-13`, Gap-Quelle G-02/G-03/G-04/G-09/G-10).

## Global Constraints

- **Verdrahten statt erfinden:** `CheckpointStore`, `execute_plan`/`checkpoint_ref`, `spec_plan.parse_plan_ledger`, `spec_plan`-Validator, `quality_pipelines`/`reflection_pairs`, `resolve_spec_plan_bundle` werden genutzt und erweitert. Kein zweites Ledger-/Recovery-Format, keine zweite ID-Vergabe.
- **Keine Rollen-Routen in Templates:** `agents/1-generic/*` und `rules/1-generic/*` erhalten keine Route-Tabellen, keine `roleA → roleB`-Ketten, keine Handoff-Sätze mit Rollen und keine Rollen in `NEXT:`-Blöcken. `tests/test_no_role_routes_in_templates.py` (AC-26) muss unverändert grün bleiben. Reviews/Routing nur über `quality_pipelines`/`reflection_pairs`.
- **Identität ist explizit, nie zufällig:** `plan_id`/`task_ref` in Checkpoints leiten sich ausschließlich aus explizitem `plan_id` (Argument bzw. `--plan-id`/`--plan`) ab. Die `KIND-<uuid>`-Fallback von `BarrierResult.plan_id` wird niemals in einen Checkpoint kopiert (F1).
- **Gruppierungs-Mechanik synchron an 4 Stellen:** neue Aspect `recovery-rehydrate` in `config/spec-plan-groups.yaml` **nach `consistency-noop`, vor `ke-auto-index`**; identische Position in `scripts/lib/dod.py::_SPEC_PLAN_FALLBACK_ASPECTS` und in `tests/test_spec_plan_group_consistency.py` (Nachtrag in `SEED_EQUAL_ASPECTS` speist `ALL_ASPECTS`). Mechanism-Enum unverändert (`pipeline-stage-condition` existiert).
- **Provider-Agnostik & Portabilität:** kein `if provider == "…"`, kein Provider-Literal in neuen/geänderten Modulen; keine externen Python-Dependencies; Py3.9-kompatibel; keine PEP-604-Annotationen in neuen Modulen.
- **Namens-Verbot:** kein externer Modellname in Code, Doku, Kommentaren, Commit-Messages oder diesem Plan.
- **Bite-sized & TDD:** jede Task ist einzeln testbar und committbar (Test fail → implementieren → Test pass → Commit). Ein Task ist erst done, wenn der Test tatsächlich beobachtet wurde.
- **Mutationen nur im Projektroot:** `--update-plan-ledger`/`--checkpoint` schreiben ausschließlich im Projektroot (Checkpoints unter `.meta-viz/`); `--rehydrate` und der Drift-Check sind read-only.
- **Geteilte Dateien = sequentiell:** Mehrere Tasks legen bewusst dieselbe Datei an (`scripts/sync.py` in Task 6/9/10, `scripts/lib/consistency/spec_plan.py` in Task 4/5, `scripts/lib/orchestration.py` in Task 3/7, `config/role-defaults.yaml` in Task 11/12). `Depends on` macht sie strikt sequentiell; nur ownership-disjunkte Tasks laufen parallel. Der statische `check_plan_file_overlap`-Befund ist für abhängige Tasks Barrieren-Input, keine Parallelisierungsfreigabe.
- **Bestehende Verträge nicht brechen:** Signaturen/Verhalten von `save_checkpoint`, `load_session`, `get_last_checkpoint`, `get_completed_steps`, `list_sessions`, `delete_session`, `cleanup_old_sessions`, `save_raw_output`, `render_barrier_result`, Status-Aggregation und `BarrierResult.plan_id`-Fallback bleiben unverändert.

## File Structure

### Neue Dateien

- Create: `scripts/lib/plan_identity.py` — Leaf-Modul: `PLAN_ID_RE`, `TASK_ID_RE`, `TASK_HEADER_RE`, `derive_plan_id`, `normalize_task_id`, `make_task_ref`. Gemeinsamer Schlüssel für Parser/Writer/Checkpoint/Validator (IC-01).
- Create: `scripts/lib/recovery.py` — read-only Recovery-Resolver: Legacy- und Store-Quellen zusammenführen, resumierbare Session finden, Resume-Kontext bauen/rendern (IC-03, G-02).
- Create: `scripts/lib/rehydrate.py` — CLI-Modus `--rehydrate` (read-only, kein Write) über `recovery.py` (IC-04).
- Create: `scripts/lib/plan_ledger.py` — Ledger-Writer (Checkboxen + erstes `Status:`) nach `parse_plan_ledger`-Semantik, `handle_update_plan_ledger` für `--update-plan-ledger` (IC-05, G-04).
- Create: `scripts/lib/checkpoint_record.py` — stehender Produktions-Writer für Checkpoints (`--checkpoint`, ohne G-08-Dispatcher) (IC-11).
- Create: `rules/1-generic/session-recovery.md` — Session-Start liest einen Resume-Kontext, bevor neue Plan-Arbeit beginnt; offener Task wird an `next_task_ref` fortgesetzt (IC-09/IC-10).
- Create: `rules/1-generic/root-cause-gate.md` — vor jedem Fix werden Ursache und Vorversuche belegt; Symptom-Fix erfüllt das Gate nicht (IC-09/IC-10).

### Geänderte Dateien

- Modify: `scripts/lib/checkpoint.py` — `Checkpoint.plan_id`/`task_ref`, `to_dict`/`from_dict`, `CheckpointStore.get_checkpoint_for_task`, `CheckpointStore.find_sessions_for_plan` (IC-02).
- Modify: `scripts/lib/orchestration.py` — `execute_plan` schreibt Per-Entry-Checkpoints und schließt optional den Ledger; `checkpoint_from_barrier_entry` (IC-06).
- Modify: `scripts/lib/consistency/spec_plan.py` — hyphen-aware `TASK_HEADER_RE`, Delegation `_normalize_task_id`, `parse_task_ledgers`, `_check_ledger_drift` (IC-07).
- Modify: `scripts/lib/pipelines.py` — `_validate_task_review_rounds`, aufgerufen aus `validate_pipelines` (IC-08).
- Modify: `scripts/lib/dod.py` — Fallback-Aspect `recovery-rehydrate` an fixierter Position (IC-09).
- Modify: `scripts/lib/rules.py` — `_rule_gate_satisfied`-Branch für `dod.root-cause-required` (IC-09).
- Modify: `scripts/sync.py` — Flags `--rehydrate`, `--checkpoint` (+ dessen Argumente), `--update-plan-ledger` (+ `--task`/`--open`/`--status`), Handler-Registrierung in `_MODE_HANDLERS` (IC-04/IC-05/IC-11).
- Modify: `config/spec-plan-groups.yaml` — Aspect `recovery-rehydrate` nach `consistency-noop`, vor `ke-auto-index` (IC-09).
- Modify: `config/role-defaults.yaml` — `reflection_pairs` `task-req-review-loop`/`task-quality-review-loop`; `concept-driven-dev` Stages `review-req`/`review-quality` + `task-review.max-rounds: 4`; `bugfix` Stage `root-cause`; `quick-fix` konditionale Stage `root-cause` (IC-08).
- Modify: `config/dod-presets.yaml` — `root-cause-required` in jedem Preset (IC-09).
- Modify: `config/rules-presets.yaml` — `rule-gates` `session-recovery` und `root-cause-gate` (IC-09).
- Modify: `config/project-config.schema.json` — `spec-plan-workflow.recovery`, `spec-plan-workflow.ledger-drift`, `dod.root-cause-required`, `stageItem.condition.dod_flag/payload_flag`, `pipelineDefinition.task-review` (IC-09).
- Modify: `rules/1-generic/plan-ledger.md` — zweistufiger Review + Writer-Pflicht; `execute_plan`-out-of-scope-Aussage durch IC-06-Verdrahtung ersetzen (IC-10).
- Modify: `snippets/orchestrator/checkpointing.md` — Session-Start-Prosa auf rehydrate-Pfad, Store als autoritative Quelle, 24h-Auto-Delete-Versprechen entfernen, Tier-A/-B-Tokens erhalten (IC-10).
- Modify: `tests/test_spec_plan_group_consistency.py` — `recovery-rehydrate` in `SEED_EQUAL_ASPECTS` (IC-09).
- Modify: `tests/test_orchestration_contract.py` — `test_concept_driven_dev_spec_plan_phase_order` auf 10 Stages (IC-08, AC-32).
- Modify: `tests/scenarios/registry.md` — Zeile `59-progress-ledger` (AC-28).

### Neue Test-/Szenario-Dateien

- Create: `tests/test_plan_identity.py` — AC-01/02/03.
- Create: `tests/test_checkpoint_plan_identity.py` — AC-04/05/06.
- Create: `tests/test_plan_ledger_writer.py` — AC-07/08/09/10.
- Create: `tests/test_recovery.py` — AC-17/18/19 + M4.
- Create: `tests/test_rehydrate_cli.py` — AC-20.
- Create: `tests/test_checkpoint_cli.py` — AC-33 + M1/M3.
- Create: `tests/test_progress_ledger_conventions.py` — AC-29/30 (Py3.9-Syntax, Provider-Agnostik).
- Create: `tests/scenarios/configs/59-progress-ledger.project.yaml` — Szenario-Config (AC-28).
- Create: `tests/scenarios/asserts/59-progress-ledger.sh` — Content-Assertions (AC-28).
- Modify: `tests/test_spec_plan_consistency.py` — Drift-/Parser-Fälle (AC-15/16/34).
- Modify: `tests/test_spec_plan_config_schema.py` — Schema-Fälle (AC-25).
- Modify: `tests/test_pipelines.py` — `_validate_task_review_rounds` (AC-22).

### Step-Agent-Map (plan-driven `implement`)

| Step | Task | Agent |
|------|------|-------|
| 1 | plan_identity | developer |
| 2 | checkpoint schema | developer |
| 3 | execute_plan checkpoints | developer |
| 4 | spec_plan parser | developer |
| 5 | ledger drift | senior-developer |
| 6 | plan_ledger writer + CLI | developer |
| 7 | execute_plan ledger close-out | developer |
| 8 | recovery resolver | senior-developer |
| 9 | rehydrate CLI | developer |
| 10 | checkpoint CLI | developer |
| 11 | task review + round cap | developer |
| 12 | root-cause pipeline stages | developer |
| 13 | DoD flag + rule gates | developer |
| 14 | config schema | developer |
| 15 | grouping aspect | developer |
| 16 | rule/snippet docs | developer |
| 17 | scenario 59 | developer |
| 18 | convention ratchet | developer |

---

### Task 1: plan_identity Basis-Modul

**Files:**
- Create: `scripts/lib/plan_identity.py` — Identitäts-Primitive (Leaf, nur `pathlib`, `re`, `typing`).
- Test: `tests/test_plan_identity.py`.

**Interfaces:** (Produces / Consumes)
- Produces: `PLAN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")`; `TASK_ID_RE = re.compile(r"^task-[0-9]+$")`; `TASK_HEADER_RE` (Gruppe 1 = rohe Task-ID inkl. `-._`, Gruppe 2 = Titel, ein Treffer pro Zeile); `derive_plan_id(plan_path: Path, text: Optional[str] = None) -> str`; `normalize_task_id(raw: str) -> str`; `make_task_ref(plan_id: Optional[str], task_id: str) -> Optional[str]`.
- Consumes: nur Stdlib.

**Depends on:** —

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_plan_identity.py::test_header_regex_hyphen_and_numeric`, `::test_derive_plan_id_explicit_and_slug`, `::test_derive_plan_id_never_raises_on_missing_file`, `::test_normalize_task_id`, `::test_make_task_ref_none_and_existing_hash`.
- [ ] Step 2: Implementieren — exakt die IC-01-Signaturen; `derive_plan_id`-Präzedenz: explizites `plan-id:`-Feld (Frontmatter/`> plan-id:`) wenn `PLAN_ID_RE`; sonst deterministischer Slug aus `plan_path.stem` (`[^a-z0-9]+` → `-`, trim, lowercase); `OSError`/fehlende Datei → Stem-Slug; nie Random/Timestamp. `make_task_ref` gibt `None` bei falschem `plan_id`, `task_id` mit `#` unverändert, sonst `f"{plan_id}#{task_id}"`.
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_plan_identity.py -q`.
- [ ] Step 4: Commit — `feat: add plan identity primitives for progress ledger`.

**Acceptance:** AC-01, AC-02, AC-03.

---

### Task 2: Checkpoint-Schema und Query-Helfer

**Files:**
- Modify: `scripts/lib/checkpoint.py`.
- Test: `tests/test_checkpoint_plan_identity.py`.

**Interfaces:** (Produces / Consumes)
- Produces: `Checkpoint.__init__(..., plan_id: Optional[str] = None, task_ref: Optional[str] = None)`; `to_dict()` mit `"plan_id"`/`"task_ref"`; `from_dict(data)` liest `plan_id` und `task_ref or make_task_ref(plan_id, data["task_id"])` (vier Pflichtfelder unverändert hart); `CheckpointStore.get_checkpoint_for_task(session_id, task_ref) -> Optional[Checkpoint]`; `CheckpointStore.find_sessions_for_plan(plan_id) -> List[str]` (neueste `updated_at` zuerst, korrupte Dateien überspringen).
- Consumes: `plan_identity.make_task_ref`.

**Depends on:** 1

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `test_checkpoint_plan_identity.py::test_from_dict_legacy_without_new_keys`, `::test_from_dict_backfills_task_ref`, `::test_round_trip_serializes_plan_fields`, `::test_get_checkpoint_for_task_hit_miss_and_backcompat`, `::test_find_sessions_for_plan_skips_corrupt_file`.
- [ ] Step 2: Implementieren — optionale Felder dürfen nichts mandatory machen; Loader bleiben fail-soft (`None`/`[]` bei fehlender/korrupter Session). Backward-Compat-Pfad: `plan_id` + `task_id` rekonstruiert denselben Ref.
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_checkpoint_plan_identity.py tests/test_plan_ledger.py tests/test_persistence_atomicity.py -q`.
- [ ] Step 4: Commit — `feat: attach plan identity to checkpoints`.

**Acceptance:** AC-04, AC-05, AC-06.

---

### Task 3: execute_plan schreibt Per-Entry-Checkpoints

**Files:**
- Modify: `scripts/lib/orchestration.py`.
- Test: `tests/test_orchestration_contract.py`.

**Interfaces:** (Produces / Consumes)
- Produces: `execute_plan(plan, dispatcher, *, store=None, session_id=None, plan_id=None, write_checkpoints: bool = True) -> BarrierResult`; `checkpoint_from_barrier_entry(entry: BarrierEntry, *, plan_id: Optional[str] = None, task_description: str = "") -> Checkpoint`.
- Consumes: `CheckpointStore.save_checkpoint`, `Checkpoint`, `plan_identity.make_task_ref`, bestehende Raw-Output-Archivierung.

**Depends on:** 1, 2

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `test_orchestration_contract.py::test_execute_writes_plan_identity_checkpoints`, `::test_execute_write_checkpoints_false_is_legacy`, `::test_execute_without_plan_id_writes_null_identity`, `::test_checkpoint_write_oserror_is_fail_soft`.
- [ ] Step 2: Implementieren — Status-Mapping `success→"completed"`, `failed→"failed"`, `timeout→"timeout"`; `agent = entry.agent`; `task_description` aus passendem `FanoutTask.prompt` (Fallback `entry.task_id`); `status_summary = entry.summary`. Identität nur aus explizitem `plan_id` (F1): `task_ref = make_task_ref(plan_id, entry.task_id)`, bei `None` beide `None`. `BarrierResult.plan_id`-Fallback (`plan_id or f"{plan.kind.upper()}-<uuid>"`) unverändert; `OSError` loggen, Status nicht ändern. `write_checkpoints=False` = Altverhalten.
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_orchestration_contract.py -q`.
- [ ] Step 4: Commit — `feat: write per-entry checkpoints from execute_plan`.

**Acceptance:** AC-11, AC-12, AC-13.

---

### Task 4: hyphen-aware Task-Parser und parse_task_ledgers

**Files:**
- Modify: `scripts/lib/consistency/spec_plan.py`.
- Test: `tests/test_spec_plan_consistency.py`.

**Interfaces:** (Produces / Consumes)
- Produces: `_TASK_HEADER_RE` als Alias von `plan_identity.TASK_HEADER_RE`; `_normalize_task_id` delegiert an `plan_identity.normalize_task_id`; `parse_task_ledgers(plan_path: Path) -> dict` mit `{"<task-id>": {"total": int, "checked": int, "complete": bool, "start": int, "end": int}}`.
- Consumes: `plan_identity.TASK_HEADER_RE`, `plan_identity.normalize_task_id`.

**Depends on:** 1

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `test_spec_plan_consistency.py::test_parse_plan_tasks_hyphen_header`, `::test_parse_task_ledgers_counts_and_offsets`, `::test_parse_task_ledgers_normalizes_ids`.
- [ ] Step 2: Implementieren — Dokument an `TASK_HEADER_RE` splitten; nur führende `^- \[( |x|X)\]`-Zeilen im Block zählen; IDs normalisieren. Bestehende `_parse_plan_tasks`/`_check_plan_graph`-Semantik erhalten (parst jetzt korrekt `task-<n>`-Header).
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_spec_plan_consistency.py tests/test_orchestration_contract.py -q`.
- [ ] Step 4: Commit — `feat: parse hyphenated plan task headers`.

**Acceptance:** AC-01 (Integrationspfad), Vorbereitung AC-15/AC-16.

---

### Task 5: Ledger-Drift-Check mit changed-files-Scope

**Files:**
- Modify: `scripts/lib/consistency/spec_plan.py`.
- Test: `tests/test_spec_plan_consistency.py`, `tests/test_spec_plan_validate_cli.py`.

**Interfaces:** (Produces / Consumes)
- Produces: `_check_ledger_drift(project_root: Path, plans: List[Path], texts: Dict[Path, str], findings: List[Finding]) -> None`, aufgerufen nach `_check_ledger_format`. Finding-Code `spec_plan_ledger_drift`; Severity aus `spec-plan-workflow.ledger-drift.severity` (Default `WARNING`); Check wird übersprungen, wenn `ledger-drift.enabled is False` (M2).
- Consumes: `parse_task_ledgers`, `plan_identity.derive_plan_id`, `CheckpointStore.find_sessions_for_plan`, `CheckpointStore.get_completed_steps`, `check_spec_plan_workflow`-`changed_files`.

**Depends on:** 2, 4

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `test_spec_plan_consistency.py::test_drift_ledger_ahead_of_checkpoints`, `::test_drift_checkpoint_ahead_of_ledger`, `::test_drift_status_complete_but_ledger_open`, `::test_drift_skipped_without_sessions`, `::test_drift_disabled_flag_suppresses_finding`, `::test_drift_severity_override`; CLI `test_spec_plan_validate_cli.py::test_drift_finding_sets_exit_1`.
- [ ] Step 2: Implementieren — driften nur, wenn `consistency-noop` aktiv (bestehender Early-Return); Sitzungen nur über `find_sessions_for_plan(derive_plan_id(plan))`; keine Treffer → keine Findings. Sichtbarkeit erbt `changed_files`-Filter der `_collect_artifacts`-Pipeline (F4) — kein Force-Include.
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_spec_plan_consistency.py tests/test_spec_plan_validate_cli.py -q`.
- [ ] Step 4: Commit — `feat: detect plan ledger drift against checkpoints`.

**Acceptance:** AC-15, AC-16, AC-34, M2.

---

### Task 6: Ledger-Writer und --update-plan-ledger

**Files:**
- Create: `scripts/lib/plan_ledger.py`.
- Modify: `scripts/sync.py`.
- Test: `tests/test_plan_ledger_writer.py`, `tests/test_plan_ledger.py`.

**Interfaces:** (Produces / Consumes)
- Produces: `MODE = "update-plan-ledger"`; `LedgerWriteResult(plan_path, ok, reason, tasks_updated, checkboxes_toggled, unmatched, status, dry_run)`; `update_plan_ledger(plan_path: Path, updates: Mapping[str, bool], *, status: Optional[str] = None, dry_run: bool = False) -> LedgerWriteResult`; `set_plan_status(plan_path: Path, status: str, *, dry_run: bool = False) -> LedgerWriteResult`; `handle_update_plan_ledger(ctx) -> None`.
- Consumes: `plan_identity.TASK_HEADER_RE`, `plan_identity.normalize_task_id`, `io.write_atomic`, `consistency.spec_plan.parse_plan_ledger`.
- CLI (neu in `sync.py`): `--update-plan-ledger <plan>`, `--task <id>` (nargs `*`), `--open`, `--status <s>`, plus global `--dry-run`.

**Depends on:** 1

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `test_plan_ledger_writer.py::test_toggle_task_on_matches_parser`, `::test_toggle_task_off_and_others_untouched`, `::test_all_closed_parser_complete_true`, `::test_status_written_and_read_back`, `::test_missing_plan_reason_plan_not_found`, `::test_unknown_task_in_unmatched_others_written`, `::test_no_change_no_write`; `test_plan_ledger.py` bleibt grün.
- [ ] Step 2: Implementieren — nur führende `^- \[( |x|X)\]` in genau dem per `TASK_HEADER_RE` lokalisierten Block ändern (Einrückung/Trailing-Text erhalten); erstes `Status:`-Vorkommen ersetzen, sonst `> Status: <value>` nach H1 einfügen; Doku in-memory bauen, atomar über `io.write_atomic`, kein Write ohne Änderung. Fehlerpfade `ok=False` (`plan-not-found`, `io-error:<ClassName>`), nie raise. Handler druckt Result und beendet `0` bei `ok` ohne `unmatched`, sonst `1`.
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_plan_ledger_writer.py tests/test_plan_ledger.py -q` und `python3 scripts/sync.py --update-plan-ledger docs/plans/2026-09-13-progress-ledger-system.md --task 1 --status "IN PROGRESS" --dry-run`.
- [ ] Step 4: Commit — `feat: add plan ledger writer and --update-plan-ledger mode`.

**Acceptance:** AC-07, AC-08, AC-09, AC-10.

---

### Task 7: execute_plan schließt den Ledger ab

**Files:**
- Modify: `scripts/lib/orchestration.py`.
- Test: `tests/test_orchestration_contract.py`.

**Interfaces:** (Produces / Consumes)
- Produces: `execute_plan(..., ledger_path: Optional[Path] = None)`; nach Aggregation: Erfolgs-Entries als done markieren, Status `complete` wenn alle Checkboxen geschlossen, sonst `IN PROGRESS`.
- Consumes: `scripts/lib/plan_ledger.py` (Lazy-Import gegen Zyklus), `BarrierEntry.status`.

**Depends on:** 3, 6

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `test_orchestration_contract.py::test_execute_with_ledger_path_closes_success_tasks`, `::test_execute_with_failing_entry_keeps_task_open`, `::test_execute_without_ledger_path_no_write`.
- [ ] Step 2: Implementieren — ausschließlich `success`-Entries togglen; `ledger_path=None` = kein Write; Ledger-Fehler fail-soft (Status/Aggregation unverändert).
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_orchestration_contract.py -q`.
- [ ] Step 4: Commit — `feat: close out the plan ledger from execute_plan`.

**Acceptance:** AC-14.

---

### Task 8: Recovery-Resolver (read-only)

**Files:**
- Create: `scripts/lib/recovery.py`.
- Test: `tests/test_recovery.py`.

**Interfaces:** (Produces / Consumes)
- Produces: `REHYDRATE_CONFIG_PATH = "spec-plan-workflow.recovery.rehydrate"`; `RecoverySource`; `ResumeContext`; `load_legacy_checkpoints(project_root: Path) -> List[RecoverySource]`; `load_store_sources(store: CheckpointStore) -> List[RecoverySource]`; `resolve_recovery_sources(project_root, *, store=None, max_age_seconds=None, include_legacy=True) -> List[RecoverySource]`; `find_resumable_session(project_root, *, store=None, max_age_seconds=None) -> Optional[RecoverySource]`; `build_resume_context(project_root, session_id, *, plan_id=None, store=None) -> Optional[ResumeContext]`; `render_resume_context(context: ResumeContext) -> str`.
- Consumes: `CheckpointStore.list_sessions/get_last_checkpoint/get_completed_steps`, `plan_identity.derive_plan_id`, `consistency.spec_plan.parse_plan_ledger`; Plans-Verzeichnis aus `spec-plan-workflow.paths.plans` (Default `docs/plans`, **M4**).

**Depends on:** 2, 4

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_recovery.py::test_legacy_checkpoint_source`, `::test_store_wins_on_duplicate_session_id`, `::test_find_resumable_skips_completed`, `::test_find_resumable_newest_first`, `::test_build_resume_context_next_task_ref`, `::test_render_contains_session_and_no_role_name`, `::test_build_resume_context_uses_configured_plans_dir` (M4).
- [ ] Step 2: Implementieren — Legacy-Reader (`session_id`, `created_at`, `task_summary`, `completed_steps`, `pending_steps`, `context`; unbekannte Keys ignorieren; malformte Dateien warnen+skippen; `plan_id=None`; Pending ohne Task-ID → `step:<n>`); Store-Reader über die drei Loader; Merge mit Store-Vorrang, Dedupe per `session_id`, Altersfilter, neueste zuerst; `find_resumable_session` liefert neueste nicht-`completed`-Quelle mit offenen Refs; Plan-Auflösung über `derive_plan_id`-Suche im konfigurierten Plans-Verzeichnis; `render_resume_context` bounded Markdown, keine Rollen-Namen, keine Dispatch-Anweisungen. Nie mutieren, nie raise für Content-Probleme.
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_recovery.py -q`.
- [ ] Step 4: Commit — `feat: add read-only recovery resolver`.

**Acceptance:** AC-17, AC-18, AC-19, M4.

---

### Task 9: --rehydrate CLI-Modus

**Files:**
- Create: `scripts/lib/rehydrate.py`.
- Modify: `scripts/sync.py`.
- Test: `tests/test_rehydrate_cli.py`.

**Interfaces:** (Produces / Consumes)
- Produces: `MODE = "rehydrate"`; `rehydrate(project_root: Path, config: Optional[dict], log: SyncLog) -> int`; `_handle_rehydrate(ctx) -> None`; Flag `--rehydrate`; Registration in `_MODE_HANDLERS` (analog `_handle_validate_spec_plan`).
- Consumes: `CheckpointStore`, `recovery.find_resumable_session/build_resume_context/render_resume_context`, `spec-plan-workflow.recovery.rehydrate`.

**Depends on:** 8

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `test_rehydrate_cli.py::test_no_unfinished_session_exit_0_with_note`, `::test_resumable_session_prints_context_exit_0`, `::test_rehydrate_disabled_prints_and_exit_0`, `::test_rehydrate_writes_no_file`.
- [ ] Step 2: Implementieren — `rehydrate: false` → "rehydrate disabled", return `0`; keine resumierbare Session → explizite "no unfinished session"-Notiz, return `0`; sonst Kontext drucken, return `0`. Read-only, kein Sync, kein Dispatch-Tail (Handler beendet direkt wie `_handle_validate_spec_plan`).
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_rehydrate_cli.py -q` und `python3 scripts/sync.py --rehydrate`.
- [ ] Step 4: Commit — `feat: add read-only --rehydrate mode`.

**Acceptance:** AC-20.

---

### Task 10: --checkpoint Produktions-Writer

**Files:**
- Create: `scripts/lib/checkpoint_record.py`.
- Modify: `scripts/sync.py`.
- Test: `tests/test_checkpoint_cli.py`.

**Interfaces:** (Produces / Consumes)
- Produces: `MODE = "checkpoint"`; `record_checkpoint(project_root, config, log, *, session_id, task_id, agent, status, task_description="", plan_id=None, status_summary=None, next_step=None) -> int`; `_handle_checkpoint(ctx) -> None`; Flags `--checkpoint`, `--session-id`, `--task`, `--agent`, `--status`, `--plan`, `--plan-id`, `--description`, `--summary`, `--next-step`.
- Consumes: `Checkpoint`, `CheckpointStore.save_checkpoint`, `plan_identity.derive_plan_id/make_task_ref/normalize_task_id`.

**Depends on:** 1, 2

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `test_checkpoint_cli.py::test_record_with_plan_id_sets_ref` (AC-33), `::test_record_with_plan_path_derives_id`, `::test_record_without_plan_is_null_identity`, `::test_missing_required_arg_exits_1_without_write` (M3), `::test_task_id_normalized_before_ref` (M1: `3` → `p#task-3`), `::test_store_oserror_exits_1`.
- [ ] Step 2: Implementieren — `plan_id = --plan-id` oder `derive_plan_id(--plan)` oder `None` (nie random); `task_ref = make_task_ref(plan_id, normalize_task_id(task_id))` (**M1**); Pflichtargumente manuell validieren (nicht argparse-required), fehlend → Meldung + `1`, kein Write (**M3**); schreibt nur via Store unter `.meta-viz/`; `OSError` → `1`. `--status` akzeptiert `completed|failed|timeout|in_progress`.
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_checkpoint_cli.py -q` und `python3 scripts/sync.py --checkpoint --session-id S --task task-1 --agent developer --status completed --plan-id p`.
- [ ] Step 4: Commit — `feat: add --checkpoint production writer`.

**Acceptance:** AC-33, M1, M3.

---

### Task 11: Zweistufiger Task-Review mit Runden-Cap (G-09)

**Files:**
- Modify: `config/role-defaults.yaml`.
- Modify: `scripts/lib/pipelines.py`.
- Test: `tests/test_pipelines.py`, `tests/test_orchestration_contract.py`.

**Interfaces:** (Produces / Consumes)
- Produces: `reflection_pairs` `task-req-review-loop` (`generator: developer`, `critic: validator`, `max_iterations: 2`, `on_blocked: escalate_to_orchestrator`) und `task-quality-review-loop` (`generator: developer`, `critic: code-reviewer`, `max_iterations: 2`, `on_blocked: escalate_to_orchestrator`); in `quality_pipelines.concept-driven-dev`: `task-review: {max-rounds: 4}` und Stages `review-req` (`agent: validator`, `mode: loop`, `loop_ref: task-req-review-loop`) und `review-quality` (`agent: code-reviewer`, `mode: loop`, `loop_ref: task-quality-review-loop`) unmittelbar nach `implement`, vor `validate`; `_validate_task_review_rounds(pipelines, reflection_pairs) -> List[str]`, aufgerufen aus `validate_pipelines`.
- Consumes: bestehendes `resolve_stage_loop`; `loop_ref`-Rendering (`_generate_pipeline_block`, `reflection.inject_loop_config`).

**Depends on:** —

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_pipelines.py::test_task_review_rounds_cap_enforced` (Cap < Summe → Fehler mit Pipeline-Namen), `::test_task_review_rounds_default_ok` (4 ≥ 2+2, keine Fehler), `::test_task_review_rounds_missing_loop_ref_errors`; `tests/test_orchestration_contract.py::test_concept_driven_dev_spec_plan_phase_order` auf die 10er-Liste `explore, classify, specify, review, approve, plan, implement, review-req, review-quality, validate` umstellen (AC-32).
- [ ] Step 2: Implementieren — Validator prüft, dass jede Stage in `{review-req, review-quality}` einen `loop_ref` mit explizitem `max_iterations ≥ 1` auflöst und die Summe ≤ `task-review.max-rounds` (Default 4) ist (fail-closed, Fehlerstrings). Kein neues Rendering; Cap bleibt aus `max_iterations` der Paare gespeist.
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_pipelines.py tests/test_orchestration_contract.py -q` und `python3 scripts/sync.py --validate`.
- [ ] Step 4: Commit — `feat: add two-stage task review with round cap`.

**Acceptance:** AC-21, AC-22, AC-32.

---

### Task 12: Root-Cause-Stages in den Bugfix-Pipelines (G-10)

**Files:**
- Modify: `config/role-defaults.yaml`.
- Test: `tests/test_pipelines.py`.

**Interfaces:** (Produces / Consumes)
- Produces: in `quality_pipelines.bugfix` eine unbedingte Stage `root-cause` (`agent: bug-feature-analyzer`, `mode: sequential`) zwischen `triage` und `fix`; in `quality_pipelines.quick-fix` eine Stage `root-cause` mit `condition: {dod_flag: root-cause-required}`.
- Consumes: bestehende Pipeline-/Condition-Mechanik (`dod_flag`).

**Depends on:** 13 (Flag-Auflösung), damit die konditionale Stage auflösbar ist

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_pipelines.py::test_bugfix_has_mandatory_root_cause_stage`, `::test_quick_fix_root_cause_is_conditional`, `::test_all_role_defaults_pipelines_are_clean` bleibt grün.
- [ ] Step 2: Implementieren — nur `config/role-defaults.yaml`; keine Rollen-Namen in Templates.
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_pipelines.py -q` und `python3 scripts/sync.py --validate`.
- [ ] Step 4: Commit — `feat: add root-cause gate stage to bugfix pipelines`.

**Acceptance:** AC-23.

---

### Task 13: DoD-Flag und Rule-Gates für Root-Cause

**Files:**
- Modify: `config/dod-presets.yaml`.
- Modify: `config/rules-presets.yaml`.
- Modify: `scripts/lib/rules.py`.
- Test: `tests/test_rules_activation_gate.py`, `tests/test_spec_plan_config_schema.py`.

**Interfaces:** (Produces / Consumes)
- Produces: `root-cause-required` in **jedem** Preset (inkl. `full`); `true` für `spec-driven`, `concept-driven`, `spec-certified`, sonst `false`; `rule-gates`-Einträge `session-recovery: {requires: spec-plan-workflow.enabled}` und `root-cause-gate: {requires: dod.root-cause-required}`; `_rule_gate_satisfied`-Branch für `dod.root-cause-required` über `resolve_dod(config, agent_meta_root).get("root-cause-required", False)`; unbekannte Requirements bleiben fail-closed.
- Consumes: `resolve_dod`.

**Depends on:** —

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `test_rules_activation_gate.py::test_root_cause_gate_flag_on_off`, `::test_unknown_gate_requirement_fails_closed`, `::test_session_recovery_gate_follows_workflow`; Fixture-Root mit `root-cause-gate.md` (analog bestehender `_consumer_root`).
- [ ] Step 2: Implementieren — `resolve_dod` konsumiert den Wert automatisch (Preset-Iteration); neue Rules bleiben plain (kein `channel`), solange der Gate erfüllt ist.
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_rules_activation_gate.py -q`.
- [ ] Step 4: Commit — `feat: gate root-cause and session-recovery rules via DoD`.

**Acceptance:** AC-24, AC-25 (Flag-Auflösung).

---

### Task 14: Config-Schema erweitern

**Files:**
- Modify: `config/project-config.schema.json`.
- Test: `tests/test_spec_plan_config_schema.py`.

**Interfaces:** (Produces / Consumes)
- Produces: `spec-plan-workflow.recovery` (`rehydrate: boolean`, `max-age-seconds: integer`, `include-legacy: boolean`); `spec-plan-workflow.ledger-drift` (`enabled: boolean`, `severity: string`); `dod.root-cause-required: boolean`; `stageItem.condition` mit `dod_flag`/`payload_flag` (string) neben `type`/`agent`; `pipelineDefinition.task-review.max-rounds` (integer, `minimum: 1`).
- Consumes: nichts (Schema ist Deklaration/Tippfehler-Guard, Konsum erfolgt in Task 5/12/13).

**Depends on:** —

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `test_spec_plan_config_schema.py::test_recovery_and_ledger_drift_accepted`, `::test_root_cause_required_accepted`, `::test_task_review_max_rounds_accepted`, `::test_condition_payload_flag_accepted`, `::test_unknown_recovery_key_rejected`.
- [ ] Step 2: Implementieren — Properties in die jeweiligen Objekte; deren `additionalProperties: false` erhalten; `stageItem`/`pipelineDefinition` bleiben `additionalProperties: true` (F7: explizite Doku + Tippfehler-Guard).
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_spec_plan_config_schema.py -q`.
- [ ] Step 4: Commit — `feat: extend project config schema for recovery and gates`.

**Acceptance:** AC-25 (Schema-Akzeptanz), M2 (Deklaration).

---

### Task 15: Gruppierungs-Aspect recovery-rehydrate

**Files:**
- Modify: `config/spec-plan-groups.yaml`.
- Modify: `scripts/lib/dod.py`.
- Modify: `tests/test_spec_plan_group_consistency.py`.
- Test: `tests/test_spec_plan_group_consistency.py`.

**Interfaces:** (Produces / Consumes)
- Produces: Aspect `recovery-rehydrate` (`mechanism: pipeline-stage-condition`, `config-path: spec-plan-workflow.recovery.rehydrate`, `enabled-when: seed`, `consumer: scripts/lib/recovery.py::find_resumable_session`), **nach `consistency-noop`, vor `ke-auto-index`**; identische Position in `_SPEC_PLAN_FALLBACK_ASPECTS` als `("recovery-rehydrate", "seed")`; `"recovery-rehydrate"` in `SEED_EQUAL_ASPECTS` direkt nach `"consistency-noop"`.
- Consumes: `recovery.py` muss den Token `spec-plan-workflow.recovery.rehydrate` textuell referenzieren (Consumer-Ratchet).

**Depends on:** 8

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `test_spec_plan_group_consistency.py::test_fallback_group_matches_yaml` (paarweise Reihenfolge), `::test_expected_aspect_ids_present` und `::test_bundle_exposes_exactly_seed_and_all_aspects` um `recovery-rehydrate` erweitern; Consumer-Referenz-Check.
- [ ] Step 2: Implementieren — die vier Stellen synchron in exakt der fixierten Position ändern (YAML, Fallback-Tuple, `SEED_EQUAL_ASPECTS`); `SPEC_PLAN_WHEN_OPERANDS` bleibt unverändert (`seed` bereits erlaubt).
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_spec_plan_group_consistency.py -q`.
- [ ] Step 4: Commit — `feat: add recovery-rehydrate plan-mode aspect`.

**Acceptance:** AC-27, F8.

---

### Task 16: Rule- und Snippet-Dokumentationsflächen

**Files:**
- Create: `rules/1-generic/session-recovery.md`.
- Create: `rules/1-generic/root-cause-gate.md`.
- Modify: `rules/1-generic/plan-ledger.md`.
- Modify: `snippets/orchestrator/checkpointing.md`.
- Test: `tests/test_no_role_routes_in_templates.py`, `tests/test_progress_file_documented.py`.

**Interfaces:** (Produces / Consumes)
- Produces: `session-recovery`-Regel (Session-Start liest Resume-Kontext über den read-only rehydrate-Modus; offener Task wird an `next_task_ref` fortgesetzt, nie still übersprungen/umsortiert); `root-cause-gate`-Regel (Ursache + Vorversuche belegt, Symptom-Fix erfüllt nicht); aktualisierte `plan-ledger.md` (zweistufiger Review + Writer-Pflicht; `execute_plan` ist jetzt verdrahtet, nur G-08-Dispatcher bleibt out-of-scope); `checkpointing.md` (rehydrate-Pfad, Store autoritativ, Legacy-Format read-only, 24h-Auto-Delete-Promise entfernt, `checkpoint_ref`/`current.md`/Tier-A/Tier-B-Tokens erhalten).
- Consumes: nichts (Doku surface).

**Depends on:** 6, 11, 13

**Steps:**
- [ ] Step 1: Test schreiben (fail) — Integration-Assert: reale `rules/1-generic/root-cause-gate.md` und `session-recovery.md` existieren und werden durch `collect_rule_sources` bei erfülltem Gate gelistet; `tests/test_no_role_routes_in_templates.py` (AC-26) und `tests/test_progress_file_documented.py` (AC-31) bleiben grün.
- [ ] Step 2: Implementieren — Wording ausschließlich mit Pipeline-/Stage-/Pair-IDs, nie Rollen-Namen oder `roleA → roleB`; keine Route-Tabellen; `NEXT:`-Blöcke rollenfrei.
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_no_role_routes_in_templates.py tests/test_progress_file_documented.py tests/test_rules_activation_gate.py -q`.
- [ ] Step 4: Commit — `docs: document session recovery and root-cause gate rules`.

**Acceptance:** AC-26, AC-31.

---

### Task 17: Szenario 59-progress-ledger

**Files:**
- Create: `tests/scenarios/configs/59-progress-ledger.project.yaml`.
- Create: `tests/scenarios/asserts/59-progress-ledger.sh` (ausführbar).
- Modify: `tests/scenarios/registry.md`.
- Test: `tests/scenarios/run.sh 59`.

**Interfaces:** (Produces / Consumes)
- Produces: eigenständige Consumer-Config (spec-plan aktiv, `paths.plans` gesetzt, `recovery.rehydrate: true`); Assert-Script, das `execute_plan`-Checkpoint, Ledger-Update, Drift-Warnung für einen synthetischen Mismatch und `next_task_ref` aus dem rehydrate-Pfad prüft.
- Consumes: `scripts/lib/*` (Tasks 1–16), `tests/scenarios/run.sh`-Vertrag (`cwd` = Temp-Projekt, `$1`/`REPO_ROOT` = Checkout).

**Depends on:** 3, 5, 6, 7, 8, 9, 10

**Steps:**
- [ ] Step 1: Test schreiben (fail) — Assert-Script mit `fail()`-Helper; registry-Zeile `| \`59-progress-ledger\` | Claude | strict (default) | … |`; Szenario-Config auf `dry_rc=0 && sync_rc=0 && val_rc=0 && assert_rc=0` auslegen.
- [ ] Step 2: Implementieren — Assert-Script legt Plan-/Checkpoint-Fixtures an, ruft die neuen Pfade read-only/write im Temp-Root, prüft Ledger-Write, Drift-`WARNING` und Resume-Kontext.
- [ ] Step 3: Test (pass) — `tests/scenarios/run.sh 59` → `PASS`.
- [ ] Step 4: Commit — `test: add progress-ledger scenario`.

**Acceptance:** AC-28.

---

### Task 18: Konventions-Ratchet (Py3.9 + Provider-Agnostik)

**Files:**
- Create: `tests/test_progress_ledger_conventions.py`.
- Test: `tests/test_progress_ledger_conventions.py`.

**Interfaces:** (Produces / Consumes)
- Produces: Guard-Test, der (a) in den neuen Modulen `scripts/lib/plan_identity.py`, `recovery.py`, `rehydrate.py`, `plan_ledger.py`, `checkpoint_record.py` keine PEP-604-Union-Syntax (`X | Y` in Annotationen) und `from __future__ import annotations`-Präsenz prüft, (b) kein `if provider ==` und kein Provider-Literal in den neuen/geänderten Modulen findet.
- Consumes: `ast` (Stdlib).

**Depends on:** 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `test_progress_ledger_conventions.py::test_new_modules_import_and_no_pep604`, `::test_no_provider_literals_in_new_modules`.
- [ ] Step 2: Implementieren — nur den Guard-Test; gefundene Verstöße in den Tasks 1–16 korrigieren.
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_progress_ledger_conventions.py -q` und `python3 scripts/sync.py --validate` und `python3 scripts/consistency-check.py` (exit 0).
- [ ] Step 4: Commit — `test: lock provider-agnosticism and py39 syntax`.

**Acceptance:** AC-29, AC-30.

---

## Acceptance-Criteria → Task-Mapping

| AC | Task(s) |
|----|---------|
| AC-01 | 1, 4 |
| AC-02 | 1 |
| AC-03 | 1 |
| AC-04 | 2 |
| AC-05 | 2 |
| AC-06 | 2 |
| AC-07 | 6 |
| AC-08 | 6 |
| AC-09 | 6 |
| AC-10 | 6 |
| AC-11 | 3 |
| AC-12 | 3 |
| AC-13 | 3 |
| AC-14 | 7 |
| AC-15 | 5 |
| AC-16 | 5 |
| AC-17 | 8 |
| AC-18 | 8 |
| AC-19 | 8 |
| AC-20 | 9 |
| AC-21 | 11 |
| AC-22 | 11 |
| AC-23 | 12 |
| AC-24 | 13 |
| AC-25 | 13, 14 |
| AC-26 | 16 (global: alle Tasks) |
| AC-27 | 15 |
| AC-28 | 17 |
| AC-29 | 18 |
| AC-30 | 18 |
| AC-31 | 16 |
| AC-32 | 11 |
| AC-33 | 10 |
| AC-34 | 5 |

## Self-Review

- **AC-Abdeckung:** Alle 34 Acceptance Criteria sind mindestens einer Task zugeordnet (Tabelle oben). Kein AC ohne Task, keine Task ohne AC-Bezug.
- **Test je Task:** Jede Task hat einen konkreten Testfall mit Testpfad und Verifikationskommando; kein Task ist ohne beobachtbaren Test „done".
- **Traceability:** `spec-id: SPEC-PROGRESS-LEDGER-2026-09-13` ↔ Task-ID ↔ Test ist vollständig; `pipeline_stages.implement` zeigt auf Step 1.
- **Interface-Vollständigkeit:** Jede Task hat nicht-leere `Produces`/`Consumes`; neue Symbole sind mit Datei, Name und Signatur benannt.
- **Abhängigkeiten:** Graph ist zyklenfrei; `plan_identity` (1) ist Wurzel, `checkpoint`/`orchestration`/`consistency` hängen davon ab, CLI-Modi hängen an ihren Modulen, `recovery-rehydrate` (15) hängt an `recovery` (8), Szenario (17) integriert 3/5/6/7/8/9/10, Ratchet (18) schließt ab.
- **Rahmenbedingungen:** Keine Rollen-Route in `agents/1-generic/*`/`rules/1-generic/*` (AC-26 in Task 16; alle Tasks vermeiden Route-Tabellen/Handoffs). Gruppierung synchron an 4 Stellen in Task 15. Keine Modellnamen. Stdlib only, Py3.9, provider-agnostisch (Task 18 ratet). Bestehende Infrastruktur wird verdrahtet, nichts parallel erfunden.
- **Minor-Findings:** M1 (Normalisierung in `--checkpoint`) → Task 10; M2 (`ledger-drift.enabled/severity`) → Task 5 + Deklaration Task 14; M3 (Exit 1 bei Pflichtargumenten) → Task 10; M4 (`plans`-Pfad aus Config) → Task 8.
- **No-Placeholder:** Keine Platzhalter-Marker, keine leeren Interfaces; exakte Pfade, Symbole, Signaturen und Commit-Messages.

## Ausführungs-Handoff

- **Reihenfolge:** Task 1 → 18 in aufsteigender Numerik. Task 12 und 13 sind zueinander abhängig (13 liefert das Flag, das 12 konditional konsumiert); 12 deshalb nach 13 ausführen. Tasks mit disjunkten Dateien (11, 13, 14) dürfen nach ihren Abhängigkeiten parallel laufen; Barrieren/Ownership kommen aus dem `Files:`-Block (`check_plan_file_overlap`).
- **Loop-Cap:** Der zweistufige Task-Review (`review-req` → `review-quality`) läuft mit `max_iterations: 2` je Pair und `task-review.max-rounds: 4`; `_validate_task_review_rounds` ist fail-closed. Nach `on_blocked: escalate_to_orchestrator` wird nicht weiter iteriert.
- **Task-für-Task (SDD):** Jede Task wird von einem frischen Subagenten mit frischem Kontext ausgeführt, reviewt und erst dann committet; die Ledger-Checkboxen werden nach Task-Abschluss über den Writer aktualisiert (Task 6/7). Kein Task ohne Test und Commit.
- **Blocked-Regel:** Kann eine Task ihre Akzeptanz nicht belegen, bleibt sie offen (Checkbox `- [ ]`), wird an den Orchestrator eskaliert und blockiert Nachfolger; sie wird nie stillschweigend übersprungen oder umsortiert (Session-Recovery-Vertrag, Task 16).
- **Abschluss-Gate:** Vor Freigabe laufen `python3 scripts/sync.py --validate`, `python3 scripts/consistency-check.py` (exit 0), `python3 -m pytest` (relevante Suiten) und `tests/scenarios/run.sh 59` (PASS).
