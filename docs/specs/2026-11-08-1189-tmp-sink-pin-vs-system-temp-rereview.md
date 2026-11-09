# Re-Review — Spec `SPEC-1189-tmp-sink-pin-vs-system-temp` (Issue #1189), Revision 2

> **Gegenstand:** `docs/specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-spec.md`,
> `Revision: 2`, `Status: DRAFT (2026-11-08)`, Klasse M.
> **Vorlage:** `docs/specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-review.md`
> (CHANGES_REQUESTED, 16 Findings RVW-1…RVW-16).
> **Review-Typ:** Re-Review, beschränkt auf die in Rev 1 geänderten Abschnitte
> (IC-1, IC-2, IC-3, IC-4, IC-5, IC-7, IC-8, IC-9, IC-10, IC-11, D1–D8 inkl.
> OQ-Auflösung, ADR-1189-03/05/06/07, Risiken R1/R10–R14, AC-04/05/10/11/14/15/17/23,
> 24a/24b/24c, AC-25…32, Threat Model, Umsetzungsschnitt). Keine neuen Prüfdimensionen.
> **Datum:** 2026-11-08 · Repo `agent-meta` (Arbeitskopie, Stand wie im Auftrag `d12d4218`;
> Hash nicht selbst per `git` geprüft)
> **Prüfmethode:** Gegenlesen am Code, jede Aussage mit `datei:zeile` belegt.
> **Nicht ausgeführt:** `sync.py`, `pytest`, `git`. Kein Code, keine Implementierung,
> keine Änderung an der geprüften Spec, kein Commit.

---

## 1. Votum

**APPROVE WITH CHANGES** (entspricht `CHANGES_REQUESTED`) — **die Freigabe durch den User
kann derzeit noch nicht erfolgen.**

Die beiden Blocker aus Rev 1 sind **im Kern** adressiert, aber **nicht beide wirksam
geschlossen**:

| Rev-1-Blocker | Status in Rev 2 | Bewertung |
|---|---|---|
| **RVW-1** (Threading-Prämisse / prozessglobale Env-Mutation) | **wirksam behoben.** IC-1 wählt den Fallback read-only aus der Stdlib-Kandidatenliste, ohne `os.environ` oder `tempfile.tempdir` anzufassen; es gibt keinen Remove-/Restore-Vertrag mehr. | ✅ geschlossen (Rest = Stdlib-Cache, korrekt als R10 geführt; AC-Formulierung siehe RVW2-4) |
| **RVW-2** (`_tmp_sink_env` schluckt Fehler ⇒ stilles ungepinntes Kind) | **für 3 von 4 Kopien behoben, für die vierte doppelt gebrochen.** `run_role_routing_eval.py::_tmp_sink_env` hat einen anderen Rückgabetyp als IC-5 behauptet, und ein dort geworfenes `TmpSinkError` wird vom Aufrufer als „Case-Miss" verschluckt (RVW2-1). | ❌ **nicht wirksam geschlossen** |
| **neu: RVW2-2** | Der 401-als-Erfolg-Pfad (D6/IC-7) meldet bei belegtem Port einen falschen Erfolg — genau der Fall, den AC-1189-17 abdecken soll. | ❌ blocking |

Es bleibt damit bei **2 blocking**, **3 major**, **5 minor**, **1 info**. Der Design-
Richtungsentscheid (D1/D2/D3, §5.5-Konformität, kein Token-Versand, read-only Fallback)
ist **nicht** strittig — die Nacharbeit ist eng begrenzt und berührt keine Architektur.

**Votum-Mapping:** `CHANGES_REQUESTED` / `APPROVE WITH CHANGES` — kein `REJECT`
(keine fundamental falsche Richtung, keine unlösbare Lücke).

---

## 2. Antworten auf die sechs Prüfaufträge

### 2.1 Ist RVW-1 wirksam behoben?

**Ja.** Begründung am Code:

- **Keine Mutation mehr.** IC-1 Schritt 3 (Zeilen 442–452 der Spec) bestimmt den Fallback
  aus einer Kandidatenliste und filtert; Schritt „Keine Mutation (RVW-1)" (Zeilen 453–460)
  schließt `os.environ`- und `tempfile.tempdir`-Schreibzugriffe vertraglich aus. Gegenprobe
  am Produktivcode: `grep` über `scripts/**` findet **keine** Zuweisung an `tempfile.tempdir`
  und **keine** `os.environ[...] =`/`del os.environ`/`os.environ.update(`-Stelle. Es gibt
  also keinen verbleibenden prozessglobalen Mutationspfad im Framework.
- **Verträglich mit dem Threading-Server.** `_DaemonThreadingHTTPServer(ThreadingHTTPServer)`
  mit `daemon_threads = True` (`admin-server.py:5817-5824`), die kritischen Aufrufer in
  Request-Threads (`SyncExecutor._run` `:1352-1370`, `ConsistencyService.run_consistency_check`
  `:1744-1750`, `VizManager._start` `:640-660`) und der selbst gepinnte Server
  (`env=_tmp_sink_env(root)` `:6032`/`:6038`) sind unkritisch, weil `system_temp_root`
  ausschließlich liest. Der einzige verbleibende gemeinsame Zustand ist der Stdlib-Cache
  `tempfile.tempdir`, den `tempfile.gettempdir()` unter `_once_lock` **set-once** füllt —
  thread-sicher und in R10 benannt. Kein `RLock` nötig; die Begründung in ADR-1189-07
  (Zeile 753) trägt.
- **Restrisiko sauber geführt.** R10 (Zeile 971) nennt die transiente Schreibprobe und den
  Cache; IC-1 Schritt 1 (Zeilen 434–439) dokumentiert die Probe im sanktionierten Sink bzw.
  System-Temp. Das ist genau die von RVW-1 Punkt 3 geforderte Benennung.

Einziger Restfehler ist **nicht** die Nebenläufigkeit, sondern die Test-/AC-Formulierung
(RVW2-4).

### 2.2 Ist RVW-2 wirksam behoben?

**Nein — für die dritte Kopie ja, für die vierte nein.** D7/IC-5 sind für
`admin-server.py::_tmp_sink_env` (`:311-336`), `consistency-check.py::_tmp_sink_env`
(`:74-95`) und `cli_commands.py::_admin_tmp_env` (`:188-210`) korrekt: alle drei geben
heute `dict | None` zurück und schlucken `TmpSinkError` über `except Exception`
(`admin-server.py:334`, `consistency-check.py:93`, `cli_commands.py:208`) — die Abkehr
davon ist konsistent beschrieben.

Die vierte Kopie passt **nicht** in den Vertrag (Details RVW2-1):

- `run_role_routing_eval.py::_tmp_sink_env` (`:697`) hat die Signatur
  `(base: dict | None = None) -> dict` und gibt in **allen** Fehlerfällen das geerbte
  Env-Dict zurück (`:712-713`), nie `None`. IC-5 (Zeilen 526–545) behauptet für „alle vier
  Kopien" `None`-Rückgabe; ein `None` würde in `call_provider` sofort in
  `env[model_var] = model_id` (`:729-732`) mit `TypeError` abstürzen.
- Ein dort geworfenes `TmpSinkError` erreicht den Nutzer **nicht**: die Case-Schleife fängt
  `Exception` und verbucht den Fall als Miss (`:793-802`), nur `ProviderError` wird
  re-raised. Die Eval liefe weiter und schriebe eine Baseline aus lauter Misses — genau der
  stille Zustand, den D7 (Zeilen 366–396) ausschließen will.
- Die in IC-5 Punkt 2 geforderte `ImportError`-Behandlung ist für diese Kopie **strukturell
  unmöglich**: `load_config` und `resolve_tmp_paths` werden auf Modulebene importiert
  (`:55`, `:62`); ein Import-Fehler beendet das Modul, bevor `_tmp_sink_env` läuft.

**Zur Fehlerkennung `tmp-sink.pin-unavailable`:** formal konsistent (Format `tmp-sink.<x>`,
`TmpSinkError(code, message)`, `repo_containment.py:563-574`), aber (a) **nicht** im dort
dokumentierten Code-Set (`:566-568`), und (b) die Exit-Code-Konvention ist offen: der
Docstring sagt „Callers map it to Exit 2" (`:568`), die Hausform für `TmpSinkError` ist
`error: <code>: <message>` + Exit 2 (`cli_commands.py:1357-1359`), D7 sagt nur „Exit ≠ 0".
**Von `sync.py --validate` wird `tmp-sink.pin-unavailable` nie gemeldet** — der Code
entsteht ausschließlich in den vier Helfern; `sync --validate` ist der im Text genannte
*Reparaturhinweis* für die Ursache. Für den CLI-Pfad ist `sync.py` allerdings selbst der
Pin-Aufrufer (`cli_commands.py:575/:1732`) und hat **keinen** `TmpSinkError`-Handler
(`sync.py:804-847`) ⇒ Traceback statt Meldung (RVW2-5).

### 2.3 Sind die neuen AC (25–32) prüfbar und testbar?

| AC | Prüfbar? | Testanker | Befund |
|---|---|---|---|
| 25 | ja | `test_admin_server.py` (nur Kopie 1) | **Lücke:** „bei allen vier Helfern" ist nicht abgedeckt; U4-26 prüft nur `admin-server.py`. Die drei Skripte sind per `importlib` ladbar (Muster `test_admin_server.py:41-51`), ein Anker fehlt aber im Testplan. |
| 26 | ja, außer `ImportError` für Kopie 4 | dito | `ImportError`-Zweig dort nicht implementierbar (RVW2-1). |
| 27 | ja | `test_admin_server.py` | — |
| 28 | ja (mockbarer Opener) | `test_admin_server.py` | Negativkriterium „unter keinen Umständen" ist nur per Mock/Inspektion belegbar — als Formulierung akzeptabel. |
| 29 | ja | `test_admin_server.py` | — |
| 30 | **nein, wie formuliert** | `test_tmp_sink_system_temp_root.py` (neu) | Der Snapshot-Teil ist mit der vorgeschriebenen Testkonvention unerfüllbar (RVW2-4); der Parallelitätsteil ist testbar. |
| 31 | ja | `test_admin_server.py` (Hook im Fake-`_wait_for_admin`) | Feasibel (PID-Datei wird laut IC-8 Schritt 3 sofort geschrieben). |
| 32 | ja | Grep/Doku-Test | Prüfbar; deckt aber die `TmpSinkError`-Code-Doku nicht mit ab (RVW2-5). |

Die genannten Datei-Anker existieren und tragen: `test_tmp_sink_output_dirs.py:367-378`,
`:389-397`; `test_tmp_paths_builder.py:245-305`; `test_repo_containment_validate.py:332-343`;
`test_admin_server.py:41-51`, `:1087-1093`; `test_tmp_sink_path_hardening.py:218-222`,
`:246-255`; `tests/timeouts.py` (`SYNC_VALIDATE_TIMEOUT`). `tests/test_tmp_sink_env_coverage.py`
bleibt grün, auch wenn der Helfer-Aufruf in eine lokale Variable ausgelagert wird
(`_env_is_pinned` löst `Name`-Zuweisungen im Scope auf, `:156-172`,
`_PIN_TOKENS` `:46`) — AC-1189-30 (Guard) hält also. **Positiv:** Die bestehenden
Negativtests bleiben unter IC-3 grün, weil sie `tempfile.gettempdir` auf einen *Nicht-Sink*
patchen (`test_pytest_basetemp_rejects_temp_root_inside_project` `:389-397`).

### 2.4 Ist D2 widerspruchsfrei zu §5.5 und zur Vorgänger-Spec (Option C)?

**Ja, inhaltlich.** §5.5 Punkt 1 verlangt „Basetemp NIE im Arbeitsbaum", Punkt 5 lässt die
conftest-Warnung warning-only (`docs/concepts/repo-containment-prison-mode.md:413-433`);
Option C der Vorgänger-Spec ist „System-Temp ausschließlich für `pytest --basetemp` …
`tempfile.gettempdir()`, kein `/tmp`-Literal"
(`docs/specs/2026-10-24-tmp-sink-injection-spec.md:626-631`). D2 (Zeilen 259–293) wählt
genau das, lehnt `<sink>/pytest` mit der Ancestor-Kollision ab und erklärt die Baseline als
„dieselbe Env ohne die drei Sink-Keys". D8 (Zeilen 400–413) macht die dadurch nötige
Präzisierung der Vorgänger-Spec verbindlich — das war die offene Flanke aus RVW-13/RVW-16
und ist jetzt geschlossen. Zwei Präzisierungen ohne Verdictsrelevanz: die Baseline-Definition
weicht bewusst von einem echten Custom-`TMPDIR`-Lauf ab (in D2/AC-04 offen benannt, korrekt),
und die Begründung „Golden-Bruch" ist überzogen (RVW2-9).

### 2.5 Verbleibende Risiken (Token, 401, `mode`, Stale Pin)

| Risiko | Adressiert? | Befund |
|---|---|---|
| Token-Identität | teilweise | Kein Token-Versand ist sauber gelöst (D6, AC-28). **Aber:** `token_configured` ist nicht an `_resolve_admin_token` gebunden (RVW2-3) — mit `ADMIN_UI_TOKEN`/`admin-ui.token-file` erwartet der Elternprozess 200, bekommt 401 und meldet Fehlschlag. |
| 401 als Erfolg | **nein** | Der 401-Pfad hat kein Bestätigungsfenster; ein Fremdprozess liefert 401 sofort ⇒ falscher Erfolg (RVW2-2). R11/R12 beschreiben die Ursache, lösen sie aber nicht. |
| `mode`-Fälschbarkeit | ja | `pid` ist primär, `mode` nur Fallback (IC-7 Zeilen 576–581, R14). Akzeptabel; Restfall „fremde agent-meta-Instanz im selben Modus" ist in R4/R14 benannt. |
| Stale Pin | ja | R13 (Zeile 974) + Repair-Hinweis in IC-4 (Zeilen 511–514) und AC-1189-06. Der Hinweis erscheint genau im In-Repo-Fall, also dort, wo der Stale Pin auftritt — konsistent. (Der Hinweis ist bei echter Fehlkonfiguration leicht irreführend, aber harmlos.) |

### 2.6 Threat-Model-Kurzcheck

Die vier Fragen sind beantwortet (Zeilen 757–782), die Mitigationen sind auf die
Containment-Grenze bezogen (kein Token, kein Proxy, kein Redirect, lauter Abbruch,
read-only Resolver, exakter Pfadvergleich). Das ist eine echte Verbesserung gegenüber Rev 1.
Zwei Lücken: Frage 2 nennt den **falschen Erfolg über 401** nicht (RVW2-2), und Frage 2
analysiert das neue `root`-Feld in `/api/health` nicht (RVW2-10). Frage 4 ist ehrlich
(„Verfügbarkeits-, keine Vertraulichkeitswirkung").

### 2.7 Spec-Template-Checks (unverändert zu prüfen)

| Check | Ergebnis |
|---|---|
| Pflichtsektionen (Interface Contracts, Acceptance Criteria, Datenfluss, Problem/Ziel/Nicht-Ziele, Offene Fragen, Risiken) | **grün** |
| Trace-Anker `spec-id: SPEC-1189-tmp-sink-pin-vs-system-temp` | **grün** (Zeile 9 und 1012–1019) |
| Approval-Marker | **grün** — `Status: DRAFT`, ausdrücklich „User setzt APPROVED", konsistent zum Review-Stand |
| No-Placeholder | **grün** — kein `TODO`/`TBD`; `<sink>`/`<root>`/`<system-temp>` sind Metavariablen, `Plan: <wird nach Approval erzeugt>` ist die vorgesehene Vorwärtsreferenz |
| OQ-Tabelle | **grün** — OQ-1…OQ-4 auf „entschieden"/„verbindliche Dokumentationspflicht" reduziert (RVW-16) |

---

## 3. Findings

Legende: **blocking** = ohne Änderung nicht approbierbar ·
**major** = substanzielle Lücke, blockierend für die Umsetzung · **minor** = Verbesserung ·
**info** = Hinweis ohne Handlungszwang.

### RVW2-1 — blocking · Logik / Vollständigkeit (IC-5 gilt nicht für die vierte Kopie)

**Befund.** IC-5 (Zeilen 526–545) erklärt einen „gemeinsamen Vertrag" für **alle vier**
Pin-Helfer und verlangt `None` für die drei definierten Zustände. Für
`scripts/run_role_routing_eval.py::_tmp_sink_env` ist das dreifach falsch:

1. **Rückgabetyp.** Signatur `def _tmp_sink_env(base: dict | None = None) -> dict`
   (`:697`); der Fehler-/Disabled-Zweig gibt `env` zurück (`:709-713`), nie `None`.
   Der Aufrufer dereferenziert direkt: `env = _tmp_sink_env(os.environ.copy())` (`:729`),
   `env[model_var] = model_id` (`:732`) ⇒ `None` wäre ein `TypeError`.
2. **Fehler wird verschluckt.** Die Case-Schleife fängt `Exception` und verbucht den Fall
   als Miss, nur `ProviderError` wird re-raised (`:783-802`). Ein aus `_tmp_sink_env`
   propagierendes `TmpSinkError` führt daher **nicht** zum Abbruch, sondern zu einer Eval,
   die weiterläuft und eine Baseline aus lauter Misses schreibt. Das ist exakt der stille
   Pfad, den D7 ausschließen soll — und er wäre nach der Änderung **neu** (heute scheitert
   die Eval an `SystemExit` aus `load_config`, weil `except Exception` `SystemExit` nicht
   fängt).
3. **`ImportError`-Zweig unmöglich.** `load_config` (`:55`) und
   `resolve_tmp_paths`/`tmp_env` (`:62`) sind Modul-Level-Importe; ein `ImportError` beendet
   das Modul vor jedem Helfer-Aufruf. IC-5 Punkt 2 ist dort nicht implementierbar.

**Wirkung.** RVW-2 ist damit für eine von vier Kopien nicht behoben; die Spec behauptet das
Gegenteil („alle vier Kopien", D7-Tabelle Zeile 385: „kein ungepinntes Kind, keine
ungepinnte Eval").

**Änderungsauflage.**
1. IC-5 in eine **Pro-Kopie-Tabelle** überführen: Rückgabetyp je Kopie; „`None`" wird für
   Kopie 4 als „das übergebene `base`-Env unverändert zurückgeben" definiert.
2. Für `run_role_routing_eval.py` festlegen, **wo** `TmpSinkError` den Lauf beendet:
   entweder `except TmpSinkError: raise` neben `ProviderError` (`:793`) **oder** — besser —
   das Pin-Env einmal pro Model-Klasse **vor** der Case-Schleife auflösen.
3. Den `ImportError`-Zweig für Kopie 4 ausdrücklich als „nicht anwendbar (Modul-Level-
   Importe)" markieren oder auf die drei übrigen Kopien beschränken.
4. AC-1189-25 entsprechend präzisieren („bei allen vier Helfern" → mit benanntem
   Aufrufer-Verhalten je Kopie).

**Beleg:** `scripts/run_role_routing_eval.py:55`, `:62`, `:697-713`, `:729-732`, `:783-802`;
Spec IC-5, D7-Tabelle.

---

### RVW2-2 — blocking · Logik (401-als-Erfolg erzeugt weiterhin falschen Erfolg)

**Befund.** IC-7 definiert Erfolg als `proc.poll() is None` **und** (bei konfiguriertem
Token) HTTP **401** (Zeilen 576–581). Die Prüfung kehrt beim **ersten** passenden Ergebnis
zurück. `/api/health` ist token-gated (`admin-server.py:3514-3524`, `:3541-3545`).

Damit gilt bei belegtem Port: Ein **Fremdprozess**, der auf `/api/health` mit 401 antwortet,
erfüllt das Kriterium sofort — zum Zeitpunkt t≈0, an dem das eigene Kind noch importiert und
den Port noch gar nicht gebunden hat. Erst danach scheitert der Bind (`:5918`) und das Kind
stirbt; `poll()` sieht das zu spät. Ergebnis: Erfolgsmeldung, PID-Datei auf einem toten
Kind — derselbe Fehler, den AC-1189-17 („kein falscher Erfolg") verhindern soll. R11
behauptet die umgekehrte Reihenfolge („Kind-Bind scheitert bei belegtem Port ⇒ `poll()`
erkennt Exit"), die nicht garantiert ist; R12 bezieht sich nur auf einen halbfertigen
*eigenen* Server.

**Wirkung.** Für die Token-Konfiguration — dem dokumentierten Remote-Access-Setup — ist der
Kernnutzen von D5/D6 („nie falscher Erfolg") nicht erreicht. AC-1189-17 ist so formulierbar
erfüllbar, ohne dass der Bug verschwindet (`kein 401` ist beim Fremdprozess nicht der Fall).

**Änderungsauflage.** Eine Bestätigung statt eines ersten Treffers festschreiben, z. B.:
1. **Bestätigungsfenster:** Erfolg erst, wenn das Kriterium über ein Fenster
   (`START_CONFIRM_GRACE`, z. B. 1,0 s) **stabil** gilt und `proc.poll() is None` am Ende
   des Fensters erneut geprüft wird (ein bindender Fehlstart ist dann sicher exit).
2. **oder** `/api/health` token-frei stellen (additiv, siehe RVW2-10) und **immer** `pid`
   vergleichen — dann entfällt der 401-Pfad ganz (Auth-Oberfläche ändern ⇒ eigene
   Entscheidung + Threat-Model-Zeile).
3. **oder** Listener-Ownership bestimmen (PID/Port-Owner plattformspezifisch) — teurer.
4. Frage 2 des Threat Models um diesen Pfad ergänzen; R11 entsprechend korrigieren
   („Reihenfolge nicht garantiert, deshalb Bestätigungsfenster").

**Beleg:** `scripts/admin-server.py:3514-3524`, `:3541-3545`, `:3794-3799`, `:5918`,
`:6041-6051`; Spec IC-7, D6, R11, R12, AC-1189-17.

---

### RVW2-3 — major · Feasibility (`token_configured` ist nicht definiert)

**Befund.** IC-7 nimmt `token_configured: bool` als Eingabe, IC-8 sagt nur
„`token_configured` = aufgelöster Token ist nicht `None`". Die tatsächliche Auflösung ist
dreistufig: `_resolve_admin_token(cli_token, config_token, config_token_file)` mit
Priorität CLI > `ADMIN_UI_TOKEN` (Env) > `admin-ui.token` > `admin-ui.token-file`
(`admin-server.py:887-906`, angewandt in `:5864-5868`, gesetzt in `:5916`). Leitet
`_admin_start_detached` das Flag nur aus `args.admin_token` ab, erwartet der Elternprozess
für Server mit Env- oder Config-Token **200**, bekommt **401** und meldet Fehlschlag —
also die Umkehrung des heutigen Bugs, und zwar für das in
`docs/howto/admin-ui-remote-access.md` beschriebene Setup.

**Wirkung.** Fehlschlagender `start` in jeder Token-Konfiguration, die nicht über
`--admin-token` läuft. Das ist ein Regressionsrisiko ersten Ranges für den einzigen Pfad,
den D5/D6 heilen soll.

**Änderungsauflage.** In IC-7/IC-8 die Quelle festschreiben: `_load_admin_ui_config(root)`
+ `_resolve_admin_token(...)` mit denselben Argumenten wie `AdminServer.__init__`
(`:5862-5868`), inklusive Verhalten bei geschluckten Fehlern (Defaults ⇒ kein Token).
Test ergänzen: `monkeypatch.setenv("ADMIN_UI_TOKEN", "x")` ⇒ 401 gilt als Erfolg,
**ohne** dass ein `Authorization`-Header gesendet wird (AC-28).

**Beleg:** `scripts/admin-server.py:887-906`, `:520-566`, `:5862-5868`, `:5916`.

---

### RVW2-4 — major · Teststrategie (AC-1189-11/30 ist wie formuliert unerfüllbar)

**Befund.** AC-1189-11 und AC-1189-30 verlangen einen identischen Snapshot von
`os.environ` **und** `tempfile.tempdir` vor/nach dem Aufruf; U1-5 wiederholt das. Die
verbindliche Testkonvention (Spec Zeilen 804–816) schreibt für Pin-Fälle
`tempfile.tempdir = None` **vor** dem Aufruf vor. `tempfile.gettempdir()` setzt den
Modul-Cache aber beim ersten Aufruf genau dann, wenn er leer ist (`tempdir =
_get_default_tempdir()`, guarded durch `_once_lock`, Stdlib-Verhalten). Nach
`system_temp_root(...)` ist `tempfile.tempdir` daher `<sink>` bzw. `/tmp` statt `None` —
die Assertion schlägt zwangsläufig fehl. Ein „Restore" im Produktivcode wäre eine
prozessglobale Mutation und würde RVW-1 wieder öffnen.

**Wirkung.** Ein AC, das nicht grün werden kann, plus die Versuchung, ihn mit einem
Restore-Workaround zu „lösen" — der dann die gerade entfernte Nebenläufigkeitslücke
zurückbringt.

**Änderungsauflage.** AC-1189-11/30 und U1-5 umformulieren: (a) `os.environ` bleibt
byte-identisch; (b) `tempfile.tempdir` wird **ausschließlich** vom Stdlib-Cache gesetzt
(set-once, nicht durch `system_temp_root`), Snapshot **nach** Priming von `gettempdir()`
nehmen; (c) R10 als die Stelle benennen, die diese Ausnahme trägt.

**Beleg:** Spec AC-1189-11, AC-1189-30, U1-5, „Testkonvention" (Zeilen 802–816);
CPython-`tempfile.gettempdir` (Set-once-Cache).

---

### RVW2-5 — major · Vollständigkeit (Aufrufer-Verhalten nicht auf IC-Ebene verankert)

**Befund.** Die D7-Tabelle (Zeilen 379–386) verspricht konkrete Ergebnisse, die aus den
heutigen Aufrufern **nicht** folgen und für die kein IC den Eingriff benennt:

1. `ConsistencyService.run_consistency_check` fängt `Exception` generisch und liefert über
   `_generic_error_response` (`admin-server.py:1630-1644`, Aufruf `:1761-1767`)
   `{"error": "ERR_CONSISTENCY_CHECK"}` mit HTTP-500 — nicht das versprochene
   `{"error": "tmp-sink pin unavailable: …"}`. Es braucht einen eigenen `except TmpSinkError`
   **vor** dem generischen Handler.
2. `cli_commands.py` übergibt inline `env=_admin_tmp_env(...)` (`:575`, `:1732`) innerhalb
   von `sync_command`; dort werden nur `SyncError` gefangen (`:436`, `:666`, `:728`), und
   `sync.py::main` (`:804-847`) hat keinen Top-Level-Handler ⇒ roher Traceback statt
   „Meldung + Exit ≠ 0".
3. `consistency-check.py::main` (`:287`) hat keinen Handler ⇒ Traceback.
4. `SyncExecutor._run` würde den Fehler über den generischen `except Exception`
   (`:1380-1381`) als `"sync.py failed: …"` verbuchen — die Tabelle sagt
   `"tmp-sink pin unavailable: …"`. Auch das braucht einen eigenen `except`-Zweig.
5. **Exit-Code und Meldungsformat** sind offen („Exit ≠ 0"). Hausform ist
   `error: <code>: <message>` + Exit 2 (`cli_commands.py:1357-1359`), passend zum
   `TmpSinkError`-Docstring „Callers map it to Exit 2" (`repo_containment.py:568`);
   `admin-server.py` nutzt Exit 1 (`:6051`).
6. `tmp-sink.pin-unavailable` fehlt im dokumentierten Code-Set von `TmpSinkError`
   (`repo_containment.py:566-568`); AC-1189-32 deckt diese Doku nicht ab.

**Wirkung.** Die Spec verspricht Nutzerverhalten, das der Plan ohne weitere Festlegung nicht
erzeugen kann — mit dem Risiko, dass „kein stiller Durchlauf" durch einen Traceback oder
eine 500er-Antwort ersetzt wird, die den Reparaturhinweis nicht enthält.

**Änderungsauflage.** In IC-5 eine kleine Tabelle „Aufrufer → catch-Stelle → Exit-Code →
Meldungsformat" ergänzen (inkl. Exit 2 als Default für Skripte, 1 für `start`), den
`TmpSinkError`-Docstring um `tmp-sink.pin-unavailable` erweitern und AC-1189-25 um Code und
Exit-Code präzisieren.

**Beleg:** `scripts/admin-server.py:1380-1381`, `:1630-1644`, `:1761-1767`;
`scripts/lib/cli_commands.py:436`, `:575`, `:666`, `:728`, `:1357-1359`, `:1732`;
`scripts/consistency-check.py:287`; `scripts/sync.py:804-847`;
`scripts/lib/repo_containment.py:563-574`.

---

### RVW2-6 — minor · Teststrategie (AC-1189-25 ohne Anker für drei Kopien)

**Befund.** AC-1189-25 fordert das Abbruchverhalten „bei allen vier Helfern"; der Testplan
nennt nur U4-26 für `admin-server.py::_tmp_sink_env`. Für `consistency-check.py`,
`cli_commands.py` und `run_role_routing_eval.py` gibt es keinen Anker, obwohl das Muster
existiert (`test_admin_server.py:41-51` lädt per `importlib`).

**Änderungsauflage.** Drei kleine Tests (je Kopie: gültige Config ⇒ Pin, defekte Config ⇒
`TmpSinkError("tmp-sink.pin-unavailable")`) als U4-26a/b/c im Testplan verankern oder AC-25
auf die drei `dict | None`-Kopien begrenzen und Kopie 4 separat prüfen.

**Beleg:** Spec AC-1189-25, U4-26; `tests/test_admin_server.py:41-51`.

---

### RVW2-7 — minor · Konsistenz (IC-9: „gleiche Konstanten" verlangsamt den Boot)

**Befund.** IC-9 (Zeilen 606–613) ersetzt `time.sleep(1.5)` durch ein `poll()`-basiertes
Warten mit „gleiche[n] Konstanten". Welche gemeint sind, ist offen; naheliegend ist
`START_VERIFY_TIMEOUT` (Default 5,0 s, IC-7). Da ein gesundes Viz-/MCP-Kind nie stirbt, kann
Erfolg erst nach Ablauf des Fensters gemeldet werden ⇒ `start_all()` (zwei Kinder,
`admin-server.py:5950-5952`) verzögert den Serverstart um bis zu 10 s statt 3 s.

**Änderungsauflage.** Eigene Konstante (`VIZ_START_GRACE`, Default 1,5 s) benennen und
begründen, warum dort kein HTTP-Kriterium greift.

**Beleg:** `scripts/admin-server.py:640-660`, `:5945-5952`; Spec IC-7/IC-9.

---

### RVW2-8 — minor · Vollständigkeit (IC-2-Vertrag passt nicht zum Resolver)

**Befund.** IC-2 sagt „`None` bei deaktiviertem/ungültigem Sink". Der Resolver fällt bei
ungültigem `tmp-sink.path` jedoch auf den Default `.tmp` zurück und protokolliert das als
Finding (`repo_containment.py:540-549`); `_resolve_sink_dir` liefert dann brav
`<root>/.tmp` (`:304-327`). Ein `None` verlangt einen expliziten Finding-Check, wie ihn
`_active_sink_dir` bereits macht (`:590-594`). Funktional unkritisch (der Validator bricht
bei ungültigem Pfad ohnehin an `config.py:939-950` ab), aber der Vertrag ist so nicht
implementierbar.

**Änderungsauflage.** In IC-2 den Finding-Check nennen oder „Fallback-Default wird
zurückgegeben" festschreiben.

**Beleg:** `scripts/lib/repo_containment.py:304-327`, `:540-560`, `:590-594`;
`scripts/lib/config.py:939-950`.

---

### RVW2-9 — minor · Konsistenz (D2: „Golden-Bruch" überzogen)

**Befund.** D2 Begründung (2) (Zeilen 283–285) nennt „Golden-/Drift-Bruch". Die
Slimming-Goldens tragen den **unaufgelösten** Token `{{PYTEST_BASETEMP}}`
(`tests/fixtures/slimming-golden/tester.md:45`, `documenter.md:68`, `e2e-tester.md:73`,
`test-executor.md:33,41`) und würden durch einen anderen Basetemp **nicht** brechen. Der
Drift-Teil stimmt (die deployten Agenten-Dateien enthalten den aufgelösten absoluten Pfad,
`config.py:2066-2071`).

**Änderungsauflage.** Begründung auf „Drift der deployten Artefakte" präzisieren; die
Entscheidung ADR-1189-02 selbst bleibt unberührt (sie steht auf §5.5 + Vorgänger-Spec).

**Beleg:** `tests/fixtures/slimming-golden/*.md`; `scripts/lib/config.py:2066-2071`.

---

### RVW2-10 — minor · Risiken (IC-10: `root` im Health-Payload wird nirgends genutzt)

**Befund.** IC-10/AC-1189-27 ergänzen `pid` **und** `root`. Kein Kriterium (IC-7,
AC-1189-15/17) prüft `root`; das Threat Model erwähnt es nicht. Bei **nicht** konfiguriertem
Token ist `/api/health` unauthentifiziert und gäbe den absoluten Projektpfad preis (kein
*neuer* Leak — `/api/mode` liefert `root` schon heute, `admin-server.py:3801-3813`, dort aber
token-gated, weil `/api/mode` nicht public ist).

**Änderungsauflage.** Entweder `root` fällt weg (nur `pid`), oder IC-7 nutzt es als
zusätzliches Identitätskriterium im Token-freien Fall und das Threat Model bekommt eine
Zeile dazu.

**Beleg:** `scripts/admin-server.py:3794-3799`, `:3801-3813`; Spec IC-10, AC-1189-27.

---

### RVW2-11 — info · `lib/rc.py` existiert nicht; Annotationsstil

**Befund.** Die Prüffrage nennt `lib/rc.py`. Es gibt kein solches Modul: `rc` ist der Alias
`from . import repo_containment as rc` (`scripts/lib/tmp_paths.py:33`). Kein Mangel der Spec,
aber relevant für die Frage „konsistent mit `lib/rc.py`-Konventionen" — die Konvention liegt
in `repo_containment.TmpSinkError`. Ergänzend: IC-1/IC-2 zeigen `str | os.PathLike[str]`
unquoted; die Bestandsdatei quotet solche Annotationen für Python 3.9
(`repo_containment.py:305`).

---

## 4. Was in Rev 2 überzeugt (Stichproben, VERIFIED)

- **RVW-1 ist echt gelöst, nicht nur umformuliert.** Der Verzicht auf Env-Mutation ist die
  einzige Variante, die im `ThreadingHTTPServer` ohne Restrisiko trägt; ADR-1189-07 und
  IC-1 „Keine Mutation" sind konsequent. Die Gegenprobe am Code findet keinen verbliebenen
  Mutationspfad.
- **D7 ist die richtige Antwort auf RVW-2.** `None` auf drei definierte Zustände zu
  begrenzen und `SystemExit` bewusst mitzufangen (IC-5 Punkt 4) trifft die Ursache — der
  `SystemExit`-Durchschlag ist am Code bestätigt (`admin-server.py:334`,
  `cli_commands.py:208`, `consistency-check.py:93`).
- **D6 ohne Token ist die richtige Sicherheitsentscheidung.** Der Verzicht auf
  Credential-Versand, `ProxyHandler({})`, deaktivierter Redirect-Handler und Loopback-Probe
  bei Wildcard-Bind sind präzise und testbar; das Threat Model ist ein echter Zugewinn.
- **RVW-8 korrekt eingearbeitet.** PID-Datei sofort (`IC-8 Schritt 3`), Erfolgsmeldung erst
  nach Verifikation, Aufräumen bei Fehlschlag — deckt sich mit dem heutigen Muster
  (`admin-server.py:6041-6051`) und macht AC-1189-31 testbar.
- **RVW-9/RVW-16 sind sauber geschlossen.** AC-1189-05 ist auf den expliziten Block
  beschränkt, Matrix-Zeile 5 korrigiert (`config.py:892`), U3-16 dokumentiert den No-op;
  die OQ-Tabelle enthält keine Scheinfragen mehr.
- **Belegdisziplin bleibt hoch.** Die im Auftrag geprüften Zeilenangaben stimmen
  (`:311-336`, `:74-95`, `:188-210`, `:697`, `:5817-5824`, `:1352-1370`, `:1744-1750`,
  `:5912`/`:5920-5943`, `:5945-5952`); die einzige sachliche Fehlannahme betrifft die
  vierte Kopie (RVW2-1).

---

## 5. Nächster Schritt (Rev 3, minimaler Umfang)

1. **RVW2-1** — IC-5 als Pro-Kopie-Vertrag neu fassen; `TmpSinkError` in der Eval-Schleife
   re-raisen (oder Env vor der Schleife auflösen); `ImportError`-Zweig für Kopie 4
   streichen; AC-1189-25 anpassen.
2. **RVW2-2** — 401-Pfad mit Bestätigungsfenster (oder token-freies `/api/health` mit
   `pid`-Vergleich); R11 korrigieren; Threat-Model-Frage 2 ergänzen; AC-1189-17 verschärfen.
3. **RVW2-3** — `token_configured` an `_load_admin_ui_config` + `_resolve_admin_token`
   binden; Test mit `ADMIN_UI_TOKEN`.
4. **RVW2-4** — AC-1189-11/30 und U1-5 auf `os.environ` + „Stdlib-Set-once-Cache"
   umformulieren.
5. **RVW2-5** — catch-Stellen/Exit-Codes/Meldungsformat je Aufrufer in IC-5; Code-Set in
   `TmpSinkError` erweitern.
6. **Minor:** RVW2-6 (Testanker für drei Kopien), RVW2-7 (`VIZ_START_GRACE`), RVW2-8
   (IC-2-Finding-Check), RVW2-9 (D2-Begründung), RVW2-10 (`root` nutzen oder streichen).

**Danach:** kurzes Re-Review, beschränkt auf RVW2-1…RVW2-5. Sind diese fünf Punkte
geschlossen und keine neuen Widersprüche entstanden, ist die Spec **approbierbar**; der
Approval-Marker `Status: APPROVED (Datum)` wird ausschließlich vom User gesetzt. Erst dann
schreitet die Pipeline `quality_pipelines.concept-driven-dev` fort (specify → review →
approve → plan), und der Plan referenziert `spec-id: SPEC-1189-tmp-sink-pin-vs-system-temp`.

---

*Re-Review-Bericht, keine Umsetzung. Die geprüfte Spec wurde nicht verändert; es wurde kein
Code geschrieben und kein Commit erstellt (Auftragsvorgabe).*
