"""Phase 0 of the admin-ui consistency plan (docs/superpowers/plans/2026-08-07-admin-ui-consistency.md):
3 isolated, live-verified visual bugs found during the 2026-08-07 audit.
"""

import pytest
pytest.importorskip('playwright')
from playwright.sync_api import expect


def test_rules_presets_matrix_heading_has_no_raw_html_entity(browser_ctx):
    """Task 1: the "Preset Matrix" summary heading must show a real em dash,
    not the literal string "&#8212;" — el() inserts text as a text node, so
    HTML entities in that position are never decoded."""
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/config/rules-presets")
        page.wait_for_load_state("networkidle")
        heading = page.get_by_text("Preset Matrix", exact=False).first
        expect(heading).to_be_visible(timeout=5000)
        text = heading.text_content() or ""
        assert "&#8212;" not in text, f"raw HTML entity leaked into heading text: {text!r}"
        assert "—" in text
    finally:
        page.close()


def test_skill_card_recommended_badge_has_no_literal_tag_suffix(browser_ctx):
    """Task 2: the "Recommended" badge on a skill card must read exactly
    "Recommended", not "Recommended Tag"."""
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/project/skills-overrides")
        page.wait_for_load_state("networkidle")
        badge = page.locator("span.badge", has_text="Recommended").first
        expect(badge).to_be_visible(timeout=5000)
        text = (badge.text_content() or "").strip()
        assert text == "Recommended", f"badge text is {text!r}, expected exactly 'Recommended'"
    finally:
        page.close()


def test_loading_indicator_uses_ellipsis_character_consistently():
    """Task 3: all "Loading" placeholders use the single ellipsis character
    (…), not three literal dots (...) — was previously split across the file
    (2 already used the character, 4 used three dots, one of those built
    dynamically as "Loading <noun>...").

    A source-level check rather than a live one: the "loading" state is
    transient and frequently resolves before Playwright observes it, which
    made an earlier version of this test pass even without the fix (false
    confidence) — the underlying admin-server responds fast enough locally
    that the loading text is rarely on screen long enough to assert against.
    """
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")
    offending = [
        line for line in source.splitlines()
        if "Loading" in line and "..." in line
    ]
    assert not offending, f"found three-dot 'Loading...' text, expected the unicode ellipsis (…): {offending}"
