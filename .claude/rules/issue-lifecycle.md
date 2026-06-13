---
alwaysApply: false
---
# GitHub Issue Lifecycle

Wenn deine Arbeit mit einem GitHub Issue verknüpft ist, schließe es nach Abschluss ab.

Ist keine Issue-Nummer bekannt oder kein GitHub-Issue verknüpft → Issue-Phase überspringen. Dokumentiere: „Issue nicht verknüpft".

## Pflicht nach erledigter Arbeit

1. **Kommentiere das Issue** — kurze Zusammenfassung was implementiert wurde und in welchem Commit
2. **Schließe das Issue** — `gh issue close <number>`

```bash
# Kommentar + schließen in einem Schritt
gh issue close <number> --comment "Implemented in <commit>: <one-line summary>"

# Oder separat (wenn ausführlicherer Kommentar gewünscht)
gh issue comment <number> --body "..."
gh issue close <number>
```

## Wann gilt das?

- Nach jedem abgeschlossenen Feature, Bugfix oder Task der einem Issue zugeordnet ist
- Auch wenn kein PR erstellt wird (direkte Commits auf main)
- Der `git`-Agent kennt den vollständigen Workflow (inkl. Formulierungshilfe)

## Commit-Message-Referenz

Issue-Referenzen in Commit-Messages sind optional, aber empfohlen:
```
feat(REQ-042): add queue persistence  (closes #22)
```

## Fehlerbehandlung

- `gh` CLI nicht verfügbar oder nicht authentifiziert → **Stoppe** die Issue-Phase und melde den Fehler. Kein Issue-Status raten.
- `gh issue close` oder `gh issue comment` schlägt fehl → Fehler eindeutig melden, keine Annahmen über den Issue-Status treffen.

## Delegation

Für GitHub-Operationen → `git`-Agent
