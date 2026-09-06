"""Unified plugin catalog facade: probe, compact-channel and browse-layer
logic for the kind-discriminated plugin catalog. The catalog loading,
kind filtering and registry-backed activation resolution moved to the
neutral :mod:`lib.registry_query` core (Issue #478 dependency inversion —
this module may import it top-level without a cycle, since nothing in
registry_query's import closure reaches back here).

Backward-compatible re-exports: ``load_plugin_catalog``, ``plugins_of_kind``
and ``_activation_from_config`` keep being importable from this module
(sync.py, admin-server.py, tests and the registry facades import them via
``lib.plugins``).
"""
from __future__ import annotations

import shutil
import urllib.request
from pathlib import Path

from .registry_query import (  # noqa: F401 -- re-exported for API compat (Issue #478)
    PLUGIN_CATALOG_YAML,
    _activation_from_config,
    load_plugin_catalog,
    plugins_of_kind,
    resolve_active_external_tools,
    resolve_active_mcp_servers,
)


def resolve_active_plugins(
    config: dict,
    agent_meta_root: Path,
    project_root: Path | None = None,
    catalog: dict | None = None,
) -> list[str]:
    """All active plugin ids (any kind), catalog order. Used by the browse/probe/
    scout/test features.

    Delegates to the two generation-layer resolvers (resolve_active_mcp_servers
    for mcp-server plugins, resolve_active_external_tools for cli-tool plugins)
    so this browse/probe layer sees EXACTLY the plugins artifact generation
    activates — no third, looser notion of "active". This matters because the
    two kinds have *different* activation models: cli-tools honour the catalog's
    enabled-by-default flag, but mcp-servers do NOT (they are active only via an
    explicit enabled: true or a platform bundle). A single enabled-by-default
    fallback for both kinds (the old implementation) made enabled-by-default
    mcp-servers look active to the probe/scout layer while being absent from the
    generated .mcp.json — see I5 in the plugin-catalog-unification fix wave.

    Both resolvers come from lib.registry_query at module top level (Issue
    #478): the former deferred imports here existed to break the
    plugins <- mcp_registry / external_tools import cycle; the cycle is gone
    now that the catalog core and both resolvers live in registry_query.
    """
    if catalog is None:
        catalog = load_plugin_catalog(config=config, agent_meta_root=agent_meta_root, project_root=project_root)
    active = set(resolve_active_mcp_servers(config, agent_meta_root, project_root))
    active |= set(resolve_active_external_tools(config, agent_meta_root, project_root))
    return [pid for pid in catalog if pid in active]


def provider_has_lazy_channel(pc: dict) -> bool:
    """True if the provider has a lazy (non-always-on) channel for full plugin
    content: a native rules dir OR the skills capability. Providers with
    neither (ZCode, KimiCode) must never receive the compact-only variant, or
    the full agent-hint is silently lost (spec status-quo gap)."""
    return bool(pc.get("has_rules")) or ("skills" in (pc.get("capabilities") or []))


def resolve_plugin_compact(global_compact: bool, pcs: list[dict]) -> bool:
    """Convergence-safe compact decision for embedded plugin content. Compact
    only when the project opted in AND every provider sharing the target
    context_file has a lazy channel — otherwise force full embedding (spec
    provider-agnostik fix; mirrors the #638 shared-file union rule)."""
    return global_compact and all(provider_has_lazy_channel(pc) for pc in pcs)


def probe_plugin_availability(plugin_def: dict) -> bool:
    """Cheap, side-effect-free reachability check for the sync-time hint
    (Layer 3). Never spawns a long-lived process or sends auth."""
    probe = plugin_def.get("availability-probe", "none")
    if probe == "always":
        return True
    if probe == "command-v":
        binary = plugin_def.get("binary") or (plugin_def.get("connection", {}) or {}).get("command", "")
        return bool(binary) and shutil.which(binary) is not None
    if probe == "npx-resolve":
        return shutil.which("npx") is not None
    if probe == "http-head":
        url = (plugin_def.get("connection", {}) or {}).get("url", "")
        if not url:
            return False
        try:
            req = urllib.request.Request(url, method="HEAD")  # noqa: S310 (curated catalog URL)
            with urllib.request.urlopen(req, timeout=3):  # noqa: S310
                return True
        except Exception:  # noqa: BLE001 - any failure means "not reachable"
            return False
    return False
