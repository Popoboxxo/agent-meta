"""Orchestrator name-dispatch contract in the routing fallback (AC A9).

Spec ``docs/specs/2026-09-19-dynamic-routing-template-slimming.md`` AC A9:
when no callable ``route_intent`` tool is registered, §3 of the generated
orchestrator prompt must instruct the orchestrator to resolve the target by
NAME through the ``name_index`` of the generated tool definition, and must
mark ``addressability: name_only`` roles as reachable only through that
channel. The rendered ``INTENT_ROUTING_TOOLS`` payload must carry the
``name_only`` entries (prompt-text + payload assertion).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

_AGENT_META_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_AGENT_META_ROOT / "scripts"))

from lib.agent_sync import _build_provider_vars  # noqa: E402
from lib.config import build_variables, load_config  # noqa: E402
from lib.delegation_syntax import DelegationSyntaxEngine  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.providers import load_providers_config, resolve_providers  # noqa: E402
from lib.variables import strip_inactive_conditional_blocks, substitute  # noqa: E402


def _active_provider() -> str:
    """First active provider of this repo's own config (never hardcoded)."""
    config = load_config(_AGENT_META_ROOT / ".meta-config" / "project.yaml")
    provider_config = load_providers_config(_AGENT_META_ROOT)
    active_providers = resolve_providers(config, provider_config)
    assert active_providers, "no active providers resolved from this repo's config"
    return active_providers[0]


def _build_variables() -> dict:
    config = load_config(_AGENT_META_ROOT / ".meta-config" / "project.yaml")
    variables, _ = build_variables(config, _AGENT_META_ROOT, _AGENT_META_ROOT)
    return variables


def _render_section3(provider: str) -> str:
    """Render the template's §3 exactly like the sync pipeline (substitute,
    then strip inactive conditionals) so the capability branch is observable."""
    template = (
        _AGENT_META_ROOT / "agents" / "1-generic" / "orchestrator.md"
    ).read_text(encoding="utf-8")
    section = template[
        template.index("## 3. Intent routing"):
        template.index("## 4.")
    ]
    merged = _build_provider_vars({}, provider, _build_variables(), _AGENT_META_ROOT)
    rendered = substitute(section, merged, "test", SyncLog())
    return strip_inactive_conditional_blocks(rendered, merged)


def _rendered_routing_payload(provider: str) -> dict:
    """Parse the rendered ``INTENT_ROUTING_TOOLS`` payload in the provider's
    own handoff format (json vs yaml_text_block)."""
    merged = _build_provider_vars({}, provider, _build_variables(), _AGENT_META_ROOT)
    rendered = substitute(
        "before\n\n{{INTENT_ROUTING_TOOLS}}\n\nafter", merged, "test", SyncLog()
    )
    body = rendered.strip().removeprefix("before").removesuffix("after").strip()
    engine = DelegationSyntaxEngine(config_dir=_AGENT_META_ROOT / "config")
    tool_format = str(engine.get_capabilities(provider).get("handoff_format") or "")
    if tool_format == "json":
        return json.loads(body)
    if tool_format == "yaml_text_block":
        return yaml.safe_load(body)
    pytest.fail(f"{provider}: unexpected handoff_format '{tool_format}'")


def test_fallback_branch_mandates_name_index_dispatch():
    """``ROUTE_INTENT_CALLABLE=false`` (all providers today): the fallback must
    name the ``name_index`` channel and the ``name_only`` restriction, while the
    unregistered-tool mandate stays suppressed and the no-tool-invention
    sentence stays verbatim."""
    provider = _active_provider()
    engine = DelegationSyntaxEngine(config_dir=_AGENT_META_ROOT / "config")
    assert engine.has_route_intent_tool(provider) is False

    rendered = _render_section3(provider)
    assert "kein** natives `route_intent`-Tool registriert" in rendered
    assert "**Erfinde keinen Tool-Aufruf.**" in rendered
    assert "name_index" in rendered
    assert "addressability: name_only" in rendered
    assert "Rufe `route_intent` auf, BEVOR du delegierst" not in rendered
    assert "{{else}}" not in rendered
    assert "ROUTE_INTENT_CALLABLE" not in rendered


def test_intent_routing_payload_carries_name_only_entries():
    """The generated routing payload contains the ``name_only`` entries that the
    fallback contract routes through — sorted by ``agent`` and with a reason."""
    provider = _active_provider()
    parsed = _rendered_routing_payload(provider)

    name_index = parsed["routing"]["name_index"]
    assert name_index, "name_index is empty"
    assert name_index == sorted(name_index, key=lambda entry: entry["agent"])

    name_only = [entry for entry in name_index if entry["addressability"] == "name_only"]
    assert name_only, "no name_only entry in the routing payload"
    intern = next((entry for entry in name_only if entry["agent"] == "intern-developer"), None)
    assert intern is not None, "intern-developer missing from the name_only entries"
    assert intern["name_only_reason"], "name_only entry carries no name_only_reason"
