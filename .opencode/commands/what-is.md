---
description: Explain what an agent does — its role, tools, and boundaries
allowed-tools: ["Read", "Glob", "Bash"]
argument-hint: "<agent-name, e.g. developer>"
---

Explain what the specified agent does. $ARGUMENTS

**Step 0 — Check for missing input**

If $ARGUMENTS is empty:
> "Which agent would you like to know about? Available agents:"

List all `.md` files in `.claude/agents/` (strip `.md` extension for display).

> "Please type an agent name to continue."

Stop here and wait for the user to respond.

**Step 1 — Find the agent file**

Look for `.claude/agents/<name>.md`. If not found:
- Try case-insensitive match
- If still not found:
  > "Agent '<name>' not found. Available agents: [list]"
  Stop.

**Step 2 — Summarize**

Read the agent file and produce a concise summary in this structure:

**[Agent Name]** — `<description from frontmatter>`

**Zuständigkeit:** [1-2 sentences: what does this agent own, what decisions does it make]

**Tools:** [list tools from frontmatter, with one-word explanation each if non-obvious]

**Wann einsetzen:**
- [2-3 concrete trigger examples from the agent's instructions]

**Wann NICHT einsetzen / Grenzen:**
- [1-2 explicit limitations or handoff points]

**Typischer Aufruf:**
> [one realistic example prompt that would invoke this agent]

Keep the summary to ~15 lines. No wall of text. The goal is that someone unfamiliar with this agent knows exactly when and how to use it after reading.
