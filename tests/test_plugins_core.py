from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.plugins import (  # noqa: E402
    PLUGIN_CATALOG_YAML,
    plugins_of_kind,
    probe_plugin_availability,
    provider_has_lazy_channel,
    resolve_active_plugins,
    resolve_plugin_compact,
)
from lib.external_tools import resolve_active_external_tools  # noqa: E402
from lib.mcp_registry import resolve_active_mcp_servers  # noqa: E402

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


def test_resolve_active_plugins_agrees_with_generation_layer():
    """I5 regression: the browse/probe/scout layer (resolve_active_plugins)
    must report EXACTLY what artifact generation activates — no plugin that is
    "active" here but absent from the generated artifacts, and vice versa.

    An mcp-server with enabled-by-default: true but no explicit activation and
    no platform bundle is the exact case that used to diverge (looked active to
    the probe, absent from .mcp.json)."""
    catalog = {
        "graphify": {"kind": "cli-tool", "enabled-by-default": True},
        "off-tool": {"kind": "cli-tool", "enabled-by-default": False},
        "ebd-server": {"kind": "mcp-server", "enabled-by-default": True},
        "on-server": {"kind": "mcp-server", "enabled-by-default": False},
    }
    # No explicit `plugins:` block, no platforms → legacy/opt-in path.
    config = {"plugins": {"on-server": {"enabled": True}}}

    import lib.plugins as plugins
    from unittest import mock
    root = REPO_ROOT  # unused by the mocked loaders

    with mock.patch.object(plugins, "load_plugin_catalog", return_value=catalog), \
         mock.patch("lib.registry_query.load_mcp_registry",
                    return_value={k: v for k, v in catalog.items() if v["kind"] == "mcp-server"}), \
         mock.patch("lib.registry_query.load_external_tools_registry",
                    return_value={k: v for k, v in catalog.items() if v["kind"] == "cli-tool"}):
        active = set(resolve_active_plugins(config, root, catalog=catalog))
        gen_mcp = set(resolve_active_mcp_servers(config, root))
        gen_cli = set(resolve_active_external_tools(config, root))

    # enabled-by-default mcp-server WITHOUT explicit activation is NOT active
    assert "ebd-server" not in active
    assert "ebd-server" not in gen_mcp
    # explicit enabled: true mcp-server IS active in both layers
    assert "on-server" in active and "on-server" in gen_mcp
    # enabled-by-default cli-tool IS active in both layers
    assert "graphify" in active and "graphify" in gen_cli
    assert "off-tool" not in active
    # the two layers agree exactly
    assert active == (gen_mcp | gen_cli)


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
