<!-- agent-meta:managed-begin -->
<!-- Dieser Block wird von sync.py bei jedem sync automatisch aktualisiert. -->
<!-- Manuelle Änderungen hier werden überschrieben. -->

{{PROVIDER_ROUTING}}

{{#if CONTEXT_MANAGED_NOTES_AS_COMMENT}}<!--
Generiert von agent-meta v{{AGENT_META_VERSION}} — `{{AGENT_META_DATE}}`
DoD-Preset: **{{DOD_PRESET}}** | REQ-Traceability: {{DOD_REQ_TRACEABILITY}} | Tests: {{DOD_TESTS_REQUIRED}} | Codebase-Overview: {{DOD_CODEBASE_OVERVIEW}} | Security-Audit: {{DOD_SECURITY_AUDIT}}
-->{{else}}Generiert von agent-meta v{{AGENT_META_VERSION}} — `{{AGENT_META_DATE}}`
DoD-Preset: **{{DOD_PRESET}}** | REQ-Traceability: {{DOD_REQ_TRACEABILITY}} | Tests: {{DOD_TESTS_REQUIRED}} | Codebase-Overview: {{DOD_CODEBASE_OVERVIEW}} | Security-Audit: {{DOD_SECURITY_AUDIT}}{{/if}}
{{AGENT_HINTS}}
<!-- agent-meta:managed-end -->