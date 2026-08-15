# Pipeline `concept-development`

Execution mode: loop

1. task(subagent_type="ideation", prompt="Recherche: Stand der Technik, Optionen, Quellen, Trade-offs") → warten bis abgeschlossen

**concept** — REPEAT_UNTIL Loop:
  - task(subagent_type="ideation", prompt="Konzept/Design-Doc erstellen und Review-Feedback einarbeiten")
  - task(subagent_type="concept-reviewer", prompt="Review / Critic feedback")
  Max iterations: 3 → Erfolg pruefen; bei Abbruch User benachrichtigen

2. task(subagent_type="requirements", prompt="Konzept in REQs überführen") → warten bis abgeschlossen
