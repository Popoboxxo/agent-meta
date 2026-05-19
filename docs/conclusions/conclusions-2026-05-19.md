# Erkenntnisse — 19. Mai 2026

## Session-Zusammenfassung

Windows-Kompatibilitäts-Fixes für die global installierte CLI `opencode-pixel-office` (v1.2.2, npm) dokumentiert und als Cross-Project Learning erfasst.

---

## 1. Windows-Inkompatibilitäten in Node.js CLIs

### Drei kritische Bugs in `opencode-pixel-office`

Die CLI `bin/opencode-pixel-office.js` enthielt drei Unix-spezifische Aufrufe die auf Windows mit ENOENT scheitern:

1. **`spawn('tsx', ...)`** — Shebang-Skripte aus `node_modules/.bin/` sind auf Windows nicht direkt ausführbar
   - Lösung: `node --import <tsx/loader.mjs>` auf Windows, Fallback über `cmd /c tsx.cmd`

2. **`lsof -t -i :PORT`** — Port-Belegungsprüfung via `lsof` ist Unix-only
   - Lösung: PowerShell `Get-NetTCPConnection -LocalPort PORT` als Windows-Äquivalent

3. **`start URL`** — `start` ist cmd.exe-Builtin, kein Binary
   - Lösung: `start "" "URL"` mit leerem Titel-Argument

### Zusätzliche Anforderung
- Import von `pathToFileURL` aus `node:url` für das `--import` Flag

### Wichtige Einschränkung
Dies sind lokale Änderungen im globalen npm-Paket. Bei `npm update -g opencode-pixel-office` werden sie überschrieben. Der Fix muss als GitHub Issue + PR an das Upstream-Repository gemeldet werden.

### Cross-Project Relevanz
Dieses Pattern betrifft ALLE Node.js CLIs die Unix-spezifische Befehle verwenden. Bei der Entwicklung eigener CLIs sollte von Anfang an plattformübergreifende Kompatibilität berücksichtigt werden.

---

## 2. Dokumentation aktualisiert

- `docs/LEARNINGS.md` → Neuer Eintrag `BUG-002` mit vollständigem Fix-Pattern
- Diese Conclusions-Datei erstellt
