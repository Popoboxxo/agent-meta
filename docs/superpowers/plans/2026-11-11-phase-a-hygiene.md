---
pipeline_stages:
  implement: 2
status: DRAFT
date: 2026-11-11
base-commit: a3d65da4
branch: fix/phase-a-pytest-split-marker
trace:
  - roadmap-2026-11-10-backlog-roadmap
  - phase-A-hygiene
---

# Phase A (Hygiene) Implementation Plan

> Status: **DRAFT** (2026-11-11). Dieser Plan führt nichts aus: keine `gh`-Änderung, kein Commit, kein Push, kein Löschen.
> Ausführung strikt **nach Freigabe durch den User**. Basis: `origin/main a3d65da4` (Plan-Stand). Basischeck: `origin/main` jetzt `9aa0e0c0`; read-only per `gh` verifiziert (Entscheidung 38f): PR #1218 MERGED (mergeCommit `9aa0e0c0c45b08363a8bf75a88600d863d3e5172`, 2026-11-11T06:41:30Z), Issue #1190 CLOSED durch Auto-Close (2026-11-11T06:41:32Z, COMPLETED, ohne Kommentar). Anker gemäß Task 1 Step 2 gegenprüfen.
> **Entscheidungen:** 17-34 (Quelle `.tmp/decisions-part2.md`, bindend), 35-38 (Quelle `.tmp/decisions-part3.md`, bindend), siehe Abschnitt »Entscheidungen (beantwortet)«.
> **Roadmap:** `docs/superpowers/plans/2026-11-10-backlog-roadmap.md` (APPROVED 2026-11-11), Abschnitt 2 Phase A, Abschnitt 3 Welle 0, Abschnitt 7 Entscheidungen 12 und 13.
> **Issues (11):** #547, #857, #858, #1007, #1116, #1151, #1150, #946, #885, #977, #1190 (bereits CLOSED durch Auto-Close, Task 9 prüft nur und reicht den Beleg nach). **PRs:** #1218 (MERGED), #1145, #1148.
> **Querverweis-Aktionen (zählen in anderen Phasen):** Label `blocked` für #860/#854 (G), Teil-Kommentare #1155 (C), #1158/#1159/#1161 (H), #1160 (G).
> **Querverweis #1086g (Entscheidung 24, Phase C):** Schließen mit Entscheidungskommentar, keine Aktion in Phase A.
> **Abhängigkeiten:** Welle 0, Phase A hängt von nichts ab. #1190 hing am Merge von #1218; #1218 ist in `origin/main 9aa0e0c0` gemergt, #1190 ist durch Auto-Close geschlossen (Task 9, Entscheidung 38f). Phase B (Welle 1) wartet auf grüne CI, die der Marker-Fix (Task 2) entlastet.

## Änderungsprotokoll

Stand 2026-11-13, gegen `origin/main b36184b5` im Worktree geprüft (nicht nur PR-Beschreibung). Status bleibt **DRAFT** (keine neue Freigabe).

| PR | Zustand | Task | Beleg |
|---|---|---|---|
| #1223 | MERGED 2026-11-12 | Task 2 (Marker-Fix), Task 7 (Marker-PR gemergt) | `tests/requirements.txt:13-14` (zwei Marker-Zeilen), `tests/test_requirements_pytest_split_marker.py` (3 Tests, lokal grün) |
| #1221 | MERGED 2026-11-12 | kein Task dieses Plans | Freshness-Tooling `scripts/check_plan_refs.py` (Frische-Check-Referenzen) |
| #1145, #1148 | CLOSED (`gh`) | Task 8 | Zustand bestätigt; Schließ-Kommentar und Urheber nicht geprüft, Checkboxen nicht gesetzt |
| Issues #547, #857, #858, #1007, #1116, #1151, #1150, #1190 | CLOSED (`gh`) | Tasks 3-6, 9 | nur Zustand geprüft, Evidenz-Kommentare/Reihenfolge nicht geprüft, Checkboxen nicht gesetzt |

Offen (Stand `gh`): #946 (Task 10), #885 (Task 12), #977 (Task 11) OPEN; Label `blocked` an #860/#854 vorhanden (Task 13, Kommentar-Inhalt ungeprüft); Task 14 (Teil-Kommentare) und Task 15 ungeprüft. Task 2 Steps 2/5/6 (Rot-Lauf, Resolver-Trockenlauf, `--validate`) und Task 7 Step 2 (CI-Watch) nicht einzeln belegt, daher unabgehakt.

**Goal:** Das Backlog bereinigen: erledigte Issues mit Evidenz-Kommentar schließen, Duplikat-PRs abräumen, Tracker (#977, #885) und Teil-Stände (#1155, #1158..#1161) dokumentieren, blockierte Issues labeln, die Branch/Stash-Tabelle für #946 zur Freigabe vorlegen. Einzige Code-Änderung: der Marker-Fix für `pytest-split` in `tests/requirements.txt`.

**Architecture:** Reiner Operationsplan. Jede Operation ist ein `gh`-Befehl (oder eine Prüfung), der **nicht** ausgeführt wird, bevor der User freigibt. Kommentartexte werden als Dateien unter `.tmp/phase-a/comments/` geschrieben (Roadmap Abschnitt 4: Text als Datei, nicht inline per Shell) und per `--body-file` übergeben. Jede Schließung hat eine Vorprüfung (Gate) und eine Nachprüfung (`gh issue view`).

**Tech Stack:** `gh` CLI (`/home/hermes/.local/bin/gh`, nicht im `$PATH`), pytest, Python 3.9+ (stdlib), pip-Marker nach PEP 508.

**Spec:** keine, siehe Klassifizierung: alle Arbeiten sind Klasse S (Operationen ohne Produktcode, ein Einzeiler plus Test). Es gibt kein Spec-Gate in Phase A.

## Klassifizierung (Spec-Plan-Gate)

| Item | Klasse | Begründung |
|---|---|---|
| Marker-Fix `tests/requirements.txt` | S | eine Datei, zwei Zeilen, ein Test, keine Produktlogik |
| Issue-/PR-Operationen (alle übrigen) | S | keine Repo-Änderung, nur GitHub-Zustand |
| #946 Branch/Stash-Tabelle | S | Erhebung plus Entscheidungsvorlage; Löschung nur nach Tabellenfreigabe (Entscheidung 12) |

Spec-Gates: **0**.

## Global Constraints

- Python 3.9 kompatibel (kein `X | Y`, kein `match`), stdlib plus PyYAML. Der Marker-Test nutzt `packaging` nur per `pytest.importorskip` (pytest bringt `packaging` mit).
- Provider-agnostisch über Config-Keys, nie `if provider == ...`. Phase A fasst keinen Syncer-Code an.
- Commits: Englisch, Conventional Commits, erste Zeile höchstens 72 Zeichen, Imperativ, kein BOM (Issue #842).
- Kein `isolation: "worktree"`. Kein Admin-Bypass. Squash-Merge nach grüner CI.
- Tests: `python3 -m pytest <datei>::<test>`; Validierung: `python3 scripts/sync.py --validate`.
- **Keine Operation vor Freigabe.** Schließen nur mit Evidenz-Kommentar, Kommentar zuerst, dann manuell schließen (Entscheidung 38e). PR- und Commit-Texte von Phase A enthalten keine Schlüsselwörter `Closes`/`Fixes`/`Resolves`, damit kein Auto-Close entsteht. Bei Kommalisten in "Resolves" schließt nur die erste Nummer automatisch.
- **Destruktive Git-Befehle werden nie umgangen.** Blockiert der Guard (exit 2), liefert der Assistent die fertigen Befehle, der User führt sie per `!` aus (Entscheidung 12, Roadmap Abschnitt 4).
- `gh`-Alias für alle Befehle: `GH=/home/hermes/.local/bin/gh`.
- Das Arbeitsverzeichnis für Kommentardateien ist `.tmp/phase-a/` (Repo-Containment-Sink, gitignored).
- Ein PR pro Phase (Entscheidung 17): Phase A hat genau einen PR (Marker-Fix, Task 7). Alle übrigen Operationen sind `gh`-Schritte ohne PR.

## File Structure

- Modify: `tests/requirements.txt` — Zeile 13 `pytest-split>=0.8` wird in zwei Marker-Zeilen aufgeteilt (Task 2).
- Create: `tests/test_requirements_pytest_split_marker.py` — Test, der die beiden Marker-Zeilen und ihre Auswahl je Python-Version prüft (Task 2).
- Create (gitignored, nicht committet): `.tmp/phase-a/comments/<N>.md` — Kommentartexte je Issue/PR.
- Create (gitignored, nicht committet): `.tmp/phase-a/946-branch-table.md`, `.tmp/phase-a/946-stash-838.patch` — Tabelle und Stash-Sicherung (Task 10).
- Create (gitignored, nicht committet): `.tmp/phase-a/977-body.md` — bearbeiteter Tracker-Body (Task 11).

## Abweichung zur Roadmap

Jede Abweichung wurde im Worktree `W` gegen den Code geprüft. `W` = `/home/hermes/repos/agent-meta/.tmp/wt-phase-plans`.

1. **#857, Anker falsch.** Die Roadmap nennt `ai-providers.yaml:150-154`. Dort steht der Gemini/Antigravity-Discovery-Block (`config/ai-providers.yaml:150-155`: `model-literal: inherit`, `discovery`). Die Mammouth-Belege stehen bei `config/ai-providers.yaml:645-647` (Capabilities `skills`, `mcp`), `:659-669` (Kommentar `#857: real MCP surface`, `mcp-config` mit `committed-file: mammouth.json`) und `:670` (`skills_dir: .mammouth/skills`).
2. **#1190, Schließweg.** Die PR-Beschreibung von #1218 endet mit `Closes #1190` (`.tmp/prs/1218.md`, letzte Zeile). Der Merge von #1218 nach `main` hat #1190 automatisch geschlossen (2026-11-11T06:41:32Z, read-only per `gh` verifiziert). Phase A schließt #1190 nicht erneut und öffnet es nicht wieder; Task 9 prüft den Zustand und reicht den Evidenz-Kommentar nach (Entscheidung 38f).
3. **#1007, "SCHON_GEBAUT" nur teilweise.** Von den 7 Punkten sind 5 belegt; Punkt 2 (`experimental.todo`) und Punkt 5 (`$schema`/`skills`) weichen bewusst vom Issue-Text ab (Details Task 4). Die Schließung ist durch Entscheidung 21 (A-N2) gedeckt: schließen mit Evidenz-Kommentar, beide Abweichungen benannt.
4. **#547, "SCHON_GEBAUT" nur teilweise.** `docs/guides/cross-harness-dev-isolation.md:171-199` ("Open points / Follow-ups") listet **fünf** bewusst nicht umgesetzte Punkte (Review 2026-11-11 gegen `origin/main 9aa0e0c0`): 1 Strategy B (`:176-182`), 2 Auswahl des dritten Harness (`:183-185`), 3 Task-Partitionierung (`:186-189`), 4 Branch-Purge (`:190-194`, läuft in #946), 5 Per-Harness- vs. zentrales Config-Verzeichnis (`:195-199`). Die Schließung ist durch Entscheidung 20 (A-N1) gedeckt; Entscheidung 39 (A-Q1) erweitert das Follow-up-Issue auf alle fünf Punkte (`:176-199`).
5. **#1186-Text veraltet.** Der Issue-Text von #1186 (Stand 2026-11-08) nennt `/tmp/opencode/` in acht Generic-Templates als offen. In `W` ist das behoben: `agents/1-generic/backend-reviewer.md:64` nennt keinen Pfad mehr, kein Treffer für `/tmp/opencode` in `agents/1-generic/`. Das ist ein Hinweis für Phase E, keine Phase-A-Aktion.
6. **Hook-Pfade.** Die Hooks liegen in `W` unter `hooks/1-generic/` (nicht `.claude/hooks/` wie im Issue-Text von #1151). Die Zeilenanker des Issues sind verschoben (Task 5).
7. **#885-Stand verifiziert.** F-01, F-04, F-07 sind in `W` belegt behoben (Task 12). F-08 bleibt laut Roadmap behoben, ist nicht selbst geprüft.
8. **`check_plan_refs.py`.** Das Skript liegt nicht auf `origin/main` (`git ls-tree origin/main scripts/check_plan_refs.py` leer), aber ungemergt im Worktree `/home/hermes/repos/agent-meta/.tmp/wt-check-plan-refs/scripts/check_plan_refs.py`. Task 1 Step 2 nutzt es, solange es dort liegt; sonst manuelle Prüfung.

## Entscheidungen (beantwortet)

Quelle: Roadmap-Entscheidungen 17-34 (`.tmp/decisions-part2.md`, bindend). Originalnummern dieses Plans in Klammern.

- **A-N1 (#547 schließen trotz drei offener Follow-ups): beantwortet durch Entscheidung 20.** Gewählt: Option (b). Schließen mit Evidenz-Kommentar und Follow-up-Issue; dessen Umfang setzt Entscheidung 39 auf alle fünf Guide-Punkte. Anlage und Schließung erst nach Freigabe der Phase-A-Ausführung; Text vorab als Datei (Task 3b).
- **A-N2 (#1007 schließen trotz zweier Abweichungen): beantwortet durch Entscheidung 21.** Gewählt: Option (a). Schließen mit Evidenz-Kommentar (PRs #1012, #1016-#1019, `docs/providers/opencode.md`); die Abweichungen `experimental.todo` (nur per Projekt-Option, keine Ableitung aus `todowrite`) und `$schema`/`skills` sind benannt (Task 4b).
- **Weitere Entscheidungen aus 17-34, die diesen Plan berühren:**
  - 17: ein PR pro Phase; der Marker-Fix ist der eine PR von Phase A.
  - 19: Kette #1187 -> #1186 -> #1188 -> #1181 -> #1141. #1186 liegt in Phase E; die Duplikat-Schließung #1150 bleibt davon unberührt.
  - 24: #1086g wird mit Entscheidungskommentar geschlossen (Phase C); hier nur Querverweis.
  - 38c (#1086): g bleibt Dokumentation und Schließen (Phase C), konsistent mit dem Querverweis oben; keine Aktion in Phase A.
  - 35, 36: kein Phase-A-Bezug (35 betrifft Phase D/F, 36 die PR-Ausnahmen #1209 und #1086i).
- **38e (Auto-Close-Regel, beantwortet durch Entscheidung 38e):** Die Regel »Issues nur mit Evidenz-Kommentar schließen« gilt. PR- und Commit-Texte ohne Schlüsselwörter `Closes`/`Fixes`/`Resolves`; Kommentar zuerst, dann manuell schließen. Umgesetzt in Global Constraints, Task 6 (Reihenfolge Kommentar, dann Schließen) und Task 7 (PR-Text).
- **38f (#1190, beantwortet durch Entscheidung 38f):** PR #1218 gemergt (`9aa0e0c0c45b08363a8bf75a88600d863d3e5172`), #1190 durch Auto-Close geschlossen. Task 9 ist eine Prüf-Task mit nachträglichem Beleg-Kommentar nach Freigabe; kein Schließen, kein Wiederöffnen.

**Offen (neu, ungeklärt):** keine mehr; A-Q1 ist beantwortet:

- **A-Q1 (#547, Guide-Punkte 4 und 5): beantwortet durch Entscheidung 39.** Alle fünf offenen Guide-Punkte (`docs/guides/cross-harness-dev-isolation.md:176-199`), auch 4 Branch-Purge (`:190-194`) und 5 Per-Harness- vs. zentrales Config-Verzeichnis (`:195-199`), gehen ins Follow-up-Issue (Task 3b). Ersetzt die drei Punkte aus Entscheidung 20.

## Frische-Check-Referenzen

- Pfade: `tests/requirements.txt`, `tests/test_requirements_pytest_split_marker.py`, `.github/workflows/orchestration-test.yml`, `.github/dependabot.yml`, `config/ai-providers.yaml`, `config/provider-capabilities.yaml`, `docs/guides/cross-harness-dev-isolation.md`, `docs/providers/opencode.md`, `scripts/lib/opencode_v2_config.py`, `scripts/lib/mcp_provider_config.py`, `scripts/lib/isolation.py`, `scripts/lib/provider_transform.py`, `scripts/lib/consistency/artifact_contracts.py`, `scripts/lib/deactivation.py`, `tests/test_orchestrator_guard_hook.py`, `tests/test_hook_common_lib.py`, `tests/test_no_role_routes_in_templates.py`, `hooks/1-generic/orchestrator-guard-impl.sh`, `hooks/1-generic/repo-containment-impl.sh`, `hooks/1-generic/lib/hook_common.sh`, `tests/scenarios/asserts/69-opencode-v2-surface.sh`, `tests/scenarios/asserts/79-opencode-v2-full-surface.sh`, `config/harnesses/claude.yaml`, `config/harnesses/opencode.yaml`, `config/harnesses/third.yaml`, `agents/1-generic/backend-reviewer.md`, `docs/analysis/2026-09-30-provider-audit-docs-part2.md`, `.tmp/decisions-part2.md` (Entscheidungen 17-34), `.tmp/decisions-part3.md` (Entscheidungen 35-38), `.tmp/prs/1218.md`. Zeilenanker: nicht neu gemessen; Re-Measure nur, wo ein Task es verlangt.
- Symbole: `_HANG_GUARD_SECONDS`, `permission_deny_required`, `reconcile_opencode_surface_gate`, `sync_opencode_v2_managed_keys`, `map_tools_to_opencode_v2_permissions`, `check_mcp_connection_keys`, `_SCOPE_GLOBS`, `write_atomic`.
- Issues und PRs: #547, #857, #858, #860, #854, #885, #904, #946, #977, #994, #1007, #1012, #1016, #1017, #1018, #1019, #1116, #1145, #1148, #1150, #1151, #1153, #1155, #1158, #1159, #1160, #1161, #1163, #1164, #1165, #1086, #1186, #1190, #1218, #1219.
- Commits (Review 2026-11-11 per `git log`/`merge-base --is-ancestor` geprüft, siehe »Nicht verifiziert«; zusätzlich `97b4e49f` = #1018): `fa37d7d0`, `c1e810c6`, `283fcd3c`, `f55601ba`, `89cc6381`, `35f591e6`, `90be1146`. Basis-Commit nach Basischeck: `9aa0e0c0` (origin/main, enthält #1218; Anker nicht neu geprüft). Merge-Commit #1218: `9aa0e0c0c45b08363a8bf75a88600d863d3e5172` (read-only per `gh` verifiziert, Entscheidung 38f).

---

### Task 1: Vorbedingungen und Freshness (read-only)

**Rolle:** `git` (Git-Lesezugriffe über Subagent), Rest `developer`. **Klasse:** S. **Hängt ab von:** Freigabe.
**Files:** keine. Legt `.tmp/phase-a/` an.
**Interfaces:** Produces: bestätigter Ausgangsstand für alle folgenden Tasks.

- [ ] Step 1: `$GH auth status` — Erwartung: authentifiziert für `Popoboxxo/agent-meta`.
- [ ] Step 2: `git fetch origin && git rev-parse --short origin/main` — Erwartung: `a3d65da4` oder neuer. Ist es neuer, jeden Zeilenanker dieses Plans per `git diff a3d65da4 origin/main --stat -- <datei>` gegenprüfen, plus `python3 .tmp/wt-check-plan-refs/scripts/check_plan_refs.py --plans <dieser Plan> --repo . --ref origin/main` (falls vorhanden). Review 2026-11-11: alle Anker dieses Plans gegen `9aa0e0c0` nachgezogen (a3d65da4..9aa0e0c0 ändert u. a. `scripts/lib/isolation.py` und `.github/workflows/orchestration-test.yml`).
- [ ] Step 3: Stand der Zielobjekte erheben, Erwartung: alle Issues `OPEN` außer #1190 (`CLOSED` seit 2026-11-11T06:41:32Z durch Auto-Close), #1218 `MERGED`, #1145/#1148 `OPEN`:
  `for n in 547 857 858 1007 1116 1151 1150 946 885 977 1190; do $GH issue view $n --json number,state,title -q '"\(.number) \(.state) \(.title)"'; done`
  `for n in 1218 1145 1148; do $GH pr view $n --json number,state,mergeable,statusCheckRollup -q '"\(.number) \(.state) \(.mergeable)"'; done`
- [ ] Step 4: Label prüfen: `$GH label list --search blocked --json name,color` — Erwartung: leer (read-only gemessen 2026-11-11: `gh label list --search blocked` ohne Treffer), dann legt Task 13 Step 1 das Label an. Im Label-Spec `docs/specs/2026-11-09-issue-label-taxonomy-spec.md` kommt `blocked` nicht vor; die Taxonomie (#1188) ist nicht umgesetzt, daher gilt hier der Name aus der Roadmap.
- [ ] Step 5: `mkdir -p .tmp/phase-a/comments` (nur Repo-Sink).
- Akzeptanz: Step 1 exit 0; Step 3 listet 11 Issues und 3 PRs mit Zustand; jede Abweichung vom Erwartungszustand ist im Ausführungsprotokoll vermerkt, bevor ein weiterer Task startet.

### Task 2: Marker-Fix `pytest-split` (einziger Code-Task, Klasse S)

**Rolle:** `developer`. **Hängt ab von:** Task 1.
**Files:** Modify `tests/requirements.txt`; Create `tests/test_requirements_pytest_split_marker.py`.
**Interfaces:** Produces: zwei Marker-Zeilen, die Python 3.9 bei `>=0.8` halten und Python >=3.10 auf `>=0.11.0` heben. Consumes: CI-Matrix `python-version: ['3.9', '3.12']` (`.github/workflows/orchestration-test.yml:210` und `:392`, Stand `9aa0e0c0`), Installationsschritte `pip install -r tests/requirements.txt` (`:237`, `:409`, `:490`).

**Belegter Ist-Stand (in `W` gelesen):**
- `tests/requirements.txt:13` lautet exakt `pytest-split>=0.8`. Die Datei nutzt dasselbe Marker-Muster bereits für `pytest` (`:5-6`), `jsonschema` (`:10-11`) und `tomli` (`:9`); Kommentar `:4`: "Newer pytest/jsonschema need Python >=3.10; CI still tests 3.9".
- Ursache: pytest-split 0.11.0 entfernt Python 3.8/3.9 (Dependabot-Text in #1145/#1148: "Removed: Support for Python 3.8 and 3.9"). Beide PRs setzen `>=0.11.0` ohne Marker; die 3.9-Jobs finden dann keine passende Version.
- Wirksamkeit des Markers: Die 3.9-Jobs bekommen `pytest-split>=0.8` (wie heute), die 3.12-Jobs `pytest-split>=0.11.0`. Beide Jobs laufen den `--splits 3 --group N`-Schritt (`orchestration-test.yml:356`). `.github/workflows/validate.yml` installiert nur `requirements.txt` (Zeilen 100, 120) und ist nicht betroffen.
- Dependabot scannt `/` und `/tests` (`.github/dependabot.yml:5`); die Marker-Zeilen werden von Dependabot als zwei Einträge gelesen. Ob Dependabot beim nächsten Lauf die Marker-Zeilen korrekt fortschreibt, ist nicht verifiziert.

- [x] Step 1: Test schreiben (rot) in `tests/test_requirements_pytest_split_marker.py`:
  ```python
  from pathlib import Path

  import pytest

  _REQ = Path(__file__).resolve().parent / "requirements.txt"
  _env = {"39": {"python_version": "3.9"}, "312": {"python_version": "3.12"}}


  def _split_requirements():
      req_mod = pytest.importorskip("packaging.requirements")
      reqs = []
      for raw in _REQ.read_text(encoding="utf-8").splitlines():
          line = raw.split("#", 1)[0].strip()
          if line.startswith("pytest-split"):
              reqs.append(req_mod.Requirement(line))
      return reqs


  def _selected(env):
      return [r for r in _split_requirements() if r.marker is None or r.marker.evaluate(env)]


  def test_pytest_split_has_two_marker_lines():
      assert len(_split_requirements()) == 2


  def test_python39_selects_exactly_the_old_floor():
      ver = pytest.importorskip("packaging.version")
      sel = _selected(_env["39"])
      assert len(sel) == 1
      assert ver.Version("0.8.0") in sel[0].specifier


  def test_python312_requires_0_11():
      ver = pytest.importorskip("packaging.version")
      sel = _selected(_env["312"])
      assert len(sel) == 1
      assert ver.Version("0.10.0") not in sel[0].specifier
      assert ver.Version("0.11.0") in sel[0].specifier
  ```
- [ ] Step 2: `python3 -m pytest tests/test_requirements_pytest_split_marker.py -q` — Erwartung rot: `2 failed, 1 passed` — `test_pytest_split_has_two_marker_lines` schlägt fehl (`1 != 2`), `test_python312_requires_0_11` schlägt fehl (heute `>=0.8` lässt 0.10.0 zu). Review 2026-11-11: in einer Sandbox-Kopie unter `.tmp/` mit Python 3.13 gemessen: alt `2 failed, 1 passed`, mit den Marker-Zeilen `3 passed`. Fehlt `packaging`, werden die Tests übersprungen; dann ist der Test hier nicht aussagekräftig und der Befund geht ins Protokoll.
- [x] Step 3: `tests/requirements.txt` ändern: Zeile 13 `pytest-split>=0.8` ersetzen durch genau
  ```text
  pytest-split>=0.8; python_version < "3.10"
  pytest-split>=0.11.0; python_version >= "3.10"
  ```
  und den Kommentar in Zeile 4 um "and pytest-split 0.11 drops 3.9" ergänzen (kein neuer Kommentarblock).
- [x] Step 4: `python3 -m pytest tests/test_requirements_pytest_split_marker.py -q` — Erwartung: `3 passed`.
- [ ] Step 5: Resolver-Trockenlauf, soweit lokal verfügbar: `python3 -m pip install --dry-run -r tests/requirements.txt` — Erwartung: exit 0. Ist ein Python 3.9 vorhanden: dasselbe mit `python3.9` (Review 2026-11-11: auf diesem Host kein `/usr/bin/python3.9`). Nicht vorhanden: als "nicht verifiziert" ins Protokoll; die Wirksamkeit belegt dann erst die CI-Matrix des Phase-A-PRs (3.9 und 3.12 grün).
- [ ] Step 6: `python3 scripts/sync.py --validate` — Erwartung: exit 0 (keine Wirkung erwartet, Regressionsschutz).
- [x] Step 7: Commit: `fix(ci): split pytest-split pin by python version`
- Akzeptanz: Test `3 passed`; CI-Jobs `test (3.9)` und `test (3.12)` im PR grün. PR-Text als Datei `.tmp/phase-a/pr-body-marker.md`, nicht inline.

### Task 3a: Evidenz-Check #547 (read-only)

**Rolle:** `developer`. **Hängt ab von:** Task 1.
**Files:** keine. **Interfaces:** Produces: Punkt-für-Punkt-Tabelle für #547, Eingabe für Entscheidung 20 (A-N1).

Die vier Vorschlagspunkte des RFC gegen den Code (in `W` gelesen):

| # | RFC-Punkt (Issue-Text) | Befund | Beleg |
|---|---|---|---|
| 1 | Checkout-Konvention, getrennte Checkouts | umgesetzt (Strategy A, Worktrees bewusst verworfen) | `docs/guides/cross-harness-dev-isolation.md:14-41` |
| 2 | Branch-Strategie `agent/<harness>` | im Guide behandelt | `docs/guides/cross-harness-dev-isolation.md:57-62` ("Branch strategy", `agent/claude`, `agent/opencode`) |
| 3 | Harness-Abstraktion `config/harnesses/*.yaml`, sync.py harness-aware | umgesetzt: drei Dateien, Schreib-Isolation | `config/harnesses/claude.yaml`, `opencode.yaml`, `third.yaml`; Guide `:3-5` |
| 3b | Task-Partitionierung pro Harness | **nicht umgesetzt** (`default-providers` nur Hinweis) | Guide `:186-189` |
| 4 | Provider-Agnostik gewahrt | im Guide zugesagt; Testdatei existiert (Inhalt nicht auf #547 geprüft) | `tests/test_provider_agnostic_dispatch.py` (in `origin/main` vorhanden) |
| 5 | Branch-Purge ("30+ lokale Branches") | wird in #946 weitergeführt; zusätzlich Punkt 4 im Follow-up-Issue (Entscheidung 39) | Guide `:190-194`; Task 10 |
| 5b | Per-Harness- vs. zentrales Config-Verzeichnis | **offen**, ins Follow-up-Issue (Entscheidung 39) | Guide `:195-199` |
| 6 | Offene Frage Strategy A/B | A umgesetzt, **B offen**, braucht eigene RFC-Runde | Guide `:176-182` |
| 7 | Offene Frage 3. Harness | **offen** (kein Mechanismus, wie ein Tool den Slot belegt) | Guide `:183-185` |

- [ ] Step 1: Punkte 2 und 4 nachprüfen: `grep -n "agent/claude\|agent/opencode" docs/guides/cross-harness-dev-isolation.md` und `ls tests | grep provider_agnostic` — Erwartung: Treffer. Kein Treffer ⇒ die Zeile in der Tabelle auf "nicht belegt" setzen und im Kommentar (Task 3b) streichen.
- [ ] Step 2: Befund ans Ausführungsprotokoll: #547 ist **teilweise** gebaut (4 von 9 Zeilen offen: 3b, 5b, 6, 7; Zeile 5 läuft in #946). Das Roadmap-Verdikt SCHON_GEBAUT gilt nur für den Teil "Isolation per Checkout und Harness-Config".
- Akzeptanz: Tabelle vollständig mit je einem Beleg oder dem Vermerk "nicht belegt"; Entscheidung 20 (A-N1) liegt vor.

### Task 3b: #547 schließen und Follow-up-Issue anlegen (Entscheidung 20)

**Rolle:** `developer`. **Hängt ab von:** Task 3a, Entscheidung 20 (A-N1, Option b), Freigabe der Phase-A-Ausführung.
**Files:** Create `.tmp/phase-a/comments/547.md`, `.tmp/phase-a/comments/547-followup.md` (Vorlage, vorab).

Kommentartext `.tmp/phase-a/comments/547.md`:
```markdown
Geprüft gegen origin/main 9aa0e0c0. Der RFC ist im Kern umgesetzt, fünf Punkte sind bewusst offen.

Umgesetzt:
- Getrennte Checkouts je Harness statt Worktrees, mit Begründung: `docs/guides/cross-harness-dev-isolation.md:14-41`.
- Harness-Abstraktion `config/harnesses/claude.yaml`, `opencode.yaml`, `third.yaml`; sync.py schreibt nur in den eigenen Checkout (Guide Zeilen 3-5, 162-167).

Bewusst offen (Guide Zeilen 171-199, "Open points / Follow-ups"):
1. Strategy B (Runtime-Verlinkung der Checkouts): braucht eine eigene RFC-Runde.
2. Auswahl des dritten Harness: kein Mechanismus, wie ein Tool den Slot `third.yaml` belegt.
3. Task-Partitionierung je Harness: `default-providers` ist nur ein Hinweis.
4. Branch-Purge gemergter lokaler Branches: Umsetzung läuft in #946.
5. Per-Harness- vs. zentrales Config-Verzeichnis: offene RFC-Frage.

Schließe als erledigt; die fünf offenen Punkte sind im Follow-up-Issue #<FU> erfasst (Guide `:171-199` bleibt Quelle).
```
A-Q1 ist durch Entscheidung 39 beantwortet: alle fünf Guide-Punkte (`:176-199`, gegen den Guide geprüft) gehen ins Follow-up-Issue, auch Punkt 4 (Branch-Purge, Querverweis #946) und Punkt 5.
- [ ] Step 1 (vorab, ohne Anlage, schreibt nur nach `.tmp/`): Datei `.tmp/phase-a/comments/547-followup.md` mit folgendem Text anlegen:
  ```markdown
  Follow-up zu #547 (RFC "Cross-Harness-Dev-Isolation", Teil "Isolation per Checkout und Harness-Config" ist umgesetzt).

  Offene Punkte laut `docs/guides/cross-harness-dev-isolation.md:171-199` (Stand origin/main 9aa0e0c0):
  1. Strategy B (Runtime-Verlinkung der Checkouts): braucht eine eigene RFC-Runde (Guide `:176-182`).
  2. Auswahl des dritten Harness: kein Mechanismus, wie ein Tool den Slot `config/harnesses/third.yaml` belegt (Guide `:183-185`).
  3. Task-Partitionierung je Harness: `default-providers` ist nur ein Hinweis (Guide `:186-189`).
  4. Branch-Purge gemergter lokaler `agent/*`- und `feat/*`-Branches: sichere, dokumentierte Routine; Umsetzung läuft in #946 (Guide `:190-194`).
  5. Per-Harness- vs. zentrales Config-Verzeichnis: offene RFC-Frage, Config-Drift vs. Single Source of Truth (Guide `:195-199`).

  Ziel: je Punkt eine Entscheidung oder ein eigenes Issue. Herkunft: Schließung von #547 (Entscheidungen 20 und 39).
  ```
- [ ] Step 2 (erst nach Freigabe der Phase-A-Ausführung): Follow-up-Issue anlegen: `$GH issue create --title "design: harness follow-ups (strategy B, third harness, partitioning, purge, config dir)" --body-file .tmp/phase-a/comments/547-followup.md`. Ausgegebene Nummer notieren als `<FU>`.
- [ ] Step 3: Platzhalter `#<FU>` in `.tmp/phase-a/comments/547.md` durch die Nummer aus Step 2 ersetzen, dann `$GH issue comment 547 --body-file .tmp/phase-a/comments/547.md`.
- [ ] Step 4: `$GH issue close 547 --reason completed`.
- [ ] Step 5: `$GH issue view 547 --json state,stateReason -q '.state + " " + .stateReason'` — Erwartung: `CLOSED COMPLETED`. `$GH issue view <FU> --json state -q .state` — Erwartung: `OPEN`.
- Akzeptanz: #547 `CLOSED`; Follow-up-Issue `OPEN` und im Kommentar verlinkt; Kommentar sichtbar (`$GH issue view 547 --comments | tail -20`). Anlage und Schließung ohne Freigabe der Ausführung: nicht zulässig.

### Task 4a: Evidenz-Check #1007 (read-only, die 7 Punkte einzeln)

**Rolle:** `developer`. **Hängt ab von:** Task 1.
**Files:** keine. **Interfaces:** Produces: Tabelle der 7 "zu bauen"-Punkte gegen PRs #1012, #1016, #1017, #1018, #1019; Eingabe für Entscheidung 21 (A-N2).

Die sieben Punkte stammen aus Abschnitt "3. What has to be built" des Issues. Befund in `W`:

| # | Punkt (Issue) | PR laut PR-Text | Befund im Code | Verdikt |
|---|---|---|---|---|
| 1 | `experimental.subagent_depth` auf v2 | #1012 | `scripts/lib/opencode_v2_config.py:504-513` schreibt `managed["experimental.subagent_depth"]`; `docs/providers/opencode.md:58,90,109` | erfüllt |
| 2 | `experimental.todo: true` auf v2, wenn eine Rolle `todowrite` deklariert | #1012 | `scripts/lib/opencode_v2_config.py:515-517` schreibt den Key **nur bei explizit gesetzter Projekt-Option** `experimental-todo`; `docs/providers/opencode.md:91,110` ("ohne Key wird nichts geschrieben"). Keine Ableitung aus `todowrite` | **Abweichung** (Option statt Auto-Ableitung), bewusst laut Entscheidung 21 |
| 3 | Native `permissions[]` mit `shell`/`subagent`/`edit` auf v2 | #1016, #1018 | `scripts/lib/provider_transform.py:968` `map_tools_to_opencode_v2_permissions`; `scripts/lib/isolation.py:1290` `permission_deny_required`, `:1915` `reconcile_opencode_surface_gate` (Stand `9aa0e0c0`; in `a3d65da4` noch `:1242`/`:1751`); `docs/providers/opencode.md:59` | erfüllt |
| 4 | `mcp.servers.<name>.disabled` statt `enabled` | #1016 | `scripts/lib/mcp_provider_config.py:278-281` (v2 ohne `enabled`, `disabled` nur bei `True`); `docs/providers/opencode.md:60` | erfüllt |
| 5 | `$schema`/`plugins`/`skills` auf v2 | #1012, #1017 | `plugins`: `docs/providers/opencode.md:57` und #1017. `$schema`: bewusst **nicht** emittiert, `scripts/lib/opencode_v2_config.py:494` ("v2 has no published schema; AC-B11"). Flache `skills`-Liste: kein Beleg gefunden | **Abweichung** (`$schema`, bewusst laut Entscheidung 21) und **Abweichung** (flache `skills`-Liste nicht umgesetzt, bewusst laut Entscheidung 21; Code-Beleg fehlt) |
| 6 | V2-Verifikationsszenario und Lab-Diff v1 gegen v2 | #1012, #1018 | `tests/scenarios/asserts/69-opencode-v2-surface.sh`, `tests/scenarios/asserts/79-opencode-v2-full-surface.sh`, `tests/scenarios/configs/69-opencode-v2-surface.project.yaml`, `tests/scenarios/configs/79-opencode-v2-full-surface.project.yaml` existieren; Lab-Diff nur laut PR-Text #1018 (Task 29) | erfüllt (Lab-Diff nur PR-Text) |
| 7 | Migrationshinweis (opt-in per `surface-version`; bestehende `opencode.json` wird nicht umgeformt) | #1018 | Opt-in dokumentiert: `docs/providers/opencode.md:49,71-84`. Die im Issue genannte Falle "INIT-only shaping" ist durch den Managed-Merge `sync_opencode_v2_managed_keys` (`scripts/lib/opencode_v2_config.py:680`) und `docs/providers/opencode.md:105-137` behoben | erfüllt (anders gelöst) |

Zusatzbefunde des Issues (Abschnitt 4): "INIT-only shaping" gelöst durch Managed-Merge (Punkt 7); "`surface-version` nicht auffindbar" gelöst durch `docs/providers/opencode.md:71-80` (Schalter in `provider-options.Opencode`). Einstiegspunkt "v1 broken": `scripts/lib/provider_transform.py:483-488` setzt `mode: primary` bei explizitem `primary-role` auf v1 und v2; die Positionsfrage gehört zu #1190 (PR #1218, laut Basischeck in `origin/main 9aa0e0c0` gemergt).

- [ ] Step 1: Punkt 5 nachprüfen: `grep -n "skills" scripts/lib/opencode_v2_config.py scripts/lib/provider_transform.py | grep -i "flat\|array\|list"` — Erwartung: Treffer oder keiner. Kein Treffer ⇒ Punkt 5 bleibt "flache `skills`-Liste nicht umgesetzt" (bewusste Abweichung laut Entscheidung 21, kein Code-Beleg). Treffer ⇒ Befund und Kommentar vor dem Posten neu bewerten.
- [ ] Step 2: Lab-Diff prüfen: `git show --stat 97b4e49f` (Squash-Commit von #1018, Subject "feat(opencode): native v2 agents, cli.json, docs and assurance tests (phase D, #1007) (#1018)") und `grep -rn "lab" tests/scenarios/asserts/79-opencode-v2-full-surface.sh` — Erwartung: Hinweis auf v1/v2-Diff. Kein Beleg ⇒ Punkt 6 "nur PR-Text".
- [ ] Step 3: Tests laufen lassen: `python3 -m pytest tests/test_opencode_v2_surface.py -q` — Erwartung: grün (Plan-Wert; PR-Text #1018: 130 passed bei Release; Review 2026-11-11: `--collect-only` sammelt 132 Tests, nicht ausgeführt). Rot ⇒ nicht schließen.
- Akzeptanz: 7 Zeilen mit Beleg oder "nicht belegt"; Entscheidung 21 (A-N2) liegt vor.

### Task 4b: #1007 schließen (Entscheidung 21)

**Rolle:** `developer`. **Hängt ab von:** Task 4a, Entscheidung 21 (A-N2, Option a), Freigabe der Phase-A-Ausführung.
**Files:** Create `.tmp/phase-a/comments/1007.md`.

Kommentartext `.tmp/phase-a/comments/1007.md` (Punkte 5 und 6 vor dem Posten an das Ergebnis von Task 4a Step 1/2 anpassen):
```markdown
Geprüft gegen origin/main 9aa0e0c0, Punkt für Punkt gegen PRs #1012, #1016, #1017, #1018, #1019.

Erfüllt:
1. `experimental.subagent_depth`: `scripts/lib/opencode_v2_config.py:504-513` (#1012).
3. Native `permissions[]`: `scripts/lib/provider_transform.py:968`, `scripts/lib/isolation.py:1290,1915` (#1016, #1018).
4. `mcp.servers.<name>.disabled`: `scripts/lib/mcp_provider_config.py:278-281` (#1016).
6. Szenarien `tests/scenarios/asserts/69-opencode-v2-surface.sh` und `79-opencode-v2-full-surface.sh`.
7. Migrations- und Opt-in-Doku: `docs/providers/opencode.md:49,71-137`. Die "INIT-only"-Falle ist durch den Managed-Merge `sync_opencode_v2_managed_keys` (`opencode_v2_config.py:680`) behoben.

Bewusste Abweichungen vom Issue-Text:
2. `experimental.todo` wird nur bei gesetzter Projekt-Option `experimental-todo` geschrieben, nicht aus `todowrite` abgeleitet (`opencode_v2_config.py:515-517`). Bewusste Abweichung.
5. `$schema` wird bewusst nicht emittiert, da v2 kein veröffentlichtes Schema hat (`opencode_v2_config.py:494`, AC-B11). Eine flache `skills`-Liste ist nicht umgesetzt. Beide Abweichungen sind bewusst.

Release: 2.0.0-beta.3 (#1019). Schließe als erledigt.
```
- [ ] Step 1: `$GH issue comment 1007 --body-file .tmp/phase-a/comments/1007.md`
- [ ] Step 2: `$GH issue close 1007 --reason completed`
- [ ] Step 3: `$GH issue view 1007 --json state,stateReason -q '.state + " " + .stateReason'` — Erwartung `CLOSED COMPLETED`.
- Akzeptanz: Zustand `CLOSED`, Evidenz-Kommentar sichtbar. Entscheidung 21 gedeckt, kein Entfall.

### Task 5: Evidenz-Checks der Schließkandidaten #857, #858, #1116, #1151, #1150 (read-only)

**Rolle:** `developer`. **Hängt ab von:** Task 1. **Files:** keine. **Interfaces:** Produces: je Issue ein Gate "bestanden/nicht bestanden" für Task 6.

- [ ] Step 1 (#857, Mammouth): Belege in `W`: `config/ai-providers.yaml:645-647` (Capabilities `skills`, `mcp`), `:659-669` (`mcp-config: committed-file: mammouth.json, secrets-file: .mammouth/mcp.local.json, format: opencode-json`), `:670` (`skills_dir: .mammouth/skills`). Gate-Befehl: `python3 -m pytest tests -k "mammouth and (mcp or skill)" -q` — Erwartung: mindestens 1 Test grün (Review 2026-11-11: `--collect-only` wählt 9 Tests, nicht ausgeführt). 0 gesammelt oder rot ⇒ #857 nicht schließen. Die Hashes `f55601ba` (#904) und `89cc6381` (#994) mit `git show --stat <hash>` bestätigen. Rest der Frage "emittiert `.mammouth/skills/` Dateien": #994 Task 1.22 (`.tmp/issues/994.md`, "Lazy rule skills written for every skills channel") ist der Beleg; nicht selbst ausgeführt.
- [ ] Step 2 (#858, Codex/Continue): Belege: `config/ai-providers.yaml:474` (`native-skill-channel` für Continue), `:770` (`skills_dir: .agents/skills` für Codex), `config/provider-capabilities.yaml:528-529` (`rules_read_channels: [embedded, skills]`, `skills_discovery_dirs: [".agents/skills"]`). Gate-Befehl: `python3 -m pytest tests -k "native_skill or skills_channel or rule_channels" -q` — Erwartung: mindestens 1 Test grün (Review 2026-11-11: `--collect-only` wählt 63 Tests, nicht ausgeführt). Hinweis aus #994: `declared-surface-empty` bleibt WARN (`.tmp/issues/994.md`, Entscheidung 2); der Kommentar nennt das als Restpunkt.
- [ ] Step 3 (#1116): Belege (verifiziert in `W`): `tests/test_orchestrator_guard_hook.py:59-63` (`_HANG_GUARD_SECONDS = 40.0`, Kommentar "NOT a performance assertion"), `:1863` Test `test_fork_bomb_scan_does_not_hang_on_a_300kb_command`, `:1876-1878` Assertion `elapsed < _HANG_GUARD_SECONDS`; `tests/test_hook_common_lib.py:36` (`_HANG_GUARD_SECONDS = 40.0`), `:541-543` (`elapsed_ms < _HANG_GUARD_SECONDS * 1000.0`). Gate-Befehl: `python3 -m pytest tests/test_orchestrator_guard_hook.py::test_fork_bomb_scan_does_not_hang_on_a_300kb_command tests/test_hook_common_lib.py::test_fork_bomb_detection_is_linear_on_a_300kb_identifier -q` — Erwartung `2 passed`. Offen laut Akzeptanzkriterien des Issues: Mutationsbeweis (Detektor in Endlosschleife) und `-n 2`-Lauf. Review 2026-11-11: `git show fa37d7d0 --stat --format=%B` enthält dazu **keine** Aussage (Body: "Finding B (wall-clock) ... raise them to a generous 40 s"; 3 Testdateien); der Kommentar nennt daher nur das Belegte.
- [ ] Step 4 (#1151): Belege (verifiziert in `W`): F6-01 `hooks/1-generic/orchestrator-guard-impl.sh:28-29,290-294` und `hooks/1-generic/repo-containment-impl.sh:233-240` (NotebookEdit/MultiEdit zählen als Edit, PowerShell als Bash); F6-02 `hooks/1-generic/lib/hook_common.sh:178-183` (Allowlist um `LSP`, `PowerShell`, `EndConversation`, `ListAgents`, `ListMcpResourcesTool`, `ReadMcpResourceTool` ergänzt); F6-03 Testfälle mit Kommentar "(#1151 F6-03)" in `tests/test_hook_common_lib.py:493-498`. F6-04..F6-13 stützen sich auf den PR-Text von #1153 (`.tmp/issues/1153.md`), nicht auf eigene Codelektüre. Gate-Befehl: `python3 -m pytest tests/test_hook_notebook_multiedit.py tests/test_hook_smoke_optin.py tests/test_hook_common_lib.py -q` — Erwartung grün (alle drei Dateien in `origin/main` vorhanden; `--collect-only`: 14 + 4 + 164 Tests, nicht ausgeführt). Explizit nicht Teil von #1151 (Non-Goals im Issue): Indirektion (#592) und Hook-Latenz F6-11 (offen in #1169).
- [ ] Step 5 (#1150, Duplikat von #1186): Abdeckung der vier Akzeptanzkriterien von #1150 durch #1186 prüfen: Matrix und Default-Werte, Rollen referenzieren generierte Variablen, Konsistenzprüfung ("technical enforcement (hook blocks + consistency check warns)"), Promotion/Retention (`.tmp/issues/1186.md`, Summary). Der Owner-Kommentar vom 2026-11-08 in #1150 sagt, das Issue "stays valid as the problem statement" und der Mechanismus liege in #1186; Schließen als Duplikat ist damit stimmig. #1186 ist `TEILWEISE` (Spec und Plan APPROVED, PR #1212, kein Code); Umsetzung in Phase E laut Entscheidung 19. Gate: `$GH issue view 1186 --json state -q .state` — Erwartung `OPEN` (Ziel des Verweises muss offen sein).
- Akzeptanz: je Issue ein protokolliertes Gate-Ergebnis; schlägt ein Gate fehl, wird das Issue aus Task 6 gestrichen und im Ausführungsprotokoll begründet.

### Task 6: Evidenz-Kommentare schreiben und #857, #858, #1116, #1151, #1150 schließen

**Rolle:** `developer`. **Hängt ab von:** Task 5 (je Issue sein Gate), Freigabe.
**Files:** Create `.tmp/phase-a/comments/857.md`, `858.md`, `1116.md`, `1151.md`, `1150.md`.

`.tmp/phase-a/comments/857.md`:
```markdown
Geprüft gegen origin/main 9aa0e0c0. Behoben durch PR #904 (`f55601ba`, Titel "provider model-ID prefix, settings file, mcp config (#852, #853, #857)") und PR #994 (`89cc6381`).

Beleg in `config/ai-providers.yaml` (Mammouth):
- Zeilen 645-647: Capabilities `skills` und `mcp` deklariert.
- Zeilen 659-669: echte MCP-Oberfläche (`mcp-config`: `committed-file: mammouth.json`, `secrets-file: .mammouth/mcp.local.json`, `format: opencode-json`).
- Zeile 670: `skills_dir: .mammouth/skills`; Lazy-Skills für jeden Skills-Kanal laut PR #994 (Task 1.22).

Deklarierte und emittierte Oberfläche stimmen überein. Schließe als erledigt.
```
`.tmp/phase-a/comments/858.md`:
```markdown
Geprüft gegen origin/main 9aa0e0c0. Behoben durch PR #994 (`89cc6381`, Task 1.22: Lazy-Rule-Skills für jeden Skills-Kanal, Continue erhält `native-skill-channel`).

Beleg:
- Continue: `config/ai-providers.yaml:474` (`native-skill-channel`), `skills_dir: .continue/skills` (Zeile 495).
- Codex: `config/ai-providers.yaml:770` (`skills_dir: .agents/skills`); `config/provider-capabilities.yaml:528-529` (`rules_read_channels: [embedded, skills]`, `skills_discovery_dirs: [".agents/skills"]`).

Restpunkt, nicht Teil dieses Issues: der Check `declared-surface-empty` bleibt WARN (Entscheidung 2 in PR #994). Schließe als erledigt.
```
`.tmp/phase-a/comments/1116.md`:
```markdown
Geprüft gegen origin/main 9aa0e0c0. Behoben durch `fa37d7d0`.

Beleg:
- `tests/test_orchestrator_guard_hook.py:59-63`: `_HANG_GUARD_SECONDS = 40.0`, Kommentar nennt es einen Hang Guard und keine Performance-Assertion; Assertion in `:1876-1878` (`elapsed < _HANG_GUARD_SECONDS`).
- `tests/test_hook_common_lib.py:36` und `:541-543`: dieselbe Grenze (40 s, in ms umgerechnet).

Die engen Grenzen (5 s, 100 ms) sind durch eine Hang-Grenze ersetzt, der Docstring benennt den Zweck. Schließe als erledigt.
```
Keine Ergänzung zu Mutationsbeweis/`-n 2`: `fa37d7d0` belegt beides nicht (Task 5 Step 3).
`.tmp/phase-a/comments/1151.md`:
```markdown
Geprüft gegen origin/main 9aa0e0c0. Behoben durch PR #1153 (`c1e810c6`, `283fcd3c`).

In `W` selbst nachgelesen:
- F6-01: `hooks/1-generic/orchestrator-guard-impl.sh:28-29,290-294` und `hooks/1-generic/repo-containment-impl.sh:233-240` fangen NotebookEdit/MultiEdit als Edit und PowerShell als Bash ab.
- F6-02: `hooks/1-generic/lib/hook_common.sh:178-183` kennt jetzt `LSP`, `PowerShell`, `EndConversation`, `ListAgents`, `ListMcpResourcesTool`, `ReadMcpResourceTool`.
- F6-03: Testfälle für Command-Substitution und Backticks in `tests/test_hook_common_lib.py:493-498`.

F6-04..F6-13 laut PR #1153 (Test-Evidenz dort: Guard und DoD 1120 passed, Gruppe 1692 passed); dort nicht selbst nachgelesen.
Bewusst nicht Teil dieses Issues: Indirektion (#592) und Hook-Latenz F6-11 (offen in #1169). Schließe als erledigt.
```
`.tmp/phase-a/comments/1150.md`:
```markdown
Duplikat von #1186. Dieses Issue beschreibt das Problem (keine verbindliche Zuordnung Artefakttyp zu Ablageort); der Mechanismus `artifact-locations` mit Pfad und Modus je Klasse steht in #1186, Spec und Plan APPROVED (PR #1212). Die hier vorgeschlagene Matrix wird dort zu den Default-Werten (siehe Kommentar vom 2026-11-08). Weiterverfolgung in #1186.
```
- [ ] Step 1: Die fünf Dateien mit dem Write-Werkzeug anlegen (Text oben, nach Gate-Ergebnis aus Task 5 angepasst).
- [ ] Step 2: Je Issue N in {857, 858, 1116, 1151}: `$GH issue comment N --body-file .tmp/phase-a/comments/N.md` und `$GH issue close N --reason completed`.
- [ ] Step 3: #1150: `$GH issue comment 1150 --body-file .tmp/phase-a/comments/1150.md` und `$GH issue close 1150 --reason "not planned"`.
- [ ] Step 4: Nachprüfung: `for n in 857 858 1116 1151 1150; do $GH issue view $n --json number,state,stateReason -q '"\(.number) \(.state) \(.stateReason)"'; done` — Erwartung: alle `CLOSED`, #1150 mit `NOT_PLANNED`, die übrigen `COMPLETED`.
- Akzeptanz: 5 Issues `CLOSED`, je ein Kommentar mit Dateipfad und Zeilenangabe oder PR-Verweis sichtbar.

### Task 7: Marker-PR mergen (Voraussetzung für Task 8)

**Rolle:** `git` (Push, PR, Merge), Review durch `code-reviewer`. **Hängt ab von:** Task 2.
**Files:** keine.

- [x] Step 1: Branch `fix/phase-a-pytest-split-marker` pushen und PR gegen `main` öffnen, Text `--body-file .tmp/phase-a/pr-body-marker.md` (ohne `Closes`/`Fixes`/`Resolves`, Entscheidung 38e); Titel = Commit-Subject aus Task 2.
- [ ] Step 2: CI abwarten: `$GH pr checks <PR> --watch` — Erwartung: `test (3.9)` und `test (3.12)` grün, kein Admin-Bypass.
- [x] Step 3: Squash-Merge durch `git`-Rolle nach Freigabe: `$GH pr merge <PR> --squash`.
- Akzeptanz: PR `MERGED`; `git show origin/main:tests/requirements.txt` enthält die zwei Marker-Zeilen.

### Task 8: Dependabot-PRs #1145 und #1148 schließen

**Rolle:** `developer`. **Hängt ab von:** Task 7 (Marker auf `main`).
**Files:** Create `.tmp/phase-a/comments/1145.md`.

Kommentartext `.tmp/phase-a/comments/1145.md` (identisch für #1148, Verweis auf den jeweils anderen PR):
```markdown
Ersetzt durch den Marker-Fix auf main (PR <Marker-PR>): `tests/requirements.txt` trennt `pytest-split` nach Python-Version (`>=0.8` unter 3.10, `>=0.11.0` ab 3.10). pytest-split 0.11.0 entfernt Python 3.9; die 3.9-Jobs der CI-Matrix (`.github/workflows/orchestration-test.yml:210,392`) können `>=0.11.0` ohne Marker nicht auflösen. Duplikat von #1148 beziehungsweise #1145. Schließe ohne Merge.
```
- [ ] Step 1: Vorprüfung: `$GH pr view 1145 --json files -q '.files[].path'` und dasselbe für 1148 — Erwartung: nur `tests/requirements.txt` (Review 2026-11-11 read-only: beide `OPEN`, je nur `tests/requirements.txt`, Diff `-pytest-split>=0.8` / `+pytest-split>=0.11.0`). Andere Datei ⇒ nicht schließen, Befund melden.
- [ ] Step 2: `$GH pr comment 1145 --body-file .tmp/phase-a/comments/1145.md` und `$GH pr close 1145`; dasselbe für `1148`.
- [ ] Step 3: Nachprüfung: `for n in 1145 1148; do $GH pr view $n --json number,state -q '"\(.number) \(.state)"'; done` — Erwartung `CLOSED`.
- Akzeptanz: beide PRs `CLOSED` (nicht `MERGED`). Risiko: Dependabot kann beim nächsten Wochenlauf einen neuen PR für die Marker-Zeile eröffnen; dann prüfen, ob er den Marker erhält.

### Task 9: #1190 Prüfung und Beleg-Nachtrag (Entscheidung 38f)

**Rolle:** `developer` (read-only Prüfung; Kommentar erst nach Freigabe). Kein `git`-Schritt, kein Schließen, kein Wiederöffnen. **Hängt ab von:** Freigabe der Phase-A-Ausführung (nur für Step 3).
**Files:** Create `.tmp/phase-a/comments/1190.md` (Text unten).

Stand (read-only per `gh` verifiziert, Entscheidung 38f): PR #1218 `MERGED` (mergedAt 2026-11-11T06:41:30Z, mergeCommit `9aa0e0c0c45b08363a8bf75a88600d863d3e5172`). Issue #1190 `CLOSED` durch Auto-Close (closedAt 2026-11-11T06:41:32Z, stateReason `COMPLETED`, keine Kommentare). Die Schließregel (Entscheidung 38e) verlangt einen Evidenz-Kommentar; der wird hier **nachträglich** gesetzt, nicht als neues Schließen. Der frühere Stand (OPEN, 104 Dateien, `test 3.12` Shard 2 rot) ist überholt. Alle anderen Tasks laufen unabhängig.

- [ ] Step 1: `$GH pr view 1218 --json state,mergedAt,mergeCommit -q '.state + " " + .mergedAt + " " + .mergeCommit.oid'` — Erwartung `MERGED 2026-11-11T06:41:30Z 9aa0e0c0c45b08363a8bf75a88600d863d3e5172`. Abweichung ⇒ Task stoppt und meldet.
- [ ] Step 2: Zustand am Tag der Ausführung neu lesen (nicht aus diesem Plan übernehmen):
  `$GH issue view 1190 --json state,closedAt,stateReason,comments`
  Erwartung: `state` `CLOSED`, `closedAt` `2026-11-11T06:41:32Z`, `stateReason` `COMPLETED`. Enthält `comments` bereits einen Beleg-Kommentar ⇒ Step 3 entfällt, Befund melden. `OPEN` ⇒ Abweichung melden; kein Schließen und kein Öffnen ohne neue Freigabe des Users.
- [ ] Step 3 (erst nach Freigabe der Phase-A-Ausführung, nur wenn Step 2 keinen Beleg zeigt): Kommentar `.tmp/phase-a/comments/1190.md`:
  ```markdown
  Nachtrag zum automatischen Schließen am 2026-11-11T06:41:32Z durch den Merge von PR #1218 (mergeCommit 9aa0e0c0c45b08363a8bf75a88600d863d3e5172, 2026-11-11T06:41:30Z). Das Auto-Close erfolgte ohne Evidenz-Kommentar; dieser Kommentar ist der nachträgliche Beleg.

  Entschieden und umgesetzt in PR #1218: 24-Zellen-Entscheidungsmatrix, ADR 0002, Positionsmodell POS-1/POS-2/POS-3, `scripts/lib/topology.py`, drei neue Diagnosen. Die Akzeptanzkriterien dieses Issues (Matrix, Empfehlung, Follow-up-Artefakte, Doku in `docs/concepts/active/orchestrator-topology.md`) sind dort erfüllt. Das Issue bleibt geschlossen.
  ```
  Befehl: `$GH issue comment 1190 --body-file .tmp/phase-a/comments/1190.md`.
  **Nicht** ausführen: `$GH issue close 1190` und jede Form des Wiederöffnens (`$GH issue reopen 1190`, `$GH issue edit 1190 --state open`).
- [ ] Step 4: Vor Step 3 prüfen, dass die genannten Artefakte auf `main` liegen (Git-Lesezugriff über den `git`-Subagenten): `ls docs/adr | grep 0002` — Erwartung: ADR 0002 vorhanden. Fehlt sie, den Kommentar nicht posten und den Befund melden.
- [ ] Step 5: Nachprüfung: `$GH issue view 1190 --json state,stateReason,comments -q '.state + " " + .stateReason + " " + (.comments|length|tostring)'` — Erwartung `CLOSED COMPLETED 1` (ein Beleg-Kommentar).
- Akzeptanz: #1190 bleibt `CLOSED` (ohne zusätzliches Schließen, ohne Wiederöffnen), genau ein Beleg-Kommentar sichtbar, Kommentar erst nach Freigabe.

### Task 10: #946 Branch/Stash-Tabelle (Entscheidung 12)

**Rolle:** `git` (Erhebung und Sicherung, Git-Lesezugriffe), `developer` (Tabelle). **Hängt ab von:** Task 1. **Löschung** hängt zusätzlich an der Freigabe der Tabelle durch den User.
**Files:** Create `.tmp/phase-a/946-stash-838.patch`, `.tmp/phase-a/946-branch-table.md`, `.tmp/phase-a/946-delete-commands.sh` (nur Textvorlage für den User, wird nie ausgeführt).

Ausgangsstand (Review 2026-11-11 read-only im Haupt-Checkout erhoben, `FETCH_HEAD` vom 2026-11-11 14:59; am Ausführungstag mit Step 3/4 neu erheben): 18 Zweifelsbranches auf origin plus 1 nur lokaler Branch (`fix/sync-check-tracked-only`, 1 Commit `35f591e6`, kein Remote), 9 Stash-Einträge (Issue nennt 7), `docs/838-spec-revision` nur noch im Stash (`stash@{2}`). Zusätzlich trägt der lokale Branch `feat/repository-documentation-consolidation` einen nicht gepushten Commit `90be1146` (`git rev-list --count origin/<b>..<b>` = 1); er muss mit ins Bundle. Kein Branch hat `git cherry`-Anzahl 0; die Regel "Löschen" in Step 5 greift damit für keinen Branch (squash-gemergte Inhalte erkennt `git cherry` nicht).

- [ ] Step 1: **Stash `docs/838-spec-revision` sichern (vor allem anderen).** Index bestimmen: `git stash list | grep -n "838"` — Erwartung: ein Eintrag `stash@{N}`. Dann (alles lesend, schreibt nur nach `.tmp/`):
  `git diff stash@{N}^1 stash@{N} > .tmp/phase-a/946-stash-838.patch`
  `git rev-parse --verify --quiet stash@{N}^3 && git diff 4b825dc642cb6eb9a060e54bf8d69288fbee4904 stash@{N}^3 > .tmp/phase-a/946-stash-838-untracked.patch`
  `sha256sum .tmp/phase-a/946-stash-838*.patch > .tmp/phase-a/946-stash-838.sha256`
  `git apply --stat .tmp/phase-a/946-stash-838.patch` — Erwartung: Dateiliste mit Zeilenzahlen, exit 0. Dateigröße 0 oder Fehler ⇒ **Abbruch, kein Löschen**; alternativ den Stash als Datei per `git stash show -p --include-untracked stash@{N}` sichern.
- [ ] Step 2: Alle 18+1 Branches sichern, bevor etwas gelöscht wird (das Archiv `.tmp/cleanup-archive` ist weg): `git bundle create .tmp/phase-a/946-doubt-branches.bundle <jede origin/Branch-Referenz der Tabelle> fix/sync-check-tracked-only feat/repository-documentation-consolidation` (lokale Refs mit ungepushten Commits, hier `90be1146`) und `git bundle verify .tmp/phase-a/946-doubt-branches.bundle` — Erwartung: `is okay`.
- [ ] Step 3: Stash-Liste erheben: `git stash list --format='%gd | %cs | %s'` — Erwartung: 9 Zeilen mit numerischem Index (`--date=short` würde `%gd` als `stash@{<datum>}` ausgeben und den Index verlieren; Review 2026-11-11 gemessen). Die zwei im Issue nicht genannten Einträge in der Tabelle als "nicht im Issue" markieren.
- [ ] Step 4: Branch-Daten erheben, je Branch `<b>` (alle lesend): letzter Commit `git log -1 --format='%h %cd %s' --date=short origin/<b>`; Remote ja/nein `git branch -r --list origin/<b>`; Commits vor main `git rev-list --count origin/main..origin/<b>`; patch-äquivalent `git cherry origin/main origin/<b> | grep -c '^+'` (Anzahl nicht in main enthaltener Commits); für nur lokale Branches `<b>` statt `origin/<b>`; ungepushte lokale Commits `git rev-list --count origin/<b>..<b>`.
- [ ] Step 5: Tabelle `.tmp/phase-a/946-branch-table.md` schreiben. Regel für die Spalte "Vorschlag": `git cherry` zeigt 0 Zeilen mit `+` ⇒ **Löschen** (Inhalt in main); ≥1 Zeile mit `+` und das Issue nennt "echte ungemergte Arbeit" ⇒ **PR** oder **behalten**; ≥1 Zeile mit `+` und "Inhalt nicht in main belegt" ⇒ **User-Entscheidung** (mit Diff-Größe in der Begründung). Die Vorschläge unten sind **vorläufig** und stützen sich auf den Issue-Text; die Spalten "letzter Commit", "Remote" und "vor main / cherry+" sind read-only am 2026-11-11 gemessen (Haupt-Checkout, `origin/main 9aa0e0c0`) und am Ausführungstag mit Step 4 zu bestätigen.

| Name | Letzter Commit | Remote | vor main / cherry+ | Vorschlag (vorläufig) | Begründung (Issue-Text) |
|---|---|---|---|---|---|
| `feat/issue-batch-677-728` | `ea626956` 2026-09-11 | ja (+ lokal, identisch) | 10 / 10 (Issue: 4) | PR | PR #742 gemergt, 4 Commits fehlen in main (Browser-Fixture, Changelog-Dropdowns, Konsistenz-Check, Test); gemessen 10, Differenz in der Tabelle begründen |
| `fix/sync-check-tracked-only` | `35f591e6` 2026-09-17 | **nein** (nur lokal) | 1 / 1 | PR | kein PR, 1 Commit plus Stash; nur lokal, daher Bundle zwingend |
| `feat/repository-documentation-consolidation` | `12c6b8ae` 2026-09-26 (origin); lokal `90be1146`, 1 Commit ungepusht | ja (+ lokal, 1 voraus) | 38 / 38 | behalten | PR #837 geschlossen, pausiert; lokale Ref ins Bundle |
| `feat/repository-documentation-consolidation-main` | `d367a408` 2026-09-29 | ja (+ lokal, identisch) | 59 / 59 | behalten | PR #839 geschlossen |
| `feat/lit-769-core-development` | `886a4d4d` 2026-09-14 | ja | 18 / 18 | User-Entscheidung | SRE/SLO-Referenzen, ASVS-Mapping, Accessibility G1-G3 fehlen in main |
| `feat/lit-770` | `ee5aece4` 2026-09-13 | ja | 6 / 6 | User-Entscheidung | wie oben |
| `feat/lit-773` | `4024ffb2` 2026-09-13 | ja | 1 / 1 | User-Entscheidung | wie oben |
| `feat/lit-774` | `ee43d9a0` 2026-09-13 | ja | 2 / 2 | User-Entscheidung | wie oben |
| `feat/lit-775` | `020c1e7f` 2026-09-13 | ja | 2 / 2 | User-Entscheidung | documenter §6, Link-Rot-Absätze |
| `feat/lit-777` | `33b3ac44` 2026-09-13 | ja | 6 / 6 | User-Entscheidung | 11 `reference_standards`-Absätze |
| `docs/auto-commit-tiers-spec` | `06ab8f29` 2026-09-08 | ja | 2 / 1 | User-Entscheidung (cherry nicht leer) | Plan zu 93,7 % in main, Checkbox-Zeilen umformatiert |
| `feat/model-inherit-main-chat` | `fc809081` 2026-08-22 | ja | 8 / 8 | User-Entscheidung | `inherit_active`-Guard in `scripts/lib/agents.py` nicht in main. Hinweis: ein `inherit_active`-Guard existiert in main unter `scripts/lib/provider_transform.py:662`; Issue-Aussage vor Vorlage per Diff prüfen |
| `docs/integrations-framework-concept` | `91d4f8fb` 2026-06-15 | ja | 2 / 1 | User-Entscheidung | Inhalt nicht in main belegt |
| `docs/readme-architecture-overhaul` | `4a8a5271` 2026-08-25 | ja | 2 / 2 | User-Entscheidung | Inhalt nicht in main belegt |
| `feat/integrations-framework` | `1891052b` 2026-06-15 | ja | 2 / 2 | User-Entscheidung | Inhalt nicht in main belegt |
| `feat/knowledge-engine-phase-b` | `54acd544` 2026-07-23 | ja | 2 / 1 | User-Entscheidung | Inhalt nicht in main belegt |
| `feat/platform-defaults` | `5cd2150a` 2026-08-25 | ja | 2 / 2 | User-Entscheidung | Inhalt nicht in main belegt |
| `fix/bugfix-session-june-2026` | `279423c6` 2026-06-09 | ja | 20 / 20 | User-Entscheidung | Inhalt nicht in main belegt |
| `feat/concept-driven-pipeline` | `d552302b` 2026-07-27 | ja | 2 / 2 | User-Entscheidung | 88 Dateien, 3 % absorbiert; Issue #370 ohne PR geschlossen |

Zählung: 15 Branches der Gruppe "zur Entscheidung" plus 4 Branches der Gruppe "behalten" = 19 Zeilen = 18 auf origin plus 1 nur lokal. Stimmt die erhobene Zahl nicht, ist die Differenz in der Tabelle zu benennen.

Stash-Tabelle (Index und Datum read-only gemessen 2026-11-11 mit `git stash list --format='%gd | %cs | %s'`; Indizes vor Step 7 neu erheben):

| Stash | Index / Datum | Vorschlag (vorläufig) | Begründung |
|---|---|---|---|
| `docs/cleanup-plans-specs-readme` ("handback-fix working tree") | `stash@{0}` 2026-11-05 | User-Entscheidung | **nicht im Issue** |
| `chore/project-yaml-refresh` (WIP auf `8c996398`) | `stash@{1}` 2026-10-31 | User-Entscheidung | **nicht im Issue** |
| `docs/838-spec-revision` | `stash@{2}` 2026-10-06 | **behalten bis Patch gesichert (Step 1), dann User-Entscheidung** | unveröffentlichte Re-Review, laut Issue wertvoll; einziger Träger |
| `fix/sync-check-tracked-only` | `stash@{3}` 2026-09-18 | zusammen mit dem Branch entscheiden | gehört zu Branch `35f591e6` |
| `feat/issue-batch-677-728` | `stash@{4}` 2026-09-11 | zusammen mit dem Branch entscheiden | gehört zu den offenen Commits |
| `feat/plugin-catalog-unification` | `stash@{5}` 2026-09-05 | User-Entscheidung | im Issue ohne Detail |
| `main` (perf cache #656, mit Untracked-Teil) | `stash@{6}` 2026-09-04 | User-Entscheidung | Untracked-Teil per `^3` mitsichern |
| `feat/issue-562-prompt-injection-defense` | `stash@{7}` 2026-08-31 | User-Entscheidung | im Issue als `feat/issue-562-…` abgeschnitten |
| `fix/admin-ui-remote-token` | `stash@{8}` 2026-08-29 | User-Entscheidung | im Issue ohne Detail |

- [ ] Step 6: Tabelle dem User zur Freigabe vorlegen (Entscheidung 12: "Löschung erst nach Freigabe der Tabelle"). Zeile für Zeile: Merge / PR / Löschen / behalten. Ohne Freigabe geschieht nichts.
- [ ] Step 7: Nach Freigabe die Löschbefehle als Datei `.tmp/phase-a/946-delete-commands.sh` bereitstellen und dem User **als fertige `!`-Befehle** geben. **Der Assistent führt sie nicht aus**; blockiert der Guard (exit 2), wird er nicht umgangen. Vorlage (je freigegebene Zeile; Beispiel mit Platzhaltern, die aus der freigegebenen Tabelle ersetzt werden):
  ```text
  ! git push origin --delete <branch>
  ! git branch -D <branch>
  ! git stash drop stash@{N}
  ```
  Reihenfolge: Branches vor Stashes; Stash-Drops in **absteigender** Indexreihenfolge, weil sich Indizes nach jedem Drop verschieben. Den Stash `docs/838-spec-revision` erst nach bestätigtem Patch (Step 1) und `git bundle verify` (Step 2) droppen.
- [ ] Step 8: Nachprüfung: `git branch -r | grep -c <Muster>`, `git stash list | wc -l` — Erwartung: nur freigegebene Einträge fehlen. Kommentar `.tmp/phase-a/comments/946.md` mit der finalen Tabelle als Beleg; #946 erst schließen, wenn jede Zeile eine dokumentierte Entscheidung hat (Akzeptanzkriterium des Issues). Bis dahin bleibt #946 offen.
- Akzeptanz: Patch (nicht leer, `git apply --stat` exit 0) und Bundle (`is okay`) existieren vor jeder Löschung; Tabelle liegt dem User vor; kein Löschbefehl wurde vom Assistenten ausgeführt.

### Task 11: #977 Tracker-Update

**Rolle:** `developer`. **Hängt ab von:** Task 1. **Files:** Create `.tmp/phase-a/977-body.md`, `.tmp/phase-a/comments/977.md`.

Stand laut Roadmap (nicht selbst geprüft): #963-#968 und #970-#976 CLOSED, nur #969 offen, Phasen 2 und 3 ohne Issues.

- [ ] Step 1: Zustand prüfen, Erwartung: 13 Zeilen `CLOSED`, #969 `OPEN`:
  `for n in 963 964 965 966 967 968 969 970 971 972 973 974 975 976; do $GH issue view $n --json number,state -q '"\(.number) \(.state)"'; done`
- [ ] Step 2: Body sichern und anpassen (nur Nummern, die in Step 1 `CLOSED` waren):
  `$GH issue view 977 --json body -q .body > .tmp/phase-a/977-body.orig.md`
  `cp .tmp/phase-a/977-body.orig.md .tmp/phase-a/977-body.md`
  `sed -i -E 's/^- \[ \] #(963|964|965|966|967|968|970|971|972|973|974|975|976)\b/- [x] #\1/' .tmp/phase-a/977-body.md`
  `diff .tmp/phase-a/977-body.orig.md .tmp/phase-a/977-body.md` — Erwartung: genau 13 geänderte Zeilen, `#969` unverändert `[ ]`.
- [ ] Step 3: `$GH issue edit 977 --body-file .tmp/phase-a/977-body.md`
- [ ] Step 4: Kommentar `.tmp/phase-a/comments/977.md`:
  ```markdown
  Tracker-Stand 2026-11-11: Phase 0 (#963-#968) und Phase 1 (#970-#976) sind geschlossen. Offen ist nur #969 (0f: Eval-Korpus, Toleranzmodell, Freigabe-Wrapper; `eval_gate` aus PR #986 gebaut, Baseline-Run nur nach Kostenschätzung und ausdrücklichem User-Ja, McNemar-Schnittstelle in Phase H der Roadmap). Phasen 2 (`meta-optimizer`, Profil `compact`) und 3 (Boilerplate-Deduplizierung, Kimi D-1) haben noch keine Issues. Das Issue bleibt als Tracker offen, bis #969 und die Folgephasen entschieden sind.
  ```
  `$GH issue comment 977 --body-file .tmp/phase-a/comments/977.md`
- [ ] Step 5: Nachprüfung: `$GH issue view 977 --json body -q .body | grep -c '\[x\]'` — Erwartung `13`.
- Akzeptanz: 13 Checkboxen gesetzt, #977 `OPEN`, Kommentar sichtbar.

### Task 12: #885 Tracking-Kommentar (nicht schließen, Entscheidung 13)

**Rolle:** `developer`. **Hängt ab von:** Task 1. **Files:** Create `.tmp/phase-a/comments/885.md`.

Selbst in `W` nachgeprüft: **F-01** `tests/test_no_role_routes_in_templates.py:71-77` (`_SCOPE_GLOBS` enthält `agents/2-platform/*.md` und `rules/2-platform/*.md`); **F-04** `agents/1-generic/backend-reviewer.md:64` ohne `/tmp/opencode`, kein Treffer in `agents/1-generic/`; **F-07** kein `{{ROLE}}` in `agents/`. Laut Roadmap-Sweep, nicht selbst geprüft: F-08 behoben; F-02, F-03, F-05, F-06 offen; F-09..F-16 nicht geprüft; Kinder #932, #933, #934, #935, #936 `CLOSED COMPLETED` (read-only per `gh` gemessen 2026-11-11).

- [ ] Step 1: Kinder prüfen: `for n in 932 933 934 935 936; do $GH issue view $n --json number,state -q '"\(.number) \(.state)"'; done` — Ergebnis in den Kommentar übernehmen.
- [ ] Step 2: F-08 prüfen: `python3 scripts/consistency-check.py --json` — Erwartung: keine `placeholders`-Warnungen für `OUTPUT_GUARD_BLOCK`/`PARSE_INPUT_BLOCK` (beide Namen stehen in der Block-Variablen-Liste `scripts/lib/consistency/placeholders.py:154`). Treffer ⇒ F-08 in die offene Liste verschieben.
- [ ] Step 3: Kommentar `.tmp/phase-a/comments/885.md` (Zeilen an Step 1 und 2 anpassen):
  ```markdown
  Tracking-Stand 2026-11-11 gegen origin/main 9aa0e0c0. Das Epic bleibt offen und wird am Ende der letzten Welle der Backlog-Roadmap geschlossen. Restpunkte werden nicht einzeln neu angelegt.

  Behoben (nachgelesen):
  - F-01: `tests/test_no_role_routes_in_templates.py:71-77`, `_SCOPE_GLOBS` deckt jetzt die Platform-Ebene ab.
  - F-04: kein `/tmp/opencode` mehr in `agents/1-generic/` (z. B. `backend-reviewer.md:64`).
  - F-07: kein `{{ROLE}}` mehr in `agents/`.
  - F-08: laut Sweep behoben (`consistency-check.py` ohne Placeholder-Fehlalarme).

  Offen laut Sweep: F-02, F-03, F-05, F-06. Nicht geprüft: F-09 bis F-16.
  Kinder: #932, #933, #934, #935, #936 geschlossen.
  ```
- [ ] Step 4: `$GH issue comment 885 --body-file .tmp/phase-a/comments/885.md`
- [ ] Step 5: Nachprüfung: `$GH issue view 885 --json state -q .state` — Erwartung `OPEN`. **#885 wird nicht geschlossen.**
- Akzeptanz: Kommentar sichtbar, #885 `OPEN`.

### Task 13: Label `blocked` für #860 und #854

**Rolle:** `developer`. **Hängt ab von:** Task 1. **Files:** keine.

- [ ] Step 1: Existiert das Label nicht (Task 1 Step 4): `$GH label create blocked --color B60205 --description "Blocked by an external dependency or an open decision"`.
- [ ] Step 2: `$GH issue edit 860 --add-label blocked` und `$GH issue edit 854 --add-label blocked`.
- [ ] Step 3: Kommentar `.tmp/phase-a/comments/854.md`:
  ```markdown
  Blockiert durch #860: Der Umzug der Gemini-Commands auf Skills (Entscheidung 10 der Backlog-Roadmap) erfolgt erst nach einer Runtime-Probe, und die ist wegen des `agy`-SIGILL (kein `pclmul`) auf diesem Host nicht möglich. Bis dahin bleibt der Default `agent-discovery: false` (`config/ai-providers.yaml:141-147`). Label `blocked` gesetzt.
  ```
  `$GH issue comment 854 --body-file .tmp/phase-a/comments/854.md`. Für #860 genügt das Label, der Blocker steht bereits in den Owner-Kommentaren vom 2026-10-27 und 2026-10-29.
- [ ] Step 4: Nachprüfung: `for n in 860 854; do $GH issue view $n --json labels -q '"\(.labels|map(.name)|join(","))"'; done` — Erwartung: beide enthalten `blocked`.
- Akzeptanz: beide Issues tragen `blocked`, beide `OPEN`.

### Task 14: Teil-Kommentare zu #1155, #1158, #1159, #1160, #1161

**Rolle:** `developer`. **Hängt ab von:** Task 1. **Files:** Create `.tmp/phase-a/comments/1155.md`, `1158.md`, `1159.md`, `1160.md`, `1161.md`.

Alle Issues bleiben offen. Nur Punkte posten, die die Vorprüfung bestätigt; sonst die Zeile streichen. Eigene Nachprüfung in `W`: **#1155 F2** ist behoben (`scripts/lib/deactivation.py:279` ruft `log.error(str(provider_root), ...)` mit zwei Argumenten auf). **#1160 G4-1** passt zu `config/ai-providers.yaml:141-147` (Kommentar `#1160 (G4-1)`, `agent-discovery: false`, "Default flip deferred until a runtime probe"). Alle anderen Angaben stammen aus dem Roadmap-Sweep und PR-Titeln.

- [ ] Step 1: Vorprüfung #1155: `python3 -m pytest tests -k "deactivation or write_atomic or frontmatter" -q` — Erwartung grün; zusätzlich `scripts/lib/io.py:350` (`def write_atomic(path: Path, content: str, mode: str = "w", *, private: bool = False) -> None`; Issue nennt veraltet `:377`) auf erhaltene Dateimode lesen (F6). Offen laut Roadmap: F5 (Policy: Plain-Sync bleibt exit 0, Entscheidung 4), F10 (`topology-probe.py:232`).
- [ ] Step 2: Vorprüfung #1158/#1159/#1161: `$GH pr view 1163 --json state,mergedAt`, `$GH pr view 1164 --json state,mergedAt` — Erwartung `MERGED`. #1161: Punkte 1 und 3 laut Roadmap gebaut; Beleg selbst suchen (`grep -n "route_intent" scripts/lib/agents.py`; Review 2026-11-11: Treffer u. a. `:35` `ROUTING_TOOL_NAME = "route_intent"`, Zuordnung zu Punkt 1/3 nicht geprüft) oder die Zeile streichen. Anker Punkt 5: `hooks/1-generic/lib/hook_common.sh:63` ist `hook_json_get()` (passt zu #1161/F6-11); `scripts/lib/context.py:204` ist nicht zugeordnet (nicht verifiziert).
- [ ] Step 3: Kommentartexte:
  - `1155.md`: "Teilstand gegen origin/main 9aa0e0c0: F2 behoben (`scripts/lib/deactivation.py:279`, zwei Argumente); F3, F4, F6, F7, F8, F9 laut Sweep gebaut. Offen: F5 (Exit-Code bei `[ERROR]`: Plain-Sync bleibt bewusst exit 0, nur `--strict`/`--fail-on-p0`, Entscheidung 4; Umsetzung in Phase C) und F10 (`topology-probe.py:232`). Issue bleibt offen."
  - `1158.md`: "Teilstand gegen origin/main 9aa0e0c0: K-02..K-06 und K-10 gebaut (PR #1163). K-01 und K-13 nicht verifiziert. Issue bleibt offen, Rest in Phase H."
  - `1159.md`: "Teilstand gegen origin/main 9aa0e0c0: K-08, K-09, K-11, K-14, K-15 und F-OC3 gebaut (PR #1164). Offen: K-12, K-16, K-17, F-PA1; F-PA2 teilweise; F-OC2 nicht verifiziert. Issue bleibt offen, Rest in Phase H."
  - `1160.md`: "Teilstand gegen origin/main 9aa0e0c0: Schritt 1 (Ziel-Plattform dokumentieren) gebaut in PR #1165; `config/ai-providers.yaml:141-147` hält den Default `agent-discovery: false` bis zur Runtime-Probe. Schritte 2 und 3 sind blockiert durch #860 (agy SIGILL). Issue bleibt offen, Phase G."
  - `1161.md`: "Teilstand gegen origin/main 9aa0e0c0: Punkte 1 und 3 gebaut. Offen: Punkte 2, 4, 5 (`context.py:204`, `hook_common.sh:63`; Anker aus dem Sweep, verschoben möglich). Issue bleibt offen, Phase H."
- [ ] Step 4: `for n in 1155 1158 1159 1160 1161; do $GH issue comment $n --body-file .tmp/phase-a/comments/$n.md; done`
- [ ] Step 5: Nachprüfung: `for n in 1155 1158 1159 1160 1161; do $GH issue view $n --json number,state,comments -q '"\(.number) \(.state) \(.comments|length)"'; done` — Erwartung: alle `OPEN`, Kommentarzahl um 1 gestiegen.
- Akzeptanz: 5 Kommentare sichtbar, 5 Issues `OPEN`.

### Task 15: Abschlussverifikation Phase A

**Rolle:** `validator`. **Hängt ab von:** Tasks 2-14 (soweit freigegeben/entschieden).
**Files:** keine.

- [ ] Step 1: Zustandsliste: `for n in 547 857 858 1007 1116 1151 1150 946 885 977 1190; do $GH issue view $n --json number,state,stateReason -q '"\(.number) \(.state) \(.stateReason)"'; done` — Erwartung: #857, #858, #1116, #1151 `CLOSED COMPLETED`; #1150 `CLOSED NOT_PLANNED`; #547 `CLOSED COMPLETED` plus Follow-up-Issue `OPEN` (Entscheidung 20); #1007 `CLOSED COMPLETED` (Entscheidung 21); #1190 `CLOSED COMPLETED` (Auto-Close durch #1218, Beleg-Kommentar aus Task 9 Step 3); #946, #885, #977 `OPEN`.
- [ ] Step 2: `for n in 1218 1145 1148; do $GH pr view $n --json number,state -q '"\(.number) \(.state)"'; done` — Erwartung: #1218 `MERGED` (nicht Aufgabe von Phase A), #1145/#1148 `CLOSED`.
- [ ] Step 3: `python3 -m pytest tests/test_requirements_pytest_split_marker.py -q` — Erwartung `3 passed`; `python3 scripts/sync.py --validate` — Erwartung exit 0.
- [ ] Step 4: Re-Planning: Annahmen prüfen (Abschnitt "Nicht verifiziert"), offene Punkte in die Roadmap (Phase A Detail) zurückmelden. Danach Welle 1 (Phase B) freigeben.
- Akzeptanz: Ergebnisse von Step 1-3 stimmen mit den Erwartungen überein; Abweichungen sind im Protokoll begründet.

## Nicht verifiziert

- Review 2026-11-11 (read-only) hat gemessen: Zustände aller Phase-A-Issues/PRs und der #885-/#977-Kinder per `gh`, Branch-/Stash-Daten (#946), Commit-Hashes, Testsammlung (`--collect-only`), Marker-Test in einer Sandbox-Kopie. **Nicht ausgeführt:** alle schreibenden `gh`-Befehle, die Gate-Testläufe selbst (nur gesammelt), `pip install --dry-run`, `consistency-check.py --json`.
- Commit-Hashes: `fa37d7d0`, `c1e810c6`, `283fcd3c`, `f55601ba` (#904), `89cc6381` (#994) liegen in `origin/main`; `35f591e6` und `90be1146` nur lokal (nicht in `origin/main`, `90be1146` auch nicht auf `origin/feat/repository-documentation-consolidation`).
- #1151 F6-04..F6-13, #857 Skills-Emission zur Laufzeit, #858 Codex-Skills-Emission, #1007 Lab-Diff und `skills`-Liste: nur PR-Text oder keine Fundstelle.
- Wirksamkeit des Marker-Fixes in der CI: nicht gelaufen; kein Python 3.9 auf dem Host. Dependabot-Verhalten bei Marker-Zeilen: unbekannt.
- #1218-Stand: gemergt in `9aa0e0c0`, read-only per `gh` verifiziert (Entscheidung 38f). CI-Stand des Merge-Commits nicht geprüft. Die Aussagen "24-Zellen-Matrix" und "drei neue Diagnosen" im #1190-Kommentar stammen aus dem PR-Text (`.tmp/prs/1218.md:14,16`); ADR `docs/adr/0002-orchestrator-mode-topology.md` liegt in `origin/main`. #885 F-08, alle Angaben zu #1155 (außer F2), #1158, #1159, #1161 (außer `hook_common.sh:63`): laut Roadmap-Sweep.
- `scripts/lib/context.py:204` (#1161): Zuordnung zum Issue-Punkt nicht verifiziert.
- `inherit_active` (#946, `feat/model-inherit-main-chat`): die Issue-Aussage "nicht in main" ist durch `scripts/lib/provider_transform.py:662` fraglich; ob der Branch-Guard inhaltlich abweicht, ist nicht verifiziert.

## Re-Planning

Nach Task 7 (Marker gemergt), nach Task 9 (Merge #1218 in `9aa0e0c0` bestätigen) und nach Freigabe der #946-Tabelle prüfen: gelten die Annahmen noch (CI-Matrix `['3.9', '3.12']`, #1218-Stand, Branch-Zahlen)? Plan aktualisieren, nicht einfrieren. Aufwand: Textverweis auf `effort-estimator`, hier keine Zahl.

## Self-Review

- Jeder der 11 Phase-A-Issues ist genau einem Task zugeordnet: #547 (3a/3b), #1007 (4a/4b), #857/#858/#1116/#1151/#1150 (5/6), #1190 (9), #946 (10), #977 (11), #885 (12). PRs: #1218 (9), #1145/#1148 (2, 7, 8). Querverweis-Aktionen: #860/#854 (13), #1155/#1158/#1159/#1160/#1161 (14).
- Jeder Task hat genau eine Rolle (`developer`, `git`, `validator`) und messbare Akzeptanzkriterien (Befehl plus Erwartung).
- Keine TBD/TODO/Platzhalter außer den PR-Nummern des Marker-PRs (existieren erst nach Task 7) und der Follow-up-Nummer `<FU>` in Task 3b (entsteht erst bei Anlage).
- Entscheidungen 12 und 13 eingehalten: #946 nur Tabelle plus `!`-Befehle, #885 nicht geschlossen. #1190: Auto-Close durch #1218 (`9aa0e0c0`) eingetreten (38f); Task 9 prüft und reicht den Beleg-Kommentar nach, ohne erneutes Schließen.
- Entscheidungen 17, 19, 20, 21, 24, 39 eingehalten: ein PR für Phase A; #1186 in Phase E; #547 schließen plus Follow-up-Issue mit fünf Guide-Punkten (Anlage nur nach Freigabe); #1007 schließen mit benannten Abweichungen; #1086g nur Querverweis, Aktion in Phase C.
- Entscheidungen 35-38 eingehalten: 35/36 ohne Phase-A-Bezug; 38c konsistent mit dem #1086g-Querverweis; 38e (Texte ohne Closing-Keywords, Kommentar vor manuellem Schließen) in Global Constraints, Task 6, Task 7 umgesetzt; 38f (#1190 bereits durch Auto-Close geschlossen) in Task 9 als Prüf- und Nachtrags-Task umgesetzt, kein Schließen und kein Wiederöffnen.
- A-N1/A-N2 durch Entscheidungen 20/21 beantwortet, A-Q1 durch Entscheidung 39 (Task 3b mit fünf Punkten). Keine offene User-Frage in Phase A.
- Signaturen und Zeilenanker sind mit Datei und Zeile belegt (in `W` gelesen) oder als "laut Sweep/PR-Text" markiert.
