# Test-Szenario — Smart-Light IoT Controller

**Dokument-Typ:** SE-Test-Szenario
**Version:** 1.0.0
**Datum:** 2026-05-24
**Status:** Entwurf

---

## 1. Systembeschreibung

Der **Smart-Light IoT Controller** ist ein vernetztes Steuerungssystem fur die Beleuchtung in Smart-Home-Umgebungen. Das System erfasst Umgebungdaten uber Sensoren, verarbeitet diese in einer zentralen Steuereinheit und schaltet bzw. dimmt Lichtquellen uber Aktoren. Eine Cloud-Anbindung ermoglicht Remote-Zugriff, Monitoring und Firmware-Updates.

### Systemkomponenten (Ubersicht)

| Komponente | Typ | Beschreibung |
|---|---|---|
| Bewegungsmelder | Sensor | Erkennt Prasenz im Raum via PIR |
| Helligkeitssensor | Sensor | Misst Umgebungslicht in Lux |
| Zentrale Steuerung | Processing | Regelt Logik, Zeitplaten, Szenen |
| Lichtschalter | Aktor | Ein/Aus-Schaltung 230V |
| Dimmer | Aktor | Stufenlose Helligkeitsregelung |
| Cloud-Gateway | Kommunikation | MQTT/HTTPS-Anbindung an Cloud |
| Mobile App | UI | Remote-Steuerung fur Endnutzer |

### Kontextdiagramm (textuell)

```
[Bewegungsmelder] ──┐
                    ├──► [Zentrale Steuerung] ◄──► [Cloud-Gateway] ◄──► [Cloud-Backend] ◄──► [Mobile App]
[Helligkeitssensor]─┘         │
                              ├──► [Lichtschalter] ──► [Beleuchtung]
                              └──► [Dimmer] ─────────► [Beleuchtung]
```

---

## 2. Stakeholder-Bedurfnisse

Die ausfuhrlichen Stakeholder-Needs sind in `tests/se-test-data/stakeholder-needs.md` definiert. Ubersicht:

| Stakeholder | ID | Kernbedurfnisse |
|---|---|---|
| Hausbesitzer | SH-01 | Automatische Lichtsteuerung, Helligkeitsanpassung, Reaktionszeit < 200ms |
| Elektriker | SH-02 | 230V-Kompatibilitat, Fehlerdiagnose-Schnittstelle, Normenkonformitat |
| Cloud-Provider | SH-03 | Stabile MQTT-Verbindung, Bandbreiten-Effizienz, OTA-Update-Fahigkeit |
| Datenschutzbeauftragter | SH-04 | Keine Speicherung von Bewegungsdaten, DSGVO-konforme Verarbeitung, lokale Fallback-Steuerung |
| Wartungstechniker | SH-05 | Remote-Diagnose, Modulares Design, Selbsttest-Funktion |

---

## 3. Erwartete SE-Kaskade

Die folgende Tabelle beschreibt den vollstandigen Durchlauf der Systems-Engineering-Kaskade fur dieses Test-Szenario.

### 3.1 Kaskaden-Ubersicht

| Schritt | Agent | Input | Output | Level |
|---|---|---|---|---|
| 1 | `orchestrator (SE-Mode)` | Dieses Dokument + `stakeholder-needs.md` | Koordinierter Task-Plan | — |
| 2 | `se-requirements` | `stakeholder-needs.md` | L1 Blackbox Requirements | L1 |
| 3 | `se-architect` | L1 Requirements | L2 System-Architektur mit Komponenten & Schnittstellen | L2 |
| 4 | `se-critic` | L2 Architektur | Audit-Report (Orthogonalitat, Testbarkeit, Traceability) | L2 |
| 5 | `se-termination` | L2 Architektur + Audit | Entscheidung: L3 erreicht? (Ja/Nein) | L2→L3 |
| 6 | `se-integration-and-test-manager` | L2 Architektur + L1 Requirements | V&V-Strategie fur rechten V-Modell-Flugel | L3 |
| 7 | `se-test-engineer` | V&V-Strategie + Architektur | Test-Modelle und Integrationstests | L3 |
| 8 | `se-verifier` | Test-Modelle + Architektur | Multi-Level Verification Report | L3 |
| 9 | `se-validator` | L1 Requirements + System | L1 System-Validierung (End-to-End User Journeys) | L1 |

### 3.2 Detaillierte Schritt-Beschreibung

#### Schritt 1: orchestrator (SE-Mode) — Koordination

- **Aufgabe:** Zerlegt das Gesamtziel in Sub-Tasks, dispatcht parallel wo moglich, sequenziell wo Abhangigkeiten bestehen.
- **Input:** `stakeholder-needs.md`, dieses Test-Szenario
- **Output:** Ausfuhrungsplan mit Agent-Dispatch-Reihenfolge

#### Schritt 2: se-requirements — L1 Blackbox Requirements

- **Aufgabe:** Extrahiert aus Stakeholder-Needs formale, testbare Requirements.
- **Input:** `stakeholder-needs.md`
- **Output:** Strukturierte L1 Requirements mit IDs, Prioritaten, Kategorien, Acceptance Criteria
- **Erwartetes Format:** Siehe `expected-l1-requirements.json`

#### Schritt 3: se-architect — L2 System-Architektur

- **Aufgabe:** Entwirft System-Architektur mit Subsystemen, Komponenten, Schnittstellen und Signal-Flussen.
- **Input:** L1 Requirements
- **Output:** Architekturmodell mit SYS-/COMP-/IF-IDs, Signal-Flow-Graph
- **Erwartetes Format:** Siehe `expected-architecture.json`

#### Schritt 4: se-critic — Architektur-Audit

- **Aufgabe:** Pruft die L2-Architektur gegen generische Gesetze.
- **Input:** L2 Architektur
- **Output:** Audit-Report mit Pass/Fail fur Orthogonalitat, Testbarkeit, Traceability
- **Kriterien:**
  - Orthogonalitat: Keine Komponente hat mehr als eine Hauptverantwortung
  - Testbarkeit: Jede Komponente hat isolierbare Schnittstellen
  - Traceability: Jedes Requirement ist mindestens einer Komponente zugeordnet

#### Schritt 5: se-termination — L3-Entscheidung

- **Aufgabe:** Entscheidet deterministisch ob Component-Level (L3) erreicht ist.
- **Input:** L2 Architektur + Audit-Report
- **Output:** `terminated: true/false` mit Begrundung
- **Kriterium:** Alle Komponenten sind hinreichend spezifiziert fur Test-Design

#### Schritt 6: se-integration-and-test-manager — V&V-Strategie

- **Aufgabe:** Plant Integrationsstrategie und Test-Koordination fur rechten V-Modell-Flugel.
- **Input:** L2 Architektur, L1 Requirements, Audit-Report
- **Output:** V&V-Strategie mit Integrationsreihenfolge, Test-Priorisierung

#### Schritt 7: se-test-engineer — Test-Modelle

- **Aufgabe:** Erstellt konkrete Test-Cases und Integrationstests.
- **Input:** V&V-Strategie, Architektur, Requirements
- **Output:** Test-Modell mit TC- und IT-IDs, Inputs, Expected Outputs, Coverage-Matrix
- **Erwartetes Format:** Siehe `expected-test-model.json`

#### Schritt 8: se-verifier — Multi-Level Verification

- **Aufgabe:** Verifiziert implementierte Komponenten gegen Spezifikation.
- **Input:** Test-Modelle, Architektur, Implementierung (simuliert)
- **Output:** Verification Report mit Pass/Fail pro Test-Level

#### Schritt 9: se-validator — L1 System-Validierung

- **Aufgabe:** Validiert End-to-End User Journeys gegen Stakeholder-Bedurfnisse.
- **Input:** L1 Requirements, System-Verhalten (simuliert)
- **Output:** Validierungs-Report: Erfullt das System die ursprunglichen Stakeholder-Needs?

---

## 4. Erfolgskriterien pro Schritt

| Schritt | Agent | Pass-Kriterium |
|---|---|---|
| 1 | orchestrator (SE-Mode) | Task-Plan vollstandig, alle Agenten dispatcht, keine zirkularen Abhangigkeiten |
| 2 | se-requirements | Alle Stakeholder-Needs abgedeckt, jedes Requirement hat ID + Acceptance Criteria, Traceability-Matrix vollstandig |
| 3 | se-architect | Mindestens 4 Subsysteme definiert, alle Schnittstellen spezifiziert, Signal-Flow konsistent |
| 4 | se-critic | Alle 3 Audit-Kategorien (Orthogonalitat, Testbarkeit, Traceability) = "pass" |
| 5 | se-termination | `terminated: true` — alle Komponenten hinreichend spezifiziert |
| 6 | se-integration-and-test-manager | V&V-Strategie deckt alle Komponenten und Schnittstellen ab |
| 7 | se-test-engineer | 100% Requirement-Coverage, mindestens 15 Test-Cases, mindestens 5 Integrationstests |
| 8 | se-verifier | Alle Test-Cases bestanden, keine offenen Defekte |
| 9 | se-validator | Alle L1 Requirements gegen Stakeholder-Needs validiert, keine Lucken |

---

## 5. Test-Skript-Struktur

### 5.1 Grober Ablauf von `test-runner.py`

```
Phase 1: SETUP
  ├── Lade stakeholder-needs.md
  ├── Lade expected-l1-requirements.json
  ├── Lade expected-architecture.json
  └── Lade expected-test-model.json

Phase 2: SE-KASKADE (Links)
  ├── Dispatch se-requirements → vergleiche Output mit expected-l1-requirements.json
  │   ├── Prufe: Anzahl Requirements >= 12
  │   ├── Prufe: Alle Stakeholder-IDs in Traceability-Matrix
  │   └── Prufe: Jedes Requirement hat id, title, description, acceptance_criteria
  │
  ├── Dispatch se-architect → vergleiche Output mit expected-architecture.json
  │   ├── Prufe: Anzahl Subsysteme >= 4
  │   ├── Prufe: Alle Schnittstellen haben eindeutige IDs
  │   ├── Prufe: Signal-Flow ist konsistent (keine dangling references)
  │   └── Prufe: Alle L1 Requirements sind Komponenten zugeordnet
  │
  ├── Dispatch se-critic → prufe Audit-Report
  │   └── Prufe: orthogonality == "pass", testability == "pass", traceability == "pass"
  │
  └── Dispatch se-termination → prufe L3-Entscheidung
      └── Prufe: terminated == true

Phase 3: V&V-PLANUNG
  └── Dispatch se-integration-and-test-manager → prufe V&V-Strategie
      └── Prufe: Alle Komponenten und Schnittstellen abgedeckt

Phase 4: TEST-MODELLE (Rechts)
  ├── Dispatch se-test-engineer → vergleiche Output mit expected-test-model.json
  │   ├── Prufe: Anzahl Test-Cases >= 15
  │   ├── Prufe: Anzahl Integrationstests >= 5
  │   ├── Prufe: Requirement-Coverage == 100%
  │   └── Prufe: Jeder Test-Case referenziert gueltige REQ-ID und COMP-ID
  │
  ├── Dispatch se-verifier → prufe Verification Report
  │   └── Prufe: Alle Tests bestanden
  │
  └── Dispatch se-validator → prufe Validierungs-Report
      └── Prufe: Alle Stakeholder-Needs erfullt

Phase 5: REPORT
  ├── Sammle alle Einzelergebnisse
  ├── Generiere Gesamt-Report (JSON + Markdown)
  └── Exit-Code: 0 wenn alle Steps passed, sonst 1
```

### 5.2 Vergleichslogik

Der Test-Runner vergleicht nicht auf byte-gleiche JSON-Ubereinstimmung, sondern auf **strukturelle und semantische Aquivalenz**:

- **Requirements:** IDs mussen nicht exakt matchen, aber Anzahl, Kategorien und Traceability mussen konsistent sein.
- **Architektur:** Subsystem-Namen konnen variieren, aber Struktur (SYS → COMP → IF) und Signal-Flow-Konsistenz sind Pflicht.
- **Test-Modelle:** Test-Case-IDs konnen variieren, aber Coverage-Matrix muss 100% ergeben und alle Requirements abdecken.

### 5.3 Fehlerbehandlung

| Fehler-Typ | Verhalten |
|---|---|
| Agent-Output fehlt | Step = "fail", Report mit "missing output" |
| Struktur-Abweichung | Step = "fail", Diff im Report |
| Coverage < 100% | Step = "fail", fehlende Requirements im Report |
| Audit-Kategorie != "pass" | Step = "fail", Begrundung im Report |
| Timeout (> 5 Min pro Agent) | Step = "timeout", Retry mit Warning |

---

## 6. Referenz-Dateien

| Datei | Zweck |
|---|---|
| `tests/se-test-data/stakeholder-needs.md` | Input fur se-requirements |
| `tests/se-test-data/expected-l1-requirements.json` | Erwarteter L1-Output |
| `tests/se-test-data/expected-architecture.json` | Erwarteter L2-Output |
| `tests/se-test-data/expected-test-model.json` | Erwarteter L3-Output |
| `docs/test-scenario.md` | Dieses Dokument |
