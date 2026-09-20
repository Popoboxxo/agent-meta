"""Call-site contract for the ``template_roles`` / ``warn_sink`` parameters.

Builders called without explicit template roles must resolve the generatable
set lazily and never raise ``ValueError``; the parameters are passed through
the whole chain ``get_active_agents_data`` → ``get_intent_routing_table`` →
``build_routing_tool_definition`` → ``build_routing_tool_definitions_for_providers``.
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib.agents import (
    build_agent_hints,
    build_agent_table,
    build_routing_tool_definition,
    build_routing_tool_definitions_for_providers,
)
from scripts.lib.delegation_table import (
    get_active_agents_data,
    get_intent_routing_table,
    get_routing_rules,
)
from scripts.lib.roles import resolve_active_roles, resolve_template_roles

_AGENT_META_ROOT = Path(".")


def test_call_sites_resolve_lazily_without_value_error():
    assert get_routing_rules(_AGENT_META_ROOT, {}, {})["target_agents"]
    assert get_active_agents_data(_AGENT_META_ROOT, {}, {})
    assert get_intent_routing_table(_AGENT_META_ROOT, {}, {})
    assert build_agent_hints({}, _AGENT_META_ROOT)
    assert build_agent_table({}, _AGENT_META_ROOT)[0]
    assert build_routing_tool_definition(_AGENT_META_ROOT, {}, {})


def test_routing_definition_enum_matches_data_layer():
    definition = build_routing_tool_definition(_AGENT_META_ROOT, {}, {})
    enum = definition["tool"]["input_schema"]["properties"]["target_agent"]["enum"]
    assert enum == get_routing_rules(_AGENT_META_ROOT, {}, {})["target_agents"]


def test_intent_routing_table_accepts_template_roles_and_sink():
    template_roles = resolve_template_roles(_AGENT_META_ROOT, {})
    sink: list[str] = []
    table = get_intent_routing_table(
        _AGENT_META_ROOT,
        {},
        {},
        template_roles=template_roles,
        warn_sink=sink,
    )
    assert table
    assert sink == sorted(set(sink))


def test_provider_builder_passes_sink_through():
    config: dict = {}
    template_roles = resolve_template_roles(_AGENT_META_ROOT, config)
    layer2 = resolve_active_roles(
        _AGENT_META_ROOT,
        config,
        require_template=True,
        template_roles=template_roles,
    )
    dropped = sorted(layer2)[0]
    sink: list[str] = []
    rendered = build_routing_tool_definitions_for_providers(
        _AGENT_META_ROOT,
        config,
        {},
        ["Claude"],
        template_roles=template_roles - {dropped},
        warn_sink=sink,
    )
    assert f"active role without template: {dropped}" in sink
    assert "Claude" in rendered
