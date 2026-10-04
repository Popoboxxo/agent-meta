"""render_auto_commit_block (issue #694, authority model #767): mode x
authority matrix, never instructs a role to push/tag/branch (git role's
exclusive job), correctly reflects the approved non-blocking suggest tier."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.auto_commit import render_auto_commit_block

_AUTHORITIES = ("direct", "delegate", "notify")
_AUTO = {
    "mode": "auto",
    "triggers": ["task-boundary", "context-pressure"],
    "file_count_threshold": 5,
    "secret_scan": True,
}


def test_off_mode_renders_empty_string_for_every_authority():
    for authority in (*_AUTHORITIES, "none"):
        assert render_auto_commit_block({"mode": "off"}, authority) == ""


def test_none_authority_renders_empty_string_in_every_mode():
    for mode_cfg in (
        {"mode": "suggest", "secret_scan": True},
        {"mode": "auto", "triggers": ["per-edit"], "secret_scan": True},
        {"mode": "custom", "custom_script": "x.sh", "secret_scan": True},
    ):
        assert render_auto_commit_block(mode_cfg, "none") == ""


def test_suggest_mode_says_propose_not_pause():
    block = render_auto_commit_block({"mode": "suggest", "triggers": [], "secret_scan": True})
    assert "propose" in block.lower() or "vorschlag" in block.lower() or "suggest" in block.lower()
    assert "pause" not in block.lower()
    assert "wait" not in block.lower() or "do not" in block.lower()


def test_suggest_block_is_authority_agnostic():
    cfg = {"mode": "suggest", "triggers": [], "secret_scan": True}
    blocks = [render_auto_commit_block(cfg, a) for a in _AUTHORITIES]
    assert blocks[0] == blocks[1] == blocks[2]
    for block in blocks:
        assert "Commit directly" not in block
        assert "delegate" not in block.lower()


def test_auto_mode_lists_active_triggers():
    block = render_auto_commit_block({
        "mode": "auto",
        "triggers": ["task-boundary", "context-pressure"],
        "secret_scan": True,
    })
    assert "task-boundary" in block
    assert "context-pressure" in block
    assert "per-edit" not in block


def test_custom_mode_mentions_custom_script():
    block = render_auto_commit_block({
        "mode": "custom", "custom_script": "scripts/should-commit.sh", "secret_scan": True,
    })
    assert "scripts/should-commit.sh" in block


def test_custom_mode_without_script_renders_config_error_not_none():
    for authority in _AUTHORITIES:
        block = render_auto_commit_block({"mode": "custom", "secret_scan": True}, authority)
        assert "None" not in block
        assert "misconfigured" in block.lower()
        assert "Commit directly" not in block


# --- auto mode: direct / delegate / notify (AC4, AC5, AC6) --------------

def test_auto_direct_commits_directly():
    block = render_auto_commit_block(_AUTO, "direct")
    assert "Commit directly as soon as ANY" in block
    assert "secret scan" in block.lower()


def test_auto_delegate_delegates_to_git_at_trigger_boundary():
    block = render_auto_commit_block(_AUTO, "delegate")
    assert "delegate the commit to the `git` agent" in block
    assert "trigger boundary" in block
    assert "task-boundary" in block and "context-pressure" in block
    assert "Commit directly" not in block
    # push/tag/branch stay the git agent's job
    assert "pushing, tagging, or branch" in block


def test_auto_notify_reports_files_and_message():
    block = render_auto_commit_block(_AUTO, "notify")
    assert "changed files" in block
    assert "ready-to-use Conventional-Commits message" in block
    assert "result/report" in block
    assert "Commit directly" not in block
    assert "delegate" not in block.lower()


# --- custom mode: direct / delegate / notify (AC9) ----------------------

_CUSTOM = {"mode": "custom", "custom_script": "scripts/should-commit.sh", "secret_scan": True}


def test_custom_direct_commits_whenever_script_exits_zero():
    block = render_auto_commit_block(_CUSTOM, "direct")
    assert "Commit directly whenever" in block
    assert "scripts/should-commit.sh" in block


def test_custom_delegate_gated_on_script():
    block = render_auto_commit_block(_CUSTOM, "delegate")
    assert "scripts/should-commit.sh" in block
    assert "delegate the commit to the `git` agent" in block
    assert "Commit directly" not in block


def test_custom_notify_gated_on_script():
    block = render_auto_commit_block(_CUSTOM, "notify")
    assert "scripts/should-commit.sh" in block
    assert "changed files" in block
    assert "ready-to-use Conventional-Commits message" in block
    assert "Commit directly" not in block
    assert "delegate" not in block.lower()


def test_no_mode_ever_mentions_push_tag_or_branch():
    for authority in _AUTHORITIES:
        for mode_cfg in (
            {"mode": "suggest", "triggers": [], "secret_scan": True},
            {"mode": "auto", "triggers": ["per-edit"], "secret_scan": True},
            {"mode": "custom", "custom_script": "x.sh", "secret_scan": True},
        ):
            block = render_auto_commit_block(mode_cfg, authority).lower()
            assert "git push" not in block
            assert "git tag" not in block


# --- F1 (issue #767): the secret_scan requirement reaches every authority ---
# Direct already carried it; delegate and notify used to drop it silently.


def test_auto_delegate_forwards_secret_scan_requirement():
    block = render_auto_commit_block(_AUTO, "delegate")
    assert "secret scan" in block.lower()
    assert "Before delegating the commit" in block
    assert "blocks the commit" in block


def test_auto_notify_forwards_secret_scan_requirement_to_caller():
    block = render_auto_commit_block(_AUTO, "notify")
    assert "secret scan" in block.lower()
    assert "caller/orchestrator" in block
    assert "blocks the commit" in block


def test_custom_delegate_and_notify_forward_secret_scan_requirement():
    for authority in ("delegate", "notify"):
        block = render_auto_commit_block(_CUSTOM, authority)
        assert "secret scan" in block.lower(), authority


def test_delegate_and_notify_omit_scan_when_disabled():
    cfg = {**_AUTO, "secret_scan": False}
    for authority in ("delegate", "notify"):
        block = render_auto_commit_block(cfg, authority)
        assert "secret scan" not in block.lower(), authority
        assert "secret scanning" not in block.lower(), authority
    custom_off = {**_CUSTOM, "secret_scan": False}
    for authority in ("delegate", "notify"):
        block = render_auto_commit_block(custom_off, authority)
        assert "secret scan" not in block.lower(), authority


# --- F4 (issue #767): unknown authority must fail CLOSED, not open ----------


def test_unknown_or_none_authority_fails_closed_to_none():
    for bad in (None, "bogus", "Direct", ""):
        assert render_auto_commit_block(_AUTO, bad) == "", repr(bad)


def test_default_authority_parameter_stays_direct():
    assert "Commit directly as soon as ANY" in render_auto_commit_block(_AUTO)
