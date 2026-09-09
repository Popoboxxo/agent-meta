"""Regression tests for the platform dod-preset cascade
(Task 4 of the platform-project-defaults feature, scripts/lib/dod.py).

Uses the real agent-meta repo_root and the real
platform-configs/hacs.defaults.yaml fixture from Task 1 (dod-preset:
standard). Distinguishing assertions use dod-presets.yaml's real per-preset
field values (config/dod-presets.yaml): full.codebase-overview=True,
standard.tests-required=True/codebase-overview=False,
rapid-prototyping.tests-required=False.
Spec: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib.dod import resolve_dod, resolve_dod_preset_name

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_explicit_project_dod_preset_wins_over_platform_default():
    config = {"platforms": ["hacs"], "dod-preset": "rapid-prototyping"}
    assert resolve_dod_preset_name(config, _REPO_ROOT) == "rapid-prototyping"
    resolved = resolve_dod(config, _REPO_ROOT)
    assert resolved["tests-required"] is False  # rapid-prototyping, not hacs' 'standard'


def test_platform_dod_preset_wins_when_project_does_not_set_one():
    config = {"platforms": ["hacs"]}
    assert resolve_dod_preset_name(config, _REPO_ROOT) == "standard"
    resolved = resolve_dod(config, _REPO_ROOT)
    assert resolved["tests-required"] is True      # 'standard', not 'full's implicit default
    assert resolved["codebase-overview"] is False   # 'full' would be True here


def test_no_platforms_and_no_override_falls_back_to_full():
    config = {}
    assert resolve_dod_preset_name(config, _REPO_ROOT) == "full"
    resolved = resolve_dod(config, _REPO_ROOT)
    assert resolved["codebase-overview"] is True  # 'full' preset value
