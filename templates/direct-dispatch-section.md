
## Direkter Dispatch (nur nach Regel 2)

| Operation | Direkt an | Bedingung |
|-----------|-----------|-----------|
{{#if ROLE_GIT_ACTIVE}}
| Commit, Push, Branch, Tag, PR | `git` | Einzelner Git-Befehl |
{{/if}}
{{#if ROLE_AGENT_META_MANAGER_ACTIVE}}
| Sync, Upgrade, Meta-Konfiguration | `agent-meta-manager` | Reine agent-meta-Operation |
{{/if}}
{{#if ROLE_FEEDBACK_ACTIVE}}
| Bug/Feature/Verbesserung melden | `feedback` | Issue-Erstellung |
{{/if}}
{{#if ROLE_DOCUMENTER_ACTIVE}}
| Session-Erkenntnisse speichern | `documenter` | Nur bei Session-Ende |
{{/if}}

> **Faustregel:** >1 Tool-Call → Orchestrator. Unsicher → Orchestrator.
