---
type: "Guide"
title: "SE Session Resume — Wiederaufnahme nach Token-Loss"
description: "Lange SE-Kaskaden akkumulieren viele Token im Kontextfenster. Bei Ueberschreitung des Limits terminiert die Session — alle Zwischenergebnisse sind verloren. Eine neue Session..."
tags: [guide, se-cascade]
timestamp: "2026-07-27"
resource: "../../sources/docs/se-cascade/se-resume-session.md"
migrated_from: "docs/se-cascade/se-resume-session.md"
---
# SE Session Resume — Wiederaufnahme nach Token-Loss

> Quelle: `docs/concepts/se-pipeline-extension.md` — Loesung A
> Relevante REQs: REQ-SE-01, REQ-SE-02, REQ-SE-03, REQ-SE-04, REQ-SE-05

---

## Problem

Lange SE-Kaskaden akkumulieren viele Token im Kontextfenster. Bei Ueberschreitung des Limits terminiert die Session — alle Zwischenergebnisse sind verloren. Eine neue Session muss von vorne beginnen.

## Loesung: Teilresultat-Protokoll

Jeder SE-Agent persistiert seinen Output nach JEDEM Schritt in `docs/se/<projektname>/`. Die `.se-state.yaml` dient als Wiederaufnahme-Pointer.

---

## Wiederaufnahme-Algorithmus

```
1. Pruefe ob {SE_BASE_DIR}/.se-state.yaml existiert
2. Wenn nicht: starte neue SE-Kaskade mit se-requirements
3. Wenn ja:
   a. Lies .se-state.yaml
   b. Verifiziere last_completed_step.output_file existiert
   c. Lies dieses File und alle in next_expected_step.input_files
   d. Starte next_expected_step.agent mit diesem Kontext
   e. Schreibe Output gemaess Schritt-Tabelle
   f. Aktualisiere .se-state.yaml atomar (write-to-tmp + rename)
```

---

## Schritt-Tabelle: Wer schreibt was wann

| Schritt | Agent | Output-Datei |
|---------|-------|-------------|
| 1 | `se-requirements` | `requirements/L{n}_{FolderName}_Requirements.md` |
| 2 | `se-critic` (req-review) | `requirements/L{n}_{FolderName}_Requirements.critic.iter-{i}.md` |
| 3 | `se-architect` | `architecture/L{n}_{FolderName}_Architecture.iter-{i}.md` |
| 4 | `se-critic` (arch-review) | `architecture/L{n}_{FolderName}_Architecture.critic.iter-{i}.md` |
| 5 | `se-interface-mgr` | `interfaces/L{n}_{FolderName}_Interfaces.md` |
| 6 | `se-termination` | `termination/L{n}_{FolderName}_Decisions.md` |
| 7 | `se-{tier}-developer` | `implementation/L{n}_{ComponentName}_Impl.md` |
| 8 | `se-validator` / `se-verifier` | `validation/L{n}_{FolderName}_Validation.md` |
| 9 | `se-integration-and-test-manager` | `validation/L{n}_{FolderName}_TestPlan.md` |

---

## Verzeichnisstruktur

```
docs/se/<projektname>/
├── STRATEGY.md
├── .se-state.yaml
│
├── L1/Gesamtsystem/
│   ├── requirements/
│   │   ├── L1_Gesamtsystem_Requirements.md
│   │   ├── L1_Gesamtsystem_Requirements.critic.iter-1.md
│   │   └── L1_Gesamtsystem_Requirements.critic.final.md
│   ├── architecture/
│   │   ├── L1_Gesamtsystem_Architecture.iter-1.md
│   │   ├── L1_Gesamtsystem_Architecture.critic.iter-1.md
│   │   └── L1_Gesamtsystem_Architecture.final.md
│   ├── interfaces/
│   │   └── L1_Gesamtsystem_Interfaces.md
│   ├── termination/
│   │   └── L1_Gesamtsystem_Decisions.md
│   │
│   └── L2/AuthServiceSystem/
│       ├── requirements/
│       ├── architecture/
│       └── ...
│
└── diagrams/
    ├── architecture-overview.mmd
    └── interface-graph.mmd
```

---

## Iterations-Suffix-Konvention

- `*.iter-1.md`, `*.iter-2.md`, ... `*.iter-N.md` — alle Zwischenstaende
- `*.final.md` — finale, vom Critic approved Version
- Ohne Suffix (`*.md`) — Single-Shot-Schritte (Requirements, Interfaces, Termination)

---

## `.se-state.yaml` Schema

```yaml
project: <projektname>
last_updated: "2026-06-21T14:32:11Z"
current_level: L2
current_node: AuthServiceSystem
last_completed_step:
  agent: se-architect
  iteration: 2
  status: approved
  output_file: L1/Gesamtsystem/L2/AuthServiceSystem/architecture/L2_AuthServiceSystem_Architecture.final.md
next_expected_step:
  agent: se-interface-mgr
  input_files:
    - L1/Gesamtsystem/L2/AuthServiceSystem/architecture/L2_AuthServiceSystem_Architecture.final.md
    - L1/Gesamtsystem/interfaces/L1_Gesamtsystem_Interfaces.md
pending_decisions: []
budget_consumed:
  cells: 7
  tokens: 42100
  estimated_eur: 1.85
```

Schema-Referenz: `schemas/se-state.schema.json`

---

## Atomic Write

Jede Persistenz erfolgt atomar:

1. Schreibe Output in temporaere Datei
2. Rename auf Zielpfad (atomar auf gleichem Dateisystem)
3. Kein partieller Schreibzustand sichtbar

Bei Crash waehrend des Schreibens: temporaere Datei wird ignoriert, letzter gueltiger Stand bleibt erhalten.