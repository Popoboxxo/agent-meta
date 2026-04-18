# Branch-Guard — Feature-Branch Pflicht

**Gilt für alle code-ändernden Aufgaben — Agenten und Hauptchat.**

## Pflicht vor jeder Implementierung

Vor Features, Bugfixes und Refactorings **immer zuerst** den Branch prüfen:

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

## Ausnahmen (direkte Commits auf main erlaubt)

- `chore:` — Wartung, Dependencies, Config, Version-Bumps
- `docs:` — Reine Doku-Änderungen ohne Code
- Einzeiliger Fix mit **expliziter User-Bestätigung**

## Warum

Direkte Commits auf main bei größeren Changes verhindern Review, machen Rollback schwerer
und verstoßen gegen den Team-Workflow (PR → Review → Merge).
