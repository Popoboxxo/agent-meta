---
snippet: closing-summary
version: "1.0.0"
language: markdown
runtime: "agent-meta Modern Mode"
---

**Mandatory closing summary (issue #267):** the structured block above is your entire return value — the orchestrator consumes only this summary, never raw output. RESULT: compact summary (max 2-3 sentences) covering what changed, success/failure and the next step. Raw command output, diffs and logs never go into RESULT — they belong in ARTIFACTS (file paths).
