"""H5 description lint (PR 6.1 / Loop Batch 1, Task 2.3).

Pins rubric R1 (description <= 160 chars, plan §4) and E-29 (no ``Issue #N``
in the prompt description) for every source agent template under
``agents/1-generic``. Unit cases exercise the pure helper directly; the
parametrized case is the repo-wide ratchet that must go GREEN in this PR.

Source templates are the lint target (rendered output is rebaselined centrally).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.agent_description_lint import (  # noqa: E402
    MAX_DESCRIPTION_LENGTH,
    extract_description,
    lint_description,
    lint_template_files,
)

AGENTS_DIR = REPO_ROOT / "agents" / "1-generic"


def _doc(description: str) -> str:
    return f'---\nname: probe\ndescription: "{description}"\n---\nbody'


# --- unit level -----------------------------------------------------------


def test_max_length_is_160():
    assert MAX_DESCRIPTION_LENGTH == 160


def test_accepts_description_at_limit():
    assert lint_description(_doc("x" * 160)) == []


def test_rejects_description_over_limit():
    findings = lint_description(_doc("x" * 161), "probe.md")
    assert len(findings) == 1
    assert "161 chars" in findings[0]
    assert "probe.md" in findings[0]


def test_missing_description_is_finding_not_crash():
    assert lint_description("---\nname: probe\n---\nbody") != []


def test_unquoted_description_is_supported():
    assert extract_description("---\ndescription: plain text\n---\nbody") == "plain text"


def test_issue_reference_in_description_is_rejected():
    text = _doc("Audits requirements (Issue #339 B1).")
    assert any("issue reference" in f for f in lint_description(text))


def test_issue_number_in_html_comment_is_ignored():
    text = '---\ndescription: "Audits requirements."\n---\nbody <!-- Issue #339 -->'
    assert lint_description(text) == []


# --- repo-wide ratchet ----------------------------------------------------


def _templates():
    # 101 files = 99 roles + _README.md + _wf-orchestrator-reference.md.
    # Only role templates carry a frontmatter description (rubric R1).
    return sorted(
        p for p in AGENTS_DIR.glob("*.md")
        if p.is_file() and not p.name.startswith("_")
    )


def test_agent_templates_present():
    assert len(_templates()) >= 90


@pytest.mark.parametrize("path", _templates(), ids=lambda p: p.stem)
def test_description_r1_and_e29(path: Path):
    findings = lint_description(path.read_text(encoding="utf-8"), path.name)
    assert findings == [], "\n".join(findings)


def test_lint_template_files_matches_per_file_results():
    results = lint_template_files(AGENTS_DIR)
    assert results
    assert all(findings == [] for findings in results.values())
    assert set(results) == {p.name for p in _templates()}
