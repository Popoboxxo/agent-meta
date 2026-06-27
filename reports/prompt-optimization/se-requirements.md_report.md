# Prompt Optimization Report: `se-requirements.md`

## 1. Executive Summary
As the `prompt-engineer`, I have evaluated the `se-requirements.md` template against the `agent-meta` framework rules and modern context engineering best practices (OpenAI/Lakera/Context Engineering 2026). 
The current prompt is structurally sound, utilizing Markdown well and adhering strictly to `agent-meta` conventions (e.g., Anti-Recursion Guard). However, it contains verbose prose, redundant file path explanations, and oversized examples that consume unnecessary input tokens. 
By streamlining the prompt, we can achieve an estimated **20-30% token reduction**, improving latency (Time-to-First-Token) and lowering inference costs, without losing any functional depth or ISO/IEC 15288 compliance.

## 2. Current State Analysis
- **Token Efficiency**: The prompt spans 251 lines (~11.8 KB). While clear, it leans heavily on conversational phrasing instead of structured prompting.
- **Strengths**: 
  - Clear multi-phase workflow.
  - Strict adherence to the Architecture Boundary (role separation).
  - Proper integration of framework variables (e.g., `{{#if DOD_SE_STRICT}}`).
- **Weaknesses**:
  - **Redundancy**: "Output File Convention" and "Step Persistence" sections explain the identical file path and directory structure twice.
  - **Verbosity**: The JSON Schema example provides two full requirement objects (40+ lines), which is unnecessary.
  - **Prose**: Sections like "Architecture Boundary" and "Domain Assignment" use long sentences where compact lists/enums would suffice.

## 3. Actionable Optimization Proposals (Verschlankung)

### Proposal 1: Consolidate Output & Persistence Rules
**Current Issue**: The exact same path schema `{SE_BASE_DIR}/{parent_path}/L{level}/{FolderName}/...` is explained in two different sections.
**Action**: Merge "Output File Convention" and "Step Persistence" into a single, highly structured `## Output & Persistence` section.
**Impact**: Removes ~150 words of redundant explanations.

### Proposal 2: Compress the JSON Schema Example
**Current Issue**: The JSON example array contains two items (`REQ-L1-001` and `REQ-L1-005`).
**Action**: Condense this into a **single** comprehensive JSON object that demonstrates all fields at once, including the edge cases (`arch_impact: true`, `arch_trigger`, and `external_interfaces`).
**Impact**: Saves ~20 lines of JSON tokens. 

### Proposal 3: Implement Chain-of-Symbol (CoS) & Telegraphic Style
**Current Issue**: "You MAY" and "You MUST NOT" sections use full sentences. Workflow rules are conversational.
**Action**: Use imperative, telegraphic style and Chain-of-Symbol techniques.
*Example Refactoring:*
Instead of: `"The system shall decouple order acceptance from order processing so acceptance latency is independent of processing duration."` -> `"The system shall decouple acceptance from processing" + arch_impact: true`
Use strict allowed/forbidden lists:
- `[+] Formulate measurable black-box requirements`
- `[-] Choose architecture patterns (Microservice, etc.)`

### Proposal 4: Inline Enums for Classifications
**Current Issue**: "Domain Assignment" and "External Interface Capture" use block lists with prose descriptions.
**Action**: Compress into inline structures. LLMs parse these just as efficiently.
*Example Refactoring:*
`Domains: [system (cross-cutting), software (logic/algorithms), hardware (electronics), mechanics (structure)]`
`Interfaces -> direction: [input, output], type: [physical, data, energy, control, user]`

### Proposal 5: Streamline the 3-Phase Workflow
**Current Issue**: The phases are described with redundant transition statements ("Strict 3-phase process; user is iteratively involved before the cascade starts").
**Action**: Reduce to strict imperative commands:
1. **Elicitation:** Iterative dialogue. Clarify constraints. No JSON generation yet.
2. **Approval:** Present bulleted L1-SH list. Explicitly ask: *"Proceed to formalization?"*. Block until confirmed.
3. **Formalization:** Formulate black-box rules, assign REQ-IDs/domains. Output final JSON.

## 4. Draft Snippet: Consolidated Output & Persistence
```markdown
## Output & Persistence
**1. Atomic Write:** Write output atomically via temp file rename to:
`{SE_BASE_DIR}/{parent_path}/L{level}/{FolderName}/L{level}_{FolderName}_Requirements.md`
*(Note: FolderName = SystemName + `System`|`Component` postfix. Variables from A2A-Envelope-Payload).*

**2. Frontmatter:** Must include:
---
step: requirements
agent: se-requirements
iteration: 1
status: done
timestamp: "<ISO 8601>"
schema_version: "1.0.0"
---

**3. State Update:** Update `{SE_BASE_DIR}/.se-state.yaml` setting `last_completed_step` to this file.
```

## 5. Conclusion
Applying these structural changes will drastically increase the prompt's token density. By relying on structural prompting, inline enums, and eliminating repetition, the `se-requirements` agent will become faster and cheaper to execute while maintaining its high precision in the Systems Engineering cascade.
