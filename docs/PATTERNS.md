# PATTERNS.md — Cross-Plugin Patterns

> This file lives in the meta-repo and documents reusable implementation patterns across all plugins.

## Pattern: SDK Compatibility Layer

**Applies to:** All plugins supporting multiple SDK versions  
**Owner:** Meta-repo maintainers  
**Status:** Active

Centralize compatibility code in `src/utils/*-compat.ts`. Mark every fallback with `TODO(SDK-upgrade): Remove after SDK >= X.Y.Z`.

→ Full specification: `rules/2-platform/sharkord-sdk.md`

---

## Pattern: Voice Action Resolution

**Applies to:** Voice/streaming plugins  
**Owner:** Meta-repo maintainers  
**Status:** Active

Use `ctx.voice.getRouter(channelId)` (SDK >= 0.0.16). For fallback probing, wrap in `resolveVoiceRouter()` in `utils/voice-compat.ts`.

---

## Pattern: Hook Naming Convention

**Applies to:** All plugins with custom React hooks  
**Owner:** Meta-repo maintainers  
**Status:** Active

All Sharkord-specific hooks MUST use the `useSharkord<Feature>` prefix (e.g., `useSharkordVoiceRouter`).

→ Full specification: `rules/2-platform/sharkord-plugin-structure.md`

---

*Add new patterns via PR against this file. Reference the originating plugin and commit for traceability.*
