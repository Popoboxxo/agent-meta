# Orchestrator — Pflichtnutzung

Einstiegspunkt für alle Entwicklungsaufgaben: `orchestrator`-Agent.

## Immer Orchestrator

Feature | Bugfix | Refactoring | Anforderungen | Tests | Audit | Release | Docker | Ideation

## Routing-Signale — wann welcher Agent

### Explorative / Research-Fragen → `ideation`

Direkt an `ideation` delegieren (nicht inline beantworten) wenn:

- Frage beginnt mit "Wie könnte ich...", "Was wäre wenn...", "Welche Möglichkeiten gibt es..."
- Expliziter Recherche-Wunsch: "Recherchiere...", "Suche Beispiele...", "Vergleiche Ansätze..."
- WebSearch/WebFetch nötig (externe Quellen, Best Practices, andere Projekte)
- Frage hat keinen konkreten Implementierungs-Scope (kein Ticket, kein Code-Pfad)

**Grenze:** Wenn eine Frage direkt in einem laufenden Task beantwortet werden kann (≤2 Sätze, kein Research nötig) → inline. Sonst → `ideation`.

### Log-Analyse → `log-analyzer`

Bei: Fehler-Logs, Stack Traces, Produktions-Incidents, Monitoring-Daten analysieren.

### Performance → `performance`

Bei: "ist langsam", "zu viel Memory", "Bottleneck finden", "profilen".

### Code-Review → `reviewer`

Bei: PR-Review, "schau dir den Code an", "ist das gut implementiert?", vor dem Merge.

## Ausnahmen — direkt an

| Aufgabe | Agent |
|---------|-------|
| Git-Commit / Push / Tag / Frage | `git` |
| Erkenntnisse speichern | `documenter` |
| agent-meta Upgrade / Sync | `agent-meta-manager` |
| Projekt-Feedback einreichen (Bugs, Features) | `feedback` |
| agent-meta-Feedback einreichen | `meta-feedback` |
| Neues Feature (≥3 Dateien, Lifecycle) | `feature` → delegiert an `developer` |

> **`feature` vs. `developer`:**
> - `feature` koordiniert den gesamten Lifecycle (Branch, REQ, Dev, Test, PR) — implementiert **nichts** selbst
> - `developer` implementiert und fixt direkt
> - Bei parallelen unabhängigen Teilaufgaben: mehrere `developer` via Map-Reduce statt einem `feature`
> - Faustregel: eine Datei → selbst | 2-3 Dateien → `developer` | Lifecycle nötig → `feature`

## Hauptchat ohne Orchestrator

Branch-Guard manuell: `git branch --show-current` — auf `main` → Branch anlegen.
