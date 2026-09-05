# tests/test_sync_plugin_probe.py
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import sync  # noqa: E402


def test_probe_reports_available_but_inactive(monkeypatch):
    monkeypatch.setattr(sync, "load_plugin_catalog", lambda **kw: {
        "graphify": {"kind": "cli-tool", "availability-probe": "command-v", "binary": "graphify"},
        "honcho": {"kind": "mcp-server", "availability-probe": "http-head"},
    })
    monkeypatch.setattr(sync, "resolve_active_plugins", lambda *a, **k: ["honcho"])
    monkeypatch.setattr(sync, "probe_plugin_availability", lambda d: d.get("binary") == "graphify")
    lines = sync._probe_inactive_plugins(REPO_ROOT, REPO_ROOT, {})
    assert any("graphify" in ln and "HINWEIS" in ln for ln in lines)
    assert not any("honcho" in ln for ln in lines)  # active -> not reported
