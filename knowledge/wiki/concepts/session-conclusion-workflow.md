---
type: "Concept"
title: "Konzept: Session-Conclusion Workflow & Documentation Sync"
description: "Standardisierter Session-Abschluss-Prozess zur Delegation von Dokumentations-Updates an den documenter-Agenten zur Pflege von CODEBASE_OVERVIEW.md."
tags: [concept, workflow, documentation, status:active]
timestamp: "2026-07-27"
resource: "../../rules/1-generic/session-conclusion.md"
migrated_from: "rules/1-generic/session-conclusion.md"
---
# Konzept: Session-Conclusion Workflow & Documentation Sync

> Status: **Umgesetzt — aktiv**  
> Verwandt: [Development Workflow](architecture-dev-workflow.md), [Definition of Done](definition-of-done.md)  
> Betroffen: `rules/1-generic/session-conclusion.md`, `agents/1-generic/documenter.md`  

---

## 1. Problemstellung

Am Ende umfangreicher Entwicklungs-Sessions oder nach Fertigstellung großer Features verändert sich die Codebase-Struktur dramatisch. Wird die Dokumentation (`CODEBASE_OVERVIEW.md`, `ARCHITECTURE.md`) nicht direkt im Anschluss aktualisiert, veraltet das Projektwissen schleichend.

---

## 2. Der Session-Abschluss Ablauf

```
  Entwicklungs-Task abgeschlossen (Code & Tests grün)
                         │
                         ▼
  Session-Conclusion-Rule triggert
                         │
                         ▼
  Delegation an documenter-Subagent
                         │
                         ▼
  documenter aktualisiert CODEBASE_OVERVIEW.md & ARCHITECTURE.md
                         │
                         ▼
  Finaler Session-Abschluss & PR/Merge
```

---

## 3. Aufgaben des `documenter`-Agenten beim Session-Abschluss

- Erfassung neu hinzugefügter Module, Skripte, CLI-Flags oder API-Endpunkte.
- Aktualisierung der Verzeichnisstruktur in `CODEBASE_OVERVIEW.md`.
- Festhalten von Architekturentscheidungen (ADRs) oder geänderten Datenflüssen.
- Bereinigung veralteter Pfad- und Komponentenreferenzen.