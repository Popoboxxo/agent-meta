# Stacking-Note — `feat/lit-cluster-core-agents` (Cluster aus PR #795 + #791)

**Status:** aktiv, vorwärtsgerichtet. Keine abgeschlossene Arbeit.

## Was

`feat/lit-cluster-core-agents` führt **PR #795** (`feat/lit-769-core-development`,
Core-Development-Rollen) und **PR #791** (`feat/lit-777`, Design-/Data-/Content-Rollen) in
einem Branch zusammen, inklusive der Review-Fixes. Die Ausgangs-PRs bleiben offen; sie
werden nicht kommentiert oder geschlossen.

- Cluster-PR: [#817](https://github.com/Popoboxxo/agent-meta/pull/817)
- Ausgangs-PRs: [#795](https://github.com/Popoboxxo/agent-meta/pull/795), [#791](https://github.com/Popoboxxo/agent-meta/pull/791)
- Abhängigkeit: [#801](https://github.com/Popoboxxo/agent-meta/pull/801) (`feat/reference-standards-support`)

## Stacking

| | |
|---|---|
| Basis-Commit des Branches | `a59623c2` — Head von PR #801 |
| PR-Basis | `feat/reference-standards-support` (**nicht** `main`) |
| Grund | `reference_standards` (#801) ist die Grammatik, gegen die die Einträge aus #769/#777 validiert werden |

## Pflicht-Schritt nach dem Merge von #801

```bash
git fetch origin
git switch feat/lit-cluster-core-agents
git rebase origin/main                 # #801-Inhalte sind dann bereits in main
git push --force-with-lease origin feat/lit-cluster-core-agents
# danach: PR-Basis von feat/reference-standards-support auf main umstellen
```

Nach dem Rebase ist der Diff des Cluster-PRs gegen `main` frei von den #801-Änderungen;
der Stacking-Absatz im PR-Body ist dann zu entfernen.

## Belege (Stand des Branches)

- 21 Rollen-Templates (`agents/1-generic/`), genau **ein** korrekter Bump je Rolle relativ
  zu `main` (9 Core-Development aus #769, 12 Design/Data/Content aus #777).
  - `explorer` 1.4.0 und `orchestrator` 8.0.0 (MAJOR) — beide waren echte Versions-Konflikte
    gegen `main` (unabhängiger Bump durch #786).
  - `concept-architect` / `concept-specifier` 1.4.0 — die PRs brachten sonst eine Regression
    (1.2.0 < main 1.3.0).
- `catalog.behavior.yaml`: **beide** B7-Blöcke erhalten (21 Fälle, gesamt 28);
  `promptfooconfig.generated.yaml` regeneriert (77 Tests, 21 davon `b7-`).
- `reference_standards`: 30 Einträge, 0 ungültig (Grammatik aus #801).
- Keine Body-Zeiger mehr auf das per Default gestrippte Feld `reference_standards`.
- `python3 scripts/gen_promptfoo_config.py --check` = rc 0, `python3 scripts/sync.py --check` = rc 0,
  `--validate` = rc 0, `python3 scripts/consistency-check.py` = rc 0.
- Volle Suite `pytest tests/ --ignore=tests/browser`: 2987 passed, 1 failed — der Fehlschlag
  (`test_model_discovery.py`) ist umgebungsbedingt (Live-Fetch per `pytest-socket` blockiert).

## Abgrenzung zum Schwester-Cluster

`feat/lit-cluster-review-security` (PR #816, aus #790 + #792) ist ein **eigener** gestackter
Branch auf derselben Basis `a59623c2`. Der B7-Hygiene-Gate (`"b7-"` in der ID-Präfix-Liste von
`tests/test_agent_eval_framework.py`) wird dort eingeführt und hier bewusst nicht dupliziert,
um keinen Konflikt zwischen den beiden gestackten Cluster-PRs zu erzeugen.
