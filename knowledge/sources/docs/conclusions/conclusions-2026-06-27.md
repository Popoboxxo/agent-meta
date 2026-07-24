# Erkenntnisse — 27. Juni 2026

## Session-Zusammenfassung

Feature-Implementierung "A2A Anti-Re-Delegation Gates" auf Branch `feat/a2a-anti-re-delegation`. Zwei Defekte aus einem Ziel-Repo gefixt: (1) Spec-Dump im Handoff — `payload.t` enthielt volle Implementierungs-Spec statt kurzer Task-Beschreibung, (2) Fehlende Re-Delegation-Sperre — `source_agent == target_agent` wurde nicht geprüft, ermöglichte `main → orchestrator → orchestrator → orchestrator`-Ketten. Implementiert in 2 Commits: Hard-Reject-Logik (Self-Handoff + Tiefenlimit + T-Size-Limit + Re-Delegation-Detection) in den Orchestrator- und Validator-Agenten, plus Konfigurierbarkeit des Tiefenlimits via `project.yaml`.

---

## 1. Was wurde implementiert

### Commit 1: `c41e78d` — `feat: add A2A anti-re-delegation gates`

| Datei | Änderung |
|-------|----------|
| `schemas/a2a-handoff.schema.json` | Neues Pflichtfeld `delegation_depth` (int, 0..2 → später auf 50 erweitert), `source_agent ≠ target_agent`-Doku im Schema-Description |
| `agents/1-generic/orchestrator.md` | v4.5.0 → v5.0.0 (Major). Anti-Recursion-Section komplett neu geschrieben: Hard-Reject-Tabelle mit Self-Handoff-Verbot, Tiefenlimit, T-Size-Limit, Re-Delegation-Detection |
| `agents/1-generic/validator.md` | v3.3.1 → v4.0.0 (Major). Topological Hard Rejects: selbe Gates als Validator-Checklist |
| `scripts/lib/delegation_syntax.py` | Tier-1.5 Topological Validation: `validate_envelope()` prüft `source_agent ≠ target_agent` + `delegation_depth` Range |
| `rules/1-generic/a2a-delegation-gates.md` | **NEU** — provider-agnostische Rule mit Hard-Reject-Tabelle, Werten, Verhaltensmatrix, Propagations-Hinweis |
| `AGENTS.md` (managed block) | Neue Sektion »A2A Anti-Re-Delegation Gates« mit Regeln, Werten und Verhaltensmatrix |
| `CLAUDE.md` (managed block) | Gleiche Sektion wie AGENTS.md |
| `.opencode/agents/orchestrator.md` | Via Sync generiert: Hard-Reject-Sektion in generierter Datei |
| `.claude/agents/orchestrator.md` | Via Sync generiert: Hard-Reject-Sektion in generierter Datei |
| `.opencode/agents/validator.md` | Via Sync generiert: Topological Hard Rejects |
| `.claude/agents/validator.md` | Via Sync generiert: Topological Hard Rejects |

### Commit 2: `b3731a6` — `feat(a2a): make delegation depth configurable via project.yaml`

| Datei | Änderung |
|-------|----------|
| `schemas/a2a-handoff.schema.json` | `maximum` von 2 auf 50 erweitert (Schema-Bereich, nicht konfiguriertes Limit) |
| `agents/1-generic/orchestrator.md` | v5.0.0 → v5.1.0 (Minor). Hardcoded `2` → `{{A2A_MAX_DEPTH}}` Template-Variable |
| `agents/1-generic/validator.md` | v4.0.0 → v4.1.0 (Minor). Hardcoded `2` → `{{A2A_MAX_DEPTH}}` Template-Variable |
| `scripts/lib/delegation_syntax.py` | `validate_envelope()` nimmt `max_depth` Parameter (Default 10) |
| `scripts/lib/config.py` | `build_variables()` injiziert `A2A_MAX_DEPTH` aus `project.yaml → orchestrator.delegation.max_depth` (Default 10, Range 1–50) |
| `config/project-config.schema.json` | Neues optionales Property `orchestrator.delegation.max_depth` (int, 1–50, Default 10) |
| `docs/admin-ui.html` | Neuer "Delegation"-Panel in Orchestrator-View mit max_depth-Slider (10–50) + Save-Button |
| `howto/project.yaml.example` | Kommentierte Config-Zeile für `orchestrator.delegation.max_depth` |
| `.opencode/agents/orchestrator.md` | Neu generiert via Sync (enthält `{{A2A_MAX_DEPTH}}` aufgelöst) |
| `.claude/agents/orchestrator.md` | Neu generiert via Sync |
| `.opencode/agents/validator.md` | Neu generiert via Sync |
| `.claude/agents/validator.md` | Neu generiert via Sync |

### Indirekt generiert (via sync.py-Propagation)

| Artefakt | Änderung |
|----------|----------|
| `.claude/rules/a2a-delegation-gates.md` | Propagiert via Sync |
| `.gemini/rules/a2a-delegation-gates.md` | Propagiert via Sync |
| `.continue/rules/a2a-delegation-gates.md` | Propagiert via Sync |
| `AGENTS.md` (updated managed block) | Zeilen 49–82: neue Sektion |
| `CLAUDE.md` (updated managed block) | Gleiche Sektion |

---

## 2. Bug-Hintergrund

### Auslöser
In einem Ziel-Repo führte eine Aufgabe zu folgender Delegationskette:

```
main → orchestrator → orchestrator → orchestrator
```

Zwei Defekte:
1. **Spec-Dump im Handoff:** Der Hauptchat packte die vollständige Implementierungs-Spec (viele Zeilen) in `payload.t`, statt einer kurzen Task-Beschreibung.
2. **Fehlende Re-Delegation-Sperre:** `agents/1-generic/orchestrator.md` prüfte zwar Delegation-Tiefe/Anzahl, aber NICHT ob `source_agent == target_agent`. Dadurch konnte der Orchestrator an sich selbst delegieren.

### Warum das kritisch ist
- Self-Handoff erzeugt Endlos-Schleifen ohne äußere Kontrolle (LLM merkt nicht dass es sich selbst aufruft)
- Spec-Dump überschwemmt `payload.t` und verschwendet Tokens
- Kein struktureller Schutz im A2A-Envelope-Schema

---

## 3. Designentscheidungen

### 3.1 JSON Schema kann `source_agent ≠ target_agent` nicht nativ ausdrücken
JSON Schema (Draft-07) hat keinen `not`-Constraint der zwei Properties vergleicht. Daher:
- **Schema-Ebene:** `delegation_depth` als required + maximum 50, Self-Handoff nur in `description` dokumentiert
- **Enforcement:** In `delegation_syntax.py` Tier-1.5 (läuft ohne jsonschema-Dependency)

### 3.2 Schema-maximum 50 statt 10
Das konfigurierbare Limit (Default 10) liegt **innerhalb** des Schema-Bereichs (0–50). 50 als Schema-Maximum verhindert unsinnige Werte >50, erlaubt aber Abweichungen nach oben falls nötig. Die `validate_envelope()`-Funktion nutzt das konfigurierte Limit, nicht das Schema-Maximum.

### 3.3 `isinstance(dd, bool)` Exclusion
Python `bool` ist eine `int`-Subklasse. Ohne explizite Exclusion würde `True`/`False` als `1`/`0` durchgehen:
```python
if not isinstance(dd, int) or isinstance(dd, bool):
    errors.append(...)
```

### 3.4 Self-Handoff bleibt nicht-konfigurierbar
Anders als `max_depth` ist Self-Handoff-Verbot ein **struktureller Fehler** ohne legitimen Use-Case. Konfigurierbarkeit würde nur Fehlkonfigurationen ermöglichen.

### 3.5 Admin UI manuell ergänzt
`viewProjectOrchestrator()` in `docs/admin-ui.html` rendert nicht automatisch aus dem Schema. Der neue "Delegation"-Panel (Slider + Label + Save-Button) wurde manuell eingefügt.

### 3.4 Rule-Benennung
Die Rule heißt `a2a-delegation-gates.md` (Plural "Gates") — nicht `a2a-delegation-gate.md`. Dies betont dass es sich um ein **System von Prüfungen** handelt (Self-Handoff + Tiefenlimit + T-Size-Limit + Re-Delegation-Detection), nicht um eine einzelne Hürde. Die 4 Gates sind:
1. Self-Handoff-Verbot (HARD REJECT)
2. Tiefenlimit (HARD REJECT bei >max_depth)
3. T-Size-Limit (KEIN Dispatch, User informieren)
4. Re-Delegation-Detection (HARD REJECT bei "Du bist..."-Erkennung)

---

## 4. Vererbungs-Architektur

```
rules/1-generic/a2a-delegation-gates.md    ← Quelle (einmal definieren)
    │
    ├── sync.py propagiert → .claude/rules/a2a-delegation-gates.md
    ├── sync.py propagiert → .gemini/rules/a2a-delegation-gates.md
    ├── sync.py propagiert → .continue/rules/a2a-delegation-gates.md
    ├── AGENTS.md (managed block, Zeilen 49–82)
    └── CLAUDE.md (managed block, gleicher Inhalt)
```

**Warum das wichtig ist:** Die Rule ist provider-agnostisch gehalten (kein Claude-/Gemini-/Continue-spezifischer Inhalt). Sync.py kopiert sie 1:1 in jedes Provider-Rules-Verzeichnis. Änderungen an der Quelle propagieren automatisch in alle Provider und in alle Projekte die agent-meta als Submodul eingebunden haben.

**Platzhalter in der Rule:** `{{A2A_MAX_DEPTH}}` und `{{A2A_T_SIZE_LIMIT}}` werden via `scripts/lib/config.py → build_variables()` pro Projekt aufgelöst. Das bedeutet: verschiedene Projekte können unterschiedliche Limits haben, ohne die Rule ändern zu müssen.

---

## 5. Validierungsergebnisse

### sync.py — Schema-Validierung und Generierung
- `python scripts/sync.py` erfolgreich durchgelaufen
- Alle generierten Artefakte (`.opencode/agents/*.md`, `.claude/agents/*.md`, Rules, AGENTS.md, CLAUDE.md) neu erzeugt
- Keine Sync-Fehler protokolliert

### Schema-Tests
- `schemas/a2a-handoff.schema.json` — `delegation_depth` als required + maximum 50
- Schema-Dokumentation aktualisiert: Self-Handoff-Verbot im `description`-Feld
- `config/project-config.schema.json` — neues Property `orchestrator.delegation.max_depth` in bestehendem `delegation`-Block

### Depth-Tests (via validate_envelope)
- `validate_envelope()` akzeptiert `max_depth` Parameter (Default 10)
- `delegation_depth` 0..max_depth → valid
- `delegation_depth` > max_depth → error
- `delegation_depth` vom Typ `bool` → error (False/True durchgelassen)
- `delegation_depth` fehlt → required-fields-error
- `source_agent == target_agent` → Self-Handoff-Reject
- `source_agent ≠ target_agent` → kein Self-Handoff-Fehler
- `delegation_depth` negativ → error

---

## 6. Offene Punkte / Lessons Learned

### 6.1 JSON Schema Limit
JSON Schema (Draft-07) kann `source_agent ≠ target_agent` nicht nativ als Constraint ausdrücken. Die Prüfung in `delegation_syntax.py` Tier-1.5 ist der korrekte Ort, aber es wäre eleganter wenn das Schema selbst diesen Constraint abbilden könnte. JSON Schema 2020-12 hat `dependentRequired` und komplexere `if/then/else` — auch damit lässt sich Property-Ungleichheit nicht abbilden.

### 6.2 Admin UI Auto-Render fehlt
Der neue "Delegation"-Panel in `docs/admin-ui.html` wurde manuell ergänzt. `viewProjectOrchestrator()` rendert nicht automatisch aus der Schema-Konfiguration. Zukünftig könnte der UI-Code refactored werden um dynamisch aus `project-config.schema.json` zu rendern.

### 6.3 T-Size-Limit noch nicht vollständig in Agents integriert
Die Rule (`rules/1-generic/a2a-delegation-gates.md`) und die Template-Variable (`A2A_T_SIZE_LIMIT`) sind definiert. Die Orchestrator/Validator-Agenten haben noch keine explizite `payload.t > limit`-Prüfung im Fließtext — sie verlassen sich auf die Rule. Das ist pragmatisch aber nicht vollständig deterministisch. Ein expliziter Code-Check (z.B. in `delegation_syntax.py`) wäre härter.

### 6.4 Re-Delegation-Detection sprachabhängig
Die "Du bist..."-Erkennung funktioniert nur für Deutsch. Für englischsprachige Projekte müsste "You are..." ergänzt werden. Derzeit nicht konfigurierbar.

---

## 7. Nächste Schritte

1. **PR erstellen:** `feat/a2a-anti-re-delegation` → `main` via GitHub
   - Branch-Guard: Branch existiert, Feature ist vollständig
   - Vor Merge: `python scripts/sync.py` nochmal laufen lassen
2. **Push:** erst nach PR-Merge (oder wenn User explizit Push anfordert)
3. **T-Size-Limit Härtung:** Explizite Prüfung in `delegation_syntax.py` oder Orchestrator-Template
4. **Re-Delegation-Sprachen:** Englisch-Support für "You are..."-Detection
5. **Admin UI Refactoring:** Auto-Render aus project-config.schema.json

---

## 8. Monitoring / Metriken (vorgeschlagen)

Nach dem Rollout sollten folgende Metriken getrackt werden:
- Wie oft wird `HARD REJECT` wegen Self-Handoff ausgelöst? (→ Indikator für Routing-Fehler)
- Wie oft wird `delegation_depth > max_depth` ausgelöst? (→ Indikator für zu komplexe Ketten)
- Wie oft wird T-Size-Limit ausgelöst? (→ Indikator für Spec-Dump-Trend)

---

## 9. Versions-Updates

| Artefakt | Alte Version | Neue Version | Grund |
|----------|-------------|-------------|-------|
| `agents/1-generic/orchestrator.md` | 4.5.0 | 5.1.0 | Major: Anti-Recursion-Section; Minor: Configurable depth |
| `agents/1-generic/validator.md` | 3.3.1 | 4.1.0 | Major: Topological Hard Rejects; Minor: Configurable depth |
| `rules/1-generic/a2a-delegation-gates.md` | — | 1.0.0 | Neu: Provider-agnostische Anti-Re-Delegation Rule |

---

## 10. Branch & Commits

**Branch:** `feat/a2a-anti-re-delegation`

**Commits:**
1. `c41e78d` — `feat: add A2A anti-re-delegation gates`
2. `b3731a6` — `feat(a2a): make delegation depth configurable via project.yaml`

**Nächster Commit (diese Session):** `docs: document A2A anti-re-delegation gates feature`
