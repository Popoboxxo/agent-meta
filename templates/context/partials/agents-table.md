---
name: "Agent Table"
version: 2.0.0
---
| Agent | Core Capabilities |
|-------|-------------------|
{{#if COMPACT_MODE}}{{#each active_agents}}| `{{name}}` | {{keywords}} |
{{/each}}{{else}}{{#each active_agents}}
| `{{name}}` | {{keywords}} |
{{/each}}{{/if}}
