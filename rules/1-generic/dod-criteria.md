# Definition of Done (DoD)

Pflicht: Code komplett, Konventionen & Conv. Commits eingehalten, keine Regressions.
{{#if DOD_REQ_TRACEABILITY}}REQ-Traceability: REQ-ID in `docs/REQUIREMENTS.md` & Commit (`<type>(REQ-xxx): ...`){{/if}}
{{#if DOD_TESTS_REQUIRED}}Tests: Test vorhanden & grün{{/if}}
{{#if DOD_CODEBASE_OVERVIEW}}Doku: `CODEBASE_OVERVIEW.md` aktualisiert{{/if}}
{{#if DOD_SECURITY_AUDIT}}Security: Audit vor Release{{/if}}
{{#if DOD_AI_SECURITY_REVIEW}}AI-Security: KI-generierter Code muss AI-spezifisches Security-Review passieren (ai-security-guardian){{/if}}
{{#if DOD_PROMPT_GOVERNANCE}}Prompt-Governance: Prompts werden als Source Code governed (prompt-governor){{/if}}
{{#if DOD_LIFECYCLE_OWNERSHIP}}Lifecycle: Jede App/jeder Service braucht benannten Owner + Deprecation-Plan (app-lifecycle-governor){{/if}}
