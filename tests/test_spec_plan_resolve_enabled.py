"""Tests for resolve_spec_plan_enabled and its injection into resolve_dod
(spec 5.4, F8). Precedence: explicit bool > dod.spec-plan-required > false.
Absence semantics matter: a missing key falls back to the preset, never to
a materialized nested default."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.dod import (
    resolve_dod,
    resolve_spec_plan_bundle,
    resolve_spec_plan_enabled,
)  # noqa: E402


def _meta_root(tmp_path: Path, required: bool) -> Path:
    root = tmp_path / "agent-meta"
    config_dir = root / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "dod-presets.yaml").write_text(
        "presets:\n"
        "  full:\n"
        f"    spec-plan-required: {str(required).lower()}\n"
        "    spec-plan-traceability: false\n"
        '    se-required: "false"\n',
        encoding="utf-8",
    )
    return root


def test_explicit_enabled_true_wins(tmp_path):
    root = _meta_root(tmp_path, required=False)
    config = {"platforms": [], "spec-plan-workflow": {"enabled": True}}
    assert resolve_spec_plan_enabled(config, root) is True


def test_explicit_enabled_false_wins_over_preset_true(tmp_path):
    root = _meta_root(tmp_path, required=True)
    config = {"platforms": [], "spec-plan-workflow": {"enabled": False}}
    assert resolve_spec_plan_enabled(config, root) is False


def test_absent_key_falls_back_to_preset_true(tmp_path):
    root = _meta_root(tmp_path, required=True)
    assert resolve_spec_plan_enabled({"platforms": []}, root) is True


def test_absent_key_and_preset_false_is_false(tmp_path):
    root = _meta_root(tmp_path, required=False)
    assert resolve_spec_plan_enabled({"platforms": []}, root) is False


def test_dod_override_beats_preset(tmp_path):
    root = _meta_root(tmp_path, required=False)
    config = {"platforms": [], "dod": {"spec-plan-required": True}}
    assert resolve_spec_plan_enabled(config, root) is True


def test_injected_dod_is_used_without_second_resolution(tmp_path):
    root = _meta_root(tmp_path, required=False)
    config = {"platforms": [], "spec-plan-workflow": {"enabled": True}}
    assert resolve_spec_plan_enabled(config, root, dod={"spec-plan-required": False}) is True


def test_resolve_dod_injects_synthetic_key(tmp_path):
    root = _meta_root(tmp_path, required=True)
    resolved = resolve_dod({"platforms": []}, root)
    assert resolved["spec-plan-enabled"] is True


_BUNDLE_CASES = [
    ({"platforms": []}, False),
    ({"platforms": []}, True),
    ({"platforms": [], "spec-plan-workflow": {"enabled": True}}, False),
    ({"platforms": [], "spec-plan-workflow": {"enabled": False}}, True),
    ({"platforms": [], "dod": {"spec-plan-required": True}}, False),
]


@pytest.mark.parametrize("config,required", _BUNDLE_CASES)
def test_wrapper_matches_bundle_enabled(tmp_path, config, required):
    root = _meta_root(tmp_path, required)
    assert (
        resolve_spec_plan_enabled(config, root)
        == resolve_spec_plan_bundle(config, root)["enabled"]
    )


def test_wrapper_matches_bundle_enabled_with_injected_dod(tmp_path):
    root = _meta_root(tmp_path, required=False)
    config = {"platforms": []}
    dod = {"spec-plan-required": True}
    assert (
        resolve_spec_plan_enabled(config, root, dod=dod)
        == resolve_spec_plan_bundle(config, root, dod=dod)["enabled"]
    )
