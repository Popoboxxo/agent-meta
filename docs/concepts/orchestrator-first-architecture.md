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

### 3.4 Orchestrator-Aktivierungs-Schalter

**Neue Konfiguration in `.meta-config/project.yaml`:**

```yaml
# Orchestrator-Steuerung
orchestrator:
  enabled: true        # true = Orchestrator aktiv (Default), false = Main-Chat-Modus
  strict: true         # true = Immer delegieren (Default), false = Fallback erlaubt
  unknown-fallback: meta-feedback  # meta-feedback | main-chat | ask-user
```

| Feld | Default | Werte | Bedeutung |
|------|---------|-------|-----------|
| `enabled` | `true` | `true` / `false` | Ist der Orchestrator überhaupt aktiv? |
| `strict` | `true` | `true` / `false` | Bei unbekanntem Intent: Meta-Feedback oder Main-Chat? |
| `unknown-fallback` | `meta-feedback` | `meta-feedback` / `main-chat` / `ask-user` | Was passiert bei nicht verortbarem Task? |

### 3.5 Unknown Task Handling & Meta-Feedback Loop

**Problem:** Der Orchestrator kann einen User-Intent nicht klassifizieren — er taucht in keiner Intent-Routing-Tabelle auf und passt zu keinem bekannten Muster.

**Lösung: Vier Modi, steuerbar via Konfig + User-Override**

```
User-Input empfangen
│
├─ User sagt explizit: "Nicht delegieren" / "Mach hier" / "Kein Orchestrator"
│   → User-Override: Main-Chat arbeitet selbst (ignoriert alle Regeln)
│   → Nach Abschluss: Frage ob das für zukünftige ähnliche Anfragen beibehalten werden soll
│
├─ orchestrator.enabled: false
│   → Main-Chat-Modus: Kein Orchestrator, alles wird im Hauptchat erledigt
│   → Wie heute, aber bewusst konfiguriert
│
├─ orchestrator.enabled: true  AND  Intent bekannt
│   → Normaler Orchestrator-Flow (Intent-Routing → Delegation)
│
└─ orchestrator.enabled: true  AND  Intent UNBEKANNT
    ├─ unknown-fallback: meta-feedback
    │   → Anonymisiertes Meta-Feedback + User-Frage nach alternativer Formulierung
    │   → Verboten: Selbst ausführen
    │
    ├─ unknown-fallback: main-chat
    │   → Main-Chat arbeitet selbst (wie heute)
    │   → Gleichzeitig: Meta-Feedback erstellen (für Verbesserung)
    │
    └─ unknown-fallback: ask-user
        → "Soll ich das hier im Hauptchat erledigen oder ein Feedback senden?"
        → User entscheidet → Main-Chat oder Meta-Feedback
```

#### Modus A: strict=true, unknown-fallback=meta-feedback (Default)

```
Schritt 1 — Analyseversuch (max. 1 Klärungsfrage):
  "Ich bin mir unsicher: Meint Ihr [Option A] oder [Option B]?"
  → Wenn User klärt → normaler Intent-Routing

Schritt 2 — Wenn nicht geklärt:
  NICHT selbst ausführen.
  NICHT "Sorry, ich verstehe das nicht" abbrechen.

Schritt 3 — Anonymisiertes Meta-Feedback erstellen:
  Projektname → "[PROJECT]", Pfade → "[PATH]", Secrets → "[REDACTED]"
  Kurze Beschreibung: "Unbekannter Intent: [Kategorie-Guess]."

Schritt 4 — Delegation an meta-feedback:
  "Erstelle ein GitHub Issue in agent-meta: 'Orchestrator: Unknown Intent'"

Schritt 5 — User informieren:
  "Ich konnte den Auftrag nicht zuordnen. Ich habe ein Verbesserungsvorschlag
   an das agent-meta Team gesendet. Möchtet Ihr den Auftrag anders formulieren?"
```

#### Modus B: strict=false, unknown-fallback=main-chat

```
Schritt 1 — Analyseversuch (max. 1 Klärungsfrage)
Schritt 2 — Wenn nicht geklärt:
  MAIN-CHAT ARBEITET SELBST (wie heute ohne Orchestrator)
  → Dateien lesen, Code schreiben, Befehle ausführen
  → Parallel: Anonymisiertes Meta-Feedback erstellen (kein Blocker)
Schritt 3 — User informieren:
  "Ich habe den Auftrag im Hauptchat erledigt. Gleichzeitig habe ich ein
   Verbesserungsvorschlag gesendet, damit solche Anfragen zukünftig besser
   geroutet werden können."
```

#### Modus C: enabled=false (Main-Chat-Modus)

```
Der Orchestrator ist komplett deaktiviert. Der Hauptchat verhält sich wie ein
klassischer Agent ohne Routing:
- Liest Dateien selbst
- Analysiert Code selbst
- Schreibt und editiert selbst
- Führt Befehle aus

Verhalten: Identisch zu agent-meta vor Orchestrator-First.
Use-Case: Kleine Projekte, Prototypen, Nutzer die den Orchestrator nicht wollen.
```

#### Modus D: User-Override (bewusste Hauptchat-Ausführung)

**Trigger-Sätze:**
- "Nicht delegieren"
- "Mach das hier"
- "Im Hauptchat bitte"
- "Kein Orchestrator"
- "Ohne Orchestrator"
- "Ich will hier arbeiten"

**Verhalten:**
```
1. User sagt einen Trigger-Satz
2. Bestätigung: "Ich arbeite den Auftrag im Hauptchat selbst ab."
3. Main-Chat führt die Aufgabe aus (wie Modus C)
4. Nach Abschluss:
   → "Soll ich für zukünftige ähnliche Anfragen ebenfalls im Hauptchat
      arbeiten, oder wieder über den Orchestrator routen?"
   → Optionen: "Immer Hauptchat" | "Immer Orchestrator" | "Frag jedes Mal"
   → Wenn User "Immer Hauptchat" wählt → setze unknown-fallback=main-chat
```

**Regeln für Anonymisierung (nur für Meta-Feedback):**

| Was | Beispiel | Anonymisiert zu |
|-----|----------|-----------------|
| Projektname | "agent-meta" | `[PROJECT]` |
| Dateipfade | "scripts/sync.py" | `[PATH]/sync.py` oder `[FILE]` |
| URLs | "github.com/Popoboxxo/..." | `[URL]` |
| API-Keys, Tokens | "sk-abc123" | `[REDACTED]` |
| Domain-Begriffe | "MBSE", "StrictDoc", "Sharkord" | bleiben (relevant für Klassifikation) |
| Anfragetyp | "Füge eine neue Sensor-Klasse hinzu" | bleiben (das ist der eigentliche Intent) |

**Warum anonymisiert?**
- Datenschutz: Projekt-interne Details bleiben im Projekt
- agent-meta erhält nur den Intent-Typ, nicht den konkreten Inhalt
- Das Feedback-Loop ist rein strukturell: "Wir brauchen einen neuen Intent-Kategorie X"

**Integration in Orchestrator-Template:**

Neue Section im Orchestrator (nach Intent-Routing):
```
## Unknown Intent Protocol

Wenn der Intent in keiner bekannten Kategorie landet:
1. Prüfe ob orchestrator.enabled = false → Main-Chat-Modus, selbst ausführen
2. Prüfe ob User-Override aktiv → Main-Chat, selbst ausführen
3. Versuche mit max. 1 Klärungsfrage
4. Wenn nicht geklärt:
   - strict=true → Anonymisiere Inhalte → Delegiere an meta-feedback
   - strict=false → Main-Chat arbeitet selbst + Meta-Feedback im Hintergrund
   - unknown-fallback=ask-user → Frage User nach Präferenz
5. Frage User nach alternativer Formulierung (bei meta-feedback)

Verboten (nur in strict=true): Selbst ausführen, selbst raten, abbrechen.
```

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

## 5. Projektspezifische Agenten & Platform-Agenten — 100% Kompatibilität

### 5.1 Die Override-Hierarchie

```
1-generic/orchestrator.md          ← Template mit Task Decomposition
      │
      ▼
2-platform/<plattform>-orchestrator.md  ← Full-Replacement oder Composition
      │                                    (z.B. sharkord-spezifische Workflows)
      ▼
3-project/orchestrator.md               ← Full-Override (komplett ersetzt)
      │
      ▼
3-project/am-orchestrator-ext.md        ← Extension (additiv, nie von sync.py berührt)
```

### 5.2 Projektspezifische Agenten (3-project/)

**Problem:** Ein Projekt definiert eigene Agenten (z.B. `openscad-developer`, `home-organization-specialist`). Diese tauchten nicht in der Orchestrator-Intent-Routing-Tabelle auf.

**Lösung:** Der Orchestrator muss projektspezifische Agenten erkennen können. Das geschieht über die `roles`-Liste aus `.meta-config/project.yaml`.

**Mechanismus:**

```yaml
# .meta-config/project.yaml
roles:
  - orchestrator
  - developer
  - openscad-developer      # ← Projekt-spezifisch
  - home-organization-specialist  # ← Projekt-spezifisch
```

`sync.py` generiert aus der `roles`-Liste eine dynamische Intent-Routing-Erweiterung, die dem Orchestrator injiziert wird:

```
{{#if PROJECT_SPECIFIC_AGENTS}}
## Projektspezifische Agenten

| Agent | Zuständigkeit | Routing-Trigger |
|-------|--------------|-----------------|
| openscad-developer | Parametrische 3D-Modelle | "OpenSCAD", "3D-Druck", "STL" |
| home-organization-specialist | Home-Assistant Automation | "Home", "Haus", "Automation" |
{{/if}}
```

**Varibale `PROJECT_SPECIFIC_AGENTS`:**
- Wird von `sync.py` aus `roles` minus `role-defaults.yaml` bekannten Rollen generiert
- Enthält Name, Beschreibung, Routing-Keywords
- Wird in den Orchestrator injiziert (nach der Standard-Intent-Routing-Tabelle)

**Parallelisierung von projektspezifischen Agenten:**
- Identisch zu generischen Agenten: FANOUT, PARALLEL_GROUP, BARRIER funktionieren gleich
- `MAX_PARALLEL_AGENTS` gilt auch für projektspezifische Agenten
- Batching-Logik: 5× openscad-developer gleichzeitig → zwei Batches (4 + 1)

### 5.3 Platform-Agenten (2-platform/)

**Plattform-Overrides können:**

1. **Full-Replacement:** `2-platform/sharkord-orchestrator.md` ersetzt den generischen Orchestrator komplett → Die Plattform-Version enthält die Task Decomposition und Parallel Engine selbst
2. **Composition:** `2-platform/sharkord-orchestrator.md` mit `extends: "1-generic/orchestrator.md"` + `patches:` → Die Parallel Engine wird aus 1-generic geerbt und um plattformspezifische Intents erweitert

**Kompatibilitätstabelle:**

| Override-Typ | Task Decomposition | Parallel Engine | Meta-Feedback Loop | Kompatibel? |
|--------------|--------------------|-----------------|--------------------|-------------|
| Full-Replacement (kein extends:) | Muss selbst implementieren | Muss selbst implementieren | Muss selbst implementieren | **Ja** — Plattform ist frei |
| Composition (extends: + patches:) | Wird von 1-generic geerbt | Wird von 1-generic geerbt | Wird von 1-generic geerbt | **Ja** — automatisch |
| Kein Override | 1-generic verwendet | 1-generic verwendet | 1-generic verwendet | **Ja** — Standard |

**Plattform-spezifische Intents:**

Eine Plattform (z.B. Sharkord) kann ihre eigenen Intents hinzufügen:

```yaml
# 2-platform/sharkord-orchestrator.md (Composition)
extends: "1-generic/orchestrator.md"
patches:
  - op: append-after
    anchor: "## Intent-Routing"
    content: |
      ### Sharkord-spezifische Intents
      
      | User-Intent | Ziel-Agent | Tier |
      |-------------|-----------|------|
      | "Erstelle eine Dashboard-Kachel" | `dashboard-designer` | balanced |
      | "Füge MQTT-Sensor hinzu" | `sensor-developer` | fast |
      | "Update Sharkord-Config" | `sharkord-manager` | fast |
      
      > Diese Intents werden parallelisiert wie alle anderen (FANOUT bei Multi-Tasks).
```

### 5.4 External Skills (0-external/)

**Skill-Agenten** (via `config/skills-registry.yaml`) werden als eigenständige Rollen behandelt:

```yaml
# config/skills-registry.yaml
skills:
  home-organization:
    repo: "https://github.com/..."
    agent: "home-organization-specialist"
    approved: true
```

- Skill-Agenten tauchen automatisch in der generierten Agenten-Tabelle auf
- Der Orchestrator kann sie über die dynamische `PROJECT_SPECIFIC_AGENTS`-Variable erkennen
- Parallelisierung: `FANOUT(2, home-organization-specialist)` funktioniert identisch zu generischen Agenten

### 5.5 Zusammenfassung Kompatibilität

| Agent-Typ | Task Decomp. | Parallel Engine | Meta-Feedback | Routing |
|-----------|-------------|-----------------|----------------|---------|
| 1-generic (generisch) | ✓ v3.0.0 | ✓ abstrakt + PARALLEL_PATTERN | ✓ automatisch | ✓ feste Tabelle |
| 2-platform (Full-Replace) | ✓ plattform-eigen | ✓ plattform-eigen | ✓ plattform-eigen | ✓ plattform-eigen |
| 2-platform (Composition) | ✓ geerbt | ✓ geerbt | ✓ geerbt | ✓ erweitert |
| 3-project (Override) | ✓ projekt-eigen | ✓ projekt-eigen | ✓ projekt-eigen | ✓ projekt-eigen |
| 3-project (Extension) | ✓ geerbt + additiv | ✓ geerbt | ✓ geerbt | ✓ erweitert |
| 0-external (Skill) | ✓ dynamisch | ✓ dynamisch | ✓ dynamisch | ✓ dynamisch |

**100% Kompatibilität ist garantiert**, weil:**
1. Die Override-Hierarchie unverändert bleibt (1-generic → 2-platform → 3-project → 0-external)
2. Full-Replacements sind frei, ihre eigene Logik zu implementieren
3. Compositions erben automatisch alle neuen Features
4. Neue Variablen (`PROJECT_SPECIFIC_AGENTS`) werden injiziert — bestehende Templates ignorieren sie einfach

---

## 6. Main Session Thinning

### 6.1 Vorher/Nachher — Managed Block

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

### 6.2 Selective Rule Embedding (Phase 2)

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

## 7. use-orchestrator Rule — Vollständiger neuer Text

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
  enabled: true               # true = Orchestrator aktiv, false = Main-Chat-Modus
  strict: true                # true = Immer delegieren, false = Fallback erlaubt
  unknown-fallback: ask-user  # meta-feedback | main-chat | ask-user
```

| Modus | enabled | strict | unknown-fallback | Verhalten bei unbekanntem Intent |
|-------|---------|--------|------------------|-----------------------------------|
| **Strict** | true | true | meta-feedback | Meta-Feedback, NICHT selbst ausführen |
| **Relaxed** | true | false | main-chat | Main-Chat arbeitet selbst + Meta-Feedback |
| **Ask** | true | true/false | ask-user | User gefragt: "Hier oder Feedback?" |
| **Disabled** | false | — | — | Kein Orchestrator, Main-Chat macht alles selbst |

**Empfehlung:** Default ist `strict` für Produktionsprojekte, `relaxed` für Prototypen, `disabled` für kleine Einzelnutzer-Projekte.

## Hauptchat ohne Orchestrator (Fallback)

Wenn der Orchestrator nicht verfügbar ist:
- Branch-Guard manuell: `git branch --show-current`
- Auf `main`/`master` → Branch anlegen
- Keine parallelen Tasks möglich
- Sequentieller Workflow selbst koordinieren
```

---

## 8. Orchestrator v3.0.0 — Neue Template-Struktur

### 8.1 Version-Bump

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

### 8.2 Neue Sections

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

### 8.3 Workflow-Erweiterungen

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

## 9. Orchestration Testing & Dry-Run Framework

### 9.1 Ziel

Sicherstellen, dass die Orchestrator-First-Architektur auf jedem Provider korrekt funktioniert — bevor echte Aufgaben delegiert werden. Ein Dry-Run simuliert die Orchestrierung ohne echte Agent-Ausführung und validiert:

1. **Intent-Routing:** Wird jeder Intent korrekt zugeordnet?
2. **Task Decomposition:** Werden Multi-Tasks korrekt zerlegt?
3. **Parallel Dispatch:** Werden FANOUT/PARALLEL_GROUP korrekt generiert?
4. **Provider-Kompatibilität:** Funktioniert die Syntax für den aktiven Provider?
5. **BARRIER-Synchronisation:** Werden Ergebnisse korrekt aggregiert?
6. **Viz-Log-Integration:** Werden Events korrekt ins Viz-Log geschrieben?

### 9.2 Test-Package-Struktur

```
tests/orchestration/
├── __init__.py
├── conftest.py                 # Pytest-Fixtures für alle Provider
├── test_intent_routing.py      # Intent-Klassifikation
├── test_task_decomposition.py  # Task-Zerlegung
├── test_parallel_dispatch.py   # FANOUT/PARALLEL_GROUP/BARRIER
├── test_provider_syntax.py     # Provider-spezifische Syntax-Validierung
├── test_viz_integration.py     # Viz-Log-Events
├── test_unknown_intent.py      # Unknown Intent Protocol + Meta-Feedback
├── test_user_override.py       # User-Override-Mechanismus
├── fixtures/
│   ├── intents.yaml            # 50+ Test-Intents mit erwarteten Ziel-Agenten
│   ├── multi_tasks.yaml        # 30+ Multi-Task-Szenarien mit erwarteter Zerlegung
│   └── providers/
│       ├── claude.json         # Erwartete Syntax für Claude
│       ├── opencode.json       # Erwartete Syntax für Opencode
│       ├── gemini.json         # Erwartete Syntax für Gemini
│       └── continue.json       # Erwartete Syntax für Continue (sequentiel)
└── dry_run/
    ├── __init__.py
    ├── engine.py               # Dry-Run-Engine (simuliert Orchestrator)
    ├── validators.py           # Validierungs-Logik für Zerlegung/Dispatch
    └── reporters.py            # Report-Generierung (Markdown, JSON)
```

### 9.3 Dry-Run-Engine

Die Engine simuliert den Orchestrator ohne echte Agent-Ausführung:

```python
# tests/orchestration/dry_run/engine.py

class OrchestratorDryRun:
    """Simuliert Orchestrator-Entscheidungen ohne echte Delegation."""

    def __init__(self, provider: str, config: dict):
        self.provider = provider
        self.config = config
        self.events = []  # Für Viz-Log

    def classify_intent(self, user_input: str) -> str:
        """Klassifiziert Intent und gibt Ziel-Agent zurück."""
        # Nutzt Intent-Routing-Tabelle aus orchestrator.md
        # Return: agent_name oder "UNKNOWN"

    def decompose_task(self, user_input: str) -> list[SubTask]:
        """Zerlegt Multi-Tasks in Sub-Tasks."""
        # Prüft Unabhängigkeit, Gruppiert nach Agent-Typ
        # Return: Liste von SubTask(name, agent_type, dependencies)

    def generate_dispatch_plan(self, subtasks: list[SubTask]) -> DispatchPlan:
        """Erzeugt Dispatch-Plan mit FANOUT/PARALLEL_GROUP/sequentiell."""
        # Berücksichtigt MAX_PARALLEL_AGENTS, Provider-Fähigkeiten
        # Return: DispatchPlan mit Operationen und Reihenfolge

    def validate_syntax(self, plan: DispatchPlan) -> SyntaxReport:
        """Validiert generierte Syntax gegen Provider-Spezifikation."""
        # Vergleicht mit tests/fixtures/providers/{provider}.json

    def run(self, user_input: str) -> DryRunReport:
        """Führt kompletten Dry-Run durch."""
        intent = self.classify_intent(user_input)
        self.log_event("intent_classified", {"input": user_input, "intent": intent})

        if intent == "UNKNOWN":
            return self.handle_unknown_intent(user_input)

        subtasks = self.decompose_task(user_input)
        self.log_event("task_decomposed", {"subtasks": len(subtasks)})

        plan = self.generate_dispatch_plan(subtasks)
        self.log_event("dispatch_plan_generated", {"plan": plan.to_dict()})

        syntax_report = self.validate_syntax(plan)
        self.log_event("syntax_validated", {"valid": syntax_report.valid})

        return DryRunReport(
            intent=intent,
            subtasks=subtasks,
            plan=plan,
            syntax=syntax_report,
            provider=self.provider,
            events=self.events,
        )
```

### 9.4 Test-Szenarien

#### A. Intent-Routing-Tests (test_intent_routing.py)

```yaml
# tests/fixtures/intents.yaml
- input: "Füge Login hinzu"
  expected_agent: developer
  expected_tier: balanced
  provider: all

- input: "Commit die Änderungen"
  expected_agent: git
  expected_tier: fast
  provider: all

- input: "Analysiere die Architektur"
  expected_agent: ideation
  expected_tier: balanced
  provider: all

- input: "Fix Bug A in parser und Bug B in renderer"
  expected_agent: developer  # Nach Decomposition
  expected_tier: balanced
  expected_parallel: true
  expected_fanout: 2
  provider: all

- input: "Mache etwas mit dem Ding"
  expected_agent: UNKNOWN
  expected_fallback: meta-feedback  # strict=true
  provider: all

- input: "Mach das hier, nicht delegieren"
  expected_agent: USER_OVERRIDE
  expected_behavior: main_chat_self_execute
  provider: all

- input: "Erstelle Dashboard-Kachel für Temperatur"
  expected_agent: dashboard-designer  # Projekt-spezifisch
  provider: all
  project: sharkord
```

#### B. Task-Decomposition-Tests (test_task_decomposition.py)

```yaml
# tests/fixtures/multi_tasks.yaml
- description: "3 unabhängige Bugfixes"
  input: "Fix parser crash, renderer leak, validator error"
  expected:
    decomposition: FANOUT
    agent_type: developer
    count: 3
    independent: true
    batches: 1  # 3 <= MAX_PARALLEL(4)

- description: "5 unabhängige Bugfixes (Batching)"
  input: "Fix A, B, C, D, E"
  expected:
    decomposition: FANOUT
    agent_type: developer
    count: 5
    independent: true
    batches: 2  # Batch 1: A,B,C,D | Batch 2: E

- description: "Abhängige Tasks (Pipeline)"
  input: "Feature X implementieren mit Tests"
  expected:
    decomposition: PIPELINE
    sequence:
      - agent: requirements
      - agent: tester
      - agent: developer
      - agent: tester
    parallel: false

- description: "Gemischte parallele Tasks"
  input: "Fix Bug A und schreib Tests für Modul B"
  expected:
    decomposition: PARALLEL_GROUP
    agents:
      - type: developer
        count: 1
      - type: tester
        count: 1
    parallel: true

- description: "Lifecycle (Feature komplett)"
  input: "Feature Y komplett umsetzen"
  expected:
    decomposition: LIFECYCLE
    agent: feature
    internal_steps: 8
    parallel: false  # feature-Agent orchestriert intern
```

#### C. Parallel-Dispatch-Tests (test_parallel_dispatch.py)

Für jeden Provider wird geprüft:

```python
@pytest.mark.parametrize("provider", ["Claude", "Opencode", "Gemini", "Continue"])
def test_fanout_syntax(provider):
    """Validiert FANOUT-Syntax für jeden Provider."""
    plan = generate_plan(provider, "Fix A, B, C")
    syntax = validate_syntax(plan, provider)

    if provider in ["Claude", "Opencode", "Gemini"]:
        assert syntax.valid
        assert syntax.parallel_supported
        assert syntax.operation == "FANOUT"
        assert syntax.agent_count == 3
    else:  # Continue
        assert not syntax.parallel_supported
        assert syntax.fallback == "sequential"
        assert syntax.agent_count == 3
```

#### D. Provider-Syntax-Validierung (test_provider_syntax.py)

```json
// tests/fixtures/providers/opencode.json
{
  "provider": "Opencode",
  "parallel_support": true,
  "syntax": {
    "fanout": "Multiple task() calls in single message",
    "barrier": "Automatic — response waits for all tasks",
    "parallel_group": "Multiple task() with different subagent_type in single message",
    "max_agents": "Limited by MAX_PARALLEL_AGENTS config"
  },
  "example": "task(subagent_type='developer', ...)\ntask(subagent_type='developer', ...)\ntask(subagent_type='developer', ...)",
  "expected_output": "task_results as array [result_A, result_B, result_C]"
}
```

### 9.5 Viz-Log-Integration

Jeder Dry-Run schreibt Events ins Viz-Log:

```python
# tests/orchestration/test_viz_integration.py

def test_dry_run_logs_events():
    """Prüft ob alle Dry-Run-Schritte im Viz-Log landen."""
    engine = OrchestratorDryRun(provider="Opencode", config={"max-parallel-agents": 4})
    report = engine.run("Fix A, B, C")

    events = report.events
    assert events[0]["type"] == "intent_classified"
    assert events[1]["type"] == "task_decomposed"
    assert events[2]["type"] == "dispatch_plan_generated"
    assert events[3]["type"] == "syntax_validated"
    assert events[4]["type"] == "dry_run_complete"

    # Viz-Log-Format prüfen
    for event in events:
        assert "timestamp" in event
        assert "provider" in event
        assert "session_id" in event
```

**Viz-Log-Event-Struktur:**

```json
{
  "timestamp": "2026-05-21T19:40:17Z",
  "session_id": "dry-run-abc123",
  "provider": "Opencode",
  "type": "task_decomposed",
  "data": {
    "input": "Fix A, B, C",
    "subtasks": 3,
    "decomposition": "FANOUT",
    "agent_type": "developer",
    "parallel": true
  }
}
```

### 9.6 Trigger-Mechanismen

#### A. Manuell: Command-basiert

```bash
# Generierter Command für jeden Provider (via sync.py)
# .claude/commands/test-orchestration.md
# .opencode/commands/test-orchestration.md
# .gemini/commands/test-orchestration.toml
# .continue/commands/test-orchestration.md
```

**Command-Text (Beispiel Opencode):**

```markdown
# test-orchestration

Führt einen Orchestration-Dry-Run durch und validiert:
- Intent-Routing
- Task-Decomposition
- Parallel-Dispatch
- Provider-Syntax
- Viz-Log-Integration

## Parameter

--provider    Aktiver Provider (auto-detected)
--scenario    Test-Szenario: all | routing | decomposition | parallel | unknown | override
--verbose     Detaillierte Ausgabe
--viz         Viz-Log-Events anzeigen

## Beispiele

/test-orchestration                    # Alle Tests für aktiven Provider
/test-orchestration --scenario=parallel # Nur Parallel-Dispatch-Tests
/test-orchestration --verbose --viz     # Alle Tests mit Viz-Log
```

#### B. Automatisiert: Pre-Commit / Pre-Push

```bash
# .claude/hooks/orchestration-test.sh (optional)
# Wird vor jedem Commit ausgeführt

#!/bin/bash
# Prüft ob Orchestrator-Templates syntaktisch korrekt sind
python tests/orchestration/dry_run/engine.py --provider=$(detect_provider) --quick

# Exit 0 = OK, Exit 1 = Fehler (blockt Commit)
```

#### C. Automatisiert: Post-Sync

```python
# In sync.py integriert (optional, via Flag --test-orchestration)

# Nach jedem sync.py-Lauf:
# "Möchtest du einen Orchestration-Dry-Run durchführen?"
# → Ja → Führt Tests für alle aktiven Provider durch
```

#### D. Automatisiert: CI/CD

```yaml
# .github/workflows/orchestration-test.yml (optional)
name: Orchestration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        provider: [Claude, Opencode, Gemini, Continue]
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Run Orchestration Tests
        run: |
          pip install -r tests/requirements.txt
          python -m pytest tests/orchestration/ -v --provider=${{ matrix.provider }}
```

### 9.7 Test-Report

Der Dry-Run generiert einen strukturierten Report:

```markdown
# Orchestration Dry-Run Report

**Provider:** Opencode
**Datum:** 2026-05-21 19:40:17
**Config:** max-parallel-agents=4, orchestrator.enabled=true, strict=true

---

## Zusammenfassung

| Metrik | Wert |
|--------|------|
| Tests ausgeführt | 47 |
| Bestanden | 45 |
| Warnungen | 2 |
| Fehler | 0 |

## Intent-Routing

| Input | Erwartet | Tatsächlich | Status |
|-------|----------|-------------|--------|
| "Füge Login hinzu" | developer | developer | ✅ |
| "Commit die Änderungen" | git | git | ✅ |
| "Mache etwas mit dem Ding" | UNKNOWN | UNKNOWN | ✅ |
| "Mach das hier" | USER_OVERRIDE | USER_OVERRIDE | ✅ |

## Task-Decomposition

| Szenario | Zerlegung | Agent | Anzahl | Parallel | Status |
|----------|-----------|-------|--------|----------|--------|
| "Fix A, B, C" | FANOUT | developer | 3 | Ja | ✅ |
| "Fix A..E" | FANOUT(2 Batches) | developer | 5 | Ja | ✅ |
| "Feature X mit Tests" | PIPELINE | — | 4 | Nein | ✅ |
| "Fix A + Test B" | PARALLEL_GROUP | dev+tester | 2 | Ja | ✅ |

## Parallel-Dispatch (Opencode)

| Operation | Syntax | Valid | Status |
|-----------|--------|-------|--------|
| FANOUT(3) | 3× task() in einer Nachricht | ✅ | ✅ |
| PARALLEL_GROUP(2) | 2× task() verschiedene Typen | ✅ | ✅ |
| BARRIER | Automatisch | ✅ | ✅ |

## Viz-Log-Events

| # | Typ | Timestamp | Status |
|---|-----|-----------|--------|
| 1 | intent_classified | 19:40:17 | ✅ |
| 2 | task_decomposed | 19:40:18 | ✅ |
| 3 | dispatch_plan_generated | 19:40:18 | ✅ |

## Warnungen

- `test_fanout_batching`: "Continue-Nutzer: FANOUT fällt auf sequentiellen Modus zurück."
- `test_unknown_fallback`: "ask-user-Modus erfordert User-Interaktion — nicht für CI geeignet."
```

### 9.8 File Change Impact Matrix (Testing)

| Datei | Änderung | Typ | Risiko |
|-------|---------|-----|--------|
| `tests/orchestration/` | Neues Test-Package | Code | Niedrig |
| `tests/fixtures/` | Test-Daten (Intents, Multi-Tasks, Provider-Syntax) | Config | Niedrig |
| `tests/orchestration/dry_run/engine.py` | Dry-Run-Engine | Code | Mittel |
| `.claude/commands/test-orchestration.md` | Command für Claude | Text | Niedrig |
| `.opencode/commands/test-orchestration.md` | Command für Opencode | Text | Niedrig |
| `.gemini/commands/test-orchestration.toml` | Command für Gemini | Text | Niedrig |
| `.continue/commands/test-orchestration.md` | Command für Continue | Text | Niedrig |
| `.claude/hooks/orchestration-test.sh` | Optionaler Pre-Commit-Hook | Script | Niedrig |
| `tests/requirements.txt` | Test-Dependencies (pytest, yaml) | Config | Niedrig |

---

## 10. File Change Impact Matrix

### Phase 1 (Core — Orchestrator v3.0.0 + Rules)

| Datei | Änderung | Typ | Risiko |
|-------|---------|-----|--------|
| `rules/1-generic/use-orchestrator.md` | Komplett neu schreiben | Text | Niedrig |
| `config/rules-presets.yaml` | `use-orchestrator` aus `silent` entfernen | Config | Niedrig |
| `agents/1-generic/orchestrator.md` | v2.10.0 → v3.0.0: neue Sections, erweiterte Workflows, Unknown Intent Protocol, User-Override | Major | Mittel |
| `scripts/lib/agents.py` | `_PROVIDER_PARALLEL_PATTERNS` für alle 4 Provider präzisieren | Code | Niedrig |
| `scripts/lib/config.py` | Neue Variable `ORCHESTRATOR_MODE` injizieren (enabled/strict/unknown-fallback) | Code | Niedrig |
| `commands/1-generic/test-orchestration.md` | Neuer Command: Orchestration-Dry-Run | Text | Niedrig |
| `tests/orchestration/` | Neues Test-Package mit Dry-Run-Engine | Code | Mittel |
| `tests/fixtures/` | Testdaten: Intents, Multi-Tasks, Provider-Syntax | Config | Niedrig |
| `tests/requirements.txt` | Test-Dependencies (pytest, pyyaml) | Config | Niedrig |

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

## 11. Rückwärtskompatibilität

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

## 12. Risiken & Mitigation

| Risiko | W'keit | Schwere | Mitigation |
|--------|--------|---------|-----------|
| **Token-Explosion durch N parallele Agenten** | Mittel | Mittel | `MAX_PARALLEL_AGENTS` begrenzt. Batching bei N > Limit. Jeder Sub-Agent bekommt fokussierten Prompt. |
| **Falsche Parallelisierung → Merge-Konflikte** | Mittel | Hoch | Strikte Unabhängigkeits-Prüfung. "Im Zweifel sequentiell". User-Prüfung vor FANOUT > 2. |
| **Continue-Nutzer ohne Parallel-Feature** | Hoch | Niedrig | Klarer Fallback im PARALLEL_PATTERN. User-Info. Kein Funktionsverlust — nur langsamer. |
| **Orchestrator wird Bottleneck bei trivialen Tasks** | Mittel | Niedrig | Ausnahmen-Liste für atomare Ops bleibt. "Fix typo in one line" geht direkt an developer. |
| **Orchestrator v3.0.0 sprengt Kontext-Limit** | Niedrig | Mittel | Neue Sections sind kompakt (<150 Zeilen gesamt). Bestehende Logik unverändert. |
| **User lehnt parallele Ausführung ab** | Mittel | Niedrig | Human-in-the-Loop-Gate: User bestätigt FANOUT > 2. User kann jederzeit `max-parallel-agents: 1` setzen. |
| **Test-Package erhöht Wartungsaufwand** | Mittel | Mittel | Fixtures sind statisch (YAML/JSON), keine Logik. Tests sind deterministisch. Trennung von Dry-Run-Engine und Testdaten. |
| **Dry-Run-Engine driftet vom echten Orchestrator ab** | Mittel | Hoch | Engine liest dasselbe Template (orchestrator.md). Bei Template-Änderung → Tests failen sofort (wünschenswert). |
| **Provider-Syntax-Tests veralten** | Niedrig | Mittel | Fixtures/providers/*.json werden bei jeder PARALLEL_PATTERN-Änderung mitaktualisiert. CI prüft Konsistenz. |

---

## 13. Phasen-Plan

```
Phase 1 — Core (jetzt)
├── use-orchestrator Rule neu schreiben (inkl. User-Override, Orchestrator-Schalter)
├── rules-presets.yaml: use-orchestrator aus silent entfernen
├── agents/1-generic/orchestrator.md → v3.0.0
│   ├── Task Decomposition Protocol
│   ├── Parallel Execution Engine (abstrakt)
│   ├── Result Aggregation
│   ├── Unknown Intent Protocol (mit Meta-Feedback Loop)
│   └── User-Override Handler
├── scripts/lib/agents.py: PARALLEL_PATTERNs präzisieren
├── scripts/lib/config.py: ORCHESTRATOR_MODE Variable injizieren
├── howto/project.yaml.example: orchestrator-Block dokumentieren
├── tests/orchestration/ → Test-Package anlegen
│   ├── dry_run/engine.py
│   ├── fixtures/intents.yaml, multi_tasks.yaml
│   ├── fixtures/providers/*.json
│   └── test_*.py (Intent, Decomposition, Parallel, Provider, Viz, Unknown, Override)
├── commands/test-orchestration.md (1-generic) → für alle Provider generieren
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

## 14. Glossar

| Begriff | Definition |
|---------|-----------|
| **FANOUT** | N Instanzen des gleichen Agent-Typs parallel starten |
| **PARALLEL_GROUP** | Mehrere verschiedene Agent-Typen parallel starten |
| **BARRIER** | Synchronisationspunkt: auf alle parallelen Ergebnisse warten |
| **Thin Router** | Main Session die nur routet, keine Arbeit verrichtet |
| **Task Decomposition** | Zerlegung eines komplexen User-Tasks in unabhängige Sub-Tasks |
| **Selective Embedding** | Nur bestimmte Rules in den Managed Block einbetten, andere als separate Dateien |
| **Graceful Degradation** | Automatischer Fallback auf sequentielle Ausführung bei Providern ohne Parallel-Fähigkeit |
| **User-Override** | Bewusste Umgehung der Orchestrator-Pflicht durch expliziten User-Befehl |
| **Orchestrator-Schalter** | Konfiguration in project.yaml (enabled/strict/unknown-fallback) |
| **Meta-Feedback Loop** | Anonymisiertes Feedback an agent-meta bei unbekannten Intents zur System-Verbesserung |
| **Unknown-Fallback** | Verhalten bei nicht klassifizierbarem Intent: meta-feedback / main-chat / ask-user |
| **Dry-Run** | Simulation der Orchestration ohne echte Agent-Ausführung |
| **Test-Fixtures** | Statische Testdaten (YAML/JSON) für Intent-Routing, Task-Decomposition, Provider-Syntax |
| **FANOUT** | N Instanzen des gleichen Agent-Typs parallel starten |
| **PARALLEL_GROUP** | Mehrere verschiedene Agent-Typen parallel starten |
| **BARRIER** | Synchronisationspunkt: auf alle parallelen Ergebnisse warten |
| **Thin Router** | Main Session die nur routet, keine Arbeit verrichtet |
| **Task Decomposition** | Zerlegung eines komplexen User-Tasks in unabhängige Sub-Tasks |
| **Selective Embedding** | Nur bestimmte Rules in den Managed Block einbetten, andere als separate Dateien |
| **Viz-Log** | Event-Log für Agenten-Visualisierung und Session-Tracking |
| **Orchestration-Test** | Automatisierter Test der gesamten Delegations-Pipeline |
