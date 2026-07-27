---
type: "Concept"
title: "Konzept: GitHub Issue Lifecycle & Traceability"
description: "Verbindlicher Lebenszyklus für GitHub Issues: Referenzierung, automatische Schließung via PR/Commit Keywords und Abschlusskommentierung."
tags: [concept, workflow, github, status:active]
timestamp: "2026-07-27"
resource: "../../rules/1-generic/issue-lifecycle.md"
migrated_from: "rules/1-generic/issue-lifecycle.md"
---
# Konzept: GitHub Issue Lifecycle & Traceability

> Status: **Umgesetzt — aktiv**  
> Verwandt: [Commit-Konventionen](commit-conventions.md), [Development Workflow](architecture-dev-workflow.md)  
> Betroffen: `rules/1-generic/issue-lifecycle.md`, `agents/1-generic/bug-feature-analyzer.md`, `agents/1-generic/feedback.md`  

---

## 1. Problemstellung

Ohne klare Zuordnung zwischen Git-Commits/Pull-Requests und GitHub-Issues entstehen in Projekten "tote" oder verwaiste Issues. Entwickler schließen Tickets nicht manuell oder verpassen es, den Kontext der Lösung im Issue zu dokumentieren.

---

## 2. Der 3-Stufen Issue-Lebenszyklus

```
  1. Issue Triage & Referenzierung
               │
               ▼
  2. Implementierung & Auto-Closing Keyword (PR/Commit)
               │
               ▼
  3. Abschlusskommentierung & State Transition
```

### Stufe 1: Issue-Referenzierung
Vor Beginn der Arbeit wird das Issue von `bug-feature-analyzer` analysiert und eine Issue-Nummer (z.B. `#123`) ermittelt. Alle Entwicklungsarbeiten und Branches nehmen Bezug auf diese Nummer.

### Stufe 2: Automatische Schließung via Keywords
Im Pull Request Body oder im finalen Commit-Body MUSS das passende GitHub Auto-Close Keyword verwendet werden:

| Keyword | Anwendungsfall | Beispiel |
|---|---|---|
| `Fixes #<id>` | Behebung eines Bugs | `Fixes #123` |
| `Closes #<id>` | Fertigstellung eines Features oder Chores | `Closes #456` |
| `Resolves #<id>` | Lösung einer Aufgabe | `Resolves #789` |

### Stufe 3: Abschlusskommentierung
Nach der Durchführung aller Tests hinterlässt der zuständige Agent (z.B. `git` oder `feedback`) einen kurzen Abschlusskommentar im Issue mit einer Zusammenfassung der Änderungen, betroffenen Dateien und PR-Links.

---

## 3. Tooling & Automatisierung

Der `feedback`-Agent nutzt GitHub CLI (`gh issue comment`, `gh issue close`), um die Schnittstelle zwischen lokaler Agenten-Ausführung und dem GitHub-Issue-Tracker sauber zu schließen.