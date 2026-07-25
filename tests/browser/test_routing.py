"""Routing smoke tests covering the three SPA pages affected by the bug fixes."""

from playwright.sync_api import expect


def test_dashboard_loads(browser_ctx):
    """The root route must render without 404 and expose an H1 heading."""
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(base)
        expect(page.locator("h1").first).to_be_visible(timeout=5000)
    finally:
        page.close()


def test_config_audit_route(browser_ctx):
    """Bug 2: /config-audit must render its own page, not redirect to dashboard."""
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/config-audit")
        page.wait_for_load_state("networkidle")
        # The config-audit view has an H1 with "Config" in its text.
        expect(page.locator("#content h1").first).to_contain_text("Config", timeout=5000)
        # Must NOT show the dashboard's "Overview" heading.
        heading_text = page.locator("#content h1").first.text_content() or ""
        assert "Overview" not in heading_text, (
            "Config-audit route fell back to dashboard (route not registered)"
        )
    finally:
        page.close()


def test_tier_presets_edit_tab(browser_ctx):
    """Bug 3: Edit Mappings tab must be clickable and show the edit table."""
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/tier-presets")
        page.wait_for_load_state("networkidle")
        edit_btn = page.get_by_text("Edit Mappings", exact=True)
        expect(edit_btn).to_be_visible(timeout=5000)
        edit_btn.click()
        expect(page.locator("table.tier-presets-table")).to_be_visible(timeout=3000)
    finally:
        page.close()
