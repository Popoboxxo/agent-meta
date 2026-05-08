---
description: Create a PR for the current branch and merge it into main
allowed-tools: ["Bash"]
argument-hint: "[PR title or empty to auto-generate]"
---

Create a pull request for the current branch and merge it. $ARGUMENTS

**Step 1 — Check branch**

```bash
git branch --show-current
```

If on `main` or `master`:
> "⚠️ Already on `main` — nothing to merge. Switch to a feature branch first."
Stop.

**Step 2 — Check for uncommitted changes**

```bash
git status --short
```

If uncommitted changes exist:
> "There are uncommitted changes. Commit them first with `/commit`, or stash them.
> Continue anyway (without uncommitted changes)? (yes/no)"
If no: stop.

**Step 3 — Push branch**

```bash
git push -u origin HEAD 2>&1
```

If push fails (hook or other error): report the error and stop.

**Step 4 — Check for existing PR**

```bash
gh pr view --json number,title,state 2>/dev/null
```

If PR already exists and is open: skip to Step 6.

**Step 5 — Compose PR**

Gather context:
```bash
git log main..HEAD --oneline
git diff main...HEAD --stat
```

If $ARGUMENTS provides a title, use it. Otherwise derive the title from the commits (first commit message or common theme).

Compose:
- **Title**: max 70 chars, imperative mood
- **Body**: bullet summary of changes + test plan checklist

Show draft to user:
> "PR draft:
> Title: `<title>`
> Body: [summary]
>
> Create PR? (yes/edit/no)"

Wait for confirmation. If "edit": ask what to change.

**Step 6 — Create & merge PR**

```bash
gh pr create --title "<title>" --body "<body>"
gh pr merge --squash --delete-branch
```

Report: PR URL + merge confirmation.

> "✅ Merged. Branch deleted. Run `git checkout main && git pull` to update your local main."
