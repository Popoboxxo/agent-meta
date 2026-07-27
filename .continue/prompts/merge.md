---
description: Create a PR for the current branch and merge it into main
allowed-tools: ["Bash"]
argument-hint: "[PR title or empty to auto-generate]"
invokable: true
---

Create a pull request for the current branch and merge it. $ARGUMENTS

Workflow: check current branch (abort if on main), ensure clean working tree, push HEAD, create PR if none exists, squash-merge and delete branch.

Use $ARGUMENTS as PR title if provided; otherwise derive from commits.

Report PR URL and merge confirmation.
