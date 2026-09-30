"""Plan-ledger <-> checkpoint drift check (IC-07, G-04).

Read-only comparison of a plan's human-readable ledger (per-task checkbox
state plus the ``Status:`` header) against the machine-readable
:class:`~lib.checkpoint.CheckpointStore`. Findings use the dedicated code
``spec_plan_ledger_drift``.

Scope (F4): the caller passes only the plans already selected by the
validator's ``changed_files`` filter; this module never force-includes a plan
that is linked to a checkpoint session. The check is provider-agnostic and
performs no writes.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .report import Finding, Severity
from ..plan_identity import derive_plan_id, make_task_ref, normalize_task_id

if TYPE_CHECKING:
    from ..checkpoint import CheckpointStore

_FINDING = "spec_plan_ledger_drift"


def _severity(raw) -> Severity:
    """Resolve the configured severity, defaulting to ``WARNING`` (M2)."""
    if isinstance(raw, Severity):
        return raw
    if isinstance(raw, str):
        try:
            return Severity(raw.strip().upper())
        except ValueError:
            return Severity.WARNING
    return Severity.WARNING


def _enabled(ledger_drift) -> bool:
    """Drift is opt-out: only an explicit ``enabled: false`` disables it (M2)."""
    return not (
        isinstance(ledger_drift, dict)
        and ledger_drift.get("enabled") is False
    )


def _rel(project_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _task_id_from_ref(task_ref: str) -> str:
    return task_ref.split("#", 1)[1] if "#" in task_ref else task_ref


def _completed_task_ids(
    store: "CheckpointStore", sessions: list[str], plan_id: str,
) -> set[str]:
    """Normalized task ids of ``completed`` checkpoints belonging to ``plan_id``."""
    completed: set[str] = set()
    for session_id in sessions:
        for checkpoint in store.get_completed_steps(session_id):
            task_ref = checkpoint.task_ref or make_task_ref(
                checkpoint.plan_id, checkpoint.task_id,
            )
            if not task_ref:
                continue
            if checkpoint.plan_id == plan_id or task_ref.startswith(plan_id + "#"):
                completed.add(
                    normalize_task_id(_task_id_from_ref(task_ref))
                )
    return completed


def check_ledger_drift(
    project_root: Path,
    plans: list[Path],
    texts: dict[Path, str],
    findings: list[Finding],
    ledger_drift: Optional[dict] = None,
) -> None:
    """Append ``spec_plan_ledger_drift`` findings for drifted plan ledgers.

    A plan is only inspected when at least one checkpoint session exists for
    its derived ``plan_id`` (plans that predate the wiring stay silent). Drift
    kinds: ledger ahead of the checkpoints, a completed checkpoint ahead of the
    ledger, and a ``Status: complete`` header whose ledger is still open.
    """
    if not _enabled(ledger_drift):
        return
    severity = _severity(
        ledger_drift.get("severity") if isinstance(ledger_drift, dict) else None
    )

    store = None
    for plan in plans:
        text = texts.get(plan, "")
        plan_id = derive_plan_id(plan, text)
        if store is None:
            store = _store(project_root)
        sessions = store.find_sessions_for_plan(plan_id)
        if not sessions:
            continue

        from .spec_plan import parse_plan_ledger, parse_task_ledgers

        task_ledger = parse_task_ledgers(plan)
        completed_ids = _completed_task_ids(store, sessions, plan_id)
        complete_in_ledger = {
            task_id for task_id, info in task_ledger.items() if info["complete"]
        }

        ahead = sorted(complete_in_ledger - completed_ids)
        behind = sorted(completed_ids - complete_in_ledger)
        if ahead:
            findings.append(Finding(
                severity,
                _FINDING,
                _rel(project_root, plan),
                "ledger marks task(s) done without a completed checkpoint: "
                + ", ".join(ahead),
                suggestion="write a completed checkpoint for the task or reopen "
                           "the ledger checkbox",
            ))
        if behind:
            findings.append(Finding(
                severity,
                _FINDING,
                _rel(project_root, plan),
                "completed checkpoint without a closed ledger task: "
                + ", ".join(behind),
                suggestion="close the ledger checkbox or remove the stale "
                           "checkpoint",
            ))

        ledger = parse_plan_ledger(plan)
        status = (ledger.get("status") or "").strip().lower()
        if status == "complete" and not ledger["complete"]:
            findings.append(Finding(
                severity,
                _FINDING,
                _rel(project_root, plan),
                "plan status is 'complete' while the ledger is not complete",
                suggestion="reopen the plan status or close the remaining "
                           "checkboxes",
            ))


def _store(project_root: Path) -> "CheckpointStore":
    from ..checkpoint import CheckpointStore

    return CheckpointStore.from_config(project_root)
