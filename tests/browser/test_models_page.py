"""Browser tests for the unified Models & Pricing page.

Covers:
- Source toggle (Registry ↔ models.dev)
- Configured provider filters (models.dev table defaults to the 4 providers
  configured in .meta-config/project.yaml → ai-providers)
- "Show all providers" toggle (lifts the configured-provider default filter)
- Registry table rendering
- models.dev table rendering with import buttons and Source provenance badges
- Curated-provider treatment (Mammouth, sourced from pricing-overlay.yaml)
- Capability filter toggles
- Legacy page
"""
import re

import pytest
from playwright.sync_api import expect

# Providers configured under `ai-providers:` in .meta-config/project.yaml —
# these are the ones the models.dev table shows by default (state.showAllProviders
# starts false). Keep in sync with that file.
CONFIGURED_PROVIDER_LABELS = ["Anthropic", "Google", "Mammouth Code", "OpenCode Go"]


def test_models_page_loads(browser_ctx, admin_server):
    """Models page renders heading and source toggle buttons."""
    ctx, url = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{url}/#/models", wait_until="networkidle")
        # Heading (use role-based locator to avoid sidebar h1)
        expect(page.get_by_role("heading", name="Models & Pricing")).to_be_visible()
        # Source toggle buttons
        expect(page.get_by_role("button", name="model-registry.json")).to_be_visible()
        expect(page.get_by_role("button", name="models.dev")).to_be_visible()
        # Default source should be "registry" — we see registry-style content
        expect(page.locator("thead")).to_contain_text("Input Cost")
        expect(page.locator("thead")).to_contain_text("Output Cost")
        expect(page.locator("thead")).to_contain_text("Cost Factor")
    finally:
        page.close()


def test_registry_table_has_data(browser_ctx, admin_server):
    """Registry table shows model rows with cost data when selected."""
    ctx, url = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{url}/#/models", wait_until="networkidle")
        page.wait_for_timeout(1000)  # let data load

        # Click registry toggle
        page.get_by_role("button", name="model-registry.json").click()
        page.wait_for_timeout(500)

        # Registry table should have rows
        tbody = page.locator("table.data tbody")
        if tbody.is_visible():
            rows = tbody.locator("tr")
            row_count = rows.count()
            assert row_count > 0, "Registry table should have model rows"
    finally:
        page.close()


def test_switch_to_models_dev(browser_ctx, admin_server):
    """Switching to models.dev source shows provider filters and model table."""
    ctx, url = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{url}/#/models", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Click models.dev toggle
        page.get_by_role("button", name="models.dev").click()
        page.wait_for_timeout(2000)  # wait for API data

        # Should show the provider quick-filter strip (the capability filters
        # are a second, nested .quick-filter-strip — scope to the first one).
        strip = page.locator(".quick-filter-strip").first
        expect(strip).to_be_visible(timeout=5000)

        # Default state is scoped to configured providers only, so the
        # "all" button reads "All Configured" (not "All Providers" — that
        # label only appears once "Show all providers" is toggled on).
        expect(page.get_by_role("button", name="All Configured")).to_be_visible()

        # Should show a table with model data
        table = page.locator("table.data")
        expect(table).to_be_visible(timeout=5000)

        # Table header should contain capabilities column
        expect(page.locator("thead")).to_contain_text("Capabilities")
    finally:
        page.close()


def test_configured_providers_in_filter_strip(browser_ctx, admin_server):
    """Configured AI providers appear prominently in the quick-filter strip,
    and the table defaults to showing only those providers' models."""
    ctx, url = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{url}/#/models", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Switch to models.dev
        page.get_by_role("button", name="models.dev").click()
        page.wait_for_timeout(2000)

        strip = page.locator(".quick-filter-strip").first
        expect(strip).to_be_visible(timeout=5000)

        # Default ("show all providers" off) — the catch-all button reads
        # "All Configured".
        all_btn = page.get_by_role("button", name="All Configured")
        expect(all_btn).to_be_visible()

        # Every provider configured in .meta-config/project.yaml (Claude/anthropic,
        # Opencode/opencode-go, Mammouth [curated], Gemini/google) has its own
        # button in the strip.
        for label in CONFIGURED_PROVIDER_LABELS:
            expect(strip.get_by_role("button", name=re.compile(re.escape(label)))).to_be_visible()

        # Without "Show all providers" there should be exactly one "all"
        # button + the 4 configured-provider buttons — no unrelated
        # providers (e.g. from the full ~150+ models.dev catalog) leak in.
        provider_buttons = strip.locator("button")
        count = provider_buttons.count()
        assert count == 5, f"Expected 'All Configured' + 4 configured providers, got {count}"

    finally:
        page.close()


def test_show_all_providers_toggle(browser_ctx, admin_server):
    """The 'Show all providers' toggle lifts the configured-provider default
    filter and exposes the full models.dev catalog."""
    ctx, url = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{url}/#/models", wait_until="networkidle")
        page.wait_for_timeout(1000)

        page.get_by_role("button", name="models.dev").click()
        page.wait_for_timeout(2000)

        strip = page.locator(".quick-filter-strip").first
        expect(strip).to_be_visible(timeout=5000)

        # Default: scoped to configured providers, small row count.
        rows = page.locator("table.data tbody tr")
        expect(rows.first).to_be_visible(timeout=5000)
        scoped_count = rows.count()

        # Flip the "Show all providers" toggle (reuses the shared .toggle slider).
        page.locator(".toggle").click()
        page.wait_for_timeout(1000)

        # The catch-all button now reads "All Providers", and an "Other
        # providers (...)" dropdown for the non-configured catalog appears.
        expect(strip.get_by_role("button", name="All Providers")).to_be_visible(timeout=5000)
        expect(strip.locator("select")).to_be_visible()

        # The full catalog has far more rows than the configured-only scope.
        expect(rows.first).to_be_visible(timeout=5000)
        full_count = rows.count()
        assert full_count > scoped_count, (
            f"Expected more rows after 'Show all providers' ({scoped_count} -> {full_count})"
        )
    finally:
        page.close()


def test_mammouth_curated_provider_treatment(browser_ctx, admin_server):
    """Mammouth has no real models.dev catalog entry — admin-server.py
    synthesizes a 'curated' provider from config/pricing-overlay.yaml. The UI
    must show it with a 'Registry (curated)' Source badge and 'No pricing' in
    the Actions cell rather than a fabricated per-token cost."""
    ctx, url = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{url}/#/models", wait_until="networkidle")
        page.wait_for_timeout(1000)

        page.get_by_role("button", name="models.dev").click()
        page.wait_for_timeout(2000)

        strip = page.locator(".quick-filter-strip").first
        expect(strip).to_be_visible(timeout=5000)

        # Filter down to the Mammouth Code provider via its strip button.
        strip.get_by_role("button", name=re.compile("Mammouth Code")).click()
        page.wait_for_timeout(500)

        rows = page.locator("table.data tbody tr")
        expect(rows.first).to_be_visible(timeout=5000)
        assert rows.count() == 1, f"Expected exactly the curated Mammouth model row, got {rows.count()}"

        row_text = rows.first.inner_text()
        assert "Registry (curated)" in row_text, f"Expected curated Source badge, got: {row_text}"
        assert "No pricing" in row_text, f"Expected 'No pricing' Actions cell, got: {row_text}"

        # No fabricated per-token cost — Input/Output cost columns render the
        # em-dash placeholder, not a synthesized number.
        cost_cells = rows.first.locator("td.mono")
        for i in range(cost_cells.count()):
            text = cost_cells.nth(i).inner_text().strip()
            assert "$" not in text, f"Did not expect a fabricated $-cost for curated Mammouth, got: {text}"
    finally:
        page.close()


def test_capability_filter_toggles(browser_ctx, admin_server):
    """Capability filter toggles are visible in models.dev mode."""
    ctx, url = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{url}/#/models", wait_until="networkidle")
        page.wait_for_timeout(1000)

        page.get_by_role("button", name="models.dev").click()
        page.wait_for_timeout(2000)

        # Capability badges should be visible
        for label in ["🧠", "🔧", "📎", "👁", "📋"]:
            badge_btn = page.locator(f"button.badge", has_text=label)
            try:
                expect(badge_btn.first).to_be_visible(timeout=2000)
                break  # at least one is visible — OK
            except AssertionError:
                continue
        else:
            # If none found with badge class, check for any button with those emojis
            for label in ["🧠", "🔧", "📎", "👁", "📋"]:
                btn = page.get_by_text(label, exact=False).first
                if btn.is_visible():
                    break
            else:
                pytest.fail("No capability filter toggle buttons found")
    finally:
        page.close()


def test_import_button_visible_on_models_dev(browser_ctx, admin_server):
    """Models in models.dev view show Import or In Registry status in the
    last (Actions / Ref) column. Import moved there when the Source
    provenance column was introduced; the column header itself is now
    "Actions / Ref", not "Import"."""
    ctx, url = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{url}/#/models", wait_until="networkidle")
        page.wait_for_timeout(1000)

        page.get_by_role("button", name="models.dev").click()
        page.wait_for_timeout(3000)

        # The table's last column header is "Actions / Ref" (Import buttons
        # / "In Registry" / "No pricing" render inside its cells).
        expect(page.locator("thead")).to_contain_text("Actions / Ref", timeout=5000)
        # A separate Source column now carries model-provenance badges.
        expect(page.locator("thead")).to_contain_text("Source", timeout=5000)

        # At least some table rows exist
        rows = page.locator("table.data tbody tr")
        expect(rows.first).to_be_visible(timeout=5000)

        # Actions column in each row should contain either "Import" button or "In Registry" badge
        first_row = rows.first
        import_cell = first_row.locator("td").last
        cell_text = import_cell.inner_text()
        assert "Import" in cell_text or "In Registry" in cell_text or "No pricing" in cell_text, \
            f"Expected 'Import', 'In Registry', or 'No pricing' in last cell, got: {cell_text}"
    finally:
        page.close()


def test_source_column_provenance_badges(browser_ctx, admin_server):
    """The Source column badges communicate model-provenance: plain
    'models.dev' for untouched entries, 'models.dev (overlay)' for entries
    whose price was overridden by config/pricing-overlay.yaml, and
    'Registry (curated)' for synthesized registry-only providers (Mammouth)."""
    ctx, url = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{url}/#/models", wait_until="networkidle")
        page.wait_for_timeout(1000)

        page.get_by_role("button", name="models.dev").click()
        page.wait_for_timeout(2000)

        rows = page.locator("table.data tbody tr")
        expect(rows.first).to_be_visible(timeout=5000)

        source_texts = set()
        for i in range(rows.count()):
            cells = rows.nth(i).locator("td")
            source_texts.add(cells.nth(cells.count() - 2).inner_text().strip())

        # Default configured-provider scope (Claude/Anthropic overlays are
        # configured in pricing-overlay.yaml) should show at least the plain
        # and curated variants.
        assert "models.dev" in source_texts, f"Expected plain 'models.dev' badge, got: {source_texts}"
        assert "models.dev (overlay)" in source_texts, f"Expected overlay-override badge, got: {source_texts}"
        assert "Registry (curated)" in source_texts, f"Expected curated badge, got: {source_texts}"
    finally:
        page.close()


def test_source_toggle_preserves_state(browser_ctx, admin_server):
    """Toggling between sources switches table content."""
    ctx, url = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{url}/#/models", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Start on registry
        page.get_by_role("button", name="model-registry.json").click()
        page.wait_for_timeout(500)
        # Registry table shows Cost Factor in text (may include whitespace)
        headers = page.locator("thead").text_content() or ""
        assert "Cost Factor" in headers, f"Expected 'Cost Factor' in thead, got: {headers[:200]}"

        # Switch to models.dev
        page.get_by_role("button", name="models.dev").click()
        page.wait_for_timeout(2000)
        # models.dev table shows Capabilities
        headers = page.locator("thead").text_content() or ""
        assert "Capabilities" in headers, f"Expected 'Capabilities' in thead, got: {headers[:200]}"

        # Switch back to registry
        page.get_by_role("button", name="model-registry.json").click()
        page.wait_for_timeout(500)
        # Registry table shows Cost Factor again
        headers = page.locator("thead").text_content() or ""
        assert "Cost Factor" in headers, f"Expected 'Cost Factor' on switch back, got: {headers[:200]}"

    finally:
        page.close()


def test_legacy_models_page(browser_ctx, admin_server):
    """Legacy page at /#/models-legacy renders with old-style content."""
    ctx, url = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{url}/#/models-legacy", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Heading indicates legacy
        expect(page.get_by_role("heading", name="Models & Pricing (Legacy)")).to_be_visible()

        # Legacy table has the old columns
        expect(page.locator("thead")).to_contain_text("Input Cost")
        expect(page.locator("thead")).to_contain_text("Output Cost")
        expect(page.locator("thead")).to_contain_text("Cost Factor")
        expect(page.locator("thead")).to_contain_text("Status")
        expect(page.locator("thead")).to_contain_text("Actions")

        # Has Refresh button
        expect(page.get_by_role("button", name="Refresh via sync.py")).to_be_visible()
    finally:
        page.close()
