# Opencode v2-Support — Ausführungsstatus (Plan B / Issue #1007)

**Zweck:** Ausführungs-Ledger zum Plan `docs/plans/2026-10-22-opencode-v2-support-plan.md` (Phasen C0, B, C1/C2, C3, D) und damit zum Tracking-Issue #1007. Das Dokument hält je Phase und je Task den erreichten Stand, die Beleg-Commits, die Testlage und die substanziellen Befunde fest; es ersetzt weder Plan noch Spec.

**Geltungsbereich:** Branch `feat/1007-b-keys` (Basis `main` = `526a5dab`; Phase C0 über PR #1011 gemergt, C0-Ledger-Commit `52a72a0f`, Evidenz-Nachbesserung `2978753c`). Phase-B-Arbeit von `bd49dc5b` bis `d5853d1e`. Phase C1/C2 auf Branch `feat/1007-c1-c2-gate` (Basis `d0b81f91`), Commits `f07ab459` bis `ad4380e1`. Phase C3 auf Branch `feat/1007-c3-plugin` (Basis `9f274040`), Commits `c8270845` und `c673991f`. Phase D auf Branch `feat/1007-d-surface` (Basis `dfb77de4`), Commits `fa42ec7b` bis `04d41eb8` (13 Commits, inklusive Folgelauf zu Task 23). Stand: 2026-10-24.

**Datenquelle:** Commits dieses Branches, die im Plan gesetzten Checkboxen (C0: Tasks 1, 2, 3, 3a, 24; B: Tasks 4–12; C1/C2: Tasks 13, 13a, 14–17; C3: Tasks 18, 19; D: Tasks 20–23 inklusive Folgelauf, 25–32; Task 33 bewusst offen) sowie die dort protokollierten Testläufe und die Phasen-Exit-Kriterien.

**Legende der Spaltenwerte**

| Spalte | Werte |
|---|---|
| `Status` (Task) | `done` = alle Steps erledigt und committet · `done (Review/PR offen)` = Arbeit abgeschlossen, Review bzw. PR steht aus · `offen` = nicht begonnen |
| `Status` (Phase) | wie oben, auf Phasenebene aggregiert |
| `Tests` | letzter belegter Testlauf; `N failed` = erwarteter Rot-Lauf (red-before-green) · `—` = im Ledger kein Testlauf überliefert |
| `Abweichungen/Befunde` | substanzielle Ergebnisse, die über den Planwortlaut hinausgehen oder ihn präzisieren |

## Phasenübersicht

| Phase | Tasks | Status |
|---|---|---|
| C0 | 1, 2, 3, 3a, 24 | `done (gemergt, PR #1011)` |
| B | 4–12 | `done (Review/PR offen)` |
| C1/C2 | 13, 13a, 14–17 | `done (Review/PR offen)` |
| C3 | 18–19 | `done (Review/PR offen)` |
| D | 20–33 (ohne 24) | `done (Review/PR offen; Task 33 offen)` |

**Entry-Kriterien:** E1 done · E2 done · E3 done · E4 done.

## C0

| Task | Agent | Commit | Tests | Status | Abweichungen/Befunde |
|---|---|---|---|---|---|
| 1 | `tester` | `1c1cc31` | `7 failed` (erwarteter Rot-Lauf) | `done` | Struktur-Test für das Spike-Ergebnisdokument angelegt; bleibt rot bis Task 2. |
| 2 | `provider-expert` | `5eadea26` | — | `done` | `VERDICT-C3: GO` (reale Runtime-Proben auf v2.1.3). `VERDICT-FIELDS: AMEND`, weil `agents.title.model` UNVERIFIED ist. Review-Nachlauf QA-C0-04/RVW-C0-04: `Proben`-Zählweise im Spike präzisiert (je Frage höchstens eine Probe pro Inspektionskommando); die Zahlen bleiben unverändert (Q1 2, Q2 3, Q3 2, Q4 0, Q5 2, Q6 2). |
| 3 | `concept-specifier` | `80302a7` | `7 passed` | `done` | Amendment B1 in die Spec (Rev. 1.5) eingearbeitet: `agents.title.model`/AC-B9 entfällt; `providers`-Innenform korrigiert auf `settings.baseURL` + `env`; in `cli.json` nur `plugins` dokumentiert; verwaltete Deny-Tripel werden jetzt am **Ende** von `permissions[]` angehängt (last-match-wins); `plugins` im Plural; `timeout.startup` ergänzt. C0-Review-Nachlauf: OAuth-Bewusste-Einschränkung, AC-C2-Staging und die Ableitung der Agent-internen Reihenfolge präzisiert. |
| 3a | `tester` | `e340f0f` | `8 passed` | `done` | Der GO-Zweig prüft nur die Implikation „Keys vorhanden ⇒ GO“ (Äquivalenz folgt in Task 19). **Negativprobe reproduzierbar (Review QA-C0-11/RVW-C0-03/QA-C0-10):** in einer Wegwerf-Kopie des Repos (nicht committet) (1) im Spike-Dokument `VERDICT-C3: GO` durch `VERDICT-C3: NO-GO` ersetzen und (2) im Opencode-Eintrag von `config/ai-providers.yaml` `surface-plugin-protocols` **und** `surface-has-plugins` injizieren → `python3 -m pytest tests/test_opencode_v2_spike.py -q -k ac_c2` ergibt `1 failed` (Assertion „NO-GO verdict but the registry declares C3 keys“). Kontrolllauf: dieselbe Kopie ohne injizierte C3-Schlüssel, aber mit dem im Spike-Dokument ergänzten Satz „Fallback = Permissions-Tier“ → `1 passed`. |
| 24 | `provider-expert` | `31001cc1`, `2978753c` | `1 passed` (`-k ac_d8_evidence`), `16 passed` (Datei) | `done` | Evidenz trägt `ERGEBNIS: JSONC-TRAEGT-NICHTS-BEI`. Nachbesserung `2978753c` (`docs: verify opencode v2 jsonc loading behaviour`): v2.1.3 wurde nachträglich geprobt; das `ERGEBNIS` bleibt unverändert (`JSONC-TRAEGT-NICHTS-BEI`). Für den ursprünglichen Lauf wurde nur `opencode 1.19.3` verwendet. |

## B

| Task | Agent | Commit | Tests | Status | Abweichungen/Befunde |
|---|---|---|---|---|---|
| 4 | `developer` | `bd49dc5b` | rot `1 failed, 4 passed` → `5 passed` | `done` | 5 Tests (Amendment B1: kein `small-model`); `python3 scripts/sync.py --validate` rc 0. |
| 5 | `developer` | `06d2094d` | rot `1 failed, 2 passed` → `33 passed` | `done` | Neue Konstanten `_STATE_V2_{KEYS,PERMISSIONS,CLI,MCP}` + `_STATE_DICT_KEYS` als einzige Quelle; Spec-A-Namespaces unverändert. |
| 6 | `developer` | `d7633d67` | rot `3 failed, 4 passed` → `105 passed` | `done` | Der Rot-Lauf zeigte drei Symptome einer einzigen fehlenden Auflösung, nicht eines wie im Plan angenommen. Registry erhält `cli-files.v2`, `surface-model-patterns.v2`, `surface-v2-fields`; noch keine C3-Schlüssel. |
| 7 | `senior-developer` | `cd963c51` | rot `ModuleNotFoundError` → `10 passed` | `done` | Reine Entscheidungs-Engine, kein I/O; Rand-Semantik der Zeilen 3b/4a dokumentiert. Vorwärtsrisiko: `isolation` darf `opencode_v2_config` nur funktionslokal importieren (der Azyklizitätstest folgt nur Top-Level-Imports). |
| 8 | `senior-developer` | `13ccf688` | rot `ImportError` → `22 passed` | `done` | `owns_opencode_surface` ist False für Claude-artige und Mammouth-artige Einträge; kein `agents.title.model`, kein `$schema`. |
| 9 | `senior-developer` | `7b9ccecb` | rot `13 failed` → `84 passed` | `done` | Der Writer schreibt nur neu, wenn eine Entscheidung das Dokument verändert hat (JSONC-Kommentare überleben); Nicht-Objekt-JSON gilt als Parse-Fehler. |
| 10 | `senior-developer` | `ccbfe520` | rot `6 failed, 1 passed` → `47 passed` | `done` | Rot umfasste die 5 Plan-Tests plus 1 zusätzlichen Ownership-Konflikt-Guard. Laufbezogener Parameter `claimed_files` ergänzt; `warn_ignored_v2_options` wird aus dem Writer heraus aufgerufen; die Aufrufbedingung `== "permission"` ist nachweislich unverändert (reine Einfügungen). |
| 11 | `senior-developer` | `db35f684` | rot `5 failed` (`KeyError: 'experimental'`) → `73 passed` | `done` | Szenario 69 PASS. Das Assert liegt in `69-opencode-v2-surface.sh:203` (nicht `:173` wie im Plan; Review RVW-B-04). Spec-Prosa-Drift: AC-B1 nannte Tiefe 3, die Repo-Capability `required_depth` ist 2 — **erledigt**: die Klammer in AC-B1 wurde in der Phase-B-Review-Runde auf „aktuell 2" korrigiert (`511d6111`); der normative Gehalt des AC (Wert = `required_depth` der Capability) blieb unverändert. |
| 12 | `developer` | `d5853d1e` | rot `3 failed` → `92 passed` | `done` | `consistency-check.py` PASS. Das Task-6-Muster akzeptiert `a/b/c` im Modellsegment; eine ungültige Regex in `model-pattern` schlägt bewusst offen fehl (keine Prüfung). |

## Phase-B-Review-Fixrunde (2026-10-23)

**Quelle:** Review zu `feat/1007-b-keys` (Verdict `CHANGES_REQUESTED`). Commits dieser Runde: `1b7e5959`, `511d6111`, `bdff8459` — Status `done`.

| Finding | Schwere | Änderung | Beleg |
|---|---|---|---|
| QA-B-01 | BLOCKER | Einzeleigentum `experimental.subagent_depth`: `context.apply_settings_surface_shape` entfernt nur noch den Top-Level-Key und schreibt die Tiefe nicht mehr; `build_managed_keys` ist der einzige Writer. End-to-End-Test (Init-Shape + Writer, Option 3) plus v2→v1-Rollback; AC-B1-Dokumentassertion aus den Settings-Shape-Unittests dorthin verschoben. | `scripts/lib/context.py`, `tests/test_opencode_v2_surface.py::test_ac_b1_end_to_end_*`, Spec Amendment B2 (Rev. 1.6) |
| QA-B-02 | MAJOR | Claim (`claimed_files.add`) hinter die „nichts zu tun"-Prüfung und vor den Datei-Read; `warn_ignored_v2_options` nach dem Claim. Der AC-B13-Warnpfad im No-op-Zweig bleibt erhalten (Warnung ist keine Dateiarbeit). Zwei-Owner-Test mit „erster Owner hat keine Arbeit". | `scripts/lib/opencode_v2_config.py`, `::test_ac_b20_owner_conflict_first_owner_without_work_does_not_block` |
| QA-B-03 | MAJOR | `_set_path` ersetzt keinen Nicht-dict-Vorfahren mehr: `False` + Warnung, kein Schreiben, kein State. Regressionstest `{"experimental": "legacy-user-value"}`. | `scripts/lib/opencode_v2_config.py`, `::test_ac_b5_non_dict_ancestor_is_kept_with_warning` |
| QA-B-04 | MAJOR | `claimed_files` ist jetzt Pflicht-Keyword (`*`); beide Produktionsaufrufe unverändert als Keyword, Testhelfer `_run` angepasst. | `scripts/lib/opencode_v2_config.py`, `tests/test_opencode_v2_surface.py::_run` |
| QA-B-05 | MINOR | Abgeleiteter State-Pfad läuft durch `isolation.safe_path` wie der Managed-File-Pfad. | `scripts/lib/opencode_v2_config.py` |
| QA-B-06 | MINOR | Secret-Kontext wird auf Kinder eines secret-benannten Keys vererbt (`{"token": {"value": "PLAINTEXT"}}` ist ein Finding). | `scripts/lib/opencode_v2_config.py`, `::test_ac_b10_secret_object_value_under_secret_name_is_finding` |
| QA-B-07 | MINOR | AC-B19-Test prüft zusätzlich Byte-Gleichheit des Dokuments. | `tests/test_opencode_v2_surface.py::test_ac_b19_user_deleted_key_not_rewritten` |
| QA-B-10 | MINOR | Kommentar in `model_contracts._catalog_id`: `#variant`-Stripping ist eine universelle Modell-ID-Regel, keine v2-Sonderregel (kein Verhaltenswechsel). | `scripts/lib/consistency/model_contracts.py` |
| QA-B-11 | MINOR | `providers.<id>: null` wird in `build_managed_keys` nicht geschrieben und gewarnt; für einen Pfad im State endet die Verwaltung (Zeile 4: entfernen bzw. Prior wiederherstellen), für einen frischen wird nichts geschrieben. | `scripts/lib/opencode_v2_config.py`, `::test_ac_b11_providers_null_entry_not_written_ends_management` |
| QA-B-12 | MINOR | End-to-End Adopt (3a) → Optionsänderung (2) → Rollback stellt den ursprünglichen Prior wieder her. | `::test_ac_b1_review_single_ownership_e2e_adopt_change_rollback` |
| QA-B-13 | MINOR | Identitäts- durch Gleichheitsassertion für `kwargs["config"]` ersetzt. | `tests/test_opencode_v2_surface.py` |
| RVW-B-01 | MINOR | AC-IDs in Testnamen ergänzt: `test_ac_b11_build_managed_keys_v2_full`, `test_ac_b3_build_managed_keys_without_todo_omits_key`, `test_ac_b10_secret_*`. | `tests/test_opencode_v2_config.py` |
| RVW-B-02 | MINOR | Test: vorhandenes `$schema` überlebt einen v2-Merge byte-exakt. | `::test_ac_b11_schema_preserved_through_v2_merge` |
| RVW-B-04 | MINOR | Ledger-Zeilenreferenz des Szenario-69-Asserts korrigiert (`:199` → `:203`). | dieses Dokument, Zeile Task 11 |

**Bewusste Abweichung:** Der frühere Test „Template-Tiefe wird ohne Capabilities nach `experimental.subagent_depth` übernommen" entfällt als eigene Assertion, weil die bindende Entscheidung die Template-Tiefe als Quelle streicht (nur Projekt-Option oder Capability). Die Capability-Quelle bleibt als End-to-End-Test erhalten.

**Phase-B-Exit-Kriterien (2026-10-23):** `python3 -m pytest tests/test_opencode_v2_surface.py tests/test_opencode_v2_config.py tests/test_opencode_v2_schema.py tests/test_opencode_v2_aux_selection.py tests/test_opencode_runtime_gate.py -q` → `106 passed`; `python3 scripts/sync.py --validate` rc 0; `python3 scripts/sync.py --check` rc 0 (kein Drift, 0 Aktionen / 449 übersprungen, 35 Warnungen aus Altstand/Umgebung); `python3 scripts/consistency-check.py` → `[PASS] All checks passed.` rc 0.

## C1/C2

**Branch:** `feat/1007-c1-c2-gate` (Basis `d0b81f91`; Arbeitsstand `ad4380e1`). Alle sechs Task-Blöcke sind im Plan abgehakt.

| Task | Agent | Commit | Tests | Status | Abweichungen/Befunde |
|---|---|---|---|---|---|
| 13 | `senior-developer` | `f07ab459` | rot `7 failed, 2 passed` → `99 passed` | `done` | `permission_deny_required` als eigene Wahrheitstabelle (Tier `permission` → True; `plugin`+`observe` → True; `plugin`+`enforce` → False; `advisory` → False). Die verwalteten Tripel werden am **Ende** von `permissions[]` angehängt (Amendment B1, Spike Q3: last match wins) und der Rollback arbeitet positionsunabhängig über das exakte Tripel. v2 erhält die v1-`permission`-Map nicht mehr. **Abweichung:** Die Writer-Signatur hat kein `config`, deshalb übergibt sie `allow_secrets=False, config=None` (Spec-A-Parität); eine leere `permissions`-Liste wird bereinigt. |
| 13a | `senior-developer` | `3bdfac09` | rot `9 failed, 1 passed` → `109 passed` | `done` | Rückbau-Matrix mit allen 7 Zeilen umgesetzt. IC-4-Quelltext-Hashes im Test eingebettet (`_opencode_runtime_gate_entries` `b4a6c142…`, `opencode_runtime_gate_wanted` `294986792…`); die Bedingung `provider_runtime_gate_tier(pc, caps) == "permission"` tritt je Sync-Datei genau einmal auf. Die Verdrahtung sitzt zwischen Gate-Block und Managed-Keys-Writer. **Abweichung:** Die 7 Matrix-Zeilen laufen in einer einzigen Testfunktion (um den exakten RED-Zähler des Plans zu erhalten), nicht als `parametrize`. |
| 14 | `developer` | `a9e3353a` | rot `3 failed, 1 passed` (Plan prognostizierte einen Fehlschlag) → `9 passed` | `done` | Beide MCP-`connection`-Objekte des Schemas sind offen (kein `additionalProperties`), daher waren alle drei Ablehnungsfälle vor dem Eingriff rot; der Akzeptanztest prüft deshalb zusätzlich, dass die Schlüssel auf **beiden** Objekten deklariert sind. `timeout` erlaubt `startup`; `oauth` ist bewusst auf drei Schlüssel begrenzt (dokumentierte, aber nicht unterstützte Schlüssel schlagen sichtbar fehl). |
| 15 | `senior-developer` | `b7c6177a` | rot `4 failed, 2 passed` → `115 passed` | `done` | Der v2-Eintrag trägt kein `enabled`; `disabled`/`timeout`/`oauth` werden nur bei Gültigkeit emittiert; ein Klartext-OAuth-Secret bricht über `SyncError` ab. **Abweichung (Plandefekt):** `tests/test_mcp_config.py` musste geändert werden — `test_build_connection_entry_opencode_json_v2_matches_v1_shape` kodierte die Vorspike-Annahme „v2 == v1 inkl. `enabled: true`“, die AC-C7 widerspricht; die Assertion wurde invertiert (v1 `enabled is True`, v2 ohne `enabled`, übrige Schlüssel gleich) und der v1-Freeze verschärft. Der Plan behauptete, die Datei bleibe unverändert. |
| 16 | `senior-developer` | `ba8282d5` | rot `7 failed` → `155 passed` | `done` | `mcp.servers.<name>` je Pfad, Namespace `opencode-v2-mcp`; der Rückbau greift auch auf den frühen Return-Pfaden und ist unabhängig von der Zahl aktiver Server. **Bekannte Grenzen:** Der MCP-Writer nimmt nicht am laufbezogenen `claimed_files`-Set teil (im Modul-Docstring dokumentiert; die aktuelle Registry hat genau einen v2-Eigentümer); Schreibvorgänge auf dieselbe Datei überspringen den committeten Managed-Write. |
| 17 | `developer` | `ad4380e1` | rot `6 failed, 1 passed` → `115 passed` | `done` | `_validate_opencode_v2`-Findings plus neues `check_mcp_connection_keys` auf dem zusammengeführten Katalog (`Severity.ERROR`, `mcp-connection-key: <server>.<key> invalid`); ein Projekt-Override heilt eine Framework-Verletzung (nachgewiesen). **Abweichungen:** Zweite Fixture-Korrektur in `tests/test_mcp_config.py` (ein synthetisches v2-Dokument trug `enabled: true` — ungültig nach AC-C10; der Schlüssel wurde entfernt, die Assertions blieben unverändert); `timeout` wird je vorhandenem Schlüssel geprüft (kein Pflicht-Paar Katalog+Execution); `disabled` wird zusätzlich auf Dokumentebene typgeprüft. |

**C1/C2-Exit-Kriterien (2026-10-23, Arbeitsstand `ad4380e1`):**

```
python3 -m pytest tests/test_opencode_v2_surface.py tests/test_opencode_runtime_gate.py tests/test_runtime_gate_wiring.py tests/test_artifact_contracts.py tests/test_mcp_config.py tests/test_opencode_v2_schema.py -q
python3 scripts/sync.py --validate
python3 scripts/sync.py --check
python3 scripts/consistency-check.py
python3 -m pytest tests/test_provider_agnostic_dispatch.py tests/test_import_acyclicity.py tests/test_python_compat_consistency.py -q
```

**Ergebnisse:** (1) `214 passed, 15 warnings` rc 0; (2) rc 0, `[PASS] All checks passed.`; (3) rc 0, `0 action(s) | 449 skipped | 35 warning(s)`, Provider-Kontextdateien aktuell; (4) rc 0, `[PASS] All checks passed.`; (5) `84 passed` rc 0.

**Verdikt zum Kriterium „`tests/test_mcp_config.py` unverändert grün“: NICHT erfüllt — bewusst abgewichen.** Die Datei wurde in Task 15 und Task 17 zweimal gezielt korrigiert, weil sie Vorspike-Annahmen festschrieb, die AC-C7 bzw. AC-C10 widersprechen. Der v1-Byte-Freeze selbst wird weiterhin geprüft: `test_ac_c11_v1_entry_byte_identical_to_reference` und die verschärfte Assertion in `test_build_connection_entry_opencode_json_v2_matches_v1_shape` (`v1["enabled"] is True` plus Gleichheit aller übrigen Schlüssel) sind grün. Das Kriterium gilt damit als abgewichen, nicht als verfehlt im Sinne einer Regression.

## C1/C2-Review-Fixrunde (2026-10-23)

**Quelle:** Review zu `feat/1007-c1-c2-gate` (Verdict `CHANGES_REQUESTED`). Branch-Arbeitsstand `9b4d28d6`.

| Finding | Schwere | Änderung | Beleg |
|---|---|---|---|
| QA-C-01 | BLOCKER | `active_set` ist jetzt Pflicht-Keyword von `reconcile_opencode_surface_gate` **und** `_opencode_v2_gate_permissions` und wird von beiden Produktionsaufrufern (`sync_pipeline._sync_stage_per_provider`, `cli_commands`-Test-Repo-Pfad) sowie in der Zeile-6-Warnung mit demselben Wert wie Spec A benutzt. Kein Fail-open-`None` mehr. | `scripts/lib/isolation.py`, `scripts/lib/sync_pipeline.py`, `scripts/lib/cli_commands.py`, `::test_ac_c15_non_generated_primary_role_gets_no_triples_on_*`, Spec Amendment B3 (Rev. 1.7) |
| QA-C-02 | MAJOR (Vertrag) | Agent-Ebene (`deny_edit`, Task 22) MUSS `permission_deny_required` verwenden (auch `plugin`+`observe`), nicht `opencode_runtime_gate_wanted`; AC-C14 gilt auch für die Agent-Ebene. Nur Vertrag/Plan, Implementierung bleibt Task 22. | Spec Amendment B3, AC-C14, Plan Task 22 („Amendment-B3-Folge") |
| QA-C-04 | MINOR | `_drop_flat_mcp_keys` loggt eine Warnung je verworfenem flachen v1-Key (`opencode-v2 mcp: dropped flat v1 key 'mcp.<name>'`); der Managed-Container `servers` wird nie gemeldet. | `scripts/lib/opencode_v2_config.py`, `::test_qa_c04_flat_v1_keys_dropped_with_one_warning_per_key` |
| RVW-C-01 | MINOR | Freeze-Test prüft die Aufrufbedingung **in place** (Bedingung + direkt eingerückter `_sync_opencode_runtime_gate(`-Aufruf) und dass beide Aufrufer `active_set=active_set` übergeben. | `::test_ic4_functions_and_call_condition_unchanged` |
| RVW-C-02 | MINOR | Matrix-Zeile „1b-v1-to-v2-advisory": v1-Map wird entfernt, `runtime-gate-deny` geleert, keine Tripel/kein State. | `::test_reconcile_matrix_seven_rows` / `_matrix_v1_to_v2_advisory` |
| RVW-C-03 | MINOR | End-to-End `disabled: true` durch `generate_provider_configs`: `mcp.servers.<name>.disabled is True`, kein `enabled`. | `::test_ac_c7_disabled_true_reaches_document_end_to_end` |
| RVW-C-04 | MINOR | AC-C10 klargestellt: ein Timeout-Teil-Subset ist gültig, Finding nur bei nicht-ganzzahligen Werten. | Spec AC-C10 |
| RVW-C-05 | MINOR | §3.4 dokumentiert den neuen `active_set`-Parameter und warum Fail-open an der Einstiegspunkt-Prüfung unzulässig ist. | Spec §3.4 |
| RVW-C-06 | MINOR | AC-C16(a)-Rollback-Hälfte: Verschwindet `primary-role`, wird `default_agent` entfernt und der `default-agent`-State geleert. | `::test_ac_c16a_default_agent_removed_when_primary_role_disappears` |
| RVW-C-07 | MINOR | Plan-Task-15-Step-3 verweist für „`tests/test_mcp_config.py` unverändert" auf die bewusste Ledger-Abweichung. | Plan Task 15 |

## C3

**Branch:** `feat/1007-c3-plugin` (Basis `9f274040`; Arbeitsstand `c673991f`). Beide Task-Blöcke sind im Plan abgehakt; `VERDICT-C3: GO` lag bereits vor (Spike 2026-10-23).

| Task | Agent | Commit | Tests | Status | Abweichungen/Befunde |
|---|---|---|---|---|---|
| 18 | `senior-developer` | `c8270845` | rot `2 failed, 1 passed` → `177 passed`; Aux/Surface `30 passed`; `python3 scripts/sync.py --validate` rc 0, `--check` rc 0; `node --check` rc 0 | `done` | Neues Template `templates/plugins/runtime-gate.opencode-v2-plugin.js.tmpl` ist ein ESM-Default-Export als **Objekt** mit `id` und `setup(ctx)` und registriert `ctx.tool.hook("execute.before")` — reiner Observe-Pfad, **kein** Permission-Deny-Hook. Die Registry erhält `surface-plugin-protocols: {v2: opencode-plugin-v2-js}` und `surface-has-plugins: {v2: true}`; das statische `has_plugins: false` bleibt unverändert. Aufgelöst ergibt v2 Tier `plugin` plus Plugin-Datei, v1 Tier `permission` ohne Datei. **Befund:** Der Plan-Step für `test_ac_c13` erwartete einen Test; ein zusätzlicher Positiv-Kontrollzweig hält die Negativ-Assertion nicht vakuös. |
| 19 | `tester` | `c673991f` | erster Lauf grün (`165 passed`, Task-19-Step-2-Kommando) | `done` | Reine Absicherungstests, kein Produktivcode. Zwei Negativproben feuern wie erwartet und wurden danach zurückgenommen: (1) `permission_deny_required` ohne den `plugin`+`observe`-Zweig → `test_ac_c14_real_v2_registry_plugin_observe_keeps_deny_triples` `1 failed`; (2) Entfernen der beiden C3-Registry-Schlüssel → `test_ac_c2_gate_fallback_invariants` `1 failed`. Der GO-Zweig des Spike-Tests prüft jetzt die **Äquivalenz** „C3-Schlüssel vorhanden ⇔ GO“: ein Teil-Schlüsselsatz schlägt unter beiden Verdikten fehl. |

**C3-Exit-Kriterien (2026-10-24, Arbeitsstand `c673991f`):**

```
python3 -m pytest tests/test_opencode_v2_surface.py tests/test_opencode_v2_spike.py tests/test_runtime_gate_plugins.py tests/test_runtime_gate_rendering.py tests/test_provider_agnostic_dispatch.py -q
python3 scripts/sync.py --validate
python3 scripts/sync.py --check
python3 scripts/consistency-check.py
bash tests/scenarios/run.sh 69-opencode-v2-surface
```

**Ergebnisse:**

1. `188 passed in 14.81s` → rc 0.
2. rc 0, `0 action(s)  |  382 skipped  |  2 warning(s)` (die zwei Warnungen stammen aus der Umgebung: gedroppte `se`-Gruppe und ein fehlgeschlagener Checkout in `agent-meta-test/external/awesome-claude-code`).
3. rc 0, `0 action(s)  |  449 skipped  |  35 warning(s)`, `Provider context files are up to date.`
4. rc 0, `[PASS]  All checks passed.`
5. `PASS  69-opencode-v2-surface` → `Scenarios: 1  Passed: 1  Failed: 0`, rc 0.

## C3-Review-Fixrunde (2026-10-24)

**Quelle:** Zwei Reviews zu `feat/1007-c3-plugin` (Verdict `CHANGES_REQUESTED`), Arbeitsstand `523bf1f9`. Alle vier Findings sind geschlossen; QA-D-02 ist eine **Vertragspräzisierung** (Spec Amendment B4), keine Verhaltensänderung.

| Finding | Schwere | Änderung | Beleg |
|---|---|---|---|
| QA-D-01 | MINOR (Abdeckung) | Der Stage-Helper `_run_stage` spioniert neben `_sync_opencode_runtime_gate` jetzt auch `sync_pipeline.sync_runtime_gate_plugins` (`plugin_calls`-Out-Parameter). Zwei neue Tests fahren den echten Dispatch `if pc.get("has_plugins")` mit der **ausgelieferten** Registry: v2 ⇒ Writer genau einmal (mit aufgelöstem Provider-Registry-Dict), v1 ⇒ nie. Szenario 69 prüft zusätzlich, dass der v2-Lauf `.opencode/plugins/agent-meta-runtime-gate.js` erzeugt, die Datei `export default {` und `MODE = "observe"` trägt und der v1-Baseline-Lauf **kein** Plugin-Artefakt erhält. | `tests/test_opencode_v2_surface.py::test_qa_d01_stage_dispatches_plugin_writer_for_real_v2_registry`, `::test_qa_d01_stage_does_not_dispatch_plugin_writer_for_v1`, `tests/scenarios/asserts/69-opencode-v2-surface.sh` (Abschnitt 2d) |
| QA-D-02 | MAJOR (Vertrag) | **Akzeptierte, dokumentierte Grenze.** Verhalten unverändert (OQ-B12: „Eigenprüfung genügt (kein Eingriff in Spec A)“). AC-C16(a) ist jetzt in (a1) Tier `permission` (Managed-Merge mit State `default-agent`, User-Wert-WARNUNG, Rollback) und (a2) Tier `plugin` (C3-v2: `settings-init` schreibt `default_agent` einmalig, `reconcile_opencode_surface_gate` prüft nur den Einstiegspunkt; **keine** weitere Abstimmung: gelöschter Wert wird nicht ergänzt, abweichender Wert ohne Warnung belassen, verschwundene `primary-role` nimmt den Wert nicht zurück) geschnitten. Auf Tier `plugin`+`observe` schützen Agent-Ebene (`deny_edit`, Task 22) und die Config-Tripel. | Spec Revision 1.8 / Amendment B4, §3.4-Cross-Referenz, AC-C16, Plan Task 22 („Amendment-B4-Folge"), `::test_ac_c16a_no_default_agent_reconciliation_at_tier_plugin` |
| QA-D-03 | MINOR | Der Registry-Kommentar bei `has_plugins` ist jetzt wahr für v1 (statischer Default ⇒ Tier `permission`, kein Artefakt) und verweist für v2 auf den C3-Datenblock; P6 gatet nur noch `MODE=enforce` (der Observe-Pfad ist ausgeliefert, der blockierende Pfad nicht implementiert). | `config/ai-providers.yaml` (Kommentar bei `has_plugins: false`) |
| QA-D-04 | MINOR | Die AC-C2-Äquivalenz ist global: der Check läuft über **alle** Einträge aus `load_providers_config(_REPO_ROOT)`, die einen der beiden C3-Keys deklarieren (jeder solche Eintrag muss den Both-or-None-Satz tragen; unter `GO` muss mindestens einer existieren), statt nur über den `Opencode`-v2-Eintrag. | `tests/test_opencode_v2_spike.py::test_ac_c2_gate_fallback_invariants` |

## D

**Branch:** `feat/1007-d-surface` (Basis `dfb77de4`; Arbeitsstand `04d41eb8`). Die Plan-Blöcke der Tasks 20, 21, 22, 23, 25, 26, 27, 28, 29, 30, 31 und 32 sind abgehakt; Task 33 bleibt offen (HITL). Task 24 war bereits mit PR C0 gemergt.

| Task | Agent | Commit | Tests | Status | Abweichungen/Befunde |
|---|---|---|---|---|---|
| 20 | `senior-developer` | `fa42ec7b` | rot `3 failed, 1 passed` → `5 passed` | `done` | Der Builder ist closed-world: je Aktion (`edit`, `shell`, `subagent`, in dieser Reihenfolge) **genau ein** Eintrag. `_map_claude_tools_to_opencode_permissions` bleibt unverändert. |
| 21 | `senior-developer` | `920882b1` | rot `4 failed, 1 passed` → `5 passed` | `done` | Artefakt trägt `permissions:` als Liste, `steps` ohne `maxSteps`, `model` mit `#variant`; kein `tools`, kein `subagent_depth`, kein `system:`. v1-Referenzprobe byte-identisch. Die Provenienz-Logik wurde in einen gemeinsamen Helfer extrahiert (v1-Rumpf unverändert). |
| 22 | `senior-developer` | `90459853` | rot **`3 failed, 2 passed`** (Plan erwartete `4 failed, 1 passed`) → `173 passed` | `done` | `deny_edit = strict AND permission_deny_required(pc, caps, plugin_mode)` wird am Frontmatter-Aufrufort aufgelöst (Amendment B3); der `*`-Deny steht **vor** den Pfad-Allows; schreibgeschützte Rollen werden nie erweitert; `system` in `allowed-fields` aufgenommen. **Befund zum Rot-Zähler:** `test_ac_c16b_no_edit_deny_without_gate` und der Mammouth-Fall waren bereits grün, weil der v2-Builder `deny_edit` noch ignorierte und Mammouth schon auf `opencode-native` lief. |
| 23 | `senior-developer` | `7033a04` | rot `5 failed, 1 passed` → `123 passed` | `done` | Verwaltete `cli.json` mit generischem Passthrough (dokumentierter Key nur `plugins`); `tui.json` nachweislich unberührt (Hash); Rückbau, wenn die Option entfällt. |
| 23-fix | `senior-developer` | `d4b17147` | neuer Test `test_ac_b22_cli_json_rolled_back_on_v1_surface`; `127 passed` | `done` | Auf einer v1-Oberfläche löste `cli_file` nicht auf, deshalb überlebte der Namespace. Behoben: der Rückbau löst die Datei aus der überlebenden `cli-files`-Map auf und warnt, wenn es mehrdeutig bleibt (kein Raten). |
| 25 | `developer` | `aae4664f` | rot `2 failed, 1 passed` → `41 passed` | `done` | Provider-agnostisch über `settings_file` jedes aktiven Providers; die Warnung erscheint für das Repo, `--strict` rc 1, nicht-strikt rc 0. |
| 26 | `developer` | `e9911b1b` | rot `1 failed` → `2 passed` | `done` | Die Datei enthielt nur Kommentare und ein identisches `$schema` ⇒ keine Inhaltsüberführung (Evidenz `JSONC-TRAEGT-NICHTS-BEI`). Die Warnung `opencode-config-duplicate` verschwindet; die Nicht-Vakuität ist gegen das HEAD-Paar belegt. |
| 27 | `technical-writer` | `2e40c5e7` | echter Rot-Lauf durch Wiederherstellen der alten Doku (`2 failed`) → `2 passed` | `done` | Vier Abschnitte, `AGENTS.md-only`, Verweis auf `.opencode/rules/` entfernt. Zusätzlich `docs/concepts/runtime-gate-tiers.md` korrigiert (Aussagen aus der Zeit vor C3). |
| 28 | `tester` | `979a7800` | Szenario PASS; Negativprobe mit `surface-version: v1` Exit 1 | `done` | Registry-Zeilenzahl 1; Assert-Skript im Modus 100755. |
| 29 | `tester` | `54a5eeaf` | `2 passed` | `done` | Prüft genau 6 differierende Dateien und 3 v2-only-Artefakte, alles Übrige byte-identisch; beide Negativproben feuern. **Offener Punkt:** das v2-Plugin-Artefakt überlebt einen Rückwechsel v2→v1 (außerhalb des Geltungsbereichs von AC-B7/B22) — als bekannte Grenze für ein Follow-up notiert. |
| 30 | `tester` | `9736a8ec` | `2 passed`; 135 Golden-Tests grün | `done` | Drei eingebettete Fixture-Digests (`ac01-baseline`, `slimming-golden`, `compact-golden`). |
| 31 | `tester` | `00624008` | `203 passed` | `done` | `opencode_v2_config.py` in den lib-Sweep aufgenommen; AC-T3-Abdeckungstest; AST-Guard gegen Provider-Zweige; die Negativprobe (Provider-Literal) feuert. |
| 32 | `developer` | `04d41eb8` | rot `1 failed` → `1 passed` | `done` | CHANGELOG in `Added`/`Changed` mit Trennung DOKU/VERIFIED. Alle 79 Szenarien PASS (in Batches gefahren); `--validate`, `--check` und `consistency-check` rc 0. **Der vollständige `pytest tests`-Lauf beendete lokal nicht (1188 passed, 0 failed bei ca. 17 %); den Vollsuite-Beleg liefert CI.** |
| 33 | `release` | — | — | `offen — Release-Bump erfordert ausdrückliche Nutzerfreigabe (HITL)` | Kein Bump, kein Tag, kein Push in Phase D. |

## Phase-D-Review-Fixrunde (2026-10-24)

**Quelle:** Review zu `feat/1007-d-surface` (Arbeitsstand `d7e8d187`), Verdict `CHANGES_REQUESTED` ohne Blocker — zwei echte Defekte (QA-E-01, QA-E-03), der Rest Abdeckungs- und Doku-Präzisierung. Der Fixrunden-Commit folgt direkt auf `d7e8d187`.

| Finding | Schwere | Änderung | Beleg |
|---|---|---|---|
| QA-E-01 | MAJOR (Bug) | `opencode-config-duplicate` prüft nur noch `.json`-Settings-Dateien auf einen `.jsonc`-Zwilling. Für `.yaml` (z. B. `.continue/config.yaml`) wurde `config.jsonc` erfunden und ein Phantom-Finding erzeugt, das `--strict` scheitern ließ. | `scripts/lib/consistency/artifact_contracts.py`, `tests/test_artifact_contracts.py::test_ac_d9_yaml_settings_file_is_never_probed_for_a_jsonc_twin` |
| QA-E-03 | MAJOR (Defekt) | Beide Pfadableitungen in `sync_opencode_cli_file` sind gewrappt: ein absolutes `mcp-config.committed-file` (`relative_to` → `ValueError`) und ein aus dem Root ausbrechendes `cli-files`-Value (`safe_path` → `ValueError`) warnen jetzt und kehren zurück, statt einen Traceback zu werfen. | `scripts/lib/opencode_v2_config.py`, `::test_cli_writer_absolute_committed_file_warns_instead_of_raising`, `::test_cli_writer_escaping_cli_files_value_warns_instead_of_raising` |
| QA-E-02 | MINOR | Zwei stille No-ops sind sichtbar: ein Nicht-Objekt-Dokument und ein `cli`-Key mit `null` werden gewarnt (`opencode-v2-cli: <key> is null — not written`), analog zu `providers.<id>: null`. | `scripts/lib/opencode_v2_config.py`, `::test_cli_writer_warns_on_null_value`, `::test_cli_writer_warns_on_non_object_document` |
| QA-E-04 | MINOR | Provider-Doku qualifiziert die closed-world-Aussage: eine Basiszeile je Aktion; der Gate-Lock der `primary-role` erweitert `edit` bei aktivem Gate um `*`-Deny plus Pfad-Allows. | `docs/providers/opencode.md` |
| QA-E-05 | MINOR | Der Gate-Lock-Test behauptet nicht mehr Tier `permission`: er belegt explizit Tier `plugin` + baked `observe` (der v2-Registry-Fall) und präzisiert den Docstring. | `tests/test_opencode_v2_surface.py::test_ac_c16b_orchestrator_artifact_has_edit_deny_when_gate_active` |
| QA-E-06 | MINOR | `test_ac_t3_required_acs_have_tests` ist im Docstring als Namens-/Traceability-Guard ausgewiesen, nicht als Verhaltensabdeckung. | `tests/test_opencode_v2_surface.py` |
| QA-E-07 | MINOR | Szenario 79 prüft zusätzlich die Reihenfolge (`edit`-`*`-Deny vor den Pfad-Allows) und `edit: deny` einer read-only Rolle; die Fixture generiert dafür `explorer`. Folge für den Lab-Diff (Task 29): die Zeile „6 differierende Dateien“ ist damit überholt — der Test erwartet jetzt 7 Dateien und 4 Manifest-Einträge. | `tests/scenarios/asserts/79-opencode-v2-full-surface.sh`, `tests/scenarios/configs/79-opencode-v2-full-surface.project.yaml` |
| RVW-E-02 | MINOR | CHANGELOG-Pfad auf `tests/scenarios/asserts/79-opencode-v2-full-surface.sh` korrigiert. | `CHANGELOG.md` |
| RVW-E-03 | MINOR | AC-C16(a2) deckt jetzt auch den abweichenden User-Wert auf Tier `plugin` ab: kein Merge, keine Warnung, Byte-Gleichheit. | `tests/test_opencode_v2_surface.py::test_ac_c16a_divergent_user_value_stays_silent_at_tier_plugin` |
| RVW-E-05 | MINOR | Plan Task 32 Step 3 annotiert, dass der lokale Vollsuite-Lauf nicht beendete (`1188 passed/0 failed bei ~17 %`); der Vollsuite-Beleg bleibt CI. | `docs/plans/2026-10-22-opencode-v2-support-plan.md` |

## Offene Punkte

- **C3-Gate-Plugin ist observe-only (bekannte Grenze):** Das generierte v2-Plugin annotiert vorgeschlagene Tool-Aufrufe und blockiert nie. Blockieren wäre in v2 erst über `ctx.permission.hook("evaluate")` möglich; dieser Deny-Pfad ist bewusst nicht enthalten und bleibt P6-gated (`MODE=enforce` ist nicht implementiert). Das tatsächliche Gate bleibt damit der Permission-Deny aus C1: `permission_deny_required` hält die verwalteten Edit-/Shell-Tripel bei Tier `plugin`+`observe` additiv erhalten.
- **Amendment B3 (Task 22):** Die Agent-Ebene (`deny_edit`) ist bei Tier `plugin`+`observe` ebenfalls an `permission_deny_required` gebunden (AC-C14 gilt auch dort); verantwortlich ist Task 22, in C3 ist dazu nichts implementiert. Details siehe QA-C-02.
- **QA-C-02 (MAJOR, Vertrag):** Die Agent-Ebene (`deny_edit`, Task 22) muss `permission_deny_required` verwenden (auch Tier `plugin`+`observe`); der Frontmatter-Aufrufort braucht dafür `capabilities` + `plugin_mode`. Bindend im Plan (Task 22) und in Spec Amendment B3 hinterlegt — **nicht** in dieser Runde implementiert.
- **QA-C-03 (MINOR, bekannt):** Ein bereits vorhandenes, identisches, aber unverfolgtes Tripel unterdrückt die End-Einfügung (schwächste Position) und wird nie geclaimt. Nach State-Verlust kann ein v2→v1-Wechsel `permissions[]` (inkl. unserer Tripel) auf einem v1-Dokument hinterlassen, das ein Zod-`.strict`-Parser ablehnen könnte. Entscheidung „Dedupe vs. End-Einfügung" und eine Warnung bei vorhandenen Tripeln ohne State stehen aus.
- **QA-C-05 (MINOR, bekannt):** `finding.file` ist immer `config/plugin-catalog.yaml`, auch für Verstöße aus `.meta-config`-Override oder Inline-Katalog. Die Meldung nennt damit nicht die tatsächliche Quelle.
- **QA-C-06 (MINOR, bekannt):** `_v2_committed_file`/`_v2_provider_entry` duplizieren den Owner-/Committed-File-Scan aus `opencode_v2_config`; `_V2_ACTION_RENAME` ist derzeit toter Code (weder verdrahtet noch entfernt).
- **QA-C-07 (MINOR, bekannt):** `scripts/lib/isolation.py` ist mit 1407 Zeilen (+614 in C1) ein God-Modul, oberhalb der im Repo zitierten ≤600-Richtlinie. Follow-up: Extraktion des v2-Gate-Blocks (dokumentierte Spec-Abweichung).
- **QA-C-08 (MINOR, bekannt):** Die v2-Gate-Writer nutzen `allow_secrets=False`, während der Schwester-Writer derselben Datei `config["allow-committed-secrets"]` durchreicht. Ein Klartext-Secret eines Users bricht damit auch einen reinen Rollback ab; entweder gleiche Secret-Gate-Parameter durchreichen oder die strengere Wahl dokumentieren.
- **OQ-B12** ist mit `VERDICT-C3: GO` an seinem Entscheidungszeitpunkt angelangt. Der dokumentierte Default „Eigenprüfung genügt (kein Eingriff in Spec A)“ gilt weiter, eine ausdrückliche Entscheidung steht jedoch noch aus.
- **QA-D-02 (MAJOR, akzeptierte Grenze, AC-Geltungsbereich):** Auf Tier `plugin` (C3-v2) läuft `_sync_opencode_runtime_gate` — und damit der `default_agent`-Managed-Merge — nicht; `settings-init` schreibt `default_agent` einmalig und `reconcile_opencode_surface_gate` prüft nur den Einstiegspunkt. Ein gelöschter `default_agent` wird dort nicht wieder ergänzt, ein abweichender User-Wert bleibt ohne Merge-WARNUNG, ein verschwundener `primary-role` nimmt den Wert nicht zurück. AC-C16(a) ist entsprechend in (a1) Tier `permission` / (a2) Tier `plugin` geschnitten (Spec Rev. 1.8 / Amendment B4). Schutz auf Tier `plugin`: Agent-Ebene (`deny_edit`) plus Config-Tripel. Eine Angleichung bräuchte einen Eingriff in Spec A oder einen zweiten `default_agent`-Writer — bewusst nicht Teil dieses Auftrags (eigener Spec-Auftrag möglich).
- **Bekannte Doku-Lücke (nicht Teil von QA-D-03):** `docs/concepts/runtime-gate-tiers.md` beschreibt in §2/§7 noch den Stand vor C3 („kein Provider deklariert `runtime_gate: plugin`“, „`has_plugins: false` … **dauerhaft** gesperrt“). Für die v2-Oberfläche ist das inzwischen falsch; die Datei braucht eine eigene, redaktionelle Nachführung. **Erledigt in Task 27 (`2e40c5e7`):** die Aussagen sind korrigiert.
- Die unabhängigen Stränge B, C1/C2 und D sind durch OQ-B12 nicht blockiert.
- **Plandefekt Task 15:** Der Plan ging davon aus, dass `tests/test_mcp_config.py` unverändert bleibt. Der Test `test_build_connection_entry_opencode_json_v2_matches_v1_shape` kodierte jedoch „v2 == v1 inkl. `enabled: true`“, was AC-C7 widerspricht; die Assertion musste invertiert werden (v1 `enabled is True`, v2 ohne `enabled`, übrige Schlüssel gleich).
- **Plandefekt Task 17:** Eine zweite Fixture in `tests/test_mcp_config.py` führte ein synthetisches v2-Dokument mit `enabled: true`; nach AC-C10 ist das ungültig. Der Schlüssel wurde entfernt, die Assertions blieben unverändert.
- **Bekannte Grenze für C3/D:** Der MCP-Writer partizipiert nicht am laufbezogenen `claimed_files`-Set (im Modul-Docstring dokumentiert; die aktuelle Registry hat genau einen v2-Eigentümer). Bei einem zweiten v2-Eigentümer auf derselben Datei muss die Kollisionsbehandlung vor Task 23/D nachgezogen werden; ebenso überspringen Schreibvorgänge auf dieselbe Datei den committeten Managed-Write.

### Aus Phase D

- **Task 33 (Release-Bump) offen:** Der Minor-Bump und das Verschieben des Unreleased-Abschnitts in einen Versionsabschnitt erfordern eine ausdrückliche Nutzerfreigabe (HITL). Der Task ist im Plan bewusst nicht abgehakt; Push und Tag bleiben Aufgabe der `git`-Rolle.
- **Bekannte Grenze — v2-Plugin-Artefakt beim Rückwechsel:** Ein Wechsel v2→v1 baut die verwalteten Config-Namespaces und die `cli.json` zurück, lässt aber `.opencode/plugins/agent-meta-runtime-gate.js` stehen. Das liegt außerhalb des Geltungsbereichs von AC-B7/AC-B22 (Befund aus Task 29, `54a5eeaf`) und ist als Follow-up offen.
- **Bekannte Grenze — `claimed_files`:** MCP- und `cli.json`-Writer treten dem laufbezogenen `claimed_files`-Set nicht bei (siehe „Bekannte Grenze für C3/D“). Die aktuelle Registry hat genau einen v2-Eigentümer, daher ist das heute folgenlos; bei einem zweiten Eigentümer derselben Datei muss die Kollisionsbehandlung vorher nachgezogen werden.
- **Amendment B4 (`default_agent`):** Auf Tier `plugin` wird `default_agent` nicht abgestimmt (Details unter QA-D-02 oben). Die Agent-Ebene (`deny_edit`, umgesetzt in Task 22) zusammen mit den Config-Tripeln ist dort die tragende Schutzschicht.
- **Doku-Vorbehalt für MCP-Felder:** Die Doku zu MCP-Feldern trennt DOKU- und VERIFIED-Aussagen (CHANGELOG in Task 32 ebenso). Die Vorbehalte sind beim Weiterbau der Doku zu erhalten; für Felder, die nur als DOKU belegt sind, darf keine Verifikationsbehauptung entstehen.

## Nächste Schritte

1. Review und PR für Phase D (Tasks 20–32 ohne 24) auf `feat/1007-d-surface` (Arbeitsstand `04d41eb8`).
2. Nach dem Merge: Task 33 ausschließlich mit ausdrücklicher Nutzerfreigabe (Release-Bump; Push und Tag danach durch die `git`-Rolle).
