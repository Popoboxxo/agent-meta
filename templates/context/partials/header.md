---
name: "Standard Header"
---
> **ROUTING:**
{{#if PLATFORM_CLAUDE}} Claude->CLAUDE.md |{{/if}}
{{#if PLATFORM_OPENCODE}} Opencode->AGENTS.md |{{/if}}
{{#if PLATFORM_GEMINI}} Gemini->AGENTS.md{{/if}}
> **ENTRY:** `orchestrator`-Agent (für alle Dev-Tasks).
`agent-meta v{{AGENT_META_VERSION}}` | DoD: `{{DOD_PRESET}}` | REQ-Trace: `{{DOD_REQ_TRACEABILITY}}`
