"""Tests for lib.consistency.docs.check_requirements_no_plan_sections.

Structural enforcement of the fix for issue #677: agents/1-generic/requirements.md
documents (in prose only) that docs/REQUIREMENTS.md must never carry
implementation-plan chapters (ordered steps, agent assignment, effort estimate,
`pipeline_stages:` mapping) -- those belong to `planner`. This check catches a
silent reintroduction of such a chapter (PR #742 code-review finding 3).
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.consistency.docs import check_requirements_no_plan_sections  # noqa: E402


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_no_finding_on_missing_file(tmp_path: Path) -> None:
    assert check_requirements_no_plan_sections(tmp_path) == []


def test_clean_requirements_file_is_not_flagged(tmp_path: Path) -> None:
    """Mirrors agent-meta's own current docs/REQUIREMENTS.md (no plan chapter)."""
    _write(
        tmp_path, "docs/REQUIREMENTS.md",
        "# Anforderungen — agent-meta\n\n"
        "## Commands-System\n\nSome requirement text.\n\n"
        "## Admin UI Setup-Modus\n\nAnother requirement.\n",
    )
    assert check_requirements_no_plan_sections(tmp_path) == []


def test_flags_plan_heading(tmp_path: Path) -> None:
    _write(
        tmp_path, "docs/REQUIREMENTS.md",
        "# Anforderungen\n\n## Requirement A\n\nText.\n\n"
        "## Implementation Plan\n\n| Step | Agent |\n|---|---|\n",
    )
    findings = check_requirements_no_plan_sections(tmp_path)
    assert len(findings) == 1
    assert findings[0].check == "docs.requirements_no_plan_sections"
    assert findings[0].file == "docs/REQUIREMENTS.md"


def test_flags_step_by_step_heading(tmp_path: Path) -> None:
    _write(
        tmp_path, "docs/REQUIREMENTS.md",
        "# Anforderungen\n\n## Step-by-Step Implementation\n\n"
        "| # | Step | Agent | Depends on |\n|---|---|---|---|\n",
    )
    findings = check_requirements_no_plan_sections(tmp_path)
    assert len(findings) == 1


def test_flags_numbered_step_heading(tmp_path: Path) -> None:
    _write(
        tmp_path, "docs/REQUIREMENTS.md",
        "# Anforderungen\n\n## Step 1 — Fix tier filter\n\nDetails.\n",
    )
    findings = check_requirements_no_plan_sections(tmp_path)
    assert len(findings) == 1


def test_flags_pipeline_stages_frontmatter(tmp_path: Path) -> None:
    _write(
        tmp_path, "docs/REQUIREMENTS.md",
        "---\ntype: Plan\npipeline_stages:\n  - requirements\n  - developer\n---\n\n"
        "# Anforderungen\n",
    )
    findings = check_requirements_no_plan_sections(tmp_path)
    assert len(findings) == 1
