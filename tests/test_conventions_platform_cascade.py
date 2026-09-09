"""Regression tests for the platform conventions-preset cascade
(Task 5 of the platform-project-defaults feature, scripts/lib/conventions.py).

See this task's plan notes for why a synthetic agent_meta_root fixture is
used instead of the real platform-configs/ (none of the three real
platforms sets conventions-preset, by design -- see Task 1).
Spec: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md
"""
from __future__ import annotations

import shutil
from pathlib import Path

from scripts.lib.conventions import resolve_conventions

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _fake_agent_meta_root(tmp_path: Path) -> Path:
    (tmp_path / "config").mkdir(parents=True)
    shutil.copy(
        _REPO_ROOT / "config" / "conventions-presets.yaml",
        tmp_path / "config" / "conventions-presets.yaml",
    )
    platform_dir = tmp_path / "platform-configs"
    platform_dir.mkdir()
    (platform_dir / "testplat.defaults.yaml").write_text(
        "conventions-preset: calver\n", encoding="utf-8",
    )
    return tmp_path


def test_explicit_project_conventions_preset_wins_over_platform_default(tmp_path):
    root = _fake_agent_meta_root(tmp_path)
    config = {"platforms": ["testplat"], "conventions-preset": "conventional-strict"}
    resolved = resolve_conventions(config, root)
    assert resolved["release"]["changelog"]["format"] == "angular"  # conventional-strict marker


def test_platform_conventions_preset_wins_when_project_does_not_set_one(tmp_path):
    root = _fake_agent_meta_root(tmp_path)
    config = {"platforms": ["testplat"]}
    resolved = resolve_conventions(config, root)
    assert resolved["release"]["versioning"]["scheme"] == "calver"  # platform default 'calver'


def test_no_platforms_and_no_override_falls_back_to_default(tmp_path):
    root = _fake_agent_meta_root(tmp_path)
    config = {}
    resolved = resolve_conventions(config, root)
    assert resolved["release"]["versioning"]["scheme"] == "semver"
    assert resolved["release"]["changelog"]["format"] == "keep-a-changelog"  # 'default' marker
