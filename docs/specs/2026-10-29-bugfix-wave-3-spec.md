# Bugfix-Welle 3 — Spec

> Status: Entwurf
>
> spec-id: SPEC-bugfix-wave-3
>
> **Betroffener Bereich:** PreToolUse-/Push-Hooks (`dod-push-check`, `orchestrator-guard`,
> `repo-containment`), Hook-Deployment (`scripts/lib/hooks.py`, `scripts/lib/hook_plugins.py`),
> Handoff-Contracts (`config/role-defaults.yaml`), Variablen-Builder (`scripts/lib/config.py`),
> Placeholder-Ratchet, Admin-Server-Netzwerkmodus, Doctor-Detektor `rules-file-wrong-suffix`,
> zcode-Provider-Doku.
> **Umfang:** 13 Bugs (B1–B13, siehe »Bug-Liste«) in 4 PRs (+ PR 0 Housekeeping, nur nach
> ausdrücklicher Freigabe).
> **Nicht in diesem Dokument:** Implementierung, Commits, Issue-Änderungen, Plan
> (`docs/plans/2026-10-29-bugfix-wave-3-plan.md`).
> **Belege:** Datei:Zeile beziehen sich auf `origin/main` = `043d29a4` (Stand 2026-10-29).
> Zeilennummern driften, maßgeblich sind die Symbole.

## Problem

Ein Analysebericht (2026-10-28) und ein Verifikationsvorlauf (2026-10-29) gegen `origin/main` zeigen
13 reale Defekte, die auf der Release-Linie `v2.0.0-beta.4` liegen:

- **Fail-open in Sicherheits-Hooks:** `is_fork_bomb` ist quadratisch (20 KB Bezeichner = 4,9 s auf
  Funktionsebene, 5,16 s end-to-end); ein Hook-Timeout lässt den Befehl durch. Ein Absturz des
  Befehls-Klassifikators in `orchestrator-guard-impl.sh` fällt auf `none narrow none` zurück
  (Destructive-/Mutation-Gate übersprungen). `repo-containment` reicht Impl-Abstürze ungefiltert
  durch und verschluckt Detector-Abstürze per `|| true`.
- **Falsche/irreführende Meldungen:** `dod-push-check` meldet `Protected branches: main, main, master`;
  der Doctor meldet für Manifest-Dateien `rules-file-wrong-suffix` mit einem schädlichen Fix-Hinweis;
  der Admin-Server weist im Netzwerkmodus jede Mutation mit `origin not allowed` ab.
- **Plattformabhängige Ausgabe:** vier Schreibpfade im Hook-Code (ein Scaffold, drei Managed-Indizes)
  nutzen `Path.write_text` ohne `newline=` und schreiben unter Windows CRLF (#961-Rest).
- **Release-Gate rot auf dem Tag:** 8 `handoff.output-not-consumed`-Warnungen (reproduziert,
  `python3 scripts/consistency-check.py`, 2026-10-29).
- **Literale Platzhalter im generierten Output:** `{{TECH_STACK}}`, `{{AGENT_META_REPO}}`,
  `{{TEST_COMMANDS}}`, `{{PROJECT_DESCRIPTION}}` u. a. bleiben ungefüllt (#983, #1037).
- **Testlücken:** `dod-push-check`-Tests sind nicht hermetisch und lassen Prüfungen des
  2. Security-Re-Reviews aus (#951, #954).

Zusätzlich ist der Issue-Zustand inkonsistent zum Code (siehe Abschnitt »Scope-Befund A«).

### Bug-Liste (Zählung der »13 Bugs«)

| Nr. | Issue | Kurzbeschreibung | PR |
|---|---|---|---|
| B1 | #1033 | doppeltes `main` in der Block-Meldung | 1 |
| B2 | #943(a)(m) | `is_fork_bomb` quadratisch; Geschwister: Klassifikator-Absturz fail-open | 1 |
| B3 | #944 SR-B-17 | `repo-containment.sh` reicht Impl-Abstürze durch | 1 |
| B4 | #944 `\|\| true` | Write-Detector-Absturz = kein Block | 1 |
| B5 | #961-Rest | Schreibpfade ohne LF-Garantie | 2 |
| B6 | #951 | `dod-push-check`-Tests nicht hermetisch | 2 |
| B7 | #954 | ausgelassene Security-Re-Review-Checks | 2 |
| B8 | #1031 | 8 unkonsumierte Output-Contracts | 3 |
| B9 | #983 | `TECH_STACK`/`AGENT_RULES`/`EXTERNAL_DOCS_LANGUAGE` ohne Filler | 3 |
| B10 | #1037 | `project.description` und ableitbare Variablen ohne Fallback | 3 |
| B11 | #897 | `origin not allowed` im Netzwerkmodus | 4 |
| B12 | #1034 | `rules-file-wrong-suffix` meldet Manifest-Dateien | 4 |
| B13 | #856 | zcode ZC-1 — Doku-Eintrag, laut D8 **kein Code-Bug** | 4 |

- Echte Code-Defekte: 12 (B1–B12); B13 zählt mit, weil D1 den Umfang so festlegt.
- **Nicht** mitgezählt: optionaler Task #944 SR-B-19 (kein Pflichtumfang). Der Klassifikator-Fail-open
  (Review-Befund M1) ist Geschwisterpfad von B2 (gleicher Python-Block wie `is_fork_bomb`) und kein
  eigener Zähler.

## Ziel

- Jeder der 12 Code-Bugs (B1–B12) ist an der Root-Cause behoben (alle Aufrufer/Geschwisterpfade
  derselben Fehlerklasse innerhalb des benannten Scopes), mit mindestens einem Regressionstest je Bug
  (D4); B13 (#856) ist ein Doku-Eintrag ohne Regressionstest (D8).
- Alle Sicherheits-Hooks bleiben fail-closed; kein Fix darf einen neuen Fail-open-Pfad öffnen.
- `python3 scripts/consistency-check.py` auf frischem Checkout: 0 `handoff.output-not-consumed`.
- Seriell mergbare PRs mit genau einem AC-01-Rebaseline pro PR, der Render-Output ändert,
  jeweils auf frischem `main` (D5, Rest-Regel).

## Nicht-Ziele

- #1035 (geschlossen, NOT_PLANNED), #1032 (Gemini/Antigravity `hooks.json` cwd-abhängig),
  #1036 (geschlossen; Code-Zustand nicht Teil dieser Welle).
- Reste der Epics #943/#944 außer #943(a)(m), #944 SR-B-17 und `|| true`, optional SR-B-19
  → Folge-Issues mit eigener Spec (D6).
- #945 (Guard-Test-Isolation, CI-Timeouts). Hinweis: Brief empfiehlt, #945 vorzuziehen, bevor
  #943-Tests erweitert werden — hier nicht eingeplant (Timing-AC als Skalierungs-AC robust
  formuliert), Entscheidung: Q6, siehe Risiko R6.
- Weitere hartkodierte Repo-Identitäten in URL-Form: `scripts/lib/standalone.py:35` (`REPO_URL`),
  `scripts/hermes_export.py:96` (`REPO_URL`), `scripts/admin-server.py:4284` (Raw-URL
  `model-registry.json`). Kein Platzhalter-Leak, sie rendern korrekte Werte; andere Form
  (volle URL statt `owner/repo`) → Folge-Issue, nicht Teil von AC-3.12.
- #1006/#1020/#1007 (Plan A/B; Plan A bereits gemergt, siehe Befund A).
- Die übrigen ~75 `write_text`-Aufrufe in `scripts/` ohne `newline=` (u. a.
  `scripts/lib/skills.py:85`, managed index) — gleiche Fehlerklasse, Folge-Issue.
- Bugfix des Spec/Plan-Validators: `scripts/lib/consistency/spec_plan.py` klassifiziert nur
  `*-design.md` als Spec (`_DESIGN_RE` :50, `_classify` :318); diese `*-spec.md` wird als Plan
  geprüft. Nur erwähnt, nicht behoben.
- Ausführen von Issue-Änderungen (Schließen, Reopen, Neuanlage) — nur als Plan-Tasks mit
  Textentwurf (D2, D6).

## Entscheidungsregister

Bindende User-Entscheidungen vom 2026-10-29.

| ID | Entscheidung | Konsequenz in dieser Spec |
|---|---|---|
| D1 | Scope: alle 4 PRs / 13 Bugs. | Abschnitte PR 1–PR 4. |
| D2 | Schließ-Kandidaten #948, #950, #952, #953, #207, #534, #865, #962; #961/#971 erst nach Fix/Verifikation; #192 bleibt offen. Ausführung wartet auf Freigabe. | Plan-Task »PR 0 Housekeeping (nur nach ausdrücklicher Freigabe des Users)« inkl. Kommentar-Entwürfen (Englisch) und #953-Folge-Issue-Entwurf (`push.recurseSubmodules` per Config/`-c` nicht erkannt). Laut Befund A sind #948, #950, #952, #953 bereits geschlossen; offen: #207, #534, #865, #962, #971. |
| D3 | Hooks-PR zuerst (PR 1), #897 danach. | Merge-Reihenfolge. |
| D4 | Pro Bug mindestens ein Regressionstest (trotz `rapid-prototyping`). | Jeder Bug-Abschnitt nennt Test-Name/-Ort. #856 ist laut D8 kein Code-Bug (siehe dort). |
| D5 | PR 1/2/4 vor Plan A, PR 3 und #1036 danach; Rebaselines immer auf frischem `main` nach Merge des anderen PRs. | **Gegenstandslos laut Befund A** (Plan A gemergt). Weiter gültig nur die Rebaseline-Regel. Formale Aufhebung: Q2. |
| D6 | Epic-Reste #943/#944 → Folge-Issues mit Spec; PRs nutzen »Refs«, nicht »Closes«. | Plan-Task mit Issue-Textentwurf, nicht ausführen. |
| D7 | #1037: `PLATFORM`/`RUNTIME` ohne Konfig bleiben leer (kein Fehler); `AGENT_META_REPO` aus dem Default-Repo. | Fix-Vertrag #1037. |
| D8 | #856: Doku + wontfix (documented). | PR 4, kein Code. |

Zusatzregel aus dem Brief: Closing-Keywords je Issue einzeln (»Closes #a«, »Closes #b«) — nur die
erste Nummer einer Kommaliste schließt automatisch. Bis Q1 entschieden ist, gilt für bereits
geschlossene Issues »Refs« (Befund A).

## Scope-Befund A — Issue-Zustand widerspricht dem Code

- `gh issue view` (2026-10-29): geschlossen (~05:00Z, COMPLETED, Kommentar »Verifiziert – behoben in
  <hash>«): #1033, #943, #944, #961, #951, #954, #1031, #983, #1037, #1034, #948, #950, #952, #953,
  #1036; #1035 NOT_PLANNED.
- Die genannten Commits `587e8684`, `c85ee04e`, `ebfa789b`, `24233481`, `26d2affa`, `63b12bde`,
  `af9abe9e`, `f9c33165` existieren im Repo nicht (weder lokal noch auf einem `origin`-Branch); nur
  `ce13a6bf` (#956) existiert.
- Die Fixes fehlen nachweislich im Code von `origin/main` (Stichprobe dieser Spec bestätigt:
  `hooks/1-generic/dod-push-check.sh:1071` dupliziert, `is_fork_bomb` unbeschränkt,
  `repo-containment-impl.sh:702` `|| true`, `scripts/lib/hooks.py:708` `write_text`,
  `_UNKNOWN_TEMPLATE_RATCHET` nicht leer, 8 Handoff-Warnungen).
- **Stance:** Die Fehler sind real; die Spec gilt wie gebrieft. Die Issue-Schließung ist ein externer
  Fakt, der vor PR 1 zu klären ist (Q1, Plan-Task »PR 0a Issue-Zustand klären«, nur Text-Entwurf).
- Weiterhin offen: #897, #856, #945, #1032, #1007, #207, #534, #865, #962, #971, #192.
- Plan A ist gemergt: #1006 via PR #1010 (`9ccc27c8`), #1020 geschlossen, Teile #1007 via
  PRs #1016–#1018 (+ #1019 Release 2.0.0-beta.3); PR #1009 war reine Doku.

## PR 1 — `fix/hooks-hardening-w1` (Security zuerst)

### #1033 — doppeltes `main` in der Block-Meldung

- **Problem:** Block-Meldung lautet `Protected branches: main, main, master.` (Default-Fall).
- **Root-Cause:** `hooks/1-generic/dod-push-check.sh:1071` gibt `$MAIN_BRANCH, main, master`
  ungefiltert aus. Einzige Meldungsstelle (Grep). Geschwisterpfad: der Python-Klassifikator setzt
  `PROTECTED = {"main", "master", MAIN_BRANCH} - {""}` (:531) bereits dedupliziert — nur die
  Shell-Meldung ist betroffen. `MAIN_BRANCH` kommt aus Env `AGENT_META_MAIN_BRANCH` > Config-Key
  `GIT_MAIN_BRANCH` (`read_config_var`) > `main` (:221-226). Quelle ist `hooks/1-generic/`;
  `.agents/hooks/`-Kopien sind gerendert. Der Hook wird nur für Claude verteilt.
- **Fix-Vertrag:** Die Meldung listet `MAIN_BRANCH`, `main`, `master` in dieser Reihenfolge ohne
  Duplikate (reine Shell, keine neue Abhängigkeit). Sonstiger Meldungstext unverändert.
- **AC:**
  - **AC-1.1** Default (kein Env, kein Config-Key): Meldung enthält exakt
    `Protected branches: main, master.`
  - **AC-1.2** `AGENT_META_MAIN_BRANCH=develop`: Meldung enthält exakt
    `Protected branches: develop, main, master.`
  - **AC-1.3** `AGENT_META_MAIN_BRANCH=master`: Meldung enthält exakt
    `Protected branches: master, main.`
  - **AC-1.4** Kein Env, `variables: {GIT_MAIN_BRANCH: develop}` in `.meta-config/project.yaml`
    (gelesen über `read_config_var`, :135/:224): Meldung enthält exakt
    `Protected branches: develop, main, master.`
- **Regressionstest:** `tests/test_dod_push_check_hook.py::test_block_message_dedups_default_main`,
  `::test_block_message_lists_custom_main_branch`, `::test_block_message_dedups_master_main_branch`,
  `::test_block_message_lists_config_main_branch` (Namen neu).

### #943(a)(m) — `is_fork_bomb` quadratisch, Timeout = fail-open

- **Problem:** Lange Eingaben treiben `is_fork_bomb` in quadratische Laufzeit; der Hook-Timeout lässt
  den Befehl durch.
- **Root-Cause:** `hooks/1-generic/orchestrator-guard-impl.sh:is_fork_bomb` (:805) — Regex
  `([A-Za-z_:][A-Za-z0-9_:]*)\s*\(\s*\)\s*\{([^}]*)\}` mit `re.finditer`. Zwei quadratische Pfade
  (gemessen, Py3.13): (1) Header ohne linke Verankerung — jeder Startpunkt im Bezeichner wird erneut
  probiert (`{0,63}` allein: 300 KB = 0,50 s, verfehlt das Ziel); (2) Body `\{([^}]*)\}` —
  `"f(){ "*60000` (300 KB) = 86 s, auch mit `{0,63}`. Einziger Aufrufer:
  `destructive = is_fork_bomb(strip_quoted(command))` (:816).
- **Root-Cause Geschwisterpfad (Klassifikator-Absturz, Review-Befund M1):** Der Python-Block, der
  `is_fork_bomb` enthält, ist der gemeinsame Befehls-Klassifikator für Destructive-, Mutation- und
  BOM-Gate (`_GIT_SCAN_RAW=$(… "$_PY" -c "…" "$PAYLOAD_CWD" 2>/dev/null || echo "none narrow none")`,
  :333–:846). Jeder Absturz (Exception, rc ≠ 0) und jede leere Ausgabe ergibt `none` → beide Gates
  übersprungen = fail-open, gleiche Fehlerklasse wie #944 `|| true`. Kommentar :328-329 dokumentiert
  das bewusst (»fail-open, matching the prior gates«) → **benannte Verhaltensänderung**, Kommentar
  wird mitgeändert. Unbekannte Ausgabewerte werden nur für das BOM-Wort normalisiert (:853-856),
  nicht für Kategorie/Scope. Übrige `"$_PY"`-Aufrufe im Impl geprüft (Grep): :145 (JSON-Validierung,
  blockt), :195 (Sentinel, `|| echo ""` → kein Sentinel = keine Elevation, :238), :265/:280
  (Allowlist, Fallback `off`/`0` = keine Elevation), :905 (`STRICT`, Fallback strict) — alle fallen
  auf die restriktivere Seite; nur :846 ist fail-open.
- **Fix-Vertrag (Default, Q3):**
  - Header mit Lookbehind: `(?<![A-Za-z0-9_:])([A-Za-z_:][A-Za-z0-9_:]*)\s*\(\s*\)\s*\{` —
    **keine** Namenslängengrenze (`{0,63}` + Lookbehind würde Namen > 64 verpassen = fail-open).
  - Body begrenzt: `str.find('}', end, end + body_max)` mit `body_max = 1024`. **Ohne `}` im Fenster
    → `True` (Block, fail-closed).** Die frühere Variante »Fenster selbst als Body prüfen« öffnet
    einen Fail-open-Pfad (Self-Pipe nach > 1024 Body-Zeichen) und widerspricht dem Ziel; sie bleibt
    nur als Q3-Alternative. Preis: Fehlalarm-Klasse R3 (jede Funktionsdefinition, deren erste
    1024 Body-Zeichen kein **ungequotetes** `}` enthalten; harter Block ohne Ausweg über den
    `git`-Sentinel).
  - Block-Meldung: Das Destructive-Gate (`orchestrator-guard-impl.sh`, Meldung `destructive operation
    requires explicit user approval`) gibt zusätzlich eine Hinweiszeile aus, die die Fenstergrenze
    nennt (`1024` Zeichen, ungequotetes `}`, Verweis auf »Bekannte Grenzen« in `branch-guard`), damit
    ein Fehlalarm der Klasse R3 erkennbar ist. Das Ausgabeformat des Klassifikators (drei Felder)
    bleibt unverändert; die Zeile steht bei jedem Destructive-Block und ist konditional formuliert
    (»falls …«).
  - **Kein** Kappen der Gesamteingabe, außer die Kappung **blockt** (Kappen ohne Block verpasst
    Bomben hinter der Kappe = fail-open).
  - Klassifikator: Exit-Code erfassen (kein `|| echo "none narrow none"`). rc ≠ 0 **oder** Ausgabe, die
    nicht exakt `<none|mutation|destructive> <narrow|broad> <none|message|file>` ist → Meldung
    `ORCHESTRATOR_GUARD: command classifier failed rc=<n>, failing closed` auf stderr + `exit 2`,
    unabhängig von Sentinel/Strict-Mode (wie das Destructive-Gate). Kommentar :320-329 entsprechend.
  - `is_fork_bomb`-Contract: wirft die Funktion (z. B. `re.error`), propagiert die Exception → rc ≠ 0
    → Block (kein lokales `try/except`, das `False` liefert).
  - Header-»known gaps« (`orchestrator-guard-impl.sh`/`orchestrator-guard.sh`) und »Bekannte Grenzen«
    in `rules/1-generic/branch-guard.md` (Quelle; gerendert u. a. nach `.claude/rules/branch-guard.md`,
    `.continue/rules/branch-guard.md`, `.github/instructions/branch-guard.instructions.md`, alle in
    `hashes.json` → PR-1-Rebaseline AC-1.21) ergänzen: Funktionskörper, deren erste 1024 Zeichen kein
    ungequotetes `}` enthalten, werden hart geblockt (Fehlalarm-Grenze R3, kein Sentinel-Ausweg);
    Klassifikator-Absturz blockt.
- **AC:**
  - **AC-1.5** Skalierung, lange Bezeichner: `is_fork_bomb("a"*n + "(){ :; }")` für n = 300 000 und
    n = 600 000, je best-of-3 mit `time.perf_counter`: `t(600k) / t(300k) < 3` (linear ≈ 2,
    quadratisch ≈ 4) **und** `t(300k) < 1 s` (Altverhalten: 20 KB = 4,9 s).
  - **AC-1.6** Wiederholte Header: (i) `is_fork_bomb("f(){ " * 60000)` → `True` (erstes Fenster ohne
    `}`) in < 1 s (Altverhalten 86 s); (ii) Skalierung mit geschlossenen Bodies
    `is_fork_bomb("f(){ x} " * k)` für k = 60 000 und k = 120 000, best-of-3:
    `t(120k) / t(60k) < 3` **und** `t(60k) < 1 s`.
  - **AC-1.7** Body-Fenster erschöpft: `is_fork_bomb("f(){ " + "x"*1025)` (kein `}`) → `True`;
    `is_fork_bomb("f(){ " + "x"*1000 + " }")` → `False`; Self-Pipe nach > 1024 Body-Zeichen
    (`"f(){ " + "x"*2000 + " f|f& }"`) → `True`.
  - **AC-1.8** Alle bisher getesteten Fork-Bomb-Fälle (`test_fork_bomb_blocked`,
    `test_fork_bomb_text_literal_not_blocked`) unverändert; zusätzlich ein Name mit > 64 Zeichen
    (`"b"*100 + "(){ " + "b"*100 + "|" + "b"*100 + "& };"`) erkannt.
  - **AC-1.9** Hook end-to-end mit 20 KB Bezeichner: korrektes Verdikt und Laufzeit < 2 s (gemessen
    bisher 5,16 s; harmloser 300-KB-Befehl e2e 0,53 s). Hook-Timeout: in der Registrierung nicht
    gesetzt (kein `timeout` in `scripts/lib/hooks.py`, Grep) → Provider-Default; Claude Code laut
    externer Hook-Doku 60 s, Gemini/Antigravity **unverifiziert**. Die AC prüft daher nur
    »Verdikt korrekt, < 2 s«, nicht »innerhalb des Hook-Timeouts«.
  - **AC-1.10** Header-»known gaps« (beide Guard-Dateien) und `rules/1-generic/branch-guard.md`
    »Bekannte Grenzen« nennen die Body-Fenster-Grenze (Block, wenn die ersten 1024 Body-Zeichen kein
    ungequotetes `}` enthalten; gequotete Spannen inkl. `"${…}"` entfernt `strip_quoted` vorher; kein
    Ausweg über den Sentinel) und das Fail-closed bei Klassifikator-Absturz. Zusätzlich (Test):
    Hook end-to-end mit `"f(){ " + "x"*1025` → exit 2, stderr enthält `1024`.
  - **AC-1.11** Kalibrierung: Messwerte (best-of-3) der Tests zu AC-1.5, AC-1.6, AC-1.9 lokal vor
    und nach dem Fix im PR dokumentiert; Grenzen werden nur gelockert, wenn ein Wert näher als
    Faktor 3 an der Grenze liegt.
  - **AC-1.12** Klassifikator rc ≠ 0: PATH-Shim `python3`, der nur bei einem Marker des
    Klassifikator-Codes im `-c`-Argument (z. B. `def is_fork_bomb`) mit rc 1 endet und sonst das
    echte Python `exec`t → harmloser Bash-Befehl (`ls`) wird mit exit 2 geblockt, stderr enthält
    `command classifier failed rc=`. Test vor dem Fix nachweislich rot (heute Allow).
  - **AC-1.13** Klassifikator rc 0 mit leerer bzw. formatfremder Ausgabe (Shim druckt `garbage`) →
    exit 2.
- **Regressionstest:** `tests/test_orchestrator_guard_hook.py::test_fork_bomb_linear_on_long_identifier`,
  `::test_fork_bomb_linear_on_repeated_headers`, `::test_fork_bomb_body_window_exhausted_blocks`,
  `::test_fork_bomb_long_name_detected`, `::test_fork_bomb_end_to_end_long_input_fast`,
  `::test_classifier_crash_fails_closed`, `::test_classifier_garbage_output_fails_closed`
  (Namen neu). Mechanik, wie der Test die in die `.sh` eingebettete Python-Funktion isoliert aufruft:
  **unverifiziert** (Plan klärt).

### #944 SR-B-17 + `|| true` — `repo-containment` reicht Abstürze fail-open durch

- **Problem:** (a) Ein Absturz von `repo-containment-impl.sh` (rc 1, 128+n, 141) wird vom Wrapper als
  Exit-Code durchgereicht — nicht 2, also kein Block. (b) Ein Absturz des Python-Write-Detectors
  liefert keine Kandidaten und damit kein Block.
- **Root-Cause:**
  - `hooks/1-generic/repo-containment.sh:46-48`: `printf … | bash "$IMPL"; exit $?` mit `pipefail`
    (SIGPIPE 141 des `printf` wird ebenfalls durchgereicht). Referenzmuster ohne den Fehler:
    `hooks/1-generic/orchestrator-guard.sh:55-66` (`PIPESTATUS[1]`, nur 0/2 durch, sonst exit 2).
  - `hooks/1-generic/repo-containment-impl.sh:702`: `WRITE_TARGETS=$(… "$_PY" -c '…' 2>/dev/null || true)`.
    Kommentar :574-581 dokumentiert das Fail-open bewusst als »best-effort« → der Fix ist eine
    **benannte Verhaltensänderung**, Kommentar wird mitgeändert. Issue-Zeile :492 ist veraltet.
  - Geschwister geprüft: `containment_verdict`-Auswertung (:560, :709) blockt im `*)`-Zweig bei
    unbekannter/leerer Ausgabe (fail-closed); nur der Detector (:585–:702) ist fail-open.
    Gleiche Klasse im Orchestrator-Guard: Klassifikator :846 (siehe B2, M1).
- **Fix-Vertrag:**
  - Wrapper: Exit-Normalisierung wie `orchestrator-guard.sh` — `PIPESTATUS[1]` auswerten; `0` → 0,
    `2` → 2, alles andere → Meldung auf stderr + `exit 2`.
  - Impl: Exit des Detectors erfassen (kein `|| true`); Detector-rc ≠ 0 → Block (exit 2) mit Meldung
    `repo-containment: write detector failed rc=<n>, failing closed`. rc = 0 ohne Kandidaten bleibt
    Allow. Kommentar :574-581 entsprechend.
  - Versionen: Wrapper `1.0.0`, Impl `1.2.0` → Bump nach conventions-Skill (Stufe im Plan).
- **AC:**
  - **AC-1.14** Impl endet mit rc ∈ {1, 137, 141} → Wrapper exit 2 mit stderr-Meldung.
  - **AC-1.15** Impl endet mit 0 bzw. 2 → Wrapper reicht 0 bzw. 2 unverändert durch.
  - **AC-1.16** Detector stürzt ab → Bash-Tool-Aufruf exit 2, stderr enthält
    `write detector failed rc=`. `_PY` wird vorher schon benutzt (`resolve_realpath` :162,
    `read_effective_containment` :332, `containment_verdict` :484) — ein generell kaputtes `_PY`
    würde den Test aus falschem Grund grün machen. Daher: PATH-Shim `python3` (wird über
    `hook_python_bin` als `_PY` gewählt, :122), der **nur** beim Detector-Aufruf (Marker `INPLACE = {`
    im `-c`-Argument, :600) mit rc 1 endet und sonst das echte Python `exec`t. Test vor dem Fix
    nachweislich rot (heute `|| true` → Allow).
  - **AC-1.17** Detector rc 0 ohne Kandidaten → unverändert Allow.
- **Regressionstest:** `tests/test_repo_containment_hook.py::test_wrapper_fails_closed_on_impl_crash`
  (parametrisiert, Vorlage `tests/test_orchestrator_guard_hook.py:1332`),
  `::test_bash_detector_crash_fails_closed`, `::test_bash_detector_no_targets_allows` (Namen neu).

### Optional — #944 SR-B-19 (In-place-Flags, `cp -t DIR`)

- **Status:** OPTIONALER Task; nur mit Tests; mittleres Fehlalarm-Risiko.
- **Root-Cause (Stichprobe):** Detector-Zweig `elif cmd in INPLACE:` (`repo-containment-impl.sh`,
  ~:690) erkennt `-i`/`-i.<suffix>`/`--in-place`, aber keine gebündelten Flags (`sed -Ei`,
  `perl -pi`); `cp -t DIR` ist nicht erfasst. Vollständigkeit der Geschwisterpfade (andere
  Kopier-/Move-Kommandos mit `-t`): **unverifiziert**.
- **AC (nur falls umgesetzt):**
  - **AC-1.18** `sed -Ei 's/a/b/' /etc/x`, `perl -pi -e … /etc/x`, `cp -t /etc a` → Block.
  - **AC-1.19** `sed -E 's/a/b/' f`, `perl -p -e … f` (ohne `i`) → kein Kandidat (kein Fehlalarm).
- **Regressionstest:** `tests/test_repo_containment_hook.py::test_bundled_inplace_flags_detected`,
  `::test_non_inplace_flags_not_flagged`, `::test_cp_target_dir_detected` (Namen neu).

### PR-1-Querschnitt: Versionen, Changelog, Rebaseline

- **AC-1.20** Jede geänderte Hook-Datei hat einen gebumpten `# version:`-Header
  (`dod-push-check.sh` 2.1.5, `orchestrator-guard-impl.sh` 1.7.0, ggf. `orchestrator-guard.sh` 3.2.0,
  `repo-containment.sh` 1.0.0, `repo-containment-impl.sh` 1.2.0 als Ausgangsstände); `CHANGELOG.md`
  hat einen Eintrag.
- **AC-1.21** Genau ein AC-01-Rebaseline: `python tests/test_ac01_render_identity.py --write`,
  Begründung im Docstring-Rebaseline-Log von `tests/test_ac01_render_identity.py`, Digests in
  `tests/test_opencode_v2_surface.py::_FIXTURE_TREES` nachgezogen; beide Tests grün. Erwartete Drift:
  die geänderten Hook-Dateien (Claude + Gemini), die gerenderten `branch-guard`-Regeln
  (Claude/Continue/Copilot, AC-1.10) **sowie** die davon abgeleiteten Manifeste/Indizes genau dieser
  Provider: `<Provider>/.meta-config/generated-file-hashes.json`, `<Provider>/.meta-config/context-hashes.json`
  und die betroffenen Managed-Indizes (z. B. `Claude/.claude/hooks/.agent-meta-managed`;
  `hashes.json` :98/:148/:153 für Claude). Jede andere Drift ist unerwartet.
- **AC-1.22** Nach `python3 scripts/sync.py` auf diesem Repo ist jede deployte Kopie der geänderten
  Hooks (`.agents/hooks/*` versioniert; `.claude/hooks/*` lokal, gitignored) byte-identisch zum
  **Render** der Quelle `hooks/1-generic/<name>` (Quelle mit `{{AGENT_META_PROVIDER}}` →
  Provider-Name, `scripts/lib/hooks.py:526`) — nicht zur rohen Quelle, die sich genau darin
  unterscheidet. `check_stale_deployed_hooks` (`scripts/lib/consistency/hook_drift.py`, prüft nur
  `# version:`) ohne Findings. Ist-Stand: lokale `.claude/hooks/dod-push-check.sh` steht auf 2.1.2
  gegen Quelle 2.1.5 (veraltet, nicht versioniert).

## PR 2 — `fix/hooks-py-lf-and-tests`

### #961-Rest — Hook-Schreibpfade ohne LF-Garantie

- **Problem:** Unter Windows übersetzt `Path.write_text` `\n` zu `\r\n`; per `--create-hook`
  erzeugte Hook-Scaffolds und die Managed-Indizes bekommen CRLF.
- **Root-Cause:**
  - `scripts/lib/hooks.py:708` (`target_path.write_text(content, encoding="utf-8")`) gehört zu
    `create_hook` (:679, Scaffold für `sync.py --create-hook`, überschreibt nie), **nicht** zum
    Deploy.
  - Managed-Indizes: `scripts/lib/hooks.py:635`, `scripts/lib/hook_plugins.py:160` (Release-Gates)
    und `:348` (Hook-Lib).
  - Der eigentliche Hook-Deploy ist bereits LF-sicher: `write_checked` (`hooks.py:555`,
    `hook_plugins.py:132`, `:328`) → `write_atomic`.
  - Es gibt **keine** `chmod`-Folge in `hooks.py`, `hook_plugins.py` oder `io.py` (Grep); Hooks werden
    als `bash <path>` registriert (`hooks.py:147-148`) und brauchen kein Exec-Bit.
  - Geschwister derselben Klasse außerhalb des Scopes: `scripts/lib/skills.py:85` und ~75 weitere
    (Nicht-Ziel).
- **Fix-Vertrag:** Alle vier Stellen schreiben über `scripts/lib/io.py:write_atomic(path, content,
  mode="w")` (öffnet mit `newline="\n"`, :378). `write_text(newline=)` wird nicht genutzt (erst
  Py 3.10). `write_atomic` ist in beiden Modulen bereits importiert (`hooks.py:9`,
  `hook_plugins.py:16`) — neue Aufrufstellen, kein neuer Konsument.
  **Benannte Verhaltensänderung:** `write_atomic` nutzt `mkstemp` (:377) → Modus 0600. Neu erzeugte
  Scaffold-Hooks und die drei Index-Dateien wechseln vom umask-Modus (typisch 0644/0664) auf 0600.
  Git unberührt (Git versioniert nur das Exec-Bit, das hier weder vorher noch nachher gesetzt ist).
- **AC:**
  - **AC-2.1** Für jede der vier Stellen: bei simulierter Windows-Übersetzung (Monkeypatch analog
    `tests/test_newline_normalization.py::test_write_atomic_passes_lf_newline_to_text_mode`) enthält
    die geschriebene Datei kein `\r`.
  - **AC-2.2** Modus-Änderung dokumentiert: `CHANGELOG.md`-Eintrag von PR 2 nennt »Hook-Scaffold
    (`--create-hook`) und Managed-Indizes werden mit 0600 geschrieben«; ein Scaffold-Hook ist über die
    registrierte Form `bash <path>` weiterhin ausführbar (Test).
  - **AC-2.3** Idempotenz: Nach zweitem Sync ohne Quelländerung ist der Inhalt jeder der drei
    Index-Dateien byte-identisch zum ersten Lauf. (Die Indizes werden heute bei jedem Sync neu
    geschrieben, `hooks.py:634`, `hook_plugins.py:158`; ein `is_unchanged`-Guard ist nicht Teil dieses
    Fixes.)
- **Regressionstest:** `tests/test_newline_normalization.py::test_create_hook_writes_lf`,
  `::test_hook_managed_index_writes_lf`, `::test_hook_plugin_managed_index_writes_lf`,
  `::test_hook_lib_managed_index_writes_lf`, `::test_create_hook_runs_via_bash`,
  `::test_hook_managed_indices_idempotent` (Namen neu).

### #951 — `dod-push-check`-Tests nicht hermetisch, Fälle fehlen

- **Problem:** Testergebnis hängt von `AGENT_META_*` der Aufrufer-Shell ab; vier Fälle ungetestet.
- **Root-Cause:** `tests/test_dod_push_check_hook.py:_run_hook` (:42) übergibt kein `env` → erbt
  `AGENT_META_*`. Die übrigen Helfer bauen `dict(os.environ, …)` und räumen höchstens
  `AGENT_META_MAIN_BRANCH` ab: `_run_hook_failing_tests` (:308, nicht einmal das), `_assert_outcome`
  (:392-393), Inline-Lauf (:610-611), `_run_payload` (:833-834); `_run_hook_with_config` (:189) delegiert an `_run_hook`
  und erbt damit alles. Sie setzen bewusst `AGENT_META_TEST_COMMAND=false`/`AGENT_META_TEST_TIMEOUT=5`; Aufrufer
  übergeben Overrides per `env_extra` (z. B. :550 `AGENT_META_MAIN_BRANCH=develop`, :918 `PATH`).
  Git-Variablen der Aufrufer-Shell (`GIT_DIR`, `GIT_CONFIG_*`, globale/System-Config) werden ebenfalls
  geerbt.
- **Fix-Vertrag:** Ein gemeinsamer Env-Bereiniger im Testmodul, Reihenfolge:
  1. Basis = `os.environ` ohne alle `AGENT_META_*`, ohne `GIT_DIR`, `GIT_WORK_TREE`,
     `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_*`/`GIT_CONFIG_VALUE_*`, `GIT_CONFIG_PARAMETERS`.
  2. Git-Isolation: `GIT_CONFIG_GLOBAL=<tmp>/gitconfig` (bzw. `HOME=<tmp>`), `GIT_CONFIG_NOSYSTEM=1`.
  3. Helfer-Defaults (`AGENT_META_TEST_COMMAND`, `AGENT_META_TEST_TIMEOUT`, wo heute gesetzt).
  4. Aufrufer-Overrides (`env_extra`) zuletzt — damit bleiben :550 und die #954-Injektions-Tests
     möglich.
  Alle Run-Helfer nutzen ihn. Kein Hook-Code betroffen.
- **AC:**
  - **AC-2.4** Mit gesetztem `AGENT_META_MAIN_BRANCH=foo`, `AGENT_META_TEST_COMMAND=true`,
    `GIT_DIR=/nonexistent` und `GIT_CONFIG_PARAMETERS="'push.default=matching'"` in der
    Test-Umgebung liefern alle Helfer dasselbe Ergebnis wie ohne; explizite `env_extra`-Overrides
    wirken weiterhin.
  - **AC-2.5** `GIT_MAIN_BRANCH: develop` aus `project.yaml` → Push nach `develop` geblockt.
  - **AC-2.6** Tag und Branch gleichnamig `main` → Push auf Branch `main` geblockt.
  - **AC-2.7** `git -C <anderes Repo> push …` mit Argument ≠ `.` → Branch des Ziel-Repos maßgeblich.
  - **AC-2.8** Jeder der vier neuen Tests schlägt fehl, wenn die zugehörige Logik entfernt wird
    (Mutations-Check, im PR dokumentiert).
- **Regressionstest:** `tests/test_dod_push_check_hook.py::test_run_helpers_ignore_caller_agent_meta_env`,
  `::test_main_branch_from_project_yaml`, `::test_tag_branch_name_collision_main`,
  `::test_dash_c_other_repo` (Namen neu).

### #954 — ausgelassene Security-Re-Review-Checks (R2S-7)

- **Problem:** Die Sicherheitsaussage der Round-2-Fixes von `dod-push-check.sh` ist nicht vollständig
  belegt.
- **Root-Cause:** Re-Review abgebrochen, bevor diese Prüfungen liefen (Issue #954).
- **Fix-Vertrag:** Tests für die unten genannten Pfade; erwartetes Verhalten jeweils fail-closed
  (Block). Hook-Fixes sind **unbeziffert** — siehe Eskalationsregel (Risiko R1).
- **Ist (verifiziert, für R1 relevant):**
  - `git config --list -z` (`dod-push-check.sh:716`) läuft ohne rc-Prüfung und ohne eigenen Timeout;
    Kommentar: »Empty on error« → leere Config. Ob das zu einem Allow führt, klärt AC-2.10
    (potenzieller R1-Fall).
  - `git for-each-ref` (:289) ohne rc-Prüfung; leere Ref-Menge gilt laut Kommentar als »not tag-only
    (fail closed)«.
  - Zeitbudget: `CLASSIFY_BUDGET=20` (:236) per `timeout -k 2` um den gesamten Python-Klassifikator
    (:238-239); `git config`/`for-each-ref` laufen als Subprozesse **in** diesem Prozess, das Budget
    gilt also auch für sie. Überschreitung → rc 124 → Block mit `exceeded 20s` (:1069).
  - Inline-Präfix-Injektion ist schon getestet (`GIT_CONFIG_PARAMETERS=x git push` :757,
    `GIT_CONFIG_COUNT=1 … git p` :799). Neu sind nur geerbte Prozess-Env-Werte und Includes.
  - `read_config_var` (:135-) liefert bei Fehler `""` → `MAIN_BRANCH` fällt auf `main` zurück
    (ein konfigurierter `develop` wäre dann ungeschützt). Nicht in #954 genannt; als R1-Kandidat
    vermerkt, Test optional.
- **AC:**
  - **AC-2.9** Config-Injection über die **Prozess-Env** des Hooks (`GIT_CONFIG_COUNT`/
    `GIT_CONFIG_KEY_n`/`GIT_CONFIG_VALUE_n`, `GIT_CONFIG_PARAMETERS`, per `env_extra`) und über
    `include.path`/`includeIf` in der Repo-Config ändert die Klassifikation nicht zum Allow eines
    geschützten Pushes. Keine Duplikate zu :757/:799.
  - **AC-2.10** Fehlschlagender `git config` (PATH-Shim `git`, der nur für `config --list` rc 1
    liefert und sonst das echte `git` `exec`t) → Block eines geschützten Pushes. Langsamer
    `git config`: Budget = `CLASSIFY_BUDGET` = 20 s (verifiziert, siehe Ist). CI-Abdeckung über den
    vorhandenen `test_r2_3_classifier_over_budget_blocks` (:910, `timeout`-Stub rc 124); ein echter
    Langsam-Test (`git`-Shim mit `sleep 30` → Block mit `exceeded 20s`, ≥ 20 s Laufzeit) wird
    **einmalig manuell** ausgeführt und das Ergebnis im PR dokumentiert, nicht in CI.
  - **AC-2.11** Fehlschlagender `git for-each-ref` → Block.
  - **AC-2.12** `python3` fehlt bzw. PATH-Shim liefert Müll → Block (Abgleich mit vorhandenen
    #595-Tests, Duplikate vermeiden).
  - **AC-2.13** Matrix `push.default` ∈ {simple, current, upstream, nothing, matching}, je einmal in
    einem Repo mit Submodul: geschützter Push geblockt, Feature-Push erlaubt.
  - **AC-2.14** Test: Für jeden in `.agents/hooks/` versionierten Guard (`orchestrator-guard.sh`,
    `orchestrator-guard-impl.sh`, `repo-containment.sh`, `repo-containment-impl.sh`) ist die Datei
    byte-identisch zu `hooks/1-generic/<name>` nach Ersetzen von `{{AGENT_META_PROVIDER}}` durch den
    Provider-Namen. Provider = der Eintrag aus `ai-providers` der Projekt-Config
    (`.meta-config/project.yaml`), dessen `hooks_dir` in `config/ai-providers.yaml` `.agents/hooks`
    ist — heute `Gemini` (`config/ai-providers.yaml:157`; gerenderte Kopie trägt
    `AGENT_META_PROVIDER="Gemini"`); der Test ermittelt ihn aus beiden Dateien, nicht als Literal.
    Vergleichsbasis ist der Arbeitsbaum des PR-Branches, nicht `origin/main`
    (Abweichung vom Issue-Wortlaut: `origin/main` ist während des PRs ein bewegliches Ziel).
    `dod-push-check.sh` ist nur für Claude verteilt (`.claude/` gitignored) → nicht Teil des Tests,
    dort gilt AC-1.22.
  - **AC-2.15** 5-Mutations-Check der neuen Tests im PR dokumentiert; Laufzeiten der R2S-3-Tests
    (`test_r2_3_*`, R2S-3 = Befund »superlineare Klassifizierer-Laufzeit« aus
    `docs/reviews/2026-10-11-w2-b1-dod-push-check-review-findings.md:130`) unabhängig nachgemessen
    (best-of-3) und im PR festgehalten.
- **Regressionstest:** `tests/test_dod_push_check_hook.py::test_git_config_env_injection_*`,
  `::test_git_config_failure_blocks`, `::test_for_each_ref_failure_blocks`,
  `::test_python3_shim_garbage_blocks`, `::test_push_default_matrix` (parametrisiert) (Namen neu).
- **Rebaseline:** keiner geplant. Erzwingt ein Hook-Fix aus R1 eine Hook-Änderung, wird der
  Rebaseline in PR 2 nach R1 nachgezogen (Abweichung explizit im PR).

## PR 3 — `fix/config-contracts-placeholders`

### #1031 — 8 unkonsumierte Output-Contracts

- **Problem:** `handoff.output-not-consumed`, 8× (reproduziert 2026-10-29).
- **Root-Cause:** `config/role-defaults.yaml`: die 8 Literatur-Rollen deklarieren `output_contract` +
  `target_roles` (Key heißt `target_roles`, nicht `targets`), keine Zielrolle führt den Contract in
  `handoff.input_contracts`. Prüfer: `scripts/lib/consistency/handoff_contracts.py`
  (Schritt 2b). Kein Code-Fehler, Daten-Inkonsistenz.
- **Fix-Vertrag (Default-Regel: erste Rolle in `target_roles`):**

  | Produzent | Contract | Konsument (Default) | Handoff-Block beim Konsumenten |
  |---|---|---|---|
  | `memory-architect` | `memory-architecture-v1` | `rag-engineer` | vorhanden |
  | `context-engineer` | `context-budget-report-v1` | `agent-meta-manager` | vorhanden |
  | `red-team-agent` | `redteam-findings-v1` | `prompt-engineer` | vorhanden |
  | `chaos-engineer` | `chaos-experiment-v1` | `sre-engineer` | vorhanden |
  | `ux-researcher` | `ux-research-findings-v1` | `product-manager` | vorhanden, ohne `input_contracts` |
  | `privacy-compliance-officer` | `privacy-assessment-v1` | `ai-governance-engineer` | vorhanden |
  | `secrets-manager` | `secret-inventory-v1` | `devops-engineer` | **neu**, nur `input_contracts` |
  | `reproducible-builds-engineer` | `build-determinism-v1` | `devops-engineer` | (derselbe neue Block) |

  Hinweis: `privacy-compliance-officer` zielt auf `app-lifecycle-governor` (Issue schreibt
  `lifecycle-governor`, existiert nicht). Ein Handoff-Block ohne `output_contract` ist zulässig
  (verifiziert): Präzedenz `validator` (`config/role-defaults.yaml:403-408`, nur `input_contracts`,
  `validate_handoff`, `output_schema`); `handoff_contracts.py` wertet `output_contract` nur aus, wenn
  vorhanden (:70, :82, :99).
- **AC:**
  - **AC-3.1** `python3 scripts/consistency-check.py`: 0 `handoff.output-not-consumed`, keine neuen
    `handoff.*`-Findings.
  - **AC-3.2** Jeder der 8 Contracts steht in den `input_contracts` genau des Default-Konsumenten.
  - **AC-3.3** Render-Auswirkung geprüft: `delegation_table.py` filtert `input_contracts` nach aktiven
    Produzenten → `tests/fixtures/slimming-golden/orchestrator.md` kann sich ändern (**unverifiziert**);
    falls ja, im Rebaseline (AC-3.13) mit Begründung. Kein Hermes-Golden für das echte Repo (Tests
    nutzen synthetische Fixture).
- **Regressionstest:** `tests/test_consistency_checks.py::test_role_defaults_no_unconsumed_output_contracts`
  (Name neu; prüft das echte `config/role-defaults.yaml`).

### #983 — `TECH_STACK`, `AGENT_RULES`, `EXTERNAL_DOCS_LANGUAGE` ohne Filler

- **Problem:** Drei Platzhalter ohne Builder; `{{TECH_STACK}}` kann in `sharkord-release` leaken.
- **Root-Cause:**
  - `{{TECH_STACK}}`: `agents/2-platform/sharkord-release.md:142` (deploybar; :274 ist eine
    Doku-Tabelle). Kein Eintrag in `scripts/lib/config.py:_VARIABLE_FALLBACKS` (:197), nicht in
    `scripts/lib/consistency/placeholders.py:_BUILTIN_VARS` (:12).
  - `{{AGENT_RULES}}` (:79) und `{{EXTERNAL_DOCS_LANGUAGE}}` (:121, :175):
    `agents/1-generic/_reference-agent.md` (nicht deploybar). Namensdrift: Gegenstück
    `DOCS_LANGUAGE` existiert (Fallback `"Englisch"`, config.py:200); zu `AGENT_RULES` existiert kein
    Gegenstück.
  - Alle drei eingefroren in `placeholders.py:_UNKNOWN_TEMPLATE_RATCHET` (:277-279).
- **Fix-Vertrag:**
  - `"TECH_STACK": ""` in `_VARIABLE_FALLBACKS`; da es damit Builder-Variable wird, verlangt
    `placeholders.py:309-318` den Eintrag in `_BUILTIN_VARS` → dort ergänzen.
  - `_reference-agent.md`: `EXTERNAL_DOCS_LANGUAGE` → `DOCS_LANGUAGE`; `AGENT_RULES` aus der Liste
    entfernen (Default; Alternative: Escape per Placeholder-Escape-Syntax — Syntax **unverifiziert**).
    Agent-Version nach conventions-Skill bumpen.
  - `_UNKNOWN_TEMPLATE_RATCHET` wird leer (`frozenset()`), Kommentar angepasst.
  - `_reference-agent.md` steht in `tests/test_template_slimming_equivalence.py:_PARSE_INPUT_MIGRATED`
    (:327-329) → Test muss grün bleiben.
  - Hinweis: Eine »CLAUDE.md-Variablentabelle« (Projekt-Constraint) existiert nicht; es entstehen keine
    neuen Platzhalter, nur ein Fallback für einen bestehenden.
- **AC:**
  - **AC-3.4** `_UNKNOWN_TEMPLATE_RATCHET == frozenset()`.
  - **AC-3.5** Sync eines Projekts mit aktiver Rolle `sharkord-release` ohne `TECH_STACK`-Variable
    rendert kein `{{TECH_STACK}}`; mit gesetzter Variable deren Wert.
  - **AC-3.6** `_reference-agent.md` enthält weder `{{AGENT_RULES}}` noch `{{EXTERNAL_DOCS_LANGUAGE}}`;
    `tests/test_template_slimming_equivalence.py` grün.
  - **AC-3.7** `placeholders.builder-known-set`-Check ohne Findings für die drei Namen.
- **Regressionstest:** `tests/test_config_variable_fallbacks.py::test_tech_stack_falls_back_to_empty`,
  `tests/test_template_integrity_checks.py::test_unknown_template_ratchet_is_empty` (Namen neu;
  vorhandene Assertion `not _ph._is_family("TECH_STACK")` :126 prüfen).

### #1037 — `project.description` und ableitbare Variablen ohne Fallback

- **Problem:** 9-Provider-Sync mit `project: {name, description}` liefert literale Tokens
  (Issue: 95 `active-set.unresolved-placeholder`, 54 Doctor-WARNINGs). Positive Kontrolle laut Issue:
  dieselben Werte unter `variables:` lösen alles außer `{{PIPELINE_DETAIL_BLOCKS}}`.
- **Root-Cause:** `scripts/lib/config.py:_build_core_variables` (:1315; Projekt-Felder :1346-1349)
  liest aus `project` nur `prefix`/`short`/`name`. `PROJECT_GOAL`-Ableitung aus
  `PROJECT_DESCRIPTION` (:1467-1469) greift daher nie aus `project.description`. Schema
  `config/project-config.schema.json` → `properties.project`: `additionalProperties: false`,
  Properties nur `name`/`prefix`/`short` (verifiziert). `AGENT_META_REPO` fest `"Popoboxxo/agent-meta"` in `scripts/lib/setup.py:276/314`.
  Plattform-Kaskade prüft `project_vars`; leere Fallbacks sind dort unschädlich
  (`tests/test_build_variables_platform_cascade.py`).
- **Fix-Vertrag:**
  - `variables.setdefault("PROJECT_DESCRIPTION", project.get("description", ""))` (explizite
    `variables:` gewinnen), **vor** der `PROJECT_GOAL`-Ableitung.
  - `config/project-config.schema.json` `properties.project` um `description` (string) erweitern.
  - Leer-Fallbacks in `_VARIABLE_FALLBACKS`: `TEST_COMMANDS`, `TEST_COMMAND`, `BUILD_COMMAND`,
    `BUILD_COMMANDS`, `PLATFORM`, `RUNTIME`, `KEY_PATTERNS`, `ENTRY_POINT_PATTERN`, `DEV_STACK_RELOAD`
    (D7: `PLATFORM`/`RUNTIME` leer, kein Fehler). Registrierung in `_BUILTIN_VARS`, soweit nicht
    vorhanden.
  - Abgrenzung zum Gegenmuster `config.py:1403-1412` (`<VAR>_SET` + `{{#if <VAR>_SET}}`, #425): Das
    Muster gilt dort, wo `""` einen **irreführenden** Inhalt erzeugt (Pfad mit hängendem `/`). Bei den
    neun Variablen entsteht schlimmstenfalls ein leerer Wert bzw. leerer Code-Span (z. B.
    `release.md:106` ``**Test:** `{{TEST_COMMAND}}` ``) — kosmetisch, keine falsche Aussage; D7 legt
    »leer« für `PLATFORM`/`RUNTIME` fest. Alternative (verworfen für diese Welle): `_SET`-Flags +
    `{{#if}}` an allen ~37 Template-Stellen (u. a. `agents/1-generic/release.md`, `docker.md`,
    `templates/context/partials/project-metadata.md`, `templates/configs/*`) — größerer Diff und
    Render-Änderung; Folge-Issue möglich.
  - Nebenwirkung (benannt): `PROJECT_CONTEXT` fällt auf `PROJECT_DESCRIPTION` zurück
    (`config.py:1479-1480`). Mit dem Seed aus `project.description` erhält `PROJECT_CONTEXT` diesen
    Wert statt `""` → Render-Änderung, Teil des Rebaselines AC-3.13.
  - Standalone-Rendering unberührt: `scripts/lib/standalone.py:_standalone_variables` (:261) baut ein
    eigenes Dict aus `_IDENTITY_FALLBACKS` (:57, u. a. `TEST_COMMANDS` = »(not provided — …)«, :67) und
    ruft weder `_build_core_variables` noch `_VARIABLE_FALLBACKS` auf (Grep) → kein
    Reihenfolgekonflikt, der Standalone-Text bleibt.
  - `AGENT_META_REPO`-Fallback `"Popoboxxo/agent-meta"` aus **einer** Konstante, die auch
    `setup.py` (:276, :314) nutzt (D7). Ort der Konstante: Plan. URL-Literale in `standalone.py`,
    `hermes_export.py`, `admin-server.py`: Nicht-Ziel.
- **AC:**
  - **AC-3.8** `project.description: "X"` ohne `variables.PROJECT_DESCRIPTION` → `PROJECT_DESCRIPTION
    == "X"`, `PROJECT_GOAL == "X"` und `PROJECT_CONTEXT == "X"`; explizites
    `variables.PROJECT_DESCRIPTION` gewinnt.
  - **AC-3.9** Schema-Validierung akzeptiert `project.description`.
  - **AC-3.10** Ohne Konfig sind alle neun Fallback-Variablen `""`; `AGENT_META_REPO ==
    "Popoboxxo/agent-meta"`; kein Fehler, kein Exit ≠ 0.
  - **AC-3.11** 9-Provider-Sync mit `project: {name, description}`: kein
    `active-set.unresolved-placeholder` für die in #1037 genannten Tokens; `sync.py --doctor` ohne
    `unresolved-placeholder-in-output` für diese Tokens (`{{PIPELINE_DETAIL_BLOCKS}}` ausgenommen).
    Repro im Vorlauf **nicht** ausgeführt.
  - **AC-3.12** `setup.py` (:276, :314) und der `AGENT_META_REPO`-Fallback nutzen die gemeinsame
    Konstante; `grep -rn '"Popoboxxo/agent-meta"' scripts/` findet genau eine Stelle (die Konstante).
    URL-Formen (`https://github.com/Popoboxxo/agent-meta…`) sind ausgenommen (Nicht-Ziel).
- **Regressionstest:** `tests/test_build_variables_decomposition.py::test_project_description_seeds_variable`,
  `::test_explicit_project_description_variable_wins`,
  `tests/test_config_variable_fallbacks.py::test_derivable_variables_fall_back_empty`,
  `::test_agent_meta_repo_default` (Namen neu).

### PR-3-Querschnitt

- **AC-3.13** Genau ein Rebaseline für alle 9 Provider auf frischem `main` (nach Merge der übrigen
  PRs): `python tests/test_ac01_render_identity.py --write`, Log-Eintrag, `_FIXTURE_TREES`-Digests,
  ggf. `slimming-golden`; Versionen/`CHANGELOG.md` nach conventions-Skill. Erwartete Drift: aus
  #1031/#983/#1037 erklärbare Render-Änderungen **und** die abgeleiteten
  `.meta-config/generated-file-hashes.json`, `.meta-config/context-hashes.json` und Managed-Indizes
  der betroffenen Provider; Hook-Dateien oder nicht erklärbare Pfade sind unerwartet.

## PR 4 — `fix/admin-ui-network-and-doctor`

### #897 — `origin not allowed` im Netzwerkmodus

- **Problem:** Bei Wildcard-Bind scheitert jede Mutation aus dem Browser an `check_origin`.
- **Ist (verifiziert):** Issue-AC1/AC2 erledigt (`scripts/admin-server.py:973-985`: konkreter Bind-Host
  ist Origin-vertrauenswürdig, Hinweis in der Origin-Meldung). AC3 (hängendes Overlay) im Code
  behoben (`docs/ui/admin-ui.html:8411-8416` `finally: hideModal()`, Commit `ce13a6bf`/#956; der
  Issue-Kommentar sagt noch »offen«).
- **Root-Cause (Rest):** `scripts/admin-server.py:AdminServer.__init__` (:5653): bei Wildcard-Bind
  werden die per `socket.gethostbyname_ex` ermittelten Nicht-Loopback-Adressen (:5689-5695) nur als
  Hinweis ausgegeben, nicht an `effective_allowed_hosts` (:5673) angehängt. `check_origin` (:949)
  gibt bei `host header not allowed` (:992) keinen Hinweis. Hilfetext `--allowed-hosts` (:5929) sagt
  »Extends (does not replace)«, der Code ersetzt (:5673).
- **Fix-Vertrag:**
  - Extrahierter, socket-freier Helfer (Name Vorschlag:
    `_effective_allowed_hosts(host, cli_hosts, cfg_hosts, resolve) -> tuple[str, ...]`), weil
    `AdminServer.__init__` einen Socket bindet. Bei `host in WILDCARD_HOSTS`: erkannte
    Nicht-Loopback-Adressen werden dedupliziert, reihenfolgestabil angehängt; `OSError` → nichts
    angehängt, Hinweis wie bisher (`gethostbyname_ex` ist unvollständig → `--allowed-hosts` bleibt
    der Weg).
  - `gethostbyname_ex` liefert nur IPv4 (:5689). Bei `::`-Bind (in `WILDCARD_HOSTS`, :201) werden
    damit nur IPv4-Adressen ergänzt; der Startup-Hinweis sagt das ausdrücklich und verweist für
    IPv6-Adressen/Hostnamen weiter auf `--allowed-hosts` bzw. `admin-ui.allowed-hosts`. Kein
    `getaddrinfo`-Ausbau in dieser Welle.
  - `host header not allowed`-Meldung bekommt denselben Hinweis wie die Origin-Meldung.
  - `check_origin`-Logik unverändert; ein Origin wird **nie** aus dem Host-Header abgeleitet.
  - Hilfetext vs. Code: siehe Q5 (Default: Hilfetext an den Code anpassen, »replaces«).
  - `tests/test_admin_server.py:TestCheckOriginBindHost` (:2630) bleibt in den Assertions unverändert
    (prüft `check_origin` mit `DEFAULT_ALLOWED_HOSTS`); nur Docstring klärt die Absicht.
- **AC:**
  - **AC-4.1** Wildcard-Bind, Resolver liefert `["10.0.0.5"]` → `10.0.0.5` in den effektiven
    Hosts; `check_origin(origin="http://10.0.0.5:<port>", …)` wirft nicht.
  - **AC-4.2** Resolver wirft `OSError` → effektive Hosts = CLI bzw. Config bzw. Default, unverändert.
  - **AC-4.3** Konkreter Bind oder Loopback → keine Resolver-Adressen angehängt. Bei `::`-Bind enthält
    der Wildcard-Hinweis den Zusatz, dass nur IPv4 erkannt wird, und nennt `--allowed-hosts`.
  - **AC-4.4** `host header not allowed`-Meldung enthält `--allowed-hosts` und
    `admin-ui.allowed-hosts`.
  - **AC-4.5** Request mit `Host: evil:<port>` und `Origin: http://evil:<port>` wird weiterhin
    abgelehnt.
  - **AC-4.6** Hilfetext und Verhalten von `--allowed-hosts` stimmen überein (gemäß Q5).
- **Regressionstest:** `tests/test_admin_server.py::TestEffectiveAllowedHosts` (neu,
  AC-4.1–4.3), `::TestCheckOrigin::test_host_header_rejection_has_hint`,
  `::TestCheckOrigin::test_origin_never_derived_from_host_header`,
  `::test_allowed_hosts_help_matches_behavior` (Namen neu).

### #1034 — `rules-file-wrong-suffix` meldet Manifest-Dateien

- **Problem:** Copilot-Sync → 3 WARNINGs für `.github/instructions/.agent-meta-managed`,
  `-mcp`, `-tools`, Fix-Hinweis »umbenennen« würde den Managed-Block-Mechanismus brechen.
- **Root-Cause:** `scripts/lib/doctor_detectors.py:detect_path_exists` (:253) → `_glob_matches`
  (:240) globbt `*` und erfasst `.agent-meta-managed*`; `config/known-issues.yaml:201-206`
  (`rules-file-wrong-suffix`, `glob: "*"`) ohne Ausschluss. Geschwisterpfad derselben Klasse:
  `_files_in` (:88) → `target_files` → File-Size-Detektor `instruction-soft-cap-chars`.
- **Fix-Vertrag:** `_glob_matches` und `_files_in` schließen Dateinamen mit Präfix
  `.agent-meta-managed` aus (eine gemeinsame Prädikatsfunktion). `known-issues.yaml` unverändert.
- **Abwägung Code vs. Daten:** Datenlösung wäre `exclude_glob: ".agent-meta-managed*"` am Eintrag
  `rules-file-wrong-suffix` (`_glob_matches` unterstützt `exclude_glob` als einzelnes fnmatch-Muster,
  :248-251; Präzedenz `project-role-not-generated`, `known-issues.yaml:336`). Verworfen, weil sie nur
  diesen einen Eintrag und nur `_glob_matches` abdeckt: `_files_in` → `target_files` speist alle
  Inhalts-Detektoren (`detect_file_size` :169, `detect_regex` :215, `detect_yaml_key` :293/:302,
  `detect_toml_key` :315, `detect_json_schema` :344); jeder künftige Eintrag müsste den Ausschluss
  wiederholen. Gegenprobe: kein Eintrag in `config/known-issues.yaml` und kein Detektor in
  `scripts/lib/doctor*.py` referenziert `.agent-meta-managed` (Grep, 0 Treffer) → kein Detektor wertet
  Manifeste absichtlich aus. Restrisiko: ein künftiger Detektor, der Manifeste prüfen **will**, muss
  sie explizit per `target.path` adressieren (`target_files` gibt bei Datei-Pfad die Datei direkt
  zurück, :101 — davon unberührt, wenn das Prädikat nur in `_files_in`/`_glob_matches` greift).
- **AC:**
  - **AC-4.7** Negative Fixture mit den drei Manifest-Dateien → kein `rules-file-wrong-suffix`.
  - **AC-4.8** Positive Fixture (falsches Suffix) meldet weiterhin.
  - **AC-4.9** `instruction-soft-cap-chars` wertet `.agent-meta-managed*` nicht aus.
  - **AC-4.10** Echter Copilot-Sync + `sync.py --doctor` → 0 Treffer für die drei Manifeste
    (Repro im Vorlauf **nicht** ausgeführt).
- **Regressionstest:** Manifest-Dateien
  `tests/fixtures/doctor/rules-file-wrong-suffix/negative/.github/instructions/.agent-meta-managed`,
  `…/.agent-meta-managed-mcp`, `…/.agent-meta-managed-tools` (neben der vorhandenen
  `style.instructions.md`; das Fixture-Rules-Dir ist `.github/instructions/`). Ausgeführt über
  `tests/test_doctor_fixtures.py::test_ac38_seed_fixture_matches_expected_finding_count`
  (parametrisiert, ID `AC-38-rules-file-wrong-suffix-negative`; Negativfall verlangt
  `findings == []`, verifiziert :245-262);
  `tests/test_doctor_runner.py::test_files_in_skips_managed_manifests` (Name neu).

### #856 — zcode ZC-1 (Doku, wontfix documented)

- **Problem:** Workspace-Agent-Auto-Load ungelöst (Issue).
- **Ist:** `docs/providers/zcode.md:61-86` dokumentiert den AGENTS.md-Bootstrap bereits. Es fehlt nur
  die Entscheidungsnotiz.
- **Zweiter Issue-Teil (ZC-2, »commands capability under-claim«) — bereits behoben (verifiziert):**
  `config/provider-capabilities.yaml:509` (`commands: true … issue #807, UNDERCLAIM ZC-2 fixed`),
  `config/ai-providers.yaml:781-785`, `CHANGELOG.md:797-803` (#807), `docs/providers/zcode.md:52`.
- **Fix-Vertrag:** Entscheidungsnotiz in `docs/providers/zcode.md`: ZC-1 bleibt wontfix (documented);
  agent-meta schreibt nicht nach `~/.zcode/agents`, weil das Repo-Containment verletzt. Issue-Schließung
  als Plan-Task (D8), nicht ausführen; der Schließkommentar-Entwurf (Englisch) nennt ZC-1 =
  wontfix (documented, Verweis auf die Notiz) und ZC-2 = fixed in #807 (Verweis auf
  `provider-capabilities.yaml:509`). Schließen des gesamten Issues: Q7.
- **AC:**
  - **AC-4.11** `docs/providers/zcode.md` enthält die Notiz mit Begründung »Repo-Containment« und
    einen Verweis, dass ZC-2 mit #807 behoben ist.
- **Regressionstest:** keiner (D8: kein Code-Bug; D4 nicht anwendbar).

## Interface Contracts

| Datei:Symbol | Signatur | Fehlerpfade | Status |
|---|---|---|---|
| `hooks/1-generic/dod-push-check.sh` Block-Meldung (:1071) | stderr-Text `Protected branches: <dedup-Liste>.` | keine neuen | erweitert |
| `hooks/1-generic/orchestrator-guard-impl.sh:is_fork_bomb` | `(command: str) -> bool` | Laufzeit linear; Body-Fenster ohne `}` → `True`; Exception propagiert → Klassifikator rc ≠ 0 → exit 2 | erweitert |
| `hooks/1-generic/orchestrator-guard-impl.sh` Befehls-Klassifikator (`_GIT_SCAN_RAW`, :333–:846) | stdout eine Zeile `<none\|mutation\|destructive> <narrow\|broad> <none\|message\|file>` | rc ≠ 0 oder formatfremde/leere Ausgabe → stderr `command classifier failed rc=<n>, failing closed` + exit 2 | erweitert (bisher Fallback `none narrow none`) |
| `hooks/1-generic/repo-containment.sh` | stdin JSON → exit 0 \| 2 | Impl-rc ∉ {0,2} → exit 2 | erweitert |
| `hooks/1-generic/repo-containment-impl.sh` Bash-Detector | Kandidaten auf stdout, ein Pfad/Zeile | Detector-rc ≠ 0 → exit 2 | erweitert |
| `scripts/lib/io.py:write_atomic` | `(path: Path, content: str, mode: str = "w") -> None` | bestehend | unverändert (in `hooks.py`/`hook_plugins.py` schon importiert; vier neue Aufrufstellen: `create_hook`, drei Managed-Indizes) |
| `scripts/lib/hooks.py:create_hook` | Signatur unverändert | — | erweitert (LF via `write_atomic`, Modus 0600) |
| `tests/test_dod_push_check_hook.py` Env-Bereiniger | `(tmp: Path, extra: Optional[dict] = None) -> dict[str, str]` (Py3.9-kompatibel, CI-Matrix 3.9/3.12) (Name/Signatur im Plan): ohne `AGENT_META_*`/`GIT_DIR`/`GIT_WORK_TREE`/`GIT_CONFIG_*`, mit isolierter Git-Config, dann Helfer-Defaults, dann `extra` | — | neu (Test-Code) |
| `config/role-defaults.yaml` `handoff.input_contracts` | Liste von Contract-IDs | `handoff.*`-Findings | erweitert (Daten) |
| `scripts/lib/config.py:_VARIABLE_FALLBACKS` | `dict[str, str]` | — | erweitert |
| `scripts/lib/config.py:_build_core_variables` | Signatur unverändert | — | erweitert (`PROJECT_DESCRIPTION`) |
| `scripts/lib/consistency/placeholders.py:_BUILTIN_VARS` / `_UNKNOWN_TEMPLATE_RATCHET` | `frozenset[str]` | Ratchet darf nur schrumpfen | erweitert / geleert |
| `scripts/admin-server.py:_effective_allowed_hosts` | `(host, cli_hosts, cfg_hosts, resolve) -> tuple[str, ...]` (Vorschlag) | `OSError` aus `resolve` → keine Ergänzung | neu |
| `scripts/admin-server.py:check_origin` | unverändert | `SecurityError`-Text bei Host-Header erweitert | erweitert (nur Meldung) |
| `scripts/lib/doctor_detectors.py:_glob_matches` / `_files_in` | `(det, env, tgt) -> list` / `(directory: Path, suffix: Optional[str] = None) -> list` | — | erweitert (Ausschluss) |

## Datenfluss

- **Push-Guard:** Bash-Tool → `dod-push-check.sh` → `MAIN_BRANCH` (Env > Config > `main`) →
  Python-Klassifikator (`PROTECTED`) → Verdikt → bei Block dedup-Meldung auf stderr.
- **Orchestrator-Guard:** Bash-Tool → `orchestrator-guard.sh` → `-impl.sh` → Klassifikator
  (`is_fork_bomb(strip_quoted(command))` linear, Tokenizer) → Ausgabe validiert (Absturz/Fremdformat →
  exit 2) → BOM-/Destructive-/Mutation-Gate → exit 0/2 → Wrapper normalisiert.
- **Repo-Containment:** Tool-Aufruf → `repo-containment.sh` → `-impl.sh` → (Bash) Python-Detector →
  Kandidaten → `containment_verdict` → exit 0/2; Detector-Fehler → exit 2 → Wrapper normalisiert
  (`PIPESTATUS[1]`).
- **Hook-Deploy:** `sync.py` → `hooks.py`/`hook_plugins.py` → Hook-Skripte über `write_checked` →
  `write_atomic` (unverändert, `hooks.py:555`, `hook_plugins.py:132/328`); Managed-Indizes
  (`hooks.py:635`, `hook_plugins.py:160/348`) neu über `write_atomic` (LF, 0600) →
  `.claude/hooks/`, `.agents/hooks/` u. a. Kein `chmod`; Ausführung als `bash <path>`
  (`hooks.py:147-148`).
- **Hook-Scaffold:** `sync.py --create-hook <name>` → `create_hook` (`hooks.py:679`) → neu
  `write_atomic` (LF, 0600) → `.claude/hooks/<name>.sh` (nie überschrieben, nicht im Index).
- **Variablen:** `project.yaml` (`project.*`, `variables:`) → `_build_core_variables` →
  `PROJECT_DESCRIPTION` (setdefault) → `_VARIABLE_FALLBACKS` (:1390) → `PROJECT_GOAL` (:1467) →
  `PROJECT_CONTEXT` (:1479) → Renderer →
  Placeholder-Checks (`_BUILTIN_VARS`, Ratchet) → generierter Output.
- **Handoff:** `role-defaults.yaml` → `handoff_contracts.py` (2a/2b/2c) und `delegation_table.py`
  (Orchestrator-Render).
- **Admin-Server:** CLI/Config/Default → `_effective_allowed_hosts` (+ Resolver bei Wildcard) →
  `AdminRequestHandler.allowed_hosts` → `check_origin` je Mutation.
- **Doctor:** `known-issues.yaml` → `detect_path_exists` → `_glob_matches`/`_files_in` (ohne
  Manifeste) → Findings.

## Acceptance Criteria

AC-Definitionen stehen in den PR-Abschnitten. Index:

| PR | Bug | AC-IDs |
|---|---|---|
| PR 1 | B1 #1033 | AC-1.1 – AC-1.4 |
| PR 1 | B2 #943(a)(m) | AC-1.5 – AC-1.11 |
| PR 1 | B2 Geschwister: Klassifikator fail-closed | AC-1.12, AC-1.13 |
| PR 1 | B3/B4 #944 SR-B-17 + `\|\| true` | AC-1.14 – AC-1.17 |
| PR 1 | #944 SR-B-19 (optional) | AC-1.18, AC-1.19 |
| PR 1 | Querschnitt | AC-1.20 – AC-1.22 |
| PR 2 | B5 #961-Rest | AC-2.1 – AC-2.3 |
| PR 2 | B6 #951 | AC-2.4 – AC-2.8 |
| PR 2 | B7 #954 | AC-2.9 – AC-2.15 |
| PR 3 | B8 #1031 | AC-3.1 – AC-3.3 |
| PR 3 | B9 #983 | AC-3.4 – AC-3.7 |
| PR 3 | B10 #1037 | AC-3.8 – AC-3.12 |
| PR 3 | Querschnitt | AC-3.13 |
| PR 4 | B11 #897 | AC-4.1 – AC-4.6 |
| PR 4 | B12 #1034 | AC-4.7 – AC-4.10 |
| PR 4 | B13 #856 | AC-4.11 |

Umnummerierung gegenüber dem Review-Stand (alt → neu): AC-1.4 → AC-1.5, AC-1.5 → AC-1.6,
AC-1.6 → AC-1.8, AC-1.7 → AC-1.9, AC-1.8 → AC-1.10, AC-1.9 → AC-1.14, AC-1.10 → AC-1.15,
AC-1.11 → AC-1.16, AC-1.12 → AC-1.17, AC-1.13 → AC-1.18, AC-1.14 → AC-1.19, AC-1.15 → AC-1.20,
AC-1.16 → AC-1.21. Neu: AC-1.4, AC-1.7, AC-1.11, AC-1.12, AC-1.13, AC-1.22. Inhaltlich ersetzt bei
gleicher ID: AC-2.2, AC-2.3; neu formuliert: AC-2.4, AC-2.9, AC-2.10, AC-2.14, AC-2.15, AC-3.8,
AC-3.12, AC-4.3, AC-4.11.

Für jede PR gilt zusätzlich: `python3 scripts/sync.py --validate` und die betroffenen Testmodule grün;
neue Tests sind vor dem Fix rot (TDD).

## Merge-Reihenfolge und Abhängigkeiten

1. **PR 0a/0 Housekeeping** (nur Text-Entwürfe; Ausführung nur nach ausdrücklicher Freigabe). Q1 muss
   vor PR-1-Start entschieden sein (bestimmt »Closes« vs. »Refs«).
2. **PR 1** (D3) — zuerst; Hook-Dateien, Versionen, AC-01-Rebaseline.
3. **PR 2** — nach PR 1: teilt `hooks/1-generic/dod-push-check.sh` (#1033 vs. mögliche #954-Fixes),
   `tests/test_dod_push_check_hook.py`, `CHANGELOG.md`.
4. **PR 4** — nach PR 1; dateidisjunkt zu PR 2 (bis auf `CHANGELOG.md`; `VERSION` ändert sich nur in Release-PRs, nicht in PR 1–4), parallel
   entwickelbar, seriell gemergt.
5. **PR 3** — zuletzt: größter Rebaseline (alle 9 Provider) auf frischem `main` nach Merge von PR 1, 2, 4.

Konfliktdateien: `tests/fixtures/ac01-baseline/hashes.json` (enthält Hook-Dateien Claude + Gemini),
`tests/test_opencode_v2_surface.py:_FIXTURE_TREES`, `CHANGELOG.md`. Regel: Rebaseline immer auf
frischem `main` nach Merge des jeweils vorigen PRs, nie per Merge-Konfliktauflösung.

## Begründung des 4-PR-Schnitts

- **PR 1** bündelt die Fail-open-Fixes in Hooks (Security-Priorität, D3) und braucht genau einen
  Rebaseline, weil Hook-Dateien in `hashes.json` stehen.
- **PR 2** ändert Deploy-Code und Tests, aber keinen Render-Output (kein Rebaseline geplant); getrennt
  von PR 1, damit der Security-Fix nicht vom offenen Umfang von #954 (R1) blockiert wird.
- **PR 3** ändert Konfig-Daten und Variablen-Builder mit Wirkung auf alle Provider; ein gemeinsamer
  Rebaseline für #1031/#983/#1037 statt drei.
- **PR 4** ist dateidisjunkt (Admin-Server, Doctor, Doku) und rebaseline-frei (Annahme,
  verifiziert: `tests/fixtures/ac01-baseline/hashes.json` enthält keinen `docs/providers`-Pfad, `zcode.md` wird nicht gerendert).
- Abweichung vom Brief: keine im Schnitt. Inhaltliche Abweichungen aus dem Vorlauf: Env-Variable
  `AGENT_META_MAIN_BRANCH` statt `GIT_MAIN_BRANCH` (#1033-Tests); `{0,63}`/Eingabe-Kappen ersetzt durch
  Lookbehind + Body-Fenster mit Block bei Erschöpfung (#943); Klassifikator-Fail-open als
  Geschwisterpfad in PR 1 aufgenommen (nicht per D6 vertagt, weil derselbe Python-Block wie
  `is_fork_bomb` ohnehin geändert wird und Version-Bump/Rebaseline schon anfallen); #961 betrifft
  Scaffold + Indizes, nicht den Hook-Deploy; D5 gegenstandslos; #897-AC1–AC3 schon erledigt.

## Risiken

- **R1 — #954-Eskalationsregel:** Neue #954-Tests können Fail-open-Lücken in `dod-push-check.sh`
  aufdecken. Regel: (a) Ein solcher Test wird nie per `skip`/`xfail` stillgelegt. (b) Fix im selben
  PR nur, wenn er auf eine Funktion/einen Zweig von `dod-push-check.sh` begrenzt ist und erlaubte
  Pushes nicht ändert; dann Version-Bump + Rebaseline in PR 2 mit Vermerk. (c) Sonst Stopp: Befund an
  den User, Folge-Issue-Entwurf, PR 2 wird ohne den betroffenen Test nicht gemergt, bis der User
  entscheidet (Fix in PR 2, eigener PR oder Aufteilung).
- **R2 — Verhaltensänderung `repo-containment` und Orchestrator-Guard:** Fail-closed bei Detector-
  bzw. Klassifikator-Fehler kann bisher durchgelassene Bash-Aufrufe blocken (z. B. kaputtes
  `python3`); ein reproduzierbarer Klassifikator-Absturz blockt **jeden** Bash-Aufruf, auch mit
  `git`-Sentinel. Gewollt (Verfügbarkeit < Fail-closed); Meldung muss den Grund und rc nennen.
- **R3 — Body-Fenster #943:** Fehlalarm-Klasse = **jede** Funktionsdefinition (`name() {` irgendwo im
  ungequoteten Befehlstext, auch in einem ungequoteten Heredoc-Body), deren erste 1024 Body-Zeichen
  nach `strip_quoted` kein `}` enthalten. Nur ein **ungequotetes** `}` schließt das Fenster:
  `strip_quoted` (`orchestrator-guard-impl.sh:712`) entfernt Einfach-/Doppelquote-Spannen vollständig,
  ein gequotetes `"${x}"` zählt also nicht; ungequotetes `${x}` oder eine verschachtelte `{ … }`
  schließen es. Wirkung: **harter Block ohne Ausweg über den `git`-Sentinel** — das Destructive-Gate
  (:872-878) greift unabhängig vom Sentinel; Auswege sind nur Ausführung durch den Nutzer oder
  Umschreiben des Befehls (Funktion kürzen/aufteilen, Skript als Datei statt inline). Die Block-Meldung
  nennt die Fenstergrenze (AC-1.10). Kein Fail-open-Pfad mehr. Alternative bei Ablehnung: Q3.
- **R4 — Datei-Modus #961:** Hook-Scaffold (`--create-hook`) und die drei Managed-Indizes werden
  durch `mkstemp` mit 0600 statt umask-Modus (typisch 0644/0664) geschrieben; für Mehrbenutzer-
  Checkouts liest ein anderer Nutzer die Indizes nicht mehr. Kein Exec-Bit betroffen.
- **R5 — Wildcard-Allowlist #897:** Auto-Ergänzung erweitert die Origin-Allowlist um eigene Adressen
  des Hosts; Token-Pflicht für Nicht-Loopback bleibt (:5675-5681).
- **R6 — #945 nicht vorgezogen:** PR 1 erweitert Guard-Tests ohne die Isolation/CI-Timeouts aus #945.
  Gemindert: Funktions-AC sind Skalierungs-AC (Verhältnis, best-of-3, AC-1.5/AC-1.6) mit großzügiger
  absoluter Obergrenze; die e2e-AC (AC-1.9, < 2 s) hat Faktor ≈ 2,5 Abstand zum Altwert und ist die
  einzige absolute Grenze mit Restrisiko. Kalibrierung: AC-1.11. Entscheidung: Q6.
- **R7 — Validator-Fehlklassifikation:** `spec_plan.py` prüft diese `*-spec.md` als Plan
  (`_DESIGN_RE` :50) → mögliche Warnungen zu Plan-Pflichtsektionen; nicht behoben (Nicht-Ziel).
- **R8 — Issue-Zustand (Befund A):** Geschlossene Issues mit nicht existierenden Fix-Commits;
  ohne Q1-Entscheidung droht fehlerhafte Traceability.

## Offene Fragen

| ID | Frage | Default | Entscheidung bis |
|---|---|---|---|
| Q1 | Geschlossene, aber im Code nicht behobene Issues (#1033, #943, #944, #961, #951, #954, #1031, #983, #1037, #1034): Reopen oder neue Issues? | Reopen-Kommentar-Entwurf je Issue (Englisch, Plan-Task PR 0a); bis dahin »Refs« in PRs | vor PR-1-Start, durch User |
| Q2 | D5 formal aufheben? | Ja; nur die Rebaseline-Regel bleibt | vor PR-3-Start, durch User |
| Q3 | Fix-Vertrag #943: (a) Lookbehind-Header + Body-Fenster 1024, Fenster ohne `}` → **Block**; (b) wie (a), aber Fenster ohne `}` wird als Body geprüft (fail-open für Self-Pipe nach > 1024 Zeichen); (c) `{0,63}` + Eingabe-Kappung (verfehlt Laufzeitziel, fail-open bei Namen > 64 bzw. hinter der Kappe)? | (a) — fail-closed, Fehlalarm-Grenze R3. Prototyp (a) gemessen 2026-10-29, Py 3.13, best-of-3: 300/600 KB Bezeichner 2,3/4,2 ms; `"f(){ x} "` × 60k/120k 108/212 ms (linear); Fälle aus AC-1.7/AC-1.8 erfüllt | vor PR-1-Implementierung, durch User |
| Q4 | #897: »Closes« oder »Refs«? | »Closes #897« nach Fix | vor PR-4-Beschreibung, durch User |
| Q5 | `--allowed-hosts`: Hilfetext an Code anpassen (»replaces«) oder Code an Hilfetext (»extends«)? (zusätzlich zu Q1–Q4) | Hilfetext anpassen (keine Verhaltensänderung) | vor PR-4-Implementierung, durch User |
| Q6 | #945 (Guard-Test-Isolation, CI-Timeouts) vor PR 1 vorziehen? | Nein — Timing-AC sind als Skalierungs-AC robust (AC-1.5/AC-1.6/AC-1.11), R6 | vor PR-1-Start, durch User |
| Q7 | #856 nach PR 4 vollständig schließen (ZC-1 wontfix documented, ZC-2 fixed in #807)? | Ja, ein Schließkommentar mit beiden Verweisen (Plan-Task, nicht ausführen) | vor PR-4-Beschreibung, durch User |

## Trace-Anker

spec-id: SPEC-bugfix-wave-3
