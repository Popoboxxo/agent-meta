# CODEBASE_OVERVIEW — agent-meta

> Letzte Aktualisierung: 2026-08-08 (v0.92.0: `howto/`→`docs/guides/`+`docs/se-cascade/`-Pfade korrigiert; Knowledge Engine seit v0.82.0 implementiert, Phase A-C abgeschlossen)

---

## Inhaltsverzeichnis

1. [SE-Agenten-Kaskade](#1-se-agenten-kaskade)
2. [Provider-Expert-Agenten](#2-provider-expert-agenten)
3. [Agent-Templates (1-generic)](#3-agent-templates-1-generic)
4. [Konfiguration](#4-konfiguration)
5. [Schemas](#5-schemas)
6. [Templates](#6-templates)
7. [Howto-Dokumentation](#7-howto-dokumentation)
8. [Model Discovery & Curation (REQ-MOD-01)](#8-model-discovery--curation-req-mod-01)
9. [Scripts](#9-scripts)
10. [Provider Abstraction Layer (PAL)](#10-provider-abstraction-layer-pal)
11. [A2A-Handoff-Protokoll](#11-a2a-handoff-protokoll)
12. [Prompt-Modernisierung (Legacy / Hybrid / Modern)](#12-prompt-modernisierung-legacy--hybrid--modern)
13. [Singleton-Orchestrator-Guard](#13-singleton-orchestrator-guard)
14. [Knowledge Engine](#14-knowledge-engine)

---

## 1. SE-Agenten-Kaskade

Die SE-Agenten-Kaskade ist ein fraktales, rekursives Systems-Engineering-System mit 6 spezialisierten Agenten, die zusammen eine 6-stufige Black-Box → White-Box-Zerlegung koordinieren.

### 1.1 `agents/1-generic/se-orchestrator.md` (deprecated)

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

## 2.5 4-Tier-Developer-System (v0.74.0 — erweitert um ultra-Tier)

Das System wurde vollständig in Orchestrator und Templates integriert. Vier spezialisierte Developer-Agenten mit Eskalations- und De-Eskalations-Protokoll:

### Tier-Übersicht

| Tier | Agent | Modell | Einsatz | Signale | Eskaliert zu |
|------|-------|--------|--------|---------|--------------|
| `fast` | `junior-developer` | Günstiger/Fast | Trivialer Fix ≤2 Dateien, offensichtliche Lösung | Typo, Off-by-one, Config-Wert, Logging, Boilerplate-nach-Vorlage | `developer` ODER `senior-developer` |
| `balanced` | `developer` | Balanced | Standard-Implementierung, klarer Scope | Feature mit Pattern, normaler Bugfix, ≤3 Dateien | `senior-developer` (bei Scope-Überschreitung) |
| `max` | `senior-developer` | Powerful/Max | Architektur-Impact, Risiko, unklare Ursache | API/Schema-Änderung, Cross-Cutting-Refactoring, Race Condition, Security, Performance | `principal-developer` (via dev-review-loop `on_blocked`) |
| `ultra` | `principal-developer` | Ultra (stärkstes Realmodell) | Last-Resort nach wiederholtem senior-developer-Versagen. Root-Cause-Diagnose vor Implementierung mandatiert. `orchestrator_only: true` | Nur über `on_blocked: escalate_to_principal-developer` im dev-review-loop | — (end-of-line) |

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
| `principal-developer.md` | 1.0.0 | read, write, edit, glob, grep | Ultra-Tier: Last-Resort-Eskalation nach wiederholtem senior-developer-Versagen; Root-Cause-Diagnose mandatiert; `orchestrator_only: true` |
| `intern-developer.md` | 1.0.0 | read, glob, grep | Nano-Tier: Easter-Egg/Gag-Agent, read-only, nie für Produktionsarbeit geroutet |
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
| `database-engineer.md` | 1.0.0 | read, write, edit, glob, grep, bash | Powerful-Tier: DB-Schema, backwards-kompatible Migrationen, Query-Optimierung |
| `incident-responder.md` | 1.0.0 | read, glob, grep, bash | Powerful-Tier: Live-Incident-Koordination, RCA (5-Whys/Fishbone), Hotfix-Priorisierung |
| `dependency-auditor.md` | 1.0.0 | read, glob, grep, bash | Balanced-Tier: Supply-Chain-Hygiene, SBOM-Analyse, CVE-Checks, Lizenz-Compliance |
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

### `config/ai-providers.yaml` & Provider Tier Mapping

**Zweck:** Provider-Konfiguration mit Capabilities-Matrix, Settings-Templates und Model-IDs (früher feste Zuordnung, jetzt via Presets).

**Felder pro Provider (Stand v0.66.0):**

| Feld | Typ | Zweck |
|------|-----|-------|
| `agents_dir` | string | Output-Verzeichnis für generierte Agenten |
| `agent_ext` | string | Dateiendung (`.md`) |
| `context_file` | string | Context-Datei (z.B. `CLAUDE.md`) |
| `context_template` | string | Template für Context-Datei |
| `has_rules` / `has_hooks` / `has_commands` / `has_settings` | bool | Feature-Flags |
| `capabilities` | string[] | Capability-Matrix: `agents`, `rules`, `hooks`, `commands`, `settings`, `snippets`, `skills`, `artifacts`, `checkpoints`, `mcp`, `context-managed-block`, `context-embedded-rules` |
| `artifact_dir` | string | Artifact-Verzeichnis (z.B. `.claude/artifacts`) |
| `checkpoint_dir` | string | Checkpoint-Verzeichnis |
| `settings_file` | string | Provider-Settings-Datei (z.B. `.claude/settings.json`) |
| `settings_template` | string | Template für Settings-Datei (z.B. `templates/configs/CLAUDE.settings-template.json`) |
| `settings_local_file` | string | Lokale/persönliche Override-Datei (z.B. `.claude/settings.local.json`) |
| `settings_local_template` | string | Template für lokale Settings |
| `model-tiers` | dict | `nano/fast/balanced/powerful/max` → konkrete Modell-ID |
| `model-aliases` | dict | Kurznamen → Modell-ID |
| `gitignore_entries` | string[] | Einträge für agent-meta managed Block in `.gitignore` |
| `isolation-dirs` | string[] | Verzeichnisse die isoliert werden (Cross-Provider-Contamination-Schutz) |

**Neue Settings-Templates (v0.66.0):**
- `templates/configs/CLAUDE.settings-template.json` — committed settings skeleton
- `templates/configs/CLAUDE.settings-local-template.json` — local/personal overrides (gitignored)

### `config/tier-presets.yaml` (NEU, REQ-MOD-01)

**Zweck:** Globale Tier-Presets mit direktem Modell-Assignment statt indirektem Mapping.

**Format — altes Format (backward-compat):**
```yaml
cheap:
  nano: cheap-nano
  fast: cheap-fast
  mapping:  # fallback layer
    nano: nano-tier
    fast: fast-tier
```

**Format — neues Format (direkt, REQ-MOD-01):**
```yaml
cheap:
  tiers:
    nano: openai/gpt-4-mini
    fast: openrouter/mistral/mistral-7b
    balanced: anthropic/claude-3-haiku
    powerful: anthropic/claude-3.5-sonnet
    max: anthropic/claude-opus
```

**5 vordefinierte Presets:**
1. `cheap` — günstigste echte Modelle pro Tier
2. `normal` — balanced Preis/Performance
3. `advanced` — stärkere Modelle, höhere Kosten
4. `expensive` — max Kosten, max Performance
5. `expensive-as-hell` — Claude max + Opus wo verfügbar

**Preset-Auflösung (resolve_model):**
1. Schaue `project.yaml:tier-preset` (project-lokal, überschreibt global)
2. Lade Preset aus `tier-presets.yaml:tiers` oder fallback `mapping`
3. Wenn Preset hat `tiers.tier` → direkt Model-ID
4. Sonst: versuche `mapping` oder fallback zu `role-defaults.yaml:tiers`
5. SE-Rollen upgrade: +1 Tier via SE-Prefix (balanced → powerful, etc.)

### `config/pricing-overlay.yaml` & `config/generated/model-registry.json`

**Pricing Overlay:** Manueller Überschreib-Mechanismus für Preise. API-Preise werden bevorzugt, außer Overlay definiert einen eigenen Preis (z.B. 0.00$ für Zen-Subscriptions). Preise können direkt in der Admin-UI editiert werden.

**Model Registry:** Cacht die dynamisch von OpenRouter/Zen/Go abgerufenen Modelle (406 Modelle). Produziert von `sync.py --update-models`.

### Backup-Konfiguration (Phase 6 — v0.68.0)

**Zweck:** Automatische Versionierung von Konfigurationsdateien vor Änderungen über die Admin-UI.

**Konfiguration in `.meta-config/project.yaml`:**
```yaml
backup:
  retention:
    max_backups: 10          # maximale Anzahl Backups speichern
    max_age_days: 30         # alte Backups nach N Tagen löschen
  enabled: true              # default: true
```

**Backup-Verzeichnis:** `.meta-config/backups/` 
- Archivformat: `config-YYYYMMDD-HHMMSS.tar.gz`
- Enthält: `.meta-config/project.yaml` + `config/role-defaults.yaml` (vom Sync)

**Endpunkte für Admin-UI:**
- `GET /api/backups` — Liste aller verfügbaren Backups
- `POST /api/backups/create` — Neues Backup erstellen
- `POST /api/backups/restore` — Aus Backup wiederherstellen
- `DELETE /api/backups/<archive>` — Backup löschen

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

### 5.6 `schemas/se-orchestrator.schema.json` (Existierend, deprecated)

**Zweck:** Orchestrierungs-Metadaten (deprecated � Funktionalit�t jetzt im Haupt-orchestrator SE-Mode). **Bleibt unverändert** — wird als `payload` in A2A-Envelope eingebettet.

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

### `docs/se-cascade/se-workflow.md` (181 Zeilen)

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

### `docs/se-cascade/se-blackbox-to-whitebox.md` (154 Zeilen)

**Zweck:** Erklärung des zentralen BB → WB-Übergangs mit 7-Schritte-Methode, Beispiel (Wassererhitzungssystem), Regeln und Critic-Checkliste.

**Inhalt:**
- Black-Box vs. White-Box Definition
- 7 Schritte des Architects
- Vollständiges Beispiel mit Mermaid-Diagramm
- 6 Regeln für den Übergang
- Häufige Fehler-Tabelle
- Critic-Checkliste (8 Punkte)

### `docs/se-cascade/se-interface-management.md` (190 Zeilen)

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

### `docs/se-cascade/se-mcp-adapters.md` (250 Zeilen)

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

## 8. Model Discovery & Curation (REQ-MOD-01)

### 8.1 `scripts/lib/model_discovery.py`

**Version:** 1.0.0 (neu in v0.65.0)
**Beschreibung:** Keyless API-basierte Modell-Discovery von OpenRouter (338 Modelle), OpenCode Zen (48 Modelle) und OpenCode Go. Schreibt ein dedupliziertes Registry nach `config/generated/model-registry.json` mit Fallback bei Netzwerkausfällen.

**Exportierte API:**

| Funktion | Signatur | Zweck |
|----------|----------|-------|
| `fetch_openrouter_models` | `(blacklist: List[str] \| None) → List[Dict]` | OpenRouter keyless Endpoint (`https://openrouter.ai/api/v1/models`), Provider-Attribution via ID-Präfix, Preise in `pricing.prompt`/`completion` |
| `fetch_opencode_zen_models` | `(blacklist: List[str] \| None) → List[Dict]` | OpenCode Zen Endpoint (`https://opencode.ai/zen/v1/models`), IDs namespaced als `opencode/<raw_id>` |
| `fetch_opencode_go_models` | `(blacklist: List[str] \| None) → List[Dict]` | OpenCode Go Endpoint (`https://opencode.ai/zen/go/v1/models`), IDs als `opencode-go/<raw_id>` |
| `discover_models` | `(_project_root: str \| None) → Dict` | Orchestriert alle Fetcher, dedupliciert nach ID, appliziert Registry-Guard (min. 10 Modelle) |
| `_load_blacklist` | `(project_root: str) → List[str]` | Lädt `config/model-curation.yaml` → `blacklist` Sektion |

**Kritische Flows:**

1. **Network-resilience:** Jeder Fetcher returniert `[]` bei HTTP/Parse-Fehler → `discover_models` merged mit leerer Liste
2. **Registry Guard:** Falls Discovery < 10 Modelle zurückgibt, preserviert existentes Registry (Netzwerkausfall-Schutz)
3. **Deduplication:** Sorted nach ID, erste Occurrence wins (kein Merge von Duplikaten)
4. **Blacklist-Integration:** Modelle in `config/model-curation.yaml:blacklist` werden gefiltert WÄHREND Discovery (nicht nachträglich)

**Provider Attribution (REQ-MOD-01):**
- OpenRouter: Prefix vor erstem `/` ist Provider (`qwen/qwen3` → `qwen`)
- OpenCode Zen: Alle als `opencode-zen` (später merged zu `opencode`)
- OpenCode Go: Alle als `opencode-go` (später merged zu `opencode`)

### 8.2 `scripts/lib/curation.py` (NEU)

**Version:** 1.0.0
**Beschreibung:** Typsichere Curation-File-Verwaltung mit Fallback auf Default-Dicts bei fehlender/malformed YAML.

**Exportierte API:**

| Funktion | Signatur | Zweck |
|----------|----------|-------|
| `load_curation` | `(root: str) → Dict[str, List[str]]` | Lädt `config/model-curation.yaml`, returns `{"blacklist": [...], "disabled": [...]}` oder Default `{}` |
| `save_curation` | `(root: str, data: Dict) → None` | Schreibt Curation-Datei atomar (temp → rename) mit PyYAML |
| `_normalize` | `(data: Any) → Dict[str, List[str]]` | Coercion zu kanonischer Form (nur `blacklist` + `disabled`, beide Lists) |
| `_default` | `() → Dict[str, List[str]]` | Fresh copy der Default-Struktur |

**Curation-Semantik:**
- `blacklist` — hard exclusion, gefiltert während Discovery, nie in Registry
- `disabled` — soft exclusion, in Registry aber hidden in Admin-UI Dropdowns/Pickers
- **Fallback:** Beide Listen default zu empty `[]`, so Callers brauchten nicht auf fehlende YAML zu prüfen

### 8.3 `config/model-curation.yaml` (NEU)

**Zweck:** Single source of truth für Modell-Sichtbarkeit (Blacklist + Disabled).

**Format:**
```yaml
blacklist:
  - google/gemini-3.1-flash-image  # entfernt während discovery
  - google/gemini-3-pro-image
disabled: []                         # hidden in UI, aber in registry
```

**Migrationspfad:** Legacy `pricing-overlay.yaml:excluded_models` wurde nach `blacklist` migriert (2026-06-21).

### 8.4 `config/generated/model-registry.json` (NEU, generiert)

**Zweck:** Cache der echten Modelle von OpenRouter + Zen + Go. Produziert von `sync.py --update-models` via `model_discovery.discover_models()`.

**Schema:**
```json
{
  "models": [
    {
      "id": "openrouter/anthropic/claude-3.5-sonnet",
      "name": "Claude 3.5 Sonnet",
      "provider": "anthropic",
      "input_cost_api": 3.0,        // Million-Token-Äquiv., z.B. 0.003 = 3.0
      "output_cost_api": 15.0,
      "context_length": 200000,
      "tier": "Standard"
    }
  ]
}
```

**Fakten:**
- 406 echte Modelle nach Dedup (38 OpenRouter-Provider, 48 Zen, max ~9 Go)
- Preise von OpenRouter API oder `config/pricing-overlay.yaml` (Overlay wins)
- Admin-UI lädt Registry und zeigt `[API]` / `[Overlay]` / `[Calc]` Badges pro Modell

---

## 9. Scripts

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

### `scripts/lib/config.py` — `build_variables()`

**Zweck:** Zentrale Template-Variablen-Auflösung für alle Placeholder-Substitutionen in Agent-Templates.

**Neue Platzhalter (Phase 6 — Token Efficiency):**

| Platzhalter | Typ | Beschreibung |
|-------------|-----|-------------|
| `ORCH_MODE_DISABLED` | bool | Orchestrator komplett deaktiviert (statt {{#if}} Nesting) |
| `ORCH_MODE_STRICT` | bool | Orchestrator aktiv + strict mode (immer delegieren) |
| `ORCH_MODE_ADVISORY` | bool | Orchestrator aktiv + advisory mode (Main-Chat kann fallback nutzen) |
| `AGENT_HINTS_CLAUDE` | string | Agent-Hints ohne Tabelle (für Claude native agent injection) |
| `A2A_HANDOFF_BLOCK` | string | A2A-Envelope-Dokumentation (leer wenn deaktiviert) |
| `SE_MODE_BLOCK` | string | SE-Mode-Sektion aus `snippets/orchestrator/se-mode.md` |
| `A2A_PROTOCOL_BLOCK` | string | A2A-Protokoll-Sektion aus `snippets/orchestrator/a2a-protocol.md` |
| `CHECKPOINTING_BLOCK` | string | Checkpointing-Sektion aus `snippets/orchestrator/checkpointing.md` |
| `QUALITY_PIPELINES_BLOCK` | string | Quality-Pipelines-Sektion aus `snippets/orchestrator/quality-pipelines.md` |

**Flat-Mode-Flags (statt nested {{#if}}/{{else}}):**
- Genau ein ORCH_MODE_*-Flag ist `true`, alle anderen `false`
- Ermöglicht deterministische Conditional Stripping ohne Nesting-Risiken
- Auflösung aus orchestrator-Block in project.yaml

**Lazy-Loaded Snippets:**
Template-Inhalte für SE-Mode, A2A-Protokoll, Checkpointing und Quality-Pipelines werden zur Build-Zeit aus `snippets/orchestrator/<name>.md` geladen, statt hardcodiert in Agents zu stehen. Bei Deaktivierung werden die Variablen leer (""), so Conditional Stripper können sie zuverlässig entfernen.

**hint/description-Deduplication:**
Redundante `hint`-Felder werden automatisch aus Agent-Frontmattern gelöscht wenn identisch mit `description` (Zeile 220-227 in agents.py). AGENT_HINTS wird immer aus Quell-Templates gebaut (nicht aus generierten Dateien), daher keine Token-Verschwendung.

### `scripts/admin-server.py` & `docs/admin-ui.html` (Phase 5: CRUD + Reflection + Model Mapping)

**Zweck:** Interaktive webbasierte Admin UI für Modell-Management, Provider-Config, Tier-Presets, Pricing, Quality Pipelines, Reflection Pairs, Prompt Modes und Agent→Model-Mapping.
**Architektur:** Single-File Frontend (`docs/admin-ui.html`, Vanilla JS, Zero Dependencies) + Python-Backend (`scripts/admin-server.py`).

**Bestehende Sektionen (REQ-MOD-01):**

| Sektion | Features | Button-Flow |
|---------|----------|------------|
| **Models & Pricing** | Sortierbare Tabelle (400+ Modelle), Filter-Strip (Claude/OpenCode/GitHub/OpenAI/Google), Preis-Heatmap, `[API]`/`[Overlay]`/`[Calc]` Badges | Edit → Save/Cancel, Enable/Disable/Blacklist per Modell, Crawl Button |
| **Provider Tier Mappings** | Per-Provider Datalist-Filtering, display-name Anzeige | Edit → Save/Cancel |
| **Tier Presets** | 2 Tabs: **Resolved View** (aktuell aufgelöste Modelle) + **Edit Mappings** (direkte Modell-Inputs), Tier-Dropdown-Picker | Save/Cancel, Quick-Preset-Switcher |
| **Project General** | tier-preset Dropdown (fixed), Global Framework Setup Link | Edit → Save/Cancel |
| **AI Providers** | Project Tier Override Panel | Enable/Disable pro Provider |

**Neue CRUD-Endpunkte (Phase 5 — v0.66.0 + Phase 6 — v0.68.0 Backups):**

| Endpunkt | Methoden | Zweck |
|----------|----------|-------|
| `/api/pipelines` | `GET` · `PUT` | Liste aller Quality Pipelines lesen / ersetzen |
| `/api/pipelines/{name}` | `GET` · `PUT` · `DELETE` | Einzelne Pipeline lesen / anlegen/aktualisieren / löschen |
| `/api/reflection-pairs` | `GET` · `POST` · `PUT` | Liste aller Reflection Pairs lesen / neu anlegen (mit auto-generierter ID) / ersetzen |
| `/api/reflection-pairs/{id}` | `GET` · `PUT` · `DELETE` | Einzelnes Pair lesen / aktualisieren / löschen |
| `/api/prompt-modes` | `GET` · `PUT` | Prompt-Mode-Config (`agent-prompts` Block) lesen / schreiben |
| `/api/prompt-modes/roles/{role}` | `GET` · `PUT` · `POST` · `DELETE` | Prompt-Mode-Override für eine Rolle setzen / löschen |
| `/api/model-mapping` | `GET` | Matrix: Rolle × Provider → resolved model ID + source |
| `/api/backups` | `GET` · `POST` | Liste aller Config-Backups lesen / neue Backup erstellen |
| `/api/backups/<archive>` | `DELETE` | Backup löschen |
| `/api/backups/restore` | `POST` | Konfiguration aus Backup wiederherstellen |

**Neue UI-Pages (Phase 5):**

| Page | Route | Beschreibung |
|------|-------|-------------|
| **Reflection Pairs** | `/reflection-pairs` | CRUD-Oberfläche für Generator-Critic-Paare (z.B. developer↔code-reviewer) mit `max_iterations` und `enabled`-Flag |
| **Model Mapping** | `/model-mapping` | Lese-Ansicht der aufgelösten Modelle pro Rolle und Provider — Zellen zeigen Modell-ID + Source (`role-default`, `explicit-override`). Write-Overrides via `/api/config/project/section` oder `/api/models/update` |

**Hilfsmethode `_update_role_defaults_section()`:**

Ersetzt einen einzelnen Top-Level-YAML-Schlüssel in `config/role-defaults.yaml` kind-spezifisch: unveränderte Pipelines oder Reflection-Pair-Einträge behalten ihre ursprüngliche Formatierung und Kommentare bei. Nur geänderte oder neue Kinder werden mit PyYAML neu serialisiert. Kommentare, Leerzeilen und andere Top-Level-Sektionen außerhalb der bearbeiteten Sektion bleiben ebenfalls erhalten.

```python
def _update_role_defaults_section(self, key: str, value: Any) -> dict:
    # Regex extrahiert den Sektions-Body
    # Kinder werden einzeln geparst und nur bei Änderung neu gedumpt
    # Backup + atomares replace
```

**Agent→Model-Mapping-Endpunkt (`/api/model-mapping`):**

Ruft `lib.roles.resolve_model()` für jede aktive Rolle × Provider-Kombination auf. Pro Zelle wird zurückgegeben:
- `model_id` — die aufgelöste konkrete Modell-ID
- `source` — `"role-default"`, `"explicit-override"` oder `"fallback"`

Die Auflösungslogik ist identisch mit der in `scripts/lib/agents.py` (`_compose_agent()`).

**UI Patterns (REQ-MOD-01):**
1. **Quick-Filter Strip** oben in Models-Tabelle → Click-to-filter nach Provider
2. **Enable/Disable/Blacklist Row Buttons** statt Inline-Checkboxen → weniger Jitter, bessere UX
3. **Datalist-Filtering** in Provider-Mappings → zeigt nur verfügbare Modelle per Provider
4. **Resolved View Tab** → Users sehen aktuell aufgelöste Modelle VOR Bearbeitung

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

### `scripts/lib/mcp.py`

**Zweck:** Zentrale Verwaltung und Generierung der MCP-Server-Integrationen aus der `config/mcp-registry.yaml`.

**Hauptfunktionen:**
- `load_mcp_registry()`: Lädt und mergt globale und projektspezifische MCP-Registries.
- `resolve_active_mcp_servers()`: Bestimmt aktive Server (explizit aus `project.yaml` und implizit über Provider-Defaults).
- `generate_mcp_artifacts()`: Generiert Markdown-Regeldateien (`mcp-<server>.md`) pro Provider und fügt Provider-Konfigurationen (`mcpServers` in `.mcp.json` für Claude, providerspezifisch für andere) ein.
- `sync_secrets_template()`: Erstellt bzw. ergänzt bei jedem Sync-Lauf die lokale, gitignorierte `.meta-config/secrets.local.yaml` um die Secret-Keys aller aktiven MCP-Server (z.B. API-Keys) — neu aktivierte Server bekommen ihre fehlenden Keys automatisch angehängt, bestehende Werte bleiben unangetastet.

**Integrierte MCP-Server (Registry):**
- **ReqogniLoom:** Plattform für Requirements-Engineering, Architektur, Tests und Traceability (via SSE).
- **Honcho:** Lokaler Memory- und Kontext-Server für persistente Cross-Session-Speicherung (via SSE).
- **Home Assistant:** Smart Home Integration (Read-only).
- **InfluxDB:** Zeitreihendaten-Analyse (Read-only via Flux).
- **Playwright:** E2E-Tests und Browser-Automatisierung.
- Weitere System-MCPs wie `viz-logger` und `a2a-handoff`.

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

## 10. Provider Abstraction Layer (PAL)

Der Provider Abstraction Layer (PAL) isoliert generische Agent-Templates von provider-spezifischer Delegationssyntax. Er verhindert "Syntax Leaks" und handhabt provider-spezifische Bootstrap-Mechanismen.

### 10.1 `config/delegation-syntax.yaml` — Provider-Delegation Syntax Registry

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

### 10.2 `config/provider-capabilities.yaml`

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

### 10.3 `config/provider-bootstrap.yaml`

**Zweck:** Definiert Registrierungsmechanismus pro Provider.

**Mechanismen:**

| Mechanismus | Provider | Aktion |
|-------------|----------|--------|
| `file-based` | Claude, Opencode, Copilot | `none` — Auto-Discovery |
| `api-based` | Gemini | `inject-bootstrap-instructions` in GEMINI.md |
| `config-based` | Continue | `update-config` in `.continue/config.yaml` |

### 10.4 `scripts/lib/delegation_syntax.py`

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

### 10.5 `scripts/lib/bootstrap.py`

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

### 10.6 `templates/bootstrap/gemini-session-bootstrap.md`

**Zweck:** Bootstrap-Template für Gemini/Antigravity Session-Start.

**Inhalt:**
- Erklärung warum Bootstrap nötig ist (keine dateibasierte Registry)
- 4-Schritte-Workflow: Dateien einlesen → define_subagent → Orchestrator zuerst → Anfragen bearbeiten
- Hinweise: Ephemere Registrierung, Version-Abhängigkeit von sync.py, Konsequenzen ohne Bootstrap

### 10.7 `scripts/lib/context.py` — Provider-Kontext-Management (Phase 5 Refactoring)

**Zweck:** Erzeugen und Aktualisieren von provider-spezifischen Context-Dateien (CLAUDE.md, GEMINI.md, AGENTS.md, .continue/rules/project-context.md), Settings-Dateien und `.gitignore`-Managed-Blöcken.

**Capability-Driven Dispatch (`sync_context_for_provider()`):**

Die Dispatch-Logik verwendet die `capabilities`-Matrix aus `config/ai-providers.yaml` statt hartkodierter Provider-Namen:

| Capability | Strategie | Betroffene Provider |
|------------|-----------|-------------------|
| `context-embedded-rules` | Opencode-Strategie: Regeln in AGENTS.md managed block | Opencode |
| `provider == "Continue"` | Continue-Strategie: project-context.md + config.yaml comment block | Continue |
| `context-managed-block` | Generische HTML-Managed-Block-Strategie | Claude, Gemini |

**Neue Initialisierungs-Funktionen (v0.66.0, provider-config-getrieben):**

| Funktion | Signatur | Zweck |
|----------|----------|-------|
| `init_settings_json()` | `(agent_meta_root, project_root, log, dry_run, providers, provider_config, variables)` | Erstellt committed Settings-Dateien für alle aktiven Provider aus deren `settings_template` |
| `init_settings_local_json()` | `(agent_meta_root, project_root, log, dry_run, providers, provider_config, variables)` | Erstellt lokale/persönliche Settings-Dateien aus `settings_local_template` (gitignored) |
| `only_variables()` | `(project_root, variables, log, dry_run, providers, provider_config)` | Substituiert `{{VARIABLE}}`-Platzhalter in bestehenden Context-Dateien |
| `ensure_gitignore_entries()` | `(project_root, log, dry_run, gitignore_entries, exact_entries)` | Stellt agent-meta Managed-Block in `.gitignore` sicher (additiv oder exakt) |

**Provider-Eigenschaften (`_init_provider_settings_json()`):**
- Liest `settings_file` und `settings_template` aus `config/ai-providers.yaml`
- Template-Substitution via `substitute()` — Variablen werden eingesetzt
- Fallback auf minimales JSON/YAML-Skelett wenn Template fehlt

### 10.8 Integration in `scripts/lib/agents.py`

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

## 11. A2A-Handoff-Protokoll

> **Status:** Vollständig implementiert (Phasen 1–4) — 22 Dateien, 818 Zeilen
> **Basiert auf:** [GitHub Issue #212](https://github.com/Popoboxxo/agent-meta/issues/212) — W3C ANP White Paper
> **Dokument:** `docs/concepts/a2a-handoff-protocol.md`
> **Analyse:** `docs/concepts/archive/2026-06-a2a-best-practice-analysis.md`

### 11.1 Prinzip: A2A als EINZIGES Format

**A2A-Envelopes sind das einzige Format für Agent-zu-Agent-Daten.** Natural-Language-Prompts zwischen Agenten werden vollständig durch strukturierte Envelopes ersetzt. Dies eliminiert Context Loss, ermöglicht deterministische Validierung und schafft lückenloses Supersession-Tracking.

Ausnahme: Continue/Copilot (`structured_handoff: false`) erhalten einen YAML-Text-Block statt JSON — identisches Konzept, anderes Transport-Format.

### 11.2 Kernkonzepte

| Konzept | Beschreibung |
|---------|-------------|
| **A2A-Envelope** | Standardisierter JSON-Wrapper mit Metadaten — das **einzige** Austauschformat |
| **TaskSpec** | Universelles Kern-Payload-Schema für 60-80% aller Delegationen (kurze Feldnamen) |
| **Extensions** | 4 domain-spezifische Erweiterungen zu TaskSpec (Ideation, Design, API, Review) |
| **compact_mode** | Envelope-Flag: `true` = kurze Payload-Namen (Token-sparend), `false` = lesbare Namen |
| **Supersession** | Version-Tracking mit `history[]`-Array für vollständige Revisionsketten |
| **Contract** | Jede Route deklariert Schema + Extension + compact_mode in der Routing-Tabelle |
| **Delegation Gates** | Anti-Re-Delegation: `delegation_depth` (konfigurierbar via `project.yaml`, Default 10), Self-Handoff-Verbot (`source_agent ≠ target_agent`), T-Size-Limit, Re-Delegation-Detection — 4 Hard-Reject-Gates in `rules/1-generic/a2a-delegation-gates.md` |

### 11.3 A2A vs. viz-Debug — Separate Konzepte

Das A2A-Protokoll und der viz-Handshake sind **separate Systeme** mit loser Kopplung:

| Ebene | System | ID | Default | Token-Kosten |
|-------|--------|-----|---------|-------------|
| **Data Contract Layer** | A2A-Envelope | `handoff_id` | **Immer aktiv** | Envelope-Overhead (~60 Tokens) |
| **Operational Layer** | viz-Handshake | `viz_task_id` | Aktiv (basic) | 0 (MCP-basiert) |
| **Debug-Ebene** | viz A2A-Events | `viz_task_id` | **AUS** (`viz.debug: false`) | 0 Tokens |

**Lose Kopplung via `trace_context.viz_task_id`** — das einzige Feld das beide Systeme verbindet. Der A2A-Envelope funktioniert vollständig ohne viz, und viz funktioniert ohne A2A.

### 11.4 Schema-Strategie: 1 Core + 4 Extensions + 1 SE

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

### 11.5 Orchestrator als Envelope-Fabrik

Der Orchestrator ist der primäre Envelope-Produzent:

| Orchestrator-Funktion | A2A-Rolle |
|-----------------------|-----------|
| Intent-Routing | Bestimmt `target_agent` + `schema_ref` + `compact_mode` aus Routing-Tabelle |
| FANOUT | Produziert N parallele Envelopes mit gemeinsamem `trace_context.trace_id` |
| BARRIER | Konsumiert Response-Envelopes, aggregiert Ergebnisse |
| PIPELINE | Verkettet Envelopes via `trace_parent` |
| REPEAT_UNTIL | Managed Supersession-Ketten via `supersession.history[]` |

### 11.6 Provider-Matrix: Transport-Format

| Provider | structured_handoff | handoff_format | Envelope-Transport |
|----------|-------------------|----------------|-------------------|
| Claude | `true` | `json` | JSON im Task-Tool-Prompt |
| Opencode | `true` | `json` | JSON im task()-Prompt |
| Gemini | `true` | `json` | JSON im define_subagent-Prompt |
| Continue | `false` | `yaml_text_block` | YAML-Block im Prompt-Text |
| Copilot | `false` | `yaml_text_block` | YAML-Block im Prompt-Text |

### 11.7 Token-Budget & Optimierungen

| Optimierung | Ersparnis | Status |
|-------------|-----------|--------|
| Kurze Payload-Feldnamen (TaskSpec + Extensions) | 20–50 Tokens/Handoff | ✓ Umgesetzt |
| `schema_ref` optional (implizit aus Route) | ~20 Tokens | ✓ Im Schema |
| `protocol_version` default = aktuell | ~9 Tokens | ✓ Konvention |
| `compact_mode`-Flag zur Steuerung | — (schaltet #1) | ✓ Im Envelope |
| viz.debug: false (default) | 30 Tokens/Handoff | ✓ In Config |

### 11.8 Betroffene Artefakte

| Artefakt | Änderung | Status |
|----------|----------|--------|
| `schemas/a2a-handoff.schema.json` | Envelope: `batch`, `retry_count`, `requires_human_approval`, `negotiated_format`, `supersession.history[]`, `delegation_depth` (required, max 50) | ✓ Phase 1 (erweitert) |
| `schemas/handoffs/task-spec.schema.json` | Universelles Kern-Payload (NEU) — kurze Feldnamen | ✓ Phase 1 |
| `schemas/handoffs/ext/*.schema.json` | 4 Extensions (NEU): Ideation, Design, API, Review | ✓ Phase 1 |
| `schemas/se-decomposition.schema.json` | **Unverändert** — in Envelope eingebettet | — |
| `schemas/se-orchestrator.schema.json` | **Unverändert** — in Envelope eingebettet | — |
| `.meta-config/project.yaml` | `orchestrator.handoff`-Block + `viz.debug` + `viz.a2a_events` | ✓ Phase 1 |
| `docs/concepts/a2a-handoff-protocol.md` | Implementation-nahes Konzept (v2.0, 872 Zeilen) | ✓ Phase 1 |
| `docs/CODEBASE_OVERVIEW.md` | Abschnitte 5 + 10 aktualisiert | ✓ Phase 1 |
| `rules/1-generic/a2a-delegation-gates.md` | Anti-Re-Delegation Gates: Self-Handoff-Verbot, Tiefenlimit, T-Size-Limit, Re-Delegation-Detection | ✓ Phase 4 (erweitert) |
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

### 11.9 Roadmap

| Phase | Inhalt | Status |
|-------|--------|--------|
| 1 — Konzept + Schemas | Core-Schema + 4 Extensions + Envelope-Anpassungen + Config + Doku | ✓ Abgeschlossen |
| 2 — Provider-Capabilities | `{{PAL_HANDOFF}}`-Platzhalter + `structured_handoff`-Flags + delegation-syntax.yaml | ✓ Abgeschlossen |
| 3 — Agent-Updates | Orchestrator-Envelope-Fabrik + handoff-Contracts + ideation, feature, developer, SE-Agenten | ✓ Abgeschlossen |
| 4 — MCP & Tooling | MCP-Tools (resolve-handoff-schema, validate-handoff, resolve-handoff) + viz-Integration | ✓ Abgeschlossen |

### 11.10 Handoff-Contracts in `config/role-defaults.yaml`

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

Die `input_schema`- und `output_schema`-Felder referenzieren JSON-Schemas für optionale Schema-Validierung vor/nach Delegation. `target_roles` deklariert die typischen Empfänger — der Orchestrator nutzt dies für dynamisches Routing.

---


## 13. Singleton-Orchestrator-Guard

**Eingeführt:** v0.65.1 (2026-06-30) — Branch `feat/orchestrator-singleton-guard`
**Session-Fix:** 2026-07-01 (Commit 139eab7) — HITL-Gate-Deadlock behoben

**Problem:** 
1. Opencode-Worker-Agents konnten mehrere Orchestrator-Instanzen spawnen → Routing-Konflikte.
2. HITL-Gates ("Destruktive Aktionen IMMER bestätigen") machten User-Freigaben via main_chat ungültig → Endlos-Bestätigungsschleife.

**Lösung:**
- Body-Constraint-Injection in alle Worker-Agenten + Gate #5 in A2A-Delegation-Gates
- main_chat als legitimer User-Proxy etabliert — seine relayten Freigaben zählen

### 13.1 Durchsetzungs-Mechanismus

| Schicht | Datei | Mechanismus |
|---------|-------|-------------|
| Gate #5 (Doku) | `rules/1-generic/a2a-delegation-gates.md` | HARD REJECT bei `subagent_type="orchestrator"` durch Worker |
| Body-Constraint | `scripts/lib/agents.py` (sync) | `SINGLETON_CONSTRAINT_BLOCK` wird in alle Worker-Agenten injiziert |
| Orchestrator-Doku | `agents/1-generic/orchestrator.md` | Singleton-Regel in `<persona>` + Bullet in Anti-Recursion-Sektion |
| Projekt-Hinweis | `CLAUDE.md` | Singleton-Regel nach Rollen-Tabelle |
| HITL-Gate-Fix | `agents/1-generic/orchestrator.md` | main_chat als User-Proxy: "seine Anweisungen und relayten Freigaben tragen User-Autorität" |

### 13.2 Singleton-Regel

> **NUR der `main_chat` darf den `orchestrator` spawnen.**
> Worker-Agents (`delegation_depth >= 2`) dürfen `task(subagent_type="orchestrator", ...)` NIEMALS aufrufen.

### 13.3 HITL-Gate-Deadlock-Fix (Session 2026-07-01)

**Problem:** Orchestrator-Dokumentation sagte "Destruktive Aktionen IMMER bestätigen — auch bei explizitem Befehl". Das machte relayten User-Freigaben durch main_chat ungültig → User hatte keinen direkten Kanal zum Orchestrator, nur indirekt via main_chat → Deadlock.

**Lösung:** Orchestrator erkennt main_chat als User-Proxy an:
- main_chat ist der autorisierte User-Vertreter
- main_chat Anweisungen ("mach jetzt") zählen als gültige Freigabe
- Orchestrator warnt für destruktive Ops TROTZDEM, respektiert aber main_chat-Freigabe
- Schutzwirkung bleibt (Agenten-to-Agenten Freigaben sind weiter ungültig)

- `agents/1-generic/orchestrator.md`: "<persona>"-Block nennt main_chat explizit

Konzept: `docs/concepts/active/singleton-orchestrator-architecture.md`

---

## 14. Knowledge Engine

**Eingeführt:** v0.82.0 (2026-07-24) — Branch `main` (gemergt aus `feat/knowledge-engine-phase-abc`)
**Status:** Vollständig implementiert, Phase A (Scaffolding) + B (Agenten + Routing) + C (AdminUI) abgeschlossen.

Die Knowledge Engine ist ein **optional per Schalter aktivierbares Wissensmanagement-System**, das Karpathys LLM-Wiki-Pattern und Googles Open Knowledge Format (OKF v0.1) fusioniert. Die Engine liefert **7 spezialisierte Agenten** aus, die von der Erstmigration bis zur täglichen Wissens-Pflege spezialisierte Arbeiten übernehmen.

**Designprinzipien:**
- **Zero-Overhead-Garantie:** Agenten werden nur generiert wenn der Schalter aktiv ist (analog SE-Kaskade)
- **Zwei bewusste Abweichungen vom Konzept-Dokument:**
  - Templates `knowledge-index.template.md`/`knowledge-log.template.md` existieren NICHT als Dateien — Inhalte werden zur Laufzeit in `scripts/lib/knowledge.py` generiert (Funktionen `generate_initial_index()` / `generate_initial_log()`)
  - `config/knowledge-presets.yaml` existiert NICHT — 6 Domain-Presets liegen **inline** als JavaScript-Objekt `const PRESETS = {...}` in `docs/ui/admin-ui.html`
- **Framework-Integration:** Realisiert in allen 22 bestehenden Framework-Mechanismen (DoD, Orchestrator-Routing, Hooks, MCP, Lifecycle-Tasks, etc.)

### 14.1 Die 7 Agenten

**Agenten-Rollen (neu in `agents/1-generic/`):**

| Datei | Version | Tier | Beschreibung |
|-------|---------|------|-------------|
| `knowledge-curator.md` | 1.0.0 | balanced | Überwacht Knowledge-Bundle-Gesundheit: Findung von Widersprüchen, veralteten Claims, Orphan-Seiten, fehlenden Concepts. Integration in Lint-Workflows. |
| `knowledge-ingestor.md` | 1.0.0 | balanced | Migriert externe Quellen (Artikel, Papiere, Bilder, Daten) in Bundle-Struktur: Summary schreiben, Entity-/Concept-/Topic-Seiten aktualisieren, Index/Log pflegen. |
| `knowledge-querier.md` | 1.0.0 | balanced | Antwortet auf Fragen durch Index-Navigieren, Seiten-Drilling, Synthese mit Citations. **File-Back:** Gute Antworten werden als neue Wiki-Seiten abgelegt (Wissen compoundiert). |
| `knowledge-linter.md` | 1.0.0 | fast | Automatisierte Formatkontrolle: Frontmatter-Validierung, Dead Links, Markdown-Syntax, OKF-Konformität. Schnelle asynchrone Checks, kein LLM-Reasoning. |
| `knowledge-indexer.md` | 1.0.0 | fast | Generiert/aktualisiert `index.md` und `log.md` in OKF-Format. Parsinglogik via `grep "^## \["` für chronologische Einträge. |
| `knowledge-gardener.md` | 1.0.0 | balanced | Proaktive Wartung: Obsolete Seiten archivieren, Konzept-Verzeichnung erweitern, Verlinkung optimieren, periodische Knowledge-Kompression. |
| `knowledge-migrator.md` | 1.0.0 | balanced | Basis-Initialisierer: Neue Bundle-Struktur scaffolden, Bestands-Wikis migrieren (z.B. Obsidian → OKF), Domänen-Concept-Types definieren. |

**Routing im Orchestrator (per `{{#if KNOWLEDGE_ENGINE_ENABLED}}`):**
- `query` über Knowledge-Bundle → `knowledge-querier`
- `lint` Knowledge-Bundle → `knowledge-linter`
- `ingest` externe Quelle → `knowledge-ingestor`
- `curate` oder `health-check` → `knowledge-curator`
- Komplexe Domain-Setup-Anfrage → `knowledge-migrator`
- Archivieren/Kompression → `knowledge-gardener`
- Index/Log aktualisieren → `knowledge-indexer`

### 14.2 Aktivierungsmechanismus

**Konfiguration in `.meta-config/project.yaml`:**

```yaml
knowledge-engine:
  enabled: true                      # Aktiviert Agenten-Generierung + Routing
  domain: research                   # Domain aus DOMAIN_CONCEPT_TYPES
  bundle_path: docs/knowledge        # Wo soll Bundle liegen?
  bundle_init_template: default      # Aus PRESETS: default, minimal, advanced, research, business
```

**Konfigurierbare Domänen (in `scripts/lib/knowledge.py:DOMAIN_CONCEPT_TYPES`):**

| Domain | Concept Types | Anwendungsfall |
|--------|---------------|----------------|
| `research` | paper, finding, method, dataset | Wissenschaftliche Literatur, Papers, Forschungsergebnisse |
| `personal` | person, event, place, memory | Persönliches Tagebuch, Ziele, Selbstverbesserung |
| `business` | customer, deal, product, decision | Geschäftsmodelle, Kunden, Projekte, Geschäftsentscheidungen |
| `book` | character, location, theme, chapter | Buchanalyse, Roman-Handlung, Charakterentwicklung |
| `custom` | concept | Generische Fallback-Domain |

**Auswirkungen bei Aktivierung:**
1. `sync.py` generiert 7 Knowledge-Agenten-Dateien in `.claude/agents/`
2. `scripts/lib/delegation_table.py:generate_intent_routing_table()` injiziert Knowledge-Intent-Routen (gated per `KNOWLEDGE_ENGINE_ENABLED`)
3. `admin-server.py` allowlisted Knowledge-Engine-Config-Writes
4. `docs/ui/admin-ui.html` rendert `/project/knowledge-engine` Route mit Preset-Picker

**Bei Deaktivierung (`enabled: false`):**
- Agenten NICHT generiert
- No Intent-Routing-Pollution
- `knowledge-*.md` Zeilen in `.claude/agents/` existieren nicht
- Zero Runtime-Overhead

### 14.3 Bundle-Struktur (OKF v0.1 Format)

```
docs/knowledge/                      # Konfigurierbar via bundle_path
├── schema.md                        # Steuerungsdokument (generiert via knowledge.py)
├── index.md                         # Content-Katalog (generiert via knowledge.py)
├── log.md                           # Chronologisches Event-Log (generiert via knowledge.py)
├── papers/                          # Subdirectories gruppieren Concepts
│   ├── index.md
│   ├── transformer-attention.md     # Concept-Dokumente (Frontmatter + Body)
│   └── bert-pretraining.md
├── entities/
│   ├── index.md
│   ├── author-yoshua-bengio.md
│   └── dataset-imagenet.md
└── topics/
    ├── index.md
    └── self-attention-mechanisms.md
```

**Spezial-Dateien (generiert von `knowledge.py`):**

| Datei | Generierungspunkt | Mutable | Beschreibung |
|-------|-----------------|--------|-------------|
| `schema.md` | `knowledge_migrator` → `sync_knowledge_engine()` | Co-evolved | Steuerungsdokument: Bundle-Domäne, Concept-Types, Konventionen, Workflows (ähnlich CLAUDE.md) |
| `index.md` | `knowledge_indexer` + `generate_initial_index()` | Append-only | Directory Listing nach Konzept-Kategorie; LLM navigiert zuerst hier hin |
| `log.md` | `knowledge_indexer` + `generate_initial_log()` | Append-only | Chronologisches Change-Log, Format: `YYYY-MM-DD HH:MM — <op> — <summary>`, parsebar |

**Frontmatter pro Concept-Dokument (OKF §4):**
```yaml
---
concept_id: papers/transformer-attention     # Dateipfad ohne .md
created: 2026-07-24
updated: 2026-07-24
category: paper                              # Aus DOMAIN_CONCEPT_TYPES
tags: [attention, nlp, neural-networks]
links: [papers/bert-pretraining]             # Inbound/Outbound Cross-Links
citations:
  - url: https://arxiv.org/abs/1706.03762
    title: "Attention Is All You Need"
---
```

### 14.4 Runtime-Generierung (scripts/lib/knowledge.py)

**Exportierte Funktionen:**

| Funktion | Signatur | Zweck |
|----------|----------|-------|
| `generate_schema` | `(domain: str, bundle_path: str, agent_meta_root: Path) → str` | Rendert `schema.md` aus Template mit Domain-Concept-Types |
| `generate_initial_index` | `() → str` | Leeres `index.md` Skeleton |
| `generate_initial_log` | `() → str` | Leeres `log.md` Skeleton mit Format-Dokumentation |
| `DOMAIN_CONCEPT_TYPES` | dict | Mapping Domain → Concept-Type-Liste (Quelle der Wahrheit) |

**Caller:** `scripts/sync.py:sync_knowledge_engine()` (Phase A Scaffolding)

**Keine Dateien-Persistence in knowledge.py** — `sync.py` besitzt alle I/O- und Idempotenz-Entscheidungen.

### 14.5 Admin-UI-Integration

**Route:** `/project/knowledge-engine` (neu in `docs/ui/admin-ui.html`)

**Komponenten:**

| Komponente | Datei | Zweck |
|-----------|-------|-------|
| Preset-Picker | `admin-ui.html:const PRESETS` | 6 Domain-Presets inline als JS-Objekt: `research`, `personal`, `business`, `book`, `internal-docs`, `custom` |
| Toggle-Switch | `admin-ui.html` | Enable/Disable Schalter für `knowledge-engine.enabled` |
| Domain-Selector | `admin-ui.html` | Dropdown aus `DOMAIN_CONCEPT_TYPES` |
| Bundle-Path-Input | `admin-ui.html` | Text-Input für `bundle_path` |
| Config-Save-Button | `admin-ui.html` → `POST /api/project/config` | Speichert zu `.meta-config/project.yaml` |
| Status-Panel | `admin-ui.html` | Zeigt Anzahl Generierter Agenten, Bundle-Größe, Last-Index-Update |

**Presets inline in HTML (Abweichung vom Konzept):**

```javascript
const PRESETS = {
  research: { domain: "research", "bundle-path": "knowledge", ... },
  personal: { domain: "personal", "bundle-path": "knowledge", ... },
  business: { domain: "business", "bundle-path": "knowledge", ... },
  book: { domain: "book", "bundle-path": "knowledge", ... },
  "internal-docs": { domain: "internal-docs", "bundle-path": "knowledge", ... },
  custom: { domain: "custom", "bundle-path": "knowledge", ... },
};
```

**Admin-Server Allowlist (`scripts/admin-server.py`):**
- Schreibzugriffe auf `knowledge-engine.*` in `.meta-config/project.yaml` erlaubt
- GET `/project/knowledge-engine` → gibt aktuellen Config zurück
- POST `/project/knowledge-engine` → validated gegen Schema und speichert

### 14.6 Role-Defaults-Einträge

**In `config/role-defaults.yaml` (neu):**

```yaml
# Knowledge Engine Agents (v0.82.0+)
knowledge-curator:
  model: balanced
  memory: project
  workflow_tier: optional
  description: "Monitors knowledge bundle health — finds contradictions, stale claims, orphans."

knowledge-ingestor:
  model: balanced
  memory: project
  workflow_tier: optional
  description: "Migrates external sources into bundle structure with summaries and link updates."

knowledge-querier:
  model: balanced
  memory: project
  workflow_tier: optional
  description: "Answers questions by navigating index and synthesizing with citations."

knowledge-linter:
  model: fast
  memory: —
  workflow_tier: optional
  description: "Automated format validation (YAML, Dead Links, OKF Compliance)."

knowledge-indexer:
  model: fast
  memory: —
  workflow_tier: optional
  description: "Generates/updates index.md and log.md in OKF format."

knowledge-gardener:
  model: balanced
  memory: project
  workflow_tier: optional
  description: "Proactive maintenance — archive obsolete pages, optimize linking."

knowledge-migrator:
  model: balanced
  memory: project
  workflow_tier: optional
  description: "Base initializer — scaffold new bundles, migrate from existing wikis."
```

### 14.7 Intent-Routing-Integration

**In `scripts/lib/delegation_table.py:generate_intent_routing_table()`:**

```python
if config.get("knowledge-engine", {}).get("enabled"):
    routes.extend([
        ("query", "knowledge-querier"),
        ("lint.*knowledge", "knowledge-linter"),
        ("ingest.*knowledge", "knowledge-ingestor"),
        ("knowledge.*health", "knowledge-curator"),
        ("migrate.*wiki", "knowledge-migrator"),
        ("archive.*knowledge", "knowledge-gardener"),
        ("index.*knowledge", "knowledge-indexer"),
    ])
```

**Skip-Logik:** `role_name.startswith("knowledge-")` → übersprungen wenn `KNOWLEDGE_ENGINE_ENABLED == false`.

### 14.8 Testing

**Test-Datei:** `tests/test_knowledge_engine.py` (44 Tests, alle grün)

| Test-Kategorie | Anzahl | Fokus |
|---|---|---|
| Domain Validation | 8 | Gültige/ungültige Domänen, Concept-Types |
| Template Generation | 10 | `generate_schema()`, `generate_initial_index()`, `generate_initial_log()` |
| OKF Compliance | 12 | Frontmatter-Parsing, Concept-ID-Validierung, Link-Format |
| Bundle Scaffolding | 8 | Verzeichnisstruktur, Datei-Erstellen, Fallback-Verhalten |
| Sync Integration | 6 | `sync_knowledge_engine()` in sync.py, Idempotenz |

**Integration-Tests:** `tests/test_knowledge_sync_integration.py`
- E2E Bundle-Scaffolding
- Orchestrator-Routing bei aktiviertem Knowledge Engine
- Config-Fallback bei deaktiviertem Feature

### 14.9 Dokumentation & Referenzen

| Datei | Zweck |
|-------|-------|
| `docs/concepts/knowledge-engine-concept.md` | Detailliertes Designdokument mit OKF/Karpathy Fusion, 42 Abschnitte |
| `templates/knowledge-schema.template.md` | Domain-spezifisches Steuerungsdokument-Template |

---

*Ende der Bestandsaufnahme*
