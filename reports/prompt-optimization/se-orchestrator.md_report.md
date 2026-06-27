# Prompt Optimization Report: `se-orchestrator`

## 1. Executive Summary & Current State
**Target:** `agents/1-generic/se-orchestrator.md`
**Status:** DEPRECATED (Maintained for backward compatibility).
**Current Size:** ~284 lines, ~15.2 KB.
**Observation:** The prompt is highly narrative, containing verbose ASCII-art diagrams, pretty-printed JSON examples, and overlapping sections (Workflow, Pipelines, V&V Integration). As a deprecated agent, minimizing its token footprint is crucial to reduce system-wide load without breaking legacy workflows.

## 2. Optimization Strategy (Context Engineering 2026)
Following the `prompt-engineer` persona rules (OpenAI Best Practices, Prompt Compression, Context Engineering 2026), the following streamlining techniques should be applied:

### 2.1 Structured Prompting & De-Duplication
**Issue:** The prompt describes the 6-stage breakdown, the V&V Integration, the Pipeline A/B flows, and the 9-step Workflow in four separate, redundant sections.
**Action:** Consolidate these into a single, dense matrix or list.
**Implementation:**
- Merge the `V&V Integration (Right Wing)` directly into the `Pipeline A — System-Level` definition.
- Remove the narrative `Workflow` section entirely, as its constraints are already covered by the Pipeline definitions.
- *Token Savings:* High. Reduces repetition and LLM reasoning buffer overhead.

### 2.2 JSON Minification & Output Shaping
**Issue:** Large, pretty-printed JSON blocks for A2A Handoffs and Output Structure consume excessive structural tokens (newlines, spaces).
**Action:** Compress JSON examples into single lines or utilize strict schema referencing without inline examples.
**Implementation:**
- Replace the formatted `A2A Handoff` JSON with inline JSON: `{"protocol_version":"1.0.0","handoff_id":"...","source_agent":"orchestrator",...}`.
- Remove redundant fields in the examples that do not drive behavior.
- *Token Savings:* Medium, but improves attention on actual instructions.

### 2.3 Chain-of-Symbol (CoS) vs ASCII Art
**Issue:** The `Zig-Zag Traceability Matrix` and `Pipeline Routing` flows use large ASCII diagrams that are token-heavy and susceptible to "Lost in the Middle" parsing degradation.
**Action:** Use Chain-of-Symbol abstractions.
**Implementation:**
- Replace the Zig-Zag matrix with a symbolic rule: `Trace: [L(n) Need] <-satisfies- [L(n+1) Req] -allocates-> [L(n+1) Arch] <-satisfies- [L(n+2) Req]`.
- Replace Pipeline flows with linear symbol chains: `Pipeline A: se-req -> se-critic(req) -> se-arch -> se-critic(arch) -> se-if-mgr -> se-term -> [leaf/continue]`.
- *Token Savings:* High. Faster token parsing.

### 2.4 Verbosity Control for Routing & Tier Selection
**Issue:** The `Implementation Phase Routing`, `Tier Selection Matrix`, and `Routing Inputs` are written in a prosaic, conversational style.
**Action:** Apply Relevance Filtering and Output Shaping. Convert to dense Key-Value rules.
**Implementation:**
- `Tier Routing:`
  - `junior`: 0-1 IF, trivial.
  - `developer`: 2-4 IF, standard.
  - `senior`: 5+ IF, cross-cutting/boundary/critical.
- `Escalations:` `junior->dev`, `dev->senior`. IF changes -> `se-architect`.
- *Token Savings:* Medium. Accelerates inference latency.

### 2.5 Deprecation Metadata Refinement
**Issue:** The deprecation warning is repeated in `description`, `hint`, and text.
**Action:** Keep `deprecated: true` and `deprecated_by` in the frontmatter. Condense the description and hint to avoid bloating the global `CLAUDE.md`/`AGENTS.md` framework graphs.
**Implementation:** Remove the verbose text from the `description` block and rely purely on the `deprecated` flag.

## 3. Actionable Next Steps
1. **Refactor JSON:** Minify lines 32-45 and 240-274 into single-line `<schema>` blocks.
2. **Replace Diagrams:** Condense lines 85-99 and 143-153 into linear text logic using Chain-of-Symbol (`->`, `<-`).
3. **Merge Workflow:** Delete lines 226-236 (Workflow) and integrate unique constraints (like `decision: continue`) into the core Pipeline definitions.
4. **Condense Routing:** Flatten the Tier Selection Matrix (lines 186-192) into a comma-separated constraints list.

## 4. Expected Impact
By applying these context engineering practices, the `se-orchestrator.md` file can be reduced by approximately **40-50% in token size**. This provides lower latency, reduced token costs, and stricter adherence to the agent-meta framework's anti-recursion policies, all without losing its legacy routing capabilities.
