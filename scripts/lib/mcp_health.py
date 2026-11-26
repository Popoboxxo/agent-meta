"""MCP health checks (#1080 / D17, #1262 / C1).

``check_mcp_health`` is advisory only: sync never fails and never blocks on an
empty secret or an unresolvable command; it reports one WARNING per affected,
active server so the operator can act.

``validate_mcp_health`` backs ``--validate`` (#1262): it returns
``(server, severity, message)`` tuples for syntactically invalid MCP URLs and
for plaintext secrets where an env reference belongs. Purely structural — no
network call is ever made — and it never echoes a secret value.

Provider-agnostic — everything is derived from the resolved MCP registry and
the per-project secrets/env sources, never from a provider name.
"""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import Mapping, Optional
from urllib.parse import urlparse

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


# ---------------------------------------------------------------------------
# Structural validation for --validate (#1262 / C1) — no network, ever
# ---------------------------------------------------------------------------

SEVERITY_ERROR = "ERROR"
SEVERITY_WARNING = "WARNING"

ALLOWED_MCP_URL_SCHEMES = frozenset({"http", "https", "ws", "wss"})

# Env-reference forms seen in the committed outputs: ``${VAR}`` (shell /
# committed config), ``{{VAR}}`` (catalog template), ``$VAR`` and the
# provider-specific ``${env:VAR}`` / ``{env:VAR}`` variants.
_ENV_REF_RX = re.compile(
    r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}"
    r"|\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}"
    r"|\$\{env:([A-Za-z_][A-Za-z0-9_]*)\}"
    r"|\{env:([A-Za-z_][A-Za-z0-9_]*)\}"
    r"|\$([A-Za-z_][A-Za-z0-9_]*)"
)

_REF_TOKEN = (
    r"(?:\$\{[A-Za-z_][A-Za-z0-9_]*\}"
    r"|\{\{[A-Za-z_][A-Za-z0-9_]*\}\}"
    r"|\$\{env:[A-Za-z_][A-Za-z0-9_]*\}"
    r"|\{env:[A-Za-z_][A-Za-z0-9_]*\}"
    r"|\$[A-Za-z_][A-Za-z0-9_]*)"
)
_EXACT_REF_RX = re.compile(rf"^\s*{_REF_TOKEN}\s*$")
# ``Authorization: Bearer ${VAR}`` is still a reference — the scheme prefix is
# syntax, not a secret value.
_PREFIXED_REF_RX = re.compile(
    rf"^\s*(?:Bearer|Basic|Token|Digest)\s+{_REF_TOKEN}\s*$", re.IGNORECASE
)

# Distinctive credential words, matched inside a single key segment so that
# compounds such as ``authtoken`` or ``accesstokenvalue`` still count.
_LONG_SECRET_WORDS = (
    "token", "secret", "password", "passwd", "passphrase", "apikey",
    "authorization", "bearer", "credential",
)
# Short, ambiguity-prone word: exact segment only, so ``X-Author`` (a person's
# name) is not read as ``auth``.
_SHORT_SECRET_WORDS = frozenset({"auth"})
# ``api`` + ``key`` is a credential only as that pair (``api_key``,
# ``X-API-KEY``, ``apiKey``) — a lone ``key`` segment is not one.
_SECRET_PHRASES = (("api", "key"), ("api", "keys"))
# A trailing segment naming a *locator* rather than a value means the entry
# points at an endpoint/metadata, not at a literal credential
# (``token_url``, ``authorization_uri``, ``client_secret_name``).
_NON_SECRET_SUFFIXES = frozenset({
    "url", "uri", "endpoint", "path", "host", "port", "scheme", "method",
    "name", "type", "id", "label", "field", "header", "headers", "format",
    "prefix", "count", "len", "length", "timeout", "mode", "scope", "scopes",
})


def _key_segments(key: str) -> list[str]:
    """Split a key into lowercase word segments (``X-Api-Key`` → x, api, key)."""
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(key))
    return [seg for seg in re.split(r"[^A-Za-z0-9]+", spaced.lower()) if seg]


def _is_sensitive_key(key: str) -> bool:
    """True when *key* names a credential slot (never a credential *endpoint*)."""
    segments = _key_segments(key)
    if not segments or segments[-1] in _NON_SECRET_SUFFIXES:
        return False
    for segment in segments:
        if segment in _SHORT_SECRET_WORDS:
            return True
        if any(word in segment for word in _LONG_SECRET_WORDS):
            return True
    joined = "_".join(segments)
    return any("_".join(phrase) in joined for phrase in _SECRET_PHRASES)


def _env_ref_names(value: str) -> list[str]:
    """Names referenced by *value*, in order of appearance."""
    names: list[str] = []
    for match in _ENV_REF_RX.finditer(value):
        name = next((group for group in match.groups() if group), None)
        if name and name not in names:
            names.append(name)
    return names


def _lookup_reference(name: str, secrets: Mapping, env: Mapping[str, str]) -> Optional[str]:
    """Resolve *name* from secrets/environment; ``None`` when unset/empty."""
    for source in (secrets, env):
        raw = source.get(name) if hasattr(source, "get") else None
        value = str(raw or "").strip()
        if value:
            return value
    return None


def _is_env_reference(value: str, *, allow_scheme_prefix: bool = False) -> bool:
    """True when *value* consists only of an env-reference token."""
    if _EXACT_REF_RX.match(value):
        return True
    return allow_scheme_prefix and bool(_PREFIXED_REF_RX.match(value))


def _substitute(value: str, secrets: Mapping, env: Mapping[str, str]) -> tuple[str, list[str]]:
    """Replace resolvable env references; return ``(text, missing_names)``."""
    missing: list[str] = []

    def _replace(match: re.Match) -> str:
        name = next((group for group in match.groups() if group), None)
        if not name:  # pragma: no cover - defensive, the regex always groups
            return match.group(0)
        resolved = _lookup_reference(name, secrets, env)
        if resolved is None:
            if name not in missing:
                missing.append(name)
            return match.group(0)
        return resolved

    return _ENV_REF_RX.sub(_replace, value), missing


def _check_url(
    connection: Mapping,
    secrets: Mapping,
    env: Mapping[str, str],
    out: list[tuple[str, str]],
) -> None:
    """Append URL findings; messages never contain the resolved URL."""
    url = connection.get("url")
    if not isinstance(url, str) or not url.strip():
        return
    resolved, missing = _substitute(url, secrets, env)
    for name in missing:
        out.append((
            SEVERITY_WARNING,
            f"environment variable '{name}' is not set (referenced in "
            "connection.url); URL syntax not checked",
        ))
    if missing:
        return
    parsed = urlparse(resolved)
    scheme = (parsed.scheme or "").lower()
    if not scheme:
        out.append((
            SEVERITY_ERROR,
            "connection.url has no scheme (expected http, https, ws or wss)",
        ))
        return
    if scheme not in ALLOWED_MCP_URL_SCHEMES:
        out.append((
            SEVERITY_ERROR,
            f"connection.url uses unsupported scheme '{scheme}' "
            "(allowed: http, https, ws, wss)",
        ))
        return
    if not parsed.netloc:
        out.append((SEVERITY_ERROR, "connection.url has no host"))
        return
    if parsed.username is not None or parsed.password is not None:
        out.append((
            SEVERITY_ERROR,
            "connection.url embeds plaintext credentials — use an env "
            "reference (${VAR})",
        ))


def _iter_secret_slots(connection: Mapping):
    """Yield ``(path, value, allow_scheme_prefix)`` for credential slots."""
    headers = connection.get("headers")
    if isinstance(headers, Mapping):
        for key, value in headers.items():
            if _is_sensitive_key(str(key)):
                yield f"headers.{key}", value, True
    auth = connection.get("auth")
    if isinstance(auth, str):
        yield "auth", auth, True
    elif isinstance(auth, Mapping):
        for key, value in auth.items():
            if _is_sensitive_key(str(key)):
                yield f"auth.{key}", value, True
    env_map = connection.get("env")
    if isinstance(env_map, Mapping):
        for key, value in env_map.items():
            if _is_sensitive_key(str(key)):
                yield f"env.{key}", value, False
    for key, value in connection.items():
        if key in ("headers", "auth", "env", "url"):
            continue
        if _is_sensitive_key(str(key)):
            yield str(key), value, False


def _check_secret_references(
    connection: Mapping,
    secrets: Mapping,
    env: Mapping[str, str],
    out: list[tuple[str, str]],
) -> None:
    """Append ERRORs for literal credentials — never the literal itself."""
    for path, value, allow_prefix in _iter_secret_slots(connection):
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            continue
        text = str(value).strip()
        if not text:
            continue
        if _is_env_reference(text, allow_scheme_prefix=allow_prefix):
            for name in _env_ref_names(text):
                if _lookup_reference(name, secrets, env) is None:
                    out.append((
                        SEVERITY_WARNING,
                        f"environment variable '{name}' is not set "
                        f"(referenced in connection.{path})",
                    ))
            continue
        out.append((
            SEVERITY_ERROR,
            f"plaintext secret in connection.{path} — use an env reference "
            "(${VAR}); the literal value is not echoed",
        ))


def validate_mcp_health(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    env: Optional[Mapping[str, str]] = None,
    registry: Optional[dict] = None,
    active: Optional[list] = None,
) -> list[tuple[str, str, str]]:
    """Return ``(server, severity, message)`` findings for ``--validate``.

    Structural only (``urllib.parse``), never a network call (#1262 / C1).
    URL placeholders resolve from ``secrets.local.yaml`` then the environment;
    a missing variable degrades to a WARNING, never an exception. Secrets must
    stay env references — a literal credential is an ERROR, and the literal is
    never part of the message.

    ``registry``/``active`` may be pre-loaded by the caller to avoid re-reading
    the plugin catalog; otherwise they are resolved here. Malformed catalog
    entries are skipped, so an advisory check can never break ``--validate``.
    """
    env_vars = os.environ if env is None else env
    findings: list[tuple[str, str, str]] = []
    try:
        if registry is None:
            registry = load_mcp_registry(
                Path(agent_meta_root), config, Path(project_root)
            )
        if not isinstance(registry, dict):
            registry = {}
        if active is None:
            active = resolve_active_mcp_servers(
                config, Path(agent_meta_root), Path(project_root), registry=registry
            )
        secrets = _load_secrets(Path(project_root))
    except Exception:  # noqa: BLE001 - advisory, never breaks --validate
        return findings

    for name in active or []:
        server = registry.get(name)
        if not isinstance(server, dict):
            continue
        connection = server.get("connection")
        if not isinstance(connection, dict):
            # ``connection: "sse"`` (a string override) has nothing to inspect.
            continue
        server_findings: list[tuple[str, str]] = []
        _check_url(connection, secrets, env_vars, server_findings)
        _check_secret_references(connection, secrets, env_vars, server_findings)
        for severity, message in server_findings:
            findings.append((str(name), severity, f"server '{name}': {message}"))
    return findings
