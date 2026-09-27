"""Reference-resolution checks — is every claim in the docs resolvable?

Family of the file-check cut of Spec §4.1 (U-1, decision U-1 / K18): this
module owns exactly one question — *"Is every reference resolvable?"* — and
therefore exactly the checks that resolve a *target* a document names:

* **V3** ``check_internal_links`` (AC-09, IC-05, R6) — W2-2.
* **V4** ``check_readme_docs_index`` — the documentation index of the entry
  documents.
* the two pre-W2 alt checks ``check_sync_cli_docs`` and
  ``check_ui_help_mappings``, whose signature and severity IC-05 pins.

The V4/alt-check overlap is intentional and is how Spec §4.1 records it: V4 *is*
``check_readme_docs_index``, and IC-05 additionally pins the pre-existing trio
in ``docs_links``. No check of any other module resolves a target, so none is
shared with ``docs_freshness``.

``docs.py`` stays the facade the runner and the test suite import (K19); this
module is reached through it. Nothing here is stdlib-external.
"""

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
