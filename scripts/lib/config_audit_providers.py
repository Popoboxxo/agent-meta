"""Provider-registry-completeness check for config_audit (issue #625).

Provider-keyed Python maps/branches scattered across ``scripts/`` are meant to
enumerate *every* registered provider from ``config/ai-providers.yaml``. When a
new provider is added to the YAML registry, these Python-side enumerations are
easy to forget silently -- proven by ``scripts/lifecycle_check.py``'s
pending-tasks map, which still doesn't know about Copilot/Mammouth despite
both being registered for a while (docs/plans/audit-2026-09-system-concept.md
§4.2(a)).

This module defines the known enumeration touchpoints and a cheap text-based
check: for each registered provider, verify its name literal appears inside
the touchpoint's source chunk. Text-based rather than AST-based on purpose --
these are flat string-keyed dict/list/if-elif constructs, a regex is the
lazy-correct tool here.

Deliberately WARN-only (never error): a provider can be legitimately excluded
from a given touchpoint (e.g. no hook support), and this check has no way to
know that -- it only flags "not mentioned", a human decides if that's a gap.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProviderTouchpoint:
    """A known provider-keyed enumeration construct in scripts/.

    Attributes:
        id: Short machine-readable identifier (e.g. "lifecycle_check.pending_tasks").
        file: Path relative to the agent-meta repo root.
        chunk_pattern: Regex whose first capture group isolates the construct's
            source text (the dict/list/branch body) so provider-name checks
            don't false-positive on unrelated code elsewhere in the file.
        description: Human-readable name for report messages.
    """

    id: str
    file: str
    chunk_pattern: re.Pattern
    description: str


# The concrete touchpoints named in issue #625 -- deliberately not an
# exhaustive repo-wide scan (would risk false positives / scope creep; the
# full inventory of known "doubled truths" is docs/plans/audit-2026-09-system
# -concept.md §4.2(a)).
#
# Issue #627 eliminated all 5 originally-listed literal Python maps in favor
# of reading config/ai-providers.yaml directly. Four of them (pending_tasks,
# provider_dirs, terminal_tool, valid_providers) simply vanished as source
# constructs -- their chunk_pattern below no longer matches anything, so they
# fall through the "silently skipped" path in find_missing_providers() and
# stop producing findings on their own, no touchpoint removal needed.
#
# The 5th, isolation.py's sync_provider_isolation, could not be handled the
# same way: the function itself still exists (it's the public API), so its
# chunk_pattern still matches -- but the per-provider dispatch inside it was
# converted from a literal `if provider == "Name"` chain to a config-key
# lookup (config/ai-providers.yaml::isolation-mechanism), so the function
# body no longer contains provider name literals at all. Left in place, this
# touchpoint would misfire on every registered provider instead of none. Its
# entry is therefore retired here rather than gamed with a decoy literal.
PROVIDER_TOUCHPOINTS: tuple[ProviderTouchpoint, ...] = (
    ProviderTouchpoint(
        id="lifecycle_check.pending_tasks",
        file="scripts/lifecycle_check.py",
        chunk_pattern=re.compile(
            r"_PROVIDER_PENDING_FILES\s*:\s*dict\[[^\]]*\]\s*=\s*\{(.*?)\n\s*\}", re.S
        ),
        description="lifecycle_check.py pending-tasks-by-provider map (_PROVIDER_PENDING_FILES)",
    ),
    ProviderTouchpoint(
        id="context.provider_dirs",
        file="scripts/lib/context.py",
        chunk_pattern=re.compile(r"provider_dirs\s*=\s*\{(.*?)\n\s*\}", re.S),
        description="context.py agents-dir-by-provider map (provider_dirs)",
    ),
    ProviderTouchpoint(
        id="viz.terminal_tool",
        file="scripts/lib/viz.py",
        chunk_pattern=re.compile(
            r"_PROVIDER_TERMINAL_TOOL\s*:\s*dict\[[^\]]*\]\s*=\s*\{(.*?)\n\s*\}", re.S
        ),
        description="viz.py bash-tool-name-by-provider map (_PROVIDER_TERMINAL_TOOL)",
    ),
    ProviderTouchpoint(
        id="setup.valid_providers",
        file="scripts/lib/setup.py",
        chunk_pattern=re.compile(r"valid_providers\s*=\s*\[(.*?)\]", re.S),
        description="setup.py wizard provider choices (valid_providers)",
    ),
)


def find_missing_providers(
    agent_meta_root: Path, registered_providers: set[str]
) -> list[tuple[ProviderTouchpoint, str]]:
    """Return ``(touchpoint, provider)`` pairs missing from their construct.

    A touchpoint whose ``chunk_pattern`` no longer matches (e.g. the code was
    refactored) is silently skipped rather than flagged -- keeping this check
    warn-only and false-positive-averse per issue #625's design intent.
    """
    missing: list[tuple[ProviderTouchpoint, str]] = []
    for touchpoint in PROVIDER_TOUCHPOINTS:
        path = agent_meta_root / touchpoint.file
        if not path.is_file():
            continue
        match = touchpoint.chunk_pattern.search(path.read_text(encoding="utf-8"))
        if not match:
            continue
        chunk = match.group(1)
        for provider in sorted(registered_providers):
            if f'"{provider}"' not in chunk and f"'{provider}'" not in chunk:
                missing.append((touchpoint, provider))
    return missing
