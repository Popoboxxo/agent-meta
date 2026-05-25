---
name: template-orchestrator
version: "1.0.0"
based-on: "1-generic/orchestrator.md@3.7.0"
description: "Gemini/Antigravity-spezifischer Orchestrator-Override: Mention-Interception und Tool-Dispatch."
tools:
  - Agent
  - TodoWrite
---

# Orchestrator — {{PROJECT_NAME}} (Gemini/Antigravity)

extends: "1-generic/orchestrator.md"
patches:
  - op: append-after
    anchor: "## Mention-Interception Policy (Pflicht)"
    content: |
      ### Gemini/Antigravity-spezifische Hinweise

      **Technische Einschränkung:** Die Gemini/Antigravity UI interceptet **ausschließlich** den `@orchestrator`-Mention.
      Alle anderen `@<agent>`-Mentions (`@git`, `@feedback`, `@meta-feedback`, `@developer`, etc.) werden als
      reiner Text gerendert und lösen **keine** Subagent-Invocation aus.

      **Pflicht-Regeln für Gemini:**
      1. Verwende IMMER `@orchestrator <Aufgabe>` für alle Delegationsaufrufe
      2. Verwende NIEMALS `@git`, `@feedback`, `@developer` oder andere Agent-Mentions
      3. Wenn der Hauptchat delegieren muss: `@orchestrator Delegiere an git: "Commit message..."`
      4. Die "Ausnahmen — direkter Dispatch" aus use-orchestrator.md gelten in Gemini **nicht** als User-Mentions — sie sind rein interne Delegationsentscheidungen

      **Beispiel — Falsch (funktioniert nicht in Gemini):**
      > "@meta-feedback Bitte erstelle ein Issue für..."

      **Beispiel — Richtig:**
      > "@orchestrator Delegiere an meta-feedback: Erstelle ein Issue für..."

      **Oder über Tool-Call (bevorzugt):**
      Verwende das native `task()`-Tool des Orchestrators — das umgeht Mention-Parsing komplett.
