"""Registry query layer for the unified plugin catalog (Issue #478).

Neutral, plugins-free core for everything that *reads* the unified plugin
catalog (``config/plugin-catalog.yaml``) and resolves registry-backed
activation:

* catalog loading and kind filtering (``load_plugin_catalog``,
  ``plugins_of_kind``, ``_activation_from_config`` — moved verbatim from
  ``lib.plugins``),
* the mcp-server slice (``load_mcp_registry``, ``resolve_active_mcp_servers``,
  ``build_mcp_guardrails_list``, ``SECRETS_LOCAL_FILE`` — moved verbatim from
  ``lib.mcp_registry``),
* the cli-tool slice (``load_external_tools_registry``,
  ``_validate_permitted_injections``, ``_tool_is_active``,
  ``resolve_active_external_tools`` — moved verbatim from
  ``lib.external_tools``).

Dependency inversion (Issue #478): this module depends only on
:mod:`lib.io`. The former bidirectional needs are dissolved —

* ``mcp_registry`` / ``external_tools`` imported the catalog core *from*
  ``plugins`` while ``plugins`` lazily imported their ``resolve_active_*``
  functions back (plugins ↔ mcp_registry ↔ plugins 3-cycle),
* ``rules``, ``mcp_provider_config`` and ``external_tools_drift`` lazily
  reached into ``mcp_registry``/``mcp``.

Now every consumer (``plugins``, ``rules``, ``mcp``,
``mcp_provider_config``, ``external_tools``, ``external_tools_drift``)
imports the resolution layer from here at module top level, and nothing in
this module's import closure reaches back to any of them — the top-level
import graph stays a DAG (guarded by tests/test_import_acyclicity.py).

``mcp_registry`` / ``external_tools`` / ``plugins`` remain as thin facades
re-exporting these names so every historical import path
(``from lib.mcp import resolve_active_mcp_servers``, issue #613 ABI;
``from lib.plugins import load_plugin_catalog``; ``from lib.external_tools
import resolve_active_external_tools``) keeps working unchanged.
"""
from __future__ import annotations

from pathlib import Path

from .io import (
    SyncError,
    _deep_merge,
    _load_yaml_or_json,
    _normalize_enabled_config,
)

PLUGIN_CATALOG_YAML = "config/plugin-catalog.yaml"

SECRETS_LOCAL_FILE = ".meta-config/secrets.local.yaml"


# ---------------------------------------------------------------------------
# Unified plugin catalog core (moved verbatim from lib.plugins, #478)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# MCP registry slice (moved verbatim from lib.mcp_registry, #478)
# ---------------------------------------------------------------------------

def load_mcp_registry(agent_meta_root: Path, config: dict | None = None, project_root: Path | None = None) -> dict:
    """Return the mcp-server slice of the unified plugin catalog (same shape as
    the old config/mcp-registry.yaml `mcp-servers` map)."""
    catalog = load_plugin_catalog(agent_meta_root=agent_meta_root, config=config, project_root=project_root)
    return plugins_of_kind(catalog, "mcp-server")


def resolve_active_mcp_servers(
    config: dict, agent_meta_root: Path, project_root: Path | None = None,
    registry: dict | None = None,
) -> list[str]:
    """Determine which MCP servers are active for this project.

    Sources (merged, preserving order, no duplicates):
      1. Explicit: the unified `plugins:` block in project.yaml (or the legacy
         `mcp-servers` list for un-migrated projects) — servers flagged
         enabled: true are always active
      2. Implicit: platform bundles rules/2-platform/<platform>-mcp.yaml —
         only active when the server's enabled-by-default flag is true (default: true)

    Servers from bundles not in the explicit list are skipped when
    enabled-by-default: false in the catalog.

    registry: pass an already-loaded load_mcp_registry() result to skip
    re-reading/re-parsing the plugin catalog when the caller has one on hand
    (e.g. sync.py's per-provider loop, which would otherwise reload the same
    on-disk catalog once per active provider).
    """
    if registry is None:
        registry = load_mcp_registry(agent_meta_root, config, project_root)
    if config.get("plugins") is not None:
        activation = _activation_from_config(config)
        ordered = [pid for pid, v in activation.items()
                   if v.get("enabled") and pid in registry]
    else:
        ordered = list(config.get("mcp-servers", []))
    explicit: set[str] = set(ordered)
    active: list[str] = list(ordered)

    platform_dir = agent_meta_root / "rules" / "2-platform"
    for platform in config.get("platforms", []):
        bundle_path = platform_dir / f"{platform}-mcp.yaml"
        if not bundle_path.exists():
            continue
        data, _ = _load_yaml_or_json(bundle_path)
        for server in (data or {}).get("mcp-servers", []):
            if server in active:
                continue
            if server in explicit:
                # already in active list (should not happen, but guard anyway)
                continue
            server_def = registry.get(server, {})
            if server_def.get("enabled-by-default", True):
                active.append(server)

    return active


def build_mcp_guardrails_list(registry: dict, active_servers: list[str]) -> str:
    """Render the hard-prohibitions bullet list for rules/1-generic/mcp-guardrails.md.

    Generated from each active server's tools.blocked (config/plugin-catalog.yaml)
    instead of being hand-copied — a server added/removed from the active list,
    or a blocked-tools edit, is picked up on the next sync instead of silently
    going stale in a hand-authored always-on guardrail file.
    """
    lines = [
        f"- **{name}:** " + ", ".join(f"`{t}`" for t in blocked) + " — absolut verboten."
        for name in sorted(active_servers)
        if (blocked := (registry.get(name, {}).get("tools", {}).get("blocked", [])))
    ]
    if not lines:
        return "- (keine aktiven MCP-Server mit gesperrten Tools)"
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# External-tools (cli-tool) slice — moved verbatim from lib.external_tools
# ---------------------------------------------------------------------------

_INJECTION_KINDS_NAME = {"skill", "hook", "rule"}
_INJECTION_KINDS_PATH = {"config", "other"}


def _validate_permitted_injections(tool_name: str, entries: list[dict]) -> None:
    """Validate a tool's ``permitted-injections`` list.

    kind in {skill, hook, rule} requires 'name' (provider-relative);
    kind in {config, other} requires an explicit 'path'. Mixing either
    field with the wrong kind group is a SyncError.
    """
    if not isinstance(entries, list):
        raise SyncError(
            f"external-tools-registry: '{tool_name}'.permitted-injections must be a list"
        )
    for entry in entries:
        if not isinstance(entry, dict):
            raise SyncError(
                f"external-tools-registry: '{tool_name}'.permitted-injections entries must be objects"
            )
        kind = entry.get("kind")
        if kind not in _INJECTION_KINDS_NAME | _INJECTION_KINDS_PATH:
            raise SyncError(
                f"external-tools-registry: '{tool_name}'.permitted-injections has invalid "
                f"kind '{kind}' (expected one of skill, hook, rule, config, other)"
            )
        if kind in _INJECTION_KINDS_NAME:
            if not entry.get("name"):
                raise SyncError(
                    f"external-tools-registry: '{tool_name}'.permitted-injections entry "
                    f"with kind '{kind}' requires 'name'"
                )
            if entry.get("path"):
                raise SyncError(
                    f"external-tools-registry: '{tool_name}'.permitted-injections entry "
                    f"with kind '{kind}' must not set 'path' (use 'name')"
                )
        else:
            if not entry.get("path"):
                raise SyncError(
                    f"external-tools-registry: '{tool_name}'.permitted-injections entry "
                    f"with kind '{kind}' requires 'path'"
                )
            if entry.get("name"):
                raise SyncError(
                    f"external-tools-registry: '{tool_name}'.permitted-injections entry "
                    f"with kind '{kind}' must not set 'name' (use 'path')"
                )


def load_external_tools_registry(
    agent_meta_root: Path,
    config: dict | None = None,
    project_root: Path | None = None,
) -> dict:
    """Return the cli-tool slice of the unified plugin catalog.

    Loads config/plugin-catalog.yaml (with its own framework/project/inline
    deep-merge, see load_plugin_catalog) and filters to the
    ``cli-tool`` kind, giving the same flat {tool_name: tool_def} shape the
    old config/external-tools-registry.yaml `external-tools` map had. Each
    returned tool's permitted-injections list is validated eagerly.
    """
    catalog = load_plugin_catalog(agent_meta_root=agent_meta_root, config=config, project_root=project_root)
    registry = plugins_of_kind(catalog, "cli-tool")

    for tool_name, tool_def in registry.items():
        if isinstance(tool_def, dict) and "permitted-injections" in tool_def:
            _validate_permitted_injections(tool_name, tool_def["permitted-injections"])

    return registry


def _tool_is_active(name: str, merged_def: dict, project_tools: dict) -> bool:
    """Return True if an external tool should be rendered for this project.

    Precedence (mirrors skills._skill_is_active):
      1. Explicit project setting: project_tools[name]['enabled'] (true OR
         false) always wins, independent of the registry default.
      2. Otherwise: merged_def['enabled-by-default'] (framework value, possibly
         replaced via an external-tools-registry project override).
      3. Fallback: False — external CLI tools are opt-in.
    """
    if name in project_tools and "enabled" in project_tools[name]:
        return bool(project_tools[name]["enabled"])
    if "enabled-by-default" in merged_def:
        return bool(merged_def["enabled-by-default"])
    return False


def resolve_active_external_tools(
    config: dict,
    agent_meta_root: Path,
    project_root: Path | None = None,
    registry: dict | None = None,
) -> list[str]:
    """Determine which external tools are active for this project.

    Returns tool names (registry order) for which _tool_is_active is True.
    Tools named in the project config but absent from the registry are skipped
    — without a registry definition there is no rule-content to render.

    registry: pass an already-loaded load_external_tools_registry() result to
    skip re-reading/re-parsing the plugin catalog when the caller has one on
    hand.
    """
    if registry is None:
        registry = load_external_tools_registry(agent_meta_root, config, project_root)
    if (config or {}).get("plugins") is not None:
        project_tools = _activation_from_config(config)
    else:
        project_tools = _normalize_enabled_config((config or {}).get("external-tools", {}))

    active: list[str] = []
    for name, tool_def in registry.items():
        if not isinstance(tool_def, dict):
            continue
        if _tool_is_active(name, tool_def, project_tools):
            active.append(name)
    return active
