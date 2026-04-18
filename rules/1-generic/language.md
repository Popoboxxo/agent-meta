# Sprachregeln

Diese Regel gilt für alle Agenten und den Hauptchat.

## Sprachzuordnung

| Kontext | Sprache |
|---------|---------|
| Kommunikation mit dem Nutzer | **{{COMMUNICATION_LANGUAGE}}** |
| Nutzer-Eingaben verstehen | **{{USER_INPUT_LANGUAGE}}** |
| Externe Dokumente (README, CHANGELOG, Release Notes, GitHub Issues) | **{{DOCS_LANGUAGE}}** |
| Interne Dokumente (CODEBASE_OVERVIEW, ARCHITECTURE, REQUIREMENTS, Berichte) | **{{INTERNAL_DOCS_LANGUAGE}}** |
| Code-nahe Artefakte (Kommentare, Commit-Messages, Test-Beschreibungen) | **{{CODE_LANGUAGE}}** |

## Rollenspezifische Präzisierungen

Agenten-Templates können zusätzliche Präzisierungen für ihren spezifischen Output-Typ enthalten
(z.B. welche Datei unter welche Kategorie fällt). Diese Regel definiert den Rahmen — die
rollenspezifische Zuordnung konkretisiert ihn.
