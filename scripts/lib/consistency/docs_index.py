"""Documentation-build checks — is the documentation structure complete and curated?

Family of the file-check cut of Spec §4.1 (U-1, decision U-1 / K18): the cut
follows **the question a check asks**, not file size and not the wave a check
belongs to. This module owns exactly one question — *"Is the documentation
structure complete and curated?"* — and therefore exactly the checks that
compare the **set of documentation pages** against the **index that is supposed
to carry them**:

* **V2** ``check_docs_index_completeness`` (AC-12, IC-05) — implemented here
  (W2-6).
* **V9** ``check_stale_backups`` (IC-05) — W8-4, assigned here by Spec §4.1
  because a stale backup is likewise an artefact of the documentation build
  rather than of a link or of a computed fact.

No check of any other module answers that question, so none is shared with
``docs_links`` (is a reference resolvable?), ``docs_freshness`` (does the prose
match the computed state?) or ``docs_wiki`` (does the derived knowledge surface
match its sources?). The 600-line ceiling is a consequence of the cut, not its
purpose (K18).

**V2 is scheduled red until W3-6.** ``docs/INDEX.md`` is a specified contract
(``spec_plan_scaffold.py:26``, ``fallback-index``) that does not exist yet, so
every page is unindexed and V2 reports all of them. That is a term with an
owner, not a defect of the check (Spec §10, point 5); the **end-to-end** proof
against the real, generated ``docs/INDEX.md`` is W3-6's, and this file therefore
tests the rule on fixtures rather than on a count that W3-6 will change.

**"Tracked" is read as "present in the tree".** IC-05 bounds V2 to *getrackte*
``docs/**/*.md``. This check does not shell out to git: the runner is
stdlib-only and must behave identically in a fixture directory that is not a
repository, so a page is in scope when it exists under ``docs/``. Every page a
checkout would track exists on disk, and a page on disk that the index does not
mention is exactly the drift V2 exists to report.

**In-scope is a positive and a negative boundary, and both halves matter.**
Positive: a Markdown file below ``docs/``. Negative: ``docs/INDEX.md`` itself
(it is the target, and a generated file cannot list its own path before it
exists) and everything below an ``archive/`` or ``_archive/`` directory (IC-05
excludes retired documents by name). Both exclusions are load-bearing: without
the first the check is unsatisfiable by construction, without the second it
fires on pages the project has deliberately retired.

``docs.py`` stays the facade the runner and the test suite import (K19). This
module is reached through it, and the re-export of
``check_docs_index_completeness`` into that ``__all__`` is **W2-7's** write-set
alone (K20/K46) — W2-6 does not touch it. Nothing here is stdlib-external.
"""

from __future__ import annotations

import re
from pathlib import Path

from .report import Finding, Severity

V2_CHECK_ID = "docs.docs_index_completeness"

V2_DOCS_RELDIR = "docs"

V2_INDEX_RELPATH = "docs/INDEX.md"

V2_PAGE_SUFFIX = ".md"

V2_ARCHIVE_DIRNAMES = frozenset({"archive", "_archive"})

V2_SUGGESTION = (
    f"Re-run the sync with `docs-consolidation.enabled: true` — {V2_INDEX_RELPATH} "
    f"is generated, so a page belongs in it only through the generator."
)


_V2_LINK_TARGET_RE = re.compile(r"\]\(\s*(?P<target>[^()\s]+)(?:\s+[^()]*)?\)")

_V2_PATH_TOKEN_RE = re.compile(r"[\w./-]+")

V2_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")


def _v2_is_archived(relpath: str) -> bool:
    """Whether ``relpath`` names a page below a retired-document directory.

    IC-05 excludes ``archive/`` and ``_archive/``; the repository contains both
    spellings (``docs/concepts/archive/``, ``docs/plans/archive/``), so matching
    one of them alone would look correct on either tree but not on both.
    """
    parts = relpath.split("/")
    return any(part in V2_ARCHIVE_DIRNAMES for part in parts[1:-1])


def _v2_in_scope(relpath: str) -> bool:
    """Whether ``relpath`` is a page the index is responsible for.

    The path is project-root relative. The index itself is excluded, everything
    archived is excluded, and only Markdown counts — IC-05 bounds V2 to
    ``docs/**/*.md``, so a ``project.yaml.example`` is not a page.
    """
    if relpath == V2_INDEX_RELPATH:
        return False
    if not relpath.startswith(f"{V2_DOCS_RELDIR}/"):
        return False
    if not relpath.endswith(V2_PAGE_SUFFIX):
        return False
    return not _v2_is_archived(relpath)


def _v2_page_relpaths(root: Path) -> list[str]:
    """Every in-scope documentation page, sorted.

    Sorted so the report is a diff against a stable order rather than a stream
    whose sequence depends on the filesystem.
    """
    docs_dir = root / V2_DOCS_RELDIR
    if not docs_dir.is_dir():
        return []
    relpaths = {
        path.relative_to(root).as_posix()
        for path in docs_dir.rglob(f"*{V2_PAGE_SUFFIX}")
        if path.is_file()
    }
    return sorted(relpath for relpath in relpaths if _v2_in_scope(relpath))


def _v2_mentioned_relpaths(text: str) -> set[str]:
    """The in-scope page paths the index names, normalised to project-root form.

    IC-10 makes the index **100 % generated** and canonicalises it as
    ``- [Title](<path relative to docs/>)`` — ``- [Layer Model]
    (architecture/01-layer-model.md)``. The link target is therefore
    ``docs/``-**relative** and a bare path token in prose is usually
    project-root-relative, so both spellings occur. Both are accepted and
    normalised to the project-root form, which is what :func:`_v2_page_relpaths`
    produces; a page counts as indexed if *either* spelling is present.

    Requiring ``docs/`` on the normalised result is what keeps ordinary prose
    from being read as a path, and dropping any ``#anchor`` suffix is what lets
    a link to a section of a page still count as a link to the page.
    """
    mentioned: set[str] = set()
    for match in _V2_LINK_TARGET_RE.finditer(text):
        target = match.group("target").split("#", 1)[0].strip()
        if not target or target.startswith("/") or V2_SCHEME_RE.match(target):
            continue
        mentioned.add(_v2_normalise(target))
    mentioned.update(
        _v2_normalise(token)
        for token in _V2_PATH_TOKEN_RE.findall(text)
        if token.startswith(f"{V2_DOCS_RELDIR}/")
    )
    return {relpath for relpath in mentioned if relpath.startswith(f"{V2_DOCS_RELDIR}/")}


def _v2_normalise(target: str) -> str:
    """A link target as a project-root-relative path.

    A target already rooted at ``docs/`` is returned unchanged; a ``docs/``-
    relative one — the IC-10 canonical form — gains the prefix. Anything else is
    returned unchanged and filtered out by the caller.
    """
    if target.startswith(f"{V2_DOCS_RELDIR}/"):
        return target
    return f"{V2_DOCS_RELDIR}/{target}"


def _v2_indexed_relpaths(root: Path) -> set[str]:
    """The page paths the index names; empty when the index is absent or unreadable.

    An absent index yields the empty set, which makes every page unindexed.
    That is deliberate rather than fail-soft: a missing index is precisely the
    drift V2 reports, and tolerating it here would make the check vacuous
    exactly when the drift is largest.
    """
    try:
        text = (root / V2_INDEX_RELPATH).read_text(encoding="utf-8")
    except OSError:
        return set()
    return _v2_mentioned_relpaths(text)


def check_docs_index_completeness(root: Path, config: dict | None = None) -> list[Finding]:
    """V2: a documentation page the generated index does not carry (AC-12, IC-05).

    One form, and the one IC-05 names: a ``docs/**/*.md`` outside
    ``archive/``/``_archive/`` and other than ``docs/INDEX.md`` itself whose path
    is absent from ``docs/INDEX.md``. The severity is **ERROR** — IC-05 fixes it,
    and unlike V1 it does not follow ``docs-consolidation.checks.strict``, so
    there is no severity key to read.

    ``config`` is accepted for the runner's uniform call signature and is not
    read. The common gate ``docs-consolidation.enabled`` and the registration in
    ``run_checks()`` are W2-7's, which is why V2 can be scheduled red without
    being able to fail a build: nothing calls it yet.

    V2 is **scheduled red** until W3-6 creates the generated index, so the
    finding count currently tracks the number of pages rather than the number of
    defects. Pinning that number would mean editing this check's test in the
    very task that resolves it, so the rule is what the tests pin.
    """
    findings: list[Finding] = []
    indexed = _v2_indexed_relpaths(root)
    for relpath in _v2_page_relpaths(root):
        if relpath in indexed:
            continue
        findings.append(Finding(
            severity=Severity.ERROR,
            check=V2_CHECK_ID,
            file=relpath,
            message=f"documentation page '{relpath}' is not listed in {V2_INDEX_RELPATH}",
            suggestion=V2_SUGGESTION,
        ))
    return findings
