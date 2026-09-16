# Stacking-Note — `feat/lit-cluster-se-test` (Cluster aus PR #788 + #789)

**Status:** aktiv, vorwärtsgerichtet. Keine abgeschlossene Arbeit.

## Was

`feat/lit-cluster-se-test` führt **PR #788** (`feat/lit-771`, Testing- & V&V-Rollen)
und **PR #789** (`feat/lit-772`, Systems-Engineering-Rollen) in einem Branch zusammen,
inklusive der Review-Fixes. Die Ausgangs-PRs bleiben offen; sie werden nicht
kommentiert oder geschlossen.

- Cluster-PR: [#815](https://github.com/Popoboxxo/agent-meta/pull/815)
- Ausgangs-PRs: [#788](https://github.com/Popoboxxo/agent-meta/pull/788), [#789](https://github.com/Popoboxxo/agent-meta/pull/789)
- Abhängigkeit: [#801](https://github.com/Popoboxxo/agent-meta/pull/801) (`feat/reference-standards-support`)

## Stacking

| | |
|---|---|
| Basis-Commit des Branches | `a59623c2` — Head von PR #801 |
| PR-Basis | `feat/reference-standards-support` (**nicht** `main`) |
| Grund | `reference_standards` (`#801`) ist die Grammatik, gegen die die 17 Einträge aus #788/#789 validiert werden |

## Pflicht-Schritt nach dem Merge von #801

```bash
git fetch origin
git switch feat/lit-cluster-se-test
git rebase origin/main                 # #801-Inhalte sind dann bereits in main
git push --force-with-lease origin feat/lit-cluster-se-test
# danach: PR-Basis von feat/reference-standards-support auf main umstellen
```

Nach dem Rebase ist der Diff des Cluster-PRs gegen `main` frei von den
#801-Änderungen; der Stacking-Absatz im PR-Body ist dann zu entfernen.

## Belege (Stand des Branches)

- 18 Rollen-Templates (`agents/1-generic/`), genau ein Minor-Bump je Rolle relativ zu `a59623c2`.
- `catalog.behavior.yaml`: beide B7-Blöcke erhalten; `promptfooconfig.generated.yaml` regeneriert (74 Tests).
- `python3 scripts/gen_promptfoo_config.py --check` = rc 0, `python3 scripts/sync.py --check` = rc 0,
  `--validate` = rc 0, `python3 scripts/consistency-check.py` = rc 0.
