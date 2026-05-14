---
description: Sharkord Plugin Structure — enforced directory layout, naming conventions, and config export validation. Auto-loaded for all Sharkord agents.
---

# Sharkord Plugin Structure

## Directory Layout

Every Sharkord plugin MUST follow this structure:

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

## Enforcement Rules

- `src/index.ts` must exist and have a default export typed as `PluginConfig`.
- Hooks must live in `src/hooks/` and use the `useSharkord<Feature>` prefix.
- `dist/` must be listed in `.gitignore`.
- `package.json` must declare `@sharkord/plugin-sdk` in `peerDependencies`.
- `tsconfig.json` must enable `strict: true`.

## Naming Conventions

### Hooks
- **Mandatory prefix:** `useSharkord<Feature>`
- Examples:
  - `useSharkordVoiceRouter`
  - `useSharkordStreamState`
  - `useSharkordHeroAnimation`
- Rationale: Prevents collisions with generic React hooks and makes Sharkord-specific intent explicit.

### Components
- PascalCase, descriptive (e.g., `VoiceChannelPanel`, `StreamOverlay`)

### Utils
- camelCase, action-oriented (e.g., `normalizeUserId`, `formatStreamDuration`)

## Config Export Validation

The default export from `src/index.ts` MUST be a valid Sharkord `PluginConfig`:

```typescript
import { PluginConfig } from "@sharkord/plugin-sdk";

const config: PluginConfig = {
  name: "my-plugin",
  version: "1.0.0",
  // ... required fields
};

export default config;
```

### Pre-Completion Checklist
- [ ] `src/index.ts` exists and has a default export
- [ ] Default export is typed as `PluginConfig`
- [ ] `package.json` has `@sharkord/plugin-sdk` in `peerDependencies`
- [ ] `tsconfig.json` has `strict: true`

## Cross-Plugin Pattern Sharing

If you discover a reusable pattern during development:

1. Document it in a concise markdown snippet.
2. Propose adding it to the meta-repo's `docs/sharkord/PATTERNS.md` via the `meta-feedback` agent or a manual PR.
3. Reference the originating plugin and the specific commit for traceability.

Examples of patterns worth sharing:
- New hook patterns (e.g., `useSharkord<Feature>` variants)
- Mediasoup connection lifecycle management
- Command argument validation helpers
- Docker networking configurations for plugins
