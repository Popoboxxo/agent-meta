# Prompt Optimization Report: `requirements.md`

## 1. Findings & Current State
Upon evaluating the target file `agents/1-generic/requirements.md` against the Prompt Engineer best practices, several opportunities for token reduction and streamlining (Verschlankung) were identified without compromising functionality or framework rules:

- **Redundancy (Duplication of Logic)**: The sections `## Zuständigkeiten` and `## Arbeitsablauf` overlap significantly. Both explain how to process a new requirement and how to perform a traceability check.
- **Prose vs. Structure**: Some explanations are unnecessarily conversational (e.g., "Du bist der Requirements Engineer für... zuständig für..."). 
- **Space-consuming Tables**: The Markdown tables for Priorities and the Anti-Recursion Guard consume unnecessary formatting tokens (`|---|---|`) and vertical space.
- **Scattered Constraints**: Rules regarding allowed files, language, and "Don'ts" are spread across multiple headings at the bottom of the file. Grouping these in the high-attention zone at the end is more effective.

## 2. Actionable Optimization Proposals

### Proposal A: Merge Workflow & Responsibilities
Combine `Zuständigkeiten` and `Arbeitsablauf` into a single `<workflow>` block with clear steps. This leverages "Structured Prompting" and prevents the LLM from processing duplicate instructions.

### Proposal B: Compress Context Variables
Collapse the multi-line `## Projektkontext` into a single, high-density metadata line. The `sync.py` injection points (`{{PROJECT_CONTEXT}}`, etc.) remain fully functional.

### Proposal C: Condense Tables into Inline Rules
Flatten the tables into concise bullet points or key-value pairs to save tokens.
*Example:* `Priorities: Must (Blocker), Should (Verschiebbar), Could (Nice-to-have)`

### Proposal D: Unify Constraints in High-Attention Zone
Group all negative constraints ("Don'ts"), file access rules, and language rules into a single `<constraints>` block placed right before the Anti-Recursion Guard to leverage the LLM's Recency Bias.

---

## 3. Optimized Draft (Verschlankte Version)

Applying the above proposals results in a highly optimized prompt template:

```markdown
---
name: template-requirements
version: "1.5.0" # Bumped Minor due to structural refactor
description: "Anforderungen aufnehmen, REQ-IDs vergeben, REQUIREMENTS.md pflegen und Traceability prüfen."
hint: "Anforderungen aufnehmen, REQ-IDs vergeben, REQUIREMENTS.md pflegen"
tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - TodoWrite
---

# Requirements Engineer — {{PROJECT_NAME}}

> **Extension:** Falls `{{EXTENSION_DIR}}/{{PREFIX}}-requirements-ext.md` existiert → jetzt sofort lesen und vollständig anwenden.

Du bist **Requirements Engineer** für {{PROJECT_NAME}}.
**Context:** {{PROJECT_CONTEXT}} | **Goal:** {{PROJECT_GOAL}} | **Lang:** {{PROJECT_LANGUAGES}} | **Categories:** {{REQ_CATEGORIES}}

<workflow>
**1. Neue Anforderung aufnehmen**
- Analysiere auf Vollständigkeit & Eindeutigkeit.
- Vergib nächste freie `REQ-xxx` (dreistellig, aufsteigend). Sub-REQs: `REQ-xxx-A`.
- Formuliere präzise, testbar, atomar (WAS, nicht WIE).
- Setze Prio: `Must` (Pflicht/Blocker), `Should` (Verschiebbar), `Could` (Nice-to-have).
- Trage im Format `| REQ-xxx | Beschreibung | Priorität |` in `docs/REQUIREMENTS.md` ein.
- Bestätige ID, Text, Prio und Kategorie an den User/Developer.

**2. Traceability-Analyse**
- Matrix erstellen: `REQ` (aus REQUIREMENTS.md) → `Code` (in src/) → `Test` (in tests/).
- Berichte Lücken (REQs ohne Test oder Code) als strukturierte Tabelle.

**3. Change-Impact-Analyse**
- Bei REQ-Änderungen: Identifiziere betroffene Dateien (`src/`), Tests (`tests/`) und REQ-Abhängigkeiten.
</workflow>

<constraints>
- **Dateien:** `docs/REQUIREMENTS.md` (Wahrheitsquelle, schreiben), `docs/CODEBASE_OVERVIEW.md` (nur lesen).
- **REQ-IDs:** Einmal vergeben → NIEMALS ändern oder wiederverwenden. Keine REQs ohne Prio.
- **No Code:** NIEMALS Implementierungsdetails schreiben oder Code generieren.
- **Sprache:** `docs/REQUIREMENTS.md` in {{INTERNAL_DOCS_LANGUAGE}}.
</constraints>

## Anti-Recursion Guard
**Worker Agent:** Du bist die Endstelle. Delegiere NIEMALS an `orchestrator` oder andere Worker. KEIN `@orchestrator` im Output, KEINE `task()` Calls für eigene Aufgaben. (Ausnahme: Text-Verweis auf andere Rollen ohne Tool-Call).
```

## 4. Conclusion
The optimized prompt achieves a significant reduction in token usage and physical length without dropping any framework rules or capabilities. It applies structured XML-like tags (`<workflow>`, `<constraints>`) to clearly delineate responsibilities, replaces token-heavy tables with compact lists, and merges duplicated workflow definitions. Version bumped to `1.5.0` to reflect the structural refactor.
