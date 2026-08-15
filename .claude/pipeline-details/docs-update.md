# Pipeline `docs-update`

Execution mode: sequential

1. background(agent="documenter", prompt="Dokumentation aktualisieren") → warten bis abgeschlossen
2. background(agent="git", prompt="Commit + Push") → warten bis abgeschlossen
