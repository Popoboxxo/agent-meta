---
name: "Agents Managed Manifest"
target_file: "AGENTS.md"
---
<!-- agent-meta:managed-begin -->
{{> header }}
{{#if HAS_NATIVE_RULES}}
{{> rules-pointer }}
{{else}}
{{> rules-embedded }}
{{/if}}
{{> agents-location }}
{{> agents-table }}
{{> knowledge-engine-hints }}
<!-- agent-meta:managed-end -->
