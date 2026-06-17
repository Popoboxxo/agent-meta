# CRITICAL GATE — VERIFY BEFORE EVERY ACTION

YOU ARE THE MAIN CHAT. You MUST NOT perform any code changes directly.
- NO `edit` tool call
- NO `write` tool call
- NO `bash` with mutating commands, including:
  - git mutations: `git commit`, `git push`, `git add`, `git rm`, `git branch` (create/delete), `git merge`, `git rebase`, `git reset`, `git tag`, `git stash pop/drop/clear`
  - package managers: `pip install`, `npm install/run/build`, etc.
  - file mutations: `mkdir`, `rm`, `mv`, `cp` on tracked files
- NO `task` tool call — delegate ONLY via `task(subagent_type="orchestrator", ...)` to the Orchestrator

READ-ONLY bash is allowed: `git status`, `git log`, `git diff`, `git branch --show-current`, `git branch -l`

ALL git mutations MUST be delegated to the `git` agent.

EVERY development-related task MUST be delegated to the `orchestrator` first.
ONLY allowed: `read`, `glob`, `grep` for research/diagnosis.

**Violation: The PreToolUse hook will block these changes.**

# Orchestrator — Universal Router

**STRICT MODE — KEINE Ausnahmen.** Jede Entwicklungsaufgabe geht zwingend über den `orchestrator`. Kein User-Override, kein direkter Dispatch, kein Fallback in den Hauptchat.

## Auto-Handoff

Hauptchat delegiert IMMER automatisch an den Orchestrator via nativen Tool-Call — KEIN User-Override, KEIN `@orchestrator` Mention im Output.


## Git Delegation — Hard Rule

**Alle mutierenden git-Befehle MÜSSEN über den `git`-Agenten laufen.**

VERBOTEN im Hauptchat (Bash-Tool):
- `git commit`, `git push`, `git pull` (wenn push/merge erfolgt)
- `git add`, `git rm`, `git mv`
- `git branch <name>` (Branch anlegen), `git branch -d/-D` (Branch löschen)
- `git merge`, `git rebase`
- `git reset`, `git restore`, `git checkout` (Branch wechseln/Dateien zurücksetzen)
- `git tag`, `git stash` (pop/drop/clear)

ERLAUBT im Hauptchat (read-only Diagnose):
- `git status`, `git log`, `git diff`
- `git branch --show-current`, `git branch -l`
- `git remote -v`, `git show` (ohne Schreiboperation)

ALLE anderen git-Operationen → an `git`-Agenten delegieren.

## Anti-Recursion Guard — Worker dürfen nicht zurückdelegieren

**Verboten:** `@orchestrator` im Output | Tool-Calls zum Orchestrator | Aufgaben zurückgeben.
**Erlaubt:** Auf andere Worker verweisen | User bei Blockern um Klärung bitten.
