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

**Current version:** `0.9.0`

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

### 1. Add as submodule

```bash
git submodule add <repo-url> .agent-meta
cd .agent-meta && git checkout v0.9.0 && cd ..
```

### 2. Create config

```bash
cp .agent-meta/agent-meta.config.example.json agent-meta.config.json
# Fill in your project values
```

### 3. Generate agents

```bash
py .agent-meta/scripts/sync.py --config agent-meta.config.json
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
py .agent-meta/scripts/sync.py --config agent-meta.config.json --create-ext developer

# Create extensions for all roles
py .agent-meta/scripts/sync.py --config agent-meta.config.json --create-ext all

# Update managed blocks after config changes
py .agent-meta/scripts/sync.py --config agent-meta.config.json --update-ext
```

Extensions live in `.claude/3-project/<prefix>-<role>-ext.md` in your project — never in this repo.

---

## Upgrading

```bash
# Check current version
cat .agent-meta/VERSION

# Pull new version
cd .agent-meta && git checkout v<new-version> && cd ..

# Update config version field
# "agent-meta-version": "<new-version>"

# Dry-run to check for missing variables
py .agent-meta/scripts/sync.py --config agent-meta.config.json --dry-run

# Regenerate agents
py .agent-meta/scripts/sync.py --config agent-meta.config.json

# Update extension managed blocks
py .agent-meta/scripts/sync.py --config agent-meta.config.json --update-ext
```

See [howto/upgrade-guide.md](howto/upgrade-guide.md) for details.

---

## Repository Structure

```
agent-meta/
  agents/
    1-generic/        ← universal agent templates
    2-platform/       ← platform-specific overrides (e.g. sharkord-docker.md)
    3-project/        ← intentionally empty (extensions live in your project)
  howto/
    instantiate-project.md
    upgrade-guide.md
    CLAUDE.project-template.md
    sync-concept.md
  scripts/
    sync.py           ← agent generator
  agent-meta.config.example.json
  VERSION
  CHANGELOG.md
```

---

## Supported Platforms

| Platform | Agents |
|----------|--------|
| Generic | orchestrator, developer, tester, validator, requirements, documenter, release, docker |
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
| `release` | Versioning, changelog, GitHub release |
| `docker` | Dev stack, test stack, binary management |
