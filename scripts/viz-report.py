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
    event_log: .meta-viz/events.jsonl
    report:
      retention_days: 7
      session_timeout_min: 5
"""

import argparse
import json
import re
import sys
import time
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_SESSION_FALLBACK_MINUTES = 60
_MIN_EVENTS_FALLBACK = 50
_INACTIVITY_CHECK_INTERVAL_MAX = 30
_STATUS_ICONS = {"idle": "○", "running": "▶", "done": "✓", "success": "✓", "error": "✗"}

# Add scripts/ directory to sys.path so lib/ is importable regardless of cwd
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.log import SyncLog
from lib.viz import (
    read_events, list_sessions, get_viz_dir, get_event_log_path,
    cleanup_old_sessions, _TIER_ICONS, _TIER_COLORS, viz_lock,
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


def _extract_latest_session(events: list[dict], user_window: bool = False) -> list[dict]:
    """Extrahiere nur Events der letzten Session (nach letztem session_start).

    Wenn kein session_start vorhanden:
    - user_window=True: alle übergebenen Events zeigen (Nutzer hat Fenster explizit gewählt)
    - user_window=False: nur Events der letzten 60 Minuten (Phantomdauer vermeiden)
    """
    last_start_idx = None
    for i, ev in enumerate(events):
        if ev.get("event") == "session_start":
            last_start_idx = i
    if last_start_idx is not None:
        return events[last_start_idx:]

    if user_window:
        return events  # Nutzer hat explizit ein Zeitfenster gewählt — alles anzeigen

    # Fallback: letzte N Minuten
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=_SESSION_FALLBACK_MINUTES)
    recent = [
        ev for ev in events
        if _parse_ts(ev.get("ts", "1970-01-01T00:00:00Z")) >= cutoff
    ]
    return recent if recent else events[-_MIN_EVENTS_FALLBACK:]  # Immer mindestens N Events zeigen


def build_session_state(events: list[dict], user_window: bool = False) -> dict:
    """Baue den Session-State aus Events.

    Args:
        events: Rohe Event-Liste
        user_window: True wenn der Nutzer ein explizites Zeitfenster gewählt hat.
                     Deaktiviert den 60-Min-Fallback in _extract_latest_session.

    Returns:
        {
            "agents": {"name": {"status": "idle|running|done|error", "started_at": dt, "ended_at": dt, ...}},
            "edges": [{"from": "...", "to": "...", "ts": dt}],
            "timeline": [...],
            "duration_sec": float,
            "session_name": str,
        }
    """
    events = _extract_latest_session(events, user_window=user_window)

    agents = defaultdict(lambda: {
        "status": "idle",
        "started_at": None,
        "ended_at": None,
        "duration_sec": 0.0,
        "last_error": None,
        "tool_calls": 0,
        "tools_used": {},
        "provider": "",
        "model": "",
    })
    edge_map: dict[tuple, dict] = {}   # (from, to) → merged edge with count + tasks
    timeline = []
    session_start = None
    session_end = None
    session_name = "Unnamed Session"

    for ev in events:
        ts_str = ev.get("ts", "")
        if not ts_str:
            continue  # Skip events without timestamp
        ts = _parse_ts(ts_str)
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
            if ev.get("provider"):
                agents[agent]["provider"] = ev["provider"]
            if ev.get("model"):
                agents[agent]["model"] = ev["model"]
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
            to_agent   = ev.get("to", "")
            task       = ev.get("task", "")
            key = (from_agent, to_agent)
            if key not in edge_map:
                edge_map[key] = {"from": from_agent, "to": to_agent, "count": 0, "tasks": [], "ts": ts}
            edge_map[key]["count"] += 1
            if task:
                edge_map[key]["tasks"].append(task)
            timeline.append({"ts": ts, "icon": "→", "msg": f"{from_agent} → {to_agent}"})
        elif event_type == "tool_call":
            tool = ev.get("tool", "")
            agents[agent]["tool_calls"] += 1
            tools = agents[agent]["tools_used"]
            tools[tool] = tools.get(tool, 0) + 1
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
        "edges": list(edge_map.values()),
        "timeline": timeline,
        "duration_sec": duration,
        "session_start": session_start,
        "session_end": session_end,
        "session_name": session_name,
    }


class _DateTimeEncoder(json.JSONEncoder):
    """JSON-Encoder der datetime-Objekte automatisch als ISO-Strings serialisiert."""

    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


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
        status_icon = _STATUS_ICONS.get(status, "?")

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
    # Mermaid 10.x braucht ein Datum bei dateFormat; wir nutzen einen Dummy-Tag
    dummy = "2026-01-01"
    lines = [
        "```mermaid",
        "gantt",
        "    title Agenten-Ablauf",
        "    dateFormat YYYY-MM-DD HH:mm:ss",
        "    axisFormat %H:%M:%S",
        "    section Session",
    ]
    for name, info in sorted(state["agents"].items()):
        if info["started_at"]:
            s = info["started_at"].strftime(f"{dummy} %H:%M:%S")
            e = info["ended_at"].strftime(f"{dummy} %H:%M:%S") if info["ended_at"] else "now"
            status = info["status"]
            tag = {"running": "active", "success": "done", "done": "done", "error": "crit"}.get(status, "")
            if tag:
                lines.append(f'    {name} :{tag}, {s}, {e}')
            else:
                lines.append(f'    {name} :{s}, {e}')
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


def render_html(events: list[dict], live_mode: bool = False) -> str:
    """Rendere HTML-Report mit Mermaid-Gantt und D3.js Delegations-Graph."""
    state = build_session_state(events)
    session_name = state.get("session_name", "Unnamed Session")
    live_meta = '<meta http-equiv="refresh" content="5">\n' if live_mode else ''

    # Agenten-Karten
    agent_cards = []
    for name, info in sorted(state["agents"].items()):
        status = info["status"]
        duration = info["duration_sec"]
        dur_str = _format_duration(duration) if duration else "—"
        status_class = status
        status_icon = _STATUS_ICONS.get(status, "?")

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

    # Mermaid Gantt
    gantt = _render_mermaid_gantt(state)

    # D3.js Daten (JSON-serialisiert für XSS-Sicherheit)
    nodes_data = []
    for name, info in state["agents"].items():
        color = {"running": "#ffd43b", "success": "#69db7c", "done": "#69db7c", "error": "#ff6b6b"}.get(info["status"], "#868e96")
        nodes_data.append({"id": name, "status": info["status"], "color": color})
    nodes_json = json.dumps(nodes_data, ensure_ascii=False)

    edges_sorted = sorted(state["edges"], key=lambda e: e["ts"])
    links_data = []
    for e in edges_sorted:
        links_data.append({"source": e["from"], "target": e["to"], "ts": e["ts"]})
    links_json = json.dumps(links_data, ensure_ascii=False)

    d3_script = f"""
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
        (function() {{
            const nodes = {nodes_json};
            const links = {links_json};
            const container = document.getElementById("delegation-graph");
            const width = container.clientWidth || 800;
            const height = 500;

            const svg = d3.select("#delegation-graph")
                .append("svg")
                .attr("viewBox", `0 0 ${{width}} ${{height}}`)
                .attr("preserveAspectRatio", "xMidYMid meet")
                .style("width", "100%")
                .style("height", "auto")
                .style("max-height", "600px");

            const simulation = d3.forceSimulation(nodes)
                .force("link", d3.forceLink(links).id(d => d.id).distance(140))
                .force("charge", d3.forceManyBody().strength(-500))
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("collide", d3.forceCollide().radius(35));

            const linkGroup = svg.append("g").attr("class", "links");
            const nodeGroup = svg.append("g").attr("class", "nodes");

            const link = linkGroup.selectAll("line")
                .data(links)
                .join("line")
                .attr("stroke", "#444")
                .attr("stroke-width", 2)
                .attr("stroke-opacity", 0.6);

            const node = nodeGroup.selectAll("g")
                .data(nodes)
                .join("g")
                .call(d3.drag()
                    .on("start", (event, d) => {{
                        if (!event.active) simulation.alphaTarget(0.3).restart();
                        d.fx = d.x; d.fy = d.y;
                    }})
                    .on("drag", (event, d) => {{
                        d.fx = event.x; d.fy = event.y;
                    }})
                    .on("end", (event, d) => {{
                        if (!event.active) simulation.alphaTarget(0);
                        d.fx = null; d.fy = null;
                    }}));

            node.append("circle")
                .attr("r", 22)
                .attr("fill", d => d.color)
                .attr("stroke", "#fff")
                .attr("stroke-width", 2);

            node.append("text")
                .text(d => d.id)
                .attr("text-anchor", "middle")
                .attr("dy", ".35em")
                .attr("fill", "#fff")
                .attr("font-size", "11px")
                .attr("font-weight", "bold")
                .style("pointer-events", "none");

            // Tooltip
            const tooltip = d3.select("body").append("div")
                .style("position", "absolute")
                .style("background", "#1a1a2e")
                .style("color", "#eaeaea")
                .style("padding", "8px 12px")
                .style("border-radius", "6px")
                .style("border", "1px solid #2a2a4a")
                .style("font-size", "12px")
                .style("pointer-events", "none")
                .style("opacity", 0)
                .style("transition", "opacity 0.2s");

            node.on("mouseover", (event, d) => {{
                tooltip.style("opacity", 1).html(`<strong>${{d.id}}</strong><br>status: ${{d.status}}`);
            }})
            .on("mousemove", (event) => {{
                tooltip.style("left", (event.pageX + 10) + "px").style("top", (event.pageY + 10) + "px");
            }})
            .on("mouseout", () => tooltip.style("opacity", 0));

            simulation.on("tick", () => {{
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);
                node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
            }});

            // Animated particle traveling along edges
            if (links.length > 0) {{
                const particle = svg.append("circle")
                    .attr("r", 6)
                    .attr("fill", "#ffd43b")
                    .attr("stroke", "#0f0f23")
                    .attr("stroke-width", 2)
                    .style("filter", "drop-shadow(0 0 6px #ffd43b)");

                let currentLink = 0;
                function animateParticle() {{
                    const l = links[currentLink];
                    if (!l) return;
                    particle
                        .attr("cx", l.source.x)
                        .attr("cy", l.source.y)
                        .transition()
                        .duration(1200)
                        .ease(d3.easeLinear)
                        .attr("cx", l.target.x)
                        .attr("cy", l.target.y)
                        .on("end", () => {{
                            currentLink = (currentLink + 1) % links.length;
                            setTimeout(animateParticle, 200);
                        }});
                }}
                // Start after layout settles
                setTimeout(animateParticle, 800);
            }}
        }})();
    </script>
    """

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="utf-8">
{live_meta}    <title>Session Report — {session_name}</title>
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
        .viz-container {{ background: var(--surface); padding: 20px; border-radius: 8px; margin: 20px 0; overflow: auto; }}
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
        <div class="viz-container">
            <div class="mermaid">
{gantt}
            </div>
        </div>
        <h2>Delegationen</h2>
        <div class="viz-container" id="delegation-graph" style="min-height:500px;">
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
{d3_script}
</body>
</html>
"""


class _ServerLog:
    """Strukturiertes Server-Logging mit optionalem Debug-Modus."""

    def __init__(self, debug: bool = False, log_file: Path | None = None):
        self.debug = debug
        self.log_file = log_file
        self._counts: dict[str, int] = {}

    def _write(self, level: str, msg: str):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{ts}] {level:5s} {msg}"
        print(line, file=sys.stderr, flush=True)
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except Exception:
                pass

    def info(self, msg: str):
        self._write("INFO", msg)

    def dbg(self, msg: str):
        if self.debug:
            self._write("DEBUG", msg)

    def warn(self, msg: str):
        self._write("WARN", msg)

    def err(self, msg: str, exc: Exception | None = None):
        self._write("ERROR", msg + (f": {exc}" if exc else ""))

    def req(self, method: str, path: str, status: int, events: int | None = None, extra: str = ""):
        detail = f"events={events}" if events is not None else ""
        if extra:
            detail = f"{detail} {extra}".strip()
        self._write("REQ", f"{status} {method} {path}" + (f"  [{detail}]" if detail else ""))


def _parse_window_param(window: str) -> datetime | None:
    """Konvertiert einen Fenster-String in einen 'since'-Timestamp.

    Unterstützte Formate: '15m', '30m', '1h', '3h', '6h', '24h', 'today', 'all'
    Gibt None zurück für 'all' (kein Filter).
    """
    if not window or window == "all":
        return None
    if window == "today":
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        return today
    m = re.match(r'^(\d+)(m|h)$', window)
    if m:
        amount = int(m.group(1))
        unit = m.group(2)
        delta = timedelta(minutes=amount) if unit == "m" else timedelta(hours=amount)
        return datetime.now(timezone.utc) - delta
    # Unknown format — caller may log a warning
    return None


def serve_web(project_root: Path, port: int = 8765, open_browser: bool = False,
              timeout_sec: int = 300, debug: bool = False):
    """Starte einen lokalen Webserver für die Echtzeit-Visualisierung (keine externen Dependencies)."""
    import mimetypes
    import threading
    import traceback
    from wsgiref.simple_server import WSGIServer, WSGIRequestHandler
    from socketserver import ThreadingMixIn
    from urllib.parse import parse_qs

    class _ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
        """Threaded WSGI server — handles concurrent requests (browser polling + UI actions)."""
        daemon_threads = True

    viz_dir   = get_viz_dir(project_root)
    docs_dir  = project_root / "docs"
    event_log = get_event_log_path(project_root)
    log       = _ServerLog(debug=debug, log_file=viz_dir / "server.log")
    shutdown_event = threading.Event()
    last_request_time = [time.time()]  # updated on every HTTP request

    def _resolve_docs_asset(rel_path: str) -> Path:
        """Resolve a docs asset path with fallback to the submodule layout.

        Mirrors the resolution order used by SyncExecutor / VizManager:
          1. ``<project_root>/docs/<rel_path>``              -- top-level checkout
          2. ``<project_root>/.agent-meta/docs/<rel_path>``  -- submodule layout

        Returns the primary path even when neither file exists, so callers can
        log the expected location in their 404 responses.
        """
        rel_clean = rel_path.lstrip("/")
        primary  = docs_dir / rel_clean
        fallback = project_root / ".agent-meta" / "docs" / rel_clean
        if primary.exists():
            return primary
        if fallback.exists():
            return fallback
        return primary

    # ── Startup info ────────────────────────────────────────────────────────
    log.info(f"=== viz-server start ===  port={port}  debug={debug}")
    log.info(f"project_root : {project_root}")
    log.info(f"event_log    : {event_log}  exists={event_log.exists()}")
    log.info(f"docs_dir     : {docs_dir}  exists={docs_dir.exists()}")
    _dashboard_path = _resolve_docs_asset("live-dashboard.html")
    log.info(f"dashboard    : {_dashboard_path}  "
             f"exists={_dashboard_path.exists()}")
    if event_log.exists():
        try:
            n = sum(1 for ln in event_log.read_text(encoding="utf-8-sig").splitlines() if ln.strip())
            log.info(f"events in log: {n}")
        except Exception as e:
            log.warn(f"cannot count events: {e}")

    class _SilentHandler(WSGIRequestHandler):
        """Suppress wsgiref's default stderr access log — we do our own."""
        def log_message(self, fmt, *args):
            pass

    def wsgi_app(environ, start_response):
        last_request_time[0] = time.time()
        method = environ.get("REQUEST_METHOD", "GET")
        path   = environ.get("PATH_INFO", "/")
        qs_params = parse_qs(environ.get("QUERY_STRING", ""))
        json_hdr  = [("Content-Type", "application/json; charset=utf-8")]
        # Always consume the request body so wsgiref doesn't hang on POST
        try:
            cl = int(environ.get("CONTENT_LENGTH") or 0)
            if cl > 0:
                environ["wsgi.input"].read(cl)
        except Exception:
            pass

        try:
            # ── Static HTML files ──────────────────────────────────────────
            if path in ("/", "/live-dashboard.html"):
                html_path = _resolve_docs_asset("live-dashboard.html")
                if html_path.exists():
                    body = html_path.read_bytes()
                    log.req(method, path, 200, extra=f"{len(body)//1024}KB  src={html_path}")
                    start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
                    return [body]
                log.warn(f"live-dashboard.html not found at {html_path}")
                start_response("404 Not Found", json_hdr)
                return [b'{"error":"live-dashboard.html not found"}']

            if path == "/agent-graph.html":
                html_path = _resolve_docs_asset("agent-graph.html")
                if html_path.exists():
                    start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
                    log.req(method, path, 200, extra=f"src={html_path}")
                    return [html_path.read_bytes()]
                log.warn(f"agent-graph.html not found at {html_path}")
                start_response("404 Not Found", json_hdr)
                return [b'{"error":"agent-graph.html not found"}']

            # ── /api/state ─────────────────────────────────────────────────
            if path == "/api/state":
                window      = qs_params.get("window", [None])[0]
                user_window = window is not None
                since       = _parse_window_param(window) if user_window else None
                if user_window and window != "all" and since is None:
                    log.warn(f"unbekanntes window-Format: {window}")
                events      = read_events(project_root, since=since)

                by_type: dict[str, int] = {}
                by_agent: dict[str, int] = {}
                for ev in events:
                    by_type[ev.get("event","?")] = by_type.get(ev.get("event","?"),0)+1
                    by_agent[ev.get("agent","?")] = by_agent.get(ev.get("agent","?"),0)+1

                state = build_session_state(events, user_window=user_window)
                body  = json.dumps(state, ensure_ascii=False, cls=_DateTimeEncoder).encode("utf-8")

                log.req(method, path, 200, events=len(events),
                        extra=f"window={window or 'default'}  "
                              f"agents={list(state['agents'].keys())}  "
                              f"edges={len(state['edges'])}  "
                              f"types={by_type}  "
                              f"by_agent={by_agent}")
                if not state["agents"]:
                    log.warn("state has no agents — check if session_start/agent_start events exist in log")
                start_response("200 OK", json_hdr)
                return [body]

            # ── /api/events ────────────────────────────────────────────────
            if path == "/api/events":
                window = qs_params.get("window", [None])[0]
                since  = _parse_window_param(window) if window else None
                if window and window != "all" and since is None:
                    log.warn(f"unbekanntes window-Format: {window}")
                events = read_events(project_root, since=since)
                body   = json.dumps(events, ensure_ascii=False, default=str).encode("utf-8")
                log.req(method, path, 200, events=len(events), extra=f"window={window or 'all'}")
                start_response("200 OK", json_hdr)
                return [body]

            # ── /api/clear-log ─────────────────────────────────────────────
            if path == "/api/clear-log" and method == "POST":
                try:
                    log_path = get_event_log_path(project_root)
                    prev_lines = 0
                    with viz_lock:
                        if log_path.exists():
                            prev_lines = sum(1 for _ in log_path.read_text(encoding="utf-8-sig").splitlines() if _)
                        # Atomic truncate via 'w' mode
                        with open(log_path, "w", encoding="utf-8") as f:
                            pass
                    log.info(f"log cleared — removed {prev_lines} events")
                    log.req(method, path, 200, extra=f"cleared {prev_lines} events")
                    start_response("200 OK", json_hdr)
                    return [json.dumps({"ok": True, "cleared": prev_lines}).encode("utf-8")]
                except Exception as exc:
                    log.err("clear-log failed", exc)
                    body = json.dumps({"ok": False, "error": str(exc)}).encode("utf-8")
                    start_response("500 Internal Server Error", json_hdr)
                    return [body]

            # ── /api/sessions ──────────────────────────────────────────────
            if path == "/api/sessions":
                sessions = list_sessions(project_root)
                body = json.dumps(sessions, ensure_ascii=False).encode("utf-8")
                log.req(method, path, 200, extra=f"{len(sessions)} sessions")
                start_response("200 OK", json_hdr)
                return [body]

            if path.startswith("/api/session/"):
                session_id = path.split("/")[-1]
                events = read_events(project_root, session_id)
                body   = json.dumps(events, ensure_ascii=False, default=str).encode("utf-8")
                log.req(method, path, 200, events=len(events))
                start_response("200 OK", json_hdr)
                return [body]

            # ── /api/debug ─────────────────────────────────────────────────
            if path == "/api/debug":
                info: dict = {
                    "event_log": str(event_log),
                    "event_log_exists": event_log.exists(),
                    "event_count": 0,
                    "event_types": {},
                    "event_agents": {},
                    "sessions": list_sessions(project_root),
                    "debug_mode": debug,
                    "docs_dir": str(docs_dir),
                }
                if event_log.exists():
                    evs = read_events(project_root)
                    info["event_count"] = len(evs)
                    for ev in evs:
                        t = ev.get("event", "?")
                        a = ev.get("agent", "?")
                        info["event_types"][t] = info["event_types"].get(t, 0) + 1
                        info["event_agents"][a] = info["event_agents"].get(a, 0) + 1
                body = json.dumps(info, ensure_ascii=False, indent=2).encode("utf-8")
                log.req(method, path, 200)
                start_response("200 OK", json_hdr)
                return [body]

            # ── Static files from docs/ ────────────────────────────────────
            static_path = _resolve_docs_asset(path)
            if static_path.exists() and static_path.is_file():
                ctype, _ = mimetypes.guess_type(str(static_path))
                start_response("200 OK", [("Content-Type", (ctype or "application/octet-stream") + "; charset=utf-8")])
                log.req(method, path, 200, extra=f"src={static_path}")
                return [static_path.read_bytes()]

            log.req(method, path, 404)
            start_response("404 Not Found", json_hdr)
            return [b'{"error":"not found"}']

        except Exception as exc:
            log.err(f"unhandled exception for {method} {path}", exc)
            if debug:
                log.err(traceback.format_exc())
            start_response("500 Internal Server Error", json_hdr)
            return [json.dumps({"error": str(exc)}).encode("utf-8")]

    def inactivity_watcher():
        """Beende Server nach Inaktivitaet.

        Inaktivitaet = max(last HTTP request time, log file mtime).
        HTTP-Polling vom Dashboard zaehlt als Aktivitaet, da der User
        aktiv zuschaut — auch wenn keine neuen Events geschrieben werden.
        """
        last_size = event_log.stat().st_size if event_log.exists() else 0
        check_interval = min(_INACTIVITY_CHECK_INTERVAL_MAX, timeout_sec // 2) if timeout_sec > 0 else _INACTIVITY_CHECK_INTERVAL_MAX

        while not shutdown_event.is_set():
            shutdown_event.wait(check_interval)
            if shutdown_event.is_set():
                break
            current_size = event_log.stat().st_size if event_log.exists() else 0
            if current_size != last_size:
                last_size = current_size
            # Activity = last log change OR last HTTP request (browser polling counts)
            last_activity = max(last_request_time[0],
                                event_log.stat().st_mtime if event_log.exists() else 0)
            elapsed = time.time() - last_activity
            remaining = timeout_sec - elapsed
            if remaining <= 60 and remaining > 0:
                print(f"\n  !  Auto-Shutdown in {int(remaining)}s (keine Aktivitaet)")
            if elapsed >= timeout_sec:
                print(f"\n  i  Auto-Shutdown nach {timeout_sec}s Inaktivitaet.")
                httpd.shutdown()
                break

    print(f"  i  Webserver läuft auf http://localhost:{port}")
    print(f"  i  Live-Dashboard: http://localhost:{port}/")
    if timeout_sec > 0:
        print(f"  i  Auto-Shutdown nach {timeout_sec}s Inaktivitaet")
    print(f"  i  Drücke Ctrl+C zum Beenden")

    if open_browser:
        import webbrowser
        webbrowser.open(f"http://localhost:{port}/")

    httpd = _ThreadingWSGIServer(("127.0.0.1", port), WSGIRequestHandler)
    httpd.set_app(wsgi_app)

    if timeout_sec > 0:
        watcher = threading.Thread(target=inactivity_watcher, daemon=True)
        watcher.start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  i  Server beendet")
    finally:
        shutdown_event.set()
        httpd.shutdown()


def main():
    # UTF-8 für Windows-Terminal erzwingen
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

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
    parser.add_argument("--timeout", type=int, default=300,
                        help="Auto-Shutdown nach N Sekunden Inaktivitaet (default: 300)")
    parser.add_argument("--debug", action="store_true",
                        help="Debug-Logging aktivieren (ausfuehrliche Server-Logs)")

    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()

    if args.serve:
        serve_web(project_root, port=args.port, timeout_sec=args.timeout, debug=args.debug)
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

    def _load_and_render(live: bool = False):
        events = read_events(project_root, session_id, since)
        if not events:
            print("  !  Keine Events gefunden")
            return None

        if args.format == "terminal":
            return render_terminal(events, args.agent)
        elif args.format == "html":
            return render_html(events, live_mode=live)
        elif args.format == "json":
            return json.dumps(events, indent=2, ensure_ascii=False)
        return None

    if args.watch:
        is_html = args.format == "html"

        if is_html:
            # Starte Server statt statische Datei zu schreiben
            serve_web(project_root, port=args.port, open_browser=True, debug=args.debug)
            return
        else:
            print(f"  i  Live-Monitoring gestartet (Ctrl+C zum Beenden)")

        last_len = 0
        try:
            while True:
                events = read_events(project_root, session_id, since)
                if len(events) != last_len:
                    last_len = len(events)
                    output = _load_and_render(live=False)
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
