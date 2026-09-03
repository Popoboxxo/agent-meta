---
type: "Architecture"
title: "Development Workflow"
description: "Die feature-lifecycle-Pipeline ist ein Shortcut — sie deckt denselben Lifecycle wie Workflow A ab, aber als deklarative Pipeline-Definition mit festem Stage-Ablauf inkl. Branch + PR."
tags: [architecture, "status:active"]
timestamp: "2026-09-03"
resource: "../../sources/docs/architecture/04-dev-workflow.md"
migrated_from: "docs/architecture/04-dev-workflow.md"
migration_note: "Re-Ingest 2026-09-03 (Issue #651): vollständig aus aktueller Quelle resynct — der frühere eigenständige 'feature'-Agent (8-Schritt-Workflow-Agent) wurde durch die deklarative 'feature-lifecycle'-Pipeline ersetzt (config/role-defaults.yaml, engine: scripts/lib/pipelines.py)."
---
# Development Workflow

> [Back to Architecture Overview](../../../ARCHITECTURE.md)

## Workflow A: Neues Feature (via orchestrator)

```mermaid
sequenceDiagram
    actor User
    participant ORC as orchestrator
    participant REQ as requirements
    participant TST as tester
    participant DEV as developer
    participant VAL as validator
    participant DOC as documenter
    participant GIT as git

    User->>ORC: new feature request
    ORC->>REQ: assign REQ-ID
    REQ-->>ORC: REQ-042 done
    ORC->>TST: write tests TDD red
    TST-->>ORC: tests written
    ORC->>DEV: implement
    DEV-->>ORC: code done
    ORC->>TST: run tests
    TST-->>ORC: tests green
    ORC->>VAL: DoD check
    VAL-->>ORC: DoD passed
    ORC->>DOC: update docs
    DOC-->>ORC: docs updated
    ORC->>GIT: commit and push
    GIT-->>ORC: committed
    ORC-->>User: feature complete
```

## Workflow B: Neues Feature (via feature-lifecycle Pipeline)

Die `feature-lifecycle`-Pipeline ist ein **Shortcut** — sie deckt denselben Lifecycle wie Workflow A ab,
aber als deklarative Pipeline-Definition (`config/role-defaults.yaml`, engine: `scripts/lib/pipelines.py`)
mit festem Stage-Ablauf inkl. Branch + PR, statt über eigenständige Agent-Tool-Delegation.

Stages: `branch → requirement (conditional: req-traceability) → tests (conditional: tests-required) → implement (plan-driven) → verify (conditional: tests-required) → validate-and-document (parallel: validator + documenter) → commit`.

> **Historie:** Vor der August-Refactoring-Roadmap gab es einen eigenständigen `feature`-Agent
> mit hartem 8-Schritt-Prozess (Branch → REQ → Tests → Implement → Verify → DoD → Docs → Commit/PR).
> Dieser wurde durch die deklarative `feature-lifecycle`-Pipeline abgelöst — gleicher Lifecycle,
> aber als Config statt eigener Agent-Rolle.

## Wann feature-lifecycle, wann orchestrator?

| Situation | Agent |
|-----------|-------|
| Neues Feature von Null, mit Branch + PR | `feature-lifecycle` Pipeline |
| Bugfix, Refactoring, Ad-hoc-Aufgaben | `orchestrator` |
| Mehrere unabhängige Tasks in einer Session | `orchestrator` |
| Strukturierter TDD-Lifecycle erzwungen | `feature-lifecycle` Pipeline |
