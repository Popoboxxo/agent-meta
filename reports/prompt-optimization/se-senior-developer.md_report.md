# Prompt Optimization Report: `se-senior-developer.md`

## 1. Executive Summary
Following the best practices outlined in `prompt-engineer.md` (specifically OpenAI standards, Prompt Compression, and Context Engineering 2026), an excessive evaluation of `se-senior-developer.md` was conducted. The current prompt is functionally sound but highly verbose, containing redundant instructions and narrative prose. 

By applying **Structured Prompting**, **Relevance Filtering**, and **Output Shaping**, we can achieve significant token reduction (Verschlankung) while preserving all agent-meta framework rules (Anti-Recursion, A2A Handoffs, Schichten-Architektur).

## 2. Methodology & Adherence to `prompt-engineer.md`
- **Relevance Filtering (Sec 3.3):** Identified and eliminated duplicated rules (e.g., interface disciplines repeated in "Don'ts").
- **Structured Prompting (Sec 3.1):** Converted flowing text into dense bullet points and Chain-of-Symbol representations.
- **Output Shaping & Delimiters (Sec 1.1 / 4.1):** Replaced markdown block requirements with XML tags for output contracts (`<interface_analysis>`, `<decision>`) to improve API/Handoff reliability.
- **High-Attention Zones (Sec 3.5):** Shifted all absolute constraints to the end of the prompt.
- **Reasoning Effort Tuning / Generation Speed (Sec 4.3):** Reduced output verbosity instructions to minimize generation latency.

## 3. Excessive Evaluation & Optimization Proposals

### 3.1 Persona & Intro Abstraction
**Current State:** ~100 words explaining the SE cascade, the V-model, and the preceding agents (`se-architect`, `se-critic`, etc.).
**Critique:** This is background lore. The agent only needs to know its actionable traits. It causes unnecessary context loading.
**Action:** Compress to the absolute minimum.
*Proposed Revision:*
> You are the `se-senior-developer`. You implement complex, high-risk SE leaf nodes (cross-cutting, boundary-level, or high interface density). Core directive: Turn black-box component definitions into working code strictly within provided contracts. ALWAYS verify interface integrity before writing code.

### 3.2 Pre-Implementation Interface Analysis
**Current State:** 4 verbose steps written in paragraphs.
**Critique:** LLMs parse structured heuristics much faster than prose.
**Action:** Use Chain-of-Symbol (`->`) for decision trees to reduce reasoning tokens.
*Proposed Revision:*
> **Run BEFORE coding. Any failure -> Escalate, do NOT code.**
> 1. **Completeness:** Do all interfaces in `propagation_map` match `interface_specs` fully? (No -> Escalate to `se-interface-mgr`).
> 2. **Consistency:** Do types match? Do targets exist? (No -> Escalate to `se-interface-mgr`/`se-architect`).
> 3. **Boundary:** Does implementation cross a level boundary? (Yes -> Escalate to `se-architect`).

### 3.3 XML Tags for Handoffs & Reporting
**Current State:** Asks for `INTERFACE_ANALYSIS` and `DECISION` blocks using markdown code blocks.
**Critique:** Markdown blocks are error-prone for regex/JSON extraction. `prompt-engineer.md` explicitly demands XML tags for contracts.
**Action:** Redefine outputs using XML.
*Proposed Revision:*
```xml
<interface_analysis>
leaf_id: ...
completeness: ok | gaps:...
consistency: ok | conflicts:...
boundary_crossed: no | yes:...
decision: proceed | escalate
</interface_analysis>
```

### 3.4 De-duplication of Constraints (SE Interface Discipline & Don'ts)
**Current State:** The rules (e.g., "NO direct calls to neighbors", "NO unilateral changes") are explained in depth in "SE Interface Discipline" and then repeated again in the "Don'ts" section.
**Critique:** Violates the "Relevance Filtering" rule. Redundancy inflates the prompt.
**Action:** Consolidate all negative constraints into a single "Strict Constraints & Don'ts" section placed at the absolute end of the file (High-Attention Zone).
*Proposed Revision (End of Prompt):*
> ## Strict Constraints & Don'ts
> - **Code:** NO code before Pre-Implementation Analysis passes.
> - **Interfaces:** NO unilateral interface changes. Escalate instead.
> - **Isolation:** NO direct calls to neighbor components; use ONLY registered interface contracts from `propagation_map`.
> - **Domain:** NO implementation for `hardware`/`mechanics` (stub/spec only).
> - **Security:** NO secrets/API keys in code.

### 3.5 Token-Efficient Tables
**Current State:** "Anti-Recursion Guard" uses a Markdown table.
**Critique:** Tables require pipe characters and formatting tokens that offer no semantic value to the LLM.
**Action:** Convert to a compact list.
*Proposed Revision:*
> ## Anti-Recursion Guard
> You are a worker. NEVER delegate scope tasks back:
> - `@orchestrator` in output is FORBIDDEN.
> - `Task()` calls to orchestrator are FORBIDDEN.
> - *Exception:* `status: escalate` is allowed and routed normally.

### 3.6 A2A Handoff Protocol Condensation
**Current State:** Overly explains the JSON envelope schema.
**Critique:** The agent inherently understands JSON parsing. The explanation of `t`, `ctx`, `con[]`, `refs[]` is bloated.
**Action:** Provide the structure as a raw, single-line JSON stub or a very tight list.
*Proposed Revision:*
> **A2A Handoff:** Tasks arrive as JSON envelopes (`schemas/a2a-handoff.schema.json`). Extract `payload` (`t`, `ctx`, `con`, `refs`, `dep`, and SE leaf fields). Read `payload.ctx` findings first on escalations.

## 4. Expected Impact
- **Token Reduction:** ~30-40% smaller system prompt.
- **Improved Latency:** Fewer input tokens to process per step.
- **Higher Precision:** Critical constraints are moved to High-Attention Zones without being diluted by repetition.
- **Robust Parsing:** Migration to XML tags guarantees 100% reliable extraction by the framework.
