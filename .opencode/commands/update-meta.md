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

## When to use

- After editing agent templates in `agents/1-generic/`
- After editing rules in `rules/`
- After editing hooks in `hooks/`
- After changing `project.yaml` variables
- After editing commands in `commands/1-generic/`

## Do NOT use for

- Updating agent-meta to a new version → use `/upgrade-meta`
- First-time setup → use `sync.py --init`
