"""Structured intent-routing tool definitions (issue #264).

Covers the generation-side pipeline introduced by #264:

- ``delegation_table.get_routing_rules()`` — data layer (activation filters,
  routing_patterns resolution, orchestrator exclusion, pipeline routes).
- ``agents.build_routing_tool_definition()`` — provider-neutral tool definition.
- ``agents.render_routing_tool_definition()`` — mechanism-keyed format
  serialization (json / yaml_text_block, same value domain as the existing
  ``handoff_format`` capability key).
- ``agents.build_routing_tool_definitions_for_providers()`` — per-provider
  emission driven purely by config capability keys.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.lib.agents import (
    ROUTING_TOOL_NAME,
    build_routing_tool_definition,
    build_routing_tool_definitions_for_providers,
    render_routing_tool_definition,
)
from scripts.lib.delegation_table import get_routing_rules
from scripts.lib.roles import load_roles_config

_AGENT_META_ROOT = Path(".")

# Standard flag set used by the existing delegation-table tests: SE cascade,
# knowledge engine and developer tiers disabled → those roles stay filtered out.
_BASE_VARIABLES: dict = {
    "SE_ENABLED": "false",
    "VALIDATOR_ENABLED": "true",
    "KNOWLEDGE_ENGINE_ENABLED": "false",
    "DEVELOPER_TIERS_ENABLED": "false",
}


# ---------------------------------------------------------------------------
# Config data integrity (guards the routing_patterns migration itself)
# ---------------------------------------------------------------------------

def test_role_defaults_routing_patterns_match_intent_keywords():
    """Every role with legacy intent_keywords carries equivalent routing_patterns."""
    roles = load_roles_config(_AGENT_META_ROOT)["roles"]
    migrated = 0
    for role, info in roles.items():
        legacy = (info.get("routing") or {}).get("intent_keywords")
        if not isinstance(legacy, list) or not legacy:
            continue
        patterns = info.get("routing_patterns")
        assert isinstance(patterns, dict), f"{role}: routing_patterns missing"
        assert patterns.get("keywords") == legacy, (
            f"{role}: routing_patterns.keywords drifted from routing.intent_keywords"
        )
        assert isinstance(patterns.get("examples"), list) and patterns["examples"], (
            f"{role}: routing_patterns.examples missing"
        )
        migrated += 1
    assert migrated >= 50, "unexpectedly few routed roles — config migration lost?"


def test_roles_without_routing_stay_patternless():
    """Roles that were never keyword-routed (easter egg, no-routing) keep no patterns."""
    roles = load_roles_config(_AGENT_META_ROOT)["roles"]
    assert "routing_patterns" not in roles["intern-developer"]
    assert "routing_patterns" not in roles["orchestrator"]
    assert "routing_patterns" not in roles["openscad-developer"]
    assert "routing_patterns" not in roles["principal-developer"]


# ---------------------------------------------------------------------------
# get_routing_rules — data layer
# ---------------------------------------------------------------------------

def test_get_routing_rules_excludes_orchestrator_and_inactive_groups():
    rules = get_routing_rules(_AGENT_META_ROOT, {}, dict(_BASE_VARIABLES))
    enum = rules["target_agents"]
    assert "orchestrator" not in enum, "anti-recursion: no self-route target"
    assert not [n for n in enum if n.startswith("se-")]
    assert not [n for n in enum if n.startswith("knowledge-")]
    assert "junior-developer" not in enum
    assert "senior-developer" not in enum
    assert "principal-developer" not in enum
    assert "validator" in enum  # VALIDATOR_ENABLED=true in fixture (no whitelist)
    assert not [r["agent"] for r in rules["rules"] if r["agent"] == "orchestrator"]


def test_get_routing_rules_respects_roles_whitelist():
    config = {"roles": ["developer", "tester"]}
    rules = get_routing_rules(_AGENT_META_ROOT, config, dict(_BASE_VARIABLES))
    assert rules["target_agents"] == ["developer", "tester"]
    assert {r["agent"] for r in rules["rules"]} == {"developer", "tester"}


def test_get_routing_rules_includes_role_metadata():
    rules = get_routing_rules(_AGENT_META_ROOT, {}, dict(_BASE_VARIABLES))
    dev = next(r for r in rules["rules"] if r["agent"] == "developer")
    assert dev["tier"] == "required"
    assert dev["parallel"] is True
    assert dev["orchestrator_only"] is False
    assert dev["keywords"] == ["Bugfix", "Refactoring", "Implementierung", "Code schreiben"]
    assert dev["examples"]
    assert dev["output_contract"] == "dev-result-v1"
    assert "task-spec-v1" in dev["input_contracts"]
    triage = next(r for r in rules["rules"] if r["agent"] == "bug-feature-analyzer")
    assert triage["orchestrator_only"] is True
    # Patternless escalation role: in the enum (dispatchable through the
    # escalation gate) but without a keyword rule — matching the prose status
    # quo where principal-developer has no intent-keyword row either.
    with_tiers = get_routing_rules(
        _AGENT_META_ROOT, {}, dict(_BASE_VARIABLES, DEVELOPER_TIERS_ENABLED="true")
    )
    assert "principal-developer" in with_tiers["target_agents"]
    assert not [r for r in with_tiers["rules"] if r["agent"] == "principal-developer"]


def test_get_routing_rules_sorted_and_deterministic():
    a = get_routing_rules(_AGENT_META_ROOT, {}, dict(_BASE_VARIABLES))
    b = get_routing_rules(_AGENT_META_ROOT, {}, dict(_BASE_VARIABLES))
    assert a == b
    assert a["target_agents"] == sorted(a["target_agents"])
    rule_agents = [r["agent"] for r in a["rules"]]
    assert rule_agents == sorted(rule_agents)


def test_get_routing_rules_pipeline_routes():
    pipelines = {
        "feature-lifecycle": {"signal_keywords": ["Feature implementieren", "neues Feature"]},
        "quick-fix": {"signal_keywords": ["Bug fixen"]},
        "empty-pipeline": {"signal_keywords": []},
    }
    rules = get_routing_rules(
        _AGENT_META_ROOT, {}, dict(_BASE_VARIABLES), pipelines=pipelines
    )
    assert rules["pipelines"] == [
        {"route": "pipeline", "pipeline": "feature-lifecycle",
         "keywords": ["Feature implementieren", "neues Feature"]},
        {"route": "pipeline", "pipeline": "quick-fix", "keywords": ["Bug fixen"]},
    ]
    # Default pipelines=None keeps the artifact pipeline-free (backward compat).
    assert get_routing_rules(_AGENT_META_ROOT, {}, dict(_BASE_VARIABLES))["pipelines"] == []


def test_get_routing_rules_keyword_fallback_and_precedence(tmp_path):
    """routing_patterns.keywords wins; legacy intent_keywords is the fallback."""
    root = tmp_path
    (root / "config").mkdir()
    (root / "config" / "role-defaults.yaml").write_text(
        "roles:\n"
        "  legacy-role:\n"
        "    model: fast\n"
        "    workflow_tier: required\n"
        "    routing:\n"
        "      intent_keywords:\n"
        "      - Legacy-Keyword\n"
        "      parallel: true\n"
        "  explicit-role:\n"
        "    model: fast\n"
        "    workflow_tier: optional\n"
        "    routing:\n"
        "      intent_keywords:\n"
        "      - Legacy-Only\n"
        "    routing_patterns:\n"
        "      keywords:\n"
        "      - Explicit-Keyword\n"
        "      examples:\n"
        "      - \"Nutze den explicit-role.\"\n"
        "  patternless-role:\n"
        "    model: fast\n",
        encoding="utf-8",
    )
    variables = {k: "false" for k in _BASE_VARIABLES}
    rules = get_routing_rules(root, {}, variables)
    agents = {r["agent"]: r for r in rules["rules"]}
    assert agents["legacy-role"]["keywords"] == ["Legacy-Keyword"]
    assert agents["legacy-role"]["examples"] == []
    assert agents["explicit-role"]["keywords"] == ["Explicit-Keyword"]
    assert agents["explicit-role"]["examples"]
    assert "patternless-role" in rules["target_agents"]
    assert "patternless-role" not in agents


# ---------------------------------------------------------------------------
# build_routing_tool_definition — neutral tool definition
# ---------------------------------------------------------------------------

def test_build_routing_tool_definition_shape():
    definition = build_routing_tool_definition(
        _AGENT_META_ROOT, {}, dict(_BASE_VARIABLES)
    )
    assert definition["tool"]["name"] == ROUTING_TOOL_NAME
    schema = definition["tool"]["input_schema"]
    assert schema["required"] == ["intent", "target_agent"]
    enum = schema["properties"]["target_agent"]["enum"]
    assert enum == get_routing_rules(_AGENT_META_ROOT, {}, dict(_BASE_VARIABLES))["target_agents"]
    assert "orchestrator" not in enum
    assert definition["routing"]["rules"]
    # Deterministic/idempotent output (two calls → equal dicts).
    assert definition == build_routing_tool_definition(
        _AGENT_META_ROOT, {}, dict(_BASE_VARIABLES)
    )


def test_build_routing_tool_definition_embeds_pipelines():
    pipelines = {"quick-fix": {"signal_keywords": ["Bug fixen"]}}
    definition = build_routing_tool_definition(
        _AGENT_META_ROOT, {}, dict(_BASE_VARIABLES), pipelines=pipelines
    )
    assert definition["routing"]["pipelines"] == [
        {"route": "pipeline", "pipeline": "quick-fix", "keywords": ["Bug fixen"]}
    ]


# ---------------------------------------------------------------------------
# render_routing_tool_definition — format dispatch
# ---------------------------------------------------------------------------

def _sample_definition() -> dict:
    return build_routing_tool_definition(
        _AGENT_META_ROOT, {"roles": ["developer", "tester"]}, dict(_BASE_VARIABLES)
    )


def test_render_json_round_trip():
    definition = _sample_definition()
    rendered = render_routing_tool_definition(definition, "json")
    assert json.loads(rendered) == definition
    assert f'"name": "{ROUTING_TOOL_NAME}"' in rendered


def test_render_yaml_text_block_round_trip():
    definition = _sample_definition()
    rendered = render_routing_tool_definition(definition, "yaml_text_block")
    assert yaml.safe_load(rendered) == definition


def test_render_unknown_format_fails_closed():
    with pytest.raises(ValueError) as excinfo:
        render_routing_tool_definition(_sample_definition(), "xml_tool")
    message = str(excinfo.value)
    assert "xml_tool" in message
    assert "json" in message and "yaml_text_block" in message
    # No provider names may leak into the mechanism-key error.
    assert "Claude" not in message and "Opencode" not in message


# ---------------------------------------------------------------------------
# build_routing_tool_definitions_for_providers — config-driven emission
# ---------------------------------------------------------------------------

def test_build_for_providers_follows_handoff_format_capability():
    rendered = build_routing_tool_definitions_for_providers(
        _AGENT_META_ROOT,
        {"roles": ["developer", "tester"]},
        dict(_BASE_VARIABLES),
        providers=["Claude", "Continue", "Codex", "KimiCode"],
    )
    definition = _sample_definition()
    assert json.loads(rendered["Claude"]) == definition       # handoff_format: json
    assert json.loads(rendered["Codex"]) == definition        # handoff_format: json
    assert yaml.safe_load(rendered["Continue"]) == definition  # yaml_text_block
    assert yaml.safe_load(rendered["KimiCode"]) == definition
    # Format differences come from config only — same payload, different envelope.
    assert rendered["Claude"] != rendered["Continue"]


def test_build_for_providers_unknown_provider_fails_soft():
    """Missing capability entry → "" (PAL missing-definition semantics), not a crash."""
    rendered = build_routing_tool_definitions_for_providers(
        _AGENT_META_ROOT, {}, dict(_BASE_VARIABLES), providers=["NotAProvider"]
    )
    assert rendered == {"NotAProvider": ""}


# ---------------------------------------------------------------------------
# Placeholder wiring (orchestrator consolidation, roadmap phase 4b)
# ---------------------------------------------------------------------------

def test_build_variables_prerenders_intent_routing_tools_per_provider():
    """build_variables stores the provider-mapped prerender under
    ``_INTENT_ROUTING_TOOL_DEFS`` — the wiring source for the
    ``{{INTENT_ROUTING_TOOLS}}`` placeholder in orchestrator.md. The
    prerender covers every active provider of this repo's own config."""
    from scripts.lib.config import build_variables, load_config

    config = load_config(_AGENT_META_ROOT / ".meta-config" / "project.yaml")
    variables, unmapped = build_variables(config, _AGENT_META_ROOT, _AGENT_META_ROOT)
    assert unmapped == []
    prerender = variables["_INTENT_ROUTING_TOOL_DEFS"]
    assert prerender, "empty prerender — resolve_providers returned no provider"
    for provider, text in prerender.items():
        assert isinstance(text, str), f"{provider}: non-string prerender"
    # At least one json-format provider (Opencode is active in this config)
    # must carry a parseable route_intent definition.
    json_providers = [p for p, t in prerender.items() if t.strip().startswith("{")]
    assert json_providers, "no json-format prerender despite active json providers"
    for provider in json_providers:
        assert json.loads(prerender[provider])["tool"]["name"] == ROUTING_TOOL_NAME


def test_build_provider_vars_resolves_intent_routing_tools(tmp_path):
    """``_build_provider_vars`` resolves ``INTENT_ROUTING_TOOLS`` for the
    provider currently being synced and shadows the prerender key over the
    shared variables dict."""
    from scripts.lib.agent_sync import _build_provider_vars

    variables = {
        "_INTENT_ROUTING_TOOL_DEFS": {"Opencode": '{"name": "route_intent"}',
                                      "Gemini": '{"name": "route_intent"}'},
        "INTENT_ROUTING_TABLE": "table",
    }
    merged = _build_provider_vars({}, "Opencode", variables, tmp_path)
    assert merged["INTENT_ROUTING_TOOLS"] == '{"name": "route_intent"}'
    # The prerender key stays present but must not leak into a placeholder
    # value; other providers' entries remain for their own sync runs.
    assert merged["_INTENT_ROUTING_TOOL_DEFS"] == variables["_INTENT_ROUTING_TOOL_DEFS"]
    gemini_merged = _build_provider_vars({}, "Gemini", variables, tmp_path)
    assert gemini_merged["INTENT_ROUTING_TOOLS"] != merged["INTENT_ROUTING_TOOLS"] or \
        gemini_merged is not merged


def test_build_provider_vars_empty_without_prerender(tmp_path):
    """Missing prerender key (legacy variables dicts) → "" (fail-soft)."""
    from scripts.lib.agent_sync import _build_provider_vars

    merged = _build_provider_vars({}, "Opencode", {}, tmp_path)
    assert merged["INTENT_ROUTING_TOOLS"] == ""


def test_intent_routing_tools_placeholder_substitutes_cleanly():
    """End-to-end wiring check: the orchestrator template's
    ``{{INTENT_ROUTING_TOOLS}}`` placeholder substitutes to the rendered
    definition for a provider with handoff_format — no open placeholder and
    no missing-variable warning in the output. The parse side mirrors each
    provider's ``handoff_format`` (json vs yaml_text_block)."""
    from scripts.lib.config import build_variables, load_config
    from scripts.lib.agent_sync import _build_provider_vars
    from scripts.lib.delegation_syntax import DelegationSyntaxEngine
    from scripts.lib.variables import substitute
    from scripts.lib.log import SyncLog

    config = load_config(_AGENT_META_ROOT / ".meta-config" / "project.yaml")
    variables, _ = build_variables(config, _AGENT_META_ROOT, _AGENT_META_ROOT)
    template = (_AGENT_META_ROOT / "agents" / "1-generic" / "orchestrator.md").read_text(
        encoding="utf-8"
    )
    assert "{{INTENT_ROUTING_TOOLS}}" in template, "placeholder missing from template"
    engine = DelegationSyntaxEngine(config_dir=_AGENT_META_ROOT / "config")
    for provider in ("Opencode", "Gemini", "Mammouth"):
        tool_format = str(engine.get_capabilities(provider).get("handoff_format") or "")
        merged = _build_provider_vars({}, provider, variables, _AGENT_META_ROOT)
        log = SyncLog()
        rendered = substitute(
            "before\n\n{{INTENT_ROUTING_TOOLS}}\n\nafter", merged, "test", log
        )
        assert "INTENT_ROUTING_TOOLS" not in rendered, (
            f"{provider}: placeholder left unsubstituted"
        )
        assert rendered.strip().startswith("before")
        assert rendered.strip().endswith("after")
        # The rendered body is a parseable tool definition in this provider's
        # handoff_format (json → JSON, yaml_text_block → YAML).
        body = rendered.strip().removeprefix("before").removesuffix("after").strip()
        if tool_format == "json":
            parsed = json.loads(body)
        elif tool_format == "yaml_text_block":
            parsed = yaml.safe_load(body)
        else:  # pragma: no cover — all three fixtures carry a known format
            pytest.fail(f"{provider}: unexpected handoff_format '{tool_format}'")
        assert parsed["tool"]["name"] == ROUTING_TOOL_NAME
        assert not [w for w in log.warnings if "INTENT_ROUTING_TOOLS" in w]
