"""Standing production checkpoint writer behind ``sync.py --checkpoint``.

This module is the concrete, dispatcher-independent production trigger for
G-02/G-04 of the progress/ledger system design
(``SPEC-PROGRESS-LEDGER-2026-09-13``, IC-11). It writes a single
:class:`~lib.checkpoint.Checkpoint` through the existing
:class:`~lib.checkpoint.CheckpointStore` -- no new persistence format and no
G-08 coupling; the automatic in-harness path in ``execute_plan`` stays the only
dispatcher-dependent writer.

Identity is explicit, never random (F1): ``plan_id`` comes from an explicit
``--plan-id`` value or from :func:`lib.plan_identity.derive_plan_id` of an
explicit ``--plan <path>``; when neither is given it is ``None``. The raw task
id is normalized with :func:`lib.plan_identity.normalize_task_id` *before* the
composite ref is built (M1), so ``--task 1`` produces ``<plan-id>#task-1`` and
never ``<plan-id>#1``.

The mode mutates only under ``.meta-viz/`` (the store's checkpoint directory
plus its existing ``progress/current.md`` write-through). It never dispatches,
never touches a plan document and stays provider-agnostic: no provider
equality branch, no provider literal and no model name appears here.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from .checkpoint import Checkpoint, CheckpointStore, validate_session_id
from .log import SyncLog
from .plan_identity import derive_plan_id, make_task_ref, normalize_task_id

MODE = "checkpoint"

ALLOWED_STATUSES = ("completed", "failed", "timeout", "in_progress")

_REQUIRED_FLAGS = (
    ("session_id", "--session-id"),
    ("task", "--task"),
    ("agent", "--agent"),
    ("status", "--status"),
)


def record_checkpoint(
    project_root: Path,
    config: Optional[dict],
    log: SyncLog,
    *,
    session_id: str,
    task_id: str,
    agent: str,
    status: str,
    task_description: str = "",
    plan_id: Optional[str] = None,
    status_summary: Optional[str] = None,
    next_step: Optional[str] = None,
) -> int:
    """Append one checkpoint to ``session_id`` and return an exit code.

    ``task_id`` is normalized first (M1) so it is identical to the id the plan
    parser/ledger use. ``plan_id`` is passed through verbatim -- callers own the
    explicit-identity rule (F1); ``task_ref`` follows from
    :func:`lib.plan_identity.make_task_ref` and is ``None`` when there is no
    ``plan_id``.

    Returns ``0`` on a successful write and ``1`` when the store raises
    ``OSError`` (nothing half-written: the store's atomic write is unchanged).
    ``config`` is accepted for handler symmetry and unused here.
    """
    normalized_task_id = normalize_task_id(str(task_id))
    checkpoint = Checkpoint(
        task_id=normalized_task_id,
        agent=agent,
        task_description=task_description or "",
        status=status,
        plan_id=plan_id,
        task_ref=make_task_ref(plan_id, normalized_task_id),
        status_summary=status_summary,
        next_step=next_step,
    )

    store = CheckpointStore(project_root=project_root)
    try:
        store.save_checkpoint(session_id, checkpoint)
    except OSError as exc:
        log.warn(
            "--checkpoint: could not write session {} ({})".format(
                session_id, type(exc).__name__
            )
        )
        return 1

    log.note(
        MODE,
        "session {} task {} status {}{}".format(
            session_id,
            normalized_task_id,
            status,
            "" if plan_id is None else " plan {}".format(plan_id),
        ),
    )
    return 0


def _resolve_plan_id(ctx, args) -> Optional[str]:
    """Resolve the explicit plan identity (F1), or ``None`` when absent.

    ``--plan-id`` wins over ``--plan``. A relative ``--plan`` path is resolved
    against the project root (not the process cwd) before deriving the id.
    """
    explicit_id = getattr(args, "plan_id", None)
    if explicit_id:
        return str(explicit_id)

    raw_plan = getattr(args, "plan", None)
    if not raw_plan:
        return None

    plan_path = Path(raw_plan)
    if not plan_path.is_absolute():
        plan_path = Path(ctx.project_root) / plan_path
    return derive_plan_id(plan_path)


def _handle_checkpoint(ctx) -> None:
    """CLI handler for ``sync.py --checkpoint`` (IC-11).

    Required input is ``--session-id``, ``--task``, ``--agent`` and ``--status``.
    Validation is manual (``sys.exit(1)``) so a missing required argument
    reports exit code 1 instead of argparse's default 2 (M3). The session id is
    validated before any store access (path-traversal containment, IC-11), so a
    rejected id exits 1 and never writes outside ``.meta-viz/``. The mode exits
    directly -- it never falls through to the common sync tail -- and returns 0
    only when the checkpoint was written.
    """
    args = ctx.args
    ctx.mode = MODE
    log = getattr(ctx, "log", None)

    missing = [
        flag
        for attr, flag in _REQUIRED_FLAGS
        if not _arg_value(getattr(args, attr, None))
    ]
    if missing:
        print(
            "  !  --checkpoint requires " + ", ".join(missing),
            file=sys.stderr,
        )
        sys.exit(1)

    session_id = str(getattr(args, "session_id"))
    try:
        validate_session_id(session_id)
    except ValueError as exc:
        print(f"  !  --checkpoint: {exc}", file=sys.stderr)
        sys.exit(1)

    raw_tasks = [str(task) for task in (getattr(args, "task", None) or [])]
    task_id = raw_tasks[0]
    agent = str(getattr(args, "agent"))
    status = str(getattr(args, "status"))

    if status not in ALLOWED_STATUSES:
        print(
            "  !  --checkpoint --status must be one of: "
            + ", ".join(ALLOWED_STATUSES),
            file=sys.stderr,
        )
        sys.exit(1)

    plan_id = _resolve_plan_id(ctx, args)

    code = record_checkpoint(
        ctx.project_root,
        getattr(ctx, "config", None),
        log,
        session_id=session_id,
        task_id=task_id,
        agent=agent,
        status=status,
        task_description=getattr(args, "description", None) or "",
        plan_id=plan_id,
        status_summary=getattr(args, "summary", None),
        next_step=getattr(args, "next_step", None),
    )

    ref = make_task_ref(plan_id, normalize_task_id(task_id))
    print(f"  i  checkpoint: session {session_id} task {task_id} status {status}")
    print(f"     task_ref: {ref if ref is not None else '(none)'}")
    sys.exit(code)


def _arg_value(value) -> bool:
    """Truthiness for a CLI argument: an empty list/counts as missing (M3)."""
    if value is None:
        return False
    if isinstance(value, (list, tuple)) and not value:
        return False
    return bool(value)
