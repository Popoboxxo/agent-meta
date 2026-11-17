"""Static UI assertions for the Admin-UI "Artifacts" pane (issue #1186, T19).

The pane is verified against the file text, not a live browser: issue #1189
makes the admin-server start testable, so T19 deliberately keeps these as
static assertions (plan §5, T19). The tests pin the contract that matters:
per-class rendering by ``artifact.id``, the section save, routing, the mode /
git selects, the read-only legacy / unmanaged lists, and the status-JSON-fed
preview (no second resolver in the browser).
"""
from __future__ import annotations

import re
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ADMIN_UI = _PROJECT_ROOT / "docs" / "ui" / "admin-ui.html"
_HELP_REF = _PROJECT_ROOT / "docs" / "api" / "admin-ui-reference.md"


def _ui() -> str:
    return _ADMIN_UI.read_text(encoding="utf-8")


def _function_body(src: str, name: str) -> str:
    """Return a whole ``function name(...) { ... }`` by brace balancing."""
    match = re.search(r"function\s+" + re.escape(name) + r"\s*\([^)]*\)\s*\{", src)
    assert match, "function %s() not found in admin-ui.html" % name
    depth = 0
    for idx in range(match.end() - 1, len(src)):
        char = src[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return src[match.start():idx + 1]
    raise AssertionError("unbalanced braces in %s()" % name)


# --------------------------------------------------------------------------- #
# T19 — 6 static tests (plan §5, AC-06)
# --------------------------------------------------------------------------- #


def test_ui_has_artifact_pane() -> None:
    """A pane renders each class by artifact.id and saves the section."""
    ui = _ui()
    assert "viewProjectArtifacts" in ui
    body = _function_body(ui, "viewProjectArtifacts")
    assert "artifactId" in body, "pane must render one row per artifact.id"
    assert 'saveProjectSection("artifact-locations"' in body


def test_ui_routes_pane() -> None:
    """The help route map and the router map project/artifacts to the pane."""
    ui = _ui()
    assert '"project/artifacts": "project_instance-artifact_locations"' in ui
    assert 'router.register("/project/artifacts", viewProjectArtifacts)' in ui


def test_ui_renders_mode_and_git_selects() -> None:
    """Each class row exposes mode (files|inline|off) and git (tracked|ignored)."""
    body = _function_body(_ui(), "viewProjectArtifacts")
    assert 'dropdownField("Mode"' in body
    assert '["files", "inline", "off"]' in body
    assert 'dropdownField("Git"' in body
    assert '["tracked", "ignored"]' in body


def test_ui_renders_legacy_readonly() -> None:
    """legacy[] / unmanaged[] are rendered by a control-free read-only helper."""
    body = _function_body(_ui(), "artifactReadonlyList")
    assert "artifact-readonly" in body
    assert "(read-only)" in body
    # A read-only list renders text nodes only — no editor, no save control.
    assert "saveProjectSection" not in body
    assert "button" not in body
    assert "onclick" not in body


def test_ui_preview_uses_status_json() -> None:
    """The preview consumes --status-artifacts --json; no browser resolver."""
    ui = _ui()
    body = _function_body(ui, "loadArtifactStatus")
    assert "--status-artifacts --json" in ui
    assert "/api/status-artifacts" in body or "__ARTIFACT_STATUS_JSON__" in body
    # Resolution happens in sync.py only, never reimplemented in the browser.
    assert "resolveArtifactLocations" not in ui
    assert "resolveCellPath" not in ui


def test_help_id_is_documented() -> None:
    """A missing help-id makes consistency-check ERROR docs.ui_help_mappings."""
    ref = _HELP_REF.read_text(encoding="utf-8")
    assert "<!-- help-id: project_instance-artifact_locations -->" in ref
