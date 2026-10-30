# Test-Hygiene #945 (Wave 4) — Spec

> spec-id: SPEC-test-hygiene-945
> Status: Entwurf
> Datum: 2026-10-30
> Issue: #945
> Revision: 1
> Grundlage: Systemdesign des `concept-architect` vom 2026-10-30, hier als `## Systemdesign` konserviert (es existiert keine separate Designdatei)
> Verifizierter Stand: `main` @ `3c440c33`, 2026-10-30

## Problem

Issue #945 wurde in Wave 2 nur teilweise geschlossen. Der `CHANGELOG.md`-Eintrag
`[2.0.0-beta.2] - 2026-10-20` sagt selbst „CI robustness (#945, **partial**)".
Übrig bleiben vier offene bzw. unbewiesene Akzeptanzkriterien und zwei
Strukturmängel, die sie verdecken:

- **Hook-Tests schreiben potenziell in den Checkout.** Nur
  `tests/test_orchestrator_guard_hook.py` isoliert sich (modulglobales
  `tempfile.mkdtemp`-Verzeichnis); die übrigen Hook-Module laufen gegen die echte
  Arbeitskopie, und `.claude/hooks/.guard-audit.log` ist gitignored
  (`.gitignore` → `.guard-audit.log`), fällt also niemandem auf.
- **Ungebremste Subprozesse.** `tests/timeouts.py` existiert mit
  `SYNC_TIMEOUT`/`SYNC_VALIDATE_TIMEOUT`/`SCRIPT_TIMEOUT`, aber die
  Hook-Module und rund zwei Dutzend weitere Module setzen weiterhin kein
  `timeout=`. Ein hängendes `bash`-Kind blockiert den Runner bis zum
  Job-Timeout.
- **Artefakt-Tests sind in der CI vermutlich übersprungen** — sie brauchen einen
  gesyncten Baum, und keiner der beiden Workflows synct vor `pytest` in einem
  `test`-Bein.
- **Playwright hat keinen CI-Pfad.** `tests/browser` (11 Module) wird lokal
  gefahren und in der CI nie ausgeführt, ohne dokumentierte Begründung.
- **Kein Regressionsschutz.** Nach dem Fix kann dieselbe Lücke (fehlendes
  `timeout=`, fehlende Isolation) unbemerkt wieder eingebaut werden; es gibt
  keinen Check, der „jeder Aufruf hat `timeout=`" prüft.

## Ziel

Wave 4 schließt #945 vollständig: AC1, AC3, AC4 und AC6 werden umgesetzt, AC5
wird als bewusste Ablehnung dokumentiert; AC2 bleibt unverändert (bereits
erfüllt) und wird nur gegen Regression abgesichert. Der Fix ist in sechs
phasenweise mergebare PRs zerlegt, damit jeder Schritt einzeln revertierbar ist
und die Isolation nicht mit der repo-weiten Timeout-Adoption kollidiert. Neu
ist ein AST-basierter Konsistenz-Check, der `timeout=` als Pflicht macht statt
als Konvention.

**Scope:** `tests/`, `.github/workflows/`, `scripts/lib/consistency/`,
`scripts/consistency-check.py`, `.meta-config/`, `CHANGELOG.md`, `tests/README.md`.

## Nicht-Ziele

- Kein `pytest-timeout`, kein `pytest-rerunfailures`, keine neue Test-Dependency
  außer dem Browser-Extra (`tests/requirements-browser.txt`).
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
- Keine Per-Test-Zeitbudgets, keine Performance-Assertions, keine
  provider-spezifischen Verzweigungen.
- Keine Korrektur der historischen Release-Notiz „`pytest -n auto`" in
  `CHANGELOG.md` (`[2.0.0-beta.2]`) — Release-Text bleibt historisch.

## Stand

Verifiziert am 2026-10-30 gegen `main` `3c440c33`. Jede Zeile nennt die
Fundstelle als `datei:symbol` (bzw. `datei:zeile` nur dort, wo der Stand aus
einer Zeilennummer stammt und die Zeile stabil ist).

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

### AC1 — teilweise erfüllt

- `tests/test_orchestrator_guard_hook.py:_PROJECT_ROOT` legt ein
  `tempfile.mkdtemp`-Projekt an, kopiert `.meta-config/project.yaml`, erzeugt
  `.claude/hooks/` und räumt per `atexit` auf; `_run_hook` und
  `_bash_payload` verwenden dieses Verzeichnis als `cwd`.
- `tests/test_orchestrator_guard_hook.py::test_strict_cases_never_write_the_repo_audit_log`
  ist der Beweistest: Byte-Vergleich der echten `.guard-audit.log` vor/nach
  einem Hook-Lauf (`read_bytes() if exists() else None`).
- `tests/test_repo_containment_hook.py::_run_hook` nutzt bewusst
  `process_cwd=_REPO_ROOT` als Default (die zu prüfende Eigenschaft ist „der
  Root kommt aus dem Payload, nie aus `$PWD`").
- `tests/test_hook_common_lib.py::_call`, `tests/test_graphify_guard_hooks.py`
  (drei Runner-Aufrufe), `tests/test_dod_push_check_hook.py`,
  `tests/test_artifact_freshness_hook.py`, `tests/test_pre_release_check_hook.py`,
  `tests/test_auto_github_release_hook.py`, `tests/test_release_gate_checksums.py`
  setzen kein `cwd=` bzw. kein Hook-Projekt — sie laufen gegen den Checkout.
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
- Hook-Slice: `grep` über die Hook-Test-Module findet 69
  `subprocess.run`/`Popen`/`check_output`/`check_call`-Treffer in 10 Modulen
  (darunter zwei, die nicht im P1-Scope liegen:
  `tests/test_antigravity_hooks_registration.py`,
  `tests/test_hook_registration_invariant.py`). Nur 4 Aufrufe sind gebremst
  (die `SCRIPT_TIMEOUT`-Stellen in `test_antigravity_hooks_registration.py`).
  Die Zählung ist grep-basiert und kann abgeschnitten sein — die
  autoritative Zahl liefert der P3-Check.
- Issue-Behauptung „75 Aufrufe / 25 Dateien repo-weit" ist **unverifiziert**
  (derselbe grep-Vorbehalt).
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
  `tests/test_mcp_role_tools.py` (`"e2e-tester not generated in this project"`).

### AC5 — unverifiziert

- `validate.yml` → Job `compat-311` ist ein gezielter 9-Datei-Job (`TOML
  boundary + code hygiene`, Python 3.11 fest); es gibt keine
  Szenario-Matrix über mehrere Python-Versionen.
- Der Job `scenarios` pinnt Python 3.11 (`setup-python` → `'3.11'`) und shardet
  nur (4 Shards), nicht nach Version.
- Es gibt keine dokumentierte Entscheidung dazu — weder im Workflow-Header
  (`validate.yml:1-24` beschreibt nur Jobaufteilung und Timeouts) noch im
  `CHANGELOG.md`.

### AC6 — nicht erfüllt

- Kein Workflow enthält `playwright` (beide Workflow-Dateien geprüft).
- `tests/requirements.txt` enthält `pytest`, `pyyaml`, `questionary`, `tomli`
  (nur <3.11), `jsonschema`, `pytest-xdist`, `pytest-split` — kein Playwright.
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
vollständig konserviert, damit Plan und Review eine stabile Referenz haben).

### Phasenzerlegung (Merge-Reihenfolge)

Größenklassen nach F7: **S** ≤ 2 Dateien, **M** 3–8, **L** 9–20, **XL** > 20.

| Phase | Inhalt | Größe | Dateien | Schließt | Abhängigkeit |
|---|---|---|---|---|---|
| **P1** | Timeout-Contract + Hook-Slice-Isolation | L | 14 | AC1 (lokal beweisbar), AC3 (Hook-Slice) | — |
| **P2** | Repo-weite Timeout-Adoption außerhalb des Hook-Slice | L–XL | ≈18–28 | AC3 (Rest) | strikt nach P1 |
| **P3** | Vollständigkeits-Check (`subprocess-timeout-missing`) | M | 5 | AC3 (Beweis) | strikt nach P2 |
| **P4** | CI-Beweis + Artefakt-Job | M | 2 | AC1 (CI), AC4 | parallel zu P1/P5/P6 möglich |
| **P5** | AC5-Entscheidung dokumentiert | S | 1–2 | AC5 | parallel |
| **P6** | Playwright-CI-Pfad | M | 3 | AC6 | parallel |

Merge-Reihenfolge: **P1 → P2 → P3 strikt sequenziell** (P2 und P3 teilen die
Konstanten und die Dateimenge; P3 ist als ERROR nur bei null Verstößen
verteidigbar). **P4, P5, P6 sind untereinander und gegen P1 parallelisierbar**;
P4 setzt allerdings die Hook-Module aus P1 voraus, weil der Digest-Schritt sie
in der Remainder-Menge erwartet.

### ADR-1 — Timeout-Mechanismus: Konstanten + explizite Adoption + AST-Check

- **Kontext:** AC3 verlangt `timeout=` an jedem `subprocess.run` in den Tests.
  Ein Hang-Guard muss einen blockierten Kindprozess töten, darf aber einen
  langsam-arbeitenden Test auf einem 2-Kern-Runner nicht rot machen.
- **Entscheidung:** zentrale Konstanten in `tests/timeouts.py`, explizite
  Adoption pro Aufrufstelle, Presence-Check per AST im
  `sync.py --validate`-Pfad.
- **Konsequenzen:** der Satz „Hang-Guard, keine Performance-Zusicherung" bleibt
  wörtlich wahr. Der Check prüft **nur die Anwesenheit** von `timeout=`, nicht
  die Richtigkeit des Werts — das ist bewusst und muss so dokumentiert bleiben.
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

### ADR-2 — Isolation: gemeinsame Fixture statt Modul-Globals

- **Kontext:** AC1 verlangt `tmp_path`-Projekte für alle Hook-Tests; heute
  arbeitet genau ein Modul isoliert, und zwar über ein modulglobales
  `mkdtemp`+`atexit`-Paar, das pytest nicht kennt.
- **Entscheidung:** eine modul-scoped Fixture `hook_project_root` in
  `tests/conftest.py`, die `tmp_path_factory` nutzt. pytest räumt auf, der
  `--basetemp`-Guard aus `conftest.py` greift, und die Fixture ist unter
  `-n 2 --dist loadfile` pro Worker/Modul einmalig.
- **Konsequenzen:** gleiche Semantik wie heute für das Guard-Modul, aber
  auffindbar und in allen Hook-Modulen wiederverwendbar. Der Beweistest bleibt
  unangetastet (er ist der Regressionsanker für die Fixture-Umstellung).
- **Verworfen:** `monkeypatch.chdir` (ändert nur den Prozess-CWD, nicht den
  `cwd=` des Kindes und nicht `$CLAUDE_PROJECT_DIR`), globale Session-Fixture
  (ein Projekt für alle Tests maskiert Cross-Test-Leaks).

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
- Kein Test definiert danach ein modul-lokales `RUN_TIMEOUT`; die sechs
  Vorkommen werden auf `SLOW_TIMEOUT` umgestellt.

### IC-2 — Mapping-Regel: Aufrufklasse → Konstante

| Aufrufklasse | Konstante | Default | Env-Override |
|---|---|---|---|
| Bash-Hook unter Test | `SCRIPT_TIMEOUT` | 60 | `AGENT_META_SCRIPT_TIMEOUT` |
| Git-Plumbing (`git status`, `git commit`, `git add`) | `SCRIPT_TIMEOUT` | 60 | `AGENT_META_SCRIPT_TIMEOUT` |
| `bash -c`-Schnipsel (Sourcing von `hook_common.sh`) | `SCRIPT_TIMEOUT` | 60 | `AGENT_META_SCRIPT_TIMEOUT` |
| Helper-CLI (Eval-Wrapper, Hook-Adapter) | `SCRIPT_TIMEOUT` | 60 | `AGENT_META_SCRIPT_TIMEOUT` |
| `sync.py` ohne `--validate` | `SYNC_TIMEOUT` | 180 | `AGENT_META_SYNC_TIMEOUT` |
| `sync.py --validate` | `SYNC_VALIDATE_TIMEOUT` | 180 (Fallback `SYNC_TIMEOUT`) | `AGENT_META_SYNC_VALIDATE_TIMEOUT` |
| Langläufer-CLI in Tests (meta_optimizer-Familie) | `SLOW_TIMEOUT` | 900 | `AGENT_META_SLOW_TIMEOUT` |
| One-Shot-Readiness-Probe (`git --version`) | Literal | ≤ 10, empfohlen 5 | — |

**Per-Call-Site-Override-Regel:** ein abweichender Wert ist nur als **benannte
Konstante** zulässig oder als Literal ≤ 10 für eine Readiness-Probe. Ein
nacktes Literal > 10 an einer Stelle, die nicht in die Tabelle passt, ist ein
Spec-Verstoß und braucht eine neue Tabellenzeile (Spec-Revision), keine
Inline-Ausnahme.

**Check-Semantik:** `test.subprocess-timeout-missing` prüft die **Anwesenheit**
von `timeout=`; er behauptet nicht, den Wert zu beweisen. `Popen` hat keinen
`timeout`-Parameter → nur Allowlist-Eintrag (Datei + Begründung) mit eigenem
Finding `subprocess-timeout.stale-allowlist-entry`.

### IC-3 — Fixture-Contract `hook_project_root`

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
- **Semantik:** ersetzt den `mkdtemp`+`atexit`-Block in
  `tests/test_orchestrator_guard_hook.py` (Zeilenbereich um `_PROJECT_ROOT`)
  eins zu eins; pytest räumt auf, der `--basetemp`-Guard aus `conftest.py`
  bleibt wirksam.
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
| `test_orchestrator_guard_hook.py` | `hook_project_root` | `SCRIPT_TIMEOUT` | Fixture-Umzug; `STRICT_CASES` via kopierter `project.yaml`; Beweistest unverändert |
| `test_hook_common_lib.py` | `hook_project_root` (`_call`) | `SCRIPT_TIMEOUT` | PATH/HOME bleiben echt (`command -v python3`); `hook_audit_log_append`-Tests schreiben bereits in explizite `tmp_path`-Logs |
| `test_graphify_guard_hooks.py` | `tmp_path` (drei Runner) | `SCRIPT_TIMEOUT` | `env` bleibt das reduzierte PATH-Dict |
| `test_dod_push_check_hook.py` | bereits `tmp`-basiert | `SCRIPT_TIMEOUT` | nur `timeout=` |
| `test_artifact_freshness_hook.py` | bereits `tmp`-basiert | `SCRIPT_TIMEOUT` | nur `timeout=` |
| `test_pre_release_check_hook.py` | bereits `tmp`-basiert | `SCRIPT_TIMEOUT` | nur `timeout=` |
| `test_auto_github_release_hook.py` | bereits `tmp`-basiert | `SCRIPT_TIMEOUT` | nur `timeout=` |
| `test_release_gate_checksums.py` | bereits `tmp`-basiert | `SCRIPT_TIMEOUT` | nur `timeout=` |
| `test_repo_containment_hook.py` | **bewusst `_REPO_ROOT`** | `SCRIPT_TIMEOUT` | siehe IC-5; zusätzlich ein Docstring-Satz und ein Eintrag im neuen Guard-Test |

### IC-5 — Ausnahmen mit echten-Checkout-Semantik (verbindliche Liste)

Diese Stellen bleiben gegen den echten Checkout, jeweils mit Begründung im Code:

1. `tests/test_repo_containment_hook.py::_run_hook` — Default `cwd=_REPO_ROOT`
   ist die geprüfte Eigenschaft („Root kommt aus dem Payload, nie aus `$PWD`").
   Ein `tmp_path`-Default würde den Test entwerten.
2. `tests/test_antigravity_hooks_registration.py` — prüft `git status
   --porcelain` des echten Repos (Registrierung darf nichts verändern).
3. `tests/test_agent_eval_framework.py` — liest das gerenderte
   `.claude/agents/orchestrator.md`.
4. `tests/test_orchestrator_guard_hook.py::test_header_lists_known_gaps` und die
   `_IMPL_PATH`-Lesevorgänge — lesen die echte Hook-Implementierung.

**Warum diese Stellen den Audit-Log nicht schreiben können:** `hook_audit_log_append`
(`hooks/1-generic/lib/hook_common.sh`) hat genau einen Aufrufer,
`hooks/1-generic/orchestrator-guard-impl.sh:421`; die
`repo-containment*.sh`-Hooks enthalten keinen Audit-Schreibvorgang (grep). Die
verbleibenden Ausnahmen betreffen `git status`, Datei-Lesevorgänge und die
Registrierungsprüfung. P4's Vorher/Nachher-Digest fängt jede künftige Änderung
dieser Eigenschaft.

### IC-6 — Statischer Guard-Test `tests/test_hook_test_isolation.py` (neu)

- **Eingabe:** alle Hook-Test-Module (Mindestmenge: die neun P1-Module).
- **Verfahren:** `ast`-Parse; für jeden Aufruf von `subprocess.run` /
  `subprocess.call` / `subprocess.check_output` / `subprocess.check_call` /
  `subprocess.Popen`, dessen argv ein `orchestrator-guard`-Literal enthält, ist
  ein `cwd=`-Keyword-Argument Pflicht.
- **Fehlerbild:** ein Finding, das Datei + Funktionsname nennt; kein
  Repo-Schreibvorgang, keine Ausführung des Hooks.
- **Nicht-Zusicherung:** der Test beweist nicht, dass `cwd` auf ein
  `tmp_path`-Verzeichnis zeigt (das leistet der Laufzeit-Beweistest plus der
  CI-Digest).

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
- **Meta-Test (repo-lokal):** jedes Modul, das `_skip_unless_generated` oder
  `pytest.skip("... run sync.py")`/`"unsynced checkout"`/`"generated roots
  absent"` enthält, muss in `ARTIFACT_TESTS` stehen. Seed:
  `tests/test_opencode_agents.py`, `tests/test_agent_eval_framework.py`,
  `tests/test_reference_standards_documented.py`,
  `tests/test_legacy_registries_removed.py`, `tests/test_mcp_role_tools.py`.

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

- **Matrix:** eine Achse, `python-version: ['3.12']` (Single-Leg).
- **`timeout-minutes: 15`.**
- **Steps in dieser Reihenfolge:** Checkout → `actions/setup-python` (Cache auf
  `tests/requirements.txt`) → `pip install -r tests/requirements.txt` →
  `python scripts/sync.py` → `python -m pytest -q -n 0 $ARTIFACT_TESTS -rs --tb=short`
  → Assertion „0 Skips mit Begründung `generated` / `run sync.py` / `unsynced`
  / `generated roots absent`".
- **Kein Drift-Gate in diesem Job.** Das Gate bleibt ausschließlich in
  `validate.yml` (`Check generated files are committed`); ein `sync.py`-Lauf
  hier darf nicht als zweites Gate wirken.
- **Kein Leg des `test`-Jobs:** ein gesyncter Checkout schiebt `Claude/`,
  `.opencode/`, `.gemini/` usw. in jede Repo-Copy-Fixture; die 17
  Heavy-Fixture-Module sind von genau diesen Kopien setup-dominiert.
- **Verworfene Alternative:** Sync-Step im `test`-Job unter
  `if: matrix.shard == 1 && matrix.python-version == '3.12'` — bläht die
  Repo-Copy-Fixtures dieses Legs auf und riskiert die 30-Minuten-Grenze.

### IC-10 — Workflow `browser-test.yml` (AC6, P6)

- **Datei:** `.github/workflows/browser-test.yml` (neu).
- **`timeout-minutes: 20`.**
- **Trigger:** `push`/`pull_request` mit Pfadfilter analog
  `orchestration-test.yml` (u. a. `scripts/**`, `tests/**`, `config/**`,
  die Workflow-Datei selbst).
- **Steps:** Checkout → `setup-python` → `pip install -r
  tests/requirements-browser.txt` → `python -m playwright install --with-deps
  chromium` → `python -m pytest tests/browser -q -n 0`.
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
  Klammerung und `# noqa` sind irrelevant). `scripts/` bleibt außerhalb (dort
  gilt `temp_literals.check_subprocess_env_pinning`).
- **Pflicht-Keywords:** `run`, `call`, `check_output`, `check_call` brauchen
  `timeout=`. `Popen` ist allowlist-only.
- **Alias-Auflösung:** `import subprocess as sp` und
  `from subprocess import run` werden aufgelöst; `**kwargs`-Spread → **fail
  closed** (Finding), weil die Anwesenheit nicht statisch bewiesen ist.
- **Findings:** `test.subprocess-timeout-missing` (Severity **ERROR**),
  `subprocess-timeout.stale-allowlist-entry` (WARNING) für Allowlist-Einträge
  ohne Treffer.
- **Allowlist:** `.meta-config/subprocess-timeout-allowlist.yaml`, Schema wie
  die bestehende `temp-literal-allowlist.yaml` (Top-Level `entries:` mit
  `file` und `reason`); ein Eintrag ohne Begründung ist ungültig. Das Laden
  darf nie werfen (Muster: `temp_literals._load_allowlist_entries`).
- **Registrierung:** `scripts/consistency-check.py` importiert
  `check_subprocess_timeout` aus `lib.consistency.subprocess_timeout` und ruft
  ihn im globalen Cross-Reference-Block direkt neben `check_py39_union_syntax`
  auf. Damit läuft er in `sync.py --validate` auf 3.9/3.11/3.12.
- **Kein Baseline-File.** Eine Baseline wäre die „jeder"-Lüge: sie würde
  bestehende Verstöße als akzeptabel einfrieren.
- **Unit-Tests:** `tests/test_subprocess_timeout_guard.py` als Spiegel von
  `tests/test_python_compat_consistency.py` (tmp-Fixtures, Finding-Code,
  Alias-Formen, `**kwargs`, Popen-Allowlist, stale entry) plus ein
  Registrierungs-Meta-Test, der belegt, dass der Check im
  `consistency-check.py`-Pfad aufgerufen wird.

### IC-12 — AC5-Dokumentations-Contract (P5)

- **Ort:** Header von `.github/workflows/validate.yml` (Kommentarblock oberhalb
  der Jobs, aktuell der Erläuterungsblock zur Jobaufteilung).
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
  Follow-up." P1 ergänzt die `SLOW_TIMEOUT`-Zeile; P2 entfernt/aktualisiert den
  Follow-up-Satz, sobald die Vereinheitlichung abgeschlossen ist.
- `CHANGELOG.md`: P1 trägt den Sammel-Eintrag „CI robustness (#945, residual)";
  P2–P6 ergänzen je ihren eigenen Bullet unter `## [Unreleased]`, sobald sie
  Dateien anlegen. Kein Eintrag in eine abgeschlossene Release-Sektion.
- Commit-Messages: Conventional Commits, Englisch, ≤ 72 Zeichen erste Zeile.

## Datenfluss

**Lokaler Hook-Testlauf (nach P1):** `pytest` sammelt Modul → Fixture
`hook_project_root` erzeugt `tmp`-Root mit `project.yaml` und
`.claude/hooks/` → Test baut PreToolUse-JSON mit `cwd=<root>` → `subprocess.run`
startet `bash hook` mit `cwd=<root>`, `env` ohne `CLAUDE_PROJECT_DIR` und
`timeout=SCRIPT_TIMEOUT` → Hook löst Projekt-Root aus Payload/`$PWD` auf, liest
`project.yaml`, schreibt ggf. `<root>/.claude/hooks/.guard-audit.log` →
Exitcode wird asserted. Der echte Checkout bleibt unberührt; der Beweistest
vergleicht die echte Logdatei byteweise vor/nach.

**CI-`test`-Job (nach P4):** Checkout → `pip install` → Partition validieren →
**Digest vorher** (`sha256` oder `absent`) → Heavy-Fixture-Slice → Remainder
(enthält alle Hook-Module) → **Digest nachher + Vergleich** → bei Shard 1
`sync.py --validate`.

**CI-`artifacts`-Job (nach P4):** Checkout → install → `sync.py` (rendert
Provider-Bäume) → `pytest $ARTIFACT_TESTS -rs` → Skip-Assertion. Kein
Drift-Gate, keine Parallelität (`-n 0`).

**CI-`browser-test.yml` (nach P6):** Checkout → install
`requirements-browser.txt` → Chromium installieren → `pytest tests/browser -n 0`
→ `conftest.py` startet einen `admin-server` auf 7421, wartet auf HTTP-Antwort,
gibt URL aus, beendet den Prozess im `finally`.

**Konsistenz-Check (nach P3):** `sync.py --validate` → `consistency-check.py`
→ `check_subprocess_timeout(root)` → AST über `tests/**/*.py` → Finding je
fehlendem `timeout=` (ERROR) → Exitcode des Validators.

## Acceptance Criteria

Die sechs Kriterien aus Issue #945, **wörtlich** (nicht umformuliert):

> **AC1:** Alle Hook-Tests arbeiten gegen ein `tmp_path`-Projekt. Nach einem vollständigen Testlauf ist `.claude/hooks/.guard-audit.log` unverändert.

> **AC2:** Jeder CI-Job hat `timeout-minutes` gesetzt.

> **AC3:** Jeder `subprocess.run`-Aufruf in den Tests hat `timeout=`.

> **AC4:** Die Artefakt-Tests laufen in der CI, weil der Sync vor pytest in einem Matrix-Bein ausgeführt wird.

> **AC5:** Szenario-Suite-Entscheidung für mehrere Python-Versionen ist getroffen und dokumentiert (Umsetzung oder bewusste Ablehnung).

> **AC6:** Playwright-Tests haben einen CI-Pfad oder eine dokumentierte Begründung, warum nicht.

### AC1 — normative Lesart (verbindlich, nicht stillschweigend „repariert")

AC1 Satz 1 ist für `tests/test_repo_containment_hook.py` nicht wörtlich
erfüllbar, ohne die geprüfte Eigenschaft zu zerstören (der Hook muss gegen eine
Wurzel laufen, die `$PWD` **ist** und trotzdem nicht adoptiert wird). Bindende
Lesart:

> „Kein Hook-Test schreibt in den Checkout; jede Hook-Ausführung bekommt
> entweder ein `tmp`-Projekt als Wurzel oder eine dokumentierte
> Echt-Checkout-Begründung."

Beobachtbar — und damit der eigentliche Contract — ist AC1 Satz 2: die echte
`.claude/hooks/.guard-audit.log` ist nach einem vollständigen Lauf unverändert
(byte-gleich oder weiterhin abwesend). Diese Lesart ist eine
Spec-Interpretation und liegt als OQ-1 dem Nutzer zur Bestätigung vor.

### AC4 — Wortlaut-Divergenz (dokumentiert, nicht kaschiert)

AC4 sagt „in einem Matrix-Bein". Der neue `artifacts`-Job ist ein **Single-Leg**
(`python-version: ['3.12']`). Das erfüllt die Absicht (Sync vor pytest in einem
CI-Matrix-Job), nicht den Buchstaben (mehrere Beine). Die Alternative — Sync im
`test`-Job unter `if: matrix.shard == 1 && matrix.python-version == '3.12'` —
wurde aus Laufzeitgründen verworfen (IC-9). Divergenz ist im `CHANGELOG`-Eintrag
zu P4 zu benennen.

### Evidenz-Matrix

| AC | Evidenz | Phase | Status nach Wave 4 |
|---|---|---|---|
| **AC1** | statisch: `tests/test_hook_test_isolation.py` (cwd-Pflicht für `orchestrator-guard`-argv) · lokal: `test_strict_cases_never_write_the_repo_audit_log` (Byte-Vergleich) · CI: sha256 vor/nach je Shard (IC-8) | P1, P4 | erfüllt (unter OQ-1-Lesart) |
| **AC2** | bereits erfüllt; Regressions-Grep über beide Workflows (jeder Job hat `timeout-minutes`, inkl. der neuen Jobs aus P4/P6) | P4, P6 | erfüllt (bereits) |
| **AC3** | Finding `test.subprocess-timeout-missing` (ERROR) aus `check_subprocess_timeout`, registriert in `scripts/consistency-check.py` neben `check_py39_union_syntax`, läuft via `sync.py --validate` auf 3.9/3.11/3.12 · AST über `tests/**/*.py`, Aliase aufgelöst, `**kwargs` fail-closed, `Popen` allowlist-only, keine Baseline · Unit-Tests + Registrierungs-Meta-Test | P1, P2, P3 | erfüllt |
| **AC4** | Job `artifacts` grün und „0 Skips mit Begründung `generated`/`run sync.py`" (`-rs`) · Meta-Test, dass jedes Skip-Gate-Modul in `ARTIFACT_TESTS` steht | P4 | erfüllt (Single-Leg, siehe Divergenz) |
| **AC5** | dokumentierte Entscheidung in `validate.yml`-Header, konsistent mit der Abwesenheit eines Per-Version-Szenario-Beins | P5 | erfüllt (Ablehnung dokumentiert) |
| **AC6** | `.github/workflows/browser-test.yml` existiert und ist grün; ≥ 10 gesammelte Module in `tests/browser` (Ist: 11); 0 Playwright-Skips | P6 | erfüllt |

## Phasen

Reihenfolge und Abhängigkeiten: **P1 → P2 → P3** strikt; **P4 / P5 / P6**
parallel untereinander und gegen P1.

### P1 — Timeout-Contract + Hook-Slice-Isolation (L, 14 Dateien)

**Dateien (Modify/Create):**

- Modify: `tests/timeouts.py` (nur `SLOW_TIMEOUT`, IC-1)
- Modify: `tests/conftest.py` (Fixture `hook_project_root`, IC-3)
- Modify: `tests/test_orchestrator_guard_hook.py` (Fixture-Umzug, `timeout=`)
- Modify: `tests/test_repo_containment_hook.py` (`timeout=`, Docstring-Satz)
- Modify: `tests/test_hook_common_lib.py` (`cwd=`, `timeout=`)
- Modify: `tests/test_graphify_guard_hooks.py` (`cwd=tmp_path`, `timeout=`)
- Modify: `tests/test_dod_push_check_hook.py` (`timeout=`)
- Modify: `tests/test_artifact_freshness_hook.py` (`timeout=`)
- Modify: `tests/test_pre_release_check_hook.py` (`timeout=`)
- Modify: `tests/test_auto_github_release_hook.py` (`timeout=`)
- Modify: `tests/test_release_gate_checksums.py` (`timeout=`)
- Create: `tests/test_hook_test_isolation.py` (IC-6)
- Modify: `tests/README.md` (Timeout-Tabelle + `SLOW_TIMEOUT`-Zeile; Begründung
  siehe „Abweichungen" im Rückgabebericht)
- Modify: `CHANGELOG.md` (`[Unreleased]`-Sammel-Eintrag „CI robustness (#945, residual)")

**Interne Commit-Reihenfolge:** (1) `tests/timeouts.py` (`SLOW_TIMEOUT`,
importierbar, noch ungenutzt) → (2) `tests/conftest.py`-Fixture + `cwd=`-Umstellung
in den Hook-Modulen → (3) `timeout=`-Adoption in allen P1-Modulen. So ist jeder
Commit für sich grün und die Fixture-Umstellung vom Timeout-Thema getrennt.

**Warum ein PR:** AC1 und AC3 berühren dieselben Helfer (`_run_hook`, `_call`);
getrennte PRs würden in jedem Helfer-Hunk kollidieren.

**Schließt:** AC1 (lokal beweisbar), AC3 (Hook-Slice).
**Rollback:** PR-Revert; die Fixture ist additiv, `SLOW_TIMEOUT` ist ungenutzt,
solange kein Modul es importiert.

### P2 — Repo-weite Timeout-Adoption (L–XL, ≈18–28 Dateien)

**Seed-Kandidaten (grep, unvollständig; autoritative Menge = P3 bei null
Verstößen):** `tests/test_agent_eval_framework.py`, `tests/test_migration_paths.py`,
`tests/test_admin_server.py`, `tests/test_tmp_sink_migration_error.py`,
`tests/test_provider_reactivation_artifacts.py`, `tests/test_tmp_paths_builder.py`,
`tests/test_context_budget_checks.py`, `tests/test_context_report.py`,
`tests/test_tmp_sink_output_dirs.py`, `tests/test_gitignore_shadowing.py`,
`tests/test_active_set_consumers_identity.py`, `tests/test_context_anchors.py`,
`tests/test_dispatch_depth_and_hard_cap.py`, `tests/test_standalone_export_in_sync.py`,
`tests/test_audit_config_readonly.py`, `tests/test_only_variables_updates_context_806.py`,
`tests/test_docker_image_scan_multi.py`, `tests/test_provider_matrix_sync.py`,
`tests/test_doctor_cli.py`, `tests/test_backup_round_trip_804.py`,
`tests/test_context_filename_settings.py`, `tests/test_ac01_render_identity.py`,
und die sechs `tests/test_meta_optimizer_*.py`-Module.

**Inhalt:** `timeout=` nach IC-2 ergänzen; die sechs lokalen
`RUN_TIMEOUT = 900`-Definitionen auf `SLOW_TIMEOUT` umstellen und die
Importe auf `from tests.timeouts import SLOW_TIMEOUT` ziehen; `tests/README.md`
Follow-up-Satz aktualisieren; `CHANGELOG.md`-Bullet.

**Größenrisiko:** übersteigt die Ist-Menge 20 Dateien, ist die Phase XL und
wird nach OQ-2 geteilt (P2a/P2b) — die Mapping-Tabelle bleibt dieselbe.

**Schließt:** AC3 (Rest). **Rollback:** PR-Revert; Werte stammen ausschließlich
aus der Tabelle, Defaults ≥ gemessenem Worst Case.

### P3 — Vollständigkeits-Check (M, 5 Dateien)

**Dateien:** Create `scripts/lib/consistency/subprocess_timeout.py` (IC-11) ·
Modify `scripts/consistency-check.py` (+2 Zeilen: Import + Aufruf neben
`check_py39_union_syntax`) · Create `tests/test_subprocess_timeout_guard.py` ·
Create `.meta-config/subprocess-timeout-allowlist.yaml` · Modify `CHANGELOG.md`.

**Severity:** ERROR. Nur bei null Verstößen verteidigbar, daher strikt nach P2.
**Escape Hatch:** als WARNING landen und in einem Folge-Commit auf ERROR
flippen (1 Zeile) — nur falls P2 nicht rechtzeitig auf null kommt.
**Schließt:** AC3 (Beweis). **Rollback:** Severity auf WARNING stellen (1 Zeile)
oder Check-Aufruf entfernen.

### P4 — CI-Beweis + Artefakt-Job (M, 2 Dateien)

**Dateien:** Modify `.github/workflows/orchestration-test.yml` (Digest-Schritte
im `test`-Job, neue `ARTIFACT_TESTS`-Env-Liste, neuer Job `artifacts`) ·
Modify `CHANGELOG.md`.

**Schließt:** AC1 (CI), AC4. **Rollback:** Job und Schrittpaar löschen; die
Env-Liste bleibt additiv und unschädlich, kann aber mit entfallen.

### P5 — AC5-Entscheidung (S, 1–2 Dateien)

**Dateien:** Modify `.github/workflows/validate.yml` (Header-Kommentar, IC-12) ·
Modify `CHANGELOG.md`. **Schließt:** AC5. **Rollback:** Doku-Zeilen löschen.

### P6 — Playwright-CI-Pfad (M, 3 Dateien)

**Dateien:** Create `.github/workflows/browser-test.yml` (IC-10) · Create
`tests/requirements-browser.txt` (Playwright-Pin, keine weiteren Extras) ·
Modify `CHANGELOG.md`. **Schließt:** AC6. **Rollback:** Workflow-Datei löschen
(die Requirements-Datei ist dann ungenutzt).

## Risiken und Mitigationen

| Risiko | Wirkung | Mitigation |
|---|---|---|
| Unvollständige `ARTIFACT_TESTS` | grüner Job, der nichts beweist | „0 Skips"-Assertion (`-rs` mit Begründungsfilter) + Meta-Test über die Skip-Gates |
| `sync.py` verändert den Baum im `artifacts`-Job | Git-Drift-Assertion schlägt aus falschem Grund fehl | kein Drift-Gate in diesem Job; Gate bleibt exklusiv in `validate.yml` |
| P2-Blast-Radius (≈18–28 mechanische Dateien) | ein zu knapper Wert tötet einen legitimen langsamen Test unter Last | Werte nur aus der Tabelle, Defaults ≥ gemessenem Worst Case, Env-Override je Konstante |
| AST-False-Positive bei Spread/Indirektion | Entwickler umgehen den Check oder er wird abgeschaltet | fail closed für `**kwargs`, Allowlist mit Pflicht-Begründung, Stale-Finding, Alias-Formen unit-getestet |
| Playwright-Flakiness (Port 7421, Serverstart) | roter Job ohne Codefehler | `-n 0`, dedizierter Port, 20-Minuten-Deckel, optional `continue-on-error: true` für genau eine Runde (OQ-4) |
| Fixture-Refactor beschädigt den AC1-Beweistest | der einzige Regressionsanker fällt weg | Beweistest in P1 unverändert lassen; Fixture-Austausch nur im Setup-Pfad |
| Verbleibendes Echt-Checkout-Modul (`test_repo_containment_hook.py`) | AC1 wirkt unvollständig | statischer Guard-Test + CI-Digest + begründete Ausnahmeliste (IC-5) |
| CHANGELOG-Pflicht für drei neue Dateien + fehlenden Rest-Eintrag | Konsistenz-Check `check_changelog_mentions_new_files` schlägt fehl | P1 trägt den Sammel-Eintrag; P2–P6 je eigener Bullet |
| Doku-Drift `tests/README.md` (Timeout-Tabelle + Follow-up-Satz) | Tabelle behauptet drei Konstanten, Code hat vier | P1 ergänzt die Zeile, P2 entfernt den Follow-up-Satz (IC-13) |
| AC2-Regression durch neue Jobs | AC2 fällt hinter den Stand zurück | jeder neue Job (P4 `artifacts`, P6 `browser-test`) deklariert `timeout-minutes` |

**Rollback je Phase:** P1/P2 PR-Revert · P3 Severity-Flip (1 Zeile) · P4
Job/Schrittpaar löschen · P5 Doku-Zeilen löschen · P6 Workflow-Datei löschen.

## Offene Fragen

| ID | Frage | Empfohlener Default | Entscheider |
|---|---|---|---|
| **OQ-1** | AC1 Satz 1 ist für `test_repo_containment_hook.py` nicht wörtlich erfüllbar. Wird die bindende Lesart („kein Schreibvorgang in den Checkout; jede Hook-Ausführung mit tmp-Wurzel oder dokumentierter Echt-Checkout-Begründung", Contract = Satz 2) akzeptiert? | **Ja, Lesart übernehmen.** Sie ist die einzige, die die geprüfte Eigenschaft („Root aus Payload, nie `$PWD`") erhält, und der beobachtbare Contract bleibt Satz 2. | User |
| **OQ-2** | Überschreitet P2 nach der P3-Messung 20 Dateien (XL)? Dann greift die F7-Grenze. | **Bei > 20 Dateien in P2a/P2b teilen** (gleiche Mapping-Tabelle, P2a = Hook-nahe/CLI-Module, P2b = Fixture-/Kontext-Module). Bei ≤ 20 Dateien ungeteilt lassen. | User |
| **OQ-3** | Landet `test.subprocess-timeout-missing` sofort als ERROR oder zuerst als WARNING mit Flip? | **ERROR**, wie im Design — nur bei null Verstößen. Kommt P2 nicht rechtzeitig auf null, WARNING landen und den Flip als Folge-Issue führen (1 Zeile). | User |
| **OQ-4** | Soll `browser-test.yml` beim ersten Lauf `continue-on-error: true` bekommen? | **Ja, genau eine Runde**, danach im selben PR entfernen und den Entfall im `CHANGELOG`-Bullet zu P6 nennen. Dauerhaftes `continue-on-error` wäre ein stiller Skip und widerspräche AC6. | User |

## Unverified / Messlücken

Diese Punkte sind **nicht** belegt und dürfen im Plan nicht als Faktum
behandelt werden:

1. **Repo-weite Aufrufzahl.** Issue sagt 75 Aufrufe / 25 Dateien, der Hook-Slice
   misst 69 Treffer in 10 Modulen (Design: 69 / 9). Beide Zahlen sind
   grep-basiert und können abgeschnitten sein; die autoritative Zahl liefert
   erst der P3-Check (AST). Die P2-Dateizahl „≈18" ist eine Schätzung, die
   Seed-Liste umfasst 28 Namen.
2. **Exakte `ARTIFACT_TESTS`-Mitgliedschaft.** Nur fünf Seed-Module sind über
   ihre Skip-Gates identifiziert; die Vollständigkeit muss gegen einen
   **ungesyncten** Checkout neu abgeleitet werden.
3. **Größeneffekt der generierten Provider-Bäume** auf Repo-Copy-Fixtures — nur
   für die verworfene In-`test`-Variante relevant, nicht gemessen.
4. **Laufzeit von `tests/browser` (11 Module)** gegen den 20-Minuten-Deckel —
   kein CI-Messwert vorhanden.
5. **Suite-Größe widersprüchlich.** Der Workflow-Header nennt 6575 Tests / 362
   Module; die Wave-3-Messung nennt 6207 / 359. Diese Spec pinnt **keine** Zahl.
6. **`sync.py --validate` grün mit dem neuen Check** auf einem gesyncten
   Checkout — erwartet ja (null Verstöße nach P2), nicht ausgeführt.
7. **Fixture-Scoping vs. `-n 2 --dist loadfile`** — erwartet kollisionsfrei
   (modul-scoped, pro Worker), nicht ausgeführt.
8. **Ob die Artefakt-Tests heute tatsächlich überspringen** — die Skip-Gates
   sind belegt, ein Lauf gegen einen ungesyncten Checkout mit `-rs` fehlt
   (AC4-Ausgangslage).
9. **Ob AC1 heute in der CI verletzt wird** — kein Digest vorhanden, also keine
   Aussage über tatsächliche Schreibvorgriffe in CI-Läufen.
10. **Design vs. Messung: Browser-Modulzahl.** Design nennt 10 Module, im
    Checkout liegen 11 (`tests/browser/test_*.py`). Das Kriterium „≥ 10" bleibt
    erfüllt; die Zahl im Design ist eine Untergrenze, kein Messwert.

## Revision-Log

| Rev. | Datum | Änderung |
|---|---|---|
| 1 | 2026-10-30 | Erste Spezifikation aus dem Systemdesign vom 2026-10-30: Stand je AC verifiziert, IC-1…IC-13 normiert, Phasen P1…P6 mit Rollback, AC1-Lesart und AC4-Wortlaut-Divergenz dokumentiert, vier offene Fragen, zehn Messlücken. `tests/README.md` als Doku-Pflicht ergänzt (im Design nicht gelistet). |

## Trace-Anker

`spec-id: SPEC-test-hygiene-945`

Der Plan referenziert diesen Wert in seinem Trace-Anker und verweist über
`**Spec:** docs/specs/2026-10-30-test-hygiene-945-design.md` auf diese Datei.
Die Datei ist bewusst `*-design.md` benannt, weil
`scripts/lib/consistency/spec_plan.py` nur dieses Muster als Spec klassifiziert.
Die Freigabe erfolgt ausschließlich durch den Nutzer über den maschinenlesbaren
Approval-Marker im Kopf dieser Datei (Wert `APPROVED` mit Datum) — diese
Revision bleibt bewusst `Entwurf`.
