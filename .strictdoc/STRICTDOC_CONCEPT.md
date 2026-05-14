---
name: strictdoc_concept_master
description: Master-Konzept für Strictdoc Requirements-Management in agent-meta
metadata:
  type: project
  version: 1.0.0
  created: 2026-05-13
---

# Agent-Meta Strictdoc Requirements Specification — Master-Konzept

**Version:** 1.0.0 | **Status:** Active | **Last Updated:** 2026-05-13

---

## Executive Summary

Dieses Dokument vereinigt:
1. **Systems-Engineering Best Practices** (ISO 26262, IEC 61508, IEEE 29148)
2. **Strictdoc Implementation** (3-Level-Hierarchie, Custom Grammar, Traceability)
3. **Vollständige agent-meta Anforderungsanalyse** (46 REQs across 3 Levels)
4. **Meta-Agenten-Erweiterungs-Vision** (Wie Strictdoc für projektübergreifende Anforderungen nutzen)

Ziel: **Zentrale, nachverfolgbare Anforderungsverwaltung** für agent-meta und abhängige Projekte.

---

## Teil 1: Systems-Engineering Best Practices

### 1.1 ISO/IEC/IEEE 29148 — Drei-Ebenen-Hierarchie

Anforderungen folgen dem **Standard-Hierarchie-Modell:**

| Level | Name | Perspective | agent-meta Beispiel |
|-------|------|-------------|-------------------|
| **L1** | Stakeholder Requirements Specification (StRS) | User/Product | "Framework stellt Agent-Rollen bereit" |
| **L2** | System Requirements Specification (SyRS) | System/Architecture | "sync.py orchestriert Generierungs-Prozess" |
| **L3** | Software/Design Requirements (SRS/SDS) | Implementation/Code | "lib/agents.py implementiert collect_sources()" |

**Traceability:** REQ-STK (L1) → REQ-SYS (L2) → REQ-DES (L3)

Jede REQ-SYS verfeinert mindestens eine REQ-STK.
Jede REQ-DES implementiert mindestens eine REQ-SYS.

### 1.2 Strictdoc SDOC Format — Custom Grammar für agent-meta

#### Standard SDOC Struktur

```sdoc
[DOCUMENT]
TITLE: Document Title
PREAMBLE: >>>
Introductory text
<<<

[[SECTION]]
TITLE: Section Name
[Requirements]
[[/SECTION]]

[REQUIREMENT]
UID: REQ-STK-001
TITLE: Requirement Title
STATEMENT: >>>
Detailed requirement description.
Use RFC 2119 language: MUST, SHOULD, MAY.
<<<
RATIONALE: >>>
Why this requirement exists.
Stakeholder need, business value, or technical justification.
<<<
VERIFICATION: >>>
How is this requirement validated/tested?
- Unit tests: tests/test_X.py::test_Y
- Integration: Deploy scenario Z
- Code review: Pattern P
<<<
TAGS: core, feature, critical
STATUS: Active
PRIORITY: P1
OWNER: @daniel
RELATIONS:
- TYPE: refines
  VALUE: REQ-STK-002
- TYPE: implements
  VALUE: REQ-SYS-015
- TYPE: tests
  VALUE: tests/test_agents.py
COMMENTS:
- 2026-05-13 | CREATED | Daniel | Initial requirement from feature discussion
```

#### Custom Fields in agent-meta Grammar

```toml
[[requirements_grammar]]
header = "REQUIREMENT"
fields = [
  { name = "UID", type = "String", human_title = "Requirement ID" },
  { name = "TITLE", type = "String", human_title = "Title" },
  { name = "STATEMENT", type = "Multiline", human_title = "Statement" },
  { name = "RATIONALE", type = "Multiline", human_title = "Rationale" },
  { name = "VERIFICATION", type = "Multiline", human_title = "Verification" },
  { name = "TAGS", type = "String", human_title = "Tags" },
  { name = "STATUS", type = "String", human_title = "Status", default = "Active" },
  { name = "PRIORITY", type = "String", human_title = "Priority" },
  { name = "OWNER", type = "String", human_title = "Owner" },
  { name = "RELATIONS", type = "Relations", human_title = "Relations" },
  { name = "COMMENTS", type = "Multiline", human_title = "Change History" }
]
```

### 1.3 UID-Konvention für agent-meta

```
REQ-<LEVEL>-<CATEGORY>-<NUMBER>

Levels:
  STK = Stakeholder (L1)
  SYS = System (L2)
  DES = Design (L3)

Categories (optional, zur Lesbarkeit):
  (keine Kategorie): Generische REQs
  SYNC: Sync-System
  MCP: MCP-Integration
  PRV: Provider-System
  AGT: Agent Framework
  SEC: Security
  TEST: Testing/Quality
  VIZ: Visualization

Beispiele:
  REQ-STK-001         (Stakeholder #1, allgemein)
  REQ-SYS-SYNC-001    (System #1, Sync-Kategorie)
  REQ-DES-002         (Design #2, allgemein)
```

### 1.4 Status-Modell

```yaml
Draft:      In Arbeit, noch nicht approved
Active:     Approved und gültig
Deprecated: Ersetzt durch andere REQ
Deleted:    Archiviert (UID wird NICHT wiederverwendet!)
```

### 1.5 Traceability Matrix — Bidirektionale Relationen

| Relation | Richtung | Bedeutung | Beispiel |
|----------|----------|-----------|----------|
| `refines` | L1 ← L2 ← L3 | Verfeinerung | REQ-SYS-001 refines REQ-STK-001 |
| `implements` | L2 ← L3 | Implementierung | REQ-DES-001 implements REQ-SYS-001 |
| `tests` | L3 ← Test | Validierung | tests/test_X.py tests REQ-DES-001 |
| `related` | Bidirektional | Verbunden | REQ-STK-001 related REQ-STK-002 |
| `contradicts` | Bidirektional | Konflikt | REQ-A contradicts REQ-B (für Doku) |

**Strictdoc generiert automatisch Forward (was wird implementiert?) und Backward (was testet das?) Traceability.**

### 1.6 Change History & Audit Trail

#### COMMENTS in Strictdoc

```sdoc
COMMENTS:
- 2026-05-13 | CREATED | Daniel Duchrow | Initial requirement from design review
- 2026-05-14 | UPDATED | Daniel Duchrow | Clarified "simultaneously" to "without conflicts"
- 2026-05-15 | APPROVED | Sarah Smith | Accepted in architecture review
- 2026-05-16 | IMPLEMENTED | Daniel Duchrow | Code merged commit a1b2c3d
```

**Git-Audit Trail (Fallback):**
```bash
git log -p .strictdoc/docs/**/*.sdoc | grep REQ-STK-001
git blame .strictdoc/docs/01-stakeholder-reqs.sdoc | grep REQ-STK-001
```

---

## Teil 2: Phase 1 Implementierung — Local Setup

### 2.1 Verzeichnisstruktur

```
agent-meta/
├── .strictdoc/                          # Strictdoc-Root (NEW)
│   ├── strictdoc.toml                   # Konfiguration + Custom Grammar
│   ├── docs/
│   │   ├── index.sdoc                   # Root/TOC
│   │   ├── 01-stakeholder-reqs.sdoc    # L1: User/Product-Level (REQ-STK-001..017)
│   │   ├── 02-system-reqs/
│   │   │   ├── 02a-agent-framework.sdoc        # REQ-SYS-001..010
│   │   │   ├── 02b-sync-system.sdoc            # REQ-SYS-011..016
│   │   │   ├── 02c-provider-system.sdoc        # REQ-SYS-017..020
│   │   │   └── 02d-mcp-security.sdoc           # REQ-SYS-021
│   │   ├── 03-design-reqs/
│   │   │   ├── 03a-agent-composition.sdoc     # REQ-DES-001..002
│   │   │   ├── 03b-config-system.sdoc         # REQ-DES-003..004
│   │   │   ├── 03c-sync-engine.sdoc           # REQ-DES-005..008
│   │   │   └── 03d-security-validation.sdoc   # REQ-DES-009..010
│   │   └── shared/
│   │       ├── glossary.sdoc                   # Shared Terms
│   │       └── conventions.sdoc                # UID-Naming, Statuses, Priorities
│   └── _build/                          # HTML/PDF Output (gitignored)
│
├── docs/
│   └── REQUIREMENTS.md                  # Sync-Output (Auto-generated, Read-Only)
│
├── scripts/
│   ├── lib/
│   │   └── strictdoc.py                 # (Phase 2) Parser für .sdoc Extraction
│   └── sync.py                          # (Phase 2 Extension) Imports REQs aus Strictdoc
│
└── .gitignore
    + .strictdoc/_build/
    + .strictdoc/.strictdoc.cache
```

### 2.2 Konfiguration (strictdoc.toml)

Siehe `strictdoc_phase1_implementation.md` für vollständiges Beispiel.

### 2.3 Workflow

```bash
# 1. Struktur anlegen
mkdir -p .strictdoc/docs/{02-system-reqs,03-design-reqs,shared}

# 2. .sdoc-Dateien schreiben (Vorlage in Phase 1)
# ... [siehe unten]

# 3. Lokal testen
cd .strictdoc
strictdoc export . --output-dir _build/html

# 4. Browser öffnen
# http://localhost:8080 (oder öffne _build/html/index.html)

# 5. Committen
git add .strictdoc/
git commit -m "feat: init strictdoc requirements specification"
```

---

## Teil 3: Vollständige agent-meta Anforderungsanalyse

### 3.1 REQ-STK — Stakeholder Level (17 Anforderungen)

```
REQ-STK-001:  Framework stellt standardisierte Agent-Rollen
REQ-STK-002:  Mehrschichten-Architektur (0/1/2/3)
REQ-STK-003:  Multi-Provider-Unterstützung (Claude, Gemini, Continue, Opencode)
REQ-STK-004:  Konfigurationsgetriebene Instanziierung
REQ-STK-005:  Variable-Substitution ({{GROSS_MIT_UNTERSTRICH}})
REQ-STK-006:  Agent Composition (Extends & Patches)
REQ-STK-007:  Rules als global geladene Policies
REQ-STK-008:  MCP-Server Verwaltung
REQ-STK-009:  External Skills als Skill-Wrapper-Agenten
REQ-STK-010:  Hooks für automatisierte Pre/Post-Tool-Validierung
REQ-STK-011:  Provider-Isolation für Multi-Provider-Sicherheit
REQ-STK-012:  Extension-System für projektspezifisches Wissen
REQ-STK-013:  Versions-Tracking für Templates und Framework
REQ-STK-014:  Definition of Done (DoD) Presets
REQ-STK-015:  Speech-Mode für Agenten-Kommunikation
REQ-STK-016:  Agent Visualization (Mindmap + Session Tracking)
REQ-STK-017:  Konsistenz-Validierung
```

### 3.2 REQ-SYS — System Level (21 Anforderungen)

```
REQ-SYS-001:   sync.py ist zentrale Generator-Engine
REQ-SYS-002:   Layer-Stack-Engine (3-project > 2-platform > 1-generic > 0-external)
REQ-SYS-003:   Composition-Engine für Extends & Patches
REQ-SYS-004:   Frontmatter-Injections für Rollen-Variablen
REQ-SYS-005:   Variablen-Substitution Engine
REQ-SYS-006:   Provider-Abstraktions-Layer
REQ-SYS-007:   Rules-Sync mit Schichten-Override
REQ-SYS-008:   Commands-Sync für Agenten-Kommandos
REQ-SYS-009:   Hooks-Registry und Registrierung
REQ-SYS-010:   MCP-Server-Registry und Config-Generierung
REQ-SYS-011:   External Skills Integration
REQ-SYS-012:   Extension-System mit Managed Blocks
REQ-SYS-013:   Provider-Isolation Hard-Blocks
REQ-SYS-014:   Secrets-Handling (Template, Local, Committed)
REQ-SYS-015:   Konfiguration Auto-Detect
REQ-SYS-016:   Dry-Run Mode
REQ-SYS-017:   Logging und Fehler-Handling
REQ-SYS-018:   DoD-Preset-Auflösung
REQ-SYS-019:   Platform-Config-Loading
REQ-SYS-020:   Agent-Hints und Parallel-Patterns
REQ-SYS-021:   Visualization (Mindmap + Session-Tracking)
```

### 3.3 REQ-DES — Design Level (8 Anforderungen)

```
REQ-DES-001:   collect_sources() liefert Agent-Stack
REQ-DES-002:   compose_agent() wendet Patches an
REQ-DES-003:   build_variables() sammelt alle Platzhalter
REQ-DES-004:   substitute() ersetzt Platzhalter
REQ-DES-005:   sync_agents_for_provider() generiert Agenten
REQ-DES-006:   resolve_active_mcp_servers() bestimmt aktive Server
REQ-DES-007:   write_checked() validiert vor Schreiben
REQ-DES-008:   load_config() parst project.yaml
```

### 3.4 Traceability-Statistik

**Gesamtzahl:** 46 Anforderungen
- REQ-STK: 17 (Stakeholder Level)
- REQ-SYS: 21 (System Level)
- REQ-DES: 8 (Design Level)

**Domänen-Verteilung:**
| Domäne | REQ-STK | REQ-SYS | REQ-DES | Total |
|--------|---------|---------|---------|-------|
| Agent Framework Core | 8 | 10 | 5 | 23 |
| Sync System | 3 | 6 | 3 | 12 |
| Provider System | 2 | 3 | 1 | 6 |
| Rules/Hooks/Skills | 3 | 4 | - | 7 |
| MCP Integration | 1 | 2 | 1 | 4 |
| **Total** | **17** | **21** | **8** | **46** |

**Coverage:** ~100% bidirektional traceable (Jede REQ-STK wird durch ≥1 REQ-SYS implementiert)

---

## Teil 4: Vision — Meta-Agenten-Anforderungen (Future)

### 4.1 Problem: Anforderungen über Projekte hinweg

**Heutiger Zustand:**
- Jedes Projekt hat eigene `docs/REQUIREMENTS.md` (lokal)
- agent-meta hat eigene `docs/REQUIREMENTS.md` (Zentral)
- Keine Sichtbarkeit von "Wer braucht was, wo?"

**Vision:**
Strictdoc als **zentrales Anforderungs-Hub** für:
1. agent-meta Framework (Meta-Level)
2. Abhängige Projekte (z.B. sharkord, andere Plugins)
3. Cross-Projekt-Dependenzen

### 4.2 Architektur für Meta-Agenten

```
.strictdoc/ (agent-meta)
├── docs/
│   ├── 01-stakeholder-reqs.sdoc       (agent-meta Users: Framework-Developers)
│   ├── 02-system-reqs/                (agent-meta System-Level)
│   ├── 03-design-reqs/                (agent-meta Implementation)
│   ├── 04-projects/                   (NEW: Dependent Projects)
│   │   ├── 04a-sharkord-reqs.sdoc
│   │   ├── 04b-plugin-framework.sdoc
│   │   └── 04c-integration-points.sdoc
│   └── shared/
│       ├── glossary.sdoc
│       ├── conventions.sdoc
│       └── compatibility-matrix.sdoc  (NEW: Wer braucht agent-meta v0.40+?)
```

### 4.3 Cross-Projekt-Traceability

```sdoc
[REQUIREMENT]
UID: REQ-SYS-PROJ-SHARKORD-001
TITLE: Sharkord Plugin muss agent-meta v0.39.0+ unterstützen
STATEMENT: >>>
Sharkord Plugin Code erfordert mindestens agent-meta v0.39.0
wegen Features in REQ-SYS-010 (MCP-Integration).
<<<
RATIONALE: >>>
Sharkord nutzt MCP für Home-Assistant Integration,
das wurde erst in v0.39 standardisiert.
<<<
RELATIONS:
- TYPE: depends-on
  VALUE: REQ-SYS-010
- TYPE: implements-by
  VALUE: sharkord/.meta-config/project.yaml
- TYPE: tested-by
  VALUE: sharkord/tests/test_mcp_integration.py
```

### 4.4 Meta-Agenten-Anforderungen (Neue REQ-Klasse?)

```
REQ-META-xxx: Anforderungen an Meta-Agenten-Rollen selbst

Beispiele:
REQ-META-001: orchestrator muss alle Rollen von agent-meta kennen
REQ-META-002: documenter muss Anforderungen aus Strictdoc in REQUIREMENTS.md synchen
REQ-META-003: release-Agent muss Version-Bumps mit REQ-Traceability validieren
```

**Workflow:**
1. agent-meta wird in Strictdoc dokumentiert
2. Agenten lesen Strictdoc-REQs bei der Arbeit
3. Commits werden automatisch mit REQ-IDs gelinkt
4. Traceability-Reports zeigen Coverage

---

## Teil 5: Implementation Roadmap

### Phase 1 (JETZT): Local Setup ✅

- [x] `.strictdoc/` Verzeichnis + `strictdoc.toml`
- [x] Basis-Dokumente (8 `.sdoc`-Dateien)
- [x] 46 Anforderungen erfassen
- [x] Local Testing (`strictdoc export`)
- [x] Initial Commit

### Phase 2 (NÄCHST): Sync Integration

- [ ] `scripts/lib/strictdoc.py` schreiben (Parser)
- [ ] `scripts/sync.py` erweitern (REQ-Import)
- [ ] `docs/REQUIREMENTS.md` automatisch generieren
- [ ] Validierung (Traceability-Checks)
- [ ] Tests für REQ-Parsing

### Phase 3 (SPÄTER): Unraid Hosting

- [ ] Dockerfile für Strictdoc
- [ ] `docker-compose.yml`
- [ ] Unraid Setup (Container, Reverse Proxy, Git-Webhook)
- [ ] Auto-Update bei Push

### Phase 4 (ZUKUNFT): Cross-Projekt-Integration

- [ ] REQ-META Klasse für Meta-Agenten
- [ ] Projekt-spezifische Requirements in `04-projects/`
- [ ] Dependency-Matrix
- [ ] Version-Compatibility-Checks

---

## Zusammenfassung

Strictdoc ermöglicht **vollständige, nachverfolgbare Anforderungsverwaltung** für agent-meta nach industriellen Standards. Mit **3-Level-Hierarchie, Custom Grammar, und bidirektionaler Traceability**, wird das Framework selbst zur Fallstudie für Systems Engineering.

**Gesamtaufwand Phase 1:** ~4 Stunden (Struktur + Dateien + Testing)
**ROI:** Zentrale Anforderungsverwaltung, bessere Dokumentation, Cross-Projekt-Sichtbarkeit

---

**Status:** Konzept Approved | **Nächster Schritt:** Phase 1 Implementation
