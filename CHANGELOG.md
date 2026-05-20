# Changelog

## [0.44.0] — 2026-05-20

### Added

- **Orchestrator v3.3.0**: New "Aufgaben-Kontext orchestrieren" section with task-depth classification (surface/structure/architecture), context tailoring by depth level, worker-to-tier matching, and cost-awareness for delegation decisions.
- **4 new model aliases** in `config/ai-providers.yaml`: `deepseek-pro`, `glm`, `mimo`, `minimax` — easier shorthand references for opencode-go models.

### Changed

- **Opencode powerful tier**: `kimi-k2.5` → `deepseek-v4-pro` (frontier reasoning model).
- **All 12 opencode-go models documented** in `config/ai-providers.yaml` with strengths and req/5h limits.

---

## [0.43.0] — 2026-05-19

### Added

- **Evaluator-Optimizer-Loop**: Generic quality-loop system with 6 configurable generator-evaluator pairs (`config/evaluator-criteria.yaml` — 19 criteria, injected into templates via `EVALUATOR_CRITERIA_TABLE`). Pairs cover developer↔reviewer, requirements↔reviewer, documenter↔reviewer, tester↔validator, developer↔security-auditor, release↔validator. Configurable max iterations, modes, and criteria per pair.
- **Orchestrator v3.2.0**: Major overhaul with delegation guard (code work always via `developer`), Map-Reduce for parallel independent tasks, context management, resilience patterns, and fast-routing for trivial questions.
- **README.md**: Complete feature overview with 35+ links to documentation, howtos, and architecture docs.

### Changed

- **Feature vs Developer routing clarification** in `AGENTS.md` and `use-orchestrator` rule — explicit decision tree for when to use `feature` (lifecycle coordination) vs `developer` (direct implementation).
- **10 Orchestrator optimization issues** created (#163–#172) tracking follow-up improvements.

---

## [Unreleased]

---

## [0.42.0] — 2026-05-19

### Added

- **`code-splitter` agent** (`agents/1-generic/code-splitter.md` v1.0.0): New agent for splitting large files into smaller modules, modularizing monolithic code, and refactoring oversized files. Registered in `config/role-defaults.yaml`, schema enum, and deployed roles in `project.yaml`. Generated for all 4 providers (Claude, Continue, Gemini, Opencode).
- **`/update-meta` command** (`commands/1-generic/update-meta.md`): New slash-command for re-syncing agents without a version upgrade. Allows projects to pick up template changes without bumping their `agent-meta-version`. Generated for all active providers.
- **Module splits in `scripts/lib/`**: `agents.py` (886→536 lines) and `context.py` (763→257 lines) refactored into smaller, focused modules for better readability and LLM-assisted development.
- **REQUIREMENTS.md extended**: 30 new requirements added across 3 categories (framework features, agent templates, developer experience).

### Fixed

- **VERSION mismatch in `project.yaml`**: `agent-meta-version` was stuck at `0.39.0` while the repo was at `0.41.0`. Updated to match current version.
- **Issue #162 — Feedback routing**: Split feedback instructions in `AGENTS.md` into separate sections for project-feedback (project issues) and agent-meta-feedback (framework issues). Previously conflated, causing confusion about which feedback channel to use.
- **`code-splitter` missing from schema enum**: Added `code-splitter` to `config/project-config.schema.json` roles enum to suppress config validation warning.

---

## [Unreleased]

---

## [0.41.0] — 2026-05-15

### Added

- **Sharkord plugin system** (`agents/2-platform/sharkord-developer.md`, `sharkord-validator.md`, `sharkord-feature.md`, `sharkord-orchestrator.md`): Enhanced developer agent with plugin structure, naming conventions, config validation, and cross-plugin pattern sharing. New validator agent with SDK deprecation, structure, test pyramid, and Docker checks. New feature agent with skeleton bootstrap checklist. New orchestrator extension with cross-plugin standardization workflow. Closes #140, #131, #132, #133.
- **Sharkord test pyramid** (`rules/2-platform/sharkord-developer.md`, `sharkord-feature.md`): Test pyramid guidance for Sharkord plugins. Closes #137.
- **SDK compatibility layer** (`rules/2-platform/sharkord-sdk.md`): SDK compatibility layer with stale TODO validation. Closes #136.
- **Build variant decision guide** (`rules/2-platform/sharkord-release.md`, `sharkord-docker-ops.md`): Build variant guidance for Sharkord releases and Docker operations. Closes #138.
- **Sharkord CI template** (`templates/sharkord-plugin-ci.yml`): CI template referenced by sharkord-release.md. Closes #135.
- **Meta-repo documentation strategy** (`agents/1-generic/documenter.md`, `docs/PATTERNS.md`, `docs/LEARNINGS.md`, `docs/CONVENTIONS.md`, `templates/learning-capture.md`): New documentation strategy with pattern/learning/convention files and learning-capture template. Closes #134, #142.
- **Multi-repo workspace support** (`scripts/lib/config.py`, `rules/1-generic/multi-repo-workspace.md`, `howto/project.yaml.example`): Config placeholders, multi-repo workspace rule, and project.yaml example updates. Closes #141.
- **Meta-repo as first-class config option** (`config/project-config.schema.json`, `scripts/lib/config.py`): `meta-repo` top-level config option with schema validation. Closes #148.
- **Standardized Sharkord starter templates** (`templates/2-platform/sharkord/starter/`): Plugin starter templates with standardized build system and structure enforcement, organized in layered directory structure.

### Fixed

- **Opencode provider support** (`config/project-config.schema.json`, `scripts/setup.py`): Added Opencode to all provider enums, missing roles (log-analyzer, feedback, infrastructure-check), missing top-level config fields (rules-preset, viz). Relaxed model-override pattern. Closes #139.
- **Sharkord orchestrator scope** (`agents/2-platform/sharkord-orchestrator.md`): Cross-plugin features now only active when `META_REPO: true`. Removed incorrect assumption that all Sharkord plugin repos are meta-repos. Closes #147.
- **StrictDoc double blank lines** (`docs/requirements/*.sdoc`): Removed consecutive blank lines causing TextX parse failures in 01-stakeholder-reqs.sdoc, 02a-agent-framework.sdoc, and index.sdoc. Closes #129.

### Changed

- **Templates directory layer architecture**: Moved starter templates from flat `templates/plugin-starter/` to layered `templates/2-platform/sharkord/starter/` structure, mirroring agents/ and rules/ conventions. Updated `sync.py` `copy_starter_templates()` accordingly. Closes #151.

---

## [0.40.0] — 2026-05-14

### Added

- **`infrastructure-check` agent** (`agents/1-generic/infrastructure-check.md` v2.0.0): New on-demand agent that inspects all generated project artifacts (hooks, MCP configs, agent templates, skills registry) and reports missing external prerequisites with platform-aware install suggestions (winget/scoop/brew/apt). Closes #125, #127.
- **StrictDoc requirements specification** (`docs/requirements/`): Comprehensive module-level requirements specification in StrictDoc format (Phase 1 Extended), covering all major sync.py subsystems.
- **StrictDoc GitHub Pages workflow** (`.github/workflows/strictdoc-pages.yml`): Automated HTML export and GitHub Pages deployment of the requirements specification on every push to main.
- **StrictDoc sync workflow** (`.github/workflows/strictdoc-sync.yml`, `scripts/strictdoc-sync.py`): Workflow for pushing private requirements to Unraid server.

### Fixed

- **`infrastructure-check` multi-provider awareness** (`agents/1-generic/infrastructure-check.md` v2.0.0): Template v1.0.0 only scanned Claude-specific paths. Extended Schritt 2–4 to cover all provider settings/hooks/agent directories. Added Provider-Pfad-Mapping table. Bumped version 1.0.0 → 2.0.0. Closes #128.
- **Invalid PREAMBLE fields in StrictDoc documents** (`docs/requirements/*.sdoc`): Removed invalid PREAMBLE fields from all sdoc documents that caused StrictDoc parse errors. Closes #126.
- **CI unit-tests and validate workflows** (`.github/workflows/test.yml`, `.github/workflows/validate.yml`): Lower `--cov-fail-under` from 70 to 20 to reflect actual lib/ coverage. Drop invalid `--all` flag from consistency-check. Register `PLUGIN_DIR_NAME` and `TECH_STACK` as built-in vars. Fix 21 unused imports via ruff. Whitelist documentation literals in placeholder check. Closes #124.

---

## [0.39.0] — 2026-05-12

### Added

- **`requires-agent:` Command Guard** (`scripts/lib/commands.py`, `commands/1-generic/`): Commands can declare a `requires-agent: <role>` frontmatter field. sync.py skips the command if that role is not active in `config['roles']`. Prevents dead slash-commands that delegate to inactive agents. Closes #113.
- **`skip: true` Rule Option** (`scripts/lib/rules.py`, `config/rules-presets.yaml`): New rule option that suppresses a rule for all providers (not just Gemini). Documented in `howto/features/rules.md` and `rules-preset-optimization.md`. Closes #90.
- **Continue model-tiers** (`config/ai-providers.yaml`): Continue provider now has a full 5-tier model mapping (nano/fast: `codellama:7b`, balanced: `claude-sonnet-4-6`, powerful/max: `claude-opus-4-7`). Closes #117.
- **Model tiers for core agents** (`config/role-defaults.yaml`): `orchestrator` → `fast`, `developer`/`feature`/`requirements` → `balanced`. Ensures coding quality is independent of the user's active model selection. Closes #116.
- **Framework-Feedback-Routing in Orchestrator** (`agents/1-generic/orchestrator.md` v2.8.0): Explicit routing section — any criticism or improvement suggestion targeting agent-meta itself must go to `meta-feedback`, not `git`. Closes #85.
- **`reviewer` agent** (`agents/1-generic/reviewer.md` v1.0.0): New code-review agent with MUST-FIX/SUGGESTION/NITPICK format. Added to orchestrator workflow. Closes #116.
- **`performance` agent** (`agents/1-generic/performance.md` v1.0.0): New performance-profiling agent (CPU, memory, I/O). Added to orchestrator workflow Q. Closes #116.
- **`/parallel` command** (`commands/1-generic/parallel.md`): New slash-command for spawning multiple agents in parallel. Closes #118.
- **temperature/maxTokens injection** (`scripts/lib/roles.py`, `scripts/lib/agents.py`): New `resolve_temperature()` / `resolve_max_tokens()` functions and corresponding frontmatter injection. Role defaults in `role-defaults.yaml`. Closes #79.
- **Code refactoring** (`scripts/lib/io.py`, `agents.py`, `config.py`, `mcp.py`): YAML import guard centralized in `io.py`. `inject_agent_fields()` helper reduces duplication. Closes #72.
- **API documentation** (`docs/architecture/07-api-reference.md`, `docs/architecture/08-provider-matrix.md`): Full module-by-module API reference and provider feature-comparison matrix. Closes #73.
- **GitHub Actions CI/CD** (`.github/workflows/validate.yml`, `scripts/validate-frontmatter.py`): Automated validation pipeline — consistency check, sync dry-run, placeholder check, frontmatter validation. Closes #83.
- **Unit test suite** (`scripts/lib/tests/`): 74 tests across `test_roles.py`, `test_agents.py`, `test_config.py`. CI via `.github/workflows/test.yml`. Closes #66.

### Fixed

- **Opencode MCP connection types** (`scripts/lib/mcp.py`): `_transform_for_opencode()` now maps `sse` → `remote` and `stdio` → `local`, and injects `"enabled": true` on every MCP entry. Opencode rejected the previously generated config. Closes #114.
- **lifecycle-check hook enabled** (`.meta-config/project.yaml`): `lifecycle-check: enabled: true` added — hook was copied but never activated. Git events now trigger pending-tasks generation. Closes #82.
- **Empty `allow`/`deny` arrays in settings.json** (`scripts/lib/hooks.py`): Init skeleton no longer writes empty permission arrays, reducing noise in new projects. Closes #108 (partial).
- **`{{VAR}}` substitution warnings in docs** (`agents/1-generic/agent-meta-manager.md`, `commands/1-generic/consistency-check.md`): Documentation examples showing `{{VAR}}` syntax now use the escape form `{{%VAR%}}` to prevent false "Variable not in config" warnings. Closes #76.

---

## [0.38.0] — 2026-05-11

### Added

- **Thread-Safe Event Logging** (`scripts/lib/viz.py`):
  - Added `threading.RLock` (`viz_lock`) for all read/write access to `events.jsonl`.
  - Atomic `clear-log` operation under the lock.
  - Tail-read heuristic for large logs (>1MB): reads last 10,000 lines instead of full file when a `since` filter is active.

- **Config-Driven Viz Server** (`scripts/viz-server.py`, `.meta-config/project.yaml`):
  - `viz.server.port` and `viz.server.timeout_sec` configurable via `project.yaml`.
  - `viz-server.py` reads settings from config; falls back to hardcoded defaults (8765 / 300s).

- **Dashboard UX Improvements** (`docs/live-dashboard.html`):
  - Toast notifications after log clear (with event count).
  - `localStorage` persistence for time-window selector and model-toggle state.
  - Graceful degradation when Cytoscape CDN fails to load.
  - Improved replay pause/resume precision via `pausedTotal` tracking.
  - Canvas resize synchronization with Cytoscape layout refit.

- **Documentation**:
  - `docs/viz-api.md` — Complete API endpoint reference.
  - `docs/viz-event-schema.md` — All 7 event types with field descriptions.
  - `docs/viz-architecture.md` — Design decisions (stable edge IDs, two-mode system, inactivity watcher, thread-safety).

### Changed

- **Code Quality** (`scripts/viz-report.py`):
  - Replaced `_state_to_json()` with `_DateTimeEncoder` for JSON serialization.
  - Extracted magic numbers to module constants (`_SESSION_FALLBACK_MINUTES`, `_MIN_EVENTS_FALLBACK`, etc.).
  - Consolidated duplicate status-icon mappings to `_STATUS_ICONS`.
  - Fixed XSS vector in `render_html()` by using `json.dumps()` instead of string interpolation for D3.js data.
  - Robust handling of events without timestamps (skip instead of crash).
  - Warning log for unknown `?window=` parameter values.
  - `import re` moved to module level (no more inline import).

---

## [0.37.0-beta.1] — 2026-05-10

### Added

- **Agent Visualization Dashboard** (`scripts/lib/viz.py`, `scripts/viz-report.py`, `docs/agent-mindmap.md`, `docs/agent-graph.html`):
  - **Static Mindmap**: Auto-generated Mermaid mindmap and interactive HTML graph of all agents, their delegations, and `workflow_tier` color-coding (🔴 required / 🔵 recommended / ⚪ optional). Generated via `sync.py --viz` or `sync.py --viz-only`.
  - **Dynamic Event Logging**: Opt-in mode where all generated agents receive a prompt block instructing them to write JSONL events (`agent_start`, `delegate`, `agent_end`, `tool_call`) to `.meta-viz/events.jsonl`. Sessions are per-run, gitignored, and auto-cleaned after `retention_days`.
  - **Four Viz Modes** (`project.yaml` → `viz.mode`): `off` (default), `static` (mindmap only), `dynamic` (event logging only), `full` (both mindmap + event logging).
  - **`viz-report.py` CLI**: Session reports in terminal (live watch), HTML (with Mermaid Gantt + sequence diagrams), or JSON. Optional Flask-based web server (`--serve`). Auto-cleanup of old sessions.
  - **Viz Commands**: `/viz-mindmap` (generate static viz), `/viz-report` (session report), `/viz-watch` (live monitoring), `/viz-toggle` (cycle or set viz mode: off→static→dynamic→full→off, then triggers sync).
  - **Howto** (`howto/agent-visualization.md`): Complete setup guide, manual event creation, JSONL format reference, session management, and architecture overview.
  - **Visualization prompt injection** applies to **all providers** (Claude, Continue, Gemini, Opencode) when `viz.mode` is `dynamic` or `full`.

---

## [0.36.0] — 2026-05-10

### Added

- **`log-analyzer` agent** (`agents/1-generic/log-analyzer.md`): Analysiert System- und Applikations-Logs mit Frequency-Clustering (Bash-basiert, vor LLM-Analyse), RFC-5424-konformer Severity-Klassifikation (CRITICAL/HIGH/MEDIUM/LOW/INFO), Auto-Discovery bekannter Log-Pfade (syslog, journald, Docker, Home Assistant, Nginx) und strukturierten Finding-Cards. Zwei Modi: `--quick` (Standard, token-sparend) und `--deep` (Codebase-Suche + Online-Recherche). Delegations-Routing zu `feedback`, `developer`, `security-auditor` und `requirements`. `workflow_tier: required`.
- **`homeassistant-log-analyzer` platform agent** (`agents/2-platform/homeassistant-log-analyzer.md`): Erweitert den generischen Log-Analyzer via `extends: + patches:` mit HA-spezifischem Log-Format, Logger-zu-Komponenten-Mapping, bekannten Fehlermustern (TemplateError, Platform not ready, MQTT disconnect, ZHA, Recorder), Startup-Rauschen-Filter und HA-spezifischen Delegations-Ressourcen (community.home-assistant.io, HACS).
- **`feedback` agent** (`agents/1-generic/feedback.md`): Standardisiert Bug-Reports, Feature-Requests und Verbesserungsvorschläge für das eingesetzte Projekt als GitHub Issues. Pflicht-Gate vor jeder direkten `git`-basierten Issue-Erstellung. Sechs Typen (`bug`, `feat`, `improvement`, `docs`, `security`, `question`) mit Body-Templates. Auto-Repo-Erkennung via `gh repo view`. Klare Abgrenzung zu `meta-feedback` (Framework vs. Projekt). `workflow_tier: required`.
- **`/analyze-logs` command** (`commands/1-generic/analyze-logs.md`): Delegiert an `log-analyzer`-Agent. Unterstützt optionalen Pfad und `--quick`/`--deep`-Flags. Wird für alle aktiven Provider generiert (Claude → `.claude/commands/`, Gemini → `.gemini/commands/` (`.toml`), Opencode → `.opencode/commands/`, Continue → `.continue/prompts/`).
- **`/feedback` command** (`commands/1-generic/feedback.md`): Delegiert an `feedback`-Agent. Unterstützt optionalen Typ-Keyword (`bug | feat | improvement | docs | security | question`) und Kurzbeschreibung als Argument. Wird für alle aktiven Provider generiert.
- **`/report-bug` command aktualisiert** (`commands/1-generic/report-bug.md`): Delegiert jetzt an `feedback`-Agent (Typ `bug` vorbelegt) statt eigenem Inline-Workflow — konsistent mit dem standardisierten Feedback-Kanal.
- **Orchestrator Workflow O + P** (`agents/1-generic/orchestrator.md`): Workflow O (Log-Analyse via `log-analyzer`) und Workflow P (Projekt-Issue via `feedback → gh issue create`) ergänzt. Beide neuen Agenten in der Agenten-Tabelle eingetragen.
- **`consistency-check.py`** (`scripts/consistency-check.py` + `scripts/lib/consistency/`): Neues Python-Script zur deterministischen Konsistenzprüfung von Agent-Templates, Commands und Cross-References ohne LLM-Aufruf. Prüft: Frontmatter-Version-Bumps (git-diff-basiert), semver-Format, extends/patches-Anchor-Auflösung, role-defaults-Vollständigkeit, Orchestrator-Tabelle, CHANGELOG-Erwähnungen, Platzhalter-Typos. Exit-Codes: 0=ok, 1=Fehler, 2=Script-Error. Flags: `--changed`, `--file`, `--strict`, `--json`, `--root`. Stdlib-only, PyYAML optional.
- **`/consistency-check` command** (`commands/1-generic/consistency-check.md`): Slash-Command ruft das Script auf, interpretiert Findings und bietet interaktive Fixes an. Wird für alle aktiven Provider generiert.
- **`agent-meta-manager` v1.5.0** (`agents/1-generic/agent-meta-manager.md`): Neuer Abschnitt 8 "Consistency-Check" mit vollständiger Referenz, Wann-ausführen-Tabelle und Link auf Howto.
- **Howto** (`howto/features/consistency-check.md`): Vollständige Referenz mit manueller Ausführung, allen CLI-Flags, Check-Katalog, JSON-Format, GitHub-Actions-Integration und Anleitung zum Hinzufügen neuer Checks.

---

## [0.35.0] — 2026-05-08

### Added

- **Provider config generation** (`scripts/lib/mcp.py` → `generate_provider_configs()`): sync.py now writes committed provider configs (with `${ENV_VAR}` references) and gitignored local configs (with actual values from `secrets.local.yaml`) for all active MCP servers. Supports all four formats: `claude-settings` (`.claude/settings.json`), `gemini-settings` (`.gemini/settings.json`), `opencode-json` (`opencode.json`), `continue-yaml` (`.continue/config.yaml`). Closes the Phase-2 gap from #86.
- **`init_secrets_template()`** (`scripts/lib/mcp.py`): `sync.py --init` now generates `.meta-config/secrets.local.yaml` from the active servers' `secrets:` lists. Users fill in actual values; the file is always gitignored.
- **`allow-committed-secrets`** in `project.yaml` / JSON Schema: new opt-out flag. `sync.py` reads the value and passes it to MCP config generation. Default: `false`.

### Changed

- **`write_checked()` now blocks on detected secrets** (`scripts/lib/io.py`): changed from warn-only to raising `SyncError` when a secret pattern is found in content destined for a committed file (`allow_secrets=False`, the new default). Local/gitignored files pass `allow_secrets=True` and continue to warn only. `sync.py` catches `SyncError` and exits with a clear message.
- **`SyncError`** added to `scripts/lib/io.py`: new exception class for fatal sync conditions.
- **`resolve_active_mcp_servers()` now respects `enabled-by-default`** (`scripts/lib/mcp.py`): servers added via platform bundles are only activated when their `enabled-by-default` flag is `true` (default). Servers explicitly listed in `mcp-servers:` in `project.yaml` are always activated regardless. Previously the flag had no effect.
- **`generate_mcp_artifacts()` signature extended** (`scripts/lib/mcp.py`): new `allow_committed_secrets` parameter threaded from `sync.py`.
- **`mcp-servers` and `allow-committed-secrets`** added to `config/project-config.schema.json`.

---

## [0.34.2] — 2026-05-07

### Added

- **MCP as first-class framework concept** (`config/mcp-registry.yaml`, `scripts/lib/mcp.py`, `scripts/lib/secrets.py`, `config/ai-providers.yaml`, `howto/mcp-setup.md`): global provider-agnostic MCP server catalog; rule file generation per active server + provider; automatic `.gitignore` entries for secrets files; secrets detection for MCP-generated content; platform bundles (`rules/2-platform/<platform>-mcp.yaml`). Closes #86.

### Security

- **Shell injection fixed** (`hooks/1-generic/dod-push-check.sh`, `lifecycle-check.sh`): Replaced `echo "$INPUT" | python3` pattern with heredoc-based stdin parsing. Eliminated `$DIR` interpolation into Python inline strings by passing the config path as `sys.argv[1]`. Closes #67, #75.
- **Secrets detection** (`scripts/lib/secrets.py`, `scripts/lib/io.py`): New `scan_for_secrets()` scans all generated files for API keys, tokens and passwords before writing. `write_checked()` helper integrates the scan into agents.py and rules.py with `[WARN]` output — does not block sync. Closes #68.

### Fixed

- **Gemini missing rules** (`config/rules-presets.yaml`): Removed all `gemini: skip` entries from `minimal` and `silent` presets. Gemini now receives `dod-criteria`, `issue-lifecycle`, `lifecycle-tasks`, `use-orchestrator` and `sync-interface` as plain rule files. Closes #71, #80.
- **Bare `except Exception:`** (`scripts/lib/agents.py`, `config.py`, `platform.py`, `skills.py`): All 6 broad exception catches replaced with specific types (`YAMLError`, `OSError`, `SubprocessError`, `JSONDecodeError`, `KeyError`). Closes #65.
- **Continue config.yaml never updating** (`scripts/lib/context.py`): Introduced a YAML-comment managed block (`# agent-meta:managed-begin/end`) that is refreshed on every sync with version and path metadata. User model configuration is left untouched. Closes #69.
- **Description truncation in non-Claude agents** (`scripts/lib/agents.py`): `extract_frontmatter_field()` now handles multi-line YAML folded strings — Continue and Opencode agents no longer get truncated descriptions. Closes #77.

### Performance

- **Incremental sync** (`scripts/lib/io.py`, `agents.py`, `rules.py`): `write_checked()` skips writing when content is already identical to the existing file. `sync.log` shows `[SKIP] unchanged` for unmodified files. Closes #70.

---

## [0.34.1] — 2026-05-07

### Security

- **`safe_path()` helper** (`scripts/lib/io.py`): New path traversal guard. Validates all generated file paths stay within the project root before writing. Prevents malicious config values (e.g. `prefix: "../../evil"`) from escaping the project directory.
- **All write operations secured** (`scripts/lib/agents.py`, `rules.py`, `hooks.py`, `commands.py`, `context.py`, `extensions.py`, `skills.py`): Every `write_text()`, `mkdir()`, and `unlink()` now uses `safe_path()`.

### Fixed

- Issue #64 — Path Traversal in sync.py (closed).

---

## [0.34.0] — 2026-05-07

### Added

- **`speech-mode: submissive`** (`speech/submissive.md`, `config/project-config.schema.json`, `README.md`, `howto/configs/*`): New communication style — completely devoted and submissive. Addresses user as master/mistress, no contradiction, no own opinion. No hardcoded mode list in syncer; works out-of-the-box via dynamic `speech/{mode}.md` resolution.
- Project config now uses `speech-mode: submissive` for agent-meta itself.

---

## [0.33.0] — 2026-05-07

### Added

- **Opencode provider** (`config/ai-providers.yaml`, `scripts/lib/agents.py`, `scripts/lib/commands.py`, `scripts/lib/context.py`): Full sync.py support for [opencode](https://opencode.ai) (sst/opencode), a terminal-based AI coding assistant with 75+ provider support.
  - Native agent frontmatter: `description`, `mode: subagent`, `model: anthropic/provider-id` (AI SDK convention)
  - Rules embedded into `AGENTS.md` managed block (opencode has no native rules/ dir); respects `opencode: skip` rule option; includes speech-mode
  - Commands: `.opencode/commands/*.md` — same `.md` + `$ARGUMENTS` format as Claude (no transformation needed)
  - Context: `AGENTS.md` with managed block (agent hints + all active rules)
  - Settings: `opencode.json` skeleton, created once, never overwritten
  - Model tiers: `anthropic/claude-*` IDs by default; configurable via `model-overrides.Opencode`
- **`AGENTS.personal.md`** (`howto/configs/AGENTS.personal-template.md`, `scripts/lib/context.py`): Personal opencode context file, analogous to `CLAUDE.personal.md`. Auto-created from template on first sync, gitignored, loaded via `instructions` field in `opencode.json`.
- **Provider-agnostic gitignore collection** (`scripts/sync.py`): `ensure_gitignore_entries` now collects `gitignore_entries` from ALL active providers, not only Claude. Previously non-Claude provider entries (e.g. `AGENTS.personal.md`) were silently dropped when Claude was absent.
- **Templates**: `howto/configs/OPENCODE.project-template.md`, `howto/configs/OPENCODE.settings-template.json`, `howto/configs/AGENTS.personal-template.md`
- **Docs**: `docs/providers/opencode.md`, updated `docs/providers/multi-provider.md`

---

## [0.32.0] — 2026-04-28

### Added

- **Provider-spezifische Modell-Tiers** (`config/ai-providers.yaml`, `config/role-defaults.yaml`, `scripts/lib/roles.py`): Fünf abstrakte Tiers (`nano`, `fast`, `balanced`, `powerful`, `max`) ersetzen Claude-spezifische Aliase in `role-defaults.yaml`. `sync.py` mappt Tiers per Provider auf konkrete Modell-IDs — Gemini bekommt jetzt korrekte Gemini-Modelle statt ungültige Claude-Aliase.
- **Provider-Tier-Mapping** (`config/ai-providers.yaml`): `model-tiers` und `model-aliases` pro Provider:
  - Claude: `nano/fast` → `claude-haiku-4-5-20251001` | `balanced` → `claude-sonnet-4-6` | `powerful/max` → `claude-opus-4-7`
  - Gemini: `nano/fast` → `gemini-2.5-flash` | `balanced/powerful/max` → `gemini-2.5-pro`
  - Continue: leer — Continue verwaltet Modelle zentral in `config.yaml`
- **Provider-spezifische `model-overrides`** (`config/project-config.schema.json`, `scripts/lib/roles.py`): Neues Format `model-overrides.Claude.git: fast` neben Legacy `model-overrides.git: fast`. Provider-Block hat Vorrang für den jeweiligen Provider; Legacy-Block gilt nur für Claude.
- **Rückwärtskompatibilität**: `haiku`/`sonnet`/`opus` als Aliase für Claude weiter gültig. Für andere Provider werden sie auf den entsprechenden Tier gemappt (`haiku` → `fast`, `sonnet` → `balanced`, `opus` → `powerful`).
- **Konkretes `run_in_background`-Beispiel** (`agents/1-generic/orchestrator.md` v2.5.0): Orchestrator zeigt jetzt Python-Code-Pattern für parallele Delegation (Vordergrund + `run_in_background=True`).

### Fixed

- **Gemini-Agenten hatten ungültige `model:`-Felder** (`scripts/lib/agents.py`): `model: haiku` oder `model: sonnet` wurden in Gemini-Frontmatter geschrieben — Gemini CLI ignoriert oder lehnt diese ab. Alle Gemini-Agenten erhalten jetzt korrekte Gemini-Modell-IDs.

---

## [0.31.0] — 2026-04-27

### Added

- **Debug Mode** (`scripts/lib/agents.py`, `config/project-config.schema.json`): New `debug-mode: true/false` flag in `project.yaml`. When active, `sync.py` injects a debug block into every generated agent — agents announce themselves (`[Agent: <name>]`), log delegations (`→ Delegiere an: ...`), and confirm completion (`✓ [Agent: <name>] fertig`). Default: `false` — zero change to any agent file.
- **Provider filter for hooks** (`hooks/1-generic/`, `scripts/lib/hooks.py`): New `# provider: <name>` metadata in hook scripts. Hooks declaring a specific provider (e.g. `Claude`) are skipped for all other providers (e.g. Gemini). `lifecycle-check.sh` and `dod-push-check.sh` now correctly declare `# provider: Claude`.

### Changed

- **`orchestrator` v2.4.0** (`agents/1-generic/orchestrator.md`): Agents table now includes all roles — `feature`, `release`, `meta-feedback`, `agent-meta-manager` added; `tester`, `validator`, `docker` annotated as optional/conditional.

### Fixed

- **Gemini/Continue received Claude-specific hooks** (`scripts/lib/hooks.py`): `lifecycle-check.sh` and `dod-push-check.sh` use the Claude Code hook API (JSON on stdin) and must not be copied to Gemini/Continue hook directories. Provider filter now enforces this.

---

## [0.30.0] — 2026-04-27

### Added

- **`session-conclusion.md` Rule** (`rules/1-generic/`): New generic rule enforcing session-end recognition in main chat and orchestrator. Defines session-end signals and requires documenter delegation.
- **`rules-preset-optimization.md` Howto** (`howto/features/`): New document explaining word-count thresholds, preset selection guide (`default`/`minimal`/`silent`), and lazy-load `_wf-` pattern for platform-heavy projects.
- **Configurable `.gitignore` behavior** (`scripts/sync.py`, `config/project-config.schema.json`): New `gitignore` section in `project.yaml` with three boolean flags — `local` (default: true), `generated` (default: false), `settings` (default: false). `generated: true` gitignores all provider agents/rules/hooks/commands dirs.
- **Post-merge branch cleanup** (`agents/1-generic/git.md` v2.2.0): New section with keep/delete signal detection (open TODOs, disabled automations, Phase-2 hints) and user-confirmation flow.
- **InfluxDB `measurement_schema` + `timezone` config** (`platform-configs/homeassistant.defaults.yaml`): New fields `influxdb_measurement_schema` (`by_entity`/`by_unit`) and `influxdb_timezone` prevent query failures from unknown schema or UTC offset.
- **Multi-tool strategy (AGENTS.md)** (`howto/features/sync-concept.md`): New section documenting `CLAUDE.md` ↔ `AGENTS.md` symlink pattern for teams using multiple AI tools.
- **Folder-level CLAUDE.md** (`howto/features/sync-concept.md`): New section with use cases and comparison table vs. `-ext.md`.

### Changed

- **`meta-feedback` agent v2.0.0** (`agents/1-generic/meta-feedback.md`): Complete rewrite with explicit decision tree and 10 typed issue templates — `bug`, `feat`, `new-agent`, `new-command`, `new-skill`, `new-platform`, `new-speech`, `improvement`, `docs`, `design`. Each type has its own title prefix, label set, and body template.
- **`orchestrator` v2.3.0** (`agents/1-generic/orchestrator.md`): Session-end now offers documenter (conclusions) and workflow K (feedback) explicitly.
- **`git` agent v2.2.0** (`agents/1-generic/git.md`): Post-merge cleanup decision block added.
- **`agent-meta-manager` v1.4.2** (`agents/1-generic/agent-meta-manager.md`): Section 6 now includes `--create-rule`, `--create-command`; section 8 adds active `wc -l` length check with threshold table; Don'ts add AGENTS.md symlink guidance.
- **`branch-guard.md` genericized** (`rules/1-generic/branch-guard.md`): `sync.py`-specific logic removed — rule now applies cleanly to non-agent-meta projects.
- **`agent-meta-sync-interface.md` extended** (`rules/2-platform/`): Branch-guard extension for `sync.py` added here (agent-meta-specific only).
- **`_wf-ha-mcp-local.md`** (`rules/2-platform/`): InfluxDB section now shows measurement schema and timezone context.
- **`sync-concept.md`** (`howto/features/`): `.gitignore` config section, folder-level CLAUDE.md, multi-tool AGENTS.md strategy, and `gitignore` field in project.yaml table.

### Fixed

- **`branch-guard.md`** (`rules/1-generic/`): Was leaking agent-meta-internal `sync.py` references into generic projects. (#57)

---

## [0.29.0] — 2026-04-25

### Added

- **Lazy-load `_wf-*.md` pattern** (`agents/1-generic/`, `rules/2-platform/`): Verbose workflow content extracted into `_wf-*.md` files that are skipped by `sync.py` and read on-demand via Read tool. Reduces always-loaded rule/agent tokens by 60–85%.
- **`rules-preset` framework** (`config/rules-presets.yaml`): Central control for `alwaysApply: false` (Claude + Continue) and `gemini: skip` per rule. Configured in `project.yaml` with preset inheritance (`default`, `minimal`, `silent`). Analogous to `dod-preset`.
- **Provider-aware `sync_rules()`** (`scripts/lib/rules.py`): Now receives `provider` parameter — injects `alwaysApply: false` frontmatter for Claude/Continue, skips rules entirely for Gemini based on preset config.
- **DoD conditional blocks in agent templates**: `{{#if DOD_X}}...{{/if}}` blocks in `feature.md`, `validator.md` — inactive DoD features produce zero output in generated agents.
- **New lazy-load knowledge files** (`agents/1-generic/`): `_wf-sync-interface.md`, `_wf-git-ops.md`, `_wf-security-audit.md`, `_wf-claude-review.md`, `_wf-feedback.md`, `_wf-scout.md`, `_wf-skill-lifecycle.md`, `_wf-upgrade.md`, `_wf-issue.md`.
- **New lazy-load knowledge files** (`rules/2-platform/`): `_wf-ha-package-migration.md`, `_wf-ha-entity-data.md`, `_wf-ha-mcp-local.md`, `_wf-ha-energy-template.md`, `_wf-sharkord-docker-binaries.md`, `_wf-sharkord-mediasoup.md`.

### Changed

- **Slim platform rules** (`rules/2-platform/`): `homeassistant-package-structure.md`, `homeassistant-entity-data.md`, `homeassistant-mcp-integration.md`, `homeassistant-energy-abstraction.md`, `sharkord-docker-ops.md`, `sharkord-sdk.md` — core constraints only, workflow detail moved to `_wf-*.md`.
- **Slim 1-generic rules**: `branch-guard.md`, `use-orchestrator.md`, `dod-criteria.md` — decision tree and verbose examples removed.
- **Slim agents** (`agents/1-generic/`): `orchestrator.md`, `git.md`, `agent-meta-manager.md`, `security-auditor.md` — workflow content extracted to `_wf-*.md` files.
- **`collect_rule_sources()`** (`scripts/lib/rules.py`): Now filters `_` prefix in both `1-generic` and `2-platform` layers — same pattern as `collect_sources()` in `agents.py`.

### Fixed

- **`strip_inactive_dod_blocks()` IndexError** (`scripts/lib/config.py`): Wrong group index `m.group(2)` (regex had only one capture group). Fixed via Python default argument closure.

---

## [0.28.1] — 2026-04-19

### Fixed

- **`context.py`: CLAUDE.md never created on `--init`** (`scripts/lib/context.py`): Template paths for `CLAUDE.project-template.md` and `CLAUDE.personal-template.md` corrected from `howto/` to `howto/configs/` — templates had been moved there but the paths were not updated.
- **`first-steps.md`: wrong `project.yaml.example` path** (`howto/setup/first-steps.md`): `cp` command corrected from `howto/project.yaml.example` to `howto/configs/project.yaml.example`.

---

## [0.28.0] — 2026-04-19

### Added

- **HA platform: MCP-Server-Guidelines** (`rules/2-platform/homeassistant-mcp-integration.md`): Neue Sektion "Lokale / Projektspezifische MCP-Server" — Dokumentationskonvention für lokale MCP-Server via `platform-config.yaml`, gitignore-Hinweise, Fallback-Strategie.
- **HA platform: project.yaml Template** (`howto/configs/project.yaml.homeassistant.example`): HA-spezifisches Beispiel ohne Build-Artifact-Felder, mit YAML/Jinja2-Kontext und HA-typischer Rollen-Whitelist.
- **branch-guard Rule** (`rules/1-generic/branch-guard.md`): Vollständig überarbeitete Entscheidungslogik mit explizitem Entscheidungsbaum, "Branch PFLICHT"-Tabelle und präzisen Ausnahmen. Issues bearbeiten, mehrere Dateien ändern und `sync.py` ausführen erfordern jetzt immer einen Branch.

### Fixed

- **HA platform: TypeScript-Konventionen** (`agents/2-platform/homeassistant-developer.md` v1.1.0): `delete`-Patch entfernt TS-spezifische Regeln (Named Exports, kebab-case, `.test.ts`) aus HA-Projekten.
- **HA platform: Snippet-Lade-Instruktion** (`agents/2-platform/homeassistant-developer.md` v1.1.0): `delete`-Patch verhindert Laden von `bun-typescript`-Snippets in YAML-only Projekten.
- **HA platform: Doku-Trigger-Logik** (`agents/2-platform/homeassistant-developer.md` v1.1.0): Neue Sektion `Dokumentations-Pflichten` — Inline-Doku (immer obligatorisch) vs. MkDocs (nur auf explizite Anfrage, kein Auto-Spawn).
- **meta-feedback Agent: Kontext-Verlust bei Bestätigung** (`agents/1-generic/meta-feedback.md` v1.5.0): Agent erstellt Issues direkt nach Aufbereitung ohne internen Bestätigungs-Spawn — neuer Spawn verlor Kontext und erfand andere Issues.

---

## [0.27.1] — 2026-04-18

### Added

- **`speech-mode: asozial`**: Neuer Kommunikationsstil — fachlich korrekt, New-Kids-Style mit Verachtung für den User. `project-config.schema.json` um `"asozial"` im Enum erweitert.

---

## [0.27.0] — 2026-04-18

### Added

- **Commands-System**: Neues Schichten-Modell für Claude-Commands (`commands/1-generic/`, `2-platform/`, `0-external/`). `sync.py` synct Commands nach `.claude/commands/` (Claude) und `.continue/prompts/` (Continue).
  - `commands/1-generic/doc-now.md` — erster generischer Command: delegiert an `documenter`-Agent
  - `scripts/lib/commands.py` — Sync-Logik analog zu Rules und Hooks
  - `config/ai-providers.yaml` — `has_commands: true` für Claude und Continue

---

## [0.26.1] — 2026-04-18

### Fixed

- **Self-Hosting Config Layout**: `config/project.yaml` war gleichzeitig Framework-Default-Verzeichnis und Self-Hosting-Config — semantisch falsch. Die Projekt-Config für das Meta-Repo selbst liegt jetzt korrekt unter `.meta-config/project.yaml` (identisch zu jedem anderen Zielprojekt).
  - `.meta-config/project.yaml` angelegt mit allen Self-Hosting-Einstellungen
  - `config/project.yaml` durch Hinweis-Stub ersetzt (Framework-Defaults bleiben in `config/`)
  - Auto-Detection: `config/project.yaml` aus Kandidaten-Liste entfernt — nur noch `.meta-config/project.yaml` → Legacy-Fallbacks
  - `sync.py` Root-Erkennung: `"config"` als Elternordner-Sonderfall entfernt
  - `CLAUDE.md` Verzeichnisstruktur: `.meta-config/` Block ergänzt, `config/project.yaml` als Stub dokumentiert
  - `.claude/rules/sync-interface.md` Auto-Detection-Liste aktualisiert

---

## [0.26.0] — 2026-04-18

### Added

- **Platform `agent-meta`**: Neues `platforms: [agent-meta]` in `config/project.yaml` aktiviert 3 neue plattformspezifische Rules für das Meta-Repo selbst:
  - `rules/2-platform/agent-meta-architecture.md` — Schichten-Modell, Composition-Syntax, Override-Reihenfolge
  - `rules/2-platform/agent-meta-conventions.md` — Invarianten, Versions-Bump-Tabelle, Rollen- und Platzhalter-Lifecycle
  - `rules/2-platform/agent-meta-sync-interface.md` — sync.py Flags, log-Format, Python-Modulstruktur
- **`agents/2-platform/agent-meta-developer.md`**: Erweiterter Developer-Agent speziell für das Meta-Repo (extends `1-generic/developer.md`). Ergänzt um Python-Stdlib-Only-Regel, ≤600-Zeilen-Modul-Grenze, SyncLog-Pflicht, keine `print()` in `lib/`.
- **Rules-Substitution**: `sync_rules()` wendet jetzt `substitute()` auf Rule-Inhalte an — Rules bekommen projektspezifische Variablen injiziert (z.B. `{{DOD_REQ_TRACEABILITY}}`, `{{CODE_LANGUAGE}}`).
- **`rules/1-generic/commit-conventions.md`**: Kanonische Commit-Konventions-Rule für alle Projekte — ersetzt duplizierte Tabellen in Agent-Templates.
- **`rules/1-generic/dod-criteria.md`**: DoD-Checkliste als Rule mit echten Projekt-Werten via Variablen-Substitution — jedes Projekt sieht seine tatsächlich konfigurierten DoD-Features.

### Changed

- **Config-Restructuring**: Framework-Config liegt jetzt sauber in `config/` (Meta-Repo-owned); Projektconfig in `.meta-config/project.yaml` (Projekt-owned, unabhängig von Submodul-Pfad und AI-Provider).
  - Auto-Detection: `.meta-config/project.yaml` → `config/project.yaml` → Legacy-Fallbacks
  - `--fill-defaults` schreibt in erkannte Config-Datei
- **`agents/1-generic/developer.md`** (2.0.1): Doppelte Commit-Tabelle entfernt — verweist auf Rule.
- **`agents/1-generic/validator.md`** (2.0.1): Doppelte DoD-Checkliste entfernt — verweist auf Rule.
- **`agents/1-generic/orchestrator.md`** (2.0.1): Veraltete Config-Pfad-Referenzen auf `.meta-config/project.yaml` aktualisiert.
- **`agents/1-generic/git.md`** (2.0.1): Veraltete `agent-meta.config.yaml` Referenzen bereinigt.
- **`agents/1-generic/agent-meta-manager.md`** (1.1.1): Alle 15 `agent-meta.config.yaml` Referenzen auf `.meta-config/project.yaml` aktualisiert.

### Fixed

- **`config.py` `substitute()`**: `{{%VAR%}}` Escape-Syntax funktionierte nicht — escaped Werte wurden vor der Substitution in echte Platzhalter umgewandelt und dann als fehlende Variablen gewarnt. Fix: Stash-before/restore-after Sentinel-Mechanismus.

---

## [0.25.1] — 2026-04-17

### Fixed

- **CLAUDE.md**: Veraltete Referenzen auf `ROLE_MAP in sync.py`, `DOD_DEFAULTS in sync.py`
  und `MANAGED_BLOCK_TEMPLATE in sync.py` korrigiert — zeigen jetzt auf die richtigen
  Dateien (`roles.config.yaml`, `dod-presets.config.yaml`, `templates/managed-block.md`,
  `scripts/lib/dod.py`).
- **CLAUDE.md**: Verzeichnisstruktur um `scripts/lib/`, `templates/` und
  `providers.config.yaml` ergänzt.
- **howto/sync-concept.md**: Struktur um neue Module aktualisiert.
- **howto/upgrade-guide.md**: `MANAGED_BLOCK_TEMPLATE` → `templates/managed-block.md`.

---

## [0.25.0] — 2026-04-17

### Added

- **`scripts/lib/`** — sync.py in 13 eigenständige Module aufgeteilt (log, io, config,
  roles, dod, platform, providers, agents, rules, hooks, skills, extensions, context).
  Jedes Modul ist ≤600 Zeilen und einzeln lesbar — optimiert für LLM-gestützte Entwicklung.
- **`providers.config.yaml`** — `PROVIDER_CONFIG` aus sync.py ausgelagert.
  Neuen AI-Provider (Cursor, Windsurf, ...) hinzufügen ohne Python-Code-Änderung.
  Enthält auch `gitignore_entries` pro Provider.
- **`templates/`** — Managed-Block-Templates als echte Dateien statt Multiline-Strings im Code:
  `managed-block.md`, `managed-block-project-stub.md`, `claude-md-managed.md`

### Changed

- **`scripts/sync.py`**: 3151 → 259 Zeilen — reiner CLI-Entrypoint.
  Alle Logik in `scripts/lib/` Module verschoben.
- **`roles.config.yaml`**: `ROLE_MAP` wird jetzt dynamisch aus den Rollen-Keys gebaut —
  kein separates Dict mehr im Python-Code.
- **`dod-presets.config.yaml`**: `DOD_DEFAULTS` hardcoded Dict entfernt —
  das `full`-Preset dient als Fallback (war inhaltlich identisch).

---

## [0.24.0] — 2026-04-17

### Added

- **YAML config format** — All configuration files now use YAML as the primary format.
  JSON is still supported as a backward-compatible fallback (auto-detected by file extension).
  - `agent-meta.config.yaml` replaces `agent-meta.config.json`
  - `roles.config.yaml` replaces `roles.config.json`
  - `dod-presets.config.yaml` replaces `dod-presets.config.json`
  - `external-skills.config.yaml` replaces `external-skills.config.json`
- **`scripts/migrate-config.py`** — Migration helper: converts an existing
  `agent-meta.config.json` to `agent-meta.config.yaml`. Strips `_comment*` keys,
  preserves multiline strings as YAML block scalars, renames original to `.json.bak`.
  Usage: `py .agent-meta/scripts/migrate-config.py --config agent-meta.config.json`
- **`howto/agent-meta.config.example.yaml`** — YAML version of the example config
  (replaces `agent-meta.config.example.json`).

### Changed

- **`sync.py`**: `load_config()` now accepts `.yaml` / `.yml` files directly.
  When `--config agent-meta.config.json` is passed but a `.yaml` sibling exists,
  the YAML file is preferred automatically (zero-friction migration).
  `fill_defaults` write-back also writes YAML when the config is YAML.
- **`sync.py`**: `load_dod_presets()`, `load_roles_config()`,
  `load_external_skills_config()` all prefer `.yaml` over `.json` fallback.
- **`sync.py`**: `add_skill` (`--add-skill`) writes `external-skills.config.yaml`.
- All documentation and howto files updated: `.config.json` → `.config.yaml`.

### Migration

Existing projects on JSON configs continue to work unchanged.
To migrate a project config to YAML:

```bash
py .agent-meta/scripts/migrate-config.py --config agent-meta.config.json
py .agent-meta/scripts/sync.py --config agent-meta.config.yaml
```

---

## [0.23.0] — 2026-04-16

### Added

- **Platform Config Instantiation** — `sync.py` now reads `platform-configs/<platform>.defaults.yaml`
  and merges platform-level defaults into the project config before generating agents.
  Projects using a platform get sensible variable defaults without manual repetition.
  Supports `variables`, `dod`, `model-overrides`, `memory-overrides`, `permission-mode-overrides`.
- **HomeAssistant platform** (`platform-configs/homeassistant.defaults.yaml`) — Platform defaults
  for Home Assistant Python integrations (Python language, German docs, YAML conventions).
- **Sharkord platform config** (`platform-configs/sharkord.defaults.yaml`) — Extracted shared
  Sharkord defaults (Bun/TypeScript, plugin structure, build commands) into platform config.
- **HomeAssistant agents** (`agents/2-platform/`):
  - `homeassistant-developer.md` — HA-specific developer with Python/HACS conventions
  - `homeassistant-documenter.md` — HA-specific documenter
- **HomeAssistant rules** (`rules/2-platform/`):
  - `homeassistant-energy-abstraction.md` — Energy platform integration patterns
  - `homeassistant-entity-data.md` — Entity state/attribute data conventions
  - `homeassistant-mcp-integration.md` — MCP server integration guide
  - `homeassistant-notifications.md` — Persistent notification patterns
  - `homeassistant-package-structure.md` — HACS package layout conventions
  - `homeassistant-yaml-conventions.md` — HA YAML configuration patterns
- **Sharkord rules** (`rules/2-platform/`):
  - `sharkord-docker-ops.md` — Docker operations for Sharkord plugins
  - `sharkord-sdk.md` — Sharkord SDK usage patterns
- **`howto/platform-config.md`** — Full documentation for the platform config system.

### Changed

- **`sharkord-developer.md`**: Reduced to platform-specific overrides only; shared content
  moved to `sharkord.defaults.yaml` and rules files.
- **`sharkord-docker.md`**, **`sharkord-release.md`**: Minor updates aligned with platform config.
- **`sync.py`**: Added `load_platform_defaults()` and `merge_platform_defaults()` functions.
  Platform defaults are merged at sync start — project config values always win.

---

## [0.22.0] — 2026-04-14

### Added

- **`--fill-defaults`** — New `sync.py` parameter that writes missing structural config fields
  (`dod-preset`, `max-parallel-agents`, `speech-mode`, `dod.*`) with their schema defaults
  into `agent-meta.config.yaml`. Missing `variables.*` keys are reported as `[WARN]` only —
  no empty strings written (no sensible default exists for project-specific variables).
  Supports `--dry-run`. Useful for onboarding new projects or auditing existing configs.

---

## [0.21.0] — 2026-04-12

### Added

- **Multi-Provider Support** (`ai-providers` array in `agent-meta.config.yaml`):
  Projects can now target Claude, Gemini, and Continue simultaneously.
  Backward-compatible: legacy `ai-provider` string field still works.
- **Continue integration**: sync.py generates `.continue/agents/`, `.continue/prompts/`,
  and `.continue/rules/` for use with local LLMs (Ollama, ROCm, etc.) via Continue IDE extension.
  Controlled by `provider-options.Continue.generate-prompts` and `prompt-mode` (`full` | `slim`).
- **`provider-options` config block**: Per-provider options with schema validation.
  Currently active: `Continue.generate-prompts`, `Continue.prompt-mode`.
- **`speech-mode`** — Configurable agent communication style:
  Generates `.claude/rules/speech-mode.md` (auto-loaded by Claude Code into all agent contexts).
  Modes: `full` (default, no rule), `short` (facts only, no filler), `childish` (playful,
  animal/toy analogies, emojis), `caveman` (brutally short, cave-speak).
  No agent template changes needed — purely via the Rules layer.
- **`speech/` directory**: Mode definition files (`short.md`, `childish.md`, `caveman.md`, `full.md`).
  Add new modes by dropping a file here and extending the schema enum.
- **Howto files**: `howto/multi-provider.md`, `howto/CONTINUE.config-template.yaml`,
  `howto/CONTINUE.project-template.md`, `howto/GEMINI.project-template.md`.

### Changed

- **`agent-meta.schema.json`**: Added `ai-providers` (array), `provider-options` (object),
  `speech-mode` (enum) fields with full validation.
- **`sync.py`**: `sync_speech_mode()` function — copies speech rule on sync, removes it on `full`.
  `resolve_provider_options()`, `resolve_providers()` for multi-provider resolution.
  Continue prompt generation (`sync_prompts_for_continue()`).
- **CLAUDE.md**: `speech-mode` config section, `speech/` in directory structure,
  updated `provider-options` documentation.
- **`howto/agent-meta.config.example.json`**: Added `speech-mode`, `provider-options` examples.

### Migration from v0.20.0

No breaking changes — fully backward-compatible.

- `speech-mode` is optional. If absent (or `"full"`), no rule is generated — behavior unchanged.
- `ai-provider` (string) still works. `ai-providers` (array) is the new preferred form.
- `provider-options` is optional. Omitting it keeps all existing behavior intact.

## [0.20.0] — 2026-04-08

### Added

- **DoD-Presets** (`dod-preset` in `agent-meta.config.yaml`):
  Predefined quality profiles that set defaults for all DoD criteria.
  Three built-in presets: `full` (all checks, default), `standard` (tests yes, REQ-IDs no),
  `rapid-prototyping` (all off — max speed). Individual overrides via `dod` block.
  Precedence: `dod` override > `dod-preset` > `full`.
- **`dod-presets.config.yaml`**: New config file defining presets. Meta-maintainer managed.
  Easy to extend: add a new preset entry, update schema enum.
- **DoD visibility**: Resolved DoD values now appear in CLAUDE.md managed block
  (preset name + all criteria). sync.log shows `[INFO] DoD preset '...' -> ...`.
- **`DOD_PRESET` template variable**: Auto-injected by sync.py, available in agent templates.
- **`dod-push-check` hook v1.1.0**: Now includes Branch-Guard — blocks `git push` on
  main/master. TEST_COMMAND missing = skip test gate (was: hard block).

### Changed

- **CLAUDE.md**: DoD section restructured — `dod-preset` as primary entry, `dod` as override.
  Added "how to add new presets" and "how to add new columns" instructions.
- **agent-meta.schema.json**: New `dod-preset` field (enum: full, standard, rapid-prototyping).
  `dod` description updated (override semantics).
- **Example config** (`howto/agent-meta.config.example.json`): Added `dod-preset` field.

### Migration from v0.19.0

No breaking changes — fully backward-compatible.

- `dod-preset` is optional. If absent, `full` is used (same behavior as before).
- Existing `dod` blocks continue to work as overrides on top of the preset.
- The `dod-push-check` hook is opt-in (requires `"hooks": {"dod-push-check": {"enabled": true}}`).

## [0.19.0] — 2026-04-07

### Added

- **OpenSCAD Developer Agent** (`1-generic/openscad-developer.md` v1.0.0):
  Specialized developer role for parametric 3D model generation in OpenSCAD.
  - Render-Inspect-Refine Loop as core workflow (visual feedback via MCP)
  - Mandatory gates: `validate_scad` before render, `analyze_model` before export
  - MCP-agnostic: works without MCP server (writes .scad directly), full loop with openscad-mcp
  - Print optimization knowledge: tolerances, overhangs, wall thickness, `$fn` guidelines, hole correction formula
  - Parametric-by-default: all dimensions as named variables, parameter table as standard output
  - Skill-aware: discovers opengrid-openscad and home-organization skills at runtime
  - BOSL2-aware: checks via `get_libraries`, uses library features when available
  - Versioned iteration: `model_v01.scad` → `model_v02.scad` — never overwrites previous state
- New role in `roles.config.yaml`: tier `optional`, model `sonnet`, memory `local`
- New role in `agent-meta.schema.json` roles enum
- ROLE_MAP entry in `sync.py`

### Changed

- **CLAUDE.md**: Role classification, model defaults, memory defaults, dependency map updated
- **README.md**: Supported Platforms and Agent Roles tables updated

### Fixed

- **`.gitignore` missing `agent-memory-local/`**: Local agent memory directories were not
  gitignored. Added `.claude/agent-memory-local/` to `GITIGNORE_ENTRIES` in `sync.py`
  and to the managed .gitignore block.

## [0.18.0] — 2026-04-07

### Added

- **Configurable Definition of Done** (`dod` block in `agent-meta.config.yaml`):
  Four independently toggleable quality criteria: `req-traceability` (default: true),
  `tests-required` (default: true), `codebase-overview` (default: true),
  `security-audit` (default: false). Missing `dod` block = all defaults (backward-compatible).
  `sync.py` injects `{{DOD_REQ_TRACEABILITY}}`, `{{DOD_TESTS_REQUIRED}}`,
  `{{DOD_CODEBASE_OVERVIEW}}`, `{{DOD_SECURITY_AUDIT}}` as template variables.
- **Role tier classification** (`tier` field in `roles.config.yaml`):
  `required` (orchestrator, developer, git), `recommended` (tester, validator, documenter,
  requirements, feature), `optional` (all others). Tier is a recommendation — all roles
  are generated by default. Users control via `roles` whitelist.
- **Parallel agent execution** (`max-parallel-agents` in config + schema):
  Configurable limit (1–5, default: 2). Orchestrator and feature workflows now mark
  parallelizable steps with `∥`. `run_in_background` guidance in coordinator templates.
- **Agent delegation map** (`howto/agent-delegation-map.md`): Complete matrix of all
  agent-to-agent references (delegation vs. referral), Mermaid graph, role categories,
  parallelizable groups, common delegation paths.
- **Branch-Guard (Step 0)** in orchestrator workflows A, B, E, L: Prevents direct
  commits on main/master. Creates `feat/`, `fix/`, `refactor/` branches automatically.
- **Workflow N** in orchestrator: External skill repo suggestion — orchestrates
  scout evaluation → manager activation → git commit.
- **Commit type `ci`** added to all commit convention tables.
- **External Skill lifecycle** in agent-meta-manager (7.1–7.7): Status matrix,
  activate, deactivate, add-skill, user feedback, submodule management, consistency check.
- **Feedback type `external-skill`** in meta-feedback agent with label support.

### Changed

- **orchestrator.md** v1.7.0 → v2.0.0: Configurable DoD (tiered checklist),
  conditional workflow steps (`?` marker), Branch-Guard, parallel steps (`∥`),
  DoD-Status block with injected variables.
- **developer.md** v1.4.1 → v2.0.0: REQ-ID requirement conditional on `req-traceability`,
  dual workflow (with/without REQ), commit table corrected, DoD-Status block.
- **validator.md** v1.3.1 → v2.0.0: Traceability audit conditional on `req-traceability`,
  DoD checklist tiered (always-active + conditional sections), DoD-config reference table.
- **git.md** v1.3.0 → v2.0.0: Commit types corrected (`chore` → never REQ-ID),
  dual examples (with/without req-traceability), `REQ-Traceability` status in header.
- **feature.md** v1.1.0 → v1.2.0: Conditional lifecycle steps (`?` marker),
  parallel validation+documentation (6∥7), DoD-Status block.
- **agent-meta-manager.md** v1.0.0 → v1.1.0: Seven skill lifecycle sub-workflows.
- **meta-feedback.md** v1.3.2 → v1.4.0: External skill feedback type + label.
- **roles.config.yaml**: `tier` field added to all roles, `developer` description
  simplified (removed "nach REQ-IDs" — now conditional).
- **agent-meta.schema.json**: `dod` block, `max-parallel-agents` field.
- **CLAUDE.md**: DoD config section, commit format with Conventional Commits explanation,
  role classification table, Branch-Guard in workflows, auto-injected variables list updated.

### Fixed

- **`chore` commit type** falsely required REQ-ID in all commit convention tables.
  Example (`chore: bump version to 1.2.0`) contradicted the table. Now correctly: never.
- **DoD was monolithic** — all-or-nothing with no way to disable REQ-traceability,
  tests, or codebase overview per project. agent-meta itself has no REQUIREMENTS.md
  but enforced REQ-IDs in its own DoD.
- **Orchestrator workflows A, B, E, L** had no branch-guard — allowed direct commits
  on main/master without user confirmation.

### Migration from v0.17.0

No breaking changes — all new features are opt-in with backward-compatible defaults.

- `dod` block is optional. If absent, all defaults apply (same behavior as before).
- `max-parallel-agents` defaults to 2. Set to 1 to keep sequential behavior.
- `tier` in `roles.config.yaml` is informational — does not filter roles.
- Agent templates now contain `?`-marked steps that respect DoD config. With default
  config (all true), behavior is identical to v0.17.0.
- Commit conventions now correctly exempt `chore`, `docs`, `ci` from REQ-ID requirement.
  If your project used `chore(REQ-xxx):` format, it still works but is no longer required.

---

## [0.17.0] — 2026-04-07

### Added

- **Hooks-Schichten-System** (`hooks/`): Vier-Schichten-Modell analog zu Rules und Agents.
  `sync.py` kopiert Hook-Skripte aus `0-external/`, `1-generic/`, `2-platform/` nach `.claude/hooks/`.
  Stale-Tracking via `.claude/hooks/.agent-meta-managed`.
  Registrierung in `.claude/settings.json` nur bei Opt-in: `"hooks": {"<name>": {"enabled": true}}`.
  Settings.json wird bei jedem Sync gemergt (Hooks-Section) — nicht mehr nur einmalig angelegt.
- **`dod-push-check.sh`** (`hooks/1-generic/`): Blockiert `git push` wenn Tests nicht grün sind.
  Liest `TEST_COMMAND` aus `agent-meta.config.yaml` oder `$AGENT_META_TEST_COMMAND`.
- **`--create-hook <name>`** in `sync.py`: Erstellt `.claude/hooks/<name>.sh` als Template.
  Projekt-eigene Hooks — nie von sync.py überschrieben.
- **`init_settings_local_json()`** in `sync.py`: Erstellt `.claude/settings.local.json` Skeleton
  beim ersten Claude-Sync (`--init` oder `ai-provider: Claude`). Einmalig, nie überschrieben.
- **`howto/hooks.md`** (neu): Vollständige Dokumentation des Hooks-Systems —
  Schichten, Sync-Verhalten, dod-push-check Konfiguration, Abgrenzung zu Rules.
- **`permissionMode`-Injection** in `sync.py`: `resolve_permission_mode()` +
  `inject_permission_mode_field()` — analog zu `model` und `memory`.
  Liest aus `roles.config.yaml` (Meta-Default) oder `permission-mode-overrides` in
  `agent-meta.config.yaml` (Projekt-Override).
- **`permission_mode`-Feld in `roles.config.yaml`**: `validator` → `plan`,
  `security-auditor` → `plan`. Alle anderen Rollen leer (Standard-Verhalten).
- **`permission-mode-overrides`** in `agent-meta.config.yaml`: Projekte können einzelne Rollen
  überschreiben. Gültige Werte: `plan`, `acceptEdits`, `bypassPermissions`, `default`.
- **`agent-meta.schema.json`** (neu): Vollständiges JSON Schema Draft-07 für
  `agent-meta.config.yaml`. Validiert alle Top-Level-Keys, Enum-Werte für
  `model-overrides` (haiku/sonnet/opus), `memory-overrides` (project/local/user),
  `permission-mode-overrides` (plan/acceptEdits/bypassPermissions/default), Hooks, External Skills.
- **Optionale Schema-Validierung** in `sync.py`: Wenn `jsonschema` installiert ist,
  werden Config-Fehler als Warnings ausgegeben (graceful fallback wenn nicht installiert).
- **`howto/agent-isolation.md`** (neu): Dokumentation für `isolation: worktree` —
  Wann sinnvoll, bekannte Fallstricke (Submodule, Merge-Konflikte, Windows), Konfiguration.
- **`rules/1-generic/issue-lifecycle.md`** (neu): Erste generische Rule.
  Erinnert alle Agenten daran, GitHub Issues nach Abschluss zu kommentieren und zu schließen.

### Changed

- **Agent-Descriptions bereinigt**: Alle `1-generic/*.md` Templates hatten
  „Generisches Template für den X-Agenten." in der `description:` — entfernt.
  Ersetzt durch prägnante, einzeilige Beschreibungen ohne interne Implementierungsdetails.
  Wirkt sich sofort auf den Claude Code Agent-Picker aus (nach nächstem Sync).
- **`git.md`** v1.2.0 → v1.3.0: DoD-Hooks-Sektion + Workflow 7 (Issue schließen nach Arbeit).
- **`feature.md`** v1.0.0 → v1.1.0: Frontmatter-Kommentar mit `isolation: worktree` Opt-in-Hinweis.
- **`CLAUDE.md`**: Hooks-System, permissionMode-Overrides, JSON-Schema, settings.json-Verhalten,
  settings.local.json-Init, agent-isolation.md — alle neuen Konzepte vollständig dokumentiert.
- **`howto/instantiate-project.md`**: `$schema`-Zeile im Config-Template ergänzt.
- **`agent-meta.config.yaml`** (self-hosting): `$schema`-Referenz ergänzt.

### Migration von v0.16.5

Keine Breaking Changes.

- Neue Dateien in `.claude/hooks/` werden automatisch angelegt — kein Opt-in nötig.
- `.claude/settings.json` wird bei aktivierten Hooks gemergt. Bestehende Dateien ohne
  Hooks-Section bleiben unverändert bis ein Hook aktiviert wird.
- `.claude/settings.local.json` wird beim nächsten Sync (wenn nicht vorhanden) erstellt.
- `validator` und `security-auditor` erhalten `permissionMode: plan` im generierten Agent.
  Falls das für ein Projekt nicht gewünscht ist:
  `"permission-mode-overrides": {"validator": "default"}` in `agent-meta.config.yaml`.

---

## [0.16.5] — 2026-04-06

### Added

- **Rules-Schichten-System** (`rules/`): Vier-Schichten-Modell analog zu Agenten.
  `sync.py` kopiert Rules aus `0-external/`, `1-generic/`, `2-platform/` nach `.claude/rules/`.
  Platform-Rules (`<platform>-<name>.md`) überschreiben gleichnamige Generic-Rules.
  Stale-Tracking via `.claude/rules/.agent-meta-managed` — entfernt veraltete Managed-Rules.
- **`--create-rule <name>`** in `sync.py`: Erstellt `.claude/rules/<name>.md` als leeres Template.
  Überschreibt nie bestehende Dateien.
- **`howto/rules.md`** (neu): Vollständige Dokumentation des Rules-Systems —
  Schichten, Sync-Verhalten, Naming-Konvention, Abgrenzung zu Extensions.
- **`CLAUDE.md`**: Rules-Abschnitt ergänzt (Vier-Schichten-Modell, Sync-Verhalten,
  Abgrenzung zu Extensions), Update-Verhalten-Tabelle um Rules-Zeilen erweitert,
  Verzeichnisstruktur um `rules/` ergänzt.

### Migration von v0.16.4

Keine Breaking Changes. `sync.py` läuft silent durch wenn `rules/1-generic/` leer ist —
kein Log-Eintrag, kein Warning.

---

## [0.16.4] — 2026-04-06

### Added

- **`howto/agent-memory.md`** (neu): Vollständige Dokumentation des Agent-Memory-Systems —
  drei Scopes (`project`, `local`, `user`), Konfiguration via `roles.config.yaml` +
  `memory-overrides`, MEMORY.md-Struktur-Empfehlungen, `.gitignore`-Verhalten.
- **`memory:`-Injection in `sync.py`**: `resolve_memory()` + `inject_memory_field()` —
  liest Memory-Scope aus `roles.config.yaml` (Meta-Default) oder `memory-overrides` in
  `agent-meta.config.yaml` (Projekt-Override). Wird nach `model:` in den Frontmatter injiziert.
- **`memory`-Feld in `roles.config.yaml`**: Memory-Scope-Defaults für alle Rollen.
  `validator`, `documenter`, `requirements`, `security-auditor` → `project`;
  `agent-meta-scout` → `local`; alle anderen → leer (kein Gedächtnis).
- **`memory-overrides`** in `agent-meta.config.yaml`: Projekte können einzelne Rollen
  überschreiben. Precedence: Projekt-Override > Meta-Default > kein Feld.
- **`CLAUDE.md`**: `memory-overrides`-Abschnitt mit Scopes-Tabelle und Defaults ergänzt.

### Migration von v0.16.3

Keine Breaking Changes — generierte Agenten bekommen ggf. ein neues `memory:`-Feld,
wenn `roles.config.yaml` einen Default definiert. Wer das nicht möchte: `"memory-overrides": { "<rolle>": "" }` im Projekt setzen.

---

## [0.16.3] — 2026-04-06

### Changed

- **`roles.config.yaml`** (neu): Modell-Defaults aus `sync.py` ausgelagert —
  Meta-Maintainer pflegt Rollen + empfohlene Modelle + Beschreibungen zentral in dieser Datei.
  `sync.py` liest Defaults von dort statt aus einer hardkodierten Konstante.
- **`sync.py`**: `DEFAULT_MODEL_MAP`-Konstante entfernt → `load_roles_config()` liest
  `roles.config.yaml`; `resolve_model()` nimmt `agent_meta_root` als Parameter.
- **`CLAUDE.md`**: `model-overrides`-Abschnitt zeigt auf `roles.config.yaml` statt sync.py;
  Verzeichnisbaum um `roles.config.yaml` ergänzt.

### Migration von v0.16.2

Keine Breaking Changes — Verhalten identisch. Modell-Anpassungen jetzt in
`roles.config.yaml` statt in `sync.py`.

---

## [0.16.2] — 2026-04-06

### Added

- **Zentrales Modell-Mapping** (`DEFAULT_MODEL_MAP` in `sync.py`): Meta-Maintainer pflegt
  empfohlene Claude-Modelle pro Rolle. `sync.py` injiziert `model:`-Feld beim Generieren.
- **`model-overrides`** in `agent-meta.config.yaml`: Projekte können einzelne Rollen überschreiben.
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
- **`external-skills.config.yaml`**: neuer `repos`-Eintrag für `awesome-claude-code`.
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

- `external-skills.config.yaml`: `"submodules"` renamed to `"repos"` — update existing configs
- `external-skills.config.yaml`: `"enabled"` renamed to `"approved"` (meta-maintainer quality gate)
- `external-skills.config.yaml`: skill key `"submodule"` renamed to `"repo"`
- `external-skills.catalog.json`: removed — content merged into `external-skills.config.yaml`
- Projects must now opt-in to external skills via `"external-skills"` block in `agent-meta.config.yaml`

### Added

- **Two-gate system for external skills:** `approved: true` (meta-maintainer) + `enabled: true` in project config both required
- **`repos` section** in `external-skills.config.yaml`: 1:n relationship to skills, with `pinned_commit` for deterministic versioning
- **`pinned_commit` enforcement:** `sync.py` warns on every sync if submodule deviates from pinned commit
- **`add_skill()`** now auto-pins current commit to `pinned_commit` on registration
- **Project opt-in:** new `"external-skills"` block in `agent-meta.config.yaml` activates approved skills per project
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

In `external-skills.config.yaml`:
- Rename `"submodules"` → `"repos"`, add `"pinned_commit"` to each repo entry
- Rename `"enabled"` → `"approved"` in each skill entry
- Rename `"submodule"` → `"repo"` in each skill entry

In each project's `agent-meta.config.yaml`:
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

- `agent-meta.config.yaml` (self-hosting) — `roles` whitelist added, excludes `docker` + `tester` → 0 warnings on sync
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
- `external-skills.config.yaml` — zentrale Skill-Konfiguration (Modell A): Submodule-URLs + Skill-Mapping + `enabled: true/false` Aktivierung
- `sync.py` — `sync_external_skills()`: generiert `.claude/agents/<role>.md` + kopiert Skill-Dateien nach `.claude/skills/<skill-name>/`
- `sync.py` — `--add-skill <repo-url> --skill-name --source --role [--entry]`: registriert Git Submodule + legt Config-Eintrag an
- CLAUDE.md — vollständiger "External Skills (0-external Layer)"-Abschnitt mit Konzept, Konfigurationsformat, Workflow, Versionierung

### Changed

- CLAUDE.md — "Drei-Schichten-Modell" → "Schichten-Modell" (0-external ergänzt, Override-Reihenfolge aktualisiert)
- CLAUDE.md — Verzeichnisstruktur: `0-external/`, `external/`, `external-skills.config.yaml` dokumentiert
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
