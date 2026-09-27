"""Documentation freshness checks — does the prose match the computed state?

Family of the file-check cut of Spec §4.1 (U-1, decision U-1 / K18): the cut
follows **the question a check asks**, not file size and not the wave a check
belongs to. This module owns exactly one question — *"Does the documentation
match the computed actual state?"* — and therefore exactly the checks that
compare a hand-written number against a computed one:

* **V1a/V1b** ``check_no_manual_counts`` (AC-07, AC-08) — implemented here
  (W2-1).
* **V6** ``check_docs_facts_fresh`` (AC-36, IC-23, R14) — implemented here
  (W2-5): the two comparisons a rendered fact has to pass, the marker region
  and the hand-maintained oracle. It is also the reason the V1 tests live in
  ``tests/test_doc_freshness.py``.
* **V5** ``check_role_generation_parity`` — W2-4, assigned here by Spec §4.1
  because it compares a documented inventory against the actually generated
  one, which is the same question as V1 and V6.

No check of any other module answers that question, so no check is shared with
``docs_links``. The 600-line ceiling is a consequence of the cut, not its
purpose (K18).

``docs.py`` stays the facade the runner and the test suite import (K19); this
module is reached through it. Nothing here is stdlib-external.
"""

from __future__ import annotations

import re
from itertools import zip_longest
from pathlib import Path

from ..doc_facts import (
    EXPECTED_DOC_FACTS_RELPATH,
    MISMATCH_KIND,
    MISSING_IN_EXPECTED_KIND,
    compare_expected_doc_facts,
    compute_doc_facts,
    load_expected_doc_facts,
)
from ..doc_renderer import (
    DOCS_BEGIN_RE,
    DOCS_BLOCK_RE,
    REGION_FACT_KEYS,
    is_valid_region,
    render_doc_fact_block,
)
from ..io import load_yaml_file
from .report import Finding, Severity

# ---------------------------------------------------------------------------
# V1 — check_no_manual_counts (IC-05, spec §5.1.1, plan W2-1)
# ---------------------------------------------------------------------------
#
# V1 does not check the *value* of a number; it checks the **absence of a
# marker region at that place**. An author either lets the number be generated
# into an ``agent-meta:docs-begin`` … ``agent-meta:docs-end`` region, or marks
# the line deliberately with ``agent-meta:docs-exempt``. There is no silent
# pass-by.
#
# Two disjoint branches (the rev-0.1 regex is dead — it matched none of the
# verified quote lines and is not used here):
#
# * **V1a "counted thing"** — a bare integer token ``\b\d{1,4}\b`` that is not
#   part of a dotted ``\d+(\.\d+)+`` token, with a whitelisted noun at most
#   ``V1_MAX_TOKEN_GAP`` tokens away **in either direction** on the same line.
# * **V1b "version literal"** — a Semver-like ``\d+.\d+.\d+[-suffix]`` on a line
#   that also contains ``version`` (case-insensitive).
#
# Disjointness is structural, not incidental: ``v1a_count_spans`` drops every
# integer token whose span lies inside a dotted numeric span, and
# ``v1b_version_spans`` only ever returns spans that *are* dotted numeric spans.
# No character range can therefore be reported by both branches.
#
# Severity: WARNING by default, ERROR once ``docs-consolidation.checks.strict``
# is ``true`` (IC-05 "V2: WARNING, nach W3: ERROR" — the promotion itself is
# W3-4's job, this check only reads the key).

V1_CHECK_ID = "docs.no_manual_counts"

#: Entry documents that are expected to carry the rendered ``DOCS_*`` facts.
V1_SCAN_RELPATHS: tuple[str, ...] = ("README.md", "llms.txt", "ARCHITECTURE.md")

#: Suppression rule 4 — a file that is itself generated never carries a
#: hand-maintained count, because every number in it came from the generator.
V1_GENERATED_RELPATHS = frozenset({"docs/INDEX.md"})

V1_MAX_TOKEN_GAP = 3

V1_REGION_BEGIN = "agent-meta:docs-begin"
V1_REGION_END = "agent-meta:docs-end"
V1_EXEMPT_MARKER = "agent-meta:docs-exempt"

V1_SUGGESTION = (
    "Move the number into an agent-meta:docs-begin/docs-end region so it is "
    f"generated, or mark the line `{V1_EXEMPT_MARKER}: <reason>`."
)

#: ``\d+(\.\d+)+`` plus an optional pre-release tail — any dotted numeric
#: token. Used to exclude V1a false positives and to recognise a V1b candidate.
#: The tail matters: without it the trailing ``1`` of ``1.2.3-rc.1`` would look
#: like a bare count and would overlap the V1b span of the same line.
_V1_DOTTED_RE = re.compile(r"\d+(?:\.\d+)+(?:-\w[\w.]*)?")
#: Semver-like literal with an optional ``v`` prefix.
#:
#: The spec writes ``\b\d+\.\d+\.\d+...\b``. That form does **not** match its
#: own positive fixture: ``(v1.0.0)`` has a word character in front of the
#: leading digit, so ``\b`` fails there and line 4 would report nothing. The
#: boundary is therefore written as a lookbehind that tolerates the ``v``
#: prefix, which is the only way the line the spec mandates can fire at all.
_V1_SEMVER_RE = re.compile(r"(?<![0-9A-Za-z.])v?\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?")
#: A bare integer of 1..4 digits. A count, never a version and never a year
#: long enough to be one (deliberate: a year next to a whitelisted noun is
#: indistinguishable from a count and is exempt-able).
_V1_COUNT_RE = re.compile(r"\b\d{1,4}\b")

#: Whitelisted nouns, case-insensitive, singular and plural.
_V1_NOUN_RE = re.compile(
    r"^(?:agents?|hooks?|providers?|pipelines?|presets?|tiers?|templates?"
    r"|configs?|commands?|scenarios?|szenarios?|szenarien?|roles?|skills?"
    r"|rules?|tests?)$",
    re.IGNORECASE,
)
#: Whitespace-separated word with its character span.
_V1_WORD_RE = re.compile(r"\S+")
#: Opening code fence (``` or ~~~), 0..3 leading spaces per CommonMark.
_V1_FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
#: Punctuation stripped off a word before it is tested against the noun list.
_V1_WORD_TRIM = "()[]{}<>|#*_\"',;:!?/\\`"

Span = tuple[int, int, str]


def _dotted_spans(line: str) -> list[Span]:
    return [(m.start(), m.end(), m.group(0)) for m in _V1_DOTTED_RE.finditer(line)]


def _inside(span: Span, others: list[Span]) -> bool:
    start, end, _text = span
    return any(o_start <= start and end <= o_end for o_start, o_end, _ in others)


def v1a_count_spans(line: str) -> list[Span]:
    """V1a number tokens of ``line``, left to right.

    A bare integer that is part of a dotted numeric token is **not** a count —
    that is what keeps ``v1.0.0`` out of V1a and makes the two branches
    disjoint. The exclusion is a purely lexical property of the token, so it
    holds whether or not the line also says ``version``.
    """
    dotted = _dotted_spans(line)
    return [
        (m.start(), m.end(), m.group(0))
        for m in _V1_COUNT_RE.finditer(line)
        if not _inside((m.start(), m.end(), m.group(0)), dotted)
    ]


def v1b_version_spans(line: str) -> list[Span]:
    """V1b Semver-like literals of ``line``, left to right."""
    return [(m.start(), m.end(), m.group(0)) for m in _V1_SEMVER_RE.finditer(line)]


def _words(line: str) -> list[tuple[int, Span]]:
    """Whitespace-separated words as ``(index, (start, end, word))``.

    A token without an alphanumeric character (``##``, ``|``, ``—``) is not a
    word and does not count towards the token gap — otherwise Markdown
    structure, not prose distance, would decide a finding.
    """
    words: list[tuple[int, Span]] = []
    for match in _V1_WORD_RE.finditer(line):
        word = match.group(0).strip(_V1_WORD_TRIM)
        if not any(ch.isalnum() for ch in word):
            continue
        words.append((len(words), (match.start(), match.end(), word)))
    return words


def _v1a_hit(line: str) -> tuple[str, str] | None:
    """First ``(number, noun)`` pair of ``line`` that V1a accepts, or ``None``."""
    words = _words(line)
    nouns = {index: word for index, _start_end, word in
             ((i, span[0], span[2]) for i, span in words)
             if _V1_NOUN_RE.match(word)}
    for start, _end, number in v1a_count_spans(line):
        here = next((i for i, span in words if span[0] <= start <= span[1]), None)
        if here is None:
            continue
        best: tuple[int, str] | None = None
        for index, noun in nouns.items():
            gap = abs(index - here) - 1
            if gap <= V1_MAX_TOKEN_GAP and (best is None or gap < best[0]):
                best = (gap, noun)
        if best is not None:
            return number, best[1]
    return None


def _v1_is_generated(relpath: str) -> bool:
    """Suppression rule 4: the file is generated, so its numbers are computed."""
    return relpath in V1_GENERATED_RELPATHS


def _v1_suppressed_lines(text: str) -> set[int]:
    """Line numbers killed by suppression rules 1, 2 and 3 (§5.1.1).

    Rule 1 — inside an ``agent-meta:docs-begin`` … ``agent-meta:docs-end``
    region (both delimiters included).
    Rule 2 — the line carries an ``agent-meta:docs-exempt`` marker.
    Rule 3 — the line is inside a Markdown fenced code block that declares a
    language (```` ```text ```` or ``~~~yaml``); the fence delimiters themselves
    carry no number.

    Rule 3 is narrowed to **typed** fences (K16 / B-4 / E-14, §5.1.1). An
    opening fence **without** an info string is a fenced code block just like
    every other one — it only declares no language — so V1 scans its content as
    a literal transcript. In the entry documents that is exactly where the
    hand-maintained inventory lives: the ``README.md`` directory structure
    opens untyped at ``:680``, closes at ``:737`` and carries the IC-05 sites
    F2 (``:688``), F3-Site-2 (``:690``) and F4 (``:734``). Suppressing it made
    rule 3 incompatible with IC-05.

    The narrowing is keyed on the Markdown info string only — no language
    allowlist, no path or section heuristic, no per-line number rule — so it
    cannot special-case the four sites. The fence state machine is unaffected:
    an untyped block is still tracked, which keeps a tagged fence that follows
    it from being misread as its closing delimiter (i.e. rule 3 is narrowed,
    never switched off).
    """
    suppressed: set[int] = set()
    in_region = False
    fence: str | None = None
    fence_suppresses = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        if fence is not None:
            closing = re.fullmatch(rf" {{0,3}}{re.escape(fence[0])}{{{len(fence)},}}\s*", line)
            if closing is None:
                if fence_suppresses:
                    suppressed.add(lineno)
                continue
            fence = None
            fence_suppresses = False
            continue
        opening = _V1_FENCE_OPEN_RE.match(line)
        if opening is not None:
            fence = opening.group(1)
            fence_suppresses = bool(line[opening.end():].strip())
            continue
        if V1_REGION_BEGIN in line:
            in_region = True
        if in_region or V1_EXEMPT_MARKER in line:
            suppressed.add(lineno)
        if V1_REGION_END in line:
            in_region = False
    return suppressed


def v1_strict(config: dict | None) -> bool:
    """``docs-consolidation.checks.strict`` — absent means ``False``.

    Same absence semantics as the generator (IC-22 / ``knowledge.py:127``): a
    missing block and an explicit ``false`` are observationally identical.
    """
    block = (config or {}).get("docs-consolidation")
    if not isinstance(block, dict):
        return False
    checks = block.get("checks")
    if not isinstance(checks, dict):
        return False
    return bool(checks.get("strict", False))


def _v1_finding(severity: Severity, relpath: str, lineno: int, branch: str,
                message: str) -> Finding:
    """Build the house ``Finding`` and attach the two attributes IC-05 requires.

    ``Finding`` (``report.py``) has no ``line`` and no ``branch`` field and that
    module is not owned by W2-1, so the attributes are set on the instance.
    W2-7, which owns both the runner registration and the common gate, should
    promote them to dataclass fields so ``--json`` stops dropping them.
    """
    finding = Finding(
        severity=severity,
        check=V1_CHECK_ID,
        file=relpath,
        message=message,
        suggestion=V1_SUGGESTION,
    )
    finding.line = lineno
    finding.branch = branch
    return finding


def check_no_manual_counts(root: Path, config: dict | None = None) -> list[Finding]:
    """V1: hand-maintained counts and version literals in the entry documents.

    ``config`` is the project config dict; only
    ``docs-consolidation.checks.strict`` is read (severity). The
    ``docs-consolidation.enabled`` common gate and the runner registration
    belong to W2-7 — until then this function is a no-op in practice because
    nothing calls it (AC-38).
    """
    severity = Severity.ERROR if v1_strict(config) else Severity.WARNING
    findings: list[Finding] = []
    for relpath in V1_SCAN_RELPATHS:
        if _v1_is_generated(relpath):
            continue
        path = root / relpath
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        suppressed = _v1_suppressed_lines(text)
        for lineno, line in enumerate(text.splitlines(), start=1):
            if lineno in suppressed:
                continue
            hit = _v1a_hit(line)
            if hit is not None:
                number, noun = hit
                findings.append(_v1_finding(
                    severity, relpath, lineno, "V1a",
                    f"line {lineno}: hand-maintained count {number!r} next to "
                    f"{noun!r} outside a marker region",
                ))
            if "version" in line.lower():
                versions = v1b_version_spans(line)
                if versions:
                    findings.append(_v1_finding(
                        severity, relpath, lineno, "V1b",
                        f"line {lineno}: hand-maintained version literal "
                        f"{versions[0][2]!r} on a 'version' line",
                    ))
    return findings


# ---------------------------------------------------------------------------
# V6 — check_docs_facts_fresh (IC-05, IC-23, AC-36, R14, plan W2-5)
# ---------------------------------------------------------------------------
# Two axes, three kinds. ``handedit`` (ERROR): a rendered marker region differs
# from ``render_doc_fact_block`` on the computed facts. ``expected-mismatch``
# (ERROR): the facts differ from ``config/doc-facts-expected.yaml`` (IC-23).
# ``missing-in-expected`` (WARNING): a pinnable fact the oracle does not carry
# — IC-23 lets the file grow, so that is not a defect. ``checks.strict`` is
# deliberately **not** read: V6 is ERROR from its first wave, unlike V1.
# ``docs/INDEX.md`` joins axis (a) with W3-3's ``render_docs_index``, which does
# not exist yet — a stated boundary, not a placeholder.
#
# The second axis is the only thing in the initiative that breaks the closed
# circle ``doc_facts -> renderer -> V6`` (R14). The first compares the render
# output against the very formula that produced it, so a *systematically* wrong
# factor passes every gate — the spec's F19, F22 and F14 are three real
# counting errors no V-check would have found. The oracle is the only right-hand
# side a human maintains and the formula never sees, so an ``expected-mismatch``
# means: *the rendered documentation is self-consistent and the two sources
# disagree* — either the formula is wrong, or the oracle was not carried along
# in the same commit, which is the intended review signal (R14 residual risk)
# and not a defect.

V6_CHECK_ID = "docs.docs_facts_fresh"

#: The documents the generator renders fact blocks into (spec §6 (a)) — the same
#: three entry documents V1 scans, but its own constant so that W3's generator
#: target list and V1's scan list move independently and a test can point one
#: axis at a fixture alone.
V6_SCAN_RELPATHS: tuple[str, ...] = ("README.md", "llms.txt", "ARCHITECTURE.md")

#: Where the facts come from when the caller passes no project config — the
#: canonical single-file loader path, as in ``placeholders.load_project_vars``.
V6_PROJECT_CONFIG_RELPATH = ".meta-config/project.yaml"

V6_KIND_HANDEDIT = "handedit"

#: The **check's** spelling of the comparator's ``mismatch`` (F10): the two
#: vocabularies are deliberately distinct, because the check owns a third axis.
#: The shared spelling is not re-invented here — it is ``doc_facts``' own.
V6_KIND_EXPECTED_MISMATCH = "expected-mismatch"
V6_KIND_MISSING_IN_EXPECTED = MISSING_IN_EXPECTED_KIND

#: The three kinds and how each is reported. Keyed by the ``kind`` constants —
#: never by a copied literal — so the word a finding carries and the severity the
#: runner counts cannot drift apart.
V6_SEVERITY_BY_KIND: dict[str, Severity] = {
    V6_KIND_HANDEDIT: Severity.ERROR,
    V6_KIND_EXPECTED_MISMATCH: Severity.ERROR,
    V6_KIND_MISSING_IN_EXPECTED: Severity.WARNING,
}

#: One remediation per kind, because the three axes are fixed by three different
#: people: the renderer, the formula, and whoever maintains the oracle.
V6_SUGGESTION: dict[str, str] = {
    V6_KIND_HANDEDIT: (
        "Re-render the region (`python3 scripts/sync.py`) or restore the "
        "hand-edited text — a marker region is generated, never maintained."
    ),
    V6_KIND_EXPECTED_MISMATCH: (
        "Fix the formula in `scripts/lib/doc_facts.py`, or — if the computed "
        f"value is the right one — update `{EXPECTED_DOC_FACTS_RELPATH}` and "
        "bump `verified-at` in the same commit (the R14 review signal)."
    ),
    V6_KIND_MISSING_IN_EXPECTED: (
        f"Pin the value in `{EXPECTED_DOC_FACTS_RELPATH}`, or record next to "
        "the other IC-23 exclusions why the fact stays unpinned."
    ),
}


def _v6_project_config(root: Path, config: dict | None) -> dict:
    """The project config the facts are computed from.

    ``config`` is what the runner holds (the IC-05 signature); when it is absent
    the check loads the canonical file itself, because a check that needed a
    config but silently compared against an empty one would report the whole
    repository as drifted.
    """
    if config:
        return config
    data = load_yaml_file(
        Path(root) / V6_PROJECT_CONFIG_RELPATH, on_error="default", default=None
    )
    return data if isinstance(data, dict) else {}


def _v6_computed_facts(root: Path, config: dict | None) -> dict[str, str]:
    """The computed facts, reduced to the ones that carry a value.

    A comparison needs two values. Without a project config no formula can run,
    and with a missing source one cannot — ``doc_facts`` never raises for either
    (IC-01), it yields the empty string. An empty value against a pinned one is
    an absence, not a drift, and reporting it as one is the F21
    permanent-false-alarm class; an empty result means "nothing is comparable",
    which the caller turns into silence, not into eleven mismatches.
    """
    project_config = _v6_project_config(root, config)
    if not project_config:
        return {}
    facts = compute_doc_facts(Path(root), project_config)
    return {name: value for name, value in facts.items() if value}


def _v6_first_difference(actual: str, expected: str) -> tuple[int, str, str]:
    """``(body line, actual line, expected line)`` of the first difference.

    Relative to the region body, which starts *on* the ``docs-begin`` line, so
    the caller adds ``begin_lineno - 1``. ``(0, "", "")`` means only the
    terminator or a trailing blank line differs. A finding that merely says
    "differs" costs the reader a diff run.
    """
    for index, (left, right) in enumerate(
        zip_longest(actual.splitlines(), expected.splitlines(), fillvalue=""),
        start=1,
    ):
        if left != right:
            return index, left, right
    return 0, "", ""


def _v6_rendered_regions(text: str) -> list[tuple[str, str, int]]:
    """``(region, body, begin line)`` per region the renderer *would* write.

    Mirrors the three decision rules of ``doc_renderer.apply_fact_blocks``,
    because a region the renderer never touches cannot be repaired by
    re-rendering: an unpaired ``docs-begin`` leaves the **whole file** alone
    (AC-15), a repeated region name renders only its first pair (AC-16), an
    unknown name is not rendered at all (IC-08).
    """
    balanced = list(DOCS_BLOCK_RE.finditer(text))
    paired = {match.start() for match in balanced}
    if any(match.start() not in paired for match in DOCS_BEGIN_RE.finditer(text)):
        return []
    regions: list[tuple[str, str, int]] = []
    seen: set[str] = set()
    for match in balanced:
        region = match.group("region")
        if region in seen or not is_valid_region(region):
            continue
        seen.add(region)
        regions.append((
            region,
            match.group("body"),
            text.count("\n", 0, match.start()) + 1,
        ))
    return regions


def _v6_finding(kind: str, relpath: str, message: str, *,
                lineno: int | None = None) -> Finding:
    """The house ``Finding`` for *kind*, plus the ``kind`` attribute.

    ``Finding`` (``report.py``) has no ``kind`` and no ``line`` field and that
    module is not owned by W2-5, so both are set on the instance — the same
    two-part contract ``_v1_finding`` uses, and the same W2-7 follow-up.
    ``line`` is set only where the finding points into a document; the oracle
    axis names a key, and a magic ``0`` would print as a location.
    """
    finding = Finding(
        severity=V6_SEVERITY_BY_KIND[kind],
        check=V6_CHECK_ID,
        file=relpath,
        message=message,
        suggestion=V6_SUGGESTION[kind],
    )
    finding.kind = kind
    if lineno is not None:
        finding.line = lineno
    return finding


def _v6_handedit_findings(root: Path, facts: dict[str, str]) -> list[Finding]:
    """Axis (a): the rendered marker regions against the computed facts.

    A region whose fact is not among the computed ones is skipped: the renderer
    would write the ``docs-empty`` placeholder for it, and comparing a real
    region against that placeholder would report a drift no config source can
    fix. On the scalar side the same absence is ``missing-in-expected``; here
    silence is right — a rendered block is not a pinnable number.
    """
    findings: list[Finding] = []
    for relpath in V6_SCAN_RELPATHS:
        path = Path(root) / relpath
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for region, body, begin_lineno in _v6_rendered_regions(text):
            if REGION_FACT_KEYS[region] not in facts:
                continue
            expected = render_doc_fact_block(region, facts)
            if body == expected:
                continue
            index, left, right = _v6_first_difference(body, expected)
            detail = (f"line {index}: {left!r} != {right!r}" if index
                      else "trailing blank line or line terminator")
            findings.append(_v6_finding(
                V6_KIND_HANDEDIT,
                relpath,
                f"line {begin_lineno + index - 1}: marker region {region!r} "
                f"differs from the block the facts render ({detail})",
                lineno=begin_lineno + index - 1,
            ))
    return findings


def _v6_expected_findings(root: Path, facts: dict[str, str]) -> list[Finding]:
    """Axes (b) and (c): the computed facts against the hand-maintained oracle.

    The loader is fail-soft (IC-01): a missing, unreadable or malformed oracle
    yields ``{}``, and "nothing is pinned" is the honest answer — V6 then stays
    silent. The comparator already sorts by ``fact`` and limits itself to the
    pinnable facts, so this only maps its two kinds onto the check's three.
    """
    expected = load_expected_doc_facts(Path(root))
    if not expected:
        return []
    findings: list[Finding] = []
    for entry in compare_expected_doc_facts(facts, expected):
        if entry["kind"] == MISMATCH_KIND:
            kind = V6_KIND_EXPECTED_MISMATCH
            message = (
                f"{entry['fact']}: computed {entry['computed']!r} != oracle "
                f"{entry['expected']!r} — the formula and the human-maintained "
                "value disagree although the rendered documentation matches "
                "the formula"
            )
        else:
            kind = V6_KIND_MISSING_IN_EXPECTED
            message = (
                f"{entry['fact']}: computed {entry['computed']!r} is not "
                "pinned in the oracle"
            )
        findings.append(_v6_finding(kind, EXPECTED_DOC_FACTS_RELPATH, message))
    return findings


def check_docs_facts_fresh(root: Path, config: dict | None = None) -> list[Finding]:
    """V6: the rendered documentation and the computed facts against the oracle.

    ``config`` is the project config (IC-05 signature), loaded from the repo
    when absent. The ``docs-consolidation.enabled`` common gate and the runner
    registration are W2-7's task; until then nothing calls this function and no
    scenario can regress from W2-5 (AC-38). The order is fixed — expected-value
    axis first in the comparator's ``fact`` order, then the handedit axis in scan
    order.
    """
    facts = _v6_computed_facts(root, config)
    if not facts:
        return []
    return _v6_expected_findings(root, facts) + _v6_handedit_findings(root, facts)
