# Overall Architectural Systems Engineering Breakdown Rules

Die folgenden Regeln müssen bei jedem Anforderungs-Herunterbruch beachtet werden:

* **Regel 1: Trennung von Problem & Lösungsraum** Problem- & Lösungsraum strikt trennen: Ebene 1 (Stakeholder & L1 Blackbox) darf NIEMALS technische Begriffe enthalten. Erst in den System Whitebox Requirements beginnt der Lösungsraum.
* **Regel 2: Orthogonality First** Keine L3-Komponente darf Verantwortlichkeiten einer anderen Komponente übernehmen (Single Responsibility Principle).
* **Regel 3: Traceability and Skipping** Eine Anforderung darf nur erstellt werden, wenn sie von einer übergreifenden Anforderung abgeleitet wurde. Der Pfad ist: Stakeholder Requirement -> L1 System Blackbox Requirement -> L1 System Whitebox Requirement -> L2 System Blackbox Requirement -> L2 System Whitebox Requirement -> L3 Component Requirement.
* **Regel 3.1: Vollständiger Herunterbruch** Es ist essentiell, dass alle notwendigen Anforderungen der nächsten Stufe erstellt wurden. Keine funktionalen Lücken.
* **Regel 4: Tracer Bullet Fokus** Es darf nur das nach unten abgeleitet werden, dass die darüber liegende Anforderung hergibt. Kein Over-Engineering für zukünftige Features.
* **Regel 5: Binäre Testbarkeit** Formuliere alle Anforderungen so, dass ein QA-Engineer sofort einen Test (True/False) daraus ableiten kann. Verwende imperatives "MUSS" / "DARF NICHT".
* **Regel 6: Nutzung von abstrakten Interfaces** Ein- und Ausgänge von Komponenten ausschließlich über abstrakte Interfaces definieren. Keine kontextgebundenen Properties an den Außengrenzen.
* **Regel 7: Strikter System & Komponentenkontext** Der Herunterbruch muss durch die bestehende Architektur ermöglicht werden. Neue Systeme müssen validiert und begründet werden.
* **Regel 8: Kommunikations-Matrix & Routing Gesetz (CQRS & Events)** Inter-System-Kommunikation muss lose gekoppelt sein (Commands für Action Requests, Events für State Changes, State Mutations für tatsächliche Datenänderungen, Queries für zustandslose Abfragen).
* **Regel 9: Globales Anforderungsdenken** Beim Herunterbruch muss immer berücksichtigt werden, dass dieses Feature Teil einer Gesamtarchitektur ist.
* **Regel 10: System- & Systemkomponentenkürzel** Bei der Angabe der Anforderungs-IDs sind exakt definierte Kürzel zu nutzen.
* **Regel 11: Gesetz des Gemeinsamen Taktes (Event/Clock Sovereignty)** Alle asynchronen Berechnungen müssen synchron, deterministisch und orchestriert in den Systemzustand gemerged werden. Keine unkontrollierten Mutationen zur Laufzeit.
