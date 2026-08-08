# Standalone Agent Personas

Pre-rendered, fully self-contained copies of [agent-meta](https://github.com/Popoboxxo/agent-meta)'s generic agent personas — no Python, no `sync.py`, no repo clone required.

## How to use

1. Pick the role below that matches what you need help with.
2. Open its file (or ask a browsing-capable chat AI to fetch it from this repo directly).
3. Paste the whole file as your system prompt / custom instructions.

**Scope note:** each persona is a solo snapshot. No multi-agent delegation, no DoD gate, no A2A protocol, no project-specific config — for the full pipeline (multi-agent orchestration, project-aware context, quality gates), see the [main repo](https://github.com/Popoboxxo/agent-meta).

## Available roles

| Role | Description | File |
|------|-------------|------|
| `developer` | Use when a REQ-ID or clearly scoped task needs direct feature/bugfix implementation. | [`agents/developer.md`](agents/developer.md) |
| `senior-developer` | Complex features, architecture decisions, hard bugs and cross-cutting refactorings. | [`agents/senior-developer.md`](agents/senior-developer.md) |
| `documenter` | Maintains CODEBASE_OVERVIEW.md, ARCHITECTURE.md, README.md and session insights. | [`agents/documenter.md`](agents/documenter.md) |
| `technical-writer` | External developer- and user-facing documentation: API references, getting-started guides, SDK docs, tutorials, CLI help pages, user-facing release notes and UX microcopy. | [`agents/technical-writer.md`](agents/technical-writer.md) |
| `requirements` | Capture requirements, assign REQ-IDs, maintain REQUIREMENTS.md and check traceability. | [`agents/requirements.md`](agents/requirements.md) |
| `tester` | Isolated unit tests with mocks/stubs following a TDD workflow. | [`agents/tester.md`](agents/tester.md) |
| `proofreader` | Proofreading: pure correctness pass on existing text — spelling, grammar, punctuation. | [`agents/proofreader.md`](agents/proofreader.md) |
| `copyeditor` | Copyediting: style, sentence structure, word repetition, narrative/argumentative flow, and content consistency on top of a clean text. | [`agents/copyeditor.md`](agents/copyeditor.md) |

---
Generated from agent-meta v0.92.0. Regenerate via `python scripts/sync.py --render-standalone` (or the Admin UI's Sync page).
