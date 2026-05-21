# Konzept: Orchestrator-First Architecture — Provider-agnostische Delegations-Pyramide

> Status: **Konzept-Phase** | Branch: `feat/orchestrator-first-architecture`
> Datum: 2026-05-21

---

## Executive Summary

Dieses Konzept beschreibt eine **provider-agnostische Neuausrichtung des Delegations-Systems** von agent-meta: Statt dass die Main Session selbst Arbeit verrichtet (Dateien lesen, Code analysieren, Multi-Step-Workflows ausführen), wird sie zum **Thin Router** — alle Aufgaben fließen durch den Orchestrator, der sie zerlegt, parallelisiert und an spezialisierte Worker-Agents delegiert.

**Kerninnovationen:**
1. **Task Decomposition Protocol** — Der Orchestrator zerlegt "Mach X, Y, Z" in unabhängige Sub-Tasks und dispatched sie parallel an mehrere Agenten des gleichen Typs.
2. **Provider-Agnostic Parallel Model** — Gleiche Entscheidungslogik für Claude, Opencode, Gemini, Continue. Nur die Syntax variiert (via `PARALLEL_PATTERN`).
3. **Main Session Thinning** — Reduktion von ~500 auf ~40 Zeilen Managed Block. Alle Rules bleiben als separate Dateien, nur die Routing-Logik und Agenten-Tabelle verbleiben inline.

**Ziel:** `max-parallel-agents` (heute ungenutzt) wird zum aktiven Steuerungsparameter. Der Orchestrator wird von einem linearen Delegierer zu einem echten **Task-Orchestrator** mit FANOUT, BARRIER und PARALLEL_GROUP.

---

## 1. Problem-Analyse: Ist-Zustand

### 1.1 Architektur-Übersicht

```
┌────────────────────────────────────────────────────┐
│                  MAIN SESSION                      │
│  CLAUDE.md / AGENTS.md (~500 Zeilen)               │
│  ┌──────────────────────────────────────────────┐  │
│  │ Agent-Tabelle                                │  │
│  │ ALLE Rules inline (branch-guard, commit,     │  │
│  │   dod, issue-lifecycle, language,            │  │
│  │   lifecycle-tasks, session-conclusion,       │  │
│  │   use-orchestrator, architecture,            │  │
│  │   conventions, sync-interface, speech)       │  │
│  │ Projekt-spezifischer Kontext                 │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  Verhalten: Liest Dateien, führt Bash aus,         │
│  analysiert Code, macht Recherche SELBST            │
└────────────────────┬───────────────────────────────┘
                     │ (manchmal)
                     ▼
┌────────────────────────────────────────────────────┐
│               ORCHESTRATOR v2.10.0                  │
│  Intent-Routing │ Model-Tier-Routing │ Workflows   │
│  Delegiert linear: A→B→C→D                         │
│  Parallel NUR: validator ∥ documenter              │
└────────────────────┬───────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────┐
│  developer │ tester │ validator │ git │ ideation   │
│  (sequentiell, nie parallel gleicher Typ)          │
└────────────────────────────────────────────────────┘
```

### 1.2 Konkrete Defizite

| Defizit | Auswirkung |
|---------|-----------|
| **Main Session macht alles selbst** | ~500 Zeilen Kontext. Analysiert, recherchiert, führt Multi-Step-Commands aus — obwohl die `use-orchestrator`-Rule existiert |
| **use-orchestrator im silent-Preset deaktiviert** | `config/rules-presets.yaml` setzt `use-orchestrator: alwaysApply: false` unter `silent`. Die Rule wird nicht geladen |
| **Ausnahmen-Liste zu breit** | `git`, `documenter`, `agent-meta-manager`, `feedback` gehen direkt — oft auch bei mehrschrittigen Operationen |
| **Kein Task-Splitting** | "Fix Bug A, B, C" wird als ein Task an einen developer gegeben — statt in 3 parallele Tasks zerlegt |
| **max-parallel-agents ungenutzt** | Auf 4 konfiguriert, aber nur 1× genutzt (validator∥documenter). 75% der Parallel-Kapazität liegt brach |
| **PARALLEL_PATTERN vage** | Opencode: "Starte unabhängige Agenten nacheinander — sie laufen implizit parallel." Keine Syntax, keine Limits, keine Beispiele |
| **Regel-Duplizierung** | Alle Rules existieren als separate `.md`-Dateien UND sind 1:1 in den Managed Block von AGENTS.md/CLAUDE.md eingebettet (~380 Zeilen Duplikation) |

### 1.3 Provider-Parallel-Fähigkeiten (Ist)

| Provider | Parallel? | Mechanismus | Dokumentiert als |
|----------|-----------|-------------|-----------------|
| Claude | Ja | `run_in_background=True` | Syntax-Beispiel für validator∥documenter |
| Opencode | Ja | Mehrere `task()`-Calls in einer Nachricht | "läuft implizit parallel" |
| Gemini | Ja | Automatisch bei mehreren Tool-Calls | "automatisch parallelisiert" |
| Continue | Nein | Kein natives Parallel | "sequentiell ausführen" |

---

## 2. Target Architecture: Orchestrator-First

### 2.1 Delegations-Pyramide

```
┌──────────────────────────────────────────────┐
│        MAIN SESSION (Thin Router)            │
│  ~40 Zeilen Managed Block                    │
│                                              │
│  Agent-Tabelle + "Für ALLES → Orchestrator"  │
│  Ausnahmen NUR: atomare Git-Ops, Sync,       │
│  Meta-Fragen, Feedback-Issues                │
│                                              │
│  Verhalten: KEIN Datei-Lesen, KEIN Bash,     │
│  KEINE Analyse — nur Routing                 │
└──────────────────┬───────────────────────────┘
                   │ (immer)
                   ▼
┌──────────────────────────────────────────────┐
│          ORCHESTRATOR v3.0.0                 │
│                                              │
│  ┌────────────┐ ┌──────────┐ ┌────────────┐ │
│  │ Intent     │ │ Task     │ │ Parallel   │ │
│  │ Routing    │ │ Decomp.  │ │ Dispatcher │ │
│  └────────────┘ └──────────┘ └────────────┘ │
│  ┌──────────────────────────────────────┐   │
│  │ Result Aggregation & Reporting       │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  Provider-agnostische Entscheidungslogik     │
│  Provider-spezifische Syntax via             │
│  {{PARALLEL_PATTERN}}                        │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│           WORKER AGENTS                      │
│                                              │
│  developer₁ │ developer₂ │ developer₃        │
│  tester₁    │ tester₂    │ validator₁        │
│  (parallel: bis zu {{MAX_PARALLEL_AGENTS}}   │
│   Instanzen des gleichen Typs gleichzeitig)  │
└──────────────────────────────────────────────┘
```

### 2.2 Design-Prinzipien

1. **Main Session = Thin Router.** Sie hat kein Domänenwissen, liest keine Dateien, führt keine Befehle aus. Sie routet nur.
2. **Orchestrator = Universal Dispatcher.** Jede Entwicklungsaufgabe geht durch ihn. Er zerlegt, parallelisiert, aggregiert.
3. **Worker Agents = Stateless.** Bekommen vollständigen Kontext im Prompt. Keine Abhängigkeiten untereinander.
4. **Provider-Agnostik.** Die Entscheidungslogik (ob parallel, wie zerlegen) ist identisch für alle Provider. Nur die konkrete Syntax wird via `PARALLEL_PATTERN` injiziert.
5. **Graceful Degradation.** Provider ohne Parallel-Fähigkeit (Continue) fallen auf sequentiellen Modus zurück.

---

## 3. Task Decomposition Protocol

### 3.1 Zerlegungs-Algorithmus

```
Eingabe: User-Task T

Schritt 1 — Intent-Klassifikation:
  type ∈ {feat, fix, refactor, test, docs, analyze, design, release, ...}
  agent = lookup(type) aus Intent-Routing-Tabelle

Schritt 2 — Multi-Task-Erkennung:
  Enthält T mehrere unabhängige Teilaufgaben [t₁, t₂, ..., tₙ]?
    ├─ Nein → Schritt 5 (Einzel-Dispatch)
    └─ Ja → Schritt 3

Schritt 3 — Parallelitäts-Prüfung:
  Für jedes Paar (tᵢ, tⱼ):
    Sind tᵢ und tⱼ unabhängig? (kein Shared State, keine Output-Abhängigkeit)
      ├─ Ja → parallel_kandidaten.add(tᵢ, tⱼ)
      └─ Nein → sequentiell (tᵢ vor tⱼ)

Schritt 4 — Agent-Typ-Gruppierung:
  Gruppiere nach Ziel-Agent:
    gleicher Typ + alle unabhängig → FANOUT(N, AgentType, tasks)
    verschiedene Typen + unabhängig → PARALLEL_GROUP([(A₁,t₁), (A₂,t₂), ...])
    abhängige Tasks → sequentielle Pipeline

Schritt 5 — Dispatch:
  FANOUT/PARALLEL_GROUP/sequentiell ausführen
  BARRIER: auf alle parallelen Ergebnisse warten

Schritt 6 — Aggregation:
  Ergebnisse sammeln, Konsistenz prüfen, Zusammenfassung an User
```

### 3.2 Entscheidungsmatrix

| User sagt | Zerlegung | Dispatch-Muster | Parallel? |
|-----------|-----------|-----------------|-----------|
| "Fix Bug A" | 1 Task | Einzel-Dispatch | Nein |
| "Fix Bug A, B, C" | 3 unabhängige Tasks | FANOUT(3, developer) | Ja |
| "Fix Bugs A–H" (8 Stück) | 8 Tasks | FANOUT(4, developer) → BARRIER → FANOUT(4, developer) | Ja (Batch à 4) |
| "Feature X mit Tests" | Pipeline | req → test → dev → test → val | Nein (Abhängigkeiten) |
| "Fix A, B + schreib Tests für C" | 3 Tasks, 2 Typen | PARALLEL_GROUP: 2×dev ∥ 1×tester | Ja (gemischt) |
| "Feature Y komplett" | Lifecycle | → feature-Agent (orchestriert intern) | feature-intern |
| "Analysiere Modul A und B" | 2 Tasks | FANOUT(2, ideation) | Ja |
| "Schreib Docs für A, B, C" | 3 Tasks | FANOUT(3, documenter) | Ja |

### 3.3 Unabhängigkeits-Regeln

Zwei Sub-Tasks tᵢ und tⱼ sind **unabhängig** wenn:

1. **Disjunkte Dateimengen:** tᵢ und tⱼ bearbeiten verschiedene Dateien (oder verschiedene, nicht-überlappende Abschnitte derselben Datei)
2. **Keine Kausalkette:** Das Ergebnis von tᵢ wird nicht als Input für tⱼ benötigt
3. **Kein Shared State:** Beide Tasks verändern keinen gemeinsamen globalen Zustand (Konfiguration, Datenbank, Singleton)

**Faustregel:** Wenn der Orchestrator unsicher ist → sequentiell. Falsche Parallelisierung ist schlimmer als fehlende.

---

## 4. Provider-Agnostic Parallel Model

### 4.1 Abstrakte Operationen

Der Orchestrator arbeitet mit **drei abstrakten Operationen**, unabhängig vom Provider:

```
FANOUT(N, AgentType, [task₁, ..., taskₙ])
  Startet N Instanzen desselben Agent-Typs parallel.
  Jede Instanz erhält genau einen Task.
  Beispiel: FANOUT(3, developer, ["Fix A", "Fix B", "Fix C"])

PARALLEL_GROUP([(AgentType₁, task₁), (AgentType₂, task₂), ...])
  Startet mehrere verschiedene Agent-Typen parallel.
  Beispiel: PARALLEL_GROUP([(developer, "Fix A"), (tester, "Test B")])

BARRIER()
  Wartet bis ALLE gestarteten parallelen Agenten beendet sind.
  Sammelt alle Ergebnisse ein.
  Gibt ein Ergebnis-Array zurück: [result₁, result₂, ..., resultₙ]
```

Diese Operationen sind **provider-agnostisch** — sie beschreiben WAS getan wird, nicht WIE. Das WIE liefert `{{PARALLEL_PATTERN}}`.

### 4.2 Provider-spezifische Implementierungen

Die konkrete Syntax wird via `{{PARALLEL_PATTERN}}`-Variable zur Sync-Zeit in den Orchestrator injiziert. Der Orchestrator selbst enthält nur die abstrakten Operationen.

#### Claude

```
## Parallel-Dispatch (Claude)

FANOUT: N Agenten starten — N-1 im Hintergrund (run_in_background=True), 1 im Vordergrund.
PARALLEL_GROUP: Verschiedene Agent-Typen — alle bis auf einen im Hintergrund.
BARRIER: Warten bis Vordergrund-Agent fertig → alle Hintergrund-Ergebnisse sind dann da.

Beispiel — FANOUT(3, developer, ["Fix A", "Fix B", "Fix C"]):
  Agent(subagent_type="developer", prompt="Fix Bug A: ...", run_in_background=True)
  Agent(subagent_type="developer", prompt="Fix Bug B: ...", run_in_background=True)
  Agent(subagent_type="developer", prompt="Fix Bug C: ...")  # Vordergrund

Limit: Kein hartes Limit. max-parallel-agents steuert die Anzahl.
```

#### Opencode

```
## Parallel-Dispatch (Opencode)

FANOUT: Alle N task()-Calls in EINER Antwort-Nachricht. Kein separater Background-Marker.
PARALLEL_GROUP: Mehrere task()-Calls mit verschiedenen subagent_type in einer Antwort.
BARRIER: Automatisch — die Antwort kommt erst wenn alle Tasks fertig sind.

Beispiel — FANOUT(3, developer, ["Fix A", "Fix B", "Fix C"]):
  task(subagent_type="developer", description="Fix Bug A", prompt="...")
  task(subagent_type="developer", description="Fix Bug B", prompt="...")
  task(subagent_type="developer", description="Fix Bug C", prompt="...")
  // Alle drei Calls in derselben Antwort → parallele Ausführung

Ergebnisse: task_results als Array [result_A, result_B, result_C].
```

#### Gemini

```
## Parallel-Dispatch (Gemini)

FANOUT: Alle N Agent-Calls in einer Antwort. Gemini parallelisiert automatisch.
PARALLEL_GROUP: Funktioniert identisch zu FANOUT — Gemini erkennt verschiedene Typen.
BARRIER: Automatisch — Antwort kommt nach allen Ergebnissen.

Beispiel — FANOUT(3, developer, ["Fix A", "Fix B", "Fix C"]):
  (Drei separate Agent-Tool-Calls in einer Antwort)
  Gemini führt sie automatisch parallel aus.

Limit: Kein hartes Limit. max-parallel-agents steuert die Anzahl.
```

#### Continue

```
## Parallel-Dispatch (Continue)

Continue unterstützt KEINE native parallele Subagent-Ausführung.

FANOUT/PARALLEL_GROUP: Nicht verfügbar → sequentieller Fallback.
Informiere den User: "Continue kann nicht parallelisieren. Führe Tasks sequentiell aus."

Falle auf sequentiellen Dispatch zurück:
  1. task₁ an Agent delegieren → warten
  2. task₂ an Agent delegieren → warten
  3. ...
```

### 4.3 Provider-Capability Detection

Der Orchestrator muss nicht wissen welcher Provider ihn ausführt. `{{PARALLEL_PATTERN}}` enthält die vollständige Anleitung — wenn dort "nicht unterstützt" steht, verwendet er den sequentiellen Fallback.

```
Implizite Capability-Erkennung:
  Enthält {{PARALLEL_PATTERN}} das Wort "Hintergrund" oder "background"?
    → Claude-Modus (run_in_background)
  Enthält {{PARALLEL_PATTERN}} "task(" ohne "background"?
    → Opencode-Modus (mehrere task()-Calls)
  Enthält {{PARALLEL_PATTERN}} "automatisch parallel"?
    → Gemini-Modus (automatisch)
  Enthält {{PARALLEL_PATTERN}} "nicht unterstützt" oder "sequentiell"?
    → Continue-Modus (sequentieller Fallback)
```

---

## 5. Main Session Thinning

### 5.1 Vorher/Nachher — Managed Block

**Vorher** (heute, ~380 Zeilen Rules + Agent-Tabelle im Managed Block):

```markdown
<!-- agent-meta:managed-begin -->

Generiert von agent-meta v0.46.2 — 2026-05-21
DoD-Preset: rapid-prototyping | REQ-Traceability: false | Tests: false | ...

> Einstiegspunkt: Starte mit dem orchestrator-Agenten für alle Entwicklungsaufgaben.

| Agent | Zuständigkeit |
|-------|--------------|
| ...   | ...          |

## Regeln

# Branch-Guard — Feature-Branch Pflicht
[...]

# Commit-Konventionen (Conventional Commits)
[...]

# Definition of Done (DoD)
[...]

# GitHub Issue Lifecycle
[...]

# Sprachregeln
[...]

# Lifecycle-Tasks
[...]

# Session-Abschluss
[...]

# Orchestrator — Pflichtnutzung
[...]

# agent-meta — Schichten-Architektur
[...]

# agent-meta — Entwicklungskonventionen
[...]

# agent-meta — sync.py Interface
[...]

# Kommunikationsstil: Submissive
[...]

<!-- agent-meta:managed-end -->
```

**Nachher** (Phase 2, ~40 Zeilen):

```markdown
<!-- agent-meta:managed-begin -->

Generiert von agent-meta v0.47.0 — 2026-05-21
DoD-Preset: rapid-prototyping | REQ-Traceability: false | Tests: false | ...

> **Routing-Regel:** JEDE Aufgabe → `orchestrator`.
> Ausnahmen: atomare Git-Operationen → `git`, Sync/Upgrade → `agent-meta-manager`,
> Feedback-Issue → `feedback`, Session-Erkenntnisse → `documenter`.
> **Der Hauptchat ist ein Router, kein Worker.**

| Agent | Zuständigkeit | Tier |
|-------|--------------|------|
| `orchestrator` | Universal-Router — zerlegt, parallelisiert, delegiert | entry |
| `developer` | Feature-Implementierung, Bugfixes | balanced+ |
| `feature` | Vollständiger Feature-Lifecycle | balanced |
| `git` | Commits, Branches, Tags, Push/Pull | fast |
| ... | ... | ... |

<!-- agent-meta:managed-end -->
```

Die Rules selbst bleiben als separate Dateien in `.claude/rules/`, `.opencode/rules/` etc. bestehen — sie werden vom Provider-Runtime geladen, nicht mehr in den Managed Block eingebettet.

### 5.2 Selective Rule Embedding (Phase 2)

Nicht alle Rules müssen aus dem Managed Block entfernt werden. Einige sind fundamental und sollten immer sichtbar sein:

| Rule | Embed? | Begründung |
|------|--------|-----------|
| `use-orchestrator` | **Ja** | Kritisch für die Routing-Entscheidung |
| `branch-guard` | **Ja** | Sicherheitsrelevant, gilt für Main Session direkt |
| `commit-conventions` | **Nein** | Nur für git-Agent relevant |
| `dod-criteria` | **Nein** | Nur für validator/developer relevant |
| `issue-lifecycle` | **Nein** | Nur für git/feedback relevant |
| `language` | **Ja** | Betrifft Main Session direkt |
| `lifecycle-tasks` | **Nein** | Situativ |
| `session-conclusion` | **Ja** | Betrifft Main Session direkt |
| `architecture` | **Nein** | Agent-meta-spezifisch, nicht für Zielprojekte |
| `conventions` | **Nein** | Agent-meta-spezifisch |
| `sync-interface` | **Nein** | Nur für agent-meta-manager |
| `speech-mode` | **Ja** | Betrifft Main Session direkt |

**Implementierung:** Ein `embed: false` Feld im Rule-Frontmatter oder in `rules-presets.yaml` steuert die Einbettung. `embed: true` (Default) → wird in Managed Block eingebettet. `embed: false` → bleibt nur als separate Rule-Datei.

```yaml
# config/rules-presets.yaml (erweitert)
presets:
  minimal:
    commit-conventions:
      embed: false
    dod-criteria:
      embed: false
    issue-lifecycle:
      embed: false
```

---

## 6. use-orchestrator Rule — Vollständiger neuer Text

```markdown
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

> **Faustregel:** Wenn du >1 Tool-Call brauchst → Orchestrator.
> Wenn du unsicher bist → Orchestrator.
> Wenn du Code lesen/analysieren/schreiben willst → Orchestrator.

## Verboten im Hauptchat

- Code lesen, schreiben, editieren, analysieren
- Architektur verstehen, Konzepte entwerfen, Design-Docs schreiben
- Recherche zu Implementierungsfragen, Impact-Analysen
- Multi-Step-Workflows (egal wie einfach)
- Shell-Befehle die nicht reinem Routing dienen
- Direkte Delegation an: developer, tester, validator, requirements,
  ideation, release, feature, log-analyzer, security-auditor, docker

> **Der Hauptchat ist ein Thin Router.** Er hat keine Domänenkompetenz.
> Seine einzige Aufgabe: User-Intent erkennen und korrekt routen.

## Hauptchat ohne Orchestrator (Fallback)

Wenn der Orchestrator nicht verfügbar ist:
- Branch-Guard manuell: `git branch --show-current`
- Auf `main`/`master` → Branch anlegen
- Keine parallelen Tasks möglich
- Sequentieller Workflow selbst koordinieren
```

---

## 7. Orchestrator v3.0.0 — Neue Template-Struktur

### 7.1 Version-Bump

```yaml
---
name: template-orchestrator
version: "3.0.0"       # Major: Neue Task-Decomposition + Parallel-Engine
description: "Provider-agnostischer Task-Orchestrator: zerlegt, parallelisiert, delegiert."
hint: "Einstiegspunkt für ALLE Entwicklungsaufgaben — zerlegt komplexe Tasks und dispatched parallel"
tools:
  - Agent
  - TodoWrite
---
```

### 7.2 Neue Sections

```
## Planning-Phase (Pflicht vor komplexen Aufgaben)     [erweitert]
  + Ankündigung von FANOUT/PARALLEL_GROUP im Plan
  + Anzahl paralleler Agenten im Plan zeigen

## Intent-Routing (Pflicht vor jeder Antwort)           [erweitert]
  + Neue Intents: Multi-Fix, Multi-Analyse, Batch-Test, Batch-Docs
  + Routing-Tabelle um "Parallel-Eligible"-Spalte ergänzt

## Task Decomposition Protocol (NEU)
  + Zerlegungs-Algorithmus (6 Schritte)
  + Entscheidungsmatrix (FANOUT, PARALLEL_GROUP, Pipeline, Lifecycle)
  + Unabhängigkeits-Regeln (3 Kriterien)
  + Batching für N > MAX_PARALLEL_AGENTS

## Parallel Execution Engine (NEU)
  + Abstrakte Operationen: FANOUT, PARALLEL_GROUP, BARRIER
  + Provider-spezifische Syntax via {{PARALLEL_PATTERN}}
  + Capability Detection (automatisch aus PARALLEL_PATTERN)

## Result Aggregation (NEU)
  + Ergebnisse sammeln und auf Konsistenz prüfen
  + Bei Konflikten: User informieren, nicht automatisch mergen
  + Zusammenfassung: Was wurde parallel erledigt, was ist offen?

## Dynamic Model Tier Routing                         [unverändert]

## Human-in-the-Loop Gates                             [erweitert]
  + FANOUT > 2 Agenten: User-Bestätigung einholen
  + "Ich starte jetzt N parallele [Agent]-Instanzen für: [Liste]. Fortfahren?"

## Delegations-Protokoll                               [erweitert]
  + Parallel-Dispatch: "Ich starte 3× developer parallel für: A, B, C"
  + Ergebnis: "[2/3] developer melden Erfolg. [1/3] braucht Klärung..."

## Analysis- und Design-Guard                          [unverändert]

## Agenten                                             [erweitert]
  + Parallel-fähige Agenten markieren (∥)

## Workflows                                           [erweitert]
  + Parallele Workflow-Varianten (F: Fix-Batch, T: Test-Batch)

## Don'ts                                               [erweitert]
  + KEINE falsche Parallelisierung — im Zweifel sequentiell
  + KEIN automatisches Mergen paralleler Ergebnisse ohne User-Prüfung
```

### 7.3 Workflow-Erweiterungen

```
A  Neues Feature:    0.git  1.?req  2.?test  3.dev  4.?test  5∥6.val+?doc  7.git
B  Bugfix:           0.git  1.?req  2.?test  3.dev  4.?test  5∥6.val+?doc  7.git
...
Q  Multi-Fix:        FANOUT(N, developer, [fix₁..fixₙ]) → BARRIER → git
R  Multi-Test:       FANOUT(N, tester, [test₁..testₙ]) → BARRIER
S  Multi-Analyse:    FANOUT(N, ideation, [analyze₁..analyzeₙ]) → BARRIER → report
T  Multi-Docs:       FANOUT(N, documenter, [doc₁..docₙ]) → BARRIER
```

---

## 8. File Change Impact Matrix

### Phase 1 (Core — Orchestrator v3.0.0 + Rules)

| Datei | Änderung | Typ | Risiko |
|-------|---------|-----|--------|
| `rules/1-generic/use-orchestrator.md` | Komplett neu schreiben | Text | Niedrig |
| `config/rules-presets.yaml` | `use-orchestrator` aus `silent` entfernen | Config | Niedrig |
| `agents/1-generic/orchestrator.md` | v2.10.0 → v3.0.0: neue Sections, erweiterte Workflows | Major | Mittel |
| `scripts/lib/agents.py` | `_PROVIDER_PARALLEL_PATTERNS` für alle 4 Provider präzisieren | Code | Niedrig |

### Phase 2 (Thinning — Selective Embedding)

| Datei | Änderung | Typ | Risiko |
|-------|---------|-----|--------|
| `templates/claude-md-managed.md` | Auf ~20 Zeilen eindampfen | Text | Mittel |
| `config/rules-presets.yaml` | `embed: false` pro Rule konfigurierbar | Config | Mittel |
| `scripts/lib/context.py` | `_collect_embedded_rules_md()` um `embed: false`-Filter erweitern | Code | Hoch |

### Nicht betroffen (garantiert stabil)

- `config/role-defaults.yaml` — keine neuen Rollen, bestehende unverändert
- `.meta-config/project.yaml` — keine neuen Pflichtfelder
- `sync.py` Hauptlogik — nur Text-Inhalte ändern sich
- `agents/2-platform/` — keine Plattform-Overrides nötig
- Worker-Agent-Templates (`developer.md`, `tester.md`, etc.) — unverändert

---

## 9. Rückwärtskompatibilität

### Garantiert

1. **Bestehende Projekte laufen weiter.** Templates außer Orchestrator sind unverändert.
2. **sync.py kein Breaking Change.** Nur Textänderungen in generierten Dateien. Keine neuen Pflichtfelder in `project.yaml`.
3. **Bestehende Overrides respektiert.** Wenn ein Projekt `3-project/orchestrator.md` hat (Full-Replacement), wird der neue v3.0.0-Orchestrator nicht verwendet.
4. **Extensions weiter wirksam.** `3-project/orchestrator-ext.md` wird weiterhin additiv geladen.

### Migration

```
Projekt migrieren:
  1. agent-meta Submodul aktualisieren (git pull im Submodul)
  2. sync.py ausführen → Orchestrator v3.0.0 wird generiert
  3. Ggf. eigenes max-parallel-agents in project.yaml setzen
  4. Fertig. Keine manuellen Änderungen nötig.
```

### silent-Preset-Nutzer

Projekte mit `rules-preset: silent` erhalten `use-orchestrator` nach dem Update plötzlich als `alwaysApply: true`. Das ist gewünscht — "silent" bedeutet weniger Kontext, nicht "ohne Orchestrator".

---

## 10. Risiken & Mitigation

| Risiko | W'keit | Schwere | Mitigation |
|--------|--------|---------|-----------|
| **Token-Explosion durch N parallele Agenten** | Mittel | Mittel | `MAX_PARALLEL_AGENTS` begrenzt. Batching bei N > Limit. Jeder Sub-Agent bekommt fokussierten Prompt. |
| **Falsche Parallelisierung → Merge-Konflikte** | Mittel | Hoch | Strikte Unabhängigkeits-Prüfung. "Im Zweifel sequentiell". User-Prüfung vor FANOUT > 2. |
| **Continue-Nutzer ohne Parallel-Feature** | Hoch | Niedrig | Klarer Fallback im PARALLEL_PATTERN. User-Info. Kein Funktionsverlust — nur langsamer. |
| **Orchestrator wird Bottleneck bei trivialen Tasks** | Mittel | Niedrig | Ausnahmen-Liste für atomare Ops bleibt. "Fix typo in one line" geht direkt an developer. |
| **Orchestrator v3.0.0 sprengt Kontext-Limit** | Niedrig | Mittel | Neue Sections sind kompakt (<150 Zeilen gesamt). Bestehende Logik unverändert. |
| **User lehnt parallele Ausführung ab** | Mittel | Niedrig | Human-in-the-Loop-Gate: User bestätigt FANOUT > 2. User kann jederzeit `max-parallel-agents: 1` setzen. |

---

## 11. Phasen-Plan

```
Phase 1 — Core (jetzt)
├── use-orchestrator Rule neu schreiben
├── rules-presets.yaml: use-orchestrator aus silent entfernen
├── agents/1-generic/orchestrator.md → v3.0.0
│   ├── Task Decomposition Protocol
│   ├── Parallel Execution Engine (abstrakt)
│   └── Result Aggregation
├── scripts/lib/agents.py: PARALLEL_PATTERNs präzisieren
├── sync.py --dry-run → verifizieren
└── Commit + PR

Phase 2 — Thinning (nächster Schritt)
├── Selective Rule Embedding (embed: false)
├── templates/claude-md-managed.md eindampfen
├── scripts/lib/context.py: embed-Filter
└── sync.py --dry-run über alle Testprojekte

Phase 3 — Advanced (optional, später)
├── Result-Caching (gleicher Task + gleicher Input → Cache)
├── Dynamisches Batching (Lernkurve: welche Tasks sind wirklich parallelisierbar?)
└── Agent-Pooling (wiederverwendbare Agent-Sessions)
```

---

## 12. Glossar

| Begriff | Definition |
|---------|-----------|
| **FANOUT** | N Instanzen des gleichen Agent-Typs parallel starten |
| **PARALLEL_GROUP** | Mehrere verschiedene Agent-Typen parallel starten |
| **BARRIER** | Synchronisationspunkt: auf alle parallelen Ergebnisse warten |
| **Thin Router** | Main Session die nur routet, keine Arbeit verrichtet |
| **Task Decomposition** | Zerlegung eines komplexen User-Tasks in unabhängige Sub-Tasks |
| **Selective Embedding** | Nur bestimmte Rules in den Managed Block einbetten, andere als separate Dateien |
| **Graceful Degradation** | Automatischer Fallback auf sequentielle Ausführung bei Providern ohne Parallel-Fähigkeit |
