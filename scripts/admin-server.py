#!/usr/bin/env python3
"""
agent-meta Admin UI Server
==========================
Zero-dependency HTTP server (Python stdlib + PyYAML) that exposes a visual
configuration surface for agent-meta. Serves a single-page web UI from
``docs/ui/admin-ui.html`` and provides REST + SSE endpoints over the YAML/JSON
configuration files of the framework.

Two modes:
  * ``super_admin`` — running inside the agent-meta framework repository
    itself (``agents/1-generic/`` exists). All super-admin configs become
    editable.
  * ``project_admin`` — running inside a target repository that has agent-meta
    integrated as a submodule. Only ``.meta-config/project.yaml`` is exposed.

Start:
  python scripts/admin-server.py               (Admin UI + Viz dashboard + MCP server, foreground)
  python scripts/admin-server.py --no-viz      (Admin UI only, lightweight mode)
  python scripts/admin-server.py --port 7420 --root .
  python scripts/sync.py --admin               (after a normal sync)
  python scripts/sync.py --admin-only          (skip sync)

Detached background mode (for scripts / slash-commands):
  python scripts/admin-server.py start          (launch detached, returns immediately)
  python scripts/admin-server.py stop           (stop Admin UI + Viz + MCP)
  python scripts/admin-server.py status         (show running state)
  python scripts/admin-server.py restart

Unified entry-point:
  In super_admin mode the server also starts the Viz dashboard (viz-report.py)
  and the MCP SSE server (viz-logger.py) as supervised subprocesses unless
  ``--no-viz`` is passed.  PID-files and logs are written to ``.meta-viz/``.
  In project_admin (target-repo) mode the same subprocesses are started via
  the submodule path (``.agent-meta/scripts/``).
"""

from __future__ import annotations

import argparse
import json
import hmac
import logging
import os
import queue
import stat
import subprocess
import sys
import threading
import time
from collections.abc import Iterable
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, ClassVar
from urllib.parse import parse_qs, urlparse

try:
    import yaml
except ImportError:  # pragma: no cover
    print("  !  PyYAML is required. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# --------------------------------------------------------------------------- #
# Logging                                                                     #
# --------------------------------------------------------------------------- #

# Full exception details (stack traces, file paths, library internals) are
# logged server-side only — never sent to HTTP clients, see
# ``AdminRequestHandler._handle_error`` (issue #581). No handler is attached
# here on purpose: Python's logging "handler of last resort" already prints
# WARNING+ to stderr, which matches this script's existing stderr-only
# diagnostic convention without adding a second, competing output path.
logger = logging.getLogger("agent_meta.admin_server")


# --------------------------------------------------------------------------- #
# Constants                                                                   #
# --------------------------------------------------------------------------- #

DEFAULT_PORT = 7420
DEFAULT_HOST = "127.0.0.1"
MAX_BACKUPS = 5
SSE_HEARTBEAT_SECONDS = 15
# Upper bound on a single PUT/POST request body (issue #585). Every current
# use case — model config edits, pricing overlays, pipeline/reflection-pair
# definitions — is well under 1 MB; 10 MB leaves generous headroom while
# still bounding memory allocation per request (``_read_body`` would
# otherwise call ``self.rfile.read(length)`` with an attacker/client-supplied
# ``Content-Length``, unbounded).
MAX_BODY_SIZE = 10 * 1024 * 1024  # 10 MB

# --- Centralized per-provider model-source preference ---------------------- #
# A provider's model dropdowns/suggestions are served EXCLUSIVELY from one
# source: the local registry (model-registry.json + pricing overlay) or the
# live models.dev catalog. The preference is persisted centrally in
# ``.meta-config/project.yaml`` under ``model-source-preference`` and is the
# single source of truth for every model suggestion endpoint — no client-side
# state, no mixing of both sources.
#
# The framework-wide default (fallback when no per-provider override exists)
# lives in ``config/ai-providers.yaml`` -> ``default-model-source`` (see
# ``AdminRequestHandler._default_model_source``) rather than being hardcoded
# here, so operators can change it without touching Python.
_FALLBACK_MODEL_SOURCE = "registry"
VALID_MODEL_SOURCES: tuple[str, ...] = ("registry", "modelsdev")
# The two mutually exclusive per-provider model blocks in project.yaml.
# A provider may be truthy-set in at most ONE of them. Sync-side enforcement
# lives in lib/config.py::_validate_model_inheritance (hard-fatal, SystemExit);
# the admin-server counterparts below keep UI/section writes from persisting a
# config that would kill every later sync run.
MODEL_EXCLUSIVE_BLOCKS: tuple[str, str] = ("model-override-all", "model-inherit-main-chat")


def _other_model_block(section: str) -> str:
    """Return the opposite block of :data:`MODEL_EXCLUSIVE_BLOCKS`."""
    return MODEL_EXCLUSIVE_BLOCKS[1] if section == MODEL_EXCLUSIVE_BLOCKS[0] else MODEL_EXCLUSIVE_BLOCKS[0]


def find_model_block_conflicts(data: Any, other: Any) -> list[str]:
    """Return providers that would be truthy-set in BOTH exclusive blocks.

    ``data`` is the incoming payload for one block, ``other`` the currently
    persisted opposite block. Only truthy entries on both sides conflict —
    ``false`` counts as unset and different providers never conflict,
    mirroring lib/config.py::_validate_model_inheritance().
    """
    if not isinstance(data, dict) or not isinstance(other, dict):
        return []
    return [provider for provider, value in data.items() if value and other.get(provider)]


def _normalized_model_id(model_id: str) -> str:
    """Normalize a model id for drift-tolerant curation matching.

    Registry id formats changed across discovery generations (bare vs.
    provider-prefixed, dash vs. dot version separators), so curation entries
    written against an older registry would silently stop matching with a
    plain equality check (e.g. ``claude-opus-4-1`` vs. the current
    ``anthropic/claude-opus-4.1``). The comparison key strips any
    ``<provider>/`` namespace (keeping only the last ``/``-segment),
    lowercases and maps dots to dashes, so both spellings above normalize
    to ``claude-opus-4-1``. Used ONLY for the ``curation.disabled`` check —
    surfaced model ids are never rewritten.

    Accepted trade-off: stripping the namespace makes a disabled entry match
    the same tail id under EVERY provider (``openai/gpt-4o`` also disables a
    hypothetical bare ``gpt-4o`` of another provider). Curation intent is
    model-level ("disable this model everywhere"), so this cross-provider
    overreach is deliberate; distinct models keep distinct tails (e.g.
    ``4.1`` vs ``4.1:batch``), which the tail-preserving comparison keeps
    apart.
    """
    tail = str(model_id).strip().lower().rsplit("/", 1)[-1]
    return tail.replace(".", "-")


# Framework provider name -> models.dev catalog slug. Mirrors
# ``PROVIDER_MODELSDEV_MAP`` in ``docs/ui/admin-ui.html`` — keep both in sync.
# Providers absent here (e.g. Mammouth, Continue) have no models.dev catalog
# entry, so ``modelsdev`` yields no suggestions for them. Opencode maps to
# the "opencode-go" slug: models.dev's catalog exposes it as a distinct
# provider entry (api https://opencode.ai/zen/go/v1) that is the exact same
# endpoint ``fetch_opencode_go_models()`` in
# ``scripts/lib/model_discovery.py`` fetches directly, so the two sources
# describe the same catalog and it's safe to resolve suggestions from
# models.dev for this provider.
PROVIDER_MODELSDEV_SLUGS: dict[str, str] = {
    "Claude": "anthropic",
    "Gemini": "google",
    "Opencode": "opencode-go",
    "Copilot": "github-copilot",
}

# PID files and logs for supervised sub-servers (relative to project root).
VIZ_PID_FILE   = ".meta-viz/.server-pid"
VIZ_LOG_FILE   = ".meta-viz/server.log"
MCP_PID_FILE   = ".meta-viz/.mcp-server-pid"
MCP_LOG_FILE   = ".meta-viz/mcp-server.log"
ADMIN_PID_FILE = ".meta-viz/.admin-server-pid"
ADMIN_LOG_FILE = ".meta-viz/admin-server.log"

_DEFAULT_VIZ_PORT          = 8765
_DEFAULT_VIZ_TIMEOUT       = 300
_DEFAULT_MCP_PORT          = 9090
_DEFAULT_VIZ_ENABLED       = False
_DEFAULT_VIZ_MODE          = "off"
_DEFAULT_VIZ_EVENT_LOG     = ".meta-viz/events.jsonl"
_DEFAULT_VIZ_RETENTION     = 7
_DEFAULT_VIZ_SESSION_TIMEOUT = 5

# Loopback addresses are the default values the ``--host`` flag accepts.
# Remote binding is now possible when token authentication (``--token``) is
# configured — see ``--help`` for details.  Without token auth, the in-process
# guard still restricts binding to DEFAULT_ALLOWED_HOSTS.
DEFAULT_ALLOWED_HOSTS: tuple[str, ...] = ("127.0.0.1", "localhost", "::1")
LOOPBACK_HOSTS: tuple[str, ...] = ("127.0.0.1", "localhost", "::1")

# Super-admin config files (only available when ``agents/1-generic/`` exists).
SUPER_ADMIN_FILES: dict[str, str] = {
    "role-defaults":     "config/role-defaults.yaml",
    "ai-providers":      "config/ai-providers.yaml",
    "skills-registry":   "config/skills-registry.yaml",
    "mcp-registry":      "config/mcp-registry.yaml",
    "external-tools-registry": "config/external-tools-registry.yaml",
    "dod-presets":       "config/dod-presets.yaml",
    "rules-presets":     "config/rules-presets.yaml",
    "conventions-presets": "config/conventions-presets.yaml",
    "delegation-syntax": "config/delegation-syntax.yaml",
    "export":            "config/export.yaml",
}

# Always-available project configs.
PROJECT_FILES: dict[str, str] = {
    "project": ".meta-config/project.yaml",
    "project-mcp-registry": ".meta-config/mcp-registry.yaml",
    "project-external-tools-registry": ".meta-config/external-tools-registry.yaml",
}


# --------------------------------------------------------------------------- #
# Asset resolution                                                            #
# --------------------------------------------------------------------------- #


def resolve_asset(root: Path, *parts: str) -> Path:
    """Resolve a framework asset path, honouring the submodule layout.

    agent-meta can be checked out at the project root (super-admin) or embedded
    as a submodule under ``.agent-meta/`` (project-admin). Every framework asset
    (``config/``, ``docs/``, ``agents/``, ``scripts/``, ``VERSION`` …) therefore
    lives under one of two prefixes. Resolution order:

      1. ``<root>/<*parts>``               -- top-level checkout
      2. ``<root>/.agent-meta/<*parts>``   -- submodule layout

    Returns the primary path even when neither exists, so callers can surface
    the expected top-level location in ``not_found`` errors and route new writes
    there. To pick the correct layout for a file that may not exist yet (e.g. an
    optional overlay), resolve its parent directory instead, then join the file
    name: ``resolve_asset(root, "config") / "pricing-overlay.yaml"``.
    """
    primary = root.joinpath(*parts)
    if primary.exists():
        return primary
    fallback = root.joinpath(".agent-meta", *parts)
    if fallback.exists():
        return fallback
    return primary


def _ensure_scripts_on_path(root: Path) -> None:
    """Idempotently make ``lib.*`` importable for both directory layouts.

    Many handler methods perform a deferred ``from lib.<module> import ...``
    (kept lazy so the server still starts when ``lib`` isn't needed for a
    given request) and need one of two directories on ``sys.path`` first:
    ``<root>/scripts`` (super-admin layout) or ``<root>/.agent-meta/scripts``
    (project-admin/submodule layout). ``root`` is constant for the lifetime
    of a running server, so re-inserting the same two paths on every single
    request — as every call site used to do — makes ``sys.path`` grow without
    bound (issue #584). Skip paths already present instead.
    """
    for candidate in (root / "scripts", root / ".agent-meta" / "scripts"):
        str_candidate = str(candidate)
        if str_candidate not in sys.path:
            sys.path.insert(0, str_candidate)


# --------------------------------------------------------------------------- #
# Viz / MCP sub-server manager                                               #
# --------------------------------------------------------------------------- #


def _viz_defaults() -> dict:
    """Return the full default viz configuration block."""
    return {
        "enabled":     _DEFAULT_VIZ_ENABLED,
        "mode":        _DEFAULT_VIZ_MODE,
        "event_log":   _DEFAULT_VIZ_EVENT_LOG,
        "viz_port":    _DEFAULT_VIZ_PORT,
        "viz_timeout": _DEFAULT_VIZ_TIMEOUT,
        "mcp_port":    _DEFAULT_MCP_PORT,
        "retention_days":      _DEFAULT_VIZ_RETENTION,
        "session_timeout_min": _DEFAULT_VIZ_SESSION_TIMEOUT,
    }


def _load_viz_config(root: Path) -> dict:
    """Load the full viz configuration from ``.meta-config/project.yaml``.

    Returns a flat dict with all viz fields the Admin UI exposes:
      * ``enabled``              (bool)        — viz.enabled
      * ``mode``                 (str)         — viz.mode
      * ``event_log``            (str)         — viz.event_log
      * ``viz_port``             (int)         — viz.server.port
      * ``viz_timeout``          (int)         — viz.server.timeout_sec
      * ``mcp_port``             (int)         — viz.mcp.port
      * ``retention_days``       (int)         — viz.report.retention_days
      * ``session_timeout_min``  (int)         — viz.report.session_timeout_min

    Falls back to the documented defaults on any read/parse error so the
    Viz/MCP supervisor can still start with sensible values.
    """
    config_path = root / ".meta-config" / "project.yaml"
    if not config_path.exists():
        return _viz_defaults()
    try:
        _ensure_scripts_on_path(root)
        from lib.config import load_config
        config = load_config(config_path)
        viz_cfg = config.get("viz") or {}
        server_cfg = viz_cfg.get("server") or {}
        mcp_cfg = viz_cfg.get("mcp") or {}
        report_cfg = viz_cfg.get("report") or {}
        return {
            "enabled":     bool(viz_cfg.get("enabled", _DEFAULT_VIZ_ENABLED)),
            "mode":        str(viz_cfg.get("mode", _DEFAULT_VIZ_MODE)),
            "event_log":   str(viz_cfg.get("event_log", _DEFAULT_VIZ_EVENT_LOG)),
            "viz_port":    int(server_cfg.get("port", _DEFAULT_VIZ_PORT)),
            "viz_timeout": int(server_cfg.get("timeout_sec", _DEFAULT_VIZ_TIMEOUT)),
            "mcp_port":    int(mcp_cfg.get("port", _DEFAULT_MCP_PORT)),
            "retention_days":      int(report_cfg.get("retention_days", _DEFAULT_VIZ_RETENTION)),
            "session_timeout_min": int(report_cfg.get("session_timeout_min", _DEFAULT_VIZ_SESSION_TIMEOUT)),
        }
    except Exception:
        return _viz_defaults()


def _load_admin_ui_config(root: Path) -> dict:
    """Load admin-ui configuration from ``.meta-config/project.yaml``.

    Returns a flat dict:
      * ``bind_host``     (str)          — admin-ui.bind-host
      * ``token``         (str | None)   — admin-ui.token (None if not set)
      * ``token_file``    (str | None)   — admin-ui.token-file (None if not set)
      * ``allowed_hosts`` (list[str])    — admin-ui.allowed-hosts
      * ``enabled``       (bool)         — admin-ui.enabled
      * ``port``          (int)          — admin-ui.port
    """
    config_path = root / ".meta-config" / "project.yaml"
    if not config_path.exists():
        return {
            "bind_host":     DEFAULT_HOST,
            "token":         None,
            "token_file":    None,
            "allowed_hosts": list(DEFAULT_ALLOWED_HOSTS),
            "enabled":       True,
            "port":          DEFAULT_PORT,
        }
    try:
        _ensure_scripts_on_path(root)
        from lib.config import load_config
        config = load_config(config_path)
        admin_cfg = config.get("admin-ui") or {}
        return {
            "bind_host":     str(admin_cfg.get("bind-host", DEFAULT_HOST)),
            "token":         admin_cfg.get("token"),
            "token_file":    admin_cfg.get("token-file"),
            "allowed_hosts": list(admin_cfg.get("allowed-hosts", list(DEFAULT_ALLOWED_HOSTS))),
            "enabled":       bool(admin_cfg.get("enabled", True)),
            "port":          int(admin_cfg.get("port", DEFAULT_PORT)),
        }
    except Exception:
        return {
            "bind_host":     DEFAULT_HOST,
            "token":         None,
            "token_file":    None,
            "allowed_hosts": list(DEFAULT_ALLOWED_HOSTS),
            "enabled":       True,
            "port":          DEFAULT_PORT,
        }


def _is_pid_running(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            handle = kernel32.OpenProcess(1, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        else:
            os.kill(pid, 0)
            return True
    except (OSError, ProcessLookupError):
        return False


def _read_pid(pid_file: Path) -> int | None:
    if pid_file.exists():
        try:
            return int(pid_file.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            pass
    return None


class VizManager:
    """Manages the Viz dashboard and MCP SSE server as supervised subprocesses.

    Both sub-servers run in detached sessions (``start_new_session=True`` on
    POSIX, ``CREATE_NEW_PROCESS_GROUP`` on Windows) so they survive a parent
    process re-exec but are cleaned up when :meth:`stop_all` is called.

    Resolution order for script paths (same pattern as SyncExecutor):
      1. ``<root>/scripts/viz-report.py``              -- top-level checkout
      2. ``<root>/.agent-meta/scripts/viz-report.py``  -- submodule layout
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self._viz_report = self._resolve_script("viz-report.py")
        self._viz_logger = self._resolve_script("viz-logger.py")

    # ---------------------------------------------------------------------- #
    # Internal helpers                                                       #
    # ---------------------------------------------------------------------- #

    def _resolve_script(self, name: str) -> Path:
        return resolve_asset(self.root, "scripts", name)

    def _start(
        self,
        args: list,
        pid_file: Path,
        log_file: Path,
        label: str,
    ) -> bool:
        """Start a detached subprocess, record its PID, return True on success."""
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        if log_file.exists():
            try:
                log_file.unlink()
            except PermissionError:
                pass

        if sys.platform == "win32":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            proc = subprocess.Popen(
                args,
                stdout=open(log_file, "a", encoding="utf-8"),  # noqa: SIM115
                stderr=subprocess.STDOUT,
                startupinfo=si,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                cwd=str(self.root),
            )
        else:
            proc = subprocess.Popen(
                args,
                stdout=open(log_file, "a", encoding="utf-8"),  # noqa: SIM115
                stderr=subprocess.STDOUT,
                start_new_session=True,
                cwd=str(self.root),
            )

        pid_file.write_text(str(proc.pid), encoding="utf-8")
        time.sleep(1.5)

        if _is_pid_running(proc.pid):
            print(f"  +  {label} started (PID: {proc.pid})")
            return True
        else:
            print(f"  !  {label} failed to start -- see {log_file}")
            pid_file.unlink(missing_ok=True)
            return False

    def _stop(self, pid_file: Path, label: str) -> None:
        pid = _read_pid(pid_file)
        if not pid or not _is_pid_running(pid):
            pid_file.unlink(missing_ok=True)
            return
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/F"],
                    check=True, capture_output=True,
                )
            else:
                os.kill(pid, 15)
                time.sleep(1)
                if _is_pid_running(pid):
                    os.kill(pid, 9)
            print(f"  -  {label} stopped (PID: {pid})")
        except Exception as exc:  # noqa: BLE001
            print(f"  !  Error stopping {label}: {exc}")
        finally:
            pid_file.unlink(missing_ok=True)

    # ---------------------------------------------------------------------- #
    # Public interface                                                       #
    # ---------------------------------------------------------------------- #

    def start_all(self) -> None:
        """Start both the Viz dashboard and the MCP server."""
        cfg = _load_viz_config(self.root)

        # --- Viz dashboard ---
        viz_pid = self.root / VIZ_PID_FILE
        viz_log = self.root / VIZ_LOG_FILE
        if not _is_pid_running(_read_pid(viz_pid)):
            if self._viz_report.exists():
                self._start(
                    [
                        sys.executable,
                        str(self._viz_report),
                        "--serve",
                        "--port", str(cfg["viz_port"]),
                        "--timeout", str(cfg["viz_timeout"]),
                    ],
                    viz_pid, viz_log,
                    f"Viz dashboard (port {cfg['viz_port']})",
                )
            else:
                print("  -  viz-report.py not found, skipping Viz dashboard")

        # --- MCP server ---
        mcp_pid = self.root / MCP_PID_FILE
        mcp_log = self.root / MCP_LOG_FILE
        if not _is_pid_running(_read_pid(mcp_pid)):
            if self._viz_logger.exists():
                self._start(
                    [
                        sys.executable, "-u",
                        str(self._viz_logger),
                        "--root", str(self.root),
                        "--http", str(cfg["mcp_port"]),
                    ],
                    mcp_pid, mcp_log,
                    f"MCP server (port {cfg['mcp_port']})",
                )
            else:
                print("  -  viz-logger.py not found, skipping MCP server")

    def stop_all(self) -> None:
        """Terminate both sub-servers."""
        self._stop(self.root / VIZ_PID_FILE, "Viz dashboard")
        self._stop(self.root / MCP_PID_FILE, "MCP server")

    # ---------------------------------------------------------------------- #
    # Individual service control                                             #
    # ---------------------------------------------------------------------- #

    def start_viz(self) -> bool:
        """Start only the Viz dashboard subserver.

        Returns ``True`` if the server is running afterwards (either freshly
        started or already alive), ``False`` if the launch failed or the
        ``viz-report.py`` script could not be resolved.
        """
        cfg = _load_viz_config(self.root)
        viz_pid = self.root / VIZ_PID_FILE
        viz_log = self.root / VIZ_LOG_FILE
        if _is_pid_running(_read_pid(viz_pid)):
            return True
        if not self._viz_report.exists():
            return False
        return self._start(
            [
                sys.executable,
                str(self._viz_report),
                "--serve",
                "--port", str(cfg["viz_port"]),
                "--timeout", str(cfg["viz_timeout"]),
            ],
            viz_pid, viz_log,
            f"Viz dashboard (port {cfg['viz_port']})",
        )

    def stop_viz(self) -> bool:
        """Stop only the Viz dashboard subserver. Always returns ``True``."""
        self._stop(self.root / VIZ_PID_FILE, "Viz dashboard")
        return True

    def restart_viz(self) -> bool:
        """Restart the Viz dashboard subserver."""
        self.stop_viz()
        return self.start_viz()

    def start_mcp(self) -> bool:
        """Start only the MCP SSE server subserver.

        Returns ``True`` if the server is running afterwards (either freshly
        started or already alive), ``False`` if the launch failed or the
        ``viz-logger.py`` script could not be resolved.
        """
        cfg = _load_viz_config(self.root)
        mcp_pid = self.root / MCP_PID_FILE
        mcp_log = self.root / MCP_LOG_FILE
        if _is_pid_running(_read_pid(mcp_pid)):
            return True
        if not self._viz_logger.exists():
            return False
        return self._start(
            [
                sys.executable, "-u",
                str(self._viz_logger),
                "--root", str(self.root),
                "--http", str(cfg["mcp_port"]),
            ],
            mcp_pid, mcp_log,
            f"MCP server (port {cfg['mcp_port']})",
        )

    def stop_mcp(self) -> bool:
        """Stop only the MCP SSE server subserver. Always returns ``True``."""
        self._stop(self.root / MCP_PID_FILE, "MCP server")
        return True

    def restart_mcp(self) -> bool:
        """Restart the MCP SSE server subserver."""
        self.stop_mcp()
        return self.start_mcp()

    def status(self) -> dict:
        """Return a status dict for the ``/api/subserver-status`` endpoint.

        Includes both the live subserver state (running flags, PIDs, URLs) and
        the full viz configuration so the Admin UI can render the editor
        without a second round-trip.
        """
        cfg = _load_viz_config(self.root)
        viz_pid_val = _read_pid(self.root / VIZ_PID_FILE)
        mcp_pid_val = _read_pid(self.root / MCP_PID_FILE)
        viz_running = _is_pid_running(viz_pid_val)
        mcp_running = _is_pid_running(mcp_pid_val)
        return {
            "viz": {
                "running": viz_running,
                "pid":     viz_pid_val,
                "port":    cfg["viz_port"],
                "url":     f"http://localhost:{cfg['viz_port']}/",
                "log":     VIZ_LOG_FILE,
            },
            "mcp": {
                "running": mcp_running,
                "pid":     mcp_pid_val,
                "port":    cfg["mcp_port"],
                "url":     f"http://127.0.0.1:{cfg['mcp_port']}/sse",
                "log":     MCP_LOG_FILE,
            },
            "config": {
                "enabled":             cfg["enabled"],
                "mode":                cfg["mode"],
                "event_log":           cfg["event_log"],
                "server_port":         cfg["viz_port"],
                "server_timeout_sec":  cfg["viz_timeout"],
                "mcp_port":            cfg["mcp_port"],
                "retention_days":      cfg["retention_days"],
                "session_timeout_min": cfg["session_timeout_min"],
            },
        }


# --------------------------------------------------------------------------- #
# Exceptions                                                                  #
# --------------------------------------------------------------------------- #


class SecurityError(Exception):
    """Raised when a write/read attempt fails security validation."""


class AuthError(Exception):
    """Raised when token authentication fails. Mapped to HTTP 401."""


class PayloadTooLargeError(Exception):
    """Raised when a request body exceeds ``MAX_BODY_SIZE``. Mapped to HTTP 413."""


def _verify_token(provided: str | None, expected: str | None) -> bool:
    """Constant-time token comparison using hmac.compare_digest."""
    if not provided or not expected:
        return False
    return hmac.compare_digest(
        provided.encode("utf-8"),
        expected.encode("utf-8"),
    )


def _resolve_admin_token(
    cli_token: str | None,
    config_token: str | None,
    config_token_file: str | None,
    env_var_name: str = "ADMIN_UI_TOKEN",
) -> str | None:
    """Resolve the admin token from multiple sources. Priority: CLI > env > config > file."""
    if cli_token:
        return cli_token
    env_token = os.environ.get(env_var_name)
    if env_token:
        return env_token
    if config_token:
        return config_token
    if config_token_file:
        try:
            return Path(config_token_file).read_text().strip()
        except OSError:
            pass
    return None


class AuthService:
    """Stateless token- and origin-verification for the admin HTTP endpoints.

    Extracted from :class:`AdminRequestHandler` (issue #572). Holds the pure
    authentication/authorization logic: it receives the already-extracted
    request fields plus the configured expectations, raises :class:`AuthError`
    / :class:`SecurityError` on failure and returns ``None`` on success. The
    handler keeps thin ``_check_token`` / ``_check_origin`` wrappers that feed
    it the per-request headers and the class-level server configuration, so the
    HTTP layer stays free of auth business logic.
    """

    @staticmethod
    def check_token(
        *,
        expected: str | None,
        auth_header: str,
        query: str,
        allow_query_token: bool,
    ) -> None:
        """Verify the admin token when token auth is configured.

        Accepts the token from ``Authorization: Bearer <token>``. The
        ``?token=<token>`` query parameter is honoured **only** when
        ``allow_query_token`` is ``True`` (the single opt-in is the SSE
        ``/api/events`` endpoint, whose ``EventSource`` client cannot set
        headers — issue #577). When ``expected`` is ``None`` no token is
        configured (loopback-only mode) and the check is a no-op.

        Raises :class:`AuthError` on mismatch or a missing token.
        """
        if expected is None:
            return  # No token configured → no check needed (loopback-only mode)

        if auth_header.startswith("Bearer "):
            provided = auth_header[7:]  # len("Bearer ") == 7
            if _verify_token(provided, expected):
                return

        if allow_query_token:
            token_list = parse_qs(query).get("token", [])
            if token_list and _verify_token(token_list[0], expected):
                return

        raise AuthError("invalid or missing admin token")

    @staticmethod
    def check_origin(
        *,
        origin: str | None,
        host: str,
        allowed_hosts: Iterable[str],
        bind_host: str,
        bind_port: int,
    ) -> None:
        """Reject mutating requests whose Origin/Host is not allow-listed.

        Contract (issue #588):

        - ``origin`` **present** (including the empty string): must equal one of
          ``http://<allowed-host>:<bind-port>`` exactly; an empty string is
          *present but invalid* and therefore rejected.
        - ``origin`` **absent** (``None``): only the Host header is checked —
          curl/wget and other non-browser CLI clients omit Origin and must stay
          usable for local admin scripting.
        - In both cases ``host`` must equal ``<allowed-host>:<bind-port>`` or the
          actual ``<bind-host>:<bind-port>``. A missing/malformed Host header is
          rejected.

        Raises :class:`SecurityError` on any mismatch.
        """
        allowed = list(allowed_hosts)
        if origin is not None:
            allowed_origins = {f"http://{h}:{bind_port}" for h in allowed}
            if origin not in allowed_origins:
                raise SecurityError(f"origin not allowed: {origin!r}")

        allowed_host_values = {f"{h}:{bind_port}" for h in allowed}
        # Always allow the actual bind host (covers explicit ``--host``).
        allowed_host_values.add(f"{bind_host}:{bind_port}")
        if host not in allowed_host_values:
            raise SecurityError(f"host header not allowed: {host!r}")


def _warn_if_world_readable(path: Path) -> None:
    """Print a stderr warning if ``path`` is readable by group or other.

    ``.meta-config/project.yaml`` can hold a plaintext admin token
    (``admin-ui.token``); with a typical ``022`` umask a freshly created file
    is world-readable, letting any other local user read the token (issue
    #589). Best-effort / non-fatal: startup must not break on platforms or
    filesystems without POSIX permission bits.
    """
    if not path.exists():
        return
    try:
        mode = path.stat().st_mode
    except OSError:
        return
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        print(
            f"  !  WARNING: {path} is readable by group/other users "
            f"(mode {oct(mode & 0o777)}). It may contain a plaintext admin "
            f"token — run: chmod 600 {path}",
            file=sys.stderr,
        )


# --------------------------------------------------------------------------- #
# Mode detection                                                              #
# --------------------------------------------------------------------------- #


def detect_mode(root: Path) -> str:
    """Return ``"super_admin"`` if ``agents/1-generic/`` exists, otherwise
    ``"project_admin"``.

    The presence of the generic agent templates is the canonical marker of the
    agent-meta framework repository itself. A target project never carries
    these files (it consumes them through the submodule).
    """
    return "super_admin" if (root / "agents" / "1-generic").is_dir() else "project_admin"


# --------------------------------------------------------------------------- #
# Config manager                                                              #
# --------------------------------------------------------------------------- #


class ConfigManager:
    """Read/write YAML configuration files with backup + atomic write.

    All filesystem access is mediated by :py:meth:`resolve_path`, which is the
    only place that maps logical keys to actual paths. Unknown keys raise a
    :class:`SecurityError` — there is no fallback to user-supplied paths.
    """

    def __init__(self, root: Path, mode: str) -> None:
        self.root = root.resolve()
        self.mode = mode

    # ------------------------------------------------------------------ #
    # Path resolution                                                    #
    # ------------------------------------------------------------------ #

    def _allowed_keys(self) -> dict[str, str]:
        # Always allow reading both so project_admin mode can view framework defaults
        return {**PROJECT_FILES, **SUPER_ADMIN_FILES}

    def resolve_path(self, key: str) -> Path:
        """Translate a logical config key (e.g. ``role-defaults``) to its
        absolute path on disk.

        Supports both layouts for super-admin files:
          * ``<root>/config/...``           — top-level checkout of agent-meta
          * ``<root>/.agent-meta/config/...`` — agent-meta as a submodule

        If a file already exists in the submodule layout, that path is
        returned to keep edits consistent with the rest of the code base
        (``_build_agent_hierarchy``, ``_find_schema_path``). Otherwise the
        primary path is returned (the file may not exist yet).

        Deliberately mode-agnostic: ``_allowed_keys()`` always returns both
        ``PROJECT_FILES`` and ``SUPER_ADMIN_FILES`` so project_admin mode can
        still *view* framework defaults (e.g. ``role-defaults``). The write
        boundary for project_admin mode is enforced in :py:meth:`write`, not
        here -- resolving a path is not the same as being allowed to write it.

        Raises:
            SecurityError: if ``key`` is unknown, or the resolved path would
                escape ``root`` (path traversal protection). Does NOT raise
                for mode restrictions -- see :py:meth:`write`.
        """
        if not isinstance(key, str) or not key:
            raise SecurityError("invalid config key")
        if any(sep in key for sep in ("/", "\\", "..")):
            raise SecurityError(f"path traversal attempt blocked: {key!r}")

        mapping = self._allowed_keys()
        rel = mapping.get(key)
        if rel is None:
            raise SecurityError(f"config key not in whitelist: {key!r}")

        primary = (self.root / rel).resolve()
        # Only super-admin config keys live under ``config/`` — fall back to the
        # submodule layout (``.agent-meta/config/``) if the primary path does
        # not exist there. Project-admin files (.meta-config/...) never get a
        # fallback (they are always at the project root).
        if rel.startswith("config/") and not primary.exists():
            fallback = (self.root / ".agent-meta" / rel).resolve()
            if fallback.exists():
                target = fallback
            else:
                target = primary
        else:
            target = primary

        # Ensure the resolved path stays within the project root.
        try:
            target.relative_to(self.root)
        except ValueError as exc:  # pragma: no cover - defence in depth
            raise SecurityError(f"resolved path escapes root: {target}") from exc
        return target

    # ------------------------------------------------------------------ #
    # Read / write                                                       #
    # ------------------------------------------------------------------ #

    def read(self, key: str) -> dict:
        """Load and return a YAML file as a Python dict. Returns ``{}`` if the
        file does not exist (so the UI can render an empty form)."""
        path = self.resolve_path(key)
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if data is not None else {}

    def write(self, key: str, data: Any) -> dict:
        """Write a Python object back as YAML using atomic replace + backup.
        
        Returns a status dict describing where the backup was stored.
        """
        if self.mode != "super_admin" and key in SUPER_ADMIN_FILES and key not in PROJECT_FILES:
            raise SecurityError(f"Cannot write super-admin config '{key}' in project mode.")

        # Guard against corrupting a YAML config file with a scalar payload
        # (e.g. PUT /api/config/role-defaults with body "just a string").
        # A valid config document is always a mapping or a sequence.
        if not isinstance(data, (dict, list)):
            raise ValueError("Invalid payload type: expected object")  # noqa: TRY004
        path = self.resolve_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        backup_info: str | None = None
        if path.exists():
            backup_info = self._backup(path)
            self._prune_backups(path)

        tmp_path = path.with_suffix(path.suffix + ".tmp")
        try:
            with tmp_path.open("w", encoding="utf-8") as fh:
                yaml.dump(
                    data,
                    fh,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
            os.replace(tmp_path, path)
        except Exception:
            # Never leave an orphaned .tmp behind if yaml.dump or os.replace
            # fails — that would surface as confusing diff noise on the next run.
            tmp_path.unlink(missing_ok=True)
            raise

        if key in PROJECT_FILES:
            # PROJECT_FILES (``.meta-config/*.yaml``) are per-instance runtime
            # config that can hold plaintext secrets (``admin-ui.token``,
            # MCP/external-tool credentials) — unlike SUPER_ADMIN_FILES
            # (``config/*.yaml``), which are framework templates meant to be
            # git-committed and shared. Restrict to owner-only (issue #589);
            # best-effort — not fatal on platforms/filesystems without POSIX
            # permission bits (e.g. some Windows/FAT mounts).
            try:
                os.chmod(path, 0o600)
            except OSError:  # pragma: no cover - platform-dependent
                pass

        return {
            "status": "saved",
            "key": key,
            "path": str(path.relative_to(self.root)),
            "backup": backup_info,
        }

    # ------------------------------------------------------------------ #
    # Backup helpers                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _backup(path: Path) -> str:
        """Create a timestamped backup copy of ``path`` next to the original.

        Uses UTC (issue #589) — a naive local-time timestamp is ambiguous
        across instances/hosts in different timezones (which backup is
        newer? sorting by filename breaks if clocks/timezones drift), and
        silently shifts if the host timezone ever changes.
        """
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_UTC")
        backup_path = path.with_suffix(path.suffix + f".bak.{stamp}")
        backup_path.write_bytes(path.read_bytes())
        return str(backup_path.name)

    @staticmethod
    def _prune_backups(path: Path) -> None:
        """Keep at most ``MAX_BACKUPS`` backup copies, deleting the oldest."""
        pattern = f"{path.name}.bak.*"
        backups = sorted(
            path.parent.glob(pattern),
            key=lambda p: p.stat().st_mtime,
        )
        # ``backups[:-MAX_BACKUPS]`` is the oldest slice that exceeds the cap.
        # If ``len(backups) <= MAX_BACKUPS`` the slice is empty and the loop
        # is a no-op.
        for old in backups[:-MAX_BACKUPS]:
            old.unlink(missing_ok=True)


# --------------------------------------------------------------------------- #
# Sync executor                                                               #
# --------------------------------------------------------------------------- #


class SyncExecutor:
    """Run ``sync.py`` as a subprocess and capture its output."""

    #: Sidecar file that records metadata about the most recent sync run.
    STATUS_FILE = Path(".meta-viz") / "sync-status.json"

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        # Fallback to the submodule layout for target repos that embed
        # agent-meta under ``.agent-meta/``.
        self.sync_script = resolve_asset(self.root, "scripts", "sync.py")

    def _run(self, extra_args: list[str]) -> dict:
        if not self.sync_script.exists():
            return {
                "success": False,
                "output": f"sync.py not found at {self.sync_script}",
                "returncode": -1,
            }
        cmd = [sys.executable, str(self.sync_script), *extra_args]
        try:
            proc = subprocess.run(  # noqa: PLW1510
                cmd,
                cwd=str(self.root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
            )
            output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
            result = {
                "success": proc.returncode == 0,
                "output": output,
                "returncode": proc.returncode,
                "command": " ".join(cmd),
            }
        except subprocess.TimeoutExpired:
            result = {"success": False, "output": "sync.py timed out (300s)", "returncode": -1}
        except Exception as exc:  # pragma: no cover  # noqa: BLE001
            result = {"success": False, "output": f"sync.py failed: {exc}", "returncode": -1}
        self._record_run(result)
        return result

    @staticmethod
    def _extract_summary(output: str) -> str | None:
        """Return the sync SUMMARY line (e.g. ``61 action(s) | 89 skipped | ...``)."""
        for line in output.splitlines():
            stripped = line.strip()
            if "action(s)" in stripped and "skipped" in stripped:
                return stripped
        return None

    def _record_run(self, result: dict) -> None:
        """Persist run metadata to ``.meta-viz/sync-status.json``."""
        status_path = self.root / self.STATUS_FILE
        payload = {
            "last_run_timestamp": datetime.now(timezone.utc).isoformat(),
            "last_run_exit_code": result.get("returncode"),
            "last_run_summary": self._extract_summary(result.get("output", "")),
        }
        try:
            status_path.parent.mkdir(parents=True, exist_ok=True)
            status_path.write_text(
                json.dumps(payload, indent=2), encoding="utf-8"
            )
        except OSError:
            pass  # status persistence is best-effort

    def dry_run(self) -> dict:
        """Execute ``sync.py --validate``. The flag is used because ``--dry-run``
        in agent-meta still touches some artefacts; ``--validate`` is a pure
        read-only check that returns a diff-like report."""
        return self._run(["--validate"])

    def run(self) -> dict:
        """Execute a real ``sync.py`` run (no extra flags)."""
        return self._run([])

    def render_standalone(self) -> dict:
        """Execute ``sync.py --render-standalone``: regenerate the fully
        self-contained, English-only agent personas under ``standalone/``
        that don't require a Python install to use."""
        return self._run(["--render-standalone"])

    def status(self) -> dict:
        """Return current sync status for the admin UI.

        Combines persisted run metadata (``.meta-viz/sync-status.json``) with
        live filesystem checks for context hashes and pending tasks.
        """
        status = {
            "last_run_timestamp": None,
            "last_run_exit_code": None,
            "last_run_summary": None,
            "context_hashes_present": (
                self.root / ".meta-config" / "context-hashes.json"
            ).exists(),
            "pending_tasks_present": self._has_pending_tasks(),
        }
        status_path = self.root / self.STATUS_FILE
        if status_path.exists():
            try:
                saved = json.loads(status_path.read_text(encoding="utf-8"))
                for key in ("last_run_timestamp", "last_run_exit_code", "last_run_summary"):
                    status[key] = saved.get(key)
            except (OSError, json.JSONDecodeError):
                pass
        return status

    def _has_pending_tasks(self) -> bool:
        """True if ``.claude/pending-tasks.md`` exists with at least one open item."""
        pending = self.root / ".claude" / "pending-tasks.md"
        if not pending.exists():
            return False
        try:
            return any(
                line.lstrip().startswith("- [ ]")
                for line in pending.read_text(encoding="utf-8").splitlines()
            )
        except OSError:
            return False


# --------------------------------------------------------------------------- #
# Config watcher                                                              #
# --------------------------------------------------------------------------- #


class ConfigWatcher(threading.Thread):
    """Polls configuration files for changes and appends events to
    ``.meta-viz/events.jsonl`` so the live dashboard can react.

    Pure polling is used to remain dependency-free (no ``watchdog``).
    """

    daemon = True

    def __init__(self, root: Path, interval: float = 2.0) -> None:
        super().__init__(name="ConfigWatcher")
        self.root = root.resolve()
        self.interval = interval
        self._stop_event = threading.Event()
        self._mtimes: dict[Path, float] = {}
        self._events_path = self.root / ".meta-viz" / "events.jsonl"
        self._subscribers: list[queue.Queue] = []
        self._subscribers_lock = threading.Lock()

    def stop(self) -> None:
        self._stop_event.set()

    def subscribe(self) -> queue.Queue:
        """Register a listener for config change events.

        Returns a fresh :class:`queue.Queue`. Emitted event dicts are pushed to
        every registered queue; consumers call ``get(timeout=...)`` and catch
        :class:`queue.Empty` for heartbeats. The SSE handler owns one queue per
        open connection.
        """
        q: queue.Queue = queue.Queue()
        with self._subscribers_lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        """Remove a previously registered listener queue."""
        with self._subscribers_lock:
            try:
                self._subscribers.remove(q)
            except ValueError:
                pass

    def _tracked_files(self) -> Iterable[Path]:
        for rel in {**PROJECT_FILES, **SUPER_ADMIN_FILES}.values():
            path = self.root / rel
            if path.exists():
                yield path

    def run(self) -> None:
        # Initial snapshot — do not fire events for already-present files.
        for path in self._tracked_files():
            try:
                self._mtimes[path] = path.stat().st_mtime
            except OSError:
                continue

        while not self._stop_event.is_set():
            for path in self._tracked_files():
                try:
                    mtime = path.stat().st_mtime
                except OSError:
                    continue
                prev = self._mtimes.get(path)
                if prev is None:
                    self._mtimes[path] = mtime
                    self._emit("config-created", path)
                elif mtime > prev:
                    self._mtimes[path] = mtime
                    self._emit("config-modified", path)
            self._stop_event.wait(self.interval)

    def _emit(self, event_type: str, path: Path) -> None:
        try:
            rel_path = str(path.relative_to(self.root))
        except ValueError:
            rel_path = str(path)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "path": rel_path,
        }
        try:
            self._events_path.parent.mkdir(parents=True, exist_ok=True)
            with self._events_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:  # pragma: no cover - best effort
            pass
        # Fan out to live SSE subscribers regardless of file-write success.
        with self._subscribers_lock:
            subscribers = list(self._subscribers)
        for q in subscribers:
            try:
                q.put_nowait(entry)
            except queue.Full:  # pragma: no cover - best effort
                pass


# --------------------------------------------------------------------------- #
# Request handler                                                             #
# --------------------------------------------------------------------------- #


def _generic_error_response(
    exc: Exception, error_code: str = "ERR_INTERNAL"
) -> tuple[int, dict[str, str]]:
    """Log ``exc`` with full server-side detail and return a generic,
    client-safe ``(status, body)`` pair.

    Raw exception text (absolute file paths, internal variable/function names,
    library-internal details) must never reach an HTTP client — it helps an
    attacker map the server's filesystem and architecture (issue #581). The
    stable ``error_code`` lets client-side handling distinguish failure modes
    without any leaked detail. Shared by :meth:`AdminRequestHandler._handle_error`
    and the extracted service classes (issue #572).
    """
    logger.error("%s: %s", error_code, exc, exc_info=True)
    return 500, {"error": error_code, "message": "Internal server error"}


class ServiceContext:
    """Live view onto the shared collaborators an :class:`AdminRequestHandler`
    exposes, handed to the extracted service classes (issue #572).

    Attributes are read off the handler **class** on every access, so the
    established unit-test seam — reassigning ``AdminRequestHandler.root`` /
    ``.config_manager`` on a handler built via ``__new__`` — is always
    reflected. This keeps the domain services free of any direct back-reference
    into the HTTP handler for framework state.
    """

    def __init__(self, handler_cls: type, handler: AdminRequestHandler | None = None) -> None:
        self._handler_cls = handler_cls
        self._handler = handler

    @property
    def handler(self) -> AdminRequestHandler | None:
        """The live handler instance, when a service was built for one request.

        Services route calls to methods that unit tests monkeypatch on the
        handler *instance* (notably ``_load_models_dev_data``, the models.dev
        cache/network seam) through this reference so those mocks still take
        effect after the logic moved into a service (issue #572)."""
        return self._handler

    @property
    def handler_cls(self) -> type:
        """The AdminRequestHandler class itself — used by :class:`ModelsService`
        as the store for its process-wide models.dev cache (the attributes the
        unit tests seed and reset directly)."""
        return self._handler_cls

    @property
    def root(self) -> Path:
        return self._handler_cls.root

    @property
    def config_manager(self) -> ConfigManager:
        return self._handler_cls.config_manager

    @property
    def mode(self) -> str:
        return self._handler_cls.mode

    @property
    def version(self) -> str:
        return self._handler_cls.version

    def agent_meta_root(self) -> Path:
        """Resolve the agent-meta framework root for lib helpers.

        In super_admin mode the server root is the framework checkout; in
        project_admin mode the framework sources live under ``.agent-meta/``.
        """
        root = self.root
        if (root / "agents" / "1-generic").is_dir():
            return root
        submodule = root / ".agent-meta"
        if (submodule / "agents" / "1-generic").is_dir():
            return submodule
        return root

    def ensure_lib_on_path(self) -> None:
        """Ensure ``scripts/lib`` is on ``sys.path`` for framework imports."""
        lib = self.root / "scripts" / "lib"
        if str(lib) not in sys.path:
            sys.path.insert(0, str(lib))

    def role_defaults_path(self) -> Path:
        """Resolve ``config/role-defaults.yaml`` for either layout — shared by
        the template, pipeline and reflection services."""
        return resolve_asset(self.root, "config", "role-defaults.yaml")


class AuditService:
    """Consistency checks, config audit, external-tool drift and provider
    (de)activation — the read-only/analysis business domain extracted from
    :class:`AdminRequestHandler` (issue #572).

    Methods return plain data (or raise) — the handler keeps thin wrappers that
    format the HTTP response. Internal failure branches reuse
    :func:`_generic_error_response` so no raw exception text leaks (issue #581).
    """

    def __init__(self, ctx: ServiceContext) -> None:
        self._ctx = ctx

    def run_consistency_check(self) -> dict:
        """Run the overall repository consistency check and return JSON."""
        import json
        import subprocess
        import sys
        # Layout-aware resolution (issue #587): in project_admin (submodule)
        # mode the script lives under ".agent-meta/scripts/", not the top-level
        # "scripts/" — use the same resolution every other asset lookup uses.
        check_script = resolve_asset(self._ctx.root, "scripts", "consistency-check.py")
        try:
            r = subprocess.run(  # noqa: PLW1510
                [sys.executable, str(check_script), "--json"],
                cwd=str(self._ctx.root),
                capture_output=True,
                text=True,
            )
            # consistency-check.py --json prints pure JSON to stdout regardless
            # of exit code.
            return json.loads(r.stdout)
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse JSON output",
                "output": r.stdout,
                "findings": [],
                "summary": {"total": 0, "errors": 0, "warnings": 0},
            }
        except Exception as exc:  # noqa: BLE001
            _, body = _generic_error_response(exc, "ERR_CONSISTENCY_CHECK")
            return {
                "error": body["error"],
                "findings": [],
                "summary": {"total": 0, "errors": 0, "warnings": 0},
            }

    def run_config_audit(self) -> dict:
        """Run the consistency audit over the current configuration."""
        self._ctx.ensure_lib_on_path()
        import dataclasses

        from lib.config_audit import audit_config
        project_config_path = self._ctx.root / ".meta-config" / "project.yaml"
        report = audit_config(self._ctx.root, project_config_path)
        return {
            "has_issues": report.has_issues,
            "errors": [dataclasses.asdict(i) for i in report.errors],
            "warnings": [dataclasses.asdict(i) for i in report.warnings],
            "issues": [dataclasses.asdict(i) for i in report.issues],
        }

    def apply_config_audit(self) -> dict:
        """Apply safe fixes reported by the consistency audit."""
        self._ctx.ensure_lib_on_path()
        from lib.config_audit import apply_audit, audit_config
        project_config_path = self._ctx.root / ".meta-config" / "project.yaml"
        report = audit_config(self._ctx.root, project_config_path)
        count = apply_audit(report, project_config_path)
        return {"fixed": count}

    def compute_injection_drift(self) -> dict:
        """Return undeclared external-tool artifacts per active provider."""
        project_root = self._ctx.root
        try:
            _ensure_scripts_on_path(project_root)
            from lib.external_tools import scan_injection_drift  # type: ignore[import]
            from lib.providers import load_providers_config  # type: ignore[import]

            # agent_meta_root, NOT project_root: in project_admin (submodule)
            # mode the framework's config/ai-providers.yaml and
            # config/external-tools-registry.yaml live under .agent-meta/, not
            # the project root — passing project_root there silently finds
            # nothing and produces false-positive "undeclared artifact"
            # findings for every legitimately registered tool/provider.
            agent_meta_root = self._ctx.agent_meta_root()
            project_config = self._ctx.config_manager.read("project")
            provider_config = load_providers_config(agent_meta_root)
            findings = scan_injection_drift(agent_meta_root, project_root, project_config, provider_config)
            return {"findings": findings}
        except Exception as exc:  # noqa: BLE001
            _, body = _generic_error_response(exc, "ERR_INJECTION_DRIFT")
            return body

    def deactivation_status(self) -> dict:
        """Return current provider deactivation status."""
        root = self._ctx.root
        try:
            _ensure_scripts_on_path(root)
            from lib.deactivation import get_deactivation_status  # type: ignore[import]
            from lib.providers import load_providers_config  # type: ignore[import]

            project_config = self._ctx.config_manager.read("project")
            provider_config = load_providers_config(root)
            return get_deactivation_status(root, project_config, provider_config)
        except Exception as exc:  # noqa: BLE001
            _, body = _generic_error_response(exc, "ERR_DEACTIVATION_STATUS")
            return body

    def deactivate_providers(self, providers: list) -> dict:
        """Deactivate ``providers`` (zip + remove their directories) and return
        the result payload. Raises on failure — the caller formats the error."""
        root = self._ctx.root
        _ensure_scripts_on_path(root)
        from lib.deactivation import (  # type: ignore[import]
            deactivate_providers,
            get_deactivation_status,
        )
        from lib.providers import load_providers_config  # type: ignore[import]

        project_config = self._ctx.config_manager.read("project")
        provider_config = load_providers_config(root)
        results = deactivate_providers(
            root, providers if providers else ["all"],
            provider_config, project_config, _NullDeactivationLog(), dry_run=False,
        )
        return {
            "success": True,
            "results": results,
            "status": get_deactivation_status(root, project_config, provider_config),
        }

    def activate_providers(self, providers: list) -> dict:
        """Activate ``providers`` (restore from backup zips) and return the
        result payload. Raises on failure — the caller formats the error."""
        root = self._ctx.root
        _ensure_scripts_on_path(root)
        from lib.deactivation import (  # type: ignore[import]
            activate_providers,
            get_deactivation_status,
        )
        from lib.providers import load_providers_config  # type: ignore[import]

        project_config = self._ctx.config_manager.read("project")
        provider_config = load_providers_config(root)
        results = activate_providers(
            root, providers,
            provider_config, project_config, _NullDeactivationLog(), dry_run=False,
        )
        return {
            "success": True,
            "results": results,
            "status": get_deactivation_status(root, project_config, provider_config),
        }


class _NullDeactivationLog:
    """Silent logger sink accepted by the ``lib.deactivation`` helpers."""

    def info(self, *a: Any) -> None: ...
    def warn(self, *a: Any) -> None: ...
    def error(self, *a: Any) -> None: ...


class TemplateService:
    """Agent-template discovery, resolution, reading and writing — the template
    business domain extracted from :class:`AdminRequestHandler` (issue #572).

    Methods return plain data (or raise) and the handler keeps thin wrappers
    that format the HTTP response.
    """

    def __init__(self, ctx: ServiceContext) -> None:
        self._ctx = ctx

    def find_schema_path(self) -> Path:
        return resolve_asset(self._ctx.root, "config", "project-config.schema.json")

    def template_path(self, role: str) -> Path | None:
        """Resolve the template path sync.py would actually use for this role.

        Delegates to ``lib.frontmatter.collect_sources`` — the SAME resolution
        sync.py itself uses (1-generic < 2-platform < 3-project, scoped to this
        project's own active ``platforms`` list, in list order). Globbing all of
        ``agents/2-platform/*.md`` instead would let an unrelated but
        same-named platform override (e.g. ``sharkord-developer.md``) be loaded
        AND saved in filesystem order — see the original method's history.
        """
        if not role or any(c in role for c in ("/", "\\", "..")):
            raise SecurityError(f"invalid role name: {role!r}")
        safe = "".join(ch for ch in role if ch.isalnum() or ch in ("-", "_"))
        if safe != role:
            raise SecurityError(f"invalid role name: {role!r}")
        agent_meta_root = self._ctx.agent_meta_root()
        candidate = agent_meta_root / "agents" / "1-generic" / f"{role}.md"
        try:
            project_root = self._ctx.root
            _ensure_scripts_on_path(project_root)
            from lib.frontmatter import collect_sources  # type: ignore[import]
            project_config = self._ctx.config_manager.read("project") or {}
            active_platforms = project_config.get("platforms", [])
            overrides, _ = collect_sources(agent_meta_root, active_platforms)
            resolved = overrides.get(role)
            if resolved is not None:
                return resolved
        except Exception:  # noqa: BLE001
            # Fall through to the plain generic-template path — better to edit
            # the generic base than to error out of the Templates page.
            pass
        return candidate

    def read_template_description(self, role: str) -> str:
        """Read the ``description`` from a generated template's frontmatter."""
        try:
            path = self.template_path(role)
        except SecurityError:
            return ""
        if not path or not path.exists():
            return ""
        with path.open("r", encoding="utf-8") as fh:
            text = fh.read()
        if not text.startswith("---"):
            return ""
        try:
            _, front, _ = text.split("---", 2)
            front_data = yaml.safe_load(front) or {}
            desc = front_data.get("description")
            if isinstance(desc, str):
                return desc.strip()
        except Exception:  # noqa: BLE001, S110
            pass
        return ""

    def list_agent_templates(self) -> dict:
        """Return the agent templates available for generation (top-level
        ``agents/1-generic`` first, then the submodule layout)."""
        templates_dir = resolve_asset(self._ctx.root, "agents", "1-generic")
        if not templates_dir.is_dir():
            return {"templates": [], "available": False}
        names = sorted(
            p.stem for p in templates_dir.glob("*.md")
            if p.is_file() and not p.name.startswith("_")
        )
        return {"templates": names, "available": True}

    def build_agent_hierarchy(self) -> dict:
        """Derive a lightweight role hierarchy from ``config/role-defaults.yaml``.

        Falls back to an empty list when the file is missing (project-admin mode
        without super-admin configs). Each role entry carries name/tier/model/
        memory/parallel/permission_mode, a never-empty ``description`` (falls
        back to the template frontmatter) and ``targets`` (delegation targets).
        """
        role_defaults_path = self._ctx.role_defaults_path()
        roles: list[dict] = []

        if role_defaults_path.exists():
            with role_defaults_path.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
            raw = data.get("roles") or data
            if isinstance(raw, dict):
                for name, attrs in raw.items():
                    if not isinstance(attrs, dict):
                        continue
                    handoff = attrs.get("handoff") or {}
                    targets_raw = handoff.get("target_roles") if isinstance(handoff, dict) else None
                    targets: list[str] = []
                    if isinstance(targets_raw, list):
                        targets = [str(t) for t in targets_raw if isinstance(t, str) and t]

                    description = attrs.get("description") or ""
                    if not description:
                        description = self.read_template_description(name)
                    if not description:
                        description = f"{name} agent (no description)"

                    roles.append({
                        "name": name,
                        "tier": (attrs.get("workflow_tier")
                                 or attrs.get("tier")
                                 or attrs.get("workflow-tier")
                                 or "optional"),
                        "model": attrs.get("model"),
                        "memory": attrs.get("memory"),
                        "parallel": bool(attrs.get("parallel", False)),
                        "permission_mode": attrs.get("permissionMode") or attrs.get("permission_mode"),
                        "description": description,
                        "targets": targets,
                        "group": attrs.get("group"),
                    })
        return {"roles": roles, "count": len(roles)}

    def write_template(self, role: str, body: Any) -> dict:
        """Validate and atomically write a template back to disk, returning the
        result payload. Raises ValueError/FileNotFoundError for the handler to
        map to 400/404."""
        if body is None:
            raise ValueError("empty body")
        # Frontend sends JSON ``{"content": "..."}``; a bare string body is
        # tolerated for backward compatibility with plain-text clients.
        if isinstance(body, dict):
            content = body.get("content")
        elif isinstance(body, str):
            content = body
        else:
            content = None
        if not isinstance(content, str):
            raise ValueError("expected 'content' field with template text")  # noqa: TRY004
        path = self.template_path(role)
        if not path:
            raise FileNotFoundError(f"template not found: {role}")
        cm = self._ctx.config_manager
        if path.exists():
            backup = cm._backup(path)
            cm._prune_backups(path)
        else:
            backup = None
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
        return {
            "status": "saved",
            "role": role,
            "backup": backup,
            "bytes": len(content.encode("utf-8")),
        }


class RoleDefaultsEditor:
    """Formatting-preserving editor for ``config/role-defaults.yaml``, shared by
    :class:`PipelineService` and :class:`ReflectionService` (issue #572).

    ``update_section`` replaces a single top-level section in place with a
    fine-grained, child-aware edit so untouched inner keys, list items and
    comments keep their original formatting; only new/changed children are
    re-serialised. ``load`` returns the parsed document (``{}`` when absent).
    """

    def __init__(self, ctx: ServiceContext) -> None:
        self._ctx = ctx

    def load(self) -> dict:
        """Return the parsed role-defaults document, or ``{}`` if missing/blank."""
        path = self._ctx.role_defaults_path()
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _indent_yaml_dump(value: Any, indent: int) -> list[str]:
        """Dump ``value`` to YAML and prefix every line with ``indent`` spaces."""
        raw = yaml.dump(
            value,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        if not raw.endswith("\n"):
            raw += "\n"
        out: list[str] = []
        for line in raw.splitlines(keepends=True):
            if line == "\n":
                out.append("\n")
            else:
                out.append(" " * indent + line)
        return out
    @staticmethod
    def _format_yaml_list_item(item: Any, indent: int, value_indent: int) -> list[str]:
        """Format a list item (``- key: value``) preserving nested indentation.

        ``indent`` is the column of the ``-`` marker; ``value_indent`` is the
        column used for the item's body lines.
        """
        lines = RoleDefaultsEditor._indent_yaml_dump(item, value_indent)
        if not lines:
            return [(" " * indent) + "- \n"]
        # The first dumped line already has ``value_indent`` spaces; replace
        # them with the list marker at ``indent``.
        first_content = lines[0][value_indent:]
        lines[0] = (" " * indent) + "- " + first_content
        return lines
    @staticmethod
    def _infer_child_value_indent(body_lines: list[str], base_indent: int) -> int:
        """Return the indentation used for a child mapping/list body.

        Falls back to ``base_indent + 2`` when the body is empty.
        """
        for line in body_lines:
            stripped = line.lstrip()
            if stripped in ("", "\n"):
                continue
            indent = len(line) - len(stripped)
            if indent > base_indent:
                return indent
        return base_indent + 2
    @staticmethod
    def _trailing_blank_lines(lines: list[str]) -> list[str]:
        """Return only the trailing blank/whitespace lines of a block."""
        last = -1
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() not in ("", "\n"):
                last = i
                break
        if last == -1:
            return lines[:]
        return lines[last + 1 :]
    @staticmethod
    def _extract_list_item_id(lines: list[str]) -> str | None:
        """Parse a single YAML list item and return its ``id`` field, if any."""
        try:
            data = yaml.safe_load("".join(lines))
            if isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict):
                return data[0].get("id")
        except Exception:  # noqa: BLE001, S110
            pass
        return None
    @staticmethod
    def _split_dict_children(body_lines: list[str], base_indent: int) -> list[dict]:
        """Locate top-level mapping keys inside a section body."""
        children: list[dict] = []
        i = 0
        n = len(body_lines)
        while i < n:
            line = body_lines[i]
            stripped = line.lstrip()
            if stripped in ("", "\n"):
                i += 1
                continue
            indent = len(line) - len(stripped)
            if indent < base_indent:
                break
            if indent == base_indent and not stripped.startswith("-") and ":" in stripped:
                key_name = stripped.split(":", 1)[0]
                start = i
                i += 1
                while i < n:
                    l = body_lines[i]
                    if l.strip() in ("", "\n"):
                        i += 1
                        continue
                    ind = len(l) - len(l.lstrip())
                    if ind < base_indent:
                        break
                    if ind == base_indent and not l.lstrip().startswith("-"):
                        break
                    i += 1
                children.append({"type": "dict", "key": key_name, "start": start, "end": i})
            else:
                i += 1
        return children
    @staticmethod
    def _split_list_children(body_lines: list[str], base_indent: int) -> list[dict]:
        """Locate top-level list items inside a section body."""
        children: list[dict] = []
        i = 0
        n = len(body_lines)
        while i < n:
            line = body_lines[i]
            stripped = line.lstrip()
            if stripped in ("", "\n"):
                i += 1
                continue
            indent = len(line) - len(stripped)
            if indent < base_indent:
                break
            if indent == base_indent and stripped.startswith("- "):
                start = i
                i += 1
                while i < n:
                    l = body_lines[i]
                    if l.strip() in ("", "\n"):
                        i += 1
                        continue
                    ind = len(l) - len(l.lstrip())
                    if ind <= base_indent:
                        break
                    i += 1
                children.append({"start": start, "end": i})
            else:
                i += 1
        return children
    @staticmethod
    def _splice_appended_children(
        new_lines: list[str], tail: list[str], appended_new: list[str]
    ) -> None:
        """Attach freshly appended children to ``new_lines`` in-place.

        New children are spliced in *after* the existing content but *before*
        ``tail`` — the trailing blank/comment lines that were captured with the
        section body but usually head the *following* top-level section (e.g.
        the ``# SE cascade variables`` comment that precedes ``se_variables:``).
        Placing new keys after that tail would glue them onto the comment line
        (the section-body regex drops the final newline before the next key),
        silently commenting the new key out. Newline boundaries are enforced so
        a new key can never land on the same physical line as a trailing comment.

        When there are no new children the tail is appended verbatim, preserving
        the exact byte layout of update-only and delete writes.
        """
        if not appended_new:
            new_lines.extend(tail)
            return
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] = new_lines[-1] + "\n"
        new_lines.extend(appended_new)
        if tail:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines[-1] = new_lines[-1] + "\n"
            new_lines.extend(tail)
    def _build_role_defaults_section_body(
        self, key: str, value: Any, body_lines: list[str]
    ) -> str:
        """Rebuild the body of a top-level ``role-defaults.yaml`` section.

        Dict sections (e.g. ``quality_pipelines``) are edited child-by-child.
        Children whose parsed value equals the new value keep their original
        formatting; only changed or new children are re-serialised. List
        sections with an ``id`` field (e.g. ``reflection_pairs``) are matched
        by id using the same rule. Comments and blank lines that are not part
        of a child block are preserved unchanged.
        """
        base_indent = 2
        value_indent = self._infer_child_value_indent(body_lines, base_indent)

        def _scalar_dump(v: Any) -> str:
            return yaml.dump(v, default_flow_style=True, allow_unicode=True).strip()

        def _build_dict_child(k: str, v: Any, child: dict | None) -> list[str]:
            if child:
                trailing = self._trailing_blank_lines(
                    body_lines[child["start"] : child["end"]]
                )
                if isinstance(v, (dict, list)):
                    header = body_lines[child["start"]]
                    child_value_indent = self._infer_child_value_indent(
                        body_lines[child["start"] + 1 : child["end"]], base_indent
                    )
                    value_lines = self._indent_yaml_dump(v, child_value_indent)
                    return [header] + value_lines + trailing
                else:
                    return [
                        " " * base_indent + k + ": " + _scalar_dump(v) + "\n"
                    ] + trailing
            else:
                if isinstance(v, (dict, list)):
                    header = " " * base_indent + k + ":\n"
                    value_lines = self._indent_yaml_dump(v, value_indent)
                    return [header] + value_lines + ["\n"]
                else:
                    return [
                        " " * base_indent + k + ": " + _scalar_dump(v) + "\n",
                        "\n",
                    ]

        def _build_list_child(item: dict, child: dict | None) -> list[str]:
            if child:
                trailing = self._trailing_blank_lines(
                    body_lines[child["start"] : child["end"]]
                )
                value_lines = self._format_yaml_list_item(item, base_indent, value_indent)
                return value_lines + trailing
            else:
                value_lines = self._format_yaml_list_item(item, base_indent, value_indent)
                return value_lines + ["\n"]

        def _assigned_indices(children: list[dict]) -> set[int]:
            indices: set[int] = set()
            for child in children:
                indices.update(range(child["start"], child["end"]))
            return indices

        if isinstance(value, dict):
            children = self._split_dict_children(body_lines, base_indent)
            old_by_key = {c["key"]: c for c in children if c["type"] == "dict"}
            # Line indices that belong to deleted children must be skipped so
            # that deleting a pipeline actually removes it from the written YAML.
            deleted_indices: set[int] = set()
            for old_key, old_child in old_by_key.items():
                if old_key not in value:
                    deleted_indices.update(range(old_child["start"], old_child["end"]))
            new_lines: list[str] = []
            pos = 0
            appended_new: list[str] = []
            for k, v in value.items():
                child = old_by_key.get(k)
                if child:
                    new_lines.extend(
                        body_lines[i]
                        for i in range(pos, child["start"])
                        if i not in deleted_indices
                    )
                    old_block = body_lines[child["start"] : child["end"]]
                    try:
                        parsed = yaml.safe_load("".join(old_block))
                        old_value = parsed.get(k) if isinstance(parsed, dict) else None
                    except Exception:  # noqa: BLE001
                        old_value = None
                    if old_value == v:
                        new_lines.extend(old_block)
                    else:
                        new_lines.extend(_build_dict_child(k, v, child))
                    pos = child["end"]
                else:
                    appended_new.extend(_build_dict_child(k, v, None))
            tail = [
                body_lines[i]
                for i in range(pos, len(body_lines))
                if i not in deleted_indices
            ]
            self._splice_appended_children(new_lines, tail, appended_new)
            return "".join(new_lines)

        if isinstance(value, list) and key == "reflection_pairs":
            children = self._split_list_children(body_lines, base_indent)
            old_by_id: dict[str, dict] = {}
            for child in children:
                item_id = self._extract_list_item_id(
                    body_lines[child["start"] : child["end"]]
                )
                if item_id:
                    old_by_id[item_id] = child

            new_lines: list[str] = []
            pos = 0
            appended_new: list[str] = []
            for item in value:
                if not isinstance(item, dict):
                    continue
                item_id = item.get("id")
                child = old_by_id.get(item_id) if item_id else None
                if child:
                    new_lines.extend(body_lines[pos : child["start"]])
                    old_block = body_lines[child["start"] : child["end"]]
                    try:
                        parsed = yaml.safe_load("".join(old_block))
                        old_value = parsed[0] if isinstance(parsed, list) and parsed else None
                    except Exception:  # noqa: BLE001
                        old_value = None
                    if old_value == item:
                        new_lines.extend(old_block)
                    else:
                        new_lines.extend(_build_list_child(item, child))
                    pos = child["end"]
                else:
                    appended_new.extend(_build_list_child(item, None))
            self._splice_appended_children(new_lines, body_lines[pos:], appended_new)
            return "".join(new_lines)

        # Fallback for any other shape: replace the whole body with a fresh dump.
        snippet = yaml.dump(
            {key: value},
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        lines = snippet.splitlines(keepends=True)
        if lines and lines[0].startswith(key + ":"):
            return "".join(lines[1:])
        return snippet

    def update_section(self, key: str, value: Any) -> dict:
        """Replace one top-level section of ``role-defaults.yaml`` in-place.

        Uses a fine-grained, child-aware edit so that untouched inner keys,
        list items, and comments keep their original formatting. Only new or
        changed children are re-serialised with PyYAML. Falls back to a full
        block dump when the section is missing or its structure is unexpected.
        Backup + atomic-replace rules mirror :class:`ConfigManager`.
        """
        import re

        path = self._ctx.role_defaults_path()
        original_text = path.read_text(encoding="utf-8") if path.exists() else ""
        text = original_text.replace("\r\n", "\n")

        # Skip the actual write if the parsed content is unchanged.
        try:
            parsed_original = yaml.safe_load(original_text) or {}
        except Exception:  # noqa: BLE001
            parsed_original = {}
        if isinstance(parsed_original, dict) and parsed_original.get(key) == value:
            return {
                "status": "unchanged",
                "key": key,
                "path": str(path.relative_to(self._ctx.root)),
                "backup": None,
            }

        block_re = re.compile(
            rf"^{re.escape(key)}:\s*(?:\n|$)"
            rf"(?P<body>.*?)"
            rf"(?=\n^[A-Za-z0-9_\-]+:\s*(?:\n|$)|\Z)",
            re.MULTILINE | re.DOTALL,
        )
        match = block_re.search(text)
        if not match:
            snippet = yaml.dump(
                {key: value},
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
            new_text = text.rstrip("\n") + "\n\n" + snippet
        else:
            section_start = match.start()
            section_end = match.end()
            header = text[section_start : match.start("body")]
            body_lines = match.group("body").splitlines(keepends=True)
            new_body = self._build_role_defaults_section_body(key, value, body_lines)
            new_text = text[:section_start] + header + new_body + text[section_end:]

        cm = self._ctx.config_manager
        if path.exists():
            backup = cm._backup(path)
            cm._prune_backups(path)
        else:
            backup = None
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(new_text, encoding="utf-8")
        os.replace(tmp, path)
        return {
            "status": "saved",
            "key": key,
            "path": str(path.relative_to(self._ctx.root)),
            "backup": backup,
        }


class PipelineService:
    """Quality-pipeline CRUD + help, backed by :class:`RoleDefaultsEditor`
    (issue #572)."""

    def __init__(self, ctx: ServiceContext) -> None:
        self._ctx = ctx
        self._editor = RoleDefaultsEditor(ctx)

    def read_pipelines(self) -> dict:
        """Return the ``quality_pipelines`` block in a stable envelope shape."""
        pipelines = self._editor.load().get("quality_pipelines") or {}
        if not isinstance(pipelines, dict):
            pipelines = {}
        return {"pipelines": pipelines}

    def read_single_pipeline(self, name: str) -> dict:
        """Return a single pipeline by name or raise."""
        pipelines = self.read_pipelines().get("pipelines", {})
        if name not in pipelines:
            raise FileNotFoundError(f"pipeline not found: {name}")
        return {"pipeline": pipelines[name]}

    def write_pipelines(self, pipelines: dict) -> dict:
        """Replace ONLY the ``quality_pipelines`` key in ``role-defaults.yaml``."""
        return self._editor.update_section("quality_pipelines", pipelines)

    def write_single_pipeline(self, name: str, pipeline: dict) -> dict:
        """Create or update a single pipeline by name."""
        all_pipelines = self.read_pipelines().get("pipelines", {})
        all_pipelines[name] = pipeline
        result = self.write_pipelines(all_pipelines)
        result["pipeline"] = pipeline
        result["name"] = name
        return result

    def delete_pipeline(self, name: str) -> dict:
        """Delete a single pipeline by name."""
        all_pipelines = self.read_pipelines().get("pipelines", {})
        if name not in all_pipelines:
            raise FileNotFoundError(f"pipeline not found: {name}")
        del all_pipelines[name]
        result = self.write_pipelines(all_pipelines)
        result["deleted"] = name
        return result

    def pipeline_help(self) -> dict:
        """Return comprehensive help documentation for the pipelines API."""
        pipeline_names = list(self.read_pipelines().get("pipelines", {}).keys())
        return {
            "help": {
                "title": "Quality Pipelines API",
                "version": self._ctx.version,
                "description": (
                    "Quality Pipelines define multi-stage workflows for agent orchestration. "
                    "Each pipeline consists of sequential, parallel, loop, or conditional stages "
                    "that delegate work to specific agents."
                ),
                "endpoints": {
                    "GET /api/pipelines": {
                        "description": "List all pipelines with their full stage definitions.",
                        "response": '{"pipelines": {"<name>": {...}}}',
                    },
                    "GET /api/pipelines?help": {
                        "description": "Show this help documentation.",
                        "response": '{"help": {...}}',
                    },
                    "GET /api/pipelines/<name>": {
                        "description": "Get a single pipeline by name.",
                        "response": '{"pipeline": {...}}',
                        "example": f"/api/pipelines/{pipeline_names[0]}" if pipeline_names else "/api/pipelines/standard-feature",
                    },
                    "PUT /api/pipelines": {
                        "description": "Replace ALL pipelines (whole-file replace with backup).",
                        "body": '{"pipelines": {"<name>": {...}}}',
                        "warning": "This replaces the entire quality_pipelines block. Use with care.",
                    },
                    "PUT /api/pipelines/<name>": {
                        "description": "Create or update a single pipeline by name.",
                        "body": '{"description": "...", "stages": [...], "on_error": "..."}',
                    },
                    "DELETE /api/pipelines/<name>": {
                        "description": "Delete a single pipeline by name.",
                        "response": '{"deleted": "<name>"}',
                    },
                },
                "pipeline_structure": {
                    "description": "string — human-readable description of the pipeline",
                    "on_error": "enum: escalate_to_orchestrator | skip | abort | retry",
                    "stages": [
                        {
                            "id": "string — unique stage identifier within the pipeline",
                            "agent": "string — role name of the agent to delegate to",
                            "task": "string — task description for the agent",
                            "mode": "enum: sequential | parallel_group | fanout | loop | conditional | agent_decision",
                            "loop": {
                                "description": "Only required when mode=loop",
                                "generator": "string — agent that produces output",
                                "critic": "string — agent that reviews output",
                                "max_iterations": "integer — loop limit (default 3)",
                            },
                            "condition": {
                                "description": "Only required when mode=conditional",
                                "type": "agent_decision",
                                "agent": "string — agent making the decision",
                            },
                            "parallel_group": {
                                "description": "Only required when mode=parallel_group",
                                "items": [{"agent": "string", "task": "string"}],
                            },
                        }
                    ],
                },
                "stage_modes_explained": {
                    "sequential": "Run one agent after another in sequence.",
                    "parallel_group": "Run multiple agents in parallel (fixed list).",
                    "fanout": "Split work across N independent instances of the same agent.",
                    "loop": "Generator→Critic loop for iterative refinement (e.g. implement→review).",
                    "conditional": "Agent decides which path to take next.",
                    "agent_decision": "Similar to conditional — agent makes a programmatic decision.",
                },
                "available_pipelines": pipeline_names,
            },
        }


class ReflectionService:
    """Reflection-pair CRUD, backed by :class:`RoleDefaultsEditor` (issue #572)."""

    def __init__(self, ctx: ServiceContext) -> None:
        self._ctx = ctx
        self._editor = RoleDefaultsEditor(ctx)

    def read_reflection_pairs(self) -> dict:
        """Return the ``reflection_pairs`` block (always a list, empty if absent)."""
        pairs = self._editor.load().get("reflection_pairs") or []
        if not isinstance(pairs, list):
            pairs = []
        return {"reflection_pairs": pairs}

    def read_reflection_pair(self, pair_id: str) -> dict:
        """Return a single reflection pair by ``id`` or raise."""
        for pair in self.read_reflection_pairs().get("reflection_pairs", []):
            if isinstance(pair, dict) and pair.get("id") == pair_id:
                return {"reflection_pair": pair}
        raise FileNotFoundError(f"reflection pair not found: {pair_id}")

    def write_reflection_pairs(self, pairs: list) -> dict:
        """Replace ONLY the ``reflection_pairs`` key in ``role-defaults.yaml``."""
        result = self._editor.update_section("reflection_pairs", pairs)
        result["reflection_pairs"] = pairs
        result["count"] = len(pairs)
        return result

    def ensure_pair_id(self, pair: dict, pair_id: str | None = None) -> str:
        """Return a valid id for a reflection pair, generating one if missing."""
        if pair_id:
            pair["id"] = pair_id
            return pair_id
        if not pair.get("id"):
            existing = self.read_reflection_pairs().get("reflection_pairs", [])
            base = pair.get("generator", "pair") + "-" + pair.get("critic", "critic")
            idx = 1
            candidate = f"{base}-{idx}"
            old_ids = {p.get("id") for p in existing if isinstance(p, dict)}
            while candidate in old_ids:
                idx += 1
                candidate = f"{base}-{idx}"
            pair["id"] = candidate
        return pair["id"]

    def write_reflection_pair(self, pair_id: str, pair: dict) -> dict:
        """Create or update a single reflection pair by id."""
        self.ensure_pair_id(pair, pair_id)
        pairs = self.read_reflection_pairs().get("reflection_pairs", [])
        found = False
        for i, existing in enumerate(pairs):
            if isinstance(existing, dict) and existing.get("id") == pair_id:
                pairs[i] = pair
                found = True
                break
        if not found:
            pairs.append(pair)
        result = self.write_reflection_pairs(pairs)
        result["reflection_pair"] = pair
        return result

    def delete_reflection_pair(self, pair_id: str) -> dict:
        """Delete a single reflection pair by id."""
        pairs = self.read_reflection_pairs().get("reflection_pairs", [])
        new_pairs = [p for p in pairs if not (isinstance(p, dict) and p.get("id") == pair_id)]
        if len(new_pairs) == len(pairs):
            raise FileNotFoundError(f"reflection pair not found: {pair_id}")
        result = self.write_reflection_pairs(new_pairs)
        result["deleted"] = pair_id
        return result

class ModelsService:
    """Model registry + pricing overlay + curation, the models.dev catalog
    (SDK snapshot / live API with class-level caching), provider/tier model
    resolution and suggestions — the model business domain extracted from
    :class:`AdminRequestHandler` (issue #572).

    The models.dev cache stays on the handler class (``ctx.handler_cls``):
    it is process-wide state the unit tests seed and reset directly, and the
    ``_MODELS_DEV_ERROR_TTL_SECONDS`` constant likewise lives on the handler.
    """

    # Overlay provider keys with no real models.dev catalog entry; kept in
    # sync with ``REGISTRY_ONLY`` in ``docs/ui/admin-ui.html``.
    CURATED_ONLY_PROVIDER_KEYS: ClassVar[set[str]] = {"mammouth", "continue"}

    def __init__(self, ctx: ServiceContext) -> None:
        self._ctx = ctx

    def _curation_root(self) -> Path:
        """Return the project root that owns ``config/model-curation.yaml``.

        Mirrors the layout-resolution used elsewhere in this handler: prefers
        the top-level checkout (``<root>/config/``) and falls back to the
        submodule layout (``<root>/.agent-meta/config/``) when the framework
        is embedded in a target repo.
        """
        # ``resolve_asset(root, "config")`` selects the layout by the presence of
        # the ``config/`` directory; its parent is the framework root that
        # ``load_curation``/``save_curation`` expect.
        return resolve_asset(self._ctx.root, "config").parent
    def _load_curation(self) -> dict:
        """Load ``config/model-curation.yaml`` via ``scripts.lib.curation``.

        The import is performed lazily (and ``sys.path`` is extended on demand)
        to mirror the pattern used by ``_load_viz_config`` at module level:
        the admin server must keep starting even when the ``lib`` package is
        not on ``sys.path`` at process boot.
        """
        root = self._ctx.root
        _ensure_scripts_on_path(root)
        from lib.curation import load_curation  # type: ignore[import]
        curation = load_curation(str(self._curation_root()))
        # ``load_curation`` already normalises shape; ensure keys exist for
        # downstream callers regardless of any future schema changes.
        curation.setdefault("blacklist", [])
        curation.setdefault("disabled", [])
        return curation
    def _save_curation(self, curation: dict) -> None:
        """Persist a curation document via ``scripts.lib.curation.save_curation``."""
        root = self._ctx.root
        _ensure_scripts_on_path(root)
        from lib.curation import save_curation  # type: ignore[import]
        save_curation(str(self._curation_root()), curation)
    def _collect_models(self) -> list[dict]:
        """Resolve the model registry + pricing overlay + curation into the
        enriched ``models`` list that powers both ``/api/models`` and
        ``/api/models/active``.

        Each entry exposes the legacy pricing fields (``input_cost``,
        ``output_cost``, ``cost_factor`` …) plus the new curation flags:

        * ``enabled``     — ``True`` unless the id is in ``curation.disabled``.
        * ``blacklisted`` — always ``False`` here. Blacklisted ids are filtered
          out during registry generation, so a blacklisted model never reaches
          this code path; the field is included for response-shape stability.
        """
        # Resolve the config dir once (submodule-aware) so registry + overlay
        # always share the same layout, even when either file is absent.
        config_dir = resolve_asset(self._ctx.root, "config")
        registry_path = config_dir / "generated" / "model-registry.json"
        pricing_path = config_dir / "pricing-overlay.yaml"

        override_registry = Path(self._ctx.root) / ".meta-config" / "generated" / "model-registry.json"
        
        models: list[dict] = []
        if override_registry.exists():
            models = json.loads(override_registry.read_text(encoding="utf-8")).get("models", [])
        elif registry_path.exists():
            models = json.loads(registry_path.read_text(encoding="utf-8")).get("models", [])

        pricing: dict = {}
        if pricing_path.exists():
            pricing = yaml.safe_load(pricing_path.read_text(encoding="utf-8")) or {}
        prices = pricing.get("prices", {}) if isinstance(pricing, dict) else {}

        curation = self._load_curation()
        # Tolerant comparison (see _normalized_model_id): curation entries
        # written against older registry id formats must keep matching.
        disabled_ids = {
            _normalized_model_id(x) for x in curation.get("disabled", [])
            if isinstance(x, str) and x
        }

        for m in models:
            provider = m.get("provider", "")
            model_id = m.get("id", "")
            model_name = m.get("name") or model_id

            api_input = m.get("input_cost_api", 0.0)
            api_output = m.get("output_cost_api", 0.0)

            provider_prices = prices.get(provider, {}) if isinstance(prices, dict) else {}
            model_prices = provider_prices.get(model_id, {}) if isinstance(provider_prices, dict) else {}

            overlay_input = model_prices.get("input") if isinstance(model_prices, dict) else None
            overlay_output = model_prices.get("output") if isinstance(model_prices, dict) else None

            input_cost = overlay_input if overlay_input is not None else api_input
            output_cost = overlay_output if overlay_output is not None else api_output

            input_source = "Overlay" if overlay_input is not None else "API"
            output_source = "Overlay" if overlay_output is not None else "API"

            # Blended cost per 1M tokens (30% input, 70% output)
            cost_factor = round((input_cost * 0.3) + (output_cost * 0.7), 2)

            m["name"] = model_name
            m["input_cost"] = input_cost
            m["output_cost"] = output_cost
            m["input_source"] = input_source
            m["output_source"] = output_source
            m["cost_factor"] = cost_factor
            m["source_url"] = provider_prices.get("_url", "") if isinstance(provider_prices, dict) else ""
            m["enabled"] = _normalized_model_id(model_id) not in disabled_ids
            # Blacklisted ids are filtered during discovery and never appear in
            # the registry; surfaced models are therefore always non-blacklisted.
            m["blacklisted"] = False

        return models
    def _load_models_dev_data(self, force_refresh: bool = False) -> dict:
        """Load the models.dev catalog payload (class-level cached).

        Normal resolution order: fresh in-memory cache → SDK snapshot
        (``node_modules/@opencode-ai/models``) → live models.dev API → stale
        cache → short-TTL negative cache of the last total failure. An
        explicit ``force_refresh`` (the UI's ↻ button) bypasses all caches
        and reverses API/SDK precedence so a refresh actually reaches the
        network even when a stale SDK snapshot exists.

        A total failure returns ``{"source": "error", "error": <reason>,
        "providers": {}, "models": {}}`` and is negative-cached for
        ``_MODELS_DEV_ERROR_TTL_SECONDS`` so an unreachable network cannot
        turn every request into a fresh 30 s blocking fetch attempt.
        """
        cls = self._ctx.handler_cls
        now = time.time()

        if not force_refresh:
            cache = getattr(cls, '_models_dev_cache', None)
            cache_ts = getattr(cls, '_models_dev_cache_ts', 0)
            if cache and cache.get('source') == 'sdk':
                return cache
            if cache and cache.get('source') == 'api' and (now - cache_ts) < 3600:
                return cache
            error_cache = getattr(cls, '_models_dev_error', None)
            if (isinstance(error_cache, tuple) and len(error_cache) == 2
                    and (now - error_cache[1]) < self._ctx.handler_cls._MODELS_DEV_ERROR_TTL_SECONDS):
                return error_cache[0]

        if force_refresh:
            # Explicit refresh: live data wins over the (potentially stale)
            # bundled SDK snapshot; the snapshot is the offline fallback.
            loaded = self._load_from_models_dev_api()
            if not loaded:
                loaded = self._load_from_sdk_snapshot()
        else:
            loaded = self._load_from_sdk_snapshot()
            if not loaded:
                loaded = self._load_from_models_dev_api()

        if loaded:
            cls._models_dev_cache = loaded
            cls._models_dev_cache_ts = time.time()
            if hasattr(cls, '_models_dev_error'):
                delattr(cls, '_models_dev_error')
            return loaded

        # Total failure — serve any stale cache before reporting the error,
        # and stamp it as the negative-cache entry so subsequent requests
        # within the TTL re-serve the stale payload WITHOUT re-attempting the
        # (up to 30 s blocking) fetch.
        stale = getattr(cls, '_models_dev_cache', None)
        if stale:
            cls._models_dev_error = (stale, time.time())
            return stale
        detail = getattr(cls, '_models_dev_last_fetch_error', '') or 'No data available'
        error_payload = {"source": "error", "error": detail, "providers": {}, "models": {}}
        cls._models_dev_error = (error_payload, time.time())
        return error_payload
    def _load_from_sdk_snapshot(self) -> dict | None:
        try:
            snapshot_path = resolve_asset(self._ctx.root, "node_modules",
                                          "@opencode-ai", "models", "dist", "snapshot.js")
            if not snapshot_path.exists():
                return None

            content = snapshot_path.read_text(encoding="utf-8")
            prefix = 'JSON.parse("'
            start = content.find(prefix)
            if start == -1:
                return None
            start += len(prefix)
            # Find closing ") before \nexport
            end = content.find('")' + '\nexport', start)
            if end == -1:
                # Fallback: find last ") before export
                export_pos = content.find('\nexport const providers', start)
                if export_pos == -1:
                    return None
                end = content.rfind('")', start, export_pos)
                if end == -1:
                    return None

            json_str = content[start:end]
            # Unescape JS string: \" → "  \\ → \
            json_str = json_str.replace('\\\\', '\x00bs\x00')
            json_str = json_str.replace('\\"', '"')
            json_str = json_str.replace('\x00bs\x00', '\\')
            data = json.loads(json_str)

            generated_at = ""
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("export const generatedAt = "):
                    quote_start = stripped.find('"')
                    if quote_start != -1:
                        quote_end = stripped.find('"', quote_start + 1)
                        if quote_end != -1:
                            generated_at = stripped[quote_start + 1:quote_end]
                    break

            return {
                "source": "sdk",
                "generated_at": generated_at,
                "providers": data.get("providers", {}),
                "models": data.get("models", {}),
            }
        except Exception as exc:  # noqa: BLE001
            self._ctx.handler_cls._models_dev_last_fetch_error = f"SDK snapshot read failed: {exc}"
            return None
    def _load_from_models_dev_api(self) -> dict | None:
        try:
            from urllib.request import Request, urlopen

            req = Request("https://models.dev/catalog.json",
                          headers={"User-Agent": "agent-meta-admin/1.0"})
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            # Success — clear any stale failure reason so the error payload
            # never reports an ancient message after a later recovery.
            self._ctx.handler_cls._models_dev_last_fetch_error = ""
            return {
                "source": "api",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "providers": data.get("providers", {}),
                "models": data.get("models", {}),
            }
        except Exception as exc:  # noqa: BLE001
            # Record WHY the fetch failed so the error payload returned to the
            # UI can explain itself instead of a bare "No data available".
            self._ctx.handler_cls._models_dev_last_fetch_error = f"models.dev fetch failed: {exc}"
            return None
    def _apply_pricing_overlay(self, providers: dict) -> dict:
        """Merge ``config/pricing-overlay.yaml`` on top of models.dev provider data.

        Two behaviors, mirroring how ``_collect_models`` already merges the
        overlay into the Legacy registry view:

        * **Override** — if the overlay's provider key matches a real
          models.dev provider id (e.g. ``anthropic``), matching model ids get
          their ``cost.input``/``cost.output`` replaced by the overlay value.
          Overridden models are tagged ``_costSource: "overlay"`` so the UI
          can surface provenance.
        * **Curated** — if the overlay's provider key is listed in
          ``CURATED_ONLY_PROVIDER_KEYS`` (no real models.dev catalog entry,
          e.g. Mammouth — a flat-fee multi-model gateway with no public
          per-token pricing), a synthetic provider node is added with
          ``source: "curated"`` so the models.dev live view can render it
          with a provenance badge instead of the previous strikethrough
          workaround.

        Returns a new dict; ``providers`` is not mutated in place (the caller
        may hold a reference to the cached models.dev payload).
        """
        config_dir = resolve_asset(self._ctx.root, "config")
        pricing_path = config_dir / "pricing-overlay.yaml"
        if not pricing_path.exists():
            return providers

        try:
            pricing = yaml.safe_load(pricing_path.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            return providers
        prices = pricing.get("prices", {}) if isinstance(pricing, dict) else {}
        if not isinstance(prices, dict):
            return providers

        merged = dict(providers)
        for provider_key, provider_prices in prices.items():
            if not isinstance(provider_prices, dict):
                continue
            model_entries = {
                k: v for k, v in provider_prices.items()
                if not k.startswith("_") and isinstance(v, dict)
            }
            if not model_entries:
                continue

            if provider_key in merged:
                # Override path: real models.dev provider — patch matching models only.
                provider_node = dict(merged[provider_key])
                models = dict(provider_node.get("models", {}))
                overlay_prefix = f"{provider_key}/"
                for model_id, price in model_entries.items():
                    # config/pricing-overlay.yaml key format is inconsistent
                    # across providers: anthropic/gemini/mammouth use bare ids
                    # matching models.dev directly, but opencode-go's ids are
                    # prefixed with "opencode-go/" (that prefix IS the real,
                    # runnable model id for this framework's `model:` config
                    # field — model-registry.json's own `id` matches it, and
                    # the legacy /models-legacy view resolves correctly off of
                    # that). The live models.dev catalog itself only knows the
                    # bare id, so try both before giving up — without this,
                    # every opencode-go override silently no-ops and the UI
                    # falls back to models.dev's own (inapplicable, since
                    # opencode-go is a flat-fee gateway with no real per-token
                    # cost) pricing guess instead of our curated $0 override.
                    resolved_id = model_id if model_id in models else None
                    if resolved_id is None and model_id.startswith(overlay_prefix):
                        bare_id = model_id[len(overlay_prefix):]
                        if bare_id in models:
                            resolved_id = bare_id
                    if resolved_id is None:
                        continue
                    model = dict(models[resolved_id])
                    cost = dict(model.get("cost") or {})
                    if price.get("input") is not None:
                        cost["input"] = price["input"]
                    if price.get("output") is not None:
                        cost["output"] = price["output"]
                    model["cost"] = cost
                    model["_costSource"] = "overlay"
                    models[resolved_id] = model
                provider_node["models"] = models
                merged[provider_key] = provider_node
            elif provider_key in self.CURATED_ONLY_PROVIDER_KEYS:
                # Curated path: no real models.dev slug for this provider.
                curated_models = {}
                for model_id, price in model_entries.items():
                    curated_models[model_id] = {
                        "id": model_id,
                        "name": price.get("name") or model_id,
                        "cost": {"input": price.get("input"), "output": price.get("output")},
                    }
                merged[provider_key] = {
                    "name": provider_prices.get("_name") or provider_key.capitalize(),
                    "models": curated_models,
                    "source": "curated",
                }
            # else: overlay key doesn't match a real provider and isn't on
            # the curated allow-list — inert legacy data, ignored.
        return merged
    def _read_model_source_prefs(self) -> dict:
        """Load the per-provider model-source map from ``project.yaml``.

        Returns a ``{provider_name: "registry"|"modelsdev"}`` dict, dropping
        any entries whose value is not a recognised source. Missing/invalid
        section yields ``{}`` (every provider then defaults to the central
        ``default-model-source`` from ``config/ai-providers.yaml``, see
        ``_default_model_source``).
        """
        project = self._ctx.config_manager.read("project") or {}
        prefs = project.get("model-source-preference") if isinstance(project, dict) else None
        if not isinstance(prefs, dict):
            return {}
        return {
            str(k): v for k, v in prefs.items()
            if isinstance(v, str) and v in VALID_MODEL_SOURCES
        }
    def _default_model_source(self) -> str:
        """Read the framework-wide default model source from
        ``config/ai-providers.yaml`` -> ``default-model-source``.

        Falls back to ``_FALLBACK_MODEL_SOURCE`` when the file or key is
        missing (older projects synced before this key existed) or the value
        is not one of ``VALID_MODEL_SOURCES``.
        """
        try:
            path = self._ai_providers_path()
            if not path.exists():
                return _FALLBACK_MODEL_SOURCE
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            value = data.get("default-model-source") if isinstance(data, dict) else None
            if isinstance(value, str) and value in VALID_MODEL_SOURCES:
                return value
            return _FALLBACK_MODEL_SOURCE
        except Exception:  # noqa: BLE001
            return _FALLBACK_MODEL_SOURCE
    def _resolve_model_source(self, provider_name: str) -> str:
        """Resolve the effective source for ``provider_name`` (per-provider
        override from ``project.yaml``, or the central default when unset)."""
        return self._read_model_source_prefs().get(provider_name, self._default_model_source())
    def _provider_model_tiers(self, provider_name: str) -> dict:
        """Return the ``model-tiers`` map for ``provider_name`` from
        ``ai-providers.yaml`` (``{}`` when absent)."""
        path = self._ai_providers_path()
        if not path.exists():
            return {}
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        providers = data.get("providers") or {}
        conf = providers.get(provider_name) or {} if isinstance(providers, dict) else {}
        tiers = conf.get("model-tiers") or {} if isinstance(conf, dict) else {}
        return tiers if isinstance(tiers, dict) else {}
    def _suggestions_from_registry(self, provider_name: str) -> list[dict]:
        """Registry-sourced model suggestions for ``provider_name``.

        The provider's tier values pin down which registry provider slug(s)
        (e.g. ``opencode-go``, ``anthropic``) belong to this framework
        provider, and only active (non-disabled) models for those slugs are
        returned. When no slug can be inferred, ``[]`` is returned — the
        previous behaviour of offering ALL active models flooded datalists
        with cross-provider ids that would corrupt the config if selected
        (e.g. Gemini's bare ``gemini-*`` tier ids do not exist in a registry
        that only carries anthropic + opencode-go entries).
        """
        models = [m for m in self._collect_models() if m.get("enabled")]
        tier_vals = [str(v) for v in self._provider_model_tiers(provider_name).values() if v]
        registry_slugs: set = set()
        for model_id in tier_vals:
            if "/" in model_id:
                prefix = model_id.split("/", 1)[0]
                for m in models:
                    if str(m.get("id", "")).startswith(prefix + "/"):
                        registry_slugs.add(m.get("provider"))
            else:
                for m in models:
                    if m.get("id") == model_id:
                        registry_slugs.add(m.get("provider"))
        if not registry_slugs:
            return []
        selected = [m for m in models if m.get("provider") in registry_slugs]
        return [
            {"id": m.get("id"), "name": m.get("name") or m.get("id"), "provider": m.get("provider")}
            for m in selected
        ]
    def _registry_model_ids_by_provider(self) -> dict[str, set[str]]:
        """Map every registry provider slug to the set of its registry ids.

        Reads the SAME registry source ``_collect_models()`` uses (override
        registry when present, framework registry otherwise), so ids resolved
        through :meth:`_resolve_registry_model_id` always line up with the
        ids ``_collect_models`` looks the pricing overlay up by.
        """
        out: dict[str, set[str]] = {}
        try:
            collected = self._collect_models()
        except Exception:  # noqa: BLE001
            return out
        for m in collected:
            provider = str(m.get("provider") or "")
            model_id = str(m.get("id") or "")
            if provider and model_id:
                out.setdefault(provider, set()).add(model_id)
        return out
    def _resolve_registry_model_id(
        self,
        provider_slug: str,
        raw_id: str,
        ids_by_provider: dict[str, set[str]] | None = None,
    ) -> str:
        """Resolve the registry-conform id for a bare models.dev model id.

        Registry id conventions are PER MODEL, not per provider: anthropic
        carries bare canonical ids (``claude-opus-5``) AND namespaced
        OpenRouter extras (``anthropic/claude-opus-4.8-fast``), while
        opencode-go namespaces every id. Resolution order:

        1. the bare id exists in the registry for this provider → bare;
        2. the namespaced ``<slug>/<raw>`` id exists → namespaced;
        3. neither exists (model not synced into the registry yet) →
           namespaced only when EVERY registry id of this provider is
           namespaced (unanimous convention), else bare — a not-yet-synced
           opencode-go model stays runnable (``opencode-go/<raw>``) while a
           mixed-convention provider (anthropic) defaults to the canonical
           bare form.

        No provider names are hardcoded; the convention is derived entirely
        from the registry. Callers resolving many ids should pass
        ``ids_by_provider`` (from :meth:`_registry_model_ids_by_provider`)
        to avoid re-reading the registry per model. The resolved id is what
        ``_collect_models()`` looks the pricing overlay up by and what
        ``roles.py::_resolve_tier_to_model`` persists verbatim into the
        ``model:`` frontmatter — both consumers need the exact registry id.
        """
        if ids_by_provider is None:
            ids_by_provider = self._registry_model_ids_by_provider()
        ids = ids_by_provider.get(provider_slug, set())
        if raw_id in ids:
            return raw_id
        namespaced = f"{provider_slug}/{raw_id}"
        if namespaced in ids:
            return namespaced
        fully_namespaced = bool(ids) and all(i.startswith(f"{provider_slug}/") for i in ids)
        return namespaced if fully_namespaced else raw_id
    def _suggestions_from_models_dev(self, provider_name: str) -> list[dict]:
        """models.dev-sourced model suggestions for ``provider_name``.

        Returns ``[]`` for providers without a models.dev catalog slug.
        Suggestion ids match the registry's PER-MODEL id convention (see
        :meth:`_resolve_registry_model_id`): bare models.dev ids stay 1:1
        where the registry is bare (anthropic, google, github-copilot) and
        get the ``<slug>/`` prefix where the registry is namespaced
        (currently opencode-go) — the value persisted on save (model-tiers /
        tier-preset / provider-tier overrides) must be the runnable config
        id, and ``roles.py::_resolve_tier_to_model`` passes it through
        verbatim. The ``provider`` field always carries the models.dev slug
        (e.g. ``opencode-go``) as namespace info for display.
        """
        slug = PROVIDER_MODELSDEV_SLUGS.get(provider_name)
        if not slug:
            return []
        data = (self._ctx.handler or self)._load_models_dev_data()
        providers = self._apply_pricing_overlay(dict(data.get("providers", {})))
        node = providers.get(slug)
        if not isinstance(node, dict):
            return []
        ids_by_provider = self._registry_model_ids_by_provider()
        out: list[dict] = []
        for m in (node.get("models") or {}).values():
            raw_id = m.get("id")
            if not raw_id:
                continue
            suggestion_id = self._resolve_registry_model_id(slug, str(raw_id), ids_by_provider)
            out.append({"id": suggestion_id, "name": m.get("name") or raw_id, "provider": slug})
        return out
    def _ai_providers_path(self) -> Path:
        """Resolve the path to ``config/ai-providers.yaml`` for either layout."""
        return resolve_asset(self._ctx.root, "config", "ai-providers.yaml")
    def _list_providers(self) -> list[dict]:
        """Return the configured AI providers with their model tiers/aliases."""
        path = self._ai_providers_path()
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        providers = data.get("providers") or {}
        if not isinstance(providers, dict):
            return []
        out: list[dict] = []
        for name, conf in providers.items():
            if not isinstance(conf, dict):
                continue
            tiers = conf.get("model-tiers") or {}
            aliases = conf.get("model-aliases") or {}
            if not isinstance(tiers, dict):
                tiers = {}
            if not isinstance(aliases, dict):
                aliases = {}
            out.append({
                "name": name,
                "display_name": conf.get("display-name") or name,
                "has_model_tiers": bool(tiers),
                "model_tiers": tiers,
                "model_aliases": aliases,
            })
        out.sort(key=lambda p: p["name"].lower())
        return out
    def _list_platforms(self) -> list[dict]:
        """Return distinct platform prefixes derived from ``agents/2-platform/``."""
        names: set[str] = {"agent-meta", "generic"}
        known_roles = sorted(
            (r["name"] for r in self._list_roles()),
            key=len,
            reverse=True,
        )
        platform_dir = resolve_asset(self._ctx.root, "agents", "2-platform")
        if platform_dir.is_dir():
            for entry in platform_dir.glob("*.md"):
                stem = entry.stem
                if "-" not in stem:
                    continue
                prefix = None
                for role in known_roles:
                    suffix = f"-{role}"
                    if stem.endswith(suffix) and len(stem) > len(suffix):
                        prefix = stem[: -len(suffix)]
                        break
                if prefix is None:
                    prefix = stem.rsplit("-", 1)[0]
                if prefix:
                    names.add(prefix)
        return [{"name": n} for n in sorted(names, key=str.lower)]
    def _list_roles(self) -> list[dict]:
        """Return the role names declared in ``role-defaults.yaml``."""
        hierarchy = TemplateService(self._ctx).build_agent_hierarchy()
        rolenames = sorted(
            (r.get("name") for r in hierarchy.get("roles") or [] if r.get("name")),
            key=str.lower,
        )
        return [{"name": n} for n in rolenames]

class AdminRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler — dispatches to GET/PUT/POST routes.

    Class-level attributes are populated by :class:`AdminServer` before the
    server starts. They are intentionally shared across requests because the
    handler instance is recreated on every connection.
    """

    config_manager: ConfigManager
    sync_executor: SyncExecutor
    viz_manager: VizManager
    config_watcher: ConfigWatcher
    mode: str
    root: Path
    version: str
    bind_host: str
    bind_port: int

    # ------------------------------------------------------------------ #
    # Logging                                                            #
    # ------------------------------------------------------------------ #

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress default request-log line; keep stderr clean.
        return

    # ------------------------------------------------------------------ #
    # Response helpers                                                   #
    # ------------------------------------------------------------------ #

    def _send_json(self, payload: Any, status: int = 200,
                   extra_headers: dict[str, str] | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text: str, status: int = 200, content_type: str = "text/plain; charset=utf-8") -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> Any:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return None
        if length > MAX_BODY_SIZE:
            # Reject BEFORE calling self.rfile.read(length) — that call would
            # itself allocate/buffer up to `length` bytes, so checking first
            # is what actually bounds memory use (issue #585: an oversized
            # or forged Content-Length must not reach read()).
            raise PayloadTooLargeError(
                f"request body of {length} bytes exceeds the "
                f"{MAX_BODY_SIZE}-byte limit"
            )
        raw = self.rfile.read(length)
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON body: {exc}") from exc

    # ------------------------------------------------------------------ #
    # Centralized error handling                                         #
    # ------------------------------------------------------------------ #

    def _handle_error(self, exc: Exception, error_code: str = "ERR_INTERNAL") -> tuple[int, dict[str, str]]:
        """Log an unexpected exception with full detail and return a generic,
        client-safe (status, body) pair.

        Raw exception text (absolute file paths, internal variable/function
        names, library-internal details such as ``yaml.YAMLError`` file
        positions) must never reach an HTTP client — it helps an attacker map
        the server's filesystem and architecture (issue #581). Callers pass a
        short, stable ``error_code`` (e.g. ``"ERR_MODEL_FETCH"``) so client-side
        error handling / support requests can still distinguish failure modes
        without any leaked detail.

        Thin wrapper over :func:`_generic_error_response` (issue #572) so the
        handler and the extracted service classes share one implementation.
        """
        return _generic_error_response(exc, error_code)

    # ------------------------------------------------------------------ #
    # Service wiring                                                      #
    # ------------------------------------------------------------------ #

    def _service_context(self) -> ServiceContext:
        """Build a :class:`ServiceContext` that reads this handler's shared
        collaborators live (see ServiceContext for the live-read rationale)."""
        return ServiceContext(self.__class__, self)

    def _audit_service(self) -> AuditService:
        return AuditService(self._service_context())

    def _template_service(self) -> TemplateService:
        return TemplateService(self._service_context())

    def _pipeline_service(self) -> PipelineService:
        return PipelineService(self._service_context())

    def _reflection_service(self) -> ReflectionService:
        return ReflectionService(self._service_context())

    def _models_service(self) -> ModelsService:
        return ModelsService(self._service_context())

    # ------------------------------------------------------------------ #
    # CSRF / DNS-rebinding protection                                    #
    # ------------------------------------------------------------------ #

    def _check_token(self, *, allow_query_token: bool = False) -> None:
        """Verify the admin token when token auth is configured.

        Extracts token from ``Authorization: Bearer <token>`` header. The
        ``?token=<token>`` query parameter is accepted **only** when
        ``allow_query_token=True`` is passed explicitly.

        Bearer-only is the default for every ``/api/*`` endpoint (issue #577):
        query parameters leak into proxy/reverse-proxy access logs, browser
        history and ``Referer`` headers, none of which are under this
        server's control. The single exception is ``/api/events`` (SSE) —
        the browser ``EventSource`` API cannot set custom headers, so that
        one read-only, non-mutating endpoint keeps the query-parameter path
        via an explicit opt-in from its caller. See
        ``docs/howto/admin-ui-remote-access.md`` for the remote-access
        migration note.

        When no token is configured (AdminRequestHandler.admin_token is None),
        this is a no-op — the server is loopback-only and auth is not required.

        Raises AuthError on mismatch or missing token.

        Thin HTTP wrapper: the verification logic lives in
        :meth:`AuthService.check_token` (issue #572).
        """
        AuthService.check_token(
            expected=self.__class__.admin_token,
            auth_header=self.headers.get("Authorization", ""),
            query=urlparse(getattr(self, "path", "")).query,
            allow_query_token=allow_query_token,
        )

    def _check_origin(self) -> None:
        """Reject mutating requests whose Origin/Host is not in the configured
        allowed-hosts list (default: loopback only).

        - Browser tabs on other origins cannot mutate configs (CSRF defence).
        - Even if a hostile site DNS-rebinds to ``127.0.0.1``, the ``Host``
          header on the forged request will not match the bind ``host:port``,
          so the request is rejected (DNS-rebinding defence).

        See :meth:`AuthService.check_origin` for the full contract (issue #588);
        this is a thin HTTP wrapper that feeds it the per-request headers and the
        class-level server configuration (issue #572).
        """
        AuthService.check_origin(
            origin=self.headers.get("Origin"),
            host=self.headers.get("Host", ""),
            allowed_hosts=self.__class__.allowed_hosts,
            bind_host=self.__class__.bind_host,
            bind_port=self.__class__.bind_port,
        )

    # ------------------------------------------------------------------ #
    # Routing                                                            #
    # ------------------------------------------------------------------ #

    def do_OPTIONS(self) -> None:
        # No cross-origin access is permitted; respond with a minimal 204 and
        # no CORS headers so the browser will not consider this an allowed
        # cross-site preflight.
        self.send_response(204)
        self.send_header("Allow", "GET, PUT, POST, DELETE, OPTIONS")
        self.end_headers()

    def _is_public_get_path(self) -> bool:
        """Return True for GET paths served without token auth.

        The admin UI shell (``/``) and its favicon are static, self-contained
        public assets — they carry no secrets and must load *before* the
        client can present the token login overlay. Every ``/api/*`` endpoint
        remains token-gated (and, for mutations, origin-checked).
        """
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        return path in ("/", "/favicon.png")

    def _is_sse_events_path(self) -> bool:
        """Return True for the live-event SSE stream endpoint.

        The only ``/api/*`` route allowed to authenticate via the ``?token=``
        query parameter (issue #577) — the browser ``EventSource`` API has no
        way to set an ``Authorization`` header, so header-only auth would
        make the live dashboard unusable for remote/token-protected setups.
        Read-only (GET, no state mutation), so this narrow carve-out does not
        reintroduce a CSRF/leak risk equivalent to the general query-token
        removal.
        """
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        return path == "/api/events"

    def do_GET(self) -> None:
        try:
            if not self._is_public_get_path():
                self._check_token(allow_query_token=self._is_sse_events_path())
            self._dispatch_get()
        except AuthError as exc:
            self._send_json(
                {"error": "unauthorized", "detail": str(exc)},
                status=401,
                extra_headers={"WWW-Authenticate": "Bearer"},
            )
        except SecurityError as exc:
            self._send_json({"error": "forbidden", "detail": str(exc)}, status=403)
        except FileNotFoundError as exc:
            self._send_json({"error": "not_found", "detail": str(exc)}, status=404)
        except ConnectionError:
            # Client disconnected (covers BrokenPipeError, ConnectionResetError,
            # ConnectionAbortedError / Windows WinError 10053). Writing an error
            # response on a dead socket would raise another exception and cause
            # a confusing double traceback — bail out silently.
            return
        except Exception as exc:  # pragma: no cover  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_INTERNAL")
            self._send_json(body, status=status)

    def do_PUT(self) -> None:
        try:
            self._check_token()
            self._check_origin()
            self._dispatch_put()
        except AuthError as exc:
            self._send_json(
                {"error": "unauthorized", "detail": str(exc)},
                status=401,
                extra_headers={"WWW-Authenticate": "Bearer"},
            )
        except SecurityError as exc:
            self._send_json({"error": "forbidden", "detail": str(exc)}, status=403)
        except PayloadTooLargeError as exc:
            self._send_json({"error": "payload_too_large", "detail": str(exc)}, status=413)
        except ValueError as exc:
            self._send_json({"error": "bad_request", "detail": str(exc)}, status=400)
        except FileNotFoundError as exc:
            self._send_json({"error": "not_found", "detail": str(exc)}, status=404)
        except ConnectionError:
            # See ``do_GET`` — silently bail on dead client socket.
            return
        except Exception as exc:  # pragma: no cover  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_INTERNAL")
            self._send_json(body, status=status)

    def do_POST(self) -> None:
        try:
            self._check_token()
            self._check_origin()
            self._dispatch_post()
        except AuthError as exc:
            self._send_json(
                {"error": "unauthorized", "detail": str(exc)},
                status=401,
                extra_headers={"WWW-Authenticate": "Bearer"},
            )
        except SecurityError as exc:
            self._send_json({"error": "forbidden", "detail": str(exc)}, status=403)
        except PayloadTooLargeError as exc:
            self._send_json({"error": "payload_too_large", "detail": str(exc)}, status=413)
        except ValueError as exc:
            self._send_json({"error": "bad_request", "detail": str(exc)}, status=400)
        except ConnectionError:
            # See ``do_GET`` — silently bail on dead client socket.
            return
        except Exception as exc:  # pragma: no cover  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_INTERNAL")
            self._send_json(body, status=status)

    def do_DELETE(self) -> None:
        try:
            self._check_token()
            self._check_origin()
            self._dispatch_delete()
        except AuthError as exc:
            self._send_json(
                {"error": "unauthorized", "detail": str(exc)},
                status=401,
                extra_headers={"WWW-Authenticate": "Bearer"},
            )
        except SecurityError as exc:
            self._send_json({"error": "forbidden", "detail": str(exc)}, status=403)
        except FileNotFoundError as exc:
            self._send_json({"error": "not_found", "detail": str(exc)}, status=404)
        except ConnectionError:
            return
        except Exception as exc:  # pragma: no cover  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_INTERNAL")
            self._send_json(body, status=status)

    # ------------------------------------------------------------------ #
    # GET routes                                                         #
    # ------------------------------------------------------------------ #

    # ------------------------------------------------------------------ #
    # Route tables                                                        #
    #                                                                     #
    # Each verb maps a normalized path (trailing slash stripped) to a     #
    # self-responding handler-method NAME. Exact matches are resolved     #
    # first, then the ordered prefix table (the path suffix after the     #
    # prefix is passed to the handler). This preserves the exact          #
    # evaluation order of the previous if-chains (issue #572): exact      #
    # routes always win over prefixes, and the only path that matches     #
    # both a prefix and would otherwise be an exact —                     #
    # ``/api/config/submodule-protection`` — is intentionally NOT listed  #
    # as an exact GET route so it keeps resolving through the generic     #
    # ``/api/config/`` reader, exactly as the original chain did.         #
    # Method names are resolved via ``getattr(self, name)`` at call time  #
    # so monkeypatched/overridden instance methods still take effect.     #
    # ------------------------------------------------------------------ #

    _GET_EXACT_ROUTES: ClassVar[dict[str, str]] = {
        "/": "_serve_ui",
        "/favicon.png": "_serve_favicon",
        "/api/health": "_route_get_health",
        "/api/mode": "_route_get_mode",
        "/api/project": "_route_get_project",
        "/api/schema/project": "_route_get_schema_project",
        "/api/help": "_route_get_help",
        "/api/sync/status": "_route_get_sync_status",
        "/api/agents/hierarchy": "_route_get_agents_hierarchy",
        "/api/pipelines": "_route_get_pipelines",
        "/api/reflection-pairs": "_route_get_reflection_pairs",
        "/api/agents/templates": "_route_get_agents_templates",
        "/api/events": "_stream_events",
        "/api/subserver-status": "_route_get_subserver_status",
        "/api/providers": "_route_get_providers",
        "/api/platforms": "_route_get_platforms",
        "/api/roles": "_route_get_roles",
        "/api/config-audit": "_route_get_config_audit",
        "/api/consistency-check": "_route_get_consistency_check",
        "/api/external-tools/drift": "_route_get_external_tools_drift",
        "/api/models": "_handle_get_models",
        "/api/models/active": "_handle_get_models_active",
        "/api/models-dev": "_handle_get_models_dev",
        "/api/model-source": "_handle_get_model_source",
        "/api/model-suggestions": "_handle_get_model_suggestions",
        "/api/ai-providers": "_handle_get_ai_providers",
        "/api/tier-presets": "_handle_get_tier_presets",
        "/api/tier-presets/merged": "_handle_get_tier_presets_merged",
        "/api/model-mapping": "_handle_get_model_mapping",
        "/api/provider-deactivation/status": "_route_get_provider_deactivation_status",
        "/api/backups": "_handle_get_backups",
        "/api/submodule-protection": "_route_get_submodule_protection",
        "/api/environments": "_route_get_environments",
        "/api/environments/scripts": "_route_get_env_scripts",
    }
    _GET_PREFIX_ROUTES: ClassVar[tuple[tuple[str, str], ...]] = (
        ("/api/config/", "_route_get_config"),
        ("/api/pipelines/", "_route_get_single_pipeline"),
        ("/api/reflection-pairs/", "_route_get_single_reflection_pair"),
        ("/api/agent-template/", "_send_template"),
    )

    _PUT_EXACT_ROUTES: ClassVar[dict[str, str]] = {
        # ``/api/submodule-protection`` and ``/api/config/project/section`` are
        # exacts that must beat the generic ``/api/config/`` prefix — exact
        # routes are resolved first, so this ordering is preserved.
        "/api/submodule-protection": "_write_submodule_protection",
        "/api/config/project/section": "_write_project_section",
        "/api/pipelines": "_route_put_pipelines",
        "/api/reflection-pairs": "_route_put_reflection_pairs",
    }
    _PUT_PREFIX_ROUTES: ClassVar[tuple[tuple[str, str], ...]] = (
        ("/api/config/", "_route_put_config"),
        ("/api/agent-template/", "_write_template"),
        ("/api/pipelines/", "_route_put_single_pipeline"),
        ("/api/reflection-pairs/", "_route_put_single_reflection_pair"),
    )

    _POST_EXACT_ROUTES: ClassVar[dict[str, str]] = {
        "/api/sync/dry-run": "_route_post_sync_dry_run",
        "/api/sync/run": "_route_post_sync_run",
        "/api/sync/render-standalone": "_route_post_sync_render_standalone",
        "/api/config-audit/apply": "_route_post_config_audit_apply",
        "/api/models/update": "_handle_post_models_update",
        "/api/models/clear-override": "_handle_post_models_clear_override",
        "/api/models-dev/refresh": "_handle_post_models_dev_refresh",
        "/api/models-dev/import": "_handle_post_models_dev_import",
        "/api/model-source": "_handle_post_model_source",
        "/api/model-source/batch": "_handle_post_model_source_batch",
        "/api/model-inherit": "_handle_post_model_inherit",
        "/api/models/exclude": "_handle_post_models_exclude",
        "/api/models/disable": "_handle_post_models_disable",
        "/api/models/enable": "_handle_post_models_enable",
        "/api/pricing/update": "_handle_post_pricing_update",
        "/api/pricing/reset": "_handle_post_pricing_reset",
        "/api/ai-providers/update": "_handle_post_ai_providers_update",
        "/api/tier-presets/update": "_handle_post_tier_presets_update",
        "/api/reflection-pairs": "_route_post_reflection_pair",
        "/api/provider-deactivation/deactivate": "_handle_deactivate_providers",
        "/api/provider-deactivation/activate": "_handle_activate_providers",
        "/api/backups/create": "_handle_create_backup",
        "/api/backups/restore": "_handle_restore_backup",
    }

    _DELETE_PREFIX_ROUTES: ClassVar[tuple[tuple[str, str], ...]] = (
        ("/api/pipelines/", "_route_delete_pipeline"),
        ("/api/reflection-pairs/", "_route_delete_reflection_pair"),
        ("/api/backups/", "_handle_delete_backup"),
        ("/api/environments/", "_route_delete_environment"),
    )

    def _resolve_route(
        self,
        path: str,
        exact: dict[str, str],
        prefixes: tuple[tuple[str, str], ...],
    ) -> Any:
        """Return a zero-argument callable that serves ``path``, or ``None``.

        Exact matches are tried first, then the ordered ``prefixes`` table; a
        prefix handler receives the path suffix (the portion after the prefix)
        as its single positional argument.
        """
        name = exact.get(path)
        if name is not None:
            return getattr(self, name)
        for prefix, handler_name in prefixes:
            if path.startswith(prefix):
                suffix = path[len(prefix):]
                method = getattr(self, handler_name)
                return lambda: method(suffix)
        return None

    def _dispatch_get(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        handler = self._resolve_route(path, self._GET_EXACT_ROUTES, self._GET_PREFIX_ROUTES)
        if handler is None:
            raise FileNotFoundError(path)
        return handler()

    # ------------------------------------------------------------------ #
    # GET route handlers (thin — read/format only, delegate the work)    #
    # ------------------------------------------------------------------ #

    def _serve_favicon(self) -> None:
        favicon_path = resolve_asset(self.root, "docs", "ui", "favicon.png")
        if favicon_path.exists():
            return self._send_bytes(favicon_path.read_bytes(), "image/png")
        self.send_response(404)
        self.end_headers()

    def _route_get_health(self) -> None:
        return self._send_json({
            "status": "ok",
            "version": self.__class__.version,
            "mode": self.__class__.mode,
        })

    def _route_get_mode(self) -> None:
        payload: dict = {
            "mode": self.__class__.mode,
            "root": str(self.__class__.root),
            "allowed_keys": sorted(self.__class__.config_manager._allowed_keys().keys()),
        }
        # In super_admin mode the project.yaml of the meta-repo is also
        # available as the "target repo" view.  Signal this to the UI so
        # it can render the combined dashboard.
        if self.__class__.mode == "super_admin":
            project_yaml = self.__class__.root / ".meta-config" / "project.yaml"
            payload["project_admin_available"] = project_yaml.exists()
        return self._send_json(payload)

    def _route_get_project(self) -> None:
        project_data = self.__class__.config_manager.read("project").get("project", {})
        return self._send_json({"project": {
            "name": project_data.get("name", ""),
            "version": project_data.get("version", ""),
            "id-prefix": project_data.get("id-prefix", project_data.get("prefix", ""))
        }})

    def _route_get_config(self, key: str) -> None:
        data = self.__class__.config_manager.read(key)
        return self._send_json(data)

    def _route_get_schema_project(self) -> None:
        schema_path = self._template_service().find_schema_path()
        if not schema_path.exists():
            raise FileNotFoundError("project-config.schema.json")
        self._send_bytes(schema_path.read_bytes(), "application/json; charset=utf-8")

    def _route_get_help(self) -> None:
        return self._send_json(self._get_help_docs())

    def _route_get_sync_status(self) -> None:
        return self._send_json(self.__class__.sync_executor.status())

    def _route_get_agents_hierarchy(self) -> None:
        return self._send_json(self._template_service().build_agent_hierarchy())

    def _route_get_pipelines(self) -> None:
        query = urlparse(self.path).query
        if "help" in (query or "").lower():
            return self._send_json(self._pipeline_service().pipeline_help())
        return self._send_json(self._pipeline_service().read_pipelines())

    def _route_get_single_pipeline(self, name: str) -> None:
        return self._send_json(self._pipeline_service().read_single_pipeline(name))

    def _route_get_reflection_pairs(self) -> None:
        return self._send_json(self._reflection_service().read_reflection_pairs())

    def _route_get_single_reflection_pair(self, pair_id: str) -> None:
        return self._send_json(self._reflection_service().read_reflection_pair(pair_id))

    def _route_get_agents_templates(self) -> None:
        return self._send_json(self._template_service().list_agent_templates())

    def _route_get_subserver_status(self) -> None:
        return self._send_json(self.__class__.viz_manager.status())

    def _route_get_providers(self) -> None:
        return self._send_json(self._models_service()._list_providers())

    def _route_get_platforms(self) -> None:
        return self._send_json(self._models_service()._list_platforms())

    def _route_get_roles(self) -> None:
        return self._send_json(self._models_service()._list_roles())

    def _route_get_config_audit(self) -> None:
        return self._send_json(self._audit_service().run_config_audit())

    def _route_get_consistency_check(self) -> None:
        return self._send_json(self._audit_service().run_consistency_check())

    def _route_get_external_tools_drift(self) -> None:
        return self._send_json(self._audit_service().compute_injection_drift())

    def _route_get_provider_deactivation_status(self) -> None:
        return self._send_json(self._audit_service().deactivation_status())

    def _route_get_submodule_protection(self) -> None:
        return self._send_json(self._get_submodule_protection_status())

    def _route_get_environments(self) -> None:
        return self._send_json(self._read_environments())

    def _route_get_env_scripts(self) -> None:
        return self._send_json(self._read_env_scripts())

    def _write_submodule_protection(self) -> None:
        body = self._read_body()
        if not isinstance(body, dict):
            raise ValueError("expected JSON body")
            
        root = self.__class__.root
        project_config = self.__class__.config_manager.read("project")
        if not isinstance(project_config, dict):
            project_config = {}
            
        restore_default = body.get("restore_default", False)
        enabled = body.get("enabled", True)
        override_text = body.get("override_text", "")
        
        if restore_default:
            # Remove from project.yaml
            if "submodule-protection" in project_config:
                del project_config["submodule-protection"]
            if "submodule_protection" in project_config:
                del project_config["submodule_protection"]
            if "rules" in project_config and isinstance(project_config["rules"], dict) and "submodule-protection" in project_config["rules"]:
                del project_config["rules"]["submodule-protection"]
                
            # Delete override files
            for p in [
                root / ".claude" / "rules" / "submodule-protection.md",
                root / "rules" / "3-project" / "submodule-protection.md",
                root / ".meta-config" / "submodule-protection.md"
            ]:
                p.unlink(missing_ok=True)
                
            self.__class__.config_manager.write("project", project_config)
            return self._send_json({"status": "restored"})
            
        if not enabled:
            project_config["submodule-protection"] = False
        else:
            project_config["submodule-protection"] = override_text

        # Clean up a stale nested override so only one representation exists.
        if "rules" in project_config and isinstance(project_config["rules"], dict):
            project_config["rules"].pop("submodule-protection", None)

        self.__class__.config_manager.write("project", project_config)
        return self._send_json({"status": "saved"})

    # ------------------------------------------------------------------ #
    # DELETE routes                                                      #
    # ------------------------------------------------------------------ #

    def _dispatch_delete(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        handler = self._resolve_route(path, {}, self._DELETE_PREFIX_ROUTES)
        if handler is None:
            raise FileNotFoundError(path)
        return handler()

    def _route_delete_pipeline(self, name: str) -> None:
        return self._send_json(self._pipeline_service().delete_pipeline(name))

    def _route_delete_reflection_pair(self, pair_id: str) -> None:
        return self._send_json(self._reflection_service().delete_reflection_pair(pair_id))

    def _route_delete_environment(self, name: str) -> None:
        return self._send_json(self._delete_environment(name))

    # ------------------------------------------------------------------ #
    # PUT routes                                                         #
    # ------------------------------------------------------------------ #

    def _dispatch_put(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        handler = self._resolve_route(path, self._PUT_EXACT_ROUTES, self._PUT_PREFIX_ROUTES)
        if handler is None:
            raise FileNotFoundError(path)
        return handler()

    def _route_put_config(self, key: str) -> None:
        body = self._read_body()
        if body is None:
            raise ValueError("empty body")
        if key == "project":
            existing = self.__class__.config_manager.read("project")
            self._deep_merge(existing, body)
            result = self.__class__.config_manager.write("project", existing)
        else:
            result = self.__class__.config_manager.write(key, body)
        return self._send_json(result)

    def _route_put_pipelines(self) -> None:
        body = self._read_body()
        if not isinstance(body, dict) or "pipelines" not in body:
            raise ValueError("expected JSON body with 'pipelines' field")
        pipelines = body["pipelines"]
        if not isinstance(pipelines, dict):
            raise ValueError("'pipelines' must be an object")
        result = self._pipeline_service().write_pipelines(pipelines)
        return self._send_json(result)

    def _route_put_single_pipeline(self, name: str) -> None:
        body = self._read_body()
        if not isinstance(body, dict):
            raise ValueError("expected JSON body with pipeline object")
        result = self._pipeline_service().write_single_pipeline(name, body)
        return self._send_json(result)

    def _route_put_reflection_pairs(self) -> None:
        body = self._read_body()
        if not isinstance(body, dict) or "reflection_pairs" not in body:
            raise ValueError("expected JSON body with 'reflection_pairs' field")
        pairs = body["reflection_pairs"]
        if not isinstance(pairs, list):
            raise ValueError("'reflection_pairs' must be a list")
        result = self._reflection_service().write_reflection_pairs(pairs)
        return self._send_json(result)

    def _route_put_single_reflection_pair(self, pair_id: str) -> None:
        body = self._read_body()
        if not isinstance(body, dict):
            raise ValueError("expected JSON body with reflection pair object")
        result = self._reflection_service().write_reflection_pair(pair_id, body)
        return self._send_json(result)

    # ------------------------------------------------------------------ #
    # POST routes                                                        #
    # ------------------------------------------------------------------ #

    def _dispatch_post(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        handler = self._resolve_route(path, self._POST_EXACT_ROUTES, ())
        if handler is not None:
            return handler()

        # Individual subserver control: /api/subserver/{name}/{action}
        # name in {viz, mcp}, action in {start, stop, restart}. This is a
        # parametric route with its own whitelist validation, kept as an
        # explicit matcher rather than a table entry.
        subserver = self._match_subserver_route(path)
        if subserver is not None:
            name, action = subserver
            return self._handle_subserver_action(name, action)

        raise FileNotFoundError(path)

    def _route_post_sync_dry_run(self) -> None:
        return self._send_json(self.__class__.sync_executor.dry_run())

    def _route_post_sync_run(self) -> None:
        return self._send_json(self.__class__.sync_executor.run())

    def _route_post_sync_render_standalone(self) -> None:
        return self._send_json(self.__class__.sync_executor.render_standalone())

    def _route_post_config_audit_apply(self) -> None:
        return self._send_json(self._audit_service().apply_config_audit())

    def _route_post_reflection_pair(self) -> None:
        body = self._read_body()
        if not isinstance(body, dict):
            raise ValueError("expected JSON body with reflection pair object")
        for field in ("id", "generator", "critic"):
            value = body.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError("id, generator and critic are required")
        pair_id = self._reflection_service().ensure_pair_id(body)
        result = self._reflection_service().write_reflection_pair(pair_id, body)
        return self._send_json(result)

    @staticmethod
    def _match_subserver_route(path: str) -> tuple[str, str] | None:
        """Return ``(name, action)`` if ``path`` matches the subserver control
        route ``/api/subserver/{name}/{action}`` with a whitelisted name and
        action, otherwise ``None``."""
        prefix = "/api/subserver/"
        if not path.startswith(prefix):
            return None
        parts = path[len(prefix):].split("/")
        if len(parts) != 2:
            return None
        name, action = parts
        if name in ("viz", "mcp") and action in ("start", "stop", "restart"):
            return name, action
        return None

    def _handle_subserver_action(self, name: str, action: str) -> None:
        """Dispatch a validated subserver control action to the VizManager and
        return the resulting status."""
        vm = self.__class__.viz_manager
        method = getattr(vm, f"{action}_{name}")
        ok = bool(method())
        return self._send_json({
            "success": ok,
            "service": name,
            "action": action,
            "status": vm.status(),
        })

    def _handle_get_models(self) -> None:
        """Return all registered models with curation + pricing metadata."""
        try:
            models = self._models_service()._collect_models()
            return self._send_json({"models": models})
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_MODELS")
            return self._send_json(body, status=status)

    def _handle_get_models_active(self) -> None:
        """Return only models that are currently active.

        A model is active when it is not blacklisted (always true here, see
        ``_collect_models``) and not in ``curation.disabled``. Tier dropdowns
        and model pickers in the admin UI consume this endpoint so disabled
        ids disappear from selectable options without rebuilding the registry.
        """
        try:
            models = [m for m in self._models_service()._collect_models() if m.get("enabled")]
            return self._send_json({"models": models})
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_MODELS_ACTIVE")
            return self._send_json(body, status=status)

    # ------------------------------------------------------------------ #
    # Models.dev integration (SDK primary, API fallback)                  #
    # ------------------------------------------------------------------ #

    # Negative-cache TTL for a total models.dev load failure (seconds). Keeps
    # an unreachable network from re-attempting a 30 s-timeout fetch on every
    # single request while still retrying soon enough to recover on its own.
    _MODELS_DEV_ERROR_TTL_SECONDS = 60.0

    def _load_models_dev_data(self, force_refresh: bool = False) -> dict:
        """Delegates to :class:`ModelsService` (issue #572).

        Kept as a real method (not inlined at call sites) because
        ``ModelsService._suggestions_from_models_dev`` routes through
        ``self._ctx.handler`` so unit tests can monkeypatch this exact
        instance method as their models.dev cache/network seam — see
        :attr:`ServiceContext.handler`.
        """
        return self._models_service()._load_models_dev_data(force_refresh)

    def _handle_get_models_dev(self) -> None:
        try:
            raw = self._models_service()._load_models_dev_data()
            data = dict(raw)
            providers = self._models_service()._apply_pricing_overlay(dict(raw.get("providers", {})))
            # Optional: filter to specific providers via ?providers=a,b,c.
            # Applied AFTER the overlay merge so curated providers (and
            # overlay overrides) are resolved against the full catalog —
            # filtering first would make a curated key look "unmatched" and
            # get miscategorized.
            parsed = urlparse(self.path)
            from urllib.parse import parse_qs
            qs = parse_qs(parsed.query)
            provider_filter = qs.get('providers', [None])[0]
            if provider_filter:
                requested = {p.strip() for p in provider_filter.split(',') if p.strip()}
                if requested:
                    providers = {k: v for k, v in providers.items() if k in requested}
                    data['_filtered'] = True
            data['providers'] = providers
            return self._send_json(data)
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_MODELS_DEV")
            return self._send_json(body, status=status)

    def _handle_post_models_dev_refresh(self) -> None:
        try:
            for attr in ('_models_dev_cache', '_models_dev_cache_ts', '_models_dev_error'):
                if hasattr(self.__class__, attr):
                    delattr(self.__class__, attr)
            # force_refresh=True tries the live API BEFORE the local SDK
            # snapshot, so pressing ↻ actually re-fetches even when a stale
            # bundled snapshot exists (the normal load path prefers the
            # snapshot by design — "SDK primary, API fallback").
            return self._send_json(self._models_service()._load_models_dev_data(force_refresh=True))
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_MODELS_DEV_REFRESH")
            return self._send_json(body, status=status)

    def _handle_post_models_dev_import(self) -> None:
        """Import a model from models.dev into pricing-overlay.yaml."""
        try:
            body = self._read_body()
            if not isinstance(body, dict):
                raise ValueError("expected JSON body")  # noqa: TRY004
            provider_id = body.get("provider", "").strip()
            model_id = body.get("model_id", "").strip()
            input_cost = body.get("input_cost")
            output_cost = body.get("output_cost")
            if not provider_id or not model_id:
                raise ValueError("provider and model_id required")

            config_dir = resolve_asset(self.__class__.root, "config")
            pricing_path = config_dir / "pricing-overlay.yaml"

            pricing = {}
            if pricing_path.exists():
                pricing = yaml.safe_load(pricing_path.read_text(encoding="utf-8")) or {}
            if not isinstance(pricing, dict):
                pricing = {}
            prices = pricing.setdefault("prices", {})
            if not isinstance(prices, dict):
                prices = {}
                pricing["prices"] = prices
            prov = prices.setdefault(provider_id, {})
            if not isinstance(prov, dict):
                prov = {}
                prices[provider_id] = prov
            # Persist the overlay key under the EXACT registry id
            # _collect_models() looks the price up by (per-model resolution,
            # see _resolve_registry_model_id): anthropic's canonical models
            # are bare, its OpenRouter extras are namespaced, and opencode-go
            # is namespaced throughout — a blanket per-provider rule would
            # make imported prices silently invisible in /api/models.
            overlay_key = self._models_service()._resolve_registry_model_id(provider_id, model_id)
            prov[overlay_key] = {"input": float(input_cost) if input_cost is not None else 0.0,
                                 "output": float(output_cost) if output_cost is not None else 0.0}

            # Atomic write with backup. Only back up an EXISTING file —
            # _backup() reads the original, so a first-ever import (no
            # pricing-overlay.yaml yet) would otherwise fail with a 500.
            if pricing_path.exists():
                self.__class__.config_manager._backup(pricing_path)
            pricing_path.write_text(yaml.dump(pricing, default_flow_style=False, allow_unicode=True, sort_keys=False),
                                    encoding="utf-8")
            return self._send_json({"success": True, "provider": provider_id, "model_id": overlay_key})
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_MODELS_DEV_IMPORT")
            return self._send_json(body, status=status)

    def _handle_post_models_update(self) -> None:
        """Trigger sync.py --update-models or download from GitHub if submodule override."""
        try:
            agent_meta_root = self._agent_meta_root()
            project_root = Path(self.__class__.root)
            is_submodule = agent_meta_root != project_root

            if is_submodule:
                import json
                import urllib.request
                url = "https://raw.githubusercontent.com/Popoboxxo/agent-meta/main/config/generated/model-registry.json"
                req = urllib.request.Request(url, headers={"User-Agent": "agent-meta-admin"})
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode("utf-8"))
                
                target_file = project_root / ".meta-config" / "generated" / "model-registry.json"
                target_file.parent.mkdir(parents=True, exist_ok=True)
                with open(target_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                return self._send_json({"success": True, "override": True})
            else:
                res = self.__class__.sync_executor._run(["--update-models"])
                return self._send_json(res)
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_MODELS_UPDATE")
            return self._send_json(body, status=status)

    def _handle_post_models_clear_override(self) -> None:
        """Clear the downloaded override model registry."""
        try:
            project_root = Path(self.__class__.root)
            target_file = project_root / ".meta-config" / "generated" / "model-registry.json"
            if target_file.exists():
                target_file.unlink()
            return self._send_json({"success": True})
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_MODELS_CLEAR_OVERRIDE")
            return self._send_json(body, status=status)

    def _read_id_list(self) -> list[str]:
        """Parse the request body and return a deduplicated list of model ids.

        Body shape: ``{"ids": ["model-id-1", ...]}``. Raises ``ValueError``
        on an empty or invalid body so the dispatcher returns HTTP 400.
        """
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            raise ValueError("empty body")
        raw = self.rfile.read(length).decode("utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON body: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("body must be a JSON object with 'ids' field")  # noqa: TRY004
        ids = data.get("ids")
        if not isinstance(ids, list):
            raise ValueError("'ids' must be a list of strings")  # noqa: TRY004
        seen: set[str] = set()
        result: list[str] = []
        for item in ids:
            if not isinstance(item, str) or not item:
                continue
            if item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result

    def _handle_post_models_exclude(self) -> None:
        """Add model ids to the curation blacklist (hard exclusion).

        Blacklisted ids are filtered out during model-registry generation, so
        the next ``sync.py --update-models`` run will drop them entirely. The
        response shape (``{"success": true, "blacklisted_count": N}``) keeps
        backward compatibility with the existing UI while signalling that the
        backing store is now ``config/model-curation.yaml`` rather than
        ``config/pricing-overlay.yaml``.
        """
        try:
            try:
                ids_to_blacklist = self._read_id_list()
            except ValueError as exc:
                return self._send_json({"error": str(exc)}, status=400)

            curation = self._models_service()._load_curation()
            blacklist = list(curation.get("blacklist", []))
            existing = set(blacklist)
            added = 0
            for model_id in ids_to_blacklist:
                if model_id not in existing:
                    blacklist.append(model_id)
                    existing.add(model_id)
                    added += 1
            curation["blacklist"] = blacklist
            self._models_service()._save_curation(curation)

            return self._send_json({
                "success": True,
                "blacklisted_count": added,
                "total": len(blacklist),
            })
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_MODELS_EXCLUDE")
            return self._send_json(body, status=status)

    def _handle_post_models_disable(self) -> None:
        """Add model ids to the curation ``disabled`` list (soft exclusion).

        Disabled ids stay in the registry (so historical references remain
        resolvable) but are hidden from tier dropdowns and model pickers via
        ``/api/models/active``.
        """
        try:
            try:
                ids_to_disable = self._read_id_list()
            except ValueError as exc:
                return self._send_json({"error": str(exc)}, status=400)

            curation = self._models_service()._load_curation()
            disabled = list(curation.get("disabled", []))
            existing = set(disabled)
            added = 0
            for model_id in ids_to_disable:
                if model_id not in existing:
                    disabled.append(model_id)
                    existing.add(model_id)
                    added += 1
            curation["disabled"] = disabled
            self._models_service()._save_curation(curation)

            return self._send_json({
                "status": "ok",
                "disabled_count": added,
                "total": len(disabled),
            })
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_MODELS_DISABLE")
            return self._send_json(body, status=status)

    def _handle_post_models_enable(self) -> None:
        """Remove model ids from the curation ``disabled`` list.

        Re-enables previously soft-excluded models. Ids that are not currently
        disabled are silently skipped so the call is idempotent.
        """
        try:
            try:
                ids_to_enable = self._read_id_list()
            except ValueError as exc:
                return self._send_json({"error": str(exc)}, status=400)

            curation = self._models_service()._load_curation()
            disabled = list(curation.get("disabled", []))
            to_remove = set(ids_to_enable)
            removed = 0
            new_disabled = []
            for model_id in disabled:
                if model_id in to_remove:
                    removed += 1
                else:
                    new_disabled.append(model_id)
            curation["disabled"] = new_disabled
            self._models_service()._save_curation(curation)

            return self._send_json({
                "status": "ok",
                "enabled_count": removed,
                "total": len(new_disabled),
            })
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_MODELS_ENABLE")
            return self._send_json(body, status=status)

    def _handle_post_pricing_update(self) -> None:
        """Update pricing-overlay.yaml with new prices from UI."""
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length <= 0:
                return self._send_json({"error": "Empty body"}, status=400)
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)

            pricing_path = resolve_asset(self.__class__.root, "config") / "pricing-overlay.yaml"

            pricing = {}
            if pricing_path.exists():
                pricing = yaml.safe_load(pricing_path.read_text(encoding="utf-8")) or {}
            
            if "prices" not in pricing:
                pricing["prices"] = {}
                
            updates = data.get("updates", [])
            for u in updates:
                provider = u.get("provider")
                model_id = u.get("id")
                input_c = u.get("input_cost")
                output_c = u.get("output_cost")
                
                if provider not in pricing["prices"]:
                    pricing["prices"][provider] = {}
                    
                if model_id not in pricing["prices"][provider]:
                    pricing["prices"][provider][model_id] = {}
                    
                if input_c is not None:
                    pricing["prices"][provider][model_id]["input"] = float(input_c)
                if output_c is not None:
                    pricing["prices"][provider][model_id]["output"] = float(output_c)
                    
            pricing_path.parent.mkdir(parents=True, exist_ok=True)
            with pricing_path.open("w", encoding="utf-8") as fh:
                yaml.dump(pricing, fh, default_flow_style=False, sort_keys=False)
                
            return self._send_json({"success": True})
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_PRICING_UPDATE")
            return self._send_json(body, status=status)

    def _handle_post_pricing_reset(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length <= 0:
                return self._send_json({"error": "Empty body"}, status=400)
            data = json.loads(self.rfile.read(length).decode("utf-8"))

            pricing_path = resolve_asset(self.__class__.root, "config") / "pricing-overlay.yaml"

            if pricing_path.exists():
                pricing = yaml.safe_load(pricing_path.read_text(encoding="utf-8")) or {}
                if "prices" in pricing:
                    provider = data.get("provider")
                    model_id = data.get("id")
                    if provider in pricing["prices"] and model_id in pricing["prices"][provider]:
                        del pricing["prices"][provider][model_id]
                        # Remove provider block if empty or only metadata (_url) remains.
                        remaining = set(pricing["prices"][provider].keys())
                        if not remaining or remaining == {"_url"}:
                            del pricing["prices"][provider]
                        with pricing_path.open("w", encoding="utf-8") as fh:
                            yaml.dump(pricing, fh, default_flow_style=False, sort_keys=False)
                            
            return self._send_json({"success": True})
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_PRICING_RESET")
            return self._send_json(body, status=status)

    # ------------------------------------------------------------------ #
    # Centralized per-provider model-source preference                    #
    # ------------------------------------------------------------------ #

    def _handle_get_model_source(self) -> None:
        """Return the central per-provider model-source map (single source of
        truth for every model dropdown/suggestion in the Admin UI)."""
        try:
            return self._send_json({
                "preferences": self._models_service()._read_model_source_prefs(),
                "default": self._models_service()._default_model_source(),
            })
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_MODEL_SOURCE")
            return self._send_json(body, status=status)

    def _handle_post_model_source(self) -> None:
        """Set one provider's model source and persist it centrally to
        ``.meta-config/project.yaml`` → ``model-source-preference``.

        Body: ``{"provider": "Opencode", "source": "modelsdev"}``.
        """
        try:
            body = self._read_body()
            if not isinstance(body, dict):
                raise ValueError("expected JSON body")  # noqa: TRY004
            provider = str(body.get("provider", "")).strip()
            source = str(body.get("source", "")).strip()
            if not provider:
                return self._send_json({"error": "provider required"}, status=400)
            if source not in VALID_MODEL_SOURCES:
                return self._send_json(
                    {"error": f"source must be one of {list(VALID_MODEL_SOURCES)}"}, status=400)

            project = self.__class__.config_manager.read("project")
            if not isinstance(project, dict):
                project = {}
            prefs = project.get("model-source-preference")
            if not isinstance(prefs, dict):
                prefs = {}
            prefs[provider] = source
            project["model-source-preference"] = prefs
            self.__class__.config_manager.write("project", project)

            return self._send_json({
                "success": True,
                "preferences": {
                    str(k): v for k, v in prefs.items()
                    if isinstance(v, str) and v in VALID_MODEL_SOURCES
                },
            })
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_MODEL_SOURCE")
            return self._send_json(body, status=status)

    def _handle_post_model_source_batch(self) -> None:
        """Set the model source for multiple providers in a single write.

        Persists the whole ``model-source-preference`` map in one
        ``config_manager.write`` call, so the Admin UI's "Per provider" row
        can offer a batched Save instead of one POST per dropdown change.

        Body: ``{"preferences": {"Opencode": "modelsdev", "Claude": "registry"}}``.
        """
        try:
            body = self._read_body()
            if not isinstance(body, dict):
                raise ValueError("expected JSON body")  # noqa: TRY004
            incoming = body.get("preferences")
            if not isinstance(incoming, dict) or not incoming:
                return self._send_json({"error": "preferences object required"}, status=400)

            invalid_sources = {
                str(source) for source in incoming.values()
                if source not in VALID_MODEL_SOURCES
            }
            if invalid_sources:
                return self._send_json(
                    {"error": f"source must be one of {list(VALID_MODEL_SOURCES)}"}, status=400)

            project = self.__class__.config_manager.read("project")
            if not isinstance(project, dict):
                project = {}
            prefs = project.get("model-source-preference")
            if not isinstance(prefs, dict):
                prefs = {}
            for provider, source in incoming.items():
                prefs[str(provider)] = str(source)
            project["model-source-preference"] = prefs
            self.__class__.config_manager.write("project", project)

            return self._send_json({
                "success": True,
                "preferences": {
                    str(k): v for k, v in prefs.items()
                    if isinstance(v, str) and v in VALID_MODEL_SOURCES
                },
            })
        except Exception as exc:
            status, body = self._handle_error(exc, "ERR_MODEL_SOURCE_BATCH")
            return self._send_json(body, status=status)

    def _handle_post_model_inherit(self) -> None:
        """Toggle main-chat model inheritance for one provider.

        Server-side counterpart of the Models page's second toggle bar
        (next to the Override-All bar): sets or deletes the provider key in
        the project.yaml ``model-inherit-main-chat`` block. When enabled,
        sync.py omits the model field for every agent of that provider so it
        inherits the main chat model at runtime (lib/roles.py::resolve_model
        returns "" and inject_model_field() skips the field).

        Body: ``{"provider": "Opencode", "enabled": true}``. Disabling
        removes the provider key; an empty block is removed entirely.

        Rejects enabling a provider that still has a truthy
        ``model-override-all`` entry with HTTP 409 — the two keys are
        mutually exclusive per provider (same rule the sync-side validation
        in lib/config.py enforces hard-fatal on direct YAML edits).

        Rejects providers missing from the central registry
        (``load_providers_config``, i.e. config/ai-providers.yaml) with
        HTTP 400.
        """
        try:
            body = self._read_body()
            if not isinstance(body, dict):
                return self._send_json({"error": "expected JSON body"}, status=400)
            provider = str(body.get("provider", "")).strip()
            enabled = body.get("enabled")
            if not provider:
                return self._send_json({"error": "provider required"}, status=400)
            if not isinstance(enabled, bool):
                return self._send_json(
                    {"error": "enabled must be true or false"}, status=400)

            # Whitelist against known provider keys (same registry the
            # Models page consumes via config/ai-providers.yaml).
            self._ensure_lib_on_path()
            from lib.providers import load_providers_config

            provider_config = load_providers_config(self._agent_meta_root())
            if not isinstance(provider_config, dict) or provider not in provider_config:
                return self._send_json(
                    {"error": f"unknown provider '{provider}'"}, status=400)

            project = self.__class__.config_manager.read("project")
            if not isinstance(project, dict):
                project = {}

            if enabled:
                override_all = project.get("model-override-all")
                if isinstance(override_all, dict) and override_all.get(provider):
                    other = _other_model_block("model-inherit-main-chat")
                    return self._send_json(
                        {
                            "error": (
                                f"conflicting model configuration for provider "
                                f"'{provider}': '{other}' and "
                                f"'model-inherit-main-chat' are mutually "
                                f"exclusive per provider — clear the '{other}' "
                                f"entry for '{provider}' first."
                            )
                        },
                        status=409,
                    )

            inherit = project.get("model-inherit-main-chat")
            if not isinstance(inherit, dict):
                inherit = {}
            if enabled:
                inherit[provider] = True
            else:
                inherit.pop(provider, None)
            if inherit:
                project["model-inherit-main-chat"] = inherit
            else:
                project.pop("model-inherit-main-chat", None)
            self.__class__.config_manager.write("project", project)

            return self._send_json({
                "success": True,
                "provider": provider,
                "enabled": enabled,
                "inherit_main_chat": dict(inherit),
            })
        except Exception as exc:
            status, body = self._handle_error(exc, "ERR_MODEL_INHERIT")
            return self._send_json(body, status=status)

    def _handle_get_model_suggestions(self) -> None:
        """Return the model suggestions for one provider, drawn EXCLUSIVELY
        from that provider's centrally-configured source. This is the single
        endpoint every model dropdown (Models & Pricing per-provider view and
        Provider Tier Overrides datalists) consumes — guaranteeing identical,
        un-mixed results across views.

        Query: ``?provider=<framework provider name>``.
        Response: ``{"provider", "source", "models": [{"id","name","provider"}]}``.
        """
        try:
            from urllib.parse import parse_qs
            qs = parse_qs(urlparse(self.path).query)
            provider = (qs.get("provider", [""])[0] or "").strip()
            if not provider:
                return self._send_json({"error": "provider query param required"}, status=400)
            source = self._models_service()._resolve_model_source(provider)
            # Providers with no models.dev catalog slug (Mammouth, Continue)
            # are registry-only regardless of what's persisted in
            # ``model-source-preference`` -- a stale/manually-edited "modelsdev"
            # entry must not silently degrade to an empty suggestion list (see
            # ``PROVIDER_MODELSDEV_SLUGS``). Force registry and report the
            # honest, effective source back to the caller.
            if source == "modelsdev" and provider in PROVIDER_MODELSDEV_SLUGS:
                models = self._models_service()._suggestions_from_models_dev(provider)
                if not models:
                    # The models.dev catalog is unavailable (network failure,
                    # stale SDK snapshot) or has no models for this provider's
                    # slug. Degrade to registry suggestions instead of serving
                    # a silently empty dropdown, and report the honest,
                    # effective source back to the caller — mirroring the
                    # registry-only provider forcing below. This is a
                    # fail-over that REPLACES the result, never a mix of both
                    # catalogs in one response.
                    source = "registry"
                    models = self._models_service()._suggestions_from_registry(provider)
            else:
                source = "registry"
                models = self._models_service()._suggestions_from_registry(provider)
            return self._send_json({"provider": provider, "source": source, "models": models})
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_MODEL_SUGGESTIONS")
            return self._send_json(body, status=status)

    def _handle_get_ai_providers(self) -> None:
        try:
            path = resolve_asset(self.__class__.root, "config") / "ai-providers.yaml"
            data = {}
            if path.exists():
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return self._send_json(data)
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_AI_PROVIDERS")
            return self._send_json(body, status=status)

    def _handle_post_ai_providers_update(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}
            path = resolve_asset(self.__class__.root, "config") / "ai-providers.yaml"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as fh:
                yaml.dump(data, fh, default_flow_style=False, sort_keys=False)
            return self._send_json({"success": True})
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_AI_PROVIDERS_UPDATE")
            return self._send_json(body, status=status)

    def _handle_get_tier_presets(self) -> None:
        try:
            path = resolve_asset(self.__class__.root, "config") / "tier-presets.yaml"
            data = {}
            if path.exists():
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return self._send_json(data)
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_TIER_PRESETS")
            return self._send_json(body, status=status)

    def _handle_get_tier_presets_merged(self) -> None:
        """Return merged tier presets: global + project-local.

        Each preset carries a ``source`` field (``"global"`` or ``"project"``).
        Project-local presets (from ``.meta-config/project.yaml`` →
        ``tier-presets``) override global ones with the same key. The Admin UI
        uses this endpoint to surface both sets in tier-preset dropdowns and
        the tier-presets matrix view.
        """
        try:
            # 1. Load global tier presets (mirrors _handle_get_tier_presets).
            global_path = resolve_asset(self.__class__.root, "config") / "tier-presets.yaml"
            global_data: dict = {}
            if global_path.exists():
                global_data = yaml.safe_load(global_path.read_text(encoding="utf-8")) or {}

            # 2. Load project-local tier-presets from .meta-config/project.yaml.
            project_data: dict = {}
            try:
                project_cfg = self.__class__.config_manager.read("project") or {}
                if isinstance(project_cfg, dict):
                    raw = project_cfg.get("tier-presets") or {}
                    if isinstance(raw, dict):
                        project_data = raw
            except Exception:  # noqa: BLE001
                project_data = {}

            # 3. Merge — global first, project overrides per-key with source tag.
            merged: dict = {}
            for key, val in (global_data or {}).items():
                if not isinstance(val, dict):
                    continue
                entry = dict(val)
                entry["source"] = "global"
                merged[key] = entry
            for key, val in (project_data or {}).items():
                if not isinstance(val, dict):
                    continue
                entry = dict(val)
                entry["source"] = "project"
                merged[key] = entry

            return self._send_json(merged)
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_TIER_PRESETS_MERGED")
            return self._send_json(body, status=status)

    def _handle_post_tier_presets_update(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}
            if not isinstance(data, dict):
                return self._send_json({"error": "Payload must be a JSON object"}, status=400)
            for preset_id, preset_val in data.items():
                if not isinstance(preset_val, dict) or (
                    "tiers" not in preset_val and "mapping" not in preset_val
                ):
                    return self._send_json(
                        {"error": f"Preset '{preset_id}' must be an object with a 'tiers' or 'mapping' key"},
                        status=400,
                    )
                # Strip synthetic fields added by the merged endpoint before persisting.
                preset_val.pop("source", None)
                providers_block = preset_val.get("providers")
                if isinstance(providers_block, dict):
                    for prov_val in providers_block.values():
                        if isinstance(prov_val, dict):
                            prov_val.pop("source", None)
            path = resolve_asset(self.__class__.root, "config") / "tier-presets.yaml"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as fh:
                yaml.dump(data, fh, default_flow_style=False, sort_keys=False)
            return self._send_json({"success": True})
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_TIER_PRESETS_UPDATE")
            return self._send_json(body, status=status)

    def _agent_meta_root(self) -> Path:
        """Resolve the agent-meta framework root for lib helpers.

        Delegates to :meth:`ServiceContext.agent_meta_root` (issue #572) so the
        handler and the extracted services share one resolution.
        """
        return self._service_context().agent_meta_root()

    def _handle_get_model_mapping(self) -> None:
        """Return a matrix of role → resolved model ID for every provider.

        Loads role-defaults.yaml and tier-presets.yaml once, then resolves
        each role × provider combination in memory — no repeated disk I/O.
        """
        try:
            self._ensure_lib_on_path()
            from lib.io import _load_yaml_or_json
            from lib.providers import resolve_providers
            from lib.roles import _KNOWN_TIERS, _resolve_tier_to_model, _upgrade_tier

            project_config = self.__class__.config_manager.read("project") or {}
            agent_meta_root = self._agent_meta_root()
            raw_providers_cfg, _ = _load_yaml_or_json(agent_meta_root / "config" / "ai-providers.yaml")
            if not isinstance(raw_providers_cfg, dict):
                raw_providers_cfg = {}
            providers_cfg = raw_providers_cfg.get("providers") or {}
            providers = resolve_providers(project_config, providers_cfg)

            hierarchy = self._template_service().build_agent_hierarchy()
            role_names = [r["name"] for r in hierarchy.get("roles", [])]
            project_roles = project_config.get("roles") or []
            if isinstance(project_roles, list):
                for role in project_roles:
                    if role not in role_names:
                        role_names.append(role)

            # --- Pre-load configs once ---
            role_defaults, _ = _load_yaml_or_json(agent_meta_root / "config" / "role-defaults.yaml")
            if not isinstance(role_defaults, dict):
                role_defaults = {}
            roles_cfg = role_defaults.get("roles") or {}
            global_presets, _ = _load_yaml_or_json(agent_meta_root / "config" / "tier-presets.yaml")
            if not isinstance(global_presets, dict):
                global_presets = {}
            project_presets = project_config.get("tier-presets") or {}

            provider_names = sorted(providers, key=str.lower)
            rows: list[dict] = []
            for role in role_names:
                row: dict = {"name": role, "mappings": {}}
                meta_model = (roles_cfg.get(role) or {}).get("model", "")
                for provider in provider_names:
                    pc = providers_cfg.get(provider) or {}

                    # --- Inline resolve_model (single call per cell, no I/O) ---
                    model_id = ""
                    tier_or_id = ""
                    explicit = False

                    overrides = project_config.get("model-overrides") or {}
                    prov_override = overrides.get(provider, {}) if isinstance(overrides, dict) else {}
                    if isinstance(prov_override, dict) and role in prov_override:
                        tier_or_id = str(prov_override[role])
                        explicit = True
                    elif isinstance(overrides, dict) and role in overrides and not isinstance(overrides[role], dict):
                        if provider == "Claude":
                            tier_or_id = str(overrides[role])
                            explicit = True

                    if not tier_or_id:
                        tier_or_id = meta_model

                    if not explicit:
                        tier_overrides = project_config.get("tier-overrides") or {}
                        if role in tier_overrides:
                            tier_or_id = str(tier_overrides[role])

                    if tier_or_id and tier_or_id not in _KNOWN_TIERS:
                        model_id = _resolve_tier_to_model(tier_or_id, provider, pc)
                    else:
                        base_tier = tier_or_id
                        preset_name = project_config.get("tier-preset", "Normal") or "Normal"
                        se_focus = bool(project_config.get("se-focus", False))
                        if preset_name.endswith(" (SE)"):
                            se_focus = True
                            preset_name = preset_name.replace(" (SE)", "")
                        if se_focus and role.startswith("se-"):
                            base_tier = _upgrade_tier(base_tier, 1)

                        presets = project_presets.get(preset_name) if isinstance(project_presets, dict) and preset_name in project_presets else global_presets.get(preset_name) or {}
                        if isinstance(presets, dict) and "tiers" in presets:
                            prov_tiers = (presets.get("providers") or {}).get(provider, {}).get("tiers") or {}
                            direct = prov_tiers.get(base_tier) or presets["tiers"].get(base_tier, "")
                            if direct:
                                pto = project_config.get("provider-tier-overrides") or {}
                                if provider in pto and base_tier in pto[provider]:
                                    model_id = str(pto[provider][base_tier])
                                else:
                                    model_id = direct
                            else:
                                model_id = _resolve_tier_to_model(base_tier, provider, pc)
                        else:
                            preset_matrix = presets.get("mapping") or {}
                            mapped = preset_matrix.get(base_tier, base_tier)
                            pto = project_config.get("provider-tier-overrides") or {}
                            if provider in pto and mapped in pto[provider]:
                                model_id = str(pto[provider][mapped])
                            else:
                                model_id = _resolve_tier_to_model(mapped, provider, pc)

                    source = "explicit-override" if explicit else "role-default"
                    row["mappings"][provider] = {"model_id": model_id or "", "source": source}
                rows.append(row)

            return self._send_json({"providers": provider_names, "roles": rows})
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_MODEL_MAPPING")
            return self._send_json(body, status=status)

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #

    def _serve_ui(self) -> None:
        ui_path = resolve_asset(self.root, "docs", "ui", "admin-ui.html")
        if not ui_path.exists():
            raise FileNotFoundError("docs/ui/admin-ui.html (UI bundle missing)")
        self._send_bytes(ui_path.read_bytes(), "text/html; charset=utf-8")

    def _role_defaults_path(self) -> Path:
        """Resolve the path to ``role-defaults.yaml`` for either layout.

        Delegates to :meth:`ServiceContext.role_defaults_path` (issue #572) —
        the single resolver shared with the template/pipeline/reflection code.
        """
        return self._service_context().role_defaults_path()

    def _deep_merge(self, base: Any, override: Any) -> Any:
        """Recursively merge ``override`` into ``base``."""
        if isinstance(base, dict) and isinstance(override, dict):
            result = dict(base)
            for k, v in override.items():
                result[k] = self._deep_merge(result.get(k), v)
            return result
        return override

    def _write_project_section(self) -> None:
        """Partial update of one top-level section of ``project.yaml``."""
        body = self._read_body()
        if isinstance(body, dict) and "section" in body and "data" in body:
            section = body["section"]
            data = body["data"]
        elif isinstance(body, dict) and "key" in body and "value" in body:
            section = body["key"]
            data = body["value"]
        else:
            raise ValueError("expected JSON body with 'section' and 'data', or 'key' and 'value'")
        allowed = {
            "agent-prompts",             "model-overrides", "model-override-all", "model-inherit-main-chat", "memory-overrides", "permission-mode-overrides",
            "steps-overrides", "dod", "rules", "roles", "orchestrator", "viz", "admin-ui",
            "provider-tier-overrides", "project", "dod-preset", "rules-preset", "speech-mode",
            "conventions", "conventions-preset",
            "tier-preset", "se-focus", "ai-providers", "platforms", "provider-options",
            "provider-isolation", "environments", "model-source-preference", "knowledge-engine",
            "gitignore", "mcp-servers", "mcp-registry", "external-skills", "skills-registry",
            "external-tools", "external-tools-registry", "context_file",
        }
        if section not in allowed:
            raise ValueError(f"section not allowed: {section}")
        if section == "external-tools-registry" and isinstance(data, dict):
            self._validate_permitted_injections_overrides(data)
        existing = self.__class__.config_manager.read("project")
        if not isinstance(existing, dict):
            existing = {}
        self._guard_model_block_write(section, data, existing)
        existing[section] = data
        return self._send_json(self.__class__.config_manager.write("project", existing))

    def _guard_model_block_write(self, section: str, data: Any, existing: dict) -> None:
        """Reject section writes that would break the next ``sync.py`` run.

        Guards the two mutually exclusive per-provider model blocks
        (``MODEL_EXCLUSIVE_BLOCKS``):

        1. Exclusivity: a write whose resulting block would leave a provider
           truthy-set in BOTH ``model-override-all`` AND
           ``model-inherit-main-chat`` is rejected with ``ValueError``
           (mapped to HTTP 400 by :meth:`do_POST`). resolve_model() returns
           on a truthy override-all entry before inheritance is ever
           consulted, so a both-set provider is a config bug — sync-side it
           aborts with SystemExit(1) (lib/config.py::
           _validate_model_inheritance); here the write itself fails so the
           Admin UI gets the same guarantee as direct YAML edits.
        2. Typing: every ``model-inherit-main-chat`` provider entry must be
           a bool (schema: additionalProperties.type=boolean); non-bool
           values are silently ignored by resolve_model() and hard-fail the
           next sync.

        ``false`` counts as unset; different providers never conflict.
        """
        if section not in MODEL_EXCLUSIVE_BLOCKS:
            return

        if section == "model-inherit-main-chat":
            if not isinstance(data, dict):
                raise ValueError(
                    "invalid 'model-inherit-main-chat': expected a mapping "
                    f"of provider -> true/false, got {type(data).__name__}"
                )
            non_bool = sorted(str(k) for k, v in data.items() if not isinstance(v, bool))
            if non_bool:
                raise ValueError(
                    "invalid 'model-inherit-main-chat' entries (every "
                    f"provider entry must be true/false): {', '.join(non_bool)}"
                )

        other = _other_model_block(section)
        conflicts = find_model_block_conflicts(data, existing.get(other))
        if conflicts:
            quoted = ", ".join(f"'{p}'" for p in sorted(conflicts))
            raise ValueError(
                f"conflicting model configuration for provider(s): {quoted} — "
                f"'{section}' and '{other}' are mutually exclusive per "
                "provider. Clear the conflicting "
                f"'{other}' or '{section}' entry for each listed provider first."
            )

    def _validate_permitted_injections_overrides(self, overrides: dict) -> None:
        """Reject a project-override write whose ``permitted-injections`` would
        break the next ``sync.py`` run (schema-invalid kind/name/path combo).

        Without this, a bad edit in the Admin UI (e.g. switching an entry's
        ``kind`` without migrating ``name``/``path``) silently persists to
        ``project.yaml`` and only surfaces as a hard ``SyncError`` the next
        time anything calls ``load_external_tools_registry`` — which is most
        sync operations, not just this panel.
        """
        root = self.__class__.root
        _ensure_scripts_on_path(root)
        from lib.external_tools import _validate_permitted_injections  # type: ignore[import]
        from lib.io import SyncError  # type: ignore[import]

        for tool_name, override in overrides.items():
            if not isinstance(override, dict) or "permitted-injections" not in override:
                continue
            try:
                _validate_permitted_injections(tool_name, override["permitted-injections"])
            except SyncError as exc:
                raise ValueError(str(exc)) from exc

    def _audit_paths(self) -> list[Path]:
        """Return the set of config/agent files to audit."""
        paths = []
        root = self.__class__.root
        for rel in list(SUPER_ADMIN_FILES.values()) + list(PROJECT_FILES.values()):
            p = root / rel
            if p.exists():
                paths.append(p)
        return paths

    def _ensure_lib_on_path(self) -> None:
        """Ensure ``scripts/lib`` is on ``sys.path`` for imports."""
        lib = self.__class__.root / "scripts" / "lib"
        if str(lib) not in sys.path:
            sys.path.insert(0, str(lib))

    def _get_help_docs(self) -> dict:
        """Parse admin-ui-reference.md and return help-id mapping."""
        ref_path = self.__class__.root / "docs" / "api" / "admin-ui-reference.md"
        if not ref_path.exists():
            return {}
            
        content = ref_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        
        help_map = {}
        current_id = None
        current_text = []
        
        for line in lines:
            if line.startswith("<!-- help-id: "):
                # Save previous block if exists
                if current_id:
                    help_map[current_id] = "\n".join(current_text).strip()
                current_id = line.replace("<!-- help-id: ", "").replace(" -->", "").strip()
                current_text = []
            elif line.startswith(("### ", "## ")):
                # A new heading stops the current block parsing until the next help-id
                if current_id:
                    help_map[current_id] = "\n".join(current_text).strip()
                    current_id = None
            elif current_id:
                # Skip other HTML comments like <!-- last-updated -->
                if line.startswith("<!--"):
                    continue
                current_text.append(line)
                
        # Catch the last one
        if current_id:
            help_map[current_id] = "\n".join(current_text).strip()
            
        return help_map

    def _send_template(self, role: str) -> None:
        """Send a generated agent template as plain text."""
        path = self._template_service().template_path(role)
        if not path.exists():
            raise FileNotFoundError(f"agent template not found: {role}")
        return self._send_bytes(path.read_bytes(), "text/markdown; charset=utf-8")

    def _write_template(self, role: str) -> None:
        """Write an agent template back to disk.

        HTTP glue only — validation and the atomic write live in
        :meth:`TemplateService.write_template` (issue #572).
        """
        body = self._read_body()
        return self._send_json(self._template_service().write_template(role, body))

    def _stream_events(self) -> None:
        """SSE endpoint that streams configuration change events."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        watcher = self.__class__.config_watcher
        event_queue = watcher.subscribe()
        try:
            while True:
                try:
                    event = event_queue.get(timeout=SSE_HEARTBEAT_SECONDS)
                except queue.Empty:
                    self.wfile.write(b"data: heartbeat\n\n")
                    self.wfile.flush()
                    continue
                if event is None:
                    self.wfile.write(b"data: heartbeat\n\n")
                else:
                    self.wfile.write(f"data: {json.dumps(event)}\n\n".encode())
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            # Client disconnected — end the stream quietly.
            pass
        finally:
            watcher.unsubscribe(event_queue)

    def _get_submodule_protection_status(self) -> dict:
        """Return Submodule Protection status (Framework Default vs Project Override)."""
        root = self.__class__.root
        project_config = self.__class__.config_manager.read("project")

        override_text = None
        is_override = False

        if isinstance(project_config, dict):
            sp_cfg = project_config.get("submodule-protection") or project_config.get("submodule_protection")
            if sp_cfg is not None:
                is_override = True
                if isinstance(sp_cfg, str):
                    override_text = sp_cfg
                elif isinstance(sp_cfg, dict):
                    override_text = sp_cfg.get("text") or sp_cfg.get("content") or json.dumps(sp_cfg, indent=2)
            else:
                rules_cfg = project_config.get("rules", {})
                if isinstance(rules_cfg, dict) and "submodule-protection" in rules_cfg:
                    is_override = True
                    override_text = str(rules_cfg["submodule-protection"])

        if not is_override:
            proj_rule_paths = [
                root / ".claude" / "rules" / "submodule-protection.md",
                root / "rules" / "3-project" / "submodule-protection.md",
                root / ".meta-config" / "submodule-protection.md",
            ]
            for p in proj_rule_paths:
                if p.exists():
                    is_override = True
                    override_text = p.read_text(encoding="utf-8")
                    break

        default_template = resolve_asset(root, "templates", "submodule-protection.template.md")
        default_rule = resolve_asset(root, "rules", "1-generic", "submodule-protection.md")

        default_text = ""
        if default_template.exists():
            default_text = default_template.read_text(encoding="utf-8")
        elif default_rule.exists():
            default_text = default_rule.read_text(encoding="utf-8")

        status_type = "Project Override" if is_override else "Framework Default"
        text = override_text if (is_override and override_text) else default_text

        return {
            "status": status_type,
            "is_override": is_override,
            "text": text,
            "default_text": default_text
        }

    def _read_environments(self) -> dict:
        """Return the environments: section from project.yaml."""
        project_config = self.__class__.config_manager.read("project")
        if not isinstance(project_config, dict):
            return {}
        return project_config.get("environments", {})

    def _read_env_scripts(self) -> dict:
        """Return the generated env script contents."""
        root = self.__class__.root
        scripts = {}
        for script_file in (".meta-config/env.ps1", ".meta-config/env.sh",
                             ".meta-config/env.unset.ps1", ".meta-config/env.unset.sh"):
            p = root / script_file
            if p.exists():
                scripts[script_file] = p.read_text(encoding="utf-8")
            else:
                scripts[script_file] = None
        return scripts

    def _delete_environment(self, name: str) -> dict:
        """Remove a single env var from the environments section of project.yaml."""
        project_config = self.__class__.config_manager.read("project")
        if not isinstance(project_config, dict):
            return {"error": "project config not found"}
        envs = project_config.get("environments", {})
        if not isinstance(envs, dict) or name not in envs:
            raise FileNotFoundError(f"environment variable '{name}' not found")
        del envs[name]
        project_config["environments"] = envs
        result = self.__class__.config_manager.write("project", project_config)
        return {"ok": True, "deleted": name, "result": result}

    def _handle_deactivate_providers(self) -> None:
        """Deactivate providers: zip and remove their directories.

        HTTP glue only — the work lives in
        :meth:`AuditService.deactivate_providers` (issue #572).
        """
        body = self._read_body() or {}
        providers = body.get("providers", [])
        if not isinstance(providers, list):
            providers = []
        try:
            return self._send_json(self._audit_service().deactivate_providers(providers))
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_DEACTIVATE_PROVIDERS")
            return self._send_json(body, status=status)

    def _handle_activate_providers(self) -> None:
        """Activate providers: restore from backup zips.

        HTTP glue only — the work lives in
        :meth:`AuditService.activate_providers` (issue #572).
        """
        body = self._read_body() or {}
        providers = body.get("providers", [])
        if not isinstance(providers, list):
            providers = []
        try:
            return self._send_json(self._audit_service().activate_providers(providers))
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_ACTIVATE_PROVIDERS")
            return self._send_json(body, status=status)

    # ------------------------------------------------------------------ #
    # Backup handlers                                                    #
    # ------------------------------------------------------------------ #

    def _handle_get_backups(self) -> None:
        root = self.__class__.root
        try:
            _ensure_scripts_on_path(root)
            from lib.backup import list_backups  # type: ignore[import]
            from lib.providers import load_providers_config  # type: ignore[import]

            project_config = self.__class__.config_manager.read("project")
            provider_config = load_providers_config(root)
            return self._send_json(list_backups(root, project_config, provider_config))
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_BACKUPS")
            return self._send_json(body, status=status)

    def _handle_create_backup(self) -> None:
        root = self.__class__.root
        body = self._read_body() or {}
        providers = body.get("providers", None)
        label = body.get("label", None)
        
        try:
            _ensure_scripts_on_path(root)
            from lib.backup import create_backup  # type: ignore[import]
            from lib.providers import load_providers_config  # type: ignore[import]

            project_config = self.__class__.config_manager.read("project")
            provider_config = load_providers_config(root)

            class _Log:
                def info(self, *a): pass
                def warn(self, *a): pass
                def error(self, *a): pass

            log = _Log()
            result = create_backup(
                root, providers, provider_config, project_config, log,
                label=label, source_version=self.__class__.version
            )
            return self._send_json(result)
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_CREATE_BACKUP")
            return self._send_json(body, status=status)

    def _handle_restore_backup(self) -> None:
        root = self.__class__.root
        body = self._read_body() or {}
        archive_name = body.get("archive_name")
        if not archive_name:
            return self._send_json({"error": "archive_name is required"}, status=400)
            
        providers = body.get("providers", None)
        force = body.get("force", False)

        try:
            _ensure_scripts_on_path(root)
            from lib.backup import restore_backup  # type: ignore[import]
            from lib.providers import load_providers_config  # type: ignore[import]

            project_config = self.__class__.config_manager.read("project")
            provider_config = load_providers_config(root)

            class _Log:
                def info(self, *a): pass
                def warn(self, *a): pass
                def error(self, *a): pass

            log = _Log()
            result = restore_backup(
                root, archive_name, provider_config, project_config, log,
                providers=providers, force=force
            )
            return self._send_json(result)
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_RESTORE_BACKUP")
            return self._send_json(body, status=status)

    def _handle_delete_backup(self, archive_name: str) -> None:
        root = self.__class__.root
        if not archive_name:
            return self._send_json({"error": "archive_name is required"}, status=400)

        try:
            _ensure_scripts_on_path(root)
            from lib.backup import delete_backup  # type: ignore[import]

            project_config = self.__class__.config_manager.read("project")

            class _Log:
                def info(self, *a): pass
                def warn(self, *a): pass
                def error(self, *a): pass

            log = _Log()
            result = delete_backup(root, archive_name, project_config, log)
            return self._send_json(result)
        except Exception as exc:  # noqa: BLE001
            status, body = self._handle_error(exc, "ERR_DELETE_BACKUP")
            return self._send_json(body, status=status)

class _DaemonThreadingHTTPServer(ThreadingHTTPServer):
    """Threading HTTP server that marks request threads as daemons.

    Prevents long-lived SSE connections from blocking process shutdown after
    Ctrl+C — the daemon threads die automatically when the main thread exits.
    """

    daemon_threads = True

    def handle_error(self, request, client_address) -> None:
        """Suppress tracebacks for routine client disconnects.

        Browsers routinely open speculative/keep-alive connections and abort
        them mid-read (tab close, navigation, SSE stream torn down) — that
        surfaces here as ConnectionAbortedError/ConnectionResetError/
        BrokenPipeError/TimeoutError raised while socketserver is still
        reading the request line, before a request handler even runs. That
        is expected traffic noise, not a server bug; printing a full
        traceback for every one of them (the default handle_error behavior)
        drowns out real errors. Anything else still gets the normal
        traceback so actual bugs stay visible.
        """
        exc_type = sys.exc_info()[0]
        if exc_type is not None and issubclass(
            exc_type, (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, TimeoutError)
        ):
            return
        super().handle_error(request, client_address)


class AdminServer:
    """Container that owns the HTTP server and optional watcher thread."""

    def __init__(
        self,
        root: Path,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        enable_watcher: bool = False,
        enable_viz: bool = True,
        admin_token: str | None = None,
        admin_token_file: str | None = None,
        allowed_hosts: tuple[str, ...] | None = None,
    ) -> None:
        # Load admin-ui config from project.yaml (token, allowed-hosts, bind-host)
        admin_cfg = _load_admin_ui_config(root)
        # CLI args override config file values
        effective_token = _resolve_admin_token(
            cli_token=admin_token,
            config_token=admin_cfg["token"],
            config_token_file=admin_token_file or admin_cfg["token_file"],
        )
        # Allowed hosts: CLI > config > default loopback
        effective_allowed_hosts = tuple(allowed_hosts) if allowed_hosts else tuple(admin_cfg["allowed_hosts"])
        # --- Fail-closed: non-loopback requires token ---
        is_loopback = host in LOOPBACK_HOSTS
        if not is_loopback and not effective_token:
            raise ValueError(
                f"refusing to bind on non-loopback host {host!r} without token authentication.\n"
                f"Configure admin-ui.token in .meta-config/project.yaml, set ADMIN_UI_TOKEN "
                f"environment variable, or pass --admin-token."
            )
        if not is_loopback:
            print(f"  * Token auth enabled — binding to {host}:{port}", file=sys.stderr)
        self.root = root.resolve()
        self.host = host
        self.port = port
        self.mode = detect_mode(self.root)
        _warn_if_world_readable(self.root / ".meta-config" / "project.yaml")
        # Always create the watcher instance so the SSE endpoint can subscribe;
        # the background polling thread is only started when enabled (see start()).
        self.watcher: ConfigWatcher = ConfigWatcher(self.root)
        self.enable_watcher = enable_watcher
        self.enable_viz = enable_viz
        self.viz_manager = VizManager(self.root)

        AdminRequestHandler.config_manager = ConfigManager(self.root, self.mode)
        AdminRequestHandler.sync_executor = SyncExecutor(self.root)
        AdminRequestHandler.viz_manager = self.viz_manager
        AdminRequestHandler.config_watcher = self.watcher
        AdminRequestHandler.mode = self.mode
        AdminRequestHandler.root = self.root
        AdminRequestHandler.version = self._read_version()
        AdminRequestHandler.bind_host = self.host
        AdminRequestHandler.bind_port = self.port
        AdminRequestHandler.allowed_hosts = effective_allowed_hosts
        AdminRequestHandler.admin_token = effective_token

        self.httpd = _DaemonThreadingHTTPServer((self.host, self.port), AdminRequestHandler)

    def _read_version(self) -> str:
        # First try to read agent-meta-version from .meta-config/project.yaml
        config_path = self.root / ".meta-config" / "project.yaml"
        if config_path.exists():
            try:
                _ensure_scripts_on_path(self.root)
                from lib.config import load_config  # type: ignore[import]
                config = load_config(config_path)
                if "agent-meta-version" in config:
                    return str(config["agent-meta-version"])
            except Exception:  # noqa: BLE001, S110
                pass

        # Fallback 1: .agent-meta/VERSION (if used as submodule)
        fallback_file = self.root / ".agent-meta" / "VERSION"
        if fallback_file.exists():
            return fallback_file.read_text(encoding="utf-8").strip()

        # Fallback 2: VERSION in root (if used standalone)
        version_file = self.root / "VERSION"
        if version_file.exists():
            return version_file.read_text(encoding="utf-8").strip()
            
        return "unknown"

    def start(self) -> None:
        """Run the server (blocking). Honours ``Ctrl+C``."""
        if self.enable_watcher:
            self.watcher.start()

        # Start Viz dashboard + MCP server as supervised subprocesses.
        if self.enable_viz:
            self.viz_manager.start_all()

        print("  i  agent-meta Admin UI")
        print(f"  i  Mode:    {self.mode}")
        print(f"  i  Version: {AdminRequestHandler.version}")
        print(f"  i  URL:     http://{self.host}:{self.port}")
        print(f"  i  Root:    {self.root}")
        if self.enable_watcher:
            print("  i  Watcher: enabled (.meta-viz/events.jsonl)")
        if not self.enable_viz:
            print("  i  Viz/MCP: disabled (--no-viz)")
        print("  i  Press Ctrl+C to stop")
        print()

        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  i  Server stopped.")
        finally:
            self.httpd.server_close()
            if self.watcher is not None:
                self.watcher.stop()
            # Sub-servers are intentionally left running — they are detached
            # processes with their own PID-files. Stop them via
            # ``python scripts/admin-server.py stop`` (or ``viz-server.py stop``).


# --------------------------------------------------------------------------- #
# CLI subcommands (start/stop/status) -- detached background mode            #
# --------------------------------------------------------------------------- #
#
# ``start`` launches the Admin UI (and, unless --no-viz, the Viz dashboard +
# MCP server) as a detached background process and returns immediately, so it
# can be driven from a slash-command/skill without blocking the caller.
# A bare invocation with no subcommand keeps the historic behaviour: it runs
# the server in the foreground until Ctrl+C.


def _admin_start_detached(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    pid_file = root / ADMIN_PID_FILE
    log_file = root / ADMIN_LOG_FILE

    existing_pid = _read_pid(pid_file)
    if _is_pid_running(existing_pid):
        print(f"  -  Admin UI already running (PID: {existing_pid})")
        print(f"  i  URL: http://{args.host}:{args.port}")
        return

    pid_file.parent.mkdir(parents=True, exist_ok=True)
    if log_file.exists():
        try:
            log_file.unlink()
        except PermissionError:
            pass

    # Re-invoke this script with the same flags but no subcommand, so the
    # child runs the historic blocking `serve_forever()` path.
    cmd = [sys.executable, str(Path(__file__).resolve()),
           "--port", str(args.port), "--host", args.host, "--root", str(root)]
    if args.admin_token:
        cmd += ["--admin-token", args.admin_token]
    if args.allowed_hosts:
        cmd += ["--allowed-hosts", *args.allowed_hosts]
    if args.watch:
        cmd.append("--watch")
    if args.no_viz:
        cmd.append("--no-viz")

    log_fh = open(log_file, "a", encoding="utf-8")  # noqa: SIM115
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        proc = subprocess.Popen(
            cmd, stdout=log_fh, stderr=subprocess.STDOUT,
            startupinfo=si, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            cwd=str(root),
        )
    else:
        proc = subprocess.Popen(
            cmd, stdout=log_fh, stderr=subprocess.STDOUT,
            start_new_session=True, cwd=str(root),
        )

    pid_file.write_text(str(proc.pid), encoding="utf-8")
    time.sleep(1.5)

    if _is_pid_running(proc.pid):
        print(f"  +  Admin UI started (PID: {proc.pid})")
        print(f"  i  URL:  http://{args.host}:{args.port}")
        print(f"  i  Logs: {log_file}")
    else:
        print(f"  !  Admin UI failed to start -- see {log_file}")
        pid_file.unlink(missing_ok=True)
        sys.exit(1)


def _admin_stop(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    pid_file = root / ADMIN_PID_FILE
    pid = _read_pid(pid_file)
    if pid and _is_pid_running(pid):
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/F"],
                    check=True, capture_output=True,
                )
            else:
                os.kill(pid, 15)
                time.sleep(1)
                if _is_pid_running(pid):
                    os.kill(pid, 9)
            print(f"  -  Admin UI stopped (PID: {pid})")
        except Exception as exc:  # noqa: BLE001
            print(f"  !  Error stopping Admin UI: {exc}")
    else:
        print("  -  Admin UI not running")
    pid_file.unlink(missing_ok=True)

    # Stop the supervised Viz dashboard + MCP server too -- `start` brings
    # all three up together, so `stop` tears all three down together.
    VizManager(root).stop_all()


def _admin_status(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    admin_pid = _read_pid(root / ADMIN_PID_FILE)
    admin_running = _is_pid_running(admin_pid)
    print(f"  Admin UI      (port {args.port}): {'RUNNING' if admin_running else 'STOPPED'}")
    if admin_running:
        print(f"    PID: {admin_pid}  |  http://{args.host}:{args.port}")

    status = VizManager(root).status()
    viz = status["viz"]
    mcp = status["mcp"]
    print(f"  Viz dashboard (port {viz['port']}): {'RUNNING' if viz['running'] else 'STOPPED'}")
    if viz["running"]:
        print(f"    PID: {viz['pid']}  |  {viz['url']}")
    print(f"  MCP server    (port {mcp['port']}): {'RUNNING' if mcp['running'] else 'STOPPED'}")
    if mcp["running"]:
        print(f"    PID: {mcp['pid']}  |  {mcp['url']}")


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #


def main() -> None:
    parser = argparse.ArgumentParser(
        description="agent-meta Admin UI Server (zero-dependency stdlib HTTP)",
    )
    parser.add_argument("command", nargs="?", default=None,
                        choices=["start", "stop", "status", "restart"],
                        help="start: launch detached in the background (default when omitted: "
                             "run in the foreground until Ctrl+C). stop: terminate Admin UI + "
                             "Viz + MCP. status: show running state. restart: stop then start.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"Server port (default: {DEFAULT_PORT})")
    parser.add_argument("--host", default=DEFAULT_HOST,
                        help=f"Bind host address (default: {DEFAULT_HOST}). "
                             f"Non-loopback addresses (e.g., 0.0.0.0) require --admin-token or ADMIN_UI_TOKEN env var.")
    parser.add_argument("--admin-token", default=None,
                        help="Authentication token for remote access. "
                             "REQUIRED when --host is non-loopback. "
                             "Equivalent to ADMIN_UI_TOKEN env var or admin-ui.token in project.yaml.")
    parser.add_argument("--allowed-hosts", nargs="*", default=None,
                        help="Additional allowed origin hosts for CORS/DNS-rebinding protection. "
                             "Default: 127.0.0.1 localhost ::1. "
                             "Extends (does not replace) the default loopback set.")
    parser.add_argument("--root", default=".",
                        help="Project root directory (default: current directory)")
    parser.add_argument("--watch", action="store_true",
                        help="Enable filesystem watcher (polls config files every 2s)")
    parser.add_argument(
        "--no-viz",
        dest="no_viz",
        action="store_true",
        help=(
            "Skip starting the Viz dashboard and MCP server as subprocesses. "
            "Useful for lightweight / CI environments where only the Admin UI "
            "itself is needed."
        ),
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"  !  root directory does not exist: {root}", file=sys.stderr)
        sys.exit(1)

    if args.command == "stop":
        _admin_stop(args)
        return
    if args.command == "status":
        _admin_status(args)
        return
    if args.command == "start":
        _admin_start_detached(args)
        return
    if args.command == "restart":
        _admin_stop(args)
        time.sleep(1)
        _admin_start_detached(args)
        return

    server = AdminServer(
        root,
        host=args.host,
        port=args.port,
        enable_watcher=args.watch,
        enable_viz=not args.no_viz,
        admin_token=args.admin_token,
        allowed_hosts=tuple(args.allowed_hosts) if args.allowed_hosts else None,
    )
    server.start()


if __name__ == "__main__":
    main()
