---
description: Sharkord Plugin-SDK Konventionen — gilt automatisch für alle Agenten
---

# Sharkord Plugin-SDK

## PluginContext API

```typescript
ctx.log(message) / ctx.debug(message) / ctx.error(message)
ctx.path                              // Absoluter Plugin-Pfad
ctx.events.on(event, handler)
ctx.commands.register(definition)
ctx.settings.register(definitions)
ctx.voice.getRouter(channelId)        // SDK >= 0.0.16
ctx.voice.createStream(options)
ctx.voice.getListenInfo()             // { ip, announcedAddress }
```

## Command-Registrierung

```typescript
ctx.commands.register<{ userId: string; filePath: string }>({
  name: "my-command",
  description: "Kurzbeschreibung.",
  args: [
    { name: "userId",   type: "string", required: true },
    { name: "filePath", type: "string", required: false },
  ],
  async executes(invokerCtx, args) { /* Implementierung */ },
});
```

## Naming Conventions

### Hooks
- **Mandatory prefix:** `useSharkord<Feature>` for all Sharkord-specific hooks.
- Examples: `useSharkordVoiceRouter`, `useSharkordStreamState`, `useSharkordHeroAnimation`
- Rationale: Prevents collisions with generic React hooks and makes intent explicit.

### Components
- PascalCase, descriptive (e.g., `VoiceChannelPanel`, `StreamOverlay`)

### Utils
- camelCase, action-oriented (e.g., `normalizeUserId`, `formatStreamDuration`)

## Plugin Config Export

`src/index.ts` MUST default-export a valid `PluginConfig` object:

```typescript
import { PluginConfig } from "@sharkord/plugin-sdk";

const config: PluginConfig = {
  name: "my-plugin",
  version: "1.0.0",
  // ... required fields
};

export default config;
```

## SDK Compatibility Layer Pattern

When supporting multiple SDK versions or deprecated APIs, use a centralized compatibility layer:

### Rules
1. **Centralize compatibility code** in dedicated files under `src/utils/` (e.g., `voice-compat.ts`, `command-compat.ts`).
2. **Never inline compatibility fallbacks** in feature code.
3. **Mark every fallback** with a lifecycle TODO:
   ```typescript
   // TODO(SDK-upgrade): Remove after SDK >= 0.1.0 — ctx.actions.voice deprecated in 0.0.16
   ```
4. **One file per concern** — `voice-compat.ts` for voice, `command-compat.ts` for commands.

### Example
```typescript
// utils/voice-compat.ts
// TODO(SDK-upgrade): Remove after SDK >= 0.1.0

import { PluginContext } from "@sharkord/plugin-sdk";

export function resolveVoiceRouter(ctx: PluginContext, channelId: string) {
  if (ctx.voice) {
    return ctx.voice.getRouter(channelId);
  }
  // Fallback for SDK < 0.0.16
  return ctx.actions.voice.getRouter(channelId);
}
```

## Don'ts

- KEIN `ctx.actions.voice` — deprecated seit SDK 0.0.16 → `ctx.voice`
- KEIN `child_process.spawn` → `Bun.spawn`
- KEIN `node:` Prefix wenn Bun-Äquivalent existiert
- KEINE camelCase Spaltennamen in SQLite → snake_case
- KEIN `var` → `const` / `let`
- KEIN implizites `any`
- KEINE Hooks ohne `useSharkord`-Prefix
- KEIN `src/index.ts` ohne `PluginConfig` Default-Export
- KEINE inline Compatibility-Fallbacks ohne `TODO(SDK-upgrade)` Marker

Vollständige Mediasoup-Implementierung (Transport, Producer, Events):
→ `rules/2-platform/_wf-sharkord-mediasoup.md` (Read bei Bedarf)
