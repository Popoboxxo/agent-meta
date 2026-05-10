# Agent-Visualisierung

> Anleitung für die Nutzung des agent-meta Visualisierungs-Features.

---

## Übersicht

das agent-meta Framework bietet zwei Visualisierungs-Features:

1. **Statische Mindmap** — Interaktiver Graph aller Agenten und ihrer Beziehungen
2. **Dynamischer Modus** — Session-basiertes Event-Logging und Reporting (opt-in)

---

## Feature 1: Statische Mindmap

### Aktivierung

In `.meta-config/project.yaml`:

```yaml
viz:
  enabled: true
  format: "mermaid"    # mermaid | html | both
  output_dir: "docs"   # wohin die Dateien geschrieben werden
```

Oder via CLI:

```bash
# Nur Visualisierung generieren
python .agent-meta/scripts/sync.py --viz-only

# Während des normalen Sync
python .agent-meta/scripts/sync.py --viz
```

### Ausgabe

Generiert zwei Dateien:

| Datei | Format | Beschreibung |
|-------|--------|--------------|
| `docs/agent-mindmap.md` | Mermaid | Für GitHub/Doku — wird nativ gerendert |
| `docs/agent-graph.html` | HTML + D3.js | Interaktive Seite mit Dark Mode |

### Inhalt

- **Mindmap** mit `orchestrator` als Root
- **Delegationen** als gerichtete Kanten
- **Farbcodierung** nach `workflow_tier`:
  - 🔴 required (rot)
  - 🔵 recommended (blau)
  - ⚪ optional (grau)
- **Agenten-Details** mit Beschreibung, Model, Memory

---

## Feature 2: Dynamischer Visualisierungsmodus

### Aktivierung

In `.meta-config/project.yaml`:

```yaml
viz:
  enabled: true
  mode: "dynamic"              # off | static | dynamic
  event_log: ".agent-meta/viz/events.jsonl"
  report:
    retention_days: 7          # Wie lange Sessions aufbewahrt werden
    session_timeout_min: 5     # Session-Ende nach X Minuten Inaktivität
```

### Wie es funktioniert

1. **Agenten schreiben Events** — Jeder generierte Agent bekommt einen Prompt-Block, der ihn auffordert, seine Aktionen in `events.jsonl` zu protokollieren.
2. **Sessions** — Events werden pro Session in separaten Dateien gespeichert (`events-<session_id>.jsonl`).
3. **Reports** — `viz-report.py` parst die Events und generiert Terminal/HTML-Reports.

### Event-Format (JSONL)

Jede Zeile ist ein gültiges JSON-Objekt:

```json
{"ts":"2026-05-10T19:00:00Z","event":"agent_start","agent":"orchestrator","provider":"Claude"}
{"ts":"2026-05-10T19:00:01Z","event":"delegate","from":"orchestrator","to":"developer"}
{"ts":"2026-05-10T19:01:00Z","event":"agent_end","agent":"developer","status":"success"}
```

**Event-Typen:**

| Event | Beschreibung |
|-------|--------------|
| `session_start` | Nutzer startet eine Aufgabe |
| `session_end` | Session beendet |
| `agent_start` | Agent beginnt mit Arbeit |
| `agent_end` | Agent fertig (`success`/`error`/`cancelled`) |
| `delegate` | Delegation von A an B |
| `tool_call` | Agent führt Tool aus |
| `log` | Freitext-Log |

### CLI-Tool: `viz-report.py`

```bash
# Live-Monitoring (aktualisiert alle 5 Sekunden)
python .agent-meta/scripts/viz-report.py --watch

# Einmaliger Report im Terminal
python .agent-meta/scripts/viz-report.py --session <id> --format terminal

# HTML-Report generieren
python .agent-meta/scripts/viz-report.py --session <id> --format html --output report.html

# Lokaler Webserver (optional — erfordert Flask)
python .agent-meta/scripts/viz-report.py --serve --port 8765

# Alte Sessions aufräumen
python .agent-meta/scripts/viz-report.py --cleanup --days 7
```

### Session-Management

- **Session-ID**: Wird automatisch aus dem Zeitstempel generiert (`YYYYMMDD-HHMMSS`)
- **Speicherort**: `.agent-meta/viz/events-<session_id>.jsonl`
- **Git**: Alle Viz-Dateien sind automatisch in `.gitignore` eingetragen
- **Aufräumen**: Alte Sessions werden nach `retention_days` automatisch gelöscht

---

## Gitignore

Folgende Einträge werden automatisch verwaltet:

```
.agent-meta/viz/
.agent-meta/viz/events-*.jsonl
.agent-meta/viz/session-reports/
```

---

## Wichtige Hinweise

1. **Statische Mindmap** funktioniert sofort — kein Opt-in nötig.
2. **Dynamischer Modus** ist opt-in — der Nutzer muss ihn aktivieren.
3. **Events werden vom LLM geschrieben** — Die Zuverlässigkeit hängt davon ab, ob der Agent den Prompt-Block befolgt.
4. **Keine IDE-Integration** — Das Framework beobachtet die IDEs nicht von außen. Stattdessen berichten die Agenten freiwillig von innen.
5. **Sessions sind flüchtig** — Sie werden nie committed und regelmäßig aufgeräumt.

---

## Architektur-Übersicht

```
agent-meta/
├── scripts/
│   ├── sync.py              # --viz, --viz-mode dynamic
│   ├── viz-report.py        # CLI Reports + optionaler Webserver
│   └── lib/
│       └── viz.py           # Generator + Event-Log-Management
├── docs/
│   ├── agent-mindmap.md     # GENERIERT (Mermaid)
│   └── agent-graph.html     # GENERIERT (Interaktiv)
└── .agent-meta/viz/         # SESSION-DATEN (gitignored)
    ├── events-*.jsonl
    └── session-reports/
```
