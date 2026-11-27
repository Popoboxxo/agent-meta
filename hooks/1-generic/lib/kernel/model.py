"""Provider-neutral event and decision types for the hook kernel.

The contract follows the approved target architecture in
``docs/analysis/2026-11-14-fable-provider-hooks-audit.md`` section D.2:

* ``NormEvent`` carries only normalized fields -- no provider name and no
  harness-specific environment variable or payload shape. Its ``project_dir``
  is supplied by adapter normalization of ``AM_PROJECT_DIR``.
* ``Decision`` is ``allow | deny | ask`` with a reason and a structured audit
  payload. ``ask`` is prepared here but no adapter maps it to a provider
  protocol yet (migration step 3).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

TOOL_KINDS = frozenset({"write", "shell", "dispatch", "read"})
IDENTITY_SOURCES = frozenset({"harness", "sentinel", "none"})
OUTCOMES = frozenset({"allow", "deny", "ask"})


@dataclass(frozen=True)
class NormEvent:
    """A provider-normalized PreToolUse-style event.

    Adapters own ``AM_PROJECT_DIR`` and pass its normalized value as
    ``project_dir``; the kernel never reads provider environment variables.
    """

    tool_kind: str
    path: Optional[str] = None
    command: Optional[str] = None
    cwd: Optional[str] = None
    project_dir: Optional[str] = None
    agent_id: Optional[str] = None
    declared_agent: Optional[str] = None
    identity_source: str = "none"
    event: str = ""

    def __post_init__(self) -> None:
        if self.tool_kind not in TOOL_KINDS:
            raise ValueError("unknown tool_kind: %r" % (self.tool_kind,))
        if self.identity_source not in IDENTITY_SOURCES:
            raise ValueError(
                "unknown identity_source: %r" % (self.identity_source,)
            )


@dataclass(frozen=True)
class Identity:
    """Attribution resolved from an explicit identity source (concept D.4)."""

    source: str
    agent_id: Optional[str] = None
    role: Optional[str] = None


@dataclass(frozen=True)
class Decision:
    """The kernel verdict. Adapters map it to the provider block protocol."""

    outcome: str
    reason: str
    audit: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.outcome not in OUTCOMES:
            raise ValueError("unknown outcome: %r" % (self.outcome,))

    @classmethod
    def allow(cls, reason: str, audit: Optional[dict] = None) -> "Decision":
        return cls("allow", reason, dict(audit or {}))

    @classmethod
    def deny(cls, reason: str, audit: Optional[dict] = None) -> "Decision":
        return cls("deny", reason, dict(audit or {}))

    @classmethod
    def ask(cls, reason: str, audit: Optional[dict] = None) -> "Decision":
        return cls("ask", reason, dict(audit or {}))
