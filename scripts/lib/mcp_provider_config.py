"""MCP provider-config generation: JSON/YAML mcp-server entries for each
provider's committed + local secrets config files.

Split out of ``mcp.py`` (module size limit — see CLAUDE.md "Python
(scripts/lib/)" conventions, <= 600 lines per module) to keep registry
loading / rule-doc generation / secrets-template bookkeeping in that module
separate from the provider-config-writing concern here. This module imports
the registry helpers it needs from ``.mcp`` only inside function bodies
(deferred import) — ``mcp.py`` imports ``generate_provider_configs`` from
here at its own top level, so a top-level import in the other direction here
would be a circular import.

Public interface:
    generate_provider_configs(...)  → writes committed + local MCP provider
                                       config files for one provider
"""
from __future__ import annotations

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
from .toml_writer import dumps as _toml_dumps

# ---------------------------------------------------------------------------
# Provider config generation helpers
# ---------------------------------------------------------------------------

def _subst_with_placeholder(value: str, secrets: dict | None, placeholder) -> str:
    """Replace {{VAR}} placeholders, shared by _subst() and _subst_opencode() (#586).

    secrets=None  → placeholder(var_name)  (committed config — env var reference, safe to commit)
    secrets=dict  → actual value from dict, or placeholder(var_name) if key
                    absent/still empty (secrets_template.py pre-fills new keys
                    as "" — those must keep falling back to the placeholder,
                    not resolve to "")
    """
    def _replace(m: re.Match) -> str:
        var_name = m.group(1)
        if secrets is not None and secrets.get(var_name):
            return str(secrets[var_name])
        return placeholder(var_name)
    return re.sub(r'\{\{([A-Z0-9_]+)\}\}', _replace, value)


def _subst(value: str, secrets: dict | None) -> str:
    """Replace {{VAR}} placeholders with ${VAR} (shell/committed-config syntax)."""
    return _subst_with_placeholder(value, secrets, lambda var_name: f"${{{var_name}}}")


def _subst_opencode(value: str, secrets: dict | None) -> str:
    """Replace {{VAR}} placeholders with opencode {env:VAR} syntax."""
    return _subst_with_placeholder(value, secrets, lambda var_name: f"{{env:{var_name}}}")


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


def _config_rel_label(path: Path) -> str:
    """Log label for a provider config file: include the containing directory
    when there is one, so sibling configs (.vscode/mcp.json vs .cursor/mcp.json)
    stay distinguishable in sync.log instead of both reading as "mcp.json".
    """
    rel = str(path.name)
    if path.parent.name:
        rel = str(path.relative_to(path.parent.parent))
    return rel


def _read_existing_json_dict(path: Path, rel: str, log: SyncLog) -> dict | None:
    """Read an existing JSON provider config, tolerating empty/unparseable files.

    Returns {} when the file is missing or zero-byte (a zero-byte file is
    invalid JSON but not a real conflict — self-heal to {} instead of silently
    skipping the injection, audit #400 Secondary Finding A), the parsed dict
    otherwise, and None when the content is not a JSON object (a warning has
    already been emitted — the caller must skip to avoid data loss).
    """
    if path.exists() and path.stat().st_size > 0:
        parsed = _read_json_lenient(path)
        if not isinstance(parsed, dict):
            log.warning(
                f"mcp: could not parse '{rel}' as a JSON object — "
                "MCP config not injected. Add mcpServers manually."
            )
            return None
        return parsed
    return {}


def _write_json_config(
    path: Path,
    data: dict,
    rel: str,
    log: SyncLog,
    dry_run: bool,
    allow_secrets: bool,
    config: dict | None,
    verify_gitignored: bool,
    log_label: str,
) -> None:
    """Serialize a provider config dict as clean JSON and write it via write_checked."""
    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
    if write_checked(path, content, log, rel, allow_secrets=allow_secrets, config=config,
                     dry_run=dry_run, verify_gitignored=verify_gitignored):
        log.action("WRITE", rel, log_label)
    else:
        log.skip(rel, "unchanged")


def _update_json_config(
    path: Path,
    mcp_key: str,
    mcp_entries: dict,
    log: SyncLog,
    dry_run: bool,
    allow_secrets: bool,
    config: dict | None = None,
    verify_gitignored: bool = False,
) -> None:
    """Merge mcp_entries into a JSON settings file under mcp_key.

    Reads the existing file (if any), updates the MCP key, writes clean JSON.
    Warns and skips if the file cannot be parsed.
    """
    rel = _config_rel_label(path)
    existing = _read_existing_json_dict(path, rel, log)
    if existing is None:
        return

    # Bereinigung der Legacy-Keys wurde auf Wunsch des Users entfernt,
    # um manuelle Einträge in den Config-Dateien zu erhalten.

    existing[mcp_key] = mcp_entries
    _write_json_config(path, existing, rel, log, dry_run, allow_secrets, config,
                       verify_gitignored, f"mcp-registry → {mcp_key}")


def _update_zcode_json_config(
    path: Path,
    mcp_entries: dict,
    log: SyncLog,
    dry_run: bool,
    allow_secrets: bool,
    config: dict | None = None,
    verify_gitignored: bool = False,
) -> None:
    """Merge mcp_entries into .zcode/config.json under the NESTED mcp.servers key.

    ZCode reads workspace MCP servers from the nested `mcp.servers` key (V2),
    not from a top-level key. All other keys in the file (user model config
    etc.) are preserved; only `mcp.servers` is replaced wholesale.
    """
    rel = _config_rel_label(path)
    existing = _read_existing_json_dict(path, rel, log)
    if existing is None:
        return
    existing.setdefault("mcp", {})["servers"] = mcp_entries
    _write_json_config(path, existing, rel, log, dry_run, allow_secrets, config,
                       verify_gitignored, "mcp-registry → mcp.servers")


def _update_continue_yaml_config(
    path: Path,
    mcp_entries: dict,
    log: SyncLog,
    dry_run: bool,
    allow_secrets: bool,
    config: dict | None = None,
    verify_gitignored: bool = False,
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
    if write_checked(path, new_content, log, rel, allow_secrets=allow_secrets, config=config, dry_run=dry_run,
                      verify_gitignored=verify_gitignored):
        log.action("WRITE", rel, "mcp-registry → mcpServers")
    else:
        log.skip(rel, "unchanged")


# Bearer-token env indirection (V8): the committed placeholder form
# "Bearer ${VAR}" (the ${VAR} rendering of the registry's "Bearer {{VAR}}")
# becomes a Codex-native bearer_token_env_var reference to the bare env var.
_BEARER_PLACEHOLDER_RE = re.compile(r"^Bearer \$\{([A-Z0-9_]+)\}$")

CODEX_TOML_BLOCK_BEGIN = "# agent-meta:mcp-begin"
CODEX_TOML_BLOCK_END = "# agent-meta:mcp-end"


def _adapt_entry_for_codex(entry: dict) -> dict:
    """Adapt a generic MCP connection entry to Codex's config.toml schema.

    Codex has no `type` discriminator in [mcp_servers.<name>] tables — stdio
    vs. remote is implied by the presence of `command` vs. `url` — so the key
    is dropped. A committed `Authorization: Bearer ${VAR}` header is replaced
    by the native env-indirection key `bearer_token_env_var = "<VAR>"` (V8
    strategy: Codex has no include/import mechanism for a secrets file, so
    secrets are referenced through the environment instead). Any remaining
    headers stay under `headers` unchanged — the exact remaining-header key
    semantics Codex accepts are part of the P6 real-repo test (V8).
    """
    conn_type = entry.get("type", "")
    adapted = {k: v for k, v in entry.items() if k != "type"}
    if conn_type != "sse":
        return adapted

    headers = dict(adapted.pop("headers", None) or {})
    match = _BEARER_PLACEHOLDER_RE.match(str(headers.get("Authorization", "")))
    if match:
        del headers["Authorization"]
        adapted["bearer_token_env_var"] = match.group(1)
    if headers:
        adapted["headers"] = headers
    return adapted


def _update_codex_toml_config(
    path: Path,
    mcp_entries: dict,
    log: SyncLog,
    dry_run: bool,
    allow_secrets: bool,
    config: dict | None = None,
    verify_gitignored: bool = False,
) -> None:
    """Inject a managed [mcp_servers.*] block into a Codex config.toml file.

    Follows the managed-block pattern of _update_continue_yaml_config: the
    generated MCP tables live between comment markers so subsequent syncs
    replace them in place, while user content outside the block (model config,
    profiles, ...) is never reordered or rewritten. Codex has no
    include/import mechanism for a second TOML file (V8), so this committed
    block is the only MCP surface and carries ${VAR} env references directly.
    """
    rel = _config_rel_label(path)

    block_content = (
        f"{CODEX_TOML_BLOCK_BEGIN}\n"
        "# Generated by agent-meta — do not edit manually.\n"
    )
    if mcp_entries:
        adapted = {name: _adapt_entry_for_codex(entry) for name, entry in mcp_entries.items()}
        toml_block = _toml_dumps({"mcp_servers": adapted})
        # toml_writer emits an empty [mcp_servers] parent-table header before
        # the per-server sections; drop that leading line — each
        # [mcp_servers.<name>] header implicitly creates the parent table,
        # which keeps the block valid, tomllib-parseable TOML.
        lines = toml_block.splitlines()
        if lines and lines[0] == "[mcp_servers]":
            lines = lines[1:]
        block_content += "\n".join(lines) + "\n"
    block_content += CODEX_TOML_BLOCK_END

    if path.exists():
        existing = path.read_text(encoding="utf-8")
        block_re = re.compile(
            rf"^{re.escape(CODEX_TOML_BLOCK_BEGIN)}.*?^{re.escape(CODEX_TOML_BLOCK_END)}",
            re.MULTILINE | re.DOTALL,
        )
        if block_re.search(existing):
            new_content = block_re.sub(block_content, existing, count=1)
        else:
            # TOML table headers at the end of the document are safe to
            # append — no prior key/value line can be re-attributed to them.
            new_content = existing.rstrip("\n") + "\n\n" + block_content + "\n"
    else:
        new_content = (
            "# Codex project config — MCP block managed by agent-meta.\n\n"
            + block_content
            + "\n"
        )

    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
    if write_checked(path, new_content, log, rel, allow_secrets=allow_secrets, config=config,
                     dry_run=dry_run, verify_gitignored=verify_gitignored):
        log.action("WRITE", rel, "mcp-registry → mcp_servers")
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
    # Sourced from mcp_registry.py, not mcp.py, so this module never depends
    # on mcp.py — that direction would recreate the mcp/mcp_provider_config/
    # rules import cycle mcp_registry.py was extracted to break (#613).
    from .mcp_registry import SECRETS_LOCAL_FILE, load_mcp_registry, resolve_active_mcp_servers

    registry = load_mcp_registry(agent_meta_root, config, project_root)
    if not registry:
        return

    active_servers = resolve_active_mcp_servers(config, agent_meta_root, project_root, registry=registry)
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
            allow_secrets=True,  # local files are always meant to be gitignored
            config=config,
            verify_gitignored=True,  # verify that assumption instead of trusting it (#586)
        )


def _write_provider_config(
    path: Path,
    mcp_entries: dict,
    fmt: str,
    log: SyncLog,
    dry_run: bool,
    allow_secrets: bool,
    config: dict | None = None,
    verify_gitignored: bool = False,
) -> None:
    """Dispatch to format-specific writer."""
    if fmt in ("claude-settings", "gemini-settings"):
        _update_json_config(path, "mcpServers", mcp_entries, log, dry_run, allow_secrets, config=config,
                             verify_gitignored=verify_gitignored)
    elif fmt == "opencode-json":
        _update_json_config(path, "mcp", mcp_entries, log, dry_run, allow_secrets, config=config,
                             verify_gitignored=verify_gitignored)
    elif fmt == "continue-yaml":
        _update_continue_yaml_config(path, mcp_entries, log, dry_run, allow_secrets, config=config,
                                      verify_gitignored=verify_gitignored)
    elif fmt == "codex-toml-mcp":
        _update_codex_toml_config(path, mcp_entries, log, dry_run, allow_secrets, config=config,
                                  verify_gitignored=verify_gitignored)
    elif fmt == "zcode-json":
        _update_zcode_json_config(path, mcp_entries, log, dry_run, allow_secrets, config=config,
                                  verify_gitignored=verify_gitignored)
    else:
        log.warning(f"mcp: unknown provider format '{fmt}' — skipping config generation for {path.name}")

