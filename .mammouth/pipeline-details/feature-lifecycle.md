# Pipeline `feature-lifecycle`

Execution mode: parallel_group

1. background(agent="git", prompt="Feature-Branch anlegen") → warten bis abgeschlossen

**implement** — Plan-driven: Agent aus payload.plan_ref (Stage-ID 'implement') übernehmen.

  **Plan-Validierung (vor Delegation):**
  1. Prüfe: payload.plan_ref-Pfad existiert → sonst fallback_agent = `developer`
  2. Prüfe: Plan-Frontmatter `pipeline_stages` enthält `implement` → sonst Fehler
  3. Prüfe: Agent in Stage `implement` ∈ {junior-developer, developer, senior-developer, frontend-component-engineer} → sonst `developer`
  4. Bei allen Fehlern: `developer` verwenden, Fehler in Status-Payload dokumentieren


**validate-and-document** — Parallel dispatch:
  - background(agent="validator", prompt="DoD-Check")
  - background(agent="documenter", prompt="CODEBASE_OVERVIEW aktualisieren")

2. background(agent="git", prompt="Commit: feat([REQ-ID]): ... + PR") → warten bis abgeschlossen
