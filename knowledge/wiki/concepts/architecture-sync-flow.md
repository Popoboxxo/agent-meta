---
type: "Architecture"
title: "Sync Flow"
description: "sync.py ist reiner Entrypoint (Argparse + Dispatch); die eigentliche Logik liegt in scripts/lib/. Config kommt aus .meta-config/project.yaml + config/*.yaml, nicht mehr aus Root-Config-Dateien."
tags: [architecture, "status:active"]
timestamp: "2026-09-03"
resource: "../../sources/docs/architecture/02-sync-flow.md"
migrated_from: "docs/architecture/02-sync-flow.md"
migration_note: "Re-Ingest 2026-09-03 (Issue #651): vollständig aus aktueller Quelle resynct — alte Config-Dateinamen (agent-meta.config.yaml, external-skills.config.yaml, roles.config.yaml) und 'Neue Features in v0.17.0'-Überschrift waren massiv veraltet (Audit-Fund P1)."
---
# Sync Flow

> [Back to Architecture Overview](../../../ARCHITECTURE.md)

```mermaid
flowchart TD
    CFG[.meta-config/project.yaml]
    RCFG[config/role-defaults.yaml + config/ai-providers.yaml + config/*.yaml]
    SYNC[sync.py]

    subgraph sources [agent-meta]
        G1[1-generic agents]
        G2[2-platform agents]
        SN[snippets]
        EX[external SKILL.md]
        WR[skill-wrapper template]
        RL[rules/1-generic + 2-platform]
        HK[hooks/1-generic + 2-platform]
    end

    subgraph target [target project]
        AG[.claude/agents/ generated]
        SK[.claude/skills/ copied]
        SNC[.claude/snippets/ copied]
        RLO[.claude/rules/ copied]
        HKO[.claude/hooks/ copied]
        EXT[.claude/3-project/ ext created once]
        CLA[CLAUDE.md managed block updated]
        SET[.claude/settings.json hooks merged]
        SETL[.claude/settings.local.json created once]
    end

    CFG --> SYNC
    RCFG --> SYNC
    G1 --> SYNC
    G2 --> SYNC
    SN --> SYNC
    EX --> SYNC
    WR --> SYNC
    RL --> SYNC
    HK --> SYNC

    SYNC -->|WRITE| AG
    SYNC -->|COPY| SNC
    SYNC -->|COPY| SK
    SYNC -->|COPY| RLO
    SYNC -->|COPY| HKO
    SYNC -->|CREATE once| EXT
    SYNC -->|UPDATE managed block| CLA
    SYNC -->|MERGE hooks| SET
    SYNC -->|CREATE once| SETL
```

## Aktueller Sync-Flow

`scripts/sync.py` ist reiner Entrypoint (Argparse + Dispatch), die eigentliche Logik
liegt in `scripts/lib/`. Ablauf (grob):

1. **Config laden:** `.meta-config/project.yaml` (Standardpfad; legacy `agent-meta.config.yaml`/`.json`
   im Projekt-Root werden nur noch als Fallback erkannt) + Framework-Config aus `config/*.yaml`
   (`ai-providers.yaml`, `role-defaults.yaml`, `dod-presets.yaml`, `rules-presets.yaml`,
   `skills-registry.yaml` u.a.) über `lib/config.py::load_config`.
2. **Kontext bauen:** `_build_context()` in `sync.py` erzeugt eine `_SyncContext` (aufgelöste
   Provider, Variablen, Platforms, DoD/Rules-Presets) — gemeinsamer State für alle CLI-Modi.
3. **Dispatch:** `_dispatch(ctx)` routet auf den passenden `_handle_*`-Handler
   (`_handle_sync`, `_handle_validate`, `_handle_create_ext`, …) je nach CLI-Flag.
4. **Provider-Iteration:** `_handle_sync` löst die aktiven Provider aus `ai-providers.yaml`
   + Projekt-Config auf (`resolve_providers`) und rendert für jeden Provider die Agenten.
5. **Template-Rendering:** `lib/agent_sync.py` liest `agents/1-generic/<rolle>.md`, wendet
   `2-platform`-Overrides (`extends`+`patches` oder Full-Replacement) und
   `.claude/3-project/<rolle>-ext.md`-Extensions an, substituiert `{{PLATZHALTER}}` und
   schreibt das Ergebnis nach `.claude/agents/` (bzw. providerspezifisches Zielverzeichnis).
6. **Nebenläufig:** Rules (`rules/1-generic`+`rules/2-platform` → `.claude/rules/`), Hooks
   (`hooks/1-generic`+`hooks/2-platform` → `.claude/hooks/` + Merge in `.claude/settings.json`),
   Snippets, Skills und der `CLAUDE.md`-Managed-Block werden im selben Lauf synchronisiert.

`permissionMode` je Rolle stammt aus `config/role-defaults.yaml` (`permission_mode`-Feld)
plus projektseitigen `permission-mode-overrides` in `.meta-config/project.yaml`, Validation
läuft über `config/project-config.schema.json`.

> **Historie (vor der August-Refactoring-Roadmap):** `sync.py`'s `main()` war eine lange
> `if/elif`-Kette. Diese wurde durch die `_dispatch()`-Tabelle über `_SyncContext`/`_handle_*`-Handler
> ersetzt (10-Wave-Roadmap, #563–#615 et al.) — siehe `singleton-orchestrator-architecture.md`
> für den analogen Umbau bei providerspezifischer Logik.

## CLAUDE.md managed block

Bei jedem normalen sync aktualisiert `sync.py` automatisch den managed block in `CLAUDE.md`
(nur wenn `ai-provider: Claude` in config):

```
<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on every sync. -->

Generiert von agent-meta vX.Y.Z — YYYY-MM-DD

| Agent | Zuständigkeit |
|-------|--------------|
| orchestrator | ... |
| developer    | ... |
...
<!-- agent-meta:managed-end -->
```

- **Außerhalb des Blocks** — handgeschrieben, nie überschrieben
- **Innerhalb des Blocks** — vollständig generiert, manuelle Änderungen gehen verloren
- **Block fehlt** → `[WARN]` im sync.log mit Hinweis zum manuellen Einfügen
