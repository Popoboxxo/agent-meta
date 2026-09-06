"""Orchestration plan, barrier contract, and dispatch seam (issue #265).

agent-meta owns PLAN + CONTRACT + VALIDATION. Live sub-agent dispatch stays a
harness concern, injected via the ``Dispatcher`` protocol — the framework
never calls a provider API itself, and no code here halts an LLM generation
loop (see docs/spikes/2026-09-06-issue-265-async-fanout-spike.md §1.1/§7 and
the harness-dependency section of the #265 report: a synchronous tool call IS
the hard interrupt; this module defines what that tool receives and returns).

Usage:
    from scripts.lib.orchestration import FanoutPlan, validate_plan, execute_plan

    plan = FanoutPlan(kind="fanout", tasks=(...))
    errors = validate_plan(plan, max_parallel=4, file_overlap=check_file_overlap)
    if errors:
        ...                       # fail fast before any dispatch
    result = execute_plan(plan, dispatcher=my_harness_dispatcher)
    print(render_barrier_result(result))

Boundary (deliberate, spike §3): no HTTP/API client, no subprocess of a
provider CLI, no provider-name branch. Provider differences live in
``config/provider-capabilities.yaml`` (``fanout_mechanism`` /
``barrier_collect``) and are read via
``scripts.lib.delegation_syntax.DelegationSyntaxEngine``.
"""
from __future__ import annotations

import re
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal, Protocol

from .checkpoint import CheckpointStore
from .file_affinity import check_file_overlap
from .roles import _TIER_SEQUENCE

__all__ = [
    "BARRIER_ENTRY_MARKER",
    "BarrierEntry",
    "BarrierResult",
    "Dispatcher",
    "FanoutPlan",
    "FanoutTask",
    "check_plan_file_overlap",
    "execute_plan",
    "find_dependency_errors",
    "render_barrier_result",
    "summarize_result",
    "validate_plan",
]

# ---------------------------------------------------------------------------
# Shared contract constants (single source of truth — see
# scripts/lib/consistency/fanout_contracts.py for the drift check)
# ---------------------------------------------------------------------------

# §7 result wrapper marker emitted by render_barrier_result and referenced by
# agents/1-generic/orchestrator.md (backward-compatible format).
BARRIER_ENTRY_MARKER = "||| agent="

# Structured exit-summary marker in worker output (#267 Summarization-as-a-
# Contract): "SUMMARY: ..." line preferred over prose extraction.
_SUMMARY_MARKER_RE = re.compile(r"^[ \t]*SUMMARY:[ \t]*(.*)$", re.IGNORECASE | re.MULTILINE)

# A following "KEY: value" style marker ends a multi-line SUMMARY block.
_SECTION_MARKER_RE = re.compile(r"^[ \t]*[A-Z][A-Z_]{2,}:")

_FALLBACK_SUMMARY_MAX_CHARS = 400


# ---------------------------------------------------------------------------
# Plan structures (generation-time contract — what the orchestrator issues)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FanoutTask:
    """One sub-agent dispatch inside a fanout/parallel-group plan.

    ``files_touched`` feeds the #266 static overlap check (projected to the
    ``file_affinity.check_file_overlap`` dict-input shape). ``handoff``
    carries the A2A envelope fragment (schemas/a2a-handoff.schema.json —
    with ``batch: true`` the same fields live in each payload-array entry).
    ``dependencies`` lists task_ids inside the SAME plan that must complete
    first (A2A batch dependency edges; cycle/deadlock detection input).
    """

    task_id: str                    # local to the plan (A2A batch task_id)
    target_agent: str
    prompt: str
    files_touched: tuple[str, ...] = ()      # #266 input
    tier_override: str | None = None         # issue #346 semantics, pre-validated
    handoff: dict | None = None              # full A2A envelope (optional)
    dependencies: tuple[str, ...] = ()       # in-plan prerequisite task_ids


@dataclass(frozen=True)
class FanoutPlan:
    """A validated-in-advance dispatch plan for FANOUT or PARALLEL_GROUP.

    One plan models ONE barrier group. Batching across several barriers
    (more tasks than ``max_parallel``) is the caller's concern — the dry-run
    engine emits one plan per FANOUT batch.
    """

    kind: Literal["fanout", "parallel_group", "sequential"]
    tasks: tuple[FanoutTask, ...]
    barrier: bool = True                    # False = fire-and-forget (explicitly discouraged)
    max_parallel: int = 2                   # mirrors project.yaml max-parallel-agents


# ---------------------------------------------------------------------------
# Barrier result structures (#267-compatible contract)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BarrierEntry:
    """One task's outcome at the barrier — the ONLY orchestrator-facing data.

    ``summary`` carries the bounded 2-3 sentence exit summary (#267
    Summarization-as-a-Contract); ``checkpoint_ref`` points at the full raw
    output inside ``.meta-viz/checkpoints/<session>/``. ``raw_output`` is a
    transient transport field for the dispatcher→checkpoint hand-off: it is
    consumed (and cleared) by :func:`execute_plan` when BOTH a
    ``CheckpointStore`` and a ``session_id`` are given, and never rendered
    by :func:`render_barrier_result`.
    """

    task_id: str
    agent: str
    status: Literal["success", "failed", "timeout"]
    summary: str
    checkpoint_ref: str | None = None       # e.g. ".meta-viz/checkpoints/<session>/<file>.txt"
    overlap_warnings: tuple[str, ...] = ()  # #266 conflicts observed during execution
    duration_s: float = 0.0
    raw_output: str | None = None           # transient; see class docstring


@dataclass(frozen=True)
class BarrierResult:
    """Aggregated barrier outcome — injected to the orchestrator as ONE tool-response."""

    plan_id: str
    status: Literal["success", "partial", "failed", "timeout"]
    entries: tuple[BarrierEntry, ...]
    total_duration_s: float = 0.0


# ---------------------------------------------------------------------------
# Dispatch seam — the ONLY place the harness plugs in
# ---------------------------------------------------------------------------

class Dispatcher(Protocol):
    """Harness-side async dispatch adapter (spike §7 bridge variants).

    Implementations: stub (tests / dry-run), SubagentBarrierRuntime-based
    subprocess bridge (future MCP barrier tool), in-harness native batch.
    Must return one :class:`BarrierEntry` per task in task order — barrier
    semantics are deterministic. Raw worker output may ride in
    ``BarrierEntry.raw_output`` for #267 archiving.
    """

    def dispatch(self, tasks: Sequence[FanoutTask]) -> Sequence[BarrierEntry]: ...


# ---------------------------------------------------------------------------
# Static plan validation — no agents, no I/O (file_overlap aside)
# ---------------------------------------------------------------------------

def find_dependency_errors(tasks: Sequence[FanoutTask]) -> list[str]:
    """Graph-level plan checks: empty plan, duplicate ids, deadlocks, cycles.

    Public because the dry-run engine validates the whole task graph BEFORE
    generating any dispatch plan (fail-closed: cycle → sequential fallback).

    Checks (in order):
    1. Empty plan.
    2. Duplicate task_ids.
    3. Dangling dependency (references a task_id outside the plan) —
       reported as an unresolvable wait, i.e. a deadlock by construction.
    4. Cycles over ``FanoutTask.dependencies`` (Kahn topological sort) —
       remaining nodes after peeling form the cycle set.
    """
    errors: list[str] = []
    if not tasks:
        return ["plan contains no tasks"]

    seen: dict[str, int] = {}
    for position, task in enumerate(tasks):
        if task.task_id in seen:
            errors.append(
                f"duplicate task_id '{task.task_id}' "
                f"(first defined at position {seen[task.task_id] + 1}, "
                f"duplicate at position {position + 1})"
            )
        else:
            seen[task.task_id] = position

    known = set(seen)
    for task in tasks:
        for dep in task.dependencies:
            if dep == task.task_id:
                errors.append(f"task '{task.task_id}' depends on itself (cycle of length 1)")
            elif dep not in known:
                errors.append(
                    f"deadlock: task '{task.task_id}' depends on unknown "
                    f"task_id '{dep}' (not part of this plan) — unresolvable wait"
                )

    # Kahn's algorithm: peel nodes whose dependencies are all satisfied.
    # Pure self-dependencies are filtered out here — they are already
    # reported above via the dedicated "depends on itself" message and
    # would never be peeled anyway.
    remaining_deps = {
        task.task_id: {d for d in task.dependencies if d in known and d != task.task_id}
        for task in tasks
    }
    satisfied = [tid for tid, deps in remaining_deps.items() if not deps]
    while satisfied:
        current = satisfied.pop()
        for tid, deps in remaining_deps.items():
            if current in deps:
                deps.remove(current)
                if not deps:
                    satisfied.append(tid)
    cyclic = sorted(tid for tid, deps in remaining_deps.items() if deps)
    if cyclic:
        errors.append(
            "cycle detected over task dependencies: " + " -> ".join(cyclic) +
            " — FANOUT members must be mutually independent"
        )
    return errors


def validate_plan(
    plan: FanoutPlan,
    *,
    max_parallel: int | None = None,
    file_overlap: Callable[[list[dict[str, Any]]], Any] | dict[str, Any] | None = None,
) -> list[str]:
    """Static plan validation — no agents, no I/O. Returns error strings.

    Args:
        plan: The dispatch plan to validate.
        max_parallel: Parallel-dispatch ceiling (mirrors project.yaml
            ``max-parallel-agents``). ``None`` (default) takes the ceiling
            from the plan itself (``FanoutPlan.max_parallel``) — the plan is
            the single source of truth, so this function layers no
            conflicting default on top of it. An explicit value overrides
            the plan's ceiling (e.g. a harness re-validating under a
            stricter limit). Exceeding the effective ceiling is rejected
            here — batching into several barrier groups happens upstream
            (HITL rule: FANOUT > N requires confirmation).
        file_overlap: Either a PRECOMPUTED ``#266`` result dict
            (``{"safe": [...], "conflict": [(task_a, task_b, [files]), ...]}``,
            e.g. from :func:`check_plan_file_overlap`) or a callable that
            receives the plan's tasks projected to ``file_affinity`` dict
            inputs and returns such a dict (or a flat ``list[str]`` of
            conflict descriptions). ``None`` skips the check — it NEVER
            silently claims file-safety.

    Checks (in order):
    1. Empty plan / duplicate task_ids / deadlocks / cycles (via
       :func:`find_dependency_errors`).
    2. Over-commitment: ``len(tasks) > effective max_parallel`` (plan's own
       ceiling unless overridden) — split into several barrier groups
       before dispatch.
    3. File overlap via the injected #266 seam; conflicts mean the plan must
       be rejected or the affected tasks sequentialized BEFORE dispatch —
       static analysis, not an LLM guess.
    4. ``tier_override`` present without a valid abstract tier name (coarse
       check; full guardrails live in
       ``DelegationSyntaxEngine.resolve_tier_override`` — no duplicated
       policy).

    Returns:
        Human-readable error strings; an empty list means the plan is valid.
    """
    errors = find_dependency_errors(plan.tasks)
    if errors:
        return errors  # graph is broken — later checks would produce noise

    effective_max_parallel = plan.max_parallel if max_parallel is None else max_parallel
    if len(plan.tasks) > effective_max_parallel:
        errors.append(
            f"over-commitment: plan has {len(plan.tasks)} tasks but "
            f"max_parallel is {effective_max_parallel} — batch into multiple barrier "
            "groups (FANOUT > max_parallel requires confirmation)"
        )

    if file_overlap is not None:
        if callable(file_overlap):
            overlap = file_overlap(_project_tasks_for_overlap(plan.tasks))
        else:
            overlap = file_overlap
        errors.extend(_overlap_errors(overlap))

    for task in plan.tasks:
        if task.tier_override is not None and task.tier_override not in _TIER_SEQUENCE:
            errors.append(
                f"task '{task.task_id}': invalid tier_override "
                f"'{task.tier_override}' — must be one of {', '.join(_TIER_SEQUENCE)}"
            )
    return errors


def check_plan_file_overlap(
    plan: FanoutPlan,
    project_root: Path | str | None = None,
) -> dict[str, Any]:
    """Run the #266 static file-affinity analysis over a plan's tasks.

    Single seam between plans and ``file_affinity.check_file_overlap``:
    tasks are projected to the module's dict-input shape
    (``{"id", "task", "files"}``) so ``FanoutTask.prompt`` / prompt-referenced
    files participate exactly like the duck-typed SubTask inputs. Returns the
    ``#266`` result dict ``{"safe": [...], "conflict": [...]}`` verbatim.
    Callers typically feed the result back into :func:`validate_plan`.
    """
    return check_file_overlap(_project_tasks_for_overlap(plan.tasks), project_root)


def _project_tasks_for_overlap(tasks: Sequence[FanoutTask]) -> list[dict[str, Any]]:
    """Project plan tasks to the #266 dict-input shape."""
    return [
        {
            "id": task.task_id,
            "task": task.prompt,
            "files": list(task.files_touched),
        }
        for task in tasks
    ]


def _overlap_errors(overlap: Any) -> list[str]:
    """Convert a #266 overlap result (dict or flat list) into error strings.

    Fail-closed: an unsupported result shape (non-dict, non-list, or a dict
    without the ``conflict`` key) is an error, never a silent pass.
    """
    if isinstance(overlap, dict) and "conflict" in overlap:
        conflicts = overlap.get("conflict") or []
        errors: list[str] = []
        for entry in conflicts:
            try:
                task_a, task_b, files = entry
            except (TypeError, ValueError):
                errors.append(
                    f"file-overlap check returned malformed conflict entry: {entry!r}"
                )
                continue
            errors.append(
                f"file overlap between '{task_a}' and '{task_b}': "
                f"{', '.join(str(f) for f in files)} — sequentialize or merge "
                "the affected tasks before dispatch"
            )
        return errors
    if isinstance(overlap, list):
        return [str(item) for item in overlap]
    return [
        f"file-overlap check returned unsupported result type "
        f"{type(overlap).__name__} — treating plan as unvalidated"
    ]


# ---------------------------------------------------------------------------
# Execution — barrier aggregation over the injected dispatcher
# ---------------------------------------------------------------------------

def execute_plan(
    plan: FanoutPlan,
    dispatcher: Dispatcher,
    *,
    store: CheckpointStore | None = None,
    session_id: str | None = None,
    plan_id: str | None = None,
) -> BarrierResult:
    """Execute a plan through the injected dispatcher with BARRIER semantics.

    The dispatcher owns the real async dispatch (harness-side). This function
    guarantees the barrier contract around it:

    - deterministic entry order = plan task order (dispatcher returns may be
      re-ordered defensively; extras are appended after the known tasks),
    - status aggregation (see below),
    - #267 archiving: when ``store`` AND ``session_id`` are given, per-entry
      ``raw_output`` is persisted via ``CheckpointStore.save_raw_output``
      and the entry rides on with only ``checkpoint_ref`` set. ``raw_output``
      is consumed (persisted + cleared) ONLY when both are passed — if
      either is missing, it is neither persisted nor cleared and stays on
      the entry (transient; never rendered by ``render_barrier_result``).

    Status aggregation (deterministic, mirrors the tested semantics of
    ``runtime.SubagentBarrierRuntime``):
    - any entry ``timeout`` → ``"timeout"``
    - all entries ``failed`` → ``"failed"``
    - some ``failed`` (with successes present) → ``"partial"``
    - otherwise → ``"success"``
    """
    resolved_plan_id = plan_id or f"{plan.kind.upper()}-{uuid.uuid4().hex[:8]}"
    started = time.perf_counter()

    returned = list(dispatcher.dispatch(plan.tasks))
    by_task_id: dict[str, BarrierEntry] = {}
    extras: list[BarrierEntry] = []
    for entry in returned:
        if entry.task_id in by_task_id:
            extras.append(entry)  # defensive: unexpected duplicate dispatch id
        else:
            by_task_id[entry.task_id] = entry
    ordered = [by_task_id.pop(task.task_id) for task in plan.tasks if task.task_id in by_task_id]
    ordered.extend(by_task_id.values())   # missing-from-plan entries keep arrival order
    ordered.extend(extras)

    resolved_entries: list[BarrierEntry] = []
    for entry in ordered:
        if store is not None and session_id and entry.raw_output:
            archive_path = store.save_raw_output(
                session_id, entry.task_id, entry.agent, entry.raw_output
            )
            try:
                ref = archive_path.relative_to(store.project_root).as_posix()
            except ValueError:
                ref = str(archive_path)
            entry = replace(entry, checkpoint_ref=ref, raw_output=None)
        resolved_entries.append(entry)

    statuses = [entry.status for entry in resolved_entries]
    if "timeout" in statuses:
        status: Literal["success", "partial", "failed", "timeout"] = "timeout"
    elif statuses and all(s == "failed" for s in statuses):
        status = "failed"
    elif "failed" in statuses:
        status = "partial"
    else:
        status = "success"

    return BarrierResult(
        plan_id=resolved_plan_id,
        status=status,
        entries=tuple(resolved_entries),
        total_duration_s=time.perf_counter() - started,
    )


# ---------------------------------------------------------------------------
# #267 synergy — bounded summary extraction
# ---------------------------------------------------------------------------

def summarize_result(raw_output: str, *, max_sentences: int = 3) -> str:
    """Extract the worker exit summary (#267 Summarization-as-a-Contract).

    Strategy:
    1. Structured marker first: the ``SUMMARY:`` line of the worker's
       standard output contract. A multi-line SUMMARY block is collected
       until a blank line or the next ``KEY:``-style section marker.
    2. Fallback: the first ``max_sentences`` sentences of the output
       (bounded to a soft 400-char cap so a marker-less blob cannot flood
       the orchestrator context).

    Pure string processing — never touches a checkpoint file.
    """
    if not raw_output:
        return ""
    match = _SUMMARY_MARKER_RE.search(raw_output)
    if match:
        lines: list[str] = []
        inline = match.group(1).strip()
        if inline:
            lines.append(inline)
        # match always ends at the SUMMARY line's end, so the first
        # splitlines() element is that line's terminator, not a separate
        # blank line — drop it before scanning the block.
        following = raw_output[match.end():].splitlines()
        if following and following[0] == "":
            following = following[1:]
        for line in following:
            stripped = line.strip()
            if not stripped or _SECTION_MARKER_RE.match(line):
                break
            lines.append(stripped)
        return " ".join(lines)
    # Fallback: first N sentences, bounded.
    text = " ".join(raw_output.split())
    sentences = re.split(r"(?<=[.!?])\s+", text)
    summary = " ".join(sentences[:max_sentences]).strip()
    if len(summary) > _FALLBACK_SUMMARY_MAX_CHARS:
        summary = summary[:_FALLBACK_SUMMARY_MAX_CHARS].rstrip() + "…"
    return summary


# ---------------------------------------------------------------------------
# Rendering — the single orchestrator-facing tool-response block
# ---------------------------------------------------------------------------

def render_barrier_result(result: BarrierResult) -> str:
    """Render the barrier outcome as ONE orchestrator-facing text block.

    Backward-compatible with orchestrator.md §7 (issue #265): the
    ``||| agent=<name> result_key=<key> |||`` wrapper is preserved, the
    ``status=`` field is added, and the closing "[N] agents completed" line
    is emitted. ``raw_output`` is never rendered — bulk output lives behind
    ``checkpoint_ref`` (#267). Pure formatting — no I/O.
    """
    lines = [f"BARRIER {result.plan_id}: {result.status}"]
    for entry in result.entries:
        lines.append(
            f"{BARRIER_ENTRY_MARKER}{entry.agent} result_key={entry.task_id} "
            f"status={entry.status} |||"
        )
        if entry.summary:
            lines.append(entry.summary)
        if entry.checkpoint_ref:
            lines.append(f"Full output: {entry.checkpoint_ref}")
        for warning in entry.overlap_warnings:
            lines.append(f"Overlap warning: {warning}")
    lines.append(f"[{len(result.entries)}] agents completed")
    return "\n".join(lines)
