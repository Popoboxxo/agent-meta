# Freigabe-Vermerk (Rev 4) — `SPEC-1189-tmp-sink-pin-vs-system-temp`

> **Gegenstand:** `docs/specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-spec.md`,
> `Revision: 4`, `Status: DRAFT`.
> **Umfang:** ausschließlich RVW3-1 (blocking) und RVW3-2…RVW3-6 aus
> `…-rereview2.md`; alles davor gilt als abgenommen.
> **Methode:** Gegenlesen am Code (`datei:zeile`). **Nicht ausgeführt:** `sync.py`,
> `pytest`, `git`; keine Implementierung, keine Änderung der Spec, kein Commit.

## 1. RVW3-1 (blocking) — **geschlossen**

| Prüfpunkt | Befund |
|---|---|
| Option B umgesetzt | Ja: D6 Punkt 0, IC-12, IC-8 Schritt 2, Datenfluss 1, AC-17/17a/17b, ADR-1189-08, OQ-5 — durchgängig dieselbe Entscheidung. |
| **IC-12** (Bind-Probe) | `socket(family, SOCK_STREAM)` + `SO_REUSEADDR` (**kein** `SO_REUSEPORT`), `bind()`, `finally: close()`; **kein** `listen()`/`accept()` ⇒ kein `TIME_WAIT`, kein Leerzustand. Die Parität zum Kind ist strukturell korrekt (`_DaemonThreadingHTTPServer` :5817 erbt `allow_reuse_address = 1`; als ASSUMED markiert). `port == 0` ⇒ übersprungen; `OSError` ⇒ `(False, errno)` ohne Raise; Privilegienfall (`EACCES`) korrekt als Fehlschlag. |
| **IC-8 Schritt 2** | Probe **vor** jedem Spawn, belegter/nicht bindbarer Port ⇒ Exit 1 mit `host:port` + errno, **kein** Spawn, **keine** PID-Datei (Schreiben erst Schritt 4, vgl. Bestand `:6041`). `restart` erbt das Verhalten (Schritt 8, AC-18). |
| **Heuristik statt Garantie** | D6 Punkt 2, IC-7 „Was es nicht leistet", Datenfluss 1, AC-34: das Fenster wird ausdrücklich als Lebenslauf-Heuristik ausgewiesen; die Rev-3-Absolutaussage ist gestrichen (nur noch im Changelog zitiert). `START_CONFIRM_GRACE` steht als **Zeitannahme** in R11a, die Deadline-/Fenster-Semantik in IC-7 bleibt konsistent. |
| **TOCTOU ehrlich benannt** | R11 (Mechanismus korrigiert: „Kind hat am Fensterende noch nicht gebunden"), R11a (Zeitannahme), R16 (Probe→Kind-Bind), Threat-Model (g) mit Dreiteilung „deterministisch abgefangen / heuristisch begrenzt / nicht ausgeschlossen". |
| **AC-Trennung** | Sauber: AC-17 deterministisch (Pre-Flight), AC-17a Identität ohne Token (`pid`-Vergleich, nur token-frei prüfbar), AC-17b ausdrücklich heuristisch inkl. benanntem Restrisiko. AC-18/AC-34 verweisen korrekt darauf. |

## 2. RVW3-2…RVW3-6 — **eingearbeitet**

| Auflage | Befund (Beleg) |
|---|---|
| RVW3-2 Warnzeilentext | Wortlaut identisch in D7 (`:502-512`), IC-5a (`:745-747`) und AC-26 (`:1462`); „Text unverändert" ist gestrichen. Stream = stderr, Wortlaut `  !  tmp-sink pin unavailable: framework lib not importable; inheriting environment`. |
| RVW3-3 drei Docstrings | D8.4 nennt alle drei mit Zeilen und Zielaussage; am Code bestätigt: `admin-server.py:315-320` („keeps operating with the inherited env"), `consistency-check.py:80` („this helper never raises"), `cli_commands.py:193-196` („a CLI start never fails because of it"). AC-32 (`:1468`) + Test 31 decken es ab; vierte Kopie `:698-704` sprachlich angeglichen. |
| RVW3-4 „inhaltlich gleich" | IC-5a (`:729`, `:736-741`), AC-26 und Test 26c sagen übereinstimmend „gleicher Key-Set, gleiche Werte, **nicht** dasselbe Objekt"; `assert result is base` ausdrücklich unzulässig. Bestand kopiert (`run_role_routing_eval.py:705`). |
| RVW3-5 stdout | IC-5b (`:776-782`) legt stdout für die Lifecycle-Zeilen fest; Bestandsmuster `:6049-6051` ist `print(...)` ohne `file=` (verifiziert). AC-14 (`:1446`) untersagt den stderr-Test ausdrücklich. |
| RVW3-6 Belege/Form | `scripts/lib/eval_gate.py:278` enthält wörtlich `results = [runner() for runner in runners]` (Aufruf `run_role_routing_eval.py:1021`); U4-26a…**e** vollständig vorhanden (`:1368-1390`); „Pin pro Model-Klasse" (`:755-757`) und die zwei direkten `tmp_env`-Verbraucher (`:550-553`) sind aufgenommen. |

## 3. Neue Widersprüche zu abgenommenen Abschnitten?

**Keine.** D7 / IC-5a / IC-5b / AC-25 / AC-26 / AC-32 sind untereinander und mit IC-8/IC-12
deckungsgleich (Stream, Rückgabetypen, Exit-Codes, Warnzeile). Template-Checks bleiben grün
(`spec-id` gesetzt, `Status: DRAFT`, keine Platzhalter in Pflichtsektionen).

## 4. Hinweise für den Plan (nicht blocking)

1. **IC-12 Adressfamilie:** `getaddrinfo(...)[0]` kann von der Kind-Bindung abweichen — das
   Kind nutzt `socketserver`-Default **AF_INET** (`admin-server.py:5817`, kein
   `address_family`-Override). Bei `--host localhost` (`DEFAULT_ALLOWED_HOSTS:199`) wäre
   ::1 denkbar ⇒ falscher Durchlauf bzw. falscher Abbruch. Der Plan sollte die Probe-Familie
   an das Kind angleichen (U4-18b erweitern).
2. **IC-7 Formulierung** „(failed to start/PID-Datei)" (`:868-869`): Nach der Erfolgsmeldung
   ist der Elternprozess beendet — sichtbar ist der Fehlschlag über `status`/Log, nicht als
   `failed to start`-Zeile. Reine Wortpräzisierung.

## 5. Votum

**APPROVE** — keine blocking Findings. RVW3-1 ist wirksam geschlossen, RVW3-2…RVW3-6 sind
am Code belegt eingearbeitet; die Hinweise aus Abschnitt 4 sind Plan-Details.

**Freigabe durch den User möglich (`Status: APPROVED`).** Den Marker setzt ausschließlich der
User; danach schreitet `quality_pipelines.concept-driven-dev` fort (specify → review →
approve → plan), der Plan referenziert `spec-id: SPEC-1189-tmp-sink-pin-vs-system-temp`.

*Kein Code, keine Implementierung, keine Änderung der geprüften Spec, kein Commit.*
