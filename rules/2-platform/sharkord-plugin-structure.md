---
description: Sharkord Plugin Projektstruktur — verbindliche Konvention für alle Plugins
---

# Sharkord Plugin Struktur

## Verzeichnisstruktur (verbindlich)

```
<plugin-name>/
  src/
    index.ts              # EINZIGER Entry-Point (exportiert PluginConfig)
    commands/             # Sharkord Commands (eine Datei pro Command)
    services/             # Business Logic
    handlers/             # Event Handler (voice events, message events, etc.)
    hooks/                # Custom Hooks (Naming: useSharkord<Feature>)
    utils/                # Hilfsfunktionen
    types/                # Interne Type-Definitionen
  scripts/
    build.ts              # Standard Build-Script (verbindlich)
  tests/
    unit/                 # Unit Tests
    integration/            # Integration Tests
    helpers/                # mock-plugin-context.ts
    fixtures/               # Test-Fixtures
  docs/
    ARCHITECTURE.md
    REQUIREMENTS.md         # oder reqs/ bei Doorstop
  docker-compose.dev.yml
  package.json
  tsconfig.json
  README.md
```

## Naming Conventions

### Hooks
- **Pflicht-Präfix:** `useSharkord<Feature>`
- Gut: `useSharkordVoiceRouter`, `useSharkordStreamState`
- Schlecht: `useVoice`, `useStream`

### Commands
- Datei: `src/commands/<command-name>.ts`
- Registrierung: `name: "<command-name>"` (lowercase, hyphenated)

### Services
- Datei: `src/services/<domain>.ts`
- Funktionen: `camelCase`, beschreibend

### Utils
- Datei: `src/utils/<category>.ts`
- Funktionen: `camelCase`, beschreibend

## Verbotene Dateien / Ordner

Diese dürfen **nicht** in einem Sharkord Plugin existieren:
- `.claude/`, `.opencode/`, `.continue/`, `.gemini/`
- `AGENTS.md`, `CLAUDE.md`
- `.agent-meta/`, `.meta-config/`
- `.github/agents/` (veraltet)

## Entry-Point Konvention

`src/index.ts` **muss** einen Default-Export haben:

```typescript
import { PluginConfig, PluginContext } from "@sharkord/plugin-sdk";

export default function plugin(context: PluginContext): PluginConfig {
  // Commands registrieren
  // Events subscriben
  return {
    name: "...",
    version: "...",
    onLoad() { ... },
    onUnload() { ... },
  };
}
```

## Hard Rules

- **Max 300 Zeilen pro Datei** (enforced by validator)
- **`index.ts` = Wiring only** — nur Imports + Registrierung, keine Business Logic
- **Jeder Command** bekommt seine eigene Datei unter `src/commands/`
