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
3. **Orchestrator** — everything else.

Rule of thumb: more than one step, more than one agent, or files in critical paths → orchestrator.
## Direkter Dispatch (nur nach Regel 2)

| Operation | Direkt an | Bedingung |
|-----------|-----------|-----------|
| Commit, Push, Branch, Tag, PR | `git` | Einzelner Git-Befehl |
| Sync, Upgrade, Meta-Konfiguration | `agent-meta-manager` | Reine agent-meta-Operation |
| Bug/Feature/Verbesserung melden | `feedback` | Issue-Erstellung |
| Session-Erkenntnisse speichern | `documenter` | Nur bei Session-Ende |

> **Faustregel:** >1 Tool-Call → Orchestrator. Unsicher → Orchestrator.

Auto-handoff: delegate to `orchestrator` via native tool call. `@orchestrator` is the only mention the user may use directly.

## Git Delegation — Hard Rule

All mutating git commands must run through the `git` agent.

Forbidden in main chat: `git commit`, `git push`, `git pull`, `git add`, `git rm`, `git mv`, `git branch`, `git merge`, `git rebase`, `git reset`, `git restore`, `git checkout`, `git tag`, `git stash`.

Allowed read-only: `git status`, `git log`, `git diff`, `git branch --show-current`, `git branch -l`, `git remote -v`, `git show`.

All other git operations → `git` agent.

## Anti-Recursion Guard

Workers must not re-delegate to `orchestrator`. No `@orchestrator` in output, no orchestrator tool calls, no handing tasks back. Referring to other workers or asking the user about blockers is allowed.
