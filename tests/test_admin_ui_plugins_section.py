from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HTML = (REPO_ROOT / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")


def test_available_plugins_view_defined():
    assert "async function viewAvailablePlugins(" in HTML


def test_view_uses_catalog_and_test_endpoints():
    assert "/api/config/plugin-catalog" in HTML
    assert "/api/plugins/" in HTML and "/test" in HTML


def test_view_saves_plugins_section():
    # activation persists via the unified `plugins` project section
    assert 'section: "plugins"' in HTML or "section: 'plugins'" in HTML


def test_view_is_routed():
    assert "viewAvailablePlugins" in HTML  # referenced by the router table, not only defined
    assert HTML.count("viewAvailablePlugins") >= 2
