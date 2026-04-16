---
description: Sharkord Plugin-SDK Konventionen — gilt automatisch für alle Agenten
---

# Sharkord Plugin-SDK

## Plugin Entry-Point

```typescript
const onLoad = async (ctx: PluginContext) => {
  // Initialisierung: Commands, Settings, Events registrieren
};

const onUnload = (ctx: PluginContext) => {
  // Cleanup: Streams, Transports, Producers schließen
};

export { onLoad, onUnload };
```

## PluginContext API

```typescript
// Logging
ctx.log(message)        // Info-Level
ctx.debug(message)      // Debug-Level
ctx.error(message)      // Error-Level

// Plugin-Pfad
ctx.path                // Absoluter Pfad zum Plugin-Verzeichnis

// Events
ctx.events.on(event, handler)         // Event-Handler registrieren

// Commands
ctx.commands.register(definition)     // Command registrieren

// Settings
ctx.settings.register(definitions)   // Settings registrieren

// Voice/Mediasoup (SDK >= 0.0.16)
ctx.voice.getRouter(channelId)        // Mediasoup Router holen
ctx.voice.createStream(options)       // Audio-Stream registrieren
ctx.voice.getListenInfo()             // RTP Listen-Adresse { ip, announcedAddress }
```

## Command-Registrierung

```typescript
ctx.commands.register<{ userId: string; filePath: string }>({
  name: "my-command",
  description: "Kurzbeschreibung des Commands.",
  args: [
    { name: "userId",   type: "string", required: true },
    { name: "filePath", type: "string", required: false },
  ],
  async executes(invokerCtx, args) {
    // Implementierung
  },
});
```

## Mediasoup Audio-Streaming

```typescript
const router = ctx.voice.getRouter(channelId);
const { ip, announcedAddress } = ctx.voice.getListenInfo();

const transport = await router.createPlainTransport({
  listenInfo: { protocol: "udp", ip, announcedAddress },
  rtcpMux: false,
  comedia: true,
});

const producer = await transport.produce({
  kind: "audio",
  rtpParameters: {
    codecs: [{ mimeType: "audio/opus", payloadType: 101, clockRate: 48000, channels: 2 }],
    encodings: [{ ssrc: 1234 }],
  },
});

const stream = ctx.voice.createStream({
  channelId,
  key: "my-stream",
  title: "Stream-Titel",
  producers: { audio: producer },
});

// Cleanup (immer in voice:runtime_closed):
stream.remove();
producer.close();
transport.close();
```

## Events-Referenz

| Event | Auslöser |
|-------|----------|
| `voice:runtime_initialized` | Voice-Channel geöffnet |
| `voice:runtime_closed` | Voice-Channel geschlossen → **CLEANUP erforderlich!** |
| `user:joined_voice` | Nutzer betritt Voice-Channel (SDK >= 0.0.16) |
| `user:left_voice` | Nutzer verlässt Voice-Channel (SDK >= 0.0.16) |
| `user:joined` | Nutzer betritt den Server |

## Don'ts (Sharkord-spezifisch)

- KEIN `ctx.actions.voice` — deprecated seit SDK 0.0.16 → stattdessen `ctx.voice`
- KEIN `child_process.spawn` → immer `Bun.spawn`
- KEIN `node:` Prefix wenn Bun-Äquivalent existiert (z.B. `Bun.file` statt `node:fs`)
- KEINE camelCase Spaltennamen in SQLite-Queries → Sharkord nutzt snake_case
- KEIN direkter Zugriff auf `window` / `document` — kein Browser-API
- KEIN `var` → `const` / `let`
- KEIN implizites `any`
