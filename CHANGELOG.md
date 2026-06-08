# Changelog

## [0.57.1] — 2026-06-01

### Fixed

- **COCOPILOT.md typo**: Renamed `COCOPILOT.md` to `COPILOT.md` — fixes broken file reference for Copilot platform.
- **Gemini settings.json not initialized**: Gemini `settings.json` was never created during sync, causing missing configuration in Gemini projects.
- **Gemini orchestrator had zero tools**: Gemini orchestrator agent received an empty tool list, breaking all delegation capabilities.
- **Cross-block matching in conditional stripping**: Prevented false-positive matches when stripping inactive `{{#if}}` blocks across separate template sections.

### Changed

- **use-orchestrator rule shortened**: Reduced from 188 to 29 lines by extracting verbose content to lazy-load `_wf-use-orchestrator.md` file. (#280)
- **Orchestrator template reduced**: Shrunk from 547 to 323 lines (-41%) by extracting workflow details to `_wf-*.md` files.
- **PAL wiring completed**: Moved all provider-specific syntax from generic templates into platform adapter templates — full Provider Abstraction Layer integration. (#278)
- **Orphaned GEMINI.md removed**: Removed stale root-level `GEMINI.md` — Gemini now correctly reads `.gemini/GEMINI.md`.

---

## [0.57.0] — 2026-05-31

### Added

- **Provider Abstraction Layer (PAL)**: 3-layer architecture that eliminates cross-provider syntax leaks and enables clean orchestration across Gemini, Continue, and Copilot. Resolves Issue #277.
  - **Layer 1 — Generic Core**: Provider-agnostic agent templates in `1-generic/` remain strictly universal with zero provider-specific references.
  - **Layer 2 — Platform Adapters**: Provider-specific orchestration patches and syntax normalization in `2-platform/` for Gemini, Continue, and Copilot.
  - **Layer 3 — Bootstrap Engine**: Dynamic provider detection and config injection at sync-time, ensuring each generated agent receives only the tools and syntax valid for its target provider.
- **9 new files**: PAL core modules, provider adapter templates, and bootstrap engine components.
- **Provider-specific patches**: Gemini, Continue, and Copilot orchestration templates with native tool mapping and syntax isolation.
- **HowTo documentation**: Complete PAL setup guide and migration instructions for existing projects.

### Changed

- **5 modified files**: Agent templates updated to use PAL delegation patterns instead of direct provider references.
- **3 config files**: Provider registry, role defaults, and project config schema extended with PAL metadata.
- **2 Python modules**: `sync.py` and `scripts/lib/agents.py` updated for PAL bootstrap injection and provider-aware generation.

### Fixed

- **Cross-provider syntax leaks**: Eliminated provider-specific tool syntax (at-agent, claude -a, define_subagent) from generic templates that previously leaked into non-target provider environments.
- **Gemini/Continue/Copilot orchestration**: Each provider now receives native delegation syntax via platform adapters, fixing broken subagent dispatch in non-Claude environments.

---

## [0.56.0] — 2026-05-29

### Added

- **Checkpointing** (`scripts/lib/checkpoint.py`): Resume long orchestrations after session interruption. Saves the current delegation state and enables resumption without repeating already completed sub-tasks. (Issue #169)
- **Auto-Generated Delegation Table**: The delegation table in generated agents is now automatically created from `config/role-defaults.yaml` (managed block). No more manual maintenance of the routing table needed — new roles appear automatically. (Issue #249)
- **SE-Cascade Runner** (`scripts/run-cascade.py`): Command-line runner for the Systems Engineering cascade on platforms without native subagent dispatch (especially Gemini/Antigravity). Orchestrates the 6-level SE cascade sequentially with state tracking. (Issue #209)

### Changed

- **Worker-Guard tightened**: Orchestrator is now explicitly defined as router-only with ABSOLUTE BAN on self-implementing worker tasks. Any attempt by the orchestrator to write code itself or run tests itself is now blocked by clear anti-recursion rules. (Issue #260)

---

## [0.55.2] — 2026-05-28

### Changed

- **Orchestrator Platform Patches**: Replaced static `agents/2-platform/gemini-orchestrator.md` template with programmatic platform patches in `config.py` (`PLATFORM_ORCHESTRATOR_PATCHES` dict). Extended conditional block handling to support `{{#if}}...{{else}}...{{/if}}` and `{{#unless}}` syntax. Provider isolation set to disabled. (Issue #250)

---

## [0.55.1] — 2026-05-28

### Fixed

- **Orchestrator Agent Task Tool**: Added `Agent` task tool to orchestrator template, enabling proper subagent delegation in provider environments that support it.
- **Provider Tool Whitelists**: Added `Agent` to both Opencode and Claude provider tool whitelists (`config/provider-tools.yaml`), preventing sync warnings when the tool is referenced in agent templates.

---

## [0.55.0] — 2026-05-27

### Added

- **5 Provider Expert Agents**: New expert agents for each supported AI provider — `claude-expert`, `gemini-expert`, `opencode-expert`, `continue-expert`, `copilot-expert`. Each provides provider-specific configuration guidance, best practices, and troubleshooting.
- **1-generic/provider-expert.md**: Base template for provider expert agents with `based-on` composition pattern, enabling platform-specific overrides while maintaining a common expert structure.
- **Orchestrator Expert Routing**: Delegation table extended with expert-agent routing — users requesting provider-specific help are now routed to the matching expert agent.

### Fixed

- **Tool Name Permission Mapping**: Tool names normalized from lowercase to PascalCase across all generated agent frontmatter — fixes incorrect permission mapping in provider environments that expect exact tool name casing.
- **Consistency Checker based-on Detection**: Consistency checker now recognizes and validates `based-on` relationships between `1-generic/` and `2-platform/` agent templates, preventing broken composition chains.

### Changed

- **Expert Template hint Fields**: All provider expert templates now include descriptive `hint` fields in their frontmatter for better agent discovery and routing context.

---

## [0.54.2] — 2026-05-27

### Fixed

- **Stability and Validation**: Minor bugfixes and stability improvements discovered during the release process validation.

---

## [0.54.1] — 2026-05-27

### Fixed

- **Opencode JSON parsing**: Added `opencode.json` as a pure JSON alternative to `opencode.jsonc` to resolve parser warnings in strict JSON environments.

---

## [0.54.0] — 2026-05-27

### Added

- **Effort-Estimator Agent** (`agents/1-generic/effort-estimator.md`): New agent for structured task effort estimation with complexity scoring and time-range prediction. Supports the orchestrator's planning phase before task decomposition. (#246)
- **Outcome Cache** (`scripts/lib/cache.py`): SHA256-based delegation result cache with LRU eviction and configurable TTL. Reduces token costs for recurring orchestrator sub-tasks by caching previous outcomes. (#172)
- **Quality Pipeline Framework** (`scripts/lib/pipelines.py`): Configurable quality pipeline definitions with provider-specific injection. Enables project-level customization of the multi-stage quality flow (code-review → validate → release). (#164)
- **Reflection-Loop Infrastructure** (`scripts/lib/reflection.py`): Generator-Critic pair configuration (e.g., developer ↔ code-reviewer) with max-iterations and pair-enabling per project. Supports iterative quality improvement loops. (#163, #166)
- **Parallel Barrier Runtime** (`scripts/lib/runtime.py`): ThreadPoolExecutor-based barrier implementation for deterministic parallel subagent execution with per-agent and global timeout handling. (#240)
- **Provider Tool Whitelists** (`config/provider-tools.yaml`): Per-provider tool capability declarations. Prevents agents from referencing tools unavailable in their target provider environment. Documents unsupported Gemini tools. (#223, #240)
- **Path-Based Contextual Rules** (`config/rules-presets.yaml`): Rules can now be restricted to specific file paths via glob patterns, enabling context-aware rule activation (e.g., Python rules only for `.py` files). (#226)
- **Critical Rules Footer**: Every generated agent file now receives a critical-rules footer section at the bottom, ensuring essential policies (branch-guard, commit-conventions, provider-agnostic) are always visible. (#225)
- **Few-Shot Orchestration Examples**: Orchestrator template enhanced with concrete few-shot examples for FANOUT, PIPELINE, and PARALLEL_GROUP dispatch patterns. (#224)
- **XML Section Wrapping**: Generated agent files now use XML-tagged sections for key blocks, improving structural machine-parseability while maintaining human readability. (#227)
- **File-Affinity Check**: Parallel task execution now checks file-level conflicts before dispatching, preventing race conditions when multiple agents touch the same files. (#241)
- **Temperature, Steps, Deny-Permissions in Opencode Frontmatter**: Opencode agent generation now supports `temperature`, `steps` (execution step limit), and explicit `deny` permission rules in frontmatter. (#242)

### Changed

- **Orchestrator v3.12.0**: Integrated cache, pipelines, reflection-loops, barrier runtime, Gemini Auto-Handoff protocol, and anti-recursion guard into the delegation workflow. Entry-point hint updated with orchestrator-exclusive dispatch clarification.
- **SE Orchestrator v1.5.0**: Extended 6-level cascade with traceability enhancements and validation integration.
- **SE Requirements v1.5.0**: Enhanced requirements elicitation with improved traceability.
- **agent-meta-manager v1.9.0**: Clarified update-meta vs upgrade-meta commands. Added reflection-loop and quality pipeline configuration sections.

### Fixed

- **Orchestrator Auto-Handoff Clarification**: Prioritized native tool-calls over text-based `@orchestrator` triggering. Clarified `@orchestrator` as the sole direct-dispatch interceptor for all platforms. (#213, #214)
- **Gemini Auto-Handoff Protocol**: Gemini orchestrator now implements the full auto-handoff pattern with explicit planning-mode override, correcting missing functionality. (#208, #243)
- **Anti-Recursion Guard**: Worker agents now explicitly blocked from delegating back to the orchestrator, preventing infinite delegation loops. (#232, #242)
- **Opencode Frontmatter**: Removed invalid `memory` field, corrected `mode` resolution from template YAML instead of hardcoded `subagent`, and completed frontmatter for Continue and Claude/Opencode. (#239, #217, #220)
- **Gemini Agent Frontmatter**: Stripped unsupported config parameters, added proper tool mapping translation for Gemini native tools. (#222, #221)
- **Tool-Specific Placeholders**: Removed provider-tool references from 1-generic templates to maintain provider-agnostic invariance. (#210)
- **Agent Tool Exclusion**: `Agent` tool removed from generic template frontmatter to eliminate sync warnings across providers. (#236, #238)
- **Sync Schema Enums**: Updated enums to match current providers and roles, preventing validation errors. (#234, #237)
- **Bug-Feature-Analyzer**: Excluded from direct dispatch exceptions, enforcing orchestrator routing for issue triage. (#241)
- **Test-Repo Validation**: Parametrized path resolution for out-of-tree test-repository validation, supporting flexible test setups.

---

### Fixed

- **Regenerate all generated files** after orchestrator entry-point sentence fix (PR #231, commit 0225e0e). The fix adds an explicit exceptions reference to the orchestrator entry-point hint to prevent over-delegation for trivial non-development queries.

---

## [0.53.0] — 2026-05-24

### Added

- **`bug-feature-analyzer` agent**: New agent for automated GitHub issue triage and feature analysis. (#219)

### Fixed

- **Orchestrator self-execution guard**: Prevented orchestrator from executing worker tasks directly, enforcing proper delegation protocol.

---

## [0.52.1] — 2026-05-24

### Fixed

- **TOML escaping for Gemini /commands**: Fixed triple-quote escaping in `_md_to_toml()` to prevent invalid TOML when command bodies contain `"""`. (#206)
- **Orchestrator validator references**: Made `validator` agent references in orchestrator template conditional via `{{#if VALIDATOR_ENABLED}}`, preventing routing to non-existent agents in projects without `validator` in roles. (#204)
- **Inline conditional block preservation**: Fixed `strip_inactive_conditional_blocks()` to preserve inline table rows (no trailing newline) when stripping inactive `{{#if}}` blocks, preventing broken Markdown tables. (#196)
- **SE orchestrator schema**: Added `schemas/se-orchestrator.schema.json` for orchestration metadata validation. (#195)

### Changed

- **Orchestrator version**: 3.2.0 → 3.3.0 (conditional validator blocks = scope extension)

---

## [0.52.0] — 2026-05-24

### Added

- **11 new agent templates**: Complete SE right-wing (se-test-engineer, se-testreviewer, se-verifier, se-validator, se-integration-and-test-manager) and SWE agents (code-reviewer, ui-ux-designer, api-specialist, devops-engineer, performance-optimizer, export-manager). (#209)
- **Manual test framework**: Generic black-box test procedure with 15 scenarios (5 SE + 10 meta-agent), including `--dry-run` support, provider detection, auto-generated bug reports, and target-repository testing. (#209)
- **Export configuration**: New `config/export.yaml` for target-agnostic output routing (Markdown, Confluence, Jira-Xray). (#209)
- **Lifecycle hooks integration**: `se-validator` triggered on-release, `code-reviewer` on-merge. (#209)
- **Placeholder skills registry**: Future skill placeholders for mermaid-renderer, figma-reader, postman-collection-generator. (#209)

### Changed

- **Orchestrator routing table**: Extended with all 11 new agents and V&V workflows. (#209)
- **Validator/tester templates**: Refocused validator as process guardian, tester as isolated unit-test writer. (#209)
- **Role defaults**: Added 11 new roles with appropriate model tiers (balanced/powerful/fast). (#209)
- **Project config**: Activated all new SE and V&V roles. (#209)
- **Test restructure**: Moved automated tests to `tests/automated/`, manual tests to `tests/manual/`. (#209)

---

## [0.51.0] — 2026-05-24

### Fixed

- **Provider-agnostic approach for generic templates**: Corrected orchestrator model handling to ensure 1-generic templates remain provider-agnostic. The generic orchestrator no longer references provider-specific model IDs. (#208)

### Added

- **Planning-Mode section in orchestrator**: Added explicit planning-mode guidance for providers that support native planning (Gemini, Opencode), ensuring the orchestrator's planning phase takes precedence over provider-native planning. (#208)
- **Gemini Auto-Handoff protocol**: Gemini orchestrator now supports the same auto-handoff pattern as other providers, with explicit planning-mode override instructions. (#208)
- **New policy rule for generic templates**: Formalized the provider-agnostic policy as a standalone rule, preventing provider names, tool syntax, and API details from leaking into 1-generic templates. (#208)

### Changed

- Various minor corrections and clarifications across agent templates and rules. (#208)

---

## [0.49.0] — 2026-05-22

### Changed

- **Main Session Auto-Handoff Protocol**: Refactored the orchestrator-first architecture to empower the Main Session as a Smart Communication Interface. The Main Session can now read files and analyze context, but automatically delegates the execution to the Orchestrator via a tool call instead of generating a text refusal message.

---

## [0.48.0] — 2026-05-22

- Introduce Orchestrator-First Architecture with FANOUT, PARALLEL_GROUP, and BARRIER patterns for multi-agent orchestration.

---

## [0.47.2-beta] — 2026-05-21

### Added

- **Dry-Run Engine improvements**: Enhanced dry-run engine with German keyword support, word boundary matching, and better FANOUT splitting for more accurate orchestration simulation.

### Changed

- **README.md updated**: Added comprehensive documentation for orchestrator-first architecture v3.0.0 beta features.
- **Version bump**: Upgraded agent-meta to v0.47.0-beta in preparation for this release.

---

## [0.47.0-beta] — 2026-05-21

### Added

- **Orchestrator-First Architecture v3.0.0 (Beta)**: Universal router for all development tasks with task decomposition protocol (FANOUT/PARALLEL_GROUP/BARRIER). The orchestrator becomes the primary entry point, replacing direct main-chat code work.
- **Provider-Agnostic Parallel Execution Engine**: Supports 4 providers (Claude, Opencode, Gemini, Continue) with precise PARALLEL patterns per provider.
- **Unknown Intent Protocol**: Meta-Feedback Loop for unrecognized user intents with configurable fallback behavior.
- **User-Override Mechanism**: Trigger phrases ("Nicht delegieren", "Mach das hier", "Kein Orchestrator", etc.) allow users to bypass the orchestrator and work directly in main chat.
- **Orchestrator Configuration Switch**: Granular `enabled`/`strict`/`unknown-fallback` settings in `project.yaml` with three boolean flags (`meta-feedback`, `main-chat`, `ask-user`).
- **Orchestration Test Infrastructure**: Dry-run engine, fixtures, and test commands for validating orchestration behavior.
- **Trilingual Glossary** (EN/DE/Explanation): Comprehensive terminology reference for the meta-agent framework.

### Changed

- **`use-orchestrator` rule removed from `silent` preset**: Orchestrator usage is now always active, not preset-dependent.
- **Agent templates regenerated** with orchestrator-first architecture.

### Deferred (Phase 2 & 3)

- Phase 2: Selective Rule Embedding, Main Session Thinning
- Phase 3: Result Caching, Dynamic Batching, Agent Pooling
- See Issue #192 for tracking.

---

## [0.46.1] — 2026-05-21

### Fixed

- **Opencode frontmatter schema validation**: Removed `generated-from` field from Opencode agent frontmatter — caused schema validation error (`Extra inputs are not permitted`) in opencode. (#188)

---

## [0.46.2] — 2026-05-21

### Fixed

- **Opencode orchestrator permission mapping**: Added missing permission mapping for subagent task tool in opencode orchestrator agent. (#190)

---

## [0.50.0] — 2026-05-24

### Added

- **Systems Engineering (SE) Agent Cascade**: Introduced a 6-level recursive breakdown model with specialized agents: `se-requirements`, `se-architect`, `se-critic`, `se-interface-mgr`, `se-orchestrator`, and `se-termination`. Enables structured requirements-to-architecture workflows.
- **Requirements Quality Gate**: The `se-critic` agent now validates outputs from `se-requirements` before they are passed to `se-architect`, catching flawed requirements early before architecture work begins.
- **SE Config Integration**: Configuration support for the SE agent cascade, enabling project-specific tuning of the 6-level breakdown process.

---

## [0.47.2-beta] — 2026-05-21

### Added

- **Phase 2: Selective Rule Embedding** (`config/rules-presets.yaml`, `scripts/lib/context.py`, `scripts/lib/rules.py`): Rules can now be excluded from the Opencode managed block with `embed: false`. Excluded rules remain available as separate files (e.g. `.claude/rules/dod-criteria.md`). Default behavior unchanged (`embed: true`). Activated for `dod-criteria` and `sync-interface` in the `silent` preset.

### Changed

- **AGENTS.md thinning**: Main Session managed block reduced from ~580 to ~370 lines (-36%, -210 lines). 2 rules (`dod-criteria`, `sync-interface`) moved from embedded to file-only.
- **`/update-meta` command**: New command for syncing agent-meta without version upgrade.

---

## [0.46.0] — 2026-05-21

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

- **`log-analyzer` agent** (`agents/1-generic/log-analyzer.md`): Analyzes system and application logs with frequency clustering (Bash-based, before LLM analysis), RFC-5424-compliant severity classification (CRITICAL/HIGH/MEDIUM/LOW/INFO), auto-discovery of known log paths (syslog, journald, Docker, Home Assistant, Nginx) and structured finding cards. Two modes: `--quick` (default, token-efficient) and `--deep` (codebase search + online research). Delegation routing to `feedback`, `developer`, `security-auditor` and `requirements`. `workflow_tier: required`.
- **`homeassistant-log-analyzer` platform agent** (`agents/2-platform/homeassistant-log-analyzer.md`): Extends the generic log analyzer via `extends: + patches:` with HA-specific log format, logger-to-component mapping, known error patterns (TemplateError, Platform not ready, MQTT disconnect, ZHA, Recorder), startup noise filter and HA-specific delegation resources (community.home-assistant.io, HACS).
- **`feedback` agent** (`agents/1-generic/feedback.md`): Standardizes bug reports, feature requests and improvement suggestions for the target project as GitHub Issues. Mandatory gate before any direct `git`-based issue creation. Six types (`bug`, `feat`, `improvement`, `docs`, `security`, `question`) with body templates. Auto-repo-detection via `gh repo view`. Clear separation from `meta-feedback` (framework vs. project). `workflow_tier: required`.
- **`/analyze-logs` command** (`commands/1-generic/analyze-logs.md`): Delegates to `log-analyzer` agent. Supports optional path and `--quick`/`--deep` flags. Generated for all active providers (Claude → `.claude/commands/`, Gemini → `.gemini/commands/` (`.toml`), Opencode → `.opencode/commands/`, Continue → `.continue/prompts/`).
- **`/feedback` command** (`commands/1-generic/feedback.md`): Delegates to `feedback` agent. Supports optional type keyword (`bug | feat | improvement | docs | security | question`) and short description as argument. Generated for all active providers.
- **`/report-bug` command updated** (`commands/1-generic/report-bug.md`): Now delegates to `feedback` agent (type `bug` pre-selected) instead of own inline workflow — consistent with the standardized feedback channel.
- **Orchestrator Workflow O + P** (`agents/1-generic/orchestrator.md`): Workflow O (log analysis via `log-analyzer`) and Workflow P (project issue via `feedback → gh issue create`) added. Both new agents listed in the agents table.
- **`consistency-check.py`** (`scripts/consistency-check.py` + `scripts/lib/consistency/`): New Python script for deterministic consistency checking of agent templates, commands and cross-references without LLM calls. Checks: frontmatter version bumps (git-diff-based), semver format, extends/patches anchor resolution, role-defaults completeness, orchestrator table, CHANGELOG mentions, placeholder typos. Exit codes: 0=ok, 1=error, 2=script-error. Flags: `--changed`, `--file`, `--strict`, `--json`, `--root`. Stdlib-only, PyYAML optional.
- **`/consistency-check` command** (`commands/1-generic/consistency-check.md`): Slash command calls the script, interprets findings and offers interactive fixes. Generated for all active providers.
- **`agent-meta-manager` v1.5.0** (`agents/1-generic/agent-meta-manager.md`): New section 8 "Consistency-Check" with full reference, when-to-run table and link to howto.
- **Howto** (`howto/features/consistency-check.md`): Full reference with manual execution, all CLI flags, check catalog, JSON format, GitHub Actions integration and guide for adding new checks.

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

- **Provider-specific model tiers** (`config/ai-providers.yaml`, `config/role-defaults.yaml`, `scripts/lib/roles.py`): Five abstract tiers (`nano`, `fast`, `balanced`, `powerful`, `max`) replace Claude-specific aliases in `role-defaults.yaml`. `sync.py` maps tiers per provider to concrete model IDs — Gemini now receives correct Gemini models instead of invalid Claude aliases.
- **Provider-Tier-Mapping** (`config/ai-providers.yaml`): `model-tiers` and `model-aliases` per provider:
  - Claude: `nano/fast` → `claude-haiku-4-5-20251001` | `balanced` → `claude-sonnet-4-6` | `powerful/max` → `claude-opus-4-7`
  - Gemini: `nano/fast` → `gemini-2.5-flash` | `balanced/powerful/max` → `gemini-2.5-pro`
  - Continue: empty — Continue manages models centrally in `config.yaml`
- **Provider-specific `model-overrides`** (`config/project-config.schema.json`, `scripts/lib/roles.py`): New format `model-overrides.Claude.git: fast` alongside legacy `model-overrides.git: fast`. Provider block takes precedence for the respective provider; legacy block applies only to Claude.
- **Backward compatibility**: `haiku`/`sonnet`/`opus` remain valid as aliases for Claude. For other providers they are mapped to the corresponding tier (`haiku` → `fast`, `sonnet` → `balanced`, `opus` → `powerful`).
- **Concrete `run_in_background` example** (`agents/1-generic/orchestrator.md` v2.5.0): Orchestrator now shows Python code pattern for parallel delegation (foreground + `run_in_background=True`).

### Fixed

- **Gemini agents had invalid `model:` fields** (`scripts/lib/agents.py`): `model: haiku` or `model: sonnet` were written into Gemini frontmatter — Gemini CLI ignores or rejects these. All Gemini agents now receive correct Gemini model IDs.

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

- **HA platform: MCP-Server-Guidelines** (`rules/2-platform/homeassistant-mcp-integration.md`): New section "Local / Project-Specific MCP Servers" — documentation convention for local MCP servers via `platform-config.yaml`, gitignore hints, fallback strategy.
- **HA platform: project.yaml Template** (`howto/configs/project.yaml.homeassistant.example`): HA-specific example without build artifact fields, with YAML/Jinja2 context and HA-typical role whitelist.
- **branch-guard Rule** (`rules/1-generic/branch-guard.md`): Completely revised decision logic with explicit decision tree, "Branch PFLICHT" table and precise exceptions. Working on issues, changing multiple files and running `sync.py` now always require a branch.

### Fixed

- **HA platform: TypeScript conventions** (`agents/2-platform/homeassistant-developer.md` v1.1.0): `delete` patch removes TS-specific rules (Named Exports, kebab-case, `.test.ts`) from HA projects.
- **HA platform: Snippet loading instruction** (`agents/2-platform/homeassistant-developer.md` v1.1.0): `delete` patch prevents loading of `bun-typescript` snippets in YAML-only projects.
- **HA platform: Doc trigger logic** (`agents/2-platform/homeassistant-developer.md` v1.1.0): New section `Documentation Responsibilities` — inline docs (always mandatory) vs. MkDocs (only on explicit request, no auto-spawn).
- **meta-feedback Agent: Context loss on confirmation** (`agents/1-generic/meta-feedback.md` v1.5.0): Agent now creates issues directly after preparation without internal confirmation spawn — new spawn lost context and invented different issues.

---

## [0.27.1] — 2026-04-18

### Added

- **`speech-mode: asozial`**: New communication style — technically correct, New-Kids-style with contempt for the user. `project-config.schema.json` extended with `"asozial"` in enum.

---

## [0.27.0] — 2026-04-18

### Added

- **Commands-System**: New layer model for Claude commands (`commands/1-generic/`, `2-platform/`, `0-external/`). `sync.py` syncs commands to `.claude/commands/` (Claude) and `.continue/prompts/` (Continue).
  - `commands/1-generic/doc-now.md` — first generic command: delegates to `documenter` agent
  - `scripts/lib/commands.py` — sync logic analogous to rules and hooks
  - `config/ai-providers.yaml` — `has_commands: true` for Claude and Continue

---

## [0.26.1] — 2026-04-18

### Fixed

- **Self-Hosting Config Layout**: `config/project.yaml` was simultaneously the framework default directory and self-hosting config — semantically incorrect. The project config for the meta repo itself now correctly resides under `.meta-config/project.yaml` (identical to any other target project).
  - `.meta-config/project.yaml` created with all self-hosting settings
  - `config/project.yaml` replaced with a notice stub (framework defaults remain in `config/`)
  - Auto-Detection: `config/project.yaml` removed from candidate list — only `.meta-config/project.yaml` → legacy fallbacks
  - `sync.py` root detection: `"config"` parent directory special case removed
  - `CLAUDE.md` directory structure: `.meta-config/` block added, `config/project.yaml` documented as stub
  - `.claude/rules/sync-interface.md` auto-detection list updated

---

## [0.26.0] — 2026-04-18

### Added

- **Platform `agent-meta`**: New `platforms: [agent-meta]` in `config/project.yaml` activates 3 new platform-specific rules for the meta repo itself:
  - `rules/2-platform/agent-meta-architecture.md` — layer model, composition syntax, override order
  - `rules/2-platform/agent-meta-conventions.md` — invariants, version bump table, role and placeholder lifecycle
  - `rules/2-platform/agent-meta-sync-interface.md` — sync.py flags, log format, Python module structure
- **`agents/2-platform/agent-meta-developer.md`**: Extended developer agent specifically for the meta repo (extends `1-generic/developer.md`). Added Python-stdlib-only rule, ≤600-line module limit, SyncLog requirement, no `print()` in `lib/`.
- **Rules-Substitution**: `sync_rules()` now applies `substitute()` to rule content — rules receive project-specific variables injected (e.g. `{{DOD_REQ_TRACEABILITY}}`, `{{CODE_LANGUAGE}}`).
- **`rules/1-generic/commit-conventions.md`**: Canonical commit conventions rule for all projects — replaces duplicated tables in agent templates.
- **`rules/1-generic/dod-criteria.md`**: DoD checklist as rule with real project values via variable substitution — each project sees its actually configured DoD features.

### Changed

- **Config-Restructuring**: Framework config now cleanly in `config/` (meta-repo owned); project config in `.meta-config/project.yaml` (project-owned, independent of submodule path and AI provider).
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

- **CLAUDE.md**: Outdated references to `ROLE_MAP in sync.py`, `DOD_DEFAULTS in sync.py`
  and `MANAGED_BLOCK_TEMPLATE in sync.py` corrected — now point to the correct
  files (`roles.config.yaml`, `dod-presets.config.yaml`, `templates/managed-block.md`,
  `scripts/lib/dod.py`).
- **CLAUDE.md**: Directory structure extended with `scripts/lib/`, `templates/` and
  `providers.config.yaml`.
- **howto/sync-concept.md**: Structure updated with new modules.
- **howto/upgrade-guide.md**: `MANAGED_BLOCK_TEMPLATE` → `templates/managed-block.md`.

---

## [0.25.0] — 2026-04-17

### Added

- **`scripts/lib/`** — sync.py split into 13 independent modules (log, io, config,
  roles, dod, platform, providers, agents, rules, hooks, skills, extensions, context).
  Each module is ≤600 lines and individually readable — optimized for LLM-assisted development.
- **`providers.config.yaml`** — `PROVIDER_CONFIG` extracted from sync.py.
  Add a new AI provider (Cursor, Windsurf, ...) without Python code changes.
  Also contains `gitignore_entries` per provider.
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

- **Hooks Layer System** (`hooks/`): Four-layer model analogous to Rules and Agents.
  `sync.py` copies hook scripts from `0-external/`, `1-generic/`, `2-platform/` to `.claude/hooks/`.
  Stale tracking via `.claude/hooks/.agent-meta-managed`.
  Registration in `.claude/settings.json` only on opt-in: `"hooks": {"<name>": {"enabled": true}}`.
  Settings.json is merged on every sync (hooks section) — no longer only created once.
- **`dod-push-check.sh`** (`hooks/1-generic/`): Blocks `git push` when tests are not green.
  Reads `TEST_COMMAND` from `agent-meta.config.yaml` or `$AGENT_META_TEST_COMMAND`.
- **`--create-hook <name>`** in `sync.py`: Creates `.claude/hooks/<name>.sh` as template.
  Project-owned hooks — never overwritten by sync.py.
- **`init_settings_local_json()`** in `sync.py`: Creates `.claude/settings.local.json` skeleton
  on first Claude sync (`--init` or `ai-provider: Claude`). One-time, never overwritten.
- **`howto/hooks.md`** (new): Full documentation of the hooks system —
  layers, sync behavior, dod-push-check configuration, distinction from Rules.
- **`permissionMode`-Injection** in `sync.py`: `resolve_permission_mode()` +
  `inject_permission_mode_field()` — analogous to `model` and `memory`.
  Reads from `roles.config.yaml` (meta default) or `permission-mode-overrides` in
  `agent-meta.config.yaml` (project override).
- **`permission_mode` field in `roles.config.yaml`**: `validator` → `plan`,
  `security-auditor` → `plan`. All other roles empty (default behavior).
- **`permission-mode-overrides`** in `agent-meta.config.yaml`: Projects can override
  individual roles. Valid values: `plan`, `acceptEdits`, `bypassPermissions`, `default`.
- **`agent-meta.schema.json`** (new): Full JSON Schema Draft-07 for
  `agent-meta.config.yaml`. Validates all top-level keys, enum values for
  `model-overrides` (haiku/sonnet/opus), `memory-overrides` (project/local/user),
  `permission-mode-overrides` (plan/acceptEdits/bypassPermissions/default), Hooks, External Skills.
- **Optional Schema Validation** in `sync.py`: When `jsonschema` is installed,
  config errors are output as warnings (graceful fallback when not installed).
- **`howto/agent-isolation.md`** (new): Documentation for `isolation: worktree` —
  when useful, known pitfalls (submodules, merge conflicts, Windows), configuration.
- **`rules/1-generic/issue-lifecycle.md`** (new): First generic rule.
  Reminds all agents to comment on and close GitHub Issues after completion.

### Changed

- **Agent-Descriptions cleaned up**: All `1-generic/*.md` templates had
  "Generic template for the X agent." in `description:` — removed.
  Replaced with concise, one-line descriptions without internal implementation details.
  Takes effect immediately on the Claude Code Agent Picker (after next sync).
- **`git.md`** v1.2.0 → v1.3.0: DoD hooks section + Workflow 7 (close issue after work).
- **`feature.md`** v1.0.0 → v1.1.0: Frontmatter comment with `isolation: worktree` opt-in hint.
- **`CLAUDE.md`**: Hooks system, permissionMode overrides, JSON schema, settings.json behavior,
  settings.local.json init, agent-isolation.md — all new concepts fully documented.
- **`howto/instantiate-project.md`**: `$schema` line added to config template.
- **`agent-meta.config.yaml`** (self-hosting): `$schema` reference added.

### Migration from v0.16.5

No Breaking Changes.

- New files in `.claude/hooks/` are created automatically — no opt-in required.
- `.claude/settings.json` is merged when hooks are activated. Existing files without
  hooks section remain unchanged until a hook is activated.
- `.claude/settings.local.json` is created on next sync (if not present).
- `validator` and `security-auditor` receive `permissionMode: plan` in the generated agent.
  If this is not desired for a project:
  `"permission-mode-overrides": {"validator": "default"}` in `agent-meta.config.yaml`.

---

## [0.16.5] — 2026-04-06

### Added

- **Rules Layer System** (`rules/`): Four-layer model analogous to agents.
  `sync.py` copies rules from `0-external/`, `1-generic/`, `2-platform/` to `.claude/rules/`.
  Platform rules (`<platform>-<name>.md`) override generic rules with the same name.
  Stale tracking via `.claude/rules/.agent-meta-managed` — removes outdated managed rules.
- **`--create-rule <name>`** in `sync.py`: Creates `.claude/rules/<name>.md` as empty template.
  Never overwrites existing files.
- **`howto/rules.md`** (new): Full documentation of the rules system —
  layers, sync behavior, naming convention, distinction from extensions.
- **`CLAUDE.md`**: Rules section added (four-layer model, sync behavior,
  distinction from extensions), update behavior table extended with rules rows,
  directory structure extended with `rules/`.

### Migration from v0.16.4

No Breaking Changes. `sync.py` runs silently when `rules/1-generic/` is empty —
no log entry, no warning.

---

## [0.16.4] — 2026-04-06

### Added

- **`howto/agent-memory.md`** (new): Full documentation of the agent memory system —
  three scopes (`project`, `local`, `user`), configuration via `roles.config.yaml` +
  `memory-overrides`, MEMORY.md structure recommendations, `.gitignore` behavior.
- **`memory:`-Injection in `sync.py`**: `resolve_memory()` + `inject_memory_field()` —
  reads memory scope from `roles.config.yaml` (meta default) or `memory-overrides` in
  `agent-meta.config.yaml` (project override). Injected after `model:` in frontmatter.
- **`memory` field in `roles.config.yaml`**: Memory scope defaults for all roles.
  `validator`, `documenter`, `requirements`, `security-auditor` → `project`;
  `agent-meta-scout` → `local`; all others → empty (no memory).
- **`memory-overrides`** in `agent-meta.config.yaml`: Projects can override individual
  roles. Precedence: project override > meta default > no field.
- **`CLAUDE.md`**: `memory-overrides` section with scopes table and defaults added.

### Migration from v0.16.3

No Breaking Changes — generated agents may receive a new `memory:` field
if `roles.config.yaml` defines a default. To disable: set `"memory-overrides": { "<role>": "" }` in the project config.

---

## [0.16.3] — 2026-04-06

### Changed

- **`roles.config.yaml`** (new): Model defaults extracted from `sync.py` —
  meta maintainer manages roles + recommended models + descriptions centrally in this file.
  `sync.py` reads defaults from there instead of a hardcoded constant.
- **`sync.py`**: `DEFAULT_MODEL_MAP` constant removed → `load_roles_config()` reads
  `roles.config.yaml`; `resolve_model()` takes `agent_meta_root` as parameter.
- **`CLAUDE.md`**: `model-overrides` section points to `roles.config.yaml` instead of sync.py;
  directory tree extended with `roles.config.yaml`.

### Migration from v0.16.2

No Breaking Changes — behavior identical. Model adjustments now in
`roles.config.yaml` instead of `sync.py`.

---

## [0.16.2] — 2026-04-06

### Added

- **Central Model Mapping** (`DEFAULT_MODEL_MAP` in `sync.py`): Meta maintainer manages
  recommended Claude models per role. `sync.py` injects `model:` field during generation.
- **`model-overrides`** in `agent-meta.config.yaml`: Projects can override individual roles.
  Precedence: project override > meta default > no field (inherits from parent).
- **`resolve_model()`** + **`inject_model_field()`** in `sync.py`: new helper functions.
  `inject_model_field()` inserts `model:` after `name:`, overwrites existing values,
  or removes the field when no model is configured (clean output).
- **`[INFO]`-Log** in `sync.log` on model injection: shows set model + source
  (`meta default` vs. `project override`).
- **`agents/1-generic/security-auditor.md`** (v1.0.0-beta): new generic agent for
  static security analysis — OWASP Top 10, Secrets, Dependencies, Supply Chain, Crypto.
  Read-only (no Write/Edit), no alarm fanaticism, clear separation from `validator`/`tester`.

### Changed

- `scripts/sync.py`: `DEFAULT_MODEL_MAP` Konstante + `resolve_model()` + `inject_model_field()`
- `scripts/sync.py`: `sync_agents()` ruft Model-Injection nach `build_frontmatter()` auf
- `CLAUDE.md`: new section `model-overrides` with full defaults table
- `CLAUDE.md`: `roles` whitelist extended with `agent-meta-scout` and `security-auditor`

### Meta-Defaults (injected when no project override)

| Modell | Rollen |
|--------|--------|
| `haiku` | `git`, `meta-feedback`, `docker` |
| `sonnet` | `tester`, `validator`, `documenter`, `security-auditor`, `agent-meta-scout`, `agent-meta-manager`, `release` |
| *(empty)* | `orchestrator`, `developer`, `requirements`, `ideation`, `feature` |

---

## [0.16.1] — 2026-04-06

### Added

- **`agents/1-generic/agent-meta-scout.md`** (v1.0.0): new generic agent — scouts the
  Claude Code ecosystem for new skills, agent roles, rules and workflow patterns.
  Reads `evaluate-repository.md` from the `awesome-claude-code` submodule as evaluation framework.
  Started **exclusively on explicit user request** (no auto-trigger).
- **`external/awesome-claude-code`**: new Git submodule (meta repo with curated Claude skills).
  Pinned to `3d8bde25`. No skill wrapper — used directly by `agent-meta-scout` via Read tool.
- **`external-skills.config.yaml`**: new `repos` entry for `awesome-claude-code`.
- **Orchestrator Workflow M**: "Scout Claude ecosystem" — explicit trigger list,
  `agent-meta-scout` listed in agents table.

### Changed

- `scripts/sync.py`: `ROLE_MAP` extended with `agent-meta-scout`
- `agents/1-generic/orchestrator.md` (v1.6.1 → v1.7.0): Agents table + Workflow M added
- `CLAUDE.md`: Agents table + dependency map extended with `agent-meta-scout`

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
- `howto/sync-concept.md` — sync behavior table expanded; Personal vs. Team table updated with "Created by" column
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
- `CLAUDE_MD_MANAGED_TEMPLATE` — new "Available Agents" section with `{{AGENT_HINTS}}` + orchestrator entry point hint; technical table moved to subsection
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

- New variable `{{USER_INPUT_LANGUAGE}}` — language in which the user gives instructions (Agent-Input), independent of `COMMUNICATION_LANGUAGE` (Agent-Output)
- `howto/agent-meta.config.example.json` — `USER_INPUT_LANGUAGE` added with comment

### Changed

- All 13 agent templates (`+0.0.1` Patch): `USER_INPUT_LANGUAGE` in `## Sprache` section added
  - `1-generic`: orchestrator `1.6.1`, developer `1.4.1`, tester `1.4.1`, validator `1.3.1`, requirements `1.3.1`, documenter `1.3.1`, release `1.3.1`, docker `1.3.1`, git `1.1.1`, meta-feedback `1.3.1`, ideation `1.2.1`
  - `2-platform`: sharkord-release `1.3.1`, sharkord-docker `1.2.1`
  - `0-external`: _skill-wrapper `1.0.1`
- `howto/agent-meta.config.example.json` moved under `howto/` (was previously in repo root)
- All references to `agent-meta.config.example.json` updated: README, CLAUDE.md, ARCHITECTURE.md, howto/*, orchestrator.md
- CLAUDE.md — `COMMUNICATION_LANGUAGE` description refined (end-user output), `USER_INPUT_LANGUAGE` added to variables table

---

## [0.12.1] — 2026-04-04

### Added

- `orchestrator.md` (`1.6.0`) — Workflow L: Process GitHub Issue (read issue → requirements → tester → developer → tester → validator → documenter → git close)
- `git.md` (`1.1.0`) — `gh issue` commands: list, view, close with comment, PR with "Closes #id"

---

## [0.12.0] — 2026-04-04

### Added

- **`1-generic/git.md`** (`1.0.0`) — new Git agent: Commits, Branches, Merges, Tags, Push/Pull, Commit Messages, platform-independent (GitHub, GitLab, Gitea)
- New variables: `{{GIT_PLATFORM}}`, `{{GIT_REMOTE_URL}}`, `{{GIT_MAIN_BRANCH}}`
- `sync.py` ROLE_MAP + CLAUDE.md: `git` role registered

### Changed

- `orchestrator.md` (`1.5.0`) — `git` agent in agents table; Git commits in workflows A/B/E/H1/H2 delegated to `git`; commit conventions section removed (→ `git.md`); DoD item updated
- `release.md` (`1.3.0`) — Release workflow step 5→6 reordered: `git tag` → delegation to `git`; checklist + delegation updated
- `sharkord-release.md` (`1.3.0`) — Step 6 (Commit + Tag + Push) formulated as delegation to `git` agent; checklist updated

---

## [0.11.0] — 2026-04-04

### Added

- **`0-external` Layer** — new agent layer for external skill packages from third-party repos
- `agents/0-external/_skill-wrapper.md` — generic wrapper template: Header + `{{SKILL_CONTENT}}` substitution + lazy `additional_files`
- `external-skills.config.yaml` — central skill configuration (Model A): Submodule URLs + Skill mapping + `enabled: true/false` activation
- `sync.py` — `sync_external_skills()`: generates `.claude/agents/<role>.md` + copies skill files to `.claude/skills/<skill-name>/`
- `sync.py` — `--add-skill <repo-url> --skill-name --source --role [--entry]`: registers Git submodule + creates config entry
- CLAUDE.md — full "External Skills (0-external Layer)" section with concept, configuration format, workflow, versioning

### Changed

- CLAUDE.md — "Three-layer model" → "Layer model" (0-external added, override order updated)
- CLAUDE.md — Directory structure: `0-external/`, `external/`, `external-skills.config.yaml` documented
- CLAUDE.md — Dependency map + change categories extended with External Skills

---

## [0.10.7] — 2026-04-03

### Added

- `snippets/developer/bun-typescript.md` (`1.0.0`) — Imports/Exports, Typing, Error Handling, File Structure, Async for TypeScript/Bun
- `snippets/developer/pytest-python.md` (`1.0.0`) — Python equivalents
- **`{{DEVELOPER_SNIPPETS_PATH}}`** — new variable, points to developer snippet file

### Changed

- `developer.md` (`1.4.0`) — `DEVELOPER_SNIPPETS_PATH` Read instruction integrated into language best practices
- CLAUDE.md — `DEVELOPER_SNIPPETS_PATH` in variables table + snippets table + directory structure
- `agent-meta.config.example.json` — `DEVELOPER_SNIPPETS_PATH` added

---

## [0.10.6] — 2026-04-03

### Added

- **Snippet System** — language-specific code examples extracted to `snippets/<role>/`
- `snippets/tester/bun-typescript.md` (`1.0.0`) — TypeScript/Bun test syntax, naming, assertions
- `snippets/tester/pytest-python.md` (`1.0.0`) — Python/pytest equivalents
- **`{{TESTER_SNIPPETS_PATH}}`** — new variable, points to snippet file (relative to `snippets/`)
- `sync.py` — `sync_snippets()`: copies snippet files to `.claude/snippets/` in target project (respects `--dry-run`, logs version)
- CLAUDE.md — new section "Snippets" with concept, frontmatter, available snippets, guide

### Changed

- `tester.md` (`1.4.0`) — TypeScript code blocks replaced with language-agnostic pseudocode; `{{TESTER_SNIPPETS_PATH}}` Read instruction integrated at 3 locations
- `orchestrator.md` (`1.4.0`) — `py .agent-meta/scripts/sync.py` → `python .agent-meta/scripts/sync.py` (cross-platform)

---

## [0.10.5] — 2026-04-03

### Added

- **`{{CODE_LANGUAGE}}`** — new variable for code-near artifacts: code comments, commit messages, test descriptions, docker-compose comments (Default: `English`)
- **`{{INTERNAL_DOCS_LANGUAGE}}`** — new variable for internal docs: CODEBASE_OVERVIEW, ARCHITECTURE, REQUIREMENTS, conclusions (Default: `German`)

### Changed

- `COMMUNICATION_LANGUAGE` default value: `German` → `English`
- `developer.md` (`1.3.0`) — Code comments + Commit messages → `{{CODE_LANGUAGE}}`
- `docker.md` (`1.3.0`) — docker-compose comments → `{{CODE_LANGUAGE}}`
- `documenter.md` (`1.3.0`) — File table + README-IMPORTANT → `{{DOCS_LANGUAGE}}`/`{{INTERNAL_DOCS_LANGUAGE}}`; language section split
- `meta-feedback.md` (`1.3.0`) — GitHub Issues → `{{DOCS_LANGUAGE}}`
- `tester.md` (`1.3.0`) — Test descriptions → `{{CODE_LANGUAGE}}`
- `requirements.md` (`1.3.0`) — REQUIREMENTS.md → `{{INTERNAL_DOCS_LANGUAGE}}`
- `validator.md` (`1.3.0`) — Reports → `{{INTERNAL_DOCS_LANGUAGE}}`
- `sharkord-docker.md` (`1.2.0`) — Comments → `{{CODE_LANGUAGE}}`, communication → `{{COMMUNICATION_LANGUAGE}}`
- `sharkord-release.md` (`1.2.0`) — Release Notes → `{{DOCS_LANGUAGE}}`, communication → `{{COMMUNICATION_LANGUAGE}}`
- CLAUDE.md — Variables table extended with `CODE_LANGUAGE` + `INTERNAL_DOCS_LANGUAGE`

---

## [0.10.4] — 2026-04-03

### Changed

- All agents — `## Projekt-specific Extension` block compressed from 8 to 1 line (no content loss, ~84 lines saved)
- `tester.md` (`1.2.0`) — Don'ts section: duplicates from "Quality Principles" section removed, replaced with cross-reference
- `developer.md` (`1.2.0`) — "Language Best Practices": explanatory paragraph removed, rule to one line
- `orchestrator.md` (`1.3.0`) — Extension block compressed
- All other 1-generic agents (`1.2.0`) — Extension block compressed
- 2-platform agents (`1.1.0`) — Extension block compressed

---

## [0.10.3] — 2026-04-03

### Added

- **`{{COMMUNICATION_LANGUAGE}}`** — new variable in all agents; controls language of user communication
- **`{{DOCS_LANGUAGE}}`** — new variable in all agents; controls language of documentation files
- **`{{PROJECT_GOAL}}`** — new variable in project context block of all agents (primary goal)
- **`{{PROJECT_LANGUAGES}}`** — new variable in project context block of all agents
- **`{{AGENT_META_REPO}}`** — new variable in `meta-feedback.md`; replaces hardcoded `Popoboxxo/agent-meta`
- `config.example.json` — all new variables added with defaults

### Changed

- `tester.md` (`1.1.0`) — new section "Quality Principles: No Shortcuts": real assertions, realistic test data (no `"foo"`/`"test"`/`123` dummy data), warning about tests that are always green
- `developer.md` (`1.1.0`) — new subsection "Language Best Practices": strictly follow best practices of the used language(s)
- `meta-feedback.md` (`1.1.0`) — `--repo Popoboxxo/agent-meta` replaced with `--repo {{AGENT_META_REPO}}`
- `orchestrator.md` (`1.2.0`) — Language variables + project context extended
- All other 1-generic agents (`1.1.0`) — Language variables + project context extended
- CLAUDE.md — Variables table extended with new variables

---

## [0.10.2] — 2026-04-03

### Fixed

- `orchestrator.md` — version bumped from `1.0.0` to `1.1.0` (was missed at 0.10.1)

### Changed

- Release process in CLAUDE.md — Step 1 "Check agent versions" explicitly added; rule: ask user when unsure

---

## [0.10.1] — 2026-04-03

### Added

- **New Agent `ideation`** (`1-generic/ideation.md`) — Guides the early, fuzzy phase for new projects and features: explore ideas, ask questions, sharpen scope, provide external impulses, structured handover to the Requirements agent
- **Workflow I** in Orchestrator — "Explore new idea / vision" with Ideation → Requirements chain
- **Workflow H** in CLAUDE.md — documents the new Ideation workflow

### Changed

- `orchestrator.md` — `ideation` in agents table + Workflow I; previous Workflow I (meta-feedback) → Workflow K
- CLAUDE.md — `ideation` in agent role tables, names table and dependency map
- `sync.py` ROLE_MAP — `ideation` added

---

## [0.10.0] — 2026-04-03

### Added

- **Agent Versioning** — Every template file now carries `version:` in its frontmatter
- `based-on:` in 2-platform agents — documents the generic base with version (e.g. `1-generic/docker.md@1.0.0`)
- `generated-from:` — automatically written by `sync.py` into generated agents on every sync
- `extract_frontmatter_field()` in `sync.py` — reads any YAML fields from templates
- [howto/agent-versioning.md](howto/agent-versioning.md) — full documentation of the versioning concept

### Changed

- `build_frontmatter()` in `sync.py` — writes `generated-from:` into generated frontmatter; `version` and `based-on` remain unchanged
- `sync_agents()` in `sync.py` — reads `version` from source template and populates `generated-from` automatically
- CLAUDE.md — new section "Agent Versioning", dependency table extended with version notes
- All 1-generic agents start with `version: "1.0.0"`
- All 2-platform agents start with `version: "1.0.0"` and `based-on:`

### Fixed

- `update_extensions()` in `sync.py` — pre-existing `updated += 1` bug (uninitialized variable) removed

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

- `SYSTEM_DEPENDENCIES` — Markdown list of all core dependencies with versions
- `SYSTEM_URLS` — Markdown list of all relevant system URLs
- `EXTRA_PORTS` — Markdown list of additional ports alongside `PRIMARY_PORT`
- `config.example.json` grouped into four clear sections:
  - **Generic** — for every project
  - **Infrastructure** — Docker, Ports, Containers
  - **Platform** — only with `platforms: ["sharkord"]`
  - **Project-specific** — individual values per project
- `CLAUDE.md` — Variables table structured by the same four sections

### Changed

- `sharkord-docker.md` — Placeholder documentation updated, port template generalized

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
