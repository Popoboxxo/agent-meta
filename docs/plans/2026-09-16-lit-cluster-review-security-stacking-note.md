# Stacking-Note — `feat/lit-cluster-review-security` (Cluster aus PR #790 + #792)

**Status:** aktiv, vorwärtsgerichtet. Keine abgeschlossene Arbeit.

## Was

`feat/lit-cluster-review-security` führt **PR #790** (`feat/lit-774`, Security- &
Operations-Rollen) und **PR #792** (`feat/lit-773`, Review- & Quality-Rollen) in
einem Branch zusammen, inklusive der Review-Fixes. Die Ausgangs-PRs bleiben offen;
sie werden nicht kommentiert oder geschlossen.

- Cluster-PR: [#816](https://github.com/Popoboxxo/agent-meta/pull/816)
- Ausgangs-PRs: [#790](https://github.com/Popoboxxo/agent-meta/pull/790), [#792](https://github.com/Popoboxxo/agent-meta/pull/792)
- Abhängigkeit: [#801](https://github.com/Popoboxxo/agent-meta/pull/801) (`feat/reference-standards-support`)

## Stacking

| | |
|---|---|
| Basis-Commit des Branches | `a59623c2` — Head von PR #801 |
| PR-Basis | `feat/reference-standards-support` (**nicht** `main`) |
| Grund | `reference_standards` (`#801`) ist die Grammatik, gegen die die Einträge aus #790 validiert werden |

## Pflicht-Schritt nach dem Merge von #801

```bash
git fetch origin
git switch feat/lit-cluster-review-security
git rebase origin/main                 # #801-Inhalte sind dann bereits in main
git push --force-with-lease origin feat/lit-cluster-review-security
# danach: PR-Basis von feat/reference-standards-support auf main umstellen
```

Nach dem Rebase ist der Diff des Cluster-PRs gegen `main` frei von den
#801-Änderungen; der Stacking-Absatz im PR-Body ist dann zu entfernen.

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
