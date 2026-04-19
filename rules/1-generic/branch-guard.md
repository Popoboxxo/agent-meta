# Branch-Guard — Feature-Branch Pflicht

**Gilt für alle code-ändernden Aufgaben — Agenten und Hauptchat.**

## Pflicht vor jeder Implementierung

Vor dem ersten Datei-Edit **immer zuerst** den Branch prüfen:

```bash
git branch --show-current
```

| Aktueller Branch | Aktion |
|-----------------|--------|
| `main` / `master` | **Feature-Branch anlegen, dann weiter** |
| Bereits passender Feature-Branch | Weiter |

**Branch-Naming:**
- Neues Feature → `feat/<thema>`
- Bugfix → `fix/<thema>`
- Refactoring → `refactor/<thema>`

---

## Entscheidungsbaum: Branch nötig oder nicht?

```
Ändere ich mindestens eine Datei?
│
├─ NEIN → kein Branch nötig (reine Analyse, Erklärung, Recherche)
│
└─ JA → Wie viele Dateien / wie groß?
        │
        ├─ Mehrere Dateien ODER inhaltliche Änderung an Logik/Verhalten/Templates
        │   → BRANCH PFLICHT — unabhängig vom Commit-Typ
        │
        └─ Genau eine Datei, eine Zeile, trivialer Tippfehler/Formatierung
            → Direkt auf main erlaubt, ABER nur mit expliziter User-Bestätigung
```

---

## Branch PFLICHT — diese Situationen immer mit Branch

| Situation | Warum |
|-----------|-------|
| GitHub Issue(s) bearbeiten | Issues sind Aufgaben, egal ob feat/fix/chore |
| Bugfix an Templates, Agents, Rules, Scripts | Inhaltliche Änderung = Review nötig |
| Neues Feature, neue Datei, neue Rolle | Klar |
| Refactoring (auch einzeilig wenn mehrere Stellen) | Rollback-Sicherheit |
| Mehrere Dateien gleichzeitig ändern | Immer — egal wie trivial einzeln |
| Änderung an generiertem Output (`sync.py` ausführen) | Sync propagiert in alle Projekte |

**Faustregel: Wenn du `sync.py` ausführst oder mehr als eine Datei anfasst → Branch.**

---

## Direkt auf main erlaubt — nur diese Situationen

| Situation | Bedingung |
|-----------|-----------|
| Version-Bump (`VERSION`, `CHANGELOG.md`, `README.md`) | Nur diese drei Dateien, kein Logik-Code |
| Dependency-Update (`package.json`, `requirements.txt`) | Nur Versions-Zeilen, kein Logik-Code |
| Einzelner Tippfehler / Formatierung | Genau eine Datei, eine Zeile, **explizite User-Bestätigung** |
| `chore:` Commit nach abgeschlossenem Feature-Branch-Merge | Bereits gereviewed — Post-Merge-Pflege |

**Diese Ausnahmen gelten NIE für:**
- Inhaltliche Änderungen an Agent-Templates, Rules oder Scripts — egal wie klein
- Änderungen die `sync.py` auslösen oder auslösen sollten
- Jede Arbeit die aus einem Issue stammt

---

## Warum

Direkte Commits auf main bei inhaltlichen Changes verhindern Review, machen Rollback schwerer
und propagieren Fehler sofort in alle Projekte beim nächsten Sync.
