# CONVENTIONS.md — Cross-Plugin Coding Conventions

> This file lives in the meta-repo and documents coding conventions that apply across all plugins.

## TypeScript

- `strict: true` in `tsconfig.json` is mandatory
- No implicit `any`
- No `var` — use `const` / `let`
- Named exports preferred over default exports (except `src/index.ts` PluginConfig)

## SQLite

- Column names MUST be `snake_case`
- No camelCase in database schemas

## Hooks

- Custom hooks MUST use the `useSharkord<Feature>` prefix
- Examples: `useSharkordVoiceRouter`, `useSharkordStreamState`

## File Naming

- Components: PascalCase (e.g., `VoiceChannelPanel.tsx`)
- Utils: camelCase (e.g., `normalizeUserId.ts`)
- Compatibility layers: `*-compat.ts` in `src/utils/`

## SDK Compatibility

- Centralize in `src/utils/*-compat.ts`
- Mark with `TODO(SDK-upgrade): Remove after SDK >= X.Y.Z`
- One file per concern

## Testing

- Test names MUST include `[REQ-xxx]` for traceability
- Three-tier pyramid: unit → integration → docker E2E

---

*Update this file when conventions evolve. Propose changes via PR.*
