# Plan-Review 2026-11-11

## Methode

- Review je Plan durch einen code-reviewer, sequentiell bearbeitet (kein paralleler Lauf).
- Referenzen und Code-Anker gegen origin/main 9aa0e0c0 per grep/git show geprueft.
- Frische-Check-Skript check_plan_refs.py vor und nach den Fixes ausgefuehrt.
- Bare `:NNNN`-Anker von Hand geprueft, da das Skript sie nicht sicher aufloest.
- Fixes direkt im Plan, jeweils mit Beleg datei:zeile.
- Nicht ausgefuehrte Testwerte werden nicht als Planwerte uebernommen.
- Keine Tests und keine Syncs ausgefuehrt.

## Phase A
### Review Phase-A-Plan (`docs/superpowers/plans/2026-11-11-phase-a-hygiene.md`)

Stand: 2026-11-11, gegen `origin/main 9aa0e0c0`. Alles read-only (Code per `git show origin/main:`, `gh` nur lesend, Messungen im Haupt-Checkout ohne Schreibzugriff). Marker-Test in einer Sandbox-Kopie unter `.tmp/` ausgeführt, die danach gelöscht wurde.

## Befunde

| # | Befund | Beleg | Verdikt | Fix |
|---|---|---|---|---|
| 1 | #547: laut Plan nennt der Guide unter `:171-189` drei offene Punkte | `docs/guides/cross-harness-dev-isolation.md:171-199`: fünf Punkte (4 Branch-Purge `:190-194`, 5 Per-Harness- vs. zentrales Config-Verzeichnis `:195-199`) | falsch | Abweichung 4, Tabelle 3a (Zeile 5b), Kommentar- und Follow-up-Text auf `:171-199`; Punkt 5 als User-Frage A-Q1 |
| 2 | CI-Anker `orchestration-test.yml:209/391` (Matrix), `:236/:408/:489` (pip), `:355` (splits) | `git show origin/main:.github/workflows/orchestration-test.yml` → `:210`, `:392`, `:237`, `:409`, `:490`, `:356` (Datei geändert a3d65da4..9aa0e0c0) | falsch | Task 2 und Task-8-Kommentar nachgezogen |
| 3 | `isolation.py:1242` `permission_deny_required`, `:1751` `reconcile_opencode_surface_gate` | `git grep "def permission_deny_required\|def reconcile_opencode_surface_gate" origin/main` → `isolation.py:1290`, `:1915` | falsch | Task 4a und 4b |
| 4 | `write_atomic` laut Issue `io.py:377` | `scripts/lib/io.py:350` `def write_atomic(path: Path, content: str, mode: str = "w", *, private: bool = False) -> None` | falsch (veraltet) | Task 14 Step 1, Signatur exakt übernommen |
| 5 | Stash-Erhebung `git stash list --format='%gd ...' --date=short` | Messung: `--date` schaltet `%gd` auf `stash@{<datum>}`, der Index geht verloren; `%cs` ohne `--date` liefert `stash@{0..8}` | falsch | Task 10 Step 3 |
| 6 | Bundle in Task 10 Step 2 sichert nur `origin/*` plus `fix/sync-check-tracked-only` | `git rev-list --count origin/feat/repository-documentation-consolidation..feat/repository-documentation-consolidation` = 1 (`90be1146` nur lokal; `merge-base --is-ancestor` gegen den Remote: nein) → Datenverlust beim Löschen des lokalen Branches | falsch (blocking) | lokale Ref ins Bundle aufgenommen, Step 4 um lokale Refs ergänzt |
| 7 | #946-Tabelle "zu erheben", Stashes "2 weitere zu erheben" | Messung `git log -1`/`rev-list --count`/`git cherry` je Branch und `git stash list` | ungeprüft → gemessen | Tabelle gefüllt (19 Branches, 9 Stashes mit Index); Werte am Ausführungstag neu erheben |
| 8 | `docs/auto-commit-tiers-spec`: "Löschen, falls `git cherry` leer" | `git cherry origin/main origin/docs/auto-commit-tiers-spec` → 1 `+`-Zeile; kein Branch hat 0 | falsch (Regel greift nie) | Vorschlag auf User-Entscheidung; Hinweis, dass `git cherry` Squash-Merges nicht erkennt |
| 9 | `feat/issue-batch-677-728`: 4 Commits vor main (Issue) | `rev-list --count origin/main..origin/feat/issue-batch-677-728` = 10 | falsch (Issue veraltet) | in Tabelle vermerkt |
| 10 | `feat/model-inherit-main-chat`: `inherit_active`-Guard "nicht in main" (Issue) | `scripts/lib/provider_transform.py:662` `inherit_active = bool(...)` in main | fraglich | Hinweis in Tabelle und »Nicht verifiziert« |
| 11 | Label `blocked`: nicht geprüft | `gh label list --search blocked` → leer | ungeprüft → gemessen | Task 1 Step 4: Erwartung leer, Task 13 Step 1 legt an |
| 12 | #885-Kinder #932/#936 "nicht geprüft" | `gh issue view` → beide `CLOSED COMPLETED` | ungeprüft → gemessen | Task 12 und Kommentartext |
| 13 | `check_plan_refs.py` "existiert nicht" | `git ls-tree origin/main scripts/check_plan_refs.py` leer; Datei liegt in `.tmp/wt-check-plan-refs/scripts/` | teilweise falsch | Abweichung 8, Task 1 Step 2 |
| 14 | Existenz `tests/test_provider_agnostic_dispatch.py`, `test_hook_notebook_multiedit.py`, `test_hook_smoke_optin.py`, Guide-Abschnitt Branch-Strategie "nicht geprüft" | `git ls-tree origin/main tests/`: alle vorhanden; Guide `:57-62` | korrekt (jetzt belegt) | Tabelle 3a, Task 5 Step 4, »Nicht verifiziert« |
| 15 | #1116: Mutationsbeweis/`-n 2` in `fa37d7d0`? (bedingt) | `git show --stat --format=%B fa37d7d0`: keine Aussage dazu | aufgelöst | bedingte Ergänzung des Kommentars entfernt |
| 16 | Platzhalter `<Merge-Commit von #1018>` | `git log origin/main` → `97b4e49f ... (#1018)` | Platzhalter | durch `97b4e49f` ersetzt |
| 17 | `tests/scenarios/configs/69-...yaml`, `79-...yaml` (elidiert) | `git ls-tree`: `69-opencode-v2-surface.project.yaml`, `79-opencode-v2-full-surface.project.yaml` | unpräzise | volle Pfade |
| 18 | Kommentartexte "Geprüft gegen origin/main a3d65da4" | Anker in diesem Review an `9aa0e0c0` gemessen | veraltet | auf `9aa0e0c0` umgestellt (Frontmatter/Basis bleibt a3d65da4 als Plan-Stand) |
| 19 | Task 2 Step 2: Rot-Erwartung ohne Zahl | Sandbox, Python 3.13: alt `2 failed, 1 passed`, mit Marker `3 passed` | korrekt (präzisiert) | Zahl ergänzt; kein `python3.9` auf dem Host vermerkt |
| 20 | `tests/requirements.txt:13` `pytest-split>=0.8`, Marker-Muster `:4-6`, `:9-11` | `git show origin/main:tests/requirements.txt` | korrekt | — |
| 21 | Dependabot `/` und `/tests` (`dependabot.yml:5`), `validate.yml:100,120` | gelesen | korrekt | — |
| 22 | Mammouth `ai-providers.yaml:645-647`, `:659-669`, `:670`; Continue `:474`, `:495`; Codex `:770`; `provider-capabilities.yaml:528-529`; Gemini `:141-147`, `:150-155` | gelesen | korrekt | — |
| 23 | `opencode_v2_config.py:494`, `:504-513`, `:515-517`, `:680`; `provider_transform.py:968`, `:483-488`; `mcp_provider_config.py:278-281`; `docs/providers/opencode.md:49,57-60,71-84,90-91,105-137` | gelesen | korrekt | Task 4a Step 3: Testsammlung 132 ergänzt |
| 24 | Hang-Guards `test_orchestrator_guard_hook.py:59-63,1863,1876-1878`; `test_hook_common_lib.py:36,521,541-543` | gelesen | korrekt | — |
| 25 | #1151 F6-01/02/03: `orchestrator-guard-impl.sh:28-29,290-294`, `repo-containment-impl.sh:233-240`, `hook_common.sh:178-183`, `test_hook_common_lib.py:493-498` | gelesen | korrekt | — |
| 26 | #885 F-01 `_SCOPE_GLOBS` `:71-77`, F-04 kein `/tmp/opencode`, F-07 kein `{{ROLE}}` | gelesen, `git grep` ohne Treffer | korrekt | — |
| 27 | #1155 F2 `deactivation.py:279` zwei Argumente | gelesen | korrekt | — |
| 28 | #1161 Punkt 5 `hook_common.sh:63` | `hook_json_get()` an `:63` | korrekt | vermerkt |
| 29 | #977-Body: 13 Checkboxen `- [ ] #963..#976` ohne #969, sed-Muster passt | `gh issue view 977 --json body` | korrekt | — |
| 30 | Issue-/PR-Zustände (11 A-Issues, #1186 `OPEN`, #1190 `CLOSED COMPLETED` mit 0 Kommentaren, #1145/#1148 `OPEN` nur `tests/requirements.txt`, #963-#976 außer #969 `CLOSED`) | `gh issue/pr view` | korrekt | Task 8 Step 1 belegt |
| 31 | Hashes `fa37d7d0`, `c1e810c6`, `283fcd3c`, `f55601ba` (#904), `89cc6381` (#994) in main; `35f591e6`, `90be1146` nur lokal | `git merge-base --is-ancestor`, `git log -1 --format=%s` | korrekt | »Nicht verifiziert« aktualisiert |
| 32 | ADR 0002 und #1190-Kommentaraussagen (24-Zellen-Matrix, drei Diagnosen) | `docs/adr/0002-orchestrator-mode-topology.md` vorhanden; `.tmp/prs/1218.md:14,16` | korrekt (Quelle PR-Text) | als PR-Text markiert |
| 33 | Gate-Ausdrücke Task 5/14 sammeln Tests | `pytest --collect-only -k`: 9 / 63 / 177 | korrekt | Zahlen als Sammelwerte ergänzt |
| 34 | Konsistenz mit Entscheidungen: 1 PR (17), keine Closing-Keywords (38e), keine Trailer-Constraint-Zeile (#1168), `!`-Befehle (12), #885 offen (13), #1190 nur Nachtrag (38f) | `grep -n "Co-Authored\|Closes\|Fixes\|Resolves"`: nur Regeltext und Zitat aus `.tmp/prs/1218.md` | korrekt | — |
| 35 | Spec-Gate: alle Items S, 0 Spec-Gates | eine Code-Datei plus Test; Rest `gh`-Ops | korrekt (plausibel) | — |
| 36 | Phasenzähler A = 11 | Roadmap `:145` | korrekt | — |
| 37 (advisory) | Task 9 Step 4 (ADR-Check) steht nach Step 3, soll aber davor laufen | Plan Task 9 | judgment, non-blocking | nicht geändert (Text sagt "Vor Step 3") |

## Zähler

- korrekt: 19 (Befunde 14, 19-36)
- falsch: 12 (1, 2, 3, 4, 5, 6, 8, 9, 10, 13, 16, 18)
- ungeprüft (vor Review), jetzt gemessen: 4 (7, 11, 12, 15)
- unpräzise: 1 (17); advisory: 1 (37)
- Fixes im Plan: 44 Edit-Aufrufe plus ein `sed` (drei Kommentartext-Muster `a3d65da4` → `9aa0e0c0`)
- Phasenanzahl: unverändert A = 11 Issues (Roadmap `:145`, Summe 89)

## Verbleibende echte User-Entscheidungen

| Plan | ID | Frage | Empfehlung |
|---|---|---|---|
| Phase A | A-Q1 | Guide-Punkt 5 "Per-harness vs. central config dir" (`docs/guides/cross-harness-dev-isolation.md:195-199`) als vierten Punkt ins #547-Follow-up aufnehmen? Entscheidung 20 nennt nur drei Punkte. | ja; sonst bleibt der Punkt nach dem Schließen von #547 ohne Tracker |

Alle übrigen Punkte (#946-Tabellenzeilen) sind bereits als Freigabe-Schritt (Entscheidung 12) im Plan, keine neue Frage.

## Nicht verifiziert

- Gate-Tests nur gesammelt, nicht ausgeführt; `pip install --dry-run`, `consistency-check.py --json` (F-08) nicht ausgeführt.
- Wirksamkeit des Markers in CI (kein Python 3.9 auf dem Host); Dependabot-Verhalten bei Marker-Zeilen.
- #1151 F6-04..F6-13, #857/#858 Skills-Emission zur Laufzeit, #1007 Lab-Diff und flache `skills`-Liste: nur PR-Text.
- `scripts/lib/context.py:204` (#1161): Zuordnung zum Issue-Punkt unklar.
- `route_intent`-Treffer (`agents.py:35`) als Beleg für #1161 Punkt 1/3: Zuordnung nicht geprüft.
- `inherit_active` im Branch vs. in main (`provider_transform.py:662`): inhaltlicher Unterschied nicht geprüft.
- #1155 F3-F9, #1158, #1159 Teilstände: laut Roadmap-Sweep.
- Branch-/Stash-Werte gelten für `FETCH_HEAD` 2026-11-11 14:59; am Ausführungstag neu erheben.

## Checker (`check_plan_refs.py --ref origin/main`)

- Vorher: 1 ERROR, 14 WARN, 13 INFO (`.tmp/a-before.txt`; identisch mit Abschnitt Phase A im Rohbericht `.tmp/check-plan-refs-report.md:10-26`).
- Nachher: 1 ERROR, 12 WARN, 13 INFO (`.tmp/a-after.txt`).
- Verbleibender ERROR (neu geplante Datei, Klasse a): `tests/test_requirements_pytest_split_marker.py` (Task 2 Create).
- Klassifizierung der WARNs:
  - b (behoben): `isolation.py:1242/1751` (jetzt `:1290/:1915`), `tests/scenarios/configs/69-...yaml` (volle Pfade), `inherit_active` / `OUTPUT_GUARD_BLOCK` / `PARSE_INPUT_BLOCK` (jetzt mit realer Fundstelle belegt).
  - c (Checker-Artefakt): `provider_transform.py:968`/`isolation.py:1290` ANCHOR_DRIFT (Checker paart Symbole mit dem ersten Anker der Zeile; Definitionen per `git grep` verifiziert), `test_orchestrator_guard_hook.py:59` und `test_hook_common_lib.py:493` (Symbole gehören zu anderen Ankern derselben Zeile), `.mammouth/mcp.local.json` (Config-Wert, keine Repo-Datei), `stateReason` und `FETCH_HEAD` (`gh`-JSON-Feld bzw. Git-Ref, kein Code-Symbol), `scripts/check_plan_refs.py` (bewusst als "nicht auf origin/main" beschrieben).
- INFO: 13× ISSUE_CLOSED für gemergte PRs (#904, #994, #1012, #1016-#1019, #1153, #1163-#1165, #1218, #1219), erwartet.


## Phase B

### Review Phase-B-Plan (`docs/superpowers/plans/2026-11-11-phase-b-small-bugs.md`)

Stand: 2026-11-11, W = `.tmp/wt-phase-plans` (Code identisch mit origin/main `9aa0e0c0`). Rohberichte des Checkers: `.tmp/rb/before.txt`, `.tmp/rb/after.txt`.

## Befunde

| # | Befund | Beleg (datei:zeile / command+output) | Verdikt | Fix |
|---|---|---|---|---|
| 1 | Basis `a3d65da4` statt `9aa0e0c0` | `git merge-base --is-ancestor a3d65da4 origin/main` = ja, 93 Dateien Diff in scripts/tests/config/... | falsch | Frontmatter `base-commit`, Kopf, Global Constraints, Self-Review auf 9aa0e0c0 |
| 2 | T1 Anker (`timeout=300` `:53`, Fixture `:27`, `SYNC_TIMEOUT`-Default `:36`, `SLOW_TIMEOUT` `:69`, Importstil `test_generated_file_drift.py:844`), `SLOW_TIMEOUT` sonst ungenutzt | `tests/test_cli_smoke_multi_provider.py:27,53`; `tests/timeouts.py:36,69`; grep: nur timeouts.py/README/Doku | korrekt | – |
| 3 | T2 Funktion `:885-901`, Notiz `provider-capabilities.yaml:290`, keine Aufrufer, `G4-2` nicht in tests | `scripts/lib/provider_transform.py:885`; repo-grep ohne `.tmp` | korrekt | – |
| 4 | T3 `context.py`-Anker `:1656/:1740/:1768` | `scripts/lib/context.py:1815` (`apply_settings_surface_shape`), `:1899`, `:1927` | falsch | Anker in Befund + Abweichung 1 ersetzt |
| 5 | T3 Signaturen `sync_opencode_v2_managed_keys` `:680`, `build_managed_keys` `:464`, `validate_json_document` `:304`, `_validate_opencode_v2` `:436`, `_finding` `:155` | gelesen in W | korrekt | – |
| 6 | T3 Einfügepunkt "nach `:773`" würde von `changed = False` überschrieben | `scripts/lib/opencode_v2_config.py:776-777` | falsch | Step 3: nach `:776`, vor `:777` |
| 7 | T3 Validator-Test prüft `experimental.subagent_depth` in `.message`, Plan legt es in die Suggestion | Plan Step 3 vs. Test; `Finding.suggestion` `scripts/lib/consistency/report.py:34` | falsch | Assertion auf `.message`/`.suggestion` aufgeteilt |
| 8 | T3 "3 FAILED" erwartet; Idempotenz-Test ist vor der Änderung grün | Logik: heute wird nichts entfernt, Lauf 2 = Lauf 1 | falsch | Plan-Wert 2 FAILED |
| 9 | T3 `mock.patch` auf `log.action` unnötig, `mock` nicht importiert | `tests/test_opencode_v2_surface.py:67` (SyncLog), `:770` (`log.actions`), `scripts/lib/log.py:29-37` | falsch | Test nutzt `log.actions`; Helfer-Signaturen mit Zeilen eingetragen |
| 10 | T4 Aufrufer-Anker `sync_pipeline.py:1912`, `cli_commands.py:1437`, `config.py:1806` | `sync_pipeline.py:1993`, `cli_commands.py:1465`, `config.py:1807` | falsch | ersetzt |
| 11 | T4 `test_keys_equal_schema_properties` dupliziert bestehenden Test, AK 1 (schema-only-Key) ohne Test | `tests/test_auto_commit_violations.py:111-123` (`assert set(_KEYS) == set(ac["properties"])`) | falsch | Duplikat entfernt; `_load_schema_keys(path=_SCHEMA_PATH)` + Tests für AK 1 und Fallback; Plan-Wert 4 FAILED |
| 12 | T4 Nutzer von `_KEYS` "nicht abschließend gesucht" | grep scripts/tests: `auto_commit.py:222`, `tests/test_auto_commit_violations.py:116/:123` | ungeprueft → belegt | im Befund eingetragen, aus "Nicht verifiziert" entfernt |
| 13 | T5 Anker `spec_plan.py:490-492`, `:197`, `:55`, `:100`, `:479`, `plan_identity.py:27` | gelesen in W | korrekt | – |
| 14 | T5 erzeugt falschen ERROR: `_APPROVED_RE` erkennt `Status: **APPROVED**` nicht | `spec_plan.py:85-87`; `docs/specs/2026-11-09-artifact-locations-matrix-spec.md:3`; Python-Lauf: `_APPROVED_RE.search(...) = False` | falsch (Lücke) | Step 3b + Test `test_bold_approved_value_counts_as_approved` |
| 15 | T5 Fehlalarm-Risiko von `_TASK_LIKE_HEADER_RE` | Messung über docs/plans, docs/superpowers/plans, docs/specs: 5 Treffer, alle echte Task-Header | ungeprueft → belegt korrekt | Messung im Befund |
| 16 | T5/T6 Vollscan-Befehl stürzt ab | `OSError: [Errno 36] File name too long` in `spec_plan.py:414` (`_check_traceability`); Prosa-`**Spec:**` in Plan D (277 B) und I (353 B) | falsch (Lücke) | Warnhinweis in T5 Step 4; Ursache außerhalb B (Plan D/I bzw. eigener Bug) |
| 17 | T6 "13 Dateien" | `git ls-tree origin/main docs/specs` → 16 `*-spec.md` | falsch | auf 16 korrigiert |
| 18 | T6 "Variante (a) bindend gewählt" ohne Entscheidungsnummer | `.tmp/issues/1214.md:68` (Issue-Vorzug) | falsch | als Issue-Vorzugsvariante formuliert |
| 19 | T6 `_matches_template` erweitern ist wirkungslos | `spec_plan.py:51` `_DATED_RE`, `:312-315` | falsch (YAGNI) | nur `_classify` ändern |
| 20 | T6 "Rule-Version im Frontmatter heben" | `rules/1-generic/spec-plan-workflow.md:1` beginnt mit `#`; keine Datei in `rules/1-generic/` hat Frontmatter | falsch | entfernt; Einfügestelle `## Phasen` konkret; drei Regel-Tests in Step 4 |
| 21 | T7 Anker `config.py:1621/:1837`, `sync_pipeline.py:1893` | `config.py:1622`, `:1838`; `sync_pipeline.py:1974` | falsch | ersetzt (Interfaces + Abweichung 7) |
| 22 | T7 Existenz `agent_sync.py::sync_agents_for_provider`, `subagent_permissions.py` | `scripts/lib/agent_sync.py:1519`; Datei existiert | ungeprueft → belegt | eingetragen; "Stand a3d65da4" → "Stand 9aa0e0c0" |
| 23 | T7 Spec-Status "Entwurf", `is_role_eligible` `:146-153` | `docs/specs/767-auto-commit-permission-authority.md:2`; `auto_commit.py:146-153` | korrekt | Ankerliste präzisiert (14 Regex-Treffer + `:10/:11/:17`) |
| 24 | T8 Zählung 3/2/2/2, #1187 APPROVED | `str.count` über `agents/1-generic/*.md`; Spec `:3`, Plan `:3` | ungeprueft → belegt korrekt | eingetragen |
| 25 | T8 Querbezug: #1187-T9 macht Ratchet rot, E-Plan/#1187-Plan kennen den Test nicht | grep `placeholder_ratchet`/`_KNOWN_DUPLICATES` in `docs/superpowers/plans/*.md`: nur Plan B | falsch (Lücke) | Hinweis in T8 Step 3; E-Plan muss nachziehen |
| 26 | T9 Anker `build_variables :2737`, `_build_core_variables :1621` | `config.py:2779`, `:1622`; `docs/guides/features/sync-concept.md` existiert | falsch | ersetzt |
| 27 | T9 einzige "Variablen-Tabelle"-Stelle, `_inject_dod` fehlt, `agents/agent-meta-developer.md` fehlt | `knowledge/wiki/concepts/core-principle-pal-variables.md:80-81`; grep | korrekt | – |
| 28 | T10 Anker Handler/Guard/UI (`:5065`, `:5089`, `:4941`, `:4957`, `:4983-5000`, `:5071`, `admin-ui.html:10907/10950/10953/1025/1074`) | gelesen in W | korrekt | – |
| 29 | T10 Files/File-Structure nennen UI-Änderung, "neu zu bauen" widerspricht Step 3 (Toast reicht) | Plan Task 10 vs. `admin-ui.html:10953-10954` | falsch | UI aus Task-10-Files entfernt, Texte angeglichen |
| 30 | T10 "Kein Bypass-Dialog (Entscheidung 22)" — steht nicht in Entscheidung 22 | Roadmap §7b Nr. 22 | falsch | umformuliert |
| 31 | T10 Folge: `config/tier-presets.yaml:24` hat Kommentar → UI-Save hier immer HTTP 400 | grep; Präzedenz ai-providers.yaml (234 Kommentarzeilen, UI `:10845` ohne `__allow_lossy__`) | falsch (Lücke) | PR-Notiz ergänzt (deckt sich mit Entscheidung 22) |
| 32 | T11 Anker (`:7639`, `:803`, `:5960`, `:7650`, `:7753-7761`, `:7735-7752`, Browser-Test `:63`) | gelesen in W | korrekt | – |
| 33 | T12 Anker (UI-Helfer, `ai-providers.yaml:112-122`, ModelsService `:2717/:2846/:2906/:2957/:2961/:2980/:3182`, Import `:4328`, `:4372`, Delegat `:4278`) | gelesen in W | korrekt | `:4364-4365` für Kostenübernahme ergänzt |
| 34 | T12 Precondition P-12 "NICHT AUSGEFÜHRT" | `python3 -I` Abfrage models.dev (read-only): alle vier IDs mit `cost` (haiku 0.1/0.5 + tiers, sonnet 2/10, opus 4/20, fable 10/50) | ungeprueft → belegt | Ergebnis eingetragen, Wiederholung beim Umsetzen |
| 35 | T12 Testpins alter IDs `test_model_discovery.py:697-700`, `:778-781` | gelesen | korrekt | – |
| 36 | T13 Anker (`VizManager :597`, `:749-783`, `:820`, `:4208`, `:4232`, `viz-report.py:953-961`, `_load_viz_config :483-518`, `viewVizDashboard :9526`) | gelesen | korrekt | – |
| 37 | "Offene Entscheidung" Toast-Design ist keine echte User-Entscheidung | Entscheidung 22 verlangt nur Fehleranzeige; Toast `:10953-10954` | falsch | entfernt, begründet |
| 38 | Frische-Check-Liste: kaputtes Listenelement (`checkboxGroupField`)- `config/...`) | Plan-Zeile ~712 | falsch | Zeilenumbruch, neue Symbole als "(neu)" markiert |
| 39 | Phasenzähler B 13, ein PR, 13 Commits, keine Closing-Keywords, kein Co-Authored-By-Verbot | Plan Kopf/PR-Schnitt; Roadmap §2 | korrekt | – |
| 40 | Spec-Gate: alle S; #1197-Teil in B = nur Test, M-Arbeit liegt im APPROVED-Plan #1187 | Spec/Plan #1187 `:3` | korrekt | – |
| 41 | Dateiüberlappung `auto_commit.py` mit C/D (B ändert Meldungstext) | grep Phasenpläne C/D | ungeprueft | nicht geändert; C-Plan auf Meldungs-Assertions prüfen |
| 42 | T12 `test_threshold_is_conditional…`: Teilassertion `"file-count-threshold" in view` ist heute schon wahr | `admin-ui.html` TRIGGERS-Literal in `viewProjectAutoCommit` | Hinweis (nicht blockierend) | nicht geändert (zweite Assertion macht den Test rot) |

## Zähler

- korrekt: 15 (2, 3, 5, 13, 15, 23, 24, 27, 28, 32, 33, 35, 36, 39, 40 — davon 15 und 24 erst im Review gemessen)
- falsch: 22 (1, 4, 6, 7, 8, 9, 10, 11, 14, 16, 17, 18, 19, 20, 21, 25, 26, 29, 30, 31, 37, 38)
- ungeprueft im Plan, im Review belegt: 3 (12, 22, 34)
- ungeprueft (bleibt): 1 (41); Hinweis: 1 (42)
- Fixes im Plan: 25 (alle 22 "falsch" + 3 nachgemessene; 16, 25, 31 als Hinweis/PR-Notiz, Ursache außerhalb B)
- Phasenzähler: B = 13 (unverändert, passt zur Roadmap A 11, B 13, C 11, D 8, E 5, F 6, G 7, H 11, I 17 = 89)

## Verbleibende echte User-Entscheidungen

| Plan | ID | Frage | Empfehlung |
|---|---|---|---|
| B | – | keine | – |

Hinweise für andere Pläne (keine B-Entscheidung): Plan D und I kürzen ihre `**Spec:**`-Zeile (Befund 16); Plan E/#1187-T9 muss den Ratchet aus B Task 8 senken (Befund 25) — überholt: T9 behält den Token, Ratchet bleibt 3/2/2/2 (siehe Roadmap-Konsistenz Q1).

## Nicht verifiziert

- Keine Testausführung, kein `sync.py --validate`; alle Test-Erwartungen im Plan sind Plan-Werte.
- Vorher/Nachher-Zählung des Spec-Plan-Vollscans (bricht ab, Befund 16).
- Ob Golden-Fixtures den Text von `rules/1-generic/spec-plan-workflow.md` pinnen (Task 6).
- Ob C-Plan-Tests auf den alten `auto_commit`-Meldungstext prüfen (Befund 41).
- Browser-/Playwright-Läufe (Tasks 10-13), Viz-Live-Test-Fixture (Task 13).
- Live-Payload models.dev kann sich bis zur Umsetzung ändern (P-12 wiederholen).

## Checker (`check_plan_refs.py --no-issues`)

- Vorher: 6 ERROR, 62 WARN. Nachher: 7 ERROR, 74 WARN.
- ERRORs nachher, alle neu geplante Symbole (Klasse a): `auto_commit._STATIC_KEYS`, `_SCHEMA_PATH`, `_load_schema_keys`; `spec_plan._SPEC_RE`, `_TASK_LIKE_HEADER_RE`, `_check_task_detection`; `admin-ui.html::checkboxGroupField`.
- Klassifizierung der Vorher-Meldungen: (a) neu geplant: 9 FILE_MISSING neuer Testdateien, SYMBOL_MISSING für `_DEAD_TOP_LEVEL_KEYS`, `_TASK_LIKE_HEADER_RE`, `spec_plan_no_tasks_detected`, `_check_task_detection`, `_KNOWN_DUPLICATES`, `checkboxGroupField`, `thresholdField`, `test_dead_key_removal_is_idempotent`, `SLOW_TIMEOUT` in Smoke-Datei, alle 6 ERRORs. (b) wirklich veraltet: keine der Checker-Meldungen — die echten Drifts (`context.py`, `config.py`, `sync_pipeline.py`, `cli_commands.py`, `build_variables`) sind nackte `:NNNN`-Anker, die der Checker nicht prüft; manuell gefunden und korrigiert. (c) Checker-Artefakte: alle ANCHOR_DRIFT (Symbole einer Zeile werden dem ersten Anker der Zeile zugeordnet, z.B. `admin-server.py:2846` für `_apply_pricing_overlay`), SYMBOL_MISSING in mitgenannten Dateien (z.B. `_classify` in `rules/...`), absichtlich als fehlend genannte Pfade (`docs/admin-ui.html`, `agents/agent-meta-developer.md`), Kurzpfad `lib/yaml_roundtrip.py`.
- Neue WARNs nachher: ausschließlich (a)/(c) (neu eingefügte Mehrfachnennungen in einer Zeile).


## Phase C

### Review Phase C — `docs/superpowers/plans/2026-11-11-phase-c-sync-config.md`

Basis: `origin/main 9aa0e0c0` (Worktree-Code identisch, `git diff origin/main HEAD -- scripts config rules tests snippets templates .github` leer). Belege per `git -C <repo> show/grep origin/main:...`. Eingriffe: 68 kleine Edit-Operationen am Plan, kein Rewrite. Kein Commit.

## Befunde

| # | Befund | Beleg | Verdikt | Fix |
|---|---|---|---|---|
| 1 | Task-Texte nannten noch Anker vom Stand a3d65da4 (z.B. `_sync_stage_auto_commit_allowlist` :1893, `build_gate_card` :2170, Konstanten :945-946) | `sync_pipeline.py:1974`, `context.py:2329/:2300`, `sync_pipeline.py:969-970/:1029` | falsch | alle Task-/File-Structure-Anker auf 9aa0e0c0 gezogen |
| 2 | Task 1: `--validate` zählt den `auto_commit`-Fehler nicht, Erwartung "3 warnings/0 errors" | `cli_commands.py:1465-1467` (`consistency_errors += 1`, #1091) → Exit :1532/:1534 | falsch | Ist-Zustand korrigiert: rc 1 gibt es schon; offen ist nur Summary + Allowlist-Write |
| 3 | Task 1: Summary-Formatter `report.py:110-114` als Kandidat | `report.py:102-115` `_print_summary` zählt nur Consistency-Findings (`print_report` :44) | falsch (Zuordnung) | korrigiert, `SyncLog.write`-Summary `log.py:165-170` als 2. Weg genannt |
| 4 | Task 1: `log.error` "Ziel laut Log-API prüfen" | `log.py:59` `error(self, target: str, message: str)` | ungeprueft → belegt | exakter Aufruf eingetragen |
| 5 | Task 4: nur eine P0-Stelle, `log.warn` | `sync_pipeline.py:1897` und `:1899` via Alias `log.warning` (`log.py:55-57`) | falsch | beide Stellen + Alias-Signatur mit `p0` |
| 6 | Task 4: "ob CI P0 erzeugt" nicht verifiziert | `.meta-config/project.yaml:293` `ignore-provider-dirs: true`; `gitignore.py:478`, `:533` | ungeprueft → belegt (keine P0) | Abnahme-Text + lokaler Vorlauf-Check `sync.py --fail-on-p0` |
| 7 | Task 4: Step-Umgebung von `validate.yml:126` nicht gelesen | `validate.yml:119-143` | ungeprueft → belegt | eingetragen |
| 8 | `orchestration-test.yml :366` | `orchestration-test.yml:367` | falsch | korrigiert |
| 9 | Task 0: Flag `--validate-spec-plan` "nicht verifiziert" | `sync.py:352`, Handler :101/:783 | ungeprueft → belegt | Step 3 konkretisiert |
| 10 | Task 5: "19 Stellen / 24 Grep-Treffer in 16 Dateien" | `git grep text=True`: 23 Zeilen/15 Dateien; AST-Scan: **1** Stelle `topology-probe.py:229` (Skript `.tmp/c_ast_scan.py`) | falsch | Klasse S statt S-M, Step 2 erwartet 1 Verstoß |
| 11 | Task 5: AST-Test nur auf `subprocess.run/check_output/Popen` | offene Stelle ist `runner(...)` (`topology-probe.py:229`) → Test wäre grün ohne Fix | falsch | Test auf jeden `ast.Call` mit `text=True` |
| 12 | F4/F7 (#1155) "nicht verifiziert" | `config.py:311`, `hooks.py:447`; `write_atomic` `config.py:1420/1486/1507`, `skill_admin.py:99`, `sync_pipeline.py:883` | ungeprueft → per Code behoben | A1/Task 5 Step 5 als Laufzeit-Nachweis |
| 13 | Task 7 Ist-Zustand: `use-orchestrator.md:1-24`, advisory/main-chat ohne Überschrift | `use-orchestrator.md:1-56` strict; `:58` `# Orchestrator`, `:65` `# Main-Chat Mode` | falsch (Befund #1182 bleibt bestätigt) | korrigiert, U2-Option 3 präzisiert |
| 14 | Task 7: Test-Variablen als Bools | `variables.py:351-354` liefern `"true"`/`"false"` | falsch | Strings im Test |
| 15 | Task 7: Variablenquelle "nicht lokalisiert" | `_orch_mode_flags(orch_mode: str) -> dict` `variables.py:339` | ungeprueft → belegt | eingetragen |
| 16 | Task 7: Aufrufer `_build_managed_block ~:2821` | Aufruf `context.py:3077-3079` | falsch | korrigiert |
| 17 | Task 8: Anker :2604-2750/:2281/:2082; `agents-managed.md:8`/`context-anchors.yaml:82-89` nicht gelesen | `context.py:2241/:2440/:2958-2963`; `agents-managed.md:8`; `context-anchors.yaml:89-96` | falsch / ungeprueft → belegt | korrigiert |
| 18 | Task 9: erwartet 2 Treffer, a2a :16 | `branch-guard.md:21`, `repo-containment.md:5`, `a2a-delegation-gates.md:17/:29/:44` = 5 in 3 Dateien; `dod-criteria.md:4` (`docs/REQUIREMENTS.md`) braucht Ausnahme | falsch | Step 1/2 korrigiert |
| 19 | Task 9: Docs-URL-Variable "nicht verifiziert" | Grep `scripts/` `config/`: nur `ANTHROPIC_DOCS_URL` (`model_discovery.py:47`) | ungeprueft → existiert nicht | U1 präzisiert |
| 20 | #1086e "unverifiziert" | `context_budget.py:282-285` Message nur `{provider}` | ungeprueft → offen per Code | Step 1e als konkreter Test |
| 21 | #1086b: `pc` im Scope unklar, Quelle `ai-providers.yaml:156-158` | `hooks.py:488/:490`; `ai-providers.yaml:178` | ungeprueft → belegt / Anker falsch | Fix-Ausdruck konkret |
| 22 | #1086c: Aufrufer-Liste offen | `git grep -c`: 22 Stellen in 15 Dateien | ungeprueft → gemessen | eingetragen |
| 23 | Task 11: Step 1f eigener Commit neben Step-3-Commit | Global Constraint "ein Commit pro Task", Entscheidung 17 | falsch | 1f in den Task-11-Commit |
| 24 | Task 12 h: "Resolver liefert Rolle mit 10", Klasse S | kein Code-Resolver; `delegation_table.py:289` `get_routing_rules`, Rule-Dict :374-386; Issue #1086 (h) "left to the LLM" | falsch | Klasse S-M hinter Task 0, Test auf `get_routing_rules`/`check_keyword_overlap`, U9 umformuliert |
| 25 | Task 12 g: "Issue #1086g schließen" | g ist Unterpunkt von #1086 | falsch (formal) | Entscheidungskommentar, #1086 bleibt offen; neue Frage U11 |
| 26 | Task 13: Import-Zyklus "prüfen" | `progress_paths.py:31` importiert schon `.io`; `io.py:4-12` nur Stdlib | ungeprueft → kein Zyklus | eingetragen |
| 27 | Task 13: neue Warnung "möglich", Opt-out `progress.dir` | `.gitignore:54` `.meta-viz/`; Key `progress.checkpoint-dir` `progress_paths.py:7-9/:43` | falsch | "sicher", richtiger Key |
| 28 | Task 14: "ein Commit", Freshness gegen a3d65da4 | #1189-Plan :133 "Ein Commit pro Task", 16 Tasks; Basis jetzt 9aa0e0c0 | falsch | 16 Commits (Entscheidung 36), Basis 9aa0e0c0; #1189 noch nicht umgesetzt (Grep) |
| 29 | Kopf: Parallelität zu E offen gelassen | Phase-E-Plan :64: nicht disjunkt (`sync_pipeline.py`, `config.py`, `admin-server.py`) | falsch (unvollständig) | "C vor E" eingetragen |
| 30 | Verweise auf Entscheidung 19 statt 35 (Goal, Task 0, Task 14, Entsch. 3/4/8) | Roadmap 7b, Entscheidung 35 | falsch | auf 35 umgestellt |
| 31 | A8: `AGENTS.md:140` nicht gelesen | `AGENTS.md:140` `# CRITICAL GATE` | ungeprueft → belegt | eingetragen |
| 32 | A9: Checker fehlt | `.tmp/wt-check-plan-refs/scripts/check_plan_refs.py` (nicht in origin/main) | falsch (unvollständig) | korrigiert |
| 33 | Phase-Zähler C = 11 Issues, 16 Tasks | Roadmap §2 Zeile C (11); Plan Kopf | korrekt | — |
| 34 | 1 PR pro Phase, einzige C-Ausnahme #1086i | Entscheidungen 17, 18, 36 | korrekt | — |
| 35 | Kette #1187→#1186→#1188→#1181→#1141, #1141 nicht in C | Entscheidung 35; Task 2 | korrekt | — |
| 36 | #1085b nur `--fail-on-p0`, `--strict` `--doctor`-exklusiv | Entscheidung 38b; `sync.py:122-131` | korrekt | — |
| 37 | Trailer-Constraint (#1168), keine "do not set Co-Authored-By"-Zeile | Plan Global Constraints; Entscheidung 25 | korrekt | — |
| 38 | Keine Closing-Keywords in Commit-/PR-Texten | Grep im Plan: nur Regeltext | korrekt | — |
| 39 | Keine destruktiven Git-Befehle, keine kostenpflichtigen Läufe | Grep im Plan | korrekt | — |
| 40 | A3/A4 (`log.py:52-53`, :77, :159-183, :166; `hooks.py:593`) | `log.py`, `hooks.py` gelesen | korrekt | — |
| 41 | A5 `_config_rel_label` :330-338 + 5 Aufrufer | `mcp_provider_config.py:330/399/427/453/621/911` | korrekt | — |
| 42 | A7 Tier-Mapping | `tier-presets.yaml:39`, `:46-48`, `:54-56` | korrekt | — |
| 43 | `detect_shadowed_provider_roots` :457, :478, Text :507-514 | `gitignore.py` | korrekt | — |
| 44 | Signaturen `select_prunable_sync_backups`/`backup_drifted_files` | `generated_file_drift.py:147-151`, `:462-464` | korrekt | exakte Typen eingetragen |
| 45 | `progress_paths.py:34-35/:49/:180`, `checkpoint.py:338/:367` | gelesen | korrekt | — |
| 46 | `validate.yml:126`, `topology-probe.py:229-236`, `test_sync_end_checks.py`/`test_context_compact_mode.py` vorhanden | `git show`/`ls-tree` | korrekt | — |
| 47 | #1189-Plan/Spec APPROVED, 16 Tasks | Plan :4, :22-23; Spec :3 | korrekt | — |
| 48 | Alle 11 Phase-C-Issues OPEN | `gh issue view` (read-only) | korrekt | — |
| 49 | Python 3.9, provider-agnostisch (Task 11 1c über `pc`-Key) | Plan-Text | korrekt | — |

## Zähler

- Befunde gesamt: 49 — korrekt 17, falsch 19, ungeprueft im Plan → jetzt belegt 13 (#4, 6, 7, 9, 12, 15, 19, 20, 21, 22, 26, 31; #17 teilweise).
- Fixes: 32 Befunde im Plan nachgezogen (19 falsch + 13 belegt; 68 Edit-Operationen).
- Phase-Zähler: C = 11 Issues (Roadmap A 11, B 13, C 11, D 8, E 5, F 6, G 7, H 11, I 17 = 89) — unverändert. Tasks: 16 (0, 0b, 1, 3-15). Commits in der Phase-C-PR: Tasks 0, 0b, 1, 3-13 je 1, Task 14 = 16, Task 15 eigener PR.
- Spec-Gate: blockiert jetzt Tasks 4, 6, 7, 8, 9, 10 und Task 12 h (neu). Sofort ausführbar: 1, 3, 5, 11, 12 g.

## Verbleibende echte User-Entscheidungen

| Plan | ID | Frage | Empfehlung (Plan) |
|---|---|---|---|
| C | U1 | #1180: Absolutize vs. Self-contain der `docs/`-Pointer in Regeln | Self-contain (keine Docs-URL-Variable vorhanden) |
| C | U2 | #1182: WARN + Sektion auslassen vs. Gate-Karte nutzt `# Orchestrator`/`# Main-Chat Mode` | Option 1 (WARN) |
| C | U3 | #1195: Wert `SYNC_BACKUP_MAX_TOTAL_PER_DIR` und Verhalten bei Quellen > Limit | 30, neueste je Quelle bleibt |
| C | U4 | #1000: Verhalten ohne Git-Repo; stellt dieses Repo `progress.checkpoint-dir` um? | fail-soft; Entscheidung in Spec 0b |
| C | U5 | #1142: stale Allowlist bei Verstoß liegen lassen | nicht löschen |
| C | U9 | #1086h: Wirkung von `priority` ohne Code-Resolver | nur emittieren (Rule-Dict + Overlap-Message) |
| C | U11 (neu) | #1086 offen lassen, solange f zurückgestellt ist, oder nach a-e, g, h, i schließen? | offen lassen |

U1-U5, U9 werden über die Spec-Freigabe (Task 0/0b) entschieden; U11 ist eine direkte User-Frage. U6, U7, U8, U10 sind jetzt Tasks (Task 5 Step 5, Task 10 Step 1, Task 11 Steps 1e/1f).

## Nicht verifiziert

- F4/F7 (#1155) zur Laufzeit (Code-Lesen: behoben).
- Ort des #1085a-Tool-Regeltexts.
- #1208: Context-Writer und Ursache der `--check`-Blindstelle; Render-Abweichung von `AGENTS.md` nicht ausgeführt.
- Ob der `--validate`-Pfad `SyncLog.write` vor dem Exit erreicht (Task 1 Step 3).
- #1189-Plananker (`admin-server.py:311/:650/:659`, `config.py:888-937`, `tmp_paths.py:298`) gegen 9aa0e0c0.
- Default von `orchestrator.mode`; Schema für `role-defaults.yaml`.
- Keine Tests ausgeführt: alle FAIL/PASS-Erwartungen sind Plan-Werte.

## Checker (`check_plan_refs.py --ref origin/main`)

- Vorher: 11 ERROR, 24 WARN, 3 INFO (`.tmp/c-check-before.txt`).
- Nachher: 11 ERROR, 36 WARN, 3 INFO (`.tmp/c-check-after.txt`). Mehr WARN, weil der Plan jetzt mehr Belege nennt; die zusätzlichen Treffer sind Heuristik-Artefakte (Symbol und Datei in derselben Zeile, aber unabhängig voneinander).
- Die 11 ERROR sind alle Dateien, die der Plan neu anlegt (a): `tests/test_fail_on_p0.py`, `docs/specs/2026-11-11-phase-c-sync-config-spec.md`, `docs/specs/2026-11-11-1000-checkpoint-tracking-spec.md`, `tests/test_sync_backup_retention.py`, `tests/test_gate_card_modes.py`, `tests/test_compact_rule_fallback.py`, `tests/test_rule_doc_pointers.py`, `tests/test_check_context_drift.py`, `tests/test_routing_priority.py`, `tests/test_checkpoint_tracking.py`, `tests/test_subprocess_encoding.py`.
- Einordnung der WARN (Rohbericht vorher):
  - (a) neu geplant: `tests/test_auto_commit_invalid_sync.py`, `tests/test_sync_log_output.py`, `SYNC_BACKUP_MAX_TOTAL_PER_DIR`, `max_total`, `variables_for_mode` (Test-Helfer), `mcp_provider_config.py:330`/`project_root` (neuer Parameter).
  - (b) wirklich veraltet, behoben: `sync_pipeline.py:1811/1812` → :1893, `sync_pipeline.py:1999` → :2080.
  - (c) Checker-Artefakt: `docs/superpowers/plans/2026-11-11-phase-c-1086i-context-split.md` (liegt im Branch `docs/phase-plans`, nicht in origin/main), `scripts/check_plan_refs.py` (bewusst als nicht vorhanden genannt), `consistency/active_set_refs.py`/`consistency/report.py` (Kurzpfad unter `scripts/lib/`), `docs/...md` (Platzhalter im Regex-Text), `.meta-viz/checkpoint-x.json` (Testfixture), `.claude/settings.json` (Default-String), `BaseException`/`_strict_enabled`/`write_atomic`/`compact_embedded_rule`/`_extract_rule_section`/`sync_hooks`/`get_routing_rules`/`detect_invisible_keep_paths` (falscher Datei-Bezug durch Zeilen-Heuristik), `check_dangling_mention` @ :408 (A6 sagt genau das), `delegation_table.py:289`/`routing_patterns` (Funktionsanfang vs. Docstring), `report.py:102`/`print_report`, `sync.py:352`/`_handle_validate_spec_plan`, `variables.py:339`/`SyncError`, `auto_commit.py:167`/`resolve_auto_commit_config`, CREATE_EXISTS `tests/test_context_compact_mode.py` (als "Bestehend" markiert) und `config/tier-presets.yaml` (als "nicht geändert" markiert); ISSUE_CLOSED #1072/#1091/#739 (nur Querverweise).

Hinweis: Im Worktree gibt es außerdem eine uncommittete Änderung an `2026-11-11-phase-b-small-bugs.md`. Die stammt nicht aus diesem Review.


## Phase C-1086i

### Review Phase C / #1086i — `docs/superpowers/plans/2026-11-11-phase-c-1086i-context-split.md`

Basis: `origin/main 9aa0e0c0` (Worktree-Code identisch). Ist-Stand per `ast` (`lineno`/`end_lineno`) gemessen; Aufrufgraph-Skripte `.tmp/c1086i/graph.py` (Plan-Schnitt) und `.tmp/c1086i/graph3.py` (korrigierter Schnitt) im Plan-Worktree. Rund 70 gezielte Ersetzungen; zwei Abschnitte (Ist-Stand/Modulschnitt, Nicht verifiziert) neu gefasst, weil jede Zeile veraltet war. Kein Commit.

## Befunde

| # | Befund | Beleg | Verdikt | Fix |
|---|---|---|---|---|
| 1 | `context.py` hat 3495 Zeilen | `wc -l` auf 9aa0e0c0: 3750 | falsch | Kopf, Goal, Abweichung 1 |
| 2 | "~100 Aufrufer" | `git grep` Importe `scripts`+`tests`: 47 Stellen in 33 Dateien | falsch | Kopf |
| 3 | Modulschnitt-Tabelle mit `def`-Zeilen vom Stand a3d65da4 | `ast` auf 9aa0e0c0: z.B. `_sync_managed_block_context` :899, `_build_managed_block` :2603-3091, `init_claude_personal` :3099 | falsch | Tabelle neu gemessen |
| 4 | Neue Funktionen fehlen im Schnitt | `_position_aware_agent_hints` :799-896, `_shared_topology_flags` :2526-2600 | falsch | in `managed_html` bzw. `base` eingeordnet |
| 5 | Geplanter Schnitt ist ein DAG ("L0-L3") | Graph über den Plan-Schnitt: 8 Modulzyklen, z.B. `adapters -> managed_html -> adapters` (`_dispatch_context_strategy` -> `_sync_managed_block_context`; `_update_managed_html_block` -> `_inject_adapter_line`), `static -> context` (`_ensure_context_file` -> `_project_name`) | falsch (blockierend) | `_project_name`, `_adapter_reference_line`, `_inject_adapter_line`, `_shared_topology_flags` -> `base`; `_dispatch_context_strategy`, `sync_context_adapters_for_provider` bleiben in `context.py`; `graph3.py`: 0 Zyklen |
| 6 | Begründung "`_write_reader_context` ruft `_shared_context_users` (629)" | :629 liegt in `_managed_notes_as_html_comment` (609-645); `reader` hat keine internen Abhängigkeiten | falsch | Begründung mit echten Aufrufern (:629, :832, :2486, :2640) |
| 7 | Task-Reihenfolge 7 (managed_html) und 9 (provider_sync) vor 10 (settings/init_files) | `_sync_managed_block_context` -> `_init_provider_settings_json` (:991); `_sync_opencode_context` -> `init_opencode_personal`; neue Module dürfen `lib.context` nicht importieren | falsch (blockierend) | Ausführungsreihenfolge 0-6, 10, 7, 8, 9, 11-14; Depends-on angepasst |
| 8 | `SNIPPETS_DIR` in `base` UND in Task 11, "Nutzer per Grep klären" | einziger Nutzer `sync_snippets_for_provider` :3707; andere `scripts/`-Treffer sind Platzhalter-Strings | ungeprüft -> belegt | eindeutig in `prompts_snippets` |
| 9 | Quelltext-Scan-Tests fehlen im Plan | `test_compact_rule_channels.py:165-166` (IndexError nach Move), `test_capability_keys_ic09.py:141-143`, `test_context_prompt_index.py:179-184`, `test_provider_agnostic_dispatch.py:314-317` (Allowlist, Schlüssel `Path(module).name` :347), `test_orchestrator_topology_effective_flags.py:53-61` | falsch (blockierend, Suite würde rot) | Liste in "Aufrufer"; Fixes in Tasks 6/7/8/14; Spec-Punkt Step 2b (Ratchet-Allowlist umschlüsseln heißt nicht erweitern) |
| 10 | Test-Importeure unvollständig | `tests/test_entry_hint_topology.py:32`, `tests/test_orchestrator_topology_render_parity.py:47` | falsch | ergänzt, Tasks 7/8/13 |
| 11 | `test_context_adapters.py:699` Namen "nicht gelesen" | :702-705 `_adapter_settings_activation`, `_write_adapter_settings_activation` | ungeprüft -> belegt | eingetragen |
| 12 | Test-/Aufrufer-Anker driften | `agent_sync.py:1498` (nicht 1388), `cli_commands.py:236` (nicht 235), `test_gate_card_compact.py:71/224-228/249`, Idempotency :99/132/166, Compact :670/757, File-Modes :560, Convergence :119/152 | falsch | korrigiert |
| 13 | Lazy-Import-Zeilenliste, Konstanten-Zeilen | `ast`/grep auf 9aa0e0c0 | falsch | neu gemessen |
| 14 | `context.py:3311` importiert `.agent_sync` | `context.py:3566` `from .agent_sync import compose_agent` | falsch | korrigiert |
| 15 | Text-Referenzen (placeholders :163, rules :358/489, config :2020/2041) | `placeholders.py:172`, `rules.py:377/509`, `config.py:2028/2046/2083`, zusätzlich `context_size.py:26,28`, `context_topology.py:40` | falsch | korrigiert |
| 16 | `docs/ARCHITECTURE.md` (Task 14, Checker-ERROR) | nicht im Tree; Modulbeschreibung steht in `docs/CODEBASE_OVERVIEW.md:1506` (10.7) | falsch | Ziel auf `CODEBASE_OVERVIEW.md` umgestellt |
| 17 | #885-Anker `context.py:1678` | Kommentar `placeholders.py:172` zeigt auf `context.py:1761`; `MCP_GUARDRAILS_LIST` liegt bei :2893/:3071 | falsch | Abhängigkeitstabelle; Task 14 zieht Kommentar nach |
| 18 | Abweichung 2: Touchpoint tot, "eigenes Issue"; `ignore_provider_dirs` in `sync_pipeline.py:1814` | `config_audit_providers.py:53-57` dokumentiert das als gewollt (#627); `ignore_provider_dirs` nur `gitignore.py:256` | falsch | umformuliert, kein Issue nötig |
| 19 | Abweichung 4: Checker existiert nicht | liegt in `.tmp/wt-check-plan-refs/scripts/check_plan_refs.py` | falsch | korrigiert |
| 20 | Roadmap-Anker :1710/:2147 "plausibel" | `apply_settings_surface_shape` :1815-1873, `_extract_rule_section` :2300-2326 | falsch | als veraltet markiert |
| 21 | #1086e/f laufen in H nach dem Split | Entscheidung 34 C-N4 / 38c: a-e jetzt in C (vor dem Split), f zurückgestellt | falsch | Abhängigkeitstabelle + Risiken |
| 22 | "Entscheidung 18, einzige Ausnahme" | Entscheidung 36: Ausnahmen #1086i und #1209 | falsch | korrigiert |
| 23 | Task 12 `tests/test_cli_commands*.py` | existiert nicht | falsch | `test_cli_smoke_multi_provider.py`, `test_dispatch_depth_and_hard_cap.py` |
| 24 | Task 14 `sync.py --check` "falls vorhanden" | `scripts/sync.py:334` | ungeprüft -> belegt | korrigiert |
| 25 | Task 6 Patch-Stelle Zeile 204-208 | `test_gate_card_compact.py:224-228`; File Structure nannte "Tasks 7/8" statt 6/8 | falsch | korrigiert |
| 26 | Weitere Monkeypatch-Stellen offen | `git grep` setattr/`"lib.context.`-Strings: nur die zwei bekannten | ungeprüft -> belegt | Task 1 Step 3b wiederholt den Grep |
| 27 | Risiko "Smoke-Test für lazy Importe" unkonkret | — | falsch (Plan-Qualität) | Task 1: `test_lazy_imports_resolve` (importlib.util.resolve_name + import_module + hasattr) |
| 28 | `_build_managed_block` ~473 Zeilen, Datei ~480 | 489 Zeilen; mit `_shared_topology_flags` 564; #1183 (Phase C) ändert die Funktion vorher | falsch | Helper nach `base`; bedingte User-Frage U1 |
| 29 | Paketname/Schichtung als offene User-Frage | wird mit Spec-Freigabe (Task 0) entschieden | falsch eingeordnet | Task 0 Step 2c, keine eigene Frage |
| 30 | Spec-Gate: Task 0 vor allen Implementierungs-Tasks, Klasse L | Task 0 Akzeptanz `Status: APPROVED`; 3750 Zeilen, 47 Importstellen | korrekt | — |
| 31 | Eigener PR direkt nach dem übrigen C, ein Commit je Task | Entscheidungen 17, 18, 36; Roadmap :213, :247 | korrekt | — |
| 32 | Kein Closing-Keyword, keine Co-Authored-By-Constraint | grep im Plan: keine Treffer | korrekt | — |
| 33 | Monkeypatch-Migration Tasks 6/8 (`_load_gate_card_sections` in compact, `TemplateBuilder` in managed_block) | `build_gate_card` :2352, `TemplateBuilder(...)` :3081 in `_build_managed_block` | korrekt | — |
| 34 | `ac01`-Fixtures, `context-profiles-spec`, `test_import_acyclicity` (lazy Importe ausgenommen) existieren | Tree 9aa0e0c0; `test_import_acyclicity.py:10-11` | korrekt | — |
| 35 | Phase-H-Plan verweist auf `context_sync/base.py` für `_backup_context_file` | `phase-h-context-eval.md:42`; `_backup_context_file` bleibt in `base` | korrekt (konsistent) | — |
| 36 | Phase-C-Plan Task 15 verweist hierher, C vor 1086i | `phase-c-sync-config.md:381-383` | korrekt | — |

## Zähler

- Befunde: 36 — korrekt 7, falsch 24 (davon 3 blockierend: #5, #7, #9), ungeprüft -> belegt 5.
- Roadmap-Phasenzähler: dieser Plan hat keine Phasentabelle. #1086 zählt einmal in C (C = 11; A 11, B 13, C 11, D 8, E 5, F 6, G 7, H 11, I 17 = 89, Roadmap :147/:154/:562). #1086i ist ein eigener PR, aber kein eigener Zählposten — konsistent.

## Verbleibende echte User-Entscheidungen

| Plan | ID | Frage | Empfehlung |
|---|---|---|---|
| c-1086i | C1086i-U1 (bedingt) | Falls `managed_block.py` nach #1183 > 600 Zeilen: Budget-Ausnahme für genau diese Datei oder Teilung von `_build_managed_block`? Nur stellen, wenn die Messung in Task 0 Step 2 das auslöst. | Budget-Ausnahme (Teilung verletzt "wortgleich", Verhaltensrisiko) |

## Nicht verifiziert

- Keine Tests, kein `--validate` ausgeführt; Grünstand der Suite vor dem Split unbekannt.
- Aufrufgraph nur über `ast.Name`-Referenzen in top-level-Funktionen; `getattr`/String-Zugriffe nicht erfasst.
- Modulgrößen = Summe der `ast`-Spannen ohne Kopf/Leerzeilen (Planwert).
- Abdeckung der Continue-/Prompt-Pfade durch ac01 nicht geprüft.
- Alle Anker gelten für 9aa0e0c0; der Phase-C-PR verschiebt sie vor dem Start erneut.

## Checker (`check_plan_refs.py --ref origin/main --no-issues`)

- Vorher: 1 ERROR (`docs/ARCHITECTURE.md` :125, nicht im Tree, (b) wirklich veraltet -> behoben), 43 WARN. Rohausgabe `.tmp/c1086i-check-before.txt`.
- Nachher: **0 ERROR**, 71 WARN (mehr, weil der Plan jetzt mehr Referenzen enthält). Rohausgabe `.tmp/c1086i-check-after.txt`.
- Verbleibende WARN-Klassen:
  - (a) vom Plan neu angelegt: `scripts/lib/context_sync/*.py`, `tests/test_context_split_characterization.py`, `tests/fixtures/context-split/*.json`, `docs/specs/2026-11-11-context-split-1086i-spec.md`, Testnamen `test_public_surface_unchanged` u.a., Symbol `context_sync`.
  - (c) Checker-Artefakte: ANCHOR_DRIFT bei Zeilen mit mehreren Ankern (Name gehört zum späteren Anker derselben Zeile, z.B. `cli_commands.py:46`/`:236`, `test_gate_card_compact.py:71`/`:249`, `test_context_adapters.py:41`/`:702`); Kurzpfade `lib/context.py`, `consistency/placeholders.py`; SYMBOL_MISSING durch Zeilen-Heuristik (z.B. `_COMPACT_PLATFORM_RULES` gegen `test_gate_card_compact.py`); `hook_json_get_many` (Entscheidung 28, wird erst geplant); `PROVIDER_TOUCHPOINTS`/`ignore_provider_dirs` gegen `context.py` (Text sagt genau, dass sie dort fehlen).
- Blanke `:NNNN`-Anker von Hand gegen `ast`/grep auf 9aa0e0c0 geprüft (Befunde 3, 12-15, 17, 20, 25).


## Phase D

### Review Phase D — `docs/superpowers/plans/2026-11-11-phase-d-guards-hooks.md`

Basis: `origin/main 9aa0e0c0`. Der Worktree-Code ist identisch (`git diff --stat origin/main -- scripts hooks config agents rules tests` leer). Belege stammen aus Dateien im Worktree. Eingriffe: kleine String-Ersetzungen am Plan, kein Rewrite (60+/58-). Kein Commit.

## Befunde

| # | Befund | Beleg | Verdikt | Fix |
|---|---|---|---|---|
| 1 | `**Spec:**`-Zeile ist Prosa (309 B), der Vollscan bricht ab | `scripts/lib/consistency/spec_plan.py:80` (Regex), `:414` `(project_root / ref).exists()` → Errno 36 | falsch | Zeile enthält jetzt nur den Pfad `docs/specs/2026-11-09-commit-authority-grant-spec.md` (existiert, längste Komponente 41 B). Detail steht in einem eigenen Absatz. `_check_traceability` liefert für D 0 Findings. Der Vollscan bricht weiter ab, jetzt wegen Plan I |
| 2 | Basis `a3d65da4` im Kopf und in den Ankern | Code-Dateien haben sich seit a3d65da4 geändert (`use-orchestrator.md`, `config.py`, `git diff --stat a3d65da4..origin/main`) | falsch | Front-Matter und Kopf auf `9aa0e0c0` gesetzt, Anker nachgemessen |
| 3 | Guard-Anker `:45,:239,:245,:255,:262-269,:307,:326,:333,:384,:418-481,:496,:895,:1262,:1383-1392,:1395-1490,:1527-1547,:1535` | `orchestrator-guard-impl.sh` (1549 Zeilen) | korrekt | — |
| 4 | Spawn-Zählung #1169: Git-Scan „`:1321` Umfeld“, Strict „nicht gezählt“, Gültigkeitsprüfung `:231` fehlt | Python-Starts bei `:214`(Probe), `:231`, `:239`, `:269`, `:307`, `:326`, `:384`, `:1330`, `:1419` = 9; bedingt `:275/:280/:450/:465/:500` | falsch (unvollständig) | Abweichung #1169 neu gezählt. Task 5 Step 2 nimmt `:231` auf (Ziel ≤5 nur, wenn `:231` in den Mehrfeld-Parse wandert, sonst 6) |
| 5 | `hook_json_get_many`: NUL-getrennte Ausgabe; ein `\u0000` in `tool_input.command` verschiebt die Felder (z. B. `cwd` gefälscht) | Design Task 5/7; die Reihenfolge der Felder ist laut Task 7 Step 1 tool_name/agent_id/command/cwd | falsch (Sicherheitslücke im Design, blocking) | Task 5: NUL-Regel (fail closed) in der Spec und der Fehlertabelle. Task 7: Test `test_hook_json_get_many_nul_in_value_cannot_shift_fields` |
| 6 | Task 5 „alle Felder = Default“, obwohl `_many` kein Default-Argument hat | `hook_common.sh:52` `hook_json_get <json-string> <dotted.path> [default]` | falsch (inkonsistent zu Task 7) | Ersetzt durch „leeres Feld, wie hook_json_get ohne default“, Signatur zitiert |
| 7 | Probe-Anker `:208-217` | Probe `:214-218` (`:208` ist ein Kommentar) | falsch | korrigiert |
| 8 | `hook_common.sh` Version 1.9.0, Changelog `:5`, `:63-110`, `:128-131`, `:169`, `:264` | `hook_common.sh:3-5`, Funktionsköpfe | korrekt | Signatur `hook_audit_log_append <logfile> <line>` (`:264-265`, Aufruf Guard `:500`) ergänzt |
| 9 | Audit `:496-499` | Aufruf endet `:500` | falsch (knapp) | `:496-500` |
| 10 | `use-orchestrator.md` `## Git Delegation` „Zeile 53“/„:53-61“, `ROLE_GIT_ACTIVE` „:55“ | Abschnitt `:85-93`, `ROLE_GIT_ACTIVE` `:87` | falsch | korrigiert |
| 11 | Task 2 Step 3: Bedingung `ROLE_GIT_ACTIVE` wiederverwenden. Sie liegt aber in `{{#unless AUTO_COMMIT_ENABLED}}`; dieses Repo rendert den AUTO_COMMIT-Zweig | `use-orchestrator.md:86-91`; gerendertes `.claude/rules/use-orchestrator.md` enthält den Commit-Authority-Satz | falsch (Akzeptanz wäre rot) | Absatz außerhalb beider Zweige (nach `:92`) |
| 12 | Task 2 Test-Assertion vage („Satz `Merge`“) | — | falsch (Planqualität) | konkrete Marker `#1172` + `#783` |
| 13 | `orchestrator.md` Version „8.11.1“ | `agents/1-generic/orchestrator.md:3` = `"8.12.0"` | falsch | korrigiert, §7 `:258-277` |
| 14 | `orchestrator.md:262/:266/:276`, Frontmatter-Tools `:7-11` | Datei | korrekt | — |
| 15 | `git.md` `## 4. Operation :52`, Commit-Format `:134`, BOM `:136`, kein `Co-Authored-By` | `agents/1-generic/git.md` | korrekt | Task 4 Assertion konkretisiert (`Co-Authored-By` ×1 + `verbatim`) |
| 16 | `ai-providers.yaml:64` `hook-agent-id`, `:133` `primary-role-tools`; kein Monitor-Grant | Datei; `grep Monitor config/*.yaml scripts/lib/*.py` ohne Grant | korrekt | — |
| 17 | `hooks/component-config.yaml` „Existenz nicht verifiziert“ | `git ls-files` ohne Treffer | falsch (existiert nicht) | aus Task 1a entfernt, Verweis auf `ai-providers.yaml:64` |
| 18 | `hooks.py`-Baking „Zeile nicht verifiziert“ | `scripts/lib/hooks.py:554-561`, Guard `:360` | ungeprueft → belegt | in Task 8 eingetragen |
| 19 | Testanker `:110,:163,:383,:407,:565,:595,:653,:961,:968,:1002`, `report_contract.py:90-99` | Dateien | korrekt | — |
| 20 | `config.py` `:256/:266/:280/:302/:310/:636/:676-685/:703-708` | Datei | korrekt (ANCHOR_DRIFT des Checkers = Artefakt, siehe unten) | — |
| 21 | Task 12: Aufruf „nach `:671`“ | `:672-674` rufen noch weitere Validatoren auf | falsch (knapp) | „nach `:674`“ |
| 22 | Task 12: „Flag aus `_validate_config` `:676`“ | Flag heißt `_JSONSCHEMA_AVAILABLE`, definiert `config.py:111` | falsch (unpräzise) | Name und Zeile eingetragen |
| 23 | Schema `_comment :12`, `additionalProperties :2854`; `rules-preset/test-repo/backup` fehlen | `python3 json.load` der Schema-Datei; `.meta-config/project.yaml:11/:294/:371` | korrekt | — |
| 24 | Leser der #1141-Keys „nicht gelesen“ | `rules.py:98`, `sync_pipeline.py:194`, `context_profile.py:116-117` (Skalar); `cli_commands.py:133,:141`, `backup.py:48` (Mapping); Top-Level-`mcp` ohne Leser (nur `admin-server.py:508` `viz_cfg.get("mcp")`) | ungeprueft → belegt | Abweichung + Task 11 Step 1 |
| 25 | „`mcp` bis zur Klärung nicht ins Schema aufnehmen“ widerspricht der bindenden Entscheidung 5/35 | Roadmap Entscheidung 5 und 35 | falsch (Konflikt mit Entscheidung) | Aufnahme fest; nur der Typ läuft über das Spec-Gate Task 11. `mcp` im Test `test_known_keys_no_warning` ergänzt |
| 26 | #1181-AC-1/N-9: `git diff --name-only aaed14c2..HEAD -- agents/` muss leer sein | Referenzplan `:1087`, `:1488`, `:1501`; schon auf origin/main nicht leer (`_reference-agent.md`, `orchestrator.md`). Task 2/3/4 ändern `agents/` zusätzlich | falsch (verdeckter Konflikt) | Step A1: Pflicht-Änderungsnotiz, Basis = A-Start-Commit. Strom-B-Commits nie zwischen A-Start und T14 |
| 27 | Datei-Overlap #1181 vs. Strom B „nicht geprüft“ | File-Structure-Map `:279-314` nennt keine der drei Dateien | ungeprueft → belegt (kein Overlap) | Reihenfolge-Abschnitt aktualisiert |
| 28 | „Block A (T16)“ als Ende von Block A | Ausführungsreihenfolge Referenzplan `:60-61`: letzter Task T14 | falsch | Task 11 + Diagramm: Gate G-A/T14 |
| 29 | Render-Diff-Anker „Plan `:76-80`“ | Zielbild Punkt 2 steht `:77-79` | falsch | korrigiert |
| 30 | Referenzplan `:17` (Kette), `:279`, `:1139` T16, `:1200`; Spec APPROVED Rev. 1.4; Spec `:857` (#1172) | Dateien | korrekt | — |
| 31 | Closing-Keywords und Paid-Runs nicht als Constraint geführt | Entscheidung 38e, 11 (analog); Task 3 Step 4 / Task 4 Dry-Run sind echte Agentenläufe | falsch (Lücke) | Global Constraints + Task 3/4/10 ergänzt; `!`-Regel (Entscheidung 12) ergänzt |
| 32 | Trailer-Regel (Entscheidung 25) | Global Constraints: Task-Prompt-Trailer, kein „selbst nicht setzen“ | korrekt | — |
| 33 | Ein PR, Kette #1187→#1186→#1188→#1181→#1141, D = 8 Issues | Front-Matter `issues:` 8 Nummern; Roadmap `:148` | korrekt | — |
| 34 | Spec-Gates: Task 0/1/5/11 vor 8/9/6-7/12; S-Tasks 2/3/4 ohne Spec; #1181 APPROVED | Plan-Abhängigkeiten | korrekt | — |
| 35 | Ratchet `_KNOWN_DUPLICATES` (B Task 8) | betrifft 4 andere Templates; `orchestrator.md`/`git.md` je 1× `{{PROJECT_CONTEXT}}`; #1181-Map ohne `agents/` | korrekt (keine Berührung) | Self-Review-Hinweis |
| 36 | Offene Entscheidungen 2-4 sind Verifikationen, keine User-Fragen | Task 1a, Task 1 Step 2, Task 11 Step 1 | falsch (Einordnung) | als „(Verifikation, Task X)“ markiert |
| 37 | `review-policy-gate.sh` existiert nicht | `git ls-files` 0 Treffer | korrekt | Stand auf 9aa0e0c0 gesetzt |
| 38 | Phasen C/E ändern `config.py`, Schema, `use-orchestrator.md` vor D | Plan C `:481/:498`, Plan E `:344/:350` | korrekt (sequentiell), Anker-Drift erwartet | Hinweis: Anker vor Ausführung neu messen |
| 39 | Commit-Subjects ≤ 72 Zeichen, ohne Closing-Keywords | max. 69 Zeichen | korrekt | — |

## Zähler

- korrekt: 16 (#3, 8, 14, 15, 16, 19, 20, 23, 30, 32, 33, 34, 35, 37, 38, 39)
- falsch: 20 (#1, 2, 4, 5, 6, 7, 9, 10, 11, 12, 13, 17, 21, 22, 25, 26, 28, 29, 31, 36)
- ungeprueft → belegt: 3 (#18, 24, 27); ungeprueft verbleibend in der Tabelle: 0 (Rest unter „Nicht verifiziert“)
- Planänderungen: 28 Befunde (auch korrekte Befunde mit Präzisierung: #8, 15, 35, 37, 38)
- Roadmap-Zähler D = 8: korrekt

## Verbleibende echte User-Entscheidungen

| Plan | ID | Frage | Empfehlung |
|---|---|---|---|
| D | Offen 1 | #1172 Vorschlag 3: Soll eine Provider-Permission-Regel für den `git`-Agenten gebaut werden, oder bleibt es beim Doku-Teil? | Beim Doku-Teil bleiben. Eine Permission-Regel erst nach Evidenz, dass der Provider sie unterstützt |
| D | Offen 5 | #1141: Soll `--audit-config` die Unknown-Key-Warnung ebenfalls zeigen (Issue-Body ja, Issue-AC nur `--validate`)? | Ja, beide über denselben `_validate_config`-Pfad, falls `--audit-config` ihn nutzt (in Task 11 belegen) |

Bedingte Fragen (erst bei negativem Befund): `ask`-Support fehlt (Task 1a → Entscheidung 1: Spec überarbeiten), kein Payload-Rollenfeld (Task 0 → Entscheidung 38a: User bestätigt neu), Typ von Top-Level-`mcp` (Spec-Freigabe Task 11).

## Nicht verifiziert

- Keine Tests, kein `--validate`, kein Benchmark ausgeführt. Spawn-Zahl 9 nur statisch aus dem Quelltext gezählt.
- Inhaltliche Passung von #1181 T5/T8/T16 nach #1190 (Topologie): nicht geprüft. Belegt ist nur, dass die AC-1-Basis gebrochen ist (#26).
- Ob der ganze Vollscan nach dem Fix in D sauber läuft: er bricht weiter an Plan I ab (Prosa-`**Spec:**`, außerhalb dieses Reviews). D allein über `_check_traceability`: 0 Findings.
- Claude-Code-Hook-API (`ask`, Rollenfeld im Payload): extern, nicht geprüft.
- Ob `--audit-config` `_validate_config` aufruft: nicht gelesen.

## Checker (`check_plan_refs.py --ref origin/main`)

- Vorher: 5 ERROR, 46 WARN. Nachher: 5 ERROR, 47 WARN, 2 INFO (mit Issue-Check: #1187 CLOSED, #1218 MERGED, beide erwartet).
- Verbleibende ERROR (alle FILE_MISSING, alle neu geplant): `docs/analysis/2026-11-11-hook-api-ask-permission.md`, `docs/specs/2026-11-11-guard-role-attribution-spec.md`, `docs/specs/2026-11-11-guard-destructive-ask-spec.md`, `docs/specs/2026-11-11-hook-single-parse-spec.md`, `docs/specs/2026-11-11-config-unknown-keys-spec.md`.
- Checker-Artefakte (WARN):
  - ANCHOR_DRIFT `config.py:636` für `_schema_top_level_props/_non_object_top_level_keys/_object_top_level_keys`: Die Self-Review-Zeile nennt mehrere Symbole mit je eigener Zeile (`:256/:266/:302`, korrekt). Der Checker misst alle gegen `:636`.
  - ANCHOR_DRIFT `.meta-config/project.yaml:332` für `_comment`: Gemeint ist das Schema `:12`, nicht `project.yaml`.
  - SYMBOL_MISSING für neue Tests/Funktionen (`hook_json_get_many`, `_warn_unknown_top_level_keys`, `test_*`): Sie sind neu geplant.
  - SYMBOL_MISSING `get_close_matches` (stdlib `difflib`), `agent_type` (hypothetisches Payload-Feld), `authority_overrides` (#1181-Plan neu), `_KNOWN_DUPLICATES` (neu in Plan B). Hinzu kommen Symbole, die der Checker in der falschen Datei sucht (`agent_id`, `run_in_background`, `hook_*` in `config.py`).
- Rohberichte: `.tmp/d-check-before.txt`, `.tmp/d-check-after.txt`.


## Phase E

### Review Plan E (`docs/superpowers/plans/2026-11-11-phase-e-artifact-locations.md`)

Basis: origin/main `9aa0e0c0`, Worktree `docs/phase-plans`. Nur lesend gemessen, keine Tests ausgeführt.

## Befunde

| # | Befund | Beleg | Verdikt | Fix |
|---|---|---|---|---|
| 1 | Roadmap-Pfad `.tmp/roadmap.md` (weicht von der verbindlichen Roadmap ab) | `diff .tmp/roadmap.md docs/superpowers/plans/2026-11-10-backlog-roadmap.md`: verschieden; Pläne A/C nennen den docs-Pfad | falsch | Kopf auf `docs/superpowers/plans/2026-11-10-backlog-roadmap.md` |
| 2 | "Phase E sequentiell nach C" mit Entscheidungen 17, 19 begründet, Roadmap-Hinweis "verworfen" | Roadmap §3 Z.221 (E parallel zu C nur, wenn disjunkt), Regel Z.230; Entscheidungen 17/19 (Z.367-382) sagen nichts zu C/E | falsch (Zuordnung) | Begründung = Roadmap-Regel, Bedingung nicht erfüllt; keine Abweichung. Ordnung C vor E bleibt |
| 3 | Reihenfolge C vor E konsistent mit Plan C | Plan C `:7` "C vor E"; C Files `:69` (`sync_pipeline.py`), Task 14 (#1189 `admin-server.py`) | korrekt | `cli_commands.py` als weitere Überlappung ergänzt |
| 4 | "Phase-C-PRs" (Plural) | Entscheidung 36: #1189 als Commits im C-PR | falsch | "Phase-C-PR (ein PR, enthält #1189, #1195)"; #1086i nicht nötig (Kern berührt `context.py` nicht, Kernplan §2) |
| 5 | Ratchet `_KNOWN_DUPLICATES` (Plan B Task 8) fehlt in Plan E | Plan B `:438-443`, `:450`, `:453` | falsch (Lücke) | Querbezug in E-C0 ergänzt |
| 6 | Plan-B-Annahme "#1187-T9 muss `_KNOWN_DUPLICATES` senken" | #1187-Plan `docs/plans/2026-11-09-project-context-injection-scope-plan.md:376-380`: T9 umschließt `{{PROJECT_CONTEXT}}` mit `{{#if}}`, der Token bleibt; `str.count` bleibt 3/2/2/2 | falsch (in Plan B) | In E dokumentiert: kein Senken nötig, Ratchet-Lauf im T9-Commit. **Plan B Task 8 Step 3 / Kommentar `:437` korrigieren (außerhalb E)** |
| 7 | #1187-Status "nicht prüfbar" | `gh issue view 1187`: CLOSED 2026-11-09T21:55:41Z, COMPLETED, ohne Kommentar; PR #1212 `closingIssuesReferences`=[1187], Docs-only; `git grep PROJECT_CONTEXT_INJECTED origin/main -- scripts agents` = 0; configs enden bei 93 | ungeprüft -> gemessen | Vormessung in E-C0; Matrix-Zeile 2 präzisiert ("Implementierungs-PR"); U10 ergänzt |
| 8 | E-C0 prüft Szenarien 94-98 | `docs/plans/2026-11-09-commit-authority-grant-plan.md:259`: 94 = #1181 (läuft nach E), 95-98 = #1187; "Befund 34 in W" nicht auffindbar | falsch | 95-98 mit Beleg |
| 9 | Spec "Zeile 94" sagt 16 | Spec `:102` und F-1 `:1167`; `:94` ist eine andere Zeile | falsch | korrigiert |
| 10 | 18 einfach + 4 doppelt `SE_BASE_DIR` in 12 Dateien | `grep -o` je `se-*.md`: 22 gesamt, 4 doppelt; kein bloßes `SE_BASE_DIR` ohne Klammern | korrekt | "zweite Zählung steht aus" entfernt |
| 11 | `placeholders.py:198,200` (Fences/Inline), `:195` (Frontmatter) | origin/main: Frontmatter `:204`, Fences `:207`, Inline `:209` | falsch | korrigiert |
| 12 | `config.py:2273` SE_BASE_DIR-Default | `scripts/lib/config.py:2315` (Kommentar `:2312`) | falsch | korrigiert |
| 13 | `consistency-check.py:62/215/222` | `:62` Import, `:215` `check_placeholders`, `:222` `check_command_frontmatter` | korrekt | als gemessen vermerkt |
| 14 | `_VAR_PATTERN :136`, `_FALSE_DEFAULT_CONDITIONALS :59`, `_conditional_active :604-614` (Default `:613`), `strip_inactive_conditional_blocks :662`, `:689/:703/:704` | gelesen | korrekt | — |
| 15 | `_BUILTIN_VARS :12`, `SE_BASE_DIR :98`, `ARTIFACT_ZIP_CMD :59`, `check_placeholders :196`, `load_project_vars :234`, `_rel :245`, `check_builder_known_set :323` | gelesen | korrekt | — |
| 16 | `Finding`/`Severity` in `report.py:29/22`, `ERROR :23` | gelesen | korrekt | — |
| 17 | `PROJECT_WRITABLE_SECTIONS :234`, `_assert_project_sections_writable :5241`, `_assert_project_update_writable :5257` (Signaturen) | gelesen, Signaturen identisch | korrekt | — |
| 18 | Kommentarblock `:225-233` | Block beginnt `:224` | falsch | `:224-233` |
| 19 | 47 Whitelist / 70 Schema / 39 Schnitt / 8 ohne Schema / 31 Schema ohne Whitelist | `ast` + `json` gegen origin/main | korrekt | "nicht nachgerechnet" entfernt |
| 20 | `_make_handler` bei `tests/test_admin_server.py:2153-2158`, "ggf. importierbar" | Methode `TestWriteProjectSectionFeatureBSections._make_handler` `:2124` (Klasse `:2118`), nicht importierbar; `:2153` ist eine Nutzung | falsch / vage | Roundtrip-Test fest in diese Klasse; Files ergänzt; Importweg `:42-51` |
| 21 | `test_variables_stays_unwritable` `:2166-2168` | `:2166` | korrekt | — |
| 22 | Testparser `test_context_profile_admin.py:22-24` (Regex), `test_knowledge_engine.py:574-576` (`ast.dump`) | gelesen | korrekt | — |
| 23 | #1199-Belege `lib/config.py:151,161` | `scripts/lib/config.py:152,162`; Kurzpfade ohne `scripts/` | falsch | korrigiert, volle Pfade |
| 24 | E-T4-Drifttest vs. Plan D Task 12 (#1141 nimmt `rules-preset`, `backup` ins Schema) | Plan D `:64`, `:291` | falsch (Lücke, plan-übergreifend) | Hinweis in E-T4: #1141-Commit muss 2 Einträge entfernen, Zahl 6. **Plan D nachziehen (außerhalb E)** |
| 25 | Kernplan "Voraussetzung 8" (keine Parallel-Edits) | Kernplan `:63` | korrekt | — |
| 26 | 54-Namen-Pin nur in T7 | auch T6 `test_artifact_variable_count_is_54` (Kernplan `:593`); T7 `:623` | unvollständig | beide genannt |
| 27 | `check_artifact_locations` "Name nachlesen, z. B." (Platzhalter in ausführbarem Task) | Kernplan `:810` Signatur `check_artifact_locations(agent_meta_root, project_root, config) -> list[Finding]`; `missing-dir` = INFO `:803` | falsch (Platzhalter) | Signatur eingesetzt |
| 28 | `test_fallback_mentions_inline_mode` in T10/T11 | nur T10 (Kernplan `:714`) | falsch | T10 |
| 29 | `ResolvedMatrix.legacy/unmanaged`, `resolve_artifact_locations`-Signatur | Kernplan `:1164-1174` | korrekt | — |
| 30 | Kern §3.2a: 7 Doku-Bäume `unmanaged`, `docs/superpowers/**` und `audit-*.md` `legacy` | Kernplan `:313-327`, `:452`, `:1393-1394` | korrekt | — |
| 31 | Spec AC-05 Zeile 1111 | Spec `:1111` | korrekt | — |
| 32 | E-T5 "Frontmatter wie andere concepts, nicht verifiziert" | alle 12 `docs/concepts/*.md` beginnen mit `# `, kein YAML-Frontmatter | ungeprüft -> gemessen | Step 2 präzisiert |
| 33 | 4 Audit-Dateien + 9 Doku-Unterbäume existieren | `git cat-file -e` / `ls-tree` | korrekt | Nicht-verifiziert-Punkt entfernt |
| 34 | Version-Bump-Regel unverifiziert | `scripts/lib/consistency/frontmatter.py:48-56` (ERROR bei gleicher Version wie HEAD für geänderte Datei) | ungeprüft -> gemessen | E-T1 Step 2 präzisiert |
| 35 | Check-Regex E-T2 trifft heute nur `SE_BASE_DIR` | Simulation mit `_BUILTIN_VARS | load_project_vars`: `agents/`+`commands/` 12 Dateien nur `SE_BASE_DIR`; `rules/` 0 von 49 | korrekt (Planwert gestützt) | in U8 vermerkt |
| 36 | `check_plan_refs.py` "Existenz nicht geprüft" | nicht in origin/main; Branch `chore/check-plan-refs` | ungeprüft -> gemessen | E-T0 Step 2 + Global Constraints konkret |
| 37 | `docs/api/pal-variables.md` "nicht verifiziert" | existiert in origin/main | ungeprüft -> gemessen | U7/E-T7 angepasst |
| 38 | Py3.9: `set[str] \| None` in Signatur | `placeholders.py:2` und `admin-server.py:38` haben `from __future__ import annotations` | korrekt | — |
| 39 | Konsistenz Entscheidungen: ein Phasen-PR + Ausnahme #1209; Kette; Trailer wörtlich (25); keine Closing-Keywords; kein `Co-Authored-By`-Verbot | Plan-Grep; Roadmap §3/§4 | korrekt | — |
| 40 | Spec-Gate: #1209 (M) hinter E-T7; #1186 APPROVED; #1198/#1199/#1200 S | Kernplan-Kopf `status: APPROVED`; E-T7/E-T8 | korrekt | — |
| 41 | Zähler E = 5 | Roadmap §2 Z.149 | korrekt | — |
| 42 | E-T4 Commit-Typ `test:`, ändert aber `scripts/admin-server.py` | Plan E-T4 Step 4 | ungeprüft (Judgment, nicht blockierend) | nicht geändert |
| 43 | E-T7-Commit: welcher Branch (Phasen-PR oder #1209-PR) bleibt offen | Plan E Block 4 | ungeprüft (Judgment, nicht blockierend) | nicht geändert |

## Zähler

- korrekt: 20 (3, 10, 13-17, 19, 21, 22, 25, 29-31, 33, 35, 38-41)
- falsch: 16 (1, 2, 4, 5, 6, 8, 9, 11, 12, 18, 20, 23, 24, 26, 27, 28)
- ungeprüft -> jetzt gemessen: 5 (7, 32, 34, 36, 37); ungeprüft offen: 2 (42, 43); Summe 43
- Fixes im Plan: rund 25 Edit-Stellen (alle 16 "falsch"-Befunde außer #6, der Plan B betrifft, plus die 5 Messungen)

## Verbleibende echte User-Entscheidungen

| Plan | ID | Frage | Empfehlung |
|---|---|---|---|
| E | U10 | #1187 ist nur per Docs-PR #1212 geschlossen, Code fehlt: #1187 vor Block 2 nachziehen oder Abhängigkeit #1187 -> #1186 streichen? (Roadmap-Konflikt 8) | keine (Plan legt nicht fest; Kernplan nennt #1187 als Voraussetzung 2, `:51`) |
| E | U8 | `placeholders.single-brace` auch auf `rules/` ausweiten? | Plan: nicht ausweiten (heute 0 Treffer) |
| E | U1-U7 | Spec-Inhalte #1209 (Gate-Form, `files` vs `file`, Suffix-Match, Default, Umfang, AC-05-Inhalt, Doku-Ort) | Empfehlungen in E-T7 Step 1; entschieden mit Spec-Freigabe |

## Plan-übergreifend (außerhalb E zu fixen)

- Plan B Task 8 (`2026-11-11-phase-b-small-bugs.md:437`, `:453`): Aussage "#1187-T9 muss `_KNOWN_DUPLICATES` senken" stimmt nicht; T9 behält den Token im `{{#if}}`.
- Plan D Task 12 (#1141): muss `_RUNTIME_ONLY_SECTIONS` um `rules-preset`, `backup` kürzen und `test_runtime_only_count_is_eight` auf 6 setzen.

## Nicht verifiziert

- Keine Tests, kein `consistency-check.py`, kein `--validate`; alle "Erwartung"-Zahlen (4/10/4 passed) sind Planwerte.
- Status #1189 und CI nicht abgerufen.
- Kern-Signaturen (E-T6, E-T8) stammen aus dem Kernplan, Code existiert noch nicht.
- `pipeline_stages` `implement: 1` gegen die Pipeline nicht geprüft.

## Checker

- Vorher (Rohbericht, Abschnitt E): 0 ERROR, 64 WARN.
- Nachher: 0 ERROR, 67 WARN, 1 INFO (`.tmp/e-check-after.txt`). Ein Zwischenlauf hatte 7 ERROR (Artefakt: gemischte Datei-/Symbolzeile im Frische-Abschnitt); durch Aufteilen in Einzelzeilen behoben.
- WARN-Klassen: (a) neu geplant: FILE_MISSING für `tests/test_se_single_brace_placeholders.py`, `tests/test_admin_whitelist_drift.py`, `tests/test_artifact_subtree_classification.py`, `docs/concepts/artifact-subtree-classification.md`, `docs/specs/2026-11-12-artifact-mode-template-gating-spec.md`, `tests/test_artifact_mode_gating.py`, Kern-Dateien (`scripts/lib/artifact_locations.py`, `config/artifact-locations-presets.yaml`, `hooks/1-generic/artifact-path-guard.sh`, `tests/test_artifact_locations_{placeholders,variables}.py`, `tests/test_consistency_artifact_locations.py`), Plan-B-Datei `tests/test_project_context_placeholder_ratchet.py`; SYMBOL_MISSING für alle neuen Testnamen, `check_single_brace_placeholders`, `_RUNTIME_ONLY_SECTIONS`, `_build_artifact_variables`, `check_artifact_locations`, `_MODE_*`. (b) wirklich veraltet: `config.py:2273`, `test_admin_server.py:2153` (beide behoben) plus die von Hand gefundenen nackten Anker (#9, #11, #18, #23). (c) Checker-Artefakte: ANCHOR_DRIFT `admin-server.py:248` (Anker gilt `backup`, Symbol `PROJECT_WRITABLE_SECTIONS` aus derselben Zeile), `tests/test_admin_server.py:42` (Importweg-Anker, Symbole derselben Zeile), SYMBOL_MISSING in mitgenannten Dateien (`_BUILTIN_VARS` in `report.py`, `_comment` in `test_admin_server.py`), `se_output` (im Schema absichtlich fehlend).


## Phase F

### Review Phase F (Label-Taxonomie) — Plan `docs/superpowers/plans/2026-11-11-phase-f-label-taxonomy.md`

Basis: origin/main `9aa0e0c0` (`git show origin/main:<pfad>`). Kein Code/Test ausgeführt.

## Befunde

| # | Befund | Beleg | Verdikt | Fix |
|---|---|---|---|---|
| 1 | `_handle_backup` bei `cli_commands.py:1032` | Def `scripts/lib/cli_commands.py:1060` | falsch | -> `:1060` (File Structure, Frische-Check, Task 1, Self-Review) |
| 2 | `args.label` bei `:1046` | `label=args.label` `cli_commands.py:1074` | falsch | -> `:1074` |
| 3 | `ISSUE_LANGUAGE` bei `config.py:2720(-2722)` | Zuweisung `config.py:2762-2764` in `_build_convention_variables` `:2715` | falsch | korrigiert (3 Stellen) |
| 4 | `_validate_config` bei `config.py:635` | `config.py:636` | falsch | -> `:636` |
| 5 | `--backup`-Hilfetext bei `sync.py:455` | `sync.py:451-454` (Satz "Use --label" `:454`) | falsch | -> `:451-454` |
| 6 | `_normalize_check_dry_run`-Aufruf ":811 nicht belegt" | Aufruf `sync.py:811` in `main()` `:804` | falsch (offen gelassen) | belegt eingetragen |
| 7 | `_build_arg_parser` `:217`, `allow_abbrev=False` `:223`, `--label` `:456-457`, Def `_normalize_check_dry_run` `:113` | `scripts/sync.py` | korrekt | — |
| 8 | Presets `namespace` `:56,93,125`; `_render_git_issue_naming` `:277`, `:285,290`, Aufruf `:132` | `config/conventions-presets.yaml`, `scripts/lib/conventions.py` | korrekt | — |
| 9 | `viewProjectConventionsOverrides` `:4156`, `DOMAIN_FIELDS` `:4189-4204`, `issues` `:4198-4203` | `docs/ui/admin-ui.html` | korrekt | — |
| 10 | `cli-reference.md:209`, `backup.py:18`, `test_cli_smoke_multi_provider.py:101` (`--label`) | jeweilige Dateien | korrekt | — |
| 11 | `meta-feedback.md:48`, BFA-Matrix `:93-97`, `:117`; `incident-responder.md:72,126`; `template-auditor.md:114` | `agents/1-generic/*` | korrekt | — |
| 12 | Referenzplan-Anker `:1154` (F-1), `:1157` (F-4), `:1177` (Kritische Tasks), `:1313-1316`; Status APPROVED; Basis `aaed14c2` | `docs/plans/2026-11-09-issue-label-taxonomy-plan.md:2,12` | korrekt | — |
| 13 | Kern-Spec `Status: APPROVED` | `docs/specs/2026-11-09-issue-label-taxonomy-spec.md:3` | korrekt | — |
| 14 | Kern-Anker `config.py:2673-2734` | `_build_convention_variables` jetzt `:2715` | falsch (Referenzplan-Drift) | in Task K Step 1 annotiert; Referenzplan unverändert |
| 15 | "nicht verifiziert": `from scripts.sync import` importierbar? | `tests/test_checkpoint_cli.py:317` (`from sync import _build_arg_parser`) | geklärt | Muster in Task 1 Step 2, Eintrag entfernt |
| 16 | "nicht verifiziert": `test_conventions_migration_invariant.py` pinnt Block? | nur Abwesenheit `:87`; Referenzplan `:364` "nicht ändern" | geklärt | Task 2 Step 2 |
| 17 | Task 2 übersieht gepinnten Alt-Wert | `tests/fixtures/slimming-golden/git.md:154` (`type: <type>`) | falsch (Lücke) | Fixture-Update + Tests in Task 2 Step 2/3 aufgenommen |
| 18 | Task 4 Verifikation `tests/test_contract_labels.py` | Datei prüft Output-Contract-Marker (#541), kein `DOMAIN_FIELDS` (`:1-15`) | falsch | entfernt |
| 19 | "nicht verifiziert": HTML-Textparse-Tests möglich? | `tests/test_admin_ui_git_section.py:17` (`read_text`) | geklärt | Muster in Task 4 eingetragen |
| 20 | Task 4 Teil-1-Tests (`language` in `DOMAIN_FIELDS.issues`) scheitern nach Teil 2 (Domain entfernt); ein Commit für zwei zeitlich getrennte Teile | Plan Task 4 alt Step 1/3/5 | falsch | Task 4 auf zwei Commits aufgeteilt, Teil-2-Tests definiert |
| 21 | Klassifikation #1204 Teil 2 "M, durch Kern-T26 abgedeckt" | Referenzplan F-4 `:1157`: T26 fasst alte View nicht an | falsch | Teil 2 als S (Inhalt fixiert durch Entscheidung 34 F-neu-6), keine Spec |
| 22 | `**Spec:**`-Zeile lang (Errno-36-Risiko) | Plan Z. 21 alt | falsch | auf Pfad-Pointer gekürzt, Zuordnung in "Klassifikation" verschoben |
| 23 | Kein Constraint zu Live-Label-Ops / Closing-Keywords / Trailer | Entscheidungen 25, 38e; Referenzplan `:1051` (kein echtes Netz) | Lücke | Global Constraint ergänzt (Label-Löschung nur als `!`-Befehl) |
| 24 | Base-Header/Frontmatter `a3d65da4` | Roadmap 7b, Konfliktpunkt 7: Pläne auf `9aa0e0c0` | falsch | auf `9aa0e0c0` gesetzt, Frische-Check neu |
| 25 | Zähler F = 6, Summe 89 (11+13+11+8+5+6+7+11+17) | Roadmap `:150`, Entscheidung 35 | korrekt | — |
| 26 | Entscheidungsnummern 5, 17, 19, 25, 26, 34 (F-neu-4/5/6), 35 | Roadmap Abschnitt 7/7b | korrekt (F-neu-3 -> 26 nur inhaltlich zuordenbar) | — |
| 27 | Ein Phasen-PR, kein Co-Authored-By-Verbot, keine Closing-Keywords | Plan-Grep | korrekt | — |
| 28 | Issue-AC #1201 "GitHub = `bug`" vs. Referenzplan `type/…` | `.tmp/issues/1201.md:47`; Referenzplan `:1154` | korrekt als offene User-Entscheidung | — |
| 29 | Doppelte Graphify-Zeile in "Nicht verifiziert" | Plan alt Z. 287/291 | falsch | Duplikat entfernt |

## Zähler

- korrekt: 13 (7-13, 25-28)
- falsch: 14 (1-6, 14, 17, 18, 20-22, 24, 29)
- Lücke ergänzt: 1 (23)
- geklärt (vorher ungeprüft): 3 (15, 16, 19)
- ungeprüft: 0
- Roadmap-Zähler F = 6: korrekt.

## Offene echte Entscheidungen

| Plan | ID | Frage | Empfehlung |
|---|---|---|---|
| F | F-offen-1 | #1201: GitHub-Projektion `bug` (Issue-AC `.tmp/issues/1201.md:47`) oder `type/bug` (Referenzplan K-7/F-1 `:1154`, APPROVED)? | nicht beantwortet (wird in Task 0 dem User vorgelegt) |

## Nicht verifiziert

- Welcher Test die Fixture `tests/fixtures/slimming-golden/git.md` byte-genau vergleicht (Kandidaten `test_template_slimming_equivalence.py`, `test_ac01_render_identity.py`); Task 2 misst.
- Kern-Anker des Referenzplans `sync.py:757-787`, `admin-server.py:234-259`, `placeholders.py:114-123` (Task K Step 1).
- `render_priority_table`-Signatur (Kern existiert nicht).
- Labels per `gh label list` nicht abgefragt (Plan macht keine Aussagen über Live-Label-Namen/-Anzahl).

## Checker

- Vorher: 3 ERROR, 46 WARN (`.tmp/f-check-before.txt`).
- Nachher: 3 ERROR, 53 WARN (`.tmp/f-check-after.txt`; WARN-Zuwachs durch neue Anker-Zeilen).
- ERRORs (alle Kategorie (a), neu geplant): `scripts/lib/issue_conventions.py`, `scripts/lib/issue_adapters.py` (Referenzplan File Structure `:305` "neu"), `docs/specs/2026-11-11-issue-label-children-spec.md` (Task 0).
- Verbleibende ANCHOR_DRIFT: Checker-Artefakte (c) — Zeilen mit mehreren Ankern (Frische-Check Z. 95, Task 4 Interfaces), bewusst zitierte Alt-Anker (Issue `:4157` in Abweichung 5, Referenzplan `config.py:2673`).

## Cross-Plan

- E: #1187 laut E-Review durch Docs-PR #1212 ohne Code geschlossen (Frage U10). Task V Step 2 sperrt Task K, solange #1187 "nicht erfüllt" — Ergebnis von U10 bestimmt den Start von Phase F.
- D: #1181 erst nach F-Kern; #1141 nach #1181 im D-Plan (Entscheidung 35) — Plan konsistent.
- Roadmap `:222` sagt "#1203 erst nach #1188-Kern"; Plan zieht #1203 vor (Issue erlaubt "vor oder mit", Abweichung 4). Technische Ordnung, keine User-Entscheidung; Roadmap-Zeile ggf. nachziehen.
- Dateikonflikte `docs/ui/admin-ui.html` / `scripts/sync.py` mit A/B/C: nicht gegen deren Pläne geprüft.

## Phase G

### Review Phase G (Provider) — 2026-11-11

Plan: `docs/superpowers/plans/2026-11-11-phase-g-provider.md`. Geprüft gegen `origin/main 9aa0e0c0`. Seit der Plan-Basis `a3d65da4` haben sich von den referenzierten Dateien nur `scripts/lib/config.py` und `scripts/lib/agent_sync.py` geändert (`git diff --stat a3d65da4 origin/main -- <G-Dateien>`).

## Befunde

| # | Befund | Beleg | Verdikt | Fix |
|---|---|---|---|---|
| 1 | Basis `a3d65da4`, Anker "nach Rebase neu prüfen" | diff-stat s.o. | falsch (veraltet) | base-commit/Header auf `9aa0e0c0`, Re-Verifikations-Notizen entfernt |
| 2 | `config.py:353-355` Fail-closed-Muster | `config.py:354-356` | falsch | korrigiert |
| 3 | `_validate_providers` `config.py:716` | `config.py:717` | falsch | korrigiert |
| 4 | `agent_sync.py:417` (Issue-Anker, "nicht neu geprüft") | `target_dir = project_root / pc['agents_dir']` jetzt `agent_sync.py:483` | falsch | Task 0b korrigiert |
| 5 | `export_skill_pack`-Signatur "nicht gelesen" | `hermes_export.py:486-492` | ungeprüft -> belegt | Signatur in Task 1 + Self-Review eingetragen |
| 6 | Task 1 Rot-Verifikation `-k fails_closed` deckt 2. Test nicht ab | Testnamen im Plan | falsch | `-k "fails_closed or without_pyyaml"` -> 2 failed (Plan-Wert) |
| 7 | Task 1 Einfügestelle "vor `:541`" | `generic_dir` `:512`, `read_version` `:541` | unpräzise | erste Anweisung vor `:512`, `Raises:` ergänzen |
| 8 | Task 1 Klassen/Fixture `TestExportSkillPackMiniRepo`, `mini_meta :122`, `TestCli` | `tests/test_hermes_export.py:122,245,565` | korrekt | Platzierung + `_run_main` ergänzt |
| 9 | `_YAML_AVAILABLE :98-102`, `main :655`, except `:679-681`, `_SKILL_DIR :125`, `resolve_abstract_tier :217`, Fallback `:292-295` | hermes_export.py | korrekt | — |
| 10 | `load_roles_config` `roles.py:53`, leere Rollen `:71-72`, Cache-Docstring `:56` | roles.py | korrekt | — |
| 11 | io.py PyYAML-Warnung `:71-73` | `io.py:72` | korrekt | — |
| 12 | ai-providers.yaml `:179-182`, `:203`, `:214`, `:250`, allowed-fields `:387-414`, Kommentar `:399-405` | grep -n origin/main | korrekt | — |
| 13 | provider-tools.yaml `:41`, `:142` | grep -n | korrekt | — |
| 14 | Task 2 Step 2 "Vollständigkeit nicht verifiziert" | YAML-Parse: nur Gemini `tool-name-map.Bash=run_command`; `terminal_tool` hat 9 Provider | ungeprüft -> belegt | Erwartung grün als statisch geprüft markiert |
| 15 | Task 2 xfail-Erwartung `code_execution == code_execution != run_command` | `:203`, `:142`, `:250` | korrekt | — |
| 16 | `#1175` heute nicht in ai-providers.yaml (Task 3 Test 1 rot) | grep | korrekt | — |
| 17 | Evidenz `runtime-opencode-v1.md:63-74`, `:131-132`; audit part1 `:132,155-156,330`; consolidation `:42-43` | sed origin/main | korrekt | — |
| 18 | mcp_provider_config `:167,:187,:222-227,:261-275,:292,:158-163`; Signatur `_build_connection_entry` | grep/sed | korrekt | — |
| 19 | `test_stdio_command_*` `:1064-1102` | `tests/test_mcp_config.py:1078-1102` | falsch | korrigiert |
| 20 | plugins.py `:77,:84,:89` | probe_plugin_availability | korrekt | — |
| 21 | `projectatlas` mit `config-generated-by` im Katalog | `plugin-catalog.yaml:372-398` | korrekt | — |
| 22 | commands.py `:147`, Formate `:165-167`, Dispatch/Fehler `:259-266` | grep | korrekt | — |
| 23 | provider-capabilities G4-1..G4-3 `:289-291`; contracts `:60`; hooks-Tests `:361`, `:375` | sed | korrekt | "nicht neu gelesen" entfernt |
| 24 | Hermes nur in hermes_export.py + 4 Testdateien | git grep -il | korrekt | — |
| 25 | Issue-Anker #800 (`io.py:66-69`, `config.py:242-245`, `~199-230`, `:417`), #1175 `378-391`, #814 `134-147` | `.tmp/issues/*.md` | korrekt zitiert | — |
| 26 | Spec-Gate-Grep `Status: APPROVED` | `_APPROVED_RE` `consistency/spec_plan.py:85-87` erkennt `Status: **APPROVED**` nicht | korrekt, Hinweis fehlte | Formhinweis in Task 0a |
| 27 | Kostenpflichtige Läufe (Task 5 agy-Probe, Task 6 Request-Capture) ohne Kosten-Gate | Roadmap §4 | falsch | Gate in Global Constraints + Task 5/6 |
| 28 | Closing-Keyword-Regel fehlte | Entscheidung 38e | falsch (Lücke) | Global Constraint ergänzt; Commit-Betreffs enthalten keine |
| 29 | Destruktive-Git-Regel fehlte | Roadmap §4 | Lücke | Constraint ergänzt (keine im Plan) |
| 30 | C-Flag ohne Name | Entscheidung 4/38b | unpräzise | `--fail-on-p0` ergänzt |
| 31 | Trailer (Entscheidung 25) | Plan Global Constraints | korrekt | keine Verbotszeile vorhanden |
| 32 | Ein Phasen-PR, ein Commit je Task | Entscheidung 17/36 | korrekt | — |
| 33 | G-N1/G-N3/G-N4 "final erst nach Probe-Evidenz" | `.tmp/decisions-part2.md:22` ("each final only after probe evidence") | korrekt | — (Roadmap §7b `:476` lässt das für G-N1 weg, siehe Cross-Plan) |
| 34 | File Structure unvollständig (3 Testdateien, Task-6-Evidenz) | Tasks 4, 6, 8 | falsch | ergänzt |
| 35 | `**Spec:**`-Zeile Prosa | Vorgabe kurz | unpräzise | auf `keine (Spec-Gates: Task 0a/0b/0c)` gekürzt |
| 36 | Skill `provider-agnostic` "nicht gefunden" | nur ungetrackt im Main-Checkout `.claude/skills/provider-agnostic` | teilweise | Formulierung präzisiert |
| 37 | Freshness-Check-Skript "Existenz nicht verifiziert" | nicht auf origin/main, liegt in `.tmp/wt-check-plan-refs/scripts/` | präzisiert | Constraint angepasst |
| 38 | Roadmap-Zähler G = 7 | Roadmap §2 `:151`, Entscheidung 35 | korrekt | — |
| 39 | Klassifizierung (S/M/L) und Spec-Gates 0a/0b/0c vor Task 7/8/9/10 | Plan-Tabelle | plausibel | — |
| 40 | Provider-Agnostik: Format-Werte, keine `provider ==`-Zweige; Namensliteral-Tests Task 8/10 | Plan | korrekt | — |
| 41 | Rollen `requirements`, `senior-developer`, `tester`, `developer` | `agents/1-generic/` | korrekt | — |

Zähler: 41 Befunde — korrekt 24 (inkl. #39 plausibel), falsch/Lücke/unpräzise 15 (alle gefixt), ungeprüft -> belegt 2. Offen ungeprüft: 0 Befunde (Rest siehe "Nicht verifiziert").

## Checker

- Vorher: 5 ERROR, 24 WARN. Nachher: 5 ERROR, 27 WARN (+3 WARN = neu gelistete geplante Testdateien in File Structure).
- ERROR (alle (a) neu geplant): `docs/analysis/runbooks/antigravity-runtime-probe.md`, `docs/analysis/runbooks/opencode-request-options-probe.md`, `docs/guides/hermes-integration.md`, `docs/specs/2026-11-11-800-hermes-provider-target-spec.md`, `docs/specs/2026-11-11-gemini-target-platform-spec.md`.
- ANCHOR_DRIFT `mcp_provider_config.py:261` / `hermes_export.py:125`: (c) Checker-Artefakt (ordnet Symbole derselben Zeile dem Anker zu; Anker selbst stimmen: Stdio-Zweig `:261`, `_SKILL_DIR` `:125`).
- SYMBOL_MISSING (Testnamen, `unknown_connection_keys`), FILE_MISSING WARN: (a) neu geplant.

## Offene echte Entscheidungen

| Plan | ID | Frage | Empfehlung |
|---|---|---|---|
| G | G-O1 | Probe-Art und Evidenzpfad, mit denen G-N1 (#800 Option A) final wird | Spec 0b schlägt vor, User gibt frei |
| G | G-O2 | Phasen-PR öffnen/mergen, solange Tasks 5, 6, 0c, 8, 9, 10 extern/probe-gesperrt sind (Entscheidung 17 regelt nur 1 PR) | User entscheidet; Optionen: PR mit entsperrten Tasks mergen und Rest nachziehen vs. warten |
| G | G-O3 | Kostenfreigabe für Task 5/6 (echte Provider-Läufe) | Kostenschätzung vor Ausführung vorlegen |

"Ist die `gemini`-CLI auf dem Host probebar" ist eine Mess-Aufgabe, keine Entscheidung (Task 0c Consumes).

## Nicht verifiziert

- Keine Tests/kein `--validate` gelaufen; rot/grün-Erwartungen sind Plan-Werte.
- Opencode-Quelle, Capture-Weg, `agy`/`gemini`-CLI-Verfügbarkeit, `pclmul` des Hosts.
- `cwd`-Unterstützung der Zielformate (Herstellerdoku), Schreibpfad `mcp_provider_config.py` jenseits `:320`.
- Hermes-seitige Fakten und Messzahlen aus #800.

## Cross-Plan

- G vs H (beide Welle 4, laut Roadmap parallel): nicht disjunkt. H Task 8 (O-H1, `roster_in_harness`) legt Flag-Ort in `provider-capabilities.yaml`/`ai-providers.yaml` fest; H Task 24 (F-OC2) liest die Opencode-Allow-list, die G Task 3 kommentiert. Im Plan vermerkt: sequentiell oder Rebase.
- D (Welle 3) ändert `config/ai-providers.yaml` (D-Plan `:253`); B ändert `provider-capabilities.yaml` (G4-2) und `provider_transform.py`; C ändert `mcp_provider_config.py` (`_config_rel_label`, Aufrufer). G-Anker nach deren Merge neu messen (im Plan vermerkt).
- #1086i (`context.py`) berührt G nicht.
- Roadmap §7b `:476` (G-N1) lässt "endgültig erst nach Probe-Evidenz" weg, Quelle `.tmp/decisions-part2.md:22` gilt für G-N1, G-N3, G-N4. Roadmap-Text nicht geändert (nicht Auftrag); Korrektur beim Roadmap-Owner.

## Phase H

### Review Phase H (Kontext/Token/Eval) — Fragment

Plan: `docs/superpowers/plans/2026-11-11-phase-h-context-eval.md` · Basis `origin/main 9aa0e0c0` · Review 2026-11-11.
Methode: `git show`/`git grep` gegen `origin/main`, Checker `check_plan_refs.py --no-issues`, Issue-Texte `.tmp/issues/`. Nichts ausgefuehrt (keine Tests, kein Sync).

## Befunde

| # | Befund | Beleg | Verdikt | Fix |
|---|---|---|---|---|
| 1 | Kopf: Basis `a3d65da4`, Abhaengigkeit "D-Strom C" | Roadmap §3 Z. 225 (H haengt von B, C ab); kein "D-Strom C" in der Roadmap | falsch | Basis 9aa0e0c0, B/C + Task 10 nach D |
| 2 | `**Spec:**`-Zeile ist Prosa | `consistency/spec_plan.py:401-414` liest den Wert als Pfad | falsch | Zeile = nur Pfad, Prosa in Folgezeile |
| 3 | "#1161 Pkt 5 gehoert zu Phase D" | Roadmap Z. 427: "#1169 in Phase D, #1161 Punkt 5 in Phase H" | falsch | Klassifikation, Abweichung 5, Entscheidungstabelle umformuliert |
| 4 | "Roadmap Zeile 422" fuer Entscheidung 28 | Roadmap Z. 424-427 | falsch | korrigiert |
| 5 | Re-Pin-Tasks "12/17" | Re-Pin steht in Tasks 6, 13, 21 | falsch | korrigiert |
| 6 | `agents.py:515-521` / `name_index :343` | `agents.py:541` (separators), `:364`, `:423` | falsch | korrigiert |
| 7 | Prune-Anker `sync_pipeline.py:1005/:946/:957-1002/:973-983` | `:1029`, `:970`, `:981-1026`, `:997-1006` | falsch | korrigiert |
| 8 | `sync.py:632` | `_preview_backups_to_prune` `sync.py:622`; Preview nur Agent-Dir (`:676ff`) | falsch | korrigiert, Akzeptanz praezisiert |
| 9 | `_IST_COMPACT :582` | `tests/test_context_budgets.py:583` | falsch | korrigiert |
| 10 | K-01/K-13 "-> Task 12" | K-01/K-13 stehen in Task 18 | falsch | korrigiert |
| 11 | K-13 `config.py:2337-2338` = `PROJECT_SPECIFIC_AGENTS` | stimmt auf Issue-Basis `96f5a2e5`; auf 9aa0e0c0 `:2379-2381` | korrekt | Hinweis ergaenzt |
| 12 | `rules.py:478` ohne Default / `:583` Default Claude | `provider: str` `:436`, `:498`; Default `"Claude"` `:605` | falsch | korrigiert |
| 13 | Task 23: `providers.py:358` per Config-Lookup ersetzen | Fallback fuer fehlendes ai-providers.yaml; Guard nimmt `providers.py` bewusst aus (`tests/test_provider_agnostic_dispatch.py:367-369`) | falsch | `providers.py` aus Task 23 entfernt |
| 14 | F-PA1-Anker isolation `:725/:1156/:1751`, cli `:324-344`, sync_pipeline `:893/:1573`, consistency `:97/:88` | `:796/:1204/:1915`; cli `:327/:340/:372`; sync_pipeline `:917/:1636/:1652`; topology `:115`, orchestrator_strict `:93` | falsch | korrigiert |
| 15 | F-PA1 "39 Fundstellen in 6 Testdateien" | `git grep -c -w`: 53 Zeilen in 9 Testdateien + 29 in 4 Lib-Dateien inkl. `deactivation.py:259-261` | falsch | Files + Akzeptanz (`git grep` leer) |
| 16 | `validator.md:38-39` ungegated | liegt in `{{#if DOD_REQ_TRACEABILITY}}` `:35-41`; nur `:53` ungegated | falsch | Abweichung 13, Task 21 |
| 17 | #1167 "107 Treffer in 39 Dateien" | `git grep -c -E 'REQ-ID\|REQ-xxx' -- agents/1-generic`: 90 Zeilen / 36 Dateien | falsch | korrigiert |
| 18 | O-H1: Flag-Name/-Ort offen | `roster_in_harness` existiert (`config/provider-capabilities.yaml:140..667`), `EMIT_AGENT_ROSTER` `context.py:2777-2786`; Template gated nur Compact (`templates/context/agents-managed.md:20-21`) | falsch | O-H1 geschlossen, Abweichung 15, Task 8 |
| 19 | O-H3: Zuordnung lifecycle-check/sync-on-config-change offen | Entscheidung 28 legt #1161 Pkt 5 in H | falsch | in Task 10 aufgenommen |
| 20 | Task 10 "D-Task 6 (optional)" | D-Task 6 = Benchmark; optionaler Schritt steht in D-Task 7 (D-Plan Z. 248) | falsch | korrigiert |
| 21 | Task 10 ohne ac01-Re-Pin | `tests/fixtures/ac01-baseline/hashes.json:102,107,116,118` pinnen gerenderte Hooks | fehlt | Files + Step ergaenzt |
| 22 | Task 10 Commit-Betreff = optionaler D-Commit | D-Plan Z. 248 | falsch | neuer Betreff |
| 23 | Task 5 `--model-class <name>=<provider>:<modell>` | Format `NAME=PROVIDER/MODEL` (`run_role_routing_eval.py:18,644`) | falsch | korrigiert, Flag-Anker belegt |
| 24 | `compute_case_outcomes`-Schluessel `ambiguous` | heutiges Grade-Dict nutzt `ambiguous_expected` (`run_role_routing_eval.py:200-216`) | falsch | korrigiert |
| 25 | McNemar fuer top1 + collision (Design) vs. nur top1 (Task 2) | `per_case` traegt nur `correct` | inkonsistent | auf top1 vereinheitlicht |
| 26 | Task 4 Test-Dokument `per_case {"c1": [...]}` ohne Klasse | Schema `{cls: {case_id: [...]}}` (Task 2) | falsch | korrigiert |
| 27 | `mcnemar_exact`-Interface-Text verstuemmelt ("b = ... Konvention") | Plan Z. 128 alt | falsch | bereinigt |
| 28 | McNemar-Erwartungswerte (0,8)->0.0078125, (3,3)->1.0, c=3/b=0 -> 0.25, 10/0 -> 2/1024 | Handrechnung exakter Binomialtest | korrekt | — |
| 29 | Task 20 `check_req_ids(...) -> List[str]`, Registrierung unbekannt | Checks liefern `List[Finding]`; Registrierung in `cli_commands.py::_handle_validate` `:1408`, Muster `check_temp_literals` `:1507`, `temp_literals.py:559-563` | falsch | Signatur + Files korrigiert |
| 30 | `tests/test_external_tools_drift.py` | existiert nicht; vorhanden: `test_external_tools_drift_catalog_ref.py`, `test_external_tools_registry.py` | falsch | korrigiert |
| 31 | Task 24 vergleicht mit "Doku-Liste aus der Zieldatei", Rot -> Doku aendern | Liste in keiner Repo-Datei; Issue verlangt Listen-Angleichung; G-N4 + G-Tasks aendern `config/ai-providers.yaml` | falsch | Task 24 = Befundnotiz, Listenaenderung nach O-H6 |
| 32 | Entscheidungen 35-38 nicht beruecksichtigt (36, 38e), keine `!`-Regel | Roadmap Z. 493-508, §4 | fehlt | Global Constraints + Entscheidungstabelle |
| 33 | G/H "parallel" ohne Dateiabgleich | G aendert `.meta-config/project.yaml` (G-Task 8) = H-Task 17; G aendert `config/ai-providers.yaml`/`provider-capabilities.yaml`, H liest sie (Tasks 10b, 23, 24) | fehlt | Abhaengigkeitszeile G + O-H7 |
| 34 | H fasst `context.py` nicht an (Ordnung zu #1086i) | Task 7 nur `sync_pipeline.py`; Task 10b nur Template, da `EMIT_AGENT_ROSTER` schon berechnet | korrekt | Zeile C-1086i ergaenzt |
| 35 | Paid-Run-Gate Task 5 | `--estimate-only` ohne Provider (`:17`), `--approval` `:865`, Entscheidung 11 | korrekt | #1014-Evalfaelle als kostenpflichtig ergaenzt |
| 36 | Anker eval_gate (`:28-33`, `:53-54`, `:124`, `:245`, `:331`) und Runner (`:186`, `:287`, `:363`, `:520`, `:769`, `:830`, `:930`, `:1021`) | `git show origin/main` | korrekt | — |
| 37 | `context_report.py:130,:156`; Budget-Test `:291-299`, `:300`, `:308`, `:341-354`, Toleranzwerte 4096/256/0.02 | `git show origin/main` | korrekt | — |
| 38 | 28 `hook_json_get`-Aufrufe in 6 Dateien | `git grep -c -w` | korrekt | — |
| 39 | `delegation_table.py:229,:253`, Test `:219`, `role-defaults.yaml:189-190,:2668`, `provider-expert` 0 Treffer | `git show`/`git grep` | korrekt | Signaturen in Tasks 12/13 ergaenzt |
| 40 | `orchestrator.md:385-386`, `principal-developer.md:171`, `senior-developer.md:164`, `dod-presets.yaml:54-55`, `standalone.py:130-134` | `git show` | korrekt | — |
| 41 | `project-config.schema.json:1160-1162`, `mcp.py:427,477` | `git show` | korrekt | — |
| 42 | `branch-guard.md` Z. 5/18/21 | `git show` | korrekt | — |
| 43 | `docs/REQUIREMENTS.md:4` und Abschnitte 9..110 | `git show` | korrekt | — |
| 44 | Spec "§9.1 / IC-36" | IC-36 ist `### IC-36` `:1937`; "§9.1" nicht belegt | falsch | auf Zeile 1937 umgestellt |
| 45 | #960 nichts gebaut | `git grep model_range origin/main` = 0 | korrekt | aus "Nicht verifiziert" in Task 16 |
| 46 | Roadmap-Zaehler H = 11 | Roadmap §2 Z. 152, Entscheidung 35 | korrekt | im Self-Review vermerkt |
| 47 | Task 7: Wurzelverzeichnis prunen ist sicher | `select_prunable_sync_backups` nur direkte Kinder (`generated_file_drift.py:153-155`) | korrekt | — |
| 48 | File Structure: `tests/test_routing_language_guard.py` unter Modify | Datei neu (Checker ERROR) | falsch | nach Create verschoben |
| 49 | Task 22 als S (82 Zeilen, 13 Dateien, rein mechanisch) | Urteil | ungeprueft (judgment) | belassen, Umfang im Task vermerkt |
| 50 | Task 6 importiert `tests.test_context_budgets` (pytest als Laufzeit-Abhaengigkeit des Helpers) | `test_context_budgets.py:44` | ungeprueft (advisory) | Hinweis im Task |
| 51 | Erwartete rot/gruen-Zustaende und Exit-Codes in Steps | nicht ausgefuehrt | ungeprueft | als Plan-Werte markiert |

## Zaehler

- korrekt: 15 · falsch/fehlend: 33 · ungeprueft: 3 (gesamt 51)
- Fixes im Plan: 33 Korrekturen (alle Zeilen "falsch/fehlt/inkonsistent"), plus Nicht-verifiziert- und Self-Review-Abschnitt neu.

## Offene echte Entscheidungen

| Plan | ID | Frage | Empfehlung |
|---|---|---|---|
| H | O-H2 | Ziffernzahl im REQ-Regex: `\d{2}` (woertlich `<NN>`) oder `\d{2,3}`? | `\d{2}`, falls die Messung in Task 19 keine Nummer > 99 je Bereich findet |
| H | O-H4 | Wartet der eine H-PR auf alle sechs Spec-Gates samt Folge-Tasks, oder geht er mit den freigegebenen Tasks? | mit den freigegebenen Tasks; nicht freigegebene Folge-Tasks in einen Folgeplan |
| H | O-H5 | #339 schlaegt `REQ-L2-AT-018` vor (`.tmp/issues/339.md:47`), D-H4 `REQ-<AREA>-<NN>`: mehrteilige Bereiche zulassen? | D-H4 strikt; #339 passt sich bei Neufreigabe an (Entscheidung 30) |
| H | O-H6 | F-OC2: Darf H die Opencode-Allow-Liste aendern (`max_tokens`, `subagent`), oder nur den Befund belegen? | nur Befund in H; Listenaenderung nach G-Probe-Evidenz (G-N4) |
| H/G | O-H7 | G und H sind nicht dateidisjunkt: welche Phase merged zuerst? | G zuerst (aendert die Provider-Configs, die H liest) |
| H | O-H8 | #1014-Folgeplaene: welche Phase, welcher PR-Schnitt (Issue: "One PR per step", Entscheidung 36 ohne Ausnahme)? | eigener spaeterer Phasenplan mit einem PR, bis der User eine Ausnahme setzt |

Geschlossen ohne User-Frage: O-H1 (Flag existiert im Code), O-H3 (Entscheidung 28).

## Nicht verifiziert

- Keine Tests/kein Sync/kein Render ausgefuehrt; alle Erwartungen in Steps sind Plan-Werte.
- Inhalt von `tests/test_routing_overlap.py`, `tests/test_routing_keyword_overlap_check.py`, `config/review-rules/`, `config/tier-presets.yaml`, `scripts/lib/roles.py` nicht gelesen.
- Herkunft der F-OC2-Liste (`steps, top_p, disable, prompt`): im Repo nicht gefunden.
- D-Spec-Inhalt (#1169) nicht gelesen; nur D-Plan Z. 210-248.
- `UEBERGREIFENDE-MUSTER.md` (#1014) nicht im Repo.

## Checker

- Vorher: 3 ERROR, 97 WARN.
  - `tests/test_routing_language_guard.py` (Z. 112): neu geplant, unter "Modify" gelistet -> (b) behoben (jetzt Create).
  - `docs/superpowers/plans/2026-11-11-phase-c-1086i-context-split.md`, `docs/superpowers/plans/2026-11-11-phase-d-guards-hooks.md`: liegen auf Branch `docs/phase-plans`, nicht auf `origin/main` -> (c) Checker-Artefakt.
- Nachher: 2 ERROR (beide (c), Geschwisterplaene), 98 WARN. Report: `.tmp/h-check-after.txt`.
- Verbleibende ANCHOR_DRIFT-WARN sind (c): der Checker ordnet Symbole dem ersten Anker der Zeile zu (z.B. `name_index` an `agents.py:541`, `_backup_context_file` an `generated_file_drift.py:199`), oder der Anker ist bewusst der veraltete Issue-Anker (`test_context_budgets.py:270`, `orchestrator.md:385` fuer K-01). SYMBOL_MISSING/FILE_MISSING-WARN: neu geplante Symbole/Dateien (a).

## Cross-Plan-Hinweise

- **G:** nicht dateidisjunkt. `.meta-config/project.yaml` (G-Task 8 / H-Task 17) wird von beiden geaendert; `config/ai-providers.yaml` und `config/provider-capabilities.yaml` aendert nur G, H liest sie (Tasks 10b, 23, 24). H-Task 8 legt **kein** neues Flag an (`roster_in_harness` existiert); die G-Review-Annahme "H legt Flag-Ort fest" ist damit hinfaellig. H-Task 24 aendert die Allow-Liste nicht mehr (O-H6). Reihenfolge: O-H7.
- **C-1086i:** H aendert `context.py` nicht. C-1086i-Plan Z. 26 behauptet, #1161 Pkt 5 beruehre `context.py`/`context_sync` — falsch (Pkt 5 = Hooks); Pkt 2 nur, falls die Spec eine Variablenaenderung verlangt. Korrektur im C-1086i-Plan empfohlen (nicht hier editiert).
- **C:** aendert `templates/context/agents-managed.md` (C-Plan Z. 296) und Retention-Konstanten `sync_pipeline.py:969-970` (C-Plan Z. 119); H-Task 7/10b rebasen auf C.
- **D:** `hook_json_get_many` entsteht in D-Task 7; H-Task 10 haengt am D-Merge. Der optionale D-Schritt (D-Plan Z. 248) und H-Task 10 teilen sich `repo-containment-impl.sh`/`dod-push-check.sh`; H uebernimmt nur, was D nicht umgestellt hat.
- **E/F/C/D:** `scripts/lib/cli_commands.py` wird auch von C, D, E, F geaendert; H-Tasks 20 und 22 messen Anker nach deren Merge neu.

## Phase I

### Review Plan I (`docs/superpowers/plans/2026-11-11-phase-i-features-concept.md`)

Basis: origin/main `9aa0e0c0`, Belege per `git show origin/main:<pfad>`, `git grep`, `gh issue view` (read-only), Stand 2026-11-11.

## Befunde

| # | Befund | Beleg | Verdikt | Fix |
|---|---|---|---|---|
| 1 | `**Spec:**`-Zeile Prosa (363 B) → Errno 36 im Vollscan | `scripts/lib/consistency/spec_plan.py:80` (Regex), `:414` `(project_root / ref).exists()` | falsch | Zeile 10 = `keine (Spec-Gates je Issue, siehe »Fahrplan je Issue«)`; Ausnahmen in neue Zeile `**Bestehende Specs/Pläne:**`. `check_spec_plan_workflow(W)` läuft durch (1101 Findings gesamt, 0 für Plan I, kein Crash) |
| 2 | "Phase I liefert pro Stufe Concept-/Spec-PRs", "Teil-PR" (Z. 8, 64, 66, 101, 148, 180) widerspricht 17/36 | Roadmap 7b Entscheidung 17 (Z. 369), 36 (Z. 495) | falsch | ein PR für Phase I, ein Commit je Item/Teil; Umsetzungs-PR "nach Entscheidung 17" |
| 3 | "Teil-PR je Feature, Roadmap §3" | Roadmap §3 (Z. 211-235) enthält das nicht | falsch | Verweis entfernt |
| 4 | I-N2 "getrennte Specs/PRs" | `.tmp/decisions-part2.md:22` "separate specs" | falsch | auf "getrennte Specs" korrigiert (Fahrplan #676/#1106 und Abschnitt 34) |
| 5 | File Structure `<datum>-hacs-best-practice-spec.md` (676+1106) = gemeinsame Spec, widerspricht I-N2 | dito | falsch | Spec nur #676, #1106 eigene Teilspecs |
| 6 | `admin-server.py:978` Bind-Host-Origin | Z. 978 = Docstring "Raises SecurityError"; Kommentar Z. 981-982 | falsch | `:981-982` |
| 7 | `orchestrator.md:105` "Guardrail zu erfundenen Tool-Aufrufen" | Z. 105: "kein natives `route_intent`-Tool registriert" | falsch | Beschreibung korrigiert |
| 8 | BARRIER "258-271+" | `orchestrator.md:258`, `## 8. Reflection loop` Z. 278 | falsch (ungenau) | 258-277 |
| 9 | `bugfix-wave-plan.md:449` "setzt #877 voraus" | `docs/plans/2026-10-06-bugfix-wave-plan.md:449` "möglicher Duplikat zu #820", Z. 452 Empfehlung | falsch | korrigiert, Pfad ergänzt, durch Entscheidung 7 erledigt |
| 10 | `glob("*.md")`-Liste unvollständig (Summe 29/17 stimmt) | `git grep -c 'glob("\*\.md")' origin/main -- scripts` | falsch (Liste) | vollständige Liste inkl. `consistency/commands.py`, `_migrations/...` |
| 11 | #897 State "unverifiziert" | `gh issue view 897` = CLOSED | falsch (veraltet) | CLOSED eingetragen, Abhängigkeit #896 aufgelöst |
| 12 | "Phase G: kein Plan in W" | `docs/superpowers/plans/2026-11-11-phase-g-provider.md` existiert, #1171 Z. 16 | falsch | Verweis gesetzt, Frische-Liste ergänzt |
| 13 | Entscheidungs-Bereiche "§7", "17-34", "17-38" (Z. 16, 222, 259, 306) | Roadmap §7 (1-16) + §7b (17-38) | falsch | auf 1-38 / §7/§7b |
| 14 | Verifikationen als "Offene Entscheidungen" (#339 Rest, #896/#897, #957 Konsistenz, #548 Zerlegung, HA-Prüfer) | Auftrag Check 7 | falsch | neuer Abschnitt »Prüf-Tasks« P1-P8 |
| 15 | #339 Spec §10 offene User-Punkte fehlten | Spec `2026-10-07-339-...md:293-301` (OQ-12, R2) | falsch (Lücke) | als offene User-Entscheidung zur Re-Approval aufgenommen |
| 16 | `check_plan_refs.py` nicht in origin/main | `git ls-tree` | korrekt | Pfad präzisiert |
| 17 | `def load_config` Z. 332 | `scripts/lib/config.py:332` | korrekt | – |
| 18 | PROJECT_SPECIFIC_AGENTS Z. 2381, Kommentar 2379 | `config.py:2379/2381` | korrekt | – |
| 19 | `orchestrator.md:22` ask-user, `:258` BARRIER, `:304` Fallback | gelesen | korrekt | – |
| 20 | `planner.md:3` `1.6.1`, kein `parallel_with`/`conflicts_with` | grep | korrekt | – |
| 21 | `provider-capabilities.yaml:57-66` route_intent_tool | Kommentarblock 57-66, Werte ab 124 | korrekt | präzisiert |
| 22 | `ask_user_tool` existiert nicht | `git grep`: nur Roadmap Z. 79 | korrekt | – |
| 23 | #339 Spec `status: APPROVED`, `approved_by: concept-reviewer`, `size: M`, §0 HK-1..5 in `se_cascade.py`, `--validate-se` | Spec Z. 2/9/11/22-34; `scripts/sync.py:344` | korrekt | – |
| 24 | Archiv-Concept v1.2, `docs/architecture/07-se-cascade.md` | `git ls-tree`, Concept Z. 3 | korrekt | – |
| 25 | Admin-Plan DRAFT Z. 11, PR #913 Z. 59 | gelesen | korrekt | – |
| 26 | PR-Templates-Spec DRAFT Z. 11 | gelesen | korrekt | – |
| 27 | Commits `23893133`, `81b913c` | `git cat-file -t` = commit | korrekt | – |
| 28 | `hacs-integration-development.md`, `platform-configs/{hacs,homeassistant,sharkord}.defaults.yaml` | `git ls-tree` | korrekt | – |
| 29 | Phase I = 17 Issues | Roadmap Z. 153, Plan Z. 7 (17 Nummern) | korrekt | – |
| 30 | Abhängigkeiten #1085c/#1142 (C), #1176/#1141 (D), #1167/#969 (H), #1171 (G) | Grep in den Phasenplänen | korrekt | – |
| 31 | Spec-Gate: keine ausführbare Umsetzungs-Task vor APPROVED | Plan ist Konzept-Fahrplan (Roadmap Z. 185 "keine Umsetzung"); Prüf-Tasks read-only | korrekt | – |
| 32 | Keine Closing-Keywords, keine "Co-Authored-By nicht setzen"-Vorgabe, keine destruktiven Git-/Bezahl-Läufe | grep | korrekt | – |
| 33 | #339 Klasse M, #1004 L, #820+877 XL plausibel | Spec §10 Z. 295; Entscheidung 7 | korrekt | – |
| 34 | `gitignore.py`, `se_validate.py` existieren | `git ls-tree` | korrekt | – |
| 35 | `hermes_export.py`-Fundstellen #820 | – | ungeprueft | P6 |
| 36 | IC-17/IC-18 Umsetzung (#958) | – | ungeprueft | P7 |
| 37 | Externe HA/HACS-Aussagen, Provider-Ask-User-Matrix | – | ungeprueft | P4, P8 |
| 38 | Merge PR #913 | – | ungeprueft | P2 |
| 39 | `config/provider-tools.yaml`, `hacs-integration-development.md` Inhalt, `config_audit.py` | – | ungeprueft | – |

Plan-Qualität (writing-plans): Dokument ist bewusst ein Konzept-Fahrplan ohne TDD-Tasks (Roadmap Z. 185, 226); Header Goal/Architecture/Tech Stack/Spec, Global Constraints, File Structure vorhanden. Keine TBD außer `<datum>`.

## Zähler

- korrekt: 19 (Nr. 16-34)
- falsch: 15 (Nr. 1-15), alle gefixt
- ungeprueft: 5 (Nr. 35-39)
- Roadmap-Zähler I = 17: korrekt. Sweep 57/24/7/1 = 89 aus der Tabelle (Roadmap Z. 34-140) neu gezählt: korrekt. Phase-I-Anteil: 11 ECHT_OFFEN + 6 TEILWEISE.

## Offene echte Entscheidungen

| Plan | ID | Frage | Empfehlung |
|---|---|---|---|
| I | #339-OQ12/R2 | Spec §10: `sub_components`-Schematiefe; Wrapper-Agent R2 bauen oder `--validate-se` in CI genügt? | bei der Re-Approval (Entscheidung 30) beantworten |
| I | #329/#330 | Baseline-Freeze in `project.yaml`; neue Metrik-Rolle vs. Erweiterung; Interaktion requirements/release | in den Specs (38d) vorlegen |
| I | #1004 | Quelle `max_concurrent_agents`; Graph-Format Mermaid/ASCII | in der #1004-Spec |
| I | #957 | MVP-Set-Feinschnitt; Manager-Rückmeldung (#548) | in der Spec-Revision |
| I | I-UMS | In welcher Phase/welchem PR läuft die spätere Umsetzung der 17 Items? (17 gilt je Phase; keine Umsetzungsphase definiert) | eigene Folgephase(n) je Umsetzungsplan, Entscheidung durch User |

## Nicht verifiziert

- Nr. 35-39.
- Ob `check_spec_plan_workflow` Plan I überhaupt als Plan klassifiziert (0 Findings für Plan I trotz `Spec: keine (...)`).

## Checker

- Vorher: 9 ERROR, 14 WARN (`.tmp/i-check-before.txt`). Nachher: 10 ERROR, 22 WARN (`.tmp/i-check-after.txt`).
- Alle ERROR = FILE_MISSING für Phasenpläne A-I (inkl. neu verlinktem `phase-g-provider.md` und Plan I selbst), die nur im Branch `docs/phase-plans` liegen → (c) Checker-Artefakt (Ref origin/main).
- WARN: `W/...`-Präfixpfade → (c) Artefakt (Dateien existieren ohne Präfix, per `git ls-tree` geprüft); `docs/concepts/se-cascade-optimization-339.md` → bewusst als nicht existent genannt; SYMBOL_MISSING `merge_gate`, `max_concurrent_agents`, `ask_user_tool` → (a) vorgeschlagene/künftige Namen.

## Cross-Plan-Hinweise

- Roadmap-Sweep-Zeilen veraltet (nicht editiert, außerhalb Scope): #339 Concept-Pfad (archiviert), #896 "hängt an #897" (#897 CLOSED), #1004 Anker `:240-276` (jetzt 258-277) und Klasse M (Plan: L).
- #681, #1004-E, #1113 sequentiell nach Plan D (#1176) wegen `orchestrator.md` (16 Treffer in Plan D).
- #832/#958/#820+877 nach Plan C und `context.py`-Split (#1086i, eigener PR).
- Phase-I-PR ist ein großer Docs-PR (Entscheidung 36); Rebase-Konflikte mit parallelen Phasen-PRs in `docs/`.

## Roadmap-Konsistenz und Querbezuege

Stand: 2026-11-11, W = `.tmp/wt-phase-plans`, Code-Basis origin/main `9aa0e0c0`. Zeilenangaben = Stand nach Fix.

| Nr | Befund | Beleg | Verdikt | Fix |
|---|---|---|---|---|
| Q1 | Plan B Task 8: "#1187-T9 muss `_KNOWN_DUPLICATES` senken" | `docs/plans/2026-11-09-project-context-injection-scope-plan.md:376-380` (T9 umschliesst den Token mit `{{#if}}`, Token bleibt); E-Plan `:119` | falsch | B `:437-438` (Kommentar), `:454` (Step 3): Ratchet bleibt 3/2/2/2, T9 laesst den Test nur mitlaufen; B-Review-Hinweis (Abschnitt Phase B, "Hinweise fuer andere Plaene") als ueberholt markiert |
| Q2 | Plan D Task 12 (#1141) erwaehnt die E-T4-Drift-Tests nicht | E-Plan `:239-245` (`test_runtime_only_count_is_eight`, Kuerzung um `rules-preset`/`backup`) | fehlt | D `:69` (Files-Liste), `:298` (Files), `:302` (Step 2): `_RUNTIME_ONLY_SECTIONS` ohne `rules-preset`/`backup`, erwartete Anzahl 6, Drift-Test mitlaufen |
| Q3 | C-1086i: "#1161 Pkt 5 beruehrt `context.py`/`context_sync`" | H-Plan `:71` (Pkt 5 = `hook_common.sh`/Hooks), `:125` (Files nur `hooks/1-generic/*`), `:49`; Pkt 4 nur `sync_pipeline.py` (`:44`) | falsch | C-1086i `:26`, `:390`: Pkt 5 nur Hooks; Pkt 2 nur falls die H-Spec eine Variablenaenderung verlangt |
| Q4 | H-Ueberschriften "Pkt 5 in Phase D" widersprechen Entscheidung 28 ("#1161 Punkt 5 in Phase H") und H-Task 10 | Roadmap Entscheidung 28; H-Plan `:27`, `:235` | inkonsistent | H `:207`, `:219`: Funktion/Spec in D, Rest-Hooks H-Task 10 |
| Q5 | F-Plan Task 2 verweist auf "Offene Entscheidungen" Punkt 2, die Liste hat nur Punkt 1 | F-Plan `:219-221` | falsch | F `:172` auf Punkt 1 |
| Q6 | Roadmap Welle 1 und Sweep #1194: `context.py:1710` | `git show origin/main:scripts/lib/context.py`: `apply_settings_surface_shape` `:1815` | veraltet | Roadmap `:110`, `:218` |
| Q7 | Roadmap #1203 "erst nach #1188-Umsetzung" / "#1203/#1211 erst nach #1188-Kern" | Issue `.tmp/issues/1203.md:53` ("vor oder mit der Einfuehrung"); F-Plan `:19`, `:113` (Task 1 vor Kern-T21) | veraltet | Roadmap `:118`, `:180`, `:222`; #1211 bleibt nach dem Kern (Pilot-Gate) |
| Q8 | Sweep #339: Concept unter `docs/concepts/se-cascade-optimization-339.md` | `git ls-tree origin/main`: nur `docs/concepts/archive/2026-06-se-cascade-optimization-339.md` | veraltet | Roadmap `:44` |
| Q9 | Sweep #896 "haengt an #897" | `gh issue view 897` = CLOSED (2026-11-11) | veraltet | Roadmap `:64` |
| Q10 | Sweep #1004 Anker `orchestrator.md:240-276`, Klasse M | origin/main `## 7. BARRIER protocol` `:258`, `## 8.` `:278`; Plan I `:176` Klasse L (Entscheidung 9) | veraltet | Roadmap `:73` (`:258-277`, L mit Sweep-Vermerk M) |
| Q11 | §7b G-N1 ohne "endgueltig erst nach Probe-Evidenz" | `.tmp/decisions-part2.md:22` ("each final only after probe evidence" fuer G-N1, G-N3, G-N4) | unvollstaendig | Roadmap `:476` |
| Q12 | Kette C -> E -> F -> D; Roadmap Welle 2 sagte "E parallel zu C, falls disjunkt" | E-Plan `:64`, `:431`; C-Plan `:7` (nicht disjunkt: `sync_pipeline.py`, `config.py`, `admin-server.py`). Kette #1187 -> #1186 (E) -> #1188 (F) -> #1181 (D) -> #1141 (D) gleichlautend in E `:65`, F `:27`, D `:103`, Roadmap `:223` | Bedingung nicht erfuellt | Roadmap `:220-221`: E haengt von C ab, keine Parallelitaet |
| Q13 | G parallel zu H (Roadmap Welle 4) | G-Task 8 und H-Task 17 aendern `.meta-config/project.yaml` (G `:77`, H `:328`); G-Plan `:281`, H-Plan `:48` | inkonsistent | Roadmap `:224-225`: nicht dateidisjunkt, sequentiell; Reihenfolge bleibt User-Frage O-H7 (Empfehlung G zuerst) |
| Q14 | H haengt laut Roadmap nur von B, C ab | H-Task 10 nach D-Merge (H `:46`), H nach #1086i (H `:44`) | fehlt | Roadmap `:225` |
| Q15 | #681/#1004-E/#1113 nach D (#1176) | I-Plan `:118`, `:178`, `:200` | korrekt | Roadmap Welle 5 `:226` ergaenzt |
| Q16 | #832/#958/#820+877 nach C und #1086i | I-Plan `:132` (#832 nach C; aendert `config.py`, nicht `context.py`), `:139-141` (#958 nach #1086i), `:146-148` (#820+877) | korrekt (fuer #832 genuegt C) | Roadmap `:226` |
| Q17 | Phase C vs. E Dateiueberlappung | C `:7`, E `:64` | korrekt, gleichlautend | — |
| Q18 | Verbotene Reste (Closing-Keywords in Commit/PR-Texten, "kein Co-Authored-By selbst setzen", `isolation: "worktree"`, `if provider ==`) | Grep ueber Roadmap und alle Phasenplaene: Treffer nur als Verbot ("kein ..."), als Entscheidung-25-Regel (Trailer aus dem Task-Prompt) oder als Zitat des historischen PR-Texts `Closes #1190` (A `:68`, Roadmap `:509`) | korrekt | — |
| Q19 | Phasenzaehler Plaene vs. Roadmap | Issue-Listen der Plan-Koepfe (A `:19`, B `:16`, C `:5`, D/F Frontmatter `issues:`, E `:12`, G `:16`, H `:11`, I `:7`) per Skript gegen Roadmap `:145-153` verglichen | korrekt | — |

## Entscheidungen 39-53 eingearbeitet

Quelle: Roadmap Abschnitt 7c. Commits aus `git -C W log --oneline` (Subjects `apply decisions 39-53 to ...`). Roadmap = `1ef17dcf`, A = `22500673`, C = `84a7fe9f`, D = `1c459178`, E = `f767206a`, F = `b7d1572d`, G = `87470d25`, H = `08c9cf30`, I = `37e41bdc`; C-1086i = Commit durch den Parent (Message `.tmp/commit-d39-c1086i.txt`), SHA beim Schreiben noch nicht vorhanden.

| Entscheidung | betroffene Dateien | Aenderung in einem Satz | Commit-SHA |
|---|---|---|---|
| 39 (A-Q1, #547) | Roadmap, A | Follow-up-Issue-Entwurf mit allen fuenf Guide-Punkten statt drei. | `1ef17dcf`, `22500673` |
| 40 (C U1, #1180) | Roadmap, C | Self-contain: Kernlimits inline, keine `docs/concepts/`-Verweise, keine Docs-URL-Variable. | `1ef17dcf`, `84a7fe9f` |
| 41 (C U2, #1182) | Roadmap, C | WARN und Sektion auslassen, kein Reject-Pfad. | `1ef17dcf`, `84a7fe9f` |
| 42 (C U3, #1195) | Roadmap, C | `SYNC_BACKUP_MAX_TOTAL_PER_DIR = 30`, aelteste gitignorierte Backups loeschen. | `1ef17dcf`, `84a7fe9f` |
| 43 (C U4, #1000) | Roadmap, C | Ohne Git-Repo fail-soft; Teilfrage `progress.checkpoint-dir` bleibt offen. | `1ef17dcf`, `84a7fe9f` |
| 44 (C U5, #1142) | Roadmap, C | Stale Allowlist bei ungueltiger Config liegen lassen. | `1ef17dcf`, `84a7fe9f` |
| 45 (C U9, #1086h) | Roadmap, C | `priority` nur emittieren, kein Verhaltenswechsel. | `1ef17dcf`, `84a7fe9f` |
| 46 (C U11, #1086) | Roadmap, C, C-1086i | #1086 bleibt offen bis Punkt f entschieden/verworfen; kein Schliess-Schritt. | `1ef17dcf`, `84a7fe9f`, d8c37e61 |
| 47 (D Offen 1, #1172) | Roadmap, D | Machbarkeits-Task 2a zuerst, Permission-Regel bedingt in Task 2b, Doku-Pfad als Fallback. | `1ef17dcf`, `1c459178` |
| 48 (D Offen 5, #1141) | Roadmap, D | Unknown-Key-Warnung auch in `--audit-config`. | `1ef17dcf`, `1c459178` |
| 49 (E U10, #1187) | Roadmap, E, F | #1187 als Block 0 von E (nach User-Freigabe zum Wiederoeffnen); E = 6, gesamt 90; F-Sperre faellt nach Block 0. | `1ef17dcf`, `f767206a`, `b7d1572d` |
| 50 (E U8, #1198) | Roadmap, E | Single-Brace-Lint auch fuer `rules/`, Fixture gegen Fehlalarm. | `1ef17dcf`, `f767206a` |
| 51 (F-offen-1, #1201) | Roadmap, F | GitHub-Projektion `bug`; Referenzplan unveraendert, Task 2 gesperrt bis Freigabe (Task 0b). | `1ef17dcf`, `b7d1572d` |
| 52 (G-O2, O-H4, O-H8) | Roadmap, C, D, E, F, G, H, C-1086i | Phasen-PR nur mit ausfuehrbaren Tasks, gesperrte in einem Nachfolge-PR (max. 2 PRs je Phase). | `1ef17dcf`, `84a7fe9f`, `1c459178`, `f767206a`, `b7d1572d`, `87470d25`, `08c9cf30`, d8c37e61 |
| 53 (Phase-I-Schnitt) | Roadmap, I | Doku-PR je Issue (Concept, Spec, Gate), Umsetzung spaeter in J1, J2, ...; ersetzt 36 fuer I. | `1ef17dcf`, `37e41bdc` |

Zuordnung per Diff `c6a1e911..HEAD` (Grep nach Entscheidungsnummern) plus Lesen; reine "nicht zutreffend"-Erwaehnungen nicht gezaehlt.

Neue Zaehler: A 11, B 13, C 11, D 8, E 6, F 6, G 7, H 11, I 17 = **90**. Sweep unveraendert 57/24/7/1 = 89; #1187 wird separat gezaehlt (Entscheidung 49, nicht im Sweep).

PR-Schnitt: grundsaetzlich ein PR je Phase (Entscheidung 17). Ausnahmen: #1086i (eigener PR nach dem letzten Phase-C-PR, Entscheidung 18), #1209 (eigene Spec, eigener PR), Regel 52 (je Phase hoechstens ein Nachfolge-PR fuer gesperrte/spec-gesteuerte Tasks) und Phase I (Doku-PR je Issue, Umsetzung in J-Phasen J1, J2, ... mit eigenem Plan und PR, Entscheidung 53).

## Entscheidungen 54-57 eingearbeitet

Quelle: Roadmap Abschnitt 7d. Commits (Subjects `apply decisions 54-57 to ...`): Roadmap = `888ecfa4`, C = `d55fe907`, C-1086i = `1361f2fe`, E = `08906635`, F = `05fcf68a`, G = `12f853b3`, H = `7d3220b8`, I = `428c42e7`. A, B, D ohne Aenderung.

| Entscheidung | Dateien | Aenderung in einem Satz | Commit-SHA |
|---|---|---|---|
| 54 (O-H5, #1167; #339) | Roadmap, H, I | REQ-Format strikt ein Bereich `REQ-<BEREICH>-<NN>`; Fixture `REQ-L2-AT-018` wird abgelehnt, #339 passt sich bei Neufreigabe an. | `888ecfa4`, `7d3220b8`, `428c42e7` |
| 55 (#1000 Teilfrage) | Roadmap, C | agent-meta behaelt `.meta-viz/`; Warnung `progress.checkpoint-dir-ignored` dokumentiert hingenommen, da kein Unterdrueckungs-Key existiert (C Task 0b `:190`, Task 13 Step 4 `:373`, Beleg `scripts/lib/progress_paths.py:41-43`). | `888ecfa4`, `d55fe907` |
| 56 (Defaults) | Roadmap, C, C-1086i, E, F, G, H, I | O-H6/O-H7, E U1-U4/U7, #1195 >30 Quellen (neuestes Backup je Quelle bleibt), #1086i als Nachfolge-PR nach dem letzten C-PR, F nicht vor E-Kern, gemeinsame Phase-I-Concepts im Doku-PR des frueheren Issues. | `888ecfa4`, `d55fe907`, `1361f2fe`, `08906635`, `05fcf68a`, `12f853b3`, `7d3220b8`, `428c42e7` |
| 57 (#1201 GitLab) | Roadmap, F | GitLab-Projektion `type::bug` mit Trenner aus Host-Config-Key; Task 2 bleibt bis Task 0b (beide Werte) gesperrt. | `888ecfa4`, `05fcf68a` |

Zuordnung per Diff-Grep nach Entscheidungsnummern je Commit; C-1086i nennt 54/55/57 nur als "nicht zutreffend" (nicht gezaehlt). Zaehler unveraendert 90.

## Gesamtliste / Zaehler / offene Entscheidungen / Nicht verifiziert

### (i) Zaehler je Plan

Befundzaehler aus den Plan-Abschnitten oben; Commit = Review-Fix-Commit (`git -C W log --oneline`); Checker = ERROR-Anzahl vorher / nach Review / Endlauf (`.tmp/final-check/<plan>.txt`, `--ref origin/main --no-issues`).

| Plan | korrekt | falsch | ungeprueft (-> belegt / offen) | Fixes | Commit | ERROR vorher / Review / final |
|---|---|---|---|---|---|---|
| A | 19 | 12 (+1 unpraezise, 1 advisory) | 4 / 0 | 44 Edits + 1 `sed` | `d3c419e6` | 1 / 1 / 1 |
| B | 15 | 22 | 3 / 1 | 25 (+ Q1) | `b8802f04` | 6 / 7 / 7 |
| C | 17 | 19 | 13 / 0 | 32 | `25ec53e2` | 11 / 11 / 11 |
| C-1086i | 7 | 24 | 5 / 0 | siehe Abschnitt (+ Q3) | `707bb7fd` | 1 / 0 / 0 |
| D | 16 | 20 | 3 / 0 | 28 (+ Q2) | `48864a54` | 5 / 5 / 6 |
| E | 20 | 16 | 5 / 2 | ca. 25 | `5673864e` | 0 / 0 / 0 |
| F | 13 | 14 (+1 Luecke) | 3 / 0 | 15 (+ Q5) | `856ca060` | 3 / 3 / 3 |
| G | 24 | 15 | 2 / 0 | 15 | `d7614236` | 5 / 5 / 5 |
| H | 15 | 33 | 3 (offen) | 33 (+ Q4) | `e8b6987e` | 3 / 2 / 2 |
| I | 19 | 15 | 0 / 5 | 15 | `975311fd` | 9 / 10 / 10 |
| Roadmap | — | 6 (Q6-Q11) + 3 Wellen-Luecken (Q12-Q14) | — | Q6-Q16 | (dieser Lauf) | — / — / 0 |

Verbleibende ERROR (final 45): alle (a) neu geplante Dateien/Symbole oder (c) Geschwisterplaene, die nur im Branch `docs/phase-plans` liegen. A: 1 Testdatei; B: 7 neue Symbole (`_STATIC_KEYS`, `_SCHEMA_PATH`, `_load_schema_keys`, `_SPEC_RE`, `_TASK_LIKE_HEADER_RE`, `_check_task_detection`, `checkboxGroupField`; B `:568`, `:701-702`); C: 11 neue Test-/Spec-Dateien; D: 5 neue Spec-/Analyse-Dateien plus `tests/test_admin_whitelist_drift.py` (neu durch E-T4, Verweis aus Q2); F: 3 vom Kern gelieferte Dateien/Spec; G: 5 neue Runbooks/Specs/Guide; H: 2 Geschwisterplaene; I: 10 Geschwisterplaene (inkl. Selbstverweis).

### (ii) Verbleibende echte User-Entscheidungen

Stand nach Entscheidungen 54-57. Nur noch offene Fragen; jede per Grep in der genannten Plan-Stelle nachgelesen (kein Plan beantwortet sie). "Aufgaben" (kein User-Entscheid) stehen getrennt darunter.

| Plan | ID | Frage | Beleg |
|---|---|---|---|
| G | G-O1 | Probe-Art und Evidenzpfad, mit denen G-N1 final wird | G `:110` |
| G | G-O3 | Kostenfreigabe fuer Task 5/6 (echte Provider-Laeufe): Kostenschaetzung + ausdrueckliches User-Ja | G `:112` |
| H | O-H2 | REQ-Regex `\d{2}` oder `\d{2,3}`? Erst nach Task-19-Messung | H `:146` |
| C-1086i | C1086i-U1 (bedingt) | `managed_block.py` > 600 Zeilen: Budget-Ausnahme oder Teilung? Nur falls Messung ausloest | C-1086i `:398` |
| E | U5/U6 | #1209-Spec: Umfang der Templates mit Gates (U5); Inhalt der Vertragsaenderung AC-05 (U6) | E `:339-340` |
| E | Szenarien 95-98 | Zuordnung je Modus ist Vorschlag des Wrapper-Plans, nicht aus 49 | E `:170`, E-B0-T2 |
| H | H-Gate | Was gilt, wenn eine Gate-Task auch beim H2-Schnitt (Nachfolge-PR) nicht APPROVED ist? | H `:81` |
| F | Task 0b | User-Freigabe der Referenzplan-Aenderung K-7/F-1, beide Werte (`bug`, `type::bug`) | F `:118-123` |
| E | #1187 reopen | User muss #1187 wieder oeffnen (User-Aktion) | E `:25` |
| I | #339-OQ12/R2 | `sub_components`-Schematiefe; Wrapper-Agent R2 oder `--validate-se` in CI? | I `:107` |
| I | #329/#330 | Baseline-Freeze in `project.yaml`; Rolle der Metrik | I `:116` |
| I | #1004 | Quelle `max_concurrent_agents`; Graph-Format Mermaid/ASCII | I `:208` |
| I | #957 | MVP-Set-Feinschnitt | I `:199` |
| Roadmap | Konflikt 6 | Zuschnitt der uebrigen D-Streams | Roadmap 7d "Weiterhin offen", 8 |

Summe: 14 offene Zeilen (davon 1 bedingt: C1086i-U1). Roadmap 7d listet zusaetzlich "C Task 6 Details ueber 56 hinaus"; C `:399` setzt 56 um, keine Restfrage im Plan, daher nicht gezaehlt.

Aufgabe, keine Frage: D Task 2a (#1172 Machbarkeit Provider-Permission) - Ergebnis ausstehend, entscheidet ueber Task 2b.

Beantwortet (Entscheidung 39-57):

| Frage | Entscheidung |
|---|---|
| A-Q1 | 39 |
| C U1 | 40 |
| C U2 | 41 |
| C U3 | 42 |
| C U4 | 43 (Teilfrage `progress.checkpoint-dir` -> 55) |
| C U5 | 44 |
| C U9 | 45 |
| C U11 | 46 |
| D Offen 1 | 47 |
| D Offen 5 | 48 |
| E U10 (= Konflikt 8) | 49 |
| E U8 | 50 |
| F-offen-1 | 51 |
| G-O2, O-H4, O-H8 | 52 |
| I-UMS (Phase-I-Schnitt) | 53 |
| O-H5 (#339 strikt `REQ-<BEREICH>-<NN>`) | 54 |
| #1000-Teilfrage checkpoint-dir | 55 (agent-meta behaelt `.meta-viz/`; Warnung dokumentiert hingenommen, da kein Unterdrueckungs-Key im Code; C Task 0b `:190` / Task 13 `:373` zitieren `scripts/lib/progress_paths.py:41-43`) |
| O-H6, O-H7, E U1-U4/U7, #1195 >30 Quellen, #1086i (18 vs. 52: Nachfolge-PR nach dem letzten C-PR), F nicht vor E-Kern, Phase-I gemeinsame Concepts | 56 |
| F-offen-2 (#1201 GitLab `type::bug`) | 57 |

### (iii) Nicht verifiziert (konsolidiert)

- Keine Tests, kein `sync.py --validate`, kein Render, kein Benchmark ausgefuehrt (alle Plaene); alle rot/gruen-Erwartungen sind Planwerte.
- Externe Fakten: Claude-Code-Hook-API (`ask`, Rollenfeld; D), Opencode-Quelle und Capture-Weg, `agy`/`gemini`-CLI, `pclmul` des Hosts, Hermes-Fakten (#800), `cwd`-Support der Zielformate (G), Herkunft der F-OC2-Liste (H), Live-Payload models.dev (B P-12, am Ausfuehrungstag wiederholen), Live-Labels (`gh label list`, F).
- Laufzeitverhalten: Marker-Wirkung in CI/Dependabot (A), F4/F7 #1155, `SyncLog.write` vor Exit, #1208-Ursache (C), Browser-/Playwright-Laeufe (B Tasks 10-13), Continue-/Prompt-Pfade in ac01 (C-1086i), Golden-Fixture-Vergleicher fuer `slimming-golden/git.md` (F).
- Code-Stellen nicht gelesen: `--audit-config` -> `_validate_config` (D), #1189-Plananker, `orchestrator.mode`-Default, `role-defaults.yaml`-Schema (C), Routing-/Review-Rule-Dateien, D-Spec #1169 (H); Kern-Signaturen E-T6/E-T8 und `render_priority_table` existieren noch nicht.
- Status #1189 und CI nicht abgerufen (E); Branch-/Stash-Werte gelten fuer `FETCH_HEAD` 2026-11-11 (A).
- Spec-Plan-Vollscan bricht an Prosa-`**Spec:**` ab (B Befund 16, D); ob `check_spec_plan_workflow` Plan I als Plan klassifiziert (I); I-Befunde 35-39.
- Durch diesen Lauf erledigt: A "Zuordnung `context.py:204` (#1161) unklar" -> Pkt 4, `_backup_context_file` (H-Plan `:70`).
- Roadmap-Sweep-Zeilen ausser Q6-Q10 bleiben "Subagent, ungeprueft".
- Neu (Entscheidungen 39-53): Szenario-Zuordnung 95-98 ist Vorschlag des E-Wrapper-Plans, nicht aus 49 (E `:500`).
- Neu: D Task 2a - Machbarkeit einer Repo-konfigurierbaren Provider-Permission und Verhalten des externen Auto-Mode-Classifiers unbelegt (D `:175`, `:185`).
- Neu: Anker des #1187-Plans (Basis `aaed14c2`) nicht gegen `9aa0e0c0` nachgemessen (E `:500`, E-B0-T1 Step 2).
- Neu: Dateireihenfolge H/G (O-H7) nur aus dem Wellenplan abgeleitet, Ueberlappung nicht neu gemessen.
- Neu: Zuordnung "Entscheidung -> Datei" in der Tabelle oben per Diff-Grep, keine Volllesung jedes Plans; C-1086i-Commit-SHA beim Schreiben noch nicht vorhanden.
- Neu (Entscheidungen 54-57): Unterdrueckungsweg zu 55 - kein Config-Key existiert (`scripts/lib/progress_paths.py:41-43`), die Warnung wird hingenommen; Ausgabeflaeche der Warnung legt erst die #1000-Spec fest.
- Neu: GitLab-Trenner-Key (57) ist durch den Referenzplan plan-eingefuehrt (`config/issue-conventions-presets.yaml`, `config/issue-adapters.yaml`), auf origin/main nicht vorhanden (F `:183`).
- Neu: Ziffernzahl N im REQ-Regex offen (O-H2), Task-19-Messung steht aus.
- Neu: `_MODE_FILES`/`_MODE_INLINE` sind plan-eingefuehrte Namen (0 Treffer in `scripts/`, E `:334`).

### (iv) Phasen-Zaehler

Geaendert durch Entscheidung 49: A 11, B 13, C 11, D 8, **E 6**, F 6, G 7, H 11, I 17 = **90**. Sweep unveraendert: ECHT_OFFEN 57, TEILWEISE 24, SCHON_GEBAUT 7, DOPPELT 1 = 89 (Roadmap `:29-33`); #1187 zaehlt separat (nicht im Sweep). Phase I: Zaehler 17 bleibt, Schnitt nach 53 (Doku-PR je Issue, J-Phasen). Entscheidungen 54-57 aendern keinen Zaehler: A11 B13 C11 D8 E6 F6 G7 H11 I17 = 90.
