# Sharkord Docker — Binary-Strategien & Details

## Strategie A: Init-Container (yt-dlp / spezifisches ffmpeg-Static-Build)

Wählen wenn das Plugin yt-dlp oder ein spezifisches ffmpeg-Static-Build benötigt.
Init-Container lädt Binaries idempotent — nur wenn noch nicht vorhanden.

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

## Strategie B: Dockerfile (nur ffmpeg via apt)

Wählen wenn nur `ffmpeg` via apt ausreicht — kein yt-dlp, kein Static-Build.

```dockerfile
# Dockerfile.dev
FROM sharkord/sharkord:{{platform.sharkord.image_tag}}

USER root
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
USER bun
```

## Port-Register

| Plugin | Web-Port | Mediasoup Signal | Mediasoup RTP |
|--------|----------|-----------------|---------------|
| sharkord-vid-with-friends | 3000 | — | 40000–40100/udp |
| sharkord-hero-introducer | 4991 | 40000/tcp | 40000/udp |
| _(neues Projekt)_ | freien Port wählen | freien Port wählen | freien Port wählen |
