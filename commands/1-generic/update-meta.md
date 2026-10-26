---
description: Re-sync all agents from current agent-meta templates without upgrading version
allowed-tools: ["Bash", "Read"]
argument-hint: "[--dry-run | --only-variables]"
---

# update-meta

Re-sync all agents, rules, commands, and hooks from the current agent-meta templates without upgrading the agent-meta version.

## Difference from upgrade-meta

| Command | What it does |
|---------|-------------|
| `/update-meta` | Runs `sync.py` with current version — **no version change** |
| `/upgrade-meta` | Checks out newer tag, **then** runs sync |

## Usage

```
/update-meta              # Full sync
/update-meta --dry-run    # Preview what would change
/update-meta --only-variables  # Only update managed blocks (AGENTS.md, CLAUDE.md, etc.)
```

## Steps

1. Run sync:
   ```bash
   python scripts/sync.py $ARGUMENTS
   ```

2. Review sync.log for warnings or errors:
   ```bash
   cat sync.log | tail -20
   ```

3. Stage and commit:
   ```bash
   git add .claude/ .opencode/ .continue/ .gemini/ CLAUDE.md AGENTS.md
   git commit -m "chore: regenerate agents"
   ```

## Permissions prerequisite

A sync that runs with a configured primary role and active strict mode writes the
Main-Chat runtime gate into `opencode.json`: `permission.edit` and
`permission.bash` get the mapping-form glob `"**": "deny"`. From then on the
Main Chat cannot edit files or run shell commands — including the commands in
`## Steps` above.

Therefore run `/update-meta` through the `orchestrator` (or one of its workers),
or set `orchestrator.strict: false` before syncing and re-enable it afterwards.

### Recovery from a locked-out state

- Commit the pending changes from another harness or agent that still has write access.
- Or roll back: remove the managed `"**": "deny"` entries from `permission.edit`
  and `permission.bash` in `opencode.json`, then re-sync with
  `orchestrator.strict: false`. The next non-strict sync removes the managed deny
  itself and restores the prior value.
- Use the `git` agent for commits and pushes while the permission rules are in flux.

### Recovering lost `## Eigene Notizen` content

The notes section is user-owned and must never be overwritten by a sync (#515,
#1027). If it is missing after a sync, inspect the timestamped backups next to the
context file (`AGENTS.md.sync-backup-*`, `CLAUDE.md.sync-backup-*`) and copy the
`## Eigene Notizen` block back. The footer of `AGENTS.md` is rebuilt on every sync —
the notes are carried over verbatim and excluded from the drift signature, so a
backup only appears when the rest of the static part actually changed.

### `--validate` is not a test gate

`python scripts/sync.py --validate` validates configuration and template
consistency (placeholders, roles, references). It does **not** run the test
suite — run the tests separately when code changed:

```bash
python3 -m pytest tests/ -n 0 -q
```

## When to use

- After editing agent templates in `agents/1-generic/`
- After editing rules in `rules/`
- After editing hooks in `hooks/`
- After changing `project.yaml` variables
- After editing commands in `commands/1-generic/`

## Do NOT use for

- Updating agent-meta to a new version → use `/upgrade-meta`
- First-time setup → use `sync.py --init`
