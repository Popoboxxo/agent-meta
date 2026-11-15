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


def _claude_render(config=_CONFIG) -> str:
    return transform_agent_content_for_provider(
        _TEMPLATE, "Claude", "git", "git", "desc",
        "1-generic/git.md@0", config, REPO_ROOT, REPO_ROOT,
        REPO_ROOT / ".claude" / "agents" / "git.md",
        load_providers_config(REPO_ROOT), SyncLog(),
        provider_capabilities=load_provider_capabilities(REPO_ROOT),
    )


def test_git_template_states_trailer_precedence():
    text = _claude_render()
    assert text.count("Co-Authored-By") == 1
    paragraph = next(p for p in text.split("\n\n") if "Co-Authored-By" in p)
    assert "verbatim" in paragraph


def _render_with_variables(trailers):
    from lib.variables import strip_inactive_conditional_blocks, substitute
    variables = {"COMMIT_TRAILERS": "\n".join(trailers),
                 "COMMIT_TRAILERS_SET": "true" if trailers else "false"}
    text = strip_inactive_conditional_blocks(_claude_render(), variables)
    return substitute(text, variables, "git.md", SyncLog())


def test_git_template_version_and_precedence_wording():
    assert 'version: "2.2.0"' in _TEMPLATE
    paragraph = next(p for p in _claude_render().split("\n\n") if "Co-Authored-By" in p)
    assert "explicit brief from the requester > project config (`commit.trailers`) > harness attribution" in paragraph
    assert "brief wins" in paragraph and "exactly once" in paragraph
    assert "Verbindliche Trailer" not in _render_with_variables([])


def test_git_template_renders_config_trailers_verbatim():
    line = "Reviewed-by: Ann <ann@example.com>"
    text = _render_with_variables([line])
    assert text.count(line) == 1 and "Verbindliche Trailer" in text
    assert text.count("Co-Authored-By") == 1
    assert "Verbindliche Trailer" not in _render_with_variables([])
    assert "{{COMMIT_TRAILERS}}" not in _render_with_variables([])
