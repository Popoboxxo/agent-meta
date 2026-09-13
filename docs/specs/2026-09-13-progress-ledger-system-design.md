---
spec-id: SPEC-PROGRESS-LEDGER-2026-09-13
title: Progress / Ledger System Design
status: APPROVED
gaps: [G-02, G-03, G-04, G-09, G-10]
source-analysis: docs/process-capability-gaps.md
---

# Progress / Ledger System — Technical Specification

> Status: APPROVED — review findings F1–F9 are incorporated below; the approval marker
> `Status: APPROVED` is set by `concept-reviewer`, not by this document.
> Trace anchor: `spec-id: SPEC-PROGRESS-LEDGER-2026-09-13`.
> Gap source: `docs/process-capability-gaps.md` (G-02, G-03, G-04, G-09, G-10).
> This document is a specification only. It contains interface contracts, not implementation.

### Revision — incorporated review findings

| Finding | Change |
|---|---|
| F1 | Checkpoint identity derives **only** from an explicit `plan_id`; no random fallback in checkpoints (IC-06, AC-11, AC-13, Flow B). |
| F2 | New canonical 10-stage order fixed; the exact-order pytest must be updated (IC-08, AC-21, AC-32). |
| F3 | Concrete production triggers added: `--rehydrate` (read) and `--checkpoint` (write), plus the existing `--update-plan-ledger`; G-08 coupling documented (IC-11, AC-33, "Limitations & coupling"). |
| F4 | Drift scope explicitly documented as changed-files-scoped (IC-07, AC-34). |
| F5 | Scenario renumbered `51-…` → `59-progress-ledger`, registry entry added (AC-28). |
| F6 | `plan-ledger.md` and `checkpointing.md` alignment; auto-deletion promise removed; Tier-A/Tier-B tokens preserved (IC-10, AC-31). |
| F7 | Schema additions justified as explicit documentation / typo guard (`additionalProperties: true` already) (IC-09). |
| F8 | `recovery-rehydrate` insertion position fixed: after `consistency-noop`, before `ke-auto-index` (IC-09). |
| F9 | `Checkpoint.__init__` line references corrected (Problem, IC-02). |

## Problem

The repository already ships two independent progress surfaces, but they are not wired into one
running system:

1. **Human-readable plan ledger** — checkboxes (`- [ ]` / `- [x]`) plus a `> Status:` header on a
   plan document. It is parsed by `scripts/lib/consistency/spec_plan.py::parse_plan_ledger` (line 82)
   and format-checked by `::_check_ledger_format` (line 458), but **there is no writer**: the ledger
   is only ever read. The observed state (0/56 checkboxes on the current backlog) proves that manual
   ticking does not happen.
2. **Machine-readable checkpoint store** — `scripts/lib/checkpoint.py::CheckpointStore` writes
   `.meta-viz/checkpoints/<session>.json` plus `.meta-viz/progress/current.md`. `save_checkpoint`
   (line 349) has **no production caller**; `get_last_checkpoint` (line 410), `get_completed_steps`
   (line 417) and `list_sessions` (line 428) are only exercised by tests; `execute_plan`
   (`scripts/lib/orchestration.py`, line 372) archives raw output but never persists a checkpoint and
   has no production caller either.

Consequences verified against the code:

- **G-02** — no automatic re-hydrate path. Resume exists only as prose
  (`snippets/orchestrator/checkpointing.md`, lines 22–29). Nothing reads the store on session start.
- **G-03** — no stable key linking plan task and checkpoint. Plan tasks are normalized to
  `task-<n>` (`spec_plan.py::_normalize_task_id`, line 549) while checkpoints carry `task_id` and a
  random UUID (`checkpoint.py::Checkpoint.__init__`: `def` at line 205, `self.id = str(uuid.uuid4())`
  at line 218). A checkpoint cannot be mapped to a
  plan task across sessions. Additionally `_TASK_HEADER_RE` (lines 51–53) is hyphen-blind: the
  character class excludes `-`, so `### Task task-1: …` captures only `task`.
- **G-04** — no machine write path for the ledger and no drift observation between ledger and
  checkpoints.
- **G-09** — task review is a single quality loop (`config/role-defaults.yaml`, `bugfix` stage
  `review`, lines 2441–2448, `max_iterations: 2`). There is no separate requirement-fidelity pass and
  no aggregate round cap across the review stages.
- **G-10** — no mandatory root-cause gate before a bugfix. `agents/1-generic/principal-developer.md`
  (lines 72–80) has a `root_cause` decision block, but it is an escalation convention, not a gate.

## Ziel

Wire the existing infrastructure into one recoverable progress/ledger loop, without inventing a
parallel format and without adding role routing to generic templates:

1. **Stable identity (G-03):** a deterministic `plan_id` and a composite `task_ref`
   (`<plan_id>#task-<n>`) shared by plan → task → checkpoint; backward compatible with existing
   checkpoint JSON and existing plan files.
2. **Real resume (G-02):** a read-only production caller for `list_sessions` / `get_last_checkpoint` /
   `get_completed_steps` (`--rehydrate`), a concrete production writer for checkpoints (`--checkpoint`),
   plus a checkpoint writer inside `execute_plan` for the automatic path.
3. **Writable, drift-checked ledger (G-04):** a writer API that produces output exactly matching
   `parse_plan_ledger` semantics, exposed as the production mode `--update-plan-ledger`, and a drift
   check inside the existing consistency run.
4. **Two-stage task review with round cap (G-09):** expressed via `reflection_pairs` and pipeline
   stages in `config/role-defaults.yaml` only.
5. **Root-cause gate (G-10):** a mandatory pipeline stage plus a DoD flag and a condition schema
   extension; no role literal in generic templates.

## Nicht-Ziele

- No system redesign for XL changes; this is a bounded M/L specification on existing machinery.
- No new ledger format. The plan document stays the human view; `CheckpointStore` stays the machine
  view.
- No changes to `agents/1-generic/*.md` that introduce role routes, route tables, `roleA → roleB`
  chains, handoff sentences with role names, or role labels inside `NEXT:` blocks.
- No provider-specific behaviour and no `if provider == …`. Provider differences stay config-driven.
- No REQ-ID assignment, no implementation, no config/template edits in this document.
- Not in scope: G-01 (global board), G-05 (24h rotation wiring), G-06 (full format unification),
  G-07 (`current.md` as recovery input), G-08 (`execute_plan` backend dispatcher), G-11/G-12/G-13.
  G-06 is only addressed insofar as the recovery resolver must tolerate both existing formats
  read-only. Only the **automatic in-harness** dispatch path is coupled to G-08 (see IC-11,
  "Limitations & coupling"); the CLI production triggers in IC-04/IC-05/IC-11 are delivered here and do
  not wait for G-08.
- No automatic deletion or migration of legacy checkpoint files.

## Interface Contracts

All new/changed symbols are listed as `file:Symbol`. New modules must use
`from __future__ import annotations` or `typing.Optional` / `typing.Tuple`; PEP 604 (`X | Y`)
annotations are not introduced in new modules (Python 3.9 compatibility). Standard library only.

### IC-01 — `scripts/lib/plan_identity.py` (new module)

Leaf module (imports `pathlib`, `re`, `typing` only). Shared by parser, writer, checkpoint writer and
validator.

```python
PLAN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
TASK_ID_RE = re.compile(r"^task-[0-9]+$")
_PLAN_ID_FIELD_RE = re.compile(
    r"(?im)^[ \t]*>?[ \t]*\**plan-id\**:[ \t]*([A-Za-z0-9][A-Za-z0-9._-]*)"
)
TASK_HEADER_RE = re.compile(
    r"(?m)^###[ \t]+Task[ \t]+([A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*)"
    r"[ \t]*(?::|[—–-])?[ \t]*(.*?)[ \t]*$"
)

def derive_plan_id(plan_path: Path, text: Optional[str] = None) -> str: ...
def normalize_task_id(raw: str) -> str: ...
def make_task_ref(plan_id: Optional[str], task_id: str) -> Optional[str]: ...
```

- `TASK_HEADER_RE` **replaces** the hyphen-blind private regex. Group 1 is the raw task id and may
  contain `-`, `.`, `_`; group 2 is the title. `### Task task-1: X` → group 1 `task-1`.
  `### Task 1 — X` → group 1 `1`, group 2 `X`. The pattern still matches at most one header per line.
- `derive_plan_id` precedence: explicit `plan-id:` field in the document text (frontmatter or a
  `> plan-id:` header line) if it matches `PLAN_ID_RE`; otherwise a deterministic slug of
  `plan_path.stem` (`[^a-z0-9]+` → `-`, trim, lowercase). Never random, never timestamp-based. An
  unreadable file (`OSError`) falls back to the stem slug; the function never raises.
- `normalize_task_id` keeps the current behaviour (`"3"` → `"task-3"`, `"TASK-3"` → `"task-3"`,
  otherwise unchanged) and becomes the single implementation; `spec_plan._normalize_task_id`
  delegates to it.
- `make_task_ref(plan_id, task_id)`: `None` when `plan_id` is falsy; when `task_id` already contains
  `#`, returns `task_id` unchanged; otherwise `f"{plan_id}#{task_id}"`.

### IC-02 — `scripts/lib/checkpoint.py` (changed)

`Checkpoint` gains two optional fields; nothing becomes mandatory.

```python
def __init__(
    self, task_id, agent, task_description, status,
    result=None, next_step=None, status_summary=None, pipeline=None,
    stage=None, timestamp=None,
    plan_id=None, task_ref=None,
) -> None: ...
```

- `to_dict()` adds `"plan_id": self.plan_id` and `"task_ref": self.task_ref` (values may be `None`).
- `from_dict(data)` reads `data.get("plan_id")` and
  `data.get("task_ref") or make_task_ref(data.get("plan_id"), data["task_id"])`. Existing JSON
  documents without the new keys must keep loading (the four hard-required fields
  `task_id`, `agent`, `task_description`, `status` are unchanged).
- New query helpers on `CheckpointStore`, fail-soft like the existing loaders:

```python
def get_checkpoint_for_task(self, session_id: str, task_ref: str) -> Optional[Checkpoint]: ...
def find_sessions_for_plan(self, plan_id: str) -> List[str]: ...
```

  - `get_checkpoint_for_task` returns the last checkpoint whose `task_ref == task_ref`, or — for
    backward compatibility with pre-`task_ref` entries — whose `plan_id` and `task_id` reconstruct
    the same ref. Returns `None` on missing or corrupt session.
  - `find_sessions_for_plan` returns session ids (newest `updated_at` first) containing at least one
    checkpoint with that `plan_id`; corrupt files are skipped, never raised.
- `save_checkpoint`, `load_session`, `get_last_checkpoint`, `get_completed_steps`, `list_sessions`,
  `delete_session`, `cleanup_old_sessions`, `save_raw_output` keep their signatures and behaviour.

### IC-03 — `scripts/lib/recovery.py` (new module)

Production read path for G-02. Never mutates. This module is the documented caller of
`list_sessions` / `get_last_checkpoint` / `get_completed_steps`.

```python
REHYDRATE_CONFIG_PATH = "spec-plan-workflow.recovery.rehydrate"

@dataclass(frozen=True)
class RecoverySource:
    session_id: str
    plan_id: Optional[str]
    source_format: str          # "store" | "legacy"
    updated_at: float
    completed_task_refs: Tuple[str, ...]
    pending_task_refs: Tuple[str, ...]
    last_status: Optional[str]
    note: Optional[str]

@dataclass(frozen=True)
class ResumeContext:
    session_id: str
    plan_id: Optional[str]
    source_format: str
    last_checkpoint: Optional[Checkpoint]
    completed_task_refs: Tuple[str, ...]
    next_task_ref: Optional[str]
    plan_path: Optional[str]
    ledger: Optional[dict]
    drift: Tuple[str, ...]

def load_legacy_checkpoints(project_root: Path) -> List[RecoverySource]: ...
def load_store_sources(store: CheckpointStore) -> List[RecoverySource]: ...
def resolve_recovery_sources(project_root: Path, *,
                             store: Optional[CheckpointStore] = None,
                             max_age_seconds: Optional[float] = None,
                             include_legacy: bool = True) -> List[RecoverySource]: ...
def find_resumable_session(project_root: Path, *,
                           store: Optional[CheckpointStore] = None,
                           max_age_seconds: Optional[float] = None) -> Optional[RecoverySource]: ...
def build_resume_context(project_root: Path, session_id: str, *,
                         plan_id: Optional[str] = None,
                         store: Optional[CheckpointStore] = None) -> Optional[ResumeContext]: ...
def render_resume_context(context: ResumeContext) -> str: ...
```

- `load_legacy_checkpoints` reads `.meta-viz/checkpoint-*.json` (the manually written format from
  `snippets/orchestrator/checkpointing.md`, lines 2–16: `session_id`, `created_at`, `task_summary`,
  `completed_steps`, `pending_steps`, `context`). Unknown keys are ignored, malformed files are
  skipped with a warning. Legacy entries have `plan_id=None`; pending steps without a task id get the
  synthetic ref `step:<n>`.
- `load_store_sources` uses `CheckpointStore.list_sessions()`, then `get_last_checkpoint` and
  `get_completed_steps` per session. `plan_id` is taken from the newest checkpoint that carries one.
- `resolve_recovery_sources` merges both formats, deduplicates by `session_id` (store source wins
  when a session id appears in both), filters by `max_age_seconds` (`None` means the configured
  default), and sorts newest first. It never raises for content problems.
- `find_resumable_session` returns the newest source whose last status is not `completed`, or which
  still has pending refs. If the linked plan resolves and its ledger is complete while the source has
  no pending work, the source is not resumable.
- `build_resume_context` re-reads the plan ledger via
  `consistency.spec_plan.parse_plan_ledger` when the plan path can be resolved from the plan identity
  (search `docs/plans` for a file whose `derive_plan_id` equals the source `plan_id`), computes
  `next_task_ref` as the first ledger task not present in `completed_task_refs`, and records drift
  strings. Returns `None` when the session does not exist.
- `render_resume_context` returns a bounded Markdown block (session id, plan, completed steps, next
  open task, drift lines). It sends no dispatch instructions and names no role.

### IC-04 — `scripts/lib/rehydrate.py` (new module)

Read-only CLI mode, provider-agnostic, no sync and no writes.

```python
MODE = "rehydrate"

def rehydrate(project_root: Path, config: Optional[dict], log: SyncLog) -> int: ...
def _handle_rehydrate(ctx) -> None: ...
```

- Behaviour: resolve `CheckpointStore(project_root)`; call
  `find_resumable_session(project_root, store=store)`. If a session is resumable, print
  `render_resume_context(build_resume_context(...))` and return `0`. If none is resumable, print an
  explicit "no unfinished session" note and return `0`. The mode never returns a failure code for
  "nothing to resume" — it is an informational read path.
- Configuration is read from `spec-plan-workflow.recovery` (see IC-09). `rehydrate: false` makes the
  mode print "rehydrate disabled" and return `0`.
- Registered in `scripts/sync.py` next to `--validate-spec-plan` (same handler convention as
  `spec_plan_validate.py`).

### IC-05 — `scripts/lib/plan_ledger.py` (new module)

Writer for G-04. Semantics are defined by `parse_plan_ledger`, not the other way round.

```python
MODE = "update-plan-ledger"

@dataclass(frozen=True)
class LedgerWriteResult:
    plan_path: str
    ok: bool
    reason: Optional[str]
    tasks_updated: Tuple[str, ...]
    checkboxes_toggled: int
    unmatched: Tuple[str, ...]
    status: Optional[str]
    dry_run: bool

def update_plan_ledger(plan_path: Path, updates: Mapping[str, bool], *,
                       status: Optional[str] = None,
                       dry_run: bool = False) -> LedgerWriteResult: ...
def set_plan_status(plan_path: Path, status: str, *,
                    dry_run: bool = False) -> LedgerWriteResult: ...
def handle_update_plan_ledger(ctx) -> None: ...
```

- `update_plan_ledger` locates each task block with `plan_identity.TASK_HEADER_RE`, using
  `normalize_task_id` on group 1. `updates["task-3"] = True` rewrites every leading
  `- [ ]` / `- [x]` checkbox inside that block to `- [x]`; `False` resets them to `- [ ]`.
  Only line-leading checkboxes (`^- \[( |x|X)\]`) are touched; indentation and trailing text are
  preserved. Checkboxes outside task blocks and in other tasks are never modified.
- If `status` is given, the **first** `Status:` header line of the document is replaced; when no such
  line exists, `> Status: <value>` is inserted directly after the H1 title. Only the first line is
  considered, matching `parse_plan_ledger`'s `re.search` behaviour.
- The writer must guarantee the parser contract: after marking every task done,
  `parse_plan_ledger(plan_path)["complete"] is True`. Conversely, `complete` must be `False` while any
  leading checkbox is open.
- Atomicity: the whole new document is built in memory and written with the existing
  `scripts/lib/io.py::write_atomic`. When nothing changes, no write happens.
- Error behaviour (never raises for content problems):
  - missing plan → `ok=False`, `reason="plan-not-found"`, no write;
  - task id not found → recorded in `unmatched`, all other updates still applied;
  - `OSError` → `ok=False`, `reason="io-error:<ClassName>"`.
- `set_plan_status` is a thin wrapper over `update_plan_ledger(plan_path, {}, status=...)`. Accepted
  status values are `geplant`, `IN PROGRESS`, `complete`; any non-empty string is written verbatim
  and read back by the parser.
- `handle_update_plan_ledger` is the CLI handler for
  `sync.py --update-plan-ledger <plan> --task <id> [--open] [--status <s>] [--dry-run]`. It prints
  the `LedgerWriteResult` and exits `0` on `ok`, `1` when `ok=False` or any `unmatched` entry exists.
  This path is a deliberate mutation and must only be invoked inside the project root.

### IC-06 — `scripts/lib/orchestration.py` (changed)

Checkpoint writer (G-02) and optional ledger close-out (G-04).

```python
def execute_plan(
    plan: FanoutPlan,
    dispatcher: Dispatcher,
    *,
    store: Optional[CheckpointStore] = None,
    session_id: Optional[str] = None,
    plan_id: Optional[str] = None,
    write_checkpoints: bool = True,
    ledger_path: Optional[Path] = None,
) -> BarrierResult: ...

def checkpoint_from_barrier_entry(
    entry: BarrierEntry, *, plan_id: Optional[str] = None,
    task_description: str = "",
) -> Checkpoint: ...
```

- Current raw-output archiving behaviour is unchanged.
- When `store` and `session_id` are given and `write_checkpoints` is `True` (the default), one
  checkpoint is appended per resolved entry via `store.save_checkpoint`. Mapping:
  `status`: `success → "completed"`, `failed → "failed"`, `timeout → "timeout"`;
  `agent = entry.agent`; `task_description` from the matching `FanoutTask.prompt` (fallback
  `entry.task_id`); `status_summary = entry.summary`.
- **Checkpoint identity rule (F1):** `plan_id` and `task_ref` are derived **only** from the explicit
  `plan_id` argument. `checkpoint_from_barrier_entry` sets `plan_id = plan_id` (the argument,
  verbatim) and `task_ref = make_task_ref(plan_id, entry.task_id)`; when `plan_id` is `None`, both
  resolved fields are `None`. The random `KIND-<uuid>` value stays exclusively on
  `BarrierResult.plan_id` and is never copied into a checkpoint: a per-run display id is not a durable
  cross-session key, and a random value must never become recovery identity. Deriving identity from
  `ledger_path` is deliberately rejected — the path is an arbitrary caller-provided location, and
  silent slug derivation would couple recovery to a filesystem path the caller did not declare as
  identity. Identity stays an explicit caller input.
- `write_checkpoints=False` restores the previous behaviour exactly (raw-output archive only).
- Write failures are fail-soft: a checkpoint `OSError` is logged and the barrier continues; it must
  not change the aggregated `BarrierResult.status`.
- When `ledger_path` is given, after aggregation the function marks every `success` entry's task done
  in the plan and sets the plan status (`complete` when all `- [ ]` checkboxes are closed, otherwise
  `IN PROGRESS`). This uses a lazy import of `scripts/lib/plan_ledger.py` to avoid an import cycle and
  is fail-soft for the same reason. `ledger_path=None` performs no ledger write.
- Status aggregation semantics, entry ordering and `render_barrier_result` stay unchanged.
- `BarrierResult.plan_id` keeps the existing `plan_id or f"{plan.kind.upper()}-<uuid>"` fallback
  unchanged (`tests/test_orchestration_contract.py::test_execute_generated_plan_id_falls_back_to_kind`
  stays green); that random value is never propagated to checkpoints (F1).

### IC-07 — `scripts/lib/consistency/spec_plan.py` (changed)

Drift check (G-04) and hyphen-aware task parsing (G-03).

```python
from ..plan_identity import TASK_HEADER_RE

def parse_task_ledgers(plan_path: Path) -> dict: ...
def _check_ledger_drift(project_root: Path, plans: List[Path],
                        texts: Dict[Path, str], findings: List[Finding]) -> None: ...
```

- `parse_task_ledgers` returns
  `{"<task-id>": {"total": int, "checked": int, "complete": bool, "start": int, "end": int}}`,
  splitting the document on `TASK_HEADER_RE` and counting only leading `- [ ]` / `- [x]` lines inside
  each block. Task ids are normalized with `plan_identity.normalize_task_id`.
- `_TASK_HEADER_RE` (private) becomes an alias of `TASK_HEADER_RE`; `_normalize_task_id` delegates to
  `plan_identity.normalize_task_id`. Existing graph behaviour (`_parse_plan_tasks`,
  `_check_plan_graph`) is preserved; it now correctly parses `task-<n>` headers.
- `_check_ledger_drift` is called from `check_spec_plan_workflow` after `_check_ledger_format`. It
  only runs when the `consistency-noop` aspect is active (existing early-return already covers this)
  and when at least one `CheckpointStore` session exists for the plan's derived `plan_id`.
  Findings use the new code `spec_plan_ledger_drift` with severity `WARNING`:
  - task fully checked in the ledger but no `completed` checkpoint for its `task_ref`;
  - `completed` checkpoint for a `task_ref` but the ledger task not fully checked;
  - plan `Status: complete` while the ledger is not complete.
  A plan with checkboxes but no matching checkpoint sessions yields no drift findings (avoids noise
  for plans that predate the wiring).
- Drift resolution loads sessions via `CheckpointStore.find_sessions_for_plan` and
  `get_completed_steps`; `plan_id` is derived with `plan_identity.derive_plan_id`.
- **Scope (F4):** the drift check inherits the validator's `changed_files` filter.
  `spec_plan_validate.validate_spec_plan` computes `changed_files=_changed_files(project_root)` and
  passes it into `check_spec_plan_workflow`, so drift findings are reported only for plan files that
  are changed in the working tree, staged, or untracked. Unchanged plans are not drift-checked. This
  is intentional and matches the existing `spec-plan-workflow.scan.changed-files-only` default; no
  force-include of plan paths linked to checkpoint sessions is performed.

### IC-08 — Pipeline stages and reflection pairs (G-09, G-10)

`config/role-defaults.yaml` only; no role names appear in generic templates.

- New `reflection_pairs` entries (both with explicit `max_iterations` and `on_blocked`):
  - `task-req-review-loop` — `generator: developer`, `critic: validator`, `max_iterations: 2`,
    `on_blocked: escalate_to_orchestrator`;
  - `task-quality-review-loop` — `generator: developer`, `critic: code-reviewer`,
    `max_iterations: 2`, `on_blocked: escalate_to_orchestrator`.
- `quality_pipelines.concept-driven-dev` gains `task-review: {max-rounds: 4}` and two stages after
  `implement`, before `validate`:
  - `review-req` — `agent: validator`, `mode: loop`, `loop_ref: task-req-review-loop`, requirement
    fidelity against the task's acceptance criteria;
  - `review-quality` — `agent: code-reviewer`, `mode: loop`, `loop_ref: task-quality-review-loop`,
    code quality and blast radius.
- **Canonical exact order (F2):**
  `explore → classify → specify → review → approve → plan → implement → review-req → review-quality
  → validate` (10 stages; `review-req` and `review-quality` sit immediately after `implement` and
  before `validate`). The existing exact-order test
  `tests/test_orchestration_contract.py::test_concept_driven_dev_spec_plan_phase_order` (lines
  757–775) asserts the previous 8-stage list and **must be updated to this 10-stage list as part of
  the change**. This is covered by AC-32, which is a pytest assertion and not only a
  `sync.py --validate` check.
- `quality_pipelines.bugfix` gains an unconditional `root-cause` stage between `triage` and `fix`
  (`agent: bug-feature-analyzer`, `mode: sequential`): a fix stage is only reached after the cause is
  evidenced.
- `quality_pipelines.quick-fix` gains an optional `root-cause` stage with
  `condition: {dod_flag: root-cause-required}` (lightweight pipelines stay lean unless the flag is
  set).
- New validator sub-check `scripts/lib/pipelines.py::_validate_task_review_rounds(pipelines,
  reflection_pairs) -> List[str]`, called from `validate_pipelines` (line 180). It requires that
  every stage id in `{review-req, review-quality}` resolves a `loop_ref` with an explicit
  `max_iterations ≥ 1`, and that the sum of the resolved `max_iterations` of these stages is
  `≤ pipelines["<name>"]["task-review"]["max-rounds"]` (default `4`). Violations are returned as
  error strings (fail-closed). Unknown `loop_ref` already raises in `inject_pipeline_blocks`.
- Round cap visibility: nothing new is rendered. The existing loop rendering in
  `pipelines.py::_generate_pipeline_block` prints `Max iterations: <n>`, and
  `reflection.py::inject_loop_config` fills `{{MAX_ITERATIONS}}` for role templates. Both read the
  same `max_iterations` sourced from the pair, so config and rendered cap cannot drift.

### IC-09 — Declarative grouping and configuration surfaces

- `config/spec-plan-groups.yaml`: one new aspect in group `plan-mode`:

  ```yaml
  - id: recovery-rehydrate
    mechanism: pipeline-stage-condition
    config-path: spec-plan-workflow.recovery.rehydrate
    enabled-when: seed
    consumer: scripts/lib/recovery.py::find_resumable_session
  ```

  **Insertion position (F8):** the aspect is placed in `groups.plan-mode.aspects` immediately
  **after `consistency-noop` and before `ke-auto-index`**. The same position is mirrored in the
  fallback tuple and in the test aspect list so `test_fallback_group_matches_yaml`'s pairwise order
  comparison holds.
  `SPEC_PLAN_WHEN_OPERANDS` is intentionally **not** extended: the aspect uses the existing `seed`
  operand, so the closed `enabled-when` grammar is unchanged.
- `scripts/lib/dod.py::_SPEC_PLAN_FALLBACK_ASPECTS` gains `("recovery-rehydrate", "seed")`, inserted
  after `("consistency-noop", "seed")` and before `("ke-auto-index", …)`, so the built-in fallback
  group keeps the exact order of the YAML.
- `tests/test_spec_plan_group_consistency.py`: add `"recovery-rehydrate"` to `SEED_EQUAL_ASPECTS`
  after `"consistency-noop"` (the tuple feeds `ALL_ASPECTS`), so the test's canonical list order
  matches YAML and fallback. No mechanism enum change is required because
  `pipeline-stage-condition` already exists in `SPEC_PLAN_MECHANISMS` and `MECHANISM_ENUM`.
- `config/project-config.schema.json`:
  - `spec-plan-workflow` gains a `recovery` object
    (`rehydrate: boolean`, `max-age-seconds: integer`, `include-legacy: boolean`) and a
    `ledger-drift` object (`enabled: boolean`, `severity: string`);
  - the resolved `dod` object gains `root-cause-required: boolean`;
  - `stageItem.condition` declares the real, already-consumed properties `dod_flag` and `payload_flag`
    (both strings) in addition to `type` and `agent`. **Justification (F7):** `stageItem` and
    `pipelineDefinition` already accept extra keys (`additionalProperties: true`), so this addition is
    **explicit documentation and a typo guard**, not a hard functional necessity — it makes the
    consumed `condition` keys visible to schema validation instead of relying on permissive passthrough;
  - pipeline override schema gains `task-review` (`max-rounds: integer, minimum 1`).
- `config/dod-presets.yaml`: `root-cause-required` is declared in **every** preset (notably `full`,
  which `resolve_dod` iterates); `true` for `spec-driven`, `concept-driven` and `spec-certified`,
  `false` for the lightweight presets.
- `config/rules-presets.yaml` `rule-gates` gains:
  - `session-recovery: {requires: spec-plan-workflow.enabled}`;
  - `root-cause-gate: {requires: dod.root-cause-required}`.
- `scripts/lib/rules.py::_rule_gate_satisfied` gains one branch for `dod.root-cause-required`,
  resolving `resolve_dod(config, agent_meta_root).get("root-cause-required", False)`. Unknown
  requirement strings stay fail-closed (`False`).
- New rules (no role names, no route tables):
  - `rules/1-generic/session-recovery.md` — session start reads a resume context (via the read-only
    rehydrate mode) before starting new plan work; an unfinished task is resumed at `next_task_ref`,
    never silently skipped or reordered.
  - `rules/1-generic/root-cause-gate.md` — before any fix, the root cause and prior attempts are
    evidenced; a symptom-level change does not satisfy the gate.

### IC-10 — Rule and snippet documentation surfaces

Documentation surfaces are updated so the runtime contract and the written contract cannot drift.

- `rules/1-generic/plan-ledger.md`: the review subsection states the two-stage task review
  (requirement fidelity first, quality second) and the round cap, and the ledger subsection states
  that plan checkboxes are updated by the writer after each task rather than only by hand. Wording
  uses pipeline/stage/pair ids, never role names or `roleA → roleB` chains, so the guard test in AC-26
  stays green.
- `snippets/orchestrator/checkpointing.md`: the session-start prose is aligned with the implemented
  read path — session start runs the read-only rehydrate path, the store format
  (`.meta-viz/checkpoints/<session>.json`) is the authoritative machine recovery source, and the
  manual `.meta-viz/checkpoint-<ts>.json` format stays readable for backward compatibility but is not
  written by the runtime. The existing `CheckpointStore.save_checkpoint` reference and the
  `current.md` sentence required by `tests/test_progress_file_documented.py` are preserved verbatim.
  **F6 alignment:** the "delete checkpoints older than 24h automatically (on next start)" promise is
  removed, because this specification does not wire rotation (G-05 is out of scope and IC-03 forbids
  auto-deletion); the retained Tier-A/Tier-B tokens
  (`tests/test_progress_file_documented.py` requires them) are explicitly marked as preserved.
  `rules/1-generic/plan-ledger.md`'s former "`execute_plan` remains out-of-scope" statement is
  updated to match this specification: `execute_plan` is now wired as the checkpoint/ledger writer
  (IC-06), while only the G-08 dispatcher backend remains out of scope.

### IC-11 — `scripts/lib/checkpoint_record.py` (new module) — production checkpoint writer

Minimal concrete production trigger for G-02/G-04 that does not depend on the G-08 dispatcher.

```python
MODE = "checkpoint"

def record_checkpoint(
    project_root: Path, config: Optional[dict], log: SyncLog, *,
    session_id: str,
    task_id: str,
    agent: str,
    status: str,
    task_description: str = "",
    plan_id: Optional[str] = None,
    status_summary: Optional[str] = None,
    next_step: Optional[str] = None,
) -> int: ...
def _handle_checkpoint(ctx) -> None: ...
```

- Builds `Checkpoint(task_id=..., agent=..., task_description=..., status=...,
  plan_id=plan_id, task_ref=make_task_ref(plan_id, task_id), status_summary=..., next_step=...)` and
  calls `CheckpointStore(project_root).save_checkpoint(session_id, checkpoint)`.
- Identity rule matches F1: `plan_id` comes from the explicit `--plan-id` value, or from
  `plan_identity.derive_plan_id(<plan path>)` when `--plan <path>` is supplied; when neither is given
  it is `None` (never random). `task_ref` follows from `make_task_ref`.
- CLI: `sync.py --checkpoint --session-id <id> --task <id> --agent <name>
  --status <completed|failed|timeout|in_progress> [--plan <path> | --plan-id <id>]
  [--description <text>] [--summary <text>] [--next-step <text>]`.
- Exit code `0` on a successful write, `1` on missing required arguments or an `OSError` from the
  store. The mode mutates only under `.meta-viz/checkpoints/` (plus the store's existing
  `progress/current.md` write-through). It never dispatches, never touches the plan.
- Registered in `scripts/sync.py` alongside `--rehydrate` and `--update-plan-ledger`.

**Production trigger inventory and G-08 coupling (F3):**

| Trigger | Kind | Production effect | Depends on G-08 |
|---|---|---|---|
| `--rehydrate` (IC-04) | read | Calls `list_sessions` / `get_last_checkpoint` / `get_completed_steps`; emits a resume context | no |
| `--checkpoint` (IC-11) | write | Calls `CheckpointStore.save_checkpoint`; creates recovery data | no |
| `--update-plan-ledger` (IC-05) | write | Updates plan checkboxes / first `Status:` line | no |
| drift check in `--validate-spec-plan` (IC-07) | read | Compares ledger against checkpoints | no |
| in-harness per-entry checkpointing in `execute_plan` (IC-06) | write | Automatic per-task checkpoints during a barrier | **yes** |

The last row is the only G-08-dependent path: `execute_plan` has no production dispatcher in this
repository today, so its automatic checkpoint/ledger write is exercised by tests and by any future
G-08 dispatcher. This is a documented limitation and coupling, not a silent deferral — G-02 and G-04
are already effective through the three CLI triggers above.

## Datenfluss

### Flow A — Session start → re-hydrate (G-02)

```
session start
  → orchestrator reads session-recovery rule (rule-gate: spec-plan-workflow.enabled)
  → runs read-only rehydrate mode (IC-04)
      → CheckpointStore.list_sessions()                      (production caller)
      → get_last_checkpoint() / get_completed_steps() per session
      → legacy .meta-viz/checkpoint-*.json merged (read-only)
      → find_resumable_session() → newest unfinished source
      → build_resume_context()
          → derive plan_id (IC-01) → locate plan in docs/plans
          → parse_plan_ledger() + completed_task_refs
          → next_task_ref = first open ledger task
  → print resume context; orchestrator proposes resuming at next_task_ref
  → no write, no dispatch
```

### Flow B — Task run → checkpoint + ledger write (G-02, G-03, G-04)

```
Automatic path (only path coupled to G-08, see IC-11):
execute_plan(plan, dispatcher, store=..., session_id=..., plan_id=<explicit>, ledger_path=...)
  → dispatcher returns BarrierEntry list
  → per entry: archive raw output (existing) → checkpoint_ref set
  → per entry (write_checkpoints=True):
        checkpoint_from_barrier_entry(entry, plan_id)
           → plan_id = explicit plan_id argument (None when not supplied — F1)
           → task_ref = make_task_ref(plan_id, entry.task_id)  (None when plan_id is None)
        → CheckpointStore.save_checkpoint(session_id, cp)
           → .meta-viz/checkpoints/<session>.json + .meta-viz/progress/current.md
  → aggregate BarrierResult.status (unchanged; its plan_id may still be the KIND-uuid fallback)
  → if ledger_path:
        plan_ledger.update_plan_ledger(plan, {<task>: True for successes})
        plan_ledger.set_plan_status(... complete | IN PROGRESS)
  → return BarrierResult

Standing production path (no G-08 dependency, IC-11):
sync.py --checkpoint --session-id S --task task-N --agent A --status completed \
        (--plan docs/plans/<plan>.md | --plan-id P)
  → plan_id = explicit --plan-id, or derive_plan_id(--plan), else None
  → CheckpointStore.save_checkpoint(S, Checkpoint(plan_id=P, task_ref=P#task-N, ...))
```

### Flow C — Consistency → drift check (G-04)

```
sync.py --validate-spec-plan
  → check_spec_plan_workflow()
      → bundle["consistency-noop"] false → return []          (existing no-op)
      → required sections / placeholders / traceability / approval / ledger format (existing)
      → _check_ledger_drift():
            per plan: derive_plan_id() → find_sessions_for_plan()
            if no sessions: skip
            parse_task_ledgers() vs get_completed_steps()
            → WARNING spec_plan_ledger_drift (ledger ahead / ledger behind / status mismatch)
      → _check_plan_graph() with hyphen-aware TASK_HEADER_RE
  → exit 0 (clean/no artifacts) or 1 (any finding)             (existing contract)
  → note (F4): changed-files-scoped — only plans present in _changed_files() are drift-checked
```

### Flow D — Bugfix with root-cause gate (G-10)

```
quick-fix:  root-cause is skipped when dod.root-cause-required == false
bugfix:     triage → root-cause (mandatory) → fix → review → document
            root-cause must evidence root_cause + prior_attempts
            → otherwise the fix stage is not entered; step returns to root-cause
```

## Acceptance Criteria

All criteria are testable. `python3 scripts/sync.py --validate` / the automated test suite is the
observable harness unless stated otherwise.

- **AC-01** — Given `### Task task-1: Title`, `plan_identity.TASK_HEADER_RE` group 1 is `task-1`;
  given `### Task 1 — Title`, group 1 is `1` and group 2 is `Title`; given `### Task 1 - Title`,
  group 1 is `1`.
- **AC-02** — Given a plan file without `plan-id:`, `derive_plan_id` returns the slug of the file
  stem; given a plan with `> plan-id: my-plan`, it returns `my-plan`; both results match
  `PLAN_ID_RE`. Calling it twice on the same input returns the same value.
- **AC-03** — Given `plan_id="p"` and `task_id="task-3"`, `make_task_ref` returns `"p#task-3"`;
  with `plan_id=None` it returns `None`.
- **AC-04** — Given an existing checkpoint JSON without `plan_id`/`task_ref` keys,
  `Checkpoint.from_dict` succeeds and yields `plan_id is None`; the four hard-required fields are
  still enforced.
- **AC-05** — Given a session with a checkpoint created with `plan_id="p"`, `task_id="task-3"`,
  `CheckpointStore.get_checkpoint_for_task(session, "p#task-3")` returns that checkpoint;
  `find_sessions_for_plan("p")` contains the session; both return empty/`None` for unknown input.
- **AC-06** — Given a corrupt session JSON and an unrelated valid session,
  `find_sessions_for_plan` skips the corrupt file without raising.
- **AC-07** — Given a plan with two checkboxes in one task block, `plan_ledger.update_plan_ledger`
  with `{"task-1": True}` produces `parse_plan_ledger(path)["checked"] == 2`, leaves other tasks
  untouched, and the file on disk equals the in-memory result (atomic single write).
- **AC-08** — Given a plan with leading `- [x]` all over, `update_plan_ledger(path, {"task-2": False})`
  sets exactly the `task-2` block checkboxes back to `- [ ]`; `parse_plan_ledger(path)["complete"]`
  is `False` afterwards.
- **AC-09** — Given a plan where all task checkboxes are closed through the writer,
  `parse_plan_ledger(path)["complete"] is True`; the status header read by the parser equals the
  value passed to `set_plan_status`.
- **AC-10** — Given a missing plan file, `update_plan_ledger` returns `ok=False`,
  `reason="plan-not-found"` and writes nothing; given an unknown task id, the id appears in
  `unmatched` while known tasks are still written.
- **AC-11** — Given `execute_plan(..., plan_id="p", store=store, session_id="s")` with two successful
  entries, `store.load_session("s")` contains two checkpoints, each with `plan_id == "p"` and
  `task_ref == "p#<task-id>"`.
- **AC-12** — Given `execute_plan(..., store=store, session_id="s", write_checkpoints=False)`, no
  session JSON is created, while raw output archiving and `checkpoint_ref` behave exactly as before.
- **AC-13** — Given `execute_plan(..., store=store, session_id="s")` without a `plan_id` argument (and
  task ids such as `t1`, `t2`), the run completes and every written checkpoint has
  `plan_id is None` and `task_ref is None` (F1: no random/UUID-derived identity), without raising.
  `BarrierResult.plan_id` may still carry the `KIND-<uuid>` fallback in the same run.
- **AC-14** — Given `execute_plan(..., ledger_path=<plan>)` with all tasks successful, the plan's
  leading checkboxes are closed and its first `Status:` line is `complete`; with a failing entry, the
  affected task stays open and the status is not `complete`.
- **AC-15** — Given a store session for a plan where the ledger marks a task done but no `completed`
  checkpoint exists, `check_spec_plan_workflow` emits one `spec_plan_ledger_drift` WARNING for that
  plan; given no checkpoint sessions, it emits none.
- **AC-16** — Given a plan where a `completed` checkpoint exists but the ledger task is open, the
  drift check emits `spec_plan_ledger_drift` (WARNING); exit code of `--validate-spec-plan` is `1`.
- **AC-17** — Given a legacy `.meta-viz/checkpoint-<ts>.json` file, `resolve_recovery_sources`
  returns one `RecoverySource` with `source_format == "legacy"`; given a store session with the same
  id, the store source wins and appears once.
- **AC-18** — Given a session whose last checkpoint is `completed` and a complete plan ledger,
  `find_resumable_session` returns `None`; given an unfinished last checkpoint, it returns that
  source (newest first among several).
- **AC-19** — Given a resolvable session, `build_resume_context` returns a context whose
  `next_task_ref` is the first ledger task absent from `completed_task_refs`; `render_resume_context`
  contains the session id and no role name.
- **AC-20** — `python3 scripts/sync.py --rehydrate` with no resumable session terminates with exit
  code `0` and prints an explicit "no unfinished session" note; it writes no file.
- **AC-21** — In `concept-driven-dev`, the canonical stage order is exactly
  `explore → classify → specify → review → approve → plan → implement → review-req → review-quality
  → validate` (10 stages), both review stages use `mode: loop` with a `loop_ref`, and
  `validate_pipelines` returns no errors for the shipped configuration. The pytest assertion on the
  exact list is AC-32.
- **AC-22** — Given a simulated `task-review.max-rounds` below the sum of the two review pairs'
  `max_iterations`, `validate_pipelines` returns an error naming the pipeline; with
  `max-rounds: 4` and `2 + 2` iterations it returns no error.
- **AC-23** — In `bugfix`, a `root-cause` stage exists between `triage` and `fix` with
  `mode: sequential`; in `quick-fix` it exists with `condition: {dod_flag: root-cause-required}`.
- **AC-24** — Given `dod.root-cause-required: false`, `rules.collect_rule_sources` does not emit the
  `root-cause-gate` rule; given `true`, it emits it. An unknown gate requirement still fails closed.
- **AC-25** — With `root-cause-required: true` resolved, `resolve_dod` returns the flag and the
  `stageItem.condition` schema accepts `dod_flag`/`payload_flag` without validation errors.
- **AC-26** — `tests/test_no_role_routes_in_templates.py` passes unchanged: no route column,
  `roleA → roleB` chain, handoff sentence with a role, or role inside `NEXT:` is added to
  `agents/1-generic/*` or `rules/1-generic/*`.
- **AC-27** — `tests/test_spec_plan_group_consistency.py` passes with `recovery-rehydrate` in
  `ALL_ASPECTS`; the consumer `scripts/lib/recovery.py::find_resumable_session` exists, mentions a
  token of `spec-plan-workflow.recovery.rehydrate`, and the fallback group matches the YAML.
- **AC-28** — New scenario `59-progress-ledger` in `tests/scenarios/` (the id `51-` is already taken
  by `51-spec-plan-disabled`, hence the renumber) reports PASS via `tests/scenarios/run.sh`
  (`dry_rc=0 && sync_rc=0 && val_rc=0 && assert_rc=0`) and asserts: checkpoint written by
  `execute_plan`, ledger updated, drift warning emitted for a synthetic mismatch, rehydrate returns
  the expected `next_task_ref`. A matching row is added to `tests/scenarios/registry.md`.
- **AC-29** — All new modules import under Python 3.9 and use no PEP 604 annotations; `python3
  scripts/sync.py --validate` and `python3 scripts/consistency-check.py` (exit 0) stay green.
- **AC-30** — The recovery path and the writer are provider-agnostic: no `if provider ==` branch and
  no provider literal is introduced in the new/changed modules (grep-level check).
- **AC-31** — `rules/1-generic/plan-ledger.md` names the two-stage review and the writer obligation
  without introducing a role route (guard test green), and its former
  "`execute_plan` remains out-of-scope" statement is replaced by the IC-06 wiring (only the G-08
  dispatcher backend stays out of scope). `tests/test_progress_file_documented.py` stays green after
  the `snippets/orchestrator/checkpointing.md` update: the `CheckpointStore.save_checkpoint`
  reference, the `current.md` sentence and the Tier-A/Tier-B tokens are preserved, while the
  "delete checkpoints older than 24h automatically" promise is removed.
- **AC-32** — `tests/test_orchestration_contract.py::test_concept_driven_dev_spec_plan_phase_order`
  (lines 757–775) is updated to assert the 10-stage canonical list from AC-21/IC-08 and passes under
  `pytest`; the previous 8-stage assertion is removed.
- **AC-33** — `python3 scripts/sync.py --checkpoint --session-id S --task task-1 --agent developer
  --status completed --plan-id p` exits `0` and `CheckpointStore.load_session("S")` contains a
  checkpoint with `plan_id == "p"` and `task_ref == "p#task-1"`; omitting both `--plan` and
  `--plan-id` yields `plan_id is None`; a missing required argument exits `1` and writes nothing.
- **AC-34** — Drift is deliberately changed-files-scoped: a plan whose ledger/checkpoint state
  mismatches but which is not in `_changed_files()` produces no `spec_plan_ledger_drift` finding,
  while the same plan being changed does (documented in IC-07).

## Offene Fragen

Each item states the recommended decision and what remains genuinely undecided. No implementation
starts while an item is open and blocking.

1. **Round-cap default (G-09).** Recommended `2 + 2 = 4` total (mirrors the existing bugfix loop).
   Open: whether the cap should be per pipeline override only or also a global ceiling. Blocking for
   AC-22's exact constant only.
2. **Drift severity (G-04).** Recommended `WARNING` unconditionally, so activating the check cannot
   break existing plans in CI. Open: whether `spec-plan-traceability: true` should escalate "ledger
   behind checkpoints" to `ERROR`.
3. **Plan id for legacy plans (G-03).** Recommended fallback to the file-stem slug with no file
   rename. Open: whether existing plans should be backfilled with an explicit `plan-id:` field.
4. **CLI placement (G-02/G-04).** Decided (F3): three production triggers as `sync.py` subflags —
   `--rehydrate` (read), `--checkpoint` (write), `--update-plan-ledger` (write), matching
   `--validate-spec-plan`. Open: whether the two mutating writers should later move to a separate
   script to keep `sync.py` read-only.
5. **Config placement (G-02).** Recommended `spec-plan-workflow.recovery` (rides the existing seed);
   open whether a top-level `recovery` block is preferable for non-spec-plan use.
6. **Legacy checkpoint lifecycle (G-02/G-06).** Decided (F6): read-only tolerance, no auto-delete;
   the snippet's 24h auto-delete promise is removed and deletion stays with G-05's rotation wiring
   (out of scope). Open: when the legacy format is formally declared deprecated.
7. **Root-cause stage role (G-10).** Recommended `bug-feature-analyzer` for the mandatory analysis
   stage, keeping `principal-developer` as escalation only. Open: whether a dedicated analysis role
   is warranted.
8. **Drift session scope.** Recommended comparing against **all** sessions linked to the plan id.
   Open: whether only the newest session should count once multiple dispatches share one plan.
9. **`max-age-seconds` default for rehydrate (G-02).** Recommended `86400` (matches the documented
   cleanup horizon). Open: whether stale-but-unfinished sessions should be surfaced anyway.

## Trace-Anker

- `spec-id: SPEC-PROGRESS-LEDGER-2026-09-13` (plans reference this value via their `**Spec:**` field).
- Gap mapping:

  | Gap | Interface contracts | Acceptance criteria |
  |---|---|---|
  | G-02 | IC-03, IC-04, IC-06, IC-11 | AC-11, AC-12, AC-13, AC-17, AC-18, AC-19, AC-20, AC-33 |
  | G-03 | IC-01, IC-02, IC-07 | AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-13 |
  | G-04 | IC-05, IC-06, IC-07, IC-11 | AC-07, AC-08, AC-09, AC-10, AC-14, AC-15, AC-16, AC-33, AC-34 |
  | G-09 | IC-08 | AC-21, AC-22, AC-32 |
  | G-10 | IC-08, IC-09 | AC-23, AC-24, AC-25 |
  | Guards / test impacts | IC-09, IC-10, IC-11 | AC-26, AC-27, AC-28, AC-29, AC-30, AC-31, AC-32, AC-33, AC-34 |

- Source analysis: `docs/process-capability-gaps.md` (sections 2.2, 2.3, 4, 5).
- Binding frame: `config/spec-plan-groups.yaml`, `scripts/lib/dod.py::SPEC_PLAN_WHEN_OPERANDS`,
  `tests/test_spec_plan_group_consistency.py::ALL_ASPECTS`,
  `tests/test_no_role_routes_in_templates.py`.
