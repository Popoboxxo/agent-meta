# agent-meta

agent-meta ist ein Git-Repository das als Submodul in Projekte eingebunden wird. Es stellt standardisierte Claude-Agenten-Templates bereit (1-generic, 2-platform, 0-external) und generiert via sync.py projektfertige Agenten-Dateien in .claude/agents/. Das Repo verwendet sich selbst — die hier generierten Agenten koordinieren die Weiterentwicklung von agent-meta.

<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on every sync. -->
<!-- Manual changes here will be overwritten. -->

Generiert von agent-meta v0.57.1 — `2026-06-08`
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
| `docker` | Dev-Stack starten/stoppen, Dockerfiles, Binary-Management |
| `documenter` | Doku pflegen: CODEBASE_OVERVIEW, ARCHITECTURE, README, Erkenntnisse |
| `effort-estimator` | Aufwandsschätzung für Tasks — delegiere hierher wenn User nach Zeit/Kosten fragt |
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
| `tester` | Tests schreiben (TDD), Test-Suite ausführen, Coverage sicherstellen |
| `ui-ux-designer` | UI-Spezifikation, Mockup-Erstellung und Design-System-Definition — implementiert nicht, spezifiziert. |
<!-- agent-meta:managed-end -->

## Agents

Agent files are in `.gemini/agents/`. Agents must be registered at session start via the bootstrap instructions above. `@agent` text mentions are not intercepted by Gemini.

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
   - `docker.md` → registriere als `docker`
   - `documenter.md` → registriere als `documenter`
   - `effort-estimator.md` → registriere als `effort-estimator`
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
   - `tester.md` → registriere als `tester`
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
   define_subagent(name="docker", ...)
   define_subagent(name="documenter", ...)
   define_subagent(name="effort-estimator", ...)
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
   define_subagent(name="tester", ...)
   define_subagent(name="ui-ux-designer", ...)
   ```

3. Erst danach: Bearbeite User-Anfragen (Delegation an Orchestrator etc.)

> **Ohne diese Registrierung existieren die Agenten NICHT in der Runtime**
> und der Orchestrator kann nicht delegieren.
<!-- agent-meta:bootstrap-end -->

## Project Setup

- **Build:** `python scripts/sync.py`
- **Test:** `python scripts/sync.py --validate`
- **Platform:** Python CLI (sync.py)
- **Runtime:** Python 3.x
