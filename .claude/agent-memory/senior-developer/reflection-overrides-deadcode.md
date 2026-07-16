---
name: reflection-overrides-deadcode
description: reflection-pairs.overrides in project.yaml haben KEINE Wirkung auf generiertes Output — reflection.py ist nicht verdrahtet
metadata:
  type: project
---

`reflection-pairs.overrides` (z.B. `dev-review-loop.max_iterations: 5`) in `.meta-config/project.yaml` schlagen sich NICHT im generierten Agenten-Output nieder.

**Why:** `scripts/lib/reflection.py` hat die komplette Merge-Machinerie (`load_project_overrides`, `apply_project_overrides`, `inject_loop_config`), aber `scripts/lib/config.py` (build_variables, ~Zeile 488-499) ruft sie NIE auf — es setzt nur `REFLECTION_PAIRS_ENABLED` und ein hartkodiertes `MAX_ITERATIONS="3"`. Zusätzlich existiert `{{MAX_ITERATIONS}}` in keinem Template. reflection.py ist damit Dead Code im Sync-Flow. Gegensatz: `quality-pipelines.overrides` funktionieren (config.py ruft `apply_overrides` auf, se-cascade-disable + max_iter greifen).

**How to apply:** Wenn jemand reflection-pair-Overrides „reparieren" will → config.py mit reflection.py verdrahten UND einen Ziel-Platzhalter im Template schaffen. Verifiziert 2026-07-16, ungefixt. Verwandt: Admin-UI `/api/reflection-pairs` liefert ebenfalls nur Rohwerte aus role-defaults.yaml (keine Override-Anzeige).
