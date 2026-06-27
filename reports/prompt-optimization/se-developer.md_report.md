# Prompt Optimization Report: `se-developer.md`

## 1. Executive Summary
An evaluation of the `se-developer.md` prompt was conducted following the `prompt-engineer` best practices (OpenAI, Lakera, and Context Engineering 2026). The focus was on "Verschlankung" (streamlining) and token reduction without losing functional precision or violating `agent-meta` rules. 

The current prompt is robust but contains significant narrative "fluff" and structural redundancies. By applying Structured Prompting and Context Engineering techniques, the prompt can be reduced by an estimated 30-40% in tokens, leading to lower latency and better instruction adherence ("Lost in the Middle" mitigation).

## 2. Current State Analysis
- **Redundancy in Contracts:** The prompt defines input/output in `Input (A2A Handoff)` and `Output (A2A Handoff)`, but then repeats schema requirements in `A2A Handoff — Incoming Tasks`.
- **Narrative Prose:** The `Persona` description and `SE Interface Discipline` contain explanatory prose (e.g., "You sit at the implementation floor of the SE cascade...", "This is the critical distinction..."). LLMs do not need this motivation; they need strict constraints.
- **Verbose Boilerplate:** The `Anti-Recursion Guard` and `Reflection Loop` use lengthy tables and paragraphs for standard worker instructions.

## 3. Actionable Optimization Proposals

### Proposal 1: Merge and Structure A2A Contracts
Combine all A2A handoff definitions into a single, highly structured markdown block. Drop the narrative explanations of schemas.

**Optimized Structure:**
```markdown
## A2A Contract
**Input (`task-spec-v1` / `a2a-handoff.schema.json`):**
- Extracts: `leaf_id`, `req_id`, `domain` (software|hardware|mechanics), `description`, `interface_specs`, `propagation_map`, `acceptance_criteria`, `context_boundary`.

**Output (`dev-result-v1`):**
- Returns: `leaf_id`, `req_id`, `artifacts`, `interfaces_implemented`, `test_coverage`, `status` (done|partial|escalate), `escalation` (optional).
```

### Proposal 2: Convert Narrative to Strict Constraints (SE Discipline)
Remove the "why" and focus purely on the "what" and "how". LLMs parse bullet points much faster than paragraphs.

**Optimized Structure:**
```markdown
## SE Interface Discipline
- **Strict Boundary:** Code EXCLUSIVELY against `description` + `acceptance_criteria` in your `context_boundary`.
- **Orthogonality:** NO direct communication with sibling nodes. All communication routes via parent contracts.
- **Interfaces:** Implement ONLY the `propagation_map` rows (`inherited_external`, `new_internal_incoming`, `new_internal_outgoing`).
- **Contract Fidelity:** Unilateral changes FORBIDDEN. Escalate immediately if `interface_specs` are insufficient.
- **Domain Gate:** If `domain` is hardware/mechanics → output stub/COTS spec only, return `status: done`.
```

### Proposal 3: Streamline the Reflection & Escalation Loops
Use highly compressed logic for operational loops.

**Optimized Structure:**
```markdown
## Escalation & Reflection
**Escalate (`status: escalate`) IF:**
- `propagation_map` > 4 interfaces.
- Cross-cutting concerns surface (auth, crypto, secrets).
- Contradictory specs, unsolvable requirements, or required interface changes.
*Output:* `ESCALATE | leaf_id | req_id | reason | recommended_tier (e.g., se-senior-developer) | findings | partial_work`

**Revision Mode (from `se-critic`):**
- Fix ONLY flagged findings. Ignore non-flagged code. Confirm fixes.
- If iteration max reached: prioritize criticals or escalate as "blocked".
```

### Proposal 4: Compress Standard Boilerplate
Reduce the Anti-Recursion guard and Step Persistence to their bare minimum.

**Optimized Structure:**
```markdown
## Anti-Recursion
**WORKER AGENT:** NEVER delegate tasks back to orchestrator or other workers. You are the endpoint. Escalation (`status: escalate`) is the only exception. No `@orchestrator`.

## Persistence
Write atomic output to: `{SE_BASE_DIR}/{parent_path}/L{level}/{FolderName}/implementation/L{level}_{FolderName}_Impl.md`
Use frontmatter: `step: implementation`, `agent: se-developer`, `status`, `timestamp`, `schema_version: "1.0.0"`. Update `.se-state.yaml` (`last_completed_step`).
```

## 4. Conclusion
By applying these reductions, the prompt focuses purely on execution logic. The removal of ~30% tokens will directly improve generation speed and enforce the SE contract discipline more strictly, as the LLM's attention is not diluted by explanatory prose.
