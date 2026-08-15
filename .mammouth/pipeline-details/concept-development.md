# Pipeline `concept-development`

Execution mode: loop

1. background(agent="ideation", prompt="Recherche: Stand der Technik, Optionen, Quellen, Trade-offs") → warten bis abgeschlossen

**concept** — REPEAT_UNTIL Loop:
  - background(agent="ideation", prompt="Konzept/Design-Doc erstellen und Review-Feedback einarbeiten")
  - background(agent="concept-reviewer", prompt="Review / Critic feedback")
  Max iterations: 3 → Erfolg pruefen; bei Abbruch User benachrichtigen

2. background(agent="requirements", prompt="Konzept in REQs überführen") → warten bis abgeschlossen
