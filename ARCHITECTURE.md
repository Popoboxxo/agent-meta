# agent-meta — Architecture Overview

> Version: **0.12.0** — last updated: 2026-04-04

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
├── external-skills.config.json  ← Skill-Aktivierung (enabled: true/false)
├── agent-meta.config.example.json
├── scripts/
│   └── sync.py              ← Agent-Generator
└── howto/
    ├── instantiate-project.md
    └── upgrade-guide.md
```

---

## Layer Model — Override Priority

```mermaid
graph LR
    A["1-generic/<br/>universell"] -->|überschrieben durch| B["2-platform/<br/>plattformspezifisch"]
    B -->|überschrieben durch| C["3-project/<br/>rolle.md Override<br/>(im Zielprojekt)"]
    D["0-external/<br/>Skill-Wrapper<br/>eigenständige Rollen"] -.->|zusätzlich zu| E[".claude/agents/<br/>im Zielprojekt"]
    A --> E
    B --> E
    C --> E

    style A fill:#4a7c59,color:#fff
    style B fill:#2d6a9f,color:#fff
    style C fill:#8b4513,color:#fff
    style D fill:#6b3fa0,color:#fff
    style E fill:#333,color:#fff
```

---

## Sync Flow — agent-meta → Zielprojekt

```mermaid
flowchart TD
    CFG["agent-meta.config.json<br/>(Projekt-Config)"]
    ECFG["external-skills.config.json<br/>(Skill-Config, Modell A)"]
    SYNC["sync.py"]

    subgraph SOURCES ["agent-meta Sources"]
        G1["1-generic/*.md"]
        G2["2-platform/*.md"]
        SN["snippets/**/*.md"]
        EX["external/<repo>/SKILL.md"]
        WR["0-external/_skill-wrapper.md"]
    end

    subgraph TARGET [".claude/ im Zielprojekt"]
        AG[".claude/agents/*.md<br/>(generiert — nie manuell bearbeiten)"]
        SK[".claude/skills/<skill>/<br/>(kopiert)"]
        SNC[".claude/snippets/<role>/<br/>(kopiert)"]
        EXT[".claude/3-project/*-ext.md<br/>(Extension — manuell pflegbar)"]
    end

    CFG --> SYNC
    ECFG --> SYNC
    G1 --> SYNC
    G2 --> SYNC
    SN --> SYNC
    EX --> SYNC
    WR --> SYNC

    SYNC -->|"WRITE (substituiert)"| AG
    SYNC -->|"COPY"| SNC
    SYNC -->|"COPY (enabled skills)"| SK
    SYNC -->|"CREATE (einmalig)"| EXT

    style SOURCES fill:#1a1a2e,color:#eee,stroke:#444
    style TARGET fill:#16213e,color:#eee,stroke:#444
    style SYNC fill:#0f3460,color:#fff,stroke:#e94560
```

---

## Agent Roles & Responsibilities

```mermaid
graph TD
    ORC["🎯 orchestrator<br/>Koordination & Workflows"]

    ORC --> IDE["💡 ideation<br/>Vision & Scope"]
    ORC --> REQ["📋 requirements<br/>REQ-IDs & REQUIREMENTS.md"]
    ORC --> DEV["👨‍💻 developer<br/>Implementierung"]
    ORC --> TST["🧪 tester<br/>TDD & Test-Suite"]
    ORC --> VAL["✅ validator<br/>DoD & Traceability"]
    ORC --> DOC["📚 documenter<br/>CODEBASE_OVERVIEW & Erkenntnisse"]
    ORC --> GIT["🔀 git<br/>Commits, Branches, Tags, Push/Pull"]
    ORC --> REL["🚀 release<br/>Versioning & GitHub Release"]
    ORC --> DOK["🐳 docker<br/>Dev-Stack & Binaries"]
    ORC --> MFB["🔧 meta-feedback<br/>GitHub Issues an agent-meta"]

    EXT["🌐 0-external Skills<br/>(z.B. opengrid-designer,<br/>home-organization-specialist)"]

    style ORC fill:#e94560,color:#fff
    style GIT fill:#f39c12,color:#fff
    style EXT fill:#6b3fa0,color:#fff
```

---

## Development Workflow (Standard)

```mermaid
sequenceDiagram
    actor User
    participant ORC as orchestrator
    participant REQ as requirements
    participant TST as tester
    participant DEV as developer
    participant VAL as validator
    participant DOC as documenter
    participant GIT as git

    User->>ORC: Neues Feature
    ORC->>REQ: REQ-ID vergeben
    REQ-->>ORC: REQ-042 ✓
    ORC->>TST: Tests schreiben (TDD Red)
    TST-->>ORC: Tests geschrieben ✓
    ORC->>DEV: Implementieren
    DEV-->>ORC: Code fertig ✓
    ORC->>TST: Tests ausführen
    TST-->>ORC: Tests grün ✓
    ORC->>VAL: DoD-Check
    VAL-->>ORC: DoD erfüllt ✓
    ORC->>DOC: Doku aktualisieren
    DOC-->>ORC: Doku aktuell ✓
    ORC->>GIT: Commit + Push
    GIT-->>ORC: feat(REQ-042): ... ✓
    ORC-->>User: Feature abgeschlossen ✓
```

---

## External Skills Integration

```mermaid
flowchart LR
    subgraph REPOS ["Externe Repos (Git Submodule)"]
        NLP["neat-little-package<br/>@ be411f3"]
    end

    subgraph SKILLS ["external-skills.config.json"]
        S1["home-organization<br/>enabled: false"]
        S2["opengrid-openscad<br/>enabled: false"]
    end

    subgraph WRAPPER ["agent-meta"]
        WR["0-external/_skill-wrapper.md"]
    end

    subgraph TARGET ["Zielprojekt (.claude/)"]
        AG["agents/opengrid-designer.md"]
        SK["skills/opengrid-openscad/<br/>SKILL.md<br/>enhancements.md"]
    end

    NLP --> S2
    S2 -->|"enabled: true → sync"| WR
    WR -->|"SKILL_CONTENT substituiert"| AG
    S2 -->|"COPY"| SK

    style REPOS fill:#1a1a2e,color:#eee
    style SKILLS fill:#16213e,color:#eee
    style WRAPPER fill:#0f3460,color:#fff
    style TARGET fill:#1a3a1a,color:#eee
```

---

## Versioning Strategy

```mermaid
graph LR
    RV["Repo Version<br/>(VERSION file)<br/>SemVer: 0.12.0"]
    AV["Agent Version<br/>(Frontmatter)<br/>per Datei unabhängig"]
    SV["Snippet Version<br/>(Frontmatter)<br/>per Datei unabhängig"]

    RV -->|"Major: Breaking Changes<br/>Minor: Neue Features<br/>Patch: Fixes/Docs"| RV
    AV -->|"Major: Verhalten/Struktur<br/>Minor: Neue Sektion<br/>Patch: Text/Klarstellung"| AV
    SV -->|"bei inhaltlichen Änderungen<br/>erhöhen"| SV

    PL["2-platform Agent<br/>based-on: 1-generic@x.y.z"]
    AV --> PL
```

---

## Update Instructions

Diese Datei wird bei jedem **Major Release** aktualisiert.
Bei Minor/Patch-Releases nur wenn sich die Architektur ändert.

Zu aktualisierende Bereiche:
- Version in der Überschrift
- `Repository Structure` (neue Dateien/Verzeichnisse)
- `Agent Roles` (neue Rollen)
- `External Skills Integration` (neue Skills/Submodule)
- `Versioning Strategy` (neue Versionsnummern)
