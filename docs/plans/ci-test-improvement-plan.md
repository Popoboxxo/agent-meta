# CI- und Test-Verbesserungsplan

**Status:** APPROVED
**Freigabe:** Nutzer, 2026-10-29 ('Setze den Plan in die Tat um'); Revision 2 inkl.
**Datum:** 2026-10-29
**Basis:** Read-only-Analyse auf Branch `docs/bugfix-wave-3-spec-plan` (HEAD `e5d5d75a`)
**Scope:** `.github/workflows/*`, `tests/`, `.claude/hooks/`, Repo-Settings (read-only via `gh`)

---

## 1. Gesamturteil

CI und Testsuite sind für ein Python-CLI-Repo mit ~6.575 Tests und 362 Modulen **solide, aber nicht Best Practice**.

Stärken:
- Generierte Ausgabe wird per Drift-Gate gegen Commit geprüft (`validate.yml` Z.63-77).
- Matrix 3.9/3.12 plus 3.11-Boundary-Job, mit expliziter Partitions-Validierung (`orchestration-test.yml` Z.161-238).
- `-n 2 --dist loadfile` mit dokumentierter Begründung gegen `-n auto` (`tests/README.md`).
- Concurrency-Gruppen mit `cancel-in-progress` nur für PRs.
- Timeouts zentral und env-konfigurierbar (`tests/timeouts.py`).

Kritische Lücken:
- **CI ist kein Merge-Gate.** Die Ruleset `Main-Protect` kennt nur `deletion` und `non_fast_forward` — und zielt wegen `include: []` auf gar keinen Branch (Rev. 2).
- **Kein Security-Scan in der Pipeline.** Weder SAST, Dependency-Audit noch Secret-Scan laufen in CI.
- **Least-Privilege nur auf Repo-Ebene.** Repo-Default-Token ist `read`, aber kein `permissions:`-Block im Code; Actions nur über Tags gepinnt.
- **Keine Lint-, Format- oder Typecheck-Stufe.**
- **Browser-/E2E-Tests (Admin-UI) laufen nie.** Sie werden per `importorskip` still übersprungen.

---

## 2. Ist-Zustand (mit Belegen)

### 2.1 Workflows

| Datei | Jobs / Trigger | Belege |
|---|---|---|
| `.github/workflows/validate.yml` | Jobs `scenarios` (4 Shards, Py 3.11, 30 min) und `validate` (10 min). Trigger: push/PR auf main, Cron `0 3 * * *`. | Z.1-9, Z.17-42 (scenarios), Z.44-96 (validate) |
| `.github/workflows/orchestration-test.yml` | Job `test` (Matrix 3.9/3.12 × 3 Shards), `subprocess-shard` (3.9/3.12 × 3), `compat-311`. Path-Filter auf `scripts/ tests/ config/ agents/ VERSION CHANGELOG.md`. | Z.106-125 (Filter), Z.133-140, Z.280-291, Z.340-369 |
| `.github/workflows/test.yml` ("Unit Tests") | **Nicht im Repo.** GitHub-API listet den Workflow (id 275536195) trotzdem als `active`. Datei existiert in HEAD und `origin/main` nicht. Historie (Rev. 2 korrigiert): auf main angelegt in `bc33d826` (2026-05-12), geändert in `2b4effc8`, entfernt über Merge `f44487e1` (2026-05-20). Letzter Run 2026-05-21 auf `feat/se-agent-concept` (90 Runs gesamt) — Altbranches, die die Datei noch enthalten, können ihn weiter auslösen. | `gh api …/actions/workflows`, `…/actions/workflows/test.yml/runs`; `git log origin/main --full-history -m --diff-filter=D` |

Weitere Befunde:
- Kein `permissions:`-Block in irgendeinem Workflow (geprüft: `grep permissions:` leer).
- Actions nur über Tags: `actions/checkout@v4`, `actions/setup-python@v5` (validate.yml Z.29-50, orchestration-test.yml Z.143-349).
- Repo-Settings: `actions.sha_pinning_required: false`, `allowed_actions: all`. `default_workflow_permissions: read` ist **bereits gesetzt**, `can_approve_pull_request_reviews: false` (Rev. 2, `gh api …/actions/permissions/workflow`).
- Kein `pull_request_target`, kein `workflow_run`, keine `secrets.*`-Nutzung in den Workflows (grep, Rev. 2). `actions/checkout` läuft ohne `persist-credentials: false`.
- Trigger-Asymmetrie (Rev. 2): `validate.yml` hat **keinen** Path-Filter, `orchestration-test.yml` filtert auf Trigger-Ebene (`on.push.paths`/`on.pull_request.paths`, Z.106-125). Relevant für Required Checks (siehe G23).
- Python-Setup nutzt `cache: pip` mit `requirements.txt` bzw. `tests/requirements.txt` (validate.yml Z.30-34, orchestration-test.yml Z.148-151). Caching ist vorhanden.
- Timeouts: 10/30 min pro Job (validate.yml Z.20, Z.47; orchestration-test.yml Z.135, Z.286, Z.342).
- Lauf-Historie (letzte 12 Runs via `gh api actions/runs`): alle `success`. Wall-Clock Orchestration-Tests: ca. 23-27 min (push 14:40→15:03, PR 13:18→13:45). Validate: ca. 15-16 min (push/PR), 71 min (Cron 09:25→10:36).

### 2.2 Repo-Settings (read-only via `gh`)

| Bereich | Befund |
|---|---|
| Branch-Protection (classic) | `404 Branch not protected` |
| Rulesets | `Main-Protect` (id 17124218), `enforcement: active`, Regeln: `deletion`, `non_fast_forward`. **Kein** `pull_request`, **kein** `required_status_checks`. **Rev. 2:** `conditions.ref_name.include: []` — die Ruleset zielt auf **keinen** Branch und schützt `main` damit faktisch gar nicht (auch nicht vor Force-Push/Löschung). Bypass: `RepositoryRole` id 5 (Admin), `bypass_mode: always`. |
| Workflow-Token | `default_workflow_permissions: read` (bereits Least-Privilege auf Repo-Ebene) |
| Code Scanning | CodeQL Default Setup `state: not-configured`; erkannte Sprachen u.a. `python`, `actions` |
| Dependabot Security Updates | `disabled` |
| Vulnerability-Alerts | `404` (nicht aktiv) |
| Secret Scanning | `enabled`; Push Protection `enabled`; Validity Checks und Non-Provider-Patterns `disabled` |
| Repo-Sichtbarkeit | `PUBLIC` (CodeQL und Dependabot ohne Kostenthema verfügbar) |
| Merge-Methoden | Merge und Squash erlaubt; `deleteBranchOnMerge: false` |

### 2.3 Repo-Dateien (Governance)

- `.github/dependabot.yml`: fehlt.
- `.github/CODEOWNERS`: fehlt.
- `.github/PULL_REQUEST_TEMPLATE.md`: fehlt. Dieses Verzeichnis enthält nur `workflows/`.
- `.pre-commit-config.yaml`: fehlt. Unter `.git/hooks/` nur `*.sample`.
- `pyproject.toml`, `pytest.ini`, `setup.cfg`, `tox.ini`: fehlen. Pytest-Konfiguration existiert nicht.
- Lint-/Typ-Konfiguration (ruff, flake8, mypy): fehlt. `.ruff_cache/` ist vorhanden, also lokaler Ad-hoc-Lauf ohne Config.
- `requirements.txt`: nur `PyYAML>=6.0` (Z.1).
- `tests/requirements.txt`: pytest, pyyaml, questionary, tomli (<3.11), jsonschema, pytest-xdist, pytest-split (Z.4-10). **Kein** pytest-cov, **kein** Playwright, **kein** pytest-asyncio.

### 2.4 Testsuite

- Umfang: `tests/` enthält 377 `test_*.py`-Dateien. Laut CI-Header (`orchestration-test.yml` Z.6-10): 6.575 Tests in 362 Modulen.
- Runner: pytest (kein `pytest.ini`/`pyproject.toml`, Defaults). 218 Dateien referenzieren pytest explizit, 149 nicht (überwiegend Plain-Asserts, 12 Dateien mit `unittest`).
- Verzeichnisse:
  - `tests/browser/` (Rev. 2 korrigiert: 41 Dateien inkl. `__pycache__`, davon **11 Testmodule** + `conftest.py` + `__init__.py`). Jedes Testmodul `pytest.importorskip('playwright')` (z.B. `test_admin_ui_consistency_p1.py` Z.13), zusätzlich `conftest.py` Z.78 `pytest.skip(...)`. Playwright ist in keiner CI-Datei installiert. Die Module **werden in CI gesammelt** (Remainder-Step `pytest tests/`) und übersprungen; dank `-ra` erscheinen die Skips im Summary, sie brechen aber nichts — „still“ heißt also „nicht fehlschlagend“, nicht „unsichtbar“.
  - `tests/scenarios/` (Rev. 2 korrigiert: 178 Dateien gesamt, davon 88 in `configs/`): `run.sh`, `registry.md`, `configs/`, `asserts/`. Läuft im Job `scenarios` (validate.yml Z.17-42, laut Kommentar 79 Szenarien ≈ 46 min seriell, 4 Shards). Abweichung 88 Configs vs. 79 Szenarien ist nicht geklärt.
  - `tests/orchestration/`, `tests/routing-llm-eval/`, `tests/manual/`, `tests/automated/`: keine CI-Stufe für `manual/` und `routing-llm-eval/` erkennbar.
- Conftest: `tests/conftest.py` Z.60-74 warnt nur bei In-Repo-basetemp (`warn, never fail`).
- Subprocess-Hygiene: `tests/timeouts.py` mit Defaults 180 s (sync) und 60 s (scripts). Begründung im Docstring: CI-Run 40210737659 (Py 3.9) hatte `TimeoutExpired`.
- Test-Isolation: `_clean_env()` nur in `tests/test_orchestrator_guard_hook.py` Z.84. Andere Module verlassen sich auf Repo-Kopie-Fixtures.
- Golden/Snapshot: `tests/fixtures/{ac01-baseline, compact-golden, slimming-golden, active-set, ...}`, `tests/test_substitution_engines_golden.py`, `tests/test_ac01_render_identity.py`. Update-Prozess für Goldens ist nicht dokumentiert.
- Partitionierung: Die Listen der 15 Subprocess- und 17 Heavy-Fixture-Dateien sind **manuell gepflegt** (`orchestration-test.yml` Z.66-104). Ein Validator (Z.167-238) wacht über Duplikate und Anzahl. Es gibt kein committed `.test_durations`. Der Header nennt das selbst als Follow-up (Z.34-38).

### 2.5 Sync-Checks und Drift

- `python scripts/sync.py` (Generierung) → `git status --porcelain` ohne `.meta-config/` (validate.yml Z.61-77).
- `python scripts/sync.py --validate` läuft **dreimal** pro Lauf: validate-Job (3.11), `test`-Job Shard 1 (3.9 und 3.12) (orchestration-test.yml Z.267-269). Gemessen 12-55 s je Aufruf (Workflow-Kommentar Z.261: 12-38 s). Der Kommentar (Z.258-265) erklärt die Doppelung als **bewusste Entscheidung**: nur dort sieht `--validate` die Versionen 3.9/3.12.
- Frontmatter-Lint: Inline-Python-Snippet mit PyYAML (validate.yml Z.80-96), nur Syntax, kein Schema.
- Drift-Gate-Ausnahme: `.meta-config/` ausgeschlossen, weil Lockfiles auf main bereits driften (validate.yml Z.65-69). Das ist eine bekannte Schuld, kein Vorsatz.

### 2.6 Lokale Hooks (`.claude/hooks/`)

- `dod-push-check.sh` (Z.8: `enabled_by_default: false`). Fail-closed bei fehlendem `python3` (Z.51-56). Convention boundary für die Classify-Logik, security boundary für Dependency-Verfügbarkeit.
- `orchestrator-guard.sh`, `repo-containment.sh`, `graphify-*-guard.sh`, `lifecycle-check.sh`, `sync-on-config-change.sh`, `viz-log.sh`, `auto-github-release.sh`.
- `release-gates/`: `action-pin-validation.sh`, `artifact-freshness.sh`, `docker-image-scan.sh`. Ausgeführt über `pre-release-check.sh` (manuell, `event: Manual`).
- **Wichtig (Rev. 2 korrigiert):** `action-pin-validation.sh` prüft laut Header (Z.5) sehr wohl `.github/workflows/*.yml` — aber nur, ob jede referenzierte Ref (Tag **oder** SHA) upstream existiert. Es erzwingt **kein** SHA-Pinning, ist `enabled_by_default: false` und läuft nur manuell vor Releases. Ein Tag-Pin wie `@v4` besteht das Gate.

### 2.7 Python-Matrix und Kompatibilität

- CI-Matrix: 3.9 (Floor), 3.11 (Boundary), 3.12 (Ceiling).
- Lokal existiert nur `/usr/bin/python3` = 3.13.5. Kein 3.9 zur Reproduktion lokal.
- `scripts/lib/consistency/python_compat.py` prüft zwei Hazards per Scan: PEP-604-Union-Syntax ohne `from __future__` und Backslash in f-String-Expressions (`tests/test_python_compat_consistency.py`). Das ist eine gezielte, gut begründete Maßnahme.
- Nicht abgedeckt: API-Verfügbarkeit unter 3.9 (z.B. `zip(strict=)`, `str | None` in Laufzeit-Introspektion, `dataclass(slots=)`). `ast.parse(..., feature_version=(3, 9))` würde Syntax-Regressionen repo-weit fangen (Machbarkeit nicht separat getestet). **Rev. 2:** Laut Python-Doku ist `feature_version` nur „best-effort“ — es garantiert nicht, dass jede neuere Syntax abgelehnt wird. API-Nutzung (`zip(strict=)`) fängt weder `ast` noch ruff; das deckt nur der echte 3.9-Matrixlauf.
- Python 3.9 ist seit Oktober 2025 End-of-Life. Der Floor ist eine bewusste Kompatibilitätszusage des Projekts und muss als Entscheidung dokumentiert werden.

### 2.8 Stdlib-only-Constraint

- `CLAUDE.md` (Code-Konventionen): „Keine externen Python-Dependencies außer Stdlib“.
- Realität: `requirements.txt` enthält `PyYAML`. 33 Dateien in `scripts/` importieren `yaml`. `sync.py` ist davon abhängig.
- Dev-/Test-Tools in `tests/requirements.txt` (pytest, questionary, jsonschema, pytest-split) sind für CI akzeptabel, aber nicht begründet dokumentiert.
- **Konflikt zwischen Dokumentation und Code.** Entweder Doku korrigieren (PyYAML als dokumentierte Ausnahme) oder Abhängigkeit entfernen.

### 2.9 Lokale Messung (Zeitmessung)

- Befehl: `python3 -m pytest tests/ -q -n 2 --dist loadfile --ignore=tests/browser --durations=15 -p no:cacheprovider`
- Ergebnis: Timeout (560 s) bei ca. 23 % Fortschritt. Projektion vollständiger Lauf: ca. 40 min Wall-Clock auf 4 Kernen mit `-n 2`.
- Keine `F`/`E`-Tests in der beobachteten Fortschrittsausgabe. Die Buchstaben im Log stammen aus Warnungen (pytest-asyncio-Deprecation).
- **Hermetik-Lücke:** Lokal wurde das pytest-asyncio-Plugin aus `~/.local` geladen, obwohl es nicht in `tests/requirements.txt` steht. Lokaler Lauf ist also nicht CI-äquivalent.
- Zeitmessung ohne `--durations`-Auswertung über den vollständigen Lauf: nicht abgeschlossen. Ergebnis deshalb als Projektion markiert.

### 2.10 Security-Scans im Pipeline-Kontext

| Scan | Status |
|---|---|
| Secret-Scan (CI) | nicht vorhanden. Lokal: `scripts/lib/cli_commands.py` Z.475 (`handle_scan_staged`), getestet in `tests/test_scan_staged.py`, **nicht in CI-Pipeline eingebunden**. |
| Secret-Scan (GitHub) | Secret Scanning und Push Protection aktiv. |
| Dependency-Audit | nicht vorhanden (kein pip-audit, kein Dependabot). |
| SAST | nicht vorhanden (kein CodeQL). |
| Container-Scan | nicht relevant (kein Image). |
| SBOM / Signatur | nicht vorhanden. |

### 2.11 Test-Pyramide

| Ebene | Umfang | Anmerkung |
|---|---|---|
| Unit (in-process) | Ein Großteil der 6.575 Tests | Schnell, aber nicht getrennt markiert. |
| Subprocess / sync.py-Integration | 15 Module, 451 Tests, seriell (`-n 0`) | Teuerster Teil. Das kritische Pfad-Problem der CI. |
| Heavy-Fixture (Repo-Kopien) | 17 Module | Setup-dominiert. |
| Szenario-Harness | 79 Szenarien, 4 Shards | Regressionstest über Consumer-Konfigs. |
| Browser / E2E (Admin-UI) | 11 Testmodule | **Nie in CI ausgeführt** (importorskip, Skip im `-ra`-Summary sichtbar). |
| Routing-LLM-Eval | `tests/routing-llm-eval/` | Kein CI-Job erkennbar. |

Es gibt keine Marker (`@pytest.mark.slow`, `integration`, `unit`), daher lässt sich kein schneller Smoke-Subset für PRs bilden.

### 2.12 DoD-Preset `rapid-prototyping`

- `scripts/lib/config.py` Z.146: `dod-preset: rapid-prototyping`. `setup.py` Z.295: „All checks disabled for fast iteration“.
- `CLAUDE.md` (Agenten-Konfiguration): `Tests: false`, `Security-Audit: false`.
- Realität: Dieses Repo fährt 6.575 Tests und sync-Validierung in CI. Der DoD-Preset widerspricht der tatsächlichen Gate-Praxis. Die CI ist faktisch die einzige echte Qualitätsbarriere.

---

## 3. Gap-Analyse

Priorität: **P0** (sofort, Risiko hoch), **P1** (nächste Welle), **P2** (mittelfristig), **P3** (Hygiene).
Aufwand: **S** (< 0,5 Tag), **M** (0,5-2 Tage), **L** (> 2 Tage).

| # | Lücke | Best Practice | Beleg | Prio | Aufwand |
|---|---|---|---|---|---|
| G1 | CI nicht merge-blockierend: Ruleset ohne `required_status_checks` und ohne PR-Pflicht; **Ruleset zielt auf keinen Branch** (`include: []`), Admin-Bypass `always` | Ruleset auf `~DEFAULT_BRANCH`, Required Checks + PR-Pflicht auf main | Ruleset `Main-Protect` (gh API) | **P0** | S |
| G2 | Kein Security-Scan in der Pipeline (SAST, Dependency-Audit, Secret-Scan) | Security-Stufe vor Merge, MTTG < 10/30 min | Keine Datei in `.github/workflows/`; `handle_scan_staged` ungenutzt in CI | **P0** | M |
| G3 | Browser/E2E (11 Testmodule) laufen nie, Skip bricht nichts | Explizite E2E-Stufe oder explizit deaktiviert, kein stilles Skip | `tests/browser/*.py` `importorskip`; keine Playwright-Installation in CI | **P1** | M |
| G4 | Keine expliziten `permissions:` (Repo-Default ist bereits `read`, aber nicht im Code verankert), Actions nur über Tags, `persist-credentials` nicht deaktiviert | Workflow-Level `permissions: contents: read` (Job-Level nur wo nötig), Actions per Full-SHA gepinnt, danach `sha_pinning_required: true` | grep leer; `uses: actions/...@v4`; `…/actions/permissions` | **P1** | S |
| G5 | Kein Dependabot (pip + github-actions), Security Updates deaktiviert | Dependabot-Updates für Python und Actions | `.github/dependabot.yml` fehlt; `dependabot_security_updates: disabled` | **P1** | S |
| G6 | Keine Lint-, Format-, Typecheck-Stufe | Lint + Format in Pre-commit und CI (Fast-Feedback < 5 min) | keine ruff/flake8/mypy-Config; `.ruff_cache` nur lokal | **P1** | M |
| G7 | Py-3.9-Parität nicht lokal reproduzierbar; API-Kompatibilität nicht gescannt | `ast.parse(feature_version=(3,9))` repo-weit + Entscheidung zum Floor | `python_compat.py` deckt nur 2 Hazards; lokal nur 3.13 | **P1** | S |
| G8 | Stale Workflow-Registrierung `Unit Tests` (test.yml), auf Altbranches weiter auslösbar | Nur registrierte, existierende Workflows | `gh api actions/workflows`; Datei fehlt in HEAD | **P1** | S |
| G9 | Kein Aggregat-Check (`ci-gate`) für Required Checks; Matrix-Jobnamen fragil | Ein stabiler Gate-Job **pro Workflow** (`needs:` wirkt nicht workflow-übergreifend) | `orchestration-test.yml` Matrix-Jobnamen | **P1** | S |
| G10 | Kein Fast-Feedback-Subset: 6.575 Tests, keine Marker | PR-Smoke < 5 min, Full-Suite nightly/main | `pytest tests/` ohne Marker; Wall-Clock 23-27 min | **P1** | M |
| G11 | Path-Filter von `orchestration-test.yml` lässt sync.py-Eingaben aus: `hooks/`, `rules/`, `schemas/`, `templates/`, `snippets/`, `commands/`, `platform-configs/`, `speech/`, `standalone/`, `.claude/`, `requirements.txt` | Filter spiegelt Abhängigkeiten (oder Filter entfällt, siehe G23) | Z.106-125; Referenzen per grep in `scripts/lib` | **P2** | S |
| G23 | **Path-Filter × Required Check (Rev. 2):** Ein Trigger-Level-`paths:`-Filter erzeugt bei Nicht-Treffer **gar keinen** Check-Run. Ein darauf gesetzter Required Check bleibt auf „Expected — Waiting for status“ hängen und blockiert z.B. reine Doku-PRs. Ein per `if:` übersprungener **Job** zählt dagegen als bestanden. | Workflow immer triggern, Änderungserkennung im Job (`git diff --name-only` gegen `github.event.pull_request.base.sha`, stdlib/Shell), Jobs per `if:` skippen; Gate-Job mit `if: always()` | `orchestration-test.yml` Z.106-125 | **P0** (Voraussetzung für G1) | S |
| G24 | Keine Reproduzierbarkeit: `requirements.txt`/`tests/requirements.txt` nur mit `>=`-Ranges, kein Lock/Constraints; Tool-Versionen (pytest, xdist, split) driften zwischen Runs | `tests/constraints.txt` (gepinnt, optional `--require-hashes`), `pip install -r … -c …`; Dependabot pflegt Pins | `tests/requirements.txt` Z.4-10 | **P2** | S |
| G25 | Kein Workflow-Lint und keine Supply-Chain-Bewertung | `actionlint` + `zizmor` (Workflow-Security-Lint) in CI; OpenSSF Scorecard (wöchentlich) | keine Datei in `.github/workflows/` | **P2** | S |
| G12 | Partitionierung manuell gepflegt (15/17 Dateilisten); kein `.test_durations` | `pytest-split` mit committed Durations oder `least_duration` | `orchestration-test.yml` Z.66-104, Z.34-38 | **P2** | M |
| G13 | Keine Coverage-Messung, kein Gate | Coverage-Report als Artefakt, Ratchet-Gate | `tests/requirements.txt` ohne pytest-cov; alter `--cov-fail-under 20` in `2b4effc8` entfernt | **P2** | M |
| G14 | Keine JUnit-/Durations-Artefakte, keine Flake-Erkennung | JUnit XML als Artefakt, Flake-Report | nur `--durations=10` in Logs | **P2** | S |
| G15 | Stdlib-only-Konflikt: PyYAML in Runtime, dokumentiert als Stdlib-only | Doku und Code konsistent | `requirements.txt`; 33 Dateien mit `import yaml`; `CLAUDE.md` | **P2** | M (Entscheidung) |
| G16 | Lokale Hermetik: `~/.local`-Plugins leaken in Testlauf | `PYTHONNOUSERSITE=1` / Venv, lokal = CI | pytest-asyncio-Warnung im Lauf | **P2** | S |
| G17 | Lokal-Befehl abweichend (`-n 8` in `tests/README.md` vs. CI `-n 2`) und kein `make ci` / Skript | Eine Quelle für Lokal = CI | `tests/README.md` Z.12 vs. `orchestration-test.yml` Z.256 | **P2** | S |
| G18 | `sync.py --validate` dreifach ausgeführt, teuer | Einmal pro Stufe mit klarer Verantwortung | validate.yml Z.79; orchestration-test.yml Z.267 | **P3** | S |
| G19 | Golden-Update-Prozess undokumentiert | Dokumentierter `--update-golden`-Pfad | `tests/fixtures/*-golden` | **P3** | S |
| G20 | DoD-Preset `rapid-prototyping` widerspricht realer Gate-Praxis | Doku spiegelt tatsächliche Gates | `CLAUDE.md` Tests: false | **P3** | S |
| G21 | `.meta-config/` aus Drift-Gate ausgenommen (bekannte Schuld) | Drift-Gate vollständig | validate.yml Z.65-72 | **P2** | M |
| G22 | Keine Mutation-/Property-Tests | Property-Tests nur für Parser (z.B. `hypothesis`) | Parser in `scripts/lib/` | **P3** | L (optional) |

**Stärken, die erhalten bleiben:**
- Drift-Gate, `--validate`, Golden-Fixtures, Concurrency-Gruppen, `timeouts.py`, `-n 2 --dist loadfile`, `python_compat`-Scan.

---

## 4. Maßnahmenplan in Wellen / PRs

Repo-Settings-Änderungen (G1, G5-Settings, G8) sind **Admin-Aktionen** und werden nicht vom Agenten ausgeführt. Der Plan nennt sie als Vorschlag für den Maintainer.

### Welle 1 — Gates und Sicherheit (P0/P1, überwiegend S)

| PR | Inhalt | Lücke |
|---|---|---|
| W1-A | Ruleset `Main-Protect` reparieren und erweitern: `conditions.ref_name.include: ["~DEFAULT_BRANCH"]` (sonst wirkt keine Regel), `pull_request` (0 Reviews bei Solo-Maintainer reicht, PR-Pflicht ist der Gewinn), `required_status_checks` auf die Gate-Jobs aus W1-F, mit `integration_id` der GitHub-Actions-App (15368), damit kein anderer Status-Absender den Check fälschen kann. Bypass von `always` auf `pull_request` umstellen (Admin darf Regeln nur im PR-Merge umgehen, kein Direkt-Push). `strict_required_status_checks_policy` (Branch up-to-date) bewusst entscheiden: sicherer, aber mehr Re-Runs bei 25-min-Suite. Admin-Aktion. **Erst nach W1-F/G23 aktivieren.** | G1, G9 |
| W1-B | `permissions: contents: read` auf Workflow-Ebene in beiden Workflows, Job-Level-Erweiterung nur wo nötig (CodeQL: `security-events: write`; Scorecard: `security-events: write`, `id-token: write`). `persist-credentials: false` an jedem `actions/checkout`. Repo-Default `read` ist **bereits gesetzt** (keine Admin-Aktion nötig). | G4 |
| W1-C | `.github/dependabot.yml`: `pip` (`directories: ["/", "/tests"]`) und `github-actions` (`directory: "/"`), wöchentlich, `groups` gegen PR-Flut, `cooldown.default-days` (z.B. 7) gegen frisch kompromittierte Releases. Actions per Full-SHA pinnen mit Tag-Kommentar (`@<sha> # v4.x.y`) — Dependabot aktualisiert SHA und Kommentar. Danach Repo-Setting `sha_pinning_required: true` (Admin). Admin: Dependabot-Alerts aktivieren (Voraussetzung für Security Updates, aktuell 404). | G4, G5 |
| W1-D | Security-Stufe: (1) **CodeQL Default Setup** (Admin-Klick, kein Workflow-File, Sprachen `python` + `actions`) statt eigenem Workflow. (2) Job `security` in `validate.yml`: `pip-audit -r requirements.txt -r tests/requirements.txt` (Dev-Tool nur in CI). (3) Secret-Scan in CI ist durch aktive Push Protection teilweise redundant — `scan-staged` repo-weit genügt als Zusatz; gitleaks nur bei Bedarf. | G2 |
| W1-E | Py-3.9-Syntax-Gate: bevorzugt über ruff (`target-version = "py39"`, ruff meldet versionsfremde Syntax seit 0.9) aus W2-A; sonst Stdlib-Job `ast.parse(feature_version=(3,9))` über `scripts/`, `tests/`. Beides ist best-effort; die 3.9-Matrix bleibt die maßgebliche Prüfung. | G7 |
| W1-F | Gate-Job **je Workflow** (`validate-gate`, `orchestration-gate`), da `needs:` nicht workflow-übergreifend wirkt. Muster: `needs: [alle Jobs]`, `if: always()`, Fail wenn `contains(needs.*.result, 'failure') \|\| contains(needs.*.result, 'cancelled')`; `skipped` gilt als ok. **Ohne `if: always()` wird das Gate bei fehlgeschlagenem Need selbst `skipped` — und ein übersprungener Required Check zählt als bestanden.** Gleichzeitig Trigger-Level-`paths:` in `orchestration-test.yml` entfernen und durch In-Job-Änderungserkennung ersetzen (G23). Push-/Cron-Läufe bleiben vollständig. | G9, G23 |
| W1-G | Admin: Workflow `Unit Tests` (test.yml) per `gh workflow disable 275536195` deaktivieren; Altbranches mit `test.yml` (u.a. `feat/se-agent-concept`) prüfen/aufräumen. | G8 |
| W1-H | Workflow-Lint: `actionlint` und `zizmor` (pip-installierbar, findet u.a. fehlende `permissions`, `persist-credentials`, Template-Injection, ungepinnte Actions) als Job; OpenSSF Scorecard als separater, wöchentlicher Workflow (`ossf/scorecard-action`, `publish_results: true` nutzt OIDC `id-token: write` — einzige OIDC-Nutzung, da kein Cloud-Deploy/PyPI-Publish existiert). | G25 |

**Akzeptanzkriterien W1:**
- `gh api …/rulesets/17124218` zeigt `include: ["~DEFAULT_BRANCH"]`; direkter Push auf `main` wird abgelehnt (auch für Admin, Bypass nur via PR).
- PR mit fehlgeschlagenem Gate-Job kann nicht gemergt werden.
- Reiner Doku-PR (nur `docs/**`) wird **nicht** durch einen wartenden Required Check blockiert (Gate grün, Testjobs `skipped`).
- Gate-Job ist rot, wenn ein Need `failure` oder `cancelled` ist (Test mit absichtlich rotem Job).
- `permissions` ist in allen Workflows explizit gesetzt; `actionlint` und `zizmor` sind grün.
- Dependabot öffnet mindestens einen Test-PR.
- `security`-Job schlägt bei einem absichtlich eingefügten Testgeheimnis (Dummy) fehl und wird nach Entfernen grün.

### Welle 2 — Qualität und Fast-Feedback (P1/P2, M)

| PR | Inhalt | Lücke |
|---|---|---|
| W2-A | Lint/Format: `ruff` mit exakt gepinnter Version (Regeln ändern sich zwischen Minor-Releases), `target-version = "py39"`, minimaler Regelsatz (E, F, W, I). ruff hat **keine** native Baseline-Datei: Altbestand per `ruff check --add-noqa` oder `per-file-ignores` einfrieren, neue Verstöße blockieren. Config in `ruff.toml` (kein `pyproject.toml` nötig). Dev-Tool, nicht in `requirements.txt`. Begründung in `docs/` (Stdlib-only gilt für Produktcode). | G6, G7 |
| W2-B | Browser-E2E-Job: `pip install playwright` + `playwright install --with-deps chromium`, `pytest tests/browser` mit Browser-Cache. Alternativ explizit Marker `e2e` und dokumentierter Opt-out. Skip-Fail (`> 0 Skips`) **nur im Browser-Job**, nicht global — die Hauptsuite enthält legitime Skips. | G3 |
| W2-C | PR-Smoke-Subset: Marker `unit`/`integration`/`e2e`, registriert in einer neuen `pytest.ini` mit `--strict-markers` (Tippfehler-Schutz). Marker zentral in `tests/conftest.py` per `pytest_collection_modifyitems` nach Verzeichnis/Dateiliste vergeben statt 377 Dateien anzufassen. PR-Pfad < 5 min; Vollsuite auf main und nightly. | G10 |
| W2-D | Path-Logik (nach W1-F im Job, nicht im Trigger) um alle sync.py-Eingaben erweitern: `hooks/`, `rules/`, `schemas/`, `templates/`, `snippets/`, `commands/`, `platform-configs/`, `speech/`, `standalone/`, `.claude/hooks/`, `.meta-config/`, `requirements.txt`. Im Zweifel invertieren: nur bei reinen `docs/**`/`*.md`-Änderungen skippen. | G11 |
| W2-G | Reproduzierbarkeit: `tests/constraints.txt` mit exakten Pins (generiert per `pip freeze` aus einer frischen Venv je Floor-Version oder `pip-compile`), Install als `pip install -r tests/requirements.txt -c tests/constraints.txt`; `cache-dependency-path` auf beide Dateien. Dependabot pflegt die Pins. | G24 |
| W2-E | JUnit-XML (`--junitxml`) und Durations als Artefakt (`actions/upload-artifact`). | G14 |
| W2-F | `PYTHONNOUSERSITE=1` in `tests/README.md` und Skript `scripts/ci-local.sh` (Venv, identische Flags wie CI). | G16, G17 |

**Akzeptanzkriterien W2:**
- `ruff check` ist grün mit Baseline; neuer Verstoß bricht den PR.
- Browser-Job meldet Anzahl ausgeführter Tests; Skip-Zähler = 0 oder begründet.
- PR-Smoke-Stufe < 5 min Wall-Clock.
- Änderung nur in `hooks/1-generic/` löst Orchestration-Test aus.
- Artefakt `junit-*.xml` pro Job verfügbar.

### Welle 3 — Struktur und Metriken (P2/P3, M-L)

| PR | Inhalt | Lücke |
|---|---|---|
| W3-A | Durations-basierte Partitionierung: `workflow_dispatch`-Job mit `--store-durations`, committed `.test_durations`, `--splitting-algorithm least_duration`. Manuelle Listen entfallen. Hinweise: pytest-split misst pro Test, die Heavy-Fixture-Kosten landen beim ersten Test des Moduls — mit `--dist loadfile` bleibt das Modul zusammen, daher Shard-Balance nach Umstellung nachmessen. Neue Tests ohne Eintrag bekommen den Mittelwert; Durations je Python-Version (3.9 ist ~2x langsamer) getrennt erwägen. | G12 |
| W3-B | Coverage: `pytest-cov` mit Report-Artefakt, Ratchet-Gate (Schwelle als Datei im Repo, Start = aktueller Wert minus Puffer, nur nach oben anpassen). Shards liefern `.coverage.*`-Artefakte, `coverage combine` im Gate-Job. **Subprocess-Abdeckung:** `sync.py`-Kindprozesse werden nur mit `COVERAGE_PROCESS_START` bzw. `[run] patch = subprocess` (coverage ≥ 7.10) erfasst — sonst fehlt genau der teuerste Testteil im Wert. | G13 |
| W3-C | Stdlib-Entscheidung: entweder `PyYAML` als dokumentierte Runtime-Ausnahme in `CLAUDE.md` oder Ersatz durch Stdlib-Parser. ADR in `docs/`. | G15 |
| W3-D | `.meta-config/` in Drift-Gate einbeziehen, sobald Lockfiles regeneriert sind. | G21 |
| W3-E | `sync.py --validate`: Doppelung ist laut Workflow-Kommentar bewusst (einzige 3.9/3.12-Abdeckung). Nur konsolidieren, wenn die Versionsabdeckung anders gesichert ist; sonst G18 schließen. | G18 |
| W3-F | Golden-Update-Doku (`docs/`) und DoD-Preset-Text mit tatsächlichen Gates abgleichen. | G19, G20 |
| W3-G | Optional: Property-Tests für Parser (`hypothesis` als Dev-Tool, Begründung dokumentiert). | G22 |

**Akzeptanzkriterien W3:**
- `.test_durations` aktuell (< 14 Tage) und Shard-Laufzeiten innerhalb ±20 %.
- Coverage-Report verfügbar; Gate verhindert Rückgang.
- ADR zur Stdlib-Frage existiert und ist verlinkt.
- Keine manuellen Dateilisten mehr in `orchestration-test.yml`.

---

## 5. Metriken (DORA und MTTG)

| Metrik | Ist | Ziel nach Welle 2 |
|---|---|---|
| MTTG Lint | nicht gemessen (keine Stufe) | < 5 min |
| MTTG SAST/Security-Scan | nicht vorhanden | < 10 min / < 30 min |
| MTTG Review | nicht erzwungen | < 60 min |
| Lead Time (PR-Feedback) | Orchestration ca. 25 min, Validate ca. 15 min | PR-Smoke < 5 min, Vollsuite < 25 min |
| Change-Fail-Rate | nicht gemessen (CI nicht Merge-Gate) | Merge nur bei grünem `ci-gate` |
| Deployment-Frequenz | nicht relevant (CLI-Repo, Release über Hook) | unverändert |

---

## 6. Risiken

- **R1 Ruleset-Änderung blockiert Solo-Maintainer.** Mitigation: Admin-Bypass `pull_request` dokumentieren; 0 Pflicht-Reviews. Der Modus „Evaluate“ ist nur in GitHub Enterprise verfügbar, hier also **nicht** nutzbar — stattdessen Required Checks erst aktivieren, wenn die Gate-Jobs mehrere Läufe stabil grün waren.
- **R10 Path-Filter × Required Check (Rev. 2).** Wird ein Check aus einem Workflow mit Trigger-`paths:` required, hängen PRs ohne passende Änderung dauerhaft auf „Expected“. Mitigation: W1-F vor W1-A; Abnahmetest mit Doku-only-PR.
- **R11 Gate-Job falsch gebaut.** Ohne `if: always()` wird das Gate bei rotem Need übersprungen und zählt als bestanden; Matrix-Jobnamen als Required Checks brechen bei jeder Matrix-Änderung still. Mitigation: nur Gate-Jobs required; Negativtest in W1-Akzeptanz.
- **R12 Python-3.9-Verfügbarkeit auf Runnern.** 3.9 ist EOL; `actions/setup-python` bezieht Versionen aus `actions/python-versions`. Fällt 3.9 für `ubuntu-latest` weg, bricht die Floor-Matrix ohne Codeänderung. Mitigation: Runner-Image pinnen (`ubuntu-24.04`) und Floor-Entscheidung (R6) zeitnah treffen.
- **R13 Fork-PRs und Token-Rechte.** Aktuell kein `pull_request_target` (gut). Neue Workflows (z.B. PR-Kommentare von Coverage-Bots) dürfen `pull_request_target`/`workflow_run` nicht mit Checkout des PR-Heads kombinieren. Mitigation: `zizmor` in W1-H erkennt das.
- **R2 SHA-Pinning erzeugt Wartungslast.** Mitigation: Dependabot für Actions aktivieren, bevor Pins gesetzt werden.
- **R3 CodeQL/Secret-Scan erzeugt Fehlalarme in Fixtures.** Mitigation: Baseline; Fixtures über `.shipsafeignore` / Scanner-Ausnahmen.
- **R4 ruff-Baseline ist groß (ungeprüfter Code).** Mitigation: nur neue Verstöße blockieren; mangels nativer Baseline per `--add-noqa`/`per-file-ignores`.
- **R5 Browser-E2E ist flakig und langsam.** Mitigation: eigener Job, `continue-on-error` nicht verwenden; zuerst als nicht-required Job starten.
- **R6 Python-3.9-Floor-Entscheidung.** 3.9 ist EOL. Wird der Floor angehoben, entfallen ca. 1/3 der Shard-Last. Das ist eine Produktentscheidung, nicht technisch.
- **R7 Durations-Datei veraltet.** Mitigation: `workflow_dispatch`-Job, Ablaufdatum-Check.
- **R8 Lokale Messung unvollständig.** Der Vollauf wurde nicht abgeschlossen; Wall-Clock ist Projektion. Vor Welle 2 einmal vollständig mit `--durations=50` messen (ggf. über Nacht).
- **R9 Repo-Settings sind außerhalb des Repos.** Änderungen an Rulesets und Workflow-Permissions wirken nicht über PR, nur über Admin-Aktion. Dokumentation im PR-Text verlinken.

---

## 7. Offene Entscheidungen für den Maintainer

- Python-3.9-Floor beibehalten oder anheben? (G7, R6)
- PyYAML-Runtime-Abhängigkeit als Ausnahme dokumentieren oder entfernen? (G15)
- Browser-E2E als required Check oder optionaler Job? (G3, R5)
- Security-Scanner: CodeQL plus gitleaks oder nur GitHub-natives Secret Scanning? (G2)
- `strict_required_status_checks_policy` (Branch muss up-to-date sein) ja/nein? (W1-A)
- Merge Queue einsetzen? Falls ja, brauchen alle Workflows mit Required Checks den Trigger `merge_group`. (W1-A)

---

## 8. Quellen (Repo-intern)

- `.github/workflows/validate.yml`, `.github/workflows/orchestration-test.yml`
- `tests/conftest.py`, `tests/timeouts.py`, `tests/README.md`, `tests/requirements.txt`
- `tests/test_python_compat_consistency.py`, `scripts/lib/consistency/python_compat.py`
- `.claude/hooks/dod-push-check.sh`, `.claude/hooks/release-gates/`
- `scripts/lib/config.py` (DoD-Preset), `CLAUDE.md` (Code-Konventionen, Agenten-Konfiguration)
- Repo-Settings: `gh api repos/Popoboxxo/agent-meta/rulesets/17124218`, `…/actions/workflows`, `…/actions/permissions`, `…/branches/main/protection` (404)

---

## 9. Revision 2 – Review-Ergebnisse

**Datum:** 2026-10-29 · **Status bleibt:** DRAFT · Belege per Stichprobe gegen `.github/workflows/*`, `gh api` und Dateisystem nachgeprüft.

Korrekturen (Befund war falsch oder unvollständig):
- Ruleset `Main-Protect`: `conditions.ref_name.include: []` — zielt auf keinen Branch, schützt `main` faktisch nicht; Bypass Admin `always` (2.2, G1, W1-A).
- `default_workflow_permissions` ist bereits `read`; W1-B braucht keine Admin-Aktion (2.1, 2.2, G4).
- `test.yml`-Historie: Datei war auf main (`bc33d826`, `2b4effc8`), entfernt über Merge `f44487e1`; Runs kommen von Altbranches (2.1, G8, W1-G).
- `tests/browser/`: 11 Testmodule statt „41 Dateien“; Skips sind dank `-ra` sichtbar, brechen aber nichts (2.4, 2.11, G3).
- `tests/scenarios/`: 88 Configs statt 40 (2.4).
- `action-pin-validation.sh` prüft die eigenen Workflows, aber nur Ref-Existenz, kein SHA-Zwang (2.6).
- Wall-Clock in G10 auf 23-27 min vereinheitlicht; `--validate`-Doppelung ist laut Workflow-Kommentar bewusst (2.5, W3-E).
- „Evaluate“-Modus für Rulesets ist Enterprise-only (R1).

Ergänzungen (Best Practices):
- G23/R10/R11: Path-Filter × Required Check, Gate-Job je Workflow mit `if: always()`, In-Job-Änderungserkennung statt Trigger-`paths:` (W1-F, Akzeptanzkriterien).
- G24/W2-G: Constraints-Datei für Reproduzierbarkeit; G25/W1-H: `actionlint`, `zizmor`, OpenSSF Scorecard (einzige OIDC-Nutzung).
- W1-A: `integration_id` für Required Checks, Bypass-Modus `pull_request`, Strict-Policy und Merge Queue (`merge_group`) als offene Entscheidung.
- W1-C/W1-D: Dependabot mit `directories`, `groups`, `cooldown`; Dependabot-Alerts als Voraussetzung; CodeQL Default Setup statt Workflow; `sha_pinning_required` nach Pinning; `persist-credentials: false`.
- W2-A/W1-E: ruff ohne native Baseline, Versions-Pin, `target-version = "py39"`; `ast.feature_version` ist nur best-effort.
- W2-B/W2-C/W2-D: Skip-Fail nur im Browser-Job; Marker zentral per Conftest + `--strict-markers`; Path-Liste um `snippets/`, `commands/`, `platform-configs/`, `speech/`, `standalone/`, `requirements.txt` erweitert.
- W3-A/W3-B: pytest-split-Grenzen bei Modul-Fixtures; Coverage-Combine über Shards und Subprocess-Coverage für `sync.py`.
- R12/R13: 3.9-Verfügbarkeit auf Runnern, `pull_request_target`-Verbot für künftige Workflows.
