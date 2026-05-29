#!/usr/bin/env python3
"""
viz-server.py — Start/Stop/Toggle/Status für den agent-meta Viz- und MCP-Server
=================================================================================

Usage:
  python scripts/viz-server.py start      # Dashboard + MCP-Server starten
  python scripts/viz-server.py stop       # Beide Server beenden
  python scripts/viz-server.py status     # Status beider Server
  python scripts/viz-server.py restart    # Beide neustarten
  python scripts/viz-server.py toggle     # Umschalten
  python scripts/viz-server.py open       # Dashboard im Browser öffnen
  python scripts/viz-server.py mcp-only   # Nur MCP-Server starten (ohne Dashboard)

Konfiguration (.meta-config/project.yaml):

  viz:
    server:
      port: 8765          # Dashboard-Port
      timeout_sec: 300    # Auto-Shutdown nach Inaktivität
    mcp:
      port: 9090          # MCP-SSE-Port (opencode verbindet sich hierher)
"""

import sys
import os
import subprocess
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# --- Dashboard server ---
VIZ_REPORT = SCRIPT_DIR / "viz-report.py"
VIZ_PID_FILE = PROJECT_ROOT / ".meta-viz/.server-pid"
VIZ_LOG_FILE = PROJECT_ROOT / ".meta-viz/server.log"

# --- MCP server ---
VIZ_LOGGER = SCRIPT_DIR / "viz-logger.py"
MCP_PID_FILE = PROJECT_ROOT / ".meta-viz/.mcp-server-pid"
MCP_LOG_FILE = PROJECT_ROOT / ".meta-viz/mcp-server.log"

# --- Defaults ---
_DEFAULT_VIZ_PORT = 8765
_DEFAULT_VIZ_TIMEOUT = 300
_DEFAULT_MCP_PORT = 9090


def _load_server_config() -> dict:
    """Load viz config from project.yaml, returns dict with defaults."""
    config_path = PROJECT_ROOT / ".meta-config" / "project.yaml"
    try:
        sys.path.insert(0, str(SCRIPT_DIR))
        from lib.config import load_config
        config = load_config(config_path)
        viz_cfg = config.get("viz", {})
        server_cfg = viz_cfg.get("server", {})
        mcp_cfg = viz_cfg.get("mcp", {})
        return {
            "viz_port": int(server_cfg.get("port", _DEFAULT_VIZ_PORT)),
            "viz_timeout": int(server_cfg.get("timeout_sec", _DEFAULT_VIZ_TIMEOUT)),
            "mcp_port": int(mcp_cfg.get("port", _DEFAULT_MCP_PORT)),
        }
    except Exception:
        return {
            "viz_port": _DEFAULT_VIZ_PORT,
            "viz_timeout": _DEFAULT_VIZ_TIMEOUT,
            "mcp_port": _DEFAULT_MCP_PORT,
        }


def _is_process_running(pid: int) -> bool:
    if not pid:
        return False
    try:
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
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
            return int(pid_file.read_text().strip())
        except ValueError:
            pass
    return None


def _start_process(args: list[str], pid_file: Path, log_file: Path, label: str) -> bool:
    """Start a background process, write PID. Returns True on success."""
    pid_file.parent.mkdir(parents=True, exist_ok=True)

    # Rotate old log
    if log_file.exists():
        try:
            log_file.unlink()
        except PermissionError:
            pass

    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
        proc = subprocess.Popen(
            args,
            stdout=open(log_file, "a", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            startupinfo=si,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            cwd=str(PROJECT_ROOT),
        )
    else:
        proc = subprocess.Popen(
            args,
            stdout=open(log_file, "a", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
            cwd=str(PROJECT_ROOT),
        )

    pid_file.write_text(str(proc.pid))
    time.sleep(1.5)

    if _is_process_running(proc.pid):
        print(f"  + {label} gestartet. PID: {proc.pid}")
        return True
    else:
        print(f"  ! {label} konnte nicht gestartet werden. Siehe {log_file}")
        pid_file.unlink(missing_ok=True)
        return False


def _stop_process(pid_file: Path, label: str):
    pid = _read_pid(pid_file)
    if not pid:
        print(f"  - {label}: läuft nicht.")
        pid_file.unlink(missing_ok=True)
        return

    if not _is_process_running(pid):
        print(f"  - {label}: Prozess {pid} nicht mehr aktiv.")
        pid_file.unlink(missing_ok=True)
        return

    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=True, capture_output=True)
        else:
            os.kill(pid, 15)
            time.sleep(1)
            if _is_process_running(pid):
                os.kill(pid, 9)
        print(f"  - {label} beendet (PID: {pid}).")
    except Exception as e:
        print(f"  ! Fehler beim Beenden von {label}: {e}")
    finally:
        pid_file.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Dashboard server
# ---------------------------------------------------------------------------

def start_viz():
    cfg = _load_server_config()
    pid = _read_pid(VIZ_PID_FILE)
    if pid and _is_process_running(pid):
        print(f"  - Dashboard läuft bereits (PID: {pid}, Port: {cfg['viz_port']})")
        return
    _start_process(
        [sys.executable, str(VIZ_REPORT), "--serve", "--port", str(cfg["viz_port"]), "--timeout", str(cfg["viz_timeout"])],
        VIZ_PID_FILE, VIZ_LOG_FILE,
        f"Dashboard (Port {cfg['viz_port']})",
    )


def stop_viz():
    _stop_process(VIZ_PID_FILE, "Dashboard")


def viz_running() -> bool:
    pid = _read_pid(VIZ_PID_FILE)
    return bool(pid and _is_process_running(pid))


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

def start_mcp():
    cfg = _load_server_config()
    pid = _read_pid(MCP_PID_FILE)
    if pid and _is_process_running(pid):
        print(f"  - MCP-Server läuft bereits (PID: {pid}, Port: {cfg['mcp_port']})")
        return
    _start_process(
        [sys.executable, "-u", str(VIZ_LOGGER), "--http", str(cfg["mcp_port"])],
        MCP_PID_FILE, MCP_LOG_FILE,
        f"MCP-Server (Port {cfg['mcp_port']})",
    )


def stop_mcp():
    _stop_process(MCP_PID_FILE, "MCP-Server")


def mcp_running() -> bool:
    pid = _read_pid(MCP_PID_FILE)
    return bool(pid and _is_process_running(pid))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_start(mcp_only: bool = False):
    cfg = _load_server_config()
    if not mcp_only:
        start_viz()
    start_mcp()
    print()
    if not mcp_only:
        print(f"  Dashboard: http://localhost:{cfg['viz_port']}/")
    print(f"  MCP-SSE:   http://127.0.0.1:{cfg['mcp_port']}/sse")
    print(f"  Logs:      {PROJECT_ROOT / '.meta-viz'}")


def cmd_stop():
    stop_viz()
    stop_mcp()


def cmd_status():
    cfg = _load_server_config()
    viz = viz_running()
    mcp = mcp_running()

    print(f"  Dashboard  (Port {cfg['viz_port']}): {'LAUFT' if viz else 'GESTOPPT'}")
    if viz:
        print(f"    PID: {_read_pid(VIZ_PID_FILE)}  |  http://localhost:{cfg['viz_port']}/")

    print(f"  MCP-Server (Port {cfg['mcp_port']}): {'LAUFT' if mcp else 'GESTOPPT'}")
    if mcp:
        print(f"    PID: {_read_pid(MCP_PID_FILE)}  |  http://127.0.0.1:{cfg['mcp_port']}/sse")


def cmd_toggle():
    if viz_running() or mcp_running():
        print("  i  Server laufen — stoppe...")
        cmd_stop()
    else:
        print("  i  Server gestoppt — starte...")
        cmd_start()


def cmd_restart():
    cmd_stop()
    time.sleep(1)
    cmd_start()


def cmd_open():
    import webbrowser
    cfg = _load_server_config()
    webbrowser.open(f"http://localhost:{cfg['viz_port']}/")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()

    commands = {
        "start": lambda: cmd_start(),
        "mcp-only": lambda: cmd_start(mcp_only=True),
        "stop": cmd_stop,
        "status": cmd_status,
        "restart": cmd_restart,
        "toggle": cmd_toggle,
        "open": cmd_open,
    }

    handler = commands.get(cmd)
    if handler:
        handler()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
