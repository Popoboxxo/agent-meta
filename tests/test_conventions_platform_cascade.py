"""Regression tests for the platform conventions-preset cascade
(Task 5 of the platform-project-defaults feature, scripts/lib/conventions.py).

See this task's plan notes for why a synthetic agent_meta_root fixture is
used instead of the real platform-configs/ (none of the three real
platforms sets conventions-preset, by design -- see Task 1).
Spec: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.conventions import resolve_conventions
from scripts.lib.frontmatter import parse_frontmatter_file


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


# --- 2-platform override version governance (spec/plan workflow, Task 19) -----
#
# Every 2-platform override of a role changed by the spec/plan-workflow plan
# must track its 1-generic base: `based-on` pins the exact *current* generic
# version and the override carries a valid semver `version`
# (rules/2-platform/agent-meta-conventions.md, Change Checklist).
#
# The existing config_audit drift check only fires on major-version skew, so a
# minor/patch lag (e.g. documenter 1.4.1 behind 1.9.0) stays invisible. This
# test closes that gap for the roles touched by the spec/plan workflow.

_BASED_ON_RE = re.compile(
    r"^1-generic/(?P<stem>[A-Za-z0-9_-]+)\.md@(?P<version>[\w.\-]+)$"
)
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

# Roles changed by the spec/plan workflow (spec §9).
_PLAN_CHANGED_ROLES = frozenset({
    "ideation", "explorer", "concept-architect", "concept-specifier",
    "concept-reviewer", "planner", "orchestrator", "documenter",
})


def _plan_changed_overrides() -> list[Path]:
    """2-platform overrides whose 1-generic base is a plan-changed role."""
    overrides: list[Path] = []
    for path in sorted((_REPO_ROOT / "agents" / "2-platform").glob("*.md")):
        based_on = parse_frontmatter_file(path).get("based-on", "")
        match = _BASED_ON_RE.match(based_on) if isinstance(based_on, str) else None
        if match and match.group("stem") in _PLAN_CHANGED_ROLES:
            overrides.append(path)
    return overrides


def test_plan_changed_overrides_exist():
    """Guard: the drift scan must actually find the documenter override."""
    names = {path.name for path in _plan_changed_overrides()}
    assert "homeassistant-documenter.md" in names


def test_plan_changed_overrides_track_current_generic_version():
    """`based-on` must pin the exact current 1-generic version — no drift."""
    overrides = _plan_changed_overrides()
    assert overrides, "expected at least one plan-changed 2-platform override"
    for path in overrides:
        based_on = parse_frontmatter_file(path).get("based-on")
        match = _BASED_ON_RE.match(based_on) if isinstance(based_on, str) else None
        assert match, f"{path.name}: malformed based-on {based_on!r}"

        generic_stem = match.group("stem")
        generic_path = _REPO_ROOT / "agents" / "1-generic" / f"{generic_stem}.md"
        assert generic_path.is_file(), f"{path.name}: missing base {generic_path}"

        generic_version = parse_frontmatter_file(generic_path).get("version")
        assert based_on == f"1-generic/{generic_stem}.md@{generic_version}", (
            f"{path.name}: based-on {based_on!r} is stale; base "
            f"{generic_stem}.md is at @{generic_version}"
        )


def test_plan_changed_overrides_have_valid_version():
    """Every affected override carries a well-formed semver `version`."""
    overrides = _plan_changed_overrides()
    assert overrides, "expected at least one plan-changed 2-platform override"
    for path in overrides:
        version = parse_frontmatter_file(path).get("version")
        assert isinstance(version, str) and _SEMVER_RE.match(version), (
            f"{path.name}: invalid frontmatter version {version!r}"
        )
