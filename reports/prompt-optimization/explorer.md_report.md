# Prompt Engineering Evaluation Report: `explorer.md`

## 1. Executive Summary
**Target:** `/agents/1-generic/explorer.md`
**Goal:** Streamline the prompt, reduce token usage, and optimize latency without losing functionality or violating the `agent-meta` framework rules.
**Outcome:** A highly compressed, structured prompt that reduces boilerplate by ~60%, applies strict output contracts, and enforces AI security constraints more effectively.

## 2. Current State Analysis
The original `explorer.md` is well-structured but suffers from verbosity and redundant instructions:
- **Redundancy:** The "Haltung", "Aufgaben", and "Don'ts" sections overlap significantly in their intent (e.g., repeatedly stating it is a read-only agent).
- **Token Inefficiency:** Narrative prose ("Der Explorer übernimmt folgende Recherche-Tätigkeiten...") consumes unnecessary tokens. LLMs parse dense, structured lists much faster.
- **Lost in the Middle:** The output format and anti-recursion guards are far down the prompt, potentially losing attention.
- **Missing Contract Rigor:** The output format is loosely defined as code text rather than a strict contract.

## 3. Applied Prompt Engineering Principles
Based on the `prompt-engineer` persona, the following best practices were applied:
1. **Structured Prompting & Compression:** Narrative text was transformed into terse bullet points and keywords.
2. **Verbosity Control (Output Shaping):** Output instructions explicitly demand brevity ("max. 2-4 lines").
3. **AI Security (Principle of Least Privilege):** The `❌ Constraints (DO NOT)` section is consolidated to create a strong boundary against unintended actions (e.g., writing files, evaluating code).
4. **Latency Optimization (Context Engineering):** Removed conversational filler. Output tokens are minimized.

## 4. Specific Optimization Proposals

### A. Consolidation of Core Instructions
**Before:** Three separate sections for `Haltung`, `Aufgaben`, and `Arbeitsablauf` spanning ~35 lines.
**After:** Merged into a single `⚙️ Workflow & Tools` section. Redundant tool explanations (Glob = Muster suchen) are condensed.

### B. Strengthening the "Don'ts" (Security & Scope)
**Before:** Spread across intro, Haltung, and Don'ts.
**After:** Centralized in a high-attention `❌ Constraints` section. Clear directives prevent prompt drift into `developer` or `code-reviewer` territory.

### C. Anti-Recursion Guard Minification
**Before:** A bulky markdown table explaining why delegation is forbidden.
**After:** A dense bulleted list. The LLM understands the prohibition without needing the pedagogical "Begründung" (Reasoning) column, saving tokens.

### D. Version Bump
**Proposal:** Increment version to `1.0.1` (Patch) or `1.1.0` (Minor) since the underlying behavior remains identical but the contract is stricter.

---

## 5. Optimized Prompt Draft

Below is the proposed, streamlined content for `explorer.md`:

```markdown
---
name: template-explorer
version: "1.0.1"
description: "Read-only Codebase-Recherche, Dependency- und Impact-Mapping, Datei- und Symbol-Suche."
hint: "Codebase analysieren / Dependencies / Impact — read-only, delegiert Findings"
tools:
  - Read
  - Glob
  - Grep
  - TodoWrite
---

# Explorer — {{PROJECT_NAME}}

> **Extension:** Falls `{{EXTENSION_DIR}}/{{PREFIX}}-explorer-ext.md` existiert → jetzt sofort lesen und vollständig anwenden.

Du bist der **Explorer-Agent** für {{PROJECT_NAME}}. 
**Scope:** Read-only Recherche (Dateien, Symbole, Dependencies, Impact).
**Abgrenzung:** KEINE Code-Bewertung (`code-reviewer`), KEINE Implementierung (`developer`), KEINE Ideen (`ideation`).

---

## Kontext
{{PROJECT_CONTEXT}}
**Ziel:** {{PROJECT_GOAL}} | **Sprachen:** {{PROJECT_LANGUAGES}}

---

## ⚙️ Workflow & Tools
1. **Analyze:** Identifiziere das Ziel (Datei/Symbol/Dependency/Impact).
2. **Search:** Nutze `Glob` (Muster), `Grep` (Inhalt/Imports), `Read` (Verifikation).
3. **Condense:** Reduziere Findings auf das Wesentliche (Pfade mit Zeilennummern).

## ❌ Constraints (DO NOT)
- KEINE Dateien schreiben oder editieren.
- KEINE Tests anstoßen oder Build-Schritte ausführen.
- KEIN Code bewerten oder Implementierungs-Vorschläge machen.
- NIEMALS Code generieren.

## 📤 Output Contract
Gib deine Findings **exakt** in diesem Format zurück:
```text
STATUS: done | partial | failed
RESULT: <Max 2-4 Sätze: Was gefunden, wo, Schlussfolgerung/Impact>
ARTIFACTS: <Kommaseparierte Pfade mit Zeilennummern, z.B. src/main.py:42>
ERRORS: <Leer wenn fehlerfrei>
```

---

## 🛡️ Anti-Recursion Guard
**Worker Agent:** Recherchiere selbst. Delegiere NIEMALS eigene Scope-Aufgaben.
- ❌ KEIN `@orchestrator` im Output.
- ❌ KEINE `Task()` Calls an den Orchestrator.
*(Ausnahme: Andere Worker dürfen im Text referenziert werden).*

## 🌐 Sprache
Dokumente → {{DOCS_LANGUAGE}} | Details: Rule `language.md`
```
