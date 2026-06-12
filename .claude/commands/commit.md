---
description: Stage changes and create a conventional commit with a suggested message
allowed-tools: ["Bash"]
argument-hint: "[commit message or topic, e.g. 'fix login redirect']"
---

Create a git commit for the current changes. $ARGUMENTS

**Step 1 — Check branch**

```bash
git branch --show-current
```

If on `main` or `master`:
> "⚠️ You are on `main`. Direct commits to main are not recommended.
> Create a feature branch first with: `git checkout -b feat/<topic>`
> Continue anyway? (yes/no)"
If no: stop.

**Step 2 — Show what will be committed**

```bash
git status --short
git diff --stat HEAD
```

If nothing to commit:
> "Nothing to commit — working tree is clean."
Stop.

**Step 3 — Stage changes**

If $ARGUMENTS is empty and no staged files exist:
> "Which files should be committed? Options:
> - `all` — stage everything (`git add -A`)
> - List specific files or patterns
>
> What would you like to stage?"
Wait for input.

If $ARGUMENTS is provided or user responds: stage accordingly.

Show staged diff summary after staging:
```bash
git diff --cached --stat
```

**Step 4 — Suggest commit message**

If $ARGUMENTS provides a message or topic, use it as the basis.
Otherwise analyze the staged diff to infer the change type and scope.

Suggest a message following Conventional Commits format:
```
<type>: <description>
```
Types: `feat` | `fix` | `refactor` | `docs` | `chore` | `test` | `ci`

Show the suggestion:
> "Suggested commit message:
> `<type>: <description>`
>
> Accept, edit, or type your own message?"

Wait for confirmation or correction.

**Step 5 — Commit**

```bash
git commit -m "<confirmed message>"
```

Report: commit hash + message.
Suggest next step:
> "Committed. Run `/merge` to create a PR, or keep working."
