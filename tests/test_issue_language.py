"""Unit tests for ISSUE_LANGUAGE (#579 — configurable feedback issue language).

Mirrors the style of test_build_variables_decomposition.py: exercises
_build_convention_variables() directly with plain dicts + this repo's own
agent_meta_root, no mocking needed.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.config import _build_convention_variables, build_variables, load_config

AGENT_META_ROOT = REPO_ROOT


def _base_config():
    return {
        "project": {"prefix": "tp", "short": "Test", "name": "Test Project"},
        "roles": ["developer", "feedback"],
    }


def test_issue_language_defaults_to_english():
    config = _base_config()
    variables = {}
    _build_convention_variables(variables, config, AGENT_META_ROOT)
    assert variables["ISSUE_LANGUAGE"] == "english"


def test_issue_language_overridable_via_conventions_block():
    config = _base_config()
    config["conventions"] = {"issues": {"language": "deutsch"}}
    variables = {}
    _build_convention_variables(variables, config, AGENT_META_ROOT)
    assert variables["ISSUE_LANGUAGE"] == "deutsch"


def test_issue_language_set_even_when_git_role_inactive():
    """ISSUE_LANGUAGE is consumed by feedback.md, not git.md — must not be
    gated behind the 'issues' domain's applies_to_roles: [git]."""
    config = _base_config()
    config["roles"] = ["feedback"]  # 'git' deliberately absent
    variables = {}
    _build_convention_variables(variables, config, AGENT_META_ROOT)
    assert variables["ISSUE_LANGUAGE"] == "english"
    assert "GIT_ISSUE_NAMING_BLOCK" not in variables


def test_build_variables_self_hosting_config_has_english_issue_language():
    """agent-meta's own project.yaml sets no conventions override -> default."""
    config = load_config(REPO_ROOT / ".meta-config" / "project.yaml")
    variables, _ = build_variables(config, AGENT_META_ROOT, AGENT_META_ROOT)
    assert variables["ISSUE_LANGUAGE"] == "english"
