# Orchestrator — Universal Router

**JEDE Entwicklungsaufgabe geht über den Orchestrator.**

## Ausnahmen — direkter Dispatch

NUR für atomare Einzeloperationen (ein Schritt, ein Agent, keine Abhängigkeiten):

| Operation | Direkt an | Bedingung |
|-----------|-----------|-----------|
| Commit, Push, Branch, Tag, PR | `git` | Einzelner Git-Befehl |
| Sync, Upgrade, Meta-Konfiguration | `agent-meta-manager` | Reine agent-meta-Operation |
| Bug/Feature/Verbesserung melden | `feedback` | Issue-Erstellung |
| Session-Erkenntnisse speichern | `documenter` | Nur bei Session-Ende |

> **Faustregel:** >1 Tool-Call → Orchestrator. Unsicher → Orchestrator.

## User-Override

Trigger-Sätze (User sagt explizit): "Nicht delegieren" | "Mach das hier" | "Im Hauptchat bitte" | "Kein Orchestrator" | "Ohne Orchestrator" | "Ich will hier arbeiten" | "Delegiere nicht"

## Auto-Handoff

Hauptchat delegiert automatisch an Orchestrator via nativen Tool-Call — KEIN `@orchestrator` Mention im Output. `@orchestrator` ist der EINZIGE Mention den User direkt verwenden dürfen.

## Subagent Invocation Policy (Pflicht)

**Der Hauptchat darf KEINE Worker-Agenten direkt aufrufen.**

| Aktion | Hauptchat | Orchestrator |
|--------|-----------|--------------|
| Worker aufrufen (developer, tester, git, etc.) | **Verboten** | Erlaubt |
| Orchestrator aufrufen | Erlaubt (einziger erlaubter Agent-Call) | — |
| Atomare Ausnahme (siehe "Ausnahmen — direkter Dispatch") | Erlaubt | — |

**Begründung:** Nur der Orchestrator kennt Intent-Routing, A2A-Envelopes, Parallel-Engine
und Anti-Recursion-Guards. Direkte Worker-Aufrufe umgehen diese Infrastruktur.

## Anti-Recursion Guard — Worker dürfen nicht zurückdelegieren

**Verboten:** `@orchestrator` im Output | Tool-Calls zum Orchestrator | Aufgaben zurückgeben.
**Erlaubt:** Auf andere Worker verweisen | User bei Blockern um Klärung bitten.
