# agent-meta

## Projekt

**Name:** agent-meta
**Präfix:** am
**Plattform:** Python CLI (sync.py)
**Beschreibung:** Zentrales Meta-Repository für die Standardisierung und Wiederverwendung von Claude-Agenten-Rollen über alle Projekte hinweg.

> Stack: Python 3.x · Python 3, Markdown, YAML · Deps: - Python: `>=3.8`

> Struktur: `.meta-config/project.yaml` → `variables.PROJECT_STRUCTURE`.

**Entry-Point:** `scripts/sync.py — Haupt-CLI für Agent-Generierung`

**Besondere Patterns:**
- Agent-Templates haben YAML-Frontmatter (name, version, description, tools)
- Platzhalter {{VARIABLE}} werden von sync.py substituiert
- Extensions (.claude/3-project/*-ext.md) werden vom Agenten zur Laufzeit gelesen
- Snippet-Dateien haben eigenes YAML-Frontmatter (snippet, version, language, runtime)


## Code-Konventionen

- Python: PEP 8, snake_case, klare Funktionsnamen
- Keine externen Python-Dependencies außer Stdlib
- Markdown-Dateien: GitHub Flavored Markdown
- YAML Frontmatter in allen Agent-Templates


> Build: `python scripts/sync.py` · Test: `python3 scripts/sync.py --validate` · Dev: `(kein Dev-Stack)` · Reload: `(kein Dev-Stack)`

## Anforderungs-Kategorien

Kategorien für `docs/REQUIREMENTS.md`:

- Framework-Features (sync.py, neue Agenten-Rollen, Variablen)
- Agenten-Templates (Workflows, Sprach-Sektionen, Versionierung)
- Entwickler-Experience (Howto, Beispiele, Doku)



<!-- agent-meta:managed-begin -->
<!-- Dieser Block wird von sync.py bei jedem sync automatisch aktualisiert. -->
<!-- Manuelle Änderungen hier werden überschrieben. -->

> **AI ROUTING:** Claude -> CLAUDE.md | Opencode, Gemini -> AGENTS.md | Mammouth -> MAMMOUTH.md

Generiert von agent-meta v0.101.0-beta.4 — `2026-08-31`
DoD-Preset: **rapid-prototyping** | REQ-Traceability: false | Tests: false | Codebase-Overview: false | Security-Audit: false
> **Einstiegspunkt:** Starte mit dem `orchestrator`-Agenten für alle Entwicklungsaufgaben — Ausnahmen siehe Abschnitt »Orchestrator — Universal Router«.

| Agent | Zuständigkeit |
|-------|--------------|
| `accessibility-specialist` | Accessibility-Audit: WCAG 2.1/2.2, ARIA, Keyboard-Nav, Screenreader-Guidelines, Kontrast, Focus-Management, A11y-Tree — Findings mit A/AA/AAA-Severity |
| `agent-meta-manager` | Manage agent-meta: upgrade, sync, feedback, create project-specific agents |
| `agent-meta-scout` | Scout the AI ecosystem: discover new skills, roles, rules, and patterns for agent-meta |
| `api-specialist` | Use this agent for API design, OpenAPI specifications, and contract-first development. |
| `bug-feature-analyzer` | Issue triage: classify bug vs. user-error vs. feature vs. out-of-scope — before developer/feature-lifecycle delegation |
| `claude-expert` | Claude Code Experte: Funktionsweise, .claude Konfiguration, Best Practices |
| `code-reviewer` | Checks code quality, blast radius, and Clean Code — not functional correctness (that's validator). |
| `concept-reviewer` | Review concept/design doc: completeness, logic, risks, Approve/Iterate |
| `continue-expert` | Continue Experte: Funktionsweise, .continue Konfiguration, Best Practices |
| `copilot-expert` | GitHub Copilot Experte: Funktionsweise, .github/copilot Konfiguration, Best Practices |
| `data-engineer` | Data-Pipelines: ETL/ELT, Schema-Migration (Datenebene), Data-Quality, Lineage, Pipeline-Monitoring, Streaming/Batch — übergibt Pipeline-Spec an developer |
| `dependency-auditor` | Dependency audit: SBOM, license compatibility, version drift, outdated/vulnerable packages — files findings via feedback as an issue |
| `design-system-architect` | Design-System-Schema → echte Token-Artefakte: Primitive/Semantic/Component-Ebenen, Farbharmonie + Kontrast-Gate (Design-time, kein WCAG-Audit), Spacing/Breakpoint-Methodik, Variant-Contracts, Motion-Tokens. |
| `developer` | Feature-Implementierung und Bugfixes im agent-meta Framework (Python, Markdown, YAML) |
| `devops-engineer` | Use this agent for CI/CD, IaC, Kubernetes, monitoring, and infrastructure tasks. |
| `docker` | Start/stop dev stack, Dockerfiles, binary management |
| `documenter` | Maintain docs: CODEBASE_OVERVIEW, ARCHITECTURE, README, insights |
| `e2e-tester` | Browser-Testing-Agent: E2E-Flows, visuelle Regression, Accessibility-Audit — nicht für Unit-Tests |
| `effort-estimator` | Effort estimation for tasks — delegate here when the user asks about time/cost |
| `explorer` | Analyze codebase / dependencies / impact — read-only, delegates findings |
| `export-manager` | Use this agent for export routing of structured data to configured targets. |
| `feedback` | Project feedback: submit bugs, features, improvements as standardized GitHub issues — always before git |
| `frontend-component-engineer` | Screen-Spec + Token-/Variant-Contract → produktionsreife UI-Komponenten: Props-Contract, State-Matrix (loading/error/empty/success), A11y-Baseline (kein Audit), Motion aus Tokens, Mobile-first, Test-Grundgerüst. |
| `gemini-expert` | Gemini Experte: Funktionsweise, .gemini Konfiguration, Best Practices |
| `git` | Commits, branches, tags, push/pull and all git operations |
| `ideation` | Nutze ideation zum Scopen einer rohen Idee, bevor ein Konzept oder REQ existiert. |
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
| `planner` | Nutze planner wenn ein Konzept/REQ/Bug in konkrete, geordnete Umsetzungsschritte übersetzt werden muss. |
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

## Eigene Notizen

Hier kannst du eigene, projektspezifische Notizen eintragen. Dieser Bereich wird von `agent-meta` nicht überschrieben!
