# agent-meta

agent-meta ist ein Git-Repository das als Submodul in Projekte eingebunden wird. Es stellt standardisierte Claude-Agenten-Templates bereit (1-generic, 2-platform, 0-external) und generiert via sync.py projektfertige Agenten-Dateien in .claude/agents/. Das Repo verwendet sich selbst — die hier generierten Agenten koordinieren die Weiterentwicklung von agent-meta.

<!-- agent-meta:managed-begin -->
> **ROUTING:**


 Gemini->AGENTS.md
> **ENTRY:** `orchestrator`-Agent (für alle Dev-Tasks).
`agent-meta v0.87.0` | DoD: `rapid-prototyping` | REQ-Trace: `false`

## Agent Directory
> ⚠️ **ACHTUNG:** Agenten (Prompts) liegen in `.gemini/agents bzw. .opencode/agents`.

| Agent | Core Capabilities |
|-------|-------------------|

| `accessibility-specialist` | WCAG 2.1/2.2 Compliance-Audit, ARIA-Checks, Keyboard-Navigation, Screenreader... |

| `agent-meta-manager` | agent-meta verwalten: Upgrade, Sync, Feedback, projektspezifische Agenten anl... |

| `agent-meta-scout` | Claude-Ökosystem scouten: neue Skills, Rollen, Rules und Patterns entdecken |

| `api-specialist` | OpenAPI/Contract-First API Design, Schnittstellen-Spezifikationen. |

| `bug-feature-analyzer` | Issue-Triage: Eingehende Bug-Meldungen und Feature-Requests analysieren und k... |

| `claude-expert` | Absoluter Analyse-Experte für die Plattform Claude Code: Funktionsweise, Konf... |

| `code-reviewer` | Clean Code Gatekeeper: Blast-Radius-Analyse, SOLID/DRY Prüfung, Code-Qualität... |

| `concept-reviewer` | Konzept-Critic: reviewt Design-Docs und Konzepte auf Vollständigkeit, Logik, ... |

| `continue-expert` | Absoluter Analyse-Experte für die Plattform Continue: Funktionsweise, Konfigu... |

| `copilot-expert` | Absoluter Analyse-Experte für die Plattform GitHub Copilot: Funktionsweise, K... |

| `data-engineer` | ETL/ELT-Pipelines, Schema-Migration (Datenebene), Data-Quality-Checks, Lineag... |

| `dependency-auditor` | Supply-Chain-Hygiene: SBOM-Analyse, Lizenz-Kompatibilität, Version-Drift und ... |

| `developer` | Feature-Implementierung und Bugfixes |

| `devops-engineer` | CI/CD, Infrastructure as Code, Kubernetes, Observability. |

| `docker` | Dev-Stack verwalten, Test-Stack starten, Binary-Management, Dockerfiles erste... |

| `documenter` | CODEBASE_OVERVIEW, ARCHITECTURE, README, Erkenntnisse pflegen |

| `e2e-tester` | E2E-Tests, visuelle Regression und Accessibility-Audits via Playwright |

| `effort-estimator` | Schätzt Aufwände für Entwicklungsaufgaben basierend auf Task-Typ und LLM-Kali... |

| `explorer` | Read-only Codebase-Recherche, Dependency- und Impact-Mapping, Datei- und Symb... |

| `export-manager` | Target-agnostischer Output-Router: Markdown, Confluence, Jira-Xray, Notion. |

| `feature` | Feature-Lifecycle-Subagent: Branch → REQ → TDD → Dev → Validate → PR |

| `feedback` | Projekt-Feedback standardisieren: Bugs, Features, Verbesserungen als GitHub I... |

| `gemini-expert` | Absoluter Analyse-Experte für die Plattform Gemini (Antigravity): Funktionswe... |

| `git` | Commits, Branches, Tags, Push/Pull und alle Git-Operationen |

| `ideation` | Neue Ideen explorieren, Vision schärfen, Übergabe an requirements |

| `incident-responder` | Live-Incident-Koordination: korreliert Logs und Metriken, führt Runbook-Schri... |

| `intern-developer` | [EASTER EGG / GAG] Der übereifrige Praktikant |

| `junior-developer` | Triviale Code-Änderungen (≤2 Dateien, kein Architektur-Impact) |

| `knowledge-curator` | Strategische Knowledge-Engine-Steuerung: Schema-Evolution, Wiki-Strukturierun... |

| `knowledge-gardener` | Kleinteilige Wiki-Pflege: Links reparieren, Tags harmonisieren, Frontmatter e... |

| `knowledge-indexer` | Pflegt index.md (Content-Katalog, OKF §6) und log.md (Chronologisches Event-L... |

| `knowledge-ingestor` | Sources einlesen, Key Information extrahieren, Wiki-Seiten erstellen/ aktuali... |

| `knowledge-linter` | Wiki-Gesundheitscheck: Widersprüche, Orphans, veraltete Claims, kaputte Links... |

| `knowledge-migrator` | Vorhandene Projektinhalte aufräumen und OKF-konform ins Knowledge Wiki migrieren |

| `knowledge-querier` | Fragen gegen das Knowledge Wiki beantworten |

| `log-analyzer` | System- und Applikations-Logs analysieren: Frequency-Clustering, Severity-Kla... |

| `mammouth-expert` | Absoluter Analyse-Experte für die Plattform Mammouth Code: Funktionsweise, Ko... |

| `meta-feedback` | Verbesserungsvorschläge für agent-meta als GitHub Issues einreichen |

| `opencode-expert` | Absoluter Analyse-Experte für die Plattform Opencode: Funktionsweise, Konfigu... |

| `orchestrator` | Einstiegspunkt für alle Entwicklungsaufgaben |

| `performance-optimizer` | Big-O Bottleneck-Identifikation und datengetriebene Performance-Optimierung. |

| `principal-developer` | Last-Resort-Eskalationsstufe |

| `prompt-engineer` | Der ultimative Experte für Prompt-Engineering |

| `refactoring-specialist` | Systematische großflächige Code-Transformation mit Sicherheitsnetz: Strangler... |

| `release` | Versioning, Changelog, Build-Artifact, GitHub Release erstellen |

| `requirements` | Anforderungen aufnehmen, REQ-IDs vergeben, REQUIREMENTS.md pflegen |

| `senior-developer` | Komplexe Features, Architektur-Entscheidungen, schwierige Bugs, Cross-Cutting... |

| `technical-writer` | Externe entwickler- und nutzergerichtete Doku: API-Referenzen, Getting-Starte... |

| `tester` | TDD, Test-Suite ausführen, Testabdeckung sichern |

| `ui-ux-designer` | UI-Spezifikationen, Mockups und Design-Systeme erstellen. |

| `validator` | Code gegen REQs prüfen, DoD-Checkliste, Traceability-Audit |


## Knowledge Engine
> Nutze `knowledge-engine`, um komplexe Analysen und Context-Queries durchzuführen.


## Regeln

# A2A Anti-Re-Delegation Gates

1. Limit depth to 10, no self-handoff.
2. Short payload: `payload.t` max 300 Zeichen.
3. No Re-Delegation (payload starts with "Du bist...").
4. Singleton Orchestrator: NUR der `main_chat` darf den `orchestrator` spawnen.
5. Execution-Trace-Isolation: Worker-Output muss strukturiert sein (STATUS, RESULT, ARTIFACTS). Keine rohen Logs propagieren.



# Branch-Guard

Verwende Feature-Branches (`feat/`, `fix/`, `chore/`). Keine Code-Änderungen direkt auf `main` oder `master`.



# Commit-Konventionen

Verwende Conventional Commits (feat, fix, chore).
Beschreibungssprache: `Englisch`
Max 72 Zeichen in erster Zeile. Imperativ.

Format: `<type>: <beschreibung>` (Bsp: `feat: ...`)




# GitHub Issue Lifecycle

Issues referenzieren und am Ende mit passendem Keyword (`Fixes #123`, `Closes #123`) im PR oder Commit schließen. Kommentiere das Issue nach Fertigstellung.



# Sprachregeln

| Kontext | Sprache |
|---|---|
| User-Kommunikation | **Deutsch** |
| User-Input | **Deutsch** |
| Externe Doku | **Englisch** |
| Interne Doku | **Deutsch** |
| Code/Commits | **Englisch** |



# Lifecycle-Tasks

Beim Start prüfen: existiert `.gemini/pending-tasks.md`?
Falls ja und enthält `- [ ]`: User fragen ob delegiert werden soll.
Nach Erledigung: löschen. Datei nicht committen.



# No Worktree Isolation

**Anti-Pattern:** Niemals das Argument `isolation: "worktree"` beim Spawnen von Subagenten verwenden.
**Grund:** Agenten schreiben dann ihren Output in den internen Ordner `.claude/worktrees/agent-<id>/` anstatt in das eigentliche Projektverzeichnis. Das führt zu fehlgeleiteten Dateien und Datenverlust in der eigentlichen Codebase.

Alle Agenten müssen direkt im Projektverzeichnis arbeiten (Isolation deaktivieren oder weglassen). Der `.claude/` Ordner (sowie `.gemini/`, `.continue/`, `.mammouth/` etc.) ist strikt als Infrastruktur-Ordner zu betrachten und darf nicht für Arbeitskopien missbraucht werden.



# Provider-Agnostic Policy

Generische Templates in `1-generic/` müssen provider-agnostisch sein. Keine spezifischen Prompts für Claude, Gemini etc., außer als Fallback/Feature-Flag.



# Python Conventions

PEP8 einhalten. Type Hints (typing) verwenden. Docstrings für Klassen/Methoden schreiben.



# Session-Abschluss

Delegate Session-Zusammenfassung an `documenter` am Ende großer Features, um CODEBASE_OVERVIEW.md aktuell zu halten.



# Submodule-Schutzkonzept

Regeln für den Umgang mit dem `.agent-meta`-Submodul und `.gitmodules`:

- **Keine direkten Änderungen in `.agent-meta/`:** Dateien in `.agent-meta/` dürfen in Konsumenten-Repositories niemals direkt editiert oder committet werden.
- **Keine Mutation von `.gitmodules` / Git Staging:** `.gitmodules` darf nicht automatisch modifiziert werden und Submodule dürfen nicht automatisch via `git add` gestaged werden.
- **Kein Source-Code-Scaffolding in Konsumenten-Projekten:** In Konsumenten-Projekten wird kein Anwendungscode generiert/gerüstet; verwaltet werden ausschließlich `.meta-config/project.yaml` und die Managed Blocks.
- **Framework-Änderungen nur im agent-meta Repo:** Änderungen am agent-meta Framework müssen auf Feature-Branches im agent-meta Repository selbst durchgeführt werden.




# CRITICAL GATE
MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`. Keine Ausnahmen.




## Git Delegation
Git Mutationen (commit, push, add etc) -> `git` Agent. Read-only (status, log) im Main Chat ok.



Native Extensions (Skills/Hooks) erlaubt, ignorieren nicht Branch-Guard/DoD.





Anti-Recursion: Worker dürfen nicht an `orchestrator` zurück delegieren.


## Anti-Patterns
- **Worktree Isolation:** Niemals `isolation: "worktree"` bei Subagenten verwenden (schreibt in interne Infrastruktur-Ordner, führt zu Datenverlust).



# agent-meta — Schichten-Architektur

Dieses Repo ist das Meta-Repository für Agenten-Standards. Jede Änderung an Templates
wirkt sich auf alle Projekte aus die dieses Submodul einbinden.

## Schichten-Modell

```
0-external/   Externe Skill-Agenten aus Drittrepos (via Git Submodule).
              Höchste Priorität. Konfiguriert in config/skills-registry.yaml.
              approved: true/false — Meta-Maintainer Quality Gate.

1-generic/    Universell. Gilt für jedes Projekt. Wird immer generiert,
              solange kein Override in 2-platform oder 3-project existiert.

2-platform/   Plattformspezifisch. Überschreibt den Generic-Agent für alle
              Projekte auf dieser Plattform.
              Modi: Full-replacement (kein extends:) oder Composition (extends: + patches:)

3-project/    Projektspezifisch.
              - <rolle>.md      → Override: ersetzt generierten Agent komplett
              - <rolle>-ext.md  → Extension: additiv geladen vom generierten Agent
```

**Override-Reihenfolge:**
```
1-generic  →  2-platform  →  3-project/<rolle>.md  →  0-external (eigenständige Rollen)
```

## Composition-Syntax (2-platform und 3-project)

```yaml
extends: "1-generic/<rolle>.md"
patches:
  - op: append-after        # nach Section einfügen
    anchor: "## Section"
    content: |
      ## Neue Section ...
  - op: replace             # Section vollständig ersetzen
    anchor: "## Section"
    content: |
      ## Section ...
  - op: delete              # Section entfernen
    anchor: "## Section"
  - op: append              # ans Dateiende anhängen
    content: |
      ## Anhang ...
```

Composition wird zur Build-Zeit aufgelöst — das generierte `.gemini/agents bzw. .opencode/agents/<rolle>.md`
enthält das vollständige Dokument. Kein `extends:` im Output.

## Abhängigkeitsprinzip

Jede Änderung an einer Quelldatei propagiert in alle instanziierten Projekte
beim nächsten `sync.py`-Lauf. Daher:

- **1-generic geändert** → alle Projekte neu syncen
- **2-platform geändert** → alle Projekte auf dieser Plattform neu syncen
- **config/role-defaults.yaml geändert** → alle Projekte neu syncen
- **config/skills-registry.yaml geändert** → alle betroffenen Projekte neu syncen

## Platzhalter-Escape

`{{%VAR%}}` → rendert als `{{%VAR%}}` ohne Substitution (für Dokumentation in Templates)



# agent-meta — Development Conventions

## Hard Invariants

1. `.gemini/agents bzw. .opencode/agents` is generated output — never edit manually. Make changes in `agents/` or `.meta-config/project.yaml`.
2. Bump agent version in frontmatter on every content change:
   - Major (`X.0.0`): renamed variable, changed behavior, new mandatory section
   - Minor (`x.Y.0`): new optional section, expanded scope
   - Patch (`x.y.Z`): text improvements, clarifications, config path fixes
   - Platform agents (`2-platform/`) also keep `based-on` up to date.
3. Placeholders are always `{{%GROSS_MIT_UNTERSTRICH%}}`. Lowercase or mixed case will not match.

## Composition-Risiko: Instruction Bleed

Bei `extends + patches` in `2-platform/` und `3-project/` gilt:

**Instruction Bleed:** Text-Level-Composition kann Behavioral-Logic ungewollt zwischen Schichten übertragen — ein `append-after` an einer Section, die in einer anderen Schicht semantisch umdefiniert wurde, produziert widersprüchliche Instruktionen im generierten Agent.

**Prüfpunkte vor einem Patch-Commit:**
- Überschreibt der Patch eine Section, die in der übergeordneten Schicht eine andere Semantik trägt?
- Erzeugt `append-after` doppelte oder widersprüchliche Regelaussagen?
- Ist der Override vollständig (replace) oder additiv (append-after)? Additiv = höheres Bleed-Risiko.

> Empirische Grundlage: Instruction Bleed Paper (arXiv:2606.26356) belegt Cross-Module-Interference bei Text-Level-Composition als häufige Fehlerquelle.

## Adding a New Agent Role

Manual (required):
1. Create `agents/1-generic/<role>.md` with frontmatter: `name`, `version`, `description`, `hint`, `tools`
2. Add entry in `config/role-defaults.yaml`
3. Update `howto/setup/instantiate-project.md`

Auto-generated by `sync.py` (never edit manually):
- `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.continue/config.yaml`
- `.*/agents/*.md`
- `docs/agent-graph.html`, `docs/agent-mindmap.md`
- `.*/rules/conventions.md`
- `config/project-config.schema.json` roles enum

Only `1-generic/<role>.md`, `config/role-defaults.yaml`, and `howto/setup/instantiate-project.md` are maintained manually.

## Adding a New Placeholder

1. Add to `scripts/lib/config.py` → `build_variables()` or `_inject_dod()`
2. Document in `CLAUDE.md` variables table
3. Add to `howto/project.yaml.example` (optional)

## Change Checklist (before commit)

| Changed | Check |
|---|---|
| `1-generic/<role>.md` | bump version; sync affected projects |
| `2-platform/<platform>-<role>.md` | `version` and `based-on` current? |
| `agents/0-external/_skill-wrapper.md` | re-sync all enabled skills |
| `config/skills-registry.yaml` | re-sync projects |
| `config/role-defaults.yaml` (new role) | update CLAUDE.md + howto files |
| `config/project-config.schema.json` | test IDE autocomplete / jsonschema |
| `hint:` in agent template | sync projects (regenerates `AGENT_HINTS`) |
| `rules/` or `hooks/` | sync projects (overwrites generated copies) |



# agent-meta — sync.py Interface

`sync.py` ist der einzige Weg Agenten zu generieren. Nie direkt in `.gemini/agents bzw. .opencode/agents` schreiben.

Vollständige Referenz (Flags, sync.log, Modulstruktur):
→ `.agent-meta/agents/1-generic/_wf-sync-interface.md`

## Branch-Guard-Erweiterung für agent-meta

Zusätzlich zu den generischen Branch-Guard-Regeln gilt hier:

- `sync.py` ausführen → immer Branch (Sync propagiert in alle Projekte)

**Faustregel: sync.py ausführen oder >1 Datei anfassen → Branch.**

**NIE direkt auf main:** sync.py-Läufe, Template-Änderungen, Rule-Änderungen — egal wie klein.

## Warum

Direkte Commits auf main propagieren Fehler sofort in alle Projekte beim nächsten Sync.

---

## Neue Funktionen: Smart Context Regeneration

### --check Flag (CI-Mode)

```bash
python .agent-meta/scripts/sync.py --check
python .agent-meta/scripts/sync.py --dry-run --check
```

**Verhalten:**
- Exit Code `0` wenn provider context files (CLAUDE.md, AGENTS.md, GEMINI.md, etc.) aktuell sind
- Exit Code `1` wenn Dateien regeneriert werden müssten
- Keine Dateien geschrieben (pure Status-Abfrage)

**Einsatz in CI:** Blockiert PRs wenn `.meta-config/project.yaml` verändert wurde und context files noch nicht neu generiert wurden.

**Vorteil:** Verhindert Drift zwischen Konfiguration und generiertem Projektkontext — besonders wichtig bei Multi-Provider-Setups.

### context-hashes.json (Drift-Erkennung)

Neuer Sidecar-Datei: `.meta-config/context-hashes.json`

```json
{
  "version": 1,
  "hashes": {
    "claude": "sha256:abc123...",
    "gemini": "sha256:def456...",
    "continue": "sha256:ghi789..."
  }
}
```

**Zweck:** Speichert Hashes der generierten statischen Header, um zu erkennen ob der User die Datei manuell bearbeitet hat (Drift).

**Verhalten:**
- Wird bei jedem Sync aktualisiert
- Bei Drift → Backup erstellt (`.CLAUDE.md.sync-backup-<timestamp>`) mit Warnung
- User kann Backup reviewen und Änderungen manuell merge

**WICHTIG: Mit Git committen** — ermöglicht Drift-Erkennung über Rechner und CI hinweg.

**Nicht gitignoren.**

### sync-on-config-change Hook (Automatische Re-Sync)

Neuer Hook in `hooks/1-generic/sync-on-config-change.sh`

**Trigger:** PostToolUse — reagiert auf Write/Edit-Operationen die `.meta-config/project.yaml` verändern

**Aktion:** 
- Erkennt wenn Projekt-Config geändert wurde (z.B. neue Provider hinzugefügt, Rolle aktiviert)
- Schreibt Lifecycle-Task für `agent-meta-manager` in `.claude/pending-tasks.md`
- `agent-meta-manager` merkt beim nächsten Start dass sync.py erneut laufen muss

**Konfiguration in project.yaml:**

```yaml
lifecycle-triggers:
  on-config-change:
    - agent: agent-meta-manager
      task: "Re-run sync.py — project.yaml has changed."

hooks:
  sync-on-config-change:
    enabled: true
```

**Vorteil:** Keine manuellen Sync-Aufrufe nötig wenn Konfiguration sich ändert — vollautomatische Reconciliation.

---

## Zusammenfassung: Provider Context Lifecycle

```
Developer ändert .meta-config/project.yaml
        ↓
sync-on-config-change Hook erkennt änderung
        ↓
lifecycle_check.py schreibt pending-task für agent-meta-manager
        ↓
agent-meta-manager führt sync.py aus
        ↓
sync.py vergleicht context-hashes.json mit aktuellen Hashes
        ↓
Drift erkannt? → Backup + Regeneration
Kein Drift? → Stille Aktualisierung der managed blocks
        ↓
.meta-config/context-hashes.json aktualisiert
```





<!-- agent-meta:managed-end -->





















































## Project Setup

- **Build:** `python scripts/sync.py`
- **Test:** `python scripts/sync.py --validate`
- **Platform:** Python CLI (sync.py)
- **Runtime:** Python 3.x

<!-- agent-meta:bootstrap-begin -->

## Agent Bootstrap — Session-Start Pflicht

Gemini/Antigravity benötigt eine einmalige Agent-Registrierung pro Session.
**Führe folgende Schritte zu Beginn JEDER Session aus:**

1. Lies alle Agenten-Dateien aus `.gemini/agents/`:
   - `accessibility-specialist.md` → registriere als `accessibility-specialist`
   - `agent-meta-manager.md` → registriere als `agent-meta-manager`
   - `agent-meta-scout.md` → registriere als `agent-meta-scout`
   - `api-specialist.md` → registriere als `api-specialist`
   - `bug-feature-analyzer.md` → registriere als `bug-feature-analyzer`
   - `change-manager.md` → registriere als `change-manager`
   - `claude-expert.md` → registriere als `claude-expert`
   - `code-reviewer.md` → registriere als `code-reviewer`
   - `concept-reviewer.md` → registriere als `concept-reviewer`
   - `continue-expert.md` → registriere als `continue-expert`
   - `copilot-expert.md` → registriere als `copilot-expert`
   - `data-engineer.md` → registriere als `data-engineer`
   - `dependency-auditor.md` → registriere als `dependency-auditor`
   - `developer.md` → registriere als `developer`
   - `devops-engineer.md` → registriere als `devops-engineer`
   - `docker.md` → registriere als `docker`
   - `documenter.md` → registriere als `documenter`
   - `e2e-tester.md` → registriere als `e2e-tester`
   - `effort-estimator.md` → registriere als `effort-estimator`
   - `explorer.md` → registriere als `explorer`
   - `export-manager.md` → registriere als `export-manager`
   - `feature.md` → registriere als `feature`
   - `feedback.md` → registriere als `feedback`
   - `gemini-expert.md` → registriere als `gemini-expert`
   - `git.md` → registriere als `git`
   - `home-organization-specialist.md` → registriere als `home-organization-specialist`
   - `ideation.md` → registriere als `ideation`
   - `incident-responder.md` → registriere als `incident-responder`
   - `intern-developer.md` → registriere als `intern-developer`
   - `junior-developer.md` → registriere als `junior-developer`
   - `knowledge-curator.md` → registriere als `knowledge-curator`
   - `knowledge-gardener.md` → registriere als `knowledge-gardener`
   - `knowledge-indexer.md` → registriere als `knowledge-indexer`
   - `knowledge-ingestor.md` → registriere als `knowledge-ingestor`
   - `knowledge-linter.md` → registriere als `knowledge-linter`
   - `knowledge-migrator.md` → registriere als `knowledge-migrator`
   - `knowledge-querier.md` → registriere als `knowledge-querier`
   - `log-analyzer.md` → registriere als `log-analyzer`
   - `mammouth-expert.md` → registriere als `mammouth-expert`
   - `meta-feedback.md` → registriere als `meta-feedback`
   - `opencode-expert.md` → registriere als `opencode-expert`
   - `opengrid-designer.md` → registriere als `opengrid-designer`
   - `orchestrator.md` → registriere als `orchestrator`
   - `performance-optimizer.md` → registriere als `performance-optimizer`
   - `principal-developer.md` → registriere als `principal-developer`
   - `prompt-engineer.md` → registriere als `prompt-engineer`
   - `quality-auditor.md` → registriere als `quality-auditor`
   - `refactoring-specialist.md` → registriere als `refactoring-specialist`
   - `release.md` → registriere als `release`
   - `requirements-architect.md` → registriere als `requirements-architect`
   - `requirements.md` → registriere als `requirements`
   - `risk-analyst.md` → registriere als `risk-analyst`
   - `senior-developer.md` → registriere als `senior-developer`
   - `technical-writer.md` → registriere als `technical-writer`
   - `test-engineer.md` → registriere als `test-engineer`
   - `tester.md` → registriere als `tester`
   - `ui-ux-designer.md` → registriere als `ui-ux-designer`
   - `validator.md` → registriere als `validator`

2. Registriere jeden Agenten via define_subagent API-Call:
   ```
   define_subagent(name="accessibility-specialist", ...)
   define_subagent(name="agent-meta-manager", ...)
   define_subagent(name="agent-meta-scout", ...)
   define_subagent(name="api-specialist", ...)
   define_subagent(name="bug-feature-analyzer", ...)
   define_subagent(name="change-manager", ...)
   define_subagent(name="claude-expert", ...)
   define_subagent(name="code-reviewer", ...)
   define_subagent(name="concept-reviewer", ...)
   define_subagent(name="continue-expert", ...)
   define_subagent(name="copilot-expert", ...)
   define_subagent(name="data-engineer", ...)
   define_subagent(name="dependency-auditor", ...)
   define_subagent(name="developer", ...)
   define_subagent(name="devops-engineer", ...)
   define_subagent(name="docker", ...)
   define_subagent(name="documenter", ...)
   define_subagent(name="e2e-tester", ...)
   define_subagent(name="effort-estimator", ...)
   define_subagent(name="explorer", ...)
   define_subagent(name="export-manager", ...)
   define_subagent(name="feature", ...)
   define_subagent(name="feedback", ...)
   define_subagent(name="gemini-expert", ...)
   define_subagent(name="git", ...)
   define_subagent(name="home-organization-specialist", ...)
   define_subagent(name="ideation", ...)
   define_subagent(name="incident-responder", ...)
   define_subagent(name="intern-developer", ...)
   define_subagent(name="junior-developer", ...)
   define_subagent(name="knowledge-curator", ...)
   define_subagent(name="knowledge-gardener", ...)
   define_subagent(name="knowledge-indexer", ...)
   define_subagent(name="knowledge-ingestor", ...)
   define_subagent(name="knowledge-linter", ...)
   define_subagent(name="knowledge-migrator", ...)
   define_subagent(name="knowledge-querier", ...)
   define_subagent(name="log-analyzer", ...)
   define_subagent(name="mammouth-expert", ...)
   define_subagent(name="meta-feedback", ...)
   define_subagent(name="opencode-expert", ...)
   define_subagent(name="opengrid-designer", ...)
   define_subagent(name="orchestrator", ...)
   define_subagent(name="performance-optimizer", ...)
   define_subagent(name="principal-developer", ...)
   define_subagent(name="prompt-engineer", ...)
   define_subagent(name="quality-auditor", ...)
   define_subagent(name="refactoring-specialist", ...)
   define_subagent(name="release", ...)
   define_subagent(name="requirements-architect", ...)
   define_subagent(name="requirements", ...)
   define_subagent(name="risk-analyst", ...)
   define_subagent(name="senior-developer", ...)
   define_subagent(name="technical-writer", ...)
   define_subagent(name="test-engineer", ...)
   define_subagent(name="tester", ...)
   define_subagent(name="ui-ux-designer", ...)
   define_subagent(name="validator", ...)
   ```

3. Erst danach: Bearbeite User-Anfragen (Delegation an Orchestrator etc.)

> **Ohne diese Registrierung existieren die Agenten NICHT in der Runtime**
> und der Orchestrator kann nicht delegieren.
<!-- agent-meta:bootstrap-end -->


<!-- headroom:rtk-instructions -->
# RTK (Rust Token Killer) - Token-Optimized Commands

When running shell commands, **always prefix with `rtk`**. This reduces context
usage by 60-90% with zero behavior change. If rtk has no filter for a command,
it passes through unchanged — so it is always safe to use.

## Key Commands
```bash
# Git (59-80% savings)
rtk git status          rtk git diff            rtk git log

# Files & Search (60-75% savings)
rtk ls <path>           rtk read <file>         rtk grep <pattern>
rtk find <pattern>      rtk diff <file>

# Test (90-99% savings) — shows failures only
rtk pytest tests/       rtk cargo test          rtk test <cmd>

# Build & Lint (80-90% savings) — shows errors only
rtk tsc                 rtk lint                rtk cargo build
rtk prettier --check    rtk mypy                rtk ruff check

# Analysis (70-90% savings)
rtk err <cmd>           rtk log <file>          rtk json <file>
rtk summary <cmd>       rtk deps                rtk env

# GitHub (26-87% savings)
rtk gh pr view <n>      rtk gh run list         rtk gh issue list

# Infrastructure (85% savings)
rtk docker ps           rtk kubectl get         rtk docker logs <c>

# Package managers (70-90% savings)
rtk pip list            rtk pnpm install        rtk npm run <script>
```

## Rules
- In command chains, prefix each segment: `rtk git add . && rtk git commit -m "msg"`
- For debugging, use raw command without rtk prefix
- `rtk proxy <cmd>` runs command without filtering but tracks usage
<!-- /headroom:rtk-instructions -->
