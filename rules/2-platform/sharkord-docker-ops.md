---
description: Sharkord Docker-Betriebswissen — Port-Register, SYS_NICE, Binary-Strategien, Token
---

# Sharkord Docker-Konventionen

## Version Pinning (KRITISCH)

NIE `latest`-Tag für Sharkord Docker-Images verwenden. Immer auf konkrete Version pinnen. Version explizit nach Kompatibilitätstest aktualisieren.

```yaml
# RICHTIG — gepinnte Version
image: ghcr.io/sharkord/sharkord:v0.0.20

# FALSCH — nie verwenden
image: ghcr.io/sharkord/sharkord:latest
```

## Pflicht-Capability SYS_NICE

```yaml
cap_add:
  - SYS_NICE    # Mediasoup worker benötigt thread priority scheduling
```

## Plugin-Verzeichnis-Namenskonvention

Verzeichnisname in `plugins/` muss exakt dem `name`-Feld in `package.json` entsprechen.

```yaml
volumes:
  - ./dist/<plugin-name>:/home/bun/.config/sharkord/plugins/<plugin-name>
```

## Access Token nach Volume-Reset

```bash
docker logs <container-name> 2>&1 | grep -i "token\|access" | head -5
```

**WARNUNG: `docker compose down --volumes` löscht die Datenbank → Token ungültig!**

## Build Context

Docker builds MUST respect the plugin's build variant:

| Build Variant | Docker Context | Notes |
|--------------|----------------|-------|
| **Variant A (Timestamp)** | `dist/<plugin-name>/` contains `index.js`, `package.json` (with timestamp), `bin/` | Dockerfile copies from `dist/` |
| **Variant B (1:1 Copy)** | `dist/<plugin-name>/` contains `server.js`, `client.js`, `package.json` (1:1) | Dockerfile copies from `dist/` |

**Important:** The Dockerfile `COPY` source must match the build output structure. If switching from Variant B to A, update both the build script AND the Dockerfile.

## Binary-Strategie

- **Nur ffmpeg via apt** → Strategie B: Dockerfile (einfacher, kein separater Service)
- **yt-dlp oder spezifisches ffmpeg-Static-Build** → Strategie A: Init-Container

Vollständige YAML-Vorlagen (Init-Container, Dockerfile, Port-Register):
→ `rules/2-platform/_wf-sharkord-docker-binaries.md` (Read bei Bedarf)
