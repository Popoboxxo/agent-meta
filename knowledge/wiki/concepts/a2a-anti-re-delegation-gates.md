---
type: "Concept"
title: "Konzept: A2A Anti-Re-Delegation Gates & Governance"
description: "Standardisierte Sicherheits- und Stabilitäts-Gates für Agent-zu-Agent-Delegationen zur Vermeidung von Rekursionsschleifen, Kontext-Overhead und State-Corruption."
tags: [concept, governance, a2a, status:active]
timestamp: "2026-07-27"
resource: "../../rules/1-generic/a2a-delegation-gates.md"
migrated_from: "rules/1-generic/a2a-delegation-gates.md"
---
# Konzept: A2A Anti-Re-Delegation Gates & Governance

> Status: **Umgesetzt — aktiv**  
> Verwandt: [A2A-Handoff-Protokoll](a2a-handoff-protocol.md), [Singleton-Orchestrator](singleton-orchestrator-architecture.md)  
> Betroffen: `rules/1-generic/a2a-delegation-gates.md`, `agents/1-generic/orchestrator.md`  

---

## 1. Problemstellung & Motivation

In Multi-Agenten-Systemen führt unkontrollierte Agent-zu-Agent-Kommunikation (A2A) ohne Governance-Regeln zu typischen Systemdefekten:
- **Endlose Rekursionsschleifen**: Subagenten delegieren Aufgaben zurück an den Orchestrator oder rufen sich gegenseitig zirkulär auf.
- **Kontext-Überlauf (Context Explosion)**: Weitergabe roher, unstrukturierter Log-Dateien oder ellenlanger Traces verbraucht unnötig Token-Budget.
- **Prompt Injection & Persona Bleed**: Wenn Subagent-Payloads mit Instruktionsphrasen wie *"Du bist..."* beginnen, wird die Ziel-Rolle überschrieben oder konfiguriertes Verhalten korrumpiert.

Zur Absicherung des Multi-Agenten-Netzwerks definiert agent-meta **fünf verbindliche Hard Gates**.

---

## 2. Die 5 Hard Gates im Detail

| Gate | Regel | Zweck / Schutzwirkung |
|---|---|---|
| **1. Max Depth Limit** | Maximale Delegationstiefe `A2A_MAX_DEPTH` (Standard: 10). Keinesfalls Self-Handoff. | Verhindert unendliche Aufrufketten und Stack-Overflow-Vorgänge in tief geschachtelten Workflows. |
| **2. Short Payload Limit** | `payload.t` darf maximal `A2A_T_SIZE_LIMIT` (Standard: 300 Zeichen) umfassen. | Erzwingt prägnante Task-Zusammenfassungen und schützt vor Token-Verschwendung. |
| **3. No Re-Delegation / Anti-Prompt-Leakage** | Payloads dürfen NIE mit *"Du bist..."* oder System-Prompt-Phrasen beginnen. | Schützt die Rolle und Instruktionen des empfangenden Subagenten vor Überschreibung. |
| **4. Singleton Orchestrator** | NUR der `main_chat` darf den `orchestrator`-Agenten spawnen. Worker dürfen NIEMALS den Orchestrator anrufen. | Verhindert zirkuläre Rückdelegation und Deadlocks im System routing. |
| **5. Execution-Trace-Isolation** | Worker-Outputs müssen strikt strukturiert sein (`STATUS`, `RESULT`, `ARTIFACTS`). Keine rohen Logs propagieren. | Hält Kontext sauber; Hauptagent erhält strukturierte Zusammenfassung statt unverarbeiteter Log-Massen. |

---

## 3. Execution-Trace-Isolation & Output-Struktur

Worker-Agenten sind verpflichtet, ihre Ergebnisse im A2A-Protokoll nach folgendem Format zu kapseln:

```markdown
STATUS: SUCCESS | FAILED | BLOCKED
RESULT: <Kompakte Zusammenfassung des Ergebnisses>
ARTIFACTS:
  - path/to/changed_file.py
  - path/to/generated_doc.md
```

### Unzulässige Log-Propagierung (Anti-Pattern):
```markdown
# BAD: Rohe CLI-Outputs oder Logfiles direkt zurückmelden
$ pytest tests/
============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-7.4.0, pluggy-1.2.0
rootdir: /home/user/repo
collected 142 items
tests/test_core.py ..................................................... [ 37%]
... (500 Zeilen Log-Output) ...
```

---

## 4. Integration & Enforcement

Die Anti-Re-Delegation Gates sind in `rules/1-generic/a2a-delegation-gates.md` definiert und werden von `sync.py` in alle generierten Agenten injiziert. Sie dienen dem runtime protection layer auf allen unterstützten AI-Plattformen.