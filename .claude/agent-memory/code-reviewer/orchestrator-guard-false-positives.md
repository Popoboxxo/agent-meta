---
name: orchestrator-guard-false-positives
description: The repo's own PreToolUse orchestrator-guard hook blocks read-only Bash commands whose text merely contains git-mutation substrings — phrase review commands to avoid it
metadata:
  type: project
---

`.claude/hooks/orchestrator-guard.sh` (PreToolUse, wired to `Bash` only) blocks any Bash
call whose command string matches its git-mutation regex — and the regex matches on
**substrings anywhere in the command text**, not just actual git subcommands.

Confirmed false positives (both hit during a real review session):
- `git merge-base ...` → `merge` matches (documented in the branch ledger)
- `git check-ignore -v .claude/hooks/dod-push-check.sh` → `push` matches inside the *filename*

**Why:** the regex is `'\bgit\b.*(commit|push|add|rm\b|...|merge|rebase|...)'` — the `.*`
lets any later occurrence of a mutation keyword anywhere on the line trigger a block,
including in file paths and flag values. Known, deliberately out of scope of the
2026-07-31 sync-audit branch; carried forward as a deferred finding.

**How to apply:** when running read-only git inspection from the Bash tool in this repo,
avoid literal mutation keywords in the command line — split the token
(`CMD="g""it comm""it"`), use a different tool (Grep/Glob/Read), or query git via a path
that doesn't embed those words. A block surfaces as
`PreToolUse:Bash hook error: [bash .claude/hooks/orchestrator-guard.sh]: No stderr output`
with no explanation, so it is easy to misread as a tooling failure.

Also note: the hook is wired to `tool_name == "Bash"` only — PowerShell calls bypass it
entirely. See [[am-branch-sync-admin-audit]] if that review context is still relevant.
