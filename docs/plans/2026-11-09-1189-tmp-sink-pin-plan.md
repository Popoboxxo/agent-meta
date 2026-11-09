---
pipeline_stages:
  implement: 1
status: APPROVED
date: 2026-11-09
base-commit: 7e52f571
branch: feat/1189-tmp-sink-pin
trace:
  - SPEC-1189-tmp-sink-pin-vs-system-temp
  - issue-1189
---

# Tmp-Sink-Pin vs. System-Temp-Root (Issue #1189) — Implementation Plan

> Status: **APPROVED (2026-11-09)** — durch den User freigegeben; dieser Plan
> implementiert nichts und committet nichts.
> **Quelle:** `docs/specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-spec.md`,
> `Status: APPROVED (2026-11-09)`, Revision 4, Klasse **M**.
> Die Auflagen aus Review / Re-Review / Re-Review 2 / Freigabe-Vermerk sind in der Spec
> eingearbeitet (RVW-1…RVW-16, RVW2-1…RVW2-11, RVW3-1…RVW3-6). Dieser Plan öffnet **keine**
> dieser Entscheidungen erneut; er setzt sie in Tasks um.
> **Reihenfolge (Spec §„Umsetzungsschnitt", RVW-15):** Einheit 1 = Semantik (Tasks 1–10),
> Einheit 2 = Start-Robustheit (Tasks 11–15), Doku-Pflicht D8 verteilt auf Tasks 5–7 und 16.
> Beide Einheiten sind getrennt revertierbar.

**Goal:** Der framework-eigene `TMPDIR=<sink>`-Pin ist ein Transport-Detail und **nie** ein
Beweis über den System-Temp-Root. Exception-Prüfung (`config._validate_repo_containment`) und
`PYTEST_BASETEMP` (`tmp_paths.resolve_pytest_basetemp`) bewerten ab dem Fix den **ungepinnten**
Root; ein fehlbarer Pin bricht sichtbar ab statt still `env=None` zu spawnen (D7/IC-5a/IC-5b).
`admin-server.py start` meldet keinen unbelegten Erfolg mehr: belegter Port ⇒ deterministisch
Exit 1 **vor** dem Spawn (IC-12), toter Kindprozess ⇒ Exit 1 über Exitstatus + Health
(Heuristik mit ausgewiesenem Restfenster, IC-7/IC-8).

**Architecture:** Eine neue read-only Funktion `repo_containment.system_temp_root(project_root,
sink_dir)` ist die **einzige** Stelle, die „System-Temp-Root" bestimmt (IC-1); sie mutiert weder
`os.environ` noch `tempfile.tempdir` und ist damit thread-tauglich im
`_DaemonThreadingHTTPServer`. `resolve_sink_absolute` (IC-2) ist der öffentliche, dünne
Sink-Resolver für `config.py`, der das Resolver-Finding `repo-containment.tmp-sink-path`
auswertet statt still auf `.default` zurückzufallen. Konsumenten sind ausschließlich
`tmp_paths.resolve_pytest_basetemp` (IC-3) und `config._validate_repo_containment` (IC-4) sowie
für die Start-Robustheit `admin-server.py` (IC-6…IC-12). Es gibt **keine** neue Env-Variable,
**kein** Config-Feld, **keine** Schema-Änderung und **keine** Abschwächung des Pins.

**Tech Stack:** Python 3 (stdlib only: `tempfile`, `socket`, `urllib.request`, `subprocess`,
`pathlib`), PyYAML (bestehende Runtime-Ausnahme), pytest, Markdown/YAML.

**Spec:** docs/specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-spec.md
**Spec-ID:** SPEC-1189-tmp-sink-pin-vs-system-temp
**Issue:** #1189 · Regression aus `f9e3f3e5` (PR #1023) · Vorgänger-Spec (gültig, nur D8-Verweis):
SPEC-tmp-sink-injection (`docs/specs/2026-10-24-tmp-sink-injection-spec.md`)
**Klasse:** M · **Datum:** 2026-11-09 · **Base:** `main @ 7e52f571` (Branch nach Fast-Forward
auf `origin/main`; die 6 neuen Commits sind Dependabot-Bumps in `tests/requirements.txt` —
pytest ≥9.2.0 und questionary ≥2.1.1 für Python ≥3.10 — und testinfrastruktur-neutral)
**Branch-Vorschlag:** `feat/1189-tmp-sink-pin`
**Aufwand:** 16 Tasks, 7 Produktionsdateien, 7 Testdateien (davon 3 neu, 4 erweitert) plus
2 unveränderte Prüfanker, 3 Doku-/Changelog-Änderungen. Eine belastbare Schätzung liefert
`effort-estimator` (Textverweis, hier bewusst nicht berechnet).

## Trace-Anker

`spec-id: SPEC-1189-tmp-sink-pin-vs-system-temp` — referenziert über `**Spec:**` und den
Trace-Anker in der Spec selbst. Die Vorgänger-Spec `SPEC-tmp-sink-injection` bleibt gültig und
wird inhaltlich **nicht** geändert (nur D8.2 ergänzt einen Verweis).

## Klarstellungen (Plan-Präzisierung, keine Spec-Änderung)

- **K-1 (`rc` ist ein Alias, kein Modul):** `system_temp_root`/`resolve_sink_absolute` liegen in
  `scripts/lib/repo_containment.py`. `tmp_paths.py` importiert das Modul als
  `from . import repo_containment as rc` (`scripts/lib/tmp_paths.py:33`); ein `scripts/lib/rc.py`
  existiert nicht und wird nicht angelegt (RVW2-11).
- **K-2 (Annotationsstil je Datei):** `repo_containment.py`, `tmp_paths.py` und `config.py`
  schreiben gequotete Annotationen (`"str | os.PathLike[str]"`, `Optional[...]`) wie im Bestand;
  `admin-server.py` schreibt ungequotet (`str | None`, `tuple[Path, bool]`) — so wie die Datei
  heute schon ist (IC-1/IC-12).
- **K-3 (Adressfamilie der Bind-Probe, Approval-Hinweis (a)):** Das Kind bindet über
  `_DaemonThreadingHTTPServer` (`scripts/admin-server.py:5817`) einen `ThreadingHTTPServer` ohne
  `address_family`-Override, also **AF_INET**. Die Probe darf deshalb nicht blind
  `getaddrinfo(...)[0]` nehmen: sie **bevorzugt AF_INET** und fällt nur dann auf AF_INET6 zurück,
  wenn der Host keinen AF_INET-Eintrag hat (IPv6-Literal wie `::1`). Damit ist
  `--host localhost` für beide Seiten IPv4 (`127.0.0.1`) — der Fall aus dem Approval-Vermerk,
  in dem `::1` sonst einen falschen Durchlauf oder falschen Abbruch erzeugt.
- **K-4 (Formulierung nach Eltern-Exit, Approval-Hinweis (b)):** `failed to start` erscheint
  **nur** im Fehlerpfad des Elternprozesses (IC-8 Schritt 7). Im Heuristik-Restfenster
  (AC-1189-17b) ist der Elternprozess bereits beendet; sichtbar ist der Fehlschlag dann über
  `status` und den Log, **nicht** als `failed to start`-Zeile. Keine Meldung, kein Docstring und
  kein Test darf diese Zeile für den Restfenster-Fall versprechen.
- **K-5 (Träger für die Kopien 2–4):** `tests/test_admin_server.py` lädt ausschließlich
  `admin-server.py` per `importlib` (`:41-51`). Die Kopien 2–4 (`consistency-check.py`,
  `cli_commands.py`, `run_role_routing_eval.py`) und der Eval-Abbruch bekommen deshalb einen
  eigenen Träger `tests/test_tmp_sink_pin_policy.py` (neu) mit demselben `importlib`-Muster.
- **K-6 (bewusst unverändert, aber im Regressionsnetz):** `tests/conftest.py` (RVW-5/Nicht-Ziel)
  und `tests/test_tmp_sink_env_coverage.py` (AC-1189-30: keine neuen Allowlist-Zeilen) werden
  **nicht** editiert; sie sind Prüfanker, keine Task-Dateien.
- **K-7 (Baseline-Begriff):** „Ungepinnt" heißt **dieselbe Env ohne `TMPDIR`/`TEMP`/`TMP`** —
  nicht „der Custom-`TMPDIR` des Aufrufers" (RVW-4). Ein Custom-`TMPDIR` wird vom Pin bewusst
  verdeckt und ist ein eigener, dokumentierter Testfall, keine Invariante.
- **K-8 (Exit-2-Doppelbelegung):** `consistency-check.py` nutzt Exit 2 bereits für
  „File not found"; die neue Pin-Abbruchroute belegt denselben Code. Zulässig und in IC-5b so
  vorgesehen, hier einmal benannt (Re-Review 2, §2.5 Nebenbefund).
- **K-9 (außerhalb von D7):** `scripts/lib/context_report.py:347` und
  `scripts/lib/meta_optimizer.py:1532` rufen `tmp_env` **direkt**; sie schlucken keine Fehler und
  geben kein `None` zurück. Sie bleiben unverändert und werden **nicht** in D7 gezogen (RVW3-6).

## Global Constraints

- **stdlib only, keine neue Dependency**; dieser Plan fasst `tests/requirements.txt` und
  `pyproject.toml` **nicht** an. Die mit der Base eingegangenen Dependabot-Bumps (pytest ≥9.2.0
  bzw. ≥7.0 auf 3.9, `pytest-xdist`/`pytest-split` unverändert, questionary ≥2.1.1) sind
  **testinfrastruktur-neutral**: kein Task nutzt `questionary` (nur `scripts/lib/setup.py`, hier
  nicht berührt), und alle verwendeten pytest-Oberflächen (`monkeypatch`, `pytest.raises`,
  `pytest.mark.skipif`, `--basetemp`, `-q`) sind stabile, dokumentierte APIs; `pytest-timeout`
  bleibt ungenutzt.
- **Kein neues Config-Feld, kein neuer Env-Key, keine Schema-Änderung:**
  `config/project-config.schema.json` und `.meta-config/project.yaml` bleiben byte-identisch
  (AC-1189-22).
- **Pin bleibt für alle Kinder** (D4): kein Aufrufer wird ausgenommen; „kein Pin" existiert nur
  für die drei definierten Zustände aus D7 (Config-Datei fehlt, Sink deaktiviert,
  Framework-`lib` nicht importierbar).
- **Read-only-Semantik (RVW-1):** `system_temp_root` mutiert `os.environ` und
  `tempfile.tempdir` **nicht**; keine Sperre, kein Restore-Vertrag, keine Datei/Verzeichnis-
  Anlage durch die Funktion selbst (nur der Stdlib-`gettempdir()`-Probe-Aufruf, IC-1 Schritt 1).
- **Kein Token-Versand, kein Proxy, keine Redirects** in der Health-Probe (D6/IC-7); die
  Auth-Oberfläche bleibt unverändert (`/api/health` bleibt token-gated, Option A ist verworfen).
- **`tests/conftest.py` wird nicht angefasst** (RVW-5); die Grenze „pytest ohne `--basetemp`
  erbt den Pin" wird nur dokumentiert (D8.1).
- **Testkonvention (Spec §Testkonvention, RVW-14):** Pin-Fälle **env-basiert** modellieren
  (`monkeypatch.setenv` für `TMPDIR`/`TEMP`/`TMP` **plus** `tempfile.tempdir = None`);
  `monkeypatch.setattr(tempfile, "gettempdir", ...)` nur für Fälle **ohne** Env-Bezug (z. B.
  „Temp-Root = Projekt-Root", „Temp-Root = Sink-Unterverzeichnis"). Ein `gettempdir`-Patch ist
  für Pin-Fälle **unzulässig** — der read-only Fallback würde denselben Patch sehen.
- **Testkommando:** `python3 -m pytest <pfad> --basetemp="$PYTEST_BASETEMP"`. Niemals ein
  Basetemp im Baum, niemals `rtk pytest` (defekt).
- **Ein Commit pro Task**, Englisch, Conventional Commits, ≤ 72 Zeichen erste Zeile, Imperativ,
  **ohne BOM** (Guard-Hook). Kein Push, kein Tag, kein Merge — das ist Sache der Rolle `git`.
- **Kein `isolation: "worktree"`**; Arbeit direkt im Projektverzeichnis.
- **Sprache:** Plan und Doku Deutsch, Code/Tests/Commits Englisch.

## Exit-Code- und Meldungsmatrix (IC-5b, verbindlich für Tasks 5–8 und 14)

Stream-Konvention (RVW3-5): `admin-server.py`-Lifecycle-Zeilen gehen mit `print(...)` ohne
`file=` auf **stdout** (Bestandsmuster `scripts/admin-server.py:6044-6051`). Alle übrigen
Aufrufer schreiben `error: <code>: <message>` auf **stderr** (`TmpSinkError.__str__` liefert
bereits `"<code>: <message>"`).

| Aufrufer | Fangstelle (Datei:Zeile) | Ergebnis | Stream |
|---|---|---|---|
| `_admin_start_detached` | `try/except TmpSinkError` um den `env=`-Ausdruck (`admin-server.py:6032`/`:6038`), **vor** dem Spawn | kein Spawn; **Exit 1**; `  !  tmp-sink pin unavailable: <message>` + `  i  Reparatur: python scripts/sync.py --validate` | stdout |
| `VizManager._start` | dito um `admin-server.py:650`/`:659` | kein Spawn; `False`, keine PID-Datei; `  !  <label> not started: tmp-sink pin unavailable: <message>` | stdout |
| `SyncExecutor._run` | eigener `except TmpSinkError` **vor** `except Exception` (`admin-server.py:1380`) | kein Kind; `{"success": False, "output": "tmp-sink pin unavailable: <code>: <message>", "returncode": -1}`, via `_record_run` persistiert | `output`-Feld |
| `ConsistencyService.run_consistency_check` | eigener `except TmpSinkError` **vor** `except Exception` (`admin-server.py:1761`) | kein Kind; `{"error": "tmp-sink pin unavailable: <code>: <message>", "findings": [], "summary": {"total": 0, "errors": 0, "warnings": 0}}`; HTTP-Status unverändert (200) | `error`-Feld |
| `cli_commands` (`sync.py`-Pfad) | neuer Helfer `_admin_tmp_env_or_exit(root)`; ersetzt die Inline-Aufrufe `cli_commands.py:575` und `:1732` | **Exit 2**; `error: tmp-sink.pin-unavailable: <message>` | stderr |
| `consistency-check.py::main` | Top-Level-`try/except TmpSinkError` um den Lauf (Einstieg `consistency-check.py:287`) | **Rückgabe 2**; bei `--json` genau **ein** JSON-Objekt `{"error": "tmp-sink.pin-unavailable", "detail": "<message>"}` | stderr bzw. stdout (`--json`) |
| `run_role_routing_eval.py::main` | Top-Level-`try/except TmpSinkError` um den Lauf (Einstieg `run_role_routing_eval.py:930`) | **Rückgabe 2**; `error: tmp-sink.pin-unavailable: <message>` | stderr |

**Pro-Kopie-Rückgabe (IC-5a):** Kopien 1–3 (`admin-server.py`, `consistency-check.py`,
`cli_commands.py`) → `dict | None`, `None` nur für die drei D7-Zustände. Kopie 4
(`run_role_routing_eval.py::_tmp_sink_env`) → **`dict`**, nie `None`; im „kein Pin"-Fall das
übergebene `base`-Env **inhaltlich gleich** (gleicher Key-Set, gleiche Werte — **nicht**
dasselbe Objekt, der Bestand kopiert in `:705`). Jeder andere Fehler ⇒
`TmpSinkError("tmp-sink.pin-unavailable", <Originalmeldung + "python scripts/sync.py --validate">)`.

**Einzige Warnzeile (D7 Punkt 3, RVW3-2 — Text ist neu, es gibt keine Bestandszeile):**

```text
  !  tmp-sink pin unavailable: framework lib not importable; inheriting environment
```

Sie erscheint **genau einmal** pro Aufruf, nur im `ImportError`-Fall der Kopien 1–3, auf
**stderr**. Für Kopie 4 ist der Zweig nicht anwendbar (Modul-Level-Importe `:55`/`:62`).

## Regressionsnetz (der ursprüngliche Bug, explizit)

Diese Tests müssen **vor** dem Fix rot bzw. gegenstandslos sein und **nach** dem Fix grün
bleiben; sie sind der Nachweis, dass Issue #1189 geheilt ist und nicht nur umgangen:

| # | Test / Prüfung | Heute | Nach dem Fix |
|---|---|---|---|
| G1 | Repro: `TMPDIR=<root>/.tmp python3 scripts/sync.py --validate` | Exit 1, `tmp-sink.system-temp-exception` | Exit 0 (AC-1189-12, Task 10) |
| G2 | Repro Boot: `TMPDIR=<root>/.tmp` + `from lib.config import load_config; load_config(...)` | `SystemExit(1)` | rc 0 (Task 10) |
| G3 | `tests/test_tmp_sink_path_hardening.py::test_config_load_with_tmpdir_in_sink` (`:246-255`) | grün (Block fehlt ⇒ Validator prüft nicht) | **bleibt grün, unverändert** — Anker und Beweis, dass AC-1189-05 nicht über den Default-Block „gelöst" wurde (RVW-9) |
| G4 | `tests/test_tmp_paths_builder.py::test_system_temp_exception_matrix[tmp-sink.system-temp-exception]` (`:284-305`) | grün (Fehler bei In-Root-Temp) | **bleibt grün**; der Fehlerfall wird jetzt über `system_temp_root` erzeugt, nicht über `gettempdir()` direkt |
| G5 | `tests/test_repo_containment_validate.py::test_system_temp_exception_rejects_temp_root_inside_project` (`:332-343`) | grün | **bleibt grün** + neue Assertion auf den Repair-Hinweis (Task 4) |
| G6 | `tests/test_tmp_sink_output_dirs.py::test_pytest_basetemp_rejects_temp_root_inside_project` (`:389-397`) | grün | **bleibt grün**; neuer Nachbarfall „Sink-Unterverzeichnis" (Task 3, U2-13) |
| G7 | `tests/test_tmp_sink_env_coverage.py::test_subprocess_calls_pin_temp_env` (`:230`) | grün | **bleibt grün ohne neue Allowlist-Zeile** (AC-1189-30) |
| G8 | `tests/test_tmp_sink_path_hardening.py::test_location_default_ok_when_tempdir_is_sink` (`:218-222`) | grün | **bleibt grün** — Präzedenzfall für D1 (`tmp_sink_location_error`) |

## File Structure

### Produktion (7 Dateien)

- Modify: `scripts/lib/repo_containment.py` — neu `system_temp_root` (IC-1) und
  `resolve_sink_absolute` (IC-2); `TmpSinkError`-Docstring um `tmp-sink.pin-unavailable` +
  `tmp-sink.system-temp-exception` und die Exit-1-Ausnahme `admin-server`-Lifecycle erweitern
  (`:563-574`); `tmp_sink_location_error`-Docstring korrigieren (`:360-367`, D8.3). T1, T2
- Modify: `scripts/lib/tmp_paths.py` — `resolve_pytest_basetemp` nutzt `system_temp_root`
  (`:234-284`); `_system_temp_basetemp(temp_root)` erhält den Root als Parameter (`:220-224`).
  T3
- Modify: `scripts/lib/config.py` — Exception-Matrix ersetzt `tempfile.gettempdir()` durch
  `resolve_sink_absolute` + `system_temp_root`, plus Repair-Hinweis (`:888-937`). T4
- Modify: `scripts/admin-server.py` — `_tmp_sink_env`-Politik + Docstring (`:311-335`, T5);
  `SyncExecutor._run`/`ConsistencyService.run_consistency_check` catch (T9); `_is_pid_running`
  Zombie-Guard (`:569-585`) + `_route_get_health` `pid` (`:3794-3799`) (T11);
  `_probe_port_bindable` neu (T12); `_wait_for_admin` + Konstanten neu (T13);
  `_admin_start_detached` (`:5990-6051`) inkl. `token_configured`-Quelle (T14);
  `VizManager._start` (`:621-671`) mit `VIZ_START_GRACE` (T15)
- Modify: `scripts/consistency-check.py` — `_tmp_sink_env`-Politik + Docstring (`:74-94`);
  Top-Level-`TmpSinkError`-Fang in `main` (`:287`). T6
- Modify: `scripts/lib/cli_commands.py` — `_admin_tmp_env`-Politik + Docstring (`:188-209`);
  neu `_admin_tmp_env_or_exit`; Aufrufstellen `:575` und `:1732`. T7
- Modify: `scripts/run_role_routing_eval.py` — `_tmp_sink_env` (`:697-713`, `-> dict`, Abbruch
  vor der Case-Schleife), `call_provider(..., env=None)` (`:716-732`), `run_class`
  (`:769-802`: Pin einmal je Klasse + `except TmpSinkError: raise`), `main`-Fang (`:930`). T8

### Tests (7 Dateien; 3 neu, 4 erweitert) plus 2 unveränderte Prüfanker

- Create: `tests/test_tmp_sink_system_temp_root.py` — U1-1…U1-9 + IC-2-Fälle (`system_temp_root`,
  `resolve_sink_absolute`). T1, T2
- Modify: `tests/test_tmp_sink_output_dirs.py` — U2-10…U2-13 (Resolver-Ebene, Pin env-basiert,
  Baseline-Invariante). T3, T10
- Modify: `tests/test_tmp_paths_builder.py` — U3-14 (expliziter Block unter Pin ⇒ kein
  `SystemExit`) und U3-16 (Default-Block = No-op). T4
- Modify: `tests/test_repo_containment_validate.py` — U3-15 (`load_config` unter Pin) und
  Repair-Hinweis in der Meldung (AC-1189-06). T4
- Modify: `tests/test_admin_server.py` — U4-18, 18a–18d, 19, 19a–19c, 20, 21, 22, 23, 24, 25,
  26, 26e, 27, 27a. T5, T9, T11, T12, T13, T14, T15
- Create: `tests/test_tmp_sink_pin_policy.py` — U4-26a…26d + `_admin_tmp_env_or_exit` +
  Eval-Abbruch + Docstring-Greps (Test 31); in T16 zusätzlich die D8-Text-Assertions. T6, T7,
  T8, T16
- Create: `tests/test_tmp_sink_pin_integration.py` — I1 (U4-28) und I2 (U4-29) als
  Subprozess-Nachweis; AC-1189-12/13. T10
- Unverändert (Prüfanker, **kein** Edit): `tests/conftest.py` (`:45-59`, RVW-5) und
  `tests/test_tmp_sink_env_coverage.py` (`:46`, `:156-172`, AC-1189-30). —

### Doku / Meta (4 Dateien)

- Modify: `docs/concepts/repo-containment-prison-mode.md` — §5.5 (`:407-476`) erhält den
  D8.1-Satz zum Pin als Nicht-System-Temp-Root und die Grenze „pytest ohne `--basetemp`". T16
- Modify: `docs/specs/2026-10-24-tmp-sink-injection-spec.md` — Option C (`:626-645`) erhält den
  D8.2-Verweis: die dortige `tempfile.gettempdir()`-Definition gilt **abzüglich** des
  framework-eigenen Pins. T16
- Modify: `CHANGELOG.md` — Eintrag unter `Unreleased`: Pin-Semantik, Pin-Policy-Abbruch,
  `start`-Exit-Verhalten (Vorbereitung, konsistent zu `crossrefs.changelog-missing-entry`). T16
- Create: `docs/plans/2026-11-09-1189-tmp-sink-pin-plan.md` — dieser Plan (Freigabe durch den
  User). —

---

## Einheit 1 — Semantik (Tasks 1–10)

### Task 1: `system_temp_root` — der ungepinnte System-Temp-Root (IC-1)

**Agent:** developer
**Depends on:** —
**Files:**
- Modify: `scripts/lib/repo_containment.py`
- Create: `tests/test_tmp_sink_system_temp_root.py`
**Interfaces:** Produces `repo_containment.system_temp_root(project_root: "str | os.PathLike[str]", sink_dir: Optional[Path]) -> str` (read-only, einzige Stelle mit der Semantik „System-Temp-Root"); Consumes `tempfile.gettempdir()`, `getattr(tempfile, "_candidate_tempdir_list", None)` (guarded), `os.path.realpath`/`normcase`, `TmpSinkError` (`repo_containment.py:563-574`).

- [ ] Step 1: **Test zuerst** in `tests/test_tmp_sink_system_temp_root.py` (Modul-Docstring nennt IC-1 und AC-1189-01/02/10/11/30): `test_no_sink_returns_gettempdir` (U1-1), `test_pin_returns_existing_dir_outside_root` (U1-2), `test_tmpdir_only_pin_matches_all_keys_pin` (U1-3, `skipif` für nicht-Linux), `test_observed_root_not_sink_returns_unchanged` (U1-4), `test_environ_and_tempdir_cache_unchanged` (U1-5, Priming **vor** Snapshot), `test_concurrent_calls_agree` (U1-6, 8 Threads), `test_sink_candidate_is_skipped` (U1-7), `test_no_candidate_outside_root_raises` (U1-8, `TmpSinkError.code == "tmp-sink.system-temp-exception"`), `test_normcase_comparison_windows` (U1-9, `normcase`/`realpath`-Monkeypatch). Pin-Fälle **env-basiert** (`monkeypatch.setenv("TMPDIR", ...)` + `tempfile.tempdir = None`), kein `gettempdir`-Patch (Global Constraint K-7/Spec-Testkonvention).
  Lauf: `python3 -m pytest tests/test_tmp_sink_system_temp_root.py --basetemp="$PYTEST_BASETEMP" -q` → **rot — 9 failed** (`AttributeError: module 'lib.repo_containment' has no attribute 'system_temp_root'`).
- [ ] Step 2: `system_temp_root` implementieren — Schritt 1 `observed = tempfile.gettempdir()` (`OSError` ⇒ `TmpSinkError("tmp-sink.system-temp-exception", …)`); Schritt 2 bei `sink_dir is None` **oder** `normcase(realpath(observed)) != normcase(realpath(sink_dir))` ⇒ `observed` **unverändert** (verbatim, kein `realpath` auf dem Rückgabewert); Schritt 3 im Pin-Fall read-only Kandidatenwahl in Stdlib-Reihenfolge (primär `tempfile._candidate_tempdir_list()` per `getattr`-Guard, sonst dokumentierter Nachbau `TMPDIR`/`TEMP`/`TMP` → `/tmp`,`/var/tmp`,`/usr/tmp` bzw. `%LOCALAPPDATA%\Temp` → `os.getcwd()`), Filter „nicht leer, absolut, `isdir`, `realpath != Sink`, `realpath` nicht innerhalb `project_root`", erster Treffer **verbatim**; leere Liste ⇒ `TmpSinkError("tmp-sink.system-temp-exception", …)`. **Keine** Mutation von `os.environ`/`tempfile.tempdir`, keine Sperre, keine Datei-Anlage, kein Import aus `config`/`tmp_paths` (Bibliotheks-Doktrin `repo_containment.py:1-8`).
- [ ] Step 3: `TmpSinkError`-Docstring (`:566-568`) um `tmp-sink.pin-unavailable` und `tmp-sink.system-temp-exception` erweitern; „Callers map it to Exit 2" behalten und die Ausnahme `admin-server`-Lifecycle (Exit 1) benennen (IC-5b Docstring-Pflicht). Zusätzlich `tmp_sink_location_error`-Docstring (`:360-367`, D8.3) korrigieren: die Aussage „Only place that consults `tempfile.gettempdir` in the sink context" trifft nicht mehr zu — `system_temp_root` ist der zweite Konsument; **kein** Verhaltenswechsel, kein Test ändert sich dadurch.
- [ ] Step 4: Lauf: **grün — 9 passed**; `python3 -m pytest tests/test_repo_containment_validate.py tests/test_tmp_sink_path_hardening.py --basetemp="$PYTEST_BASETEMP" -q` → **0 failed** (G3/G5/G8 bleiben grün).
- [ ] Step 5: `python3 scripts/sync.py --validate` → **rc 0**.
- [ ] Step 6: Commit `feat: resolve un-pinned system temp root read-only`.

### Task 2: `resolve_sink_absolute` — Sink ohne stillen Default-Fallback (IC-2)

**Agent:** developer
**Depends on:** 1
**Files:**
- Modify: `scripts/lib/repo_containment.py`
- Modify: `tests/test_tmp_sink_system_temp_root.py`
**Interfaces:** Produces `repo_containment.resolve_sink_absolute(project_root: "str | os.PathLike[str]", config: Optional[dict]) -> Optional[Path]` (realpath-`Path` oder `None`); Consumes `resolve_effective_repo_containment` (`:475-560`), das Finding `repo-containment.tmp-sink-path` (`:540-549`), `_resolve_sink_dir` (`:304-327`).

- [ ] Step 1: **Test zuerst** in `tests/test_tmp_sink_system_temp_root.py`: `test_resolve_sink_absolute_returns_realpath` (gültige Config ⇒ `Path(realpath(<root>/<sink>))`), `test_resolve_sink_absolute_none_when_disabled`, `test_resolve_sink_absolute_none_on_invalid_path_finding` (z. B. `tmp-sink.path: "../escape"` ⇒ `None` **und** das Finding existiert, kein stiller `.tmp`-Default). Lauf → **rot — 3 failed** (`AttributeError`).
- [ ] Step 2: Implementieren: `effective = resolve_effective_repo_containment(config)`; bei `not effective.tmp_sink_enabled` ⇒ `None`; `bad = [f for f in effective.findings if f.code == "repo-containment.tmp-sink-path"]` ⇒ bei Treffer `None`; sonst `_resolve_sink_dir(project_root, effective)` (das liefert bereits `None` für lexikalische/Realpath-Fehler). **Nicht** exitierend, keine Meldung, kein Log (wie der Resolver).
- [ ] Step 3: Docstring mit dem Finding-Check begründen (RVW2-8: der Resolver fällt auf `.tmp` zurück, der Wrapper darf das nicht adeln).
- [ ] Step 4: Lauf: **grün — 3 passed**; `python3 -m pytest tests/test_tmp_sink_system_temp_root.py --basetemp="$PYTEST_BASETEMP" -q` → **12 passed** gesamt.
- [ ] Step 5: Commit `feat: expose sink resolver that refuses the default fallback`.

### Task 3: `resolve_pytest_basetemp` nutzt den ungepinnten Root (IC-3, D2)

**Agent:** developer
**Depends on:** 1
**Files:**
- Modify: `scripts/lib/tmp_paths.py`
- Modify: `tests/test_tmp_sink_output_dirs.py`
**Interfaces:** Produces `tmp_paths.resolve_pytest_basetemp(project_root, paths) -> str` mit **unveränderter** Signatur und `tmp_paths._system_temp_basetemp(temp_root: str) -> str`; Consumes `rc.system_temp_root(project_root, paths.absolute if paths.enabled else None)` (Task 1).

- [ ] Step 1: **Test zuerst** in `tests/test_tmp_sink_output_dirs.py` (bestehende Helfer `_exception_cfg`/`_system_temp_outside_project` weiterverwenden, Pin env-basiert): `test_pytest_basetemp_under_pin_is_outside_root` (U2-10: keine `TmpSinkError`, Pfad außerhalb `tmp_path`, endet auf `pytest-agent-meta`), `test_pytest_basetemp_matches_clean_env_baseline` (U2-11: Baseline in sauberer Env ermitteln, **dann** pinnen, identischer Wert — K-7), `test_pytest_basetemp_custom_tmpdir_is_masked_by_pin` (U2-11 zweiter Fall: Ergebnis = Plattform-Default, **nicht** der Custom-Wert), `test_pytest_basetemp_disabled_sink_with_tmpdir_in_sink_raises` (U2-12), `test_pytest_basetemp_rejects_sink_subdirectory_as_temp_root` (U2-13/D3, `gettempdir`-Patch hier zulässig — kein Env-Bezug). Lauf → **rot — 5 failed** (erste vier an `tmp-sink.system-temp-exception`, der Baseline-Fall an der Abweichung).
- [ ] Step 2: `_system_temp_basetemp(temp_root)` implementieren (Parameter statt verstecktem `gettempdir()`); in `resolve_pytest_basetemp` beide Aufrufstellen (`:253`, `:258`) auf `rc.system_temp_root(project_root, paths.absolute if paths.enabled else None)` umstellen.
- [ ] Step 3: Die Inside-Prüfung (`:274-282`) auf **denselben** Wert umstellen, der in den Pfad eingeht (`_is_inside(project_real, temp_real)` bleibt als Defense-in-depth, prüft aber `system_temp_root`-Ergebnis statt `gettempdir()`); Fehlertexte (`system-temp-exception`, Quote-/Newline-Prüfung) unverändert lassen.
- [ ] Step 4: Lauf: **grün — 5 passed**; Nachbarregression `python3 -m pytest tests/test_tmp_sink_output_dirs.py --basetemp="$PYTEST_BASETEMP" -q` → **0 failed**, insbesondere `test_pytest_basetemp_rejects_temp_root_inside_project` (`:389-397`, G6) und `test_pytest_basetemp_uses_system_temp_when_exception_active` (`:367-378`).
- [ ] Step 5: Commit `fix: derive pytest basetemp from the un-pinned temp root`.

### Task 4: Validator-Matrix über `resolve_sink_absolute` + `system_temp_root` (IC-4)

**Agent:** developer
**Depends on:** 1, 2
**Files:**
- Modify: `scripts/lib/config.py`
- Modify: `tests/test_tmp_paths_builder.py`
- Modify: `tests/test_repo_containment_validate.py`
**Interfaces:** Produces `config._validate_repo_containment` mit Pin-bewusster Exception-Matrix und Repair-Hinweis; Consumes `repo_containment.resolve_sink_absolute` + `repo_containment.system_temp_root`, `_path_is_inside` (`config.py:786-792`, unverändert), `_fail` (`:808-810`).

- [ ] Step 1: **Test zuerst**: in `tests/test_tmp_paths_builder.py` `test_system_temp_exception_accepts_pin_equivalent_temp_root` (U3-14: `gettempdir()` == Sink **und** expliziter Block ⇒ **kein** `SystemExit`; Pin env-basiert) und `test_system_temp_exception_default_block_is_noop_under_pin` (U3-16: fehlender Block ⇒ Validator prüft nicht, No-op dokumentiert); in `tests/test_repo_containment_validate.py` `test_load_config_under_pin_with_explicit_block_passes` (U3-15: `load_config(<fixture>/.meta-config/project.yaml)` unter Pin, kein `SystemExit`, Dict enthält `repo_containment.tmp-sink.path`) und `test_system_temp_exception_message_contains_stale_pin_repair_hint` (AC-1189-06: echter In-Root-Root ≠ Sink ⇒ Exit 1, Meldung unverändert **plus** „If this is a stale framework pin: open a new shell or re-run 'python scripts/sync.py'."). Lauf → **rot — 4 failed**.
- [ ] Step 2: In der Matrix (`:930-937`) `temp_root = tempfile.gettempdir()` durch `sink = resolve_sink_absolute(config_path.parent.parent, config)` und `temp_root = system_temp_root(config_path.parent.parent, sink)` ersetzen; `root` bleibt `config_path.parent.parent`; Prüfscope **unverändert** nur bei vorhandenem `system-temp-exception`-Block (`:893`).
- [ ] Step 3: `_fail`-Meldung erweitern: bestehender Text `platform temp root <repr> is inside the project root — the exception cannot take effect.` bleibt **inhaltlich unverändert**, der Repair-Hinweis wird **nur** angehängt, wenn der beobachtete Root innerhalb des Repos liegt (RVW-12). `TmpSinkError` aus IC-1 wird zu `_fail(str(exc))` (Exit 1). Ist `resolve_sink_absolute` `None` (Sink aus/ungültig), verhält sich die Temp-Root-Prüfung wie heute; die Pfad-Meldung (`:939-950`) bleibt unverändert.
- [ ] Step 4: Lauf: **grün — 4 passed**; Regression `python3 -m pytest tests/test_tmp_paths_builder.py tests/test_repo_containment_validate.py tests/test_tmp_sink_path_hardening.py --basetemp="$PYTEST_BASETEMP" -q` → **0 failed** (G3/G4/G5).
- [ ] Step 5: `python3 scripts/sync.py --validate` → **rc 0** und `TMPDIR=$PWD/.tmp python3 scripts/sync.py --validate` → **rc 0** (erster grüner Vor-Beweis für AC-1189-12; End-to-End folgt in Task 10).
- [ ] Step 6: Commit `fix: validate the un-pinned temp root against the sink pin`.

### Task 5: Pin-Policy Kopie 1 — `admin-server.py::_tmp_sink_env` (IC-5a/IC-5b, D7)

**Agent:** developer
**Depends on:** —
**Files:**
- Modify: `scripts/admin-server.py`
- Modify: `tests/test_admin_server.py`
**Interfaces:** Produces `admin-server.py::_tmp_sink_env(root: Path, base: dict | None = None) -> dict | None` mit D7-Politik (Signatur unverändert) und `TmpSinkError("tmp-sink.pin-unavailable", …)`; Consumes `lib.repo_containment.TmpSinkError` (lazy import), `lib.config.load_config`, `lib.tmp_paths.resolve_tmp_paths`/`tmp_env`.

- [ ] Step 1: **Test zuerst** in `tests/test_admin_server.py`, neue Klasse `TestTmpSinkEnvPolicy` (Muster `importlib`-Laden `:41-51`): `test_pin_returns_sink_env_when_config_valid` (U4-26: gepinnte äußere Env + gültige Fixture-Config ⇒ `TMPDIR == TEMP == TMP == str(sink)`), `test_broken_config_raises_pin_unavailable` (`repo_containment: "x"` ⇒ `TmpSinkError`, `code == "tmp-sink.pin-unavailable"`, Meldung enthält `python scripts/sync.py --validate`), `test_missing_config_returns_none`, `test_disabled_sink_returns_none` (D7-Fälle 1/2), `test_docstring_drops_inherited_env_promise` (Test 31: Docstring enthält **nicht** `keeps operating with the inherited env`, enthält `tmp-sink.pin-unavailable`). Lauf → **rot — 5 failed**.
- [ ] Step 2: `_tmp_sink_env` implementieren: `except ImportError` ⇒ **eine** Warnzeile (Wortlaut aus der Matrix) auf **stderr** + `None`; `except TmpSinkError` und `except SystemExit` (aus `load_config`) sowie jeder andere Fehler ⇒ `TmpSinkError("tmp-sink.pin-unavailable", f"{orig}; repair: python scripts/sync.py --validate")`. `SystemExit` bewusst mitfangen (`BaseException`-Erbe; in einem Request-Thread würde die Antwort sonst ohne Meldung verworfen).
- [ ] Step 3: Docstring (`:311-321`) gemäß D8.4 umschreiben: `None` **nur** für die drei definierten Zustände; jeder andere Fehler ⇒ `TmpSinkError` und der Start bricht sichtbar ab.
- [ ] Step 4: Lauf: **grün — 5 passed**; `python3 -m pytest tests/test_admin_server.py --basetemp="$PYTEST_BASETEMP" -q` → **0 failed** (Bestandsfälle unberührt).
- [ ] Step 5: Commit `fix: make the admin pin helper fail loud instead of unpinning`.

### Task 6: Pin-Policy Kopie 2 — `consistency-check.py::_tmp_sink_env` + Exit 2 (IC-5a/IC-5b)

**Agent:** developer
**Depends on:** —
**Files:**
- Modify: `scripts/consistency-check.py`
- Create: `tests/test_tmp_sink_pin_policy.py`
**Interfaces:** Produces `consistency-check.py::_tmp_sink_env(root: Path) -> dict | None` (D7) und den Top-Level-`TmpSinkError`-Fang in `main` mit Rückgabe 2 (JSON-Variante bei `--json`); Consumes `lib.repo_containment.TmpSinkError`, `lib.config.load_config`, `lib.tmp_paths.resolve_tmp_paths`/`tmp_env`.

- [ ] Step 1: **Test zuerst** in `tests/test_tmp_sink_pin_policy.py` (neu, `importlib`-Laden von `scripts/consistency-check.py` nach dem Muster `tests/test_admin_server.py:41-51`; Modul-Docstring nennt K-5 und IC-5a/IC-5b): `test_consistency_check_pin_returns_sink_env` (U4-26a), `test_consistency_check_pin_broken_config_raises` (`tmp-sink.pin-unavailable`), `test_consistency_check_pin_missing_config_returns_none`, `test_consistency_check_main_pin_error_returns_2` (gepatchter Helfer, der `TmpSinkError` wirft; `main([...]) == 2`, stderr `error: tmp-sink.pin-unavailable:`), `test_consistency_check_main_pin_error_json_object` (`--json` ⇒ genau ein JSON-Objekt `{"error": "tmp-sink.pin-unavailable", "detail": …}` auf stdout), `test_consistency_check_docstring_drops_never_raises_promise` (Test 31: nicht mehr `this helper never raises`). Lauf → **rot — 6 failed**.
- [ ] Step 2: `_tmp_sink_env` wie Kopie 1 umbauen (`ImportError` ⇒ Warnzeile + `None`; sonst `TmpSinkError("tmp-sink.pin-unavailable", …)`); Docstring (`:74-81`) gemäß D8.4.
- [ ] Step 3: In `main` (`:287`) den Lauf in `try/except TmpSinkError` legen: stderr `error: tmp-sink.pin-unavailable: <message>`, bei `--json` stattdessen das JSON-Objekt auf stdout; Rückgabe **2** in beiden Fällen (Doppelbelegung mit „File not found", K-8).
- [ ] Step 4: Lauf: **grün — 6 passed**; `python3 scripts/consistency-check.py` → **kein** neuer ERROR, rc unverändert (0 auf sauberem `main`).
- [ ] Step 5: Commit `fix: abort consistency-check loudly when the pin is unavailable`.

### Task 7: Pin-Policy Kopie 3 — `cli_commands.py` + `_admin_tmp_env_or_exit` (IC-5a/IC-5b)

**Agent:** developer
**Depends on:** —
**Files:**
- Modify: `scripts/lib/cli_commands.py`
- Modify: `tests/test_tmp_sink_pin_policy.py`
**Interfaces:** Produces `cli_commands._admin_tmp_env(root: Path) -> dict | None` (D7) und `cli_commands._admin_tmp_env_or_exit(root: Path) -> dict | None` (Exit 2 bei `TmpSinkError`, sonst Passthrough); Consumes `_admin_tmp_env` an den Aufrufstellen `:575` und `:1732`, `lib.repo_containment.TmpSinkError` (lazy).

- [ ] Step 1: **Test zuerst** in `tests/test_tmp_sink_pin_policy.py`: `test_cli_admin_tmp_env_returns_sink_env` (U4-26b), `test_cli_admin_tmp_env_broken_config_raises` (`tmp-sink.pin-unavailable`), `test_cli_admin_tmp_env_or_exit_exits_2_on_pin_error` (`pytest.raises(SystemExit)`, `code == 2`, stderr `error: tmp-sink.pin-unavailable: …`), `test_cli_admin_tmp_env_or_exit_passes_none_through` (deaktivierter Sink ⇒ `None` ohne Exit — D7-Fall 2), `test_cli_commands_docstring_drops_never_fails_promise` (Test 31: nicht mehr `a CLI start never fails because of it`). Lauf → **rot — 5 failed**.
- [ ] Step 2: `_admin_tmp_env` wie die übrigen `dict | None`-Kopien umbauen; Docstring (`:188-196`) gemäß D8.4.
- [ ] Step 3: `_admin_tmp_env_or_exit` ergänzen (`TmpSinkError` lazy importieren, `print(f"error: {exc}", file=sys.stderr)`, `sys.exit(2)`; bei Erfolg `_admin_tmp_env`-Rückgabe unverändert weitergeben) und die beiden Inline-Aufrufe `:575`/`:1732` darauf umstellen.
- [ ] Step 4: Lauf: **grün — 5 passed**; `python3 -m pytest tests/test_cli_commands.py --basetemp="$PYTEST_BASETEMP" -q` → **0 failed** (bzw. der zutreffende CLI-Testträger; keine neuen Fehlschläge).
- [ ] Step 5: Commit `fix: exit 2 instead of spawning an unpinned admin CLI child`.

### Task 8: Pin-Policy Kopie 4 — Eval bricht **vor** der Case-Schleife ab (IC-5a RVW2-1)

**Agent:** senior-developer
**Depends on:** —
**Files:**
- Modify: `scripts/run_role_routing_eval.py`
- Modify: `tests/test_tmp_sink_pin_policy.py`
**Interfaces:** Produces `run_role_routing_eval._tmp_sink_env(base: dict | None = None) -> dict` (nie `None`), `call_provider(..., env: dict | None = None)` (additiv, sechs Positionsparameter unverändert), `run_class` mit Pin-Auflösung **einmal je Model-Klasse vor** der Run-/Case-Schleife und `except TmpSinkError: raise`; Consumes `lib.repo_containment.TmpSinkError`, `eval_gate.run_with_approval` (`scripts/lib/eval_gate.py:278` ruft Runner ohne `try/except`).

- [ ] Step 1: **Test zuerst** in `tests/test_tmp_sink_pin_policy.py`: `test_eval_pin_returns_sink_env` (U4-26c), `test_eval_pin_broken_config_raises_pin_unavailable` (**nie** Rückgabe des `base`-Envs), `test_eval_pin_missing_config_returns_base_env_equal` und `test_eval_pin_disabled_sink_returns_base_env_equal` (jeweils `assert result == base`, **nicht** `is`, plus Key-Set-Vergleich — RVW3-4), `test_eval_pin_never_returns_none`, `test_eval_run_class_aborts_before_call_provider` (U4-26d: gepatchter `_tmp_sink_env` wirft; `call_provider` als „verboten" gepatcht ⇒ `TmpSinkError` propagiert, 0 Aufrufe), `test_eval_main_returns_2_on_pin_error` (`main([...]) == 2`, stderr-Zeile, **keine** Baseline-Datei geschrieben), `test_eval_case_loop_reraises_tmp_sink_error` (direkt in `call_provider` geworfenes `TmpSinkError` wird **nicht** als Miss verbucht), `test_eval_call_provider_uses_passed_env_and_pins_by_default` (`env=`-Keyword wird verwendet; ohne `env` wird gepinnt). Lauf → **rot — 9 failed**.
- [ ] Step 2: `_tmp_sink_env` umbauen: `-> dict` bleibt; „kein Pin" (fehlende Config, deaktivierter Sink) ⇒ `dict(os.environ if base is None else base)` (inhaltlich gleich, Kopie bleibt); jeder andere Fehler inkl. `SystemExit` ⇒ `TmpSinkError("tmp-sink.pin-unavailable", …)`. Docstring (`:697-704`) sprachlich angleichen („off" bleibt erlaubt, „unlesbar/defekt" nicht).
- [ ] Step 3: `call_provider` um `env: dict | None = None` erweitern und **genau** die guard-verträgliche Form verwenden: `child_env = dict(_tmp_sink_env(os.environ.copy()) if env is None else env)`; alle folgenden `env[...]`-Zuweisungen und `subprocess.run(env=…)` (`:747-756`) auf `child_env` umstellen. Ein Zwischenschritt ohne Pin-Token (z. B. `child_env = dict(env)`) ist **unzulässig** (`_env_is_pinned` erkennt nur `_PIN_TOKENS = ("tmp_env", "tmp_sink_env")`, `tests/test_tmp_sink_env_coverage.py:46`, `:156-172`).
- [ ] Step 4: `run_class`: `pinned_env = _tmp_sink_env(os.environ.copy())` **einmal** vor der Run-Schleife (`:779`) auflösen und an `call_provider(..., env=pinned_env)` weiterreichen; in der Case-Schleife (`:783-802`) vor `except Exception` die Klausel `except TmpSinkError: raise` einfügen (Defense-in-depth, Reihenfolge: `ProviderError` → `TmpSinkError` → `Exception`).
- [ ] Step 5: `main` (`:930`) um den Top-Level-Fang ergänzen: `except TmpSinkError as exc: print(f"error: {exc}", file=sys.stderr); return 2`.
- [ ] Step 6: Lauf: **grün — 9 passed**; `python3 -m pytest tests/test_tmp_sink_env_coverage.py tests/test_eval_baseline_schema.py --basetemp="$PYTEST_BASETEMP" -q` → **0 failed** und **keine** neue Allowlist-Zeile in `.meta-config/temp-env-allowlist.yaml` (AC-1189-30).
- [ ] Step 7: Commit `fix: abort the routing eval before spending on an unpinned run`.

### Task 9: API-Aufrufer — `SyncExecutor._run` und `ConsistencyService` (IC-5b)

**Agent:** developer
**Depends on:** 5
**Files:**
- Modify: `scripts/admin-server.py`
- Modify: `tests/test_admin_server.py`
**Interfaces:** Produces `SyncExecutor._run` mit eigenem `except TmpSinkError` **vor** `except Exception` (`:1380`) und `ConsistencyService.run_consistency_check` mit eigenem Fang **vor** `:1761`; Consumes `_tmp_sink_env` aus Task 5.

- [ ] Step 1: **Test zuerst** in `tests/test_admin_server.py`: `test_sync_executor_pin_error_returns_success_false` (`success is False`, `returncode == -1`, `"tmp-sink pin unavailable:"` im `output`, `subprocess.run` **nicht** aufgerufen, Status via `_record_run` geschrieben), `test_consistency_service_pin_error_returns_error_field` (`error`-Feld gesetzt, `findings == []`, `summary.total == 0`). Lauf → **rot — 2 failed**.
- [ ] Step 2: Beide Fangklauseln einbauen (je `except TmpSinkError as exc` **vor** dem generischen Handler); Meldungstexte exakt aus der Exit-Code-Matrix, HTTP-Status unverändert.
- [ ] Step 3: Lauf: **grün — 2 passed**; `python3 -m pytest tests/test_admin_server.py --basetemp="$PYTEST_BASETEMP" -q` → **0 failed**.
- [ ] Step 4: Commit `fix: report an unavailable pin as a sync result, not a crash`.

### Task 10: Integration — Repro aus #1189 als Subprozess (AC-1189-12/13, U4-28/29)

**Agent:** developer
**Depends on:** 3, 4
**Files:**
- Create: `tests/test_tmp_sink_pin_integration.py`
- Modify: `tests/test_tmp_sink_output_dirs.py`
**Interfaces:** Produces Subprozess-Nachweise `sync.py --validate`, `load_config`-Boot und `--dry-run --validate` unter gepinnter Env; Consumes `tests/timeouts.py::SYNC_VALIDATE_TIMEOUT` und das Subprozess-Muster aus `tests/test_sharkord_service_name_migration.py:47`.

- [ ] Step 1: **Test zuerst** in `tests/test_tmp_sink_pin_integration.py`: `test_sync_validate_under_pin_exits_zero` (Env `TMPDIR=TEMP=TMP=realpath(<repo>/.tmp)`, `[sys.executable, scripts/sync.py, --validate]`, `timeout=SYNC_VALIDATE_TIMEOUT`, `rc == 0`, `"tmp-sink.system-temp-exception"` **nicht** in stdout+stderr), `test_load_config_under_pin_exits_zero_fast` (`-c`-Variante mit `load_config`, rc 0), `test_dry_run_validate_under_pin_exits_zero` (I2/AC-1189-13). In `tests/test_tmp_sink_output_dirs.py` zusätzlich `test_render_under_pin_matches_baseline` (AC-1189-09/23: `build_variables`/`_build_orch_variables` liefern unter Pin dieselben `PYTEST_BASETEMP`/`TEST_COMMANDS` wie in sauberer Env, `PYTEST_BASETEMP` liegt außerhalb `REPO_ROOT`). Lauf → **rot — 4 failed** vor Einheit 1 (bzw. grün nur, wenn Task 1–4 bereits gelandet sind — Reihenfolge beachten).
- [ ] Step 2: Die Tests auf `REPO_ROOT = Path(__file__).resolve().parent.parent` und `tests.timeouts` stützen; kein `pytest-timeout`, kein Sleep; Pin **env-basiert**, `tempfile.tempdir` im Kind irrelevant (Subprozess).
- [ ] Step 3: Lauf: **grün — 4 passed**; die drei Repro-Kommandos zusätzlich manuell belegen: `TMPDIR=$PWD/.tmp python3 scripts/sync.py --validate` → rc 0; `TMPDIR=$PWD/.tmp python3 -c "import sys; sys.path.insert(0,'scripts'); from lib.config import load_config; load_config('.meta-config/project.yaml')"` → rc 0; `TMPDIR=$PWD/.tmp python3 scripts/sync.py --dry-run --validate` → rc 0.
- [ ] Step 4: Commit `test: pin the issue-1189 reproduction as a subprocess gate`.

---

## Einheit 2 — Start-Robustheit (Tasks 11–15)

### Task 11: `_is_pid_running`-Zombie-Guard + `/api/health`-`pid` (IC-6/IC-10)

**Agent:** developer
**Depends on:** —
**Files:**
- Modify: `scripts/admin-server.py`
- Modify: `tests/test_admin_server.py`
**Interfaces:** Produces `_is_pid_running(pid: int | None) -> bool` mit POSIX-Zombie-Guard (`/proc/<pid>/stat`, Feld 3 == `Z` ⇒ `False`, Feature-Detection) und `_route_get_health` mit additivem `pid` (`os.getpid()`) **ohne** `root`; Consumes Bestandsrouten-Registry (`:3663`) und `_send_json`.

- [ ] Step 1: **Test zuerst** in `tests/test_admin_server.py`: `test_is_pid_running_false_for_zombie` (U4-24: `os.fork()`, Kind sofort `os._exit(0)`, **kein** `waitpid` ⇒ `_is_pid_running(pid) is False`; `skipif` bei `win32` oder fehlendem `/proc`; Aufräumen per `waitpid` im `finally`), `test_is_pid_running_keeps_true_for_live_pid` (eigener Prozess), `test_health_payload_contains_pid_and_no_root` (U4-27a: `status`, `version`, `mode` unverändert, `pid == os.getpid()`, Schlüssel `root` **fehlt**). Lauf → **rot — 3 failed**.
- [ ] Step 2: Zombie-Guard implementieren: nach erfolgreichem `os.kill(pid, 0)` nur auf POSIX und nur wenn `/proc/<pid>/stat` lesbar ist, Feld 3 prüfen (`Z` ⇒ `False`); jeder Lesefehler ⇒ bisheriges Verhalten (`True`); **keine** Exception nach außen, Windows-Zweig unverändert.
- [ ] Step 3: `_route_get_health` (`:3794-3799`) um `"pid": os.getpid()` ergänzen — **kein** `root`-Feld (RVW2-10), keine Statuscode-Änderung, kein neues Route-Verhalten.
- [ ] Step 4: Lauf: **grün — 3 passed**; bestehender Health-Test bleibt grün (`python3 -m pytest tests/test_admin_server.py --basetemp="$PYTEST_BASETEMP" -q` → **0 failed**).
- [ ] Step 5: Commit `feat: detect zombie children and expose the serving pid`.

### Task 12: Pre-Flight-Bind-Probe `_probe_port_bindable` (IC-12, deterministisch)

**Agent:** senior-developer
**Depends on:** —
**Files:**
- Modify: `scripts/admin-server.py`
- Modify: `tests/test_admin_server.py`
**Interfaces:** Produces `admin-server.py::_probe_port_bindable(host: str, port: int) -> tuple[bool, str]` (neu, privat; ungequotete Annotation wie die Datei selbst, K-2); Consumes `socket.getaddrinfo`, `socket.socket`, `SO_REUSEADDR` — **kein** `listen()`/`accept()`/`SO_REUSEPORT`.

- [ ] Step 1: **Test zuerst** in `tests/test_admin_server.py`: `test_probe_port_bindable_false_while_listener_holds_port` (U4-18a: Hilfs-Socket hält `127.0.0.1:<free port>` im `listen()`; Probe ⇒ `(False, …)` mit `EADDRINUSE` im Text), `test_probe_port_bindable_releases_port_immediately` (U4-18b: freier Port ⇒ `(True, "")`; direkt danach zweite Probe **und** ein echtes `bind()` erfolgreich — kein `TIME_WAIT`, kein Leak), `test_probe_port_bindable_skips_port_zero` (U4-18c: `(True, "skipped:port-0")`, kein `getaddrinfo`/`bind` — per Mock gezählt), `test_probe_port_bindable_never_raises` (U4-18d: `gaierror` bei unauflösbarem Host, `PermissionError` für privilegierten Port ⇒ `(False, …)`, kein Raise), `test_probe_port_bindable_uses_ipv4_for_localhost` (**K-3/Approval-Hinweis (a)**: bei `host="localhost"` und belegtem `::1` aber freiem `127.0.0.1` ⇒ `(True, "")`; bei belegtem `127.0.0.1` und freiem `::1` ⇒ `(False, "EADDRINUSE: …")` — die Probe folgt der Kind-Familie AF_INET), `test_probe_port_bindable_uses_ipv6_for_ipv6_literal` (`host="::1"` ⇒ AF_INET6-Pfad, Skip wenn kein IPv6 verfügbar). Lauf → **rot — 6 failed** (`AttributeError`).
- [ ] Step 2: Implementieren: `port == 0` ⇒ sofort `(True, "skipped:port-0")`; `getaddrinfo(host, port, type=SOCK_STREAM, flags=AI_PASSIVE)` mit **Familienauswahl nach K-3** (AF_INET bevorzugen, AF_INET6 nur wenn kein AF_INET-Eintrag; `gaierror` ⇒ `(False, "<errno-name>: <strerror>")`); `sock = socket.socket(family, SOCK_STREAM)`, `setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)` (**kein** `SO_REUSEPORT` — Parität zu `HTTPServer.allow_reuse_address = 1`, den `_DaemonThreadingHTTPServer` erbt), `sock.bind(sockaddr)` in `try/except OSError`, `finally: sock.close()`; **kein** `listen()`/`accept()`, nichts persistieren.
- [ ] Step 3: Docstring mit Reichweite/TOCTOU (R11/R16: Momentaufnahme zwischen `close()` und Kind-Bind `:5918`; kein Beweis über den Portinhaber) und dem Hinweis, dass `VizManager._start` **nicht** geprobt wird (eigene Ports aus der Config, IC-12 letzter Absatz).
- [ ] Step 4: Lauf: **grün — 6 passed**; `python3 -m pytest tests/test_admin_server.py --basetemp="$PYTEST_BASETEMP" -q` → **0 failed**.
- [ ] Step 5: Commit `feat: probe the bind port before spawning the admin child`.

### Task 13: `_wait_for_admin` — Bestätigungsfenster als Heuristik (IC-7)

**Agent:** senior-developer
**Depends on:** 11
**Files:**
- Modify: `scripts/admin-server.py`
- Modify: `tests/test_admin_server.py`
**Interfaces:** Produces `admin-server.py::_wait_for_admin(proc, host, port, *, expected_mode, token_configured, timeout=START_VERIFY_TIMEOUT, interval=START_VERIFY_INTERVAL, confirm_grace=START_CONFIRM_GRACE) -> tuple[bool, str]` und die Modul-Konstanten `START_VERIFY_TIMEOUT` (5.0), `START_VERIFY_INTERVAL` (0.1), `START_CONFIRM_GRACE` (1.0); Consumes `urllib.request.build_opener(ProxyHandler({}))` mit deaktiviertem `HTTPRedirectHandler`, `proc.poll()`, `pid` aus `/api/health` (Task 11).

- [ ] Step 1: **Test zuerst** in `tests/test_admin_server.py` (Fake-Proc mit steuerbarem `poll()`, gemockter Opener; jeweils `timeout=0.2`, `confirm_grace=0.05`): `test_wait_for_admin_success_with_pid` (U4-19), `test_wait_for_admin_timeout` (`(False, "timeout")`), `test_wait_for_admin_wrong_pid` (`identity:pid`), `test_wait_for_admin_wrong_mode_without_pid` (`identity:mode`), `test_wait_for_admin_exited` (`exited:0`), `test_wait_for_admin_token_mode_accepts_stable_401` (U4-19 + 20), `test_wait_for_admin_single_401_is_not_success` (U4-19a: 401 für ~0.1 s, dann `poll() → 0` ⇒ `(False, "exited:0")`), `test_wait_for_admin_window_resets_after_non_ok` (U4-19b: 401 → 502 → 401 ⇒ Erfolg erst nach voller `confirm_grace` bzw. `timeout`), `test_start_confirm_grace_lt_verify_timeout` (U4-19c), `test_wait_for_admin_sends_no_authorization_header` (U4-20: gemockter Opener sieht **keinen** `Authorization`-Header, auch mit Token), `test_wait_for_admin_ignores_proxy_and_follows_no_redirect` (U4-21: `http_proxy=http://127.0.0.1:9` ändert das Ziel nicht; 302 ⇒ `health:302`, kein Redirect). Lauf → **rot — 11 failed**.
- [ ] Step 2: Kandidaten-Kriterium implementieren: `token_configured is False` ⇒ HTTP 200 + `status == "ok"` + (`pid` vorhanden ⇒ `pid == proc.pid`, sonst `mode == expected_mode`); `token_configured is True` ⇒ HTTP **401**. Früh-Abbruch `proc.poll() is not None` ⇒ `(False, "exited:<code>")`.
- [ ] Step 3: Bestätigungsfenster implementieren: erster Treffer setzt `confirm_since`; Erfolg nur bei ununterbrochen erfülltem Kriterium über `confirm_grace` **und** am Fensterende in der Reihenfolge „letzte HTTP-Antwort erfüllt Kriterium → `proc.poll() is None`"; jede nicht erfüllte Probe setzt `confirm_since = None`; Deadline begrenzt die **Kandidatensuche**, ein laufendes Fenster darf um höchstens `confirm_grace` überzogen werden, ein neues wird nach der Deadline nicht begonnen.
- [ ] Step 4: Netzwerk/Fehlerfälle: nur `http://`; `build_opener(ProxyHandler({}))` + deaktivierter `HTTPRedirectHandler`; Wildcard-Host (`0.0.0.0`/`::`) ⇒ Loopback (`127.0.0.1`/`::1`); Verbindungs-Timeout ≤ 1 s pro Versuch; Rückgaben `timeout`, `unconfirmed:<last_status>`, `health:<status>`, `identity:<…>` exakt wie in IC-7.
- [ ] Step 5: Docstring: **explizit** „Heuristik über den Kind-Lebenslauf, keine Erfolgsgarantie"; die Rev-3-Absolutaussage („kann einen falschen Erfolg generell verhindern") wird **nicht** übernommen (RVW3-1). Kein `token`-Parameter, kein `Authorization`-Header.
- [ ] Step 6: Lauf: **grün — 11 passed**; `python3 -m pytest tests/test_admin_server.py --basetemp="$PYTEST_BASETEMP" -q` → **0 failed**.
- [ ] Step 7: Commit `feat: verify the admin child via health over a confirm window`.

### Task 14: `_admin_start_detached` — Probe → Pin-Fang → PID → Verifikation (IC-8)

**Agent:** senior-developer
**Depends on:** 5, 12, 13
**Files:**
- Modify: `scripts/admin-server.py`
- Modify: `tests/test_admin_server.py`
**Interfaces:** Produces den neuen `start`-Ablauf (`:5990-6051`): Pre-Flight-Probe, `TmpSinkError`-Fang vor dem Spawn, PID-Datei sofort, `_wait_for_admin` mit aufgelöstem `token_configured`, Log-Tail (letzte 20 Zeilen), Exit 1; Consumes `_probe_port_bindable` (12), `_wait_for_admin` (13), `_tmp_sink_env` (5), `_load_admin_ui_config` (`:524-566`) + `_resolve_admin_token` (`:887-906`).

- [ ] Step 1: **Test zuerst** in `tests/test_admin_server.py`: `test_admin_start_aborts_without_spawn_when_port_busy` (U4-18a zweiter Teil: echter Loopback-Listener hält den Port ⇒ `SystemExit(1)`, `subprocess.Popen` **0** Aufrufe, **keine** PID-Datei, Meldung enthält `cannot bind` und `host:port`), `test_admin_start_dead_child_exits_1_with_log_tail` (U4-18: Fake-Popen `poll() → 1`, Log-Datei mit der tmp-sink-Zeile ⇒ `SystemExit(1)`, `failed to start` **und** Log-Tail in **stdout**, PID entfernt), `test_admin_start_writes_pid_before_verification` (U4-22: Hook im gepatchten `_wait_for_admin` liest die PID-Datei erfolgreich), `test_admin_start_missing_health_exits_1_and_cleans_pid` (U4-19 Timeout-Fall ⇒ `(False, "timeout")`, Kind beendet, PID entfernt), `test_admin_start_pin_error_exits_1_without_spawn` (`_tmp_sink_env` wirft ⇒ kein `Popen`, Exit 1, stdout `  !  tmp-sink pin unavailable:` + `  i  Reparatur:`), `test_admin_start_token_configured_from_admin_ui_token_env` und `..._from_token_file` (U4-26e: `ADMIN_UI_TOKEN` bzw. `admin-ui.token-file` in der Fixture ⇒ `_wait_for_admin` erhält `token_configured=True`, obwohl `args.admin_token is None`; ohne jede Quelle `False`; Opener sieht weiterhin **keinen** `Authorization`-Header), `test_restart_dead_child_exits_1` (U4-23). Lauf → **rot — 8 failed**.
- [ ] Step 2: Reihenfolge in `_admin_start_detached` implementieren: (1) „already running" unverändert; (2) `_probe_port_bindable(args.host, args.port)` **vor** jedem Spawn — `(False, reason)` ⇒ `  !  cannot bind <host>:<port>: <reason>` + `  i  Port belegt? Anderen --port wählen.` + **Exit 1**, ohne Spawn/PID/Log-Eintrag (`port == 0` ⇒ Schritt entfällt); (3) `_tmp_sink_env(root)` in `try/except TmpSinkError` **vor** dem `Popen`; (4) PID-Datei sofort nach dem Spawn (`:6041` beibehalten); (5) `token_configured` aus `_load_admin_ui_config(root)` + `_resolve_admin_token(cli_token=args.admin_token, config_token=admin_cfg["token"], config_token_file=admin_cfg["token_file"])` — **nicht** `args.admin_token` allein (RVW2-3; es gibt keinen `--admin-token-file`-Schalter); (6) `_wait_for_admin(proc, args.host, args.port, expected_mode=detect_mode(root), token_configured=…)`; (7) Erfolg erst danach (URL-Meldung, kein erneutes PID-Schreiben); (8) Fehlschlag ⇒ `proc.terminate()` (Windows `proc.kill()`), PID `unlink(missing_ok=True)`, Log-Tail (letzte 20 Zeilen, ohne Roh-Stack), Meldung mit `failed to start`, `sys.exit(1)`.
- [ ] Step 3: Erfolgsmeldung inhaltlich schärfen (D6 Punkt 2/IC-8 Schritt 6): keine Aussage „Port gehört nachweislich dem Kind", sondern „Kind lebt nach dem Bestätigungsfenster, Port antwortet erwartungsgemäß". Zusätzlich als Kommentar am Fehlerpfad und im Docstring festhalten (K-4/Approval-Hinweis (b)): im Heuristik-Restfenster ist der Elternprozess bereits beendet — sichtbar ist der Fehlschlag über `status` und den Log, **nicht** als `failed to start`-Zeile. Kein Test darf `failed to start` für den Restfenster-Fall erwarten.
- [ ] Step 4: `restart` unverändert als `stop` + `start` belassen (erbt Probe und Verifikation ohne eigene Logik, IC-8 Schritt 8).
- [ ] Step 5: Lauf: **grün — 8 passed**; `python3 -m pytest tests/test_admin_server.py --basetemp="$PYTEST_BASETEMP" -q` → **0 failed**.
- [ ] Step 6: Commit `feat: fail admin start on a busy port or a dead child`.

### Task 15: `VizManager._start` — `poll()` mit `VIZ_START_GRACE` (IC-9)

**Agent:** developer
**Depends on:** 4, 5
**Files:**
- Modify: `scripts/admin-server.py`
- Modify: `tests/test_admin_server.py`
**Interfaces:** Produces `VizManager._start` mit `poll()`-Warten über die **eigene** Konstante `VIZ_START_GRACE` (1.5) statt `time.sleep(1.5)` + `_is_pid_running` und mit `TmpSinkError`-Fang; Consumes `_tmp_sink_env` (5), die Pin-bewusste Config-Validierung (4) für den Kind-Boot.

- [ ] Step 1: **Test zuerst** in `tests/test_admin_server.py`: `test_viz_manager_start_dead_child_returns_false_and_cleans_pid` (U4-25: Fake-Popen `poll() → 1` ⇒ `False`, PID-Datei entfernt, Meldung `failed to start -- see <log>` plus Log-Tail), `test_viz_manager_start_pin_error_returns_false_without_spawn` (kein `Popen`, `False`, Meldung mit `tmp-sink pin unavailable`, keine PID-Datei), `test_viz_manager_uses_viz_start_grace_not_verify_timeout` (`VIZ_START_GRACE == 1.5` **und** `VIZ_START_GRACE is not START_VERIFY_TIMEOUT`), `test_admin_server_boot_under_pin_yields_version` (U4-27/AC-1189-24b: `AdminServer(root, port=0, enable_viz=False)` in gepinnter Env ⇒ kein `SystemExit`, `_read_version()` liefert eine Version; `viz_manager.start_all()` mit gemocktem `_start` ebenso). Lauf → **rot — 4 failed**.
- [ ] Step 2: In beiden Plattformzweigen (`:643-660`) `env=_tmp_sink_env(self.root)` in `try/except TmpSinkError` legen (kein Spawn, `False`, stdout-Meldung nach Matrix); danach PID schreiben und statt `time.sleep(1.5)`/`_is_pid_running` über `VIZ_START_GRACE` mit `proc.poll()` pollen.
- [ ] Step 3: Fehlerpfad beibehalten (`pid_file.unlink(missing_ok=True)`, `False`) und Log-Tail ergänzen, wenn die Log-Datei lesbar ist; Erfolgsmeldung unverändert.
- [ ] Step 4: Lauf: **grün — 4 passed**; `python3 -m pytest tests/test_admin_server.py --basetemp="$PYTEST_BASETEMP" -q` → **0 failed**.
- [ ] Step 5: Commit `fix: verify viz children by liveness instead of a fixed sleep`.

### Task 16: Doku-Pflicht D8 + CHANGELOG

**Agent:** documenter
**Depends on:** 4, 14
**Files:**
- Modify: `docs/concepts/repo-containment-prison-mode.md`
- Modify: `docs/specs/2026-10-24-tmp-sink-injection-spec.md`
- Modify: `CHANGELOG.md`
- Modify: `tests/test_tmp_sink_pin_policy.py`
**Interfaces:** Produces die drei D8-Textnachweise (D8.1, D8.2, Changelog) und zwei Doku-Assertion-Tests; Consumes die Tasks 1–4 (Semantik) und 14 (`start`-Verhalten).

- [ ] Step 1: **Test zuerst** in `tests/test_tmp_sink_pin_policy.py`: `test_prison_mode_5_5_distinguishes_pin_from_system_temp` (Doc-Text enthält den Satz „der framework-eigene Pin … ist **kein** System-Temp-Root" und die Grenze „pytest **ohne** `--basetemp` erbt den Pin; `tests/conftest.py` warnt nur") und `test_predecessor_spec_option_c_links_this_spec` (Option-C-Abschnitt enthält `SPEC-1189-tmp-sink-pin-vs-system-temp` und den Zusatz „abzüglich des framework-eigenen Pins"). Lauf → **rot — 2 failed**.
- [ ] Step 2: `docs/concepts/repo-containment-prison-mode.md` §5.5 (`:407-476`): Satz zu D8.1 in Punkt 1 bzw. im Anschluss an Punkt 5 einfügen — Exception-Prüfung und `PYTEST_BASETEMP` betrachten den **ungepinnten** Root; der Pin (`TMPDIR=<sink>`) ist Transport-Detail; **Grenze:** pytest ohne `--basetemp` erbt den Pin, `tests/conftest.py` warnt warning-only (RVW-5). Punkt 1 („Basetemp NIE im Arbeitsbaum") bleibt wörtlich bestehen.
- [ ] Step 3: `docs/specs/2026-10-24-tmp-sink-injection-spec.md`, Option C (`:626-645`): Verweis ergänzen — die dortige Definition („System-Temp = `tempfile.gettempdir()`") gilt **abzüglich** des framework-eigenen Pins; Vorgänger-ACs bleiben inhaltlich unverändert (kein Re-Write, nur Verweis).
- [ ] Step 4: `CHANGELOG.md` unter `Unreleased`: Pin-Semantik (Pin ≠ System-Temp-Root), Pin-Policy-Abbruch (`tmp-sink.pin-unavailable`, Exit 2 / `start` Exit 1), `start`-Verhalten (belegter Port ⇒ Exit 1 ohne Spawn; toter Kindprozess ⇒ Exit 1), Hinweis „Option A (`/api/health` token-frei) bewusst verworfen".
- [ ] Step 5: Lauf: **grün — 2 passed**; `python3 -m pytest tests/test_tmp_sink_pin_policy.py --basetemp="$PYTEST_BASETEMP" -q` → **0 failed**; `python3 scripts/consistency-check.py` → kein neuer ERROR (u. a. `crossrefs.*`, `spec_plan_*`).
- [ ] Step 6: Commit `docs: state that the tmp-sink pin is not the system temp root`.

---

## Verifikations-Gate (nach Task 16, vor dem Abschluss)

In dieser Reihenfolge ausführen; jeder Schritt muss belegt werden (Ausgabe/Zahl im Ausführungsnachweis):

1. `python3 scripts/sync.py --validate` → **rc 0**, keine `tmp-sink.system-temp-exception`-Zeile.
2. `python3 -m pytest tests/ -q --basetemp="$PYTEST_BASETEMP"` → **0 failed**; Laufzeit-Hinweis: die Suite ist lang, CI shardet — lokal dürfen die berührten Shards einzeln belegt werden, das Ergebnis muss pro Shard dokumentiert sein.
3. `python3 scripts/consistency-check.py` → **kein neuer ERROR**; `spec_plan_traceability`/`spec_plan_approval_marker` grün für diesen Plan (Spec ist `APPROVED`).
4. **Realer Smoke-Test (Pflicht, nicht mockbar):**
   - `TMPDIR=$PWD/.tmp python3 scripts/sync.py --validate` → **rc 0** (Repro aus #1189, G1).
   - `python3 scripts/admin-server.py start --root . --port 7421 --no-viz` → **Exit 0**, PID-Datei vorhanden, URL-Meldung; danach `curl -s http://127.0.0.1:7421/api/health` → `{"status":"ok",…,"pid":<kind pid>}` **ohne** `root`.
   - `curl -s -X POST http://127.0.0.1:7421/api/sync/dry-run` → `success: true`, **keine** tmp-sink-Exception im `output`.
   - `python3 scripts/admin-server.py start --root . --port 7421 --no-viz` ein zweites Mal bei laufendem Server → „already running"; nach `stop` und mit einem Fremd-Listener auf 7421 → **Exit 1**, `cannot bind 127.0.0.1:7421`, **kein** neues Kind.
   - `python3 scripts/admin-server.py stop --root .` → PID-Datei entfernt.
5. **Guard-Probe:** `python3 -m pytest tests/test_tmp_sink_env_coverage.py --basetemp="$PYTEST_BASETEMP" -q` → **0 failed** und `git diff --stat .meta-config/temp-env-allowlist.yaml` ist **leer** (AC-1189-30).
6. **Keine Schema-/Config-Drift:** `git diff --stat config/project-config.schema.json .meta-config/project.yaml` ist **leer** (AC-1189-22).

## Risiken und Rollback

| # | Risiko | Wirkung | Gegenmaßnahme im Plan |
|---|---|---|---|
| P1 | Nachbau der Stdlib-Kandidatenreihenfolge driftet (Spec R1) | Fallback wählt unerwarteten Root (nie Sink, nie Repo-Root) | Primär `tempfile._candidate_tempdir_list()` guarded; U1-8 prüft „kein Kandidat"; Baseline-Test in Task 3 erkennt Drift |
| P2 | Kein Kandidat außerhalb `root` (Spec R2) | Exception kann nicht wirksam werden | Lauter Abbruch `tmp-sink.system-temp-exception` (U1-8/AC-1189-10), kein stiller Sink-Wechsel |
| P3 | Manuell gesetzter `TMPDIR=<sink>` wird als Pin akzeptiert (Spec R3) | Exception-Prüfung entfällt genau dort | Gewollt (D1/D3); Basetemp bleibt über D2 außerhalb |
| P4 | Pre-Flight-Probe nutzt falsche Adressfamilie (Approval-Hinweis (a)) | Falscher Durchlauf (Kind bindet IPv4) oder falscher Abbruch | K-3: AF_INET bevorzugt, AF_INET6 nur ohne AF_INET-Eintrag; U4-18b mit `localhost`-Matrix |
| P5 | Health-Probe trifft Fremdprozess (Spec R4/R11/R16) | Falscher Erfolg im Token-Setup | Stufe 1 deterministisch (Task 12), Stufe 2 als Heuristik ausgewiesen (Task 13), `pid`-Vergleich (Task 11); Restfenster **nicht** heilbar und in Task 13 Docstring benannt |
| P6 | Zeitannahme `START_CONFIRM_GRACE` (Spec R6/R11a) | Kalte CI: Fenster zu kurz ⇒ Restrisiko; zu lang ⇒ späterer Fehlschlag | Modul-Konstanten (Tests klein), Invariante `START_CONFIRM_GRACE < START_VERIFY_TIMEOUT` (U4-19c), Log-Tail nennt Ursache |
| P7 | Änderung an `_tmp_sink_env` bricht einen unbekannten Aufrufer | Kind startet unerwartet nicht | IC-5b-Matrix deckt alle 7 Aufrufer; jedes `dict`-oder-`None`-Ziel behält seine Signatur; Tasks 5–9 einzeln revertierbar |
| P8 | Guard `test_tmp_sink_env_coverage.py` wird rot durch die neue `env`-Form in `call_provider` | Neue Allowlist-Zeile nötig (wäre AC-1189-30-Verstoß) | Task 8 Schritt 3 schreibt die guard-verträgliche Form `dict(_tmp_sink_env(...) if env is None else env)` vor; Gate 5 prüft leerem Allowlist-Diff |
| P9 | Stale Pin nach Sink-Pfadwechsel (Spec R13) | Harter Abbruch bei jedem CLI-Start | Repair-Hinweis in der Meldung (Task 4), AC-1189-06-Test |

**Rollback:** Zwei getrennt revertierbare Einheiten (Spec §„Umsetzungsschnitt"). Einheit 1
(Tasks 1–10) ist der Semantik-Fix; ein `git revert` der Unit-1-Commits stellt exakt das heutige
Verhalten wieder her (kein Config-Feld, keine Migration, keine Daten). Einheit 2 (Tasks 11–15)
ist unabhängig revertierbar — danach meldet `start` wieder den alten `kill(pid,0)`-Erfolg,
aber der Pin-Bug bleibt geheilt. Task 16 ist reine Doku und kann einzeln zurückgenommen werden.
Es gibt **keinen** Rollback-Bedarf auf Config- oder Schema-Ebene, weil keine Datei dort geändert
wird.

## Offene Punkte

**Keine.** Die Spec hat keine offene Frage (D1–D8 entschieden, OQ-5 = Option B). Die
Plan-Präzisierungen K-1…K-9 sind Umsetzungsdetails gegen den Checkout `7e52f571`, keine
Entscheidungsbedarfe. Zwei Punkte sind **bewusst** Annahmen statt offener Fragen und in der Spec
verankert: `START_CONFIRM_GRACE` als Zeitannahme (R11a) und das TOCTOU-Restfenster (R11/R16) —
beide sind ausgewiesen, nicht „gelöst".

## Annahmen (wenn falsch, wird der betroffene Task neu geschnitten — nicht die Spec)

1. `_DaemonThreadingHTTPServer` erbt `address_family = AF_INET` von `socketserver.TCPServer`
   (kein Override in `admin-server.py:5817`); deshalb ist AF_INET die Kind-Familie (K-3).
2. `_load_admin_ui_config` schluckt nur `Exception`, nicht `SystemExit` (`:558`) — ein
   durchschlagender `SystemExit` beendet den Start sichtbar und nie mit falschem Erfolg.
3. `eval_gate.run_with_approval` ruft Runner ohne `try/except` (`scripts/lib/eval_gate.py:278`);
   ein `TmpSinkError` aus `run_class` erreicht `main` ungefiltert.
4. Der Bestand kopiert das Env in der Eval (`run_role_routing_eval.py:705`), daher „inhaltlich
   gleich" statt Objektidentität (RVW3-4).
5. `tests/test_admin_server.py` bleibt der einzige Träger für `admin-server.py`-Tests
   (`importlib`-Laden `:41-51`); die Kopien 2–4 brauchen einen eigenen Träger (K-5).
6. Die Base-Bumps (pytest ≥9.2.0 / questionary ≥2.1.1 für Python ≥3.10, aus `origin/main`
   per Fast-Forward nach `7e52f571`) ändern nichts an Task-Struktur, Testkommandos oder
   Fixtures: `questionary` wird ausschließlich in `scripts/lib/setup.py` importiert (kein Task),
   und kein Testfall hängt an einer pytest-Versionseigenheit. Falls doch ein Bestandstest unter
   pytest 9.x neu rot wird, ist das **kein** Plan-Blocker für diesen Fix, sondern ein eigener
   Befund (dann Task 10 vorziehen und den Befund separat melden).

## Self-Review

- **Agenten:** Jeder Task hat genau eine Rolle aus {`developer`, `senior-developer`,
  `documenter`}. Kein Task ist ohne Agent; kein Task berührt eine Datei außerhalb seiner
  `Files:`-Liste.
- **File-Ownership/Barrieren:** `scripts/admin-server.py` und `tests/test_admin_server.py` werden
  ausschließlich **sequenziell** in der Reihenfolge 5 → 9 → 11 → 12 → 13 → 14 → 15 berührt (kein
  Parallel-Lauf möglich). Parallelisierbare Gruppen ohne Dateiüberlappung: **G1** {5, 6, 7, 8}
  (vier verschiedene Produktions- und Testträger), **G2** {1, 11}, **G3** {3, 6}, **G4** {4, 12}
  nach jeweiligem Vorgänger. `scripts/lib/repo_containment.py` liegt nur in Tasks 1 und 2
  (sequenziell), `tests/test_tmp_sink_pin_policy.py` in 6 → 7 → 8 → 16 (sequenziell).
- **Kein Platzhalter:** Jeder Task nennt Datei, Symbol, Testnamen, Kommando und erwartetes
  Ergebnis; jeder Schritt ist ausführbar und sein Ausgang messbar.
- **AC-Abdeckung:** siehe Matrix unten — jedes AC der Spec hat mindestens einen Task.
- **Spec-Treue:** Keine Entscheidung aus D1–D8 wird neu verhandelt; die zwei Approval-Hinweise
  (a)/(b) sind als K-3/K-4 eingeplant, nicht als neue Frage.

| AC | Tasks |
|---|---|
| AC-1189-01 | 1 |
| AC-1189-02 | 1 |
| AC-1189-03 | 3, 10 |
| AC-1189-04 | 3, 10 |
| AC-1189-05 | 4 |
| AC-1189-06 | 4 |
| AC-1189-07 | 3 |
| AC-1189-08 | 3 |
| AC-1189-09 | 10 |
| AC-1189-10 | 1, 3 |
| AC-1189-11 | 1 |
| AC-1189-12 | 10 |
| AC-1189-13 | 10 |
| AC-1189-14 | 14 |
| AC-1189-15 | 13, 14 |
| AC-1189-16 | 13, 14 |
| AC-1189-17 | 12, 14 |
| AC-1189-17a | 11, 13 |
| AC-1189-17b | 13 |
| AC-1189-18 | 14 |
| AC-1189-19 | 11 |
| AC-1189-20 | 15 |
| AC-1189-21 | 1, 3, 4, 8, 10 (Regressionsnetz G1–G8) |
| AC-1189-22 | Gate 6 |
| AC-1189-23 | 10 |
| AC-1189-24a | 14 |
| AC-1189-24b | 4, 15 |
| AC-1189-24c | 10 |
| AC-1189-25 | 5, 6, 7, 8, 9 |
| AC-1189-26 | 5, 6, 7, 8 |
| AC-1189-27 | 11 |
| AC-1189-28 | 13 |
| AC-1189-29 | 13 |
| AC-1189-30 | 1, 8, Gate 5 |
| AC-1189-31 | 14 |
| AC-1189-32 | 1–7 (Docstrings), 16 (Doku) |
| AC-1189-33 | 14 |
| AC-1189-34 | 13 |

## DoD-Checkliste

- [ ] Alle 16 Tasks abgeschlossen; jeder Task-Test wurde **beobachtet** (rot → grün), nicht
      angenommen.
- [ ] Verifikations-Gate 1–6 vollständig belegt (rc-Werte, Testzahlen, Smoke-Test-Ausgaben).
- [ ] AC-Matrix vollständig abgedeckt; keine AC ohne Task.
- [ ] `config/project-config.schema.json` und `.meta-config/project.yaml` byte-identisch;
      kein neuer Env-Key, kein neues Config-Feld.
- [ ] `.meta-config/temp-env-allowlist.yaml` unverändert (Guard grün ohne neue Zeile).
- [ ] `tests/conftest.py` unverändert; die Grenze „pytest ohne `--basetemp`" ist in §5.5
      dokumentiert.
- [ ] D8 vollständig: §5.5-Satz, Option-C-Verweis der Vorgänger-Spec, drei Helfer-Docstrings
      (Tasks 5/6/7), `tmp_sink_location_error`-Docstring (Task 1), `TmpSinkError`-Docstring.
- [ ] Ein Commit pro Task, Englisch, Conventional Commits, ≤ 72 Zeichen, **ohne BOM**; kein
      Push/Tag/Merge (Rolle `git`).
- [ ] Plan-Status auf `IN PROGRESS`/`complete` nachgezogen und Ledger-Checkboxen aktuell.

