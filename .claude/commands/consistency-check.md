---
description: Validate agent templates, commands and cross-references for consistency (version bumps, anchors, placeholders, cross-refs)
allowed-tools: ["Bash"]
argument-hint: "[--changed | --all | --file <path> | --strict]"
---

Run the agent-meta consistency check. $ARGUMENTS

**Argument interpretation:**
- No arguments → check only git-changed files (fast, recommended before commit)
- `--all` → check all agents and commands in the repository (full audit)
- `--file <path>` → check a single specific file
- `--strict` → treat warnings as errors (exit 1 on any finding)
- `--json` → machine-readable JSON output

**Step 1 — Locate the script**

Detect whether running inside a project (agent-meta as submodule) or inside the meta-repo itself:

```bash
# Inside a project:
test -f .agent-meta/scripts/consistency-check.py && echo "project"
# Inside agent-meta itself:
test -f scripts/consistency-check.py && echo "meta"
```

**Step 2 — Run the check**

```bash
# Default: changed files only
py .agent-meta/scripts/consistency-check.py --changed

# Or inside agent-meta meta-repo:
py scripts/consistency-check.py --changed
```

Apply flags from $ARGUMENTS:
- `--all` → omit `--changed` flag (runs full check)
- `--file <path>` → add `--file <path>`
- `--strict` → add `--strict`
- `--json` → add `--json`

**Step 3 — Interpret and report**

If exit code is 0:
> "Consistency check passed — no issues found."

If findings exist, show the output and for each ERROR:
1. Explain what the check means in plain language
2. State the concrete fix required
3. Ask: "Should I fix this now? (yes/no)"

If user says yes → apply the fix, then re-run the check to confirm.

**Common fixes by check type:**

| Check | Fix |
|---|---|
| `frontmatter.version-bump` | Increment the `version:` field in the agent frontmatter |
| `frontmatter.patch-anchor-not-found` | Update the `anchor:` string to match the current base file |
| `frontmatter.extends-not-found` | Correct the `extends:` path |
| `crossrefs.role-not-in-role-defaults` | Add entry to `config/role-defaults.yaml` |
| `crossrefs.orchestrator-table-incomplete` | Add row to orchestrator agent table |
| `placeholders.typo` | Fix the `{{VAR}}` spelling |
| `commands.allowed-tools-not-list` | Change `allowed-tools` to a JSON array |
