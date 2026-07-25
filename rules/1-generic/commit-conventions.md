# Commit-Konventionen

Verwende Conventional Commits (feat, fix, chore).
Beschreibungssprache: `{{CODE_LANGUAGE}}`
Max 72 Zeichen in erster Zeile. Imperativ.
{{#if DOD_REQ_TRACEABILITY}}
Format: `<type>(REQ-xxx): <beschreibung>` (Bsp: `feat(REQ-123): ...`)
{{else}}
Format: `<type>: <beschreibung>` (Bsp: `feat: ...`)
{{/if}}
