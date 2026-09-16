# Stacking-Note — `feat/lit-cluster-product-planning` (Cluster aus PR #787 + #793)

**Status:** aktiv, vorwärtsgerichtet. Keine abgeschlossene Arbeit.

## Was

`feat/lit-cluster-product-planning` führt **PR #787** (`feat/lit-775`, Knowledge-/
Documentation-Rollen) und **PR #793** (`feat/lit-770`, Product-/Planning-/Feedback-/
Governance-Rollen) in einem Branch zusammen, inklusive der Review-Fixes. Die Ausgangs-PRs
bleiben offen; sie werden nicht kommentiert oder geschlossen.

- Cluster-PR: [#818](https://github.com/Popoboxxo/agent-meta/pull/818)
- Ausgangs-PRs: [#787](https://github.com/Popoboxxo/agent-meta/pull/787), [#793](https://github.com/Popoboxxo/agent-meta/pull/793)
- Abhängigkeit: [#801](https://github.com/Popoboxxo/agent-meta/pull/801) (`feat/reference-standards-support`)

## Stacking

| | |
|---|---|
| Basis-Commit des Branches | `a59623c2` — Head von PR #801 |
| PR-Basis | `feat/reference-standards-support` (**nicht** `main`) |
| Grund | `reference_standards` (#801) ist die Grammatik, gegen die die Einträge aus #787/#793 validiert werden |

## Pflicht-Schritt nach dem Merge von #801

```bash
git fetch origin
git switch feat/lit-cluster-product-planning
git rebase origin/main                 # #801-Inhalte sind dann bereits in main
git push --force-with-lease origin feat/lit-cluster-product-planning
# danach: PR-Basis von feat/reference-standards-support auf main umstellen
```

Nach dem Rebase ist der Diff des Cluster-PRs gegen `main` frei von den #801-Änderungen;
der Stacking-Absatz im PR-Body ist dann zu entfernen.

## Belege (Stand des Branches)

- 19 Rollen-Templates (`agents/1-generic/`), genau **ein** korrekter Bump je Rolle relativ
  zu `main` (9 aus #787, 10 aus #793). Besondere Konfliktfälle:
  - `documenter` **1.10.0** — der PR beanspruchte 1.9.0, main hatte 1.9.0 aber unabhängig
    belegt (`## 6. Plan-Archivierung`) → ein weiterer Minor-Bump; neuer Abschnitt als
    `## 7. Documentation structure`, `Return` → `## 8.`.
  - `ideation` **1.15.0** — die Branch-Version 1.13.0 war eine Regression gegen main 1.14.0;
    main's Routing-/§4-Inhalt bleibt erhalten, nur die Skeleton-Ergänzungen kamen hinzu.
  - `planner` **1.5.0** — Branch == main (1.4.0); main's §3 Plan-Template + Nummerierung
    bleiben, `Assumptions`/`Re-planning` kommen hinzu.
  - `knowledge-ingestor` **1.6.0** — PR-Bump kollidierte mit main (beide 1.5.0), obwohl
    Inhalt hinzukam.
- `agents/2-platform/homeassistant-documenter.md`: `based-on` auf `1-generic/documenter.md@1.10.0`
  nachgezogen (Guard `test_conventions_platform_cascade.py`), Version 1.1.1.
- `catalog.behavior.yaml`: **beide** B7-Blöcke erhalten (9 aus #787 + 10 aus #793 = 19 Fälle,
  gesamt 26); `promptfooconfig.generated.yaml` regeneriert (718 Zeilen, nie manuell gemerged).
- Eval-Literale: alle reinen Regex-Literale der beiden neuen Blöcke auf plain literals
  umgestellt (promptfoo `icontains-any` matcht literal); `'definition.of.ready'`/`'tech.debt'`
  → `'definition-of-ready'`/`'tech-debt'`.
- `reference_standards`: Einträge grammatik-valide (nur `"Frictionless Data @optional-interop"`
  war ungültig → `"Frictionless Data"`).
- `.meta-config/project.yaml`: `product-manager` + `app-lifecycle-governor` ausgewählt, damit
  die zwei B7-Cases auf synced Rollen auflösen. **Folge:** Agent-Directory im always-on
  managed block +2 Zeilen (222 → 224) → Ratchet in `tests/test_context_compact_mode.py`
  dokumentiert angehoben. Retarget wurde verworfen, weil kein synced Role-Template die
  Portfolio-/Tech-Debt-/SLI-/Exit-Kriterien-Disziplin trägt (`SLI` gibt es nur in
  `sre-engineer`, ebenfalls nicht synced) — ein retargeteter Case wäre nicht erfüllbar.
- Gates: `python3 scripts/gen_promptfoo_config.py --check` = rc 0,
  `python3 scripts/sync.py --check` = rc 0, `--validate` = rc 0,
  `python3 scripts/consistency-check.py` = rc 0. Targeted-Suite: 572 passed.
- Volle Suite `pytest tests/ --ignore=tests/browser`: 2987 passed, 1 failed — der Fehlschlag
  (`test_model_discovery.py::test_fetch_anthropic_models_respects_blacklist`) ist
  umgebungsbedingt (Live-Fetch per `pytest-socket` blockiert → curated fallback).

## Abgrenzung zu den Schwester-Clustern

- `feat/lit-cluster-review-security` (PR #816, aus #790 + #792) ist ein **eigener** gestackter
  Branch auf derselben Basis `a59623c2`. Der B7-Hygiene-Gate (`"b7-"` in der ID-Präfix-Liste
  von `tests/test_agent_eval_framework.py`) wird dort eingeführt und hier bewusst **nicht**
  dupliziert, um keinen Konflikt zwischen den gestackten Cluster-PRs zu erzeugen.
- `feat/lit-cluster-core-agents` (PR #817, aus #795 + #791) ist ebenfalls ein eigener
  gestackter Branch auf `a59623c2`.
