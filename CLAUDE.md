# agent-meta

> Projektbeschreibung für Claude-Agenten. Diese Datei ist die **einzige Quelle**
> für projektspezifischen Kontext — Agenten lesen sie, statt eigenen Kontext zu haben.
>
> Generiert von agent-meta v0.57.1 — `2026-06-13`
>
> **Längenempfehlung:** 200–500 Zeilen optimal. Über 500 Zeilen → Detailwissen in
> `docs/ARCHITECTURE.md`, `docs/API.md` o.ä. auslagern und manuell verlinken.
> Agent-spezifisches Wissen → `.claude/3-project/<rolle>-ext.md` (Extension).
>
> **CLAUDE.md Hierarchie (Claude Code lädt in dieser Reihenfolge):**
> 1. `~/.claude/CLAUDE.md` — global, alle Projekte (~50 Zeilen max, persönliche Präferenzen)
> 2. `<projekt>/CLAUDE.md` — diese Datei, projektspezifisch (von agent-meta verwaltet)
> 3. `<ordner>/CLAUDE.md` — optional in Unterordnern (z.B. `src/backend/CLAUDE.md`)

---

## Projekt

**Name:** agent-meta
**Präfix:** am
**Plattform:** Python CLI (sync.py)
**Beschreibung:** Zentrales Meta-Repository für die Standardisierung und Wiederverwendung von Claude-Agenten-Rollen über alle Projekte hinweg.

---

## Tech-Stack

- **Runtime:** Python 3.x
- **Sprache:** Python 3, Markdown, YAML
- **Key-Dependencies:** - Python: `>=3.8`

---

## Architektur

```
agents/
  0-external/       # Wrapper-Template für externe Skills
  1-generic/        # Universelle Agent-Templates
  2-platform/       # Plattform-Overrides (z.B. sharkord)
scripts/
  sync.py           # Agent-Generator
snippets/           # Sprachspezifische Code-Snippets
external/           # Git Submodule (externe Skill-Repos)
howto/              # Anleitungen und Beispiel-Config
docs/architecture/  # Architektur-Diagramme (Mermaid)

```

**Entry-Point:**
```
scripts/sync.py — Haupt-CLI für Agent-Generierung
```

**Besondere Patterns:**
- Agent-Templates haben YAML-Frontmatter (name, version, description, tools)
- Platzhalter {{VARIABLE}} werden von sync.py substituiert
- Extensions (.claude/3-project/*-ext.md) werden vom Agenten zur Laufzeit gelesen
- Snippet-Dateien haben eigenes YAML-Frontmatter (snippet, version, language, runtime)


---

## Code-Konventionen

- Python: PEP 8, snake_case, klare Funktionsnamen
- Keine externen Python-Dependencies außer Stdlib
- Markdown-Dateien: GitHub Flavored Markdown
- YAML Frontmatter in allen Agent-Templates


---

## Build & Development

```bash
# Build
python scripts/sync.py

# Tests
python scripts/sync.py --validate

# Dev-Stack starten
(kein Dev-Stack)

# Nach Änderungen neu laden
(kein Dev-Stack)
```

---

## Anforderungs-Kategorien

Kategorien für `docs/REQUIREMENTS.md`:

{{REQ_CATEGORIES_LIST}}

---

## Agenten-Konfiguration

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
<!-- agent-meta:managed-end -->

**Singleton-Regel:** Es existiert genau EIN `orchestrator` pro Session — der vom `main_chat` gespawnte. Worker-Agents dürfen niemals `task(subagent_type="orchestrator", ...)` aufrufen. Verstoß = Deadlock / Routing-Konflikt.

---

## Sprachregeln

<!-- Die globale Rule .claude/rules/language.md (generiert von sync.py) deckt den Kern ab. -->
<!-- Hier nur projektspezifische Abweichungen eintragen — sonst leer lassen. -->

- `README.md` → **Englisch**
- Alle anderen Dokumente → **Deutsch**
- Code-Kommentare, Commit-Messages → **Englisch**
- Kommunikation mit dem Nutzer → **Deutsch**
