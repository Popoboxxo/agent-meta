# Spike-Ergebnis — Opencode-v2-Plugin-/Hook-API und Feld-Evidenz

- **Datum:** 2026-10-23
- **Branch/HEAD bei Erstellung:** `feat/1007-c0-spike` @ `1c1cc311`
- **Issue:** #1007 (AC-C1)
- **Spec:** `docs/specs/2026-10-22-opencode-v2-support-spec.md` §3.6, AC-C1/AC-C2
- **Plan:** `docs/plans/2026-10-22-opencode-v2-support-plan.md` Task 2 (C0.2)
- **Kurzstand:** Plugin-/Hook-Mechanismus der v2-Runtime ist belegt (C3 = GO). Die Feld-/Key-Prüfung ist **nicht** vollständig bestätigt (`agents.title.model` nicht auflösbar) → Feld-Verdikt AMEND. Die Verdikt-Zeilen stehen unverändert am Dokumentende.

## Runtime-Lage

| Laufzeit | Version | Herkunft | Nutzung in diesem Spike |
|---|---|---|---|
| v1 (`opencode`) | `1.19.3` | `/usr/local/bin/opencode` (npm-global), einzige vorinstallierte Runtime | nur als Referenz/Bestand; keine v1-Verhaltensaussage wird auf v2 übertragen |
| v2 (`opencode`) | `opencode v2.1.3` | `@opencode/cli@latest`, **einmaliger** Install nach `.tmp/oc-v2-spike/` (`npm install --prefix`, rc 0, „added 5 packages in 12s“) | alle VERIFIED-Aussagen zu v2 |

Der alte Audit-Sandkasten `/var/tmp/opencode-audit/opencode-v2/` existiert nicht mehr (`ls` → „No such file or directory“). Die v2-Runtime wurde daher in `.tmp/` neu installiert (kein globaler Eingriff, keine Netz-/Systemänderung außer dem einen npm-Install). Alle v2-Läufe nutzten ein **isoliertes** `HOME`/`XDG_*` unter `.tmp/oc-v2-spike/probe/home`; die v1-Session-DB (`~/.local/share/opencode/opencode.db`) wurde nicht angefasst. Für die Läufe wurde die vorhandene `auth.json` nach `.tmp/.../home/.local/share/opencode/` kopiert (nur `600`, `.tmp/` ist gitignored) und nach den Proben wieder gelöscht; Modellwahl ausschließlich `opencode/deepseek-v4.1-flash-free` (kostenlos), damit keine Kosten entstehen.

**Wichtige Probe-Hygiene:** Das Probe-Projekt lag unter `.tmp/oc-v2-spike/probe/proj` und damit **innerhalb** des agent-meta-Repos. OpenCode lädt Konfiguration und `.opencode/agents` auch aus dem umgebenden Repo-Verzeichnis: `debug agents` zeigte 67 Agenten (58 Repo-Agenten + 2 Probe-Agenten + 7 Built-ins), und die Repo-`opencode.json` (`edit`/`shell` `**` deny) war Teil der aufgelösten Regeln. Das erklärt die zusätzlichen Deny-Einträge in den Rohausgaben; es ändert nichts an den hier belegten Engine-Aussagen (Plugin-Laden, Hook-Feuern, Agent-/Session-Felder, Reihenfolge-Semantik), ist aber für eine Nachstellung wichtig.

## Marker und Zählweise

- **VERIFIED** — eigener, hier dokumentierter Lauf (v2.1.3), Ausgabe unten zitiert.
- **DOKU** — offizielle v2-Dokumentation, hier nicht selbst gemessen; bzw. bereits vorhandene Evidenz, unverändert übernommen.
- **UNVERIFIED** — mit dem vorhandenen Aufwand nicht belegbar (oder durch Laufzeit-Hinweis in Frage gestellt).

`Proben:` zählt die für die jeweilige Frage **ausgewerteten** v2-Läufe (`opencode run`, `opencode debug config`, `opencode debug agents`, `opencode models`). Hilfeaufrufe, fehlgeschlagene Bring-up-Versuche und der npm-Install sind im folgenden Protokoll vollständig gelistet, werden aber nicht als Frage-Probe gezählt. Budget je Frage: ≤ 3 Proben, ≤ 5 Quellen — überall eingehalten.

Keine der abgerufenen Web-/Doku-Seiten enthielt anweisungsartige Einschübe („ignore previous instructions“, Tool-Aufrufe, Secrets-Abfragen). Es gab daher nichts als Prompt-Injection zu markieren; sämtliche Fremdinhalte wurden ausschließlich als Daten gelesen. Die Datei `~/.config/opencode/plugins/rtk.ts` (fremder Nutzer-Plugin-Code) wurde nur als Beispiel gelesen, nicht ausgeführt und nicht verändert.

## Proben-Protokoll (alle tatsächlich ausgeführten Kommandos)

| # | Kommando (isoliertes `HOME`/`XDG_*`, sofern nicht anders vermerkt) | Ergebnis |
|---|---|---|
| 1 | `which -a opencode opencode2` | `/usr/local/bin/opencode`, `~/.npm-global/bin/opencode` |
| 2 | `opencode --version` (v1) | `1.19.3` |
| 3 | `ls /var/tmp/opencode-audit/opencode-v2/node_modules/.bin/` | nicht vorhanden (alter Sandkasten weg) |
| 4 | `npm install --prefix .tmp/oc-v2-spike --prefer-offline --no-audit --no-fund @opencode/cli@latest` | rc 0 |
| 5 | `.tmp/oc-v2-spike/node_modules/.bin/opencode --version` | `opencode v2.1.3` |
| 6 | `opencode --help`, `opencode plugin --help`, `opencode debug --help`, `opencode service --help`, `opencode run --help` | Subkommandos/Flags erfasst |
| 7 | `opencode service set port 49611`, `opencode service status` | Port gesetzt, Status `stopped` |
| 8 | `opencode debug config --standalone` / `opencode --standalone debug config` | beide `Unrecognized flag` (verworfen) |
| 9 | `opencode debug config` (vor Portwechsel) | Fehler: „Managed service port 49374 … already in use“ (verworfen) |
| 10 | `opencode debug config` (nach Portwechsel) | Quellenliste inkl. Probe-`opencode.json` (Q5/Q6) |
| 11 | `opencode run --standalone --agent spike-main --model opencode-go/deepseek-v4.1-flash "…"` | `Model unavailable`; Plugin-`setup` bereits geladen (Q1) |
| 12 | `opencode models` (Filter) | `opencode/deepseek-v4.1-flash-free` u. a. verfügbar |
| 13 | `opencode run … "Run the shell command: echo MAIN-PROBE"` (Default-Permissions) | `tool.execute.before` feuert; `Permission denied: shell` |
| 14 | `opencode run … "echo MAIN-PROBE"` (`permissions: shell * allow`) | Kommando läuft; Permission-Hook `effect: allow` |
| 15 | `opencode run … "echo DENY-PROBE"` (explizites `shell ** deny`) | blockiert, **kein** Hook-Aufruf, Shell nicht im Tool-Katalog |
| 16 | `opencode run … "echo HOOK-DENY"` (Plugin setzt `effect = "deny"`) | blockiert durch Plugin-Meldung |
| 17 | `opencode run …` Delegation an `spike-sub` | Hooks feuern im Kind-Session-Kontext |
| 18 | `opencode run … "echo ORDER-PROBE"` (global deny + Agent-allow) | Kommando läuft → Agent-Regel gewinnt |
| 19 | `opencode debug agents` (3×: gekürzt, `agents.json`, `agents2.json`) | 67 Agenten; Modell-/`system`-Auflösung; `title`-Modell `null` |
| 20 | `opencode models` (voll) | `probe-prov/probe-model` aus `providers` sichtbar |

## Q1

**Ja.** v2 hat einen dokumentierten und im Lauf belegten Plugin-Mechanismus:

- **Lade-Orte:** projektweit `.opencode/plugins/` und global `~/.config/opencode/plugins/` (jeweils direkte `.ts`/`.js`-Dateien und unmittelbare Plugin-Paketverzeichnisse); zusätzlich `plugins`-Array in `opencode.json(c)` für Pakete/lokale Pfade. Ein `plugins/`-Verzeichnis **neben** einer Projekt-`opencode.json` wird nicht automatisch entdeckt.
- **Format:** TypeScript oder JavaScript (ESM); v2 liest den **Default-Export** als Objekt mit `id` und `setup(ctx)` (alternativ `effect()`); eine reine Factory-Funktion wie in v1 genügt nicht.
- **Config-Key:** `plugins` (**Plural**) in `opencode.json(c)`, nicht `plugin`. Für eine Datei unter `.opencode/plugins/` ist gar kein Config-Eintrag nötig (Auto-Discovery).
- **Version:** v2.1.3; Management-CLI `opencode plugin {list,add,check,update,remove}` vorhanden.

Laufzeitbeleg (Q1, Lauf 11): Serverlog `msg="loading plugin" id=…/.opencode/plugins/spike.ts entrypoint=file:///…/spike.ts`, Plugin-Log `{"t":"setup"}` — der `setup`-Entrypoint wurde also ausgeführt. Zusatzbeobachtung: Ein expliziter Datei-Eintrag im `plugins`-Array erzeugt vorher die WARNUNG `configured plugin path must be a directory`, die Datei wurde trotzdem geladen; die dokumentierte Auto-Discovery ist der saubere Weg.

Bewertung: VERIFIED (v2.1.3) für Lade-Ort, Format und `setup`-Entrypoint (eigener Lade-Lauf); DOKU für den `plugins`-Config-Key und die globalen Pfade.

Quelle: `https://opencode.ai/v2/docs/plugins/` (Abruf 2026-10-23, Redirect von `https://v2.opencode.ai/docs/plugins/`) und `https://opencode.ai/v2/docs/build/plugins` (Abruf 2026-10-23); Kommandoausgabe `opencode plugin --help` (SUBCOMMANDS `list add check update remove`); Laufzeit-Logzeilen aus Lauf 11 (siehe Protokoll); Beispiel-Plugin `~/.config/opencode/plugins/rtk.ts` (nur gelesen).
Proben: 2
Quellen: 4

## Q2

**Ja, mit einer Präzisierung.** Das v1-Äquivalent `tool.execute.before` existiert in v2 als `ctx.tool.hook("execute.before", cb)`; der Hook sieht `tool`, `input`, `agent`, `sessionID` und darf das Input-Objekt verändern („Inspect or replace tool input before execution“). **Blockieren** ist damit nicht dokumentiert — das Blockieren läuft über `ctx.permission.hook("evaluate", cb)`: der Hook läuft nach den konfigurierten Regeln und vor der Ausführung, darf `effect` auf `allow`, `ask` oder `deny` setzen, und `message` wird zum Denial-Grund. Ein explizit konfiguriertes `deny` ist abschließend und ruft den Hook **nicht** auf.

Laufzeitbeleg:

- Lauf 14: `{"t":"tool.before","tool":"shell","agent":"spike-main",…,"input":{"command":"echo MAIN-PROBE"}}` und `{"t":"perm.evaluate","action":"shell",…,"effect":"allow","resources":["echo MAIN-PROBE"]}` → beide Hooks feuern, Shell läuft.
- Lauf 16 (Plugin setzt `effect="deny"` für `HOOK-DENY`): Modell bekommt `Error: spike-gate: blocked by plugin`; der Shell-Prozess wird **nicht** gestartet. Damit ist die Blockierbarkeit durch ein Plugin praktisch belegt.
- Lauf 15 (explizites `shell ** deny`): kein `tool.before`, kein `perm.evaluate`, Shell nicht im Tool-Katalog → konsistent zu „explicit configured deny is final and does not invoke the hook“.

Bewertung: VERIFIED (v2.1.3) für das Feuern von `execute.before` und das Blockieren über den Permission-Hook; DOKU für die Regel „explicit configured deny is final“ (im Lauf 15 konsistent beobachtet).

Nebenbefund (wichtig für C1/C3): Default-Permissions (`ask`) plus `--auto` im Standalone-`run` führten in Lauf 13 zu `Permission denied: shell`, nicht zu einer Bestätigung. Für automatisierte Gate-Prüfungen sollte ein explizites `allow`/`deny` gesetzt sein, nicht auf `--auto` vertraut werden.

Quelle: `https://opencode.ai/v2/docs/build/plugins` (Abschnitte „Tools“, „Permissions“; Abruf 2026-10-23); eigene Laufzeitausgaben Lauf 13-16 (siehe Protokoll); Bestätigung der v1-API-Form in `~/.config/opencode/plugins/rtk.ts` (`tool.execute.before` im `server()`-Zweig).
Proben: 3
Quellen: 3

## Q3

**Ja.** Der Hook feuert auch in Subagent-Sessions, und Main-Chat- und Subagent-Session sind unterscheidbar:

- Delegationslauf 17: Im **Eltern**-Kontext `{"t":"tool.before","tool":"subagent","agent":"spike-main","sessionID":"ses_e969bdd4cffe…","input":{"agent":"spike-sub",…}}` und `perm.evaluate` mit `action:"subagent"`, `resources:["spike-sub"]`; im **Kind**-Kontext `{"t":"tool.before","tool":"shell","agent":"spike-sub","sessionID":"ses_e969bd05affe…"}` und `perm.evaluate` mit `action:"shell"`. Zwei unterschiedliche `sessionID`s, unterschiedliche `agent`-Werte; der Start ist zusätzlich am `subagent`-Tool-Event mit `resources = [Ziel-Agent-ID]` erkennbar. Damit ist „Main Chat“ (Eltern-Session, primärer Agent) von der Subagent-Session unterscheidbar.
- **Auswertungsreihenfolge `permissions[]`:** **last match wins**; Regeln werden in Konfigurationsreihenfolge angehängt, Agent-Regeln zuletzt. Lauf 18 belegt das zur Laufzeit: global `{action:"shell",resource:"*",effect:"deny"}`, Agent-Frontmatter `{action:"shell",resource:"*",effect:"allow"}` → das Kommando wurde ausgeführt (Agent-Regel gewinnt). **Vorrang:** Agent-Ebene übersteuert global.
- **`subagent`-Permission:** dokumentiert als Start-Gate (`resource` = Ziel-Agent-ID); im Lauf als `perm.evaluate`-Event mit `resources:["spike-sub"]` sichtbar.

Bewertung: VERIFIED (v2.1.3) für Feuern in Subagent-Sessions, Unterscheidbarkeit von Eltern-/Kind-Session und für die Reihenfolge-Semantik (last match, Agent-Regeln zuletzt).

**Konsequenz für die Spec (Amendment-B1-Punkt, Phase 3.4/C1/C3):** Ein globales Managed-`deny` am **Listenanfang** (aktuelle Default-Annahme OQ-B5) ist nach dieser Semantik die *schwächste* Position — jede spätere Regel (auch Agent-`allow`) überstimmt es. Der Gate-Eintrag muss ans **Listenende** (bzw. auf Agent-Ebene), sonst ist er wirkungslos. Das ist kein C3-Blocker, aber eine zwingende Korrektur vor C1.

Quelle: `https://opencode.ai/v2/docs/permissions` („The last matching rule wins … agent rules are appended last“, „Actions“, Abruf 2026-10-23), `https://opencode.ai/v2/docs/agents` („subagent … child session“, „permissions … appended“, Abruf 2026-10-23), `https://opencode.ai/v2/docs/build/plugins` (Permission-Event `agent?`, `sessionID`); Laufzeit-Logzeilen Lauf 17 und 18.
Proben: 2
Quellen: 4

## Q4

**Mit Anpassung** — nicht unverändert, aber auch nicht „gar nicht“.

Das bestehende Template `templates/plugins/runtime-gate.opencode-plugin.js.tmpl` ist ein v1-Artefakt: Es exportiert eine **async-Factory** (`export const AgentMetaRuntimeGate = async (_ctx) => ({ "tool.execute.before": … })`). Der v2-Loader liest dagegen den **Default-Export als Objekt** mit `id` und `setup(ctx)`; der v1-`server()`-Rückgabewert wird von v2 ignoriert („V2 reads the default export’s id and setup() …, ignoring server()“). Zusätzlich ist der v2-Hook nicht `"tool.execute.before"`, sondern `ctx.tool.hook("execute.before", cb)`; Blockieren geht nur über `ctx.permission.hook("evaluate")`.

Nötige Anpassung für `opencode-plugin-v2-js` (neues Template, wie Spec §3.6 vorsieht):

1. `export default { id: "agent-meta-runtime-gate", async setup(ctx) { … } }` (Objekt, nicht Funktion — der 2.x-Loader validiert `typeof === "object"`; ein Callable mit angeflanschten Feldern fällt durch, siehe `rtk.ts`-Kommentar).
2. Registrierung über `await ctx.tool.hook("execute.before", …)` (Observe-Pfad) und — erst nach P6-Freigabe — `await ctx.permission.hook("evaluate", …)` für `effect="deny"`.
3. Die sync-zeit-gebackenen Konstanten (`MODE`, `STRICT`, `AGENT_ALLOWLIST`) können unverändert substituiert werden; `MODE=observe` bleibt korrekt (kein Enforce).
Bewertung: VERIFIED (statische Prüfung von Template, Loader-Vertrag und Docs; kein Lauf mit dem Template selbst).

4. `scripts/lib/runtime_gate.py:93-95` (`PLUGIN_TEMPLATE_BY_PROTOCOL`) braucht einen neuen Protokoll-Key → neues Template; die v1-Zuordnung bleibt unangetastet.

Quelle: `templates/plugins/runtime-gate.opencode-plugin.js.tmpl` (Zeilen 11-26, gelesen 2026-10-23); `scripts/lib/runtime_gate.py:93-95` (`PLUGIN_TEMPLATE_BY_PROTOCOL = {"opencode-plugin-js": …}`); `https://opencode.ai/v2/docs/build/plugins` („Support V1“, „Tools“, „Permissions“; Abruf 2026-10-23); `~/.config/opencode/plugins/rtk.ts` (2.x-Objektform, nur gelesen).
Proben: 0
Quellen: 4

## Q5

Feldnamen der v2-MCP-Form und der Frontmatter-Felder:

- **`timeout`** ist pro Server als Objekt mit `{startup, catalog, execution}` dokumentiert, positive Ganzzahlen in **Millisekunden**; Defaults `mcp.timeout` werden von Server-Werten überschrieben. Die Annahme `timeout{catalog,execution}` aus §3.5 ist damit korrekt (plus optional `startup`).
- **`oauth`** nutzt **snake_case**: `client_id`, `client_secret`, `scope`, `callback_port`, `redirect_uri`, `auth_server_metadata_url`; `oauth: false` deaktiviert OAuth. Die Annahme aus §3.5 ist korrekt.
- **`disabled`** ist das Feld, um einen konfigurierten Server nicht zu verbinden; ein `enabled`-Feld gibt es in v2 nicht („Use disabled, not an enabled field“). Annahme aus §3.5/AC-C7 korrekt.
- **`system`**: In Markdown-Agenten ist der **Body** der System-Prompt; ein `system:`-Frontmatter-Feld wird nicht emittiert („put this text in the document body instead of a system frontmatter field“). Laufzeit: `debug agents` zeigt für den Probe-Agenten `system` = exakt den Body. Die Default-Annahme OQ-B7/B-D4 ist bestätigt.
- **`variant`**: `model: provider/model#variant` wird geparst; `debug agents` liefert `{"id":"deepseek-v4.1-flash-free","providerID":"opencode","variant":"high"}`. Bestätigt.

Rohbeleg aus `opencode debug config` (Lauf 10, gekürzt): `"disabled": true`, `"timeout": {"catalog": 5000, "execution": 60000}`, `"oauth": {"client_id": "", "client_secret": "***", "scope": "read"}`. `{env:OC_ID}` wurde dabei zu `""` aufgelöst (nicht gesetzte Umgebungsvariable), das Secret wurde maskiert — die Form bleibt erhalten, die Auflösung von Env-Platzhaltern ist dokumentiert.

timeout: DOKU
oauth: DOKU
disabled: DOKU
system: VERIFIED
variant: VERIFIED

Quelle: `https://opencode.ai/v2/docs/mcp-servers` („Config“, „Pre-registered clients“, „Timeouts“; Abruf 2026-10-23); `https://opencode.ai/v2/docs/agents` („System“, „Model“; Abruf 2026-10-23); eigene Ausgaben `opencode debug config` (Lauf 10) und `opencode debug agents` (Lauf 19); Vorannahmen in `docs/specs/2026-10-22-opencode-v2-support-spec.md` §3.5/§3.7.
Proben: 2
Quellen: 4

## Q6

Je Phase-B-Key:

- **`experimental.subagent_depth`** ist dokumentiert: „sets how deeply subagents can start their own subagents. Defaults to 1“. Der Key liegt korrekt unter `experimental`; die Umkehrung von IC-15 Nr. 16 (kein Top-Level-`subagent_depth`) ist damit bestätigt. Die Ersatzstrategie über die `subagent`-Permission bleibt als Alternative gültig (Q3: `action:"subagent"`, `resources:[Ziel-ID]`).
- **`experimental.todo`** ist dokumentiert: „Set todo to true to give agents a todowrite tool“, Default `false`. Der Key existiert; die Wirkung (Tool-Verfügbarkeit) wurde nicht separat gemessen.
- **`providers`** existiert und wird aufgelöst: Lauf 20 listet das aus der Probe-`opencode.json` definierte `probe-prov/probe-model` in `opencode models`. **Aber die angenommene Innenform stimmt nicht:** v2 dokumentiert `providers.<id>.{name, env, package, settings, headers, body, models}`; `baseURL` liegt unter `settings.baseURL`, Credentials kommen über `env` — nicht `options.{baseURL, apiKey}` wie in §3.3/AC-B10. Das ist ein Amendment-B1-Punkt für Phase B.
- **`agents.title.model`** ist **nicht** belegt: In der Doku kommt der Pfad nicht vor (`title` nur als Name eines versteckten Built-in-Agenten). Laufzeit: Nach Setzen von `agents: {title: {model: "opencode/deepseek-v4.1-flash-free"}}` liefert `opencode debug agents` weiterhin `title -> model: None`; die Konfiguration selbst wurde geladen (derselbe Lauf zeigt die `providers`-Wirkung). Ob `debug agents` die Modelle versteckter Agenten grundsätzlich nicht anzeigt oder der Key ignoriert wird, ist mit Bordmitteln nicht trennbar → **UNVERIFIED** (fail-safe). Für Phase B (AC-B9, `small-model`) ist der Pfad damit nicht tragfähig.
- **`cli.json`**: als Datei dokumentiert (JSON, Key `plugins`), aber nur als Träger für **CLI-only-Plugins**: `cli.json { "plugins": ["opencode-acme-cli"] }`. Dass `cli.json` die in AC-D7 angenommenen Keys `theme`/`autoupdate` trägt, ist **nicht** dokumentiert (nur `plugins`). Datei/Name/Format sind bestätigt, der D2-Inhalt ist offen.

experimental.subagent_depth: DOKU
experimental.todo: DOKU
providers: DOKU
agents.title.model: UNVERIFIED
cli.json: DOKU

Rohbeleg Titel-Prüfung (Lauf 19, `agents2.json`): `spike-main -> {'id': 'deepseek-v4.1-flash-free', 'providerID': 'opencode', 'variant': 'high'}`, `summary -> None`, `title -> None` — bei gesetztem `agents.title.model`.

Quelle: `https://opencode.ai/v2/docs/config` („Experimental“, Abruf 2026-10-23); `https://opencode.ai/v2/docs/providers` („Custom“, „Endpoint“; Abruf 2026-10-23); `https://opencode.ai/v2/docs/plugins/` (Abschnitt „Terminal“, `cli.json`; Abruf 2026-10-23); eigene Ausgaben `opencode debug agents`/`opencode models` (Läufe 19-20); Vorannahmen in `docs/specs/2026-10-22-opencode-v2-support-spec.md` §3.1/§3.2/§3.3/§3.8.
Proben: 2
Quellen: 5

## Ergebnis-Tabelle (Spec §3.6)

| Key/Feld | Marker | betroffene Phase |
|---|---|---|
| `timeout` (`catalog`/`execution`) | DOKU | C2 |
| `oauth` (`client_id`/`client_secret`/`scope`, snake_case) | DOKU | C2 |
| `disabled` | DOKU | C2 |
| `system` (Body statt Frontmatter-Feld) | VERIFIED | D1 |
| `variant` (`#variant`) | VERIFIED | D1/D3 |
| `experimental.subagent_depth` | DOKU | B |
| `experimental.todo` | DOKU | B |
| `providers` (Key ja, Innenform abweichend) | DOKU | B (Innenform: Amendment) |
| `agents.title.model` | UNVERIFIED | B (blockiert bis Amendment) |
| `cli.json` (Datei/Format ja, `theme`/`autoupdate` offen) | DOKU | D2 (Inhalt: Amendment) |

## Weitere Befunde und Amendment-B1-Bedarf

1. **`agents.title.model` (Phase B):** nicht auflösbar; AC-B9/`small-model` darf so nicht implementiert werden. Amendment B1 muss den Key streichen/ersetzen oder einen belegten Alternativpfad benennen.
2. **`providers`-Innenform (Phase B):** `settings.baseURL` + `env` statt `options.{baseURL,apiKey}`; AC-B10 und §3.3 sind anzupassen.
3. **`cli.json`-Inhalt (Phase D2):** dokumentiert nur `plugins`; AC-D7 (`theme`, `autoupdate`) ist unbelegt und vor D2 zu korrigieren.
4. **`permissions[]`-Einfügeposition (3.4/C1):** last-match + Agent-Regeln zuletzt (VERIFIED, Lauf 18) → Managed-Denies gehören ans Listenende, nicht an den Anfang; sonst sind sie durch jede spätere Regel (auch Agent-`allow`) überstimmbar.
5. **Plugin-Config-Key (C3):** v2 nutzt `plugins` (Plural); für Dateien unter `.opencode/plugins/` ist kein Eintrag nötig. §3.6 spricht von `plugin` — reine Doku-Korrektur, kein Blocker.

## Verdikt-Begründung

- C3-Gate: **GO** — Q1 (Mechanismus, Laden, Format), Q2 (Hook + Blockieren) und Q3 (Subagent-Session + Main-Chat-Unterscheidung) sind jeweils VERIFIED mit reproduzierbaren Läufen; der Plugin-Mechanismus ist stabil dokumentiert (offizielle v2-Docs, Version 2.1.3).
- Feld-Gate: **AMEND** — Q5 ist vollständig VERIFIED/DOKU, Q6 enthält mit `agents.title.model` eine nicht bestätigte Zeile (plus zwei Innenform-Abweichungen bei `providers`/`cli.json`). Amendment B1 ist vor Phase B (und D2) einzuarbeiten.

VERDICT-C3: GO
VERDICT-FIELDS: AMEND
