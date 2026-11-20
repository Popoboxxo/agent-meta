"""E-23 / PR 4.1: direct-dispatch section generated from role metadata (AC-R7).

The static ``config/direct-dispatch-section.md`` copy is removed; the section is
generated from ``routing.direct_dispatch: true`` roles and stays text-identical
to the ``templates/direct-dispatch-section.md`` golden for the same data.
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib.intent_routing import build_direct_dispatch_section

_ROOT = Path(".")


def test_generated_matches_template_golden_for_all_active_roles():
    body = build_direct_dispatch_section(
        _ROOT,
        {"git", "agent-meta-manager", "feedback", "documenter"},
    )
    template = (_ROOT / "templates" / "direct-dispatch-section.md").read_text(
        encoding="utf-8"
    )
    # The template carries {{#if}} guards; with every role active the resolved
    # body equals the generated one byte-for-byte.
    resolved = "\n".join(
        line for line in template.splitlines()
        if not line.strip().startswith("{{#if ")
        and not line.strip().startswith("{{/if")
    ).strip("\n")
    assert body.strip("\n") == resolved


def test_inactive_role_is_dropped():
    body = build_direct_dispatch_section(_ROOT, {"git"})
    assert "| Commit, Push, Branch, Tag, PR | `git` |" in body
    assert "`documenter`" not in body
