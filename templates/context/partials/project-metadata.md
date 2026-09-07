---
name: "Project Metadata"
version: 2.0.0
---
## Projekt

**Name:** {{PROJECT_NAME}}
**Präfix:** {{PREFIX}}
**Plattform:** {{PLATFORM}}
**Beschreibung:** {{PROJECT_DESCRIPTION}}

> Struktur: siehe Verzeichnisstruktur im Repo (`ls`/`find`); deklarativ: `.meta-config/project.yaml` → `variables.PROJECT_STRUCTURE`.

> Runtime & Abhängigkeiten: siehe Projekt-Manifest (`pyproject.toml` / `requirements.txt` / `package.json` / `manifest.json`).

**Entry-Point:** `{{ENTRY_POINT_PATTERN}}`

**Besondere Patterns:**
{{KEY_PATTERNS}}

## Code-Konventionen

{{CODE_CONVENTIONS}}

{{#if COMPACT_MODE}}> Build: `{{BUILD_COMMAND}}` · Test: `{{TEST_COMMAND}}` · Dev: `{{DEV_STACK_START}}` · Reload: `{{DEV_STACK_RELOAD}}`

{{else}}## Build & Development

```bash
# Build
{{BUILD_COMMAND}}

# Tests
{{TEST_COMMAND}}

# Dev-Stack starten
{{DEV_STACK_START}}

# Nach Änderungen neu laden
{{DEV_STACK_RELOAD}}
```

{{/if}}## Anforderungs-Kategorien

Kategorien für `docs/REQUIREMENTS.md`:

{{REQ_CATEGORIES_LIST}}
