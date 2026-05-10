---
description: Report a bug in this project by filing a standardized GitHub issue via the feedback agent
allowed-tools: ["Agent"]
argument-hint: "[short bug description]"
---

Delegate to the `feedback` agent with this task:

Create a bug report (type: bug) as a GitHub issue for this project. $ARGUMENTS

Pre-select issue type `bug`. If $ARGUMENTS is provided, use it as the title basis.
The feedback agent will collect remaining details and file the issue via `gh issue create`.
