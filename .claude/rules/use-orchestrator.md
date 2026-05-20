---
alwaysApply: false
---
# Orchestrator — Pflichtnutzung

Einstiegspunkt für alle Entwicklungsaufgaben: `orchestrator`-Agent.

## Immer Orchestrator

Feature | Bugfix | Refactoring | Anforderungen | Tests | Audit | Release | Docker | Ideation | Analyse | Design

> **Der Orchestrator wählt automatisch das kosteneffizienteste Model-Tier** für jede Delegation (nano → fast → balanced → powerful → max). Nie direkt an teurere Agenten delegieren als nötig.

## Ausnahmen — direkt an

| Aufgabe | Agent |
|---------|-------|
| Git-Operationen (Commit, Push, Branch, Tag, PR) | `git` |
| Erkenntnisse speichern (Session-Ende) | `documenter` |
| agent-meta Upgrade / Sync / Extension / Meta-Fragen | `agent-meta-manager` |
| Projekt-Feedback als GitHub Issue einreichen | `feedback` |

## Was NIE direkt an andere Agenten geht

| Falsch | Richtig |
|--------|---------|
| "Wie funktioniert der Sync?" → `git` | → `agent-meta-manager` |
| "Ist mein Code gut?" → `validator` | → `orchestrator` (der entscheidet ob/wann `validator`) |
| "Erstelle ein Feature" → `feature` (direkt) | → `orchestrator` (der startet `feature`) |
| "Was bedeutet diese Rule?" → `validator` | → `agent-meta-manager` |
| "Analysiere die Codebase" → im Hauptchat | → `orchestrator` → `ideation` |
| "Entwirf ein Konzept" → im Hauptchat | → `orchestrator` → `ideation` |

## Hauptchat ohne Orchestrator

Branch-Guard manuell: `git branch --show-current` — auf `main` → Branch anlegen.
