---
name: "Agents Managed Manifest"
target_file: "AGENTS.md"
---
<!-- agent-meta:managed-begin -->
{{> header }}
{{> project-metadata }}
{{> agents-location }}
{{> agents-table }}
{{> knowledge-engine-hints }}
{{#if HAS_NATIVE_RULES}}
{{> rules-pointer }}
{{else}}
{{> rules-embedded }}
{{/if}}
<!-- agent-meta:managed-end -->
