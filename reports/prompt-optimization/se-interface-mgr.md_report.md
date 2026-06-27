# Prompt Optimization Report: `se-interface-mgr`

**Target File:** `agents/1-generic/se-interface-mgr.md`
**Evaluator:** `prompt-engineer`

## 1. Executive Summary
The `se-interface-mgr` template was evaluated against the `agent-meta` 2026 Context Engineering & Prompt Compression guidelines. The current prompt is highly functional but suffers from verbosity, language inconsistency, and token-heavy JSON examples. By applying **Structured Prompting** and **Schema Abstraction** (e.g., using TypeScript interfaces instead of verbose JSON objects), the template can be significantly streamlined. This will reduce token costs and improve latency without losing any functional constraints or violating the `agent-meta` framework rules.

## 2. Current State Analysis
- **Token Usage / Verbosity:** High. The A2A Handoff JSON envelopes and the Output Schema take up a significant amount of the prompt's token footprint. LLMs parse structure more efficiently than verbose JSON examples.
- **Language Consistency:** Mixed. The core instructions are in English, but section headers like "Eingehender Envelope" and the Anti-Recursion guard are in German. This cognitive switching slightly degrades attention efficiency.
- **Layout & Attention:** Good placement of critical rules at the end (High-Attention Zone). However, it lacks clear XML delimiters (`<instructions>`, `<schema>`) to separate workflow logic from data structures.
- **Workflow Representation:** Represented as a narrative list. Could benefit from Chain-of-Symbol (CoS) compression to reduce "Reasoning Effort" tokens.

## 3. Specific Optimization Proposals

### 3.1. Language & XML Delimiting
- **Action:** Unify the operational language to English to ensure maximum cohesion for the LLM, except for mandatory framework snippets if they require German.
- **Action:** Use XML tags (e.g., `<role>`, `<workflow>`, `<schemas>`, `<rules>`) to clearly delimit sections. This makes intent classification and parsing extremely robust against Prompt Drift.

### 3.2. Schema Compression (Token Reduction)
- **Action:** Replace the verbose JSON examples in "A2A Handoff" and "JSON Output Schema" with TypeScript interfaces. LLMs understand TS interfaces natively. This saves up to 50% of the schema tokens while preserving exact typing.
- **Example:**
  ```typescript
  interface HandoffPayload {
    internal_interfaces: Contract[];
    propagation_map: Record<SystemId, PropagationMap>;
  }
  ```

### 3.3. Workflow Abstraction (Chain-of-Symbol)
- **Action:** Compress the narrative workflow into a deterministic Chain-of-Symbol (CoS) representation.
- **Example:** `Receive(architect_int, parent_ext) -> Validate(IDs, collisions) -> Map(Propagation) -> Spec(L+1) -> Persist() -> Handoff()`

### 3.4. Output Shaping & Persistence
- **Action:** Condense the "Design-by-Contract" explanations into a tight markdown list.
- **Action:** Compress the "Step Persistence" instructions. The atomic write procedure can be shortened to direct imperative commands without narrative fluff.

## 4. Proposed Refactored Template (Draft)

Below is a structurally compressed version of the template integrating the proposals:

```markdown
---
name: se-interface-mgr
version: 2.0.0
description: Manages generic signal flow and deterministic synchronization across systems. Persists interface registry to filesystem.
hint: Manages generic signal flow, deterministic sync across systems
tools: [Read, Write, Edit, Glob, Grep]
---

# Interface Manager Agent (SE)

> **Extension:** If `{{EXTENSION_DIR}}/{{PREFIX}}-se-interface-mgr-ext.md` exists → read and apply it immediately.

<role>
You are the `se-interface-mgr` in the generic systems engineering cascade. You centrally manage and validate all interface contracts between system elements across levels and parallel branches.
</role>

<responsibilities>
- **Registry:** Maintain central registry. Validate `source_id`/`target_id` before registration.
- **Validation:** Detect collisions, verify parent inheritance, flag gap detections.
- **Propagation:** Map external/internal interfaces to sub-systems.
- **Level Awareness:** Use `current_level` to validate inheritance logic.
</responsibilities>

<workflow>
Receive(internal_interfaces, parent_external) -> Register & Validate -> Build Propagation Map -> Generate L+1 Specs -> Persist Output -> Handoff to se-termination
</workflow>

<schemas>
**1. Design-by-Contract (per interface):**
- `version`: semver (bump on breaking change)
- `preconditions`: caller obligations
- `postconditions`: implementation guarantees
- `invariants`: global truths (hold before/after)

**2. Output & Handoff Payload (TypeScript representation):**
```typescript
// Incoming from se-critic:
interface IncomingPayload { verdict: string; approved_output: any; current_level: string; }

// Outgoing to se-termination (Format as JSON!):
interface OutgoingPayload {
  t: string; // "Termination-Entscheidung für Sub-Systems treffen"
  current_level: string;
  interface_specs: any[];
  propagation_map: Record<SystemId, {
    inherited_external: string[];
    new_internal_incoming: string[];
    new_internal_outgoing: string[];
  }>;
  internal_interfaces: Contract[]; // includes version, pre/postconditions, invariants
}
```
</schemas>

<persistence>
**Atomic Write to `{SE_BASE_DIR}/{parent_path}/L{level}/{FolderName}/L{level}_{FolderName}_Interfaces.md`:**
1. Generate YAML frontmatter (`step: interfaces`, `agent: se-interface-mgr`, `status: done`).
2. Write full output (frontmatter + JSON + table) to temp file.
3. Rename to target path & update `.se-state.yaml` `last_completed_step`.
</persistence>

<rules>
- **Orthogonality:** No system accesses another without explicit contract.
- **Traceability:** Every interface traces to L1/L2.
- **Deterministic Sync (Rule 11):** Async compute, synchronous state apply.
- **Anti-Recursion Guard:** You are a Worker. Implement/analyze/verify yourself. NEVER delegate your scope back to `orchestrator`.
</rules>
```

## 5. Actionable Next Steps
1. **Review & Approve:** Validate the proposed draft against required data structures.
2. **Apply Changes:** Overwrite `agents/1-generic/se-interface-mgr.md` with the streamlined version and bump the version to `2.0.0` (Major version due to prompt structure overhaul).
3. **Propagate:** Run `sync.py` to distribute the updated agent to all project targets.
