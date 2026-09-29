"""Fail-soft plan-ledger close-out wired into ``orchestration.execute_plan``.

Scope: G-04 (writable, drift-checked ledger) of the progress/ledger system
design (``SPEC-PROGRESS-LEDGER-2026-09-13``, IC-06). Once a plan run reaches
the barrier, the successful tasks are marked done in the human-readable plan
ledger and the plan status becomes ``complete`` when no leading ``- [ ]``
checkbox remains, otherwise ``IN PROGRESS``.

This module is deliberately a leaf: the ledger writer (:mod:`lib.plan_ledger`)
and the parser (:func:`lib.consistency.spec_plan.parse_plan_ledger`) are
imported lazily so no import cycle with :mod:`lib.orchestration` is
introduced. Every failure is logged and swallowed (fail-soft) — a ledger
problem must never change the aggregated barrier result.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List, Optional, Protocol

_logger = logging.getLogger(__name__)


class _BarrierLike(Protocol):
    """Structural view of the barrier entries this module consumes (IC-06)."""

    task_id: str
    status: str


def _success_task_ids(entries: Iterable[_BarrierLike]) -> List[str]:
    """Return the task ids of all ``success`` entries, in entry order."""
    return [entry.task_id for entry in entries if entry.status == "success"]


def _plan_is_complete(plan_path: Path) -> bool:
    """Reuse the parser's completeness semantics for the written document."""
    from .consistency.spec_plan import parse_plan_ledger

    return bool(parse_plan_ledger(plan_path).get("complete"))


def close_out_plan_ledger(
    ledger_path: Optional[Path],
    entries: Iterable[_BarrierLike],
) -> None:
    """Close out the plan ledger for one barrier run (IC-06, AC-14).

    ``ledger_path=None`` is a no-op (legacy behaviour: no ledger write). Only
    ``success`` entries are marked done; tasks whose entry ``failed``/``timeout``
    stay open. The plan status is set to ``complete`` when every leading
    checkbox is closed, otherwise ``IN PROGRESS``.

    Fail-soft by contract: write problems are logged and never propagate, so
    the caller's aggregated ``BarrierResult`` is unchanged.
    """
    if ledger_path is None:
        return
    try:
        from .plan_ledger import set_plan_status, update_plan_ledger

        path = Path(ledger_path)
        updates = {task_id: True for task_id in _success_task_ids(entries)}
        write_result = update_plan_ledger(path, updates)
        if not write_result.ok:
            _logger.warning(
                "execute_plan: plan ledger close-out skipped for %s: %s",
                path,
                write_result.reason,
            )
            return
        status = "complete" if _plan_is_complete(path) else "IN PROGRESS"
        set_plan_status(path, status)
    except Exception as exc:  # noqa: BLE001 - fail-soft by contract
        _logger.warning(
            "execute_plan: plan ledger close-out failed for %s: %s: %s",
            ledger_path,
            type(exc).__name__,
            exc,
        )
