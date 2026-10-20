---
name: "Agent List Compact"
version: 1.0.0
---
{{#each active_agents}}- `{{name}}`: {{short_desc}}
{{/each}}
