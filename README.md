# agent-meta

> [!WARNING]
> ## VibeCoding Experiment — Read Before Using
> This repository is intentionally run as a **VibeCoding experiment**.
> The primary goal is to demonstrate both the **benefits** and **risks** of LLM-driven development on a real but evolving framework.
>
> ### Ground rules of this repo
> - **Source code interventions should happen only in absolute emergencies.**
> - The preferred workflow is to explore how far we can get with LLM providers, agent orchestration, and prompt-driven iteration.
> - This project is a **sandbox/playground** for experimenting with different AI coding styles, tooling, and operational patterns.
> - "Production hardening" is not the primary objective; learning effects and transparent trade-offs are.
>
> In short: this is a practical lab setup to evaluate VibeCoding methods, compare approaches, and develop agent frameworks while keeping limitations visible.

> [!IMPORTANT]
> ## AI Agent Setup & Initialization Protocol
> 
> When initializing or connecting to a project, AI coding assistants and autonomous agents (Claude Code, Gemini/Antigravity, Opencode, Continue, GitHub Copilot, Mammouth Code, etc.) **MUST** follow these steps to integrate `agent-meta`:
> 
> 1. **Add Submodule:** If `.agent-meta` is missing in your repository, embed the framework:
>    ```bash
>    git submodule add https://github.com/Popoboxxo/agent-meta .agent-meta
>    git submodule update --init --recursive
>    ```
> 2. **Initialize Configuration & Generate Agents:** Run `sync.py` to scaffold `.meta-config/project.yaml` and generate provider-specific agent files:
>    - **Interactive Guided Setup:** `python .agent-meta/scripts/sync.py --setup`
>    - **Automated Default Init:** `python .agent-meta/scripts/sync.py --init`
> 3. **Re-Sync After Config Changes:** Re-run `python .agent-meta/scripts/sync.py` whenever `.meta-config/project.yaml` is modified.

[![Version](https://img.shields.io/badge/version-0.91.2-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.x-green.svg)]()
[![License](https://img.shields.io/badge/license-MIT-gray.svg)]()
| **Date:** 2026-08-01

> Central meta-repository for standardizing and reusing Claude agent roles across all projects.
> Git submodule embedded in projects. Provides standardized agent templates (1-generic, 2-platform, 0-external).
> Generates project-ready agent files in `.claude/agents/` via `sync.py`.

> Supports 6 AI providers: Claude Code, Gemini, Opencode, Continue, GitHub Copilot, Mammouth Code.

## Architecture

```mermaid
graph TD
    subgraph Agent Meta Submodule
        A[agent-meta/1-generic]
        B[agent-meta/2-platform]
        C[agent-meta/0-external]
    end
    
    D[.meta-config/project.yaml] --> S(sync.py)
    A --> S
    B --> S
    C --> S
    
    S -->|Scaffolds| K[Knowledge Engine Bundle]
    S -->|Generates Agents| P1[.claude/agents]
    S -->|Generates Agents| P2[.gemini/agents]
    S -->|Generates Agents| P3[.opencode/agents]
```


## Quick Start

```bash
# Add as submodule
git submodule add https://github.com/Popoboxxo/agent-meta .agent-meta
cd .agent-meta && git checkout v0.91.2 && cd ..

# Install dependencies
pip install -r .agent-meta/requirements.txt

# Run interactive setup
python .agent-meta/scripts/sync.py --setup
```

## Core Capabilities & Features

```mermaid
mindmap
  root((agent-meta))
    Generation Engine
      sync.py Template Compilation
      Context Compaction V2
      Single-Tree XML Architecture
    Knowledge Engine
      OKF-Compliant Scaffolding
      Domain Presets
      Bundle Manager
    Admin UI
      Live Configuration
      Live Model Registry Download
      Viz Dashboard
    Workflow Management
      A2A Handoff Protocol
      DoD Presets
      Quality Pipelines
    Extensions
      Native Extensions Whitelist
      MCP Servers
      External Skills
```

## Agent Roster — 51 Generic Agents

### Core Development (12 agents)

| Agent | Tier | Version | Description |
|-------|------|---------|-------------|
| **orchestrator** | balanced | 6.6.0 | Provider-agnostic task router: decomposes, parallelizes, delegates with FANOUT/PIPELINE/BARRIER |
| **developer** | powerful | 2.5.2 | Feature implementation and bugfixes |
| **junior-developer** | fast | 1.1.1 | Trivial changes (1-2 files, no architecture impact) |
| **senior-developer** | powerful | 1.1.2 | Complex features, architecture decisions, difficult bugs |
| **principal-developer** | ultra | 1.0.0 | Last-resort escalation above senior-developer — root-cause diagnosis, systemic reasoning, no symptom fixes (most expensive call) |
| **intern-developer** | nano | 1.0.0 | Easter-egg/gag agent: over-eager clueless intern, read-only and harmless — not for production |
| **requirements** | balanced | 1.4.2 | Capture requirements, assign REQ-IDs, maintain REQUIREMENTS.md |
| **tester** | balanced | 2.1.2 | Isolated unit tests with mocks/stubs (TDD workflow) |
| **validator** | balanced | 4.1.1 | Formal DoD gatekeeper: checkbox audit, REQ-ID presence, commit conventions |
| **code-reviewer** | powerful | 1.2.2 | Code health gatekeeper: Clean Code, SOLID, blast-radius analysis |
| **documenter** | fast | 1.4.2 | Maintains CODEBASE_OVERVIEW.md, ARCHITECTURE.md, README.md, conclusions |
| **git** | fast | 2.4.0 | All git operations: commits, branches, merges, tags, push/pull |

### Workflow & Framework (9 agents)

| Agent | Tier | Version | Description |
|-------|------|---------|-------------|
| **feature** | balanced | 1.10.1 | Full feature lifecycle: Branch → REQ → TDD → Dev → Validate → PR |
| **release** | balanced | 1.4.2 | Versioning, changelogs, build processes, GitHub releases |
| **ideation** | balanced | 1.6.1 | Idea exploration, vision sharpening, concept concretization |
| **feedback** | fast | 1.2.2 | Standardizes bug reports and feature requests as GitHub issues |
| **agent-meta-manager** | balanced | 1.11.1 | Manage agent-meta: upgrades, sync, feedback, project-specific agents |
| **agent-meta-scout** | balanced | 1.1.3 | Scout AI ecosystem: new skills, roles, rules, patterns |
| **meta-feedback** | fast | 2.1.3 | Improvement proposals for agent-meta as GitHub issues |
| **prompt-engineer** | balanced | 1.3.1 | Expert for prompt engineering, AI security, agent design |
| **concept-reviewer** | balanced | 1.0.1 | Reviews design docs for completeness, logic, risks, feasibility |

### Specialist Roles (16 agents)

| Agent | Tier | Version | Description |
|-------|------|---------|-------------|
| **api-specialist** | balanced | 1.1.3 | API design, OpenAPI specs, contract-first development |
| **bug-feature-analyzer** | balanced | 1.1.2 | Triage and classify incoming bug reports and feature requests |
| **database-engineer** | powerful | 1.0.0 | Relational schema design, backwards-compatible migrations, query optimization, index strategy |
| **dependency-auditor** | balanced | 1.0.0 | Supply-chain hygiene: SBOM analysis, license compatibility, version drift, outdated/vulnerable packages |
| **devops-engineer** | fast | 1.1.2 | CI/CD pipelines, IaC, container orchestration |
| **docker** | fast | 1.4.2 | Docker operations: Compose stacks, binary management, test environments |
| **effort-estimator** | fast | 1.0.1 | Estimates effort for development tasks with complexity scoring |
| **explorer** | nano | 1.0.0 | Read-only codebase research, dependency and impact mapping |
| **export-manager** | fast | 1.1.2 | Routes JSON payloads to Markdown/Confluence/Jira-Xray/Notion |
| **incident-responder** | powerful | 1.0.0 | Live incident coordination: RCA (5-Whys/Fishbone), severity classification, prioritized hotfixes |
| **log-analyzer** | balanced | 1.1.2 | Log analysis: frequency clustering, RFC 5424 severity classification |
| **openscad-developer** | balanced | 1.1.3 | Parametric 3D models in OpenSCAD |
| **performance-optimizer** | powerful | 1.1.2 | Data-driven Big-O bottleneck identification |
| **security-auditor** | powerful | 1.2.2 | Static security analysis: OWASP Top 10, secrets, supply-chain |
| **ui-ux-designer** | balanced | 1.1.2 | UI specs, mockups, design systems |
| **e2e-tester** | balanced | 1.0.0 | End-to-end browser testing via Playwright: user flows, visual regression, accessibility audits |


### Knowledge Engine (7 agents)

| Agent | Tier | Version | Description |
|-------|------|---------|-------------|
| **knowledge-curator** | balanced | 1.0.0 | Strategic Knowledge Engine control: schema evolution, domain adaptation |
| **knowledge-gardener** | fast | 1.0.0 | Small-scale wiki maintenance: repair links, harmonize tags |
| **knowledge-indexer** | fast | 1.0.0 | Maintains index.md (content catalog) and log.md (event log) |
| **knowledge-ingestor** | powerful | 1.0.0 | Ingests sources, extracts key info, creates/updates wiki pages |
| **knowledge-linter** | balanced | 1.0.0 | Wiki health check: contradictions, orphans, stale claims, broken links |
| **knowledge-migrator** | balanced | 1.0.0 | Cleans up and migrates existing project content into the OKF Wiki |
| **knowledge-querier** | fast | 1.0.0 | Answers questions against the Knowledge Wiki |

### Knowledge Engine Framework (Feature Overview)
Introduced in v0.83.0, the Knowledge Engine brings semantic codebase management to the next level:
- **Phase A (OKF-compliant Scaffolding):** Instantiates a structured `knowledge/` folder with `index.md`, `log.md`, and dedicated domain directories (Architecture, Domain, Entities, Guides).
- **Phase B (Domain Presets):** Select pre-configured domain structures directly from the Admin UI (e.g. `technical-project`, `gamedev`, `personal-wiki`).
- **Phase C (Bundle Manager):** The `knowledge.py` subsystem automatically aggregates wiki markdown into provider-specific context files dynamically.

### Provider Expert Agents (5 agents)

| Agent | Tier | Version | Description |
|-------|------|---------|-------------|
| **claude-expert** | powerful | 1.0.0 | Claude Code platform analysis: .claude/ config, best practices, MCP integration |
| **gemini-expert** | powerful | 1.0.0 | Gemini expert: configuration (.gemini), best practices, MCP integration |
| **opencode-expert** | powerful | 1.0.0 | Opencode expert: configuration (.opencode), best practices, MCP integration |
| **mammouth-expert** | powerful | 1.0.0 | Mammouth Code expert: configuration (.mammouth), best practices, MCP integration |
| **continue-expert** | powerful | 1.0.0 | Continue expert: configuration (.continue), best practices, MCP integration |
| **copilot-expert** | powerful | 1.0.0 | GitHub Copilot expert: configuration (.github/copilot), best practices, MCP integration |

### Systems Engineering Cascade (13 agents — Legacy SE mode)

| Agent | Tier | Version | Description |
|-------|------|---------|-------------|
| **se-requirements** | balanced | 1.10.0 | Elicits stakeholder needs, captures multi-level requirements (L0→L1) |
| **se-architect** | powerful | 1.8.0 | Designs system architecture via functional decomposition (L1→L3) |
| **se-critic** | powerful | 1.8.0 | Audits requirements and architecture against generic laws |
| **se-interface-mgr** | balanced | 1.7.0 | Manages generic signal flow and deterministic synchronization |
| **se-termination** | fast | 1.7.0 | Deterministic leaf/continue decision with dynamic depth control |
| **se-junior-developer** | fast | 1.1.0 | Trivial SE leaf nodes (COTS wrappers, single-interface) |
| **se-developer** | balanced | 1.1.0 | Standard SE leaf nodes with multiple interfaces |
| **se-senior-developer** | powerful | 1.1.0 | Complex SE leaf nodes (5+ interfaces, cross-cutting) |
| **se-test-engineer** | balanced | 1.2.1 | MBSE test models and integration tests |
| **se-testreviewer** | powerful | 1.2.1 | Audits test strategy for edge cases and flakiness |
| **se-validator** | powerful | 1.2.0 | L1 system validation: end-to-end user journeys |
| **se-verifier** | balanced | 1.2.0 | Multi-level verification L1-Ln |
| **se-integration-and-test-manager** | balanced | 1.2.0 | V&V orchestrator: integration strategy, test levels |

**Note:** SE roles remain in legacy format. Main roles operate on the newer Context Compaction V2 (Single-Tree XML Architecture).

## Platform Overrides (2-platform/)

Overrides provide platform-specific customizations. Two modes:
- **Full-replacement** (no `extends:`) — completely replaces the generic agent
- **Composition** (`extends:` + `patches:`) — adds/modifies sections

| Platform | Overrides | Mode |
|----------|-----------|------|
| agent-meta | developer, claude-expert, continue-expert, copilot-expert, gemini-expert, opencode-expert, mammouth-expert | composition |
| Home Assistant | developer, documenter, log-analyzer | composition |
| Sharkord | developer, docker, release | composition |

## External Skills (0-external/)

External skills are registered in `config/skills-registry.yaml` and are dynamically cloned by `sync.py` when enabled via `.meta-config/project.yaml`.

**Active Skills:**
- `home-organization` — Home Organization Specialist (Gridfinity, OpenGrid, NeoGrid, French Cleat, Underware, Deskware)
- `opengrid-openscad` — OpenGrid OpenSCAD Designer (28mm Grid, QuackWorks patterns)

**Add a new skill:**
```bash
python scripts/sync.py --add-skill <repo-url> --skill-name <name> --role <role>
```

## 📖 Documentation Index

The extensive documentation for Agent-Meta has been reorganized into the `docs/` folder for better readability.

### Guides & How-Tos (`docs/guides/`)
- Setup, CI integration, feature guides, and reflection loops.
- MCP configurations and quality pipelines.

### API & Framework Reference (`docs/api/`)
Detailed definitions of all core functions, CLI commands, and framework mappings:
- **[CLI Reference](docs/api/cli-reference.md)**: Full list of all `sync.py` flags and operations.
- **[Slash Commands](docs/api/slash-commands.md)**: All available chat-UI commands.
- **[Composition System](docs/api/composition-system.md)**: Documentation on Agent overrides (`2-platform`, `3-project`) and patches.
- **[PAL Variables](docs/api/pal-variables.md)**: Mappings for `{{PAL_DELEGATE}}` and other abstraction layer placeholders.
- **[Admin UI Reference](docs/api/admin-ui-reference.md)**: Detailed configuration guide and help texts for the Agent Meta Manager.

### Architecture & UI (`docs/ui/`)
- **[Agent Graph Visualization](docs/ui/agent-graph.html)**: Interactive node-graph of agent delegations.
- **[Admin UI](docs/ui/admin-ui.html)**: The web-frontend for `admin-server.py`.
- **[Viz API](docs/api/viz-api.md)**: Architecture documentation for the Viz Server.
- **[Viz Event Schema](docs/api/viz-event-schema.md)**: JSON schema for Viz events.

### Systems Engineering Cascade (`docs/se-cascade/`)
- V-Model documentation and workflow specifications for the SE cascade.

## DoD Presets (6 presets)

| Preset | REQ-Traceability | Tests | Codebase-Overview | Security-Audit | SE |
|--------|-----------------|-------|-------------------|----------------|----|
| **full** | ✅ | ✅ | ✅ | ❌ | — |
| **standard** | ❌ | ✅ | ❌ | ❌ | — |
| **rapid-prototyping** | ❌ | ❌ | ❌ | ❌ | — |
| **spec-optional** | ❌ | ✅ | ❌ | ❌ | — |
| **spec-driven** | ✅ | ✅ | ❌ | ❌ | recommended |
| **spec-certified** | ✅ | ✅ | ✅ | ✅ | ✅ |

Change preset in `.meta-config/project.yaml`:
```yaml
dod-preset: rapid-prototyping
```

Or via slash command: `/set-preset`

## Model Tiers & Tier Presets

### 5 Model Tiers

| Tier | Claude | Gemini | Opencode |
|------|--------|--------|----------|
| **nano** | claude-haiku-4-5-20251001 | gemini-3.5-flash-medium | deepseek-v4-flash |
| **fast** | claude-haiku-4-5-20251001 | gemini-3.5-flash-high | deepseek-v4-flash |
| **balanced** | claude-sonnet-4-6 | gemini-3.1-pro-low | qwen3.7-plus |
| **powerful** | claude-opus-4-8 | gemini-3.1-pro-high | kimi-k2.6 |
| **max** | claude-fable-5 | gemini-3.1-pro-high | kimi-k2.7-code |
| **ultra** | claude-opus-4-8 | gemini-3.1-pro-high | kimi-k2.7-code |

**ultra** is reserved exclusively for `principal-developer` (last-resort escalation after repeated senior-developer failures). Never auto-routed by keyword. Resolves to the strongest *real* model (not fictitious IDs like claude-fable-5).

Continue and Copilot: no per-agent model tiers (managed centrally).

### 5 Tier Presets

- **Cheap** — balance cost and quality
- **Normal** — standard, mid-range models
- **Advanced** — higher-quality, more powerful models
- **Expensive** — top-tier, expert-grade models
- **Expensive as Hell** — maximum capability, cost-no-object

## Slash Commands (22 commands)

| Command | Description |
|---------|-------------|
| `/add-mcp-server` | Guided setup to activate an MCP server |
| `/add-project-role` | Add a project-specific agent role (override or extension) |
| `/add-provider` | Add an AI provider to this project |
| `/admin` | Start or stop the Admin UI server (includes viz dashboard and MCP server) |
| `/analysis` | Run AST dependency analysis |
| `/analyze-logs` | Analyze log files with severity classification (RFC 5424) |
| `/checkpoint` | List or resume orchestrator checkpoints |
| `/commit` | Stage changes and create a conventional commit |
| `/consistency-check` | Validate agent templates, commands, cross-references |
| `/diagnose` | Health-check the agent-meta setup |
| `/doc-now` | Update CODEBASE_OVERVIEW.md via documenter agent |
| `/feedback` | Report bug/feature as standardized GitHub issue |
| `/merge` | Create PR for current branch and merge into main |
| `/open-docs` | Open docs/ folder or specific analysis document |
| `/pipelines` | Show all quality pipelines — active/disabled status |
| `/report-bug` | Report a bug via feedback agent |
| `/set-preset` | Change DoD preset or speech mode |
| `/test-orchestration` | Run orchestration dry-run and validate functions |
| `/update-extensions` | Update managed blocks in project extension files |
| `/update-meta` | Re-sync all agents without upgrading version |
| `/upgrade-meta` | Upgrade submodule to latest version and re-sync |
| `/what-is` | Explain what an agent does |

## Quality Pipelines (7 pipelines)

| Pipeline | Stages | Flow |
|----------|--------|------|
| **standard-feature** | branch → implement → review (developer/code-reviewer, 3x) → commit | Full feature with reviews |
| **quick-fix** | fix → commit | Immediate fix without review |
| **bugfix** | triage → fix → review (2x) → document | Bug with double review |
| **concept-development** | research → concept-loop (ideation/concept-reviewer, 3x) → handoff | Idea refinement |
| **refactor** | analyze (senior-developer) → implement → review (2x) → commit | Large refactor |
| **docs-update** | update → commit | Documentation only |
| **se-cascade** | L0 stakeholder → L3 architecture → implementation → V&V (8 stages) | Full Systems Engineering |

## Reflection Pairs (5 pairs)

| Pair ID | Generator | Critic | Max Iterations |
|---------|-----------|--------|---|
| **dev-review-loop** | developer | code-reviewer | 3 |
| **se-requirements-loop** | se-requirements | se-critic | 3 |
| **se-architect-loop** | se-architect | se-critic | 3 |
| **se-test-loop** | se-test-engineer | se-testreviewer | 3 |
| **se-dev-review-loop** | se-developer | code-reviewer | 3 |

## Hooks (5 hooks, propagated to all providers)

| Hook | Trigger | Effect |
|------|---------|--------|
| `orchestrator-guard.sh` | PreToolUse | Enforces orchestrator-first rules (prevents self-handoff, validates delegation depth) |
| `dod-push-check.sh` | PrePush | Blocks push if DoD criteria unmet (commit conventions, REQ-IDs if traceability active) |
| `lifecycle-check.sh` | Post-commit | Detects Git events (release-tag, merge), writes pending-tasks.md for triggered agents |
| `sync-on-config-change.sh` | PostToolUse | Triggers sync.py re-run when `.meta-config/project.yaml` changes (detects via Write/Edit tools) |
| `viz-log.sh` | Events | Logs agent events to viz event file for dashboard tracking |

## MCP Servers (7 servers)

| Server | Transport | Description |
|--------|-----------|-------------|
| **home-assistant** | SSE | Read-only HA data (GetLiveContext, GetDateTime, todo_get_items) |
| **influxdb** | stdio | Time-series queries (Flux, write blocked) |
| **viz-logger** | stdio | Agent event logging (log_viz_event) |
| **a2a-handoff** | stdio | A2A schema validation (validate_handoff, resolve_handoff) |
| **honcho** | SSE | Persistent memory and context storage across sessions |
| **reqogniloom** | SSE | Requirements, architecture, tests, and traceability platform |
| **playwright** | stdio | E2E browser automation, snapshots, and accessibility audits |

## Admin UI Features

Web-based control panel for project configuration (default: `http://localhost:7420`).

**Key Controls:**

- **Orchestrator Mode Selector** — Dropdown to switch between `strict`, `advisory`, and `main-chat` modes. Writes directly to `.meta-config/project.yaml` → `orchestrator.mode`. No restart required.
- **DoD Preset Selector** — Change quality pipeline preset (full, standard, rapid-prototyping, etc.)
- **MCP Server Dashboard** — View active MCP server status and configurations
- **Agent Visualization** — Interactive agent dependency graph and mindmap

Start with: `python scripts/sync.py --admin` or `/admin` slash command.

## A2A Handoff Protocol

Structured JSON envelopes for Agent-to-Agent communication:

```json
{
  "protocol_version": "2.0",
  "handoff_id": "unique-id",
  "source_agent": "developer",
  "target_agent": "tester",
  "schema_ref": "schemas/handoffs/task-spec.schema.json",
  "payload": {
    "t": "Implement feature X with tests",
    "ctx": { "req_ids": ["REQ-042"] },
    "con": { "codebase_size": "medium" },
    "refs": [],
    "pri": 1,
    "dep": []
  }
}
```

**Limits:**
- `payload.t` max 300 characters
- Delegation depth max 5 (Claude Code platform limit)
- No re-delegation (prevents self-handoff loops)

**Schemas:** `schemas/` directory includes TaskSpec core and 4 extension schemas (Ideation, Design, API, Review + SE Decomposition). Cover 84% of agent routes.

## Provider Generation Matrix

| Provider | Context File | Agents Dir | Rules | Hooks | Commands | Settings |
|----------|-------------|-----------|-------|-------|----------|---------|
| Claude Code | CLAUDE.md | .claude/agents/ | .claude/rules/ | .claude/hooks/ | .claude/commands/ | .claude/settings.json |
| Gemini | AGENTS.md | .gemini/agents/ | .gemini/rules/ | — | .gemini/commands/ | .gemini/settings.json |
| Opencode | AGENTS.md | .opencode/agents/ | (in AGENTS.md) | — | .opencode/commands/ | opencode.json |
| Continue | CONTINUE.md | .continue/agents/ | .continue/rules/ | — | .continue/prompts/ | .continue/config.yaml |
| Copilot | .github/copilot/COPILOT.md | .github/copilot/agents/ | .github/copilot/rules/ | — | — | .github/copilot/copilot.json |

## Native Extensions Whitelist

Provider-native extensions (plugins, hooks, skills) require explicit approval gates to run safely.
Configure your exemptions in `.meta-config/project.yaml`:
```yaml
extensions:
  whitelist:
    - home-assistant-mcp
    - custom-git-hook
```
Extensions not listed here will be blocked during execution.

## Speech Modes (6 modes)

| Mode | Style |
|------|-------|
| **full** | Default, no restrictions |
| **short** | Facts only, minimal verbosity, bullet points |
| **childish** | Playful, animal/toy analogies, emojis |
| **caveman** | Brutally short, cave-speak |
| **asozial** | Technically correct, dripping with contempt |
| **submissive** | Completely devoted, addresses as master/mistress |

## Lifecycle Triggers

```yaml
lifecycle-triggers:
  on-release:
    - agent: documenter
      task: "Update CODEBASE_OVERVIEW.md and ARCHITECTURE.md for this release."
  on-merge:
    - agent: code-reviewer
      task: "Post-Merge Blast-Radius-Analyse: check affected code paths."
```

## Systems Engineering (SE) Mode

**Recursive Zig-Zag Decomposition:** L0 (stakeholder) → L6 (implementation)

**SE Variables:**
- `SE_BASE_DIR` — Output directory for decomposition
- `SE_MIN_DEPTH`, `SE_MAX_DEPTH` — Depth constraints (default: 0-6)
- `SE_MAX_CRITIC_ITERATIONS` — Max architecture critique rounds (default: 3)
- `SE_MAX_PARALLEL_CELLS` — Max parallel components at one level
- `SE_MAX_CELLS` — Max total components in cascade
- `cost_limit_eur` — Token cost ceiling

**SE Cascade Pipeline:** Full 8-stage V-model from stakeholder requirements to system validation.

**SE Roles:** 13 dedicated agents (see Agent Roster section).

Reference: `howto/se-workflow.md`

## Model Discovery

Dynamic model registry updated via `sync.py --update-models`:

**Sources:**
- OpenRouter: ~338 models with live pricing
- OpenCode Zen: ~48 models
- OpenCode Go: max-tier models

**Storage:** `config/generated/model-registry.json` (cached, network-outage resilient)

**Live override capability:** Target configurations can now dynamically download updated model registries directly from GitHub via the Admin UI, enabling instant access to the latest models without waiting for a full `agent-meta` release!

**Curation:** `config/model-curation.yaml` — blacklist (hard exclusion) and disabled (soft-hide)

## CLI & Maintenance Features

- **Config Audit Routine:** Run `python scripts/sync.py --audit-config` to deeply inspect and validate your project and provider configurations for inconsistencies. Add `--apply` to auto-fix issues.
- **Environments & Secrets:** Dynamically scaffold `.meta-config/env.ps1` and `.meta-config/env.sh` based on variables defined in `project.yaml`.

## Directory Structure

```
agents/
  0-external/                # External skill wrappers (dynamically cloned)
  1-generic/                 # Universal provider-agnostic templates (44 + 13 SE agents)
  2-platform/                # Platform-specific overrides (extends + patches)
config/
  role-defaults.yaml         # Agent defaults, routing, handoff contracts
  skills-registry.yaml       # External skill repos
  dod-presets.yaml           # 6 DoD presets
  tier-presets.yaml          # 5 tier presets (cheap, normal, advanced, expensive)
  ai-providers.yaml          # 6 provider configs (Claude, Gemini, Opencode, Continue, Copilot, Mammouth)
  mcp-registry.yaml          # 7 MCP server configs
  generated/
    model-registry.json      # Cached real models (338+ models from APIs)
  model-curation.yaml        # Model visibility: blacklist and disabled lists
scripts/
  sync.py                    # Main CLI — agent generation and management
  admin-server.py            # Admin UI backend (port 7420)
  viz-logger.py              # Agent event logging (MCP + CLI fallback)
  viz-server.py              # Live dashboard server
  viz-report.py              # Session report generator
  consistency-check.py       # Template validation
  run-cascade.py             # SE cascade runner
  lib/
    config.py, agents.py, rules.py, hooks.py, commands.py
    model_discovery.py       # Keyless API fetching (OpenRouter, Zen, Go)
    curation.py              # Model visibility management
    delegation_syntax.py     # PAL engine (placeholder substitution)
    bootstrap.py             # Provider bootstrap (Gemini API, Continue config)
    mcp.py                   # MCP rules and config injection
snippets/                    # Language-specific code snippets
  developer/, tester/, orchestrator/
external/                    # Dynamically cloned skill repositories (gitignored)
schemas/                     # A2A handoff JSON schemas
speech/                      # Speech mode rule files
howto/
  setup/                     # First steps, instantiation, upgrade
  features/                  # 22 feature how-to guides
  configs/                   # Template configs (project.yaml, CLAUDE.md)
docs/
  architecture/              # Mermaid architecture diagrams
  concepts/                  # Feature design decisions
  providers/                 # Provider-specific documentation
  admin-ui.html              # Web frontend for Admin UI
  agent-graph.html           # Interactive agent visualization
  agent-mindmap.md           # Mermaid mindmap of all agents
VERSION                      # Current version (v0.86.3)
CHANGELOG.md                 # Version history
README.md                    # This file
```

## Adding a New Agent Role

Manual steps (required):

1. Create `agents/1-generic/<role>.md` with YAML frontmatter:
   ```yaml
   ---
   name: role-name
   version: 1.0.0
   description: What this agent does
   hint: Short hint for /what-is
   tools: [tool1, tool2]
   ---
   ```
2. Add entry to `config/role-defaults.yaml` (model tier, memory, permissionMode, routing)
3. Update `howto/setup/instantiate-project.md` agent table

Everything else (provider agents, CLAUDE.md, visualization) is auto-generated by `sync.py`.

## Placeholders (PAL — Provider Abstraction Layer)

Resolved at sync-time to handle provider-specific differences:

| Placeholder | Resolves to | Purpose |
|-------------|------------|---------|
| `{{PAL_DELEGATE}}` | Provider-specific agent dispatch syntax | Isolation from delegation syntax differences |
| `{{PAL_FANOUT}}` | Parallel same-type dispatch syntax | Provider-specific parallel execution |
| `{{PAL_PARALLEL_GROUP}}` | Parallel different-type dispatch syntax | Cross-agent parallelization |
| `{{PAL_FALLBACK}}` | Fallback when tools unavailable | Graceful degradation |
| `{{PAL_TOOL_PREAMBLE}}` | Provider tool intro block | Consistent tool documentation |

All placeholders follow `{{GROSS_MIT_UNTERSTRICH}}` naming convention.

## Configuration

### Project Configuration

Create `.meta-config/project.yaml`:

```yaml
project:
  name: my-project
  prefix: mp

ai-providers:
  - Claude
  - Gemini

roles:
  - orchestrator
  - developer
  - tester
  - documenter
  - git

orchestrator:
  enabled: true
  mode: strict    # strict | advisory | main-chat

dod-preset: rapid-prototyping
speech-mode: short
```

### Config Ownership

| Location | Owner | Purpose |
|----------|-------|---------|
| `.agent-meta/config/` | agent-meta framework | Role defaults, providers, DoD presets — read-only |
| `.meta-config/project.yaml` | Your project | Project identity, active roles, providers, orchestrator config |
| `.claude/platform-config.yaml` | Your project | Platform-specific variable overrides |

### Orchestrator Modes

Three operational modes for task routing and delegation:

| Mode | Description | Use Case |
|------|-------------|----------|
| **strict** | Orchestrator required, no direct dispatch, enforces all routing rules | Production codebases, strict quality gates, large teams |
| **advisory** | Orchestrator recommended but user can override, direct dispatch allowed | Flexible workflows, balanced control |
| **main-chat** | No orchestrator spawned; main_chat acts as router + worker in one | Rapid prototyping, single-developer projects, low overhead |

Set in `.meta-config/project.yaml`:
```yaml
orchestrator:
  mode: strict              # default for production
  mode: advisory            # flexible routing
  mode: main-chat           # direct execution, no subagent overhead
```

#### Per-Provider Overrides

The `orchestrator.mode` above is the framework default, applied to every provider. Override it
for a single provider via `orchestrator.provider-overrides`:

```yaml
orchestrator:
  mode: main-chat                  # framework default for all providers
  provider-overrides:
    Gemini:
      mode: strict                 # Gemini gets a dedicated orchestrator subagent
```

Providers without an entry (or without `mode` set) inherit the global `orchestrator.mode`.
Configurable via the Admin UI under Orchestrator → Provider Overrides.

### Synchronization Variables

Custom project variables for conditional feature activation:

| Variable | Type | Purpose |
|----------|------|---------|
| `WEB_PROJECT_ENABLED` | boolean | When true, activates web-specific verification steps in developer, senior-developer, performance-optimizer agents (Playwright MCP, visual regression, accessibility checks) |

Set in `.meta-config/project.yaml` under `variables:`
```yaml
variables:
  WEB_PROJECT_ENABLED: true
```

## Workflows

| ID | Workflow | Orchestrator Agent | Stages |
|----|----------|-------------------|--------|
| **A** | New Feature | feature | Branch → REQ → Test → Dev → Validate → PR |
| **B** | Bugfix | feature | Branch → REQ → Test → Dev → Validate → PR |
| **C** | Code Audit | code-reviewer | Review → blast-radius → quality scan |
| **E** | Refactoring | feature | Branch → REQ → Dev → Test → Validate → PR |
| **H1** | Agent Sync | agent-meta-manager | sync.py → commit "chore: regenerate agents" |
| **H2** | Upgrade | agent-meta-manager | Read workflow → apply |
| **I** | Ideation | ideation | Explore → sharpen vision → handoff to requirements |
| **K** | Meta-Feedback | meta-feedback | Collect feedback → create GitHub issue |
| **L** | GitHub Issue | orchestrator | Read → requirements → dev → test → validate → close |
| **M** | Scout Ecosystem | agent-meta-scout | Search new skills/roles/rules/patterns |
| **O** | Log Analysis | log-analyzer | Analyze → cluster → delegate findings |
| **P** | Project Issue | feedback | Create standardized bug/feature issue |
| **U** | SE Cascade | orchestrator (SE-Mode) | 8-stage V-model: stakeholder → architecture → implementation → V&V |

## Contributing

### Branch Policy

**Never commit directly to `main`** for template, rule, script, or sync changes. Always create a feature branch.

Direct commits on `main` allowed only for:
- Version bumps (VERSION, CHANGELOG.md, README.md)
- Single-line typo fixes (with user confirmation)
- Post-merge maintenance

**Always create a feature branch:**
```bash
git checkout -b feat/my-change
git add .
git commit -m "feat: add my feature"
git push -u origin feat/my-change
```

### Development Workflow

1. Create a branch (`feat/...`, `fix/...`, `refactor/...`, `docs/...`)
2. Edit templates in `agents/1-generic/` or configuration in `config/`
3. Bump the template version in frontmatter (major/minor/patch per semver)
4. Run consistency check: `python scripts/consistency-check.py`
5. Verify generation: `python scripts/sync.py --dry-run`
6. Commit with Conventional Commits format
7. Create a PR

### Conventional Commits

```
<type>(REQ-xxx): <description>   ← with req-traceability
<type>: <description>            ← without req-traceability
```

| Type | Description | REQ-ID |
|------|-------------|--------|
| `feat` | New feature | When req-traceability active |
| `fix` | Bug fix | When req-traceability active |
| `refactor` | Refactoring without behavior change | When req-traceability active |
| `test` | Add or modify tests | When req-traceability active |
| `chore` | Maintenance, dependencies, versions | Never |
| `docs` | Documentation | Never |
| `ci` | CI/CD changes | Never |

### Development Conventions

- **No external Python dependencies** — stdlib only (except tests)
- **Agent templates** use YAML frontmatter with semver versioning
- **Placeholders** follow `{{GROSS_MIT_UNTERSTRICH}}` naming convention
- **Generated output** (`.claude/agents/`, `.opencode/agents/`, etc.) is never edited manually
- **Validation:** `sync.py --dry-run` and `consistency-check.py` are your test suite

## License

MIT
