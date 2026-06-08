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
| `docs/live-dashboard.html` | HTML + Cytoscape.js | **Echtzeit-Dashboard** für laufende Sessions |

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
  event_log: ".meta-viz/events.jsonl"
  report:
    retention_days: 7          # Wie lange Sessions aufbewahrt werden
    session_timeout_min: 5     # Session-Ende nach X Minuten Inaktivität
```

**Oder via CLI (überschreibt Config):**

```bash
python .agent-meta/scripts/sync.py --viz-mode dynamic
```

Gültige Werte für `mode`:
- `off` — Keine Visualisierung (default)
- `static` — Nur Mindmap generieren
- `dynamic` — Event-Logging in Agenten aktivieren
- `full` — Beides: Mindmap generieren + Event-Logging aktivieren

### Wie es funktioniert

Das Visualisierungs-System nutzt einen **zweistufigen Ansatz** für maximale Zuverlässigkeit:

#### Stufe 1: Pflicht-Prompt-Block (alle Provider)

Jeder generierte Agent erhält einen Prompt-Block am Ende seiner Definition, der ihn **verpflichtet**, seine Aktionen in `events.jsonl` zu protokollieren. Dieser Block wird nur injiziert wenn `viz.mode` auf `dynamic` oder `full` gesetzt ist.

**Protokollierte Events:**
- `agent_start` — Agent beginnt mit Arbeit
- `agent_end` — Agent fertig (success/error/cancelled)
- `delegate` — Delegation von A an B
- `tool_call` — Agent führt Tool aus

#### Stufe 2: System-Hook (Claude Code + Gemini CLI)

Für Provider mit Hook-Infrastruktur (Claude Code, Gemini CLI) wird automatisch ein System-Hook registriert.
Der Hook nutzt das kanonische Event `PreToolUse` — sync.py mapped dies automatisch auf das
provider-spezifische Äquivalent (Gemini: `BeforeTool`).

| Komponente | Pfad | Zweck |
|------------|------|-------|
| Quell-Hook | `hooks/1-generic/viz-log.sh` | Bash-Skript mit eingebettetem Python |
| Ziel-Hook (Claude) | `.claude/hooks/viz-log.sh` | Kopiert von sync.py |
| Ziel-Hook (Gemini) | `.gemini/hooks/viz-log.sh` | Kopiert von sync.py |
| Registrierung (Claude) | `.claude/settings.json` | PreToolUse Event → intercept |
| Registrierung (Gemini) | `.gemini/settings.json` | BeforeTool Event → intercept |

**Funktionsweise:**
1. Hook intercepted **jeden** Tool-Aufruf auf System-Ebene (vor Ausführung)
2. Extrahiert Tool-Name, Input-Vorschau, Agent-Name und Provider aus dem Hook-Kontext
3. Schreibt automatisch ein `tool_call`-Event in `.meta-viz/events.jsonl`
4. Exit 0 — der Tool-Aufruf wird nicht blockiert

**Provider-Unterstützung:**

| Provider | Hook-Infrastruktur | Hook-Event | Logging-Mechanismus |
|----------|-------------------|------------|---------------------|
| Claude Code | ✅ Hooks | PreToolUse | Hook + Pflicht-Prompt (MCP/CLI) |
| Gemini CLI | ✅ Hooks | BeforeTool | Hook + File-based Prompt |
| Opencode | ❌ Keine Hooks | — | Nur Pflicht-Prompt (MCP/CLI) |
| Continue | ❌ Keine Hooks | — | Nur Pflicht-Prompt (MCP/CLI) |

#### Conditional Hook-Management

Der `viz-log` Hook wird **nur** kopiert und registriert wenn `viz.mode` == `dynamic` oder `full`:

| viz.mode | viz-log.sh kopiert? | In settings.json registriert? |
|----------|---------------------|-------------------------------|
| `off` | ❌ | ❌ (stale wird gelöscht) |
| `static` | ❌ | ❌ (stale wird gelöscht) |
| `dynamic` | ✅ | ✅ (auto-enabled) |
| `full` | ✅ | ✅ (auto-enabled) |

Das Clean-up funktioniert vollautomatisch: Wenn `viz.mode` von `dynamic` auf `static` wechselt, erkennt `sync.py` den Hook als stale und entfernt ihn sowohl aus `.claude/hooks/` als auch aus `.claude/settings.json`.

### Event-Format (JSONL)

Jede Zeile ist ein gültiges JSON-Objekt:

```json
{"ts":"2026-05-10T19:00:00Z","event":"agent_start","agent":"orchestrator","provider":"Claude"}
{"ts":"2026-05-10T19:00:01Z","event":"delegate","from":"orchestrator","to":"developer"}
{"ts":"2026-05-10T19:01:00Z","event":"agent_end","agent":"developer","status":"success"}
```

### Manuelle Event-Erstellung

Wenn Agenten das automatische Logging nicht verwenden, können Events manuell in die JSONL-Datei geschrieben werden:

```bash
# Session starten
echo '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","event":"session_start","agent":"user","payload":{"task":"Meine Aufgabe"}}' >> .meta-viz/events.jsonl

# Agent starten
echo '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","event":"agent_start","agent":"orchestrator","provider":"Claude"}' >> .meta-viz/events.jsonl

# Delegation
echo '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","event":"delegate","from":"orchestrator","to":"developer"}' >> .meta-viz/events.jsonl

# Agent beenden
echo '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","event":"agent_end","agent":"developer","status":"success"}' >> .meta-viz/events.jsonl

# Session beenden
echo '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","event":"session_end","agent":"user"}' >> .meta-viz/events.jsonl
```

**Wichtig:** Jede Zeile muss ein gültiges JSON-Objekt sein. Nutze `>>` zum Anhängen.

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

### Commands (Schnellzugriff)

Folgende Commands stehen zur Verfügung (automatisch in `.claude/commands/` generiert):

| Command | Zweck |
|---------|-------|
| `/viz-mindmap` | Statische Mindmap generieren |
| `/viz-report` | Session-Report anzeigen (Terminal/HTML/JSON) |
| `/viz-watch` | Live-Monitoring starten |

### CLI-Tool: `viz-report.py`

```bash
# Live-Monitoring im Terminal (aktualisiert alle 5 Sekunden)
python scripts/viz-report.py --watch

# Einmaliger Report im Terminal
python scripts/viz-report.py --session <id> --format terminal

# HTML-Report generieren (einmalig)
python scripts/viz-report.py --session <id> --format html --output report.html

# Alte Sessions aufräumen
python scripts/viz-report.py --cleanup --days 7
```

### Live-Dashboard Server: `viz-server.py`

Für die **Echtzeit-Visualisierung** laufender Sessions:

```bash
# Server starten (oder stoppen falls bereits laufend)
python scripts/viz-server.py toggle

# Weitere Befehle
python scripts/viz-server.py start      # Im Hintergrund starten
python scripts/viz-server.py stop       # Beenden
python scripts/viz-server.py status     # Status prüfen
python scripts/viz-server.py restart    # Neustarten
python scripts/viz-server.py open       # Dashboard im Browser öffnen
```

**Features:**
- **Echtzeit-Graph** mit Cytoscape.js — Agenten als Nodes, Delegationen als animierte Kanten
- **Auto-Shutdown** nach 5 Minuten Inaktivität (keine neuen Events). Konfigurierbar:
  ```bash
  python scripts/viz-server.py start --timeout 600  # 10 Minuten
  ```
- **Keine externen Dependencies** — nutzt Python's eingebauten `wsgiref` Server
- **API-Endpunkte:**
  - `GET /api/state` — Berechneter Session-State (Agenten, Delegationen, Timeline)
  - `GET /api/events` — Rohe Events aus dem JSONL-Log
  - `GET /api/sessions` — Liste aller Session-IDs

### Session-Management

- **Session-ID**: Wird automatisch aus dem Zeitstempel generiert (`YYYYMMDD-HHMMSS`)
- **Speicherort**: `.meta-viz/events-<session_id>.jsonl`
- **Git**: Alle Viz-Dateien sind automatisch in `.gitignore` eingetragen
- **Aufräumen**: Alte Sessions werden nach `retention_days` automatisch gelöscht

---

## Gitignore

Folgende Einträge werden automatisch verwaltet:

```
.meta-viz/
.meta-viz/events-*.jsonl
.meta-viz/session-reports/
```

---

## Gemini / Antigravity — Einschränkungen & Workaround

Die Gemini/Antigravity-Plattform hat zwei Limitationen die das Event-Logging beeinflussen:

### Blockierte Mechanismen

| Mechanismus | Status | Grund |
|-------------|--------|-------|
| MCP `log_viz_event` Tool | ❌ Blockiert | Antigravity's Sandbox blockiert stdio-basierte MCP-Server |
| CLI `viz-logger.py` | ❌ Blockiert | Gemini's `code_execution` erfordert manuelle User-Bestätigung — unbrauchbar für Subagenten |
| System-Hook (`BeforeTool`) | ✅ Funktioniert | Hook läuft auf System-Ebene, nicht in der Sandbox |

### File-based Workaround

Für Gemini-Agenten injiziert sync.py einen **file-based Prompt-Block** statt des MCP/CLI-basierten Blocks.
Der Agent schreibt Event-JSONL-Zeilen direkt in `.meta-viz/events.jsonl` mittels seines Datei-Schreib-Tools.

**Vorteile:**
- Kein MCP-Server nötig (umgeht Sandbox-Blockade)
- Kein `code_execution` nötig (umgeht User-Confirmation)
- Gleiches Event-Format wie über MCP/CLI generierte Events

**Einschränkung:**
- Der Agent muss die Events selbstständig protokollieren (via Prompt-Anweisung).
  Bei MCP/CLI wird dies tool-seitig erledigt. Die Zuverlässigkeit hängt daher stärker
  von der Prompt-Compliance des LLMs ab.

---

## Wichtige Hinweise

1. **Statische Mindmap** funktioniert sofort — kein Opt-in nötig.
2. **Dynamischer Modus** ist aktiviert via `viz.enabled: true` und `mode: dynamic` oder `full`.
3. **Zweistufiges Logging** — Pflicht-Prompt-Block für alle Provider + System-Hook für Claude (`PreToolUse`) und Gemini (`BeforeTool`).
4. **Hook ist conditional** — `viz-log.sh` wird nur kopiert/registriert wenn `viz.mode` == `dynamic` oder `full`. Bei Wechsel auf `off`/`static` automatisch entfernt.
5. **Keine IDE-Integration** — Das Framework beobachtet die IDEs nicht von außen. Stattdessen protokollieren die Agenten ihre Aktivitäten selbst (via Prompt) und Hooks intercepten Tool-Aufrufe (via System-Ebene).
6. **Sessions sind flüchtig** — Sie werden nie committed und regelmäßig aufgeräumt.

---

## Architektur-Übersicht

```
agent-meta/
├── scripts/
│   ├── sync.py              # --viz, --viz-mode dynamic
│   ├── viz-report.py        # CLI Reports
│   ├── viz-server.py        # Live-Dashboard Server (start/stop/toggle)
│   └── lib/
│       ├── viz.py           # Generator + Event-Log-Management + inject_viz_prompt_block()
│       └── hooks.py         # sync_hooks: conditional viz-log Management
├── hooks/
│   └── 1-generic/
│       └── viz-log.sh       # System-Hook: intercept tool calls → events.jsonl (PreToolUse/BeforeTool)
├── docs/
│   ├── agent-mindmap.md     # GENERIERT (Mermaid)
│   ├── agent-graph.html     # GENERIERT (Interaktiv, statisch)
│   └── live-dashboard.html  # GENERIERT (Echtzeit, Cytoscape.js)
└── .meta-viz/         # SESSION-DATEN (gitignored)
    ├── events.jsonl         # Haupt-Event-Log (append-only JSONL)
    ├── events-*.jsonl       # Session-spezifische Logs
    ├── .server-pid          # PID des laufenden viz-server
    └── server.log           # Server-Log
```

### Event-Logging Pipeline

```
┌─────────────────────────────────────────────────────────┐
│                    Agent-Session                        │
│                                                         │
│  ┌──────────────┐    ┌──────────────────────────────┐  │
│  │ Pflicht-     │    │ System-Hook (Claude:       │  │
│  │ Prompt-Block │    │ PreToolUse / Gemini:       │  │
│  │ (alle Prov.) │    │ BeforeTool)                │  │
│  │              │    │  Intercept: JEDER Tool-Aufruf │  │
│  │ LLM schreibt │    │  → python3 extrahiert:       │  │
│  │ Events:      │    │    - tool_name               │  │
│  │ agent_start  │    │    - tool_input (preview)    │  │
│  │ agent_end    │    │    - agent_name, provider    │  │
│  │ delegate     │    │                              │  │
│  └──────┬───────┘    └──────────────┬───────────────┘  │
│         │                           │                   │
│         │         ┌─────────────────┘                   │
│         ▼         ▼                                     │
│  ┌──────────────────────────────────┐                  │
│  │  .meta-viz/events.jsonl    │                  │
│  │  (append-only JSONL, gitignored) │                  │
│  └──────────────────────────────────┘                  │
│                           │                             │
└───────────────────────────┼─────────────────────────────┘
                            ▼
              ┌─────────────────────────┐
              │  viz-report.py          │
              │  --watch / --format     │
              │  Terminal / HTML / JSON │
              └─────────────────────────┘
```
