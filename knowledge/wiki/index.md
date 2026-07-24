# Knowledge Index

> Auto-maintained entry point into the knowledge bundle. Lists all concepts, entities and topics as they are added.

## Concepts

- [A2A Best Practice Analysis](concepts/a2a-best-practice-analysis.md) — Envelope-Feldanzahl und Best-Practice-Bewertung des A2A-Handoff-Schemas. `concept`
- [A2A-Handoff-Protokoll](concepts/a2a-handoff-protocol.md) — Implementationsnahe Konzeptschärfung: Schemas, Orchestrator als Envelope-Fabrik. `concept`
- [Architektur: Admin-UI — Technische Spezifikation](concepts/admin-ui-architecture.md) — Admin-Server nur localhost, kein Auth-Layer, Super-Admin via Dateisystem-Check. `concept, status:planned`
- [Konzept: Admin-UI — Config Surface & Workflow Editor](concepts/admin-ui-concept.md) — project.yaml Config-Oberfläche, Workflow-Editor. `concept, status:planned`
- [Konzept: Agent-Visualisierungs-Dashboard (AVD)](concepts/agent-visualization-dashboard.md) — Lokaler Webserver zeigt Agenten-Aktivität in Echtzeit. `concept`
- [Konzept: Agent-Visualisierung Dashboard v2](concepts/agent-visualization-v2.md) — Umsetzung: viz.py, agent-mindmap.md, agent-graph.html, viz-logger/server/report.py. `concept`
- [agent-meta — Architecture Overview](concepts/architecture.md) — SE-Agenten-Kaskade als fraktales 6-Stufen Black-Box→White-Box-System. `architecture, status:active`
- [Agent Roles](concepts/architecture-agent-roles.md) — feature-Agent als Shortcut zum orchestrator. `architecture, status:active`
- [Development Workflow](concepts/architecture-dev-workflow.md) — feature-Agent als 8-Schritt Workflow inkl. Branch + PR. `architecture, status:active`
- [External Skills Integration](concepts/architecture-external-skills.md) — Integration von Drittrepo-Skills als eigenständige Agenten. `architecture, status:active`
- [Overall Architectural Systems Engineering Breakdown Rules](concepts/architecture-law.md) — Verbindliche Regeln für jeden Anforderungs-Herunterbruch. `concept`
- [Layer Model](concepts/architecture-layer-model.md) — Rules werden automatisch in jeden Agenten-Kontext geladen. `architecture, status:active`
- [SE-Agenten-Kaskade — Architektur-Detail](concepts/architecture-se-cascade.md) — Fraktale SE-Kaskade mit drei Floors, 5 aktiven Decomposition-Agenten. `architecture, status:active`
- [Sync Flow](concepts/architecture-sync-flow.md) — sync.py aktualisiert bei jedem Lauf den managed block in CLAUDE.md. `architecture, status:active`
- [Versioning Strategy](concepts/architecture-versioning.md) — Versionierungsstrategie für Agenten-Templates. `architecture, status:active`
- [Circuit-Breaker, DoD-as-Gate, and Judge/Validator Pattern](concepts/circuit-breaker-dod-gate-judge-pattern.md) — Best Practice Audit 2026-07, geplantes Pattern. `concept, status:active`
- [Konzept: Dynamische Modellerfassung & Tier-Presets](concepts/dynamic-model-presets.md) — Abkehr von statischen Modell-Zuweisungen hin zu preisbewusstem Preset-System. Umgesetzt. `concept, status:planned`
- [Generalisiertes Integrations-Framework für agent-meta](concepts/integrations-framework.md) — paket-verwaltete MCP-Tools, Referenz semble v0.3.4. `concept`
- [Knowledge Engine für agent-meta — Konzept v4](concepts/knowledge-engine-concept.md) — Finales Konzept: Karpathy LLM-Wiki + Google OKF Analyse, Deep-Dive. `concept`
- [Konzept: Main-Chat-Orchestrator-Modus](concepts/main-chat-orchestrator-mode.md) — orchestrator.enabled/strict leiten drei exklusive Modus-Flags ab. `concept, status:active`
- [Konzept: Orchestrator-First Architecture](concepts/orchestrator-first-architecture.md) — Provider-agnostische Delegations-Pyramide, Intent-Routing, FANOUT/BARRIER. `concept`
- [Developer — Modern Mode (planned)](concepts/planned-1-generic-modern-developer.md) — Two-Mode-Prompt-Architektur Beispiel für Developer-Rolle. `concept, status:planned`
- [Konzept: Prompt-Modernisierung durch Two-Mode-Prompt-Architektur](concepts/prompt-modernization.md) — Systematische Evaluierung aller 55 generischen Templates. `concept, status:planned`
- [Konzept: Systems Engineering Agenten-Kaskade](concepts/se-agent-concept.md) — 14 SE-Agenten-Templates, Decomposition + Verification. `concept`
- [Implementierungsplan: SE-Agenten-Kaskade (Generic Edition)](concepts/se-agent-implementation-plan.md) — Rekursives SE-Zellenmodell mit universellem 6-Stufen-Herunterbruch. `concept`
- [Konzept: SE-Kaskaden-Standardisierung — Issue #339](concepts/se-cascade-optimization-339.md) — 6 strukturelle Befunde: ADR-Standards, Rollentrennung u.a. `concept, status:planned`
- [Konzept: SE-Pipeline-Erweiterung](concepts/se-pipeline-extension.md) — Teilresultat-Protokoll & Rollentrennung für SE-Framework-Schwachstellen. `concept`
- [Evaluierung der generischen SE-Prinzipien](concepts/se-principles-evaluation.md) — Misst 6-Stufen-Modell, Orthogonalität, CQRS gegen reale Praxis. `concept`
- [Konzept: SE-Kaskaden-Standardisierung & Prompt-Modernisierung](concepts/se-und-prompt-modernisierung.md) — Kombination aus SE-Standardisierung und Prompt-Modernisierung. `concept, status:active`
- [Architektur: Singleton-Orchestrator](concepts/singleton-orchestrator-architecture.md) — Provider-agnostische Subagent-Spawn-Restriction. `concept, status:active`
- [Konzept: Visualisierung & Logging Simplifizierung](concepts/viz-logging-mcp.md) — Architektur-Überarbeitung von Logging/Viz-Mechanismus (MCP/CLI Fallback). `concept`

## Entities

- [Admin UI & Function Reference](entities/admin-ui-reference.md) — Exhaustive Referenz aller Config-Optionen und Funktionen im Agent Meta Manager. `api`
- [CLI Reference: sync.py](entities/cli-reference.md) — Zentraler Einstiegspunkt, generiert Agenten, verwaltet Provider-Configs. `api`
- [Agent-Meta Composition System](entities/composition-system.md) — extends/patches-Mechanismus für plattform-/projektspezifische Anpassung. `api`
- [Provider Abstraction Layer (PAL) Variables](entities/pal-variables.md) — Platzhalter in Agent-Templates, zur Build-Zeit provider-spezifisch aufgelöst. `api`
- [Slash Commands Reference](entities/slash-commands.md) — Chat-Shortcuts für Workflows über alle AI-Provider. `api`
- [Viz-Report API-Dokumentation](entities/viz-api.md) — HTTP-API-Endpunkte des viz-report.py WSGI-Servers. `api`
- [Viz-Event-Schema](entities/viz-event-schema.md) — Alle Event-Typen in .meta-viz/events.jsonl. `api`

## Topics

- [Industry Best Practices: Agentic Systems (#274)](topics/274-industry-bestpractices.md) — Anthropic/OpenAI/LangGraph/AutoGen/DeepMind Best-Practice-Vergleich. `analysis`
- [Audit: Architecture Robustness (#276)](topics/276-architecture-robustness-audit.md) — Audit von scripts/lib/config.py, agents.py, runtime.py, viz.py. `analysis`
- [Agent Composition — extends & patches](topics/agent-composition.md) — Composition-Mechanismus vermeidet vollständige Template-Duplikate. `guide, feature`
- [Agent Delegation Map](topics/agent-delegation-map.md) — Übersicht aller Agent-zu-Agent-Verweise im Framework. `guide, feature`
- [Agent Isolation — isolation: worktree](topics/agent-isolation.md) — Claude-Code-Feature für isolierte Git-Worktree-Ausführung. `guide, feature`
- [Agent Memory — Persistentes Agenten-Gedächtnis](topics/agent-memory.md) — memory:-Feld im Frontmatter für Cross-Session-Persistenz. `guide, feature`
- [Agent-Versionierung](topics/agent-versioning.md) — version:-Nummer pro generischem/plattformspezifischem Agent. `guide, feature`
- [Commands — Slash Commands im Layer-System](topics/commands.md) — Aufrufbare Slash-Commands im selben Schichten-Modell wie Agents. `guide, feature`
- [Config-Layout — Drei Ebenen](topics/config-layout.md) — Trennung der Konfiguration in drei unabhängige Ebenen. `guide, setup`
- [Howto: Consistency-Check](topics/consistency-check.md) — Deterministische Validierung von Templates, Commands, Cross-References. `guide, feature`
- [External Skills — Vollständige Anleitung](topics/external-skills.md) — Spezialisierte Drittrepo-Agenten für hochspezifisches Wissen. `guide, feature`
- [First Steps — agent-meta einrichten](topics/first-steps.md) — Schritt-für-Schritt Einrichtung mit Rückfragen statt Automatik. `guide, setup`
- [Honcho MCP Setup](topics/honcho-setup.md) — Lokaler Memory/Context-Server als Cross-Session-Gedächtnis. `guide, mcp`
- [Hooks — Shell-Hooks im Layer-System](topics/hooks.md) — Shell-Skripte vor/nach Tool-Aufrufen, im selben Schichten-Modell wie Rules/Agents. `guide, feature`
- [Howto: Neues Projekt mit agent-meta einrichten](topics/instantiate-project.md) — Agenten via sync.py generieren, Projektkontext über CLAUDE.md. `guide, setup`
- [Lifecycle Triggers](topics/lifecycle-triggers.md) — Agenten-Tasks automatisch bei Git-Events (Release, Merge). `guide, feature`
- [MCP Setup — Best Practices](topics/mcp-setup.md) — MCP-Server-Registry, Regel-Generierung, Secrets-Handling providerübergreifend. `guide`
- [models-dev-table-redesign](topics/models-dev-table-redesign.md) — UI-Spec SCR-MODELS-01: Models & Pricing Tabelle aus models.dev. `ui-spec`
- [Platform Config Instantiation](topics/platform-config.md) — Platzhalter wie {{platform.homeassistant.admingroup}} über Sync-Config aufgelöst. `guide, feature`
- [Provider Abstraction Layer (PAL) — Syntax-Isolation](topics/provider-abstraction-layer.md) — Provider-agnostische Templates für 5 Provider aus einer Quelle. `guide, feature`
- [Gemini CLI — Provider-Dokumentation](topics/provider-gemini-cli.md) — Terminal-Agent von Google, vergleichbar mit Claude Code. `guide, provider`
- [Multi-Provider Support](topics/provider-multi-provider.md) — Gleichzeitige Generierung für Gemini, Continue und Claude aus einer Config. `guide, provider`
- [opencode — Provider-Dokumentation](topics/provider-opencode.md) — Terminal-Agent von SST, 75+ Tools. `guide, provider`
- [Quality Pipelines](topics/quality-pipelines.md) — Vordefinierte Multi-Agent-Ketten für wiederkehrende Workflows. `guide`
- [Reflection-Loops — Generische Iterative Verbesserung](topics/reflection-loops.md) — Generator/Critic-Rollenpaar für iterative Output-Verbesserung. `guide`
- [ReqFlow MCP Setup](topics/reqflow-setup.md) — Self-hosted Requirements-Engineering-Plattform mit AI-Ableitung. `guide, mcp`
- [Rules — Projekt-globale Regeln](topics/rules.md) — .claude/rules/ automatisch in jeden Agenten-Kontext geladen. `guide, feature`
- [Rules-Preset Optimierung](topics/rules-preset-optimization.md) — Selektive Rule-Ladung für platform-heavy Projekte. `guide, feature`
- [Black-Box → White-Box Transition](topics/se-blackbox-to-whitebox.md) — Zentrale Methode des Übergangs von Anforderung zu Architektur. `guide, se-cascade`
- [SE-Cascade auf Gemini / Antigravity](topics/se-cascade-gemini.md) — Kein natives Subagent-Dispatch-Tool auf Gemini/Antigravity — Workaround. `guide, se-cascade`
- [Interface-Management in der SE-Kaskade](topics/se-interface-management.md) — Kritischste Rolle für funktionierende Rekursion zwischen Komponenten. `guide, se-cascade`
- [MCP-Adapter für die SE-Kaskade](topics/se-mcp-adapters.md) — Export von Requirements/Architektur/Traceability in Ticket-Systeme (Phase 3). `guide, se-cascade`
- [SE Session Resume](topics/se-resume-session.md) — Wiederaufnahme langer SE-Kaskaden nach Token-Loss. `guide, se-cascade`
- [SE Role Boundaries](topics/se-role-boundaries.md) — Strikte Trennung Stakeholder Requirements vs. System Architecture nach ISO/IEC 15288. `guide, se-cascade`
- [SE-Workflow: Die rekursive SE-Kaskade](topics/se-workflow.md) — Vollständiger Ablauf des fraktalen SE-Workflows. `guide, se-cascade`
- [CI: Provider Context Sync Check](topics/sync-check.md) — Verhindert veraltete Provider-Context-Files in main. `guide`
- [agent-meta Sync-Konzept](topics/sync-concept.md) — Einbindung von agent-meta via versioniertem Python-Script + Config. `guide, feature`
- [Template Gap-Analyse — Stand 2026-04-01](topics/template-gap-analysis.md) — Vergleich generische Templates vs. instanziierte Agenten (skplugin, skherointroduce). `guide, feature`
- [Test-Repository Validation](topics/test-repo-validation.md) — Validierung generierter Agenten-Dateien in separatem Test-Repo. `guide`
- [Upgrade Guide](topics/upgrade-guide.md) — .claude/agents/ wird bei jedem Sync neu generiert; entfernte Rollen automatisch gelöscht. `guide, setup`

## Sources (Session Conclusions)

- [Erkenntnisse — 10. Mai 2026](sources/2026-05-10-session.md) — Framework Health-Check + Viz-Logging-Fix. `session, conclusion`
- [Erkenntnisse — 23. Mai 2026](sources/2026-05-23-session.md) — Vollständige Entwicklung der SE-Agenten-Kaskade, 6 Templates + JSON-Schemas. `session, conclusion`
- [Erkenntnisse — 27. Mai 2026](sources/2026-05-27-session.md) — Formatierungs-/Kompatibilitätsfixes, Nesting-Bug behoben. `session, conclusion`
- [Erkenntnisse — 12. Juni 2026](sources/2026-06-12-session.md) — Fehlerquellen-Elimination: Root-Cause-Bug in PAL-Engine u.a. `session, conclusion`
- [Erkenntnisse — 27. Juni 2026](sources/2026-06-27-session.md) — A2A Anti-Re-Delegation Gates implementiert, 2 Defekte gefixt. `session, conclusion`
- [Session-Erkenntnisse — 2026-07-01](sources/2026-07-01-session.md) — Prompt-Modernisierung Debug & HITL-Deadlock-Fix. `session, conclusion`
