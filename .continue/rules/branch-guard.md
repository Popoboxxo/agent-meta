# Branch-Guard — Feature-Branch Pflicht

**Gilt für alle code-ändernden Aufgaben.**

## Pflicht vor dem ersten Edit

```bash
git branch --show-current
```

Auf `main`/`master` → Branch anlegen: `feat/<thema>` | `fix/<thema>` | `refactor/<thema>`

## Branch PFLICHT wenn

- Mehr als eine Datei geändert
- Inhaltliche Änderung an Agent-Templates, Rules, Scripts
- GitHub Issue bearbeitet
- `sync.py` ausgeführt wird

**Faustregel: sync.py ausführen oder >1 Datei anfassen → Branch.**

## Direkt auf main erlaubt (Ausnahmen)

Nur: Version-Bump (`VERSION`, `CHANGELOG.md`, `README.md`) | einzelner Tippfehler (1 Datei, 1 Zeile, User-Bestätigung) | Post-Merge-Pflege nach Review.

**NIE für:** Agent-Templates, Rules, Scripts — egal wie klein. Nie für Issue-Arbeit.

## Warum

Direkte Commits auf main propagieren Fehler sofort in alle Projekte beim nächsten Sync.
