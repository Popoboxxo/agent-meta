"""Plan ledger writer behind ``sync.py --update-plan-ledger``.

The human-readable plan ledger is the leading ``- [ ]`` / ``- [x]`` checkbox
list inside the task blocks of a plan document plus the first ``Status:``
header line. This module writes exactly the format that
:func:`lib.consistency.spec_plan.parse_plan_ledger` reads, so every document
produced here round-trips through the parser: after marking all task
checkboxes done, ``parse_plan_ledger(path)["complete"]`` is ``True``.

Scope: G-04 (writable, drift-checked ledger) of the progress/ledger system
design (``SPEC-PROGRESS-LEDGER-2026-09-13``, IC-05). No new persistence and no
provider-specific behaviour: task discovery and task-id normalization are
shared with the parser via :mod:`lib.plan_identity`, and the whole new
document is written atomically through :func:`lib.io.write_atomic`.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Tuple

from .io import write_atomic
from .plan_identity import TASK_HEADER_RE, normalize_task_id

MODE = "update-plan-ledger"

# Exactly the line-leading checkbox marker the parser reads. Only this prefix
# is rewritten; indentation (which the parser ignores) and trailing text stay
# untouched.
_CHECKBOX_RE = re.compile(r"^- \[( |x|X)\]", re.MULTILINE)

# First lowercase-sensitive ``Status:`` header line, mirroring
# ``parse_plan_ledger``'s single ``re.search``. Group 1 is the prefix so the
# value is replaced without losing the ``>`` marker or indentation.
_STATUS_LINE_RE = re.compile(r"(?m)^([ \t]*>?[ \t]*Status:)[ \t]*.*$")

# The H1 title line -- the insertion anchor for a missing ``Status:`` header.
_H1_RE = re.compile(r"(?m)^# .*$")


@dataclass(frozen=True)
class LedgerWriteResult:
    """Outcome of one ledger write.

    ``tasks_updated`` lists the normalized task ids whose checkboxes actually
    changed; ``checkboxes_toggled`` is the number of markers rewritten to a
    different state; ``unmatched`` lists requested task ids that no task block
    matched. ``status`` is the value written (``None`` when only checkboxes
    were touched).
    """

    plan_path: str
    ok: bool
    reason: Optional[str]
    tasks_updated: Tuple[str, ...]
    checkboxes_toggled: int
    unmatched: Tuple[str, ...]
    status: Optional[str]
    dry_run: bool


def _task_blocks(text: str):
    """Yield ``(task_id, start, end)`` for every task block in ``text``.

    A block spans its ``:data:`TASK_HEADER_RE` header up to the next header (or
    the end of the document), matching :func:`parse_task_ledgers` in the
    parser.
    """
    headers = list(TASK_HEADER_RE.finditer(text))
    blocks = []
    for index, header in enumerate(headers):
        start = header.start()
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        blocks.append((normalize_task_id(header.group(1).strip()), start, end))
    return blocks


def _result(path: Path, *, ok: bool, reason: Optional[str], dry_run: bool,
            tasks_updated=(), checkboxes_toggled: int = 0,
            unmatched=(), status: Optional[str] = None) -> LedgerWriteResult:
    """Build a :class:`LedgerWriteResult` with deterministic tuple ordering."""
    return LedgerWriteResult(
        plan_path=str(path),
        ok=ok,
        reason=reason,
        tasks_updated=tuple(sorted(tasks_updated)),
        checkboxes_toggled=checkboxes_toggled,
        unmatched=tuple(sorted(unmatched)),
        status=status,
        dry_run=dry_run,
    )


def update_plan_ledger(plan_path: Path, updates: Mapping[str, bool], *,
                       status: Optional[str] = None,
                       dry_run: bool = False) -> LedgerWriteResult:
    """Rewrite task checkboxes and/or the first ``Status:`` line of a plan.

    ``updates["task-3"] = True`` rewrites every leading ``- [ ]`` / ``- [x]``
    inside the ``task-3`` block to ``- [x]``; ``False`` resets it to ``- [ ]``.
    ``status``, when given, replaces the first ``Status:`` header line (or
    inserts ``> Status: <value>`` directly after the H1 title). The full new
    document is built in memory and written atomically; when nothing changes no
    write happens. Content problems never raise: a missing plan yields
    ``ok=False`` with ``reason="plan-not-found"``, an ``OSError`` yields
    ``reason="io-error:<ClassName>"`` and an unknown task id is reported in
    ``unmatched`` while the other updates are still applied.
    """
    path = Path(plan_path)
    normalized = {
        normalize_task_id(str(raw_id)): bool(flag)
        for raw_id, flag in (updates or {}).items()
    }

    if not path.exists():
        return _result(path, ok=False, reason="plan-not-found", dry_run=dry_run)

    try:
        original = path.read_text(encoding="utf-8")
    except OSError as exc:
        return _result(path, ok=False, reason=f"io-error:{type(exc).__name__}",
                       dry_run=dry_run)

    updated = original
    toggled = 0
    changed_ids = set()
    matched_ids = set()

    # Back to front: edits at higher offsets never invalidate the offsets of
    # the blocks still to be processed.
    for task_id, start, end in reversed(_task_blocks(original)):
        if task_id not in normalized:
            continue
        matched_ids.add(task_id)
        body = original[start:end]
        target = "x" if normalized[task_id] else " "
        changed = 0

        def _replace(match, _target=target):
            nonlocal changed
            if match.group(1).lower() != _target:
                changed += 1
            return "- [" + _target + "]"

        new_body = _CHECKBOX_RE.sub(_replace, body)
        if new_body != body:
            updated = updated[:start] + new_body + updated[end:]
        if changed:
            toggled += changed
            changed_ids.add(task_id)

    status_value = None
    if status is not None:
        if _STATUS_LINE_RE.search(updated):
            updated = _STATUS_LINE_RE.sub(
                lambda match: match.group(1) + " " + status, updated, count=1
            )
        else:
            title = _H1_RE.search(updated)
            header = "> Status: " + status
            if title is not None:
                updated = updated[:title.end()] + "\n" + header + updated[title.end():]
            else:
                updated = header + "\n" + updated
        status_value = status

    if updated == original:
        return _result(path, ok=True, reason=None, dry_run=dry_run,
                       tasks_updated=changed_ids, checkboxes_toggled=toggled,
                       unmatched=set(normalized) - matched_ids, status=status_value)

    if not dry_run:
        try:
            write_atomic(path, updated)
        except OSError as exc:
            return _result(path, ok=False,
                           reason=f"io-error:{type(exc).__name__}",
                           dry_run=dry_run, tasks_updated=changed_ids,
                           checkboxes_toggled=toggled,
                           unmatched=set(normalized) - matched_ids,
                           status=status_value)

    return _result(path, ok=True, reason=None, dry_run=dry_run,
                   tasks_updated=changed_ids, checkboxes_toggled=toggled,
                   unmatched=set(normalized) - matched_ids, status=status_value)


def set_plan_status(plan_path: Path, status: str, *,
                    dry_run: bool = False) -> LedgerWriteResult:
    """Set the first ``Status:`` header line of a plan document.

    Thin wrapper over :func:`update_plan_ledger` with no checkbox updates. The
    value is written verbatim and read back by ``parse_plan_ledger``.
    """
    return update_plan_ledger(plan_path, {}, status=status, dry_run=dry_run)


def _print_result(result: LedgerWriteResult) -> None:
    """Print the human-readable result of a ledger write.

    CLI output is a documented exception to the "no ``print`` in ``lib``"
    convention (same as ``spec_plan_validate``): the mode is terminal-facing.
    """
    print(f"  i  plan-ledger: {result.plan_path}")
    if not result.ok:
        print(f"  !  not written ({result.reason})", file=sys.stderr)
        return
    if result.dry_run:
        print("     dry-run — no file written")
    verb = "would toggle" if result.dry_run else "toggled"
    print(f"     tasks updated: {', '.join(result.tasks_updated) or '(none)'}")
    print(f"     checkboxes {verb}: {result.checkboxes_toggled}")
    if result.status is not None:
        print(f"     status: {result.status}")
    if result.unmatched:
        print(f"     unmatched task ids: {', '.join(result.unmatched)}",
              file=sys.stderr)


def handle_update_plan_ledger(ctx) -> None:
    """CLI handler for ``sync.py --update-plan-ledger`` (IC-05).

    Required input is the plan path plus at least one action (``--task`` and/or
    ``--status``). Validation is manual (``sys.exit(1)``), so a missing
    argument reports exit code 1 rather than argparse's default 2. The write is
    restricted to the project root and exits 0 only when the plan was written
    and no task id was unmatched.
    """
    args = ctx.args
    ctx.mode = MODE
    log = getattr(ctx, "log", None)

    raw_plan = getattr(args, "update_plan_ledger", None)
    task_ids = [str(task) for task in (getattr(args, "task", None) or [])]
    status = getattr(args, "status", None)
    reopen = bool(getattr(args, "open", False))
    dry_run = bool(getattr(args, "dry_run", False))

    # M3: required-argument validation belongs to the handler, so the exit
    # code is 1 (usage error) instead of argparse's 2.
    if not raw_plan:
        print("  !  --update-plan-ledger requires a plan path", file=sys.stderr)
        sys.exit(1)
    if not task_ids and status is None:
        print("  !  --update-plan-ledger requires --task and/or --status",
              file=sys.stderr)
        sys.exit(1)

    project_root = Path(ctx.project_root).resolve()
    plan_path = Path(raw_plan)
    if not plan_path.is_absolute():
        plan_path = project_root / plan_path

    # Mutations are confined to the project root.
    try:
        plan_path.resolve().relative_to(project_root)
    except ValueError:
        print(f"  !  plan path outside the project root: {plan_path}",
              file=sys.stderr)
        sys.exit(1)
    plan_path = plan_path.resolve()

    updates = {normalize_task_id(task): not reopen for task in task_ids}
    if log is not None:
        log.note(MODE, f"{plan_path} tasks={sorted(updates)} status={status}")

    result = update_plan_ledger(plan_path, updates, status=status, dry_run=dry_run)
    _print_result(result)

    code = 0 if (result.ok and not result.unmatched) else 1
    if log is not None:
        log.note(MODE, f"exit {code} ok={result.ok} unmatched={list(result.unmatched)}")
    sys.exit(code)
