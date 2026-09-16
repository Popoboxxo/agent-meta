# Stacking-Note — `feat/lit-cluster-review-security` (Cluster aus PR #790 + #792)

**Status:** aufgelöst — Branch auf `origin/main` rebased, PR-Basis auf `main` umgestellt
(nach dem Merge von #801).

## Was

`feat/lit-cluster-review-security` führt **PR #790** (`feat/lit-774`, Security- &
Operations-Rollen) und **PR #792** (`feat/lit-773`, Review- & Quality-Rollen) in
einem Branch zusammen, inklusive der Review-Fixes. Die Ausgangs-PRs bleiben offen;
sie werden nicht kommentiert oder geschlossen.

- Cluster-PR: [#816](https://github.com/Popoboxxo/agent-meta/pull/816)
- Ausgangs-PRs: [#790](https://github.com/Popoboxxo/agent-meta/pull/790), [#792](https://github.com/Popoboxxo/agent-meta/pull/792)
- Abhängigkeit: [#801](https://github.com/Popoboxxo/agent-meta/pull/801) (`feat/reference-standards-support`)

## Stacking (aufgelöst)

| | |
|---|---|
| Ehemalige Basis | `a59623c2` — Head von PR #801 (`feat/reference-standards-support`) |
| **Aktuelle Basis** | `main` (PR-Basis umgestellt) |
| Rebase-Ziel | `origin/main` @ `cfb4d40f` — Merge-Commit von #801 |
| Grund für die Stacking-Phase | `reference_standards` (`#801`) war die Grammatik, gegen die die Einträge aus #790 validiert werden |

## Erledigter Rebase-Schritt

```bash
git fetch origin
git switch feat/lit-cluster-review-security
git rebase origin/main                 # die 4 #801-Commits wurden als bereits-upstream übersprungen
git push --force-with-lease origin feat/lit-cluster-review-security
# danach: PR-Basis von feat/reference-standards-support auf main umgestellt
```

Der Rebase lief konfliktfrei; der Diff des Cluster-PRs gegen `main` ist frei von den
#801-Änderungen. Der Stacking-Absatz im PR-Body wurde entsprechend ersetzt.

## Belege (Stand des Branches)

- 15 Rollen-Templates (`agents/1-generic/`), genau ein Minor-Bump je Rolle relativ zu `main`
  (7 Security/Ops aus #790, 8 Review/Quality aus #792).
- `concept-reviewer.md`: `main`-Stand 1.8.0 (inkl. #786) gehalten, nur die #792-Ergänzungen
  re-appliziert, Bump auf 1.9.0 — #786 wird nicht revertiert.
- `catalog.behavior.yaml`: beide B7-Blöcke erhalten (15 Fälle, gesamt 22);
  `promptfooconfig.generated.yaml` regeneriert (71 Tests).
- `config/review-rules/*.yaml`: additiv (`BE-07`, `DB-07`, `FE-07`, `UI-06`, `UI-07`,
  `security.yaml` `asvs_level`), keine ID-Umnummerierung.
- `python3 scripts/gen_promptfoo_config.py --check` = rc 0, `python3 scripts/sync.py --check` = rc 0,
  `--validate` = rc 0, `python3 scripts/consistency-check.py` = rc 0.

## Post-Rebase-Verifikation (gegen `cfb4d40f`)

- `python3 scripts/gen_promptfoo_config.py --check` = rc 0.
- `python3 scripts/sync.py --check` = rc 0, `--validate` = rc 0.
- `python3 scripts/consistency-check.py` = rc 0.
- `pytest tests --ignore=tests/browser`: 2993 passed, 1 failed (bekannter, netzwerkbedingter
  `test_model_discovery`-Fehlschlag).
- `bash tests/scenarios/run.sh`: 63/63 bestanden, rc 0.
