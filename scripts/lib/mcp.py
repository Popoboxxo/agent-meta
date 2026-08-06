"""MCP framework: server registry, rule generation, gitignore management,
provider config generation and secrets template initialisation.

Public interface:
    load_mcp_registry(agent_meta_root)              → dict of server definitions
    resolve_active_mcp_servers(config, root)        → list of active server names
    generate_mcp_artifacts(...)                     → writes rule + provider config files,
                                                      returns gitignore entries
    sync_secrets_template(...)                       → creates/updates .meta-config/secrets.local.yaml
"""

import json
import re
from pathlib import Path

from .io import (
    _load_yaml_or_json,
    read_json_lenient,
    safe_path,
    write_checked,
)
from .log import SyncLog

MCP_REGISTRY_YAML = "config/mcp-registry.yaml"
MCP_RULE_PREFIX = "mcp-"
SECRETS_LOCAL_FILE = ".meta-config/secrets.local.yaml"
# Fallback rules directory for providers without an explicit rules_dir (Claude).
# Mirrors rules.CLAUDE_RULES_DIR to keep MCP rule output aligned with sync_rules().
DEFAULT_RULES_DIR = ".claude/rules"


# ---------------------------------------------------------------------------
# Registry loading
# ---------------------------------------------------------------------------

def _deep_merge(dict1: dict, dict2: dict) -> dict:
    """Recursively merges dict2 into dict1."""
    for k, v in dict2.items():
        if isinstance(v, dict) and k in dict1 and isinstance(dict1[k], dict):
            _deep_merge(dict1[k], v)
        else:
            dict1[k] = v
    return dict1

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


# ---------------------------------------------------------------------------
# Server resolution
# ---------------------------------------------------------------------------

def resolve_active_mcp_servers(config: dict, agent_meta_root: Path, project_root: Path | None = None) -> list[str]:
    """Determine which MCP servers are active for this project.

    Sources (merged, preserving order, no duplicates):
      1. Explicit: config["mcp-servers"] list in project.yaml — always active
      2. Implicit: platform bundles rules/2-platform/<platform>-mcp.yaml —
         only active when the server's enabled-by-default flag is true (default: true)

    Servers from bundles not in the explicit list are skipped when
    enabled-by-default: false in mcp-registry.yaml.
    """
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
# Provider config generation helpers
# ---------------------------------------------------------------------------

def _subst(value: str, secrets: dict | None) -> str:
    """Replace {{VAR}} placeholders.

    secrets=None  → ${VAR}  (committed config — env var reference, safe to commit)
    secrets=dict  → actual value from dict, or ${VAR} if key absent/still empty
                    (secrets_template.py pre-fills new keys as "" — those must
                    keep falling back to the placeholder, not resolve to "")
    """
    def _replace(m: re.Match) -> str:
        var_name = m.group(1)
        if secrets is not None and secrets.get(var_name):
            return str(secrets[var_name])
        return f"${{{var_name}}}"
    return re.sub(r'\{\{([A-Z0-9_]+)\}\}', _replace, value)


def _subst_opencode(value: str, secrets: dict | None) -> str:
    """Replace {{VAR}} placeholders with opencode {env:VAR} syntax.

    secrets=None  → {env:VAR}  (committed config — env var reference)
    secrets=dict  → actual value from dict, or {env:VAR} if key absent/still empty
                    (see _subst — an unfilled "" placeholder must not resolve to "")
    """
    def _replace(m: re.Match) -> str:
        var_name = m.group(1)
        if secrets is not None and secrets.get(var_name):
            return str(secrets[var_name])
        return f"{{env:{var_name}}}"
    return re.sub(r'\{\{([A-Z0-9_]+)\}\}', _replace, value)


def _build_connection_entry(conn: dict, secrets: dict | None, fmt: str | None = None) -> dict:
    """Convert a registry connection block to a provider-config dict.

    fmt="opencode-json" uses opencode-specific syntax:
      - command as array (not command + args)
      - "environment" key (not "env")
      - {env:VAR} interpolation (not ${VAR})
    """
    conn_type = conn.get("type", "")
    orig_type = conn_type

    is_opencode = fmt == "opencode-json"
    if is_opencode:
        if conn_type == "sse":
            conn_type = "remote"
        elif conn_type == "stdio":
            conn_type = "local"

    entry: dict = {"type": conn_type}

    if is_opencode:
        entry["enabled"] = True

    if orig_type == "sse":
        raw_url = conn.get("url", "")
        if is_opencode:
            entry["url"] = _subst_opencode(raw_url, secrets)
        else:
            entry["url"] = _subst(raw_url, secrets)
        headers = conn.get("headers", {})
        if headers:
            if is_opencode:
                entry["headers"] = {k: _subst_opencode(str(v), secrets) for k, v in headers.items()}
            else:
                entry["headers"] = {k: _subst(str(v), secrets) for k, v in headers.items()}

    elif orig_type == "stdio":
        cmd = conn.get("command", "")
        args = list(conn.get("args", []))
        env = conn.get("env", {})

        if is_opencode:
            entry["command"] = [cmd] + args
            if env:
                entry["environment"] = {k: _subst_opencode(str(v), secrets) for k, v in env.items()}
        else:
            entry["command"] = cmd
            entry["args"] = args
            if env:
                entry["env"] = {k: _subst(str(v), secrets) for k, v in env.items()}

    return entry


def _build_mcp_entries(
    active_servers: list[str],
    registry: dict,
    secrets: dict | None,
    fmt: str | None = None,
    provider: str = "",
) -> dict:
    """Build a {server_name: config_dict} map for insertion into provider configs.
    
    Respects per-server provider-skip: when a server lists the current provider
    in its provider-skip list, it is omitted (e.g. Honcho plugin for Opencode).
    """
    entries: dict = {}
    for server_name in active_servers:
        server_def = registry.get(server_name)
        if not server_def:
            continue
        skip = server_def.get("provider-skip", [])
        if isinstance(skip, list) and provider in skip:
            continue
        conn = server_def.get("connection")
        if not conn:
            continue
        entries[server_name] = _build_connection_entry(conn, secrets, fmt)
    return entries


def _read_json_lenient(path: Path) -> dict | None:
    """Read a JSON file, tolerating JSONC comments and trailing commas."""
    return read_json_lenient(path)


def _update_json_config(
    path: Path,
    mcp_key: str,
    mcp_entries: dict,
    log: SyncLog,
    dry_run: bool,
    allow_secrets: bool,
    config: dict | None = None,
) -> None:
    """Merge mcp_entries into a JSON settings file under mcp_key.

    Reads the existing file (if any), updates the MCP key, writes clean JSON.
    Warns and skips if the file cannot be parsed.
    """
    rel = str(path.name)

    existing: dict = {}
    if path.exists():
        if path.stat().st_size == 0:
            # A zero-byte file is invalid JSON but not a real conflict —
            # self-heal to {} instead of silently skipping the injection
            # (audit #400, Secondary Finding A).
            existing = {}
        else:
            parsed = _read_json_lenient(path)
            if parsed is None:
                log.warning(
                    f"mcp: could not parse '{rel}' as JSON/JSONC — "
                    "MCP config not injected. Add mcpServers manually."
                )
                return
            existing = parsed

    # Bereinigung der Legacy-Keys wurde auf Wunsch des Users entfernt,
    # um manuelle Einträge in den Config-Dateien zu erhalten.

    existing[mcp_key] = mcp_entries
    content = json.dumps(existing, indent=2, ensure_ascii=False) + "\n"
    str(path.relative_to(path.parent.parent)) if path.parent.name else rel

    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
    if write_checked(path, content, log, rel, allow_secrets=allow_secrets, config=config, dry_run=dry_run):
        log.action("WRITE", rel, f"mcp-registry → {mcp_key}")
    else:
        log.skip(rel, "unchanged")


def _update_continue_yaml_config(
    path: Path,
    mcp_entries: dict,
    log: SyncLog,
    dry_run: bool,
    allow_secrets: bool,
    config: dict | None = None,
) -> None:
    """Merge mcpServers into a Continue config.yaml file.

    Injects a managed block so the section can be updated on subsequent syncs.
    User model and other settings are left untouched.
    """
    try:
        import yaml as _yaml
    except ImportError:
        log.warning("mcp: PyYAML not installed — skipping Continue MCP config generation")
        return

    BLOCK_BEGIN = "# agent-meta:mcp-begin"
    BLOCK_END = "# agent-meta:mcp-end"

    rel = str(path.name)

    # Build the managed block content
    _yaml.dump(
        {"mcpServers": list(mcp_entries.values())},
        allow_unicode=True, default_flow_style=False, sort_keys=False,
    )
    # Annotate with server names as comments
    server_lines: list[str] = []
    for server_name, entry in mcp_entries.items():
        server_yaml = _yaml.dump(
            {server_name: entry},
            allow_unicode=True, default_flow_style=False, sort_keys=False,
        )
        server_lines.append(server_yaml.rstrip())

    block_content = (
        f"{BLOCK_BEGIN}\n"
        "# Generated by agent-meta — do not edit manually.\n"
        "mcpServers:\n"
    )
    for server_name, entry in mcp_entries.items():
        entry_yaml = _yaml.dump(
            entry, allow_unicode=True, default_flow_style=False, sort_keys=False,
        )
        # Indent each line by 2 spaces and prepend the server name
        block_content += f"  - name: {server_name}\n"
        for line in entry_yaml.splitlines():
            if line.strip():
                block_content += f"    {line}\n"
    block_content += BLOCK_END

    if path.exists():
        existing = path.read_text(encoding="utf-8")
        block_re = re.compile(
            rf"^{re.escape(BLOCK_BEGIN)}.*?^{re.escape(BLOCK_END)}",
            re.MULTILINE | re.DOTALL,
        )
        if block_re.search(existing):
            new_content = block_re.sub(block_content, existing, count=1)
        else:
            new_content = existing.rstrip("\n") + "\n\n" + block_content + "\n"
    else:
        new_content = block_content + "\n"

    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
    if write_checked(path, new_content, log, rel, allow_secrets=allow_secrets, config=config, dry_run=dry_run):
        log.action("WRITE", rel, "mcp-registry → mcpServers")
    else:
        log.skip(rel, "unchanged")


# ---------------------------------------------------------------------------
# Provider config generation — main entry point
# ---------------------------------------------------------------------------

def _warn_stale_mcp_servers_key(
    project_root: Path,
    provider_cfg: dict,
    committed_file: str,
    secrets_file: str | None,
    log: SyncLog,
) -> None:
    """Warn once if a leftover mcpServers key sits in a file no longer targeted.

    Migration aid for #388/#400: projects synced before Claude's mcp-config
    moved to .mcp.json can have an inert `mcpServers` block still sitting in
    settings.json/settings.local.json. sync.py deliberately never strips
    unrelated keys from those files (manual entries must survive a sync), so
    this leftover has to be pointed out instead of silently cleaned up.
    """
    current_targets = {committed_file, secrets_file}
    for key in ("settings_file", "settings_local_file"):
        stale_rel = provider_cfg.get(key)
        if not stale_rel or stale_rel in current_targets:
            continue
        stale_path = safe_path(project_root, stale_rel)
        if not stale_path.exists():
            continue
        parsed = _read_json_lenient(stale_path)
        if isinstance(parsed, dict) and "mcpServers" in parsed:
            log.warning(
                f"mcp: '{stale_rel}' still has a leftover 'mcpServers' key from "
                f"before MCP config moved to '{committed_file}' — it has no "
                "effect there and can be removed manually."
            )


def generate_provider_configs(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    provider_config: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    allow_committed_secrets: bool = False,
) -> None:
    """Generate committed and local MCP provider config files.

    For the committed file: substitutes {{VAR}} → ${VAR} (safe env-var references).
    For the local/secrets file: substitutes {{VAR}} → actual value from secrets.local.yaml
    (only generated when secrets.local.yaml exists).

    Raises SyncError if actual secrets are found in committed content and
    allow_committed_secrets is False.
    """
    registry = load_mcp_registry(agent_meta_root, config, project_root)
    if not registry:
        return

    active_servers = resolve_active_mcp_servers(config, agent_meta_root, project_root)
    if not active_servers:
        return

    pc = provider_config.get(provider, {})
    mcp_cfg = pc.get("mcp-config", {})
    if not mcp_cfg:
        return

    fmt = mcp_cfg.get("format")
    committed_file = mcp_cfg.get("committed-file")
    secrets_file = mcp_cfg.get("secrets-file")

    if not fmt or not committed_file:
        return

    _warn_stale_mcp_servers_key(project_root, pc, committed_file, secrets_file, log)

    # Load secrets.local.yaml if present
    secrets_path = project_root / SECRETS_LOCAL_FILE
    secrets: dict | None = None
    if secrets_path.exists():
        secrets_data, _ = _load_yaml_or_json(secrets_path)
        secrets = secrets_data or {}

    committed_entries = _build_mcp_entries(active_servers, registry, secrets=None, fmt=fmt, provider=provider)
    local_entries = _build_mcp_entries(active_servers, registry, secrets=secrets, fmt=fmt, provider=provider) if secrets else {}

    # --- Committed provider config ---
    committed_path = safe_path(project_root, committed_file)
    _write_provider_config(
        path=committed_path,
        mcp_entries=committed_entries,
        fmt=fmt,
        log=log,
        dry_run=dry_run,
        allow_secrets=allow_committed_secrets,
        config=config,
    )

    # --- Local/secrets provider config (only when secrets.local.yaml exists) ---
    if secrets_file and local_entries:
        local_path = safe_path(project_root, secrets_file)
        _write_provider_config(
            path=local_path,
            mcp_entries=local_entries,
            fmt=fmt,
            log=log,
            dry_run=dry_run,
            allow_secrets=True,  # local files are always gitignored
            config=config,
        )


def _write_provider_config(
    path: Path,
    mcp_entries: dict,
    fmt: str,
    log: SyncLog,
    dry_run: bool,
    allow_secrets: bool,
    config: dict | None = None,
) -> None:
    """Dispatch to format-specific writer."""
    if fmt in ("claude-settings", "gemini-settings"):
        _update_json_config(path, "mcpServers", mcp_entries, log, dry_run, allow_secrets, config=config)
    elif fmt == "opencode-json":
        _update_json_config(path, "mcp", mcp_entries, log, dry_run, allow_secrets, config=config)
    elif fmt == "continue-yaml":
        _update_continue_yaml_config(path, mcp_entries, log, dry_run, allow_secrets, config=config)
    else:
        log.warning(f"mcp: unknown provider format '{fmt}' — skipping config generation for {path.name}")


# ---------------------------------------------------------------------------
# Secrets template sync (runs on every sync.py invocation)
# ---------------------------------------------------------------------------

def _required_secrets_by_server(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
) -> dict[str, list[str]]:
    """Map active MCP server → its declared `secrets:` list, skipping servers without any."""
    registry = load_mcp_registry(agent_meta_root, config, project_root)
    if not registry:
        return {}

    active_servers = resolve_active_mcp_servers(config, agent_meta_root, project_root)
    if not active_servers:
        return {}

    required: dict[str, list[str]] = {}
    for server_name in active_servers:
        server_def = registry.get(server_name)
        if not server_def:
            continue
        secrets = server_def.get("secrets", [])
        if secrets:
            required[server_name] = secrets
    return required


def _render_secrets_template(required: dict[str, list[str]]) -> str:
    """Build full secrets.local.yaml content (header + one block per server)."""
    lines: list[str] = [
        "# MCP Secrets — lokale Konfiguration",
        "# ====================================",
        "# NIEMALS committen. Diese Datei ist gitignored.",
        "# Nur Einträge befüllen die im Projekt aktiv genutzt werden.",
        "# Danach: python .agent-meta/scripts/sync.py",
        "",
    ]
    for server_name, secrets in required.items():
        lines.append(f"# ── {server_name} ──")
        for secret in secrets:
            lines.append(f'{secret}: ""')
        lines.append("")
    return "\n".join(lines)


def sync_secrets_template(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Keep .meta-config/secrets.local.yaml prepared for every active MCP server.

    Runs on every sync.py invocation (not just --init), so activating a new MCP
    server (e.g. via /add-mcp-server) immediately preps its required env vars as
    empty placeholders — the "Env Dialog" doesn't need to be filled out by hand
    from mcp-registry.yaml.

    - File missing: write the full template.
    - File exists: append only the secret keys of newly-active servers that
      aren't declared yet. Existing keys/values/comments are never touched or
      reordered, so filled-in secrets survive re-syncs untouched.
    """
    required = _required_secrets_by_server(agent_meta_root, project_root, config)
    if not required:
        return

    target_path = project_root / SECRETS_LOCAL_FILE

    if not target_path.exists():
        content = _render_secrets_template(required)
        log.action("INIT", SECRETS_LOCAL_FILE, "MCP secrets template (gitignored)")
        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")
        return

    existing_data, _ = _load_yaml_or_json(target_path)
    existing_keys = set((existing_data or {}).keys())

    added_lines: list[str] = []
    added_count = 0
    for server_name, secrets in required.items():
        missing = [s for s in secrets if s not in existing_keys]
        if not missing:
            continue
        added_lines.append(f"# ── {server_name} (neu aktiviert) ──")
        for secret in missing:
            added_lines.append(f'{secret}: ""')
            added_count += 1
        added_lines.append("")

    if not added_lines:
        log.skip(SECRETS_LOCAL_FILE, "all required secrets already present")
        return

    log.action(
        "UPDATE", SECRETS_LOCAL_FILE,
        f"appended {added_count} new secret key(s) for newly active MCP server(s)",
    )
    if dry_run:
        return

    existing_text = target_path.read_text(encoding="utf-8")
    if not existing_text.endswith("\n"):
        existing_text += "\n"
    target_path.write_text(
        existing_text + "\n" + "\n".join(added_lines).rstrip() + "\n",
        encoding="utf-8",
    )


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
    allow_committed_secrets: bool = False,
) -> list[str]:
    """Generate MCP rule files + provider configs for all active servers.

    For each active server (from project.yaml + platform bundles):
      - Writes mcp-<server>.md into the provider's rules_dir (if has_rules)
      - Writes/updates committed provider config with ${ENV_VAR} references
      - Writes/updates local provider config with actual values (if secrets.local.yaml exists)

    Returns a list of paths to add to the .gitignore managed block:
      - Provider-specific secrets-file (from ai-providers.yaml mcp-config)
      - .meta-config/secrets.local.yaml (central secret store)
    """
    registry = load_mcp_registry(agent_meta_root, config, project_root)
    if not registry:
        return []

    active_servers = resolve_active_mcp_servers(config, agent_meta_root, project_root)
    if not active_servers:
        return []

    pc = provider_config.get(provider, {})

    # --- Rule file generation ---
    # Providers without an explicit rules_dir (e.g. Claude) fall back to the
    # default .claude/rules directory — mirrors sync_rules() in rules.py.
    effective_rules_dir = rules_dir or DEFAULT_RULES_DIR
    if pc.get("has_rules"):
        target_dir = project_root / effective_rules_dir
        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)

        for server_name in active_servers:
            server_def = registry.get(server_name)
            if not server_def:
                log.warning(f"mcp: server '{server_name}' not in registry — skipping rule generation")
                continue

            filename = f"{MCP_RULE_PREFIX}{server_name}.md"
            target_path = safe_path(target_dir, filename)
            content = _generate_rule_content(server_name, server_def)
            rel_out = str(target_path.relative_to(project_root))
            src_label = f"mcp-registry/{server_name}"

            if write_checked(target_path, content, log, src_label, config=config, dry_run=dry_run):
                log.action("WRITE", rel_out, src_label)
            else:
                log.skip(rel_out, "unchanged")

    # --- Provider config generation ---
    generate_provider_configs(
        agent_meta_root=agent_meta_root,
        project_root=project_root,
        config=config,
        provider_config=provider_config,
        log=log,
        dry_run=dry_run,
        provider=provider,
        allow_committed_secrets=allow_committed_secrets,
    )

    # --- Gitignore entries ---
    gitignore_extras: list[str] = []
    secrets_file = pc.get("mcp-config", {}).get("secrets-file")
    if secrets_file:
        gitignore_extras.append(secrets_file)

    gitignore_extras.append(SECRETS_LOCAL_FILE)

    return gitignore_extras
