# agent-meta

agent-meta ist ein Git-Repository das als Submodul in Projekte eingebunden wird. Es stellt standardisierte Claude-Agenten-Templates bereit (1-generic, 2-platform, 0-external) und generiert via sync.py projektfertige Agenten-Dateien in .claude/agents/. Das Repo verwendet sich selbst — die hier generierten Agenten koordinieren die Weiterentwicklung von agent-meta.

<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on --update-ext. -->
<!-- Project-specific additions belong in the section BELOW this marker. -->

**Projekt:** agent-meta | **Plattform:** Python CLI (sync.py) | **Runtime:** Python 3.x
**Build:** `python scripts/sync.py` | **Test:** `python scripts/sync.py --validate`
<!-- agent-meta:managed-end -->

## Agent Rules

Agent context files are in `.continue/rules/`.
Continue loads all Markdown files in this directory automatically as context.
