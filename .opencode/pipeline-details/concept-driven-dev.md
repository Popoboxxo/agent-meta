# Pipeline `concept-driven-dev`

Execution mode: loop

1. task(subagent_type="explorer", prompt="Codebase-/Kontext-Analyse (read-only): betroffene Dateien, Patterns, Risiko-Zonen, empfohlener Approach") → warten bis abgeschlossen
2. task(subagent_type="concept-specifier", prompt="Technische Spezifikation schreiben (Interface-Contracts, Datenfluss, Akzeptanzkriterien) — XL-Tasks: vorab Systemdesign über concept-architect") → warten bis abgeschlossen

**review** — REPEAT_UNTIL Loop:
  - task(subagent_type="concept-specifier", prompt="Spec/Design reviewen — Verdict APPROVED/CHANGES_REQUESTED/BLOCKED + Findings mit Severity")
  - task(subagent_type="concept-reviewer", prompt="Review / Critic feedback")
  Max iterations: 3 → Erfolg pruefen; bei Abbruch User benachrichtigen

3. task(subagent_type="developer", prompt="Implementierung gegen die freigegebene Spezifikation — Tier nach Task-Größe (S/M/L/XL): S junior-developer, M developer, L senior-developer, XL principal-developer") → warten bis abgeschlossen

**validate** — Parallel dispatch:
  - task(subagent_type="validator", prompt="DoD-Check + Traceability")
  - task(subagent_type="tester", prompt="Tests grün, keine Regression")

