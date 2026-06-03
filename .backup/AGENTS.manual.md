# agent-meta

agent-meta ist ein Git-Repository das als Submodul in Projekte eingebunden wird. Es stellt standardisierte Claude-Agenten-Templates bereit (1-generic, 2-platform, 0-external) und generiert via sync.py projektfertige Agenten-Dateien in .claude/agents/. Das Repo verwendet sich selbst — die hier generierten Agenten koordinieren die Weiterentwicklung von agent-meta.

## Agents

Agent files are in `.opencode/agents/`. Invoke them by name in opencode.

## Project Setup

- **Build:** `python scripts/sync.py`
- **Test:** `(kein automatisiertes Test-System — manuelle Verifikation via --dry-run)`
- **Platform:** Python CLI (sync.py)
- **Runtime:** Python 3.x
