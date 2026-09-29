"""Browser tests for the unified Models & Pricing page.

Covers:
- Source toggle (Registry ↔ models.dev)
- Configured provider filters (models.dev table defaults to the providers
  configured in .meta-config/project.yaml → ai-providers)
- "Show all providers" toggle (lifts the configured-provider default filter)
- Registry table rendering
- models.dev table rendering with import buttons and Source provenance badges
- Curated-provider treatment (registry-only providers such as Mammouth,
  synthesized by admin-server.py from config/pricing-overlay.yaml)
- Capability filter toggles
- Legacy page

The provider roster is deliberately NOT hardcoded: the models.dev view is
scoped by whatever ``.meta-config/project.yaml`` → ``ai-providers`` declares
for the project under test, so every provider expectation below is derived
from that live contract (see :func:`provider_contract`). A hardcoded roster
would assert providers the project does not enable.
"""
import importlib.util
import json
import re
import sys
import urllib.request
from pathlib import Path

import pytest
pytest.importorskip('playwright')
from playwright.sync_api import expect


REPO_ROOT = Path(__file__).resolve().parents[2]


def _admin_server_module():
    """Load ``scripts/admin-server.py`` as a module (hyphenated filename).

    Gives the tests the server-side provider mapping constants instead of a
    second, drift-prone copy of them.
    """
    name = "am_admin_server_for_models_page_tests"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            name, REPO_ROOT / "scripts" / "admin-server.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


_API_CACHE: dict = {}


def api_json(url: str, path: str) -> dict:
    """GET a JSON route from the running admin server, cached per session."""
    key = (url, path)
    if key not in _API_CACHE:
        with urllib.request.urlopen(url + path, timeout=60) as resp:
            _API_CACHE[key] = json.loads(resp.read().decode("utf-8"))
    return _API_CACHE[key]


def provider_contract(url: str) -> dict:
    """Derive the active provider contract from the live project config.

    Mirrors what ``docs/ui/admin-ui.html`` resolves at runtime:
    ``.meta-config/project.yaml`` → ``ai-providers`` (served by
    ``/api/config/project``) mapped onto models.dev catalog ids via
    ``PROVIDER_MODELSDEV_SLUGS``, plus the ``source: "curated"`` nodes
    admin-server.py synthesizes for the registry-only providers listed in
    ``config/pricing-overlay.yaml``.

    Returns ``{"configured": [names], "providers": [{name, id, label,
    model_count}], "curated": {id: label}}``.
    """
    admin = _admin_server_module()
    project = api_json(url, "/api/config/project")
    configured = project.get("ai-providers")
    assert isinstance(configured, list) and configured, (
        f"project.yaml must configure at least one AI provider, got {configured!r}"
    )

    catalog = (api_json(url, "/api/models-dev") or {}).get("providers") or {}
    registry_only = {k.capitalize() for k in admin.ModelsService.CURATED_ONLY_PROVIDER_KEYS}

    providers = []
    for name in configured:
        pid = admin.PROVIDER_MODELSDEV_SLUGS.get(name)
        if pid is None and name in registry_only:
            pid = name.lower()
        if pid is None:
            continue  # no models.dev view -> the strip cannot offer it
        node = catalog.get(pid) or {}
        providers.append({
            "name": name,
            "id": pid,
            "label": node.get("name") or name,
            "model_count": len(node.get("models") or {}),
        })
    assert providers, (
        f"None of the configured providers {configured!r} resolve to a models.dev "
        f"catalog id (known slugs: {sorted(admin.PROVIDER_MODELSDEV_SLUGS)})"
    )

    curated = {
        pid: (node.get("name") or pid)
        for pid, node in catalog.items()
        if node.get("source") == "curated"
    }
    assert curated, (
        "Expected at least one curated provider node synthesized by "
        "admin-server.py from config/pricing-overlay.yaml"
    )
    return {"configured": configured, "providers": providers, "curated": curated}


def open_models_dev_table(page, url: str) -> None:
    """Open the Models page, switch to the models.dev source, await the strip."""
    page.goto(f"{url}/#/models", wait_until="networkidle")
    page.get_by_role("button", name="models.dev").click()
    expect(page.locator(".quick-filter-strip").first).to_be_visible(timeout=10000)


def enable_show_all_providers(page) -> None:
    """Flip the strip's "Show all providers" toggle into full-catalog mode."""
    strip = page.locator(".quick-filter-strip").first
    toggle = strip.locator(".toggle")
    if not toggle.locator("input").is_checked():
        toggle.click()
    expect(strip.get_by_role("button", name="All Providers")).to_be_visible(timeout=10000)


def select_other_provider(page, provider_id: str) -> None:
    """Pick a provider from the strip's "Other providers" dropdown.

    Providers outside ``ai-providers`` are not strip buttons; in full-catalog
    mode they move into this ``<select>``.
    """
    strip = page.locator(".quick-filter-strip").first
    sel = strip.locator("select")
    expect(sel).to_be_visible(timeout=10000)
    options = sel.locator("option")
    values = [options.nth(i).get_attribute("value") for i in range(options.count())]
    assert provider_id in values, (
        f"Provider {provider_id!r} must be reachable through the "
        "'Other providers' dropdown in full-catalog mode"
    )
    sel.select_option(provider_id)


def source_badges(page) -> set:
    """The distinct Source-column badges of the currently rendered rows."""
    rows = page.locator("table.data tbody tr")
    badges = set()
    for i in range(rows.count()):
        cells = rows.nth(i).locator("td")
        badges.add(cells.nth(cells.count() - 2).inner_text().strip())
    return badges


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
    and the table defaults to showing only those providers' models.

    The expected roster comes from the live project contract: the strip offers
    "All Configured" plus one badge per provider that ``ai-providers`` enables
    AND that has a models.dev catalog view.
    """
    ctx, url = browser_ctx
    contract = provider_contract(url)
    page = ctx.new_page()
    try:
        open_models_dev_table(page, url)

        strip = page.locator(".quick-filter-strip").first
        all_btn = page.get_by_role("button", name="All Configured")
        expect(all_btn).to_be_visible()

        for provider in contract["providers"]:
            expect(
                strip.get_by_role("button", name=re.compile(re.escape(provider["label"])))
            ).to_be_visible()

        provider_buttons = strip.locator("button")
        count = provider_buttons.count()
        expected = 1 + len(contract["providers"])
        assert count == expected, (
            f"Expected 'All Configured' + {len(contract['providers'])} configured "
            f"provider buttons for {contract['configured']!r}, got {count}: "
            f"{provider_buttons.all_inner_texts()}"
        )

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
    """Curated (registry-only) providers get a synthesized catalog node.

    admin-server.py adds a ``source: "curated"`` node for every
    ``CURATED_ONLY_PROVIDER_KEYS`` entry present in
    ``config/pricing-overlay.yaml`` (Mammouth being the canonical one). Such a
    provider is normally *not* part of ``ai-providers``, so it is not a strip
    button in the configured-provider default scope -- it only becomes
    selectable in the full-catalog ("Show all providers") mode, where it moves
    into the "Other providers" dropdown. The UI must then show it with a
    "Registry (curated)" Source badge and "No pricing" in the Actions cell
    rather than a fabricated per-token cost.
    """
    ctx, url = browser_ctx
    contract = provider_contract(url)
    page = ctx.new_page()
    try:
        open_models_dev_table(page, url)
        enable_show_all_providers(page)

        catalog = (api_json(url, "/api/models-dev") or {}).get("providers") or {}
        for pid, label in contract["curated"].items():
            select_other_provider(page, pid)

            rows = page.locator("table.data tbody tr")
            expect(rows.first).to_be_visible(timeout=5000)
            expected_rows = len((catalog[pid] or {}).get("models") or {})
            assert rows.count() == expected_rows, (
                f"Expected the {expected_rows} curated model row(s) of {label!r} "
                f"({pid}), got {rows.count()}"
            )

            row_text = rows.first.inner_text()
            assert "Registry (curated)" in row_text, f"Expected curated Source badge, got: {row_text}"
            assert "No pricing" in row_text, f"Expected 'No pricing' Actions cell, got: {row_text}"

            cost_cells = rows.first.locator("td.mono")
            for i in range(cost_cells.count()):
                text = cost_cells.nth(i).inner_text().strip()
                assert "$" not in text, (
                    f"Did not expect a fabricated $-cost for curated {label!r}, got: {text}"
                )
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
            badge_btn = page.locator("button.badge", has_text=label)
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
    "models.dev" for untouched entries, "models.dev (overlay)" for entries
    whose price was overridden by config/pricing-overlay.yaml, and
    "Registry (curated)" for synthesized registry-only providers.

    The configured-provider default scope only contains real models.dev
    providers, so the curated badge is asserted in the full-catalog scope,
    where the synthesized node is reachable.
    """
    ctx, url = browser_ctx
    contract = provider_contract(url)
    page = ctx.new_page()
    try:
        open_models_dev_table(page, url)

        rows = page.locator("table.data tbody tr")
        expect(rows.first).to_be_visible(timeout=5000)

        badges = source_badges(page)
        assert "models.dev" in badges, f"Expected plain 'models.dev' badge, got: {badges}"
        assert "models.dev (overlay)" in badges, f"Expected overlay-override badge, got: {badges}"

        enable_show_all_providers(page)
        for pid in contract["curated"]:
            select_other_provider(page, pid)
            curated_badges = source_badges(page)
            assert curated_badges == {"Registry (curated)"}, (
                f"Curated provider {pid!r} must be the only provenance in its "
                f"own scope, got: {curated_badges}"
            )
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


def test_provider_tier_overrides_datalist_has_opencode_prefixed_ids(browser_ctx, admin_server):
    """Regression: OpenCode autocomplete candidates must be registry-runnable
    ids. models.dev reports BARE ids (e.g. "kimi-k2.7-code"), but the runnable
    config id for this framework is namespaced ("opencode-go/kimi-k2.7-code")
    and sync persists tier values verbatim into the `model:` frontmatter.

    The assertion holds in BOTH server modes — online (modelsdev source with
    the prefix re-applied server-side) and offline/degraded (registry source,
    whose ids are namespaced by discovery) — so it cannot silently pass on a
    source change.
    """
    ctx, url = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{url}/#/project/provider-tier-overrides", wait_until="networkidle")
        page.wait_for_timeout(2000)

        expect(page.get_by_role("heading", name="Project — Provider Tier Overrides")).to_be_visible()

        # Per-provider datalists keyed by framework provider name.
        opencode_options = page.locator("#pto-dl-Opencode option")
        expect(opencode_options.first).to_be_attached(timeout=5000)

        values = [opencode_options.nth(i).get_attribute("value") for i in range(opencode_options.count())]
        values = [v for v in values if v]
        assert values, "OpenCode datalist must not be empty"

        prefixed = [v for v in values if v.startswith("opencode-go/")]
        assert prefixed, (
            "OpenCode datalist candidates must carry the runnable 'opencode-go/' "
            f"prefix; got: {values[:10]}"
        )

        # Regression (B1, mixed id conventions): anthropic carries bare
        # canonical ids AND prefixed OpenRouter extras — a provider-wide
        # prefix heuristic produced non-runnable 'anthropic/claude-*'
        # candidates for canonical Claude models. Claude datalist values must
        # therefore stay bare in every server mode.
        claude_options = page.locator("#pto-dl-Claude option")
        expect(claude_options.first).to_be_attached(timeout=5000)
        claude_values = [claude_options.nth(i).get_attribute("value") for i in range(claude_options.count())]
        claude_values = [v for v in claude_values if v]
        assert claude_values, "Claude datalist must not be empty"
        assert not any(v.startswith("anthropic/") for v in claude_values), (
            "Claude datalist candidates must be bare canonical ids, got: "
            f"{claude_values[:10]}"
        )

        # The other providers' datalists exist too (sanity).
        for provider in ["Mammouth"]:
            expect(page.locator(f"#pto-dl-{provider} option").first).to_be_attached(timeout=5000)
    finally:
        page.close()


def test_registry_table_survives_modelsdev_provider_override(browser_ctx, admin_server):
    """Regression: providers whose effective source is "modelsdev" must not
    wipe the registry table when the models.dev catalog is usable — their
    rows are substituted from the models.dev data (flagged via the Status
    cell), while registry-sourced providers keep their normal rows."""
    ctx, url = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{url}/#/models", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Registry table is the default view; Claude + Opencode are persisted
        # as "modelsdev" in model-source-preference, so their rows come from
        # the live catalog. The table must still render rows.
        rows = page.locator("table.data tbody tr")
        expect(rows.first).to_be_visible(timeout=5000)
        row_count = rows.count()
        assert row_count > 0, "Registry table must render rows even with modelsdev-overridden providers"
    finally:
        page.close()
