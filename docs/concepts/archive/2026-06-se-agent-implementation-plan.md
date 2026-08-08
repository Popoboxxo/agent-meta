# Implementierungsplan: Systems Engineering Agenten-Kaskade (Generic Edition)

> Status: **Entwurf**
> Basis: `se-agent-concept.md` kombiniert mit abstrahierten `.local-Inputs` (100% branchen- und domänenübergreifend)

## 1. Executive Summary & Synthese
Das rekursive Systems-Engineering-Zellenmodell aus dem Basis-Konzept wird mit einem universellen, strikten 6-Stufen-Herunterbruch (Stakeholder -> L1 -> L2 -> L3) verschmolzen. Die Agenten operieren dabei unter einem verbindlichen, generischen Architektur-Regelwerk, welches klare Trennung von Problem- und Lösungsraum, Orthogonalität und strikte Traceability einfordert. Jede Referenz auf spezifische Domänen (wie z.B. Spieleentwicklung) wurde zugunsten maximaler Wiederverwendbarkeit im agent-meta Framework entfernt.

## 2. Anpassung der Agenten-Rollen (Die generische SE-Zelle)

### 2.1 Requirements Agent (`se-requirements`)
- **Aufgabe:** Startet den Prozess durch Aufnahme des *Stakeholder Requirements (REQ-L1-SH)*. Führt den Dialog zur Klärung von Varianzen und fehlendem Kontext.
- **Workflow:** Setzt das 6-stufige `featuretemplate.md` um, ohne Annahmen über das Zielsystem zu treffen.
- **Output:** Liefert das formale Fundament für den Architekten.

### 2.2 Architect Agent (`se-architect`)
- **Verhalten:** Agiert streng nach den generischen Architektur-Gesetzen.
- **Aufgabe:**
  - **L1 (System-Ebene):** Zerlegt L1-Blackbox in L1-Whitebox. Definiert abstrakte Sub-Systeme (ohne technische Lösungen auf dieser Ebene vorwegzunehmen - Regel 1).
  - **L2 (Komponenten-Ebene):** Zerlegt L2-Blackbox in L2-Whitebox und benennt konkrete Komponenten.
  - **Kommunikation & Routing (Regel 8):** Implementiert ein universelles CQRS/Event-Driven-Muster (Commands, Events, State Mutation, Queries, Rejections) für die Inter-System-Kommunikation.

### 2.3 Critic Agent (`se-critic`)
- **Verhalten:** Universeller Auditor des Herunterbruchs.
- **Prüfkriterien:**
  - **Orthogonalität (Regel 2):** Übernimmt eine L3-Komponente fachfremde Aufgaben? Gilt das Single Responsibility Principle?
  - **Traceability (Regel 3):** Ist das `Refines:` Feld korrekt referenziert? Ist die Vererbung lückenlos?
  - **Binäre Testbarkeit (Regel 5):** Sind Anforderungen mit MUSS/DARF NICHT so formuliert, dass sie mit True/False testbar sind?
  - **Interface-Compliance (Regel 6):** Sind Schnittstellen abstrakt definiert (ohne kontextgebundene Properties)?
- **Workflow:** Iteriert den Output des Architect, bis alle generischen Regeln erfüllt sind.

### 2.4 Interface Manager Agent (`se-interface-mgr`)
- **Verhalten:** Überwacht den domänenagnostischen Signalfluss.
- **Aufgabe:** Sichert die Einhaltung deterministischer Zeit- oder Takt-Prinzipien (Regel 11 abstrahiert: Verarbeitungsschritte dürfen asynchron berechnet, aber nur kontrolliert und synchron auf den Systemzustand angewandt werden). Verwaltet das Registry für Commands und Events über alle Systemgrenzen hinweg.

### 2.5 Termination Agent (`se-termination`)
- **Verhalten:** Deterministischer Abbruch auf der L3-Ebene.
- **Aufgabe:** Terminiert den Ast, sobald ein *L3 Component Requirement (REQ-[Kürzel]-CP)* erreicht ist, welches die atomare Grundlage für die nachfolgende Software-, Mechanik- oder Elektronik-Entwicklung bildet.

## 3. Der generische 6-Stufen-Herunterbruch

Die Agenten-Zelle iteriert durch folgende Phasen, um jedes Feature systematisch herunterzubrechen:

1. **Iteration 1 (Stakeholder & L1):**
   - *Ebenen:* Stakeholder Requirement -> L1 System Blackbox -> L1 System Whitebox
   - *Agenten:* Requirements -> Architect -> Critic

2. **Iteration 2 (L2 - Sub-Systeme):**
   - *Ebenen:* L1 System Whitebox -> L2 System Blackbox -> L2 System Whitebox
   - *Agenten:* Architect -> Critic -> Interface Mgr

3. **Iteration 3 (L3 - Component):**
   - *Ebenen:* L2 System Whitebox -> L3 Component Requirement
   - *Agenten:* Architect -> Critic -> Termination
   - *Ergebnis:* Übergabe an die ausführenden Disziplinen.

## 4. Konkrete Implementierungsschritte (Roadmap)

### Phase 1: Bereinigung & Abstraktion der Wissensbasis
- Überführung von `architecture_law.md` in ein domänenagnostisches Regelwerk (Entfernung aller Game-Dev-Begriffe wie "Spieler", "World State", "Network System").
- Bereinigung von `featuretemplate.md` zu einem universellen Systems-Engineering-Standard.
- Ablage der generalisierten Dokumente in `docs/concepts/` und `templates/`.

### Phase 2: Agenten-Templates anpassen (in `agents/1-generic/`)
- Anpassung der Core-Prompts für alle 5 Agenten (`se-requirements.md`, `se-architect.md`, `se-critic.md`, `se-interface-mgr.md`, `se-termination.md`), sodass sie die 100% generischen Architektur-Gesetze durchsetzen.

### Phase 3: Structured Output Schema
- Anpassung von `schemas/se-decomposition.schema.json` zur Abbildung der universellen 6-Stufen-Architektur.
