---
description: Report a bug, feature request, or improvement for this project as a standardized GitHub issue
allowed-tools: ["Agent"]
argument-hint: "[bug | feat | improvement | docs | security | question] [short description]"
---

Delegate to the `feedback` agent with this task:

Create a GitHub issue for this project. $ARGUMENTS

**Argument interpretation:**
- No arguments → agent asks for type and description interactively
- Type keyword provided (`bug`, `feat`, `improvement`, `docs`, `security`) → pre-select that type
- Description provided → use as title basis, still ask for missing details
- Both provided (e.g. `bug login fails on mobile`) → type + title basis, collect remaining details

The feedback agent standardizes the issue format, confirms with the user, and files it via `gh issue create`.
