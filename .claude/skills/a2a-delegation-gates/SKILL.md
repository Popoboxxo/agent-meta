---
name: a2a-delegation-gates
description: "Use when delegating to subagents with A2A envelopes — covers depth limits, payload size, re-delegation and orchestrator singleton gates."
---

# A2A Anti-Re-Delegation Gates

1. Limit depth to 10, no self-handoff.
2. Short payload: `payload.t` max 300 Zeichen.
3. No Re-Delegation (payload starts with "Du bist...").
4. Singleton Orchestrator: NUR der `main_chat` darf den `orchestrator` spawnen.
5. Execution-Trace-Isolation: Worker-Output muss strukturiert sein (STATUS, RESULT, ARTIFACTS). Keine rohen Logs propagieren.

## Bekannte Grenzen

- **Tiefenlimit (Punkt 1) ist modellbasiert, keine technische Barriere.** Eine passende Implementierung existiert (`validate_envelope(max_depth=...)` in `scripts/lib/delegation_syntax.py`), wird aber im aktiven Delegationspfad nirgends aufgerufen. Die Regel verlässt sich auf Modell-Gehorsam, nicht auf Enforcement.
- **Singleton-Orchestrator (Punkt 4) wird nur über eine Selbstdeklaration der Agenten-Identität gestützt** (`#agent-meta:agent=<name>` in `.claude/hooks/orchestrator-guard.sh`), die im Hook-Quelltext selbst als "soft, self-reported convention, not a security boundary" dokumentiert ist. Jeder Agent kann sich technisch als privilegiert deklarieren.
