# Prompt Evaluation & Optimization Report: `se-critic.md`

**Agent:** `prompt-engineer`
**Target:** `/agents/1-generic/se-critic.md`
**Goal:** Streamlining and token reduction without losing functionality or violating agent-meta rules.

## 1. Current State & Findings

The `se-critic.md` prompt is well-structured and adheres to the AutoGen Reflection Pattern, acting as a strict quality gate. However, it spans over 300 lines and consumes a significant amount of tokens due to verbose descriptions, repetitive JSON payload examples, and overlapping sections. 

**Key Findings:**
1. **JSON Bloat:** The A2A envelope examples (Input, Approval Output, Rejection Output) repeat the full schema (e.g., `protocol_version`, `schema_ref`, `trace_parent`) multiple times. This is token-heavy.
2. **Redundant Sections:** The "Decision Logic" and "Correction Loop" sections describe the identical workflow and can be merged.
3. **Verbose Audit Criteria:** The criteria lists use full sentences where concise key-phrases would suffice.
4. **Step Persistence:** The atomic write procedure is overly narrative.
5. **High-Attention Zones:** The prompt ends with the Anti-Recursion Guard, which is good, but the core output schema is buried in the middle.

## 2. Optimization Proposals (Actionable Insights)

### 2.1. Compress Data Contracts (A2A Envelopes & Output Schema)
**Action:** Replace full JSON structures with minimal representations. For A2A envelopes, define the base structure once and only show the *deltas* (changes in `payload` and `supersession`) for Approval vs. Rejection. For the review output, avoid listing every single check in the JSON example.
*Benefit:* Massive token savings and faster LLM parsing (Latency Reduction).

*Example Optimization:*
```markdown
### A2A Handoff — Output
Generate a standard A2A-Envelope. Update only these fields based on the verdict:

**Approval (`passed: true`):**
- `target_agent`: "se-interface-mgr"
- `payload`: { "verdict": "approved", "review_target": "...", "checks": {...}, "approved_output": {...} }

**Rejection (`passed: false`):**
- `target_agent`: "se-architect" (or "se-requirements")
- `payload`: { "verdict": "rejected", "review_target": "...", "checks": {...}, "issues": [...] }
- `supersession`: { "supersedes": "<rejected_handoff>", "history": [...], "reason": "...", "timestamp": "..." }
```

### 2.2. Consolidate Flow Logic
**Action:** Merge "Decision Logic" and "Correction Loop" into a single, highly compressed mapping.
*Benefit:* Removes redundancy, speeds up instruction processing (Chain-of-Symbol / Reasoning Effort Tuning).

*Example Optimization:*
```markdown
## Decision & Loop Logic (Max Iterations: {{MAX_ITERATIONS}})
- `approved`: All checks pass → Handoff to `se-interface-mgr`.
- `rejected`: Fixable issues → Return `correction_hints` to generator (`se-requirements` or `se-architect`).
- `blocked`: Critical flaw (safety, physics, parent violation) → Escalate to parent cell. No local correction.
- `max_iterations` reached: Escalate with latest hints.
```

### 2.3. Streamline Audit Criteria (Structured Prompting)
**Action:** Convert the detailed bullet points in "Requirements Review Checks" and "Architecture Review Checks" into ultra-compact keywords or short questions.
*Benefit:* Faster parsing, lower context footprint.

*Example Optimization (Requirements Completeness):*
- *Current:* "All stakeholder needs captured? Missing requirements? Edge cases, safety, error-handling considered? All external interfaces enumerated per requirement?"
- *Optimized:* "Completeness: Stakeholder needs fully captured? Edge/safety/error cases covered? All external interfaces enumerated?"

### 2.4. Condense the Role Boundary Check
**Action:** The forbidden terms list is critical but takes up vertical space. Format it as inline, comma-separated lists. 
*Example:* 
`Arch Patterns:` microservice, event-bus, event-sourcing, monolith, CQRS, hexagonal, layered.
`Tech:` PostgreSQL, MySQL, MongoDB, DynamoDB, RabbitMQ, Kafka, Redis, S3, Docker, Kubernetes, nginx.

### 2.5. Tighten Step Persistence
**Action:** Reduce the atomic write procedure to a direct command sequence.
*Example:*
```markdown
**Atomic Write:**
1. Write full output to temp file: `{SE_BASE_DIR}/.../L{level}_{FolderName}_[Target].critic.iter-{N}.md`
2. Rename to final path. If `approved`, copy to `.final.md`.
3. Update `.se-state.yaml` (`last_completed_step`).
```

## 3. Conclusion
By applying these "Context Engineering" techniques, the `se-critic.md` prompt can be reduced by roughly 30-40% in token size. This will directly decrease generation latency and API costs while maintaining the strict quality gating and agent-meta framework compliance.
