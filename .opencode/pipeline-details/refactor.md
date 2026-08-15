# Pipeline `refactor`

Execution mode: loop

1. task(subagent_type="senior-developer", prompt="Blast-Radius-Analyse: Scope bestimmen, betroffene Dateien identifizieren, Risiken bewerten") → warten bis abgeschlossen
2. task(subagent_type="developer", prompt="Refactoring implementieren ohne funktionale Änderungen") → warten bis abgeschlossen

**review** — REPEAT_UNTIL Loop:
  - task(subagent_type="developer", prompt="Refactoring auf Clean Code, SOLID, DRY prüfen und Feedback einarbeiten")
  - task(subagent_type="code-reviewer", prompt="Review / Critic feedback")
  Max iterations: 2 → Erfolg pruefen; bei Abbruch User benachrichtigen

3. task(subagent_type="git", prompt="Commit + Push") → warten bis abgeschlossen
