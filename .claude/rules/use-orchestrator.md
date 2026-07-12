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
## Git Delegation — Hard Rule

All mutating git commands must run through the `git` agent.

Forbidden in main chat: `git commit`, `git push`, `git pull`, `git add`, `git rm`, `git mv`, `git branch`, `git merge`, `git rebase`, `git reset`, `git restore`, `git checkout`, `git tag`, `git stash`.

Allowed read-only: `git status`, `git log`, `git diff`, `git branch --show-current`, `git branch -l`, `git remote -v`, `git show`.

All other git operations → `git` agent.

## Anti-Recursion Guard

Workers must not re-delegate to `orchestrator`. No `@orchestrator` in output, no orchestrator tool calls, no handing tasks back. Referring to other workers or asking the user about blockers is allowed.
