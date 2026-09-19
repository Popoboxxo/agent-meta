"""Unit tests for the canonical role activation resolver (SPEC Block A, A2).

Covers the resolver foundation in ``scripts/lib/roles.py``:

- ``resolve_dotted`` — nested config lookups incl. missing-path semantics.
- ``resolve_activation_gates`` — single default table from
  ``role-defaults.yaml::activation_groups``; project config beats default.
- ``is_role_enabled`` — group gating via ``role_patterns``.
- ``resolve_template_roles`` — generatable role set (Layer 2 universe).
- ``resolve_active_roles`` — Layer 1 / Layer 2 activation sets + ``warn_sink``.

All fixtures build a throwaway ``agent_meta_root`` (config + templates) so the
tests stay independent of the live repository state (``activation_groups`` is
added to the real config in a later task).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.roles import (  # noqa: E402
    is_role_enabled,
    load_roles_config,
    resolve_activation_gates,
    resolve_active_roles,
    resolve_dotted,
    resolve_template_roles,
)

_ROLES_CONFIG = """\
roles:
  orchestrator:
    short_desc: Router
  developer:
    short_desc: Dev
  tester:
    short_desc: Tester
  se-architect:
    short_desc: SE
  knowledge-curator:
    short_desc: Knowledge
  validator:
    short_desc: Validator
  junior-developer:
    short_desc: Junior
  senior-developer:
    short_desc: Senior
  principal-developer:
    short_desc: Principal
activation_groups:
  se:
    default: false
    role_patterns: ["se-*"]
    mirror_variable: SE_ENABLED
    config_predicate:
      kind: config_flag
      path: systems-engineering.enabled
  knowledge:
    default: false
    role_patterns: ["knowledge-*"]
    mirror_variable: KNOWLEDGE_ENGINE_ENABLED
    config_predicate:
      kind: config_flag
      path: knowledge-engine.enabled
  validator:
    default: false
    role_patterns: ["validator"]
    mirror_variable: VALIDATOR_ENABLED
    config_predicate:
      kind: roles_membership
      mode: any
      roles: ["validator"]
  developer_tiers:
    default: false
    role_patterns: ["junior-developer", "senior-developer", "principal-developer"]
    mirror_variable: DEVELOPER_TIERS_ENABLED
    config_predicate:
      kind: roles_membership
      mode: all
      roles: ["junior-developer", "senior-developer"]
  optional:
    default: true
    role_patterns: ["optional-role"]
    config_predicate:
      kind: config_flag
      path: optional.enabled
"""

_TEMPLATED_ROLES = {
    "orchestrator",
    "developer",
    "tester",
    "se-architect",
    "validator",
    "junior-developer",
    "senior-developer",
    "principal-developer",
}


@pytest.fixture()
def agent_meta_root(tmp_path: Path) -> Path:
    """Throwaway agent-meta root with fixture config and templates."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "role-defaults.yaml").write_text(_ROLES_CONFIG, encoding="utf-8")

    generic_dir = tmp_path / "agents" / "1-generic"
    generic_dir.mkdir(parents=True)
    for role in _TEMPLATED_ROLES:
        (generic_dir / f"{role}.md").write_text(
            f"---\nname: {role}\nhint: {role} hint\n---\nbody\n", encoding="utf-8"
        )
    # Excluded by convention: underscore-prefixed reference + wrapper template.
    (generic_dir / "_reference-agent.md").write_text("---\nname: ref\n---\n", encoding="utf-8")
    (generic_dir / "provider-expert.md").write_text("---\nname: pe\n---\n", encoding="utf-8")
    return tmp_path


# --------------------------------------------------------------------------
# resolve_dotted
# --------------------------------------------------------------------------

def test_resolve_dotted_walks_nested_mappings():
    assert resolve_dotted({"a": {"b": {"c": 1}}}, "a.b.c") == 1
    assert resolve_dotted({"a": {"b": False}}, "a.b") is False
    assert resolve_dotted({"a": {"b": 0}}, "a.b") == 0


def test_resolve_dotted_missing_path_returns_none():
    assert resolve_dotted({}, "a.b") is None
    assert resolve_dotted({"a": 1}, "a.b") is None
    assert resolve_dotted({"a": {}}, "a.b") is None


# --------------------------------------------------------------------------
# resolve_activation_gates
# --------------------------------------------------------------------------

def test_gates_config_flag_missing_path_falls_back_to_default(agent_meta_root: Path):
    gates = resolve_activation_gates(agent_meta_root, {})
    assert gates["se"]["enabled"] is False
    assert gates["knowledge"]["enabled"] is False
    # default: true group with no project value stays enabled
    assert gates["optional"]["enabled"] is True


def test_gates_project_config_beats_default(agent_meta_root: Path):
    gates = resolve_activation_gates(agent_meta_root, {"optional": {"enabled": False}})
    assert gates["optional"]["enabled"] is False

    gates = resolve_activation_gates(
        agent_meta_root, {"systems-engineering": {"enabled": True}}
    )
    assert gates["se"]["enabled"] is True


def test_gates_roles_membership_any(agent_meta_root: Path):
    assert resolve_activation_gates(agent_meta_root, {})["validator"]["enabled"] is False
    assert (
        resolve_activation_gates(agent_meta_root, {"roles": ["validator"]})["validator"][
            "enabled"
        ]
        is True
    )
    assert (
        resolve_activation_gates(agent_meta_root, {"roles": ["developer"]})["validator"][
            "enabled"
        ]
        is False
    )


def test_gates_roles_membership_all(agent_meta_root: Path):
    both = {"roles": ["junior-developer", "senior-developer"]}
    assert resolve_activation_gates(agent_meta_root, both)["developer_tiers"]["enabled"] is True
    assert (
        resolve_activation_gates(agent_meta_root, {"roles": ["junior-developer"]})[
            "developer_tiers"
        ]["enabled"]
        is False
    )
    # principal-developer alone cannot satisfy the all-predicate
    assert (
        resolve_activation_gates(agent_meta_root, {"roles": ["principal-developer"]})[
            "developer_tiers"
        ]["enabled"]
        is False
    )


def test_gates_carry_group_role_patterns(agent_meta_root: Path):
    gates = resolve_activation_gates(agent_meta_root, {})
    assert gates["se"]["role_patterns"] == ["se-*"]
    assert gates["developer_tiers"]["role_patterns"] == [
        "junior-developer",
        "senior-developer",
        "principal-developer",
    ]


def test_gates_are_deterministic(agent_meta_root: Path):
    first = resolve_activation_gates(agent_meta_root, {"roles": ["validator"]})
    second = resolve_activation_gates(agent_meta_root, {"roles": ["validator"]})
    assert first == second
    assert list(first) == sorted(first)


# --------------------------------------------------------------------------
# is_role_enabled
# --------------------------------------------------------------------------

def test_is_role_enabled_gates_grouped_roles(agent_meta_root: Path):
    disabled = resolve_activation_gates(agent_meta_root, {})
    assert is_role_enabled("se-architect", {}, disabled) is False
    assert is_role_enabled("knowledge-curator", {}, disabled) is False
    assert is_role_enabled("validator", {}, disabled) is False

    enabled = resolve_activation_gates(
        agent_meta_root, {"systems-engineering": {"enabled": True}}
    )
    assert is_role_enabled("se-architect", {}, enabled) is True


def test_is_role_enabled_ungrouped_role_is_always_true(agent_meta_root: Path):
    gates = resolve_activation_gates(agent_meta_root, {})
    assert is_role_enabled("developer", {}, gates) is True
    assert is_role_enabled("orchestrator", {}, gates) is True


# --------------------------------------------------------------------------
# resolve_template_roles
# --------------------------------------------------------------------------

def test_resolve_template_roles_returns_generatable_set(agent_meta_root: Path):
    assert resolve_template_roles(agent_meta_root, {}) == _TEMPLATED_ROLES


def test_resolve_template_roles_is_idempotent(agent_meta_root: Path):
    first = resolve_template_roles(agent_meta_root, {})
    second = resolve_template_roles(agent_meta_root, {})
    assert first == second


# --------------------------------------------------------------------------
# resolve_active_roles — Layer 1
# --------------------------------------------------------------------------

def test_layer1_applies_gates_and_whitelist_without_value_error(agent_meta_root: Path):
    config = {"roles": ["developer", "tester", "se-architect"]}
    active = resolve_active_roles(agent_meta_root, config)
    # se-architect is whitelisted but its group default is false
    assert active == ["developer", "tester"]


def test_layer1_includes_roles_without_template(agent_meta_root: Path):
    config = {"knowledge-engine": {"enabled": True}}
    active = resolve_active_roles(agent_meta_root, config)
    assert "knowledge-curator" in active
    assert "developer" in active


# --------------------------------------------------------------------------
# resolve_active_roles — Layer 2 + lazy template resolution
# --------------------------------------------------------------------------

def test_layer2_intersects_explicit_template_roles(agent_meta_root: Path):
    config = {"knowledge-engine": {"enabled": True}}
    active = resolve_active_roles(
        agent_meta_root,
        config,
        require_template=True,
        template_roles={"developer", "knowledge-curator"},
    )
    # knowledge-curator has no template -> dropped, developer kept
    assert active == ["developer"]


def test_layer2_template_roles_none_is_resolved_lazily(agent_meta_root: Path):
    config = {"knowledge-engine": {"enabled": True}}
    active = resolve_active_roles(agent_meta_root, config, require_template=True)
    # Layer 1 gates out se-*/validator/junior/senior/principal (defaults false);
    # knowledge-curator is active but has no template -> dropped by Layer 2.
    assert active == ["developer", "orchestrator", "tester"]
    assert "knowledge-curator" not in active


def test_layer2_is_deterministic(agent_meta_root: Path):
    config = {"roles": ["developer", "tester"]}
    first = resolve_active_roles(agent_meta_root, config, require_template=True)
    second = resolve_active_roles(agent_meta_root, config, require_template=True)
    assert first == second == ["developer", "tester"]


# --------------------------------------------------------------------------
# resolve_active_roles — warn_sink
# --------------------------------------------------------------------------

def test_warn_sink_reports_active_role_without_template(agent_meta_root: Path):
    config = {"knowledge-engine": {"enabled": True}}
    sink: list[str] = []
    resolve_active_roles(
        agent_meta_root,
        config,
        require_template=True,
        template_roles={"developer"},
        warn_sink=sink,
    )
    assert "active role without template: knowledge-curator" in sink


def test_warn_sink_reports_template_without_role_defaults_entry(agent_meta_root: Path):
    sink: list[str] = []
    resolve_active_roles(
        agent_meta_root,
        {"roles": ["developer"]},
        require_template=True,
        template_roles={"developer", "ghost-role", "provider-expert"},
        warn_sink=sink,
    )
    assert "template without role-defaults entry: ghost-role" in sink
    assert not [w for w in sink if "provider-expert" in w]


def test_warn_sink_is_sorted_and_deduplicated(agent_meta_root: Path):
    config = {"knowledge-engine": {"enabled": True}}
    sink: list[str] = []
    kwargs = {
        "require_template": True,
        "template_roles": {"developer"},
        "warn_sink": sink,
    }
    resolve_active_roles(agent_meta_root, config, **kwargs)
    resolve_active_roles(agent_meta_root, config, **kwargs)
    assert sink == sorted(set(sink))
    assert sink.count("active role without template: knowledge-curator") == 1


def test_warn_sink_none_does_not_swallow_warning(agent_meta_root: Path, capsys):
    config = {"knowledge-engine": {"enabled": True}}
    resolve_active_roles(
        agent_meta_root, config, require_template=True, template_roles={"developer"}
    )
    captured = capsys.readouterr()
    assert "active role without template: knowledge-curator" in captured.err


# --------------------------------------------------------------------------
# load_roles_config — activation_groups exposure (back-compat)
# --------------------------------------------------------------------------

def test_load_roles_config_exposes_activation_groups(agent_meta_root: Path):
    cfg = load_roles_config(agent_meta_root)
    assert "developer" in cfg["roles"]
    assert set(cfg["activation_groups"]) == {
        "se",
        "knowledge",
        "validator",
        "developer_tiers",
        "optional",
    }
