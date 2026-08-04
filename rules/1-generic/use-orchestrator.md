{{#if ORCH_MODE_STRICT}}
# CRITICAL GATE
MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`. Keine Ausnahmen.
{{/if}}
{{#if ORCH_MODE_ADVISORY}}
# Orchestrator
Jeder Dev-Task -> `orchestrator`. Ausnahme: User Override oder 1-Step (falls erlaubt).
{{#if DIRECT_DISPATCH_ENABLED}}
{{DIRECT_DISPATCH_SECTION}}
{{/if}}
{{/if}}
{{#if ORCH_MODE_MAIN_CHAT}}
# Main-Chat Mode
Main Chat ist Router + Worker. Kein Orchestrator-Subagent. Du bist der Orchestrator!

## Intent Routing
{{INTENT_ROUTING_TABLE}}

## A2A Delegation
{{A2A_HANDOFF_BLOCK}}

## Plan Delegation
Plan vorhanden (`plan-*.md` oder Knowledge-Wiki Plan-Seite) -> `feature` mit `payload.plan_ref`, statt neuen Lifecycle blind zu starten.
{{/if}}

## Git Delegation
Git Mutationen (commit, push, add etc) -> `git` Agent. Read-only (status, log) im Main Chat ok.
{{#if ORCH_MODE_MAIN_CHAT}}Ausnahme auf User-Wunsch erlaubt.{{/if}}

{{#if NATIVE_EXTENSIONS_ENABLED}}
Native Extensions (Skills/Hooks) erlaubt, ignorieren nicht Branch-Guard/DoD.
{{#if NATIVE_EXTENSIONS_WHITELIST_ACTIVE}}
Erlaubt:
{{NATIVE_EXTENSIONS_WHITELIST_TABLE}}
{{/if}}
{{/if}}
{{#unless NATIVE_EXTENSIONS_ENABLED}}
Native Extensions deaktiviert.
{{/unless}}

{{#unless ORCH_MODE_MAIN_CHAT}}
Anti-Recursion: Worker dürfen nicht an `orchestrator` zurück delegieren.
{{/unless}}
