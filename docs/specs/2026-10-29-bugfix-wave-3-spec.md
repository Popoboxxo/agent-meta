# Bugfix-Welle 3 — Spec (Rest-Welle)

> Status: Entwurf
>
> spec-id: SPEC-bugfix-wave-3
>
> **Revision:** 3.1 (2026-10-29) — ersetzt Revision 2, siehe »Änderungslog«.
> **Betroffener Bereich:** Fork-Bomb-Scanner (`hooks/1-generic/lib/hook_common.sh`), Destructive-Gate
> (`hooks/1-generic/orchestrator-guard-impl.sh`), Regel »Bekannte Grenzen« (`rules/1-generic/branch-guard.md`),
> Managed-Index-Schreibpfade (`scripts/lib/hooks.py`, `scripts/lib/hook_plugins.py`),
> Admin-Server-Meldungen/Hilfetext/Schema (`scripts/admin-server.py`, `docs/howto/admin-ui-remote-access.md`,
> `config/project-config.schema.json`), zcode-Provider-Doku (`docs/providers/zcode.md`).
> **Umfang:** 4 Restpunkte (R1–R4) in 2 PRs (PR A, PR B). Alle übrigen Bugs der Welle sind mit
> PR #1038 auf `main` (siehe »Stand nach PR #1038«).
> **Nicht in diesem Dokument:** Implementierung, Commits, Issue-Änderungen, Plan
> (`docs/plans/2026-10-29-bugfix-wave-3-plan.md`).
> **Belege:** Datei:Zeile beziehen sich auf `origin/main` = `3e340690` (Merge PR #1038), Branch
> `docs/bugfix-wave-3-spec-plan` (nur Spec/Plan zusätzlich). Zeilennummern driften, maßgeblich
> sind die Symbole.

## Änderungslog

| Rev. | Datum | Änderung | Grund |
|---|---|---|---|
| 1 | 2026-10-29 | 13 Bugs (B1–B13) in PR 1–4 + PR 0/0b Housekeeping, Basis `043d29a4`. | Analysebericht 2026-10-28, Vorlauf 2026-10-29. |
| 2 | 2026-10-29 | Umbau auf Rest-Welle: PR 1–4 und PR 0/0a/0b entfallen; neu PR A (R1) und PR B (R2–R4). AC neu nummeriert (AC-A.n, AC-B.n). Befund A (»Fix-Commits existieren nicht«) gestrichen. Q1/Q2 gegenstandslos, Q3 durch neuen R1-Vertrag ersetzt. Verifikation der erledigten Bugs als eigener Abschnitt. | PR #1038 hat B1, B2 (bis auf Restlücke), B3, B4, SR-B-19, B6–B10, B12 und den `create_hook`-Teil von B5 nach `main` gebracht; die in Rev. 1 als fehlend gemeldeten Commits `587e8684`, `c85ee04e`, `ebfa789b`, `24233481`, `26d2affa`, `63b12bde`, `af9abe9e`, `f9c33165` existieren jetzt (`git log -1 <hash>`, geprüft 2026-10-29). |
| 3 | 2026-10-29 | Q3-Default (a) → (b) (Name exakt, Body fail-closed); AC-A.1/A.2/A.3/A.5/A.7/A.8/A.9 angepasst; neu **AC-A.10** (»Bekannte Grenzen« in `rules/1-generic/branch-guard.md`) und **Q10** (Body endet am ersten `}`, Folge-Issue); Variante (a) wird Alternative, Variante (i) notiert. R3 um `config/project-config.schema.json` (»Extends«, »host:port«) erweitert, AC-B.7 verschärft (kein `Additional allowed`, Beispiele mit Loopback-Hinweis). AC-B.1 »enthält«, AC-B.3 mit zwei neuen Charakterisierungstests. AC-A.9-Drift aus Rebaseline-Logs und Matrix-Render belegt (13 statt »4 + unverifiziert«). | Review-Findings S-1…S-10 zu Rev. 2; Nachmessung 2026-10-29 (Py 3.13): `f(){ : ${x}; f|f& };f` und `f(){ { :; }; f|f& };f` → `False` (heute und unter (b)). |
| 3.1 | 2026-10-29 | Minor-Findings: Drift-Zahlen als `13 + k` (k ∈ {0, 6}); AC-A.10-Zielwert ≥ 1 Treffer; Q3 (c) 11 bzw. 13 Einträge; R3-Schema-Bullet (Auto-Fill-Satz ersetzt); RK-1/RK-5 präzisiert; Entscheidungsregister »Status Rev. 3«. | Review Rev. 3 (M1–M6, INFO-1…6). |

Überholt aus Rev. 1 (nicht mehr gültig): Abschnitte »Scope-Befund A«, »PR 1«–»PR 4«, »Begründung
des 4-PR-Schnitts«, Fix-Vertrag #943 mit Lookbehind-Regex und Body-Fenster 1024 (die gemergte
Implementierung ist ein manueller Linear-Scan mit Grenzen 64/512), Auto-Ergänzung erkannter Adressen
bei Wildcard-Bind (#897, nicht umgesetzt, nicht mehr im Scope), Risiken R1 (#954-Eskalation), R6,
R8 der Rev. 1.

## Problem

Nach PR #1038 bleiben vier echte Restpunkte:

- **R1 — Fork-Bomb-Scanner fail-open an seinen Grenzen (#943-Rest):** `is_fork_bomb`
  (`hooks/1-generic/lib/hook_common.sh:722`) ist linear, überspringt aber jede Funktionsdefinition
  mit einem Namen > 64 Zeichen (`_MAX_FUNC_NAME`, :437, :743-747) und jede, deren erstes `}` nicht
  innerhalb von 512 Zeichen nach `{` liegt (`_MAX_FUNC_BODY`, :438, :755-757: `continue`). Gemessen
  2026-10-29 (Py 3.13, Funktionsebene, Eingabe nach `strip_quoted`):
  - `"b"*70 + "(){ " + "b"*70 + "|" + "b"*70 + "& };" + "b"*70` (289 Zeichen) → `False`
  - `"f(){ " + "x"*520 + " f|f& };f"` (534 Zeichen, Body ≈ 527) → `False`
  - `"f(){ " + "x"*980 + " f|f& };f"` (994 Zeichen, Body ≈ 987) → `False`
  - Kontrolle: Name mit 64 Zeichen → `True`; `:(){ :|:& };:` → `True`.
  Eine echte Fork-Bomb passiert damit das Destructive-Gate (Allow statt Block).
  **Weitere Lücke (außerhalb des R1-Vertrags, Q10):** der Body endet am **ersten** `}` (:755,
  `command.find('}', …)`, keine Verschachtelung). `f(){ : ${x}; f|f& };f` und
  `f(){ { :; }; f|f& };f` → `False` (gemessen 2026-10-29, Funktionsebene nach `strip_quoted`; auch mit
  dem Prototyp (b) `False`). Unabhängig von Q3 fail-open.
- **R2 — Managed-Indizes ohne LF-Garantie (#961-Rest):** drei Schreibpfade nutzen weiter
  `Path.write_text` ohne `newline=` und schreiben unter Windows CRLF:
  `scripts/lib/hooks.py:635` (`sync_hooks`, Hook-Index), `scripts/lib/hook_plugins.py:160`
  (`sync_release_gates`, Release-Gate-Index), `scripts/lib/hook_plugins.py:348` (`sync_hook_lib`,
  Lib-Index). `create_hook` ist bereits umgestellt (`hooks.py:712`, `ebfa789b`).
- **R3 — Admin-Server-Meldung, Hilfetext und Schema (#897-Rest):** `AuthService.check_origin`
  (`scripts/admin-server.py:948`) wirft bei falschem Host-Header `host header not allowed: '…'` (:992)
  ohne Handlungshinweis (die Origin-Meldung :982-986 hat ihn). Der Hilfetext von `--allowed-hosts`
  (:5926-5929) sagt »Additional allowed …« und »Extends (does not replace) the default loopback set«,
  der Code ersetzt (`AdminServer.__init__`, :5673: CLI > Config > Default; Config ersetzt ebenso, :547).
  Dieselbe Falschaussage steht in `docs/howto/admin-ui-remote-access.md:62` (»Additional allowed«,
  »**Extends**«) und `:166`, sowie in `config/project-config.schema.json:1927`
  (`admin-ui.allowed-hosts`: »List of host:port origins … Extends the default loopback set«). »host:port«
  ist ebenfalls falsch: der Code hängt den Port selbst an (`f"http://{h}:{bind_port}"` :980, `f"{h}:{bind_port}"`
  :988), erwartet also reine Hosts.
- **R4 — zcode ZC-1 ohne Entscheidungsnotiz (#856):** `docs/providers/zcode.md` beschreibt den
  AGENTS.md-Bootstrap (:61-86), nennt aber nicht die Entscheidung, dass ZC-1 wontfix (documented)
  bleibt (Grep `ZC-1|wontfix` leer). Kein Code-Bug (D8).

## Ziel

- R1: Das Destructive-Gate prüft Funktionsnamen exakt (ohne Längengrenze) und ist an der Body-Grenze
  fail-closed (Default-Vertrag Q3 (b)), Laufzeit bleibt linear; die Body-Grenze, die daraus folgende
  Fehlalarm-Klasse und die verbleibende `}`-Lücke (Q10) sind dokumentiert und in der Block-Meldung bzw.
  in »Bekannte Grenzen« erkennbar.
- R2: Alle drei Managed-Index-Schreibpfade schreiben über `scripts/lib/io.py:write_atomic` (LF).
- R3: Die Host-Header-Ablehnung nennt den Ausweg; Hilfetext und How-to beschreiben das tatsächliche
  Verhalten von `--allowed-hosts` (Q5).
- R4: `docs/providers/zcode.md` enthält die ZC-1-Entscheidungsnotiz.
- Je Code-Restpunkt (R1–R3) mindestens ein vorher roter Regressionstest (D4); R4 ohne Test (D8).
- Höchstens ein AC-01-Rebaseline (nur PR A), auf frischem `main`.

## Nicht-Ziele

- Erneute Arbeit an den bereits behobenen Bugs (B1, B2 außer Restlücke, B3, B4, SR-B-19, B5
  `create_hook`, B6–B10, B12) — nur Verifikationsnachweis, keine Tasks.
- #945 (Guard-Test-Isolation, CI-Timeouts) — Vorziehen siehe Q4.
- #1032 (Gemini/Antigravity `hooks.json` cwd-abhängig), #1007 (Plan B), #1035 (NOT_PLANNED).
- Bash-Form `function NAME { … }` ohne `()` — `is_fork_bomb` sucht nur `(` (:727), erkennt diese Form
  nie; vorbestehende Lücke außerhalb R1, siehe Q7.
- Fix der `}`-Lücke (Body endet am ersten `}`, `${x}`/verschachtelte Gruppen, Q10): in PR A nur
  dokumentiert (AC-A.10), Fix per Folge-Issue durch den User (Text-Entwurf im Plan-Status).
- Auto-Ergänzung per `gethostbyname_ex` erkannter Adressen bei Wildcard-Bind (Rev. 1, AC-4.1–4.3):
  nicht umgesetzt; der vorhandene Startup-Hinweis mit Adressen (`admin-server.py:5684-5695`) bleibt.
- Die übrigen `write_text`-Aufrufe ohne `newline=` in `scripts/` (u. a. `scripts/lib/skills.py:85`,
  ebenfalls ein Managed-Index) — gleiche Fehlerklasse, Folge-Issue.
- Abdeckung von `lib/` durch `check_stale_deployed_hooks` (siehe Risiko RK-2) — Folge-Issue.
- Bugfix des Spec/Plan-Validators: `scripts/lib/consistency/spec_plan.py` klassifiziert nur
  `*-design.md` als Spec (`_DESIGN_RE` :50); diese `*-spec.md` wird als Plan geprüft. Nur erwähnt.
- Ausführen von Issue-Änderungen (Schließen, Reopen, Neuanlage) durch Agenten.

## Entscheidungsregister

Bindende User-Entscheidungen vom 2026-10-29, Status nach PR #1038.

| ID | Entscheidung | Status Rev. 3 |
|---|---|---|
| D1 | Scope: alle 4 PRs / 13 Bugs. | **Neu bewertet:** 9 der 13 Bugs sind auf `main`; Scope = Rest-Welle R1–R4 in PR A/PR B. |
| D2 | Schließ-Kandidaten #948, #950, #952, #953, #207, #534, #865, #962; #961/#971 erst nach Fix/Verifikation; #192 bleibt offen. | #948/#950/#952/#953 geschlossen. #207/#534/#865/#962 offen — **schließt der User selbst** per `! gh issue close`. #953-Folge-Issue legt der User an (Body `.tmp/issue-953-followup.md`). #961 geschlossen (R2 = Rest, »Refs«). #971 offen (Kriterium fehlt, Q8). #192 bleibt offen. Kein Agent-Task. |
| D3 | Hooks-PR zuerst, #897 danach. | Hooks-Härtung mit PR #1038 gemergt. Für die Rest-Welle: PR A (Hook) wird vor PR B gemergt; Entwicklung parallel (dateidisjunkt bis auf `CHANGELOG.md`). Die in der Analyse als »optional D3« bezeichnete `--allowed-hosts`-Frage (ersetzt vs. erweitert) ist **nicht** dieses D3, sie steht als Q5. |
| D4 | Pro Bug mindestens ein Regressionstest. | Gilt für R1–R3; R4 nach D8 ohne Test. |
| D5 | PR 1/2/4 vor Plan A, PR 3/#1036 danach; Rebaseline auf frischem `main`. | **Gegenstandslos** (Plan A und PR #1038 gemergt). Weiter gültig: Rebaseline nur auf frischem `main`, höchstens einmal je PR. |
| D6 | Epic-Reste #943/#944 → Folge-Issues mit Spec; PRs nutzen »Refs«. | #943/#944 sind geschlossen. PR A nutzt `Refs #943`; kein Reopen (Q9). Weitere Epic-Reste: in dieser Spec nicht erhoben. |
| D7 | #1037: `PLATFORM`/`RUNTIME` ohne Konfig leer; `AGENT_META_REPO` aus Default-Repo. | Mit `63b12bde` **abweichend** umgesetzt: ohne Quelle bleibt die Variable undefiniert (kein Leer-Fallback), `AGENT_META_REPO` aus `.gitmodules`-URL bzw. Git-Remote (`CHANGELOG.md` [Unreleased] »Derived defaults«). Ob `PLATFORM`/`RUNTIME` betroffen sind: **unverifiziert**. Nicht Teil der Rest-Welle. |
| D8 | #856: Doku + wontfix (documented). | R4 in PR B; Schließen durch den User nach Merge (Q6). |

Closing-Keywords je Issue einzeln (»Closes #a«, »Closes #b«) — nur die erste Nummer einer Kommaliste
schließt automatisch. Für bereits geschlossene Issues gilt »Refs«.

## Stand nach PR #1038 (Verifikationsnachweis)

Methode: Grep/Read gegen `3e340690`, Existenz der Tests geprüft, Testläufe **nicht** ausgeführt
(grün = unverifiziert). Quelle: `.tmp/wave3-status.md`, Stichproben dieser Revision markiert (✓).

| Bug | Issue | Status | Beleg (Datei:Symbol) | Test (vorhanden) |
|---|---|---|---|---|
| B1 | #1033 | behoben | `hooks/1-generic/dod-push-check.sh`: `PROTECTED_LIST=$(hook_protected_branches …)` (:265) ✓; Commit `587e8684` ✓ | `tests/test_dod_push_check_hook.py::test_1033_block_message_lists_protected_branches_once` (:1061) ✓ |
| B2 | #943 (a)(m) | behoben bis auf **R1** (+ `}`-Lücke Q10) | `hook_common.sh:is_fork_bomb` (:722) linearer Scan ✓; einziger Aufrufer `orchestrator-guard-impl.sh:1157` ✓ | `tests/test_hook_common_lib.py::test_fork_bomb_detection_is_linear_on_a_300kb_identifier` (:422), `::test_fork_bomb_detector_matches_real_bombs`; `tests/test_orchestrator_guard_hook.py::test_fork_bomb_scan_does_not_hang_on_a_300kb_command` (:1681) ✓ |
| B2-Geschwister | #943 (k) | behoben | Klassifikator fail-closed bei rc ≠ 0, Fremdformat, unbekannter Kategorie/Scope/BOM (`orchestrator-guard-impl.sh:1199-1233`) ✓ | `tests/test_orchestrator_guard_hook.py::test_classifier_crash_fails_closed` (:1902) ✓ |
| B3 | #944 SR-B-17 | behoben | `repo-containment.sh`: `PIPESTATUS`-Auswertung (:53-57) ✓ | `tests/test_repo_containment_hook.py::test_wrapper_fails_closed_on_impl_crash` (:717) ✓ |
| B4 | #944 `\|\| true` | behoben | `repo-containment-impl.sh` 1.5.0: Detektor-Exit ≠ 0 blockt (`CHANGELOG.md` [Unreleased]) | `tests/test_repo_containment_hook.py::test_detector_crash_fails_closed` (:940) ✓ |
| SR-B-19 | #944 | behoben | `repo-containment-impl.sh` (perl -pi, sed -Ei/-ni, cp -t) | Param-Tests `tests/test_repo_containment_hook.py` ~:969-991 |
| B5 | #961 | `create_hook` behoben, **R2** offen | `hooks.py:712` `write_atomic` ✓; Rest `hooks.py:635`, `hook_plugins.py:160`, `:348` ✓ | `tests/test_newline_normalization.py::test_create_hook_writes_lf_through_write_atomic` (:246) ✓ |
| B6 | #951 | behoben | `tests/test_dod_push_check_hook.py:_clean_env` (:42) ✓ | Tests ab ~:1186 |
| B7 | #954 | behoben (Stichprobe) | `test_954_*` ab ~:1239; Byte-Identität/5-Mutations-Check/R2S-3-Laufzeit: **unverifiziert** | ja |
| B8 | #1031 | behoben | `handoff.advisory` (`scripts/lib/consistency/handoff_contracts.py:111`, nur `is True`) ✓; 9× `advisory: true` in `config/role-defaults.yaml` ✓ | `tests/test_handoff_contracts.py::test_advisory_roles_declare_the_data_marker` (:59) ✓ |
| B9 | #983 | behoben mit Abweichung (D7) | `_UNKNOWN_TEMPLATE_RATCHET = frozenset()` (`placeholders.py:282`) ✓; `TECH_STACK` aus `PROJECT_LANGUAGES` | `tests/test_placeholder_grace_and_derivation.py` ✓ |
| B10 | #1037 | behoben mit Abweichung (D7) | `project.description`-Seed, `AGENT_META_REPO`-Ableitung (`63b12bde`) ✓ | `tests/test_placeholder_grace_and_derivation.py`, `tests/scenarios/asserts/87-project-description.sh` ✓ |
| B11 | #897 | Kern behoben, **R3** offen | konkreter Bind-Host autorisiert Origin (`admin-server.py:973-977`) ✓; Origin-Meldung mit Hinweis (:982-986) ✓; Wildcard-Startup-Hinweis (:5684-5695) ✓; Overlay-Timeout `81b913c3` ✓ | `tests/test_admin_server.py::TestCheckOriginBindHost` (:2630) ✓ |
| B12 | #1034 | behoben | `doctor_detectors.py:is_dotfile` (:88) ✓ in `_files_in`/`_glob_matches` | `tests/test_doctor_runner.py::test_path_exists_glob_ignores_dotfiles` (:413), `::test_directory_enumeration_ignores_dotfiles` (:423) ✓ |
| B13 | #856 | offen (**R4**) | kein ZC-1-Eintrag in `docs/providers/zcode.md` ✓; ZC-2 behoben (#807) | n/a (D8) |

**Gegenstandslose AC der Revision 1** (erfüllt durch PR #1038 oder aus dem Scope genommen):

- erfüllt: AC-1.1–1.4 (B1), AC-1.5, 1.6, 1.8, 1.9 (Linearität B2, mit anderem Vertrag), AC-1.12/1.13
  (Klassifikator), AC-1.14–1.17 (B3/B4), AC-1.18/1.19 (SR-B-19), AC-2.1 (`create_hook`), AC-2.4–2.8
  (B6), AC-2.9–2.15 (B7, Einzelabgleich unverifiziert), AC-3.1–3.3 (B8), AC-3.4–3.13 (B9/B10, mit
  Abweichung D7), AC-4.7–4.9 (B12; AC-4.10 echter Copilot-Sync unverifiziert).
- ersetzt: AC-1.7, AC-1.10, AC-1.11, AC-1.20–1.22 → AC-A.1–AC-A.9; AC-2.2/2.3 → AC-B.1–AC-B.4;
  AC-4.4/4.6 → AC-B.5/AC-B.7; AC-4.5 → vorhandener Test (AC-B.6); AC-4.11 → AC-B.9.
- entfallen: AC-4.1–4.3 (Auto-Ergänzung bei Wildcard-Bind, Nicht-Ziel).

## Issue-Stand (nur Status, kein Agent-Task)

- **CLOSED:** #948, #950, #952, #953, #1033, #943, #944, #961, #951, #954, #1031, #983, #1037,
  #1034, #1036, #897; #1035 (NOT_PLANNED).
- **Offen, schließt der User selbst** (`! gh issue close …`): #207, #534, #865, #962.
- **#953-Folge-Issue:** legt der User an, Body-Datei `.tmp/issue-953-followup.md` (vorhanden).
- **#856:** OPEN — nach Merge von PR B als wontfix (documented) zu schließen; der Plan liefert nur den
  Kommentar-Entwurf als Handoff an den User (Q6).
- **#971:** offen, Verifikationskriterium undefiniert (Q8). **#192:** bleibt offen.
- **#961:** geschlossen, R2 ist der Rest → PR B `Refs #961`.

## PR A — `fix/fork-bomb-window-gap` (R1)

### R1 — `is_fork_bomb` fail-open an Namens- und Body-Grenze (#943-Rest)

- **Root-Cause:** `hooks/1-generic/lib/hook_common.sh:is_fork_bomb` (:722) wird über
  `hook_shell_scan_py` (:431) als Python-Quelltext emittiert. Bei Name > `_MAX_FUNC_NAME` (64) bricht der
  Rückwärts-Scan ab und `continue` überspringt den Header (:743-747); findet
  `command.find('}', j + 1, j + 1 + _MAX_FUNC_BODY)` kein `}`, folgt ebenfalls `continue` (:755-757).
  Beide Grenzen sind als Laufzeitschranke gedacht (Header-Kommentar :426-430), fallen aber auf
  »kein Treffer« = Allow. Davon unabhängig endet der Body am ersten `}` ohne Verschachtelung (:755,
  Q10).
- **Aufrufer/Geschwisterpfade (verifiziert, Grep):**
  - einziger Aufruf: `orchestrator-guard-impl.sh:1157`
    `destructive = is_fork_bomb(strip_quoted(_scan_code))`; das Ergebnis speist das Destructive-Gate
    (:1253-1258), das unabhängig vom Sentinel blockt.
  - `repo-containment-impl.sh:760` emittiert `hook_shell_scan_py` ebenfalls, ruft `is_fork_bomb`
    aber nicht auf (nur Splitter) → nicht betroffen, wohl aber vom Re-Render (Rebaseline).
  - `dod-push-check.sh` nutzt `hook_shell_scan_py` nicht.
  - `_MAX_FUNC_NAME`/`_MAX_FUNC_BODY` werden nur in `is_fork_bomb` gelesen (Grep: :437-438, :743,
    :746, :755; dazu die gerenderte Kopie `.agents/hooks/lib/hook_common.sh`).
  - Deployte Kopien (gerendert, nicht editieren): `.agents/hooks/lib/hook_common.sh` (versioniert),
    `.claude/hooks/lib/hook_common.sh` (gitignored).
  - Linearität der heutigen Implementierung: 300 KB Bezeichner mit `(){ :; }` 34 ms, `"f(){ "*60000`
    87 ms (gemessen 2026-10-29).
- **Fix-Vertrag (Default Q3 (b): Name exakt, Body fail-closed):**
  - Der Rückwärts-Scan des Namens ist unbegrenzt; `_MAX_FUNC_NAME` und beide Prüfungen darauf
    (:743-747) entfallen. Der Name wird wie jeder andere inhaltlich geprüft (`_body_calls_itself_piped`).
    Begründung Linearität: ein Rückwärts-Scan startet nur an einem `(` mit folgendem `)`; der davor
    liegende Bezeichner endet an genau diesem `(`, zwei Scans überdecken sich daher nie
    (Gesamtarbeit O(n)). Prototyp (Scratch, nicht im Repo): 300 000/600 000 Zeichen 36/72 ms
    (Rev. 2), Nachmessung Rev. 3 inkl. `strip_quoted` 57/117 ms — linear.
  - Body-Fenster erschöpft (kein `}` in den ersten 512 Zeichen nach `{`): `True` statt `continue`.
  - `_MAX_FUNC_BODY = 512` bleibt (Fenstergröße: Q3).
  - Laufzeit linear: Body-Arbeit je Header ≤ 512 Zeichen, Abbruch beim ersten Block.
  - Kein `try/except`, das `False` liefert; Exceptions propagieren (Klassifikator rc ≠ 0 → Block,
    vorhanden).
  - Block-Meldung: das Destructive-Gate (`orchestrator-guard-impl.sh:1255-1257`) gibt eine weitere
    Zeile aus, die die Body-Grenze nennt (»… without an unquoted '}' in its first 512 characters …«),
    konditional formuliert (»If …«), damit ein Fehlalarm erkennbar ist. Klassifikator-Ausgabeformat
    (drei Felder) unverändert.
  - Header-Kommentar `hook_common.sh:426-430` beschreibt: Name unbegrenzt (linear), Body fail-closed
    bei 512, Body endet am ersten ungequoteten `}` (bekannte Lücke, Q10).
  - **Benannte Verhaltensänderung:** bisher erlaubte Befehle mit langen Funktionskörpern ohne
    ungequotetes `}` in den ersten 512 Zeichen werden hart geblockt (RK-1). Lange Funktionsnamen
    blocken nicht mehr pauschal, sondern nur als echte Bombe.
- **Dokumentation der `}`-Lücke (Q10, unabhängig von Q3):** `rules/1-generic/branch-guard.md`
  »Bekannte Grenzen« erhält einen Punkt: der Fork-Bomb-Scan beendet den Funktionskörper am ersten
  ungequoteten `}` (keine Verschachtelung), Bomben mit `${…}` oder `{ …; }` vor dem Selbstaufruf
  werden nicht erkannt; Fix: Folge-Issue. Die Regel wird gerendert (Claude/Continue/Copilot als
  Regeldatei, Codex/Gemini/KimiCode/Mammouth/Opencode/ZCode in `AGENTS.md` eingebettet, gemessen per
  Matrix-Render 2026-10-29) → Drift in AC-A.9. Keine Versionszeile (Regel ohne Frontmatter/Version).
- **AC:**
  - **AC-A.1** Langer Name wird exakt geprüft: `"b"*70 + "(){ " + "b"*70 + "|" + "b"*70 + "& };" + "b"*70`
    → `True` (heute `False`); harmlos `"a"*65 + "(){ :; }"` → `False` (heute `False`,
    Charakterisierung).
  - **AC-A.2** Kurze Namen und Bezeichner ohne `{` unverändert: `"a"*64 + "(){ :; }"` → `False`,
    `"b"*64 + "(){ " + "b"*64 + "|" + "b"*64 + "& };"` → `True`, `"a"*100 + "()"` → `False`
    (heute ebenso, Charakterisierung).
  - **AC-A.3** Body-Fenster erschöpft → `True`: `"f(){ " + "x"*520 + " f|f& };f"`,
    `"f(){ " + "x"*980 + " f|f& };f"` (heute `False`); die `{`-Kette `"f(){ " * 60000` → `True` ist
    mit Zeitmessung in AC-A.5 abgedeckt.
  - **AC-A.4** Geschlossener Body im Fenster wird weiter inhaltlich geprüft:
    `"f(){ " + "x"*500 + " }"` → `False`; `"f(){ x} " * 60000` → `False`.
  - **AC-A.5** Laufzeit (je Fall < 1 s, `time.perf_counter` im Subprozess, Watchdog `timeout=5`):
    `"a"*n + "(){ :; }"` für n = 20 000 und n = 300 000 → `False` (heute `False`, Charakterisierung);
    `{`-Kette `"f(){ " * 60000` → `True` (heute `False`).
  - **AC-A.6** Unverändert grün: `tests/test_hook_common_lib.py::test_fork_bomb_detector_matches_real_bombs`,
    `::test_fork_bomb_detector_ignores_a_quoted_string_argument`,
    `::test_fork_bomb_detection_is_linear_on_a_300kb_identifier`,
    `tests/test_orchestrator_guard_hook.py::test_fork_bomb_blocked`,
    `::test_fork_bomb_text_literal_not_blocked`, `::test_fork_bomb_text_in_a_heredoc_body_is_not_a_bomb`,
    `::test_commented_out_fork_bomb_is_not_a_bomb`, `::test_fork_bomb_scan_does_not_hang_on_a_300kb_command`.
  - **AC-A.7** Hook end-to-end: Bash-Befehl `"f(){ " + "x"*520 + " f|f& };f"` → exit 2, stderr enthält
    `user approval` und die Grenzphrase `first 512` (Variante (a) zusätzlich `over 64 characters`).
    Der Befehlstext selbst enthält keine Ziffern, die Phrase stammt also aus der neuen Zeile.
  - **AC-A.8** Versionen/Changelog: `hooks/1-generic/lib/hook_common.sh` `# version:` 1.4.0 → 1.5.0
    (Minor, Verhaltensänderung) mit `# changelog:`-Eintrag (Datei hat Header-Changelog, :5);
    `hooks/1-generic/orchestrator-guard-impl.sh` `# version:` 1.9.2 → 1.9.3 (Patch, Meldungstext) —
    die Datei hat **keine** `# changelog:`-Zeile (Grep 2026-10-29: 0 Treffer), es wird keine angelegt;
    `CHANGELOG.md` [Unreleased] → `### Fixed` nennt die Fehlalarm-Klasse und die dokumentierte
    `}`-Lücke; `VERSION` unverändert.
  - **AC-A.9** Genau ein AC-01-Rebaseline auf frischem `main`, **13 + k von 1085** Hashes (k ∈ {0, 6}: `context-hashes.json` der 6 `AGENTS.md`-Provider, nicht erwartet; also 13, bzw. 19 mit context-hashes), 0 hinzugefügt/
    entfernt:
    - 4 Hook-Renders: `Claude/.claude/hooks/lib/hook_common.sh`, `Gemini/.agents/hooks/lib/hook_common.sh`,
      `Claude/.claude/hooks/orchestrator-guard-impl.sh`, `Gemini/.agents/hooks/orchestrator-guard-impl.sh`
      (Präzedenz: Rebaseline-Logs Welle 6, `tests/test_ac01_render_identity.py:388-447` — nur
      Hook-Renders, »No agent/rule artifact, AGENTS.md, context-hashes.json … changed«).
    - 9 Regel-Renders aus AC-A.10: `Claude/.claude/rules/branch-guard.md`,
      `Continue/.continue/rules/branch-guard.md`, `Copilot/.github/instructions/branch-guard.instructions.md`,
      `Codex/AGENTS.md`, `Gemini/AGENTS.md`, `KimiCode/AGENTS.md`, `Mammouth/AGENTS.md`,
      `Opencode/AGENTS.md`, `ZCode/AGENTS.md` (Matrix-Render 2026-10-29: genau diese Dateien enthalten
      den »Bekannte Grenzen«-Text).
    - **Keine** Drift: `<Provider>/.meta-config/generated-file-hashes.json` — `_hash_file`
      (`tests/test_ac01_render_identity.py:526-531`, `_DERIVED_HASHES_NAME`) hasht nur die Schlüsselmenge,
      nicht die Werte. `slimming-golden`/`compact-golden` enthalten den Abschnitt nicht (Grep).
    - Möglich, nicht erwartet: `<Provider>/.meta-config/context-hashes.json` der sechs `AGENTS.md`-Provider
      — gehasht wird nur der statische Header (`scripts/lib/context.py:_record_static_hash`, :90; die
      sechs Werte sind heute identisch, obwohl ihre `AGENTS.md`-Hashes differieren). Bei Task 4 messen,
      im Log benennen.
    Patch je Eintrag (kein `--write`, Docstring :12-13 verlangt dafür sauberes `main`), Digests
    unabhängig per `_hash_file` neu berechnet. Log im Docstring von `tests/test_ac01_render_identity.py`
    (inkl. Zahl unberührter Zeilen), Digest in `tests/test_opencode_v2_surface.py::_FIXTURE_TREES`
    (:5297) mit Log-Kommentar (:5280-5296). Self-Sync aktualisiert versioniert
    `.agents/hooks/lib/hook_common.sh`, `.agents/hooks/orchestrator-guard-impl.sh`,
    `.meta-config/generated-file-hashes.json` (Werte u. a. für `.claude/rules/branch-guard.md`, :103);
    das eigene `AGENTS.md` trägt nur den Compact-Zeiger (:57) und driftet nicht;
    `check_stale_deployed_hooks` ohne Findings.
  - **AC-A.10** `rules/1-generic/branch-guard.md` »Bekannte Grenzen« nennt die `}`-Lücke des
    Fork-Bomb-Scans mit den Beispielen `${…}` und `{ …; }` und verweist auf das Folge-Issue (Q10);
    `Grep` `ersten ungequoteten` in der Datei ≥ 1 Treffer.
- **Variante Q3 (a) — fail-closed an beiden Grenzen (Alternative):** zusätzlich Name > 64 mit
  vollständigem Header (`NAME\s*(\s*)\s*{`) → `True`, `_MAX_FUNC_NAME = 64` bleibt. AC-A.1: auch
  harmlos `"a"*65 + "(){ :; }"` → `True`; AC-A.5: n = 20 000/300 000 → `True`; AC-A.7 zusätzlich
  `over 64 characters`. **Fehlalarm:** jede Inline-Funktion mit Namen > 64 Zeichen wird hart geblockt,
  ohne Sentinel-Ausweg (RK-1) — Grund, warum (b) Default ist: (b) erkennt dieselben Bomben ohne diese
  Fehlalarm-Klasse und bleibt linear.
- **Variante Q3 (c) — belassen + dokumentieren:** AC-A.1 (Bombe)/AC-A.3/AC-A.5 (`{`-Kette) kehren sich
  um (Tests pinnen `False` als bekannte Lücke), AC-A.7 entfällt, Doku in `hook_common.sh`-Header und
  zusätzlich zu AC-A.10 in »Bekannte Grenzen«; Version Patch. Drift wie AC-A.9 (11 bzw. 13 Einträge, je nach Bump von `orchestrator-guard-impl.sh`;
  da AC-A.10 ohnehin die Regel ändert; `context-hashes.json` möglich, bei Revision messen).
- **Variante Q10 (i) — `}`-Lücke in PR A mitschließen (Alternative zu Folge-Issue):** Body-Ende als
  das tiefenpassende `}` innerhalb des 512er-Fensters (Zähler für `{`/`}`), sonst fail-closed. Prototyp
  (Scratch, auf (b)): beide Q10-Beispiele `True`, alle AC-A.1–A.5-Fälle unverändert, `"f(){ x} " * 60000`
  119 ms, 600 000-Zeichen-Name 113 ms (linear). Dann zusätzliche AC (Q10-Beispiele → `True`), AC-A.10
  entfällt bzw. nennt nur Restgrenzen; Fehlalarme durch `{` in ungequotetem Text im Body möglich
  (nicht gemessen).
- **Regressionstest:** `tests/test_hook_common_lib.py::test_fork_bomb_scans_long_function_name_exactly`
  (Variante (a): `::test_fork_bomb_fails_closed_on_long_function_name`),
  `::test_fork_bomb_function_name_at_limit_is_scanned`,
  `::test_fork_bomb_fails_closed_on_exhausted_body_window`,
  `::test_fork_bomb_closed_body_within_window_is_scanned`,
  `::test_fork_bomb_scan_stays_linear_on_long_header_names` (alle fünf per `@pytest.mark.parametrize`);
  `tests/test_orchestrator_guard_hook.py::test_fork_bomb_window_block_names_scan_limits` (Namen neu).
  Mechanik vorhanden: `_scan` (`tests/test_hook_common_lib.py:378`) führt den emittierten Quelltext per
  `sys.executable -c` aus; für AC-A.5 bekommt er einen optionalen `timeout`. AC-A.10: Grep, kein Test.

## PR B — `fix/index-lf-admin-hint-zcode-doc` (R2, R3, R4)

### R2 — Managed-Indizes über `write_atomic` (#961-Rest)

- **Root-Cause:** `scripts/lib/hooks.py:sync_hooks` (:635), `scripts/lib/hook_plugins.py:sync_release_gates`
  (:160), `scripts/lib/hook_plugins.py:sync_hook_lib` (:348) schreiben den `.agent-meta-managed`-Index
  per `Path.write_text(…, encoding="utf-8")` (Text-Modus übersetzt `\n` → `os.linesep`).
  `write_atomic` ist in beiden Modulen importiert (`hooks.py:9`, `hook_plugins.py:16`).
  Geschwister außerhalb Scope: `scripts/lib/skills.py:85` (Nicht-Ziel).
- **Fix-Vertrag:** Die drei Aufrufe gehen über `write_atomic(path, content)` (öffnet mit
  `newline="\n"`, `io.py:378`). Bedingungen unverändert: nur `not dry_run`; `sync_hooks` schreibt den
  Index auch leer, wenn vorher Einträge bestanden (#630); `mkdir` der Elternverzeichnisse übernimmt
  `write_atomic` (:375), die vorhandenen `mkdir`-Aufrufe dürfen bleiben.
  **Benannte Verhaltensänderung:** `write_atomic` nutzt `mkstemp` (:377) → Modus 0600 statt
  umask-Modus für die drei Index-Dateien. Git unberührt (kein Exec-Bit).
- **Rebaseline:** keiner. AC-01 hasht nur Dateiinhalte (`tests/test_ac01_render_identity.py:540`,
  `sha256(data)`); auf LF-Plattformen ist der Inhalt identisch.
- **AC:**
  - **AC-B.1** Für jeden der drei Writer: ein Spy auf `write_atomic` im jeweiligen Modul (Muster
    `tests/test_newline_normalization.py::test_create_hook_writes_lf_through_write_atomic`): die
    Spy-Aufrufliste **enthält** den Index-Pfad `<…>/.agent-meta-managed` (weitere Aufrufe, z. B. für
    Skripte, sind zulässig), und die Index-Bytes enthalten kein `\r`.
  - **AC-B.2** `Grep` `\.write_text\(` in `scripts/lib/hooks.py` und `scripts/lib/hook_plugins.py` → 0 Treffer.
  - **AC-B.3** #630-/Dry-Run-Verhalten des Hook-Index bleibt, gepinnt durch zwei **neue
    Charakterisierungstests** (vor und nach dem Fix grün; vorhandene Tests decken das für `sync_hooks`
    nicht ab — Grep `revocation|agent-meta-managed` in `tests/test_provider_hooks_config.py`,
    `tests/test_hook_drift.py` ohne Treffer zu diesem Pfad; Vorbild für Dry-Run nur
    `tests/test_hook_lib_sync.py::test_dry_run_makes_no_filesystem_changes` :82 für `sync_hook_lib`):
    - `test_hook_managed_index_dry_run_writes_nothing`: `sync_hooks(…, dry_run=True)` → kein
      `.agent-meta-managed`, Spy-Liste ohne Index-Pfad.
    - `test_hook_managed_index_rewritten_empty_after_revocation`: erster Lauf mit unterstütztem
      Hook-Protokoll schreibt einen nicht-leeren Index; zweiter Lauf mit derselben Provider-Config ohne
      `hook_protocol` (Gate `provider_hooks_supported`, `hooks.py:486`) → Index existiert, 0 Bytes.
    `CHANGELOG.md` nennt den Modus 0600.
  - **AC-B.4** `tests/test_ac01_render_identity.py` grün ohne Rebaseline.
- **Regressionstest:** `tests/test_newline_normalization.py::test_hook_managed_index_writes_lf_through_write_atomic`,
  `::test_release_gate_managed_index_writes_lf_through_write_atomic`,
  `::test_hook_lib_managed_index_writes_lf_through_write_atomic` (vorher rot);
  Charakterisierung `::test_hook_managed_index_dry_run_writes_nothing`,
  `::test_hook_managed_index_rewritten_empty_after_revocation` (vorher grün). Namen neu.

### R3 — Host-Header-Hinweis und `--allowed-hosts`-Semantik (#897-Rest)

- **Root-Cause:** `scripts/admin-server.py:AuthService.check_origin` (statisch, :947-992) hängt nur an
  die Origin-Meldung einen Hinweis; die Host-Meldung (:992) nicht. Hilfetext (:5926-5929, »Additional
  allowed …«, »Extends (does not replace)«), How-to (`docs/howto/admin-ui-remote-access.md:62`
  »Additional allowed …«/»**Extends**«, `:166` »it extends the default«) und Schema
  (`config/project-config.schema.json:1927`, `admin-ui.allowed-hosts.description`: »List of host:port
  origins … Extends the default loopback set«) behaupten »Extends«, Code ersetzt (:547, :5673); das
  Schema nennt zudem »host:port«, der Code erwartet Hosts (Port wird angehängt, :980/:988).
- **Fix-Vertrag (Default Q5):**
  - `host header not allowed`-Meldung erhält denselben Hinweis wie die Origin-Meldung
    (`--allowed-hosts <host>` bzw. `admin-ui.allowed-hosts`) plus `include loopback names if needed`.
    Logik unverändert; ein Origin wird nie aus dem Host-Header abgeleitet.
  - Wildcard-Startup-Hinweis (`admin-server.py:5694-5695`, »writes from other machines need
    --allowed-hosts …«) erhält denselben Zusatz `include loopback names if needed` (er ersetzt die
    Default-Liste ebenfalls).
  - Hilfetext (:5927-5929), How-to-Tabelle (:62) und -Bullet (:166) beschreiben »replaces the default
    loopback set« (Loopback-Namen bei Bedarf mit angeben); der Hilfetext beginnt nicht mehr mit
    »Additional«. How-to-Beispiele `--allowed-hosts myhost.example.com` (:216-224) und der YAML-Block
    (`allowed-hosts: ["myhost.example.com"]`, :157) erhalten den Hinweis, dass Loopback-Zugriff dann
    nur mit zusätzlich gelisteten Loopback-Namen bleibt.
  - Schema-`description` von `admin-ui.allowed-hosts`: Hostnamen/IPs (ohne Port, der Server-Port wird
    angehängt), ersetzt die Loopback-Defaults. Das Schema wird nicht gerendert (kein Pfad in
    `tests/fixtures/ac01-baseline/hashes.json`; Matrix-Render 2026-10-29 ohne Treffer für den
    Beschreibungstext) → kein Rebaseline. Die Beschreibung wird nur von UI/Validierung gelesen
    (`fill_defaults`, `scripts/lib/config.py:~1060-1104`, füllt `admin-ui` nicht); keine Verhaltensänderung.
  - Keine Verhaltensänderung des Servers.
  - Keine Helfer-Extraktion: `check_origin` ist statisch (direkt testbar), der Hilfetext ist per
    `python3 scripts/admin-server.py --help` prüfbar (Exit 0, geprüft 2026-10-29). Eine Extraktion aus
    `AdminServer.__init__` (bindet einen Socket) wird nur nötig, wenn Q5 auf »Code an Hilfetext
    angleichen« entschieden wird (dann socket-freier Helfer für die effektive Host-Liste).
- **AC:**
  - **AC-B.5** `check_origin(origin=None, host="evil.example:7420", allowed_hosts=DEFAULT_ALLOWED_HOSTS,
    bind_host="127.0.0.1", bind_port=7420)` wirft `SecurityError`, Text enthält
    `host header not allowed`, `--allowed-hosts`, `admin-ui.allowed-hosts` und `loopback names`.
  - **AC-B.6** Forged Host mit passendem Origin bleibt abgelehnt — vorhandener Test
    `tests/test_admin_server.py::TestCheckOrigin::test_dns_rebinding_forged_host_rejected_even_with_matching_origin`
    (:831) und `TestCheckOriginBindHost` unverändert grün.
  - **AC-B.7** Replace-Semantik überall:
    - `python3 scripts/admin-server.py --help` (Whitespace normalisiert) enthält `Replaces` und weder
      `does not replace` noch `Additional allowed`;
    - die Schema-Beschreibung `properties.admin-ui.properties.allowed-hosts.description` enthält
      `Replaces` und weder `Extends` noch `host:port`;
    - `Grep -i` `\*\*Extends\*\*|extends the default|Additional allowed` in `scripts/admin-server.py`,
      `docs/howto/admin-ui-remote-access.md`, `config/project-config.schema.json` → 0 Treffer;
    - `Grep` `loopback names` in `scripts/admin-server.py` ≥ 3 Treffer (Hilfetext, Host-Meldung,
      Wildcard-Hinweis) und in `docs/howto/admin-ui-remote-access.md` ≥ 2 (YAML-Block :157, Beispiel
      :216-224).
- **Regressionstest:** `tests/test_admin_server.py::TestCheckOrigin::test_host_header_rejection_names_allowlist_hint`,
  `::test_allowed_hosts_help_states_replace_semantics` (prüft `--help` **und** die Schema-Beschreibung
  per `json.load`; Namen neu). Kein eigener Schema-Test: das Schema ist nicht in `hashes.json` und wird
  von keinem Test inhaltlich gepinnt; die Schema-Assertion im Help-Test ist vorher rot.

### R4 — zcode ZC-1 Entscheidungsnotiz (#856, D8)

- **Ist:** Bootstrap dokumentiert (`docs/providers/zcode.md:61-86`); ZC-2 (commands under-claim) mit
  #807 behoben (`docs/providers/zcode.md:52`, `config/provider-capabilities.yaml` Kommentar
  »UNDERCLAIM ZC-2 fixed«). Datei ist englisch (Provider-Doku) → Notiz englisch.
- **Fix-Vertrag:** neuer Punkt in »Deliberate limitations« (:207-216): ZC-1 (workspace agent auto-load)
  stays wontfix (documented); agent-meta does not write to `~/.zcode/agents` (outside the project root,
  would violate repo containment); the AGENTS.md bootstrap is the supported path; ZC-2 fixed in #807.
  `docs/providers/` ist nicht gerendert (kein Pfad in `tests/fixtures/ac01-baseline/hashes.json`).
- **AC:**
  - **AC-B.8** `docs/providers/zcode.md` enthält `ZC-1`, `wontfix`, `repo containment`, `~/.zcode/agents`
    und `#807` im Abschnitt »Deliberate limitations«.
  - **AC-B.9** Schließkommentar-Entwurf für #856 (englisch) liegt als Handoff-Text vor; ausgeführt
    wird er vom User nach Merge von PR B (Q6).
- **Regressionstest:** keiner (D8).

## Interface Contracts

| Datei:Symbol | Signatur | Fehlerpfade | Status |
|---|---|---|---|
| `hooks/1-generic/lib/hook_common.sh:is_fork_bomb` (emittiert von `hook_shell_scan_py`) | `(command: str) -> bool` | Name unbegrenzt exakt geprüft (Q3 (b)); Body-Fenster ohne `}` → `True`; Body endet am ersten `}` (Lücke Q10, unverändert); Exception propagiert | geändert |
| `hooks/1-generic/orchestrator-guard-impl.sh` Destructive-Gate-Meldung | stderr, eine Zeile mehr (Body-Grenze 512) | — | erweitert |
| `rules/1-generic/branch-guard.md` »Bekannte Grenzen« | Markdown, ein Punkt mehr (`}`-Lücke) | — | erweitert (gerendert, AC-A.9) |
| `config/project-config.schema.json` `admin-ui.allowed-hosts.description` | Text | — | nur Beschreibung |
| `scripts/lib/io.py:write_atomic` | `(path: Path, content: str, mode: str = "w") -> None` | bestehend | unverändert, drei neue Aufrufstellen |
| `scripts/lib/hooks.py:sync_hooks`, `scripts/lib/hook_plugins.py:sync_release_gates`, `:sync_hook_lib` | Signaturen unverändert | — | Index via `write_atomic` (LF, 0600) |
| `scripts/admin-server.py:AuthService.check_origin` | unverändert (keyword-only, statisch) | `SecurityError`-Text bei Host-Header erweitert | nur Meldung |
| `scripts/admin-server.py` CLI `--allowed-hosts` | `nargs="*"`, ersetzt Default | — | nur Hilfetext |

## Datenfluss

- **Destructive-Gate:** Bash-Tool → `orchestrator-guard.sh` → `-impl.sh` → Klassifikator
  (`split_shell_statements_and_clean` → `strip_quoted` → `is_fork_bomb`) → `destructive` → Gate
  (:1253) → exit 2 mit Meldung (+ Grenzen-Zeile).
- **Hook-Deploy:** `sync.py` → `sync_hooks` / `sync_release_gates` / `sync_hook_lib` → Skripte über
  `write_checked` (unverändert) → Index über `write_atomic` (neu) → `<hooks_dir>/.agent-meta-managed`,
  `…/release-gates/.agent-meta-managed`, `…/lib/.agent-meta-managed`.
- **Admin-Server:** CLI > Config > Default → `effective_allowed_hosts` (:5673) →
  `AdminRequestHandler.allowed_hosts` → `check_origin` je Mutation → `SecurityError` mit Hinweis.

## Acceptance Criteria

AC-Definitionen in den PR-Abschnitten. Index:

| PR | Restpunkt | AC-IDs |
|---|---|---|
| PR A | R1 #943-Rest | AC-A.1 – AC-A.7 |
| PR A | Querschnitt (Version, Rebaseline) | AC-A.8, AC-A.9 |
| PR A | Q10-Lücke dokumentiert | AC-A.10 |
| PR B | R2 #961-Rest | AC-B.1 – AC-B.4 |
| PR B | R3 #897-Rest | AC-B.5 – AC-B.7 |
| PR B | R4 #856 | AC-B.8, AC-B.9 |

Für jede PR zusätzlich: `python3 scripts/sync.py --validate` Exit 0, betroffene Testmodule grün,
neue Tests vor dem Fix rot (TDD) — ausgenommen ausdrücklich als Charakterisierung markierte Fälle
(AC-A.1 harmlos, AC-A.2, AC-A.4, AC-A.5 n = 20 000/300 000, AC-B.3), die vorher und nachher grün sind.

## PR-Schnitt und Merge-Reihenfolge

- **PR A** enthält nur R1 (inkl. AC-A.10): einziger Restpunkt mit gerenderter Ausgabe (Hook + Regel)
  und damit einziger mit AC-01-Rebaseline und Self-Sync von `.agents/hooks/`. Isoliert, damit der
  Rebaseline genau einmal auf frischem `main` läuft und ein Revert nur Hook-Verhalten und Regeltext
  betrifft.
- **PR B** bündelt R2, R3, R4: reiner Python-/Doku-/Schema-Code ohne gerenderte Ausgabe (Schema
  geprüft, s. R3), kein Rebaseline; drei kleine, unabhängige Punkte.
- Dateidisjunkt bis auf `CHANGELOG.md` → parallel entwickelbar. Merge seriell: PR A zuerst (D3,
  Security), dann PR B auf frischem `main` (Append-Konflikt in `CHANGELOG.md` manuell lösen; kein
  Rebaseline-Konflikt, weil PR B `hashes.json`/`_FIXTURE_TREES` nicht berührt).

## Risiken

- **RK-1 — Fehlalarm-Klasse R1 (Default (b)):** jede Funktionsdefinition im ungequoteten Befehlstext
  (nach Entfernen von Heredoc-Bodies, Kommentaren und gequoteten Spannen) ohne ungequotetes `}` in den
  ersten 512 Body-Zeichen wird **hart** geblockt — das Destructive-Gate hat keinen Sentinel-Ausweg.
  Ausweg: Funktion kürzen, Skript als Datei statt inline, Ausführung durch den User. Gemindert durch die
  Grenzen-Zeile in der Meldung (AC-A.7; erscheint bei jedem Destructive-Block, nicht nur bei diesem Fehlalarm). Unter Variante (a) kommt jede Funktion mit Namen > 64 Zeichen
  hinzu (Grund für Default (b)). Alternative: Q3 (c).
- **RK-7 — `}`-Lücke bleibt fail-open (Q10):** Fork-Bomben mit `${…}` oder `{ …; }` vor dem
  Selbstaufruf passieren das Destructive-Gate weiterhin, bis das Folge-Issue umgesetzt ist (oder
  Variante Q10 (i) gewählt wird). Gemindert nur durch Dokumentation (AC-A.10); Convention boundary.
- **RK-2 — Veraltete deployte Lib unbemerkt:** `check_stale_deployed_hooks`
  (`scripts/lib/consistency/hook_drift.py:29-86`) vergleicht nur Namen aus `<hooks_dir>/.agent-meta-managed`
  (Top-Level-Skripte), nicht `lib/hook_common.sh`. Ein Projekt ohne Re-Sync behält den fail-open-Scanner
  ohne Warnung. Gemindert: `orchestrator-guard-impl.sh` wird mitgebumpt (AC-A.8), dessen Drift wird
  gemeldet. Vollständige Abdeckung: Nicht-Ziel/Folge-Issue.
- **RK-3 — Datei-Modus R2:** drei Index-Dateien neu 0600 statt umask-Modus; ein anderer lokaler
  Nutzer liest sie nicht mehr. Kein Exec-Bit betroffen.
- **RK-4 — `CHANGELOG.md`-Konflikt** zwischen PR A und PR B; manuelle Auflösung im später gemergten PR.
- **RK-5 — Timing-Tests ohne #945:** AC-A.5 nutzt Subprozess + Watchdog und Grenze 1 s gegen gemessene
  57–117 ms (Faktor > 8). Restrisiko gering (Q4).
- **RK-6 — Validator-Fehlklassifikation:** `spec_plan.py` prüft diese `*-spec.md` als Plan; Warnungen
  zu Plan-Pflichtsektionen sind erwartet (Nicht-Ziel).

## Offene Fragen

| ID | Frage | Default | Entscheidung bis |
|---|---|---|---|
| Q1 | (Rev. 1) Reopen vs. neue Issues für geschlossene, angeblich unbehobene Issues | **gegenstandslos** — Fixes sind gemergt, Commits existieren | — |
| Q2 | (Rev. 1) D5 formal aufheben? | **gegenstandslos** — nur die Rebaseline-Regel bleibt | — |
| Q3 | R1-Vertrag: (a) fail-closed an beiden Grenzen; (b) Name unbegrenzt exakt prüfen + Body fail-closed; (c) belassen und dokumentieren? Zusatz: Body-Fenster 512 beibehalten oder auf 1024 erhöhen (weniger Fehlalarme, Laufzeit weiter linear)? | **(b)**, Fenster 512 — erkennt die Bombe mit langem Namen exakt, linear (36/72 ms bzw. 57/117 ms für 300 000/600 000 Zeichen), ohne die Fehlalarm-Klasse »Name > 64« von (a) (RK-1) | vor PR-A-Task 1, durch User |
| Q4 | #945 (Guard-Test-Isolation, CI-Timeouts) vor PR A vorziehen? | Nein — neue Timing-Tests laufen im Subprozess mit Watchdog, Grenze > Faktor 8 über Messwert (RK-5) | vor PR-A-Start, durch User |
| Q5 | `--allowed-hosts`: Hilfetext/How-to an Code anpassen (»replaces«) oder Code an Hilfetext (»extends«, Verhaltensänderung)? | Hilfetext/How-to anpassen | vor PR-B-Task 2, durch User |
| Q6 | #856 nach Merge von PR B schließen (ZC-1 wontfix documented, ZC-2 fixed in #807)? | Ja, durch den User mit dem Kommentar-Entwurf aus dem Plan | vor PR-B-Beschreibung, durch User |
| Q7 | Form `function NAME { … }` (ohne `()`) in R1 aufnehmen? | Nein — vorbestehende Lücke, Folge-Issue durch den User | vor PR-A-Task 1, durch User |
| Q8 | Kriterium für das Schließen von #971 (D2)? | #971 bleibt offen, bis der User ein Kriterium nennt | offen, durch User |
| Q9 | Bereits geschlossene Bezugs-Issues (#943, #961, #897) in den PRs: »Refs« oder Reopen + »Closes«? | »Refs«, kein Reopen | vor den PR-Beschreibungen, durch User |
| Q10 | `}`-Lücke (Body endet am ersten `}`; `${…}`, `{ …; }`): (ii) in PR A nur in »Bekannte Grenzen« dokumentieren + Folge-Issue, oder (i) in PR A per tiefenpassendem `}` im Fenster mitschließen? | (ii): Folge-Issue durch den User (Text-Entwurf im Plan-Status, nicht ausgeführt); Doku AC-A.10 | vor PR-A-Task 1, durch User |

## Trace-Anker

spec-id: SPEC-bugfix-wave-3
