# CRITICAL GATE
MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`. Keine Ausnahmen.

## Git Delegation
Git Mutationen (commit, push, add etc) -> `git` Agent. Read-only (status, log) im Main Chat ok.

Native Extensions (Skills/Hooks) erlaubt, ignorieren nicht Branch-Guard/DoD.

Anti-Recursion: Worker dürfen nicht an `orchestrator` zurück delegieren.

## Anti-Patterns
- **Worktree Isolation:** Niemals `isolation: "worktree"` bei Subagenten verwenden (schreibt in interne Infrastruktur-Ordner, führt zu Datenverlust).
