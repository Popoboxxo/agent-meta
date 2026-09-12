"""build_variables() coverage for the readme.* config block (issue #682 §3)."""

from pathlib import Path

from scripts.lib.config import build_variables

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_readme_variables_default_when_block_absent():
    variables, _ = build_variables({}, _REPO_ROOT)
    assert variables["README_BADGES"] == "version, stack, license"
    assert variables["README_WARNINGS_ENABLED"] == "false"
    assert variables["README_SECTIONS"] == "description, badges, setup, structure"


def test_readme_variables_reflect_explicit_config():
    config = {
        "readme": {
            "badges": ["version", "ci"],
            "warnings": True,
            "sections": ["description", "setup"],
        }
    }
    variables, _ = build_variables(config, _REPO_ROOT)
    assert variables["README_BADGES"] == "version, ci"
    assert variables["README_WARNINGS_ENABLED"] == "true"
    assert variables["README_SECTIONS"] == "description, setup"


def test_readme_variables_accept_agent_meta_badge_opt_in():
    """`agent-meta` flows through README_BADGES as a plain, data-driven badge
    type -- it is never added implicitly (opt-in only), so an explicit
    `["version","agent-meta"]` must survive verbatim
    (docs/concepts/agent-meta-version-badge.md §3/§7)."""
    config = {"readme": {"badges": ["version", "agent-meta"]}}
    variables, _ = build_variables(config, _REPO_ROOT)
    assert variables["README_BADGES"] == "version, agent-meta"


def test_readme_variables_keep_agent_meta_off_by_default():
    """The `agent-meta` badge must NOT be default-on: with no explicit
    badges list the default stays `version, stack, license`."""
    variables, _ = build_variables({"readme": {}}, _REPO_ROOT)
    assert variables["README_BADGES"] == "version, stack, license"
    assert "agent-meta" not in variables["README_BADGES"]
