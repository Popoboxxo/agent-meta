from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.plugins import (  # noqa: E402
    PLUGIN_CATALOG_YAML,
    _plugin_is_active,
    plugins_of_kind,
    probe_plugin_availability,
    provider_has_lazy_channel,
    resolve_plugin_compact,
)

_CATALOG = {
    "graphify": {"kind": "cli-tool", "enabled-by-default": False},
    "viz-logger": {"kind": "mcp-server", "enabled-by-default": True},
    "honcho": {"kind": "mcp-server", "enabled-by-default": False},
}


def test_constant_points_at_new_catalog_file():
    assert PLUGIN_CATALOG_YAML == "config/plugin-catalog.yaml"


def test_plugins_of_kind_filters_by_discriminator():
    mcp = plugins_of_kind(_CATALOG, "mcp-server")
    assert set(mcp) == {"viz-logger", "honcho"}
    assert set(plugins_of_kind(_CATALOG, "cli-tool")) == {"graphify"}


def test_plugin_is_active_precedence():
    # explicit project setting wins over the registry default
    assert _plugin_is_active("honcho", _CATALOG["honcho"], {"honcho": {"enabled": True}}) is True
    assert _plugin_is_active("viz-logger", _CATALOG["viz-logger"], {"viz-logger": {"enabled": False}}) is False
    # fall back to enabled-by-default
    assert _plugin_is_active("viz-logger", _CATALOG["viz-logger"], {}) is True
    assert _plugin_is_active("honcho", _CATALOG["honcho"], {}) is False


def test_provider_has_lazy_channel():
    assert provider_has_lazy_channel({"has_rules": True}) is True
    assert provider_has_lazy_channel({"capabilities": ["agents", "skills"]}) is True
    # ZCode/KimiCode shape: no rules, no skills capability -> no lazy channel
    assert provider_has_lazy_channel({"capabilities": ["agents", "mcp"]}) is False
    assert provider_has_lazy_channel({}) is False


def test_resolve_plugin_compact_convergence_safe():
    has = {"has_rules": True}
    none = {"capabilities": ["mcp"]}
    assert resolve_plugin_compact(True, [has]) is True
    assert resolve_plugin_compact(True, [none]) is False          # no lazy channel -> force full
    assert resolve_plugin_compact(True, [has, none]) is False     # any shared user lacks it -> full
    assert resolve_plugin_compact(False, [has]) is False          # global full always wins


def test_probe_local_binary(monkeypatch):
    import lib.plugins as plugins
    monkeypatch.setattr(plugins.shutil, "which", lambda name: "/usr/bin/graphify" if name == "graphify" else None)
    assert probe_plugin_availability({"availability-probe": "command-v", "binary": "graphify"}) is True
    assert probe_plugin_availability({"availability-probe": "command-v", "binary": "nope"}) is False
    assert probe_plugin_availability({"availability-probe": "always"}) is True
    assert probe_plugin_availability({"availability-probe": "none"}) is False
