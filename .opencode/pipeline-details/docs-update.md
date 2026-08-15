# Pipeline `docs-update`

Execution mode: sequential

1. task(subagent_type="documenter", prompt="Dokumentation aktualisieren") → warten bis abgeschlossen
2. task(subagent_type="git", prompt="Commit + Push") → warten bis abgeschlossen
