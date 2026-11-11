---
pipeline_stages:
  implement: 4
status: DRAFT
date: 2026-11-11
base-commit: 9aa0e0c0
roadmap: docs/superpowers/plans/2026-11-10-backlog-roadmap.md
phase: F
issues: [1188, 1201, 1202, 1203, 1204, 1211]
branch: feat/phase-f-label-taxonomy
---

# Phase F: Label-Taxonomie (Wrapper-Plan um #1188) Implementation Plan

> Status: DRAFT
> Revision: Entscheidungen 49 (#1187 erster Block von E), 51 (#1201 GitHub-Projektion `bug`) 52 (max. 2 PRs je Phase), 56 (F nicht vor E-Kern) und 57 (#1201 GitLab-Projektion `type::bug`) eingearbeitet; F-offen-1 (51) und F-offen-2 (57) beantwortet, Restschritt = Freigabe-Gate Task 0b (beide Werte).
> Base: `origin/main 9aa0e0c0` (Code-Anker im Review 2026-11-11 gegen `9aa0e0c0` neu gemessen; Plan ursprünglich gegen `a3d65da4`) | Roadmap Phase F (Welle 3) | Issues #1188, #1201, #1202, #1203, #1204, #1211 (6 Issues; #1141 gehört nach Entscheidung 35 zu Phase D)

**Goal:** Reihenfolge, PR-Schnitt und Abhängigkeiten der sechs Phase-F-Issues festlegen, ohne den APPROVED Plan zu #1188 zu duplizieren. Der Kern (#1188) wird per Task-ID des bestehenden Plans ausgeführt; #1141 (Schema-Keys) ist nicht mehr Teil von Phase F, sondern letzter Teil von Phase D nach #1181 (Entscheidung 35); die Kinder (#1201-#1204) bekommen eigene, kleine TDD-Tasks; #1211 bleibt bis zum Pilot-Gate gesperrt. Phasen-PR mit den derzeit ausführbaren Tasks, gesperrte/spec-gesteuerte Tasks (Task 2, Task 3) in einem Nachfolge-PR derselben Phase; max. 2 PRs, ein Commit je Task (Entscheidungen 17, 52).
**Architecture:** Drei Blöcke. (1) #1203 vorab (S, unabhängig vom Kern, muss vor Kern-T21 landen). (2) Kern #1188 = Referenz auf `docs/plans/2026-11-09-issue-label-taxonomy-plan.md` T1-T30. (3) Kinder #1201/#1202/#1204 nach dem Kern (nutzen Resolver, `ISSUE_*`-Platzhalter und die Admin-UI-Sektion). #1141 (Schema-Keys, Unbekannt-Key-Warnung) liegt im Phase-D-Plan `docs/superpowers/plans/2026-11-11-phase-d-guards-hooks.md` als letzter Teil nach #1181 (Entscheidung 35). #1211 nicht ausführbar (Pilot-Gate, Entscheidung 26).
**Tech Stack:** Python 3.9+ (stdlib + PyYAML), pytest, YAML-Presets, Markdown-Templates mit Platzhaltern, Vanilla-JS in `docs/ui/admin-ui.html`.
**Spec:** `docs/specs/2026-11-09-issue-label-taxonomy-spec.md` (APPROVED, Kern); Kinder: Task 0.

Abhängigkeiten/Wellen (Roadmap Abschnitt 3): Welle 3, hängt ab von E (#1186, Templates/Preset-Dateien) und A/B/C (CI grün, Dateikonflikte `admin-server.py`/`admin-ui.html`). Parallel zu D, mit Reihenfolge-Kette unten.

## Reihenfolge-Kette (verbindlich)

- Freigegebene Kette (Plan #1188 `## Global Constraints`, Wave-Reihenfolge, Entscheidung 35): `#1187 -> #1186 -> #1188 -> #1181 -> #1141`. #1141 ist letzter Teil von Phase D (nach #1181), nicht Teil dieses Plans.
- Regel (Entscheidung 56): **Phase F startet NICHT vor dem E-Kern (Kette); Phase E (#1186, Artefaktorte) läuft vor Phase F**. Entscheidung 49 hebt nur die #1187-Sperre auf (Task V), nicht die Abhängigkeit von #1186; Task K bleibt hinter #1186 (E); der E-Plan liegt in W vor (`docs/superpowers/plans/2026-11-11-phase-e-artifact-locations.md`, Check-Task E-C0 für #1187). Die Reihenfolge #1186 (E) vor #1188 (F-Kern) aus der Kette bleibt unverändert.
- #1187 (Kern-Voraussetzung): laut Entscheidung 49 **erster Block von Phase E** (E-Block 0, E-B0-T1/E-B0-T2; Phase E = 6 Issues, Roadmap-Gesamtzahl 90; Wiederöffnen von #1187 nur nach User-Freigabe, nicht eigenmächtig). Die #1187-Sperre für Phase F fällt, sobald der #1187-Block von E drin ist (Entscheidung 49: "Block 2 von E und damit F sind entsperrt"). **Kein eigener Check in Phase F**: Querverweis auf E-C0/E-Block 0 (Entscheidungen 19, 49), hier nicht dupliziert. Task V unten.
- Phase D Strom A (#1181) braucht **nach** Phase F-Kern (#1188). Phase D (`docs/superpowers/plans/2026-11-11-phase-d-guards-hooks.md:277`) führt dies als D-neu-2, durch Entscheidung 19 beantwortet (Kette #1188 -> #1181). Kinder #1201/#1202/#1204 blockieren #1181 nicht.
- #1141 ist **nicht** Teil von Phase F (Entscheidung 35, Querverweis auf den D-Plan `docs/superpowers/plans/2026-11-11-phase-d-guards-hooks.md`). Der frühere offene Konflikt (#1141 in F vs. Kette nach #1181) ist damit aufgelöst; Task 5 entfällt.

## Global Constraints

- Python 3.9-kompatibel (kein `X | Y`-Typsyntax ohne `from __future__ import annotations`, kein `match`); nur stdlib + PyYAML.
- Provider-agnostisch: Verzweigung über Config-Keys/Capability-Flags (`scoped-labels`, `labels`, `issue-forms`), nie `if provider == "Name"`; Alias `Codeberg` nur als Daten in `config/issue-adapters.yaml`.
- Commits: Englisch, Conventional Commits, Subject <= 72 Zeichen, ein Commit pro Task, kein BOM; Bodies später als Datei. Phasen-PR auf Branch `feat/phase-f-label-taxonomy` (Entscheidung 17), dazu höchstens ein Nachfolge-PR derselben Phase für gesperrte/spec-gesteuerte Tasks (Entscheidung 52).
- Kein `isolation: "worktree"`; Tests via `python3 -m pytest <datei>::<test>`; Gesamtprüfung `python3 scripts/sync.py --validate`.
- Keine Aktivierung von `issue-conventions` in `.meta-config/project.yaml` dieses Repos (Golden-Test AC-9 bleibt beweiskräftig).
- Eine Konfliktfläche = ein Task: `docs/ui/admin-ui.html` (Kern T26/T27, #1204), `scripts/sync.py` (#1203, Kern T21), `scripts/lib/consistency/issue_labels.py` (Kern T23, #1202) strikt sequentiell.
- Keine Live-Label-Operation gegen echte Tracker im Plan (Referenzplan: Mock, "kein echtes Netzwerk" `:1051`). Label-Löschungen/Prune im echten Repo nur als fertige `!`-Befehle für den User, nie selbst ausführen. Keine Closing-Keywords in Commits/PR (Entscheidung 38e); Trailer wörtlich aus dem Task-Prompt (Entscheidung 25).
- Kern wird **nicht** neu geplant: Ausführung gemäß Plan #1188 inkl. dessen Constraints (Transport-Härtung H-1..H-7, Prune nur über Manifest, kein Auto-Commit).

## Klassifikation

Spec-Zuordnung: Kern-Spec deckt #1188 und die Projektionsteile von #1201/#1202. Kinder-Addendum (#1201 Migration, #1202 Priority) über Task 0. #1203 und #1204 (beide Teile): Klasse S, keine Spec.

| Issue | Klasse | Begründung | Spec |
|---|---|---|---|
| #1188 | XL | 30 Tasks, 3 Module, Schema, UI | APPROVED, Plan APPROVED (`docs/plans/2026-11-09-issue-label-taxonomy-plan.md`). Referenz |
| #1203 | S | ein Flag-Rename mit Alias, Parser-Test, Doku | entfällt |
| #1201 | M | Preset-Default + Migrationswarnung + Projektion | Task 0 (Addendum), Projektionsteil durch #1188-Spec abgedeckt |
| #1202 | M | Priority-Kanonisierung, Platzhalter, Consistency-Regel; `status`/`severity` offen | Task 0 (Addendum) |
| #1204 | S (Teil 1), S (Teil 2) | Teil 1: UI-Hinweis + `language` ins Feldset; Teil 2: `issues`-Eintrag aus `DOMAIN_FIELDS` (`admin-ui.html:4198-4203`) entfernen + Verweis, Inhalt durch Entscheidung 34 (F-neu-6) festgelegt | entfällt (beide S). Kern-T26 deckt Teil 2 nicht ab (Referenzplan F-4 `:1157`: alte View bleibt unberührt) |
| #1211 | M (verfrüht) | Default-Flip + Löschung `LEGACY_ROLE_BLOCKS`; Pilot-Zyklus fehlt | blockiert, siehe unten (Entscheidung 26) |

Zähler: Phase F = 6 Issues (#1188, #1201, #1202, #1203, #1204, #1211). Summe der Roadmap = 90 (A 11, B 13, C 11, D 8, E 6, F 6, G 7, H 11, I 17; #1141 in D nach #1181, Entscheidung 35; #1187 als E-Block 0, Entscheidung 49).

## PR-Schnitt

Höchstens zwei PRs, ein Commit je Task (Entscheidungen 17 und 52; ersetzt die frühere Aufteilung in F-PR1..4). **F-PR1 (Phasen-PR)** enthält nur die derzeit ausführbaren Tasks; **F-PR2 (Nachfolge-PR derselben Phase)** enthält die spec-gesteuerten bzw. gesperrten Tasks und wird erst nach den Gates (Task 0 Step 2, Task 0b) und auf den gemergten F-PR1 rebased geöffnet. Der Kern (30 Tasks, 8 Meilensteine im Referenzplan) bleibt als Commit-Folge in F-PR1; Meilenstein-Schnitt des Referenzplans gilt für die Commit-Gruppierung.

| PR | Commit-Gruppe (Reihenfolge) | Inhalt | Tasks | Abhängt von |
|---|---|---|---|---|
| F-PR1 | Vorlauf | Kinder-Addendum-Spec (Commit erst nach Freigabe, Step 2 vor Step 3; liegt die Freigabe beim Merge von F-PR1 nicht vor, wandert der Commit in F-PR2) | Task 0 | — |
| F-PR1 | Vorlauf | #1203 Flag-Disambiguierung | Task 1 | E-Block 0 (#1187) drin, nur Ordnung |
| F-PR1 | Kern | #1188 Kern | Referenzplan T1-T30 (Meilenstein-Schnitt dort), Wrapper-Task K | Task 1, Task V, #1186 (E) laut Kette |
| F-PR1 | Kinder | #1204 | Task 4 (Teil 1 nach Task 1 und vor Kern-T26, Teil 2 nach Task K) | s. Task 4 |
| F-PR1 | Querverweis | #1187 | Task V (kein Code) | E-C0 / E-Block 0 (Entscheidung 49) |
| — (Gate, kein Commit) | Gate | Spec-Freigabe Kinder-Addendum; User-Freigabe Referenzplan-Änderung K-7/F-1 | Task 0 Step 2, Task 0b | User |
| F-PR2 | Kinder | #1202 | Task 3 | Task K (T9, T13, T23), Task 0 APPROVED |
| F-PR2 | Kinder | #1201 | Task 2 | Task 3, Task K (T5, T7, T14), Task 0 APPROVED, Task 0b freigegeben |
| (gesperrt, keinem PR zugeordnet) | — | #1211 | kein Task | Pilot-Gate, Entscheidung 26 |

Fallen die Gates vor Abschluss von F-PR1 nicht, bleibt F-PR1 trotzdem mergebar; F-PR2 wartet.

## File Structure

- Modify: `scripts/sync.py` — `--backup-label` + Alias `--label` (`:456-457`), Hilfetext (Task 1).
- Modify: `scripts/lib/cli_commands.py` — `_handle_backup` (`:1060`) liest `args.label` (`:1074`); Warnung bei `--label` ohne `--backup` (Task 1).
- Modify: `docs/api/cli-reference.md` — `--label` (`:209`) -> `--backup-label` (Task 1).
- Modify: `scripts/lib/backup.py` — Usage-Docstring (`:18`) (Task 1).
- Create: `tests/test_sync_cli_flag_disjoint.py` — Parser-Test Task 1.
- Modify: `config/conventions-presets.yaml` — `labels.namespace` in drei Presets (`:56,93,125`) (Task 2).
- Modify: `scripts/lib/conventions.py` — `_render_git_issue_naming` (`:277-292`), Migrationswarnung (Task 2).
- Create: `tests/test_conventions_issue_namespace.py` — Task 2.
- Create/Modify: `scripts/lib/issue_conventions.py` (vom Kern geliefert) — `render_priority_table()` (Task 3).
- Modify: `scripts/lib/consistency/placeholders.py` — `ISSUE_PRIORITY_TABLE` in `_BUILTIN_VARS` (Task 3).
- Modify: `agents/1-generic/meta-feedback.md` (`:48`), `agents/1-generic/bug-feature-analyzer.md` (`:93-97`, `:117`) — Task 3.
- Modify: `scripts/lib/consistency/issue_labels.py` (vom Kern) — Regel `template.duplicate-priority-definition` (Task 3).
- Create: `tests/test_issue_priority_canonical.py` — Task 3.
- Modify: `docs/ui/admin-ui.html` — `DOMAIN_FIELDS.issues` (`:4198-4203`) (Task 4).
- Create: `tests/test_admin_ui_conventions_inert_fields.py` — Task 4.
- Create: `docs/specs/2026-11-11-issue-label-children-spec.md` — Task 0.
- Entfällt (Entscheidung 35): #1141-Dateien (`config/project-config.schema.json`, `tests/test_config_unknown_top_level_keys.py`) liegen im D-Plan `docs/superpowers/plans/2026-11-11-phase-d-guards-hooks.md`. `scripts/lib/config.py` bleibt für Task 4 (`ISSUE_LANGUAGE`, `:2762-2764` in `_build_convention_variables` `:2715`) gelistet.

## Frische-Check vor Ausführung

Roadmap-Zeilenanker stammen von `a41745ed`. Review 2026-11-11 gegen origin/main `9aa0e0c0` (`git show origin/main:<pfad>`): `scripts/sync.py:113` (Def `_normalize_check_dry_run`, Aufruf `:811` in `main()` `:804`), `:217` (`_build_arg_parser`), `:223` (`allow_abbrev=False`), `:451-454` (`--backup` inkl. Hilfetext), `:456-457` (`--label`); `scripts/lib/cli_commands.py:1060` (`_handle_backup`), `:1074` (`label=args.label`); `scripts/lib/config.py:636` (`_validate_config`), `:2715` (`_build_convention_variables`), `:2762-2764` (`ISSUE_LANGUAGE`); `config/conventions-presets.yaml:56,93,125` (`namespace`); `docs/ui/admin-ui.html:4156` (`viewProjectConventionsOverrides`), `:4189-4204` (`DOMAIN_FIELDS`). Bei Ausführung erneut messen (Roadmap Abschnitt 7b, Konfliktpunkt 7).

## Stand des Kerns in W (Teilumsetzung geprüft)

Geglobt in W: `scripts/lib/issue_*.py` und `config/issue-*.yaml` ergeben **keinen** Treffer. `scripts/sync.py` kennt nur `--label` (`:456`), kein `--labels`. `_render_git_issue_naming` rendert weiter `namespace` roh (`scripts/lib/conventions.py:285,290`). `ISSUE_LANGUAGE` ist die einzige Issue-Variable in `config.py:2762`. Ergebnis: Kern ist **nicht** (auch nicht teilweise) umgesetzt; Roadmap-Verdikt "kein Code" stimmt.

---

### Task 0: Spec schreiben + Freigabe-Gate (Kinder-Addendum #1201/#1202)

**Agent:** `requirements` · **Depends on:** — · **Größe:** S
**Files:** Create `docs/specs/2026-11-11-issue-label-children-spec.md`
**Interfaces:** Consumes `docs/specs/2026-11-09-issue-label-taxonomy-spec.md` (Achsen, D2, D15); Produces Spec-ID `SPEC-issue-label-children-2026-11-11`.

- [ ] Step 1: Spec schreibt (a) #1201: GitHub-Projektion = `bug` (Issue-Kriterium, Entscheidung 51; Abweichung vom Referenzplan K-7/F-1, siehe Abweichung 2 und Task 0b), GitLab-Projektion = `type::bug` (scoped label, Entscheidung 57; Namespace-Trenner aus Host-Config-Key, kein Host-Literal im Code), Migrationswarnung für `type: {type}`; (b) #1202: eine kanonische Priority-Definition P0-P3 je Klasse (BUG/FEATURE/USER-ERROR/FINDING), Platzhalter `{{ISSUE_PRIORITY_TABLE}}`, neue Regel `template.duplicate-priority-definition`; (c) entfällt: keine `severity`/`status`-Achse (Entscheidung 34, F-neu-4).
- [ ] Step 2: Review-Gate: `Status: APPROVED` durch User. Ohne Freigabe sind Task 2 und Task 3 **nicht ausführbar**.
- [ ] Step 3: Commit `docs: add spec for label taxonomy children 1201 1202` (F-PR1, falls bis dahin freigegeben, sonst F-PR2).

### Task 0b: Freigabe-Gate Referenzplan-Abweichung #1201 (Entscheidungen 51, 57, kein Code, kein Commit)

**Agent:** `main_chat` (User-Freigabe) · **Depends on:** Task 0 Step 1 · **Größe:** keine
Entscheidung 51 legt die GitHub-Projektion auf `bug` fest, Entscheidung 57 die GitLab-Projektion auf `type::bug` (Wirkung wie 51); der APPROVED Referenzplan `docs/plans/2026-11-09-issue-label-taxonomy-plan.md` (K-7, F-1 `:1154`) nennt `type/…`. Die Abweichung ist in diesem Plan festgehalten (Abweichung 2). Eine Änderung am Referenzplan braucht die **erneute** Freigabe des Users; dieser Plan ändert den Referenzplan nicht und setzt keinen Status auf APPROVED.

- [ ] Step 1: User beide Projektionswerte zur erneuten Freigabe vorlegen: GitHub `bug` (Entscheidung 51, Abweichung K-7/F-1) und GitLab `type::bug` (Entscheidung 57; Referenzplan T2 `:444`, T7 `:513` `test_gitlab_type_uses_double_colon`), jeweils Fundstelle Referenzplan und Wortlaut der Entscheidung.
- [ ] Step 2: Ohne Freigabe bleibt Task 2 (Projektion) gesperrt. Eine Anpassung des Referenzplans erfolgt nur nach dieser Freigabe und nur in dem vom User freigegebenen Umfang.

### Task 1: #1203 Flag-Disambiguierung `--backup-label` (S, vor Kern-T21)

**Agent:** `developer` · **Depends on:** — (muss vor Referenzplan T21 mergen) · **Größe:** S
**Files:** Modify `scripts/sync.py`, `scripts/lib/cli_commands.py`, `docs/api/cli-reference.md`, `scripts/lib/backup.py`; Create `tests/test_sync_cli_flag_disjoint.py`
**Interfaces:** Consumes `_build_arg_parser() -> argparse.ArgumentParser` (`scripts/sync.py:217`), `_handle_backup(ctx: _SyncContext) -> None` (`scripts/lib/cli_commands.py:1060`), `label=args.label` (`:1074`). Produces `--backup-label TEXT` (dest `label`), `--label` als deprecated Alias mit stderr-Warnung. `allow_abbrev=False` bereits gesetzt (`scripts/sync.py:223`).

- [ ] Step 1: Test schreiben (fail), `tests/test_sync_cli_flag_disjoint.py`:
  - `test_no_two_long_options_differ_only_by_trailing_s`: alle `option_strings` aus `_build_arg_parser()._actions` sammeln; Assertion: für jedes Paar `a, b` gilt nicht `a + "s" == b`.
  - `test_backup_label_sets_label`: `_build_arg_parser().parse_args(["--backup", "--backup-label", "x"]).label == "x"`.
  - `test_legacy_label_alias_still_parses`: `parse_args(["--backup", "--label", "x"]).label == "x"`.
  - `test_label_without_backup_warns`: `--label x` ohne `--backup` löst über den Handler/Validator eine Warnung auf stderr aus (capsys, Text enthält `--backup`).
  - `test_label_alias_warns_once_on_stderr`: Warnung enthält `--backup-label`.
- [ ] Step 2: Implementieren: `add_argument("--backup-label", "--label", dest="label", ...)` ist für die Warnung zu wenig; stattdessen eigener `--backup-label` und `--label` mit `dest="legacy_label"`, Normalisierung in einer kleinen Funktion `_normalize_label_flags(args)` analog `_normalize_check_dry_run` (Definition `scripts/sync.py:113`, Aufruf `:811` in `main()` `:804`; `_normalize_label_flags` direkt danach aufrufen). `--help`-Text von `--backup` (`:451-454`, Satz "Use --label ..." `:454`) auf `--backup-label` umstellen. Test-Import wie `tests/test_checkpoint_cli.py:317` (`from sync import _build_arg_parser`, `scripts/` im `sys.path`).
- [ ] Step 3: `docs/api/cli-reference.md:209` und `scripts/lib/backup.py:18` auf `--backup-label` umstellen; `tests/test_cli_smoke_multi_provider.py:101` nutzt `--label` weiter (Alias) und bleibt unverändert grün.
- [ ] Step 4: Verifikation: `python3 -m pytest tests/test_sync_cli_flag_disjoint.py` grün; `python3 -m pytest tests/test_cli_smoke_multi_provider.py` grün; `python3 scripts/sync.py --validate` ohne Fehler.
- [ ] Step 5: Commit `fix: rename sync --label to --backup-label with alias`.

Hinweis zum Referenzplan: T21 Step 2 verlangt "`--label` nicht umbenennen" und der Test `test_help_distinguishes_label_and_labels` bleibt gültig. Nach Task 1 ist die Umbenennung bereits erledigt; der T21-Test prüft nur noch, dass `--labels` ein eigener, eindeutig beschriebener Schalter ist (siehe Abweichung 4).

### Task K: Kern #1188 ausführen (Referenz, kein neuer Inhalt)

**Agent:** `senior-developer` · **Depends on:** Task 1, Task V (#1187-Block von E drin, Entscheidung 49), Phase-E-Kern (#1186) laut Kette (Entscheidung 56) · **Größe:** XL · **PR:** F-PR1
Ausführung nach `docs/plans/2026-11-09-issue-label-taxonomy-plan.md`: T1 bis T30 in der dortigen Reihenfolge und Meilenstein-Schnitt (Abschnitt "Kritische Tasks", `:1177`). Wrapper-Pflichten:

- [ ] Step 1: Vor Start Freshness-Check: Basis des Referenzplans ist `aaed14c2`, Ziel ist aktueller origin/main; Zeilenanker des Referenzplans (z.B. `scripts/lib/config.py:2673-2734`, heute `_build_convention_variables` ab `:2715`; `scripts/sync.py:757-787`, `scripts/admin-server.py:234-259`) neu prüfen.
- [ ] Step 2: `pipeline_stages` des Referenzplans bleibt dort ungebunden; ein Pipeline-Lauf über Phase F nutzt dieses Frontmatter (`implement: 4`) und delegiert an die T-Blöcke.
- [ ] Step 3: Nach T21 und T25: `python3 scripts/sync.py --validate` und `python3 -m pytest tests/test_issue_labels_cli.py tests/test_issue_conventions_golden.py` grün (Namen laut Referenzplan File Structure).
- [ ] Step 4: Beim Kern vermerkte Kinder-Nicht-Ziele einhalten: T14 löst #1201 nicht, T26 ändert die alte Conventions-View nicht (Referenzplan F-1/F-4, `:1154,1157`).
- Acceptance: alle 30 Tasks des Referenzplans abgehakt, `enabled: false` byte-identisch (AC-9, Golden-Test), kein Token in Ausgaben (AC-8).

### #1141 — kein Task in Phase F (verschoben nach Phase D)

Entscheidung 35: #1141 (Schema-Keys, Unbekannt-Key-Warnung) ist letzter Teil des Phase-D-PRs, nach #1181. Vollständiger Task, Dateien und Tests stehen im D-Plan `docs/superpowers/plans/2026-11-11-phase-d-guards-hooks.md`. Dieser Plan führt keinen #1141-Task aus.


### Task V: #1187 Status (Querverweis, kein Code, kein Commit)

**Agent:** wie E-C0 · **Depends on:** E-C0 und E-Block 0 (E-B0-T1, E-B0-T2; Phase E) · **Größe:** keine
Kein eigener Check in Phase F (Entscheidungen 19, 49; keine Duplikation). #1187 ist laut Entscheidung 49 erster Block von Phase E; Block 2 von E und damit Phase F sind entsperrt, sobald dieser Block drin ist. Ergebnis aus E-C0 und Stand von E-Block 0 im PR-Body von F-PR1 (Abschnitt Vorbedingungen) übernehmen.
- [ ] Step 1: Ergebnis E-C0 und Stand E-Block 0 (`docs/superpowers/plans/2026-11-11-phase-e-artifact-locations.md`, Abschnitte "E-C0" und "Block 0") lesen und übernehmen.
- [ ] Step 2: Ist der #1187-Block von E nicht drin, Task K nicht starten.

### Task 3: #1202 Priority kanonisch (M, nach Kern-T9/T13/T23, Spec-Gate Task 0)

**Agent:** `developer` · **Depends on:** Task 0 (APPROVED), Task K (T9, T13, T23) · **Größe:** M · **PR:** F-PR2 (spec-gesteuert, Entscheidung 52)
**Files:** Modify `scripts/lib/issue_conventions.py`, `scripts/lib/consistency/placeholders.py`, `scripts/lib/consistency/issue_labels.py`, `agents/1-generic/meta-feedback.md`, `agents/1-generic/bug-feature-analyzer.md`; Create `tests/test_issue_priority_canonical.py`
**Interfaces:** Produces `render_priority_table(resolved) -> str` (Signatur-Stil der Kern-Renderer aus T9; exakte Signatur nach Kern-T9 gegen den dann existierenden Code lesen, hier **nicht** verifizierbar, siehe Nicht verifiziert), Platzhalter `{{ISSUE_PRIORITY_TABLE}}`, Check-ID `template.duplicate-priority-definition`. Consumes Kern: `priority`-Achse (`priority.values.<P>.description`).

- [ ] Step 1: Tests (fail): `test_priority_table_lists_p0_to_p3`; `test_meta_feedback_has_no_priority_literal` (Template enthält `{{ISSUE_PRIORITY_TABLE}}`, keine Zeile `Severity: P0-P3`; Ist: `meta-feedback.md:48`); `test_bfa_matrix_replaced_by_placeholder` (Ist: Tabelle `bug-feature-analyzer.md:93-97`, Output-Contract `:117`); `test_duplicate_priority_definition_rule_fires` (Template mit lokaler P0-P3-Tabelle + verfügbarem Block => Finding `template.duplicate-priority-definition`); `test_placeholder_registered` (in `_BUILTIN_VARS`); `test_incident_responder_and_template_auditor_untouched` (`incident-responder.md:72,126`, `template-auditor.md:114` bleiben, kein Fund).
- [ ] Step 2: Implementieren. `severity`-/`status`-Achse **nicht** (Entscheidung 34, F-neu-4: nur Priority kanonisch, keine Severity/Status-Achse).
- [ ] Step 3: Verifikation: `python3 -m pytest tests/test_issue_priority_canonical.py tests/test_issue_labels_consistency.py tests/test_issue_conventions_golden.py` grün (Golden unverändert: `enabled:false` byte-identisch, daher Legacy-Pfad via `LEGACY_ROLE_BLOCKS`); `python3 scripts/sync.py --validate`.
- [ ] Step 4: Commit `feat: add canonical issue priority table placeholder`.

### Task 2: #1201 Namespace-Default und Migrationswarnung (M, nach Task 3, Spec-Gate Task 0)

**Agent:** `developer` · **Depends on:** Task 0 (APPROVED), Task 0b (User-Freigabe Referenzplan-Abweichung, beide Werte, Entscheidungen 51, 57), Task 3, Task K (T5, T7, T14) · **Größe:** M · **PR:** F-PR2 (gesperrt bis Task 0b, Entscheidung 52)
**Files:** Modify `config/conventions-presets.yaml`, `scripts/lib/conventions.py`; Create `tests/test_conventions_issue_namespace.py`
**Interfaces:** Consumes `_render_git_issue_naming(spec: dict) -> str` (`scripts/lib/conventions.py:277`), Preset-Schlüssel `issues.labels.namespace` (`config/conventions-presets.yaml:56,93,125`, jeweils `"type: {type}"`), Kern-Projektion (T7). Namespace-Trenner (Entscheidung 57): auf `origin/main 9aa0e0c0` existiert **kein** Config-Key dafür (geprüft: `config/`, `scripts/lib/`); plan-eingeführt durch den Referenzplan: `platform.gitlab.defaults.separator.single: "::"` in `config/issue-conventions-presets.yaml` (T2, Referenzplan `:444`) bzw. `separator.single/multi` je Adapter in `config/issue-adapters.yaml` (T3, `:304`; Objektform K-2 `:147-153`). Task 2 liest den Trenner nur aus diesem Key, kein Host-Literal im Code. Produces: Preset-Default ohne `": "`, Warnung bei Alt-Wert.

- [ ] Step 1: Tests (fail): `test_no_label_name_contains_colon_space` (alle drei Presets, gerenderter Block); `test_github_projection_pinned` und `test_gitlab_projection_pinned` (pro Adapter exakter Soll-String aus der freigegebenen Spec; GitHub = `bug` laut Entscheidung 51, GitLab = `type::bug` laut Entscheidung 57; beide gültig erst nach Task 0b; der GitLab-Test erzeugt `::` über den Separator-Key des Adapters, ein Test `test_projection_has_no_host_literal` prüft per `ast`-String-Konstanten, dass `scripts/lib/conventions.py` weder `"::"` noch einen Host-Namen als String-Literal enthält; Kommentare zählen nicht, z.B. `dod.py::…` in `:66`); `test_legacy_namespace_value_warns_not_silent` (Projekt-Override `type: {type}` => Warnung im Log, Wert wird nicht still übernommen); `test_single_axis_value_documented`.
- [ ] Step 2: Presets (drei Stellen) auf den Spec-Wert; `_render_git_issue_naming` darf das Label nicht mehr als freie Namespace-Prosa rendern, sondern aus dem Resolver, sobald `issue-conventions.enabled: true`. Default-Wert wird geändert (Entscheidung 34, F-neu-5). Bei `enabled: false` ändert sich damit `GIT_ISSUE_NAMING_BLOCK`: Golden-Test bewusst anpassen und die Änderung im Commit-Body/PR benennen. `tests/test_conventions_migration_invariant.py` pinnt den Block nicht (nur Abwesenheit, `:87`) und bleibt laut Referenzplan unverändert (`:364`). Gepinnt ist der Alt-Wert in `tests/fixtures/slimming-golden/git.md:154` (`type: <type>`): Fixture bewusst nachziehen und `python3 -m pytest tests/test_template_slimming_equivalence.py tests/test_ac01_render_identity.py` laufen lassen (Erwartung: grün nach Fixture-Update; welche der beiden Dateien die Fixture vergleicht, im Task messen). Ab Kern-T10 außerdem `tests/test_issue_conventions_golden.py` prüfen.
- [ ] Step 3: Verifikation: `python3 -m pytest tests/test_conventions_issue_namespace.py tests/test_conventions_migration_invariant.py tests/test_conventions_platform_cascade.py tests/test_template_slimming_equivalence.py tests/test_issue_conventions_golden.py` grün (Plan-Erwartung, nicht ausgeführt); `python3 scripts/sync.py --validate`.
- [ ] Step 4: Commit `fix: replace type namespace label default with axis projection`.

### Task 4: #1204 Admin-UI inerte `issues.*`-Felder (S/M, zweistufig)

**Agent:** `developer` · **Depends on:** Teil 1: Task 1 (nur Ordnung); Teil 2: Task K (T26) · **Größe:** S + M
**Files:** Modify `docs/ui/admin-ui.html`; Create `tests/test_admin_ui_conventions_inert_fields.py`
**Interfaces:** Consumes `DOMAIN_FIELDS` (`docs/ui/admin-ui.html:4189`, `issues` in `:4198-4203`: `title_format`, `types`, `labels.namespace`, `closing_keywords`), `viewProjectConventionsOverrides` (`:4156`), `saveProjectSection("conventions", ...)`. Consumer des einzigen wirksamen Feldes: `variables["ISSUE_LANGUAGE"]` aus `issues.language` (`scripts/lib/config.py:2762-2764`). Einziger Renderer-Consumer der vier Felder: `_render_git_issue_naming` (`scripts/lib/conventions.py:277`, aufgerufen `:132`).

- [ ] Step 1 (Teil 1): Tests (fail): `test_issues_domain_fields_include_language` (Eintrag `[["language"], "language", "scalar"]` in `DOMAIN_FIELDS.issues`, Regex/Text-Parse der HTML-Datei); `test_inert_fields_marked_documentation_only` (Hinweistext "documentation only" für die vier Felder); Wert-Test: jedes `DOMAIN_FIELDS`-Feld hat einen Consumer-Eintrag in einer Test-Liste (`ISSUE_LANGUAGE` für `language`, `GIT_ISSUE_NAMING_BLOCK` für die vier anderen), sonst Fehler.
- [ ] Step 2: `DOMAIN_FIELDS.issues` um `language` erweitern, Hinweis-Badge für die vier Felder.
- [ ] Step 3 (Teil 1): Verifikation: `python3 -m pytest tests/test_admin_ui_conventions_inert_fields.py` grün; `python3 scripts/sync.py --validate`. Textparse-Muster wie `tests/test_admin_ui_git_section.py:17` (`read_text` der HTML-Datei).
- [ ] Step 4 (Teil 1): Commit `fix: mark inert issues fields and expose issues.language in UI`.
- [ ] Step 5 (Teil 2, nach Kern-T26): Tests umstellen (fail): `test_issues_domain_fields_include_language` und `test_inert_fields_marked_documentation_only` ersetzen durch `test_overrides_view_has_only_release_domain` (`DOMAIN_FIELDS` enthält nur den Schlüssel `release`) und `test_overrides_view_links_taxonomy_section` (Verweistext auf die Kern-T26-Sektion). Dann `issues`-Domain entfernen (Entscheidung 34, F-neu-6), Verweis einfügen. `language` ist danach nur über die neue Sektion erreichbar.
- [ ] Step 6 (Teil 2): Verifikation wie Step 3; Commit `fix: drop issues domain from conventions overrides view`.

### #1211 — kein Task (gesperrt)

Blockiert durch #1188-Kern **und** Pilot-Kriterium aus Issue (ein Release-Zyklus mit `enabled: true` in einem Pilotprojekt, Issue #1211 Kriterium 1). Beides ist heute nicht erfüllt/prüfbar. Entscheidung 26: Pilot-Gate bleibt, das Issue bleibt blocked. Nur Vorbereitung ohne Code: nach Task K Kommentar im Issue mit Verweis auf Referenzplan K-1/F-5 und die vier ACs. Ausführung (Default-Flip, `LEGACY_ROLE_BLOCKS`-Löschung, Template-Cleanup in **einem** Change) erst nach bestandenem Pilot-Gate.

## Abweichung zur Roadmap

1. Roadmap: "Phase F, 6 Issues, ein PR". Entscheidung 19 hatte #1141 ergänzt (7 Issues); Entscheidung 35 entfernt #1141 wieder (6 Issues). Statt eines PRs höchstens zwei (Entscheidung 52: F-PR1 ausführbare Tasks inkl. Kern als Commit-Folge, F-PR2 Task 3 und Task 2).
2. **Abweichung vom APPROVED Referenzplan (Entscheidung 51).** #1201 Issue-Text: GitHub-Projektion `bug` (flach); Referenzplan K-7 und F-1 (`:1154`): `type/…`. Entscheidung 51 legt GitHub = `bug` fest (Issue-Kriterium), Referenzplan widerspricht. Der Referenzplan wird hier **nicht** geändert; seine Änderung braucht die erneute User-Freigabe (Task 0b). Bis dahin bleibt Task 2 gesperrt. Kein Status wird durch diesen Plan auf APPROVED gesetzt.
3. Roadmap Welle 2 setzte #1141 (Phase C) vor F. Entscheidung 19 hatte #1141 nach F gezogen; Entscheidung 35 setzt #1141 als letzten Teil von Phase D nach #1181 (Konflikt aufgelöst).
4. Roadmap: "#1203 prospektiv, erst nach #1188-Umsetzung". Befund: `--label` existiert heute (`scripts/sync.py:456`), das Issue verlangt Entscheidung "vor oder mit der Einführung" von `--labels` (Issue #1203, Related). Plan zieht #1203 **vor** den Kern.
5. Roadmap/Issue #1204 nennt `docs/ui/admin-ui.html:4157`; Anker real: `viewProjectConventionsOverrides` `:4156`, `DOMAIN_FIELDS` `:4189-4204`. Issue-Anker `:4197-4202` verschoben um +1/+2 (`:4198-4203`).
6. Roadmap: #1201 Anker `conventions-presets.yaml:56,93,125` bestätigt. Issue #1201: `conventions.py:285,290` bestätigt.
7. Roadmap #1211 "verfrüht, blockiert durch #1188" bestätigt, zusätzlich Pilot-Gate (Issue-Text Kriterium 1).
8. Referenzplan `:1313-1316`: "#1201-#1204 werden nicht zugeordnet, solange die Titel nicht abgeglichen sind." Abgleich hier: #1201=F-1, #1202=F-2, #1203=F-3, #1204=F-4, #1211=F-5 (Titel/Beleg stimmen mit den Issue-Dumps überein). Der Referenzplan bleibt unverändert; Zuordnung gilt nur in diesem Wrapper.

## Entscheidungen (beantwortet)

Quelle: Roadmap-Entscheidungen 17-35 und 49-52 (User-Antworten, Roadmap Abschnitt 7b/7c). Die ursprünglichen Ids stehen in Klammern.

- **Entscheidung 17 (F-neu-1): ein Phasen-PR.** Die Aufteilung F-PR1..4 entfällt; ein Branch, ein Commit je Task. Durch Entscheidung 52 ergänzt.
- **Entscheidung 52 (PR-Regel gesperrte/spec-gesteuerte Tasks): max. 2 PRs je Phase.** F-PR1 = derzeit ausführbare Tasks (Task 1, Task K, Task 4 Teil 1+2, Task V; Task 0 nur, wenn die Spec-Freigabe vorliegt, sonst F-PR2); F-PR2 = Nachfolge-PR derselben Phase mit Task 3 und Task 2. Abschnitt "PR-Schnitt" angepasst.
- **Entscheidung 49 (#1187, E U10): erster Block von Phase E.** Phase E = 6 Issues, Roadmap 90. Block 2 von E und damit Phase F sind entsperrt, sobald der #1187-Block drin ist (Task V). Konflikt 8 gelöst. Wiederöffnen von #1187 nur nach User-Freigabe (im E-Plan, nicht hier).
- **Entscheidung 51 (F-offen-1, #1201): GitHub-Projektion = `bug`, nicht `type/bug`.** Abweichung vom APPROVED Referenzplan (K-7, F-1) festgehalten (Abweichung 2). Restschritt: erneute User-Freigabe für die Referenzplan-Änderung (Task 0b); Task 2 bleibt bis dahin gesperrt.
- **Entscheidung 57 (F-offen-2, #1201): GitLab-Projektion = `type::bug`** (scoped label; Trenner über Host-Config-Key, kein Host-Literal im Code). Wirkung wie 51: Referenzplan-Änderung braucht erneute User-Freigabe (Task 0b, deckt beide Werte); Task 2 bleibt bis dahin gesperrt.
- **Entscheidung 56 (F vor E-Kern): F startet NICHT vor dem E-Kern (Kette).** Nur die #1187-Sperre fällt durch 49; Task K bleibt hinter #1186 (E). Abschnitt "Reihenfolge-Kette" angepasst.
- **Entscheidung 19 (F-neu-2, D-neu-2): Kette.** `#1187 -> #1186 (E) -> #1188 (F) -> #1181 (D Strom A) -> #1141`. Die Platzierung von #1141 in F ist durch Entscheidung 35 zurückgenommen.
- **Entscheidung 35 (#1141): Phase D, nach #1181.** #1141 verlässt Phase F (Task 5 entfällt, Querverweis auf den D-Plan). Phase F = 6 Issues (1188, 1201, 1202, 1203, 1204, 1211). Der offene Konflikt "#1141 Platzierung vs. Kette" (früher Punkt 1) ist damit aufgelöst. Der offene Punkt zu `mcp`/`backup` (früher Punkt 3) betrifft nur #1141 und wandert mit dem Task in den D-Plan; er ist in F nicht mehr offen.
- **Entscheidung 19: #1187.** Kein Code-Check in F; Querverweis auf E-C0 (Task V), durch Entscheidung 49 auf E-Block 0 erweitert. Ob #1187 umgesetzt ist, ist nicht geprüft und wird hier nicht vorausgesetzt.
- **Entscheidung 26 (F-neu-3): #1211 Pilot-Gate bleibt, Issue bleibt blocked.** Kein Task, nur Kommentar-Vorbereitung nach Task K.
- **Entscheidung 34 (F-neu-4, #1202): keine `severity`/`status`-Achse.** Nur Priority wird kanonisiert (Task 3).
- **Entscheidung 34 (F-neu-5, #1201): Default-Wert ändern.** Golden-Test wird bewusst angepasst (Task 2).
- **Entscheidung 34 (F-neu-6, #1204 Teil 2): `issues`-Domain aus der Overrides-View entfernen.** Nur `release` bleibt, Verweis auf die neue Sektion (Task 4 Teil 2).
- **Entscheidung 5 (#1141): Unbekannt-Keys warnen, Schema bleibt offen.** Gilt für #1141 im D-Plan (Entscheidung 35), nicht mehr für Phase F.

## Offene Entscheidungen (neu, ungeklaert)

1. ~~**#1201 GitHub-/GitLab-Projektion `bug` vs. `type/bug`.**~~ **Beantwortet durch Entscheidung 51** (GitHub = `bug`). Verbleibender Gate-Schritt: erneute User-Freigabe der Referenzplan-Änderung K-7/F-1 (Task 0b). Task 2 bleibt bis dahin gesperrt (F-PR2).
2. ~~**#1201 GitLab-Projektion.**~~ **Beantwortet durch Entscheidung 57** (GitLab = `type::bug`, Trenner aus Host-Config-Key). Verbleibender Gate-Schritt wie Punkt 1: Task 0b (beide Werte); Task 2 bleibt bis dahin gesperrt (F-PR2).

Ausführbar ohne weitere Entscheidung (F-PR1): Task 0 Step 1 (Spec schreiben; Commit nach Freigabe), Task 1, Task V, Task K (Referenzplan), Task 4 Teil 1 und Teil 2. Gesperrt (F-PR2): Task 3 (Task 0 APPROVED), Task 2 (Task 0 APPROVED + Task 0b).

## Frische-Check-Referenzen

- docs/plans/2026-11-09-issue-label-taxonomy-plan.md
- docs/specs/2026-11-09-issue-label-taxonomy-spec.md
- docs/specs/2026-11-11-issue-label-children-spec.md
- docs/superpowers/plans/2026-11-10-backlog-roadmap.md
- docs/superpowers/plans/2026-11-11-phase-d-guards-hooks.md
- docs/superpowers/plans/2026-11-11-phase-e-artifact-locations.md
- scripts/sync.py
- scripts/lib/cli_commands.py
- scripts/lib/backup.py
- scripts/lib/config.py
- scripts/lib/conventions.py
- scripts/lib/issue_conventions.py
- scripts/lib/issue_adapters.py
- scripts/lib/consistency/placeholders.py
- scripts/lib/consistency/issue_labels.py
- config/conventions-presets.yaml
- config/issue-adapters.yaml
- docs/api/cli-reference.md
- docs/ui/admin-ui.html
- agents/1-generic/meta-feedback.md
- agents/1-generic/bug-feature-analyzer.md
- agents/1-generic/incident-responder.md
- agents/1-generic/template-auditor.md
- tests/test_sync_cli_flag_disjoint.py
- tests/test_conventions_issue_namespace.py
- tests/test_issue_priority_canonical.py
- tests/test_admin_ui_conventions_inert_fields.py
- tests/test_cli_smoke_multi_provider.py
- tests/test_conventions_migration_invariant.py
- tests/test_conventions_platform_cascade.py
- tests/test_contract_labels.py
- tests/test_issue_labels_cli.py
- tests/test_issue_conventions_golden.py
- tests/test_issue_labels_consistency.py
- symbol: _build_arg_parser
- symbol: _handle_backup
- symbol: _render_git_issue_naming
- symbol: _normalize_check_dry_run
- symbol: DOMAIN_FIELDS
- symbol: viewProjectConventionsOverrides
- symbol: ISSUE_LANGUAGE
- symbol: GIT_ISSUE_NAMING_BLOCK
- symbol: ISSUE_PRIORITY_TABLE
- symbol: LEGACY_ROLE_BLOCKS
- symbol: _BUILTIN_VARS
- issue: 1141
- issue: 1181
- issue: 1186
- issue: 1187
- issue: 1188
- issue: 1201
- issue: 1202
- issue: 1203
- issue: 1204
- issue: 1211

## Nicht verifiziert

- Keine Ausführung von Code oder Tests; alle erwarteten Testergebnisse sind Vorhersagen.
- Exakte Signatur von `render_priority_table` und Namen der Kern-Renderer: Kern-Code existiert nicht in W, Task 3 liest sie nach Kern-T9.
- Ob Phase-E-Merge bzw. E-Block 0 (#1187) erfolgt ist: E-Plan liegt in W vor (`2026-11-11-phase-e-artifact-locations.md`), Merge, E-C0-Ergebnis und Block-0-Stand nicht geprüft.
- Graphify-Orientierung (`graphify-out/graph.json`, laut Hook potentiell veraltet) nicht ausgeführt; kein Shell-Zugriff im Lauf, Read/Grep direkt genutzt.
- Ob die Kern-Zeilenanker des Referenzplans (`sync.py:757-787`, `admin-server.py:234-259`, `placeholders.py:114-123`) auf `9aa0e0c0` noch stimmen; `config.py:2673-2734` ist gedriftet (`_build_convention_variables` jetzt `:2715`). Task K Step 1 misst neu.
- Welcher Test `tests/fixtures/slimming-golden/git.md` byte-genau vergleicht (Kandidaten `tests/test_template_slimming_equivalence.py`, `tests/test_ac01_render_identity.py`; Task 2 misst).

## Self-Review

- Jedes der 6 Phase-F-Issues genau einmal: #1188 (Task K), #1203 (Task 1), #1202 (Task 3), #1201 (Task 2), #1204 (Task 4), #1211 (gesperrt, kein Task). #1141 nicht in F, Querverweis auf D-Plan (Entscheidung 35). #1187 nur als Querverweis (Task V, kein Duplikat von E-C0).
- Task-Zahl: Task 0, 0b, 1, 2, 3, 4, K, V (8 Einträge; Task 0b und V ohne Commit; Arbeits-Tasks ohne K, V, 0b: 0-4). Task 4 hat zwei Commits (Teil 1 vor, Teil 2 nach Kern-T26). Kern-Tasks T1-T30 im Referenzplan.
- Spec-Gates: Task 0 (Kinder-Addendum); #1188 per Referenz auf APPROVED Spec.
- PR-Form: max. 2 PRs, ein Commit je Task (Entscheidungen 17, 52): F-PR1 ausführbare Tasks, F-PR2 Task 3 und Task 2.
- Entscheidungen 5, 17, 19, 26, 34 (F-neu-1..6), 35, 49, 51, 52, 56, 57 als "Entscheidungen (beantwortet)" referenziert; Punkt 1 (#1201 GitHub) durch 51, Punkt 2 (GitLab `type::bug`) durch 57 beantwortet (Rest-Gate Task 0b für beide Werte).
- Kein TBD/TODO-Platzhalter; offene Punkte stehen unter "Offene Entscheidungen (neu, ungeklaert)" bzw. "Nicht verifiziert".
- Signaturen mit Evidenz: `_build_arg_parser` (`scripts/sync.py:217`), `_handle_backup` (`scripts/lib/cli_commands.py:1060`), `_render_git_issue_naming` (`scripts/lib/conventions.py:277`), `_validate_config` (`scripts/lib/config.py:636`); `render_priority_table` ist ausdrücklich als nach Kern-T9 zu verifizieren markiert.
- Reihenfolge E -> F-Kern -> D-Strom A (#1181) -> #1141 (D-Plan) benannt; #1141-Konflikt durch Entscheidung 35 aufgelöst.
