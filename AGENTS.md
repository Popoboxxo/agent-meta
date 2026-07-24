# agent-meta

agent-meta ist ein Git-Repository das als Submodul in Projekte eingebunden wird. Es stellt standardisierte Claude-Agenten-Templates bereit (1-generic, 2-platform, 0-external) und generiert via sync.py projektfertige Agenten-Dateien in .claude/agents/. Das Repo verwendet sich selbst — die hier generierten Agenten koordinieren die Weiterentwicklung von agent-meta.

<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on every sync. -->
<!-- Manual changes here will be overwritten. -->

> **AI ROUTING:** Claude -> CLAUDE.md | Opencode -> AGENTS.md | Gemini -> .gemini/GEMINI.md

Generiert von agent-meta v0.82.0 — `2026-07-24`
DoD-Preset: **rapid-prototyping** | REQ-Traceability: false | Tests: false | Codebase-Overview: false | Security-Audit: false

> **Einstiegspunkt:** Starte mit dem `orchestrator`-Agenten für alle Entwicklungsaufgaben — Ausnahmen siehe Abschnitt »Orchestrator — Universal Router«.

| Agent | Zuständigkeit |
|-------|--------------|
| `accessibility-specialist` | Accessibility-Audit: WCAG 2.1/2.2, ARIA, Keyboard-Nav, Screenreader-Guidelines, Kontrast, Focus-Management, A11y-Tree — Findings mit A/AA/AAA-Severity |
| `agent-meta-manager` | agent-meta verwalten: Upgrade, Sync, Feedback, projektspezifische Agenten anlegen |
| `agent-meta-scout` | KI-Ökosystem scouten: neue Skills, Rollen, Rules und Patterns für agent-meta entdecken |
| `api-specialist` | Verwende diesen Agenten fuer API-Design, OpenAPI-Spezifikationen und Contract-First Development. |
| `bug-feature-analyzer` | Issue-Triage: Bug vs. User-Error vs. Feature vs. Out-of-Scope klassifizieren — vor developer/feature-Delegation |
| `claude-expert` | Claude Code Experte: Funktionsweise, .claude Konfiguration, Best Practices |
| `code-reviewer` | Prüft Code-Qualität, Blast-Radius und Clean Code — nicht funktionale Korrektheit (das macht validator). |
| `concept-reviewer` | Konzept/Design-Doc reviewen: Vollständigkeit, Logik, Risiken, Approve/Iterate |
| `continue-expert` | Continue Experte: Funktionsweise, .continue Konfiguration, Best Practices |
| `copilot-expert` | GitHub Copilot Experte: Funktionsweise, .github/copilot Konfiguration, Best Practices |
| `data-engineer` | Data-Pipelines: ETL/ELT, Schema-Migration (Datenebene), Data-Quality, Lineage, Pipeline-Monitoring, Streaming/Batch — übergibt Pipeline-Spec an developer |
| `developer` | Feature-Implementierung und Bugfixes im agent-meta Framework (Python, Markdown, YAML) |
| `devops-engineer` | Verwende diesen Agenten fuer CI/CD, IaC, Kubernetes, Monitoring und Infrastructure-Aufgaben. |
| `docker` | Dev-Stack starten/stoppen, Dockerfiles, Binary-Management |
| `documenter` | Doku pflegen: CODEBASE_OVERVIEW, ARCHITECTURE, README, Erkenntnisse |
| `e2e-tester` | Browser-Testing-Agent: E2E-Flows, visuelle Regression, Accessibility-Audit — nicht für Unit-Tests |
| `effort-estimator` | Aufwandsschätzung für Tasks — delegiere hierher wenn User nach Zeit/Kosten fragt |
| `explorer` | Codebase analysieren / Dependencies / Impact — read-only, delegiert Findings |
| `export-manager` | Verwende diesen Agenten fuer Export-Routing von strukturierten Daten zu konfigurierten Targets. |
| `feature` | Feature-Lifecycle-Subagent: Branch → REQ → TDD → Dev → Validate → PR. Wird vom Orchestrator gestartet, nicht direkt vom User. |
| `feedback` | Projekt-Feedback: Bugs, Features, Verbesserungen als GitHub Issues standardisiert einreichen — immer vor git |
| `gemini-expert` | Gemini Experte: Funktionsweise, .gemini Konfiguration, Best Practices |
| `git` | Commits, Branches, Tags, Push/Pull und alle Git-Operationen |
| `ideation` | Neue Ideen explorieren, Vision schärfen, Übergabe an requirements |
| `junior-developer` | Low-Tier-Developer: triviale Fixes, Typos, kleine klar umrissene Änderungen — eskaliert bei Scope-Überschreitung |
| `knowledge-curator` | Wiki-Strategie, Schema-Evolution, OKF-Compliance |
| `knowledge-gardener` | Wiki-Pflege: Links, Tags, Frontmatter, Typos, Timestamps |
| `knowledge-indexer` | index.md und log.md pflegen — nur als Delegationsziel anderer Knowledge-Agenten |
| `knowledge-ingestor` | Sources verarbeiten, Wiki-Seiten schreiben, Cross-References pflegen |
| `knowledge-linter` | Wiki-Healthcheck: 10 Lint-Checks (Karpathy + OKF) |
| `knowledge-migrator` | Vorhandene Docs ins Wiki migrieren (einmalig, mit User-Freigabe) |
| `knowledge-querier` | Wiki-Fragen beantworten, Index-First, Synthese mit Citations |
| `log-analyzer` | Log-Analyse: Fehler clustern, Severity klassifizieren (RFC 5424), Findings als Issues oder Tasks delegieren |
| `mammouth-expert` | Mammouth Code Experte: Funktionsweise, .mammouth Konfiguration, Best Practices |
| `meta-feedback` | Verbesserungsvorschläge für agent-meta als GitHub Issues einreichen |
| `opencode-expert` | Opencode Experte: Funktionsweise, .opencode Konfiguration, Best Practices |
| `orchestrator` | Einstiegspunkt für ALLE Entwicklungsaufgaben — zerlegt komplexe Tasks und dispatched parallel |
| `performance-optimizer` | Verwende diesen Agenten fuer Performance-Analyse, Big-O-Optimierung und Bottleneck-Beseitigung. |
| `principal-developer` | Last-resort developer: only after senior-developer failed multiple times — root-cause analysis, systemic reasoning, no symptom fixes. The most expensive call in the system. |
| `prompt-engineer` | Prompts und Agenten entwerfen oder reviewen |
| `refactoring-specialist` | Systematische Transformation: Strangler Fig, inkrementelles Refactoring, Legacy-Modernisierung, Feature-Flag-Rewrites — braucht exklusiven Zugriff auf betroffene Module |
| `release` | Versioning, Changelog, Build-Artifact, GitHub Release erstellen |
| `requirements` | Anforderungen aufnehmen, REQ-IDs vergeben, REQUIREMENTS.md pflegen |
| `senior-developer` | High-Tier-Developer: Architektur-Impact, komplexe/riskante Änderungen, schwierige Bugs — analysiert erst, implementiert dann |
| `technical-writer` | Externe Doku: API-Referenz, Getting-Started, SDK-Docs, Tutorials, CLI-Help, User-Release-Notes, Microcopy — für externe Entwickler und Endnutzer |
| `tester` | Tests schreiben (TDD), Test-Suite ausführen, Coverage sicherstellen |
| `ui-ux-designer` | UI-Spezifikation, Mockup-Erstellung und Design-System-Definition — implementiert nicht, spezifiziert. |
| `validator` | Interner Qualitäts-Checker: DoD-Checkliste, Traceability-Audit. Wird vom Orchestrator nach der Implementierung aufgerufen. Nicht für direkte User-Fragen oder Setup-Hilfe. |

## Knowledge Engine

Die Knowledge Engine ist aktiviert. Domäne: **personal**.

**Bundle-Pfad:** `knowledge/`
| Pfad | Zweck |
|------|-------|
| `knowledge/schema.md` | Steuerungsdokument — Konventionen, Concept Types, Workflows |
| `knowledge/sources/` | Immutable Raw Sources — LLM liest, modifiziert NIEMALS |
| `knowledge/wiki/` | OKF Knowledge Bundle — LLM-owned, strukturiertes Wiki |
| `knowledge/wiki/index.md` | Content-Katalog aller Wiki-Seiten (OKF §6) |
| `knowledge/wiki/log.md` | Chronologisches Event-Log (OKF §7) |

### Knowledge-Agenten
- **Schema-Owner:** `knowledge-curator` verwaltet `knowledge/schema.md` und Concept-Type-Konventionen

### Knowledge-Workflows
- **Ingest:** Source in `knowledge/sources/` ablegen → `knowledge-ingestor` verarbeitet → Wiki aktualisiert
- **Query:** Frage stellen → `knowledge-querier` durchsucht Index → synthetisiert Antwort
- **Lint:** `knowledge-linter` prüft Wiki-Gesundheit (Widersprüche, Orphans, OKF-Compliance)
- **Migration:** `knowledge-migrator` räumt vorhandene Inhalte auf und migriert ins OKF-Format
- **Gardening:** `knowledge-gardener` pflegt Links, Tags, Typos, Timestamps

## Agents

- **OpenCode:** Agent files in `.opencode/agents/`. Invoke by name.


## Regeln

# A2A Anti-Re-Delegation Gates

Provider-agnostische Regeln für A2A-Handoffs zwischen Agenten. Verhindert Delegations-Schleifen und unkontrollierten Spec-Dump in `payload.t`.

## Hard Reject Gates (jeder Verstoß → Dispatch ablehnen, User informieren)

1. **Self-Handoff verboten:** `source_agent == target_agent` ist ein harter Strukturfehler. Niemals akzeptieren.
2. **Tiefenlimit:** `delegation_depth` darf maximal `10` sein (konfigurierbar via `orchestrator.delegation.max_depth` in project.yaml, Default 10). Tiefer = struktureller Fehler im Aufrufer. Gilt nur für Provider ohne Plattform-Limit
3. **T-Size-Limit:** `payload.t` darf maximal `300 Zeichen` umfassen. Bei Überschreitung → kein Dispatch, User informieren.
4. **Re-Delegation-Detection:** Wenn `payload.t` mit "Du bist" / "Du bist ein" / "Du bist eine" beginnt → das ist ein Re-Delegations-Versuch. Ablehnen, User informieren.

## Werte

- `delegation_depth`:
  - `0` = Hauptchat (User-Eingang)
  - `1` = Orchestrator (Routing-Ebene)
  - `2+` = Worker / Sub-Worker (Ausführungs-Ebene, bis 10)
- Hochzählen: bei jeder Delegation inkrementiert der Absender das Feld um 1.

## Verhalten bei Verstoß

| Verstoß | Aktion |
|---------|--------|
| `source_agent == target_agent` | HARD REJECT, keine Ausführung, User informieren |
| `delegation_depth > 10` | HARD REJECT, User informieren |
| `payload.t > 300 Zeichen` | KEIN Dispatch, User informieren ("kürze auf einen Satz") |
| `payload.t` startet mit "Du bist..." | HARD REJECT, User informieren ("Re-Delegation erkannt") |

## Singleton-Regel: Orchestrator-Spawn

**NUR der `main_chat` darf den `orchestrator` spawnen. Worker-Agents niemals.**

- `delegation_depth >= 2` → kein `subagent_type="orchestrator"` Dispatch erlaubt
- Verstoß → HARD REJECT, User informieren: "Singleton-Regel verletzt: Orchestrator darf nur vom main_chat gespawnt werden."

| Verstoß | Aktion |
|---------|--------|
| Worker ruft `task(subagent_type="orchestrator", ...)` | HARD REJECT, User informieren |
| Worker ruft `Agent(subagent_type="orchestrator", ...)` | HARD REJECT, User informieren |

## Execution-Trace-Isolation

Worker-Output an den Orchestrator muss eine **strukturierte Zusammenfassung** sein — keine rohen Execution-Traces propagieren.

**Pflicht:**
- Ergebnis in Kategorien: STATUS, RESULT, ARTIFACTS, ERRORS
- Interne Zwischenschritte (Tool-Calls, Reasoning) nicht an übergeordnete Agenten weitergeben
- Orchestrator fasst BARRIER-Ergebnisse weiter zusammen (Context Pollution verhindern)

**Verboten:**
- Rohe Bash-Outputs (Hunderte Zeilen) als Ergebnis zurückgeben
- Vollständige Datei-Inhalte in Ergebnis einbetten (→ Artifact Pattern verwenden)
- Sub-Agent-Kontexte mit Orchestrator-Kontext mischen

## Provider-Limits

| Provider | Max. Tiefe | Konfigurierbar? | Empfehlung |
|----------|-----------|-----------------|-----------|
| Gemini / OpenCode / Continue | kein Limit bekannt | via `A2A_MAX_DEPTH` | Default 10 ausreichend |

---

# Branch-Guard — Feature-Branch Pflicht

**Gilt für alle code-ändernden Aufgaben.**

## Pflicht vor dem ersten Edit

```bash
git branch --show-current
```

Auf `main`/`master` → Branch anlegen: `feat/<thema>` | `fix/<thema>` | `refactor/<thema>`

Auf anderem Branch → weiterarbeiten (Branch existiert bereits).

Bei detached HEAD oder leerem Branch-Namen → **stoppe** und frage den User nach dem Ziel-Branch. Keinen Branch raten.

## Branch PFLICHT wenn

- Zwei oder mehr Dateien betroffen (tracked files im working tree, inkl. neuer Dateien)
- Inhaltliche Änderung an Templates, Rules, Scripts
- GitHub Issue bearbeitet

**Faustregel: Änderung betrifft ≥2 Dateien ODER berührt agents/, rules/, hooks/, scripts/, config/ → Branch.**

## Direkt auf main erlaubt (Ausnahmen)

Nur: Version-Bump (`VERSION`, `CHANGELOG.md`, `README.md`) | einzelner Tippfehler (1 Datei, 1 Zeile, User-Bestätigung) | Post-Merge-Pflege nach Review.

**NIE für:** Templates, Rules, Scripts — egal wie klein. Nie für Issue-Arbeit.

---

# Commit-Konventionen (Conventional Commits)

Gilt für alle Agenten die Commits erstellen oder vorbereiten.

## Format

```
<type>(REQ-xxx): <beschreibung>   ← mit req-traceability
<type>: <beschreibung>            ← ohne req-traceability
```

| Type | Bedeutung | REQ-ID |
|------|-----------|--------|
| `feat` | Neues Feature | Wenn `req-traceability` aktiv |
| `fix` | Bugfix | Wenn `req-traceability` aktiv |
| `refactor` | Refactoring ohne Verhaltensänderung | Wenn `req-traceability` aktiv |
| `test` | Tests hinzufügen/ändern | Wenn `req-traceability` aktiv |
| `chore` | Wartung: Dependencies, Config, Versions-Bumps | **Nie** |
| `docs` | Dokumentation | **Nie** |
| `ci` | CI/CD-Änderungen | **Nie** |

## Regeln

- Beschreibung im **Imperativ**: `add feature`, nicht `added feature`
- Maximal **72 Zeichen** in der ersten Zeile
- Beschreibungssprache: `Englisch`
- Body optional: Was **und warum** geändert wurde

## Beispiele

**Mit req-traceability:**
```
feat(REQ-042): add queue persistence across restarts
fix(REQ-017): prevent duplicate video entries on reconnect
test(REQ-042): add persistence tests
chore: bump version to 1.2.0
docs: update installation instructions
```

**Ohne req-traceability:**
```
feat: add queue persistence across restarts
fix: prevent duplicate video entries on reconnect
chore: bump version to 1.2.0
```

---

# Definition of Done (DoD)

Aufgabe abgeschlossen wenn alle **aktiven** Kriterien erfüllt sind.

## Immer Pflicht

- [ ] Code implementiert die Aufgabe vollständig
- [ ] Code-Konventionen eingehalten
- [ ] Commit-Message im Conventional-Commits-Format
- [ ] Keine Regressions

**Keine finale Antwort und keine Commit-Empfehlung** ohne Prüfung aller aktiven Kriterien.

---

# GitHub Issue Lifecycle

Wenn deine Arbeit mit einem GitHub Issue verknüpft ist, schließe es nach Abschluss ab.

Ist keine Issue-Nummer bekannt oder kein GitHub-Issue verknüpft → Issue-Phase überspringen. Dokumentiere: „Issue nicht verknüpft".

## Pflicht nach erledigter Arbeit

1. **Kommentiere das Issue** — kurze Zusammenfassung was implementiert wurde und in welchem Commit
2. **Schließe das Issue** — `gh issue close <number>`

```bash
# Kommentar + schließen in einem Schritt
gh issue close <number> --comment "Implemented in <commit>: <one-line summary>"

# Oder separat (wenn ausführlicherer Kommentar gewünscht)
gh issue comment <number> --body "..."
gh issue close <number>
```

## Wann gilt das?

- Nach jedem abgeschlossenen Feature, Bugfix oder Task der einem Issue zugeordnet ist
- Auch wenn kein PR erstellt wird (direkte Commits auf main)
- Der `git`-Agent kennt den vollständigen Workflow (inkl. Formulierungshilfe)

## Commit-Message-Referenz

Issue-Referenzen in Commit-Messages sind optional, aber empfohlen:
```
feat(REQ-042): add queue persistence  (closes #22)
```

## Fehlerbehandlung

- `gh` CLI nicht verfügbar oder nicht authentifiziert → **Stoppe** die Issue-Phase und melde den Fehler. Kein Issue-Status raten.
- `gh issue close` oder `gh issue comment` schlägt fehl → Fehler eindeutig melden, keine Annahmen über den Issue-Status treffen.

## Delegation

Für GitHub-Operationen → `git`-Agent

---

# Sprachregeln

Diese Regel gilt für alle Agenten und den Hauptchat.

## Sprachzuordnung

| Kontext | Sprache |
|---------|---------|
| Kommunikation mit dem Nutzer | **Deutsch** |
| Nutzer-Eingaben verstehen | **Deutsch** |
| Externe Dokumente (README, CHANGELOG, Release Notes, GitHub Issues) | **Englisch** |
| Interne Dokumente (CODEBASE_OVERVIEW, ARCHITECTURE, REQUIREMENTS, Berichte) | **Deutsch** |
| Code-nahe Artefakte (Kommentare, Commit-Messages, Test-Beschreibungen) | **Englisch** |

## Rollenspezifische Präzisierungen

Agenten-Templates können zusätzliche Präzisierungen für ihren spezifischen Output-Typ enthalten
(z.B. welche Datei unter welche Kategorie fällt). Diese Regel definiert den Rahmen — die
rollenspezifische Zuordnung konkretisiert ihn.

---

# Lifecycle-Tasks — Ausstehende Aufgaben prüfen

Beim Start einer neuen Konversation: prüfe ob `.opencode/pending-tasks.md` existiert.

## Pflicht beim Konversations-Start

```bash
# Prüfen ob Lifecycle-Tasks ausstehen
test -f .opencode/pending-tasks.md && cat .opencode/pending-tasks.md
```

Wenn die Datei existiert und offene Tasks enthält (`- [ ]`):

1. Informiere den User:
   > "Es gibt ausstehende Lifecycle-Tasks aus einem Git-Event. Soll ich diese jetzt bearbeiten?"

2. Zeige die offenen Tasks kompakt (Agent + Aufgabe, eine Zeile je Task).

3. Wenn User bestätigt → delegiere Tasks an die genannten Agenten.

4. Nach Erledigung aller Tasks: lösche `.opencode/pending-tasks.md`.

## Wann diese Rule greift

Lifecycle-Tasks entstehen wenn der `lifecycle-check`-Hook aktiv ist und ein konfiguriertes
Git-Event erkannt wird (z.B. Release-Tag, Version-Bump, Merge).

Konfiguration in `.meta-config/project.yaml`:
```yaml
lifecycle-triggers:
  on-release:
    - agent: documenter
      task: "Update CODEBASE_OVERVIEW.md and ARCHITECTURE.md for this release."
  on-merge:
    - agent: code-reviewer
      task: "Post-Merge Blast-Radius-Analyse: Prüfe betroffene Code-Pfade auf Clean-Code-Verletzungen."
```

## Wenn keine Tasks offen sind

Datei existiert nicht oder enthält keine `- [ ]` Zeilen → nichts tun.
Datei nicht committen — sie ist gitignored (`.opencode/pending-tasks.md`).

---

# Provider-Agnostic Policy — Generic Templates

**Generische Agenten-Templates (1-generic/) müssen universell und provider-agnostisch bleiben.**

## Verboten in 1-generic/

- Provider-Namen (Claude, Gemini, Opencode, Continue, VS Code, etc.)
- Provider-spezifische Tool-Aufruf-Syntax (at-agent, claude -a, define_subagent, etc.)
- Provider-spezifische Dateipfade (.claude/, .gemini/, etc.)
- Provider-spezifische APIs oder Protokolle

## Erlaubt in 1-generic/

- Abstrakte Konzepte ("Agent", "Orchestrator", "Subagent", "Task", "Rule")
- Platzhalter (geschrieben als GROSS_MIT_UNTERSTRICH in doppelten geschweiften Klammern) die vom Sync-Prozess substituiert werden
- Generische Hinweise auf Umgebungsverhalten ("nativer Planungsmodus", "Fallback")

## Wo Provider-Spezifika hingehören

| Ebene | Ort | Beispiel |
|-------|-----|----------|
| **2-platform/** | Plattform-spezifische Overrides | 2-platform/gemini-orchestrator.md |
| **Sync-Generierung** | scripts/lib/agents.py injiziert Provider-spezifische Felder | model, memory, permissionMode |
| **3-project/** | Projekt-spezifische Erweiterungen | .gemini/3-project/am-orchestrator-ext.md |

## Prüfung

Bevor ein Commit in 1-generic/ gemerged wird:
- Enthält der Text Provider-Namen? → Ablehnen oder in 2-platform/ verschieben
- Enthält der Text Tool-Syntax eines Providers? → Ablehnen oder abstrahieren

---

# Python Conventions

**Gilt für alle Python-Dateien (`*.py`).**

## Code Style

- PEP 8 einhalten
- Type Hints verwenden wo möglich
- Docstrings für alle öffentlichen Funktionen/Klassen

## Imports

- Standard Library → Third Party → Local
- Keine wildcard imports (`from x import *`)

---

# Session-Abschluss — Erkenntnisse sichern

Gilt für Hauptchat und Orchestrator.

## Session-Ende erkennen

Signale dass eine Session abgeschlossen ist:

- User sagt "tschüss", "bye", "bis später", "fertig", "done", "das war's"
- User fragt nach einem Commit oder Push (Task ist abgeschlossen)
- User wechselt explizit das Thema zu etwas Unverbundenem
- User fragt "was haben wir heute gemacht?"

## Pflicht bei Session-Ende

Wenn ein Signal erkannt wird und in der Session etwas Nennenswertes passiert ist
(Code geändert, Architektur-Entscheid getroffen, Bug analysiert, Feature implementiert):

> "Session abschließen? Ich kann die Erkenntnisse an den documenter-Agenten delegieren."

Bei Bestätigung → `documenter` mit Session-Zusammenfassung delegieren:
- Was wurde implementiert / gefixt / entschieden
- Offene Punkte / Follow-ups
- Wichtige Erkenntnisse (Probleme, Lösungsansätze, Architektur-Änderungen)

## Wann NICHT fragen

- Kurze Fragen ohne Code-Änderungen (nur Erklärungen, Reviews ohne Fixes)
- User hat Erkenntnisse bereits explizit gespeichert
- Session war trivial (1 Datei, 1 Zeile Fix)

---

# CRITICAL GATE — VERIFY BEFORE EVERY ACTION

YOU ARE THE MAIN CHAT. Do not perform code changes directly.
- No `edit`, `write`, or mutating `bash` calls
- No `task` calls — delegate only to `orchestrator`
- Read-only bash allowed: `git status`, `git log`, `git diff`, `git branch --show-current`, `git branch -l`
- All git mutations → `git` agent
- Every dev task → `orchestrator` first

Violation: PreToolUse hook blocks these changes.

# Orchestrator — Universal Router

**STRICT MODE — no exceptions.** Every dev task goes through `orchestrator`. No user override, no direct dispatch.

Auto-handoff: the main chat always delegates to `orchestrator` via a native tool call — no `@orchestrator` mention in output.

## Git Delegation — Hard Rule

All mutating git commands must run through the `git` agent.

Forbidden in main chat: `git commit`, `git push`, `git pull`, `git add`, `git rm`, `git mv`, `git branch`, `git merge`, `git rebase`, `git reset`, `git restore`, `git checkout`, `git tag`, `git stash`.

Allowed read-only: `git status`, `git log`, `git diff`, `git branch --show-current`, `git branch -l`, `git remote -v`, `git show`.

All other git operations → `git` agent.

## Native Provider-Erweiterungen

Native Erweiterungsmechanismen der Plattform — Skills, Plugins, Lifecycle-Hooks — werden von diesem Gate NICHT blockiert. Sie laufen im Rahmen des eigenen Invocation-Flows der Plattform (z.B. ein SessionStart-Hook, der eine Skill lädt) und zählen nicht als `task`-Call oder `edit`/`write`-Aktion im Sinne dieser Regel. Folge ihren Anweisungen gemäß Plattform-Konvention. Das hebt Branch-Guard, Commit-Konventionen und DoD-Criteria NICHT auf — die gelten weiterhin für jede daraus resultierende Code-Änderung.

## Anti-Recursion Guard

Workers must not re-delegate to `orchestrator`. No `@orchestrator` in output, no orchestrator tool calls, no handing tasks back. Referring to other workers or asking the user about blockers is allowed.

---

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

Composition wird zur Build-Zeit aufgelöst — das generierte `.opencode/agents/<rolle>.md`
enthält das vollständige Dokument. Kein `extends:` im Output.

## Abhängigkeitsprinzip

Jede Änderung an einer Quelldatei propagiert in alle instanziierten Projekte
beim nächsten `sync.py`-Lauf. Daher:

- **1-generic geändert** → alle Projekte neu syncen
- **2-platform geändert** → alle Projekte auf dieser Plattform neu syncen
- **config/role-defaults.yaml geändert** → alle Projekte neu syncen
- **config/skills-registry.yaml geändert** → alle betroffenen Projekte neu syncen

## Platzhalter-Escape

`{{VAR}}` → rendert als `{{VAR}}` ohne Substitution (für Dokumentation in Templates)

---

# agent-meta — Development Conventions

## Hard Invariants

1. `.opencode/agents` is generated output — never edit manually. Make changes in `agents/` or `.meta-config/project.yaml`.
2. Bump agent version in frontmatter on every content change:
   - Major (`X.0.0`): renamed variable, changed behavior, new mandatory section
   - Minor (`x.Y.0`): new optional section, expanded scope
   - Patch (`x.y.Z`): text improvements, clarifications, config path fixes
   - Platform agents (`2-platform/`) also keep `based-on` up to date.
3. Placeholders are always `{{GROSS_MIT_UNTERSTRICH}}`. Lowercase or mixed case will not match.

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

---

# agent-meta — sync.py Interface

`sync.py` ist der einzige Weg Agenten zu generieren. Nie direkt in `.opencode/agents` schreiben.

Vollständige Referenz (Flags, sync.log, Modulstruktur):
→ `.agent-meta/agents/1-generic/_wf-sync-interface.md`

## Branch-Guard-Erweiterung für agent-meta

Zusätzlich zu den generischen Branch-Guard-Regeln gilt hier:

- `sync.py` ausführen → immer Branch (Sync propagiert in alle Projekte)

**Faustregel: sync.py ausführen oder >1 Datei anfassen → Branch.**

**NIE direkt auf main:** sync.py-Läufe, Template-Änderungen, Rule-Änderungen — egal wie klein.

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

---

# Kommunikationsstil: Short

**Diese Regel gilt für alle Antworten und überschreibt alle anderen Stilanweisungen.**

- Keine Begrüßung. Kein Abschluss. Keine Zusammenfassung.
- Keine Floskeln: kein "Gerne", "Natürlich", "Ich werde jetzt...", "Zusammenfassend lässt sich sagen...".
- Nur Fakten und Ergebnisse. Was ist passiert, was fehlt, was als nächstes.
- Bullet Points statt Fließtext. Maximal 1 Satz pro Punkt.
- Erklärungen nur auf explizite Nachfrage des Nutzers.
- Code-Blöcke ohne Einleitung — einfach zeigen.
- Fehler: direkt benennen, keine Entschuldigung.
- Rückfragen: 1 Satz, kein Kontext drumherum.

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
   - `claude-expert.md` → registriere als `claude-expert`
   - `code-reviewer.md` → registriere als `code-reviewer`
   - `concept-reviewer.md` → registriere als `concept-reviewer`
   - `continue-expert.md` → registriere als `continue-expert`
   - `copilot-expert.md` → registriere als `copilot-expert`
   - `data-engineer.md` → registriere als `data-engineer`
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
   - `ideation.md` → registriere als `ideation`
   - `junior-developer.md` → registriere als `junior-developer`
   - `log-analyzer.md` → registriere als `log-analyzer`
   - `mammouth-expert.md` → registriere als `mammouth-expert`
   - `meta-feedback.md` → registriere als `meta-feedback`
   - `opencode-expert.md` → registriere als `opencode-expert`
   - `orchestrator.md` → registriere als `orchestrator`
   - `performance-optimizer.md` → registriere als `performance-optimizer`
   - `principal-developer.md` → registriere als `principal-developer`
   - `prompt-engineer.md` → registriere als `prompt-engineer`
   - `refactoring-specialist.md` → registriere als `refactoring-specialist`
   - `release.md` → registriere als `release`
   - `requirements.md` → registriere als `requirements`
   - `senior-developer.md` → registriere als `senior-developer`
   - `technical-writer.md` → registriere als `technical-writer`
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
   define_subagent(name="claude-expert", ...)
   define_subagent(name="code-reviewer", ...)
   define_subagent(name="concept-reviewer", ...)
   define_subagent(name="continue-expert", ...)
   define_subagent(name="copilot-expert", ...)
   define_subagent(name="data-engineer", ...)
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
   define_subagent(name="ideation", ...)
   define_subagent(name="junior-developer", ...)
   define_subagent(name="log-analyzer", ...)
   define_subagent(name="mammouth-expert", ...)
   define_subagent(name="meta-feedback", ...)
   define_subagent(name="opencode-expert", ...)
   define_subagent(name="orchestrator", ...)
   define_subagent(name="performance-optimizer", ...)
   define_subagent(name="principal-developer", ...)
   define_subagent(name="prompt-engineer", ...)
   define_subagent(name="refactoring-specialist", ...)
   define_subagent(name="release", ...)
   define_subagent(name="requirements", ...)
   define_subagent(name="senior-developer", ...)
   define_subagent(name="technical-writer", ...)
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
