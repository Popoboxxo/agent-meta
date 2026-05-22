# Erkenntnisse — 23. Mai 2026

## Session-Zusammenfassung
Vollständige Entwicklung und Dokumentation der Systems Engineering (SE) Agenten-Kaskade in agent-meta. Alle 6 SE-Agenten-Templates wurden inhaltlich massiv erweitert, JSON Schema erweitert, neue Templates und Howto-Dokumente erstellt, Dokumentation aktualisiert, README gepatcht und Sync über alle 4 Provider durchgeführt. Zusätzlich 4 GitHub Issues erstellt (1 Feature, 3 Bugs).

---

## 1. SE-Agenten-Templates erweitert (v1.0.0 → v1.1.0)

### se-requirements.md (31 → 93 Zeilen)
- ISO/IEC 15288 Bezug eingeführt
- REQ-ID-Logik spezifiziert
- Domänen-Zuweisung (software/hardware/mechanics/system)
- Externe Schnittstellen-Erfassung
- JSON Output Schema definiert

### se-architect.md (27 → 115 Zeilen)
- Context Boundary (~2k Token Limit)
- INCOSE Functional Decomposition
- Domänen-Aufteilung
- Interne/externe Interfaces
- Trade-offs und Rationale
- JSON Output Schema

### se-critic.md (23 → 108 Zeilen)
- AutoGen Reflection Pattern implementiert
- 4 Prüf-Dimensionen: Completeness, Consistency, Verifiability, Traceability
- Verdikt-System: approved / rejected / blocked
- correction_hints für abgelehnte Designs
- Max 3 Iterationen
- JSON Output Schema

### se-interface-mgr.md (48 → 121 Zeilen)
- Interface Registry
- **Propagations-Map** als zentraler Mechanismus eingeführt
- Interface-Spec pro Komponente
- Validierung gegen bestehende Verträge
- Frontmatter korrigiert (`name: se-interface-mgr`)

### se-termination.md (46 → 124 Zeilen)
- Leaf/Continue-Entscheidung pro Komponente
- Kriterien: atomare Code-Einheit, COTS, ausgereizte Domäne, explizite Grenze
- Schutzregeln: max_depth, max_total_cells, Zirkular-Check
- Frontmatter korrigiert (`name: se-termination`)

### se-orchestrator.md (55 → 153 Zeilen)
- Rekursive System-Zelle (fraktal, n→n+1)
- Cell Spawning Mechanismus
- Context Hygiene
- Parallele Zellen-Ausführung
- JSON Output Schema
- Frontmatter korrigiert (`name: se-orchestrator`)

---

## 2. JSON Schema erweitert (`schemas/se-decomposition.schema.json`)

Neue Felder rückwärtskompatibel hinzugefügt:
- `sub_components`
- `internal_interfaces`
- `propagation_map`
- `architectural_rationale`
- `decomposition_completeness`
- `termination_decisions`
- `termination_summary`
- `critic_status`

Bestehende Felder (`l1_system`, `l2_subsystems`, `l3_components`, `cqrs_interfaces`) unverändert.

---

## 3. Neue Templates und Howto-Dokumente

| Datei | Zweck |
|-------|-------|
| `templates/SE-STRATEGY.template.md` | Adaptiert vom Compound Engineering STRATEGY.md-Pattern |
| `howto/se-workflow.md` | Rekursiver Workflow mit Mermaid-Diagramm |
| `howto/se-blackbox-to-whitebox.md` | Blackbox→Whitebox Methodik |
| `howto/se-interface-management.md` | Interface-Propagation detailliert |
| `howto/se-mcp-adapters.md` | MCP-Adapter-Konzept für Phase 3 |

---

## 4. Dokumentation aktualisiert

| Datei | Änderung |
|-------|----------|
| `docs/CODEBASE_OVERVIEW.md` | Neu erstellt (~556 Zeilen) |
| `ARCHITECTURE.md` | Erweitert (+133 / −6 Zeilen) |
| `docs/architecture/07-se-cascade.md` | Neu erstellt (~286 Zeilen) |
| `docs/architecture/03-agent-roles.md` | Erweitert (+13 Zeilen) |
| `README.md` | Version 0.47.0-beta → 0.49.0, SE-Abschnitt + Tabellen ergänzt |

---

## 5. Sync über alle Provider

`python scripts/sync.py` erfolgreich ausgeführt. Alle 6 SE-Rollen für alle 4 Provider (Claude, Opencode, Gemini, Continue) neu generiert.

---

## 6. GitHub Issues erstellt

| Issue | Titel | Typ |
|-------|-------|-----|
| #204 | Bug: orchestrator references delegable validator agent which is not a valid subagent_type | Bug |
| #205 | Fix: orchestrator agent missing model definition in frontmatter across all providers | Bug |
| #206 | Fix: Gemini /commands not working in newly generated editors | Bug |
| #207 | Feat: autonomous MBSE engine (SE-Runner) to process requirement collections through the SE cascade | Feature |

---

## 7. Wichtige Erkenntnisse

### 7.1 Prompt-MVP vs. autonome Engine
Die Agenten-Templates sind inhaltlich vollständig, aber es gibt **keine ausführbare Zustandsmaschine**. Die "Rekursion" existiert nur als Prompt-Konzept. Für echte Autonomie fehlt ein Python-Runner (geschätzt ~1–1,5 Wochen Aufwand).

### 7.2 Orchestrator-Frontmatter-Bug
`model: ""` in `role-defaults.yaml` führt dazu, dass **kein** `model:` Feld in generierten Orchestrator-Agenten erscheint. Betroffen: alle 4 Provider. Ursache: `scripts/lib/agents.py` filtert leere Werte heraus.

### 7.3 Gemini Commands defekt
`sync.py` konvertiert `.md` → `.toml`, aber die generierten TOMLs funktionieren nicht in Gemini CLI. Mögliche Ursachen:
- Schema-Änderung bei Gemini CLI
- Fehlende Felder im generierten TOML
- Pfad-Problem

### 7.4 Validator-Agent nicht delegierbar
`validator` existiert in `role-defaults.yaml` und `agents/1-generic/validator.md`, aber ist **kein gültiger `subagent_type`**. Der Orchestrator suggeriert Delegation an `validator`, was fehlschlägt.

### 7.5 Context Drift Risiko
Ohne den SE-Runner gibt es keine technische Durchsetzung der Context-Hygiene. Agenten sehen den gesamten Chat-Verlauf, nicht nur die Parent-Black-Box + Nachbar-Interfaces. Das ist ein inhärentes Limit des reinen Prompt-Ansatzes.

---

## 8. Offene Punkte / Follow-ups

1. **SE-Runner implementieren** (Feature #207)
   - Phase 1 Semi-autonom (2–3 Tage)
   - Phase 2 Vollautonom (+3–4 Tage)

2. **Orchestrator-Modell-Defekt fixen** (Bug #205)
   - `model: balanced` oder `model: fast` in `role-defaults.yaml` setzen

3. **Gemini Commands reparieren** (Bug #206)
   - Prüfen ob `.toml` Format aktuell ist
   - Prüfen ob Gemini neue Struktur erwartet

4. **Validator als Subagent-Typ hinzufügen oder aus Orchestrator entfernen** (Bug #204)

5. **Dokumentation pflegen**
   - `CODEBASE_OVERVIEW.md` und `ARCHITECTURE.md` bei zukünftigen SE-Änderungen aktualisieren

---

## 9. Branch

`feat/se-agent-cascade`

### Commits
- `feat: expand SE agent cascade prompts, schemas, templates and howto docs`
- `docs: update CODEBASE_OVERVIEW and ARCHITECTURE for SE cascade`
- `docs: update README with SE cascade feature and version bump`
