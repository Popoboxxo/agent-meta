---
name: sharkord-feature
version: "1.0.0"
based-on: "1-generic/feature.md@1.3.1"
description: "Sharkord-spezifischer Feature-Agent. Ergänzt den generischen Feature-Lifecycle um einen Skeleton-Bootstrap-Check, der sicherstellt dass neue Plugins die minimale erforderliche Struktur haben bevor Features implementiert werden."
hint: "Neues Sharkord-Feature end-to-end — mit Skeleton-Bootstrap-Validierung"
tools:
  - Bash
  - Read
  - Glob
  - Agent
  - TodoWrite
extends: "1-generic/feature.md"
patches:
  - op: append-after
    anchor: "## Feature-Lifecycle"
    content: |
      ## Schritt 0 — Skeleton Bootstrap Check (nur bei neuen Plugins / leeren Skeletons)

      Bevor Schritt 1 beginnt, prüfe ob das Projekt das minimale Sharkord-Plugin-Skeleton hat.
      Dieser Schritt ist ein **Blocker** — fehlende Dateien müssen zuerst angelegt werden.

      ### Skeleton-Checkliste

      Prüfe ob diese Dateien existieren:

      - [ ] `package.json` — mit `name`, `version`, `scripts` (build, test), `@sharkord/plugin-sdk` in `peerDependencies`
      - [ ] `tsconfig.json` — mit `strict: true` und `outDir: "dist"`
      - [ ] `src/index.ts` — wiring-only Entry-Point mit `PluginConfig` Default-Export
      - [ ] `tests/helpers/mock-plugin-context.ts` — Test-Infrastruktur für PluginContext
      - [ ] `docker-compose.dev.yml` — lokaler Dev-Stack mit Sharkord core + Plugin mount
      - [ ] `docs/REQUIREMENTS.md` — existiert (kann leer sein, muss aber vorhanden sein)
      - [ ] `README.md` — Projekt-Readme mit Installation und Build-Anweisungen

      ### Verifikation

      ```bash
      # Quick-check ob Skeleton vollständig ist
      for f in package.json tsconfig.json src/index.ts tests/helpers/mock-plugin-context.ts docker-compose.dev.yml docs/REQUIREMENTS.md README.md; do
        test -f "$f" && echo "✓ $f" || echo "✗ $f MISSING"
      done
      ```

      ### Bei fehlenden Dateien

      1. **Sofort an `developer` delegieren:**
         ```
         Delegiere an: developer
         Aufgabe: Skeleton-Bootstrap — folgende Dateien fehlen oder sind unvollständig:
                  [Liste der fehlenden Dateien]
                  Erstelle die minimalen Skeleton-Dateien gemäß Sharkord Plugin-Struktur.
                  Verwende die bestehenden Plugins (vid-with-friends, stream-with-friends, hero-introducer) als Referenz.
         ```

      2. **Warte auf Fertigstellung.**

      3. **Erstelle dann einen separaten Commit:**
         ```
         Delegiere an: git
         Aufgabe: Commit die Skeleton-Dateien als eigenen Commit:
                  "chore: bootstrap minimal sharkord plugin skeleton"
         ```

      4. **Danach erst mit Schritt 1 (Feature-Branch) fortfahren.**

      > **Hinweis:** Wenn alle Skeleton-Dateien bereits existieren → diesen Schritt überspringen und sofort mit Schritt 1 fortfahren.

      ### Schritt 0b — Test-Pyramid Verifizierung (nur bei Features mit Voice/Streaming)

      Wenn das Feature Voice-, Streaming- oder Mediasoup-Logik betrifft, prüfe ob die Test-Pyramid vorhanden ist:

      - [ ] `tests/unit/` existiert und hat Tests für die neue Logik
      - [ ] `tests/integration/` existiert und testet Command-to-Service flows
      - [ ] `tests/docker/` existiert mit Health-Checks für Docker-E2E
      - [ ] Alle Tests verwenden `[REQ-xxx]` im Test-Namen

      Fehlende Test-Ebenen sind **Blocker** — vor Implementierung müssen sie vom `tester` angelegt werden.
