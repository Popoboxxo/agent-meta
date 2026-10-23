# Opencode v2-Support — Ausführungsstatus (Plan B / Issue #1007)

**Zweck:** Ausführungs-Ledger zum Plan `docs/plans/2026-10-22-opencode-v2-support-plan.md` (Phasen C0, B, C1/C2, C3, D) und damit zum Tracking-Issue #1007. Das Dokument hält je Phase und je Task den erreichten Stand, die Beleg-Commits, die Testlage und die substanziellen Befunde fest; es ersetzt weder Plan noch Spec.

**Geltungsbereich:** Branch `feat/1007-b-keys` (Basis `main` = `526a5dab`; Phase C0 über PR #1011 gemergt, C0-Ledger-Commit `52a72a0f`, Evidenz-Nachbesserung `2978753c`). Phase-B-Arbeit von `bd49dc5b` bis `d5853d1e`. Stand: 2026-10-23.

**Datenquelle:** Commits dieses Branches, die im Plan gesetzten Checkboxen (C0: Tasks 1, 2, 3, 3a, 24; B: Tasks 4–12) sowie die dort protokollierten Testläufe.

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
| C1/C2 | 13, 13a, 14–17 | `offen` |
| C3 | 18–19 | `offen` |
| D | 20–33 (ohne 24) | `offen` |

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

## Offene Punkte

- **OQ-B12** ist mit `VERDICT-C3: GO` an seinem Entscheidungszeitpunkt angelangt. Der dokumentierte Default „Eigenprüfung genügt (kein Eingriff in Spec A)“ gilt weiter, eine ausdrückliche Entscheidung steht jedoch noch aus.
- Die unabhängigen Stränge B, C1/C2 und D sind durch OQ-B12 nicht blockiert.

## Nächste Schritte

1. Review und PR für Phase B (Tasks 4–12).
2. Danach Phase C1/C2 (Tasks 13, 13a, 14–17), PR nach grüner CI.
