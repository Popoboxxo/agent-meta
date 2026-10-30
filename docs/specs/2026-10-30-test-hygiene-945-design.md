# Test-Hygiene #945 (Wave 4) — Spec

> spec-id: SPEC-test-hygiene-945
> Status: Entwurf
> Datum: 2026-10-30 (Rev. 2)
> Issue: #945
> Revision: 2
> Grundlage: Systemdesign des `concept-architect` vom 2026-10-30, hier als `## Systemdesign` konserviert (es existiert keine separate Designdatei)
> Verifizierter Stand: `main` @ `3c440c33`; Rev. 2 gegen den Arbeitsstand vom 2026-10-30 nachgeprüft
> Review-Historie: Rev. 1 → `CHANGES_REQUESTED` (B1–B7, A1–A12); alle Punkte in Rev. 2 eingearbeitet (siehe Revision-Log)

## Problem / Ziel / Nicht-Ziele

### Problem

Issue #945 wurde in Wave 2 nur teilweise geschlossen. Der `CHANGELOG.md`-Eintrag
`[2.0.0-beta.2] - 2026-10-20` sagt selbst „CI robustness (#945, **partial**)".
Übrig bleiben vier offene bzw. unbewiesene Akzeptanzkriterien und zwei
Strukturmängel, die sie verdecken:

- **Hook-Tests schreiben potenziell in den Checkout.** `tests/test_orchestrator_guard_hook.py`
  isoliert sich (modulglobales `tempfile.mkdtemp`-Verzeichnis), und fünf weitere
  Hook-Module sind bereits `tmp`-basiert (`tests/test_dod_push_check_hook.py`,
  `tests/test_artifact_freshness_hook.py`, `tests/test_pre_release_check_hook.py`,
  `tests/test_auto_github_release_hook.py`, `tests/test_release_gate_checksums.py`).
  **Nicht** isoliert sind zwei Stellen: `tests/test_hook_common_lib.py`
  (`_call` setzt weder `cwd=` noch `timeout=`, sieben weitere Aufrufe im Modul
  ebenso) und die Default-Wurzel von `tests/test_repo_containment_hook.py::_run_hook`
  (`cwd=_REPO_ROOT`). `.claude/hooks/.guard-audit.log` ist gitignored
  (`.gitignore` → `.guard-audit.log`), fällt also niemandem auf.
- **Ungebremste Subprozesse.** `tests/timeouts.py` existiert mit
  `SYNC_TIMEOUT`/`SYNC_VALIDATE_TIMEOUT`/`SCRIPT_TIMEOUT`, aber die
  Hook-Module und der überwiegende Teil der übrigen Module setzt weiterhin kein
  `timeout=`. Rev. 2 hat das gemessen (siehe „Messung Rev. 2"): **201
  Subprozess-Aufrufe in 73 Dateien** unter `tests/**/*.py`, davon 72 in den
  neun P1-Modulen. Ein hängendes `bash`-Kind blockiert den Runner bis zum
  Job-Timeout.
- **Artefakt-Tests sind in der CI vermutlich übersprungen** — sie brauchen einen
  gesyncten Baum, und keiner der beiden Workflows synct vor `pytest` in einem
  `test`-Bein.
- **Playwright hat keinen CI-Pfad.** `tests/browser` (11 Module) wird lokal
  gefahren und in der CI nie ausgeführt, ohne dokumentierte Begründung.
- **Kein Regressionsschutz.** Nach dem Fix kann dieselbe Lücke (fehlendes
  `timeout=`, fehlende Isolation) unbemerkt wieder eingebaut werden; es gibt
  keinen Check, der „jeder Aufruf hat `timeout=`" prüft.

### Ziel

Wave 4 schließt #945 vollständig: AC1, AC3, AC4 und AC6 werden umgesetzt, AC5
wird als bewusste Ablehnung dokumentiert; AC2 bleibt unverändert (bereits
erfüllt) und wird nur gegen Regression abgesichert. Der Fix ist in phasenweise
mergebare PRs zerlegt, damit jeder Schritt einzeln revertierbar ist und die
Isolation nicht mit der repo-weiten Timeout-Adoption kollidiert. Neu ist ein
AST-basierter Konsistenz-Check, der `timeout=` als Pflicht macht statt als
Konvention.

**Scope:** `tests/`, `.github/workflows/`, `scripts/lib/consistency/`,
`scripts/consistency-check.py`, `.meta-config/`, `CHANGELOG.md`, `tests/README.md`.

### Nicht-Ziele

- Kein `pytest-timeout`, kein `pytest-rerunfailures`, keine neue Test-Dependency
  außer dem Browser-Extra (`tests/requirements-browser.txt`). Der
  pytest-Stack der CI kommt weiterhin aus `tests/requirements.txt`.
- Keine neue `pytest.ini` / `pyproject.toml` / `setup.cfg`; kein globaler
  Timeout über Konfigurationsdatei.
- Keine Laufzeit-Optimierung, kein Shard-Rebalancing, keine
  `.test_durations`/`--splitting-algorithm least_duration` (im Workflow-Header
  bereits als Follow-up deklariert).
- Keine Reparatur des `compat-311`-Listen-Duplikats.
- Kein Eingriff in die `-n auto`-Politik, die 15/17-Invariante oder die sechs
  Listen — außer der additiven `ARTIFACT_TESTS`-Liste.
- Kein Aufräumen der ~246 Testzeilen im lokalen `.claude/hooks/.guard-audit.log`
  (Audit-Trail, Nutzerentscheidung in
  `docs/plans/2026-10-07-bugfix-batch-2.md`).
- Kein Umbau von `tests/browser/conftest.py` über `timeout=`/Allowlist hinaus.
- **Keine Vereinheitlichung bestehender Timeout-Literale** (30/120/180/300/600)
  auf die Konstanten aus `tests/timeouts.py`. Bestandswerte bleiben unverändert
  (Regel in IC-2); eine Angleichung wäre ein eigener Task.
- Keine Per-Test-Zeitbudgets, keine Performance-Assertions, keine
  provider-spezifischen Verzweigungen.
- Keine Korrektur der historischen Release-Notiz „`pytest -n auto`" in
  `CHANGELOG.md` (`[2.0.0-beta.2]`) — Release-Text bleibt historisch.

## Stand

Verifiziert am 2026-10-30 gegen `main` `3c440c33`, Nachprüfung Rev. 2 am selben
Tag. Jede Zeile nennt die Fundstelle als `datei:symbol`; Zeilennummern nur dort,
wo sie aus einer stabilen, nachgeprüften Fundstelle stammen.

### Messung Rev. 2 — Subprozess-Aufrufe unter `tests/**/*.py`

Methode (read-only, in Rev. 2 tatsächlich ausgeführt): Grep auf
`subprocess\.(run|call|check_output|check_call|Popen)\s*\(`, partitioniert über
Dateinamen-Globs (`test_[a-c]*` … `test_[t-z]*` plus die Hilfsmodule), damit die
Trefferliste nicht abschneidet; danach Abgleich gegen
`^\s*(import subprocess|from subprocess import)`.

| Größe | Wert |
|---|---|
| Dateien mit `import subprocess` | 77 |
| davon ohne echten Aufruf (nur `mock.patch`/`TimeoutExpired`): `test_doctor_fixtures.py`, `test_doctor_runner.py`, `test_se_export.py`, `test_context_compact_mode.py` | 4 |
| **Dateien mit mindestens einem Aufruf** | **73** |
| **Aufrufstellen insgesamt** | **201** |
| davon in den neun P1-Modulen | 72 |
| davon außerhalb P1 (P2-Scope) | 129 in 64 Dateien |
| `Popen(`-Aufrufstellen | 2 (`tests/active_set_render.py::sync_configs_parallel`, `tests/browser/conftest.py::admin_server`) |

Die Zählung ist grep-basiert (Kommentare/Strings sind nicht ausgeschlossen); die
autoritative Zahl liefert `check_subprocess_timeout` (AST) in P3. Die
Dateimengen in P2a/P2b sind aus dieser Messung abgeleitet, nicht geschätzt.

### AC2 — bereits erfüllt

| Workflow | Job | `timeout-minutes` |
|---|---|---|
| `.github/workflows/orchestration-test.yml` | `test` | 30 |
| `.github/workflows/orchestration-test.yml` | `subprocess-shard` | 30 |
| `.github/workflows/orchestration-test.yml` | `compat-311` | 30 |
| `.github/workflows/validate.yml` | `scenarios` | 30 |
| `.github/workflows/validate.yml` | `validate` | 10 |

Es gibt genau diese zwei Workflow-Dateien (`.github/workflows/` enthält nur
`orchestration-test.yml` und `validate.yml`). Neue Jobs in P4 und P6 müssen
`timeout-minutes` mitbringen, sonst bricht AC2.

### AC1 — erfüllt bis auf zwei Stellen

- `tests/test_orchestrator_guard_hook.py:_PROJECT_ROOT` legt ein
  `tempfile.mkdtemp`-Projekt an, kopiert `.meta-config/project.yaml`, erzeugt
  `.claude/hooks/` und räumt per `atexit` auf; `_run_hook` und
  `_bash_payload` verwenden dieses Verzeichnis als `cwd`.
- `tests/test_orchestrator_guard_hook.py::test_strict_cases_never_write_the_repo_audit_log`
  ist der Beweistest: Byte-Vergleich der echten `.guard-audit.log` vor/nach
  einem Hook-Lauf (`read_bytes() if exists() else None`).
- Fünf Hook-Module sind bereits `tmp`-basiert (`test_dod_push_check_hook.py`,
  `test_artifact_freshness_hook.py`, `test_pre_release_check_hook.py`,
  `test_auto_github_release_hook.py`, `test_release_gate_checksums.py`);
  `test_graphify_guard_hooks.py` nutzt `tmp_path` für seine drei Runner-Aufrufe.
- **Nicht isoliert:** `tests/test_hook_common_lib.py` — `_call` setzt kein
  `cwd=`; sieben weitere Aufrufe im Modul (u. a.
  `test_hook_json_get_lone_surrogate_is_not_dropped`,
  `test_hook_json_get_invalid_utf8_input_is_not_dropped`,
  `_scan`, `test_shell_scan_py_emits_compilable_source`, `_resolve`,
  `test_shell_resolver_py_emits_compilable_source`,
  `test_command_start_skips_pure_assignment_statements`) ebenso wenig.
- **Nicht isoliert:** `tests/test_repo_containment_hook.py::_run_hook` defaultet
  auf `process_cwd=_REPO_ROOT`; zusätzlich neun Inline-Aufrufe mit
  `cwd=str(_REPO_ROOT)` (u. a. `test_payload_cwd_cannot_redefine_the_deployed_jail_root`,
  `test_claude_project_dir_is_a_fixed_anchor_from_the_source_tree`,
  `test_fixed_anchor_is_provider_neutral`,
  `test_write_inside_the_fixed_anchor_is_allowed`,
  `test_f5_unresolvable_fixed_root_fails_closed`, beide
  `test_missing_pyyaml_*`-Tests).
- Kein CI-Schritt prüft, dass der Audit-Log unverändert bleibt.

### AC3 — offen

- `tests/timeouts.py` existiert und exportiert `SYNC_TIMEOUT` (180),
  `SYNC_VALIDATE_TIMEOUT` (180, Fallback `SYNC_TIMEOUT`) und `SCRIPT_TIMEOUT`
  (60); `_env_seconds` fällt bei nicht-ganzzahligen, leeren oder nicht-positiven
  Werten auf den Default zurück und wirft nie beim Import.
- Importpfad ist `from tests.timeouts import ...` (`tests/__init__.py` existiert);
  aktuell nutzen ihn `tests/test_agent_eval_framework.py`,
  `tests/test_sharkord_service_name_migration.py`,
  `tests/test_knowledge_engine.py`,
  `tests/test_platform_defaults_resolved_file.py`,
  `tests/test_antigravity_hooks_registration.py`.
- Hook-Slice: 72 Aufrufe in den neun P1-Modulen (Rev. 1 nannte 69 Treffer in
  zehn Modulen — die zehn enthielten zwei Module außerhalb des P1-Scope:
  `tests/test_antigravity_hooks_registration.py`,
  `tests/test_hook_registration_invariant.py`). Gebremst sind nur 4 Aufrufe (die
  `SCRIPT_TIMEOUT`-Stellen in `test_antigravity_hooks_registration.py`).
- Repo-weit: 201 Aufrufe in 73 Dateien (Messung Rev. 2, siehe oben).
  `tests/test_secrets_and_isolation.py` ist der einzige geprüfte Kandidat, der
  bereits an allen vier Aufrufen `timeout=` setzt.
- Bestandsliterale > 10 (grep-Stichprobe, nicht vollständig — die vollständige
  Liste liefert P3): 30 (`tests/test_admin_server.py`, `admin-server --help`),
  120 (`tests/test_agent_eval_framework.py`, Katalog-Generator), 180
  (`tests/test_migration_paths.py`, 300 (`tests/test_doctor_cli.py::_cli`),
  600 (`tests/test_context_report.py::_run`) — alle `sync.py`-Treiber. Behandlung:
  IC-2, „Bestandswerte".
- Sechs Modul-lokale `RUN_TIMEOUT = 900`-Definitionen existieren
  (`tests/test_meta_optimizer_{runner,applier,credentials,inactive_scope,refill,fanout}.py`).

### AC4 — unverifiziert

- `orchestration-test.yml` → Step `Validate agent templates`
  (`if: matrix.shard == 1`) läuft **nach** der `pytest`-Remainder-Stufe.
- `validate.yml` → `Generate sync output` (`python scripts/sync.py`) →
  `Check generated files are committed (drift gate)` → `Validate sync output`.
- Ob die Artefakt-Tests dadurch tatsächlich **nicht** mehr überspringen, ist
  nicht belegt: es gibt keinen Lauf gegen einen ungesyncten Checkout mit
  `-rs`. Die Skip-Gates existieren nachweislich, u. a.
  `tests/test_opencode_agents.py:_skip_unless_generated` (Aufruf in sechs Tests),
  `tests/test_agent_eval_framework.py` (`pytest.skip("rendered orchestrator missing (run sync.py)")`),
  `tests/test_reference_standards_documented.py`
  (`"no generated conventions skill copies (unsynced checkout)"`),
  `tests/test_legacy_registries_removed.py`
  (`"generated roots absent (gitignored); run scripts/sync.py"`),
  `tests/test_mcp_role_tools.py` (`"e2e-tester not generated in this project"` —
  dieser Text matcht **keinen** der vier in Rev. 1 genannten Suchstrings, siehe
  IC-7).

### AC5 — unverifiziert

- `validate.yml` → Job `compat-311` ist ein gezielter 9-Datei-Job (`TOML
  boundary + code hygiene`, Python 3.11 fest); es gibt keine
  Szenario-Matrix über mehrere Python-Versionen.
- Der Job `scenarios` pinnt Python 3.11 (`setup-python` → `'3.11'`) und shardet
  nur (4 Shards), nicht nach Version.
- Es gibt keine dokumentierte Entscheidung dazu. Korrektur zu Rev. 1:
  `validate.yml` hat **keinen** erläuternden Header-Kommentarblock über
  Jobaufteilung und Timeouts — dort stehen nur zwei Inline-Kommentare (über
  `concurrency.group` zur Event-Scoping-Regel und über
  `jobs.scenarios.timeout-minutes` zu „79 Szenarien / 4 Shards"). Der
  ausführliche Erläuterungsblock zur Jobpartition steht in
  `orchestration-test.yml` (Zeilen 3–59). IC-12 legt deshalb einen **neuen**
  Kommentarblock in `validate.yml` an.

### AC6 — nicht erfüllt

- Kein Workflow enthält `playwright` (beide Workflow-Dateien geprüft).
- `tests/requirements.txt` enthält `pytest`, `pyyaml`, `questionary`, `tomli`
  (nur <3.11), `jsonschema`, `pytest-xdist`, `pytest-split` — kein Playwright.
  Wichtig für IC-10: `pytest` **und** `pytest-xdist` (für `-n 0`) kommen aus
  dieser Datei, nicht aus dem Browser-Extra.
- `tests/browser/` hat 11 Testmodule; jedes beginnt mit
  `pytest.importorskip("playwright")` (bzw. einfachen Quotes), `tests/browser/conftest.py`
  setzt zusätzlich `has_playwright` und startet den `admin-server` auf Port 7421.
  Ohne Playwright wird also still übersprungen, nie ausgeführt.

### Changelog-Status

`CHANGELOG.md` hat einen gefüllten `## [Unreleased]`-Abschnitt (Added/Fixed aus
#1006, #1037 u. a.), aber **keinen** #945-Rest-Eintrag. Der bestehende
#945-Eintrag steht in der abgeschlossenen Release-Sektion
`[2.0.0-beta.2] - 2026-10-20` und markiert sich selbst als „partial". Jede
Phase, die Dateien anlegt, schuldet einen `[Unreleased]`-Eintrag; P1 trägt den
Sammel-Eintrag „CI robustness (#945, residual)".

## Systemdesign

Quelle: Systemdesign `concept-architect`, 2026-10-30 (in diesem Dokument
vollständig konserviert, damit Plan und Review eine stabile Referenz haben),
Rev. 2 mit den Entscheidungen ADR-3 und der gemessenen Phasenzerlegung.

### Phasenzerlegung (Merge-Reihenfolge)

Größenklassen nach F7: **S** ≤ 2 Dateien, **M** 3–8, **L** 9–20, **XL** > 20.

| Phase | Inhalt | Größe | Dateien | Schließt | Abhängigkeit |
|---|---|---|---|---|---|
| **P1** | Timeout-Contract + Hook-Slice-Isolation | L | 14 | AC1 (lokal beweisbar), AC3 (Hook-Slice) | — |
| **P2a** | Timeout-Adoption, Sync-/CLI-Treiber + Optimizer-Familie | XL (32) | 32 | AC3 (Teil) | strikt nach P1 |
| **P2b** | Timeout-Adoption, Fixture-/Kontext-/Repo-Copy-Module | XL (31) | 31 | AC3 (Rest) | strikt nach P2a |
| **P3** | Vollständigkeits-Check (`subprocess-timeout-missing`) | M | 5 | AC3 (Beweis) | strikt nach P2b |
| **P4** | CI-Beweis + Artefakt-Job + Meta-Test | M | 3 | AC1 (CI), AC4 | **nach P1**; parallel zu P2a/P2b/P3/P5/P6 |
| **P5** | AC5-Entscheidung dokumentiert | S | 2 | AC5 | parallel (unabhängig) |
| **P6** | Playwright-CI-Pfad | M | 3 | AC6 | parallel (unabhängig) |

Merge-Reihenfolge: **P1 → P2a → P2b → P3 strikt sequenziell** (P2a/P2b teilen
die Konstanten-Tabelle, sind aber dateidisjunkt; P3 ist als ERROR nur bei null
Verstößen verteidigbar). **P5 und P6 sind unabhängig und jederzeit
parallelisierbar. P4 ist parallel zu P2a/P2b/P3/P5/P6, aber erst nach P1
mergebar** — der Digest-Schritt erwartet die Hook-Module aus P1 in der
Remainder-Menge; P4 vor P1 macht den Digest rot.

Beide P2-Hälften sind nach F7 XL (32 bzw. 31 Dateien). Das ist die direkte
Konsequenz der Messung: F7 kennt für > 20 nur XL, und die Adoption betrifft 64
Dateien. Eine weitere Aufteilung in vier PRs à ~16 Dateien (L) ist beim Plan
zulässig, ohne diese Spec zu ändern — die Dateilisten sind disjunkt und die
Mapping-Tabelle bleibt dieselbe.

### ADR-1 — Timeout-Mechanismus: Konstanten + explizite Adoption + AST-Check

- **Kontext:** AC3 verlangt `timeout=` an jedem `subprocess.run` in den Tests.
  Ein Hang-Guard muss einen blockierten Kindprozess töten, darf aber einen
  langsam-arbeitenden Test auf einem 2-Kern-Runner nicht rot machen.
- **Entscheidung:** zentrale Konstanten in `tests/timeouts.py`, explizite
  Adoption pro Aufrufstelle, Presence-Check per AST im
  `sync.py --validate`-Pfad.
- **Konsequenzen:** der Satz „Hang-Guard, keine Performance-Zusicherung" bleibt
  wörtlich wahr. Der Check prüft **nur die Anwesenheit** von `timeout=` (und
  dass der Wert nicht `None` ist), nicht die Richtigkeit des Werts — das ist
  bewusst und muss so dokumentiert bleiben.
- **Verworfen — `pytest-timeout`:** misst die Test-Wanduhr, tötet langsame, aber
  fortschreitende Tests auf 2-Kern-Runnern, kann das blockierte Kind nicht
  benennen, die `thread`-Methode kann ein blockierendes `waitpid` nicht
  unterbrechen, und es bräuchte eine Konfigurationsdatei, die die
  sync-/Consistency-Toolchain nicht hat.
- **Verworfen — conftest-Wrapper um `subprocess.run`:** versteckt die Absicht,
  fängt auch In-Process-Aufrufe in `scripts/lib` ab, bricht
  `tests/test_dry_run_no_working_tree_write.py` (monkeypatcht
  `skills_mod.subprocess.run` und asserted, dass es nicht aufgerufen wird) und
  verschluckt beabsichtigte 900-s-Langläufer.

### ADR-2 — Isolation: gemeinsame Fixture + modulgebundene Modul-Globals

- **Kontext:** AC1 verlangt `tmp_path`-Projekte für alle Hook-Tests; heute baut
  sich `tests/test_orchestrator_guard_hook.py` sein Projekt über ein
  modulglobales `mkdtemp`+`atexit`-Paar, das pytest nicht kennt.
- **Entscheidung:** eine modul-scoped Fixture `hook_project_root` in
  `tests/conftest.py`, die `tmp_path_factory` nutzt. Die Hook-Module behalten
  ihre Modul-Globals (`_PROJECT_ROOT` bzw. `_HOOK_CWD`), binden sie aber aus der
  Fixture über eine modul-scoped `autouse`-Fixture — **kein** Umbau der
  Aufrufstellen (Begründung und Grenzen: IC-3).
- **Konsequenzen:** gleiche Semantik wie heute für das Guard-Modul, aber
  auffindbar, von pytest aufgeräumt (kein `atexit`) und in allen Hook-Modulen
  wiederverwendbar. Der Beweistest bleibt unangetastet (er ist der
  Regressionsanker für die Fixture-Umstellung). Der `--basetemp`-Guard in
  `tests/conftest.py::pytest_configure` ist **warn-only** (`tests/conftest.py`
  Modul-Docstring: „deliberately only *warns*"); er erzwingt nichts und ist
  keine Voraussetzung der Fixture.
- **Verworfen:** `monkeypatch.chdir` (ändert nur den Prozess-CWD, nicht den
  `cwd=` des Kindes und nicht `$CLAUDE_PROJECT_DIR`), globale Session-Fixture
  (ein Projekt für alle Tests maskiert Cross-Test-Leaks).

### ADR-3 — Decoy-`tmp`-Projekt statt Echt-Checkout als Prozess-`cwd`

- **Kontext:** `tests/test_repo_containment_hook.py` prüft, dass der Hook seinen
  Root aus dem Payload (bzw. dem Fixanker) nimmt und **nie** aus `$PWD`. Rev. 1
  hielt dafür den echten Checkout als Prozess-`cwd` für nötig. Das ist falsch:
  diskriminierend ist allein, dass der Prozess-`cwd` (i) ein `.meta-config/`
  trägt und (ii) **nicht** die Payload-Wurzel ist. Ein `tmp`-Decoy erfüllt
  beides.
- **Entscheidung:** Der Default von `_run_hook` und die neun Inline-Aufrufe mit
  `cwd=str(_REPO_ROOT)` laufen gegen ein modul-scoped Decoy-Projekt
  (`tmp_path_factory.mktemp("containment-decoy")`), das eine echte
  `.meta-config/project.yaml` mit `repo_containment.enabled: true` und
  `tmp-sink.path: ".tmp"` sowie `.claude/hooks/` enthält. Der Hook unter Test
  bleibt der **echte** Skriptpfad (`_HOOK_PATH`/`_IMPL_PATH`, read-only).
- **Invarianten (verbindlich):**
  1. `cwd` des Kindes trägt `.meta-config/project.yaml` (sonst prüft der Test
     die Trivialität „kein Projekt gefunden").
  2. `cwd` ≠ jede Payload-Wurzel (sonst wäre „Root aus dem Payload" nicht vom
     „Root aus `$PWD`" unterscheidbar).
  3. Die Decoy-Konfiguration ist **aktiv** (`enabled: true` + `tmp-sink`
     aktiviert): ein Hook, der `$PWD` adoptiert, würde einen relativen Write als
     „inside root" erlauben und den Test rot machen — die Zähne bleiben.
  4. Payload-Wurzeln bleiben die per-Test-`tmp_path`-Projekte; nur der
     Prozess-`cwd` wird zum Decoy.
  5. Das Decoy wird **nicht** über `atexit`, sondern über `tmp_path_factory`
     aufgeräumt.
- **Konsequenzen:** AC1 Satz 1 („alle Hook-Tests arbeiten gegen ein
  `tmp_path`-Projekt") ist wörtlich erfüllbar; es bleibt **keine**
  Echt-Checkout-Ausnahme für einen Prozess-`cwd` übrig. Ein Test, der den
  echten Checkout als `cwd` zwingend bräuchte, ist bei der Nachprüfung nicht
  gefunden worden; sollte einer auftauchen, ist er als `datei::test` zu benennen
  und zu begründen, warum ein Decoy für genau diesen Test scheitert.
- Zwei Docstrings werden dabei entschärft: `_run_hook` („defaults to the
  agent-meta repo root") und
  `test_claude_project_dir_is_a_fixed_anchor_from_the_source_tree` („even when
  run from the source tree" → „even when the process cwd is a project-carrying
  directory").

## Interface Contracts

### IC-1 — Timeout-Konstanten (`tests/timeouts.py`, **bestehendes Modul erweitern**)

Verbindlich: `tests/timeouts.py` existiert bereits; P1 fügt **nur** `SLOW_TIMEOUT`
hinzu und lässt `_env_seconds`, `SYNC_TIMEOUT`, `SYNC_VALIDATE_TIMEOUT`,
`SCRIPT_TIMEOUT` unverändert. Wortlaut des neuen Blocks (verbatim):

```python
#: Long-running helper CLI whose measured runtime exceeds SYNC_TIMEOUT
#: (the meta_optimizer family). Env: AGENT_META_SLOW_TIMEOUT.
#: Absorbs the six former local `RUN_TIMEOUT = 900` definitions.
SLOW_TIMEOUT: int = _env_seconds("AGENT_META_SLOW_TIMEOUT", 900)
```

Zusatzbedingungen:

- Importpfad: `from tests.timeouts import SLOW_TIMEOUT` (`tests` ist ein Paket).
- `_env_seconds`-Semantik gilt unverändert: nicht-ganzzahlig, leer oder ≤ 0 →
  Default; Import wirft nie.
- **Modul-Docstring mitpflegen:** der Docstring listet die Env-Variablen
  (`AGENT_META_SYNC_TIMEOUT`, `AGENT_META_SYNC_VALIDATE_TIMEOUT`,
  `AGENT_META_SCRIPT_TIMEOUT`) auf. P1 ergänzt dort
  `* ``AGENT_META_SLOW_TIMEOUT`` -> :data:`SLOW_TIMEOUT`` in derselben
  Änderung — sonst dokumentiert der Docstring drei von vier Konstanten.
- Kein Test definiert danach ein modul-lokales `RUN_TIMEOUT`; die sechs
  Vorkommen werden auf `SLOW_TIMEOUT` umgestellt.

### IC-2 — Mapping-Regel: Aufrufklasse → Konstante

| Aufrufklasse | Konstante | Default | Env-Override |
|---|---|---|---|
| Bash-Hook unter Test | `SCRIPT_TIMEOUT` | 60 | `AGENT_META_SCRIPT_TIMEOUT` |
| Git-Plumbing (`git status`, `git commit`, `git add`) | `SCRIPT_TIMEOUT` | 60 | `AGENT_META_SCRIPT_TIMEOUT` |
| `bash -c`-Schnipsel (Sourcing von `hook_common.sh`) | `SCRIPT_TIMEOUT` | 60 | `AGENT_META_SCRIPT_TIMEOUT` |
| Helper-CLI (Eval-Wrapper, Hook-Adapter, `python -c`-Snippets) | `SCRIPT_TIMEOUT` | 60 | `AGENT_META_SCRIPT_TIMEOUT` |
| `sync.py` ohne `--validate` | `SYNC_TIMEOUT` | 180 | `AGENT_META_SYNC_TIMEOUT` |
| `sync.py --validate` | `SYNC_VALIDATE_TIMEOUT` | 180 (Fallback `SYNC_TIMEOUT`) | `AGENT_META_SYNC_VALIDATE_TIMEOUT` |
| Langläufer-CLI in Tests (meta_optimizer-Familie) | `SLOW_TIMEOUT` | 900 | `AGENT_META_SLOW_TIMEOUT` |
| One-Shot-Readiness-Probe (`git --version`) | Literal | ≤ 10, empfohlen 5 | — |

**Geltungsbereich der Override-Regel — nur neue/changed Werte:** ein von den
Phasen **eingeführter oder geänderter** `timeout=`-Wert muss eine der obigen
Zeilen treffen; ein abweichender Wert ist nur als benannte Konstante zulässig
oder als Literal ≤ 10 für eine Readiness-Probe. Ein neu eingeführtes nacktes
Literal > 10, das in keine Zeile passt, ist ein Spec-Verstoß und braucht eine
neue Tabellenzeile (Spec-Revision), keine Inline-Ausnahme.

**Bestandswerte — explizit geregelt:** bereits vorhandene Literale werden in P1,
P2a und P2b **unverändert übernommen**. Die Phasen ergänzen `timeout=`
ausschließlich dort, wo keines existiert; sie ersetzen kein bestehendes Literal
durch eine Konstante. Ein Bestandsliteral > 10 löst damit **keine**
Spec-Revision aus und ist kein Finding. Belegte Bestandsklassen
(grep-Stichprobe, vollständig erst über P3):

| Wert | Beispiel (verifiziert) | Behandlung |
|---|---|---|
| ≤ 10 | `tests/test_secrets_and_isolation.py` (`git --version`, `timeout=5`) | Readiness-Probe, bleibt |
| 30 | `tests/test_admin_server.py` (`admin-server --help`) | Bestandswert, bleibt |
| 120 | `tests/test_agent_eval_framework.py` (Katalog-Generator) | Bestandswert, bleibt |
| 180 | `tests/test_migration_paths.py` (`sync.py`) | entspricht `SYNC_TIMEOUT`, bleibt als Literal |
| 300 | `tests/test_doctor_cli.py::_cli` (`sync.py`) | bewusst konservativer als `SYNC_TIMEOUT`, bleibt |
| 600 | `tests/test_context_report.py::_run` (`sync.py`) | bewusst konservativer als `SYNC_TIMEOUT`, bleibt |
| 900 | die sechs `RUN_TIMEOUT`-Definitionen | **wird** `SLOW_TIMEOUT` (einzige Pflichtumstellung) |

**Check-Semantik:** `test.subprocess-timeout-missing` prüft die **Anwesenheit**
von `timeout=` und dass der Wert nicht das Literal `None` ist; er behauptet
nicht, den Wert zu beweisen. `Popen` hat keinen `timeout`-Parameter → nur
Allowlist-Eintrag (Schema und Inhalt: IC-11) mit eigenem Finding
`subprocess-timeout.stale-allowlist-entry`.

### IC-3 — Fixture-Contract `hook_project_root` + Bindungsmechanismus (P1)

- **Ort:** `tests/conftest.py`.
- **Signatur:** `hook_project_root(tmp_path_factory) -> pathlib.Path`.
- **Scope:** `scope="module"`, Realisierung über
  `tmp_path_factory.mktemp("hook-project")`.
- **Inhalt (verbindlich):** Kopie von `.meta-config/project.yaml` nach
  `<root>/.meta-config/project.yaml` (enthält `orchestrator.strict: true`, das
  die `STRICT_CASES` tragen); Verzeichnis `<root>/.claude/hooks/` existiert.
- **Rückgabe:** der Projekt-Root; Aufrufer setzen ihn als `cwd=` des Kindes und
  als Payload-`cwd` (beide müssen übereinstimmen, sonst prüft der Test eine
  andere Wurzel als der Hook sieht).
- **Bindungsmechanismus (verbindlich, ersetzt „eins zu eins"):** Die
  Hook-Module behalten ihr Modul-Global, initialisieren es aber mit `None` und
  binden es über eine modul-scoped `autouse`-Fixture:

  ```python
  # tests/test_orchestrator_guard_hook.py (Muster; analog test_hook_common_lib.py)
  _PROJECT_ROOT: Path | None = None

  @pytest.fixture(scope="module", autouse=True)
  def _bind_project_root(hook_project_root):
      global _PROJECT_ROOT
      _PROJECT_ROOT = hook_project_root
      yield
      _PROJECT_ROOT = None
  ```

  Damit bleiben alle `_run_hook(...)`-Aufrufstellen unverändert (kein Editing
  der Aufruf-Sites). **Zwei Grenzen, die der Plan kennen muss:**
  1. Die `mkdtemp`+`atexit`-Zeilen (inkl. `atexit`-Import) entfallen; der
     Modul-Global wird nicht mehr zur Importzeit gefüllt.
  2. Modul-level `@pytest.mark.parametrize`-Daten, die `_PROJECT_ROOT` zur
     Importzeit auswerten, funktionieren nicht mehr. Betroffen ist genau **ein**
     Block: `test_missing_or_non_scalar_tool_name_fails_closed` (vier
     Payload-Dicts mit `"cwd": _PROJECT_ROOT.as_posix()`). Diese Payloads werden
     im Testkörper gebaut (`payload = {..., "cwd": _PROJECT_ROOT.as_posix()}`)
     — die Parametrisierung bleibt, nur das `cwd`-Feld wandert in die
     Testfunktion. Das ist die **einzige** Aufrufstellen-Änderung im
     Guard-Modul.
- **Semantik:** pytest räumt auf (`tmp_path_factory`);
  `tests/conftest.py::pytest_configure` **warnt nur**, wenn der effektive
  Basetemp im Repo liegt (Modul-Docstring: „deliberately only *warns* — it never
  calls `pytest.exit` or `pytest.fail`") und erzwingt keine Isolation. Die
  Fixture ist von diesem Guard unabhängig.
- **Nicht-Zusicherung:** die Fixture kopiert **nicht** den ganzen Repo-Baum und
  legt **kein** `.claude/hooks/.guard-audit.log` an — der Hook erzeugt es bei
  Bedarf selbst; das ist der Nachweis, dass der Schreibpfad in der Fixture
  landet.
- **Parallelität:** modul-scoped, daher unter `-n 2 --dist loadfile` pro Worker
  und Modul einmalig; kein Session-Scope, damit kein Test den Zustand eines
  anderen sieht.

### IC-4 — Per-Modul-Isolationsmatrix (P1)

| Modul | `cwd=` | Timeout | Anmerkung |
|---|---|---|---|
| `test_orchestrator_guard_hook.py` | `hook_project_root` (Global, IC-3) | `SCRIPT_TIMEOUT` | Fixture-Bindung statt `mkdtemp`; ein Parametrize-Block wandert in den Testkörper; Beweistest unverändert |
| `test_hook_common_lib.py` | `hook_project_root` (Global, IC-3-Muster) | `SCRIPT_TIMEOUT` | `_call` **und** die sieben direkten Aufrufe erhalten `cwd=`/`timeout=`; PATH/HOME bleiben echt (`command -v python3`); `_scan`-Default wird `SCRIPT_TIMEOUT` statt `None` |
| `test_graphify_guard_hooks.py` | `tmp_path` (drei Runner) | `SCRIPT_TIMEOUT` | `env` bleibt das reduzierte PATH-Dict |
| `test_dod_push_check_hook.py` | bereits `tmp`-basiert | `SCRIPT_TIMEOUT` | nur `timeout=` (20 Aufrufe) |
| `test_artifact_freshness_hook.py` | bereits `tmp`-basiert | `SCRIPT_TIMEOUT` | nur `timeout=` |
| `test_pre_release_check_hook.py` | bereits `tmp`-basiert | `SCRIPT_TIMEOUT` | nur `timeout=` |
| `test_auto_github_release_hook.py` | bereits `tmp`-basiert | `SCRIPT_TIMEOUT` | nur `timeout=` |
| `test_release_gate_checksums.py` | bereits `tmp`-basiert | `SCRIPT_TIMEOUT` | nur `timeout=` |
| `test_repo_containment_hook.py` | **Decoy-Projekt** (ADR-3) | `SCRIPT_TIMEOUT` | Default von `_run_hook` **und** die neun Inline-`cwd=str(_REPO_ROOT)`-Stellen auf den Decoy; zwei Docstrings (ADR-3) |

Alle neun Module erfüllen danach dieselbe Regel: **jeder** Subprozess-Aufruf
setzt `cwd=` (Wert ≠ `None`) und `timeout=` (Wert ≠ `None`).

### IC-5 — Echt-Checkout-**Lese**vorgänge (nicht mehr: Prozess-`cwd`-Ausnahmen)

Nach ADR-3 gibt es **keine** Hook-Test-Ausnahme mehr, die den echten Checkout als
Prozess-`cwd` braucht. Als echte-Checkout-Semantik bleiben nur Lesevorgänge
außerhalb des P1-Scan-Sets dokumentiert:

1. `tests/test_agent_eval_framework.py::_run_provider` — `cwd=str(_REPO_ROOT)`,
   weil die Wrapper in `tests/routing-llm-eval/` Prompts/Katalog relativ zum
   Checkout auflösen.
2. `tests/test_antigravity_hooks_registration.py::_repo_status` — `git -C
   <repo> status --porcelain`; der Pfad kommt aus `-C`, der Prozess-`cwd` ist
   irrelevant (kein `cwd=` nötig, Modul liegt außerhalb des P1-Scope).
3. `tests/test_orchestrator_guard_hook.py::test_header_lists_known_gaps` und die
   `_IMPL_PATH`-Lesevorgänge — reine Datei-Lesevorgänge, keine Subprozesse.

**Warum diese Stellen den Audit-Log nicht schreiben können:**
`hook_audit_log_append` (`hooks/1-generic/lib/hook_common.sh`) hat genau einen
Aufrufer, `hooks/1-generic/orchestrator-guard-impl.sh`; die
`repo-containment*.sh`-Hooks enthalten keinen Audit-Schreibvorgang (grep). Die
verbleibenden Stellen betreffen `git status`, Datei-Lesevorgänge und
Registrierungsprüfungen. P4's Vorher/Nachher-Digest fängt jede künftige Änderung
dieser Eigenschaft.

### IC-6 — Statischer Guard-Test `tests/test_hook_test_isolation.py` (neu)

- **Scan-Set (verbindlich, neun Module):** `test_orchestrator_guard_hook.py`,
  `test_hook_common_lib.py`, `test_graphify_guard_hooks.py`,
  `test_dod_push_check_hook.py`, `test_artifact_freshness_hook.py`,
  `test_pre_release_check_hook.py`, `test_auto_github_release_hook.py`,
  `test_release_gate_checksums.py`, `test_repo_containment_hook.py`.
- **Regel 1 (cwd-Pflicht, nicht mehr nur für `orchestrator-guard`-argv):** jeder
  Aufruf von `subprocess.run` / `call` / `check_output` / `check_call` /
  `Popen` im Scan-Set braucht ein `cwd=`-Keyword-Argument, dessen Wert nicht das
  Literal `None` ist. Das deckt alle neun Module ab, nicht nur die
  Guard-Implementierungs-Aufrufe.
- **Regel 2 (Timeout-Pflicht):** jeder dieser Aufrufe braucht `timeout=` mit
  einem Wert, der nicht das Literal `None` ist (`subprocess.run(...,
  timeout=None)` ist ein Finding). `Popen` ist von Regel 2 ausgenommen
  (kein Keyword) und wird über die Allowlist aus IC-11 geführt.
- **Alias-Auflösung:** `import subprocess as sp`, `from subprocess import run`.
  `**kwargs`-Spread → fail closed (Finding).
- **Ausnahmen:** keine. Das Scan-Set enthält keinen Eintrag, der die Regel
  bricht; jede Ausnahme wäre eine Spec-Änderung.
- **Fehlerbild:** ein Finding, das Datei + Funktionsname nennt; kein
  Repo-Schreibvorgang, keine Ausführung des Hooks.
- **Nicht-Zusicherung:** der Test beweist nicht, dass `cwd` auf ein
  `tmp_path`-Verzeichnis zeigt (das leisten ADR-3, der Laufzeit-Beweistest und
  der CI-Digest).

### IC-7 — `ARTIFACT_TESTS`-Env-Listen-Contract (P4)

- **Ort:** `env:`-Block von `.github/workflows/orchestration-test.yml`, neben
  den sechs bestehenden Listen („single source of truth").
- **Format:** `>-`-Block mit einem Modulpfad pro Zeile, exakt wie
  `SUBPROCESS_SHARD_<n>` / `HEAVY_FIXTURE_SHARD_<n>`.
- **Konsument:** ausschließlich der neue Job `artifacts`; die Liste wird
  **nicht** in die `--ignore`-Ableitung des `test`-Jobs eingespeist und trägt
  einen Kommentar „not part of the 15/17 partition".
- **Eigene Existenzprüfung:** analog zur bestehenden Pfadprüfung im
  Validierungsschritt; jede gelistete Datei muss existieren.
- **Meta-Test (repo-lokal, eigene Datei `tests/test_artifact_tests_list.py`,
  gehört zu P4):** jedes Modul der Test-Suite, dessen Skip-Gate auf einen
  generierten Baum zeigt, muss in `ARTIFACT_TESTS` stehen. Erkennungsmenge
  (verbindlich, korrigiert gegenüber Rev. 1):
  - Aufruf von `_skip_unless_generated`, **oder**
  - `pytest.skip(...)` mit einem Grund, der einen dieser Strings enthält:
    `run sync.py`, `unsynced checkout`, `generated roots absent`,
    `not generated in this project`.

  Rev. 1 nannte nur die ersten drei Strings und `_skip_unless_generated`; der
  Seed `tests/test_mcp_role_tools.py` matcht **keinen** davon (sein Grund lautet
  `"e2e-tester not generated in this project"`). Mit dem vierten String ist der
  Seed vollständig abgedeckt. Seed-Menge:
  `tests/test_opencode_agents.py`, `tests/test_agent_eval_framework.py`,
  `tests/test_reference_standards_documented.py`,
  `tests/test_legacy_registries_removed.py`, `tests/test_mcp_role_tools.py`.
  Der Meta-Test prüft beide Richtungen (jedes erkannte Modul steht in der Liste;
  kein gelistetes Modul ohne Erkennungssignal).
- **Nicht-Zusicherung:** die Erkennungsmenge ist grep-/AST-heuristisch. Ein
  ungesyncter Checkout kann weitere Skip-Gates zeigen (Kandidat:
  `tests/test_lazy_skills_channel.py`, Skip-Gründe „no skills channel"/„native
  rules channel") — siehe `Unverified`.

### IC-8 — CI-Digest-Schritt-Contract (AC1 in der CI, P4)

- **Vorher-Schritt** (vor der Heavy-Fixture-Slice im `test`-Job, je Shard):
  schreibt in `$GITHUB_ENV` eine Variable mit dem SHA-256 von
  `.claude/hooks/.guard-audit.log` oder dem Sentinel `absent`, wenn die Datei
  nicht existiert (`sha256sum` bzw. `test -f`).
- **Nachher-Schritt** (nach der count-basierten Remainder-Stufe): berechnet
  denselben Wert neu und vergleicht; bei Abweichung `exit 1` mit
  `::error::`-Meldung, die den Pfad nennt.
- **Granularität:** pro Shard korrekt, weil die Hook-Module in **keiner** der
  sechs Listen stehen und damit in der Remainder-Menge laufen (über drei Shards
  verteilt).
- **Nicht-Zusicherung:** der Digest ist eine Zustandsprüfung, kein
  Reihenfolgebeweis; er sagt nichts über Testinhalte, nur über den Log.

### IC-9 — Job `artifacts` (AC4, P4)

- **Matrix:** `strategy.matrix` mit einer Achse, `python-version: ['3.12']`
  (Single-Leg). Formell ist das eine Matrix mit einem Bein — AC4 ist damit
  buchstäblich erfüllt (Wortlaut-Notiz unter „Acceptance Criteria").
- **`timeout-minutes: 15`.**
- **Steps in dieser Reihenfolge:** Checkout → `actions/setup-python` (Cache auf
  `tests/requirements.txt`) → `pip install -r tests/requirements.txt` →
  `python scripts/sync.py` → `python -m pytest -q -n 0 $ARTIFACT_TESTS -rs --tb=short`
  → Assertion „0 Skips mit Begründung `generated` / `run sync.py` / `unsynced`
  / `generated roots absent` / `not generated`".
- **Kein Drift-Gate in diesem Job.** Das Gate bleibt ausschließlich in
  `validate.yml` (`Check generated files are committed`); ein `sync.py`-Lauf
  hier darf nicht als zweites Gate wirken.
- **Kein Leg des `test`-Jobs:** ein gesyncter Checkout schiebt `Claude/`,
  `.opencode/`, `.gemini/` usw. in jede Repo-Copy-Fixture; die 17
  Heavy-Fixture-Module sind von genau diesen Kopien setup-dominiert.
- **Verworfene Alternative:** Sync-Step im `test`-Job unter
  `if: matrix.shard == 1 && matrix.python-version == '3.12'` — beruht auf der
  **ungemessenen** Annahme, dass die Repo-Copy-Fixtures dieses Legs die
  30-Minuten-Grenze sprengen (`Unverified`: Laufzeiteffekt der generierten
  Provider-Bäume).

### IC-10 — Workflow `browser-test.yml` (AC6, P6)

- **Datei:** `.github/workflows/browser-test.yml` (neu).
- **`timeout-minutes: 20`.**
- **Trigger:** `push`/`pull_request` mit Pfadfilter analog
  `orchestration-test.yml` (u. a. `scripts/**`, `tests/**`, `config/**`,
  die Workflow-Datei selbst).
- **Steps:** Checkout → `setup-python` (Cache auf `tests/requirements.txt`) →
  **`pip install -r tests/requirements.txt -r tests/requirements-browser.txt`**
  → `python -m playwright install --with-deps chromium` →
  `python -m pytest tests/browser -q -n 0`.
- **Warum beide Requirements-Dateien:** `tests/requirements-browser.txt`
  enthält **nur** den Playwright-Pin. `pytest` und `pytest-xdist` (nötig für
  `-n 0`) kommen aus `tests/requirements.txt`. Ohne deren Installation bricht
  der Job beim ersten `python -m pytest` ab (bzw. `-n 0` ist ein unbekanntes
  Argument ohne xdist).
- **Playwright darf nicht in `tests/requirements.txt`:** das würde 10+ Module im
  `test`-Job-Count-Remainder entskippen und in sechs parallelen Legs je einen
  `admin-server` auf Port 7421 starten.
- **Port-Disziplin:** `tests/browser/conftest.py` pinnt 7421; der Workflow läuft
  `-n 0`, damit genau ein Server je Job existiert.

### IC-11 — Check-Modul `scripts/lib/consistency/subprocess_timeout.py` (P3)

- **Öffentliche Funktion:**
  `check_subprocess_timeout(root: Path) -> list[Finding]`, Rückgabe über
  `lib.consistency.report.Finding`/`Severity`.
- **Scan-Scope:** `tests/**/*.py` (AST, nicht grep → mehrzeilige Aufrufe,
  Klammerung und `# noqa` sind irrelevant) **ohne** `tests/manual/**` (nicht von
  pytest gesammelt, nur von Menschen aufgerufen, keine CI-Exposition — ein
  `timeout=` dort wäre eine unbelegte Wahl). `scripts/` bleibt außerhalb (dort
  gilt `temp_literals.check_subprocess_env_pinning`).
- **Pflicht-Keywords:** `run`, `call`, `check_output`, `check_call` brauchen
  `timeout=`, und der Wert darf nicht das Literal `None` sein. `Popen` ist
  allowlist-only.
- **Alias-Auflösung:** `import subprocess as sp` und
  `from subprocess import run` werden aufgelöst; `**kwargs`-Spread → **fail
  closed** (Finding), weil die Anwesenheit nicht statisch bewiesen ist.
- **Findings:** `test.subprocess-timeout-missing` (Severity **ERROR**),
  `subprocess-timeout.stale-allowlist-entry` (WARNING) für Allowlist-Einträge
  ohne Treffer, `subprocess-timeout.allowlist-entry` (WARNING) für unvollständige
  Einträge.
- **Allowlist:** `.meta-config/subprocess-timeout-allowlist.yaml`. Schema exakt
  wie die bestehende `temp-literal-allowlist.yaml`: Top-Level `entries:`, pro
  Eintrag **`path`** (repo-relativer Pfad/Glob), **`pattern`** (Regex auf die
  Aufrufzeile) und **`reason`** (Pflicht, nicht leer); optional `owner`.
  Unbekannte Felder (z. B. `expires`) und unvollständige Einträge unterdrücken
  nichts und erzeugen `subprocess-timeout.allowlist-entry`. Das Laden darf nie
  werfen (Muster: `temp_literals._load_allowlist_entries`).
- **Pflichtinhalt der Allowlist (P3 legt genau diese Einträge an, sonst ist der
  Check auf Anhieb rot):**

  ```yaml
  entries:
    - path: "tests/browser/conftest.py"
      pattern: "subprocess\\.Popen\\("
      reason: >-
        Popen kennt kein timeout=-Keyword; die Lebensdauer ist im Fixture
        begrenzt (_wait_for_server(timeout=15.0), proc.wait(timeout=5.0),
        proc.kill() im finally).
    - path: "tests/active_set_render.py"
      pattern: "subprocess\\.Popen\\("
      reason: >-
        Popen kennt kein timeout=-Keyword; die Obergrenze liegt eine Zeile
        später auf proc.communicate(timeout=900) im selben
        Schleifendurchlauf.
  ```

  Diese zwei Einträge sind die **vollständige** aktuelle `Popen`-Menge (Rev.
  2: genau zwei `Popen(`-Aufrufstellen unter `tests/`, per grep verifiziert).
- **Severity-Flip:** Der Check landet in **einem** Commit mit diesen zwei
  Einträgen und ist damit von Anfang an ERROR und grün. Es gibt keinen
  WARNING-Vorlauf; die Reihenfolge P1 → P2a → P2b → P3 stellt sicher, dass alle
  übrigen Findings vorher abgearbeitet sind.
- **Registrierung:** `scripts/consistency-check.py` importiert
  `check_subprocess_timeout` aus `lib.consistency.subprocess_timeout` und ruft
  ihn im globalen Cross-Reference-Block direkt neben `check_py39_union_syntax`
  auf. Damit läuft er in `sync.py --validate` auf 3.9/3.11/3.12.
- **Kein Baseline-File.** Eine Baseline wäre die „jeder"-Lüge: sie würde
  bestehende Verstöße als akzeptabel einfrieren.
- **Unit-Tests:** `tests/test_subprocess_timeout_guard.py` als Spiegel von
  `tests/test_python_compat_consistency.py` (tmp-Fixtures, Finding-Code,
  Alias-Formen, `**kwargs`, `timeout=None`, Popen-Allowlist, stale entry,
  unvollständiger Eintrag) plus ein Registrierungs-Meta-Test, der belegt, dass
  der Check im `consistency-check.py`-Pfad aufgerufen wird.

### IC-12 — AC5-Dokumentations-Contract (P5)

- **Ort:** **neuer** Kommentarblock in `.github/workflows/validate.yml`,
  unmittelbar oberhalb von `jobs:` — dort existiert heute **kein**
  Erläuterungsblock (nur zwei Inline-Kommentare: über `concurrency.group` und
  über `jobs.scenarios.timeout-minutes`). Vorbild für Ton und Länge ist der
  Erläuterungsblock in `orchestration-test.yml` (Zeilen 3–59); er beschreibt die
  Jobpartition und bleibt unverändert.
- **Pflichtinhalt:** (a) Entscheidung = **bewusste Ablehnung** einer
  Szenario-Matrix über mehrere Python-Versionen; (b) Begründung: Szenario-Suite
  ist shell-/provider-agnostisch, versionsspezifische Grenzen werden bereits
  von `compat-311` (TOML-Boundary 3.9/3.10/3.11) und den beiden vollständig
  getesteten Endpunkten 3.9/3.12 im `test`-Job abgedeckt; (c) Alternative, die
  verworfen wurde (Szenarien je Version) und ihr Kostentreiber (79 Szenarien ×
  4 Shards × n Versionen); (d) Wiederaufnahme-Bedingung (z. B. ein
  versionsspezifischer Szenario-Fehler).
- **Kein Workflow-Verhalten ändert sich** — reine Dokumentation.

### IC-13 — Doku- und Changelog-Pflichten (alle Phasen)

- `tests/README.md` dokumentiert die Timeout-Tabelle und sagt heute „Weitere
  Heavy-Module nutzen noch modul-lokale Obergrenzen; Vereinheitlichung ist ein
  Follow-up." P1 ergänzt die `SLOW_TIMEOUT`-Zeile **und** einen kurzen Abschnitt
  „CI-Job-Timeouts" mit dem manuellen Prüfkommando für AC2 (siehe
  Evidenz-Matrix); P2b entfernt/aktualisiert den Follow-up-Satz, sobald die
  Vereinheitlichung abgeschlossen ist.
- `CHANGELOG.md`: P1 trägt den Sammel-Eintrag „CI robustness (#945, residual)";
  jede weitere Phase ergänzt ihren eigenen Bullet unter `## [Unreleased]`, sobald
  sie Dateien anlegt. Ein Bullet nennt den neuen Job mit seinem
  `timeout-minutes`, wenn die Phase einen Job anlegt (AC2-Nachweis). Kein
  Eintrag in eine abgeschlossene Release-Sektion.
- Commit-Messages: Conventional Commits, Englisch, ≤ 72 Zeichen erste Zeile.

## Datenfluss

**Lokaler Hook-Testlauf (nach P1):** `pytest` sammelt Modul → die modul-scoped
`autouse`-Fixture bindet `hook_project_root` in das Modul-Global (bzw. liefert
den Decoy in `test_repo_containment_hook.py`) → Test baut PreToolUse-JSON mit
`cwd=<root>` → `subprocess.run` startet `bash hook` mit `cwd=<root>`, `env` ohne
`CLAUDE_PROJECT_DIR` und `timeout=SCRIPT_TIMEOUT` → Hook löst Projekt-Root aus
Payload/`$PWD` auf, liest `project.yaml`, schreibt ggf.
`<root>/.claude/hooks/.guard-audit.log` → Exitcode wird asserted. Der echte
Checkout bleibt unberührt; der Beweistest vergleicht die echte Logdatei
byteweise vor/nach.

**Decoy-Pfad (`test_repo_containment_hook.py`, nach P1):** Prozess-`cwd` =
Decoy-Projekt (eigenes `.meta-config/project.yaml`, ≠ Payload-Wurzel), Hook =
echter Skriptpfad, Payload-`cwd` = per-Test-`tmp_path`-Projekt. Ein Hook, der
`$PWD` adoptiert, würde relativ adressierte Ziele im Decoy als „inside root"
erlauben und den Test rot machen.

**CI-`test`-Job (nach P4, setzt P1 voraus):** Checkout → `pip install` →
Partition validieren → **Digest vorher** (`sha256` oder `absent`) →
Heavy-Fixture-Slice → Remainder (enthält alle Hook-Module) → **Digest nachher +
Vergleich** → bei Shard 1 `sync.py --validate`.

**CI-`artifacts`-Job (nach P4):** Checkout → install aus
`tests/requirements.txt` → `sync.py` (rendert Provider-Bäume) →
`pytest $ARTIFACT_TESTS -rs` → Skip-Assertion. Kein Drift-Gate, keine
Parallelität (`-n 0`).

**CI-`browser-test.yml` (nach P6):** Checkout → install aus
`tests/requirements.txt` **und** `tests/requirements-browser.txt` → Chromium
installieren → `pytest tests/browser -n 0` → `conftest.py` startet einen
`admin-server` auf 7421, wartet auf HTTP-Antwort, gibt URL aus, beendet den
Prozess im `finally`.

**Konsistenz-Check (nach P3):** `sync.py --validate` → `consistency-check.py`
→ `check_subprocess_timeout(root)` → AST über `tests/**/*.py` (ohne
`tests/manual/`) → Finding je fehlendem `timeout=` oder `timeout=None` (ERROR)
→ Exitcode des Validators.

## Acceptance Criteria

Die sechs Kriterien aus Issue #945, **wörtlich** (nicht umformuliert):

> **AC1:** Alle Hook-Tests arbeiten gegen ein `tmp_path`-Projekt. Nach einem vollständigen Testlauf ist `.claude/hooks/.guard-audit.log` unverändert.

> **AC2:** Jeder CI-Job hat `timeout-minutes` gesetzt.

> **AC3:** Jeder `subprocess.run`-Aufruf in den Tests hat `timeout=`.

> **AC4:** Die Artefakt-Tests laufen in der CI, weil der Sync vor pytest in einem Matrix-Bein ausgeführt wird.

> **AC5:** Szenario-Suite-Entscheidung für mehrere Python-Versionen ist getroffen und dokumentiert (Umsetzung oder bewusste Ablehnung).

> **AC6:** Playwright-Tests haben einen CI-Pfad oder eine dokumentierte Begründung, warum nicht.

### AC1 — Messlatte (wörtlich erfüllbar, keine Sonderlesart)

AC1 Satz 1 ist **wörtlich** erfüllbar. Diskriminierend für
`tests/test_repo_containment_hook.py` ist nicht „Echt-Checkout vs. `tmp_path`",
sondern ausschließlich: (i) der Prozess-`cwd` trägt `.meta-config/` und (ii) er
ist **nicht** die Payload-Wurzel. Ein `tmp`-Decoy-Projekt erfüllt beides
(ADR-3), also ist die Eigenschaft „Root kommt aus dem Payload, nie aus `$PWD`"
auch gegen ein `tmp_path`-Projekt prüfbar. Damit entfällt die in Rev. 1
behauptete Ausnahme; es bleibt keine Interpretation offen.

Prüfbar wird das über drei Ebenen:

1. **statisch:** `tests/test_hook_test_isolation.py` — `cwd=`/`timeout=` an
   jedem Subprozess-Aufruf der neun P1-Module (IC-6).
2. **lokal:** `tests/test_orchestrator_guard_hook.py::test_strict_cases_never_write_the_repo_audit_log`
   (Byte-Vergleich) plus ADR-3-Invarianten (Decoy aktiv konfiguriert).
3. **CI:** sha256 vor/nach je Shard (IC-8).

### AC4 — Wortlaut-Notiz (keine Verletzung)

AC4 sagt „in einem Matrix-Bein". Der neue `artifacts`-Job ist eine
`strategy.matrix` mit **einem** Bein (`python-version: ['3.12']`). Formell ist
das eine Matrix, also erfüllt der Job AC4 buchstäblich; die Absicht („Sync vor
pytest in einem CI-Matrix-Job") ebenfalls. Offen ist nur die Wortwahl: die
Formulierung „Matrix-Bein" lädt zur Lesart „mehrere Beine" ein. Der
`CHANGELOG`-Bullet zu P4 nennt deshalb ausdrücklich „Single-Leg-Matrix".

Die Alternative — Sync im `test`-Job unter
`if: matrix.shard == 1 && matrix.python-version == '3.12'` — wurde nicht wegen
eines belegten Problems verworfen, sondern wegen einer **ungemessenen**
Laufzeitannahme (Repo-Copy-Fixtures dieses Legs; siehe `Unverified`). Sie bleibt
gültig, falls die Messung sie stützt.

### Evidenz-Matrix

| AC | Evidenz | Phase | Status nach Wave 4 |
|---|---|---|---|
| **AC1** | statisch: `tests/test_hook_test_isolation.py` (`cwd=`/`timeout=` an jedem Aufruf der neun Module) · lokal: `test_strict_cases_never_write_the_repo_audit_log` (Byte-Vergleich) + Decoy-Invarianten (ADR-3) · CI: sha256 vor/nach je Shard (IC-8) | P1, P4 | erfüllt (wörtlich) |
| **AC2** | bereits erfüllt; Regressionsprüfung = **manueller** Grep über beide Workflows (`grep -c timeout-minutes` je Job-Definition), Kommando dokumentiert in `tests/README.md` (P1) und ausgeführt in P4/P6 nach dem Anlegen der neuen Jobs. Kein automatisierter Test. | P1 (Doku), P4, P6 (Ausführung) | erfüllt (bereits) |
| **AC3** | Finding `test.subprocess-timeout-missing` (ERROR) aus `check_subprocess_timeout`, registriert in `scripts/consistency-check.py` neben `check_py39_union_syntax`, läuft via `sync.py --validate` auf 3.9/3.11/3.12 · AST über `tests/**/*.py` ohne `tests/manual/`, Aliase aufgelöst, `**kwargs` fail-closed, `timeout=None` Finding, `Popen` allowlist-only (2 Einträge), keine Baseline · Unit-Tests + Registrierungs-Meta-Test | P1, P2a, P2b, P3 | erfüllt |
| **AC4** | Job `artifacts` grün und „0 Skips mit Begründung `generated`/`run sync.py`/`unsynced`/`generated roots absent`/`not generated`" (`-rs`) · Meta-Test `tests/test_artifact_tests_list.py`, dass jedes Skip-Gate-Modul in `ARTIFACT_TESTS` steht | P4 | erfüllt (Single-Leg-Matrix) |
| **AC5** | dokumentierte Entscheidung im neuen `validate.yml`-Kommentarblock, konsistent mit der Abwesenheit eines Per-Version-Szenario-Beins | P5 | erfüllt (Ablehnung dokumentiert) |
| **AC6** | `.github/workflows/browser-test.yml` existiert und ist grün; ≥ 10 gesammelte Module in `tests/browser` (Ist: 11); 0 Playwright-Skips | P6 | erfüllt |

## Phasen

Reihenfolge und Abhängigkeiten: **P1 → P2a → P2b → P3** strikt; **P4 nach P1**,
sonst parallel zu P2a/P2b/P3/P5/P6; **P5 und P6** unabhängig.

### P1 — Timeout-Contract + Hook-Slice-Isolation (L, 14 Dateien)

**Dateien (Modify/Create):**

- Modify: `tests/timeouts.py` (`SLOW_TIMEOUT`, **Docstring-Env-Liste**, IC-1)
- Modify: `tests/conftest.py` (Fixture `hook_project_root`, IC-3)
- Modify: `tests/test_orchestrator_guard_hook.py` (Fixture-Bindung, ein
  Parametrize-Block, `timeout=`, Docstrings)
- Modify: `tests/test_repo_containment_hook.py` (Decoy-Default + neun
  Inline-`cwd`-Stellen, `timeout=`, zwei Docstrings, ADR-3)
- Modify: `tests/test_hook_common_lib.py` (`cwd=`/`timeout=` an `_call` **und**
  den sieben direkten Aufrufen, `_scan`-Default)
- Modify: `tests/test_graphify_guard_hooks.py` (`cwd=tmp_path`, `timeout=`)
- Modify: `tests/test_dod_push_check_hook.py` (`timeout=`)
- Modify: `tests/test_artifact_freshness_hook.py` (`timeout=`)
- Modify: `tests/test_pre_release_check_hook.py` (`timeout=`)
- Modify: `tests/test_auto_github_release_hook.py` (`timeout=`)
- Modify: `tests/test_release_gate_checksums.py` (`timeout=`)
- Create: `tests/test_hook_test_isolation.py` (IC-6)
- Modify: `tests/README.md` (`SLOW_TIMEOUT`-Zeile, AC2-Prüfkommando)
- Modify: `CHANGELOG.md` (`[Unreleased]`-Sammel-Eintrag „CI robustness (#945, residual)")

**Interne Commit-Reihenfolge:** (1) `tests/timeouts.py` (`SLOW_TIMEOUT` +
Docstring, importierbar, noch ungenutzt) → (2) `tests/conftest.py`-Fixture +
Bindung/Decoy in den Hook-Modulen → (3) `timeout=`-Adoption in allen
P1-Modulen → (4) `tests/test_hook_test_isolation.py`. So ist jeder Commit für
sich grün und die Isolations-Umstellung vom Timeout-Thema getrennt.

**Aufwand (aus dem Bindungsmechanismus, IC-3):** ~90 geänderte Zeilen in 14
Dateien. Der Fixture-Umzug kostet 1 Modul-Global + 1 `autouse`-Fixture + 1
Parametrize-Umbau im Guard-Modul; der Decoy kostet 1 Modul-Global + 1
`autouse`-Fixture + 9 `cwd=`-Ersetzungen im Containment-Modul; `timeout=` an 72
Aufrufstellen. **Keine** Massenänderung an den `_run_hook(...)`-Aufrufstellen.

**Warum ein PR:** AC1 und AC3 berühren dieselben Helfer (`_run_hook`, `_call`);
getrennte PRs würden in jedem Helfer-Hunk kollidieren.

**Schließt:** AC1 (lokal beweisbar), AC3 (Hook-Slice).
**Rollback:** PR-Revert. **Grenze:** unabhängig revertierbar ist P1 nur
**solange P2a noch nicht gemergt ist** — `SLOW_TIMEOUT` ist bis dahin ungenutzt.
Nach P2a importieren die `meta_optimizer`-Module die Konstante; ein P1-Revert
muss dann P2b → P2a → P1 in dieser Reihenfolge laufen.

### P2a — Timeout-Adoption: Sync-/CLI-Treiber + Optimizer-Familie (XL, 32 Dateien)

**Dateien (alle Modify):** `tests/test_agent_eval_framework.py`,
`tests/test_migration_paths.py`, `tests/test_admin_server.py`,
`tests/test_doctor_cli.py`, `tests/test_compact_matrix.py`,
`tests/test_cleanup_preview_cli.py`,
`tests/test_consistency_reference_standards.py`,
`tests/test_sharkord_service_name_migration.py`,
`tests/test_platform_defaults_resolved_file.py`,
`tests/test_provider_matrix_sync.py`,
`tests/test_provider_reactivation_artifacts.py`,
`tests/test_standalone_export_in_sync.py`,
`tests/test_expected_agents_active_set.py`,
`tests/test_generated_file_drift_e2e.py`, `tests/test_sync_validation_gate.py`,
`tests/test_sync_end_checks.py`, `tests/test_scan_staged.py`,
`tests/test_problem1_integration.py`, `tests/test_pipeline_active_set_filter.py`,
`tests/test_cli_smoke_multi_provider.py`,
`tests/test_auto_commit_allowlist_pipeline.py`,
`tests/test_meta_optimizer_runner.py`, `tests/test_meta_optimizer_applier.py`,
`tests/test_meta_optimizer_marks.py`,
`tests/test_meta_optimizer_credentials.py`,
`tests/test_meta_optimizer_refill.py`,
`tests/test_meta_optimizer_inactive_scope.py`,
`tests/test_meta_optimizer_fanout.py`, `tests/test_knowledge_engine.py`,
`tests/test_role_routing_eval_catalog.py`, `tests/test_lifecycle_check_args.py`,
`tests/test_antigravity_hooks_registration.py`.

**Inhalt:** `timeout=` nach IC-2 ergänzen, wo keines existiert (Bestandswerte
unverändert), die sechs lokalen `RUN_TIMEOUT = 900`-Definitionen auf
`SLOW_TIMEOUT` umstellen und die Importe auf
`from tests.timeouts import SLOW_TIMEOUT` ziehen. `CHANGELOG.md`-Bullet.

**Schließt:** AC3 (Teil). **Rollback:** PR-Revert; die Werte stammen
ausschließlich aus IC-2, Defaults ≥ gemessenem Worst Case.

### P2b — Timeout-Adoption: Fixture-/Kontext-/Repo-Copy-Module (XL, 31 Dateien)

**Dateien (Modify, 29 mit Edits):** `tests/test_ac01_render_identity.py`,
`tests/test_active_set_consumers_identity.py`,
`tests/test_audit_config_readonly.py`, `tests/test_backup_round_trip_804.py`,
`tests/test_basetemp_guard.py`, `tests/test_check_ignored_absent.py`,
`tests/test_context_anchors.py`, `tests/test_context_budget_checks.py`,
`tests/test_context_filename_settings.py`,
`tests/test_context_profile_schema.py`, `tests/test_context_report.py`,
`tests/test_continue_prompts_active_set.py`,
`tests/test_deactivation_status_read_only.py`,
`tests/test_dispatch_depth_and_hard_cap.py`,
`tests/test_docker_image_scan_multi.py`, `tests/test_gitignore_keep.py`,
`tests/test_gitignore_shadowing.py`,
`tests/test_hook_registration_invariant.py`,
`tests/test_newline_normalization.py`,
`tests/test_only_variables_updates_context_806.py`,
`tests/test_opencode_v2_surface.py`, `tests/test_secrets_and_isolation.py`,
`tests/test_tmp_paths_builder.py`, `tests/test_tmp_sink_default_on.py`,
`tests/test_tmp_sink_injection.py`, `tests/test_tmp_sink_migration_error.py`,
`tests/test_tmp_sink_output_dirs.py`, `tests/test_tmp_sink_path_parity.py`,
`tests/test_unread_channels_removed.py`.

**Allowlist-only (kein Edit, Eintrag entsteht in P3):**
`tests/active_set_render.py` (`Popen`), `tests/browser/conftest.py` (`Popen`).

**Nicht im Scope:** `tests/manual/**` (IC-11 schließt es aus).

**Inhalt:** `timeout=` nach IC-2 ergänzen, wo keines existiert. Zwei
Sonderfälle beim Plan verifizieren: `tests/test_secrets_and_isolation.py` setzt
bereits an allen vier Aufrufen `timeout=` (dann 0 Edits, Phase bleibt bei 31
gelisteten Dateien), und `tests/test_tmp_sink_output_dirs.py` prüft `env` von
`subprocess.run`-Aufrufen per eigener AST-Hilfe — die darf durch das neue
Keyword nicht brechen. `tests/README.md` Follow-up-Satz aktualisieren,
`CHANGELOG.md`-Bullet.

**Schließt:** AC3 (Rest). **Rollback:** PR-Revert.

### P3 — Vollständigkeits-Check (M, 5 Dateien)

**Dateien:** Create `scripts/lib/consistency/subprocess_timeout.py` (IC-11) ·
Modify `scripts/consistency-check.py` (Import + Aufruf neben
`check_py39_union_syntax`) · Create `tests/test_subprocess_timeout_guard.py` ·
Create `.meta-config/subprocess-timeout-allowlist.yaml` (**mit den zwei
verbindlichen Einträgen** aus IC-11) · Modify `CHANGELOG.md`.

**Severity:** ERROR ab dem ersten Commit, weil die Allowlist im selben PR die
beiden `Popen`-Stellen abdeckt (IC-11) und P2a/P2b vorher alle übrigen
Aufrufstellen versorgt haben. Kein WARNING-Vorlauf, kein Folge-Flip.
**Escape Hatch (nur bei belegtem Blocker in P2b):** P3 als WARNING landen und
den Flip als eigener Commit im selben PR nachziehen — dann nennt der
`CHANGELOG`-Bullet den Zwischenstand.
**Schließt:** AC3 (Beweis). **Rollback:** Severity auf WARNING stellen (1 Zeile)
oder Check-Aufruf entfernen.

### P4 — CI-Beweis + Artefakt-Job + Meta-Test (M, 3 Dateien)

**Abhängigkeit:** **nach P1** (der Digest-Schritt erwartet die Hook-Module in
der Remainder-Menge); parallel zu P2a/P2b/P3/P5/P6.

**Dateien:** Modify `.github/workflows/orchestration-test.yml` (Digest-Schritte
im `test`-Job, neue `ARTIFACT_TESTS`-Env-Liste, neuer Job `artifacts` mit
`timeout-minutes: 15`) · Create `tests/test_artifact_tests_list.py` (Meta-Test,
IC-7) · Modify `CHANGELOG.md`.

**Schließt:** AC1 (CI), AC4. **Rollback:** Job und Schrittpaar löschen; die
Env-Liste bleibt additiv und unschädlich, kann aber mit entfallen; der
Meta-Test entfällt mit.

### P5 — AC5-Entscheidung (S, 2 Dateien)

**Dateien:** Modify `.github/workflows/validate.yml` (neuer Kommentarblock
oberhalb von `jobs:`, IC-12) · Modify `CHANGELOG.md`. **Schließt:** AC5.
**Rollback:** Doku-Zeilen löschen.

### P6 — Playwright-CI-Pfad (M, 3 Dateien)

**Dateien:** Create `.github/workflows/browser-test.yml` (IC-10) · Create
`tests/requirements-browser.txt` (Playwright-Pin, keine weiteren Extras —
`pytest`/`pytest-xdist` kommen aus `tests/requirements.txt`) · Modify
`CHANGELOG.md`. **Schließt:** AC6. **Rollback:** Workflow-Datei löschen (die
Requirements-Datei ist dann ungenutzt).

## Risiken und Mitigationen

| Risiko | Wirkung | Mitigation |
|---|---|---|
| Unvollständige `ARTIFACT_TESTS` | grüner Job, der nichts beweist | „0 Skips"-Assertion (`-rs` mit Begründungsfilter) + Meta-Test über die Skip-Gates in beiden Richtungen (IC-7) |
| `sync.py` verändert den Baum im `artifacts`-Job | Git-Drift-Assertion schlägt aus falschem Grund fehl | kein Drift-Gate in diesem Job; Gate bleibt exklusiv in `validate.yml` |
| Decoy verliert die Zähne (Hook adoptiert `$PWD`, Test bleibt trotzdem grün) | AC1-Prüfung wird zur Attrappe | Decoy trägt aktives `repo_containment` mit `.tmp`-Sink; ein `$PWD`-adoptierender Hook erlaubt einen relativen Write und wird rot (ADR-3, Invariante 3) |
| P2-Blast-Radius (32 + 31 Dateien) | ein zu knapper Wert tötet einen legitimen langsamen Test unter Last | Werte nur aus IC-2, Defaults ≥ gemessenem Worst Case, Env-Override je Konstante, Bestandsliterale unverändert |
| AST-False-Positive bei Spread/Indirektion | Entwickler umgehen den Check oder er wird abgeschaltet | fail closed für `**kwargs`, Allowlist mit Pflicht-Begründung (`path`/`pattern`/`reason`), Stale-Finding, Alias-Formen unit-getestet |
| Allowlist wird zum Sammelbecken | CHECK bleibt grün, obwohl `timeout=` fehlt | `stale-allowlist-entry` + `allowlist-entry` (unvollständig) als WARNING; Einträge nur für `Popen` zulässig |
| Playwright-Flakiness (Port 7421, Serverstart) | roter Job ohne Codefehler | `-n 0`, dedizierter Port, 20-Minuten-Deckel, optional `continue-on-error: true` für genau eine Runde (OQ-4) |
| Fixture-Refactor beschädigt den AC1-Beweistest | der einzige Regressionsanker fällt weg | Beweistest in P1 unverändert lassen; Bindung nur im Setup-Pfad; ein Parametrize-Block ist die einzige Aufrufstellen-Änderung (IC-3) |
| P1-Revert nach P2a | `SLOW_TIMEOUT`-Importe in sechs Modulen brechen | Revert-Reihenfolge P3 → P2b → P2a → P1 dokumentieren (P1-Rollback) |
| CHANGELOG-Pflicht für drei neue Dateien + fehlenden Rest-Eintrag | Konsistenz-Check `check_changelog_mentions_new_files` schlägt fehl | P1 trägt den Sammel-Eintrag; P2a–P6 je eigener Bullet |
| Doku-Drift `tests/README.md` (Timeout-Tabelle + Follow-up-Satz) | Tabelle behauptet drei Konstanten, Code hat vier | P1 ergänzt Zeile + AC2-Abschnitt, P2b entfernt den Follow-up-Satz (IC-13) |
| AC2-Regression durch neue Jobs | AC2 fällt hinter den Stand zurück | jeder neue Job (P4 `artifacts`, P6 `browser-test`) deklariert `timeout-minutes`; manueller Grep (Evidenz-Matrix) + `CHANGELOG`-Bullet nennt den Wert |

**Rollback je Phase:** P1/P2a/P2b PR-Revert (P1 nur vor P2a unabhängig) · P3
Severity-Flip (1 Zeile) · P4 Job/Schrittpaar + Meta-Test löschen · P5
Doku-Zeilen löschen · P6 Workflow-Datei löschen.

## Offene Fragen

| ID | Frage | Empfohlener Default | Entscheider |
|---|---|---|---|
| **OQ-4** | Soll `browser-test.yml` beim ersten Lauf `continue-on-error: true` bekommen? | **Ja, genau eine Runde**, danach im selben PR entfernen und den Entfall im `CHANGELOG`-Bullet zu P6 nennen. Dauerhaftes `continue-on-error` wäre ein stiller Skip und widerspräche AC6. | User |

**In Rev. 2 geschlossen:**

- **OQ-1 (AC1-Lesart)** — entfällt: AC1 Satz 1 ist mit dem Decoy-Projekt
  wörtlich erfüllbar (ADR-3). Es gibt keine zu bestätigende Sonderlesart mehr.
- **OQ-2 (P2-Größe)** — entfällt: die Vorabmessung ist erfolgt (201 Aufrufe /
  73 Dateien, 64 außerhalb P1); P2 ist in P2a (32) und P2b (31) geteilt.
- **OQ-3 (ERROR vs. WARNING)** — entfällt: die Allowlist enthält ab dem ersten
  Commit die vollständige `Popen`-Menge (2 Einträge), ERROR ist damit auf Anhieb
  verteidigbar (IC-11). Der Escape Hatch bleibt nur als belegter Blocker-Fall.

## Unverified / Messlücken

Diese Punkte sind **nicht** belegt und dürfen im Plan nicht als Faktum
behandelt werden:

1. **Aufrufzahlen.** Rev. 2 misst grep-basiert 201 Aufrufe in 73 Dateien
   (P1-Slice 72 in 9 Modulen); Issue #945 nennt 75/25, Rev. 1 69/10. Kommentare
   und String-Literale sind nicht ausgeschlossen. Autoritativ ist erst der
   P3-Check (AST); die P2a/P2b-Dateilisten stammen aus der Grep-Messung und
   können um einzelne Dateien abweichen.
2. **Vollständigkeit der `Popen`-Menge.** Rev. 2 findet genau zwei
   `Popen(`-Aufrufstellen unter `tests/`; ein `Popen` über Alias/Indirektion
   wäre unsichtbar. Der `stale-allowlist-entry`-Fund und der P3-AST-Lauf klären
   das.
3. **Bestandsliterale > 10.** Nur vier Klassen sind stichprobenartig verifiziert
   (30/120/300/600); 180 stammt aus dem Review-Befund. Die vollständige Liste
   liefert der P3-Check (AST); sie ist vor dem P3-Commit zu sichten, weil P3
   ohne WARNING-Vorlauf direkt als ERROR landet.
4. **Exakte `ARTIFACT_TESTS`-Mitgliedschaft.** Fünf Seed-Module sind über ihre
   Skip-Gates identifiziert; `tests/test_lazy_skills_channel.py` („no skills
   channel"/„native rules channel") ist ein ungeprüfter Kandidat. Die
   Vollständigkeit muss gegen einen **ungesyncten** Checkout neu abgeleitet
   werden.
5. **Laufzeiteffekt der generierten Provider-Bäume** auf Repo-Copy-Fixtures —
   betrifft nur die verworfene In-`test`-Variante (AC4-Wortlaut-Notiz), nicht
   gemessen.
6. **Laufzeit von `tests/browser` (11 Module)** gegen den 20-Minuten-Deckel —
   kein CI-Messwert vorhanden.
7. **Suite-Größe widersprüchlich.** Der Workflow-Header nennt 6575 Tests / 362
   Module; die Wave-3-Messung nennt 6207 / 359. Diese Spec pinnt **keine** Zahl.
8. **`sync.py --validate` grün mit dem neuen Check** auf einem gesyncten
   Checkout — erwartet ja (nach P2a/P2b kein Finding außer den zwei
   Allowlist-Einträgen), nicht ausgeführt.
9. **Fixture-Scoping vs. `-n 2 --dist loadfile`** — erwartet kollisionsfrei
   (modul-scoped, pro Worker), nicht ausgeführt.
10. **Ob die Artefakt-Tests heute tatsächlich überspringen** — die Skip-Gates
    sind belegt, ein Lauf gegen einen ungesyncten Checkout mit `-rs` fehlt
    (AC4-Ausgangslage).
11. **Ob AC1 heute in der CI verletzt wird** — kein Digest vorhanden, also keine
    Aussage über tatsächliche Schreibvorgänge in CI-Läufen.
12. **Design vs. Messung: Browser-Modulzahl.** Design nennt 10 Module, im
    Checkout liegen 11 (`tests/browser/test_*.py`). Das Kriterium „≥ 10" bleibt
    erfüllt; die Zahl im Design ist eine Untergrenze, kein Messwert.

## Revision-Log

| Rev. | Datum | Änderung |
|---|---|---|
| 1 | 2026-10-30 | Erste Spezifikation aus dem Systemdesign vom 2026-10-30: Stand je AC verifiziert, IC-1…IC-13 normiert, Phasen P1…P6 mit Rollback, AC1-Lesart und AC4-Wortlaut-Divergenz dokumentiert, vier offene Fragen, zehn Messlücken. `tests/README.md` als Doku-Pflicht ergänzt (im Design nicht gelistet). |
| 2 | 2026-10-30 | Review Rev. 1 (`CHANGES_REQUESTED`) eingearbeitet. **B1** → ADR-3 (Decoy-Projekt), AC1-Abschnitt neu gefasst, IC-5 auf Lesevorgänge reduziert, OQ-1 gelöscht. **B2** → P4 = 3 Dateien/M inkl. `tests/test_artifact_tests_list.py`, IC-7-Erkennungstoken „not generated in this project" ergänzt. **B3** → IC-10 installiert `tests/requirements.txt` **und** `requirements-browser.txt`. **B4** → IC-11/P3 mit den zwei verbindlichen Allowlist-Einträgen, ERROR ab erstem Commit. **B5** → Messung „201 Aufrufe / 73 Dateien" in „Stand", P2a (32)/P2b (31) ersetzt P2, OQ-2 gelöscht. **B6** → P4 hängt von P1 ab, Parallelitätstabelle korrigiert. **B7** → IC-2 gilt nur für neue Werte; Bestandswert-Tabelle + Nicht-Ziel „keine Vereinheitlichung". **A1** → IC-6 Regel 1 gilt für jeden Subprozess-Aufruf der neun Module. **A2** → IC-4/IC-3 decken `_call` plus sieben direkte `test_hook_common_lib.py`-Aufrufe. **A3** → `timeout=None` ist Finding (IC-6/IC-11), `_scan`-Default wird `SCRIPT_TIMEOUT`. **A4** → IC-12 legt einen **neuen** Block in `validate.yml` an; AC5-Stand korrigiert (`orchestration-test.yml:3-59`). **A5** → IC-3/ADR-2: Basetemp-Guard ist warn-only. **A6** → Allowlist-Schema `path`/`pattern`/`reason` (+`owner`). **A7** → Bindungsmechanismus (Modul-Global + `autouse`-Fixture, ein Parametrize-Block) und P1-Aufwand benannt. **A8** → Problem-Absatz trennt „bereits tmp-basiert" von „nicht isoliert". **A9** → AC2-Evidenz als manueller Grep mit Ort (P1-Doku in `tests/README.md`, Ausführung P4/P6). **A10** → AC4 als Wortlaut-Notiz, Single-Leg-Matrix formell erfüllt, Prämisse der verworfenen Variante als ungemessen markiert. **A11** → P1-Rollback-Grenze nach P2a dokumentiert. **A12** → IC-1 verlangt Docstring-Update in `tests/timeouts.py`. Redaktionell: `tests/manual/**` aus dem Check-Scope ausgeschlossen, Unverified auf 12 Punkte nachgezogen. |

## Trace-Anker

`spec-id: SPEC-test-hygiene-945`

Der Plan referenziert diesen Wert in seinem Trace-Anker und verweist über
`**Spec:** docs/specs/2026-10-30-test-hygiene-945-design.md` auf diese Datei.
Die Datei ist bewusst `*-design.md` benannt, weil
`scripts/lib/consistency/spec_plan.py` nur dieses Muster als Spec klassifiziert.
Die Freigabe erfolgt ausschließlich durch den Nutzer über den maschinenlesbaren
Approval-Marker im Kopf dieser Datei (Wert `APPROVED` mit Datum) — diese
Revision bleibt bewusst `Entwurf`.
