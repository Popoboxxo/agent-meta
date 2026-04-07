# Layer Model

> [Back to Architecture Overview](../../ARCHITECTURE.md)

## Agents — Override-Priorität

```mermaid
graph LR
    A[1-generic] -->|overridden by| B[2-platform]
    B -->|overridden by| C[3-project override]
    D[0-external skills] -.->|added to| E[.claude/agents/]
    A --> E
    B --> E
    C --> E
```

## Rules — Auto-loaded in alle Agenten

```mermaid
graph LR
    R0[rules/0-external] -->|merged into| RO[.claude/rules/]
    R1[rules/1-generic] -->|merged into| RO
    R2[rules/2-platform] -->|overrides same-name| RO
    R3[3-project rules] -.->|never touched by sync| RO
    RO -->|auto-loaded| AG[all agents]
```

Rules werden von Claude Code automatisch in jeden Agenten-Kontext geladen — kein Read-Tool nötig.
Ideal für Cross-Cutting-Policies (Security, Coding-Konventionen, Issue-Lifecycle).

## Hooks — Opt-in Shell Scripts

```mermaid
graph LR
    H0[hooks/0-external] -->|copied to| HO[.claude/hooks/]
    H1[hooks/1-generic] -->|copied to| HO
    H2[hooks/2-platform] -->|copied to| HO
    HO -->|registered in| SJ[.claude/settings.json]
    SJ -->|triggers| CL[Claude Code PreToolUse/PostToolUse]
```

Hooks werden **immer kopiert**, aber nur ausgeführt wenn `enabled: true` in `agent-meta.config.json`:
```json
"hooks": {
  "dod-push-check": { "enabled": true }
}
```
