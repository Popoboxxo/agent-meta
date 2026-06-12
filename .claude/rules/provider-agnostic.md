# Provider-Agnostic Policy — Generic Templates

**Generische Agenten-Templates (1-generic/) müssen universell und provider-agnostisch bleiben.**

## Verboten in 1-generic/

- Provider-Namen (Claude, Gemini, Opencode, Continue, VS Code, etc.)
- Provider-spezifische Tool-Aufruf-Syntax (at-agent, claude -a, define_subagent, etc.)
- Provider-spezifische Dateipfade (.claude/, .gemini/, etc.)
- Provider-spezifische APIs oder Protokolle

## Erlaubt in 1-generic/

- Abstrakte Konzepte ("Agent", "Orchestrator", "Subagent", "Task", "Rule")
- Platzhalter (geschrieben als GROSS_MIT_UNTERSTRICH in doppelten geschweiften Klammern) die vom Sync-Prozess substituiert werden
- Generische Hinweise auf Umgebungsverhalten ("nativer Planungsmodus", "Fallback")

## Wo Provider-Spezifika hingehören

| Ebene | Ort | Beispiel |
|-------|-----|----------|
| **2-platform/** | Plattform-spezifische Overrides | 2-platform/gemini-orchestrator.md |
| **Sync-Generierung** | scripts/lib/agents.py injiziert Provider-spezifische Felder | model, memory, permissionMode |
| **3-project/** | Projekt-spezifische Erweiterungen | .gemini/3-project/am-orchestrator-ext.md |

## Prüfung

Bevor ein Commit in 1-generic/ gemerged wird:
- Enthält der Text Provider-Namen? → Ablehnen oder in 2-platform/ verschieben
- Enthält der Text Tool-Syntax eines Providers? → Ablehnen oder abstrahieren

> **Warum:** 1-generic/ propagiert in ALLE Projekte. Ein Provider-Name hier würde in Claude-Projekten "Gemini" stehen und in Gemini-Projekten "Claude" — beides falsch und verwirrend.
