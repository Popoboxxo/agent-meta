# Welle 4 (Test-Hygiene #945) — Status / Pause-Punkt

> Status: pausiert (2026-10-31)
>
> **Pause-Punkt, kein Abschluss.** Welle 4 ist eröffnet, die Spec ist freigegeben
> und gemergt, **P1 ist gemergt** — sechs der sieben Phasen sind offen. Dieses
> Dokument hält den Stand für den Wiedereinstieg fest; es ersetzt weder Spec noch
> Phasenplan.

| Feld | Wert |
|---|---|
| Repo | `agent-meta` (`/home/hermes/repos/agent-meta`) |
| Datum | 2026-10-31 |
| `main` | `653c8228` == `origin/main` |
| Arbeitsbaum | clean |
| Spec | `docs/specs/2026-10-30-test-hygiene-945-design.md` — Rev. 3.1, `Status: APPROVED (2026-10-31)` |
| P1-Plan | `docs/plans/2026-10-31-wave-4-p1-timeout-contract-plan.md` — DONE |
| Tracking | Issue #945 (`tests,ci`) |
| Letztes Release | `v2.0.0-beta.6` (Tag-Ziel `fe086a57`) |

## Wo wir stehen

- **Welle 4 ist eröffnet:** Issue #945 (Test-Hygiene), sieben Phasen
  P1 → P2a → P2b → P3 → P4 → P5 → P6.
- **Spec APPROVED und gemergt:** `docs/specs/2026-10-30-test-hygiene-945-design.md`,
  Rev. 3.1, freigegeben am 2026-10-31 durch den User; PR #1100, Merge `ff334aa3`.
- **P1 ist fertig und gemergt:** PR #1103, Merge `653c8228`, 23/23 CI-Checks grün,
  Review **APPROVED** (0 blockierend, 8 nicht blockierende Advisories).
  Exit-Gate: **1370 passed / 0 failed** über die neun Hook-Module plus den neuen
  Guard (26 Tests); `.claude/hooks/.guard-audit.log` vor/nach byte-identisch;
  `sync.py --validate` Exit 0; `consistency-check` PASS.
- **Sechs Phasen sind offen:** P2a, P2b, P3, P4, P5, P6.

## Phasenstand

| Phase | Inhalt | Größe | Dateien | Stand | Schließt |
|---|---|---|---|---|---|
| **P1** | Timeout-Contract + Hook-Slice-Isolation | L | 14 | **done** (PR #1103, Merge `653c8228`) | AC1 (lokal beweisbar), AC3 (Hook-Slice) |
| **P2a** | Timeout-Adoption: Sync-/CLI-Treiber + Optimizer-Familie | XL | 32 | open | AC3 (Teil) |
| **P2b** | Timeout-Adoption: Fixture-/Kontext-/Repo-Copy-Module | XL | 31 | open | AC3 (Rest) |
| **P3** | Vollständigkeits-Check `test.subprocess-timeout-missing` (ERROR) | M | 5 | open | AC3 (Beweis) |
| **P4** | CI-Beweis + Artefakt-Job + Meta-Test | M | 3 | open | AC1 (CI), AC4 |
| **P5** | AC5-Entscheidung dokumentiert | S | 2 | open | AC5 |
| **P6** | Playwright-CI-Pfad (`browser-test.yml`) | M | 3 | open | AC6 |

Reihenfolge laut Spec: **P1 → P2a → P2b → P3 strikt sequenziell**; **P4 nach P1**,
sonst parallel; **P5 und P6 unabhängig**. Rollback-Reihenfolge bei Revert-Kaskade:
**P3 → P2b → P2a → P1**.

## Was seit beta.6 auf main kam

- **#1050 — Fork-Bomb-Brace-Nesting:** PR #1097, Merge `b578aa79` (Issue CLOSED).
- **#1051 — Submodule-Push-Ziele:** PR #1098, Merge `f541de75` (Issue CLOSED).
- **#1088 — `timeout-minutes` für `scorecard.yml:jobs.analysis`:** Merge
  `a1c58800` → **AC2 9/9**. *Hinweis:* `a1c58800` ist Vorfahre des beta.6-Tags
  (`fe086a57`), also **in `v2.0.0-beta.6` enthalten** und nicht „seit beta.6";
  der Punkt gehört inhaltlich in dieses Etappen-Fenster.
- **Welle-4-Spec Rev. 3.1 APPROVED + gemergt:** PR #1100, Merge `ff334aa3`.
- **P1-Plan gemergt:** PR #1101, Merge `314f9451`.
- **P1 (Timeout-Contract + Hook-Slice-Isolation) gemergt:** PR #1103, Merge
  `653c8228` — heute `main`/`origin/main`.

## Was beim Wiedereinstieg zuerst zu tun ist

1. **P2a-Plan schreiben** (32 Dateien, XL) — aus Rev. 3.1 ableiten, Plan-Gate
   durchlaufen, dann ausführen. P2a ist strikt nach P1 erlaubt und blockiert
   P2b und P3.
2. **P2b** (31 Dateien, XL) — dedupliziert sechs `RUN_TIMEOUT = 900` auf
   `SLOW_TIMEOUT`; strikt nach P2a.
3. **P3** (5 Dateien, M) — der AST-Vollständigkeits-Check
   `test.subprocess-timeout-missing` (Severity ERROR) wird erst sinnvoll, wenn
   P2a und P2b die Adoption abgeschlossen haben; vorher meldet er hunderte
   Findings.
4. **P4** (3 Dateien, M) — CI-Digest je Shard + `artifacts`-Job + Meta-Test;
   nach P1 erlaubt, parallel zu P2a/P2b/P3/P5/P6.
5. **P5** (2 Dateien, S) und **P6** (3 Dateien, M) — unabhängig, jederzeit
   parallelisierbar.

## Bekannte Einschränkungen (übernommen)

- **Volllauf:** lokal ~**6207 Tests / ~3,4 h** — passt in keinen Tool-Call
  (Kappung bei ~25 min).
- **CI-Sharding:** `.github/workflows/orchestration-test.yml` fährt mit
  `-n 2 --dist loadfile`.
- **`-n auto` ist repo-weit verboten** — jeder Worker spawnt eigene `sync.py`-Kinder.
- **Runner-Queues** von bis zu ~25 min; Checks niemals per `--admin` umgehen.
- **`rtk pytest` ist defekt** (`Failed to spawn process`) → immer
  `python3 -m pytest`.
- **`--basetemp`-Guard in `tests/conftest.py` ist warn-only** (kein
  `pytest.exit`, kein `pytest.fail`) — eine Warnung über ein Basetemp im Repo ist
  erwartet und kein Fehler.

## Bekannte Follow-ups (Review-Advisories aus PR #1103)

Nicht blockierend, 0 blockierende Findings; für eine spätere Aufräum-Runde:

1. **Indirekte Call-Ziele im Guard:** `tests/test_hook_test_isolation.py:_classify`
   erkennt nur `Attribute`/`Name`-Ziele — `getattr(subprocess, "run")(...)`,
   `importlib.import_module("subprocess").run(...)`, `runner = subprocess.run; runner(...)`
   und `functools.partial(subprocess.run, …)` ergeben null Findings. Der Scope ist
   IC-6-konform; der Docstring („every" solche Aufrufe) überzeichnet ihn.
2. **Doppelte Guard-Assertions:** `test_every_call_sets_cwd` und
   `test_every_call_sets_non_none_timeout` haben byte-identische Körper
   (`findings == []`); die Fehlermeldung des cwd-Tests spricht von „without cwd=",
   kann aber auch fehlende `timeout=`-Findings melden.
3. **Brittiger Zähne-Test:** `test_guard_has_teeth_on_a_stripped_real_module`
   behauptet `len(findings) == 1`, nachdem jedes `timeout=SCRIPT_TIMEOUT,` aus
   `tests/test_pre_release_check_hook.py` gestrippt wurde — eine legitime zweite
   Call-Site dort bräche den Selbsttest aus sachfremdem Grund (Cross-Modul-Kopplung).
4. **Veralteter `STRICT_CASES`-Kommentar:** in `tests/test_orchestrator_guard_hook.py`
   ist die Formulierung „meaningful without a fixture project" überholt — das Modul
   läuft inzwischen gegen `hook_project_root`.
5. **Doppelter Import (Nitpick):** `tests/conftest.py` führt `import pytest` neben dem
   bestehenden `from pytest import PytestWarning`; ein Import-Stil genügt.
6. **Checkout-Bindung nur teilweise:** `tests/test_hook_test_isolation.py:_binds_repo_root`
   (Regel 3) ist strenger als IC-6, aber umgehbar — ein Inline-
   `cwd=str(Path(__file__).resolve().parents[1])` oder eine funktionslokale
   Repo-Root-Variable entgeht ihr. Sinnvolle Härtung, aber nicht die vollständige
   Garantie, die der Regeltext suggeriert.
7. **Prozess — Commit-Aufteilung:** der Plan versprach acht separate Commits, HEAD
   hatte sieben (die beiden Doku-Tasks landeten zusammen), und der Betreff von Task 1
   nutzt `feat:` statt des geplanten `test:`.
8. **Prozess — Plan-Arithmetik:** der Plan zählte 13 fehlende `cwd=`-Sites, der
   AST-Guard fand **14** (die `bash -n`-Call-Site in `test_hook_containment…`).
   Die Implementierung ist korrekt, die Plan-Zahl veraltet.

## Trace

- Spec: `SPEC-test-hygiene-945` → `docs/specs/2026-10-30-test-hygiene-945-design.md`
- P1-Plan + Ledger: `docs/plans/2026-10-31-wave-4-p1-timeout-contract-plan.md`
- Fortsetzungsplan: `docs/plans/2026-10-30-wave-4-continuation-plan.md`
- Issue: #945 · Mitgeführt: #1050, #1051, #1088
- PRs: #1097, #1098, #1100, #1101, #1103
