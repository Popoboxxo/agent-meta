# agent-meta

agent-meta ist ein Git-Repository das als Submodul in Projekte eingebunden wird. Es stellt standardisierte Claude-Agenten-Templates bereit (1-generic, 2-platform, 0-external) und generiert via sync.py projektfertige Agenten-Dateien in .claude/agents/. Das Repo verwendet sich selbst — die hier generierten Agenten koordinieren die Weiterentwicklung von agent-meta.

<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on every sync. -->
<!-- Manual changes here will be overwritten. -->

Generiert von agent-meta v0.57.0 — `2026-05-31`
DoD-Preset: **rapid-prototyping** | REQ-Traceability: false | Tests: false | Codebase-Overview: false | Security-Audit: false

> **Einstiegspunkt:** Starte mit dem `orchestrator`-Agenten für alle Entwicklungsaufgaben — Ausnahmen siehe Abschnitt »Orchestrator — Universal Router«.

| Agent | Zuständigkeit |
|-------|--------------|
| `agent-meta-manager` | agent-meta verwalten: Upgrade, Sync, Feedback, projektspezifische Agenten anlegen |
| `agent-meta-scout` | KI-Ökosystem scouten: neue Skills, Rollen, Rules und Patterns für agent-meta entdecken |
| `api-specialist` | Verwende diesen Agenten fuer API-Design, OpenAPI-Spezifikationen und Contract-First Development. |
| `bug-feature-analyzer` | Issue-Triage: Bug vs. User-Error vs. Feature vs. Out-of-Scope klassifizieren — vor developer/feature-Delegation |
| `claude-expert` | Claude Code Experte: Funktionsweise, .claude Konfiguration, Best Practices |
| `code-reviewer` | Prüft Code-Qualität, Blast-Radius und Clean Code — nicht funktionale Korrektheit (das macht validator). |
| `continue-expert` | Continue Experte: Funktionsweise, .continue Konfiguration, Best Practices |
| `copilot-expert` | GitHub Copilot Experte: Funktionsweise, .github/copilot Konfiguration, Best Practices |
| `developer` | Feature-Implementierung und Bugfixes im agent-meta Framework (Python, Markdown, YAML) |
| `devops-engineer` | Verwende diesen Agenten fuer CI/CD, IaC, Kubernetes, Monitoring und Infrastructure-Aufgaben. |
| `documenter` | Doku pflegen: CODEBASE_OVERVIEW, ARCHITECTURE, README, Erkenntnisse |
| `export-manager` | Verwende diesen Agenten fuer Export-Routing von strukturierten Daten zu konfigurierten Targets. |
| `feature` | Feature-Lifecycle-Subagent: Branch → REQ → TDD → Dev → Validate → PR. Wird vom Orchestrator gestartet, nicht direkt vom User. |
| `feedback` | Projekt-Feedback: Bugs, Features, Verbesserungen als GitHub Issues standardisiert einreichen — immer vor git |
| `gemini-expert` | Gemini Experte: Funktionsweise, .gemini Konfiguration, Best Practices |
| `git` | Commits, Branches, Tags, Push/Pull und alle Git-Operationen |
| `ideation` | Neue Ideen explorieren, Vision schärfen, Übergabe an requirements |
| `log-analyzer` | Log-Analyse: Fehler clustern, Severity klassifizieren (RFC 5424), Findings als Issues oder Tasks delegieren |
| `meta-feedback` | Verbesserungsvorschläge für agent-meta als GitHub Issues einreichen |
| `opencode-expert` | Opencode Experte: Funktionsweise, .opencode Konfiguration, Best Practices |
| `orchestrator` | Einstiegspunkt für ALLE Entwicklungsaufgaben — zerlegt komplexe Tasks und dispatched parallel |
| `performance-optimizer` | Verwende diesen Agenten fuer Performance-Analyse, Big-O-Optimierung und Bottleneck-Beseitigung. |
| `release` | Versioning, Changelog, Build-Artifact, GitHub Release erstellen |
| `requirements` | Anforderungen aufnehmen, REQ-IDs vergeben, REQUIREMENTS.md pflegen |
| `se-architect` | Use this agent to design L1 and L2 architectures from requirements. |
| `se-critic` | Use this agent to validate requirements before architecture, and audit architectural decompositions. |
| `se-integration-and-test-manager` | Orchestriert den gesamten rechten Flügel der V&V-Kaskade — Bottom-Up, Top-Down, Integrationsplanung. |
| `se-interface-mgr` | Manages generic signal flow, deterministic sync across systems |
| `se-orchestrator` | Coordinates the 6-level recursive breakdown |
| `se-requirements` | Use this agent to clarify requirements and start the SE cascade. |
| `se-termination` | Deterministic termination at L3 (Component Requirement) |
| `se-test-engineer` | Use this agent to create model-based test models and integration test strategies from architectural decompositions. |
| `se-testreviewer` | Use this agent to review and audit test models and integration test strategies before execution. |
| `se-validator` | Validiert das System auf L1-Ebene durch User-Journey-Simulation — ignoriert Code, prüft ob der User-Need erfüllt ist. |
| `se-verifier` | Use this agent to verify integrated systems against their specifications on all architecture levels (L1 through Ln). |
| `ui-ux-designer` | UI-Spezifikation, Mockup-Erstellung und Design-System-Definition — implementiert nicht, spezifiziert. |
<!-- agent-meta:managed-end -->

## Agents

Agent files are in `.gemini/agents/`. Use them with `@agent-name` in Gemini CLI.

## Project Setup

- **Build:** `python scripts/sync.py`
- **Test:** `(kein automatisiertes Test-System — manuelle Verifikation via --dry-run)`
- **Platform:** Python CLI (sync.py)
- **Runtime:** Python 3.x

## REGELN!!!!
Befolge strikt und stoisch ALLES was in /rules steht!

<!-- agent-meta:bootstrap-begin -->

## Agent Bootstrap — Session-Start Pflicht

Gemini/Antigravity benötigt eine einmalige Agent-Registrierung pro Session.
**Führe folgende Schritte zu Beginn JEDER Session aus:**

1. Lies alle Agenten-Dateien aus `.gemini/agents/`:
   - `agent-meta-manager.md` → registriere als `agent-meta-manager`
   - `agent-meta-scout.md` → registriere als `agent-meta-scout`
   - `api-specialist.md` → registriere als `api-specialist`
   - `bug-feature-analyzer.md` → registriere als `bug-feature-analyzer`
   - `claude-expert.md` → registriere als `claude-expert`
   - `code-reviewer.md` → registriere als `code-reviewer`
   - `continue-expert.md` → registriere als `continue-expert`
   - `copilot-expert.md` → registriere als `copilot-expert`
   - `developer.md` → registriere als `developer`
   - `devops-engineer.md` → registriere als `devops-engineer`
   - `documenter.md` → registriere als `documenter`
   - `export-manager.md` → registriere als `export-manager`
   - `feature.md` → registriere als `feature`
   - `feedback.md` → registriere als `feedback`
   - `gemini-expert.md` → registriere als `gemini-expert`
   - `git.md` → registriere als `git`
   - `ideation.md` → registriere als `ideation`
   - `log-analyzer.md` → registriere als `log-analyzer`
   - `meta-feedback.md` → registriere als `meta-feedback`
   - `opencode-expert.md` → registriere als `opencode-expert`
   - `orchestrator.md` → registriere als `orchestrator`
   - `performance-optimizer.md` → registriere als `performance-optimizer`
   - `release.md` → registriere als `release`
   - `requirements.md` → registriere als `requirements`
   - `se-architect.md` → registriere als `se-architect`
   - `se-critic.md` → registriere als `se-critic`
   - `se-integration-and-test-manager.md` → registriere als `se-integration-and-test-manager`
   - `se-interface-mgr.md` → registriere als `se-interface-mgr`
   - `se-orchestrator.md` → registriere als `se-orchestrator`
   - `se-requirements.md` → registriere als `se-requirements`
   - `se-termination.md` → registriere als `se-termination`
   - `se-test-engineer.md` → registriere als `se-test-engineer`
   - `se-testreviewer.md` → registriere als `se-testreviewer`
   - `se-validator.md` → registriere als `se-validator`
   - `se-verifier.md` → registriere als `se-verifier`
   - `ui-ux-designer.md` → registriere als `ui-ux-designer`

2. Registriere jeden Agenten via define_subagent API-Call:
   ```
   define_subagent(name="agent-meta-manager", ...)
   define_subagent(name="agent-meta-scout", ...)
   define_subagent(name="api-specialist", ...)
   define_subagent(name="bug-feature-analyzer", ...)
   define_subagent(name="claude-expert", ...)
   define_subagent(name="code-reviewer", ...)
   define_subagent(name="continue-expert", ...)
   define_subagent(name="copilot-expert", ...)
   define_subagent(name="developer", ...)
   define_subagent(name="devops-engineer", ...)
   define_subagent(name="documenter", ...)
   define_subagent(name="export-manager", ...)
   define_subagent(name="feature", ...)
   define_subagent(name="feedback", ...)
   define_subagent(name="gemini-expert", ...)
   define_subagent(name="git", ...)
   define_subagent(name="ideation", ...)
   define_subagent(name="log-analyzer", ...)
   define_subagent(name="meta-feedback", ...)
   define_subagent(name="opencode-expert", ...)
   define_subagent(name="orchestrator", ...)
   define_subagent(name="performance-optimizer", ...)
   define_subagent(name="release", ...)
   define_subagent(name="requirements", ...)
   define_subagent(name="se-architect", ...)
   define_subagent(name="se-critic", ...)
   define_subagent(name="se-integration-and-test-manager", ...)
   define_subagent(name="se-interface-mgr", ...)
   define_subagent(name="se-orchestrator", ...)
   define_subagent(name="se-requirements", ...)
   define_subagent(name="se-termination", ...)
   define_subagent(name="se-test-engineer", ...)
   define_subagent(name="se-testreviewer", ...)
   define_subagent(name="se-validator", ...)
   define_subagent(name="se-verifier", ...)
   define_subagent(name="ui-ux-designer", ...)
   ```

3. Erst danach: Bearbeite User-Anfragen (Delegation an Orchestrator etc.)

> **Ohne diese Registrierung existieren die Agenten NICHT in der Runtime**
> und der Orchestrator kann nicht delegieren.
<!-- agent-meta:bootstrap-end -->
