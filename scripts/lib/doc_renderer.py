"""Renders the ``agent-meta:docs-*`` marker regions of the hybrid doc files.

Two layers, one module. The **rendering** layer (:data:`DOCS_BLOCK_RE`,
:func:`render_doc_fact_block`, :func:`apply_fact_blocks`) is a neutral leaf: it
knows no documentation file, opens nothing and **writes nothing** — the caller
owns the file. It is a pure string transformer plus the marker regexes (IC-07),
so it stays importable from anywhere without a cycle
(``scripts/lib/config.py`` consumes it in W3, and this module must not import
``config`` back).

The **writer** layer (:func:`sync_docs_consolidation`, W3-1 / IC-13) added in
this wave is the exception, and it is deliberately narrow: it owns the *gate*,
the *ownership decision* and the single call into
:func:`~scripts.lib.io.write_checked`. It never writes through a second path —
one funnel is what keeps the idempotency check, the secret scan and ``dry_run``
from drifting apart — and it never imports ``config``, so the IC-11 bridge stays
possible.

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

from .doc_index import (
    DOCS_INDEX_FILENAME,
    DOCS_INDEX_RELPATH,
    build_index_model,
    has_docs_tree,
)
from .io import safe_path, write_checked

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from .log import SyncLog

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


# ---------------------------------------------------------------------------
# W3-1 — write, idempotency and dry_run contract (IC-13, AC-23, AC-26)
# ---------------------------------------------------------------------------

LOG_TARGET: str = "docs-consolidation"
"""Log target of this writer — the ``skip``/``note`` target IC-13 names."""

DISABLED_REASON: str = "disabled in project.yaml"
"""Reason for the disabled/absent gate (IC-13, verbatim)."""

NO_DOCS_TREE_REASON: str = "no docs/ tree — not created in a foreign project"
"""Reason a consumer project without a documentation tree is skipped (AC-26)."""

OWNERSHIP_REASON: str = (
    "existing index was not written by this generator — not overwritten "
    "(IC-13 ownership rule)"
)
"""Reason an index owned by another writer is reported instead of replaced."""

ALREADY_CURRENT_REASON: str = "already up to date — not rewritten"
"""Reason an identical target is reported as ``unchanged`` (IC-13)."""

UNREADABLE_REASON: str = "target not readable — ownership unprovable, not written"
"""Reason an unreadable target is skipped: no ownership, no write (fail-closed)."""

WRITER_SOURCE: str = "docs consolidation"
"""``log.action`` source of this writer (IC-13)."""

DOCS_GENERATOR_ID: str = "doc-indexer/1"
"""Static generator id (IC-14) — also this writer's **ownership anchor**.

It is the only thing that lets a later run tell "this file is mine, I may
update it" apart from "another writer produced this, leave it alone". IC-14
fixes the id as a static version constant precisely so diffs stay stable; W3-2
carries the same value into the ``facts-hash`` footer, so the id survives the
move from this marker into the footer.
"""


def _render_index_document(index_model: Mapping[str, object]) -> str:
    """Return the document this writer is responsible for.

    **The body is provisional and the plan says so.** W3-1 owns the *write
    contract*; the full IC-10 document — sections grouped by kind, one-line
    descriptions, the ``docs-volatile`` section and the IC-14 footer — is W3-2's
    ``render_docs_index``, which replaces this function's body. What is *not*
    provisional is the ownership anchor: :data:`DOCS_GENERATOR_ID` is stamped
    into the output, because without it the ownership rule in
    :func:`sync_docs_consolidation` would freeze the index after its very first
    creation.
    """
    # IC-10/AC-17: the index never lists itself. The filter lives here and not
    # in ``build_index_model`` on purpose — the model stays a faithful
    # description of the tree (W1-8's published contract), while the *document*
    # decides what it lists. It is also what keeps the writer idempotent: a
    # document that counted its own target would change content the moment the
    # file was created, and every later run would rewrite it. Model paths are
    # relative to the docs root, hence the bare file name.
    entries = index_model.get("entries") or ()
    count = sum(1 for entry in entries if entry.get("path") != DOCS_INDEX_FILENAME)
    return (
        "# Documentation Index\n"
        "\n"
        f"<!-- agent-meta:generator {DOCS_GENERATOR_ID} -->\n"
        "\n"
        "Generated by agent-meta from the `docs/` tree — "
        f"{count} page(s) indexed.\n"
    )


def _carries_generator_id(text: str) -> bool:
    """True when *text* carries :data:`DOCS_GENERATOR_ID`.

    Deliberately a substring probe rather than a regex over one exact marker
    spelling: the question is "did this generator produce this file?", not "does
    this file use today's marker?". A strict pattern would make ownership
    unprovable the moment W3-2 moves the id into the IC-14 footer, and an
    unprovable ownership is a permanent skip — the index would freeze on the
    first run after the tree changed. The id is specific enough that a
    hand-written page quoting it is not a realistic collision.
    """
    return DOCS_GENERATOR_ID in text


def _empty_plan() -> dict[str, list[str]]:
    """A fresh all-empty result; a new dict per call, never a shared constant."""
    return {"written": [], "unchanged": [], "skipped": []}


def sync_docs_consolidation(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    provider_config: dict,
    log: SyncLog,
    dry_run: bool,
) -> dict[str, list[str]]:
    """Render the docs index of *project_root* under the IC-13 write contract.

    Returns ``{'written': [...], 'unchanged': [...], 'skipped': [...]}`` — three
    lists of project-relative paths, all three keys always present. The caller
    (W3-4's sync stage) owns *when* this runs; this function owns *what may
    happen*.

    The decision order **is** the contract, and every step can only make the
    outcome more conservative:

    1. **Gate, fail-off (IC-22).** ``docs-consolidation.enabled`` is not exactly
       ``True`` — including a *completely absent* block, which is the shape
       every scenario fixture has — means one ``log.skip`` and **zero**
       filesystem access, not even a stat.
    2. **No docs tree (AC-26).** The index path goes to ``skipped`` with a
       reason. The directory is **never** created: a consumer project without
       documentation did not ask for any.
    3. **Ownership (IC-13).** An existing target is only ever written when it is
       byte-identical (nothing to do) or carries this generator's id. Anything
       else belongs to another writer and is *reported*, never overwritten — a
       hand-edited index has to survive a sync, and so does the spec-plan
       scaffold's ``file-index`` skeleton until W3-3 teaches this function to
       recognise it (IC-15).
    4. **Write.** Exactly one :func:`~scripts.lib.io.write_checked` call, which
       is where the idempotency comparison, the secret scan and ``dry_run``
       live. Under ``dry_run`` it performs only the change detection, so the
       write candidates still surface in ``written`` (AC-23) with nothing on
       disk touched — and the action is tagged ``WOULD-CREATE``/``WOULD-UPDATE``
       rather than ``CREATE``/``UPDATE``, so a dry-run log cannot be misread as
       a record of writes.

    Args:
        agent_meta_root: agent-meta checkout. Unused in W3-1 — the facts
            computation that needs it belongs to W3-2 — but part of the pinned
            signature (IC-13), so the call site does not change on the day it
            starts to matter.
        project_root: the consumer project whose ``docs/`` tree is indexed.
        config: the loaded ``project.yaml`` mapping.
        provider_config: the resolved provider configuration. Unused in W3-1;
            the provider bridge for the hybrid files is W3-7's.
        log: ``SyncLog``, or anything with ``skip``/``note``/``action``.
        dry_run: when True, decide and report but write nothing.

    Returns:
        ``{'written', 'unchanged', 'skipped'}``, always all three keys.
    """
    plan = _empty_plan()
    index_rel = DOCS_INDEX_RELPATH

    block = config.get("docs-consolidation")
    block = block if isinstance(block, dict) else {}
    if block.get("enabled", False) is not True:
        log.skip(LOG_TARGET, DISABLED_REASON)
        return plan

    if not has_docs_tree(project_root):
        plan["skipped"].append(index_rel)
        log.note(LOG_TARGET, f"{index_rel}: {NO_DOCS_TREE_REASON}")
        return plan

    target = safe_path(project_root, index_rel)
    content = _render_index_document(build_index_model(project_root))

    try:
        with target.open("r", encoding="utf-8", newline="") as handle:
            existing: str | None = handle.read()
    except FileNotFoundError:
        tag = "CREATE"
    except (OSError, UnicodeDecodeError) as exc:
        # A directory, a permission problem, a broken link — or bytes that are
        # not UTF-8. The last one is raised by the *read*, not the open, and
        # ``UnicodeDecodeError`` is a ``ValueError``, not an ``OSError``, so an
        # ``except OSError`` alone lets a single latin-1 byte abort the sync in
        # the one place that claims to be hardened. Either way ownership cannot
        # be established, so fail closed and say why rather than clobber
        # whatever is there. The class name only — an OS message can carry a
        # path.
        plan["skipped"].append(index_rel)
        kind = exc.__class__.__name__
        log.note(LOG_TARGET, f"{index_rel}: {UNREADABLE_REASON} ({kind})")
        return plan
    else:
        if existing == content:
            plan["unchanged"].append(index_rel)
            log.note(LOG_TARGET, f"{index_rel}: {ALREADY_CURRENT_REASON}")
            return plan
        if not _carries_generator_id(existing):
            plan["skipped"].append(index_rel)
            log.note(LOG_TARGET, f"{index_rel}: {OWNERSHIP_REASON}")
            return plan
        tag = "UPDATE"

    if write_checked(target, content, log, index_rel, dry_run=dry_run):
        plan["written"].append(index_rel)
        # A dry run must log intent, not a write: ``sync --dry-run --check`` is a
        # CI gate, and a log line tagged CREATE/UPDATE reads as a write that
        # happened. Reuses the ``WOULD-`` tag vocabulary of
        # ``sync_pipeline.py:436-441`` rather than minting a parallel one.
        log.action(f"WOULD-{tag}" if dry_run else tag, index_rel, WRITER_SOURCE)
    return plan
