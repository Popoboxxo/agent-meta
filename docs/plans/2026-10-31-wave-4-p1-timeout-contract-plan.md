---
pipeline_stages:
  implement: 1
status: geplant
date: 2026-10-31
base-commit: ff334aa3
trace:
  - SPEC-test-hygiene-945
  - issue-945
---

# Welle 4 / P1 — Timeout-Contract + Hook-Slice-Isolation (Implementation Plan)

> Status: Entwurf (Plan)
>
> **Kein Freigabe-Marker in diesem Dokument.** Die zugehörige Spec ist mit
> `APPROVED (2026-10-31)` freigegeben (durch den User, nie durch den Planer);
> dieser Plan wird erst durch den User bzw. den Orchestrator zur Ausführung
> freigegeben. Bis dahin gilt das Spec/Plan-Gate (`spec-plan-workflow`).

**Goal:** P1 der Welle 4 stellt den zentralen Timeout-Contract (`SLOW_TIMEOUT`) bereit, zieht die neun Hook-Testmodule auf `tmp`-isolierte Projektwurzeln (gemeinsame Fixture `hook_project_root`, Decoy-Projekt für das Containment-Modul) und setzt `timeout=` an allen 67 Subprozess-Aufrufen dieser Module; ein neuer AST-Guard macht `cwd=` und `timeout=` dauerhaft zur Pflicht. P1 schließt AC1 lokal beweisbar und den Hook-Slice von AC3.

**Architecture:** Kein neues Subsystem. `tests/timeouts.py` bekommt genau eine Konstante (`SLOW_TIMEOUT`, Default 900, IC-1); `tests/conftest.py` bekommt genau eine modul-scoped Fixture (`hook_project_root` über `tmp_path_factory`, IC-3), die von den Modulen mit Modul-Global per modul-scoped `autouse`-Fixture gebunden wird, ohne eine einzige `_run_hook`-Aufrufstelle anzufassen. `tests/test_repo_containment_hook.py` erhält statt des Echt-Checkouts ein Decoy-Projekt mit aktiver `repo_containment`-Konfiguration (ADR-3, fünf Invarianten). Die `timeout=`-Adoption ist mechanisch und folgt ausschließlich der Klassen-Tabelle IC-2; der neue statische Guard `tests/test_hook_test_isolation.py` prüft danach Anwesenheit von `cwd=` und `timeout=` über AST (IC-6).

**Tech Stack:** Python 3.9+ (stdlib only), pytest (ohne `pytest-timeout`), Bash-Hooks als Testsubjekte, Markdown.

**Spec:** `docs/specs/2026-10-30-test-hygiene-945-design.md`
**Spec-ID:** SPEC-test-hygiene-945 (Spec-Status APPROVED 2026-10-31, Revision 3.1)
**Phase:** P1 aus `## Phasen` der Spec, Größe **L (F7: 9-20 Dateien)**, 14 Dateien.
**Pipeline:** Stage `implement` → Task 1 (`pipeline_stages.implement: 1`); alle weiteren Tasks sind Folgeschritte derselben Stage.
**Aufwand:** ~90 geänderte Zeilen in 14 Dateien (Spec §P1 „Aufwand"); eine Detailschätzung liefert `effort-estimator` (Textverweis, hier nicht berechnet).
**Vorbedingung (außerhalb dieses Plans):** Feature-Branch durch die Rolle `git` (Vorschlag `feat/wave4-p1-timeout-contract`); kein Commit auf `main`.

## Trace-Anker

`spec-id: SPEC-test-hygiene-945` — referenziert über `**Spec:** docs/specs/2026-10-30-test-hygiene-945-design.md`. Die Spec ist bewusst `*-design.md` benannt (`scripts/lib/consistency/spec_plan.py` klassifiziert nur dieses Muster als Spec).

## Ausgangslage (verifiziert 2026-10-31 gegen `main` `ff334aa3`)

| Fakt | Beleg |
|---|---|
| 67 Subprozess-Aufrufstellen in 9 Modulen — 20 `test_orchestrator_guard_hook.py`, 15 `test_repo_containment_hook.py`, 15 `test_dod_push_check_hook.py`, 8 `test_hook_common_lib.py`, 3 `test_graphify_guard_hooks.py`, 2 `test_artifact_freshness_hook.py`, 2 `test_release_gate_checksums.py`, 1 `test_pre_release_check_hook.py`, 1 `test_auto_github_release_hook.py` | je Modul nachgezählt (Spec §P1-Slice, Rev. 3) |
| **keiner** dieser 67 Aufrufe trägt `timeout=` | die drei gebremsten Stellen liegen in `tests/test_antigravity_hooks_registration.py::_repo_status` (`:268`, `:277`, `:404`) und damit außerhalb des P1-Sets |
| 66 neue `timeout=`-Keywords; die 67. Stelle ist `tests/test_hook_common_lib.py::_scan` (`subprocess.run(..., timeout=timeout)`) und erhält nur den Default `SCRIPT_TIMEOUT` statt `None` | `tests/test_hook_common_lib.py:_scan` |
| **13** Aufrufe ohne `cwd=`: 8 in `test_hook_common_lib.py` (`_call` + `_scan` + 6 direkte), 3 in `test_graphify_guard_hooks.py`, 1 in `test_pre_release_check_hook.py::_run_dispatcher`, 1 in `test_release_gate_checksums.py::_run_dispatcher` | `grep -c 'cwd='` je Datei; IC-6 Regel 1 verlangt `cwd=` an jedem Aufruf der neun Module |
| **10** Stellen in `test_repo_containment_hook.py` nutzen den Echt-Checkout als Prozess-`cwd`: 1 Default (`else _REPO_ROOT`) + 9 Inline `cwd=str(_REPO_ROOT)` | `grep -n` je Muster |
| `_PROJECT_ROOT` wird import-time gebunden (`tempfile.mkdtemp` + `atexit`), einziger import-time Konsument ist der `parametrize`-Block von `test_missing_or_non_scalar_tool_name_fails_closed` | `tests/test_orchestrator_guard_hook.py:_PROJECT_ROOT` + `:1613` |
| Default-`cwd` von `_run_hook` ist `_REPO_ROOT`; Kind-Prozess-`cwd` ≠ Payload-Wurzel ist die diskriminierende Eigenschaft (nicht „Echt-Checkout vs. `tmp`") | `tests/test_repo_containment_hook.py:_run_hook`, ADR-3 |
| `--basetemp`-Guard in `tests/conftest.py::pytest_configure` ist **warn-only** (kein `pytest.exit`, kein `pytest.fail`) | `tests/conftest.py` Docstring |
| `.meta-config/project.yaml` trägt `orchestrator.strict: true` sowie `repo_containment.enabled: true` + `tmp-sink.path: .tmp` | `.meta-config/project.yaml:306`, `:393` |
| `tests/test_hook_test_isolation.py` existiert **nicht** (P1 legt sie an) | `glob` ohne Treffer |

## Global Constraints

- **TDD mit gemessenen Rot/Grün-Zahlen:** jeder Task beginnt mit einem Step, der die Zielbedingung als *heute verletzt* nachweist (Rot-Zählung im Step). Reine Mechanik-Steps (Adoption identischer Keyword-Muster) werden ausdrücklich als **Charakterisierung** ausgewiesen: `0 failed` vor und nach der Änderung bei unveränderter Testanzahl; die Zahl der geänderten Aufrufstellen ist der Rot-Beleg.
- **Keine neue Dependency.** Kein `pytest-timeout`, kein `pytest-rerunfailures`; `tests/requirements.txt` bleibt unverändert.
- **Keine `pytest.ini` / `pyproject.toml` / `setup.cfg`.** Kein globaler Timeout per Konfigurationsdatei; der Contract lebt in `tests/timeouts.py` und an den Aufrufstellen.
- **Keine handgeschriebenen generierten Dateien.** P1 rendert nichts: kein `scripts/sync.py`-Lauf als Task-Schritt, keine Änderung an `.claude/hooks/`, `.agents/`, `.opencode/`, `.gemini/`.
- **`-n 2 --dist loadfile` bleibt unangetastet.** Die Fixture ist modul-scoped (pro Worker und Modul einmalig, IC-3); kein Session-Scope, keine Anpassung an Workflows oder Shard-Listen.
- **Kein AC-01-Rebaseline — Invariante, nicht Ergebnis:** P1 ändert kein gerendertes Artefakt, also bleibt `tests/fixtures/ac01-baseline/hashes.json` byte-identisch. Wer nach P1 einen Hash neu pinnt, hat einen Fehler gemacht; es gibt für P1 nichts zu rebaselineen.
- **Werte werden nicht neu entschieden:** `SLOW_TIMEOUT` = 900 (IC-1), Klassen-Mapping ausschließlich IC-2, Fixture-Contract IC-3, Per-Modul-Verhalten IC-4, Guard-Regeln IC-6. Bestandsliterale (`30/120/180/300/600/900-Literal`) bleiben unverändert (IC-2 „Bestandswerte").
- **Kein `isolation: "worktree"`.** Arbeit direkt im Projektverzeichnis; Schreiben nur im Projektroot und `.tmp/`.
- **Python 3.9-kompatibel:** keine `X | Y`-Annotation in Modulen ohne `from __future__ import annotations` (siehe Klarstellung K-2), kein `match`, `Optional[...]`/`Union[...]` statt PEP-604.
- **Testkommando:** `python3 -m pytest <pfade> -q` (`rtk pytest` ist defekt). Liegt der effektive Basetemp im Repo, warnt `tests/conftest.py::pytest_configure` — das ist erwartet und kein Fehler; kein `/tmp`-Literal in Kommandos.
- **Commits:** Englisch, Conventional Commits (`test:`/`docs:` wie in `docs/plans/2026-10-31-bug-batch-plan.md` üblich), erste Zeile ≤ 72 Zeichen, Imperativ, ohne BOM. Ein Commit pro Task; Push/Tag/Branch ausschließlich Rolle `git`.
- **Doku-Sprache:** Plan und `tests/README.md` Deutsch, Code/Commit Englisch.

## Klarstellungen und Abweichungen gegenüber den Spec-Belegen

Beim Erstellen des Plans durch Lesen und `grep` geprüft; keine inhaltliche Abweichung von IC-1 bis IC-6, nur Präzisierungen:

- **K-1 (Fixture-Geltungsbereich):** IC-3 nennt „die **sieben** Module mit Modul-Global". Im Checkout existiert genau **ein** solcher Modul-Global (`_PROJECT_ROOT` in `test_orchestrator_guard_hook.py`); fünf der acht Nicht-Containment-Module sind bereits `tmp`-basiert und reichen ihre Wurzel pro Aufruf durch (`test_dod_push_check_hook.py`, `test_artifact_freshness_hook.py`, `test_pre_release_check_hook.py`, `test_auto_github_release_hook.py`, `test_release_gate_checksums.py`), `test_graphify_guard_hooks.py` nutzt `tmp_path` pro Aufruf. Der Plan folgt deshalb **IC-4 als normative Per-Modul-Fassung**: die Fixture wird im Guard-Modul gebunden (bestehender Global) und in `test_hook_common_lib.py` neu eingeführt (dort braucht `_call` eine Wurzel); die sechs übrigen Module behalten ihre per-Test-Wurzel — die Gleichheitsregel „Kind-`cwd` == Payload-Wurzel" gilt dort unverändert, ohne Umbau der Aufrufstellen.
- **K-2 (Python-3.9-Form des Globals):** der IC-3-Schnipsel `_PROJECT_ROOT: Path | None = None` ist in `tests/test_orchestrator_guard_hook.py` **nicht** importierbar, weil das Modul kein `from __future__ import annotations` hat und eine Modul-Variable-Annotation unter 3.9 zur Laufzeit ausgewertet wird (`TypeError: unsupported operand type(s) for |`). Der Plan schreibt `_PROJECT_ROOT: Optional[Path] = None` (plus `from typing import Optional`). In `tests/test_repo_containment_hook.py` ist `from __future__ import annotations` vorhanden (Zeile 20) — dort ist die Kurzform zulässig; der Plan nutzt trotzdem `Optional[Path]` für ein einheitliches Muster.
- **K-3 (Commit-Granularität):** die Spec nennt vier interne Commits (Konstante → Fixture/Bindung/Decoy → `timeout=`-Adoption → Guard). Der Plan schneidet acht reviewbare Tasks mit je einem Commit; die Spec-Reihenfolge bleibt als Gruppenfolge erhalten, die beiden Doku-Commits kommen hinzu. Damit ist jeder Commit für sich grün (die Spec-Begründung) und Isolation bleibt vom Timeout-Thema getrennt.
- **K-4 (zwei zusätzliche `cwd=`):** IC-4 notiert für `test_pre_release_check_hook.py` und `test_release_gate_checksums.py` „nur `timeout=`". Verifiziert fehlt dort je einem Aufruf (`_run_dispatcher`) das `cwd=`; IC-4-Schlussregel und IC-6 Regel 1 verlangen es. Beide Stellen bekommen `cwd=str(project_root)` (Task 5), sonst ändert sich an diesen Modulen nichts.
- **K-5 (fremde `_PROJECT_ROOT`-Treffer):** `tests/test_admin_server.py` und `tests/test_ai_providers_roundtrip_847.py` definieren ebenfalls `_PROJECT_ROOT`, liegen aber außerhalb des P1-Sets und bleiben unberührt.

## Task-Übersicht

| # | Task | Agent | Depends on | Dateien | Rot/Grün-Erwartung |
|---|---|---|---|---|---|
| 1 | `SLOW_TIMEOUT` + Docstring-Env-Liste | junior-developer | — | 1 | Rot: `ImportError`; Grün: 4 Assertions, 0 Fehlschläge |
| 2 | Fixture `hook_project_root` + Bindung im Guard-Modul | senior-developer | 1 | 2 | Rot: 1 Import-Zeit-Nebeneffekt; Grün: `0 failed`, Baseline-Anzahl |
| 3 | `cwd=` in `test_hook_common_lib.py` + `test_graphify_guard_hooks.py` | developer | 2 | 2 | Rot: 11 fehlende `cwd=`; Grün: 0, `0 failed` |
| 4 | Decoy-Projekt im Containment-Modul (ADR-3) | senior-developer | — | 1 | Rot: 10 Echt-Checkout-`cwd`; Grün: 0, `0 failed` |
| 5 | `timeout=`-Adoption in den neun Modulen | developer | 2, 3, 4 | 9 | Rot: 66 fehlende `timeout=`; Grün: 0, `0 failed` |
| 6 | AST-Guard `tests/test_hook_test_isolation.py` | developer | 5 | 1 | Rot-Beleg: 15 Findings auf dem Stand vor der Adoption, 1 Finding auf einer gestrippten Kopie; Grün: `26 passed` |
| 7 | `tests/README.md` (Timeout-Tabelle + CI-Job-Timeouts) | junior-developer | 1 | 1 | Doku, `0 failed` (kein Test berührt) |
| 8 | `CHANGELOG.md`-Sammel-Eintrag | junior-developer | 5, 6, 7 | 1 | Doku, `check_changelog_mentions_new_files` ohne Befund |

## File Structure

- Modify: `tests/timeouts.py` — `SLOW_TIMEOUT` + Docstring-Env-Liste (Task 1, IC-1)
- Modify: `tests/conftest.py` — Fixture `hook_project_root` (Task 2, IC-3)
- Modify: `tests/test_orchestrator_guard_hook.py` — Global `None` + `autouse`-Bindung, ein Parametrize-Block in den Testkörper, `timeout=` (Tasks 2, 5)
- Modify: `tests/test_repo_containment_hook.py` — Decoy-Fixture + 10 `cwd=`-Stellen, zwei Docstrings, `timeout=` (Tasks 4, 5, ADR-3)
- Modify: `tests/test_hook_common_lib.py` — neuer Global + `autouse`-Bindung, `cwd=` an 8 Stellen, `_scan`-Default, `timeout=` (Tasks 3, 5, IC-3/IC-4)
- Modify: `tests/test_graphify_guard_hooks.py` — `cwd=tmp_path` an 3 Stellen, `timeout=` (Tasks 3, 5, IC-4)
- Modify: `tests/test_dod_push_check_hook.py` — `timeout=` an 15 Stellen (Task 5)
- Modify: `tests/test_artifact_freshness_hook.py` — `timeout=` an 2 Stellen (Task 5)
- Modify: `tests/test_pre_release_check_hook.py` — `cwd=` + `timeout=` an 1 Stelle (Task 5)
- Modify: `tests/test_auto_github_release_hook.py` — `timeout=` an 1 Stelle (Task 5)
- Modify: `tests/test_release_gate_checksums.py` — `cwd=` + `timeout=` an 2 Stellen (Task 5)
- Create: `tests/test_hook_test_isolation.py` — statischer AST-Guard (Task 6, IC-6)
- Modify: `tests/README.md` — `SLOW_TIMEOUT`-Zeile + Abschnitt „CI-Job-Timeouts" (Task 7, IC-13)
- Modify: `CHANGELOG.md` — `[Unreleased]`-Sammel-Eintrag „CI robustness (#945, residual)" (Task 8, IC-13)

Summe: **14** Dateien — 13 `Modify:`-Pfade (die Hook-Module erscheinen je Task in der `Files:`-Liste erneut, besessen sind sie einmal) und 1 `Create:`-Pfad.

---

### Task 1: `SLOW_TIMEOUT`-Konstante und Docstring-Env-Liste

**Agent:** junior-developer
**Depends on:** —

**Files:**
- Modify: `tests/timeouts.py`

**Interfaces:** Produces: `SLOW_TIMEOUT: int = _env_seconds("AGENT_META_SLOW_TIMEOUT", 900)` plus die Docstring-Zeile für `AGENT_META_SLOW_TIMEOUT` (IC-1, Wortlaut verbatim). Consumes: `_env_seconds` unverändert (nicht-ganzzahlig, leer oder ≤ 0 → Default; Import wirft nie).

- [ ] **Step 1: Rot nachweisen (1 Fehlschlag).** `python3 -c "from tests.timeouts import SLOW_TIMEOUT"` → `ImportError: cannot import name 'SLOW_TIMEOUT'`, Exitcode 1. Ausgabe im Ledger festhalten.
- [ ] **Step 2: Block einfügen.** Den IC-1-Block **wörtlich** (drei `#:`-Kommentarzeilen + Assignment) direkt nach dem `SCRIPT_TIMEOUT`-Assignment am Dateiende einfügen. `_DEFAULT_SYNC_TIMEOUT`, `_DEFAULT_SCRIPT_TIMEOUT`, `_env_seconds`, `SYNC_TIMEOUT`, `SYNC_VALIDATE_TIMEOUT`, `SCRIPT_TIMEOUT` bleiben byte-identisch.
- [ ] **Step 3: Docstring mitpflegen.** In der Env-Liste des Modul-Docstrings eine vierte Zeile im RST-Stil der drei Nachbarzeilen ergänzen: Env-Name `AGENT_META_SLOW_TIMEOUT`, Pfeil, Ziel `:data:`SLOW_TIMEOUT`` (Spaltenausrichtung der Nachbarzeilen übernehmen). Der Satz „importing this module must never raise" bleibt stehen.
- [ ] **Step 4: Grün nachweisen (4 Assertions, 0 Fehlschläge).** `python3 -c "from tests.timeouts import SLOW_TIMEOUT as t; assert t == 900, t"`; `AGENT_META_SLOW_TIMEOUT=1200 python3 -c "from tests.timeouts import SLOW_TIMEOUT as t; assert t == 1200, t"`; `AGENT_META_SLOW_TIMEOUT=abc python3 -c "from tests.timeouts import SLOW_TIMEOUT as t; assert t == 900, t"`; `AGENT_META_SLOW_TIMEOUT=0 python3 -c "from tests.timeouts import SLOW_TIMEOUT as t; assert t == 900, t"` — alle Exitcode 0.
- [ ] **Step 5: Bestand unverändert belegen.** `python3 -c "from tests.timeouts import SYNC_TIMEOUT, SYNC_VALIDATE_TIMEOUT, SCRIPT_TIMEOUT; assert (SYNC_TIMEOUT, SYNC_VALIDATE_TIMEOUT, SCRIPT_TIMEOUT) == (180, 180, 60)"` → Exitcode 0; `grep -n 'SLOW_TIMEOUT' tests/timeouts.py` → genau zwei Treffer (Docstring-Zeile, Assignment).
- [ ] **Step 6: Commit.** `git add tests/timeouts.py` und `git commit -m "test: add SLOW_TIMEOUT constant for long-running helpers"`.

---

### Task 2: Fixture `hook_project_root` und Bindung im Orchestrator-Guard-Modul

**Agent:** senior-developer
**Depends on:** 1

**Files:**
- Modify: `tests/conftest.py`
- Modify: `tests/test_orchestrator_guard_hook.py`

**Interfaces:** Produces: `hook_project_root(tmp_path_factory) -> Path`, `scope="module"`, `mktemp("hook-project")`, Inhalt `<root>/.meta-config/project.yaml` (Kopie der Repo-Config mit `orchestrator.strict: true`) und `<root>/.claude/hooks/`; im Guard-Modul `_PROJECT_ROOT: Optional[Path] = None` + modul-scoped `autouse`-Fixture `_bind_project_root`. Consumes: `.meta-config/project.yaml` des Repos (IC-3).

- [ ] **Step 1: Baseline messen und Rot nachweisen.** (a) `python3 -m pytest tests/test_orchestrator_guard_hook.py -q` → `0 failed`; die gesammelte Testanzahl **X** aus der Zusammenfassung ins Ledger schreiben. (b) `python3 -c "import tests.test_orchestrator_guard_hook as m; print(m._PROJECT_ROOT)"` → druckt einen `mkdtemp`-Pfad und legt bei jedem Import ein Verzeichnis an; **1 verletzte Invariante** (`import`-Zeit-Nebeneffekt). (c) `sha256sum .claude/hooks/.guard-audit.log` (oder `absent`, wenn die Datei fehlt) notieren.
- [ ] **Step 2: Fixture in `tests/conftest.py` anlegen.** `@pytest.fixture(scope="module") def hook_project_root(tmp_path_factory):` → `root = tmp_path_factory.mktemp("hook-project")`; `(root / ".meta-config").mkdir()`; `shutil.copy(_AGENT_META_ROOT / ".meta-config" / "project.yaml", root / ".meta-config" / "project.yaml")`; `(root / ".claude" / "hooks").mkdir(parents=True)`; `return root`. Imports ergänzen: `import shutil`, `import pytest` (`from pytest import PytestWarning` bleibt). Kurzer Docstring: kein `.guard-audit.log` anlegen (der Hook erzeugt es), kein Repo-Baum-Kopie, unabhängig vom warn-only Basetemp-Guard (IC-3 „Nicht-Zusicherung").
- [ ] **Step 3: Guard-Modul auf Fixture-Bindung umstellen.** `import atexit` und `import tempfile` entfernen (`shutil` bleibt für `_BASH`); die Zeilen `_PROJECT_ROOT = Path(tempfile.mkdtemp(...))` sowie die drei folgenden Setup-Zeilen und `atexit.register(...)` durch `_PROJECT_ROOT: Optional[Path] = None` ersetzen (Klarstellung K-2: **nicht** `Path | None`) und `from typing import Optional` ergänzen. Danach die modul-scoped `autouse`-Fixture `_bind_project_root(hook_project_root)` wörtlich nach dem IC-3-Muster: `global _PROJECT_ROOT`, Zuweisung, `yield`, Rücksetzen auf `None`.
- [ ] **Step 4: Parametrize-Block in den Testkörper ziehen.** In `test_missing_or_non_scalar_tool_name_fails_closed` verlieren die vier Payload-Dicts im `@pytest.mark.parametrize("payload", [...])`-Block (u. a. `{"tool_input": {}}`, `{"tool_name": None, ...}`, `{"tool_name": ["Bash"], ...}`, `{"tool_name": {"name": "Bash"}, ...}`) jeweils den Schlüssel `"cwd": _PROJECT_ROOT.as_posix()`; im Testkörper wird `_run_hook({**payload, "cwd": _PROJECT_ROOT.as_posix()})` aufgerufen. Die Parametrisierung (vier Fälle) bleibt erhalten. **Das ist die einzige Aufrufstellen-Änderung im Modul.**
- [ ] **Step 5: Grün nachweisen.** `python3 -c "import tests.test_orchestrator_guard_hook as m; assert m._PROJECT_ROOT is None; print('ok')"` → `ok`, kein neues Verzeichnis unter dem System-Temp; `python3 -m pytest tests/test_orchestrator_guard_hook.py -q` → `0 failed` und Testanzahl **exakt X** aus Step 1 (differenzfrei).
- [ ] **Step 6: Beweistest unangetastet belegen.** `python3 -m pytest "tests/test_orchestrator_guard_hook.py::test_strict_cases_never_write_the_repo_audit_log" -q` → `1 passed`; `git diff -U0 -- tests/test_orchestrator_guard_hook.py` enthält **keine** Änderungszeile aus diesem Testkörper (er ist der Regressionsanker, ADR-2).
- [ ] **Step 7: AC1 lokal belegen.** `sha256sum .claude/hooks/.guard-audit.log` (bzw. `absent`) erneut ausführen → identisch zu Step 1 (c). Zusätzlich `python3 -m pytest tests/test_basetemp_guard.py -q` → `0 failed` (Fixture hängt nicht am warn-only Guard).
- [ ] **Step 8: Commit.** `git add tests/conftest.py tests/test_orchestrator_guard_hook.py` und `git commit -m "test: add hook_project_root fixture and bind guard module"`.

---

### Task 3: `cwd=` in `test_hook_common_lib.py` und `test_graphify_guard_hooks.py`

**Agent:** developer
**Depends on:** 2

**Files:**
- Modify: `tests/test_hook_common_lib.py`
- Modify: `tests/test_graphify_guard_hooks.py`

**Interfaces:** Produces: `test_hook_common_lib.py::_PROJECT_ROOT` (`Optional[Path]`, `None`) + `autouse`-Fixture `_bind_project_root`, `cwd=` an allen 8 Aufrufen; `test_graphify_guard_hooks.py` `cwd=str(tmp_path)` an allen 3 Aufrufen. Consumes: `hook_project_root` aus `tests/conftest.py` (IC-3-Muster).

- [ ] **Step 1: Rot messen (11 fehlende `cwd=`).** `grep -c 'cwd=' tests/test_hook_common_lib.py` → `0`; `grep -c 'cwd=' tests/test_graphify_guard_hooks.py` → `0`; Aufrufstellen: `grep -c 'subprocess.run(' tests/test_hook_common_lib.py` → `8`, `grep -c 'subprocess.run(' tests/test_graphify_guard_hooks.py` → `3`. Baseline: `python3 -m pytest tests/test_hook_common_lib.py tests/test_graphify_guard_hooks.py -q` → `0 failed`, Anzahl **Y** notieren.
- [ ] **Step 2: `test_hook_common_lib.py` binden.** `_PROJECT_ROOT: Optional[Path] = None` (Modul-Ebene, direkt nach `_BASH`) plus modul-scoped `autouse`-Fixture `_bind_project_root(hook_project_root)` nach dem IC-3-Muster (`global`, `yield`, Rücksetzen auf `None`). Kein `atexit`, kein `tempfile`.
- [ ] **Step 3: `cwd=` an die 8 Stellen setzen.** `_call` erhält `cwd=str(_PROJECT_ROOT)` im `subprocess.run(...)`; dieselbe Keyword-Zeile erhalten die sieben direkten Aufrufe: `_scan`, `test_hook_json_get_lone_surrogate_is_not_dropped`, `test_hook_json_get_invalid_utf8_input_is_not_dropped`, `test_shell_scan_py_emits_compilable_source`, `_resolve`, `test_shell_resolver_py_emits_compilable_source`, `test_command_start_skips_pure_assignment_statements`. `env`-Dicts (inkl. `dict(os.environ, LC_ALL=...)`) bleiben unverändert — PATH/HOME bleiben echt (IC-4).
- [ ] **Step 4: `test_graphify_guard_hooks.py` isolieren.** `cwd=str(tmp_path)` an die drei Runner-Aufrufe in `test_guard_passes_through_when_graphify_not_installed`, `test_guard_invokes_valid_graphify_on_path`, `test_guard_rejects_malicious_graphify_bin_env_override`; die reduzierten `env={"PATH": ..., "GRAPHIFY_BIN": ...}`-Dicts bleiben unverändert (IC-4).
- [ ] **Step 5: Grün nachweisen.** `grep -c 'cwd=' tests/test_hook_common_lib.py` → `8`, `grep -c 'cwd=' tests/test_graphify_guard_hooks.py` → `3`; `python3 -m pytest tests/test_hook_common_lib.py tests/test_graphify_guard_hooks.py -q` → `0 failed`, Testanzahl exakt **Y** aus Step 1.
- [ ] **Step 6: PATH-abhängige Proben gezielt prüfen.** `python3 -m pytest tests/test_hook_common_lib.py -q -k "have_python or python_bin or json_usable"` → `0 failed` (die `command -v python3`-/Interpreter-Proben laufen mit echtem PATH aus `_call`).
- [ ] **Step 7: Commit.** `git add tests/test_hook_common_lib.py tests/test_graphify_guard_hooks.py` und `git commit -m "test: give hook_common_lib and graphify tests an explicit cwd"`.

---

### Task 4: Decoy-Projekt im Containment-Modul (ADR-3)

**Agent:** senior-developer
**Depends on:** —

**Files:**
- Modify: `tests/test_repo_containment_hook.py`

**Interfaces:** Produces: modul-scoped Fixture `_decoy_project(tmp_path_factory)` (`mktemp("containment-decoy")`, aktive `repo_containment`-Config mit `tmp-sink.path: ".tmp"`, `.claude/hooks/`) + `_DECOY_ROOT: Optional[Path]` mit `autouse`-Bindung; `_run_hook`-Default und neun Inline-Stellen laufen auf `_DECOY_ROOT`. Consumes: vorhandener Helfer `_write_config` im Modul.

- [ ] **Step 1: Rot messen (10 Echt-Checkout-`cwd`).** `grep -c 'cwd=str(_REPO_ROOT)' tests/test_repo_containment_hook.py` → `9`; `grep -c 'else _REPO_ROOT' tests/test_repo_containment_hook.py` → `1`; Baseline: `python3 -m pytest tests/test_repo_containment_hook.py -q` → `0 failed`, Anzahl **Z** notieren.
- [ ] **Step 2: Decoy-Fixture anlegen.** `_DECOY_ROOT: Optional[Path] = None` auf Modul-Ebene und `@pytest.fixture(scope="module") def _decoy_project(tmp_path_factory):` → `root = tmp_path_factory.mktemp("containment-decoy")`; `_write_config(root, 'repo_containment:\n  enabled: true\n  tmp-sink:\n    enabled: true\n    path: ".tmp"\n')`; `(root / ".claude" / "hooks").mkdir(parents=True)`; `return root`. Die Config wird **explizit** geschrieben (nicht aus dem Repo kopiert), damit eine Änderung der Repo-Config die Zähne des Decoys nicht still entschärft.
- [ ] **Step 3: Bindung herstellen.** Modul-scoped `autouse`-Fixture `_bind_decoy(_decoy_project)` setzt `global _DECOY_ROOT`, `yield`, Rücksetzen auf `None`; Aufräumen ausschließlich über `tmp_path_factory` (ADR-3, Invariante 5 — kein `atexit`).
- [ ] **Step 4: Default umstellen.** In `_run_hook` `cwd=str(process_cwd if process_cwd is not None else _REPO_ROOT)` → `... else _DECOY_ROOT`; den Docstring von „It defaults to the agent-meta repo root, which *does* carry `.meta-config/`" auf „It defaults to a decoy project that carries `.meta-config/` but is never a payload root" umschreiben (ADR-3 nennt genau diese Entschärfung).
- [ ] **Step 5: Die neun Inline-Stellen umstellen.** Jedes `cwd=str(_REPO_ROOT)` → `cwd=str(_DECOY_ROOT)`; betroffen sind die Runner-Aufrufe in `test_garbage_python_interpreter_fails_closed`, im Detector-rc-Test mit Python-Shim, in `test_payload_cwd_cannot_redefine_the_deployed_jail_root`, `test_claude_project_dir_is_a_fixed_anchor_from_the_source_tree`, `test_fixed_anchor_is_provider_neutral`, `test_write_inside_the_fixed_anchor_is_allowed`, `test_f5_unresolvable_fixed_root_fails_closed` sowie in beiden `test_missing_pyyaml_*`-Tests. `_HOOK_PATH`/`_IMPL_PATH`/`sys.path.insert` bleiben auf `_REPO_ROOT` (der Hook unter Test bleibt der echte Skriptpfad, read-only).
- [ ] **Step 6: Zweiten Docstring entschärfen.** In `test_claude_project_dir_is_a_fixed_anchor_from_the_source_tree` „even when run from the source tree" → „even when the process cwd is a project-carrying directory".
- [ ] **Step 7: ADR-3-Invarianten belegen.** `python3 -m pytest tests/test_repo_containment_hook.py -q` → `0 failed`, Testanzahl exakt **Z** aus Step 1. Zusätzlich die beiden `$PWD`-diskriminierenden Fälle einzeln: `python3 -m pytest "tests/test_repo_containment_hook.py::test_payload_cwd_cannot_redefine_the_deployed_jail_root" "tests/test_repo_containment_hook.py::test_write_inside_the_fixed_anchor_is_allowed" -q` → `2 passed` (Invariante 2: Kind-`cwd` ≠ Payload-Wurzel; Invariante 3: der Decoy bleibt aktiv, ein `$PWD`-adoptierender Hook würde hier rot).
- [ ] **Step 8: Grün-Zählung.** `grep -c 'cwd=str(_REPO_ROOT)' tests/test_repo_containment_hook.py` → `0`; `grep -c 'else _REPO_ROOT' tests/test_repo_containment_hook.py` → `0`.
- [ ] **Step 9: Commit.** `git add tests/test_repo_containment_hook.py` und `git commit -m "test: run containment hook tests from a decoy project"`.

---

### Task 5: `timeout=`-Adoption in den neun Modulen

**Agent:** developer
**Depends on:** 2, 3, 4

**Files:**
- Modify: `tests/test_orchestrator_guard_hook.py`
- Modify: `tests/test_repo_containment_hook.py`
- Modify: `tests/test_hook_common_lib.py`
- Modify: `tests/test_graphify_guard_hooks.py`
- Modify: `tests/test_dod_push_check_hook.py`
- Modify: `tests/test_artifact_freshness_hook.py`
- Modify: `tests/test_pre_release_check_hook.py`
- Modify: `tests/test_auto_github_release_hook.py`
- Modify: `tests/test_release_gate_checksums.py`

**Interfaces:** Produces: `timeout=SCRIPT_TIMEOUT` an 66 Aufrufstellen (IC-2, Klasse „Bash-Hook unter Test" / „Git-Plumbing" / „`bash -c`-Schnipsel" / „Helper-CLI") plus `_scan`-Default `SCRIPT_TIMEOUT` (67. Stelle); Consumes: `from tests.timeouts import SCRIPT_TIMEOUT` (IC-1-Importpfad, `tests` ist ein Paket).

- [ ] **Step 1: Rot messen (66 fehlende `timeout=`).** Einmalig eine Scratch-Probe in `.tmp/` legen (`ast`-basiert: zählt `subprocess.{run,call,check_output,check_call}` ohne `timeout=`-Keyword in den neun Modulen) und ausführen → **66**. Alternativ `grep -c 'timeout='` je Modul: `0` in allen neun. Zahl im Ledger festhalten.
- [ ] **Step 2: Importe setzen.** In jedem der neun Module `from tests.timeouts import SCRIPT_TIMEOUT` in den Import-Block aufnehmen (bei `test_repo_containment_hook.py`/`test_hook_common_lib.py` nach dem jeweiligen `sys.path`-Block bzw. bei den Stdlib-Imports; Reihenfolge der vorhandenen Importgruppen beibehalten).
- [ ] **Step 3: Adoption je Modul nach Aufrufklasse (IC-2).** `timeout=SCRIPT_TIMEOUT` an alle Aufrufe der Klassen „Bash-Hook unter Test", „Git-Plumbing" und „`bash -c`/`python -c`-Schnipsel":
  - `test_orchestrator_guard_hook.py` (20 Aufrufe, u. a. `_run_hook`, `_run_hook_in`, `_run_with`),
  - `test_repo_containment_hook.py` (15 Aufrufe, inkl. `_run_hook`),
  - `test_dod_push_check_hook.py` (15 Aufrufe, inkl. der vier `run = lambda *args: subprocess.run(...)`-Git-Helfer und `_assert_outcome`),
  - `test_hook_common_lib.py` (8 Aufrufstellen: `_call` und 6 direkte erhalten das Keyword neu, `_scan` nur den Default aus Step 4),
  - `test_graphify_guard_hooks.py` (3 Aufrufe),
  - `test_artifact_freshness_hook.py` (2 Aufrufe),
  - `test_release_gate_checksums.py` (2 Aufrufe, inkl. `_run_dispatcher`),
  - `test_pre_release_check_hook.py` (1 Aufruf, `_run_dispatcher`),
  - `test_auto_github_release_hook.py` (1 Aufruf).
  Kein Bestandsliteral ersetzen (IC-2 „Bestandswerte"); keine Zeile in `tests/test_antigravity_hooks_registration.py` anfassen.
- [ ] **Step 4: `_scan`-Default.** In `tests/test_hook_common_lib.py` die Signatur `def _scan(code: str, timeout: Optional[float] = None)` auf `= SCRIPT_TIMEOUT` ändern; das Keyword `timeout=timeout` im Aufruf **bleibt** (das ist die 67. Stelle, die kein neues `timeout=` erhält).
- [ ] **Step 5: Zwei residuale `cwd=` ergänzen (Klarstellung K-4).** In `test_pre_release_check_hook.py::_run_dispatcher` und `test_release_gate_checksums.py::_run_dispatcher` zusätzlich `cwd=str(project_root)` setzen; `env={"PROJECT_ROOT": str(project_root), "PATH": ...}` bleibt unverändert.
- [ ] **Step 6: Grün nachweisen (0 fehlend, `0 failed`).** Scratch-Probe aus Step 1 erneut ausführen → **0**; `grep -c 'timeout=SCRIPT_TIMEOUT'` je Modul in der Reihenfolge der Step-3-Liste → 20 / 15 / 15 / **7** / 3 / 2 / 2 / 1 / 1 = **66** (die 67. Stelle `_scan` trägt `timeout=timeout` und erhält nur den Default). Dann `python3 -m pytest tests/test_orchestrator_guard_hook.py tests/test_repo_containment_hook.py tests/test_hook_common_lib.py tests/test_graphify_guard_hooks.py tests/test_dod_push_check_hook.py tests/test_artifact_freshness_hook.py tests/test_pre_release_check_hook.py tests/test_auto_github_release_hook.py tests/test_release_gate_checksums.py -q` → `0 failed`, `0 errors`; Testanzahl exakt X (Task 2) + Y (Task 3) + Z (Task 4).
- [ ] **Step 7: AC1 nach dem Gesamtlauf erneut belegen.** `sha256sum .claude/hooks/.guard-audit.log` (bzw. `absent`) → identisch zum Wert aus Task 2, Step 1 (c).
- [ ] **Step 8: Scratch-Probe entfernen.** `.tmp/`-Datei löschen; `git status --porcelain` zeigt nur die neun Modulpfade.
- [ ] **Step 9: Commit.** `git add` die neun Modulpfade und `git commit -m "test: bound every subprocess call in the nine hook modules"`.

---

### Task 6: Statischer AST-Guard `tests/test_hook_test_isolation.py`

**Agent:** developer
**Depends on:** 5

**Files:**
- Create: `tests/test_hook_test_isolation.py`

**Interfaces:** Produces: `SCAN_SET` (neun Modulpfade, IC-6) und `find_violations(module_path) -> list[str]` (Finding nennt Datei, Funktionsname und Zeile); Tests `test_every_call_sets_cwd` / `test_every_call_sets_non_none_timeout` (je parametrisiert über die neun Module) sowie acht Scanner-Tests. Consumes: `ast`, `pathlib`, `pytest` (Stdlib + pytest, keine neue Dependency).

- [ ] **Step 1: Testdatei mit Rot-Potenzial schreiben.** Kopf-Docstring: prüft **nur die Anwesenheit** von `cwd=` und `timeout=` (Wert ≠ Literal `None`), nicht die Richtigkeit der Werte; `Popen` ist von der Timeout-Regel ausgenommen (kein Keyword) und wird erst in P3 allowlist-geführt (IC-6 „Nicht-Zusicherung", ADR-1). `SCAN_SET` als Tupel der neun Pfade; Parser: `ast.parse`, Call-Erkennung für `subprocess.run|call|check_output|check_call|Popen` inklusive Alias-Auflösung (`import subprocess as sp`, `from subprocess import run`) und `**kwargs`-Spread → fail closed (Finding).
- [ ] **Step 2: Acht Scanner-Tests ergänzen.** (1) `test_missing_timeout_is_reported`, (2) `test_timeout_none_is_reported`, (3) `test_alias_import_is_resolved`, (4) `test_from_import_is_resolved`, (5) `test_kwargs_spread_fails_closed`, (6) `test_popen_is_exempt_from_the_timeout_rule_but_needs_cwd`, (7) `test_scan_set_lists_nine_existing_modules`, (8) `test_guard_has_teeth_on_a_stripped_real_module` (kopiert `tests/test_pre_release_check_hook.py` nach `tmp_path`, entfernt alle `timeout=`-Vorkommen, erwartet **genau 1** Finding, das Datei und Funktionsname nennt). Jeder Scanner-Test baut seinen Quelltext als String — kein Repo-Schreibvorgang, keine Hook-Ausführung.
- [ ] **Step 3: Scan-Set-Tests schreiben.** `@pytest.mark.parametrize("module", SCAN_SET)` je einmal für `cwd=` und `timeout=`; Assertion `find_violations(module) == []`, Fehlermeldung listet die Findings.
- [ ] **Step 4: Rot-Beleg der Zielbedingung.** Task 5 hat die Aufrufe bereits gebremst, deshalb wird der Rot-Fall gegen den Stand **vor** der Adoption gezeigt: den Task-5-Commit per `git log --oneline -1 -- tests/test_dod_push_check_hook.py` bestimmen, `git show <hash>^:tests/test_dod_push_check_hook.py` nach `.tmp/` schreiben, den Scanner darauf anwenden → **15** Findings (alle 15 Aufrufe ohne `timeout=`, alle mit `cwd=`); `.tmp/`-Datei danach löschen. Zahl im Ledger festhalten. Zusätzlich belegt Test (8) aus Step 2 die Zähne auf einer gestrippten Kopie mit **genau 1** Finding.
- [ ] **Step 5: Grün nachweisen.** `python3 -m pytest tests/test_hook_test_isolation.py -q` → `26 passed`, `0 failed` (18 parametrisierte Scan-Set-Fälle + 8 Scanner-Fälle).
- [ ] **Step 6: Guard gegen Fehlalarm prüfen.** `python3 -m pytest tests/test_hook_test_isolation.py -q -k "popen or kwargs or alias or from_import"` → `4 passed` (kein Fehlalarm auf `Popen`, Spread und Aliase).
- [ ] **Step 7: Commit.** `git add tests/test_hook_test_isolation.py` und `git commit -m "test: add AST guard for hook test isolation and timeouts"`.

---

### Task 7: `tests/README.md` — Timeout-Tabelle und AC2-Prüfkommando

**Agent:** junior-developer
**Depends on:** 1

**Files:**
- Modify: `tests/README.md`

**Interfaces:** Produces: `SLOW_TIMEOUT`-Zeile in der Tabelle „Zentrale Timeouts" + neuer Abschnitt „CI-Job-Timeouts" mit dem manuellen AC2-Prüfkommando (IC-13). Consumes: `tests/timeouts.py` (Task 1).

- [ ] **Step 1: Tabellenzeile ergänzen.** Im Abschnitt `## Zentrale Timeouts` eine vierte Zeile im selben Format wie die `SCRIPT_TIMEOUT`-Zeile ergänzen: Konstantenname `SLOW_TIMEOUT`, Default `900 s`, Override `AGENT_META_SLOW_TIMEOUT` (IC-1). Die drei Bestandszeilen und der Satz „Ein nicht-ganzzahliger, leerer oder nicht-positiver Env-Wert fällt auf den Default zurück" bleiben unverändert.
- [ ] **Step 2: Abschnitt „CI-Job-Timeouts" ergänzen.** Direkt nach dem Timeout-Absatz ein kurzer Abschnitt: jeder CI-Job trägt `timeout-minutes` (AC2); Prüfkommando `grep -c timeout-minutes .github/workflows/orchestration-test.yml .github/workflows/validate.yml .github/workflows/scorecard.yml`; Hinweis, dass dies ein **manueller** Grep ist (kein automatisierter Test) und nach jedem neuen Job erneut auszuführen ist.
- [ ] **Step 3: Follow-up-Satz unangetastet lassen.** Der Schlussabsatz „Weitere Heavy-Module nutzen noch modul-lokale Obergrenzen; Vereinheitlichung ist ein Follow-up." bleibt **wörtlich** stehen; die Präzisierung ist P2b (IC-13), nicht P1.
- [ ] **Step 4: Belegen.** `grep -n 'SLOW_TIMEOUT' tests/README.md` → genau ein Tabellentreffer; `grep -n 'CI-Job-Timeouts' tests/README.md` → genau ein Treffer; `git diff --stat -- tests/README.md` zeigt genau diese eine Datei mit additiven Zeilen und ohne Löschung im Follow-up-Absatz.
- [ ] **Step 5: Commit.** `git add tests/README.md` und `git commit -m "docs: document SLOW_TIMEOUT and the CI timeout check"`.

---

### Task 8: `CHANGELOG.md`-Sammel-Eintrag

**Agent:** junior-developer
**Depends on:** 5, 6, 7

**Files:**
- Modify: `CHANGELOG.md`

**Interfaces:** Produces: ein Bullet unter `## [Unreleased]` mit dem Wortlaut „CI robustness (#945, residual)" (IC-13); Consumes: nichts.

- [ ] **Step 1: Platzierung prüfen.** `grep -n '^## \[' CHANGELOG.md` → `## [Unreleased]` steht vor `## [2.0.0-beta.6]`; **kein** Eintrag in eine abgeschlossene Release-Sektion (auch nicht in `[2.0.0-beta.2]`).
- [ ] **Step 2: Bullet schreiben.** Unter `## [Unreleased]` im passenden Unterabschnitt (`### Changed`, sonst als eigener Punkt vor dem ersten vorhandenen Bullet): genau ein Bullet, der (a) den Sammel-Eintrag „CI robustness (#945, residual)" trägt, (b) `SLOW_TIMEOUT` (900 s, `AGENT_META_SLOW_TIMEOUT`) nennt, (c) die Isolation der neun Hook-Testmodule gegen `tmp_path`-Projekte samt Decoy-Projekt für `repo_containment` und (d) den neuen Guard `tests/test_hook_test_isolation.py` (Pflicht für `cwd=`/`timeout=`) beschreibt. Keine Zeilen in bestehenden Release-Sektionen ändern, kein Versions-Bump.
- [ ] **Step 3: Belegen.** `grep -c '945, residual' CHANGELOG.md` → `1`; `git diff -- CHANGELOG.md` zeigt ausschließlich additive Zeilen im `[Unreleased]`-Block.
- [ ] **Step 4: Commit.** `git add CHANGELOG.md` und `git commit -m "docs: changelog entry for wave 4 test hygiene P1"`.

---

## Exit-Kriterien (P1)

- **Neuer Guard grün:** `python3 -m pytest tests/test_hook_test_isolation.py -q` → `26 passed`, `0 failed` (18 Scan-Set-Fälle über neun Module × zwei Regeln, 8 Scanner-Fälle).
- **Die neun P1-Module grün:** `python3 -m pytest` über die neun Module → `0 failed`, `0 errors`; Testanzahl exakt gleich der Summe der Baseline-Zählungen aus Task 2 (X), Task 3 (Y) und Task 4 (Z).
- **AC1 lokal:** nach dem Modullauf ist `.claude/hooks/.guard-audit.log` byte-identisch (`sha256sum` vor/nach) bzw. in beiden Messungen `absent`; `tests/test_orchestrator_guard_hook.py::test_strict_cases_never_write_the_repo_audit_log` ist unverändert und grün.
- **AC3 Hook-Slice:** 0 Subprozess-Aufrufe ohne `timeout=` in den neun Modulen (Guard-Test), 0 Aufrufe ohne `cwd=`; 66 neue `timeout=`-Keywords plus `_scan`-Default (67. Stelle).
- **ADR-3:** `grep -c 'cwd=str(_REPO_ROOT)' tests/test_repo_containment_hook.py` → `0`; Decoy trägt `.meta-config/project.yaml` mit aktivem `repo_containment` und `tmp-sink.path: .tmp`.
- **Validator:** `python3 scripts/sync.py --validate` → Exitcode 0.
- **Consistency:** `python3 scripts/consistency-check.py` → PASS ohne ERROR-Finding; `check_changelog_mentions_new_files` akzeptiert `tests/test_hook_test_isolation.py` auf Basis des `[Unreleased]`-Eintrags; `spec_plan`-Befunde für diesen Plan: keine (Sektionen, `**Spec:**`, `pipeline_stages`, keine Platzhalter).
- **AC-01 ausdrücklich unangetastet:** `git diff --exit-code -- tests/fixtures/ac01-baseline/hashes.json` → Exitcode 0; `python3 -m pytest tests/test_ac01_render_identity.py -q` → `0 failed`. **Kein Rebaseline, keine Neu-Pinnung, kein `_FIXTURE_TREES`-Edit** — P1 rendert nichts.
- **Kein Dependency-/Konfigurations-Delta:** `git diff --exit-code -- tests/requirements.txt pytest.ini pyproject.toml setup.cfg` → Exitcode 0 (Dateien unverändert bzw. weiterhin nicht vorhanden).
- **Doku:** `tests/README.md` enthält die `SLOW_TIMEOUT`-Zeile und „CI-Job-Timeouts"; `CHANGELOG.md` enthält genau einen `[Unreleased]`-Treffer „945, residual".
- **Arbeitsbaum:** `git status --porcelain` zeigt ausschließlich die 14 P1-Pfade (nach Task 8 keine `.tmp/`-Reste).

## Risiken

| Risiko | Wirkung | Mitigation |
|---|---|---|
| Import-Zeit-Konsument von `_PROJECT_ROOT` übersehen (weitere `parametrize`/Decorator-Ausdrücke) | Modul schlägt bei der Collection fehl (`NoneType`-`AttributeError`) | `grep -n '_PROJECT_ROOT'` vor der Änderung (22 Treffer; import-time ist ausschließlich der `parametrize`-Block um `:1613`) und danach; `python3 -m pytest --collect-only -q tests/test_orchestrator_guard_hook.py` als eigener Step-Beleg |
| Decoy verliert die Zähne: ein Hook, der `$PWD` adoptiert, bliebe grün | AC1-Prüfung wird zur Attrappe | Decoy-Config wird explizit mit `enabled: true` + `tmp-sink.path: .tmp` geschrieben (nicht aus dem Repo kopiert); die beiden `$PWD`-diskriminierenden Tests werden einzeln ausgeführt (Task 4, Step 7) |
| Modul-scoped Fixture kollidiert unter `-n 2 --dist loadfile` oder leakt zwischen Tests | sporadisch rote Läufe, Zustandsübertragung | modul-scoped (pro Worker/Modul einmalig), kein Session-Scope; Rücksetzen auf `None` nach `yield`; `python3 -m pytest tests/test_hook_test_isolation.py -q -n 2 --dist loadfile` als Zusatzlauf in Task 6 |
| `cwd=`-Ergänzung ändert Semantik von Tests, die relativ zum Prozess-Verzeichnis auflösen (`_run_dispatcher` mit reduziertem `env`) | rote Tests ohne echten Fehler | `cwd` zeigt auf genau die Wurzel, die der Test per `env`/Pfad schon nutzt (`project_root`/`tmp_path`); jedes Modul wird nach der Änderung einzeln gelaufen (Task 5, Step 6) |
| AST-Guard erzeugt Fehlalarm (`**kwargs`, Alias, mehrzeilige Aufrufe) und wird deshalb abgeschaltet | Regressionsschutz fällt weg | Alias-Auflösung, `**kwargs` fail closed, `Popen`-Ausnahme und vier gezielte Scanner-Tests (Task 6, Step 6); kein Allowlist-Mechanismus in P1 |

## Annahmen und Self-Review

**Annahmen:**

- `main` == `origin/main` == `ff334aa3`; die Spec ist mit Revision 3.1 freigegeben und wird nicht mehr geändert.
- Die Zählung 67 Aufrufe / 9 Module und 66 neue `timeout=`-Keywords stimmt (Spec §P1-Slice, je Modul nachgezählt); `_scan` ist die 67. Stelle.
- 13 Aufrufe ohne `cwd=` (8 + 3 + 1 + 1) ist vollständig; der AST-Guard aus Task 6 deckt Restfälle auf und ist dann maßgeblich.
- `.meta-config/project.yaml` enthält `orchestrator.strict: true` sowie eine aktive `repo_containment`-Konfiguration; die Fixture-Kopie trägt damit die `STRICT_CASES` (IC-3).
- `python3 -m pytest` ist der funktionierende Runner (`rtk pytest` ist defekt); der Basetemp-Guard warnt nur.
- Keine Annahme hängt an einer Zeilennummer: alle Fundstellen sind als `datei:symbol` benannt und vor der Ausführung per `grep` zu verifizieren.

**Self-Review:**

- Jeder Task (1-8) nennt genau **eine** Rolle aus der erlaubten Menge `junior-developer` / `developer` / `senior-developer`; keine Rolle außerhalb dieser Menge, kein Delegationsschritt.
- Die Dateiliste summiert sich auf **14** Dateien (13 Modify, 1 Create) und deckt die P1-Zeile der Spec vollständig ab; keine Datei außerhalb der Spec-Liste wird angefasst (`tests/test_admin_server.py`, `tests/test_ai_providers_roundtrip_847.py`, `tests/test_antigravity_hooks_registration.py` bleiben unberührt).
- **Kein Task berührt ein gerendertes Artefakt** (`.claude/`, `.agents/`, `.opencode/`, `.gemini/`, Agent-Templates, `hooks/`, `rules/`): ausschließlich `tests/`, `tests/README.md`, `CHANGELOG.md`.
- **Kein AC-01-Rebaseline** ist als Invariante in den Global Constraints und als Exit-Kriterium verankert.
- Jede Task hat mindestens eine messbare Akzeptanz (Rot-Zahl, Grün-Zahl, `grep`-Zählung oder Exitcode); keine Formulierung „funktioniert korrekt".
- Die Abdeckung der geforderten Punkte (a)-(f) ist vollständig: (a) Task 1 + Task 7, (b) Task 2 + Task 3, (c) Task 4, (d) Task 5, (e) Task 6, (f) Task 8.
- `pipeline_stages` deckt die Stage `implement` mit Task 1 ab; weitere Stages erfindet der Plan nicht.
- Der Plan führt **keine neue offene Frage** ein: alle Werte stammen aus IC-1/IC-2/IC-3/IC-4/IC-6, die fünf Klarstellungen K-1 bis K-5 sind Präzisierungen ohne Entscheidungsbedarf. Die einzige offene Frage der Spec (OQ-4, `continue-on-error` in `browser-test.yml`) gehört zu P6 und wird hier nicht berührt.
- Kein Approval-Marker in diesem Dokument; die Freigabe erfolgt durch den User/Orchestrator.
