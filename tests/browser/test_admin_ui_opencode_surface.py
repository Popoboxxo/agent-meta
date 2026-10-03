"""Live browser tests for the Opencode ``surface-version`` UI.

Covers AC-A6 (SPEC-ADMIN-UI-OPENCODE-SURFACE-AMENDMENT-2026-10-03):

- ``#/config/ai-providers`` renders ``surface-version`` for a provider that
  declares ``mcp-config.surface-formats {v1,v2}`` as a ``<select>`` (not free
  text), and shows the read-only active-surface badge once
  ``GET /api/ai-providers`` exposes ``active-surface``.
- ``#/project/providers`` exposes a ``surface-version`` ``<select>`` plus an
  ``agent-discovery`` checkbox per provider, and Save carries
  ``provider-options.<Provider>.surface-version``.

The provider under test is always ``Opencode`` because it is the only provider
whose registry entry declares a ``surface-formats`` map today; the option list
is read from the live registry rather than hard-coded.

These tests drive the real admin-server on :7421 via ``tests/browser/conftest.py``.
Under the active pytest-socket sandbox the loopback socket the session fixture
needs is blocked, so the module errors at fixture setup with
``SocketBlockedError`` (4 setup errors, no test body runs) — a documented
environment baseline constraint, not a product regression. The flow is instead
verified by the static assertions in ``tests/test_admin_ui_plugins_section.py``
and a live Playwright run against admin-server, which is outside pytest's socket
block (see the test report).
"""

import os
import re
from contextlib import contextmanager
from pathlib import Path

import pytest
pytest.importorskip("playwright")
from playwright.sync_api import expect


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_YAML = REPO_ROOT / ".meta-config" / "project.yaml"
OPENCODE = "Opencode"


@contextmanager
def _project_yaml_guard():
    """Restore ``.meta-config/project.yaml`` byte-for-byte after a save test.

    ``PUT /api/config/project/section`` re-serializes the whole document (every
    comment is dropped), so the guard snapshots raw bytes and prunes any
    ``.bak.*`` side-car the server creates during the test.
    """
    raw = PROJECT_YAML.read_bytes()
    mode = PROJECT_YAML.stat().st_mode
    pre_baks = {p for p in PROJECT_YAML.parent.glob(PROJECT_YAML.name + ".bak.*")}
    try:
        yield
    finally:
        PROJECT_YAML.write_bytes(raw)
        os.chmod(PROJECT_YAML, mode)
        for p in PROJECT_YAML.parent.glob(PROJECT_YAML.name + ".bak.*"):
            if p not in pre_baks:
                p.unlink()


def _registry_opencode_formats(base_url: str, ctx) -> list:
    """Read Opencode's declared surface-formats keys from the live registry."""
    resp = ctx.request.get(base_url + "/api/ai-providers")
    data = resp.json() or {}
    registry = data.get("providers") or data
    entry = registry.get(OPENCODE) or {}
    formats = (entry.get("mcp-config") or {}).get("surface-formats") or {}
    return list(formats.keys())


def _registry_panel(page, name):
    """The ``details.panel`` accordion for a given provider."""
    return page.locator("details.panel").filter(
        has=page.locator(f"summary:text-is('{name}')")
    )


def _opencode_header(page):
    """Exact-match the provider-section header span.

    ``has_text`` is a case-insensitive substring match, so a loose ``Opencode``
    also matches the display name ``OpenCode`` in the providers checklist; the
    regex anchors to the section header's ``span.mono`` label only.
    """
    return page.locator("span.mono").filter(has_text=re.compile(r"^Opencode$")).first


def test_registry_surface_version_is_select_with_declared_options(browser_ctx):
    ctx, base = browser_ctx
    formats = _registry_opencode_formats(base, ctx)
    if not formats:
        pytest.skip("registry declares no surface-formats for Opencode")

    page = ctx.new_page()
    try:
        page.goto(base + "/#/config/ai-providers")
        page.wait_for_load_state("networkidle")
        panel = _registry_panel(page, OPENCODE)
        expect(panel).to_be_visible(timeout=10000)

        select = panel.locator("select").first
        expect(select).to_be_visible(timeout=5000)
        values = select.evaluate("el => Array.from(el.options).map(o => o.value)")
        assert values, "surface-version select has no options"
        assert set(values) == set(formats), (
            f"select options {values!r} != declared surface-formats {formats!r}"
        )
    finally:
        page.close()


def test_registry_shows_active_surface_badge_when_exposed(browser_ctx):
    ctx, base = browser_ctx
    resp = ctx.request.get(base + "/api/ai-providers")
    data = resp.json() or {}
    if not data.get("active-surface"):
        pytest.skip("GET /api/ai-providers does not expose active-surface yet (Task 3)")

    page = ctx.new_page()
    try:
        page.goto(base + "/#/config/ai-providers")
        page.wait_for_load_state("networkidle")
        panel = _registry_panel(page, OPENCODE)
        expect(panel).to_be_visible(timeout=10000)
        badge = panel.locator("summary span.badge")
        expect(badge.first).to_be_visible(timeout=5000)
        text = badge.first.text_content() or ""
        assert text.strip(), "active-surface badge rendered empty"
    finally:
        page.close()


def test_project_providers_exposes_surface_select_and_discovery_checkbox(browser_ctx):
    ctx, base = browser_ctx
    formats = _registry_opencode_formats(base, ctx)
    expected = formats or ["v1"]

    page = ctx.new_page()
    try:
        page.goto(base + "/#/project/providers")
        page.wait_for_load_state("networkidle")

        header = _opencode_header(page)
        expect(header).to_be_visible(timeout=10000)
        section = header.locator(
            "xpath=ancestor::div[contains(@style,'border:1px solid')][1]"
        )

        select = section.locator("select").first
        expect(select).to_be_visible(timeout=5000)
        values = select.evaluate("el => Array.from(el.options).map(o => o.value)")
        assert set(expected).issubset(set(values)), (
            f"project surface select options {values!r} missing {expected!r}"
        )

        checkbox = section.locator("input[type='checkbox']").first
        expect(checkbox).to_be_visible(timeout=5000)
    finally:
        page.close()


def test_project_surface_version_persists_on_save(browser_ctx):
    """Interaction round trip: pick a surface, Save, reload, value survives."""
    ctx, base = browser_ctx
    formats = _registry_opencode_formats(base, ctx)
    # Pick any declared value; keep it simple and prefer v1 when present.
    target = "v1" if "v1" in formats else (formats[0] if formats else None)
    if target is None:
        pytest.skip("registry declares no surface-formats for Opencode")

    with _project_yaml_guard():
        page = ctx.new_page()
        try:
            page.goto(base + "/#/project/providers")
            page.wait_for_load_state("networkidle")

            header = _opencode_header(page)
            expect(header).to_be_visible(timeout=10000)
            section = header.locator(
                "xpath=ancestor::div[contains(@style,'border:1px solid')][1]"
            )
            select = section.locator("select").first
            expect(select).to_be_visible(timeout=5000)
            select.select_option(target)

            page.get_by_role("button", name="Save").first.click()
            page.wait_for_timeout(750)

            # Reload from the server and confirm the value round-tripped.
            page.reload()
            page.wait_for_load_state("networkidle")
            header2 = _opencode_header(page)
            expect(header2).to_be_visible(timeout=10000)
            section2 = header2.locator(
                "xpath=ancestor::div[contains(@style,'border:1px solid')][1]"
            )
            select2 = section2.locator("select").first
            expect(select2).to_have_value(target, timeout=5000)
        finally:
            page.close()
