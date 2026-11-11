---
pipeline_stages:
  implement: 2
---

# Phase H Kontext/Token/Eval Implementation Plan

> Status: DRAFT
> Revision: Entscheidungen 54 (O-H5: REQ-Format strikt ein Bereich) und 56 (O-H6: F-OC2 nur Befund; O-H7: G vor H mergen) eingearbeitet. O-H2 bleibt offen bis zur Task-19-Messung.
> Basis `origin/main 9aa0e0c0` (PR #1218 gemergt); file:line-Anker im Review 2026-11-11 gegen `9aa0e0c0` nachgemessen (`git show`/`git grep`), bei Ausfuehrung erneut messen (Roadmap §4 Freshness-Check). Roadmap-Phase **H**, Welle 4 (Abhaengigkeit laut Roadmap §3: B, C; Task 10 zusaetzlich nach Phase D). Parallelitaet zu G nur eingeschraenkt, siehe Abhaengigkeiten (Dateilisten nicht disjunkt). Entscheidungen 17-38 und 39-53 (Roadmap §7c; fuer H wirksam: 52) beruecksichtigt (Abschnitt "Entscheidungen (beantwortet)").
> Roadmap: `docs/superpowers/plans/2026-11-10-backlog-roadmap.md` (Entscheidung 11 bindend, Risiko "#969 Interface-Umbau").
> Issues (je genau einmal): #969, #1161, #1115, #1014, #778, #779, #780, #960, #1167, #1158 (Rest K-01, K-13), #1159 (Rest K-12, K-16, K-17, F-PA1, F-PA2, F-OC2). #977 ist Phase A (nur Querverweis, hier nicht bearbeitet).

**Goal:** Per-Testfall-Schnittstelle plus McNemar im Eval-Gate (#969), Rest-Token-Reduktion (#1161), Re-Pin-Helper (#1115), und die M/L/XL-Themen (#1014, #778, #779/#780, #960, #1167) bis zur freigegebenen Spec bringen; S-Reste aus #1158/#1159 direkt erledigen.
**Architecture:** Phase H hat hoechstens zwei PRs (Entscheidung 52, Ausnahme vom "ein PR je Phase" aus Entscheidung 17): PR H1 mit den derzeit ausfuehrbaren Tasks, PR H2 (Nachfolge-PR derselben Phase) mit den gesperrten/spec-gesteuerten Tasks; ein Commit je Task; die Bloecke sind nur Gliederung. Zuordnung: Abschnitt "PR-Schnitt". Eval-Gate bleibt rueckwaertskompatibel: ohne `per_case`-Daten gilt unveraendert das tau-Kriterium. Kein Eingriff in `scripts/lib/context.py` (Split #1086i, Phase C).
**Tech Stack:** Python 3.9+ (stdlib, PyYAML-Ausnahme), pytest, bash-Hooks.
**Spec:** docs/specs/2026-10-11-context-profiles-spec.md

Spec-Hinweis: gilt fuer #969 (Zeile 22 `Status: APPROVED`, IC-36 ab Zeile 1937). Alle anderen M/L/XL-Issues: Gate-Tasks 0, 8, 11, 14, 16, 19.

## Klassifikation (Spec/Plan-Gate)

| Issue | Klasse | Begruendung | Gate |
|---|---|---|---|
| #969 | M | Interface-Umbau `eval_gate.py` + Runner + Gate-Modul; IC-36 (McNemar "preferred") steht in der APPROVED Spec | Spec vorhanden |
| #1161 Pkt 4 | S | ein Aufrufpfad in `sync_pipeline.py` | direkt |
| #1161 Pkt 2 | M | aendert Render-Output (ac01-Pins) | Task 8 Spec, Entscheidung 29 (D-H2) |
| #1161 Pkt 5 | M | Security-Hooks; Issue: "decision task" | Pkt 5 bleibt in H (Entscheidung 28: "#1169 in Phase D, #1161 Punkt 5 in Phase H"); die gemeinsame Funktion `hook_json_get_many` entsteht mit Spec/User-Freigabe in Phase D (D-Task 5/7, D-Plan Z. 218 "Abstimmung mit Phase H"); H-Task 10 stellt die uebrigen Hooks um |
| #1115 | S | ein Helper-Skript + Doku-Zeile, Toleranzen unveraendert | direkt |
| #1014 | **XL** | 34 Rollen, 8 Muster, 4 PRs | Task 0 (Concept, dann Spec) |
| #778 | M | Design-Issue, F-1..F-6 ohne Umsetzungsbeschluss | Task 14 Concept/Spec |
| #779 | M (Rest IT-2, IT-4) | Rest ist Daten + Registrierungsentscheidung | Task 11 Spec |
| #780 | M | Generator (Design C) gebaut; Rest = Doku-Regel, Guard-Test, Beispieldaten | Task 11 Spec |
| #960 | L | `model_range` quer durch Config, Schema, Orchestrator | Task 16 Spec |
| #1167 | M | Format-Entscheidung + Validator + Template-Gating | Task 19 Spec + Entscheidung 34 (D-H4) |
| #1158 Rest (K-01, K-13) | S | Verifikation + Test | direkt |
| #1159 Rest | S je Punkt | Doku/Test/mechanisches Rename | direkt |

Keine Implementierungs-Task eines M/L/XL-Blocks ist ausfuehrbar, bevor die zugehoerige Gate-Task `Status: APPROVED` erreicht hat. Tasks sind pro Block markiert mit `Gate:`.

## Abhaengigkeiten / Reihenfolge

| Abhaengigkeit | Phase | Wirkung auf H |
|---|---|---|
| #1086i `context.py`-Split | C (zuletzt) | **Reihenfolge: H laeuft nach dem Split (Entscheidung 18: eigener PR direkt nach Phase C).** Task 7 (#1161 Pkt 4) fasst bewusst `context.py` nicht an (Backup-Schreiber `_backup_context_file` bleibt unveraendert, Prune-Erweiterung sitzt in `sync_pipeline.py`). Falls Spec/Review doch eine Aenderung an `_backup_context_file` verlangt, gehoert sie nach `scripts/lib/context_sync/base.py` und rebased auf den Split (siehe `2026-11-11-phase-c-1086i-context-split.md`, Modulschnitt-Tabelle L0). Vor dem Split ist #1161 nicht zu mergen, sobald `context.py` beruehrt wird. |
| #1182/#1183/#1208/#1085c | C | beruehren `context.py`/`_build_managed_block`; keine Dateiueberlappung mit Task 7, aber die Re-Pin-Tasks 6/13/21 rebasen auf deren `tests/test_context_budgets.py`-Pins. Phase C aendert ausserdem `templates/context/agents-managed.md` (C-Plan Z. 296, `gate-card` Z. 8) und `scripts/lib/sync_pipeline.py` (Retention-Konstanten `:969-970`, C-Plan Z. 119): Task 7 und Task 10b rebasen auf C |
| Phase D (Hooks, Guard) | D, Welle 3; Strom A (#1181) nach F (Entscheidung 19) | **`hook_json_get_many` entsteht in Phase D** (#1169: D-Task 5 Spec mit User-Freigabe, D-Task 7 Impl; Entscheidung 28, Roadmap Z. 424-427). H baut die Funktion nicht erneut. Reihenfolge: D-Spec -> D-Impl -> D gemergt -> H Task 10 (uebrige Hooks, #1161 Pkt 5). D aendert `hooks/1-generic/lib/hook_common.sh` und `orchestrator-guard-impl.sh` (#1210, #1217, #1169). H rebased nach D, nie parallel |
| Phase E/F (Templates/Presets) | E, F | Tasks 20/21 (REQ-Gating) beruehren `agents/1-generic/*.md` bzw. `scripts/lib/cli_commands.py` (`_handle_validate`, auch von E/F/C/D geaendert); nach E/F rebasen |
| Phase G (Provider) | G, Welle 4 (laut Roadmap parallel) | **Dateilisten nicht disjunkt:** G aendert `.meta-config/project.yaml` (G-Task 8), `config/ai-providers.yaml` (G-Tasks 3, 8, 9, 10; Opencode-`allowed-fields` `:387-414`, Kommentar `:399-405`) und `config/provider-capabilities.yaml` (G-Tasks 8, 9, 10). H aendert `.meta-config/project.yaml` (Task 17) und liest `config/ai-providers.yaml` (Tasks 23, 24) sowie `roster_in_harness` aus `config/provider-capabilities.yaml` (Task 10b). Roadmap §3 Regel "parallel nur bei disjunkter `Files:`-Liste" -> Tasks 17, 23, 24, 10b laufen sequentiell zu G (Reihenfolge: G merged vor H, Entscheidung 56 / O-H7). H aendert keine der beiden Provider-Config-Dateien |
| Phase C-1086i (`context.py`-Split) | eigener PR nach C (Entscheidung 18) | H aendert `scripts/lib/context.py` nicht: Task 7 nur `sync_pipeline.py`; Task 10b nur Template/Fixtures, weil `EMIT_AGENT_ROSTER` bereits unbedingt in `context.py:2777-2786` berechnet wird. Die Aussage im C-1086i-Plan Z. 26, #1161 Pkt 2/5 beruehrten `context.py`, trifft fuer Pkt 5 (Hooks) nicht zu; fuer Pkt 2 nur, falls die Spec (Task 8) eine Variablenaenderung verlangt (dann gegen `context_sync/managed_block.py` rebasen) |
| Phase A #977 | A | Tracker-Update dort; H setzt keinen Kommentar |

## PR-Schnitt (Entscheidung 52)

PR H1 enthaelt nur Tasks, die beim Schnitt ausfuehrbar sind; gesperrte/spec-gesteuerte Tasks laufen in PR H2 (max. 2 PRs je Phase). Gate-Tasks (Spec/Concept) stehen in H1, Commit erst mit `Status: APPROVED`; fehlt die Freigabe beim H1-Schnitt, wandert die Gate-Task mit ihren Folge-Tasks nach H2.

| Task | Issue | PR | Gate-Grund (falls H2 oder bedingt) |
|---|---|---|---|
| 1, 2, 3, 4 | #969 | H1 | — (Spec APPROVED, IC-36) |
| 5 | #969 | H2 | User-Gate Kosten (Entscheidung 11) und Tasks 1-4 gemergt (H1) |
| 6 | #1115 | H1 | — |
| 7 | #1161 Pkt 4 | H1 | — (H laeuft nach C/#1086i) |
| 8 | #1161 Pkt 2 | H1 (Gate-Task) | Spec-Freigabe; ohne APPROVED nach H2 |
| 9 | #1161 Pkt 5 | — | Abnahmeschritt, kein Commit |
| 10 | #1161 Pkt 5 | H2 | D-Abhaengigkeit: Phase D gemergt (`hook_json_get_many`, D-Task 7) |
| 10b | #1161 Pkt 2 | H2 | Spec-Gate Task 8; G merged vor H (Entscheidung 56) |
| 11 | #779/#780 | H1 (Gate-Task) | Spec-Freigabe; ohne APPROVED nach H2 |
| 12, 13 | #779/#780 | H2 | Spec-Gate Task 11 |
| 14 | #778 | H1 (Gate-Task) | Concept-Freigabe; ohne APPROVED nach H2 |
| 0 | #1014 | H1 (Gate-Task) | Concept/Spec-Freigabe; ohne APPROVED nach H2; #1014-Folgeplaene (Umsetzung) fallen unter Entscheidung 52 |
| 16 | #960 | H1 (Gate-Task) | Spec-Freigabe; ohne APPROVED nach H2 |
| 15 | #1159 K-12 | H1 | — |
| 17 | #1159 K-16/K-17 | H1 nur falls G gemergt, sonst H2 | G merged vor H (`.meta-config/project.yaml`, Entscheidung 56) |
| 18 | #1158 | H1 | — (H laeuft nach E/F) |
| 19 | #1167 | H1 (Gate-Task) | Spec-Freigabe; ohne APPROVED nach H2 |
| 20, 21 | #1167 | H2 | Spec-Gate Task 19 |
| 22 | #1159 F-PA1 | H1 | — (Phase C gemergt) |
| 23 | #1159 F-PA2 | H1 nur falls G gemergt, sonst H2 | G merged vor H (liest `config/ai-providers.yaml`, Entscheidung 56) |
| 24 | #1159 F-OC2 | H1 nur falls G gemergt, sonst H2 | G merged vor H (Entscheidung 56); nur Befundnotiz, keine Listenaenderung in H (Entscheidung 56 / O-H6) |

Nicht durch Entscheidung 52 geregelt (offen, keine Annahme): was gilt, wenn eine Gate-Task auch beim H2-Schnitt nicht APPROVED ist.

## Global Constraints

- Python 3.9 kompatibel (`from __future__ import annotations`, kein `X | Y` zur Laufzeit, kein `match`; `math.comb` ist ab 3.8 verfuegbar).
- Nur stdlib + PyYAML (ADR 0001). Provider-agnostisch ueber Config-Keys/Capability-Flags, kein `if provider == "Name"`.
- Commits: Conventional Commits, Englisch, <= 72 Zeichen, ein Commit pro Task (Entscheidung 17). Hoechstens zwei Phase-H-PRs (H1, H2; Entscheidung 52), Zuordnung laut Abschnitt "PR-Schnitt". Commit-/PR-Texte spaeter als Datei.
- Kein Worktree-Isolation-Argument. Tests: `python3 -m pytest <datei>::<test>`; zusaetzlich `python3 scripts/sync.py --validate`.
- Commit-Trailer kommen woertlich aus dem Task-Prompt (Entscheidung 25); keine eigene Trailer-Vorgabe in diesem Plan. PR- und Commit-Texte ohne Closing-Schluesselwoerter (Closes/Fixes/Resolves; Entscheidung 38e); `(#NNNN)` als reiner Verweis ist erlaubt. Issues werden in H nicht geschlossen.
- Destruktive Git-Befehle werden nie umgangen; blockiert der Guard, liefert der Assistent die fertigen Befehle und der User fuehrt sie per `!` aus (Roadmap §4).
- **Keine kostenpflichtigen Laeufe** in diesem Plan (LLM-/Agent-/Eval-Laeufe, API-Kosten). Task 5 ist ein User-Gate; er wird nie automatisch ausgefuehrt: erst `--estimate-only`, dann Kostenschaetzung zeigen, dann nur nach ausdruecklichem User-Ja (Entscheidung 11). Dasselbe gilt fuer jeden Eval-Lauf aus Folgeplaenen (#1014 Verhaltens-Evalfaelle, Task 0).
- Toleranz-Konstanten in `tests/test_context_budgets.py` (`TOLERANCE_MAX_BYTES`, `TOLERANCE_MIN_BYTES`, `TOLERANCE_RATIO`) bleiben unveraendert.
- Golden-/Hash-Fixtures (`tests/fixtures/ac01-baseline/hashes.json`, `tests/fixtures/slimming-golden/*`) nur mit dokumentiertem Grund neu pinnen; kein Neu-Einfrieren um einen roten Test zu loeschen.
- Hook-Aenderungen: Header-`version`/`changelog` in `hook_common.sh` pflegen; deployte Kopie `.agents/hooks/lib/hook_common.sh` wird durch Sync erzeugt, nicht von Hand editiert.

## Abweichung zur Roadmap (in W gelesen)

1. **#969:** `eval_gate.py:28-33` bestaetigt "Deliberately deferred: paired McNemar". Roadmap-Verdikt TEILWEISE stimmt. Baseline-Run ist in `scripts/run_role_routing_eval.py:930ff` (`main`) fertig verdrahtet inkl. `eval_gate.run_with_approval` (`:1021`) und `build_baseline` (`:287`); kein Runner-Code fehlt fuer den Lauf selbst. Offen ist nur der User-Gate-Schritt.
2. **#1161 Pkt 1:** gebaut (`scripts/lib/agents.py:541`, `separators=(",", ":")`; `name_index` weiter vorhanden in `agents.py:364`, Konsument `_routing_name_only_entries` `:423`; Issue-Anker `agents.py:515` stammt von `96f5a2e5`). Re-Pin-Kommentar G7 in `tests/test_context_budgets.py:291-299`. Ob `name_index` Duplikate (3,5k Tokens) noch enthaelt: nicht verifiziert.
3. **#1161 Pkt 3:** gebaut: `rules/1-generic/branch-guard.md` verweist die Luecken-Liste auf `docs/concepts/branch-guard-known-limits.md` (Zeile 21); die Abschnitte "Guard-Terminologie" (Z. 5) und "Bekannte Grenzen" (Z. 18) stehen aber weiterhin im always-on Rule-Text, nur gekuerzt. Roadmap "Punkt 3 gebaut" nur teilweise belegt; wird in Task 8 mit Messung geklaert.
4. **#1161 Pkt 4:** Roadmap sagt offen. In W existiert `prune_sync_backups` (`scripts/lib/generated_file_drift.py:199`), aufgerufen ueber `_prune_managed_sync_backups` (`scripts/lib/sync_pipeline.py:1029`) mit `SYNC_BACKUP_MAX_PER_SOURCE = 3` (`:970`) fuer `skills_dir`, `agents_dir`, `hooks_dir`, `rules_dir`, `commands_dir` und das Pipeline-Details-Verzeichnis (`_managed_dirs_for_prune`, `:981-1026`). Die "168 Backups im Agent-Verzeichnis" sind damit seit #1081 abgedeckt. Offen bleibt nur das Verzeichnis der Kontextdatei (Backups aus `_backup_context_file`, `scripts/lib/context.py:197-212`) -> Task 7. Roadmap-Anker `context.py:204` ist die Zeile `backup = target_path.with_name(...)` innerhalb der Funktion ab `:197`.
5. **#1161 Pkt 5:** `hook_common.sh` liegt unter `hooks/1-generic/lib/hook_common.sh` (nicht `hook_common.sh:63` im Root); `hook_json_get` ab Zeile 63, ein `python`-Prozess pro Feld. 28 Aufrufe in 6 Dateien (`orchestrator-guard-impl.sh` 9, `repo-containment-impl.sh` 5, `lifecycle-check.sh` 3, `sync-on-config-change.sh` 2, `dod-push-check.sh` 2, `hook_common.sh` 7 inkl. interner Nutzung; `git grep -c -w` auf `9aa0e0c0` bestaetigt). Zuordnung Entscheidung 28: #1169 (Funktion + `orchestrator-guard-impl.sh`) in Phase D, #1161 Pkt 5 in H; H-Task 10 stellt die uebrigen vier Hooks um.
6. **#1115:** Issue-Anker `tests/test_context_budgets.py:270` (`_IST_FULL`) und `:524` (`_IST_COMPACT`) sind veraltet: `_IST_FULL` steht auf `:300`, `_IST_COMPACT` auf `:583`. `measure_artifacts` ist `scripts/lib/context_report.py:130`.
7. **#779:** IT-1 (`openscad-developer` hat `routing_patterns`) und IT-5 (Daten-Duplikat; `routing.intent_keywords` existiert nicht mehr, `tests/test_routing_tool_definitions.py:47`) sind gebaut. IT-3/IT-6/IT-7: Tests `tests/test_routing_overlap.py` und `tests/test_routing_keyword_overlap_check.py` existieren (Inhalt nicht gelesen). IT-2: `agents/1-generic/provider-expert.md` existiert, in `config/role-defaults.yaml` kein Eintrag (0 Treffer) -> offen. IT-4: offen (Daten).
8. **#780:** Design C ist generatorseitig gebaut: `scripts/lib/delegation_table.py:229` `_select_examples` mit sprachgetaggten Mappings, Fallback-INFO `routing.examples-language-fallback`, Test `tests/test_routing_tool_definitions.py:219`. Offen: AC1 (dokumentierte Regel), AC3 (DE-Daten je Rolle: `config/role-defaults.yaml:189-190` zeigt noch flache Listen), AC4 (Guard-Test gegen sprachspezifische Keywords). Der Code-Kommentar `delegation_table.py:253` nennt das selbst "passthrough-only until bilingual data exists".
9. **#1158 K-01:** Templates sind gegated (`agents/1-generic/orchestrator.md:385-386`, `principal-developer.md:171`, `senior-developer.md:164`). Gerenderte Dateien (`.claude/agents/`) liegen in W nicht im Repo; Drift gegen gerenderten Output nicht pruefbar -> Task 18. **K-13:** der Issue-Anker `config.py:2337-2338` zeigt auf Issue-Basis `96f5a2e5` auf `PROJECT_SPECIFIC_AGENTS` (auf `9aa0e0c0`: `config.py:2379-2381`), nicht auf einen True/False-Default; `standalone.py:130-134` hat `_CONDITIONAL_FALSE_FLAGS` (alle `false`). Der "inkonsistente Default" ist so nicht reproduzierbar -> Task 18 klaert den eigentlich gemeinten Schalter.
10. **#1159 F-PA2:** Der Default `"Opencode"` existiert in `rules.py` nicht mehr (`provider: str` ohne Default bei `:436`, `:498`; Default `"Claude"` bei `:605`). Offen: Literale als Dict-Keys in `external_tools_drift.py:186-190` (`_INFRA_ROOT_FALLBACK_DIRS`). `providers.py:358` ist die eingebettete Fallback-Registry fuer fehlendes `ai-providers.yaml` und laut `tests/test_provider_agnostic_dispatch.py:367-369` bewusst vom Literal-Guard ausgenommen ("owns the framework default provider ... by design").
11. **#1159 K-12:** `config/project-config.schema.json:1160-1162` markiert `mcp-registry` bereits als "DEPRECATED — no longer read"; Treffer in `scripts/lib/mcp.py:427,477` und `mcp_provider_config.py:409-664` sind nur Log-Labels. Roadmap "offen" -> faktisch dokumentiert; Task 15 verifiziert und schliesst ab.
12. **#1159 F-PA1:** Funktionen liegen in `scripts/lib/isolation.py` (`_sync_opencode_runtime_gate` `:796`, `rollback_opencode_runtime_gate` `:1204`, `reconcile_opencode_surface_gate` `:1915`), importiert in `cli_commands.py:241-245` (Aufrufe `:327`, `:340`, `:372`) und `sync_pipeline.py:91-95` (Aufrufe `:917`, `:1636`, `:1652`), zusaetzlich `scripts/lib/deactivation.py:259-261`. Stand `9aa0e0c0` (`git grep -c -w`): 29 Zeilen in 4 Lib-Dateien, 53 Zeilen in 9 Testdateien (nicht 39 in 6).
13. **#1167:** Issue-Belege nicht alle reproduzierbar: `docs/REQUIREMENTS.md:4` nennt zwei Formate (`REQ-xxx` dreistellig oder thematisch `REQ-CMD-xx`); `config/role-defaults.yaml` hat REQ-Text bei `:179-200` und `:2668` (`REQ-ID vergeben`), nicht `:2694`; ungegated sind `validator.md:53` und `bug-feature-analyzer.md:42,84,134`; `validator.md:38-39` liegt im Block `{{#if DOD_REQ_TRACEABILITY}}` `:35-41` (gegated), ebenso `:97`.
14. `scripts/check_plan_refs.py` liegt nicht auf `origin/main`, sondern im Review-Worktree `.tmp/wt-check-plan-refs/scripts/`; nackte `:NNNN`-Anker prueft es nicht (von Hand nachmessen).
15. **#1161 Pkt 2:** Das Capability-Flag existiert bereits: `roster_in_harness` in `config/provider-capabilities.yaml` (true: Claude `:140`, Opencode `:199`, Mammouth `:452`, Codex `:526`, ZCode `:599`, KimiCode `:667`; false: Gemini `:256`, Continue `:322`, Copilot `:383`). `context.py:2764-2786` leitet daraus `EMIT_AGENT_ROSTER` ab (Safe-Side ueber alle Teiler einer Kontextdatei), aber `templates/context/agents-managed.md:20-21` gated nur den Compact-Zweig; im Default-Profil `full` rendert `{{> agents-table }}` unbedingt. Rest von Pkt 2 = Full-Profil-Zweig an dasselbe Flag haengen.

## Entscheidungen (beantwortet)

Quelle: Roadmap-Entscheidungen 17-34 (`docs/superpowers/plans/2026-11-10-backlog-roadmap.md`, User-beantwortet, bindend). Originale Plan-IDs in Klammern.

| Nr. | Entscheidung | Wirkung auf diesen Plan |
|---|---|---|
| 17 | Ein PR je Phase, ein Commit je Task | PR-Teil durch Entscheidung 52 ergaenzt (H1/H2); Commit-Regel gilt; Task 0 und Task 10 auf je einen Commit |
| 18 | `context.py`-Split (#1086i) ist eigener PR direkt nach Phase C | H laeuft nach dem Split (Abhaengigkeiten) |
| 19 | Kette #1187 -> #1186 -> #1188 -> #1181 -> #1141 | H nach F und nach D-Strom A (#1181); #1187 ist nicht Teil dieses Plans |
| 11 | #969: Baseline-Run planen UND McNemar; Baseline nur nach Kostenschaetzung und User-Ja | Tasks 1-4 (McNemar, Per-Testfall), Task 5 User-Gate |
| 25 | #1168: Trailer aus dem Task-Prompt, Git-Agent uebernimmt wortgleich | Dieser Plan enthaelt keine Trailer-Vorgabe (Global Constraints) |
| 28 | (D-H1) `hook_json_get_many`: JSON einmal parsen, NUL-getrennt, `read -r -d ''`, bash 3.2, kein `eval`; Spec vorab mit User-Freigabe. "#1169 in Phase D, #1161 Punkt 5 in Phase H" | Funktion entsteht in Phase D (#1169: D-Task 5 Spec, D-Task 7 Impl). H-Task 9 entfaellt (keine doppelte Implementierung). H-Task 10 = #1161 Pkt 5 fuer die vier uebrigen Hooks, erst nach D-Merge |
| 29 | (D-H2) Agent-Verzeichnis in AGENTS.md nur fuer Provider ohne eigene Agent-Liste, per Capability-Flag (z.B. `roster_in_harness`), kein Provider-Namens-Branching | Flag existiert bereits (Abweichung Nr. 15); Task 8 Spec (Pkt 2) haengt den Full-Profil-Zweig daran; Umsetzung als Task 10b aus der Spec |
| 30 | #339-Spec braucht erneute User-Freigabe, keine weitere Planung davor | Task 19 grenzt nur ab; #339 wird in H nicht geplant; #339 passt sich bei seiner Neufreigabe an das strikte Format an (Entscheidung 54) |
| 36 | Ausnahmen vom Ein-PR-Schnitt nur #1086i und #1209 | Durch Entscheidung 52 ergaenzt (siehe dort) |
| 38e | Keine Closing-Schluesselwoerter in PR-/Commit-Texten | Global Constraints |
| 34 | (D-H3) Deutsche Routing-Keywords bleiben; Guard-Test friert die Menge ein | Tasks 11/12: Allowlist = Ist-Menge, neue sprachspezifische Keywords verboten |
| 34 | (D-H4) Format `REQ-<AREA>-<NN>` (kanonisch, #1167) | Tasks 19-21: ein Format; Ziffernzahl offen (O-H2) |
| 54 | (O-H5) REQ-Format STRIKT ein Bereich `REQ-<BEREICH>-<NN>`, keine mehrteiligen Bereiche; #339 (`REQ-L2-AT-018`) passt sich bei seiner Neufreigabe an (Entscheidung 30) | Tasks 19-20: Bereichs-Segment ohne `-`; Fixture `REQ-L2-AT-018` wird abgelehnt |
| 56 | (O-H6) F-OC2 nur Befund, Allow-Liste erst nach G-N4-Evidenz; (O-H7) G vor H mergen | Task 24 nur Befundnotiz; Tasks 10b, 17, 23, 24 nach G-Merge |
| 34 | (D-H5) `provider-expert` wird als `name_only` registriert | Task 11 Spec, Task 13 Eintrag in `config/role-defaults.yaml` |
| 52 | Phasen-PR nur mit derzeit ausfuehrbaren Tasks; gesperrte/spec-gesteuerte Tasks im Nachfolge-PR derselben Phase, max. 2 PRs je Phase; weitere Ausnahme neben #1086i und #1209; #1014-Folgeplaene fallen darunter | Architecture, Global Constraints, Abschnitt "PR-Schnitt" (H1/H2); beantwortet O-H4 und O-H8; Task 0 |

Durch Code bzw. Entscheidung geklaert (Review 2026-11-11, keine User-Frage mehr):

- **O-H1 (erledigt):** Flag-Name und -Ort stehen im Code: `roster_in_harness` in `config/provider-capabilities.yaml` (Abweichung Nr. 15); Provider-Liste ist Messwert (Gemini, Continue, Copilot `false`). Task 8 uebernimmt beides, kein neues Flag.
- **O-H3 (erledigt):** `lifecycle-check.sh` (3) und `sync-on-config-change.sh` (2) gehoeren laut Entscheidung 28 ("#1161 Punkt 5 in Phase H") zu H-Task 10.
- **O-H4 (beantwortet, Entscheidung 52):** Der Phase-H-PR wartet nicht auf alle Gates: H1 geht mit den ausfuehrbaren Tasks, gesperrte/spec-gesteuerte Tasks (5, 10, 10b, 12-13, 20-21 und Gate-Tasks ohne Freigabe) laufen in H2. Siehe "PR-Schnitt".
- **O-H8 (beantwortet, Entscheidung 52):** Die #1014-Folgeplaene fallen unter Entscheidung 52 und laufen in Phase H im Nachfolge-PR H2, nicht "One PR per step" (`.tmp/issues/1014.md:133`). Damit ist auch der PR-Schnitt-Teil des frueheren Konflikts zwischen dieser Issue-Vorgabe und Entscheidung 36 erledigt.

## Offene Entscheidungen (neu, ungeklaert)

- **O-H2 (Entscheidung 34, D-H4):** Ziffernzahl im Regex (`\d{2}` woertlich nach `<NN>`, alternativ `\d{2,3}` wegen `REQ-xxx` dreistellig in `docs/REQUIREMENTS.md:4`). Task 19 Step 1 misst vorher die hoechste vergebene Nummer je Bereich.
- ~~**O-H5 (Entscheidung 30 vs. D-H4):**~~ **Beantwortet durch Entscheidung 54** (strikt ein Bereich `REQ-<BEREICH>-<NN>`, keine mehrteiligen Bereiche; #339 passt sich bei Neufreigabe an). Urspruengliche Frage: #339 schlaegt ein REQ-Format `REQ-L2-AT-018` vor (`.tmp/issues/339.md:47`: mehrteiliger Bereich, dreistellig), D-H4 setzt `REQ-<AREA>-<NN>`. Darf die #1167-Spec (Task 19) mehrteilige Bereiche zulassen, oder bleibt die Abstimmung bis zur #339-Neufreigabe offen?
- ~~**O-H6 (#1159 F-OC2 vs. G-N4):**~~ **Beantwortet durch Entscheidung 56** (F-OC2 nur Befund, Allow-Liste erst nach G-N4-Evidenz; Task 24 dokumentiert nur). Urspruengliche Frage: Das Issue verlangt "Align the list with the schema" (`max_tokens`, `subagent` in `config/ai-providers.yaml:396,407`); G-N4 (Entscheidung 34) laesst Opencode-Keys bis zur Probe-Evidenz unveraendert, und die Datei gehoert in Welle 4 G. Darf H die Allow-Liste aendern, oder nur den Befund belegen (Task 24)?
- ~~**O-H7 (Roadmap §3, Parallelitaet G/H):**~~ **Beantwortet durch Entscheidung 56:** G merged vor H.

## File Structure

- Modify: `scripts/lib/eval_gate.py` — `mcnemar_exact`, Per-Testfall-Pfad in `evaluate_gate`, Docstring-Update (Tasks 1-2).
- Modify: `scripts/run_role_routing_eval.py` — `compute_case_outcomes`, `per_case` im Baseline-Dokument (Task 3).
- Modify: `scripts/lib/context_profile_gate.py` — `_as_candidate` reicht `per_case` durch (Task 4).
- Modify: `tests/test_eval_gate.py`, `tests/test_eval_baseline_schema.py`, `tests/test_context_profile_gate.py` (Tasks 1-4).
- Create: `scripts/measure_context_repin.py`, `tests/test_context_repin_helper.py` (Task 6); Modify: `rules/2-platform/agent-meta-conventions.md` (Task 6).
- Modify: `scripts/lib/sync_pipeline.py` (`_managed_dirs_for_prune`), `tests/test_generated_file_drift.py` (Task 7).
- Create: `docs/specs/2026-11-11-context-token-1161-spec.md` (Task 8); danach Modify: `templates/context/agents-managed.md`, `tests/fixtures/ac01-baseline/hashes.json`, `tests/test_context_budgets.py` (Task 10b, gated; kein Eingriff in `config/provider-capabilities.yaml`, Flag existiert); `hooks/1-generic/repo-containment-impl.sh`, `hooks/1-generic/dod-push-check.sh`, `hooks/1-generic/lifecycle-check.sh`, `hooks/1-generic/sync-on-config-change.sh`, `tests/fixtures/ac01-baseline/hashes.json` (gerenderte Hook-Kopien sind gepinnt, z.B. Z. 102, 107, 116, 118) (Task 10, nach Phase D). `hooks/1-generic/lib/hook_common.sh`, `hooks/1-generic/orchestrator-guard-impl.sh`, `tests/test_hook_common_lib.py` gehoeren Phase D (Entscheidung 28).
- Create: `docs/concepts/evidence-discipline-1014.md`, `docs/specs/2026-11-11-evidence-discipline-1014-spec.md` (Task 0).
- Create: `docs/specs/2026-11-11-routing-language-779-780-spec.md` (Task 11); danach Create: `tests/test_routing_language_guard.py` (Task 12); Modify: `config/role-defaults.yaml`, `tests/test_routing_tool_definitions.py`, `docs/guides/` Regel-Absatz (Tasks 12-13).
- Create: `docs/concepts/cross-cutting-findings-778.md` (Task 14).
- Create: `docs/specs/2026-11-11-model-range-960-spec.md` (Task 16).
- Create: `docs/specs/2026-11-11-req-id-format-1167-spec.md` (Task 19); danach Create `scripts/lib/consistency/req_format.py` und `tests/test_req_id_format.py`; Modify: `scripts/lib/cli_commands.py` (`_handle_validate` `:1408`, Registrierung neben `check_temp_literals` `:1507`), Templates/Presets laut Task 20-21.
- Create: `tests/test_dod_gating_rendered.py` (Task 18).
- Create: `docs/analysis/evidence/2026-11-11-opencode-allow-list-f-oc2.md` (F-OC2, Task 24).
- Modify (Doku/Config): `.meta-config/project.yaml` (K-17), `docs/REQUIREMENTS.md` (K-17/K-11 nur falls Spec verlangt), `CLAUDE.md`-Abschnitt "Eigene Notizen" (K-16, wird von Sync nicht ueberschrieben) (Task 17).
- Modify: `scripts/lib/isolation.py`, `scripts/lib/cli_commands.py`, `scripts/lib/sync_pipeline.py`, `scripts/lib/deactivation.py` und 9 Testdateien (F-PA1, Task 22); `scripts/lib/external_tools_drift.py`, `tests/test_provider_agnostic_dispatch.py` (F-PA2, Task 23; `providers.py` bleibt, siehe Abweichung Nr. 10).

---

## Block A: #969 Eval-Gate (M, Spec vorhanden: IC-36 in context-profiles-spec)

Design (aus gelesenem Code abgeleitet): `compute_metrics` (`run_role_routing_eval.py:186`) bildet je Fall ein `grades`-Dict mit `correct`, `collision`, `wrong_pipeline`, `clarified` und verwirft es nach der Aggregation. Neu: `compute_case_outcomes` liefert `{case_id: {"correct": bool, "collision": bool, "ambiguous_expected": bool, "wrong_pipeline": bool, "clarified": bool}}` (Schluessel wie im heutigen `grades`-Dict, `run_role_routing_eval.py:200-216`). Das Baseline-Dokument bekommt optional `per_case = {model_class: {case_id: [0|1 je Run fuer "correct"]}}`. `evaluate_gate(baseline, candidate, k=2.0, alpha=0.05)` (heute `evaluate_gate(baseline, candidate, k=2.0)`, `eval_gate.py:331`; einziger Aufrufer `context_profile_gate.py:103`): besitzen beide Seiten `per_case`, wird fuer `top1_accuracy` (nur diese Metrik; `per_case` traegt nur `correct`) zusaetzlich ein exakter McNemar-Test auf den gepaarten Faellen gefahren (Baseline-Ausgang je Fall = Mehrheit ueber die Baseline-Laeufe, ties -> falsch). `failed`, wenn der Test eine signifikante Verschlechterung (p < alpha, c > b) zeigt ODER das tau-Kriterium reisst. Ohne `per_case` bleibt das Verhalten byte-identisch (Rueckwaertskompatibilitaet, vorhandene Tests `tests/test_eval_gate.py` bleiben gruen).

### Task 1: `mcnemar_exact` (pure Funktion)

**Agent:** `tester` (Test), `developer` (Impl). **Depends on:** —. **Gate:** keins (Spec vorhanden). **Files:** Modify `scripts/lib/eval_gate.py`, `tests/test_eval_gate.py`. **Interfaces:** Produces `eval_gate.mcnemar_exact(b: int, c: int) -> float` (zweiseitiger exakter Binomial-p-Wert; Konvention: `c` = Baseline richtig, Kandidat falsch; `b` = Baseline falsch, Kandidat richtig; Verschlechterung = `c > b` und p < alpha). Consumes: `math.comb`.
- [ ] Step 1: Tests in `tests/test_eval_gate.py` (fail): `test_mcnemar_no_discordant_pairs`: `eg.mcnemar_exact(0, 0) == 1.0`; `test_mcnemar_symmetric`: `eg.mcnemar_exact(3, 3) == 1.0`; `test_mcnemar_known_value`: `abs(eg.mcnemar_exact(0, 8) - 2 * 0.5**8) < 1e-12` (= 0.0078125); `test_mcnemar_is_symmetric_in_arguments`: `eg.mcnemar_exact(2, 9) == eg.mcnemar_exact(9, 2)`; `test_mcnemar_rejects_negative`: `pytest.raises(ValueError)` fuer `(-1, 2)`.
- [ ] Step 2: `python3 -m pytest tests/test_eval_gate.py -k mcnemar -q` -> Erwartung: 5 failed (AttributeError).
- [ ] Step 3: Implementieren: `n = b + c`; `n == 0 -> 1.0`; `k = min(b, c)`; `p = 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2**n`; `return min(1.0, p)`; Negativ-Eingaben -> `ValueError`.
- [ ] Step 4: Schritt-2-Befehl -> 5 passed; `python3 -m pytest tests/test_eval_gate.py -q` komplett gruen.
- Akzeptanz: alle fuenf Tests gruen, kein bestehender Test rot.
- Commit: `feat(eval): add exact McNemar test to eval_gate`

### Task 2: `evaluate_gate` mit Per-Testfall-Pfad

**Agent:** `tester`, `developer`. **Depends on:** 1. **Files:** Modify `scripts/lib/eval_gate.py` (Funktion `evaluate_gate` `:331`, Docstring-Kopf `:28-33`), `tests/test_eval_gate.py`. **Interfaces:** Produces `evaluate_gate(baseline: dict, candidate: dict, k: float = 2.0, alpha: float = 0.05) -> str`; Schema-Erweiterung `baseline["per_case"] = {cls: {case_id: [0|1, ...]}}`, `candidate["per_case"] = {cls: {case_id: 0|1}}` (nur fuer `top1_accuracy`). Consumes `mcnemar_exact`.
- [ ] Step 1: Tests (fail): (a) `test_per_case_absent_is_unchanged`: bestehender Gate-Fall ohne `per_case` liefert dasselbe Ergebnis wie vorher (Referenz: vorhandener Test, nicht neu schreiben); (b) `test_mcnemar_significant_regression_fails`: Baseline-Aggregate und Kandidaten-Aggregat innerhalb tau (Kandidat = Baseline-Mittel - 0.5 pp), aber `per_case` mit 12 Faellen, Baseline Mehrheit richtig, Kandidat in 10 davon falsch und in 0 umgekehrt (p = 2/1024 < 0.05; synthetische Fixture, das Gate prueft Aggregat und `per_case` nicht gegeneinander) -> `eg.evaluate_gate(base, cand) == eg.FAILED`; (c) `test_mcnemar_insignificant_stays_passed`: 3 diskordante Paare (c=3, b=0 -> p=0.25) -> `PASSED`; (d) `test_per_case_corpus_mismatch_is_not_evidenced`: Case-ID-Menge von Baseline und Kandidat verschieden -> `NOT_EVIDENCED`; (e) `test_per_case_invalid_value_is_not_evidenced`: Wert `2` oder `True` -> `NOT_EVIDENCED`, nie Exception.
- [ ] Step 2: `python3 -m pytest tests/test_eval_gate.py -q` -> Erwartung: (b), (d), (e) failed.
- [ ] Step 3: Implementieren. Hilfsfunktion `_paired_regression(base_runs_by_case: Mapping, cand_by_case: Mapping, alpha: float) -> Optional[bool]` (None = nicht auswertbar -> `unevidenced`). Mehrheit: `sum(runs) * 2 > len(runs)`. Docstring-Kopf: den "Deliberately deferred"-Absatz durch eine Beschreibung des Per-Testfall-Pfads ersetzen.
- [ ] Step 4: `python3 -m pytest tests/test_eval_gate.py tests/test_context_profile_gate.py -q` -> alles gruen.
- Akzeptanz: (b) `FAILED`, (c) `PASSED`, (d)/(e) `NOT_EVIDENCED`; Rueckwaertskompatibilitaet durch unveraenderte Bestandstests belegt.
- Commit: `feat(eval): use paired McNemar when per-case results exist`

### Task 3: Runner liefert Per-Testfall-Ergebnisse

**Agent:** `tester`, `developer`. **Depends on:** 2. **Files:** Modify `scripts/run_role_routing_eval.py` (`compute_metrics` `:186`, `run_class` `:769`, `build_baseline` `:287`, `validate_baseline` `:363`), `tests/test_eval_baseline_schema.py`. **Interfaces:** Produces `compute_case_outcomes(cases: Sequence[dict], predictions: Mapping[str, Optional[dict]]) -> Dict[str, dict]`; `build_baseline` schreibt `per_case` (Schema-Version bleibt `SCHEMA_VERSION = 1`, Feld optional; `validate_baseline` akzeptiert fehlendes Feld). Consumes: `compute_metrics`-Gradelogik (bestehende `normalize_target`, kein zweiter Matching-Pfad).
- [ ] Step 1: Tests (fail): `test_compute_case_outcomes_matches_metrics`: mit den `CASES` aus der Testdatei und einer Prediction-Map gilt `mean(correct) * 100 == compute_metrics(...)["top1_accuracy"]` (Konsistenz, keine zweite Wahrheit); `test_build_baseline_includes_per_case`: Ergebnis hat `per_case[cls][case_id] == [1, 0, 1]` bei drei Laeufen; `test_validate_baseline_accepts_missing_per_case`; `test_validate_baseline_rejects_non_binary_per_case`.
- [ ] Step 2: `python3 -m pytest tests/test_eval_baseline_schema.py -q` -> Erwartung: 4 neue failed.
- [ ] Step 3: Implementieren: `compute_metrics` ruft intern `compute_case_outcomes` (Refactor ohne Ergebnisaenderung); `run_class` haengt je Lauf `"case_outcomes"` an das Run-Dict; `build_baseline` aggregiert.
- [ ] Step 4: `python3 -m pytest tests/test_eval_baseline_schema.py tests/test_eval_gate.py -q` gruen. Kein Provider-Aufruf, kein Netz.
- Akzeptanz: Konsistenztest gruen; bestehende Baseline-JSONs unter `tests/routing-llm-eval/roles/baseline/` (falls vorhanden) validieren weiter.
- Commit: `feat(eval): record per-case outcomes in role-routing baseline`

### Task 4: `context_profile_gate` reicht `per_case` durch

**Agent:** `tester`, `developer`. **Depends on:** 2, 3. **Files:** Modify `scripts/lib/context_profile_gate.py` (`_as_candidate` `:52`), `tests/test_context_profile_gate.py`. **Interfaces:** Consumes `evaluate_gate`; Produces Candidate mit `per_case` (Mehrheit je Fall ueber die Laeufe des Kandidatendokuments).
- [ ] Step 1: Test (fail): `test_as_candidate_collapses_per_case`: Dokument mit `per_case` `{cls: {"c1": [1,1,0]}}` ergibt Candidate-`per_case` `{cls: {"c1": 1}}`; `test_gate_state_uses_mcnemar`: zwei JSON-Dokumente (`profile: full` Baseline, `profile: compact` Kandidat, beide `evidence.status: evidenced`) mit signifikanter Per-Fall-Verschlechterung ergeben `context_profile_gate_state(root) == "not-evidenced"`.
- [ ] Step 2: `python3 -m pytest tests/test_context_profile_gate.py -q` -> Erwartung: 2 failed.
- [ ] Step 3: Implementieren (`_as_candidate` um `per_case`-Kollaps erweitern; Baseline-Dokument geht unveraendert durch `dict(baseline)`).
- [ ] Step 4: Schritt-2-Befehl gruen; `python3 -m pytest tests/test_eval_gate.py tests/test_eval_baseline_schema.py -q` gruen.
- Akzeptanz: beide Tests gruen; ohne `per_case` identisches Verhalten.
- Commit: `feat(eval): pass per-case results through context profile gate`

### Task 5: User-Gate Baseline-Run (nie automatisch ausfuehren)

**Agent:** `main_chat` (User-Entscheidung), danach `tester` fuer den Lauf. **Depends on:** 1-4 gemergt. **Files:** keine Aenderung im Plan; Lauf erzeugt `tests/routing-llm-eval/roles/baseline/<datum>-<label>-<profil>.json` (Name aus `baseline_filename`, `run_role_routing_eval.py:520`) oder `runs/<datum>-qg1-<label>.json` (Skip-Record).
- [ ] Step 1 (ohne Kosten): `python3 scripts/run_role_routing_eval.py --estimate-only --model-class <name>=<provider>/<modell> --repeat 3 --price-date <ISO-Datum> --price-source <Quelle>` ausfuehren (Format `NAME=PROVIDER/MODEL`, `run_role_routing_eval.py:18,644`; Flags in `build_parser` `:830-907`: `--model-class` `:844`, `--repeat` `:854`, `--approval` `:865`, `--estimate-only` `:875`, `--price-date` `:893`, `--price-source` `:898`; `--estimate-only` ruft keinen Provider, `:17`, Ende bei `:985`). Erwartung: Ausgabe von `eval_gate.format_estimate` mit Fallzahl x Modelle x Laeufe, Kosten in USD und `evidence preview`.
- [ ] Step 2: Schaetzung (Kosten, Preisquelle, `UNVERIFIED`-Hinweis) dem User zeigen. **Stopp.** Ohne ausdrueckliches "yes"/"ja" ist `SKIPPED-BY-USER` ein gueltiges Ergebnis: Gate zaehlt als "not proven", `compact` bleibt opt-in, keine Doku darf Verifikation behaupten.
- [ ] Step 3 (nur nach User-Ja, mit `--approval yes`): Lauf mit mindestens zwei Modellklassen und `--repeat 3` (AC-02: `MIN_MODEL_CLASSES = 2`, `MIN_BASELINE_RUNS = 3`, `eval_gate.py:53-54`); danach `python3 -m pytest tests/test_eval_baseline_schema.py -q`.
- Akzeptanz: entweder Skip-Record mit `status == "SKIPPED-BY-USER"` oder Baseline mit `evidence.status` gesetzt und gueltigem Schema; **dieser Plan fuehrt Step 3 nie selbst aus.**
- Commit (nur falls Baseline-Datei entsteht und freigegeben ist): `test(eval): add role-routing baseline run`

---

## Block B: #1115 Re-Pin-Helper (S)

### Task 6: Helper, der den Re-Pin-Block ausgibt

**Agent:** `tester`, `developer`. **Depends on:** —. **Files:** Create `scripts/measure_context_repin.py`, `tests/test_context_repin_helper.py`; Modify `rules/2-platform/agent-meta-conventions.md` (Zeile 84, Absatz "Budget-Re-Pin"). **Interfaces:** Produces `scripts/measure_context_repin.py::format_repin_block(report: Mapping[str, Mapping], pins: Mapping[str, Mapping[str, int]], name: str) -> str` und `main(argv=None) -> int` (`0` = keine Abweichung, `1` = Block gedruckt). Consumes `lib.context_report.measure_artifacts(project_root, active_providers, capabilities)` (`context_report.py:130`), `tests.test_context_budgets._IST_FULL`/`_IST_COMPACT` (`:300`, `:583`; Import zieht `pytest` als Laufzeitabhaengigkeit des Helpers nach, akzeptabel fuer ein Dev-Skript), `_make_project` (`tests/test_ac01_render_identity.py:1083`).
- [ ] Step 1: Test (fail): `test_format_repin_block_lists_only_changed_artifacts`: `report={"Claude": {"orchestrator": {"bytes": 80000}}}`, `pins={"Claude": {"orchestrator": 72183}}` -> Ausgabe enthaelt `"Claude": {` und `"orchestrator": 80000` plus die Delta-Zeile `Claude/orchestrator: 72183 -> 80000 (+7817)`; `test_no_delta_returns_empty`; `test_tolerance_constants_untouched`: liest `tests/test_context_budgets.py` als Text und assertet, dass `TOLERANCE_MAX_BYTES = 4096`, `TOLERANCE_MIN_BYTES = 256`, `TOLERANCE_RATIO = 0.02` vorkommen (Schutz gegen Aufweichen, AC3 des Issues).
- [ ] Step 2: `python3 -m pytest tests/test_context_repin_helper.py -q` -> Erwartung: failed (ImportError).
- [ ] Step 3: Implementieren: Helper misst alle `_PROVIDERS` wie die `measured`-Fixture (`test_context_budgets.py:341-354`), vergleicht je Artefakt `bytes > _ceiling(pin)` nur zur Meldung, druckt aber **jede** Abweichung `bytes != pin` als einfuegefertigen Block (Verifikation bleibt menschlich). Rule-Text in `agent-meta-conventions.md:84` um den Aufruf `python3 scripts/measure_context_repin.py` ergaenzen (Entdeckung vor CI). Hinweis: `.claude/skills/conventions/SKILL.md` ist eine generierte Datei und liegt nicht im Tree von `origin/main`; die Quelle ist die Regel-Datei.
- [ ] Step 4: `python3 -m pytest tests/test_context_repin_helper.py tests/test_context_budgets.py -q` gruen; manueller Lauf `python3 scripts/measure_context_repin.py` auf unveraendertem Stand -> Exit 0 (Erwartung; nicht verifiziert, siehe Nicht verifiziert).
- Akzeptanz: Block fuer synthetische Abweichung exakt wie im Test; Toleranzkonstanten unveraendert.
- Commit: `chore(tests): add context budget re-pin helper (#1115)`

---

## Block C: #1161 Token-Reduktion Rest (Pkt 4 S, Pkt 2 M, Pkt 5 Task 10; Funktion `hook_json_get_many` aus Phase D)

### Task 7: Pkt 4, Backups im Verzeichnis der Kontextdatei prunen

**Agent:** `tester`, `developer`. **Depends on:** — (kein `context.py`-Eingriff, siehe Reihenfolge). **Files:** Modify `scripts/lib/sync_pipeline.py` (`_managed_dirs_for_prune` `:981`), `tests/test_generated_file_drift.py`. **Interfaces:** Produces: `_managed_dirs_for_prune` liefert zusaetzlich das Elternverzeichnis von `pc["context_file"]` (Schluessel laut `context_report.py:156`), sofern vorhanden; Consumes `prune_sync_backups(target_dir, project_root, log, dry_run, max_age_days, max_per_source)` (`generated_file_drift.py:199`).
- [ ] Step 1: Test (fail) `test_prune_includes_context_file_dir`: `tmp_path` mit `CLAUDE.md` und fuenf `CLAUDE.md.sync-backup-2026110{1..5}-120000`; `provider_config={"Claude": {"context_file": "CLAUDE.md", "agents_dir": ".claude/agents"}}`, `config` mit aktivem Claude; nach `_prune_managed_sync_backups(tmp_path, config, provider_config, argparse.Namespace(dry_run=False), log)` (Signatur `sync_pipeline.py:1029-1032`) existieren genau 3 Backups (die neuesten), `CLAUDE.md` unveraendert. Zweiter Test: nicht-Backup-Dateien im Wurzelverzeichnis bleiben unangetastet.
- [ ] Step 2: `python3 -m pytest tests/test_generated_file_drift.py -k context_file_dir -q` -> Erwartung: failed (5 statt 3).
- [ ] Step 3: Implementieren: `specs`-Liste (`sync_pipeline.py:997-1006`) um `str(Path(pc["context_file"]).parent)` erweitern, wenn `context_file` gesetzt (Wurzel -> `.`); dedupe laeuft ueber `seen`.
- [ ] Step 4: Schritt-2-Befehl gruen; `python3 -m pytest tests/test_generated_file_drift.py tests/test_managed_index_alignment.py tests/test_cleanup_preview_cli.py -q` gruen.
- Akzeptanz: genau 3 verbleibende Backups je Quelle im Wurzelverzeichnis; `--cleanup-preview` (`_preview_backups_to_prune`, `sync.py:622`, nutzt `select_prunable_sync_backups`) bleibt unveraendert; es zeigt nur das Agent-Zielverzeichnis (`sync.py:676ff`) und deckt schon heute weder Rules noch Skills ab.
- Commit: `fix(sync): prune sync backups next to the context file (#1161)`

### Task 8: Mini-Spec #1161 Pkt 2 + Freigabe-Gate (Spec-Gate; Pkt-5-Spec in Phase D)

**Agent:** `concept-specifier`, Review `concept-reviewer`, Freigabe User. **Depends on:** Entscheidung 29 (D-H2); Pkt 5 nicht hier (Entscheidung 28, Phase D Task 5). **Files:** Create `docs/specs/2026-11-11-context-token-1161-spec.md`. **Interfaces:** Produces Spec mit `Status: APPROVED`.
- [ ] Step 1: Messung vorab (Skript unter `.tmp/`, nicht committen): Tokenproxy von `rules/1-generic/branch-guard.md` (Pkt 3 Restbestand), `name_index`-Anteil (`agents.py:364`), Agent-Directory-Groesse je Provider. Ergebnis in die Spec.
- [ ] Step 2: Spec: Verzeichnis nur ohne eigene Agent-Liste (Entscheidung 29) ueber das vorhandene Flag `roster_in_harness` und die vorhandene Variable `EMIT_AGENT_ROSTER` (`context.py:2777-2786`, Safe-Side-Regel fuer geteilte Kontextdateien); Aenderung nur im Full-Zweig von `templates/context/agents-managed.md:20-21`; betroffene Provider laut `config/provider-capabilities.yaml` (Abweichung Nr. 15), ac01-/Budget-Re-Pin-Plan fuer Pkt 2, messbare Akzeptanzkriterien (Render-Groesse je Provider vorher/nachher). Pkt 5 (`hook_json_get_many`, Fail-closed, bash 3.2, Spawn-Zahl) steht in der Phase-D-Spec; hier nur verlinken.
- [ ] Step 3: Review + `Status: APPROVED`.
- Akzeptanz: Datei enthaelt die Zeile `Status: APPROVED`; `python3 scripts/sync.py --validate` ohne neuen Fehler. Ohne diese Zeile ist Task 10b nicht ausfuehrbar.
- Commit: `docs: add spec for context token reduction (#1161)`

### Task 9: `hook_json_get_many` entfaellt in Phase H (Entscheidung 28)

**Owner:** Phase D (#1169). Die Funktion wird dort in D-Task 5 spezifiziert (User-Freigabe vor Implementierung) und in D-Task 7 implementiert (`hooks/1-generic/lib/hook_common.sh`, Tests in `tests/test_hook_common_lib.py`). Phase H baut sie nicht ein zweites Mal. Interface, Fail-closed-Semantik und bash-3.2-Regeln: siehe Phase-D-Spec.
- [ ] Step 1: Vor Task 10 pruefen (`Grep hook_json_get_many` in `hooks/1-generic/lib/hook_common.sh`), dass D-Task 7 gemergt ist.
- Akzeptanz: Funktion vorhanden, Phase-D-Tests gruen. Kein H-Commit in diesem Task.
- Commit: keiner (Abnahmeschritt).

### Task 10: Restaufrufe auf `hook_json_get_many` umstellen (Gate: Phase D gemergt)

**Agent:** `senior-developer`. **Depends on:** Phase D gemergt (D-Task 7). **Files:** Modify `hooks/1-generic/repo-containment-impl.sh` (5 Aufrufe, erster `:209`), `hooks/1-generic/dod-push-check.sh` (2, `:98-99`), `hooks/1-generic/lifecycle-check.sh` (3, `:24-26`), `hooks/1-generic/sync-on-config-change.sh` (2, `:24-25`) (Stand `9aa0e0c0`; vor Start per `git grep -c -w hook_json_get` neu zaehlen), `tests/fixtures/ac01-baseline/hashes.json` (gerenderte Hook-Kopien gepinnt, Re-Pin mit Grund). Entfaellt fuer `repo-containment-impl.sh`/`dod-push-check.sh`, falls der optionale Schritt von D-Task 7 (D-Plan Z. 248) sie bereits umgestellt hat. `orchestrator-guard-impl.sh` gehoert Phase D. **Interfaces:** Consumes `hook_json_get_many <json> <path>...` (D-Plan Z. 239: je Pfad ein NUL-terminiertes Feld; ohne Default-Argument). `lifecycle-check.sh:26` nutzt heute den Default `"0"` von `hook_json_get`; leeres Feld dort auf `0` abbilden.
- [ ] Step 1: Vorab Basis: `python3 -m pytest tests/test_repo_containment_hook.py tests/test_dod_push_check_hook.py tests/test_lifecycle_check_args.py tests/test_hook_common_lib.py tests/test_hook_smoke_optin.py -q` gruen (Ausgangslage notieren).
- [ ] Step 2: Pro Hook Felder in einem Aufruf lesen (`while IFS= read -r -d '' v; do ...; done < <(hook_json_get_many ...)`), Fail-closed-Pfade (`hook_json_usable`, `hook_known_tool_name`) unveraendert. Header-`version`/`changelog` der geaenderten Hooks anheben.
- [ ] Step 3: Suite aus Step 1 nach jedem Hook gruen; `python3 -m pytest tests/test_ac01_render_identity.py -q` nach Re-Pin gruen; Python-Spawns pro Bash-Call vorher/nachher als Zahl in die PR-Notiz.
- Akzeptanz: Guard-Verhalten identisch (alle bestehenden Hook-Tests gruen); Spawn-Zahl je Hook sinkt auf 1 Parse-Aufruf fuer die Felder.
- Commit (ein Commit, Entscheidung 17): `perf(hooks): parse hook payload once in remaining hooks (#1161)` (anderer Betreff als der optionale D-Commit, D-Plan Z. 248)

(Pkt 2, Agent-Directory: Entscheidung 29 beantwortet, Flag `roster_in_harness` vorhanden (Abweichung Nr. 15); Umsetzung als eigene Task erst nach Task 8; Dateien siehe File Structure. Eine Task-Skizze ohne freigegebene Spec waere Raterei, daher bewusst hier nicht ausformuliert; sie entsteht als Task 10b aus der Spec heraus.)

---

## Block D: #779 / #780 Routing-Sprache (M)

### Task 11: Mini-Spec (Spec-Gate) #779 Rest + #780

**Agent:** `concept-specifier`, `concept-reviewer`, User. **Depends on:** Entscheidung 34 (D-H3, D-H5). **Files:** Create `docs/specs/2026-11-11-routing-language-779-780-spec.md`. **Interfaces:** Produces Spec `Status: APPROVED`.
- [ ] Step 1: Ist-Tabelle IT-1..IT-7 und AC1-AC5 mit file:line-Beleg (Abschnitt "Abweichung zur Roadmap" Nr. 7/8 als Ausgangspunkt; Inhalte von `tests/test_routing_overlap.py` und `tests/test_routing_keyword_overlap_check.py` vorher lesen).
- [ ] Step 2: Spec: kanonische-Keyword-Regel (AC1), Pilotrollen fuer DE-Beispiele (AC3), Guard-Test (AC4) inkl. Allowlist (D-H3), Entscheidung `provider-expert` (Entscheidung 34, D-H5: registrieren als `addressability: name_only` mit Grund), Abgrenzung zu #1167 nicht noetig.
- [ ] Step 3: Review + `Status: APPROVED`.
- Akzeptanz: Zeile `Status: APPROVED` vorhanden; Tasks 12-13 sonst nicht ausfuehrbar.
- Commit: `docs: add spec for routing language and keyword hygiene (#779, #780)`

### Task 12: Guard-Test gegen sprachspezifische Keywords (Gate: Task 11)

**Agent:** `tester`, `developer`. **Depends on:** 11. **Files:** Create `tests/test_routing_language_guard.py`; Modify `docs/guides/` (Absatz zur Keyword-Regel; Zieldatei in der Spec festlegen). **Interfaces:** Consumes `scripts.lib.roles.load_roles_config(_AGENT_META_ROOT)["roles"]` (`roles.py:53`; Muster `tests/test_routing_tool_definitions.py:29,47-49`), `scripts.lib.delegation_table._select_examples(examples, language, *, role="", info_sink=None) -> list[str]` (`delegation_table.py:229`).
- [ ] Step 1: Tests (fail): `test_keywords_are_canonical`: kein Keyword ausserhalb der in der Spec eingefrorenen Allowlist enthaelt deutsche Umlaute oder DE-Stoppwoerter (Liste in der Spec); bestehende DE-Keywords bleiben erlaubt (Entscheidung 34, D-H3); `test_examples_language_variants_resolve`: fuer jede Rolle mit dict-`examples` loest `_select_examples(examples, "Deutsch")` und `("English")` jeweils eine nicht-leere Liste; `test_keyword_coverage_unchanged`: Anzahl Rollen mit `routing_patterns.keywords` >= Wert vor dem Task (Zahl aus Spec).
- [ ] Step 2: `python3 -m pytest tests/test_routing_language_guard.py -q` -> Erwartung: mindestens `test_keywords_are_canonical` failed, solange die Allowlist nicht eingefroren ist.
- [ ] Step 3: Allowlist einfrieren (aus Ist-Daten, Stand W), Doku-Absatz schreiben.
- [ ] Step 4: Test gruen; `python3 -m pytest tests/test_routing_tool_definitions.py tests/test_routing_overlap.py -q` gruen.
- Akzeptanz: AC1 (dokumentiert) und AC4 (Guard) erfuellt.
- Commit: `test(routing): guard canonical keywords and example languages`

### Task 13: DE/EN-Beispiele fuer Pilotrollen (Gate: Task 11, 12)

**Agent:** `developer`. **Depends on:** 12. **Files:** Modify `config/role-defaults.yaml` (Pilotrollen laut Spec; Struktur `examples: {Deutsch: [...], English: [...]}`; Eintrag `provider-expert` mit `addressability: name_only` plus `name_only_reason` (Feldmuster `config/role-defaults.yaml:107-108`) laut Spec, D-H5 / Entscheidung 34), `tests/test_routing_tool_definitions.py` (neuer Test). **Interfaces:** Consumes `get_routing_rules(agent_meta_root, config, variables, pipelines=None, *, template_roles=None, warn_sink=None, language="en", info_sink=None, active_set=None) -> dict` (`delegation_table.py:289-299`; Muster `tests/test_routing_tool_definitions.py:219-275`, Sprachschluessel `Deutsch`/`English`).
- [ ] Step 1: Test (fail) `test_pilot_roles_render_language_specific_examples`: fuer jede Pilotrolle liefert `get_routing_rules` mit `language="Deutsch"` andere Beispiele als mit `"English"`; `keywords` identisch.
- [ ] Step 2: `python3 -m pytest tests/test_routing_tool_definitions.py -k pilot -q` -> failed.
- [ ] Step 3: Daten ergaenzen; `python3 scripts/sync.py --validate`.
- [ ] Step 4: Test gruen; `python3 -m pytest tests/test_routing_tool_definitions.py tests/test_routing_lines_compact.py -q` gruen; ac01/Budget-Tests laufen (Orchestrator-Output wechselt), Re-Pin per Helper aus Task 6 mit Grund im Kommentar.
- Akzeptanz: AC3 (DE-Projekt bekommt DE-Beispiele, EN-Projekt EN, aus derselben Keyword-Quelle); AC5 (keine Coverage-Verluste); D-H5 (`provider-expert` als `name_only` registriert).
- Commit: `feat(routing): add German and English examples for pilot roles`

---

## Block E: #778 und #1014 Design/XL (Gate-only)

### Task 14: #778 Concept (Spec-Gate)

**Agent:** `concept-specifier`, `concept-reviewer`, User. **Depends on:** —. **Files:** Create `docs/concepts/cross-cutting-findings-778.md`. **Interfaces:** Produces je Finding F-1..F-6 eine Disposition (umsetzen/verwerfen/abspalten) mit file:line-Beleg im aktuellen Stand.
- [ ] Step 1: F-1 (Referenzstandard-Feld), F-2 (Boundary zentral; Belege: `requirements.md`/`ideation.md` "Boundary to planner"), F-3 (`config/review-rules/*.yaml` fuer alle Review-Rollen), F-4 (MCP-Bedarf), F-6 (`provider-expert` -> Entscheidung 34, D-H5; `intern-developer` nie echte Arbeit) einzeln gegen den Code pruefen.
- [ ] Step 2: Concept mit Dispositionen; Umsetzungstasks entstehen erst nach `Status: APPROVED` in einem Folgeplan.
- Akzeptanz: Concept enthaelt eine Tabelle F-1..F-6 mit Disposition und Beleg; `Status: APPROVED` durch User. Keine Template-Aenderung in diesem Plan.
- Commit: `docs: add concept for cross-cutting role findings (#778)`

### Task 0: #1014 Concept, dann Spec (XL-Gate)

**Agent:** `concept-specifier`, `concept-reviewer`, User. **Depends on:** Task 14 (gemeinsamer Hintergrund: #1014 setzt die Linie von #778 fort). **Files:** Create `docs/concepts/evidence-discipline-1014.md`, `docs/specs/2026-11-11-evidence-discipline-1014-spec.md`. **Interfaces:** Produces freigegebene Spec; Folgeplan je Sequenzschritt (Issue: Step 1 P5+P7, Step 2 P1, Step 3 P3+P4, Step 4 P2+P6+P8; je ein Folgeplan, nicht Teil dieses Plans; die Folgeplaene laufen laut Entscheidung 52 im Nachfolge-PR H2 der Phase H).
- [ ] Step 1: Concept: Rollenliste je Muster (Issue verweist auf `UEBERGREIFENDE-MUSTER.md`, nicht im Repo, nicht verifiziert), Dedupe-Check gegen expandierten Text (Substitutionsbloecke wie `{{PROMPT_INJECTION_DEFENSE_BLOCK}}`), Abgrenzung zu PR #1013 (gemergt).
- [ ] Step 2: Spec je Sequenzschritt: Dateiliste (`agents/1-generic/<rolle>.md` + `tests/routing-llm-eval/catalog.behavior.yaml`), Version-Bumps, Golden-Fixture-Rebaseline nur fuer eingefrorene Rollen (`tests/fixtures/slimming-golden/`), Akzeptanzkriterien aus dem Issue (u.a. `python3 scripts/gen_promptfoo_config.py --check` frisch; `tests/test_agents_frontmatter.py`, `tests/test_agent_eval_framework.py`, `tests/test_contract_labels.py`, `tests/test_context_compact_mode.py` gruen). Das Issue-Kriterium "eval case fails when the sentence is removed" (`.tmp/issues/1014.md:78`) braucht LLM-Laeufe: in der Spec als kostenpflichtig markieren, nur nach Kostenschaetzung und User-Ja (Global Constraints). PR-Schnitt der Folgeplaene: Entscheidung 52 (H2; O-H8 beantwortet).
- [ ] Step 3: Review + `Status: APPROVED`; danach separater Folgeplan (nicht Teil dieses Plans).
- Akzeptanz: Concept und Spec vorhanden, Spec-Zeile `Status: APPROVED`. Roadmap-Konsequenz: P1-P8 querschnittlich offen bleibt bis Folgeplaene laufen; #1014 wird hier nicht geschlossen.
- Commit (ein Commit, Entscheidung 17): `docs: add concept and spec for evidence discipline (#1014)`

---

## Block F: #960 (L, Spec zuerst)

### Task 16: Spec `model_range` (Spec-Gate)

**Agent:** `concept-specifier`, `concept-reviewer`, User. **Depends on:** —. **Files:** Create `docs/specs/2026-11-11-model-range-960-spec.md`. **Interfaces:** Produces Spec, Folgeplan danach.
- [ ] Step 1: Ist-Stand pruefen (nichts gebaut: `git grep model_range origin/main` = 0 Treffer, Review 2026-11-11), Betroffene Stellen aus dem Issue (`config/role-defaults.yaml`, `config/project-config.schema.json`, `scripts/lib/roles.py`, `agents/1-generic/orchestrator.md` §4, `scripts/lib/sync_pipeline.py`, `config/tier-presets.yaml`) gegen W lesen und Anker in der Spec belegen.
- [ ] Step 2: Spec: Mapping S/M/L/XL -> Tier-Stufe, Klammerung, `tier_override`-Interaktion, Schema `min <= max`, Opt-in-Rueckwaertskompatibilitaet, Akzeptanzkriterien aus dem Issue.
- [ ] Step 3: Review + `Status: APPROVED`.
- Akzeptanz: Spec mit `Status: APPROVED`; Implementierung erst im Folgeplan.
- Commit: `docs: add spec for tier-range model routing (#960)`

---

## Block G: #1158/#1159 Reste (S, je Punkt direkt)

### Task 18: K-01/K-13 verifizieren und per Test absichern (#1158)

**Agent:** `tester`. **Depends on:** — (nach Phase E/F rebasen, siehe Abhaengigkeiten). **Files:** Create `tests/test_dod_gating_rendered.py`. **Interfaces:** Consumes die Render-Fixture aus `tests/test_ac01_render_identity.py::_make_project`; Preset `rapid-prototyping` (`config/dod-presets.yaml:54-55`, `DOD_REQ_TRACEABILITY=false`).
- [ ] Step 1: Test (zuerst als Messung): rendert ein Projekt mit Preset `rapid-prototyping` und assertet fuer `agents_dir/orchestrator`-Datei, dass `"No feature without REQ-ID"` und `"No code without tests"` nicht vorkommen (K-01); die Zeilen im Template liegen bei `agents/1-generic/orchestrator.md:385-386`. Erwartung: gruen, falls K-01 nur ein veralteter Render war. Rot -> echter Befund, in Spec/Issue melden, Task stoppt.
- [ ] Step 2: K-13: Mit `Grep` nach dem Schalter suchen, der bei `config.py` und `standalone.py` unterschiedliche Defaults hat (kandidat: Pipeline/Spec-Plan-Schalter `spec-plan-*`, siehe `dod.py:281,374`); gefundenen Unterschied als Test festschreiben oder im Issue als nicht reproduzierbar dokumentieren (Kommentar-Text als Datei bereitstellen).
- [ ] Step 3: `python3 -m pytest tests/test_dod_gating_rendered.py -q` und `python3 scripts/sync.py --validate`.
- Akzeptanz: Test gruen (K-01 belegt) und K-13 entweder per Test belegt oder mit Beleg als "nicht reproduzierbar" an das Issue uebergeben (Kommentar durch Phase-A/User, nicht hier).
- Commit: `test(dod): assert rapid-prototyping render has no REQ/test mandates`

### Task 17: K-16, K-17 (Doku), #1159

**Agent:** `documenter`. **Depends on:** —. **Files:** Modify `.meta-config/project.yaml` (`REQ_CATEGORIES`, Z. 259-262; G-Task 8 aendert dieselbe Datei; G merged vor H, Entscheidung 56), CLAUDE.md-Abschnitt "Eigene Notizen" (Sync ueberschreibt ihn nicht, siehe Kopfkommentar in `CLAUDE.md`). **Interfaces:** keine.
- [ ] Step 1: K-17: Kategorien (`project.yaml:259`, gerendert ueber `templates/context/partials/project-metadata.md:48-52`, `{{REQ_CATEGORIES_LIST}}`) mit den Ueberschriften aus `docs/REQUIREMENTS.md` (Z. 9, 26, 34, 42, 51, 84, 100, 110) abgleichen; im Zweifel `project.yaml` anpassen (Doku-Seite bleibt Quelle der Wahrheit). Reihenfolge der Entscheidung in der PR-Notiz.
- [ ] Step 2: K-16: Ein Satz unter "Eigene Notizen": dieses Meta-Repository hat kein `.claude/3-project/`.
- [ ] Step 3: `python3 scripts/sync.py` und `python3 scripts/sync.py --validate`; Diff der generierten `CLAUDE.md` prueft nur den Kategorienblock.
- Akzeptanz: `Grep` der Kategorienamen aus `project.yaml` findet je einen gleichnamigen `## `-Abschnitt in `docs/REQUIREMENTS.md`; `--validate` ohne neuen Fehler.
- Commit: `docs: align requirement categories and note missing 3-project (#1159)`

### Task 15: K-12 verifizieren und abschliessen

**Agent:** `tester`. **Depends on:** —. **Files:** Modify `tests/test_provider_agnostic_dispatch.py` oder neue `tests/test_mcp_registry_key_unread.py`. **Interfaces:** Consumes `config/project-config.schema.json:1160`.
- [ ] Step 1: Test (gruen erwartet): Schema-Beschreibung von `mcp-registry` enthaelt `"DEPRECATED"`; Quellcode unter `scripts/lib/` liest `config["mcp-registry"]`/`.get("mcp-registry")` nirgends (nur Log-Labels `mcp-registry/...` und `mcp-registry →`).
- [ ] Step 2: `python3 -m pytest tests/test_mcp_registry_key_unread.py -q` -> gruen. Rot -> es gibt einen Leser; dann K-12 als "Doku vs. Code" im Issue belassen.
- Akzeptanz: Test gruen, K-12 mit Evidenz abschliessbar.
- Commit: `test(schema): pin mcp-registry as deprecated and unread (#1159)`

### Task 22: F-PA1 provider-neutrale Namen

**Agent:** `senior-developer`. **Depends on:** Phase C (isolation/sync_pipeline-Aenderungen) gemergt. **Files:** Modify `scripts/lib/isolation.py` (`:796`, `:1204`, `:1915`), `scripts/lib/cli_commands.py` (`:241-245`, `:327`, `:340`, `:372`), `scripts/lib/sync_pipeline.py` (`:91-95`, `:917`, `:1636`, `:1650-1674`), `scripts/lib/deactivation.py` (`:248`, `:259-261`), `tests/test_orchestrator_topology_entrypoint.py`, `tests/test_issue_1020_gate_rollback.py`, `tests/test_opencode_main_chat_entry_point.py`, `tests/test_runtime_gate_wiring.py`, `tests/test_opencode_v2_surface.py`, `tests/test_opencode_runtime_gate.py`, `tests/test_isolation_v2_topology_reconcile.py`, `tests/test_orchestrator_mode_topology_matrix.py` (Stand `9aa0e0c0`, `git grep -l -w`). **Interfaces:** Produces `sync_runtime_gate`, `rollback_runtime_gate`, `reconcile_surface_gate` (gleiche Signaturen wie die bisherigen Funktionen, vor dem Rename in `isolation.py` ablesen). Kein Verhaltenswechsel. Klasse S: rein mechanisch (82 Zeilen in 13 Dateien; Doku-Treffer ausserhalb `scripts/`/`tests/` bleiben unveraendert).
- [ ] Step 1: Test (fail) `test_isolation_exports_neutral_names`: `hasattr(lib.isolation, "sync_runtime_gate")` usw.; `test_no_opencode_named_gate_functions_in_generic_loop`: `cli_commands.py` und `sync_pipeline.py` enthalten die Zeichenfolgen `opencode_runtime_gate`/`opencode_surface_gate` nicht mehr.
- [ ] Step 2: Befehl `python3 -m pytest tests/test_provider_agnostic_dispatch.py -q` Basis gruen notieren; neue Tests rot.
- [ ] Step 3: Rename in Quelle und Tests; **keine** Alias-Funktionen (Alias wuerde die Namenslast behalten). Kommentar-/Docstring-Verweise `isolation._opencode_runtime_gate_entries` in `scripts/lib/consistency/topology.py:115` und `scripts/lib/consistency/orchestrator_strict.py:93` nur umbenennen, wenn die Funktion selbst umbenannt wird (nicht Teil dieses Tasks).
- [ ] Step 4: `python3 -m pytest tests/test_opencode_runtime_gate.py tests/test_opencode_v2_surface.py tests/test_issue_1020_gate_rollback.py tests/test_runtime_gate_wiring.py tests/test_isolation_v2_topology_reconcile.py tests/test_orchestrator_mode_topology_matrix.py tests/test_provider_agnostic_dispatch.py tests/test_ac01_render_identity.py -q` gruen; volle Suite gruen.
- Akzeptanz: `git grep -w -E '_sync_opencode_runtime_gate|rollback_opencode_runtime_gate|reconcile_opencode_surface_gate' -- scripts tests` leer; ac01-Hashes unveraendert (kein Render-Effekt).
- Commit: `refactor(isolation): use provider-neutral gate function names`

### Task 23: F-PA2 Provider-Literale als Dict-Keys

**Agent:** `tester`, `developer`. **Depends on:** — (Test-Teil sofort). **Files:** Modify `scripts/lib/external_tools_drift.py` (`_INFRA_ROOT_FALLBACK_DIRS` `:186-190`), `tests/test_provider_agnostic_dispatch.py`. `scripts/lib/providers.py:358` bleibt: eingebettete Fallback-Registry, bewusst ausgenommen (`tests/test_provider_agnostic_dispatch.py:367-369`). **Interfaces:** Consumes `scripts.lib.providers.load_providers_config`; Default-Provider bleibt `"Claude"` (`providers.py:563` liest bereits `config.get("default-provider", "Claude")`, `rules.py:605`, `setup.py:235,239`).
- [ ] Step 1: Tests (fail) in `tests/test_provider_agnostic_dispatch.py` (Muster `test_no_provider_literal_usage_in_lib` `:363`): `test_external_tools_drift_defaults_are_config_driven`: Standardpfade fuer `hooks_dir`/`rules_dir`/`commands_dir` werden aus `config/ai-providers.yaml` gelesen, nicht aus Literalen; `test_default_provider_is_consistent`: alle Default-Stellen (`providers.py:563`, `rules.py:605`, `setup.py:235,239`) liefern denselben Wert wie ein gemeinsamer Zugriff (Konstante oder Config-Key `default-provider`).
- [ ] Step 2: `python3 -m pytest tests/test_provider_agnostic_dispatch.py -q` -> neue Tests failed.
- [ ] Step 3: Implementieren: Literal-Keys durch Config-Lookup ersetzen. Falls der Lookup die Funktionssignatur aendert, in der Task-Notiz festhalten.
- [ ] Step 4: Test gruen, `python3 -m pytest tests/test_external_tools_drift_catalog_ref.py tests/test_external_tools_registry.py -q` gruen (`tests/test_external_tools_drift.py` existiert nicht), `python3 scripts/sync.py --validate`.
- Akzeptanz: Provider-agnostischer Dispatch-Test deckt beide Stellen ab.
- Commit: `refactor(providers): drop provider literals from drift defaults`

### Task 24: F-OC2 verifizieren (nur Befund belegen, Entscheidung 56)

**Agent:** `tester`. **Depends on:** G-Merge (G vor H, Entscheidung 56 / O-H7). **Files:** Create `docs/analysis/evidence/2026-11-11-opencode-allow-list-f-oc2.md` (Befundnotiz); `config/ai-providers.yaml` wird in H nicht geaendert. **Interfaces:** Consumes `Opencode.agent-transform.allowed-fields` (`config/ai-providers.yaml:387-414`, enthaelt `max_tokens` `:396` und `subagent` `:407`; Issue-Anker `~381-394` veraltet). Die Issue-Liste `steps, top_p, disable, prompt` steht in keiner Repo-Datei (`git grep` in `docs/` ohne Treffer); sie stammt laut Issue aus der Opencode-Dokumentation (extern).
- [ ] Step 1: Allow-Liste lesen; Quelle der Doku-Liste belegen (Opencode-Doku-URL mit Abrufdatum oder vorhandene Evidenz `docs/analysis/evidence/2026-09-30-runtime-opencode-v{1,2}.md`, `docs/analysis/2026-09-30-provider-audit-docs-part1.md:241,248`).
- [ ] Step 2: Befundnotiz: je Key `max_tokens`, `subagent` (und `top_p`, `disable`, `prompt`) Status VERIFIED/DOKU/UNVERIFIED mit Beleg. Kein Test auf externe Doku (nicht stabil).
- [ ] Step 3: Keine Listenaenderung in H (Entscheidung 56 / O-H6): F-OC2 endet in H mit der Befundnotiz; eine Allow-Listen-Aenderung erst nach G-N4-Probe-Evidenz, ausserhalb von H.
- Akzeptanz: Befundnotiz mit Beleg je Key; `config/ai-providers.yaml` in H unveraendert.
- Commit: `docs(opencode): record allow-list evidence for F-OC2 (#1159)`

---

## Block H: #1167 REQ-ID-Format (M)

### Task 19: Spec (Spec-Gate)

**Agent:** `concept-specifier`, `concept-reviewer`, User. **Depends on:** Entscheidung 34 (D-H4, Format `REQ-<AREA>-<NN>`), Entscheidung 54 (strikt ein Bereich). **Files:** Create `docs/specs/2026-11-11-req-id-format-1167-spec.md`. **Interfaces:** Produces Spec mit Regex-Konstante (Form `^REQ-[A-Z][A-Z0-9]*-\d{N}$` mit `re.fullmatch`: genau ein Bereichs-Segment ohne `-`, Entscheidung 54; `N` laut O-H2) und Liste aller zu aendernden Stellen (Abschnitt "Abweichung zur Roadmap" Nr. 13 als Ausgangspunkt, Belege neu lesen).
- [ ] Step 1: Alle REQ-Stellen per `Grep REQ-ID|REQ-xxx` in `agents/1-generic/`, `config/role-defaults.yaml`, `config/conventions-presets.yaml`, `docs/REQUIREMENTS.md:4` inventarisieren (90 Zeilen in 36 Dateien in `agents/1-generic`, `git grep -c -E 'REQ-ID|REQ-xxx'` auf `9aa0e0c0`); zusaetzlich hoechste vergebene Nummer je Bereich in `docs/REQUIREMENTS.md` messen (Grundlage fuer O-H2).
- [ ] Step 2: Spec: ein Format (D-H4), eine Scope-Definition, Gating auf `DOD_REQ_TRACEABILITY`, Validator-Verhalten (still bei aus, ERROR bei an und fehlerhaft), Abgrenzung zu #1158 K-01 (Task 18) und #339 (keine #339-Planung, Entscheidung 30; mehrteilige Bereiche wie `REQ-L2-AT-018` sind ungueltig, #339 passt sich bei Neufreigabe an, Entscheidung 54).
- [ ] Step 3: Review + `Status: APPROVED`.
- Akzeptanz: `Status: APPROVED`; Tasks 20-21 sonst nicht ausfuehrbar.
- Commit: `docs: add spec for unified REQ-ID format (#1167)`

### Task 20: Validator `--validate` (Gate: Task 19)

**Agent:** `tester`, `developer`. **Depends on:** 19. **Files:** Create `scripts/lib/consistency/req_format.py`, `tests/test_req_id_format.py`; Modify `scripts/lib/cli_commands.py` (`_handle_validate` `:1408`; Registrierung wie `check_temp_literals` `:1507`). **Interfaces:** Produces `check_req_ids(agent_meta_root: Path, project_root: Path, config: Optional[dict]) -> List[Finding]` (Muster `consistency/temp_literals.py:559-563`, `Finding`/`Severity` aus `consistency/report.py`); leer, wenn `req-traceability` aus.
- [ ] Step 1: Tests (fail): `test_malformed_req_id_fails_when_traceability_on`; `test_malformed_req_id_ignored_when_off`; `test_valid_ids_pass_both_states`; `test_multi_part_area_rejected` (Fixture `REQ-L2-AT-018` => Finding bei Traceability an, Entscheidung 54); `test_single_area_accepted` (Fixture `REQ-<BEREICH>-<NN>`, z.B. `REQ-CMD-01` => kein Finding); Testdaten: tmp-`REQUIREMENTS.md` mit `REQ-CMD-01` (gueltig), `REQ-L2-AT-018` (ungueltig, mehrteiliger Bereich) und `REQ-1` (ungueltig) gemaess D-H4/54 (`REQ-<BEREICH>-<NN>`, Ziffernzahl O-H2).
- [ ] Step 2: `python3 -m pytest tests/test_req_id_format.py -q` -> failed.
- [ ] Step 3: Implementieren, registrieren; Preset-Zustand ueber `DOD_REQ_TRACEABILITY`/`dod.py` lesen (keine zweite Quelle).
- [ ] Step 4: Tests gruen; `python3 scripts/sync.py --validate` meldet im Repo (Preset `rapid-prototyping`) nichts Neues.
- Akzeptanz: beide Preset-Zustaende getestet (AC4 des Issues).
- Commit: `feat(validate): check REQ-ID format when traceability is on (#1167)`

### Task 21: Template-/Preset-Gating (Gate: Task 19)

**Agent:** `developer`. **Depends on:** 19, 20 (Format-Konstante). **Files:** Modify `agents/1-generic/validator.md` (Z. 53 ungated; Z. 35-41 bereits gegated), `agents/1-generic/bug-feature-analyzer.md` (Z. 42, 84, 134), `agents/1-generic/requirements.md`, `agents/1-generic/se-requirements.md`, `agents/1-generic/se-developer.md`, `agents/1-generic/api-specialist.md`, `config/conventions-presets.yaml`, `config/role-defaults.yaml` (Zeilen laut Spec); je Agent-Datei `version:` minor erhoehen. **Interfaces:** Consumes `{{#if DOD_REQ_TRACEABILITY}}`.
- [ ] Step 1: Test (fail) in `tests/test_req_id_format.py`: Rendering mit Preset `rapid-prototyping` enthaelt in den betroffenen Agenten keine REQ-Mandate (Grep auf `REQ-ID`/`REQ-xxx` im gerenderten Text); mit Preset mit Traceability an enthaelt es genau das kanonische Format.
- [ ] Step 2: Test laeuft rot auf `validator.md`/`bug-feature-analyzer.md`.
- [ ] Step 3: Bloecke gaten, Format vereinheitlichen; `python3 scripts/sync.py --validate`.
- [ ] Step 4: Test gruen; `python3 -m pytest tests/test_agents_frontmatter.py tests/test_ac01_render_identity.py tests/test_context_budgets.py -q`; Re-Pin per Helper (Task 6) mit Grund.
- Akzeptanz: Gating-Grep im Rendering mit `rapid-prototyping` leer.
- Commit: `fix(templates): gate REQ-ID wording on DOD_REQ_TRACEABILITY (#1167)`

---

## Frische-Check-Referenzen

- #969, #977, #1161, #1115, #1014, #778, #779, #780, #960, #1167, #1158, #1159, #1086i, #1013, #1081, #1085c, #1182, #1183, #1208, #1210, #1217, #1218, #1169, #1181, #1186, #1187, #1188, #1141, #339, #885
- `docs/superpowers/plans/2026-11-10-backlog-roadmap.md`
- `docs/superpowers/plans/2026-11-11-phase-c-1086i-context-split.md`
- `docs/superpowers/plans/2026-11-11-phase-d-guards-hooks.md` (Owner `hook_json_get_many`, Entscheidung 28)
- `config/provider-capabilities.yaml` (`roster_in_harness`, gelesen), `templates/context/agents-managed.md`, `scripts/lib/consistency/temp_literals.py`, `scripts/lib/deactivation.py`
- origin/main `9aa0e0c0` (PR #1218): Rebase-Pruefung aller Anker
- `docs/specs/2026-10-11-context-profiles-spec.md`
- `scripts/lib/eval_gate.py`, `scripts/run_role_routing_eval.py`, `scripts/lib/context_profile_gate.py`
- `tests/test_eval_gate.py`, `tests/test_eval_baseline_schema.py`, `tests/test_context_profile_gate.py`
- `scripts/lib/context_report.py`, `tests/test_context_budgets.py`, `tests/test_ac01_render_identity.py`
- `scripts/lib/context.py`, `scripts/lib/sync_pipeline.py`, `scripts/lib/generated_file_drift.py`, `scripts/sync.py`
- `scripts/lib/agents.py`, `scripts/lib/delegation_table.py`, `scripts/lib/isolation.py`, `scripts/lib/cli_commands.py`
- `scripts/lib/rules.py`, `scripts/lib/providers.py`, `scripts/lib/external_tools_drift.py`, `scripts/lib/setup.py`, `scripts/lib/standalone.py`, `scripts/lib/config.py`, `scripts/lib/dod.py`, `scripts/lib/mcp.py`, `scripts/lib/mcp_provider_config.py`
- `hooks/1-generic/lib/hook_common.sh`, `hooks/1-generic/orchestrator-guard-impl.sh`, `hooks/1-generic/repo-containment-impl.sh`, `hooks/1-generic/dod-push-check.sh`, `hooks/1-generic/lifecycle-check.sh`, `hooks/1-generic/sync-on-config-change.sh`
- `tests/test_hook_common_lib.py`, `tests/test_generated_file_drift.py`, `tests/test_managed_index_alignment.py`, `tests/test_cleanup_preview_cli.py`, `tests/test_routing_tool_definitions.py`, `tests/test_routing_overlap.py`, `tests/test_routing_keyword_overlap_check.py`, `tests/test_provider_agnostic_dispatch.py`, `tests/test_opencode_runtime_gate.py`, `tests/test_opencode_v2_surface.py`, `tests/test_issue_1020_gate_rollback.py`, `tests/test_runtime_gate_wiring.py`, `tests/test_orchestrator_topology_entrypoint.py`, `tests/test_opencode_main_chat_entry_point.py`, `tests/test_isolation_v2_topology_reconcile.py`, `tests/test_orchestrator_mode_topology_matrix.py`, `tests/test_repo_containment_hook.py`, `tests/test_dod_push_check_hook.py`, `tests/test_lifecycle_check_args.py`, `tests/test_hook_smoke_optin.py`, `tests/test_external_tools_drift_catalog_ref.py`, `tests/test_external_tools_registry.py`
- `config/role-defaults.yaml`, `config/project-config.schema.json`, `config/dod-presets.yaml`, `config/conventions-presets.yaml`, `config/ai-providers.yaml`, `config/pricing-overlay.yaml`
- `agents/1-generic/orchestrator.md`, `agents/1-generic/validator.md`, `agents/1-generic/bug-feature-analyzer.md`, `agents/1-generic/provider-expert.md`, `agents/1-generic/principal-developer.md`, `agents/1-generic/senior-developer.md`
- `templates/context/agents-managed.md`, `rules/1-generic/branch-guard.md`, `rules/2-platform/agent-meta-conventions.md`, `docs/REQUIREMENTS.md`, `.meta-config/project.yaml`, `docs/concepts/branch-guard-known-limits.md`
- Neu (geplant): `scripts/measure_context_repin.py`, `tests/test_context_repin_helper.py`, `tests/test_routing_language_guard.py`, `tests/test_dod_gating_rendered.py`, `tests/test_req_id_format.py`, `tests/test_mcp_registry_key_unread.py`, `scripts/lib/consistency/req_format.py`, `docs/analysis/evidence/2026-11-11-opencode-allow-list-f-oc2.md`, `docs/specs/2026-11-11-context-token-1161-spec.md`, `docs/specs/2026-11-11-evidence-discipline-1014-spec.md`, `docs/specs/2026-11-11-routing-language-779-780-spec.md`, `docs/specs/2026-11-11-model-range-960-spec.md`, `docs/specs/2026-11-11-req-id-format-1167-spec.md`, `docs/concepts/evidence-discipline-1014.md`, `docs/concepts/cross-cutting-findings-778.md`
- Symbole: `evaluate_gate`, `mcnemar_exact`, `estimate_cost`, `run_with_approval`, `compute_metrics`, `compute_case_outcomes`, `build_baseline`, `validate_baseline`, `_as_candidate`, `measure_artifacts`, `_IST_FULL`, `_IST_COMPACT`, `format_repin_block`, `_managed_dirs_for_prune`, `prune_sync_backups`, `_backup_context_file`, `hook_json_get`, `hook_json_get_many`, `_select_examples`, `get_routing_rules`, `_sync_opencode_runtime_gate`, `rollback_opencode_runtime_gate`, `reconcile_opencode_surface_gate`, `check_req_ids`

## Nicht verifiziert

- Nichts wurde ausgefuehrt (keine Tests, kein `--validate`, kein Render). Alle "gruen erwartet"/"rot erwartet"-Angaben und Zahlen in Test-Erwartungen sind Plan-Werte aus dem gelesenen Code.
- Anker und Zaehlungen wurden im Review 2026-11-11 per `git show`/`git grep` gegen `origin/main 9aa0e0c0` gemessen; nach B/C/D/E/F verschieben sie sich erneut (Freshness-Check vor Ausfuehrung).
- Gerenderte Dateien (`.claude/agents/`, `AGENTS.md`) wurden nicht neu erzeugt; K-01 gegen gerenderten Output, `name_index`-Duplikate (#1161 Pkt 1) und Token-Zahlen des Issues nicht nachgemessen.
- Inhalt von `tests/test_routing_overlap.py` und `tests/test_routing_keyword_overlap_check.py` nicht gelesen (IT-3/IT-6/IT-7-Status nur aus Dateiexistenz).
- `config/review-rules/`, `config/tier-presets.yaml`, `scripts/lib/roles.py`: existieren, Inhalt nicht gelesen.
- `UEBERGREIFENDE-MUSTER.md` (#1014) nicht im Repo; 79-Rollen-Review-Grundlage nicht pruefbar.
- Phase-D-Plan nur ausschnittweise gelesen (Tasks 5-7, Z. 210-248); Tasks 5/6/7-Zuordnung geprueft, Inhalt der D-Spec nicht.
- Herkunft der F-OC2-Doku-Liste (`steps, top_p, disable, prompt`): im Repo nicht gefunden, extern vermutet.
- `docs/guides/`-Zieldatei fuer den Keyword-Regel-Absatz (Task 12) offen bis Spec.

## Self-Review

- Kein TBD/TODO/Platzhalter im ausfuehrbaren Teil. Bewusst nicht ausformuliert: #1161 Pkt 2 (Task 10b, nach Spec), Folgepläne zu #1014, #778, #960 (erst nach `Status: APPROVED`).
- Abdeckung je Issue genau einmal: #969 -> Tasks 1-5; #1115 -> 6; #1161 -> 7 (Pkt 4), 8 + 10b (Pkt 2), 10 (Pkt 5, Funktion aus Phase D Task 5-7), Pkt 1 gebaut, Pkt 3 Restmessung in Task 8; #1014 -> Task 0; #778 -> 14; #779/#780 -> 11-13; #960 -> 16; #1167 -> 19-21; #1158-Rest -> 18; #1159-Rest -> 15 (K-12), 17 (K-16, K-17), 22 (F-PA1), 23 (F-PA2), 24 (F-OC2); #977 nur Querverweis (Phase A).
- Spec-Gates: Task 0, 8, 11, 14, 16, 19 (sechs). #969 nutzt die bestehende APPROVED Spec.
- Signaturen gegen `9aa0e0c0` belegt: `evaluate_gate` (`eval_gate.py:331`), `run_with_approval` (`:245`), `estimate_cost` (`:124`), `compute_metrics` (`run_role_routing_eval.py:186`), `build_baseline` (`:287`), `measure_artifacts` (`context_report.py:130`), `prune_sync_backups` (`generated_file_drift.py:199`), `hook_json_get` (`hook_common.sh:63`), `_select_examples` (`delegation_table.py:229`), `get_routing_rules` (`delegation_table.py:289`), `_prune_managed_sync_backups` (`sync_pipeline.py:1029`), `check_temp_literals` (`consistency/temp_literals.py:559`). Neue Signaturen sind als "Produces" markiert.
- Plan-Template: Task-Nummern nicht fortlaufend sortiert (0, 14 nach Block-Logik); `pipeline_stages` im Frontmatter zeigt auf Schritt 2 (Implementierung nach Gate).
- Entscheidungen eingearbeitet: 11 (Tasks 1-5), 17 (ein Commit je Task; PR-Schnitt durch 52 ersetzt), 18/19 (Reihenfolge), 25 (keine Trailer-Vorgabe), 28 (Task 9 entfaellt, Funktion aus D; Task 10 = #1161 Pkt 5), 29 (Task 8/10b, vorhandenes Flag), 30 (#339 nur Abgrenzung), 34 (D-H3 Task 12, D-H4 Tasks 19-21, D-H5 Task 13), 36 (durch 52 ergaenzt), 38e (keine Closing-Keywords), 52 (H1/H2-Schnitt, O-H4/O-H8 beantwortet).
- Task-Zaehlung: nummeriert 0-24 (25), davon aktiv 24; Task 9 entfaellt. Gate-Tasks: 0, 8, 11, 14, 16, 19 (sechs) plus Phase-D-Abnahme vor Task 10.
- Offene Punkte: O-H2 unter "Offene Entscheidungen (neu, ungeklaert)" (bis Task-19-Messung); O-H5 per Entscheidung 54, O-H6/O-H7 per Entscheidung 56 beantwortet; O-H1/O-H3 per Code bzw. Entscheidung 28 geklaert, O-H4/O-H8 per Entscheidung 52; nichts davon geraten.
- Roadmap-Zaehler Phase H = 11 Issues (Roadmap §2 Z. 152): #969, #1161, #1115, #1014, #778, #779, #780, #960, #1167, #1158, #1159 — stimmt mit dem Kopf ueberein.
