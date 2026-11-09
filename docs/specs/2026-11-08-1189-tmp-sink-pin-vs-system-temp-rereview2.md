# Re-Review-Nachtrag (Rev 3) — Spec `SPEC-1189-tmp-sink-pin-vs-system-temp`

> **Gegenstand:** `docs/specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-spec.md`,
> `Revision: 3`, `Status: DRAFT (2026-11-08)`, Klasse M.
> **Vorlage:** Re-Review Rev 2 (`…-rereview.md`, RVW2-1…RVW2-11).
> **Prüfumfang (Auftrag):** **nur** RVW2-1…RVW2-5; RVW-1 gilt als behoben und wurde
> nicht erneut geprüft. RVW2-6…RVW2-11 nur daraufhin, ob ihre Einarbeitung **neue**
> Widersprüche erzeugt.
> **Prüfmethode:** Gegenlesen am Code, jede Aussage mit `datei:zeile` belegt.
> **Nicht ausgeführt:** `sync.py`, `pytest`, `git`, Shell-Messungen (keine Ausführungs-
> rechte in dieser Session) — Zeitannahmen sind deshalb als Annahme markiert.
> Kein Code, keine Implementierung, keine Änderung der geprüften Spec, kein Commit.

---

## 1. Ergebnis je Auflage

| Auflage | Status Rev 3 | Kernbeleg |
|---|---|---|
| **RVW2-1** (IC-5 gilt nicht für die vierte Kopie) | **geschlossen** (Rest: RVW3-2, RVW3-4) | IC-5a deckt `run_role_routing_eval.py::_tmp_sink_env` (`:697-713`) exakt: `-> dict`, Rückgabe `env` in allen Fehlerfällen, kein `None`, Aufrufer-Deref `:729-732`, Modul-Level-Importe `:55`/`:62`, Case-Schleife `:783-802` mit nur `except ProviderError: raise` (`:793`) vor `except Exception` (`:795`). Die vorgeschlagene Guard-Form ist mit `tests/test_tmp_sink_env_coverage.py:46`, `:134-153`, `:156-172` verträglich (s. 2.1). |
| **RVW2-2** (401-als-Erfolg) | **nicht wirksam geschlossen** → **RVW3-1** | Bestätigungsfenster entfernt den *deterministischen* Fall, aber das Fensterende kann **vor** dem Bind-Versuch des Kindes liegen (`admin-server.py:5918`); Restfenster bleibt. |
| **RVW2-3** (`token_configured` undefiniert) | **geschlossen** | `_load_admin_ui_config` `:524-566` (Fang `:558` nur `Exception`, `SystemExit` schlägt durch), `_resolve_admin_token` `:887-906` (CLI > `ADMIN_UI_TOKEN` > `admin-ui.token` > `token-file`), Kind identisch `:5862-5868`; kein `--admin-token-file` im Parser `:6110-6142`; Env-Vererbung ins Kind über `work_dir_env` `repo_containment.py:751`. |
| **RVW2-4** (AC-11/AC-30 unerfüllbar) | **geschlossen** | AC-1189-11/30 + U1-5 (Spec `:1026-1035`, `:1168`, `:1189`) verlangen jetzt `os.environ` byte-identisch + `tempfile.tempdir` nur Stdlib-Set-once, Snapshot **nach** Priming, R10 als Träger; kein Widerspruch zur Testkonvention `:1003-1005` (dort `tempdir=None` **vor** dem Aufruf, danach Priming). |
| **RVW2-5** (Aufrufer-Verhalten nicht verankert) | **geschlossen** (Rest: RVW3-5) | IC-5b `:644-661` deckt **alle** realen Aufrufstellen ab: 12 Stellen / 7 Symbole (s. 2.5); Exit-Codes passen zur Hausform (`cli_commands.py:1357-1359`), Admin-Lifecycle `:6049-6051`. |

**Neue Widersprüche aus RVW2-6…RVW2-11:** keine inhaltlichen. Einziger Formfehler:
der Rev-3-Kopf (`:50`) nennt „U4-26a…d", der Testplan führt 26a…**e** (`:1100-1120`).

---

## 2. Prüfantworten (Auftrag 1–5)

### 2.1 RVW2-1 — deckt IC-5a die vierte Kopie wirklich ab?

**Ja, in allen vier Teilfragen:**

- **Rückgabetyp:** `_tmp_sink_env(base: dict | None = None) -> dict` (`:697`), Rückgabe
  `dict(os.environ if base is None else base)` (`:705`), nie `None`; IC-5a Zeile 4 sagt
  genau das.
- **Abbruch vor der Case-Schleife:** `run_class` (`:769`), Run-Schleife `:779`,
  Case-Schleife `:782-802`; die Auflösung „einmal vor der Run-/Case-Schleife" liegt
  damit vor dem ersten Provider-Aufruf. Der Propagationsweg bis `main` ist belegt:
  `run_class` wird über den Runner `:1008-1019` in `eval_gate.run_with_approval`
  (`eval_gate.py:245-279`) aufgerufen, das die Runner ohne `try/except` ausführt
  (`eval_gate.py:278`) ⇒ `TmpSinkError` erreicht `main` (`:930`) ungefiltert. Das ist
  **stärker** als in der Spec begründet — die Spec sollte `eval_gate.py:278` als
  Belegstelle nennen, sonst wirkt „ungefiltert bis main" unbelegt.
- **`except TmpSinkError: raise` als Defense-in-depth:** funktioniert, weil die Klausel
  **vor** `except Exception` (`:795`) stehen muss und `ProviderError` (`:793`) bereits
  re-raised; IC-5a formuliert das korrekt.
- **`ImportError`-Sonderbehandlung:** korrekt als „nicht anwendbar" markiert —
  `load_config` (`:55`) und `resolve_tmp_paths`/`tmp_env` (`:62`) sind Modul-Level.
  Damit ist AC-1189-25/26 (`:1184-1185`) widerspruchsfrei.
- **Guard-Verträglichkeit:** `_env_is_pinned` (`:156-172`) prüft zuerst
  `ast.unparse(env_value)` auf `_PIN_TOKENS = ("tmp_env", "tmp_sink_env")` (`:46`) und
  fällt nur bei `ast.Name` auf Zuweisungen im selben Scope zurück (`:134-153`). Die
  vorgeschriebene Form `child_env = dict(_tmp_sink_env(...) if env is None else env)`
  trägt den Token im `dict(...)`-Ausdruck ⇒ Guard grün, keine neue Allowlist-Zeile. Die
  Gegenaussage der Spec (`child_env = dict(env)` wäre rot) stimmt ebenfalls.

**Reste:** RVW3-2 (Warnzeilentext), RVW3-4 („identisch" bei Kopie 4). Zusätzlich
unschädlich, aber notierenswert: `run_class` löst den Pin **pro Model-Klasse** auf, also
nach der Freigabe (`eval_gate.py:278`) und ggf. nach bezahlten Aufrufen von Klasse 1.
Da die Config innerhalb eines Laufs konstant ist, ist das kein Risiko — nur ein
Satz, den der Plan kennen sollte.

### 2.2 RVW2-2 — verhindert IC-7/IC-8 den falschen Erfolg?

**Nur teilweise.** Das Fenster beseitigt den *deterministischen* Fehlschlag (erster
Treffer ⇒ Erfolg), aber die Begründung stützt sich auf eine **Zeitannahme**, die die
Spec nicht benennt:

1. `/api/health` bleibt token-gated (`_is_public_get_path` `:3514-3524`; `do_GET`
   `:3541-3551`). Bei gesetztem Token sieht der Elternprozess **nur** 401.
2. Ein Fremdprozess, der den Port hält, antwortet ab t≈0 mit 401 ⇒
   `confirm_since ≈ 0`; das Fenster endet nach `START_CONFIRM_GRACE` (1,0 s).
3. Das eigene Kind bindet erst in `_DaemonThreadingHTTPServer((host, port), …)`
   (`:5918`) — **nach** Interpreter-Start, Modul-Importen (`:40-58`, PyYAML `:60`) und
   **zwei** vollen `load_config`-Läufen (`:5862` über `_load_admin_ui_config` `:548`,
   `:5912` über `_read_version` `:5927`).
4. Ist diese Pre-Bind-Phase länger als das Fenster, liefert `proc.poll()` am Fensterende
   `None` ⇒ **Erfolg**, obwohl der Bind anschließend scheitert (zwei Listener auf
   derselben Adresse sind auch mit `SO_REUSEADDR` nicht möglich) und das Kind exit't.
   Ergebnis: Erfolgsmeldung + PID-Datei auf einem toten Kind — genau AC-1189-17.

Die Spec behauptet dagegen absolut: „Damit kann ein Fremdprozess mit sofortigem 401 den
Start nicht mehr fälschlich als Erfolg markieren" (IC-7, `:718-719`). Das ist **nicht
belegt**; es gilt nur unter `Kind-Pre-Bind-Zeit < START_CONFIRM_GRACE` — eine Annahme,
die auf kalten/langsamen Umgebungen (R6 nennt CI selbst) kippt. R11 (`:1211`) benennt
zwar ein Restrisiko, beschreibt es aber falsch: nicht „Fremdprozess bleibt >1 s gesund",
sondern „**unser Kind hat am Fensterende noch nicht gebunden**" — unabhängig vom
Verhalten des Angreifers. Als Heuristik ist das vertretbar, als formulierte Garantie
nicht.

**Auflösung (eine von zwei, beide klein):**
- **A (empfohlen, strukturell):** `/api/health` in `_is_public_get_path` (`:3524`)
  aufnehmen und **immer** `pid == proc.pid` prüfen; der 401-Zweig entfällt, IC-7 und
  `token_configured` (RVW2-3) werden einfacher. Die Spec rechnet mit diesem Fall bereits:
  IC-10 begründet das Streichen von `root` ausdrücklich mit der token-freien Antwort
  (`:792-796`), das Threat Model führt sie als Position (`:948-952`, (h) `:971-972`).
  Als bewusste Entscheidung mit Threat-Model-Zeile festzuschreiben (Auth-Oberfläche!).
- **B (Fenster behalten, dann aber ehrlich):** (i) Pre-Flight-Bind-Probe des
  Elternprozesses vor dem Spawn (gleiche `allow_reuse_address`-Semantik wie
  `http.server.HTTPServer`), damit der reale Fall „Port schon belegt" **vor** dem Spawn
  mit Exit 1 endet; (ii) `START_CONFIRM_GRACE` an die gemessene Kaltstartzeit koppeln und
  als Annahme (ASSUMED) + R6/R11 ausweisen; (iii) IC-7/D6/R11 auf „Heuristik" umstellen.

Zusätzlich: AC-1189-17 (`:1174`) mischt zwei Konfigurationen — die erste Klausel
(„Health-`pid`/`mode` passt nicht") ist nur **ohne** Token prüfbar, die zweite nur
**mit**. Getrennt formulieren.

### 2.3 RVW2-3 — ist die `token_configured`-Quelle korrekt?

**Ja, byte-genau am Code:**
`_load_admin_ui_config(root)` (`:524-566`, `token` `:552`, `token_file` `:553`) +
`_resolve_admin_token(cli_token, config_token, config_token_file)` (`:887-906`);
Priorität CLI > `ADMIN_UI_TOKEN` > `admin-ui.token` > `token-file`. Das Kind löst
identisch (`:5862-5868`) — mit dem einzigen Unterschied, dass `__init__`
`admin_token_file or admin_cfg["token_file"]` übergibt; im `start`-Pfad existiert kein
`--admin-token-file` (Parser `:6110-6142`), also ist `admin_cfg["token_file"]`
äquivalent. `args.admin_token` wird an das Kind weitergereicht (`:6012-6013`),
`ADMIN_UI_TOKEN` erbt es über `work_dir_env` (`repo_containment.py:751`), `token-file`
liest das Kind selbst (`:5867`). Fehlerfälle sind konsistent: ein nicht lesbarer
Token-File ergibt auf beiden Seiten `None` (⇒ 200 erwartet); `SystemExit` aus
`load_config` wird von `:558` **nicht** geschluckt (nur `Exception`) und beendet den
Start sichtbar.

**Fehlklassifikation „Token gesetzt, Probe sendet keinen"?** Nein — das ist der
Konstruktionsfall: der eigene Server **muss** 401 antworten, wenn ein Token aufgelöst
wurde. Kritisch ist nur, dass Eltern und Kind **denselben** Token-Begriff haben; das ist
jetzt der Fall. Rest siehe RVW3-1 (Identität, nicht Token-Erkennung).

### 2.4 RVW2-4 — sind AC-11 und AC-30 erfüllbar?

**Ja.** AC-1189-11 (`:1168`) verlangt nur noch `os.environ` byte-identisch, keine
persistenten Artefakte, die transiente Stdlib-Probe und `tempfile.tempdir` **ausschließlich**
aus dem Set-once-Cache mit Snapshot **nach** Priming; AC-1189-30 (`:1189`) wiederholt das
für 8 Threads; U1-5/U1-6 (`:1026-1035`) setzen es in Testschritte um, R10 (`:1210`) trägt
die Ausnahme. Das ist mit `cpython:tempfile.gettempdir` (`_once_lock`, `tempdir =
_get_default_tempdir()`) und mit IC-1 „Keine Mutation" (`:515-522`) konsistent; die
Testkonvention (`:1003-1005`, `tempdir=None` vor dem Aufruf) widerspricht nicht, weil
das Priming **nach** dem Setzen erfolgt. Kein Restbefund.

### 2.5 RVW2-5 — ist die IC-5b-Matrix vollständig?

**Ja für den Geltungsbereich (die vier Helfer).** Gegenprobe über alle Aufrufstellen:

| Symbol | Stellen | IC-5b |
|---|---|---|
| `_admin_start_detached` | `:6032`, `:6038` | „um den `env=`-Ausdruck", Exit 1 ✔ |
| `VizManager._start` | `:650`, `:659` (kein `try` im Bestand) | eigener Fang, `False` ✔ |
| `SyncExecutor._run` | `:1369` (generisch `:1380`, `_record_run` `:1382`) | eigener `except` davor ✔ |
| `ConsistencyService.run_consistency_check` | `:1749` (generisch `:1761` via `_generic_error_response` `:1630-1644`) | eigener `except` davor, 200 via `_route_get_consistency_check` `:3875-3876` ✔ |
| `cli_commands` | `:575`, `:1732` | `_admin_tmp_env_or_exit`, Exit 2 ✔ |
| `consistency-check.py` | `:105`, `:112`, `:128` (Fang nur `OSError`/`SubprocessError` `:116`, `:132`) | Top-Level in `main` `:287`, Exit 2 ✔ |
| `run_role_routing_eval.py` | `:729` | Top-Level in `main` `:930`, Exit 2 ✔ |

Kein fehlender Pfad. Zwei **direkte** `tmp_env`-Verbraucher außerhalb der vier Helfer
(`context_report.py:347`, `meta_optimizer.py:1532`) schlucken keine Fehler und bleiben
bewusst außerhalb von D7 — kein Finding, im Plan nennen. Nebenbefund: `consistency-check.py`
nutzt Exit 2 bereits für „File not found" (`:322`); die Doppelbelegung ist zulässig,
sollte aber im Plan einmal benannt sein.

---

## 3. Findings

### RVW3-1 — blocking · Logik / Risiken (Restfenster im 401-Kriterium)

**Befund.** IC-7/D6 sagen absolut, ein Fremdprozess mit sofortigem 401 könne den Start
„nicht mehr fälschlich als Erfolg markieren" (`:718-719`). Das Fenster
(`confirm_since` + `poll()`-Recheck) schützt nur, wenn das Kind **innerhalb** des Fensters
bindet und scheitert. Der Elternprozess kann aber ab t≈0 einen 401-Kandidaten sehen,
während das Kind noch importiert und `load_config` zweimal ausführt; gebunden wird erst
bei `admin-server.py:5918`. Überschreitet die Pre-Bind-Phase `START_CONFIRM_GRACE`
(1,0 s; R6 nennt CI/langsame Maschinen selbst als Risiko), endet das Fenster mit
`poll() is None` ⇒ Erfolgsmeldung, PID-Datei auf einem toten Kind. R11 (`:1211`)
beschreibt das Restrisiko als „Fremdprozess bleibt >1 s gesund" und trifft damit nicht
den Mechanismus; die Aussage „der Bind-Fehlstart exit't innerhalb des Fensters" ist
eine Zeitannahme, kein Beweis. AC-1189-17 (`:1174`) ist in der zweiten Klausel
erfüllbar, in der ersten („`pid`/`mode` passt nicht") im Token-Setup nicht prüfbar.

**Wirkung.** Für das dokumentierte Remote-/Token-Setup bleibt der falsche Erfolg
möglich — genau der Zustand, den D5/D6 und AC-1189-17 ausschließen sollen. Kein
Architekturproblem, aber eine unbelegte Garantie in einem verbindlichen IC.

**Änderungsauflage.** Eine der beiden Auflösungen aus 2.2 festschreiben:
(A) `/api/health` token-frei (`_is_public_get_path` `:3514-3524` erweitern) + **immer**
`pid`-Vergleich; D6/IC-7 entsprechend vereinfachen, Threat-Model-Zeile ergänzen,
401-Zweig streichen. **oder** (B) 401-Fenster behalten, aber (i) Pre-Flight-Bind-Probe
vor dem Spawn mit Exit 1, (ii) `START_CONFIRM_GRACE` als gemessene, dokumentierte
Annahme (ASSUMED + R6), (iii) IC-7/D6/R11 explizit als **Heuristik** formulieren
(„Restfenster = Kind-Pre-Bind-Zeit"); AC-1189-17 in die zwei Konfigurationen trennen.

**Beleg:** `admin-server.py:3514-3524`, `:3541-3551`, `:5862-5868`, `:5912`/`:5920-5943`,
`:5918`, `:40-60`, `:6041-6051`; `eval_gate` unberührt; Spec IC-7 `:712-728`, D6
`:377-405`, R11 `:1211`, AC-17 `:1174`.

---

### RVW3-2 — minor · Vollständigkeit („Warnzeile … Text unverändert" existiert nicht)

**Befund.** IC-5a (`:625`) und D7 Punkt 3 (`:416-417`) verlangen für den
`ImportError`-Fall „genau eine Warnzeile (Text unverändert)". Im Bestand gibt es keine
solche Zeile: die drei `dict | None`-Kopien geben im `except Exception` **still** `None`
zurück (`admin-server.py:334-335`, `consistency-check.py:93-94`,
`cli_commands.py:208-209`).

**Wirkung.** Der Plan muss den Text **neu** definieren; „unverändert" führt zu der
Annahme, es gäbe eine bestehende Formulierung, und macht AC-1189-26 (`:1185`) nicht
prüfbar.

**Änderungsauflage.** In IC-5a den Wortlaut der einen Warnzeile festschreiben
(z. B. `  !  tmp-sink pin unavailable: framework lib not importable; inheriting environment`)
und „Text unverändert" streichen.

---

### RVW3-3 — minor · Konsistenz (Docstrings der drei Helfer widersprechen D7)

**Befund.** D7 kehrt die dokumentierte Zusage der Helfer um, aber D8/AC-1189-32
(`:1191`) erfassen nur `TmpSinkError` und `tmp_sink_location_error`. Unverändert falsch
blieben: `admin-server.py:315-320` („None … at runtime the server keeps operating with the
inherited env instead of blocking its UI"), `consistency-check.py:77-81` („this helper
never raises"), `cli_commands.py:193-196` („a CLI start never fails because of it").
Genau diese Dateien werden ohnehin angefasst.

**Wirkung.** Doku-/Verhaltens-Drift im selben Commit; der Guard/die Doku-Tests aus AC-32
merken es nicht.

**Änderungsauflage.** D8 um Punkt 4 (drei Helfer-Docstrings) erweitern und AC-1189-32
um diesen Grep erweitern.

---

### RVW3-4 — minor · Testbarkeit („identisch" bei Kopie 4 ist mehrdeutig)

**Befund.** IC-5a Zeile 4 (`:615`) und Test 26c (`:1108-1109`) verlangen, die Rückgabe
sei „das übergebene `base`-Env **unverändert**" bzw. „**identisch**". Der Bestand kopiert
(`env = dict(os.environ if base is None else base)`, `:705`); ein Test mit `assert result
is base` schlüge fehl, obwohl das Verhalten korrekt ist.

**Änderungsauflage.** Formulierung auf „inhaltlich gleich (gleicher Key-Set und gleiche
Werte), nicht zwingend dasselbe Objekt" schärfen — in IC-5a, AC-1189-26 und Test 26c.

---

### RVW3-5 — minor · Konsistenz (IC-5b nennt `stderr`, das zitierte Muster schreibt auf stdout)

**Befund.** IC-5b (`:655`) schreibt für `_admin_start_detached` „stderr
`  !  tmp-sink pin unavailable: …`" und verweist als Muster auf `:6049-6051`. Das
Bestands­muster (`:6049-6051`) nutzt `print(...)` **ohne** `file=sys.stderr`, also
stdout; nur andere Stellen desselben Skripts schreiben nach stderr (`:567`).
AC-1189-14 (`:1171`) sagt „Meldung enthält …" ohne Stream.

**Wirkung.** Ein Test, der stderr prüft, wäre rot, ohne dass die Funktion fehlt; oder die
Implementierung ändert stillschweigend die bestehende Ausgabekonvention.

**Änderungsauflage.** In IC-5b den Zielstream **festlegen** (Empfehlung: wie Bestand
stdout für die Lifecycle-Zeilen, stderr nur für den Fall, dass eine Änderung gewollt ist)
und AC-1189-14 entsprechend präzisieren.

---

### RVW3-6 — info · Belegstellen und Formfehler

1. **Propagationsweg belegen:** IC-5a sagt „propagiert … bis `main` (siehe IC-5b)"; der
   tatsächliche Weg führt über `eval_gate.run_with_approval` (`eval_gate.py:278`, Aufruf
   `run_role_routing_eval.py:1021`). Als Belegstelle ergänzen — sonst wirkt die Aussage
   unbelegt und ein Plan könnte an der Zwischenschicht zweifeln.
2. **`run_class` löst den Pin pro Model-Klasse** auf (nach Freigabe, ggf. nach bezahlten
   Aufrufen von Klasse 1). Unschädlich (Config konstant), aber einen Satz wert.
3. **Kopf vs. Testplan:** Rev-3-Kopf `:50` „U4-26a…d", Testplan `:1100-1120` 26a…**e**.
4. **Außerhalb des Geltungsbereichs:** `context_report.py:347`, `meta_optimizer.py:1532`
   rufen `tmp_env` direkt (kein stiller Unpin, keine `None`-Rückgabe) — im Plan nennen,
   nicht in D7 ziehen.

---

## 4. Spec-Template-Checks (unverändert)

| Check | Ergebnis |
|---|---|
| Pflichtsektionen (Interface Contracts, Acceptance Criteria, Datenfluss, Problem/Ziel/Nicht-Ziele, Offene Fragen, Risiken) | **grün** |
| Trace-Anker `spec-id: SPEC-1189-tmp-sink-pin-vs-system-temp` | **grün** (`:9`, `:1252-1262`) |
| Approval-Marker | **grün** — `Status: DRAFT`, „APPROVED setzt ausschließlich der User" (`:3-4`) |
| No-Placeholder | **grün** — `<root>`/`<sink>`/`<system-temp>` sind Metavariablen, `Plan: <wird nach Approval erzeugt>` ist die vorgesehene Vorwärtsreferenz |

---

## 5. Votum

**APPROVE WITH CHANGES** (= `CHANGES_REQUESTED`) — **die Freigabe durch den User kann
noch nicht erfolgen.**

- **RVW2-1, RVW2-3, RVW2-4, RVW2-5 sind wirksam geschlossen** und am Code belegt
  (inkl. der vierten Kopie und der Guard-Verträglichkeit).
- **RVW2-2 ist nur teilweise geschlossen** (RVW3-1 blocking): Das Bestätigungsfenster ist
  die richtige Richtung und entfernt den deterministischen Fehlfall, aber die formulierte
  Garantie ist eine Zeitannahme; im Token-Setup bleibt ein Restfenster für einen falschen
  Erfolg.
- Vier kleine Nacharbeiten (RVW3-2…RVW3-5) plus vier Beleg-/Formhinweise (RVW3-6).

**Aufwand:** eng begrenzt — eine Entscheidung (A oder B) in D6/IC-7 plus
Formulierungspräzisierungen; keine Architektur-, Config- oder API-Änderung über das
bereits Beschlossene hinaus. **Kein `REJECT`:** Richtung (D1/D2/D3, read-only Fallback,
kein Token-Versand, lauter Abbruch) bleibt unstrittig.

**Nach Einarbeitung:** RVW3-1 (eine der beiden Auflösungen) und RVW3-2…RVW3-5 sind
ausreichend; ich bestätige die Freigabefähigkeit dann in einem Ein-Seiten-Vermerk, ohne
eine weitere Vollprüfung. Der Approval-Marker `Status: APPROVED (Datum)` wird
ausschließlich vom User gesetzt; erst dann schreitet
`quality_pipelines.concept-driven-dev` fort (specify → review → approve → plan) und der
Plan referenziert `spec-id: SPEC-1189-tmp-sink-pin-vs-system-temp`.

---

*Re-Review-Nachtrag, keine Umsetzung. Die geprüfte Spec wurde nicht verändert; es wurde
kein Code geschrieben und kein Commit erstellt.*
