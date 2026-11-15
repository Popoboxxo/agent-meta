# Rebaseline-Helper — Spec
> Status: DRAFT (noch nicht freigegeben; Freigabe laut Entscheidung E-10 durch den Nutzer steht aus)
> Datum: 2026-11-15 | Entscheidung: E-10 | Roadmap: `docs/plans/2026-11-15-master-roadmap.md` P4 / PR 1.3 | Issues: #1237, #1115 (Duplikat-Teil)
> Klasse: M (siehe Abschnitt Klassifikation)

## Klassifikation

- Klasse **M**: reines Tooling, 1 neues lib-Modul, 1 dünner Entrypoint, 1 Testdatei, 1 Doku-Eintrag; kein Template-Edit, kein Render-Effekt, keine Rebaseline durch den Helper-PR selbst (Roadmap P4: „keiner (Tooling)“).
- Kein L: kein neues öffentliches Config-Schema, kein neuer Admin-Schreibpfad.
- Python 3.9-kompatibel (`typing.List`/`Optional`, kein `X | Y`, kein `match`), nur Stdlib (PyYAML-Ausnahme nur, wenn ein bestehendes Modul sie schon nutzt), provider-agnostisch.

## Entscheidungen

Nutzerentscheidungen zu den Fragen der Vorversion (Status der Spec bleibt DRAFT):

1. Befehlsform: eigenes `scripts/rebaseline.py` plus `scripts/lib/rebaseline.py`; KEIN `sync.py`-Flag.
2. Reason-Log: `.meta-config/rebaseline-log.jsonl` (getrackt, nicht unter `tests/fixtures/`).
3. `_FIXTURE_TREES`-Zeile wird automatisch zeilengenau gepatcht und steht in der Gate-Allowlist.
4. `topology-golden`-a2a-Fixtures werden per Render aktualisiert (Aktion `auto`); `schema-property-paths.json` bleibt `report-only`.
5. `--base` Default `origin/main`; ohne Remote Fallback auf lokales `main` mit Warnung.
6. Preflight: nur die Rebaseline-Artefakte müssen sauber sein; Quell-Änderungen dürfen uncommittet sein.
7. Reihenfolge: Implementierung des Helpers erst NACH P3 (#1246, Determinismus); Roadmap-Reihenfolge P3 -> P4.

## Problem

- Jede Template-/Render-Änderung braucht heute eine manuelle Rebaseline aus bis zu 9 Pin-Klassen (Tabelle in „Ist-Zustand“). Die Reihenfolge steht nirgends als Mechanismus, nur als Prozess-Docstring (`tests/test_ac01_render_identity.py:20-23`) und als Task-Prosa in Plänen.
- Vergessene Fixtures sind der häufigste CI-Rot-Grund: `compact-golden/agents-managed.md`, `topology-golden/schema-property-paths.json`, Kontext-Ceilings `_IST_FULL`/`_IST_COMPACT`, AC-T4-Digests. Bei #1115 wurde dies zweimal erst in CI bemerkt (`release-checklist`, `test-environments`).
- `sync.py` ohne `--config` löst Config per `Path.cwd()` auf (`scripts/lib/cli_commands.py:673-698`); im Worktree-Betrieb läuft es dadurch im falschen Checkout.
- Es gibt kein Diff-Gate: `--write` (`tests/test_ac01_render_identity.py:1513-1517`) schreibt den gesamten Manifest-Stand; ob nur erwartete Einträge driften, prüft der Mensch per Hand-Diff (die Logs in der Testdatei dokumentieren das Verfahren „per entry statt `--write`“ an dutzenden Stellen, z. B. `:274`, `:444`, `:483`).
- Es gibt keinen Vorab-Report, welche Pins/Goldens eine Änderung betrifft.

## Ziel

- EIN Befehl führt alle Rebaseline-Schritte in fester Reihenfolge aus (Issue #1237 Empfehlung 1), erzwingt ein Diff-Gate (nur erwartete Dateien/Schlüssel dürfen sich ändern) und berichtet vorab und nachher, welche Pins/Goldens betroffen sind.
- Pflicht-Grund (`--reason`) wird in ein Log geschrieben (Issue #1237: „mandatory reason written to a log file“).
- Ceiling-Re-Pin (#1115): der Helper misst mit `measure_artifacts` und druckt den fertigen Re-Pin-Block für `_IST_FULL`/`_IST_COMPACT`; Toleranz-Konstanten bleiben unberührt (#1115 AC 3).
- `--check-only` (= `--dry-run`): nur messen und berichten, keine Schreibzugriffe; Exit 1 bei Drift.
- Idempotent: zweiter Lauf ohne Quelländerung = 0 Änderungen, Exit 0, kein Log-Eintrag.
- Root-sicher: Repo-Root kommt aus dem Ort des Helpers, nie aus `cwd`; jeder `sync.py`-Aufruf bekommt explizites `--config`.

## Nicht-Ziele

- Keine Render-Determinismus-Arbeit (Issue #1237 Empfehlung 2, Umgebungs-/Datums-/Pfadwerte aus gehashten Artefakten): Roadmap P3 (#1246) davor; hier nur Abgrenzung.
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
| AC | `tests/fixtures/ac01-baseline/hashes.json` (Provider-Matrix-Hashes) | `tests/test_ac01_render_identity.py:1054` (`_MANIFEST`), `:1141` (`render_matrix_hashes`), `:1168` (`diff_against_manifest`), `:1513-1517` (`--write`) | ja, `--write` (schreibt voll, kein Gate) |
| AC-T4 | Fixture-Baum-Digests `_FIXTURE_TREES` | `tests/test_opencode_v2_surface.py:5511-5515`, Digest-Funktion `:5518`, Test `:5530-5549` | nein (Literal von Hand) |
| SG | `tests/fixtures/slimming-golden/<rolle>.md` | `tests/test_template_slimming_equivalence.py:269` (`_GOLDEN_DIR`), Rollenzahl `:5` | nein (Hand-Patch) |
| CG | `tests/fixtures/compact-golden/{orchestrator,agents-managed}.md` | `tests/test_orchestrator_compact_sections.py:78`, `tests/test_gate_card_compact.py:93` | nein (Hand-Patch) |
| TG | `tests/fixtures/topology-golden/*` inkl. `schema-property-paths.json` | `tests/test_ac01_render_identity.py:1287-1289`, `tests/test_orchestrator_topology_docs.py:1274` | a2a-Fixtures ja (Render, `auto`), `schema-property-paths.json` nein (`report-only`) |
| H1 | `.meta-config/generated-file-hashes.json` | `scripts/lib/generated_file_drift.py:45`, `_save_hashes` `:68` | ja, durch `sync.py` |
| H2 | `.meta-config/context-hashes.json` | `scripts/lib/context.py:43`, `:69` | ja, durch `sync.py` |
| SA | `standalone/agents/*.md`, `standalone/README.md` | `scripts/lib/standalone.py:534`, `:560`; Drift `:575-582`; CLI `scripts/lib/cli_commands.py:590-611` (`--render-standalone [--check] [--dry-run]`) | ja |
| CE | Ceilings `_IST_FULL` / `_IST_COMPACT` | `tests/test_context_budgets.py:300`, `:583`, `_ceiling` `:310`; Messung `scripts/lib/context_report.py:130` (`measure_artifacts`); CLI `scripts/measure_context.py:257` | nur Messung |

Weitere Belege:

- Reihenfolge der Schritte laut bestehendem Plan: `docs/plans/2026-11-15-git-trailer-contract-plan.md:188-205` (Task 9: Golden-Patch → `--write` mit Diff-Gate → `--render-standalone` → `sync.py` → Ceilings → Commit).
- Bei der Standalone-/Fixture-Auflösung gilt: Config-Auto-Detect über `cwd` und Root-Ableitung aus `--config` (`scripts/lib/cli_commands.py:673-698`); der Setup-Wizard startet bei fehlender Config (`:680-690`) und ist im Helper-Betrieb unerwünscht.
- Der Tmp-Sink-Stage speist das Render-Ergebnis mit Umgebungswerten (`scripts/lib/sync_pipeline.py:236-291`); die Matrix normalisiert Datum und Modellzeile (`tests/test_ac01_render_identity.py:1118`, `:1141-1166`). Pseudo-Drift ist daher Sache von P3, nicht des Helpers.
- Der AC-T4-Digest läuft über `rglob("*")` des gesamten Fixture-Verzeichnisses (`tests/test_opencode_v2_surface.py:5518-5528`): jede zusätzliche Datei unter `tests/fixtures/ac01-baseline/` ändert den Digest. Das Rebaseline-Log darf deshalb NICHT dort liegen.
- Issue-Daten: `generated-file-hashes.json` in 95 Commits/90 Tagen, `ac01-baseline/hashes.json` 62, `compact-golden` 17 (#1237).
- Dokumentationsort für die Verfahrensregel: Skill `conventions` (`.claude/skills/conventions/SKILL.md`, generiert; Quelle im Skills-Template-Bestand) — #1115 AC 2 verlangt einen Verweis dort.

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
- `--check-only`/`--dry-run`: Synonyme; kein Schreibzugriff auf das Repo (Scratch-Verzeichnis unter `tempfile` ist erlaubt).
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

### C4 — Report-Format (stdout, Deutsch/Englisch-neutral, ASCII)

```
REBASELINE  root=<ROOT>  base=<REF>  mode=<write|check-only>
PRE   <Klasse>  <Artefakt>  <n> betroffen|ok|n/a   (je Pin-Klasse eine Zeile)
STEP  1 ac01        wrote 4 of 1101 hashes  gate=ok
STEP  2 standalone  wrote 1 file            gate=ok
STEP  3 sync        updated generated-file-hashes.json (9 keys), context-hashes.json (0)
STEP  4 digests     _FIXTURE_TREES: slimming-golden OLD->NEW (patched) | unchanged
STEP  5 ceilings    CE: RE-PIN-BLOCK follows (not applied)
POST  <Klasse>  <Artefakt>  ok|OFFEN
RESULT  changed=<n> files  gate=ok  verify=ok|failed|skipped  log=<Pfad>
```

- `--json` liefert dieselben Felder als ein JSON-Objekt (`pre`, `steps`, `post`, `result`).

### C5 — Pin-Registry (Daten, nicht Code-Verzweigung)

- Modul-Konstante `PINS: Tuple[PinSpec, ...]`, je Eintrag: `klass`, `paths` (Globs), `detector` (`pytest`-Knoten-IDs oder interne Funktion), `writable` (`auto|report-only`). Neue Pin-Klasse = ein Registry-Eintrag, kein neuer Ablaufcode.
- Detektoren für „vorab/nachher“: AC über `render_matrix_hashes` + `diff_against_manifest` (importiert aus `tests/test_ac01_render_identity.py` per `importlib`, nicht kopiert), AC-T4 über `_fixture_tree_sha256` vs. `_FIXTURE_TREES`, H1/SA über `sync.py --dry-run --config` bzw. `--render-standalone --check`, SG/CG/TG/CE über gezielte `pytest -q -x`-Aufrufe auf die zuständigen Testdateien (Liste in der Registry).

### C6 — Rebaseline-Log

- Datei: `.meta-config/rebaseline-log.jsonl` (getrackt, append-only, eine JSON-Zeile je Schreiblauf mit Änderungen): `{ts, reason, base, head, steps, changed_files, changed_keys, gate, verify}`.
- Nicht im Fixture-Baum (AC-T4-Digest, siehe Ist-Zustand). Nicht in `tests/fixtures/ac01-baseline/`.
- Ergänzt, ersetzt nicht das menschenlesbare Log im Docstring von `tests/test_ac01_render_identity.py`; der Helper schreibt dort nichts.

## Datenfluss

Ablauf und Reihenfolge:

Schreibmodus (feste Reihenfolge; jeder Schritt hat ein eigenes Gate):

0. Preflight: `--reason` gültig; `ROOT`/Config gelöst; `git status --porcelain` enthält keine Änderungen an Rebaseline-Artefakten (Entscheidung 6; Quell-Änderungen an Templates/Rules/Config dürfen uncommittet sein, sie definieren den Scope); Snapshot der zu schreibenden Artefakte in ein Scratch-Verzeichnis (für Rollback).
1. PRE-Report: alle Pin-Detektoren laufen auf dem Ausgangsstand (ohne Schreiben); der Report nennt je Klasse „betroffen“ oder „ok“.
2. `ac01`: Matrix-Render in Scratch (`render_matrix_hashes`), Vergleich mit Manifest; Schreiben nur der abweichenden Schlüssel in `tests/fixtures/ac01-baseline/hashes.json` (Format `json.dumps(indent=1, sort_keys=True) + "\n"` wie `:1513-1517`). Gate pro Schlüssel.
3. `standalone`: `scripts/sync.py --render-standalone --config <CFG>`; Gate auf `standalone/**`.
4. `sync`: `scripts/sync.py --config <CFG>`; erzeugt `.meta-config/generated-file-hashes.json`, `context-hashes.json` und weitere abhängige Dateien; Gate auf die Menge geänderter getrackter Dateien.
5. `topology`: a2a-Fixtures in `tests/fixtures/topology-golden/` per Render aktualisieren (`render_topology_rule`, `tests/test_ac01_render_identity.py:1335`); Gate auf genau diese Dateien (Entscheidung 4).
6. `digests`: Fixture-Baum-Digests neu berechnen; weicht ein Digest von `_FIXTURE_TREES` ab UND hat sich der zugehörige Baum in diesem Lauf oder im Arbeitsbaum gegenüber `--base` geändert, wird das Literal in `tests/test_opencode_v2_surface.py` automatisch zeilengenau ersetzt (Entscheidung 3; Gate: nur diese Zeile). Ändert sich ein Baum ohne erwarteten Pfad → Gate-Verletzung.
7. `ceilings`: `measure_artifacts` (wie `scripts/measure_context.py`) auf dem frisch gesyncten Stand; Vergleich mit `_ceiling(_IST_FULL)`/`_ceiling(_IST_COMPACT)`; nur bei Überschreitung wird der exakte Re-Pin-Block (Provider/Artefakt, alter Ist, gemessener Ist) gedruckt. Keine Dateiänderung.
8. Zweiter Check-only-Durchlauf aller Schritte (Idempotenz-Beweis); Rest-Drift → Exit 4 mit Liste.
9. Verifikation: gezielte `pytest -q`-Aufrufe der Pin-Testdateien aus der Registry (kein Voll-Lauf); rot → Exit 5.
10. Log-Eintrag (C6) nur wenn `changed_files` nicht leer.

Check-only: Schritte 1 bis 7 rechnen in Scratch bzw. mit `--dry-run`; Exit 1 bei jeder Drift, sonst 0. Schritt 10 entfällt.

Rollback: bei Exit 3/4 stellt der Helper aus dem Preflight-Snapshot alle von ihm berührten Dateien wieder her (kein `git checkout`, kein `git stash`).

## Diff-Gate

- Definition: Nach jedem Schreibschritt wird die Menge geänderter getrackter Dateien (`git diff --name-only` gegen den Preflight-Stand) und, für JSON-Hash-Dateien, die Menge geänderter Schlüssel gebildet. Jede Datei/jeder Schlüssel außerhalb der Erwartungsmenge → Exit 3, Rollback, Ausgabe der Differenz.
- Erwartungsmenge = Vereinigung aus:
  1. Klassen-Allowlist (Daten im Modul): `tests/fixtures/ac01-baseline/hashes.json`, `.meta-config/generated-file-hashes.json`, `.meta-config/context-hashes.json`, `standalone/**`, `tests/test_opencode_v2_surface.py` (nur die `_FIXTURE_TREES`-Zeilen), `tests/fixtures/topology-golden/a2a-delegation-gates.role-*.md`, `.meta-config/rebaseline-log.jsonl`.
  2. Abgeleitete Schlüsselerwartung: aus `git diff --name-only <base>...HEAD` plus Arbeitsbaum werden die geänderten Quellen (`agents/**`, `rules/**`, `hooks/**`, `templates/**`, `config/**`, `scripts/lib/**`) auf Rollen-/Rule-/Hook-Stems abgebildet; erlaubt sind `hashes.json`-Schlüssel, deren relpath einen dieser Stems enthält (Muster `<Provider>/**/<stem>*`). Quellen ohne Stem-Abbildung (z. B. `config/**`, `scripts/lib/**`) erlauben KEINE Schlüssel automatisch → der Aufrufer muss `--expect-key` angeben (fail-closed).
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
5. Zweiter Schreiblauf direkt danach → Exit 0, 0 Dateiänderungen, kein neuer Log-Eintrag (Idempotenz).
6. Unerwartete Datei- oder Schlüsseländerung (Test mit künstlich zusätzlicher Drift) → Exit 3, alle berührten Dateien byte-identisch zurückgesetzt.
7. Aufruf aus fremdem `cwd` (z. B. Hauptcheckout bei Worktree-Helper) wirkt ausschließlich auf den Root des Helper-Orts; jeder `sync.py`-Subprozess enthält `--config <ROOT>/.meta-config/project.yaml` und `cwd=<ROOT>` (Test mit gemocktem Subprozess-Runner).
8. Fehlt `.meta-config/project.yaml` → Exit 2, kein Wizard-Start.
9. Die Schrittreihenfolge ist exakt `ac01, standalone, sync, topology, digests, ceilings` (Test über aufgezeichnete Aufrufreihenfolge).
10. Preflight bricht mit Exit 2 ab, wenn Rebaseline-Artefakte im Arbeitsbaum bereits verändert sind; uncommittete Quell-Änderungen (Templates/Rules/Config) blockieren NICHT.
11. Das Log `.meta-config/rebaseline-log.jsonl` erhält pro ändernden Lauf genau eine valide JSON-Zeile mit `reason`; die AC-T4-Digests ändern sich durch den Log-Eintrag nicht (Datei liegt außerhalb `tests/fixtures/`).
12. Ceiling-Report: bei künstlich überschrittenem Ist druckt der Helper den Re-Pin-Block mit Provider, Artefakt, altem und gemessenem Wert; `TOLERANCE_MAX_BYTES`, `TOLERANCE_MIN_BYTES`, `TOLERANCE_RATIO` und alle Pins sind danach unverändert (Dateihash-Test).
13. Nach erfolgreichem Lauf sind die gezielten Pin-Tests (`test_ac01_render_identity`, `test_opencode_v2_surface::test_ac_t4_fixtures_unchanged`, `test_template_slimming_equivalence`, `test_gate_card_compact`, `test_orchestrator_compact_sections`, `test_orchestrator_topology_docs`, `test_context_budgets`) grün oder als `OFFEN` mit Aktion genannt; rote Verifikation → Exit 5.
14. `--json` liefert valides JSON mit den Feldern `pre`, `steps`, `post`, `result`.
15. Bei Subprozess-Fehler (simuliert) → Exit 4 und Rollback.
16. `scripts/lib/rebaseline.py` ≤ 600 Zeilen, nur Stdlib, kein `print()`, kein Provider-Literal (`tests/test_provider_agnostic_dispatch.py`); Python 3.9-kompatibel.
17. Der `conventions`-Skill (Quelle) und `howto/` enthalten einen Verweis auf den Befehl; `docs/` nennt Flags und Exit-Codes (#1115 AC 2).
18. `--base` ohne Remote `origin`: Fallback auf lokales `main`, Warnung im Report, Exit-Code unverändert (Test mit gemocktem Git-Runner).
19. `topology`-Schritt aktualisiert die a2a-Fixtures per Render; Drift dort wird vorab als `betroffen` gemeldet und danach als `ok`; `schema-property-paths.json` bleibt `report-only`.
20. Die `_FIXTURE_TREES`-Zeile wird zeilengenau gepatcht (alle anderen Zeilen der Datei byte-identisch); der Eintrag ist in der Gate-Allowlist.

## Offene Fragen

Keine; die sieben Fragen der Vorversion sind im Abschnitt Entscheidungen beantwortet.

## Risiken

- Der Matrix-Render ist langsam (9 Provider-Projekte); der Check-only-Modus und der Idempotenz-Durchlauf verdoppeln die Laufzeit. Gegenmaßnahme: Scratch-Render einmal, Ergebnis für Schritt 2 und 7 wiederverwenden.
- Stem-Abbildung für die abgeleitete Schlüsselerwartung kann zu eng sein (Config-/Lib-Änderungen) → fail-closed, Aufrufer gibt `--expect-key`; ein zu weites Gate würde Fehler absorbieren (Log-Historie zeigt dieses Risiko: „absorbed silently“).
- `importlib`-Import von `tests/test_ac01_render_identity.py` koppelt den Helper an die Testdatei (Modul-Level-Seiteneffekte, pytest-Fixtures). Alternative: Funktionen nach `scripts/lib/` extrahieren (größere Änderung, eigener Folge-Schritt).
- Rollback-Snapshot deckt nur vom Helper berührte Pfade; parallel editierende Prozesse sind nicht abgesichert.
- Umgebungsabhängigkeit des Renders (Tmp-Sink, Datum) kann den Idempotenzlauf stören, solange P3 offen ist (`scripts/lib/sync_pipeline.py:236-291`).
- Hand-gepflegte Goldens bleiben ein menschlicher Schritt; der Helper reduziert Vergessen, eliminiert die Arbeit nicht.
- Reihenfolge: Die Implementierung startet erst nach P3 (#1246); bis dahin ist nur Spec/Plan DRAFT (Entscheidung 7). Der Idempotenzlauf ist vorher nicht belastbar.
- Roadmap-Folge: nachfolgende Rebaseline-PRs (P6, P8, P12, P17, P19, P26, P29, P30) hängen vom Helper ab (Roadmap-Zeilen 94 und 89); ein verspäteter Helper blockiert die Welle.

## Trace-Anker

spec-id: SPEC-rebaseline-helper-2026-11-15

Verweise: Entscheidung E-10, Roadmap `docs/plans/2026-11-15-master-roadmap.md` P4 / PR 1.3, Issues #1237, #1115.
