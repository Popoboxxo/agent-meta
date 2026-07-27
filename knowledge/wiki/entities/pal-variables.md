---
type: "API Reference"
title: "Provider Abstraction Layer (PAL) Variables"
description: "The Agent-Meta Framework uses placeholders (Variables) in the agent templates, which are resolved at build-time (sync.py) based on the target provider. This allows maintaining..."
tags: [api]
timestamp: "2026-07-27"
resource: "../../sources/docs/api/pal-variables.md"
migrated_from: "docs/api/pal-variables.md"
---
# Provider Abstraction Layer (PAL) Variables

The Agent-Meta Framework uses placeholders (Variables) in the agent templates, which are resolved at build-time (`sync.py`) based on the target provider. This allows maintaining a unified, provider-agnostic agent definition for Claude, Gemini, Opencode, Continue, and Copilot.

All placeholders follow the naming convention `{{GROSS_MIT_UNTERSTRICH}}`.

## PAL Mapping Table

| Placeholder | Resolves to (Purpose) | Example Claude | Example Gemini |
|-------------|-----------------------|----------------|----------------|
| `{{PAL_DELEGATE}}` | Provider-specific syntax for delegating to another agent. Isolates differences in provider delegation tools. | `@developer` | `/invoke developer` |
| `{{PAL_FANOUT}}` | Syntax for parallel execution of *multiple agents of the same type* (e.g., running tests on multiple shards). | `run parallel @tester` | `/fanout tester` |
| `{{PAL_PARALLEL_GROUP}}` | Syntax for parallel execution of *different agent types* (e.g., frontend and backend developers in parallel). | `group @frontend @backend` | `/group frontend backend` |
| `{{PAL_FALLBACK}}` | Fallback behavior in case specific tools are unavailable in the provider. Guarantees Graceful Degradation. | `use CLI fallback` | `use python fallback` |
| `{{PAL_TOOL_PREAMBLE}}` | Introductory text/block for tool documentation in the context prompt, adapted to provider expectations. | `<tools>...` | `[Tools]...` |

## Configuration

The resolution of these variables happens in `scripts/lib/delegation_syntax.py`.
Specific project variables can additionally be defined in the `.meta-config/project.yaml` under `variables:` (e.g., `WEB_PROJECT_ENABLED`).