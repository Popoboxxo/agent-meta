---
description: Update managed blocks in project extension files after an agent-meta upgrade
allowed-tools: ["Bash", "Read"]
argument-hint: "[role-name to update a single extension, or empty for all]"
---

Update the managed blocks in project extension files. $ARGUMENTS

**Step 0 — Check context**

Check if any extension files exist:
```bash
ls .claude/3-project/*-ext.md 2>/dev/null || echo "none"
```

If none found:
> "No extension files found in `.claude/3-project/`. Nothing to update.
> Use `/add-project-role` to create your first project-specific agent extension."
Stop.

**Step 1 — Targeted or full update**

If $ARGUMENTS provides a role name:
- Update only that extension: `python .agent-meta/scripts/sync.py --update-ext`
  (sync.py --update-ext updates all extensions; note which role the user asked about)
- After update, show only the diff for that file.

If $ARGUMENTS is empty:
- Update all extensions: `python .agent-meta/scripts/sync.py --update-ext`

**Step 2 — Report changes**

After the sync, run:
```bash
git diff .claude/3-project/
```

For each changed extension file, show:
- File name
- What changed in the managed block (added/removed sections from the base agent)
- Confirm that the user's custom content (outside the managed block) was preserved

If no changes:
> "All extension managed blocks are already up to date."

If changes found:
> "The following extensions were updated with new content from the base agents:"
> [list files with summary of changes]
> "Your custom content in each file was preserved. Review the changes and commit when ready."

**Step 3 — Suggest next step**

If changes were made:
> "Run `/diagnose` to verify the overall setup is healthy after the update."
