# agent-meta

[![Version](https://img.shields.io/badge/version-0.55.2-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.x-green.svg)]()
[![License](https://img.shields.io/badge/license-MIT-gray.svg)]()

> Standardized AI agent templates with multi-provider support, orchestrator-first architecture, and Systems Engineering cascade.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
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

### Orchestrator Dispatch Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| **FANOUT** | N instances of same agent type in parallel | 3× `developer` for 3 bugfixes |
| **PARALLEL_GROUP** | Different agent types simultaneously | `developer` ∥ `tester` |
| **BARRIER** | Wait for all parallel tasks before proceeding | Collect results from FANOUT |
| **PIPELINE** | Sequential steps with dependencies | requirements → dev → test |
| **LIFECYCLE** | Complete end-to-end feature workflow | Branch → REQ → TDD → Dev → Validate → PR |

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

## Quick Start

```bash
# 1. Add as submodule
git submodule add https://github.com/Popoboxxo/agent-meta .agent-meta
cd .agent-meta && git checkout v0.55.2 && cd ..

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
    dod-presets.yaml         # DoD quality presets
    mcp-registry.yaml        # Global MCP server catalog
    provider-tools.yaml      # Per-provider tool capability whitelists
    skills-registry.yaml     # External skills registry
    rules-presets.yaml       # Rule embedding presets per provider
    export.yaml              # Export target configuration
    project-config.schema.json  # JSON Schema for project.yaml validation
  docs/                      # Documentation
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
    sync.py                  # Main generation script (CLI entrypoint)
    viz-logger.py            # MCP server & CLI fallback for agent event logging
    viz-logger-mcp.mjs       # HTTP/SSE MCP transport for OpenCode (Windows)
    viz-server.py            # Live dashboard HTTP server
    viz-report.py            # Session report generator (terminal/HTML/JSON)
    consistency-check.py     # Deterministic template consistency validation
    lib/                     # Sync library modules (config, agents, rules, etc.)
  speech/                    # Communication style mode files
  templates/                 # Managed-block templates
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
