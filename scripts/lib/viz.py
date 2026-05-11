"""Agent-Visualisierung: Statische Mindmap-Generierung und Event-Log-Management."""

import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

from .log import SyncLog
from .io import write_checked
from .agents import collect_sources, extract_frontmatter_field
from .roles import resolve_model
from .providers import load_providers_config

# Standardisierte Hierarchie: wer delegiert an wen
# Wird aus Beschreibungen und bekannten Workflows abgeleitet
_DELEGATION_MAP: dict[str, list[str]] = {
    "orchestrator": [
        "developer", "feature", "git", "documenter", "ideation",
        "release", "security-auditor", "docker", "log-analyzer",
        "feedback", "agent-meta-manager", "agent-meta-scout", "meta-feedback",
        "requirements", "validator", "tester",
    ],
    "developer": ["tester", "git"],
    "feature": ["requirements", "validator", "developer", "tester", "git"],
    "release": ["git", "documenter"],
    "log-analyzer": ["feedback", "developer", "security-auditor"],
    "agent-meta-manager": ["agent-meta-scout", "developer", "git"],
}

_TIER_ICONS = {
    "required": "🔴",
    "recommended": "🔵",
    "optional": "⚪",
}

_TIER_COLORS = {
    "required": "#e03131",
    "recommended": "#1971c2",
    "optional": "#868e96",
}

# Thread-safety lock for concurrent read/write access to event logs
viz_lock = threading.RLock()

# Tail-read heuristic: if log file exceeds this size, read from end when since filter is active
_TAIL_READ_THRESHOLD_BYTES = 1024 * 1024  # 1 MB
_TAIL_READ_MAX_LINES = 10000
_TAIL_READ_MIN_EVENTS = 100


def build_agent_hierarchy(agent_meta_root: Path, project_root: Path, config: dict, provider_config: dict | None = None) -> dict:
    """Baue die Agenten-Hierarchie aus allen verfügbaren Quellen.

    Sammelt 1-generic, 2-platform, 3-project und 0-external Skills.
    Extrahiert Frontmatter: description, model, memory, workflow_tier.
    Löst das Modell pro konfiguriertem Provider über resolve_model() auf.
    """
    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    agents: dict[str, dict] = {}
    providers = config.get("ai-providers", [])

    for role, path in overrides.items():
        if role.startswith("_"):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue

        description = extract_frontmatter_field(content, "description") or ""
        tier = _infer_tier(role, config)
        memory = extract_frontmatter_field(content, "memory") or ""

        # Resolve model per provider so the viz shows the actual assigned model
        models_by_provider: dict[str, str] = {}
        for provider in providers:
            resolved = resolve_model(role, config, agent_meta_root,
                                     provider=provider, provider_config=provider_config)
            if resolved:
                models_by_provider[provider] = resolved

        # If all providers resolve to the same model, collapse to a single value
        unique_models = set(models_by_provider.values())
        if len(unique_models) == 1:
            model = list(unique_models)[0]
        else:
            model = ""

        agents[role] = {
            "name": role,
            "description": description,
            "tier": tier,
            "model": model,
            "models_by_provider": models_by_provider,
            "memory": memory,
            "source": str(path),
            "children": _DELEGATION_MAP.get(role, []),
        }

    return agents


def _infer_tier(role: str, config: dict) -> str:
    """Inferiere workflow_tier aus role-defaults.yaml oder Config."""
    # Versuche role-defaults.yaml zu laden
    try:
        from .config import _load_yaml_or_json
        agent_meta_root = Path(__file__).resolve().parent.parent.parent
        defaults_path = agent_meta_root / "config" / "role-defaults.yaml"
        if defaults_path.exists():
            data, _ = _load_yaml_or_json(defaults_path)
            roles = data.get("roles", {})
            role_cfg = roles.get(role, {})
            return role_cfg.get("workflow_tier", "optional")
    except Exception:
        pass
    return "optional"


def render_mermaid_mindmap(agents: dict, config: dict) -> str:
    """Rendere Mermaid mindmap-Diagramm als Markdown."""
    lines = [
        "# Agenten-Übersicht",
        "",
        "> Automatisch generiert von agent-meta. Nicht manuell bearbeiten.",
        "",
        "```mermaid",
        "mindmap",
    ]

    root = agents.get("orchestrator")
    if root:
        lines.append('  root((orchestrator))')
        for child_role in root.get("children", []):
            child = agents.get(child_role)
            if child:
                tier = child.get("tier", "optional")
                icon = _TIER_ICONS.get(tier, "⚪")
                lines.append(f'    {icon} {child_role}')
                for grandchild_role in child.get("children", []):
                    if grandchild_role in agents:
                        lines.append(f'      {grandchild_role}')

    lines.extend([
        "```",
        "",
        "## Legende",
        "",
        "| Symbol | Bedeutung |",
        "|--------|-----------|",
        "| 🔴 | required — Kern-Workflow |",
        "| 🔵 | recommended — Standard-Qualität |",
        "| ⚪ | optional — Bei Bedarf |",
        "",
        "## Agenten-Details",
        "",
    ])

    for role, agent in sorted(agents.items()):
        lines.append(f"### {role}")
        lines.append(f"- **Tier:** {agent.get('tier', '-')}")
        desc = agent.get('description', '-')
        lines.append(f"- **Beschreibung:** {desc}")
        models_by_provider = agent.get("models_by_provider", {})
        if models_by_provider:
            unique = set(models_by_provider.values())
            if len(unique) == 1:
                lines.append(f"- **Model:** {list(unique)[0]}")
            else:
                parts = [f"{p}: {m}" for p, m in models_by_provider.items()]
                lines.append(f"- **Model:** {', '.join(parts)}")
        else:
            model = agent.get('model', '')
            lines.append(f"- **Model:** {model if model else 'inherited'}")
        if agent.get("children"):
            lines.append(f"- **Delegiert an:** {', '.join(agent['children'])}")
        lines.append("")

    return "\n".join(lines)


def render_mermaid_graph_td(agents: dict, config: dict) -> str:
    """Rendere Mermaid graph TD als Fallback."""
    lines = [
        "```mermaid",
        "graph TD",
    ]

    # Edges
    for role, agent in agents.items():
        for child_role in agent.get("children", []):
            if child_role in agents:
                lines.append(f"    {role} --> {child_role}")

    # Class definitions
    lines.append("")
    for tier, color in _TIER_COLORS.items():
        lines.append(
            f'    classDef {tier} fill:{color},stroke:#fff,stroke-width:2px,color:#fff'
        )

    # Assign classes
    class_lines = []
    for tier in _TIER_COLORS:
        roles_in_tier = [r for r, a in agents.items() if a.get("tier") == tier]
        if roles_in_tier:
            class_lines.append(f"    class {','.join(roles_in_tier)} {tier}")
    lines.extend(class_lines)

    lines.append("```")
    return "\n".join(lines)


def render_interactive_html(agents: dict, config: dict) -> str:
    """Rendere interaktives HTML mit eingebettetem Mermaid."""
    mermaid_src = render_mermaid_graph_td(agents, config)
    # Strip markdown code fences
    mermaid_code = mermaid_src.replace("```mermaid\n", "").replace("\n```", "")

    agent_cards = []
    for role, agent in sorted(agents.items()):
        tier = agent.get("tier", "optional")
        card_class = f"tier-{tier}"
        icon = _TIER_ICONS.get(tier, "⚪")
        desc = agent.get("description", "")
        model = agent.get("model", "")
        models_by_provider = agent.get("models_by_provider", {})
        memory = agent.get("memory", "")
        children = agent.get("children", [])

        children_html = ""
        if children:
            children_links = ", ".join(
                f'<a href="#{c}" onclick="scrollToAgent(\'{c}\')">{c}</a>'
                for c in children if c in agents
            )
            children_html = f'<div class="children"><strong>Delegiert an:</strong> {children_links}</div>'

        if models_by_provider:
            unique = set(models_by_provider.values())
            if len(unique) == 1:
                model_display = list(unique)[0]
            else:
                model_display = "<br>".join(
                    f"<span>{p}: {m}</span>" for p, m in models_by_provider.items()
                )
        else:
            model_display = model if model else 'inherited'

        agent_cards.append(f"""
        <div class="agent-card {card_class}" id="{role}">
            <div class="agent-header">
                <span class="tier-icon">{icon}</span>
                <h3>{role}</h3>
                <span class="tier-badge">{tier}</span>
            </div>
            <p class="description">{desc}</p>
            <div class="meta">
                <span><strong>Model:</strong> {model_display}</span>
                <span><strong>Memory:</strong> {memory if memory else '-'}</span>
            </div>
            {children_html}
        </div>
        """)

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 agent-meta — Agenten-Visualisierung</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        :root {{
            --bg: #0f0f23;
            --surface: #1a1a2e;
            --surface-hover: #16213e;
            --text: #eaeaea;
            --text-muted: #a0a0a0;
            --border: #2a2a4a;
            --required: #e03131;
            --recommended: #1971c2;
            --optional: #868e96;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid var(--border);
            margin-bottom: 30px;
        }}
        header h1 {{ font-size: 2rem; margin-bottom: 10px; }}
        header p {{ color: var(--text-muted); }}
        .main-grid {{
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 30px;
        }}
        @media (max-width: 1000px) {{
            .main-grid {{ grid-template-columns: 1fr; }}
        }}
        .graph-container {{
            background: var(--surface);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid var(--border);
        }}
        .graph-container h2 {{ margin-bottom: 15px; font-size: 1.3rem; }}
        .mermaid {{
            background: var(--bg);
            border-radius: 8px;
            padding: 15px;
            overflow: auto;
        }}
        .legend {{
            margin-top: 20px;
            padding: 15px;
            background: var(--surface-hover);
            border-radius: 8px;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .legend-item {{ display: flex; align-items: center; gap: 8px; }}
        .dot {{
            width: 14px; height: 14px; border-radius: 50%;
            display: inline-block;
        }}
        .dot.required {{ background: var(--required); }}
        .dot.recommended {{ background: var(--recommended); }}
        .dot.optional {{ background: var(--optional); }}
        .sidebar {{ display: flex; flex-direction: column; gap: 20px; }}
        .agent-card {{
            background: var(--surface);
            border-radius: 12px;
            padding: 20px;
            border-left: 4px solid var(--optional);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .agent-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}
        .agent-card.tier-required {{ border-left-color: var(--required); }}
        .agent-card.tier-recommended {{ border-left-color: var(--recommended); }}
        .agent-card.tier-optional {{ border-left-color: var(--optional); }}
        .agent-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }}
        .agent-header h3 {{ flex: 1; }}
        .tier-icon {{ font-size: 1.2rem; }}
        .tier-badge {{
            font-size: 0.75rem;
            text-transform: uppercase;
            padding: 3px 8px;
            border-radius: 4px;
            background: rgba(255,255,255,0.1);
        }}
        .description {{ color: var(--text-muted); margin-bottom: 10px; font-size: 0.95rem; }}
        .meta {{
            display: flex;
            gap: 15px;
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 10px;
        }}
        .children {{ font-size: 0.85rem; }}
        .children a {{
            color: var(--recommended);
            text-decoration: none;
        }}
        .children a:hover {{ text-decoration: underline; }}
        footer {{
            text-align: center;
            padding: 30px;
            color: var(--text-muted);
            font-size: 0.85rem;
            border-top: 1px solid var(--border);
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 agent-meta — Agenten-Visualisierung</h1>
            <p>Interaktive Übersicht aller Agenten und ihrer Beziehungen</p>
        </header>
        <div class="main-grid">
            <div class="graph-container">
                <h2>🕸️ Delegations-Graph</h2>
                <div class="mermaid">
{mermaid_code}
                </div>
                <div class="legend">
                    <div class="legend-item">
                        <span class="dot required"></span>
                        <span>required — Kern-Workflow</span>
                    </div>
                    <div class="legend-item">
                        <span class="dot recommended"></span>
                        <span>recommended — Standard-Qualität</span>
                    </div>
                    <div class="legend-item">
                        <span class="dot optional"></span>
                        <span>optional — Bei Bedarf</span>
                    </div>
                </div>
            </div>
            <div class="sidebar">
                <h2>📋 Agenten-Details</h2>
{''.join(agent_cards)}
            </div>
        </div>
        <footer>
            Generiert von agent-meta — <a href="agent-mindmap.md">Markdown-Version</a>
        </footer>
    </div>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            securityLevel: 'loose',
            flowchart: {{ useMaxWidth: true, htmlLabels: true, curve: 'basis' }}
        }});

        function scrollToAgent(id) {{
            const el = document.getElementById(id);
            if (el) {{
                el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                el.style.boxShadow = '0 0 20px rgba(77, 171, 247, 0.5)';
                setTimeout(() => el.style.boxShadow = '', 1500);
            }}
        }}
    </script>
</body>
</html>
"""


def generate_viz(agent_meta_root: Path, project_root: Path, config: dict, log: SyncLog, dry_run: bool):
    """Generiere alle Visualisierungs-Artefakte."""
    viz_cfg = config.get("viz", {})
    if not viz_cfg.get("enabled", False):
        return

    log.info("viz", "generiere Agenten-Visualisierung...")

    # 1. Hierarchie aufbauen (mit Provider-Config für korrekte Model-Auflösung)
    provider_config = load_providers_config(agent_meta_root)
    agents = build_agent_hierarchy(agent_meta_root, project_root, config, provider_config)
    log.info("viz", f"{len(agents)} Agenten gefunden")

    # 2. Output-Pfade bestimmen
    output_dir = project_root / viz_cfg.get("output_dir", "docs")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 3. Mermaid-Markdown
    md_path = output_dir / "agent-mindmap.md"
    mermaid_md = render_mermaid_mindmap(agents, config)
    if not dry_run:
        write_checked(md_path, mermaid_md, log=log, rel_label="agent-mindmap.md")
    else:
        log.info("viz", f"would write: {md_path}")

    # 4. Interaktives HTML
    html_path = output_dir / "agent-graph.html"
    html = render_interactive_html(agents, config)
    if not dry_run:
        write_checked(html_path, html, log=log, rel_label="agent-graph.html")
    else:
        log.info("viz", f"would write: {html_path}")

    log.info("viz", f"generiert: {md_path.name}, {html_path.name}")


# ---------------------------------------------------------------------------
# Dynamischer Modus: Event-Log-Management
# ---------------------------------------------------------------------------

VIZ_DIR = ".meta-viz"
EVENT_LOG = "events.jsonl"
SESSION_TIMEOUT_MIN = 5  # Konfigurierbar über project.yaml


def get_viz_dir(project_root: Path) -> Path:
    """Gibt das Viz-Verzeichnis zurück."""
    return project_root / VIZ_DIR


def get_event_log_path(project_root: Path, session_id: str | None = None) -> Path:
    """Gibt den Pfad zur Event-Log-Datei zurück.

    Wenn session_id gegeben: .meta-viz/events-<session_id>.jsonl
    Sonst: .meta-viz/events.jsonl (Legacy)
    """
    viz_dir = get_viz_dir(project_root)
    if session_id:
        return viz_dir / f"events-{session_id}.jsonl"
    return viz_dir / EVENT_LOG


def write_event(project_root: Path, event: dict, session_id: str | None = None, log: SyncLog | None = None):
    """Schreibe ein Event in das Session-Event-Log.

    Thread-safe via RLock (serializes concurrent reads/writes).
    """
    event.setdefault("ts", datetime.now(timezone.utc).isoformat())

    path = get_event_log_path(project_root, session_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with viz_lock:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as exc:
        if log:
            log.warn(f"viz-event: konnte nicht schreiben: {exc}")


def _tail_read_lines(path: Path, max_lines: int) -> list[str]:
    """Read approximately the last max_lines lines from a text file efficiently."""
    with open(path, "rb") as f:
        f.seek(0, 2)
        end = f.tell()
        pos = end
        chunks = []
        chunk_size = 8192

        while pos > 0 and sum(c.count(b"\n") for c in chunks) < max_lines:
            read_size = min(chunk_size, pos)
            pos -= read_size
            f.seek(pos)
            chunk = f.read(read_size)
            chunks.insert(0, chunk)

        full = b"".join(chunks)
        lines = full.decode("utf-8", errors="replace").splitlines()
        # Skip potential partial first line unless we read from start
        if pos > 0 and lines and not full.startswith(b"\n"):
            lines = lines[1:]
        return lines[-max_lines:]


def read_events(project_root: Path, session_id: str | None = None, since: datetime | None = None) -> list[dict]:
    """Lese Events aus dem Log.

    Thread-safe via RLock. Uses tail-read heuristic for large files when
    a 'since' filter is active to avoid reading the entire file.
    """
    path = get_event_log_path(project_root, session_id)
    if not path.exists():
        return []

    events = []
    try:
        with viz_lock:
            file_size = path.stat().st_size
            use_tail = since is not None and file_size > _TAIL_READ_THRESHOLD_BYTES

            if use_tail:
                lines = _tail_read_lines(path, _TAIL_READ_MAX_LINES)
            else:
                with open(path, "r", encoding="utf-8-sig") as f:
                    lines = f.readlines()

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                    if since:
                        ev_ts = datetime.fromisoformat(ev.get("ts", "").replace("Z", "+00:00"))
                        if ev_ts < since:
                            continue
                    events.append(ev)
                except (json.JSONDecodeError, ValueError):
                    continue

            # Safety fallback: if tail-read yielded too few events, read full file
            if use_tail and len(events) < _TAIL_READ_MIN_EVENTS:
                events = []
                with open(path, "r", encoding="utf-8-sig") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            ev = json.loads(line)
                            if since:
                                ev_ts = datetime.fromisoformat(ev.get("ts", "").replace("Z", "+00:00"))
                                if ev_ts < since:
                                    continue
                            events.append(ev)
                        except (json.JSONDecodeError, ValueError):
                            continue
    except Exception:
        pass
    return events


def list_sessions(project_root: Path) -> list[str]:
    """Liste alle Session-IDs (aus Dateinamen)."""
    viz_dir = get_viz_dir(project_root)
    if not viz_dir.exists():
        return []

    sessions = []
    for f in viz_dir.glob("events-*.jsonl"):
        stem = f.stem  # events-<session_id>
        if stem.startswith("events-"):
            sessions.append(stem[7:])
    return sorted(sessions, reverse=True)


def cleanup_old_sessions(project_root: Path, retention_days: int = 7, log: SyncLog | None = None, dry_run: bool = False):
    """Lösche Sessions die älter als retention_days sind.

    Sessions sind niemals Teil der Git-Ablage (via .gitignore).
    """
    viz_dir = get_viz_dir(project_root)
    if not viz_dir.exists():
        return

    cutoff = datetime.now(timezone.utc).timestamp() - (retention_days * 86400)
    removed = 0

    for f in viz_dir.glob("events-*.jsonl"):
        try:
            mtime = f.stat().st_mtime
            if mtime < cutoff:
                if not dry_run:
                    f.unlink()
                removed += 1
                if log:
                    log.info("viz-cleanup", f"gelöscht: {f.name}")
        except Exception as exc:
            if log:
                log.warn(f"viz-cleanup: {exc}")

    if log and removed:
        log.info("viz-cleanup", f"{removed} alte Session(s) entfernt")


def get_gitignore_entries() -> list[str]:
    """Gibt die gitignore-Einträge für den Viz-Modus zurück."""
    return [
        f"{VIZ_DIR}/",
        f"{VIZ_DIR}/events-*.jsonl",
        f"{VIZ_DIR}/session-reports/",
    ]


_VIZ_PY_APPEND = (
    "import json,os,sys;"
    "from datetime import datetime,timezone;"
    "d={0};"
    "d.setdefault('ts',datetime.now(timezone.utc).isoformat());"
    "p='.meta-viz/events.jsonl';"
    "os.makedirs(os.path.dirname(p),exist_ok=True);"
    "open(p,'a',encoding='utf-8').write(json.dumps(d,ensure_ascii=False)+'\\n')"
)


def _viz_bash_cmd(event_dict_literal: str) -> str:
    """Gibt den Bash-Befehl zurück der ein Event ans JSONL-Log anhängt.

    Funktioniert auf Windows (python) und Unix (python3/python).
    event_dict_literal: Python-Dict-Literal als String, z.B. "{'event':'agent_start',...}"
    """
    py = _VIZ_PY_APPEND.format(event_dict_literal)
    # Versuche python3, fallback python — beide plattformübergreifend
    return f'python3 -c "{py}" 2>/dev/null || python -c "{py}" 2>/dev/null'


def inject_viz_prompt_block(agent_content: str, role: str, provider: str,
                            viz_enabled: bool, model: str = "") -> str:
    """Injiziere den Visualization-Prompt-Block in einen Agenten.

    Nur wenn viz.mode == "dynamic" oder "full" und viz_enabled == True.
    Nutzt ausschließlich das `Bash`-Tool zum Schreiben — write_file/edit_file
    existieren in Claude Code nicht und führen dazu dass Agenten den Block ignorieren.
    """
    if not viz_enabled:
        return agent_content

    model_field = f",'model':'{model}'" if model else ""
    start_cmd = _viz_bash_cmd(
        f"{{'event':'agent_start','agent':'{role}','provider':'{provider}'{model_field}}}"
    )
    delegate_cmd = _viz_bash_cmd(
        f"{{'event':'delegate','from':'{role}','to':'ZIEL_AGENT'}}"
    )
    end_cmd_ok  = _viz_bash_cmd(
        f"{{'event':'agent_end','agent':'{role}','status':'success'}}"
    )
    end_cmd_err = _viz_bash_cmd(
        f"{{'event':'agent_end','agent':'{role}','status':'error','payload':{{'error':'FEHLERMELDUNG'}}}}"
    )

    block = f"""
## Visualization Reporting (Pflicht-Anweisung)

Der Visualisierungsmodus ist aktiv. Protokolliere deinen Status via **Bash-Tool** in `.meta-viz/events.jsonl`.

### Pflicht-Events — exakt diese Bash-Befehle ausführen

**1. Beim Start deiner Aufgabe (erstes was du tust):**
```bash
{start_cmd}
```

**2. Wenn du an einen anderen Agenten delegierst** (`ZIEL_AGENT` ersetzen):
```bash
{delegate_cmd}
```

**3. Wenn du fertig bist — Erfolg:**
```bash
{end_cmd_ok}
```

**3b. Wenn du fertig bist — Fehler** (`FEHLERMELDUNG` ersetzen):
```bash
{end_cmd_err}
```

### Regeln
- Diese Bash-Befehle **immer ausführen** — sie schreiben eine Zeile JSON ans Log.
- Kein anderes Tool verwenden — nur `Bash`.
- Timestamp wird automatisch gesetzt.
- Nie den Bash-Befehl weglassen oder überspringen.
"""

    return agent_content.rstrip() + "\n\n" + block.strip() + "\n"
