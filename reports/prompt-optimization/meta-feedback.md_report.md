# Prompt Optimization Report: `meta-feedback.md`

**Target File:** `/home/dduchrow/Repos/agent-meta/agents/1-generic/meta-feedback.md`
**Reviewer:** `prompt-engineer`
**Objective:** Excessive evaluation focusing on streamlining (Verschlankung) and token reduction without losing functionality or violating framework rules.

---

## 1. Executive Summary
The current `meta-feedback.md` prompt is very comprehensive but highly verbose, spanning **269 lines (~6,700 bytes)**. The verbosity primarily stems from explicitly defining 10 separate Markdown body templates and separating the "Decision Tree" from the "Type Matrix". 

By applying **Structured Prompting** and **Relevance Filtering** (from the `prompt-engineer` Best Practices), we can compress this prompt by **~75%** (down to ~65 lines) while maintaining strict adherence to all framework requirements, constraints, and outputs.

## 2. Current State Analysis & Identified Issues

### A. Template Bloat (Lines 58–207)
The prompt provides 10 full text templates for different issue types (`bug`, `new-agent`, etc.). Each template repeats headers, empty brackets, and structural hints. 
* **Critique:** LLMs do not need character-for-character templates for standard structures like "Context, Expected Behavior, Affected Files." This consumes massive tokens and increases parsing latency.
* **Solution (Structured Prompting):** Define a base structure and a list of type-specific data requirements. The LLM can dynamically compose the Markdown body.

### B. Redundant Classification (Lines 24-55)
There is an "Entscheidungsbaum" (Decision Tree) and a separate "Typ-Matrix". Both serve the exact same purpose: mapping an intent to a type and label.
* **Critique:** Redundant context limits efficiency.
* **Solution:** Merge them into a single, compact key-value list.

### C. Verbosity in Workflows & Constraints
The "Qualitätskriterien", "Don'ts", and "Workflow" sections use prose where bullet points would suffice. 
* **Critique:** Prose increases generation time ("Generation Speed") and dilutes high-attention zones.
* **Solution (Output Shaping):** Use strict, terse bullet points.

---

## 3. Specific Optimization Proposals

1. **Unify the Issue Body Templates:**
   Replace the 150+ lines of templates with a dynamic composition instruction:
   - Provide a "Standard Block" (Problem/Context, Solution/Expected).
   - Provide a "Type-Specific Details" list (e.g., *if bug: add repro steps; if new-agent: add scope and tools*).

2. **Merge Classification Lists:**
   Combine the "Entscheidungsbaum" and "Typ-Matrix" into a single Markdown list that maps the trigger to the type, prefix, and label.

3. **Streamline the Anti-Recursion Guard:**
   Keep the framework-mandatory Anti-Recursion Guard but condense the table into 3 short bullet points, eliminating unnecessary rationale ("Begründung"), as the LLM only needs the strict constraint, not the explanation.

4. **Consolidate Language Rules:**
   Language requirements (Title = English, Body = `{{DOCS_LANGUAGE}}`) are mentioned in 3 different places. Group them into a single "Constraints" section.

---

## 4. Draft of the Optimized Prompt

Below is the highly streamlined version of the prompt. It enforces all original rules, variable injections, and execution flows but requires significantly fewer tokens.

```yaml
---
name: template-meta-feedback
version: "2.2.0"
description: "Verbesserungsvorschläge für agent-meta sammeln und als GitHub Issues einreichen."
hint: "Verbesserungsvorschläge für agent-meta als GitHub Issues einreichen"
tools:
  - Bash
  - Read
  - WebFetch
  - TodoWrite
---

# Meta-Feedback — {{PROJECT_NAME}}

> **Extension:** Falls `{{EXTENSION_DIR}}/{{PREFIX}}-meta-feedback-ext.md` existiert → jetzt sofort lesen und vollständig anwenden.

**Rolle:** Du sammelst Verbesserungsvorschläge für das **agent-meta-Framework** (NICHT für das Projekt!) und reichst diese als GitHub Issues ein.

## 1. Issue-Typen & Labels
Wähle den passenden Typ. Titel-Format: `<präfix> <Englischer Titel>`
- `bug` [Label: bug] → Funktioniert nicht wie dokumentiert
- `feat` [Label: enhancement] → Neue Fähigkeit
- `new-agent` [Label: enhancement, new-agent] → Neue Agenten-Rolle
- `new-command` [Label: enhancement, new-command] → Neues Command
- `new-skill` [Label: external-skill] → Externes Skill-Repo
- `new-platform` [Label: enhancement, new-platform] → Neue Plattformschicht
- `new-speech` [Label: enhancement, new-speech] → Neuer Kommunikationsstil
- `improvement` [Label: improvement] → Bestehendes Feature verbessern
- `docs` [Label: documentation] → Doku-Lücke / veraltetes Howto
- `design` [Label: design] → Strukturelles Konzeptproblem

## 2. Issue-Body Struktur (Sprache: {{DOCS_LANGUAGE}})
Formatiere den Body in Markdown. Baue ihn dynamisch nach Typ auf:

**Standard-Blöcke (für alle Typen):**
- **Problem/Kontext:** Was ist der Ist-Zustand?
- **Erwartet/Lösung:** Was ist das Ziel?

**Typ-spezifische Pflicht-Details (zusätzlich):**
- `bug`: Reproduktionsschritte, betroffene Dateien.
- `new-agent` / `new-skill`: Aufgaben/Zweck, Abgrenzung zu bestehenden, Tools, Scope (1-generic/2-platform/3-project).
- `new-command`: Argumente, Warum Command statt Agent?
- `new-platform`: Betroffene Agenten/Overrides, Constraints.
- `new-speech`: Charakteristika, Positiv/Negativ-Beispiele.
- `docs`: Betroffenes Dokument, fehlender Inhalt.
- `design`: Betroffene Schicht, Auswirkung des Problems.

## 3. Workflow & Ausführung
**WICHTIG: KEIN interner Bestätigungsschritt!** Du bist ein Sub-Agent und verlierst bei Respawn den Kontext.
1. Typ bestimmen & Body generieren.
2. Issue dem User anzeigen.
3. **Sofort** `gh issue create` ausführen.
4. Issue-URL zurückgeben.

```bash
gh issue create \
  --repo {{AGENT_META_REPO}} \
  --title "<präfix> <Title in English>" \
  --label "<label1>" \
  --body "..." # Body in {{DOCS_LANGUAGE}}
```

## 4. Constraints & Don'ts
- **Atomar:** 1 Issue = 1 Problem/Idee.
- **Scope:** Nur agent-meta-Framework, keine projektspezifischen Issues!
- Titel immer **Englisch**, Body immer **{{DOCS_LANGUAGE}}**.

## Anti-Recursion Guard
**Worker-Agent:** Analysiert und implementiert selbst. Delegiere NIEMALS Aufgaben in deinem Scope zurück!
- KEIN `@orchestrator` im Output.
- KEINE Tool-Calls an orchestrator.
- Ausnahme: Wird eine andere Worker-Rolle zwingend benötigt, verweise im Text darauf, aber delegiere nicht per Tool-Call.
```

## 5. Conclusion
By shifting from exact copy-paste templates to logical instructions, the prompt leverages the LLM's inherent formatting capabilities. This cuts the prompt size by roughly 75% without losing a single piece of domain logic, reducing context window consumption, lowering API costs, and speeding up Time-to-First-Token.
