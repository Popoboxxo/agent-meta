#!/usr/bin/env python3
"""
agent-meta Admin UI Server
==========================
Zero-dependency HTTP server (Python stdlib + PyYAML) that exposes a visual
configuration surface for agent-meta. Serves a single-page web UI from
``docs/admin-ui.html`` and provides REST + SSE endpoints over the YAML/JSON
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
import sys
import subprocess
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Iterable, Optional
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
}


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
    except Exception:
        return _viz_defaults()


def _is_pid_running(pid: Optional[int]) -> bool:
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


def _read_pid(pid_file: Path) -> Optional[int]:
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
        primary  = self.root / "scripts" / name
        fallback = self.root / ".agent-meta" / "scripts" / name
        return primary if primary.exists() else fallback

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
                stdout=open(log_file, "a", encoding="utf-8"),
                stderr=subprocess.STDOUT,
                startupinfo=si,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                cwd=str(self.root),
            )
        else:
            proc = subprocess.Popen(
                args,
                stdout=open(log_file, "a", encoding="utf-8"),
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
        except Exception as exc:
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
        if self.mode == "super_admin":
            return {**PROJECT_FILES, **SUPER_ADMIN_FILES}
        return dict(PROJECT_FILES)

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
        path = self.resolve_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        backup_info: Optional[str] = None
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
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        candidate = self.root / "scripts" / "sync.py"
        if not candidate.exists():
            # Fallback for target repos that embed agent-meta as a submodule.
            candidate = self.root / ".agent-meta" / "scripts" / "sync.py"
        self.sync_script = candidate

    def _run(self, extra_args: list[str]) -> dict:
        if not self.sync_script.exists():
            return {
                "success": False,
                "output": f"sync.py not found at {self.sync_script}",
                "returncode": -1,
            }
        cmd = [sys.executable, str(self.sync_script), *extra_args]
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
            )
            output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
            return {
                "success": proc.returncode == 0,
                "output": output,
                "returncode": proc.returncode,
                "command": " ".join(cmd),
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "sync.py timed out (300s)", "returncode": -1}
        except Exception as exc:  # pragma: no cover
            return {"success": False, "output": f"sync.py failed: {exc}", "returncode": -1}

    def dry_run(self) -> dict:
        """Execute ``sync.py --validate``. The flag is used because ``--dry-run``
        in agent-meta still touches some artefacts; ``--validate`` is a pure
        read-only check that returns a diff-like report."""
        return self._run(["--validate"])

    def run(self) -> dict:
        """Execute a real ``sync.py`` run (no extra flags)."""
        return self._run([])


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

    def stop(self) -> None:
        self._stop_event.set()

    def _tracked_files(self) -> Iterable[Path]:
        for rel in {**PROJECT_FILES, **SUPER_ADMIN_FILES}.values():
            path = self.root / rel
            if path.exists():
                yield path

    def run(self) -> None:  # noqa: D401 - thread entry point
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
            self._events_path.parent.mkdir(parents=True, exist_ok=True)
            entry = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "type": event_type,
                "path": str(path.relative_to(self.root)),
            }
            with self._events_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:  # pragma: no cover - best effort
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
    viz_manager: "VizManager"
    mode: str
    root: Path
    version: str
    bind_host: str
    bind_port: int

    # ------------------------------------------------------------------ #
    # Logging                                                            #
    # ------------------------------------------------------------------ #

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
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

    def do_OPTIONS(self) -> None:  # noqa: N802 - http verb
        # No cross-origin access is permitted; respond with a minimal 204 and
        # no CORS headers so the browser will not consider this an allowed
        # cross-site preflight.
        self.send_response(204)
        self.send_header("Allow", "GET, PUT, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
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
        except Exception as exc:  # pragma: no cover
            self._send_json({"error": "internal", "detail": str(exc)}, status=500)

    def do_PUT(self) -> None:  # noqa: N802
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
        except Exception as exc:  # pragma: no cover
            self._send_json({"error": "internal", "detail": str(exc)}, status=500)

    def do_POST(self) -> None:  # noqa: N802
        try:
            self._check_origin()
            self._dispatch_post()
        except SecurityError as exc:
            self._send_json({"error": "forbidden", "detail": str(exc)}, status=403)
        except ConnectionError:
            # See ``do_GET`` — silently bail on dead client socket.
            return
        except Exception as exc:  # pragma: no cover
            self._send_json({"error": "internal", "detail": str(exc)}, status=500)

    # ------------------------------------------------------------------ #
    # GET routes                                                         #
    # ------------------------------------------------------------------ #

    def _dispatch_get(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/":
            return self._serve_ui()

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

        if path == "/api/agents/hierarchy":
            return self._send_json(self._build_agent_hierarchy())

        if path == "/api/pipelines":
            return self._send_json(self._read_pipelines())

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

        if path == "/api/models":
            return self._handle_get_models()

        if path == "/api/models/active":
            return self._handle_get_models_active()

        if path == "/api/ai-providers":
            return self._handle_get_ai_providers()

        if path == "/api/tier-presets":
            return self._handle_get_tier_presets()

        if path == "/api/tier-presets/merged":
            return self._handle_get_tier_presets_merged()

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
        if path == "/api/config/project/section":
            return self._write_project_section()

        if path.startswith("/api/config/"):
            key = path[len("/api/config/"):]
            body = self._read_body()
            if body is None:
                raise ValueError("empty body")
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

        # Individual subserver control: /api/subserver/{name}/{action}
        # name in {viz, mcp}, action in {start, stop, restart}.
        subserver = self._match_subserver_route(path)
        if subserver is not None:
            name, action = subserver
            return self._handle_subserver_action(name, action)

        raise FileNotFoundError(path)

    @staticmethod
    def _match_subserver_route(path: str) -> Optional[tuple[str, str]]:
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
        root = self.__class__.root
        if (root / "config").exists():
            return root
        if (root / ".agent-meta" / "config").exists():
            return root / ".agent-meta"
        return root

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
        registry_path = self.__class__.root / "config" / "generated" / "model-registry.json"
        pricing_path = self.__class__.root / "config" / "pricing-overlay.yaml"
        if not registry_path.exists():
            fallback_registry = (
                self.__class__.root / ".agent-meta" / "config" / "generated" / "model-registry.json"
            )
            if fallback_registry.exists():
                registry_path = fallback_registry
                pricing_path = (
                    self.__class__.root / ".agent-meta" / "config" / "pricing-overlay.yaml"
                )

        models: list[dict] = []
        if registry_path.exists():
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
        except Exception as exc:
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
        except Exception as exc:
            return self._send_json({"error": str(exc)}, status=500)

    def _handle_post_models_update(self) -> None:
        """Trigger sync.py --update-models"""
        try:
            res = self.__class__.sync_executor._run(["--update-models"])
            return self._send_json(res)
        except Exception as exc:
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
            raise ValueError("body must be a JSON object with 'ids' field")
        ids = data.get("ids")
        if not isinstance(ids, list):
            raise ValueError("'ids' must be a list of strings")
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
        except Exception as exc:
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
        except Exception as exc:
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
        except Exception as exc:
            return self._send_json({"error": str(exc)}, status=500)

    def _handle_post_pricing_update(self) -> None:
        """Update pricing-overlay.yaml with new prices from UI."""
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length <= 0:
                return self._send_json({"error": "Empty body"}, status=400)
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
            
            pricing_path = self.__class__.root / "config" / "pricing-overlay.yaml"
            if not (self.__class__.root / "config").exists():
                pricing_path = self.__class__.root / ".agent-meta" / "config" / "pricing-overlay.yaml"
                
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
        except Exception as exc:
            return self._send_json({"error": str(exc)}, status=500)

    def _handle_post_pricing_reset(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length <= 0:
                return self._send_json({"error": "Empty body"}, status=400)
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            
            pricing_path = self.__class__.root / "config" / "pricing-overlay.yaml"
            if not (self.__class__.root / "config").exists():
                pricing_path = self.__class__.root / ".agent-meta" / "config" / "pricing-overlay.yaml"
                
            if pricing_path.exists():
                pricing = yaml.safe_load(pricing_path.read_text(encoding="utf-8")) or {}
                if "prices" in pricing:
                    provider = data.get("provider")
                    model_id = data.get("id")
                    if provider in pricing["prices"] and model_id in pricing["prices"][provider]:
                        del pricing["prices"][provider][model_id]
                        if not pricing["prices"][provider] and "_url" not in pricing["prices"][provider]:
                             # Maybe don't delete empty providers to be safe, but they have _url usually
                             pass
                        with pricing_path.open("w", encoding="utf-8") as fh:
                            yaml.dump(pricing, fh, default_flow_style=False, sort_keys=False)
                            
            return self._send_json({"success": True})
        except Exception as exc:
            return self._send_json({"error": str(exc)}, status=500)

    def _handle_get_ai_providers(self) -> None:
        try:
            path = self.__class__.root / "config" / "ai-providers.yaml"
            if not (self.__class__.root / "config").exists():
                path = self.__class__.root / ".agent-meta" / "config" / "ai-providers.yaml"
            data = {}
            if path.exists():
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return self._send_json(data)
        except Exception as exc:
            return self._send_json({"error": str(exc)}, status=500)

    def _handle_post_ai_providers_update(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}
            path = self.__class__.root / "config" / "ai-providers.yaml"
            if not (self.__class__.root / "config").exists():
                path = self.__class__.root / ".agent-meta" / "config" / "ai-providers.yaml"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as fh:
                yaml.dump(data, fh, default_flow_style=False, sort_keys=False)
            return self._send_json({"success": True})
        except Exception as exc:
            return self._send_json({"error": str(exc)}, status=500)

    def _handle_get_tier_presets(self) -> None:
        try:
            path = self.__class__.root / "config" / "tier-presets.yaml"
            if not (self.__class__.root / "config").exists():
                path = self.__class__.root / ".agent-meta" / "config" / "tier-presets.yaml"
            data = {}
            if path.exists():
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return self._send_json(data)
        except Exception as exc:
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
            global_path = self.__class__.root / "config" / "tier-presets.yaml"
            if not (self.__class__.root / "config").exists():
                global_path = self.__class__.root / ".agent-meta" / "config" / "tier-presets.yaml"
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
            except Exception:
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
        except Exception as exc:
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
            path = self.__class__.root / "config" / "tier-presets.yaml"
            if not (self.__class__.root / "config").exists():
                path = self.__class__.root / ".agent-meta" / "config" / "tier-presets.yaml"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as fh:
                yaml.dump(data, fh, default_flow_style=False, sort_keys=False)
            return self._send_json({"success": True})
        except Exception as exc:
            return self._send_json({"error": str(exc)}, status=500)

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #

    def _serve_ui(self) -> None:
        primary  = self.root / "docs" / "admin-ui.html"
        fallback = self.root / ".agent-meta" / "docs" / "admin-ui.html"
        ui_path = primary if primary.exists() else fallback
        if not ui_path.exists():
            raise FileNotFoundError("docs/admin-ui.html (UI bundle missing)")
        self._send_bytes(ui_path.read_bytes(), "text/html; charset=utf-8")

    def _find_schema_path(self) -> Path:
        candidates = [
            self.__class__.root / "config" / "project-config.schema.json",
            self.__class__.root / ".agent-meta" / "config" / "project-config.schema.json",
        ]
        for c in candidates:
            if c.exists():
                return c
        return candidates[0]

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
        primary = self.__class__.root / "config" / "role-defaults.yaml"
        if primary.exists():
            return primary
        return self.__class__.root / ".agent-meta" / "config" / "role-defaults.yaml"

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

    def _write_pipelines(self, pipelines: dict) -> dict:
        """Replace ONLY the ``quality_pipelines`` key in ``role-defaults.yaml``.

        All other top-level keys (``roles``, ``outcome-caching``,
        ``reflection_pairs`` …) are preserved untouched. Goes through the
        ConfigManager so the regular backup + atomic-replace contract applies.
        """
        cm = self.__class__.config_manager
        # ``role-defaults`` is the whitelisted key — never accept a raw path.
        existing = cm.read("role-defaults")
        if not isinstance(existing, dict):
            existing = {}
        existing["quality_pipelines"] = pipelines
        return cm.write("role-defaults", existing)

    @staticmethod
    def _deep_merge(base: dict, overlay: dict) -> dict:
        """Recursively merge ``overlay`` into ``base`` and return ``base``.

        Nested dicts are merged key-by-key; every other value type (scalars,
        lists) is replaced wholesale. Mutates and returns ``base``.
        """
        for key, value in overlay.items():
            if (
                key in base
                and isinstance(base[key], dict)
                and isinstance(value, dict)
            ):
                AdminRequestHandler._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def _write_project_section(self) -> None:
        """Apply a partial update to a single top-level section of
        ``project.yaml`` using a read-modify-write deep merge.

        Body shape: ``{"key": "<top-level-yaml-key>", "value": <section-data>}``.
        The remaining top-level keys are preserved untouched. Goes through the
        whitelisted ``project`` config key so backup + atomic-replace apply.
        """
        body = self._read_body()
        if not isinstance(body, dict) or "key" not in body or "value" not in body:
            raise ValueError("expected JSON body with 'key' and 'value' fields")
        key = body["key"]
        value = body["value"]
        if not isinstance(key, str) or not key:
            raise ValueError("'key' must be a non-empty string")

        existing = self.__class__.config_manager.read("project")
        if not isinstance(existing, dict):
            existing = {}
        if isinstance(existing.get(key), dict) and isinstance(value, dict):
            self._deep_merge(existing[key], value)
        else:
            existing[key] = value
        result = self.__class__.config_manager.write("project", existing)
        return self._send_json(result)

    def _read_template_description(self, role: str) -> str:
        """Read the ``description:`` field from a generic agent template's
        YAML frontmatter (if available). Used as a fallback when the role in
        ``role-defaults.yaml`` does not carry a description of its own.
        """
        try:
            path = self._template_path(role)
        except SecurityError:
            return ""
        if not path.exists():
            return ""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return ""
        if not text.startswith("---"):
            return ""
        # Parse only the YAML frontmatter block (between leading ``---`` and
        # the next ``---``). Avoids pulling in the entire template body.
        end = text.find("\n---", 3)
        if end == -1:
            return ""
        try:
            front = yaml.safe_load(text[3:end]) or {}
        except yaml.YAMLError:
            return ""
        if isinstance(front, dict):
            desc = front.get("description")
            if isinstance(desc, str):
                return desc.strip()
        return ""

    def _list_agent_templates(self) -> dict:
        templates_dir = self.__class__.root / "agents" / "1-generic"
        if not templates_dir.is_dir():
            return {"templates": [], "available": False}
        names = sorted(p.stem for p in templates_dir.glob("*.md") if p.is_file())
        return {"templates": names, "available": True}

    def _ai_providers_path(self) -> Path:
        """Resolve the path to ``ai-providers.yaml`` for either layout."""
        primary = self.__class__.root / "config" / "ai-providers.yaml"
        if primary.exists():
            return primary
        return self.__class__.root / ".agent-meta" / "config" / "ai-providers.yaml"

    def _list_providers(self) -> list[dict]:
        """Return the configured AI providers with their model tiers/aliases.

        Each entry exposes:
          * ``name`` — provider key (e.g. ``Claude``)
          * ``has_model_tiers`` — ``True`` if the provider declares any model
            tiers (providers like Continue/Copilot manage models centrally and
            report ``False``)
          * ``model_tiers`` — mapping of tier name → concrete model ID
          * ``model_aliases`` — mapping of alias name → concrete model ID

        Sorted alphabetically by provider name. Returns ``[]`` if the file is
        absent (project-admin mode without super-admin configs).
        """
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
        """Return distinct platform prefixes derived from ``agents/2-platform/``.

        Filenames follow the ``<prefix>-<role>.md`` convention. Roles can
        themselves contain hyphens (e.g. ``claude-expert``), so the prefix is
        resolved by stripping the longest known role name from the end of the
        filename stem. If no known role matches, fall back to everything before
        the last ``-``. ``agent-meta`` and ``generic`` are always included.
        Sorted alphabetically.
        """
        names: set[str] = {"agent-meta", "generic"}
        # Known role names (longest first) so multi-segment roles strip cleanly.
        known_roles = sorted(
            (r["name"] for r in self._list_roles()),
            key=len,
            reverse=True,
        )
        platform_dir = self.__class__.root / "agents" / "2-platform"
        if not platform_dir.is_dir():
            platform_dir = self.__class__.root / ".agent-meta" / "agents" / "2-platform"
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
        """Return the role names declared in ``role-defaults.yaml``.

        Reuses :meth:`_build_agent_hierarchy` so the role list stays consistent
        with the delegation graph. Sorted alphabetically.
        """
        hierarchy = self._build_agent_hierarchy()
        roles = hierarchy.get("roles") or []
        names = sorted((r.get("name") for r in roles if r.get("name")), key=str.lower)
        return [{"name": n} for n in names]

    # ------------------------------------------------------------------ #
    # Config audit                                                       #
    # ------------------------------------------------------------------ #

    def _audit_paths(self) -> tuple[Path, Path]:
        """Return ``(agent_meta_root, project_config_path)`` for the audit.

        In project-admin mode the agent-meta sources live under
        ``<root>/.agent-meta/`` — fall back to that layout when the top-level
        ``agents/`` directory is missing. The project config is always
        ``<root>/.meta-config/project.yaml``.
        """
        root = self.__class__.root
        agents_top = root / "agents" / "1-generic"
        if agents_top.exists():
            meta_root = root
        else:
            submodule_root = root / ".agent-meta"
            if (submodule_root / "agents" / "1-generic").exists():
                meta_root = submodule_root
            else:
                meta_root = root
        project_config = root / ".meta-config" / "project.yaml"
        return meta_root, project_config

    def _ensure_lib_on_path(self) -> None:
        """Make sure ``lib.config_audit`` is importable in both layouts."""
        root = self.__class__.root
        for candidate in (root / "scripts", root / ".agent-meta" / "scripts"):
            if candidate.exists() and str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))

    def _run_config_audit(self) -> dict:
        """Execute a read-only config audit and return a JSON-friendly dict."""
        self._ensure_lib_on_path()
        try:
            from lib.config_audit import audit_config, report_to_dict
        except ImportError as exc:
            raise FileNotFoundError(f"config_audit module unavailable: {exc}")
        meta_root, project_config = self._audit_paths()
        if not project_config.exists():
            raise FileNotFoundError(f"project config not found: {project_config}")
        report = audit_config(meta_root, project_config)
        return report_to_dict(report)

    def _apply_config_audit(self) -> dict:
        """Apply the auto-fix step: comment out deprecated roles in project.yaml.

        Creates a timestamped backup beforehand to allow recovery and returns
        the number of modified lines plus the resulting issue list.
        """
        self._ensure_lib_on_path()
        try:
            from lib.config_audit import audit_config, apply_audit, report_to_dict
        except ImportError as exc:
            raise FileNotFoundError(f"config_audit module unavailable: {exc}")
        meta_root, project_config = self._audit_paths()
        if not project_config.exists():
            raise FileNotFoundError(f"project config not found: {project_config}")
        # Backup via the existing ConfigManager so the file rotation policy
        # (timestamped ``.bak.<stamp>``, ``MAX_BACKUPS`` retention) stays
        # consistent with regular PUT writes.
        cm = self.__class__.config_manager
        try:
            cm._backup(project_config)  # type: ignore[attr-defined]
            cm._prune_backups(project_config)  # type: ignore[attr-defined]
        except Exception:
            # The backup is best-effort — never block the apply step.
            pass
        report = audit_config(meta_root, project_config)
        changed = apply_audit(report, project_config)
        # Re-audit after apply so the UI immediately reflects the new state.
        report_after = audit_config(meta_root, project_config)
        result = report_to_dict(report_after)
        result["changed"] = changed
        return result

    def _send_template(self, role: str) -> None:
        path = self._template_path(role)
        if not path.exists():
            raise FileNotFoundError(f"agent template not found: {role}")
        self._send_text(path.read_text(encoding="utf-8"), content_type="text/markdown; charset=utf-8")

    def _write_template(self, role: str) -> None:
        if self.__class__.mode != "super_admin":
            raise SecurityError("agent templates are read-only in project_admin mode")
        body = self._read_body()
        if not isinstance(body, dict) or "content" not in body:
            raise ValueError("expected JSON body with 'content' field")
        content = body["content"]
        if not isinstance(content, str):
            raise ValueError("'content' must be a string")
        path = self._template_path(role)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
        self._send_json({"status": "saved", "role": role, "bytes": len(content)})

    def _template_path(self, role: str) -> Path:
        if not role or any(c in role for c in ("/", "\\", "..")):
            raise SecurityError(f"invalid role name: {role!r}")
        safe = "".join(ch for ch in role if ch.isalnum() or ch in ("-", "_"))
        if safe != role:
            raise SecurityError(f"invalid role name: {role!r}")
        return self.__class__.root / "agents" / "1-generic" / f"{role}.md"

    # ------------------------------------------------------------------ #
    # Server-Sent Events                                                 #
    # ------------------------------------------------------------------ #

    def _stream_events(self) -> None:
        events_path = self.__class__.root / ".meta-viz" / "events.jsonl"
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        try:
            self.wfile.write(b": stream-open\n\n")
            self.wfile.flush()
        except ConnectionError:
            # ConnectionError is the base class covering BrokenPipeError,
            # ConnectionResetError, ConnectionAbortedError (Windows WinError
            # 10053) and platform-specific variants. Client disconnected
            # before the stream even opened — nothing to do.
            return

        offset = events_path.stat().st_size if events_path.exists() else 0
        last_heartbeat = time.time()

        try:
            while True:
                if events_path.exists() and events_path.stat().st_size > offset:
                    with events_path.open("r", encoding="utf-8") as fh:
                        fh.seek(offset)
                        for line in fh:
                            line = line.strip()
                            if line:
                                self.wfile.write(f"data: {line}\n\n".encode("utf-8"))
                        offset = fh.tell()
                    self.wfile.flush()
                if time.time() - last_heartbeat > SSE_HEARTBEAT_SECONDS:
                    self.wfile.write(b": heartbeat\n\n")
                    self.wfile.flush()
                    last_heartbeat = time.time()
                time.sleep(1.0)
        except ConnectionError:
            # ConnectionError is the base class covering BrokenPipeError,
            # ConnectionResetError, ConnectionAbortedError (Windows WinError
            # 10053) and platform-specific variants. Normal client disconnect.
            return


# --------------------------------------------------------------------------- #
# Server bootstrap                                                            #
# --------------------------------------------------------------------------- #


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
        self.watcher: Optional[ConfigWatcher] = None
        self.enable_watcher = enable_watcher
        self.enable_viz = enable_viz
        self.viz_manager = VizManager(self.root)

        AdminRequestHandler.config_manager = ConfigManager(self.root, self.mode)
        AdminRequestHandler.sync_executor = SyncExecutor(self.root)
        AdminRequestHandler.viz_manager = self.viz_manager
        AdminRequestHandler.mode = self.mode
        AdminRequestHandler.root = self.root
        AdminRequestHandler.version = self._read_version()
        AdminRequestHandler.bind_host = self.host
        AdminRequestHandler.bind_port = self.port

        self.httpd = _DaemonThreadingHTTPServer((self.host, self.port), AdminRequestHandler)

    def _read_version(self) -> str:
        version_file = self.root / "VERSION"
        if version_file.exists():
            return version_file.read_text(encoding="utf-8").strip()
        # Fallback for submodule layout
        submodule_version = self.root / ".agent-meta" / "VERSION"
        if submodule_version.exists():
            return submodule_version.read_text(encoding="utf-8").strip()
        return "unknown"

    def start(self) -> None:
        """Run the server (blocking). Honours ``Ctrl+C``."""
        if self.enable_watcher:
            self.watcher = ConfigWatcher(self.root)
            self.watcher.start()

        # Start Viz dashboard + MCP server as supervised subprocesses.
        if self.enable_viz:
            self.viz_manager.start_all()

        print(f"  i  agent-meta Admin UI")
        print(f"  i  Mode:    {self.mode}")
        print(f"  i  Version: {AdminRequestHandler.version}")
        print(f"  i  URL:     http://{self.host}:{self.port}")
        print(f"  i  Root:    {self.root}")
        if self.enable_watcher:
            print(f"  i  Watcher: enabled (.meta-viz/events.jsonl)")
        if not self.enable_viz:
            print(f"  i  Viz/MCP: disabled (--no-viz)")
        print(f"  i  Press Ctrl+C to stop")
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
