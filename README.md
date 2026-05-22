# agent-meta

> [!WARNING]
> ## VibeCoding Experiment — Read Before Using
> This repository is intentionally run as a **VibeCoding experiment**.
> The primary goal is to demonstrate both the **benefits** and **risks** of LLM-driven development on a real but minimal project around Sharkord.
>
> ### Ground rules of this repo
> - **Source code interventions should happen only in absolute emergencies.**
> - The preferred workflow is to explore how far we can get with LLM providers, agent orchestration, and prompt-driven iteration.
> - This project is a **sandbox/playground** for experimenting with different AI coding styles, tooling, and operational patterns.
> - "Production hardening" is not the primary objective; learning effects and transparent trade-offs are.
> - And yes: it is also just a fun way to spend an evening with the Dudes on Sharkord, trying out weird and funny plugin ideas. :)
>
> In short: this is a practical lab setup around Sharkord to evaluate VibeCoding methods, compare approaches, and optionally extend a cool project while making limitations visible.

---

Central meta-repository for standardizing and reusing Claude agent roles across all projects.
Provides generic agent templates that are instantiated per project via `sync.py`.

**Current version:** `0.49.0`

---

## What is agent-meta?

`agent-meta` is a Git submodule that projects include to get a standardized multi-agent system — usable across multiple AI providers from a single source of truth.

**Core principle: Define once, transform per provider.**
Agent roles, rules, skills, hooks, and commands are defined once in provider-agnostic source files (`agents/1-generic/`, `rules/1-generic/`, ...). `sync.py` transforms them at build time into provider-ready artifacts:

| Provider | Agents | Rules | Commands |
|----------|--------|-------|----------|
| Claude Code | `.claude/agents/` | `.claude/rules/` | `.claude/commands/` |
| Gemini CLI | `.gemini/agents/` | `.gemini/rules/` | `.gemini/commands/` |
| Opencode | `.opencode/agents/` | *(embedded in AGENTS.md)* | `.opencode/commands/` |
| Continue | `.continue/agents/` | `.continue/rules/` | `.continue/prompts/` |

Platform- and project-specific layers stack on top of the generic definitions — but always remain provider-agnostic in their source. No knowledge needs to be maintained twice.

It provides:

- **Generic agent templates** for orchestrator, developer, tester, validator, requirements engineer, documenter, release, docker, and systems engineering (SE) cascade roles
- **Orchestrator-First Architecture** (Beta): Universal task decomposition with parallel FANOUT/PARALLEL_GROUP dispatch, provider-agnostic across Claude, Opencode, Gemini, and Continue
- **Platform-specific overrides** (e.g., Sharkord plugins) that extend generic agents
- **A sync script** (`sync.py`) that generates provider-ready agent files from a single set of templates
- **An extension system** that lets projects add project-specific knowledge without touching generated files
- **Agent visualization** (opt-in): auto-generated mindmaps of all agents + dynamic session tracking with event reports (Gantt, sequence diagrams, live watch)

---

## Three-Layer Architecture

```
1-generic/    Universal agents — generated for every project
2-platform/   Platform-specific — overrides generic agents for a specific platform
3-project/    Project-specific — either full overrides or additive extensions
```

**Override priority:**
```
1-generic  ←  overridden by  →  2-platform  ←  overridden by  →  3-project/<role>.md
```

**Extensions (additive, not override):**
```
generated agent  +  .claude/3-project/<prefix>-<role>-ext.md  =  full agent context
```

---

## Quick Start

> **First time setup?** Use [howto/setup/first-steps.md](howto/setup/first-steps.md) — hand it to your AI assistant
> and say: "Help me set up agent-meta in this project." The assistant will guide you interactively.

### 1. Add as submodule

```bash
git submodule add <repo-url> .agent-meta
```

```bash
cd .agent-meta && git checkout v0.28.1
```

```bash
cd ..
```

```bash
git submodule update --init --recursive
```

### 2. Create config

```bash
mkdir -p .meta-config
cp .agent-meta/howto/configs/project.yaml.example .meta-config/project.yaml
```

Fill in your project values — see [howto/setup/first-steps.md](howto/setup/first-steps.md) for a guided walkthrough.

### 3. Generate agents

```bash
py .agent-meta/scripts/sync.py --config .meta-config/project.yaml --init
```

```bash
cat sync.log
```

Agents are written to `.claude/agents/`. Never edit them manually — they are regenerated on every sync.

---

## Systems Engineering Cascade (Beta v0.49.0)

A recursive, fractal systems engineering workflow for model-based system decomposition across L1–L3.

### How it works

The SE cascade treats every level as an identical **system cell**:

1. **`se-requirements`** — Captures stakeholder needs and formalizes L1 black-box requirements
2. **`se-architect`** — Decomposes black-boxes into white-box architectures with sub-components, domains (software/hardware/mechanics/system), and interfaces
3. **`se-critic`** — Quality gate: completeness, consistency, traceability, verifiability (max 3 iterations)
4. **`se-interface-mgr`** — Registers interfaces, validates contracts, generates propagation maps for parallel branches
5. **`se-termination`** — Decides per sub-component: leaf node or spawn next cell (n+1)
6. **`se-orchestrator`** — Coordinates the entire 6-stage breakdown with context hygiene and parallel cell execution

### Recursive Cell Spawning

White-box elements of level n become black-box requirements of level n+1. Each cell receives only its parent requirement + neighbor interfaces (~2k token limit) to prevent context drift.

### Protection Mechanisms

- `max_depth: 5` — hard recursion limit
- `max_total_cells: 20` — global cell budget
- `max_critic_iterations: 3` — bounded correction loops
- `max_parallel_cells: 4` — parallel execution cap

### Documentation

- [docs/architecture/07-se-cascade.md](docs/architecture/07-se-cascade.md) — Architecture deep-dive
- [howto/se-workflow.md](howto/se-workflow.md) — Workflow guide with Mermaid diagrams
- [howto/se-blackbox-to-whitebox.md](howto/se-blackbox-to-whitebox.md) — BB→WB transition methodology
- [howto/se-interface-management.md](howto/se-interface-management.md) — Interface propagation explained
- [howto/se-mcp-adapters.md](howto/se-mcp-adapters.md) — MCP adapter concept for Phase 3

---

## Agent Visualization (Opt-in)

Visualize your agent fleet, their delegations, and runtime sessions.

### Static Mindmap

Auto-generated on every sync when `viz.enabled: true`:

```bash
py .agent-meta/scripts/sync.py --viz
```

- `docs/agent-mindmap.md` — Mermaid diagram (renders natively on GitHub)
- `docs/agent-graph.html` — Interactive dark-mode graph with agent details

### Dynamic Session Tracking

Enable event logging in `project.yaml`:

```yaml
viz:
  enabled: true
  mode: "full"        # off | static | dynamic | full
```

When `dynamic` or `full`, every generated agent receives a prompt block that instructs it to log events (`agent_start`, `delegate`, `agent_end`, `tool_call`) to `.meta-viz/events.jsonl`.

### Session Reports

```bash
# Live terminal watch
py .agent-meta/scripts/viz-report.py --watch

# Live Dashboard (browser, auto-refreshes via API)
py scripts/viz-server.py toggle

# Toggle mode and trigger sync
/viz-toggle dynamic
```

Sessions are gitignored and auto-cleaned after `retention_days`. See [howto/agent-visualization.md](howto/agent-visualization.md) for the full guide.

---

## Orchestrator-First Architecture (Beta v3.0.0)

The orchestrator is the universal entry point for all development tasks. Instead of the main session handling work directly, every task flows through the orchestrator, which decomposes, parallelizes, and delegates to specialized worker agents.

### Task Decomposition & Parallel Execution

The orchestrator automatically splits multi-tasks into independent sub-tasks and dispatches them in parallel:

| Pattern | Use Case | Example |
|---------|----------|---------|
| **FANOUT** | N instances of same agent type | "Fix bugs A, B, C" → 3× `developer` parallel |
| **PARALLEL_GROUP** | Different agent types simultaneously | "Fix A + test B" → `developer` ∥ `tester` |
| **PIPELINE** | Sequential with dependencies | "Feature with tests" → requirements → tester → dev → tester |
| **LIFECYCLE** | Complete end-to-end workflow | "Feature Y complete" → `feature` agent orchestrates |
| **BARRIER** | Synchronization point | Wait for all parallel agents before next step |

**Provider-agnostic:** Same decision logic for Claude, Opencode, Gemini, and Continue (Continue falls back to sequential).

### Unknown Intent Protocol

When the orchestrator cannot classify an intent, it follows a configurable fallback chain:

```yaml
orchestrator:
  enabled: true
  strict: true
  unknown-fallback:
    meta-feedback: true   # Send anonymized feedback to agent-meta
    main-chat: true      # Allow main chat to handle the task
    ask-user: false      # Ask user for preference
```

**Fallback priority:**
1. `ask-user=true` → Always ask user first
2. `strict=true` + `meta-feedback=true` → Feedback + rephrase request
3. `strict=false` + `main-chat=true` → Main-Chat handles it + optional feedback
4. No fallback enabled → Ask for clarification

### User Override

Users can bypass the orchestrator at any time with explicit phrases:

- "Not delegate" / "Do it here" / "No orchestrator" / "Without orchestrator"
- "I want to work here" / "Don't delegate"

The main chat then acts as a classical agent for that request. After completion, the user can choose whether to persist this preference.

### Orchestration Testing

Validate the entire delegation pipeline without real agent execution:

```bash
/test-orchestration                    # All tests for active provider
/test-orchestration --scenario=parallel # Parallel dispatch tests only
/test-orchestration --verbose --viz     # All tests with Viz-Log
```

Tests cover: Intent routing, task decomposition, parallel dispatch, provider syntax, Viz-Log integration.

---

## Project Extensions

Extensions let you add project-specific knowledge to a generated agent. The extension file has two parts:

- **Managed block** — auto-generated from config variables, updated via `--update-ext`
- **Project section** — handwritten, never touched by sync.py

```bash
# Create extension for one role
py .agent-meta/scripts/sync.py --create-ext developer

# Create extensions for all roles
py .agent-meta/scripts/sync.py --create-ext all

# Update managed blocks after config changes
py .agent-meta/scripts/sync.py --update-ext
```

Extensions live in `.claude/3-project/<prefix>-<role>-ext.md` in your project — never in this repo.

---

## MCP Servers

agent-meta manages MCP servers as a first-class framework concept across all providers.

### How it works

1. **Registry** — `config/mcp-registry.yaml` defines available servers (tools, connection, secrets)
2. **Activation** — activate per project via `mcp-servers:` in `project.yaml` or implicitly via platform bundles
3. **Sync** — `sync.py` generates everything automatically:
   - Rule files (`mcp-<server>.md`) per provider with allowed/blocked tools and agent hints
   - Committed provider configs with `${ENV_VAR}` references (safe to commit)
   - Gitignored local configs populated from `.meta-config/secrets.local.yaml` (actual values)
   - `.gitignore` managed block entries for all secrets files

```yaml
# .meta-config/project.yaml
mcp-servers:
  - home-assistant
  - influxdb
```

```bash
# On first --init: .meta-config/secrets.local.yaml is generated automatically
py .agent-meta/scripts/sync.py --init
# Fill in secrets, then re-sync:
py .agent-meta/scripts/sync.py
```

**Security:** `sync.py` raises a hard error (`SyncError`) when a real secret is detected in a committed file. Set `allow-committed-secrets: true` in `project.yaml` to downgrade to a warning (not recommended).

See [howto/mcp-setup.md](howto/mcp-setup.md) for full documentation.

---

## Upgrading

```bash
cat .agent-meta/VERSION
```

```bash
cd .agent-meta && git checkout v<new-version>
```

```bash
cd ..
```

Update config version field in `.meta-config/project.yaml`: `agent-meta-version: "<new-version>"`

```bash
py .agent-meta/scripts/sync.py --config .meta-config/project.yaml --dry-run
```

```bash
py .agent-meta/scripts/sync.py --config .meta-config/project.yaml
```

```bash
py .agent-meta/scripts/sync.py --config .meta-config/project.yaml --update-ext
```

See [howto/setup/upgrade-guide.md](howto/setup/upgrade-guide.md) for details.

---

## Repository Structure

```
agent-meta/
  agents/
    0-external/       <- wrapper template for external skill agents
    1-generic/        <- universal agent templates
    2-platform/       <- platform-specific overrides (e.g. sharkord-docker.md)
    3-project/        <- intentionally empty (extensions live in your project)
  config/             <- framework config (managed by agent-meta, do not edit manually)
    project.yaml                <- agent-meta self-hosting config
    role-defaults.yaml          <- default model/memory/permissionMode per role
    dod-presets.yaml            <- DoD quality presets
    ai-providers.yaml           <- provider settings (Claude, Gemini, Opencode, Continue)
    mcp-registry.yaml           <- global MCP server catalog (tools, connection, secrets)
    skills-registry.yaml        <- external skills registry (approved/pinned)
    project-config.schema.json  <- JSON Schema for project.yaml
  external/           <- Git submodules for external skill repos (pinned commits)
  hooks/
    0-external/       <- hooks from external skill repos
    1-generic/        <- universal hooks (e.g. dod-push-check.sh)
    2-platform/       <- platform-specific hook overrides
  platform-configs/
    *.defaults.yaml   <- default values for {{platform.*}} placeholders
  rules/
    0-external/       <- rules from external skill repos
    1-generic/        <- universal rules (auto-loaded into every agent context)
    2-platform/       <- platform-specific rule overrides
  snippets/
    tester/           <- language-specific test snippets (bun-typescript, pytest-python)
    developer/        <- language-specific code pattern snippets
  speech/
    short.md          <- facts-only style (no filler)
    childish.md       <- playful, toy/animal analogies
    caveman.md        <- caveman style: short, direct
    asozial.md        <- technically correct, dripping with contempt
    submissive.md     <- completely devoted and submissive
  templates/
    managed-block.md              <- extension managed-block template
    managed-block-project-stub.md <- project area stub for new extensions
    claude-md-managed.md          <- CLAUDE.md managed-block template
  docs/
    architecture/       <- architecture deep-dives (layer model, sync flow, roles, ...)
    providers/
      gemini-cli.md     <- Gemini CLI: features, limits, config reference
      multi-provider.md <- multi-provider setup and comparison
  howto/
    setup/              <- first-time setup, instantiation, upgrade
      first-steps.md
      instantiate-project.md
      upgrade-guide.md
    features/
      agent-memory.md   <- persistent agent memory: scopes, config, best practices
      config-layout.md
    features/           <- feature-specific how-tos
      agent-composition.md
      agent-delegation-map.md
      agent-isolation.md
      agent-memory.md
      agent-versioning.md
      external-skills.md
      hooks.md
      lifecycle-triggers.md
      platform-config.md
      rules.md
      sync-concept.md
    configs/            <- templates and starter configs (never edit directly)
      CLAUDE.project-template.md
      CLAUDE.personal-template.md
      GEMINI.project-template.md
      GEMINI.settings-template.json
      CONTINUE.project-template.md
      CONTINUE.config-template.yaml
      project.yaml.example        <- starter config for new projects
  scripts/
    sync.py           <- CLI entrypoint (argparse + main)
    lib/
      agents.py       <- frontmatter, composition, sync_agents
      config.py       <- load_config, build_variables, substitute
      context.py      <- init_claude_md, sync_context, gitignore, sync_snippets
      dod.py          <- load_dod_presets, resolve_dod
      extensions.py   <- create_extension, update_extensions
      hooks.py        <- sync_hooks, create_hook
      io.py           <- YAML/JSON loader
      log.py          <- SyncLog
      platform.py     <- load_platform_config, substitute_platform
      providers.py    <- load_providers_config, resolve_providers
      roles.py        <- load_roles_config, build_role_map
      rules.py        <- sync_rules, sync_speech_mode, create_rule
      skills.py       <- external skills: load, sync, add
  VERSION
  CHANGELOG.md
```

**Config layout:**

| Location | Owned by | Purpose |
|----------|----------|---------|
| `.agent-meta/config/` | agent-meta framework | Role defaults, providers, DoD presets, skill registry — do not edit |
| `.meta-config/project.yaml` | Your project | Project identity, variables, active roles, providers, orchestrator config |
| `.claude/platform-config.yaml` | Your project | Platform-specific value overrides (`{{platform.*}}` placeholders) |

---

## Supported Platforms

| Platform | Agents |
|----------|--------|
| Generic | orchestrator, developer, tester, validator, requirements, documenter, meta-feedback, release, docker, git, ideation, feature, agent-meta-manager, agent-meta-scout, openscad-developer, se-orchestrator, se-requirements, se-architect, se-critic, se-interface-mgr, se-termination |
| Sharkord | sharkord-docker, sharkord-release |

---

## Agent Roles

| Role | Responsibility |
|------|---------------|
| `orchestrator` | Universal router — classifies intents, decomposes tasks, parallelizes with FANOUT/PARALLEL_GROUP, delegates to workers |
| `developer` | REQ-driven implementation, code conventions |
| `tester` | TDD, test suite, coverage per REQ-ID |
| `validator` | DoD check, traceability audit, code quality |
| `requirements` | Requirement intake, REQ-IDs, REQUIREMENTS.md |
| `documenter` | CODEBASE_OVERVIEW, architecture docs, conclusions |
| `meta-feedback` | Collect framework feedback, create GitHub Issues in agent-meta |
| `release` | Versioning, changelog, GitHub release |
| `docker` | Dev stack, test stack, binary management |
| `git` | Commits, branches, tags, push/pull and all Git operations |
| `ideation` | Explore new ideas, sharpen vision, hand off to requirements |
| `feature` | New feature end-to-end: branch → REQ → TDD → dev → validate → PR |
| `agent-meta-manager` | Manage agent-meta: upgrade, sync, feedback, create project-specific agents |
| `agent-meta-scout` | Scout the Claude ecosystem for new skills, roles, rules and patterns |
| `openscad-developer` | Parametric 3D models in OpenSCAD, render-inspect-refine via MCP, print optimization |
| `se-orchestrator` | Coordinates the 6-level recursive systems engineering cascade |
| `se-requirements` | Elicits stakeholder needs and formalizes L1 black-box requirements |
| `se-architect` | Decomposes black-boxes into white-box architectures (L1/L2/L3) |
| `se-critic` | Audits decompositions: completeness, consistency, traceability, verifiability |
| `se-interface-mgr` | Manages interface contracts and propagation maps across cascade levels |
| `se-termination` | Deterministic termination at L3 component requirements |
