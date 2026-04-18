# Template Gap-Analyse — Stand 2026-04-01

Vergleich zwischen den generischen Templates in `agent-meta/agents/` und den
instanziierten Agenten in `sk_plugin` (Präfix `vwf`) und `sk_hero_introduce` (Präfix `hi`).

---

## Gesamtbewertung

Die Templates decken ca. **70 %** der realen Agenten-Inhalte ab.
Der fehlende Anteil besteht aus:

1. **Projektspezifischem Kontext**, der korrekt als `{{PLATZHALTER}}` gehört
2. **Konkrete Best-Practices aus den Projekten**, die ins Template zurückfließen müssen
3. **Neuen Abschnitten**, die in den Projekten entstanden sind, aber im Template fehlen
4. **Inkonsistenzen zwischen vwf und hi**, die vereinheitlicht werden sollten

---

## ORCHESTRATOR

### Fehlt im Template (in Projekten vorhanden)

| Inhalt | Quelle | Priorität |
|--------|--------|-----------|
| Testsystem Neuaufsatz Startup-Display (ASCII-Box mit Token, URL, Debug-Cache) | vwf + hi | Hoch |
| Docker-Kommandos im Dev-Environment Block konkret ausformuliert | vwf + hi | Hoch |
| DoD-Punkt: Zod-Validierung für Input-Schemas | vwf | Mittel |

### Unterschiede vwf ↔ hi

| Aspekt | vwf | hi |
|--------|-----|----|
| DoD-Punkt Zod | Ja | Nein |
| Startup-Display | Vollständig (inkl. Debug-Cache) | Minimal |

### Empfehlung

- Startup-Display-Block als optionales Snippet ins Template aufnehmen
- Zod-DoD-Punkt als `(falls zutreffend)` markieren

---

## DEVELOPER

### Fehlt im Template (in Projekten vorhanden)

| Inhalt | Quelle | Priorität |
|--------|--------|-----------|
| Plugin-SDK Referenz (PluginContext API, Events, Commands, Settings, Voice-Actions) | vwf + hi | Hoch |
| Command-Registrierungs-Pattern (TypeScript-Codebeispiel) | vwf + hi | Hoch |
| Mediasoup Streaming Pattern (Router → Transport → Producer → Stream → Cleanup) | vwf | Hoch |
| Daten-Persistenz-Pattern (JSON-Dateien in `<pluginPath>/data/`) | hi | Mittel |
| Plugin `package.json`-Format (inkl. entry-point: single vs. server/client) | vwf + hi | Mittel |
| Zod-Validierung in Code-Konventionen | vwf | Mittel |
| Explizite SDK-Zielversion | vwf | Niedrig |

### Unterschiede vwf ↔ hi

| Aspekt | vwf | hi |
|--------|-----|----|
| Architektur-Komplexität | 7 Module (`queue/`, `stream/`, `sync/`, `commands/`, `ui/`, `utils/`, `index.ts`) | 2 Dateien (`server.ts`, `client.ts`) |
| Zod in Code-Konventionen | Ja | Nein |
| UI-Komponenten | React (`components.tsx`) | Keine |
| Daten-Persistenz | Streams (In-Memory) | JSON-Dateien |
| entry-point | `export { onLoad, onUnload, components }` | `export { onLoad, onUnload }` |
| SDK-Versionspinning | `@sharkord/plugin-sdk@0.0.16` | Unversioned |

### Empfehlung

- Placeholder `{{PLUGIN_SDK_REFERENCE}}` ergänzen mit PluginContext, Events-Tabelle
- Zwei Architektur-Varianten im Template zeigen: *Simple* (2 Dateien) und *Modular* (Module-Verzeichnisse)
- Zod als optionaler Punkt kennzeichnen

---

## TESTER

### Fehlt im Template (in Projekten vorhanden)

| Inhalt | Quelle | Priorität |
|--------|--------|-----------|
| Docker Testsystem Startup-Display (Token-Extraktion, Warnung bei `--volumes`) | vwf + hi | Hoch |
| Abschnitt "Testbare Bereiche" (projektspezifische Funktionsbereiche) | vwf + hi | Mittel |
| Bestehende Test-Dateien Inventar (Unit/Integration/E2E Liste) | vwf | Mittel |
| Mock-Helper-Pattern (`mock-plugin-context.ts`) | vwf | Mittel |
| Warnung: bei `docker compose down --volumes` NEUEN Token extrahieren | vwf + hi | Mittel |

### Unterschiede vwf ↔ hi

| Aspekt | vwf | hi |
|--------|-----|----|
| Test-Dateien Inventar | Detailliert (9 Unit + 3 Integration) | Nicht aufgelistet |
| Testbare Bereiche | Queue, Stream, Sync, Commands, UI | Music-Map, Daily-Greets, Commands, Playback, Settings |
| Mock-Helpers | `mock-plugin-context.ts` dokumentiert | Nur implizit erwähnt |
| Docker Startup-Box | Mit Debug-Cache-Verweis | Minimal |

### Empfehlung

- Optionalen Abschnitt `## Testbare Bereiche` hinzufügen mit Placeholder `{{TESTABLE_AREAS}}`
- Test-Dateien-Inventar als optionalen Abschnitt mit Placeholder `{{TEST_FILES_INVENTORY}}`
- Docker Startup-Display-Block als Standard ins Template

---

## VALIDATOR

### Fehlt im Template (in Projekten vorhanden)

| Inhalt | Quelle | Priorität |
|--------|--------|-----------|
| **E2E Manueller Test-Workflow** (19-Punkte-Ablauf, Log-Prüfung, Bewertungs-Tabelle) | hi | Hoch |
| Code-Qualitäts-Tabelle konkret (kein `node:`, Zod, Error Handling, Logging-Pattern) | vwf | Hoch |
| TodoWrite-Integration für Fortschritts-Tracking im Validator | hi | Mittel |
| Bug-Dokumentation → Developer Übergabe-Workflow | hi | Mittel |

### hi-validator hat komplett neuen Abschnitt: "Interaktiver Manueller Test (E2E)"

Enthält:
- Voraussetzungen (Plugin läuft, Voice-Channel existiert)
- 19-Punkte Befehlsreihenfolge (Data-Read, Data-Write, Negativ, Playback, etc.)
- Log-Prüfung pro Befehl (Docker-Logs analysieren)
- Bewertungs-Tabelle: PASS / FAIL / FAIL(SDK)
- Abschluss-Report mit Zusammenfassung

**Das fehlt in vwf komplett und ist nicht im Template.**

### Unterschiede vwf ↔ hi

| Aspekt | vwf | hi |
|--------|-----|----|
| E2E Manueller Test | Nicht vorhanden | Vollständiger 19-Punkte-Workflow |
| Code-Qualitäts-Tabelle | Explizit (7 Regeln) | Implizit |
| TodoWrite in Validator | Nein | Ja |

### Empfehlung

- E2E Manueller Test-Abschnitt als optionalen Block ins Template aufnehmen mit Platzhalter `{{E2E_TEST_COMMANDS}}`
- Code-Qualitäts-Tabelle konkretisieren mit Standard-Regeln + Platzhalter für projektspezifische Ergänzungen
- Bug aus hi-validator beheben: Titel enthält noch `vwf-release` statt `hi-release`

---

## REQUIREMENTS

### Fehlt im Template (in Projekten vorhanden)

| Inhalt | Quelle | Priorität |
|--------|--------|-----------|
| Detaillierte Anforderungs-Kategorien-Liste | vwf + hi | Hoch |
| REQ-Bereich-Angabe (aktuell höchste ID) | vwf | Mittel |
| Prioritäten mit konkretem Versions-Ziel verknüpft | vwf | Niedrig |

### Unterschiede vwf ↔ hi

| Aspekt | vwf | hi |
|--------|-----|----|
| Kategorien | 7 (Wiedergabe, Queue, Hybrid-Sync, Lifecycle, Stream-Vorbereitung, UI-Steuerung, NFA) | 6 (Wiedergabe, Mapping, Steuerung, Verhalten, Lifecycle, NFA) |
| REQ-Bereich | Explizit `REQ-001` bis `REQ-040` | Implizit |
| Versions-Ziel in Prioritäten | Ja (`v0.1.0`) | Nein |

### Empfehlung

- Beispiel-Kategorien ins Template als Orientierung, `{{REQ_CATEGORIES}}` weiterhin als Pflicht-Platzhalter behalten
- REQ-Bereich-Hinweis standardisieren

---

## DOCUMENTER

### Fehlt im Template (in Projekten vorhanden)

| Inhalt | Quelle | Priorität |
|--------|--------|-----------|
| **Maintenance Template** (Feature-Name, Geänderte Dateien, Methoden, Flows, Doku-Checkliste) | vwf | Hoch |
| Qualitätskriterien für CODEBASE_OVERVIEW.md (4 Punkte) | vwf | Mittel |
| Zeilennahe Referenzen als Qualitätsmerkmal | vwf | Niedrig |
| Erweiterte Conclusions-Kategorien (7 Typen inkl. Docker, Dependencies, Performance) | vwf | Mittel |

### Maintenance Template (aus vwf-documenter) — fehlt komplett im Template:

```markdown
## Feature: [Name]

**Geänderte Dateien:**
- src/[module]/file.ts — [kurze Beschreibung]

**Neue/Geänderte Methoden:**
- Class.newMethod() — [signature]

**Flows die sich änderten:**
- [Flow-Name]: [old] → [new]

**Doku Updates:**
- [x] docs/CODEBASE_OVERVIEW.md
- [ ] docs/ARCHITECTURE.md (falls Modul-Beziehungen ändern)
- [ ] README.md (falls neue Commands/Setup-Schritte)
```

### Unterschiede vwf ↔ hi

| Aspekt | vwf | hi |
|--------|-----|----|
| Maintenance Template | Detailliert (6 Abschnitte) | Vereinfacht (5 Abschnitte) |
| Qualitätskriterien | Explizit (4 Punkte) | Implizit |
| Conclusions-Tiefe | 7 Kategorien (inkl. Docker, Environment, Performance) | 3 Kategorien |
| Zeilennahe Referenzen | Ja | Nein |

### Empfehlung

- Maintenance Template direkt ins generische Template aufnehmen (beste Ergänzung)
- Qualitätskriterien als Checkliste standardisieren

---

## RELEASE

### Fehlt im Template (in Projekten vorhanden)

| Inhalt | Quelle | Priorität |
|--------|--------|-----------|
| Build-Script-Variante mit Timestamp-Suffix (für Dist-`package.json`) | vwf | Hoch |
| Asset-Naming-Konvention (Sharkord erkennt Plugin am Dateinamen!) | vwf | Hoch |
| ZIP-Inhalt-Spezifikation (welche Dateien, Verzeichnisstruktur) | vwf + hi | Hoch |
| Binary-Handling-Tabelle (ffmpeg, yt-dlp — Quellen für Linux/Windows) | vwf | Mittel |
| GitHub CLI PATH-Problem-Hinweis (Windows: `C:\Program Files\GitHub CLI`) | vwf | Niedrig |
| Mindest-Sharkord-Version (`>= 0.0.7` vs `>= 0.0.15`) | vwf + hi | Niedrig |

### Unterschiede vwf ↔ hi

| Aspekt | vwf | hi |
|--------|-----|----|
| Build-Script | `scripts/write-dist-package.ts` (Timestamp in Version) | `build.ts` (einfach, 1:1) |
| Dist-package.json | Mit Timestamp-Suffix `0.1.0-alpha.1-190326-20_26_02` | Identisch mit Quell-`package.json` |
| ZIP-Inhalt | `index.js`, `package.json`, `bin/`, `logo.png` (Einzeldateien) | Ganzes `dist/sharkord-hero-introducer/`-Verzeichnis |
| Asset-Naming | Exakt `sharkord-vid-with-friends` (kritisch!) | Ganzes Verzeichnis |
| Binaries | ffmpeg + yt-dlp | nur ffmpeg |
| Min. Sharkord | >= 0.0.7 | >= 0.0.15 |

### Bekannter Bug in hi-release.md

- Zeile 14 enthält fälschlicherweise `vwf-release` statt `hi-release` im Agenten-Titel

### Empfehlung

- Zwei Build-Varianten explizit ins Template aufnehmen (Simple vs. Timestamp)
- Asset-Naming als kritischen Abschnitt hervorheben (`{{ASSET_NAME}}` Platzhalter)
- Binary-Handling als Platzhalter `{{REQUIRED_BINARIES}}` + Beispiel-Tabelle

---

## Fehlende Platzhalter in den Templates (Zusammenfassung)

Diese `{{PLATZHALTER}}` sollten in den Templates ergänzt werden:

| Platzhalter | Gehört in | Beispiel vwf | Beispiel hi |
|-------------|-----------|--------------|-------------|
| `{{PLUGIN_SDK_REFERENCE}}` | developer | PluginContext, Voice-Actions, Events | PluginContext, Voice-Actions, Events |
| `{{TESTABLE_AREAS}}` | tester | Queue, Stream, Sync, Commands | Music-Map, Daily-Greets, Commands |
| `{{TEST_FILES_INVENTORY}}` | tester | 9 Unit + 3 Integration Dateien | (leer) |
| `{{E2E_TEST_COMMANDS}}` | validator | (leer) | 19 Slash-Commands |
| `{{ASSET_NAME}}` | release | `sharkord-vid-with-friends` | `sharkord-hero-introducer` |
| `{{REQUIRED_BINARIES}}` | release | ffmpeg + yt-dlp | ffmpeg |
| `{{SHARKORD_MIN_VERSION}}` | release | >= 0.0.7 | >= 0.0.15 |
| `{{ZIP_CONTENTS}}` | release | index.js, package.json, bin/, logo.png | dist/-Verzeichnis |

---

## Priorisierte Handlungsliste

### Tier 1 — Direkt umsetzen (hoher Impact)

- [ ] **validator/template**: E2E Manueller Test-Abschnitt hinzufügen (basierend auf hi-validator)
- [ ] **developer/template**: Plugin-SDK Referenz Section ergänzen
- [ ] **developer/template**: Zwei Architektur-Varianten zeigen (Simple vs. Modular)
- [ ] **release/template**: Asset-Naming-Abschnitt + `{{ASSET_NAME}}`-Platzhalter
- [ ] **release/template**: ZIP-Inhalt-Platzhalter `{{ZIP_CONTENTS}}`

### Tier 2 — Bald (Best Practices)

- [ ] **documenter/template**: Maintenance Template-Block aufnehmen
- [ ] **orchestrator/template**: Startup-Display-Snippet aufnehmen
- [ ] **tester/template**: `{{TESTABLE_AREAS}}` + optionalen Test-Inventar-Abschnitt
- [ ] **validator/template**: Code-Qualitäts-Tabelle konkretisieren

### Tier 3 — Später (Verfeinerung)

- [ ] **requirements/template**: Beispiel-Kategorien zeigen
- [ ] **documenter/template**: Conclusions-Kategorien-Liste
- [ ] **release/template**: Binary-Handling-Tabelle

### Bugfix

- [ ] **hi-release.md**: Zeile 14 — `vwf-release` → `hi-release` korrigieren
