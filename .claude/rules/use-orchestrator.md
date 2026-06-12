# Orchestrator — Universal Router

**STRICT MODE — KEINE Ausnahmen.** Jede Entwicklungsaufgabe geht zwingend über den `orchestrator`. Kein User-Override, kein direkter Dispatch, kein Fallback in den Hauptchat.

## Auto-Handoff

Hauptchat delegiert IMMER automatisch an den Orchestrator via nativen Tool-Call — KEIN User-Override, KEIN `@orchestrator` Mention im Output.


## Anti-Recursion Guard — Worker dürfen nicht zurückdelegieren

**Verboten:** `@orchestrator` im Output | Tool-Calls zum Orchestrator | Aufgaben zurückgeben.
**Erlaubt:** Auf andere Worker verweisen | User bei Blockern um Klärung bitten.
