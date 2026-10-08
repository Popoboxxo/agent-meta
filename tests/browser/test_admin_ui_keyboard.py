"""Keyboard operability of the admin UI core controls (SR-D-09/A1, SR-D-15/A7).

WCAG 2.1.1 (Keyboard) / 4.1.2 (Name, Role, Value): sidebar navigation, role
cards, agent-template rows and environment rows must be operable without a
mouse and expose their state programmatically.
"""

import json

import pytest
pytest.importorskip('playwright')
from playwright.sync_api import expect

IS_FOCUSED = "el => el === document.activeElement"


def _open(ctx, url):
    page = ctx.new_page()
    page.goto(url)
    page.wait_for_load_state("networkidle")
    return page


def test_sidebar_nav_reachable_by_tab_and_enter(browser_ctx):
    """Tab reaches every nav item, Enter navigates, active item has aria-current."""
    ctx, base = browser_ctx
    page = _open(ctx, base)
    try:
        items = page.locator("#nav .nav-item")
        routes = items.evaluate_all("ns => ns.map(n => n.dataset.route)")
        assert routes, "sidebar rendered no nav items"

        reached = set()
        for _ in range(len(routes) + 40):
            page.keyboard.press("Tab")
            route = page.evaluate(
                "() => { const a = document.activeElement;"
                " return a && a.classList.contains('nav-item') ? a.dataset.route : null; }"
            )
            if route is not None:
                reached.add(route)
            if reached == set(routes):
                break
        assert reached == set(routes), f"not tab-reachable: {set(routes) - reached}"

        target = page.locator('#nav .nav-item[data-route="/sync"]')
        target.focus()
        assert target.evaluate(IS_FOCUSED)
        page.keyboard.press("Enter")
        page.wait_for_function("() => location.hash === '#/sync'", timeout=5000)
        expect(target).to_have_attribute("aria-current", "page")
        assert page.locator('#nav .nav-item[aria-current="page"]').count() == 1
    finally:
        page.close()


def test_role_card_toggles_with_space_and_enter(browser_ctx):
    """A role card is a toggle button whose aria-pressed follows the state."""
    ctx, base = browser_ctx
    page = _open(ctx, f"{base}/#/roles")
    try:
        card = page.locator(".role-grid .role-card").first
        expect(card).to_be_visible(timeout=5000)
        card.focus()
        assert card.evaluate(IS_FOCUSED), "role card is not focusable"
        before = card.get_attribute("aria-pressed")
        assert before in ("true", "false")
        flipped = "false" if before == "true" else "true"

        page.keyboard.press("Space")
        expect(card).to_have_attribute("aria-pressed", flipped)
        page.keyboard.press("Enter")
        expect(card).to_have_attribute("aria-pressed", before)
    finally:
        page.close()


def test_template_row_loads_with_enter(browser_ctx):
    """A template row loads its template into the editor via the keyboard."""
    ctx, base = browser_ctx
    page = _open(ctx, f"{base}/#/agents")
    try:
        row = page.locator(".template-list .template-row").first
        expect(row).to_be_visible(timeout=5000)
        role = (row.text_content() or "").strip()
        row.focus()
        assert row.evaluate(IS_FOCUSED), "template row is not focusable"
        page.keyboard.press("Enter")
        expect(page.locator(".template-editor .muted")).to_have_text(f"Loaded {role}.md", timeout=5000)
        assert page.locator(".template-editor textarea").input_value() != ""
    finally:
        page.close()


def test_env_row_edit_button_opens_modal(browser_ctx):
    """Each env row has a button in its first cell that opens the edit modal."""
    ctx, base = browser_ctx
    page = ctx.new_page()

    def inject_env(route):
        # Read-only fixture: inject one variable into the GET response so the
        # table renders a row without touching the repo's project.yaml.
        resp = route.fetch()
        data = resp.json()
        data["environments"] = {"KBD_TEST_VAR": {"description": "kbd", "default": "x"}}
        route.fulfill(response=resp, body=json.dumps(data))

    page.route("**/api/config/project", inject_env)
    try:
        page.goto(f"{base}/#/project/environments")
        page.wait_for_load_state("networkidle")
        btn = page.locator("table.data tbody tr").first.locator("td").first.locator("button")
        expect(btn).to_be_visible(timeout=5000)
        overlay = page.locator("#modal-overlay")

        for key in ("Enter", "Space"):
            btn.focus()
            assert btn.evaluate(IS_FOCUSED)
            page.keyboard.press(key)
            expect(overlay).to_be_visible(timeout=3000)
            expect(overlay).to_contain_text("Edit: KBD_TEST_VAR")
            page.locator("#modal-close").click()
            expect(overlay).to_be_hidden()
    finally:
        page.close()
