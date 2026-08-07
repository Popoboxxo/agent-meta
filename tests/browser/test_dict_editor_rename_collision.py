"""Regression test: the generic dict-editor (MCP server Env/Headers overrides
in Project -> MCP Servers) must reject renaming a key to one that already
exists in the same dict, instead of silently overwriting/losing the colliding
entry's value.
"""

import pytest
pytest.importorskip('playwright')
from playwright.sync_api import expect


def _row_values(rows):
    return [
        [row.locator("input").nth(0).input_value(), row.locator("input").nth(1).input_value()]
        for row in rows.all()
    ]


def test_header_rename_to_existing_key_is_rejected(browser_ctx):
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/project/mcp-overrides")
        page.wait_for_load_state("networkidle")

        panel = page.locator(".panel").filter(has=page.get_by_role("heading", name="honcho", exact=True))
        panel.get_by_role("button", name="Customize", exact=False).click()

        rows = panel.get_by_text("Headers", exact=True).locator("xpath=following-sibling::div[1]/div")
        expect(rows).to_have_count(4, timeout=3000)
        before = _row_values(rows)

        target_row = next(
            r for r in rows.all()
            if r.locator("input").nth(0).input_value() == "X-Honcho-User-Name"
        )
        key_input = target_row.locator("input").nth(0)
        key_input.fill("Authorization")
        key_input.dispatch_event("change")
        page.wait_for_timeout(300)

        after = _row_values(rows)
        assert after == before, (
            "Renaming a header key to a key that already exists must be rejected, "
            f"not silently corrupt data. before={before} after={after}"
        )
        assert key_input.input_value() == "X-Honcho-User-Name", "rejected rename must revert the input"

        error_toast = page.locator(".toast-error")
        expect(error_toast).to_be_visible(timeout=1000)
        assert "already exists" in (error_toast.text_content() or "")
    finally:
        page.close()


def test_header_rename_to_empty_key_is_rejected(browser_ctx):
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/project/mcp-overrides")
        page.wait_for_load_state("networkidle")

        panel = page.locator(".panel").filter(has=page.get_by_role("heading", name="honcho", exact=True))
        panel.get_by_role("button", name="Customize", exact=False).click()

        rows = panel.get_by_text("Headers", exact=True).locator("xpath=following-sibling::div[1]/div")
        expect(rows).to_have_count(4, timeout=3000)
        before = _row_values(rows)

        target_row = next(
            r for r in rows.all()
            if r.locator("input").nth(0).input_value() == "X-Honcho-User-Name"
        )
        key_input = target_row.locator("input").nth(0)
        key_input.fill("")
        key_input.dispatch_event("change")
        page.wait_for_timeout(300)

        after = _row_values(rows)
        assert after == before, (
            "Clearing a header's key field must be rejected (use the delete button "
            f"instead), not silently drop the row. before={before} after={after}"
        )
    finally:
        page.close()


def test_provider_option_rename_to_existing_key_is_rejected(browser_ctx):
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/project/providers")
        page.wait_for_load_state("networkidle")

        table = page.locator("table").filter(has=page.locator('input[placeholder="key"]')).first
        rows = table.locator("tr").filter(has=page.locator('input[placeholder="key"]'))
        keys_before = [rows.nth(i).locator('input[placeholder="key"]').input_value() for i in range(rows.count())]
        assert len(keys_before) >= 2, "expected at least 2 provider-option rows to test a collision"

        target_index = next(i for i, k in enumerate(keys_before) if k != keys_before[0])
        key_input = rows.nth(target_index).locator('input[placeholder="key"]')
        key_input.fill(keys_before[0])
        key_input.dispatch_event("change")
        page.wait_for_timeout(300)

        keys_after = [rows.nth(i).locator('input[placeholder="key"]').input_value() for i in range(rows.count())]
        assert keys_after == keys_before, (
            "Renaming a provider-option key to a key that already exists must be "
            f"rejected. before={keys_before} after={keys_after}"
        )

        error_toast = page.locator(".toast-error")
        expect(error_toast).to_be_visible(timeout=1000)
    finally:
        page.close()
