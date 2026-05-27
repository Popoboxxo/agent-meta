# agent-meta

agent-meta ist ein Git-Repository das als Submodul in Projekte eingebunden wird. Es stellt standardisierte Claude-Agenten-Templates bereit (1-generic, 2-platform, 0-external) und generiert via sync.py projektfertige Agenten-Dateien in .claude/agents/. Das Repo verwendet sich selbst — die hier generierten Agenten koordinieren die Weiterentwicklung von agent-meta.

<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on every sync. -->
<!-- Manual changes here will be overwritten. -->

Generiert von agent-meta v0.54.1 — `2026-05-27`
DoD-Preset: **rapid-prototyping** | REQ-Traceability: false | Tests: false | Codebase-Overview: false | Security-Audit: false

> **Einstiegspunkt:** Starte mit dem `orchestrator`-Agenten für alle Entwicklungsaufgaben — Ausnahmen siehe Abschnitt »Orchestrator — Universal Router«.

| Agent | Zuständigkeit |
|-------|--------------|
| `orchestrator` | Einstiegspunkt für ALLE Entwicklungsaufgaben — zerlegt komplexe Tasks und dispatched parallel |
<!-- agent-meta:managed-end -->

## Agents

Agent files are in `.gemini/agents/`. Use them with `@agent-name` in Gemini CLI.

## Project Setup

- **Build:** `python scripts/sync.py`
- **Test:** `(kein automatisiertes Test-System — manuelle Verifikation via --dry-run)`
- **Platform:** Python CLI (sync.py)
- **Runtime:** Python 3.x

## REGELN!!!!
Befoolge strikt und stoisch ALLES was ain /rules steht!
