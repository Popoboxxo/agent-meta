"""Interaction tests for issue #318: browser-driven tests for the admin-UI
project form editors that actually click, fill and save — not just render
checks.

Covers the three pages the issue calls out:
- /#/project/orchestrator   — mode dropdown, checkbox toggle, number input
- /#/project/providers      — per-provider Options KV editor (Add/edit/remove)
- /#/project/model-overrides — table editor (Add row, dropdown selects, save)

All three pages write straight to this repo's real `.meta-config/project.yaml`
via PUT /api/config/project/section, so every test captures the pre-test
state and restores + re-saves it in a `finally` block, mirroring the
seed/cleanup discipline in test_dict_editor_rename_collision.py.
"""

import pytest
pytest.importorskip('playwright')
from playwright.sync_api import expect


def test_orchestrator_mode_checkbox_and_number_roundtrip(browser_ctx):
    """User flow: open Orchestrator, flip Mode + Direct dispatch + Max depth,
    save, see it stick — then restore the original values so the test is
    non-destructive to the repo's own project.yaml."""
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/project/orchestrator")
        page.wait_for_load_state("networkidle")

        mode_select = page.locator(".field").filter(has=page.get_by_text("Mode", exact=True)).locator("select")
        expect(mode_select).to_be_visible(timeout=5000)
        dd_checkbox = page.locator(".field").filter(
            has=page.get_by_text("Direct dispatch enabled", exact=True)
        ).locator('input[type="checkbox"]')
        depth_input = page.locator('input[type="number"]').first

        original_mode = mode_select.input_value()
        original_dd = dd_checkbox.is_checked()
        original_depth = depth_input.input_value()

        new_mode = "advisory" if original_mode != "advisory" else "strict"
        new_depth = "7" if original_depth != "7" else "9"

        save_btn = page.get_by_role("button", name="Save", exact=True)

        try:
            # --- Interact: dropdown, checkbox, number input ---
            mode_select.select_option(new_mode)
            assert mode_select.input_value() == new_mode

            dd_checkbox.click()
            assert dd_checkbox.is_checked() == (not original_dd)

            depth_input.fill(new_depth)
            depth_input.dispatch_event("change")
            assert depth_input.input_value() == new_depth

            # --- Save and verify the round trip persisted server-side ---
            save_btn.click()
            expect(page.locator(".toast-error")).to_have_count(0, timeout=2000)

            page.reload()
            page.wait_for_load_state("networkidle")
            mode_select = page.locator(".field").filter(has=page.get_by_text("Mode", exact=True)).locator("select")
            dd_checkbox = page.locator(".field").filter(
                has=page.get_by_text("Direct dispatch enabled", exact=True)
            ).locator('input[type="checkbox"]')
            depth_input = page.locator('input[type="number"]').first
            expect(mode_select).to_have_value(new_mode, timeout=5000)
            assert dd_checkbox.is_checked() == (not original_dd)
            assert depth_input.input_value() == new_depth
        finally:
            # --- Restore original values regardless of assertion outcome ---
            mode_select.select_option(original_mode)
            if dd_checkbox.is_checked() != original_dd:
                dd_checkbox.click()
            depth_input.fill(original_depth)
            depth_input.dispatch_event("change")
            save_btn.click()
            page.wait_for_timeout(500)
    finally:
        page.close()


def test_providers_option_add_edit_remove_roundtrip(browser_ctx):
    """User flow: on Providers & Platforms, add a new key/value row to a
    provider's Options KV editor, save, confirm it persisted, then remove
    the row via the delete-confirmation modal and save again."""
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/project/providers")
        page.wait_for_load_state("networkidle")

        add_btn = page.get_by_role("button", name="+ Add Options", exact=True).first
        expect(add_btn).to_be_visible(timeout=5000)
        rows_container = add_btn.locator("xpath=preceding-sibling::div[1]")
        before_count = rows_container.locator("> div").count()

        save_btn = page.get_by_role("button", name="Save", exact=True)
        test_key = "__e2e_test_option__"
        test_value = "e2e-value"

        try:
            # --- Add a row and fill it in ---
            add_btn.click()
            expect(rows_container.locator("> div")).to_have_count(before_count + 1)
            new_row = rows_container.locator("> div").last

            key_input = new_row.locator("input").nth(0)
            value_input = new_row.locator("input").nth(1)
            key_input.fill(test_key)
            key_input.dispatch_event("change")
            value_input.fill(test_value)

            expect(key_input).to_have_value(test_key)
            expect(value_input).to_have_value(test_value)

            # --- Save and confirm the new option persisted ---
            save_btn.click()
            expect(page.locator(".toast-error")).to_have_count(0, timeout=2000)

            page.reload()
            page.wait_for_load_state("networkidle")
            persisted_key = page.locator(f'input[value="{test_key}"]')
            expect(persisted_key).to_have_count(1, timeout=5000)
        finally:
            # --- Cleanup: remove the test row (delete confirmation modal)
            # and save again so the repo's project.yaml is left unchanged.
            persisted_key = page.locator(f'input[value="{test_key}"]')
            if persisted_key.count() > 0:
                row = persisted_key.first.locator("xpath=ancestor::div[1]")
                row.locator(".btn-danger").click()
                page.get_by_role("button", name="Delete", exact=True).click()
                page.wait_for_timeout(200)
                page.get_by_role("button", name="Save", exact=True).click()
                page.wait_for_timeout(500)
    finally:
        page.close()


def test_model_overrides_add_row_select_and_save_roundtrip(browser_ctx):
    """User flow: on Model Overrides, add a row, pick a provider + role via
    the dropdowns, type a model id, save, confirm the count/status updates —
    then remove the row and save again to leave the config unchanged."""
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/project/model-overrides")
        page.wait_for_load_state("networkidle")

        add_row_btn = page.get_by_role("button", name="Add override", exact=True)
        expect(add_row_btn).to_be_visible(timeout=5000)
        save_btn = page.get_by_role("button", name="Save", exact=True)

        rows = page.locator("table.data tbody tr")
        before_count = rows.count()

        try:
            add_row_btn.click()
            expect(rows).to_have_count(before_count + 1)
            new_row = rows.last

            prov_select = new_row.locator("select").nth(0)
            role_select = new_row.locator("select").nth(1)
            model_input = new_row.locator("input")

            prov_options = prov_select.locator("option")
            # Options are ["— select —", <tier providers...>]; pick the first
            # real provider so the row is savable.
            assert prov_options.count() > 1, "expected at least one tier-capable provider option"
            prov_value = prov_options.nth(1).get_attribute("value")
            prov_select.select_option(prov_value)

            role_options = role_select.locator("option")
            assert role_options.count() > 1, "expected at least one role option"
            role_value = role_options.nth(1).get_attribute("value")
            role_select.select_option(role_value)

            test_model = "__e2e-test-model-id__"
            model_input.fill(test_model)
            model_input.dispatch_event("change")

            assert prov_select.input_value() == prov_value
            assert role_select.input_value() == role_value
            expect(model_input).to_have_value(test_model)

            save_btn.click()
            expect(page.locator(".toast-error")).to_have_count(0, timeout=2000)

            page.reload()
            page.wait_for_load_state("networkidle")
            expect(page.locator("table.data tbody tr")).to_have_count(before_count + 1, timeout=5000)
            persisted_model = page.locator('input[value="__e2e-test-model-id__"]')
            expect(persisted_model).to_have_count(1)
        finally:
            # --- Cleanup: remove the test row and save again. ---
            persisted_model = page.locator('input[value="__e2e-test-model-id__"]')
            if persisted_model.count() > 0:
                test_row = persisted_model.first.locator("xpath=ancestor::tr")
                test_row.locator(".btn-danger").click()
                page.wait_for_timeout(200)
                save_btn = page.get_by_role("button", name="Save", exact=True)
                save_btn.click()
                page.wait_for_timeout(500)
    finally:
        page.close()
