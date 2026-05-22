# Feature: [Feature-Name]
**ID:** [z.B. F001] <br>
**Status:** [Draft / Ready for AI / In Progress / Done]

---

## System Engineering Requirements


## Requirement Template

### Stakeholder Requirement (REQ-L1-SH)
* **ID:** [REQ-L1-SH-FXXX-XXX]
* **Titel:** [Titel der Stakeholder-Anforderung]
* **Beschreibung:** Als [Akteur] möchte ich [Ziel], damit [Nutzen/Motivation].

### L1 System Blackbox Requirement (REQ-L1-BB)
* **ID:** [REQ-L1-BB-FXXX-XXX]
* **Titel:** [Titel der Blackbox-Anforderung]
* **Beschreibung:** Das System MUSS [extern sichtbares Verhalten].
* **Abnahmekriterium:** [Was muss passieren, damit diese Anforderung als erfüllt gilt?]
* **Refines:** [REQ-L1-SH-FXXX-XXX] 

### L1 System Whitebox Requirement (REQ-L1-WB)
* **ID:** [REQ-L1-WB-FXXX-XXX]
* **Titel:** [Titel der Whitebox-Anforderung]
* **Beschreibung:** *Um [REQ-L1-BB-FXXX-XXX] zu erfüllen, MUSS [Blick auf die Durchführung und Kommunikation der Sub-Systeme] 
* **Beteiligte Sub-Systeme:** [Nennung aller beteiligten Sub-Systeme - Keine Komponenten]
* **Refines:** [REQ-L1-BB-FXXX-XXX] 

### L2 System Blackbox Requirement (REQ-[Systemkürzel]-BB)
Eine L2 Anforderung hat in seiner ID Syntax ein Systemkürzel.
* **ID:** [REQ-[Systemkürzel]-BB-FXXX-XXX]
* **Titel:** [Titel der Blackbox-Anforderung]
* **Beschreibung:** Das [Systemname] MUSS [extern sichtbares Verhalten].
* **Abnahmekriterium:** [Was muss passieren, damit diese Anforderung als erfüllt gilt?]
* **Refines:** [REQ-L1-WB-FXXX-XXX] 

### L2 System Whitebox Requirement (REQ-[Systemkürzel]-WB)
* **ID:** [REQ-[Systemkürzel]-WB-FXXX-XXX] 
* **Titel:** [Titel der Whitebox-Anforderung]
* **Beschreibung:** *Um [REQ-[Systemkürzel]-BB-FXXX-XXX] zu erfüllen, MUSS [Blick auf die Durchführung und Kommunikation der zugehörigen System-Komponenten] 
* **Beteiligte System-Komponenten:** [Nennung aller beteiligten System-Komponenten]
* **Refines:** [REQ-[Systemkürzel]-BB-FXXX-XXX]

### L3 Component Requirement (REQ-[System-Komponentenkürzel]-CP)
Eine L3 Komponenten-Anforderung hat in seiner ID Syntax ein System-Komponentenkürzel.

* **ID:** [REQ-[Systemkomponentenkürzel]-CP-FXXX-XXX]
* **Titel:** [Titel der Komponenten-Anforderung]
* **Beschreibung:** Die Komponente [System-Komponentenname] MUSS [extern sichtbares Verhalten].
* **Abnahmekriterium:** [Was muss passieren, damit diese Anforderung als erfüllt gilt?]
* **Refines:** [REQ-[Systemkürzel]-WB-FXXX-XXX] 
* **Schnittstellenhinweis**: [Zusätzliche Schnittstelleninformationen als Vorbereitung für die Umsetzung]
---

## Requirements

[Hier müssen alle Anforderungen zum zugehörigen Feature gelistet werden, die von der Stakeholder Requirement vollständig heruntergebrochen wurden. Dabei muss sich immer an das Requirement Template gehalten werden.]
