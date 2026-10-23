# Evidence — Ladeverhalten `opencode.json` + `opencode.jsonc`

- **Datum:** 2026-10-23 · **Repo:** `/home/hermes/repos/agent-meta` · **Branch/HEAD:** `feat/1007-c0-spike` @ `c0e6e8ff` (read-only, keine git-Mutation).
- **Anlass:** SPEC-PROVIDER-AUDIT-OPENCODE-V2 §3.9 (Entscheidung 11), AC-D8, Plan Task 24 (D3.1). Entscheidungsgrundlage für Task 26 (Entfernen von `opencode.jsonc` im Repo-Root).
- **Vorevidenz (v1):** `docs/analysis/evidence/2026-09-30-runtime-opencode-v1.md:98-111` — dort ist für v1 bereits belegt, dass beide Dateien geladen und gemerged werden und die damals voll auskommentierte `opencode.jsonc` nichts beiträgt (VERIFIED für v1).
- **Runtime:** `opencode --version` → `1.19.3` (einzige installierte Version; eine v2-Runtime stand nicht zur Verfügung).
- **Scratch:** `.tmp/oc-jsonc-probe/` (nicht committet, nicht gestaged). Jedes Probe-Verzeichnis ist per `git init` eigener Projekt-Root; `HOME` wurde auf `.tmp/oc-jsonc-probe/home` isoliert.
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
- **v2-Verhalten:** Für eine v2-Runtime (geänderte Settings-Oberfläche, `experimental.*`) wurde **keine** Probe ausgeführt — „Probe nicht ausgeführt: auf dem System ist nur `opencode 1.19.3` installiert, v2 stand nicht zur Verfügung.“ Die v2-Aussage stützt sich auf Spez §3.9/§3.2. → **UNVERIFIED** für v2, **DOKU** für die erwartete Gleichheit des Lade-/Merge-Verhaltens

---

## 5. Bewertung für Task 26 (Entfernen der Repo-`opencode.jsonc`)

| Aussage | Marker |
|---|---|
| Beide Dateien werden geladen (v1, 1.19.3) | VERIFIED |
| Ladereihenfolge JSON → JSONC | VERIFIED |
| Merge mit „JSONC gewinnt“ bei Konflikt-Keys | VERIFIED |
| Repo-`opencode.jsonc` enthält nur Kommentare + `$schema` | VERIFIED |
| Repo-`opencode.jsonc` fügt der aufgelösten Konfiguration nichts hinzu | VERIFIED |
| Kommentarverlust beim Rückschreiben einer JSONC-Datei | DOKU |
| v2-Laufzeitverhalten | UNVERIFIED (v2 nicht installiert) |

Damit ist die Entfernung der Repo-`opencode.jsonc` ohne Funktionsverlust möglich: die Datei trägt keinen Konfigurationsinhalt bei, und ihr einziger Key (`$schema`) ist in `opencode.json` bereits vorhanden. Für Konsumenten bleibt die Warnung aus Task 25 der Schutz, weil eine **inhaltstragende** JSONC-Datei die verwaltete JSON-Datei überschreiben würde.

ERGEBNIS: JSONC-TRAEGT-NICHTS-BEI
