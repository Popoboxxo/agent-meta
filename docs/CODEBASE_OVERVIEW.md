# CODEBASE_OVERVIEW — agent-meta

> Letzte Aktualisierung: 2026-06-12 (Orchestrator v3.22.0, 3-Tier-Developer, PAL-Engine-Fix, Delegation-Syntax-Laufzeit-Platzhalter)

---

## Inhaltsverzeichnis

1. [SE-Agenten-Kaskade](#1-se-agenten-kaskade)
2. [Provider-Expert-Agenten](#2-provider-expert-agenten)
3. [Agent-Templates (1-generic)](#3-agent-templates-1-generic)
4. [Konfiguration](#4-konfiguration)
5. [Schemas](#5-schemas)
6. [Templates](#6-templates)
7. [Howto-Dokumentation](#7-howto-dokumentation)
8. [Scripts](#8-scripts)
9. [Provider Abstraction Layer (PAL)](#9-provider-abstraction-layer-pal)
10. [A2A-Handoff-Protokoll](#10-a2a-handoff-protokoll)

---

## 1. SE-Agenten-Kaskade

Die SE-Agenten-Kaskade ist ein fraktales, rekursives Systems-Engineering-System mit 6 spezialisierten Agenten, die zusammen eine 6-stufige Black-Box → White-Box-Zerlegung koordinieren.

### 1.1 `agents/1-generic/se-orchestrator.md`

**Version:** 1.1.0
**Beschreibung:** Koordiniert den gesamten 6-stufigen rekursiven Systems-Engineering-Herunterbruch als Fraktal-Zellmaschine.

**Exportierte API (Frontmatter):**
```yaml
name: se-orchestrator
version: 1.1.0
description: "Coordinates the 6-level recursive breakdown."
tools: [read_file, write_file, edit_file, glob, grep]
```

**Interne Funktionen / Zuständigkeiten:**

| Funktion | Signatur | Zweck |
|----------|----------|-------|
| `Initialization` | `(stakeholder_feature) → se-requirements` | Startet die Kaskade mit Stakeholder-Input |
| `L1_Phase` | `(requirements) → se-architect → se-critic` | L1 Blackbox → Whitebox Definition + Verifikation |
| `L2_Phase` | `(l1_whitebox) → se-architect → se-critic → se-interface-mgr` | L2 Zerlegung + Interface-Sicherung |
| `L3_Phase` | `(l2_whitebox) → se-architect → se-critic → se-termination` | L3 Komponentendefinition + finaler Check + Abschluss |
| `Cell_Spawn` | `(component, propagation_map) → new_cell(n+1)` | Spawn einer neuen Zelle für `decision: continue` Komponenten |
| `Parallel_Execution` | `(cells[], max_parallel_cells) → results[]` | Parallele Ausführung unabhängiger Zellen |

**Output-Struktur:**
```json
{
  "orchestration_id": "ORCH-001",
  "level": 1,
  "status": "completed",
  "cells_spawned": [...],
  "leaf_components": [...],
  "propagation_map_ref": "IFM-001",
  "next_actions": ["await_cell_completion", "handover_to_disciplines"]
}
```

**Kritische Regeln:**
- **No Contamination:** Zelle n+1 darf nie auf Daten fremder Zellen zugreifen
- **Deterministic Depth:** `max_depth` wird strikt eingehalten
- **Idempotence:** Gleicher Input + gleiche Konfiguration = identische Zellsequenz
- **Context Window Rule:** Zelle n+1 erhält nur Parent Black-Box (~500 Tokens) + relevante Interfaces (~300 Tokens)

**Flows:**

```
Stakeholder Input → se-requirements → L1 Black-Box REQ
                                      ↓
                              se-architect (White-Box)
                                      ↓
                              se-critic (Quality Gate)
                                      ↓
                          se-interface-mgr (Verträge)
                                      ↓
                          se-termination (Leaf/Continue?)
                           ↙              ↘
                      Leaf Node        Neue Zelle (n+1)
```

---

### 1.2 `agents/1-generic/se-requirements.md`

**Version:** 1.1.0
**Beschreibung:** Nimmt Stakeholder-Bedürfnisse auf und erstellt formale L1-Blackbox-Anforderungen nach ISO/IEC 15288.

**Exportierte API (Frontmatter):**
```yaml
name: se-requirements
version: 1.1.0
description: "Elicits stakeholder needs and uses a 6-level template for requirements engineering."
tools: [read_file, write_file, run_command, ask_question]
```

**Interne Funktionen / Zuständigkeiten:**

| Funktion | Signatur | Zweck |
|----------|----------|-------|
| `Elicit_Requirements` | `(unstructured_input) → structured_dialog` | Dialog mit User zur Klärung von Unklarheiten |
| `Formulate_BB_Requirement` | `(need) → "The system shall X under Y with Z"` | Messbare Black-Box-Anforderung formulieren |
| `Assign_REQ_ID` | `(requirement) → REQ-NNN` | Eindeutige ID vergeben (REQ-001, REQ-042, ...) |
| `Assign_Domain` | `(requirement) → {system\|software\|hardware\|mechanics}` | Domänen-Tag aus kontrolliertem Vokabular |
| `Capture_External_Interfaces` | `(requirement) → [{direction, type, description}]` | Externe Schnittstellen erfassen |
| `Prioritize` | `(requirements[]) → ordered[mandatory, desired, optional]` | Priorisierung und Konfliktlösung |

**Output-JSON-Schema:**
```json
{
  "requirements": [{
    "req_id": "REQ-001",
    "statement": "The system shall heat 500ml of water to 90°C within 120 seconds.",
    "domain": "system",
    "priority": "mandatory",
    "rationale": "Stakeholder Need: Hot water preparation",
    "external_interfaces": [
      {"direction": "input", "type": "physical", "description": "230V AC power supply"}
    ]
  }]
}
```

**6-Level-Hierarchie:**
1. Stakeholder Requirement (REQ-L1-SH)
2. L1 System Blackbox
3. L1 System Whitebox
4. L2 System Blackbox
5. L2 System Whitebox
6. L3 Component Requirement

---

### 1.3 `agents/1-generic/se-architect.md`

**Version:** 1.1.0
**Beschreibung:** Zerlegt Black-Box-Anforderungen in White-Box-Architektur nach INCOSE-Methodik (funktionale Dekomposition).

**Exportierte API (Frontmatter):**
```yaml
name: se-architect
version: 1.1.0
description: "Designs system architecture using generic laws, CQRS routing, and defines L1/L2 whiteboxes."
tools: [read_file, write_file, run_command]
```

**Interne Funktionen / Zuständigkeiten:**

| Funktion | Signatur | Zweck |
|----------|----------|-------|
| `Analyze` | `(parent_requirement) → {functional, non-functional, constraints}` | Anforderung analysieren |
| `Define_SubComponents` | `(blackbox) → sub_components[]` | Minimale Sub-Komponenten definieren |
| `Assign_Domain` | `(sub_component) → {software\|hardware\|mechanics\|system}` | Domäne zuweisen |
| `Define_Internal_Interfaces` | `(sub_components[]) → internal_interfaces[]` | Interne Schnittstellen zwischen Komponenten |
| `Map_External_Interfaces` | `(external_ifaces, sub_components) → mapping` | Externe Interfaces Sub-Komponenten zuordnen |
| `Derive_BB_Requirement` | `(sub_component) → black_box_requirement` | Neue Black-Box-REQ für nächste Ebene ableiten |
| `Rationale` | `(decisions) → {chosen, rejected_alternative, reason}` | Architekturentscheidung begründen |

**Kontext-Grenze (Strict):**
- `parent_requirement`: Einzelne Black-Box-REQ (nicht der gesamte Baum)
- `external_interfaces`: Vom Parent-Level diktiert
- `system_domain`: `{system, software, hardware, mechanics}`
- `neighbor_contracts`: Interface-Verträge vom Interface Manager
- **MAX ~2k Tokens** — kein Zugriff auf höhere Level

**Output-JSON-Schema:**
```json
{
  "parent_req_id": "REQ-001",
  "sub_components": [{
    "id": "COMP-001-01",
    "name": "Heating Element Controller",
    "domain": "hardware",
    "black_box_requirement": "...",
    "assigned_external_interfaces": ["230V AC power supply"]
  }],
  "internal_interfaces": [{
    "source_id": "COMP-001-02",
    "target_id": "COMP-001-01",
    "interface_type": "analog_signal",
    "data_payload": "PWM control signal 0-100%, 5V logic level"
  }],
  "architectural_rationale": "...",
  "decomposition_completeness": "..."
}
```

**Architektur-Gesetze:**
- Problem Space von Solution Space trennen
- Orthogonalität (keine überlappenden Verantwortlichkeiten)
- Strenge Traceability (jede Sub-Komponente → Parent-REQ)
- Lose Kopplung, hohe Kohäsion
- Minimalität: Komponente nur wenn nötig

**Post-Decomposition-Handoff:**
Architect → Critic (Quality Gate) → bei `approved` → Interface Manager + Termination

---

### 1.4 `agents/1-generic/se-critic.md`

**Version:** 1.1.0
**Beschreibung:** Universeller Auditor und Quality Gate der System-Dekomposition (AutoGen Reflection Pattern).

**Exportierte API (Frontmatter):**
```yaml
name: se-critic
version: 1.1.0
description: "Audits architecture against generic laws (orthogonality, testability, traceability)."
tools: [read_file, write_file, run_command]
```

**Interne Funktionen / Zuständigkeiten:**

| Funktion | Signatur | Zweck |
|----------|----------|-------|
| `Check_Completeness` | `(architect_output) → {passed: bool, issues: []}` | Vollständigkeitsprüfung |
| `Check_Consistency` | `(architect_output) → {passed: bool, issues: []}` | Konsistenzprüfung |
| `Check_Verifiability` | `(architect_output) → {passed: bool, issues: []}` | Testbarkeitsprüfung |
| `Check_Traceability` | `(architect_output) → {passed: bool, issues: []}` | Traceability-Prüfung |
| `Render_Verdict` | `(checks[]) → {approved\|rejected\|blocked}` | Bindinges Urteil fällen |
| `Correction_Loop` | `(rejected, hints) → architect_retry` | Korrekturschleife (max. 3 Iterationen) |

**Prüfkriterien im Detail:**

| Check | Was wird geprüft |
|-------|-----------------|
| **Completeness** | Sub-Komponenten decken Parent-REQ vollständig ab? Alle externen Interfaces zugeordnet? Minimal? |
| **Consistency** | Keine Widersprüche zwischen Komponenten? Interface-Typen kompatibel mit Payloads? Domänen sinnvoll? |
| **Verifiability** | Jede abgeleitete BB-REQ messbar? Akzeptanzkriterien vorhanden? Binär verifizierbar? |
| **Traceability** | Gültige IDs? `source_id`/`target_id` existieren? Rationale referenziert Parent? |

**Entscheidungslogik:**
- `approved` → Weiter an Interface Manager + Termination
- `rejected` → Zurück an Architect mit `correction_hints` (max. 3 Iterationen)
- `blocked` → Eskalation an Parent-Zelle (fundamentale Fehler)

**Output-JSON-Schema:**
```json
{
  "status": "approved",
  "checks": {
    "completeness": {"passed": true, "issues": []},
    "consistency": {"passed": true, "issues": []},
    "verifiability": {"passed": true, "issues": []},
    "traceability": {"passed": true, "issues": []}
  },
  "correction_hints": [],
  "iteration": 1,
  "max_iterations": 3
}
```

---

### 1.5 `agents/1-generic/se-interface-mgr.md`

**Version:** 1.1.0
**Beschreibung:** Zentrales Management und Validierung aller Interface-Verträge zwischen Systemelementen über Level und parallele Zweige hinweg.

**Exportierte API (Frontmatter):**
```yaml
name: se-interface-mgr
version: 1.1.0
description: "Manages generic signal flow and deterministic synchronization across systems."
tools: [read_file, write_file, edit_file, glob, grep]
```

**Interne Funktionen / Zuständigkeiten:**

| Funktion | Signatur | Zweck |
|----------|----------|-------|
| `Register_Interface` | `(interface) → registry_entry` | Interface in zentrale Registry aufnehmen |
| `Validate_Contracts` | `(new_interface, existing_registry) → {valid, conflicts}` | Gegen bestehende Verträge prüfen |
| `Generate_Propagation_Map` | `(internal_interfaces, external_interfaces) → propagation_map` | Propagations-Map erzeugen |
| `Generate_Interface_Spec` | `(component_id, propagation_map) → iface_spec` | Interface-Spec pro Sub-Komponente |

**Propagations-Map (Zentraler Mechanismus):**
```json
{
  "propagation_map": {
    "COMP-001-01": {
      "inherited_external": ["230V AC power supply"],
      "new_internal_incoming": [],
      "new_internal_outgoing": ["IF-001-01"]
    }
  }
}
```

**Regeln:**
- **Orthogonality:** Kein Zugriff ohne expliziten Contract
- **Traceability:** Jedes Interface → L1/L2 Architekturelement
- **Deterministic Synchronization (Rule 11):** Asynchrone Berechnung, kontrollierte synchrone Anwendung

**Workflow:**
1. `internal_interfaces` vom Architect + `external_interfaces` vom Parent empfangen
2. Jedes Interface registrieren, IDs validieren, Typen klassifizieren
3. Gegen bestehende Contracts aus parallelen Zweigen validieren
4. Propagations-Bedarf identifizieren, Propagations-Map generieren
5. Interface-Spec pro Sub-Komponente für nächste Ebene erzeugen

---

### 1.6 `agents/1-generic/se-termination.md`

**Version:** 1.1.0
**Beschreibung:** Deterministische Entscheidung pro Sub-Komponente: Leaf Node (fertig) oder neue Zelle (weiter zerlegen).

**Exportierte API (Frontmatter):**
```yaml
name: se-termination
version: 1.1.0
description: "Deterministic termination at L3 (Component Requirement)."
tools: [read_file, write_file, edit_file, glob, grep]
```

**Interne Funktionen / Zuständigkeiten:**

| Funktion | Signatur | Zweck |
|----------|----------|-------|
| `Leaf_Decision` | `(component) → {decision: "leaf", rationale}` | Leaf-Kriterien prüfen |
| `Continue_Decision` | `(component) → {decision: "continue", rationale}` | Continue-Kriterien prüfen |
| `Apply_Protection_Rules` | `(component, depth, cell_count) → forced_leaf?` | Schutzregeln anwenden |
| `Generate_Summary` | `(decisions[]) → {total, leaf_nodes, continue_nodes, current_depth, max_depth}` | Terminierungs-Zusammenfassung |

**Leaf-Kriterien (mindestens eines muss gelten):**
- **Atomic Code Unit:** Als einzelne Funktion/Klasse/Modul implementierbar
- **COTS:** Commercial Off-The-Shelf, kaufbar
- **Exhausted Domain:** Keine sinnvolle weitere Zerlegung möglich
- **Explicit Boundary:** Anforderung definiert Zukaufteil

**Continue-Kriterien:**
- Multiple unterscheidbare Sub-Tasks (>1 Verantwortung)
- Komponente spannt mehrere Domänen auf
- Komponente zu komplex für atomare Implementierung

**Schutzregeln:**
- `max_depth`: Leaf wenn current_depth >= Limit
- `max_total_cells`: Leaf wenn Gesamtzellen >= Limit
- **Circular Reference:** Leaf wenn Parent-ID-Kette Zyklus enthält

**Harte Regel:** Kein L4 oder L5 — SE endet bei L3.

**Output-JSON-Schema:**
```json
{
  "termination_decisions": [
    {"component_id": "COMP-001-01", "decision": "continue", "rationale": "..."},
    {"component_id": "COMP-001-02", "decision": "leaf", "rationale": "..."}
  ],
  "termination_summary": {
    "total": 3,
    "leaf_nodes": 2,
    "continue_nodes": 1,
    "current_depth": 1,
    "max_depth": 5
  }
}
```

---

## 2. Provider-Expert-Agenten

Die Provider-Expert-Agenten wurden in v0.55.0 eingeführt und bieten Provider-spezifische Konfigurationsberatung, Best Practices und Troubleshooting. Sie basieren auf dem generischen Template `agents/1-generic/provider-expert.md` (v1.0.0) mit `based-on` Composition Pattern.

### 2.1 Generische Basis: `agents/1-generic/provider-expert.md`

**Version:** 1.0.0
**Beschreibung:** Provider-agnostische Basis für alle Expert-Agenten.

**Plattform-Instanziierungen (2-platform/):**

| Agent | Plattform-Datei | Provider |
|-------|----------------|----------|
| `claude-expert` | `agents/2-platform/agent-meta-claude-expert.md` | Claude Code (VS Code) |
| `gemini-expert` | `agents/2-platform/agent-meta-gemini-expert.md` | Gemini (VS Code/Antigravity) |
| `opencode-expert` | `agents/2-platform/agent-meta-opencode-expert.md` | Opencode |
| `continue-expert` | `agents/2-platform/agent-meta-continue-expert.md` | Continue |
| `copilot-expert` | `agents/2-platform/agent-meta-copilot-expert.md` | GitHub Copilot |

**Zuständigkeiten:**
- Provider-spezifische Konfigurationsvalidierung (`.claude/`, `.gemini/`, `.opencode/`, `.continue/`, `.github/copilot/`)
- MCP-Server-Integration pro Provider
- Best Practices für Agent-Template-Erstellung
- Troubleshooting bei Provider-spezifischen Fehlern
- Orchestrator Routing: User-Anfragen zu Provider-Konfiguration werden an den passenden Expert-Agent delegiert

---

## 2.5 3-Tier-Developer-System (v2026-06-12)

Das System wurde vollständig in Orchestrator und Templates integriert. Drei spezialisierte Developer-Agenten mit Eskalations- und De-Eskalations-Protokoll:

### Tier-Übersicht

| Tier | Agent | Modell | Einsatz | Signale | Eskaliert zu |
|------|-------|--------|--------|---------|--------------|
| `fast` | `junior-developer` | Günstiger/Fast | Trivialer Fix ≤2 Dateien, offensichtliche Lösung | Typo, Off-by-one, Config-Wert, Logging, Boilerplate-nach-Vorlage | `developer` ODER `senior-developer` |
| `balanced` | `developer` | Balanced | Standard-Implementierung, klarer Scope | Feature mit Pattern, normaler Bugfix, ≤3 Dateien | `senior-developer` (bei Scope-Überschreitung) |
| `max` | `senior-developer` | Powerful/Max | Architektur-Impact, Risiko, unklare Ursache | API/Schema-Änderung, Cross-Cutting-Refactoring, Race Condition, Security, Performance | Keine (end-of-line) |

### Eskalations-Protokoll

Wenn Developer mit `ESCALATE`-Card antwortet (`reason`, `recommended_tier`, `findings`, `partial_work`):

1. KEINE Rückfrage an User → sofort an `recommended_tier` neu dispatchen
2. `findings` in `payload.ctx` des neuen Handoffs übernehmen (Context-Overhead sparen)
3. `trace_parent` auf ursprüngliche `handoff_id` setzen
4. **Maximal 1 Eskalation pro Task** — eskaliert auch Stufe 2, geht zum User

### De-Eskalation

Falls `senior-developer` ein Ergebnis mit `de_escalation_hint: <tier>` liefert, merkt Orchestrator sich das Muster für künftiges Routing ähnlicher Tasks.

### Routing-Entscheidung im Orchestrator

Intent-Routing-Tabelle mit {{#if DEVELOPER_TIERS_ENABLED}}-Blöcken:
- Trivialer Fix → `junior-developer` (fast)
- Komplexe Implementierung/Architektur-Impact/schwieriger Bug → `senior-developer` (max)
- Standard → `developer` (balanced, default)

**Entscheidungsregeln:**
- Im Zweifel zwischen zwei Stufen → höhere wählen (Fehlrouting nach unten kostet Eskalations-Runde)
- Batch gleichartiger Trivial-Tasks → FANOUT auf `junior-developer`

---

## 3. Agent-Templates (1-generic)

### Nicht-SE Agenten (Bestand)

| Datei | Version | Tools | Kurzbeschreibung |
|-------|---------|-------|-----------------|
| `orchestrator.md` | 3.22.0 | read, write, edit, glob, grep | Einstiegspunkt für alle Entwicklungsaufgaben; Pre-Delegation Gate, BARRIER Protocol, Error-Recovery Matrix, In-Context Tracker, Delegation-Syntax mit Laufzeit-Platzhaltern |
| `developer.md` | 2.0.1 | read, write, edit, glob, grep | Feature-Implementierung und Bugfixes |
| `junior-developer.md` | 1.0.0 | read, write, edit, glob, grep | Fast-Tier: triviale Fixes ≤2 Dateien, kein Design nötig |
| `senior-developer.md` | 1.0.0 | read, write, edit, glob, grep | Max-Tier: Architektur-Impact, komplexe/riskante Änderungen, schwierige Bugs |
| `tester.md` | — | read, write, run_command | TDD, Test-Suite, Testabdeckung |
| `validator.md` | 2.0.1 | read, run_command | Code gegen REQs prüfen, DoD-Check |
| `documenter.md` | — | read, write, edit, glob, grep | CODEBASE_OVERVIEW, ARCHITECTURE, README |
| `requirements.md` | — | read, write, run_command, ask_question | Anforderungen aufnehmen, REQ-IDs |
| `git.md` | 2.2.0 | run_command | Commits, Branches, Tags, Push/Pull |
| `release.md` | — | read, write, run_command | Versioning, Changelog, GitHub Release |
| `ideation.md` | — | read, write, ask_question | Neue Ideen explorieren |
| `feature.md` | 1.8.0 | read, write, edit, glob, grep | Feature-Lifecycle-Subagent; A2A-Envelope Integration, standardisiertes Context-Handoff |
| `agent-meta-manager.md` | 1.9.0 | read, write, edit, glob, grep | agent-meta verwalten |
| `agent-meta-scout.md` | — | read, write, glob, grep | Ökosystem scouten |
| `security-auditor.md` | — | read, run_command | Sicherheits-Audit |
| `docker.md` | — | run_command | Docker-Stack verwalten |
| `meta-feedback.md` | 2.0.0 | read, write, run_command | Verbesserungsvorschläge als Issues |
| `feedback.md` | — | read, write, run_command | Projekt-Feedback als Issues |
| `log-analyzer.md` | — | read, write, run_command | Log-Analyse, Fehler-Clustering |
| `effort-estimator.md` | — | read, write, run_command | Aufwandsschätzung mit Komplexitäts-Scoring |
| `code-reviewer.md` | — | read, write, edit, glob, grep | Clean Code Gatekeeper, Blast-Radius-Analyse |
| `ui-ux-designer.md` | — | read, write, glob, grep | UI-Spezifikationen, Mockups, Design-Systeme |
| `api-specialist.md` | — | read, write, edit, glob, grep | OpenAPI/Contract-First API-Design |
| `devops-engineer.md` | — | read, write, run_command | CI/CD, IaC, Kubernetes, Infrastruktur |
| `performance-optimizer.md` | — | read, write, run_command | Big-O Bottleneck-Identifikation |
| `export-manager.md` | — | read, write, run_command | Target-agnostisches Output-Routing |
| `bug-feature-analyzer.md` | — | read, write, glob, grep | Issue-Triage, Bug/Feature-Klassifikation |
| `openscad-developer.md` | — | read, write, run_command | Parametrische 3D-Modelle in OpenSCAD |
| `provider-expert.md` | 1.0.0 | read, write, edit, glob, grep | Basis-Template für Provider-Experten |

---

## 4. Konfiguration

### `config/role-defaults.yaml`

**SE-Rollen (neu, Zeilen 142-176):**

| Rolle | Model | Memory | Workflow-Tier | Description |
|-------|-------|--------|---------------|-------------|
| `se-requirements` | balanced | project | optional | Stakeholder-Bedürfnisse → L1-Blackbox-REQ |
| `se-architect` | powerful | project | optional | Blackbox → Whitebox (CQRS, Orthogonalität) |
| `se-critic` | powerful | — | optional | Vollständigkeit, Konsistenz, Testbarkeit |
| `se-interface-mgr` | balanced | project | optional | Schnittstellenverträge domänenübergreifend |
| `se-termination` | fast | — | optional | L3-Component-Leaf-Node Entscheidung |
| `se-orchestrator` | balanced | — | optional | 6-stufiger rekursiver SE-Herunterbruch |

### `config/ai-providers.yaml` & `config/generated/model-registry.json`

**Zweck:** Verwaltung von dynamischen Modellen und Tiers über eine Preset-Matrix.
- **Model Registry (`model-registry.json`):** Enthält dynamisch abgerufene Modelle von Provider-APIs (Anthropic, Gemini, Opencode).
- **Pricing Overlay (`pricing-overlay.yaml`):** Reichert Modelle um Input/Output-Kosten an, woraus ein normalisierter *Cost Factor* (Score 1-100) berechnet wird.
- **Tier-Presets Matrix (`project.yaml`):** Mappt dynamisch Agenten-Tiers (nano, fast, balanced, powerful, max) auf konkrete Modelle, basierend auf dem eingestellten Preset (z.B. cheap, normal, advanced, expensive). Systems-Engineering (SE) Rollen werden zusätzlich über ein SE-spezifisches Prefix künstlich aufgewertet.

---

## 5. Schemas

### 5.0 A2A-Handoff-Envelope — Das EINZIGE Austauschformat

**A2A-Envelopes sind das einzige Format für Agent-zu-Agent-Daten.** Natural-Language-Prompts zwischen Agenten werden vollständig durch strukturierte Envelopes ersetzt. Alle bisherigen Payload-Schemas (ideation-output, se-decomposition, se-orchestrator) werden unverändert als `payload` in den Envelope eingebettet.

Neue Payload-Schemas (TaskSpec + Extensions) verwenden **kurze Feldnamen** (2–3 Zeichen) mit ausführlichen `title`/`description` im Schema für Lesbarkeit — Token-Ersparnis: 20–50 Tokens pro Handoff.

**Schema-Strategie:** 1 Core (TaskSpec) + 4 Extensions (Ideation, Design, API, Review) + 1 SE (se-decomposition). Reduziert die Schema-Anzahl von 19 auf 6.

### 5.1 `schemas/a2a-handoff.schema.json` — Envelope

**Version:** Draft-07 JSON Schema
**Zweck:** Standardisierter Envelope für ALLE Agent-zu-Agent-Handoffs. Umhüllt jedes domain-spezifische Payload mit Metadaten für Validierung, Supersession-Tracking und Traceability.

**Top-Level Required Fields:**
| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `protocol_version` | string (SemVer) | Version des A2A-Protokolls (default = aktuell, nur explizit bei Major-Change) |
| `handoff_id` | string (`HOFF-YYYYMMDD-NNN`) | Eindeutige Handoff-ID |
| `source_agent` | string | Rolle des sendenden Agenten |
| `target_agent` | string | Rolle des empfangenden Agenten |
| `payload` | object | Domain-spezifische Daten (validiert gegen `schema_ref`) |

**Optionale Felder:**
| Feld | Beschreibung |
|------|-------------|
| `schema_ref` | URI zum Payload-Schema (implizit aus Route ableitbar — optional für Token-Ersparnis) |
| `compact_mode` | boolean: `true` = kurze Payload-Feldnamen (default: `false`) |
| `supersession` | Versionsinfo: `version`, `supersedes`, `history[]`, `reason`, `timestamp` |
| `trace_parent` | handoff_id des übergeordneten Handoffs (Delegationsbaum-Tracing) |
| `trace_context` | Erweitertes Tracing: `trace_id`, `span_id`, `parent_span_id`, `viz_task_id` |
| `metadata` | Extensible Key-Value-Map für provider-spezifische Metadaten |

**Definitionen:**
- `handoffRoute` — Registrierte Route zwischen zwei Rollen: `source`, `target`, `contract`, `input_schema`
- `agentContract` — Deklaration was eine Rolle konsumiert/produziert
- `handoffRegistry` — Vollständige Registry aller Routen

### 5.2 `schemas/handoffs/task-spec.schema.json` (NEU — Universelles Kern-Payload)

**Zweck:** Universelles Payload-Schema für 60-80% aller Delegationen. Kurze Feldnamen (2-3 Zeichen) für Token-Effizienz.

**Feld-Mapping (kurz → lang):**
| Feld | Key | Typ | Beschreibung |
|------|-----|-----|-------------|
| Task | `t` | string (Pflicht) | Task-Beschreibung in Natural Language |
| Context | `ctx` | string | Zusätzlicher Kontext |
| Constraints | `con` | string[] | Harte Randbedingungen |
| References | `refs` | string[] | Referenzen auf Dateien/Schemas/Issues |
| Priority | `pri` | enum | `low`, `medium`, `high`, `critical` |
| Depends on | `dep` | HOFF[] | Abhängigkeiten von anderen Handoffs |

**Token-Ersparnis vs. lange Feldnamen:** ~40 Tokens pro Handoff (31% Reduktion).

### 5.3 Extensions (NEU — 4 Dateien unter `schemas/handoffs/ext/`)

Jede Extension erweitert TaskSpec um domain-spezifische Felder via JSON Schema `allOf`:

| Extension | Datei | Route | Zusätzliche Felder |
|-----------|-------|-------|-------------------|
| IdeationExtension | `ideation-extension.schema.json` | ideation → requirements | `ci` (core_idea), `g` (goal), `sv1` (scope_v1), `oq`, `ref` |
| DesignExtension | `design-extension.schema.json` | ui-ux-designer → developer | `ds` (design_spec: components, theme), `lo` (layouts), `wf` (wireframes) |
| APIExtension | `api-extension.schema.json` | api-specialist → developer | `ct` (contract: endpoints, schemas), `cf`, `vr`, `gw` |
| ReviewExtension | `review-extension.schema.json` | code-reviewer → developer | `rd` (review_data: verdict, findings[], blast_radius), `ri` |

### 5.4 `schemas/handoffs/ideation-output.schema.json` (Existierend)

**Zweck:** Strukturiertes Payload-Schema für den Handoff von `ideation` → `requirements`. **Bleibt unverändert** — wird als `payload` in A2A-Envelope eingebettet. **Hinweis:** Dieses Schema hat noch lange Feldnamen. Neue Instanzen sollen stattdessen TaskSpec + IdeationExtension mit `compact_mode: true` nutzen.

**Required Fields:** `core_idea`, `goal`, `preliminary_requirements[]`, `scope_v1{in_scope[], out_of_scope[]}`

### 5.5 `schemas/se-decomposition.schema.json` (Existierend)

**Version:** Draft-07 JSON Schema
**Zweck:** Strukturiertes Output-Schema für generische L1-L3 Layer, CQRS-Events und SE-Agent-Konzept rekursive Zell-Outputs. **Bleibt unverändert** — wird als `payload` in A2A-Envelope eingebettet. `compact_mode: false` (lange Feldnamen erhalten).

**Top-Level Required Fields:**
- `feature_id` (string) — Eindeutige Feature-ID
- `stakeholder_requirement` (string) — Formalisierte Stakeholder-Anforderung
- `l1_system` (object) — `{blackbox: string, whitebox: string[]}`
- `l2_subsystems` (array) — `[{subsystem_id, blackbox, whitebox}]`
- `l3_components` (array) — `[{component_id, description, refines}]`
- `cqrs_interfaces` (object) — `{commands[], events[], queries[]}`

### 5.6 `schemas/se-orchestrator.schema.json` (Existierend)

**Zweck:** Orchestrierungs-Metadaten vom se-orchestrator. **Bleibt unverändert** — wird als `payload` in A2A-Envelope eingebettet.

---

## 6. Templates

### `templates/SE-STRATEGY.template.md`

**Version:** 1.0.0
**Zweck:** Durable Anchor für SE-Projekte — definiert System-Ziel, Constraints, Scope, Stakeholder, Annahmen, Risiken und SE-Kaskaden-Konfiguration.

**Platzhalter:**
| Platzhalter | Zweck |
|-------------|-------|
| `{{PROJECT_NAME}}` | Projektname im Header |
| `{{SYSTEM_GOAL}}` | Primäres Systemziel |
| `{{SUCCESS_CRITERION_N}}` | Erfolgskriterien (1-3) |
| `{{HARD_CONSTRAINT_N}}` / `{{IMPACT_N}}` | Harte Constraints |
| `{{SOFT_CONSTRAINT_N}}` / `{{PRIORITY_N}}` | Weiche Constraints |
| `{{STAKEHOLDER_N}}` / `{{INTEREST_N}}` / `{{INFLUENCE_N}}` | Stakeholder-Tabelle |
| `{{IN_SCOPE_N}}` / `{{OUT_OF_SCOPE_N}}` / `{{BOUNDARY_N}}` | Scope-Definition |
| `{{ASSUMPTION_N}}` / `{{RISK_IF_FALSE_N}}` | Annahmen mit Risiken |
| `{{RISK_N}}` / `{{PROB_N}}` / `{{IMPACT_RISK_N}}` / `{{MITIGATION_N}}` | Risikotabelle |
| `{{DATE}}` | Letztes Update-Datum |

**SE-Kaskaden-Konfiguration (YAML-Block):**
```yaml
se-cascade:
  max_depth: 5
  max_total_cells: 20
  max_critic_iterations: 3
  max_parallel_cells: 4
  cost_limit_eur: 5.00
```

**Traceability-Tabelle:** Verweist auf `docs/se/requirements.md`, `architecture.md`, `interface-registry.md`, `traceability-matrix.md`.

---

## 7. Howto-Dokumentation

### `howto/se-workflow.md` (181 Zeilen)

**Zweck:** Vollständiger Ablauf des fraktalen SE-Workflows mit Mermaid-Diagrammen, Rollenbeschreibungen, Rekursionsregeln und Konfiguration.

**Inhalt:**
- Grundprinzip der System-Zelle (Eingabe → Ablauf → Ausgabe)
- Rekursiver Fluss (Mermaid-Diagramm)
- 5 Rollen im Detail
- Rekursion und Terminierung (Übergang n → n+1)
- Parallelisierung (`max_parallel_cells`)
- Artefakte pro Ebene (Tabelle)
- Korrekturschleifen (approved/rejected/blocked)
- Konfiguration in `.meta-config/project.yaml`

### `howto/se-blackbox-to-whitebox.md` (154 Zeilen)

**Zweck:** Erklärung des zentralen BB → WB-Übergangs mit 7-Schritte-Methode, Beispiel (Wassererhitzungssystem), Regeln und Critic-Checkliste.

**Inhalt:**
- Black-Box vs. White-Box Definition
- 7 Schritte des Architects
- Vollständiges Beispiel mit Mermaid-Diagramm
- 6 Regeln für den Übergang
- Häufige Fehler-Tabelle
- Critic-Checkliste (8 Punkte)

### `howto/se-interface-management.md` (190 Zeilen)

**Zweck:** Detaillierte Erklärung des Interface-Managements mit Propagations-Map, Lifecycle, Vererbungsregeln und Fehlerbeispielen.

**Inhalt:**
- Warum ein eigener Agent?
- 4 Aufgaben des Interface Managers
- Interface-Lifecycle (Mermaid)
- Propagations-Map mit vollständigem JSON-Beispiel
- Interface-Vererbung (extern + intern)
- 5 Validierungs-Regeln
- Interface-Registry-Format
- 3 Fehlerbeispiele (Spannung, Zuordnung, Drift)

### `howto/se-mcp-adapters.md` (250 Zeilen)

**Zweck:** MCP-Adapter-Konzept für Export von SE-Artefakten in externe Ticket-Systeme (Markdown, GitHub Issues, Jira, Linear, ReqIF).

**Inhalt:**
- Export-Architektur (JSON-Graph → Adapter)
- Phasen-Roadmap (Phase 1-3)
- Adapter-Schnittstelle (Python-Klasse)
- Konfiguration für alle 5 Export-Typen
- Mapping-Tabellen (GitHub Issues, Jira)
- MCP-Server-Konfiguration (JSON)
- Export-Workflow (Mermaid)
- Sicherheit und Secrets

---

## 8. Scripts

### `scripts/sync.py`

**Zweck:** Generiert `.claude/agents/` aus Templates. Liest `config/role-defaults.yaml` für Modell-Konfiguration, Memory, Permission-Modes.

**SE-Integration:** Die 6 SE-Rollen werden wie alle anderen Rollen generiert. `workflow_tier: optional` bedeutet sie werden nur generiert wenn in `project.yaml` unter `roles` aufgelistet.

**Bekannte Flows:**
1. `sync.py` liest alle Templates aus `agents/1-generic/`, `agents/2-platform/`, `agents/3-project/`
2. Substitution der Platzhalter (`{{VAR}}`) aus `build_variables()`
3. Composition-Auflösung (`extends:` + `patches:`)
4. Output nach `.claude/agents/<rolle>.md`
5. Rules und Hooks werden nach `.claude/rules/` und `.claude/hooks/` kopiert

**Dynamisches Crawling (`--update-models`):**
Ruft das Modul `scripts/lib/model_discovery.py` auf, um aktuelle Modelle von den Provider-APIs zu laden und lokal in der `model-registry.json` zu cachen.

### `scripts/admin-server.py` & `docs/admin-ui.html`

**Zweck:** Bereitstellung einer interaktiven, webbasierten Admin UI.
- **Dashboard:** Bietet ein "Model Discovery & Pricing" Dashboard mit sortierbaren Modell-Tabellen, Preis-Heatmaps und einem Button zum direkten Ausführen von `sync.py --update-models`.
- **Config Management:** Visuelle Bearbeitung der Tier-Presets Matrix und Provider-Konfiguration inklusive Live-Vorschau.
- **Architektur:** Single-File Web Frontend (`docs/admin-ui.html`) in Vanilla JS (Zero Dependencies) und ein Python-Backend (`scripts/admin-server.py`).

### `scripts/viz-logger.py` & `scripts/viz-logger-mcp.mjs` & `scripts/lib/viz.py`

**Zweck:** Steuerung und Ausführung der Visualisierung von Agenten-Netzwerken.
- `viz-logger.py`: MCP-Server und CLI-Fallback für agenten-seitiges Event-Logging (`agent_start`, `delegate_out`, `agent_end`). Primärer Weg für MCP-fähige Provider (kein Prompt-Bloat, keine Bestätigungs-Popups). CLI-Modus als Fallback für Provider ohne MCP-Unterstützung.
- `viz-logger-mcp.mjs`: HTTP/SSE MCP-Transport für OpenCode unter Windows. Löst das Kompatibilitätsproblem mit stdio-basiertem MCP auf dieser Plattform.
- `lib/viz.py`: Beinhaltet Kernlogiken zur Mindmap/HTML-Generierung (Architektur-Graphen) und zur Injection (`inject_viz_prompt_block`), um die kurzen Logging-Instruktionen (MCP/CLI-Fallback) in die generierten Agenten-Templates zu integrieren. Die Prompt-Blöcke wurden in v0.55.2 um ~60% reduziert durch Auslagerung der Logging-Logik in das MCP-Tool.

**Architektur-Entscheidung (MCP + CLI Fallback):**
- Vermeidung von Prompt-Bloat durch Auslagerung langer Inline-Python-Skripte
- Höhere Zuverlässigkeit durch MCP-Tools (keine Bash-Bestätigungs-Popups bei Copilot, Continue, Claude Code)
- Robustes Cross-Process File-Locking mit Exponential Backoff gegen Windows `PermissionError`
- Explizites Handshake-Tracking via `task_id`/`caller`/`target` für lückenlose Delegationspfade

### `scripts/lib/pipelines.py`

**Zweck:** Quality Pipeline Configuration Management — definiert Execution-Modes (sequential/loop/parallel_group) und Pipeline-Strukturen.

**Neue Features (v2026-06-12):**
- **Execution-mode Headers:** Jede Pipeline-Definition erhält einen Ausführungsmodus mit Wait/Check-Cues pro Schritt
  - `sequential`: Schritte nacheinander, warten bis fertig
  - `loop`: Generator → Critic → Feedback → Generator (max N Iterationen)
  - `parallel_group`: Mehrere unabhängige Agenten parallel mit BARRIER
- **Pipeline Loading:** `load_quality_pipelines()` liest `config/role-defaults.yaml` → `quality_pipelines` Sektion
- **Overrides Management:** `apply_overrides()` merged base pipelines mit projekt-spezifischen Overrides aus `.meta-config/project.yaml` → `quality-pipelines` Sektion
- **Validation:** `validate_pipelines()` prüft Agent-Existenz, Loop-Definitionen, Circular-Orchestration-Prevention

**Exportierte API:**

| Funktion | Signatur | Zweck |
|----------|----------|-------|
| `load_quality_pipelines` | `(agent_meta_root: str) → dict` | Lädt `config/role-defaults.yaml` → `quality_pipelines` |
| `load_pipeline_overrides` | `(config_path: str) → dict` | Lädt `.meta-config/project.yaml` → `quality-pipelines` |
| `apply_overrides` | `(base: dict, overrides: dict) → dict` | Merged base+overrides, Stage-Level-Merging unterstützt |
| `validate_pipelines` | `(pipelines: dict, available_roles: list) → list[str]` | Validiert Agent-Existenz, Loop-Definition, Circular-Checks |

### `scripts/lib/delegation_syntax.py` & `scripts/lib/bootstrap.py`

**Zweck:** Provider Abstraction Layer (PAL) — syntaktische Isolation generischer Templates.
- `delegation_syntax.py`: `DelegationSyntaxEngine` substituiert `{{PAL_*}}` Platzhalter in provider-native Syntax während der Agent-Generierung. Lädt `config/delegation-syntax.yaml` und `config/provider-capabilities.yaml`.
- `bootstrap.py`: `BootstrapEngine` führt provider-spezifische Registrierungsaktionen aus. Gemini: `define_subagent` Instruktionen in GEMINI.md injizieren. Continue: Agent-Einträge in `.continue/config.yaml` schreiben.

---

## 9. Provider Abstraction Layer (PAL)

Der Provider Abstraction Layer (PAL) isoliert generische Agent-Templates von provider-spezifischer Delegationssyntax. Er verhindert "Syntax Leaks" und handhabt provider-spezifische Bootstrap-Mechanismen.

### 9.1 `config/delegation-syntax.yaml` — Provider-Delegation Syntax Registry

**Zweck:** Registry die abstrakte `{{PAL_*}}` Platzhalter auf provider-native Delegationssyntax mappt. Neu: Laufzeit-Platzhalter verwenden `<angle-brackets>` statt `{{}}` um LLM-Verwirrung bei Template-Substitution zu vermeiden.

**Root-Cause Bug (Issue #277):** LLM bei Runtime interpretierten `{{agent}}`/`{{task}}`/`{{calls}}`/`{{foreground}}`/`{{background}}` als ungelöste sync.py-Platzhalter → weigerte sich zu delegieren. **Fix:** Umgestellt auf `<angle-brackets>` — die LLM konkret mit Agenten-Namen und Task-Text füllt.

**Struktur:**
```yaml
delegation_syntax:
  <Provider>:
    delegate: '<native syntax mit <ziel-agent> und <vollständiger-task-text>>'
    fanout: '<parallel execution instruction>'
    parallel_group: '<mixed agent parallel instruction>'
    fallback: '<fallback instruction>'
    bootstrap: 'file-based | api-based | config-based'
    tool_preamble: true | false
    handoff: '<A2A-Envelope-Instruktion mit <quelle> <ziel> <schema-uri>>'
```

**PAL-Platzhalter-Mapping (Compile-Zeit):**

| PAL-Platzhalter | YAML-Key | Laufzeit-Form | Bedeutung |
|-----------------|----------|---------------|-----------|
| `{{PAL_DELEGATE}}` | `delegate` | `<ziel-agent>`, `<vollständiger-task-text>` | Native Agent-Delegationssyntax |
| `{{PAL_FANOUT}}` | `fanout` | `<agent_1>`, `<task_1>`, `<agent_2>`, `<task_2>` | Parallele Ausführung gleicher Agenten |
| `{{PAL_PARALLEL_GROUP}}` | `parallel_group` | `<fg_agent>`, `<fg_task>`, `<bg_agent>`, `<bg_task>` | Parallele Ausführung verschiedener Agenten |
| `{{PAL_FALLBACK}}` | `fallback` | `<task>` | Fallback bei nicht verfügbaren Tool-Calls |
| `{{PAL_HANDOFF}}` | `handoff` | `<quelle>`, `<ziel>`, `<schema-uri>`, `<parent-HOFF>` | A2A-Envelope-Strukturierung |
| `{{PAL_TOOL_PREAMBLE}}` | `tool_preamble` | — | Tool-Auflistung im Agent-Template |

**Kritische Änderung v2 (2026-06-12):**
- Alte Syntax: `{{agent}}`, `{{task}}` → Verwirrung bei LLM
- Neue Syntax: `<agent>`, `<task>` → LLM erkennt korrekt als Platzhalter für Laufzeit-Substitution

### 9.2 `config/provider-capabilities.yaml`

**Zweck:** Capability Matrix — dokumentiert welche Features jeder Provider unterstützt.

**Capability-Flags:**

| Flag | Typ | Bedeutung |
|------|-----|-----------|
| `subagent_dispatch` | boolean | Native Subagent-Dispatch-Tools verfügbar |
| `parallel_execution` | boolean | Parallele Subagent-Ausführung möglich |
| `file_based_agents` | boolean | Agenten werden aus Dateien automatisch geladen |
| `text_mentions` | boolean | `@agent` Text-Mentions als Dispatch |
| `hooks` | boolean | Git-Hook-Integration unterstützt |
| `native_agent_tools` | string[] | Namen der nativen Agent-Tools |
| `bootstrap_required` | boolean | Session-Bootstrap erforderlich |

### 9.3 `config/provider-bootstrap.yaml`

**Zweck:** Definiert Registrierungsmechanismus pro Provider.

**Mechanismen:**

| Mechanismus | Provider | Aktion |
|-------------|----------|--------|
| `file-based` | Claude, Opencode, Copilot | `none` — Auto-Discovery |
| `api-based` | Gemini | `inject-bootstrap-instructions` in GEMINI.md |
| `config-based` | Continue | `update-config` in `.continue/config.yaml` |

### 9.4 `scripts/lib/delegation_syntax.py`

**Klasse:** `DelegationSyntaxEngine`

**Exportierte API:**

| Methode | Signatur | Zweck |
|---------|----------|-------|
| `__init__` | `(config_dir: Path \| None) → None` | Initialisiert mit Config-Verzeichnis |
| `syntax_registry` | property → `dict` | Lädt `delegation-syntax.yaml` (lazy, cached) |
| `capabilities_registry` | property → `dict` | Lädt `provider-capabilities.yaml` (lazy, cached) |
| `get_syntax` | `(provider: str) → dict` | Syntax-Map für Provider |
| `get_capabilities` | `(provider: str) → dict` | Capabilities für Provider |
| `apply` | `(content: str, provider: str) → str` | Substituiert `{{PAL_*}}` in Template-Content |
| `needs_bootstrap` | `(provider: str) → bool` | Prüft ob Bootstrap erforderlich |
| `has_native_subagent_dispatch` | `(provider: str) → bool` | Native Dispatch verfügbar? |
| `has_file_based_agents` | `(provider: str) → bool` | File-based Agent-Discovery? |

**PLACEHOLDERS-Mapping (Klassenkonstante):**
```python
PLACEHOLDERS = {
    "PAL_DELEGATE": "delegate",
    "PAL_FANOUT": "fanout",
    "PAL_PARALLEL_GROUP": "parallel_group",
    "PAL_FALLBACK": "fallback",
    "PAL_HANDOFF": "handoff",
    "PAL_TOOL_PREAMBLE": "tool_preamble",
}
```

**Flow (überarbeitete Reihenfolge nach Issue #284-286):**
```
1. Template wird eingelsen, Platzhalter identifiziert
2. {{#if PAL_*}}-Blöcke werden ZUERST evaluiert (VOR strip_inactive_conditional_blocks)
   → behebt Bug wo inaktive PAL-Blöcke fälschlicherweise entfernt wurden
3. _compose_agent() ruft DelegationSyntaxEngine.apply(content, provider) auf
4. Engine lädt delegation-syntax.yaml (lazy, einmalig)
5. Für jeden PAL-Platzhalter: Regex-Substitution mit provider-spezifischer Syntax
6. Verbleibende {{PAL_*}} Placeholder werden entfernt (no-op für diesen Provider)
7. PAL_PREFIX: Marker-Zeilen werden entfernt
8. Return: bereinigter Content mit nativer Provider-Syntax
```

### 9.5 `scripts/lib/bootstrap.py`

**Klasse:** `BootstrapEngine`

**Exportierte API:**

| Methode | Signatur | Zweck |
|---------|----------|-------|
| `__init__` | `(config_dir: Path \| None) → None` | Initialisiert mit Config-Verzeichnis |
| `bootstrap_registry` | property → `dict` | Lädt `provider-bootstrap.yaml` (lazy, cached) |
| `get_bootstrap_config` | `(provider: str) → dict` | Bootstrap-Konfiguration für Provider |
| `run_bootstrap` | `(provider, agents_dir, project_root) → dict` | Führt provider-spezifischen Bootstrap aus |
| `generate_gemini_bootstrap_instructions` | `(agents_dir: Path) → str` | Generiert lesbare Bootstrap-Instruktionen für GEMINI.md |

**Bootstrap-Mechanismen:**

| Mechanismus | Methode | Beschreibung |
|-------------|---------|-------------|
| `api-based` | `_bootstrap_api_based()` | Liest Agent-Dateien, extrahiert Descriptions, generiert define_subagent Calls |
| `config-based` | `_bootstrap_config_based()` | Trägt Agenten in `.continue/config.yaml` ein (managed block mit Markern) |
| `none` | — | Skip — file-based Provider benötigen keinen Bootstrap |

**Flow für Gemini:**
```
1. BootstrapEngine.generate_gemini_bootstrap_instructions(agents_dir)
2. Liest alle .md-Dateien aus .gemini/agents/
3. Extrahiert description aus Frontmatter jeder Datei
4. Generiert Schritt-für-Schritt Instruktionen (Session-Start Pflicht)
5. _inject_gemini_bootstrap() injiziert in GEMINI.md (managed block)
```

**Flow für Continue:**
```
1. BootstrapEngine.run_bootstrap(provider, agents_dir, project_root)
2. Liest alle .md-Dateien aus .continue/agents/
3. Öffnet .continue/config.yaml
4. Findet/erstellt managed block (agent-meta:managed-agents-begin/end)
5. Schreibt Agent-Einträge (name + prompt-Pfad)
6. Nur bei Änderungen → Datei wird aktualisiert
```

### 9.6 `templates/bootstrap/gemini-session-bootstrap.md`

**Zweck:** Bootstrap-Template für Gemini/Antigravity Session-Start.

**Inhalt:**
- Erklärung warum Bootstrap nötig ist (keine dateibasierte Registry)
- 4-Schritte-Workflow: Dateien einlesen → define_subagent → Orchestrator zuerst → Anfragen bearbeiten
- Hinweise: Ephemere Registrierung, Version-Abhängigkeit von sync.py, Konsequenzen ohne Bootstrap

### 9.7 Integration in `scripts/lib/agents.py`

**Stelle:** `_compose_agent()` Funktion, Zeile ~1082

```python
# Apply PAL delegation syntax per provider (Issue #277)
from .delegation_syntax import DelegationSyntaxEngine
pal_engine = DelegationSyntaxEngine(config_dir=agent_meta_root / "config")
content = pal_engine.apply(content, provider)
```

**Stelle:** `sync_agents_for_provider()`, nach Agent-Generierung

```python
_inject_gemini_bootstrap(provider, target_dir, ...)  # Gemini: GEMINI.md
BootstrapEngine.run_bootstrap(...)                    # Continue: config.yaml
```

---

---

## 10. A2A-Handoff-Protokoll

> **Status:** Vollständig implementiert (Phasen 1–4) — 22 Dateien, 818 Zeilen
> **Basiert auf:** [GitHub Issue #212](https://github.com/Popoboxxo/agent-meta/issues/212) — W3C ANP White Paper
> **Dokument:** `docs/concepts/a2a-handoff-protocol.md`
> **Analyse:** `docs/concepts/a2a-best-practice-analysis.md`

### 10.1 Prinzip: A2A als EINZIGES Format

**A2A-Envelopes sind das einzige Format für Agent-zu-Agent-Daten.** Natural-Language-Prompts zwischen Agenten werden vollständig durch strukturierte Envelopes ersetzt. Dies eliminiert Context Loss, ermöglicht deterministische Validierung und schafft lückenloses Supersession-Tracking.

Ausnahme: Continue/Copilot (`structured_handoff: false`) erhalten einen YAML-Text-Block statt JSON — identisches Konzept, anderes Transport-Format.

### 10.2 Kernkonzepte

| Konzept | Beschreibung |
|---------|-------------|
| **A2A-Envelope** | Standardisierter JSON-Wrapper mit Metadaten — das **einzige** Austauschformat |
| **TaskSpec** | Universelles Kern-Payload-Schema für 60-80% aller Delegationen (kurze Feldnamen) |
| **Extensions** | 4 domain-spezifische Erweiterungen zu TaskSpec (Ideation, Design, API, Review) |
| **compact_mode** | Envelope-Flag: `true` = kurze Payload-Namen (Token-sparend), `false` = lesbare Namen |
| **Supersession** | Version-Tracking mit `history[]`-Array für vollständige Revisionsketten |
| **Contract** | Jede Route deklariert Schema + Extension + compact_mode in der Routing-Tabelle |

### 10.3 A2A vs. viz-Debug — Separate Konzepte

Das A2A-Protokoll und der viz-Handshake sind **separate Systeme** mit loser Kopplung:

| Ebene | System | ID | Default | Token-Kosten |
|-------|--------|-----|---------|-------------|
| **Data Contract Layer** | A2A-Envelope | `handoff_id` | **Immer aktiv** | Envelope-Overhead (~60 Tokens) |
| **Operational Layer** | viz-Handshake | `viz_task_id` | Aktiv (basic) | 0 (MCP-basiert) |
| **Debug-Ebene** | viz A2A-Events | `viz_task_id` | **AUS** (`viz.debug: false`) | 0 Tokens |

**Lose Kopplung via `trace_context.viz_task_id`** — das einzige Feld das beide Systeme verbindet. Der A2A-Envelope funktioniert vollständig ohne viz, und viz funktioniert ohne A2A.

### 10.4 Schema-Strategie: 1 Core + 4 Extensions + 1 SE

```
schemas/handoffs/
├── task-spec.schema.json              ← Core (60-80% Abdeckung)
├── ext/
│   ├── ideation-extension.schema.json  ← ideation → requirements
│   ├── design-extension.schema.json    ← ui-ux-designer → developer
│   ├── api-extension.schema.json       ← api-specialist → developer
│   └── review-extension.schema.json    ← code-reviewer → developer
└── (se-decomposition.schema.json)      ← SE-Kaskade (existierend, unverändert)
```

Reduziert die Schema-Anzahl von 19 auf 6 (84% Routen-Abdeckung mit Core + Extensions).

### 10.5 Orchestrator als Envelope-Fabrik

Der Orchestrator ist der primäre Envelope-Produzent:

| Orchestrator-Funktion | A2A-Rolle |
|-----------------------|-----------|
| Intent-Routing | Bestimmt `target_agent` + `schema_ref` + `compact_mode` aus Routing-Tabelle |
| FANOUT | Produziert N parallele Envelopes mit gemeinsamem `trace_context.trace_id` |
| BARRIER | Konsumiert Response-Envelopes, aggregiert Ergebnisse |
| PIPELINE | Verkettet Envelopes via `trace_parent` |
| REPEAT_UNTIL | Managed Supersession-Ketten via `supersession.history[]` |

### 10.6 Provider-Matrix: Transport-Format

| Provider | structured_handoff | handoff_format | Envelope-Transport |
|----------|-------------------|----------------|-------------------|
| Claude | `true` | `json` | JSON im Task-Tool-Prompt |
| Opencode | `true` | `json` | JSON im task()-Prompt |
| Gemini | `true` | `json` | JSON im define_subagent-Prompt |
| Continue | `false` | `yaml_text_block` | YAML-Block im Prompt-Text |
| Copilot | `false` | `yaml_text_block` | YAML-Block im Prompt-Text |

### 10.7 Token-Budget & Optimierungen

| Optimierung | Ersparnis | Status |
|-------------|-----------|--------|
| Kurze Payload-Feldnamen (TaskSpec + Extensions) | 20–50 Tokens/Handoff | ✓ Umgesetzt |
| `schema_ref` optional (implizit aus Route) | ~20 Tokens | ✓ Im Schema |
| `protocol_version` default = aktuell | ~9 Tokens | ✓ Konvention |
| `compact_mode`-Flag zur Steuerung | — (schaltet #1) | ✓ Im Envelope |
| viz.debug: false (default) | 30 Tokens/Handoff | ✓ In Config |

### 10.8 Betroffene Artefakte

| Artefakt | Änderung | Status |
|----------|----------|--------|
| `schemas/a2a-handoff.schema.json` | Envelope: `batch`, `retry_count`, `requires_human_approval`, `negotiated_format`, `supersession.history[]` | ✓ Phase 1 |
| `schemas/handoffs/task-spec.schema.json` | Universelles Kern-Payload (NEU) — kurze Feldnamen | ✓ Phase 1 |
| `schemas/handoffs/ext/*.schema.json` | 4 Extensions (NEU): Ideation, Design, API, Review | ✓ Phase 1 |
| `schemas/se-decomposition.schema.json` | **Unverändert** — in Envelope eingebettet | — |
| `schemas/se-orchestrator.schema.json` | **Unverändert** — in Envelope eingebettet | — |
| `.meta-config/project.yaml` | `orchestrator.handoff`-Block + `viz.debug` + `viz.a2a_events` | ✓ Phase 1 |
| `docs/concepts/a2a-handoff-protocol.md` | Implementation-nahes Konzept (v2.0, 872 Zeilen) | ✓ Phase 1 |
| `docs/CODEBASE_OVERVIEW.md` | Abschnitte 5 + 10 aktualisiert | ✓ Phase 1 |
| `config/delegation-syntax.yaml` | `handoff:`-Block für alle 5 Provider (JSON + YAML-Fallback) | ✓ Phase 2 |
| `config/provider-capabilities.yaml` | `structured_handoff` + `handoff_format` + `handoff_envelope_support` Flags | ✓ Phase 2 |
| `scripts/lib/delegation_syntax.py` | `PLACEHOLDERS` um `PAL_HANDOFF` erweitert | ✓ Phase 2 |
| `config/role-defaults.yaml` | 16 Rollen-Contracts: `input_contracts`, `output_contract`, `input_schema`, `output_schema`, `target_roles` | ✓ Phase 3 |
| `agents/1-generic/orchestrator.md` | Handoff-Routing-Tabelle + Envelope-Fabrik + Supersession-Tracking | ✓ Phase 3 |
| `agents/1-generic/ideation.md` | Envelope-basierte Handoffs | ✓ Phase 3 |
| `agents/1-generic/feature.md` | A2A-Handoff-Integration | ✓ Phase 3 |
| `agents/1-generic/developer.md` | A2A-Envelope-Consumer | ✓ Phase 3 |
| `agents/1-generic/se-*.md` | Envelope-basierte Handoffs in SE-Kaskade (6 Agenten) | ✓ Phase 3 |
| `config/mcp-registry.yaml` | `a2a-handoff` MCP-Server: `validate_handoff`, `resolve_handoff_schema`, `resolve_handoff` | ✓ Phase 4 |
| `scripts/lib/viz.py` | A2A-Events in `inject_viz_prompt_block()` hinter `viz.debug`-Flag | ✓ Phase 4 |

### 10.9 Roadmap

| Phase | Inhalt | Status |
|-------|--------|--------|
| 1 — Konzept + Schemas | Core-Schema + 4 Extensions + Envelope-Anpassungen + Config + Doku | ✓ Abgeschlossen |
| 2 — Provider-Capabilities | `{{PAL_HANDOFF}}`-Platzhalter + `structured_handoff`-Flags + delegation-syntax.yaml | ✓ Abgeschlossen |
| 3 — Agent-Updates | Orchestrator-Envelope-Fabrik + handoff-Contracts + ideation, feature, developer, SE-Agenten | ✓ Abgeschlossen |
| 4 — MCP & Tooling | MCP-Tools (resolve-handoff-schema, validate-handoff, resolve-handoff) + viz-Integration | ✓ Abgeschlossen |

### 10.10 Handoff-Contracts in `config/role-defaults.yaml`

16 Rollen deklarieren A2A-Handoff-Contracts in ihrer `handoff:`-Sektion:

| Rolle | input_contracts | output_contract | target_roles | output_schema |
|-------|----------------|-----------------|--------------|---------------|
| **orchestrator** | — | `task-spec-v1` | — | — |
| **developer** | `task-spec-v1` | `dev-result-v1` | — | — |
| **requirements** | `ideation-output-v1, task-spec-v1` | `req-output-v1` | developer, tester | — |
| **ideation** | — | `ideation-output-v1` | requirements | `ext/ideation-extension.schema.json` |
| **feature** | `task-spec-v1` | `feature-result-v1` | — | — |
| **tester** | `task-spec-v1, req-output-v1` | `test-result-v1` | — | — |
| **validator** | `task-spec-v1, dev-result-v1` | — | — | `a2a-handoff.schema.json` |
| **code-reviewer** | `dev-result-v1` | `review-output-v1` | developer | `ext/review-extension.schema.json` |
| **ui-ux-designer** | — | `design-spec-v1` | developer | `ext/design-extension.schema.json` |
| **api-specialist** | — | `api-spec-v1` | developer | `ext/api-extension.schema.json` |
| **se-requirements** | `task-spec-v1` | `se-req-output-v1` | se-critic | — |
| **se-architect** | `task-spec-v1` | `se-arch-output-v1` | se-critic | `se-decomposition.schema.json` |
| **se-critic** | `se-arch-output-v1` | `critic-result-v1` | se-architect, se-interface-mgr | — |
| **se-interface-mgr** | `critic-result-v1` | `interface-result-v1` | se-termination | — |
| **se-termination** | `interface-result-v1` | `termination-result-v1` | — | — |
| **se-orchestrator** | `task-spec-v1` | `task-spec-v1` | se-architect, se-requirements | — |

Die `input_schema`- und `output_schema`-Felder referenzieren JSON-Schemas für optionale Schema-Validierung vor/nach Delegation. `target_roles` deklariert die typischen Empfänger — der Orchestrator nutzt dies für dynamisches Routing.

---

*Ende der Bestandsaufnahme*
