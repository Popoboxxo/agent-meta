---
type: "Concept"
title: "Konzept: Lifecycle-Tasks & Config Reconciliation Hooks"
description: "Event-gesteuerte Lifecycle-Task-Verwaltung über pending-tasks.md und PostToolUse-Hooks (z.B. sync-on-config-change) zur automatischen System-Reconciliation."
tags: [concept, automation, hooks, status:active]
timestamp: "2026-07-27"
resource: "../../rules/1-generic/lifecycle-tasks.md"
migrated_from: "rules/1-generic/lifecycle-tasks.md"
---
# Konzept: Lifecycle-Tasks & Config Reconciliation Hooks

> Status: **Umgesetzt — aktiv**  
> Verwandt: [CLI Reference: sync.py](../entities/cli-reference.md), [Provider-Agnostic Policy](provider-agnostic-policy.md)  
> Betroffen: `rules/1-generic/lifecycle-tasks.md`, `hooks/1-generic/sync-on-config-change.sh`, `.meta-config/project.yaml`  

---

## 1. Problemstellung & Zweck

Wenn Konfigurationsdateien (wie `.meta-config/project.yaml`) während einer Arbeits-Session bearbeitet werden, entstehen Diskrepanzen zwischen der gespeicherten Konfiguration und den in `.claude/agents/` (bzw. `.gemini/agents/`) generierten Agenten-Prompts. 

Das **Lifecycle-Task- und Hook-System** sorgt für eine automatische Reconciliation (Abgleich) ohne manuelle Entwickler-Eingriffe.

---

## 2. Der `pending-tasks.md` Workflow

1. **Datei-Standort**: Dynamisch injiziert via `{{PENDING_TASKS_FILE}}` (z.B. `.claude/pending-tasks.md` oder `.gemini/pending-tasks.md`).
2. **Session-Start Check**: Zu Beginn jeder Agenten-Session prüft der Einstiegs-Agent, ob die Datei existiert und unerledigte Checkbox-Einträge (`- [ ]`) enthält.
3. **User-Prompt**: Enthält die Datei offene Tasks, fragt der Agent den Nutzer, ob diese sofort ausgeführt oder delegiert werden sollen.
4. **Cleanup**: Nach Erledigung wird die Datei gelöscht. Sie ist temporär und darf **niemals committet** werden.

---

## 3. Der `sync-on-config-change` Hook

Ein zentrales Element ist der Shell-Hook in `hooks/1-generic/sync-on-config-change.sh`:

```
   User/Agent ändert .meta-config/project.yaml
                       │
                       ▼ (PostToolUse Event)
   Hook sync-on-config-change.sh schlägt an
                       │
                       ▼
   Schreibt Pending-Task in .claude/pending-tasks.md:
   "- [ ] Re-run sync.py — project.yaml has changed."
                       │
                       ▼
   agent-meta-manager führt beim nächsten Schritt sync.py aus
```

---

## 4. Konfiguration in `project.yaml`

Hooks und Triggers lassen sich in der Konfigurationsdatei steuern:

```yaml
lifecycle-triggers:
  on-config-change:
    - agent: agent-meta-manager
      task: "Re-run sync.py — project.yaml has changed."

hooks:
  sync-on-config-change:
    enabled: true
```