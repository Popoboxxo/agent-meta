"""IC-18 no. 2 / AC-46: pipelines with an inactive required stage role are dropped.

``pipelines.filter_pipelines_by_active_set`` implements the Spec §4.4 rule on the
``effective`` quality-pipelines dict: a pipeline stays only if every required
stage role (agent, ``parallel_group`` member, reflection-loop generator/critic,
plan-driven fallback) is in ``ActiveSet.roles``. Stages with an inactive
``dod_flag`` and ``optional`` stages are not required.

Scope note: the filter itself is covered here at function level on the versioned
p10/p20 fixtures. Wiring it into the renderers (section 2/2a, pipeline-details,
``routing.pipelines``) is deliberately not part of this test file -- in the
default project it would remove pipelines that render today (see the task report).
"""
from __future__ import annotations

import copy
import shutil
from pathlib import Path

from scripts.lib.active_set import compute_active_set
from scripts.lib.config import load_config
from scripts.lib.dod import resolve_dod
from scripts.lib.pipelines import (
    PipelineDrop,
    filter_pipelines_by_active_set,
    format_pipeline_drop,
    load_quality_pipelines,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES = REPO_ROOT / "tests" / "fixtures" / "active-set"


def _active(tmp_path: Path, fixture: str):
    (tmp_path / ".meta-config").mkdir()
    dest = tmp_path / ".meta-config" / "project.yaml"
    shutil.copyfile(_FIXTURES / fixture / ".meta-config" / "project.yaml", dest)
    with dest.open("a", encoding="utf-8") as fh:
        fh.write("project:\n  name: t\n  prefix: t\n")
    config = load_config(dest)
    return config, compute_active_set(config, REPO_ROOT, tmp_path, warn_sink=[])


def _filter(config, active):
    pipelines = load_quality_pipelines(str(REPO_ROOT))
    return filter_pipelines_by_active_set(
        pipelines, active, {}, active_dod=resolve_dod(config, REPO_ROOT))


def test_p10_renders_no_pipeline_with_inactive_required_role(tmp_path):
    # AC-46: p10 has no senior-developer/validator/bug-feature-analyzer/concept-*/ideation.
    config, active = _active(tmp_path, "p10")
    kept, drops = _filter(config, active)
    dropped = {d.pipeline: d for d in drops}
    assert set(dropped) == {
        "bugfix", "concept-development", "concept-driven-dev", "feature-lifecycle", "refactor",
    }
    assert "senior-developer" in dropped["refactor"].missing_roles
    assert dropped["refactor"].dropped_stages == ("analyze",)
    # parallel_group member and loop critic/generator count as required roles.
    assert dropped["feature-lifecycle"].missing_roles == ("validator",)
    assert "concept-reviewer" in dropped["concept-development"].missing_roles
    # Invariant: nothing that survives (and is enabled) needs an inactive role.
    assert set(kept) == {"docs-update", "quick-fix", "se-cascade"}
    assert kept["quick-fix"] is load_quality_pipelines(str(REPO_ROOT))["quick-fix"]


def test_stage_with_inactive_dod_flag_is_not_required(tmp_path):
    # quick-fix/root-cause needs bug-feature-analyzer only if root-cause-required is on.
    config, active = _active(tmp_path, "p10")
    pipelines = load_quality_pipelines(str(REPO_ROOT))
    off, _ = filter_pipelines_by_active_set(pipelines, active, {}, active_dod={"root-cause-required": False})
    on, drops = filter_pipelines_by_active_set(pipelines, active, {}, active_dod={"root-cause-required": True})
    assert "quick-fix" in off
    assert "quick-fix" not in on
    assert next(d for d in drops if d.pipeline == "quick-fix").missing_roles == ("bug-feature-analyzer",)
    # Without active_dod the DOD_<FLAG> variable decides (unknown flag = active).
    via_var, _ = filter_pipelines_by_active_set(
        pipelines, active, {"DOD_ROOT_CAUSE_REQUIRED": "false"})
    assert "quick-fix" in via_var


def test_p20_drops_only_refactor_for_gate_dropped_senior_developer(tmp_path):
    # AC-43/AC-46: senior-developer is in `roles:` but dropped by the developer_tiers gate.
    config, active = _active(tmp_path, "p20")
    assert not active.has("senior-developer")
    _, drops = _filter(config, active)
    refactor = next(d for d in drops if d.pipeline == "refactor")
    assert refactor.missing_roles == ("senior-developer",)
    # The WARN names the pipeline, the missing role and the gate/way to enable it.
    message = format_pipeline_drop(refactor, active)
    assert message.startswith("active-set.pipeline-dropped:")
    assert "'refactor'" in message and "'senior-developer'" in message
    assert "developer_tiers" in message


def test_optional_stage_with_inactive_role_is_removed_pipeline_survives(tmp_path):
    _, active = _active(tmp_path, "p10")
    pipelines = {"p": {"stages": [
        {"id": "a", "agent": "git", "mode": "sequential", "task": "x"},
        {"id": "b", "agent": "ideation", "mode": "sequential", "task": "y", "optional": True},
    ]}}
    original = copy.deepcopy(pipelines)
    kept, drops = filter_pipelines_by_active_set(pipelines, active, {})
    assert drops == []
    assert [s["id"] for s in kept["p"]["stages"]] == ["a"]
    assert pipelines == original  # input (shared, cached) dicts are never mutated


def test_run_pipeline_reference_to_dropped_pipeline_drops_the_parent(tmp_path):
    _, active = _active(tmp_path, "p10")
    pipelines = {
        "inner": {"stages": [{"id": "s", "agent": "ideation", "mode": "sequential", "task": "x"}]},
        "outer": {"stages": [
            {"id": "go", "agent": "git", "mode": "sequential", "task": "x"},
            {"id": "sub", "mode": "run_pipeline", "run_pipeline": "inner"},
        ]},
        "unrelated": {"stages": [{"id": "s", "agent": "git", "mode": "sequential", "task": "x"}]},
    }
    kept, drops = filter_pipelines_by_active_set(pipelines, active, {})
    assert set(kept) == {"unrelated"}
    assert [d.pipeline for d in drops] == ["inner", "outer"]
    assert drops[1] == PipelineDrop("outer", ("ideation",), ("sub",))


def test_disabled_pipeline_passes_through_without_drop(tmp_path):
    _, active = _active(tmp_path, "p10")
    pipelines = {"off": {"enabled": False, "stages": [
        {"id": "s", "agent": "ideation", "mode": "sequential", "task": "x"}]}}
    kept, drops = filter_pipelines_by_active_set(pipelines, active, {})
    assert kept == pipelines and drops == []


# --- IC-18 no. 3 / AC-47 (part): allowed_agents ⊆ ActiveSet.roles -----------------

def _plan_driven(allowed, fallback="developer"):
    return {"stages": [
        {"id": "implement", "agent": "developer", "mode": "plan-driven", "task": "x",
         "plan-driven": {"fallback_agent": fallback, "allowed_agents": allowed}},
    ]}


def test_p10_allowed_agents_only_contain_active_roles(tmp_path):
    _, active = _active(tmp_path, "p10")
    allowed = ["junior-developer", "developer", "senior-developer", "frontend-component-engineer"]
    pipelines = {"impl": _plan_driven(allowed)}
    original = copy.deepcopy(pipelines)
    kept, drops = filter_pipelines_by_active_set(pipelines, active, {})
    assert drops == []
    result = kept["impl"]["stages"][0]["plan-driven"]["allowed_agents"]
    assert result == ["developer"]
    assert set(result) <= active.roles
    assert pipelines == original  # shared input untouched


def test_allowed_agents_unchanged_object_when_all_active(tmp_path):
    _, active = _active(tmp_path, "p10")
    pipelines = {"impl": _plan_driven(["developer", "tester"])}
    kept, _ = filter_pipelines_by_active_set(pipelines, active, {})
    assert kept["impl"] is pipelines["impl"]


def test_allowed_agents_never_become_an_empty_restriction(tmp_path):
    # The renderer reads [] as "no restriction" -> fall back to the fallback agent.
    _, active = _active(tmp_path, "p10")
    pipelines = {"impl": _plan_driven(["junior-developer", "senior-developer"])}
    kept, _ = filter_pipelines_by_active_set(pipelines, active, {})
    assert kept["impl"]["stages"][0]["plan-driven"]["allowed_agents"] == ["developer"]


def test_real_feature_lifecycle_allowed_agents_on_p10_with_validator_active(tmp_path):
    # feature-lifecycle is dropped on p10 (validator); with validator active the
    # real pipeline survives and its allowed_agents shrink to the active roles.
    import dataclasses

    config, active = _active(tmp_path, "p10")
    widened = dataclasses.replace(active, roles=active.roles | {"validator"})
    kept, _ = _filter(config, widened)
    stage = next(s for s in kept["feature-lifecycle"]["stages"] if s["id"] == "implement")
    assert stage["plan-driven"]["allowed_agents"] == ["developer"]
