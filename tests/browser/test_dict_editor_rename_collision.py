"""Regression test: the generic dict-editor (MCP server Env/Headers overrides
in Project -> Plugin Overrides) must reject renaming a key to one that already
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
        page.goto(f"{base}/#/project/plugin-overrides")
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
        page.goto(f"{base}/#/project/plugin-overrides")
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
    """Provider Options (Task 16 of the admin-ui consistency plan) now shares
    the same renderDictEditor as MCP Env/Headers instead of its own addKVRow
    -- div rows with placeholder="Key", not a <table>/<tr> with a lowercase
    "key" placeholder."""
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/project/providers")
        page.wait_for_load_state("networkidle")

        # Each provider gets its own "Options" editor; find the first one
        # with at least 2 rows so a rename-to-existing-key collision is
        # actually possible to trigger.
        option_labels = page.get_by_text("Options", exact=True)
        rows = None
        keys_before = None
        for i in range(option_labels.count()):
            candidate_rows = option_labels.nth(i).locator("xpath=following-sibling::div[1]/div")
            candidate_keys = [
                candidate_rows.nth(j).locator('input[placeholder="Key"]').input_value()
                for j in range(candidate_rows.count())
            ]
            if len(candidate_keys) >= 2:
                rows, keys_before = candidate_rows, candidate_keys
                break
        assert keys_before is not None, "expected at least one provider with >=2 options to test a collision"

        target_index = next(i for i, k in enumerate(keys_before) if k != keys_before[0])
        key_input = rows.nth(target_index).locator('input[placeholder="Key"]')
        key_input.fill(keys_before[0])
        key_input.dispatch_event("change")
        page.wait_for_timeout(300)

        keys_after = [rows.nth(i).locator('input[placeholder="Key"]').input_value() for i in range(rows.count())]
        assert keys_after == keys_before, (
            "Renaming a provider-option key to a key that already exists must be "
            f"rejected. before={keys_before} after={keys_after}"
        )

        error_toast = page.locator(".toast-error")
        expect(error_toast).to_be_visible(timeout=1000)
    finally:
        page.close()


def test_environment_variable_rename_to_existing_name_is_rejected(browser_ctx):
    """Task 16 finding: unlike the two generic dict editors, the Environment
    Variables page's Add/Edit modal had no rename-collision guard at all --
    renaming (or creating) a variable to a name that already exists silently
    deleted the old entry and overwrote whatever was under the new name.
    Same #319 bug class, previously undiscovered."""
    ctx, base = browser_ctx
    page = ctx.new_page()
    # This repo's real environments: {} is empty -- seed 2 test-scoped
    # variables via the actual "+ Add Variable" flow, then remove them again
    # regardless of outcome, same discipline as every other test in this
    # suite that touches the real project.yaml.
    seeded = ["__TEST_COLLISION_A__", "__TEST_COLLISION_B__"]
    try:
        page.goto(f"{base}/#/project/environments")
        page.wait_for_load_state("networkidle")

        for var_name in seeded:
            page.get_by_role("button", name="+ Add Variable", exact=True).click()
            name_input = page.locator("#modal-body input").first
            expect(name_input).to_be_visible(timeout=3000)
            name_input.fill(var_name)
            page.get_by_role("button", name="Save", exact=True).click()
            page.wait_for_timeout(300)

        rows = page.locator("table.data tbody tr").filter(has=page.locator(f"code:text-is('{seeded[0]}'), code:text-is('{seeded[1]}')"))
        expect(rows).to_have_count(2, timeout=3000)

        # Edit the second seeded row, try to rename it to the first's name.
        page.get_by_text(seeded[1], exact=True).click()
        name_input = page.locator("#modal-body input").first
        expect(name_input).to_be_visible(timeout=3000)
        name_input.fill(seeded[0])
        page.get_by_role("button", name="Save", exact=True).click()
        page.wait_for_timeout(300)

        error_toast = page.locator(".toast-error")
        expect(error_toast).to_be_visible(timeout=1000)
        assert "already exists" in (error_toast.text_content() or "")

        # Modal must still be open (save was rejected) and both seeded
        # entries must still exist, untouched.
        expect(name_input).to_be_visible()
        page.get_by_role("button", name="Cancel", exact=True).click()
        for var_name in seeded:
            expect(page.get_by_text(var_name, exact=True)).to_be_visible()
    finally:
        # deleteEnv() now goes through the confirmDestructive() modal
        # (Phase 3, Task 18) instead of deleting immediately -- click
        # through it for each seeded entry still present.
        for var_name in seeded:
            row = page.get_by_text(var_name, exact=True)
            if row.count() > 0:
                row.locator("xpath=ancestor::tr").locator(".btn-danger").click()
                page.get_by_role("button", name="Delete", exact=True).click()
                page.wait_for_timeout(200)
        page.close()
