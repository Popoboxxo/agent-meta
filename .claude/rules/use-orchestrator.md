# CRITICAL GATE — VERIFY BEFORE EVERY ACTION

YOU ARE THE MAIN CHAT. You MUST NOT perform any code changes directly.
- NO `edit` tool call
- NO `write` tool call
- NO `bash` with mutating commands (git commit, pip install, npm, etc.)
- NO `task` tool call — delegate ONLY via `task(subagent_type="orchestrator", ...)` to the Orchestrator

EVERY development-related task MUST be delegated to the `orchestrator` first.
ONLY allowed: `read`, `glob`, `grep` for research/diagnosis.

**Violation: The PreToolUse hook will block these changes.**

# Orchestrator — Universal Router

**STRICT MODE — KEINE Ausnahmen.** Jede Entwicklungsaufgabe geht zwingend über den `orchestrator`. Kein User-Override, kein direkter Dispatch, kein Fallback in den Hauptchat.

## Auto-Handoff

Hauptchat delegiert IMMER automatisch an den Orchestrator via nativen Tool-Call — KEIN User-Override, KEIN `@orchestrator` Mention im Output.


## Anti-Recursion Guard — Worker dürfen nicht zurückdelegieren

**Verboten:** `@orchestrator` im Output | Tool-Calls zum Orchestrator | Aufgaben zurückgeben.
**Erlaubt:** Auf andere Worker verweisen | User bei Blockern um Klärung bitten.
