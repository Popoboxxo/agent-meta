"""Provider-neutral hook kernel (issue #1257, concept D.2/D.3 step 1).

Public API::

    from kernel import NormEvent, decide
    verdict = decide(NormEvent(tool_kind="shell", command="git status"))

The kernel never reads a provider environment variable and never maps a
Decision to a provider block protocol -- that is the adapter's job. Adapters
and the shell-hook rewiring are later migration steps and are not part of
this bundle.
"""
from __future__ import annotations

import re
from typing import Optional

from . import containment, git_gate, identity
from .model import Decision, Identity, NormEvent

__all__ = [
    "Decision",
    "Identity",
    "NormEvent",
    "containment",
    "decide",
    "git_gate",
    "identity",
]

_WORKTREE_RE = re.compile(r"isolation\s*[:=]\s*[\"']?worktree\b", re.IGNORECASE)


def _forbidden_dispatch(command: Optional[str]) -> Optional[str]:
    """Return a deny reason for known-forbidden delegation shapes (F3-03)."""
    if not command:
        return None
    if _WORKTREE_RE.search(command):
        return "dispatch.worktree-isolation"
    lowered = command.lower()
    if "orchestrator" in lowered and (
        "subagent" in lowered or "agent" in lowered or "->" in command
    ):
        return "dispatch.orchestrator-respawn"
    return None


def decide(event: NormEvent) -> Decision:
    """Return the kernel verdict for a normalized event (fail-closed)."""
    kind = event.tool_kind

    if kind == "read":
        return Decision.allow("kernel.read")

    if kind == "write":
        verdict = containment.check_containment(event)
        return verdict if verdict is not None else Decision.allow("kernel.write")

    if kind == "shell":
        result = git_gate.classify_git(event.command)
        audit = {
            "category": result.category,
            "scope": result.scope,
            "subcommand": result.subcommand,
            "identity": identity.resolve_identity(event).__dict__,
        }
        if result.category == "destructive":
            return Decision.deny("git.destructive", audit)
        if result.category == "mutation":
            return Decision.deny("git.mutation", audit)
        return Decision.allow("kernel.shell", audit)

    if kind == "dispatch":
        reason = _forbidden_dispatch(event.command)
        if reason:
            return Decision.deny(reason)
        return Decision.allow("kernel.dispatch")

    return Decision.deny("kernel.invalid-tool-kind")
