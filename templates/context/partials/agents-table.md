---
name: "Agent Table"
---
| Agent | Core Capabilities |
|-------|-------------------|
{{#each active_agents}}
| `{{name}}` | {{short_desc}} |
{{/each}}
