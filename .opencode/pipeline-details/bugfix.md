# Pipeline `bugfix`

Execution mode: loop

1. task(subagent_type="bug-feature-analyzer", prompt="Bug klassifizieren (Bug/User-Error/Feature/Out-of-Scope). Bei User-Error/Out-of-Scope → Pipeline stoppen.") → warten bis abgeschlossen
2. task(subagent_type="developer", prompt="Bugfix implementieren") → warten bis abgeschlossen

**review** — REPEAT_UNTIL Loop:
  - task(subagent_type="developer", prompt="Code-Qualität, Blast-Radius, SOLID/DRY prüfen")
  - task(subagent_type="code-reviewer", prompt="Review / Critic feedback")
  Max iterations: 2 → Erfolg pruefen; bei Abbruch User benachrichtigen

3. task(subagent_type="documenter", prompt="CODEBASE_OVERVIEW und Session-Erkenntnisse aktualisieren") → warten bis abgeschlossen
