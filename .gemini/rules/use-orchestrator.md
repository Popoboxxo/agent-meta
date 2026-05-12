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
| Feedback einreichen | `meta-feedback` |

## Hauptchat ohne Orchestrator

Branch-Guard manuell: `git branch --show-current` — auf `main` → Branch anlegen.
