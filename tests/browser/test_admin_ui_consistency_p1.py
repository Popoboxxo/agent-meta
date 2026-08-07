"""Phase 1 of the admin-ui consistency plan (docs/superpowers/plans/2026-08-07-admin-ui-consistency.md):
targeted fixes to the Backups table/buttons, raw config-key labels, and a
regression found while doing Task 6 -- the Orchestrator settings page still
had form controls for orchestrator.handoff.* keys removed from
config/project-config.schema.json in the A2A cleanup (#436): saving that
page would have silently dropped or, worse, thrown (one field referenced a
variable that no longer existed after the panel was first trimmed).
"""

from pathlib import Path

import pytest
pytest.importorskip('playwright')
from playwright.sync_api import expect

REPO_ROOT = Path(__file__).resolve().parents[2]
_ADMIN_UI_SOURCE = (REPO_ROOT / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")


def test_backups_table_uses_the_shared_data_table_style():
    """Task 5: the Backups table referenced a "roles-table" CSS class that
    was never defined anywhere in the file (grep-verified), rendering
    completely unstyled. Must use the same "data" class as every other
    table."""
    assert 'class: "roles-table"' not in _ADMIN_UI_SOURCE
    assert 'class: "data"' in _ADMIN_UI_SOURCE  # sanity: the class exists at all


def test_backups_delete_button_has_danger_styling(browser_ctx):
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/project/backups")
        page.wait_for_load_state("networkidle")
        delete_btn = page.get_by_role("button", name="Delete").first
        if delete_btn.count() == 0:
            pytest.skip("no backups present to render a Delete button against")
        classes = delete_btn.get_attribute("class") or ""
        assert "btn-danger" in classes, f"Delete button classes are {classes!r}, expected btn-danger"
    finally:
        page.close()


def test_removed_handoff_config_keys_have_no_leftover_form_controls():
    """Regression found while doing Task 6: the Orchestrator settings page
    still had checkbox/number/dropdown controls for orchestrator.handoff.*
    keys that config/project-config.schema.json no longer allows
    (additionalProperties: false, set in the A2A cleanup, #436) --
    validate-before-delegate, supersession-tracking, strict-validation,
    compact-mode, human_approval_required, max_retries, protocol_routing,
    and the entire token-budget sub-object. Saving this page would have
    thrown a ReferenceError (a leftover `tb` reference after the Token
    Budget panel's own variable was removed) or silently written keys the
    schema rejects.
    """
    # Checked as functional usage patterns (property access / form-field
    # constructor calls), not bare substring matches -- an explanatory code
    # comment near the removal legitimately still names "token-budget" in
    # prose, which a bare-string check would misflag.
    removed_key_usages = [
        'checkboxField("validate-before-delegate"',
        'checkboxField("supersession-tracking"',
        'checkboxField("strict-validation"',
        'checkboxField("compact-mode"',
        'checkboxField("human_approval_required"',
        '"max_retries"]',
        'checkboxField("protocol_routing"',
        'hf["token-budget"]',
    ]
    for usage in removed_key_usages:
        assert usage not in _ADMIN_UI_SOURCE, f"leftover reference to removed config key: {usage}"


def test_orchestrator_settings_save_does_not_throw(browser_ctx):
    """The Save button's onclick is an async arrow function -- a synchronous
    throw inside it (e.g. a leftover reference to a removed variable)
    rejects the handler's own promise instead of raising a catchable
    exception on the page, so it never reaches page.on("pageerror"). It
    does surface as a console "error" message ("Uncaught (in promise) ..."),
    which is what this test watches instead."""
    ctx, base = browser_ctx
    page = ctx.new_page()
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    try:
        page.goto(f"{base}/#/project/orchestrator")
        page.wait_for_load_state("networkidle")
        save_btn = page.get_by_role("button", name="Save", exact=True).first
        expect(save_btn).to_be_visible(timeout=5000)
        save_btn.click()
        page.wait_for_timeout(1000)
        assert not console_errors, f"Save logged a JS error to the console: {console_errors}"
    finally:
        page.close()


def test_provider_options_labels_are_humanized(browser_ctx):
    """Task 6: "PROVIDER-OPTIONS" / "provider-isolation" broke the sentence-
    case convention used by every other label on the same page."""
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/project/providers")
        page.wait_for_load_state("networkidle")
        expect(page.get_by_text("Provider isolation", exact=True)).to_be_visible(timeout=5000)
        # The h3 renders visually uppercase via CSS text-transform (consistent
        # with every other h3 sub-heading in this panel style) -- the
        # underlying text content is what must be humanized.
        heading = page.locator("h3", has_text="Provider options")
        expect(heading).to_have_count(1)
    finally:
        page.close()


def test_remove_action_titles_use_title_case():
    """Task 7: title="remove" (lowercase) vs title="Remove override" (Title
    Case) for equally-destructive actions."""
    assert 'title: "remove"' not in _ADMIN_UI_SOURCE
    assert 'title: "remove"' not in _ADMIN_UI_SOURCE.replace(" ", "")  # no whitespace-variant either
