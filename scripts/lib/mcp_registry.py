"""Neutral MCP registry core: loading ``config/mcp-registry.yaml``, resolving
which servers are active for a project, and building the guardrails bullet
list — used by both :mod:`mcp` (rule/provider-config generation) and
:mod:`rules` (``resolve_rules``'s ``MCP_GUARDRAILS_LIST`` variable).

Split out of ``mcp.py`` (issue #613) to break the ``mcp ↔ mcp_provider_config
↔ rules`` import cycle: both other modules only ever needed this
registry-lookup slice, not the rule/provider-config generation machinery, so
extracting it here (mirrors the ``variables.py``/``frontmatter.py`` precedent
from Wave 6) lets ``mcp_provider_config`` and ``rules`` depend on it directly
instead of reaching into ``mcp`` and creating a cycle. ``mcp.py`` re-exports
these names for backward compatibility — existing callers keep importing
them via ``from .mcp import ...``.
"""
from __future__ import annotations

from pathlib import Path

from .io import _deep_merge, _load_yaml_or_json

MCP_REGISTRY_YAML = "config/mcp-registry.yaml"
SECRETS_LOCAL_FILE = ".meta-config/secrets.local.yaml"


def load_mcp_registry(agent_meta_root: Path, config: dict | None = None, project_root: Path | None = None) -> dict:
    """Load config/mcp-registry.yaml and deep-merge with project-specific mcp-registry (if provided)."""
    data, _ = _load_yaml_or_json(agent_meta_root / MCP_REGISTRY_YAML)
    registry = {}
    if data and isinstance(data, dict):
        registry = data.get("mcp-servers", {})
        if not isinstance(registry, dict):
            registry = {}

    if project_root:
        proj_data, _ = _load_yaml_or_json(project_root / ".meta-config" / "mcp-registry.yaml")
        if proj_data and isinstance(proj_data, dict):
            proj_servers = proj_data.get("mcp-servers", proj_data)
            if isinstance(proj_servers, dict):
                _deep_merge(registry, proj_servers)

    if config:
        project_registry = config.get("mcp-registry", {})
        if isinstance(project_registry, dict):
            _deep_merge(registry, project_registry)

    return registry


def resolve_active_mcp_servers(
    config: dict, agent_meta_root: Path, project_root: Path | None = None,
    registry: dict | None = None,
) -> list[str]:
    """Determine which MCP servers are active for this project.

    Sources (merged, preserving order, no duplicates):
      1. Explicit: config["mcp-servers"] list in project.yaml — always active
      2. Implicit: platform bundles rules/2-platform/<platform>-mcp.yaml —
         only active when the server's enabled-by-default flag is true (default: true)

    Servers from bundles not in the explicit list are skipped when
    enabled-by-default: false in mcp-registry.yaml.

    registry: pass an already-loaded load_mcp_registry() result to skip
    re-reading/re-parsing config/mcp-registry.yaml when the caller has one
    on hand (e.g. sync.py's per-provider loop, which would otherwise reload
    the same on-disk registry once per active provider).
    """
    if registry is None:
        registry = load_mcp_registry(agent_meta_root, config, project_root)
    explicit: set[str] = set(config.get("mcp-servers", []))
    active: list[str] = list(config.get("mcp-servers", []))

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

    Generated from each active server's tools.blocked (config/mcp-registry.yaml)
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
