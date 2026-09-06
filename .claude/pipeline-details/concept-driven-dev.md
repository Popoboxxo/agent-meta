# Pipeline `concept-driven-dev`

Execution mode: loop

1. background(agent="explorer", prompt="Codebase-/Kontext-Analyse (read-only): betroffene Dateien, Patterns, Risiko-Zonen, empfohlener Approach") → warten bis abgeschlossen
2. background(agent="concept-specifier", prompt="Technische Spezifikation schreiben (Interface-Contracts, Datenfluss, Akzeptanzkriterien) — XL-Tasks: vorab Systemdesign über concept-architect") → warten bis abgeschlossen

**review** — REPEAT_UNTIL Loop:
  - background(agent="concept-specifier", prompt="Spec/Design reviewen — Verdict APPROVED/CHANGES_REQUESTED/BLOCKED + Findings mit Severity")
  - background(agent="concept-reviewer", prompt="Review / Critic feedback")
  Max iterations: 3 → Erfolg pruefen; bei Abbruch User benachrichtigen

3. background(agent="developer", prompt="Implementierung gegen die freigegebene Spezifikation — Tier nach Task-Größe (S/M/L/XL): S junior-developer, M developer, L senior-developer, XL principal-developer") → warten bis abgeschlossen

**validate** — Parallel dispatch:
  - background(agent="validator", prompt="DoD-Check + Traceability")
  - background(agent="tester", prompt="Tests grün, keine Regression")

