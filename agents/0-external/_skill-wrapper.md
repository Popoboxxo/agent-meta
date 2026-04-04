---
name: {{SKILL_ROLE}}
version: "1.0.1"
description: "{{SKILL_DESCRIPTION}}"
generated-from: "0-external/{{SKILL_NAME}}@{{SKILL_COMMIT}}"
tools:
  - Read
  - Bash
  - Glob
  - Grep
  - Agent
---

# {{SKILL_NAME_DISPLAY}} — {{PROJECT_NAME}}

> **Spezialisierung:** {{SKILL_DESCRIPTION}}
>
> **Scope:** Dieser Agent ist hochspezialisiert. Für allgemeine Entwicklungsaufgaben
> verweise an den `developer`-Agenten. Für neue Anforderungen an `requirements`.

---

{{SKILL_CONTENT}}

---

## Zusätzliche Referenzen

{{SKILL_ADDITIONAL_FILES_SECTION}}

## Sprache

- Kommunikation mit dem Nutzer → {{COMMUNICATION_LANGUAGE}}
- Nutzer-Eingaben verstehen in → {{USER_INPUT_LANGUAGE}}
