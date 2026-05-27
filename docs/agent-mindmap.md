# Agenten-Übersicht

> Automatisch generiert von agent-meta. Nicht manuell bearbeiten.

```mermaid
mindmap
  root((orchestrator))
    ⚪ developer
      tester
      git
    ⚪ feature
      requirements
      validator
      developer
      tester
      git
    ⚪ git
    ⚪ documenter
    ⚪ ideation
    ⚪ release
      git
      documenter
    ⚪ security-auditor
    ⚪ docker
    ⚪ log-analyzer
      feedback
      developer
      security-auditor
    ⚪ feedback
    ⚪ agent-meta-manager
      agent-meta-scout
      developer
      git
    ⚪ agent-meta-scout
    ⚪ meta-feedback
    ⚪ requirements
    ⚪ validator
    ⚪ tester
```

## Legende

| Symbol | Bedeutung |
|--------|-----------|
| 🔴 | required — Kern-Workflow |
| 🔵 | recommended — Standard-Qualität |
| ⚪ | optional — Bei Bedarf |

## Agenten-Details

### agent-meta-manager
- **Tier:** optional
- **Beschreibung:** agent-meta verwalten: Upgrades, Sync, Feedback-Delegation, projektspezifische Agenten, External-Skill-Lifecycle und Erweiterungen anlegen.
- **Model:** inherited
- **Delegiert an:** agent-meta-scout, developer, git

### agent-meta-scout
- **Tier:** optional
- **Beschreibung:** Scoutet das KI-Ökosystem auf neue Skills, Agenten-Patterns, Rules und Workflows. Bewertet Kandidaten und macht konkrete Erweiterungsvorschläge für agent-meta.
- **Model:** inherited

### api-specialist
- **Tier:** optional
- **Beschreibung:** API-Design, OpenAPI-Spezifikationen, Contract-First Development. Erstellt und pflegt API-Vertraege.
- **Model:** inherited

### bug-feature-analyzer
- **Tier:** optional
- **Beschreibung:** Analysiert und klassifiziert eingehende Bug-Meldungen und Feature-Requests vor Ressourcen-Allokation. Unterscheidet: Echter Bug, User-Fehler, validierbares Feature, Out-of-Scope.
- **Model:** inherited

### code-reviewer
- **Tier:** optional
- **Beschreibung:** Gatekeeper für Code-Gesundheit: Clean Code, SOLID, Blast-Radius-Analysen und REQ-Traceability in Code-Pfaden.
- **Model:** inherited

### developer
- **Tier:** optional
- **Beschreibung:** Developer-Agent für das agent-meta Meta-Repository. Erweitert den generischen Developer um Framework-Wissen: Schichten-Architektur, Platzhalter-Lifecycle, Python-Modulstruktur, Rollen-Anlegen-Prozess und Sync-Interface.
- **Model:** inherited
- **Delegiert an:** tester, git

### devops-engineer
- **Tier:** optional
- **Beschreibung:** CI/CD-Pipelines, Infrastructure as Code, Container-Orchestrierung, Observability und Security-Best-Practices.
- **Model:** inherited

### docker
- **Tier:** optional
- **Beschreibung:** Docker-Operationen: Compose-Stacks, Binary-Management, Test-Umgebungen und Diagnose — plattformunabhängig.
- **Model:** inherited

### documenter
- **Tier:** optional
- **Beschreibung:** Pflegt CODEBASE_OVERVIEW.md, ARCHITECTURE.md, README.md und Session-Erkenntnisse.
- **Model:** inherited

### effort-estimator
- **Tier:** optional
- **Beschreibung:** Schätzt Aufwände für Entwicklungsaufgaben basierend auf Task-Typ und LLM-Fähigkeiten
- **Model:** inherited

### export-manager
- **Tier:** optional
- **Beschreibung:** Liest .meta-config/export.yaml und routet strukturierte JSON-Payloads der Fach-Agenten zum konfigurierten Target (markdown, confluence, jira-xray, etc.).
- **Model:** inherited

### feature
- **Tier:** optional
- **Beschreibung:** Vollständiger Feature-Lifecycle: Branch → Requirements → TDD → Implementierung → Validierung → Commit → PR.
- **Model:** inherited
- **Delegiert an:** requirements, validator, developer, tester, git

### feedback
- **Tier:** optional
- **Beschreibung:** Standardisiert Bug-Reports, Feature-Requests und Verbesserungsvorschläge für das eingesetzte Projekt — kategorisiert, aufbereitet und direkt als GitHub Issue eingereicht.
- **Model:** inherited

### git
- **Tier:** optional
- **Beschreibung:** Git-Operationen: Commits, Branches, Merges, Tags, Push/Pull und Commit-Messages — plattformunabhängig (GitHub, GitLab, Gitea).
- **Model:** inherited

### ideation
- **Tier:** optional
- **Beschreibung:** Ideenfindung, Visions-Schärfung und Konzept-Konkretisierung — stellt Fragen, denkt Ecken, übergibt reife Ideen an Requirements.
- **Model:** inherited

### log-analyzer
- **Tier:** optional
- **Beschreibung:** Analysiert System- und Applikations-Logs: Frequency-Clustering, Severity-Klassifikation (RFC 5424), Root-Cause-Hypothesen und strukturierte Findings mit Delegations-Routing.
- **Model:** inherited
- **Delegiert an:** feedback, developer, security-auditor

### meta-feedback
- **Tier:** optional
- **Beschreibung:** Verbesserungsvorschläge für agent-meta sammeln und als GitHub Issues einreichen.
- **Model:** inherited

### openscad-developer
- **Tier:** optional
- **Beschreibung:** Spezialisierter Developer für parametrische 3D-Modelle in OpenSCAD. Render-Inspect-Refine Loop via MCP, Druckbarkeits-Wissen, Toleranz-Management.
- **Model:** inherited

### orchestrator
- **Tier:** required
- **Beschreibung:** Provider-agnostischer Task-Orchestrator: zerlegt, parallelisiert, delegiert.
- **Model:** Claude: claude-sonnet-4-6, Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus
- **Delegiert an:** developer, feature, git, documenter, ideation, release, security-auditor, docker, log-analyzer, feedback, agent-meta-manager, agent-meta-scout, meta-feedback, requirements, validator, tester

### performance-optimizer
- **Tier:** optional
- **Beschreibung:** Datengetriebene Identifikation und Aufloesung von Big-O Bottlenecks durch Profiling-Daten, ohne funktionale Aenderungen.
- **Model:** inherited

### release
- **Tier:** optional
- **Beschreibung:** Versioning, Changelogs, Build-Prozesse und GitHub-Releases verwalten.
- **Model:** inherited
- **Delegiert an:** git, documenter

### requirements
- **Tier:** optional
- **Beschreibung:** Anforderungen aufnehmen, REQ-IDs vergeben, REQUIREMENTS.md pflegen und Traceability prüfen.
- **Model:** inherited

### se-architect
- **Tier:** optional
- **Beschreibung:** Designs system architecture using generic laws, CQRS routing, and defines L1/L2 whiteboxes.
- **Model:** inherited

### se-critic
- **Tier:** optional
- **Beschreibung:** Audits requirements and architecture against generic laws (orthogonality, testability, traceability).
- **Model:** inherited

### se-integration-and-test-manager
- **Tier:** optional
- **Beschreibung:** V&V-Orchestrator: Koordiniert Integrationsstrategie, Test-Ebenen und Traceability-Feedback über L1-Ln.
- **Model:** inherited

### se-interface-mgr
- **Tier:** optional
- **Beschreibung:** Manages generic signal flow and deterministic synchronization across systems.
- **Model:** inherited

### se-orchestrator
- **Tier:** optional
- **Beschreibung:** Coordinates the 6-level recursive breakdown with zig-zag traceability and V&V.
- **Model:** inherited

### se-requirements
- **Tier:** optional
- **Beschreibung:** Elicits stakeholder needs and uses a 6-level template for requirements engineering.
- **Model:** inherited

### se-termination
- **Tier:** optional
- **Beschreibung:** Deterministic termination at L3 (Component Requirement).
- **Model:** inherited

### se-test-engineer
- **Tier:** optional
- **Beschreibung:** Develops MBSE test models and designs integration tests (interaction of multiple SW units). Right wing of the V-model.
- **Model:** inherited

### se-testreviewer
- **Tier:** optional
- **Beschreibung:** Audits the test strategy. Checks for edge cases, boundary value analysis, equivalence class errors, and flakiness.
- **Model:** inherited

### se-validator
- **Tier:** optional
- **Beschreibung:** L1 System-Validierung: End-to-End User Journeys gegen Stakeholder-Bedürfnisse abgleichen. 'Did we build the right system?'
- **Model:** inherited

### se-verifier
- **Tier:** optional
- **Beschreibung:** Multi-Level Verification L1-Ln. Validates that fully integrated systems/sub-systems exactly fulfill architectural specifications and interfaces.
- **Model:** inherited

### security-auditor
- **Tier:** optional
- **Beschreibung:** Static security analysis: OWASP Top 10, secrets detection, dependency risks, supply-chain threats, and cryptographic weaknesses — read-only, no code execution.
- **Model:** inherited

### tester
- **Tier:** optional
- **Beschreibung:** Isolierte Unit-Tests mit Mocks/Stubs nach TDD-Workflow. Für Integrationstests → se-test-engineer.
- **Model:** inherited

### ui-ux-designer
- **Tier:** optional
- **Beschreibung:** Erstellt UI-Spezifikationen, Mockups und Design-Systeme. Ordnet UI-Elemente REQ-IDs zu.
- **Model:** inherited

### validator
- **Tier:** optional
- **Beschreibung:** Formaler Prozess-Wächter: DoD-Checkboxen, REQ-ID-Präsenz, Commit-Konventionen. Bewertet KEINE Code-Qualität — dafür code-reviewer.
- **Model:** inherited
