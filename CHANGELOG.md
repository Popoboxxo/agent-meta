# Changelog

## [0.16.3] — 2026-04-06

### Changed

- **`roles.config.json`** (neu): Modell-Defaults aus `sync.py` ausgelagert —
  Meta-Maintainer pflegt Rollen + empfohlene Modelle + Beschreibungen zentral in dieser Datei.
  `sync.py` liest Defaults von dort statt aus einer hardkodierten Konstante.
- **`sync.py`**: `DEFAULT_MODEL_MAP`-Konstante entfernt → `load_roles_config()` liest
  `roles.config.json`; `resolve_model()` nimmt `agent_meta_root` als Parameter.
- **`CLAUDE.md`**: `model-overrides`-Abschnitt zeigt auf `roles.config.json` statt sync.py;
  Verzeichnisbaum um `roles.config.json` ergänzt.

### Migration von v0.16.2

Keine Breaking Changes — Verhalten identisch. Modell-Anpassungen jetzt in
`roles.config.json` statt in `sync.py`.

---

## [0.16.2] — 2026-04-06

### Added

- **Zentrales Modell-Mapping** (`DEFAULT_MODEL_MAP` in `sync.py`): Meta-Maintainer pflegt
  empfohlene Claude-Modelle pro Rolle. `sync.py` injiziert `model:`-Feld beim Generieren.
- **`model-overrides`** in `agent-meta.config.json`: Projekte können einzelne Rollen überschreiben.
  Precedence: Projekt-Override > Meta-Default > kein Feld (erbt vom Parent).
- **`resolve_model()`** + **`inject_model_field()`** in `sync.py`: neue Hilfsfunktionen.
  `inject_model_field()` fügt `model:` nach `name:` ein, überschreibt bestehende Werte,
  oder entfernt das Feld wenn kein Modell konfiguriert (sauberer Output).
- **`[INFO]`-Log** in `sync.log` bei Model-Injection: zeigt gesetztes Modell + Quelle
  (`meta default` vs. `project override`).
- **`agents/1-generic/security-auditor.md`** (v1.0.0-beta): neuer generischer Agent für
  statische Sicherheitsanalyse — OWASP Top 10, Secrets, Dependencies, Supply Chain, Crypto.
  Read-only (kein Write/Edit), kein Alarm-Fanatismus, klare Abgrenzung zu `validator`/`tester`.

### Changed

- `scripts/sync.py`: `DEFAULT_MODEL_MAP` Konstante + `resolve_model()` + `inject_model_field()`
- `scripts/sync.py`: `sync_agents()` ruft Model-Injection nach `build_frontmatter()` auf
- `CLAUDE.md`: neuer Abschnitt `model-overrides` mit vollständiger Defaults-Tabelle
- `CLAUDE.md`: `roles`-Whitelist um `agent-meta-scout` und `security-auditor` ergänzt

### Meta-Defaults (injiziert wenn kein Projekt-Override)

| Modell | Rollen |
|--------|--------|
| `haiku` | `git`, `meta-feedback`, `docker` |
| `sonnet` | `tester`, `validator`, `documenter`, `security-auditor`, `agent-meta-scout`, `agent-meta-manager`, `release` |
| *(leer)* | `orchestrator`, `developer`, `requirements`, `ideation`, `feature` |

---

## [0.16.1] — 2026-04-06

### Added

- **`agents/1-generic/agent-meta-scout.md`** (v1.0.0): neuer generischer Agent — scoutet das
  Claude Code Ökosystem auf neue Skills, Agenten-Rollen, Rules und Workflow-Patterns.
  Liest `evaluate-repository.md` aus dem `awesome-claude-code` Submodule als Evaluation-Framework.
  Wird **ausschließlich auf explizite Nutzer-Anfrage** gestartet (kein Auto-Trigger).
- **`external/awesome-claude-code`**: neues Git Submodule (Meta-Repo mit kuratierten Claude-Skills).
  Gepinnt auf `3d8bde25`. Kein Skill-Wrapper — wird direkt vom `agent-meta-scout` per Read-Tool genutzt.
- **`external-skills.config.json`**: neuer `repos`-Eintrag für `awesome-claude-code`.
- **Orchestrator Workflow M**: "Claude-Ökosystem scouten" — explizite Trigger-Liste,
  `agent-meta-scout` in Agenten-Tabelle eingetragen.

### Changed

- `scripts/sync.py`: `ROLE_MAP` um `agent-meta-scout` erweitert
- `agents/1-generic/orchestrator.md` (v1.6.1 → v1.7.0): Agenten-Tabelle + Workflow M ergänzt
- `CLAUDE.md`: Agenten-Tabelle + Abhängigkeitskarte um `agent-meta-scout` erweitert

---

## [0.16.0] — 2026-04-06

### Added

- **Agent Composition System** (`extends:` + `patches:` in frontmatter): 2-platform and 3-project
  override agents can now compose from a base template instead of maintaining full copies.
  sync.py resolves composition at build time — the generated `.claude/agents/<role>.md` is a
  fully assembled document with no composition metadata.
- **Four patch operations:**
  - `append-after`: insert content after a named section
  - `replace`: replace a complete section (heading + body)
  - `delete`: remove a section entirely
  - `append`: append content at end of document
- **Section-aware Markdown parsing** in `sync.py`: `_find_section_bounds()` identifies sections
  by heading level, enabling precise patch targeting
- **`compose_agent()`** in `sync.py`: loads base template, applies patches, merges frontmatter;
  `extends:` and `patches:` keys are stripped from the generated output
- **`howto/agent-composition.md`**: full documentation — concept, patch ops, anchor reference,
  frontmatter-merge rules, debugging guide, 3-project compatibility
- **`agents/2-platform/sharkord-developer.md`** rebuilt as composition agent (v2.0.0):
  no longer a full copy of `1-generic/developer.md` — uses `extends:` + 3 patches

### Changed

- `sync.py`: `sync_agents()` detects `extends:` in frontmatter and invokes `compose_agent()`
  before variable substitution — full-replacement mode (no `extends:`) is unchanged
- `sync.py`: new import `pyyaml` (optional; warns gracefully if not installed)
- `agents/2-platform/sharkord-developer.md`: version bumped to 2.0.0, rebuilt as composition file
- `CLAUDE.md`: Schichten-Modell section updated — two modes for 2-platform, composition syntax,
  Entscheidungsbaum updated, howto reference added

### Notes

- **Backwards compatible:** existing platform agents without `extends:` continue to work unchanged
- **Requires PyYAML:** `pip install pyyaml` — sync.py warns and falls back to full-replacement
  if PyYAML is not available

---

## [0.15.1] — 2026-04-05

### Changed

- `agents/0-external/_skill-wrapper.md` (v1.1.0): replaced `{{SKILL_CONTENT}}` inline embedding
  with lazy Read-Instruktion — agent reads `.claude/skills/<skill>/SKILL.md` on demand
- `sync.py` — `normalize_skill_paths()`: rewrites `./ref.md` paths in copied SKILL.md to
  `.claude/skills/<skill>/ref.md` — consistent paths regardless of source repo structure
- `sync.py` — new template variables `SKILL_ENTRY_PATH` + `SKILL_BASE_PATH`; `SKILL_CONTENT` removed

---

## [0.15.0] — 2026-04-05

### Breaking Changes

- `external-skills.config.json`: `"submodules"` renamed to `"repos"` — update existing configs
- `external-skills.config.json`: `"enabled"` renamed to `"approved"` (meta-maintainer quality gate)
- `external-skills.config.json`: skill key `"submodule"` renamed to `"repo"`
- `external-skills.catalog.json`: removed — content merged into `external-skills.config.json`
- Projects must now opt-in to external skills via `"external-skills"` block in `agent-meta.config.json`

### Added

- **Two-gate system for external skills:** `approved: true` (meta-maintainer) + `enabled: true` in project config both required
- **`repos` section** in `external-skills.config.json`: 1:n relationship to skills, with `pinned_commit` for deterministic versioning
- **`pinned_commit` enforcement:** `sync.py` warns on every sync if submodule deviates from pinned commit
- **`add_skill()`** now auto-pins current commit to `pinned_commit` on registration
- **Project opt-in:** new `"external-skills"` block in `agent-meta.config.json` activates approved skills per project
- **`[WARN]`** for unknown or non-approved skills referenced in project config
- **`howto/external-skills.md`**: comprehensive howto with ASCII diagrams, full lifecycle (Skill-Autor → Meta-Maintainer → Projekt-Entwickler), `--add-skill` parameter reference, log output guide, troubleshooting, versioning strategy
- **`howto/first-steps.md`**: guided AI-assisted setup for first-time config

### Changed

- `sync.py` — `check_pinned_commits()`: new function, runs on every sync
- `sync.py` — `_skill_is_active()`: centralized two-gate check helper
- `sync.py` — `add_skill()`: writes `approved: false` as default, prints activation instructions
- `agents/1-generic/agent-meta-manager.md`: fixed skill deactivation instructions (was pointing to wrong config level)
- `howto/upgrade-guide.md`: migration guide for Breaking Changes
- `howto/instantiate-project.md`: external skills section updated, links to new howto
- `README.md`, `CLAUDE.md`: updated references, split `&&`-chained commands into individual blocks

### Migration from 0.14.x

See [howto/upgrade-guide.md](howto/upgrade-guide.md) — section "Breaking Change: v0.14.4 → approved".

In `external-skills.config.json`:
- Rename `"submodules"` → `"repos"`, add `"pinned_commit"` to each repo entry
- Rename `"enabled"` → `"approved"` in each skill entry
- Rename `"submodule"` → `"repo"` in each skill entry

In each project's `agent-meta.config.json`:
- Add `"external-skills": { "skill-name": { "enabled": true } }` for each desired skill

---

## [0.14.4] — 2026-04-05

### Added

- `howto/first-steps.md`: AI-assisted guided setup — hand this file to any AI assistant before the first sync for an interactive, step-by-step config walkthrough

### Changed

- `README.md` — Quick Start and Upgrading sections: split `&&`-chained commands into individual code blocks for granular review; added `first-steps.md` hint
- `howto/instantiate-project.md` — Step 1: split `&&`-chained commands; added tip box linking to `first-steps.md`
- `howto/agent-meta.config.example.json` — `_comment` references `first-steps.md`
- `CLAUDE.md` — directory structure updated to include `first-steps.md`

---

## [0.14.3] — 2026-04-05

### Fixed

- `sync.py` — stale agent cleanup: generated agents that are no longer in the active role set (removed from `config['roles']` or role no longer in ROLE_MAP) are now automatically deleted from `.claude/agents/` on every sync (`[DELETE]` in log). External skill agents are excluded from cleanup. Works in `--dry-run` mode.

---

## [0.14.2] — 2026-04-05

### Added

- `howto/CLAUDE.personal-template.md`: template for personal Claude preferences (gitignored, never committed)
- `sync.py` — `init_claude_personal()`: copies `CLAUDE.personal-template.md` to `CLAUDE.personal.md` in target project on first sync (only when `ai-provider: Claude`); idempotent

### Changed

- `sync.py` — `.gitignore` entries are ensured on every sync (not just once) — missing entries are appended; existing entries untouched
- `CLAUDE.md` — update-behavior table revised: added `CLAUDE.personal.md`, `.claude/settings.json`, `.gitignore` rows with committed/gitignored column
- `howto/sync-concept.md` — sync behavior table expanded; Team vs. Persönlich table updated with "Angelegt von" column
- `howto/instantiate-project.md` — commit command includes `.gitignore`; checklist expanded

## [0.14.1] — 2026-04-05

### Added

- `sync.py` — `init_settings_json()`: creates `.claude/settings.json` (team permissions skeleton) in target project if not present (only when `ai-provider: Claude`)
- `sync.py` — `ensure_gitignore_entries()`: ensures `.claude/settings.local.json`, `CLAUDE.personal.md`, and `sync.log` are in `.gitignore`; creates `.gitignore` if absent (only when `ai-provider: Claude`)

---

## [0.14.0] — 2026-04-04

### Added

- `agents/1-generic/agent-meta-manager.md` — new agent for managing agent-meta in a target project: upgrade, sync, feedback delegation, project-specific agent creation, external skill discovery
- `agents/1-generic/feature.md` — new workflow agent for full feature lifecycle (Branch → REQ → TDD → Dev → Validate → PR) via sub-agent delegation; does not implement anything itself
- `external-skills.catalog.json` — catalog of known/recommended external skill repositories; read by `agent-meta-manager` to help users discover available skills
- `scripts/sync.py` — `ROLE_MAP`: added `agent-meta-manager` and `feature` roles
- `howto/instantiate-project.md` — `feature` and `agent-meta-manager` added to generated agents table

---

## [0.13.2] — 2026-04-04

### Added

- `hint` frontmatter field in all 11 `1-generic` + 2 `2-platform` agent templates — short user-facing description used in `CLAUDE.md` agent table
- `sync.py` — `build_agent_hints()`: reads `hint` (preferred) or `description` from each active agent's template; generates `{{AGENT_HINTS}}` with orchestrator start hint + role table
- `sync.py` — `{{AGENT_HINTS}}` auto-injected variable, available in all templates
- `CLAUDE_MD_MANAGED_TEMPLATE` — new "Verfügbare Agenten" section with `{{AGENT_HINTS}}` + orchestrator entry point hint; technical table moved to subsection
- `howto/CLAUDE.project-template.md` — same agent sections added to `--init` template

### Fixed

- **#4** `howto/CLAUDE.project-template.md` — removed stale `{{PLATFORM_LAYER}}`, `{{TARGET_PLATFORM}}`; replaced `{{KEY_DEPENDENCIES}}` with `{{SYSTEM_DEPENDENCIES}}`
- **#4** `sync.py` — escape syntax `{{%VAR%}}` renders as `{{VAR}}` in output without triggering substitution (for literal docs)
- **#4** `agents/2-platform/sharkord-docker.md` — literal `{{PLATZHALTER}}` escaped to `{{%PLATZHALTER%}}`
- **#5** `sync.py` — generated agents now preserve template `description` field (with optional `{{PROJECT_NAME}}` interpolation) instead of overwriting with generic `"Agent for …"`
- `sync.py` — `build_agent_table()` and `build_agent_hints()` now respect `config['roles']` whitelist — excluded roles no longer appear in CLAUDE.md tables

---

## [0.13.1] — 2026-04-04

### Added

- `ai-provider` config field: controls provider-specific behavior; `"Claude"` enables automatic `CLAUDE.md` creation and managed block updates on every sync
- `{{AI_PROVIDER}}` variable: auto-injected from `ai-provider` config field, available as placeholder in all agent templates
- `sync.py` — if `ai-provider: Claude` and no `CLAUDE.md` exists, it is created automatically from template (no `--init` flag needed)
- `sync.py` — if `ai-provider` is not `Claude` but `CLAUDE.md` exists, managed block update is skipped with `[INFO]` log entry

### Fixed

- `sync.py` — replaced Unicode symbols (`ℹ`, `✓`, `✗`, `⚠`, `↓`) with ASCII equivalents to fix `UnicodeEncodeError` on Windows terminals (cp1252)

---

## [0.13.0] — 2026-04-04

### Added

- `sync.py` — `CLAUDE.md` managed block support: `<!-- agent-meta:managed-begin/end -->` block in project `CLAUDE.md` is updated on every normal sync with current `AGENT_TABLE`, version, and date
- `sync.py` — `sync_claude_md_managed()`: if `CLAUDE.md` exists but has no managed block, emits actionable `[WARN]` with copy-paste snippet to insert the block manually
- `howto/CLAUDE.project-template.md` — agent table now wrapped in managed block so `--init` creates a sync-maintained section out of the box
- `howto/instantiate-project.md` — note about managed block behavior added to Step 3
- `CLAUDE.md` — "Update-Verhalten bei sync" table extended with `CLAUDE.md` managed block rows + explanation

### Changed

- `sync.py` — all log output (warnings, skip reasons, info messages, print statements) is now **English only**
- `sync.py` — generated agent `description` field changed from `"Agent für …"` to `"Agent for …"`

---

## [0.12.3] — 2026-04-04

### Added

- `sync.py` — optional `"roles"` whitelist in config: only listed roles are generated; absent key = all roles (backwards-compatible). Skipped roles logged as `[SKIP]`.
- `sync.py` — `log.info()` method: disabled external skills now logged as `[INFO]` (always visible, not mixed with `[SKIP]`)
- `sync.py` — uninitialized submodule detection: if `external/<name>` dir is empty, emits actionable `[WARN]` with `git submodule update --init --recursive` hint
- `CLAUDE.md` — new "Config-Felder" section documenting `roles` whitelist

### Fixed

- **#1** `howto/agent-meta.config.example.json` — `_comment_snippets` now explicitly states path is relative to `.agent-meta/snippets/` (not `.claude/snippets/`)
- **#2** `meta-feedback.md` (`1.3.2`) — issue titles always in English regardless of `DOCS_LANGUAGE`; rule added to Don'ts and Sprache section
- **#3** `howto/instantiate-project.md` — `git submodule update --init --recursive` added to setup instructions

### Changed

- `agent-meta.config.json` (self-hosting) — `roles` whitelist added, excludes `docker` + `tester` → 0 warnings on sync
- `agent-meta.config.example.json` — `roles` field documented with comment

---

## [0.12.2] — 2026-04-04

### Added

- Neue Variable `{{USER_INPUT_LANGUAGE}}` — Sprache in der der Nutzer Anweisungen gibt (Agent-Input), unabhängig von `COMMUNICATION_LANGUAGE` (Agent-Output)
- `howto/agent-meta.config.example.json` — `USER_INPUT_LANGUAGE` mit Kommentar ergänzt

### Changed

- Alle 13 Agenten-Templates (`+0.0.1` Patch): `USER_INPUT_LANGUAGE` in `## Sprache`-Sektion ergänzt
  - `1-generic`: orchestrator `1.6.1`, developer `1.4.1`, tester `1.4.1`, validator `1.3.1`, requirements `1.3.1`, documenter `1.3.1`, release `1.3.1`, docker `1.3.1`, git `1.1.1`, meta-feedback `1.3.1`, ideation `1.2.1`
  - `2-platform`: sharkord-release `1.3.1`, sharkord-docker `1.2.1`
  - `0-external`: _skill-wrapper `1.0.1`
- `howto/agent-meta.config.example.json` nach `howto/` verschoben (war bisher im Repo-Root)
- Alle Referenzen auf `agent-meta.config.example.json` aktualisiert: README, CLAUDE.md, ARCHITECTURE.md, howto/*, orchestrator.md
- CLAUDE.md — `COMMUNICATION_LANGUAGE` Beschreibung präzisiert (End-User Output), `USER_INPUT_LANGUAGE` in Variablen-Tabelle ergänzt

---

## [0.12.1] — 2026-04-04

### Added

- `orchestrator.md` (`1.6.0`) — Workflow L: GitHub Issue bearbeiten (Issue lesen → requirements → tester → developer → tester → validator → documenter → git close)
- `git.md` (`1.1.0`) — `gh issue` Kommandos: list, view, close mit Comment, PR mit "Closes #id"

---

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
