# Session-Abschluss — Erkenntnisse sichern

Gilt für Hauptchat und Orchestrator.

## Session-Ende erkennen

Signale dass eine Session abgeschlossen ist:

- User sagt "tschüss", "bye", "bis später", "fertig", "done", "das war's"
- User fragt nach einem Commit oder Push (Task ist abgeschlossen)
- User wechselt explizit das Thema zu etwas Unverbundenem
- User fragt "was haben wir heute gemacht?"

## Pflicht bei Session-Ende

Wenn ein Signal erkannt wird und in der Session etwas Nennenswertes passiert ist
(Code geändert, Architektur-Entscheid getroffen, Bug analysiert, Feature implementiert):

> "Session abschließen? Ich kann die Erkenntnisse an den documenter-Agenten delegieren."

Bei Bestätigung → `documenter` mit Session-Zusammenfassung delegieren:
- Was wurde implementiert / gefixt / entschieden
- Offene Punkte / Follow-ups
- Wichtige Erkenntnisse (Probleme, Lösungsansätze, Architektur-Änderungen)

## Wann NICHT fragen

- Kurze Fragen ohne Code-Änderungen (nur Erklärungen, Reviews ohne Fixes)
- User hat Erkenntnisse bereits explizit gespeichert
- Session war trivial (1 Datei, 1 Zeile Fix)
