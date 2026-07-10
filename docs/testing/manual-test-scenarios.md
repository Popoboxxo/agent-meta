# Manual Test Scenarios — agent-meta Framework v0.53.0

> **Generated:** 2026-05-24
> **Total Scenarios:** 64 (16 Features × 4 Providers)
> **Status:** DRAFT

---

## Inhaltsverzeichnis

### Nach Features
1. [Multi-Provider Support](#feature-1-multi-provider-support)
2. [Layer Architecture](#feature-2-layer-architecture)
3. [Orchestrator-First](#feature-3-orchestrator-first)
4. [Systems Engineering Cascade](#feature-4-systems-engineering-cascade)
5. [Agent Visualization](#feature-5-agent-visualization)
6. [MCP Server Management](#feature-6-mcp-server-management)
7. [Provider Isolation](#feature-7-provider-isolation)
8. [Extension System](#feature-8-extension-system)
9. [External Skills](#feature-9-external-skills)
10. [Speech Modes](#feature-10-speech-modes)
11. [Lifecycle Triggers](#feature-11-lifecycle-triggers)
12. [DoD Presets](#feature-12-dod-presets)
13. [Config-Driven Generation](#feature-13-config-driven-generation)
14. [Versioned Templates](#feature-14-versioned-templates)
15. [AI Provider Tier Routing](#feature-15-ai-provider-tier-routing)
16. [Agent Composition](#feature-16-agent-composition)

### Nach Providern
- [Claude (Szenarien 1.1–16.1)](#claude-szenarien)
- [Gemini (Szenarien 1.2–16.2)](#gemini-szenarien)
- [Opencode (Szenarien 1.3–16.3)](#opencode-szenarien)
- [Continue (Szenarien 1.4–16.4)](#continue-szenarien)

---

## Einleitung

Dieses Dokument definiert 64 manuelle Test-Szenarien für das agent-meta Framework v0.53.0.
Jedes Szenario testet eines der 16 Kern-Features auf einem der 4 unterstützten AI-Provider
(Claude, Gemini, Opencode, Continue).

### Test-Umgebung

- **Repository:** agent-meta (Meta-Repo) oder ein instanziiertes Zielprojekt
- **Python:** ≥ 3.8 mit PyYAML installiert (`pip install pyyaml`)
- **Befehl:** `python scripts/sync.py` (mit optionalen Flags)
- **Testmodus:** `--dry-run` für gefahrlose Prüfung

### Status-Legende

| Status | Bedeutung |
|--------|-----------|
| ☐ PASS | Test erfolgreich — alle Erwartungen erfüllt |
| ☐ FAIL | Test fehlgeschlagen — Erwartung nicht erfüllt |
| ☐ BLOCKED | Test kann nicht durchgeführt werden (Abhängigkeit fehlt) |
| ☐ N/A | Nicht anwendbar für diesen Provider |

### Ausfüllanleitung für Tester

1. **Voraussetzungen prüfen:** Stelle sicher, dass alle genannten Bedingungen erfüllt sind.
2. **Schritte ausführen:** Führe die Schritte in der angegebenen Reihenfolge aus.
3. **Tatsächliches Ergebnis notieren:** Dokumentiere was tatsächlich passiert ist.
4. **Status setzen:** ☐ PASS / ☐ FAIL / ☐ BLOCKED.
5. **Bemerkungen:** Füge relevante Beobachtungen, Fehlermeldungen oder Abweichungen hinzu.

---

## Feature 1: Multi-Provider Support

**Beschreibung:** agent-meta unterstützt 4 AI-Provider gleichzeitig (Claude, Gemini, Opencode, Continue).
Jeder Provider bekommt eigene Agent-Dateien, Rules und Konfigurationen in separaten Verzeichnissen.
`sync.py --multi` generiert für alle konfigurierten Provider parallel.

### 1.1 Multi-Provider Support — Claude — Provider-spezifische Agent-Generierung

**Voraussetzungen:**
- agent-meta Repo eingerichtet, `.meta-config/project.yaml` existiert
- `ai-providers: [Claude]` in der Config
- PyYAML installiert

**Schritte:**
1. Führe `python scripts/sync.py --dry-run` aus
2. Prüfe die Ausgabe im Terminal: `.claude/agents/*.md` wird angezeigt
3. Öffne eine generierte Agent-Datei z.B. `.claude/agents/developer.md`
4. Prüfe das Frontmatter: `model:`, `memory:`, `permissionMode:` Felder sind vorhanden

**Erwartetes Ergebnis:**
- `.claude/agents/` wird mit Agent-Dateien befüllt (modell-spezifische Frontmatter-Felder)
- Jeder Agent hat ein `model:` Feld mit Claude-spezifischer Modell-ID (z.B. `claude-sonnet-4-6`)
- `memory:`, `permissionMode:` sind korrekt gesetzt

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 1.2 Multi-Provider Support — Gemini — Provider-spezifische Agent-Generierung

**Voraussetzungen:**
- agent-meta Repo eingerichtet, `.meta-config/project.yaml` mit `ai-providers: [Gemini]`
- PyYAML installiert

**Schritte:**
1. Führe `python scripts/sync.py --dry-run` aus
2. Prüfe ob `.gemini/agents/`-Verzeichnis im Output erscheint
3. Öffne eine generierte Datei z.B. `.gemini/agents/developer.md` (nach tatsächlichem Sync)
4. Prüfe das Frontmatter: `memory:` und `permissionMode:` sind NICHT vorhanden
5. Prüfe: Claude-spezifische Extension-Hook-Zeilen (`> **Extension:** Falls .claude/3-project/...`) wurden entfernt
6. Prüfe: `model:` Feld enthält Gemini-spezifische Modell-ID (z.B. `gemini-3.1-pro-low`)

**Erwartetes Ergebnis:**
- `.gemini/agents/` enthält bereinigte Agent-Dateien ohne Claude-spezifische Elemente
- Frontmatter hat kein `memory:` und kein `permissionMode:` Feld
- Extension-Hooks verweisen auf `.gemini/3-project/` (nicht `.claude/`)
- `model:` zeigt Gemini-Modell-ID

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 1.3 Multi-Provider Support — Opencode — Provider-spezifische Agent-Generierung

**Voraussetzungen:**
- agent-meta Repo eingerichtet, `.meta-config/project.yaml` mit `ai-providers: [Opencode]`
- PyYAML installiert

**Schritte:**
1. Führe `python scripts/sync.py --dry-run` aus
2. Prüfe ob `.opencode/agents/` im Output erscheint
3. Öffne eine generierte Datei z.B. `.opencode/agents/developer.md` (nach Sync)
4. Prüfe das Frontmatter-Format: `name:`, `description:`, `mode: subagent`
5. Prüfe: `model:` enthält Opencode-spezifische Modell-ID (z.B. `opencode/deepseek-v4-flash`)
6. Prüfe: `permission:`-Block ist vorhanden mit Tool-Berechtigungen

**Erwartetes Ergebnis:**
- `.opencode/agents/` enthält Agenten im Opencode-Frontmatter-Format
- Frontmatter: `name`, `description`, `mode: subagent`, optional `model:`, `permission:`
- Claude-spezifische Zeilen (Extension-Hooks) sind entfernt
- `permission:` Block mit gemappten Tool-Berechtigungen (z.B. `bash: allow`, `read: allow`)

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 1.4 Multi-Provider Support — Continue — Provider-spezifische Agent-Generierung

**Voraussetzungen:**
- agent-meta Repo eingerichtet, `.meta-config/project.yaml` mit `ai-providers: [Continue]`
- PyYAML installiert

**Schritte:**
1. Führe `python scripts/sync.py --dry-run` aus
2. Prüfe ob `.continue/agents/` im Output erscheint
3. Öffne eine generierte Datei z.B. `.continue/agents/developer.md` (nach Sync)
4. Prüfe das Frontmatter: minimales Format (`name:`, `description:`, `alwaysApply: false`)
5. Prüfe: kein `model:`, kein `memory:`, kein `permissionMode:` vorhanden
6. Prüfe: Claude-spezifische Extension-Hook-Zeilen sind entfernt

**Erwartetes Ergebnis:**
- `.continue/agents/` enthält Agenten mit minimalem Frontmatter
- `alwaysApply: false` ist gesetzt
- Keine modellspezifischen Felder im Frontmatter
- Claude-spezifische Zeilen sind entfernt
- Agent-Body ist auf das Wesentliche reduziert

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

## Feature 2: Layer Architecture

**Beschreibung:** agent-meta verwendet ein 4-schichtiges Architekturmodell: `0-external` (höchste Priorität) → `1-generic` (Basis) → `2-platform` (Plattform-Overrides) → `3-project` (Projekt-spezifisch). Höhere Schichten überschreiben niedrigere.

### 2.1 Layer Architecture — Claude — Generic-Basis-Template

**Voraussetzungen:**
- agent-meta Repo eingerichtet, frischer Sync-Zustand
- `agents/1-generic/developer.md` existiert und ist unverändert

**Schritte:**
1. Führe `python scripts/sync.py --dry-run` aus
2. Stelle sicher, dass `developer.md` aus `agents/1-generic/` in `.claude/agents/developer.md` generiert wird
3. Öffne `.claude/agents/developer.md` und prüfe ob `version: "2.0.3"` aus dem Frontmatter übernommen wurde
4. Prüfe: `PROJECT_NAME`-Platzhalter wurde durch den Wert aus der Config ersetzt

**Erwartetes Ergebnis:**
- Der generierte Agent basiert auf dem 1-generic Template
- Version, Description und Tools-Frontmatter werden unverändert übernommen
- `{{PROJECT_NAME}}` und andere Platzhalter sind korrekt substituiert

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 2.2 Layer Architecture — Gemini — Platform-Override (2-platform)

**Voraussetzungen:**
- agent-meta Repo eingerichtet, `agents/2-platform/agent-meta-developer.md` existiert
- Plattform `agent-meta` in der Config

**Schritte:**
1. Öffne `agents/2-platform/agent-meta-developer.md` und lies den Inhalt
2. Führe `python scripts/sync.py --dry-run` aus
3. Prüfe: der generierte Agent in `.gemini/agents/developer.md` (nach Sync) enthält die platform-spezifischen Änderungen
4. Vergleiche mit dem generischen `agents/1-generic/developer.md` — platform-spezifische Inhalte sind enthalten

**Erwartetes Ergebnis:**
- Die 2-platform Datei überschreibt (oder erweitert) die 1-generic Basis
- Der generierte Agent enthält die platform-spezifischen Ergänzungen
- Falls `extends:` verwendet wird: Composition wurde korrekt aufgelöst

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 2.3 Layer Architecture — Opencode — Layer-Priorität (External gewinnt)

**Voraussetzungen:**
- agent-meta Repo eingerichtet
- Ein 0-external Skill ist aktiviert (z.B. `home-organization` in skills-registry.yaml)
- Der Skill definiert eine Rolle die auch in 1-generic existiert

**Schritte:**
1. Prüfe in `config/skills-registry.yaml`: Welche Rollen sind in 0-external definiert?
2. Prüfe ob es eine gleichnamige Rolle in `agents/1-generic/` gibt
3. Führe `python scripts/sync.py --dry-run` aus
4. Prüfe: Im Konfliktfall gewinnt die höhere Schicht (0-external > 1-generic)

**Erwartetes Ergebnis:**
- Bei Namenskonflikten gewinnt die höherpriore Schicht
- 0-external überschreibt 1-generic
- 2-platform überschreibt 1-generic aber nicht 0-external
- Log zeigt welche Quelle gewonnen hat

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 2.4 Layer Architecture — Continue — 3-project Extension Override

**Voraussetzungen:**
- agent-meta Repo eingerichtet
- `agents/3-project/` existiert (leer oder mit Inhalt)
- Es existiert eine `developer-ext.md` oder `developer.md` in 3-project

**Schritte:**
1. Lege eine Extension-Datei an: `.continue/3-project/developer-ext.md` (oder prüfe existierende)
2. Führe `python scripts/sync.py --dry-run` aus
3. Prüfe: Die Extension wird im generierten Agenten referenziert
4. Öffne `.continue/agents/developer.md` nach Sync und prüfe den Extension-Hinweis (falls vorhanden)

**Erwartetes Ergebnis:**
- 3-project Erweiterungen werden korrekt in generierte Agenten integriert
- Eine `-ext.md` Datei wird als Extension geladen (additiv)
- Eine `.md` Datei (ohne -ext) überschreibt den gesamten Agenten (Override)

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

## Feature 3: Orchestrator-First

**Beschreibung:** Der Orchestrator ist der zentrale Einstiegspunkt für alle Entwicklungsaufgaben.
Er zerlegt komplexe Tasks, parallelisiert unabhängige Arbeitsschritte via FANOUT/PARALLEL_GROUP/BARRIER
und delegiert an spezialisierte Worker-Agenten. Provider-spezifische Parallel-Muster werden via
`{{PARALLEL_PATTERN}}` injiziert.

### 3.1 Orchestrator-First — Claude — FANOUT Parallel-Dispatch mit background

**Voraussetzungen:**
- Claude Code CLI ist installiert und konfiguriert
- Ein Projekt mit aktiviertem Orchestrator

**Schritte:**
1. Öffne Claude Code im Projekt
2. Starte den Orchestrator: `claude -a orchestrator` (oder wähle ihn in der IDE)
3. Gib ein: "Fix bugs A, B, C" (3 unabhängige Bugs)
4. Beobachte: Der Orchestrator zerlegt in 3 Tasks
5. Prüfe: Claude Code CLI startet 3 parallele Agent-Sessions (FANOUT-Pattern wird nativ unterstützt)

**Erwartetes Ergebnis:**
- Orchestrator klassifiziert den Intent korrekt als "Neues Feature / Bugfix"
- Delegiert an `developer` (oder `feature`)
- FANOUT-Muster: 3 unabhängige Sub-Tasks werden identifiziert
- Claude nutzt `run_in_background=True` für parallele Ausführung
- Nach BARRIER: Ergebnis-Zusammenfassung wird präsentiert

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 3.2 Orchestrator-First — Gemini — FANOUT mit nativem planning_mode

**Voraussetzungen:**
- Gemini Code Assist ist installiert und konfiguriert
- Ein Projekt mit aktiviertem Orchestrator

**Schritte:**
1. Öffne Gemini in VS Code
2. Gib `@orchestrator Write tests for A, B, C` ein
3. Beobachte: Gemini startet den Orchestrator
4. Prüfe: Der native planning_mode von Gemini wird durch die Orchestrator-Planning-Phase unterdrückt
5. Der Orchestrator delegiert an 3× `tester` parallel (automatisch durch Gemini's parallele Tool-Ausführung)

**Erwartetes Ergebnis:**
- Orchestrator wird via @orchestrator gestartet
- Planning-Phase des Orchestrators hat Vorrang vor Gemini's nativem planning_mode
- FANOUT(3, tester, [tests für A, tests für B, tests für C]) wird ausgeführt
- Gemini führt unabhängige Tool-Aufrufe parallel aus (automatisch)

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 3.3 Orchestrator-First — Opencode — PARALLEL_GROUP mit task()

**Voraussetzungen:**
- Opencode (VS Code Extension) installiert und konfiguriert
- Ein Projekt mit aktiviertem Orchestrator

**Schritte:**
1. Öffne Opencode in VS Code
2. Gib `@orchestrator Fix A and write tests for C` ein
3. Beobachte: Orchestrator startet
4. Prüfe: Der Orchestrator erkennt PARALLEL_GROUP (unterschiedliche Agent-Typen: developer + tester)
5. Prüfe: Opencode verwendet `task()`-Calls für parallele Dispatch, ohne `background`
6. BARRIER wartet auf beide Ergebnisse

**Erwartetes Ergebnis:**
- Orchestrator erkennt PARALLEL_GROUP-Muster (developer ∥ tester)
- Opencode verwendet `task(subagent_type="developer", ...)` und `task(subagent_type="tester", ...)` in einer Antwort
- Kein `background`-Flag nötig — alle `task()`-Calls laufen parallel
- Ergebnisse beider Agents werden gesammelt und präsentiert

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 3.4 Orchestrator-First — Continue — Sequentielle Fallback-Ausführung

**Voraussetzungen:**
- Continue (IDE Plugin) installiert und konfiguriert
- Ein Projekt mit aktiviertem Orchestrator

**Schritte:**
1. Öffne Continue in der IDE
2. Gib die Aufgabe in Continue ein: "Refactor module A and B" (mit Orchestrator-Kontext aus `.continue/agents/orchestrator.md` geladen)
3. Beobachte: Continue verarbeitet die Anfrage sequentiell
4. Prüfe: Continue hat keine native parallele Subagent-Ausführung
5. Der Orchestrator führt die Tasks sequentiell aus (ein Prompt nach dem anderen)

**Erwartetes Ergebnis:**
- Orchestrator erkennt FANOUT-Muster (2× developer parallel)
- Da Continue kein natives Parallel-Dispatch unterstützt, werden Tasks sequentiell ausgeführt
- `{{PARALLEL_PATTERN}}` zeigt "not supported" / "sequential" an
- Ergebnis: Task B wird erst gestartet nachdem Task A abgeschlossen ist

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

## Feature 4: Systems Engineering Cascade

**Beschreibung:** Die SE-Kaskade ist ein fraktales, rekursives Systems-Engineering-System mit
6 spezialisierten Agenten (se-requirements → se-architect → se-critic → se-interface-mgr →
se-termination → (se-validator | se-verifier)). Maximal 5 Stufen Tiefe. Nur in Projekten mit
`systems-engineering.enabled: true` aktiv.

### 4.1 Systems Engineering Cascade — Claude — L1 Blackbox → Whitebox Zerlegung

**Voraussetzungen:**
- `.meta-config/project.yaml` hat `systems-engineering.enabled: true`
- Claude Code CLI installiert

**Schritte:**
1. Starte Claude Code
2. Gib ein: "Starte den SE-Prozess für ein Benachrichtigungssystem"
3. Der orchestrator (SE-Mode) startet die Kaskade
4. Prüfe: se-requirements erstellt ein L1-Blackbox-Requirement
5. Prüfe: se-architect zerlegt in Whitebox-Komponenten
6. Prüfe: se-critic prüft Architekturentscheidungen
7. Prüfe: se-interface-mgr definiert Schnittstellenverträge
8. Prüfe: se-termination entscheidet Leaf/Continue
9. Bei continue: neue Zelle (n+1) wird gestartet

**Erwartetes Ergebnis:**
- Vollständige L1→L2→L3 Kaskade durchläuft
- Architekturentscheidungen werden von se-critic validiert
- Schnittstellenverträge werden von se-interface-mgr dokumentiert
- Leaf-Komponenten werden als abgeschlossen markiert
- Maximale Tiefe (`SE_MAX_DEPTH=5`) wird eingehalten

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 4.2 Systems Engineering Cascade — Gemini — Fraktale Zellteilung

**Voraussetzungen:**
- `.meta-config/project.yaml` hat `systems-engineering.enabled: true`
- Gemini Code Assist installiert

**Schritte:**
1. Starte Gemini und rufe den orchestrator (SE-Mode) auf
2. Gib eine komplexe Anforderung ein (z.B. "IoT Sensorplattform")
3. Beobachte den rekursiven Herunterbruch
4. Prüfe: Eine neue Zelle wird gestartet wenn se-termination `continue` meldet
5. Prüfe: Die Zelle hat keine Contamination (kein Zugriff auf fremde Zell-Daten)
6. Prüfe: Maximale parallele Zellen (`SE_MAX_PARALLEL_CELLS=4`) wird eingehalten

**Erwartetes Ergebnis:**
- Fraktale Zellteilung funktioniert korrekt
- Keine Contamination zwischen Zellen
- `max_depth` (5) und `max_parallel_cells` (4) Limits werden eingehalten
- Context-Window-Regel (nur Parent-Blackbox + Interfaces) wird befolgt

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 4.3 Systems Engineering Cascade — Opencode — L3 Terminierung

**Voraussetzungen:**
- `.meta-config/project.yaml` hat `systems-engineering.enabled: true`
- Opencode installiert

**Schritte:**
1. Starte den orchestrator (SE-Mode) via `@orchestrator`
2. Gib: "Starte SE-Kaskade für eine einfache CRUD-API"
3. Beobachte den rekursiven Herunterbruch bis L3
4. Prüfe: se-termination erkennt dass die Komponente ein Leaf-Node ist
5. Prüfe: Keine unendliche Rekursion — die Kaskade terminiert

**Erwartetes Ergebnis:**
- Kaskade erreicht L3 (Component Level)
- se-termination markiert Leaf-Nodes korrekt
- Deterministische Terminierung — keine Endlos-Rekursion
- Ergebnisse werden an orchestrator (SE-Mode) zurückgemeldet

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 4.4 Systems Engineering Cascade — Continue — Validierung & Verifikation

**Voraussetzungen:**
- `.meta-config/project.yaml` hat `systems-engineering.enabled: true`
- Continue IDE Plugin installiert

**Schritte:**
1. Schließe eine SE-Kaskade ab (oder simuliere eine)
2. Lade den se-validator-Kontext in Continue und gib ein: "Validiere das System gegen L1-Requirement"
3. Lade den se-verifier-Kontext in Continue und gib ein: "Verifiziere L2-Komponenten gegen Spezifikation"
4. Prüfe: se-validator führt User-Journey-Simulation durch
5. Prüfe: se-verifier prüft Multi-Level (L1-Ln)

**Erwartetes Ergebnis:**
- se-validator validiert korrekt gegen Stakeholder-Bedürfnisse
- se-verifier prüft alle Architektur-Ebenen
- Unterschied zwischen Validation ("das richtige System") und Verification ("das System richtig") wird eingehalten
- Ergebnisse werden dokumentiert

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

## Feature 5: Agent Visualization

**Beschreibung:** agent-meta generiert 4 Visualisierungs-Artefakte: (1) Statische Mermaid-Mindmap
(`docs/agent-mindmap.md`), (2) Interaktiver HTML-Graph (`docs/agent-graph.html`),
(3) Dynamisches Session-Tracking (`.meta-viz/events.jsonl`), (4) Live-Dashboard
(`docs/live-dashboard.html`). Aktivierbar per `viz.enabled: true` und `viz.mode: static|dynamic|full`.

### 5.1 Agent Visualization — Claude — Statische Mindmap-Generierung

**Voraussetzungen:**
- `.meta-config/project.yaml` hat `viz.enabled: true`, `viz.mode: full`
- `docs/agent-mindmap.md` und `docs/agent-graph.html` existieren

**Schritte:**
1. Führe `python scripts/sync.py --dry-run` aus
2. Prüfe ob im Output `docs/agent-mindmap.md` und `docs/agent-graph.html` erscheinen
3. Führe `python scripts/sync.py` (ohne --dry-run) aus
4. Öffne `docs/agent-mindmap.md` — prüfe Mermaid-Mindmap mit allen Rollen
5. Öffne `docs/agent-graph.html` im Browser — prüfe interaktive Graph-Visualisierung
6. Prüfe: Legende zeigt 🔴 required, 🔵 recommended, ⚪ optional

**Erwartetes Ergebnis:**
- Mindmap zeigt alle aktiven Agenten mit Hierarchie (Orchestrator als Root)
- HTML-Graph ist interaktiv (Klick auf Agenten scrollt zu Details)
- Farbcodierung nach Workflow-Tier (required/recommended/optional)
- Modell- und Memory-Informationen werden korrekt angezeigt

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 5.2 Agent Visualization — Gemini — Dynamic Session-Tracking

**Voraussetzungen:**
- `.meta-config/project.yaml` hat `viz.mode: dynamic` oder `full`
- `.meta-viz/` existiert und ist in `.gitignore`

**Schritte:**
1. Führe eine Aufgabe mit einem generierten Agent aus (z.B. starte den Dokumentations-Agenten)
2. Prüfe: Der Agent schreibt ein `agent_start`-Event in `.meta-viz/events.jsonl`
3. Wenn der Agent delegiert: Prüfe `delegate`-Event in `.meta-viz/events.jsonl`
4. Wenn der Agent fertig ist: Prüfe `agent_end`-Event
5. Prüfe: Alle Events haben einen `ts` (Timestamp) im ISO-8601-Format

**Erwartetes Ergebnis:**
- Events werden korrekt in `.meta-viz/events.jsonl` geschrieben
- Format: JSONL (eine Zeile JSON pro Event)
- Pflicht-Events: `agent_start`, `delegate` (optional), `agent_end`
- Timestamps sind im UTC-ISO-8601 Format
- Keine Secrets in den Events

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 5.3 Agent Visualization — Opencode — Live-Dashboard

**Voraussetzungen:**
- `.meta-config/project.yaml` hat `viz.mode: full`
- `docs/live-dashboard.html` existiert

**Schritte:**
1. Öffne `docs/live-dashboard.html` im Browser
2. Prüfe: Dashboard zeigt Session-Informationen an
3. Führe einige Agent-Aufrufe durch (erzeuge Events)
4. Lade das Dashboard neu — prüfe ob neue Events sichtbar sind
5. Prüfe: Dashboard hat Filter- oder Such-Funktionalität

**Erwartetes Ergebnis:**
- Live-Dashboard zeigt Echtzeit-Agent-Aktivität
- Events aus `.meta-viz/events.jsonl` werden angezeigt
- Visualisierung unterscheidet zwischen verschiedenen Event-Typen
- Dashboard ist responsive und funktioniert ohne Server (reines HTML/JS)

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 5.4 Agent Visualization — Continue — Event-Log Retention

**Voraussetzungen:**
- `.meta-config/project.yaml` hat `viz.mode: full`
- `viz.report.retention_days: 7` gesetzt
- Es existieren alte Session-Logs in `.meta-viz/`

**Schritte:**
1. Führe mehrer Sessions durch (erzeuge `events-*.jsonl` Dateien)
2. Simuliere alte Sessions: erstelle eine Datei `events-old.jsonl` und ändere das Datum (z.B. via `touch -d "8 days ago" .meta-viz/events-old.jsonl` auf Linux/Mac, oder manuell im Explorer unter Eigenschaften auf Windows)
3. Führe `python scripts/sync.py` aus
4. Prüfe: Alte Sessions (älter als retention_days) werden gelöscht
5. Prüfe: Aktuelle Sessions bleiben erhalten

**Erwartetes Ergebnis:**
- Retention-Mechanismus löscht Sessions älter als 7 Tage
- Nur `.meta-viz/events-*.jsonl` Dateien sind betroffen
- Aktuelle Sessions bleiben unberührt
- Cleanup läuft als Teil von sync.py (oder beim Start eines Agenten)

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

## Feature 6: MCP Server Management

**Beschreibung:** agent-meta verwaltet MCP (Model Context Protocol) Server zentral via
`config/mcp-registry.yaml`. sync.py generiert pro aktivem Server: (1) Rule-Dateien mit
Tool-Whitelist/Blacklist, (2) Provider-Konfiguration mit `${ENV_VAR}`-Referenzen,
(3) Secrets-Template `.meta-config/secrets.local.yaml`, (4) .gitignore-Einträge.

### 6.1 MCP Server Management — Claude — Registry → Rule-Generierung

**Voraussetzungen:**
- `config/mcp-registry.yaml` existiert mit mindestens 1 Server (z.B. `home-assistant`, `influxdb`)
- `.meta-config/project.yaml` hat `mcp-servers: [home-assistant]`

**Schritte:**
1. Führe `python scripts/sync.py --dry-run` aus
2. Prüfe: Rule-Datei `.claude/rules/mcp-home-assistant.md` erscheint im Output
3. Führe `python scripts/sync.py` (ohne --dry-run) aus
4. Öffne `.claude/rules/mcp-home-assistant.md`
5. Prüfe: Erlaubte Tools (z.B. `GetLiveContext`, `GetDateTime`) sind gelistet
6. Prüfe: Verbotene Tools (z.B. `HassTurnOn`, `HassTurnOff`) sind gelistet
7. Prüfe: Agent-Hinweise aus der Registry sind enthalten

**Erwartetes Ergebnis:**
- MCP-Regel-Datei wird korrekt generiert
- Tool-Whitelist und Blacklist aus mcp-registry.yaml werden übernommen
- Verbindungstyp (SSE/STDIO) wird dokumentiert
- Datei wird als "nicht manuell bearbeiten" markiert

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 6.2 MCP Server Management — Gemini — Secrets-Scanning und .gitignore

**Voraussetzungen:**
- MCP-Server mit Secrets konfiguriert (z.B. `MCP_HA_TOKEN`, `MCP_INFLUXDB_TOKEN`)
- `.meta-config/secrets.local.yaml` existiert (oder wird generiert)

**Schritte:**
1. Führe `python scripts/sync.py` aus
2. Prüfe ob `.meta-config/secrets.local.yaml` generiert wurde (wenn nicht vorhanden)
3. Öffne die generierte `.gemini/settings.json` (oder .gemini/settings.local.json) — MCP-Config mit `${MCP_HA_URL}` Variablen
4. Prüfe: Secrets-Dateien sind in `.gitignore` eingetragen
5. Prüfe: Committete Config enthält nur `${ENV_VAR}` Referenzen, keine Klartext-Secrets

**Erwartetes Ergebnis:**
- Secrets-Template wird generiert (oder existiert) mit leeren Secret-Feldern
- Provider-Konfiguration verwendet `${ENV_VAR}` oder `{{ENV_VAR}}` Syntax
- `.gitignore` enthält Einträge für Secrets-Dateien
- Keine Klartext-Secrets in committed Config-Dateien
- Secrets-Scan warnt bei versehentlichen Klartext-Secrets

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 6.3 MCP Server Management — Opencode — Config-Generierung

**Voraussetzungen:**
- MCP-Server in Registry konfiguriert
- `ai-providers` enthält Opencode

**Schritte:**
1. Führe `python scripts/sync.py` aus
2. Öffne `opencode.json`
3. Prüfe: `mcp`-Block wurde hinzugefügt mit dem konfigurierten Server
4. Prüfe: Verbindungstyp (SSE: `url` + `headers`, stdio: `command`-Array)
5. Prüfe: `{env:VAR}` Syntax für Secrets (Opencode-spezifisch)
6. Prüfe: `.opencode/mcp.local.json` als Secrets-Datei in .gitignore

**Erwartetes Ergebnis:**
- Opencode-Konfiguration in `opencode.json` enthält MCP-Einträge
- Verbindungsparameter werden korrekt in Opencode-Format konvertiert
- Secrets verwenden `{env:VAR}` Syntax (Opencode-spezifisch)
- Secrets-Datei ist in `.gitignore` eingetragen

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 6.4 MCP Server Management — Continue — YAML-Config-Integration

**Voraussetzungen:**
- MCP-Server in Registry konfiguriert
- Continue in `ai-providers` aktiv

**Schritte:**
1. Führe `python scripts/sync.py` aus
2. Öffne `.continue/config.yaml`
3. Prüfe: `mcpServers`-Block existiert (in managed Block `# agent-meta:mcp-begin/end`)
4. Prüfe: YAML-Format ist korrekt (Liste von Servern mit name + connection)
5. Prüfe: `config.local.yaml` als Secrets-Datei in .gitignore
6. Prüfe: User-spezifische Config-Teile (model, etc.) bleiben erhalten

**Erwartetes Ergebnis:**
- Continue YAML-Config enthält MCP-Einträge im managed Block
- Format: Liste von Servern mit `name:` und Verbindungsparametern
- Bestehende User-Konfiguration wird nicht überschrieben
- Managed Block ermöglicht Update bei nächstem Sync

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

## Feature 7: Provider Isolation

**Beschreibung:** Wenn mehrere AI-Provider gleichzeitig aktiv sind, generiert sync.py
Hard-Blocks um zu verhindern, dass ein Provider auf Dateien eines anderen Providers zugreift.
Claude → `permissions.deny` in settings.json. Opencode → `permission.read/edit` in opencode.json.
Gemini → TOML-Policy-Datei. Continue → Soft-Guidance-Markdown (kein nativer Hard-Block).

### 7.1 Provider Isolation — Claude — permissions.deny in settings.json

**Voraussetzungen:**
- `ai-providers: [Claude, Gemini, Opencode, Continue]` (mindestens 2)
- `.meta-config/project.yaml` hat NICHT `provider-isolation: disabled`
- `.claude/settings.json` existiert

**Schritte:**
1. Führe `python scripts/sync.py --dry-run` aus
2. Prüfe: provider-isolation wird im Log erwähnt
3. Führe `python scripts/sync.py` aus
4. Öffne `.claude/settings.json`
5. Prüfe: `permissions.deny` enthält Glob-Patterns für fremde Provider-Verzeichnisse
6. Prüfe: `.gemini/**` und `.opencode/**` sind in der Deny-Liste
7. Prüfe: Claude's eigene Verzeichnisse sind NICHT in der Deny-Liste
8. Prüfe: Companion-State-Datei `.claude/agent-meta-state.json` existiert

**Erwartetes Ergebnis:**
- `.claude/settings.json` blockiert Zugriff auf `.gemini/**`, `.opencode/**`, `.continue/**`
- Claude's eigene Verzeichnisse (`.claude/`, `CLAUDE.md`) sind nicht blockiert
- Companion-State-Datei trackt verwaltete Pattern für saubere Updates
- Bei nur 1 aktivem Provider wird keine Isolation generiert

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 7.2 Provider Isolation — Gemini — TOML-Policy-Datei

**Voraussetzungen:**
- Mindestens 2 Provider aktiv (einschließlich Gemini)
- `.gemini/policies/` existiert

**Schritte:**
1. Führe `python scripts/sync.py` aus
2. Öffne `.gemini/policies/provider-isolation.toml`
3. Prüfe: Eine `[[rule]]` pro fremdem Provider-Verzeichnis
4. Prüfe: `toolName` enthält relevante Tools (`read_file`, `write_file`, etc.)
5. Prüfe: `argsPattern` matcht den fremden Pfad
6. Prüfe: `decision = "deny"` und `priority = 9xx`
7. Prüfe: `denyMessage` nennt den besitzenden Provider

**Erwartetes Ergebnis:**
- TOML-Policy-Datei wird generiert mit einer Rule pro fremdem Verzeichnis
- Rules haben korrekte Regex-Pattern für Dateipfade
- Priorität ist hoch genug (900+)
- Verständliche denyMessage (z.B. "Provider isolation: .claude is managed by Claude Code only.")

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 7.3 Provider Isolation — Opencode — permission.read/edit in opencode.json

**Voraussetzungen:**
- Mindestens 2 Provider aktiv (einschließlich Opencode)
- `opencode.json` existiert

**Schritte:**
1. Führe `python scripts/sync.py` aus
2. Öffne `opencode.json`
3. Prüfe: `permission.read` und `permission.edit` enthalten `"deny"`-Einträge für fremde Provider-Verzeichnisse
4. Prüfe: Opencode verwendet last-match-wins — deny-Einträge sind nach allow-Einträgen sortiert
5. Prüfe: `.opencode/`-Verzeichnis ist selbst nicht blockiert

**Erwartetes Ergebnis:**
- Opencode-Konfiguration blockiert Lese-/Schreibzugriff auf `.claude/**`, `.gemini/**`, `.continue/**`
- Last-match-wins: deny-Pattern überschreiben allow-Pattern aus anderen Konfigurationen
- Companion-State-Datei in `.opencode/agent-meta-state.json` trackt verwaltete Pattern

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 7.4 Provider Isolation — Continue — Soft-Guidance (kein Hard-Block)

**Voraussetzungen:**
- Mindestens 2 Provider aktiv (einschließlich Continue)
- `.continue/rules/` existiert

**Schritte:**
1. Führe `python scripts/sync.py` aus
2. Öffne `.continue/rules/provider-isolation.md`
3. Prüfe: Dokument listet fremde Provider-Verzeichnisse auf
4. Prüfe: Es ist eine "Soft-Guidance" Regel — keine technische Durchsetzung
5. Prüfe: Text fordert dazu auf, fremde Verzeichnisse nicht zu lesen/schreiben

**Erwartetes Ergebnis:**
- Continue bekommt eine Soft-Guidance-Markdown-Datei (kein Hard-Block möglich)
- Liste der fremden Verzeichnisse ist vollständig
- Text ist klar und verständlich
- Continue hat keinen natives Mechanismus für Hard-Blocks — das ist bekannt und dokumentiert

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

## Feature 8: Extension System

**Beschreibung:** agent-meta unterstützt zwei Arten von projektspezifischen Erweiterungen:
(1) **Extensions** (`<prefix>-<rolle>-ext.md`) — werden vom generierten Agent zur Laufzeit
gelesen. (2) **Managed Blocks** (`<!-- agent-meta:managed-begin -->`) — automatisch aktualisierte
Blöcke in Extension-Dateien. `--create-ext` erstellt, `--update-ext` aktualisiert.

### 8.1 Extension System — Claude — Extension-Erstellung mit --create-ext

**Voraussetzungen:**
- agent-meta Repo eingerichtet, `.meta-config/project.yaml` mit `prefix: am`
- `.claude/3-project/` existiert

**Schritte:**
1. Führe `python scripts/sync.py --dry-run --create-ext developer` aus
2. Prüfe Log: "CREATE .claude/3-project/am-developer-ext.md"
3. Führe `python scripts/sync.py --create-ext developer` aus
4. Öffne `.claude/3-project/am-developer-ext.md`
5. Prüfe: Managed Block mit Projekt-Informationen existiert
6. Prüfe: Projektspezifischer Bereich (unter `## Projektspezifische Erweiterungen`) ist vorhanden
7. Führe denselben Befehl erneut aus — Prüfe: "extension already exists" Meldung

**Erwartetes Ergebnis:**
- Extension-Datei wird erstellt mit korrektem Prefix (`am-developer-ext.md`)
- Managed Block enthält aktuelle Projekt-Informationen
- Projektspezifischer Bereich ist leer und bereit für User-Einträge
- Doppelte Erstellung wird verhindert (idempotent)

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 8.2 Extension System — Gemini — --update-ext Managed Block

**Voraussetzungen:**
- Mindestens eine Extension-Datei existiert (z.B. `.gemini/3-project/am-developer-ext.md`)
- Projekt-Variablen wurden geändert (z.B. PROJECT_NAME geändert)

**Schritte:**
1. Ändere den PROJECT_NAME in `.meta-config/project.yaml` (temporär)
2. Führe `python scripts/sync.py --dry-run --update-ext` aus
3. Prüfe: "UPDATE .gemini/3-project/am-developer-ext.md managed block" erscheint
4. Führe `python scripts/sync.py --update-ext` aus
5. Öffne die Extension-Datei — prüfe ob PROJECT_NAME im Managed Block aktualisiert wurde
6. Prüfe: Der projektspezifische Bereich (User-Content) wurde NICHT überschrieben
7. Setze PROJECT_NAME zurück

**Erwartetes Ergebnis:**
- Managed Block wird aktualisiert ohne User-Content zu überschreiben
- Nur der Bereich zwischen `<!-- agent-meta:managed-begin -->` und `<!-- agent-meta:managed-end -->` wird ersetzt
- Projekt-spezifischer Content bleibt erhalten
- Ohne Änderung: "managed block unchanged" Meldung

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 8.3 Extension System — Opencode — Extension-Hook im generierten Agenten

**Voraussetzungen:**
- Eine Extension-Datei existiert (z.B. `.opencode/3-project/developer-ext.md`)
- Sync wurde durchgeführt

**Schritte:**
1. Öffne `.opencode/agents/developer.md`
2. Prüfe: Die erste Zeile nach dem Frontmatter enthält einen Extension-Hinweis
3. Der Hinweis verweist auf `.opencode/3-project/developer-ext.md` (oder den korrekten Extension-Dir)
4. Führe `python scripts/sync.py` aus (nach Änderung der Extension)
5. Prüfe: Der generierte Agent bleibt korrekt — Extension-Hook ist intakt

**Erwartetes Ergebnis:**
- Generierte Agenten referenzieren die Extension-Datei im richtigen Provider-Verzeichnis
- Extension-Dir ist korrekt: `.opencode/3-project/` für Opencode
- Extension wird vom Agenten zur Laufzeit geladen (wenn der Provider das unterstützt)

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 8.4 Extension System — Continue — Extension-Inhalte werden geladen

**Voraussetzungen:**
- Continue Provider aktiv, Extension-Datei vorhanden
- `.continue/agents/` wurde synchronisiert

**Schritte:**
1. Öffne `.continue/agents/developer.md`
2. Prüfe: Extension-Hook-Zeile ist vorhanden (wenn nicht entfernt für Continue)
3. Füge projektspezifische Regeln in `.continue/3-project/developer-ext.md` hinzu
4. Lade den Agenten-Kontext in Continue und stelle eine Testfrage
5. Prüfe: Die Extension-Inhalte werden im Agenten-Text referenziert (Agent verweist darauf)

**Erwartetes Ergebnis:**
- Extension wird im generierten Agenten verlinkt (oder erwähnt)
- Der Agent kann die Extension zur Laufzeit lesen
- Für Continue werden Claude-spezifische Extension-Hooks entfernt (weil sie `.claude/` referenzieren)
- Continue-spezifische Extension-Pfade werden stattdessen verwendet

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

## Feature 9: External Skills

**Beschreibung:** agent-meta unterstützt externe Skill-Pakete via Git-Submodule.
`config/skills-registry.yaml` definiert Repos und Skills. Skills haben einen
zweistufigen Approval-Prozess: (1) `approved: true` im Meta-Repo (Quality Gate),
(2) `enabled: true` im Zielprojekt. sync.py generiert Wrapper-Agenten und kopiert
Skill-Dateien in das provider-spezifische Skills-Verzeichnis.

### 9.1 External Skills — Claude — Skill-Aktivierung und Wrapper-Generierung

**Voraussetzungen:**
- `config/skills-registry.yaml` hat mindestens einen `approved: true` Skill (z.B. `home-organization`)
- Git-Submodule sind initialisiert (`git submodule update --init`)
- `.meta-config/project.yaml` hat `external-skills: {home-organization: {enabled: true}}`

**Schritte:**
1. Führe `python scripts/sync.py --dry-run` aus
2. Prüfe: Wrapper-Agent für `home-organization` wird generiert (`.claude/agents/home-organization-specialist.md`)
3. Prüfe: Skill-Dateien werden nach `.claude/skills/home-organization/` kopiert
4. Führe `python scripts/sync.py` aus
5. Öffne `.claude/agents/home-organization-specialist.md`
6. Prüfe: Frontmatter enthält korrekte Werte (Name, Description, Version)
7. Prüfe: Body verweist auf `.claude/skills/home-organization/SKILL.md`

**Erwartetes Ergebnis:**
- Wrapper-Agent wird generiert mit korrektem Frontmatter
- Skill-Dateien (SKILL.md + additional_files) werden in provider-spezifisches Skills-Verzeichnis kopiert
- Relative Pfade in SKILL.md werden zu absoluten Pfaden normalisiert
- Zwei-Gate-Check: approved + enabled muss erfüllt sein

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 9.2 External Skills — Gemini — Pinned Commit Check

**Voraussetzungen:**
- External Skill konfiguriert mit `pinned_commit` in skills-registry.yaml
- Git-Submodule existieren

**Schritte:**
1. Öffne `config/skills-registry.yaml` — notiere den `pinned_commit` für `neat-little-package`
2. Führe `git submodule status` im agent-meta Root aus
3. Vergleiche: Steht das Submodule auf dem gepinnten Commit?
4. Wenn nicht: Führe `git -C external/neat-little-package checkout <pinned_commit>` aus
5. Führe `python scripts/sync.py --dry-run` aus
6. Prüfe Log: Keine Warnung wegen falschem Commit (wenn korrekt eingestellt)

**Erwartetes Ergebnis:**
- `check_pinned_commits()` prüft ob Submodule auf dem konfigurierten Commit stehen
- Warnung bei Abweichung: "submodule is at X, expected pinned_commit Y"
- Keine Warnung bei korrektem Commit
- Commit-Präfix-Vergleich (short hash) funktioniert korrekt

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 9.3 External Skills — Opencode — Zwei-Gate Approval-System

**Voraussetzungen:**
- `config/skills-registry.yaml` enthält einen Skill mit `approved: false` (z.B. `mermaid-renderer`)

**Schritte:**
1. Prüfe in skills-registry.yaml: Ein Skill hat `approved: false`
2. Setze in `.meta-config/project.yaml`: `external-skills: {mermaid-renderer: {enabled: true}}`
3. Führe `python scripts/sync.py` aus
4. Prüfe: Der nicht-approved Skill wird NICHT generiert
5. Setze in skills-registry.yaml: `approved: true` für den Skill
6. Führe `python scripts/sync.py` aus
7. Prüfe: Der jetzt approved Skill wird generiert
8. Deaktiviere den Skill in project.yaml (`enabled: false`)
9. Führe `python scripts/sync.py` aus
10. Prüfe: Der deaktivierte Skill wird NICHT generiert (obwohl approved)

**Erwartetes Ergebnis:**
- Beide Gates müssen passieren: `approved: true` UND `enabled: true`
- Nur approved Skills können von Projekten aktiviert werden
- Deaktivierte Skills werden nicht generiert (auch wenn approved)
- Log zeigt den Status jedes Skills an

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 9.4 External Skills — Continue — Stale Skill-Bereinigung

**Voraussetzungen:**
- Ein aktivierter Skill existiert (generierte Wrapper + Skill-Dateien vorhanden)
- Der Skill wird deaktiviert (approved: false ODER enabled: false)

**Schritte:**
1. Aktualisiere skills-registry.yaml: Setze `approved: false` für einen aktiven Skill
2. Führe `python scripts/sync.py` aus
3. Prüfe: Wrapper-Agent wird gelöscht (`.continue/agents/<role>.md`)
4. Prüfe: Skill-Dateien werden entfernt (`.continue/skills/<skill_name>/`)
5. Prüfe: Log zeigt "DELETE" Aktionen für die entfernten Dateien
6. Reaktiviere den Skill und sync
7. Prüfe: Wrapper und Dateien werden neu generiert

**Erwartetes Ergebnis:**
- Stale Wrapper-Agents werden entfernt
- Stale Skill-Dateien werden gelöscht
- Nur agent-meta-verwaltete Dateien werden gelöscht (keine User-Dateien)
- Reaktivierung führt zu sauberer Neugenerierung

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

## Feature 10: Speech Modes

**Beschreibung:** agent-meta unterstützt 6 Kommunikationsmodi: `full` (Standard),
`short` (kurz & prägnant), `childish` (kindlich), `caveman` (Höhlenmensch), `asozial`
(unhöflich), `submissive` (unterwürfig). Der Modus wird via `speech-mode` in project.yaml
gesetzt und generiert eine Rule `speech/<mode>.md` → `.claude/rules/speech-mode.md`.

### 10.1 Speech Modes — Claude — Standard Modus (full)

**Voraussetzungen:**
- `.meta-config/project.yaml` hat `speech-mode: full` (oder default)
- `speech/full.md` existiert

**Schritte:**
1. Führe `python scripts/sync.py --dry-run` aus
2. Prüfe: Bei Mode "full" wird KEINE speech-mode.md generiert
3. Setze temporär `speech-mode: submissive` in project.yaml
4. Führe `python scripts/sync.py` aus
5. Prüfe: `.claude/rules/speech-mode.md` wurde erstellt
6. Setze zurück auf `speech-mode: full`
7. Führe `python scripts/sync.py` aus
8. Prüfe: `.claude/rules/speech-mode.md` wurde gelöscht

**Erwartetes Ergebnis:**
- "full" Mode: keine Rule-Datei (Default-Verhalten — kein Override nötig)
- Anderer Mode: Rule-Datei wird kopiert
- Wechsel zurück zu "full": Rule-Datei wird entfernt
- Cleanup via .agent-meta-managed Tracking

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 10.2 Speech Modes — Gemini — Submissive Modus

**Voraussetzungen:**
- `.meta-config/project.yaml` hat `speech-mode: submissive`
- `speech/submissive.md` existiert

**Schritte:**
1. Führe `python scripts/sync.py` aus
2. Öffne `.gemini/rules/speech-mode.md`
3. Prüfe: Inhalt entspricht `speech/submissive.md`
4. Prüfe: Rule enthält Anweisungen für devote/unterwürfige Kommunikation
5. Starte einen Agenten — prüfe ob der submissive Ton verwendet wird
6. Prüfe: Der Agent verwendet "Meister"/"Herrin"-Anrede oder ähnlich devote Formulierungen

**Erwartetes Ergebnis:**
- Speech-Mode Rule wird korrekt in das Provider-Regelverzeichnis kopiert
- Rule enthält vollständige Kommunikationsanweisungen für den submissiven Modus
- Agenten kommunizieren im gewählten Modus
- Rule wird als managed-Datei getrackt

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 10.3 Speech Modes — Opencode — Caveman Mode

**Voraussetzungen:**
- `.meta-config/project.yaml` hat `speech-mode: caveman`
- `speech/caveman.md` existiert

**Schritte:**
1. Führe `python scripts/sync.py` aus
2. Öffne `.opencode/rules/speech-mode.md` (falls vorhanden — Opencode hat kein natives Rules-Verzeichnis)
3. Prüfe: Speech-Mode wurde als Teil des Agent-Kontexts integriert
4. Prüfe: Inhalt entspricht der Höhlenmenschen-Kommunikation (kurze Sätze, einfache Worte)
5. Starte einen Agenten — prüfe ob Höhlenmenschen-Stil verwendet wird
6. Setze zurück auf `speech-mode: full` und sync

**Erwartetes Ergebnis:**
- Speech-Mode wird auf Opencode angewandt (soweit unterstützt)
- Agenten kommunizieren im Caveman-Stil
- Bei Opencode ohne natives Rules-Verzeichnis wird der Modus anderswo integriert
- Zurücksetzen auf "full" entfernt den Override

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 10.4 Speech Modes — Continue — Short Mode

**Voraussetzungen:**
- `.meta-config/project.yaml` hat `speech-mode: short`
- `speech/short.md` existiert

**Schritte:**
1. Führe `python scripts/sync.py` aus
2. Öffne `.continue/rules/speech-mode.md` (wenn Continue rules unterstützt)
3. Prüfe: Rule existiert und enthält "kurz und prägnant"-Anweisungen
4. Starte eine Interaktion — prüfe ob Antworten kurz gehalten werden
5. Prüfe: Agent gibt keine langen Erklärungen, sondern fokussierte Antworten

**Erwartetes Ergebnis:**
- Short-Mode Rule wird in das Continue-Regelverzeichnis kopiert
- Agenten antworten kurz und prägnant
- Keine überflüssigen Details
- Fokussierte, direkte Kommunikation

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

## Feature 11: Lifecycle Triggers

**Beschreibung:** Lifecycle-Triggers reagieren auf Git-Events (Release-Tag, Merge, Version-Bump).
Der `lifecycle-check` Hook (in `.claude/hooks/`) erzeugt `.opencode/pending-tasks.md` mit
ausstehenden Aufgaben. Konfigurierbar in `.meta-config/project.yaml` unter `lifecycle-triggers:`.

### 11.1 Lifecycle Triggers — Claude — PreToolUse Hook Lifecycle-Check

**Voraussetzungen:**
- `.claude/hooks/lifecycle-check.sh` existiert (von sync.py installiert)
- `.meta-config/project.yaml` hat lifecycle-triggers konfiguriert

**Schritte:**
1. Prüfe ob `lifecycle-check.sh` in `.claude/hooks/` existiert
2. Prüfe ob der Hook ausführbar ist (`chmod +x` auf Unix, oder Rechte prüfen auf Windows)
3. Öffne die Hook-Datei und lies den Code
4. Simuliere ein Git-Event (z.B. `git tag v0.54.0`)
5. Führe Claude Code aus — der Hook sollte ausgelöst werden
6. Prüfe: `.opencode/pending-tasks.md` wurde erstellt (wenn konfiguriert)

**Erwartetes Ergebnis:**
- Hook-Script existiert im richtigen Verzeichnis
- Hook ist in settings.json registriert (event: PreToolUse, matcher: Bash)
- Hook erkennt Git-Events (Tag, Merge, Version-Bump)
- `.opencode/pending-tasks.md` wird bei erkanntem Event generiert

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 11.2 Lifecycle Triggers — Gemini — on-release Task-Generierung

**Voraussetzungen:**
- lifecycle-triggers in project.yaml konfiguriert (z.B. `on-release` → se-validator)
- Ein Release-Tag wurde erstellt

**Schritte:**
1. Konfiguriere `lifecycle-triggers.on-release` in `.meta-config/project.yaml`
2. Erstelle einen Git-Tag: `git tag v0.99.0-test`
3. Führe den lifecycle-check Hook aus (oder simuliere den Event)
4. Prüfe: `.opencode/pending-tasks.md` wurde erstellt (projektweit, nicht provider-spezifisch)
5. Prüfe: Der Task für `se-validator` ist in der Datei enthalten
6. Prüfe: Task-Format: `- [ ] agent-name: "Aufgabenbeschreibung"`
7. Lösche den Test-Tag: `git tag -d v0.99.0-test`

**Erwartetes Ergebnis:**
- Pending-Tasks-Datei wird bei Release-Event erstellt
- Konfigurierte Tasks (aus lifecycle-triggers.on-release) sind enthalten
- Format: Markdown-Liste mit `- [ ] agent: "task description"`
- Datei ist gitignored (`.opencode/pending-tasks.md`)

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 11.3 Lifecycle Triggers — Opencode — pending-tasks.md Lebenszyklus

**Voraussetzungen:**
- `.opencode/pending-tasks.md` existiert mit offenen Tasks
- Ein Agent wird gestartet

**Schritte:**
1. Erstelle manuell `.opencode/pending-tasks.md` mit einem offenen Task:
   ```markdown
   - [ ] documenter: "Update CODEBASE_OVERVIEW.md for this release."
   ```
2. Starte eine neue Konversation mit einem Agenten (z.B. Orchestrator)
3. Der Agent prüft auf pending-tasks.md (laut Lifecycle-Tasks Rule)
4. Der Agent informiert: "Es gibt ausstehende Lifecycle-Tasks..."
5. Bestätige die Ausführung
6. Prüfe: Task wird an documenter delegiert
7. Prüfe: `.opencode/pending-tasks.md` wird nach Erledigung gelöscht

**Erwartetes Ergebnis:**
- Agent erkennt existierende pending-tasks.md
- Informiert den User über ausstehende Tasks
- Delegiert Tasks an die konfigurierten Agenten
- Löscht pending-tasks.md nach Erledigung

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 11.4 Lifecycle Triggers — Continue — Stale-Hook-Bereinigung

**Voraussetzungen:**
- Lifecycle-Hooks sind konfiguriert und wurden synchronisiert
- Ein Hook wird aus der Config entfernt

**Schritte:**
1. Entferne einen Hook aus `.meta-config/project.yaml` (z.B. lifecycle-check)
2. Führe `python scripts/sync.py` aus
3. Prüfe: Der entfernte Hook wird aus `.continue/hooks/` gelöscht
4. Prüfe: `dod-push-check.sh` (anderer Hook) bleibt erhalten
5. Prüfe: `.agent-meta-managed` zeigt aktualisierte Liste

**Erwartetes Ergebnis:**
- Stale Hook-Scripts werden gelöscht
- Stale settings.json-Einträge werden entfernt
- Andere Hooks bleiben unberührt
- Nur agent-meta-verwaltete Hooks werden bereinigt

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

## Feature 12: DoD Presets

**Beschreibung:** agent-meta bietet vordefinierte Definition-of-Done-Profile:
`rapid-prototyping`, `strict`, `enterprise` (Default). Jedes Preset steuert 4 Qualitätsdimensionen:
`req-traceability`, `tests-required`, `codebase-overview`, `security-audit`.
Projekte können einzelne Werte über `dod:`-Block überschreiben.

### 12.1 DoD Presets — Claude — Rapid-Prototyping Preset

**Voraussetzungen:**
- `.meta-config/project.yaml` hat `dod-preset: rapid-prototyping`
- sync.py wurde ausgeführt

**Schritte:**
1. Führe `python scripts/sync.py --dry-run` aus
2. Prüfe: Die generierten Agenten enthalten KEINE req-traceability/tests/codebase-overview Blöcke
3. Öffne einen generierten Agenten (z.B. `.claude/agents/developer.md`)
4. Prüfe: Die `{{#if DOD_REQ_TRACEABILITY}}...{{/if}}` Blöcke wurden entfernt
5. Prüfe: DoD-injizierte Variablen (DOD_REQ_TRACEABILITY, DOD_TESTS_REQUIRED, etc.) sind "false"

**Erwartetes Ergebnis:**
- Rapid-Prototyping deaktiviert alle optionalen Qualitätsdimensionen
- Agenten-Templates sind schlank — keine req-traceability/tests/codebase-overview Abschnitte
- Commit-Konventionen ohne REQ-ID
- Minimale DOD-Checkliste

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 12.2 DoD Presets — Gemini — Enterprise Preset mit REQ-Traceability

**Voraussetzungen:**
- `.meta-config/project.yaml` hat `dod-preset: enterprise`
- sync.py ausgeführt

**Schritte:**
1. Führe `python scripts/sync.py --dry-run` aus
2. Prüfe: Generierte Agenten enthalten REQ-Traceability Blöcke
3. Öffne `.gemini/agents/developer.md`
4. Prüfe: `{{#if DOD_REQ_TRACEABILITY}}` wurde zu aktivem Inhalt aufgelöst
5. Prüfe: Agent enthält "REQ-Traceability aktiv" Hinweis
6. Prüfe: `DOD_TESTS_REQUIRED`, `DOD_CODEBASE_OVERVIEW` und `DOD_SECURITY_AUDIT` sind "true"

**Erwartetes Ergebnis:**
- Enterprise Preset aktiviert alle Qualitätsdimensionen: req-traceability, tests, codebase-overview, security-audit
- `{{#if DOD_*}}...{{/if}}` Blöcke werden zu aktivem Inhalt
- Agent-Hinweise zeigen "REQ-Traceability aktiv", "Tests erforderlich" und "Security-Audit erforderlich"
- Alle 4 Dimensionen sind aktiv

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 12.3 DoD Presets — Opencode — Projekt-Override einzelner Werte

**Voraussetzungen:**
- `.meta-config/project.yaml` hat ein Preset und zusätzlich `dod: {tests-required: true}`

**Schritte:**
1. Setze `dod-preset: rapid-prototyping` und `dod: {tests-required: true}`
2. Führe `python scripts/sync.py` aus
3. Öffne `.opencode/agents/developer.md`
4. Prüfe: `DOD_TESTS_REQUIRED` ist "true" (override gewinnt)
5. Prüfe: `DOD_REQ_TRACEABILITY` ist "false" (aus rapid-prototyping)
6. Prüfe: Der Agent enthält Tests-Hinweise aber keine REQ-Traceability-Hinweise
7. Setze `dod-preset` zurück

**Erwartetes Ergebnis:**
- Precedence: dod (override) > dod-preset > full (default)
- Gemischte Konfiguration: einige Werte aus Preset, andere aus Override
- Agent-Inhalte passen exakt zu den aktiven/inaktiven DoD-Dimensionen

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 12.4 DoD Presets — Continue — Agent-spezifische DoD-Auswirkungen

**Voraussetzungen:**
- Verschiedene DoD-Presets wurden getestet
- Continue Provider aktiv

**Schritte:**
1. Setze `dod-preset: enterprise` und sync
2. Öffne `.continue/agents/developer.md` — prüfe auf DoD-Inhalte
3. Setze `dod-preset: rapid-prototyping` und sync
4. Öffne `.continue/agents/developer.md` — prüfe: DoD-Inhalte sind entfernt
5. Vergleiche die Länge der generierten Agenten in beiden Fällen
6. Prüfe: Continue-Agenten haben minimales Frontmatter, aber der Body reagiert auf DoD

**Erwartetes Ergebnis:**
- DoD-Presets beeinflussen den Inhalt der generierten Agenten-Templates
- Conditional Blocks (`{{#if DOD_*}}`) werden je nach Wert ein- oder ausgeblendet
- Enterprise Preset ⇒ längere Agenten mit mehr Qualitätsanforderungen
- Rapid-Prototyping ⇒ kürzere, schlankere Agenten

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

## Feature 13: Config-Driven Generation

**Beschreibung:** Alle Artefakte werden zentral via `config/`-Dateien definiert und
von `sync.py` generiert. Der Workflow ist: Config editieren → `sync.py` ausführen →
alle generierten Artefakte (Agents, Rules, Commands, Visualisierung) werden aktualisiert.
Kein manuelles Editieren von generierten Dateien.

### 13.1 Config-Driven Generation — Claude — Vollständiger Sync-Zyklus

**Voraussetzungen:**
- `.meta-config/project.yaml` ist vollständig konfiguriert
- Alle config/ Dateien existieren

**Schritte:**
1. Führe `python scripts/sync.py --dry-run` aus
2. Prüfe den gesamten Output: WRITE, SKIP, DELETE Aktionen
3. Zähle: Wieviele Agenten werden generiert? (sollte ≈ Anzahl der Rollen sein)
4. Prüfe: Rules werden gelistet (z.B. branch-guard.md, commit-conventions.md)
5. Prüfe: Commands werden gelistet (z.B. feedback.md, commit.md)
6. Führe `python scripts/sync.py` (ohne --dry-run) aus
7. Führe `python scripts/sync.py --dry-run` erneut aus — prüfe: nur SKIP + "unchanged"

**Erwartetes Ergebnis:**
- Erster Lauf: alle Dateien werden geschrieben (WRITE für jede generierte Datei)
- Zweiter Lauf (ohne Änderungen): nur SKIP/unchanged
- `--dry-run` zeigt exakt was passieren würde ohne etwas zu ändern
- Idempotenz: Wiederholte Ausführung ohne Config-Änderung erzeugt gleichen Zustand

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 13.2 Config-Driven Generation — Gemini — Config-Änderung → Neugenerierung

**Voraussetzungen:**
- `.meta-config/project.yaml` und sync.py funktionieren

**Schritte:**
1. Füge einen neuen Eintrag in `config/role-defaults.yaml` hinzu (dummy-rolle)
2. Füge die Rolle in `.meta-config/project.yaml` unter `roles:` ein
3. Erstelle eine minimales Template in `agents/1-generic/dummy-rolle.md`
4. Führe `python scripts/sync.py --dry-run` aus
5. Prüfe: Neue Agent-Datei für dummy-rolle wird generiert
6. Entferne die Rolle wieder aus project.yaml
7. Führe `python scripts/sync.py` aus
8. Prüfe: Die Datei wird gelöscht (stale removal)
9. Bereinige: Lösche `agents/1-generic/dummy-rolle.md`

**Erwartetes Ergebnis:**
- Neue Rolle in Config → neue Agent-Datei wird generiert
- Rolle aus Config entfernt → Agent-Datei wird als stale gelöscht
- Änderungen in role-defaults.yaml propagieren in generierte Frontmatter
- Config ist die Single-Source-of-Truth

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 13.3 Config-Driven Generation — Opencode — Variablen-Substitution

**Voraussetzungen:**
- `.meta-config/project.yaml` hat `variables:` Block mit benutzerdefinierten Variablen
- Templates verwenden `{{VAR}}` Platzhalter

**Schritte:**
1. Füge eine neue Variable hinzu: `variables: {MY_CUSTOM_VAR: "test-value"}`
2. Erstelle ein Test-Template mit `{{MY_CUSTOM_VAR}}` in einer Datei
3. Führe `python scripts/sync.py` aus
4. Öffne die generierte `.opencode/agents/` Datei — prüfe: `{{MY_CUSTOM_VAR}}` wurde ersetzt
5. Entferne die Variable aus der Config
6. Führe `python scripts/sync.py` aus
7. Prüfe: Unbekannte Variablen werden als Warnung geloggt (bleiben als `{{MY_CUSTOM_VAR}}` im Output)

**Erwartetes Ergebnis:**
- Benutzerdefinierte Variablen werden korrekt substituiert
- Fehlende Variablen erzeugen WARN im Log
- `{{%VAR%}}` Escaping verhindert Substitution (bleibt als `{{VAR}}`)
- Dot-Notation-Variablen (z.B. `platform.*`) werden separat behandelt

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 13.4 Config-Driven Generation — Continue — Stale-Removal von entfernten Rollen

**Voraussetzungen:**
- Ein Projekt mit mehreren Rollen in der Config
- Eine Rolle wird aus der Config entfernt

**Schritte:**
1. Notiere die aktuell generierten Agenten in `.continue/agents/`
2. Entferne eine Rolle aus `roles:` in `.meta-config/project.yaml` (z.B. `docker`)
3. Führe `python scripts/sync.py` aus
4. Prüfe: Die Agent-Datei für die entfernte Rolle wird gelöscht
5. Prüfe: Andere Dateien bleiben erhalten
6. Prüfe: `.agent-meta-managed` Datei wird aktualisiert
7. Füge die Rolle wieder hinzu und sync
8. Prüfe: Die Datei wird neu generiert

**Erwartetes Ergebnis:**
- Stale-Removal entfernt nur Dateien von entfernten Rollen
- `.agent-meta-managed` trackt verwaltete Dateien
- Nur agent-meta-verwaltete Dateien werden gelöscht (User-Dateien bleiben)
- Wiedereinfügen führt zu sauberer Neugenerierung

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

## Feature 14: Versioned Templates

**Beschreibung:** Jedes Agent-Template hat semantische Versionierung im YAML-Frontmatter.
`version: "MAJOR.MINOR.PATCH"` mit Bump-Regeln: Major für Breaking Changes, Minor für
neue optionale Sektionen, Patch für Textverbesserungen. Plattform-Agenten führen
zusätzlich `based-on: "1-generic/<rolle>.md@<version>"`.

### 14.1 Versioned Templates — Claude — Frontmatter-Version prüfen

**Voraussetzungen:**
- `agents/1-generic/developer.md` hat `version: "2.0.3"`
- sync.py ausgeführt

**Schritte:**
1. Öffne `agents/1-generic/developer.md`
2. Notiere die `version:` im Frontmatter
3. Führe `python scripts/sync.py` aus
4. Öffne `.claude/agents/developer.md`
5. Prüfe: Die Version aus dem Quell-Template wurde übernommen
6. Erhöhe die Version in `agents/1-generic/developer.md` auf `2.0.4`
7. Führe `python scripts/sync.py --dry-run` aus
8. Prüfe: Die generierte Datei wird aktualisiert
9. Setze die Version zurück

**Erwartetes Ergebnis:**
- Version aus Template-Frontmatter wird in generierte Datei übernommen
- Version-Bump im Template → generierte Datei wird aktualisiert (WRITE statt SKIP)
- Version dient als Change-Indikator für sync.py

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 14.2 Versioned Templates — Gemini — based-on Feld in Platform-Agenten

**Voraussetzungen:**
- `agents/2-platform/agent-meta-developer.md` existiert
- Das Template hat ein `based-on:` Feld

**Schritte:**
1. Öffne `agents/2-platform/agent-meta-developer.md`
2. Prüfe: `based-on: "1-generic/developer.md@<version>"` ist vorhanden
3. Prüfe: Die referenced Version stimmt mit der Version in `1-generic/developer.md` überein
4. Erhöhe die Version in `1-generic/developer.md`
5. Prüfe: Das `based-on` Feld im Platform-Agenten sollte aktualisiert werden (nach Sync)
6. Führe `python scripts/sync.py` aus
7. Prüfe ob `based-on` aktualisiert wurde

**Erwartetes Ergebnis:**
- Platform-Agenten referenzieren korrekt die Generic-Basis-Version
- `based-on` aktuell halten wenn die Basis-Version geändert wird
- Major-Bump in Generic → Plattform-Agenten brauchen Review
- based-on dient als Traceability zwischen Layer-Versionen

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 14.3 Versioned Templates — Opencode — Bump-Regeln validieren

**Voraussetzungen:**
- Ein Template mit bekannter Version

**Schritte:**
1. Öffne ein Template (z.B. `agents/1-generic/orchestrator.md` — `version: "3.5.0"`)
2. Analysiere was ein Major/Minor/Patch Bump bedeuten würde:
   - Patch: Textverbesserung, Klarstellung
   - Minor: Neue optionale Sektion
   - Major: Breaking Change (Umbenannte Variablen, geändertes Verhalten)
3. Führe einen Patch-Bump durch (z.B. 3.5.0 → 3.5.1) mit einer Textverbesserung
4. Führe `python scripts/sync.py --dry-run` aus
5. Prüfe: Die Version-Änderung führt zu WRITE (nicht SKIP)
6. Setze die Version zurück

**Erwartetes Ergebnis:**
- Patch-Bump bei Textänderungen
- Minor-Bump bei neuen optionalen Sektionen
- Major-Bump bei Breaking Changes
- Version-Änderung triggert Neugenerierung

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 14.4 Versioned Templates — Continue — Generierte-from Metadaten

**Voraussetzungen:**
- sync.py für Continue ausgeführt
- Generierte Agent-Dateien existieren

**Schritte:**
1. Öffne `.continue/agents/developer.md`
2. Prüfe: Kein `generated-from` Feld (wird von Continue ignoriert)
3. Prüfe: Frontmatter enthält `name:` und `description:` aber keine version-spezifischen Felder
4. Prüfe: Der generierte Agent hat ein `alwaysApply: false` Feld
5. Vergleiche mit Claude-generiertem Agent: Continue hat deutlich weniger Frontmatter

**Erwartetes Ergebnis:**
- Continue-Agenten haben minimales Frontmatter (name, description, alwaysApply)
- Keine versions-spezifischen Felder (generated-from wird entfernt)
- Body enthält den vollständigen Agent-Text (ohne Claude-spezifische Zeilen)

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

## Feature 15: AI Provider Tier Routing

**Beschreibung:** Der Orchestrator wählt automatisch das kosteneffizienteste Model-Tier
für jede Delegation. 5 Tiers: `nano` (ultra-schnell), `fast` (günstig), `balanced`
(Standard), `powerful` (Reasoning), `max` (Reserve). Mapping in `config/ai-providers.yaml`.

### 15.1 AI Provider Tier Routing — Claude — Default-Tier aus role-defaults

**Voraussetzungen:**
- `config/role-defaults.yaml` definiert `model:` pro Rolle (z.B. `developer: powerful`)
- `config/ai-providers.yaml` hat Claude-spezifisches Tier→Modell-Mapping

**Schritte:**
1. Öffne `config/role-defaults.yaml` — notiere `model:` für `developer`, `git`, `documenter`
2. Öffne `config/ai-providers.yaml` — prüfe Claude's model-tiers Mapping
3. Führe `python scripts/sync.py` aus
4. Öffne `.claude/agents/developer.md` — prüfe `model: claude-opus-4-7` (powerful)
5. Öffne `.claude/agents/git.md` — prüfe `model: claude-haiku-4-5-20251001` (fast)
6. Öffne `.claude/agents/documenter.md` — prüfe `model: claude-haiku-4-5-20251001` (fast)

**Erwartetes Ergebnis:**
- `developer` (powerful) → `claude-opus-4-7`
- `git` (fast) → `claude-haiku-4-5-20251001`
- `documenter` (fast) → `claude-haiku-4-5-20251001`
- Tier→Modell-Mapping aus ai-providers.yaml wird korrekt angewandt
- Projekt-Overrides (model-overrides) haben Vorrang

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 15.2 AI Provider Tier Routing — Gemini — Mapping-Prüfung

**Voraussetzungen:**
- `config/ai-providers.yaml` hat Gemini model-tiers Mapping

**Schritte:**
1. Öffne `config/ai-providers.yaml` — prüfe Gemini's model-tiers:
   - `nano: gemini-3.5-flash-medium`
   - `fast: gemini-3.5-flash-high`
   - `balanced: gemini-3.1-pro-low`
   - `powerful: gemini-3.1-pro-high`
2. Führe `python scripts/sync.py` aus
3. Öffne `.gemini/agents/developer.md` — prüfe Model
4. Öffne `.gemini/agents/git.md` — prüfe Model
5. Vergleiche mit Claude: gleiche Tiers, andere Modell-IDs

**Erwartetes Ergebnis:**
- Gleiche Tier-Namen (nano/fast/balanced/powerful/max) in role-defaults.yaml
- Provider-spezifische Modell-IDs in ai-providers.yaml
- Gemini verwendet `gemini-3.1-pro-high` für powerful (developer)
- Gemini verwendet `gemini-3.5-flash-high` für fast (git)
- Provider-agnostische Tiers + provider-spezifisches Mapping

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 15.3 AI Provider Tier Routing — Opencode — model-override Mechanismus

**Voraussetzungen:**
- `.meta-config/project.yaml` hat `model-overrides` Block

**Schritte:**
1. Füge in `.meta-config/project.yaml` hinzu:
   ```yaml
   model-overrides:
     Opencode:
       developer: opencode/kimi-k2.6
   ```
2. Führe `python scripts/sync.py` aus
3. Öffne `.opencode/agents/developer.md`
4. Prüfe: `model: opencode/kimi-k2.6` (override)
5. Öffne `.opencode/agents/documenter.md`
6. Prüfe: Default-Modell aus role-defaults (kein override)
7. Entferne den model-override Eintrag und sync

**Erwartetes Ergebnis:**
- model-overrides überschreiben Default-Tier-Mapping
- Nur die angegebenen Rollen sind betroffen
- Andere Rollen behalten Default-Tier
- Eintrag wird in sync.log dokumentiert ("from project override" vs "from meta default")

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 15.4 AI Provider Tier Routing — Continue — Keine Model-Tier-Unterstützung

**Voraussetzungen:**
- Continue Provider aktiv
- `config/ai-providers.yaml` hat leeres model-tiers für Continue: `{}`

**Schritte:**
1. Führe `python scripts/sync.py` aus
2. Öffne `.continue/agents/developer.md`
3. Prüfe: Kein `model:` Feld im Frontmatter
4. Öffne `.continue/agents/git.md`
5. Prüfe: Ebenfalls kein `model:` Feld
6. Prüfe: Continue verwaltet Modelle zentral in `.continue/config.yaml` (nicht per Agent)

**Erwartetes Ergebnis:**
- Continue hat keine per-Agent-Modell-Zuweisung
- Continue Frontmatter: name + description + alwaysApply: false
- Kein model: Feld in Continue-Agenten
- Modell-Verwaltung erfolgt zentral in Continue's eigener Config

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

## Feature 16: Agent Composition

**Beschreibung:** Das Composition-System erlaubt `extends:` und `patches:` im
Frontmatter von Platform/Project-Agenten. `extends: "1-generic/<rolle>.md"` lädt
die Basis. `patches:` definiert Änderungen (append-after, replace, delete, append).
Wird zur Build-Zeit von sync.py aufgelöst. Das generierte `.claude/agents/<rolle>.md`
enthält das vollständige Dokument ohne `extends:`.

### 16.1 Agent Composition — Claude — extends + patches definieren

**Voraussetzungen:**
- Ein Platform-Agent mit `extends:` und `patches:` existiert (oder wird erstellt)
- `config/platforms` enthält die passende Plattform

**Schritte:**
1. Öffne einen existierenden Platform-Agenten (z.B. `agents/2-platform/agent-meta-developer.md`)
2. Prüfe das Frontmatter auf `extends:` und `patches:` Felder
3. Führe `python scripts/sync.py --dry-run` aus
4. Prüfe: Log zeigt "composed from 1-generic/developer.md + agent-meta-developer.md"
5. Führe `python scripts/sync.py` aus
6. Öffne `.claude/agents/developer.md`
7. Prüfe: Frontmatter enthält KEIN `extends:` oder `patches:` Feld (wurde aufgelöst)
8. Prüfe: Die patched-Inhalte sind im generierten Dokument vorhanden

**Erwartetes Ergebnis:**
- Composition löst `extends:` auf: lädt Generic-Basis, wendet Patches an
- Generiertes Frontmatter hat keine composition-Metadaten mehr
- Patches (append-after, replace, etc.) sind korrekt angewandt
- Output ist ein vollständiges, eigenständiges Dokument

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 16.2 Agent Composition — Gemini — append-after Patch

**Voraussetzungen:**
- Ein Platform-Agent mit `append-after` Patch existiert

**Schritte:**
1. Erstelle einen Test-Composition-Agenten (oder verwende existierenden):
   ```yaml
   extends: "1-generic/developer.md"
   patches:
     - op: append-after
       anchor: "## Code-Konventionen"
       content: |
         ## Plattform-Konventionen
         - Verwende plattformspezifische APIs
   ```
2. Lege die Datei in `agents/2-platform/` ab (mit Plattform-Prefix)
3. Führe `python scripts/sync.py` aus
4. Öffne die generierte `.gemini/agents/developer.md`
5. Prüfe: "## Plattform-Konventionen" erscheint NACH "## Code-Konventionen"
6. Prüfe: Die originale "## Code-Konventionen" Sektion ist erhalten
7. Bereinige die Test-Datei

**Erwartetes Ergebnis:**
- `append-after` fügt Inhalt nach der angegebenen Sektion ein
- Originalsktion bleibt unverändert
- Anchor wird exakt gematcht (Section-Überschrift inkl. Level)
- Zusammengesetztes Dokument ist korrekt

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 16.3 Agent Composition — Opencode — replace + delete Patches

**Voraussetzungen:**
- Ein Composition-Test-Agent mit `replace` und `delete` Patches

**Schritte:**
1. Erstelle einen Test-Composition-Agenten:
   ```yaml
   extends: "1-generic/developer.md"
   patches:
     - op: replace
       anchor: "## Code-Konventionen"
       content: |
         ## Code-Konventionen (Replace)
         - Neue Konventionen
     - op: delete
       anchor: "## Don'ts"
   ```
2. Lege die Datei in `agents/2-platform/` ab
3. Führe `python scripts/sync.py` aus
4. Öffne `.opencode/agents/developer.md`
5. Prüfe: "## Code-Konventionen" enthält den neuen (replace) Inhalt
6. Prüfe: "## Don'ts" Sektion wurde entfernt (delete)
7. Bereinige die Test-Datei

**Erwartetes Ergebnis:**
- `replace` ersetzt die gesamte Sektion (inkl. Anchor-Zeile)
- `delete` entfernt die gesamte Sektion
- Nicht betroffene Sektionen bleiben unverändert
- Keine leeren Stellen oder Formatierungsfehler nach delete

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

### 16.4 Agent Composition — Continue — append-Patch (Dateiende)

**Voraussetzungen:**
- Ein Composition-Test-Agent mit `append` Patch (Dateiende)

**Schritte:**
1. Erstelle einen Test-Composition-Agenten:
   ```yaml
   extends: "1-generic/developer.md"
   patches:
     - op: append
       content: |
         ## Anhang
         - Zusätzliche Informationen
   ```
2. Lege die Datei in `agents/2-platform/` ab
3. Führe `python scripts/sync.py` aus
4. Öffne `.continue/agents/developer.md`
5. Prüfe: "## Anhang" erscheint am Ende der Datei
6. Prüfe: Der Agent ist vollständig (Basis + append)
7. Bereinige die Test-Datei

**Erwartetes Ergebnis:**
- `append` hängt Inhalt ans Dateiende an
- Keine Seiteneffekte auf andere Sektionen
- Gesamtes Dokument ist valide
- Continue-Frontmatter (minimal) bleibt korrekt

**Tatsächliches Ergebnis:**
- _(Platzhalter für Tester)_

**Status:** ☐ PASS / ☐ FAIL / ☐ BLOCKED

**Bemerkungen:**
- _(Platzhalter für Tester)_

---

## Claude-Szenarien

Alle Claude-Szenarien befinden sich in den Abschnitten oben (1.1, 2.1, 3.1, ..., 16.1).

| # | Feature | Szenario |
|---|---------|----------|
| 1.1 | Multi-Provider Support | Provider-spezifische Agent-Generierung |
| 2.1 | Layer Architecture | Generic-Basis-Template |
| 3.1 | Orchestrator-First | FANOUT Parallel-Dispatch mit background |
| 4.1 | Systems Engineering Cascade | L1 Blackbox → Whitebox Zerlegung |
| 5.1 | Agent Visualization | Statische Mindmap-Generierung |
| 6.1 | MCP Server Management | Registry → Rule-Generierung |
| 7.1 | Provider Isolation | permissions.deny in settings.json |
| 8.1 | Extension System | Extension-Erstellung mit --create-ext |
| 9.1 | External Skills | Skill-Aktivierung und Wrapper-Generierung |
| 10.1 | Speech Modes | Standard Modus (full) |
| 11.1 | Lifecycle Triggers | PreToolUse Hook Lifecycle-Check |
| 12.1 | DoD Presets | Rapid-Prototyping Preset |
| 13.1 | Config-Driven Generation | Vollständiger Sync-Zyklus |
| 14.1 | Versioned Templates | Frontmatter-Version prüfen |
| 15.1 | AI Provider Tier Routing | Default-Tier aus role-defaults |
| 16.1 | Agent Composition | extends + patches definieren |

## Gemini-Szenarien

Alle Gemini-Szenarien befinden sich in den Abschnitten oben (1.2, 2.2, 3.2, ..., 16.2).

| # | Feature | Szenario |
|---|---------|----------|
| 1.2 | Multi-Provider Support | Provider-spezifische Agent-Generierung |
| 2.2 | Layer Architecture | Platform-Override (2-platform) |
| 3.2 | Orchestrator-First | FANOUT mit nativem planning_mode |
| 4.2 | Systems Engineering Cascade | Fraktale Zellteilung |
| 5.2 | Agent Visualization | Dynamic Session-Tracking |
| 6.2 | MCP Server Management | Secrets-Scanning und .gitignore |
| 7.2 | Provider Isolation | TOML-Policy-Datei |
| 8.2 | Extension System | --update-ext Managed Block |
| 9.2 | External Skills | Pinned Commit Check |
| 10.2 | Speech Modes | Submissive Modus |
| 11.2 | Lifecycle Triggers | on-release Task-Generierung |
| 12.2 | DoD Presets | Enterprise Preset mit REQ-Traceability |
| 13.2 | Config-Driven Generation | Config-Änderung → Neugenerierung |
| 14.2 | Versioned Templates | based-on Feld in Platform-Agenten |
| 15.2 | AI Provider Tier Routing | Mapping-Prüfung |
| 16.2 | Agent Composition | append-after Patch |

## Opencode-Szenarien

Alle Opencode-Szenarien befinden sich in den Abschnitten oben (1.3, 2.3, 3.3, ..., 16.3).

| # | Feature | Szenario |
|---|---------|----------|
| 1.3 | Multi-Provider Support | Provider-spezifische Agent-Generierung |
| 2.3 | Layer Architecture | Layer-Priorität (External gewinnt) |
| 3.3 | Orchestrator-First | PARALLEL_GROUP mit task() |
| 4.3 | Systems Engineering Cascade | L3 Terminierung |
| 5.3 | Agent Visualization | Live-Dashboard |
| 6.3 | MCP Server Management | Config-Generierung |
| 7.3 | Provider Isolation | permission.read/edit in opencode.json |
| 8.3 | Extension System | Extension-Hook im generierten Agenten |
| 9.3 | External Skills | Zwei-Gate Approval-System |
| 10.3 | Speech Modes | Caveman Mode |
| 11.3 | Lifecycle Triggers | pending-tasks.md Lebenszyklus |
| 12.3 | DoD Presets | Projekt-Override einzelner Werte |
| 13.3 | Config-Driven Generation | Variablen-Substitution |
| 14.3 | Versioned Templates | Bump-Regeln validieren |
| 15.3 | AI Provider Tier Routing | model-override Mechanismus |
| 16.3 | Agent Composition | replace + delete Patches |

## Continue-Szenarien

Alle Continue-Szenarien befinden sich in den Abschnitten oben (1.4, 2.4, 3.4, ..., 16.4).

| # | Feature | Szenario |
|---|---------|----------|
| 1.4 | Multi-Provider Support | Provider-spezifische Agent-Generierung |
| 2.4 | Layer Architecture | 3-project Extension Override |
| 3.4 | Orchestrator-First | Sequentielle Fallback-Ausführung |
| 4.4 | Systems Engineering Cascade | Validierung & Verifikation |
| 5.4 | Agent Visualization | Event-Log Retention |
| 6.4 | MCP Server Management | YAML-Config-Integration |
| 7.4 | Provider Isolation | Soft-Guidance (kein Hard-Block) |
| 8.4 | Extension System | Extension-Inhalte werden geladen |
| 9.4 | External Skills | Stale Skill-Bereinigung |
| 10.4 | Speech Modes | Short Mode |
| 11.4 | Lifecycle Triggers | Stale-Hook-Bereinigung |
| 12.4 | DoD Presets | Agent-spezifische DoD-Auswirkungen |
| 13.4 | Config-Driven Generation | Stale-Removal von entfernten Rollen |
| 14.4 | Versioned Templates | Generierte-from Metadaten |
| 15.4 | AI Provider Tier Routing | Keine Model-Tier-Unterstützung |
| 16.4 | Agent Composition | append-Patch (Dateiende) |

---

## Test-Matrix

| Feature | Claude | Gemini | Opencode | Continue |
|---------|--------|--------|----------|----------|
| 1. Multi-Provider Support | 1.1 | 1.2 | 1.3 | 1.4 |
| 2. Layer Architecture | 2.1 | 2.2 | 2.3 | 2.4 |
| 3. Orchestrator-First | 3.1 | 3.2 | 3.3 | 3.4 |
| 4. Systems Engineering Cascade | 4.1 | 4.2 | 4.3 | 4.4 |
| 5. Agent Visualization | 5.1 | 5.2 | 5.3 | 5.4 |
| 6. MCP Server Management | 6.1 | 6.2 | 6.3 | 6.4 |
| 7. Provider Isolation | 7.1 | 7.2 | 7.3 | 7.4 |
| 8. Extension System | 8.1 | 8.2 | 8.3 | 8.4 |
| 9. External Skills | 9.1 | 9.2 | 9.3 | 9.4 |
| 10. Speech Modes | 10.1 | 10.2 | 10.3 | 10.4 |
| 11. Lifecycle Triggers | 11.1 | 11.2 | 11.3 | 11.4 |
| 12. DoD Presets | 12.1 | 12.2 | 12.3 | 12.4 |
| 13. Config-Driven Generation | 13.1 | 13.2 | 13.3 | 13.4 |
| 14. Versioned Templates | 14.1 | 14.2 | 14.3 | 14.4 |
| 15. AI Provider Tier Routing | 15.1 | 15.2 | 15.3 | 15.4 |
| 16. Agent Composition | 16.1 | 16.2 | 16.3 | 16.4 |

---

## Änderungshistorie

| Datum | Version | Änderung |
|-------|---------|----------|
| 2026-05-24 | 1.0.0 | Initiale Erstellung aller 64 Szenarien (16 Features × 4 Provider) |

---

*Generiert von agent-meta v0.53.0 — nicht manuell bearbeiten.*
