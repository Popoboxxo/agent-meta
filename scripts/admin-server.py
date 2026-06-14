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
  python scripts/admin-server.py
  python scripts/admin-server.py --port 7420 --root .
  python scripts/sync.py --admin            (after a normal sync)
  python scripts/sync.py --admin-only       (skip sync)
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
            return self._send_json({
                "mode": self.__class__.mode,
                "root": str(self.__class__.root),
                "allowed_keys": sorted(self.__class__.config_manager._allowed_keys().keys()),
            })

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

        if path == "/api/agents/templates":
            return self._send_json(self._list_agent_templates())

        if path.startswith("/api/agent-template/"):
            role = path[len("/api/agent-template/"):]
            return self._send_template(role)

        if path == "/api/events":
            return self._stream_events()

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
        is missing (project-admin mode without super-admin configs)."""
        role_defaults_path = self.__class__.root / "config" / "role-defaults.yaml"
        if not role_defaults_path.exists():
            role_defaults_path = self.__class__.root / ".agent-meta" / "config" / "role-defaults.yaml"

        roles: list[dict] = []
        if role_defaults_path.exists():
            with role_defaults_path.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
            raw = data.get("roles") or data
            if isinstance(raw, dict):
                for name, attrs in raw.items():
                    if not isinstance(attrs, dict):
                        continue
                    roles.append({
                        "name": name,
                        "tier": attrs.get("tier") or attrs.get("workflow-tier") or "optional",
                        "model": attrs.get("model"),
                        "memory": attrs.get("memory"),
                        "parallel": bool(attrs.get("parallel", False)),
                        "permission_mode": attrs.get("permissionMode"),
                        "description": attrs.get("description", ""),
                    })
        return {"roles": roles, "count": len(roles)}

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

        AdminRequestHandler.config_manager = ConfigManager(self.root, self.mode)
        AdminRequestHandler.sync_executor = SyncExecutor(self.root)
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

        print(f"  i  agent-meta Admin UI")
        print(f"  i  Mode:    {self.mode}")
        print(f"  i  Version: {AdminRequestHandler.version}")
        print(f"  i  URL:     http://{self.host}:{self.port}")
        print(f"  i  Root:    {self.root}")
        if self.enable_watcher:
            print(f"  i  Watcher: enabled (.meta-viz/events.jsonl)")
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
                        help=f"Bind host — loopback only (default: {DEFAULT_HOST})")
    parser.add_argument("--root", default=".",
                        help="Project root directory (default: current directory)")
    parser.add_argument("--watch", action="store_true",
                        help="Enable filesystem watcher (polls config files every 2s)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"  !  root directory does not exist: {root}", file=sys.stderr)
        sys.exit(1)

    server = AdminServer(root, host=args.host, port=args.port, enable_watcher=args.watch)
    server.start()


if __name__ == "__main__":
    main()
