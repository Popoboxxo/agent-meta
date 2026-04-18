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

**Current version:** `0.26.0`

---

## What is agent-meta?

`agent-meta` is a Git submodule that projects include to get a standardized multi-agent system for Claude Code. It provides:

- **Generic agent templates** for orchestrator, developer, tester, validator, requirements engineer, documenter, release, and docker roles
- **Platform-specific overrides** (e.g., Sharkord plugins) that extend generic agents
- **A sync script** (`sync.py`) that generates project-ready agent files into `.claude/agents/`
- **An extension system** that lets projects add project-specific knowledge without touching generated files

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

> **First time setup?** Use [howto/first-steps.md](howto/first-steps.md) — hand it to your AI assistant
> and say: "Help me set up agent-meta in this project." The assistant will guide you interactively.

### 1. Add as submodule

```bash
git submodule add <repo-url> .agent-meta
```

```bash
cd .agent-meta && git checkout v0.26.0
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
cp .agent-meta/howto/project.yaml.example .meta-config/project.yaml
```

Fill in your project values — see [howto/first-steps.md](howto/first-steps.md) for a guided walkthrough.

### 3. Generate agents

```bash
py .agent-meta/scripts/sync.py --config .meta-config/project.yaml --init
```

```bash
cat sync.log
```

Agents are written to `.claude/agents/`. Never edit them manually — they are regenerated on every sync.

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

See [howto/upgrade-guide.md](howto/upgrade-guide.md) for details.

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
    ai-providers.yaml           <- provider settings (Claude, Gemini, Continue)
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
  templates/
    managed-block.md              <- extension managed-block template
    managed-block-project-stub.md <- project area stub for new extensions
    claude-md-managed.md          <- CLAUDE.md managed-block template
  howto/
    first-steps.md
    instantiate-project.md
    agent-composition.md
    agent-delegation-map.md
    agent-isolation.md
    agent-memory.md
    agent-versioning.md
    external-skills.md
    hooks.md
    multi-provider.md
    platform-config.md
    rules.md
    sync-concept.md
    upgrade-guide.md
    config-layout.md
    CLAUDE.project-template.md
    CLAUDE.personal-template.md
    project.yaml.example          <- starter config template for new projects
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
| `.meta-config/project.yaml` | Your project | Project identity, variables, active roles, providers |
| `.claude/platform-config.yaml` | Your project | Platform-specific value overrides (`{{platform.*}}` placeholders) |

---

## Supported Platforms

| Platform | Agents |
|----------|--------|
| Generic | orchestrator, developer, tester, validator, requirements, documenter, meta-feedback, release, docker, git, ideation, feature, agent-meta-manager, agent-meta-scout, openscad-developer |
| Sharkord | sharkord-docker, sharkord-release |

---

## Agent Roles

| Role | Responsibility |
|------|---------------|
| `orchestrator` | Coordinates all agents, enforces DoD, manages workflows |
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
