---
name: "Agent Table"
---
| Agent | Core Capabilities |
|-------|-------------------|
{{#if COMPACT_MODE}}{{#each active_agents}}| `{{name}}` | {{keywords}} |
{{/each}}{{else}}{{#each active_agents}}
| `{{name}}` | {{short_desc}} |
{{/each}}{{/if}}
