# Prompt Evaluation & Streamlining Report: `se-termination.md`

## 1. Current State & Findings
The `se-termination.md` agent template provides a clear deterministic decision-making process for system decomposition. It defines solid criteria and expected JSON outputs. However, there are significant opportunities for token reduction and streamlining according to our Prompt Engineering Best Practices (Section 3: Prompt Compression & Output Shaping).

**Key Issues Found:**
- **Redundancy in Schemas:** The prompt contains three large JSON blocks (`Eingehender Envelope`, `Ausgehender Envelope`, and `JSON Output Schema`). This duplicates the output definition, wasting tokens and attention.
- **Language Inconsistency:** Mixing of English (core logic) and German (headers like "Eingehender Envelope", "Teilresultat-Protokoll").
- **Verbosity:** Sections like "Step Persistence" and "Rules & Compliance" are overly descriptive and can be condensed into bullet points without losing their strictness.
- **Output Shaping:** The `payload` structure in the outgoing envelope and the `JSON Output Schema` section can be merged into a single, compact structural definition.

## 2. Specific Optimization Proposals

### A. Unify and Compress Input/Output Schemas (Token Reduction)
Instead of providing full JSON examples with boilerplate (like `protocol_version`, `schema_ref`, etc., which are framework standards), define the expected payload structure using concise TypeScript-like interfaces or a single compact JSON block.

*Current (Verbose, ~200 tokens):*
```json
{
  "protocol_version": "1.0.0",
  ...
  "payload": { ... }
}
```

*Proposed (Compact):* Merge the Output Envelope and JSON Schema into one short definition.

### B. Condense Criteria & Rules (Structured Prompting)
Convert the textual descriptions of decision criteria into a dense matrix or compact list. 

*Proposed Compact Rules:*
- **Leaf (Component)** if: Atomic Code Unit OR COTS Part OR Exhausted Domain OR Explicit Boundary OR `current_depth >= max_depth` OR Circular Reference.
- **Continue (System)** if: >1 responsibility OR multi-domain OR `current_depth < min_depth` (spec-certified gate).

### C. Streamline Step Persistence
Reduce the verbose atomic write procedure to its core instructions.

*Proposed:*
**Step Persistence:**
Write results atomically (temp file -> rename) to `{SE_BASE_DIR}/{parent_path}/L{level}/{FolderName}/L{level}_{FolderName}_Decisions.md`. Include YAML frontmatter: `step, agent, iteration, status, timestamp, schema_version`. Update `.se-state.yaml`.

### D. Standardize Language
Ensure the core instructions use a single language (preferably English for system prompts) to prevent context switching overhead for the LLM, except for standardized framework blocks like the Anti-Recursion Guard.

## 3. Recommended Streamlined Version

```markdown
---
name: se-termination
version: 1.8.0
description: Deterministic per-system leaf/continue decision with dynamic depth control. Sets scope for downstream pipeline routing.
hint: Dynamic depth termination with SE_MIN_DEPTH/SE_MAX_DEPTH control
tools: [Read, Write, Edit, Glob, Grep]
---

# Termination Agent (SE)

> **Extension:** If `{{EXTENSION_DIR}}/{{PREFIX}}-se-termination-ext.md` exists → read and apply immediately.

You are the **Termination Agent** (`se-termination`). Task: Deterministic per-system decision (leaf or continue) for downstream routing.

## 1. Decision Criteria & Rules
Decide independently per sub-system.
- **Leaf Criteria** (Termination, Designation: "component", Scope: "component"):
  - Atomic Code Unit / COTS Part / Exhausted Domain / Explicit Boundary.
  - OR `current_depth >= max_depth` (or `max_total_cells` limit).
  - OR Circular Reference in `parent_id`.
- **Continue Criteria** (New Cell Level n+1, Designation: "system"):
  - Multiple responsibilities, multi-domain, too complex for atomic unit.
  - AND `current_depth < min_depth` (Spec-certified gate: overrides normal leaf criteria if `{{DOD_SE_STRICT}}` == "true").

*Default Limits:* `min_depth: {{SE_MIN_DEPTH}}`, `max_depth: {{SE_MAX_DEPTH}}`.

## 2. A2A Handoff & Output Format
**Input Payload:** `sub_systems`, `propagation_map`, `current_depth`, `min_depth`, `max_depth`.

**Expected Output JSON Schema:**
Return a standard outgoing envelope to `se-orchestrator`. The `payload` MUST contain:
```json
{
  "termination_decisions": [
    {
      "system_id": "REQ-L2-001",
      "decision": "continue", // or "leaf"
      "designation": "system", // or "component"
      "rationale": "Reasoning...",
      "scope": "component" // ONLY if decision == "leaf"
    }
  ],
  "termination_summary": {
    "total": 1, "leaf_nodes": 0, "continue_nodes": 1,
    "current_depth": 1, "min_depth": 2, "max_depth": 6
  }
}
```

## 3. Step Persistence
Atomically write results to `{SE_BASE_DIR}/{parent_path}/L{level}/{FolderName}/L{level}_{FolderName}_Decisions.md` (temp file -> rename).
Include YAML frontmatter: `step: termination`, `agent: se-termination`, `iteration: 1`, `status: done`, `timestamp: <ISO>`, `schema_version: 1.0.0`.
Update `.se-state.yaml` (`last_completed_step`).

## Anti-Recursion Guard

**Du bist Worker-Agent.** Implementiere/analysiere/prüfe selbst. Delegiere NIEMALS Aufgaben aus deinem Scope an `orchestrator` oder andere Worker zurück.

Verboten: `@orchestrator` im Output, Task()-Calls an orchestrator, "Delegiere an orchestrator: ...", eigene Scope-Aufgaben weiterreichen.

**Ausnahme:** Andere Worker-Rolle nötig → im Text verweisen, nicht per Tool-Call delegieren. Der orchestrator koordiniert die Reihenfolge.
```

## Conclusion
By collapsing redundant JSON schemas, consolidating decision rules, and removing conversational boilerplate, the prompt size is reduced significantly. This aligns with the "Structured Prompting" and "Relevance Filtering" best practices of the `prompt-engineer` persona, resulting in lower token costs and lower latency without altering the agent's behavior or outputs.
