## Projekt

**Name:** {{PROJECT_NAME}}
**Präfix:** {{PREFIX}}
**Plattform:** {{PLATFORM}}
**Beschreibung:** {{PROJECT_DESCRIPTION}}

{{#if COMPACT_MODE}}> Tech-Stack, Architektur & Build-Befehle: discoverable via Repo (Manifeste, CI-Configs).

{{else}}## Tech-Stack

- **Runtime:** {{RUNTIME}}
- **Sprache:** {{LANGUAGE}}
- **Key-Dependencies:** {{SYSTEM_DEPENDENCIES}}

## Architektur

```
{{PROJECT_STRUCTURE}}
```

**Entry-Point:**
```
{{ENTRY_POINT_PATTERN}}
```

**Besondere Patterns:**
{{KEY_PATTERNS}}

{{/if}}## Code-Konventionen

{{CODE_CONVENTIONS}}

{{#if COMPACT_MODE}}{{else}}## Build & Development

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
