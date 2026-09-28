"""Reference-resolution checks — is every claim in the docs resolvable?

Family of the file-check cut of Spec §4.1 (U-1, decision U-1 / K18): this module
owns exactly one question — *"Is every reference resolvable?"* — and therefore
exactly the checks that resolve a *target* a document names:

* **V3** ``check_internal_links`` (AC-09, IC-05, R6) — W2-2.
* **V4** ``check_readme_docs_index`` — the documentation index of the entry
  documents. Since W2-6 (**E-5**) it asks whether every **declared**
  ``docs/<category>/`` directory of README's ``Documentation Index`` section is
  **real** and **represented by a link**; it no longer asks whether every page below
  ``docs/`` is linked. Signature ``(root)``, check id and severity stay IC-05-pinned.
* the two pre-W2 alt checks ``check_sync_cli_docs`` and
  ``check_ui_help_mappings``, whose signature and severity IC-05 pins.

The V4/alt-check overlap is intentional and is how Spec §4.1 records it: V4 *is*
``check_readme_docs_index``, and IC-05 additionally pins the pre-existing trio. Of the
three, V4 is the only one that does **not** resolve a target — since **E-5** it compares
declared categories against the filesystem, so a dead link in the index region is a
**V3** finding, never a V4 one. No check of any other module resolves a target, so none
is shared with ``docs_freshness``.

``docs.py`` stays the facade the runner and the test suite import (K19). Stdlib-only.
"""

from __future__ import annotations

import re
from bisect import bisect_right
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


def _v4_index_region(text: str) -> str | None:
    """The README's Documentation Index section, or ``None`` when there is none.

    **E-5, extraction scope.** From the ``##`` heading whose text contains
    ``Documentation Index`` up to — not including — the next ``##`` heading; a ``###``
    heading is a *subsection* and does not close the region, which is why a section may
    declare its categories in ``###`` subheadings. ``None`` differs from ``""`` and the
    caller depends on it: ``None`` is *no index section at all*, fail-closed; ``""``
    declares nothing and is vacuously satisfied.
    """
    lines = text.splitlines()
    headings = [i for i, line in enumerate(lines) if line.startswith("## ")]
    start = next((i for i in headings if V4_INDEX_HEADING in lines[i]), None)
    if start is None:
        return None
    after = [i for i in headings if i > start]
    return "\n".join(lines[start:after[0] if after else len(lines)])


def _v4_token_starts(text: str) -> list[int]:
    """Every token start in ``text``: ``0`` plus one entry per boundary hit.

    **F-1 — why this exists.** The remote test needs the start of the token a match sits
    in, and finding it with one backward scan per boundary character per match was
    **O(n·m)**: nine scans per match, eight typically running to position 0. Measured on
    a generated index region — 116 ms at 263 KB, 488 ms at 533 KB, 2 106 ms at 1,08 MB —
    quadratic, on a check that runs on *every* ``consistency-check.py`` invocation once
    W3-6 generates ``docs/INDEX.md``. One linear pass plus a ``bisect`` per match is
    O(n + m log n): 13,3 / 28,0 / 60,8 ms on the same sizes — linear, not quadratic.
    """
    return [0, *(match.end() for match in V4_BOUNDARY_RE.finditer(text))]


def _v4_is_remote_path(text: str, start: int, token_starts: list[int]) -> bool:
    """Whether the match at ``start`` sits in a remote reference, not a local path.

    **D2 + F-3.** A bare ``docs/…`` scan has no left boundary, so
    ``https://x.invalid/docs/spam/a.md`` would *declare* a category ``spam`` that exists
    in no checkout — a false ERROR on a category never claimed. What makes a mention
    remote is a **grammar**, not an allowlist of schemes, mirroring how V3 classifies
    inertness with :data:`V3_SCHEME_RE`: a URI scheme (``https:``, ``mailto:``,
    ``ftp:``), a **protocol-relative** ``//``, or a **host** marker ``www.`` — each
    anchored at the token start with no whitespace in between. That covers the forms D2
    missed (``//cdn.invalid/…``, ``www.example.com/…``, ``mailto:docs/spam/a``) with no
    second list to maintain.

    Narrow on purpose, because the counter-requirement is real — the six heading
    categories of the real README are declared by **code spans** (`` `docs/guides/` ``),
    and a blunt "not preceded by ``/`` or ``:``" rule would break the pinned 7; a
    backtick, bracket, paren and whitespace each open a fresh token, so a code span is
    unaffected. One consequence is accepted, not tuned around: ``siehe
    auch:docs/guides/`` reads as a scheme and is dropped, as V3 would treat it.
    """
    left = token_starts[bisect_right(token_starts, start) - 1]
    return V4_REMOTE_PREFIX_RE.search(text, left, start) is not None


def _v4_categories_in(text: str) -> list[str]:
    """The declared categories of one text, in first-mention order.

    The shared inner loop of both readings below: scan, drop remote references, keep
    first mention only — a ``set`` would make report order depend on ``PYTHONHASHSEED``.
    """
    categories: list[str] = []
    token_starts = _v4_token_starts(text)
    for match in V4_CATEGORY_RE.finditer(text):
        if _v4_is_remote_path(text, match.start(), token_starts):
            continue
        name = match.group("category")
        if name not in categories:
            categories.append(name)
    return categories


def _v4_declared_categories(region: str) -> list[str]:
    """The ``docs/`` categories the index region names, in first-mention order.

    **E-5, extraction rule, verbatim from the plan (K64):** *every*
    ``docs/<category>/`` path named anywhere in the region is a declared category, not
    only those in a ``###`` heading. Load-bearing, not cosmetic: a heading-only reading
    yields **6** on the real README, because ``docs/architecture/`` is named
    *exclusively* inside the link ``docs/architecture/01-layer-model.md`` and in no
    ``###`` heading; the full reading yields **7**, and the plan pins **7**. Both give
    the same expected finding count today, which is why the count is no argument — the
    *rule* is pinned, against :func:`_v4_declared_heading_categories`.
    """
    return _v4_categories_in(region)


def _v4_declared_heading_categories(region: str) -> list[str]:
    """The ``docs/`` categories named in a heading of the region — the 6/7 foil.

    Exists solely to make the E-5 rule observable: the real README declares
    ``docs/architecture/`` **only** through a link, so this returns it not at all while
    :func:`_v4_declared_categories` does — and a test pinning both separates the rule
    from an accidental heading-glob. The same remote filter applies, so the two readings
    differ by *heading*, never by disagreeing about what a mention is. That is a claim,
    not a hope: ``test_v4_url_in_a_heading_is_filtered_in_both_readings`` removes this
    call as a mutant, and before it existed the call was untested.
    """
    categories: list[str] = []
    for line in region.splitlines():
        if not line.startswith("#"):
            continue
        for name in _v4_categories_in(line):
            if name not in categories:
                categories.append(name)
    return categories


def _v4_category_of_target(target: str) -> str | None:
    """The category a Markdown link target points into, or ``None``.

    **D1.** ``[ov]: docs/guides/x.md`` is a link, and the plan's acceptance (b) says
    "at least one link" without binding the form, so reference definitions count
    alongside ``](…)``. Angle brackets, fragments and queries go first, so
    ``](<docs/guides/x.md>)`` and ``](docs/guides/x.md#top)`` are the bare spelling too.
    Whether a target may *represent* a category is the caller's call — see
    :func:`_v4_is_image_target` for the D3 rule.
    """
    target = target.strip("<>").split("#", 1)[0].split("?", 1)[0]
    match = V4_CATEGORY_LINK_RE.match(target)
    return match.group("category") if match is not None else None


def _v4_is_image_target(region: str, start: int) -> bool:
    """Whether the inline link at ``start`` is an **embedded image**, not an entry.

    **D3.** ``![chart](docs/guides/chart.png)`` is a figure inside a list item, not an
    index entry, and must not satisfy condition (b) alone. The test is **structural**:
    a ``![`` that opens this link text, no ``]`` between it and this ``](`` — because
    an extension test was measured and **rejected**: ``docs/ui/`` is represented in the
    real README by ``](docs/ui/agent-graph.html)`` and ``](docs/ui/admin-ui.html)``,
    so an ``.md``-only rule reports a category the README genuinely links and moves the
    value from **1** to **2**. The plan's acceptance (b) says "at least one *link*" and
    binds no suffix, so the structural rule is the literal reading. **Known gap, stated
    not hidden:** ``![alt][ref]`` is not detected — its ``[ref]: target`` line carries
    no ``!`` — so such a target still counts; fixing it needs label tracking and belongs
    to the follow-up in the W2-6 plan note (V4 out of ``docs_links.py``, Spec §4.1).
    """
    head = region.rfind("![", 0, start)
    return head != -1 and "]" not in region[head + 2:start]


def _v4_linked_categories(region: str) -> set[str]:
    """The categories the region **links into** — the representation axis.

    A bare ``docs/<category>/`` mention in a heading or prose does **not** count; a link
    does, an embedded **image** (``![…](…)``) does not. That is the gap between the two
    acceptance conditions: a category may be *declared* by naming its directory yet
    stay *unrepresented* if the section links no page of it — the real tree's
    ``docs/se-cascade/``. Both Markdown link forms count, inline ``](target)`` and
    reference definitions ``[label]: target``; D1 found a false ERROR when a category
    was linked *only* the second way.
    """
    linked: set[str] = set()
    for match in V4_LINK_TARGET_RE.finditer(region):
        if _v4_is_image_target(region, match.start()):
            continue
        category = _v4_category_of_target(match.group("target"))
        if category is not None:
            linked.add(category)
    for match in V4_REFERENCE_DEF_RE.finditer(region):
        category = _v4_category_of_target(match.group("target"))
        if category is not None:
            linked.add(category)
    return linked


def _v4_finding(message: str, suggestion: str) -> Finding:
    """A V4 finding — the IC-05-pinned triple, in one place so neither drifts."""
    return Finding(severity=Severity.ERROR, check=V4_CHECK_ID,
                   file=V4_README_RELPATH, message=message, suggestion=suggestion)


def _v4_region_finding() -> Finding:
    """The single fail-closed finding for a ``docs/`` tree with no index section."""
    return _v4_finding(
        f"{V4_README_RELPATH} declares no '{V4_INDEX_HEADING}' section, so no "
        f"{V4_DOCS_RELDIR}/ category is represented there", V4_REGION_SUGGESTION)


def _v4_category_finding(relpath: str, reasons: tuple[str, ...]) -> Finding:
    """One finding for one declared-but-unrepresented category.

    Exactly **one** per category even when both conditions fail, joined by ``and`` — a
    category that is neither real nor linked is one unrepresented category, not two.
    """
    return _v4_finding(
        f"documentation category '{relpath}' is declared in the "
        f"{V4_README_RELPATH} {V4_INDEX_HEADING} section but {' and '.join(reasons)}",
        f"Link a page of `{relpath}` in the {V4_INDEX_HEADING} section, and create "
        f"the directory if the category is not meant to exist.")


def check_readme_docs_index(root: Path) -> list[Finding]:
    """V4 (**E-5**): is every category the README's Documentation Index declares real,
    and linked?

    **What V4 checks (K54).** From the ``##`` region of ``README.md`` whose heading
    names the ``Documentation Index``, take per the verbatim rule (K64) *every*
    ``docs/<category>/`` path named there. Each declared category must satisfy **two**
    conditions — (a) the directory ``docs/<category>/`` exists, (b) the region carries
    at least one ``docs/<category>/…`` **link** (inline or reference definition, never
    an embedded image). Failing either is **exactly one** ERROR: the report is about
    the **representation of a category**, never a single page.

    **What V4 no longer checks.** Every non-archived ``docs/**/*.md`` linked from the
    README — the per-page reading E-5 replaces, which produced **191/193** ERRORs here
    against a hand-maintained README that links a curated subset by design. Per-page
    completeness is **V2's** question and target: ``docs/INDEX.md``, 100 % generated,
    tracked per OQ6. Stated rather than hidden: with this scope V4 has **no** 0-target
    in W0–W8; the ``W-VALIDATE-ROT`` delta clause governs it.

    **IC-05 pin, unchanged.** Signature ``(root)`` — one argument, no ``config``;
    ``(root, config=None)`` belongs to the **nine new** V-checks. Check id
    ``docs.readme_index``, severity **ERROR**, ``file`` ``README.md``. Only the
    **scope** moved.

    **Precedence — fail-soft before fail-closed (K65),** replacing the single condition
    that used to treat a missing README and a missing ``docs/`` tree alike:

    1. **No ``docs/`` tree ⇒ ``[]`` (fail-soft), first and unconditional.** No ``docs/``
       means no region and no declared category, so "missing category" would be a
       question without an object.
    2. **``docs/`` present ⇒ fail-closed.** A ``README.md`` that cannot be read —
       **missing**, **not a file**, or **not decodable as UTF-8** — or a missing
       ``Documentation Index`` heading is **exactly one** finding, never an empty list:
       a README that cannot declare its categories is a defect, and tolerating it would
       make the check vacuous exactly when the index is absent. Those three are the read
       failures :data:`V4_READ_ERRORS` names — ``UnicodeDecodeError`` derives from
       :class:`ValueError`, not :class:`OSError`, which is why naming both is what makes
       "unreadable" true here (D4). Anything else still propagates.
    """
    docs_dir = root / V4_DOCS_RELDIR
    if not docs_dir.is_dir():
        return []

    try:
        readme_text = (root / V4_README_RELPATH).read_text(encoding="utf-8")
    except V4_READ_ERRORS:
        return [_v4_region_finding()]

    region = _v4_index_region(readme_text)
    if region is None:
        return [_v4_region_finding()]

    linked = _v4_linked_categories(region)
    findings: list[Finding] = []
    for name in _v4_declared_categories(region):
        reasons = []
        if not (docs_dir / name).is_dir():
            reasons.append("the directory does not exist")
        if name not in linked:
            reasons.append("the section links no page below it")
        if reasons:
            findings.append(_v4_category_finding(
                f"{V4_DOCS_RELDIR}/{name}/", tuple(reasons)))
    return findings


# ---------------------------------------------------------------------------
# V3 — check_internal_links (AC-09, IC-05, R6; spec §5.1.1, plan W2-2)
# ---------------------------------------------------------------------------


V3_CHECK_ID = "docs.internal_links"

V3_SUGGESTION = "Point the reference at a path that exists, or drop it."

#: Entry documents (also the only place a layout block is read, see below).
V3_ENTRY_RELPATHS: tuple[str, ...] = ("README.md", "llms.txt")
V3_DOCS_RELDIR = "docs"
V3_DOC_SUFFIXES: tuple[str, ...] = (".md", ".markdown", ".txt")

#: R6 — a URI scheme (RFC 3986 §3.1) makes a target external. Deliberately a
#: *grammar*, not an allowlist: ``sms:``, ``callto:``, ``magnet:``,
#: ``git+https:``, ``obsidian:`` and every other scheme must stay inert, or V3
#: turns a legitimate external reference into an ERROR (W2-2, review F2).
V3_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")

#: Site-root-absolute targets are not repository-internal either. The former
#: ``"//"`` entry is gone (F3): it never fired, ``"/"`` already covered it.
V3_INERT_PREFIXES = ("/",)

V3_INERT_CHARS = ("<", ">", "{", "}", "*", " ", "\\")


V3_INLINE_LINK_RE = re.compile(r"\]\(\s*(?P<target>[^()\s]+)(?:\s+[^()]*)?\)")

V3_REFERENCE_DEF_RE = re.compile(
    r"^[ ]{0,3}\[[^\]]+\]:[ \t]*(?P<target>\S+)(?:[ \t]+[\"'][^\"']*[\"'])?[ \t]*$")
V3_HTML_HREF_RE = re.compile(
    r"<a\b[^>]*\bhref=[\"'](?P<target>[^\"']+)[\"']", re.IGNORECASE)
V3_FENCE_OPEN_RE = re.compile(r"^[ ]{0,3}(?P<fence>`{3,}|~{3,})")
V3_CODE_SPAN_RE = re.compile(r"(?P<ticks>`+)(?:(?!(?P=ticks)).)*(?P=ticks)")
V3_LAYOUT_ENTRY_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<name>[A-Za-z0-9._@+-]+/)[ \t]*(?:#.*)?$")


# --- V4 (E-5) --- same facade as V3, different question (Spec §4.1), no check shared.
V4_CHECK_ID = "docs.readme_index"
V4_README_RELPATH = "README.md"
V4_DOCS_RELDIR = "docs"
V4_INDEX_HEADING = "Documentation Index"
V4_READ_ERRORS = (OSError, UnicodeDecodeError)
V4_CATEGORY_RE = re.compile(r"docs/(?P<category>[^/\s()\[\]`*]+)/")
V4_CATEGORY_LINK_RE = re.compile(V4_CATEGORY_RE.pattern + r"[^\s()\[\]<>]+")
V4_BOUNDARY_RE = re.compile(r"[ \t\n(\[]|`")
V4_REMOTE_PREFIX_RE = re.compile(r"(?:\A|[A-Za-z][A-Za-z0-9+.\-]*:|//|www\.)\S*$")

# **F-4: aliases, not copies.** Both grammars are character-identical to V3's, so one
# definition each has to be edited; V4 needs ``MULTILINE`` because it scans a region.
V4_LINK_TARGET_RE = V3_INLINE_LINK_RE
V4_REFERENCE_DEF_RE = re.compile(V3_REFERENCE_DEF_RE.pattern, re.MULTILINE)

V4_REGION_SUGGESTION = (
    f"Add a `## {V4_INDEX_HEADING}` section to {V4_README_RELPATH} that names "
    f"each {V4_DOCS_RELDIR}/ category and links at least one page of it."
)


def _v3_finding(severity: Severity, relpath: str, lineno: int, branch: str,
                message: str) -> Finding:
    """Build a V3 ``Finding`` — the two instance attributes, exactly as V1 does.
    ``Finding`` (``report.py``) has neither field and is not owned by W2-2, so
    both are set on the instance; W2-7 owns the runner and should promote them.
    """
    finding = Finding(
        severity=severity, check=V3_CHECK_ID, file=relpath, message=message,
        suggestion=V3_SUGGESTION,
    )
    finding.line = lineno
    finding.branch = branch
    return finding


def _v3_scan_relpaths(root: Path) -> list[str]:
    """Every document V3 reads: entry documents plus ``docs/**`` (IC-05)."""
    relpaths = [rel for rel in V3_ENTRY_RELPATHS if (root / rel).is_file()]
    docs_dir = root / V3_DOCS_RELDIR
    if docs_dir.is_dir():
        relpaths += [p.relative_to(root).as_posix() for p in docs_dir.rglob("*")
                     if p.is_file() and p.suffix in V3_DOC_SUFFIXES]
    return sorted(set(relpaths))


def _v3_scanned_lines(text: str) -> list[tuple[int, str, int | None]]:
    """``(lineno, line, block)`` per line; ``block`` is its fence and ``None``
    in prose — the split the two extractors need."""
    scanned: list[tuple[int, str, int | None]] = []
    fence: str | None = None
    block = 0
    for lineno, line in enumerate(text.splitlines(), start=1):
        opening = V3_FENCE_OPEN_RE.match(line)
        if fence is not None:
            if (opening is not None
                    and opening.group("fence")[0] == fence[0]
                    and len(opening.group("fence")) >= len(fence)
                    and not line[opening.end():].strip()):
                fence = None
            scanned.append((lineno, line, block))
            continue
        if opening is not None:
            fence, block = opening.group("fence"), block + 1
            scanned.append((lineno, line, block))
            continue
        scanned.append((lineno, line, None))
    return scanned


def _v3_link_targets(line: str) -> list[str]:
    """Link targets of a prose line: inline links, reference defs, ``href``."""
    targets = [m.group("target") for m in V3_INLINE_LINK_RE.finditer(line)]
    targets += [m.group("target") for m in V3_HTML_HREF_RE.finditer(line)]
    reference = V3_REFERENCE_DEF_RE.match(line)
    return targets + ([reference.group("target")] if reference else [])


def _v3_resolve(root: Path, doc: Path, target: str) -> Path | None:
    """The repository-internal path a target claims, else ``None``.

    R6: a URI scheme, a site-root-absolute or anchor-only target, a placeholder
    and a target that climbs out of the repository are never resolved —
    ``page.md#section`` drops its anchor, which is not checked.
    """
    if not target or V3_SCHEME_RE.match(target):
        return None
    base = target.split("#", 1)[0].split("?", 1)[0]
    if (not base or base.startswith(V3_INERT_PREFIXES)
            or any(char in target for char in V3_INERT_CHARS)):
        return None
    resolved = (doc.parent / base).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None
    return resolved


def _v3_layout_entries(scanned: list[tuple[int, str, int | None]]) -> list[tuple[int, str]]:
    """Directory entries of layout blocks, composed by indentation.

    Only a line whose entire content is ``name/`` plus an optional ``#``
    comment counts, which keeps prose out. A deeper entry composes onto the
    closest shallower one — ``howto/`` then ``setup/`` claims ``howto/setup/``
    — and the stack resets per fence.
    """
    entries: list[tuple[int, str]] = []
    stack: list[tuple[int, str]] = []
    current: int | None = None
    for lineno, line, block in scanned:
        match = V3_LAYOUT_ENTRY_RE.match(line) if block is not None else None
        if match is None:
            if block != current:
                stack.clear()
                current = block
            continue
        indent = len(match.group("indent").expandtabs(4))
        while stack and stack[-1][0] >= indent:
            stack.pop()
        name = match.group("name")
        composed = (stack[-1][1] if stack else "") + name
        stack.append((indent, composed))
        current = block
        entries.append((lineno, composed))
    return entries


def check_internal_links(root: Path, config: dict | None = None) -> list[Finding]:
    """V3: documented relative repository paths that do not exist (AC-09, R6).

    Two claim forms, both needed for AC-09: a Markdown or HTML link target in
    the prose of any in-scope file (branch ``"link"``) and a directory entry of
    a documented layout block (branch ``"layout"``). ``README.md`` claims
    ``howto/setup/`` and ``howto/features/`` at ``:721-723``; neither exists.

    The layout form is read **only** in the entry documents, which carry the
    repository map. Inside ``docs/**`` such an entry illustrates a *consumer*
    project (``Zielprojekt/``, ``agent-meta/`` as a submodule checkout) and is
    not distinguishable from a claim about this repository, so it is
    deliberately not checked.

    ``config`` is accepted for the runner's uniform call signature; V3 reads no
    key and has one severity (ERROR, IC-05). Gate and registration are W2-7's.
    """
    findings: list[Finding] = []
    for relpath in _v3_scan_relpaths(root):
        path = root / relpath
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        scanned = _v3_scanned_lines(text)
        for lineno, line, block in scanned:
            if block is not None:
                continue
            prose = V3_CODE_SPAN_RE.sub(lambda m: " " * len(m.group(0)), line)
            for target in _v3_link_targets(prose):
                resolved = _v3_resolve(root, path, target)
                if resolved is None or resolved.exists():
                    continue
                findings.append(_v3_finding(
                    Severity.ERROR, relpath, lineno, "link",
                    f"line {lineno}: link target {target!r} does not exist"))
        if relpath not in V3_ENTRY_RELPATHS:
            continue
        for lineno, composed in _v3_layout_entries(scanned):
            if (root / composed).exists():
                continue
            findings.append(_v3_finding(
                Severity.ERROR, relpath, lineno, "layout",
                f"line {lineno}: directory {composed!r} does not exist"))
    return findings
