# Gemini/Antigravity — Agent-Bootstrap bei Session-Start

## Warum ist das nötig?

Gemini/Antigravity verwendet **keine** dateibasierte Agent-Registry wie andere Plattformen.
Die Dateien in `.gemini/agents/` sind Textdateien — sie werden von der Runtime **nicht**
automatisch geladen oder als Subagenten registriert.

Stattdessen erfolgt die Agent-Registrierung über die API-Funktion `define_subagent`,
die bei **jedem** Session-Start erneut aufgerufen werden muss.

## Bootstrap bei Session-Start

**Führe folgende Schritte zu Beginn JEDER neuen Session aus:**

1. **Agent-Dateien einlesen:**
   Lies alle markdown-Dateien aus dem Verzeichnis `.gemini/agents/`.
   Jede Datei entspricht einem Agenten — der Dateiname (ohne `.md`) ist der Agenten-Name.

2. **Agenten registrieren:**
   Verwende `define_subagent` für jeden Agenten:
   ```
   define_subagent(
     name="<agent-name>",
     description="<kurze Beschreibung aus dem Agent-Template>",
     system_prompt="<vollständiger Inhalt der .md-Datei>"
   )
   ```

3. **Orchestrator zuerst registrieren:**
   Der `orchestrator`-Agent muss als **erster** registriert werden,
   da alle anderen Delegationen über ihn laufen.

4. **Nach vollständiger Registrierung:**
   Erst wenn alle Agenten registriert sind, können Entwicklungsaufgaben
   über den Orchestrator bearbeitet werden.

## Wichtige Hinweise

- **Ephemer:** Die Registrierung gilt NUR für die aktuelle Session. Bei einem neuen Chat
  müssen die Agenten erneut registriert werden.
- **Version:** Die Agenten-Dateien werden von `sync.py` generiert und aktuell gehalten.
  Nach einem `sync.py`-Lauf sind die Dateien auf dem neuesten Stand.
- **Ohne Bootstrap:** Ohne diese Registrierung existieren die Agenten NICHT in der
  Runtime — der Orchestrator kann nicht delegieren und der Hauptchat übernimmt
  alle Aufgaben selbst (unknown-fallback).
