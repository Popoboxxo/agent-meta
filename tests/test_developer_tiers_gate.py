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


# --- IC-18 no. 5 / AC-48: tier chain in the rendered prose -------------------

import pytest  # noqa: E402

from tests.active_set_render import (  # noqa: E402
    REPO_ROOT,
    default_config,
    fixture_config,
    section,
    sync_config,
    tiers_on_config,
)

_TIER_ROLES = ("junior-developer", "senior-developer", "principal-developer")
_SECTION4_FIXTURE = (
    REPO_ROOT / "tests" / "fixtures" / "developer-tiers" / "orchestrator-section4-tiers-on.md"
)


@pytest.fixture(scope="module")
def tier_projects(tmp_path_factory):
    root = tmp_path_factory.mktemp("tiers")
    return {
        "off-default": sync_config(root / "off-default", default_config()),
        "off-p10": sync_config(root / "off-p10", fixture_config("p10")),
        "on": sync_config(root / "on", tiers_on_config()),
    }


def _agent(project, role: str) -> str:
    return (project / ".claude" / "agents" / f"{role}.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("name", ["off-default", "off-p10"])
def test_tiers_off_orchestrator_names_no_tier_role(tier_projects, name):
    text = _agent(tier_projects[name], "orchestrator")
    leaked = [role for role in _TIER_ROLES if role in text]
    assert leaked == [], f"{name}: orchestrator references inactive tiers {leaked}"


@pytest.mark.parametrize("name", ["off-default", "off-p10"])
def test_tiers_off_developer_names_no_tier_role(tier_projects, name):
    text = _agent(tier_projects[name], "developer")
    leaked = [tier for tier in _TIER_ROLES if tier in text]
    assert leaked == [], f"{name}/developer: references inactive tiers {leaked}"


@pytest.mark.parametrize("name", ["off-default", "off-p10"])
def test_tiers_off_planner_maps_steps_without_tier_roles(tier_projects, name):
    text = _agent(tier_projects[name], "planner")
    # Step mapping and the delegation pattern are gated; the output-guard example
    # ("e.g., `senior-developer`") is a pinned mention (OG-PASS-PLANNER golden).
    assert "(`developer`, `tester`, `requirements`, ...)" in text
    assert "Consistent with the `developer` delegation pattern" in text
    lines = [line for line in text.splitlines() if "senior-developer" in line]
    assert lines == ["  write-out to a write-capable role (e.g., `senior-developer`) via the"]


def test_tiers_off_section4_routes_to_developer(tier_projects):
    text = section(_agent(tier_projects["off-default"], "orchestrator"),
                   "## 4. Developer tier selection", "## 5. ")
    assert "`developer`" in text
    assert "ESCALATE-Card intake" in text


def test_tiers_on_section4_is_byte_identical_to_pre_change(tier_projects):
    text = section(_agent(tier_projects["on"], "orchestrator"),
                   "## 4. Developer tier selection", "## 5. ")
    assert text == _SECTION4_FIXTURE.read_text(encoding="utf-8")


def test_p10_orchestrator_names_no_inactive_concept_role(tier_projects):
    text = _agent(tier_projects["off-p10"], "orchestrator")
    for role in ("concept-specifier", "concept-reviewer", "concept-architect"):
        assert f"`{role}`" not in text, role
