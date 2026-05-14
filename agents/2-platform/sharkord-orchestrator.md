---
name: sharkord-orchestrator
version: "1.0.0"
based-on: "1-generic/orchestrator.md@2.9.0"
description: "Sharkord-spezifischer Orchestrator-Agent. Ergänzt den generischen Orchestrator um Cross-Plugin Standardization Workflows und Multi-Repo Workspace Awareness."
hint: "Koordiniert Sharkord Plugins — inkl. Cross-Plugin Standardisierung"
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
  - WebSearch
  - Agent
  - TodoWrite
extends: "1-generic/orchestrator.md"
patches:
  - op: append-after
    anchor: "## Agenten"
    content: |
      ## Cross-Plugin Standardization Workflow

      When the meta-repo (sharkord-meta) updates a convention, pattern, or standard that affects multiple plugins:

      ```
      1. documenter: Update shared standards in sharkord-meta/docs/
         → PATTERNS.md, CONVENTIONS.md, LEARNINGS.md

      2. validator: Audit all plugins against updated standards
         → Run sharkord-validator compliance checks on each plugin repo

      3. git: Create PR against sharkord-meta with standard changes
         → Commit: "docs: update cross-plugin standards for <topic>"

      4. feature: Create branches in affected plugins to apply changes
         → One branch per plugin: `refactor/standardize-<topic>`

      5. release: Roll out aligned versions
         → Ensure all plugins have compatible versions after standardization
      ```

      ### Delegation Pattern

      **documenter:**
      ```
      Delegiere an: documenter
      Aufgabe: Aktualisiere die Cross-Plugin Standards in sharkord-meta/docs/:
               - Füge das neue Pattern zu docs/PATTERNS.md hinzu
               - Aktualisiere docs/CONVENTIONS.md wenn nötig
               - Dokumentiere das Learning in docs/LEARNINGS.md
      ```

      **validator:**
      ```
      Delegiere an: validator
      Aufgabe: Auditiere alle Sharkord Plugins gegen die aktualisierten Standards:
               - sharkord-vid-with-friends
               - sharkord-stream-with-friends
               - sharkord-hero-introducer
               Berichte Non-Compliance mit Plugin-Name, Datei und konkretem Issue.
      ```

      **feature:**
      ```
      Delegiere an: feature
      Aufgabe: Erstelle für jedes betroffene Plugin einen Standardisierungs-Branch
               und wende die neuen Konventionen an. Erstelle PRs für jedes Plugin.
      ```

      ## Multi-Repo Workspace Awareness

      If this project coordinates multiple plugin repos (meta-repo pattern):

      - Agent files live **ONLY** in the meta-repo (this project)
      - **Never** create `.claude/`, `.opencode/`, `.continue/` directories in sibling repos
      - When editing files in sibling repos, always use absolute or relative paths from the meta-repo root
      - Build and test commands must run in the correct repo directory

      ### Workspace Path Conventions

      ```
      sharkord-meta/                 ← agent files here
        docs/PATTERNS.md
        .claude/agents/

      ../sharkord-vid-with-friends/  ← plugin source here
        src/
        package.json
      ```

      When delegating to developer for a plugin:
      ```
      Delegiere an: developer
      Aufgabe: Editiere ../sharkord-vid-with-friends/src/index.ts
               Arbeitsverzeichnis: ../sharkord-vid-with-friends/
      ```
