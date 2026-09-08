"""render_auto_commit_block (issue #694): mode-aware prose, never mentions
push/tag/branch (git role's exclusive job), correctly reflects the
approved non-blocking suggest-tier behavior."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.auto_commit import render_auto_commit_block  # noqa: E402


def test_off_mode_renders_empty_string():
    assert render_auto_commit_block({"mode": "off"}) == ""


def test_suggest_mode_says_propose_not_pause():
    block = render_auto_commit_block({"mode": "suggest", "triggers": [], "secret_scan": True})
    assert "propose" in block.lower() or "vorschlag" in block.lower() or "suggest" in block.lower()
    assert "pause" not in block.lower()
    assert "wait" not in block.lower() or "do not" in block.lower()


def test_auto_mode_lists_active_triggers():
    block = render_auto_commit_block({
        "mode": "auto",
        "triggers": ["task-boundary", "context-pressure"],
        "secret_scan": True,
    })
    assert "task-boundary" in block
    assert "context-pressure" in block
    assert "per-edit" not in block  # not selected, must not be mentioned as active


def test_custom_mode_mentions_custom_script():
    block = render_auto_commit_block({
        "mode": "custom", "custom_script": "scripts/should-commit.sh", "secret_scan": True,
    })
    assert "scripts/should-commit.sh" in block


def test_custom_mode_without_script_renders_config_error_not_none():
    # The schema rejects this combination, but a hand-edited allowlist must
    # never leak the literal word "None" into the agent's instructions.
    block = render_auto_commit_block({"mode": "custom", "secret_scan": True})
    assert "None" not in block
    assert "misconfigured" in block.lower()


def test_no_mode_ever_mentions_push_tag_or_branch():
    for mode_cfg in (
        {"mode": "suggest", "triggers": [], "secret_scan": True},
        {"mode": "auto", "triggers": ["per-edit"], "secret_scan": True},
        {"mode": "custom", "custom_script": "x.sh", "secret_scan": True},
    ):
        block = render_auto_commit_block(mode_cfg).lower()
        assert "git push" not in block
        assert "git tag" not in block
