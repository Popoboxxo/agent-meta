#!/usr/bin/env python3
"""
viz-server.py — Thin backward-compatibility wrapper for agent-meta Admin UI
=============================================================================

This script forwards all commands to ``admin-server.py``, which is now the
unified entry-point for Admin UI, Viz dashboard and MCP SSE server.

Usage (legacy — all commands still work):
  python scripts/viz-server.py start      # Start all servers via admin-server.py
  python scripts/viz-server.py stop       # Stop Viz dashboard + MCP server
  python scripts/viz-server.py status     # Show status of all servers
  python scripts/viz-server.py restart    # Restart all servers
  python scripts/viz-server.py toggle     # Toggle start/stop
  python scripts/viz-server.py open       # Open Viz dashboard in browser
  python scripts/viz-server.py mcp-only   # Start MCP server only

Migration note:
  The preferred way to start all servers is now:
    python scripts/admin-server.py          (Admin UI + Viz + MCP)
    python scripts/admin-server.py --no-viz (Admin UI only)

  This wrapper is kept for backward compatibility with existing scripts,
  documentation and muscle memory. It will not be removed.
"""

import sys
import time
import webbrowser
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# ---------------------------------------------------------------------------
# Locate the VizManager helpers from admin-server module
# ---------------------------------------------------------------------------
# We import the shared helpers directly from admin-server.py rather than
# duplicating them — single source of truth for PID-file paths and process
# management logic.

# The module file is ``admin-server.py`` (hyphenated), which is not a valid
# Python identifier and therefore cannot be imported with a plain ``import``
# statement. Load it dynamically via importlib instead.
import importlib.util

_ADMIN_SERVER_PATH = SCRIPT_DIR / "admin-server.py"
try:
    _spec = importlib.util.spec_from_file_location("admin_server", _ADMIN_SERVER_PATH)
    if _spec is None or _spec.loader is None:
        raise ImportError(f"Cannot create module spec for {_ADMIN_SERVER_PATH}")
    _admin_module = importlib.util.module_from_spec(_spec)
    sys.modules["admin_server"] = _admin_module
    _spec.loader.exec_module(_admin_module)

    VizManager = _admin_module.VizManager
    _load_viz_config = _admin_module._load_viz_config
    _read_pid = _admin_module._read_pid
    _is_pid_running = _admin_module._is_pid_running
    VIZ_PID_FILE = _admin_module.VIZ_PID_FILE
    MCP_PID_FILE = _admin_module.MCP_PID_FILE
    _IMPORT_OK = True
except Exception:  # noqa: BLE001
    _IMPORT_OK = False


def _get_viz_manager() -> "VizManager":
    if not _IMPORT_OK:
        print("  !  Could not import admin-server.py helpers. Is the file present?",
              file=sys.stderr)
        sys.exit(1)
    return VizManager(PROJECT_ROOT)


def cmd_start(mcp_only: bool = False) -> None:
    mgr = _get_viz_manager()
    cfg = _load_viz_config(PROJECT_ROOT)
    if mcp_only:
        # Only start MCP by using a temp VizManager that skips viz
        mcp_pid = PROJECT_ROOT / MCP_PID_FILE
        mcp_log = PROJECT_ROOT / ".meta-viz" / "mcp-server.log"
        if not _is_pid_running(_read_pid(mcp_pid)):
            mgr._start(
                [sys.executable, "-u", str(mgr._viz_logger), "--http", str(cfg["mcp_port"])],
                mcp_pid, mcp_log,
                f"MCP server (port {cfg['mcp_port']})",
            )
        else:
            print(f"  -  MCP server already running (PID: {_read_pid(mcp_pid)})")
    else:
        mgr.start_all()
    print()
    if not mcp_only:
        print(f"  Viz dashboard:  http://localhost:{cfg['viz_port']}/")
    print(f"  MCP SSE:        http://127.0.0.1:{cfg['mcp_port']}/sse")
    print("  Admin UI:       http://127.0.0.1:7420/")
    print(f"  Logs:           {PROJECT_ROOT / '.meta-viz'}")


def cmd_stop() -> None:
    _get_viz_manager().stop_all()


def cmd_status() -> None:
    if not _IMPORT_OK:
        print("  !  Could not import admin-server.py helpers.", file=sys.stderr)
        sys.exit(1)
    status = _get_viz_manager().status()
    viz = status["viz"]
    mcp = status["mcp"]

    print(f"  Viz dashboard (port {viz['port']}): {'RUNNING' if viz['running'] else 'STOPPED'}")
    if viz["running"]:
        print(f"    PID: {viz['pid']}  |  {viz['url']}")
    print(f"  MCP server    (port {mcp['port']}): {'RUNNING' if mcp['running'] else 'STOPPED'}")
    if mcp["running"]:
        print(f"    PID: {mcp['pid']}  |  {mcp['url']}")


def cmd_toggle() -> None:
    if not _IMPORT_OK:
        print("  !  Could not import admin-server.py helpers.", file=sys.stderr)
        sys.exit(1)
    status = _get_viz_manager().status()
    if status["viz"]["running"] or status["mcp"]["running"]:
        print("  i  Servers running — stopping...")
        cmd_stop()
    else:
        print("  i  Servers stopped — starting...")
        cmd_start()


def cmd_restart() -> None:
    cmd_stop()
    time.sleep(1)
    cmd_start()


def cmd_open() -> None:
    if not _IMPORT_OK:
        print("  !  Could not import admin-server.py helpers.", file=sys.stderr)
        sys.exit(1)
    cfg = _load_viz_config(PROJECT_ROOT)
    webbrowser.open(f"http://localhost:{cfg['viz_port']}/")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()

    commands = {
        "start":    lambda: cmd_start(),
        "mcp-only": lambda: cmd_start(mcp_only=True),
        "stop":     cmd_stop,
        "status":   cmd_status,
        "restart":  cmd_restart,
        "toggle":   cmd_toggle,
        "open":     cmd_open,
    }

    handler = commands.get(cmd)
    if handler:
        handler()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
