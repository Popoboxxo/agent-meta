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

import yaml

from scripts.lib.config import build_variables, fill_defaults
from scripts.lib.log import SyncLog

# The real leaking set for a minimal hand-written project (issue #733),
# established empirically by syncing a config with only
# `project.name/prefix + ai-providers + roles: [developer]`: the five
# language variables plus PROJECT_GOAL / PROJECT_LANGUAGES / CODE_CONVENTIONS.
LEAKING_VARIABLES = (
    "COMMUNICATION_LANGUAGE",
    "USER_INPUT_LANGUAGE",
    "DOCS_LANGUAGE",
    "INTERNAL_DOCS_LANGUAGE",
    "CODE_LANGUAGE",
    "PROJECT_GOAL",
    "PROJECT_LANGUAGES",
    "CODE_CONVENTIONS",
)


def _minimal_config() -> dict:
    return {
        "project": {"name": "smoke-test", "prefix": "sm"},
        "ai-providers": ["Claude"],
        "roles": ["developer"],
    }


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


# ---------------------------------------------------------------------------
# Issue #733: the eight variables that leaked into generated rules/personas
# ---------------------------------------------------------------------------

def test_minimal_project_resolves_all_leaking_variables():
    """Every leaking variable must be present (so substitute() leaves no
    literal ``{{VAR}}`` behind) without any explicit ``variables:`` entry."""
    repo_root = Path(__file__).resolve().parents[1]
    variables, _ = build_variables(_minimal_config(), repo_root)
    missing = [v for v in LEAKING_VARIABLES if v not in variables]
    assert missing == [], f"still unresolved for a minimal project: {missing}"


def test_language_fallbacks_match_framework_conventions():
    """The language rule must stay usable, not render empty -- defaults mirror
    the framework's own Sprachregeln table (AGENTS.md)."""
    repo_root = Path(__file__).resolve().parents[1]
    variables, _ = build_variables(_minimal_config(), repo_root)
    assert variables["COMMUNICATION_LANGUAGE"] == "Deutsch"
    assert variables["USER_INPUT_LANGUAGE"] == "Deutsch"
    assert variables["DOCS_LANGUAGE"] == "Englisch"
    assert variables["INTERNAL_DOCS_LANGUAGE"] == "Deutsch"
    assert variables["CODE_LANGUAGE"] == "Englisch"


def test_explicit_variable_wins_over_fallback():
    repo_root = Path(__file__).resolve().parents[1]
    config = _minimal_config()
    config["variables"] = {"CODE_LANGUAGE": "Français", "PROJECT_LANGUAGES": "Rust"}
    variables, _ = build_variables(config, repo_root)
    assert variables["CODE_LANGUAGE"] == "Français"
    assert variables["PROJECT_LANGUAGES"] == "Rust"


def test_project_goal_still_prefers_description_over_empty_fallback():
    repo_root = Path(__file__).resolve().parents[1]
    config = _minimal_config()
    config["variables"] = {"PROJECT_DESCRIPTION": "A test project."}
    variables, _ = build_variables(config, repo_root)
    assert variables["PROJECT_GOAL"] == "A test project."


# ---------------------------------------------------------------------------
# Issue #737: --fill-defaults must populate the schema-required project.short
# ---------------------------------------------------------------------------

def test_fill_defaults_populates_project_short_from_name(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    config_path = tmp_path / "project.yaml"
    config_path.write_text(
        "project:\n  name: smoke-test\n  prefix: sm\n", encoding="utf-8"
    )

    fill_defaults(config_path, repo_root, SyncLog(), dry_run=False)

    reloaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert reloaded["project"]["short"] == "smoke-test"


def test_fill_defaults_falls_back_to_prefix_without_name(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    config_path = tmp_path / "project.yaml"
    config_path.write_text("project:\n  prefix: sm\n", encoding="utf-8")

    fill_defaults(config_path, repo_root, SyncLog(), dry_run=False)

    reloaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert reloaded["project"]["short"] == "sm"


def test_fill_defaults_keeps_explicit_project_short(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    config_path = tmp_path / "project.yaml"
    config_path.write_text(
        "project:\n  name: smoke-test\n  prefix: sm\n  short: custom\n",
        encoding="utf-8",
    )

    fill_defaults(config_path, repo_root, SyncLog(), dry_run=False)

    reloaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert reloaded["project"]["short"] == "custom"


def test_fill_defaults_project_short_is_reported(tmp_path):
    """The derived field must appear in the AUTO-FILL log, not silently."""
    repo_root = Path(__file__).resolve().parents[1]
    config_path = tmp_path / "project.yaml"
    config_path.write_text(
        "project:\n  name: smoke-test\n  prefix: sm\n", encoding="utf-8"
    )
    log = SyncLog()

    fill_defaults(config_path, repo_root, log, dry_run=False)

    assert any("project.short" in entry for entry in log.actions)
