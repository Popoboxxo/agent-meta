"""MCP health WARN checks (#1080 / D17).

Advisory only: sync never fails and never blocks on an empty secret or an
unresolvable command; it reports one WARNING per affected, active server so the
operator can act. Provider-agnostic — everything is derived from the resolved
MCP registry and the per-project secrets/env sources, never from a provider
name.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Mapping, Optional

from .io import _load_yaml_or_json
from .log import SyncLog
from .mcp_provider_config import _resolve_stdio_command
from .registry_query import (
    SECRETS_LOCAL_FILE,
    load_mcp_registry,
    resolve_active_mcp_servers,
)


def _load_secrets(project_root: Path) -> dict:
    """Read ``secrets.local.yaml``; an unreadable file degrades to ``{}``."""
    try:
        data, _ = _load_yaml_or_json(Path(project_root) / SECRETS_LOCAL_FILE)
    except Exception:  # noqa: BLE001 - the health check is advisory only
        return {}
    return data if isinstance(data, dict) else {}


def _is_set(name: str, secrets: dict, env: Mapping[str, str]) -> bool:
    """True when *name* has a non-empty value in secrets or the environment."""
    return bool(
        str(secrets.get(name) or "").strip() or str(env.get(name) or "").strip()
    )


def check_external_plugin_duplicates(
    registry: dict,
    active: list,
    provider_cfgs: Mapping[str, Mapping],
    log: SyncLog,
    home: Optional[Path] = None,
) -> None:
    """WARN once per server/provider when it is also enabled as external plugin.

    Best-effort and read-only (#1261): missing/defective files only debug-log.
    Capability-driven (``external_plugins_file`` per provider, catalog
    ``external-plugin-id-prefix``) — no provider or plugin name in code.
    """
    home_dir = Path.home() if home is None else Path(home)
    for name in active:
        server = registry.get(name)
        prefix = server.get("external-plugin-id-prefix") if isinstance(server, dict) else None
        if not isinstance(prefix, str) or not prefix:
            continue
        for provider, cfg in provider_cfgs.items():
            flag = cfg.get("external_plugins_file") if isinstance(cfg, Mapping) else None
            if not isinstance(flag, Mapping):
                continue
            raw_path, key = flag.get("path"), flag.get("enabled_key")
            if not isinstance(raw_path, str) or not isinstance(key, str):
                continue
            # shortcut: ``~/`` only, resolved against ``home`` (not $HOME).
            path = home_dir / raw_path[2:] if raw_path.startswith("~/") else Path(raw_path)
            try:
                enabled = json.loads(path.read_text(encoding="utf-8")).get(key)
            except (OSError, ValueError, AttributeError) as exc:
                log.debug("mcp-health", f"plugin file {path} skipped: {exc}")
                continue
            if not isinstance(enabled, dict):
                continue
            if any(isinstance(k, str) and k.startswith(prefix) and v is True
                   for k, v in enabled.items()):
                log.warn(
                    f"mcp.duplicate-plugin: server '{name}' is active in the "
                    f"catalog AND enabled as external plugin ({path}, "
                    f"{provider}). Set `enabled: false` for '{name}' under "
                    "`plugins:` in project.yaml or disable the plugin; "
                    "otherwise set both env-variable sets."
                )


def check_mcp_health(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    env: Optional[Mapping[str, str]] = None,
    provider_cfgs: Optional[Mapping[str, Mapping]] = None,
    home: Optional[Path] = None,
) -> None:
    """Emit one WARN per active server with an empty secret or bad command.

    ``provider_cfgs`` (active providers only) enables the external-plugin
    duplicate check (#1261); ``None`` skips it.
    """
    env_vars = os.environ if env is None else env
    try:
        registry = load_mcp_registry(
            Path(agent_meta_root), config, Path(project_root)
        )
        if not isinstance(registry, dict):
            registry = {}
        active = resolve_active_mcp_servers(
            config, Path(agent_meta_root), Path(project_root), registry=registry
        )
        secrets = _load_secrets(Path(project_root))
    except Exception as exc:  # noqa: BLE001 - advisory, never breaks the sync
        log.debug("mcp-health", f"skipped: {exc}")
        return

    if provider_cfgs is not None:
        try:
            check_external_plugin_duplicates(
                registry, list(active), provider_cfgs, log, home
            )
        except Exception as exc:  # noqa: BLE001 - advisory, never breaks the sync
            log.debug("mcp-health", f"plugin duplicate check skipped: {exc}")

    for name in active:
        server = registry.get(name) or {}
        if not isinstance(server, dict):
            # A malformed catalog override must never abort the sync from an
            # advisory check (the loop runs outside the try above).
            continue
        required = [str(item) for item in (server.get("secrets") or []) if item]
        missing = [item for item in required if not _is_set(item, secrets, env_vars)]
        if missing:
            log.warn(
                f"mcp.secret-empty: server '{name}': required secret(s) "
                f"{', '.join(missing)} empty (secrets.local.yaml / environment) "
                "— server will not connect"
            )
        connection = server.get("connection") or {}
        if not isinstance(connection, dict):
            # ``connection: "sse"`` (a string override) has no ``.get``; skip
            # the command check instead of raising AttributeError (#1080).
            continue
        if connection.get("type") == "stdio":
            command = str(connection.get("command") or "")
            if shutil.which(_resolve_stdio_command(command)) is None:
                log.warn(
                    f"mcp.command-unresolved: server '{name}': command "
                    f"'{command}' not found on PATH"
                )
