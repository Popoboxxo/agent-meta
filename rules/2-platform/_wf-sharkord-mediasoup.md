# Sharkord Mediasoup Audio-Streaming — Vollständige Referenz

## Transport & Producer erstellen

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
```

## Cleanup (immer in `voice:runtime_closed`)

```typescript
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
