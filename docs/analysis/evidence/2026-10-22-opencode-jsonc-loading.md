# Evidence — Ladeverhalten `opencode.json` + `opencode.jsonc`

- **Datum:** 2026-10-23 · **Repo:** `/home/hermes/repos/agent-meta` · **Branch/HEAD (Probe):** `feat/1007-c0-spike` @ `52a72a0f` (read-only, keine git-Mutation) · **Evidenz-Commit:** `31001cc1` · **Basis:** `9ccc27c8`.
- **Anlass:** SPEC-PROVIDER-AUDIT-OPENCODE-V2 §3.9 (Entscheidung 11), AC-D8, Plan Task 24 (D3.1). Entscheidungsgrundlage für Task 26 (Entfernen von `opencode.jsonc` im Repo-Root).
- **Vorevidenz (v1):** `docs/analysis/evidence/2026-09-30-runtime-opencode-v1.md:98-111` — dort ist für v1 bereits belegt, dass beide Dateien geladen und gemerged werden und die damals voll auskommentierte `opencode.jsonc` nichts beiträgt (VERIFIED für v1).
- **Runtimes:** v1 `opencode --version` → `1.19.3` (`/usr/local/bin/opencode`, vorinstalliert). v2 `.tmp/oc-v2-spike/node_modules/.bin/opencode --version` → `opencode v2.1.3` (Task-2-Install nach `.tmp/oc-v2-spike/`, siehe `docs/spikes/2026-10-22-issue-1007-opencode-v2-plugin-api-spike.md`); diese Runtime wird in §5 für eigene v2-Proben genutzt.
- **Scratch:** `.tmp/oc-jsonc-probe/` (v1) und `.tmp/oc-jsonc-v2-probe/` (v2), beide nicht committet, nicht gestaged. Jedes Probe-Verzeichnis ist per `git init` eigener Projekt-Root; `HOME`/`XDG_*` wurden auf `.tmp/oc-jsonc-v2-probe/home` isoliert.
- **Marker:** VERIFIED (eigener Lauf unten) / DOKU (Spez-/Vorevidenz, nicht erneut gemessen) / UNVERIFIED (nicht messbar).

---

## 1. Ausgangslage: die beiden Repo-Dateien

| Datei | Inhalt | Rolle |
|---|---|---|
| `opencode.json` | `$schema`, `subagent_depth: 3`, `plugin`, `mcp` (3 Server), `permission` (edit/bash `**` → deny) | aktive Projektkonfiguration, von `sync.py` verwaltet |
| `opencode.jsonc` | 14 Kommentarzeilen + `$schema` (einziger Key, gleicher Wert wie in `opencode.json`) | Kommentar-/Doku-Datei, nicht generiert (`grep` in `scripts/` findet keinen Schreiber — DOKU, siehe Spec §3.9.2) |

Damit ist die entscheidungsrelevante Frage nicht „wird JSONC geladen?“ (ja, siehe §2), sondern „trägt **diese** JSONC-Datei funktionalen Inhalt bei?“. Sie enthält ausschließlich Kommentare und den `$schema`-Zeiger; kein Konfigurationsschlüssel.

---

## 2. Probe: beide Dateien werden geladen, JSONC zuletzt

Drei Läufe in `.tmp/oc-jsonc-probe/` (Aufrufform):

```
$ cd .tmp/oc-jsonc-probe/r3
$ HOME=$PWD/../home opencode debug config --pure --print-logs --log-level DEBUG
```

Auszug `r3/err.txt` (Ladepfade; Pfadpräfixe gekürzt):

```
level=INFO message=loading path=<probe-home>/.config/opencode/config.json
level=INFO message=loading path=<probe-home>/.config/opencode/opencode.json
level=INFO message=loading path=<probe-home>/.config/opencode/opencode.jsonc
level=INFO message=loading path=<probe>/r3/opencode.json
level=INFO message=loading path=<probe>/r3/opencode.jsonc
```

**Aussage 1:** opencode 1.19.3 lädt globale und projektlokale `opencode.json` **und** `opencode.jsonc`. → **VERIFIED**

**Aussage 2:** Ladereihenfolge ist `…/opencode.json` → `…/opencode.jsonc` (JSONC nach JSON, innerhalb derselben Ebene). → **VERIFIED**

---

## 3. Merge und Konflikt: JSONC überschreibt JSON

Probe-Dateien in `r3` (beide im selben Verzeichnis, gleiche Keys, unterschiedliche Werte):

```
opencode.json   { "model": "probe/from-json",  "subagent_depth": 1 }
opencode.jsonc  { "model": "probe/from-jsonc", "subagent_depth": 2 }   // Kommentarzeile
```

Aufgelöste Konfiguration (`opencode debug config` als JSON, nur die relevanten Keys):

```
$ python3 -c "import json;d=json.load(open('out.txt'));print(d['model'],d['subagent_depth'])"
probe/from-jsonc 2
```

Der zweite Lauf `r2` (identische Werteverteilung, anderer Kommentartext/Reihenfolge im Dateisatz) liefert dasselbe Bild: `model = "probe/jsonc-only"`, `subagent_depth = 2` — also ebenfalls die JSONC-Werte. Die JSON-Datei diente jeweils als Baseline (`probe/from-json`, `subagent_depth: 1`).

**Aussage 3:** Beide Dateien werden gemerged; bei gleichem Key gewinnt der Wert aus `opencode.jsonc` (last write wins). → **VERIFIED**

**Konsequenz (abgeleitet, DOKU):** Eine inhaltstragende `opencode.jsonc` würde die von agent-meta verwaltete `opencode.json` teilweise überschreiben. Das ist genau das Shadowing-Risiko, gegen das die Dauer-WARNING `opencode-config-duplicate` (Task 25) schützt — für Konsumenten, nicht für dieses Repo.

---

## 4. Trägt die Repo-`opencode.jsonc` etwas bei?

- **Statisch:** Nach Entfernen der `//`-Zeilen bleibt `{ "$schema": "https://opencode.ai/config.json", }` — d. h. genau ein Metadaten-Key, dessen Wert identisch in `opencode.json` steht. Kein funktionaler Schlüssel (`model`, `mcp`, `permission`, `plugin`, `subagent_depth`, …) ist enthalten. → **VERIFIED** (Datei gelesen)
- **Dynamisch:** Lauf `r1` mit einer byte-identischen Kopie der Repo-`opencode.jsonc` neben der Repo-`opencode.json`: die Logzeilen zeigen beide Dateien als geladen, die aufgelöste Konfiguration enthält jedoch ausschließlich die Werte aus `opencode.json` (`subagent_depth = 3`, `mcp` mit 3 Servern, `permission` mit edit/bash-deny); aus der JSONC-Datei kommt kein zusätzlicher Key hinzu (in `r1/out.txt` sind 10 Top-Level-Keys, keiner davon aus der JSONC-Datei). → **VERIFIED**

Hinweis zur Isolation: `r1` wurde zunächst ohne eigenes `.git` angelegt; opencode lädt dann die Konfigurationen **aller** Elternverzeichnisse (bis zum Repo-Root) mit. Für `r2`/`r3` wurde deshalb im Probe-Verzeichnis `git init` ausgeführt — die Logs zeigen danach nur noch globale Konfiguration + Probe-Verzeichnis. Die Ladereihenfolge-/Merge-Aussagen stammen aus den sauberen Läufen `r2`/`r3`; `r1` dient nur als Zusatzbeleg für „Repo-JSONC trägt nichts bei“.

- **Kommentarverlust beim Rückschreiben:** agent-meta schreibt `opencode.json` ausschließlich über den Settings-Writer (JSON-Ausgabe); Kommentare einer JSONC-Datei würden bei einem Merge nicht erhalten. → **DOKU** (Spez R-4; im Probe nicht geprüft, da kein Schreibpfad ausgeführt wurde)
- **v2-Verhalten:** Die ursprüngliche Fassung dieses Dokuments führte hier „v2 stand nicht zur Verfügung“ — das war falsch: `opencode v2.1.3` wurde in Task 2 nach `.tmp/oc-v2-spike/` installiert und ist dort bis heute lauffähig. Die v2-Proben wurden nachgeholt, siehe §5. → **VERIFIED** für v2 (siehe §5); die frühere UNVERIFIED-Markierung ist damit ersetzt.

---

## 5. v2-Probe: `opencode v2.1.3`

Aufbau: `.tmp/oc-jsonc-v2-probe/` mit isoliertem `HOME`/`XDG_*` (`…/home`), `git init` in jedem Probe-Verzeichnis, Dienst-Port lokal auf `49631` gesetzt (`opencode service set port 49631`, danach `service stop`). Binary: `.tmp/oc-v2-spike/node_modules/.bin/opencode` → `opencode v2.1.3`.

**Wichtig zur Isolation (v2):** Anders als bei v1 (§4, Hinweis) stoppt `git init` im Probe-Verzeichnis den Aufwärtspfad in v2 **nicht**. Die Quellenliste enthält auch die Repo-Dateien `/home/hermes/repos/agent-meta/opencode.json` und `…/opencode.jsonc`. Die Probe-Dateien werden in der Ausgabe über ihren vollen Pfad unterschieden; die Bewertung unten bezieht sich ausschließlich auf die jeweiligen Probe-Pfade.

### 5.1 Beide Dateien werden geladen, JSONC nach JSON

Probe 1 — Verzeichnis `r1` mit `opencode.json` (`model: probe/from-json`, `subagent_depth: 1`) und `opencode.jsonc` (`model: probe/from-jsonc`, `subagent_depth: 2`):

```
$ cd .tmp/oc-jsonc-v2-probe/r1
$ HOME=…/oc-jsonc-v2-probe/home XDG_CONFIG_HOME=…/home/.config \
  XDG_DATA_HOME=…/home/.local/share XDG_CACHE_HOME=…/home/.cache \
  XDG_STATE_HOME=…/home/.local/state \
  .tmp/oc-v2-spike/node_modules/.bin/opencode debug config
```

Auszug (rc 0, Quellen in Ausgabereihenfolge; Pfadpräfixe gekürzt, nicht relevante `info`-Blöcke weggelassen, Umbrüche zur Lesbarkeit ergänzt):

```
{"type":"directory","path":"<probe-home>/.config/opencode"}
{"type":"document","path":"<repo>/opencode.json"}
{"type":"document","path":"<repo>/opencode.jsonc"}
{"type":"document","path":"<probe>/r1/opencode.json",
 "info":{"$schema":"https://opencode.ai/config.json",
         "model":{"providerID":"probe","model":"from-json"}}}
{"type":"document","path":"<probe>/r1/opencode.jsonc",
 "info":{"$schema":"https://opencode.ai/config.json",
         "model":{"providerID":"probe","model":"from-jsonc"}}}
{"type":"directory","path":"<repo>/.opencode"}
```

**Aussage 4:** opencode 2.1.3 lädt projektlokale `opencode.json` **und** `opencode.jsonc`; die JSONC-Datei wird als eigenes Dokument geparst und in der Quellenliste **nach** der JSON-Datei geführt (Reihenfolge JSON → JSONC wie in v1). → **VERIFIED**

**Nebenbefund (nicht entscheidungsrelevant):** `subagent_depth` erscheint in v2 in keinem der beiden geparsten `info`-Blöcke — v2 kennt den v1-Key nicht und verwirft ihn beim Parsen. Das betrifft die Settings-Oberfläche, nicht die JSONC-Frage.

### 5.2 Was gewinnt bei Konflikt-Keys? (v2)

`opencode debug config` listet in v2 **Quellen und deren geparsten Inhalt**, nicht die gemergte Endkonfiguration. Probe 2 — zusätzlicher Lauf in `r1` mit `opencode run --standalone "ping"` (isolierte `HOME`, Default-Modell) lief durch:

```
STATUS: done · RESULT: pong — orchestrator online, no delegation needed for a health-check · ARTIFACTS: none
> orchestrator · big-pickle
```

Der Lauf zeigt, dass v2 die Konfiguration auflöst, belegt aber **nicht**, welcher der beiden konkurrierenden `model`-Werte gewinnt: v2 wählte das Default-Modell `big-pickle`, nicht `probe/from-json` oder `probe/from-jsonc` (die Provider `probe/*` existieren nicht). Ein belastbarer Merge-Nachweis für v2 fehlt daher.

**Aussage 5:** Der Merge-Gewinner bei gleichem Key („JSONC gewinnt“) ist für v2 mit dem vorhandenen Aufwand **nicht gemessen**. → **UNVERIFIED** für v2 (für v1 siehe §3: VERIFIED). Die Entscheidung in §6 hängt nicht davon ab, weil die Repo-JSONC keinen Konflikt-Key enthält.

### 5.3 Trägt die Repo-`opencode.jsonc` unter v2 etwas bei?

Probe 3 — Verzeichnis `r2` mit byte-identischen Kopien der Repo-`opencode.json` und `opencode.jsonc` (eigenes `git init`), gleicher Aufruf wie 5.1. Geparste Top-Level-Keys je Dokument, aus `r2/out.txt` extrahiert (sortiert):

```
document <probe>/r2/opencode.json   keys: ['$schema', 'default_agent', 'mcp', 'permissions', 'plugins']
document <probe>/r2/opencode.jsonc  keys: ['$schema']
```

**Aussage 6:** v2 parst die Repo-`opencode.jsonc` zu genau einem Key (`$schema`, identischer Wert wie in `opencode.json`); sie bringt keinen funktionalen Schlüssel (`model`, `mcp`, `permissions`, `plugins`, `default_agent`, …) ein. → **VERIFIED**

**Aussage 7:** Damit trägt die Repo-`opencode.jsonc` auch unter v2.1.3 nichts zur aufgelösten Konfiguration bei. → **VERIFIED**

---

## 6. Bewertung für Task 26 (Entfernen der Repo-`opencode.jsonc`)

| Aussage | Marker |
|---|---|
| Beide Dateien werden geladen (v1, 1.19.3) | VERIFIED |
| Ladereihenfolge JSON → JSONC (v1) | VERIFIED |
| Merge mit „JSONC gewinnt“ bei Konflikt-Keys (v1) | VERIFIED |
| Repo-`opencode.jsonc` enthält nur Kommentare + `$schema` | VERIFIED |
| Repo-`opencode.jsonc` fügt der aufgelösten Konfiguration nichts hinzu (v1) | VERIFIED |
| Beide Dateien werden geladen (v2, 2.1.3) | VERIFIED |
| Ladereihenfolge JSON → JSONC (v2) | VERIFIED |
| Merge mit „JSONC gewinnt“ bei Konflikt-Keys (v2) | UNVERIFIED (debug config zeigt Quellen, nicht das Merge-Ergebnis) |
| Repo-`opencode.jsonc` fügt der aufgelösten Konfiguration nichts hinzu (v2.1.3) | VERIFIED |
| Kommentarverlust beim Rückschreiben einer JSONC-Datei | DOKU |

Damit ist die Entfernung der Repo-`opencode.jsonc` ohne Funktionsverlust möglich: die Datei trägt keinen Konfigurationsinhalt bei, und ihr einziger Key (`$schema`) ist in `opencode.json` bereits vorhanden. Die v2-Probe (§5) bestätigt das für `opencode 2.1.3`; der frühere v2-Vorbehalt („v2 nicht installiert“) war eine falsche Prämisse. Offen bleibt nur die v2-Merge-Semantik bei echten Konflikt-Keys — sie ist für diese Entscheidung irrelevant, weil die Repo-JSONC keinen solchen Key besitzt. Für Konsumenten bleibt die Warnung aus Task 25 der Schutz, weil eine **inhaltstragende** JSONC-Datei die verwaltete JSON-Datei überschreiben würde.

**Fazit:** Die v2-Proben bestätigen die v1-Bewertung; der Wert der Ergebniszeile bleibt unverändert.

ERGEBNIS: JSONC-TRAEGT-NICHTS-BEI
