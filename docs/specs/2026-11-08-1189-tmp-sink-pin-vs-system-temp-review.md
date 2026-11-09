# Review — Spec `SPEC-1189-tmp-sink-pin-vs-system-temp` (Issue #1189)

> **Gegenstand:** `docs/specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-spec.md`,
> Revision 1, `Status: DRAFT (2026-11-08)`, Klasse M.
> **Review-Typ:** Struktur-Review vor der Formal-/Implementierungsphase (Concept Reviewer).
> **Datum:** 2026-11-08 · Repo `agent-meta` @ `d12d4218`
> **Prüfmethode:** Gegenlesen am Code. Jede Aussage unten ist mit `datei:zeile` belegt
> (Stand der Arbeitskopie, keine Ausführung von `sync.py`/`pytest`).
> **Nicht Gegenstand:** Implementierung, Code-Review, Formulierung von REQ-IDs.

---

## 1. Votum

**APPROVE WITH CHANGES — in Revision 1 nicht approbierbar.**

Der Vorschlag ist inhaltlich richtig ausgerichtet: Die Kernentscheidung D1 trifft den
tatsächlichen Fehlbegriff, D2 ist gegen §5.5 und die Vorgänger-Spec **verifiziert
widerspruchsfrei**, und die Trennung von Symptom (`start`-Lüge) und Ursache (Semantik)
ist sauber. **REJECT ist deshalb nicht gerechtfertigt.**

Nicht approbierbar ist die Revision dennoch, weil **zwei tragende Aussagen der Spec am
Code falsch sind** und je eine verbindliche Festlegung an ihnen hängt:

| Blocker | Kern |
|---|---|
| **RVW-1** | IC-1/R1 begründen die prozessglobale Env-Mutation mit „wird nur in single-threaded Boot-/Validierungsphasen verwendet". Der Admin-Server ist ein `ThreadingHTTPServer`; der Fix verschiebt die Mutation genau in Request-Threads. |
| **RVW-2** | AC-1189-10 („bricht laut ab, kein stiller Wechsel") ist mit IC-5/IC-10 („`_tmp_sink_env` unverändert", `except Exception → None`) logisch unvereinbar — an 5 von 7 Pin-Stellen bleibt der Fehler stumm. |

Nach Behebung von RVW-1/RVW-2 und den Major-Auflagen (RVW-3…RVW-8, RVW-16) ist die Spec
approbierbar, ohne dass die Designrichtung wechseln muss.

**Votum-Mapping:** `CHANGES_REQUESTED` (zurück an den Autor) / `APPROVE WITH CHANGES`.

---

## 2. Findings

Legende Schweregrad: **blocking** = ohne Änderung nicht approbierbar ·
**major** = substanzielle Lücke, blockierend für die Umsetzung · **minor** = Verbesserung.

### RVW-1 — blocking · Risiken / Feasibility

**Befund.** IC-1 („Nebenläufigkeit") und R1 stützen die Zulässigkeit der prozessglobalen
Mutation von `os.environ` + `tempfile.tempdir` auf die Annahme, der Aufruf erfolge „nur in
single-threaded Boot-/Validierungsphasen". Diese Annahme ist für den Admin-Server **falsch**:

- `_DaemonThreadingHTTPServer(ThreadingHTTPServer)` mit `daemon_threads = True`
  (`scripts/admin-server.py:5817-5824`); jeder Request läuft in einem eigenen Thread.
- In Request-Threads wird `_tmp_sink_env` aufgerufen und damit `load_config` →
  `_validate_config` → `_validate_repo_containment` → `system_temp_root`:
  `SyncExecutor._run` (`:1352-1370`, via `POST /api/sync/dry-run|run`),
  `ConsistencyService.run_consistency_check` (`:1744-1750`, via `GET /api/consistency-check`),
  `VizManager._start` (`:640-660`, via Subserver-Restart-Endpoint).
- Startet der Server über `start`, ist er **selbst gepinnt** (`:6032/:6038`) — also ist
  `gettempdir() == sink` in genau dem Prozess, in dem diese Threads laufen. Der Pin-Fall ist
  damit der Normalfall, nicht die Ausnahme.

**Wirkung (worst case).** Während des Fallback-Fensters sind `TMPDIR`/`TEMP`/`TMP` aus
`os.environ` entfernt. Ein parallel laufender Thread, der in diesem Fenster einen
Kindprozess startet oder `tempfile` nutzt, erbt **keinen** Pin und schreibt in den
System-Temp — genau der Zustand, den D4 („Kein Aufrufer erbt wieder den System-Temp")
ausschließt. Zusätzlich kann ein verschachtelter Aufruf `tempfile.tempdir` in der falschen
Reihenfolge restaurieren. Das ist ein Containment-Leak, den der Fix **neu einführt**
(heute stirbt der gepinnte Prozess vorher).

**Änderungsauflage.**
1. IC-1 und R1 so umschreiben, dass sie die tatsächliche Aufrufumgebung nennen
   (`ThreadingHTTPServer`, Request-Threads, gepinnter Server).
2. Eine Nebenläufigkeitsmaßnahme festschreiben — mindestens ein modulweites
   `threading.RLock`, das Env-Mutation, Neuberechnung **und** Restore gemeinsam hält; besser:
   den Fallback ohne globale Mutation bestimmen (dokumentierte Kandidatenliste in
   `tempfile`-Reihenfolge, ohne `os.environ`/`tempfile.tempdir` anzufassen).
3. Restrisiko benennen: Ein `RLock` schützt nur Aufrufer **dieses** Helfers, nicht fremde
   `tempfile`-Nutzer im selben Prozess. Solange das Restrisiko besteht, gehört es als
   eigener Risiko-Eintrag (R10) in die Tabelle.
4. Wird die Mutation beibehalten, ist zusätzlich zu belegen, dass zwischen „Keys entfernen"
   und „Keys restaurieren" **kein** `subprocess`-Start stattfinden kann (Reihenfolge im
   `finally`).

**Beleg:** `scripts/admin-server.py:5817-5824`, `:1352-1370`, `:1744-1750`, `:640-660`,
`:6032/:6038`; `scripts/lib/config.py:669`, `:930-937`.

---

### RVW-2 — blocking · Logik / Widerspruch

**Befund.** D2 (Fehlerpfad) und AC-1189-10 verlangen: Ist unter Pin kein System-Temp-Root
bestimmbar, wird **laut** abgebrochen („nie still auf den Sink gewechselt"). IC-5 und IC-10
lassen `_tmp_sink_env` dagegen ausdrücklich **unverändert** — inklusive
`except Exception: return None` (`scripts/admin-server.py:334-335`,
`scripts/consistency-check.py:74-95`, `scripts/lib/cli_commands.py:188-210`).
`TmpSinkError` ist eine `Exception` und wird dort geschluckt. Ergebnis: `Popen(env=None)` →
das Kind erbt die Env des Aufrufers und läuft **ungepinnt**. Das ist exakt der von D4
ausgeschlossene Zustand — und er tritt still auf, ohne Meldung.

Dasselbe gilt für `resolve_tmp_paths` in `_tmp_sink_env`: Jeder `TmpSinkError`
(`tmp-sink.invalid-path`, `tmp-sink.system-temp-exception`) endet dort als „kein Pin".

**Änderungsauflage.** Eine der beiden Aussagen muss fallen:
- **(a)** AC-1189-10 auf die Stellen einschränken, an denen der Fehler tatsächlich
  propagiert (`_validate_repo_containment`, `resolve_pytest_basetemp` in
  `_build_orch_variables`), und für die Pin-Helfer explizit festhalten, dass ein
  `TmpSinkError` zu „Kind ungepinnt" führt — dann ist D4s Satz „kein Aufrufer erbt wieder
  den System-Temp" zu relativieren; **oder**
- **(b)** IC-5/IC-10 ändern: `_tmp_sink_env` reicht `TmpSinkError` weiter (bzw. meldet ihn
  und bricht den Start ab), sodass die Invariante hält. Das ist eine bewusste Abkehr von
  „Verhalten unverändert" und muss in der Nicht-Ziel-Liste korrigiert werden.

**Beleg:** `scripts/admin-server.py:325-335`; `scripts/lib/tmp_paths.py:146-205`;
`scripts/lib/config.py:2058-2061` (dort wird `TmpSinkError` → `SyncError` **nicht**
geschluckt — der Unterschied zwischen den Aufrufern ist heute schon inkonsistent).

---

### RVW-3 — major · Vollständigkeit (Interface-Contract falsch)

**Befund.** IC-1 sagt: „die Funktion legt keine Dateien/Verzeichnisse an" und AC-1189-11
prüft nur Env-/Cache-Restore. Der vorgeschriebene Mechanismus — Cache invalidieren und
`tempfile.gettempdir()` erneut rufen — löst in CPython `_get_default_tempdir()` aus, das
jeden Kandidaten durch **Anlegen und Löschen einer Probe-Datei** auf Beschreibbarkeit prüft.
Es entstehen also transiente Schreibzugriffe (außerhalb des Repos, im Kandidatenverzeichnis)
und es kann `FileNotFoundError`/`PermissionError` geworfen werden, wenn kein Kandidat
beschreibbar ist.

**Wirkung.** (a) Der Vertrag ist falsch, was bei der Implementierung zu einer
Gewissensfrage führt (Docstring vs. Realität). (b) In einem Containment-Kontext ist „der
Validator schreibt außerhalb des Repos" erklärungsbedürftig. (c) AC-1189-10 deckt nur
„`tempfile` wirft" ab, nicht die Semantik „Kandidat nicht beschreibbar".

**Änderungsauflage.** IC-1 präzisieren: „keine persistenten Artefakte; `gettempdir()` führt
eine transiente Beschreibbarkeitsprobe im gewählten Kandidaten aus (Stdlib-Verhalten);
`OSError` beim Bestimmen → `TmpSinkError('tmp-sink.system-temp-exception', …)`."
AC-1189-11 um „keine persistenten Artefakte" ergänzen, AC-1189-10 um den OSError-Fall.

**Beleg:** `tempfile.gettempdir()` → `_get_default_tempdir()` (CPython-Stdlib, Probe-Datei
per `os.open(..., O_CREAT|O_EXCL)`); Ziel-Mechanik in IC-1/D2 der Spec.

---

### RVW-4 — major · Logik (Invariante nicht definiert)

**Befund.** Ziel 2, D2 und AC-1189-04/09 fordern: „Der Pin darf das aufgelöste Ergebnis
nicht verändern", „`TmpPaths` unter Pin == `TmpPaths` ohne Pin". Die Baseline „ohne Pin" ist
nirgends definiert. Meint sie die Env des Aufrufers **mit** seinem echten `TMPDIR`
(z. B. `/var/folders/…` auf macOS, ein Custom-Temp auf einem CI-Runner), dann ist die
Invariante **unhaltbar**: Der Pin überschreibt den Custom-Temp; der Fallback liefert
`/tmp` (Linux) bzw. den Plattform-Default — also gerade **nicht** den Wert des ungepinnten
Laufs. Die Invariante gilt nur gegenüber der Baseline „Env des Aufrufers **ohne** die drei
Sink-Keys".

**Wirkung.** (a) AC-1189-04 ist als geschrieben nicht erfüllbar, sobald die Maschine einen
echten Custom-`TMPDIR` hat. (b) U2-8 („unter Pin == ohne Pin") ist plattformabhängig: ein
Test, der die Baseline per `monkeypatch.delenv` herstellt, vergleicht gegen `/tmp` und
schlägt auf macOS/CI fehl; ein Test, der die Baseline vor dem Pinnen einfängt, ist korrekt.

**Änderungsauflage.** Baseline in Ziel 2/D2 definieren („identisch zu einem Lauf in derselben
Env **ohne** die framework-gesetzten Temp-Keys"), AC-1189-04 entsprechend umformulieren,
U2-8 die Baseline-Ermittlung vorschreiben (Wert **vor** dem Pinnen erfassen, nicht per
`delenv`). Zusätzlich in D2 festhalten, dass der Pin einen echten Custom-Temp-Root bewusst
verdeckt (das ist heute schon so und bleibt so).

**Beleg:** `scripts/lib/tmp_paths.py:220-224`, `:250-284`; Spec D2/AC-1189-04/U2-8.

---

### RVW-5 — major · Vollständigkeit (nicht erfasster Verbraucher)

**Befund.** `tests/conftest.py::effective_basetemp` (`:45-59`) leitet den effektiven
pytest-Basetemp aus `os.environ["TMPDIR"]` bzw. `tempfile.gettempdir()` ab und warnt
warning-only, wenn er im Repo liegt. In einer **gepinnten Agent-Shell** (Normalfall: der
gerenderte `TMP_SINK_ENV_PIN_BLOCK` exportiert `TMPDIR=<sink>`) nutzt pytest ohne
`--basetemp` weiterhin `<root>/.tmp` als Basetemp-Root — also genau den In-Repo-Basetemp,
den §5.5 Punkt 1 verbietet. D1 kann das nicht heilen (es ist pytest-Verhalten, nicht
Framework-Verhalten), aber die Spec behauptet in Ziel 3/AC-1189-23 „§5.5 bleibt" ohne diese
Grenze. `tests/conftest.py` fehlt in der Aufrufer-Tabelle.

**Wirkung.** Ein Agent, der `python3 -m pytest tests/` ohne `--basetemp` in seiner gepinnten
Shell ausführt, reproduziert den Ancestor-Kollisions-Zustand (13 Fehlschläge) samt
Rekursionsrisiko — mit nur einer Warnung als Signal. Das ist keine Regression dieser Spec,
aber eine **dokumentationspflichtige Grenze**, sonst liest sich Ziel 3 wie eine Garantie.

**Änderungsauflage.** `tests/conftest.py::effective_basetemp` in die Tabelle
„Betroffene Komponenten" als *unverändert, aber semantisch betroffen* aufnehmen; in D2/Ziel 3
einen Satz zur Grenze ergänzen („für den **gerenderten** Aufruf; ein ungebaseter
pytest-Lauf erbt weiterhin den Pin und wird nur gewarnt"); AC-1189-23 auf „gerendert"
schärfen.

**Beleg:** `tests/conftest.py:45-76`; `docs/concepts/repo-containment-prison-mode.md:413-433`.

---

### RVW-6 — major · Risiken (neuer Credential-Pfad, kein Threat Model)

**Befund.** IC-7/D6 senden bei gesetztem Token `Authorization: Bearer <token>` an
`GET /api/health`. `/api/health` ist token-gated (`scripts/admin-server.py:3514-3524`,
`:3541-3545`, `:3794-3799`) — der Header ist also **erforderlich**. Genau deshalb geht der
Admin-Token an **den Prozess, der auf dem Port lauscht** — auch wenn das der Fremdprozess
ist, den AC-1189-17 erkennen soll. Der Token ist kein Wegwerf-Secret: er autorisiert
Konfigurationsschreiben (`PUT`) und Sync-Läufe.

**Wirkung.** Ein lokaler Angreifer, der den Port vor dem Start belegt, erhält den
Admin-Token, bevor der Start als „fehlgeschlagen" erkannt wird. Das ist ein neuer
Angriffsvektor, der im Dokument weder als Risiko (R1–R9) noch in einem Threat-Model-Abschnitt
auftaucht.

**Änderungsauflage.** (1) Threat-Model-Kurzabschnitt (4 Fragen, siehe §4 unten) ergänzen.
(2) Gegenmaßnahme oder bewusste Akzeptanz festschreiben, z. B.: Token erst senden, wenn der
Listener eindeutig als eigener Prozess erkannt ist (PID-/Port-Ownership), oder zweistufig
probieren (unauthentifizierter `GET /` als Lebendigkeit, Token nur nach 401-Antwort mit
passendem `version`-Feld), oder explizit „akzeptiert, weil lokal" dokumentieren.
(3) Neuer Risiko-Eintrag R10.

**Beleg:** `scripts/admin-server.py:3514-3524`, `:3541-3545`, `:887-906`, `:3794-3799`.

---

### RVW-7 — major · Feasibility (Proxy/Redirect im Health-Aufruf)

**Befund.** IC-7 legt die HTTP-Probe nicht fest. `urllib.request.urlopen` respektiert
standardmäßig `http_proxy`/`HTTP_PROXY`/`no_proxy` — in Firmen-/CI-Umgebungen ist das
gesetzt. Eine Probe auf `http://127.0.0.1:<port>/api/health` kann dann über einen Proxy
laufen; mit RVW-6 wird der Bearer-Token an diesen Intermediär gesendet. Zusätzlich folgt
`urlopen` standardmäßig Redirects.

**Wirkung.** Credential-Exposure an einen Proxy; im schlechtesten Fall falscher
Start-Erfolg/‑Fehlschlag, weil ein Proxy-Errorbody als Health-Antwort interpretiert wird.

**Änderungsauflage.** IC-7 um zwei explizite Vertragspunkte ergänzen:
`build_opener(ProxyHandler({}))` (kein Proxy) und **kein** Redirect-Following
(`HTTPRedirectHandler` deaktiviert), plus den Hinweis, dass nur `http://` auf Loopback
(bei Wildcard-Bind) geprobt wird. Test U4-15 um einen Fall „Proxy-Env gesetzt, Probe geht
trotzdem direkt" erweitern.

**Beleg:** `scripts/admin-server.py:378-383` (Health-Payload), IC-7 der Spec.

---

### RVW-8 — major · Logik (PID-Lebenszyklus / Race)

**Befund.** IC-8 Schritt 4 verlegt das Schreiben der PID-Datei hinter die Verifikation
(Deadline default 5 s). In diesem Fenster gilt: `status` meldet „nicht laufend"
(`_read_pid` → `None`), `stop` findet keine PID und beendet nichts, ein zweiter `start`
sieht kein „already running". Heute wird die PID-Datei sofort geschrieben
(`scripts/admin-server.py:6041`) und bei Fehlschlag entfernt (`:6050`).

**Wirkung.** Ein während der Verifikation abgesetztes `stop` hinterlässt einen laufenden
Server ohne PID-Datei (Orphan, nur noch per `pkill` auffindbar). Kein Risiko-Eintrag deckt
das ab.

**Änderungsauflage.** Entweder PID-Datei weiterhin sofort schreiben und nur die
**Erfolgsmeldung** an die Verifikation binden (bei Fehlschlag löschen — heutiges Muster),
oder das Fenster explizit als Risiko aufnehmen und das `stop`-Verhalten in diesem Fenster
definieren. AC-1189-14 („PID-Datei existiert nicht") ist an die gewählte Variante anzupassen.

**Beleg:** `scripts/admin-server.py:5995-6051`, `:673-690`.

---

### RVW-16 — major · Konsistenz (Entscheidung vs. „offene Frage")

**Befund.** D1–D6 sind als „Entscheidungen (verbindliche Zielsemantik)" überschrieben und
tragen je eine verworfene Alternative mit Begründung. Dieselben Fragen stehen in der
OQ-Tabelle als **offen** und werden mit „User-Bestätigung im Approval" versehen
(OQ-1 ↔ D1/ADR-1189-03, OQ-2 ↔ D6/IC-7, OQ-3 ↔ IC-9/AC-1189-20). OQ-4 ist keine Frage,
sondern eine redaktionelle Pflicht (§5.5-Satz), die zusätzlich die Vorgänger-Spec erfassen
muss (Option C definiert „Temp-Root" wörtlich als `tempfile.gettempdir()`).

**Wirkung.** Der Approval-Marker würde ein Dokument bestätigen, das seine eigenen
Festlegungen gleichzeitig zur Disposition stellt. Für den Plan ist damit unklar, ob er an
D1/D6 oder an einer noch zu treffenden Entscheidung hängt.

**Änderungsauflage.** OQ-1…OQ-3 entfernen oder auf „bestätigt (siehe Dx/ADR-1189-0y)"
reduzieren; OQ-4 in eine verbindliche Dokumentationsauflage umwandeln (§5.5 **und**
Vorgänger-Spec mit Verweis auf diese Spec; Verweis zusätzlich im Trace-Anker).

**Beleg:** Spec §Entscheidungen (D1–D6), §Offene Fragen, §Trace-Anker;
`docs/specs/2026-10-24-tmp-sink-injection-spec.md:616-631`.

---

### RVW-9 — minor · Vollständigkeit (Regressionstest ohne Beweiskraft)

**Befund.** AC-1189-05 und U3-11 verlangen „Default-Block **und** expliziter Block". Der
Validator prüft den Temp-Root aber ausschließlich **innerhalb** von
`if exception is not None:` (`scripts/lib/config.py:892`, nach `:866`). Fehlt der Block,
wird `tempfile.gettempdir()` nie erreicht; `load_config` ruft den Resolver nicht auf. Der
„Default-Block"-Teil von AC-1189-05 ist damit **vor dem Fix schon grün** — er testet nichts.
Der unter Pin wirksame Default-Pfad ist `resolve_pytest_basetemp`
(`scripts/lib/tmp_paths.py:250-284`), nicht der Validator. Folgerichtig ist auch die
Matrix-Zeile 5 („Block fehlt … wie Zeile 1, der wichtigste Regressionsfall") falsch
verortet: Für den Validator ist sie ein No-op.

**Änderungsauflage.** AC-1189-05 auf den expliziten Block beschränken; den Default-Fall als
Resolver-Regression (U2-7/8) benennen; Matrix-Zeile 5 korrigieren („kein Fehler, weil der
Validator hier nicht prüft; der Schutz kommt aus IC-3").

**Beleg:** `scripts/lib/config.py:864-866`, `:892`, `:930-937`;
`tests/test_tmp_sink_path_hardening.py:246-255` (`test_config_load_with_tmpdir_in_sink`
bleibt heute grün, obwohl `gettempdir() == <root>/.tmp` — Beweis der Lücke).

---

### RVW-10 — minor · Konsistenz (Zitat)

**Befund.** Die Spec schreibt: „`AdminServer.start` setzt
`AdminRequestHandler.version = self._read_version()` (`admin-server.py:5912`)". Zeile 5912
liegt in `AdminServer.__init__` (Beginn `:5850`); `start` beginnt bei `:5945`. Das
Verhalten (Boot-Abbruch vor `serve_forever`) ist korrekt beschrieben, nur die Zuordnung
nicht.

**Änderungsauflage.** Zitat auf `AdminServer.__init__` (`:5906-5918`, `_read_version`
`:5920-5931`) korrigieren; optional ergänzen, dass `viz_manager.start_all()` (`:5950-5952`)
denselben Pfad ein zweites Mal betritt.

---

### RVW-11 — minor · Risiken (`mode` ist kein Identitätsmerkmal)

**Befund.** AC-1189-17/D6 nutzen `mode` als Unterscheidung „unser Server vs. Fremdprozess".
`mode` hat nur zwei Werte (`detect_mode`, `:1036-1044`) und ist für jeden lokalen Listener
trivial fälschbar. Der Schutz greift nur zufällig.

**Änderungsauflage.** Empfehlung: `/api/health` additiv um `pid` und/oder `root` erweitern
und den Wert gegen den erwarteten Prozess prüfen (keine Schema-Änderung, nur Antwortfeld).
Alternativ in D6 als bewusste Schwäche dokumentieren.

**Beleg:** `scripts/admin-server.py:1036-1044`, `:3794-3799`.

---

### RVW-12 — minor · Risiken (Stale Pin nach Sink-Pfadwechsel)

**Befund.** D1 begründet den Pfadvergleich u. a. mit „funktioniert … nach einem Repo-Umzug".
Für einen **Pfadwechsel** des Sinks gilt das nicht: Ein in der Shell noch exportierter
alter Pin (`<root>/.tmp`) ist nach `tmp-sink.path: scratch` nicht mehr der Sink, liegt aber
weiterhin im Repo → harter Abbruch (`tmp-sink.system-temp-exception`) bei **jedem**
CLI-Start in dieser Shell, mit einer Meldung, die den Pin nicht als Ursache nennt.

**Wirkung.** Ein Konfigurationswechsel, der heute harmlos ist, führt zu einem
Boot-Totalschaden mit irreführender Diagnose — dieselbe Fehlerklasse, die die Spec behebt.

**Änderungsauflage.** Risiko-Eintrag ergänzen und die Fehlermeldung (IC-4) um einen
Reparaturhinweis erweitern („wenn dies ein veralteter Framework-Pin ist: neue Shell öffnen
oder `sync.py` erneut ausführen"). Optional: die Meldung nennt zusätzlich, ob der
Temp-Root ein In-Repo-Verzeichnis ist, das dem Muster `<root>/<tmp-sink-path>` *nicht*
entspricht.

**Beleg:** `scripts/lib/config.py:930-937`; `scripts/lib/tmp_paths.py:316-356`
(Pin-Block exportiert absolute Werte).

---

### RVW-13 — minor · Konsistenz (Docstring-Aussage wird falsch)

**Befund.** `repo_containment.tmp_sink_location_error` behauptet: „Only place that consults
`tempfile.gettempdir` in the sink context" (`scripts/lib/repo_containment.py:363`). Nach
IC-1 liegt mit `system_temp_root` ein zweiter Konsument im selben Modul. Die Funktion fehlt
zudem in der Komponententabelle.

**Änderungsauflage.** Docstring-Anpassung als Teil von IC-1/IC-2 ausweisen (Doku, kein
Verhalten); die Funktion in der Tabelle als „unverändert, aber vom selben Begriff abhängig"
führen. Erfreulich: `tmp_sink_location_error` ist bereits heute der **Präzedenzfall** für
D1 — „A sink inside the project root is always valid, even when the platform temp dir points
into it (TMPDIR=<root>/.tmp, #1136)" (`:360-367`, Test
`tests/test_tmp_sink_path_hardening.py:218-222`). Das gehört als Begründungsbeleg in D1.

---

### RVW-14 — minor · Teststrategie (Testkonvention widersprüchlich)

**Befund.** U1-2/U1-3 verlangen `monkeypatch.setenv` **plus** Reset von `tempfile.tempdir`.
Die bestehenden Tests modellieren den Temp-Root dagegen durch
`monkeypatch.setattr(tempfile, "gettempdir", …)` (u. a. `tests/test_tmp_paths_builder.py:296`,
`tests/test_repo_containment_validate.py:337`, `tests/test_tmp_sink_output_dirs.py:370/393/403/571`,
`tests/test_tmp_sink_path_hardening.py:211/221/230/241/253`). Mit gepatchtem `gettempdir`
liefert der Fallback **wieder** den Sink — AC-1189-02 („außerhalb root, ≠ Sink") ist dann
nicht erfüllbar, und die Implementierung muss entweder eine Endlosschleife oder einen
`TmpSinkError` erzeugen.

**Änderungsauflage.** Eine Testkonvention festschreiben: Pin-Fälle **env-basiert**
(`setenv` + `tempfile.tempdir = None`), `gettempdir`-Patch nur für die Fälle, die
„Temp-Root = Projekt-Root" modellieren. Zusätzlich definieren, was `system_temp_root` tut,
wenn der neu bestimmte Wert **erneut** gleich dem Sink ist (lauter Abbruch, nie Rückgabe des
Sinks) — das ist eine Vertragslücke in IC-1, die U1-2 sonst als Endlosschleife implementiert.

---

### RVW-15 — minor · Konsistenz (Scope-Kopplung)

**Befund.** Die Spec bündelt zwei unabhängige Defekte: Semantik (D1–D4, IC-1…IC-5) und
Start-Robustheit (D5/D6, IC-6…IC-9). Die Risikoprofile unterscheiden sich erheblich
(reine Pfadlogik vs. HTTP, Token, Prozess-Lifecycle, Windows, `/proc`). Die Bündelung ist
begründbar (der falsche Erfolg hat die Diagnose des eigentlichen Bugs verhindert), sie muss
aber steuerbar bleiben.

**Änderungsauflage.** Kein Split der Spec, aber im Plan zwei getrennt revertierbare
Commit-Einheiten vorsehen (Semantik zuerst, Start-Robustheit danach) und die Abhängigkeit
vermerken: Die Start-Robustheit ist ohne den Semantik-Fix testbar, aber der End-to-End-Nachweis
(AC-1189-14 mit echter tmp-sink-Zeile im Log-Tail) braucht beide.

---

## 3. Prüfaufträge im Einzelnen

### 3.1 Vollständigkeit: Aufrufer und Fehlerpfade

Alle in der Spec genannten Symbole existieren und sind korrekt zugeordnet
(`admin-server.py:311-335`, `:640-660`, `:1369`, `:1749`, `:6032/:6038`;
`consistency-check.py:74,105,112,128`; `cli_commands.py:188,575,1732`;
`run_role_routing_eval.py:697,729`). Die Korrektur zur Auftrags-Zuordnung (:6032/:6038 =
`_admin_start_detached`, nicht Viz) ist **verifiziert richtig** (`VizManager._start` liegt
bei `:621-671`).

Die Liste der `gettempdir()`-Konsumenten im Produktivcode ist vollständig
(`tmp_paths.py:223,276,280`, `repo_containment.py:380`, `config.py:931`) — alle drei
Fundstellen sind abgedeckt. **Zwei Lücken:** `tests/conftest.py:45-59` (RVW-5) und die
Docstring-Aussage in `repo_containment.py:363` (RVW-13). Der zweite Fehlerpfad (gepinnte
aufrufende Shell → `SystemExit` aus `load_config`) ist korrekt beschrieben:
`except Exception` fängt `SystemExit` nicht (`admin-server.py:334`, `cli_commands.py:204`,
`consistency-check.py:89`).

### 3.2 D2 gegen §5.5 und die Vorgänger-Spec: **konsistent**

Geprüft und bestätigt:

- §5.5 Punkt 1: „Der pytest-Basetemp darf NIE im Arbeitsbaum liegen"
  (`docs/concepts/repo-containment-prison-mode.md:413-417`).
- Vorgänger-Spec, Option A (`<sink>/pytest`) ist mit der Ancestor-Kollisions-Begründung
  **abgelehnt**, Option C („System-Temp … `tempfile.gettempdir()`, **kein** `/tmp`-Literal")
  ist die freigegebene Wahl (`docs/specs/2026-10-24-tmp-sink-injection-spec.md:586-631`).
- `PYTEST_BASETEMP`/`TEST_COMMANDS` werden aus dem Resolver gespeist
  (`scripts/lib/config.py:2059-2071`), der Token wird als `--basetemp="<path>"` eingesetzt
  (`:781-783`). Ein `<sink>/pytest`-Wert würde also tatsächlich das gerenderte Artefakt
  verändern — D2s Begründung (2) trifft zu.
- `tmp_sink_env_pin_block` exportiert ausschließlich absolute Werte
  (`scripts/lib/tmp_paths.py:316-356`) — ADR-12 unberührt, wie in der Spec behauptet.

**Ergebnis:** Die Abweichung von der Auftragsskizze (D2) ist **korrekt und begründet**. Sie
ist keine Meinungsfrage; sie folgt zwingend aus §5.5 plus der bereits getroffenen
Option-C-Entscheidung. Kein Finding.

*Ergänzung (in RVW-13/RVW-16 eingearbeitet):* Die Vorgänger-Spec definiert
„System-Temp-Root" wörtlich als `tempfile.gettempdir()`. D1 ändert diese Definition. Die
Spec sagt „Vorgänger bleibt gültig / wird nicht ersetzt" — das ist nur haltbar, wenn dort
ein Verweis ergänzt wird. Das ist eine Doku-Pflicht, keine Designänderung.

### 3.3 Belastbarkeit der 24 AC-IDs

Alle 24 sind vorhanden und formal prüfbar formuliert (jeweils beobachtbares Ergebnis, keine
Wunschformulierung). Schwächen:

| AC | Befund |
|---|---|
| AC-1189-04 | Baseline nicht definiert → nicht erfüllbar bei echtem Custom-`TMPDIR` (RVW-4) |
| AC-1189-05 | „Default-Block"-Hälfte ist vor dem Fix bereits grün (RVW-9) |
| AC-1189-10 | widerspricht IC-5/IC-10 (RVW-2); OSError-Fall fehlt (RVW-3) |
| AC-1189-11 | prüft Env/Cache, nicht „keine persistenten Artefakte" (RVW-3) |
| AC-1189-17 | `mode` als Identitätsmerkmal zu schwach (RVW-11) |
| AC-1189-23 | „gerendert" fehlt → liest sich als Garantie für alle Basetemp-Pfade (RVW-5) |
| AC-1189-24 | bündelt zwei verschiedene Prozesse (Eltern-CLI und Kind-Boot) in einem Kriterium |

**Zur Frage „fehlt ein AC für den Pfad ‚gepinnte aufrufende Shell → SystemExit in
`AdminServer.start`/`_read_version`'?"** — Er ist **teilweise** gedeckt: AC-1189-24 nennt
`admin-server.py start`, U4-19 prüft `_tmp_sink_env` in einem gepinnten Prozess. Nicht
gedeckt ist der **Kind-Boot selbst**: kein AC und kein Test verlangt, dass
`AdminServer.__init__`/`_read_version` unter gepinnter Env ohne `SystemExit` durchläuft
(Test 14 mockt `Popen`, Test 19 prüft nur den Helfer). AC-1189-24 kann außerdem allein durch
den Eltern-Pfad erfüllt werden, ohne dass das Kind je startet — die Formulierung ist
disjunktiv („der Server startet bzw. die Validierung endet Exit 0").

**Änderungsauflage:** AC-1189-24 in drei Kriterien teilen:
- **24a** Eltern-CLI: `_admin_start_detached` überlebt gepinnte Env, kein `SystemExit` aus
  `_tmp_sink_env`, erreicht `Popen`.
- **24b** Kind-Boot: `AdminServer.__init__` (inkl. `_read_version`) unter gepinnter Env
  liefert eine Version, kein `SystemExit`; analog `viz_manager.start_all()`.
- **24c** `sync.py --validate` unter Pin endet Exit 0 (bestehender Inhalt).

### 3.4 Risiken R1–R9

Vollständig für die Semantik-Seite, **lückenhaft** für die neue Betriebsseite: RVW-1
(thread-safety-Prämisse falsch), RVW-8 (PID-Fenster), RVW-12 (Stale Pin), RVW-6 (Token),
RVW-7 (Proxy). R8 ist ehrlich formuliert, unterschlägt aber zwei Punkte:

- **Zu „kann ein einmal gecachter `tempfile.tempdir` den Vergleich verfälschen?"** — Ja,
  aber nur in eine Richtung und nur theoretisch: `gettempdir()` liefert den **Cache-Wert**;
  ist er vor dem Pinning berechnet worden, wird der Pin nicht erkannt (der alte Fehler
  bliebe). Praktisch irrelevant, weil der Pin per Env vor dem Exec des Kindes gesetzt wird
  und der Cache beim Prozessstart leer ist. **Relevant** ist die umgekehrte Richtung, die
  R8 nicht nennt: Ein **falsch restaurierter** `tempfile.tempdir` (Restore-Reihenfolge,
  Ausnahme im `finally`) würde den Prozess nach dem Aufruf auf den System-Temp umschalten —
  ein Containment-Leak, den AC-1189-11 nicht erkennt (es prüft nur den Rückgabewert von
  `gettempdir()`). Der Vertrag muss „Restore vor Rückkehr, auch wenn der Fallback wirft"
  zusätzlich als **Reihenfolge** festschreiben (Env zuerst, `tempfile.tempdir` danach exakt
  auf den vorherigen Wert — inklusive `None`).
- Die Beschreibung „Fallback bleibt korrekt, solange die Kandidatenliste Env-basiert ist
  (CPython 3.9–3.13 ASSUMED)" ist korrekt als Annahme markiert; zu ergänzen ist, dass auf
  Linux nur `TMPDIR` wirkt (`TEMP`/`TMP` sind Windows), sodass U1-3 („nur `TMPDIR` gesetzt")
  auf Linux trivial ist und auf Windows anders aussieht — der Test braucht eine
  Plattform-Notiz.

### 3.5 Offene Fragen OQ-1…OQ-4

**Keine der vier ist entscheidungsbedürftig — drei sind Scheinfragen, eine ist eine
verkleidete Pflicht.** Die Spec beantwortet sie im selben Dokument:

| OQ | Status im Dokument | Bewertung |
|---|---|---|
| OQ-1 (pfadbasiert vs. Marker) | D1 „Entscheidung", ADR-1189-03, verworfene Alternative mit Begründung | entschieden → OQ streichen oder auf „bestätigt" setzen |
| OQ-2 (Health Pflicht vs. Best-Effort) | D6 „Entscheidung", IC-7, AC-1189-17 | entschieden → dito |
| OQ-3 (VizManager Deadline) | IC-9, AC-1189-20, ADR-1189-04 | entschieden → dito |
| OQ-4 (§5.5-Satz) | „Empfehlung: ja, rein redaktionell im Plan" | keine Frage, sondern eine **Dokumentationspflicht**; sie muss verbindlich werden und zusätzlich die Vorgänger-Spec (Option C, `tempfile.gettempdir()`) erfassen |

**Widerspruch:** Ein Dokument, das D1–D6 als „verbindliche Zielsemantik" markiert und
dieselben Fragen als „offen" führt, kann nicht widerspruchsfrei approbiert werden — der
Approval-Marker würde eine Selbstaussage bestätigen, die das Dokument an anderer Stelle
aufhebt. (RVW-16)

### 3.6 Threat-Model-Kurzcheck (4 Fragen)

Die Spec hat **keinen** Threat-Model-Abschnitt. Kurzcheck für die Änderung an der
Containment-Grenze:

1. **Was wird gebaut?** Ein neuer öffentlicher Resolver (`system_temp_root`,
   `resolve_sink_absolute`) in `repo_containment`, eine Neudefinition von
   „System-Temp-Root", eine HTTP-Health-Probe mit Bearer-Token im CLI, eine
   Zombie-Erkennung über `/proc`. Keine neuen Daten, keine neuen Endpunkte, kein Schema.
2. **Was kann schiefgehen?**
   (a) Token an einen Fremdprozess auf dem Port (**RVW-6**) und an einen `http_proxy`
   (**RVW-7**);
   (b) temporäre Env-Mutation in Request-Threads → Kindprozess ohne Pin (**RVW-1**);
   (c) stiller Rückfall auf „ungepinnt" statt lauter Abbruch (**RVW-2**);
   (d) transiente Schreibprobe außerhalb des Repos während der Validierung (**RVW-3**);
   (e) Fehlklassifikation als „Pin", obwohl ein echter In-Repo-Temp-Root vorliegt — nur bei
   exakter Sink-Gleichheit möglich, in D3 bewusst akzeptiert und begründet.
3. **Was wird dagegen getan?** Für (b)–(e) existieren Festlegungen (IC-1, D2, D3), aber (b)
   und (c) sind in der vorliegenden Fassung nicht durchgehalten; für (a) existiert **keine**
   Maßnahme.
4. **Konsequenzen.** Ein Leck des Admin-Tokens erlaubt Konfigurationsschreiben und
   Sync-Läufe über die UI (Integrität, nicht Vertraulichkeit); ein ungepinnter Kindprozess
   verletzt die Containment-Zusage, ohne dass es jemand merkt (Reputations-/Vertrauensverlust
   in die Regel). Beides ist bei einem Werkzeug mit „Convention boundary"-Anspruch
   dokumentierbar, aber nicht stillschweigend.

**Auflage:** Kurzabschnitt „Threat Model (4 Fragen)" in die Spec aufnehmen; er ist bei einer
Änderung an einer Containment-Grenze Pluspunkt und Begründungsbasis für R10.

### 3.7 Spec-Template-Checks

| Check | Ergebnis |
|---|---|
| Pflichtsektionen (`Interface Contracts`, `Acceptance Criteria`, Datenfluss, Problem/Ziel/Nicht-Ziele, Offene Fragen + Risiken) | **grün** — alle vorhanden und gegliedert |
| Trace-Anker `spec-id: SPEC-1189-tmp-sink-pin-vs-system-temp` | **grün** — gesetzt, im Dokumentkopf und im Trace-Block konsistent |
| Approval-Marker | **grün** — `Status: DRAFT (2026-11-08)`, konsistent zum Review-Stand (nicht approved) |
| No-Placeholder | **grün** — keine `TODO`/`TBD`/`{{…}}`; `<sink>`/`<root>`/`<system-temp>` sind Metavariablen, `Plan: <wird nach Approval erzeugt>` ist die vorgesehene Vorwärtsreferenz |

Die Mängel liegen damit nicht in der Form, sondern in zwei falschen Prämissen und einigen
Lücken — genau der Fall, für den ein Struktur-Review vor der Formalisierung gedacht ist.

---

## 4. Änderungsauflagen (verbindlich für Revision 2)

1. **RVW-1** — IC-1/R1 auf die reale Aufrufumgebung umstellen (ThreadingHTTPServer,
   Request-Threads) und eine Nebenläufigkeitsmaßnahme festschreiben; Restrisiko als R10.
2. **RVW-2** — AC-1189-10 gegen IC-5/IC-10 auflösen: entweder AC einschränken oder
   `_tmp_sink_env`-Verhalten ändern; D4s Absolutaussage entsprechend präzisieren.
3. **RVW-3** — IC-1 um die transiente Schreibprobe von `gettempdir()` und den OSError-Pfad
   korrigieren; AC-1189-10/11 anpassen.
4. **RVW-4** — Baseline der Ergebnis-Invariante definieren („ohne die drei Sink-Keys") und
   AC-1189-04/U2-8 entsprechend umformulieren.
5. **RVW-5** — `tests/conftest.py::effective_basetemp` als betroffene, unveränderte
   Komponente aufnehmen; Ziel 3/AC-1189-23 auf „gerendert" schärfen.
6. **RVW-6/RVW-7** — Threat-Model-Abschnitt (4 Fragen) + Token-Exposure-Maßnahme oder
   bewusste Akzeptanz; IC-7 um „kein Proxy, keine Redirects" erweitern; R11/R12 ergänzen.
7. **RVW-8** — PID-Datei-Lebenszyklus entscheiden (sofort schreiben + bei Fehlschlag
   löschen vs. Fenster als Risiko dokumentieren); AC-1189-14 anpassen.
8. **RVW-9** — AC-1189-05 auf den expliziten Block beschränken; Matrix-Zeile 5 korrigieren.
9. **AC-1189-24** — in 24a/24b/24c teilen (Eltern-CLI, Kind-Boot, `--validate`); siehe §3.3.
10. **RVW-16** — OQ-1…OQ-3 entfernen bzw. als „bestätigt" führen; OQ-4 als
    Dokumentationspflicht (inkl. §5.5 **und** Vorgänger-Spec Option C) verbindlich machen.

**Empfehlungen (nicht blockierend):** RVW-10 (Zitat), RVW-11 (`pid`/`root` im
Health-Payload), RVW-12 (Stale-Pin-Risiko + Reparaturhinweis), RVW-13 (Docstring +
#1136-Präzedenz als Begründungsbeleg in D1), RVW-14 (Testkonvention + Vertrag für
„Fallback == Sink"), RVW-15 (zwei Commit-Einheiten).

---

## 5. Positiv befundene Punkte (Stichproben, VERIFIED)

- **D2 ist gegen den Code geprüft und hält.** Option A ist in der Vorgänger-Spec mit
  Ancestor-Kollision abgelehnt, Option C freigegeben; §5.5 Punkt 1 ist unmissverständlich.
  Die Spec weicht damit begründet von der Auftragsskizze ab und legt die Begründung
  nachvollziehbar offen.
- **Belegdisziplin.** `VERIFIED`/`CONFIRMED`/`ASSUMED` ist konsequent verwendet; die
  Zombie-Eigenschaft ist ehrlich als ASSUMED markiert (`os.kill(pid,0)` auf einem nicht
  `wait()`-ten Kind kehrt tatsächlich erfolgreich zurück — die Annahme ist korrekt).
- **Fehleranalyse ist vollständig.** Beide Fehlerpfade (gepinntes Kind / gepinnte
  aufrufende Shell) sind erkannt; der `SystemExit`/`except Exception`-Mechanismus ist
  zutreffend erklärt.
- **Nicht-Ziele sind diszipliniert.** Variante B ist mit Containment-Begründung verworfen;
  `os.kill` bleibt in `_stop` (dort richtige Operation). Kein Symptom-Fix.
- **AC-1189-21** hält die bestehenden Negativfälle (`test_system_temp_exception_rejects…`,
  `test_pytest_basetemp_rejects…`, `test_tmp_sink_env_coverage.py`) fest — genau richtig,
  weil D1 leicht zu breite „Freibriefe" einführen könnte; D3 (exakt statt „innerhalb")
  verhindert das.
- **Präzedenzfall erkannt, aber nicht zitiert:** `tmp_sink_location_error` behandelt
  `TMPDIR=<root>/.tmp` seit #1136 als unproblematisch (Test
  `test_location_default_ok_when_tempdir_is_sink`). Damit ist D1 keine neue Semantik,
  sondern die konsequente Anwendung einer bereits freigegebenen — ein starkes Argument,
  das in D1 gehört.

---

## 6. Nächster Schritt

1. Autor: Revision 2 mit den Auflagen 1–10; `Status` bleibt **DRAFT**.
2. Re-Review beschränkt auf die geänderten Abschnitte (IC-1, IC-7, IC-8, AC-04/05/10/23/24,
   OQ-Tabelle, Matrix, R-Tabelle) — keine neuen Prüfdimensionen.
3. Erst danach `Status: APPROVED (Datum)` durch den User; danach schreitet die Pipeline
   `quality_pipelines.concept-driven-dev` (specify → review → approve → plan) fort, und der
   Plan referenziert `spec-id: SPEC-1189-tmp-sink-pin-vs-system-temp`.

---

*Review-Bericht, keine Umsetzung. Die geprüfte Spec wurde nicht verändert; es wurde kein
Commit erstellt (Auftragsvorgabe).*
