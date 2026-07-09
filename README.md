# agent-meta

[![Version](https://img.shields.io/badge/version-0.66.0-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.x-green.svg)]()
[![License](https://img.shields.io/badge/license-MIT-gray.svg)]()

> Standardized AI agent templates with multi-provider support, orchestrator-first architecture, and Systems Engineering cascade.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
   - [A2A Handoff Protocol](#a2a-handoff-protocol)
- [Agent Roster](#agent-roster)
- [Quick Start](#quick-start)
- [Setup](#setup)
- [Repository Structure](#repository-structure)
- [Configuration](#configuration)
- [Workflows](#workflows)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Multi-Provider Support:** Claude (VS Code), Gemini (VS Code/Antigravity), Opencode, Continue, GitHub Copilot — define once in generic templates, generate per provider via `sync.py`.
- **Provider Abstraction Layer (PAL):** Syntactic isolation between generic templates and provider-specific delegation syntax. Abstract placeholders (`{{PAL_DELEGATE}}`, `{{PAL_FANOUT}}`, `{{PAL_PARALLEL_GROUP}}`, `{{PAL_FALLBACK}}`, `{{PAL_TOOL_PREAMBLE}}`) are resolved at sync-time via `DelegationSyntaxEngine` using `config/delegation-syntax.yaml`. A capability matrix (`config/provider-capabilities.yaml`) drives conditional logic. Provider bootstrap mechanisms (`config/provider-bootstrap.yaml` + `scripts/lib/bootstrap.py`) handle Gemini's `define_subagent` API calls and Continue's config.yaml updates.
- **Layer Architecture:** `1-generic/` (universal, provider-agnostic) → `2-platform/` (platform-specific overrides) → `0-external/` (external skill agents via Git submodules).
- **Orchestrator-First:** Every development task flows through the orchestrator, which decomposes complex tasks into sub-tasks with FANOUT, PARALLEL_GROUP, BARRIER, PIPELINE, and LIFECYCLE dispatch patterns.
- **Systems Engineering Cascade:** A recursive 6-level (L1–L3) model-based system decomposition with dedicated agents for requirements, architecture, critique, interface management, termination, verification, and validation.
- **Provider Expert Agents:** Five dedicated expert agents (Claude, Gemini, Opencode, Continue, Copilot) for provider-specific configuration guidance, best practices, and troubleshooting.
- **Agent Visualization with MCP Logging:** Static Mermaid mindmap + interactive HTML graph + dynamic session event tracking (Gantt, sequence diagrams) via MCP server with CLI fallback, cross-process file locking, and handshake-based delegation tracking.
- **MCP Server Management:** Global server registry, per-project activation, automatic provider config generation with secret scanning and `.gitignore` management.
- **Provider Isolation:** Hard-blocks between provider directories to prevent cross-provider contamination during sync.
- **Extension System:** Managed blocks + project-specific extension files (`3-project/<prefix>-<role>-ext.md`) that add project knowledge without touching generated files.
- **External Skills:** Git submodule-based third-party agent integration with approval gating and skill wrappers.
- **Quality Pipeline Framework:** Configurable multi-stage quality pipelines (code-review → validate → release) with provider-specific injection.
- **Reflection Loops:** Generator-Critic pair configuration (e.g., developer ↔ code-reviewer) with max-iterations for iterative quality improvement.
- **Outcome Cache:** SHA256-based delegation result cache with LRU eviction and configurable TTL to reduce token costs for recurring orchestrator sub-tasks.
- **Parallel Barrier Runtime:** ThreadPoolExecutor-based barrier for deterministic parallel subagent execution with per-agent and global timeout handling.
- **Speech Modes:** `full`, `short`, `childish`, `caveman`, `asozial`, `submissive` — configurable communication styles.
- **Lifecycle Triggers:** `on-release` and `on-merge` hooks that automatically dispatch tasks (e.g., validation, code review) after Git events.
- **DoD Presets:** `rapid-prototyping`, `strict`, `enterprise` — configurable quality profiles controlling REQ traceability, tests, codebase overview, and security audit.
- **Config-Driven Generation:** All configuration lives in `config/` (role defaults, DoD presets, MCP registry, AI providers, skills registry) — `sync.py` reads and generates everything.
- **Versioned Templates:** Every agent template carries a semantic version in its frontmatter; platform agents track their base version.
- **AI Provider Tier Routing:** Five abstract model tiers (`nano`, `fast`, `balanced`, `powerful`, `max`) are mapped per provider to concrete model IDs — cost-efficient model selection.
- **Dynamic Model Discovery:** Keyless API fetching from OpenRouter (338 models), OpenCode Zen (48 models), and OpenCode Go — cached in `config/generated/model-registry.json` with network-outage resilience.
- **Model Curation:** Hard-block (blacklist) and soft-hide (disabled) models via `config/model-curation.yaml` — single source of truth for model visibility.
- **Tier-Presets Matrix:** Dynamically resolve model IDs based on provider, preset (cheap, normal, advanced, expensive), and tier — direct `tiers.tier: model_id` format with backward-compat `mapping:` fallback.
- **Admin UI Overhaul:** Interactive dashboard for Models & Pricing, Provider Tier Mappings, Tier Presets (Resolved View + Edit tabs), Quick-Filter strips, Enable/Disable/Blacklist buttons, pricing source badges (`[API]`, `[Overlay]`, `[Calc]`).
- **Admin UI CRUD Endpoints (v0.66.0):** Full CRUD for Quality Pipelines, Reflection Pairs (generator-critic), and Prompt Modes per role — all with idempotent atomic writes and automatic backups.
- **Admin UI Model Mapping (v0.66.0):** Read-only matrix view showing resolved model IDs per role and provider with source annotation (`role-default` / `explicit-override`). Uses the same resolution logic as `sync.py`.
- **Agent Composition:** Platform and project agents can extend generic templates via `extends:` + `patches:` (append, replace, delete, append-after) — no full copies needed.
- **Consistency Checking:** Built-in `consistency-check.py` for deterministic validation of frontmatter versions, semver format, cross-references, and placeholder integrity.
- **Provider Tool Whitelists:** Per-provider tool capability declarations prevent agents from referencing tools unavailable in their target provider environment.
- **Few-Shot Orchestration Examples:** Orchestrator template includes concrete examples for FANOUT, PIPELINE, and PARALLEL_GROUP dispatch patterns.
- **Critical Rules Footer:** Every generated agent file receives a critical-rules footer ensuring essential policies are always visible.

## Architecture

### Layer Override Chain

```
0-external/   → External skill agents (Git submodules, approved/unapproved)
     ↓
1-generic/    → Universal provider-agnostic templates (always generated)
     ↓
2-platform/   → Platform-specific overrides (composition or full replacement)
     ↓
3-project/    → Project-specific extensions (<role>.md or <role>-ext.md)
```

### Config-Driven Generation

```
config/role-defaults.yaml
config/dod-presets.yaml
config/ai-providers.yaml
config/skills-registry.yaml
config/mcp-registry.yaml
         ↓
    sync.py
         ↓
.claude/agents/  |  .gemini/agents/  |  .opencode/agents/  |  .continue/agents/
```

### Provider Abstraction Layer (PAL)

PAL isolates generic agent templates from provider-specific delegation syntax, preventing "syntax leaks" into wrong provider targets.

```
config/delegation-syntax.yaml
config/provider-capabilities.yaml
config/provider-bootstrap.yaml
          ↓
   PAL Engine (delegation_syntax.py + bootstrap.py)
          ↓
     sync.py
          ↓
.claude/agents/  |  .gemini/agents/  |  .opencode/agents/  |  .continue/agents/
```

| Placeholder | Meaning | Claude | Opencode | Gemini | Continue | Copilot |
|-------------|---------|--------|----------|--------|----------|---------|
| `{{PAL_DELEGATE}}` | Agent dispatch syntax | `Agent(subagent_type=...)` | `task(subagent_type=...)` | Text: "Rufe den **X-Agenten** auf" | `@agent task` | `@agent Führe aus: task` |
| `{{PAL_FANOUT}}` | Parallel same-type agents | Multi-call in one response | Multiple `task()` in one response | Text instruction | Sequential (no parallel) | Sequential |
| `{{PAL_PARALLEL_GROUP}}` | Parallel different agents | Foreground + background calls | Foreground + `task()` | Text instruction | Sequential | Sequential |
| `{{PAL_FALLBACK}}` | Fallback when tools unavailable | "Delegiere an Orchestrator" | `@orchestrator task` | "Bearbeite selbst" | `@orchestrator task` | "Bearbeite: task" |

**Bootstrap Mechanisms:**

| Provider | Mechanism | Description |
|----------|-----------|-------------|
| Claude, Opencode, Copilot | file-based | Agents auto-loaded from directory at context start |
| Gemini | api-based | `define_subagent` API call required at every session start |
| Continue | config-based | `sync.py` writes agent entries into `.continue/config.yaml` |
```

### Model Discovery & Dynamic Tier Resolution

agent-meta v0.65.0 introduces **keyless model discovery** — automatically fetch and cache real models from public AI provider APIs without needing API keys:

```bash
# Fetch latest models from OpenRouter, OpenCode Zen, and OpenCode Go
python scripts/sync.py --update-models
```

**Architecture:**
- **OpenRouter:** Keyless API at `https://openrouter.ai/api/v1/models` → 338 models with live pricing
- **OpenCode Zen:** Keyless endpoint `https://opencode.ai/zen/v1/models` → 48 models (nano-powerful tier)
- **OpenCode Go:** Keyless endpoint `https://opencode.ai/zen/go/v1/models` → max-tier models (e.g. kimi-k2.7-code)
- **Registry Guard:** If discovery returns <10 models (network outage), preserves existing registry
- **Model Curation:** `config/model-curation.yaml` blacklist (hard exclusion) and disabled (soft-hide in UI)

**Tier-Presets (Direct Model Assignment):**
```yaml
# config/tier-presets.yaml — new format (REQ-MOD-01)
cheap:
  tiers:
    nano: openai/gpt-4-mini
    fast: openrouter/mistral/mistral-7b
    balanced: anthropic/claude-3-haiku
    powerful: anthropic/claude-3.5-sonnet
    max: anthropic/claude-opus
```

**Admin UI Enhancement:**
- Models & Pricing: 400+ model table with quick-filter strips (Claude/OpenCode/GitHub/OpenAI/Google)
- Provider Tier Mappings: Datalist-filtered model picker per provider
- Tier Presets: Resolved view (current state) + edit mappings (direct input)
- Price badges: `[API]` (OpenRouter live), `[Overlay]` (manual), `[Calc]` (derived)
- CRUD endpoints: Quality Pipelines, Reflection Pairs, Prompt Modes
- Model Mapping: Read-only role×provider matrix with resolution sources

→ Full details: `scripts/lib/model_discovery.py`, `scripts/lib/curation.py`, `config/model-curation.yaml`, `config/tier-presets.yaml`
→ Admin UI usage guide: `docs/admin-ui-guide.md`

### A2A Handoff Protocol

A standardized JSON envelope for Agent-to-Agent communication with schema validation, supersession tracking, and batch FANOUT — replacing natural-language prompts between agents with structured data contracts.

This is a separate concept from the viz-handshake (Operational Layer). A2A operates as the **Data Contract Layer** — loose coupling via `trace_context.viz_task_id`.

```
Envelope (handoff_id, schema_ref, payload)
      ↓
Schema Validation (against JSON Schema Draft-07)
      ↓
Provider Adaptation (json → yaml_text_block for Continue/Copilot)
      ↓
Delivery via PAL_DELEGATE / PAL_HANDOFF
```

#### Key Features

- **Structured Envelopes** instead of natural language: `handoff_id`, `source_agent`, `target_agent`, `payload` — machine-validatable, token-efficient (~60 tokens overhead)
- **TaskSpec Core + 4 Extensions** cover 84% of agent routes (Ideation, Design, API, Review + SE Decomposition)
- **Batch-Mode** saves 56% envelope overhead on FANOUT: 3 tasks in one envelope vs 3 separate (~70 vs ~180 tokens)
- **Supersession-Tracking** for iteration histories (e.g., Critic review loops): full revision chain via `history[]` array
- **Human-in-the-Loop Gates** with `requires_human_approval` flag for critical delegations

#### Provider Transport Matrix

| Provider | structured_handoff | handoff_format | Envelope Transport |
|----------|-------------------|----------------|--------------------|
| Claude | `true` | `json` | JSON in Task-Tool-Prompt |
| Opencode | `true` | `json` | JSON in task()-Prompt |
| Gemini | `true` | `json` | JSON in define_subagent-Prompt |
| Continue | `false` | `yaml_text_block` | YAML block in prompt text |
| Copilot | `false` | `yaml_text_block` | YAML block in prompt text |

#### Handoff Contracts per Role

Each agent role declares its handoff contracts in `config/role-defaults.yaml` — what it consumes (`input_contracts`) and produces (`output_contract`). 16 roles have handoff contracts configured (orchestrator, developer, requirements, ideation, feature, tester, validator, code-reviewer, ui-ux-designer, api-specialist, and 6 SE agents).

→ Full spec: `docs/concepts/a2a-handoff-protocol.md`
→ Envelope schema: `schemas/a2a-handoff.schema.json`
→ TaskSpec + Extensions: `schemas/handoffs/task-spec.schema.json`, `schemas/handoffs/ext/*.schema.json`

### Orchestrator Dispatch Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| **FANOUT** | N instances of same agent type in parallel | 3× `developer` for 3 bugfixes |
| **PARALLEL_GROUP** | Different agent types simultaneously | `developer` ∥ `tester` |
| **BARRIER** | Wait for all parallel tasks before proceeding | Collect results from FANOUT |
| **PIPELINE** | Sequential steps with dependencies | requirements → dev → test |
| **LIFECYCLE** | Complete end-to-end feature workflow | Branch → REQ → TDD → Dev → Validate → PR |

**Orchestrator Robustness:**
- Recognizes `main_chat` as a valid HITL (Human-in-the-Loop) proxy for approval gates, preventing confirmation deadlocks in multi-agent workflows.
- Actively collects parallel subagent results via BARRIER, ensuring deterministic result ordering and timeout resilience.
- Propagates delegation trace context (`viz_task_id`) to enable cross-agent session tracking and visualization.

### Provider Generation Matrix

| Provider | Agents | Rules | Commands | Config |
|----------|--------|-------|----------|--------|
| Claude (VS Code) | `.claude/agents/` | `.claude/rules/` | `.claude/commands/` | `.claude/settings.json` |
| Gemini (VS Code/Antigravity) | `.gemini/agents/` | `.gemini/rules/` | `.gemini/commands/` (TOML) | `.gemini/settings.json` |
| Opencode | `.opencode/agents/` | Embedded in AGENTS.md | `.opencode/commands/` | `opencode.json` |
| Continue | `.continue/agents/` | `.continue/rules/` | `.continue/prompts/` | `.continue/config.yaml` |
| GitHub Copilot | `.github/copilot/agents/` | `.github/copilot/rules/` | `.github/copilot/commands/` | `.github/copilot/copilot.json` |

### Layer Agent Composition

Platform-specific (`2-platform/`) and project-specific (`3-project/`) agents can extend generic templates:

```yaml
extends: "1-generic/<role>.md"
patches:
  - op: append-after
    anchor: "## Some Section"
    content: "## Additional Content..."
  - op: replace
    anchor: "## Section"
    content: "## Replaced Content..."
  - op: delete
    anchor: "## Section"
  - op: append
    content: "## Appended Content..."
```

## Agent Roster

### Generic Agents

| Agent | Tier | Description |
|-------|------|-------------|
| **orchestrator** | balanced | Entry point for ALL development tasks — decomposes, parallelizes, delegates with FANOUT/PARALLEL_GROUP/PIPELINE |
| **developer** | powerful | Feature implementation and bugfixes |
| **tester** | balanced | TDD, test suite execution, coverage per REQ-ID |
| **validator** | balanced | DoD checklist, REQ traceability audit, code quality gate |
| **requirements** | balanced | Capture requirements, assign REQ-IDs, maintain REQUIREMENTS.md |
| **documenter** | fast | Maintain CODEBASE_OVERVIEW, ARCHITECTURE, README, session conclusions |
| **effort-estimator** | fast | Structured task effort estimation with complexity scoring and time-range prediction |
| **feature** | — | Full feature lifecycle sub-agent: Branch → REQ → TDD → Dev → Validate → PR |
| **ideation** | — | Explore new ideas, sharpen vision, structured handoff to requirements |
| **git** | fast | All Git operations: commits, branches, tags, push/pull, GitHub issues/PRs |
| **release** | balanced | Versioning, changelog, build artifact, GitHub release |
| **feedback** | fast | Standardized bug/feature/improvement reports as GitHub issues |
| **meta-feedback** | fast | Improvement suggestions for agent-meta framework as GitHub issues |
| **agent-meta-manager** | balanced | Manage agent-meta: upgrade, sync, extensions, project agents |
| **agent-meta-scout** | balanced | Scout AI ecosystem for new skills, roles, rules, and patterns |
| **log-analyzer** | balanced | Log analysis with frequency clustering, RFC 5424 severity classification, root-cause hypotheses |
| **export-manager** | fast | Target-agnostic output routing: Markdown, Confluence, Jira-Xray, Notion |
| **bug-feature-analyzer** | balanced | Issue triage: classify incoming bugs and feature requests before allocation |
| **docker** | fast | Dev/test stack management, binary management, Dockerfiles |
| **security-auditor** | powerful | Security audit: OWASP, secrets, dependencies, supply chain |
| **openscad-developer** | balanced | Parametric 3D models in OpenSCAD, render-inspect-refine loop |
| **code-reviewer** | powerful | Clean code gatekeeper: blast-radius analysis, SOLID/DRY audit |
| **ui-ux-designer** | balanced | UI specifications, mockups, design systems |
| **api-specialist** | balanced | OpenAPI/contract-first API design, interface specifications |
| **devops-engineer** | fast | CI/CD, IaC, Kubernetes, monitoring, infrastructure |
| **performance-optimizer** | powerful | Big-O bottleneck identification, data-driven performance optimization |
| **claude-expert** | balanced | Claude Code expert: configuration (.claude), best practices, MCP integration |
| **gemini-expert** | balanced | Gemini (Antigravity) expert: configuration (.gemini), best practices, MCP integration |
| **opencode-expert** | balanced | Opencode expert: configuration (.opencode), best practices, MCP integration |
| **continue-expert** | balanced | Continue expert: configuration (.continue), best practices, MCP integration |
| **copilot-expert** | balanced | GitHub Copilot expert: configuration (.github/copilot), best practices, MCP integration |

### Systems Engineering Agents

| Agent | Tier | Description |
|-------|------|-------------|
| **se-orchestrator** | balanced | Coordinates the 6-level recursive SE breakdown |
| **se-requirements** | balanced | Elicits stakeholder needs and formalizes L1 black-box requirements |
| **se-architect** | powerful | Decomposes black-boxes into white-box architectures (L1/L2/L3) |
| **se-critic** | powerful | Audits architectures for completeness, consistency, traceability, verifiability |
| **se-interface-mgr** | balanced | Manages interface contracts and propagation maps across cascade levels |
| **se-termination** | fast | Deterministic termination at L3 component requirements |
| **se-validator** | powerful | L1 system validation via end-to-end user journey simulation |
| **se-verifier** | balanced | Multi-level verification (L1–Ln) against architecture specifications |
| **se-test-engineer** | balanced | MBSE test models and integration test strategies |
| **se-testreviewer** | powerful | Audits test strategies for edge cases, boundary values, flakiness |
| **se-integration-and-test-manager** | balanced | V&V orchestrator: integration strategy, test level coordination |

## Prompt Modes (Legacy / Hybrid / Modern)

agent-meta supports three rendering modes for agent templates, selectable per role:

| Mode | Template Source | Rendering | Use Case |
|------|----------------|-----------|----------|
| `legacy` | `agents/1-generic/` | unchanged Markdown | all existing roles, full compatibility |
| `hybrid` | `agents/1-generic/` | auto-wrapped in `<section>` tags | incremental migration |
| `modern` | `agents/1-generic-modern/` | native 6-block XML | optimized LLM parsing |

### 6-Block XML Format (Modern Mode)

Modern templates use exactly 6 XML blocks in fixed order:

```xml
<persona>     role identity, singleton rules</persona>
<workflow>    numbered step-by-step process</workflow>
<context>     project context, DoD flags, agent table</context>
<tools>       allowed tools with short descriptions</tools>
<output_contract>  return format, escalation</output_contract>
<constraints> hard rules — last, for recency bias</constraints>
```

`<constraints>` is intentionally placed last — LLMs follow final instructions more reliably.

### Configuration

```yaml
# .meta-config/project.yaml
agent-prompts:
  default: legacy          # fallback for all roles without explicit override
  modes:
    developer: modern      # uses agents/1-generic-modern/developer.md
    orchestrator: modern   # uses agents/1-generic-modern/orchestrator.md
```

### Validation & Token Counting

```bash
# Validate all Modern Mode templates (6-block + frontmatter)
python scripts/validate-modern-templates.py --all --strict

# Compare token estimates: legacy vs modern
python scripts/token-counter.py --role developer
python scripts/token-counter.py --role orchestrator --threshold 4000
```

→ Architecture details: `docs/architecture/prompt-modernization.md`

### Reference Agent & Modern Template Architecture

Modern templates leverage a canonical reference agent (`agents/1-generic-modern/_reference-agent.md`) that demonstrates all framework features in native 6-block XML format. The underscore prefix ensures it is not instantiated as a role but serves as a didactic blueprint for role authors. All modern mode agents inherit from this reference's structure, ensuring consistency in <persona>, <workflow>, <context>, <tools>, <output_contract>, and <constraints> ordering.

### Singleton-Orchestrator Rule

Only `main_chat` may spawn the `orchestrator`. Worker-agents must never call
`task(subagent_type="orchestrator", ...)` — doing so causes routing conflicts and
session-state corruption. Enforced via body-constraint injection in all worker agent files
and Gate #5 in `rules/1-generic/a2a-delegation-gates.md`.

---

## Quick Start

```bash
# 1. Add as submodule
git submodule add https://github.com/Popoboxxo/agent-meta .agent-meta
cd .agent-meta && git checkout v0.57.1 && cd ..

# 2. Create project config
mkdir -p .meta-config
cp .agent-meta/howto/configs/project.yaml.example .meta-config/project.yaml

# 3. Generate agents
python .agent-meta/scripts/sync.py --config .meta-config/project.yaml --init

# 4. Verify
python .agent-meta/scripts/sync.py --config .meta-config/project.yaml --dry-run
```

## Setup

### Prerequisites

- **Python 3.8+** (stdlib only — no external dependencies required)
- **Git** (for submodule management and sync operations)
- One of: **Claude** (VS Code), **Gemini** (VS Code/Antigravity), **Opencode**, **Continue**

### Configuration

Create `.meta-config/project.yaml`:

```yaml
# Core identity
project:
  name: my-project
  prefix: mp

# AI providers to target
ai-providers:
  - Claude
  - Gemini
  - Opencode
  - Continue

# Active agent roles
roles:
  - orchestrator
  - developer
  - requirements
  - tester
  - documenter
  - git

# Orchestrator behavior
orchestrator:
  enabled: true
  strict: true

# Quality profile
dod-preset: rapid-prototyping  # rapid-prototyping | strict | enterprise

# Speech mode
speech-mode: submissive        # full | short | childish | caveman | asozial | submissive
```

### DoD Presets

| Preset | Tests | REQ Traceability | Codebase Overview | Security Audit |
|--------|-------|------------------|-------------------|----------------|
| **rapid-prototyping** | ❌ | ❌ | ❌ | ❌ |
| **strict** | ✅ | ✅ | ✅ | ❌ |
| **enterprise** | ✅ | ✅ | ✅ | ✅ |

### Dynamic Model Tiers & Presets

agent-meta supports dynamic model routing through a preset matrix defined in `.meta-config/project.yaml`. The rigid assignment of models in `ai-providers.yaml` is replaced by a tier-based preset system that allows cost-efficient and task-specific model selection.

```yaml
# In .meta-config/project.yaml
ai-provider: Claude
model-preset: standard  # standard | cheap | advanced | expensive
```

**Key components:**
1. **Dynamic Model Crawling:** Update the local model cache with the latest models from the provider APIs (Anthropic, Gemini, Opencode) by running:
   ```bash
   python scripts/sync.py --update-models
   ```
2. **Tier-Presets Matrix:** Maps agent tiers (`nano`, `fast`, `balanced`, `powerful`, `max`) dynamically to model classes, considering a normalized cost factor (1-100). Systems-Engineering (SE) roles receive an automatic 1-2 tier upgrade via an `(SE)` preset variant.
3. **Admin UI:** A "Model Discovery & Pricing" Dashboard inside the Admin UI (`docs/admin-ui.html`) provides a sortable model table, crawl button, heatmap, and a preset selector with live preview. Start the UI using `scripts/admin-server.py`.

### Speech Modes

| Mode | Description |
|------|-------------|
| `full` | Default — normal communication (no rule generated) |
| `short` | Facts only, no filler, minimal verbosity |
| `childish` | Playful, animal/toy analogies, emojis |
| `caveman` | Brutally short, cave-speak style |
| `asozial` | Technically correct, dripping with contempt |
| `submissive` | Completely devoted, addresses as master/mistress |

## Repository Structure

```
agent-meta/
  agents/
    0-external/              # Wrapper template for external skill agents
    1-generic/               # Universal provider-agnostic agent templates
    2-platform/              # Platform-specific overrides (composition agents)
  config/                    # Framework configuration (managed by agent-meta)
    role-defaults.yaml       # Model/memory/permissionMode defaults per role
    ai-providers.yaml        # Provider settings (Claude, Gemini, Opencode, Continue, Copilot)
    tier-presets.yaml        # Tier-to-model mappings (cheap, normal, advanced, expensive) — NEW v0.65.0
    model-curation.yaml      # Model visibility: blacklist (hard) and disabled (soft) — NEW v0.65.0
    pricing-overlay.yaml     # Pricing data for cost factor calculation
    generated/
      model-registry.json    # Cached real models from OpenRouter/Zen/Go (406 models, keyless API)
    dod-presets.yaml         # DoD quality presets
    mcp-registry.yaml        # Global MCP server catalog
    provider-tools.yaml      # Per-provider tool capability whitelists
    skills-registry.yaml     # External skills registry
    rules-presets.yaml       # Rule embedding presets per provider
    export.yaml              # Export target configuration
    project-config.schema.json  # JSON Schema for project.yaml validation
    delegation-syntax.yaml   # PAL: provider-specific delegation syntax registry
    provider-capabilities.yaml  # PAL: capability matrix per provider
    provider-bootstrap.yaml  # PAL: bootstrap mechanism definitions
  docs/                      # Documentation
    admin-ui.html            # Web frontend for the Admin UI
    admin-ui-guide.md         # Admin UI usage guide (v0.66.0)
    agent-graph.html         # Interactive agent visualization graph
    agent-mindmap.md         # Mermaid mindmap of all agents
    live-dashboard.html      # Live session monitoring dashboard
    architecture/            # Architecture deep-dives
    providers/               # Provider-specific documentation
    concepts/                # Feature concepts & design decisions
      viz-logging-mcp.md     # MCP-based viz logging architecture
    viz-api.md               # Visualization API reference
    viz-event-schema.md      # Session event schema reference
    viz-architecture.md      # Visualization architecture decisions
    CODEBASE_OVERVIEW.md     # Codebase inventory per agent
    REQUIREMENTS.md          # Requirements (managed by requirements agent)
  hooks/                     # Git hooks and lifecycle triggers
    0-external/              # Hooks from external skill repos
    1-generic/               # Universal hooks (e.g. dod-push-check)
    2-platform/              # Platform-specific hook overrides
  howto/                     # Setup guides, templates, feature documentation
    configs/                 # Template configs (project.yaml, CLAUDE.md, etc.)
    setup/                   # First-time setup, instantiation, upgrade
    features/                # Feature-specific how-tos
  rules/                     # Coding conventions and agent rules
    0-external/              # Rules from external skill repos
    1-generic/               # Universal rules (auto-loaded into all agents)
    2-platform/              # Platform-specific rule overrides
  scripts/                   # Build and utility scripts
    sync.py                  # Main generation script (CLI entrypoint) + --update-models flag
    admin-server.py          # Backend server for the Admin UI (v0.65.0: new Tier Presets + Models sections)
    viz-logger.py            # MCP server & CLI fallback for agent event logging
    viz-logger-mcp.mjs       # HTTP/SSE MCP transport for OpenCode (Windows)
    viz-server.py            # Live dashboard HTTP server
    viz-report.py            # Session report generator (terminal/HTML/JSON)
    consistency-check.py     # Deterministic template consistency validation
    lib/                     # Sync library modules (config, agents, rules, etc.)
      model_discovery.py     # Keyless API fetching: OpenRouter, OpenCode Zen/Go (NEW v0.65.0)
      curation.py            # Model visibility management: blacklist/disabled lists (NEW v0.65.0)
      delegation_syntax.py   # PAL: DelegationSyntaxEngine for placeholder substitution
      bootstrap.py           # PAL: BootstrapEngine for provider-specific registration
  speech/                    # Communication style mode files
  templates/                 # Managed-block templates
    bootstrap/               # PAL: bootstrap instruction templates
      gemini-session-bootstrap.md  # Gemini define_subagent session-start workflow
  snippets/                  # Language-specific code snippets
    tester/                  # Test framework snippets
    developer/               # Code pattern snippets
  platform-configs/          # Platform defaults (HomeAssistant, Sharkord, etc.)
  VERSION                    # Current version
  CHANGELOG.md               # Version history
  README.md                  # This file
```

### Config Ownership

| Location | Owner | Purpose |
|----------|-------|---------|
| `.agent-meta/config/` | agent-meta framework | Role defaults, providers, DoD presets, registries — do not edit |
| `.meta-config/project.yaml` | Your project | Project identity, active roles, providers, orchestrator config |
| `.claude/platform-config.yaml` | Your project | Platform-specific variable overrides (`{{platform.*}}`) |

## Configuration

### Orchestrator Modes

The orchestrator's behavior is configured in `.meta-config/project.yaml`:

```yaml
orchestrator:
  enabled: true        # true = orchestrator active, false = main-chat mode
  strict: true         # true = always delegate, false = fallback allowed
  unknown-fallback:
    meta-feedback: true   # Send anonymized feedback (default: true)
    main-chat: true       # Allow main chat to handle (default: true)
    ask-user: false       # Ask user for preference (default: false)
```

| Mode | enabled | strict | Behavior |
|------|---------|--------|----------|
| **Strict** | true | true | Always delegate, never execute in main chat |
| **Relaxed** | true | false | Main chat can handle unknown intents |
| **Ask-First** | true | — | User asked: "Here or delegate?" |
| **Disabled** | false | — | No orchestrator, main chat does everything |

### Visualization Modes

```yaml
viz:
  enabled: true
  mode: "full"          # off | static | dynamic | full
  event_log: ".meta-viz/events.jsonl"
  report:
    retention_days: 7
    session_timeout_min: 5
  server:
    port: 8765
    timeout_sec: 300
```

| Mode | Mindmap | Session Tracking |
|------|---------|------------------|
| `off` | ❌ | ❌ |
| `static` | ✅ | ❌ |
| `dynamic` | ❌ | ✅ |
| `full` | ✅ | ✅ |

## Workflows

| ID | Workflow | Description | Orchestrator Agent |
|----|----------|-------------|--------------------|
| **A** | New Feature | Branch → REQ → Test → Dev → Validate → PR | `feature` |
| **B** | Bugfix | Branch → REQ → Test → Dev → Validate → PR | `feature` |
| **C** | Code Audit | Code review + blast-radius + quality scan | `code-reviewer` |
| **E** | Refactoring | Branch → REQ → Dev → Test → Validate → PR | `feature` |
| **H1** | Agent Sync | sync.py → commit "chore: regenerate agents" | `agent-meta-manager` |
| **H2** | Upgrade | Read upgrade workflow → apply | `agent-meta-manager` |
| **I** | Ideation | Explore idea → sharpen vision → handoff to requirements | `ideation` |
| **K** | Meta-Feedback | Collect framework feedback → create GitHub issue | `meta-feedback` |
| **L** | GitHub Issue | Read issue → requirements → dev → test → validate → close | `orchestrator` |
| **M** | Scout Ecosystem | Search for new skills/roles/rules/patterns | `agent-meta-scout` |
| **O** | Log Analysis | Analyze logs → cluster errors → delegate findings | `log-analyzer` |
| **P** | Project Issue | Create standardized bug/feature GitHub issue | `feedback` |
| **U** | SE Cascade | 6-level recursive systems engineering breakdown | `se-orchestrator` |

## Contributing

### Branch Policy

This repository uses a strict branch policy. **Never commit directly to `main`** for template, rule, script, or sync changes.

```bash
# Always create a feature branch
git checkout -b feat/my-change
# ... make changes ...
git add .
git commit -m "feat: add my feature"
git push -u origin feat/my-change
```

Direct commits on `main` are only allowed for:
- Version bumps (`VERSION`, `CHANGELOG.md`, `README.md`)
- Single-line typo fixes (with user confirmation)
- Post-merge maintenance

### Development Workflow

1. **Create a branch** (`feat/...`, `fix/...`, `refactor/...`, `docs/...`)
2. **Edit templates** in `agents/1-generic/` or configuration in `config/`
3. **Bump the template version** in frontmatter (major/minor/patch per semver)
4. **Run consistency check**: `python scripts/consistency-check.py`
5. **Verify generation**: `python scripts/sync.py --dry-run`
6. **Commit** with [Conventional Commits](#conventional-commits)
7. **Create a PR**

### Conventional Commits

```
<type>(REQ-xxx): <description>    ← with REQ traceability
<type>: <description>             ← without REQ traceability
```

| Type | Description | REQ-ID |
|------|-------------|--------|
| `feat` | New feature | When req-traceability active |
| `fix` | Bug fix | When req-traceability active |
| `refactor` | Refactoring without behavior change | When req-traceability active |
| `test` | Add or modify tests | When req-traceability active |
| `chore` | Maintenance: dependencies, config, versions | Never |
| `docs` | Documentation | Never |
| `ci` | CI/CD changes | Never |

### Adding a New Agent Role

Manual steps:
1. Create `agents/1-generic/<role>.md` with frontmatter (`name`, `version`, `description`, `hint`, `tools`)
2. Add entry to `config/role-defaults.yaml` (model, memory, permissionMode, tier)
3. Update `howto/setup/instantiate-project.md` agent table

Everything else (CLAUDE.md, AGENTS.md, provider agents, visualization) is auto-generated by `sync.py`.

### Development Conventions

- **No external Python dependencies** beyond stdlib (stdlib-only policy)
- **Agent templates** use YAML frontmatter with semver versioning
- **Placeholders** follow `{{GROSS_MIT_UNTERSTRICH}}` naming convention
- **Generated output** (`.claude/agents/`, `.opencode/agents/`, etc.) is never edited manually
- **Unit tests**: manual verification via `sync.py --dry-run` (no automated test system)

## License

MIT
