# agent-meta — Architecture Overview

> Version: **0.17.0** — last updated: 2026-04-07

---

## Diagrams

| # | Diagram | Description |
|---|---------|-------------|
| 1 | [Layer Model](docs/architecture/01-layer-model.md) | Override-Priorität der 4 Schichten (0-external → 3-project) + Rules/Hooks |
| 2 | [Sync Flow](docs/architecture/02-sync-flow.md) | Wie `sync.py` aus agent-meta-Sources das Zielprojekt befüllt |
| 3 | [Agent Roles](docs/architecture/03-agent-roles.md) | Alle Agenten-Rollen und Zuständigkeiten |
| 4 | [Development Workflow](docs/architecture/04-dev-workflow.md) | Standard Feature-Workflow als Sequence Diagram |
| 5 | [External Skills](docs/architecture/05-external-skills.md) | Submodule → Config → Wrapper → Zielprojekt |
| 6 | [Versioning Strategy](docs/architecture/06-versioning.md) | Repo-, Agent- und Snippet-Versionen |

---

## Repository Structure

```
agent-meta/
├── agents/
│   ├── 0-external/          ← Wrapper-Template für externe Skills
│   │   └── _skill-wrapper.md
│   ├── 1-generic/           ← Universelle Agent-Templates
│   │   ├── orchestrator.md
│   │   ├── ideation.md
│   │   ├── requirements.md
│   │   ├── developer.md
│   │   ├── tester.md
│   │   ├── validator.md
│   │   ├── documenter.md
│   │   ├── git.md
│   │   ├── release.md
│   │   ├── docker.md
│   │   ├── meta-feedback.md
│   │   ├── feature.md
│   │   ├── agent-meta-manager.md
│   │   ├── agent-meta-scout.md
│   │   └── security-auditor.md
│   └── 2-platform/          ← Plattform-Overrides
│       ├── sharkord-release.md
│       └── sharkord-docker.md
├── hooks/                   ← Versionierte Hook-Scripts (3-Schichten-Modell)
│   ├── 0-external/          ← Hooks aus externen Skill-Repos
│   ├── 1-generic/           ← Universelle Hooks
│   │   └── dod-push-check.sh
│   └── 2-platform/          ← Plattform-spezifische Hooks
├── rules/                   ← Projekt-globale Regeln (auto-loaded in alle Agenten)
│   ├── 0-external/          ← Rules aus externen Skill-Repos
│   ├── 1-generic/           ← Universelle Regeln
│   │   └── issue-lifecycle.md
│   └── 2-platform/          ← Plattform-spezifische Regeln
├── snippets/                ← Versionierte Code-Snippets (per Agent + Sprache)
│   ├── tester/
│   │   ├── bun-typescript.md
│   │   └── pytest-python.md
│   └── developer/
│       ├── bun-typescript.md
│       └── pytest-python.md
├── external/                ← Git Submodule (externe Skill-Repos)
├── docs/
│   └── architecture/        ← Architektur-Diagramme (Mermaid)
├── agent-meta.schema.json   ← JSON Schema für agent-meta.config.yaml (Draft-07)
├── external-skills.config.yaml  ← Skill-Konfiguration (approved: true/false)
├── roles.config.yaml        ← Zentrale Rollen-Konfiguration (model, permissionMode)
├── scripts/
│   └── sync.py              ← Agent-Generator
└── howto/
    ├── first-steps.md
    ├── instantiate-project.md
    ├── upgrade-guide.md
    ├── agent-composition.md
    ├── external-skills.md
    ├── hooks.md             ← NEU: Hooks-Layer Dokumentation
    ├── agent-isolation.md   ← NEU: isolation: worktree für feature-Agent
    ├── rules.md
    ├── agent-memory.md
    ├── sync-concept.md
    └── agent-meta.config.example.json
```

---

## Update Instructions

Bei jedem **Major Release** aktualisieren:
- Version + Datum in der Überschrift
- `Repository Structure` (neue Dateien/Verzeichnisse)
- Diagramme in `docs/architecture/` (neue Rollen, Skills, Schichten)
