# Main-Chat Mode
Main Chat ist Router + Worker. Kein Orchestrator-Subagent. Du bist der Orchestrator!

## Intent Routing
> Parallel ist rein informativ — kein Runtime-Enforcement, nur CI-Konsistenzcheck bei required/recommended-Tier-Abdeckung.

| Intent / Keywords | Agent | Tier | Parallel |
|-------------------|-------|------|----------|
| accessibility, a11y, WCAG, ARIA, screen reader, keyboard navigation, color contrast, focus management | `accessibility-specialist` | optional | yes |
| Meta-Fragen, agent-meta, Agenten verwalten | `agent-meta-manager` | optional | no |
| Scout, neue Skills, Ökosystem | `agent-meta-scout` | optional | yes |
| API, OpenAPI, Contract-First | `api-specialist` | optional | no |
| Triage, Bug/Feature, klassifizieren | `bug-feature-analyzer` | recommended | yes |
| Claude, Claude Code | `claude-expert` | optional | no |
| Code Review, Code-Qualität, Audit | `code-reviewer` | recommended | yes |
| Konzept Review, Design Review | `concept-reviewer` | optional | yes |
| Continue | `continue-expert` | optional | no |
| Copilot, GitHub Copilot | `copilot-expert` | optional | no |
| ETL, ELT, data pipeline, data quality, lineage, streaming, batch, schema registry | `data-engineer` | optional | yes |
| dependency, license, SBOM, package audit, vulnerability, outdated, supply chain | `dependency-auditor` | optional | yes |
| Bugfix, Refactoring, Implementierung, Code schreiben | `developer` | required | yes |
| CI/CD, Kubernetes, Infrastruktur | `devops-engineer` | optional | yes |
| Docker, Dev-Stack, Container | `docker` | optional | no |
| Dokumentation, README, Docs, Doku | `documenter` | recommended | yes |
| E2E, End-to-End, Browser-Test, visuelle Regression, Accessibility, a11y | `e2e-tester` | optional | yes |
| Aufwand, Schätzung, Kosten | `effort-estimator` | optional | no |
| Codebase, Dependencies, Impact, Recherche | `explorer` | optional | yes |
| Export, Routing, Target | `export-manager` | optional | no |
| Feature Lifecycle, komplexes Feature, Feature Pipeline | `feature` | recommended | yes |
| Feedback, Issue, Bug melden | `feedback` | required | no |
| Gemini, Antigravity | `gemini-expert` | optional | no |
| Git, Commit, Branch, Push, Pull | `git` | required | no |
| Design, Konzept, Architektur, Idee | `ideation` | optional | yes |
| incident, outage, RCA, root cause, post-mortem, hotfix, P0, P1 | `incident-responder` | optional | no |
| Trivialer Fix, kleiner Fix, ≤2 Dateien | `junior-developer` | optional | yes |
| Knowledge, Wiki, Wissen, Schema, Knowledge-Engine | `knowledge-curator` | optional | no |
| Wiki-Pflege, Links reparieren, Tags aufräumen, Wiki aufräumen | `knowledge-gardener` | optional | yes |
| Index aktualisieren, Index pflegen, log pflegen | `knowledge-indexer` | optional | yes |
| Ingest, Source verarbeiten, einlesen | `knowledge-ingestor` | optional | yes |
| Wiki-Lint, Wiki-Check, Knowledge Lint, Wiki-Gesundheit | `knowledge-linter` | optional | yes |
| Migrieren, Aufräumen, Wiki-Migration, Docs migrieren, Vorhandene Docs ins Wiki | `knowledge-migrator` | optional | no |
| Wiki-Frage, Was wissen wir, Knowledge Query, Recherche im Wiki | `knowledge-querier` | optional | yes |
| Log, Logs, Fehleranalyse | `log-analyzer` | required | yes |
| Mammouth, Mammouth Code | `mammouth-expert` | optional | no |
| Meta-Feedback, Verbesserung | `meta-feedback` | optional | no |
| Opencode | `opencode-expert` | optional | no |
| Performance, Bottleneck, Optimierung | `performance-optimizer` | optional | no |
| Plan, Planung, Schritte, Umsetzungsplan, wie setzen wir das um | `planner` | recommended | no |
| Prompt, Prompt Engineering, Agenten-Definition | `prompt-engineer` | optional | no |
| refactoring, strangler fig, legacy modernization, code smell, systematic transformation, framework upgrade | `refactoring-specialist` | optional | no |
| Release, Version, Changelog | `release` | optional | no |
| Anforderungen, REQ-ID, Requirements | `requirements` | recommended | no |
| Komplex, Architektur, schwieriger Bug, Cross-Cutting | `senior-developer` | optional | no |
| API reference, getting started, tutorial, SDK docs, release notes, quickstart, user guide, microcopy | `technical-writer` | optional | yes |
| Tests, TDD, Testabdeckung | `tester` | recommended | yes |
| UI, UX, Mockup, Design | `ui-ux-designer` | optional | yes |
| Validierung, DoD, Traceability | `validator` | recommended | no |


## A2A Delegation
A2A-Envelopes verwenden: IPayload (t, ctx, con, refs, pri, dep), IEnvelope (protocol_version, handoff_id, source_agent, target_agent, schema_ref, payload). payload.t ≤ 300 Zeichen.

## Plan Delegation
Plan vorhanden (`plan-*.md` oder Knowledge-Wiki Plan-Seite) -> `feature` mit `payload.plan_ref`, statt neuen Lifecycle blind zu starten.

## Git Delegation
Git Mutationen (commit, push, add etc) -> `git` Agent. Read-only (status, log) im Main Chat ok.
Ausnahme auf User-Wunsch erlaubt.

Native Extensions (Skills/Hooks) erlaubt, ignorieren nicht Branch-Guard/DoD.

