"""MCP health WARN checks (#1080 / D17).

Advisory only: sync never fails and never blocks on an empty secret or an
unresolvable command; it reports one WARNING per affected, active server so the
operator can act. Provider-agnostic — everything is derived from the resolved
MCP registry and the per-project secrets/env sources, never from a provider
name.
"""
from __future__ import annotations

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


def check_mcp_health(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    env: Optional[Mapping[str, str]] = None,
) -> None:
    """Emit one WARN per active server with an empty secret or bad command."""
    env_vars = os.environ if env is None else env
    try:
        registry = load_mcp_registry(
            Path(agent_meta_root), config, Path(project_root)
        )
        active = resolve_active_mcp_servers(
            config, Path(agent_meta_root), Path(project_root), registry=registry
        )
        secrets = _load_secrets(Path(project_root))
    except Exception as exc:  # noqa: BLE001 - advisory, never breaks the sync
        log.debug("mcp-health", f"skipped: {exc}")
        return

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
