"""Rendering + conditional stripping for the subagent-permission policy.

Covers AC-A4 (off -> empty block, no leftover marker/blank line), AC-A5
(strict vs. warn content) and M5 boolean-flag handling.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.subagent_permissions import render_subagent_permission_block  # noqa: E402
from lib.variables import (  # noqa: E402
    _subagent_permission_flags,
    strip_inactive_conditional_blocks,
    substitute,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _flags(mode: str) -> dict:
    flags = _subagent_permission_flags(mode)
    flags["SUBAGENT_PERMISSIONS_BLOCK"] = render_subagent_permission_block(mode)
    return flags


def test_off_renders_empty():
    assert render_subagent_permission_block("off") == ""


def test_warn_report_only():
    text = render_subagent_permission_block("warn")
    assert "SUBAGENT_PERMISSION_WARNING" in text
    assert "do NOT dispatch" not in text
    assert "STATUS" in text and "ARTIFACTS" in text


def test_strict_blocks_and_requires_format():
    text = render_subagent_permission_block("strict")
    assert "do NOT dispatch" in text
    assert "STATUS" in text and "RESULT" in text and "ARTIFACTS" in text
    assert "main_chat" in text


def test_rule_strict_removes_warn_block():
    source = (_REPO_ROOT / "rules" / "1-generic" / "a2a-delegation-gates.md").read_text(
        encoding="utf-8"
    )
    rendered = strip_inactive_conditional_blocks(source, _flags("strict"))
    assert "Subagent Permission Policy (strict)" in rendered
    assert "Subagent Permission Policy (warn)" not in rendered
    assert "{{#if SUBAGENT_PERMISSIONS_" not in rendered


def test_rule_warn_removes_strict_block():
    source = (_REPO_ROOT / "rules" / "1-generic" / "a2a-delegation-gates.md").read_text(
        encoding="utf-8"
    )
    rendered = strip_inactive_conditional_blocks(source, _flags("warn"))
    assert "Subagent Permission Policy (warn)" in rendered
    assert "Subagent Permission Policy (strict)" not in rendered


def test_rule_off_removes_both_blocks():
    source = (_REPO_ROOT / "rules" / "1-generic" / "a2a-delegation-gates.md").read_text(
        encoding="utf-8"
    )
    rendered = strip_inactive_conditional_blocks(source, _flags("off"))
    assert "Subagent Permission Policy" not in rendered
    assert "SUBAGENT_PERMISSIONS" not in rendered


def test_orchestrator_off_leaves_no_blank_line():
    # M8 / AC-A4: after stripping, §5 flows into §6 with exactly one blank line.
    source = (_REPO_ROOT / "agents" / "1-generic" / "orchestrator.md").read_text(
        encoding="utf-8"
    )
    rendered = strip_inactive_conditional_blocks(source, _flags("off"))
    assert "SUBAGENT_PERMISSIONS" not in rendered
    assert 'All "yes" → start. Otherwise resolve first.\n\n## 6.' in rendered


def test_orchestrator_strict_renders_block():
    source = (_REPO_ROOT / "agents" / "1-generic" / "orchestrator.md").read_text(
        encoding="utf-8"
    )
    flags = _flags("strict")
    substituted = substitute(source, flags, "orchestrator.md", None)
    rendered = strip_inactive_conditional_blocks(substituted, flags)
    assert "Subagent Permission Policy (strict)" in rendered
    assert "{{#if SUBAGENT_PERMISSIONS_ENABLED}}" not in rendered
