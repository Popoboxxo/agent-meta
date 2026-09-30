"""Task 5 (stale-role-cleanup): managed-block shrink proof, duplicate-marker
visibility and S3 (``--only-variables``) warning.

Covers:
- AC-16 / IC-09: removing a role hint from ``variables`` shrinks the managed
  block to the new render while the surrounding foreign/user content stays
  byte-identical.
- AC-17 / IC-09 / OQ-6: a file with two ``managed-begin … managed-end`` pairs
  keeps the second block verbatim, remains parseable, and emits a warning
  instead of aborting the update.
- AC-18 (S3) / IC-09: the ``--only-variables`` path never re-renders the
  managed block and surfaces that as a visible warning.

The tests call the module-private helpers directly (as the spec contracts
them) and use this repo as ``agent_meta_root`` so the real
``templates/context/claude-managed.md`` is exercised.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.context import (  # noqa: E402
    _MANAGED_BLOCK_RE,
    _has_duplicate_managed_block,
    _split_context_file,
    _update_managed_html_block,
    only_variables,
)
from lib.log import SyncLog  # noqa: E402

FOREIGN_HEADER = "# My Project\n\nUser-authored header.\n\n"
FOREIGN_FOOTER = "\n\n## User notes\n\nThis must survive byte-for-byte.\n"

OLD_BLOCK = (
    "<!-- agent-meta:managed-begin -->\n"
    "Role hint A\n"
    "<!-- agent-meta:managed-end -->"
)

SECOND_BLOCK = (
    "\n\n<!-- agent-meta:managed-begin -->\n"
    "Second block must be preserved verbatim.\n"
    "<!-- agent-meta:managed-end -->"
)


def _run_managed_update(target: Path, project_root: Path, hint: str, log: SyncLog) -> None:
    _update_managed_html_block(
        target,
        project_root,
        {"AGENT_HINTS": hint},
        log,
        dry_run=False,
        agent_meta_root=REPO_ROOT,
        provider="Claude",
        pc={},
    )


def test_managed_block_shrinks_when_role_hint_removed(tmp_path: Path) -> None:
    """AC-16: A disappears, B appears, foreign content is byte-identical."""
    project_root = tmp_path
    target = project_root / "CLAUDE.md"
    target.write_text(FOREIGN_HEADER + OLD_BLOCK + FOREIGN_FOOTER, encoding="utf-8")

    log = SyncLog()
    _run_managed_update(target, project_root, "Role hint B", log)

    content = target.read_text(encoding="utf-8")
    header, block, footer = _split_context_file(content)

    assert block is not None
    assert "Role hint A" not in block, block
    assert "Role hint B" in block, block
    assert header == FOREIGN_HEADER
    assert footer == FOREIGN_FOOTER
    assert len(_MANAGED_BLOCK_RE.findall(content)) == 1


def test_duplicate_marker_keeps_second_block_and_warns(tmp_path: Path) -> None:
    """AC-17 / OQ-6: only the first pair is replaced; the second survives and
    the collision is surfaced as a warning (never an abort)."""
    project_root = tmp_path
    target = project_root / "CLAUDE.md"
    target.write_text(
        FOREIGN_HEADER + OLD_BLOCK + SECOND_BLOCK + FOREIGN_FOOTER,
        encoding="utf-8",
    )

    log = SyncLog()
    _run_managed_update(target, project_root, "Role hint B", log)

    content = target.read_text(encoding="utf-8")

    assert SECOND_BLOCK in content
    assert "Role hint A" not in content
    assert "Role hint B" in content
    assert len(_MANAGED_BLOCK_RE.findall(content)) == 2
    assert _has_duplicate_managed_block(content)
    assert not _has_duplicate_managed_block(FOREIGN_HEADER + OLD_BLOCK + FOREIGN_FOOTER)
    assert any("more than one" in w for w in log.warnings), log.warnings


def test_only_variables_warns_managed_block_not_refreshed(tmp_path: Path) -> None:
    """AC-18 / S3: ``--only-variables`` does not re-render the managed block
    and says so visibly."""
    project_root = tmp_path
    target = project_root / "CLAUDE.md"
    target.write_text(FOREIGN_HEADER + OLD_BLOCK + FOREIGN_FOOTER, encoding="utf-8")

    log = SyncLog()
    only_variables(
        project_root,
        {},
        log,
        dry_run=False,
        providers=["Claude"],
        provider_config={"Claude": {"context_file": "CLAUDE.md"}},
    )

    content = target.read_text(encoding="utf-8")
    assert OLD_BLOCK in content, "managed block must not be re-rendered by --only-variables"
    assert any(
        "managed block" in w and "not" in w for w in log.warnings
    ), log.warnings
