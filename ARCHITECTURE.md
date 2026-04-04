# agent-meta — Architecture Overview

> Version: **0.12.0** — last updated: 2026-04-04

---

## Diagrams

| # | Diagram | Description |
|---|---------|-------------|
| 1 | [Layer Model](docs/architecture/01-layer-model.md) | Override-Priorität der 4 Schichten (0-external → 3-project) |
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
│   │   └── meta-feedback.md
│   └── 2-platform/          ← Plattform-Overrides
│       ├── sharkord-release.md
│       └── sharkord-docker.md
├── snippets/                ← Versionierte Code-Snippets (per Agent + Sprache)
│   ├── tester/
│   │   ├── bun-typescript.md
│   │   └── pytest-python.md
│   └── developer/
│       ├── bun-typescript.md
│       └── pytest-python.md
├── external/                ← Git Submodule (externe Skill-Repos)
│   └── neat-little-package/ ← gepinnt @ be411f3
├── docs/
│   └── architecture/        ← Architektur-Diagramme (Mermaid)
├── external-skills.config.json  ← Skill-Aktivierung (enabled: true/false)
├── agent-meta.config.example.json
├── scripts/
│   └── sync.py              ← Agent-Generator
└── howto/
    ├── instantiate-project.md
    └── upgrade-guide.md
```

---

## Update Instructions

Bei jedem **Major Release** aktualisieren:
- Version + Datum in der Überschrift
- `Repository Structure` (neue Dateien/Verzeichnisse)
- Diagramme in `docs/architecture/` (neue Rollen, Skills, Schichten)
