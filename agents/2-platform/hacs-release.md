---
name: release
version: "1.0.0"
based-on: "1-generic/release.md@1.5.0"
description: "HACS Integration Release — Versioning, Tag↔manifest-Sync, VERSION nur mit Migrator, GitHub Release."
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
---
