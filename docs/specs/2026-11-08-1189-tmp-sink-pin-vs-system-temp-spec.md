# Tmp-Sink-Pin vs. System-Temp-Root (Issue #1189) — Spec

> Status: **APPROVED (2026-11-09)** — durch den User freigegeben. Der Approval-Marker
> `Status: APPROVED (Datum)` wird ausschließlich vom User gesetzt, nie vom Spec-Autor.
> Revision: 4
> Datum: 2026-11-08
> Klasse: **M** (Framework-Bugfix, 4 Produktionsdateien + Tests, keine öffentliche
> API-/Config-Schema-Änderung) — Begründung in [Klassifizierung](#klassifizierung)
> spec-id: SPEC-1189-tmp-sink-pin-vs-system-temp
> Issue: #1189 · Regression aus `f9e3f3e5` (PR #1023) · verwandt, nicht identisch: #1136/#1140 (geschlossen)
> Vorgänger-Spec (gültig, wird **nicht** ersetzt): `docs/specs/2026-10-24-tmp-sink-injection-spec.md`
> (SPEC-tmp-sink-injection, AC-11/AC-15/IC-04/IC-06/IC-18/ADR-12)
> Regel (gültig, wird **nicht** geändert): `docs/concepts/repo-containment-prison-mode.md` §5.5
> Review: `docs/specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-review.md` (CHANGES_REQUESTED, 16 Findings)
> Re-Review Rev 2: `docs/specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-rereview.md`
> (CHANGES_REQUESTED, 2 blocking + 3 major + 5 minor + 1 info)
> Re-Review Rev 3: `docs/specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-rereview2.md`
> (APPROVE WITH CHANGES, 1 blocking RVW3-1 + 4 minor + 1 info)
> Verifikations-Legende: **VERIFIED** = in dieser Session am Code gelesen (`datei:symbol`);
> **CONFIRMED** = Verhalten zusätzlich durch vorhandenen Test/Code-Pfad belegt;
> **ASSUMED** = plausibel, in dieser Session nicht ausgeführt (klar benannt).
> Diese Spec enthält **keinen Implementierungscode** — nur Verträge, Datenfluss, Kriterien.

> **Revision 2 (2026-11-08) — Review-Auflagen 1–10 eingearbeitet.** Wesentliche Änderungen:
> **(RVW-1)** Fallback ohne prozessglobale Mutation (read-only Kandidatenwahl), damit
> thread-tauglich im `_DaemonThreadingHTTPServer`; R1/R10 neu gefasst.
> **(RVW-2)** Pin-Helfer dürfen Fehler nicht mehr still schlucken: `None` nur noch für
> definierte Zustände, sonst `TmpSinkError` (neue Entscheidung D7, IC-5).
> **(RVW-3)** transiente Schreibprobe von `tempfile.gettempdir()` dokumentiert, `OSError`-Pfad.
> **(RVW-4)** Baseline der Ergebnis-Invariante definiert („ohne die drei Sink-Keys").
> **(RVW-5)** `tests/conftest.py::effective_basetemp` als betroffener Verbraucher aufgenommen,
> Ziel 3/AC-1189-23 auf „gerendert" geschärft. **(RVW-6/7)** kein Token-Versand mehr in der
> Health-Probe (D6), Threat-Model-Abschnitt, kein Proxy/keine Redirects. **(RVW-8)** PID-Datei
> wird sofort geschrieben, nur die Erfolgsmeldung hängt an der Verifikation. **(RVW-9)**
> AC-1189-05 auf den expliziten Block beschränkt, Matrix-Zeile korrigiert. **(RVW-10/11/12/13/14)**
> Zitat, `pid` im Health-Payload, Stale-Pin-Risiko, Docstring/Präzedenzfall, Testkonvention.
> **(RVW-15)** Umsetzungsschnitt für den Plan. **(RVW-16)** OQ-1…OQ-3 zu „bestätigt" aufgelöst,
> OQ-4 als verbindliche Dokumentationspflicht D8. **Status bleibt DRAFT.**

> **Revision 3 (2026-11-08) — Re-Review-Auflagen RVW2-1…RVW2-11 eingearbeitet.**
> **(RVW2-1)** IC-5 ist jetzt ein **Pro-Kopie-Vertrag**: die vierte Kopie
> (`run_role_routing_eval.py::_tmp_sink_env`) gibt `dict` zurück (nie `None`), und ihr
> `TmpSinkError` beendet die Eval **vor** der Case-Schleife (plus Re-Raise als
> Defense-in-depth); der `ImportError`-Zweig ist dort als „nicht anwendbar" markiert.
> **(RVW2-2)** HTTP 401 gilt erst nach einem **Bestätigungsfenster**
> (`START_CONFIRM_GRACE`) als Erfolg; `proc.poll()` wird am Fensterende erneut geprüft.
> **(RVW2-3)** `token_configured` wird an `_load_admin_ui_config` + `_resolve_admin_token`
> gebunden (identische Quellen/Priorität wie `AdminServer.__init__`).
> **(RVW2-4)** AC-1189-11/30 und U1-5 auf `os.environ` + Stdlib-**Set-once-Cache**
> umformuliert (prüfbar statt unerfüllbar). **(RVW2-5)** Aufrufer → catch-Stelle →
> Exit-Code → Meldungsformat je Pfad in IC-5 festgelegt; `TmpSinkError`-Code-Set erweitert.
> **(RVW2-6)** Testanker U4-26a…e für alle Kopien. **(RVW2-7)** eigene Konstante
> `VIZ_START_GRACE`. **(RVW2-8)** IC-2 prüft das Resolver-Finding (kein stiller
> Fallback-Default). **(RVW2-9)** D2-Begründung auf „Drift der deployten Artefakte"
> präzisiert. **(RVW2-10)** `root` entfällt aus `/api/health` (nur `pid`).
> **(RVW2-11)** `rc` ist ein Alias auf `repo_containment` (kein `lib/rc.py`); Signaturen
> mit gequoteten Annotationen wie im Bestand. **RVW-1 bleibt unangetastet; Status bleibt
> DRAFT; keine Architekturänderung.**

> **Revision 4 (2026-11-08) — Re-Review-Auflage RVW3-1 entschieden, RVW3-2…RVW3-6
> eingearbeitet.**
> **(RVW3-1, blocking) Option B gewählt — Pre-Flight-Bind-Probe vor dem Spawn, das
> Bestätigungsfenster wird als Heuristik ausgewiesen.** Neuer deterministischer Schritt:
> `_probe_port_bindable` (IC-12) bindet `--host`/`--port` vor dem Spawn und bricht bei
> belegtem Port mit Exit 1 ab, ohne Kind. Das Fenster (`START_CONFIRM_GRACE` + `poll() is
> None`) bleibt, ist aber ausdrücklich **keine Erfolgsgarantie**, sondern eine Heuristik
> für den Kind-Lebenslauf; die absolute Formulierung „kann den Start nicht mehr fälschlich
> als Erfolg markieren" ist gestrichen. Das Restfenster (TOCTOU zwischen Probe und
> Kind-Bind) steht benannt in R11/R16/Threat-Model (g). **AC-1189-17 wird in einen
> deterministischen und einen heuristischen Fall getrennt** (AC-1189-17/17a/17b). Option A
> (`/api/health` token-frei) ist mit Begründung **verworfen** (D6). **(RVW3-2)** Wortlaut der
> Warnzeile im `ImportError`-Fall festgeschrieben, „Text unverändert" gestrichen.
> **(RVW3-3)** D8 um Punkt 4 (drei Helfer-Docstrings) erweitert, AC-1189-32 entsprechend.
> **(RVW3-4)** „identisch" bei Kopie 4 auf „inhaltlich gleich, nicht zwingend dasselbe
> Objekt" präzisiert. **(RVW3-5)** Zielstream der Lifecycle-Zeilen in IC-5b auf **stdout**
> korrigiert (Bestandsmuster `:6049-6051` nutzt `print` ohne `file=`), AC-1189-14
> präzisiert. **(RVW3-6)** Belegstelle `eval_gate.py:278` ergänzt, Satz „Pin-Auflösung pro
> Model-Klasse", Formfehler `U4-26a…d` → `U4-26a…e` korrigiert. **Status bleibt DRAFT; keine
> Implementierung; kein Commit.**

---

## Klassifizierung

**M** — bestätigt, mit Begründung:

- **M, nicht S:** vier Produktionsdateien (`repo_containment.py`, `tmp_paths.py`, `config.py`,
  `admin-server.py`) plus mindestens vier Testdateien; ein reiner Localfix genügt nicht, weil
  Resolver, Validator und Admin-Lifecycle **denselben** Fehlbegriff („System-Temp-Root") tragen.
- **M, nicht L:** keine öffentliche Schnittstelle ändert ihr Verhalten für gültige Configs,
  kein Config-Schema-/YAML-Feld, kein Renderer-/Template-Vertrag, keine Provider-Änderung.
  Bestehende Projekte validieren unverändert.
- **M, nicht XL:** keine Komponenten-/Trade-off-Entscheidung auf Systemebene; die
  Designfrage („Pin vs. Exception") ist eine Semantikklärung in einem Subsystem
  (`repo_containment.tmp-sink`), nicht ein Subsystem-übergreifender Umbau.

Die Spec existiert trotzdem, weil die Änderung eine **dokumentierte Invariante** (§5.5) und
eine **freigegebene Vorgänger-Spec** berührt und deshalb eine explizite, reviewbare
Entscheidung braucht.

---

## Problem

### Ist-Zustand (VERIFIED; Annahmen sind inline als ASSUMED markiert)

Der Admin-Server pinnt für **jeden** von ihm gestarteten Kindprozess `TMPDIR`/`TEMP`/`TMP`
auf `<root>/<tmp-sink>`:

| Aufrufer | Symbol | Pin-Quelle |
|---|---|---|
| Admin-Server-Kind (`start`/`restart`) | `admin-server.py::_admin_start_detached` (Popen `env=_tmp_sink_env(root)`) | `_tmp_sink_env` → `lib.tmp_paths.tmp_env` |
| Viz-Dashboard + MCP-SSE | `admin-server.py::VizManager._start` (beide Plattform-Zweige) | dito |
| `POST /api/sync/dry-run`, `POST /api/sync/run`, `--validate` | `admin-server.py::SyncExecutor._run` | dito |
| `GET /api/consistency-check` | `admin-server.py::ConsistencyService.run_consistency_check` | dito |
| `consistency-check.py` (git-Kinder) | `scripts/consistency-check.py::_tmp_sink_env` | dito (eigene Kopie) |
| Rollen-Routing-Eval | `scripts/run_role_routing_eval.py::_tmp_sink_env` | dito (eigene Kopie) |
| Admin-CLI-Pfad | `scripts/lib/cli_commands.py::_admin_tmp_env` | dito (eigene Kopie) |

`_tmp_sink_env` (`admin-server.py`) ruft `resolve_tmp_paths(...)` und dann
`tmp_env(paths, base)`; `tmp_env` (`tmp_paths.py:298-313`) setzt alle drei Keys aus
`TMP_ENV_KEYS` (`tmp_paths.py:36`) auf `str(paths.absolute)`.

Jeder dieser Kinder ruft beim Boot `lib.config.load_config()`; dieses ruft
`_validate_config` → `_validate_repo_containment` (`config.py:795`, Aufruf `:669`). Die
Exception-Matrix (`config.py:888-937`) prüft dort — **nur wenn der Block existiert**
(`config.py:892`):

```text
uses_system_temp = exc_pytest_basetemp and (exc_enabled or not sink_enabled)
if uses_system_temp:
    temp_root = tempfile.gettempdir()          # ← ist der Pin
    if _path_is_inside(<root>, temp_root): _fail("… exception cannot take effect.")
```

Mit `system-temp-exception.enabled: true` + `pytest-basetemp: true` (Projekt-Config,
`.meta-config/project.yaml:402-406`) und gepinnter Env ist `gettempdir()` = `<root>/.tmp`
⇒ **`sys.exit(1)` beim Boot des Kindes**.

Dieselbe Fehlannahme steht im Resolver: `tmp_paths.py::resolve_pytest_basetemp`
(`:234-284`) nutzt `_system_temp_basetemp()` = `gettempdir()/<user>/pytest-agent-meta` und
verwirft den Wert, wenn `realpath(gettempdir())` im Projekt liegt (`:274-282`). Ein
gepinnter `sync.py`-Lauf (dry-run/run/validate) bricht damit ebenfalls ab — noch vor dem
Rendering, in `_build_orch_variables` (`config.py:2053-2065`).

**Zweiter Fehlerpfad (VERIFIED, gleiche Ursache):** Ist bereits die **aufrufende Shell**
gepinnt — im Agenten-Kontext der Normalfall, weil der gerenderte
`TMP_SINK_ENV_PIN_BLOCK` `TMPDIR=<sink>` exportiert —, stirbt schon der CLI-Prozess:
`_tmp_sink_env` ruft `load_config` im **eigenen** Prozess (`admin-server.py:330`,
`cli_commands.py:204`, `consistency-check.py:89`, `run_role_routing_eval.py:708`). Der
`try/except Exception` dieser Helfer fängt `SystemExit` **nicht** (es erbt von
`BaseException`) ⇒ `sys.exit(1)` schlägt durch und beendet `admin-server.py start` /
`consistency-check.py`, bevor überhaupt ein Kind gestartet wird.

**Dritter Fehlerpfad, im Kind (VERIFIED, RVW-10):** Der per `start` gestartete Server ist
selbst gepinnt und stirbt in `AdminServer.__init__`:
`_load_admin_ui_config` (`:524-566`, Aufruf `:5862`) und
`AdminRequestHandler.version = self._read_version()` (`:5912`, Funktion `:5920-5943`)
rufen beide `load_config` in `try/except Exception` — `SystemExit` entweicht. Der
Vollständigkeit halber: `viz_manager.start_all()` (`start()`, `:5945-5952`) betritt
denselben Pfad ein zweites Mal. Die Admin-UI-`GET`/`PUT`-Pfade sind nur insoweit nicht
betroffen, wie sie die Config über `ConfigManager`/`load_yaml_file` lesen.

**Vierter Fehlerpfad, in der Eval (VERIFIED, RVW2-1):** `run_role_routing_eval.py::_tmp_sink_env`
(`:697-713`) gibt in **allen** Fehlerfällen das geerbte Env zurück und deklariert `-> dict`
(nie `None`). Ein Fehler wird damit nicht nur verschluckt, sondern die Eval läuft weiter; ein
erst dort geworfener `TmpSinkError` würde von der Case-Schleife (`:783-802`) als „Miss"
verbucht — eine Baseline aus lauter Misses. Zusätzlich sind `load_config` (`:55`) und
`resolve_tmp_paths`/`tmp_env` (`:62`) Modul-Level-Importe, ein `ImportError`-Zweig ist dort
strukturell nicht implementierbar.

**Verbraucher außerhalb des Frameworks (RVW-5, VERIFIED):**
`tests/conftest.py::effective_basetemp` (`:45-59`) leitet den effektiven pytest-Basetemp
aus `--basetemp`, sonst `os.environ["TMPDIR"]`, sonst `tempfile.gettempdir()` ab und warnt
nur. In einer gepinnten Shell ist dieser Wert `<root>/.tmp` — pytest ohne `--basetemp` legt
den Basetemp also **im Repo** an (§5.5 Punkt 1). Das ist pytest-Verhalten, nicht
Framework-Verhalten, und **nicht** durch D1 heilbar; es muss als Grenze dokumentiert sein.

### Reproduktion (VERIFIED, Befehlsform)

```bash
TMPDIR=<root>/.tmp python3 scripts/sync.py --validate
# ERROR: …/.meta-config/project.yaml: tmp-sink.system-temp-exception: platform temp root
# '<root>/.tmp' is inside the project root — the exception cannot take effect.
```

Damit sind unbrauchbar: `admin-server.py start`/`restart` (Kind stirbt sofort),
`POST /api/sync/dry-run`, `POST /api/sync/run`, `GET /api/consistency-check`.
`start`/`restart` meldet **trotzdem Erfolg**, weil nach `time.sleep(1.5)` nur
`_is_pid_running(proc.pid)` geprüft wird (`admin-server.py:569-585`, `:6044-6051`) und
`os.kill(pid, 0)` auf einem **Zombie** des eigenen Kindes erfolgreich zurückkehrt
(**ASSUMED**: POSIX-Semantik, in dieser Session nicht ausgeführt; der Codepfad ist
VERIFIED, die Zombie-Eigenschaft ist Review-bestätigtes Standard-POSIX-Verhalten).

### Fachliche Kernfrage

Der Pin ist in sich widersprüchlich:

- `system-temp-exception` verlangt, dass der **System-Temp-Root** nicht im Repo liegt
  (sonst kann pytest den Basetemp nicht außerhalb ablegen).
- Der tmp-sink-Pin legt den **beobachteten Temp-Root** genau dorthin.

Beides ist nur auflösbar, wenn „System-Temp-Root" und „gepinnter Sink" **zwei verschiedene
Begriffe** sind. Die heutige Implementierung behandelt `tempfile.gettempdir()` als
Identität beider — das ist der Bug.

---

## Ziel

**Ein Satz:** Der framework-eigene Pin ist ein **Transport-Detail** (damit Kindprozesse
ihre Temp-Dateien im sanktionierten Sink ablegen) und **niemals** ein Beweis über den
System-Temp-Root; die Exception-Prüfung und der pytest-Basetemp betrachten deshalb den
**ungepinnten** System-Temp-Root. Zusätzlich darf `admin-server.py start`/`restart` keinen
Erfolg mehr melden, den es nicht belegen kann: ein bereits belegter Port bricht
**deterministisch** vor dem Spawn ab, ein toter/ungesunder Kindprozess wird über
Exitstatus + Health erkannt (Heuristik mit ausgewiesenem Restfenster, D6/IC-12).

Konkret:

1. **Semantik trennen (Variante A, präzisiert):** Ist der beobachtete Temp-Root
   (realpath, plattformnormalisiert) **exakt** der aufgelöste Sink, gilt er nicht als
   System-Temp-Root. Der System-Temp-Root wird dann aus einer **read-only**
   Kandidatenliste bestimmt, die die auf den Sink zeigenden Temp-Env-Keys auslässt.
   Die Exception-Prüfung wertet diesen Ersatzwert.
2. **Ergebnis-Invariante (Baseline definiert, RVW-4):** Der Pin darf das aufgelöste
   Ergebnis nicht verändern. Baseline ist **dieselbe Env ohne die drei framework-gesetzten
   Temp-Keys** (`TMPDIR`/`TEMP`/`TMP`): Gegen diese Baseline sind `pytest_basetemp` und die
   daraus gerenderten `PYTEST_BASETEMP`/`TEST_COMMANDS` identisch. Ein vom Aufrufer
   gesetzter **eigener** `TMPDIR` wird vom Pin bewusst verdeckt (heute schon so); der
   Fallback rekonstruiert ihn nicht.
3. **§5.5 bleibt — für den gerenderten Aufruf:** Der gerenderte Basetemp
   (`--basetemp={{PYTEST_BASETEMP}}`) liegt weiterhin **außerhalb** des Arbeitsbaums
   (`<system-temp>/<user>/pytest-agent-meta`). Grenze (RVW-5): Ein pytest-Lauf **ohne**
   `--basetemp` in einer gepinnten Agent-Shell nutzt weiterhin den Pin als Basetemp-Root;
   `tests/conftest.py` warnt dann nur. Diese Grenze ist dokumentiert, nicht Bestandteil des
   Fixes.
4. **Pin bleibt — und wird nicht still fallengelassen (RVW-2):** Kein Aufrufer wird vom Pin
   ausgenommen. Lässt sich der Pin nicht herstellen (Config-Fehler, nicht bestimmbarer
   Sink), startet der Aufrufer **kein** ungepinntes Kind, sondern bricht sichtbar ab
   (D7/IC-5). „Kein Pin" (Env erben) gilt nur noch für: Config-Datei fehlt, Sink deaktiviert,
   Framework-`lib` nicht importierbar — und auch dann nie still: die drei `dict | None`-Kopien
   geben `None`, die Eval-Kopie gibt das übergebene Env zurück (IC-5a).
5. **Start-Robustheit in zwei Stufen (RVW3-1):**
   **(a) deterministisch** — `start`/`restart` prüfen **vor** dem Spawn per
   Pre-Flight-Bind-Probe (IC-12), ob `--host`/`--port` bindbar sind; ist der Port belegt,
   endet der Befehl mit Exit 1 und klarer Meldung, **ohne** Kindprozess und ohne PID-Datei.
   **(b) heuristisch** — für den verbleibenden Lebenslauf wird über Prozess-Exitstatus +
   Health-Endpoint verifiziert statt über `os.kill(pid,0)`; Erfolg gilt erst nach einem
   **Bestätigungsfenster** (RVW2-2), das ausdrücklich **nur eine Heuristik** für „das Kind
   lebt noch" ist und **keine** Erfolgsgarantie. Die PID-Datei wird sofort nach dem Spawn
   geschrieben (Status/Stop bleiben im Verifikationsfenster funktionsfähig) und bei
   Fehlschlag entfernt; die Fehlermeldung enthält den Log-Tail (inkl. der echten Ursache).
6. **Kein Credential-Versand (RVW-6/7):** Die Health-Probe sendet **nie** den Admin-Token,
   geht nie über einen Proxy und folgt keinen Redirects.

---

## Nicht-Ziele

- **Keine Config-Migration**, kein neues YAML-/JSON-Feld, keine Schema-Änderung
  (`config/project-config.schema.json` bleibt unverändert).
- **Keine Abschwächung des Pins** (Variante B ist verworfen). Kein Aufrufer erbt den
  System-Temp, außer in den drei in D7 definierten Ausnahmezuständen (Config-Datei fehlt,
  Sink deaktiviert, Framework-`lib` nicht importierbar) — dort ist kein Pin herstellbar.
- **Kein In-Repo-Basetemp** und keine Umkehr von §5.5. Die von der Vorgänger-Spec
  verworfene „Option A — Basetemp unter dem Sink" bleibt verworfen; diese Spec
  **wiederholt sie nicht** in anderer Form (siehe [D2](#d2--basetemp-bleibt-auf-dem-ungepinnten-system-temp-root)).
- **Kein Eingriff in `tests/conftest.py`:** Der Warn-/Basetemp-Mechanismus bleibt
  unverändert (RVW-5); die Grenze wird nur dokumentiert.
- **Kein neuer Env-Marker** und kein neues öffentliches Env-Feld (Entscheidung D1).
- **Kein Token-Versand in der Health-Probe** (D6) und keine neue Authentifizierungsroute.
  **Keine Änderung der Auth-Oberfläche:** `/api/health` bleibt token-gated
  (Option A ist mit Begründung verworfen, D6/ADR-1189-08) — es wird **kein** Endpoint
  öffentlich gestellt und **kein** Feld über den bestehenden Rahmen (IC-10) hinaus ergänzt.
- **Keine Garantie über den Port-Bind:** Diese Spec sichert den Fall „Port dauerhaft belegt"
  deterministisch zu (Pre-Flight-Probe, IC-12) und weist den verbleibenden TOCTOU-Fall
  ausdrücklich als **Heuristik-Restrisiko** aus (R11/R16). Sie behauptet **nicht**, dass
  `start` beweisen kann, welcher Prozess den Port hält.
- **Keine Änderung an** `tmp_sink_env_pin_block` (ADR-12: absolute Werte), an
  `TMP_ENV_KEYS`, an `work_dir_env` oder am Schema der Exception-Matrix.
- **Kein Umbau** der Consistency-/Temp-Literal-Checks (`temp_literals.py`) und keine
  Änderung an `.meta-config/temp-env-allowlist.yaml`.
- **Kein Ersatz von `os.kill`** in `_admin_stop`/`_stop` (dort ist „Signal senden" die
  richtige Operation); nur die **Erfolgsprüfung** von `start` ändert sich.
- **Keine OS-Sandbox** und keine Ausweitung der Containment-Durchsetzung; alles bleibt
  Convention boundary.
- **Keine Implementierung in diesem Dokument.**

---

## Entscheidungen (verbindliche Zielsemantik)

### D1 — Zwei Begriffe, ein Vergleich: „beobachteter System-Temp-Root" ≠ „Sink"

**Entscheidung:** Der System-Temp-Root ist der Wert, den `tempfile.gettempdir()` liefert —
**außer** er ist (realpath-, plattformnormalisiert) identisch mit dem aufgelösten
Sink-Verzeichnis. In diesem Fall wurde er durch den framework-eigenen Pin gesetzt und
trägt **keine** Aussage über den System-Temp-Root.

**Begründung:**

- Der Pin wird ausschließlich vom Framework gesetzt (`tmp_env`); ein Temp-Root, der exakt
  der sanktionierte Scratch-Sink ist, ist per Definition **kein** System-Temp.
- Die Aussage der Exception („der System-Temp-Root liegt im Repo, also kann pytest nicht
  außerhalb schreiben") ist unter dem Pin **falsch**: der Pin ist transient und für
  Kindprozesse gedacht, nicht der Ort, den pytest als Basetemp wählen muss.
- **Präzedenzfall im eigenen Code (RVW-13):** `tmp_sink_location_error` behandelt
  `TMPDIR=<root>/.tmp` seit #1136 bereits als unproblematisch — „A sink inside the project
  root is always valid, even when the platform temp dir points into it"
  (`repo_containment.py:360-367`, Test
  `tests/test_tmp_sink_path_hardening.py::test_location_default_ok_when_tempdir_is_sink`
  `:218-222`). D1 ist damit keine neue Semantik, sondern ihre konsequente Anwendung.
- Der Vergleich ist **zustandslos**: keine neue Env-Variable, kein Marker, keine
  Reihenfolge-Abhängigkeit, keine Persistenz. Er funktioniert auch für manuell gesetzte
  Env (Reproduktion aus dem Issue) und nach einem Repo-Umzug.

**Verworfene Alternative: Marker-Env** (z. B. `AGENT_META_TMP_SINK_PIN=<abs>`, gesetzt von
`tmp_env`, geprüft von der Validierung). Präziser bei der Unterscheidung „Framework-Pin vs.
Nutzer-Env", aber: (a) ein weiterer Env-Key, der an alle Kinder leakt und in jeder
Doku/Allowlist auftaucht, (b) die dokumentierte Reproduktion
`TMPDIR=<root>/.tmp python3 scripts/sync.py --validate` bliebe rot, obwohl sie exakt den
Sanktionsfall beschreibt, (c) der Marker wäre eine zweite Wahrheit neben dem Pfad und
könnte bei `env=base`-Aufrufen verloren gehen. **Nicht gewählt.**

**Status (RVW-16): entschieden** (ADR-1189-03).

### D2 — Basetemp bleibt auf dem ungepinnten System-Temp-Root

**Entscheidung:** Zeigt der beobachtete Temp-Root auf den Sink, wird für `PYTEST_BASETEMP`
der System-Temp-Root aus einer **read-only** Kandidatenliste bestimmt, die (a) die auf den
Sink zeigenden `TMPDIR`/`TEMP`/`TMP`-Keys auslässt und (b) Kandidaten innerhalb des
Projekt-Roots verwirft. Ergebnis bleibt `<system-temp>/<user>/pytest-agent-meta`.

**Baseline (RVW-4, verbindlich):** „Ungepinnt" heißt **dieselbe Env ohne die drei
framework-gesetzten Temp-Keys** — nicht „die Env des Aufrufers mit ihrem echten `TMPDIR`".
Konsequenz: Ein vom Aufrufer gesetzter Custom-Temp-Root wird vom Pin verdeckt (bewusst,
heute schon so); der Fallback liefert den Plattform-Default, nicht den Custom-Wert.

**Grenze (RVW-5):** Punkt 3 gilt für den **gerenderten** Aufruf
(`--basetemp={{PYTEST_BASETEMP}}`). Ein pytest-Lauf **ohne** `--basetemp` in einer
gepinnten Shell nutzt weiterhin `<root>/.tmp`; `tests/conftest.py::effective_basetemp`
warnt warning-only. Das ist keine Regression dieser Spec, aber eine dokumentierte Grenze.

**Begründung / verworfene Alternative:** Die Auftrags-Skizze zu Variante A nannte
`<sink>/pytest` als Basetemp. Das ist **verworfen**:

1. Es widerspricht §5.5 („Der pytest-Basetemp darf NIE im Arbeitsbaum liegen") und der
   freigegebenen Vorgänger-Spec, die genau diese Option („Option A — Basetemp unter dem
   Sink") mit der Ancestor-Kollision (13 Fehlschläge 2026-09-20) begründet **abgelehnt**
   hat.
2. Es würde das **gerenderte Artefakt** verändern: `sync.py` unter Pin (Admin-Dry-run!)
   würde `TEST_COMMANDS`/`PYTEST_BASETEMP` mit einem In-Repo-Pfad rendern ⇒ **Drift der
   deployten Agenten-Dateien** (dort steht der aufgelöste absolute Pfad,
   `config.py:2066-2071`) und die Agenten-Anweisungen würden den Regelverstoß
   festschreiben. **Präzisierung (RVW2-9):** Die Slimming-**Goldens** tragen den
   unaufgelösten Token `{{PYTEST_BASETEMP}}` (`tests/fixtures/slimming-golden/*.md`) und
   brächen dadurch **nicht** — der Schaden ist der Drift, nicht ein Golden-Bruch.
3. Der Pin darf laut Ziel-Invariante (2) das Ergebnis nicht verändern — `<sink>/pytest`
   täte genau das.

**Fehlerpfad:** Ist kein Kandidat außerhalb des Projekt-Roots bestimmbar, wird **laut**
abgebrochen (`TmpSinkError("tmp-sink.system-temp-exception", …)`), nie still auf den Sink
gewechselt und nie ein Kandidat zurückgegeben, der erneut dem Sink entspricht.

**Status (RVW-16): entschieden** (ADR-1189-02).

### D3 — Vergleich exakt, nicht „innerhalb"

**Entscheidung:** Nur `normcase(realpath(gettempdir())) == normcase(realpath(sink))`
(Windows case-insensitiv) gilt als Pin. Ein **Unterverzeichnis** des Sinks oder ein anderer
In-Repo-Pfad bleibt ein echter Fehler.

**Begründung:** Der Pin setzt exakt den Sink. Ein Unterverzeichnis ist kein
Framework-Zustand; ihn zu adeln würde die Fehlermeldung für echte Fehlkonfigurationen
abschwächen. Zusätzlich bleibt die bestehende Testmatrix (Temp-Root = Fixture-Root, Sink =
`<root>/.tmp`) unverändert gültig — sie prüft genau diesen Fall.

**Bewusste Nebenwirkung (dokumentiert):** Ein Nutzer, der `TMPDIR` manuell auf den Sink
setzt und die Exception „prüfen" will, erhält keinen Fehler. Das ist gewollt: sein Zustand
ist der sanktionierte Sink, nicht ein System-Temp im Repo.

### D4 — Pin-Verhalten unverändert, aber mit definiertem Fehlerverhalten

**Entscheidung:** `_tmp_sink_env`, `tmp_env`, `_admin_tmp_env`, `consistency-check.py` und
`run_role_routing_eval.py` pinnen weiter **alle** Kinder. **Geändert** wird nur das
Fehlerverhalten: Ein fehlbarer Pin führt zum sichtbaren Abbruch des jeweiligen Starts
(D7), nicht zu `env=None`.

**Begründung:** Variante B (detached Server-Kind bzw. config-validierende Kinder vom Pin
ausnehmen) heilt nur das Symptom und **verletzt** die Containment-Absicht: genau diese
Kinder (Server, sync, consistency) erzeugen Temp-Dateien (Diagnose, Backup-Staging,
Subprozess-Zwischendateien), die dann wieder im System-Temp lägen — außerhalb des
Sanktionsbereichs. Sie würde außerdem neue, inhaltlich falsche Allowlist-Einträge in
`.meta-config/temp-env-allowlist.yaml` erzwingen (`AC-11`/`IC-18` der Vorgänger-Spec).

### D5 — Start-Verifikation: Exitstatus + Health, nicht `kill(pid,0)`

**Entscheidung:** Für **eigene** Kinder ist `Popen.poll()` die autoritative Lebendprüfung;
Erfolg gilt erst, wenn der Prozess lebt **und** `GET /api/health` ein erwartetes Ergebnis
liefert (Deadline-basiert, siehe D6/IC-7). `_is_pid_running` bleibt für fremde PIDs
(PID-Datei), erhält aber einen POSIX-Zombie-Guard (`/proc/<pid>/stat`, Zustand `Z`), wo
verfügbar.

**Reichweite (RVW3-1, verbindlich):** Diese Verifikation ist eine **Heuristik über den
Kind-Lebenslauf**, keine Erfolgsgarantie — sie kann nicht beweisen, dass das Kind den Port
tatsächlich gebunden hat (dazu unten D6/IC-12). Die *deterministische* Aussage liefert
ausschließlich die Pre-Flight-Bind-Probe **vor** dem Spawn (IC-12).

**Begründung:** `os.kill(pid, 0)` beweist nur „es gibt einen Prozesseintrag", nicht
„der Server läuft" — Zombie und Port-Kollision sind Beispiele. Der Health-Endpoint
existiert bereits (`admin-server.py::_route_get_health`, Route `/api/health`) und liefert
`{status, version, mode}`; er wird additiv um `pid` erweitert (IC-10), damit die Antwort
eine echte Identitätsaussage trägt (`mode` allein ist trivial fälschbar, RVW-11).
**Verworfene Alternative:** nur Log-Parsing (fragil, lokalisierungs- und formatabhängig).

### D6 — Start-Verifikation: Pre-Flight-Bind-Probe (deterministisch) + Health-Fenster (Heuristik), ohne Token-Versand (RVW-6/7/RVW3-1)

**Entscheidung:** `start` prüft den Port **vor** dem Spawn deterministisch (IC-12) und
verifiziert den Kind-Lebenslauf **danach** per HTTP, aber:

0. **Pre-Flight-Bind-Probe (neu, RVW3-1, Option B):** Der Elternprozess bindet
   `(--host, --port)` mit denselben Socket-Optionen wie das Kind
   (`HTTPServer.allow_reuse_address`-Semantik, `SO_REUSEADDR`, **kein**
   `SO_REUSEPORT`) und schließt den Socket sofort wieder, **ohne** `listen()`/`accept()`.
   Ergebnis:
   - Bind erfolgreich ⇒ weiter mit dem Spawn.
   - `OSError` (belegt / privilegiert / nicht bindbare Adresse) ⇒ **harter Abbruch mit
     Exit 1**, Meldung mit `host:port` und der Original-`errno`-Ursache, **kein** Spawn,
     **keine** PID-Datei. Details: IC-12.
   Damit ist „Port schon belegt" ein **deterministischer** Fehlschlag statt einer
   Zeitannahme.
1. **Es wird niemals ein `Authorization`-Header gesendet.** Die Probe ist unauthentifiziert.
   Erfolgskriterium hängt von der **tatsächlich aufgelösten** Serverkonfiguration ab
   (`token_configured`, Quelle in IC-7/IC-8, RVW2-3):
   - **kein Token konfiguriert:** HTTP 200 mit `status == "ok"` und
     `pid == proc.pid` (falls das Feld vorhanden ist; sonst `mode == detect_mode(root)`).
   - **Token konfiguriert:** HTTP **401** (der eigene Server verweigert erwartungsgemäß).
2. **Das Bestätigungsfenster ist eine Heuristik, keine Garantie (RVW2-2/RVW3-1).** Ein
   Fremdprozess, der auf `/api/health` sofort 401 antwortet, erfüllt das Kriterium sonst bei
   t≈0, **bevor** unser Kind am Bind scheitert. Deshalb: Erfolg erst, wenn das Kriterium ein
   **Bestätigungsfenster** (`START_CONFIRM_GRACE`, Default 1,0 s) **stabil** erfüllt **und**
   `proc.poll()` am Fensterende erneut `None` liefert. Reihenfolge am Fensterende: letzte
   HTTP-Antwort → `poll()` → Erfolg. Details: IC-7.
   **Ausdrücklich nicht behauptet:** Das Fenster beweist **nicht**, dass das Kind den Port
   gebunden hat oder binden konnte. Es ist genau dann kein falscher Erfolg möglich, wenn das
   Kind innerhalb des Fensters bindet bzw. am Bind scheitert. Endet das Fenster **vor** dem
   Bind-Versuch des Kindes (Pre-Bind-Phase = Interpreter-Start + Modul-Importe +
   `AdminServer.__init__` mit zwei `load_config`-Läufen bis `admin-server.py:5918`), bleibt
   ein Restfenster. Dieses Restfenster ist **kein Implementierungsfehler, sondern die
   Grenze des Verfahrens** und in R11/R16 ausgewiesen.
3. Gebunden an `0.0.0.0`/`::` wird `127.0.0.1`/`::1` geprobt; nur `http://`. Die
   Pre-Flight-Probe bindet dagegen **exakt** `--host`/`--port` (Wildcard bleibt Wildcard),
   weil sie die Bindbarkeit des Kindes nachbilden muss.
4. **Kein Proxy, keine Redirects:** `build_opener(ProxyHandler({}))` und deaktivierter
   `HTTPRedirectHandler`. `http_proxy`/`HTTP_PROXY`/`no_proxy` dürfen das Ziel nicht ändern.
5. `VizManager._start` nutzt **kein** HTTP, nur Prozess-Liveness (die Sub-Server haben
   keinen gemeinsamen Health-Vertrag); dort gilt `VIZ_START_GRACE` (IC-9).
6. **Port 0** (`--port 0`, OS-vergeben) ⇒ die Probe ist **nicht anwendbar** und wird
   übersprungen; das ist dokumentiert und kein Fehlerfall (der resultierende Port ist dem
   Elternprozess unbekannt, deshalb ist die Identitätsprüfung in diesem Modus ohnehin
   eingeschränkt — Hinweis für den Plan, kein neues Verhalten).

**Begründung:** Der Token autorisiert Konfigurationsschreiben (`PUT`) und Sync-Läufe. Ein
lokaler Angreifer, der den Port vor dem Start belegt, dürfte ihn nicht erhalten. Zwei
Verfahren standen zur Wahl:

- **Option A — `/api/health` token-frei stellen** (Aufnahme in `_is_public_get_path`
  `:3514-3524`) und **immer** `pid == proc.pid` prüfen. Strukturell am stärksten, weil die
  Identitätsaussage dann ohne 401-Umweg auskäme. **Verworfen:** Bei Bindung auf
  `0.0.0.0`/`::` erlaubte eine token-freie Antwort unauthentifizierte Enumeration von
  Version, Modus und PID an **jeden** Netzteilnehmer; das widerspricht der Absicht des
  Token-Gates (`AdminRequestHandler` prüft `/api/health` bewusst mit, `:3514-3524`,
  `:3541-3551`). Die Alternative dazu — den Token zu senden — ist genau der Fehler, den D6
  ausschließt (Credential an einen fremden Listener). Wer Option A will, muss die
  Auth-Oberfläche neu bewerten; das ist eine eigene Entscheidung und nicht Teil dieses
  Fixes.
- **Option B — Pre-Flight-Bind-Probe + Fenster als Heuristik (gewählt).** Der reale,
  deterministisch entscheidbare Fall („Port ist schon belegt") wird **vor** dem Spawn
  erkannt; der nicht deterministisch entscheidbare Rest wird ehrlich als Heuristik
  ausgewiesen, statt eine Garantie zu behaupten. Kosten: ein zusätzlicher
  Bind-/Schließ-Zyklus (< 1 ms) und ein benanntes TOCTOU-Restrisiko.

**Was die Heuristik trotzdem leistet:** Sie erkennt jeden Fehlstart, der **innerhalb** von
`START_CONFIRM_GRACE` sichtbar wird (sofortiger Crash, Importfehler, Config-Abbruch,
Bind-Fehler eines früh bindenden Kindes, `stop` während der Verifikation), und sie
verhindert den Erfolg bei einem Portinhaber, der nur kurzzeitig 401 liefert. Sie ist damit
eine Verbesserung gegenüber `os.kill(pid,0)`, aber **kein Beweis**.

**Status (RVW-16): entschieden** (ADR-1189-04/05/08).

### D7 — Pin-Helfer: „kein Pin" nur für definierte Zustände, sonst sichtbarer Abbruch (RVW-2)

**Entscheidung:** Die vier Pin-Helfer (`admin-server.py::_tmp_sink_env`,
`consistency-check.py::_tmp_sink_env`, `cli_commands.py::_admin_tmp_env`,
`run_role_routing_eval.py::_tmp_sink_env`) liefern **keinen Pin** nur in drei definierten
Zuständen:

1. `.meta-config/project.yaml` **nicht existiert** (es gibt keinen Pin zu setzen), oder
2. der Sink **deaktiviert** ist (`tmp-sink.disabled` ist ein gültiger Zustand), oder
3. das Framework-`lib` **nicht importierbar** ist (`ImportError`; dann gibt es keine
   Pin-Fähigkeit) — mit genau **einer** Warnzeile auf **stderr**, Wortlaut verbindlich
   (RVW3-2; im Bestand existiert **keine** solche Zeile, die drei `dict | None`-Kopien geben
   im `except Exception` heute **still** `None` zurück — `admin-server.py:334-335`,
   `consistency-check.py:93-94`, `cli_commands.py:208-209`):

   ```text
     !  tmp-sink pin unavailable: framework lib not importable; inheriting environment
   ```

   Der Text ist **neu zu schreiben**, nicht „unverändert" — die frühere Formulierung
   („Text unverändert") war falsch und ist gestrichen.

Der Rückgabewert dieses „kein Pin"-Falls ist **pro Kopie verschieden** (RVW2-1): die drei
`dict | None`-Kopien geben `None` („Env erben"), die Eval-Kopie gibt das **übergebene
`base`-Env inhaltlich gleich** zurück (`-> dict`, nie `None`; gleicher Key-Set und gleiche
Werte — **nicht** zwingend dasselbe Objekt, der Bestand kopiert, RVW3-4). Verbindlich ist
die Pro-Kopie-Tabelle in IC-5.

Jeder andere Fehler (`TmpSinkError`, Config-Fehler aus `load_config`, inklusive
`SystemExit`) wird in `TmpSinkError("tmp-sink.pin-unavailable", <Originalmeldung + Hinweis
"python scripts/sync.py --validate">)` übersetzt. Die Aufrufer fangen ihn **nicht** still;
catch-Stelle, Exit-Code und Meldungsformat sind je Aufrufer in
**IC-5** (Pro-Kopie- und Aufrufer-Tabelle) verankert (RVW2-5):

| Aufrufer | Verhalten bei `tmp-sink.pin-unavailable` |
|---|---|
| `_admin_start_detached` | kein Spawn; **stdout**-Meldung `  !  …` + Repair-Hinweis; **Exit 1** (IC-5b, RVW3-5) |
| `SyncExecutor._run` | kein Kind; `{"success": False, "output": "tmp-sink pin unavailable: …", "returncode": -1}`, Status recorded |
| `ConsistencyService.run_consistency_check` | kein Kind; `{"error": "tmp-sink pin unavailable: …", "findings": [], "summary": {…}}` (HTTP-Status unverändert) |
| `VizManager._start` | kein Spawn; `False`, Meldung, keine PID-Datei |
| `cli_commands` (`sync.py`-Pfad) | stderr `error: tmp-sink.pin-unavailable: …`; **Exit 2** (kein ungepinntes Kind) |
| `consistency-check.py` | stderr-Meldung (bzw. `--json`: JSON-Objekt); **Exit 2** |
| `run_role_routing_eval.py` | Abbruch **vor** der Case-Schleife; Meldung; **Exit 2** (keine ungepinnte Eval, keine Baseline aus lauter Misses) |

**Begründung:** `TmpSinkError` ist eine `Exception` und wurde bisher geschluckt; fünf von
sieben Pin-Pfaden starteten dann still mit `env=None`. Das ist exakt der Zustand, den D4
ausschließt, und er trat ohne Meldung auf. Die vierte Kopie war **doppelt** gebrochen
(RVW2-1): sie gibt `dict` statt `dict | None` zurück, und ein dort geworfener Fehler wurde
von der Case-Schleife der Eval als „Miss" verbucht — die Eval wäre mit einer Baseline aus
lauter Misses durchgelaufen. Beides ist in IC-5 abgestellt. Der Fehler ist außerdem **nicht**
„Sink aus": Wenn die Config kaputt ist, ist der Server ohnehin nicht bootfähig (Dritter
Fehlerpfad) — „am Leben halten" ist eine Illusion.

**Abgrenzung:** Ein `ImportError` (Submodul-Layout ohne `lib`) bleibt erlaubt, weil der
Server in diesem Layout bewusst ohne `lib` starten kann (`_load_admin_ui_config`,
`_read_version` fallen auf Defaults zurück); er wird aber nicht still, sondern mit einer
Warnzeile behandelt.

**Bewusst außerhalb von D7 (RVW3-6, im Plan nennen):** zwei **direkte** `tmp_env`-Verbraucher
außerhalb der vier Helfer — `scripts/lib/context_report.py:347` und
`scripts/lib/meta_optimizer.py:1532`. Sie schlucken keine Fehler und geben kein `None` zurück;
sie werden **nicht** in D7 gezogen.

**Status (RVW-16): entschieden** (ADR-1189-06).

### D8 — Dokumentationspflicht: „System-Temp-Root" wird präzisiert (RVW-16/OQ-4)

**Verbindlich (Teil des Plans, kein Code):**

1. `docs/concepts/repo-containment-prison-mode.md` §5.5 erhält einen Satz: Der
   framework-eigene Pin (`TMPDIR=<sink>`) ist **kein** System-Temp-Root; die
   Exception-Prüfung und `PYTEST_BASETEMP` betrachten den ungepinnten Root. Ein pytest-Lauf
   **ohne** `--basetemp` erbt den Pin und wird von `tests/conftest.py` nur gewarnt.
2. `docs/specs/2026-10-24-tmp-sink-injection-spec.md` (Option C, „System-Temp …
   `tempfile.gettempdir()`") erhält einen Verweis auf diese Spec: die dortige Definition
   gilt **abzüglich** des framework-eigenen Pins.
3. `repo_containment.py::tmp_sink_location_error` Docstring: die Aussage „Only place that
   consults `tempfile.gettempdir` in the sink context" (`:363`) wird korrigiert
   (`system_temp_root` ist der zweite Konsument); kein Verhaltenswechsel.
4. **Drei Helfer-Docstrings widersprechen D7 (RVW3-3, verbindlich).** Sie versprechen
   heute ausdrücklich das Gegenteil des neuen Verhaltens und werden im selben Commit
   korrigiert:

   | Datei:Zeile | Heute (falsch) | Zielaussage |
   |---|---|---|
   | `admin-server.py:315-320` | „``None`` … an admin start/stop must never fail … at runtime the server keeps operating with the inherited env instead of blocking its UI" | `None` **nur** für die drei definierten Zustände (D7/IC-5a); jeder andere Fehler ⇒ `TmpSinkError("tmp-sink.pin-unavailable")`, Start bricht sichtbar ab |
   | `consistency-check.py:77-81` | „this helper never raises" | wirft `TmpSinkError` bei fehlbarem Pin; `None` nur für die drei Zustände |
   | `cli_commands.py:193-196` | „a CLI start never fails because of it" | CLI-Start **kann** an einem fehlbaren Pin scheitern (Exit 2, IC-5b) |

   Die vierte Kopie (`run_role_routing_eval.py:698-704`, „must not fail merely because the
   sink is off") wird sprachlich angeglichen, ohne die Aussage zu ändern: „off" bleibt
   erlaubt, „unlesbar/defekt" nicht.

---

## Interface Contracts

Alle Pfade relativ zum Repo-Root; `root` = `<root>`, `sink` = realpath des aufgelösten
`repo_containment.tmp-sink.path`.

### IC-1 — `scripts/lib/repo_containment.py::system_temp_root` (RVW-1/3/4/14)

```python
def system_temp_root(
    project_root: "str | os.PathLike[str]",
    sink_dir: Optional[Path],
) -> str: ...
```

- **Annotationsstil (RVW2-11):** gequotet wie im Bestand (`repo_containment.py:305`), damit
  die Datei ihre Kompatibilitätsaussage behält; `Optional[...]` wie dort.
- **Fehlerklasse:** `TmpSinkError` (definiert in `repo_containment.py:563-574`) — **nicht**
  in einem `lib/rc.py` (existiert nicht; `rc` ist nur der Import-Alias in
  `tmp_paths.py:33`: `from . import repo_containment as rc`). Das Code-Set des Docstrings wird
  laut IC-5 um `tmp-sink.pin-unavailable` und `tmp-sink.system-temp-exception` erweitert.
- **Zweck:** Einzige Stelle, die den „System-Temp-Root" bestimmt.
- **Eingabe:** `project_root` = Projekt-Wurzel (für den Inside-Filter);
  `sink_dir` = aufgelöster Sink (realpath) oder `None` (Sink deaktiviert / nicht auflösbar).
- **Schritt 1:** `observed = tempfile.gettempdir()`. Dokumentiert (RVW-3): Der **erste**
  `gettempdir()`-Aufruf im Prozess prüft Kandidaten per transienter Probe-Datei
  (`_get_default_tempdir`, Stdlib-Verhalten). Im Pin-Fall liegt diese Probe im Sink
  (innerhalb des Repos, sanktioniert) und wird sofort gelöscht. `OSError`
  (`FileNotFoundError`/`PermissionError`) ⇒
  `TmpSinkError("tmp-sink.system-temp-exception", …)`.
- **Schritt 2:** Ist `sink_dir is None` **oder** `normcase(realpath(observed)) !=
  normcase(realpath(sink_dir))` ⇒ `observed` **unverändert** zurückgeben.
- **Schritt 3 (Pin-Fall, read-only):** Kandidaten in Stdlib-Reihenfolge:
  - primär `tempfile._candidate_tempdir_list()`, falls vorhanden (private API, guarded per
    `getattr`), sonst dokumentierter Nachbau: `TMPDIR`, `TEMP`, `TMP` (in dieser
    Reihenfolge) → plattformspezifische Defaults (`/tmp`, `/var/tmp`, `/usr/tmp`; Windows:
    `%LOCALAPPDATA%\Temp`-Äquivalent) → `os.getcwd()`.
  - Filter: nicht leer, absolut, `os.path.isdir`, `realpath` **≠** Sink, `realpath`
    **nicht innerhalb** `project_root`.
  - Erster Treffer wird **verbatim** (ohne `realpath`) zurückgegeben.
  - Ist die Liste danach leer ⇒ `TmpSinkError("tmp-sink.system-temp-exception", …)`.
    Ein Kandidat, der erneut dem Sink entspricht, wird **übersprungen**, nie
    zurückgegeben (RVW-14, keine Rekursion/Endlosschleife).
- **Keine Mutation (RVW-1):** `os.environ` und `tempfile.tempdir` werden **nicht**
  verändert; es gibt keinen Remove-/Restore-Vertrag mehr. Damit ist die Funktion
  thread-tauglich (read-only) im `_DaemonThreadingHTTPServer`
  (`admin-server.py:5817-5824`, `daemon_threads = True`) und in Request-Threads
  (`SyncExecutor._run` `:1352-1370`, `ConsistencyService` `:1744-1750`,
  `VizManager._start` `:640-660`). Das Restrisiko „fremde `tempfile`-Nutzer sehen während
  des Fallbacks kein Env" entfällt damit **vollständig**; ein `threading.RLock` ist nicht
  erforderlich.
- **Keine persistenten Artefakte:** Die Funktion selbst legt keine Dateien/Verzeichnisse
  an (nur der Stdlib-`gettempdir()`-Aufruf gemäß Schritt 1).
- **Kein zusätzliches `realpath` auf dem Rückgabewert** (Golden-Stabilität: `PYTEST_BASETEMP`
  darf sich nicht allein durch Normalisierung ändern, z. B. `/var/folders/…` vs.
  `/private/var/folders/…` auf macOS).
- **Import-Zyklus:** `repo_containment` importiert weiterhin nichts aus `config`/`tmp_paths`
  (Bibliotheks-Doktrin, `repo_containment.py:1-8`).

### IC-2 — `scripts/lib/repo_containment.py::resolve_sink_absolute`

```python
def resolve_sink_absolute(
    project_root: "str | os.PathLike[str]", config: Optional[dict]
) -> Optional[Path]: ...
```

- **Zweck:** Öffentlicher, dünner Wrapper um `resolve_effective_repo_containment` +
  `_resolve_sink_dir`, damit `config.py` den Sink nicht über eine private Funktion
  auflösen muss.
- **Rückgabe:** realpath-`Path` des Sinks; `None` nur bei (a) **deaktiviertem** Sink oder
  (b) **ungültigem** Pfad (RVW2-8).
- **Finding-Check (RVW2-8, verbindlich):** Der Resolver fällt bei ungültigem
  `tmp-sink.path` auf den Default `.tmp` zurück und protokolliert das **nur** als Finding
  `repo-containment.tmp-sink-path` (`repo_containment.py:540-549`); `_resolve_sink_dir`
  liefert dann `<root>/.tmp`. Damit `None` überhaupt entstehen kann, prüft
  `resolve_sink_absolute` **vor** `_resolve_sink_dir` genau wie `_active_sink_dir`
  (`:590-594`):
  `bad = [f for f in effective.findings if f.code == "repo-containment.tmp-sink-path"]` ⇒
  bei Treffer `None`. Der Fallback-Default wird **nicht** stillschweigend als Sink
  zurückgegeben; wer ihn braucht, nutzt den Resolver direkt.
- **Fehlerpfad:** keiner (nicht-exitierend, wie der Resolver); strukturelle
  Config-Fehler bleiben Sache von `_validate_repo_containment`.

### IC-3 — `scripts/lib/tmp_paths.py::resolve_pytest_basetemp`

Signatur **unverändert** (`(project_root: Path, paths: TmpPaths) -> str`).

- Statt `tempfile.gettempdir()` verwendet die Funktion
  `system_temp_root(project_root, paths.absolute if paths.enabled else None)`:
  - Ausnahme aktiv (`enabled and pytest_basetemp`) ⇒ `<system_temp_root>/<user>/pytest-agent-meta`.
  - sonst Sink aktiv ⇒ `<absolute>/pytest` (unverändert).
  - sonst nur Exception ⇒ derselbe System-Temp-Pfad (unverändert).
  - sonst ⇒ `tmp-sink.system-temp-exception` (unverändert).
- Die Inside-Prüfung (`_is_inside(project_real, temp_real)`) prüft **denselben** Wert, der
  in den Pfad eingeht; sie bleibt als Defense-in-depth erhalten, obwohl IC-1 bereits
  In-Root-Kandidaten verwirft.
- `_system_temp_basetemp` erhält den Temp-Root als Parameter (kein versteckter
  `gettempdir()`-Zugriff mehr).
- Fehlerpfade: unverändert (`tmp-sink.system-temp-exception` inkl. Quote-/Newline-Prüfung,
  `tmp-sink.invalid-path` aus `resolve_tmp_paths`).

### IC-4 — `scripts/lib/config.py::_validate_repo_containment`

- Ersetzt in der Exception-Matrix den direkten `tempfile.gettempdir()`-Zugriff durch
  `resolve_sink_absolute(root, config)` + `system_temp_root(root, sink)`.
- `root` bleibt `config_path.parent.parent`.
- **Prüfscope unverändert:** Die Matrix läuft weiterhin nur, wenn
  `repo_containment.tmp-sink.system-temp-exception` **existiert** (`config.py:892`). Fehlt
  der Block, prüft der Validator nichts (RVW-9) — der gepinnte Default-Pfad wird
  ausschließlich von IC-3 abgedeckt.
- **Meldung** für echte Fälle bleibt inhaltlich unverändert: `"platform temp root <repr> is
  inside the project root — the exception cannot take effect."` Zusätzlich (RVW-12)
  Reparaturhinweis, wenn der beobachtete Root **innerhalb** des Repos liegt:
  `"If this is a stale framework pin: open a new shell or re-run 'python scripts/sync.py'."`
- `TmpSinkError` aus IC-1 wird zu `_fail(str(exc))` (Exit 1) — dieselbe harte Fehlerklasse
  wie heute, kein stiller Durchlauf.
- Ist der Sink-Pfad ungültig, liefert IC-2 `None`; die Temp-Root-Prüfung verhält sich dann
  wie heute (kein Fallback). Die bestehende, aussagekräftigere Pfad-Meldung
  (`invalid 'repo_containment.tmp-sink.path' …`, `:939-950`) bleibt unverändert.
- `resolve_effective_repo_containment` ist nicht-exitierend und schreibt nichts
  (`repo_containment.py:479-488`); der Validator bleibt die einzige harte Exit-Stelle.
- Keine Änderung an `_path_is_inside` (`config.py:786-792`).

### IC-5 — Pin-Helfer: Pro-Kopie-Vertrag, Fehler- und „kein Pin"-Policy (RVW-2/RVW2-1/RVW2-5)

Betrifft `admin-server.py::_tmp_sink_env`, `consistency-check.py::_tmp_sink_env`,
`lib/cli_commands.py::_admin_tmp_env`, `run_role_routing_eval.py::_tmp_sink_env`.

**Gemeinsame Regel (D7):** Ein fehlbarer Pin führt **nie** zu einem stillen
`env=None`-Spawn, sondern zu `TmpSinkError("tmp-sink.pin-unavailable", <Originalmeldung +
Hinweis "python scripts/sync.py --validate">)` (Import aus `lib.repo_containment`; Signatur
`(code, message)`). `SystemExit` aus `load_config` wird bewusst mitgefangen und übersetzt
(es erbt von `BaseException`; in einem Request-Thread würde die Antwort sonst ohne Meldung
verworfen).

#### IC-5a — Pro-Kopie-Tabelle (Rückgabetyp und „kein Pin"-Fall)

| # | Kopie | Signatur (Ziel) | „kein Pin" (Config fehlt / Sink aus / `ImportError`) | jeder andere Fehler |
|---|---|---|---|---|
| 1 | `admin-server.py::_tmp_sink_env(root) -> dict \| None` | `-> dict \| None` (unverändert) | `None` (Env erben) | `TmpSinkError` |
| 2 | `consistency-check.py::_tmp_sink_env(root) -> dict \| None` | `-> dict \| None` (unverändert) | `None` | `TmpSinkError` |
| 3 | `cli_commands.py::_admin_tmp_env(root) -> dict \| None` | `-> dict \| None` (unverändert) | `None` | `TmpSinkError` |
| 4 | `run_role_routing_eval.py::_tmp_sink_env(base: dict \| None = None) -> dict` | **`-> dict`** (unverändert; **nie** `None`) | das übergebene `base`-Env **inhaltlich gleich** zurückgeben (`os.environ` falls `base is None`) | `TmpSinkError` |

Zur Kopie 4 (RVW2-1/RVW3-4), verbindlich:

- **Warum kein `None`:** der Aufrufer dereferenziert direkt
  (`env = _tmp_sink_env(os.environ.copy())`, danach `env[model_var] = model_id`,
  `:729-732`). `None` wäre ein `TypeError`.
- **„Inhaltlich gleich" — nicht „dasselbe Objekt" (RVW3-4, verbindlich):** der Bestand
  **kopiert** (`env = dict(os.environ if base is None else base)`, `:705`). Gefordert ist
  daher „gleicher Key-Set und gleiche Werte", **nicht** Objektidentität. Ein Test mit
  `assert result is base` wäre falsch und ist unzulässig; zulässig ist
  `assert result == base` (bzw. Key-für-Key-Vergleich). Diese Präzisierung gilt
  gleichermaßen in AC-1189-26 und Test U4-26c.
- **`ImportError`-Zweig: nicht anwendbar.** `load_config` (`:55`) und
  `resolve_tmp_paths`/`tmp_env` (`:62`) werden auf Modulebene importiert; ein
  `ImportError` beendet das Modul vor jedem Helfer-Aufruf. Der Zweig bleibt auf die Kopien
  1–3 beschränkt — mit genau einer Warnzeile auf **stderr** und dem in **D7 Punkt 3**
  festgeschriebenen Wortlaut (RVW3-2: der Text ist **neu**, im Bestand existiert keine
  solche Zeile).
- **Abbruchort: vor der Case-Schleife.** `run_class` löst den Pin **einmal je Aufruf** vor
  der Run-/Case-Schleife auf (`pinned_env = _tmp_sink_env(os.environ.copy())`); ein
  `TmpSinkError` propagiert von dort ungefiltert bis `main`: `run_class` wird über den
  Runner (`:1008-1019`, Aufruf `:1021`) in `eval_gate.run_with_approval` ausgeführt, das die
  Runner **ohne** `try/except` aufruft
  (`scripts/lib/eval_gate.py:278`: `results = [runner() for runner in runners]`) ⇒ der
  Fehler erreicht `main` (`:930`) ungefiltert (**Belegstelle ergänzt, RVW3-6**).
  **Hinweis für den Plan:** `run_class` löst den Pin **pro Model-Klasse** auf, also nach
  der Freigabe und ggf. nach bereits bezahlten Aufrufen der ersten Klasse. Unschädlich,
  weil die Config innerhalb eines Laufs konstant ist — aber der Plan soll es wissen.
- **`call_provider` (additiv):** erhält das Env über einen neuen optionalen
  Keyword-Parameter `env: dict | None = None` (bei `None` löst es selbst über
  `_tmp_sink_env()` auf, damit bestehende Direktaufrufe/Tests unverändert bleiben) und
  arbeitet auf einer **Kopie** (IC-11).
- **Defense-in-depth:** Die Case-Schleife (`:783-802`) erhält neben `except ProviderError:
  raise` ein `except TmpSinkError: raise`. Damit kann ein Pin-Fehler auch dann nicht als
  „Miss" verbucht werden, wenn `call_provider` direkt (ohne `run_class`) aufgerufen wird.
- **Guard-Verträglichkeit (verbindlich, `tests/test_tmp_sink_env_coverage.py`):** Die
  Zuweisung, die in `call_provider` an `subprocess.run(env=…)` geht, muss den Pin-Token
  **textlich** enthalten, weil `_env_is_pinned` (`:156-172`) nur `_PIN_TOKENS` =
  `("tmp_env", "tmp_sink_env")` (`:46`) im Ausdruck bzw. in der `Name`-Zuweisung desselben
  Scopes erkennt. Zulässig und vorgesehen ist deshalb genau diese Form:
  `child_env = dict(_tmp_sink_env(os.environ.copy()) if env is None else env)`.
  Ein Zwischenschritt ohne Pin-Token (z. B. `child_env = dict(env)`) würde den Guard rot
  machen und eine neue Allowlist-Zeile erzwingen — die AC-1189-30 ausschließt.

#### IC-5b — Aufrufer → catch-Stelle → Exit-Code → Meldungsformat (RVW2-5)

**Stream-Konvention (RVW3-5, verbindlich):** `admin-server.py` schreibt seine
**Lifecycle-Zeilen** (`  +  `, `  i  `, `  !  `, `  -  `) mit **`print(...)` ohne
`file=`**, also auf **stdout** — so das zitierte Bestandsmuster `:6049-6051`
(`print(f"  !  Admin UI failed to start -- see {log_file}")`). Nur wenige Stellen nutzen
`sys.stderr` (`:63` PyYAML-Fehler, `:1027`, `:5880`, `:5893`, `:6147` root-fehlt). Damit ist
für die neuen Meldungen in `_admin_start_detached` / `VizManager._start` **stdout**
verbindlich, solange die Implementierung die bestehende Lifecycle-Konvention nicht
bewusst ändert. Meldungsformat Hausform für die übrigen Aufrufer:
`error: <code>: <message>` auf **stderr** (entspricht `f"error: {exc}"`, weil
`TmpSinkError.__str__` bereits `"<code>: <message>"` liefert; Muster
`cli_commands.py:1357-1359`). Der neue Helfer `_admin_tmp_env_or_exit` importiert
`TmpSinkError` lazy aus `lib.repo_containment` (bestehender Stil, z. B. `:1343`) und gibt bei
Erfolg `dict | None` unverändert weiter.

| Aufrufer | catch-Stelle (Eingriff) | Exit / Ergebnis | Meldung |
|---|---|---|---|
| `_admin_start_detached` | `try/except TmpSinkError` um den `env=`-Ausdruck (`:6032`/`:6038`), **vor** dem Spawn | kein Spawn; **Exit 1** | **stdout** `  !  tmp-sink pin unavailable: <message>` + `  i  Reparatur: python scripts/sync.py --validate` (Lifecycle-Muster `:6049-6051`) |
| `VizManager._start` | dito um `:650`/`:659` | kein Spawn; `False`, keine PID-Datei | **stdout** `  !  <label> not started: tmp-sink pin unavailable: <message>` |
| `SyncExecutor._run` | eigener `except TmpSinkError` **vor** `except Exception` (`:1380`) | kein Kind; `{"success": False, "output": "tmp-sink pin unavailable: <code>: <message>", "returncode": -1}`, via `_record_run` persistiert | im `output`-Feld |
| `ConsistencyService.run_consistency_check` | eigener `except TmpSinkError` **vor** `except Exception` (`:1761`; der generische Handler liefert sonst `ERR_CONSISTENCY_CHECK`) | kein Kind; `{"error": "tmp-sink pin unavailable: <code>: <message>", "findings": [], "summary": {"total": 0, "errors": 0, "warnings": 0}}`; HTTP-Status wie bisher bei diesem Rückgabewert (200) | im `error`-Feld |
| `cli_commands` (`sync.py`) | neuer Modul-Helfer `_admin_tmp_env_or_exit(root)`; ersetzt die Inline-Aufrufe `:575` und `:1732` | **Exit 2** | stderr `error: tmp-sink.pin-unavailable: <message>` |
| `consistency-check.py::main` | Top-Level-`try/except TmpSinkError` um den Lauf (Einstieg `:287`) | **Rückgabe 2** | stderr `error: tmp-sink.pin-unavailable: <message>`; bei `--json` stattdessen genau ein JSON-Objekt `{"error": "tmp-sink.pin-unavailable", "detail": "<message>"}` auf stdout |
| `run_role_routing_eval.py::main` | Top-Level-`try/except TmpSinkError` um den Lauf (Einstieg `:930`) | **Rückgabe 2** | stderr `error: tmp-sink.pin-unavailable: <message>` |

**Admin-UI-Nutzer (was er sieht):** bei `POST /api/sync/dry-run|run` eine Antwort mit
`success: false` und dem Klartextgrund im `output`-Feld (kein 500er, kein Traceback); bei
`GET /api/consistency-check` ein JSON mit `error`-Feld und leeren `findings` (die UI zeigt
wie heute ihren Fehlerzustand, aber mit Ursache); bei `start`/`restart` **kein** „Admin UI
started", sondern die Fehlerzeile plus Reparaturhinweis und Exit 1.

**Docstring-Pflichten:**
`TmpSinkError` (`repo_containment.py:566-568`) listet zusätzlich `tmp-sink.pin-unavailable`
und `tmp-sink.system-temp-exception` (IC-1) und behält „Callers map it to Exit 2" — die
Ausnahme `admin-server.py`-Lifecycle (Exit 1) wird dort benannt.

**Invarianten:** Docstring „Der Pin ist Transport-Detail; Konsumenten dürfen daraus
**keine** Aussage über den System-Temp-Root ableiten." · **Kein** neuer Env-Key · keine
Änderung an `tmp_env`/`tmp_sink_env_pin_block`.

### IC-6 — `scripts/admin-server.py::_is_pid_running`

```python
def _is_pid_running(pid: int | None) -> bool: ...
```

- POSIX: nach erfolgreichem `os.kill(pid, 0)` zusätzlich Zombie-Erkennung, wenn
  `/proc/<pid>/stat` lesbar ist (Feld 3 == `Z` ⇒ `False`).
- `/proc` nicht verfügbar / nicht lesbar ⇒ bisheriges Verhalten (kein Fehlschlag).
- Windows-Zweig unverändert.
- **Keine** Ausnahme nach außen (bestehende `except`-Klauseln bleiben).

### IC-7 — `scripts/admin-server.py::_wait_for_admin` (neu; RVW-6/7/11/RVW3-1)

**Reichweite (verbindlich):** Dieser Helfer ist die **heuristische** Stufe 2 der
Start-Verifikation. Er beantwortet die Frage „lebt unser Kind nach dem Spawn noch und
antwortet auf dem Port etwas Erwartetes?" — **nicht** die Frage „hat unser Kind den Port
gebunden?". Die deterministische Stufe 1 ist IC-12 und läuft **vor** dem Spawn.

```python
def _wait_for_admin(
    proc: subprocess.Popen,
    host: str,
    port: int,
    *,
    expected_mode: str,
    token_configured: bool,
    timeout: float = START_VERIFY_TIMEOUT,
    interval: float = START_VERIFY_INTERVAL,
    confirm_grace: float = START_CONFIRM_GRACE,
) -> tuple[bool, str]: ...
```

- **Kein `token`-Parameter, kein `Authorization`-Header** — bewusst (D6).
- **Früh-Abbruch** ⇔ `proc.poll() is not None` ⇒ `(False, "exited:<code>")`.
- **Kandidaten-Kriterium** (ein einzelner Treffer ist **kein** Erfolg, RVW2-2):
  - `token_configured is False`: HTTP 200, `status == "ok"`, und (`pid` vorhanden ⇒
    `pid == proc.pid`; sonst `mode == expected_mode`).
  - `token_configured is True`: HTTP **401** (erwartete Verweigerung des eigenen Servers).
- **Bestätigungsfenster (verbindlich):** Beim ersten Kandidatentreffer wird
  `confirm_since = time.monotonic()` gesetzt. Erfolg **nur**, wenn das Kriterium
  `confirm_grace` Sekunden lang **ununterbrochen** weiter erfüllt ist **und** am
  Fensterende in dieser Reihenfolge geprüft wird: letzte HTTP-Antwort erfüllt das
  Kriterium → `proc.poll() is None`. Jede nicht-erfüllte Probe im Fenster setzt
  `confirm_since = None` (Fenster beginnt neu); ein `poll() is not None` bricht sofort ab.
  **Was das Fenster leistet:** Ein Portinhaber, der nur kurzzeitig 401 liefert, und ein Kind,
  das **innerhalb** des Fensters am Bind scheitert und exit't, führen zuverlässig zu einem
  Fehlschlag — der Einzelereignis-Erfolg aus RVW2-2 ist damit beseitigt.
  **Was es nicht leistet (RVW3-1, verbindlich):** es
  beweist **nicht**, dass das Kind gebunden hat. Endet das Fenster, bevor das Kind seinen
  Bind-Versuch erreicht (Pre-Bind-Phase: Interpreter-Start, Modul-Importe
  `:40-60`, zwei `load_config`-Läufe, Bind erst `:5918`), kann ein bereits laufender
  Portinhaber weiterhin einen falschen Erfolg erzeugen. Solange das Kind jedoch nach dem
  Fenster am Bind scheitert, exit't es unmittelbar danach — der Fehlerzustand ist dann
  sichtbar (`failed to start`/PID-Datei), nur eben **nach** der Erfolgsmeldung. Dieses
  Restrisiko ist **kein** Implementierungsfehler, sondern die Grenze des Verfahrens und in
  R11/R16 sowie Threat-Model (g) ausgewiesen. Die Rev-3-Formulierung, das Fenster verhindere
  einen falschen Erfolg generell, ist als **überzogen gestrichen**.
- **Fehlschlag** ⇔ Deadline erreicht ohne bestätigten Erfolg ⇒ `(False, "timeout")`
  (Kandidat gesehen, aber nie stabil ⇒ `(False, "unconfirmed:<last_status>")`);
  HTTP-Status ohne Erfolg ⇒ `(False, "health:<status>")`; falsche `pid`/`mode` ⇒
  `(False, "identity:<…>")`.
- **Deadline-Semantik:** `timeout` begrenzt die **Kandidatensuche**. Ein zum
  Deadline-Zeitpunkt **laufendes** Bestätigungsfenster darf bis `confirm_grace` über die
  Deadline hinaus abgeschlossen werden (sonst wäre jeder spät antwortende, aber gesunde
  Server ein falscher Fehlschlag); ein neues Fenster wird nach der Deadline nicht mehr
  begonnen.
- **`token_configured` — Quelle (RVW2-3, verbindlich, nicht `args.admin_token` allein):**
  ```text
  admin_cfg       = _load_admin_ui_config(root)            # :524-566
  effective_token = _resolve_admin_token(                  # :887-906
      cli_token=args.admin_token,
      config_token=admin_cfg["token"],
      config_token_file=admin_cfg["token_file"],           # :553
  )
  token_configured = effective_token is not None
  ```
  Priorität damit identisch zum Kind (`AdminServer.__init__`, `:5862-5868`):
  CLI > `ADMIN_UI_TOKEN` > `admin-ui.token` > `admin-ui.token-file`. **Wichtig:**
  `_admin_start_detached` hat keinen `--admin-token-file`-Schalter (argparse `:6120`) und
  reicht auch keinen an das Kind weiter (`:6012-6013`) — das Kind liest
  `admin-ui.token-file` selbst aus der Config (`:5867`); deshalb muss der Elternprozess
  `admin_cfg["token_file"]` einsetzen. Schluckt `_load_admin_ui_config` eine Exception,
  gelten seine Defaults (`token=None`) ⇒ `token_configured=False`; ein durchschlagender
  `SystemExit` beendet den Start sichtbar (Exit ≠ 0), nie mit falschem Erfolg.
- **Netzwerk:** `build_opener(ProxyHandler({}))` + deaktivierter
  `HTTPRedirectHandler`; nur `http://`; Wildcard-Bind (`0.0.0.0`/`::`) wird auf Loopback
  (`127.0.0.1`/`::1`) geprobt; Verbindungs-Timeout ≤ 1 s pro Versuch.
- Konstanten (Modul-Konstanten, in Tests überschreibbar): `START_VERIFY_TIMEOUT`
  (Default 5.0 s), `START_VERIFY_INTERVAL` (Default 0.1 s), `START_CONFIRM_GRACE`
  (Default 1.0 s). Invariante: `START_CONFIRM_GRACE < START_VERIFY_TIMEOUT`.
- Kein `sleep` im Testpfad nötig: Tests rufen den Helfer mit kleinem `timeout`/
  `confirm_grace` direkt auf.

### IC-8 — `scripts/admin-server.py::_admin_start_detached` (Ablauf; RVW-8/RVW3-1)

1. Vorprüfung „already running" über `_read_pid` + `_is_pid_running` (unverändert).
2. **Pre-Flight-Bind-Probe (neu, deterministisch, IC-12):** `_probe_port_bindable(host,
   port)` **vor** jedem Spawn. Ist der Port nicht bindbar ⇒ **Exit 1** mit Meldung
   `  !  cannot bind <host>:<port>: <errno-Text>` + `  i  Port belegt? Anderen --port wählen.`,
   **kein** Spawn, **keine** PID-Datei, **kein** Log-Eintrag. Bei `port == 0` entfällt der
   Schritt (D6 Punkt 6).
3. Log-Datei wie bisher; Spawn wie bisher **inklusive** `env=_tmp_sink_env(root)`;
   `TmpSinkError` aus IC-5 wird **vor** dem Spawn gefangen ⇒ kein Spawn,
   **stdout**-Meldung + Reparaturhinweis, **Exit 1** (D7/IC-5b).
4. **PID-Datei sofort schreiben** (wie heute, `:6041`) — `status`/`stop`/zweiter `start`
   bleiben im Verifikationsfenster funktionsfähig (RVW-8).
5. **Verifikation** über IC-7 (heuristisch) — erwarteter `mode` = `detect_mode(root)`,
   `token_configured` = **`_resolve_admin_token(...)` ist nicht `None`**, aufgelöst aus
   `_load_admin_ui_config(root)` + `args.admin_token` — exakt die Quellen/Priorität aus
   IC-7, RVW2-3; **nicht** nur `args.admin_token`. Die Verifikation prüft den
   **Kind-Lebenslauf**, nicht den Bind-Erfolg (der ist bereits durch Schritt 2 abgedeckt,
   soweit er entscheidbar war).
6. **Erst bei Erfolg** Erfolgsmeldung mit URL (kein erneutes Schreiben der PID-Datei nötig).
   Die Erfolgsmeldung ist **keine** Aussage „Port gehört nachweislich dem Kind", sondern
   „Kind lebt nach dem Bestätigungsfenster und der Port antwortet erwartungsgemäß".
7. Bei Fehlschlag: Kind beenden (`proc.terminate()`, Windows `proc.kill()`/`taskkill`),
   PID-Datei `unlink(missing_ok=True)`, **Log-Tail** (letzte 20 Zeilen, ohne
   Roh-Exception-Stack) ausgeben, `sys.exit(1)`. Die Meldung enthält weiterhin
   `failed to start` (Bestandstext, AC-1189-14) **und** den Log-Tail.
8. `restart` bleibt `stop` + `start`; es erbt das neue Verhalten ohne eigene Logik (inkl.
   Pre-Flight-Probe). Ein `stop`, das während der Verifikation läuft, beendet das Kind ⇒
   `start` endet deterministisch mit `exited:<code>` und räumt die PID-Datei auf.

### IC-9 — `scripts/admin-server.py::VizManager._start`

- Ersetzt `time.sleep(1.5)` + `_is_pid_running(proc.pid)` durch `proc.poll()`-basiertes
  Warten über eine **eigene** Konstante `VIZ_START_GRACE` (Default 1.5 s) — **nicht**
  `START_VERIFY_TIMEOUT` (RVW2-7). Begründung: Ein gesundes Viz-/MCP-Kind stirbt nie,
  Erfolg ist also erst nach Ablauf des Fensters belegbar; mit 5 s pro Kind verzögerte
  `start_all()` (`:5949-5952`, zwei Kinder) den Serverstart um bis zu 10 s statt 3 s.
  Ein HTTP-Kriterium greift dort nicht (kein gemeinsamer Health-Vertrag der Sub-Server).
- Bei Fehlschlag: bisheriges Verhalten (Meldung `"failed to start -- see <log>"`, PID-Datei
  entfernen, `False`) bleibt; zusätzlich Log-Tail, wenn die Log-Datei lesbar ist.
- `TmpSinkError` aus IC-5 ⇒ kein Spawn, `False`, Meldung (IC-5b).
- Erfolgsmeldung unverändert.

### IC-10 — `scripts/admin-server.py::_route_get_health` (additiv, RVW-11/RVW2-10)

- Antwort erhält zusätzlich **`pid`** (`os.getpid()`). **`root` entfällt** (RVW2-10): `/api/health`
  ist ohne Token unauthentifiziert (`_is_public_get_path` `:3514-3524` negativ ⇒ Token-Check,
  aber bei nicht konfiguriertem Token faktisch offen) und würde den absoluten Projektpfad
  preisgeben (`/api/mode` liefert ihn heute nur token-gated, `:3801-3813`). `pid` genügt als
  Identitätsaussage für IC-7.
- `status`, `version`, `mode` bleiben unverändert; keine Schema-/Route-Änderung, kein neues
  Feld in einer Config.
- Zweck: Identitätsprüfung der Start-Verifikation (IC-7) ohne Token-Versand.
- **Rest-Offenlegung (dokumentiert):** `pid` des Servers wird im token-freien Fall sichtbar —
  das ist eine Prozess-ID, kein Pfad und kein Credential; sie ändert die Angriffsfläche nicht
  (ein lokaler Nutzer kann PIDs ohnehin aus `/proc` ableiten).

### IC-11 — Explizit unveränderte Schnittstellen

`tmp_env`, `tmp_sink_env_pin_block`, `work_dir_env`, `TMP_ENV_KEYS`, `resolve_tmp_paths`,
`TmpPaths`, `SystemTempException`, `tmp_sink_path_error`, `tmp_sink_location_error`
(Verhalten; nur Docstring gemäß D8), `tests/conftest.py::effective_basetemp` sowie alle
Admin-HTTP-Routen außer der additiven Health-Payload behalten Signatur **und** Verhalten.
**Additiv** (kein Bestandsaufruf bricht): `call_provider(..., env: dict | None = None)` in
`run_role_routing_eval.py` (IC-5a) — die sechs Positionsparameter bleiben unverändert.
**Nicht** mehr unverändert: die vier Pin-Helfer (IC-5a/D7), `_wait_for_admin` (neu),
`_admin_start_detached`, `VizManager._start`, `_is_pid_running` (Zombie-Guard) und die
Health-Payload (IC-10).
**Neu (additiv, kein Bestandsaufruf bricht):** `_probe_port_bindable` (IC-12) — eine neue,
private Funktion in `admin-server.py`, die von `_admin_start_detached` aufgerufen wird.

### IC-12 — `scripts/admin-server.py::_probe_port_bindable` (neu; RVW3-1/D6)

```python
def _probe_port_bindable(host: str, port: int) -> tuple[bool, str]: ...
```

- **Annotationsstil:** ungequotet — so wie `admin-server.py` selbst schreibt
  (`:1114` `tuple[Path, bool]`, `:892` `str | None`); die Datei setzt PEP-604-Syntax voraus.

- **Zweck:** Deterministische Stufe 1 der Start-Verifikation — prüft **vor** dem Spawn, ob
  das Kind `(host, port)` überhaupt binden könnte. Ersetzt **keine** Kind-Bindung und
  persistiert nichts.
- **Rückgabe:** `(True, "")` bei bindbarem Port; `(True, "skipped:port-0")` bei `port == 0`;
  `(False, "<errno-name>: <strerror>")` bei `OSError` — z. B.
  `(False, "EADDRINUSE: Address already in use")`.
- **Keine Exception nach außen.** Jeder Fehler wird als `(False, …)` gemeldet; die
  Entscheidung über Exit/Meldung trifft der Aufrufer (IC-8 Schritt 2).
- **Ablauf:**
  1. `port == 0` ⇒ sofort `(True, "skipped:port-0")` (OS-vergeben, nicht vorab prüfbar —
     D6 Punkt 6).
  2. Adresse auflösen: `socket.getaddrinfo(host, port, type=SOCK_STREAM, flags=AI_PASSIVE)`;
     erster Eintrag bestimmt `family`/`sockaddr`. `socket.gaierror` ⇒ `(False, …)`.
  3. `sock = socket.socket(family, SOCK_STREAM)`; `sock.setsockopt(SOL_SOCKET,
     SO_REUSEADDR, 1)` — **dieselbe Semantik wie das Kind**.
     **VERIFIED:** das Kind nutzt `_DaemonThreadingHTTPServer((host, port), …)`
     (`:5918`), eine `ThreadingHTTPServer`-Subklasse (`:5817`);
     **ASSUMED (Stdlib-Dokumentation, in dieser Session nicht ausgeführt):**
     `http.server.HTTPServer.allow_reuse_address` ist `1`, `ThreadingHTTPServer` erbt das.
     Der Plan soll die Parität in einem Test belegen (U4-18b: nach erfolgreicher Probe ist
     ein zweites `bind()` auf denselben Port durch einen **Listener** abweisbar — d. h. die
     Probe hat den Port nicht dauerhaft belegt). **Kein** `SO_REUSEPORT` — das würde einen
     echten Doppel-Listener zulassen und die Probe entwerten.
  4. `sock.bind(sockaddr)` ⇒ Erfolg/Rückgabe; `finally: sock.close()`.
  5. **Kein** `listen()`, **kein** `accept()`, keine Verbindung ⇒ kein `TIME_WAIT`, kein
     Verbindungs-Log beim Ziel, kein Zustand.
- **Warum ein Bind und kein Connect:** Ein Connect gegen einen fremden Listener würde eine
  Anfrage auslösen (und ggf. Credentials/Logs berühren). `bind()` ist zustandslos und
  verrät nach außen nichts.
- **Privilegierte Ports (<1024):** `PermissionError` ⇒ `(False, "EACCES: …")`; das ist
  korrekt, denn das Kind scheiterte ebenso.
- **Reichweite / TOCTOU (verbindlich, RVW3-1):** Die Probe ist **nur** eine
  Momentaufnahme. Zwischen `close()` der Probe und dem `bind()` des Kindes
  (`:5918`) kann ein Fremdprozess den Port übernehmen, und die Probe selbst kann einen
  Fremdprozess für Millisekunden aussperren (der ihn dann erneut versucht). Beides ist
  **Restrisiko, kein Fehler** — ausgewiesen in R11/R16 und Threat-Model (g). Der Nutzen
  bleibt: der **häufige** Fall (Port dauerhaft belegt) ist jetzt deterministisch erkannt,
  statt über eine Zeitannahme geraten.
- **Nicht anwendbar auf** `VizManager._start`: Viz-/MCP-Kinder binden eigene Ports aus der
  Config (`viz_port`, `:713`/`:768`); eine Probe dort ist nicht Teil dieses Fixes
  (Nicht-Ziel, könnte als Folgearbeit nachgezogen werden).
- **Konstanten:** keine neuen. Die Probe ist synchron und < 1 ms; ein Timeout ist nicht
  erforderlich (kein Netzwerk-IO).

---

## Datenfluss

### Fluss 1 — Admin-Start eines Kindes (`start`/`restart`)

```text
CLI (ggf. selbst gepinnt)
  └─ _admin_start_detached
       ├─ Stufe 1 (deterministisch): _probe_port_bindable(host, port)
       │        ├─ (False, …)  ⇒ Meldung + Exit 1 (kein Spawn, keine PID-Datei)   [IC-12]
       │        └─ (True, …)   ⇒ weiter
       ├─ _tmp_sink_env(root) ── resolve_tmp_paths(root, load_config)
       │        ├─ TmpSinkError ⇒ Meldung + Exit 1 (kein Spawn)
       │        └─ tmp_env(paths) → TMPDIR=TEMP=TMP=<abs sink>
       ├─ Popen(admin-server.py, env=<pin>) + PID-Datei sofort schreiben
       └─ Stufe 2 (Heuristik): _wait_for_admin (ohne Token, ohne Proxy/Redirects)
            ├─ proc.poll()       → beendet? ⇒ Fehlschlag (Exitcode)
            └─ GET /api/health   → 200+pid/mode bzw. 401 (Token) als Kandidat, START_CONFIRM_GRACE stabil + poll() is None ⇒ Erfolg
                                    sonst ⇒ Kind beenden, PID-Datei löschen, Exit 1
            ⚠ Restfenster: endet das Fenster vor dem Kind-Bind (:5918), ist ein
              späterer Bind-Fehlschlag nicht mehr durch Stufe 2 abgedeckt (R11/R16).
```

**Was Stufe 1 und Stufe 2 zusammen garantieren:** Ein **dauerhaft** belegter Port führt
deterministisch zu Exit 1 **ohne** Spawn (Stufe 1). Ob ein **während/nach** der Probe
übernommener Port den Start fälschlich als Erfolg erscheinen lässt, entscheidet die
Kind-Pre-Bind-Zeit gegen `START_CONFIRM_GRACE` — das ist die dokumentierte Heuristik-Grenze
(Stufe 2), keine Garantie.

Der **Kindprozess** lädt beim Boot `load_config` → `_validate_repo_containment` →
`system_temp_root(root, sink)`. Da `gettempdir()` == Sink, wird der ungepinnte Root
(`/tmp`, `/var/tmp`, …) bewertet ⇒ nicht im Repo ⇒ **kein** Abbruch. Genau dieser Punkt
heilt `start`/`restart`, `dry-run`, `run`, `consistency-check` und die Viz-/MCP-Kinder, ohne
den Pin anzutasten.

### Fluss 2 — sync über den Admin-Server (`dry-run`/`run`/`--validate`)

```text
SyncExecutor._run
  ├─ env=_tmp_sink_env(root)            (Pin bleibt; TmpSinkError ⇒ kein Kind, success=False)
  └─ sync.py --validate
       ├─ load_config → _validate_repo_containment → system_temp_root(root, sink) ⇒ ok
       └─ _build_orch_variables
            └─ resolve_tmp_paths → resolve_pytest_basetemp
                 └─ system_temp_root(root, sink) ⇒ <system-temp>/<user>/pytest-agent-meta
       ⇒ PYTEST_BASETEMP/TEST_COMMANDS identisch zur Baseline „ohne Sink-Keys"
```

### Fluss 3 — Validierung ohne Pin (Referenzfall)

`system_temp_root` liefert `gettempdir()` unverändert (Schritt 2); alle Prüfungen verhalten
sich exakt wie heute. Damit ist der Fix ein **No-op** für jeden Aufruf ohne Sink-Pin.

### Matrix: Pin × Sink × Exception

| Sink | Exception | beobachteter Temp-Root | Ergebnis |
|---|---|---|---|
| aktiv | enabled + pytest | == Sink | **kein** Fehler; Basetemp = ungepinnter System-Temp-Root |
| aktiv | enabled + pytest | ≠ Sink, im Repo | Fehler `tmp-sink.system-temp-exception` + Repair-Hinweis (unverändert) |
| aktiv | enabled + pytest | ≠ Sink, außerhalb | ok, Basetemp = beobachteter Root (unverändert) |
| aktiv | `pytest-basetemp: false` | beliebig | keine Exception-Prüfung; Basetemp = `<sink>/pytest` (unverändert) |
| aktiv | **Block fehlt** (Defaults: enabled + pytest) | == Sink | **Validator prüft hier nicht** (`config.py:892`); der Schutz kommt ausschließlich aus IC-3 (Resolver) — RVW-9 |
| aktiv | `toolchain-caches: true` | == Sink | wie Zeile 1; Cache-Env im Pin-Block unverändert (`<sink>/cache/{pip,npm}`) |
| **deaktiviert** | enabled + pytest | == `<root>/.tmp` | **Fehler bleibt** (kein Pin ⇒ kein Freibrief) |
| deaktiviert | enabled + pytest | außerhalb | ok (unverändert) |
| beliebig | beliebig | Pin nicht bestimmbar (kein Kandidat außerhalb `root`) | `TmpSinkError`; Aufrufer bricht ab (D7), kein ungepinntes Kind |

---

## Betroffene Komponenten / Aufrufer

| # | Komponente / Aufrufer | Änderung | Fehlerverhalten danach |
|---|---|---|---|
| 1 | `admin-server.py::_admin_start_detached` (`start`, `restart`) | IC-12 (Pre-Flight-Probe) + IC-7/IC-8: Exitstatus + Health, PID sofort, Log-Tail | Exit 1 bei belegtem Port **vor** dem Spawn (deterministisch) und bei totem/ungesundem Kind nach dem Spawn (heuristisch); fehlbarer Pin ⇒ Exit 1. Kein falscher Erfolg für den Fall „Port dauerhaft belegt" |
| 2 | `admin-server.py::VizManager._start` (Viz + MCP) | IC-9: `poll()` statt `kill(pid,0)`/`sleep` | `False` + PID-Datei entfernt; bei `TmpSinkError` kein Spawn |
| 3 | `admin-server.py::SyncExecutor._run` (`POST /api/sync/dry-run`, `POST /api/sync/run`) | Pin bleibt; IC-5-Fehler wird zu `success=False` (kein Kind) | Kind läuft durch; `success` spiegelt echten Exitcode |
| 4 | `admin-server.py::ConsistencyService.run_consistency_check` (`GET /api/consistency-check`) | dito | JSON-Antwort statt generischem Fehler |
| 5 | `admin-server.py::_tmp_sink_env` | IC-5a/D7: „kein Pin" nur für 3 Zustände (`None`), sonst `TmpSinkError` | sichtbarer Abbruch statt stillem `env=None` |
| 6 | `consistency-check.py::_tmp_sink_env` | dito (Kopie 2, `dict \| None`) | stderr-Meldung; **Exit 2**; keine ungepinnten git-Kinder |
| 7 | `run_role_routing_eval.py::_tmp_sink_env` | **Kopie 4** (IC-5a): `-> dict`, nie `None`; Pin einmal vor der Case-Schleife; `except TmpSinkError: raise` | Eval bricht **vor** dem ersten Provider-Aufruf ab, Meldung, **Exit 2** (keine Baseline aus Misses) |
| 8 | `lib/cli_commands.py::_admin_tmp_env` | dito (Kopie 3, `dict \| None`) + `_admin_tmp_env_or_exit` an den zwei Aufrufstellen | CLI-Start bricht sichtbar ab, **Exit 2** |
| 9 | `resolve_pytest_basetemp` (`tmp_paths.py`) | IC-3: nutzt `system_temp_root` | kein Abbruch unter Pin; Wert unverändert zur Baseline |
| 10 | `_validate_repo_containment` (`config.py`) | IC-4: `resolve_sink_absolute` + `system_temp_root` + Repair-Hinweis | kein Abbruch bei Pin; echte Fehlkonfiguration bricht weiter laut ab |
| 11 | `system_temp_root` / `resolve_sink_absolute` (`repo_containment.py`) | **neu** (IC-1/IC-2), read-only | `TmpSinkError` nur, wenn kein Kandidat außerhalb `root` |
| 12 | `repo_containment.py::tmp_sink_location_error` | **unverändert**, vom selben Begriff abhängig; Docstring-Korrektur (D8) | #1136-Verhalten bleibt (Präzedenzfall für D1) |
| 13 | `admin-server.py::_route_get_health` | IC-10: `pid` additiv (**ohne** `root`, RVW2-10) | Route/Statuscodes unverändert |
| 14 | `_is_pid_running` | IC-6: Zombie-Guard (POSIX) | `status`/`stop`/„already running" melden keinen Zombie als RUNNING |
| 15 | `tests/conftest.py::effective_basetemp` | **unverändert, semantisch betroffen** (RVW-5) | warnt weiter nur; ein ungebaseter pytest-Lauf erbt den Pin (dokumentierte Grenze) |
| 16 | `admin-server.py::_probe_port_bindable` | **neu** (IC-12, RVW3-1): Bind/Schließen auf `--host`/`--port` vor dem Spawn | `(False, errno)` ⇒ Exit 1 ohne Spawn; wirft nie |

**Korrektur zur Auftrags-Zuordnung (VERIFIED):** Die Zeilen `admin-server.py:6032/:6038`
gehören zu `_admin_start_detached` (Admin-Server-Kind), **nicht** zu den Viz-/MCP-Prozessen;
diese laufen über `VizManager._start` (Popen im Bereich `:643-660`). Beide sind betroffen,
aber aus unterschiedlichen Gründen (IC-8 vs. IC-9).

---

## Rückwärtskompatibilität

- **Keine Config-Migration:** `.meta-config/project.yaml` und
  `config/project-config.schema.json` bleiben unverändert; alle bestehenden Configs
  validieren weiter (AC-1189-05).
- **Kein Verhaltenswechsel ohne Pin:** `system_temp_root(root, None oder ≠ Sink)` ==
  `gettempdir()`; jeder Bestandsaufruf außerhalb eines gepinnten Kindes ist bit-identisch.
- **Rendered-Artefakte unverändert:** `PYTEST_BASETEMP`, `TEST_COMMANDS`,
  `CODE_QUALITY_RULES`, Goldens (`tests/fixtures/slimming-golden/**`) bleiben gleich — auch
  wenn `sync.py` unter Pin läuft (AC-1189-09).
- **ADR-12 (absolute Env-Pins) unangetastet:** `tmp_env`/`tmp_sink_env_pin_block` setzen
  weiterhin ausschließlich absolute Werte; die Spec ändert nur die **Interpretation** des
  resultierenden `gettempdir()`.
- **Containment-Regeln unangetastet:** Sink darf nicht ins System-Temp auflösen
  (`tmp_sink_location_error`, #1136/#1140), Sink bleibt im Repo, §5.5 bleibt (für den
  gerenderten Aufruf).
- **Vorgänger-Spec unangetastet (inhaltlich):** AC-11 (jeder Subprozessstart pinnt oder ist
  allowlistet), AC-15 (Exception-Matrix), IC-04/IC-06/IC-18 gelten weiter. Diese Spec
  **präzisiert** „System-Temp-Root" und ergänzt in der Vorgänger-Spec nur den Verweis (D8).
- **Verhaltensänderung, bewusst:** `_tmp_sink_env` startet bei defekter Config kein
  ungepinntes Kind mehr (D7); die Eval-Kopie bricht stattdessen **vor** dem ersten
  Provider-Aufruf ab (IC-5a, RVW2-1) und schreibt keine Baseline aus Misses. Das ist die
  Abkehr von „Verhalten unverändert", die das Review verlangt; sie ist in
  [Nicht-Ziele](#nicht-ziele), D7 und IC-5b ausgewiesen.
- **API:** keine öffentliche Signatur ändert sich für gültige Aufrufer; zwei neue
  öffentliche Funktionen in `repo_containment` (IC-1/IC-2) sowie der optionale
  `env`-Keyword-Parameter an `call_provider` (IC-11) sind additiv. `_probe_port_bindable`
  (IC-12) ist eine **private** Funktion in `admin-server.py` — kein öffentlicher Vertrag.
- **Bewusste Verhaltensänderung von `start` (RVW3-1):** Ein belegter Port führt künftig
  **vor** dem Spawn zu Exit 1; heute würde der Befehl einen Prozess starten und Erfolg
  melden. Das ist die gewünschte Korrektur (AC-1189-17), keine Regression: Es gibt keinen
  Aufrufer, der von einem Fehlstart profitiert.

---

## Architektur-Entscheidungen (ADR-Kurzform)

| ADR | Kontext | Entscheidung | Konsequenzen |
|---|---|---|---|
| ADR-1189-01 | Pin und Exception benutzen `gettempdir()` als gemeinsame Wahrheit | Pin ist Transport-Detail; Sink-Gleichheit entkoppelt beide Begriffe (D1) | + ein Ort der Wahrheit `system_temp_root`; − Kandidatenliste muss Stdlib-Reihenfolge nachbilden |
| ADR-1189-02 | Auftragsskizze nannte `<sink>/pytest` als Basetemp unter Pin | ungepinnter System-Temp-Root (D2) | + §5.5 und Golden-Stabilität; − Fallback-Berechnung nötig, Fehlerpfad bei fehlendem Kandidaten |
| ADR-1189-03 | Marker-Env wäre präziser, verlangt aber neue Oberfläche | Pfadvergleich statt Marker (D1) | + keine neue Env-Variable, Reproduktion grün; − manuell gesetzter Sink-TMPDIR wird als Pin akzeptiert (gewollt) |
| ADR-1189-04 | `os.kill(pid,0)` beweist keinen laufenden Server | `Popen.poll()` + Health (D5) | + kein falscher Erfolg bei totem/ungesundem Kind, Ursache im Log-Tail sichtbar; − beweist nicht den Bind-Erfolg, deshalb Stufe 1 (ADR-1189-08) |
| ADR-1189-05 | Health-Probe würde den Admin-Token an den Portinhaber senden | **kein** Token-Versand; 200+`pid` bzw. 401 **nach Bestätigungsfenster** als Kriterium (D6/IC-7) | + kein Credential-Leak an Fremdprozess/Proxy; − Identität bei Token-Setup stützt sich auf Port-Bind + Fensterstabilität des lebenden Kindes, d. h. **Heuristik**, keine Garantie (RVW3-1) |
| ADR-1189-06 | `TmpSinkError` wurde von den Pin-Helfern geschluckt | „kein Pin" nur für 3 Zustände, sonst `TmpSinkError` (D7/IC-5a); Rückgabe je Kopie (`None` bzw. `base`-Env **inhaltlich gleich**) | + kein stilles ungepinntes Kind, auch nicht in der Eval; − Verhaltensänderung in vier Helfern (dokumentiert) |
| ADR-1189-07 | Fallback per Env-Mutation war nicht thread-tauglich | read-only Kandidatenwahl, keine Mutation (D1/IC-1) | + thread-tauglich, kein Restore-Vertrag; − private `tempfile._candidate_tempdir_list` als Primärquelle (guarded) |
| ADR-1189-08 | Der falsche Erfolg bei belegtem Port war nur über eine Zeitannahme („Kind bindet innerhalb des Fensters") abgefangen; `/api/health` token-frei zu stellen (Option A) hätte un­authentifizierte Versions-/Modus-/PID-Enumeration bei Wildcard-Bind erlaubt | **Option B:** deterministische Pre-Flight-Bind-Probe **vor** dem Spawn (IC-12) + Fenster ausdrücklich als Heuristik (D6/IC-7) | + häufiger Realfall deterministisch erkannt, kein Kind gestartet, Auth-Oberfläche unverändert; + eine Ehrlichkeitsaussage statt einer unbelegten Garantie; − TOCTOU-Restfenster zwischen Probe und Kind-Bind bleibt und ist in R11/R16 benannt; − ein zusätzlicher Bind/Schließen-Zyklus |

---

## Threat Model (4 Fragen; RVW-6)

1. **Was wird gebaut?** Ein read-only Resolver (`system_temp_root`, `resolve_sink_absolute`)
   in `repo_containment`, eine Neudefinition von „System-Temp-Root", eine
   **Pre-Flight-Bind-Probe** im Elternprozess (`_probe_port_bindable`, IC-12, bindet und
   schließt den Port, ohne `listen()`/`accept()`), eine unauthentifizierte HTTP-Health-Probe
   im CLI (ohne Token, ohne Proxy, ohne Redirects, mit Bestätigungsfenster als Heuristik),
   ein additives **`pid`**-Feld an `/api/health` (**ohne** `root`/Pfadangabe, RVW2-10) und
   eine Zombie-Erkennung über `/proc`. Keine neuen Daten, keine neuen Endpunkte, kein Schema,
   **keine** Änderung der Auth-Oberfläche (Option A ist verworfen, D6).
2. **Was kann schiefgehen?**
   (a) Credential-Exposure an einen Fremdprozess oder `http_proxy` — **durch D6 eliminiert**
   (kein Token wird gesendet; Probe ohne Proxy/Redirects);
   (b) Fallback liefert einen Pfad, der *doch* im Repo liegt (falsche Kandidatenwahl) —
   durch Doppelfilter (IC-1 + IC-3) begrenzt;
   (c) stiller Rückfall auf „ungepinnt" — **durch D7/IC-5 ausgeschlossen** (auch für die
   Eval-Kopie, RVW2-1);
   (d) transiente Schreibprobe von `gettempdir()` im Sink bzw. im Kandidatenverzeichnis —
   dokumentiert (IC-1), Probe liegt im sanktionierten Sink bzw. im System-Temp;
   (e) Fehlklassifikation als „Pin", obwohl ein echter In-Repo-Temp-Root vorliegt — nur bei
   exakter Sink-Gleichheit möglich, in D3 bewusst akzeptiert und begründet;
   (f) Identitätsprüfung per `mode` allein fälschbar — durch `pid`-Vergleich (IC-10) ersetzt,
   `mode` nur noch Fallback;
   **(g) falscher Erfolg über 401 (RVW2-2/RVW3-1) — verbleibendes Restrisiko:** Ein
   Fremdprozess, der `/api/health` sofort mit 401 beantwortet, könnte den Start als „gesund"
   erscheinen lassen, während unser Kind erst danach (oder nach dem Fenster) am Bind
   scheitert. **Deterministisch abgefangen** wird nur der Fall „Port bei der Pre-Flight-Probe
   bereits belegt" (IC-12 ⇒ Exit 1 ohne Spawn). **Heuristisch begrenzt** wird der Fall
   „Portinhaber antwortet nur kurz / Kind exit't innerhalb von `START_CONFIRM_GRACE`"
   (IC-7). **Nicht ausgeschlossen** bleibt: der Port wird **zwischen** Probe und Kind-Bind
   von einem Fremdprozess übernommen und die Kind-Pre-Bind-Phase ist länger als das Fenster
   — dann kann eine Erfolgsmeldung entstehen, die das Kind nicht einlöst (R11/R16).
   Die frühere Aussage „dadurch ausgeschlossen" ist gestrichen;
   **(h) Offenlegung des Projektpfads über `/api/health`** — **vermieden**, weil `root`
   nicht Teil der Antwort ist (RVW2-10); `pid` allein ist kein Pfad und kein Credential;
   **(i) Nebenwirkung der Pre-Flight-Probe:** Der Elternprozess hält den Port für
   Bruchteile einer Millisekunde und schließt ihn sofort; ein konkurrierender Start desselben
   Ports kann in diesem Fenster scheitern. Wirkung: Verfügbarkeit, kein Vertraulichkeits-
   oder Integritätsverlust; der konkurrierende Start scheitert mit `EADDRINUSE` an seiner
   eigenen Probe — sichtbar, nicht still.
3. **Was wird dagegen getan?** D6 (kein Token, kein Proxy, kein Redirect), **IC-12**
   (deterministische Bind-Probe vor dem Spawn), IC-7 (Bestätigungsfenster + `poll()`, als
   Heuristik ausgewiesen), IC-10 (`pid`-Vergleich), D7/IC-5 (lauter Abbruch statt stiller
   Unpin), IC-1 (read-only, Sink-/Root-Filter), D3 (exakter Vergleich), R10–R15
   (Restrisiken benannt).
4. **Konsequenzen.** Ein Token-Leak ist ausgeschlossen, weil der Token den Prozess nicht
   verlässt. Ein ungepinnter Kindprozess ist ausgeschlossen, weil der Start bei fehlbarem
   Pin abgebrochen wird. Ein **dauerhaft** belegter Port führt zu Exit 1 ohne Spawn. Rest:
   Ein lokaler Angreifer, der den Port **nach** der Probe übernimmt, kann einen falschen
   Erfolg erzeugen, wenn das Kind länger als `START_CONFIRM_GRACE` vor dem Bind braucht —
   das ist eine Verfügbarkeits-/Integritätswirkung auf die **Startmeldung**, keine
   Vertraulichkeitswirkung: der Token bleibt ungesendet, und der Angreifer erhält keinen
   Zugriff auf das Admin-API, das er nicht schon über den Port hätte.

---

## Teststrategie

### Anknüpfung an bestehende Dateien (VERIFIED)

| Datei | Nutzung |
|---|---|
| `tests/test_tmp_sink_output_dirs.py` | Resolver-Ebene (`resolve_tmp_paths`, `resolve_pytest_basetemp`, `tmp_env`); enthält bereits `test_pytest_basetemp_rejects_temp_root_inside_project` (`:389-397`) und System-Temp-Fälle (`:369-378`) |
| `tests/test_tmp_paths_builder.py` | Validator-Ebene (`_validate_repo_containment`, `build_variables`), Exception-Matrix (`:245-305`) |
| `tests/test_repo_containment_validate.py` | `load_config`/Validator über `_validate`-Helfer (`:332-343`) |
| `tests/test_tmp_sink_path_hardening.py` | #1136-Präzedenz (`:218-222`) und die heute grüne Lücke `test_config_load_with_tmpdir_in_sink` (`:246-255`, kein Exception-Block ⇒ Validator prüft nicht) |
| `tests/test_admin_server.py` | lädt `admin-server.py` per `importlib` (`:41-51`), mockt `admin_server.subprocess` (`:1087-1093`) |
| `tests/test_eval_baseline_schema.py` | Eval-Aufrufpfad: `call_provider`-Signatur/Env (`:399-435`), `run_class`-Monkeypatch-Muster (`:285-310`, `:331-366`) — Anker für U4-26c/d |
| `tests/conftest.py` | `effective_basetemp`/`basetemp_inside_repo` (`:45-59`) — Verbraucher, unverändert (RVW-5) |
| `tests/test_tmp_sink_env_coverage.py` | statischer Guard: jeder `subprocess`-Start ist gepinnt oder allowlistet (**muss grün bleiben**) |
| `tests/timeouts.py` | `SYNC_VALIDATE_TIMEOUT` für den Subprozess-Integrationstest |
| `tests/test_sharkord_service_name_migration.py:47` | Muster für `sync.py --validate` als Subprozess |

### Testkonvention (RVW-14, verbindlich)

- **Pin-Fälle** werden **env-basiert** modelliert: `monkeypatch.setenv` für `TMPDIR` (und
  `TEMP`/`TMP`, soweit plattformrelevant) **plus** `tempfile.tempdir = None`, damit
  `gettempdir()` den Env-Wert liefert. Plattform-Notiz: Auf Linux wirkt nur `TMPDIR`;
  `TEMP`/`TMP` sind Windows-Keys — Tests, die alle drei setzen, sind portabel, Tests, die
  nur `TEMP` setzen, brauchen `skipif`.
- **`monkeypatch.setattr(tempfile, "gettempdir", …)`** bleibt ausschließlich für Fälle, die
  einen Temp-Root **ohne** Env-Bezug modellieren (z. B. „Temp-Root = Projekt-Root").
  Ein solcher Patch darf **nicht** für Pin-Fälle verwendet werden: der read-only Fallback
  würde `gettempdir()` erneut patchen und denselben Wert sehen.
- Baseline „ungepinnt" = **saubere Env** (die drei Keys nicht gesetzt, `tempfile.tempdir =
  None`): dort `resolve_tmp_paths(...).pytest_basetemp` ermitteln, **dann** pinnen und
  vergleichen. Kein Vergleich gegen einen echten Custom-`TMPDIR` (der wird bewusst
  verdeckt, RVW-4).

### Neue/erweiterte Tests

**U1 — Unit `system_temp_root` (neu, `tests/test_tmp_sink_system_temp_root.py`)**

1. `sink_dir=None` ⇒ identisch zu `gettempdir()`.
2. Pin-Fall (env-basiert) ⇒ Ergebnis außerhalb `root`, != Sink, ist ein existierendes
   Verzeichnis.
3. Nur `TMPDIR` gesetzt (Linux-Fall; Plattform-Notiz) ⇒ gleiches Ergebnis.
4. `gettempdir()` ≠ Sink ⇒ unverändert (kein Fallback).
5. **Keine Mutation (RVW-1/RVW2-4):** `os.environ` ist vor/nach byte-identisch (auch im
   Pin-Fall). `tempfile.tempdir` wird **ausschließlich** vom Stdlib-`gettempdir()`-Cache
   gesetzt (**set-once**): Test **primed** zuerst `tempfile.gettempdir()`, nimmt **danach**
   den Snapshot von `tempfile.tempdir` und prüft, dass `system_temp_root` ihn nicht mehr
   ändert. Ein Snapshot **vor** dem Priming ist unerfüllbar (der Cache ist dann `None` und
   wird beim ersten `gettempdir()` gefüllt) und deshalb **nicht** Teil des Kriteriums;
   die Ausnahme trägt R10.
6. **Parallelität (RVW2-4):** 8 Threads rufen `system_temp_root` gleichzeitig; alle liefern
   dasselbe Ergebnis; `os.environ` bleibt unverändert; `tempfile.tempdir` bleibt nach dem
   Priming stabil (Snapshot im Hauptthread, nach Priming).
7. **Sink-Kandidat wird übersprungen (RVW-14):** Kandidatenliste enthält den Sink (weil
   `TMPDIR` ihn nennt) ⇒ Ergebnis != Sink; kein Rekursions-/Endlosschleifenverhalten.
8. **Kein Kandidat außerhalb `root`** (alle Kandidaten künstlich in `root`) ⇒
   `TmpSinkError("tmp-sink.system-temp-exception")`.
9. **Windows-Normalisierung:** Vergleich über `os.path.normcase` (Test simuliert
   Groß-/Kleinschreibung durch Monkeypatch von `realpath`/`normcase`).

**U2 — Resolver (`tests/test_tmp_sink_output_dirs.py`, erweitern)**

10. `resolve_tmp_paths` unter Pin: **keine** `TmpSinkError`; `pytest_basetemp` liegt
    außerhalb `tmp_path`, endet auf `pytest-agent-meta`.
11. **Ergebnis-Invariante (RVW-4):** Baseline in **sauberer Env** (kein `TMPDIR`/`TEMP`/`TMP`
    gesetzt) ermitteln, dann pinnen und identisches `pytest_basetemp` erwarten. Ein
    Custom-`TMPDIR` wird in einem separaten Fall geprüft: es wird vom Pin **verdeckt**
    (Ergebnis = Plattform-Default, nicht der Custom-Wert) — das ist dokumentiertes
    Verhalten, keine Invariante.
12. Sink deaktiviert + `TMPDIR=<root>/.tmp`: `resolve_pytest_basetemp` wirft weiterhin
    `tmp-sink.system-temp-exception` (kein Fallback ohne Sink).
13. Temp-Root = Unterverzeichnis des Sinks (`<sink>/sub`) ⇒ weiterhin Fehler (D3).

**U3 — Validator (`tests/test_tmp_paths_builder.py` / `tests/test_repo_containment_validate.py`)**

14. `_validate_repo_containment` mit `gettempdir()` == Sink **und explizitem Block** ⇒
    **kein** `SystemExit` (RVW-9: nur dieser Fall prüft den Validator-Pfad).
15. `load_config(<fixture>/.meta-config/project.yaml)` unter gepinnter Env ⇒ kein
    `SystemExit`; das zurückgegebene Dict enthält `repo_containment.tmp-sink.path`.
16. **Default-Block (RVW-9):** Fehlt `system-temp-exception`, prüft der Validator den
    Temp-Root nicht — als expliziter No-op-Test dokumentiert (die Lücke
    `test_config_load_with_tmpdir_in_sink` bleibt grün und ist damit kein Regressionsnetz).
17. Bestehende Negativfälle (`:332-343`, `:284-305`) bleiben unverändert grün.

**U4 — Admin (`tests/test_admin_server.py`, neue Klassen)**

18. `_admin_start_detached`: Fake-Popen mit `poll() → 1` ⇒ `SystemExit(1)`, PID-Datei ist
    nach dem Lauf entfernt, Ausgabe enthält `failed to start` **und** den Log-Tail mit der
    tmp-sink-Zeile.
18a. **Pre-Flight-Bind-Probe blockiert den Spawn (neu, RVW3-1):** `_probe_port_bindable`
    gegen einen **im Test tatsächlich geöffneten** Loopback-Listener (Hilfs-Socket, das den
    Port hält) ⇒ `(False, "EADDRINUSE: …")`; `_admin_start_detached` mit dieser Probe ⇒
    `SystemExit(1)`, `subprocess.Popen` **nicht** aufgerufen (Gemockter zählt Aufrufe = 0),
    **keine** PID-Datei geschrieben, Meldung enthält `cannot bind` und `host:port`.
18b. **Probe-Gegenprobe:** Freier Loopback-Port ⇒ `(True, "")`; direkt danach ist der Port
    wieder belegbar (kein `TIME_WAIT`, kein Leak) — belegt durch einen zweiten, erfolgreichen
    `_probe_port_bindable`-Aufruf sowie ein `bind()` auf denselben Port.
18c. **`port == 0` (D6 Punkt 6):** `_probe_port_bindable(host, 0)` ⇒ `(True, "skipped:port-0")`,
    kein Socket-Bind.
18d. **Keine Exception nach außen:** `getaddrinfo`-Fehler (unauflösbarer Host) und
    `PermissionError` (simuliert für privilegierten Port) ⇒ `(False, …)`, kein Raise.
19. `_wait_for_admin`: lebend + Health 200 `{"status":"ok","pid":<proc.pid>}` **stabil über
    `confirm_grace`** ⇒ `(True, …)`; Timeout ⇒ `(False, "timeout")`; falsche `pid` ⇒
    `(False, "identity:pid")`; falscher `mode` (ohne `pid`-Feld) ⇒ `(False, "identity:mode")`;
    `poll() → 0` ⇒ `(False, "exited:0")`; **Token konfiguriert + HTTP 401 stabil** ⇒
    `(True, …)`. Jeweils `timeout=0.2`, `confirm_grace=0.05`.
19a. **401 als Einzelereignis ist kein Erfolg (RVW2-2):** Fake-Proc liefert 401 für ~0,1 s
    und danach `poll() → 0` (Bind-Fehler, Kind exit't **innerhalb** des Fensters) ⇒
    `(False, "exited:0")`; ein Opener, der beim ersten Treffer `(True, …)` zurückgäbe, ist
    damit ausgeschlossen. **Grenze des Tests:** Er belegt den Fall „Kind stirbt im Fenster",
    **nicht** den Fall „Fenster endet vor dem Kind-Bind" — dieser ist per Konstruktion nicht
    grün testbar (Restrisiko R11/R16, keine Zusicherung).
19b. **Fenster-Reset (RVW2-2):** 401, dann 502, dann dauerhaft 401 innerhalb von `timeout` ⇒
    Erfolg erst nach erneuter Stabilisierung über volle `confirm_grace` (bzw.
    `(False, "timeout")` bei zu kurzem `timeout`); kein Erfolg aus dem ersten Treffer.
19c. **Invariante** `START_CONFIRM_GRACE < START_VERIFY_TIMEOUT` (Modul-Konstanten).
20. **Kein Token-Versand (RVW-6):** Der gemockte Opener erhält eine `Request` **ohne**
    `Authorization`-Header — auch wenn ein Token konfiguriert ist.
21. **Kein Proxy/Redirect (RVW-7):** Mit `http_proxy=http://127.0.0.1:9` im Env geht die
    Probe direkt an den Zielport (gemockter Opener prüft die Handler-Konfiguration); eine
    302-Antwort wird nicht verfolgt, sondern als `health:302` gewertet.
22. **PID-Fenster (RVW-8):** Während der Verifikation existiert die PID-Datei (Hook im
    Fake-`_wait_for_admin` liest sie); nach Fehlschlag ist sie entfernt.
23. `restart`: `_admin_stop` + `_admin_start_detached` mit totem Kind ⇒ Exit 1, keine
    Erfolgsmeldung.
24. `_is_pid_running`: POSIX-Zombie (Kind beendet, nicht `wait()`ed) ⇒ `False`
    (`skipif: win32 oder kein /proc`).
25. `VizManager._start`: Fake-Popen tot ⇒ `False`, PID-Datei entfernt.
26. **Pin-Policy Kopie 1 (D7/IC-5a):** `admin-server.py::_tmp_sink_env` in einem gepinnten
    Prozess mit gültiger Config ⇒ kein `SystemExit`, Rückgabe enthält `TMPDIR=<sink>`; mit
    **defekter** Config (`repo_containment: "x"`) ⇒ `TmpSinkError("tmp-sink.pin-unavailable")`;
    mit fehlender Config-Datei ⇒ `None`; mit deaktiviertem Sink ⇒ `None`.
26a. **Kopie 2 (RVW2-6):** `consistency-check.py::_tmp_sink_env` per `importlib` geladen
    (Muster `test_admin_server.py:41-51`): gültige Config ⇒ Pin-Dict; defekte Config ⇒
    `TmpSinkError("tmp-sink.pin-unavailable")`; fehlende Config ⇒ `None`.
26b. **Kopie 3 (RVW2-6):** `lib.cli_commands::_admin_tmp_env` analog; zusätzlich
    `_admin_tmp_env_or_exit` ⇒ bei `TmpSinkError` `SystemExit(2)` und stderr-Zeile
    `error: tmp-sink.pin-unavailable: …`.
26c. **Kopie 4 (RVW2-6/RVW3-4):** `run_role_routing_eval.py::_tmp_sink_env` per
    `importlib`: gültige Config ⇒ `dict` mit `TMPDIR=<sink>`; defekte Config ⇒ `TmpSinkError`
    (`tmp-sink.pin-unavailable`) — **nie** Rückgabe des `base`-Envs; fehlende Config und
    deaktivierter Sink ⇒ Rückgabe ist **inhaltlich gleich** dem übergebenen `base`-Env
    (gleicher Key-Set, gleiche Werte; **nicht** `assert result is base` — der Bestand
    kopiert, `:705`), nie `None`.
26d. **Eval-Abbruch (RVW2-1):** `runner.run_class(...)` mit gepatchtem
    `_tmp_sink_env`, das `TmpSinkError` wirft, und `call_provider` als „verboten" gepatcht
    ⇒ `TmpSinkError` propagiert, **kein** `call_provider`-Aufruf; `runner.main([...])`
    liefert `2` mit stderr-Zeile `error: tmp-sink.pin-unavailable: …` und schreibt **keine**
    Baseline-Datei. Zusätzlich: direkt geworfenes `TmpSinkError` in `call_provider` wird in
    `run_class` **nicht** als Miss verbucht (`except TmpSinkError: raise`).
26e. **Token-Quelle (RVW2-3):** `monkeypatch.setenv("ADMIN_UI_TOKEN", "x")` ⇒
    `_admin_start_detached` ermittelt `token_configured=True`, obwohl `args.admin_token`
    `None` ist; mit `admin-ui.token-file` in der Fixture ebenfalls `True`; ohne jede
    Token-Quelle `False`. Der gemockte Opener sieht weiterhin **keinen**
    `Authorization`-Header.
27. **Kind-Boot (AC-1189-24b):** `AdminServer.__init__` unter gepinnter Env (Fixture mit
    gültigem `.meta-config/project.yaml`, `port=0` oder gemockter
    `_DaemonThreadingHTTPServer`, damit kein Port belegt wird) liefert eine Version und wirft
    kein `SystemExit`; dito `viz_manager.start_all()` (mit gemocktem `_start`).
27a. **Health-Payload (AC-1189-27/RVW2-10):** `_route_get_health` liefert `status`, `version`,
    `mode` und zusätzlich **`pid` == `os.getpid()`**; der Schlüssel `root` fehlt. Statuscode
    und Routenverhalten unverändert (bestehender Health-Test bleibt grün).

**I1 — Integration `sync.py --validate` unter Pin**
(`tests/test_tmp_sink_pin_integration.py`, neu)

28. Subprozess `[sys.executable, scripts/sync.py, "--validate"]` mit
    `TMPDIR=TEMP=TMP=<repo>/.tmp`, Timeout `tests.timeouts.SYNC_VALIDATE_TIMEOUT`,
    `assert rc == 0` und `"tmp-sink.system-temp-exception" not in stdout+stderr`.
    Zusätzlich als schnelle Variante: `-c "from lib.config import load_config; load_config(…)"`
    mit derselben Env (rc 0) — fängt den Boot-Abbruch ohne die volle Consistency-Suite.

**I2 — Dry-run-Pfad**

29. `SyncExecutor`-äquivalenter Aufruf (`sync.py --dry-run --validate`) mit gepinnter Env
    endet rc 0 und enthält keine Exception (Abdeckung von „Dry-run im gepinnten Kontext").

**Guard**

30. `tests/test_tmp_sink_env_coverage.py` bleibt grün **ohne** neue Allowlist-Einträge
    (die Änderung fügt keinen `subprocess`-Start hinzu; die Health-Probe nutzt
    `urllib.request`, die Bind-Probe ein rohes `socket` — beides kein `subprocess`).
31. **Docstring-Guard (RVW3-3, neuer Grep im Plan-Schritt):** Die drei Helfer-Docstrings
    (`admin-server.py:315-320`, `consistency-check.py:77-81`, `cli_commands.py:193-196`)
    enthalten **nicht** mehr die widerlegten Zusagen (`keeps operating with the inherited
    env`, `never raises`, `never fails because of it`) und nennen stattdessen
    `tmp-sink.pin-unavailable`. Prüfbar als Text-/Grep-Assertion; kein Verhaltens-Test.

---

## Acceptance Criteria

Jedes Kriterium ist prüfbar; „gepinnt" heißt `TMPDIR` (und, wo plattformrelevant, `TEMP`/`TMP`)
zeigen auf `realpath(<root>/<sink>)`.

| ID | Kriterium |
|---|---|
| AC-1189-01 | `lib.repo_containment.system_temp_root(project_root, sink_dir)` existiert mit IC-1-Signatur; bei `sink_dir=None` oder `gettempdir() != sink` ist das Ergebnis identisch zu `tempfile.gettempdir()`. |
| AC-1189-02 | Ist `gettempdir()` (realpath, normcase) exakt der Sink, liefert `system_temp_root` einen Pfad **außerhalb** `root`, **ungleich** dem Sink und mit `os.path.isdir == True`; kein Kandidat, der erneut dem Sink entspricht, wird zurückgegeben. |
| AC-1189-03 | `resolve_tmp_paths(root, config)` wirft unter Pin **keine** `TmpSinkError`; `pytest_basetemp` liegt außerhalb `root` und endet auf `pytest-agent-meta`. |
| AC-1189-04 | **Baseline-Invariante (RVW-4):** `pytest_basetemp` unter Pin ist identisch mit dem Wert, der in **derselben Env ohne `TMPDIR`/`TEMP`/`TMP`** ermittelt wurde; `relative`, `absolute`, `enabled`, `env` sind unter Pin und ungepinnt identisch. Ein Custom-`TMPDIR` des Aufrufers wird bewusst verdeckt (nicht Teil der Invariante). |
| AC-1189-05 | `load_config(<fixture>/.meta-config/project.yaml)` mit **explizitem** `system-temp-exception`-Block läuft unter Pin ohne `SystemExit(1)` durch und liefert das Config-Dict. (Default-Block ist bewusst **nicht** Teil dieses Kriteriums — RVW-9.) |
| AC-1189-06 | Ein echter In-Repo-Temp-Root ≠ Sink (z. B. `<root>/system-temp`) führt weiterhin zu Exit 1 mit der inhaltlich unveränderten Meldung `… platform temp root … is inside the project root — the exception cannot take effect.` und enthält den Repair-Hinweis („stale framework pin … new shell … sync.py"). |
| AC-1189-07 | Bei **deaktiviertem** Sink und `TMPDIR=<root>/.tmp` bleibt es bei Exit 1 (kein Fallback ohne Sink). |
| AC-1189-08 | Ein Temp-Root, der nur ein **Unterverzeichnis** des Sinks ist, gilt nicht als Pin ⇒ Exit 1. |
| AC-1189-09 | `build_variables`/`_build_orch_variables` rendert unter Pin dieselben `PYTEST_BASETEMP`- und `TEST_COMMANDS`-Werte wie in der Baseline (byte-identisch; Goldens unverändert). |
| AC-1189-10 | Ist unter Pin kein Kandidat außerhalb `root` bestimmbar **oder** wirft `tempfile.gettempdir()` (`OSError`), bricht der Lauf **laut** mit `tmp-sink.system-temp-exception` ab (kein stiller Sink-Wechsel, kein ungepinntes Kind). |
| AC-1189-11 | **Keine Mutation (RVW-1/RVW2-4):** `system_temp_root` lässt `os.environ` **byte-identisch** (Vergleich vor/nach, auch im Pin-Fall) und legt **keine persistenten** Artefakte an; die einzige transiente Schreibprobe stammt aus dem Stdlib-`gettempdir()` und liegt im Sink bzw. im System-Temp. `tempfile.tempdir` wird **ausschließlich** vom Stdlib-**Set-once**-Cache gesetzt: Snapshot **nach** Priming von `tempfile.gettempdir()`, danach darf `system_temp_root` den Wert nicht mehr ändern (ein Snapshot vor dem Priming ist kein Kriterium; R10 trägt die Ausnahme). |
| AC-1189-12 | `TMPDIR=<root>/.tmp python3 scripts/sync.py --validate` endet mit Exit 0 und enthält die Meldung `tmp-sink.system-temp-exception` **nicht** (Reproduktion aus #1189). |
| AC-1189-13 | Ein `sync.py --dry-run --validate`-Subprozess mit gepinnter Env endet Exit 0 und enthält keine tmp-sink-Exception (Dry-run im gepinnten Kontext). |
| AC-1189-14 | `admin-server.py start` bei sofort sterbendem Kind: Exit 1, Meldung enthält `failed to start` und den Log-Tail (inkl. tmp-sink-Exception-Zeile), PID-Datei ist nach dem Lauf entfernt. **Stream (RVW3-5):** die Lifecycle-Zeilen gehen auf **stdout** (Bestandsmuster `:6049-6051`, `print` ohne `file=`); ein Test darf sie **nicht** auf stderr erwarten. |
| AC-1189-15 | `admin-server.py start` bei laufendem, gesundem Server **ohne** Token: Health 200 mit `pid == proc.pid` (bzw. passendem `mode`) ⇒ Exit 0, PID-Datei vorhanden, URL-Meldung. |
| AC-1189-16 | `admin-server.py start`, Kind lebt, Health antwortet bis zur Deadline nicht: Exit 1, Kind beendet, PID-Datei entfernt. |
| AC-1189-17 | **Kein falscher Erfolg — deterministischer Fall (RVW3-1):** Ist `(--host, --port)` bei der Pre-Flight-Bind-Probe **belegt** (`EADDRINUSE`) oder aus anderem Grund nicht bindbar, endet `start` mit **Exit 1**, **ohne** Kindprozess (`Popen` nicht aufgerufen), **ohne** PID-Datei; die Meldung nennt `host:port` und die `errno`-Ursache. `port == 0` ist von der Probe ausgenommen und kein Fehlerfall. |
| AC-1189-17a | **Kein falscher Erfolg — Identität ohne Token (RVW3-1, nur ohne Token prüfbar):** Antwortet auf dem Port ein Fremdprozess mit Health-200, dessen `pid` nicht `proc.pid` ist (bzw. dessen `mode` nicht `detect_mode(root)` ist, wenn `pid` fehlt), gilt der Start als Fehlschlag (Exit 1). |
| AC-1189-17b | **Kein falscher Erfolg — heuristischer Fall (RVW3-1, ausdrücklich Heuristik):** Bei Token-Setup genügt ein **einzelnes** 401 **nicht**: ein 401, das nicht `START_CONFIRM_GRACE` lang stabil bleibt, oder ein Kind, das am Fensterende nicht mehr lebt (`poll() != None`), führt zu Exit 1. **Nicht** zugesichert (Restrisiko R11/R16): übernimmt ein Fremdprozess den Port **zwischen** Probe und Kind-Bind und ist die Kind-Pre-Bind-Phase länger als `START_CONFIRM_GRACE`, kann eine Erfolgsmeldung entstehen, die das Kind nicht einlöst. Dieses Kriterium ist deshalb **heuristisch**, nicht deterministisch. |
| AC-1189-18 | `restart` kann keinen Erfolg mehr melden, wenn das neu gestartete Kind **innerhalb des Bestätigungsfensters** tot ist (Exit 1). Für `restart` gilt zusätzlich die Pre-Flight-Probe aus AC-1189-17 (kein Spawn bei belegtem Port). Das heuristische Restfenster aus AC-1189-17b gilt sinngemäß auch hier. |
| AC-1189-19 | `_is_pid_running` liefert auf POSIX für einen Zombie `False` (sofern `/proc` lesbar), sonst unverändertes Verhalten; Windows-Zweig unverändert. |
| AC-1189-20 | `VizManager._start` erkennt ein sofort sterbendes Viz-/MCP-Kind über `poll()` und entfernt die PID-Datei; das Wartefenster ist `VIZ_START_GRACE` (Default 1,5 s), **nicht** `START_VERIFY_TIMEOUT` (RVW2-7). |
| AC-1189-21 | Alle bestehenden Tests der genannten Dateien bleiben grün, insbesondere `test_system_temp_exception_rejects_temp_root_inside_project`, `test_pytest_basetemp_rejects_temp_root_inside_project`, `test_config_load_with_tmpdir_in_sink` und `test_tmp_sink_env_coverage.py`. |
| AC-1189-22 | `config/project-config.schema.json` und `.meta-config/project.yaml` sind unverändert; es gibt kein neues Config-Feld und keinen neuen Env-Key. |
| AC-1189-23 | Der **gerenderte** Basetemp (`--basetemp={{PYTEST_BASETEMP}}`) liegt außerhalb `root` (§5.5), auch wenn der rendernde Prozess gepinnt ist. Ein pytest-Lauf **ohne** `--basetemp` ist ausdrücklich nicht gedeckt (Grenze, RVW-5). |
| AC-1189-24a | **Eltern-CLI:** `_admin_start_detached` überlebt eine gepinnte Env ohne `SystemExit` aus `_tmp_sink_env` und erreicht bei freiem Port (AC-1189-17) den `Popen`-Aufruf. |
| AC-1189-24b | **Kind-Boot:** `AdminServer.__init__` (inkl. `_load_admin_ui_config` und `_read_version`) liefert unter gepinnter Env eine Version und wirft kein `SystemExit`; `viz_manager.start_all()` ebenso. |
| AC-1189-24c | **Validerung:** `sync.py --validate` unter Pin endet Exit 0 (bestehender Inhalt, = AC-1189-12). |
| AC-1189-25 | **Pin-Policy (RVW-2/RVW2-1/RVW2-5):** Ein `TmpSinkError` aus der Pin-Auflösung führt bei **allen vier** Helfern zum sichtbaren Abbruch **ohne** Kindprozess (kein `env=None`-Spawn, keine ungepinnte Eval). Je Kopie gilt die Rückgabe aus IC-5a (Kopien 1–3 `None`, Kopie 4 das `base`-Env im „kein Pin"-Fall). Code ist `tmp-sink.pin-unavailable`; Meldung enthält den ursprünglichen Grund und den Hinweis `python scripts/sync.py --validate`; Exit-Code je Aufrufer nach IC-5b (`start`: 1, Skripte/CLI: 2, API: Ergebnisfeld statt Exception). |
| AC-1189-26 | **Pin-Policy-Ausnahmen:** Fehlende Config-Datei und deaktivierter Sink liefern bei den Kopien 1–3 `None` und bei Kopie 4 ein **inhaltlich gleiches** `base`-Env (gleicher Key-Set, gleiche Werte — **nicht** dasselbe Objekt, der Bestand kopiert `:705`, RVW3-4); der `ImportError`-Fall gilt **nur** für die Kopien 1–3 (`None` + genau **eine** Warnzeile auf stderr mit dem in D7 Punkt 3 festgeschriebenen Wortlaut — der Text ist **neu**, RVW3-2) — bei Kopie 4 ist er nicht anwendbar (Modul-Level-Importe, IC-5a). |
| AC-1189-27 | `/api/health` enthält additiv **`pid`** und **kein** `root`-Feld (RVW2-10); `status`, `version`, `mode` und alle Statuscodes bleiben unverändert. |
| AC-1189-28 | **Kein Token-Versand (RVW-6):** Die Health-Probe sendet unter keinen Umständen einen `Authorization`-Header; mit konfiguriertem Token gilt HTTP 401 **nach bestandenem Bestätigungsfenster** als Erfolgskriterium. |
| AC-1189-29 | **Kein Proxy/Redirect (RVW-7):** Ein gesetztes `http_proxy`/`HTTP_PROXY` ändert das Probeziel nicht; 3xx-Antworten werden nicht verfolgt, sondern als Fehlschlag gewertet. |
| AC-1189-30 | **Thread-Tauglichkeit (RVW-1/RVW2-4):** 8 parallele Threads rufen `system_temp_root` auf; alle erhalten dasselbe Ergebnis, `os.environ` bleibt unverändert, und `tempfile.tempdir` bleibt **nach** dem Priming stabil (Stdlib-Set-once-Cache; kein Snapshot-vor-Priming-Kriterium). |
| AC-1189-31 | **PID-Fenster (RVW-8):** Während der Verifikation existiert die PID-Datei (Status/Stop finden sie); bei Fehlschlag ist sie entfernt. |
| AC-1189-32 | **Dokumentationspflicht (D8):** §5.5 und Option C der Vorgänger-Spec enthalten den Verweis auf diese Spec; der Docstring von `tmp_sink_location_error` nennt `system_temp_root` als zweiten Konsumenten; der `TmpSinkError`-Docstring (`repo_containment.py:566-568`) nennt `tmp-sink.pin-unavailable` und `tmp-sink.system-temp-exception` (RVW2-5). **Zusätzlich (RVW3-3):** die drei Helfer-Docstrings `admin-server.py:315-320`, `consistency-check.py:77-81`, `cli_commands.py:193-196` enthalten **nicht** mehr die widerlegten Zusagen (`keeps operating with the inherited env`, `never raises`, `never fails because of it`) und nennen stattdessen `tmp-sink.pin-unavailable` (D8 Punkt 4). (Prüfbar per Grep/Doku-Test im Plan-Schritt, Test 31.) |
| AC-1189-33 | **Token-Erkennung (RVW2-3):** `token_configured` wird aus `_load_admin_ui_config(root)` + `_resolve_admin_token(cli_token=args.admin_token, config_token=<cfg>, config_token_file=<cfg>)` bestimmt (Priorität CLI > `ADMIN_UI_TOKEN` > `admin-ui.token` > `admin-ui.token-file`, identisch zu `AdminServer.__init__`). Mit `ADMIN_UI_TOKEN` **oder** `admin-ui.token`/`token-file` erwartet `start` 401 als Erfolg (kein Fehlschlag); ohne jede Token-Quelle erwartet es 200. |
| AC-1189-34 | **Bestätigungsfenster — Heuristik (RVW2-2/RVW3-1):** Ein 401, das der Portinhaber nur kurzzeitig liefert (Kind scheitert **innerhalb des Fensters** am Bind und exit't), führt zu Exit 1; Erfolg nur bei `START_CONFIRM_GRACE`-stabilem Kriterium **und** `proc.poll() is None` am Fensterende. `START_CONFIRM_GRACE` (1,0 s) < `START_VERIFY_TIMEOUT` (5,0 s), beide als Modul-Konstanten überschreibbar; ein zum Deadline-Zeitpunkt laufendes Fenster darf um höchstens `confirm_grace` über die Deadline hinaus abgeschlossen werden. **Klarstellung:** Das Kriterium sichert **nicht** zu, dass das Kind den Port gebunden hat; es ist eine Heuristik über den Kind-Lebenslauf. Die deterministische Aussage liefert AC-1189-17. |

---

## Risiken

| # | Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|---|
| R1 | Nachbau der Stdlib-Kandidatenreihenfolge driftet mit einer künftigen Python-Version | Fallback wählt einen unerwarteten Root (aber nie den Sink und nie den Repo-Root) | Primär `tempfile._candidate_tempdir_list()` (guarded); Nachbau nur als Fallback; U1-8 testet „kein Kandidat"; Golden-Test AC-1189-04 erkennt Drift |
| R2 | Kein Kandidat außerhalb `root` | Exception kann nicht wirksam werden | lauter Abbruch mit `tmp-sink.system-temp-exception` (AC-1189-10), kein stiller Wechsel |
| R3 | Manuell gesetzter `TMPDIR=<sink>` wird als Pin akzeptiert | Exception-Prüfung entfällt in genau diesem Fall | gewollt (D1/D3); der Basetemp bleibt trotzdem außerhalb (D2) |
| R4 | Health-Probe trifft einen Fremdprozess | falscher Erfolg | **Pre-Flight-Bind-Probe** (IC-12) für den Fall „Port dauerhaft belegt"; `pid`-Vergleich (IC-10/AC-1189-17a); `poll()` erkennt das sterbende Kind; 401-Regel **nur mit Bestätigungsfenster** (Heuristik, R11/R16) |
| R5 | Health-Probe scheitert an `0.0.0.0`/`::` | Start meldet fälschlich Fehlschlag | Wildcard-Bind → Loopback-Probe; Deadline 5 s (konfigurierbar) |
| R6 | Deadline zu kurz auf langsamen Maschinen/CI | falscher Fehlschlag | `START_VERIFY_TIMEOUT` als Modul-Konstante (Tests klein, Produktion 5 s); `START_CONFIRM_GRACE` bleibt darunter (1,0 s); Log-Tail nennt die Ursache |
| R7 | Windows-Pfadvergleich (Case/Separatoren) | Pin nicht erkannt ⇒ alter Fehler | `normcase` + `realpath` (IC-1); eigener Test (U1-9) |
| R8 | `tempfile._candidate_tempdir_list` ist privat | Verhalten könnte sich ändern | `getattr`-Guard + dokumentierter Nachbau + U1-Tests; kein Verhaltensverlust bei Wegfall der privaten API |
| R9 | Zombie-Guard über `/proc` ist Linux-spezifisch | macOS/BSD unverändert | Feature-Detection; ohne `/proc` bleibt das bisherige Verhalten (kein Regress) |
| R10 | Stdlib-`gettempdir()` führt beim ersten Aufruf eine Probe-Datei aus und cacht (`tempfile.tempdir`); parallele Erstaufrufe in mehreren Threads | transiente Datei im Sink/System-Temp; theoretisch doppelte Probe | Stdlib-Verhalten, dokumentiert (IC-1); unsere Funktion mutiert nichts; Probe liegt im sanktionierten Sink |
| R11 | **Restfenster der Heuristik (RVW3-1, korrigierte Beschreibung):** Nicht „der Fremdprozess bleibt >1 s gesund" ist der Mechanismus, sondern **„unser Kind hat am Fensterende noch nicht gebunden"**. Die Pre-Bind-Phase (Interpreter-Start, Modul-Importe `:40-60`, zwei `load_config`-Läufe bis `:5918`) kann `START_CONFIRM_GRACE` überschreiten (kalte CI, langsame Maschine — R6). Dann endet das Fenster mit `poll() is None` und 401-Stabilität ⇒ Erfolgsmeldung, obwohl der Bind anschließend scheitert | Falscher Erfolg im Token-Setup (Erfolgsmeldung + PID-Datei auf einem sterbenden Kind); Verfügbarkeits-/Integritätswirkung auf die **Startmeldung**, **kein** Credential- und kein Zugriffsgewinn (der Angreifer hätte den Port ohnehin) | **Stufe 1 (deterministisch):** Pre-Flight-Bind-Probe vor dem Spawn (IC-12/AC-1189-17) erkennt den dauerhaft belegten Port und bricht ohne Spawn ab. **Stufe 2 (Heuristik):** `START_CONFIRM_GRACE` + `poll()`-Recheck (IC-7/AC-1189-17b) fängt jeden Fehlstart **innerhalb** des Fensters. **Nicht heilbar:** das TOCTOU-Fenster zwischen Probe und Kind-Bind bleibt — ehrlich als Verfahrensgrenze ausgewiesen (D6, Threat-Model (g)), kein Token verlässt den Prozess (D6) |
| R11a | `START_CONFIRM_GRACE` ist eine **Zeitannahme** (Default 1,0 s), nicht gemessen | Auf langsamen/kalten Umgebungen zu kurz ⇒ R11 greift; zu lang ⇒ späterer Fehlschlag | Wert als Modul-Konstante (Tests/CI überschreibbar); R6 benennt die Kalibrierungsgrenze; die deterministische Stufe 1 (IC-12) trägt den häufigsten Realfall unabhängig von dieser Annahme |
| R12 | `401` als Erfolg könnte einen halbfertigen Server als „gesund" melden | falscher Erfolg in seltenem Fall | 401 kommt erst nach vollständigem `__init__` (Handler/Token gesetzt); zusätzlich Bestätigungsfenster und Log-Tail bei Fehlschlag |
| R13 | **Stale Pin nach Sink-Pfadwechsel** (RVW-12): Shell exportiert alten `<root>/.tmp`-Pin, Config sagt `scratch` | harter Abbruch bei jedem CLI-Start, Meldung nennt den Pin nicht als Ursache | Repair-Hinweis in der Meldung (IC-4/AC-1189-06); neue Shell oder erneuter Sync |
| R14 | `mode` allein ist als Identitätsmerkmal fälschbar (RVW-11) | falscher Erfolg | `pid`-Vergleich ist primär; `mode` nur Fallback; R11/R4 |
| R15 | `START_CONFIRM_GRACE` verlängert den Erfolgspfad um ~1 s; die Pre-Flight-Probe fügt einen Bind/Schließen-Zyklus hinzu (< 1 ms) | späterer Erfolgszeitpunkt (kein Fehlschlag) | Fenster bleibt klein (1,0 s) und ist eine Modul-Konstante (Tests/CI überschreibbar); ein laufendes Fenster darf die Deadline um höchstens `confirm_grace` überschreiten (IC-7 „Deadline-Semantik"); die Probe ist synchron und ohne Netzwerk-IO |
| R16 | **TOCTOU zwischen Pre-Flight-Probe und Kind-Bind (RVW3-1):** die Probe schließt den Socket vor dem Spawn; ein Fremdprozess kann den Port in diesem Fenster übernehmen | Wenn zusätzlich die Kind-Pre-Bind-Phase > `START_CONFIRM_GRACE` ist, falscher Erfolg (= R11) | Keine vollständige Heilung möglich (der Port-Bind gehört dem Kind); bewusst als **Heuristik-Restrisiko** akzeptiert und dokumentiert (D6, IC-12, R11, Threat-Model (g)); der häufigste Fall — Port war schon vor dem Start belegt — ist deterministisch abgedeckt |

---

## Offene Fragen

**Keine.** Alle Festlegungen sind in D1–D8 entschieden und je mit verworfener Alternative
bzw. Belegstelle dokumentiert (RVW-16):

| Ehemals offen | Status |
|---|---|
| OQ-1 Pfadvergleich vs. Marker-Env | **entschieden** → D1/ADR-1189-03 (Präzedenz #1136: `tmp_sink_location_error`) |
| OQ-2 Health-Pflicht vs. Best-Effort | **entschieden** → D6/IC-7 (Pflicht; aber **ohne** Token-Versand) |
| OQ-3 VizManager-Verifikation | **entschieden** → IC-9/AC-1189-20 (poll-basiert, kein HTTP) |
| OQ-4 §5.5-Satz | **verbindliche Dokumentationspflicht** → D8/AC-1189-32 (§5.5 **und** Option C der Vorgänger-Spec, plus drei Helfer-Docstrings, D8 Punkt 4) |
| OQ-5 **401-Identität vs. Beweis** (neu, RVW3-1) | **entschieden → Option B** (D6/ADR-1189-08): deterministische Pre-Flight-Bind-Probe vor dem Spawn (IC-12) + Bestätigungsfenster ausdrücklich als Heuristik. **Option A** (`/api/health` token-frei) verworfen: unauth­entifizierte Versions-/Modus-/PID-Enumeration bei Wildcard-Bind widerspricht der Token-Gate-Absicht; das TOCTOU-Restfenster bleibt benannt (R11/R16) |

Offen ist ausschließlich die **Freigabe durch den User** (`Status: APPROVED (Datum)`).

---

## Umsetzungsschnitt (Hinweis für den Plan; RVW-15)

Kein Split dieser Spec, aber zwei getrennt revertierbare Commit-Einheiten:

1. **Semantik zuerst:** `repo_containment.system_temp_root`/`resolve_sink_absolute`,
   `tmp_paths.resolve_pytest_basetemp`, `config._validate_repo_containment`, Pin-Policy
   (IC-5a/IC-5b, D7 — inklusive Eval-Abbruch und Exit-Code-Mapping) und die zugehörigen
   Unit-/Integrationstests. Danach ist `sync.py --validate` unter Pin grün, aber `start`
   kann weiterhin falschen Erfolg melden.
2. **Start-Robustheit danach:** `_probe_port_bindable` + Aufruf in `_admin_start_detached`
   (IC-12, Stufe 1), `_wait_for_admin` (inkl. `START_CONFIRM_GRACE`, Stufe 2/heuristisch),
   `_admin_start_detached` (inkl. `token_configured`-Quelle), IC-10 (`pid`),
   `_is_pid_running`, `VizManager._start` (`VIZ_START_GRACE`), D8-Docstrings. Ohne Einheit 1
   testbar (gemockte Prozesse/Health), aber der End-to-End-Nachweis von AC-1189-14 (echte
   tmp-sink-Zeile im Log-Tail) braucht beide. **Reihenfolge innerhalb der Einheit:** erst die
   Probe (deterministisch, ohne Netzwerk), dann die Fenster-Heuristik — so ist der
   Hauptgewinn („Port belegt ⇒ kein Spawn") unabhängig von jeder Zeitannahme.

---

## Trace-Anker

```text
spec-id: SPEC-1189-tmp-sink-pin-vs-system-temp
Issue: #1189
Review: docs/specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-review.md
Re-Review Rev 2: docs/specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-rereview.md
Re-Review Rev 3: docs/specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-rereview2.md
Vorgänger: SPEC-tmp-sink-injection (bleibt gültig; D8 ergänzt dort einen Verweis)
Dokumentationspflicht: D8 (§5.5 + Option C der Vorgänger-Spec + drei Helfer-Docstrings)
Plan: <wird nach Approval erzeugt>
```
