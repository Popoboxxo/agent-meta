---
description: Stage changes and create a conventional commit with a suggested message
allowed-tools: ["Bash"]
argument-hint: "[commit message or topic]"
---

Create a git commit for the current changes. $ARGUMENTS

Workflow: check branch (warn on main), show status/diff, stage changes, suggest a Conventional Commit message, confirm with user, commit. Ensure the message has no leading UTF-8 BOM — the subject must start at byte 0 with the type (the guard hook rejects a BOM-prefixed commit, issue #842).

Report commit hash and message.
