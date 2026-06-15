# Audit: Orchestration Syntax Leaks (Issue #277)

**Branch:** `feat/framework-issues-batch-2`
**Datum:** 2026-06-15
**Scope:** `agents/1-generic/`, `agents/2-platform/`, `.claude/agents/`

---

## Zusammenfassung

Das PAL-Placeholder-System (`{{PAL_DELEGATE}}`, `{{PAL_FANOUT}}` etc.) funktioniert korrekt.
Die Template-Ebene (`agents/1-generic/`) ist sauber — keine hardcodierten Provider-Dispatch-Syntaxen
außerhalb der PAL-Platzhalter. Die generierten Agenten in `.claude/agents/` enthalten korrekt
die Claude-spezifischen Expansion dieser Platzhalter.

---

## 1. Syntax-Leak-Scan

### 1.1 `{{agent}}`/`{{task}}` Placeholders

```
grep -rn "{{agent}}\|{{task}}" .claude/agents/ agents/
```

**Ergebnis:** Keine Treffer. Diese Placeholder-Varianten existieren nicht im Codebase.

### 1.2 `{{PAL_DELEGATE}}` und verwandte PAL-Placeholder

**Treffer in `agents/1-generic/orchestrator.md`:**

| Zeile | Placeholder |
|-------|-------------|
| 353 | `{{PAL_DELEGATE}}` |
| 354 | `{{PAL_FANOUT}}` |
| 355 | `{{PAL_PARALLEL_GROUP}}` |
| 357 | `{{PAL_HANDOFF}}` (nur wenn `A2A_PROTOCOL_ENABLED`) |
| 363 | `{{PAL_PARALLEL_PATTERN}}` |
| 553 | `{{PAL_FALLBACK}}` |

**Bewertung:** Korrekt. Diese sind Platzhalter im Template, keine Leaks. `sync.py` substituiert
sie provider-spezifisch aus `config/delegation-syntax.yaml`.

### 1.3 Provider-spezifische Dispatch-Syntax in `1-generic/`

```
grep -rn "Agent(subagent_type\|task(subagent_type\|define_subagent" agents/1-generic/
```

**Ergebnis:** Keine Treffer. Kein Hardcoding von Claude/Opencode/Gemini-Syntax in den Templates.

### 1.4 `@agent`-Mentions in generierten Agenten

```
grep -rn "@agent\|Agent(subagent" .claude/agents/
```

**Treffer in `.claude/agents/orchestrator.md`** (generiert für Claude-Plattform):

| Zeile | Inhalt |
|-------|--------|
| 309 | `Agent(subagent_type="<ziel-agent>", ...)` — aus `{{PAL_DELEGATE}}` expandiert |
| 312–313 | FANOUT-Beispiele — aus `{{PAL_FANOUT}}` expandiert |
| 318–319 | PARALLEL_GROUP-Beispiele — aus `{{PAL_PARALLEL_GROUP}}` expandiert |
| 336, 338, 340 | Parallel-Pattern-Beispiele — aus `{{PAL_PARALLEL_PATTERN}}` expandiert |
| 500 | Fallback-Syntax — aus `{{PAL_FALLBACK}}` expandiert |

**Bewertung:** Korrekt. Dies ist erwartetes Verhalten — generierte Claude-Agenten enthalten
Claude-spezifische Syntax, weil die Expansion korrekt aus `delegation-syntax.yaml` erfolgt.

### 1.5 Provider-Namen in `1-generic/`

Zwei grenzwertige Treffer:

| Datei | Zeile | Inhalt | Bewertung |
|-------|-------|--------|-----------|
| `agents/1-generic/agent-meta-scout.md` | 28 | `Claude-Code-spezifische Sicherheits-Checkliste` | **Grenzfall:** Scout-Agent ist agent-meta-spezifisch, nicht generisch — inhaltlich vertretbar, da er Claude Code evaluiert |
| `agents/1-generic/meta-feedback.md` | 146 | `Was darf Claude auf dieser Plattform nicht` | **Grenzfall:** Template-Text als Platzhalter-Beispiel, nicht als Laufzeit-Instruktion |

### 1.6 Provider-spezifische Pfade in `1-generic/`

Treffer mit `.claude/`-Pfaden in mehreren Templates:

| Datei | Inhalt |
|-------|--------|
| `developer.md:129` | Verweis auf `Rule .claude/rules/commit-conventions.md` |
| `validator.md:77` | Verweis auf `Rule .claude/rules/dod-criteria.md` |
| `orchestrator.md:393,397` | Artefakt-Pfade `.claude/artifacts/` |
| `agent-meta-manager.md:47,245` | Verweis auf `.claude/agents/` |
| `_wf-sync-interface.md:28-32` | Workflow-Doku mit `.claude/`-Pfaden |
| `_wf-claude-review.md:41,59` | Workflow mit `.claude/rules/` Pfaden |
| `openscad-developer.md:207-210` | Skill-Pfade `.claude/skills/` |

**Bewertung:** Die `_wf-*` Workflow-Dateien sind Claude-Code-spezifische Hilfstexte (Bootstrap-
Dokumentation), kein generisches Template-Content. `agent-meta-manager.md` referenziert `.claude/`
korrekt, da es ein agent-meta-internes Tool ist. `orchestrator.md` verwendet `.claude/artifacts/`
als Artifact-Store — dies ist ein echter **Provider-Leak**, da diese Pfade für Gemini/Continue/Copilot
falsch wären (sie haben andere Konventionen).

---

## 2. Gemini-Bypass-Analyse

### 2.1 Gemini-spezifische Overrides

**In `agents/2-platform/`:** Nur `agent-meta-gemini-expert.md` — kein Gemini-Orchestrator-Override.

**In `rules/2-platform/`:** `gemini-orchestrator-first.md` definiert die SE-Kaskaden-Regel für
Gemini via `run-cascade.py`. Diese Rule existiert aber als neue Datei (untracked im Branch) und
wurde noch nicht in ein Gemini-Orchestrator-Template eingebettet.

### 2.2 Bootstrap-Problem

Laut `config/provider-capabilities.yaml`:
- Gemini: `file_based_agents: false`, `bootstrap_required: true`
- Agenten müssen per `define_subagent()` bei JEDER Session registriert werden
- `.gemini/agents/*.md` werden NICHT automatisch geladen

Laut `config/delegation-syntax.yaml` → Gemini `bootstrap`:
```
bootstrap: "api-define_subagent"
bootstrap_sequence:
  - type: "api_call"
    template: 'define_subagent(name="<name>", description="<description>", system_prompt="<prompt>")'
```

**Befund:** Es existiert kein generiertes Bootstrap-Skript, das `define_subagent()` bei Session-Start
aufruft. Die `bootstrap_sequence` in der Konfiguration wird in `scripts/lib/agents.py` nicht umgesetzt.
Dies ist ein potentieller Gemini-Bypass: Agenten werden generiert, aber nicht automatisch registriert.

### 2.3 Fallback-Verhalten auf Gemini

Gemini-Fallback in `delegation-syntax.yaml`:
```yaml
fallback: "Bearbeite folgende Aufgabe selbst, mit höchster Sorgfalt: <task>"
```

Dies bedeutet: Wenn kein Tool-Call möglich ist, führt Gemini Aufgaben direkt im Haupt-Kontext aus —
ohne Orchestrator-Kontrolle. Für SE-Kaskaden ist dies durch `gemini-orchestrator-first.md` adressiert,
aber die Rule ist noch nicht in den generierten Gemini-Orchestrator-Agent eingebettet.

---

## 3. Fix-Empfehlungen

### Priorität HOCH

| # | Problem | Empfehlung |
|---|---------|------------|
| 1 | `orchestrator.md` verwendet `.claude/artifacts/` als Artifact-Store (Zeilen 393, 397) | Placeholder `{{ARTIFACT_DIR}}` einführen — provider-spezifisch durch `config/delegation-syntax.yaml` substituieren |
| 2 | Gemini-Bootstrap-Sequenz nicht implementiert | In `scripts/lib/agents.py` oder separatem `bootstrap.py` `bootstrap_sequence` aus `delegation-syntax.yaml` umsetzen |

### Priorität MITTEL

| # | Problem | Empfehlung |
|---|---------|------------|
| 3 | `gemini-orchestrator-first.md` Rule nicht in Gemini-Orchestrator eingebettet | Gemini-Orchestrator-Override in `agents/2-platform/` erstellen (analog zu anderen Plattform-Overrides) |
| 4 | `agent-meta-scout.md:28` — `Claude-Code-spezifische Sicherheits-Checkliste` | Formulierung abstrahieren: "Plattform-spezifische Sicherheits-Checkliste" |

### Priorität NIEDRIG

| # | Problem | Empfehlung |
|---|---------|------------|
| 5 | `meta-feedback.md:146` — "Was darf Claude..." | Formulierung abstrahieren: "Was darf der Agent auf dieser Plattform nicht..." |

---

## Fazit

Das PAL-Placeholder-System ist strukturell korrekt implementiert. Die Templates in `1-generic/`
sind weitgehend provider-agnostisch — die gefundenen Provider-Nennungen sind grenzwertig, aber
inhaltlich erklärbar. Der kritischste Befund ist der hardcodierte `.claude/artifacts/`-Pfad im
Orchestrator-Template sowie das fehlende Gemini-Bootstrap-Implementierung.
