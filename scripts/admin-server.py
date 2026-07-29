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
  python scripts/admin-server.py               (Admin UI + Viz dashboard + MCP server)
  python scripts/admin-server.py --no-viz      (Admin UI only, lightweight mode)
  python scripts/admin-server.py --port 7420 --root .
  python scripts/sync.py --admin               (after a normal sync)
  python scripts/sync.py --admin-only          (skip sync)

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
import os
import queue
import subprocess
import sys
import threading
import time
from collections.abc import Iterable
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import yaml
except ImportError:  # pragma: no cover
    print("  !  PyYAML is required. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# --------------------------------------------------------------------------- #
# Constants                                                                   #
# --------------------------------------------------------------------------- #

DEFAULT_PORT = 7420
DEFAULT_HOST = "127.0.0.1"
MAX_BACKUPS = 5
SSE_HEARTBEAT_SECONDS = 15

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

_DEFAULT_VIZ_PORT          = 8765
_DEFAULT_VIZ_TIMEOUT       = 300
_DEFAULT_MCP_PORT          = 9090
_DEFAULT_VIZ_ENABLED       = False
_DEFAULT_VIZ_MODE          = "off"
_DEFAULT_VIZ_EVENT_LOG     = ".meta-viz/events.jsonl"
_DEFAULT_VIZ_RETENTION     = 7
_DEFAULT_VIZ_SESSION_TIMEOUT = 5

# Loopback addresses are the ONLY values the ``--host`` flag accepts. The admin
# UI exposes write access to every editable config file; binding the server to
# anything reachable from the network would be a privilege-escalation vector.
ALLOWED_HOSTS: tuple[str, ...] = ("127.0.0.1", "localhost", "::1")

# Super-admin config files (only available when ``agents/1-generic/`` exists).
SUPER_ADMIN_FILES: dict[str, str] = {
    "role-defaults":     "config/role-defaults.yaml",
    "ai-providers":      "config/ai-providers.yaml",
    "skills-registry":   "config/skills-registry.yaml",
    "mcp-registry":      "config/mcp-registry.yaml",
    "dod-presets":       "config/dod-presets.yaml",
    "rules-presets":     "config/rules-presets.yaml",
    "delegation-syntax": "config/delegation-syntax.yaml",
    "export":            "config/export.yaml",
}

# Always-available project configs.
PROJECT_FILES: dict[str, str] = {
    "project": ".meta-config/project.yaml",
    "project-mcp-registry": ".meta-config/mcp-registry.yaml",
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
    try:
        sys.path.insert(0, str(root / "scripts"))
        sys.path.insert(0, str(root / ".agent-meta" / "scripts"))
        from lib.config import load_config  # type: ignore[import]
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
    except Exception:  # noqa: BLE001
        return _viz_defaults()


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

        Raises:
            SecurityError: if ``key`` is unknown, restricted for the current
                mode, or would escape ``root`` (path traversal protection).
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
        """Create a timestamped backup copy of ``path`` next to the original."""
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # noqa: DTZ005
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

    def _send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
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
        raw = self.rfile.read(length)
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON body: {exc}") from exc

    # ------------------------------------------------------------------ #
    # CSRF / DNS-rebinding protection                                    #
    # ------------------------------------------------------------------ #

    def _check_origin(self) -> None:
        """Reject mutating requests whose ``Origin`` header is not a loopback
        address and whose ``Host`` header does not match the bind target.

        - Browser tabs on other origins cannot mutate configs (CSRF defence).
        - Even if a hostile site DNS-rebinds to ``127.0.0.1``, the ``Host``
          header on the forged request will not match the bind ``host:port``,
          so the request is rejected (DNS-rebinding defence).
        """
        expected_port = self.__class__.bind_port
        expected_host = self.__class__.bind_host

        origin = self.headers.get("Origin")
        if origin is None:
            # Same-origin form POSTs and CLI tools (curl) often omit Origin.
            # We still require the Host header to match — see below.
            pass
        else:
            allowed_origins = {
                f"http://127.0.0.1:{expected_port}",
                f"http://localhost:{expected_port}",
                f"http://[::1]:{expected_port}",
            }
            if origin not in allowed_origins:
                raise SecurityError(f"origin not allowed: {origin!r}")

        host = self.headers.get("Host", "")
        allowed_hosts = {
            f"127.0.0.1:{expected_port}",
            f"localhost:{expected_port}",
            f"[::1]:{expected_port}",
        }
        # Allow the configured bind host as well (covers explicit ``--host``).
        allowed_hosts.add(f"{expected_host}:{expected_port}")
        if host not in allowed_hosts:
            raise SecurityError(f"host header not allowed: {host!r}")

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

    def do_GET(self) -> None:
        try:
            self._dispatch_get()
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
            self._send_json({"error": "internal", "detail": str(exc)}, status=500)

    def do_PUT(self) -> None:
        try:
            self._check_origin()
            self._dispatch_put()
        except SecurityError as exc:
            self._send_json({"error": "forbidden", "detail": str(exc)}, status=403)
        except ValueError as exc:
            self._send_json({"error": "bad_request", "detail": str(exc)}, status=400)
        except FileNotFoundError as exc:
            self._send_json({"error": "not_found", "detail": str(exc)}, status=404)
        except ConnectionError:
            # See ``do_GET`` — silently bail on dead client socket.
            return
        except Exception as exc:  # pragma: no cover  # noqa: BLE001
            self._send_json({"error": "internal", "detail": str(exc)}, status=500)

    def do_POST(self) -> None:
        try:
            self._check_origin()
            self._dispatch_post()
        except SecurityError as exc:
            self._send_json({"error": "forbidden", "detail": str(exc)}, status=403)
        except ValueError as exc:
            self._send_json({"error": "bad_request", "detail": str(exc)}, status=400)
        except ConnectionError:
            # See ``do_GET`` — silently bail on dead client socket.
            return
        except Exception as exc:  # pragma: no cover  # noqa: BLE001
            self._send_json({"error": "internal", "detail": str(exc)}, status=500)

    def do_DELETE(self) -> None:
        try:
            self._check_origin()
            self._dispatch_delete()
        except SecurityError as exc:
            self._send_json({"error": "forbidden", "detail": str(exc)}, status=403)
        except FileNotFoundError as exc:
            self._send_json({"error": "not_found", "detail": str(exc)}, status=404)
        except ConnectionError:
            return
        except Exception as exc:  # pragma: no cover  # noqa: BLE001
            self._send_json({"error": "internal", "detail": str(exc)}, status=500)

    # ------------------------------------------------------------------ #
    # GET routes                                                         #
    # ------------------------------------------------------------------ #

    def _dispatch_get(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/":
            return self._serve_ui()

        if path == "/favicon.png":
            favicon_path = resolve_asset(self.root, "docs", "ui", "favicon.png")
            if favicon_path.exists():
                return self._send_bytes(favicon_path.read_bytes(), "image/png")
            self.send_response(404)
            self.end_headers()
            return

        if path == "/api/health":
            return self._send_json({
                "status": "ok",
                "version": self.__class__.version,
                "mode": self.__class__.mode,
            })

        if path == "/api/mode":
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

        if path == "/api/project":
            project_data = self.__class__.config_manager.read("project").get("project", {})
            return self._send_json({"project": {
                "name": project_data.get("name", ""),
                "version": project_data.get("version", ""),
                "id-prefix": project_data.get("id-prefix", project_data.get("prefix", ""))
            }})

        if path.startswith("/api/config/"):
            key = path[len("/api/config/"):]
            data = self.__class__.config_manager.read(key)
            return self._send_json(data)

        if path == "/api/schema/project":
            schema_path = self._find_schema_path()
            if not schema_path.exists():
                raise FileNotFoundError("project-config.schema.json")
            self._send_bytes(schema_path.read_bytes(), "application/json; charset=utf-8")
            return

        if path == "/api/help":
            return self._send_json(self._get_help_docs())

        if path == "/api/sync/status":
            return self._send_json(self.__class__.sync_executor.status())

        if path == "/api/agents/hierarchy":
            return self._send_json(self._build_agent_hierarchy())

        if path == "/api/pipelines":
            if "help" in (parsed.query or "").lower():
                return self._send_json(self._pipeline_help())
            return self._send_json(self._read_pipelines())

        if path.startswith("/api/pipelines/"):
            name = path[len("/api/pipelines/"):]
            return self._send_json(self._read_single_pipeline(name))

        if path == "/api/reflection-pairs":
            return self._send_json(self._read_reflection_pairs())

        if path.startswith("/api/reflection-pairs/"):
            pair_id = path[len("/api/reflection-pairs/"):]
            return self._send_json(self._read_reflection_pair(pair_id))

        if path == "/api/agents/templates":
            return self._send_json(self._list_agent_templates())

        if path.startswith("/api/agent-template/"):
            role = path[len("/api/agent-template/"):]
            return self._send_template(role)

        if path == "/api/events":
            return self._stream_events()

        if path == "/api/subserver-status":
            return self._send_json(self.__class__.viz_manager.status())

        if path == "/api/providers":
            return self._send_json(self._list_providers())

        if path == "/api/platforms":
            return self._send_json(self._list_platforms())

        if path == "/api/roles":
            return self._send_json(self._list_roles())

        if path == "/api/config-audit":
            return self._send_json(self._run_config_audit())
            
        if path == "/api/consistency-check":
            return self._send_json(self._run_consistency_check())

        if path == "/api/models":
            return self._handle_get_models()

        if path == "/api/models/active":
            return self._handle_get_models_active()

        if path == "/api/models-dev":
            return self._handle_get_models_dev()

        if path == "/api/model-source":
            return self._handle_get_model_source()

        if path == "/api/model-suggestions":
            return self._handle_get_model_suggestions()

        if path == "/api/ai-providers":
            return self._handle_get_ai_providers()

        if path == "/api/tier-presets":
            return self._handle_get_tier_presets()

        if path == "/api/tier-presets/merged":
            return self._handle_get_tier_presets_merged()

        if path == "/api/model-mapping":
            return self._handle_get_model_mapping()

        if path == "/api/provider-deactivation/status":
            return self._send_json(self._get_deactivation_status())

        if path == "/api/backups":
            return self._handle_get_backups()

        if path in ("/api/submodule-protection", "/api/config/submodule-protection"):
            return self._send_json(self._get_submodule_protection_status())

        if path == "/api/environments":
            return self._send_json(self._read_environments())

        if path == "/api/environments/scripts":
            return self._send_json(self._read_env_scripts())

        raise FileNotFoundError(path)

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
            
        self.__class__.config_manager.write("project", project_config)
        return self._send_json({"status": "saved"})


    # ------------------------------------------------------------------ #
    # DELETE routes                                                      #
    # ------------------------------------------------------------------ #

    def _dispatch_delete(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path.startswith("/api/pipelines/"):
            name = path[len("/api/pipelines/"):]
            return self._send_json(self._delete_pipeline(name))

        if path.startswith("/api/reflection-pairs/"):
            pair_id = path[len("/api/reflection-pairs/"):]
            return self._send_json(self._delete_reflection_pair(pair_id))

        if path.startswith("/api/backups/"):
            archive_name = path[len("/api/backups/"):]
            return self._handle_delete_backup(archive_name)

        if path.startswith("/api/environments/"):
            name = path[len("/api/environments/"):]
            return self._send_json(self._delete_environment(name))

        raise FileNotFoundError(path)

    # ------------------------------------------------------------------ #
    # PUT routes                                                         #
    # ------------------------------------------------------------------ #

    def _dispatch_put(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        # Partial update of a single top-level section of project.yaml. Must be
        # matched BEFORE the generic /api/config/ handler (which would treat
        # "project/section" as a config key).
        if path == "/api/submodule-protection":
            return self._write_submodule_protection()

        if path == "/api/config/project/section":
            return self._write_project_section()

        if path.startswith("/api/config/"):
            key = path[len("/api/config/"):]
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

        if path.startswith("/api/agent-template/"):
            role = path[len("/api/agent-template/"):]
            return self._write_template(role)

        if path == "/api/pipelines":
            body = self._read_body()
            if not isinstance(body, dict) or "pipelines" not in body:
                raise ValueError("expected JSON body with 'pipelines' field")
            pipelines = body["pipelines"]
            if not isinstance(pipelines, dict):
                raise ValueError("'pipelines' must be an object")
            result = self._write_pipelines(pipelines)
            return self._send_json(result)

        if path.startswith("/api/pipelines/"):
            name = path[len("/api/pipelines/"):]
            body = self._read_body()
            if not isinstance(body, dict):
                raise ValueError("expected JSON body with pipeline object")
            result = self._write_single_pipeline(name, body)
            return self._send_json(result)

        if path == "/api/reflection-pairs":
            body = self._read_body()
            if not isinstance(body, dict) or "reflection_pairs" not in body:
                raise ValueError("expected JSON body with 'reflection_pairs' field")
            pairs = body["reflection_pairs"]
            if not isinstance(pairs, list):
                raise ValueError("'reflection_pairs' must be a list")
            result = self._write_reflection_pairs(pairs)
            return self._send_json(result)

        if path.startswith("/api/reflection-pairs/"):
            pair_id = path[len("/api/reflection-pairs/"):]
            body = self._read_body()
            if not isinstance(body, dict):
                raise ValueError("expected JSON body with reflection pair object")
            result = self._write_reflection_pair(pair_id, body)
            return self._send_json(result)


        raise FileNotFoundError(path)

    # ------------------------------------------------------------------ #
    # POST routes                                                        #
    # ------------------------------------------------------------------ #

    def _dispatch_post(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/api/sync/dry-run":
            return self._send_json(self.__class__.sync_executor.dry_run())

        if path == "/api/sync/run":
            return self._send_json(self.__class__.sync_executor.run())

        if path == "/api/config-audit/apply":
            return self._send_json(self._apply_config_audit())

        if path == "/api/models/update":
            return self._handle_post_models_update()

        if path == "/api/models/clear-override":
            return self._handle_post_models_clear_override()

        if path == "/api/models-dev/refresh":
            return self._handle_post_models_dev_refresh()

        if path == "/api/models-dev/import":
            return self._handle_post_models_dev_import()

        if path == "/api/model-source":
            return self._handle_post_model_source()

        if path == "/api/model-source/batch":
            return self._handle_post_model_source_batch()

        if path == "/api/models/exclude":
            return self._handle_post_models_exclude()

        if path == "/api/models/disable":
            return self._handle_post_models_disable()

        if path == "/api/models/enable":
            return self._handle_post_models_enable()

        if path == "/api/pricing/update":
            return self._handle_post_pricing_update()

        if path == "/api/pricing/reset":
            return self._handle_post_pricing_reset()

        if path == "/api/ai-providers/update":
            return self._handle_post_ai_providers_update()

        if path == "/api/tier-presets/update":
            return self._handle_post_tier_presets_update()

        if path == "/api/reflection-pairs":
            body = self._read_body()
            if not isinstance(body, dict):
                raise ValueError("expected JSON body with reflection pair object")
            for field in ("id", "generator", "critic"):
                value = body.get(field)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError("id, generator and critic are required")
            pair_id = self._ensure_pair_id(body)
            result = self._write_reflection_pair(pair_id, body)
            return self._send_json(result)


        # Individual subserver control: /api/subserver/{name}/{action}
        # name in {viz, mcp}, action in {start, stop, restart}.
        subserver = self._match_subserver_route(path)
        if subserver is not None:
            name, action = subserver
            return self._handle_subserver_action(name, action)

        if path == "/api/provider-deactivation/deactivate":
            return self._handle_deactivate_providers()

        if path == "/api/provider-deactivation/activate":
            return self._handle_activate_providers()

        if path == "/api/backups/create":
            return self._handle_create_backup()

        if path == "/api/backups/restore":
            return self._handle_restore_backup()

        raise FileNotFoundError(path)

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
        return resolve_asset(self.__class__.root, "config").parent

    def _load_curation(self) -> dict:
        """Load ``config/model-curation.yaml`` via ``scripts.lib.curation``.

        The import is performed lazily (and ``sys.path`` is extended on demand)
        to mirror the pattern used by ``_load_viz_config`` at module level:
        the admin server must keep starting even when the ``lib`` package is
        not on ``sys.path`` at process boot.
        """
        root = self.__class__.root
        for candidate in (root / "scripts", root / ".agent-meta" / "scripts"):
            if candidate.exists() and str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
        from lib.curation import load_curation  # type: ignore[import]
        curation = load_curation(str(self._curation_root()))
        # ``load_curation`` already normalises shape; ensure keys exist for
        # downstream callers regardless of any future schema changes.
        curation.setdefault("blacklist", [])
        curation.setdefault("disabled", [])
        return curation

    def _save_curation(self, curation: dict) -> None:
        """Persist a curation document via ``scripts.lib.curation.save_curation``."""
        root = self.__class__.root
        for candidate in (root / "scripts", root / ".agent-meta" / "scripts"):
            if candidate.exists() and str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
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
        config_dir = resolve_asset(self.__class__.root, "config")
        registry_path = config_dir / "generated" / "model-registry.json"
        pricing_path = config_dir / "pricing-overlay.yaml"

        override_registry = Path(self.__class__.root) / ".meta-config" / "generated" / "model-registry.json"
        
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
        disabled_ids = set(curation.get("disabled", []))

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
            m["enabled"] = model_id not in disabled_ids
            # Blacklisted ids are filtered during discovery and never appear in
            # the registry; surfaced models are therefore always non-blacklisted.
            m["blacklisted"] = False

        return models

    def _handle_get_models(self) -> None:
        """Return all registered models with curation + pricing metadata."""
        try:
            models = self._collect_models()
            return self._send_json({"models": models})
        except Exception as exc:  # noqa: BLE001
            return self._send_json({"error": str(exc)}, status=500)

    def _handle_get_models_active(self) -> None:
        """Return only models that are currently active.

        A model is active when it is not blacklisted (always true here, see
        ``_collect_models``) and not in ``curation.disabled``. Tier dropdowns
        and model pickers in the admin UI consume this endpoint so disabled
        ids disappear from selectable options without rebuilding the registry.
        """
        try:
            models = [m for m in self._collect_models() if m.get("enabled")]
            return self._send_json({"models": models})
        except Exception as exc:  # noqa: BLE001
            return self._send_json({"error": str(exc)}, status=500)

    # ------------------------------------------------------------------ #
    # Models.dev integration (SDK primary, API fallback)                  #
    # ------------------------------------------------------------------ #

    def _load_models_dev_data(self) -> dict:
        cache = getattr(self.__class__, '_models_dev_cache', None)
        cache_ts = getattr(self.__class__, '_models_dev_cache_ts', 0)

        if cache and cache.get('source') == 'sdk':
            return cache
        if cache and cache.get('source') == 'api' and (time.time() - cache_ts) < 3600:
            return cache

        sdk_data = self._load_from_sdk_snapshot()
        if sdk_data:
            self.__class__._models_dev_cache = sdk_data
            self.__class__._models_dev_cache_ts = time.time()
            return sdk_data

        api_data = self._load_from_models_dev_api()
        if api_data:
            self.__class__._models_dev_cache = api_data
            self.__class__._models_dev_cache_ts = time.time()
            return api_data

        if cache:
            return cache
        return {"source": "error", "error": "No data available", "providers": {}, "models": {}}

    def _load_from_sdk_snapshot(self) -> dict | None:
        try:
            snapshot_path = resolve_asset(self.__class__.root, "node_modules",
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
        except Exception:  # noqa: BLE001
            return None

    def _load_from_models_dev_api(self) -> dict | None:
        try:
            from urllib.request import Request, urlopen

            req = Request("https://models.dev/catalog.json",
                          headers={"User-Agent": "agent-meta-admin/1.0"})
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            return {
                "source": "api",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "providers": data.get("providers", {}),
                "models": data.get("models", {}),
            }
        except Exception:  # noqa: BLE001
            return None

    # Provider keys in ``config/pricing-overlay.yaml`` that never have a real
    # models.dev catalog entry (subscription/flat-fee gateways with no public
    # per-token pricing). Mirrors ``REGISTRY_ONLY`` in
    # ``docs/ui/admin-ui.html`` — keep both lists in sync. Any other overlay
    # key that doesn't match a live models.dev provider id is treated as
    # inert legacy data and ignored here (e.g. a naming mismatch), so we
    # never fabricate a phantom provider for real catalog entries.
    CURATED_ONLY_PROVIDER_KEYS = {"mammouth", "continue"}  # noqa: RUF012

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
        config_dir = resolve_asset(self.__class__.root, "config")
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
                for model_id, price in model_entries.items():
                    if model_id not in models:
                        continue
                    model = dict(models[model_id])
                    cost = dict(model.get("cost") or {})
                    if price.get("input") is not None:
                        cost["input"] = price["input"]
                    if price.get("output") is not None:
                        cost["output"] = price["output"]
                    model["cost"] = cost
                    model["_costSource"] = "overlay"
                    models[model_id] = model
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

    def _handle_get_models_dev(self) -> None:
        try:
            raw = self._load_models_dev_data()
            data = dict(raw)
            providers = self._apply_pricing_overlay(dict(raw.get("providers", {})))
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
            return self._send_json({"error": str(exc)}, status=500)

    def _handle_post_models_dev_refresh(self) -> None:
        try:
            for attr in ('_models_dev_cache', '_models_dev_cache_ts'):
                if hasattr(self.__class__, attr):
                    delattr(self.__class__, attr)
            return self._send_json(self._load_models_dev_data())
        except Exception as exc:  # noqa: BLE001
            return self._send_json({"error": str(exc)}, status=500)

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
            prov[model_id] = {"input": float(input_cost) if input_cost is not None else 0.0,
                              "output": float(output_cost) if output_cost is not None else 0.0}

            # Atomic write with backup
            self.__class__.config_manager._backup(pricing_path)
            pricing_path.write_text(yaml.dump(pricing, default_flow_style=False, allow_unicode=True, sort_keys=False),
                                    encoding="utf-8")
            return self._send_json({"success": True, "provider": provider_id, "model_id": model_id})
        except Exception as exc:  # noqa: BLE001
            return self._send_json({"error": str(exc)}, status=500)

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
            return self._send_json({"error": str(exc)}, status=500)

    def _handle_post_models_clear_override(self) -> None:
        """Clear the downloaded override model registry."""
        try:
            project_root = Path(self.__class__.root)
            target_file = project_root / ".meta-config" / "generated" / "model-registry.json"
            if target_file.exists():
                target_file.unlink()
            return self._send_json({"success": True})
        except Exception as exc:  # noqa: BLE001
            return self._send_json({"error": str(exc)}, status=500)

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

            curation = self._load_curation()
            blacklist = list(curation.get("blacklist", []))
            existing = set(blacklist)
            added = 0
            for model_id in ids_to_blacklist:
                if model_id not in existing:
                    blacklist.append(model_id)
                    existing.add(model_id)
                    added += 1
            curation["blacklist"] = blacklist
            self._save_curation(curation)

            return self._send_json({
                "success": True,
                "blacklisted_count": added,
                "total": len(blacklist),
            })
        except Exception as exc:  # noqa: BLE001
            return self._send_json({"error": str(exc)}, status=500)

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

            curation = self._load_curation()
            disabled = list(curation.get("disabled", []))
            existing = set(disabled)
            added = 0
            for model_id in ids_to_disable:
                if model_id not in existing:
                    disabled.append(model_id)
                    existing.add(model_id)
                    added += 1
            curation["disabled"] = disabled
            self._save_curation(curation)

            return self._send_json({
                "status": "ok",
                "disabled_count": added,
                "total": len(disabled),
            })
        except Exception as exc:  # noqa: BLE001
            return self._send_json({"error": str(exc)}, status=500)

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

            curation = self._load_curation()
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
            self._save_curation(curation)

            return self._send_json({
                "status": "ok",
                "enabled_count": removed,
                "total": len(new_disabled),
            })
        except Exception as exc:  # noqa: BLE001
            return self._send_json({"error": str(exc)}, status=500)

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
            return self._send_json({"error": str(exc)}, status=500)

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
            return self._send_json({"error": str(exc)}, status=500)

    # ------------------------------------------------------------------ #
    # Centralized per-provider model-source preference                    #
    # ------------------------------------------------------------------ #

    def _read_model_source_prefs(self) -> dict:
        """Load the per-provider model-source map from ``project.yaml``.

        Returns a ``{provider_name: "registry"|"modelsdev"}`` dict, dropping
        any entries whose value is not a recognised source. Missing/invalid
        section yields ``{}`` (every provider then defaults to the central
        ``default-model-source`` from ``config/ai-providers.yaml``, see
        ``_default_model_source``).
        """
        project = self.__class__.config_manager.read("project") or {}
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

        Mirrors the registry-fallback logic the Admin UI used client-side:
        the provider's tier values pin down which registry provider slug(s)
        (e.g. ``opencode-go``, ``anthropic``) belong to this framework
        provider, and only active (non-disabled) models for those slugs are
        returned. When no slug can be inferred, all active models are offered
        (matches the previous UI behaviour).
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
        selected = [m for m in models if m.get("provider") in registry_slugs] if registry_slugs else models
        return [
            {"id": m.get("id"), "name": m.get("name") or m.get("id"), "provider": m.get("provider")}
            for m in selected
        ]

    def _suggestions_from_models_dev(self, provider_name: str) -> list[dict]:
        """models.dev-sourced model suggestions for ``provider_name``.

        Returns ``[]`` for providers without a models.dev catalog slug. Ids
        are always the raw models.dev id (1:1, no namespace prefix) so the
        Admin UI dropdown shows exactly what models.dev reports, and so the
        value persisted on save (model-tiers / tier-preset / provider-tier
        overrides) is the same raw id, unchanged. The ``provider`` field
        still carries the models.dev slug (e.g. ``opencode-go``) purely as
        namespace info for display -- it is never re-applied as a prefix.
        """
        slug = PROVIDER_MODELSDEV_SLUGS.get(provider_name)
        if not slug:
            return []
        data = self._load_models_dev_data()
        providers = self._apply_pricing_overlay(dict(data.get("providers", {})))
        node = providers.get(slug)
        if not isinstance(node, dict):
            return []
        out: list[dict] = []
        for m in (node.get("models") or {}).values():
            raw_id = m.get("id")
            if not raw_id:
                continue
            out.append({"id": raw_id, "name": m.get("name") or raw_id, "provider": slug})
        return out

    def _handle_get_model_source(self) -> None:
        """Return the central per-provider model-source map (single source of
        truth for every model dropdown/suggestion in the Admin UI)."""
        try:
            return self._send_json({
                "preferences": self._read_model_source_prefs(),
                "default": self._default_model_source(),
            })
        except Exception as exc:  # noqa: BLE001
            return self._send_json({"error": str(exc)}, status=500)

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
            return self._send_json({"error": str(exc)}, status=500)

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
        except Exception as exc:  # noqa: BLE001
            return self._send_json({"error": str(exc)}, status=500)

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
            source = self._resolve_model_source(provider)
            # Providers with no models.dev catalog slug (Mammouth, Continue)
            # are registry-only regardless of what's persisted in
            # ``model-source-preference`` -- a stale/manually-edited "modelsdev"
            # entry must not silently degrade to an empty suggestion list (see
            # ``PROVIDER_MODELSDEV_SLUGS``). Force registry and report the
            # honest, effective source back to the caller.
            if source == "modelsdev" and provider in PROVIDER_MODELSDEV_SLUGS:
                models = self._suggestions_from_models_dev(provider)
            else:
                source = "registry"
                models = self._suggestions_from_registry(provider)
            return self._send_json({"provider": provider, "source": source, "models": models})
        except Exception as exc:  # noqa: BLE001
            return self._send_json({"error": str(exc)}, status=500)

    def _handle_get_ai_providers(self) -> None:
        try:
            path = resolve_asset(self.__class__.root, "config") / "ai-providers.yaml"
            data = {}
            if path.exists():
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return self._send_json(data)
        except Exception as exc:  # noqa: BLE001
            return self._send_json({"error": str(exc)}, status=500)

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
            return self._send_json({"error": str(exc)}, status=500)

    def _handle_get_tier_presets(self) -> None:
        try:
            path = resolve_asset(self.__class__.root, "config") / "tier-presets.yaml"
            data = {}
            if path.exists():
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return self._send_json(data)
        except Exception as exc:  # noqa: BLE001
            return self._send_json({"error": str(exc)}, status=500)

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
            return self._send_json({"error": str(exc)}, status=500)

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
            return self._send_json({"error": str(exc)}, status=500)

    def _agent_meta_root(self) -> Path:
        """Resolve the agent-meta framework root for lib helpers.

        In super_admin mode the server root is the framework checkout. In
        project_admin mode the framework sources live under ``.agent-meta/``.
        """
        root = self.__class__.root
        if (root / "agents" / "1-generic").is_dir():
            return root
        submodule = root / ".agent-meta"
        if (submodule / "agents" / "1-generic").is_dir():
            return submodule
        return root

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

            hierarchy = self._build_agent_hierarchy()
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
            return self._send_json({"error": str(exc)}, status=500)

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #

    def _serve_ui(self) -> None:
        ui_path = resolve_asset(self.root, "docs", "ui", "admin-ui.html")
        if not ui_path.exists():
            raise FileNotFoundError("docs/ui/admin-ui.html (UI bundle missing)")
        self._send_bytes(ui_path.read_bytes(), "text/html; charset=utf-8")

    def _find_schema_path(self) -> Path:
        return resolve_asset(self.__class__.root, "config", "project-config.schema.json")

    def _build_agent_hierarchy(self) -> dict:
        """Derive a lightweight role hierarchy directly from
        ``config/role-defaults.yaml``. Falls back to an empty list if the file
        is missing (project-admin mode without super-admin configs).

        Each role entry includes:
          * ``name``, ``tier``, ``model``, ``memory``, ``parallel``,
            ``permission_mode``
          * ``description`` — never empty (falls back to template frontmatter
            ``description`` field if the role-defaults entry is missing/empty)
          * ``targets`` — list of delegation target role names from
            ``handoff.target_roles`` (or ``[]`` if not declared)
        """
        role_defaults_path = self._role_defaults_path()
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
                        description = self._read_template_description(name)
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
                    })
        return {"roles": roles, "count": len(roles)}

    def _role_defaults_path(self) -> Path:
        """Resolve the path to ``role-defaults.yaml`` for either layout."""
        return resolve_asset(self.__class__.root, "config", "role-defaults.yaml")

    def _read_pipelines(self) -> dict:
        """Return the ``quality_pipelines`` block from ``role-defaults.yaml``
        in a stable envelope shape: ``{"pipelines": {...}}``. Returns an empty
        dict if the file does not exist or the key is absent."""
        path = self._role_defaults_path()
        if not path.exists():
            return {"pipelines": {}}
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        pipelines = data.get("quality_pipelines") or {}
        if not isinstance(pipelines, dict):
            pipelines = {}
        return {"pipelines": pipelines}

    def _read_single_pipeline(self, name: str) -> dict:
        """Return a single pipeline by name or raise."""
        pipelines = self._read_pipelines().get("pipelines", {})
        if name not in pipelines:
            raise FileNotFoundError(f"pipeline not found: {name}")
        return {"pipeline": pipelines[name]}

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
        lines = AdminRequestHandler._indent_yaml_dump(item, value_indent)
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

    def _update_role_defaults_section(self, key: str, value: Any) -> dict:
        """Replace one top-level section of ``role-defaults.yaml`` in-place.

        Uses a fine-grained, child-aware edit so that untouched inner keys,
        list items, and comments keep their original formatting. Only new or
        changed children are re-serialised with PyYAML. Falls back to a full
        block dump when the section is missing or its structure is unexpected.
        Backup + atomic-replace rules mirror :class:`ConfigManager`.
        """
        import re

        path = self._role_defaults_path()
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
                "path": str(path.relative_to(self.root)),
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

        cm = self.__class__.config_manager
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
            "path": str(path.relative_to(self.root)),
            "backup": backup,
        }

    def _write_pipelines(self, pipelines: dict) -> dict:
        """Replace ONLY the ``quality_pipelines`` key in ``role-defaults.yaml``."""
        return self._update_role_defaults_section("quality_pipelines", pipelines)

    def _write_single_pipeline(self, name: str, pipeline: dict) -> dict:
        """Create or update a single pipeline by name."""
        all_pipelines = self._read_pipelines().get("pipelines", {})
        all_pipelines[name] = pipeline
        result = self._write_pipelines(all_pipelines)
        result["pipeline"] = pipeline
        result["name"] = name
        return result

    def _delete_pipeline(self, name: str) -> dict:
        """Delete a single pipeline by name."""
        all_pipelines = self._read_pipelines().get("pipelines", {})
        if name not in all_pipelines:
            raise FileNotFoundError(f"pipeline not found: {name}")
        del all_pipelines[name]
        result = self._write_pipelines(all_pipelines)
        result["deleted"] = name
        return result

    def _write_reflection_pairs(self, pairs: list) -> dict:
        """Replace ONLY the ``reflection_pairs`` key in ``role-defaults.yaml``."""
        result = self._update_role_defaults_section("reflection_pairs", pairs)
        result["reflection_pairs"] = pairs
        result["count"] = len(pairs)
        return result

    def _pipeline_help(self) -> dict:
        """Return comprehensive help documentation for the pipelines API."""
        pipeline_names = list(self._read_pipelines().get("pipelines", {}).keys())
        return {
            "help": {
                "title": "Quality Pipelines API",
                "version": self.__class__.version,
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

    def _read_reflection_pairs(self) -> dict:
        """Return the ``reflection_pairs`` block from ``role-defaults.yaml``.

        Envelope shape: ``{"reflection_pairs": [...]}``. The list is always
        returned (empty if absent).
        """
        path = self._role_defaults_path()
        if not path.exists():
            return {"reflection_pairs": []}
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        pairs = data.get("reflection_pairs") or []
        if not isinstance(pairs, list):
            pairs = []
        return {"reflection_pairs": pairs}

    def _read_reflection_pair(self, pair_id: str) -> dict:
        """Return a single reflection pair by ``id`` or raise."""
        for pair in self._read_reflection_pairs().get("reflection_pairs", []):
            if isinstance(pair, dict) and pair.get("id") == pair_id:
                return {"reflection_pair": pair}
        raise FileNotFoundError(f"reflection pair not found: {pair_id}")

    def _ensure_pair_id(self, pair: dict, pair_id: str | None = None) -> str:
        """Return a valid id for a reflection pair, generating one if missing."""
        if pair_id:
            pair["id"] = pair_id
            return pair_id
        if not pair.get("id"):
            existing = self._read_reflection_pairs().get("reflection_pairs", [])
            base = pair.get("generator", "pair") + "-" + pair.get("critic", "critic")
            idx = 1
            candidate = f"{base}-{idx}"
            old_ids = {p.get("id") for p in existing if isinstance(p, dict)}
            while candidate in old_ids:
                idx += 1
                candidate = f"{base}-{idx}"
            pair["id"] = candidate
        return pair["id"]

    def _write_reflection_pair(self, pair_id: str, pair: dict) -> dict:
        """Create or update a single reflection pair by id."""
        self._ensure_pair_id(pair, pair_id)
        pairs = self._read_reflection_pairs().get("reflection_pairs", [])
        found = False
        for i, existing in enumerate(pairs):
            if isinstance(existing, dict) and existing.get("id") == pair_id:
                pairs[i] = pair
                found = True
                break
        if not found:
            pairs.append(pair)
        result = self._write_reflection_pairs(pairs)
        result["reflection_pair"] = pair
        return result

    def _delete_reflection_pair(self, pair_id: str) -> dict:
        """Delete a single reflection pair by id."""
        pairs = self._read_reflection_pairs().get("reflection_pairs", [])
        new_pairs = [p for p in pairs if not (isinstance(p, dict) and p.get("id") == pair_id)]
        if len(new_pairs) == len(pairs):
            raise FileNotFoundError(f"reflection pair not found: {pair_id}")
        result = self._write_reflection_pairs(new_pairs)
        result["deleted"] = pair_id
        return result


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
            "agent-prompts", "model-overrides", "memory-overrides", "permission-mode-overrides",
            "steps-overrides", "dod", "rules", "roles", "orchestrator", "viz", "admin-ui",
            "provider-tier-overrides", "project", "dod-preset", "rules-preset", "speech-mode",
            "tier-preset", "se-focus", "ai-providers", "platforms", "provider-options",
            "provider-isolation", "environments", "model-source-preference", "knowledge-engine",
            "gitignore", "mcp-servers", "mcp-registry", "external-skills", "skills-registry",
        }
        if section not in allowed:
            raise ValueError(f"section not allowed: {section}")
        existing = self.__class__.config_manager.read("project")
        if not isinstance(existing, dict):
            existing = {}
        existing[section] = data
        return self._send_json(self.__class__.config_manager.write("project", existing))

    def _read_template_description(self, role: str) -> str:
        """Read the description from a generated agent template's frontmatter."""
        try:
            path = self._template_path(role)
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

    def _list_agent_templates(self) -> dict:
        """Return the list of agent templates available for generation.

        Searches the top-level ``agents/1-generic`` first and falls back to the
        submodule layout ``.agent-meta/agents/1-generic`` when agent-meta is
        embedded in a target project.
        """
        templates_dir = resolve_asset(self.__class__.root, "agents", "1-generic")
        if not templates_dir.is_dir():
            return {"templates": [], "available": False}
        names = sorted(
            p.stem for p in templates_dir.glob("*.md")
            if p.is_file() and not p.name.startswith("_")
        )
        return {"templates": names, "available": True}

    def _ai_providers_path(self) -> Path:
        """Resolve the path to ``config/ai-providers.yaml`` for either layout."""
        return resolve_asset(self.__class__.root, "config", "ai-providers.yaml")

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
        platform_dir = resolve_asset(self.__class__.root, "agents", "2-platform")
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
        hierarchy = self._build_agent_hierarchy()
        rolenames = sorted(
            (r.get("name") for r in hierarchy.get("roles") or [] if r.get("name")),
            key=str.lower,
        )
        return [{"name": n} for n in rolenames]

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

    def _run_consistency_check(self) -> dict:
        """Run the overall repository consistency check and return JSON."""
        import json
        import subprocess
        import sys
        try:
            r = subprocess.run(  # noqa: PLW1510
                [sys.executable, "scripts/consistency-check.py", "--json"], 
                cwd=str(self.__class__.root), 
                capture_output=True, 
                text=True
            )
            # consistency-check.py --json prints pure JSON to stdout regardless of exit code
            return json.loads(r.stdout)
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse JSON output",
                "output": r.stdout,
                "findings": [],
                "summary": {"total": 0, "errors": 0, "warnings": 0}
            }
        except Exception as e:  # noqa: BLE001
            return {
                "error": str(e),
                "findings": [],
                "summary": {"total": 0, "errors": 0, "warnings": 0}
            }

    def _run_config_audit(self) -> dict:
        """Run the consistency audit over the current configuration."""
        self._ensure_lib_on_path()
        import dataclasses

        from lib.config_audit import audit_config
        project_config_path = self.__class__.root / ".meta-config" / "project.yaml"
        report = audit_config(self.__class__.root, project_config_path)
        return {
            "has_issues": report.has_issues,
            "errors": [dataclasses.asdict(i) for i in report.errors],
            "warnings": [dataclasses.asdict(i) for i in report.warnings],
            "issues": [dataclasses.asdict(i) for i in report.issues],
        }

    def _apply_config_audit(self) -> dict:
        """Apply safe fixes reported by the consistency audit."""
        self._ensure_lib_on_path()
        from lib.config_audit import apply_audit, audit_config
        project_config_path = self.__class__.root / ".meta-config" / "project.yaml"
        report = audit_config(self.__class__.root, project_config_path)
        count = apply_audit(report, project_config_path)
        return {"fixed": count}

    def _send_template(self, role: str) -> None:
        """Send a generated agent template as plain text."""
        path = self._template_path(role)
        if not path.exists():
            raise FileNotFoundError(f"agent template not found: {role}")
        return self._send_bytes(path.read_bytes(), "text/markdown; charset=utf-8")

    def _write_template(self, role: str) -> None:
        """Write an agent template back to disk."""
        body = self._read_body()
        if body is None:
            raise ValueError("empty body")
        # Frontend sends JSON: {"content": "..."}. Accept the parsed dict and
        # extract the content field. A bare string body is tolerated for
        # backward compatibility with plain-text clients.
        if isinstance(body, dict):
            content = body.get("content")
        elif isinstance(body, str):
            content = body
        else:
            content = None
        if not isinstance(content, str):
            raise ValueError("expected 'content' field with template text")  # noqa: TRY004
        path = self._template_path(role)
        if not path:
            raise FileNotFoundError(f"template not found: {role}")
        cm = self.__class__.config_manager
        if path.exists():
            backup = cm._backup(path)
            cm._prune_backups(path)
        else:
            backup = None
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
        return self._send_json({
            "status": "saved",
            "role": role,
            "backup": backup,
            "bytes": len(content.encode("utf-8")),
        })

    def _template_path(self, role: str) -> Path | None:
        """Resolve the platform-specific template path for a role."""
        if not role or any(c in role for c in ("/", "\\", "..")):
            raise SecurityError(f"invalid role name: {role!r}")
        safe = "".join(ch for ch in role if ch.isalnum() or ch in ("-", "_"))
        if safe != role:
            raise SecurityError(f"invalid role name: {role!r}")
        candidate = self._agent_meta_root() / "agents" / "1-generic" / f"{role}.md"
        # Also check 2-platform for platform-specific overrides.
        for entry in (self._agent_meta_root() / "agents" / "2-platform").glob("*.md"):
            if entry.stem.endswith(f"-{role}"):
                return entry
        return candidate

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

    # ------------------------------------------------------------------ #
    # Provider deactivation handlers                                      #
    # ------------------------------------------------------------------ #

    def _get_deactivation_status(self) -> dict:
        """Return current provider deactivation status."""
        root = self.__class__.root
        try:
            sys.path.insert(0, str(root / "scripts"))
            sys.path.insert(0, str(root / ".agent-meta" / "scripts"))
            from lib.deactivation import get_deactivation_status  # type: ignore[import]
            from lib.providers import load_providers_config  # type: ignore[import]

            project_config = self.__class__.config_manager.read("project")
            provider_config = load_providers_config(root)
            return get_deactivation_status(root, project_config, provider_config)
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

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
        """Deactivate providers: zip and remove their directories."""
        root = self.__class__.root
        body = self._read_body() or {}
        providers = body.get("providers", [])
        if not isinstance(providers, list):
            providers = []

        try:
            sys.path.insert(0, str(root / "scripts"))
            sys.path.insert(0, str(root / ".agent-meta" / "scripts"))
            from lib.deactivation import (  # type: ignore[import]
                deactivate_providers,
                get_deactivation_status,
            )
            from lib.providers import load_providers_config  # type: ignore[import]

            project_config = self.__class__.config_manager.read("project")
            provider_config = load_providers_config(root)

            class _Log:
                def info(self, *a): pass
                def warn(self, *a): pass
                def error(self, *a): pass

            log = _Log()
            results = deactivate_providers(
                root, providers if providers else ["all"],
                provider_config, project_config, log, dry_run=False,
            )
            return self._send_json({
                "success": True,
                "results": results,
                "status": get_deactivation_status(root, project_config, provider_config),
            })
        except Exception as exc:  # noqa: BLE001
            return self._send_json({"error": str(exc)}, status=500)

    def _handle_activate_providers(self) -> None:
        """Activate providers: restore from backup zips."""
        root = self.__class__.root
        body = self._read_body() or {}
        providers = body.get("providers", [])
        if not isinstance(providers, list):
            providers = []

        try:
            sys.path.insert(0, str(root / "scripts"))
            sys.path.insert(0, str(root / ".agent-meta" / "scripts"))
            from lib.deactivation import (  # type: ignore[import]
                activate_providers,
                get_deactivation_status,
            )
            from lib.providers import load_providers_config  # type: ignore[import]

            project_config = self.__class__.config_manager.read("project")
            provider_config = load_providers_config(root)

            class _Log:
                def info(self, *a): pass
                def warn(self, *a): pass
                def error(self, *a): pass

            log = _Log()
            results = activate_providers(
                root, providers,
                provider_config, project_config, log, dry_run=False,
            )
            return self._send_json({
                "success": True,
                "results": results,
                "status": get_deactivation_status(root, project_config, provider_config),
            })
        except Exception as exc:  # noqa: BLE001
            return self._send_json({"error": str(exc)}, status=500)

    # ------------------------------------------------------------------ #
    # Backup handlers                                                    #
    # ------------------------------------------------------------------ #

    def _handle_get_backups(self) -> None:
        root = self.__class__.root
        try:
            sys.path.insert(0, str(root / "scripts"))
            sys.path.insert(0, str(root / ".agent-meta" / "scripts"))
            from lib.backup import list_backups  # type: ignore[import]
            from lib.providers import load_providers_config  # type: ignore[import]

            project_config = self.__class__.config_manager.read("project")
            provider_config = load_providers_config(root)
            return self._send_json(list_backups(root, project_config, provider_config))
        except Exception as exc:  # noqa: BLE001
            return self._send_json({"error": str(exc)}, status=500)

    def _handle_create_backup(self) -> None:
        root = self.__class__.root
        body = self._read_body() or {}
        providers = body.get("providers", None)
        label = body.get("label", None)
        
        try:
            sys.path.insert(0, str(root / "scripts"))
            sys.path.insert(0, str(root / ".agent-meta" / "scripts"))
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
            return self._send_json({"error": str(exc)}, status=500)

    def _handle_restore_backup(self) -> None:
        root = self.__class__.root
        body = self._read_body() or {}
        archive_name = body.get("archive_name")
        if not archive_name:
            return self._send_json({"error": "archive_name is required"}, status=400)
            
        providers = body.get("providers", None)
        force = body.get("force", False)

        try:
            sys.path.insert(0, str(root / "scripts"))
            sys.path.insert(0, str(root / ".agent-meta" / "scripts"))
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
            return self._send_json({"error": str(exc)}, status=500)

    def _handle_delete_backup(self, archive_name: str) -> None:
        root = self.__class__.root
        if not archive_name:
            return self._send_json({"error": "archive_name is required"}, status=400)

        try:
            sys.path.insert(0, str(root / "scripts"))
            sys.path.insert(0, str(root / ".agent-meta" / "scripts"))
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
            return self._send_json({"error": str(exc)}, status=500)


class _DaemonThreadingHTTPServer(ThreadingHTTPServer):
    """Threading HTTP server that marks request threads as daemons.

    Prevents long-lived SSE connections from blocking process shutdown after
    Ctrl+C — the daemon threads die automatically when the main thread exits.
    """

    daemon_threads = True


class AdminServer:
    """Container that owns the HTTP server and optional watcher thread."""

    def __init__(
        self,
        root: Path,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        enable_watcher: bool = False,
        enable_viz: bool = True,
    ) -> None:
        if host not in ALLOWED_HOSTS:
            raise ValueError(
                f"refusing to bind on non-loopback host {host!r}; "
                f"allowed: {', '.join(ALLOWED_HOSTS)}"
            )
        self.root = root.resolve()
        self.host = host
        self.port = port
        self.mode = detect_mode(self.root)
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

        self.httpd = _DaemonThreadingHTTPServer((self.host, self.port), AdminRequestHandler)

    def _read_version(self) -> str:
        # First try to read agent-meta-version from .meta-config/project.yaml
        config_path = self.root / ".meta-config" / "project.yaml"
        if config_path.exists():
            try:
                sys.path.insert(0, str(self.root / "scripts"))
                sys.path.insert(0, str(self.root / ".agent-meta" / "scripts"))
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
            # processes with their own PID-files. The user can stop them via
            # ``python scripts/viz-server.py stop`` or a subsequent
            # ``admin-server.py`` invocation with ``--stop-viz`` (future).


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #


def main() -> None:
    parser = argparse.ArgumentParser(
        description="agent-meta Admin UI Server (zero-dependency stdlib HTTP)",
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"Server port (default: {DEFAULT_PORT})")
    parser.add_argument("--host", default=DEFAULT_HOST, choices=list(ALLOWED_HOSTS),
                        help=f"Bind host -- loopback only (default: {DEFAULT_HOST})")
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

    server = AdminServer(
        root,
        host=args.host,
        port=args.port,
        enable_watcher=args.watch,
        enable_viz=not args.no_viz,
    )
    server.start()


if __name__ == "__main__":
    main()
