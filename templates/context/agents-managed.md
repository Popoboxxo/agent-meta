---
name: "Agents Managed Manifest"
target_file: "AGENTS.md"
version: 2.0.0
---
<!-- agent-meta:managed-begin -->
{{> header }}
{{#if CONTEXT_PROFILE_COMPACT}}{{> gate-card }}
{{else}}{{#if HAS_NATIVE_RULES}}
{{> rules-pointer }}
{{else}}
{{#if HAS_EMBEDDED_RULES}}
{{> rules-embedded }}
{{/if}}
{{#if HAS_LAZY_RULES}}
{{> rules-lazy }}
{{/if}}
{{/if}}{{/if}}
{{> agents-location }}
{{#if CONTEXT_PROFILE_COMPACT}}{{> agents-list-compact }}
{{else}}{{> agents-table }}{{/if}}
{{> knowledge-engine-hints }}
<!-- agent-meta:managed-end -->
