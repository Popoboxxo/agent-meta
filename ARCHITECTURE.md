# agent-meta — Architecture Overview

> Repo version: **0.96.0** — content last substantively reviewed: 2026-08-25
> Full reference: [ARCHITECTURE.full.md](ARCHITECTURE.full.md)

---

## Diagrams

| # | Diagram | Description |
|---|---|---------|-------------|
| 1 | [Layer Model](docs/architecture/01-layer-model.md) | Override priority of the 4 layers (0-external → 3-project) + rules/hooks |
| 2 | [Sync Flow](docs/architecture/02-sync-flow.md) | How `sync.py` fills the target project from agent-meta sources |
| 3 | [Agent Roles](docs/architecture/03-agent-roles.md) | All agent roles and responsibilities |
| 4 | [Dev Workflow](docs/architecture/04-dev-workflow.md) | Standard feature workflow as a sequence diagram |
| 5 | [External Skills](docs/architecture/05-external-skills.md) | Submodule → config → wrapper → target project |
| 6 | [Versioning](docs/architecture/06-versioning.md) | Repo, agent, and snippet versioning |
| 7 | [SE Cascade](docs/architecture/07-se-cascade.md) | Recursive 6-stage black-box → white-box decomposition |
| 8 | [Preset System](docs/architecture/08-preset-system.md) | Precedence pattern for DoD, tier, rules, conventions presets |
| 9 | [Quality Pipelines](docs/architecture/09-quality-pipelines.md) | 7 pre-defined workflows (feature-lifecycle, bugfix, refactor, etc.) |
| 10 | [MCP & Admin UI](docs/architecture/10-mcp-and-admin-ui.md) | MCP server activation and live configuration dashboard |
| 11 | [Viz-Logging MCP](docs/concepts/viz-logging-mcp.md) | MCP-based event logging with CLI fallback |
| 12 | [A2A Protocol](docs/concepts/a2a-handoff-protocol.md) | Structured JSON envelopes for agent-to-agent contracts |

---

## Repository Structure

Run `rtk ls agents/` for the live tree. Conceptual layout:

- `agents/{0-external,1-generic,2-platform}/` — Agent templates
- `rules/{0-external,1-generic,2-platform}/` — Auto-loaded rules
- `scripts/` — `sync.py`, `viz-logger.py`, `admin-server.py`
- `config/` — PAL syntax, capabilities, bootstrap, role defaults
- `docs/architecture/` — Diagrams and deep-dives
- `external/` — Git submodules for skills

---

## SE-Agent Cascade

A fractal, recursive system that turns stakeholder requirements into implementable components through a 6-stage black-box → white-box decomposition. The orchestrator drives the cascade when SE mode is enabled.

→ Details: `docs/architecture/07-se-cascade.md`

---

## Viz-Logging MCP

Agent events (`agent_start`, `delegate_out`, `agent_end`) are logged via an MCP tool with a CLI fallback. A short prompt block (~10 lines) is injected into each agent template at sync time.

→ Details: `docs/concepts/viz-logging-mcp.md`

---

## Provider Abstraction Layer (PAL)

PAL keeps provider-specific delegation syntax out of generic templates. It maps abstract `{{PAL_*}}` placeholders to native calls via `config/delegation-syntax.yaml`, resolves capabilities via `config/provider-capabilities.yaml`, and handles provider-specific bootstrap.

→ Full spec: `ARCHITECTURE.full.md`  
→ Config: `config/delegation-syntax.yaml`, `config/provider-capabilities.yaml`, `config/provider-bootstrap.yaml`

---

## A2A Handoff Protocol

Agent-to-agent communication uses structured JSON envelopes. The orchestrator builds envelopes, supports FANOUT/BATCH/BARRIER/PIPELINE/REPEAT_UNTIL patterns, and validates payloads against schemas in `schemas/handoffs/`.

→ Full spec: `docs/concepts/a2a-handoff-protocol.md`  
→ Envelope schema: `schemas/a2a-handoff.schema.json`

---

## Keyless Discovery & Pricing Overlay

Model catalog and pricing are fetched keylessly from OpenRouter (and OpenCode Zen), cached in `config/generated/model-registry.json`, and can be overridden via `config/pricing-overlay.yaml`.

→ Details: `ARCHITECTURE.full.md`

---

## Update Instructions

On every major release, update:
- Version and date in the header
- This file if new top-level concepts are added
- Diagrams in `docs/architecture/` (new roles, skills, layers)
