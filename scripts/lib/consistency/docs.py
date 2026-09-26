"""Documentation and UI cross-reference consistency checks."""

from __future__ import annotations

import re
from pathlib import Path

from .report import Finding, Severity


def check_sync_cli_docs(root: Path) -> list[Finding]:
    """Check that all argparse arguments in sync.py are documented in cli-reference.md."""
    findings = []
    sync_py = root / "scripts" / "sync.py"
    cli_ref = root / "docs" / "api" / "cli-reference.md"
    
    if not sync_py.exists() or not cli_ref.exists():
        return findings

    # Extract flags from sync.py
    flags = set()
    sync_content = sync_py.read_text(encoding="utf-8")
    for line in sync_content.splitlines():
        if "parser.add_argument(" in line:
            # Match flags like '"--config"' or "'--init'"
            matches = re.findall(r'["\'](--[a-zA-Z0-9-]+)["\']', line)
            flags.update(matches)
            
    # Extract documented flags from cli-reference.md
    ref_content = cli_ref.read_text(encoding="utf-8")
    doc_flags = set()
    for line in ref_content.splitlines():
        matches = re.findall(r'`(--[a-zA-Z0-9-]+)[^`]*`', line)
        doc_flags.update(matches)
        
    for flag in flags:
        if flag not in doc_flags and flag not in ("--help",):
            findings.append(Finding(
                severity=Severity.ERROR,
                check="docs.cli_reference",
                file="docs/api/cli-reference.md",
                message=f"CLI argument '{flag}' is not documented in cli-reference.md",
                suggestion=f"Add an entry for `{flag}` in the appropriate table."
            ))
            
    return findings


def check_ui_help_mappings(root: Path) -> list[Finding]:
    """Check that all routes in admin-ui.html routeMap have a valid help-id in admin-ui-reference.md."""
    findings = []
    admin_ui = root / "docs" / "ui" / "admin-ui.html"
    help_ref = root / "docs" / "api" / "admin-ui-reference.md"
    
    if not admin_ui.exists() or not help_ref.exists():
        return findings
        
    ui_content = admin_ui.read_text(encoding="utf-8")
    ref_content = help_ref.read_text(encoding="utf-8")
    
    # Parse routeMap from admin-ui.html
    route_map_block = re.search(r'const routeMap = \{([^}]+)\};', ui_content)
    if not route_map_block:
        findings.append(Finding(
            severity=Severity.ERROR,
            check="docs.ui_help_mappings",
            file="docs/ui/admin-ui.html",
            message="Could not parse 'routeMap' from admin-ui.html",
            suggestion="Ensure routeMap is a valid JS object literal."
        ))
        return findings
        
    # Extract help IDs expected by UI
    expected_help_ids = set()
    for line in route_map_block.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("//"): continue
        match = re.search(r'["\']([^"\']+)["\']\s*:\s*["\']([^"\']+)["\']', line)
        if match:
            expected_help_ids.add(match.group(2))
            
    # Extract available help IDs from Markdown
    available_help_ids = set()
    for line in ref_content.splitlines():
        if line.startswith("<!-- help-id: "):
            help_id = line.replace("<!-- help-id: ", "").replace(" -->", "").strip()
            available_help_ids.add(help_id)
            
    for help_id in expected_help_ids:
        if help_id not in available_help_ids:
            findings.append(Finding(
                severity=Severity.ERROR,
                check="docs.ui_help_mappings",
                file="docs/api/admin-ui-reference.md",
                message=f"UI route expects help-id '{help_id}', but it is missing in the documentation.",
                suggestion=f"Add `<!-- help-id: {help_id} -->` to admin-ui-reference.md."
            ))
            
    return findings


def check_readme_docs_index(root: Path) -> list[Finding]:
    """Check that all markdown files in docs/api/ are linked in README.md."""
    findings = []
    readme = root / "README.md"
    docs_api_dir = root / "docs" / "api"
    
    if not readme.exists() or not docs_api_dir.exists():
        return findings
        
    readme_content = readme.read_text(encoding="utf-8")
    
    for md_file in docs_api_dir.glob("*.md"):
        rel_path = f"docs/api/{md_file.name}"
        if rel_path not in readme_content:
            findings.append(Finding(
                severity=Severity.ERROR,
                check="docs.readme_index",
                file="README.md",
                message=f"File '{rel_path}' is not linked in README.md",
                suggestion=f"Add a link to `[{md_file.stem}]({rel_path})` in the Documentation Index section."
            ))
            
    return findings


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
    Rule 3 — the line is inside a Markdown fenced code block (```` ``` ```` or
    ``~~~``); the fence delimiters themselves carry no number.
    """
    suppressed: set[int] = set()
    in_region = False
    fence: str | None = None
    for lineno, line in enumerate(text.splitlines(), start=1):
        if fence is not None:
            closing = re.fullmatch(rf" {{0,3}}{re.escape(fence[0])}{{{len(fence)},}}\s*", line)
            if closing is None:
                suppressed.add(lineno)
                continue
            fence = None
            continue
        opening = _V1_FENCE_OPEN_RE.match(line)
        if opening is not None:
            fence = opening.group(1)
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
