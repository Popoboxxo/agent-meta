---
type: "Concept"
title: "Konzept: Branch-Guard-Strategie & Submodul-Schutz"
description: "Verbindliche Regel zur Nutzung von Feature-Branches (feat/, fix/, chore/) und Schutz des main/master-Branches vor direkten Commits bei sync.py-Läufen oder Multi-File-Edits."
tags: [concept, workflow, git, status:active]
timestamp: "2026-07-27"
resource: "../../rules/1-generic/branch-guard.md"
migrated_from: "rules/1-generic/branch-guard.md"
---
# Konzept: Branch-Guard-Strategie & Submodul-Schutz

> Status: **Umgesetzt — aktiv**  
> Verwandt: [Commit-Konventionen](commit-conventions.md), [Development Workflow](architecture-dev-workflow.md)  
> Betroffen: `rules/1-generic/branch-guard.md`, `AGENTS.md`  

---

## 1. Grundprinzip

Die **Branch-Guard-Strategie** schützt Hauptbranches (`main` oder `master`) vor ungetesteten, fehlerhaften oder unvollständigen Code-Änderungen. 

Keine direkten Code-Mutationen, Template-Anpassungen oder Skriptausführungen dürfen auf `main`/`master` vorgenommen werden. Alle Entwicklungsarbeiten müssen in isolierten Feature-Branches durchgeführt werden.

---

## 2. Naming-Conventions für Branches

Branches müssen nach folgendem Conventional-Branch-Schema benannt werden:

| Präfix | Verwendungszweck | Beispiel |
|---|---|---|
| `feat/` | Neue Features, Agenten-Rollen oder Framework-Funktionen | `feat/new-quality-auditor` |
| `fix/` | Bugfixes an Skripten, Templates oder Rules | `fix/pal-variable-replacement` |
| `chore/` | Refactoring, Doku-Updates, Dependency-Bumps | `chore/sync-pipeline-update` |

---

## 3. Erweiterte Branch-Guard-Regeln für `agent-meta`

Da `agent-meta` als Git-Submodul in zahlreiche Kunden- und Eigenprojekte eingebunden wird, haben Fehler auf dem `main`-Branch eine hohe Schadenswirkung: Ein fehlerhafter Sync-Lauf würde sofort in alle konsumierenden Repositories propagiert werden.

### Die agent-meta Erweiterungs-Regel:
- **`sync.py` ausführen** oder **mehr als 1 Datei anpassen** $\rightarrow$ **PFLICHT zur Branch-Erstellung.**
- **Keine Ausnahmen für schnelle Fixes:** Selbst kleinste Änderungen an `sync.py`, `1-generic/` Templates oder `rules/` dürfen niemals direkt auf `main` committet werden.

---

## 4. Zusammenspiel mit Subagenten & Git-Agent

1. Bei Beginn einer Entwicklungsaufgabe prüft der `orchestrator` oder `main_chat` den aktuellen Branch-Status.
2. Befindet sich das Git-Repo auf `main`/`master`, wird über den `git`-Agenten unverzüglich ein Feature-Branch angelegt.
3. Erst nach erfolgreicher Validierung und Prüfung der Definition of Done (DoD) erfolgt ein Merge bzw. PR.