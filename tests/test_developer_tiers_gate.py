"""AC A8 — ``developer_tiers``-Gate und die ``principal-developer``-Komplemente.

Der Resolver (``resolve_activation_gates``) und die Routing-Menge
(``get_routing_rules``) müssen zwei Zustände kongruent abbilden:

- aktive Gruppe (``config["roles"]`` enthält junior + senior, ``mode: all``):
  ``principal-developer`` liegt in ``target_agents`` **und** im ``name_index``
  (``addressability: name_only`` mit Begründung), erhält aber als ``name_only``-
  Rolle keine Keyword-/Example-Regel.
- inaktive Gruppe (Default ``false``): ``principal-developer`` fehlt in beiden
  Mengen — deckungsgleich mit dem bestehenden ``principal``-Gate-Fall in
  ``tests/test_routing_tool_definitions.py::test_get_routing_rules_includes_role_metadata``.

Dieselbe Komplement-Aussage wird für ``junior-developer`` (ebenfalls in den
``role_patterns`` der Gruppe) mitgeprüft, damit das Gate beide Richtungen
explizit belegt.
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib.delegation_table import get_routing_rules
from scripts.lib.roles import resolve_activation_gates

_AGENT_META_ROOT = Path(".")

_ACTIVE_TIER_CONFIG = {
    "roles": ["junior-developer", "senior-developer", "principal-developer"]
}
_TIER_MEMBERS = ("junior-developer", "principal-developer")


def _assert_developer_tiers_state(config: dict, *, enabled: bool) -> None:
    """Assert the ``developer_tiers`` gate and its routing complement.

    ``config`` is the project config fed to both the resolver and the routing
    builder; ``enabled`` is the expected effective state of the group.
    """
    gates = resolve_activation_gates(_AGENT_META_ROOT, config)
    assert gates["developer_tiers"]["enabled"] is enabled

    rules = get_routing_rules(_AGENT_META_ROOT, config, {})
    target_agents = rules["target_agents"]
    index_agents = [entry["agent"] for entry in rules["name_index"]]

    for role in _TIER_MEMBERS:
        assert (role in target_agents) is enabled, role
        assert (role in index_agents) is enabled, role

    if not enabled:
        return

    entry = next(e for e in rules["name_index"] if e["agent"] == "principal-developer")
    assert entry["addressability"] == "name_only"
    assert entry["name_only_reason"].strip()
    assert not [r for r in rules["rules"] if r["agent"] == "principal-developer"]


def test_developer_tiers_active_includes_principal_developer_as_name_only():
    """Active group: principal is a target/name_index entry but has no rule row."""
    _assert_developer_tiers_state(_ACTIVE_TIER_CONFIG, enabled=True)


def test_developer_tiers_inactive_excludes_principal_developer():
    """Default (inactive) group: principal is absent from targets and name_index."""
    _assert_developer_tiers_state({}, enabled=False)
