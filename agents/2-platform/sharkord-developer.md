---
name: sharkord-developer
version: "2.1.2"
based-on: "1-generic/developer.md@2.3.0"
description: "Sharkord-spezifischer Developer-Agent. Ergänzt den generischen Developer um Sharkord-Build-Kommandos. Das Sharkord Plugin-SDK Wissen (PluginContext API, Mediasoup, Commands, Events, Don'ts) kommt automatisch aus der Rule rules/2-platform/sharkord-sdk.md."
hint: "Feature-Implementierung und Bugfixes nach REQ-IDs (Sharkord Plugin SDK)"
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - TodoWrite
extends: "1-generic/developer.md"
patches:
  - op: replace
    anchor: "## Development Environment"
    content: |
      ## Build & Commands

      <!-- PROJEKTSPEZIFISCH: Build-Kommandos eintragen -->
      {{DEV_COMMANDS}}

  - op: replace
    anchor: "## Don'ts"
    content: |
      ## Don'ts

      - KEINE Default-Exports
      - KEINE Feature ohne REQ-ID
      - KEINE Secrets / API-Keys im Code
      - KEINE Implementierung ohne dass eine REQ-ID in `docs/REQUIREMENTS.md` existiert
      - KEIN Code ohne zugehörigen Test (mindestens Test-Skeleton für den Tester)

      <!-- PROJEKTSPEZIFISCH: Weitere Don'ts → in {{EXTENSION_DIR}}/{{PREFIX}}-developer-ext.md -->
      {{EXTRA_DONTS}}
---
