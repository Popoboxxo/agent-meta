---
description: Change the DoD preset or speech mode of this project
allowed-tools: ["Read", "Edit", "Bash"]
argument-hint: "<preset: rapid-prototyping | standard | strict> or <speech: off | professional | submissive>"
---

Change the project preset or speech mode. $ARGUMENTS

**Step 0 — Check for missing input**

If $ARGUMENTS is empty:
> "What would you like to change? Options:"
>
> **DoD Preset** (Definition of Done strictness):
> - `rapid-prototyping` — no tests, no docs, no security audit required
> - `standard` — tests required, docs recommended
> - `strict` — tests + docs + security audit required, full REQ-traceability
>
> **Speech mode** (how agents communicate):
> - `off` — neutral, professional tone
> - `professional` — structured, formal
> - `submissive` — deferential style ("Wie Ihr wünscht", "Meister")
>
> "Please type what you want to change, e.g.: `standard` or `speech: off`"

Stop here and wait for input. Do not proceed until the user specifies what to change.

**Step 1 — Parse the input**

Determine from $ARGUMENTS (or the user's follow-up):
- Is it a DoD preset? → look for `rapid-prototyping`, `standard`, `strict`
- Is it a speech mode? → look for `off`, `professional`, `submissive` (with or without `speech:` prefix)
- Unknown value:
  > "Unknown option '<value>'. Valid DoD presets: rapid-prototyping, standard, strict.
  > Valid speech modes: off, professional, submissive."
  Stop.

**Step 2 — Show current value and confirm**

Read `.meta-config/project.yaml` and show the current value of the field being changed.

> "Current: `<field>: <current-value>`
> New: `<field>: <new-value>`
> Proceed? (yes/no)"

If no: stop.

**Step 3 — Apply**

Update the relevant field in `.meta-config/project.yaml`:
- DoD preset → `dod-preset: <value>`
- Speech mode → `speech-mode: <value>`

Run: `python .agent-meta/scripts/sync.py`

**Step 4 — Confirm**

> "Done. `<field>` is now `<new-value>`.
> The change takes effect immediately in all generated agent files."

For DoD preset changes, briefly explain what is now required/relaxed:
e.g. "Tests are now required before closing a task."

For speech mode changes:
e.g. "Agents will now respond in neutral professional tone."
