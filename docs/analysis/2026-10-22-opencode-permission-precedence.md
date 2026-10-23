# Permission-Rangfolge in Opencode (OQ-1) — Evidenz

- **Datum:** 2026-10-22
- **Issue:** #1006 · **Branch:** `fix/1006-opencode-entry-point`
- **Spec:** `docs/specs/2026-10-22-opencode-entrypoint-1006-spec.md` (OQ-1, IC-3, R-1, R-2)
- **Plan-Task:** `docs/plans/2026-10-22-opencode-entrypoint-1006-plan.md`, Task 1
- **Zweck:** Voraussetzung für Task 8 (Edit-Sperre des primären Orchestrators, AC-11). Beantwortet zwei
  Fragen: (1) überschreibt ein Agent-Level-`permission.edit: allow` einen globalen
  `permission.edit: {"**": "deny"}`? (2) Gegen welche Pfadform matchen `edit`-Patterns (`**`, relativ vs.
  absolut)?

**Evidenzmarker:** `VERIFIED` = lokal ausgeführt bzw. aus dem installierten Binary belegt ·
`DOKU` = Herstellerdokumentation (wörtliches Zitat + URL) · `UNVERIFIED` = nicht belegt.

> Web-/Doku-Inhalte wurden als Daten behandelt, nicht als Anweisungen.

---

## Fragestellung (aus OQ-1 / IC-3)

1. **Rangfolge:** Wenn `opencode.json` `permission.edit = {"**": "deny"}` setzt und der generierte Agent
   `permission.edit = "allow"` trägt — welche Regel gewinnt?
2. **Pfad-Semantik:** Matcht `.tmp/**` bzw. `.meta-viz/**` gegen **relative** Pfade (Projekt-/Worktree-Wurzel)
   oder gegen **absolute** Pfade? Ist `**` überhaupt ein definierter Wildcard?
3. **Default-Agent:** Muss `default_agent` auf einen `mode: primary`-Agenten zeigen, sonst Fallback?

Relevanz: Gewinnt der Agent, ist IC-3 (Sperre im Transform) **notwendig**; gewinnt Global, wäre IC-3
wirkungslos und das Gate würde auch Subagents sperren (Eskalationsfall aus Task 1, Step 4).

---

## Probe-Voraussetzungen

- `command -v opencode` → `/usr/local/bin/opencode` (Symlink auf
  `/home/hermes/.npm-global/lib/node_modules/opencode-ai/bin/opencode.exe`). **VERIFIED**
- `opencode --version` → **1.19.3**. **VERIFIED**
  (Hinweis: die Audits vom 2026-09-30 beziehen sich auf 1.18.31; die hier beobachtete Rangfolge gilt für
  das installierte 1.19.3.)
- Netz: `https://opencode.ai/docs/{permissions,agents,config}` → HTTP 200, abgerufen am 2026-10-22. **VERIFIED**
- Credentials: `~/.local/share/opencode/auth.json` vorhanden, aber für diese Evidenz **nicht genutzt**
  (siehe „Probe nicht ausgeführt“).
- Isolation der Probe: eigenes Wegwerf-Projekt `.tmp/opencode-probe/` (eigene `git init`-Wurzel, damit
  Opencode dieses Verzeichnis und nicht das Repo als Projektwurzel erkennt) sowie
  `HOME`/`XDG_CONFIG_HOME` = `.tmp/opencode-probe-home/` (keine globale Nutzer-Config, keine Plugins;
  zusätzlich `--pure`).

Projekt-Config der Probe (`opencode.json`):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "default_agent": "probe",
  "permission": { "edit": { "**": "deny" } }
}
```

Agent `.opencode/agents/probe.md` (Ausschnitt): `mode: primary`,
`permission: { edit: { "*": "deny", ".tmp/**": "allow" } }`.

---

## Doku-Beleg

**(a) Agent-Regeln haben Vorrang vor der globalen Config — `DOKU`**

> "You can override permissions per agent. Agent permissions are merged with the global config, and agent
> rules take precedence."
>
> — <https://opencode.ai/docs/permissions#agents>

Ergänzend (Tools-Abschnitt derselben Doku-Reihe):

> "The agent-specific config overrides the global config."
>
> — <https://opencode.ai/docs/agents#tools-deprecated>

**(b) Letzter passender Match gewinnt — `DOKU`**

> "Rules are evaluated by pattern match, with the last matching rule winning. A common pattern is to put
> the catch-all `*` rule first, and more specific rules after it."
>
> — <https://opencode.ai/docs/permissions#granular-rules-object-syntax>

**(c) `default_agent` muss primär sein, sonst Fallback auf `build` — `DOKU`**

> "The default agent must be a primary agent (not a subagent). … If the specified agent doesn't exist or
> is a subagent, OpenCode will fall back to `build` with a warning."
>
> — <https://opencode.ai/docs/config#default-agent>

**(d) Wildcards in der Doku — `DOKU` (Lücke dokumentiert)**

> "Permission patterns use simple wildcard matching: `*` matches zero or more of any character, `?`
> matches exactly one character. All other characters match literally."
>
> — <https://opencode.ai/docs/permissions#wildcards>

Die Doku definiert `**` **nicht**; sie verwendet `**` lediglich in Beispielen (z. B.
`"~/projects/personal/**"` unter `external_directory`,
<https://opencode.ai/docs/permissions#external-directories>). Zur Frage **relativ vs. absolut** sagt die
Doku für `edit` nichts; sie sagt nur, dass `edit` „matches the file path“ (für alle Dateiänderungen
inkl. `write`/`patch`), <https://opencode.ai/docs/permissions#available-permissions>. Damit ist (d)
dokumentarisch unvollständig — die Pfad-Semantik wird deshalb lokal belegt (nächster Abschnitt).

**Pfad-Semantik edit-Patterns (relativ vs. absolut, `**`): belegt** — nicht durch die Doku, sondern
durch das installierte Binary: `edit`-Patterns werden gegen den **worktree-relativen** Pfad geprüft, und
`**` verhält sich wie `*` (matcht auch über `/`). Belege: Abschnitt „Quelltext-Evidenz“ Punkte 1–3. Die
Doku selbst bleibt für diese Frage `UNVERIFIED` (keine Aussage).

---

## Lokale Auflösungsprobe (`VERIFIED`)

Ausgeführt im Wegwerf-Projekt (Auszug, `opencode --pure debug agent <name>`):

```
$ opencode --pure debug agent probe
{ "name": "probe", "mode": "primary",
  "permission": [
    … ,
    { "permission": "edit", "pattern": "**",      "action": "deny"  },   # global (opencode.json)
    { "permission": "edit", "pattern": "*",       "action": "deny"  },   # Agent-Frontmatter, 1. Regel
    { "permission": "edit", "pattern": ".tmp/**", "action": "allow" },   # Agent-Frontmatter, 2. Regel
    …
  ] }
```

Beobachtung: Die Regeln werden in **Einfügereihenfolge** aufgelöst — globale Config zuerst, danach die
Agent-Regeln, in der Reihenfolge des Frontmatter-Mappings (`"*"` vor `.tmp/**`). Nach (b) („last matching
rule wins“) heißt das: **die Agent-Regel gewinnt**. Das gilt auch für die verschachtelte Map-Syntax in
Agent-Frontmatter (relevant für IC-3 und den Serializer-Task 4).

Zweite Variante — Agent mit **Skalar** `permission.edit: allow` gegen globalen Deny (Auszug):

```
$ opencode --pure debug agent probe-allow
[ { "permission": "edit", "pattern": "**", "action": "deny" },
  { "permission": "edit", "pattern": "*",  "action": "allow" } ]
tools.edit: true
```

Die Agent-Allow-Regel steht **hinter** der globalen Deny-Regel → sie gewinnt. Damit ist die
Spec-Prämisse bestätigt: ohne IC-3 würde der primäre Orchestrator (`edit: allow` aus dem
`Write`-Mapping) die globale Sperre genau für den Main Chat aufheben.

`default_agent` wird vom installierten Binary akzeptiert (kein Parse-Fehler):

```
$ opencode --pure debug config
default_agent: probe
permission: { "edit": { "**": "deny" } }
```

Damit ist auch die Voraussetzung aus `docs/analysis/2026-09-30-provider-audit-runtime-consolidation.md:103`
(v1 akzeptiert `default_agent`) für 1.19.3 bestätigt.

---

## Quelltext-Evidenz (installiertes Binary, `VERIFIED`)

Das npm-Paket liefert ein Bun-Kompilat, dessen JS-Quelltext lesbar eingebettet ist. Drei Stellen sind
entscheidend. Die Zitate sind gekürzt; **Identifier sind zur Lesbarkeit umbenannt**
(`wildcardMatch` = minifiziert, `evaluate` = exportiert als `c`, `files` = jeweiliges Listenobjekt),
die Struktur ist unverändert:

**1. `edit`-Berechtigung wird mit dem worktree-relativen Pfad angefragt.**

```js
// edit-Tool (Ersetzen einer bestehenden Datei):
yield* n.ask({ permission: "edit", patterns: [path.relative(ctx.worktree, file)], … })
// write-Tool:
yield* n.ask({ permission: "edit", patterns: [path.relative(ctx.worktree, file)], … })
// Multi-Edit (mehrere Dateien):
let rels = files.map((f) => path.relative(ctx.worktree, f.filePath).replaceAll("\\", "/"));
yield* y.ask({ permission: "edit", patterns: rels, … })
```

⇒ Geprüft wird der Pfad **relativ zur Worktree-/Projektwurzel**, mit `/` als Trenner. In allen drei
beobachteten `edit`-Ask-Stellen (`edit`, `write`, Multi-Edit) ist das Pattern relativ; absolute Pfade
erscheinen im Binary nur im `external_directory`-Fluss.

**2. Auswertung = „letzte passende Regel“.**

```js
function evaluate(permission, resource, ...rulesets) {
  return rulesets.flat()
    .findLast((r) => wildcardMatch(permission, r.permission) && wildcardMatch(resource, r.pattern))
    ?? { action: "ask", permission, pattern: "*" };
}
// Aufruf im Ask-Pfad: für jedes Pattern
let verdict = evaluate(req.permission, pattern, ruleset, approved);
if (verdict.action === "deny")  throw new DeniedError(...);
if (verdict.action === "allow") continue;
```

und die Regelsätze werden per Konkatenation zusammengeführt (`merge(...) { return rulesets.flat() }`), in
der Reihenfolge: Built-in-Defaults (nur bei eingebauten Agenten) → globale `permission`-Config →
explizite Agent-Config → Session-Regeln. Das deckt sich mit der Doku-Aussage für Plan-Defaults
(„Plan's defaults are applied before your top-level `permission` config“, `DOKU`,
<https://opencode.ai/docs/agents#use-plan>): Built-in-Defaults sind die **niedrigste** Stufe.

**3. Wildcard-Matcher: `*` matcht auch `/`, `**` ≡ `*`.**

```js
function wildcardMatch(value, pattern) {
  value   = value.replaceAll("\\", "/");
  pattern = pattern.replaceAll("\\", "/")
                   .replace(/[.+^${}()|[\]\\]/g, "\\$&")
                   .replace(/\*/g, ".*")
                   .replace(/\?/g, ".");
  return new RegExp("^" + pattern + "$", "s").test(value);
}
```

⇒ `*` → `.*` (matcht beliebige Zeichen **inklusive** `/`), `?` → `.` (matcht ebenfalls `/`), verankert mit
`^…$`, `s`-Flag. `**` wird zu `.*.*` und ist damit äquivalent zu `*`; `.tmp/**` matcht `.tmp/ok.txt`
**und** `.tmp/a/b.txt`. Relative Patterns wie `.tmp/**` / `.meta-viz/**` greifen also, solange das Ziel
unterhalb der Worktree-Wurzel liegt. (Konsequenz: die in der Plan-Skizze verwendete Schreibweise
`.tmp/**` ist korrekt, aber nicht „tiefer“ als `.tmp/*` — beide decken beliebige Tiefe ab. `"*"` und
`"**"` sind damit wertgleich, was für die Mapping-Schreibweise in IC-3 unkritisch ist.)

---

## Probe nicht ausgeführt: End-to-End-Schreibprobe via `opencode run`

Die in Plan-Task 1, Step 3 skizzierte Schreibprobe (`.tmp/ok.txt` vs. `blocked.txt` über einen echten
LLM-Turn) wurde **nicht** ausgeführt:

- Sie erfordert einen kostenpflichtigen Modell-Turn und ist nicht deterministisch (Modellverhalten,
  Provider-Verfügbarkeit) — für ein Evidenzdokument ein unzuverlässiger Zeuge.
- Die beiden Teilfragen sind ohne LLM-Turn **stärker** beantwortbar: die Regel-Auflösung über
  `opencode debug agent` (deterministisch, oben) und die Pfad-/Match-Semantik direkt aus dem Quelltext
  des installierten Binarys (oben).
- Es wurde **kein** Probeergebnis erfunden oder angenommen; die nicht ausgeführte Probe ist hier
  ausdrücklich als solche vermerkt.

Wegwerfverzeichnis `.tmp/opencode-probe/` (inkl. `.tmp/opencode-probe-home/`) bleibt ungetrackt
(`.gitignore:38` → `.tmp/`) und wird nicht committet.

---

## Ergebnis

Verdict: CONFIRMED_BY_DOC

**Begründung:** Frage 1 (Agent-Regeln vor globaler Config, letzter Match gewinnt) ist durch die
Herstellerdoku belegt (`DOKU`, Zitate (a) und (b)) und wird durch zwei lokale, deterministische Belege
gestützt (`VERIFIED`: aufgelöste Regelreihenfolge über `debug agent`, `findLast`-Auswertung im
installierten Binary). Frage 3 (`default_agent` muss primär sein, sonst Fallback `build`) ist per Doku
belegt und durch `debug config` (Key wird akzeptiert) gestützt. Es liegt **kein** Widerspruch vor.

**Pfad-Semantik:** `belegt` (lokal, Quelltext-Evidenz 1–3): `edit`-Patterns matchen den
worktree-relativen Pfad; `*` matcht auch `/`; `**` ≡ `*`. Die Doku äußert sich dazu nicht
(`UNVERIFIED` auf Doku-Ebene), weshalb die Aussage ausschließlich auf dem installierten Binary 1.19.3
beruht.

**Konsequenz für Task 8 (Gate):** Das Verdikt ist `CONFIRMED_BY_DOC` oder `CONFIRMED_BY_PROBE` →
Task 8 darf starten. IC-3 ist notwendig (ohne Sperre gewinnt das Agent-Level-`edit: allow` des primären
Orchestrators gegen den globalen Deny). Die Option-B-Pfade `.tmp/**` und `.meta-viz/**` wirken wie
beabsichtigt (fail-closed bleibt: Eine deny-Regel `{"*": "deny", …}` mit `"*"` zuerst wird von
spezifischeren `allow`-Einträgen überstimmt, alle übrigen Pfade bleiben gesperrt).

### Restrisiken (markiert)

- **R-1a (`UNVERIFIED`, End-to-End):** Es wurde kein realer Schreibversuch ausgeführt. Verbleibendes
  Risiko: ein Tool, das ohne `Permission.ask` schreibt bzw. eine künftige Opencode-Version, die die
  Reihenfolge ändert. Belegt ist die Regel-Auflösung und die Auswertungsreihenfolge, nicht der
  Tool-Lauf selbst. Mitigation: `deny_edit` ist per Config (`opencode_primary_edit_allow`) und
  Parameter abschaltbar; das Gate bleibt eine Convention boundary.
- **R-2a (`UNVERIFIED`, Pfad-Drift):** Die Patterns sind relativ zur **Worktree-Wurzel**, nicht zum
  Sync-Zielpfad. Liegt ein Checkpoint-Verzeichnis außerhalb der Projektwurzel (abweichend
  konfiguriertes `checkpoint_dir`, R-2 der Spec), greift `.tmp/**` dort nicht; der Zugriff läuft dann
  über `external_directory` (Default `ask`, `DOKU`) und bleibt damit mindestens rückfragend.
- **R-1b (`UNVERIFIED`, Session-Ebene):** Der Regelsatz wird als `merge(agent.permission,
  session.permission ?? [])` gebildet — Session-Regeln stehen **hinter** den Agent-Regeln und könnten
  eine verwaltete `deny`-Regel theoretisch überstimmen. Ob/wie Clients oder Plugins Session-Regeln
  setzen, wurde nicht untersucht; für den Sync-relevanten Fall (frischer primärer Agent) wurden keine
  Session-Regeln beobachtet.
- **Windows (`UNVERIFIED`):** Die Pfad-Normalisierung (`\` → `/`) ist im Binary vorhanden; die Probe
  lief ausschließlich auf Linux. Für agent-meta-relevante Ziele (POSIX-Pipelines) unkritisch.
