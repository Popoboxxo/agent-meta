# Prompt Optimization Report: `developer.md`

## 1. Executive Summary
This report evaluates the `/home/dduchrow/Repos/agent-meta/agents/1-generic/developer.md` template against the best practices defined in the `prompt-engineer.md` persona. The evaluation focuses on streamlining (Verschlankung), token reduction, and adherence to the agent-meta framework rules.

## 2. Findings & Violations

1. **Provider-Specific Path Violation (Critical):**
   - **Location:** `## Commit-Konventionen`
   - **Issue:** The prompt explicitly references `.claude/rules/commit-conventions.md`. This violates the core architectural rule for `1-generic` templates, which forbids provider-specific paths or names.
2. **Verbosity in A2A Handoff (Token Waste):**
   - **Location:** `## A2A Handoff — Eingehende Tasks`
   - **Issue:** The section uses extensive prose to explain the JSON schema and HITL workflow. This can be significantly compressed into structured key-value pairs and bullet points, aligning with the "Structured Prompting" and "Context Engineering" best practices.
3. **Repetitive/Verbose Instructions:**
   - **Location:** `## Reflection-Loop: Revision-Modus` and `## Deine Zuständigkeiten`
   - **Issue:** The instructions are written in narrative prose. They can be transformed into dense, symbol-heavy checklists (e.g., using `->` or bold tags) to reduce reasoning tokens and latency.
4. **Scattered Code Conventions:**
   - **Location:** `## Code-Konventionen`
   - **Issue:** The general rules ("Named Exports only", "kebab-case", "Fehlerbehandlung") take up unnecessary vertical space. They can be combined into a single compact list.

## 3. Specific Optimization Proposals

### Proposal 1: Fix Provider-Specific Path
Replace the hardcoded `.claude` path with a generic reference or a framework placeholder.
**Before:**
`→ Vollständige Tabelle und Regeln: Rule .claude/rules/commit-conventions.md (automatisch geladen)`
**After:**
`→ Vollständige Regeln: Globale Rule "commit-conventions.md" anwenden.`

### Proposal 2: Compress A2A Handoff
Use dense, structured formatting to reduce tokens and improve parser efficiency.
**Before:**
*Extensive prose about schemas, compact mode, and HITL.*
**After:**
```markdown
## A2A Handoff (Tasks)
- **Parse:** Extract `t` (Task), `ctx` (Context), `con` (Constraints) aus `payload` (bzw. Array bei `batch: true`).
- **HITL (`requires_human_approval: true`):** VOR Ausführung User fragen: `"[Aufgabe aus payload.t]. Ausführen? (yes/no)"`. Bei "no" → Abbruch & Meldung.
- **Output:**
  STATUS: done|partial|failed|escalate
  SUMMARY: <1-Satz>
  FILES_CHANGED: <liste>
```

### Proposal 3: Streamline Responsibilities & Workflow
Combine the workflow into a single, unambiguous execution chain.
**After:**
```markdown
## Workflow & Zuständigkeiten
1. **Verstehen:** Minimalen Scope anhand Aufgabe{{#if DOD_REQ_TRACEABILITY}} und REQ-ID (aus `docs/REQUIREMENTS.md`){{/if}} erfassen.
2. **Implementieren:** Code-Konventionen strikt einhalten.{{#if DOD_TESTS_REQUIRED}} Kein Code ohne Tests.{{/if}}
3. **Validieren:** Bestehende Tests dürfen nicht brechen.
{{#if DOD_REQ_TRACEABILITY}}4. **Commit:** Format `<type>(REQ-xxx): <beschreibung>`{{/if}}
```

### Proposal 4: Densify Code Conventions & Reflection-Loop
**Reflection-Loop After:**
```markdown
## Reflection-Loop (Revision)
- **Scope:** Behebe NUR monierte Findings. Keine anderen Änderungen.
- **Feedback:** Bestätige Fixes in der Antwort.
- **Awareness:** Priorisiere kritische Fehler bei finalen Runden (X==Y). Eskaliere Unlösbares als "blocked".
```

## 4. Conclusion
By applying these structural changes, the `developer.md` prompt will consume significantly fewer tokens, reduce LLM latency (by minimizing parsing/reasoning overhead), and correctly adhere to the `1-generic` provider-agnostic framework rules, all without losing any operational strictness.
