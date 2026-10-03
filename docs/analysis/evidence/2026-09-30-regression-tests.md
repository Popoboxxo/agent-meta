# Regression Tests — Provider-Audit OpenCode v2 (Phase D)

**Datum:** 2026-09-30 (Lauf endete 2026-10-01 ~00:10)
**Branch:** `feat/provider-audit-opencode-v2`
**HEAD:** `65a493ec13dd5cc67d74ea4640e3759600205faa`
**Umgebung:** Python 3.13.5 · pytest 9.1.1 · pytest-socket aktiv · playwright-Paket installiert
**Laufzeiten:** scenarios `1290s` · pytest full `464.22s (0:07:44)` · pytest `--ignore=tests/browser` `457.03s`
**Scratch/Logs:** `/var/tmp/opencode-audit/regression/` · Szenario-Tempdirs via `TMPDIR` in Scratch umgeleitet.
**Keine git-Mutation, kein Branch-Wechsel, keine Test-/Code-Reparatur.**

## 1. Arbeitsbaum vorher

```console
$ git rev-parse HEAD
65a493ec13dd5cc67d74ea4640e3759600205faa
$ git status --porcelain
?? docs/analysis/2026-09-30-provider-audit-docs-part1.md
?? docs/analysis/2026-09-30-provider-audit-docs-part2.md
?? docs/analysis/2026-09-30-provider-audit-generation.md
?? docs/analysis/evidence/
$ sync.log mtime: 2026-09-30 10:54 (unverändert bis Laufende)
```

## 2. `python3 scripts/sync.py --dry-run`

```console
$ python3 scripts/sync.py --dry-run
... [WARN] generated-file-drift: .opencode/agents/*.md ... (prospektiv)
SUMMARY
-------
27 action(s)  |  429 skipped  |  93 warning(s)
Logfile: /home/hermes/repos/agent-meta/sync.log
EXIT=0
```
Exit-Code `0`. Nachlauf: `git status --porcelain` unverändert. `sync.log` **nicht** neu geschrieben;
keine `*.sync-backup-*`-Datei angelegt (Warnung „Backup written to …" ist prospektiv).

## 3. `python3 scripts/sync.py --validate`

```console
$ python3 scripts/sync.py --validate
  !  Config validation warnings (1):
       agent-meta-version: '1.2.0-beta.2' does not match '^\\d+\\.\\d+\\.\\d+$'
  agent-meta consistency-check
  [WARN] 85 warning(s) found  (85 total findings)   # placeholders.unknown {{PARSE_INPUT_BLOCK}}/{{OUTPUT_GUARD_BLOCK}} + changelog-missing-entry
  agent-meta consistency-check
  [WARN] 1 warning(s) found  (1 total findings)      # orchestrator-strict / repo-containment no-hook-support
EXIT=0
```
Exit-Code `0`, nur WARN/INF (keine Errors). `git status --porcelain` vor/nach **identisch**
(Diff Exit `0`) → `--validate` mutiert den Arbeitsbaum nicht.

## 4. `tests/scenarios/run.sh` (voller Katalog)

```console
$ TMPDIR=<scratch> bash tests/scenarios/run.sh
... PASS 01..63 ...
----
Scenarios: 63  Passed: 63  Failed: 0
EXIT=0
RUNTIME_SECONDS=1290
```
**63 Szenarien, 63 PASS, 0 FAIL** (Katalog enthält 63 `*.project.yaml`, nicht 64).
Keine `<tmp>/.scenario-logs/*`-FAIL-Logs vorhanden, da alle Tempdirs bei PASS gelöscht wurden.

## 5. `python3 -m pytest tests/ -q`

```console
$ python3 -m pytest tests/ -q
3132 passed, 102 warnings, 35 errors, 11 subtests passed in 464.22s (0:07:44)
PYTEST_EXIT=1
```
Alle **35 Errors** liegen in `tests/browser/` und sind identisch vom Typ
`pytest_socket.SocketBlockedError: A test tried to use socket.socket.`
(Auslöser: `tests/browser/conftest.py:36 _wait_for_server` — der lokale Admin-Server
kann unter dem aktiven `pytest-socket`-Plugin nicht binden). **Umgebungsbedingt, keine Code-Regression.**

Kontrolllauf ohne Browser-Suite:

```console
$ python3 -m pytest tests/ -q --ignore=tests/browser
3127 passed, 102 warnings, 11 subtests passed in 457.03s (0:07:37)
PYTEST_NOBROWSER_EXIT=0
```
3132 − 3127 = 5 passed in `tests/browser/` + 35 Errors = 40 Browser-Tests → Bilanz konsistent.

## 6. Zusatzchecks

```console
$ python3 scripts/sync.py --check
27 file(s) out of sync — run `python scripts/sync.py` to regenerate.
CHECK_EXIT=1
```
**Repo-Checkout ist NICHT driftfrei:** 27 generierte Dateien weichen vom Template-Stand ab
(erwartet auf diesem Feature-Branch). Read-only, kein Schreibzugriff.

```console
$ python3 scripts/consistency-check.py
[WARN] 85 warning(s) found  (85 total findings)
CONSISTENCY_EXIT=0
```
Standalone identisch zum `--validate`-Block (85 Warnungen), Exit `0`.

## Ergebnis-Tabelle

| Suite | PASS | FAIL/ERROR | Exit | Verdikt |
|---|---|---|---|---|
| `sync.py --dry-run` | — | 0 errors | 0 | PASS |
| `sync.py --validate` | — | 0 errors (85 WARN) | 0 | PASS (Warnungen) |
| `tests/scenarios/run.sh` | 63 | 0 | 0 | PASS |
| `pytest tests/ -q` | 3132 | 35 ERROR (browser) | 1 | FAIL (umgebungsbedingt) |
| `pytest tests/ -q --ignore=tests/browser` | 3127 | 0 | 0 | PASS |
| `sync.py --check` | — | 27 Dateien Drift | 1 | FAIL (Drift vorhanden) |
| `consistency-check.py` | — | 85 WARN | 0 | PASS (Warnungen) |

## Fehlschläge mit Kurzursache

- **35 × `tests/browser/*`** — `pytest_socket.SocketBlockedError` im Fixture-Setup
  (`_wait_for_server`); Browser-Server kann nicht starten. Kein Produktcode involviert.
- **`sync.py --check` rc=1** — 27 generierte Dateien out-of-sync (Drift).

## Arbeitsbaum-Mutationsverdikt

**VERDICT: „keine Mutation durch Tests" — VERIFIED.**
- `git status --porcelain` nach allen Läufen: keine Tracked-Änderung, `sync.log` unverändert,
  keine neuen `*.sync-backup-*` außerhalb `.tmp/` (0 Treffer seit 23:00).
- Szenarien laufen isoliert in `mktemp`-Tempdirs (siehe `run.sh`-Header), schreiben nie ins Repo.
- Zwei neue untracked Docs erschienen (mtime 23:14:34 / 23:15:36, **während** des Szenario-Laufs):
  `docs/analysis/2026-09-30-provider-audit-runtime-consolidation.md`,
  `docs/specs/2026-09-30-provider-audit-opencode-v2-design.md`.
  Sie werden von **keinem** Test referenziert und sind Provider-Audit-Artefakte → zuzuschreiben
  **parallelen Schwester-Agenten** auf demselben Branch, nicht den Testkommandos.

## Offene Punkte

1. `--check` rc=1: Der Checkout ist nicht driftfrei (27 Dateien) — vor Merge/Release neu syncen.
2. Browser-Suite (35 Errors) ist in dieser Umgebung nicht lauffähig (`pytest-socket` blockt Sockets);
   für echte Browser-Regression `pytest-socket` deaktivieren bzw. Server-Fixture entkoppeln.
3. `--validate` meldet Config-Warnung: `agent-meta-version: '1.2.0-beta.2'` verletzt das Semver-Regex.
4. 85 Consistency-Warnungen: unbekannte Platzhalter `{{PARSE_INPUT_BLOCK}}`/`{{OUTPUT_GUARD_BLOCK}}`
   + fehlende CHANGELOG-Einträge für neue Snippets — auf diesem Branch erwartbar, aber dokumentiert.
