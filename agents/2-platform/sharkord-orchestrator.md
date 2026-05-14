---
name: sharkord-orchestrator
version: "1.0.1"
based-on: "1-generic/orchestrator.md@2.9.0"
description: "Sharkord-spezifischer Orchestrator-Agent für EINZELNE Plugin-Repos. Ergänzt den generischen Orchestrator um Plugin-spezifische Routing-Hinweise. Cross-Plugin Standardisierung ist nur aktiv wenn das Projekt als Meta-Repo konfiguriert ist (META_REPO: true)."
hint: "Koordiniert ein einzelnes Sharkord Plugin — Standardisierung nur bei Meta-Repo"
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
      ## Sharkord Plugin Routing Guide

      Standard-Verhalten (Einzelnes Plugin-Repo):
      - Alle Operationen laufen im aktuellen Plugin-Repo.
      - Keine Annahme über Meta-Repo-Struktur oder Sibling-Repos.

      ## Cross-Plugin Standardization (NUR bei Meta-Repo)

      > **Hinweis:** Dieser Abschnitt ist nur relevant wenn `META_REPO: true` in `project.yaml` gesetzt ist.
      > Für normale Plugin-Repos überspringen.

      Wenn dieses Projekt ein Meta-Repo ist (koordiniert mehrere Plugins):

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

      ### Delegation Pattern (nur Meta-Repo)

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
      Aufgabe: Auditiere alle Sharkord Plugins gegen die aktualisierten Standards.
               Berichte Non-Compliance mit Plugin-Name, Datei und konkretem Issue.
      ```

      **feature:**
      ```
      Delegiere an: feature
      Aufgabe: Erstelle für jedes betroffene Plugin einen Standardisierungs-Branch
               und wende die neuen Konventionen an. Erstelle PRs für jedes Plugin.
      ```
