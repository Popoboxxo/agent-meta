"""Schema tests for ``activation_groups`` in ``config/role-defaults.yaml``.

SPEC ``dynamic-routing-template-slimming`` AC A2 (Task 4): exactly one explicit
default table drives the activation gates — ``se``, ``knowledge``, ``validator``
and ``developer_tiers`` — each carrying a precise ``config_predicate``
(``config_flag`` with ``path`` or ``roles_membership`` with ``mode`` + ``roles``).

The tests read the REAL repo config (not a fixture copy) so a missing or
mis-shaped group fails here instead of silently defaulting at sync time.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lib.roles import load_roles_config, resolve_activation_gates

REPO_ROOT = Path(__file__).resolve().parents[1]

_EXPECTED_GROUPS = {"se", "knowledge", "validator", "developer_tiers"}
_VALID_KINDS = {"config_flag", "roles_membership"}


def _groups() -> dict:
    return load_roles_config(REPO_ROOT)["activation_groups"]


def test_activation_groups_is_a_top_level_sibling_of_roles():
    config = load_roles_config(REPO_ROOT)
    assert "roles" in config
    assert "activation_groups" in config
    assert set(_groups()) == _EXPECTED_GROUPS


@pytest.mark.parametrize("group", sorted(_EXPECTED_GROUPS))
def test_activation_group_schema_shape(group: str):
    spec = _groups()[group]
    assert isinstance(spec, dict)
    assert isinstance(spec.get("default"), bool), f"{group}: default must be bool"
    assert spec["default"] is False, f"{group}: default must be the unified false"

    patterns = spec.get("role_patterns")
    assert isinstance(patterns, list) and patterns, f"{group}: role_patterns empty"
    assert all(isinstance(p, str) and p for p in patterns), f"{group}: bad pattern"

    mirror = spec.get("mirror_variable")
    assert isinstance(mirror, str) and mirror, f"{group}: mirror_variable missing"


@pytest.mark.parametrize("group", sorted(_EXPECTED_GROUPS))
def test_activation_group_config_predicate(group: str):
    predicate = _groups()[group].get("config_predicate")
    assert isinstance(predicate, dict), f"{group}: config_predicate missing"
    kind = predicate.get("kind")
    assert kind in _VALID_KINDS, f"{group}: unknown predicate kind {kind!r}"

    if kind == "config_flag":
        path = predicate.get("path")
        assert isinstance(path, str) and path, f"{group}: config_flag needs path"
    else:
        assert predicate.get("mode") in {"any", "all"}, f"{group}: bad mode"
        roles = predicate.get("roles")
        assert isinstance(roles, list) and roles, f"{group}: roles empty"
        assert all(isinstance(r, str) and r for r in roles), f"{group}: bad role"


def test_resolve_activation_gates_is_deterministic_and_covers_all_groups():
    first = resolve_activation_gates(REPO_ROOT, {})
    second = resolve_activation_gates(REPO_ROOT, {})
    assert first == second
    assert set(first) == _EXPECTED_GROUPS
    assert all(gate["enabled"] is False for gate in first.values()), (
        "empty config must fall back to the unified default:false"
    )
    # role_patterns are carried alongside enabled for root-less is_role_enabled.
    for group in _EXPECTED_GROUPS:
        assert first[group]["role_patterns"] == _groups()[group]["role_patterns"]


def test_project_config_predicate_beats_default_config_flag():
    assert resolve_activation_gates(
        REPO_ROOT, {"systems-engineering": {"enabled": True}}
    )["se"]["enabled"] is True
    assert resolve_activation_gates(
        REPO_ROOT, {"knowledge-engine": {"enabled": True}}
    )["knowledge"]["enabled"] is True


def test_project_config_predicate_beats_default_roles_membership():
    validator = resolve_activation_gates(REPO_ROOT, {"roles": ["validator"]})
    assert validator["validator"]["enabled"] is True

    tiers_all = resolve_activation_gates(
        REPO_ROOT, {"roles": ["junior-developer", "senior-developer"]}
    )
    assert tiers_all["developer_tiers"]["enabled"] is True

    tiers_partial = resolve_activation_gates(
        REPO_ROOT, {"roles": ["junior-developer"]}
    )
    assert tiers_partial["developer_tiers"]["enabled"] is False, (
        "developer_tiers uses mode: all — junior alone must not enable the group"
    )
