# {{PROJECT_NAME}}

{{PROJECT_CONTEXT}}

<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on every sync. -->
<!-- Manual changes here will be overwritten. -->

Generiert von agent-meta v{{AGENT_META_VERSION}} — `{{AGENT_META_DATE}}`
DoD-Preset: **{{DOD_PRESET}}** | REQ-Traceability: {{DOD_REQ_TRACEABILITY}} | Tests: {{DOD_TESTS_REQUIRED}} | Codebase-Overview: {{DOD_CODEBASE_OVERVIEW}} | Security-Audit: {{DOD_SECURITY_AUDIT}}

{{AGENT_HINTS}}
<!-- agent-meta:managed-end -->

## Agents

Agent files are in `.gemini/agents/`. Agents must be registered at session start via the bootstrap instructions above. `@agent` text mentions are not intercepted by Gemini.

<!-- agent-meta:bootstrap-begin -->
<!-- agent-meta:bootstrap-end -->

## Project Setup

- **Build:** `{{BUILD_COMMAND}}`
- **Test:** `{{TEST_COMMAND}}`
- **Platform:** {{PLATFORM}}
- **Runtime:** {{RUNTIME}}
