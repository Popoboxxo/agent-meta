---
name: "Agent Table"
version: 2.1.0
---
| Agent | Core Capabilities |
|-------|-------------------|
{{#each active_agents}}| `{{name}}` | {{keywords}} |
{{/each}}
