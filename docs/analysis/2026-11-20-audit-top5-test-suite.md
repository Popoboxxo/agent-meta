# Audit: Test-Suite (P32 / PR 0.5 / E-06)

> REQ-ID: `PR 0.5/P32/E-06` · Branch: `chore/audit-top5-reports` @ `94a740c5` (verifiziert, nicht gewechselt) · Datum: 2026-11-20
> Internes Dokument (deutsch). Read-only-Teilaudits aus Anhang E-06 der Roadmap.

## 1. Scope und Methode

**Scope:** Strukturelle Bestandsaufnahme der pytest-Suite unter `tests/` sowie der zugehörigen Test-Infrastruktur (Requirements, CI-Workflows, conftest, Runner-Doku). Bewertet werden Layout, Umfang, Konfiguration und erkennbare Lücken/Risiken.

**Methode:** Reine **statische, read-only-Analyse** — Verzeichnis-/Dateizählung, `grep` über Quelltext und Konfiguration, Lektüre bestehender Doku (`tests/README.md`, Roadmap). Keine Ausführung von pytest, sync.py oder Szenario-Harness; keine Änderung an Code, Konfiguration, Workflows oder Issues.

**Gate G1 — explizite Sperre (2026-11-20):** Der Voll-Testlauf (`pytest tests/ …`) ist durch den Nutzer **ausdrücklich gesperrt** („P32-G1-Volltestlauf ist AUSDRÜCKLICH GESPERRT"). Diese Sperre deckt sich mit der Roadmap-Formulierung *„Gate G1 Voll-Testlauf erst nach Stufe A + Ja des Nutzers"*. **Es wurde kein Testlauf durchgeführt.** Alle Aussagen zu Laufzeit/Sharding stammen aus dokumentierten Erfahrungswerten (`tests/README.md`), nicht aus einer hier ausgeführten Messung.

**Performance-/Ergebnisaussagen:** Es werden keine Pass-/Fail-Raten, keine Laufzeiten und keine Code-Coverage-Prozente behauptet — diese wären nur durch den gesperrten Volllauf erhebbar.

## 2. Roadmap-Referenz (E-06 / PR 0.5 / P32)

- `docs/plans/2026-11-15-master-roadmap.md:63` — P32: *„E-06: jetzt (W0), pytest-cov temporär, Berichte per PR, Gate G1 Voll-Testlauf erst nach Stufe A + Ja des Nutzers"*.
- `docs/plans/2026-11-15-master-roadmap.md:154` — PR 0.5 `chore/audit-top5-reports`: *„P32 (E-06): pytest-cov temporär, Berichte per PR, Gate G1 Voll-Testlauf erst nach Stufe A + Ja des Nutzers"*, Issues `#1276 #1245 #1159-Teil`.
- `docs/plans/2026-11-15-master-roadmap.md:274` — E-06: *„jetzt (W0), pytest-cov temporär, Berichte per PR, G1 Voll-Testlauf erst nach Stufe A + Ja"*.
- Nutzer-Gate 2026-11-20: G1-Volltestlauf ausdrücklich gesperrt; nur statische/read-only-Analyse erlaubt.

Einordnung: Dieses Dokument ist einer der „Berichte per PR" (Audit-Top5). Es ersetzt weder den G1-Volllauf noch ist es dessen Freigabe.

## 3. Inventory der Test-Suite

### 3.1 Verzeichnisstruktur und Dateizahlen

Zählung statisch (`find`), ohne `__pycache__`:

| Pfad | Dateien | Rolle |
|---|---|---|
| `tests/` (Root, `test_*.py`) | 498 | pytest-Module (Flachstruktur, keine `unit/`/`integration/`-Trennung) |
| `tests/browser/` | 14 (davon 11 `test_*.py`) | Playwright-/Admin-UI-Tests |
| `tests/scenarios/` | 204 | Szenario-Harness (Configs, Asserts, `run.sh`, `registry.md`) |
| `tests/fixtures/` | 228 | Golden-/Baseline-Fixtures |
| `tests/manual/` | 20 | Manuelle Scenarios (`.md`/`.json`), Helper-Skripte — nicht pytest-kollektiert |
| `tests/routing-llm-eval/` | 15 | Promptfoo-/Routing-Eval-Katalog |
| `tests/orchestration/` | 9 | Dry-Run-Engine + Fixtures |
| `tests/automated/` | 6 | Meta-Modell (`expected-*.json`, `test-runner.py`, `test-report.md`) |

Gesamt: **509 `test_*.py`** (498 Root + 11 Browser), **526 `*.py`** unter `tests/`.

### 3.2/Testfunktionen und Marker (statisch gezählt)

| Metrik | Zahl |
|---|---|
| `def test_` / `async def test_` gesamt | 6.376 (Root 6.328, Browser 48) |
| `@pytest.mark.parametrize` | 470 |
| `@pytest.mark.skipif` | 37 |
| `@pytest.mark.xfail` | 2 |
| `@pytest.mark.enable_socket` | 4 (alle in `tests/test_viz_subserver_live.py`) |
| Laufzeit-`pytest.skip(`/`pytest.xfail(` | 31 |

Die 37 `skipif` sind überwiegend plattformbedingt begründet (z. B. `os.name == "nt"` / POSIX-Signale / Symlinks — `tests/test_admin_server_lifecycle_smoke.py:99,153,202,255`, `tests/test_repo_containment_tmp_sink.py:209,230,251,270`). Das ist nachvollziehbar, aber Windows-spezifische Pfade sind damit in Linux-CI nicht abgedeckt.

### 3.3 Coverage-Konfiguration — nicht vorhanden

Geprüft und **nicht vorhanden**: `pyproject.toml`, `pytest.ini`, `setup.cfg`, `tox.ini`, `.coveragerc`, `[tool.pytest.ini_options]`, `addopts`, `testpaths`.

- `requirements.txt:1` enthält nur `PyYAML>=6.0.3`.
- `tests/requirements.txt:1-14` deklariert `pytest`, `pytest-xdist`, `pytest-split`, `jsonschema`, `questionary`, `tomli` — **kein `pytest-cov`**.
- Einziger `pytest-cov`-Eintrag im Repo: `external/awesome-claude-code/requirements-dev.txt:7` (vendiertes External, nicht Projekt-Dependency).
- CI (` .github/workflows/orchestration-test.yml:356-361,434,497`) ruft `python -m pytest …` **ohne `--cov`** auf. Die Erwähnung „coverage" in `:83` betrifft Cross-Version-Abdeckung (3.9/3.12), nicht Code-Coverage.
- Das einzige `coverage_matrix`-Artefakt, `tests/automated/expected-test-model.json:208-230`, beschreibt ein **synthetisches L1-Modell** (`REQ-L1-001..015`, `requirement_coverage_pct: 100`) und ist eine Fixture des Meta-Runners — **keine echte Code-Coverage des Repos**. Nicht als Beleg für Abdeckung verwenden.

Fazit: Der Roadmap-Vorschlag „pytest-cov temporär" ist konsistent mit dem Ist-Zustand; eine dauerhafte Coverage-Messung ist nicht eingerichtet. Das ist erwartungskonform, aber auch der Grund, warum dieses Audit keine Coverage-Zahl liefern kann.

### 3.4 Test-Infrastruktur (dokumentiert, statisch verifiziert)

- `tests/README.md:86-91`: volle Suite lokal ~50 min (Erfahrungswert), daher nur gezielte Modulläufe lokal; volle Suite Aufgabe der CI-Shards.
- `tests/README.md:35-57`: 16 subprozess-lastige Module (459 Tests) laufen seriell `-n 0` in drei disjunkten `SUBPROCESS_SHARD`-Gruppen; 32 explizit platzierte Dateien (15 Subprozess + 17 Heavy-Fixture) werden aus dem Count-Split ausgeschlossen.
- `tests/README.md:24-33`: Worker-Cap `-n 2`, niemals `-n auto` (Subprozess-Fanout/Timeout-Flakes).
- `tests/README.md:93-108` / `tests/timeouts.py:36-69`: zentrale Hang-Guards `SYNC_TIMEOUT=180`, `SYNC_VALIDATE_TIMEOUT=180`, `SCRIPT_TIMEOUT=60`, `SLOW_TIMEOUT=900` (per Env override) — Timeout ist Hang-Guard, keine Performance-Zusicherung.
- `tests/conftest.py:62-79`: Basetemp-Guard ist bewusst **warn-only** (kein `pytest.exit`/`pytest.fail`), damit diagnostische Läufe mit In-Repo-Basetemp möglich bleiben; dokumentiertes Risiko eines rekursiven Kopierens (16 GB / 432.138 Einträge am 2026-09-20).
- `tests/browser/conftest.py:27,46-78`: Admin-Server auf Port 7421, Session-Fork; Browser-Skip wenn `playwright` fehlt. `tests/browser/test_admin_ui_keyboard.py:9` nutzt `pytest.importorskip('playwright')`.
- `.test_durations` ist **nicht eingecheckt** → CI nutzt Count-Split statt `least_duration` (`tests/README.md:59-83`, Workflow `:350-355`).

## 4. notable Lücken / Risiken (mit Belegen)

1. **Coverage nicht messbar / `--cov`-Konfiguration ohne Dependency.** `platform-configs/hacs.defaults.yaml:79` setzt `TEST_COMMANDS: "pytest tests/ --cov"`, aber `pytest-cov` ist nirgends als Dependency deklariert (nur vendoriert in `external/awesome-claude-code/requirements-dev.txt:7`). Wird dieser Plattform-Default ausgeführt, scheitert pytest an der unbekannten Option. Priorität hoch, weil es eine konkrete, ausführbare Fehlerquelle ist.
2. **Nicht registrierter Custom-Marker.** `@pytest.mark.enable_socket` an `tests/test_viz_subserver_live.py:82,103,136,167` ist in keiner Config registriert (weder `pytest.ini`/`pyproject` noch `tests/conftest.py:62` — dort wird nur der Basetemp-Guard registriert). Ohne externes Plugin droht `PytestUnknownMarkWarning`; der Marker steuert hier Sockets in Live-Tests, also ein potentiell stiller Verlust von Filter-/Skip-Semantik.
3. **Browser-/A11y-Tests sind opt-in.** Die 11 Browser-Dateien (48 Tests, u. a. `tests/browser/test_admin_ui_keyboard.py`) sind über `importorskip('playwright')` bzw. `has_playwright` (`tests/browser/conftest.py:20-22,77-78`) vollständig abhängig von einer nicht in `tests/requirements.txt` enthaltenen Dependency. In Standard-CI-Läufen werden sie übersprungen → Accessability-/Admin-UI-Abdeckung ist nicht Teil der regulären Suite. (Berührungspunkt zum P32-Geschwisteraudit „Admin-UI Sec+A11y".)
4. **Konditionale Skips können Abdeckung verschleiern.** Beispiele: `tests/test_agent_budget_ratchet.py:191,204` („agent_report.py missing — cannot measure current artifacts"), `tests/test_reference_standards_documented.py:66` („unsynced checkout"), `tests/test_opencode_agents.py:282` („Opencode provider not generated"), `tests/test_legacy_registries_removed.py:68` („generated roots absent"), `tests/test_p10_orchestration_checks.py:70,98` („jsonschema not installed"). Diese Skips hängen vom Checkout-/Sync-Zustand ab; in einem unsynchronisierten Checkout kann die Suite grün sein, ohne die respective Eigenschaft geprüft zu haben.
5. **Keine Unit-/Integrations-Trennung im Layout.** 498 Testmodule flach in `tests/` (nur `browser/` ist ausgelagert). DieRD-Doku (`tests/README.md`) kompensiert mit Shard-/Worker-Regeln, aber es gibt keine explodeite, statisch prüfbare Pyramidengrenze (unit vs. integration vs. e2e).
6. **Basetemp-Guard warn-only.** `tests/conftest.py:62-79` verhindert In-Repo-Basetemp nicht, sondern warnt nur. Bei einem (durch G1 sowieso gesperrten) Volllauf mit `--basetemp` im Repo besteht das dokumentierte Rekursionsrisiko. Nach Stufe A ist hier auf korrekten externen Basetemp zu achten (siehe Runner-Pflicht `--basetemp` außerhalb des Repos).

## 5. Empfehlungen (priorisiert, ohne Spekulation)

**P1 — vor jedem weiteren Testlauf / vor G1-Freigabe**
1. `platform-configs/hacs.defaults.yaml:79` entweder auf `pytest tests/` ohne `--cov` korrigieren oder `pytest-cov` als (temporäre) Test-Dependency in `tests/requirements.txt` ergänzen. Ohne diese Klärung ist der Plattform-Default nicht ausführbar.
2. G1 weiterhin gesperrt lassen. Freigabe ausschließlich nach Stufe A + explizitem „Ja" des Nutzers (Roadmap `:63,:154,:274`, Nutzer-Gate 2026-11-20). Dieses Audit ist kein Freigabe-Signal.

**P2 — mit Stufe A / im selben PR**
3. `@pytest.mark.enable_socket` zentral registrieren (z. B. `markers` in einer neuen, minimalen `pytest.ini`/`pyproject`-Sektion oder `pytest_configure` in `tests/conftest.py:62`) — verhindert stille Marker-Warnungen.
4. Für den späteren, nutzerseitig freigegebenen Volllauf: `pytest-cov` nur temporär installieren, Bericht als PR-Artefakt ablegen (entspricht E-06 „pytest-cov temporär, Berichte per PR") und danach wieder entfernen — keine dauerhafte Coverage-Config einführen, solange kein Konsens darüber besteht.

**P3 — Follow-up, nicht Teil dieses Audits**
5. Browser-/A11y-Tests (`tests/browser/`) als eigenen, expliziten CI-Job mit `playwright` in der Install-Liste führen, damit die 48 Tests nicht still übersprungen werden. Abstimmung mit dem P32-Geschwisteraudit „Admin-UI Sec+A11y".
6. Die fünf in §4.4 genannten zustandsabhängigen Skips dahingehend prüfen, ob sie im CI-Pfad (gesyncter Checkout, `jsonschema` installiert) tatsächlich ausgeführt werden — ggf. als Harte Assertion statt Skip umbauen.
7. `.test_durations` als CI-Artefakt gemäß `tests/README.md:81-83` (`workflow_dispatch` + `--store-durations`) einmalig erzeugen, damit `least_duration` greift; kein Commit der Datei ohne Abstimmung (bisher bewusst nicht eingecheckt).

## 6. Bestätigung

- **Kein Testlauf:** Weder Vollsuite noch Teil-Suite noch `sync.py --validate` wurden ausgeführt. Gate G1 (2026-11-20) respektiert.
- **Keine Code-/Config-/Workflow-/Issue-Änderung:** Es wurde ausschließlich die vorliegende Datei geschrieben:
  `docs/analysis/2026-11-20-audit-top5-test-suite.md`.
- **Kein Commit / Push / PR / Issue-Change / Worktree / Isolation-Flag.**
- Alle Zahlen stammen aus statischer Zählung; alle Bewertungen aus Repo-Dateien mit angegebenen `file:line`-Belegen.

## STATUS/RESULT/ARTIFACTS

STATUS: done
RESULT: Statisches Read-only-Audit der Test-Suite erstellt (509 Testmodule, ~6.376 Testfunktionen). Zentrale Befunde: keine Coverage-Config und kein pytest-cov bei gleichzeitigem `--cov`-Plattform-Default (`platform-configs/hacs.defaults.yaml:79`), nicht registrierter Marker `enable_socket`, opt-in Browser-/A11y-Tests, zustandsabhängige Skips. G1-Volltestlauf gemäß Nutzer-Gate 2026-11-20 nicht ausgeführt.
ARTIFACTS: `docs/analysis/2026-11-20-audit-top5-test-suite.md` (einzige geänderte Datei).
