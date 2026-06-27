# Prompt Engineering Evaluation Report: `code-reviewer.md`

**Target File:** `agents/1-generic/code-reviewer.md`
**Objective:** Streamlining & Token Reduction without losing functionality (Framework Compliance).
**Evaluator:** Prompt Engineer Agent

## 1. Executive Summary

The current `code-reviewer.md` is functional and comprehensive but suffers from significant verbosity, particularly in its output contracts. By applying Advanced Latency Optimization (Context Engineering 2026) and Prompt Compression, we can drastically reduce both **input tokens** (prompt size) and **output tokens** (generation latency) while maintaining the strict `agent-meta` framework rules.

## 2. Current State Analysis

- **Total Size:** ~334 lines, ~11.4 KB.
- **Redundancy:** The prompt defines both a massive 70-line JSON example and a 40-line Markdown template for the exact same data structure.
- **Verbosity:** Output JSON keys are long (e.g., `clean_code_findings`, `recommendation`), increasing generation time and cost.
- **Textual Workflows:** The review workflows are written as lists, which can be compressed using Chain-of-Symbol (CoS).
- **Standard Blocks:** The Anti-Recursion Guard uses a large table for simple rules, adding unnecessary markdown overhead.

## 3. Actionable Optimization Proposals

### Proposal 1: Implement Output Shaping & Key Minification (Latency Reduction)
**Why:** LLM latency scales directly with output tokens. Long JSON keys (e.g., `"recommendation"`, `"clean_code_findings"`) waste tokens on every generation.
**Action:** Replace the 70-line JSON mock data block with a compact TypeScript-style interface using short keys.
**Draft Snippet:**
```typescript
// Ersetze das lange JSON Beispiel durch einen kompakten Schema-Vertrag:
interface ReviewReport {
  id: string; scope: string; files: string[];
  finds: { f: string; l: number; p: string; sev: "minor"|"major"; desc: string; rec: string }[];
  blast: { lvl: 1|2|3|4; files: string[]; mods: string[]; break: string[]; mig: boolean };
  req_trace?: { exp: string[]; found: {id: string, f: string, l: number}[]; miss: string[] };
  rating: { read: string; main: string; rob: string; eff: string; sec: string; overall: string };
  verdict: "APPROVED" | "APPROVED_WITH_RECOMMS" | "CHANGES_REQUESTED" | "BLOCKED" | "REVISE";
  blockers: string[]; recs: string[];
}
```
*Impact:* ~60% reduction in output tokens per finding, leading to noticeably faster response times.

### Proposal 2: Consolidate Reporting Formats (Relevance Filtering)
**Why:** The prompt explicitly defines the JSON structure AND a 40-line Markdown table structure. This is redundant. LLMs can format data into markdown intuitively if told the structure.
**Action:** Delete the `## Berichtsformat (Markdown)` template block completely. Instead, use a single sentence:
> *"Falls Markdown gefordert ist: Erstelle einen kompakten Bericht mit den Abschnitten Scope, Blast-Radius, Findings (als Tabelle), [REQ-Traceability] und Gesamturteil."*

### Proposal 3: Chain-of-Symbol (CoS) for Workflows
**Why:** Textual step-by-step lists consume more tokens and are parsed slower than symbolic chains.
**Action:** Compress the "Review-Workflows" section.
**Draft Snippet:**
- **Quick Review (1 File):** `Read -> SOLID/DRY/KISS -> Blast-Radius -> [REQ] -> Rating A-F`
- **Full Review (Multi):** `Identify Files -> File-level Checks -> Cross-File DRY -> Global Blast -> [REQ] -> Global Rating`
- **Pre-Merge Gate:** `Diff -> Blast -> IF(CRITICAL) escalate -> IF(D|F) block -> ELSE approve`

### Proposal 4: Compress Standard Tables
**Why:** The Validator comparison and the Anti-Recursion Guard tables contain repetitive filler text.
**Action:** 
- **Validator Diff:** Condense into a one-liner: *"Du: Qualität (Clean Code, Blast). Validator: Korrektheit (DoD, Tests)."*
- **Anti-Recursion Guard:** Condense the table into a strict text block without losing the Hard Rules.
**Draft Snippet:**
> **Anti-Recursion Guard:** Worker-Agent! Delegiere NIEMALS in deinem Scope an `orchestrator` oder Worker zurück. VERBOTEN: `@orchestrator`, `Task()`-Calls, "Delegiere an...". Du bist die Endstelle! (Ausnahme: Passiver Verweis im Text auf andere Rollen erlaubt).

### Proposal 5: Merge Reflection-Loop Modus
**Why:** Another redundant schema definition (Lines 211-225).
**Action:** Define it as a simple subset modifier:
> *"In Reflection-Loop, only output: `{\"verdict\": \"REVISE\", \"iter\": 1, \"hints\": [\"... actionable hint...\"]}`"*

## 4. Expected Impact

Implementing these changes will:
1. **Reduce Prompt Size:** By approx. 120-140 lines (~40% token reduction).
2. **Decrease Generation Latency:** By outputting smaller JSON payloads with minified keys (`finds` vs `clean_code_findings`).
3. **Increase Reliability:** A tighter contract provides stricter boundaries for the LLM output compared to mock JSON data.
4. **Maintain Compliance:** All variables (`{{PROJECT_NAME}}`, `{{DOD_REQ_TRACEABILITY}}`) and absolute rule constraints (Blast-Radius definitions, Anti-Recursion) remain perfectly intact.
