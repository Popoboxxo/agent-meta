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


@pytest.mark.parametrize("rel", _TEMPLATES)
def test_merge_pattern_in_three_templates(rel: str) -> None:
    text = (REPO_ROOT / rel).read_text(encoding="utf-8")
    assert "#1172" in text
    assert "#783" in text


def test_merge_pattern_in_rendered_rule_once() -> None:
    rendered = (REPO_ROOT / ".claude" / "rules" / "use-orchestrator.md").read_text(encoding="utf-8")
    assert rendered.count("#1172") == 1
    assert rendered.count("#783") == 1
