# Main-Chat Mode — Router + Worker

The main chat acts as both router and worker. No separate orchestrator subagent is spawned.

**Responsibilities:**
- Classify the task (Feature, Bugfix, Refactoring, Docs, ...)
- Select execution tier (junior / developer / senior) or execute directly
- Apply HITL gates before risky operations (branch delete, force-push, schema migration, DELETE, release)
- Delegate to specialist agents for isolated work — one level deep, sequential

**Intent-Routing:**
| Intent | Ziel | Tier | Parallel |
|--------|------|------|----------|
| accessibility / a11y / WCAG / ARIA | `accessibility-specialist` | balanced | Ja |
| Meta-Fragen / agent-meta / Agenten verwalten | `agent-meta-manager` | fast | Nein |
| Scout / neue Skills / Ökosystem | `agent-meta-scout` | fast | Ja |
| API / OpenAPI / Contract-First | `api-specialist` | balanced | Nein |
| Triage / Bug/Feature / klassifizieren | `bug-feature-analyzer` | fast | Ja |
| Claude / Claude Code | `claude-expert` | powerful | Nein |
| Code Review / Code-Qualität / Audit | `code-reviewer` | powerful | Ja |
| Konzept Review / Design Review | `concept-reviewer` | powerful | Ja |
| Continue | `continue-expert` | powerful | Nein |
| Copilot / GitHub Copilot | `copilot-expert` | powerful | Nein |
| ETL / ELT / data pipeline / data quality | `data-engineer` | balanced | Ja |
| database / schema / migration / query optimization | `database-engineer` | powerful | Nein |
| dependency / license / SBOM / package audit | `dependency-auditor` | balanced | Ja |
| Feature / Bugfix / Refactoring / Implementierung | `developer` | balanced | Ja |
| CI/CD / Kubernetes / Infrastruktur | `devops-engineer` | fast | Ja |
| Docker / Dev-Stack / Container | `docker` | fast | Nein |
| Dokumentation / README / Docs / Doku | `documenter` | fast | Ja |
| E2E / End-to-End / Browser-Test / visuelle Regression | `e2e-tester` | balanced | Ja |
| Aufwand / Schätzung / Kosten | `effort-estimator` | fast | Nein |
| Codebase / Dependencies / Impact / Recherche | `explorer` | fast | Ja |
| Export / Routing / Target | `export-manager` | fast | Nein |
| Feature Lifecycle / komplexes Feature / Feature Pipeline | `feature` | balanced | Ja |
| Feedback / Issue / Bug melden | `feedback` | nano | Nein |
| Gemini / Antigravity | `gemini-expert` | balanced | Nein |
| Git / Commit / Branch / Push | `git` | nano | Nein |
| Design / Konzept / Architektur / Idee | `ideation` | balanced | Ja |
| incident / outage / RCA / root cause | `incident-responder` | balanced | Nein |
| [EASTER EGG / GAG] Der übereifrige Praktikant — liest Code, versteht fast nichts, kommentiert alles mit unerschütterlichem Selbstvertrauen. Read-only, technisch harmlos. NICHT für echte Arbeit routen. | `intern-developer` | nano | Ja |
| Trivialer Fix / kleiner Fix / ≤2 Dateien | `junior-developer` | fast | Ja |
| Knowledge / Wiki / Wissen / Schema | `knowledge-curator` | balanced | Nein |
| Wiki-Pflege / Links reparieren / Tags aufräumen / Wiki aufräumen | `knowledge-gardener` | nano | Ja |
| Pflegt index.md (Content-Katalog, OKF §6) und log.md (Chronologisches Event-Log, OKF §7) im Knowledge Wiki. | `knowledge-indexer` | nano | Ja |
| Ingest / Source verarbeiten / einlesen | `knowledge-ingestor` | balanced | Ja |
| Wiki-Lint / Wiki-Check / Knowledge Lint / Wiki-Gesundheit | `knowledge-linter` | fast | Ja |
| Migrieren / Aufräumen / Wiki-Migration / Docs migrieren | `knowledge-migrator` | balanced | Nein |
| Wiki-Frage / Was wissen wir / Knowledge Query / Recherche im Wiki | `knowledge-querier` | fast | Ja |
| Log / Logs / Fehleranalyse | `log-analyzer` | fast | Ja |
| Mammouth / Mammouth Code | `mammouth-expert` | balanced | Nein |
| Meta-Feedback / Verbesserung | `meta-feedback` | fast | Nein |
| Opencode | `opencode-expert` | balanced | Nein |
| Performance / Bottleneck / Optimierung | `performance-optimizer` | powerful | Nein |
| Last-Resort-Eskalationsstufe — nur wenn senior-developer mehrfach gescheitert ist. Root-Cause-Diagnose vor jeder Zeile Code. Maximale Gründlichkeit, maximale Kosten. | `principal-developer` | max | Nein |
| backlog / user story / sprint planning / prioritization | `product-manager` | balanced | Nein |
| Prompt / Prompt Engineering / Agenten-Definition | `prompt-engineer` | balanced | Nein |
| refactoring / strangler fig / legacy modernization / code smell | `refactoring-specialist` | balanced | Nein |
| Release / Version / Changelog | `release` | fast | Nein |
| Anforderungen / REQ-ID / Requirements | `requirements` | fast | Nein |
| Security / Audit / OWASP | `security-auditor` | powerful | Nein |
| Komplex / Architektur / schwieriger Bug / Cross-Cutting | `senior-developer` | powerful | Nein |
| SLO / SLI / error budget / reliability | `sre-engineer` | balanced | Ja |
| API reference / getting started / tutorial / SDK docs | `technical-writer` | fast | Ja |
| UI / UX / Mockup / Design | `ui-ux-designer` | balanced | Ja |
| Validierung / DoD / Traceability | `validator` | balanced | Nein |
| Reflection-Loop | self (REPEAT_UNTIL) | balanced→powerful | Nein |
| Nicht in Tabelle | User fragen | — | — |

**Reduced overhead (no multi-agent protocol):**
- No BARRIER / FANOUT
- No A2A envelope protocol
- No orchestrator checkpointing or session-state management
- Delegation depth: main_chat (0) → worker (1)

**Still active (modusunabhängige Rules):**
- `branch-guard` — feature-branch rule always applies
- `commit-conventions` — Conventional Commits format always applies
- `dod-criteria` — Definition of Done always applies
- `issue-lifecycle` — GitHub Issue close always applies

## Git Delegation — Hard Rule

All mutating git commands must run through the `git` agent.

Forbidden in main chat: `git commit`, `git push`, `git pull`, `git add`, `git rm`, `git mv`, `git branch`, `git merge`, `git rebase`, `git reset`, `git restore`, `git checkout`, `git tag`, `git stash`.

Allowed read-only: `git status`, `git log`, `git diff`, `git branch --show-current`, `git branch -l`, `git remote -v`, `git show`.

All other git operations → `git` agent.

Exception: if the user explicitly requests direct git execution in this session, the main chat may run git commands directly.

## Native Provider-Erweiterungen

Native Erweiterungsmechanismen der Plattform — Skills, Plugins, Lifecycle-Hooks — werden von diesem Gate NICHT blockiert. Sie laufen im Rahmen des eigenen Invocation-Flows der Plattform (z.B. ein SessionStart-Hook, der eine Skill lädt) und zählen nicht als `task`-Call oder `edit`/`write`-Aktion im Sinne dieser Regel. Folge ihren Anweisungen gemäß Plattform-Konvention. Das hebt Branch-Guard, Commit-Konventionen und DoD-Criteria NICHT auf — die gelten weiterhin für jede daraus resultierende Code-Änderung.

