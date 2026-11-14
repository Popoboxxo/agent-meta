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
def test_worker_control_text_names_send_message_and_task_stop(source):
    text = _SOURCES[source]()
    sec6 = _section(text, "**Sync-Call-Vertrag", "**Context format")
    assert "explizites Polling" not in sec6
    assert "`SendMessage`" in sec6 and "`TaskStop`" in sec6
    sec7 = _section(text, "## 7. BARRIER protocol", "## 8.")
    assert "no separate kill signal" not in sec7
    assert "`TaskStop`" in sec7


@pytest.mark.parametrize("source", sorted(_SOURCES))
def test_orchestrator_documents_single_async_wait_strategy(source):
    sec7 = _section(_SOURCES[source](), "## 7. BARRIER protocol", "## 8.")
    assert sec7.count("Wait strategy") == 1, sec7
    para = next(p for p in sec7.split("\n\n") if "Wait strategy" in p)
    assert "`TaskStop`" in para and "STATUS: failed" in para and "timeout" in para
    assert "end your turn" in para and "run_in_background" in para
    assert "Monitor" not in sec7


def test_rendered_claude_orchestrator_has_control_tools():
    text = _claude_render()
    fm = yaml.safe_load(text.split("---", 2)[1])
    assert {"SendMessage", "TaskStop"} <= set(fm["tools"]), fm["tools"]
