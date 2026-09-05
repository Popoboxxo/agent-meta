# tests/test_plugin_loader_redirect.py
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.external_tools import load_external_tools_registry, resolve_active_external_tools  # noqa: E402
from lib.mcp import load_mcp_registry, resolve_active_mcp_servers  # noqa: E402


def test_load_mcp_registry_sources_from_catalog():
    reg = load_mcp_registry(REPO_ROOT)
    # only mcp-server kind, cli-tools excluded
    assert "viz-logger" in reg and "honcho" in reg
    assert "graphify" not in reg


def test_load_external_tools_registry_sources_from_catalog():
    reg = load_external_tools_registry(REPO_ROOT)
    assert "graphify" in reg
    assert "honcho" not in reg


def test_active_server_order_preserved_for_legacy_config():
    # agent-meta's legacy activation order must be reproduced exactly:
    # explicit list order, then bundle additions -> byte-identical .mcp.json.
    config = {"mcp-servers": ["honcho", "playwright", "reqogniloom"], "platforms": ["agent-meta"]}
    active = resolve_active_mcp_servers(config, REPO_ROOT)
    assert active == ["honcho", "playwright", "reqogniloom", "viz-logger"]


def test_active_servers_from_unified_plugins_block_match_legacy():
    legacy = {"mcp-servers": ["honcho", "playwright", "reqogniloom"], "platforms": ["agent-meta"]}
    unified = {
        "plugins": {"honcho": {"enabled": True}, "playwright": {"enabled": True},
                    "reqogniloom": {"enabled": True}, "graphify": {"enabled": True}},
        "platforms": ["agent-meta"],
    }
    assert resolve_active_mcp_servers(unified, REPO_ROOT) == resolve_active_mcp_servers(legacy, REPO_ROOT)
    assert resolve_active_external_tools(unified, REPO_ROOT) == ["graphify"]
