"""IC-15 Nr. 5 / AC-16 (F-10): the Kimi orchestrator frontmatter carries the
subagent allowlist, Kimi tool names and ``whenToUse``.

Provider-agnostic by construction: the Kimi-specific behaviour is driven by the
``agent-transform`` block in ``config/ai-providers.yaml`` (``subagents-allowlist``
/ ``tool-name-map`` / ``rename-fields``) plus the capability key
``subagent_allowlist_required`` -- never a provider literal in ``scripts/lib``.

Run: python3 -m pytest tests/test_subagent_allowlist_frontmatter.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.active_set import compute_active_set
from lib.log import SyncLog
from lib.provider_transform import (
    _apply_tool_name_map,
    transform_agent_content_for_provider,
)
from lib.providers import load_provider_capabilities, load_providers_config

_PROVIDER = "KimiCode"
_PC = load_providers_config(REPO_ROOT)
_CAPS = load_provider_capabilities(REPO_ROOT)
_ORCHESTRATOR_TEMPLATE = (
    REPO_ROOT / "agents" / "1-generic" / "orchestrator.md"
).read_text(encoding="utf-8")

# The Kimi-native tool vocabulary (config/provider-tools.yaml + the
# ``native_agent_tools`` capability). Kept explicit: the test must fail if a
# Claude-only name (e.g. TodoWrite) leaks into the artifact.
_KIMI_TOOLS = {
    "Read", "Write", "Edit", "Grep", "Glob", "Bash", "WebSearch", "WebFetch",
    "Agent", "AgentSwarm", "TodoList",
}

_DEFAULT_CONFIG = {
    "agent-meta-version": "2.0.0-beta.1",
    "ai-providers": [_PROVIDER],
    "dod-preset": "rapid-prototyping",
    "variables": {"PROJECT_NAME": "matrix", "PROJECT_PREFIX": "mx"},
}


def _template_hint() -> str:
    fm = yaml.safe_load(_ORCHESTRATOR_TEMPLATE.split("---", 2)[1])
    return fm["hint"]


def _active():
    return compute_active_set(_DEFAULT_CONFIG, REPO_ROOT, REPO_ROOT, warn_sink=[])


def _render_orchestrator(active):
    log = SyncLog()
    out = transform_agent_content_for_provider(
        _ORCHESTRATOR_TEMPLATE, _PROVIDER, "orchestrator", "orchestrator",
        "Einstiegspunkt", "1-generic/orchestrator.md@8.5.0", _DEFAULT_CONFIG,
        REPO_ROOT, REPO_ROOT,
        REPO_ROOT / ".kimi-code" / "agents" / "orchestrator.md",
        _PC, log, active_set=active, provider_capabilities=_CAPS,
    )
    return out, log


def _frontmatter(out: str) -> dict:
    return yaml.safe_load(out.split("---", 2)[1])


def test_orchestrator_declares_subagent_allowlist_from_active_set():
    active = _active()
    fm = _frontmatter(_render_orchestrator(active)[0])
    assert "subagents" in fm, "Kimi orchestrator needs an explicit subagents allowlist"
    expected = sorted(set(active.routable) - {"orchestrator"})
    assert fm["subagents"] == expected
    assert fm["subagents"], "the allowlist must not be empty"


def test_orchestrator_tools_are_kimi_native_only():
    fm = _frontmatter(_render_orchestrator(_active())[0])
    tools = fm["tools"]
    assert "TodoList" in tools, "TodoWrite must map to the Kimi-native TodoList"
    assert "AgentSwarm" in tools, "the dispatcher needs the Kimi fan-out tool"
    assert "TodoWrite" not in tools
    unknown = [t for t in tools if t not in _KIMI_TOOLS]
    assert not unknown, f"non-Kimi tool names leaked: {unknown}"


def test_hint_becomes_when_to_use():
    fm = _frontmatter(_render_orchestrator(_active())[0])
    assert "whenToUse" in fm, "Kimi reads whenToUse, not hint"
    assert "hint" not in fm
    assert fm["whenToUse"] == _template_hint()


def test_tool_name_map_translates_todo_write():
    mapped = _apply_tool_name_map(["TodoWrite", "Agent"], {"TodoWrite": "TodoList"})
    assert mapped == ["TodoList", "Agent"]


def test_kimi_capability_and_spec_keys_are_wired():
    spec = _PC[_PROVIDER]["agent-transform"]
    assert spec["tool-name-map"].get("TodoWrite") == "TodoList"
    assert spec["rename-fields"].get("hint") == "whenToUse"
    assert spec.get("subagents-allowlist")
    assert _CAPS[_PROVIDER]["subagent_allowlist_required"] is True


def test_only_the_allowlist_provider_declares_the_dispatch_keys():
    """The render difference stays in data: no other provider gets the keys."""
    for provider, entry in _PC.items():
        spec = (entry or {}).get("agent-transform") or {}
        if provider == _PROVIDER:
            continue
        assert not spec.get("subagents-allowlist"), provider
        assert (spec.get("rename-fields") or {}).get("hint") is None, provider


# --- #1157 F3-01: orchestrator control tools (SendMessage/TaskStop) ---------
# The grant is data, not a provider branch: a provider declares the extra tools
# of its primary role under ``agent-transform.primary-role-tools`` and must
# whitelist them in config/provider-tools.yaml. Only the primary role gets them.
_CONTROL_TOOLS = {"SendMessage", "TaskStop"}


def _render(provider: str, role: str, template: str):
    log = SyncLog()
    out = transform_agent_content_for_provider(
        template, provider, role, role, "desc", f"1-generic/{role}.md@0",
        _DEFAULT_CONFIG, REPO_ROOT, REPO_ROOT,
        REPO_ROOT / ".claude" / "agents" / f"{role}.md",
        _PC, log, active_set=_active(), provider_capabilities=_CAPS,
    )
    return out, log


def test_claude_orchestrator_grants_send_message_and_task_stop():
    out, log = _render("Claude", "orchestrator", _ORCHESTRATOR_TEMPLATE)
    tools = _frontmatter(out)["tools"]
    assert _CONTROL_TOOLS <= set(tools), tools
    leaked = [w for w in log.warnings if any(t in w for t in _CONTROL_TOOLS)]
    assert not leaked, f"control tools must be whitelisted for Claude: {leaked}"


def test_claude_worker_role_gets_no_control_tools():
    developer = (REPO_ROOT / "agents" / "1-generic" / "developer.md").read_text(encoding="utf-8")
    out, _ = _render("Claude", "developer", developer)
    tools = _frontmatter(out).get("tools") or []
    assert not _CONTROL_TOOLS & set(tools), tools


def test_kimi_orchestrator_does_not_receive_claude_control_tools():
    fm = _frontmatter(_render_orchestrator(_active())[0])
    assert not _CONTROL_TOOLS & set(fm["tools"]), fm["tools"]


def test_primary_role_tools_are_whitelisted_where_declared():
    """Every declared primary-role tool is valid for its provider."""
    from lib.frontmatter import load_provider_tools_config

    tools_cfg = load_provider_tools_config(REPO_ROOT)
    declared = {
        p: (e.get("agent-transform") or {}).get("primary-role-tools")
        for p, e in _PC.items() if isinstance(e, dict)
    }
    declared = {p: t for p, t in declared.items() if t}
    assert declared.get("Claude"), "Claude must declare its orchestrator control tools"
    for provider, tools in declared.items():
        whitelist = tools_cfg.get(provider.lower()) or []
        missing = [t for t in tools if t not in whitelist]
        assert not missing, f"{provider}: {missing} not whitelisted"
