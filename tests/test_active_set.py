"""IC-17 ActiveSet contract (Task 0b.1)."""
import sys
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

from lib.active_set import ActiveSet, GateDrop, active_set_variables, compute_active_set  # noqa: E402

_FIX = Path(__file__).resolve().parent / "fixtures" / "active-set"


def _compute(name, config_override=None):
    root = _FIX / name
    config = yaml.safe_load((root / ".meta-config" / "project.yaml").read_text(encoding="utf-8"))
    config.update(config_override or {})
    sink: list = []
    return compute_active_set(config, _ROOT, root, warn_sink=sink), sink


def test_p20_gate_dropped_senior_developer():
    active, sink = _compute("p20")
    assert GateDrop(
        role="senior-developer",
        group="developer_tiers",
        reason="requires all of [junior-developer, senior-developer]",
    ) in active.gate_dropped
    assert not active.has("senior-developer")
    assert any("active-set.gate-dropped" in w and "senior-developer" in w
               and "developer_tiers" in w for w in sink)


def test_p10_excludes_ac43_roles():
    active, _ = _compute("p10")
    for role in ("senior-developer", "validator", "bug-feature-analyzer",
                 "concept-specifier", "concept-reviewer", "ideation"):
        assert not active.has(role)
    assert len(active.roles) == 10
    assert active.gate_dropped == ()


def test_pall_has_no_allowlist_and_no_gate_drops():
    active, _ = _compute("pall")
    assert active.gate_dropped == ()
    assert active.has("orchestrator") and not active.has("validator")
    assert active.roles <= active.known_roles


def test_unknown_role_warns():
    active, sink = _compute("p10", {"roles": ["orchestrator", "developer", "no-such-role"]})
    assert any("active-set.unknown-role" in w and "no-such-role" in w for w in sink)
    assert not active.has("no-such-role")
    assert "no-such-role" not in active.known_roles


def test_sets_are_sorted_and_deterministic():
    active, _ = _compute("p20")
    assert list(active.gate_dropped) == sorted(active.gate_dropped, key=lambda g: (g.role, g.group))
    assert list(active.missing_template) == sorted(active.missing_template)
    variables = active_set_variables(active)
    listed = variables["ACTIVE_ROLES"].split(",")
    assert listed == sorted(listed)
    assert active_set_variables(_compute("p20")[0]) == variables


def test_role_active_variables_cover_all_known_roles():
    active, _ = _compute("p10")
    variables = active_set_variables(active)
    for role in active.known_roles:
        key = "ROLE_%s_ACTIVE" % role.upper().replace("-", "_")
        assert variables[key] == ("true" if role in active.roles else "false")
    assert variables["ROLE_ORCHESTRATOR_ACTIVE"] == "true"
    assert variables["ROLE_SENIOR_DEVELOPER_ACTIVE"] == "false"
    assert variables["PROJECT_SPECIFIC_AGENTS"] == ""


def test_routable_excludes_orchestrator_and_sources_framework():
    active, _ = _compute("p10")
    assert "orchestrator" in active.roles and "orchestrator" not in active.routable
    assert active.routable <= active.roles
    assert set(active.sources) == set(active.known_roles)
    assert set(active.sources.values()) <= {"framework", "platform", "project"}


def test_producers_map_contracts_to_active_roles():
    active, _ = _compute("p10")
    assert "orchestrator" in active.producers["task-spec-v1"]
    for roles in active.producers.values():
        assert roles <= active.roles


def test_ha_platform_roles_are_platform_sourced():
    active, _ = _compute("ha")
    assert isinstance(active, ActiveSet)
    assert active.has("orchestrator")
    assert active.sources["developer"] == "platform"


def test_has_and_all_active():
    active, _ = _compute("p10")
    assert active.all_active(["orchestrator", "developer"])
    assert not active.all_active(["orchestrator", "validator"])


def test_routable_excludes_orchestrator_in_main_chat_mode():
    active, _ = _compute("p10", {"orchestrator": {"mode": "main-chat"}})
    assert "orchestrator" not in active.routable
    assert "developer" in active.routable


def test_missing_template_has_real_content():
    for name in ("pall", "ha"):
        active, _ = _compute(name)
        assert active.missing_template, name
        assert not set(active.missing_template) & active.roles


def test_missing_template_warnings_are_not_active_set_prefixed():
    active, sink = _compute("pall")
    assert any(w.startswith("active role without template:") for w in sink)
    assert not any(w.startswith("active-set.") for w in sink)


def test_gate_reason_config_flag_variant():
    active, _ = _compute("p10", {"roles": ["orchestrator", "se-architect"]})
    drop = [d for d in active.gate_dropped if d.role == "se-architect"]
    assert drop and drop[0].group == "se"
    assert drop[0].reason == "requires systems-engineering.enabled to be enabled"
