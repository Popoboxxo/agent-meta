---
description: Sharkord Docker-Betriebswissen — Port-Register, SYS_NICE, Binary-Strategien, Token
---

# Sharkord Docker-Konventionen

## Port-Register (alle bekannten Sharkord-Plugins)

Ports müssen projektweit eindeutig sein, wenn mehrere Plugins gleichzeitig laufen sollen.

| Plugin | Web-Port | Mediasoup Signal | Mediasoup RTP |
|--------|----------|-----------------|---------------|
| sharkord-vid-with-friends | 3000 | — | 40000–40100/udp |
| sharkord-hero-introducer | 4991 | 40000/tcp | 40000/udp |
| _(neues Projekt)_ | **freien Port wählen** | **freien Port wählen** | **freien Port wählen** |

## Pflicht-Capability SYS_NICE

Mediasoup benötigt Thread-Priority-Scheduling. Ohne diese Capability startet der Worker
möglicherweise nicht korrekt.

```yaml
cap_add:
  - SYS_NICE    # Mediasoup worker benötigt thread priority scheduling
```

## Plugin-Verzeichnis-Namenskonvention

Der Verzeichnisname in `plugins/` muss exakt dem `name`-Feld in `package.json` entsprechen.
Sharkord erkennt das Plugin anhand dieses Verzeichnisnamens.

```yaml
volumes:
  - ./dist/<plugin-name>:/home/bun/.config/sharkord/plugins/<plugin-name>
```

## Access Token nach Volume-Reset

Sharkord generiert beim ersten Start ein Access-Token, das in den Container-Logs erscheint.

```bash
# Token extrahieren
docker logs <container-name> 2>&1 | grep -i "token\|access" | head -5
```

**WARNUNG: Bei `docker compose down --volumes` wird die Datenbank gelöscht → Token ungültig!**
Immer nach einem Volume-Reset einen neuen Token aus den Logs extrahieren.

## Binary-Strategie

### Strategie A: Init-Container

Wählen wenn das Plugin yt-dlp oder ein spezifisches ffmpeg-Static-Build benötigt.
Der Init-Container lädt Binaries idempotent herunter — nur wenn sie noch nicht vorhanden sind.

```yaml
services:
  init-binaries:
    image: alpine:latest
    entrypoint: /bin/sh
    command:
      - -c
      - |
        BIN_DIR=/binaries
        if [ -f "$$BIN_DIR/ffmpeg" ] && [ -f "$$BIN_DIR/yt-dlp" ]; then
          echo "Binaries already exist, skipping."
          exit 0
        fi
        apk add --no-cache wget xz
        # yt-dlp (standalone binary)
        wget -q -O "$$BIN_DIR/yt-dlp" https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux
        chmod +x "$$BIN_DIR/yt-dlp"
        # ffmpeg (static build)
        wget -q -O /tmp/ffmpeg.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
        mkdir -p /tmp/ffmpeg-extract
        tar -xf /tmp/ffmpeg.tar.xz -C /tmp/ffmpeg-extract --strip-components=1
        cp /tmp/ffmpeg-extract/ffmpeg "$$BIN_DIR/ffmpeg"
        chmod +x "$$BIN_DIR/ffmpeg"
        rm -rf /tmp/ffmpeg.tar.xz /tmp/ffmpeg-extract
        echo "Done!"
    volumes:
      - plugin-binaries:/binaries

  sharkord:
    depends_on:
      init-binaries:
        condition: service_completed_successfully
    volumes:
      - plugin-binaries:/home/bun/.config/sharkord/plugins/<plugin-name>/bin
```

### Strategie B: Dockerfile

Wählen wenn nur `ffmpeg` via apt ausreicht (kein yt-dlp, kein spezifisches Static-Build).

```dockerfile
# Dockerfile.dev
FROM sharkord/sharkord:{{platform.sharkord.image_tag}}

USER root
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
USER bun
```

**Entscheidung:**
- Nur ffmpeg via apt → Strategie B (einfacher, kein separater Service)
- yt-dlp oder spezifisches ffmpeg-Static-Build → Strategie A (Init-Container)
