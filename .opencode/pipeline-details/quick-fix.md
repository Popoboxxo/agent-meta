# Pipeline `quick-fix`

Execution mode: sequential

1. task(subagent_type="developer", prompt="Bugfix") → warten bis abgeschlossen
2. task(subagent_type="git", prompt="Commit + Push") → warten bis abgeschlossen
