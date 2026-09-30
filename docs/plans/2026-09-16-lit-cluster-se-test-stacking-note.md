# Stacking-Note — `feat/lit-cluster-se-test` (Cluster aus PR #788 + #789)

**Status:** aufgelöst — Branch auf `origin/main` rebased, PR-Basis auf `main` umgestellt
(nach dem Merge von #801).

## Was

`feat/lit-cluster-se-test` führt **PR #788** (`feat/lit-771`, Testing- & V&V-Rollen)
und **PR #789** (`feat/lit-772`, Systems-Engineering-Rollen) in einem Branch zusammen,
inklusive der Review-Fixes. Die Ausgangs-PRs bleiben offen; sie werden nicht
kommentiert oder geschlossen.

- Cluster-PR: [#815](https://github.com/Popoboxxo/agent-meta/pull/815)
- Ausgangs-PRs: [#788](https://github.com/Popoboxxo/agent-meta/pull/788), [#789](https://github.com/Popoboxxo/agent-meta/pull/789)
- Abhängigkeit: [#801](https://github.com/Popoboxxo/agent-meta/pull/801) (`feat/reference-standards-support`)

## Stacking (aufgelöst)

| | |
|---|---|
| Ehemalige Basis | `a59623c2` — Head von PR #801 (`feat/reference-standards-support`) |
| **Aktuelle Basis** | `main` (PR-Basis umgestellt) |
| Rebase-Ziel | `origin/main` @ `cfb4d40f` — Merge-Commit von #801 |
| Grund für die Stacking-Phase | `reference_standards` (`#801`) war die Grammatik, gegen die die 17 Einträge aus #788/#789 validiert werden |

## Erledigter Rebase-Schritt

```bash
git fetch origin
git switch feat/lit-cluster-se-test
git rebase origin/main                 # die 4 #801-Commits wurden als bereits-upstream übersprungen
git push --force-with-lease origin feat/lit-cluster-se-test
# danach: PR-Basis von feat/reference-standards-support auf main umgestellt
```

Der Rebase lief konfliktfrei; der Diff des Cluster-PRs gegen `main` ist frei von den
#801-Änderungen. Der Stacking-Absatz im PR-Body wurde entsprechend ersetzt.

## Belege (Stand des Branches)

- 18 Rollen-Templates (`agents/1-generic/`), genau ein Minor-Bump je Rolle relativ zu `a59623c2`.
- `catalog.behavior.yaml`: beide B7-Blöcke erhalten; `promptfooconfig.generated.yaml` regeneriert (74 Tests).
- `python3 scripts/gen_promptfoo_config.py --check` = rc 0, `python3 scripts/sync.py --check` = rc 0,
  `--validate` = rc 0, `python3 scripts/consistency-check.py` = rc 0.

## Post-Rebase-Verifikation (gegen `cfb4d40f`)

- `python3 scripts/gen_promptfoo_config.py --check` = rc 0.
- `python3 scripts/sync.py --check` = rc 0, `--validate` = rc 0.
- `python3 scripts/consistency-check.py` = rc 0.
- `pytest tests --ignore=tests/browser`: 2993 passed, 1 failed (bekannter, netzwerkbedingter
  `test_model_discovery`-Fehlschlag).
- `bash tests/scenarios/run.sh`: 63/63 bestanden, rc 0.
