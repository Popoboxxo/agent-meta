"""Source-template boilerplate de-duplication ratchet (IC-31, AC-72, #885 F-14).

Verbatim repeated lines in the source templates (``agents/1-generic``,
``agents/2-platform``, ``rules/**``, ``commands/**``) were replaced by
``{{..._BLOCK}}`` snippet variables (``snippets/agents/``) without changing the
rendered output (AC-01 harness). This module keeps it that way:

* ``test_boilerplate_snippets_not_inline`` -- the worker-role, closing-summary
  and user-proxy lines (read from the snippet files, never duplicated here)
  must not reappear inline in any source template.
* ``test_line_duplication_ratchet`` -- counts the stripped lines of >= 40
  characters that occur in >= 5 different source files. The ceilings are the
  measured actual state after IC-31; they may only ever be lowered.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SNIPPETS = _REPO_ROOT / "snippets" / "agents"

_SCAN_GLOBS = (
    "agents/1-generic/*.md",
    "agents/2-platform/*.md",
    "rules/**/*.md",
    "commands/**/*.md",
)
_MIN_LINE_LENGTH = 40
_MIN_FILES = 5

# Ratchet ceilings (actual state after IC-31 / Tasks 1.06 + 1.07, measured by
# ``_duplicate_lines()``). Lower them when duplicates disappear; never raise.
MAX_DUPLICATE_LINES = 16        # distinct lines present in >= 5 files
MAX_DUPLICATE_OCCURRENCES = 164  # sum of files over those lines

# Snippets whose body must no longer occur inline in a source template.
_DEDUPED_SNIPPETS = ("worker-role", "closing-summary", "user-proxy")


def _source_files() -> List[Path]:
    files: List[Path] = []
    for pattern in _SCAN_GLOBS:
        files.extend(sorted(_REPO_ROOT.glob(pattern)))
    return files


def _snippet_body(name: str) -> str:
    text = (_SNIPPETS / f"{name}.md").read_text(encoding="utf-8")
    return text.split("\n---\n", 1)[1].strip("\n")


def _duplicate_lines() -> Dict[str, Set[str]]:
    occurrences: Dict[str, Set[str]] = defaultdict(set)
    for path in _source_files():
        rel = path.relative_to(_REPO_ROOT).as_posix()
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if len(stripped) >= _MIN_LINE_LENGTH:
                occurrences[stripped].add(rel)
    return {line: files for line, files in occurrences.items() if len(files) >= _MIN_FILES}


def test_boilerplate_snippets_not_inline():
    offenders: List[str] = []
    for name in _DEDUPED_SNIPPETS:
        body = _snippet_body(name)
        assert "\n" not in body, f"{name}: snippet is expected to be a single line"
        for path in _source_files():
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if line.strip() == body:
                    offenders.append(f"{path.relative_to(_REPO_ROOT).as_posix()}:{number} ({name})")
    assert not offenders, (
        "boilerplate line is inline again -- use the {{..._BLOCK}} placeholder: "
        + "; ".join(offenders)
    )


def test_no_german_closing_summary_twin():
    """Task 1.07: the DE twin of the closing summary is unified on the EN block."""
    offenders = [
        path.relative_to(_REPO_ROOT).as_posix()
        for path in _source_files()
        if "Pflicht-Abschluss-Summary" in path.read_text(encoding="utf-8")
    ]
    assert not offenders, f"German closing-summary twin is back in: {offenders}"


def test_deduped_snippets_are_referenced():
    """Vacuum guard: each de-duplicated block is still consumed by templates."""
    for name in _DEDUPED_SNIPPETS:
        placeholder = "{{" + name.upper().replace("-", "_") + "_BLOCK}}"
        users = [p for p in _source_files() if placeholder in p.read_text(encoding="utf-8")]
        assert len(users) >= 5, f"{placeholder}: only {len(users)} users"


def test_line_duplication_ratchet():
    duplicates = _duplicate_lines()
    occurrences = sum(len(files) for files in duplicates.values())
    worst = sorted(duplicates.items(), key=lambda item: -len(item[1]))[:5]
    hint = "; ".join(f"{len(files)}x {line[:60]!r}" for line, files in worst)
    assert len(duplicates) <= MAX_DUPLICATE_LINES, (
        f"duplicate source lines grew: {len(duplicates)} > {MAX_DUPLICATE_LINES} ({hint})"
    )
    assert occurrences <= MAX_DUPLICATE_OCCURRENCES, (
        f"duplicate line occurrences grew: {occurrences} > {MAX_DUPLICATE_OCCURRENCES} ({hint})"
    )
