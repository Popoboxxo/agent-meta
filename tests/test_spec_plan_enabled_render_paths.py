"""B3-Rest: SPEC_PLAN_WORKFLOW_ENABLED reaches the real render paths, and
resolve_dod() is resolved exactly once per build_variables() call. The
synthetic spec-plan-enabled key gates the conditional pipeline stage."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import lib.config as config_mod
import lib.dod as dod_mod
from lib.config import build_variables
from lib.dod import resolve_dod
from lib.pipelines import inject_pipeline_blocks


def _config(enabled):
    return {
        "platforms": [],
        "dod-preset": "full",
        "spec-plan-workflow": {"enabled": enabled},
    }


_PIPELINES = {
    "concept-driven-dev": {
        "enabled": True,
        "stages": [
            {
                "id": "specify",
                "agent": "concept-specifier",
                "task": "Spec schreiben",
                "mode": "conditional",
                "condition": {"dod_flag": "spec-plan-enabled"},
            }
        ],
    }
}


def test_variable_true_when_enabled():
    variables, _ = build_variables(_config(True), REPO_ROOT)
    assert variables["SPEC_PLAN_WORKFLOW_ENABLED"] == "true"


def test_variable_false_when_disabled():
    variables, _ = build_variables(_config(False), REPO_ROOT)
    assert variables["SPEC_PLAN_WORKFLOW_ENABLED"] == "false"


def test_default_paths_present():
    variables, _ = build_variables(_config(True), REPO_ROOT)
    assert variables["SPEC_PLAN_SPECS_DIR"] == "docs/specs"
    assert variables["SPEC_PLAN_PLANS_DIR"] == "docs/plans"


def test_path_overrides_are_reflected():
    config = {
        "platforms": [],
        "dod-preset": "full",
        "spec-plan-workflow": {
            "enabled": True,
            "paths": {"specs": "custom/specs", "plans": "custom/plans"},
        },
    }
    variables, _ = build_variables(config, REPO_ROOT)
    assert variables["SPEC_PLAN_SPECS_DIR"] == "custom/specs"
    assert variables["SPEC_PLAN_PLANS_DIR"] == "custom/plans"


def test_resolve_dod_called_once_via_fallback(monkeypatch):
    """Without an explicit `enabled`, the resolver must consult the DoD
    fallback (`spec-plan-required`) -- and it must reuse the already-resolved
    dict via `dod=`, not trigger a second resolve_dod() call."""
    calls = {"config": 0, "dod": 0}
    real_config = config_mod.resolve_dod
    real_dod = dod_mod.resolve_dod
    real_load = dod_mod.load_dod_presets

    def _spy_config(config, agent_meta_root):
        calls["config"] += 1
        return real_config(config, agent_meta_root)

    def _spy_dod(config, agent_meta_root):
        calls["dod"] += 1
        return real_dod(config, agent_meta_root)

    def _presets_with_spec_plan_required(agent_meta_root):
        # Simulate a DoD preset declaring the workflow required (the
        # `spec-plan-required: true` key Task 3 adds to the real presets).
        presets = real_load(agent_meta_root)
        presets["full"] = {**presets.get("full", {}), "spec-plan-required": True}
        return presets

    monkeypatch.setattr(config_mod, "resolve_dod", _spy_config)
    monkeypatch.setattr(dod_mod, "resolve_dod", _spy_dod)
    monkeypatch.setattr(
        dod_mod, "load_dod_presets", _presets_with_spec_plan_required,
    )

    # No explicit `spec-plan-workflow.enabled` -> the fallback branch runs.
    config = {"platforms": [], "dod-preset": "full"}
    variables, _ = build_variables(config, REPO_ROOT)

    assert variables["SPEC_PLAN_WORKFLOW_ENABLED"] == "true"
    assert calls["config"] == 1
    # If _build_dod_variables() dropped `dod=dod_resolved`, the fallback would
    # resolve the DoD a second time and this counter would be 1.
    assert calls["dod"] == 0


def test_pipeline_gate_stage_hidden_when_disabled():
    rendered = inject_pipeline_blocks(
        "{{PIPELINE_DETAIL_BLOCKS}}", _PIPELINES, "Claude",
        resolve_dod(_config(False), REPO_ROOT),
    )
    assert "concept-specifier" not in rendered


def test_pipeline_gate_stage_present_when_enabled():
    rendered = inject_pipeline_blocks(
        "{{PIPELINE_DETAIL_BLOCKS}}", _PIPELINES, "Claude",
        resolve_dod(_config(True), REPO_ROOT),
    )
    assert "concept-specifier" in rendered
