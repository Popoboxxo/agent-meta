#!/usr/bin/env python3
"""
viz-server.py — Start/Stop/Toggle/Status für den agent-meta Viz-Server
=====================================================================

Usage:
  python scripts/viz-server.py toggle     # Starten falls gestoppt, stoppen falls gestartet
  python scripts/viz-server.py start      # Server im Hintergrund starten
  python scripts/viz-server.py stop       # Server beenden
  python scripts/viz-server.py status     # Status prüfen
  python scripts/viz-server.py restart    # Neustarten
  python scripts/viz-server.py open       # Dashboard im Browser öffnen

Auto-Shutdown:
  Der Server beendet sich automatisch nach 5 Minuten Inaktivitaet
  (keine neuen Events im Log). Konfigurierbar via --timeout.
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Project-Root ist das Parent-Verzeichnis von scripts/
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
PID_FILE = PROJECT_ROOT / ".agent-meta/viz/.server-pid"
LOG_FILE = PROJECT_ROOT / ".agent-meta/viz/server.log"
VIZ_REPORT = SCRIPT_DIR / "viz-report.py"
PORT = 8765
DEFAULT_TIMEOUT = 300  # 5 Minuten


def get_pid():
    if PID_FILE.exists():
        try:
            return int(PID_FILE.read_text().strip())
        except ValueError:
            pass
    return None


def is_running(pid):
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


def start_server(timeout: int = DEFAULT_TIMEOUT):
    pid = get_pid()
    if pid and is_running(pid):
        print(f"  i  Server läuft bereits. PID: {pid}")
        print(f"  i  Dashboard: http://localhost:{PORT}/")
        return

    PID_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Altes Log rotieren
    if LOG_FILE.exists():
        try:
            LOG_FILE.unlink()
        except PermissionError:
            pass

    if sys.platform == "win32":
        # STARTUPINFO versteckt das Konsolenfenster
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
        proc = subprocess.Popen(
            [sys.executable, str(VIZ_REPORT), "--serve", "--timeout", str(timeout)],
            stdout=open(LOG_FILE, "a", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            startupinfo=si,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            cwd=str(PROJECT_ROOT),
        )
    else:
        proc = subprocess.Popen(
            [sys.executable, str(VIZ_REPORT), "--serve", "--timeout", str(timeout)],
            stdout=open(LOG_FILE, "a", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
            cwd=str(PROJECT_ROOT),
        )

    PID_FILE.write_text(str(proc.pid))
    time.sleep(1.5)

    if is_running(proc.pid):
        print(f"  i  Server gestartet. PID: {proc.pid}")
        print(f"  i  Dashboard: http://localhost:{PORT}/")
        print(f"  i  Auto-Shutdown: {timeout}s Inaktivitaet")
        print(f"  i  Log: {LOG_FILE}")
    else:
        print(f"  !  Server konnte nicht gestartet werden. Siehe {LOG_FILE}")
        PID_FILE.unlink(missing_ok=True)


def stop_server():
    pid = get_pid()
    if not pid:
        print("  i  Server läuft nicht.")
        return

    if not is_running(pid):
        print(f"  i  Prozess {pid} nicht mehr aktiv.")
        PID_FILE.unlink(missing_ok=True)
        return

    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=True, capture_output=True)
        else:
            os.kill(pid, 15)  # SIGTERM
            time.sleep(1)
            if is_running(pid):
                os.kill(pid, 9)  # SIGKILL
        print(f"  i  Server beendet (PID: {pid}).")
    except Exception as e:
        print(f"  !  Fehler beim Beenden: {e}")
    finally:
        PID_FILE.unlink(missing_ok=True)


def toggle_server():
    pid = get_pid()
    if pid and is_running(pid):
        print(f"  i  Server läuft (PID: {pid}) — stoppe...")
        stop_server()
    else:
        print(f"  i  Server läuft nicht — starte...")
        start_server()


def status():
    pid = get_pid()
    if pid and is_running(pid):
        print(f"  i  Server LAUFT. PID: {pid}")
        print(f"  i  Dashboard: http://localhost:{PORT}/")
        print(f"  i  Log: {LOG_FILE}")
    else:
        print("  i  Server läuft NICHT.")
        if PID_FILE.exists():
            PID_FILE.unlink(missing_ok=True)


def restart():
    stop_server()
    time.sleep(1)
    start_server()


def open_browser():
    import webbrowser
    webbrowser.open(f"http://localhost:{PORT}/")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "toggle":
        toggle_server()
    elif cmd == "start":
        start_server()
    elif cmd == "stop":
        stop_server()
    elif cmd == "status":
        status()
    elif cmd == "restart":
        restart()
    elif cmd == "open":
        open_browser()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
