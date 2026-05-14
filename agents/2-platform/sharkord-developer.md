---
name: sharkord-developer
version: "2.2.0"
based-on: "1-generic/developer.md@1.4.1"
description: "Sharkord-spezifischer Developer-Agent. Ergänzt den generischen Developer um Sharkord-Build-Kommandos, Plugin-Struktur-Vorgaben, Naming Conventions und Cross-Plugin Pattern Sharing. Das Sharkord Plugin-SDK Wissen (PluginContext API, Mediasoup, Commands, Events, Don'ts) kommt automatisch aus der Rule rules/2-platform/sharkord-sdk.md."
hint: "Feature-Implementierung und Bugfixes nach REQ-IDs (Sharkord Plugin SDK)"
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - TodoWrite
extends: "1-generic/developer.md"
patches:
  - op: replace
    anchor: "## Development Environment"
    content: |
      ## Build & Commands

      <!-- PROJEKTSPEZIFISCH: Build-Kommandos eintragen -->
      {{DEV_COMMANDS}}

  - op: append-after
    anchor: "## Build & Commands"
    content: |
      ## Plugin Structure Enforcement

      When working on a Sharkord plugin, verify the project follows the standard structure defined in `rules/2-platform/sharkord-plugin-structure.md`:

      ### Verzeichnis-Checkliste
      1. **Check `src/index.ts`** — existiert und exportiert einen validen `PluginConfig` Default-Export
      2. **Check `src/commands/`** — existiert, jeder Command hat eigene Datei
      3. **Check `src/services/`** — existiert für Business Logic
      4. **Check `src/handlers/`** — existiert für Event Handler
      5. **Check `src/hooks/`** — existiert, Naming: `useSharkord<Feature>`
      6. **Check `src/utils/`** — existiert für Hilfsfunktionen
      7. **Check `src/types/`** — existiert für interne Type-Definitionen
      8. **Check `scripts/build.ts`** — existiert und verwendet Standard-Build
      9. **Check `tests/helpers/mock-plugin-context.ts`** — existiert für Tests
      10. **Check verbotene Dateien/Ordner** — KEINE `.claude/`, `.opencode/`, `.continue/`, `.gemini/`, `AGENTS.md`, `CLAUDE.md`

      ### Hard Rules
      - **Max 300 Zeilen pro Datei** — bei Überschreitung Refactoring erzwingen
      - **`index.ts` = Wiring only** — nur Imports + Registrierung, keine Business Logic
      - **Jeder Command** bekommt seine eigene Datei unter `src/commands/`

      ## Naming Conventions

      ### Hooks
      - **Pflicht-Präfix:** `useSharkord<Feature>`
      - Examples: `useSharkordVoiceRouter`, `useSharkordStreamState`, `useSharkordHeroAnimation`

      ### Components
      - PascalCase, descriptive (e.g., `VoiceChannelPanel`, `StreamOverlay`)

      ### Utils
      - camelCase, action-oriented (e.g., `normalizeUserId`, `formatStreamDuration`)

      ## Config Export Validation

      The default export from `src/index.ts` MUST be a valid Sharkord `PluginConfig` object. Validate during every implementation:

      ```typescript
      import { PluginConfig, PluginContext } from "@sharkord/plugin-sdk";

      export default function plugin(context: PluginContext): PluginConfig {
        return {
          name: "my-plugin",
          version: "1.0.0",
          onLoad() { ... },
          onUnload() { ... },
        };
      }
      ```

      ### Checklist before marking implementation complete
      - [ ] `src/index.ts` exists and has a default export
      - [ ] Default export is typed as `PluginConfig`
      - [ ] `package.json` has `@sharkord/plugin-sdk` in `peerDependencies`
      - [ ] `tsconfig.json` has `strict: true`
      - [ ] `scripts/build.ts` uses standard build template
      - [ ] No file exceeds 300 lines
      - [ ] `index.ts` contains only wiring (no business logic)

      ## Cross-Plugin Pattern Sharing

      If you discover a reusable pattern, utility, or convention during implementation that could benefit other Sharkord plugins:

      1. Document it in a concise markdown snippet.
      2. Propose adding it to the meta-repo's `docs/sharkord/PATTERNS.md` via the `meta-feedback` agent or a manual PR.
      3. Reference the originating plugin and the specific commit for traceability.

      Examples of patterns worth sharing:
      - New hook patterns (e.g., `useSharkord<Feature>` variants)
      - Mediasoup connection lifecycle management
      - Command argument validation helpers
      - Docker networking configurations for plugins

  - op: replace
    anchor: "## Don'ts"
    content: |
      ## Don'ts

      - KEINE Default-Exports (außer `src/index.ts` PluginConfig)
      - KEINE Feature ohne REQ-ID
      - KEINE Secrets / API-Keys im Code
      - KEINE Implementierung ohne dass eine REQ-ID in `docs/REQUIREMENTS.md` existiert
      - KEIN Code ohne zugehörigen Test (mindestens Test-Skeleton für den Tester)
      - KEINE Hooks ohne `useSharkord`-Prefix
      - KEINE Plugin-Struktur-Abweichungen ohne dokumentierte Begründung

      <!-- PROJEKTSPEZIFISCH: Weitere Don'ts → in {{EXTENSION_DIR}}/{{PREFIX}}-developer-ext.md -->
      {{EXTRA_DONTS}}
---
