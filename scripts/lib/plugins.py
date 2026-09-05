"""Unified plugin catalog: loads config/plugin-catalog.yaml (kind-discriminated
mcp-server / cli-tool entries), resolves which plugins are active for a project,
decides the per-provider compact/full channel, and runs a cheap availability
probe. Replaces the two separate registry loaders (config/mcp-registry.yaml,
config/external-tools-registry.yaml) — see mcp_registry.py / external_tools.py,
whose loaders now source from here (kind-filtered) so rendered artifacts stay
byte-identical.
"""
from __future__ import annotations

import shutil
import urllib.request
from pathlib import Path

from .io import _deep_merge, _load_yaml_or_json, _normalize_enabled_config

PLUGIN_CATALOG_YAML = "config/plugin-catalog.yaml"


def load_plugin_catalog(
    agent_meta_root: Path,
    config: dict | None = None,
    project_root: Path | None = None,
) -> dict:
    """Load config/plugin-catalog.yaml and deep-merge project overrides.

    Sources (later wins, deep-merged):
      1. Framework: <agent_meta_root>/config/plugin-catalog.yaml
      2. Project:   <project_root>/.meta-config/plugin-catalog.yaml
      3. Inline:    config["plugin-catalog"] from project.yaml
    Returns a flat {plugin_id: plugin_def} dict.
    """
    data, _ = _load_yaml_or_json(agent_meta_root / PLUGIN_CATALOG_YAML)
    catalog: dict = {}
    if data and isinstance(data, dict):
        catalog = data.get("plugins", {})
        if not isinstance(catalog, dict):
            catalog = {}

    if project_root:
        proj_data, _ = _load_yaml_or_json(project_root / ".meta-config" / "plugin-catalog.yaml")
        if proj_data and isinstance(proj_data, dict):
            proj_plugins = proj_data.get("plugins", proj_data)
            if isinstance(proj_plugins, dict):
                _deep_merge(catalog, proj_plugins)

    if config:
        inline = config.get("plugin-catalog", {})
        if isinstance(inline, dict):
            _deep_merge(catalog, inline)

    return catalog


def plugins_of_kind(catalog: dict, kind: str) -> dict:
    """Return the subset of catalog whose 'kind' discriminator equals kind."""
    return {
        pid: pdef
        for pid, pdef in catalog.items()
        if isinstance(pdef, dict) and pdef.get("kind") == kind
    }


def _plugin_is_active(plugin_id: str, plugin_def: dict, activation: dict) -> bool:
    """True if plugin should render. Mirrors external_tools._tool_is_active:
    explicit project activation[plugin_id]['enabled'] wins, else the catalog's
    enabled-by-default, else False (opt-in)."""
    if plugin_id in activation and "enabled" in activation[plugin_id]:
        return bool(activation[plugin_id]["enabled"])
    if "enabled-by-default" in plugin_def:
        return bool(plugin_def["enabled-by-default"])
    return False


def _activation_from_config(config: dict) -> dict:
    """Resolve the canonical activation dict. Prefers the unified `plugins:`
    block; falls back to the legacy `mcp-servers:` list + `external-tools:`
    dict for un-migrated project.yaml files."""
    plugins_cfg = config.get("plugins")
    if plugins_cfg is not None:
        return _normalize_enabled_config(plugins_cfg)
    legacy = {s: {"enabled": True} for s in config.get("mcp-servers", []) or []}
    legacy.update(_normalize_enabled_config(config.get("external-tools", {})))
    return legacy


def resolve_active_plugins(
    config: dict,
    agent_meta_root: Path,
    project_root: Path | None = None,
    catalog: dict | None = None,
) -> list[str]:
    """All active plugin ids (any kind), catalog order. Used by the browse/probe/
    scout/test features — NOT by artifact generation (those keep the per-kind
    resolvers whose order is byte-identity-sensitive)."""
    if catalog is None:
        catalog = load_plugin_catalog(config=config, agent_meta_root=agent_meta_root, project_root=project_root)
    activation = _activation_from_config(config)
    return [pid for pid, pdef in catalog.items()
            if isinstance(pdef, dict) and _plugin_is_active(pid, pdef, activation)]


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
