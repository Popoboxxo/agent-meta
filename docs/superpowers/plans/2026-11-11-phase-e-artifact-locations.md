---
pipeline_stages:
  implement: 1   # Schritt-Nummer = erster ausfuehrbarer Task (E-T1); Zuordnung zur Pipeline nicht verifiziert
---

# Phase E (Artefaktorte) Wrapper-Plan: #1187 (Block 0) + #1186 Kern + Kinder #1198, #1199, #1200, #1209

> Status: DRAFT
> Datum: 2026-11-11 | Base: `origin/main a3d65da4` (Plan-Stand, Revision 2) → `origin/main 9aa0e0c0` (Revision 3, nach PR #1218) | Branch (Plan): `docs/phase-plans`
> Revision 4: Entscheidungen 49 (#1187 nachziehen, erster Block), 50 (#1198 Scope inkl. `rules/`) und 52 (PR-Schnitt, max. 2 PRs je Phase) eingearbeitet; U8 und U10 beantwortet.
> Revision 3: Entscheidungen 35-38 eingearbeitet. #1209 ist aus dem Phasen-PR abgespalten (Entscheidung 36, eigener PR erst nach APPROVED E-T7, U9 geloest). Kette (Entscheidung 35): #1187 -> #1186 (E) -> #1188 (F) -> #1181 (D Strang A) -> #1141 (D, letzter Teil). Zeilenanker gegen origin/main `9aa0e0c0` (PR #1218) re-gemessen, Abweichungen in "Frische-Check-Referenzen". Revision 2: Entscheidungen 17-34 (Phasen-PR, Kette 19, E-N2/E-N3).
> Roadmap: `docs/superpowers/plans/2026-11-10-backlog-roadmap.md` Phase E (Welle 2, Abschnitte 2, 3, 4, 5, 7 verbindlich)
> Issues: Phase E = 6 Issues (#1187 Block 0, #1186 Kern, #1198, #1199, #1200, #1209; Entscheidung 49, Roadmap-Gesamtzahl 90). Phasen-PR: #1187, #1186, #1198, #1199, #1200. Nachfolge-PR (Entscheidung 52; Ausnahmeliste: #1086i, #1209, Regel 52): #1209 (E-T7 Spec, danach E-T8). #1150 ist DOPPELT von #1186 und gehoert zu Phase A.

**Goal:** Reihenfolge, PR-Schnitt und Abhaengigkeiten fuer Phase E festlegen und die vier Kind-Issues als eigene, kleine TDD-Tasks planen. Der bereits freigegebene Kernplan fuer #1186 wird nicht dupliziert, sondern per Task-ID (T1..T24) referenziert; ebenso der APPROVED Plan fuer #1187 (`docs/plans/2026-11-09-project-context-injection-scope-plan.md`, T1..T15).
**Architecture:** Wrapper-Plan mit einem Phasen-PR fuer #1187, #1186, #1198, #1199, #1200 (Entscheidung 17, ein Commit je Task) und einem Nachfolge-PR fuer #1209 (Entscheidung 36, Regel 52: max. 2 PRs je Phase). Bloecke in dieser Reihenfolge: (0) #1187 nach dem APPROVED #1187-Plan (Entscheidung 49; Kernplan-Voraussetzung 2, `docs/plans/2026-11-09-artifact-locations-matrix-plan.md:51`). (1) #1198 behebt den stillen P1-Fehler unabhaengig vom Kern. (2) Kern #1186 laeuft unveraendert nach dem APPROVED Plan. (3) #1199 und #1200 als Nach-Block. (4) #1209 braucht eine freigegebene Spec (Klasse M); Block 4 ist der Nachfolge-PR (Regel 52), erst nach APPROVED E-T7 und rebased auf den gemergten Phasen-PR. Der Phasen-PR wartet nicht auf #1209. Kette und Gate: E-C0 (Entscheidung 19, 35), Block 0 entsperrt Block 2 und damit Phase F (Entscheidung 49).
**Tech Stack:** Python 3.9+ (stdlib, PyYAML-Ausnahme), pytest, Markdown, JSON Schema draft-07.
**Spec:** Kern #1186: `docs/specs/2026-11-09-artifact-locations-matrix-spec.md` (`Status: APPROVED`, 2026-11-09). #1187: `docs/specs/2026-11-09-project-context-injection-scope-spec.md` (APPROVED, Revision 4) + APPROVED Plan. #1198, #1199, #1200: S-Klasse, keine Spec noetig. #1209: keine, siehe Task E-T7 (Spec-Gate, Nachfolge-PR laut Entscheidung 36/52).
**Kernplan (APPROVED, nicht duplizieren):** `docs/plans/2026-11-09-artifact-locations-matrix-plan.md` (Revision 4, 24 Tasks T1..T24, T22 = Follow-up).

## Klassifikation (Spec/Plan-Gate)

| Issue | Klasse | Begruendung | Gate |
|---|---|---|---|
| #1187 | L | APPROVED Plan (Klasse L laut Plan-Kopf), 15 Tasks T1..T15, 4 Meilensteine; Szenarien 95-98 | APPROVED Spec + APPROVED Plan vorhanden; Issue-Wiederoeffnung nur nach User-Freigabe (Entscheidung 49) |
| #1186 | XL | Kernplan Klasse XL, 23 Tasks im PR | APPROVED Spec + APPROVED Plan vorhanden |
| #1198 | S | 18 Textstellen in 12 Templates + 1 Check ueber `agents/`, `commands/`, `rules/` (Entscheidung 50) | direkt |
| #1199 | S | eine Datei + ein Test, kein Verhaltenswechsel | direkt |
| #1200 | S | Doku-Tabelle + 1 Test | direkt |
| #1209 | M | neue Variablen-Familie + Renderer-Whitelist + 26 Templates, Vertragswechsel gegen Kern-AC-05 | Task E-T7: Spec zuerst |

## Befund: Kern #1186 in W teilweise implementiert?

Nein. Verifiziert in W:
- `Glob **/*artifact*` findet keinen `scripts/lib/artifact_locations.py`, `artifact_scaffold.py`, `artifact_status.py`, `artifact_migration.py`, keine `config/artifact-locations-presets.yaml`, keinen `hooks/1-generic/artifact-path-guard.sh`, keine `tests/test_artifact_locations_*`. Vorhanden sind nur unabhaengige Altdateien (`scripts/lib/artifact_validate.py`, `scripts/lib/consistency/artifact_contracts.py`, `hooks/1-generic/release-gates/artifact-freshness.sh`).
- `Grep ARTIFACT_|artifact-locations|artifact_locations` in `scripts/ config/ agents/` trifft nur `ARTIFACT_ZIP_CMD`/`ARTIFACT_TAR_CMD` (`scripts/lib/consistency/placeholders.py:59`, `config/project-config.schema.json:335,338`, `agents/2-platform/sharkord-release.md`). Kein Kern-Code.
- `tests/scenarios/configs/` endet bei `93-...`; die vom Kern reservierte ID 99 und die von #1181/#1187 reservierten 94-98 fehlen. 95-98 legt Block 0 an (E-B0-T2).
- `PROJECT_WRITABLE_SECTIONS` (`scripts/admin-server.py:234`) hat noch keinen `artifact-locations`-Eintrag; `se_output` ist im Schema nicht deklariert.

Folgerung: Der Kernplan gilt vollstaendig ab T1.

## Global Constraints

- Python 3.9 kompatibel (kein `X | Y` zur Laufzeit ohne `from __future__ import annotations`, kein `match`).
- Nur stdlib + PyYAML. Keine neue Abhaengigkeit.
- Provider-agnostisch: Unterschiede nur ueber Config-Keys/Capability-Flags, nie `if provider == "Name"`.
- Commits Englisch, Conventional Commits, Betreff <= 72 Zeichen, imperativ. Ein Commit pro Task. Commit-/PR-Body wird spaeter als Datei geschrieben. Trailer woertlich wie vom Task-Prompt vorgegeben (Entscheidung 25).
- Kein `isolation: "worktree"` beim Spawnen von Subagenten. Feature-Branches (`fix/`, `feat/`, `chore/`), nie `main`.
- Tests: `python3 -m pytest <file>::<test>`; Gesamtpruefung `python3 scripts/sync.py --validate` und `python3 scripts/consistency-check.py`.
- PR-Schnitt (Entscheidung 17, praezisiert durch 52): Phasen-PR enthaelt nur die zum PR-Zeitpunkt ausfuehrbaren Tasks (Block 0-3); gesperrte/spec-gesteuerte Tasks (Block 4, #1209) laufen in genau einem Nachfolge-PR der Phase E (max. 2 PRs). Commits sequentiell: kein Parallel-Edit derselben Datei zwischen Tasks (Kernplan Voraussetzung 8: `config/project-config.schema.json`, `scripts/admin-server.py`, `docs/ui/admin-ui.html`, `scripts/lib/consistency/placeholders.py`, `agents/1-generic/*.md`).
- Zeilenanker veralten: vor jeder Ausfuehrung `check_plan_refs.py` gegen origin/main (Skript liegt nicht in origin/main, sondern auf Branch `chore/check-plan-refs`, Review 2026-11-11; siehe E-T0). Nackte `:NNNN`-Anker prueft das Skript nicht, sie werden von Hand geprueft. origin/main steht auf `9aa0e0c0` (PR #1218): nach Rebase alle Anker neu verifizieren.
- Aufwand: Schaetzung liefert `effort-estimator` (Textverweis, hier keine Zahlen).

## Reihenfolge, PR-Schnitt, Abhaengigkeiten

| PR | Branch (Vorschlag) | Inhalt | Tasks | Haengt ab von |
|---|---|---|---|---|
| E-Phasen-PR (Entscheidung 17/52, ohne #1209) | `feat/phase-e-artifact-locations` (Vorschlag) | Block 0: #1187 (E-B0-T1, E-B0-T2; #1187-Plan T1..T15). Block 1: #1198 (E-T1, E-T2). Block 2: Kern #1186 (Kernplan T1..T21, T23, T24 + E-T3). Block 3: #1199 (E-T4), #1200 (E-T5, E-T6). Ein Commit je Task. Mergebar ohne #1209 (U9 geloest, Entscheidung 36) | E-C0, E-T0, E-B0-T1, E-B0-T2, E-T1 bis E-T6 | A (CI gruen); Phase-C-PR gemergt (ein PR, Entscheidung 36; enthaelt #1189 und #1195; #1086i nicht noetig, Kern beruehrt `context.py` nicht laut Kernplan Abschnitt 2); E-C0 misst #1187-Stand nach; Block 2 erst nach Block 0 (Entscheidung 49) |
| E-2 (#1209, Nachfolge-PR, Entscheidung 36/52) | `feat/artifact-mode-template-gating` (Vorschlag) | Block 4: E-T7 (Spec) wird vor Eroeffnung des PR freigegeben (`Status: APPROVED`). Erst danach eroeffnet der PR mit E-T8 (Umsetzung). Rebase auf den gemergten E-Phasen-PR | E-T7 (Gate), E-T8 | APPROVED E-T7; E-Phasen-PR gemergt |

Begruendung der Reihenfolge (Commit- und Block-Reihenfolge innerhalb des einen Phasen-PR, Entscheidung 17):
- #1187 (Block 0) zuerst (Entscheidung 49): APPROVED Kernplan #1186 nennt #1187 als Voraussetzung 2 (`docs/plans/2026-11-09-artifact-locations-matrix-plan.md:51`, gleiche Templates/`config.py`/Schema). Block 1 (#1198) ist davon unabhaengig und darf vor oder nach Block 0 laufen; Block 2 (Kern) und damit Phase F starten erst nach Block 0.
- #1198 vor dem Kern (erste Commits): Prioritaet P1, kleiner Fix, stiller Fehler in jeder aktiven SE-Kaskade. Der Kern-Task T11 (Deps T6, Groesse L) wuerde den Fehler sonst erst spaet beheben. Der erste Commit macht aus `{SE_BASE_DIR}` `{{SE_BASE_DIR}}`; T11 ersetzt danach `{{SE_BASE_DIR}}` durch `{{ARTIFACT_SE_*_DIR}}`. Die Dateilisten (12 SE-Templates, `placeholders.py`) kollidieren mit dem Kern nur sequentiell, nicht parallel.
- #1199 nach dem Kern: Kern T17 fuegt `artifact-locations` in `PROJECT_WRITABLE_SECTIONS` ein und T18 aendert `scripts/admin-server.py` erneut. Der Kernplan verbietet Parallel-Edits an dieser Datei.
- #1200 nach dem Kern: Die Tabelle muss gegen die Framework-Listen `legacy[]`/`unmanaged[]` des Resolvers (Kern T2, T4) pruefbar sein; AC 2 ("0 `missing-dir`") braucht Kern T14.
- #1209 zuletzt: Es aendert den Kern-Vertrag (Kern-AC-05 "kein Template-Gate", Spec Zeile 1111) und braucht eine freigegebene Spec.
- Roadmap Welle 2 sagt "E parallel zu C, falls Dateiliste disjunkt" (Roadmap Abschnitt 3, Regel "Parallel nur bei disjunkter `Files:`-Liste"). Die Bedingung ist nicht erfuellt: Der Kern aendert `scripts/lib/sync_pipeline.py`, `scripts/lib/config.py`, `scripts/lib/cli_commands.py`, `scripts/admin-server.py`, die auch Phase C beruehrt (#1189 `admin-server.py`, #1195 `sync_pipeline.py`, Plan C Files `:69`, Task 14). Nach der Roadmap-Regel selbst laeuft E daher sequentiell nach dem C-PR; Plan C (`2026-11-11-phase-c-sync-config.md:7`) sagt ebenso "C vor E". Das ist keine Abweichung von der Roadmap und folgt nicht aus Entscheidungen 17/19.
- Phasen-Kette (Entscheidungen 19, 35): #1187 -> #1186 (E) -> #1188 (F) -> #1181 (D Strang A) -> #1141 (D, letzter Teil). Phase E kommt vor Phase F. #1141 ist nicht Teil von E und nicht mehr Teil von F (F-Plan Task 5 entfaellt, Verweis auf D).
- #1209 ist abgespalten (Entscheidung 36, Antwort auf U9): Nachfolge-PR nur nach `Status: APPROVED` von E-T7. Der Phasen-PR (#1187, #1186, #1198, #1199, #1200) ist ohne #1209 mergebar. Entscheidung 52 begrenzt Phase E auf diese 2 PRs.

## File Structure

Dieser Wrapper-Plan beschreibt nur die Dateien der Kind-Issues. Dateien des Kerns: siehe Kernplan Abschnitt 2.

| Datei | Aktion | Zweck | Task |
|---|---|---|---|
| `agents/1-generic/se-requirements.md`, `se-architect.md`, `se-interface-mgr.md`, `se-developer.md`, `se-senior-developer.md`, `se-junior-developer.md`, `se-integration-and-test-manager.md`, `se-validator.md`, `se-verifier.md`, `se-termination.md`, `se-critic.md`, `se-component-requirements.md` | Modify | 18 Vorkommen `{SE_BASE_DIR}` zu `{{SE_BASE_DIR}}`, `version:` anheben | E-T1 |
| `tests/test_se_single_brace_placeholders.py` | Create | Golden-Test Templates + Check-Tests | E-T1, E-T2 |
| `scripts/lib/consistency/placeholders.py` | Modify | neue Funktion `check_single_brace_placeholders` | E-T2 |
| `scripts/consistency-check.py` | Modify | Import (`:62`) + Aufruf in Agent-Schleife (`:215`) und Command-Schleife (`:222`); neue Funktion `collect_rule_files` neben `collect_command_files` (`:155`) und Regel-Schleife (Entscheidung 50) | E-T2 |
| `tests/fixtures/single_brace_rules/` | Create | Fixture-Regeln: Beispielcode mit `{N}`/`{FolderName}` (kein Alarm) und `{SE_BASE_DIR}` im Fence (Alarm) | E-T2 |
| `tests/scenarios/configs/95-*.project.yaml` bis `98-*.project.yaml`, `tests/scenarios/registry.md` | Create/Modify | #1187-Szenarien 95-98 (Entscheidung 49) | E-B0-T2 |
| #1187-Dateien | siehe #1187-Plan Abschnitt 2 (`docs/plans/2026-11-09-project-context-injection-scope-plan.md:31`) | Block 0 | E-B0-T1 |
| `scripts/admin-server.py` | Modify | `_RUNTIME_ONLY_SECTIONS` mit Begruendungen neben `PROJECT_WRITABLE_SECTIONS` (`:234`) | E-T4 |
| `tests/test_admin_whitelist_drift.py` | Create | Drift-Test in beide Richtungen + PUT-Rundreise | E-T4 |
| `tests/test_admin_server.py` | Modify | Kern-Test `test_no_derivation_in_this_task` (aus Kern T17) entfernen | E-T4 |
| `docs/concepts/artifact-subtree-classification.md` | Create | Entscheidungstabelle (8 Unterbaeume + 4 Audit-Dateien) | E-T5 |
| `tests/test_artifact_subtree_classification.py` | Create | Tabelle vollstaendig + gegen Matrix pruefbar | E-T5, E-T6 |
| `docs/specs/2026-11-12-artifact-mode-template-gating-spec.md` | Create | Spec fuer #1209 (Datumsteil beim Schreiben anpassen) | E-T7 |

---

## Abweichung zur Roadmap und zum Kernplan (verifiziert in W)

1. **#1198: 18 statt 16 Stellen.** Kernplan (T11 Impl "16x", Test-Text "heute 16 Vorkommen", F-1) und Spec (`docs/specs/2026-11-09-artifact-locations-matrix-spec.md:102`, F-1 `:1167`; die Issue-Angabe `:94` ist veraltet) sagen 16. In W gezaehlt (Review 2026-11-11 per `grep -o` gegen origin/main bestaetigt: 22 Treffer `{SE_BASE_DIR}` inkl. 4 in `{{...}}`, also 18 einfach): 18 Vorkommen in 12 Dateien (`se-architect.md` 52, 62, 114, 117; `se-requirements.md` 43, 184; `se-critic.md` 56, 110, 114; je eines in `se-integration-and-test-manager.md:263`, `se-interface-mgr.md:153`, `se-developer.md:188`, `se-component-requirements.md:159`, `se-validator.md:177`, `se-senior-developer.md:144`, `se-termination.md:154`, `se-junior-developer.md:171`, `se-verifier.md:191`). Die Issue-Tabelle stimmt. Vier weitere Stellen nutzen schon `{{SE_BASE_DIR}}` (`se-component-requirements.md:61,142,281`, `se-requirements.md:83`).
2. **#1198: Sonderfall `se-component-requirements.md:159`.** Die Stelle steht in einem JSON-Beispiel (`"ctx": "COMP-Tabelle: {SE_BASE_DIR}/..."`), keine Schreibposition. Sie wird trotzdem ersetzt (sync substituiert auch in Beispielen).
3. **#1198: Check darf Code-Zaeune nicht ausblenden.** `check_placeholders` entfernt Frontmatter (`placeholders.py:204`), Fences und Inline-Code (`:207`, `:209`; Stand 9aa0e0c0), weil sync dort aber auch substituiert, muss der neue Check den ganzen Text scannen.
4. **#1198: Gleiche Form, anderer Zweck.** Grosse Einfach-Klammern wie `-{NNN}` (`se-architect.md:47,48`, `se-requirements.md:37,38`, `se-component-requirements.md:71`) und `${TIMEOUT}` (`developer.md:166`) sind legitim. Der Check meldet daher nur Namen, die in `_BUILTIN_VARS`/Projekt-Variablen stehen (heute: `{SE_BASE_DIR}`).
5. **#1198: `rules/` und `commands/`.** Issue nennt `agents/`, `rules/`, `commands/`. Regeln werden in `consistency-check.py` nicht per Datei gescannt (nur `agent_files`/`cmd_files`); ein Grep ueber `rules/` zeigt keine Einfach-Klammer-Treffer fuer `SE_BASE_DIR` (nur `{{SE_BASE_DIR}}`). Entscheidung 50 (weicht von Empfehlung ab): Der Check deckt `agents/`, `commands/` UND `rules/` ab. Messung Review 2026-11-11 (Regex aus E-T2 gegen `_BUILTIN_VARS | load_project_vars`): heute Treffer nur in den 12 SE-Templates, `rules/` 49 `.md`, 0 Treffer. Regeln enthalten Beispielcode mit Einfach-Klammern unbekannter Namen (`rules/1-generic/se-cascade-artifact-taxonomy.md:40`, `:55`, `:83`: `L{N}_{FolderName}_...`); der Namensfilter (nur bekannte Variablen) verhindert Fehlalarm, eine Fixture belegt das (E-T2).
6. **#1199: Issue-Vorschlag "Ableitung" ist nicht verhaltensneutral.** Das Schema hat 70 Wurzel-`properties`-Treffer (inkl. `_comment`, `agent-meta-version`, `variables`, `memory`, `release-gates` usw.); die Whitelist hat 47 Eintraege, davon 39 im Schema und 8 ohne Schema-Pendant (nachgerechnet: `agent-prompts`, `steps-overrides`, `rules`, `rules-preset`, `environments`, `skills-registry`, `backup`, `submodule-protection`). Eine Ableitung `schema-properties | runtime-only` macht mindestens 31 weitere Wurzel-Sektionen schreibbar, darunter `variables`. Der bestehende Test `tests/test_admin_server.py:2166-2168` (`test_variables_stays_unwritable`) verlangt das Gegenteil, und Issue-AC 1 verlangt "exakt die heutigen 47". Der Plan setzt daher auf Drift-Test statt Ableitung (E-T4). Die 8 Eintraege stimmen mit dem Issue (nicht mit Spec/Kernplan: dort 7, ohne `rules-preset`).
7. **#1199: Kern-T22 wird ersetzt.** Kern-T22 (Ableitung, nach #1141, 7 Eintraege) entfaellt zugunsten E-T4; E-T4 braucht #1141 nicht. Kern-T17 enthaelt `test_no_derivation_in_this_task`, das `_RUNTIME_ONLY_SECTIONS` als nicht existierend prueft; E-T4 entfernt diesen Test. Ob die APPROVED-Dokumente (Spec AC-1186-07, Kernplan T22) angefasst werden, ist entschieden: nur Vermerk im Wrapper-Plan und im PR (Entscheidung 34, E-N3).
8. **#1200: Issue-Vorschlag weicht vom freigegebenen Kern ab.** Issue schlaegt `issues` als `legacy[]` vor. Der freigegebene Kern (Plan Abschnitt 3.2a, D-8) deklariert `docs/issues/**` zusammen mit `api`, `howto`, `guides`, `testing`, `providers`, `se-cascade` als `unmanaged[]` und `docs/superpowers/{specs,plans}` sowie `docs/plans/audit-*.md` als `legacy[]`. Die Tabelle folgt dem Kern. Der Vorbehalt zu `se-cascade` ("oder eigene Klasse") ist damit entschieden.
9. **#1209: Modus-Wert `file` vs. `files`.** Issue sagt `inline|file|off`. Kern-Schema/Resolver nutzen `files|inline|off` (Plan T1 `test_mode_enum_rejects_unknown_value`). Gate-Namen im Issue (`_MODE_FILE`) sind davon unabhaengig. **Entschieden (Entscheidung 56, E U2):** Wert `files` bleibt, Flag `_MODE_FILES`, Issue-Text wird angepasst.
10. **#1209: Namenskollision.** Eine Whitelist mit blossem Praefix `ARTIFACT_*` (Issue-Vorschlag Punkt 2) wuerde die bestehenden Projekt-Variablen `ARTIFACT_ZIP_CMD`/`ARTIFACT_TAR_CMD` miterfassen (`placeholders.py:59`). **Entschieden (Entscheidung 56, E U3):** Suffix-Match auf `_MODE_FILES`/`_MODE_INLINE`.
11. **#1209: Kern-Pins.** Der Kern pinnt exakt 54 `ARTIFACT_*`-Namen (Plan Abschnitt 3.3; T6 `tests/test_artifact_locations_variables.py` `test_artifact_variable_count_is_54`, Kernplan `:593`; T7 `tests/test_artifact_locations_placeholders.py` `test_all_54_artifact_names_registered`, Kernplan `:623`). Neue Gate-Variablen brechen beide Pins; E-T8 muss sie mitfuehren.
12. **#1187 nachgezogen (Entscheidung 49).** #1187 war nicht in den 89 Roadmap-Issues, ist aber Kern-Voraussetzung (`#1187 -> #1186`). Vormessung E-C0: nur Docs-PR #1212, `PROJECT_CONTEXT_INJECTED` und Szenarien 95-98 fehlen auf origin/main. Phase E = 6 Issues, Roadmap 90. Umsetzung als Block 0 (E-B0-T1, E-B0-T2). Konflikt 8 geloest.
13. **Roadmap-Zuordnung #1189.** Roadmap legt #1189 in Phase C. Kern-M5 (T17-T19) braucht es. Das ist konsistent, wenn C vor Block 2 laeuft (siehe Reihenfolge).

---

## Tasks

### E-C0: CHECK-TASK #1187 Implementierungsstand (kein Code, kein Commit)

**Rolle:** `explorer` (nur lesen)
**Files:** keine Aenderung.
**Zweck (Entscheidung 19, 49):** #1187 ist Kern-Voraussetzung (Kette #1187 -> #1186) und laut Entscheidung 49 erster Block von Phase E. E-C0 misst am Ausfuehrungstag nach, ob Block 0 noch voll noetig ist; die Vormessung unten ist die Planungsgrundlage. Nicht raten.
**Pruefquellen (alle drei):**
- Issue-/PR-Dump in W: `.tmp/issues` oder `.tmp/prs` (Status, PR-Nummer, Merge-Commit von #1187).
- Code in W: Artefakt-Funktionen, die der Issue-Text #1187 nennt (Namen aus dem Issue uebernehmen, nicht ableiten), per Glob/Grep suchen.
- Szenarien: `tests/scenarios/configs/` auf IDs 95-98 pruefen (von #1187 reserviert; `94` gehoert #1181, das laut Kette erst nach E laeuft; Beleg `docs/plans/2026-11-09-commit-authority-grant-plan.md:259`).

**Vormessung (Review 2026-11-11, read-only, am Ausfuehrungstag wiederholen):** #1187 ist CLOSED (2026-11-09T21:55:41Z, stateReason COMPLETED, ohne Kommentar), automatisch geschlossen durch den Docs-PR #1212 (gemergt 2026-11-09T21:55:40Z, `closingIssuesReferences` = [1187], Body: "Keine Code-, Config- oder Template-Aenderung"). `git grep PROJECT_CONTEXT_INJECTED origin/main -- scripts agents`: 0 Treffer; `tests/scenarios/configs/` endet bei `93`. Damit trifft Zeile 2 der Matrix zu; Konsequenz laut Entscheidung 49: Block 0 ausfuehren.

**Querbezug Plan B (Ratchet):** Plan B Task 8 legt `tests/test_project_context_placeholder_ratchet.py` mit `_KNOWN_DUPLICATES = {"ui-ux-designer.md": 3, "bug-feature-analyzer.md": 2, "knowledge-curator.md": 2, "knowledge-migrator.md": 2}` an (`2026-11-11-phase-b-small-bugs.md:438-443`); die zweite Assertion (`:450`) wird rot, sobald eine Zahl sinkt. Wird #1187 nachgezogen, gilt fuer #1187-T9 (`docs/plans/2026-11-09-project-context-injection-scope-plan.md:368-385`): T9 umschliesst die fuenf Prosa-Stellen mit `{{#if PROJECT_CONTEXT_INJECTED}}`{{PROJECT_CONTEXT}}`{{else}}...{{/if}}`, der Token `{{PROJECT_CONTEXT}}` bleibt also stehen; `str.count` bleibt 3/2/2/2, der Ratchet bleibt gruen und muss in T9 NICHT gesenkt werden. Pflicht im T9-Commit: `python3 -m pytest tests/test_project_context_placeholder_ratchet.py` mitlaufen lassen (Erwartung passed, Planwert). Die Aussage in Plan B Task 8 ("T9 muss `_KNOWN_DUPLICATES` senken") passt nicht zu T9 (Befund an Plan B gemeldet). Phase E selbst aendert `{{PROJECT_CONTEXT}}` nicht.

**Ergebnis-Matrix (genau eine Zeile trifft zu):**

| Befund | Konsequenz |
|---|---|
| Issue geschlossen, Implementierungs-PR gemergt, Code und Szenarien 95-98 vorhanden | PR-Nummer, Merge-Commit und Datei:Zeile im Phasen-PR-Body belegen. Block 0 entfaellt; Block 2 freigegeben, sofern E-T0 gruen ist. |
| Issue geschlossen, kein gemergter Implementierungs-PR (z. B. nur Docs-PR #1212), Code oder Szenarien fehlen | Entscheidung 49: Block 0 ausfuehren (E-B0-T1, E-B0-T2). Wiederoeffnen von #1187 nur nach User-Freigabe (E-B0-T1 Step 1). Block 2 erst nach Block 0. |
| Issue offen (z. B. nach User-Freigabe wieder geoeffnet) | Block 0 ausfuehren; Block 2 erst nach Block 0. Block 1 (#1198) darf laufen. |
| Widerspruechlich oder nicht ermittelbar (z. B. Dump fehlt) | Stopp. Eine Frage an `main_chat` in einem Satz. Nicht raten. |

**Akzeptanz:** Eine Zeile der Matrix ist mit Belegen dokumentiert (Dump-Pfad, Datei:Zeile, Szenario-IDs) im Phasen-PR-Body.

---

### E-T0: Vorbedingungen und Freshness (kein Code, kein Commit)

**Rolle:** `explorer` (nur lesen)
**Files:** keine Aenderung.
**Interfaces:** Consumes: GitHub-Issue-Stand #1187 (ueber E-C0), #1189; `check_plan_refs.py` (falls vorhanden). #1141 (Phase D, Entscheidung 35) und #1188 (Phase F) sind nicht Teil von E.
- [ ] Step 1: Status von #1189 pruefen und das Ergebnis aus E-C0 uebernehmen. Ist #1187 nicht erfuellt: Block 0 ausfuehren, Block 2 erst danach (Entscheidung 49).
- [ ] Step 2: `check_plan_refs.py` liegt nicht in origin/main `9aa0e0c0`, sondern auf Branch `chore/check-plan-refs` (Review 2026-11-11). Ist es bis dahin gemergt: `python3 scripts/check_plan_refs.py --plans docs/superpowers/plans/2026-11-11-phase-e-artifact-locations.md --repo . --ref origin/main`; sonst aus dem Branch-Checkout aufrufen. Erwartung: 0 ERROR; WARN nur fuer neu geplante Dateien/Symbole (Review-Lauf: 0 ERROR, 64 WARN).
- [ ] Step 3: Alle Zeilenanker aus "Frische-Check-Referenzen" gegen origin/main `9aa0e0c0` (PR #1218) neu verifizieren. Der Stand a3d65da4 gilt nicht mehr.

**Akzeptanz:** Liste "Status #1187 (E-C0) / #1189 / Skript vorhanden / Anker aktuell" liegt im Phasen-PR-Body (Abschnitt Vorbedingungen) vor.

---

### Block 0 (Phasen-PR): #1187 nachziehen (Entscheidung 49)

### E-B0-T1: #1187-Plan ausfuehren (kein neuer Code im Wrapper)

**Rolle:** Orchestrator waehlt je Task die im #1187-Plan genannte Rolle.
**Files/Interfaces:** siehe #1187-Plan Abschnitt 2 und 5 (`docs/plans/2026-11-09-project-context-injection-scope-plan.md:31`, `:484`), nicht dupliziert. Spec `docs/specs/2026-11-09-project-context-injection-scope-spec.md` (APPROVED).
- [ ] Step 1: User-Freigabe zum Wiederoeffnen von #1187 einholen (Entscheidung 49: nicht eigenmaechtig). Ohne Freigabe Block 0 nicht starten; Block 1 darf laufen.
- [ ] Step 2: Freshness: Anker des #1187-Plans gegen den aktuellen origin/main pruefen (Plan-Basis `aaed14c2`); Abweichungen als Aenderungsnotiz im #1187-Plan, nicht neu planen.
- [ ] Step 3: #1187-Plan T1..T15 in Meilensteinen M1..M4 ausfuehren (`docs/plans/2026-11-09-project-context-injection-scope-plan.md:83`, `:91`, `:99`, `:106`), Gates je Meilenstein wie dort. Ein Commit je Task, im Phasen-PR. Pflicht im T9-Commit: `python3 -m pytest tests/test_project_context_placeholder_ratchet.py` (siehe Querbezug Plan B in E-C0).
- [ ] Step 4: Nachweis `git grep PROJECT_CONTEXT_INJECTED -- scripts agents` > 0 Treffer.

**Akzeptanz:** Gates M1..M4 des #1187-Plans gruen; `python3 scripts/sync.py --validate` rc 0; Ausfuehrungsnachweis am Ende des #1187-Plans (T15).

### E-B0-T2: #1187-Szenarien 95-98 registrieren

**Rolle:** `tester`
**Files:** Create `tests/scenarios/configs/95-project-context-mode-all.project.yaml`, `96-project-context-core-orchestrator.project.yaml`, `97-project-context-core-whitelist.project.yaml`, `98-project-context-core.project.yaml`; Modify `tests/scenarios/registry.md` (4 Zeilen). Asserts nach dem vorhandenen Muster in `tests/scenarios/asserts/`.
**Delta zum #1187-Plan:** Der Plan legt das Szenario nur als Scratch in `.tmp/` an und registriert nichts, reserviert aber `95`-`98` fuer den Fall der Registrierung (`docs/plans/2026-11-09-project-context-injection-scope-plan.md:70`, `:477`, `:571`). Entscheidung 49 verlangt die Szenarien 95-98, also wird dieser Fallback gezogen. Zuordnung (Wrapper-Vorschlag, je ein Modus aus `docs/plans/2026-11-09-project-context-injection-scope-plan.md:486-497`): 95 = `mode: all` (Lauf B, byte-identisch zu ohne Sektion), 96 = `core+orchestrator` (Lauf E), 97 = `core+whitelist` (Lauf D), 98 = `core` (Lauf C).
- [ ] Step 1: Configs und Registry-Zeilen anlegen; Assertions je Lauf aus T15 (`docs/plans/2026-11-09-project-context-injection-scope-plan.md:463-479`) uebernehmen.
- [ ] Step 2: `bash tests/scenarios/run.sh` fuer 95-98 gruen (Aufruf-Muster aus `tests/scenarios/run.sh` nachlesen); `python3 scripts/sync.py --validate` rc 0.
- [ ] Step 3: Commit: `test: register project context injection scenarios 95-98`

**Akzeptanz:** `tests/scenarios/configs/` enthaelt 95-98; Registry fuehrt sie mit Verweis auf #1187; `94` (#1181) und `99` (#1186) bleiben frei.

---

### Block 1 (Phasen-PR): #1198

### E-T1: SE-Templates auf `{{SE_BASE_DIR}}` umstellen (#1198, Klasse S)

**Rolle:** `developer`
**Files:** Modify die 12 SE-Templates (siehe File Structure); Create `tests/test_se_single_brace_placeholders.py`.
**Interfaces:** Consumes: `scripts/lib/variables.py:136` (Anker 108 veraltet, Frische-Check) `_VAR_PATTERN = re.compile(r"\{\{([A-Z0-9_]+)\}\}")`; `scripts/lib/config.py:2315` (re-gemessen, war :2273; `SE_BASE_DIR` wird immer gesetzt, Default `"SE"`). Produces: keine Einfach-Klammer-Tokens in `agents/1-generic/se-*.md`.

- [ ] Step 1: Test schreiben (rot). Datei `tests/test_se_single_brace_placeholders.py`, Kopf wie `tests/test_se_role_boundary.py:1-9` (`from __future__ import annotations`, `_REPO_ROOT = Path(__file__).resolve().parents[1]`, `sys.path.insert(0, str(_REPO_ROOT))`):
  - `test_no_single_brace_se_base_dir`: ueber `sorted((_REPO_ROOT / "agents" / "1-generic").glob("se-*.md"))` kein Treffer fuer `re.compile(r"(?<!\{)\{SE_BASE_DIR\}(?!\})")`; Assertion-Meldung nennt Datei und Zeile. Erwartung rot: 18 Treffer in 12 Dateien.
  - `test_double_brace_count_is_preserved_plus_eighteen`: Summe der `{{SE_BASE_DIR}}`-Treffer ueber alle `se-*.md` == 22 (heute 4 + 18). Rot bis Step 2.
  - `test_every_se_base_dir_token_is_substitutable`: je Datei `text.count("SE_BASE_DIR") == len([m for m in _VAR_PATTERN.finditer(text) if m.group(1) == "SE_BASE_DIR"])` mit `from scripts.lib.variables import _VAR_PATTERN`. Das ist der Golden-Test aus Issue-AC 2 (jeder Token trifft das Platzhalter-Pattern, es bleibt kein unsubstituierter Token).
  - `test_se_architect_has_no_single_brace_prefix`: `"{SE_"` kommt in `se-architect.md` nur als Teil von `{{SE_` vor (`re.search(r"(?<!\{)\{SE_", text) is None`).
- [ ] Step 2: Implementieren. In den 12 Dateien jedes `{SE_BASE_DIR}` (ohne doppelte Klammer) durch `{{SE_BASE_DIR}}` ersetzen; Satzbau und alles andere unveraendert (Issue-AC 4). In jeder Datei `version:` im Frontmatter um eine Patch-Stufe anheben (Check `frontmatter.version-bump`, `scripts/lib/consistency/frontmatter.py:48-56`: ERROR, wenn eine git-geaenderte Datei dieselbe `version:` wie HEAD traegt; Regel "patch=text"; Beispiel `se-architect.md` heute `version: 2.2.2`).
- [ ] Step 3: Test (gruen) und Gates:
  - `python3 -m pytest tests/test_se_single_brace_placeholders.py -q` Erwartung: 4 passed.
  - `grep -rnE '(^|[^{])\{SE_BASE_DIR\}' agents/1-generic/` Erwartung: 0 Treffer (Issue-AC 1).
  - `python3 scripts/consistency-check.py` Erwartung: keine neuen ERROR; `python3 scripts/sync.py --validate` rc 0.
- [ ] Step 4: Commit: `fix: use double-brace SE_BASE_DIR in SE templates`

**Akzeptanz:** 18 Stellen in 12 Dateien ersetzt; 4 Tests gruen; kein Zaehlerwechsel bei bestehenden `{{SE_BASE_DIR}}`.

### E-T2: Check `placeholders.single-brace` (#1198, Klasse S)

**Rolle:** `developer`
**Files:** Modify `scripts/lib/consistency/placeholders.py`, `scripts/consistency-check.py`; Modify `tests/test_se_single_brace_placeholders.py`; Create `tests/fixtures/single_brace_rules/example-code-rule.md` und `tests/fixtures/single_brace_rules/known-var-in-fence-rule.md`.
**Scope (Entscheidung 50):** `agents/`, `commands/`, `rules/`.
**Interfaces:** Consumes: `Finding(severity, check, file, message, suggestion="")` und `Severity.ERROR` aus `scripts/lib/consistency/report.py:23,29` (re-gemessen); `_BUILTIN_VARS` (`placeholders.py:12`, enthaelt `"SE_BASE_DIR"` in `:98`, re-gemessen); `_rel(path, root)` (`:245`); `load_project_vars` (`:234`); `check_placeholders` (`:196`). Produces:

```python
_SINGLE_BRACE_RE = re.compile(r"(?<![{$])\{([A-Z][A-Z0-9_]*)\}(?!\})")

def check_single_brace_placeholders(path: Path, content: str, agent_meta_root: Path,
                                    extra_vars: set[str] | None = None) -> list[Finding]:
    """Report {KNOWN_VAR} (single brace) -- never substituted, silent failure (#1198)."""
```

Regeln: Frontmatter wie in `check_placeholders` (`:204`, re-gemessen) entfernen, aber **keine** Fence-/Inline-Code-Entfernung; melden nur Namen aus `_BUILTIN_VARS | (extra_vars or set())`; je Name ein Finding (dedupliziert); `Severity.ERROR`, Check-ID `placeholders.single-brace`, Hinweis "use {{NAME}}".

- [ ] Step 1: Tests schreiben (rot, `ImportError`/`AttributeError`) in dieselbe Datei:
  - `test_flags_single_brace_known_var`: `check_single_brace_placeholders(Path("x.md"), "a {SE_BASE_DIR}/b", _REPO_ROOT)` ergibt genau 1 Finding mit `.check == "placeholders.single-brace"` und `.severity == Severity.ERROR`.
  - `test_ignores_double_brace`: Inhalt `"{{SE_BASE_DIR}}/b"` ergibt `[]`.
  - `test_ignores_unknown_upper_names_and_shell_form`: `"-{NNN}"`, `"${TIMEOUT}"`, `"{FolderName}"` ergeben `[]`.
  - `test_flags_inside_code_fence`: Inhalt "```\n{SE_BASE_DIR}/x\n```" ergibt 1 Finding.
  - `test_extra_vars_are_respected`: `extra_vars={"MY_VAR"}`, Inhalt `"{MY_VAR}"` ergibt 1 Finding.
  - `test_rule_example_code_does_not_false_alarm` (Entscheidung 50): Fixture `example-code-rule.md` enthaelt einen Fence mit dem realen Beispiel `L{N}_{FolderName}_{Artefakt}.md` (Quelle `rules/1-generic/se-cascade-artifact-taxonomy.md:40`) und `-{NNN}`; Ergebnis `[]`. Belegt: Schutz gegen Fehlalarm ist der Namensfilter (nur bekannte Variablen), kein Fence-Masking.
  - `test_rule_known_var_in_fence_is_flagged`: Fixture `known-var-in-fence-rule.md` mit `{SE_BASE_DIR}` im Fence ergibt 1 Finding (sync substituiert in Regeln auch in Fences nicht; stiller Fehler wie in Agenten). Damit ist dokumentiert: Es gibt keine Maskierung; eine Regel darf einen bekannten Namen nicht in Einfach-Klammern zeigen.
  - `test_collect_rule_files_covers_rules_tree`: `collect_rule_files(_REPO_ROOT)` liefert alle `rules/**/*.md` (Anzahl == `len(list((_REPO_ROOT / "rules").rglob("*.md")))`, heute 49).
  - `test_repo_agents_commands_rules_are_clean`: `rglob("*.md")` unter `agents/`, `commands/` und `rules/` (falls vorhanden), `load_project_vars(_REPO_ROOT)` als `extra_vars`; Summe der Findings == 0 (haengt von E-T1 ab; `rules/` heute 0 Treffer laut Review-Messung).
- [ ] Step 2: Implementieren: Funktion in `placeholders.py` direkt nach `check_placeholders`; in `scripts/consistency-check.py` Import-Zeile (`:62`) um `check_single_brace_placeholders` erweitern, Aufruf `findings += check_single_brace_placeholders(path, content, root, project_vars)` nach `:215` und ebenso in der Command-Schleife (nach `:222`). Neue Funktion `collect_rule_files(root, only)` direkt nach `collect_command_files` (`:155`, gleiches Muster mit `only`-Filter, `sorted((root / "rules").rglob("*.md"))`), Aufruf neben `collect_command_files` (`:206`) und eigene Regel-Schleife nur mit `check_single_brace_placeholders` (keine Agent-Frontmatter-Checks auf Regeln). Single-File-Modus (`:195-201`): Pfad mit `rules/` wird als Regel behandelt.
- [ ] Step 3: Gates: `python3 -m pytest tests/test_se_single_brace_placeholders.py -q` (13 passed); `python3 -m pytest tests/test_runtime_gate_wiring.py -q` (bestehende `placeholders`-Nutzung unveraendert gruen); `python3 scripts/consistency-check.py` ohne `placeholders.single-brace`; `python3 scripts/sync.py --validate` rc 0.
- [ ] Step 4: Commit: `feat: add placeholders.single-brace consistency check`

**Akzeptanz:** Check meldet `{SE_BASE_DIR}` als ERROR in `agents/`, `commands/` und `rules/` (Entscheidung 50), ignoriert `{NNN}`, `{N}`, `{FolderName}`, `${TIMEOUT}`, `{{...}}`; Repo ist frei von Findings (Issue-AC 3).

---

### Block 2 (Phasen-PR): Kern #1186

### E-T3: Kernplan ausfuehren, mit Delta-Regeln (kein neuer Code im Wrapper)

**Rolle:** Orchestrator waehlt je Task die im Kernplan genannte Rolle.
**Files/Interfaces:** siehe Kernplan Abschnitte 2 und 6 (nicht dupliziert).
- [ ] Step 1: Block 0 (#1187) ist abgeschlossen oder E-C0 hat #1187 als bereits erfuellt belegt (Entscheidung 49). Block 1 (E-T1, E-T2) liegt als Commits im selben Phasen-Branch vor. Phasen-Branch von aktuellem origin/main (Anker neu verifiziert).
- [ ] Step 2: Kernplan T1..T21, T23, T24 in Meilensteinen M1..M6 ausfuehren. **T22 entfaellt** (ersetzt durch E-T4, siehe Abweichung 7).
- [ ] Step 3: Delta-Regeln, die der Kernplan noch nicht kennt:
  - **T11:** Ausgangslage ist `{{SE_BASE_DIR}}` (nach Block 1), nicht `{SE_BASE_DIR}`. Zaehlung 18 statt 16. `test_no_single_brace_se_token` (Kern T11, Muster `{SE_`) muss `(?<!\{)\{SE_` nutzen, solange `{{SE_BASE_DIR}}` noch irgendwo steht, am Ende von T11 darf keines mehr stehen. Der Test aus E-T1 (`test_double_brace_count_is_preserved_plus_eighteen`) wird in T11 durch den Kern-Test ersetzt und entfernt (Ownership: T11 aendert `tests/test_se_single_brace_placeholders.py` nur an dieser Stelle).
  - **T17:** Der Test `test_no_derivation_in_this_task` bleibt bis E-T4 bestehen.
  - **T14/T10:** Der neue Check `placeholders.single-brace` (E-T2) laeuft parallel zu `artifact-locations.literal-path`; keine Ueberschneidung (andere Check-ID).
  - **M5 (T17-T19):** erst nach #1189 gemergt (Kernplan Voraussetzung 1).
- [ ] Step 3a: Gates je Meilenstein wie Kernplan Abschnitt 4.
- [ ] Step 4: Ein Commit je Task nach Kernplan, im Phasen-PR.

**Akzeptanz:** Kernplan-Gates M1..M6 gruen; `python3 -m pytest -q` 0 failed; `python3 scripts/sync.py --validate` rc 0.

---

### Block 3 (Phasen-PR): #1199 und #1200 (nach Block 2)

### E-T4: Whitelist-Drift absichern, kein Ableiten (#1199, Klasse S)

**Rolle:** `developer`
**Files:** Modify `scripts/admin-server.py`; Create `tests/test_admin_whitelist_drift.py`; Modify `tests/test_admin_server.py` (Test `test_no_derivation_in_this_task` entfernen; `test_put_roundtrip_for_runtime_only_sections` hinzufuegen).
**Interfaces:** Consumes: `PROJECT_WRITABLE_SECTIONS: frozenset[str]` (`scripts/admin-server.py:234`, 47 Eintraege auf main, 48 nach Kern T17); `AdminRequestHandler._assert_project_sections_writable(self, sections: Iterable[str]) -> None` (`:5241`); `_assert_project_update_writable(self, updates, existing) -> None` (`:5257`). Produces:

```python
_RUNTIME_ONLY_SECTIONS: dict = {
    "rules": "...", "rules-preset": "...", "agent-prompts": "...",
    "steps-overrides": "...", "environments": "...", "skills-registry": "...",
    "backup": "...", "submodule-protection": "...",
}  # name -> "kein Schema-Pendant, weil ..."
```

Das Literal `PROJECT_WRITABLE_SECTIONS` bleibt unveraendert als Literal (bestehende Tests parsen es: `tests/test_context_profile_admin.py:22-24` per Regex, `tests/test_knowledge_engine.py:574-576` per `ast.dump`). Begruendungstexte je Eintrag aus den Belegen im Issue #1199 (Stand 9aa0e0c0 re-gemessen: `backup`: `scripts/admin-server.py:248`, `scripts/lib/backup.py`; `rules-preset`: `scripts/lib/config.py:152,162` (Issue: 151,161), `scripts/lib/context_profile.py:116-117`; `steps-overrides`: `scripts/lib/roles.py:650-654`).

- [ ] Step 1: Tests schreiben (rot). `tests/test_admin_whitelist_drift.py` laedt `admin-server.py` wie `tests/test_admin_server.py` (Importweg dort uebernehmen) und das Schema per `json.loads(Path("config/project-config.schema.json").read_text(encoding="utf-8"))["properties"]`:
  - `test_runtime_only_equals_whitelist_minus_schema`: `set(admin_server._RUNTIME_ONLY_SECTIONS) == set(PROJECT_WRITABLE_SECTIONS) - set(schema_props)` (Drift in beide Richtungen: neuer schema-loser Eintrag ohne Deklaration rot; in Schema verschobener Eintrag in `_RUNTIME_ONLY_SECTIONS` rot).
  - `test_runtime_only_has_reasons`: jede Begruendung ist ein String mit `"Schema"` oder `"schema"` und Laenge > 20 (Issue-AC 3).
  - `test_runtime_only_count_is_eight`: `len(_RUNTIME_ONLY_SECTIONS) == 8` und enthaelt `rules-preset` (Korrektur gegenueber Spec/Kernplan "7").
  - `test_read_only_schema_roots_stay_unwritable`: `{"variables", "agent-meta-version", "_comment"}` sind **nicht** in `PROJECT_WRITABLE_SECTIONS` (Absicherung gegen eine spaetere Ableitung).
  - `test_put_roundtrip_for_runtime_only_sections`: je Eintrag aus `_RUNTIME_ONLY_SECTIONS` ruft `handler._assert_project_sections_writable([name])` ohne `ValueError` (Issue-AC 2). Ort: `tests/test_admin_server.py`, Klasse `TestWriteProjectSectionFeatureBSections` (`:2118`), weil `_make_handler` dort eine Methode ist (`:2124`, nicht importierbar); Muster `test_variables_stays_unwritable` (`:2166`). Die vier uebrigen Tests liegen in `tests/test_admin_whitelist_drift.py`; Modul laden wie `tests/test_admin_server.py:42-51` (`importlib.util.spec_from_file_location("admin_server", ...)`).
  - Rot-Grund heute: `_RUNTIME_ONLY_SECTIONS` existiert nicht.
  - Querbezug Phase D (#1141, laeuft nach E): Plan D Task 12 nimmt `rules-preset` und `backup` ins Schema auf (`2026-11-11-phase-d-guards-hooks.md:64`, `:291`). Danach werden `test_runtime_only_equals_whitelist_minus_schema` und `test_runtime_only_count_is_eight` absichtlich rot; der #1141-Commit muss beide Eintraege aus `_RUNTIME_ONLY_SECTIONS` entfernen und die Zahl auf 6 senken. Plan D erwaehnt das heute nicht (Befund an Plan D gemeldet).
- [ ] Step 2: Implementieren: Mapping direkt vor `PROJECT_WRITABLE_SECTIONS` einfuegen (Kommentarblock `:224-233` um "drift test pins this" ergaenzen). In `tests/test_admin_server.py` den Kern-T17-Test `test_no_derivation_in_this_task` entfernen (er behauptet das Gegenteil).
- [ ] Step 3: Gates: `python3 -m pytest tests/test_admin_whitelist_drift.py tests/test_admin_server.py tests/test_context_profile_admin.py tests/test_knowledge_engine.py -q` 0 failed; `python3 scripts/sync.py --validate` rc 0.
- [ ] Step 4: Commit: `test: pin admin writable sections against schema drift`

**Akzeptanz:** Whitelist hat unveraenderte Menge; Abweichung zum Schema schlaegt in beide Richtungen an; 8 Runtime-Sektionen tragen Begruendung; `variables` bleibt gesperrt.

### E-T5: Entscheidungstabelle `docs/` Unterbaeume (#1200, Klasse S)

**Rolle:** `documenter`
**Files:** Create `docs/concepts/artifact-subtree-classification.md`; Create `tests/test_artifact_subtree_classification.py`.
**Interfaces:** Consumes: Kernplan Abschnitt 3.2a (D-8: `unmanaged[]`-Liste und `legacy[]`-Zuordnung). Produces: Markdown-Tabelle mit Spalten `Pfad | Entscheidung | Begruendung`, `Entscheidung` in `{class:<name>, legacy, unmanaged}`.

Zuordnung (entspricht dem freigegebenen Kern, siehe Abweichung 8):

| Pfad | Entscheidung |
|---|---|
| `docs/superpowers/` (`specs`, `plans`) | legacy |
| `docs/issues/`, `docs/testing/`, `docs/providers/`, `docs/api/`, `docs/howto/`, `docs/guides/`, `docs/se-cascade/` | unmanaged |
| `docs/plans/audit-2026-09-detailed-system-audit.md`, `docs/plans/audit-admin-ui-model-loading.md`, `docs/plans/archive/audit-2026-08-refactoring-roadmap.md`, `docs/plans/archive/audit-2026-09-system-concept.md` | legacy (neue Audits: Klasse `audits`, `docs/audits`) |

- [ ] Step 1: Test schreiben (rot, Datei fehlt). `test_table_lists_all_eight_subtrees`, `test_table_lists_four_audit_files`, `test_audit_files_exist_on_disk` (die vier Pfade existieren in W, verifiziert), `test_each_row_has_valid_decision` (Regex `^(class:[a-z-]+|legacy|unmanaged)$`).
- [ ] Step 2: Dokument schreiben (Deutsch, Kopf wie die anderen `docs/concepts/*.md`: kein YAML-Frontmatter, erste Zeile `# Konzept — ...`, danach `> Status: ...`; geprueft: alle 12 `.md` in `docs/concepts/` beginnen mit `# `).
- [ ] Step 3: `python3 -m pytest tests/test_artifact_subtree_classification.py -q` Erwartung: 4 passed.
- [ ] Step 4: Commit: `docs: classify docs subtrees and audit files for artifacts`

**Akzeptanz:** Issue-AC 1: Zuordnung fuer alle acht Unterbaeume und vier Audit-Dateien dokumentiert.

### E-T6: Tabelle gegen die Matrix pruefen (#1200, Klasse S)

**Rolle:** `developer`
**Files:** Modify `tests/test_artifact_subtree_classification.py`.
**Interfaces:** Consumes (Kernplan Abschnitt 6.1, nach Block 2 vorhanden): `resolve_artifact_locations(config: dict, agent_meta_root: Path, project_root: Path | None = None) -> ResolvedMatrix` aus `scripts/lib/artifact_locations.py`; `ResolvedMatrix.legacy: tuple[str, ...]`, `ResolvedMatrix.unmanaged: tuple[str, ...]`.
- [ ] Step 1: Tests schreiben (rot, bis Tabelle und Matrix uebereinstimmen; Grund-Rot: Test nutzt `fnmatch` gegen die Listen):
  - `test_legacy_rows_are_covered_by_matrix_legacy`: je `legacy`-Zeile `any(fnmatch(path, pat) or path.startswith(pat.rstrip("*/") + "/") for pat in matrix.legacy)`.
  - `test_unmanaged_rows_are_covered_by_matrix_unmanaged`: analog fuer `matrix.unmanaged`.
  - `test_no_row_is_both_legacy_and_unmanaged`.
  - `test_missing_dir_findings_are_zero_for_this_repo`: Aufruf der Kern-Funktion aus T14 `check_artifact_locations(agent_meta_root, project_root, config) -> list[Finding]` (Kernplan `:810`) auf W; Findings mit `check == "artifact-locations.missing-dir"` (Severity INFO, Kernplan `:803`) == 0 (Issue-AC 2; vorher `python3 scripts/sync.py` ausfuehren, damit `.gitkeep`-Verzeichnisse existieren).
- [ ] Step 2: Falls Rot wegen echter Luecke: Tabelle (E-T5) oder Kern-Framework-Liste angleichen; Aenderung der Kern-Liste nur mit Hinweis im PR (Kern ist APPROVED).
- [ ] Step 3: `python3 -m pytest tests/test_artifact_subtree_classification.py tests/test_consistency_artifact_locations.py -q` 0 failed; `python3 scripts/consistency-check.py` ohne `artifact-locations.missing-dir`.
- [ ] Step 4: Commit: `test: verify docs subtree table against artifact matrix`

**Akzeptanz:** Issue-AC 2 bis 4: 0 `missing-dir`, Audit-Dateien als `legacy[]` erfasst, `unmanaged`-Baeume explizit ausgenommen.

---

### Block 4 (Nachfolge-PR, Entscheidung 36/52): #1209 (PR erst nach APPROVED E-T7)

### E-T7: Spec schreiben + Freigabe-Gate (#1209, Klasse M)

**Rolle:** `requirements` (Spec), danach Review und Freigabe durch den User.
**Files:** Create `docs/specs/2026-11-12-artifact-mode-template-gating-spec.md` (Datum beim Schreiben anpassen), `Status: DRAFT` bis Freigabe.
**Vor Block 2 nicht startbar.** Kein Implementierungs-Task (E-T8) ist vor `Status: APPROVED` ausfuehrbar. Der #1209-Nachfolge-PR wird erst eroeffnet, wenn E-T7 APPROVED ist (Entscheidung 36). Der Phasen-PR wartet nicht darauf.
- [ ] Step 1: Spec-Input. Festgelegt durch **Entscheidung 56** (Spec uebernimmt, entscheidet nicht neu; Namenspruefung origin/main: `_FALSE_DEFAULT_CONDITIONALS` existiert `scripts/lib/variables.py:59`, Default-Zeile `:613`; `_MODE_FILES`/`_MODE_INLINE` und `ARTIFACT_<CLASS>_MODE` haben 0 Treffer in `scripts/` -> `_MODE_*` plan-eingefuehrt, `ARTIFACT_<CLASS>_MODE` vom Kern #1186 eingefuehrt):
  - Gate-Form (E U1): zwei Flags `ARTIFACT_<CLASS>_MODE_FILES` und `ARTIFACT_<CLASS>_MODE_INLINE` je Klasse, abgeleitet aus `ARTIFACT_<CLASS>_MODE` (Kern). Werte: Modus `files` -> `_MODE_FILES="true"`, `_MODE_INLINE="false"`; `inline` -> `"false"`/`"true"`; `off` -> beide `"false"`.
  - Modus-Wert (E U2): `files` (Kern) bleibt; der Issue-Text von #1209 (`file`, `_MODE_FILE`) wird angepasst (Umsetzungsschritt nach APPROVED, kein Plan-Schritt mit Issue-Aenderung jetzt).
  - Whitelist (E U3): Suffix-Match `k.startswith("ARTIFACT_") and k.endswith(("_MODE_FILES", "_MODE_INLINE"))` statt Praefix (Abweichung 10); `ARTIFACT_ZIP_CMD`/`ARTIFACT_TAR_CMD` werden damit nicht erfasst. Zielort `strip_inactive_conditional_blocks` (`scripts/lib/variables.py:662`, re-gemessen; war :556), Muster `conditional_vars.update({k for k in variables if ...})` wie `:689,703,704` (re-gemessen; war :583,587,592).
  - Default bei fehlender Konfiguration (E U4): `_conditional_active` (`:604-614`, re-gemessen; war :498-508) gibt bei fehlender Variable `"true"` zurueck (Default-Zeile `:613`); das erfuellt "absent config reproduces today's output" (Issue-AC 1). Default true, **kein** Eintrag in `_FALSE_DEFAULT_CONDITIONALS` (`:59`, war :54), sonst wird jede Rolle bei fehlendem Wert abgeschaltet.
  - Umfang (offen, U5, Spec entscheidet): Welche der 26 Templates (Kernplan: 10 Nicht-SE, 12 SE, 4 Reviewer) bekommen Gates; SE-Klassen mit `subdir` und Projektions-Variablen.
  - Vertragsaenderung (offen, U6, Spec entscheidet den Inhalt): Kern-AC-05 ("kein Template-Gate", Spec Zeile 1111) und Kern-Tests, die kein `{{#if}}` erlauben (Plan T10 `test_fallback_mentions_inline_mode`, Kernplan `:714`), werden angepasst; Umgang mit der APPROVED Kern-Spec: nur Vermerk (Entscheidung 34, E-N3). Inhalt der Vertragsaenderung offen (U6).
  - Registrierung: neue Namen in `_BUILTIN_VARS` (`placeholders.py:12`), sonst ERROR in `check_builder_known_set` (`:323`, re-gemessen; war :314); Standalone-Defaults (`scripts/lib/standalone.py`); Kern-Pin der 54 Namen (T7, `tests/test_artifact_locations_placeholders.py`) erweitern.
  - Dokumentation des Template-Gate-Vertrags (Issue Punkt 4, E U7): Ort `docs/api/pal-variables.md` (existiert in origin/main).
- [ ] Step 2: Spec-Review (`concept-reviewer`/`spec-reviewer` falls vorhanden), User-Freigabe `Status: APPROVED`.
- [ ] Step 3: Commit: `docs: add spec for artifact mode template gating`

**Akzeptanz:** Spec traegt `Status: APPROVED`; U1-U4, U7 entsprechen Entscheidung 56 wortgleich; U5/U6 sind in der Spec beantwortet; Issue-ACs 1-5 sind auf Spec-Abschnitte abgebildet.

### E-T8: Umsetzungsskelett #1209 (NICHT AUSFUEHRBAR vor E-T7; Nachfolge-PR, rebased auf den gemergten E-Phasen-PR)

**Rolle:** `developer`
**Files (vorlaeufig, nach Spec zu bestaetigen):** Modify `scripts/lib/variables.py` (Whitelist in `strip_inactive_conditional_blocks`), `scripts/lib/config.py` (Builder `_build_artifact_variables`, Name aus Kern T6, nachlesen), `scripts/lib/consistency/placeholders.py`, `scripts/lib/standalone.py`, `docs/api/pal-variables.md` (E U7), bis zu 26 `agents/1-generic/*.md`; Create `tests/test_artifact_mode_gating.py`.
Vorgesehene Tests (Wortlaut folgt der Spec): `test_mode_off_removes_block_and_mode_files_keeps_it` (Issue-AC 2), `test_absent_config_renders_byte_identical` (AC 1), `test_no_unresolved_artifact_if_marker_survives_render` (AC 3), `test_gated_templates_enumeration` (AC 4, Liste der Rollen mit Pfad-Ausgabe, neue Rolle ohne Gate faellt durch), `test_zip_cmd_not_swallowed_by_whitelist` (Abweichung 10, E U3: `ARTIFACT_ZIP_CMD`/`ARTIFACT_TAR_CMD` nicht in der Whitelist, `ARTIFACT_<CLASS>_MODE_FILES`/`_MODE_INLINE` drin). Aus Entscheidung 56 zusaetzlich: `test_mode_flags_derived_from_mode` (E U1/U2, je Klasse: `files` -> `_MODE_FILES == "true"`, `_MODE_INLINE == "false"`; `inline` -> `"false"`/`"true"`; `off` -> beide `"false"`), `test_mode_flags_default_true_without_config` (E U4: `_conditional_active({}, "ARTIFACT_<CLASS>_MODE_FILES") is True` und kein `_MODE_FILES`/`_MODE_INLINE`-Name in `_FALSE_DEFAULT_CONDITIONALS`), `test_pal_variables_doc_lists_mode_flags` (E U7: `docs/api/pal-variables.md` nennt `_MODE_FILES` und `_MODE_INLINE`).
Commit-Betreff (vorlaeufig): `feat: gate artifact output sections by mode`

**Akzeptanz:** erst nach Spec konkretisieren; Aufwand per `effort-estimator`.

---

## Frische-Check-Referenzen

Stand Revision 3: Die 4 lastragenden Anker wurden per Read/Grep im Worktree W (origin/main `9aa0e0c0`, PR #1218) re-gemessen. Vor Ausfuehrung (E-T0 Step 3) alle uebrigen Anker neu pruefen; Abweichungen im Phasen-PR-Body dokumentieren.

Re-Messung 9aa0e0c0 (Anker, alter Stand a3d65da4 in Klammern):

| Anker | Stand 9aa0e0c0 | Befund |
|---|---|---|
| `PROJECT_WRITABLE_SECTIONS` (`scripts/admin-server.py`) | `:234` (234) | unveraendert |
| `_assert_project_sections_writable` / `_assert_project_update_writable` (`scripts/admin-server.py`) | `:5241` / `:5257` (5241 / 5257) | unveraendert |
| `_VAR_PATTERN` (`scripts/lib/variables.py`) | `:136` (108) | verschoben, +28 |
| `_conditional_active` (`scripts/lib/variables.py`) | `:604-614` (498-508) | verschoben, +106 |
| `strip_inactive_conditional_blocks` (`scripts/lib/variables.py`) | `:662` (556) | verschoben, +106 |
| `_FALSE_DEFAULT_CONDITIONALS` (`scripts/lib/variables.py`) | `:59` (54) | verschoben, +5 |
| `_BUILTIN_VARS` / `SE_BASE_DIR` (`scripts/lib/consistency/placeholders.py`) | `:12` / `:98` (12 / 89) | `:12` unveraendert, Eintrag verschoben +9 |
| `check_placeholders` / `load_project_vars` / `_rel` / `check_builder_known_set` (`placeholders.py`) | `:196` / `:234` / `:245` / `:323` (187|195 / 225 / 236 / 314) | verschoben, +9 |
| `Finding` / `Severity` (`scripts/lib/consistency/report.py`) | `:29` / `:22` (`Severity.ERROR` `:23`) | `Finding` unveraendert, `ERROR` ein Zeile versetzt |
| `SE_BASE_DIR` in `agents/1-generic/` | 22 Treffer (inkl. `{{...}}`) in 12 Dateien (Plan: 18 einfach + 4 doppelt) | Dateianzahl stimmt |

Deviations: `variables.py` und `placeholders.py` sind gegenueber a3d65da4 verschoben. Im Body aktualisiert: E-T1 (`_VAR_PATTERN`), E-T2 (`report.py`, `placeholders.py`), E-T7 Step 1 (`strip_inactive_conditional_blocks`, `_conditional_active`, `_FALSE_DEFAULT_CONDITIONALS`). Alte Werte stehen in Klammern. Review 2026-11-11 (gegen 9aa0e0c0 nachgemessen):
- `scripts/lib/config.py:2315` (war :2273, korrigiert).
- `scripts/consistency-check.py:62`, `:215`, `:222` stimmen.
- `scripts/lib/consistency/placeholders.py:59` (ARTIFACT_ZIP_CMD) stimmt; Frontmatter-Strip `:204`, Fences `:207`, Inline `:209` (war :195/:198/:200, korrigiert).
- `scripts/admin-server.py` Kommentarblock `:224-233`.
- `tests/test_admin_server.py`: `_make_handler` `:2124`, `test_variables_stays_unwritable` `:2166`.
- `config/project-config.schema.json:335`, `:338` stimmen.
- Kern-Anker in `docs/plans/2026-11-09-artifact-locations-matrix-plan.md`: Voraussetzung 8 `:63`, T17-Test `:954`, `check_artifact_locations` `:810`, `ResolvedMatrix` `:1164`, `resolve_artifact_locations` `:1173`.
- Spec `docs/specs/2026-11-09-artifact-locations-matrix-spec.md`: AC-05 `:1111`, "16" `:102` und `:1167`.

Dateien:
- `docs/plans/2026-11-09-artifact-locations-matrix-plan.md`
- `docs/plans/2026-11-09-project-context-injection-scope-plan.md`
- `docs/specs/2026-11-09-project-context-injection-scope-spec.md`
- `rules/1-generic/se-cascade-artifact-taxonomy.md`
- `tests/scenarios/registry.md`
- `tests/scenarios/run.sh`
- `docs/specs/2026-11-09-artifact-locations-matrix-spec.md`
- `scripts/admin-server.py`
- `scripts/lib/variables.py`
- `scripts/lib/config.py`
- `scripts/lib/standalone.py`
- `scripts/lib/consistency/placeholders.py`
- `scripts/lib/consistency/report.py`
- `scripts/consistency-check.py`
- `scripts/lib/artifact_locations.py`
- `config/project-config.schema.json`
- `agents/1-generic/se-requirements.md`
- `agents/1-generic/se-component-requirements.md`
- `agents/1-generic/se-architect.md`
- `agents/1-generic/se-interface-mgr.md`
- `agents/1-generic/se-developer.md`
- `agents/1-generic/se-senior-developer.md`
- `agents/1-generic/se-junior-developer.md`
- `agents/1-generic/se-integration-and-test-manager.md`
- `agents/1-generic/se-validator.md`
- `agents/1-generic/se-verifier.md`
- `agents/1-generic/se-termination.md`
- `agents/1-generic/se-critic.md`
- `agents/1-generic/developer.md`
- `agents/2-platform/sharkord-release.md`
- `tests/test_admin_server.py`
- `tests/test_context_profile_admin.py`
- `tests/test_knowledge_engine.py`
- `tests/test_runtime_gate_wiring.py`
- `tests/test_se_role_boundary.py`
- `tests/test_se_single_brace_placeholders.py`
- `tests/test_admin_whitelist_drift.py`
- `tests/test_artifact_subtree_classification.py`
- `tests/test_artifact_locations_placeholders.py`
- `tests/test_consistency_artifact_locations.py`
- `docs/concepts/artifact-subtree-classification.md`
- `docs/plans/audit-2026-09-detailed-system-audit.md`
- `docs/plans/audit-admin-ui-model-loading.md`
- `docs/plans/archive/audit-2026-08-refactoring-roadmap.md`
- `docs/plans/archive/audit-2026-09-system-concept.md`
- `docs/api/pal-variables.md`

Symbole:
- `PROJECT_WRITABLE_SECTIONS`
- `_RUNTIME_ONLY_SECTIONS`
- `_assert_project_sections_writable`
- `_assert_project_update_writable`
- `_VAR_PATTERN`
- `_conditional_active`
- `strip_inactive_conditional_blocks`
- `_FALSE_DEFAULT_CONDITIONALS`
- `_BUILTIN_VARS`
- `check_placeholders`
- `check_single_brace_placeholders`
- `collect_command_files`
- `collect_rule_files`
- `PROJECT_CONTEXT_INJECTED`
- `check_builder_known_set`
- `load_project_vars`
- `Finding`
- `Severity`
- `resolve_artifact_locations`
- `ResolvedMatrix`
- `SE_BASE_DIR`
- `ARTIFACT_ZIP_CMD`
- `ARTIFACT_TAR_CMD`
- `placeholders.single-brace`
- `artifact-locations.missing-dir`

Issues:
- #1186, #1187, #1188, #1189, #1198, #1199, #1200, #1209, #1141, #1150, #1181
- Kette (Entscheidungen 19, 35): #1187 -> #1186 (E) -> #1188 (F) -> #1181 (D Strang A) -> #1141 (D, letzter Teil). Nur #1187 (E-C0, Block 0), #1189, #1186, #1198, #1199, #1200, #1209 sind Teil von Phase E; #1209 im Nachfolge-PR (Entscheidung 36/52).

## Entscheidungen (beantwortet)

Quelle: Roadmap-Entscheidungen 17-34 (`decisions-part2.md`, user-beantwortet), 35-38 (`decisions-part3.md`) und 39-53 (Roadmap Abschnitt 7c; fuer E relevant: 49, 50, 52). Original-IDs in Klammern. Entscheidungen 37 (#898) und 38 (#1085b, #1086, #329/#330, #1190, #1210) betreffen Phase E nicht; keine Aenderung dieses Plans.

- **17 (= E-N1): PR-Schnitt.** Ein Phasen-PR fuer Phase E mit einem Commit je Task. Ersetzt die vier PRs E-1..E-4. Die interne Task-Reihenfolge und die Block-Reihenfolge bleiben. Ausnahme durch 36/52 (siehe unten): #1209 ist der Nachfolge-PR.
- **19: Kette.** #1187 -> #1186 (E) -> #1188 (F) -> #1181 (D Strang A) -> #1141. Phase E kommt vor Phase F. Gate fuer #1187 ist E-C0 (Pruefung ohne Annahme). Durch 35 ersetzt: #1141 steht am Ende von D, nicht mehr in F (siehe 35).
- **35: #1141 in Phase D.** Kette #1187 -> #1186 (E) -> #1188 (F) -> #1181 (D Strang A) -> #1141 (D, letzter Teil nach #1181). #1141 ist nicht Teil von E und nicht mehr Teil von F. Auswirkung auf E: nur Kettenvermerk; damals Phase E = 5 Issues, durch 49 jetzt 6 (+ #1187). Quelle: `decisions-part3.md`, Entscheidung 35.
- **36 (= U9): #1209 abgespalten.** #1209 ist aus dem Phasen-PR herausgeloest. Eigener PR nur nach APPROVED Spec (E-T7). Der Phasen-PR (#1186, #1198, #1199, #1200) ist ohne #1209 mergebar. Block 4 / E-T8 ist der separate #1209-PR (Branch-Vorschlag `feat/artifact-mode-template-gating`), rebased auf den gemergten E-Phasen-PR. Die Strict-One-PR-Regel (17) gilt fuer E sonst weiter. Quelle: `decisions-part3.md`, Entscheidung 36.
- **Phase C vs. E (keine User-Entscheidung, Roadmap-Regel):** E laeuft nach dem C-PR, weil die Dateilisten nicht disjunkt sind (Roadmap Abschnitt 3, Regel "Parallel nur bei disjunkter `Files:`-Liste"; Plan C `:7`). Der Roadmap-Hinweis "E parallel zu C, falls Dateiliste disjunkt" ist damit nicht verworfen, seine Bedingung ist nicht erfuellt.
- **34 (= E-N2): #1199 Ansatz.** Option (a): Drift-Test plus `_RUNTIME_ONLY_SECTIONS`, keine Ableitung (E-T4, Abweichung 6).
- **34 (= E-N3): APPROVED-Dokumente.** Nur Vermerk im Wrapper-Plan und im Phasen-PR. Kern-Spec AC-1186-07, Kernplan T17/T22 und AC-05 bleiben unveraendert. #1199 AC 4 wird per Vermerk erfuellt.
- **49 (= U10): #1187 nachziehen.** #1187 wird erster Block (Block 0) von Phase E; Wiederoeffnen nur nach User-Freigabe. Begruendung: APPROVED Kernplan #1186 nennt es als Voraussetzung 2; `PROJECT_CONTEXT_INJECTED` und Szenarien 95-98 fehlen auf origin/main. Phase E = 6 Issues, Roadmap 90. Block 2 und damit Phase F entsperrt, sobald Block 0 drin ist. Roadmap-Konflikt 8 geloest. Plan-Referenz: `docs/plans/2026-11-09-project-context-injection-scope-plan.md`.
- **50 (= U8): #1198 Scope inkl. `rules/`.** Weicht von der Planner-Empfehlung (nein) ab. Scope `agents/`, `commands/`, `rules/`; Fixture-Test belegt kein Fehlalarm durch Beispielcode (E-T2). Review-Messung: Regex trifft heute nur die 12 SE-Templates, 0 in `rules/`.
- **52: PR-Schnitt.** Phasen-PR nur mit derzeit ausfuehrbaren Tasks (Block 0-3); gesperrte/spec-gesteuerte Tasks (Block 4, #1209) in genau einem Nachfolge-PR; max. 2 PRs je Phase. Ausnahmeliste zur strikten Ein-PR-Regel: #1086i, #1209, Regel 52.

## Offene Entscheidungen (neu, ungeklaert)

Nicht durch 17-57 gedeckt. Nicht geraten. Entscheidung im Spec-Schritt E-T7 mit User-Freigabe:

- **U5: Umfang Template-Gates.** Welche der 26 Templates; SE-Klassen mit `subdir`.
- **U6: Inhalt der Vertragsaenderung Kern-AC-05.** Welche Kern-Tests (Plan T10/T11) angepasst werden. Das Verfahren ist per E-N3 entschieden, der Inhalt nicht.

Beantwortet durch **Entscheidung 56** (in E-T7 Step 1 und E-T8 eingearbeitet): U1 (zwei Flags `_MODE_FILES`/`_MODE_INLINE`), U2 (Wert `files`, Issue-Text anpassen), U3 (Suffix-Match), U4 (Default true, kein Eintrag in `_FALSE_DEFAULT_CONDITIONALS`), U7 (Doku `docs/api/pal-variables.md`).
- (U8 beantwortet durch 50, siehe "Entscheidungen (beantwortet)".)
- (U9 geloest durch 36, siehe "Entscheidungen (beantwortet)".)
- (U10 beantwortet durch 49, siehe "Entscheidungen (beantwortet)".)

## Nicht verifiziert

- Es wurde nichts ausgefuehrt: keine Tests, kein `consistency-check.py`, kein `--validate`, kein `sync.py`. Alle "Erwartung"-Zahlen (Testanzahl, 0 Treffer) sind Planwerte.
- Status von #1189 und CI nicht abgerufen. #1187: Vormessung im Review 2026-11-11 (siehe E-C0), am Ausfuehrungstag wiederholen; Anker des #1187-Plans (Basis `aaed14c2`) nicht gegen `9aa0e0c0` nachgemessen (E-B0-T1 Step 2). Szenario-Zuordnung 95-98 je Modus ist Wrapper-Vorschlag, nicht aus Entscheidung 49. #1141 nicht geprueft (nicht Teil von E). `check_plan_refs.py`: existiert auf Branch `chore/check-plan-refs`, nicht in origin/main.
- Zeilenanker gegen origin/main `9aa0e0c0`: im Review 2026-11-11 alle Code-Anker des Plans nachgemessen (siehe "Frische-Check-Referenzen"). Bei Ausfuehrung nach Rebase erneut messen.
- Entscheidung 36 bestaetigt die Abspaltung von #1209; der Ablauf (Spec-Freigabe vor PR-Eroeffnung) ist durch den User nur fuer E-T7 als Gate bestaetigt, nicht fuer die Branch-Namen (Vorschlaege).
- Funktionsnamen aus Kern T6/T14 (`_build_artifact_variables`, `check_artifact_locations`) stammen aus dem Kernplan, nicht aus Code (existiert noch nicht).
- `pipeline_stages`-Zuordnung (`implement: 1`) gegen die Pipeline nicht geprueft.
- Effort: nicht berechnet, `effort-estimator` liefert die Schaetzung.
- Review 2026-11-11 hat gemessen (read-only, nichts committet): 18/22 `SE_BASE_DIR` per `grep -o`; Schema 70 Wurzel-Properties, Whitelist 47, Schnitt 39, 8 ohne Schema, 31 Schema ohne Whitelist (per `json`/`ast`); die 9 `docs/`-Unterbaeume und 4 Audit-Dateien existieren; Regex aus E-T2 meldet heute nur die 12 SE-Templates. Tests, `consistency-check.py`, `--validate` liefen nicht.

## Self-Review

- Jede Phase-E-Issue genau einmal (6 Issues): #1187 (E-B0-T1, E-B0-T2, Phasen-PR, Entscheidung 49), #1186 (E-T3, Kernplan, Phasen-PR), #1198 (E-T1, E-T2, Phasen-PR), #1199 (E-T4, Phasen-PR), #1200 (E-T5, E-T6, Phasen-PR), #1209 (E-T7, E-T8, Nachfolge-PR, Entscheidung 36/52).
- Kein TBD/TODO/Platzhalter in ausfuehrbaren Tasks; E-T8 ist ausdruecklich als blockiert markiert, bis E-T7 freigegeben ist.
- Signaturen mit Beleg (Stand 9aa0e0c0, re-gemessen): `_VAR_PATTERN` (`variables.py:136`), `_conditional_active` (`:604`), `strip_inactive_conditional_blocks` (`:662`), `check_placeholders` (`placeholders.py:196`), `Finding` (`report.py:29`), `PROJECT_WRITABLE_SECTIONS` (`admin-server.py:234`), `_assert_project_sections_writable` (`:5241`), `_assert_project_update_writable` (`:5257`). Signaturen des Kerns (E-T6) stammen aus dem Kernplan, nicht aus Code.
- Entscheidungen 17-36 und 49/50/52 eingearbeitet: E-N1 (17), E-N2 und E-N3 (34) beantwortet, Kette 19 und 35, #1209-Abspaltung 36 (U9 geloest). E-C0 eingearbeitet. Entscheidungen 49 (U10), 50 (U8), 52 eingearbeitet. Entscheidung 56 eingearbeitet (E U1-U4, U7 beantwortet; F nicht vor E-Kern); 54, 55, 57 nicht Phase E. Offen nur U5/U6 (Spec-Inhalte #1209).
- Tasks: E-C0 (Check), E-T0 (Vorbedingungen), E-B0-T1 (#1187-Plan T1..T15), E-B0-T2 (Szenarien 95-98), E-T1..E-T8 (Wrapper); Kernplan 23 Tasks (T1..T21, T23, T24, T22 entfaellt). Commit-Tasks ohne Kern: E-B0-T2, E-T1, E-T2, E-T4, E-T5, E-T6, E-T7; E-T8 blockiert bis E-T7 APPROVED.
- Keine Ausfuehrung, keine Tests gelaufen. Alle Zahlen sind Planwerte.
- Roadmap-Abweichungen und Kern-Konflikte: Abschnitt "Abweichung zur Roadmap und zum Kernplan" (13 Punkte; Punkt 5 und 12 durch Entscheidung 50 und 49 aktualisiert).
