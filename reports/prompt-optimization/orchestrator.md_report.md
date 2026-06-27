# Prompt Optimization Report: Orchestrator Template
**Target:** `agents/1-generic/orchestrator.md`
**Role:** Prompt Engineer (`template-prompt-engineer`)
**Date:** 2026-06-27

## 1. Executive Summary
The Orchestrator template is the backbone of the `agent-meta` framework. With ~850 lines, it is extremely comprehensive but suffers from verbosity, scattered logic, and redundancy. By applying OpenAI and Lakera best practices—specifically structured prompting, relevance filtering, and output shaping—we can significantly reduce token consumption and latency without losing functionality.

## 2. Current State Analysis
- **Size:** 850 lines, ~35KB. High token cost per invocation.
- **Redundancy:** The core instruction "Router, not Worker" (do not execute tasks yourself) is repeated in *Kernprinzip*, *Intent-Routing*, *Unknown Intent*, and *Don'ts*.
- **Scattered Rules:** Rules around delegation, gates, validation, and failure recovery are distributed across 6+ different sections.
- **Context Bloat:** The Systems Engineering (SE) Mode takes up ~150 lines of prose. If SE is not active in every project, this adds significant conditional bloat.

## 3. Specific Optimization Proposals (Verschlankung)

### 3.1. Consolidation of Routing Logic
**Current:** We have separate sections for `Intent-Routing` (table), `Developer-Tier-Auswahl`, `Few-Shot Patterns`, and `Model Tier Routing`.
**Proposal:** Merge these into a single "Routing & Tier Matrix".
- Move the tier definition (`fast`, `balanced`, `powerful`, `max`) into a compact reference list.
- Integrate the Junior/Senior escalation logic directly into the developer row of the intent matrix, or as a small sub-table.

### 3.2. Unified Delegation Guardrails
**Current:** `Pre-Delegation Self-Validation Gate`, `Anti-Recursion & Re-Delegation Detection`, and `Human-in-the-Loop Gates` are scattered.
**Proposal:** Create a single, strict **`<delegation_checklist>`** or `<hard_gates>` section at the end of the prompt (High-Attention Zone).
*Example:*
```markdown
## Hard Gates & Validation (CHECK BEFORE DISPATCH)
1. **HitL:** Require user confirmation for: Commit on main, delete branch, release, FANOUT >2.
2. **Anti-Recursion:** `source_agent != target_agent` AND `delegation_depth <= {{A2A_MAX_DEPTH}}`.
3. **Payload Limit:** `payload.t` <= {{A2A_T_SIZE_LIMIT}} chars. NO "Du bist..." prompts.
4. **Dependency:** Check for overlapping files before parallel FANOUT.
```

### 3.3. Abstraction of Systems Engineering (SE) Mode
**Current:** Massive `se-cascade` documentation (Zig-Zag workflow, recursive cell spawns, context hygiene, V-Model integration).
**Proposal:** 
- **Best:** Extract the SE specifics into an extension file (`{{PREFIX}}-se-orchestrator-ext.md`). The orchestrator template only needs to know how to route to the `se-cascade` pipeline.
- **Alternative:** Convert the prose into a highly compressed YAML/JSON definition or bulleted constraint list. LLMs parse structured constraints faster and cheaper than continuous text.

### 3.4. Streamlining A2A Protocol and BARRIER
**Current:** Elaborate explanations of envelopes, batch modes, hitl, retry logic.
**Proposal:** Use **Structured Prompting** (Key-Value pairs) instead of narrative text.
*Example compression:*
```markdown
## A2A Envelope (Compact Mode)
- **Format:** JSON Envelope required for every dispatch.
- **Fields:** `handoff_id` (HOFF-YYYYMMDD-NNN), `schema_ref`, `trace_parent`.
- **Payload:** `t` (1 sentence task, max {{A2A_T_SIZE_LIMIT}} chars), `ctx` (context), `con` (constraints).
- **Batching:** Set `batch: true` and pass array of payloads for FANOUT.
```

### 3.5. Optimize Verbosity and Placement
- **Remove Conversational Prose:** Strip out sentences like "Du führst NICHTS selbst aus — Analyse nur zur Intent-Klassifikation". Replace with strict commands: "DO NOT execute code. ONLY route tasks."
- **High-Attention Zones:** Move the "Don'ts" and the unified "Hard Gates" to the absolute bottom of the template. The LLM focuses most on the end of the prompt.
- **Chain-of-Symbol:** In the `In-Context Delegation Tracker`, replace text statuses with symbols if possible (e.g., `[ ]` pending, `[x]` done, `[!]` failed) to save tokens in the ongoing context window.

## 4. Compliance with Framework Rules
- **Anti-Re-Delegation Gates:** Kept completely intact, just moved to a centralized Gate section.
- **Provider-Agnostic:** No provider-specific terminology was introduced.
- **Template Variables:** All `{{GROSS_MIT_UNTERSTRICH}}` Handlebars blocks remain untouched.

## 5. Next Steps / Action Items
1. Apply the consolidated Routing Matrix.
2. Extract SE Mode to an extension, or condense it into bullet points.
3. Centralize all Validation Gates at the bottom of the file.
4. Bump version to `5.2.0` (Minor update: structural optimization, reduced token footprint).
