"""E-23 / PR 4.1: compact routing line format is the DEFAULT (no opt-in).

The compact block must be capability/config gated through ``routing-overrides.format``
(default ``auto``), NOT through the global ``context-profile`` (W1 / E-29). ``format: json``
is the documented rollback to the legacy render (AC-R1).
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.lib.agents import build_routing_tool_definitions_for_providers
from scripts.lib.intent_routing import resolve_routing_format

_ROOT = Path(".")
_BASE_VARS: dict = {
    "SE_ENABLED": "false",
    "VALIDATOR_ENABLED": "true",
    "KNOWLEDGE_ENGINE_ENABLED": "false",
    "DEVELOPER_TIERS_ENABLED": "false",
}


def _claude(config: dict) -> str:
    return build_routing_tool_definitions_for_providers(
        _ROOT, config, dict(_BASE_VARS), providers=["Claude"]
    )["Claude"]


def test_format_auto_is_compact_with_context_profile_full():
    """Default format is compact even without the global compact profile (E-23a/e)."""
    config = {"roles": ["developer", "tester"], "context-profile": "full"}
    body = _claude(config)
    assert not body.lstrip().startswith("{"), "compact must not emit the JSON envelope"
    assert "developer|" in body
    assert config["context-profile"] == "full", "global context profile must stay untouched"


def test_format_json_is_legacy_render():
    """E-23 rollback: routing-overrides.format json restores the old envelope (AC-R1)."""
    body = _claude({"roles": ["developer"], "routing-overrides": {"format": "json"}})
    assert json.loads(body)["tool"]["name"] == "route_intent"


def test_resolve_routing_format_capability_gated():
    assert resolve_routing_format({}, "Claude", route_intent_tool=False) == "compact"
    assert resolve_routing_format({}, "Claude", route_intent_tool=True) == "json"
    assert resolve_routing_format(
        {"routing-overrides": {"format": "off"}}, "Claude", route_intent_tool=False
    ) == "off"
    assert resolve_routing_format(
        {"routing-overrides": {"format": "json"}}, "Claude", route_intent_tool=False
    ) == "json"
