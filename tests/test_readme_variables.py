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
