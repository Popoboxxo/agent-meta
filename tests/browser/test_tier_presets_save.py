"""Regression test for Bug 3A: tier-presets save must accept the `tiers` schema."""

from playwright.sync_api import expect


def test_edit_mappings_save_succeeds(browser_ctx):
    """Bug 3A: Save in Edit Mappings must not fail with the legacy 'mapping' error."""
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/tier-presets")
        page.wait_for_load_state("networkidle")

        page.get_by_text("Edit Mappings", exact=True).click()
        expect(page.locator("table.tier-presets-table")).to_be_visible(timeout=5000)

        save_btn = page.get_by_text("Save Configs", exact=True)
        expect(save_btn).to_be_visible(timeout=3000)
        save_btn.click()
        # Give the network round-trip and any toast animation a moment.
        page.wait_for_timeout(1500)

        # Surface any error toast text so failures are debuggable.
        error_toast = page.locator(".toast-error, .toast[data-type='error']")
        if error_toast.count() > 0 and error_toast.first.is_visible():
            text = error_toast.first.text_content() or ""
            assert "mapping" not in text.lower(), (
                f"Save still rejects 'tiers' schema with mapping-validation error: {text}"
            )
            # Any other error here is also a regression — bubble it up.
            raise AssertionError(f"Save produced an error toast: {text}")
    finally:
        page.close()


def test_edit_mappings_shows_per_provider_rows(browser_ctx):
    """Bug 3B: Edit Mappings must render at least one '↳ <provider>' override row."""
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/tier-presets")
        page.wait_for_load_state("networkidle")
        page.get_by_text("Edit Mappings", exact=True).click()
        expect(page.locator("table.tier-presets-table")).to_be_visible(timeout=5000)

        # Per-provider override rows are tagged with data-row-kind="provider".
        provider_rows = page.locator("tr[data-row-kind='provider']")
        # The admin server ships ai-providers.yaml with multiple providers, so
        # at least one per-provider row must exist for at least one preset.
        assert provider_rows.count() > 0, (
            "Edit Mappings view does not render any per-provider override rows"
        )
    finally:
        page.close()
