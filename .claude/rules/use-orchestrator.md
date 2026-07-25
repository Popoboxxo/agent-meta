# Main-Chat Mode
Main Chat ist Router + Worker. Kein Orchestrator-Subagent.

## Git Delegation
Git Mutationen (commit, push, add etc) -> `git` Agent. Read-only (status, log) im Main Chat ok.
Ausnahme auf User-Wunsch erlaubt.

Native Extensions (Skills/Hooks) erlaubt, ignorieren nicht Branch-Guard/DoD.

