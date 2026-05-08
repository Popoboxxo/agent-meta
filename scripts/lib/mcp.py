"""MCP framework: server registry, rule generation, gitignore management.

Public interface:
    load_mcp_registry(agent_meta_root)         → dict of server definitions
    resolve_active_mcp_servers(config, root)   → list of active server names
    generate_mcp_artifacts(...)                → writes rule files, returns gitignore entries
"""

from pathlib import Path

from .io import _load_yaml_or_json, safe_path, write_checked
from .log import SyncLog

MCP_REGISTRY_YAML = "config/mcp-registry.yaml"
MCP_RULE_PREFIX = "mcp-"
SECRETS_LOCAL_FILE = ".meta-config/secrets.local.yaml"


# ---------------------------------------------------------------------------
# Registry loading
# ---------------------------------------------------------------------------

def load_mcp_registry(agent_meta_root: Path) -> dict:
    """Load config/mcp-registry.yaml. Returns empty dict if file is absent."""
    data, _ = _load_yaml_or_json(agent_meta_root / MCP_REGISTRY_YAML)
    if not data:
        return {}
    return data.get("mcp-servers", {})


# ---------------------------------------------------------------------------
# Server resolution
# ---------------------------------------------------------------------------

def resolve_active_mcp_servers(config: dict, agent_meta_root: Path) -> list[str]:
    """Determine which MCP servers are active for this project.

    Sources (merged, preserving order, no duplicates):
      1. Explicit: config["mcp-servers"] list in project.yaml
      2. Implicit: platform bundles rules/2-platform/<platform>-mcp.yaml

    A platform bundle is loaded for every platform in config["platforms"].
    Servers from bundles are appended after explicit servers.
    """
    active: list[str] = list(config.get("mcp-servers", []))

    platform_dir = agent_meta_root / "rules" / "2-platform"
    for platform in config.get("platforms", []):
        bundle_path = platform_dir / f"{platform}-mcp.yaml"
        if not bundle_path.exists():
            continue
        data, _ = _load_yaml_or_json(bundle_path)
        for server in (data or {}).get("mcp-servers", []):
            if server not in active:
                active.append(server)

    return active


# ---------------------------------------------------------------------------
# Rule content generation
# ---------------------------------------------------------------------------

def _generate_rule_content(server_name: str, server_def: dict) -> str:
    """Build Markdown rule content for one MCP server from registry definition."""
    lines: list[str] = []

    desc = server_def.get("description", server_name)
    lines += [f"# MCP: {server_name}", "", f"> {desc}", "", "---", ""]

    tools = server_def.get("tools", {})
    allowed = tools.get("allowed", [])
    blocked = tools.get("blocked", [])

    if allowed:
        lines += ["## Erlaubte Tools", ""]
        lines += [f"- `{t}`" for t in allowed]
        lines.append("")

    if blocked:
        lines += ["## Verbotene Tools (ABSOLUT — keine Ausnahmen)", ""]
        lines += [f"- `{t}`" for t in blocked]
        lines.append("")

    hint = (server_def.get("agent-hint") or "").strip()
    if hint:
        lines += ["## Agent-Hinweise", "", hint, ""]

    conn = server_def.get("connection", {})
    if conn:
        conn_type = conn.get("type", "")
        lines += ["## Verbindungstyp", ""]
        lines.append(f"- Typ: `{conn_type}`")
        if conn_type == "sse":
            lines.append(f"- URL: `{conn.get('url', '')}` — Wert aus `secrets.local.yaml`")
        elif conn_type == "stdio":
            cmd = conn.get("command", "")
            args = " ".join(str(a) for a in conn.get("args", []))
            lines.append(f"- Kommando: `{cmd} {args}`")
        lines.append("")

    lines += [
        "---",
        "",
        "*Generiert von agent-meta aus `config/mcp-registry.yaml` — nicht manuell bearbeiten.*",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Artifact generation — main entrypoint called by sync.py
# ---------------------------------------------------------------------------

def generate_mcp_artifacts(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    provider_config: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    rules_dir: str | None = None,
) -> list[str]:
    """Generate MCP rule files for all active servers.

    For each active server (from project.yaml + platform bundles):
      - Writes mcp-<server>.md into the provider's rules_dir (if has_rules)

    Returns a list of paths to add to the .gitignore managed block:
      - Provider-specific secrets-file (from ai-providers.yaml mcp-config)
      - .meta-config/secrets.local.yaml (central secret store)
    """
    registry = load_mcp_registry(agent_meta_root)
    if not registry:
        return []

    active_servers = resolve_active_mcp_servers(config, agent_meta_root)
    if not active_servers:
        return []

    pc = provider_config.get(provider, {})

    if pc.get("has_rules") and rules_dir:
        target_dir = project_root / rules_dir
        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)

        for server_name in active_servers:
            server_def = registry.get(server_name)
            if not server_def:
                log.warn(f"mcp: server '{server_name}' not in registry — skipping rule generation")
                continue

            filename = f"{MCP_RULE_PREFIX}{server_name}.md"
            target_path = safe_path(target_dir, filename)
            content = _generate_rule_content(server_name, server_def)
            rel_out = str(target_path.relative_to(project_root))
            src_label = f"mcp-registry/{server_name}"

            if not dry_run:
                if write_checked(target_path, content, log, src_label):
                    log.action("WRITE", rel_out, src_label)
                else:
                    log.skip(rel_out, "unchanged")
            else:
                log.action("WRITE", rel_out, src_label)

    # Collect gitignore entries for this provider's MCP secrets file
    gitignore_extras: list[str] = []
    secrets_file = pc.get("mcp-config", {}).get("secrets-file")
    if secrets_file:
        gitignore_extras.append(secrets_file)

    # Central secrets store — always gitignored when MCP is active
    gitignore_extras.append(SECRETS_LOCAL_FILE)

    return gitignore_extras
