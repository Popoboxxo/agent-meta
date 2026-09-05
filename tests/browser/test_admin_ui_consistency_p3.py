"""Phase 3 of the admin-ui consistency plan (docs/superpowers/plans/2026-08-07-admin-ui-consistency.md):
Task 16 (KV-editor consolidation) is covered by
tests/browser/test_dict_editor_rename_collision.py, which this phase
extended with the Provider Options + Environment Variables cases.

This file covers Task 18: every destructive action (14 native confirm()
calls, plus the generic dict-editor's row delete which previously had NO
confirmation at all) now goes through the shared confirmDestructive()
helper built on the existing showModal() component, instead of a native
confirm() dialog that breaks out of the app's dark theme.
"""

import pytest
pytest.importorskip('playwright')
from playwright.sync_api import expect


def test_kv_editor_row_delete_requires_confirmation(browser_ctx):
    """Task 18 Step 2/4: the generic dict editor's own row-delete button
    (MCP server Headers/Env-Vars, Provider Options) previously deleted
    immediately on click with zero confirmation -- unlike every other
    destructive action in the file. Clicking delete on a named row must now
    show the confirmDestructive modal before anything is removed.
    """
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/project/plugin-overrides")
        page.wait_for_load_state("networkidle")

        panel = page.locator(".panel").filter(has=page.get_by_role("heading", name="honcho", exact=True))
        panel.get_by_role("button", name="Customize", exact=False).click()

        rows = panel.get_by_text("Headers", exact=True).locator("xpath=following-sibling::div[1]/div")
        expect(rows).to_have_count(4, timeout=3000)
        row_count_before = rows.count()

        rows.first.locator("button", has_text="×").click()

        # The row must still be present -- deletion is pending confirmation,
        # not yet applied.
        expect(rows).to_have_count(row_count_before, timeout=1000)

        modal_overlay = page.locator("#modal-overlay")
        expect(modal_overlay).to_be_visible(timeout=1000)
        expect(page.locator("#modal-body")).to_contain_text("Delete")
        expect(page.get_by_role("button", name="Delete", exact=True)).to_be_visible()
        expect(page.get_by_role("button", name="Cancel", exact=True)).to_be_visible()

        # Cancel must leave the row untouched.
        page.get_by_role("button", name="Cancel", exact=True).click()
        expect(modal_overlay).to_be_hidden(timeout=1000)
        expect(rows).to_have_count(row_count_before)

        # Confirming must actually remove it.
        rows.first.locator("button", has_text="×").click()
        page.get_by_role("button", name="Delete", exact=True).click()
        expect(rows).to_have_count(row_count_before - 1, timeout=1000)
    finally:
        page.close()


def test_backup_delete_uses_confirm_destructive_modal(browser_ctx):
    """Representative of the 12 former native-confirm() call sites (Backups
    "Delete", Provider Deactivation bulk actions, model Blacklist/Reset/
    Exclude, environment-variable delete, etc.): clicking a destructive
    action button must open the app's own modal, not a native browser
    confirm() dialog. If this were still confirm(), page.on("dialog")
    would fire and this test would hang/timeout waiting for #modal-overlay
    instead.
    """
    ctx, base = browser_ctx
    page = ctx.new_page()
    dialog_fired = []
    page.on("dialog", lambda d: (dialog_fired.append(d.message), d.dismiss()))
    try:
        page.goto(f"{base}/#/project/backups")
        page.wait_for_load_state("networkidle")

        delete_btn = page.get_by_role("button", name="Delete").first
        if delete_btn.count() == 0:
            pytest.skip("no backups present to render a Delete button against")
        delete_btn.click()

        modal_overlay = page.locator("#modal-overlay")
        expect(modal_overlay).to_be_visible(timeout=2000)
        assert not dialog_fired, f"native confirm() fired instead of the modal: {dialog_fired}"
        expect(page.locator("#modal-body")).to_contain_text("Delete this backup")

        # Cancel -- must not touch any backups.
        page.get_by_role("button", name="Cancel", exact=True).click()
        expect(modal_overlay).to_be_hidden(timeout=1000)
    finally:
        page.close()


def test_no_native_confirm_calls_remain_for_destructive_actions():
    """Static check: every destructive-action confirm() found by the
    Phase-3 audit was migrated to confirmDestructive(). The one exception
    -- the router's unsaved-changes-on-navigate guard -- is a synchronous
    navigation interceptor (hashchange handler needs an immediate true/false
    to decide whether to allow the already-fired hash change), a
    structurally different problem from "confirm before deleting something"
    that a modal's async click-driven flow can't cleanly replace without a
    bigger navigation-flow change. It's intentionally excluded and confirmed
    to still be the only remaining occurrence.
    """
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")

    confirm_calls = [
        line for line in source.splitlines()
        if "confirm(" in line and "confirmDestructive(" not in line and "// " not in line.split("confirm(")[0]
    ]
    assert len(confirm_calls) == 1, f"expected exactly 1 remaining confirm() call (the nav guard), found: {confirm_calls}"
    assert "_dirtyMsg" in confirm_calls[0], f"the one remaining confirm() call should be the unsaved-changes nav guard, got: {confirm_calls[0]}"
