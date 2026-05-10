#!/usr/bin/env python3
"""
agent-meta viz-report.py
========================
CLI-Tool zur Analyse und Visualisierung von Agenten-Sessions.

Usage:
  python scripts/viz-report.py --watch                    # Live-Monitoring
  python scripts/viz-report.py --format html              # HTML-Report
  python scripts/viz-report.py --format terminal          # Terminal-Ausgabe
  python scripts/viz-report.py --agent developer          # Filter auf Agenten
  python scripts/viz-report.py --serve                    # Lokaler Webserver
  python scripts/viz-report.py --cleanup --days 7         # Alte Sessions löschen

Config in .meta-config/project.yaml:
  viz:
    mode: dynamic
    event_log: .agent-meta/viz/events.jsonl
    report:
      retention_days: 7
      session_timeout_min: 5
"""

import argparse
import json
import sys
import time
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

# Add scripts/ directory to sys.path so lib/ is importable regardless of cwd
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.log import SyncLog
from lib.viz import (
    read_events, list_sessions, get_viz_dir, get_event_log_path,
    cleanup_old_sessions, _TIER_ICONS, _TIER_COLORS,
)


def _parse_ts(ts_str: str) -> datetime:
    """Parse ISO8601 timestamp."""
    return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))


def _format_duration(seconds: float) -> str:
    """Formatiere Dauer als mm:ss."""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def _format_ts(dt: datetime) -> str:
    """Formatiere Timestamp als HH:MM:SS."""
    return dt.strftime("%H:%M:%S")


def build_session_state(events: list[dict]) -> dict:
    """Baue den Session-State aus Events.

    Returns:
        {
            "agents": {"name": {"status": "idle|running|done|error", "started_at": dt, "ended_at": dt, ...}},
            "edges": [{"from": "...", "to": "...", "ts": dt}],
            "timeline": [...],
            "duration_sec": float,
            "session_name": str,
        }
    """
    agents = defaultdict(lambda: {
        "status": "idle",
        "started_at": None,
        "ended_at": None,
        "duration_sec": 0.0,
        "last_error": None,
    })
    edges = []
    timeline = []
    session_start = None
    session_end = None
    session_name = "Unnamed Session"

    for ev in events:
        ts = _parse_ts(ev.get("ts", ""))
        event_type = ev.get("event", "")
        agent = ev.get("agent", "")

        if not session_start:
            session_start = ts
        session_end = ts

        if event_type == "session_start":
            task = ev.get('payload', {}).get('task', '')
            if task:
                session_name = task
            timeline.append({"ts": ts, "icon": "▶", "msg": f"Session gestartet: {task}"})
        elif event_type == "session_end":
            timeline.append({"ts": ts, "icon": "■", "msg": "Session beendet"})
        elif event_type == "agent_start":
            agents[agent]["status"] = "running"
            agents[agent]["started_at"] = ts
            timeline.append({"ts": ts, "icon": "▶", "msg": f"{agent} gestartet"})
        elif event_type == "agent_end":
            agents[agent]["status"] = ev.get("status", "done")
            agents[agent]["ended_at"] = ts
            if agents[agent]["started_at"]:
                agents[agent]["duration_sec"] = (ts - agents[agent]["started_at"]).total_seconds()
            if ev.get("status") == "error":
                agents[agent]["last_error"] = ev.get("payload", {}).get("error", "Unknown error")
            timeline.append({"ts": ts, "icon": "✓" if ev.get("status") == "success" else "✗",
                           "msg": f"{agent} beendet ({ev.get('status', '?')})"})
        elif event_type == "delegate":
            from_agent = ev.get("from", "")
            to_agent = ev.get("to", "")
            edges.append({"from": from_agent, "to": to_agent, "ts": ts})
            timeline.append({"ts": ts, "icon": "→", "msg": f"{from_agent} → {to_agent}"})
        elif event_type == "tool_call":
            tool = ev.get("tool", "")
            timeline.append({"ts": ts, "icon": "🔧", "msg": f"{agent}: {tool}"})
        elif event_type == "log":
            level = ev.get("payload", {}).get("level", "info")
            msg = ev.get("payload", {}).get("message", "")
            icon = {"error": "⚠", "warn": "⚡", "info": "ℹ"}.get(level, "ℹ")
            timeline.append({"ts": ts, "icon": icon, "msg": f"{agent}: {msg}"})

    duration = 0.0
    if session_start and session_end:
        duration = (session_end - session_start).total_seconds()

    return {
        "agents": dict(agents),
        "edges": edges,
        "timeline": timeline,
        "duration_sec": duration,
        "session_start": session_start,
        "session_end": session_end,
        "session_name": session_name,
    }


def render_terminal(events: list[dict], agent_filter: str | None = None) -> str:
    """Rendere Terminal-Output."""
    state = build_session_state(events)
    lines = []

    # Header
    start_str = _format_ts(state["session_start"]) if state["session_start"] else "??:??:??"
    name = state.get("session_name", "Unnamed Session")
    name = name[:50] + "..." if len(name) > 50 else name
    lines.append("┌" + "─" * 77 + "┐")
    lines.append(f"│  🤖 AGENT SESSION REPORT                                               │")
    lines.append(f"│  {name:<72}│")
    lines.append(f"│  {start_str} — Dauer: {_format_duration(state['duration_sec']):<52}│")
    lines.append("├" + "─" * 77 + "┤")

    # Agenten-Status-Balken
    agent_names = sorted(state["agents"].keys())
    if agent_filter:
        agent_names = [a for a in agent_names if agent_filter.lower() in a.lower()]

    for name in agent_names:
        info = state["agents"][name]
        status = info["status"]
        duration = info["duration_sec"]
        dur_str = _format_duration(duration) if duration else "—"

        # Status-Icon
        status_icon = {"idle": "○", "running": "▶", "done": "✓", "success": "✓", "error": "✗"}.get(status, "?")

        # Progress-Bar (20 chars)
        total_dur = state["duration_sec"] or 1
        progress = min(int((duration / total_dur) * 20), 20) if duration else 0
        bar = "█" * progress + "░" * (20 - progress)

        # Hierarchie-Indent
        indent = "  " if name != "orchestrator" else ""
        if any(e["to"] == name for e in state["edges"]):
            indent = "  ├─ " + indent
        else:
            indent = "  │  " + indent
        if name == "orchestrator":
            indent = ""

        lines.append(f"│  {indent}{status_icon} {name:<18} [{bar}] {status:<8} {dur_str:<8} │")

    lines.append("├" + "─" * 77 + "┤")
    lines.append("│  Timeline:                                                               │")

    # Timeline
    for item in state["timeline"][-15:]:  # Letzte 15 Events
        ts_str = _format_ts(item["ts"])
        icon = item["icon"]
        msg = item["msg"][:55]
        lines.append(f"│  {ts_str}  {icon}  {msg:<56}│")

    lines.append("└" + "─" * 77 + "┘")
    return "\n".join(lines)


def _render_mermaid_gantt(state: dict) -> str:
    """Rendere Mermaid Gantt-Diagramm für die Session."""
    if not state["session_start"]:
        return ""
    lines = ["```mermaid", "gantt", "    title Agenten-Ablauf", "    dateFormat HH:mm:ss", "    section Session"]
    for name, info in sorted(state["agents"].items()):
        if info["started_at"]:
            start = info["started_at"].strftime("%H:%M:%S")
            end = info["ended_at"].strftime("%H:%M:%S") if info["ended_at"] else "now"
            status = info["status"]
            tag = {"running": "active", "success": "done", "done": "done", "error": "crit"}.get(status, "")
            if tag:
                lines.append(f'    {name} :{tag}, {start}, {end}')
            else:
                lines.append(f'    {name} :{start}, {end}')
    lines.append("```")
    return "\n".join(lines)


def _render_mermaid_sequence(state: dict) -> str:
    """Rendere Mermaid Sequence-Diagramm für Delegationen."""
    if not state["edges"]:
        return ""
    lines = ["```mermaid", "sequenceDiagram", "    autonumber"]
    # Sammle alle beteiligten Agenten
    participants = set()
    for e in state["edges"]:
        participants.add(e["from"])
        participants.add(e["to"])
    for p in sorted(participants):
        lines.append(f'    participant "{p}" as {p}')
    for e in state["edges"]:
        lines.append(f"    {e['from']}->>{e['to']}: delegate")
    lines.append("```")
    return "\n".join(lines)


def render_html(events: list[dict]) -> str:
    """Rendere HTML-Report mit Mermaid-Diagrammen."""
    state = build_session_state(events)
    session_name = state.get("session_name", "Unnamed Session")

    # Agenten-Karten
    agent_cards = []
    for name, info in sorted(state["agents"].items()):
        status = info["status"]
        duration = info["duration_sec"]
        dur_str = _format_duration(duration) if duration else "—"
        status_class = status
        status_icon = {"idle": "○", "running": "▶", "done": "✓", "success": "✓", "error": "✗"}.get(status, "?")

        agent_cards.append(f"""
        <div class="agent-card {status_class}">
            <div class="agent-name">{status_icon} {name}</div>
            <div class="agent-status">{status}</div>
            <div class="agent-duration">{dur_str}</div>
        </div>
        """)

    # Timeline
    timeline_rows = []
    for item in state["timeline"]:
        ts_str = _format_ts(item["ts"])
        icon = item["icon"]
        msg = item["msg"]
        timeline_rows.append(f"<tr><td>{ts_str}</td><td>{icon}</td><td>{msg}</td></tr>")

    # Mermaid Diagramme
    gantt = _render_mermaid_gantt(state)
    sequence = _render_mermaid_sequence(state)

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <title>Session Report — {session_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        :root {{
            --bg: #0f0f23;
            --surface: #1a1a2e;
            --text: #eaeaea;
            --text-muted: #a0a0a0;
            --border: #2a2a4a;
            --running: #ffd43b;
            --success: #69db7c;
            --error: #ff6b6b;
            --idle: #868e96;
        }}
        body {{ background: var(--bg); color: var(--text); font-family: sans-serif; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ border-bottom: 2px solid var(--border); padding-bottom: 10px; }}
        h2 {{ margin-top: 30px; color: var(--text-muted); }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat {{ background: var(--surface); padding: 15px; border-radius: 8px; flex: 1; }}
        .agents {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .agent-card {{ background: var(--surface); padding: 15px; border-radius: 8px; border-left: 4px solid var(--idle); }}
        .agent-card.running {{ border-left-color: var(--running); }}
        .agent-card.done, .agent-card.success {{ border-left-color: var(--success); }}
        .agent-card.error {{ border-left-color: var(--error); }}
        .agent-name {{ font-weight: bold; font-size: 1.1rem; }}
        .agent-status {{ color: var(--text-muted); margin: 5px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid var(--border); }}
        th {{ color: var(--text-muted); }}
        .mermaid-container {{ background: var(--surface); padding: 20px; border-radius: 8px; margin: 20px 0; overflow: auto; }}
        .mermaid {{ background: var(--bg); padding: 15px; border-radius: 8px; }}
        footer {{ margin-top: 30px; color: var(--text-muted); font-size: 0.85rem; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Session Report</h1>
        <h2>{session_name}</h2>
        <div class="stats">
            <div class="stat">
                <div>Session-Dauer</div>
                <div><strong>{_format_duration(state['duration_sec'])}</strong></div>
            </div>
            <div class="stat">
                <div>Agenten</div>
                <div><strong>{len(state['agents'])}</strong></div>
            </div>
            <div class="stat">
                <div>Events</div>
                <div><strong>{len(events)}</strong></div>
            </div>
        </div>
        <h2>Agenten-Ablauf (Gantt)</h2>
        <div class="mermaid-container">
            <div class="mermaid">
{gantt}
            </div>
        </div>
        <h2>Delegationen</h2>
        <div class="mermaid-container">
            <div class="mermaid">
{sequence}
            </div>
        </div>
        <h2>Agenten</h2>
        <div class="agents">
            {''.join(agent_cards)}
        </div>
        <h2>Timeline</h2>
        <table>
            <thead><tr><th>Zeit</th><th></th><th>Ereignis</th></tr></thead>
            <tbody>
                {''.join(timeline_rows)}
            </tbody>
        </table>
        <footer>
            Generiert von agent-meta viz-report
        </footer>
    </div>
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
    </script>
</body>
</html>
"""


def serve_web(project_root: Path, port: int = 8765):
    """Starte einen lokalen Webserver für die Visualisierung."""
    try:
        from flask import Flask, jsonify, render_template_string
    except ImportError:
        print("  !  Flask nicht installiert. Installiere mit: pip install flask")
        print("  !  Oder nutze --format html statt --serve")
        sys.exit(1)

    app = Flask(__name__)
    viz_dir = get_viz_dir(project_root)

    @app.route("/")
    def index():
        sessions = list_sessions(project_root)
        session_links = "<br>".join(
            f'<a href="/session/{s}">{s}</a>' for s in sessions[:10]
        ) if sessions else "<em>Keine Sessions gefunden</em>"
        return render_template_string(f"""
        <h1>🤖 agent-meta Visualisierung</h1>
        <h2>Sessions</h2>
        {session_links}
        <h2>Statische Visualisierung</h2>
        <a href="/agent-graph.html">Agenten-Graph</a>
        """)

    @app.route("/agent-graph.html")
    def agent_graph():
        graph_path = project_root / "docs" / "agent-graph.html"
        if not graph_path.exists():
            return "<h1>Agenten-Graph nicht gefunden</h1><p>Führe zuerst <code>python scripts/sync.py</code> aus.</p>", 404
        return graph_path.read_text(encoding="utf-8")

    @app.route("/session/<session_id>")
    def session_report(session_id):
        events = read_events(project_root, session_id)
        if not events:
            return "<h1>Keine Events</h1>", 404
        return render_html(events)

    @app.route("/api/sessions")
    def api_sessions():
        return jsonify(list_sessions(project_root))

    @app.route("/api/session/<session_id>")
    def api_session(session_id):
        events = read_events(project_root, session_id)
        return jsonify(events)

    print(f"  i  Webserver läuft auf http://localhost:{port}")
    print(f"  i  Drücke Ctrl+C zum Beenden")
    app.run(host="127.0.0.1", port=port, debug=False)


def main():
    # UTF-8 für Windows-Terminal erzwingen
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Agent-Session Report und Visualisierung"
    )
    parser.add_argument("--project-root", default=".",
                        help="Projekt-Root-Verzeichnis (default: current directory)")
    parser.add_argument("--session", default=None,
                        help="Session-ID (default: aktuellste)")
    parser.add_argument("--format", choices=["terminal", "html", "json"], default="terminal",
                        help="Ausgabeformat")
    parser.add_argument("--output", default=None,
                        help="Ausgabedatei (für html/json)")
    parser.add_argument("--watch", action="store_true",
                        help="Live-Monitoring (aktualisiert alle 5 Sekunden)")
    parser.add_argument("--agent", default=None,
                        help="Filter auf Agenten-Namen")
    parser.add_argument("--since", default=None,
                        help="Zeitstempel seit dem (ISO8601)")
    parser.add_argument("--serve", action="store_true",
                        help="Starte lokalen Webserver")
    parser.add_argument("--port", type=int, default=8765,
                        help="Port für Webserver (default: 8765)")
    parser.add_argument("--cleanup", action="store_true",
                        help="Lösche alte Sessions")
    parser.add_argument("--days", type=int, default=7,
                        help="Retention-Tage für Cleanup (default: 7)")

    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()

    if args.serve:
        serve_web(project_root, port=args.port)
        return

    if args.cleanup:
        log = SyncLog()
        cleanup_old_sessions(project_root, retention_days=args.days, log=log)
        print(f"  i  Cleanup abgeschlossen")
        return

    # Session-ID bestimmen
    session_id = args.session
    if not session_id:
        sessions = list_sessions(project_root)
        if sessions:
            session_id = sessions[0]
        # Fallback: keine Session-ID = events.jsonl

    since = None
    if args.since:
        since = datetime.fromisoformat(args.since.replace("Z", "+00:00"))

    def _load_and_render():
        events = read_events(project_root, session_id, since)
        if not events:
            print("  !  Keine Events gefunden")
            return None

        if args.format == "terminal":
            return render_terminal(events, args.agent)
        elif args.format == "html":
            return render_html(events)
        elif args.format == "json":
            return json.dumps(events, indent=2, ensure_ascii=False)
        return None

    if args.watch:
        print(f"  i  Live-Monitoring gestartet (Ctrl+C zum Beenden)")
        last_len = 0
        try:
            while True:
                events = read_events(project_root, session_id, since)
                if len(events) != last_len:
                    last_len = len(events)
                    output = render_terminal(events, args.agent)
                    if output:
                        os.system("cls" if os.name == "nt" else "clear")
                        print(output)
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n  i  Monitoring beendet")
    else:
        output = _load_and_render()
        if output:
            if args.output:
                Path(args.output).write_text(output, encoding="utf-8")
                print(f"  i  Gespeichert: {args.output}")
            else:
                print(output)


if __name__ == "__main__":
    main()
