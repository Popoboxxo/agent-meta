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

3. **Orchestrator:** Alles andere → an `orchestrator` delegieren.

> **Merksatz:** Mehr als ein Schritt ODER mehr als ein Agent ODER Dateien in kritischen Pfaden → immer Orchestrator. Auch wenn der User eine kurze Lösung erwartet.

## Direkter Dispatch (nur nach Regel 2)

| Operation | Direkt an | Bedingung |
|-----------|-----------|-----------|
| Commit, Push, Branch, Tag, PR | `git` | Einzelner Git-Befehl |
| Sync, Upgrade, Meta-Konfiguration | `agent-meta-manager` | Reine agent-meta-Operation |
| Bug/Feature/Verbesserung melden | `feedback` | Issue-Erstellung |
| Session-Erkenntnisse speichern | `documenter` | Nur bei Session-Ende |

> **Faustregel:** >1 Tool-Call → Orchestrator. Unsicher → Orchestrator.

## Auto-Handoff

Hauptchat delegiert automatisch an Orchestrator via nativen Tool-Call — KEIN `@orchestrator` Mention im Output. `@orchestrator` ist der EINZIGE Mention den User direkt verwenden dürfen.

## Anti-Recursion Guard — Worker dürfen nicht zurückdelegieren

**Verboten:** `@orchestrator` im Output | Tool-Calls zum Orchestrator | Aufgaben zurückgeben.
**Erlaubt:** Auf andere Worker verweisen | User bei Blockern um Klärung bitten.

# Main-Chat-Modus

Orchestrator ist deaktiviert. Alle Aufgaben werden direkt im Hauptchat ausgeführt.
Delegation an Subagenten ist optional und erfolgt nach eigenem Ermessen.

