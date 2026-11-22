"""H3 worker-block size budgets (PR 6.1 / Loop Batch 1, Task 2.2).

Pins the four hard byte ceilings from the approved loop plan Task 2.2 against
the canonical snippet sources (the single source of every rendered worker
block). Frontmatter is excluded from the budget: it is YAML metadata, not
prompt text, and is stripped by the inlining transform.

Ceilings (plan §11 Batch 1 Task 2.2):
    background-process-guard <= 500 B
    parse-input              <= 900 B
    escalate-card            <= 1200 B
    closing-summary          <= 300 B
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SNIPPETS_DIR = REPO_ROOT / "snippets" / "agents"

BUDGET_BYTES = {
    "background-process-guard.md": 500,
    "parse-input.md": 900,
    "escalate-card.md": 1200,
    "closing-summary.md": 300,
}

# Semantics that must survive the closing-summary shortening (Task 2.2
# "Semantik erhalten"). Checked against the body with HTML provenance comments
# removed, mirroring rubric R9.
CLOSING_SUMMARY_ANCHORS = (
    "the structured block above is your entire return value",
    "the orchestrator consumes only this summary",
    "RESULT:",
    "ARTIFACTS",
)


def snippet_body(name: str) -> str:
    """Return the prompt body of a snippet (YAML frontmatter removed)."""
    text = (SNIPPETS_DIR / name).read_text(encoding="utf-8")
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                return "\n".join(lines[index + 1:]).strip("\n")
    return text.strip("\n")


@pytest.mark.parametrize("name,limit", sorted(BUDGET_BYTES.items()))
def test_snippet_body_within_budget(name: str, limit: int):
    body = snippet_body(name)
    size = len(body.encode("utf-8"))
    assert size <= limit, f"{name}: {size} B > {limit} B"


def test_closing_summary_keeps_semantic_anchors():
    body = snippet_body("closing-summary.md")
    for anchor in CLOSING_SUMMARY_ANCHORS:
        assert anchor in body, f"missing semantic anchor: {anchor!r}"


def test_closing_summary_has_no_inline_issue_reference():
    """E-29: provenance belongs in an HTML comment, not in prompt prose."""
    import re

    body = snippet_body("closing-summary.md")
    without_comments = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    assert re.search(r"\bIssue\s*#\s*\d+\b", without_comments, re.IGNORECASE) is None
