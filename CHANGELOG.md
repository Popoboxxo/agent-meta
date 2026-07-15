# Changelog

## [0.72.0] — 2026-07-15

### Added
- Honcho MCP server integration: persistent cross-session memory for agents (`config/mcp-registry.yaml`, `enabled-by-default: false`)
- Honcho setup guide (`howto/mcp/honcho-setup.md`) with tool reference and activation instructions
- `MCP_HONCHO_URL` secrets template entry (`howto/configs/mcp-secrets.local-template.yaml`)
- Generated MCP rule files: `.claude/rules/mcp-honcho.md`, `.claude/rules/mcp-viz-logger.md`

### Fixed
- MCP rule-file generation for providers without explicit `rules_dir` — Claude provider was silently skipping rule generation (`scripts/lib/mcp.py`)

### Changed
- `dod-push-check.sh`: Config discovery migrated from `agent-meta.config.json` to `.meta-config/project.yaml`; PyYAML dependency replaced with stdlib fallback

## [0.71.2] — 2026-07-14

### Documentation
- docs: reconcile viz-event-schema with emitted events (#345)

## [0.71.1] — 2026-07-13

### Fixed
- viz-server.py: fix missing importlib import (caused startup crash)
- viz-logger.py + admin-server.py: add --root PROJECT_ROOT override so .agent-meta/ submodule paths resolve correctly in target projects
- viz-report.py + live-dashboard.html: fix delegate_out event rendering (events were silently dropped)
- lib/viz.py: fix newline injection (malformed output)

## [0.71.0] — 2026-07-12

### Added
- feat: add tool risk classification section to orchestrator agent

### Fixed
- fix: add provider limits and execution trace isolation to A2A delegation rules

### Documentation
- docs: document instruction bleed risk in platform composition rules
- docs: add best-practice audit report (2026-07) and circuit-breaker/DoD-gate/judge concept patterns

## [0.70.0] — 2026-07-12

### Changed — Token Efficiency (Phase 6)
- **Flat Orchestrator Mode Flags** (`ORCH_MODE_*`): Replaced nested `{{#if}}/{{else}}` blocks with three flat boolean flags (`ORCH_MODE_DISABLED`, `ORCH_MODE_STRICT`, `ORCH_MODE_ADVISORY`) — eliminates nesting-risk in conditional stripping
- **AGENT_HINTS_CLAUDE** (new parameter): `include_table=False` option for providers (like Claude) that inject agent descriptions natively — removes ~1.5 KB duplication
- **hint/description-Deduplication**: Automatic deletion of redundant `hint` field when identical to `description` in agent frontmatter (v220+ in agents.py)
- **Lazy-Loaded Orchestrator Blocks**: SE-Mode, A2A-Protocol, Checkpointing, Quality-Pipelines now loaded from `snippets/orchestrator/` at build-time instead of hardcoded — enables selective disabling via empty variables
- **Backup API Endpoints** (v0.68.0+): Added `/api/backups`, `/api/backups/create`, `/api/backups/restore`, `/api/backups/<archive>` DELETE for config versioning

### Fixed
- **Singleton-Block Injection** for spawn-capable agents only: Singleton constraint now limited to worker agents that can actually spawn (avoiding spurious warnings in non-spawning agents)
- **Submodule Path Fallback**: `.agent-meta/` fallback added to `_list_agent_templates()` for projects using agent-meta as submodule

## [0.68.0] - 2026-07-12

### Added
- **Backup API Endpoints**: Added `GET /api/backups`, `POST /api/backups/create`, `POST /api/backups/restore`, and `DELETE /api/backups/<archive>` endpoints to `admin-server.py`.
- **Backup Configuration**: Added `backup` config block with `retention` settings (`max_backups`, `max_age_days`) to `project.yaml`.
## [0.67.0] - 2026-07-10

### Added
- **Pipeline Match Check auto-generated**: `{{PIPELINE_MATCH_TABLE}}` is now dynamically assembled from `quality_pipelines` signal_keywords in `role-defaults.yaml` — eliminates hardcoded pipeline tables in orchestrator
- **Intent-Routing auto-generated**: `{{INTENT_ROUTING_TABLE}}` is now dynamically assembled from `routing` hints in `role-defaults.yaml` — eliminates hardcoded intent routing in orchestrator
- **`agents/1-generic-modern/` directory**: Phase 1 token-optimization PoC with reference-agent, developer, and orchestrator templates using 6-block XML structure

### Changed
- **Token-Optimierungs-Offensive**: ~200 KB token savings through compression of all agents, rules, and commands across the framework
- **se-orchestrator fully removed**: Agent file, schema, tests, and all documentation references deleted — replaced by `orchestrator (SE-Mode)` nomenclature
- **AGENTS.md streamlined**: Rules-Summary block (89 lines of token overhead) removed from managed block
- **ARCHITECTURE.md reduced to 53 lines**: Detailed architecture moved to `ARCHITECTURE.full.md`
- **49 active roles** (down from 50 after se-orchestrator removal)
- **Documentation references normalized**: 15-file audit updating `se-orchestrator` → `orchestrator (SE-Mode)` or `[deprecated]` across CODEBASE_OVERVIEW, ARCHITECTURE, README, and cascade docs

### Fixed
- **Admin UI section-whitelist expanded**: `_write_project_section` whitelist in `admin-server.py` expanded from 7 to 23 keys — enables saving of `roles`, `orchestrator`, `viz`, `admin-ui`, and provider settings
- **Admin UI key-name corrections**: `workflow_tier` / `permission_mode` key mismatches fixed in `admin-ui.html`
- **Admin UI cleanup**: Removed CSS artifacts and stale se-orchestrator agent cards from `agent-graph.html`
- **Placeholder validation**: `sync.py --validate` reports 0 warnings after full reference normalization

### Removed
- **`se-orchestrator.md`** agent file deleted
- **`se-orchestrator.schema.json`** deleted
- **Legacy SE test scenarios** (SE-01, SE-03, SE-04) removed — replaced by updated manual tests
- **Hardcoded pipeline/intent tables** from orchestrator — now auto-generated from role-defaults.yaml

## [0.66.0-beta.4] - 2026-07-02

### Changed — Token Optimization Phase 2 (Top-10 Compactification)
- **ui-ux-designer**: 12200 → 7907 chars (-35%, 3050 → 1976 tokens) — JSON schema examples replaced with field-table + schema-reference
- **prompt-engineer**: 12658 → 6065 chars (-52%, 3164 → 1516 tokens) — Best-Practices sections consolidated into reference tables
- **code-reviewer**: 11237 → 9351 chars (-17%, 2809 → 2337 tokens) — JSON output schema replaced with field-table
- **export-manager**: 9239 → 5647 chars (-39%, 2309 → 1411 tokens) — Two JSON schemas replaced with field-tables + snippet references
- **performance-optimizer**: 9040 → 6589 chars (-27%, 2260 → 1647 tokens) — JSON output schema + workflow phases consolidated
- **devops-engineer**: 9033 → 6451 chars (-29%, 2258 → 1612 tokens) — Pipeline-YAML + K8s-Manifest + JSON schema replaced with snippet references
- **api-specialist**: 8664 → 6542 chars (-24%, 2166 → 1635 tokens) — OpenAPI-YAML + JSON schema replaced with snippet reference
- **feature**: 8456 → 5698 chars (-33%, 2114 → 1424 tokens) — 8 step-by-step blocks collapsed into single lifecycle table
- **concept-reviewer**: 6978 → 5477 chars (-22%, 1744 → 1369 tokens) — 7 review dimensions + reflection-loop consolidated into tables

### Fixed
- **Dead link cleanup**: Removed references to deleted `_wf-skill-lifecycle.md`, `_wf-claude-review.md`, `_wf-git-ops.md`, `_wf-security-audit.md` in `agent-meta-manager.md`, `git.md`, `security-auditor.md`
- **Provider-agnostic consistency**: All compactifications are pure Markdown reductions — no XML/Modern-format, no provider-specific syntax. All 4 top providers (Claude, Opencode, Gemini, Continue, Copilot) work identically.
- **Placeholder validation**: Added `A2A_MAX_DEPTH`, `FILE_AFFINITY_HINT`, `ANALYSIS_ENABLED`, `SE_MODE_BLOCK`, `A2A_PROTOCOL_BLOCK`, `CHECKPOINTING_BLOCK`, `QUALITY_PIPELINES_BLOCK` to `_BUILTIN_VARS` in `scripts/lib/consistency/placeholders.py` — eliminates 7 false-positive consistency warnings

## [0.66.0-beta.3] - 2026-07-02

### Changed — Token Optimization Phase 1 (Quick-Wins)
- **Orchestrator externalized**: 4 conditional blocks (SE-Mode, A2A-Protocol, Quality-Pipelines, Checkpointing) moved to `snippets/orchestrator/*.md`, reducing orchestrator.md from 35836 → 22878 chars (-36%, 8959 → 5719 tokens).
- **A2A handoff documentation consolidated**: Reduced duplication between orchestrator and reference-agent templates.
- **AGENTS.md managed-block compactified**: Root managed-block trimmed from 669 → 151 lines (-77%) via compact rule summaries (title + 1-sentence summary + path).
- **`_wf-*.md` workflow files deleted**: 9 unused reference files removed, knowledge preserved in agent templates and rules files. See `agents/1-generic/_README.md` for mapping.
- **Compact-Mode default enabled**: `orchestrator.handoff.compact-mode: true` (was `false`) — A2A envelopes use short field names by default.
- **Continue prompt-mode `slim`**: `provider-options.Continue.prompt-mode: slim` (was `full`) — reduces Continue generated prompts to ~80 lines.

### Internal
- New helper `_extract_rule_compact_from_content()` in `scripts/lib/context.py`.
- `_collect_embedded_rules_md()` gained `compact: bool` parameter.
- `_build_opencode_managed_block()` passes `compact=True` for Opencode provider.

---

## [0.66.0-beta.2] - 2026-07-01

### Added
- **Prompt-Modernization PoC**: Modern Mode with 6-block XML structure for agent prompts (`feat/prompt-modernization-poc`)
- **Prompt-mode awareness**: `log`, `admin-server`, `admin-ui` now respect prompt-mode configuration (legacy/hybrid/modern)
- **Admin UI prompt-modes page**: `/project/prompt-modes` page for viewing and managing prompt-mode settings per agent
- **XML-anchor support**: Composition patches can now target XML anchors in Modern-mode templates
- **prompt_mode consistency check**: `consistency-check.py` validates prompt_mode alignment across generated agents
- **Singleton-Constraint injection**: `sync.py` injects Singleton-Constraint block into Worker agent files to prevent recursive spawning
- **A2A anti-re-delegation gates**: Configurable depth-limit, self-handoff rejection, T-size-limit, re-delegation detection (`rules/a2a-delegation-gates.md`)
- **Gate #5 — Singleton-Orchestrator Spawn Rule**: Prevents Workers from spawning additional Orchestrator instances
- **prompt-engineer agent template**: New role for prompt design, review and optimization (#337)

### Fixed
- Prompt-engineer agent template corrections and refinements
- Various minor fixes in prompt-modernization integration

### Changed
- Orchestrator-singleton-guard concept integrated into prompt-modernization-poc branch

### Documentation
- Active concept: prompt-modernization (Phase 1 complete)
- Active concept: singleton-orchestrator moved to `active/`
- Active concept: SE-und-Prompt-Modernisierung moved to `active/`
- Updated CODEBASE_OVERVIEW.md and README.md for prompt-modernization and singleton-guard

---

## [0.65.2] - 2026-06-28

### Fixed
- Orchestrator Singleton Guard (verhindert Rekursion, max Depth 10)
- Tests fuer Singleton-Verhalten ergaenzt

---

## [0.65.1] - 2026-06-22

### Fixed
- Per-provider tier presets: all 5 presets (Cheap/Normal/Advanced/Expensive/Expensive as Hell) now have `providers:` sections for Claude, Gemini and Opencode with correct model IDs
- Opencode model IDs unified with `opencode-go/` prefix; `qwen3.7-plus` replaces `qwen3.6-plus`; `flash-free` removed; aliases cleaned up (`config/ai-providers.yaml`)
- Core bug in `scripts/lib/roles.py` tier resolver: now uses `providers.<name>.tiers` before global fallback — previously all Opencode agents received Claude model IDs
- Admin UI autocomplete performance: per-provider datalists replace a single global list with thousands of entries (Tier Presets + Provider Tier Overrides dialog) (`docs/admin-ui.html`)
- Outdated project-level model overrides: Opencode prefix corrected from `opencode/` to `opencode-go/` (`.meta-config/project.yaml`)

---

## [0.65.0] - 2026-06-22

### Added
- Model discovery from OpenRouter (338 models) and OpenCode Zen/Go (68 models) via keyless APIs
- Model curation system: blacklist, disable, enable states (`config/model-curation.yaml`)
- Registry persistence guard: populated registry preserved on network failure
- Tier presets redesign: direct model-id assignment (`tiers:`) replaces tier-to-tier mapping
- Backward-compatible: old `mapping:` format still resolved
- Project-local tier presets override global ones in `resolve_model`
- OpenCode unified provider: Zen + Go merged, `display-name` field in ai-providers.yaml
- Admin UI: Edit/Save/Cancel flow for pricing, per-model enable/disable/blacklist
- Admin UI: Quick-filter strip (Claude/OpenCode/GitHub/OpenAI/Google) in model dashboard
- Admin UI: Resolved View + Edit Mappings tabs in Tier Presets
- Admin UI: Per-provider datalist filtering in Provider Tier Mappings
- Admin UI: Project Tier Override panel on ai-providers page
- `display-name` field for providers, surfaced in all admin dialogs

### Fixed
- `SyncLog.error` missing method caused `AttributeError` crash in target repos
- `resolve_model` passed `pc` instead of `provider_config` (wrong type, runtime error)
- Tier-preset dropdown fell back to stale hardcoded list with removed SE variants
- Fabricated `OPENCODE_GO_MODELS` replaced with real API data from `opencode.ai/zen/go/v1/models`
- HTTP 403 from OpenCode endpoints fixed with correct `User-Agent` header

### Changed
- `tier-presets.yaml` migrated to new `tiers:` format (all 5 presets)
- OpenCode provider: `Opencode` (Zen) and `OpencodeGo` (Go) merged into single `Opencode`
- Model registry now sourced from live APIs, not hardcoded data

### Removed
- Fabricated hardcoded `OPENCODE_GO_MODELS` list
- `scripts/patch_ui.py` (obsolete one-shot script)
- `Normal (SE)` and `Advanced (SE)` pseudo-presets (SE is now a boolean flag)

---

## [0.64.1] — 2026-06-20

### Added

- **SE_MAX_CELLS and cost_limit_eur variables**: New configuration variables for SE decomposition control — limits cell count and estimated cost per decomposition run.
- **Resilience criterion in se-critic (v1.7.0)**: Fifth evaluation dimension added to SE architectural critique — assesses fault tolerance and recovery capabilities.
- **Design-by-Contract fields in se-interface-mgr (v1.6.0)**: Interface specifications now support preconditions, postconditions, and invariants per DbC methodology.

### Changed

- **se-orchestrator deprecated in role-defaults**: SE cascade implementation stage now routed through main orchestrator (SE-Mode) instead of separate se-orchestrator role.

### Fixed

- **SE-framework consistency**: Aligned config, templates, and documentation — V&V agents marked as implemented, corrected agent count to 14 in concept docs.

---

## [0.64.0] — 2026-06-20

### Added

- **Config audit routine** (`scripts/lib/config_audit.py`): Detects 4 categories of config drift — roles without template, templates without role-default, deprecated roles (auto-fixable), and orphaned pipelines/reflection-pairs.
- **`--audit-config` / `--audit-config --apply` CLI flags**: `--audit-config` reports findings; `--audit-config --apply` auto-fixes deprecated roles by commenting them out in `project.yaml` (idempotent, comment-preserving, reversible).
- **Admin-UI "Config audit" panel**: New panel with REST endpoints `GET /api/config-audit` and `POST /api/config-audit` for interactive audit and apply from the admin interface.
- **End-of-sync audit warnings**: Non-blocking warnings for all 4 audit categories printed at the end of every `sync.py` run.

### Fixed

- **Deprecated agent templates excluded from sync**: Templates with `deprecated: true` frontmatter (e.g. `se-orchestrator`) are no longer generated or listed in any output — central filter applied in `collect_sources`.
- **Config audit false-positive for multi-instance roles**: Roles using `based-on` with multiple instances are no longer incorrectly flagged as missing role-defaults in the audit output.

---

## [0.63.0] — 2026-06-20

### Added

- **3-tier SE developer cascade**: Three new agent roles (`se-junior-developer`, `se-developer`, `se-senior-developer`) implement a tier-based leaf-node strategy with interface discipline — same-level communication only via the next-higher tier; contract-first implementation against `se-interface-mgr` specs.
- **`implementation` stage in SE cascade pipeline**: New pipeline stage inserted after `termination` and before `validation`; `se-orchestrator` routes leaf nodes tier-based depending on interface count and cross-cutting concerns.

### Changed

- **SE cascade pipeline routing**: `se-orchestrator` now dispatches to `se-junior-developer` (0–1 interfaces, trivial), `se-developer` (2–4 interfaces, standard), or `se-senior-developer` (5+ interfaces, boundary-level, security/performance-critical) based on interface complexity.

### Docs

- Updated `07-se-cascade.md` with implementation stage documentation.
- Updated `se-agent-concept.md` with the 3-tier developer model.
- Updated `instantiate-project.md` with new SE developer roles.

---

## [0.62.1] — 2026-06-18

### Fixed

- **SE recursive folder structure**: SE file-based output now uses recursive folder nesting with System/Component designation postfix naming; SE output conventions updated in orchestrator, se-requirements, and se-architect agents.
- **A2A payload.t size limit**: Hard 300-character limit on A2A `payload.t` field to prevent inline prose dumps in agent-to-agent handoff envelopes.

---

## [0.62.0] — 2026-06-18

### Added

- **SE cascade rebuild**: Pipeline von 5 auf 9 Stages erweitert (l0-stakeholder, l1-requirements, l1-architecture, l2-requirements, l2-architecture, l2-interface, l3-requirements, l3-architecture, termination, validation)
- **SE-spec DoD presets**: Drei neue DoD-Presets (spec-optional, spec-driven, spec-certified) mit se-required Feld
- **Configurable SE output directory**: SE/L{n}/{SystemName}/L{n}_{SystemName}_{Requirements|Architecture}.md
- **Component/system designation**: designation-Feld in se-termination Output (ISO terminology)

### Changed

- **SE mode integration**: SE-Mode direkt im normalen Orchestrator via {{#if SE_ENABLED}} — se-orchestrator deprecated
- **Dynamic depth control**: SE_MAX_DEPTH → SE_MIN_DEPTH + SE_MAX_DEPTH (dynamisch)
- **Generic ID prefixes**: REQ-L{n}-NNN / ARCH-L{n}-NNN statt component/sub-system-spezifisch
- **Pipeline validation**: Actionable hints bei fehlenden Rollen

### Removed

- **Strict Stop Rule L3**: Entfernt für flexible Tiefensteuerung

### Fixed

- Issue #323 geschlossen: DoD/SE-Beziehung dokumentiert

---

## [0.61.1] — 2026-06-17

### Fixed

- Add `.agent-meta/` fallback path for admin UI bundle resolution ([#322](https://github.com/Popoboxxo/agent-meta/pull/322), fixes [#321](https://github.com/Popoboxxo/agent-meta/issues/321))

---

## [0.61.0] — 2026-06-16

### Added

- **Admin UI — viz dashboard integration**: new `/viz-dashboard` page embeds the Viz dashboard via iframe; Start/Stop/Restart toggle for Viz and MCP subprocesses via new CSRF-protected routes `POST /api/subserver/{viz|mcp}/{start|stop|restart}`.
- **VizManager lifecycle methods**: `start_viz`, `stop_viz`, `restart_viz`, `start_mcp`, `stop_mcp`, `restart_mcp` in `scripts/admin-server.py`.
- **project.yaml thematic sub-pages**: dedicated editor pages (General, Providers & Platforms, Roles, Orchestrator, Viz & Admin, Model overrides, Advanced/Raw) replace the previous single generic schema editor.
- **Non-destructive section save**: new route `PUT /api/config/project/section` performs read-modify-write deep-merge, preserving unrelated top-level keys.
- **Typo-safe config data sources**: new API routes `GET /api/providers` (with model_tiers and model_aliases per provider), `GET /api/platforms`, and `GET /api/roles` back dropdowns, checkboxes, and multi-selects from real data instead of free-text inputs.
- **Visual model-overrides table editor**: provider → role → provider-specific model dropdown; replaces raw JSON textarea for `model-overrides` config.
- **Views separation in Admin UI**: Dashboard panels explain the Framework Defaults vs. Project Instance Config mental model; `config/*.yaml` (global, read-only) and `.meta-config/project.yaml` (project instance) are now visually distinguished.

### Changed

- **Admin UI navigation**: redundant `/config/project-target` nav entry removed — it pointed to the same file as `/config/project` and is superseded by the new thematic sub-pages.
- **Nested forms replace JSON textareas**: `orchestrator.handoff`/`token-budget` and `provider-options` use structured form inputs rather than raw JSON editing.

### Removed

- **`config/project.yaml`**: deleted 15-line stub file — it was dead configuration never read by `sync.py`; the canonical project config lives at `.meta-config/project.yaml`.

---

## [0.60.0] — 2026-06-15

### Added

- **Integrations Framework Concept**: new concept document (`docs/concepts/integrations-framework.md`) defining the semble-reference integration model — provider-agnostic integration patterns for external skill connectors.
- **Replacement commands**: `admin.md`, `checkpoint.md`, `analysis.md`, `open-docs.md` replace the former `viz-*` command suite — purpose-built commands for admin UI lifecycle, orchestrator session management, AST dependency analysis, and documentation browser.
- **Admin UI — target-repo view**: super-admin mode now exposes the meta-repo's own `.meta-config/project.yaml` as a "Target repo" section with a dedicated sidebar nav item (`/config/project-target`).
- **Unified admin server entry-point**: `admin-server.py` becomes the single entry-point starting Viz dashboard and MCP SSE server as supervised subprocesses; `--no-viz` flag for lightweight / CI use; `/api/subserver-status` endpoint.
- **A2A handoff schema**: complete schema with `timeout_seconds` and `escalation` fields; `delegation.a2a_envelope` boolean in `project-config.schema.json` for per-project opt-in.
- **max_tokens support**: Claude provider now supports `max_tokens` injection and corrected temperature handling (`scripts/lib/agents.py`, `scripts/lib/roles.py`).
- **Commands howto**: `howto/features/commands.md` documents the full Commands System (REQ-CMD-09).
- **GitHub Actions validation pipeline**: `.github/workflows/validate.yml` — CI workflow validating generated files on every push.

### Fixed

- **PAL delegation engine gaps**: documented build-time vs runtime placeholder split; added schema-awareness (`get_schema_ref()`, `validate_envelope()` with graceful degradation); added Agent Return Format section (`STATUS/RESULT/ARTIFACTS/ERRORS`) to orchestrator (v3.29.0).
- **Shell injection in dod-push-check.sh**: replaced `eval` with `bash -c` to prevent injection.
- **Orchestrator-first rule missing for Gemini**: generic orchestrator-first rule now enforced on Gemini platform.
- **PyYAML missing — graceful fallback**: `reflection.py` and `setup.py` now print a clear actionable error and exit cleanly instead of raising `ImportError` traceback.

### Changed

- **viz-* commands removed**: `viz-mindmap.md`, `viz-report.md`, `viz-toggle.md`, `viz-watch.md` replaced by the four purpose-built commands above.
- **Orchestrator extended**: `use-orchestrator.md` rule expanded with Main-Chat-Modus section; orchestrator agent gains full `checkpoint`, `analysis`, and `open-docs` awareness.

---

## [0.59.0] — 2026-06-15

### Added

- **Admin UI**: new single-file web frontend (`docs/admin-ui.html`) with Vanilla JS and dark theme — zero dependencies, browser-native editor.
- **Admin Server** (`scripts/admin-server.py`): stdlib HTTP server for config read/write operations, sync.py integration, SSE live events — no external dependencies.
- **Complete Admin Roadmap**: all 6 phases implemented in a single release:
  - Phase 1: Static viewer for current agent-meta state
  - Phase 2: Edit and validate configuration changes inline
  - Phase 3: Role drag-and-drop with delegation graph visualization
  - Phase 4: Pipeline builder for orchestrator workflows
  - Phase 5: Super-admin editors for skills, MCP, DoD, delegation rules, export targets, role-defaults, AI providers, and agent templates
  - Phase 6: Live-sync watcher for real-time configuration updates
- **Security hardening**: loopback-only binding, CSRF/Origin validation, no innerHTML sinks, atomic writes with backup.
- **Admin CLI flags**: `sync.py --admin`, `sync.py --admin-only`, `sync.py --admin-port` for flexible deployment.
- **Test coverage**: 24 unit tests for admin-server with full integration coverage.

---

## [0.58.0] — 2026-06-14

### Added

- **Framework-wide conditional A2A (token optimization)**: the A2A Handoff Protocol is now gated behind `A2A_PROTOCOL_ENABLED` across **all** agents (orchestrator, developer, junior/senior-developer, validator, feature, ideation) — not just the orchestrator. When `orchestrator.handoff.protocol` is `none`/`false`, no generated agent mentions envelopes, `handoff_id`, or `payload` anymore. The per-agent A2A sections were also compacted (e.g. developer 216 → 182 lines, feature 305 → 267, ideation 203 → 174), so even with A2A **on** the agents are leaner. Per-provider verified across all 5 providers: with A2A off the orchestrator drops ~18% (e.g. Claude 481 → 394 lines) while native delegation syntax stays intact.
- **Conditional orchestrator sections (token optimization)**: the A2A Handoff Protocol (~90 lines), Outcome Caching, and Checkpointing sections are now generated only when actually enabled. New flags `A2A_PROTOCOL_ENABLED` (from `orchestrator.handoff.protocol`; disable via `none`/`false`) and `CHECKPOINTING_ENABLED` (disable via `orchestrator.checkpointing: false`) gate them. The delegation context format (`TASK`/`CONTEXT`/`CONSTRAINTS`/`EXPECTED_OUTPUT`) was lifted out of the A2A block so structured context survives even when A2A is off.
- **3-tier developer system**: new roles `junior-developer` (tier `fast` — trivial, tightly-scoped changes with a structured ESCALATE protocol) and `senior-developer` (tier `max`, project memory — architecture impact, cross-cutting refactorings, hard bugs, DECISION notes). The orchestrator routes by difficulty and handles escalations without a user round-trip; active only when both roles are enabled (`DEVELOPER_TIERS_ENABLED`).
- **PAL conditionals**: `{{#if PAL_*}}...{{/if}}` blocks are now evaluated per provider by the DelegationSyntaxEngine (e.g. the orchestrator Tools section appears only for providers with `tool_preamble: true`).
- **PAL diagnostics**: missing or unknown PAL placeholder definitions now produce sync warnings instead of being silently removed.
- **Gemini registration notice**: every generated `.gemini/agents/*.md` starts with a note that the agent must be registered via `define_subagent` (Gemini is API-registered, not file-discovered).
- **SE export adapter** (`scripts/lib/se_export/`, CLI `scripts/se-export.py`): Markdown output (default) and GitHub Issues (Phase 2 config), with tests.
- **Orchestrator token-budget tracking** (`orchestrator.handoff.token-budget`, default 10 % session overhead cap).
- **CI workflow** (`.github/workflows/orchestration-test.yml`): orchestration/runtime tests and template validation.

### Fixed

- **A2A protocol leaked when disabled**: `{{PAL_HANDOFF}}` emitted the full A2A envelope protocol in the orchestrator's Parallel Execution Engine even when `A2A_PROTOCOL_ENABLED` was false — now gated. The developer-tier escalation protocol also referenced `payload.ctx`/`trace_parent`/`handoff_id` unconditionally; it is now phrased protocol-neutrally with the A2A-specific parts conditional.
- **Orchestrator Tools section leaked to all providers**: the generic conditional cleanup stripped `{{#if PAL_TOOL_PREAMBLE}}` markers before the PAL engine could evaluate them — PAL substitution now runs first.
- **Provider names in generic orchestrator**: the Provider-Transport table (Claude/Gemini/... names) violated the provider-agnostic policy — replaced with abstract transport wording (orchestrator 3.21.0).
- **PAL replacement corruption risk**: replacement strings containing backslash sequences are no longer interpreted as regex group references.
- **UnicodeEncodeError on Windows consoles**: sync.py crashed when printing the sync report on cp1252 terminals — stdout/stderr are now forced to UTF-8.
- **opencode.json JSONC parsing**: trailing commas and BOM in JSONC settings files broke parsing, silently skipping MCP injection and provider isolation. Shared lenient reader now lives in `lib/io.py`.
- **Scalar template variables**: YAML scalars (`true`, `20`) in `variables:` crashed substitution with TypeError — values are now coerced to template strings (`"true"`/`"false"` for booleans).
- **Schema gaps**: 5 provider-expert roles (`claude-expert`, `gemini-expert`, `opencode-expert`, `continue-expert`, `copilot-expert`) and the `Copilot` provider were missing from `project-config.schema.json`, producing false validation warnings.
- **Consistency-check false positives**: placeholder checker now knows all `build_variables()` built-ins (orchestrator flags, generated tables) and the dynamic `PAL_*` / `PIPELINE_*_BLOCK` families; orchestrator-table check now finds roles that share a table cell.

### Changed

- **All ~41 generic agent templates condensed**: removed redundancy and dead weight (−1077 source lines); `xml-section-wrapping`, `critical-rules-footer`, and `viz.server` disabled in project.yaml — slimmer generated agents.
- **Concept documents**: verified implementation status annotated; central `CONCEPT_INVENTORY.md` removed.
- **Deduplicated sync warnings**: identical warnings (one per provider) are now reported once.
- **Claude provider switch**: project config moved from Gemini/Opencode to Claude-only output — `.claude/` regenerated (including the `doc-now` and `report-bug` commands), `.gemini/` removed.

---

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

- **Checkpointing** (`scripts/lib/checkpoint.py`): Resume langer Orchestrierungen nach Session-Unterbrechung. Speichert den aktuellen Delegation-State und ermöglicht Wiederaufnahme ohne Wiederholung bereits abgeschlossener Sub-Tasks. (Issue #169)
- **Auto-Generated Delegation Table**: Die Delegationstabelle in generierten Agenten wird jetzt automatisch aus `config/role-defaults.yaml` erzeugt (managed block). Keine manuelle Pflege der Routing-Tabelle mehr nötig — neue Rollen erscheinen automatisch. (Issue #249)
- **SE-Cascade Runner** (`scripts/run-cascade.py`): Kommandozeilen-Runner für die Systems-Engineering-Cascade auf Plattformen ohne natives Subagent-Dispatch (insb. Gemini/Antigravity). Orchestriert die 6-level SE-Kaskade sequentiell mit State-Tracking. (Issue #209)

### Changed

- **Worker-Guard verschärft**: Orchestrator ist jetzt explizit als Router-Only definiert mit ABSOLUTEM VERBOT gegen Selbst-Implementierung von Worker-Aufgaben. Jeder Versuch des Orchestrators, Code selbst zu schreiben oder Tests selbst auszuführen, wird jetzt durch klare Anti-Recursion-Regeln blockiert. (Issue #260)

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
