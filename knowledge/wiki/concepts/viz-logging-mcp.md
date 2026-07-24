---
type: "Concept"
title: "Konzept: Visualisierung & Logging Simplifizierung (MCP / CLI Fallback)"
description: "Dieses Dokument beschreibt die Architektur-Überarbeitung des agent-meta Logging- und Visualisierungs-Mechanismus."
tags: [concept]
timestamp: "2026-06-14T15:13:32Z"
resource: "../../sources/docs/concepts/viz-logging-mcp.md"
migrated_from: "docs/concepts/viz-logging-mcp.md"
---
# Konzept: Visualisierung & Logging Simplifizierung (MCP / CLI Fallback)

Dieses Dokument beschreibt die Architektur-Überarbeitung des `agent-meta` Logging- und Visualisierungs-Mechanismus.

## Implementierungsstatus (verifiziert 2026-06-14)

**Umgesetzt:**
- `scripts/viz-logger.py`: CLI + MCP (stdio + HTTP/SSE), `.meta-viz/events.jsonl`
- Cross-Process-File-Locking: `write_event_safe` (atomares `O_EXCL`-Lockfile + Retry + Cleanup) — nicht nur `threading`
- Handshake-Tracking: Event-Felder `task_id`, `caller`, `target`, `from`, `to` (`viz-logger.py`)
- Prompt-Injection via `inject_viz_prompt_block` (`scripts/lib/viz.py`)

## Problemstellung
Bislang wurde das Event-Logging der Agenten (`agent_start`, `delegate`, `agent_end`) durch das Injizieren sehr langer, plattformabhängiger Inline-Python-Skripte (`python3 -c "import json,os,sys;..."`) in die System-Prompts realisiert. 
Dies führte zu:
- Massivem Prompt-Bloat in den generierten `.md`-Templates.
- Problemen bei Providern, die bei Terminal/Bash-Ausführungen nach Bestätigung fragen (Copilot, Continue, Claude Code), was zu "Prompt Fatigue" führte.
- Fehleranfälligkeit bei OS-Abweichungen (Windows/PowerShell vs. Linux/Bash).
- Unzuverlässigem Tracking von Delegationspfaden, da eingehende Delegationen nicht explizit mit ausgehenden verknüpft waren.
- Race-Conditions beim gleichzeitigen Schreiben in `events.jsonl` durch parallel laufende Subagenten.

## Architektonische Lösung

### 1. Nativer MCP-Server & CLI-Fallback (`scripts/viz-logger.py`)
Das Logging wird in ein eigenständiges Python-Skript ausgelagert. 
Dieses Skript fungiert zweigleisig:
- **MCP-Server:** Stellt das native Tool `log_viz_event` bereit. Dies ist der primäre Weg für IDE-integrierte Provider. Tools laufen leise im Hintergrund und verhindern lästige Bestätigungs-Popups.
- **CLI-Tool (Fallback):** Kann über OS-agnostische Befehle (z.B. via `run_command` oder `Bash`) mit Parametern aufgerufen werden (`python scripts/viz-logger.py --event agent_start ...`).

### 2. Robustes File-Locking
Um `PermissionError` unter Windows (bei parallelen Worker-Agenten) zu verhindern, implementiert das `viz-logger.py` Skript OS-übergreifendes File-Locking (z.B. via `msvcrt` auf Windows / `fcntl` auf Unix) bzw. eine Retry-Schleife mit Exponential Backoff. Die Threadsicherheit in `viz.py` bleibt für Server-Lesezugriffe bestehen.

### 3. Explizites Handshake-Tracking für Delegationen
Um den Graphen verlässlich zu zeichnen, müssen eingehende und ausgehende Pfade via `task_id` und `caller`/`target` verknüpft werden:
- **Outgoing (Orchestrator delegiert):**
  `log_viz_event(event="delegate_out", target="developer", task_id="uuid-1234")`
- **Incoming (Subagent startet):**
  `log_viz_event(event="agent_start", caller="orchestrator", task_id="uuid-1234")`
- **Return (Subagent beendet Task):**
  `log_viz_event(event="agent_end", target="orchestrator", status="success")`

### 4. Prompt-Optimierung & Concurrency
Die Injection-Logik in `scripts/lib/viz.py` wird stark vereinfacht. Die Agenten erhalten lediglich eine kurze Instruktion, das Tool (oder den CLI-Befehl) zu nutzen.
Um Latenzen und unnötige Turns zu vermeiden, wird im Prompt explizit die **gleichzeitige Ausführung (Concurrent Tool Execution)** gefordert: Der Agent ruft das Logging-Tool im selben Turn auf, in dem er z.B. eine Delegation via `send_message` durchführt.

## Umsetzungsschritte
1. Erstellen von `scripts/viz-logger.py` mit MCP- und CLI-Unterstützung sowie Cross-Process File Locking.
2. Anpassen der Injektion in `scripts/lib/viz.py` (`inject_viz_prompt_block`), um nur noch die kurzen Instruktionen auszugeben.
3. Neugenerierung der Agent-Templates über `scripts/sync.py`.
