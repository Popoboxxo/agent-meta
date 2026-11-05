---
description: Run the release checklist as a check-only dry run (no tag, push or commit)
allowed-tools: ["Agent"]
argument-hint: "[optional scope or reason]"
requires_roles: [release]
---

Delegate to the `release` agent with `MODE: check-only`. $ARGUMENTS

Return its `CHECKLIST` table and `CHECKLIST_SUMMARY` verbatim; do not perform the release yourself.

`MODE: check-only` means evaluate every checklist item and report pass / fail / n/a / not_run, but change nothing: no version bump, no build, no file or CHANGELOG edit, no commit, no git tag, no push, no `gh release`. `check: script` items still run and must be side-effect free.

If the release agent is not active in this project, say so and stop. The command also works when the release checklist mode is `off`: the agent knows `MODE: check-only` from this instruction only.
