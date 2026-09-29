"""AC A4 — deterministic ``name_index`` for the routing payload.

``get_routing_rules()`` returns exactly one ``name_index`` entry per
``target_agents`` role (including ``name_only`` roles) with the keys
``agent/short_desc/tier/orchestrator_only/addressability/name_only_reason``,
sorted by ``agent`` and identical across two calls over unchanged config.
``build_routing_tool_definition()`` passes it through inside ``routing``.
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib.agents import build_routing_tool_definition
from scripts.lib.delegation_table import get_routing_rules

_AGENT_META_ROOT = Path(".")

_ENTRY_KEYS = {
    "agent",
    "short_desc",
    "tier",
    "orchestrator_only",
    "addressability",
    "name_only_reason",
}


def test_name_index_has_one_entry_per_target_role_sorted():
    rules = get_routing_rules(_AGENT_META_ROOT, {}, {})
    entries = rules["name_index"]
    assert [entry["agent"] for entry in entries] == rules["target_agents"]
    assert [entry["agent"] for entry in entries] == sorted(entry["agent"] for entry in entries)


def test_name_index_entry_schema():
    rules = get_routing_rules(_AGENT_META_ROOT, {}, {})
    for entry in rules["name_index"]:
        assert set(entry) == _ENTRY_KEYS
        assert entry["addressability"] in {"keyword", "name_only"}
        assert isinstance(entry["short_desc"], str)


def test_name_only_role_is_present_but_has_no_keyword_rule():
    rules = get_routing_rules(_AGENT_META_ROOT, {}, {})
    entry = next(e for e in rules["name_index"] if e["agent"] == "intern-developer")
    assert entry["addressability"] == "name_only"
    assert entry["name_only_reason"].strip()
    assert entry["agent"] not in [rule["agent"] for rule in rules["rules"]]


def test_orchestrator_never_appears():
    rules = get_routing_rules(_AGENT_META_ROOT, {}, {})
    assert "orchestrator" not in rules["target_agents"]
    assert "orchestrator" not in [entry["agent"] for entry in rules["name_index"]]


def test_name_index_is_idempotent():
    first = get_routing_rules(_AGENT_META_ROOT, {}, {})
    second = get_routing_rules(_AGENT_META_ROOT, {}, {})
    assert first["name_index"] == second["name_index"]
    assert first == second


def test_definition_passes_name_index_through():
    definition = build_routing_tool_definition(_AGENT_META_ROOT, {}, {})
    routing = definition["routing"]
    assert routing["name_index"] == get_routing_rules(_AGENT_META_ROOT, {}, {})["name_index"]
    assert set(routing) == {"rules", "pipelines", "name_index"}
