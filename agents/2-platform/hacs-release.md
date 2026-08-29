---
name: release
version: "1.0.1"
based-on: "1-generic/release.md@1.5.0"
description: "HACS Integration Release — Versioning, Release-Naming (Tag-Format, Pre-Release, Immutabilität), Tag↔manifest-Sync, VERSION nur mit Migrator, GitHub Release."
hint: "Versioning, changelog, Build-Artifact und GitHub Release für HACS-Integrationen"
prompt_mode: modern
extends: "1-generic/release.md"
patches:
  - op: append-after
    anchor: "<persona>"
    content: |
      ## HACS Release-Regeln

      - **Tag↔manifest-Sync:** `manifest.json` `version` MUSS dem Git-Tag entsprechen (z.B. `v1.2.3` ↔ `"version": "1.2.3"`).
      - **VERSION nur mit Migrator:** Erhöhung von `manifest.VERSION` erfordert registrierten `async_migrate_entry`-Handler, sonst `Migration handler not found` beim User-Update.
      - **Release-Dreiklang:** Commit → Tag → echtes GitHub Release (mit Changelog). HACS zeigt nur echte Releases.

      ### Release-Naming (Details: Skill `integration-development`, Abschnitt Release-Naming-Best-Practice)

      - **Tag-Format:** Stable `vMAJOR.MINOR.PATCH`, Beta `vX.Y.Zb<N>` (z.B. `v1.3.0b0` als GitHub-**Pre-Release**). Der `v`-Prefix gehört nur in den Tag — `manifest.version` ist bare SemVer ohne `v` (`v1.2.3` ↔ `"version": "1.2.3"`, `v1.3.0b0` ↔ `"version": "1.3.0b0"`), sonst `Invalid version`/Sortierfehler.
      - **Immutabilität:** Tags/Releases nie verschieben, löschen oder wiederverwenden (HACS cacht Versionen); Promotion beta→stable = neuer Release, nie Tag mutieren — sonst bleiben User auf Alt-Stand.
      - **SemVer:** MAJOR = Breaking (`unique_id`-/Entity-Änderungen sind IMMER breaking → MAJOR), MINOR = Feature, PATCH = Fix; `v0.x` nicht ohne Hinweis als „stabil" deklarieren.
      - **Release-Notes:** Summary + ✨ New features + 💥 Breaking changes (je mit Migration-Hinweis, Pflicht bei MAJOR) + Full-Changelog-Link.
---
