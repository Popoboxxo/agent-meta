"""#1157 F3-01/F3-04: the orchestrator's worker-report and worker-control contract.

Semantic checks on the BARRIER protocol (§7) and the dispatch context format
(§6), parsed as structure (numbered BARRIER steps, the fenced context block) —
both in the generic template and in the rendered Claude orchestrator.

Run: python3 -m pytest tests/test_orchestrator_worker_report_contract.py -q
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.log import SyncLog
from lib.provider_transform import transform_agent_content_for_provider
from lib.providers import load_provider_capabilities, load_providers_config
from lib.variables import strip_inactive_conditional_blocks
from tests.conftest import ALL_PROVIDERS  # noqa: E402

_TEMPLATE = (REPO_ROOT / "agents" / "1-generic" / "orchestrator.md").read_text(encoding="utf-8")
_CONFIG = {
    "agent-meta-version": "2.0.0-beta.1",
    "ai-providers": ["Claude"],
    "dod-preset": "rapid-prototyping",
    "variables": {"PROJECT_NAME": "matrix", "PROJECT_PREFIX": "mx"},
}


def _claude_render() -> str:
    """The template through the Claude provider transform (frontmatter+body)."""
    return transform_agent_content_for_provider(
        _TEMPLATE, "Claude", "orchestrator", "orchestrator", "desc",
        "1-generic/orchestrator.md@0", _CONFIG, REPO_ROOT, REPO_ROOT,
        REPO_ROOT / ".claude" / "agents" / "orchestrator.md",
        load_providers_config(REPO_ROOT), SyncLog(),
        provider_capabilities=load_provider_capabilities(REPO_ROOT),
    )


_SOURCES = {"template": lambda: _TEMPLATE, "claude-render": _claude_render}


def _section(text: str, start: str, end: str) -> str:
    return text[text.index(start):text.index(end)]


def barrier_steps(text: str) -> dict[int, str]:
    """Numbered steps of the §7 BARRIER protocol."""
    sec = _section(text, "## 7. BARRIER protocol", "## 8.")
    return {int(n): s for n, s in re.findall(r"^(\d+)\. (.+)$", sec, re.M)}


def context_format_block(text: str) -> str:
    """The fenced dispatch block under ``**Context format (mandatory):**``."""
    sec = text[text.index("**Context format (mandatory):**"):]
    return sec.split("```", 2)[1]


@pytest.mark.parametrize("source", sorted(_SOURCES))
def test_barrier_treats_missing_worker_report_as_failed(source):
    steps = barrier_steps(_SOURCES[source]())
    hits = [
        s for s in steps.values()
        if "without" in s and "report" in s and "`status: failed`" in s
    ]
    assert len(hits) == 1, steps
    rule = hits[0]
    assert "§10" in rule, "must route through the failure-recovery section"
    assert "main_chat" in rule, "after the retry budget the user must be asked"


@pytest.mark.parametrize("source", sorted(_SOURCES))
def test_dispatch_context_tells_worker_to_end_with_report(source):
    block = context_format_block(_SOURCES[source]())
    lines = [ln for ln in block.splitlines() if ln.startswith("End your run")]
    assert len(lines) == 1, block
    assert "report" in lines[0] and "final message" in lines[0]


@pytest.mark.parametrize("source", sorted(_SOURCES))
def test_worker_control_prose_uses_provider_tool_placeholder(source):
    """The gated prose names the active provider's tools via the injected
    list, never a hard-coded Claude/Codex/Gemini literal (IC-3, AC 1/2)."""
    text = _SOURCES[source]()
    sec6 = _section(text, "**Sync-Call-Vertrag", "**Context format")
    assert "explizites Polling" not in sec6
    assert "{{WORKER_CONTROL_TOOLS}}" in sec6
    sec7 = _section(text, "## 7. BARRIER protocol", "## 8.")
    assert "no separate kill signal" not in sec7
    assert "{{WORKER_CONTROL_TOOLS}}" in sec7


@pytest.mark.parametrize("source", sorted(_SOURCES))
def test_orchestrator_documents_single_async_wait_strategy(source):
    sec7 = _section(_SOURCES[source](), "## 7. BARRIER protocol", "## 8.")
    assert sec7.count("Wait strategy") == 1, sec7
    para = next(p for p in sec7.split("\n\n") if "Wait strategy" in p)
    assert "{{WORKER_CONTROL_TOOLS}}" in para and "STATUS: failed" in para and "timeout" in para
    assert "end your turn" in para and "run_in_background" in para
    assert "Monitor" not in sec7


def test_rendered_claude_orchestrator_has_control_tools():
    text = _claude_render()
    fm = yaml.safe_load(text.split("---", 2)[1])
    assert {"SendMessage", "TaskStop"} <= set(fm["tools"]), fm["tools"]


# --- SPEC-WORKER-CONTROL-CAPABILITY-2026-11-19 (Task B2, AC 1/2/3) -----------
# The worker-control prose is gated on WORKER_CONTROL_ENABLED (derived from the
# active provider's `worker_control_tools` capability, never from a hook or a
# provider-name branch). With the gate closed, no Claude tool literal may leak
# into the render (O11); the stale "(where granted)" / "hook-capable" wordings
# must be gone for every provider, including advisory-runtime ones like Codex.


def _worker_control_tools(provider: str) -> list[str]:
    """Expected tool names, read straight from the capability registry.

    Test-side oracle: independent of the syncer's variable derivation so the
    test can fail for the right reason (wrong tool names in the prose) rather
    than on a missing helper.
    """
    caps = load_provider_capabilities(REPO_ROOT)
    declared = (caps.get(provider) or {}).get("worker_control_tools") or []
    return [t for t in declared if isinstance(t, str) and t]


def _worker_control_tools_markup(provider: str) -> str:
    """The backtick list the active provider's tools render to in the prose."""
    return ", ".join(f"`{t}`" for t in _worker_control_tools(provider))


_ALL_WORKER_CONTROL_TOOLS = frozenset({
    "SendMessage", "TaskStop", "send_input", "close_agent", "wait_agent",
    "send_message",
})


def _render_with_gate(provider: str, *, worker_control: bool) -> str:
    """Full-ish render: conditional strip + tool-list substitution + transform."""
    flag = "true" if worker_control else "false"
    body = strip_inactive_conditional_blocks(
        _TEMPLATE,
        {"WORKER_CONTROL_ENABLED": flag, "PROGRESS_CHAT_PUSH_ENABLED": flag},
    )
    body = body.replace(
        "{{WORKER_CONTROL_TOOLS}}", _worker_control_tools_markup(provider)
    )
    return transform_agent_content_for_provider(
        body, provider, "orchestrator", "orchestrator", "desc",
        "1-generic/orchestrator.md@0", _CONFIG, REPO_ROOT, REPO_ROOT,
        REPO_ROOT / ".claude" / "agents" / "orchestrator.md",
        load_providers_config(REPO_ROOT), SyncLog(),
        provider_capabilities=load_provider_capabilities(REPO_ROOT),
    )


def _worker_control_prose(text: str) -> str:
    """The two prose regions that carry worker-control instructions (§6 + §7)."""
    return "\n".join([
        _section(text, "**Sync-Call-Vertrag", "**Context format"),
        _section(text, "## 7. BARRIER protocol", "## 8."),
    ])


def test_no_where_granted_wording():
    assert "(where granted)" not in _TEMPLATE


def test_no_hook_capable_provider_wording():
    assert "hook-capable provider" not in _TEMPLATE


def test_worker_control_sentences_are_gated_on_flag():
    template_prose = _worker_control_prose(_TEMPLATE)
    assert "{{#if WORKER_CONTROL_ENABLED}}" in template_prose
    assert "{{/if}}" in template_prose


@pytest.mark.parametrize("provider", ["Claude", "Codex", "Gemini"])
def test_claude_tool_literals_vanish_when_worker_control_disabled(provider):
    """O11: closed gate -> no SendMessage/TaskStop literal in the render."""
    prose = _worker_control_prose(_render_with_gate(provider, worker_control=False))
    assert "SendMessage" not in prose, prose
    assert "TaskStop" not in prose, prose


def test_tool_mentions_subset_of_active_provider_frontmatter():
    """AC 1/2: prose tool names ⊆ the active provider's FM tools, gated."""
    # Structural half (AC 3): the prose must actually be gated.
    assert "{{#if WORKER_CONTROL_ENABLED}}" in _worker_control_prose(_TEMPLATE)
    # Semantic half (AC 1): with the gate open on Claude, every worker-control
    # tool name named in the prose is granted in the frontmatter.
    text = _render_with_gate("Claude", worker_control=True)
    fm = yaml.safe_load(text.split("---", 2)[1])
    mentioned = {t for t in ("SendMessage", "TaskStop") if t in _worker_control_prose(text)}
    assert mentioned, "gated worker-control prose must name its tools"
    assert mentioned <= set(fm["tools"]), (mentioned, fm["tools"])


@pytest.mark.parametrize("provider", ["Claude", "Codex", "Gemini"])
def test_worker_control_prose_names_only_active_provider_tools(provider):
    """AC 1/2: gated prose names exactly the active provider's tool names —
    never a foreign provider's Claude/Codex/Gemini literal."""
    expected = set(_worker_control_tools(provider))
    prose = _worker_control_prose(_render_with_gate(provider, worker_control=True))
    mentioned = {t for t in _ALL_WORKER_CONTROL_TOOLS if t in prose}
    assert mentioned <= expected, (provider, "forbidden", mentioned - expected, prose)
    assert expected <= mentioned, (provider, "missing", expected - mentioned, prose)


# --- O15 (PR D / P11): tool-mention ⊆ frontmatter for ALL providers ---------
# The worker-control invariant above only covered Claude/Codex/Gemini. O15
# closes the 6-provider gap: for every registered provider, every tool name
# named in the rendered orchestrator prompt must be granted in that provider's
# frontmatter tools. Tool-less surfaces (Codex TOML, Copilot/Mammouth/ZCode
# `tools: skip`, Continue `tools: remove`) have no FM `tools` field — for those
# the check reduces to "no foreign tool literal leaks into the prose", which
# is the strongest claim their format can carry.

def _frontmatter_tools(provider: str, text: str) -> set[str] | None:
    """FM tools of a rendered agent, or None when the format has no tools key.

    Codex renders a native TOML document (``frontmatter-mechanism:
    codex-toml``) with no ``tools`` field; YAML-frontmatter providers expose
    ``tools`` only when their transform spec keeps it.
    """
    if provider == "Codex":
        return None
    fm = yaml.safe_load(text.split("---", 2)[1])
    return set(fm.get("tools") or [])


@pytest.mark.parametrize("provider", ALL_PROVIDERS)
def test_all_providers_tool_mentions_subset_of_frontmatter(provider):
    """O15: named worker-control tools ⊆ declared capability ⊆ FM tools.

    The rendered prose may only name the active provider's own tools, and
    wherever the provider declares a ``tools`` field each named tool must be
    granted there. Providers without a tools field are covered by the
    no-foreign-literal half alone.
    """
    text = _render_with_gate(provider, worker_control=True)
    prose = _worker_control_prose(text)
    declared = set(_worker_control_tools(provider))
    mentioned = {t for t in _ALL_WORKER_CONTROL_TOOLS if t in prose}

    # No tool literal from a foreign provider leaks into this render.
    assert mentioned <= declared, (provider, "foreign", mentioned - declared, prose)
    # An active provider actually names the tools it declares.
    assert declared <= mentioned, (provider, "missing", declared - mentioned, prose)

    fm_tools = _frontmatter_tools(provider, text)
    if fm_tools is not None:
        assert mentioned <= fm_tools, (provider, "not granted", mentioned - fm_tools, fm_tools)
