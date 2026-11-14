---
spec-id: SPEC-HOOK-SINGLE-PARSE-2026-11-11
title: Einmal-Parse der Hook-Payload (hook_json_get_many) im Orchestrator-Guard
status: DRAFT
issue: "#1169"
plan: docs/superpowers/plans/2026-11-11-phase-d-guards-hooks.md (Task 5; Folge-Tasks 6 und 7)
datum: 2026-11-13
autor: concept-specifier (Subagent, Auftrag via orchestrator)
related: Phase H #1161 Punkt 5 (Abstimmung, Entscheidung 28), SPEC-GUARD-ROLE-ATTRIBUTION-2026-11-11 (#1210, gleiche Datei)
---

# Einmal-Parse der Hook-Payload (`hook_json_get_many`) — Spec

> **Status: DRAFT — Entwurf, Freigabe durch Nutzer ausstehend.** Nicht `APPROVED`. Kein Reviewer-Lauf,
> keine Nutzerfreigabe. Offene Entscheidungen stehen in §11 und werden hier **nicht** entschieden.
> Diese Datei enthält Contracts und Akzeptanzkriterien, keine Implementierung.
> Trace-Anker: `spec-id: SPEC-HOOK-SINGLE-PARSE-2026-11-11`.
>
> **Messstand:** Worktree `wt-phase-d1`, 2026-11-13. Alle `Datei:Zeile`-Anker wurden an diesem Stand
> nachgemessen (statisch, Lesen des Quelltexts); keine Laufzeitmessung.

## 1. Problem / Ziel / Nicht-Ziele

### 1.1 Problem

Der Orchestrator-Guard (`hooks/1-generic/orchestrator-guard-impl.sh`) startet pro Bash-Aufruf mehrfach einen
Python-Interpreter, um dieselbe JSON-Payload (`$INPUT`) wiederholt zu parsen. Jeder Tool-Call im Harness
durchläuft die Hook-Kette; die Kosten fallen also bei jedem Bash-Call an (Latenz **nicht gemessen**, siehe §9).

Statische Neuzählung am aktuellen Stand (Bash-Pfad ohne Sentinel, `project.yaml` vorhanden):

| # | Stelle | Zweck |
|---|---|---|
| 1 | `orchestrator-guard-impl.sh:214` -> `hook_json_usable` (`hook_common.sh:128-131`, ruft `hook_json_get`) | Interpreter-Probe |
| 2 | `:231` | JSON-Gültigkeitsprüfung (`json.loads`) |
| 3 | `:239` `hook_json_get ... tool_name` | Feld |
| 4 | `:269` `... agent_id` | Feld |
| 5 | `:307` `... tool_input.command` | Feld |
| 6 | `:326` | Sentinel-Parse (Regex auf Kommandozeile 1) |
| 7 | `:384` `... cwd` | Feld |
| 8 | `:1330` | Git-Scan (`_GIT_SCAN_SRC`, `hook_shell_scan_py`) |
| 9 | `:1419` | Strict-Config (`STRICT=$("$_PY" -c ...)`) |

= **9 Python-Starts**, identisch mit der Zählung des Plans (Abweichung #1169, Basis `9aa0e0c0`); Zeilen
unverändert. Zusätzlich nur bedingt (nicht im Grundpfad): `:275` und `:280` (nur Tool `Agent`/`Task`),
Allowlist-Lookups `:450`, `:465` (nur mit Allowlist-Sentinel), Audit-Redaktion in `hook_audit_log_append`
(nur mit Sentinel; Stelle im Plan mit `:500` angegeben, hier nicht nachgemessen).

Die Zählung geht davon aus, dass `hook_shell_scan_py` (`:533`) nur Quelltext ausgibt und keinen eigenen
Interpreter startet; **nicht verifiziert** (§9).

### 1.2 Ziel

Eine neue Funktion `hook_json_get_many` in `hooks/1-generic/lib/hook_common.sh`, die mehrere Felder in
**einem** Interpreter-Start liest. Der Guard liest seine Payload-Felder damit einmal. Zielgröße: höchstens
5 Python-Starts im Grundpfad (Planwert, **per Benchmark Task 6 zu messen**, nicht angenommen). Verhalten
unverändert fail-closed; keine neue Fail-Open-Kante.

### 1.3 Nicht-Ziele / Out-of-scope

- Keine Schwächung des Fail-Closed-Verhaltens; keine Änderung der Entscheidungslogik des Guards.
- Reihenfolge der Vorbedingungen bleibt unverändert: Lib laden (`:181`), Interpreter vorhanden (`:187`),
  Hilfsfunktionen vorhanden (`:199`), Probe `hook_json_usable` (`:214`), leerer Input (`:226`), JSON gültig,
  `tool_name` leer (`:245`), unbekannt (`:255`). Nur das **Lesen** der Felder wird zusammengefasst.
- `hook_json_get` bleibt unverändert (Signatur, Verhalten); `hook_json_usable` bleibt (Probe, 1 Spawn).
- Keine Zusammenlegung von Sentinel-Parse, Git-Scan, Strict-Config oder Allowlist-Lookups mit dem
  Mehrfeld-Parse (eigene Python-Programme).
- Keine Änderung an `repo-containment-impl.sh`, `dod-push-check.sh` im Pflicht-Umfang (siehe OQ-2, Plan
  „Optional", eigener Commit nur bei Spec-Freigabe).
- Keine Rollenbindung (#1210) und kein ask-Pfad (#1217); diese laufen nach Task 7 auf derselben Datei.
- Keine Wall-Clock-Assertion in Tests (Trap #1116).
- Keine Implementierung (Plan Task 6/7 nach Freigabe).

### 1.4 Hinweis aus dieser Session (Hinweis, nicht Beleg)

Falschalarme der Hooks durch Klartext/gequoteten Text in Kommandos wurden am 2026-11-13 in #1226, #1229,
#1232 behoben (im `git log` sichtbar: `fix: ignore quoted text of non-git commands in push guard (#1232)`,
`resolve push-guard branch from the push's own worktree` für #1229; #1226 nur über den Auftraggeber
bekannt, nicht im Log nachgesehen). Jeder Hook-Lauf parst dieselbe JSON-Payload und denselben
Kommandotext mehrfach. Das ist ein **Hinweis**, dass weniger, zentralisierte Parse-Stellen die Divergenz
zwischen Hooks verringern könnten. Es ist **kein Beleg**: Kausalität zwischen Spawn-Zahl, Latenz und
Falschalarmen ist nicht gezeigt; diese Spec stützt keine Entscheidung darauf.

## 2. Interface Contracts

### 2.1 `hook_json_get_many`

Datei: `hooks/1-generic/lib/hook_common.sh`, neu, direkt nach `hook_json_get` (`:63-110`).

```
hook_json_get_many <json-string> <dotted.path>...
```

| Aspekt | Festlegung |
|---|---|
| Argumente | `$1` JSON-Text; `$2..$N` Pfade (gleiche Punkt-Syntax wie `hook_json_get`), mindestens einer |
| Interpreter | `hook_python_bin` (`:42`); genau **ein** Start (`"$py" -c ...`); Eingabe über stdin (`printf '%s' "$json" \|`), Pfade als `sys.argv` |
| Byte-Regeln | unverändert zu `hook_json_get` v1.0.1 (`:71-76`, `:92`): Eingang `decode('utf-8','surrogateescape')`, Ausgang `encode('utf-8','surrogateescape')`, bei `UnicodeEncodeError` `surrogatepass` |
| Ausgabe (stdout) | je Pfad ein Feld, mit NUL (`\0`) **terminiert**, in Argument-Reihenfolge; danach ein **Abschlussfeld** `ok` (NUL-terminiert), nur bei vollständigem Erfolg (siehe §2.3) |
| Wert-Darstellung | `str(cur)` für Skalare wie `hook_json_get` (`:108`); Pfad nicht auflösbar, Wert `null`, Objekt oder Array: **leeres Feld** (wie `default=""`) |
| Fehlerpfade | Tabelle §2.4 |
| Rückgabecode | 0 nur bei vollständigem Erfolg; sonst 1, **keine** Ausgabe auf stdout |
| `default`-Argument | existiert nicht (anders als `hook_json_get`) |

Keine Escape-Kodierung der Werte; Trennung ausschließlich über NUL. Eine Zeilenumbruch-Ausgabe wie bei
`hook_json_get` (`emit` hängt `\n` an, `:88`) entfällt; Zeilenumbrüche im Wert bleiben erhalten
(Test `..._keeps_newlines_in_command`).

### 2.2 Konsum (bash 3.2, ohne `mapfile`/`eval`)

Entscheidung 28: `read -r -d ''`, kein `eval`, kein `mapfile`, keine Namerefs (bash 3.2 kennt beides
nicht). Bash-Variablen können kein NUL halten; deshalb liest der Aufrufer feldweise in benannte Variablen.
Vorgesehenes Muster (Contract, kein fertiger Code):

```
{
  IFS= read -r -d '' TOOL_NAME   || _P_FAIL=1
  IFS= read -r -d '' AGENT_ID    || _P_FAIL=1
  ...                                         # ein read je Pfad, gleiche Reihenfolge wie die Argumente
  IFS= read -r -d '' _P_TRAILER  || _P_FAIL=1
} < <(hook_json_get_many "$INPUT" tool_name agent_id ...)
[ "${_P_FAIL:-0}" = 0 ] && [ "$_P_TRAILER" = "ok" ] || <Guard blockiert, exit 2>
```

Regeln:

- Fehlendes Feld, fehlendes Abschlussfeld oder `read`-Rückgabecode ≠ 0 gilt als Fehlschlag des ganzen
  Aufrufs. Der Rückgabecode von `hook_json_get_many` selbst ist hinter `< <(...)` nicht auswertbar; deshalb
  das Abschlussfeld `ok` (siehe OQ-6, Abweichung vom Plan-Interface „je Pfad ein Feld").
- Die Gruppe `{ ...; }` läuft in der aktuellen Shell (kein Subshell-Verlust der Variablen).
- Die Prozess-Substitution `< <(...)` ist in bash 3.2 verfügbar; **auf macOS-bash 3.2 nicht verifiziert**
  (OQ-5).
- Variablen werden vor dem Lesen nicht vorbelegt; bei Fehlschlag ist ihr Wert unbeachtlich, der Guard
  beendet sich vor jeder Nutzung.

### 2.3 Fail-Closed-Semantik

Identisch zu `hook_json_get` in der Wirkung auf den Guard: ein nicht lesbares Feld ergibt ein **leeres**
Feld, und der Guard behandelt leer wie bisher (`:245` `tool_name` leer -> exit 2). Unterschied (bewusst):
`hook_json_get` meldet Parsefehler als `default` mit Rückgabecode 0 (`:93-95`); `hook_json_get_many`
meldet Parsefehler, NUL im Wert und fehlenden Interpreter als Fehlschlag (Rückgabecode 1, kein Abschlussfeld,
keine Teilausgabe), damit der Aufrufer „kein JSON" von „Feld fehlt" unterscheiden kann. Das ist die
Voraussetzung dafür, dass `:231` in den Mehrfeld-Parse wandern kann (Option A in §4).

### 2.4 Fehlerverhalten-Tabelle

| Fall | `hook_json_get` (heute) | `hook_json_get_many` (Soll) | Guard-Folge |
|---|---|---|---|
| Parsefehler (kein gültiges JSON) | `default` (leer), rc 0 (`:93-95`) | rc 1, keine Ausgabe, kein Abschlussfeld | exit 2 (Meldung wie `:234`, bzw. neue Meldung, OQ-1) |
| Interpreter fehlt (`hook_python_bin` leer, `:67`) | `default`, rc 0 | rc 1, keine Ausgabe | exit 2 (im Guard schon vor `:187` ausgeschlossen; Funktion bleibt für andere Aufrufer sicher) |
| Interpreter stürzt ab / rc≠0 (`... \|\| printf default`, `:109`) | `default`, rc 0 | rc 1, keine Ausgabe | exit 2 |
| Pfad nicht auflösbar / `null` | `default` | leeres Feld, Rest unverändert | wie heute (`:245` für `tool_name`) |
| Wert ist Objekt/Array (nicht skalar) | `default` (`:105`) | leeres Feld | wie heute |
| Skalar kein String (Zahl, Bool) | `str(cur)` (`:108`, z. B. `True`) | `str(cur)` identisch | wie heute |
| Ungültiges UTF-8 in Payload / Surrogat im Wert | unverändert durchgereicht (v1.0.1) | identisch (`surrogateescape`/`surrogatepass`) | wie heute |
| **NUL (`\u0000`) in einem angeforderten Wert** | Wert durch `$(...)` von bash: NUL wird verworfen (Verhalten je bash-Version, **nicht verifiziert**) | **ganzer Aufruf schlägt fehl**: rc 1, keine Ausgabe, kein Abschlussfeld | exit 2 (fail closed) |
| NUL in einem **nicht** angeforderten Feld | irrelevant | irrelevant (nur angeforderte Pfade werden geprüft) | unverändert |

Begründung der NUL-Regel: NUL ist der Feldtrenner. Ein Wert mit NUL würde sonst die Zuordnung verschieben
(z. B. könnte `tool_input.command = "a\u0000/evil"` den folgenden Wert für `cwd` stellen, Plan Task 5
Step 1). Statt Maskieren oder Abschneiden bricht die Funktion ab; der Guard blockiert.
**Verhaltensänderung:** Eine Payload mit NUL in einem angeforderten Feld wurde bisher nicht blockiert, sondern
(vermutlich) ohne NUL verarbeitet; künftig wird sie blockiert. Das ist eine Verschärfung; Auswirkung auf
legitime Aufrufe nicht bekannt (OQ-7).

## 3. Datenfluss

```
stdin -> INPUT=$(cat)                                   (:169)
  -> Lib laden, Interpreter, Hilfsfunktionen             (:181-206, unverändert)
  -> hook_json_usable (Probe, 1 Spawn)                   (:214, unverändert)
  -> INPUT leer? -> exit 2                               (:226, unverändert)
  -> [heute: json.loads-Prüfung :231]
  -> hook_json_get_many "$INPUT" tool_name agent_id
       tool_input.isolation tool_input.subagent_type
       tool_input.command cwd                            (neu; 1 Spawn)
       => TOOL_NAME AGENT_ID _ISOLATION _SUBAGENT_TYPE BASH_CMD PAYLOAD_CWD + Abschlussfeld
  -> Fehlschlag -> exit 2
  -> TOOL_NAME leer / unbekannt -> exit 2                (:245, :255, unverändert)
  -> Agent/Task-Pfad, Sentinel-Parse (:326), Projektwurzel, Git-Scan (:1330), Strict (:1419) ... (unverändert)
```

Persistenz: keine. Die Pfad-Liste (6 Pfade) deckt `:239`, `:269`, `:275`, `:280`, `:307`, `:384` ab. Hinweis:
`tool_input.command` wird heute nur für `Bash` gelesen (`:306-307`); künftig wird er für jedes Tool
gelesen und nur bei `Bash` verwendet (rein lesend, kein Verhaltensunterschied erwartet; Test AC-9).
`_SUBAGENT_TYPE` wird nachgelagert klein geschrieben (`tr`, wie `:280`); ob dafür ein Spawn entfällt, ist nicht
relevant (`tr` ist kein Python-Start).

## 4. Entscheidungspunkt: JSON-Gültigkeitsprüfung `:231`

Nicht entschieden (OQ-1). Zwei Optionen, jeweils mit statisch gezählter Spawn-Zahl:

| Option | Inhalt | Python-Starts Grundpfad | Differenz zu heute (9) | Plan-Akzeptanz „≥ 3 weniger" |
|---|---|---|---|---|
| **A** | `:231` entfällt; Parsefehler wird über rc/Abschlussfeld von `hook_json_get_many` erkannt (§2.3) | 5 (Probe, Mehrfeld, Sentinel, Git-Scan, Strict) | −4 | erfüllt |
| **B** | `:231` bleibt als eigener Start; Mehrfeld-Parse zusätzlich | 6 | −3 | erfüllt (Grenzfall) |

Beobachtung A: Die Prüfung `:231` akzeptiert jedes gültige JSON, auch Nicht-Objekte (`[]`, `1`); in beiden
Fällen endet der Guard danach über `tool_name` leer (`:245`) mit exit 2. Der Unterschied liegt nur in der
Fehlermeldung (`:234` „not valid JSON" vs. `:246` „no usable tool_name"). Bei A müsste eine Meldung für den
Fehlschlag des Mehrfeld-Parse gewählt werden (OQ-1).
Beobachtung B: bleibt mit minimalem Verhaltensunterschied (Meldungen identisch), aber mit +1 Spawn.
Der Planwert „≤ 5" ist nur mit A erreichbar.

## 5. Betroffene Stellen (Ziel-Symbole für Task 7)

| Datei | Stelle | Änderung |
|---|---|---|
| `hooks/1-generic/lib/hook_common.sh` | nach `:110` | neue Funktion `hook_json_get_many`; Header-Version `1.9.0` (`:3`) -> `1.10.0`, Changelog-Zeile (`:5`) |
| `hooks/1-generic/orchestrator-guard-impl.sh` | `:239`, `:269`, `:275`, `:280`, `:307`, `:384` | ein Aufruf + Konsum (§2.2); Reihenfolge der Vorbedingungen unverändert |
| `hooks/1-generic/orchestrator-guard-impl.sh` | `:231-237` | je OQ-1 entfernt (A) oder unverändert (B) |
| `hooks/1-generic/orchestrator-guard-impl.sh` | Prüfung `declare -F` `:199-202` | `hook_json_get_many` in die Liste der erforderlichen Funktionen aufnehmen (veraltete Lib fail-closed, wie `:203`) |
| `tests/test_hook_common_lib.py`, `tests/test_orchestrator_guard_hook.py` | — | Testmatrix §7 |
| Optional (OQ-2): `repo-containment-impl.sh` `:209`, `:272`, `:274`, `:276`, `:356` (5 Aufrufe), `dod-push-check.sh` `:98`, `:99` (2 Aufrufe) | — | eigener Commit |

Anmerkung Version: Block A (#1181 T16) und #1210 können `hook_common.sh`-Header ebenfalls anheben; die
Zielversion `1.10.0` ist daher an die tatsächliche Reihenfolge anzupassen (OQ-6).

## 6. Acceptance Criteria

Voraussetzung: Spec `APPROVED`. Format Given/When/Then; jedes AC referenziert einen Contract.

1. **AC-1 Gleiche Werte** (§2.1): Given Payload mit `tool_name`, `agent_id`, `tool_input.command`, `cwd`,
   When `hook_json_get_many` mit diesen vier Pfaden läuft, Then entsprechen die vier Felder den Ergebnissen
   von vier `hook_json_get`-Aufrufen (Test `test_hook_json_get_many_matches_single_gets`).
2. **AC-2 Zeilenumbrüche** (§2.1): Given `tool_input.command` mit `\n`, Then bleibt der Wert im Feld
   vollständig und unverändert (Test `..._keeps_newlines_in_command`).
3. **AC-3 Ein Spawn** (§2.1): Given PATH-Shim, der `python3`-Aufrufe zählt, When die Funktion mit ≥ 4 Pfaden
   läuft, Then genau 1 Aufruf (Test `..._single_python_spawn`).
4. **AC-4 Parsefehler** (§2.4): Given kein gültiges JSON, Then rc 1, stdout leer (kein Abschlussfeld).
5. **AC-5 Nicht skalar/nicht auflösbar** (§2.4): Given Pfad auf Objekt, Array, `null` oder fehlenden Schlüssel,
   Then leeres Feld an dieser Position, übrige Felder unverändert, Abschlussfeld `ok` vorhanden.
6. **AC-6 NUL im Wert** (§2.4): Given `{"tool_input":{"command":"a\u0000/evil"},"cwd":"/ok"}` und
   Pfade `tool_input.command cwd`, Then rc 1, stdout leer; `cwd` wird nie als `/evil` oder `/ok` an den
   falschen Platz geliefert (Test `..._nul_in_value_cannot_shift_fields`).
7. **AC-7 Bytes/Surrogate** (§2.1): Given Payload mit ungültigem UTF-8 bzw. `"\ud800"` im Wert, Then Ausgabe
   byte-identisch zu `hook_json_get` für dasselbe Feld (Muster der bestehenden v1.0.1-Tests).
8. **AC-8 Fehlender Interpreter** (§2.4): Given leerer PATH-Eintrag für `python3`/`python`, Then rc 1,
   stdout leer.
9. **AC-9 Guard unverändert** (§1.3): Given dieselben Payloads wie bisher, Then liefern
   `tests/test_orchestrator_guard_hook.py`, `test_hook_drift.py`, `test_repo_containment_hook.py`,
   `test_dod_push_check_hook.py` dieselben Ergebnisse; Zahl der Tests vor und nach vergleichbar; bestehende
   Tests unverändert.
10. **AC-10 Vorbedingungen-Reihenfolge** (§1.3): Given Payload ohne `tool_name`, ungültiges JSON, leerer
    Input, unbekanntes `tool_name`, Then jeweils exit 2 wie bisher (Meldung nach OQ-1).
11. **AC-11 NUL-Block im Guard** (§2.4): Given Bash-Payload mit NUL im Kommando, Then exit 2 (Stderr
    nennt die Ursache); kein Kommando wird ausgewertet.
12. **AC-12 Alte Lib** (§5): Given eine `hook_common.sh` ohne `hook_json_get_many`, Then exit 2 über den
    `declare -F`-Block (`:199-206`).
13. **AC-13 Spawn-Ziel** (§1.2): Given `scripts/bench_hooks.py --runs 5 --json` (Task 6), Then
    `python_spawns` für `bash-simple` ≤ Baseline − 3 (Option B) bzw. ≤ 5 absolut (Option A, Planwert);
    Ist-Wert im PR-Text; keine Zeitassertion.
14. **AC-14 Bash 3.2** (§2.2): Given der Konsum-Code, Then enthält er weder `mapfile`/`readarray`,
    Namerefs (`declare -n`, `local -n`) noch `eval` (statische Prüfung per Test); Lauf unter bash 3.2 nur,
    wenn verfügbar (OQ-5).
15. **AC-15 Validierung**: `python3 scripts/sync.py --validate` Exit 0; `tests/test_hook_drift.py` grün
    (gerenderte Hooks synchron).

## 7. Testmatrix (aus Plan Task 7, Step 1; erweitert)

| Fall | Payload / Setup | Erwartet |
|---|---|---|
| T1 `test_hook_json_get_many_matches_single_gets` | 4 Pfade, alle vorhanden | Felder = 4 Einzelaufrufe, Abschlussfeld `ok` |
| T2 `..._keeps_newlines_in_command` | Kommando mit `\n` | Wert unverändert |
| T3 `..._invalid_json_returns_defaults` | `not json` | **Soll nach dieser Spec: rc 1, stdout leer** (Plan-Name sagt „returns_defaults"; Abweichung, OQ-6) |
| T4 `..._single_python_spawn` | PATH-Shim | genau 1 Aufruf |
| T5 `..._nul_in_value_cannot_shift_fields` | `command="a\u0000/evil"`, `cwd="/ok"` | rc 1, kein Feld |
| T6 | Pfad nicht auflösbar / Objekt / `null` | leeres Feld, Rest unverändert |
| T7 | `"\ud800"` im Wert, invalides UTF-8 | identisch zu `hook_json_get` |
| T8 | kein Interpreter | rc 1, leer |
| T9 | Guard: Bash-Payload mit NUL | exit 2 |
| T10 | Guard: bestehende Fälle aus `test_orchestrator_guard_hook.py` | unverändert grün |
| T11 | Guard + alte Lib ohne Funktion | exit 2 |

Zusätzlich: Benchmark-Skript-Test (Task 6) nur Struktur, keine Zeitgrenze.

## 8. Abstimmung mit Phase H (#1161 Punkt 5)

Entscheidung 28 (Plan `:354`, Roadmap `:429-432`): #1169 in Phase D, #1161 Punkt 5 in Phase H; Spec vor der
Umsetzung mit Nutzerfreigabe. Der Roadmap-Eintrag führt #1161 Punkt 5 als „offen" mit Anker
`hook_common.sh:63` (Roadmap `:93`, „Subagent, ungeprüft"). Der Inhalt von #1161 Punkt 5 wurde in dieser
Session **nicht gelesen**. Damit die Funktion nicht doppelt entsteht: Phase H übernimmt `hook_json_get_many`
aus Task 7 (Name, Signatur, Abschlussfeld) unverändert, sofern der Nutzer diese Spec freigibt (OQ-3).

## 9. Nicht verifiziert

- Laufzeit-Spawn-Zahl und Latenz: nur statisch gezählt (9); Messung erst Task 6. Latenzwirkung pro
  Bash-Call nicht gemessen.
- Ob `hook_shell_scan_py` (`:533`) selbst einen Python-Start verursacht.
- Bedingung des Strict-Config-Starts `:1419` (Plan: nur wenn `project.yaml` vorhanden); Gate nicht im Detail
  gelesen.
- Zeile `:500` (Audit-Redaktion) aus dem Plan übernommen, nicht nachgemessen.
- Verhalten von `$(...)` bei NUL in bash 3.2 vs. bash 5 (Verwerfen/Warnung).
- Verfügbarkeit von `< <(...)` mit `read -r -d ''` unter macOS-bash 3.2.
- Inhalt von #1161 Punkt 5 (Issue-Text nicht gelesen) und #1226 (nicht im Log nachgesehen).
- Ob `tool_input.command` für Nicht-Bash-Tools Seiteneffekte bei der Mehrfachlesung hat (nur Lesen; nicht
  getestet).
- Ob andere Skripte (`lifecycle-check.sh:24-26`, `sync-on-config-change.sh:24-25`) von der Funktion profitieren
  sollen; außerhalb des Auftrags.

## 10. Risiken

- Sicherheitsdatei (`orchestrator-guard-impl.sh`, `hook_common.sh`): Refactor-Fehler können eine Fail-Open-Kante
  erzeugen. Mitigation: Reihenfolge der Vorbedingungen fix, AC-9/AC-10, Rückgabecode + Abschlussfeld.
- Feldverschiebung durch NUL: gemildert durch Ganz-Aufruf-Fehlschlag (AC-6, AC-11).
- Dateikonflikt: `orchestrator-guard-impl.sh` wird von Block A (#1181 T16), #1210, #1217 ebenfalls geändert;
  nur sequentiell (Plan `:103`). Task 5 selbst (diese Spec) berührt nur Dokumentation.
- Meldungstext-Änderung bei Option A kann Tests ändern, die `not valid JSON` erwarten (nicht geprüft).
- Verhaltensänderung für NUL-Payloads (§2.4).

## 11. Offene Fragen an den Nutzer

Keine ist entschieden; jede ist freigaberelevant.

1. **`:231` in den Mehrfeld-Parse?** Option A: 5 Spawns (−4), Parsefehler über rc/Abschlussfeld, neue
   Fehlermeldung nötig. Option B: 6 Spawns (−3), `:231` unverändert. Planwert „≤ 5" nur mit A erreichbar.
2. **`repo-containment-impl.sh` (5 Aufrufe) und `dod-push-check.sh` (2) ebenfalls umstellen** (Plan
   „Optional", eigener Commit)? Oder zunächst nur der Guard?
3. **Funktionsname/Signatur** mit Phase H (#1161 Punkt 5) abgestimmt? Wer pflegt die Funktion, falls H
   zuerst landet?
4. **Benchmark-Methode:** PATH-Shim `python3`, der Aufrufe zählt (Plan Task 6), akzeptabel? Misst sie
   `python`-Fallback-Aufrufe mit?
5. **Test-Umgebung bash 3.2 (macOS)** verfügbar? Ohne sie bleibt AC-14 statisch.
6. **Interface-Abweichungen vom Plan** (Abschlussfeld `ok`; Parsefehler = rc 1 statt leeres Feld; Test T3
   `..._returns_defaults` entsprechend umbenennen; Header-Zielversion): akzeptiert?
7. **NUL-Payloads blockieren** (Verhaltensänderung, §2.4) akzeptabel?
8. **Reihenfolge:** Task 7 (dieses Refactoring) vor oder nach Block A (#1181 T16, gleiche Datei)? Der Plan
   sieht nach Block A vor (`:262`, `:103`).

## 12. Trace-Anker

`spec-id: SPEC-HOOK-SINGLE-PARSE-2026-11-11`
