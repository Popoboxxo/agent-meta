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

## Don'ts

- KEIN `ctx.actions.voice` — deprecated seit SDK 0.0.16 → `ctx.voice`
- KEIN `child_process.spawn` → `Bun.spawn`
- KEIN `node:` Prefix wenn Bun-Äquivalent existiert
- KEINE camelCase Spaltennamen in SQLite → snake_case
- KEIN `var` → `const` / `let`
- KEIN implizites `any`

Vollständige Mediasoup-Implementierung (Transport, Producer, Events):
→ `rules/2-platform/_wf-sharkord-mediasoup.md` (Read bei Bedarf)
