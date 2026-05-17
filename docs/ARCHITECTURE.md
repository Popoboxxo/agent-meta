# ARCHITECTURE — agent-meta

> **Stand:** 2026-05-17 | **Version:** 0.41.0

## Überblick

agent-meta ist ein Git-Repository das als Submodul in Projekte eingebunden wird. Es stellt standardisierte Multi-Provider-Agenten-Templates bereit und generiert via `sync.py` projektfertige Agenten-Dateien in `.claude/agents/`, `.gemini/agents/`, `.opencode/agents/` und `.continue/agents/`.

```
┌─────────────────────────────────────────────────────────┐
│                    project.yaml                         │
│              (.meta-config/project.yaml)                │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                      sync.py                            │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐ │
│  │ config.py│  │ agents.py│  │ rules/hooks/commands  │ │
│  │ roles.py │  │ setup.py │  │ skills/mcp/isolation  │ │
│  │ dod.py   │  │ io.py    │  │ context/extensions    │ │
│  │ platform │  │ log.py   │  │ viz/secrets/providers │ │
│  └──────────┘  └──────────┘  └───────────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │
    ┌──────────────────┼──────────────────┐
    ▼                  ▼                  ▼
.claude/agents/   .gemini/agents/   .opencode/agents/
.claude/rules/    .gemini/rules/    .opencode/commands/
.claude/hooks/    .gemini/agents/   AGENTS.md (embedded)
.claude/commands/ .gemini/commands/ .gemini/agents/
.claude/skills/   ...               ...
```

## Drei-Schichten-Architektur

```
0-external/   Externe Skill-Agenten (Git Submodule, approved/pinned)
1-generic/    Universelle Templates — gelten für jedes Projekt
2-platform/   Plattformspezifische Overrides (z.B. sharkord-*.md)
3-project/    Projektspezifische Overrides/Extensions
```

**Override-Reihenfolge:** `1-generic → 2-platform → 3-project/<role>.md`

## Sync-Modi

| Modus | Flag | Beschreibung |
|-------|------|-------------|
| **Sync** | (default) | Inkrementeller Sync — nur geänderte Dateien werden geschrieben |
| **Update** | `--update` | Expliziter Alias für Default-Sync, loggt Mode als `update` |
| **Init** | `--init` | Sync + Initialisierung von CLAUDE.md, Settings, Secrets-Template |
| **Clean** | `--clean` | Löscht alle generierten Dateien, dann voller Sync from scratch |
| **Clean+Init** | `--clean --init` | Clean + Init mit Meta-Repo-Docs-Scaffolding |

### Clean-Mode Architektur

```
clean_generated_files()
    │
    ├── Phase 1: Provider-Verzeichnisse scannen
    │   ├── agents_dir  (explizit in Provider-Config)
    │   ├── rules_dir   (explizit ODER inferiert aus has_rules + .{provider}/rules)
    │   ├── hooks_dir   (explizit ODER inferiert aus has_hooks + .{provider}/hooks)
    │   ├── commands_dir (explizit ODER inferiert aus has_commands + .{provider}/commands)
    │   ├── skills_dir  (explizit ODER inferiert aus has_skills)
    │   └── snippets_dir (explizit ODER inferiert aus has_snippets)
    │
    ├── Phase 2: Top-level generierte Dateien
    │   └── sync.log
    │
    └── Phase 3: Löschen
        ├── Dateien zuerst (unlink)
        └── Verzeichnisse danach (shutil.rmtree)
```

**Geschützte Pfade:**
- Settings-Dateien (committed)
- Local-Settings (`*.local.*`)
- Extension-Dateien (`*-ext.md`)
- `.meta-config/` (gesamtes Verzeichnis)
- CLAUDE.md / AGENTS.md (semi-managed)
- MCP-Secrets-Dateien
- Pending-Tasks-Dateien

## Multi-Provider-Sync

Jeder Provider durchläuft denselben Sync-Pipeline-Code mit provider-spezifischen Transformationen:

| Provider | Frontmatter | Besonderheiten |
|----------|------------|----------------|
| **Claude** | Vollständig (model, memory, permissionMode, temperature, maxTokens) | CLAUDE.md Management, settings.json, Hooks |
| **Gemini** | Model only (memory/permissionMode entfernt) | Provider-mapped Model-ID |
| **Opencode** | `description` + `mode: subagent` + `model` | Native Opencode-Frontmatter-Transformation |
| **Continue** | Minimal (name, description, alwaysApply: false) | Slash-Command-Prompts optional |

## Neue Komponenten (v0.41.0)

### 1. Clean-Mode (`clean_generated_files` in `io.py`)

Provider-agnostische Verzeichnis-Scan-Logik die implizit aufgelöste Verzeichnisse erkennt. Das Problem: Claude hat keine expliziten `rules_dir`/`hooks_dir`/`commands_dir` Keys — diese werden aus `has_rules`/`has_hooks`/`has_commands` Flags + Provider-Namen abgeleitet. Die `_resolve_dir()` Hilfsfunktion kapselt diese Logik.

### 2. Meta-Repo-Docs-Scaffolding (`scaffold_meta_repo_docs` in `setup.py`)

Auto-generiert `docs/PATTERNS.md`, `docs/LEARNINGS.md`, `docs/CONVENTIONS.md` beim Sync wenn `meta-repo: true`. Nutzt Starter-Templates aus `.agent-meta/templates/docs/` falls vorhanden, sonst Standard-Header.

### 3. CI/CD Status Polling (git-Agent)

Opt-in Feature (`CI_POLL_ENABLED: true`) das nach `git push` automatisch den CI-Pipeline-Status pollt und zurückmeldet. Verwendet `gh run list` für GitHub Actions. Konfigurierbar über `CI_POLL_INTERVAL` und `CI_POLL_MAX_RETRIES`.

### 4. Inverse Conditional Blocks (`{{^VAR}}`)

Erweiterung von `strip_inactive_dod_blocks()` um inverse Blöcke: `{{^VAR}}...{{/if}}` wird entfernt wenn VAR `true` ist, angezeigt wenn VAR `false` ist. Ermöglicht z.B. `{{^CI_POLL_ENABLED}}CI polling is disabled...{{/if}}`.

## AGENTS.md Regel-Erweiterungen

### Invariante #4: Provider-Pflicht
Jede Änderung MUSS für ALLE aktiven Provider (Claude, Continue, Gemini, Opencode) funktionieren.
Prüfung vor Commit: `python scripts/sync.py --dry-run`.

### Orchestrator-Pflicht
Einstiegspunkt für ALLE Aufgaben. Hauptchat nur für triviale Direktantworten.

### Submodule Boundary Rule
Agenten dürfen NIE Dateien in Git-Submodules (`.agent-meta/`, `external/`) erstellen, verändern oder löschen.

### Multi-Repo Workspace Convention
Beim Arbeiten in Sibling-Repos MÜSSEN Agenten KEINE `.claude/` o.ä. Verzeichnisse anlegen.

## Diagramme

Vertiefte Architektur-Diagramme:
- [Schichten-Architektur](architecture/01-layer-model.md)
- [Sync-Flow](architecture/02-sync-flow.md)
- [Agent-Rollen](architecture/03-agent-roles.md)
- [Provider-Matrix](architecture/08-provider-matrix.md)
