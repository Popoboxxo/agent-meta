# Standalone Agent Personas

Pre-rendered, fully self-contained copies of [agent-meta](https://github.com/Popoboxxo/agent-meta)'s generic agent personas — no Python, no `sync.py`, no repo clone required.

*[Deutsche Beschreibung weiter unten ↓](#standalone-agent-personas-deutsch)*

## How to use

1. Pick the role below that matches what you need help with.
2. Open its file (or ask a browsing-capable chat AI to fetch it from this repo directly).
3. Paste the whole file as your system prompt / custom instructions.

**Scope note:** each persona is a solo snapshot. No multi-agent delegation, no DoD gate, no A2A protocol, no project-specific config — for the full pipeline (multi-agent orchestration, project-aware context, quality gates), see the [main repo](https://github.com/Popoboxxo/agent-meta).

## Available roles

| Role | Description | File |
|------|-------------|------|
| `accessibility-specialist` | WCAG 2.1/2.2 compliance audits, ARIA checks, keyboard navigation, screen reader testing guidelines, color contrast analysis, focus management and accessibility tree analysis. | [`agents/accessibility-specialist.md`](agents/accessibility-specialist.md) |
| `agent-meta-manager` | Manage agent-meta: upgrades, sync, feedback delegation, project-specific agents, external-skill lifecycle, and creating extensions. | [`agents/agent-meta-manager.md`](agents/agent-meta-manager.md) |
| `agent-meta-scout` | Scouts the AI ecosystem for new skills, agent patterns, rules, and workflows. | [`agents/agent-meta-scout.md`](agents/agent-meta-scout.md) |
| `api-specialist` | API design, OpenAPI specifications, contract-first development. | [`agents/api-specialist.md`](agents/api-specialist.md) |
| `bug-feature-analyzer` | Analyzes and classifies incoming bug reports and feature requests before resource allocation. | [`agents/bug-feature-analyzer.md`](agents/bug-feature-analyzer.md) |
| `code-reviewer` | Gatekeeper for code health: Clean Code, SOLID, blast-radius analysis, and REQ traceability in code paths. | [`agents/code-reviewer.md`](agents/code-reviewer.md) |
| `concept-reviewer` | Use when a concept or design doc needs a structural review before requirements — completeness, logic, assumptions, risks, feasibility. | [`agents/concept-reviewer.md`](agents/concept-reviewer.md) |
| `copyeditor` | Copyediting: style, sentence structure, word repetition, narrative/argumentative flow, and content consistency on top of a clean text. | [`agents/copyeditor.md`](agents/copyeditor.md) |
| `data-engineer` | ETL/ELT pipeline design, data-layer schema migration, data quality checks, lineage analysis, pipeline monitoring and streaming/batch design. | [`agents/data-engineer.md`](agents/data-engineer.md) |
| `database-engineer` | Relational schema design, database migrations, query optimization and index strategy. | [`agents/database-engineer.md`](agents/database-engineer.md) |
| `dependency-auditor` | Supply-chain hygiene: SBOM analysis, license compatibility (MIT/Apache/GPL matrix), version drift, outdated and deprecated packages. | [`agents/dependency-auditor.md`](agents/dependency-auditor.md) |
| `developer` | Use when a REQ-ID or clearly scoped task needs direct feature/bugfix implementation. | [`agents/developer.md`](agents/developer.md) |
| `devops-engineer` | CI/CD pipelines, Infrastructure as Code, container orchestration, observability, and security best practices. | [`agents/devops-engineer.md`](agents/devops-engineer.md) |
| `docker` | Docker operations: Compose stacks, binary management, test environments, and diagnostics — platform-independent. | [`agents/docker.md`](agents/docker.md) |
| `documenter` | Maintains CODEBASE_OVERVIEW.md, ARCHITECTURE.md, README.md and session insights. | [`agents/documenter.md`](agents/documenter.md) |
| `e2e-tester` | E2E-Tests, visuelle Regression und Accessibility-Audits via Playwright — User-Flows statt isolierter Units. | [`agents/e2e-tester.md`](agents/e2e-tester.md) |
| `effort-estimator` | Estimates effort for development tasks based on task type and LLM capabilities. | [`agents/effort-estimator.md`](agents/effort-estimator.md) |
| `explorer` | Read-only codebase research, dependency and impact mapping, file and symbol search. | [`agents/explorer.md`](agents/explorer.md) |
| `export-manager` | Reads .meta-config/export.yaml and routes structured JSON payloads from specialist agents to the configured target (markdown, confluence, jira-xray, etc.). | [`agents/export-manager.md`](agents/export-manager.md) |
| `feedback` | Standardizes bug reports, feature requests, and improvement suggestions for the deployed project — categorized, prepared, and submitted directly as a GitHub issue. | [`agents/feedback.md`](agents/feedback.md) |
| `git` | Commits, branches, tags, push/pull and all git operations. | [`agents/git.md`](agents/git.md) |
| `ideation` | Use when an idea needs scoping and thoughts need sorting before a concept or REQ exists. | [`agents/ideation.md`](agents/ideation.md) |
| `incident-responder` | Live incident coordination: ingests logs and metrics, executes runbook steps, drives root-cause analysis (5-Whys, Fishbone), classifies severity (P0/P1/P2) and produces an RCA report plus a prioritized hotfix list under time pressure. | [`agents/incident-responder.md`](agents/incident-responder.md) |
| `intern-developer` | [EASTER EGG / GAG AGENT — not for production] The eternally enthusiastic intern. | [`agents/intern-developer.md`](agents/intern-developer.md) |
| `junior-developer` | Fast, well-scoped code changes: 1-2 files, no architecture impact. | [`agents/junior-developer.md`](agents/junior-developer.md) |
| `knowledge-curator` | Strategische Knowledge-Engine-Steuerung: Schema-Evolution, Wiki-Strukturierung, Domänen-Anpassung, Ingest-Planung, OKF-Compliance-Sicherung. | [`agents/knowledge-curator.md`](agents/knowledge-curator.md) |
| `knowledge-gardener` | Kleinteilige Wiki-Pflege: Links reparieren, Tags harmonisieren, Frontmatter ergänzen, Typos korrigieren, Timestamps aktualisieren. | [`agents/knowledge-gardener.md`](agents/knowledge-gardener.md) |
| `knowledge-indexer` | Pflegt index.md (Content-Katalog, OKF §6) und log.md (Chronologisches Event-Log, OKF §7) im Knowledge Wiki. | [`agents/knowledge-indexer.md`](agents/knowledge-indexer.md) |
| `knowledge-ingestor` | Sources einlesen, Key Information extrahieren, Wiki-Seiten erstellen/aktualisieren, Cross-References pflegen. | [`agents/knowledge-ingestor.md`](agents/knowledge-ingestor.md) |
| `knowledge-linter` | Wiki-Gesundheitscheck: Widersprüche, Orphans, veraltete Claims, kaputte Links, fehlende OKF-Frontmatter, Index-Staleness. | [`agents/knowledge-linter.md`](agents/knowledge-linter.md) |
| `knowledge-migrator` | Vorhandene Projektinhalte aufräumen und OKF-konform ins Knowledge Wiki migrieren. | [`agents/knowledge-migrator.md`](agents/knowledge-migrator.md) |
| `knowledge-querier` | Fragen gegen das Knowledge Wiki beantworten. | [`agents/knowledge-querier.md`](agents/knowledge-querier.md) |
| `log-analyzer` | Analyzes system and application logs: frequency clustering, severity classification (RFC 5424), root-cause hypotheses, and structured findings with delegation routing. | [`agents/log-analyzer.md`](agents/log-analyzer.md) |
| `mammouth-expert` | Absoluter Analyse-Experte für die Plattform Mammouth Code: Funktionsweise, Konfiguration (.mammouth), Best Practices (Formatter, Hooks, MCPs) zur optimalen Anpassung von agent-meta. | [`agents/mammouth-expert.md`](agents/mammouth-expert.md) |
| `meta-feedback` | Collect improvement suggestions for agent-meta and submit them as GitHub issues. | [`agents/meta-feedback.md`](agents/meta-feedback.md) |
| `openscad-developer` | Specialized developer for parametric 3D models in OpenSCAD. | [`agents/openscad-developer.md`](agents/openscad-developer.md) |
| `orchestrator` | Provider-agnostic task orchestrator in Modern Mode: decomposes, parallelizes, delegates. | [`agents/orchestrator.md`](agents/orchestrator.md) |
| `performance-optimizer` | Data-driven identification and resolution of Big-O bottlenecks using profiling data, without functional changes. | [`agents/performance-optimizer.md`](agents/performance-optimizer.md) |
| `planner` | Use when a concept, REQ, or bug needs to be turned into a concrete, ordered implementation plan before work starts. | [`agents/planner.md`](agents/planner.md) |
| `principal-developer` | Last-resort escalation tier. | [`agents/principal-developer.md`](agents/principal-developer.md) |
| `product-manager` | Strategic, business-oriented backlog and roadmap ownership: user stories, sprint planning, prioritization frameworks (RICE, MoSCoW), KPI/metrics definition and stakeholder communication. | [`agents/product-manager.md`](agents/product-manager.md) |
| `prompt-engineer` | The ultimate expert for prompt engineering. | [`agents/prompt-engineer.md`](agents/prompt-engineer.md) |
| `proofreader` | Proofreading: pure correctness pass on existing text — spelling, grammar, punctuation. | [`agents/proofreader.md`](agents/proofreader.md) |
| `provider-expert` | Absolute analysis expert for an AI provider: how it works, configuration, best practices for optimally adapting agent-meta. | [`agents/provider-expert.md`](agents/provider-expert.md) |
| `refactoring-specialist` | Systematic large-scale code transformation with safety nets: Strangler Fig pattern, incremental refactoring, code smell detection, legacy modernization and feature-flag-driven rewrites with backwards-compatibility guarantees. | [`agents/refactoring-specialist.md`](agents/refactoring-specialist.md) |
| `release` | Manage versioning, changelogs, build processes and GitHub releases. | [`agents/release.md`](agents/release.md) |
| `requirements` | Capture requirements, assign REQ-IDs, maintain REQUIREMENTS.md and check traceability. | [`agents/requirements.md`](agents/requirements.md) |
| `se-architect` | Designs system architecture via functional decomposition. | [`agents/se-architect.md`](agents/se-architect.md) |
| `se-critic` | Audits requirements and architecture against generic laws. | [`agents/se-critic.md`](agents/se-critic.md) |
| `se-developer` | Implements standard SE leaf nodes with multiple interfaces. | [`agents/se-developer.md`](agents/se-developer.md) |
| `se-integration-and-test-manager` | V&V-Orchestrator: Koordiniert Integrationsstrategie, Test-Ebenen und Traceability-Feedback über L1-Ln. | [`agents/se-integration-and-test-manager.md`](agents/se-integration-and-test-manager.md) |
| `se-interface-mgr` | Manages generic signal flow and deterministic synchronization across systems. | [`agents/se-interface-mgr.md`](agents/se-interface-mgr.md) |
| `se-junior-developer` | Implements trivial SE leaf nodes (COTS wrappers, single-interface components). | [`agents/se-junior-developer.md`](agents/se-junior-developer.md) |
| `se-requirements` | Elicits stakeholder needs and captures multi-level requirements. | [`agents/se-requirements.md`](agents/se-requirements.md) |
| `se-senior-developer` | Implements complex SE leaf nodes. | [`agents/se-senior-developer.md`](agents/se-senior-developer.md) |
| `se-termination` | Deterministic per-system leaf/continue decision with dynamic depth control. | [`agents/se-termination.md`](agents/se-termination.md) |
| `se-test-engineer` | Develops MBSE test models and designs integration tests (interaction of multiple SW units). | [`agents/se-test-engineer.md`](agents/se-test-engineer.md) |
| `se-testreviewer` | Audits the test strategy. | [`agents/se-testreviewer.md`](agents/se-testreviewer.md) |
| `se-validator` | L1 System-Validierung: End-to-End User Journeys gegen Stakeholder-Bedürfnisse abgleichen. | [`agents/se-validator.md`](agents/se-validator.md) |
| `se-verifier` | Multi-Level Verification L1-Ln. | [`agents/se-verifier.md`](agents/se-verifier.md) |
| `security-auditor` | Static security analysis: OWASP Top 10, secrets detection, dependency risks, supply-chain threats, and cryptographic weaknesses — read-only, no code execution. | [`agents/security-auditor.md`](agents/security-auditor.md) |
| `senior-developer` | Complex features, architecture decisions, hard bugs and cross-cutting refactorings. | [`agents/senior-developer.md`](agents/senior-developer.md) |
| `sre-engineer` | Proactive reliability discipline: SLI/SLO definition, error budgets, capacity planning, toil reduction, runbook creation and pre-deployment reliability reviews. | [`agents/sre-engineer.md`](agents/sre-engineer.md) |
| `technical-writer` | External developer- and user-facing documentation: API references, getting-started guides, SDK docs, tutorials, CLI help pages, user-facing release notes and UX microcopy. | [`agents/technical-writer.md`](agents/technical-writer.md) |
| `tester` | Isolated unit tests with mocks/stubs following a TDD workflow. | [`agents/tester.md`](agents/tester.md) |
| `ui-ux-designer` | Creates UI specifications, mockups, and design systems. | [`agents/ui-ux-designer.md`](agents/ui-ux-designer.md) |
| `validator` | Formal process gatekeeper: DoD checkboxes, REQ-ID presence, commit conventions. | [`agents/validator.md`](agents/validator.md) |

---

## Standalone Agent Personas (Deutsch)

Fertig gerenderte, vollständig eigenständige Kopien der generischen Agenten-Personas von [agent-meta](https://github.com/Popoboxxo/agent-meta) — kein Python, kein `sync.py`, kein Repo-Klon nötig.

### Verwendung

1. Passende Rolle in der Tabelle oben auswählen.
2. Zugehörige Datei öffnen (oder eine browsing-fähige Chat-KI bitten, sie direkt aus diesem Repo zu holen).
3. Die gesamte Datei als System-Prompt / Custom Instructions einfügen.

**Hinweis zum Umfang:** Jede Persona ist eine isolierte Momentaufnahme — ohne Multi-Agenten-Delegation, ohne DoD-Gate, ohne A2A-Protokoll, ohne projektspezifische Konfiguration. Für die volle Pipeline (Multi-Agenten-Orchestrierung, projektbewusster Kontext, Quality Gates) siehe das [Haupt-Repo](https://github.com/Popoboxxo/agent-meta).

---
Generated from agent-meta v0.93.0. Regenerate via `python scripts/sync.py --render-standalone` (or the Admin UI's Sync page).
