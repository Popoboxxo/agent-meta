---
type: "Concept"
title: "Konzept: Definition of Done (DoD) & Presets Framework"
description: "Modular evaluierbares Definition of Done (DoD) Framework mit konfigurierbaren Presets (z.B. rapid-prototyping, production) und Prüfkriterien."
tags: [concept, quality, dod, status:active]
timestamp: "2026-07-27"
resource: "../../rules/1-generic/dod-criteria.md"
migrated_from: "rules/1-generic/dod-criteria.md"
---
# Konzept: Definition of Done (DoD) & Presets Framework

> Status: **Umgesetzt — aktiv**  
> Verwandt: [Circuit-Breaker, DoD-as-Gate](circuit-breaker-dod-gate-judge-pattern.md), [Commit-Konventionen](commit-conventions.md)  
> Betroffen: `rules/1-generic/dod-criteria.md`, `CLAUDE.md`, `.meta-config/project.yaml`  

---

## 1. Übersicht

Das **Definition of Done (DoD) Framework** stellt sicher, dass Entwicklungsaufgaben nicht vorzeitig als abgeschlossen deklariert werden. Es kombiniert unumstößliche Kernkriterien mit modular aktivierbaren Qualitätsprüfungen, die über projektspezifische **DoD-Presets** in `.meta-config/project.yaml` gesteuert werden.

---

## 2. Kernkriterien vs. Modulare Prüfpunkte

### Verbindliche Kernkriterien (Immer aktiv):
1. **Code Vollständigkeit**: Der Code ist vollständig geschrieben, ohne TBD/TODO-Stubs.
2. **Commit-Konventionen**: Alle Commits entsprechen den Conventional Commits.
3. **Keine Regressions**: Bestehende Funktionalitäten und Workflows wurden nicht gebrochen.

### Modulare Qualitätsbausteine (Über Flags steuerbar):

| Flag / Variable | Beschreibung | Standard bei `rapid-prototyping` | Standard bei `production` |
|---|---|---|---|
| `DOD_REQ_TRACEABILITY` | REQ-ID Pflicht in `docs/REQUIREMENTS.md` & Commit | `false` | `true` |
| `DOD_TESTS_REQUIRED` | Unit-/Integrationstests geschrieben & grün | `false` | `true` |
| `DOD_CODEBASE_OVERVIEW` | Aktualisierung von `CODEBASE_OVERVIEW.md` durch `documenter` | `false` | `true` |
| `DOD_SECURITY_AUDIT` | Durchführung eines Security-Audits vor Release | `false` | `true` |

---

## 3. DoD Presets

`agent-meta` bietet vordefinierte Presets für unterschiedliche Projektphasen:

```yaml
# In .meta-config/project.yaml
dod:
  preset: rapid-prototyping # Option: production | strict | rapid-prototyping
```

- **`rapid-prototyping`**: Minimale Overhead-Schranke für schnelle Exploration. Nur Kernkriterien aktiv.
- **`production`**: Maximale Qualitätssicherung. Alle Prüfpunkte (Tests, Traceability, Doku, Security) sind verpflichtend.

---

## 4. Enforcement durch Validator & Circuit-Breaker

Der `validator`-Subagent prüft bei der Abnahme einer Aufgabe den Code gegen die in `rules/1-generic/dod-criteria.md` hinterlegten Kriterien. Scheitert ein Kriterium, schlägt die Validierung fehl und das Ticket geht zur Überarbeitung an den `developer` zurück.