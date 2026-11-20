"""#1172: the supported merge dispatch pattern is documented in three templates.

Run: python3 -m pytest tests/test_merge_pattern_docs.py -q
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

_TEMPLATES = [
    "rules/1-generic/use-orchestrator.md",
    "agents/1-generic/orchestrator.md",
    "agents/1-generic/git.md",
]

# APPROVED spec IC-5 (2026-11-19): the merge sentence must carry this full text
# verbatim in every template -- not only the bare issue references.
_MERGE_FULL_TEXT = [
    "2026-11-06",
    "Merge Without Review",
    "Ursache außerhalb des Repos, nicht reproduziert",
]


def _gate_depth_before(lines: list[str], idx: int) -> int:
    """Number of unclosed {{#if}}/{{#unless}} blocks before line ``idx``."""
    depth = 0
    for line in lines[:idx]:
        stripped = line.strip()
        opens = stripped.count("{{#if") + stripped.count("{{#unless")
        closes = stripped.count("{{/if}}") + stripped.count("{{/unless}}")
        depth += opens - closes
    return depth


@pytest.mark.parametrize("rel", _TEMPLATES)
def test_merge_pattern_in_three_templates(rel: str) -> None:
    text = (REPO_ROOT / rel).read_text(encoding="utf-8")
    assert "#1172" in text
    assert "#783" in text
    for fragment in _MERGE_FULL_TEXT:
        assert fragment in text, f"{rel}: missing {fragment!r}"


def test_merge_pattern_in_rule_source_once_and_ungated() -> None:
    # Reads the tracked source (rendered .claude/ output is untracked, absent in CI).
    text = (REPO_ROOT / "rules/1-generic/use-orchestrator.md").read_text(encoding="utf-8")
    assert text.count("#1172") == 1
    assert text.count("#783") == 1
    # APPROVED spec IC-5 overrides the DRAFT gated plan: the sentence must survive
    # rendering even when AUTO_COMMIT_ENABLED / ROLE_GIT_ACTIVE are false.
    assert "{{#if ROLE_GIT_ACTIVE}}\n**Merge-Muster (#1172):**" not in text
    lines = text.splitlines()
    idx = next(i for i, line in enumerate(lines) if "**Merge-Muster (#1172):**" in line)
    assert _gate_depth_before(lines, idx) == 0
