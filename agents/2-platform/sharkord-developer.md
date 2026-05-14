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
      ## Sharkord Plugin Structure

      Every Sharkord plugin MUST follow this directory layout. Enforce it during implementation and refactoring:

      ```
      <plugin-name>/
        src/
          index.ts              # MUST export valid Sharkord PluginConfig (default export)
          components/           # React/UI components (PascalCase)
          hooks/                # Custom hooks — MUST use useSharkord<Feature> prefix
          utils/                # Helper functions (camelCase)
        package.json            # Dependencies + scripts + plugin metadata
        tsconfig.json           # TypeScript strict mode
        sharkord.config.ts      # Sharkord-specific configuration (optional but recommended)
        README.md
        dist/                   # Build output (gitignored)
      ```

      ### Enforcement Rules

      - If `src/index.ts` is missing or does not export a valid `PluginConfig`, reject the implementation.
      - If hooks exist outside `src/hooks/` or do not follow the naming convention, propose a refactor.
      - `dist/` must be in `.gitignore`.

      ## Naming Conventions

      ### Hooks
      - **Mandatory prefix:** `useSharkord<Feature>`
      - Examples: `useSharkordVoiceRouter`, `useSharkordStreamState`, `useSharkordHeroAnimation`
      - Rationale: Prevents collisions with generic React hooks and makes Sharkord-specific intent explicit.

      ### Components
      - PascalCase, descriptive (e.g., `VoiceChannelPanel`, `StreamOverlay`)

      ### Utils
      - camelCase, action-oriented (e.g., `normalizeUserId`, `formatStreamDuration`)

      ## Config Export Validation

      The default export from `src/index.ts` MUST be a valid Sharkord `PluginConfig` object. Validate during every implementation:

      ```typescript
      import { PluginConfig } from "@sharkord/plugin-sdk";

      const config: PluginConfig = {
        name: "my-plugin",
        version: "1.0.0",
        // ... required fields
      };

      export default config;
      ```

      ### Checklist before marking implementation complete
      - [ ] `src/index.ts` exists and has a default export
      - [ ] Default export is typed as `PluginConfig`
      - [ ] `package.json` has `@sharkord/plugin-sdk` in `peerDependencies`
      - [ ] `tsconfig.json` has `strict: true`

      ## Sharkord Test Pyramid

      Every Sharkord plugin MUST follow a three-tier test structure:

      ```
      tests/
        unit/              # Pure logic, mocked dependencies
        integration/       # Command-to-service flows with real SDK context
        docker/            # Smoke tests with real ffmpeg + mediasoup in container
      ```

      ### Test Naming Convention
      Every test MUST reference its REQ-ID:
      ```typescript
      it("[REQ-042] should persist queue across restarts", async () => { ... });
      ```

      ### Required Tests per Feature Type

      | Feature Type | Unit | Integration | Docker E2E |
      |-------------|------|-------------|------------|
      | Voice/Streaming | ✅ Required | ✅ Required | ✅ Required |
      | Commands | ✅ Required | ✅ Required | ⚪ Optional |
      | UI Components | ✅ Required | ⚪ Optional | ❌ Not needed |
      | Utils/Helpers | ✅ Required | ❌ Not needed | ❌ Not needed |

      ### Test Infrastructure
      - `tests/helpers/mock-plugin-context.ts` — MUST exist for integration tests
      - Integration tests MUST use a real `PluginContext` (not fully mocked)
      - Docker E2E tests MUST verify `docker-compose.dev.yml` health checks

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
