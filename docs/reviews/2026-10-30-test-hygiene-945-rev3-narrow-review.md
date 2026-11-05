# Narrow Review — SPEC-test-hygiene-945, Revision 3

> Bezug: `docs/specs/2026-10-30-test-hygiene-945-design.md` (Status: `Entwurf`, Revision 3)
> Art: **enge Nachprüfung** (kein Voll-Review). Geprüft wurden ausschließlich die
> Rev.-3-Korrekturen C1/C1b/C2/C3/C4, die Kleinbefunde A4/A11/IC-10/AC3-Evidenz/Kopf
> und Regressionen, die der Patch erzeugt haben könnte.
> Datum: 2026-10-30 · read-only (Spec nicht verändert)

## Scope & Methode

Gelesen: die Spec (1192 Zeilen) sowie die betroffenen Testmodule/Workflow-Dateien
im Arbeitsstand. Zählungen wurden mit dem Muster
`subprocess\.(run|call|check_output|check_call|Popen)\s*\(` je Datei bzw. je
Dateigruppe neu durchgeführt (Partitionierung über Dateinamen-Globs, damit keine
Trefferliste abschneidet). Kein Bash zur Verfügung — alle Zahlen stammen aus
dateiweisen Trefferlisten, nicht aus Schätzungen.

## Ergebnis je Prüfpunkt

| Punkt | Ergebnis | Beleg |
|---|---|---|
| **C1** (`test_secrets_and_isolation.py`) | verified | Datei hat **4** Aufrufe: `:109` (`_has_git`, `git --version`, `timeout=5`), `:117`/`:129`/`:173` (`git init -q`, ohne `timeout=`). Die drei ungebremsten Stellen liegen genau in `test_write_checked_warns_when_secrets_file_not_gitignored` (`:116`), `test_write_checked_no_warning_when_actually_gitignored` (`:128`), `test_write_checked_does_not_warn_for_committed_secrets_override` (`:168`). Spec (§AC3 Z. 199–206, §P2b Z. 1028–1034) sagt: 1 gebremst, **3 Edits** — korrekt; Datei steht in der P2b-Edit-Liste, Kopf dort „30 mit Edits“ = 30 Listeneinträge (nachgezählt). |
| **C1b** (`active_set_render.py`) | verified | `_prepare` Z. 41: `subprocess.run(["git", "init", "-q"], cwd=project, check=True)` — **kein** `timeout=`, also ungebremst. Weitere Aufrufe im Modul: `:49` `subprocess.run(..., timeout=900)` (gebremst) und `:70` `subprocess.Popen(...)` (kein Keyword möglich, Obergrenze über `proc.communicate(timeout=900)` Z. 74) → **kein weiterer ungebremster Aufruf**. „Allowlist-only (kein Edit)“ für dieses Modul ist nur noch im Revision-Log (historisch) vorhanden; §P2b nennt es jetzt als Edit-Datei und begründet den verbleibenden `Popen`-Allowlist-Eintrag korrekt. |
| **C2** (cwd-Regel) | verified | §IC-3 Z. 479–495: „Geltungsbereich (verbindlich): die **acht** Module … ohne Containment-Semantik“, Rückgaberegel ausdrücklich „(gilt für die acht Module)“, das neunte Modul bindet das Decoy (ADR-3, Invariante 2). §ADR-2 Z. 345–349 identisch. Kein Satz bindet mehr alle neun an `hook_project_root`; Z. 551 fordert nur die **Anwesenheit** von `cwd=`/`timeout=` (≠ `None`) für alle neun — das ist IC-6 Regel 1 und kein Widerspruch. |
| **C3** (README-Satz) | verified | `tests/README.md:104-105` enthält wörtlich „Weitere Heavy-Module nutzen noch modul-lokale Obergrenzen; Vereinheitlichung ist ein Follow-up.“ §IC-13, §P2b (Z. 1036) und Risikotabelle (Z. 1103) sagen übereinstimmend „präzisieren, nicht entfernen“; Nicht-Ziel „keine Vereinheitlichung“ bleibt konsistent (30/120/180/300/600 bleiben). |

## Recount (C4) — neun P1-Module, gemessen vs. Spec

| Modul | gemessen | Spec | Δ |
|---|---|---|---|
| `test_orchestrator_guard_hook.py` | 20 | 20 | 0 |
| `test_repo_containment_hook.py` | 15 | 15 | 0 |
| `test_hook_common_lib.py` | 8 | 8 | 0 |
| `test_graphify_guard_hooks.py` | 3 | 3 | 0 |
| `test_dod_push_check_hook.py` | 15 | 15 | 0 |
| `test_artifact_freshness_hook.py` | 2 | 2 | 0 |
| `test_pre_release_check_hook.py` | 1 | 1 | 0 |
| `test_auto_github_release_hook.py` | 1 | 1 | 0 |
| `test_release_gate_checksums.py` | 2 | 2 | 0 |
| **Summe** | **67 in 9 Dateien** | **67 in 9** | **0** |

Zusatz: in den neun Modulen existiert **kein** `import subprocess as …` /
`from subprocess import …` und kein `check_output`/`check_call`/`subprocess.call`;
die 67 sind ausschließlich `subprocess.run` — die Grep-Zahl ist damit für dieses
Set deckungsgleich mit der Aufrufstellen-Zahl. `test_hook_common_lib.py` hat 8
(`_call` + 7 direkte), `test_dod_push_check_hook.py` 15 — IC-4 stimmt.

## Partition

| Menge | Aufrufe gemessen | Dateien gemessen | Spec |
|---|---|---|---|
| P1 | 67 | 9 | 67 / 9 |
| P2a | **81** | 32 (jede Datei ≥ 1 Aufruf) | 81 / 32 |
| P2b (Edit-Dateien) | **52** | 30 (jede Datei ≥ 1 Aufruf, inkl. `active_set_render.py` = 3) | 52 / 30 |
| P2b allowlist-only (`tests/browser/conftest.py`) | **1** (`Popen` Z. 52) | 1 | 1 / 1 |
| out-of-scope (`tests/manual/run-manual-test.py`) | **2** | 1 | 2 / 1 |
| **Summen** | **203** | **73** | **203 / 73** |

Gegenprobe unabhängig von den Listen: alle `test_*.py` im `tests/`-Wurzelverzeichnis
ergeben 197 Aufrufe in 70 Dateien (Buchstabenpartitionen a–c 35, d–h 43, i–n 20,
o–z 99); `tests/browser`, `tests/orchestration`, `tests/automated`,
`tests/scenarios`, `tests/routing-llm-eval` enthalten außer dem einen `Popen` in
`tests/browser/conftest.py` **keinen** Aufruf; `tests/changelog_sections.py`,
`tests/conftest.py`, `tests/timeouts.py` keinen. 197 + 3 (`active_set_render.py`)
+ 1 (`browser/conftest.py`) + 2 (`tests/manual`) = **203 in 73 Dateien**. Keine
Datei doppelt: die 32 P2a- und 30 P2b-Namen sind untereinander und gegen die neun
P1-Module disjunkt (alle 62 Namen geprüft, nicht nur 5+5). `Sums correct.`

## Kleinbefunde

| Punkt | Ergebnis | Beleg |
|---|---|---|
| A4 (sechs Kommentargruppen in `validate.yml`) | ok | Datei hat genau die Gruppen `:13`, `:19`, `:35-36`, `:39-40`, `:46`, `:57-69`; oberhalb von `jobs:` (`:16`) steht nur der `concurrency`-Kommentar `:13`. Kernaussage „kein Erklärungsblock zur Jobpartition“ trifft zu. |
| A11 (Rollback-Reihenfolge) | ok | `P3 → P2b → P2a → P1` identisch in §P1-Rollback (Z. 952), Risikotabelle (Z. 1101) und „Rollback je Phase“ (Z. 1107). |
| IC-10 `-rs` | ok | Z. 685/686–689: `python -m pytest tests/browser -q -n 0 -rs`, mit Begründung. |
| AC3-Evidenzliste Klammern | ok | Z. 901: `(ERROR)` und `(2 Einträge)` geschlossen, keine offene Klammer. |
| Kopf | ok | Z. 3/4/7 `Datum 2026-10-30 (Rev. 3)`, `Revision: 3`, Z. 10 „1 offene Frage (OQ-4) und 12 … Punkte“ — OQ-Tabelle hat genau einen Eintrag, `Unverified` genau 1–12. |
| Spec-Pflichtsektionen / Trace / No-Placeholder | ok | `Interface Contracts`, `Acceptance Criteria`, `Datenfluss`, Problem/Ziel/Nicht-Ziele, Offene Fragen, Risiken vorhanden; `spec-id: SPEC-test-hygiene-945` + `Trace-Anker`; keine `TODO`/`TBD`/`{{…}}`; `Status: Entwurf` bewusst (nicht Teil dieser Nachprüfung). |

## Stale-Claim-Scan

Keine unmarkierte Altaussage. Gefundene Treffer der alten Zahlen sind sämtlich
als Historie gekennzeichnet: Z. 99 („Rev. 2 … 72 statt 67“), Z. 193 („Rev. 2
nannte 72, das war um 5 zu hoch“), Z. 1135 („Issue #945 nennt 75/25, Rev. 1
69/10, Rev. 2 201/72“), Z. 1179/1180 (Revision-Log). `129` und „alle vier
Aufrufe“ kommen in der Datei nicht vor; „20 Aufrufe“ nicht mehr; „allowlist-only“
erscheint nur in korrekter Bedeutung (Z. 120/124 P2b-Split, Z. 713 IC-11
`Popen`, Z. 901 AC3-Evidenz).

## Findings (keine blockierenden)

1. **minor · Konsistenz · §AC3 Z. 190–197** — „Rev. 1 nannte 69 Treffer in zehn
   Modulen — die zehn enthielten zwei Module außerhalb des P1-Scope: …“ geht
   arithmetisch nicht auf: neun P1-Module + die beiden genannten = elf Module,
   und die beiden enthalten heute 4 Aufrufe (antigravity 3 + hook_registration 1),
   also 67 + 4 = 71 ≠ 69. Zudem liest sich „Bereits gebremst sind 3 Aufrufe“
   direkt nach „67 in den neun P1-Modulen“ wie eine Aussage über den Hook-Slice,
   obwohl die drei ausdrücklich außerhalb liegen.
   *Fix (1 Zeile):* Parenthese ersetzen durch „Rev. 1 und Rev. 2 lagen zu hoch;
   von den 67 P1-Aufrufen ist keiner gebremst — die drei gebremsten
   `SCRIPT_TIMEOUT`-Stellen liegen in `tests/test_antigravity_hooks_registration.py`
   (`:268`, `:277`, `:404`), außerhalb des Sets“ und die 69/zehn-Module-Rekonstruktion streichen.
2. **minor · Konsistenz · §P1 Aufwand Z. 942** — „`timeout=` an 67 Aufrufstellen“
   ist um eins zu hoch: `tests/test_hook_common_lib.py:381` (`_scan`) führt
   bereits `timeout=timeout`; dort ändert sich nur der Default (`None` →
   `SCRIPT_TIMEOUT`, IC-4). *Fix:* „66 neue `timeout=`-Keywords + `_scan`-Default“.
3. **info · IC-2 Bestandswert-Tabelle Z. 462** — die Zeile `900` nennt nur „die
   sechs `RUN_TIMEOUT`-Definitionen“ (nachgeprüft: genau sechs, in
   runner/applier/credentials/inactive_scope/refill/fanout). Seit C1b steht
   `tests/active_set_render.py` mit einem **siebten** 900er (`timeout=900`,
   Z. 49) in P2b. Das ist durch die Bestandswert-Regel gedeckt (kein Verstoß),
   die Tabelle sollte den Fall aber nennen, damit der Plan ihn nicht
   „vereinheitlicht“.

## Verdikt

**APPROVED** — C1, C1b, C2, C3 und C4 sind vollständig und korrekt eingearbeitet;
die Neumessung ist exakt (67/81/52/1/2 = 203 in 9/32/30/1/1 = 73 Dateien, keine
Doppelzählung, keine ungelistete Datei mit Aufruf); die Kleinbefunde sind grün.
Der Patch hat keine neue Inkonsistenz erzeugt; offen bleiben nur die zwei
minor-Wortlautbefunde und eine info-Notiz, die die Freigabe nicht blockieren.
