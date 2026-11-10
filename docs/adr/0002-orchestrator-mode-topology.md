# ADR 0002: Orchestrator `mode` × `topology` — Positionen, Gate-Zusagen und Defaults

- Status: Accepted
- Datum: 2026-11-09
- Bezug: #1190, `docs/specs/2026-11-09-orchestrator-mode-topology-design.md`

## Kontext

`orchestrator.mode` (`strict | advisory | main-chat`) und `orchestrator.topology`
(`primary | subagent | hybrid`, ungesetzt = abgeleitet) wurden an den Render-Seams
unterschiedlich aufgelöst: die Emission entschied über `effective`, das Rendering über
`declared`. Daraus folgten widersprüchliche Singleton-Aussagen („nur der `main_chat`
spawnt"), zwei Gate-Varianten in derselben Datei, ein doppelter P3-Status und ein
README, das die Topologie nicht auffindbar machte. Fünf Design-Entscheidungen
(D-Q1…D-Q5) und drei Nutzer-Entscheidungen (D-OQ1…D-OQ3) legen die Auflösung fest.

## Entscheidung

### D-Q1 — `mode: main-chat` + abgeleitetes `primary`: WARNING statt ERROR

**Entscheidung.** Ein ungesetztes `topology` leitet `primary` nur ab, wenn
`providers.<P>.primary-role` die Rolle nennt **und** sie im ActiveSet liegt; sonst
`subagent`. Unter `main-chat` ist die Ableitung inert und erzeugt genau eine WARNING
`orchestrator-topology.main-chat-derived-primary`. Gleicher-Scope-**deklariert**
bleibt ein harter ERROR.

**Konsequenz.** Bestandsprojekte mit `mode: main-chat` ohne `topology` brechen nicht
(rc bleibt 0), der dangling-Zustand wird aber sichtbar; der Renderpfad braucht ein
Inert-Signal, damit `main-chat` nicht weiter `ORCH_TOPOLOGY=primary` rendert.

### D-Q2 — `strict` × `primary` in einer Main-Chat-Session ist ein Nutzungsfehler

**Entscheidung.** Der nicht statisch entscheidbare Teil wird als Betriebsregel im
gerenderten Gate-Text ausgesprochen (Ausweg: `orchestrator.mode: main-chat` oder
`orchestrator.topology: subagent`). Der entscheidbare Teil wird zur WARNING
`orchestrator-topology.strict-primary-entry-mismatch` (`mode == strict` ∧
`effective == primary` ∧ `default_agent` zeigt nicht auf die Rolle).
`strict` × `subagent` (POS-2) bleibt zulässig und empfohlen — mit ehrlichem
`gate-inactive` statt Enforcement-Versprechen.

**Konsequenz.** Das Gate nennt die Topologie-Vorbedingung; Write-Scope-Lock und
Runtime-Deny existieren nur unter `primary`. `mode` geht ausschließlich in diese eine
Prüfung ein, der Resolver bleibt mode-agnostisch.

### D-Q3 — Genau eine Empfehlung je Surface

**Entscheidung.** `strict` × `subagent` (POS-2) ist auf v1, v2, Claude und Gemini die
einzige `RECOMMENDED`-Zelle. `strict` × `primary` (POS-3) bleibt gleichwertig
`ALLOWED` (0 Hop, echter Deny auf v1/v2, aber Session-Start-Bindung).
`advisory` × `subagent` ist nur mit dem #1182-Vorbehalt geführt.

**Konsequenz.** Jede Surface-Tabelle trägt eine Positions-Spalte; die Begründung der
Empfehlung ist Session-/Context-Ownership, nicht Enforcement. `hybrid` erscheint nur
als „degraded to `subagent`".

### D-Q4 — Der Hop ist eine Eigenschaft der Position, nicht von `strict`

**Entscheidung.** POS-3 = 0 Hop, POS-2 = 1 Hop, POS-1 = 0 Hop (aber kein
Orchestrator-State). Der Hop amortisiert sich ab M (3–8 Dateien); S (≤2 Dateien, kein
Architektur-Impact) geht direkt. Default für Single-User-Harness ist
`strict` × `subagent` (POS-2), POS-3 bleibt gleichwertig wählbar.

**Konsequenz.** Die Kostenangabe pro Hop ist als `ESTIMATE` (4–8k Tokens, nicht
gemessen) ausgewiesen; `strict` × `primary` kostet keinen zusätzlichen Modellaufruf,
verlangt aber, dass die Session tatsächlich im Orchestrator startet.

### D-Q5 — `direct-dispatch-enabled` unter `main-chat`: wirkungslos, nicht falsch

**Entscheidung.** Der Key ist unter `strict`/`advisory` wirksam und nur unter
`mode: main-chat` ohne Konsument. Dokumentieren + INFO
`orchestrator-strict.direct-dispatch-inert` (nur bei Key-**Präsenz**), kein
Validator-Fehler, kein rc-Einfluss, Kanal `--validate`-only.

**Konsequenz.** Kein Schema-Change; eine gültige, abwärtskompatible Config erzeugt
keinen Fehler. In diesem Repo (`strict`, Key gesetzt) entsteht kein Finding.

### D-OQ1 — Default dieses Repos: `strict` × `subagent`, explizit deklariert

**Entscheidung (`2026-11-09`).** Default ist `strict` × `subagent` (POS-2), künftig
per `orchestrator.topology: subagent` **explizit** deklariert (Umsetzung nach dem
Code-Fix). Beide Opencode-Positionen (`main-chat`, `subagent`) sind **first-class**,
`primary` ist die dritte, optionale Position.

**Konsequenz.** Die explizite Deklaration beseitigt die derived-vs-declared-Divergenz
und macht D-Q1 in diesem Repo gegenstandslos; es gibt keinen `position`-Key — die
Position folgt aus `mode` × `effective`.

### D-OQ2 — `strict` × `subagent` bleibt erlaubt und empfohlen, Gate-Tier je Surface

**Entscheidung (`2026-11-09`).** Kein Verbot und keine „nicht empfohlen"-Markierung;
pro Surface wird der **tatsächlich** greifende Gate-**Tier** ausgewiesen
(`hook` voll, `permission` PARTIAL, `plugin` observe + `permissions[]`-Deny). Opencode
generiert je Position sauber: POS-1 ohne dangling `default_agent`, POS-2 ohne
`mode: primary` mit ehrlichem `gate-inactive`, POS-3 als Session-Einstieg.

**Konsequenz.** Je Position existiert ein eigener Test (AC-33/AC-34/AC-35); die
Zusage wird auf den tragenden Tier heruntergebrochen statt `strict` als Erzwingung zu
verkaufen.

### D-OQ3 — `advisory` × `subagent` erst nach dem Fix von #1182

**Entscheidung (`2026-11-09`).** Die Team-Empfehlung `advisory` × `subagent` gilt erst
nach dem Fix von **#1182** (`context-profile: compact` bricht für `advisory` ab). Bis
dahin ist `strict` × `subagent` die belastbare Team-Empfehlung; Szenario `103` bleibt
`BLOCKED (#1182)`.

**Konsequenz.** Jede `advisory` × `subagent`-Zeile trägt den #1182-Vorbehalt
(AC-37); keine Doku-Stelle empfiehlt die Zelle ohne diesen Zusatz.

## Konsequenzen

- Die drei Positionen POS-1/POS-2/POS-3 sind das verbindliche Modell; `mode` ×
  `topology` → Position ist dokumentiert und getestet.
- Die elf Doku-Befunde B-1…B-11 aus #1190 §9.1 sind aufgelöst; die Doku-Tests pinnen
  Topologie-Qualifizierung, den einen P3-Status, die eine Gate-Variante und diesen ADR.
- Kein Produktionscode-Change durch diesen ADR; die Umsetzung bleibt Task des #1190-Plans.
