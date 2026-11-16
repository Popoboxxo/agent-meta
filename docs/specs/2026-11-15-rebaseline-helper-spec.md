# Rebaseline-Helper — Spec
> Status: DRAFT (noch nicht freigegeben; Freigabe laut Entscheidung E-10 durch den Nutzer steht aus) — Entscheidungen OF-1/5/6 entschieden (Nutzer, 2026-11-16); Status DRAFT bis Nutzerfreigabe
> Plan: `docs/plans/2026-11-15-rebaseline-helper-plan.md`
> Datum: 2026-11-15 | Entscheidung: E-10 | Roadmap: `docs/plans/2026-11-15-master-roadmap.md` P4 / PR 1.3 | Issues: #1237, #1115 (Duplikat-Teil)
> Klasse: M (siehe Abschnitt Klassifikation)
> Abweichung zu E-10: E-10 sieht `APPROVED (User, 2026-11-15)` vor; die Spec bleibt bewusst DRAFT, weil die Nutzerfreigabe aussteht und weitere Fragen (Abschnitt „Offene Fragen“: OF-2/3/4/7/8/9) offen sind. Ob `--validate-spec-plan` den Status `DRAFT` akzeptiert, ist UNBELEGT (Rule `spec-plan-workflow` und Validator-Code nicht verifiziert; vor Task 0 per Lauf prüfen).
> PR-Hinweis: PR-Text referenziert `Refs #1237` (kein Closing-Keyword), da #1237 Empfehlung 2 hier ausdrücklich nicht gelöst wird.

## Klassifikation

- Klasse **M**: reines Tooling, 1 neues lib-Modul, 1 dünner Entrypoint, 1 Testdatei, 1 Doku-Eintrag; kein Template-Edit, keine Render-Wirkung des Helper-Codes selbst, keine Rebaseline durch den Helper-PR selbst (Roadmap P4: „keiner (Tooling)“). Ausnahme: ein Verweis im `conventions`-Skill könnte Render-Wirkung haben, falls die Skill-Quelle ein gerendertes Template ist (Quelle UNBELEGT, siehe Plan Task 10 und OF-7).
- Kein L: kein neues öffentliches Config-Schema, kein neuer Admin-Schreibpfad.
- Python 3.9-kompatibel (`typing.List`/`Optional`, kein `X | Y`, kein `match`), nur Stdlib im Helper-Code selbst; transitiv lädt der `importlib`-Import von `tests/test_ac01_render_identity.py` PyYAML (`yaml.safe_load` bei `_PROVIDERS`) — das deckt die dokumentierte Runtime-Ausnahme (`docs/adr/0001-pyyaml-runtime-ausnahme.md`); provider-agnostisch.

## Entscheidungen

Nutzerentscheidungen zu den Fragen der Vorversion (Status der Spec bleibt DRAFT):

1. Befehlsform: eigenes `scripts/rebaseline.py` plus `scripts/lib/rebaseline.py`; KEIN `sync.py`-Flag.
2. Reason-Log: `.meta-config/rebaseline-log.jsonl` (getrackt, nicht unter `tests/fixtures/`).
3. `_FIXTURE_TREES`-Zeile wird automatisch zeilengenau gepatcht und steht in der Gate-Allowlist.
4. `topology-golden`-a2a-Fixtures werden per Render aktualisiert (Aktion `auto`); `schema-property-paths.json` bleibt `report-only`.
5. `--base` Default `origin/main`; ohne Remote Fallback auf lokales `main` mit Warnung.
6. Preflight: nur die Rebaseline-Artefakte müssen sauber sein; Quell-Änderungen dürfen uncommittet sein.
7. Reihenfolge: Implementierung des Helpers erst NACH P3 (#1246, Basetemp-Pfad-Stabilität); Roadmap-Reihenfolge P3 -> P4. Hinweis: #1246 (PR #1291, offen, gestapelt auf #1290, nicht gemergt) löst nur den TMPDIR-abhängigen pytest-Basetemp und nur unter Linux (macOS/Windows: `gettempdir()`); es ist NICHT der Owner für #1237 Empfehlung 2 (siehe Nicht-Ziele, OF-4).

### Alternativen-Abwägung

| Entscheidung | Gewählt | Alternativen | Begründung |
|---|---|---|---|
| 1 Befehlsform | eigenes `scripts/rebaseline.py` | (a) `sync.py --rebaseline` (Wortlaut #1237 Empf. 1); (b) Make-/Shell-Wrapper | `sync.py` bleibt Generator ohne Test-/Fixture-Wissen; Helper braucht Testmodul-Funktionen und Git-Lesezugriff; Wrapper ohne Gate/Log wäre Status quo. Nachteil: weicht vom Issue-Wortlaut ab (OF-2). |
| 1b Funktionsquelle | `importlib` aus Testmodulen | Extraktion nach `scripts/lib/` | Keine Doppel-Logik, kleiner PR; Extraktion ist größerer Eingriff in 5500+-Zeilen-Testdateien (OF-3). |
| 3/4 Goldens | `_FIXTURE_TREES` + a2a-Fixtures `auto`, Rest `report-only` | (a) alle Goldens auto-regenerieren; (b) alles report-only | Auto-Regenerierung würde Review-Wert der Hand-Patches (SG/CG) entwerten und Fehlpins absorbieren; report-only für alles lässt die häufigsten Handgriffe manuell. |
| 0 Gesamtansatz | Helper + Gate | „Nichts tun“/nur Doku-Checkliste | Doku allein hat bei #1115 zweimal vergessene Pins nicht verhindert (CI-Rot); Aufwand M ist vertretbar. |

## Problem

- Jede Template-/Render-Änderung braucht heute eine manuelle Rebaseline aus bis zu 9 Pin-Klassen (Tabelle in „Ist-Zustand“). Die Reihenfolge steht nirgends als Mechanismus, nur als Prozess-Docstring (`tests/test_ac01_render_identity.py:20-23`) und als Task-Prosa in Plänen.
- Vergessene Fixtures sind der häufigste CI-Rot-Grund: `compact-golden/agents-managed.md`, `topology-golden/schema-property-paths.json`, Kontext-Ceilings `_IST_FULL`/`_IST_COMPACT`, AC-T4-Digests. Bei #1115 wurde dies zweimal erst in CI bemerkt (`release-checklist`, `test-environments`).
- `sync.py` ohne `--config` löst Config per `Path.cwd()` auf (`scripts/lib/cli_commands.py:673-698`); im Worktree-Betrieb läuft es dadurch im falschen Checkout.
- Es gibt kein Diff-Gate: `--write` (`__main__`-Block in `tests/test_ac01_render_identity.py`) schreibt den gesamten Manifest-Stand; ob nur erwartete Einträge driften, prüft der Mensch per Hand-Diff (die Logs in der Testdatei dokumentieren das Verfahren „per entry statt `--write`“ an dutzenden Stellen).
- Es gibt keinen Vorab-Report, welche Pins/Goldens eine Änderung betrifft.

## Ziel

- EIN Befehl führt alle Rebaseline-Schritte in fester Reihenfolge aus (Issue #1237 Empfehlung 1), erzwingt ein Diff-Gate (nur erwartete Dateien/Schlüssel dürfen sich ändern) und berichtet vorab und nachher, welche Pins/Goldens betroffen sind.
- Pflicht-Grund (`--reason`) wird in ein Log geschrieben (Issue #1237: „mandatory reason written to a log file“).
- Ceiling-Re-Pin (#1115): der Helper misst mit `measure_artifacts` und druckt den fertigen Re-Pin-Block für `_IST_FULL`/`_IST_COMPACT`; Toleranz-Konstanten bleiben unberührt (#1115 AC 3).
- `--check-only` (= `--dry-run`): nur messen und berichten, keine Schreibzugriffe; Exit 1 bei Drift.
- Idempotent: zweiter Lauf ohne Quelländerung = 0 Änderungen, Exit 0, kein Log-Eintrag.
- Root-sicher: Repo-Root kommt aus dem Ort des Helpers, nie aus `cwd`; jeder `sync.py`-Aufruf bekommt explizites `--config`.

## Nicht-Ziele

- Keine Render-Determinismus-Arbeit: #1237 Empfehlung 2 (umgebungs-/datums-/pfadabhängige Werte aus gehashten Artefakten verlagern) hat KEINEN Owner — #1246/PR #1291 löst nur den TMPDIR-abhängigen pytest-Basetemp (nur Linux). Hier explizites Nicht-Ziel; Folge-Issue wird vorgeschlagen (OF-4).
- Plattformgrenze: Idempotenz (AC 5) und Check-only-Exit 0 werden nur unter Linux zugesichert; macOS/Windows (`gettempdir()`) sind nicht belegt.
- Kein automatisches Regenerieren von `slimming-golden`/`compact-golden`/`topology-golden`: diese Fixtures werden per Hand-Patch gepflegt (Ausnahme: die a2a-Fixtures in `topology-golden`, siehe Entscheidung 4) (Logs `tests/test_ac01_render_identity.py`, `tests/test_template_slimming_equivalence.py:180-236`); der Helper prüft sie und meldet Betroffenheit, schreibt sie nicht (außer den a2a-Fixtures in `topology-golden`).
- Keine automatische Änderung der Ceiling-Tabellen (nur Druck des Blocks; Mensch verifiziert, #1115 „human step is verification only“).
- Keine Lockerung von `TOLERANCE_MAX_BYTES` (`tests/test_context_budgets.py:48`) oder irgendeiner Ceiling.
- Keine Konsolidierung der fünf Drift-Mechanismen zu einem (Issue-Kontext) und kein neues Hash-Format.
- Kein Commit/Push/Tag durch den Helper; Git nur lesend (`diff --name-only`, `status --porcelain`).
- Kein Ersatz für `sync.py`; der Helper orchestriert, er dupliziert keine Sync-Logik.

## Ist-Zustand (verifiziert auf origin/main, Worktree `wt-rebaseline-spec`)

Pin-Klassen (jede ist ein Rebaseline-Ziel):

| Klasse | Artefakt | Beleg | Regenerierbar |
|---|---|---|---|
| AC | `tests/fixtures/ac01-baseline/hashes.json` (Provider-Matrix-Hashes) | `tests/test_ac01_render_identity.py`: `_MANIFEST`, `render_matrix_hashes`, `diff_against_manifest`, `__main__`-Block mit `--write` (Symbol-Anker; zuletzt verifiziert ~:1058, :1145, :1172, :1514-1521) | ja, `--write` (schreibt voll, kein Gate) |
| AC-T4 | Fixture-Baum-Digests `_FIXTURE_TREES` | `tests/test_opencode_v2_surface.py`: `_FIXTURE_TREES`, `_fixture_tree_sha256`, `test_ac_t4_fixtures_unchanged` (Symbol-Anker; ~:5512-5516, :5519, :5534); darüber ein Kommentar-Log (~:5495-5511) | nein (Literal von Hand) |
| SG | `tests/fixtures/slimming-golden/<rolle>.md` | `tests/test_template_slimming_equivalence.py:269` (`_GOLDEN_DIR`), Rollenzahl `:5` | nein (Hand-Patch) |
| CG | `tests/fixtures/compact-golden/{orchestrator,agents-managed}.md` | `tests/test_orchestrator_compact_sections.py:78`, `tests/test_gate_card_compact.py:93` | nein (Hand-Patch) |
| TG | `tests/fixtures/topology-golden/*` inkl. `schema-property-paths.json` | `tests/test_ac01_render_identity.py` (`render_topology_rule`, ~:1339), `tests/test_orchestrator_topology_docs.py` (Zeilenanker nicht neu verifiziert) | a2a-Fixtures ja (Render, `auto`), `schema-property-paths.json` nein (`report-only`) |
| H1 | `.meta-config/generated-file-hashes.json` | `scripts/lib/generated_file_drift.py:45`, `_save_hashes` `:68` | ja, durch `sync.py` |
| H2 | `.meta-config/context-hashes.json` | `scripts/lib/context.py:43`, `:69` | ja, durch `sync.py` |
| SA | `standalone/agents/*.md`, `standalone/README.md` | `scripts/lib/standalone.py:534`, `:560`; Drift `:575-582`; CLI `scripts/lib/cli_commands.py:590-611` (`--render-standalone [--check] [--dry-run]`) | ja |
| CE | Ceilings `_IST_FULL` / `_IST_COMPACT` | `tests/test_context_budgets.py`: `_IST_FULL` (~:300), `_IST_COMPACT` (~:583, nicht neu verifiziert), `_ceiling` (~:313); Messung `scripts/lib/context_report.py:130` (`measure_artifacts`); CLI `scripts/measure_context.py:257` | nur Messung |

Weitere Belege:

- Reihenfolge der Schritte laut bestehendem Plan: `docs/plans/2026-11-15-git-trailer-contract-plan.md:188-205` (Task 9: Golden-Patch → `--write` mit Diff-Gate → `--render-standalone` → `sync.py` → Ceilings → Commit).
- Bei der Standalone-/Fixture-Auflösung gilt: Config-Auto-Detect über `cwd` und Root-Ableitung aus `--config` (`scripts/lib/cli_commands.py:673-698`); der Setup-Wizard startet bei fehlender Config (`:680-690`) und ist im Helper-Betrieb unerwünscht.
- `sync_pipeline.py:_sync_stage_tmp_sink` (~:236-291, per Read geprüft) provisioniert nur das Tmp-Sink-Verzeichnis (`resolve_tmp_paths`, `ensure_tmp_sink`); es injiziert KEINE Umgebungswerte ins Render-Ergebnis. Die frühere Zuordnung war falsch. Die Render-Injektion der Sink-Variablen liegt in `scripts/lib/config.py` (~:2124-2140, per Read verifiziert): `resolve_tmp_paths`, dann `TMP_SINK_ABS_PATH`, `TMP_SINK_ENV_PIN_BLOCK`, `PYTEST_BASETEMP` und Token-Ersetzung in `TEST_COMMANDS`/`CODE_QUALITY_RULES`. `tmp_paths.py` (~:231-258) ist `resolve_pytest_basetemp` (Basetemp-Auflösung, laut Re-Check; nicht selbst neu gelesen), keine Render-Injektion. Die Matrix normalisiert Datum und Modellzeile (`_hash_file`, `render_matrix_hashes`). Verbleibende Pseudo-Drift durch Umgebungs-/Datums-/Pfadwerte hat keinen Owner (siehe Nicht-Ziele, OF-4).
- Bestehende Sync-Drift: Der #1291-Bericht nennt 22 Dateien „out of sync“ (TMPDIR-unabhängig, nicht aus #1291; nicht gegen HEAD verglichen). Das bedroht AC 2 und Plan Task 11 Step 2 (`--check-only` → Exit 0) und muss vor Task 11 geklärt werden (Risiko, siehe unten).
- #1291 ändert `tests/fixtures/topology-golden/schema-property-paths.json` (reine Pfadliste, keine Hash-Klasse, hash-neutral laut Analyse); Roadmap P3 „RB keiner“ bleibt konsistent.
- Der AC-T4-Digest läuft über `rglob("*")` des gesamten Fixture-Verzeichnisses (`tests/test_opencode_v2_surface.py:5518-5528`): jede zusätzliche Datei unter `tests/fixtures/ac01-baseline/` ändert den Digest. Das Rebaseline-Log darf deshalb NICHT dort liegen.
- Issue-Daten: `generated-file-hashes.json` in 95 Commits/90 Tagen, `ac01-baseline/hashes.json` 62, `compact-golden` 17 (#1237).
- Dokumentationsort für die Verfahrensregel: Skill `conventions` (`.claude/skills/conventions/SKILL.md`, generiert) — #1115 AC 2 verlangt einen Verweis dort. Die Skill-Quelle (projektspezifisch vs. gerendertes Template) ist UNBELEGT: `agents/1-generic/skills/conventions/SKILL.md` existiert nicht, Glob/Grep waren nicht lauffähig. Ist die Quelle ein Template, hat der Verweis Render-Wirkung (Rebaseline nötig) — siehe OF-7.
- `tests/test_provider_agnostic_dispatch.py` scannt nur `scripts/lib/**`; `scripts/rebaseline.py` (Entrypoint) ist davon nicht abgedeckt.

## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)

### C1 — Entrypoint und Modul

- Neu: `scripts/rebaseline.py` (nur `argparse` + `main()`, wie `scripts/sync.py`; `print()` erlaubt) und `scripts/lib/rebaseline.py` (Logik, ≤ 600 Zeilen; bei Überschreiten Aufteilung in `rebaseline_pins.py` für die Pin-Registry). Ausgaben im lib-Modul über `SyncLog`/Rückgabewerte, nicht `print()`.
- Root: `ROOT = Path(__file__).resolve().parents[1]` (Entrypoint) bzw. `--root DIR` (Test-Override). `cwd` wird ignoriert; alle Subprozesse laufen mit `cwd=ROOT` und `sys.executable`.
- Config: jeder `sync.py`-Aufruf bekommt `--config <ROOT>/.meta-config/project.yaml`. Fehlt die Datei → Exit 2 (kein Wizard-Start).

### C2 — CLI-Flags

```
python3 scripts/rebaseline.py --reason TEXT [--expect GLOB]... [--expect-key GLOB]...
                              [--base REF] [--check-only | --dry-run] [--root DIR]
                              [--steps LIST] [--skip-verify] [--json]
```

- `--reason TEXT`: Pflicht im Schreibmodus (min. 10 Zeichen, nicht leer); im `--check-only`-Modus optional.
- `--expect GLOB` (wiederholbar): zusätzlich erlaubte repo-relative Pfade (POSIX, `fnmatch`).
- `--expect-key GLOB` (wiederholbar): erlaubte Schlüssel in `hashes.json` bzw. `generated-file-hashes.json`/`context-hashes.json` (Format `<Provider>/<relpath>`, bzw. relpath).
- `--base REF` (Default `origin/main`; ohne erreichbaren Remote Fallback auf lokales `main` mit Warnung im Report): Basis für die abgeleitete Erwartung (Abschnitt Diff-Gate).
- `--check-only`/`--dry-run`: Synonyme; kein Schreibzugriff auf das Repo außer dem Scratch-Sink. Scratch-/Rollback-Verzeichnisse liegen NICHT unter `tempfile`/Systemtemp, sondern im Tmp-Sink über `resolve_tmp_paths` (`.tmp/`, Repo-Containment; Vorbild `tests/test_context_budgets.py` importiert `resolve_tmp_paths`). Ist der Sink deaktiviert → Exit 2 (ENTSCHIEDEN, OF-6). Nutzung von `tempfile.TemporaryDirectory` im `--write`-Block des Testmoduls ist kein Vorbild.
- `--steps LIST`: kommagetrennte Teilmenge aus `ac01,standalone,sync,topology,digests,ceilings` (Default alle, Reihenfolge bleibt fest).
- `--skip-verify`: überspringt Schritt 9 (gezielte Pin-Tests); nur Entwickler-Diagnose, im Log vermerkt.
- `--json`: Report zusätzlich maschinenlesbar auf stdout.

### C3 — Exit-Codes

| Code | Bedeutung |
|---|---|
| 0 | OK; im Schreibmodus ggf. Änderungen geschrieben und gate-konform; im Check-only: keine Drift |
| 1 | nur Check-only: Drift vorhanden (Report listet sie) |
| 2 | Aufruf-/Preflight-Fehler (fehlendes `--reason`, Config fehlt, Arbeitsbaum nicht sauber, unbekannter Step) |
| 3 | Diff-Gate verletzt (unerwartete Datei/Schlüssel); Schreibänderungen zurückgerollt |
| 4 | Teilschritt-Subprozess fehlgeschlagen (Exit ≠ 0 von `--render-standalone`/`sync.py`/Render); zurückgerollt |
| 5 | Nach-Verifikation rot (gezielte Pin-Tests); Änderungen bleiben (Report nennt rote Pins), Log-Eintrag mit `verify: failed` |
| 6 | Rest-Drift im zweiten Check-only-Durchlauf (Idempotenz verletzt); Änderungen bleiben, Report listet Rest-Drift (Zeile `RESIDUAL`). Verifikation (Schritt 9) und Log (Schritt 10) laufen trotzdem; Log-Feld `idempotency: failed`. Priorität bei mehreren Fehlern: 5 vor 6. ENTSCHIEDEN (Nutzer, 2026-11-16, OF-1) |

### C4 — Report-Format (stdout, Deutsch/Englisch-neutral, ASCII)

```
REBASELINE  root=<ROOT>  base=<REF>  mode=<write|check-only>
PRE   <Klasse>  <Artefakt>  <n> betroffen|ok|n/a   (je Pin-Klasse eine Zeile)
STEP  1 ac01        wrote 4 of 1101 hashes  gate=ok
STEP  2 standalone  wrote 1 file            gate=ok
STEP  3 sync        updated generated-file-hashes.json (9 keys), context-hashes.json (0)
STEP  4 topology    wrote 2 a2a fixtures    gate=ok
STEP  5 digests     _FIXTURE_TREES: slimming-golden OLD->NEW (patched) | unchanged
STEP  6 ceilings    CE: RE-PIN-BLOCK follows (not applied)
POST  <Klasse>  <Artefakt>  ok|OFFEN
RESIDUAL  <Klasse>  <Artefakt|Schluessel>   (je Rest-Drift-Eintrag eine Zeile; nur bei Exit 6)
RESULT  changed=<n> files  gate=ok  verify=ok|failed|skipped  idempotent=ok|drift  log=<Pfad>
```

- Die STEP-Zeilen entsprechen exakt der Schrittreihenfolge aus AC 9 (`ac01, standalone, sync, topology, digests, ceilings`) = Datenfluss-Schritte 2 bis 7.
- `--json` liefert dieselben Felder als ein JSON-Objekt (`pre`, `steps`, `post`, `result`).

### C5 — Pin-Registry (Daten, nicht Code-Verzweigung)

- Modul-Konstante `PINS: Tuple[PinSpec, ...]`, je Eintrag: `klass`, `paths` (Globs), `detector` (`pytest`-Knoten-IDs oder interne Funktion), `writable` (`auto|report-only`). Neue Pin-Klasse = ein Registry-Eintrag, kein neuer Ablaufcode.
- Detektoren für „vorab/nachher“: AC über `render_matrix_hashes` + `diff_against_manifest` (importiert aus `tests/test_ac01_render_identity.py` per `importlib`, nicht kopiert; Risiko: Kopplung an Modul-Level-Seiteneffekte und, bei `test_opencode_v2_surface.py` (>5500 Zeilen, importiert für `_fixture_tree_sha256`/`_FIXTURE_TREES`), an eine sehr große Testdatei, siehe Risiken/OF-3), AC-T4 über `_fixture_tree_sha256` vs. `_FIXTURE_TREES`, H1/SA über `sync.py --dry-run --config` bzw. `--render-standalone --check`, SG/CG/TG/CE über gezielte `pytest -q -x`-Aufrufe auf die zuständigen Testdateien (Liste in der Registry).

### C6 — Rebaseline-Log

- Datei: `.meta-config/rebaseline-log.jsonl` (getrackt, append-only, eine JSON-Zeile je Schreiblauf mit Änderungen): `{ts, reason, base, head, steps, changed_files, changed_keys, gate, verify, idempotency}` (`idempotency`: `ok|failed`).
- Nicht im Fixture-Baum (AC-T4-Digest, siehe Ist-Zustand). Nicht in `tests/fixtures/ac01-baseline/`.
- Ergänzt, ersetzt nicht das menschenlesbare Log im Docstring von `tests/test_ac01_render_identity.py`; der Helper schreibt dort nichts.

## Datenfluss

Ablauf und Reihenfolge:

Schreibmodus (feste Reihenfolge; jeder Schritt hat ein eigenes Gate):

0. Preflight: `--reason` gültig; `ROOT`/Config gelöst; `git status --porcelain` enthält keine Änderungen an Rebaseline-Artefakten (Entscheidung 6; Quell-Änderungen an Templates/Rules/Config dürfen uncommittet sein, sie definieren den Scope); „Rebaseline-Artefakte“ = genau die Klassen-Allowlist (Abschnitt Diff-Gate), nicht SG/CG/`schema-property-paths.json`/Ceiling-Tabellen — deren Hand-Patches dürfen dirty sein (Git-Trailer-Plan: Golden-Patch zuerst). Die Granularität: dateiweise per `git status --porcelain`; einzige Ausnahme `tests/test_opencode_v2_surface.py` (Allowlist nur für die `_FIXTURE_TREES`-Zeilen): dort prüft der Preflight zeilenweise per `git diff -U0` und bricht nur bei Hunks außerhalb der `_FIXTURE_TREES`-Zeilen ab. Die Dirty-Menge des Preflights wird als Baseline gespeichert (Diff-Gate arbeitet als Differenz dazu). Snapshot der zu schreibenden Artefakte in den Tmp-Sink (`.tmp/`, via `resolve_tmp_paths`, nicht Systemtemp) für Rollback.
1. PRE-Report: alle Pin-Detektoren laufen auf dem Ausgangsstand (ohne Schreiben); der Report nennt je Klasse „betroffen“ oder „ok“.
2. `ac01`: Matrix-Render in den Scratch-Sink (`render_matrix_hashes`), Vergleich mit Manifest; Schreiben nur der abweichenden Schlüssel in `tests/fixtures/ac01-baseline/hashes.json` (Format `json.dumps(indent=1, sort_keys=True) + "\n"` wie im `--write`-Block). Gate pro Schlüssel. Dieser full-Render (9 Provider-Projekte via `_make_project`) wird für Schritt 7 (`_IST_FULL`) wiederverwendet.
3. `standalone`: `scripts/sync.py --render-standalone --config <CFG>`; Gate auf `standalone/**`.
4. `sync`: `scripts/sync.py --config <CFG>`; erzeugt `.meta-config/generated-file-hashes.json`, `context-hashes.json` und die gerenderten Agent-/Kontext-Ausgaben (vollständige Liste der Schreibziele UNBELEGT, OF-9); schreibt zudem getrackte Kontext-Dateien (`CLAUDE.md`, `AGENTS.md`) und, bei `cwd == Root`, die Schema-Enums (`update_roles_enum`/`update_providers_enum`, `scripts/lib/cli_commands.py:637-639`, per Read verifiziert; da der Helper mit `cwd=ROOT` läuft, trifft das zu; Zieldateien liegen in den Schema-Modulen, nicht in `cli_commands.py`). Gate auf die Menge geänderter getrackter Dateien als Differenz zur Preflight-Dirty-Menge.
5. `topology`: a2a-Fixtures in `tests/fixtures/topology-golden/` per Render aktualisieren (`render_topology_rule`, `tests/test_ac01_render_identity.py`); Gate auf genau diese Dateien (Entscheidung 4).
6. `digests`: Fixture-Baum-Digests neu berechnen; weicht ein Digest von `_FIXTURE_TREES` ab UND hat sich der zugehörige Baum in diesem Lauf oder im Arbeitsbaum gegenüber `--base` geändert, wird das Literal in `tests/test_opencode_v2_surface.py` automatisch zeilengenau ersetzt (Entscheidung 3; Gate: nur diese Zeile). Ändert sich ein Baum ohne erwarteten Pfad → Gate-Verletzung. Die Kommentarzeilen über `_FIXTURE_TREES` (Log, ~:5495-5511) werden NIE angefasst (ENTSCHIEDEN, Nutzer 2026-11-16: Verzicht, OF-5); gepatcht wird nur der Digest-Literalwert in der betroffenen Dictionary-Zeile.
7. `ceilings`: `measure_artifacts` (`scripts/lib/context_report.py`) misst an ZWEI getrennten Messbasen, beide NICHT am self-gesyncten Repo: `_IST_FULL` an den Matrix-Projekten von `_make_project` (Fixture `measured` in `tests/test_context_budgets.py`) — der full-Render aus Schritt 2 wird geteilt; `_IST_COMPACT` an einem eigenen Render über `context_report.render_into_work_dir(..., profile="compact")` (Messbasis des Testmoduls, Kommentar zu `_IST_COMPACT`). Vergleich mit `_ceiling(_IST_FULL)`/`_ceiling(_IST_COMPACT)`; nur bei Überschreitung wird der exakte Re-Pin-Block (Provider/Artefakt, alter Ist, gemessener Ist) gedruckt. Keine Dateiänderung. Die Messung von `scripts/measure_context.py` am Repo ist damit NICHT die Messbasis der Pins.
8. Zweiter Check-only-Durchlauf aller Schritte (Idempotenz-Beweis); Rest-Drift wird als `RESIDUAL` gelistet und der Exit-Code 6 vorgemerkt; die Schritte 9 und 10 laufen trotzdem (ENTSCHIEDEN, OF-1; Reihenfolge 5 vor 6; frühere Fassung Exit 4 kollidierte mit C3 „4 = Subprozess-Fehler mit Rollback“).
9. Verifikation: gezielte `pytest -q`-Aufrufe der Pin-Testdateien aus der Registry (kein Voll-Lauf); rot → Exit 5 (Priorität 5 vor 6).
10. Log-Eintrag (C6) nur wenn `changed_files` nicht leer; bei Rest-Drift mit Feld `idempotency: failed`.

Check-only: Schritte 1 bis 7 rechnen in Scratch bzw. mit `--dry-run`; Exit 1 bei jeder Drift, sonst 0. Schritt 10 entfällt.

Rollback: bei Exit 3/4 stellt der Helper aus dem Preflight-Snapshot alle von ihm berührten Dateien wieder her (kein `git checkout`, kein `git stash`).

## Diff-Gate

- Definition: Das Gate ist eine DIFFERENZ zur Preflight-Dirty-Menge: Nach jedem Schreibschritt wird die Menge geänderter getrackter Dateien (`git diff --name-only`/`status --porcelain` minus Preflight-Dirty-Menge; uncommittete Quellen laut Entscheidung 6 sind Baseline und kein Verstoß) und, für JSON-Hash-Dateien, die Menge geänderter Schlüssel gebildet. Jede Datei/jeder Schlüssel außerhalb der Erwartungsmenge → Exit 3, Rollback, Ausgabe der Differenz.
- Erwartungsmenge = Vereinigung aus:
  1. Klassen-Allowlist (Daten im Modul; sie ist zugleich die Definition der „Rebaseline-Artefakte“): `tests/fixtures/ac01-baseline/hashes.json`, `.meta-config/generated-file-hashes.json`, `.meta-config/context-hashes.json`, `standalone/**`, `tests/test_opencode_v2_surface.py` (nur die `_FIXTURE_TREES`-Zeilen; Preflight-Prüfung zeilenweise, siehe Datenfluss Schritt 0), `tests/fixtures/topology-golden/a2a-delegation-gates.role-*.md`, `.meta-config/rebaseline-log.jsonl`; zusätzlich als Nebenwirkungen von `sync.py --config` (abgeleitete Erwartung, nur in Schritt `sync`): die Kontext-Dateien `CLAUDE.md`/`AGENTS.md`, die Schema-Enum-Dateien von `update_roles_enum`/`update_providers_enum` und weitere getrackte Sync-Ausgaben. Pfade der Schema-Enum-Dateien und die Vollständigkeit der „weiteren getrackten Ausgaben“ sind UNBELEGT (`cli_commands.py:590-700` nennt keine Zielpfade; OF-9) und vor Task 11 per Probelauf zu ermitteln.
  2. Abgeleitete Schlüsselerwartung: aus `git diff --name-only <base>...HEAD` plus Arbeitsbaum werden die geänderten Quellen (`agents/**`, `rules/**`, `hooks/**`, `templates/**`, `config/**`, `scripts/lib/**`) auf Rollen-/Rule-/Hook-Stems abgebildet; erlaubt sind `hashes.json`-Schlüssel, deren relpath einen dieser Stems enthält (Muster `<Provider>/**/<stem>*`). Quellen ohne Stem-Abbildung (z. B. `config/**`, `scripts/lib/**`) erlauben KEINE Schlüssel automatisch → der Aufrufer muss `--expect-key` angeben (fail-closed). Key-Gate gilt für alle drei JSON-Hash-Dateien: `hashes.json` (Schlüsselformat `<Provider>/<relpath>`) UND `generated-file-hashes.json`/`context-hashes.json` (Schlüsselformat `relpath` OHNE Provider-Präfix); für letztere gilt dieselbe Stem-Regel auf dem relpath (Muster `**/<stem>*`), `--expect-key` matcht gegen den jeweiligen Schlüsselstring.
  3. Explizite `--expect`/`--expect-key`-Globs.
- Das Gate ist eine Convention boundary gegen akzidentelle Fehlschreibungen, keine Security boundary.
- Die a2a-Fixtures `tests/fixtures/topology-golden/a2a-delegation-gates.role-{inactive,active}.md` sind Teil der Klassen-Allowlist (Schritt `topology`). Geänderte Dateien der Hand-gepflegten Goldens (SG/CG, `schema-property-paths.json`, Ceilings) sind NICHT in der Erwartungsmenge; der Helper schreibt sie nicht, ihr Arbeitsbaum-Stand ist Eingabe (Preflight-Snapshot) und wird nicht als Verletzung gewertet.

## Pin-/Golden-Impact-Report (vorab / nachher)

- Vorab (Schritt 1) und nachher (Schritt 8/9) je Pin-Klasse aus C5: `ok`, `betroffen (n Einträge)` oder `n/a` (Klasse nicht erreichbar, z. B. fehlendes Fixture); bei Goldens die Liste der betroffenen Rollen/Dateien.
- „Betroffen“ heißt: Detektor wäre rot. Der Report ordnet jeder Klasse die zuständige Aktion zu (`auto` = Helper schreibt, `report-only` = Mensch patcht: slimming-/compact-Golden-Datei, Ceiling-Block, Schema-Pfad-Fixture).
- Nach dem Lauf darf keine Klasse `betroffen` mit Aktion `auto` bleiben; `report-only`-Reste sind erlaubt und werden als `OFFEN` gelistet (Exit 5 nur bei roter Verifikation, siehe AC 13).
- Besonders gelistet, weil in Sessions vergessen: `compact-golden/agents-managed.md`, `topology-golden/schema-property-paths.json`, Ceilings `_IST_FULL`/`_IST_COMPACT`, AC-T4-Digests.

## Acceptance Criteria

1. `python3 scripts/rebaseline.py` ohne `--reason` im Schreibmodus → Exit 2, keine Datei verändert.
2. `--check-only` auf sauberem Stand → Exit 0, Report zeigt alle Klassen `ok`; `git status --porcelain` vor/nach identisch.
3. `--check-only` nach einer Template-Änderung → Exit 1, Report listet betroffene Klassen/Schlüssel; kein Schreibzugriff im Repo.
4. Schreibmodus nach Template-Änderung mit passenden `--expect-key` → Exit 0; `hashes.json` ändert nur erwartete Schlüssel; `generated-file-hashes.json` und `standalone/` konsistent.
5. Zweiter Schreiblauf direkt danach → Exit 0, 0 Dateiänderungen, kein neuer Log-Eintrag (Idempotenz). Gültig unter Linux; Plattformgrenze (macOS/Windows nicht zugesichert) siehe Nicht-Ziele.
6. Unerwartete Datei- oder Schlüsseländerung (Test mit künstlich zusätzlicher Drift) → Exit 3, alle berührten Dateien byte-identisch zurückgesetzt.
7. Aufruf aus fremdem `cwd` (z. B. Hauptcheckout bei Worktree-Helper) wirkt ausschließlich auf den Root des Helper-Orts; jeder `sync.py`-Subprozess enthält `--config <ROOT>/.meta-config/project.yaml` und `cwd=<ROOT>` (Test mit gemocktem Subprozess-Runner).
8. Fehlt `.meta-config/project.yaml` → Exit 2, kein Wizard-Start.
9. Die Schrittreihenfolge ist exakt `ac01, standalone, sync, topology, digests, ceilings` (Test über aufgezeichnete Aufrufreihenfolge).
10. Preflight bricht mit Exit 2 ab, wenn Rebaseline-Artefakte (= genau die Klassen-Allowlist) im Arbeitsbaum bereits verändert sind; uncommittete Quell-Änderungen (Templates/Rules/Config) sowie dirty SG/CG/`schema-property-paths.json`/Ceiling-Hand-Patches blockieren NICHT. Granularität: dateiweise (`git status --porcelain`); für `tests/test_opencode_v2_surface.py` zeilenweise (`git diff -U0`): Änderungen außerhalb der `_FIXTURE_TREES`-Zeilen → Exit 2, Änderungen nur an diesen Zeilen blockieren nicht.
11. Das Log `.meta-config/rebaseline-log.jsonl` erhält pro ändernden Lauf genau eine valide JSON-Zeile mit `reason`; die AC-T4-Digests ändern sich durch den Log-Eintrag nicht (Datei liegt außerhalb `tests/fixtures/`).
12. Ceiling-Report (#1115 AC 1): `_IST_FULL` wird am full-Matrix-Render (`_make_project`, geteilt mit Schritt 2), `_IST_COMPACT` an einem eigenen Render über `render_into_work_dir(..., profile="compact")` gemessen (nicht am self-gesyncten Repo); bei künstlich überschrittenem Ist druckt der Helper den Re-Pin-Block mit Provider, Artefakt, altem und gemessenem Wert; `TOLERANCE_MAX_BYTES`, `TOLERANCE_MIN_BYTES`, `TOLERANCE_RATIO` und alle Pins sind danach unverändert (Dateihash-Test).
13. Nach erfolgreichem Lauf sind die gezielten Pin-Tests (`test_ac01_render_identity`, `test_opencode_v2_surface::test_ac_t4_fixtures_unchanged`, `test_template_slimming_equivalence`, `test_gate_card_compact`, `test_orchestrator_compact_sections`, `test_orchestrator_topology_docs`, `test_context_budgets`) grün oder als `OFFEN` mit Aktion genannt; rote Verifikation → Exit 5.
14. `--json` liefert valides JSON mit den Feldern `pre`, `steps`, `post`, `result`.
15. Bei Subprozess-Fehler (simuliert) → Exit 4 und Rollback.
16. `scripts/lib/rebaseline.py` ≤ 600 Zeilen, nur Stdlib im Modul selbst (transitives PyYAML über den `importlib`-Import der Testmodule fällt unter ADR 0001), kein `print()`, kein Provider-Literal (`tests/test_provider_agnostic_dispatch.py`); Python 3.9-kompatibel.
17. Der `conventions`-Skill (Quelle) und `howto/` enthalten einen Verweis auf den Befehl; `docs/` nennt Flags und Exit-Codes (#1115 AC 2).
18. `--base` ohne Remote `origin`: Fallback auf lokales `main`, Warnung im Report, Exit-Code unverändert (Test mit gemocktem Git-Runner).
19. `topology`-Schritt aktualisiert die a2a-Fixtures per Render; Drift dort wird vorab als `betroffen` gemeldet und danach als `ok`; `schema-property-paths.json` bleibt `report-only`.
20. Die `_FIXTURE_TREES`-Zeile wird zeilengenau gepatcht: ausschließlich der Digest-Literalwert der betroffenen Dictionary-Zeile ändert sich; alle anderen Zeilen der Datei, einschließlich der Log-Kommentarzeilen über `_FIXTURE_TREES`, bleiben byte-identisch (Verzicht auf Log-Kommentar, OF-5); der Eintrag ist in der Gate-Allowlist.
21. Rest-Drift im zweiten Check-only-Durchlauf (Idempotenz-Test mit gemocktem, instabilem Render) → Exit 6 (entschieden, OF-1), Änderungen bleiben, Report listet die Rest-Drift (`RESIDUAL`, `idempotent=drift`); Verifikation und Log laufen trotzdem, Log-Feld `idempotency: failed`; bei gleichzeitig roter Verifikation gilt Exit 5. Mapping: C3 (Exit 6), Datenfluss Schritte 8-10.
22. Subprozess-/Gesamtpipeline-Reihenfolge: Preflight → Schritte → Rollback bei Exit 3/4 → Idempotenzlauf → Verifikation → Log (Test mit gemocktem Runner; Verifikations-Exit 5 über `--skip-verify`-Gegenprobe).

## Offene Fragen

Die sieben Fragen der Vorversion sind im Abschnitt Entscheidungen beantwortet. OF-1, OF-5, OF-6 sind entschieden (Nutzer, 2026-11-16) und blockieren die Freigabe nicht mehr. Verbleibend offen: OF-2/3/4/7 (nicht blockierend), OF-8 (vor Plan Task 0), OF-9 (vor Plan Task 11).

### Offene Fragen (Nutzerentscheidung) mit Empfehlung

| ID | Frage | Optionen | Empfehlung | Auswirkung |
|---|---|---|---|---|
| OF-1 | Exit-Code bei Rest-Drift (Datenfluss Schritt 8) | (a) Exit 6 neu; (b) Exit 5 mit Verifikation zusammenlegen; (c) Exit 4 (kollidiert mit Rollback-Semantik) | **ENTSCHIEDEN (Nutzer, 2026-11-16): (a) Exit 6, Änderungen bleiben** | C3-Tabelle (Exit 0-6), AC 21, Plan Task 6/7; Verify (9) und Log (10) laufen trotzdem, Priorität 5 vor 6, Log `idempotency: failed` |
| OF-2 | Befehlsform: eigenes Script vs. `sync.py --rebaseline` (Issue-Wortlaut) | (a) `scripts/rebaseline.py`; (b) `sync.py`-Flag | (a) (Entscheidung 1 bleibt), Abweichung im Issue kommentieren | Keine `sync.py`-Änderung; Issue #1237 nennt (b) |
| OF-3 | Funktionsquelle: `importlib` aus Testmodulen vs. Extraktion nach `scripts/lib/` | (a) importlib; (b) Extraktion | (a) für diesen PR; (b) als Folge, falls Modul-Seiteneffekte/Größe (`test_opencode_v2_surface.py` >5500 Zeilen) stören | Kopplung der Tests an den Helper; PyYAML transitiv (ADR 0001) |
| OF-4 | Owner für #1237 Empf. 2 (Determinismus aus gehashten Artefakten) | (a) neues Folge-Issue; (b) in #1246 erweitern; (c) bewusst offen lassen | (a) Folge-Issue, im PR `Refs #1237` | Idempotenz plattformabhängig bis dahin; Roadmap-Ergänzung |
| OF-5 | Log-Kommentarzeile über `_FIXTURE_TREES` | (a) Verzicht (nur Digest-Literal patchen; maschinenlesbarer Log in `.meta-config/rebaseline-log.jsonl`); (b) Ausnahme: Helper hängt Kommentarzeile an | **ENTSCHIEDEN (Nutzer, 2026-11-16): (a) Verzicht** | AC 20 bleibt „alle anderen Zeilen byte-identisch“; Datenfluss Schritt 6 patcht nur das Digest-Literal; Log nur in `.meta-config/rebaseline-log.jsonl` |
| OF-6 | Scratch-Pfad bei deaktiviertem Tmp-Sink | (a) Exit 2 mit Hinweis; (b) Fallback Systemtemp (Containment-Ausnahme, schwächer) | **ENTSCHIEDEN (Nutzer, 2026-11-16): (a) Exit 2 mit Hinweis** | C2/C3: Helper nur mit aktivem Tmp-Sink lauffähig; kein Systemtemp-Fallback |
| OF-7 | Skill-Verweis (`conventions`) bei Template-Quelle | (a) Verweis nur in `howto/`/Docs; (b) Skill-Quelle editieren + Rebaseline mit dem Helper (Henne-Ei) | (a) bis Skill-Quelle verifiziert | AC 17, Plan Task 10 |
| OF-8 | `--validate-spec-plan` und Status `DRAFT` | Per Lauf prüfen (UNBELEGT) | Vor Task 0 testen | Task 0 Step 2 |
| OF-9 | Schreibziele von `sync.py` (Schema-Enum-Pfade, weitere getrackte Ausgaben) für die Gate-Allowlist | (a) Probelauf `sync.py --config` auf Scratch-Kopie und `git status` auswerten; (b) Schema-Module per Read durchgehen | (a) vor Task 11 | Gate-Allowlist (Diff-Gate 1.), AC 4/6 |

## Abhängigkeiten

- #1246 / PR #1291 (P3, Linux-Basetemp): offen, gestapelt auf #1290, nicht gemergt → Plan Task 0 ist hartes Gate; Reihenfolge P3 -> P4 (Entscheidung 7).
- Roadmap-Kette: nachfolgende Rebaseline-PRs (P6, P8, P12, P17, P19, P26, P29, P30) hängen vom Helper ab.
- Bestehende Sync-Drift (22 Dateien laut #1291-Bericht): muss vor Plan Task 11 Step 2 geklärt sein (Probelauf `sync.py --check` gegen main).
- #1115: nur der Duplikat-Teil (Ceiling-Re-Pin, Verfahrensverweis) wird hier gelöst; #1237 Empf. 2 bleibt ohne Owner (OF-4).
- Henne-Ei Skill-Quelle: Quelle des `conventions`-Skills UNBELEGT; ein Edit an einer Template-Quelle bräuchte den Helper selbst (OF-7).
- Spec-Freigabe (E-10) durch den Nutzer; Status bleibt bis dahin DRAFT.

## Risiken

- Abhängigkeit/Gate: P3 = PR #1291 ist offen (gestapelt auf #1290, nicht gemergt) → Plan Task 0 bleibt hartes Gate.
- Bestehende Sync-Drift (22 Dateien out of sync laut #1291-Bericht, TMPDIR-unabhängig, nicht gegen HEAD verglichen) bedroht AC 2 und Plan Task 11 Step 2 (`--check-only` → Exit 0); vor Task 11 klären (frischer `sync.py --check`-Lauf gegen main).
- `importlib`-Kopplung an `tests/test_opencode_v2_surface.py` (>5500 Zeilen) und `tests/test_ac01_render_identity.py`; PyYAML wird transitiv geladen (ADR 0001).
- Provider-Agnostik-Test deckt nur `scripts/lib/**` ab, nicht den Entrypoint `scripts/rebaseline.py`.

- Der Matrix-Render ist langsam (9 Provider-Projekte); der Check-only-Modus und der Idempotenz-Durchlauf verdoppeln die Laufzeit. Gegenmaßnahme: Scratch-Render einmal, Ergebnis für Schritt 2 und 7 wiederverwenden.
- Stem-Abbildung für die abgeleitete Schlüsselerwartung kann zu eng sein (Config-/Lib-Änderungen) → fail-closed, Aufrufer gibt `--expect-key`; ein zu weites Gate würde Fehler absorbieren (Log-Historie zeigt dieses Risiko: „absorbed silently“).
- `importlib`-Import von `tests/test_ac01_render_identity.py` koppelt den Helper an die Testdatei (Modul-Level-Seiteneffekte, pytest-Fixtures). Alternative: Funktionen nach `scripts/lib/` extrahieren (größere Änderung, eigener Folge-Schritt).
- Rollback-Snapshot deckt nur vom Helper berührte Pfade; parallel editierende Prozesse sind nicht abgesichert.
- Umgebungsabhängigkeit des Renders (Datum, Pfadwerte) kann den Idempotenzlauf stören; #1246 löst nur den Linux-TMPDIR-Basetemp, der Rest hat keinen Owner (OF-4). `sync_pipeline.py:_sync_stage_tmp_sink` ist NICHT die Ursache (provisioniert nur das Sink-Verzeichnis).
- Hand-gepflegte Goldens bleiben ein menschlicher Schritt; der Helper reduziert Vergessen, eliminiert die Arbeit nicht.
- Reihenfolge: Die Implementierung startet erst nach P3 (#1246/PR #1291); bis dahin ist nur Spec/Plan DRAFT (Entscheidung 7). Der Idempotenzlauf ist auch danach nur unter Linux und nur für den Basetemp-Anteil belastbar.
- Roadmap-Folge: nachfolgende Rebaseline-PRs (P6, P8, P12, P17, P19, P26, P29, P30) hängen vom Helper ab (Roadmap-Zeilen 94 und 89); ein verspäteter Helper blockiert die Welle.

## Trace-Anker

spec-id: SPEC-rebaseline-helper-2026-11-15

Verweise: Entscheidung E-10, Roadmap `docs/plans/2026-11-15-master-roadmap.md` P4 / PR 1.3, Issues #1237, #1115.
