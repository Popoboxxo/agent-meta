---
type: "Concept"
title: "Circuit-Breaker, DoD-as-Gate, and Judge/Validator Pattern"
description: "Status: Concept (planned) Date: 2026-07-12 Source: Best Practice Audit 2026-07"
tags: [concept, status:active]
timestamp: "2026-07-27"
resource: "../../sources/docs/concepts/active/circuit-breaker-dod-gate-judge-pattern.md"
migrated_from: "docs/concepts/active/circuit-breaker-dod-gate-judge-pattern.md"
---
# Circuit-Breaker, DoD-as-Gate, and Judge/Validator Pattern

**Status:** Concept (planned)  
**Date:** 2026-07-12  
**Source:** Best Practice Audit 2026-07

---

## 1. Circuit-Breaker / Token-Budget-Guard

### Purpose

Prevent cascading failures when a downstream agent repeatedly fails. Circuit-breaker automatically stops delegating to a failing agent, preventing wasted tokens and repeated error states. Token-budget-guard extends this by pausing parallel spawning when token budget is critically low.

### Pattern Description

**Circuit-Breaker:**
- Track consecutive failures per agent (threshold: 3)
- After N consecutive failures from the same target agent, the orchestrator **opens a circuit**: stops delegating to that agent
- Circuit remains open for the remainder of the session
- Fallback: surface partial result to user and ask how to proceed
- Reset only on explicit user instruction

**Token-Budget-Guard Variant:**
- Monitor remaining token budget in real-time
- When budget drops below critical threshold (e.g., 20%), pause parallel spawning
- Consolidate pending tasks, surface current state to user
- Force serial, high-priority-only mode for remainder of session

### Current State in agent-meta

- **Partial implementation:** `retry_count` / `max_retries` in envelope specs — 3 retries per task
- **Failure Recovery table:** orchestrator documents individual failure handling
- **GAP:** No persistent circuit-breaker tracking across multiple delegations
- **GAP:** Token-budget guard not implemented as automatic pause mechanism
- **GAP:** No session-level failure pattern detection

### Design Sketch

```
In-context State Tracking:
| agent_id      | consecutive_failures | circuit_state | opened_at |
|---|---|---|---|
| junior-dev    | 3                    | open          | 12:34:00  |
| code-reviewer | 0                    | closed        | -         |

Orchestrator Logic:
1. After each delegation result:
   - If error: increment consecutive_failures[agent]
   - If success: reset consecutive_failures[agent] to 0
   
2. Before next delegation to agent:
   - If consecutive_failures[agent] >= 3:
     - Set circuit_state[agent] = open
     - Log "Circuit open for <agent> — skipping delegations this session"
     - Return partial result + "Please advise how to proceed"
   
3. Reset:
   - Only on explicit user instruction: "reopen circuit for <agent>"
   - Clear consecutive_failures and circuit_state
```

**Benefits:**
- Prevents token waste on repeatedly failing agents
- Signals to user that a specific agent is unavailable
- Allows graceful degradation (use alternative agents)
- Reduces error cascades that propagate up the call stack

---

## 2. DoD-as-Gate (Definition of Done as Blocking Gate)

### Purpose

Enforce Definition of Done as a **blocking gate** before commit/push, not as an optional checklist. DoD criteria become non-functional requirements — code cannot advance without satisfying them.

### Current State in agent-meta

**Existing Artifacts:**
- `hooks/1-generic/orchestrator-guard.sh` — EXISTS, enforces no direct writes from main_chat
- `rules/dod-criteria.md` — EXISTS, defines active DoD checklist (text-only)
- `orchestrator.md` → "## Don'ts" section states "KEIN Abschluss ohne DoD-Check" (text enforcement only)

**Missing:**
- `hooks/1-generic/dod-pre-commit.sh` — **does not exist**
- PostToolUse hook for DoD validation (provider-agnostic)
- Pre-commit enforcement — no mechanism prevents commits that violate DoD

**Gaps Identified:**
- DoD checklist is advisory, not enforced
- No pre-commit gate validates DoD completion
- Agents can output "done" without mechanically verifying each criterion
- No provider-specific PostToolUse hooks exist to block incomplete work

### Concept for Stronger DoD-as-Gate

**Pre-Commit Gate (Hook-Based):**
```bash
# hooks/1-generic/dod-pre-commit.sh (planned)
# Runs before git add/commit from any agent

1. Read rules/dod-criteria.md
2. Identify active criteria (not marked as optional/disabled)
3. Prompt agent: "Verify each DoD criterion before commit:"
   - [ ] Code implements task fully
   - [ ] Conventions followed
   - [ ] Commit message Conventional Commits format
   - [ ] No regressions
4. If any unchecked → block commit with error code 1
5. Only proceed if all active criteria confirmed
```

**PostToolUse Gate (Provider-Specific):**
- Triggers after agent outputs before delegation/response
- Validates that final output includes DoD-checklist completion
- Warns if criteria are skipped or marked incomplete
- Gives agent option to revise or escalate

**Enforcement Model:**
- `dod-criteria.md` becomes the source of truth
- Orchestrator reads active criteria at session start
- Pre-commit hook enforces mechanically (Bash/shell)
- Provider-specific hooks (`.claude/hooks`, `.gemini/hooks`) adapt enforcement to native tool call syntax

**Status:** Concept stage — implementation deferred to next development cycle.

---

## 3. Judge / Validator-Agent Pattern

### Purpose

Quality gate with **isolated context** — prevents the evaluator from being biased by the generator's reasoning or self-assessment. An independent Judge agent assesses artifacts with a fresh perspective.

### Pattern Description

**Workflow:**
1. **Generator** (e.g., developer) completes task → produces artifact(s)
2. **Orchestrator** spawns **Judge/Validator** with fresh context (minimal handoff)
3. **Judge receives only:**
   - Original task specification
   - Artifact(s) produced (file reference or short summary)
   - Explicit evaluation criteria
4. **Judge does NOT receive:**
   - Generator's intermediate reasoning or conversation history
   - Generator's self-assessment or confidence scores
   - Debugging logs or exploration notes
5. **Judge outputs:**
   - Pass / Fail (binary or multi-level)
   - Specific findings (violations, missing elements, edge cases)
   - Optionally: suggested revision prompt for generator (if Fail)

### Current State in agent-meta

**Existing Elements:**
- `agents/1-generic/validator.md` — standalone validator agent exists
- Validator listed as allowed subagent for `senior-developer` (escalation path)
- Artifact Pattern: orchestrator documents output >200 lines → write to artifact file

**Gaps:**
- No standard pattern for "isolated judge spawn"
- Validator typically receives full context chain (conversation history, reasoning)
- No mechanism to strip context before delegating to judge
- Reflection loops (REPEAT_UNTIL) approximate this but share generator context

**Why Context Isolation Matters:**
- **Confirmation bias:** If judge sees generator's reasoning, judge tends to validate rather than evaluate
- **Anchoring:** Early claims by generator bias judge's interpretation
- **Groupthink:** Shared context between generator and judge reduces independent scrutiny

### Design Notes

**Isolation Mechanism:**
- Orchestrator compiles minimal task spec → pass to judge as `payload.t`
- Artifact file reference → judge reads file, not raw output string
- No `delegation_depth` or conversation history passed to judge
- Judge prompt explicitly forbids considering generator's stated reasoning

**Example Judge Spawn (pseudocode):**
```yaml
# Orchestrator decision:
generator_result:
  status: complete
  artifact: "generated-code.py"
  
# Spawn judge with isolated context:
task:
  type: judge
  subagent_type: validator
  payload:
    t: "Evaluate generated-code.py against these criteria: [list]. Return pass/fail and findings."
    # NO: generator's reasoning, conversation history, or self-assessment
  
judge_context:
  delegation_depth: 2  # Fresh counter, not inherited
  delegation_history: []  # Empty
  conversation: []  # Empty
```

**Integration with Orchestrator:**
- Artifact Pattern (output >200 lines → file) supports judge pattern naturally
- Judge reads from artifact file, not in-memory string
- Orchestrator can parallelize: run judge *while* generator works on revision
- Orchestrator uses judge verdict as gate: only advance if judge passes

**Comparison to Existing Patterns:**
- **Reflection loops (REPEAT_UNTIL):** Iterative, shared context, best for self-correction
- **Judge pattern:** Binary, isolated context, best for independent quality assurance
- **Hybrid:** Use reflection for generator, judge for final sign-off

**Reference:**
- Anthropic "Building Effective Agents" best practices emphasize specialized evaluation agents with narrow, well-defined scope
- Court systems and peer review use this principle: decision-maker (judge) is separate from advocate (generator)

### Planned Enhancements

- Standard prompt template for judges (available in snippets/)
- Orchestrator extension: `judgement_required: true` flag in task spec
- Provider-specific implementations: `.claude/3-project/validator-ext.md` etc.
- Metrics: track judge verdicts per agent type to identify systematic failures

---

## Relationship to Existing Patterns

| Pattern | Scope | Interaction |
|---|---|---|
| **Singleton Orchestrator** | Session-level routing | Circuit-breaker integrates with orchestrator state tracking |
| **Retry Mechanism** | Per-task resilience (3 retries) | Circuit-breaker activates *after* retries exhausted |
| **Failure Recovery** | Individual error handling | Circuit-breaker tracks *patterns* across errors |
| **DoD Checklist** | Developer task completion | DoD-as-Gate automates the checklist enforcement |
| **Orchestrator-Guard Hook** | Prevent direct main_chat writes | DoD-as-Gate complements with pre-commit enforcement |
| **Artifact Pattern** | Manage large outputs | Judge pattern relies on artifacts for clean handoff |
| **Validator Agent** | Quality assurance | Judge pattern formalizes isolated validator spawn |

---

## Next Steps

1. **Circuit-Breaker:** Design state-tracking format; implement in orchestrator.md logic
2. **DoD-as-Gate:** Create `hooks/1-generic/dod-pre-commit.sh`; add provider-specific PostToolUse rules
3. **Judge Pattern:** Define standard judge prompt template; add to `snippets/`; document orchestrator integration

---

**Version:** 0.1.0  
**Last Updated:** 2026-07-12  
**Author:** Best Practice Audit Task