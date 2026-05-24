# Test Validation Checklist — SE Framework Extensions

> **Branch:** feat/agent-framework-extensions
> **Datum:** [wird bei Durchfuehrung eingetragen]
> **Durchgefuehrt von:** [Name]

---

## 1. Agenten-Templates (Automatisiert via test-runner.py)

| Agent | Existiert | Frontmatter valide | Nicht leer | Routing in Orchestrator | Status |
|-------|-----------|-------------------|------------|------------------------|--------|
| se-orchestrator | [ ] | [ ] | [ ] | [ ] | [ ] |
| se-requirements | [ ] | [ ] | [ ] | [ ] | [ ] |
| se-architect | [ ] | [ ] | [ ] | [ ] | [ ] |
| se-critic | [ ] | [ ] | [ ] | [ ] | [ ] |
| se-interface-mgr | [ ] | [ ] | [ ] | [ ] | [ ] |
| se-termination | [ ] | [ ] | [ ] | [ ] | [ ] |
| se-test-engineer | [ ] | [ ] | [ ] | [ ] | [ ] |
| se-testreviewer | [ ] | [ ] | [ ] | [ ] | [ ] |
| se-verifier | [ ] | [ ] | [ ] | [ ] | [ ] |
| se-validator | [ ] | [ ] | [ ] | [ ] | [ ] |
| se-integration-and-test-manager | [ ] | [ ] | [ ] | [ ] | [ ] |
| code-reviewer | [ ] | [ ] | [ ] | [ ] | [ ] |
| ui-ux-designer | [ ] | [ ] | [ ] | [ ] | [ ] |
| api-specialist | [ ] | [ ] | [ ] | [ ] | [ ] |
| devops-engineer | [ ] | [ ] | [ ] | [ ] | [ ] |
| performance-optimizer | [ ] | [ ] | [ ] | [ ] | [ ] |
| export-manager | [ ] | [ ] | [ ] | [ ] | [ ] |

---

## 2. Framework-Anbindungen (Automatisiert)

| Pruefung | Status | Details |
|---------|--------|---------|
| role-defaults.yaml enthaelt alle neuen Rollen | [ ] | |
| role-defaults.yaml: Jede Rolle hat model, memory, permissionMode, tier | [ ] | |
| orchestrator.md: Intent-Routing-Tabelle aktualisiert | [ ] | |
| orchestrator.md: Agenten-Tabelle aktualisiert | [ ] | |
| orchestrator.md: Workflows (SE-Kaskade, V&V) referenzieren neue Agenten | [ ] | |
| CLAUDE.md: Agenten-Tabelle enthaelt neue Rollen | [ ] | |
| AGENTS.md: Agenten-Tabelle enthaelt neue Rollen | [ ] | |

---

## 3. Test-Daten Validierung (Automatisiert)

| Pruefung | Status | Details |
|---------|--------|---------|
| stakeholder-needs.md: Mindestens 5 Stakeholder | [ ] | |
| expected-l1-requirements.json: Valides JSON | [ ] | |
| expected-l1-requirements.json: >= 12 Requirements | [ ] | |
| expected-l1-requirements.json: Traceability vollstaendig | [ ] | |
| expected-architecture.json: Valides JSON | [ ] | |
| expected-architecture.json: >= 4 Subsysteme | [ ] | |
| expected-architecture.json: Signal-Flow definiert | [ ] | |
| expected-test-model.json: Valides JSON | [ ] | |
| expected-test-model.json: >= 15 Test-Cases | [ ] | |
| expected-test-model.json: 100% Requirement-Coverage | [ ] | |

---

## 4. Cross-Validation (Automatisiert)

| Pruefung | Status | Details |
|---------|--------|---------|
| Alle L1 REQs -> Architektur source_requirements | [ ] | |
| Alle L1 REQs -> Test-Modell coverage_matrix | [ ] | |
| Alle Komponenten -> Test-Cases referenziert | [ ] | |
| Alle Stakeholder -> Traceability-Matrix | [ ] | |

---

## 5. Manuelle Test-Schritte

| Schritt | Beschreibung | Status |
|---------|-------------|--------|
| M-01 | `python tests/se-test-data/test-runner.py` ausfuehren | [ ] |
| M-02 | Console Output pruefen: Alle Tests passed? | [ ] |
| M-03 | `tests/se-test-data/test-report.md` oeffnen und lesen | [ ] |
| M-04 | Stichprobe: 3 zufaellige Agenten-Templates manuell oeffnen | [ ] |
| M-05 | `sync.py --dry-run` ausfuehren — keine Errors? | [ ] |
| M-06 | Branch-Guard pruefen: Nicht auf main/master? | [ ] |

---

## 6. Test-Ausfuehrungsprotokoll

> Wird NACH der tatsaechlichen Test-Durchfuehrung ausgefuellt.

| Feld | Wert |
|------|------|
| Ausfuehrungsdatum | |
| test-runner.py Version | |
| Python Version | |
| Platform | |
| Gesamt-Tests | |
| Passed | |
| Failed | |
| Success Rate | |
| Kritische Findings | |
| Nicht-kritische Findings | |
| Fazit | |
| Naechste Schritte | |

---

## 7. Sign-Off

| Rolle | Name | Datum | Unterschrift |
|-------|------|-------|-------------|
| Test Engineer | | | |
| SE Architect | | | |
| Release Manager | | | |
