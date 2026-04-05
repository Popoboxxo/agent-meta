---
name: sharkord-developer
version: "2.0.0"
based-on: "1-generic/developer.md@1.4.1"
description: "Sharkord-spezifischer Developer-Agent. Ergänzt den generischen Developer um Sharkord Plugin-SDK Wissen: PluginContext API, Mediasoup Audio-Streaming, Command-Registrierung, Events, Sharkord-spezifische Don'ts."
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
      ## Sharkord Plugin-SDK

      ### Plugin Entry-Point

      ```typescript
      const onLoad = async (ctx: PluginContext) => {
        // Initialisierung: Commands, Settings, Events registrieren
      };

      const onUnload = (ctx: PluginContext) => {
        // Cleanup: Streams, Transports, Producers schließen
      };

      export { onLoad, onUnload };
      ```

      ### PluginContext API

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

      ### Command-Registrierung

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

      ### Mediasoup Audio-Streaming

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

      ### Events-Referenz

      | Event | Auslöser |
      |-------|----------|
      | `voice:runtime_initialized` | Voice-Channel geöffnet |
      | `voice:runtime_closed` | Voice-Channel geschlossen → **CLEANUP erforderlich!** |
      | `user:joined_voice` | Nutzer betritt Voice-Channel (SDK >= 0.0.16) |
      | `user:left_voice` | Nutzer verlässt Voice-Channel (SDK >= 0.0.16) |
      | `user:joined` | Nutzer betritt den Server |

  - op: replace
    anchor: "## Don'ts"
    content: |
      ## Don'ts

      - KEINE Default-Exports
      - KEINE Feature ohne REQ-ID
      - KEINE Secrets / API-Keys im Code
      - KEINE Implementierung ohne dass eine REQ-ID in `docs/REQUIREMENTS.md` existiert
      - KEIN Code ohne zugehörigen Test (mindestens Test-Skeleton für den Tester)

      <!-- PROJEKTSPEZIFISCH: Weitere Don'ts → in .claude/3-project/{{PREFIX}}-developer-ext.md -->
      {{EXTRA_DONTS}}

      ### Sharkord-spezifische Don'ts

      - **KEIN** `ctx.actions.voice` — deprecated seit SDK 0.0.16 → stattdessen `ctx.voice`
      - **KEIN** `child_process.spawn` → immer `Bun.spawn`
      - **KEIN** `node:` Prefix wenn Bun-Äquivalent existiert (z.B. `Bun.file` statt `node:fs`)
      - **KEINE** camelCase Spaltennamen in SQLite-Queries → Sharkord nutzt snake_case
      - **KEIN** direkter Zugriff auf `window` / `document` — kein Browser-API
      - **KEIN** `var` → `const` / `let`
      - **KEIN** implizites `any`
---
