---
description: Sharkord Docker-Betriebswissen — Port-Register, SYS_NICE, Binary-Strategien, Token
---

# Sharkord Docker-Konventionen

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

## Binary-Strategie

- **Nur ffmpeg via apt** → Strategie B: Dockerfile (einfacher, kein separater Service)
- **yt-dlp oder spezifisches ffmpeg-Static-Build** → Strategie A: Init-Container

Vollständige YAML-Vorlagen (Init-Container, Dockerfile, Port-Register):
→ `rules/2-platform/_wf-sharkord-docker-binaries.md` (Read bei Bedarf)
