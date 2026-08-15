# Pipeline `refactor`

Execution mode: loop

1. background(agent="senior-developer", prompt="Blast-Radius-Analyse: Scope bestimmen, betroffene Dateien identifizieren, Risiken bewerten") → warten bis abgeschlossen
2. background(agent="developer", prompt="Refactoring implementieren ohne funktionale Änderungen") → warten bis abgeschlossen

**review** — REPEAT_UNTIL Loop:
  - background(agent="developer", prompt="Refactoring auf Clean Code, SOLID, DRY prüfen und Feedback einarbeiten")
  - background(agent="code-reviewer", prompt="Review / Critic feedback")
  Max iterations: 2 → Erfolg pruefen; bei Abbruch User benachrichtigen

3. background(agent="git", prompt="Commit + Push") → warten bis abgeschlossen
