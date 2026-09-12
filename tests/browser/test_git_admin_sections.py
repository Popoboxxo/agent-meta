"""Browser smoke tests for the Admin UI Git / Subagent Permissions /
Auto-Commit sections (feature ``subagent-permissions-git-admin-ui``).

Read-only by design. Unlike ``test_project_form_editors.py`` these pages cover
sections that do not exist in this repo's own ``.meta-config/project.yaml``, so
a naive save/restore cycle would leave a ``<section>: null`` stub behind. The
tests therefore assert that the editors render, that the provider-override
table is populated for the active providers, and that the
``auto_commit mode: custom`` client gate blocks a save without persisting.
"""

import pytest

pytest.importorskip("playwright")
from playwright.sync_api import expect  # noqa: E402


def _mode_select(page):
    return page.locator(".field").filter(has=page.get_by_text("Mode", exact=True)).locator("select")


def test_subagent_permissions_editor_renders(browser_ctx):
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/project/subagent-permissions")
        page.wait_for_load_state("networkidle")

        mode = _mode_select(page)
        expect(mode).to_be_visible(timeout=5000)
        expect(mode).to_have_value("off")
        expect(page.get_by_text("Provider Overrides")).to_be_visible()

        # One override row per active provider configured in project.yaml.
        for provider in ("Claude", "Opencode", "Gemini"):
            row = page.locator(".field-row").filter(has=page.get_by_text(provider, exact=True))
            expect(row).to_have_count(1)
    finally:
        page.close()


def test_git_editor_renders(browser_ctx):
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/project/git")
        page.wait_for_load_state("networkidle")

        platform = page.locator(".field").filter(
            has=page.get_by_text("Platform", exact=True)).locator("select")
        expect(platform).to_be_visible(timeout=5000)
        expect(platform).to_have_value("GitHub")

        expect(page.locator("#git-remote-url")).to_be_visible()
        expect(page.locator("#git-main-branch")).to_be_visible()
        expect(page.locator("#git-prefix-feat")).to_be_visible()
        expect(page.locator("#git-prefix-fix")).to_be_visible()
        expect(page.locator("#git-prefix-chore")).to_be_visible()
    finally:
        page.close()


def test_auto_commit_custom_without_script_is_blocked_client_side(browser_ctx):
    ctx, base = browser_ctx
    page = ctx.new_page()
    try:
        page.goto(f"{base}/#/project/auto-commit")
        page.wait_for_load_state("networkidle")

        before = page.request.get(f"{base}/api/config/project").json().get("auto_commit")

        mode = _mode_select(page)
        expect(mode).to_be_visible(timeout=5000)
        mode.select_option("custom")
        page.locator("#auto-commit-custom-script").fill("")

        page.get_by_role("button", name="Save", exact=True).click()

        expect(page.locator("#auto-commit-status")).to_contain_text("custom_script", timeout=5000)

        after = page.request.get(f"{base}/api/config/project").json().get("auto_commit")
        assert after == before, "client gate must not persist an invalid auto_commit"
    finally:
        page.close()
