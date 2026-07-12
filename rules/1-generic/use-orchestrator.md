{{#if ORCH_MODE_STRICT}}
# CRITICAL GATE — VERIFY BEFORE EVERY ACTION

YOU ARE THE MAIN CHAT. Do not perform code changes directly.
- No `edit`, `write`, or mutating `bash` calls
- No `task` calls — delegate only to `orchestrator`
- Read-only bash allowed: `git status`, `git log`, `git diff`, `git branch --show-current`, `git branch -l`
- All git mutations → `git` agent
- Every dev task → `orchestrator` first

Violation: PreToolUse hook blocks these changes.

# Orchestrator — Universal Router

**STRICT MODE — no exceptions.** Every dev task goes through `orchestrator`. No user override, no direct dispatch.

Auto-handoff: the main chat always delegates to `orchestrator` via a native tool call — no `@orchestrator` mention in output.
{{/if}}
{{#if ORCH_MODE_ADVISORY}}
# Orchestrator — Universal Router

Every dev task goes through `orchestrator`.

Decision order:
1. **User override** — user says "do it here", "no orchestrator", etc. → stay in main chat.
{{#if DIRECT_DISPATCH_ENABLED}}
2. **Direct dispatch** — exactly one tool call, no agents/rules/hooks/scripts/config files involved, no follow-up depends on result → target agent directly.
{{/if}}
3. **Orchestrator** — everything else.

Rule of thumb: more than one step, more than one agent, or files in critical paths → orchestrator.
{{#if DIRECT_DISPATCH_ENABLED}}
{{DIRECT_DISPATCH_SECTION}}
{{/if}}

Auto-handoff: delegate to `orchestrator` via native tool call. `@orchestrator` is the only mention the user may use directly.
{{/if}}
{{#unless ORCH_MODE_DISABLED}}
## Git Delegation — Hard Rule

All mutating git commands must run through the `git` agent.

Forbidden in main chat: `git commit`, `git push`, `git pull`, `git add`, `git rm`, `git mv`, `git branch`, `git merge`, `git rebase`, `git reset`, `git restore`, `git checkout`, `git tag`, `git stash`.

Allowed read-only: `git status`, `git log`, `git diff`, `git branch --show-current`, `git branch -l`, `git remote -v`, `git show`.

All other git operations → `git` agent.

## Anti-Recursion Guard

Workers must not re-delegate to `orchestrator`. No `@orchestrator` in output, no orchestrator tool calls, no handing tasks back. Referring to other workers or asking the user about blockers is allowed.
{{/unless}}
{{#if ORCH_MODE_DISABLED}}
# Main-Chat Mode

Orchestrator is disabled. All tasks run in the main chat. Subagent delegation is optional.
{{/if}}
