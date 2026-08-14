---
name: lifecycle-tasks
description: "Use at session start or when .claude/pending-tasks.md exists — covers pending-task handling."
---

# Lifecycle-Tasks

Beim Start prüfen: existiert `.claude/pending-tasks.md`?
Falls ja und enthält `- [ ]`: User fragen ob delegiert werden soll.
Nach Erledigung: löschen. Datei nicht committen.
