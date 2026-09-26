"""Builds the documentation tree model (one entry per doc page, IC-09).

**This is the single component that knows documentation-filesystem semantics.**
The exclusion set, the relative-path shape, the title/description derivation and
the sort order all live here and *must not* be duplicated into
``scripts/lib/doc_facts.py``: a second copy of "which directories are excluded"
is a second copy of the truth, and the two drift apart silently — the counting
fact would then report a different tree than the index lists, with both sides
looking individually correct. W1-8 observed such a constant in ``doc_facts.py``
(``DOCS_EXCLUDED_DIR_SEGMENTS``, ``{'archive', '_archive'}`` — already missing
``local-Inputs``, i.e. drifted before this module existed); the W1 consolidation
fix round removed the duplicate, so ``doc_facts`` now *imports*
:data:`EXCLUDED_DIR_SEGMENTS` from here rather than re-declaring it.

Three contracts are hard, not incidental:

* **No invented description.** A page without frontmatter gets ``description``
  :data:`EMPTY_DESCRIPTION` (``—``) and a title derived from the file itself.
  Inventing plausible one-liners here would recreate, inside the generated
  index, the very defect class this initiative exists to remove — a plausible
  sentence nobody wrote and nobody can verify. A blank is visible in review; a
  fabrication is not. (IC-09 fallback; plan W1-8 acceptance.)
* **Byte-identical on repeated runs** (NFA-01). The model is a pure function of
  the tree: no timestamp, no mtime, no absolute path, no set-iteration order
  leaking into the result. ``Path.rglob`` yields entries in filesystem order,
  which differs between machines and between checkouts, so the sort in
  :func:`build_index_model` is what actually provides determinism — it is not
  cosmetic.
* **Sort by ``kind``, then ``path``** (NFA-02), using the fixed
  :data:`KIND_ORDER`. Sorting by path alone would reshuffle the whole file
  whenever a directory is added at the top of the tree; the two-key sort keeps
  the diff to the section that actually changed.

**Leaf module.** It imports only :mod:`scripts.lib.frontmatter` (re, functools
and pathlib only, no ``scripts.lib`` imports of its own) for the canonical
frontmatter splitter. It deliberately does **not** import ``config`` — W3 wires
it, and an import back into ``config`` would make that impossible without a
cycle. It **writes nothing** and never opens a file for writing; the caller owns
every file it will later render.
"""
from __future__ import annotations

from pathlib import Path

from .frontmatter import parse_frontmatter_text, split_frontmatter

EXCLUDED_DIR_SEGMENTS: frozenset[str] = frozenset({"archive", "_archive", "local-Inputs"})
"""Directory segments that never contribute an entry (IC-09).

Matched against the path *relative to the docs root*, at any depth, so
``docs/specs/archive/x.md`` and ``docs/archive/specs/y.md`` are both excluded.
Comparison is exact and case-sensitive: ``Archive/`` is a different directory
name and this initiative does not get to decide that a maintainer meant an
archive.
"""

DESCRIPTION_MAX_CHARS: int = 120
"""Maximum length of a rendered one-line description, ellipsis included.

An over-long description is **truncated**, never summarised: the result is a
prefix of a real frontmatter value, not a shortened paraphrase of it. The budget
counts the ellipsis, so a result never exceeds this value.
"""

EMPTY_DESCRIPTION: str = "—"
"""Placeholder for a page with no frontmatter ``description``.

**DEVIATION from IC-09's literal wording** (which says the model yields ``""``
and *the renderer* substitutes the dash): the model emits the dash directly, per
plan W1-8's acceptance criterion ("Frontmatter-lose Datei → Dateiname als
``title``, ``—`` als description"). The two are equivalent for a renderer that
renders the description verbatim; a renderer that normalises empty input must
treat ``""`` and :data:`EMPTY_DESCRIPTION` as the same value. Exported so that
consumer does not hard-code the character.
"""

KIND_ORDER: tuple[str, ...] = (
    "architecture",
    "api",
    "providers",
    "guides",
    "specs",
    "plans",
    "spikes",
    "concepts",
    "se-cascade",
    "other",
)
"""Canonical ``kind`` sequence — also the sort key (IC-09).

Spec §3.2 is a SSoT *matrix* and fixes no rendering order of its own; IC-09
enumerates the kinds in this order, so the enumeration is the order. ``other``
is last because it is the residual bucket: an unmapped directory is a finding
to raise, not a section to lead the index with.

Note that ``docs/howto/`` is deliberately **not** mapped to ``guides``. M-6
migrates it into ``docs/guides/`` (W5); mapping it early would make this model
assert a migration that has not happened, and the page would change section
twice for one move. Until W5 it lands in ``other``.
"""

_KIND_BY_TOP_SEGMENT: dict[str, str] = {
    "architecture": "architecture",
    "api": "api",
    "providers": "providers",
    "guides": "guides",
    "specs": "specs",
    "plans": "plans",
    "spikes": "spikes",
    "concepts": "concepts",
    "se-cascade": "se-cascade",
}

DOCS_RELPATH: str = "docs"
"""Project-relative location of the documentation tree."""

DOCS_SUFFIX: str = ".md"
"""Only Markdown pages are indexed; other files under ``docs/`` are not pages."""

_HEADING_PREFIX: str = "# "


def _normalise_description(value: object) -> str:
    """Return the one-line description for a frontmatter ``description``.

    Only a *real* frontmatter value survives. A non-string (a YAML list, an
    int) is treated as absent rather than coerced — ``str([...])`` would put a
    Python repr into tracked documentation. Whitespace is folded to single
    spaces so a wrapped YAML value cannot break the one-line contract, then the
    text is truncated to :data:`DESCRIPTION_MAX_CHARS` with an ellipsis.
    """
    if not isinstance(value, str):
        return EMPTY_DESCRIPTION
    text = " ".join(value.split())
    if not text:
        return EMPTY_DESCRIPTION
    if len(text) <= DESCRIPTION_MAX_CHARS:
        return text
    return text[: DESCRIPTION_MAX_CHARS - 1].rstrip() + "…"


def _title_from_body(body: str, path: Path) -> str:
    """First ``# `` heading, else the file name without its suffix (IC-09).

    The heading wins because a page's own H1 is written prose; the file name is
    the fallback because it is the one identifier that is always present. A
    heading of only hashes (``#`` alone) is not a title and is skipped, so the
    name is used instead of a bare ``#``.
    """
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith(_HEADING_PREFIX):
            continue
        heading = stripped[len(_HEADING_PREFIX) :].strip()
        if heading:
            return heading
    return path.stem


def _entry_for(path: Path, relpath: str) -> dict:
    """Return the index entry of one page named *relpath* below the docs root.

    The file is read **once** and both the frontmatter mapping and the body come
    out of that single text: a second read could, on a tree that changes under
    the call, produce a title from one version and a description from another —
    an entry that describes no file that ever existed.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        text = ""
    _, body = split_frontmatter(text)
    return {
        "path": relpath,
        "title": _title_from_body(body, path),
        "description": _normalise_description(parse_frontmatter_text(text).get("description")),
        "kind": _kind_for(relpath),
        "depth": _depth_for(relpath),
    }


def _kind_for(relpath: str) -> str:
    """``kind`` of the entry, decided by the top-level directory of *relpath*."""
    top = relpath.split("/", 1)[0]
    return _KIND_BY_TOP_SEGMENT.get(top, "other")


def _depth_for(relpath: str) -> int:
    """Directory nesting level below the docs root (``INDEX.md`` → 0)."""
    return relpath.count("/")


def _is_excluded(parts: tuple[str, ...]) -> bool:
    """True when any path *parts* segment is an excluded directory name."""
    return bool(EXCLUDED_DIR_SEGMENTS.intersection(parts))


def _iter_page_relpaths(docs_root: Path) -> list[str]:
    """All indexable page paths relative to *docs_root*, as posix strings.

    Symlinked files are skipped: a symlink makes the same page reachable under
    two names, and the index would then list one page twice under two titles —
    a fact nothing downstream could detect. The traversal result is sorted
    before it is returned so the *input* to the kind sort is already stable.
    """
    relpaths: list[str] = []
    for path in docs_root.rglob(f"*{DOCS_SUFFIX}"):
        if path.is_symlink() or not path.is_file():
            continue
        relpath = path.relative_to(docs_root).as_posix()
        parts = tuple(relpath.split("/")[:-1])
        if _is_excluded(parts):
            continue
        relpaths.append(relpath)
    return sorted(relpaths)


def build_index_model(project_root: Path) -> dict:
    """Return ``{'root', 'entries': [{'path','title','description','kind','depth'}]}``.

    *project_root* is the repository root; the tree scanned is
    ``<project_root>/docs``. ``root`` is the **relative** posix path of that
    tree (``'docs'``) — never an absolute path, which would put the checkout
    location into generated documentation (NFA-02).

    A missing or unreadable ``docs/`` directory yields ``{'root': 'docs',
    'entries': []}`` rather than raising: this model is consumed by a renderer
    that must degrade to "nothing to list", not abort a sync over a
    documentation gap.

    Determinism (NFA-01): entries are sorted by ``kind`` in
    :data:`KIND_ORDER`, then by ``path`` ascending, so two calls on one tree
    return equal structures that serialise to identical bytes.
    """
    docs_root = Path(project_root) / DOCS_RELPATH
    root = DOCS_RELPATH
    if not docs_root.is_dir():
        return {"root": root, "entries": []}

    entries = [
        _entry_for(docs_root / relpath, relpath) for relpath in _iter_page_relpaths(docs_root)
    ]
    entries.sort(key=lambda entry: (KIND_ORDER.index(entry["kind"]), entry["path"]))
    return {"root": root, "entries": entries}
