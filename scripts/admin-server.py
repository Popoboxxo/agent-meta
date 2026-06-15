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

_DEFAULT_VIZ_PORT    = 8765
_DEFAULT_VIZ_TIMEOUT = 300
_DEFAULT_MCP_PORT    = 9090

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


def _load_viz_config(root: Path) -> dict:
    """Load viz server ports/timeouts from ``.meta-config/project.yaml``."""
    config_path = root / ".meta-config" / "project.yaml"
    try:
        sys.path.insert(0, str(root / "scripts"))
        sys.path.insert(0, str(root / ".agent-meta" / "scripts"))
        from lib.config import load_config  # type: ignore[import]
        config = load_config(config_path)
        viz_cfg = config.get("viz", {})
        server_cfg = viz_cfg.get("server", {})
        mcp_cfg = viz_cfg.get("mcp", {})
        return {
            "viz_port":    int(server_cfg.get("port", _DEFAULT_VIZ_PORT)),
            "viz_timeout": int(server_cfg.get("timeout_sec", _DEFAULT_VIZ_TIMEOUT)),
            "mcp_port":    int(mcp_cfg.get("port", _DEFAULT_MCP_PORT)),
        }
    except Exception:
        return {
            "viz_port":    _DEFAULT_VIZ_PORT,
            "viz_timeout": _DEFAULT_VIZ_TIMEOUT,
            "mcp_port":    _DEFAULT_MCP_PORT,
        }


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

    def status(self) -> dict:
        """Return a status dict for the ``/api/subserver-status`` endpoint."""
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
        except Exception as exc:  # pragma: no cover
            self._send_json({"error": "internal", "detail": str(exc)}, status=500)

    def do_POST(self) -> None:  # noqa: N802
        try:
            self._check_origin()
            self._dispatch_post()
        except SecurityError as exc:
            self._send_json({"error": "forbidden", "detail": str(exc)}, status=403)
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

        if path == "/api/integrations":
            return self._send_json(self._integrations_overview())

        raise FileNotFoundError(path)

    # ------------------------------------------------------------------ #
    # PUT routes                                                         #
    # ------------------------------------------------------------------ #

    def _dispatch_put(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

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

        if path.startswith("/api/integrations/") and path.endswith("/toggle"):
            name = path[len("/api/integrations/"):-len("/toggle")]
            body = self._read_body() or {}
            enabled = bool(body.get("enabled", False))
            return self._send_json(self._integrations_toggle(name, enabled))

        if path.startswith("/api/integrations/") and path.endswith("/init"):
            name = path[len("/api/integrations/"):-len("/init")]
            return self._send_json(self._integrations_init(name))

        raise FileNotFoundError(path)

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #

    def _serve_ui(self) -> None:
        ui_path = self.__class__.root / "docs" / "admin-ui.html"
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
    # Integrations API                                                   #
    # ------------------------------------------------------------------ #

    def _integrations_registry_path(self) -> Path:
        """Resolve the path to ``integrations-registry.yaml`` for either layout."""
        primary = self.__class__.root / "config" / "integrations-registry.yaml"
        if primary.exists():
            return primary
        return self.__class__.root / ".agent-meta" / "config" / "integrations-registry.yaml"

    def _integrations_init_script(self) -> Path:
        """Resolve the path to ``init-integrations.py`` for either layout."""
        primary = self.__class__.root / "scripts" / "init-integrations.py"
        if primary.exists():
            return primary
        return self.__class__.root / ".agent-meta" / "scripts" / "init-integrations.py"

    @staticmethod
    def _validate_integration_name(name: str) -> str:
        """Reject anything that is not a plain alphanumeric/-/_ identifier."""
        if not name or any(c in name for c in ("/", "\\", "..")):
            raise SecurityError(f"invalid integration name: {name!r}")
        safe = "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_"))
        if safe != name:
            raise SecurityError(f"invalid integration name: {name!r}")
        return name

    def _integrations_overview(self) -> dict:
        """Return the combined registry + project + state snapshot for the UI.

        Shape::

            {
                "integrations": [
                    {
                        "name": "semble",
                        "approved": true,
                        "enabled": false,
                        "description": "...",
                        "package": "semble==0.3.4",
                        "capabilities": ["code-search", ...],
                        "installer": "uv",
                        "docs_url": "...",
                        "state": {
                            "installed": true,
                            "initialized": false,
                            "indexed": false,
                            "installed_at": "...",
                        },
                        "pending_init": true,
                    },
                    ...
                ],
                "pending": ["semble", ...],   # from .claude/pending-integrations.json
                "project_yaml_path": "...",
            }
        """
        registry_path = self._integrations_registry_path()
        registry: dict = {}
        if registry_path.exists():
            try:
                with registry_path.open("r", encoding="utf-8") as fh:
                    raw = yaml.safe_load(fh) or {}
                registry = raw.get("integrations") or {}
                if not isinstance(registry, dict):
                    registry = {}
            except (OSError, yaml.YAMLError):
                registry = {}

        # Project-side enabled flags live in .meta-config/project.yaml.
        project_data = self.__class__.config_manager.read("project") or {}
        project_integrations = project_data.get("integrations") or {}
        if not isinstance(project_integrations, dict):
            project_integrations = {}

        # Installation/init state — written by init-integrations.py
        state_path = self.__class__.root / ".meta-config" / ".integrations-state.json"
        state_data: dict = {}
        if state_path.exists():
            try:
                state_data = json.loads(state_path.read_text(encoding="utf-8")) or {}
            except (OSError, json.JSONDecodeError):
                state_data = {}
        state_by_name = state_data.get("integrations") or {}
        if not isinstance(state_by_name, dict):
            state_by_name = {}

        # Pending-init marker (set by sync.py when an enabled integration has
        # not yet been initialized).
        pending_path = self.__class__.root / ".claude" / "pending-integrations.json"
        pending: list = []
        if pending_path.exists():
            try:
                marker = json.loads(pending_path.read_text(encoding="utf-8")) or {}
                if isinstance(marker, dict):
                    pending_raw = marker.get("pending") or []
                    if isinstance(pending_raw, list):
                        pending = [str(p) for p in pending_raw if isinstance(p, str)]
            except (OSError, json.JSONDecodeError):
                pending = []

        items: list[dict] = []
        for name, entry in registry.items():
            if not isinstance(entry, dict):
                continue
            user_cfg = project_integrations.get(name) or {}
            if not isinstance(user_cfg, dict):
                user_cfg = {}
            integ_state = state_by_name.get(name) or {}
            if not isinstance(integ_state, dict):
                integ_state = {}

            items.append({
                "name": name,
                "approved": bool(entry.get("approved")),
                "enabled": bool(user_cfg.get("enabled")),
                "description": str(entry.get("description") or ""),
                "package": str(entry.get("package") or ""),
                "capabilities": list(entry.get("capabilities") or []),
                "installer": str(entry.get("installer") or "pip"),
                "docs_url": str(entry.get("docs_url") or ""),
                "min_python": str(entry.get("min_python") or ""),
                "state": {
                    "installed": bool(integ_state.get("installed")),
                    "initialized": bool(integ_state.get("initialized")),
                    "indexed": bool(integ_state.get("indexed")),
                    "installed_at": integ_state.get("installed_at") or "",
                    "initialized_at": integ_state.get("initialized_at") or "",
                    "indexed_at": integ_state.get("indexed_at") or "",
                },
                "pending_init": name in pending,
            })

        items.sort(key=lambda d: d["name"])
        return {
            "integrations": items,
            "pending": pending,
            "registry_path": str(registry_path) if registry_path.exists() else "",
            "project_yaml_path": ".meta-config/project.yaml",
            "available": bool(registry),
        }

    def _integrations_toggle(self, name: str, enabled: bool) -> dict:
        """Set ``integrations.<name>.enabled`` in ``.meta-config/project.yaml``.

        Only the enabled flag is touched; all other keys (per-integration
        options like ``content``, ``top_k``) are preserved. After the YAML is
        rewritten, ``sync.py`` is run so MCP entries / rules get regenerated
        immediately.
        """
        name = self._validate_integration_name(name)

        # Verify the integration is known to the registry — silently allowing
        # arbitrary names would write garbage into project.yaml.
        registry_path = self._integrations_registry_path()
        if not registry_path.exists():
            return {
                "success": False,
                "error": "integrations-registry.yaml not found",
                "name": name,
            }
        try:
            with registry_path.open("r", encoding="utf-8") as fh:
                raw = yaml.safe_load(fh) or {}
        except (OSError, yaml.YAMLError) as exc:
            return {"success": False, "error": f"registry unreadable: {exc}", "name": name}
        registry = raw.get("integrations") or {}
        if not isinstance(registry, dict) or name not in registry:
            return {
                "success": False,
                "error": f"integration '{name}' not in registry",
                "name": name,
            }
        if not registry[name].get("approved"):
            return {
                "success": False,
                "error": f"integration '{name}' is not approved",
                "name": name,
            }

        # Read-modify-write project.yaml through ConfigManager so the regular
        # backup + atomic-replace contract applies.
        cm = self.__class__.config_manager
        project = cm.read("project")
        if not isinstance(project, dict):
            project = {}
        integrations = project.get("integrations")
        if not isinstance(integrations, dict):
            integrations = {}
            project["integrations"] = integrations
        existing = integrations.get(name)
        if not isinstance(existing, dict):
            existing = {}
        existing["enabled"] = bool(enabled)
        integrations[name] = existing
        write_result = cm.write("project", project)

        # Re-run sync so MCP entries / rules/integrations.md reflect the change.
        sync_result = self.__class__.sync_executor.run()

        return {
            "success": bool(sync_result.get("success")),
            "name": name,
            "enabled": bool(enabled),
            "write": write_result,
            "sync": sync_result,
        }

    def _integrations_init(self, name: str) -> dict:
        """Run ``init-integrations.py --yes`` and report the captured output.

        ``init-integrations.py`` does not support an explicit per-integration
        target on the command line — it works through everything currently
        enabled in ``project.yaml``. We surface the full output so the user
        can see what happened. We still pass ``name`` so the caller knows
        which trigger fired in the response payload.
        """
        name = self._validate_integration_name(name)
        script = self._integrations_init_script()
        if not script.exists():
            return {
                "success": False,
                "output": f"init-integrations.py not found at {script}",
                "returncode": -1,
                "name": name,
            }
        cmd = [sys.executable, str(script), "--yes"]
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.__class__.root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,
            )
            output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
            return {
                "success": proc.returncode == 0,
                "output": output,
                "returncode": proc.returncode,
                "command": " ".join(cmd),
                "name": name,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "init-integrations.py timed out (600s)",
                "returncode": -1,
                "name": name,
            }
        except Exception as exc:  # pragma: no cover
            return {
                "success": False,
                "output": f"init-integrations.py failed: {exc}",
                "returncode": -1,
                "name": name,
            }

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
        except (BrokenPipeError, ConnectionResetError):
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
        except (BrokenPipeError, ConnectionResetError):
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
