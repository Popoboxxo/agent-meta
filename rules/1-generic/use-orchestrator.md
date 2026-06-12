{{#if ORCHESTRATOR_ENABLED}}
# Orchestrator — Universal Router

{{#if ORCHESTRATOR_STRICT}}
**STRICT MODE — KEINE Ausnahmen.** Jede Entwicklungsaufgabe geht zwingend über den `orchestrator`. Kein User-Override, kein direkter Dispatch, kein Fallback in den Hauptchat.

## Auto-Handoff

Hauptchat delegiert IMMER automatisch an den Orchestrator via nativen Tool-Call — KEIN User-Override, KEIN `@orchestrator` Mention im Output.

{{else}}
**JEDE Entwicklungsaufgabe geht über den Orchestrator.**

## Entscheidungsreihenfolge (Priority-Order)

1. **User-Override:** User sagt explizit "Nicht delegieren", "Mach das hier", "Im Hauptchat bitte", "Kein Orchestrator", "Ohne Orchestrator", "Ich will hier arbeiten", "Delegiere nicht" → **Im Hauptchat arbeiten, nicht delegieren.**
{{#if DIRECT_DISPATCH_ENABLED}}
2. **Direkter Dispatch:** Task ist exakt ein Tool-Call, kein Datei-Pfad in agents/, rules/, hooks/, scripts/ oder config/ betroffen, und kein Folgeschritt hängt vom Ergebnis ab → direkt an den spezifischen Agenten.
{{/if}}
3. **Orchestrator:** Alles andere → an `orchestrator` delegieren.

> **Merksatz:** Mehr als ein Schritt ODER mehr als ein Agent ODER Dateien in kritischen Pfaden → immer Orchestrator. Auch wenn der User eine kurze Lösung erwartet.

{{#if DIRECT_DISPATCH_ENABLED}}
{{DIRECT_DISPATCH_SECTION}}
{{/if}}

## Auto-Handoff

Hauptchat delegiert automatisch an Orchestrator via nativen Tool-Call — KEIN `@orchestrator` Mention im Output. `@orchestrator` ist der EINZIGE Mention den User direkt verwenden dürfen.
{{/if}}

## Anti-Recursion Guard — Worker dürfen nicht zurückdelegieren

**Verboten:** `@orchestrator` im Output | Tool-Calls zum Orchestrator | Aufgaben zurückgeben.
**Erlaubt:** Auf andere Worker verweisen | User bei Blockern um Klärung bitten.
{{else}}
# Main-Chat-Modus

Orchestrator ist deaktiviert. Alle Aufgaben werden direkt im Hauptchat ausgeführt.
Delegation an Subagenten ist optional und erfolgt nach eigenem Ermessen.
{{/if}}
