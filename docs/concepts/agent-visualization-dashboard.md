# Konzept: Agent-Visualisierungs-Dashboard (AVD)

> Status: **Konzept-Entwurf** | Branch: `feat/agent-visualization-dashboard`
> Ziel: End-to-End-Visualisierung des agent-meta Frameworks für Endanwender

---

## 1. Vision & Zielsetzung

### Was der Endanwender sehen soll

Der Nutzer öffnet einen lokalen Webserver (z.B. `http://localhost:8765`) und sieht **in Echtzeit**:

1. **Welche Agenten existieren** in seinem Projekt — als interaktive Mindmap
2. **Welcher Agent gerade aktiv ist** — mit visuellem Status (idle → running → done → error)
3. **Wer wen delegiert** — Pfeile/Verbindungen zwischen Orchestrator und Subagenten
4. **Pro Provider** — Claude, Opencode, Gemini, Continue als separate Tabs/Ansichten
5. **Den zeitlichen Ablauf** — eine minimale Timeline der letzten Aktionen

### Referenz: Pixel Agents (vereinfacht)

Pixel Agents (bekannt aus dem AI-Agent-Observability-Space) zeigt:
- Agent-Nodes als Karten/Boxen
- Verbindungen für Delegation
- Echtzeit-Status-Farben
- Chat-ähnliche Timeline pro Agent

**Unser Scope ist bewusst reduziert:**
- Keine komplexe Graph-Engine
- Kein Backend-Cluster
- Keine Persistenz-Datenbank
- **Nur:** Ein kleiner Python-Webserver + statische HTML/JS + lokale Event-Datei

---

## 2. UI-Konzept (Wireframe-Logik)

### 2.1 Layout (Single-Page, drei Bereiche)

```
+-------------------------------------------------------------+
|  [agent-meta viz]  [Claude] [Opencode] [Gemini] [Continue]  |  <- Provider-Tabs
+-------------------------------------------------------------+
|                                                             |
|   +------------------+        +-------------------------+   |
|   |                  |        | Agent-Details           |   |
|   |   MINDMAP        |        | ----------------------- |   |
|   |   (Hauptbereich) |        | Name: orchestrator      |   |
|   |                  |        | Status: RUNNING         |   |
|   |   [orchestrator] |        | Model:  (inherited)     |   |
|   |      /    |      |        | Memory: -               |   |
|   |     /     |      |        | Tier:   required        |   |
|   | [dev]  [git] [doc]|       |                         |   |
|   |   |              |        | Last Action:            |   |
|   | [test]           |        | "delegated to developer"|   |
|   |                  |        | (2s ago)                |   |
|   +------------------+        +-------------------------+   |
|                                                             |
|   +-----------------------------------------------------+   |
|   | TIMELINE                                            |   |
|   | 19:12:34  orchestrator  ->  developer   "Fix bug #42"|  |
|   | 19:12:35  developer    ->  git          "Create branch"| |
|   | 19:12:40  developer    RUNNING          "Editing file.."| |
|   +-----------------------------------------------------+   |
+-------------------------------------------------------------+
```

### 2.2 Mindmap-Darstellung (MVP)

- **Zentrale Node:** `orchestrator` (immer in der Mitte)
- **Kinder-Nodes:** Alle Agenten die vom Orchestrator direkt delegiert werden
- **Enkel-Nodes:** Agenten die von anderen Agenten delegiert werden (z.B. developer -> tester)
- **Kanten:** Gerichtete Pfeile, farblich nach Status:
  - Grau = idle (noch nicht gestartet)
  - Gelb = running (aktiv)
  - Grün = done (erfolgreich)
  - Rot = error (fehlgeschlagen)
- **Node-Farben:** Nach `workflow_tier`:
  - Rot-Rand = required
  - Blau-Rand = recommended
  - Grau-Rand = optional

### 2.3 Provider-Tabs

Jeder Provider (Claude, Opencode, Gemini, Continue) hat einen eigenen Tab:
- Zeigt nur die Agenten die für diesen Provider generiert wurden
- Zeigt provider-spezifische Meta-Daten (z.B. `.claude/agents/` vs `.gemini/`)

### 2.4 Agenten-Details (On-Click)

Wenn man auf eine Node klickt:
- Name, Beschreibung, Model-Tier, Memory-Scope
- Letzte 5 Aktionen (Timeline-Filter)
- Frontmatter-Hints (aus der generierten Agent-Datei)

### 2.5 Timeline (Bottom-Bar)

- Einfache scrollbare Liste
- Format: `Zeitstempel | Quelle | Aktion | Payload`
- Max. 100 Einträge (FIFO, kein Speicher-Overhead)

---

## 3. Architektur

### 3.1 Komponenten-Diagramm

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BROWSER (Nutzer)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Mindmap-View │  │ Provider-Tabs│  │ Timeline & Agent-Details │  │
│  │ (D3.js/SVG)  │  │ (HTML/CSS)   │  │     (HTML/CSS/JS)        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP / WebSocket
┌──────────────────────────────┼──────────────────────────────────────┐
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              VISUALIZATION SERVER (Python)                    │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐  │  │
│  │  │ HTTP Server  │ │ WebSocket    │ │ Static File Handler  │  │  │
│  │  │ (Flask/FastAPI│ │ (Socket.io)  │ │ (HTML/JS/CSS)        │  │  │
│  │  └──────────────┘ └──────────────┘ └──────────────────────┘  │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐  │  │
│  │  │ Event Parser │ │ State Manager│ │ Project Scanner      │  │  │
│  │  │ (reads .log) │ │ (in-memory)  │ │ (reads agents/ dir)  │  │  │
│  │  └──────────────┘ └──────────────┘ └──────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    EVENT SOURCES                              │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐  │  │
│  │  │ sync.log     │ │ agent-events │ │ Filesystem Watcher   │  │  │
│  │  │ (bestehend)  │ │ (.jsonl)     │ │ (agents/ changes)    │  │  │
│  │  └──────────────┘ └──────────────┘ └──────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Datenfluss

1. **Statische Daten:** Server scannt bei Start `agents/1-generic/`, `agents/2-platform/`, `.claude/agents/` etc. und baut das Agenten-Modell auf.
2. **Dynamische Daten:** Agenten (oder ein Wrapper) schreiben Events in `agent-events.jsonl` im Projekt-Root.
3. **Server** parsed die JSONL-Datei und hält den State im Memory.
4. **Browser** polled alle 2 Sekunden (MVP) oder nutzt WebSocket (Phase 2).
5. **UI** rendert Mindmap + Timeline aus dem State.

---

## 4. Datenmodell

### 4.1 Statische Agenten-Struktur (aus agent-meta)

```json
{
  "agents": [
    {
      "id": "orchestrator",
      "name": "orchestrator",
      "provider": "Claude",
      "description": "Einstiegspunkt für alle Entwicklungsaufgaben",
      "tier": "required",
      "model": "",
      "memory": "",
      "source_file": "agents/1-generic/orchestrator.md",
      "generated_file": ".claude/agents/orchestrator.md",
      "children": ["developer", "feature", "git", "documenter"],
      "parents": []
    }
  ]
}
```

### 4.2 Dynamische Events (JSONL-Format)

Jede Zeile in `agent-events.jsonl`:

```json
{"ts": "2026-05-10T19:12:34Z", "event": "agent_start", "agent": "orchestrator", "provider": "Claude", "payload": {"task": "Fix bug #42"}}
{"ts": "2026-05-10T19:12:35Z", "event": "delegate", "from": "orchestrator", "to": "developer", "payload": {"prompt": "Fix bug #42 in auth.py"}}
{"ts": "2026-05-10T19:12:36Z", "event": "agent_start", "agent": "developer", "provider": "Claude"}
{"ts": "2026-05-10T19:13:10Z", "event": "agent_end", "agent": "developer", "status": "success", "payload": {"files_changed": ["auth.py"]}}
{"ts": "2026-05-10T19:13:11Z", "event": "agent_end", "agent": "orchestrator", "status": "success"}
```

**Event-Typen (MVP):**
- `agent_start` — Agent wurde gestartet
- `agent_end` — Agent ist fertig (`status`: success | error | cancelled)
- `delegate` — Delegation von A nach B
- `tool_call` — Agent führt ein Tool aus (optional)
- `log` — Freitext-Log vom Agenten

### 4.3 Laufzeit-State (Server-Memory)

```python
state = {
    "agents": {
        "orchestrator": {
            "status": "idle",  # idle | running | done | error
            "started_at": None,
            "ended_at": None,
            "current_task": None,
            "last_error": None,
        }
    },
    "edges": [
        {"from": "orchestrator", "to": "developer", "status": "active"}
    ],
    "timeline": [...],  # letzte N Events
    "providers": ["Claude", "Opencode"],
}
```

---

## 5. Technologie-Stack

| Komponente | Technologie | Begründung |
|---|---|---|
| Webserver | **Python `http.server` + Flask** | Keine externe Dependency nötig, oder FastAPI für moderne APIs |
| Realtime | **Server-Sent Events (SSE)** | Einfacher als WebSocket, reicht für unidirektionale Updates |
| Frontend | **Vanilla JS + D3.js (lightweight)** | Kein Build-Step, keine Framework-Complexity |
| Mindmap | **D3.js Force-Directed Graph** | Standard-Library, gut dokumentiert |
| Styling | **Pure CSS** | Kein Tailwind/Bootstrap nötig für rudimentäres UI |
| Event-Log | **JSONL-Datei** | Append-only, crash-safe, einfach zu parsen |
| Config | **YAML** | Konsistent mit agent-meta |

### Alternative (ultra-minimal)

Wenn wirklich **keine** Dependencies erlaubt sind:
- Webserver: `python -m http.server` + ein kleines CGI/WSGI-Skript
- Frontend: Vanilla JS + Canvas API (statt D3.js)
- Mindmap: Selbstgezeichnete SVG-Kreise und Linien

**Empfehlung:** Flask + D3.js ist der sweet spot zwischen Einfachheit und Funktion.

---

## 6. Integration mit agent-meta

### 6.1 Woher kommen die Events?

Das ist die **zentrale Herausforderung**. Agenten laufen in verschiedenen IDEs/Claude-Instanzen — wir können sie nicht direkt instrumentieren.

**Option A: Wrapper-Script (empfohlen für MVP)**

Ein neues Skript `scripts/viz-wrapper.py` das vor dem Agenten-Aufruf Events schreibt:

```python
# Nutzer startet nicht direkt den Agenten, sondern:
python scripts/viz-wrapper.py --agent orchestrator --task "Fix bug #42"
# → schreibt agent_start Event
# → ruft tatsächlichen Agenten auf
# → schreibt agent_end Event
```

**Nachteil:** Nutzer muss über Wrapper starten. Nicht transparent.

**Option B: Hook in Agenten-Templates**

Jedes generierte Agenten-Template bekommt im Prompt eine Pflicht:

```markdown
## Visualization
Bevor du mit der Aufgabe beginnst, schreibe in die Datei `agent-events.jsonl`:
```json
{"event": "agent_start", "agent": "orchestrator", ...}
```
```

**Nachteil:** LLM muss mitspielen. Unzuverlässig.

**Option C: Log-Parser (bestehende Infrastruktur)**

`sync.py` schreibt bereits `sync.log`. Wir erweitern das Logging-Format so dass es maschinenlesbar ist und parsen es.

**Nachteil:** Nur sync-Events, keine Laufzeit-Events.

**Option D: File-System Watcher + Heuristik**

- Watch auf `.claude/agent-memory/` oder `.opencode/`
- Heuristik: Wenn Dateien geschrieben werden → Agent war aktiv

**Nachteil:** Unzuverlässig, keine Delegations-Erkennung.

### 6.2 Empfohlene Hybrid-Lösung

**Phase 1 (MVP):** `viz-wrapper.py` + manuelle Events
- Wrapper für bewusste Nutzung
- Agenten können auch manuell Events schreiben (Tool-Aufruf)

**Phase 2:** Plugin/Extension für Claude Code / Opencode
- Wenn Claude Code ein offizielles Plugin-System hat
- Oder: MCP-Server der Events emitted

**Phase 3:** Log-Injection in agent-meta Templates
- Die generierten Agenten-Prompts enthalten standardisierte Log-Aufrufe
- Via MCP-Tool oder File-Write-Tool

### 6.3 Server-Start-Integration

Neue Dateien im Projekt:

```
agent-meta/
├── viz/                          <- NEU: Visualisierungs-Modul
│   ├── server.py                 <- Hauptserver
│   ├── static/
│   │   ├── index.html
│   │   ├── style.css
│   │   └── app.js
│   ├── scanner.py                <- Liest agents/ und .claude/agents/
│   ├── state.py                  <- In-Memory State + Event-Parser
│   └── templates/                <- Jinja2 Templates für HTML
├── scripts/
│   └── viz-wrapper.py            <- Optional: Wrapper für Events
└── agent-events.jsonl            <- Runtime-Event-Log (gitignored)
```

**Start:**
```bash
python viz/server.py
# oder
python -m viz.server --port 8765 --project .
```

---

## 7. API-Design (Server-Endpunkte)

### 7.1 REST-API (MVP)

```
GET  /api/agents              -> Liste aller Agenten (statisch)
GET  /api/agents/<id>         -> Details eines Agenten
GET  /api/state               -> Aktueller Laufzeit-State
GET  /api/timeline            -> Letzte N Events
GET  /api/providers           -> Liste aktiver Provider
POST /api/events              -> Manuelles Event einwerfen (für Wrapper)
GET  /                        -> Static index.html
```

### 7.2 Server-Sent Events (SSE)

```
GET /api/events/stream
```

Streamt JSON-Events an den Browser:
```
data: {"type": "state_update", "agent": "developer", "status": "running"}

data: {"type": "new_event", "event": {...}}
```

---

## 8. Mindmap-Rendering-Logik (D3.js)

### 8.1 Knoten-Positionierung

**Force-Directed Graph** (D3.js `forceSimulation`):
- Nodes = Agenten
- Links = Delegations-Beziehungen (aus Events + statische Defaults)
- `orchestrator` hat fixe Zentrum-Position oder höhere `fx`/`fy`-Attraktion

### 8.2 Node-Design

```svg
<g class="node" data-agent="developer">
  <circle r="30" fill="#2d2d2d" stroke-width="3" />
  <text>developer</text>
  <text class="status">RUNNING</text>
</g>
```

**Farbcodierung:**
- Füllung: `#2d2d2d` (dark mode, wie IDEs)
- Rand-Status: Grau (idle) → Gelb (running) → Grün (done) → Rot (error)
- Rand-Tier: Rot (required) → Blau (recommended) → Grau (optional)
- Provider-Icon: Kleines Logo/Badge in der Ecke

### 8.3 Interaktionen

- **Click Node:** Details rechts anzeigen
- **Double-Click Node:** Timeline filtern auf diesen Agenten
- **Hover:** Kurzbeschreibung als Tooltip
- **Drag:** Node verschieben (D3-Force-Layout pausiert)

---

## 9. MVP-Scope (Minimal Viable Product)

### Muss (für ersten funktionierenden Stand)

- [ ] Python-Server (Flask) mit statischen Dateien
- [ ] Mindmap mit D3.js Force-Graph
- [ ] Statische Agenten-Daten aus `agents/1-generic/` und `agents/2-platform/`
- [ ] Provider-Tabs (mindestens Claude + Opencode)
- [ ] Timeline-Komponente (statische Beispiel-Daten)
- [ ] Dark Mode UI (konsistent mit IDE-Themes)

### Kann (Phase 2)

- [ ] Echtzeit-Updates via SSE
- [ ] `viz-wrapper.py` für echte Events
- [ ] Agent-Details Panel mit Frontmatter-Daten
- [ ] Edge-Animationen (laufende Delegationen pulsen)
- [ ] Export als PNG/SVG

### Wird nicht gemacht (Out-of-Scope)

- [ ] Persistente Datenbank
- [ ] Multi-User-Support
- [ ] Authentifizierung
- [ ] Cloud-Deployment
- [ ] Komplexe Graph-Analytics (Pfad-Suche, etc.)

---

## 10. Offene Entscheidungen & Fragen an den Nutzer

### 10.1 Kritische Architektur-Entscheidungen

1. **Wie bekommen wir Laufzeit-Daten?**
   - A) Wrapper-Skript (Nutzer muss bewusst starten)
   - B) MCP-Server-Integration (wenn Provider MCP unterstützt)
   - C) Log-Datei-Parsing (nur historisch)
   - D) Zuerst nur statische Visualisierung, keine Echtzeit

2. **Soll das Dashboard Teil von agent-meta sein oder separates Repo?**
   - A) Submodul / Ordner in agent-meta (wie hier skizziert)
   - B) Eigenständiges Python-Package
   - C) Optionaler Branch/Feature-Flag in sync.py

3. **Provider-Visualisierung:**
   - Der Nutzer sagte "pro Provider" — meint er:
   - A) Pro LLM-Provider (Claude, Opencode, Gemini) eine Mindmap-Ansicht?
   - B) Oder pro Projekt-Provider (sharkord, homeassistant) eine Ansicht?

4. **Event-Quelle:**
   - Sollen die Agenten selbst Events schreiben (verlässt sich auf LLM)?
   - Oder ein externer Observer (Datei-Watcher)?

### 10.2 Technische Fragen

5. **Flask vs. FastAPI vs. stdlib http.server?**
   - Flask: Bekannt, einfach, viele Extensions
   - FastAPI: Modern, automatische API-Docs, async
   - stdlib: Zero-Dependencies

6. **Soll die Visualisierung nur lokal laufen oder auch remote?**
   - Lokaler Server reicht?
   - Oder soll man es irgendwann auf einem Server deployen können?

---

## 11. Nächste Schritte (Roadmap)

### Schritt 1: Konzept-Validierung (JETZT)
- [ ] Nutzer-Feedback zu diesem Dokument einholen
- [ ] Offene Fragen klären
- [ ] Architektur-Entscheidungen finalisieren

### Schritt 2: Prototyp (Server + Statische Mindmap)
- [ ] `viz/server.py` implementieren
- [ ] `viz/scanner.py` implementieren (liest agents/)
- [ ] `viz/static/index.html` + `app.js` mit D3.js
- [ ] Erste Mindmap mit statischen Agenten-Daten

### Schritt 3: Event-System
- [ ] `agent-events.jsonl` Format definieren
- [ ] `viz/state.py` implementieren
- [ ] SSE-Endpunkt `/api/events/stream`
- [ ] `scripts/viz-wrapper.py` (optional)

### Schritt 4: Polish
- [ ] Dark Mode Styling
- [ ] Provider-Tabs
- [ ] Timeline-Komponente
- [ ] Agent-Details Panel

### Schritt 5: Integration
- [ ] `sync.py` erweitern um `viz/` zu syncen
- [ ] Dokumentation in howto/
- [ ] Beispiel-Events für Demo-Modus

---

## 12. Appendix: Beispiel-Event-Fluss

**Szenario:** Nutzer sagt "Fix den Login-Bug"

```
[19:00:00] orchestrator    START   "Fix den Login-Bug"
[19:00:01] orchestrator    DELEGATE -> developer
[19:00:02] developer       START   "Analyze login flow"
[19:00:10] developer       TOOL    "read_file(auth.py)"
[19:00:15] developer       DELEGATE -> tester
[19:00:16] tester          START   "Write regression test"
[19:00:45] tester          END     SUCCESS
[19:00:46] developer       TOOL    "edit_file(auth.py)"
[19:01:00] developer       END     SUCCESS
[19:01:01] orchestrator    DELEGATE -> git
[19:01:02] git             START   "Create branch + commit"
[19:01:10] git             END     SUCCESS
[19:01:11] orchestrator    END     SUCCESS
```

**Visualisierung:**
- 19:00:00-19:01:11: orchestrator-Node gelb (running)
- 19:00:01: Edge orchestrator→developer erscheint, pulsiert
- 19:00:02-19:01:00: developer-Node gelb
- 19:00:15: Edge developer→tester erscheint
- 19:00:16-19:00:45: tester-Node gelb, dann grün
- 19:01:01: Edge orchestrator→git erscheint
- 19:01:11: orchestrator grün

---

*Konzept erstellt am 2026-05-10 im Branch `feat/agent-visualization-dashboard`*
