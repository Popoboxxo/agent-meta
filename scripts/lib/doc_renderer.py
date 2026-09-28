"""Renders the ``agent-meta:docs-*`` marker regions of the hybrid doc files.

Two layers, one module. The **rendering** layer (:data:`DOCS_BLOCK_RE`,
:func:`render_doc_fact_block`, :func:`apply_fact_blocks`,
:func:`render_docs_index`) is a neutral leaf: it knows no documentation file,
opens nothing and **writes nothing** — the caller owns the file. It is a pure
string transformer plus the marker regexes (IC-07), so it stays importable from
anywhere without a cycle (``scripts/lib/config.py`` consumes it, and this
module must not import ``config`` back).

The **writer** layer (:func:`sync_docs_consolidation`, IC-13) is the exception,
and it is deliberately narrow: it owns the *gate*, the *ownership decision* and
the single call into :func:`~scripts.lib.io.write_checked`. It never writes
through a second path — one funnel is what keeps the idempotency check, the
secret scan and ``dry_run`` from drifting apart — and it never imports
``config``, so the IC-11 bridge stays possible.

The writer's second owner is the spec-plan scaffold's ``file-index`` skeleton:
:func:`~scripts.lib.spec_plan_scaffold.is_file_index_skeleton` is consulted
*before* the ownership probe, so a write that takes over the scaffold's
placeholder is logged as the scaffold's file rather than as a bug. The import is
of that function itself, never of a re-implemented probe, so a change to the
F20 marker line cannot leave this module recognising an older skeleton.

:data:`WRITER_FUNCTIONS` names the **only** module-level functions allowed to
touch the disk. It is an allowlist of writers, not of the functions that happen
to be write-free today: the W3-1 review showed that a hardcoded list of
write-free names is a hole, because every function added afterwards is
*unchecked* until someone remembers to add it. A new writer has to be declared
here, which is a visible change; a new pure function costs nothing.

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

import hashlib
import re
from typing import TYPE_CHECKING, Protocol

from .doc_facts import VOLATILE_FACTS, compute_doc_facts
from .doc_index import (
    DOCS_INDEX_FILENAME,
    DOCS_INDEX_RELPATH,
    KIND_ORDER,
    build_index_model,
    has_docs_tree,
)
from .io import safe_path, write_checked
from .spec_plan_scaffold import is_file_index_skeleton, resolve_index_mode

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

FULL_INDEX_MODE: str = "full"
SKELETON_INDEX_MODE: str = "skeleton"
"""The two values of ``docs-consolidation.index-mode`` (W1-9 schema enum)."""

DEFAULT_INDEX_MODE: str = FULL_INDEX_MODE
"""Absence default of ``index-mode`` (IC-22) — the full index replaces the skeleton."""

KE_AUTHORITATIVE_REASON: str = "knowledge-engine index is authoritative"
"""Reason no index is written while the KE index owns the path (IC-13, scenario 52)."""

SKELETON_MODE_REASON: str = (
    "index-mode: skeleton — the scaffold skeleton is always kept (IC-15)"
)
"""Reason ``index-mode: skeleton`` suppresses every write (IC-13, AC-21)."""

UNKNOWN_INDEX_MODE_REASON: str = (
    "index-mode is neither 'full' nor 'skeleton' — not written (fail-closed, IC-22)"
)
"""Reason an unrecognised ``index-mode`` suppresses every write, fail-closed.

The schema closes the enum, so this is the typo path rather than a supported
value. It is a separate reason because claiming "the skeleton is kept" for a mode
that means nothing would put a false statement in a sync log.

The enum read here is ``docs-consolidation.index-mode`` (``full``/``skeleton``)
and nothing else. A project also carries a *second*, unrelated index vocabulary
— ``spec-plan-workflow.index.mode``, whose third value is ``off`` — and a value
from that one is not a typo; :func:`_index_mode_block_reason` explains where it
lands.
"""

SCAFFOLD_SKELETON_REASON: str = (
    "target is the scaffold skeleton — replaced by the full index (IC-15)"
)
"""Reason a scaffold skeleton **is** writable, and the note that says so.

Without it the one run that legitimately overwrites another module's file is
indistinguishable in the log from a bug.
"""

DOCS_GENERATOR_ID: str = "doc-indexer/1"
"""Static generator id (IC-14) — also this writer's **ownership anchor**.

It is the only thing that lets a later run tell "this file is mine, I may
update it" apart from "another writer produced this, leave it alone". IC-14
fixes the id as a static version constant precisely so diffs stay stable; W3-2
carries the same value into the ``facts-hash`` footer, so the id survives the
move from this marker into the footer.

It MUST stay in the rendered bytes. :func:`_carries_generator_id` is a substring
probe over the whole document, so an id that disappeared from the render output
would make every index this generator wrote look foreign — a permanent
``skipped`` on every later run, with a green sync log and a frozen index. The
footer line is therefore the id's *only* carrier and is asserted by its own
test.
"""

WRITER_FUNCTIONS: frozenset[str] = frozenset({"sync_docs_consolidation"})
"""The **only** module-level functions permitted to reach the disk (IC-13).

An allowlist of *writers*, inverted on purpose. The W3-1 review proved the
opposite shape is a hole: a hardcoded list of write-free function names leaves
every function added afterwards unchecked, so a ``write_text`` smuggled into
``_carries_generator_id`` — or into the next function this wave adds — passed
the guard silently. Here a new pure function is covered by default and a new
writer has to be declared, which is a visible, reviewable change.

The writer is still held to the single-funnel rule: it may *read* its target,
but every mutation goes through :func:`~scripts.lib.io.write_checked`.
"""


# --------------------------------------------------------------------------
# IC-10 document + IC-14 footer (W3-2)
# --------------------------------------------------------------------------

INDEX_TITLE: str = "# Documentation Index"
"""First line of the generated index (IC-10)."""

INDEX_PREAMBLE: str = (
    "> Generated by agent-meta `sync.py` (docs-consolidation). Do not edit by hand —\n"
    "> every region below is regenerated on each sync. Hand prose lives in the pages\n"
    "> this index links to.\n"
)
"""IC-10's hand-edit warning, reproduced verbatim. Prose, not a marker region."""

SECTION_HEADING_TEMPLATE: str = "## {kind}"
"""One section per :data:`~scripts.lib.doc_index.KIND_ORDER` group that has pages."""

ENTRY_LINE_TEMPLATE: str = "- [{title}]({path}) — {description}"
"""IC-10's per-page line: link, then the real one-line description."""

VOLATILE_HEADING: str = "## volatile"
"""IC-10(e): the volatile section is the **last** section before the footer."""

VOLATILE_BEGIN_MARKER: str = "<!-- agent-meta:docs-volatile:begin -->"
VOLATILE_END_MARKER: str = "<!-- agent-meta:docs-volatile:end -->"

FACTS_BEGIN_MARKER: str = "<!-- agent-meta:docs-facts:begin -->"
FACTS_END_MARKER: str = "<!-- agent-meta:docs-facts:end -->"

FOOTER_BEGIN_MARKER: str = "<!-- agent-meta:docs-footer -->"
FOOTER_END_MARKER: str = "<!-- /agent-meta:docs-footer -->"
"""IC-14's footer markers, spelled exactly as the spec writes them.

The closing marker carries a leading slash (``/agent-meta:``) while the opening
one does not. That asymmetry is the spec's own spelling and is reproduced
verbatim: the footer is a published interface, and "tidying" it would make
every already-written index fail a check that expects today's marker.
"""

FACTS_HASH_CHARS: int = 16
"""Hex characters of the IC-14 ``facts-hash`` — 16, per the spec."""

VOLATILE_ROW_TEMPLATE: str = "| {name} | {value} |"
"""One volatile row. The fact **key** is the row label, never a hand-written
alias: a label map would be a second copy of the IC-02 fact table, free to
drift from the first.

**DEVIATION from IC-10's literal wording** (its sample renders human labels —
``| Version | 1.2.0 |``, ``| Scenarios | 63 |`` — where this module prints
``| DOCS_VERSION | 1.2.0 |`` and ``| DOCS_SCENARIO_COUNT | 63 |``): the row
label **is** the fact key, by design, and that is the whole reason. There is no
label registry in this repository, so a "Version" would have to come from one of
two places, both worse than the key: a hard-coded table in this module (a second
copy of the IC-02 fact table, free to drift from the first and to disagree with
it inside one file) or a per-fact label in ``doc_facts`` (a fact-name coupling
in the computer, so renaming a fact silently renames its label in generated
documentation). The key is the one spelling that is already in the code, the
config and the test suite, so it cannot rot.

This is **not** a leak into the non-volatile table: ``DOCS_REPO_FACTS_BLOCK``
renders the same convention for the same reason, which is why the two tables
read alike. Recorded here, in-module, so that the later W3 tasks and the V-gates
treat it as settled rather than re-litigating it as a missing label map. The
trade is legibility-for-humans against a second source of truth, and for a
*generated* file the source of truth wins; IC-10's sample is illustrative, not
a row contract, and the row's column headers carry the meaning a label would.
"""

VOLATILE_SECTION_NAME: str = "volatile"
"""Region name used in the ``docs-empty`` placeholder of the volatile section."""

_LINK_ESCAPES: dict[str, str] = {"[": "\\[", "]": "\\]"}
"""Characters that would otherwise break a Markdown link text.

A ``]`` inside a link text closes the link early, so a page titled
``Agent [se]`` would produce broken markup in a file nobody may hand-edit.

Escaping is a table lookup rather than a chained ``str.replace`` for a reason
that is not aesthetic: ``Path.replace`` is a *rename* and ``str.replace`` is not,
and a name-only call scan — which is how the write-free guard sees the module —
cannot tell them apart. Using a name that is unambiguous in both readings keeps
the guard's vocabulary honest instead of forcing it to whitelist an exception.
"""


def _escape_link_text(title: str) -> str:
    """Return *title* with the characters of :data:`_LINK_ESCAPES` neutralised."""
    return "".join(_LINK_ESCAPES.get(char, char) for char in title)


def _entry_link(entry: Mapping[str, object]) -> str:
    """One IC-10 list line for *entry*, carrying its real description.

    The description is rendered **verbatim**, including
    :data:`~scripts.lib.doc_index.EMPTY_DESCRIPTION`. This module invents
    nothing: a page without frontmatter shows the placeholder, which is the
    whole reason the placeholder exists. Substituting a summary here would
    recreate, inside the generated index, the exact defect class (F8/F15) this
    initiative exists to remove.
    """
    return ENTRY_LINE_TEMPLATE.format(
        title=_escape_link_text(str(entry.get("title", ""))),
        path=str(entry.get("path", "")),
        description=str(entry.get("description", "")),
    )


def _sections(index_model: Mapping[str, object]) -> list[str]:
    """The per-kind sections, in :data:`KIND_ORDER`, each with its pages.

    A kind with no pages gets **no heading at all** — an empty ``## spikes``
    section is noise in a generated file, and its presence would change the
    document the moment the first spike lands, for no informational gain.

    Ordering comes from :data:`~scripts.lib.doc_index.KIND_ORDER` rather than
    from the model's arrival order. The model already sorts by it (W1-8), but
    relying on that would make the document's shape a *consequence* of the
    model's internals: a model that stopped sorting would silently reshuffle
    every section. The renderer states the order it needs.

    Kinds outside :data:`KIND_ORDER` are an error, not a new section — a page
    would otherwise drop out of the index without a trace, and a silently
    missing page is the failure V2 exists to prevent. They are listed under a
    visible marker instead, so the page stays reachable and the reason it is in
    the wrong place is in the file.
    """
    # IC-10(c)/AC-17: the index never lists itself. The filter lives here and
    # not in ``build_index_model`` on purpose — the model stays a faithful
    # description of the tree (W1-8's published contract), while the *document*
    # decides what it lists. It is also what keeps the writer idempotent: a
    # document that counted its own target would change content the moment the
    # file was created, and every later run would rewrite it. Model paths are
    # relative to the docs root, hence the bare file name.
    entries = [
        entry
        for entry in (index_model.get("entries") or ())
        if entry.get("path") != DOCS_INDEX_FILENAME
    ]
    lines: list[str] = []
    for kind in KIND_ORDER:
        group = [entry for entry in entries if entry.get("kind") == kind]
        if not group:
            continue
        lines.append(SECTION_HEADING_TEMPLATE.format(kind=kind))
        lines.extend(_entry_link(entry) for entry in group)
        lines.append("")
    unknown = sorted(
        {str(e.get("kind", "")) for e in entries if e.get("kind") not in KIND_ORDER}
    )
    for kind in unknown:
        lines.append(f"<!-- agent-meta:docs-unknown-kind: {kind or '(empty)'} -->")
        lines.extend(_entry_link(e) for e in entries if str(e.get("kind", "")) == kind)
        lines.append("")
    return lines


def _volatile_rows(facts: Mapping[str, str]) -> list[str]:
    """Markdown table rows for every computable volatile fact, key-sorted.

    Sorted by fact key, never by the frozenset's iteration order: a
    ``frozenset`` of strings has no guaranteed order across processes, and the
    document must be byte-identical between two runs of the same sync. The
    values come from the *mapping*, so a volatile fact the caller did not
    compute gets no row instead of an empty one.
    """
    return [
        VOLATILE_ROW_TEMPLATE.format(name=name, value=facts[name])
        for name in sorted(VOLATILE_FACTS)
        if facts.get(name)
    ]


def _volatile_section(facts: Mapping[str, str]) -> list[str]:
    """The ``docs-volatile`` block: heading, markers, rows (IC-10, IC-14).

    This block is the **last** section before the footer, and that placement is
    the contract, not cosmetics: a scenario that lands changes exactly one line
    of the document, so a reviewer reads a one-line diff instead of hunting
    through a reshuffled file (R1/M7).
    """
    rows = _volatile_rows(facts)
    return [
        VOLATILE_HEADING,
        VOLATILE_BEGIN_MARKER,
        *(rows or [EMPTY_MARKER_TEMPLATE.format(name=VOLATILE_SECTION_NAME)]),
        VOLATILE_END_MARKER,
    ]


def _facts_section(facts: Mapping[str, str]) -> list[str]:
    """The ``docs-facts`` block: the non-volatile fact table (IC-10).

    The region body is :func:`render_doc_fact_block`'s output for the ``facts``
    region — the same call the hybrid files make. That is deliberate: the
    ``DOCS_REPO_FACTS_BLOCK`` value is already a ``| Fact | Value |`` table of
    exactly the non-volatile, non-pending scalars, and a second fact table
    rendered here would be a second copy of the IC-02 table, free to drift from
    the first and to disagree with it inside one file. Sharing the call also
    shares its ``docs-empty`` fallback, so an uncomputed fact is visible in
    review here exactly as it is in ``README.md`` (IC-07(d)).
    """
    return [
        FACTS_BEGIN_MARKER,
        render_doc_fact_block("facts", facts).strip("\n"),
        FACTS_END_MARKER,
    ]


def compute_facts_hash(facts: Mapping[str, str]) -> str:
    """The IC-14 ``facts-hash``: sha256 over the sorted **non-volatile** facts.

    ``sha256("\\n".join(sorted(f"{k}={v}" for k in stable facts))[:16]`` — the
    algorithm is the spec's, character for character, because a "cleaner"
    variant would produce a different digest for the same facts and every
    already-written index would then look stale.

    Volatile facts are excluded (AC-03): Track A adds scenarios continuously, and
    a hash that moved with the scenario count would rewrite the footer of every
    index in the repository for a change that carries no meaning. Their values
    are still rendered, in the ``docs-volatile`` section.

    The result is truncated to :data:`FACTS_HASH_CHARS` hex characters. The
    payload is hashed as UTF-8 so the digest cannot depend on the platform's
    default encoding.

    **Two known, deliberately unguarded properties of this digest.** Both are
    recorded here so that a later task does not "fix" them and invalidate every
    index already written; neither is a defect to be closed, and the algorithm is
    spec-pinned (IC-14) and **must not change** — a different digest for the same
    facts would make every written index look stale on the next run, and for a
    documentation index *stability* is worth more than injectivity.

    1. **A newline inside a fact value is indistinguishable from a row
       separator.** The payload is a ``"\\n"`` join of ``f"{k}={v}"``, so
       ``{"A": "1\\nB=2"}`` and ``{"A": "1", "B": "2"}`` hash to the *same*
       digest (both are the three-byte-plus text ``A=1\\nB=2``). This is
       **reachable today**, not theoretical: 7 of the 22 live facts are
       multi-line (every ``*_BLOCK`` fact — ``DOCS_AGENT_ROSTER_BLOCK``,
       ``DOCS_REPO_FACTS_BLOCK``, ``DOCS_PIPELINES_BLOCK``, ``DOCS_HOOKS_BLOCK``,
       ``DOCS_PROVIDERS_BLOCK``, ``DOCS_TIER_PRESET_BLOCK``,
       ``DOCS_DOD_PRESET_BLOCK``), and all 7 are non-volatile, i.e. inside the
       hashed payload. The collision is accepted, not guarded: escaping newlines
       would change every digest in the repository, and the colliding inputs
       would have to be *two different facts* that happen to spell the same
       joined text — which a reader of the rendered table can see is not the
       case.
    2. **NFC vs NFD changes the digest of an unchanged repository.** No Unicode
       normalisation is applied, so a normalising filesystem or editor that
       rewrites precomposed codepoints in decomposed form changes the bytes and
       therefore the hash. The roster block is the reachable case:
       ``DOCS_AGENT_ROSTER_BLOCK`` holds precomposed codepoints, and NFC/NFD of
       it are two different texts with two different digests. Again deliberate —
       normalising would mean the digest depends on a normalisation *choice*
       rather than on the file, and the same "stale every index" cost applies.
    """
    payload = "\n".join(
        sorted(
            f"{name}={value}" for name, value in facts.items() if name not in VOLATILE_FACTS
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:FACTS_HASH_CHARS]


def render_docs_index(index_model: Mapping[str, object], facts: Mapping[str, str]) -> str:
    """Return the full IC-10 ``docs/INDEX.md`` document, IC-14 footer included.

    A **pure function** of its two arguments: no filesystem access, no clock, no
    host data, no absolute path. The bytes are a function of the model and the
    facts alone, so two runs over one tree are byte-identical (NFA-01/AC-17) and
    the checkout location cannot leak into tracked documentation (NFA-02).

    Document shape, in order: title, IC-10's hand-edit warning, one section per
    non-empty :data:`KIND_ORDER` group, the ``docs-facts`` table, the
    ``docs-volatile`` section (last, IC-10(e)) and the IC-14 footer. Every page
    appears exactly once as a link; ``docs/INDEX.md`` itself never (IC-10(c)).

    Args:
        index_model: :func:`~scripts.lib.doc_index.build_index_model`'s output —
            the W1-8 contract, entries sorted by kind then path.
        facts: the computed ``DOCS_*`` facts. Volatile values render into the
            volatile section and are excluded from the hash.

    Returns:
        The document, terminated by a single newline.
    """
    lines = [INDEX_TITLE, "", INDEX_PREAMBLE.rstrip("\n"), ""]
    lines.extend(_sections(index_model))
    lines.extend(_facts_section(facts))
    lines.append("")
    lines.extend(_volatile_section(facts))
    lines.append("")
    lines.extend(
        [
            FOOTER_BEGIN_MARKER,
            f"facts-hash: {compute_facts_hash(facts)}",
            f"generator: {DOCS_GENERATOR_ID}",
            FOOTER_END_MARKER,
        ]
    )
    return "\n".join(lines) + "\n"


def _carries_generator_id(text: str) -> bool:
    """True when *text* carries :data:`DOCS_GENERATOR_ID`.

    Deliberately a substring probe rather than a regex over one exact marker
    spelling: the question is "did this generator produce this file?", not "does
    this file use today's marker?". A strict pattern would have made ownership
    unprovable the moment W3-2 moved the id into the IC-14 footer, and an
    unprovable ownership is a permanent skip — the index would have frozen on
    the first run after the tree changed. The id is specific enough that a
    hand-written page quoting it is not a realistic collision.
    """
    return DOCS_GENERATOR_ID in text


def _empty_plan() -> dict[str, list[str]]:
    """A fresh all-empty result; a new dict per call, never a shared constant."""
    return {"written": [], "unchanged": [], "skipped": []}


def _index_mode_block_reason(config: dict) -> str | None:
    """Why the config forbids an index write at all, or ``None`` for permission.

    Two independent owners of the same path, both decided from configuration
    alone, so neither depends on what happens to be on disk (IC-13, IC-15):

    * ``resolve_index_mode() == "knowledge-engine"`` — the knowledge engine owns
      the index. Scenario 52 asserts no ``docs/INDEX.md`` is written there, and
      the scaffold does not write one either, so the generator has nothing to do
      in that project.
    * ``docs-consolidation.index-mode: skeleton`` — the scaffold skeleton is
      always kept, so the generator writes nothing, not even on a first run into
      an empty tree. A mode that only blocked the *replacement* would still seed
      a full index into a project that asked for a skeleton.

    An ``index-mode`` outside the schema's enum is treated as *not* ``full``:
    fail-closed, and a reason that says so instead of guessing which mode was
    meant.

    **Two index vocabularies meet here, and only one of them is closed.**
    ``spec-plan-workflow.index.mode`` is ``knowledge-engine`` / ``file-index`` /
    ``off``; ``docs-consolidation.index-mode`` is ``full`` / ``skeleton``. The two
    owners above are the complete list of what forbids a write, so ``off`` is
    **not** one of them: it is :func:`resolve_index_mode`'s way of saying the
    *scaffold* writes no fallback index, hence claims no file on this path — with
    no placeholder to protect, the full index may own ``docs/INDEX.md``, and a
    write is permitted. ``off`` also does not stop a *leftover* skeleton from
    being replaced, since that replacement is the scaffold-ownership step, not a
    mode gate; IC-13/IC-15 do not settle that case, so both are pinned by
    :func:`test_index_mode_off_permits_the_full_index` rather than argued here.
    Treating ``off`` as fail-closed would be a different contract, and a
    behaviour change — not a docstring fix.

    Args:
        config: the loaded ``project.yaml`` mapping.

    Returns:
        The reason to log, or ``None`` when the configuration permits a write.
    """
    if resolve_index_mode(config)[0] == "knowledge-engine":
        return KE_AUTHORITATIVE_REASON
    block = config.get("docs-consolidation")
    block = block if isinstance(block, dict) else {}
    mode = block.get("index-mode", DEFAULT_INDEX_MODE)
    if mode == SKELETON_INDEX_MODE:
        return SKELETON_MODE_REASON
    if mode != FULL_INDEX_MODE:
        return UNKNOWN_INDEX_MODE_REASON
    return None


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
    3. **Index mode (IC-13, IC-15).** Two configuration facts forbid a write
       outright — a knowledge-engine project, whose KE index owns the path
       (scenario 52), and ``index-mode: skeleton``, which keeps the scaffold
       skeleton whatever is on disk. Both are decided from *configuration*, so
       they cost no filesystem access and cannot be outrun by whatever the target
       happens to contain. This step runs before the facts for the same reason
       the two above do: no work, no cost, for a run that is going to skip.
    4. **Facts.** :func:`~scripts.lib.doc_facts.compute_doc_facts` turns
       *agent_meta_root* into the ``DOCS_*`` mapping, which the IC-10 document
       renders. It never raises and writes nothing (AC-01), so a missing or
       half-readable checkout degrades to empty facts and the ``docs-empty``
       placeholders rather than aborting a sync. It runs *after* the gates
       above on purpose: a disabled run must not touch the source checkout at
       all, and a consumer project without docs must not pay for facts it will
       never render.
    5. **Ownership (IC-13).** An existing target is only ever written when it is
       byte-identical (nothing to do), is the spec-plan scaffold's ``file-index``
       skeleton (the one file this generator is *allowed* to take over, IC-15),
       or carries this generator's id. Anything else belongs to another writer
       and is *reported*, never overwritten — a hand-edited index has to survive
       a sync.

       The scaffold check is consulted **before** the generator-id probe. The
       two branches are a *union* of write permissions — a skeleton and a
       generator-owned index are both writable, anything else is not — so either
       order yields the same outcome; guard-first is a readability preference,
       because it keeps the linear shape and makes the note name the real owner
       (the scaffold) instead of a foreign writer. What *is* load-bearing is the
       order of this step and step 3: the mode gate has to run before the
       ownership block, or a knowledge-engine project reports ``OWNERSHIP_REASON``
       (or plain ``unchanged``) instead of its own authoritative-mode note, and
       the ownership step's early returns would bypass the mode decision
       entirely.
    6. **Write.** Exactly one :func:`~scripts.lib.io.write_checked` call, which
       is where the idempotency comparison, the secret scan and ``dry_run``
       live. Under ``dry_run`` it performs only the change detection, so the
       write candidates still surface in ``written`` (AC-23) with nothing on
       disk touched — and the action is tagged ``WOULD-CREATE``/``WOULD-UPDATE``
       rather than ``CREATE``/``UPDATE``, so a dry-run log cannot be misread as
       a record of writes.

    Args:
        agent_meta_root: the agent-meta checkout the ``DOCS_*`` facts are
            computed from. Part of the pinned signature (IC-13); W3-1 declared it
            unused, W3-2 is where it starts to matter. The **parameter list is
            unchanged** — only the body grew.
        project_root: the consumer project whose ``docs/`` tree is indexed.
        config: the loaded ``project.yaml`` mapping, passed through to the facts
            computation (it resolves the enabled roles and pipelines).
        provider_config: the resolved provider configuration, passed through for
            the same reason; the provider *bridge* for the hybrid files is W3-7's.
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

    mode_reason = _index_mode_block_reason(config)
    if mode_reason is not None:
        plan["skipped"].append(index_rel)
        log.note(LOG_TARGET, f"{index_rel}: {mode_reason}")
        return plan

    target = safe_path(project_root, index_rel)
    # The facts are computed here and not above: both gates have already
    # short-circuited, so a disabled run and a project without a docs tree never
    # read the source checkout. ``compute_doc_facts`` is itself a pure reader
    # (AC-01) — it never raises and never writes under either root.
    facts = compute_doc_facts(
        agent_meta_root, config, provider_config=provider_config, log=log
    )
    content = render_docs_index(build_index_model(project_root), facts)

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
        if is_file_index_skeleton(existing):
            # IC-15: the spec-plan scaffold's placeholder is the one file this
            # generator may take over, and the only one that carries no
            # ``doc-indexer/1``. Consulted *before* the id probe on purpose --
            # see the decision order in this function's docstring.
            log.note(LOG_TARGET, f"{index_rel}: {SCAFFOLD_SKELETON_REASON}")
        elif not _carries_generator_id(existing):
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
