"""Static Admin-UI assertions for the ``context_file.topology`` control (AC-20).

The topology switch lives inside the existing ``context_file`` section —
``viewProjectGeneral`` renders it and the shared Save button PUTs the whole
section. These tests assert the UI shape (default, dropdown, help text) without
starting the server.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HTML = (REPO_ROOT / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")


def test_topology_dropdown_default_unified():
    """The topology control defaults to ``unified`` (safe-side)."""
    assert 'topology: contextFileSrc.topology || "unified"' in HTML, (
        "contextFile must default topology to 'unified'"
    )
    assert '"Topology", ["unified", "per-provider"], contextFile.topology' in HTML, (
        "topology must render as a unified|per-provider dropdown"
    )


def test_core_file_default_agents_md():
    assert 'core_file: contextFileSrc.core_file || "AGENTS.md"' in HTML, (
        "contextFile must default core_file to 'AGENTS.md'"
    )
    assert '"Core file", contextFile.core_file' in HTML, (
        "core_file must render as an editable field"
    )


def test_topology_persisted_in_context_file_section():
    """No new endpoint/section: the shared Save PUTs ``context_file``."""
    assert '["context_file", contextFile]' in HTML, (
        "viewProjectGeneral must persist the context_file section"
    )


def test_help_text_distinguishes_topology_from_density():
    """The help text must separate topology from the density mode."""
    assert "Topology axis" in HTML
    lowered = HTML.lower()
    assert "density" in lowered, "help text must mention density"
    assert "context_file.mode" in HTML, "help text must name the density key"
    assert "per-provider" in HTML
