# Prompt Optimization Report: `se-architect`

**Date:** 2026-06-27
**Target File:** `agents/1-generic/se-architect.md`
**Persona:** Prompt Engineer (agent-meta Framework)

## 1. Executive Summary
The current `se-architect` prompt is highly structured and provides excellent context for systems engineering. However, it suffers from significant **token bloat** primarily due to large, verbatim JSON examples for A2A handoffs and output schemas. By applying **Structured Prompting** and **Template Abstraction** (as defined in the `prompt-engineer` best practices), we can compress these sections by ~50-60%, reducing both generation latency and token costs without losing any functional rigor.

## 2. Current State Analysis
**Strengths:**
- Clear persona definition and strict context boundary setting (Input limits, no hallucination).
- Good use of Intent Classification (Responsibilities 1-7).
- Anti-Recursion Guard is present and conforms to framework rules.

**Areas for Improvement (Bloat & Risk):**
1. **A2A Envelope Boilerplate:** The `A2A Handoff — Input` and `A2A Handoff — Output` sections use full, multi-line JSON blocks to explain routing envelopes. This is verbose and distracts the LLM from the actual `payload` semantics.
2. **JSON Output Schema Example:** A 43-line JSON example is used to specify the output. Large JSON blocks in prompts are token-heavy and increase the risk of the LLM anchoring to the example data (e.g., repeating "Heating Element Controller" terminology).
3. **Verbose File Conventions:** The explanation of `{parent_path}` and `{FolderName}` uses markdown tables and multiple examples, which can be expressed much more concisely.
4. **Redundancy:** Rules for IDs (`ARCH-L{level}-{NNN}`), file paths, and persistence mechanisms overlap conceptually and can be consolidated into a single compact section.

## 3. Actionable Optimization Proposals

### Proposal A: Compress A2A Handoff Definitions
Replace the verbose JSON envelope examples with a compact TypeScript-style interface or a minimal schema summary. The agent only needs to know what fields it receives and outputs, not the raw JSON boilerplate of the framework.

**Before (~40 lines):**
```json
{
  "protocol_version": "1.0.0",
  "handoff_id": "...",
  // ... large payload example ...
}
```

**After (~10 lines):**
```typescript
## A2A Handoff (Input & Output)
You process A2A Envelopes (`schemas/se-decomposition.schema.json`).
**Input Payload Schema:**
`{ feature_id, stakeholder_requirement, l1_system: {blackbox, whitebox}, sub_components, internal_interfaces, architectural_rationale, arch_triggers: [{req_id, arch_trigger}] }`
*Supersession:* If `supersession.supersedes` is set, integrate the history and address `supersession.reason`.
**Output Payload Schema:**
Identical to Input, but append `decomposition_completeness: string`. Target agent: `se-critic`.
```

### Proposal B: Abstract the JSON Output Schema
Use a compact type definition instead of a fully hydrated JSON example. This forces the LLM to understand the *schema rules* rather than anchoring to the *example content*, drastically cutting tokens.

**Before (~43 lines):** Fully populated JSON object with heating element examples.

**After (~12 lines):**
```typescript
## JSON Output Payload Schema
Return ONLY a JSON object matching this structure (no markdown fences):
{
  "parent_req_id": "REQ-...",
  "sub_components": [{
    "id": "ARCH-L{level}-{NNN}", "name": "...", 
    "domain": "software"|"hardware"|"mechanics"|"system",
    "black_box_requirement": "...", "assigned_external_interfaces": ["..."] // optional
  }],
  "internal_interfaces": [{ "source_id": "...", "target_id": "...", "interface_type": "...", "data_payload": "..." }],
  "architectural_rationale": "Justify choices. Explicitly address EVERY arch_trigger.",
  "decomposition_completeness": "Terminal note or completeness summary."
}
```

### Proposal C: Consolidate Output Path & Persistence
Combine the ID rules, output paths, and atomic write procedures into a single, dense `Persistence & Lifecycle` section.

**Streamlined Version:**
```markdown
## Persistence & Conventions
- **IDs:** `ARCH-L{level}-{NNN}` (e.g., ARCH-L1-001).
- **Derived REQs:** `REQ-L{level+1}-{NNN}`.
- **File Path:** `{SE_BASE_DIR}/{parent_path}/L{level}/{SystemName}[System|Component]/L{level}_{SystemName}[System|Component]_Architecture.iter-{N}.md`
  *(e.g., `SE/L1/Gesamtsystem/L2/AuthSystem/L2_AuthSystem_Architecture.iter-1.md`)*
- **Atomic Write:** 1. Write target file `.iter-{N}.md`. 2. On Critic approval, copy to `.final.md`. 3. Update `.se-state.yaml` (`last_completed_step`).
```

## 4. Expected Impact
- **Token Reduction:** ~40-50% reduction in system prompt size (saving approx. 300-500 tokens per invocation).
- **Latency:** Faster generation as the LLM has a shorter context window to process before output generation.
- **Robustness:** Eliminates the risk of the LLM hallucinating example data ("Heating Controller") into unrelated architecture tasks.
- **Alignment:** Adheres perfectly to `prompt-engineer.md` rules for *Structured Prompting* and *Context Engineering 2026*.

## 5. Next Steps
1. Apply the streamlined sections to `agents/1-generic/se-architect.md`.
2. Bump the template version from `1.8.0` to `1.9.0` (Minor version bump as scope is identical but text is significantly improved).
3. Test the agent with a sample decomposition task to verify adherence to the new schema formatting.
