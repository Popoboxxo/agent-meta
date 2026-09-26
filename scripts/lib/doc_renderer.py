"""Renders the ``agent-meta:docs-*`` marker regions of the hybrid doc files.

Neutral leaf module: it knows no documentation file, opens nothing and **writes
nothing** — the caller owns the file. It is a pure string transformer plus the
marker regexes (IC-07), so it stays importable from anywhere without a cycle
(``scripts/lib/config.py`` consumes it in W3, and this module must not import
``config`` back).

**The marker pair follows the established region-pair pattern** of
``_MANAGED_BLOCK_RE`` in ``context.py:36-39`` (same ``<!-- agent-meta:…-begin`` /
``-end`` shape, same ``re.DOTALL`` non-greedy body, same ``count=1`` "first match
wins" replacement discipline of ``context.py:42-50``). The ``docs-*`` markers are
their **own namespace** beside the ``agent-meta:managed-*`` markers (IC-08): the
two regexes cannot match each other's markers, so a file that carries both kinds
(a provider context file *and* a docs region) survives untouched outside its docs
regions.

Three contracts are hard, not incidental:

* **Unbalanced region → byte-identical output.** A ``docs-begin`` without its
  ``docs-end`` makes :func:`apply_fact_blocks` return the input text **unchanged**
  and emit **exactly one** warning. All-or-nothing: a half-written marker region
  would corrupt a tracked hand-maintained file, and "mostly updated" is not a
  state a file can be in (AC-15).
* **Duplicate region → first only.** The second pair stays byte-identical and
  produces a warning (AC-16), mirroring ``_has_duplicate_managed_block``.
* **Output is independent of the caller's dict order** (AC-27). Each region maps
  to exactly one fact key, so the rendered bytes are a function of
  ``(region, facts[key])`` alone — never of ``facts`` iteration order. No
  timestamp, no absolute path, no host data (NFA-02).

An empty fact value renders the placeholder comment
``<!-- agent-meta:docs-empty: <name> -->`` instead of an empty line, so an
incomplete fact is visible in review instead of being a silent blank row (d, IC-07).

**OPEN GAP (not a bug, W1-6 recorded it):** ``DOCS_TIER_PRESET_BLOCK`` and
``DOCS_DOD_PRESET_BLOCK`` are computed facts with no region name, because IC-08
enumerates exactly six allowed region names. They are therefore *not* renderable
here; widening :data:`ALLOWED_REGIONS` is a spec change, not a local decision.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Mapping

    class _WarnSink(Protocol):
        """The one log method this module needs (``SyncLog.warning``)."""

        def warning(self, message: str) -> None: ...

#: Region marker pair (IC-07). Form follows ``context.py:36-39``.
DOCS_BLOCK_RE = re.compile(
    r"(<!--\s*agent-meta:docs-begin\s+(?P<region>[a-z0-9-]+)\s*-->)(?P<body>.*?)"
    r"(<!--\s*agent-meta:docs-end\s+(?P=region)\s*-->)",
    re.DOTALL,
)

#: A ``docs-begin`` marker on its own — used to detect the *unpaired* ones, which
#: ``DOCS_BLOCK_RE`` cannot see (it only matches complete pairs).
DOCS_BEGIN_RE = re.compile(
    r"<!--\s*agent-meta:docs-begin\s+(?P<region>[a-z0-9-]+)\s*-->"
)

#: Warning channel, prefixed to every message (the one-argument ``SyncLog.warning``
#: signature has no channel parameter; the ``channel: message`` prefix is the repo
#: convention, cf. ``backup.py:333``).
LOG_CHANNEL = "docs"

#: Placeholder for a fact that could not be computed (fail-soft, IC-01/IC-07).
EMPTY_MARKER_TEMPLATE = "<!-- agent-meta:docs-empty: {name} -->"

#: The allowed region names (IC-08) and the single fact each one renders. This
#: mapping *is* the namespace whitelist: a name that is not a key here is not a
#: valid region.
REGION_FACT_KEYS: dict[str, str] = {
    "facts": "DOCS_REPO_FACTS_BLOCK",
    "roster": "DOCS_AGENT_ROSTER_BLOCK",
    "pipelines": "DOCS_PIPELINES_BLOCK",
    "hooks": "DOCS_HOOKS_BLOCK",
    "providers": "DOCS_PROVIDERS_BLOCK",
    "version": "DOCS_VERSION",
}

#: The six allowed region names, in the order of IC-08.
ALLOWED_REGIONS: tuple[str, ...] = tuple(REGION_FACT_KEYS)


def is_valid_region(region: str) -> bool:
    """True when *region* is one of the six allowed region names (IC-08)."""
    return region in REGION_FACT_KEYS


def render_doc_fact_block(region: str, facts: Mapping[str, str]) -> str:
    """Return the body text for *region*, rendered from *facts*.

    Deterministic and timestamp-free (NFA-02): the bytes depend only on
    ``facts[REGION_FACT_KEYS[region]]``, never on the iteration order of *facts*.
    A missing key and an empty/whitespace-only value are the same case — a fact
    that could not be computed — and render the ``docs-empty`` placeholder comment
    rather than an empty line (no silent blank-row noise in the diff).

    The return value is a **region body**: it starts with exactly one newline and
    ends with exactly one newline, because the span ``DOCS_BLOCK_RE`` calls
    ``body`` is the text *between* the two markers and therefore includes the
    newline that closes the begin line. It can be dropped between two markers
    verbatim, and it can never glue a marker to a table row.

    Args:
        region: One of :data:`ALLOWED_REGIONS`.
        facts: The computed ``DOCS_*`` facts; non-string values are coerced.

    Returns:
        The rendered body, delimited by exactly one newline on each side.

    Raises:
        ValueError: If *region* is not an allowed region name. This is the
            hard, programming-error boundary of the module. A *file* that
            contains an unknown region name is not a programming error and is
            handled fail-soft by :func:`apply_fact_blocks` (left untouched plus
            one warning), so a sync never aborts over hand-written markup.
    """
    if region not in REGION_FACT_KEYS:
        raise ValueError(
            f"unknown docs region '{region}' — allowed: {'|'.join(ALLOWED_REGIONS)}"
        )
    fact_key = REGION_FACT_KEYS[region]
    raw = facts.get(fact_key, "")
    value = "" if raw is None else str(raw)
    body = value.strip("\n").rstrip()
    if not body:
        return f"\n{EMPTY_MARKER_TEMPLATE.format(name=fact_key)}\n"
    return f"\n{body}\n"


def _warn(log: _WarnSink | None, detail: str) -> None:
    """Emit one warning on *log* (no-op when no log was passed)."""
    if log is None:
        return
    log.warning(f"{LOG_CHANNEL}: {detail}")


def apply_fact_blocks(
    text: str, facts: Mapping[str, str], log: _WarnSink | None = None
) -> str:
    """Replace the body of every docs region in *text* with the rendered fact.

    Rules, in the order they are decided:

    1. **Unbalanced region → no-op.** If any ``docs-begin`` marker has no matching
       ``docs-end``, *text* is returned byte-identical and **exactly one**
       warning naming the first unpaired region is emitted (AC-15). The
       all-or-nothing rule is deliberate: a partially rewritten marker region in
       a tracked hand-maintained file is unrecoverable by the next run.
    2. **Duplicate region → first only.** Only the first pair of a repeated region
       name is replaced; the later ones stay byte-identical and produce a warning
       (AC-16, the ``count=1`` discipline of ``context.py:42-50``).
    3. **Unknown region name → untouched plus warning.** Not a valid region, so it
       is not rendered (IC-08) and does not abort the run.
    4. Missing region → unchanged; markers outside the ``docs-*`` namespace (in
       particular ``agent-meta:managed-*``) are never touched (IC-08).

    Args:
        text: Full file content.
        facts: The computed ``DOCS_*`` facts.
        log: Optional log object with a ``warning(message)`` method; ``None``
            makes the function silent.

    Returns:
        The rewritten text, or *text* itself when there is nothing to do.
    """
    balanced = list(DOCS_BLOCK_RE.finditer(text))
    paired_starts = {match.start() for match in balanced}
    unpaired = [
        match.group("region")
        for match in DOCS_BEGIN_RE.finditer(text)
        if match.start() not in paired_starts
    ]
    if unpaired:
        _warn(log, f"unbalanced marker region '{unpaired[0]}' — file left unchanged")
        return text

    pieces: list[str] = []
    seen: set[str] = set()
    cursor = 0
    for match in balanced:
        region = match.group("region")
        if region in seen:
            _warn(log, f"duplicate marker region '{region}' — only the first is rendered")
            continue
        seen.add(region)
        if not is_valid_region(region):
            _warn(log, f"unknown marker region '{region}' — not rendered")
            continue
        pieces.append(text[cursor : match.start("body")])
        pieces.append(render_doc_fact_block(region, facts))
        cursor = match.end("body")
    pieces.append(text[cursor:])
    return "".join(pieces)
