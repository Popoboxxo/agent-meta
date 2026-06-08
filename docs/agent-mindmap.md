# Agenten-Übersicht

> Automatisch generiert von agent-meta. Nicht manuell bearbeiten.

```mermaid
mindmap
  root((orchestrator))
    🔴 developer
      tester
      git
    🔵 feature
      requirements
      validator
      developer
      tester
      git
    🔴 git
    🔵 documenter
    ⚪ ideation
    ⚪ release
      git
      documenter
    ⚪ security-auditor
    ⚪ docker
    🔴 log-analyzer
      feedback
      developer
      security-auditor
    🔴 feedback
    ⚪ agent-meta-manager
      agent-meta-scout
      developer
      git
    ⚪ agent-meta-scout
    ⚪ meta-feedback
    🔵 requirements
    🔵 validator
    🔵 tester
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
- **Model:** Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus
- **Delegiert an:** agent-meta-scout, developer, git

### agent-meta-scout
- **Tier:** optional
- **Beschreibung:** Scoutet das KI-Ökosystem auf neue Skills, Agenten-Patterns, Rules und Workflows. Bewertet Kandidaten und macht konkrete Erweiterungsvorschläge für agent-meta.
- **Model:** Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus

### api-specialist
- **Tier:** optional
- **Beschreibung:** API-Design, OpenAPI-Spezifikationen, Contract-First Development. Erstellt und pflegt API-Vertraege.
- **Model:** Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus

### bug-feature-analyzer
- **Tier:** recommended
- **Beschreibung:** Analysiert und klassifiziert eingehende Bug-Meldungen und Feature-Requests vor Ressourcen-Allokation. Unterscheidet: Echter Bug, User-Fehler, validierbares Feature, Out-of-Scope.
- **Model:** Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus

### claude-expert
- **Tier:** optional
- **Beschreibung:** Absoluter Analyse-Experte für die Plattform Claude Code: Funktionsweise, Konfiguration (.claude), Best Practices (Formatter, Hooks, MCPs) zur optimalen Anpassung von agent-meta.
- **Model:** Gemini: gemini-3.1-pro-high, Opencode: opencode-go/kimi-k2.5

### code-reviewer
- **Tier:** recommended
- **Beschreibung:** Gatekeeper für Code-Gesundheit: Clean Code, SOLID, Blast-Radius-Analysen und REQ-Traceability in Code-Pfaden.
- **Model:** Gemini: gemini-3.1-pro-high, Opencode: opencode-go/deepseek-v4-flash

### continue-expert
- **Tier:** optional
- **Beschreibung:** Absoluter Analyse-Experte für die Plattform Continue: Funktionsweise, Konfiguration (.continue), Best Practices (Formatter, Hooks, MCPs) zur optimalen Anpassung von agent-meta.
- **Model:** Gemini: gemini-3.1-pro-high, Opencode: opencode-go/kimi-k2.5

### copilot-expert
- **Tier:** optional
- **Beschreibung:** Absoluter Analyse-Experte für die Plattform GitHub Copilot: Funktionsweise, Konfiguration (.github/copilot), Best Practices (Formatter, Hooks, MCPs) zur optimalen Anpassung von agent-meta.
- **Model:** Gemini: gemini-3.1-pro-high, Opencode: opencode-go/kimi-k2.5

### developer
- **Tier:** required
- **Beschreibung:** Developer-Agent für das agent-meta Meta-Repository. Erweitert den generischen Developer um Framework-Wissen: Schichten-Architektur, Platzhalter-Lifecycle, Python-Modulstruktur, Rollen-Anlegen-Prozess und Sync-Interface.
- **Model:** Gemini: gemini-3.1-pro-high, Opencode: opencode-go/deepseek-v4-pro
- **Delegiert an:** tester, git

### devops-engineer
- **Tier:** optional
- **Beschreibung:** CI/CD-Pipelines, Infrastructure as Code, Container-Orchestrierung, Observability und Security-Best-Practices.
- **Model:** Gemini: gemini-3.5-flash-high, Opencode: opencode-go/deepseek-v4-flash

### docker
- **Tier:** optional
- **Beschreibung:** Docker-Operationen: Compose-Stacks, Binary-Management, Test-Umgebungen und Diagnose — plattformunabhängig.
- **Model:** Gemini: gemini-3.5-flash-high, Opencode: opencode-go/deepseek-v4-flash

### documenter
- **Tier:** recommended
- **Beschreibung:** Pflegt CODEBASE_OVERVIEW.md, ARCHITECTURE.md, README.md und Session-Erkenntnisse.
- **Model:** Gemini: gemini-3.5-flash-high, Opencode: opencode-go/deepseek-v4-flash

### effort-estimator
- **Tier:** optional
- **Beschreibung:** Schätzt Aufwände für Entwicklungsaufgaben basierend auf Task-Typ und LLM-Fähigkeiten
- **Model:** Gemini: gemini-3.5-flash-high, Opencode: opencode-go/deepseek-v4-flash

### export-manager
- **Tier:** optional
- **Beschreibung:** Liest .meta-config/export.yaml und routet strukturierte JSON-Payloads der Fach-Agenten zum konfigurierten Target (markdown, confluence, jira-xray, etc.).
- **Model:** Gemini: gemini-3.5-flash-high, Opencode: opencode-go/deepseek-v4-flash

### feature
- **Tier:** recommended
- **Beschreibung:** Vollständiger Feature-Lifecycle: Branch → Requirements → TDD → Implementierung → Validierung → Commit → PR.
- **Model:** inherited
- **Delegiert an:** requirements, validator, developer, tester, git

### feedback
- **Tier:** required
- **Beschreibung:** Standardisiert Bug-Reports, Feature-Requests und Verbesserungsvorschläge für das eingesetzte Projekt — kategorisiert, aufbereitet und direkt als GitHub Issue eingereicht.
- **Model:** Gemini: gemini-3.5-flash-high, Opencode: opencode-go/deepseek-v4-flash

### gemini-expert
- **Tier:** optional
- **Beschreibung:** Absoluter Analyse-Experte für die Plattform Gemini (Antigravity): Funktionsweise, Konfiguration (.gemini), Best Practices (Formatter, Hooks, MCPs) zur optimalen Anpassung von agent-meta.
- **Model:** Gemini: gemini-3.1-pro-high, Opencode: opencode-go/kimi-k2.5

### git
- **Tier:** required
- **Beschreibung:** Git-Operationen: Commits, Branches, Merges, Tags, Push/Pull und Commit-Messages — plattformunabhängig (GitHub, GitLab, Gitea).
- **Model:** Gemini: gemini-3.5-flash-high, Opencode: opencode-go/deepseek-v4-flash

### ideation
- **Tier:** optional
- **Beschreibung:** Ideenfindung, Visions-Schärfung und Konzept-Konkretisierung — stellt Fragen, denkt Ecken, übergibt reife Ideen an Requirements.
- **Model:** inherited

### log-analyzer
- **Tier:** required
- **Beschreibung:** Analysiert System- und Applikations-Logs: Frequency-Clustering, Severity-Klassifikation (RFC 5424), Root-Cause-Hypothesen und strukturierte Findings mit Delegations-Routing.
- **Model:** Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus
- **Delegiert an:** feedback, developer, security-auditor

### meta-feedback
- **Tier:** optional
- **Beschreibung:** Verbesserungsvorschläge für agent-meta sammeln und als GitHub Issues einreichen.
- **Model:** Gemini: gemini-3.5-flash-high, Opencode: opencode-go/deepseek-v4-flash

### opencode-expert
- **Tier:** optional
- **Beschreibung:** Absoluter Analyse-Experte für die Plattform Opencode: Funktionsweise, Konfiguration (.opencode), Best Practices (Formatter, Hooks, MCPs) zur optimalen Anpassung von agent-meta.
- **Model:** Gemini: gemini-3.1-pro-high, Opencode: opencode-go/kimi-k2.5

### openscad-developer
- **Tier:** optional
- **Beschreibung:** Spezialisierter Developer für parametrische 3D-Modelle in OpenSCAD. Render-Inspect-Refine Loop via MCP, Druckbarkeits-Wissen, Toleranz-Management.
- **Model:** Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus

### orchestrator
- **Tier:** required
- **Beschreibung:** Provider-agnostischer Task-Orchestrator: zerlegt, parallelisiert, delegiert.
- **Model:** Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus
- **Delegiert an:** developer, feature, git, documenter, ideation, release, security-auditor, docker, log-analyzer, feedback, agent-meta-manager, agent-meta-scout, meta-feedback, requirements, validator, tester

### performance-optimizer
- **Tier:** optional
- **Beschreibung:** Datengetriebene Identifikation und Aufloesung von Big-O Bottlenecks durch Profiling-Daten, ohne funktionale Aenderungen.
- **Model:** Gemini: gemini-3.1-pro-high, Opencode: opencode-go/kimi-k2.5

### provider-expert
- **Tier:** optional
- **Beschreibung:** Absoluter Analyse-Experte für einen AI-Provider: Funktionsweise, Konfiguration, Best Practices (Formatter, Hooks, MCPs) zur optimalen Anpassung von agent-meta.
- **Model:** inherited

### release
- **Tier:** optional
- **Beschreibung:** Versioning, Changelogs, Build-Prozesse und GitHub-Releases verwalten.
- **Model:** Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus
- **Delegiert an:** git, documenter

### requirements
- **Tier:** recommended
- **Beschreibung:** Anforderungen aufnehmen, REQ-IDs vergeben, REQUIREMENTS.md pflegen und Traceability prüfen.
- **Model:** Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus

### se-architect
- **Tier:** optional
- **Beschreibung:** Designs system architecture using generic laws, CQRS routing, and defines L1/L2 whiteboxes.
- **Model:** Gemini: gemini-3.1-pro-high, Opencode: opencode-go/kimi-k2.5

### se-critic
- **Tier:** optional
- **Beschreibung:** Audits requirements and architecture against generic laws (orthogonality, testability, traceability).
- **Model:** Gemini: gemini-3.1-pro-high, Opencode: opencode-go/kimi-k2.5

### se-integration-and-test-manager
- **Tier:** optional
- **Beschreibung:** V&V-Orchestrator: Koordiniert Integrationsstrategie, Test-Ebenen und Traceability-Feedback über L1-Ln.
- **Model:** Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus

### se-interface-mgr
- **Tier:** optional
- **Beschreibung:** Manages generic signal flow and deterministic synchronization across systems.
- **Model:** Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus

### se-orchestrator
- **Tier:** optional
- **Beschreibung:** Coordinates the 6-level recursive breakdown with zig-zag traceability and V&V.
- **Model:** Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus

### se-requirements
- **Tier:** optional
- **Beschreibung:** Elicits stakeholder needs and uses a 6-level template for requirements engineering.
- **Model:** Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus

### se-termination
- **Tier:** optional
- **Beschreibung:** Deterministic termination at L3 (Component Requirement).
- **Model:** Gemini: gemini-3.5-flash-high, Opencode: opencode-go/deepseek-v4-flash

### se-test-engineer
- **Tier:** optional
- **Beschreibung:** Develops MBSE test models and designs integration tests (interaction of multiple SW units). Right wing of the V-model.
- **Model:** Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus

### se-testreviewer
- **Tier:** optional
- **Beschreibung:** Audits the test strategy. Checks for edge cases, boundary value analysis, equivalence class errors, and flakiness.
- **Model:** Gemini: gemini-3.1-pro-high, Opencode: opencode-go/kimi-k2.5

### se-validator
- **Tier:** optional
- **Beschreibung:** L1 System-Validierung: End-to-End User Journeys gegen Stakeholder-Bedürfnisse abgleichen. 'Did we build the right system?'
- **Model:** Gemini: gemini-3.1-pro-high, Opencode: opencode-go/kimi-k2.5

### se-verifier
- **Tier:** optional
- **Beschreibung:** Multi-Level Verification L1-Ln. Validates that fully integrated systems/sub-systems exactly fulfill architectural specifications and interfaces.
- **Model:** Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus

### security-auditor
- **Tier:** optional
- **Beschreibung:** Static security analysis: OWASP Top 10, secrets detection, dependency risks, supply-chain threats, and cryptographic weaknesses — read-only, no code execution.
- **Model:** Gemini: gemini-3.1-pro-high, Opencode: opencode-go/kimi-k2.5

### tester
- **Tier:** recommended
- **Beschreibung:** Isolierte Unit-Tests mit Mocks/Stubs nach TDD-Workflow. Für Integrationstests → se-test-engineer.
- **Model:** Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus

### ui-ux-designer
- **Tier:** optional
- **Beschreibung:** Erstellt UI-Spezifikationen, Mockups und Design-Systeme. Ordnet UI-Elemente REQ-IDs zu.
- **Model:** Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus

### validator
- **Tier:** recommended
- **Beschreibung:** Formaler Prozess-Wächter: DoD-Checkboxen, REQ-ID-Präsenz, Commit-Konventionen. Bewertet KEINE Code-Qualität — dafür code-reviewer.
- **Model:** Gemini: gemini-3.1-pro-low, Opencode: opencode-go/qwen3.6-plus
