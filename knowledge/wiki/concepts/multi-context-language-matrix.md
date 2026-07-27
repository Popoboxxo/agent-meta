---
type: "Concept"
title: "Konzept: Multi-Context Language Matrix"
description: "Standardisierte Matrix zur Steuerung der Dokumentsprache je nach Interaktions-Kontext (User-Kommunikation, User-Input, Externe/Interne Doku, Code/Commits)."
tags: [concept, governance, language, status:active]
timestamp: "2026-07-27"
resource: "../../rules/1-generic/language.md"
migrated_from: "rules/1-generic/language.md"
---
# Konzept: Multi-Context Language Matrix

> Status: **Umgesetzt — aktiv**  
> Verwandt: [Commit-Konventionen](commit-conventions.md)  
> Betroffen: `rules/1-generic/language.md`, `CLAUDE.md`, `AGENTS.md`  

---

## 1. Motivation

In internationalen Open-Source- und Meta-Repositories prallen verschiedene Sprachanforderungen aufeinander:
- Benutzer bevorzugen oft die Interaktion in ihrer Muttersprache (z.B. Deutsch).
- Der Quellcode, Log-Meldungen und Git-Commit-Historien müssen international lesbar sein (Englisch).
- Externe Dokumentationen (z.B. `README.md`) richten sich an die weltweite Community, während interne Entwicklungsnotizen lokal gehalten werden können.

Das **Multi-Context Language Matrix Konzept** schafft eine klare Trennung der Sprachbereiche.

---

## 2. Die 5-Stufen Sprach-Matrix

| Kontext | Sprache | Platzhalter | Begründung / Regel |
|---|---|---|---|
| **User-Kommunikation** | **Deutsch** | `{{COMMUNICATION_LANGUAGE}}` | Antworten des Agenten an den Benutzer erfolgen immer auf Deutsch. |
| **User-Input** | **Deutsch** | `{{USER_INPUT_LANGUAGE}}` | Eingaben des Benutzers werden auf Deutsch verarbeitet. |
| **Externe Doku** | **Englisch** | `{{DOCS_LANGUAGE}}` | Öffentliche Dateien wie `README.md` werden auf Englisch gepflegt. |
| **Interne Doku** | **Deutsch** | `{{INTERNAL_DOCS_LANGUAGE}}` | Interne Konzepte, Wiki-Einträge, `AGENTS.md` werden auf Deutsch verfasst. |
| **Code / Commits** | **Englisch** | `{{CODE_LANGUAGE}}` | Quellcode, Kommentare, Variablennamen und Git-Commits sind ausnahmslos auf Englisch. |

---

## 3. Dynamische Injektion via `sync.py`

`sync.py` liest die Konfiguration aus `.meta-config/project.yaml` und substituiert die entsprechenden PAL-Platzhalter beim Bauen der Provider-Prompts. Dadurch bleibt das Regelwerk flexibel für internationale Teams anpassbar, behält aber projektspezifische Defaults bei.