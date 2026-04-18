# Lifecycle-Tasks — Ausstehende Aufgaben prüfen

Beim Start einer neuen Konversation: prüfe ob `.claude/pending-tasks.md` existiert.

## Pflicht beim Konversations-Start

```bash
# Prüfen ob Lifecycle-Tasks ausstehen
test -f .claude/pending-tasks.md && cat .claude/pending-tasks.md
```

Wenn die Datei existiert und offene Tasks enthält (`- [ ]`):

1. Informiere den User:
   > "Es gibt ausstehende Lifecycle-Tasks aus einem Git-Event. Soll ich diese jetzt bearbeiten?"

2. Zeige die offenen Tasks kompakt (Agent + Aufgabe, eine Zeile je Task).

3. Wenn User bestätigt → delegiere Tasks an die genannten Agenten.

4. Nach Erledigung aller Tasks: lösche `.claude/pending-tasks.md`.

## Wann diese Rule greift

Lifecycle-Tasks entstehen wenn der `lifecycle-check`-Hook aktiv ist und ein konfiguriertes
Git-Event erkannt wird (z.B. Release-Tag, Version-Bump, Merge).

Konfiguration in `.meta-config/project.yaml`:
```yaml
lifecycle-triggers:
  on-release:
    - agent: documenter
      task: "Update CODEBASE_OVERVIEW.md and ARCHITECTURE.md for this release."
  on-merge:
    - agent: validator
      task: "Quick DoD check for merged changes."
```

## Wenn keine Tasks offen sind

Datei existiert nicht oder enthält keine `- [ ]` Zeilen → nichts tun.
Datei nicht committen — sie ist gitignored (`.claude/pending-tasks.md`).
