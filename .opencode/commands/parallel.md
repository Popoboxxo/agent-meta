---
description: Launch multiple agents in parallel and collect their results
allowed-tools: ["Agent", "TodoWrite"]
argument-hint: "<agent>:\"<task>\" + <agent>:\"<task>\" [+ ...]"
---

Launch multiple agents in parallel and collect their results when all are done.

**Input:** $ARGUMENTS

---

## Parsing

Parse $ARGUMENTS as `+`-separated `agent:"task"` pairs. Examples:

```
developer:"Fix login bug" + documenter:"Update README"
security-auditor:"Audit auth module" + tester:"Run full test suite"
reviewer:"Review PR #42" + validator:"DoD check for feature-x"
```

## Execution

1. Parse all `agent:"task"` pairs from $ARGUMENTS
2. Validate each agent name — skip unknown agents with a warning
3. Launch all valid agents in parallel using the Agent tool (multiple calls in one message)
4. Respect `max-parallel-agents` limit — if more tasks than limit, batch sequentially
5. Collect all results as they complete

## Result summary

After all agents finish, present a unified summary:

```
## Parallel Execution Results

✅ developer — <one-line summary>
✅ documenter — <one-line summary>
❌ tester — <error or failure reason>
```

If any agent produced findings that require follow-up (e.g. reviewer found MUST-FIX issues),
mention them clearly and suggest next steps.

## Argument interpretation

- No `+` separator → treat as single agent:task delegation
- Unknown agent name → skip with warning, continue with others
- Missing quotes around task → treat rest of string as task
- `--dry-run` suffix → list what would run, don't execute
