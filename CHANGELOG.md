# Changelog

## [0.12.0] — 2026-04-04

### Added

- **`1-generic/git.md`** (`1.0.0`) — neuer Git-Agent: Commits, Branches, Merges, Tags, Push/Pull, Commit-Messages, plattformunabhängig (GitHub, GitLab, Gitea)
- Neue Variablen: `{{GIT_PLATFORM}}`, `{{GIT_REMOTE_URL}}`, `{{GIT_MAIN_BRANCH}}`
- `sync.py` ROLE_MAP + CLAUDE.md: `git`-Rolle registriert

### Changed

- `orchestrator.md` (`1.5.0`) — `git`-Agent in Agenten-Tabelle; Git-Commits in Workflows A/B/E/H1/H2 an `git` delegiert; Commit-Konventionen-Sektion entfernt (→ `git.md`); DoD-Punkt aktualisiert
- `release.md` (`1.3.0`) — Release-Workflow Schritt 5→6 umgestellt: `git tag` → Delegation an `git`; Checkliste + Delegation aktualisiert
- `sharkord-release.md` (`1.3.0`) — Schritt 6 (Commit + Tag + Push) als Delegation an `git`-Agenten formuliert; Checkliste aktualisiert

---

## [0.11.0] — 2026-04-04

### Added

- **`0-external` Layer** — neuer Agenten-Layer für externe Skill-Pakete aus Drittrepos
- `agents/0-external/_skill-wrapper.md` — generisches Wrapper-Template: Header + `{{SKILL_CONTENT}}` Substitution + lazy `additional_files`
- `external-skills.config.json` — zentrale Skill-Konfiguration (Modell A): Submodule-URLs + Skill-Mapping + `enabled: true/false` Aktivierung
- `sync.py` — `sync_external_skills()`: generiert `.claude/agents/<role>.md` + kopiert Skill-Dateien nach `.claude/skills/<skill-name>/`
- `sync.py` — `--add-skill <repo-url> --skill-name --source --role [--entry]`: registriert Git Submodule + legt Config-Eintrag an
- CLAUDE.md — vollständiger "External Skills (0-external Layer)"-Abschnitt mit Konzept, Konfigurationsformat, Workflow, Versionierung

### Changed

- CLAUDE.md — "Drei-Schichten-Modell" → "Schichten-Modell" (0-external ergänzt, Override-Reihenfolge aktualisiert)
- CLAUDE.md — Verzeichnisstruktur: `0-external/`, `external/`, `external-skills.config.json` dokumentiert
- CLAUDE.md — Abhängigkeits-Karte + Änderungs-Kategorien um External Skills ergänzt

---

## [0.10.7] — 2026-04-03

### Added

- `snippets/developer/bun-typescript.md` (`1.0.0`) — Imports/Exports, Typisierung, Fehlerbehandlung, Dateistruktur, Async für TypeScript/Bun
- `snippets/developer/pytest-python.md` (`1.0.0`) — Python-Äquivalente
- **`{{DEVELOPER_SNIPPETS_PATH}}`** — neue Variable, zeigt auf Developer-Snippet-Datei

### Changed

- `developer.md` (`1.4.0`) — `DEVELOPER_SNIPPETS_PATH` Read-Instruktion in Sprach-Best-Practices eingebaut
- CLAUDE.md — `DEVELOPER_SNIPPETS_PATH` in Variablen-Tabelle + Snippets-Tabelle + Verzeichnisstruktur
- `agent-meta.config.example.json` — `DEVELOPER_SNIPPETS_PATH` hinzugefügt

---

## [0.10.6] — 2026-04-03

### Added

- **Snippet-System** — sprachspezifische Code-Beispiele ausgelagert in `snippets/<rolle>/`
- `snippets/tester/bun-typescript.md` (`1.0.0`) — TypeScript/Bun Test-Syntax, Naming, Assertions
- `snippets/tester/pytest-python.md` (`1.0.0`) — Python/pytest Äquivalente
- **`{{TESTER_SNIPPETS_PATH}}`** — neue Variable, zeigt auf Snippet-Datei (relativ zu `snippets/`)
- `sync.py` — `sync_snippets()`: kopiert Snippet-Dateien nach `.claude/snippets/` im Zielprojekt (respektiert `--dry-run`, loggt Version)
- CLAUDE.md — neuer Abschnitt "Snippets" mit Konzept, Frontmatter, verfügbaren Snippets, Anleitung

### Changed

- `tester.md` (`1.4.0`) — TypeScript-Codeblöcke durch sprach-agnostisches Pseudocode ersetzt; `{{TESTER_SNIPPETS_PATH}}` Read-Instruktion an 3 Stellen eingebaut
- `orchestrator.md` (`1.4.0`) — `py .agent-meta/scripts/sync.py` → `python .agent-meta/scripts/sync.py` (plattformübergreifend)

---

## [0.10.5] — 2026-04-03

### Added

- **`{{CODE_LANGUAGE}}`** — neue Variable für code-nahe Artefakte: Code-Kommentare, Commit-Messages, Test-Beschreibungen, docker-compose-Kommentare (Default: `Englisch`)
- **`{{INTERNAL_DOCS_LANGUAGE}}`** — neue Variable für interne Doku: CODEBASE_OVERVIEW, ARCHITECTURE, REQUIREMENTS, conclusions (Default: `Deutsch`)

### Changed

- `COMMUNICATION_LANGUAGE` Default-Wert: `Deutsch` → `Englisch`
- `developer.md` (`1.3.0`) — Code-Kommentare + Commit-Messages → `{{CODE_LANGUAGE}}`
- `docker.md` (`1.3.0`) — docker-compose Kommentare → `{{CODE_LANGUAGE}}`
- `documenter.md` (`1.3.0`) — Datei-Tabelle + README-WICHTIG → `{{DOCS_LANGUAGE}}`/`{{INTERNAL_DOCS_LANGUAGE}}`; Sprach-Sektion aufgetrennt
- `meta-feedback.md` (`1.3.0`) — GitHub Issues → `{{DOCS_LANGUAGE}}`
- `tester.md` (`1.3.0`) — Test-Beschreibungen → `{{CODE_LANGUAGE}}`
- `requirements.md` (`1.3.0`) — REQUIREMENTS.md → `{{INTERNAL_DOCS_LANGUAGE}}`
- `validator.md` (`1.3.0`) — Berichte → `{{INTERNAL_DOCS_LANGUAGE}}`
- `sharkord-docker.md` (`1.2.0`) — Kommentare → `{{CODE_LANGUAGE}}`, Kommunikation → `{{COMMUNICATION_LANGUAGE}}`
- `sharkord-release.md` (`1.2.0`) — Release Notes → `{{DOCS_LANGUAGE}}`, Kommunikation → `{{COMMUNICATION_LANGUAGE}}`
- CLAUDE.md — Variablen-Tabelle um `CODE_LANGUAGE` + `INTERNAL_DOCS_LANGUAGE` erweitert

---

## [0.10.4] — 2026-04-03

### Changed

- Alle Agenten — `## Projektspezifische Erweiterung`-Block von 8 auf 1 Zeile komprimiert (kein Inhaltsverlust, ~84 Zeilen gespart)
- `tester.md` (`1.2.0`) — Don'ts-Sektion: Duplikate aus "Qualitätsprinzipien"-Abschnitt entfernt, durch Querverweis ersetzt
- `developer.md` (`1.2.0`) — "Sprach-Best-Practices": erklärender Absatz entfernt, Regel auf eine Zeile
- `orchestrator.md` (`1.3.0`) — Extension-Block komprimiert
- Alle anderen 1-generic Agenten (`1.2.0`) — Extension-Block komprimiert
- 2-platform Agenten (`1.1.0`) — Extension-Block komprimiert

---

## [0.10.3] — 2026-04-03

### Added

- **`{{COMMUNICATION_LANGUAGE}}`** — neue Variable in allen Agenten; steuert Sprache der Nutzer-Kommunikation
- **`{{DOCS_LANGUAGE}}`** — neue Variable in allen Agenten; steuert Sprache von Dokumentationsdateien
- **`{{PROJECT_GOAL}}`** — neue Variable im Projektkontext-Block aller Agenten (primäres Ziel)
- **`{{PROJECT_LANGUAGES}}`** — neue Variable im Projektkontext-Block aller Agenten
- **`{{AGENT_META_REPO}}`** — neue Variable in `meta-feedback.md`; ersetzt hardcodierten `Popoboxxo/agent-meta`
- `config.example.json` — alle neuen Variablen mit Defaults ergänzt

### Changed

- `tester.md` (`1.1.0`) — neuer Abschnitt "Qualitätsprinzipien: Keine Shortcuts": echte Assertions, realitätsnahe Testdaten (keine `"foo"`/`"test"`/`123`-Dummy-Daten), Warnung vor Tests die immer grün sind
- `developer.md` (`1.1.0`) — neuer Unterabschnitt "Sprach-Best-Practices": strikt Best Practices der verwendeten Sprache(n) befolgen
- `meta-feedback.md` (`1.1.0`) — `--repo Popoboxxo/agent-meta` durch `--repo {{AGENT_META_REPO}}` ersetzt
- `orchestrator.md` (`1.2.0`) — Sprachvariablen + Projektkontext erweitert
- Alle anderen 1-generic Agenten (`1.1.0`) — Sprachvariablen + Projektkontext erweitert
- CLAUDE.md — Variablen-Tabelle um neue Variablen ergänzt

---

## [0.10.2] — 2026-04-03

### Fixed

- `orchestrator.md` — version von `1.0.0` auf `1.1.0` hochgezogen (war bei 0.10.1 vergessen worden)

### Changed

- Release-Prozess in CLAUDE.md — Schritt 1 "Agenten-Versionen prüfen" explizit ergänzt; Regel: bei Unsicherheit Nutzer fragen

---

## [0.10.1] — 2026-04-03

### Added

- **Neuer Agent `ideation`** (`1-generic/ideation.md`) — Begleitet die frühe, unscharfe Phase bei neuen Projekten und Features: Ideen erkunden, Fragen stellen, Scope schärfen, externe Impulse geben, strukturierte Übergabe an den Requirements-Agenten
- **Workflow I** im Orchestrator — "Neue Idee / Vision erkunden" mit Ideation → Requirements-Kette
- **Workflow H** in CLAUDE.md — dokumentiert den neuen Ideation-Workflow

### Changed

- `orchestrator.md` — `ideation` in Agenten-Tabelle + Workflow I; bisheriger Workflow I (meta-feedback) → Workflow K
- CLAUDE.md — `ideation` in Agenten-Rollen-Tabellen, Namenstabelle und Abhängigkeits-Karte
- `sync.py` ROLE_MAP — `ideation` ergänzt

---

## [0.10.0] — 2026-04-03

### Added

- **Agent-Versionierung** — Jede Template-Datei trägt jetzt `version:` im Frontmatter
- `based-on:` in 2-platform Agenten — dokumentiert die Generic-Basis mit Version (z.B. `1-generic/docker.md@1.0.0`)
- `generated-from:` — wird von `sync.py` automatisch bei jedem Sync in generierte Agenten geschrieben
- `extract_frontmatter_field()` in `sync.py` — liest beliebige YAML-Felder aus Templates
- [howto/agent-versioning.md](howto/agent-versioning.md) — vollständige Dokumentation des Versioning-Konzepts

### Changed

- `build_frontmatter()` in `sync.py` — schreibt `generated-from:` ins generierte Frontmatter; `version` und `based-on` bleiben unverändert erhalten
- `sync_agents()` in `sync.py` — liest `version` aus Quell-Template und befüllt `generated-from` automatisch
- CLAUDE.md — neuer Abschnitt "Agent-Versionierung", Abhängigkeits-Tabelle um Versionshinweise erweitert
- Alle 1-generic Agenten starten mit `version: "1.0.0"`
- Alle 2-platform Agenten starten mit `version: "1.0.0"` und `based-on:`

### Fixed

- `update_extensions()` in `sync.py` — pre-existierender `updated += 1` Bug (nicht initialisierte Variable) entfernt

---

## [0.9.5] — 2026-04-03

### Breaking Changes

- **Variable renames** in `agent-meta.config.example.json`:
  - `SHARKORD_VERSION` → `PRIMARY_IMAGE_TAG`
  - `SHARKORD_URL` → part of `SYSTEM_URLS` (Markdown-Liste)
  - `SHARKORD_MIN_VERSION`, `SHARKORD_IMAGE` → removed (redundant)
  - `WEB_PORT` → `PRIMARY_PORT`
  - `MEDIASOUP_PORT` → part of `EXTRA_PORTS` (Markdown-Liste)
  - `KEY_DEPENDENCIES`, `TARGET_PLATFORM`, `PLATFORM_LAYER` → removed (redundant)
- **`sharkord-docker.md`** updated to use new variable names

### Added

- `SYSTEM_DEPENDENCIES` — Markdown-Liste aller Kern-Abhängigkeiten mit Versionen
- `SYSTEM_URLS` — Markdown-Liste aller relevanten System-URLs
- `EXTRA_PORTS` — Markdown-Liste weiterer Ports neben `PRIMARY_PORT`
- `config.example.json` in vier klare Sektionen gegliedert:
  - **Generisch** — für jedes Projekt
  - **Infrastruktur** — Docker, Ports, Container
  - **Plattform** — nur bei `platforms: ["sharkord"]`
  - **Projektspezifisch** — individuelle Werte pro Projekt
- `CLAUDE.md` — Variablen-Tabelle nach denselben vier Sektionen strukturiert

### Changed

- `sharkord-docker.md` — Platzhalter-Dokumentation aktualisiert, Port-Vorlage generalisiert

---

## [0.9.4] — 2026-04-03

### Added

- New agent role `meta-feedback` (`agents/1-generic/meta-feedback.md`):
  collects improvement suggestions for the agent-meta framework and creates
  GitHub Issues in the agent-meta repository
- Orchestrator Workflow I: "Feedback an agent-meta geben" — delegates to
  `meta-feedback`; orchestrator actively asks for feedback at session end
- `meta-feedback` added to `ROLE_MAP` in `sync.py`

### Changed

- `CLAUDE.md` — agent roles table and dependency map updated with `meta-feedback`
- `README.md` — agent roles table and supported platforms updated

---

## [0.9.3] — 2026-04-03

### Added

- Release process documented in `CLAUDE.md`: Semantic Versioning rules,
  step-by-step workflow, rule that README must reflect the new version
  before the tag commit

### Changed

- README version badge and Quick Start example now always reflect current
  version before tagging

---

## [0.9.1] — 2026-04-03

### Added

- README with VibeCoding experiment warning, architecture overview, quick start,
  extension system docs, upgrade instructions, and agent role reference

### Changed

- Orchestrator Workflow H2 now documents automatic platform layer selection:
  sync.py reads `"platforms": [...]` from config and picks the correct
  `2-platform/` agent automatically — no manual step required

---

## [0.9.0] — 2026-04-03

### Breaking Changes

- **Generic agent names** — agents in `.claude/agents/` no longer use a project
  prefix. Files are now named `developer.md`, `tester.md` etc. instead of
  `vwf-developer.md`. One project per workspace is the assumed model.
- **`project.prefix` is now used for extensions only**, not for agent filenames.

### Added

**Extension system** (`.claude/3-project/<prefix>-<role>-ext.md`)
- New `--create-ext <role|all>` — creates extension file with managed block +
  empty project section; never overwrites an existing file
- New `--update-ext` — updates the managed block in all existing extension files;
  project section is never touched
- Managed block (`<!-- agent-meta:managed-begin/end -->`) contains auto-generated
  context from config variables — updated on every `--update-ext`
- Meta-repo provides no extension templates — extensions are fully project-owned

**Extension-Hook in all agents**
- Every generated agent (1-generic + 2-platform) reads `.claude/3-project/<prefix>-<role>-ext.md`
  at startup if it exists — additively, without overriding the agent

**`howto/upgrade-guide.md`** — new: full upgrade workflow, `--update-ext` for
extensions, rollback, breaking-change handling, checklist

### Changed

- `config.example.json` — restored `prefix` field, removed `EXTRA_*_KNOWLEDGE`
  variables (replaced by extension system), added all missing variables
- `instantiate-project.md` — rewritten for sync.py workflow (submodule + script)
- `CLAUDE.md` — rewritten with 4 core principles, extension system docs,
  update-behavior table, decision tree

### Removed

- `EXTRA_ORCHESTRATOR/TESTER/DOCUMENTER/REQ_KNOWLEDGE` placeholders from
  1-generic agents (replaced by extension system)
- Copy-once logic for extension files

---

## [0.1.0] — 2026-04-01

Initial release of agent-meta.

### Added

**Three-layer agent architecture**
- `agents/1-generic/` — platform-independent agent roles: orchestrator, developer,
  tester, validator, requirements, documenter, release, docker
- `agents/2-platform/` — Sharkord-specific agents: sharkord-docker, sharkord-release,
  consolidating all knowledge from sharkord-vid-with-friends and sharkord-hero-introducer
- `agents/3-project/` — reserved for project-level overrides (rare)

**CLAUDE.md as single source of truth**
- Project context lives exclusively in the project's `CLAUDE.md`
- Agents read `CLAUDE.md` instead of carrying embedded context blocks
- Override hierarchy: generic ← platform ← project

**sync.py — project integration script**
- Generates `.claude/agents/*.md` from agent-meta sources
- Modes: `--init`, `--only-variables`, `--dry-run`
- Three-layer override logic with multi-platform support
- Auto-sets frontmatter (`name`, `description`) per project
- Writes `sync.log` with full summary and warnings for missing variables

**Supporting files**
- `agent-meta.config.example.json` — config template covering all known variables
- `howto/instantiate-project.md` — step-by-step setup guide
- `howto/CLAUDE.project-template.md` — project CLAUDE.md template
- `howto/sync-concept.md` — full sync concept and architecture decisions
- `howto/template-gap-analysis.md` — gap analysis vs. existing projects

### Supported platforms
- Sharkord Plugin SDK (`sharkord-docker.md`, `sharkord-release.md`)

### Known limitations
- `sync.py` requires Python 3.8+
- No automated tests for the sync script yet
- Project-level overrides (`3-project/`) are reserved but not yet exercised
