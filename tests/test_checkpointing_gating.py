"""``orchestrator.checkpointing`` gating (issue #743).

Before #743 the flag was a no-op: ``{{CHECKPOINTING_BLOCK}}`` was orphaned and
§9 hard-coded the checkpoint instructions unconditionally. These tests pin the
consumer-visible behavior end-to-end: ``checkpointing: true`` renders the
checkpoint/live-progress documentation, ``false`` suppresses it.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.config import build_variables  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.variables import strip_inactive_conditional_blocks, substitute  # noqa: E402


def _render_orchestrator(checkpointing: bool) -> tuple[dict, str]:
    config = {
        "project": {"name": "t", "prefix": "t"},
        "ai-providers": ["Claude"],
        "roles": ["orchestrator"],
        "orchestrator": {"checkpointing": checkpointing},
    }
    variables, _ = build_variables(config, _REPO_ROOT)
    template = (_REPO_ROOT / "agents" / "1-generic" / "orchestrator.md").read_text(encoding="utf-8")
    log = SyncLog()
    rendered = substitute(template, variables, "orchestrator.md", log)
    rendered = strip_inactive_conditional_blocks(rendered, variables)
    return variables, rendered


def test_checkpointing_true_renders_block():
    variables, rendered = _render_orchestrator(True)
    assert variables["CHECKPOINTING_ENABLED"] == "true"
    assert ".meta-viz/checkpoint-" in rendered
    assert ".meta-viz/progress/current.md" in rendered
    # The wrapper itself must be consumed, not left in the output.
    assert "{{#if CHECKPOINTING_ENABLED}}" not in rendered
    assert "{{CHECKPOINTING_BLOCK}}" not in rendered


def test_checkpointing_false_suppresses_block():
    variables, rendered = _render_orchestrator(False)
    assert variables["CHECKPOINTING_ENABLED"] == "false"
    assert ".meta-viz/checkpoint-" not in rendered
    assert ".meta-viz/progress/current.md" not in rendered
    assert "{{#if CHECKPOINTING_ENABLED}}" not in rendered
    assert "{{CHECKPOINTING_BLOCK}}" not in rendered


def test_checkpointing_block_and_control_differ():
    """Consumer-visible difference: true vs false produce different agent text."""
    _, enabled = _render_orchestrator(True)
    _, disabled = _render_orchestrator(False)
    assert enabled != disabled
