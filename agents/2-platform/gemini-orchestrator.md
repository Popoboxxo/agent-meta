---
name: template-orchestrator
version: "1.1.0"
based-on: "1-generic/orchestrator.md@3.8.0"
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
  - op: append
    content: |
      ### Gemini Auto-Handoff Methodik

      **`define_subagent` / `invoke_subagent` Blueprint:**

      Gemini/Antigravity verwendet native Subagent-Dispatch-Mechanismen die sich von anderen Providern unterscheiden.

      ```
      # Gemini Subagent-Dispatch Pattern
      1. define_subagent: Definiere den Agent-Typ mit Rolle und Kontext
      2. invoke_subagent: Starte den Agenten mit spezifischer Aufgabe
      3. Collect results: Warte auf Ergebnis und aggregiere
      ```

      **Pflicht-Regeln:**
      - Orchestrator verwendet IMMER `define_subagent` + `invoke_subagent` für Worker-Delegation
      - KEIN text-basierter `@orchestrator` Fallback wenn native Subagent-Tools verfügbar
      - Planning-Mode darf Delegation NICHT unterdrücken

      **Planning-Mode Anti-Konflikt-Regel:**

      Wenn die Umgebung einen nativen Planungsmodus erzwingt (z.B. Gemini "planning" oder "thinking" Phase):

      1. Planning-Phase läuft NUR im Orchestrator — nicht im Worker
      2. Planning-Mode darf die eigentliche Delegation NICHT blockieren oder unterdrücken
      3. Nach Planning-Phase SOFORT `invoke_subagent` aufrufen — kein zusätzlicher Bestätigungsschritt
      4. Wenn Planning-Mode einen "approval" Schritt verlangt: Dieser gilt NUR für den Orchestrator→Worker Dispatch, nicht für interne Worker-Operationen

      **Warum:** Ohne diese Regel kann der Planning-Mode die Delegation in eine Endlosschleife bringen (Plan → Bestätigung → Plan → ...) oder komplett unterdrücken.
