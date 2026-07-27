---
type: "Concept"
title: "Konzept: Commit-Konventionen & REQ-Traceability"
description: "Standardisierung von Commit-Nachrichten nach Conventional Commits mit imperativen Formulierungen, Längenbegrenzung und optionalem REQ-Traceability Tag."
tags: [concept, git, conventions, status:active]
timestamp: "2026-07-27"
resource: "../../rules/1-generic/commit-conventions.md"
migrated_from: "rules/1-generic/commit-conventions.md"
---
# Konzept: Commit-Konventionen & REQ-Traceability

> Status: **Umgesetzt — aktiv**  
> Verwandt: [Branch-Guard](branch-guard.md), [Definition of Done](definition-of-done.md)  
> Betroffen: `rules/1-generic/commit-conventions.md`, `CLAUDE.md`  

---

## 1. Übersicht & Standard

`agent-meta` erfordert ein durchgängiges, maschinenlesbares Git-Commit-Format auf Basis von **Conventional Commits**. Dies ermöglicht automatisierte Changelog-Generierung, Verfolgbarkeit von Anforderungen und saubere Code-Historien.

---

## 2. Commit-Format & Regeln

### Standard-Format
```text
<type>: <beschreibung>
```

### REQ-Traceability Format (falls `DOD_REQ_TRACEABILITY: true`)
```text
<type>(REQ-xxx): <beschreibung>
```

### Die vier Kernregeln:
1. **Type-Auswahl**: Nur standardisierte Typen verwenden (`feat`, `fix`, `chore`, `docs`, `refactor`, `test`).
2. **Sprache**: Commit-Nachrichten werden immer auf **Englisch** verfasst (`CODE_LANGUAGE`).
3. **Zeilenlänge**: Maximal **72 Zeichen** in der ersten Zeile.
4. **Grammatik**: Imperativer Schreibstil (z.B. `feat: add retry logic` statt `feat: added retry logic`).

---

## 3. Typen-Referenz

| Type | Bedeutung | Beispiel |
|---|---|---|
| `feat` | Neues Feature, neue Agenten-Rolle, neues Skript | `feat: add knowledge-migrator agent` |
| `fix` | Bugfix in Skripten, Templates oder Rules | `fix: resolve variable substitution issue` |
| `chore` | Wartung, Dependency-Updates, Refactoring ohne Verhaltensänderung | `chore: update sync.py helper functions` |
| `docs` | Reine Dokumentationsänderungen | `docs: update ARCHITECTURE.md` |
| `refactor` | Code-Restrukturierung ohne Bugfix/Feature | `refactor: clean up composition patch logic` |
| `test` | Hinzufügen oder Anpassen von Tests | `test: add unit test for sync check` |

---

## 4. Traceability zu Anforderungen (REQ)

Wenn im Projekt die Anforderungsverfolgung aktiviert ist (`DOD_REQ_TRACEABILITY: true`), MUSS jedem `feat`- oder `fix`-Commit eine REQ-ID aus `docs/REQUIREMENTS.md` vorangestellt werden:

```text
feat(REQ-086): implement smart context hash verification in sync.py
fix(REQ-042): fix subagent handoff format in gemini provider
```

Dies garantiert die direkte Rückverfolgbarkeit von jeder Zeile Code zur entsprechenden fachlichen Anforderung.