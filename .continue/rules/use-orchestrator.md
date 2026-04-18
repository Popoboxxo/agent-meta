# Orchestrator — Pflichtnutzung

**Der `orchestrator`-Agent ist der einzige Einstiegspunkt für alle Entwicklungsaufgaben.**

## Wann den Orchestrator anfragen?

**Immer** — bei jeder der folgenden Aufgaben:

- Neues Feature implementieren
- Bugfix durchführen
- Refactoring
- Neue Anforderungen aufnehmen
- Tests schreiben oder ausführen
- Code-Qualitätsprüfung / Audit
- Release vorbereiten
- Docker-Stack ändern
- Ideen explorieren (Ideation → Requirements → Implementierung)

## Warum

Der Orchestrator kennt:
- Branch-Guard (kein direkter Commit auf main)
- DoD-Konfiguration des Projekts (welche Schritte aktiv sind)
- Welche Agenten wann in welcher Reihenfolge delegiert werden
- Parallelisierbare Schritte (∥)

Ohne Orchestrator: Branch-Guard wird übersprungen, DoD-Schritte fehlen,
falsche Agenten werden direkt angesprochen.

## Ausnahmen (kein Orchestrator nötig)

| Aufgabe | Direkt an |
|---------|-----------|
| Einzelner Git-Commit / Push / Tag | `git`-Agent |
| Einzelne Git-Frage | `git`-Agent |
| Erkenntnisse speichern | `documenter`-Agent |
| agent-meta Upgrade / Sync | `agent-meta-manager`-Agent |
| Feedback zu agent-meta einreichen | `meta-feedback`-Agent |

## Für den Hauptchat

Falls kein Orchestrator-Agent verwendet wird (direkte Arbeit im Hauptchat):
Den Branch-Guard **manuell** ausführen — `git branch --show-current` — bevor
die erste Datei angefasst wird. Ist der Branch `main`/`master` → Feature-Branch
anlegen (`feat/<thema>`, `fix/<thema>`, `refactor/<thema>`).
