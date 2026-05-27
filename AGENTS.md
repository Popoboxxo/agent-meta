# agent-meta

agent-meta ist ein Git-Repository das als Submodul in Projekte eingebunden wird. Es stellt standardisierte Claude-Agenten-Templates bereit (1-generic, 2-platform, 0-external) und generiert via sync.py projektfertige Agenten-Dateien in .claude/agents/. Das Repo verwendet sich selbst — die hier generierten Agenten koordinieren die Weiterentwicklung von agent-meta.

<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on every sync. -->
<!-- Manual changes here will be overwritten. -->

Generiert von agent-meta v0.55.0 — `2026-05-28`
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

## Regeln

# Branch-Guard — Feature-Branch Pflicht

**Gilt für alle code-ändernden Aufgaben.**

## Pflicht vor dem ersten Edit

```bash
git branch --show-current
```

Auf `main`/`master` → Branch anlegen: `feat/<thema>` | `fix/<thema>` | `refactor/<thema>`

## Branch PFLICHT wenn

- Mehr als eine Datei geändert
- Inhaltliche Änderung an Templates, Rules, Scripts
- GitHub Issue bearbeitet

**Faustregel: >1 Datei anfassen → Branch.**

## Direkt auf main erlaubt (Ausnahmen)

Nur: Version-Bump (`VERSION`, `CHANGELOG.md`, `README.md`) | einzelner Tippfehler (1 Datei, 1 Zeile, User-Bestätigung) | Post-Merge-Pflege nach Review.

**NIE für:** Templates, Rules, Scripts — egal wie klein. Nie für Issue-Arbeit.

## Warum

Direkte Commits auf main können kaum rückgängig gemacht werden und blockieren andere Entwicklung.

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

{{#if DOD_REQ_TRACEABILITY}}
## REQ-Traceability

- [ ] REQ-ID existiert in `docs/REQUIREMENTS.md`
- [ ] Commit-Format: `<type>(REQ-xxx): <beschreibung>`
{{/if}}

{{#if DOD_TESTS_REQUIRED}}
## Tests

- [ ] Test vorhanden und grün
{{/if}}

{{#if DOD_CODEBASE_OVERVIEW}}
## Dokumentation

- [ ] `CODEBASE_OVERVIEW.md` aktualisiert
{{/if}}

{{#if DOD_SECURITY_AUDIT}}
## Security

- [ ] Security-Audit vor Release durchgeführt
{{/if}}

**Keine finale Antwort und keine Commit-Empfehlung** ohne Prüfung aller aktiven Kriterien.

---

# GitHub Issue Lifecycle

Wenn deine Arbeit mit einem GitHub Issue verknüpft ist, schließe es nach Abschluss ab.

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
    - agent: validator
      task: "Quick DoD check for merged changes."
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

> **Warum:** 1-generic/ propagiert in ALLE Projekte. Ein Provider-Name hier würde in Claude-Projekten "Gemini" stehen und in Gemini-Projekten "Claude" — beides falsch und verwirrend.

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

# Orchestrator — Universal Router

**JEDE Entwicklungsaufgabe geht über den Orchestrator.**

## Immer über Orchestrator

Feature | Bugfix | Refactoring | Analyse | Design | Konzept |
Recherche | Implementierung | Tests | Audit | Release | Docker |
Anforderungen | Validierung | Dokumentation | Log-Analyse | Ideation

Der Orchestrator zerlegt komplexe Aufgaben in Sub-Tasks, parallelisiert
unabhängige Arbeiten und delegiert an spezialisierte Worker-Agenten.

## Ausnahmen — direkter Dispatch

NUR für atomare Einzeloperationen (ein Schritt, ein Agent, keine Abhängigkeiten):

| Operation | Direkt an | Bedingung |
|-----------|-----------|-----------|
| Commit, Push, Branch, Tag, PR | `git` | Einzelner Git-Befehl |
| Sync, Upgrade, Meta-Konfiguration | `agent-meta-manager` | Reine agent-meta-Operation |
| Bug/Feature/Verbesserung melden | `feedback` | Issue-Erstellung |
| Session-Erkenntnisse speichern | `documenter` | Nur bei Session-Ende |

## Mention-Interception — `@orchestrator` ist der einzige direkte Dispatch

**WICHTIG:** `@orchestrator` ist der **EINZIGE** Mention den User direkt im Chat verwenden dürfen.

Alle anderen `@<agent>`-Mentions (z.B. `@meta-feedback`, `@git`, `@developer`, `@documenter`, `@feedback`) werden **nicht** vom Agent-Invocation-System interceptet. Sie erscheinen als reiner Text und lösen keine automatische Delegation aus.

### Regel für alle Provider

- User sagt "Erstelle ein Meta-Feedback Issue" → Hauptchat delegiert intern an `feedback` (kein `@meta-feedback` im Output)
- User sagt "Commit das" → Hauptchat delegiert intern an `git` (kein `@git` im Output)
- **Agenten antworten NIEMALS mit `@<agent>` im Chat** — sie delegieren über das native Tool-Call-Interface

### Warum

Einige Provider-Umgebungen (insbesondere Gemini/Antigravity) intercepten nur den `@orchestrator`-Mention. Andere `@<agent>`-Mentions werden als plain text gerendert und lösen keine Aktion aus. Durch die ausschließliche Verwendung von `@orchestrator` als einzigen sichtbaren Mention wird diese Inkonsistenz eliminiert.

### Konsequenz für die "Ausnahmen — direkter Dispatch"

Die in der Tabelle genannten direkten Dispatch-Ausnahmen (`git`, `feedback`, `agent-meta-manager`, `documenter`) gelten **nur für die interne Delegationslogik** des Hauptchats/Orchestrators — nicht als User-facing Mentions. User verwenden **ausschließlich** `@orchestrator` oder natürliche Sprache.

> **Faustregel:** Wenn du >1 Tool-Call brauchst → Orchestrator.
> Wenn du unsicher bist → Orchestrator.
> Wenn du Code lesen/analysieren/schreiben willst → Orchestrator.

## Die Smarte Kommunikationsoberfläche (Hauptchat)

Der Hauptchat ist die intelligente Schnittstelle zum Nutzer. Er darf und soll:
- Dateien lesen und den Kontext analysieren
- Befehle ausführen, um den Ist-Zustand zu begreifen (z.B. Git-Status, Tests)
- Architekturen und Konzepte im Dialog mit dem Nutzer schärfen

**Aber:** Sobald es an die eigentliche *Ausführung* von Entwicklungsaufgaben, tiefgreifenden Prüfungen oder Multi-Step-Workflows geht, tritt die automatische Delegationspflicht in Kraft. Direkte Delegation an Worker-Agenten (developer, tester etc.) ist im Hauptchat weiterhin verboten — all dies geht über den Orchestrator.

## User-Override: Bewusste Hauptchat-Ausführung

Der User hat jederzeit das Recht, die Orchestrator-Pflicht zu umgehen und den Auftrag direkt im Hauptchat ausführen zu lassen.

### Trigger-Sätze (User sagt explizit)

- "Nicht delegieren"
- "Mach das hier"
- "Im Hauptchat bitte"
- "Kein Orchestrator"
- "Ohne Orchestrator"
- "Ich will hier arbeiten"
- "Delegiere nicht"

### Verhalten bei User-Override

```
1. Trigger-Satz erkannt
2. Bestätigung: "Ich arbeite den Auftrag im Hauptchat selbst ab."
3. Main-Chat führt die Aufgabe aus:
   - Liest Dateien selbst
   - Schreibt Code selbst
   - Führt Befehle aus
   - Führt Multi-Step-Workflows aus
   → Kurzfristig verhält sich der Hauptchat wie ein klassischer Agent
4. Nach Abschluss:
   → "Soll ich für zukünftige ähnliche Anfragen ebenfalls im Hauptchat
      arbeiten, oder wieder über den Orchestrator routen?"
   → Optionen:
      - "Immer Hauptchat" → setze unknown-fallback=main-chat (project.yaml)
      - "Immer Orchestrator" → strict=true bleibt
      - "Frag jedes Mal" → unknown-fallback=ask-user
      - "Nur dieses Mal" → Einzel-Override, kein Persistenz
```

### Regeln für den Override

- Der Override gilt NUR für die aktuelle Anfrage (oder persistiert wenn User das wünscht)
- Der Override hebt die "Verboten im Hauptchat"-Regel auf
- Alle anderen Rules (branch-guard, commit-conventions, language, etc.) bleiben aktiv
- Meta-Feedback wird trotzdem erstellt: "User wollte Hauptchat-Modus für: [anonymisierter Intent]"

## Konfiguration: Orchestrator-Schalter

Das Verhalten wird zentral in `.meta-config/project.yaml` gesteuert:

```yaml
orchestrator:
  enabled: true        # true = Orchestrator aktiv, false = Main-Chat-Modus
  strict: true         # true = Immer delegieren, false = Fallback erlaubt
  unknown-fallback:
    meta-feedback: true   # Send anonymized feedback to agent-meta (default: true)
    main-chat: true       # Allow main chat to handle task (default: true)
    ask-user: false       # Ask user for preference (default: false)
```

| Modus | enabled | strict | meta-feedback | main-chat | ask-user | Verhalten bei unbekanntem Intent |
|-------|---------|--------|---------------|-----------|----------|-----------------------------------|
| **Strict** | true | true | true | false | false | Meta-Feedback, NICHT selbst ausführen |
| **Relaxed** | true | false | true | true | false | Main-Chat arbeitet selbst + Meta-Feedback |
| **Ask-First** | true | — | — | — | true | User gefragt: "Hier oder Feedback?" |
| **Disabled** | false | — | — | — | — | Kein Orchestrator, Main-Chat macht alles selbst |
| **Custom** | true | false | true | true | true | User gefragt → dann entscheiden |

**Fallback-Priorität:**
1. `ask-user=true` → Immer User fragen (höchste Priorität)
2. `strict=true` + `meta-feedback=true` → Feedback + Nachfrage
3. `strict=false` + `main-chat=true` → Main-Chat selbst + ggf. Feedback
4. Kein Fallback aktiv → Klärungsfrage

**Empfehlung:** Default ist `strict` für Produktionsprojekte, `relaxed` für Prototypen, `disabled` für kleine Einzelnutzer-Projekte.

## Automatische Delegationspflicht (Auto-Handoff)

Wenn der Hauptchat eine Anfrage erhält, die nicht unter "Ausnahmen — direkter Dispatch" fällt, und kein expliziter Trigger-Satz für einen User-Override vorliegt, greift der automatische Handoff an den Orchestrator.

Der Hauptchat weigert sich **niemals** mit einem Text-Block. Statt den Nutzer aufzufordern, den Orchestrator manuell aufzurufen, übernimmt der Hauptchat dies selbstständig im Hintergrund.

### Ablauf des Auto-Handoffs

1. **Kontext-Phase:** Der Hauptchat liest Dateien, führt Recherche-Tools aus und spricht mit dem Nutzer, um den genauen Umfang der Aufgabe zu verstehen.
2. **Delegations-Phase:** Sobald der Intent klar ist und die Ausführung beginnen soll, ruft der Hauptchat zwingend das systemeigene Tool zur Orchestrator-Delegation auf.
3. **Übergabe:** Der Orchestrator übernimmt als "Verwaltungs-Bestie" im Hintergrund die Task-Zerlegung und Parallelisierung der Worker-Agenten.

### Technische Durchsetzung auf LLM-Ebene

Jeder Provider-Agent liest diese Datei als System-Instruktion ein. Sobald ein auszuführender Entwicklungs-, Architektur- oder Prüf-Auftrag ansteht:

1. **Kein Redirection-Text:** Gib NIEMALS eine Textnachricht aus, die den Nutzer bittet, den Orchestrator manuell aufzurufen.
2. **Native Tool-Calls priorisieren (PRIMAER):** Verwende IMMER zuerst den nativen Subagent-Dispatch-Mechanismus deiner Umgebung. Das ist das Tool-Call-Interface das Subagenten als strukturierte Aufrufe invoziert (kein reiner Text). Dies ist die bevorzugte und zuverlaessigste Methode — sie funktioniert in allen Umgebungen mit nativer Subagent-Unterstuetzung.
3. **Text-basierter Fallback (SEKUNDAER):** Nur wenn die Umgebung KEIN natives Subagent-Tool-Call-Interface bereitstellt, verwende den textbasierten Trigger `@orchestrator <Aufgabe>` im Chat als Fallback. Dieser Mechanismus wird von einigen Frontends geparst, ist aber nicht zuverlaessig in Umgebungen mit nativen Tool-Calls.

**Entscheidungsregel:** Native Umgebung mit Subagent-Tool? → Native Tool-Calls verwenden. Nur reines Text-Chat-Frontend? → `@orchestrator` Fallback.

## Hauptchat ohne Orchestrator (Fallback)

Wenn der Orchestrator nicht verfügbar ist:
- Branch-Guard manuell: `git branch --show-current`
- Auf `main`/`master` → Branch anlegen
- Keine parallelen Tasks möglich
- Sequentieller Workflow selbst koordinieren

---

## Anti-Recursion Guard — Worker dürfen nicht zurückdelegieren

**Diese Regel gilt für ALLE Worker-Agenten.**

Worker-Agenten (developer, tester, documenter, code-reviewer, git, etc.) sind **Ausführungs-Endstellen**. Sie dürfen Aufgaben die in ihrem Scope liegen NIEMALS zurück an den Orchestrator delegieren.

### Verboten für Worker

- `@orchestrator` im Chat-Output verwenden
- Tool-Calls die den Orchestrator aufrufen
- "Delegiere an orchestrator" als Handlung
- Aufgaben zurückgeben die sie selbst lösen können

### Erlaubt für Worker

- Im Text auf andere Worker-Rollen verweisen (z.B. "Tests fehlen → tester")
- Den User informieren wenn etwas außerhalb des Scope liegt
- Bei echten Blockern den User um Klärung bitten

### Warum

Rekursive Delegationen (Hauptchat → Orchestrator → Worker → Orchestrator → ...) erzeugen:
- Endlosschleifen
- Redundante Token-Kosten
- Verwirrung über Zuständigkeiten
- Verlust des Task-Kontexts

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

Composition wird zur Build-Zeit aufgelöst — das generierte `.claude/agents/<rolle>.md`
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

# agent-meta — Entwicklungskonventionen

## Harte Invarianten (niemals verletzen)

**1. `.claude/agents/` ist generierter Output — nie manuell bearbeiten.**
Alle Änderungen gehören in die Quell-Templates unter `agents/` oder in `.meta-config/project.yaml`.
Manuelle Edits werden beim nächsten `sync.py`-Lauf überschrieben.

**2. Agent-Versionen im Frontmatter erhöhen bei jeder inhaltlichen Änderung.**

| Änderungstyp | Bump |
|---|---|
| Umbenannte Variable, geändertes Verhalten, neue Pflichtsektion | **Major** (`X.0.0`) |
| Neue optionale Sektion, erweiterter Scope | **Minor** (`x.Y.0`) |
| Textverbesserung, Klarstellung, Config-Pfad-Fix | **Patch** (`x.y.Z`) |

Plattform-Agenten (`2-platform/`) führen zusätzlich `based-on: "1-generic/<rolle>.md@<version>"`.
Dieses Feld aktuell halten wenn die Generic-Basis geändert wird.

**3. Platzhalter immer `{{GROSS_MIT_UNTERSTRICH}}`.**
Kleinbuchstaben oder gemischte Schreibweise funktioniert nicht — der Regex in `substitute()`
erfasst nur `[A-Z0-9_]+`.

## Wenn du eine neue Agenten-Rolle hinzufügst

Pflichtschritte — manuell zu pflegen (die anderen Artefakte werden automatisch generiert):

### Manuell (Pflicht)

1. `agents/1-generic/<rolle>.md` anlegen (mit Frontmatter: `name`, `version`, `description`, `hint`, `tools`)
2. Eintrag in `config/role-defaults.yaml` (model, memory, permissionMode, tier)
3. `howto/setup/instantiate-project.md` ergänzen (Agent-Tabelle und Hints)

### Automatisch via `sync.py` — NIE manuell editieren

Folgende Artefakte werden beim nächsten `sync.py`-Lauf automatisch generiert/aktualisiert:

| Artefakt | Quelle | Hinweis |
|----------|--------|---------|
| `CLAUDE.md` (managed block) | `agents/` + `config/role-defaults.yaml` | Agent-Tabelle, Hints, Rules-Referenzen |
| `AGENTS.md` (managed block) | `agents/` + `config/role-defaults.yaml` | Gleiche Quelle wie CLAUDE.md |
| `GEMINI.md` | `agents/` + `config/role-defaults.yaml` | Plattform-spezifische Generierung |
| `.continue/config.yaml` | `agents/` + `config/role-defaults.yaml` | Continue-Plattform |
| `.*/agents/*.md` | `agents/1-generic/`, `2-platform/`, `3-project/` | Generierte Agenten-Dateien |
| `docs/agent-graph.html` | `agents/` + Delegation-Map | Visualisierung |
| `docs/agent-mindmap.md` | `agents/` + Delegation-Map | Mindmap |
| `.claude/rules/conventions.md` | `rules/2-platform/agent-meta-conventions.md` | Rules-Propagation |
| `.gemini/rules/conventions.md` | `rules/2-platform/agent-meta-conventions.md` | Rules-Propagation |
| `.continue/rules/conventions.md` | `rules/2-platform/agent-meta-conventions.md` | Rules-Propagation |

**Merksatz:** Nur `1-generic/<rolle>.md`, `config/role-defaults.yaml` und `howto/setup/instantiate-project.md` sind manuell zu pflegen. Alles andere → `sync.py` ausführen.

## Wenn du einen neuen Platzhalter einführst

1. In `scripts/lib/config.py` → `build_variables()` oder `_inject_dod()` eintragen
2. In `CLAUDE.md` Variablen-Tabelle dokumentieren
3. In `howto/project.yaml.example` als Kommentar-Zeile ergänzen (optional aber empfohlen)

## Änderungs-Checkliste (before commit)

| Was geändert | Was prüfen |
|---|---|
| `1-generic/<rolle>.md` | version: erhöhen + betroffene Projekte syncen |
| `2-platform/<platform>-<rolle>.md` | version: und based-on: aktuell? |
| `agents/0-external/_skill-wrapper.md` | Alle aktivierten Skills neu syncen |
| `config/skills-registry.yaml` | Projekte neu syncen |
| `config/role-defaults.yaml` (neue Rolle) | Tabellen in CLAUDE.md + howto-Dateien |
| `hint:` Feld in Agent-Template | Projekte syncen (AGENT_HINTS wird neu generiert) |
| Rules oder Hooks in `rules/` / `hooks/` | Projekte syncen (werden überschrieben) |

---

# agent-meta — sync.py Interface

`sync.py` ist der einzige Weg Agenten zu generieren. Nie direkt in `.claude/agents/` schreiben.

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

## Agents

Agent files are in `.opencode/agents/`. Invoke them by name in opencode.

## Project Setup

- **Build:** `python scripts/sync.py`
- **Test:** `(kein automatisiertes Test-System — manuelle Verifikation via --dry-run)`
- **Platform:** Python CLI (sync.py)
- **Runtime:** Python 3.x
