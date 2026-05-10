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

#### Stufe 2: PreToolUse Hook (Claude + Gemini)

Für Provider mit Hook-Infrastruktur (Claude Code, Gemini CLI) wird automatisch ein System-Hook registriert:

| Komponente | Pfad | Zweck |
|------------|------|-------|
| Quell-Hook | `hooks/1-generic/viz-log.sh` | Bash-Skript mit eingebettetem Python |
| Ziel-Hook | `.claude/hooks/viz-log.sh` | Kopiert von sync.py |
| Registrierung | `.claude/settings.json` | PreToolUse Event → intercept |

**Funktionsweise:**
1. Hook intercepted **jeden** Tool-Aufruf auf System-Ebene (vor Ausführung)
2. Extrahiert Tool-Name, Input-Vorschau, Agent-Name und Provider aus dem Hook-Kontext
3. Schreibt automatisch ein `tool_call`-Event in `.agent-meta/viz/events.jsonl`
4. Exit 0 — der Tool-Aufruf wird nicht blockiert

**Provider-Unterstützung:**

| Provider | Hook-Infrastruktur | Logging-Mechanismus |
|----------|-------------------|---------------------|
| Claude Code | ✅ PreToolUse Hooks | Hook + Pflicht-Prompt |
| Gemini CLI | ✅ PreToolUse Hooks | Hook + Pflicht-Prompt |
| Opencode | ❌ Keine Hooks | Nur Pflicht-Prompt |
| Continue | ❌ Keine Hooks | Nur Pflicht-Prompt |

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
echo '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","event":"session_start","agent":"user","payload":{"task":"Meine Aufgabe"}}' >> .agent-meta/viz/events.jsonl

# Agent starten
echo '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","event":"agent_start","agent":"orchestrator","provider":"Claude"}' >> .agent-meta/viz/events.jsonl

# Delegation
echo '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","event":"delegate","from":"orchestrator","to":"developer"}' >> .agent-meta/viz/events.jsonl

# Agent beenden
echo '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","event":"agent_end","agent":"developer","status":"success"}' >> .agent-meta/viz/events.jsonl

# Session beenden
echo '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","event":"session_end","agent":"user"}' >> .agent-meta/viz/events.jsonl
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
# Live-Monitoring (aktualisiert alle 5 Sekunden)
python .agent-meta/scripts/viz-report.py --watch

# Einmaliger Report im Terminal
python .agent-meta/scripts/viz-report.py --session <id> --format terminal

# HTML-Report generieren
python .agent-meta/scripts/viz-report.py --session <id> --format html --output report.html

# Lokaler Webserver (optional — erfordert Flask: `pip install flask`)
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
2. **Dynamischer Modus** ist aktiviert via `viz.enabled: true` und `mode: dynamic` oder `full`.
3. **Zweistufiges Logging** — Pflicht-Prompt-Block für alle Provider + PreToolUse Hook für Claude/Gemini.
4. **Hook ist conditional** — `viz-log.sh` wird nur kopiert/registriert wenn `viz.mode` == `dynamic` oder `full`. Bei Wechsel auf `off`/`static` automatisch entfernt.
5. **Keine IDE-Integration** — Das Framework beobachtet die IDEs nicht von außen. Stattdessen protokollieren die Agenten ihre Aktivitäten selbst (via Prompt) und Hooks intercepten Tool-Aufrufe (via System-Ebene).
6. **Sessions sind flüchtig** — Sie werden nie committed und regelmäßig aufgeräumt.

---

## Architektur-Übersicht

```
agent-meta/
├── scripts/
│   ├── sync.py              # --viz, --viz-mode dynamic
│   ├── viz-report.py        # CLI Reports + optionaler Webserver
│   └── lib/
│       ├── viz.py           # Generator + Event-Log-Management + inject_viz_prompt_block()
│       └── hooks.py         # sync_hooks: conditional viz-log Management
├── hooks/
│   └── 1-generic/
│       └── viz-log.sh       # PreToolUse Hook: intercept tool calls → events.jsonl
├── docs/
│   ├── agent-mindmap.md     # GENERIERT (Mermaid)
│   └── agent-graph.html     # GENERIERT (Interaktiv)
└── .agent-meta/viz/         # SESSION-DATEN (gitignored)
    ├── events.jsonl         # Haupt-Event-Log (append-only JSONL)
    ├── events-*.jsonl       # Session-spezifische Logs
    └── session-reports/     # Generierte Reports
```

### Event-Logging Pipeline

```
┌─────────────────────────────────────────────────────────┐
│                    Agent-Session                        │
│                                                         │
│  ┌──────────────┐    ┌──────────────────────────────┐  │
│  │ Pflicht-     │    │ PreToolUse Hook (Claude/     │  │
│  │ Prompt-Block │    │ Gemini)                      │  │
│  │ (alle Prov.) │    │                              │  │
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
│  │  .agent-meta/viz/events.jsonl    │                  │
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
