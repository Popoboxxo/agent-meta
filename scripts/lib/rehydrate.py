"""Read-only ``--rehydrate`` CLI mode (IC-04, G-02).

This module is the thin CLI front-end of the read-only recovery resolver
(:mod:`lib.recovery`): it prints the resume context for the newest unfinished
session and writes nothing. The machine-readable :class:`CheckpointStore`
stays the authoritative source; this mode only reads it.

Provider-agnostic by construction: no provider-equality branch, no provider
literal, no model name and no dispatch instruction appears here. It never
returns a failure code for "nothing to resume" -- the read path is
informational.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from lib.log import SyncLog

MODE = "rehydrate"

_WORKFLOW_BLOCK = "spec-plan-workflow"
_RECOVERY_BLOCK = "recovery"

_DISABLED_NOTE = "rehydrate disabled"
_NO_SESSION_NOTE = "no unfinished session"


def _recovery_block(config: Optional[dict]) -> dict:
    """The ``spec-plan-workflow.recovery`` mapping, or ``{}`` when absent."""
    if not isinstance(config, dict):
        return {}
    workflow = config.get(_WORKFLOW_BLOCK)
    if not isinstance(workflow, dict):
        return {}
    recovery = workflow.get(_RECOVERY_BLOCK)
    return recovery if isinstance(recovery, dict) else {}


def _is_enabled(config: Optional[dict]) -> bool:
    """``rehydrate`` is opt-out: only an explicit ``false`` disables the mode."""
    return _recovery_block(config).get("rehydrate") is not False


def rehydrate(project_root: Path, config: Optional[dict], log: SyncLog) -> int:
    """Print the read-only resume context and always return ``0``.

    Behaviour (IC-04):

    * ``spec-plan-workflow.recovery.rehydrate: false`` -> print a disabled note.
    * no resumable session -> print an explicit "no unfinished session" note.
    * otherwise -> print ``render_resume_context(...)`` for the newest
      unfinished session.

    Nothing is written. The store is the authoritative resume source; the
    legacy format is tolerated read-only by :mod:`lib.recovery`.
    """
    from lib.checkpoint import CheckpointStore
    from lib.recovery import (
        build_resume_context,
        find_resumable_session,
        render_resume_context,
    )

    if not _is_enabled(config):
        log.note(MODE, _DISABLED_NOTE)
        print("\n  i  {}: {}".format(MODE, _DISABLED_NOTE))
        return 0

    store = CheckpointStore(project_root=project_root)
    source = find_resumable_session(project_root, store=store)
    if source is None:
        log.note(MODE, _NO_SESSION_NOTE)
        print("\n  i  {}: {}".format(MODE, _NO_SESSION_NOTE))
        return 0

    context = build_resume_context(
        project_root, source.session_id, plan_id=source.plan_id, store=store,
    )
    if context is None:
        log.note(MODE, _NO_SESSION_NOTE)
        print("\n  i  {}: {}".format(MODE, _NO_SESSION_NOTE))
        return 0

    rendered = render_resume_context(context)
    print(rendered, end="" if rendered.endswith("\n") else "\n")
    log.note(MODE, "resume context for session {}".format(source.session_id))
    return 0


def _handle_rehydrate(ctx) -> None:
    """Handle ``--rehydrate``: standalone, read-only, exits directly.

    Mirrors ``_handle_validate_spec_plan``: the mode must never fall through to
    the common sync tail, so it never writes files and never triggers the
    provider-restart notice.
    """
    ctx.mode = MODE
    ctx.read_only = True
    log = ctx.log
    log.note(MODE, "running rehydrate (read-only, no sync)")
    code = rehydrate(ctx.project_root, ctx.config, log)
    sys.exit(code)
