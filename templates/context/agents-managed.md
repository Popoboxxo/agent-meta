---
name: "Agents Managed Manifest"
target_file: "AGENTS.md"
version: 2.0.0
---
<!-- agent-meta:managed-begin -->
{{> header }}
{{#if HAS_NATIVE_RULES}}
{{> rules-pointer }}
{{else}}
{{#if HAS_EMBEDDED_RULES}}
{{> rules-embedded }}
{{/if}}
{{#if HAS_LAZY_RULES}}
{{> rules-lazy }}
{{/if}}
{{/if}}
{{> agents-location }}
{{> agents-table }}
{{> knowledge-engine-hints }}
<!-- agent-meta:managed-end -->