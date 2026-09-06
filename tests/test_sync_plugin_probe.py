# tests/test_sync_plugin_probe.py
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import lib.plugins as plugins_module  # noqa: E402


def test_probe_reports_available_but_inactive(monkeypatch):
    # _probe_inactive_plugins resolves the catalog/activation/probe helpers
    # through lib.plugins (its defining module — moved there by the #481
    # sync-pipeline split), so the patch targets follow the code.
    monkeypatch.setattr(plugins_module, "load_plugin_catalog", lambda **kw: {
        "graphify": {"kind": "cli-tool", "availability-probe": "command-v", "binary": "graphify"},
        "honcho": {"kind": "mcp-server", "availability-probe": "http-head"},
    })
    monkeypatch.setattr(plugins_module, "resolve_active_plugins", lambda *a, **k: ["honcho"])
    monkeypatch.setattr(plugins_module, "probe_plugin_availability", lambda d: d.get("binary") == "graphify")
    lines = plugins_module._probe_inactive_plugins(REPO_ROOT, REPO_ROOT, {})
    assert any("graphify" in ln and "HINWEIS" in ln for ln in lines)
    assert not any("honcho" in ln for ln in lines)  # active -> not reported
