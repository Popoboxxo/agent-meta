"""#1168: the git template states that a prompt-dictated Co-Authored-By trailer wins.

Run: python3 -m pytest tests/test_git_template_commit_trailer_rule.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.log import SyncLog
from lib.provider_transform import transform_agent_content_for_provider
from lib.providers import load_provider_capabilities, load_providers_config

_TEMPLATE = (REPO_ROOT / "agents" / "1-generic" / "git.md").read_text(encoding="utf-8")
_CONFIG = {
    "agent-meta-version": "2.0.0-beta.1",
    "ai-providers": ["Claude"],
    "dod-preset": "rapid-prototyping",
    "variables": {"PROJECT_NAME": "matrix", "PROJECT_PREFIX": "mx"},
}


def _claude_render() -> str:
    return transform_agent_content_for_provider(
        _TEMPLATE, "Claude", "git", "git", "desc",
        "1-generic/git.md@0", _CONFIG, REPO_ROOT, REPO_ROOT,
        REPO_ROOT / ".claude" / "agents" / "git.md",
        load_providers_config(REPO_ROOT), SyncLog(),
        provider_capabilities=load_provider_capabilities(REPO_ROOT),
    )


def test_git_template_states_trailer_precedence():
    text = _claude_render()
    assert text.count("Co-Authored-By") == 1
    paragraph = next(p for p in text.split("\n\n") if "Co-Authored-By" in p)
    assert "verbatim" in paragraph
