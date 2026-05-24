# Manuelles Test-Konzept — Generisches Delegations-Testverfahren

> **Branch:** feat/agent-framework-extensions
> **Ansatz:** Generisches Black-Box-Testverfahren für beliebige User-Intents
> **Viz-Config:** `.meta-config/project.yaml` → `viz.enabled: true`

---

## Ordnerstruktur

```
tests/manual/
├── run-manual-test.py          ← Zentraler Einstiegspunkt
├── test-engine/
│   ├── prepare-test-session.py  ← Session vorbereiten, Prompt anzeigen
│   ├── validate-delegation.py   ← Echte Viz-Logs validieren
│   └── manual-scenarios.json    ← Szenario-Definitionen
├── test-concept/
│   └── manual-test-concept.md   ← Diese Datei
├── scenarios/
│   ├── se/                      ← SE-Test-Szenarien (5 Stück)
│   └── meta-agent/              ← Meta-Agent-Funktions-Tests (5 Stück)
└── results/                     ← Test-Ergebnisse, Reports

docs/bugs/                        ← Auto-generierte Bug-Reports (bei FAIL)
```

---

## Commands

### Überblick

| Command | Beschreibung |
|---------|-------------|
| `run-manual-test.py prepare` | Session vorbereiten, Prompt anzeigen |
| `run-manual-test.py validate` | Viz-Log validieren |
| `run-manual-test.py list` | Alle Szenarien auflisten |
| `run-manual-test.py clean` | Artefakte löschen |

---

### 1. Vorbereitung

```bash
# Einzelnes Szenario vorbereiten
python tests/manual/run-manual-test.py prepare --scenario SE-01

# Mit Viz-Log leeren (sauberer Start)
python tests/manual/run-manual-test.py prepare --scenario SE-01 --clear-log

# Dry-Run (keine echten Git-/Release-Operationen)
python tests/manual/run-manual-test.py prepare --scenario FW-06 --dry-run --clear-log

# Im Ziel-Repository
python tests/manual/run-manual-test.py prepare --scenario FW-02 \
    --target-repo /pfad/zu/projekt --clear-log
```

**Ausgabe:** Zeigt den User-Prompt und die erwartete Delegationskette.

---

### 2. Validierung

```bash
# Einzelnes Szenario validieren
python tests/manual/run-manual-test.py validate --scenario SE-01

# Alle Szenarien validieren (liest aktuelles Viz-Log)
python tests/manual/run-manual-test.py validate --all

# Mit Report
python tests/manual/run-manual-test.py validate --all --report

# Mit Auto-Bug-Report bei FAIL
python tests/manual/run-manual-test.py validate --scenario SE-01 --auto-report-fail

# Im Ziel-Repository
python tests/manual/run-manual-test.py validate --scenario FW-02 \
    --target-repo /pfad/zu/meinem-projekt --auto-report-fail
```

**Ausgabe:** Zeigt PASS/FAIL pro Check, delegations Report.

---

### 3. Listen

```bash
python tests/manual/run-manual-test.py list
```

**Ausgabe:** Alle 15 Szenarien gruppiert nach SE und meta-agent.

---

### 4. Aufräumen

```bash
python tests/manual/run-manual-test.py clean
```

**Effekt:** Löscht alle Bug-Reports (`docs/bugs/`) und Ergebnis-Dateien (`tests/manual/results/`).

---

## Kompletter Test-Workflow

### In agent-meta selbst

```bash
# 1. Vorbereiten
python tests/manual/run-manual-test.py prepare --scenario SE-01 --clear-log

# 2. Prompt in Chat eingeben (manuell!)
#    "Starte den SE-Prozess für einen Smart-Light IoT Controller..."

# 3. Auf Abschluss warten

# 4. Validieren + Report
python tests/manual/run-manual-test.py validate --scenario SE-01 --report

# 5. Optional: Bei FAIL Bug-Report generieren
python tests/manual/run-manual-test.py validate --scenario SE-01 --auto-report-fail
```

### In einem Ziel-Projekt (agent-meta als Submodul)

```bash
cd mein-projekt

# 1. Vorbereiten
python .agent-meta/tests/manual/run-manual-test.py prepare \
    --scenario FW-02 --target-repo . --clear-log

# 2. Prompt in Chat eingeben
#    "Fix Bugs #42, #57 und #89..."

# 3. Validieren mit Auto-Bug-Report
python .agent-meta/tests/manual/run-manual-test.py validate \
    --scenario FW-02 --target-repo . --auto-report-fail

# 4. Bug-Report prüfen
ls docs/bugs/
```

---

## Grundprinzip

```
INPUT (User-Prompt) → DELEGATION (Orchestrator + Agenten) → LOG (Viz-Events)
→ VALIDIERUNG (Delegations-Muster gegen Routing-Tabelle)
```

Der Tester gibt einen beliebigen Prompt ein. Das System entscheidet selbstständig,
wer zuständig ist. Nachher wird nur geprüft: **Wurde der richtige Agent gewählt?**

### Warum manuell?

- Die echten Agenten-Templates enthalten komplexe Logik (DoD-Prüfungen, Extensions,
  Sprachregeln, JSON-Contract-Handover), die nicht simulierbar sind.
- Der Orchestrator entscheidet dynamisch über Model-Tiers und Parallelisierung.
- Nur ein **echter** Durchlauf zeigt, ob die Routing-Tabelle korrekt in
  Delegations-Events übersetzt wird.

---

## Test-Szenarien

### Gruppe A: Systems Engineering (5 Szenarien)

| ID | Name | Prompt | Erwartete erste Delegation |
|----|------|--------|---------------------------|
| **SE-01** | Vollständige SE-Kaskade | "Starte den SE-Prozess für einen Smart-Light IoT Controller..." | `orchestrator → se-orchestrator` |
| **SE-02** | V&V Rechter Flügel | "Führe Verifikation und Validierung für das Smart-Light System durch" | `orchestrator → se-integration-and-test-manager` |
| **SE-03** | Trade-Study mit ADR-Export | "Führe eine Trade-Study für die Kommunikationshardware durch..." | `orchestrator → se-orchestrator` |
| **SE-04** | Rekursive Dekomposition L1→L3 | "Dekomponiere die Sensorik-Einheit des Smart-Light bis auf Komponentenebene (L3)" | `orchestrator → se-orchestrator` |
| **SE-05** | Stakeholder-Validierung (L1) | "Validiere das fertige Smart-Light System gegen die ursprünglichen Stakeholder-Anforderungen" | `orchestrator → se-validator` |

### Gruppe B: Meta-Agent-Funktionen (10 Szenarien)

> Insgesamt 15 Szenarien: 5 SE + 10 Meta-Agent

| ID | Name | Prompt | Erwartete erste Delegation |
|----|------|--------|---------------------------|
| **FW-01** | Feature-Lifecycle mit TDD | "Füge eine Benutzer-Registrierung mit E-Mail-Verifikation hinzu" | `orchestrator → feature` |
| **FW-02** | Multi-Fix FANOUT | "Fix Bugs #42, #57 und #89 — alle in verschiedenen Modulen" | `orchestrator → developer` (FANOUT ×3) |
| **FW-03** | Multi-Intent Parallel | "Erstelle ein Dashboard-UI, eine CI/CD-Pipeline dafür, und optimiere die Ladezeit" | `orchestrator → [ui-ux-designer ∥ devops-engineer ∥ performance-optimizer]` |
| **FW-04** | API-Design Contract-First | "Definiere eine REST-API: Geräteverwaltung, Sensor-Daten, Konfiguration" | `orchestrator → api-specialist` |
| **FW-05** | Log-Analyse → Issue | "Analysiere die Error-Logs der letzten 24 Stunden und erstelle Issues für kritische Fehler" | `orchestrator → log-analyzer` |
| **FW-06** | Release erstellen | "Erstelle Release v1.2.0 mit Changelog und GitHub Release" | `orchestrator → release` |
| **FW-07** | Dokumentation eines neuen Features | "Dokumentiere das neue Login-Feature: Update README, Architektur-Doku..." | `orchestrator → documenter` |
| **FW-08** | Meta-Fragen zu agent-meta Setup | "Wie führe ich sync.py aus und wie funktioniert die Agenten-Erweiterung?" | `orchestrator → agent-meta-manager` |
| **FW-09** | Security-Audit | "Führe ein Security-Audit durch: Prüfe auf OWASP-Top-10, Secrets..." | `orchestrator → security-auditor` |
| **FW-10** | Ideation zu Requirements | "Ich habe eine Idee: Ein Dashboard, das alle Agenten-Aktivitäten in Echtzeit anzeigt. Formalisiere das als Requirements." | `orchestrator → ideation` |

---

## Teil 3: Dry-Run Testing (Sicherheitsmodus)

### Warum Dry-Run?

Manuelle Tests mit Befehlen wie "Release erstellen", "Git Commit", "GitHub Issue erstellen"
können **echte Seiteneffekte** auslösen. Der `--dry-run` Modus verhindert das:

- **Kein echter Git-Push**
- **Kein echter GitHub Release**
- **Kein echtes Issue erstellen**
- **Keine echten Deployments**

### Aktivierung

```bash
# Dry-Run beim Vorbereiten
python tests/manual/run-manual-test.py prepare --scenario FW-06 --dry-run --clear-log
```

**Effekt:** Der angezeigte Prompt enthält automatisch:
```
"Erstelle Release v1.2.0 mit Changelog und GitHub Release
 (dry-run: keine echten Git-Ops, kein Push, kein Release)"
```

### Welche Szenarien brauchen Dry-Run?

| Szenario | Grund für Dry-Run |
|----------|-------------------|
| **FW-06** (Release) | Verhindert echten Version-Bump und GitHub Release |
| **FW-07** (Doku) | Verhindert ungewollte Commits auf main |
| **FW-08** (Meta-Fragen) | Reine Informationsabfrage — kein Dry-Run nötig |
| **FW-09** (Security-Audit) | Nur Read-Operationen — kein Dry-Run nötig |
| **FW-10** (Ideation) | Nur REQUIREMENTS.md — ggf. Dry-Run empfohlen |
| **FW-01** (Feature) | Feature-Lifecycle kann Branches erstellen — Dry-Run empfohlen |
| **FW-02** (Bugfix) | Bugfix erstellt Commits — Dry-Run empfohlen |

### Szenario-spezifische Dry-Run-Regeln

Jedes Szenario definiert in seiner JSON-Datei unter `dry_run_notes`,
was im Dry-Run verhindert wird:

```json
{
  "dry_run_notes": [
    "Nur Version-Dateien und Changelog aktualisieren",
    "KEIN git push oder GitHub Release erstellen",
    "KEIN echter Tag anlegen"
  ]
}
```

### Empfohlener Workflow

```bash
# 1. Immer mit --dry-run vorbereiten, wenn unsicher
python tests/manual/run-manual-test.py prepare --scenario FW-06 --dry-run --clear-log

# 2. Prompt kopieren und ENTER drücken

# 3. Validieren
python tests/manual/run-manual-test.py validate --scenario FW-06 --report
```

---

## Automatische Bug-Meldung bei FAIL

### Aktivierung

```bash
python tests/manual/run-manual-test.py validate --scenario SE-01 --auto-report-fail
```

Bei FAIL wird generiert:
- `docs/bugs/bug-SE-01-Opencode-20260524-143052.md`

### Bug-Report-Inhalt

- **User-Prompt** (der getestete Input)
- **Expected Routing** (was laut Routing-Tabelle erwartet wurde)
- **Actual Delegations** (was tatsächlich im Viz-Log steht)
- **Failed Checks** (detaillierte Diffs: Expected vs. Actual)
- **Provider** (Opencode / Gemini / Claude / Continue)
- **Repository** (agent-meta oder Ziel-Projekt)
- **Next Steps** (zur Fehlerbehebung)

### Einreichung als GitHub Issue

```bash
# Option A: Manuelles Erstellen
# Kopiere den Bug-Report in ein neues GitHub Issue

# Option B: Via feedback Agent (wenn im Projekt verfügbar)
python scripts/feedback.py --bug docs/bugs/bug-SE-01-*.md
```

---

## Tests in Ziel-Repositories ausführen

### Anwendungsfall

agent-meta wird als Git-Submodul in Projekte eingebunden. Wenn im Ziel-Projekt
Probleme auftreten (z.B. falsche Delegationen), können die Tests direkt dort
ausgeführt werden.

### Voraussetzungen im Ziel-Repo

```
mein-projekt/
  .agent-meta/           ← Submodul
    tests/manual/
      test-engine/
  .meta-viz/
    events.jsonl          ← Viz-Log des Ziel-Projekts
  .meta-config/
    project.yaml          ← Projekt-Konfiguration
```

### Ausführung im Ziel-Repo

```bash
cd mein-projekt

# 1. Vorbereiten
python .agent-meta/tests/manual/run-manual-test.py prepare \
    --scenario FW-02 --target-repo . --clear-log

# 2. Prompt in Chat eingeben

# 3. Validieren + Auto-Bug-Report
python .agent-meta/tests/manual/run-manual-test.py validate \
    --scenario FW-02 --target-repo . --auto-report-fail
```

---

## Provider-Dokumentation

### Warum Provider-Dokumentation wichtig ist

Verschiedene Provider haben unterschiedliche Fähigkeiten:

| Provider | Parallelisierung | FANOUT | Model-Tiers | Besonderheiten |
|----------|-----------------|--------|-------------|----------------|
| **Opencode** | ✅ task() parallel | ✅ | ✅ | BARRIER automatisch |
| **Gemini** | ✅ Auto-parallel | ✅ | ✅ | Native Planung |
| **Claude** | ✅ Background tasks | ✅ | ✅ | Subagent-API |
| **Continue** | ❌ Sequentiell | ❌ | ⚠️ Fallback | Keine native Parallelisierung |

**Ein Test kann auf Opencode PASS und auf Continue FAIL** — weil Continue
keine FANOUT-Parallelisierung unterstützt.

### Provider-Erfassung

Der Validator liest den Provider automatisch aus den Viz-Logs:

```json
{"event": "agent_start", "agent": "developer", "provider": "Opencode", "model": "balanced"}
```

Jeder Report enthält daher:
- **Provider:** Opencode / Gemini / Claude / Continue
- **Repository:** agent-meta oder Ziel-Projekt

---

## Ergebnis-Dokumentation

### Protokoll-Template

```markdown
## Test-Session: [ID] — [Datum]

**Prompt:** "..."
**Provider:** Opencode / Gemini / Claude / Continue
**Repository:** agent-meta / my-project
**Erster Agent:** orchestrator → [Tatsächlich]
**Erwartet:** [Laut Routing-Tabelle]

### Delegationskette (aus Viz-Log)
| # | Von | Zu | Zeit | Status |
|---|-----|-----|------|--------|
| 1 | orchestrator | ... | ... | ... |

### Abweichungen
- *(keine / Liste)*

### Gesamt
**Status:** PASS / FAIL
**Begründung:** ...
```

### Gesamt-Report

```bash
python tests/manual/run-manual-test.py validate --all --report
```

Erzeugt: `tests/manual/results/` (oder `tests/manual/test-engine/delegation-report.md`)
