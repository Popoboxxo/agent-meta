"""AC A3 — one shared Layer-2 active set across routing, hints and table.

Routing targets, ``build_agent_hints`` rows and ``build_agent_table`` rows must
be derived from the identical Layer-2 resolution
(``resolve_active_roles(..., require_template=True)``); ``orchestrator`` is
removed from the routing targets only. Deviations are reported in ``warn_sink``
and never silently dropped.
"""
from __future__ import annotations

import re
from pathlib import Path

from scripts.lib.agents import build_agent_hints, build_agent_table
from scripts.lib.delegation_table import get_active_agents_data, get_routing_rules
from scripts.lib.roles import resolve_active_roles, resolve_template_roles

_AGENT_META_ROOT = Path(".")

_ROW_RE = re.compile(r"^\| `([^`]+)` \|", re.MULTILINE)


def _layer2(config: dict) -> list[str]:
    template_roles = resolve_template_roles(_AGENT_META_ROOT, config)
    return resolve_active_roles(
        _AGENT_META_ROOT,
        config,
        require_template=True,
        template_roles=template_roles,
    )


def test_routing_targets_are_layer2_without_orchestrator():
    config: dict = {}
    layer2 = _layer2(config)
    rules = get_routing_rules(_AGENT_META_ROOT, config, {})
    assert rules["target_agents"] == [role for role in layer2 if role != "orchestrator"]
    assert "orchestrator" not in rules["target_agents"]


def test_active_agents_data_uses_layer2_including_orchestrator():
    config: dict = {}
    data = get_active_agents_data(_AGENT_META_ROOT, config, {})
    assert [entry["name"] for entry in data] == _layer2(config)


def test_hints_and_table_rows_use_the_same_layer2_set():
    config: dict = {}
    expected = set(_layer2(config))
    hints = build_agent_hints(config, _AGENT_META_ROOT, include_table=True)
    table, _ = build_agent_table(config, _AGENT_META_ROOT)
    assert set(_ROW_RE.findall(hints)) == expected
    assert set(_ROW_RE.findall(table)) == expected


def test_active_role_without_template_is_warned_not_dropped():
    config: dict = {}
    template_roles = resolve_template_roles(_AGENT_META_ROOT, config)
    dropped = sorted(
        resolve_active_roles(
            _AGENT_META_ROOT,
            config,
            require_template=True,
            template_roles=template_roles,
        )
    )[0]
    sink: list[str] = []
    rules = get_routing_rules(
        _AGENT_META_ROOT,
        config,
        {},
        template_roles=template_roles - {dropped},
        warn_sink=sink,
    )
    assert f"active role without template: {dropped}" in sink
    assert dropped not in rules["target_agents"]


def test_template_without_role_defaults_entry_is_warned():
    config: dict = {}
    template_roles = resolve_template_roles(_AGENT_META_ROOT, config) | {"ghost-role"}
    sink: list[str] = []
    get_routing_rules(
        _AGENT_META_ROOT,
        config,
        {},
        template_roles=template_roles,
        warn_sink=sink,
    )
    assert "template without role-defaults entry: ghost-role" in sink


def test_warn_sink_is_deterministic_sorted_and_deduplicated():
    config: dict = {}
    template_roles = resolve_template_roles(_AGENT_META_ROOT, config) | {"ghost-role"}
    first: list[str] = []
    second: list[str] = []
    get_routing_rules(
        _AGENT_META_ROOT, config, {}, template_roles=template_roles, warn_sink=first
    )
    get_routing_rules(
        _AGENT_META_ROOT, config, {}, template_roles=template_roles, warn_sink=second
    )
    assert first == second
    assert first == sorted(set(first))
