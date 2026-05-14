---
description: Sharkord Build Conventionen — verbindlicher Standard für alle Plugin-Builds
---

# Sharkord Build Conventionen

## Standard Build-Script

Jedes Sharkord Plugin MUSS `scripts/build.ts` als Build-Einstiegspunkt verwenden.

### Verbotene Build-Ansätze
- Inline Build-Scripts in `package.json` (`"build": "bun build ... && cp ... && mkdir ..."`)
- Mehrere Entry-Points (`server.ts` + `client.ts`)
- Build-Logik über mehrere Dateien verteilt
- Manuelle `cp`/`mkdir` Shell-Kommandos im Build-Script

### Standard Build-Kommando
```bash
bun scripts/build.ts
```

### Erwartete Ausgabe-Struktur
```
dist/<plugin-name>/
  index.js          # Minified ESM Bundle
  package.json      # Plugin Metadaten (Name, Version, sharkord-Block)
  logo.png          # Plugin Logo (optional)
  bin/              # Externe Binaries (ffmpeg, yt-dlp, etc.)
```

### Build-Script Anforderungen
1. **Einstieg:** `src/index.ts` als einziger Entry-Point
2. **Ausgabe:** `dist/<plugin-name>/`
3. **Format:** ESM, minifiziert, Bun-Target
4. **Metadaten:** `package.json` mit `name`, `version`, `sharkord`-Block
5. **Binär-Verzeichnis:** `bin/` wird leer erstellt (für externe Dependencies)

## Referenz-Implementation

→ `.agent-meta/templates/plugin-starter/scripts/build.ts`

## Migration

Bestehende Plugins mit non-standard Build:
1. `.agent-meta/templates/plugin-starter/scripts/build.ts` kopieren
2. `package.json` anpassen: `"build": "bun scripts/build.ts"`
3. Entry-Point auf `src/index.ts` standardisieren
4. `bun run build` testen → `dist/`-Struktur verifizieren
5. Alte Build-Logik entfernen
