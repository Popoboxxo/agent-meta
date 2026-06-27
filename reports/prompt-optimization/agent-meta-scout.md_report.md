# Prompt Optimization Report: `agent-meta-scout.md`

## 1. Executive Summary
This report provides an extensive evaluation of the generic agent template `agent-meta-scout.md` based on advanced Prompt Engineering and Context Engineering (2026) best practices as defined in `prompt-engineer.md`. The primary goal is maximum token reduction (Verschlankung) and improved execution latency without compromising functionality or violating `agent-meta` framework rules.

## 2. Current State Analysis
- **File Length:** 162 lines, ~6.3 KB.
- **Format:** Verbose conversational text ("Du bist der...", "WICHTIG: Du wirst..."), large markdown tables, and repetitive boilerplate.
- **Deficiencies against Best Practices:**
  - **Missing Delimiters:** No clear XML tags separating persona, instructions, and constraints (violates OpenAI Best Practice 1).
  - **Verbosity (Lost in the Middle):** Heavy narrative descriptions that consume the "Reasoning-Buffer" and dilute attention.
  - **Table Overhead:** The target layer and scope tables use markdown table syntax which is token-heavy and harder for models to parse efficiently compared to compact key-value lists.
  - **Boilerplate Bloat:** The "Anti-Recursion Guard" occupies 13 lines for a standard framework rule, adding unnecessary generation latency.

## 3. Actionable Optimization Proposals

### A. Structured Prompting via XML Tags
*Best Practice:* Use delimiters to separate instructions.
*Action:* Wrap core sections in `<persona>`, `<init>`, `<workflow>`, `<constraints>`, and `<anti_recursion>` tags. This signals clear boundaries to the LLM and speeds up parsing.

### B. Condense Persona & Initialization
*Best Practice:* Replace narrative with key-value pairs.
*Action:* Replace the verbose introduction with strict, parseable intent blocks:
```xml
<persona>
Role: Agent-Meta Scout
Goal: Discover and evaluate Skills, Roles, Rules, and Patterns for agent-meta.
Trigger: **Explicit user request ONLY.** Never auto-started.
</persona>

<init>
MANDATORY: Read `.agent-meta/external/awesome-claude-code/.claude/commands/evaluate-repository.md` (Contains 1-10 scoring, safety, permissions).
</init>
```

### C. Convert Token-Heavy Tables to Compact Lists
*Best Practice:* Markdown tables cost unnecessary tokens (whitespace and pipes).
*Action:* Convert the "Was du suchst" and "Scope-Steuerung" tables into concise lists.
```xml
<targets>
- External Skills -> `0-external/` (use `--add-skill`)
- Roles -> `1-generic/<role>.md`
- Platform Patterns -> `2-platform/<platform>-*.md`
- Rules/Hooks/Workflows -> `howto/`
</targets>

<scope_rules>
- "Scout / What's new": Full Workflow (Phases 1-3)
- "Evaluate <URL>": Phase 2 only
- Topic/Role/Rule search: Phase 1 with specific filter
</scope_rules>
```

### D. Streamline the Core Workflow
*Best Practice:* Intent Classification and Output Shaping.
*Action:* Compress the three phases into a tight action list. Keep the report template, but reduce the instructional overhead.
```xml
<workflow>
1. Scouting: Fetch `awesome-claude-code` (README & CSV). Compare against `external-skills.config.yaml`. Draft Top 5-10 candidates.
2. Evaluation: Fetch repo details of Top 3-5. Apply evaluation framework. Check agent-meta fit (SKILL.md present? Submodule? Target Layer? Overlap?).
3. Report: Output concise markdown (Summary, Recommendations with Score/Next Steps, Rejections, New Ideas).
</workflow>
```

### E. Reduce Anti-Recursion Boilerplate
*Best Practice:* Relevance Filtering and Output Shaping.
*Action:* Compress the 13-line Anti-Recursion Guard into a strict 4-liner.
```xml
<anti_recursion>
- You are an ENDPOINT Worker. NO delegation to `orchestrator` or other workers.
- NO `@orchestrator` mentions or `Task()` calls.
- If another worker is needed, advise user in text.
</anti_recursion>
```

### F. Consolidate Limits
*Best Practice:* Principle of Least Privilege and Don'ts.
*Action:*
```xml
<constraints>
- PROPOSE ONLY. Never auto-install/execute.
- Read-only WebFetch (public content).
- If unsure: "Needs further manual review".
</constraints>
```

## 4. Expected Impact
Implementing these changes will reduce the prompt length by approximately **40-50%**.
- **Lower Token Costs:** Significant reduction in input tokens per execution.
- **Reduced Latency:** Faster Time-to-First-Token (TTFT) due to a smaller context window.
- **Higher Adherence:** Key constraints are easier for the model's attention mechanism to prioritize because extraneous "noise" and filler words are removed.
