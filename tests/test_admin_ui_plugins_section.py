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


# ---------------------------------------------------------------------------
# Opencode surface-version UI (SPEC-ADMIN-UI-OPENCODE-SURFACE-AMENDMENT)
# ---------------------------------------------------------------------------


def test_infer_schema_accepts_enum_opts():
    """inferSchema gains an optional opts arg carrying an enumFields map."""
    assert "function inferSchema(obj, opts)" in HTML
    assert "opts.enumFields" in HTML


def test_infer_schema_emits_enum_and_forwards_opts_nested():
    """enumFields -> {type:"string", enum:[...]}; opts forwarded through
    nested recursion so nested providers keep the enum affordance (REV-R7)."""
    assert "enum: enumFields[k]" in HTML
    assert "inferSchema(v, opts)" in HTML


def test_ai_providers_fetches_active_surface_badge_separately():
    """The badge map is fetched from GET /api/ai-providers, defensively, and is
    NEVER merged into the editable config object."""
    assert '(await api.get("/api/ai-providers").catch(() => ({})))["active-surface"] || {}' in HTML
    assert "activeSurface[provider]" in HTML


def test_ai_providers_strips_reserved_active_surface_key():
    """The reserved read-only key must be deleted before save (REV-R1/R3)."""
    assert 'delete data["active-surface"];' in HTML
    assert 'delete providers["active-surface"];' in HTML
    assert 'delete conf["active-surface"];' in HTML


def test_ai_providers_surface_options_from_formats_with_v1_fallback():
    """surface-version options = surface-formats keys, fallback ["v1"]."""
    assert "surface-formats" in HTML
    assert 'declaredFormats.length ? declaredFormats : ["v1"]' in HTML
    assert 'enumFields: { "surface-version": surfaceOptions }' in HTML


def test_project_providers_surface_select_and_discovery_checkbox():
    """Project provider-options view exposes a surface-version <select> plus an
    agent-discovery checkbox, and excludes both from the generic KV editor."""
    assert "surfaceSelect.addEventListener" in HTML
    assert 'provOpts["surface-version"] = surfaceSelect.value' in HTML
    assert "discoveryCb.addEventListener" in HTML
    assert 'provOpts["agent-discovery"] = discoveryCb.checked' in HTML
    assert 'excludeKeys: ["surface-version", "agent-discovery"]' in HTML


def test_render_dict_editor_supports_exclude_keys_opt():
    """renderDictEditor skips caller-owned keys instead of offering duplicates."""
    assert "const excludeKeys = (opts && opts.excludeKeys) || [];" in HTML
    assert "if (excludeKeys.includes(k)) return;" in HTML
