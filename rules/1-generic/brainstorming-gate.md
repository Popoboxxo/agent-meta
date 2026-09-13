# Brainstorming-Gate

Vorgelagerter Klärungs- und Freigabe-Schritt, bevor eine Spec entsteht oder Code
geschrieben wird. Diese Rule greift, wenn Ziel, Umfang oder Aufwand einer Anfrage
noch unklar sind. Normativ nur, solange der Spec/Plan-Workflow aktiviert ist.

## Klassifikation

Vor der Spezifikation wird die Anfrage grob eingeordnet:

| Klasse | Merkmal | Konsequenz |
|---|---|---|
| **Spike** | reine Recherche, keine Produktionsänderung | `explorer` (Spike-Modus) / `ideation`; Ergebnis ist ein Spike-Doc, danach **STOP** (kein Plan) |
| **Bounded** | klar abgegrenzter Umfang, 3–20 Dateien, eine Komponente | Spec nach `spec-plan-workflow`, dann Plan |
| **Architectural** | öffentliche Schnittstellen/Contracts, Datenmodell/Schema oder mehr als eine Subsystem-/Komponentengrenze betroffen | `concept-architect` → Spec → Plan; SE-Aufstieg optional, nie automatisch |

Ist die Einordnung unmöglich, bleiben die offenen Punkte explizit als
Spike/Recherche-Auftrag.

## Gate: keine Implementierung ohne Approval

- **Keine Implementierung ohne explizite Freigabe.** Solange die Klassifikation oder
  die Spec nicht abgenommen ist, wird nicht implementiert.
- Das Gate ist eine **Convention boundary** (keine Security boundary), vgl.
  `spec-plan-workflow`. Es gilt zusätzlich regelbasiert für Routen ohne eigene
  Approve-Stage.

## Gesprächsführung

- Fragen werden **einzeln** gestellt — nie als Fragenkatalog auf einmal. Eine Antwort
  determiniert die nächste Frage.
- Zu jeder echten Entscheidung werden **2–3 Lösungsansätze mit Trade-offs** vorgelegt
  (Vor-/Nachteile, Annahmen, Risiken) statt einer fertigen Lösung.
- Empfehlungen sind begründet; die Entscheidung bleibt beim Menschen.

## Abschnittsweise Abnahme

- Das Design/die Spec wird **abschnittsweise** abgenommen, nicht als Ganzes.
- Jeder Abschnitt wird erst weiterverfolgt, wenn er bestätigt oder korrigiert ist.
- Offene Fragen und Risiken werden sichtbar festgehalten, nicht stillschweigend
  angenommen.

## Ergebnis

Nach erfolgreicher Abnahme liegt eine klassifizierte Anfrage mit abgenommener Spec
(`Status: APPROVED`) vor — die Grundlage für `writing-plans`. Spike-Aufträge enden
dagegen mit einem Spike-Doc und **ohne** Plan.
