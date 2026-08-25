"""Core-logic tests for platform-level config defaults.

These run against a SYNTHETIC config/platform-defaults.yaml built in tmp_path
(not the empty production file), plus a copy of the real project-config schema so
scalar-vs-list classification matches production. Covers merge precedence, the
roles: No-Op guard, additive list dedup, and the adopt/ignore/track state
transitions (concept sections 3-5).
"""

import shutil
import textwrap
from pathlib import Path

import pytest

from scripts.lib.io import _load_yaml_or_json
from scripts.lib.platform_defaults import (
    adopt_platform_default,
    apply_platform_defaults,
    compute_platform_defaults_diff,
    ignore_platform_default,
    load_platform_defaults_state,
    resolve_platform_defaults,
    track_platform_default,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

_PLATFORM_DEFAULTS_YAML = textwrap.dedent(
    """
    platforms:
      a:
        defaults:
          dod-preset: standard
          rules-preset: minimal
          mcp-servers: [homeassistant, shared]
          roles: [developer, code-reviewer]
      b:
        defaults:
          dod-preset: full
          mcp-servers: [shared, extra]
    """
)


@pytest.fixture()
def meta_root(tmp_path: Path) -> Path:
    """Synthetic agent-meta root: real schema + a populated platform-defaults.yaml."""
    (tmp_path / "config").mkdir()
    shutil.copy(
        REPO_ROOT / "config" / "project-config.schema.json",
        tmp_path / "config" / "project-config.schema.json",
    )
    (tmp_path / "config" / "platform-defaults.yaml").write_text(
        _PLATFORM_DEFAULTS_YAML, encoding="utf-8"
    )
    return tmp_path


@pytest.fixture()
def project_root(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("project")
    (root / ".meta-config").mkdir()
    return root


def _write_project(project_root: Path, body: str) -> None:
    (project_root / ".meta-config" / "project.yaml").write_text(body, encoding="utf-8")


def _raw(project_root: Path) -> dict:
    data, _ = _load_yaml_or_json(project_root / ".meta-config" / "project.yaml")
    return data or {}


# --- Merge precedence --------------------------------------------------------

def test_scalar_project_value_wins(meta_root):
    result = apply_platform_defaults(
        {"platforms": ["a"], "dod-preset": "strict"}, meta_root
    )
    assert result["dod-preset"] == "strict"


def test_scalar_default_fills_when_absent(meta_root):
    result = apply_platform_defaults({"platforms": ["a"]}, meta_root)
    assert result["dod-preset"] == "standard"
    assert result["rules-preset"] == "minimal"


def test_scalar_conflict_last_platform_wins(meta_root):
    result = apply_platform_defaults({"platforms": ["a", "b"]}, meta_root)
    assert result["dod-preset"] == "full"


def test_list_merge_is_additive_and_deduped(meta_root):
    result = apply_platform_defaults(
        {"platforms": ["a", "b"], "mcp-servers": ["proj", "shared"]}, meta_root
    )
    # Union order: platform-a, platform-b (deduped), then project (deduped).
    assert result["mcp-servers"] == ["homeassistant", "shared", "extra", "proj"]


# --- roles: No-Op guard ------------------------------------------------------

def test_roles_noop_when_absent(meta_root):
    # Project has no roles: -> platform roles default must be a No-Op.
    result = apply_platform_defaults({"platforms": ["a"]}, meta_root)
    assert result.get("roles") is None


def test_roles_additive_when_explicit_empty_list(meta_root):
    # roles: [] is explicit -> participates in the additive merge.
    result = apply_platform_defaults({"platforms": ["a"], "roles": []}, meta_root)
    assert result["roles"] == ["developer", "code-reviewer"]


def test_roles_additive_when_explicit_nonempty(meta_root):
    result = apply_platform_defaults(
        {"platforms": ["a"], "roles": ["tester"]}, meta_root
    )
    assert result["roles"] == ["developer", "code-reviewer", "tester"]


# --- resolve_platform_defaults (flat resolution) -----------------------------

def test_resolve_returns_flat_values(meta_root):
    values = resolve_platform_defaults(["a", "b"], meta_root)
    assert values["dod-preset"] == "full"
    assert set(values["mcp-servers"]) == {"homeassistant", "shared", "extra"}


# --- State transitions -------------------------------------------------------

def test_ignore_on_inherited_materializes_and_pins(meta_root, project_root):
    _write_project(project_root, "platforms: [a]\ndod-preset: full\n")
    # rules-preset is inherited (not explicit) -> ignore materializes it.
    ignore_platform_default("rules-preset", project_root, meta_root, dry_run=False)

    assert _raw(project_root).get("rules-preset") == "minimal"
    entry = load_platform_defaults_state(project_root)["keys"]["rules-preset"]
    assert entry["status"] == "ignored"
    assert entry["last_platform_value"] == "minimal"
    assert "ignored_at" in entry


def test_adopt_on_overridden_removes_explicit_value(meta_root, project_root):
    _write_project(project_root, "platforms: [a]\ndod-preset: full\n")
    adopt_platform_default("dod-preset", project_root, meta_root, dry_run=False)

    assert "dod-preset" not in _raw(project_root)
    entry = load_platform_defaults_state(project_root)["keys"]["dod-preset"]
    assert entry["status"] == "inherited"


def test_track_lifts_ignored_and_resets_baseline(meta_root, project_root):
    _write_project(project_root, "platforms: [a]\ndod-preset: full\n")
    ignore_platform_default("rules-preset", project_root, meta_root, dry_run=False)
    track_platform_default("rules-preset", project_root, meta_root, dry_run=False)

    entry = load_platform_defaults_state(project_root)["keys"]["rules-preset"]
    assert entry["status"] != "ignored"
    assert "ignored_at" not in entry
    assert entry["last_platform_value"] == "minimal"


def test_diff_reports_inherited_and_overridden(meta_root, project_root):
    _write_project(project_root, "platforms: [a]\ndod-preset: full\n")
    config = apply_platform_defaults(_raw(project_root), meta_root)
    statuses = {
        e["key"]: e["status"]
        for e in compute_platform_defaults_diff(config, meta_root, project_root)
    }
    assert statuses["dod-preset"] == "overridden"
    assert statuses["rules-preset"] == "inherited"


def test_dry_run_does_not_write_state_or_project(meta_root, project_root):
    _write_project(project_root, "platforms: [a]\ndod-preset: full\n")
    ignore_platform_default("rules-preset", project_root, meta_root, dry_run=True)
    # No state file, project.yaml untouched.
    assert load_platform_defaults_state(project_root) == {}
    assert "rules-preset" not in _raw(project_root)
