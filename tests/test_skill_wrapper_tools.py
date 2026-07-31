"""Regression test: the external-skill wrapper template must not grant the
Agent tool — it should recommend delegation in text, not perform it itself.

Run: python -m pytest tests/test_skill_wrapper_tools.py -v
"""

import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATE = _REPO_ROOT / "agents" / "0-external" / "_skill-wrapper.md"


def test_skill_wrapper_does_not_grant_agent_tool():
    content = _TEMPLATE.read_text(encoding="utf-8")
    fm_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert fm_match, "frontmatter block not found"
    fm_block = fm_match.group(1)
    tools_match = re.search(r"^tools:\n((?:\s*-\s*.+\n?)+)", fm_block, re.MULTILINE)
    assert tools_match, "tools: list not found in frontmatter"
    tools = [line.strip("- ").strip() for line in tools_match.group(1).splitlines() if line.strip()]
    assert "Agent" not in tools, f"expected no Agent tool, got {tools!r}"
