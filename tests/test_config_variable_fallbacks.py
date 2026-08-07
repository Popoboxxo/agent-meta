"""Regression tests for build_variables() placeholder fallbacks.

PROJECT_CONTEXT, ARCHITECTURE and DEV_COMMANDS used to only ever be set by
the interactive `sync.py --setup` wizard (scripts/lib/setup.py), with no
fallback anywhere in the normal sync path. Any project whose
.meta-config/project.yaml was hand-written or predates these variables (or
simply never ran the wizard) got a literal unsubstituted `{{VAR}}` in every
template referencing them -- found live via agent-meta-test's sandbox sync
(agents/1-generic/openscad-developer.md's "Dev environment:" line).
"""

from pathlib import Path

from scripts.lib.config import build_variables


def test_project_context_falls_back_to_project_description():
    repo_root = Path(__file__).resolve().parents[1]
    config = {"variables": {"PROJECT_DESCRIPTION": "A test project."}}
    variables, _ = build_variables(config, repo_root)
    assert variables["PROJECT_CONTEXT"] == "A test project."


def test_architecture_and_dev_commands_default_to_empty_string_not_missing():
    repo_root = Path(__file__).resolve().parents[1]
    config = {}
    variables, _ = build_variables(config, repo_root)
    # Must be present (so substitute() never leaves {{ARCHITECTURE}}/
    # {{DEV_COMMANDS}} in generated output) -- empty is fine, missing is not.
    assert variables.get("ARCHITECTURE") == ""
    assert variables.get("DEV_COMMANDS") == ""


def test_explicit_project_context_wins_over_fallback():
    repo_root = Path(__file__).resolve().parents[1]
    config = {"variables": {
        "PROJECT_DESCRIPTION": "fallback text",
        "PROJECT_CONTEXT": "explicit text",
    }}
    variables, _ = build_variables(config, repo_root)
    assert variables["PROJECT_CONTEXT"] == "explicit text"
