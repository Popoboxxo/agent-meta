"""Regression tests for the platform-variable cascade in build_variables()
(Task 3 of the platform-project-defaults feature,
scripts/lib/platform.py::apply_platform_variable_cascade()).

Uses the REAL agent-meta repo_root and the real platform-configs/
hacs.defaults.yaml fixture from Task 1 (TEST_COMMANDS: "pytest tests/ --cov",
PROJECT_LANGUAGES: "Python") -- same pattern as the pre-existing
tests/test_config_variable_fallbacks.py (build_variables() against the real
agent-meta checkout, not a synthetic agent_meta_root).
Spec: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib.config import build_variables

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_explicit_project_override_wins_over_platform_default():
    config = {
        "platforms": ["hacs"],
        "variables": {"TEST_COMMANDS": "custom-test-cmd"},
    }
    variables, _ = build_variables(config, _REPO_ROOT)
    assert variables["TEST_COMMANDS"] == "custom-test-cmd"


def test_plus_suffix_appends_to_platform_default():
    config = {
        "platforms": ["hacs"],
        "variables": {"TEST_COMMANDS+": "hacs-validate ."},
    }
    variables, _ = build_variables(config, _REPO_ROOT)
    assert variables["TEST_COMMANDS"] == "pytest tests/ --cov && hacs-validate ."


def test_platform_default_applies_when_project_sets_nothing():
    config = {"platforms": ["hacs"]}
    variables, _ = build_variables(config, _REPO_ROOT)
    assert variables["TEST_COMMANDS"] == "pytest tests/ --cov"
    assert variables["PROJECT_LANGUAGES"] == "Python"
    assert variables["PLATFORM"] == "Home Assistant Custom Component"


def test_no_platforms_set_leaves_old_behavior_unchanged():
    config = {}
    variables, _ = build_variables(config, _REPO_ROOT)
    # TEST_COMMANDS has no hardcoded framework default anywhere in config.py
    # (unlike DEV_COMMANDS/ARCHITECTURE) -- absent platforms, it stays unset,
    # exactly like before this feature existed.
    assert variables.get("TEST_COMMANDS") is None


def test_field_not_in_curated_list_is_never_platform_cascaded():
    # PROJECT_DESCRIPTION is not in _CASCADED_VARIABLE_FIELDS -- platform
    # defaults must never leak into non-curated fields, even if a platform
    # config happened to define one under the same name.
    config = {"platforms": ["hacs"], "variables": {"PROJECT_DESCRIPTION": "explicit"}}
    variables, _ = build_variables(config, _REPO_ROOT)
    assert variables["PROJECT_DESCRIPTION"] == "explicit"
