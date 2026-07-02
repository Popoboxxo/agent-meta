# agent-meta

agent-meta ist ein Git-Repository das als Submodul in Projekte eingebunden wird. Es stellt standardisierte Claude-Agenten-Templates bereit (1-generic, 2-platform, 0-external) und generiert via sync.py projektfertige Agenten-Dateien in .claude/agents/. Das Repo verwendet sich selbst — die hier generierten Agenten koordinieren die Weiterentwicklung von agent-meta.

<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on every sync. -->
<!-- Manual changes here will be overwritten. -->

Generiert von agent-meta v0.66.0-beta.4 — `2026-07-02`
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
| `concept-reviewer` | Konzept/Design-Doc reviewen: Vollständigkeit, Logik, Risiken, Approve/Iterate |
| `continue-expert` | Continue Experte: Funktionsweise, .continue Konfiguration, Best Practices |
| `copilot-expert` | GitHub Copilot Experte: Funktionsweise, .github/copilot Konfiguration, Best Practices |
| `developer` | Feature-Implementierung und Bugfixes im agent-meta Framework (Python, Markdown, YAML) |
| `devops-engineer` | Verwende diesen Agenten fuer CI/CD, IaC, Kubernetes, Monitoring und Infrastructure-Aufgaben. |
| `documenter` | Doku pflegen: CODEBASE_OVERVIEW, ARCHITECTURE, README, Erkenntnisse |
| `effort-estimator` | Aufwandsschätzung für Tasks — delegiere hierher wenn User nach Zeit/Kosten fragt |
| `explorer` | Codebase analysieren / Dependencies / Impact — read-only, delegiert Findings |
| `export-manager` | Verwende diesen Agenten fuer Export-Routing von strukturierten Daten zu konfigurierten Targets. |
| `feature` | Feature-Lifecycle-Subagent: Branch → REQ → TDD → Dev → Validate → PR. Wird vom Orchestrator gestartet, nicht direkt vom User. |
| `feedback` | Projekt-Feedback: Bugs, Features, Verbesserungen als GitHub Issues standardisiert einreichen — immer vor git |
| `gemini-expert` | Gemini Experte: Funktionsweise, .gemini Konfiguration, Best Practices |
| `git` | Commits, Branches, Tags, Push/Pull und alle Git-Operationen |
| `ideation` | Neue Ideen explorieren, Vision schärfen, Übergabe an requirements |
| `junior-developer` | Low-Tier-Developer: triviale Fixes, Typos, kleine klar umrissene Änderungen — eskaliert bei Scope-Überschreitung |
| `log-analyzer` | Log-Analyse: Fehler clustern, Severity klassifizieren (RFC 5424), Findings als Issues oder Tasks delegieren |
| `meta-feedback` | Verbesserungsvorschläge für agent-meta als GitHub Issues einreichen |
| `opencode-expert` | Opencode Experte: Funktionsweise, .opencode Konfiguration, Best Practices |
| `orchestrator` | Einstiegspunkt für ALLE Entwicklungsaufgaben — zerlegt komplexe Tasks und dispatched parallel |
| `performance-optimizer` | Verwende diesen Agenten fuer Performance-Analyse, Big-O-Optimierung und Bottleneck-Beseitigung. |
| `prompt-engineer` | Prompts und Agenten entwerfen oder reviewen |
| `release` | Versioning, Changelog, Build-Artifact, GitHub Release erstellen |
| `requirements` | Anforderungen aufnehmen, REQ-IDs vergeben, REQUIREMENTS.md pflegen |
| `senior-developer` | High-Tier-Developer: Architektur-Impact, komplexe/riskante Änderungen, schwierige Bugs — analysiert erst, implementiert dann |
| `ui-ux-designer` | UI-Spezifikation, Mockup-Erstellung und Design-System-Definition — implementiert nicht, spezifiziert. |

## Regeln

### A2A Anti-Re-Delegation Gates
Provider-agnostische Regeln für A2A-Handoffs zwischen Agenten. Verhindert Delegations-Schleifen und unkontrollierten Spec-Dump in `payload.t`.
Details: `rules/.../a2a-delegation-gates.md`

---

### Branch-Guard — Feature-Branch Pflicht
**Gilt für alle code-ändernden Aufgaben.**
Details: `rules/.../branch-guard.md`

---

### Commit-Konventionen (Conventional Commits)
Gilt für alle Agenten die Commits erstellen oder vorbereiten.
Details: `rules/.../commit-conventions.md`

---

### Definition of Done (DoD)
Aufgabe abgeschlossen wenn alle **aktiven** Kriterien erfüllt sind.
Details: `rules/.../dod-criteria.md`

---

### GitHub Issue Lifecycle
Wenn deine Arbeit mit einem GitHub Issue verknüpft ist, schließe es nach Abschluss ab.
Details: `rules/.../issue-lifecycle.md`

---

### Sprachregeln
Diese Regel gilt für alle Agenten und den Hauptchat.
Details: `rules/.../language.md`

---

### Lifecycle-Tasks — Ausstehende Aufgaben prüfen
Beim Start einer neuen Konversation: prüfe ob `.opencode/pending-tasks.md` existiert.
Details: `rules/.../lifecycle-tasks.md`

---

### Provider-Agnostic Policy — Generic Templates
**Generische Agenten-Templates (1-generic/) müssen universell und provider-agnostisch bleiben.**
Details: `rules/.../provider-agnostic.md`

---

### Python Conventions
**Gilt für alle Python-Dateien (`*.py`).**
Details: `rules/.../python-conventions.md`

---

### Session-Abschluss — Erkenntnisse sichern
Gilt für Hauptchat und Orchestrator.
Details: `rules/.../session-conclusion.md`

---

### CRITICAL GATE — VERIFY BEFORE EVERY ACTION
YOU ARE THE MAIN CHAT. You MUST NOT perform any code changes directly.
Details: `rules/.../use-orchestrator.md`

---

### agent-meta — Schichten-Architektur
Dieses Repo ist das Meta-Repository für Agenten-Standards. Jede Änderung an Templates
Details: `rules/.../architecture.md`

---

### agent-meta — Entwicklungskonventionen
**1. `.opencode/agents` ist generierter Output — nie manuell bearbeiten.**
Details: `rules/.../conventions.md`

---

### agent-meta — sync.py Interface
`sync.py` ist der einzige Weg Agenten zu generieren. Nie direkt in `.opencode/agents` schreiben.
Details: `rules/.../sync-interface.md`

---

### Kommunikationsstil: Short
**Diese Regel gilt für alle Antworten und überschreibt alle anderen Stilanweisungen.**
Details: `rules/.../short.md`

<!-- agent-meta:managed-end -->

> **Hinweis:** Pfade im managed Block (z.B. `.claude/`) beschreiben die agent-meta-Framework-Architektur. Dieses Projekt verwendet `.opencode/` als Laufzeit-Plattform.

## Agents

Agent files are in `.opencode/agents/`. Invoke them by name in opencode.

## Project Setup

- **Build:** `python scripts/sync.py`
- **Test:** `python scripts/sync.py --validate`
- **Platform:** Python CLI (sync.py)
- **Runtime:** Python 3.x
