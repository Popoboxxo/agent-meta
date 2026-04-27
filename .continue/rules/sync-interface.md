---
alwaysApply: false
---
# agent-meta — sync.py Interface

`sync.py` ist der einzige Weg Agenten zu generieren. Nie direkt in `.claude/agents/` schreiben.

Vollständige Referenz (Flags, sync.log, Modulstruktur):
→ `.agent-meta/agents/1-generic/_wf-sync-interface.md`

## Branch-Guard-Erweiterung für agent-meta

Zusätzlich zu den generischen Branch-Guard-Regeln gilt hier:

- `sync.py` ausführen → immer Branch (Sync propagiert in alle Projekte)

**Faustregel: sync.py ausführen oder >1 Datei anfassen → Branch.**

**NIE direkt auf main:** sync.py-Läufe, Template-Änderungen, Rule-Änderungen — egal wie klein.

## Warum

Direkte Commits auf main propagieren Fehler sofort in alle Projekte beim nächsten Sync.
