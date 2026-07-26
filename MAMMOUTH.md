# agent-meta

<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on every sync. -->
<!-- Manual changes here will be overwritten. -->

> **AI ROUTING:** Claude -> CLAUDE.md | Opencode, Gemini -> AGENTS.md | Mammouth -> MAMMOUTH.md

Generiert von agent-meta v0.86.3 — `2026-07-26`
DoD-Preset: **rapid-prototyping** | REQ-Traceability: false | Tests: false | Codebase-Overview: false | Security-Audit: false

> **Einstiegspunkt:** Starte mit dem `orchestrator`-Agenten für alle Entwicklungsaufgaben — Ausnahmen siehe Abschnitt »Orchestrator — Universal Router«.

| Agent | Zuständigkeit |
|-------|--------------|
| `accessibility-specialist` | Accessibility-Audit: WCAG 2.1/2.2, ARIA, Keyboard-Nav, Screenreader-Guidelines, Kontrast, Focus-Management, A11y-Tree — Findings mit A/AA/AAA-Severity |
| `agent-meta-manager` | Manage agent-meta: upgrade, sync, feedback, create project-specific agents |
| `agent-meta-scout` | Scout the AI ecosystem: discover new skills, roles, rules, and patterns for agent-meta |
| `api-specialist` | Use this agent for API design, OpenAPI specifications, and contract-first development. |
| `bug-feature-analyzer` | Issue triage: classify bug vs. user-error vs. feature vs. out-of-scope — before developer/feature delegation |
| `claude-expert` | Claude Code Experte: Funktionsweise, .claude Konfiguration, Best Practices |
| `code-reviewer` | Checks code quality, blast radius, and Clean Code — not functional correctness (that's validator). |
| `concept-reviewer` | Review concept/design doc: completeness, logic, risks, Approve/Iterate |
| `continue-expert` | Continue Experte: Funktionsweise, .continue Konfiguration, Best Practices |
| `copilot-expert` | GitHub Copilot Experte: Funktionsweise, .github/copilot Konfiguration, Best Practices |
| `data-engineer` | Data-Pipelines: ETL/ELT, Schema-Migration (Datenebene), Data-Quality, Lineage, Pipeline-Monitoring, Streaming/Batch — übergibt Pipeline-Spec an developer |
| `dependency-auditor` | Dependency audit: SBOM, license compatibility, version drift, outdated/vulnerable packages — files findings via feedback as an issue |
| `developer` | Feature-Implementierung und Bugfixes im agent-meta Framework (Python, Markdown, YAML) |
| `devops-engineer` | Use this agent for CI/CD, IaC, Kubernetes, monitoring, and infrastructure tasks. |
| `docker` | Start/stop dev stack, Dockerfiles, binary management |
| `documenter` | Maintain docs: CODEBASE_OVERVIEW, ARCHITECTURE, README, insights |
| `e2e-tester` | Browser-Testing-Agent: E2E-Flows, visuelle Regression, Accessibility-Audit — nicht für Unit-Tests |
| `effort-estimator` | Effort estimation for tasks — delegate here when the user asks about time/cost |
| `explorer` | Analyze codebase / dependencies / impact — read-only, delegates findings |
| `export-manager` | Use this agent for export routing of structured data to configured targets. |
| `feature` | Feature lifecycle subagent: Branch → REQ → TDD → Dev → Validate → PR. Started by the orchestrator, not directly by the user. |
| `feedback` | Project feedback: submit bugs, features, improvements as standardized GitHub issues — always before git |
| `gemini-expert` | Gemini Experte: Funktionsweise, .gemini Konfiguration, Best Practices |
| `git` | Commits, branches, tags, push/pull and all git operations |
| `ideation` | Explore new ideas, sharpen vision, hand off to requirements |
| `incident-responder` | Incident coordination: triage logs/metrics, run runbook, produce RCA (5-Whys), prioritize hotfixes — RCA to documenter, fix to developer |
| `intern-developer` | Gag/Easter-egg agent: an over-eager, clueless intern who explains code wrong with great enthusiasm. Read-only. Do not route real work here. |
| `junior-developer` | Low-tier developer: trivial fixes, typos, small well-scoped changes — escalates on scope overrun |
| `knowledge-curator` | Wiki-Strategie, Schema-Evolution, OKF-Compliance |
| `knowledge-gardener` | Wiki-Pflege: Links, Tags, Frontmatter, Typos, Timestamps |
| `knowledge-indexer` | index.md und log.md pflegen — nur als Delegationsziel anderer Knowledge-Agenten |
| `knowledge-ingestor` | Sources verarbeiten, Wiki-Seiten schreiben, Cross-References pflegen |
| `knowledge-linter` | Wiki-Healthcheck: 10 Lint-Checks (Karpathy + OKF) |
| `knowledge-migrator` | Vorhandene Docs ins Wiki migrieren (einmalig, mit User-Freigabe) |
| `knowledge-querier` | Wiki-Fragen beantworten, Index-First, Synthese mit Citations |
| `log-analyzer` | Log analysis: cluster errors, classify severity (RFC 5424), delegate findings as issues or tasks |
| `mammouth-expert` | Mammouth Code Experte: Funktionsweise, .mammouth Konfiguration, Best Practices |
| `meta-feedback` | Submit improvement suggestions for agent-meta as GitHub issues |
| `opencode-expert` | Opencode Experte: Funktionsweise, .opencode Konfiguration, Best Practices |
| `orchestrator` | Entry point for ALL development tasks — decomposes complex tasks and dispatches in parallel |
| `performance-optimizer` | Use this agent for performance analysis, Big-O optimization, and bottleneck elimination. |
| `principal-developer` | Last-resort developer: only after senior-developer failed multiple times — root-cause analysis, systemic reasoning, no symptom fixes. The most expensive call in the system. |
| `prompt-engineer` | Design or review prompts and agents |
| `refactoring-specialist` | Systematische Transformation: Strangler Fig, inkrementelles Refactoring, Legacy-Modernisierung, Feature-Flag-Rewrites — braucht exklusiven Zugriff auf betroffene Module |
| `release` | Versioning, changelog, build artifact, create GitHub release |
| `requirements` | Capture requirements, assign REQ-IDs, maintain REQUIREMENTS.md |
| `senior-developer` | High-tier developer: architecture impact, complex/risky changes, hard bugs — analyzes first, then implements |
| `technical-writer` | Externe Doku: API-Referenz, Getting-Started, SDK-Docs, Tutorials, CLI-Help, User-Release-Notes, Microcopy — für externe Entwickler und Endnutzer |
| `tester` | Write tests (TDD), run the test suite, ensure coverage |
| `ui-ux-designer` | UI specification, mockup creation, and design-system definition — specifies, does not implement. |
| `validator` | Internal quality checker: DoD checklist, traceability audit. Invoked by the orchestrator after implementation. Not for direct user questions or setup help. |

## Knowledge Engine

Die Knowledge Engine ist aktiviert. Domäne: **personal**.

**Bundle-Pfad:** `knowledge/`
| Pfad | Zweck |
|------|-------|
| `knowledge/schema.md` | Steuerungsdokument — Konventionen, Concept Types, Workflows |
| `knowledge/sources/` | Immutable Raw Sources — LLM liest, modifiziert NIEMALS |
| `knowledge/wiki/` | OKF Knowledge Bundle — LLM-owned, strukturiertes Wiki |
| `knowledge/wiki/index.md` | Content-Katalog aller Wiki-Seiten (OKF §6) |
| `knowledge/wiki/log.md` | Chronologisches Event-Log (OKF §7) |

### Knowledge-Agenten
- **Schema-Owner:** `knowledge-curator` verwaltet `knowledge/schema.md` und Concept-Type-Konventionen

### Knowledge-Workflows
- **Ingest:** Source in `knowledge/sources/` ablegen → `knowledge-ingestor` verarbeitet → Wiki aktualisiert
- **Query:** Frage stellen → `knowledge-querier` durchsucht Index → synthetisiert Antwort
- **Lint:** `knowledge-linter` prüft Wiki-Gesundheit (Widersprüche, Orphans, OKF-Compliance)
- **Migration:** `knowledge-migrator` räumt vorhandene Inhalte auf und migriert ins OKF-Format
- **Gardening:** `knowledge-gardener` pflegt Links, Tags, Typos, Timestamps
<!-- agent-meta:managed-end -->

## Agents

Agent files are in .mammouth/agents (invoke by name).
