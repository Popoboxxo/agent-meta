# Audit: viz, Extensions-Mechanik, ReqogniLoom-Integration, Agent Meta gesamt

- **Status:** Analyse (kein Beschluss)
- **Datum:** 2026-11-14
- **Quelle:** Fable-Grobaudit, nicht gegen Code vollständig verifiziert
- **Issues:** #1237–#1276 (Audit-Folgeissues), #1276 (Folge-Audit)
- **Zugehörige Berichte:** docs/analysis/2026-11-14-fable-concept-audit.md, docs/analysis/2026-11-14-fable-provider-hooks-audit.md, docs/analysis/2026-11-14-fable-viz-extensions-audit.md, docs/analysis/2026-11-14-audit-prioritization.md

- Datum: 2026-11-14 · Stand: Arbeitskopie = origin/main (Branch `chore/main-checkout-parking`, clean)
- Modus: read-only, Code/Config/Tests gelesen; keine Runtime-Läufe außer `graphify query/explain`
- Evidenzformat: `Datei:Zeile`. Nicht Verifiziertes ist mit **[unverifiziert]** markiert.

Urteile: **A viz = teils** · **B Extensions = teils** · **C ReqogniLoom = nicht sauber** · **D Agent Meta gesamt = teils**

---

## A. viz (viz-logger, admin-server/VizManager, Dashboard, MCP, Lifecycle)

### Stärken
- Loopback-Binding überall hart: `scripts/viz-logger.py:614` (`127.0.0.1`), `scripts/viz-report.py:911` (`127.0.0.1`), `scripts/admin-server.py:89,203-206` (Default + Allowed-Hosts/Wildcard-Liste).
- Admin-Server: Token-Pflicht bei Nicht-Loopback (`admin-server.py:6412-6421`), Origin-/Host-Prüfung gegen DNS-Rebinding (`admin-server.py:1162-1187, 3651-3700`), Query-Token nur für SSE-Events (`:3736-3749`).
- Start-Robustheit nach #1189: Zombie-Erkennung (`:619-631`), Bind-Preflight (`:634`), Health-Identity-Check per PID/Mode (`:696-766`), tmp-sink-Pin fail-loud (`:816-820`).
- Echte Smoke-Tests: `tests/test_admin_server_lifecycle_smoke.py:87,104,118` (start/status/stop, Broken-Config, Temp-in-Root), `tests/test_viz_subserver_live.py:84-169` (Live-Subserver inkl. Chromium-E2E, #317), `tests/test_viz_instance_fields.py:45-95`.
- Event-Log-Lesen begrenzt (`scripts/lib/viz.py:60` Tail-Limit 10 000 Zeilen, best-effort bei Rotation `:628`).
- Kopplung an Sync-Pipeline schlank: nur `.gitignore`-Einträge (`scripts/lib/sync_pipeline.py:154,1865-1868`) und Prompt-Block-Injektion gated über `viz.enabled` + `mode` (`scripts/lib/agent_sync.py:926-930`).

### Schwächen / Risiken

| # | Befund | Evidenz | Schwere |
|---|---|---|---|
| A1 | **stdio-MCP nutzt LSP-Framing (`Content-Length`) statt newline-delimited JSON-RPC** → Claude Code sendet NDJSON, Server wartet ewig auf `\r\n\r\n` → genau das beobachtete `viz-logger (CONNECT_TIMEOUT 30000ms)`. | `scripts/viz-logger.py:285-313` (`_send_message`/`_read_message` Content-Length), `scripts/viz-logger-mcp.mjs:95,103` (gleiches Framing) | hoch |
| A2 | **Drei divergente Event-Writer** für dieselbe Datei: `lib/viz.write_event` (RLock), `viz-logger.write_event_safe` (Lockfile), `hooks/1-generic/viz-log.sh` (ohne Lock, cwd-relativ `".meta-viz"`). | `scripts/lib/viz.py:532-547`, `scripts/viz-logger.py:77-115`, `hooks/1-generic/viz-log.sh:47-51` | mittel |
| A3 | **Stale-Lockfile ohne Alter-Check**: Crash zwischen `O_EXCL` und `remove` → alle Folge-Writes scheitern nach 10×0,1 s nur mit stderr-Warnung. | `scripts/viz-logger.py:85-111` | mittel |
| A4 | **Legacy-Log wächst unbegrenzt**: viz-logger/hook schreiben in `events.jsonl`, Cleanup globbt nur `events-*.jsonl`. Keine Rotation/Size-Cap. | `scripts/viz-logger.py:46,59`, `scripts/lib/viz.py:663` | mittel |
| A5 | **PID-Reuse-Risiko bei `_stop`**: killt PID aus Pidfile ohne Identitätsprüfung (Cmdline/Starttime); SIGKILL nach 1 s. Identity-Check existiert nur für den Admin-Health-Pfad. | `scripts/admin-server.py:864-884`, Kontrast `:740-747` | mittel |
| A6 | **SSE-MCP-HTTP ohne Auth/Origin-Check, CORS `*`** (loopback, aber DNS-Rebinding kann Fake-Events ins Dashboard injizieren). | `scripts/viz-logger.py:513-519,533` | niedrig |
| A7 | **Toter Katalog-Eintrag `a2a-handoff`**: startet `viz-logger.py --mcp --mode a2a`, aber `--mode` existiert nicht und der Server exponiert nur `log_viz_event`. | `config/plugin-catalog.yaml:106-133` vs. `scripts/viz-logger.py:215,632-634` (`--mode`-Treffer: 0) | mittel |
| A8 | **MJS-Shim driftet**: spawnt pro Event einen Python-Prozess, reicht weder `--root` noch `tokens_in/out`/Instance-Felder durch; nirgends mehr referenziert außer `docs/CODEBASE_OVERVIEW.md`. | `scripts/viz-logger-mcp.mjs:219-246` | niedrig |
| A9 | **viz-logger immer in `.mcp.json`, obwohl `viz.enabled: false`** (Plattform-Bundle `agent-meta` aktiviert ihn unabhängig vom viz-Schalter) → 30 s Timeout bei jedem Session-Start (A1). | `rules/2-platform/agent-meta-mcp.yaml:8-9`, `.meta-config/project.yaml:325-327`, `.mcp.json` (`viz-logger`), `scripts/lib/registry_query.py:158-172` | mittel |
| A10 | **Relativer Command-Pfad** `scripts/viz-logger.py` in `.mcp.json` → funktioniert nur, wenn cwd = Repo-Root; im Submodul-Layout (`.agent-meta/scripts/...`) nicht. | `config/plugin-catalog.yaml:101-104`, `.mcp.json` | niedrig |
| A11 | **Monolith**: `admin-server.py` 6 473 Zeilen (VizManager + ConfigManager + Handler + CLI). Trennung Daten/Transport/UI nur innerhalb einer Datei. | `wc -l`; `admin-server.py:777,1243,3524` | mittel |
| A12 | Provider-Agnostik: viz-log-Hook und `log_viz_event` sind Claude-Hook-/MCP-zentriert; `_get_terminal_tool` mappt pro Provider (ok), aber Hook-Pfad nur Claude. | `scripts/lib/viz.py:689`, `hooks/1-generic/viz-log.sh` | niedrig |

### Testabdeckung
- Gut: Lifecycle/Start-Robustheit (`tests/test_admin_server.py:3017-3504`, 4 VizManager-Tests), Live-Subserver, Instance-Felder.
- Lücken: kein Test für stdio-Framing gegen echten MCP-Client (A1 hätte so auffallen müssen), kein Test für Lockfile-Staleness (A3), Log-Wachstum (A4), `a2a-handoff` (A7), MJS-Shim (A8).

### Empfehlung / Aufwand
- A1: Framing auf NDJSON umstellen (oder beides akzeptieren) + Contract-Test mit `initialize`-Roundtrip. **S**
- A2+A3+A4: einen Writer (`lib/viz.write_event`) als Single Source, viz-logger/hook darauf umstellen; Lockfile mit mtime-Verfall; Session-Datei statt Legacy-Datei als Default. **M**
- A5: PID-Identität (Starttime/cmdline) vor `kill`. **S**
- A7/A8: Eintrag entfernen oder implementieren; MJS-Shim löschen. **S**
- A9: viz-logger nur aktivieren, wenn `viz.enabled` oder explizit `plugins.viz-logger.enabled`. **S**
- A11: VizManager + Admin-Handler in `scripts/lib/admin/` auslagern. **L**

**Urteil A: teils** — Admin-Server/Lifecycle sind sorgfältig gehärtet und getestet; der eigentliche viz-logger (MCP-Transport, Event-Schreibpfad, Katalogpflege) ist nicht sauber.

---

## B. Extensions-Mechanik (3-project, Managed Blocks, update-extensions, External Skills, MCP-Aktivierung, Plugins, external/)

### Stärken
- Schichtenmodell 0/1/2/3 klar in Code und Doku: `agents/{0-external,1-generic,2-platform}`, Prioritätsregel `1-generic < 2-platform < 3-project` (`scripts/lib/frontmatter.py:622-626`); 3-project liegt bewusst nur im Konsumentenprojekt.
- Managed-Block-Ersetzung mit Funktions-Callback gegen Backslash-Escapes (#674) (`scripts/lib/extensions.py:96-100`); unaufgelöste `{{VAR}}`-Zeilen werden gedroppt (IC-15, `:70-87`, Test `tests/test_create_ext_unresolved.py:43-70`).
- Pfad-Härtung über `safe_path` (`extensions.py:129`), Dry-Run-Guard für Submodule-Mutation (`scripts/lib/skills.py:218-238`, #803).
- Aktivierungsmodell explizit und getestet: MCP nur via `plugins.<id>.enabled` oder Plattform-Bundle (`scripts/lib/plugins.py:29-60` Docstring, `registry_query.py:150-172`); Guardrail-Liste generiert statt handgepflegt (`registry_query.py:176-192`, Tests `tests/test_mcp_config.py:265-298`).
- Drift-Erkennung für injizierte Skills/Rules über `.agent-meta-managed`-Index (`scripts/lib/external_tools_drift.py:44-46,204`).

### Schwächen / Risiken

| # | Befund | Evidenz | Schwere |
|---|---|---|---|
| B1 | **≥6 unabhängige Managed-Block-Implementierungen** (Regex/Marker je Modul): `extensions.py`, `context.py` (mehrfach, inkl. Continue-Variante `# agent-meta:managed-begin`), `cli_commands.py`, `external_tools_drift.py`, `generated_file_drift.py`, `release_scaffold.py`. Semantik (Duplikat-Marker, Prepend-Fallback, Shrink) divergiert. | `grep managed-begin`: `scripts/lib/extensions.py:93`, `context.py:48,678,1069,2031`, `cli_commands.py:107` | mittel |
| B2 | **Kein Drift-/Tamper-Schutz für Extensions**: Managed-Block wird stumpf überschrieben (keine Hash-Prüfung, kein Versionsmarker); fehlt der Marker, wird ein neuer Block **vorangestellt** („should not happen“) statt zu warnen. | `scripts/lib/extensions.py:90-102,160-172` | mittel |
| B3 | **update-extensions prüft weder Rolle noch Präfix**: jede `*-ext.md` wird bearbeitet (auch verwaiste Rollen); Einzel-Rollen-Update laut Command nicht möglich, wird aber als Option beworben. | `extensions.py:160`, `commands/1-generic/update-extensions.md:23-25` | niedrig |
| B4 | **Doku ≠ Code**: Command verspricht „added/removed sections from the base agent“, Managed-Block enthält aber nur 4 Projektvariablen. Pfad `.agent-meta/scripts/sync.py` hart kodiert (im Meta-Repo selbst falsch). | `commands/1-generic/update-extensions.md:24,29,40,47` vs. `templates/managed-block.md:1-9` | niedrig |
| B5 | **Upgrade-Pfad hinterlässt Backup-Litter**: 702 `*.sync-backup-*`-Dateien im Arbeitsbaum, davon 14 unter `.claude/hooks/`, plus 5 `project.yaml.bak.*`. Keine Aufräum-Policy sichtbar. | `find -name "*.sync-backup-*" | wc -l` = 702; `ls .claude/hooks`, `ls .meta-config` | mittel |
| B6 | **Submodule-Protection ist Prompt-Konvention**: Skill-Text verweist auf `.gitmodules`, das Repo hat keins; `external/awesome-claude-code` ist ein nested Clone (eigene Toplevel). Hooks kennen nur `git submodule`-Lesebefehle, keinen Schreibschutz für `external/`. | `.claude/skills/submodule-protection/SKILL.md:7-12`, `git -C external/awesome-claude-code rev-parse --show-toplevel`, `hooks/1-generic/orchestrator-guard-impl.sh:557,1043` | niedrig |
| B7 | **`add-mcp-server` ist 15 Zeilen Prosa**, keine Validierung der Secret-Namen gegen Katalog, kein Hinweis auf Plugin-vs-Katalog-Doppelung (siehe C). | `commands/1-generic/add-mcp-server.md:9-13` | niedrig |
| B8 | **Neuer MCP-Server berührt ≥6 Dateien** (Katalog, role-defaults, rules-presets, recommended-skills, Plattform-Bundle, `docs/guides/mcp/<x>.md`, Test-Parametrisierung) — kein Generator/Checkliste im Code. | `grep -l playwright config/* ...` → 6 Dateien; `tests/test_mcp_role_tools.py:153` | mittel |
| B9 | **MCP-Health prüft nur Secret-Leere und Stdio-Command**, nicht Variablennamen-Konsistenz zwischen Quellen oder URL-Validität nach Substitution. | `scripts/lib/mcp_health.py:42-88` | mittel |

### Testabdeckung
- Gut: Context-Managed-Blocks (`tests/test_context_managed_block_shrink.py:64-108`), MCP-Konfig/-Rollen-Tools (`tests/test_mcp_config.py`, `tests/test_mcp_role_tools.py:36-153`), Skills-Index (`tests/test_skills.py`).
- Lücken: `update_extensions` hat keinen direkten Test (nur `create_extension`), Prepend-Fallback ungetestet, Backup-Lebenszyklus ungetestet, `add-mcp-server`-Command ungetestet.

### Empfehlung / Aufwand
- B1: eine `managed_block.py` (find/replace/validate, Marker-Varianten) und die 6 Stellen darauf ziehen. **M**
- B2: Hash im Marker (`managed-begin v=<hash>`), Warnung statt Prepend bei fehlendem Marker, `--check` für Extensions. **S–M**
- B5: Retention für `*.sync-backup-*` (z. B. letzte 3) + `/diagnose`-Hinweis. **S**
- B8: `scripts/sync.py --scaffold-mcp <id>` oder Checkliste als Test (jede Katalog-ID muss in role-defaults/docs/test auftauchen). **M**
- B4/B7: Command-Texte an Code angleichen. **S**

**Urteil B: teils** — Modell und Aktivierungslogik sind sauber dokumentiert und getestet; die Implementierung ist fragmentiert (B1), ohne Drift-Schutz (B2) und mit sichtbarem Wartungsschmutz (B5).

---

## C. ReqogniLoom-Integration

### Einbindung (Ist)
- Katalog: `config/plugin-catalog.yaml:179-288` (SSE, `{{MCP_REQOGNILOOM_URL}}/mcp/sse/`, Header `Authorization: Bearer` + `X-Project-ID/X-User-ID/X-Workspace-ID`, 5 Secrets, allowed/blocked-Listen).
- Aktiv: `.meta-config/project.yaml:87-88` (`reqogniloom: enabled: true`) → generiert `.mcp.json` (Server `reqogniloom`), `opencode.json:17-24`, Skill `.claude/skills/mcp-reqogniloom/SKILL.md` (aus Katalog), Guardrail `rules/1-generic/mcp-guardrails.md` + `{{MCP_GUARDRAILS_LIST}}` (`scripts/lib/registry_query.py:176-192`), Lazy-Rule-Zeile `rules/1-generic/use-lazy-rules.md:17`.
- Parallel: externes Claude-Plugin `reqogniloom@reqogniloom-marketplace` (`~/.claude/settings.json:10`, Quelle `/home/hermes/repos/ReqogniLoom/dist/plugins/claude-code`) mit eigenem `.mcp.json` (`${REQOGNILOOM_MCP_URL}/mcp/sse/`, Header `X-API-Key: ${REQOGNILOOM_API_KEY}`), eigenen Agents (`reqogniloom:*`) und Skills (`reqogniloom:*`). **[außerhalb Repo, nur gelesen]**
- Skills-Registry kennt zusätzlich 5 `reqogniloom-*`-Skills als External-Skill-Repo (`config/skills-registry.yaml:11-70`).

### Ursachenpfad der beiden Fehlerbilder (belegt)
1. **`reqogniloom (INVALID_CONFIG): "'url' is not a valid URL"`**
   - Katalog `url: '{{MCP_REQOGNILOOM_URL}}/mcp/sse/'` (`plugin-catalog.yaml:277`) → `_render_env_references` (`scripts/lib/mcp.py:138`) → `.mcp.json`: `"url": "${MCP_REQOGNILOOM_URL}/mcp/sse/"`.
   - `secrets.local.yaml`: alle 5 `MCP_REQOGNILOOM_*` **leer** (nur Keys geprüft, keine Werte gelesen); Env: 0 Treffer für `REQOGNILOOM`.
   - Claude Code expandiert `${MCP_REQOGNILOOM_URL}` zu `""` → URL `"/mcp/sse/"` → ungültig. `check_mcp_health` würde `mcp.secret-empty` nur als Sync-WARN melden (`scripts/lib/mcp_health.py:70-75`), der Server wird trotzdem generiert.
2. **`plugin:reqogniloom:reqogniloom (INVALID_CONFIG): "Missing environment variables: REQOGNILOOM_MCP_URL"`**
   - Externes Plugin nutzt **andere Variablennamen** (`REQOGNILOOM_MCP_URL`, `REQOGNILOOM_API_KEY`) und ein **anderes Auth-Schema** (`X-API-Key`) als der Katalog (`MCP_REQOGNILOOM_*`, `Bearer` + 3 ID-Header). Beide Quellen sind gleichzeitig aktiv.
   - Der Katalog kennt das Problem und schiebt es auf den Nutzer: „beide Variablen setzen oder eine Quelle deaktivieren“ (`plugin-catalog.yaml:273`, repliziert in `SKILL.md:95`).

### Schwächen / Risiken

| # | Befund | Evidenz | Schwere |
|---|---|---|---|
| C1 | **Zwei konkurrierende Integrationen (Plugin + Katalog) mit inkompatiblen Env-Namen und Auth-Headern**; keine Erkennung/Warnung im Sync, nur Prosa. Agents des Plugins referenzieren `mcp__reqogniloom__*`, was auf den Katalog-Server zeigt, nicht auf `plugin:reqogniloom:reqogniloom` **[unverifiziert: Tool-Namensauflösung bei Plugin-MCP]**. | `plugin-catalog.yaml:273-282`, Plugin-`.mcp.json` (s. o.), `~/.claude/settings.json:10` | hoch |
| C2 | **Katalog-Allowlist veraltet gegenüber Plugin-Toolfläche**: Plugin-Agents nutzen `change_request.*`, `review.*`, `baseline.*`, `diagram.*`, `interview.*`, `goal.*`, `main_goal.*`, `requirement_bundle.*`, `traceability.create_link`, `adr.outdate/reactivate`, `ai_derivation.derive_risks_from_architecture` — nichts davon in `tools.allowed`. Umgekehrt listet der Katalog `architecture.create/link/decompose/decompose_commit`, die kein Plugin-Agent nutzt. | `plugin-catalog.yaml:188-242` vs. Agent-Typen `reqogniloom:change-manager/-quality-auditor/...` (Session-Kontext) | mittel |
| C3 | **Verbotsliste ist Prompt-only**: `blocked` wird nur in Skill-Text und Guardrail-Rule gerendert; keine `permissions.deny`-Einträge, Hook lässt `mcp__*__*` pauschal passieren. Für Rollen ohne Opt-in schützt nur Abwesenheit aus `tools:`; der Main-Chat ist ungeschützt. | `scripts/lib/mcp.py:72-81`, `registry_query.py:188`, `.claude/settings.json` (deny nur 4 Bash-Regeln), `hooks/1-generic/lib/hook_common.sh:171-172` | hoch |
| C4 | **Kein Rollen-Opt-in im eigenen Projekt**: keine generierte Agent-Datei trägt `mcp__reqogniloom__*`; die 55-Tool-Allowlist hat hier keinen Effekt. | `grep -l mcp__reqogniloom .claude/agents/*.md` = leer; `config/role-defaults.yaml:341` einzige `mcp-servers`-Stelle | niedrig |
| C5 | **Mehrfach-Pflege desselben Inhalts**: Tool-Listen stehen in Katalog, generierter Skill, Guardrail-Rule, `AGENTS.md:94`, `CLAUDE.md` (Rules-Block), `docs/guides/mcp/reqogniloom-setup.md`; Setup-Guide kennt nur 2 der 5 Secrets. | `docs/guides/mcp/reqogniloom-setup.md:25-36` vs. `plugin-catalog.yaml:283-288` | niedrig |
| C6 | **Tool-Konsistenz-Test fehlt für ReqogniLoom**: `test_documented_toolset_matches_generated_tools` ist parametrisiert, ReqogniLoom erscheint nicht; `tests/test_skills.py` nutzt `reqogniloom-change-manager` nur als Dummy-Name. | `tests/test_mcp_role_tools.py:153`, `tests/test_skills.py:21-58` | mittel |
| C7 | **Ausfallverhalten**: ungültige Konfiguration erzeugt pro Session zwei Fehlbanner; Sync bricht nicht ab (Design: advisory). Positiv: kein Hard-Fail, negativ: Dauerzustand wird nicht sichtbar gemacht (`/diagnose` prüft Secret-Leere nur als WARN). | `scripts/lib/mcp_health.py:56-59` | mittel |
| C8 | `#1180`-Nachwirkung: `use-lazy-rules.md` listet `mcp-reqogniloom` (Phase E/#1186 noch offen) — Lazy-Skill wird vom Hauptchat selten geladen, Guardrail ist der einzige Always-on-Schutz. | `rules/1-generic/use-lazy-rules.md:17`, `rules/1-generic/mcp-guardrails.md:3-6` | niedrig |

### Empfehlung / Aufwand
- C1: Entscheidung **eine Quelle**: Katalog-Server deaktivieren, wenn Plugin aktiv (Sync-Check: `~/.claude/settings.json enabledPlugins` lesen → WARN/Skip), oder Katalog an Plugin-Variablennamen angleichen. **S** (Check) / **M** (Harmonisierung)
- C2: Allowlist gegen tatsächliche Server-Toolliste generieren (Export aus ReqogniLoom-Repo) + Test, der Katalog ↔ Plugin-Agents abgleicht. **M**
- C3: `blocked` zusätzlich als `permissions.deny: ["mcp__<server>__<tool>"]` in `.claude/settings.json` rendern (provider-agnostisch über Capability-Flag). **S**
- C6/C7: Parametrisierung erweitern; `/diagnose`: `INVALID_CONFIG`-Vorhersage (leere Secrets eines aktiven SSE-Servers = ERROR statt WARN). **S**

**Urteil C: nicht sauber** — die beiden produktiven Fehlerbilder sind direkte Folge einer bekannten, nicht aufgelösten Doppelintegration (C1); die Verbotsliste ist nur eine Konvention (C3); Tool-Listen sind nicht gegen die reale Serverfläche abgesichert (C2/C6).

---

## D. Agent Meta als Ganzes (Sicht Extensions/viz/ReqogniLoom)

### Stärken
- Ein Katalog (`config/plugin-catalog.yaml`) speist Skill, Guardrail, Provider-Configs, Health-Check — gute Single Source of Truth, generierte Artefakte tragen Herkunftsvermerk (`SKILL.md:104`).
- Konsequente Provider-Agnostik-Regel (Capability-Flags, `provider-skip`), große Testbasis (468 Testdateien), Issue-Verweise im Code (#1189, #317, #1180).

### Schwächen / Risiken

| # | Befund | Evidenz | Schwere |
|---|---|---|---|
| D1 | **Monolithen als SPOF**: `admin-server.py` 6 473, `context.py` 3 838, `sync_pipeline.py` 2 114, `cli_commands.py` 1 804 Zeilen. | `wc -l` | mittel |
| D2 | **Dubletten-Muster**: Managed-Block ×6 (B1), Event-Writer ×3 (A2), MCP-Transport ×3 (py-stdio, py-http, mjs), ReqogniLoom-Integration ×3 (Katalog, Plugin, Skills-Registry). | s. o. | mittel |
| D3 | **Katalogpflege ohne Gegenprobe**: tote (`a2a-handoff`, A7) und veraltete (`reqogniloom`, C2) Einträge bleiben unbemerkt; kein Test „Katalog-Command/Flags existieren“. | `plugin-catalog.yaml:106-133,188-242` | mittel |
| D4 | **Skalierung neuer Integration**: MCP-Server = Katalogeintrag + 5–6 Begleitdateien (B8); neuer Extension-Typ = neue Managed-Block-Variante (B1). Aufwand pro Server heute **M**, sollte **S** sein. | B8 | mittel |
| D5 | **Konvention statt Durchsetzung** bei MCP-Verboten und Submodule-Schutz (C3, B6) — konsistent mit dem deklarierten „Convention boundary“, aber für `delete`/`admin`-Tools eines SaaS zu schwach. | `.claude/rules/repo-containment.md`, `hook_common.sh:155-158` | hoch |
| D6 | **Betriebsschmutz im Repo**: 702 Backup-Dateien, `report.html`, `sync.log`, `CLAUDE.md.sync-backup-*` im Root, `graphify-out/` mit 6 Datumsordnern. | `ls`, `find` | niedrig |

### Empfehlung / Aufwand
- D3: Katalog-Lint als Test (Stdio-Command + Args gegen `--help`/Argparse, SSE-URL-Template-Variablen gegen `secrets`-Liste, allowed/blocked disjunkt). **S**
- D5: `blocked` → `permissions.deny` (C3) + Write-Guard für `external/` im repo-containment-Hook. **S–M**
- D1/D2: Admin/Viz in Paket auslagern, `managed_block.py` und einen Event-Writer. **L**

**Urteil D: teils** — tragfähige Architektur mit guter Testkultur, aber Wiederholungsmuster und Konvention-statt-Durchsetzung an den sicherheitsrelevanten Rändern.

---

## Top-10 (priorisiert)

1. **A1** viz-logger stdio-Framing (Content-Length statt NDJSON) → `CONNECT_TIMEOUT`. Fix S.
2. **C1** ReqogniLoom Plugin-vs-Katalog-Doppelung mit inkompatiblen Env-Namen/Auth → beide `INVALID_CONFIG`. Entscheidung + Sync-Check S.
3. **C3/D5** MCP-Verbotsliste nur Prompt; `permissions.deny` generieren. S.
4. **A9** viz-logger aktiv trotz `viz.enabled: false` (Plattform-Bundle). S.
5. **C2/C6** Katalog-Allowlist vs. reale Toolfläche; Konsistenztest fehlt. M.
6. **A2/A3/A4** Drei Event-Writer, stale Lockfile, unbegrenztes `events.jsonl`. M.
7. **A7/D3** Toter Katalog-Eintrag `a2a-handoff`; Katalog-Lint. S.
8. **B1/B2** Sechs Managed-Block-Implementierungen, kein Drift-Schutz für Extensions. M.
9. **A5** `_stop` killt PID ohne Identitätsprüfung. S.
10. **B5/D6** 702 Backup-Dateien, keine Retention. S.

## Nicht geprüft / Annahmen
- Keine Runtime-Läufe: A1 ist aus Code + MCP-Spezifikation (NDJSON für stdio) abgeleitet, nicht reproduziert; Claude-Code-Verhalten bei leerer `${VAR}`-Expansion aus Fehlermeldung rückgeschlossen.
- ReqogniLoom-Serverfläche nicht abgefragt (MCP bewusst nicht benutzt); C2 stützt sich auf die Tool-Listen der Plugin-Agents aus dem Session-Kontext.
- Plugin-Dateien außerhalb des Repos (`~/.claude/plugins/cache/...`, `~/.claude/settings.json`) nur gelesen, Werte aus `secrets.local.yaml` nicht gelesen (nur leer/gesetzt).
- Dashboard-UI (`viz-report.py` HTML/JS, admin-ui Frontend), `viz-server.py`, `opencode_v2_config.py`, Windows-Pfade, Browser-E2E nicht inhaltlich geprüft.
- `docs/`-Prosa nur punktuell; die Admin-UI-Doku (`docs/api/admin-ui-reference.md`) nicht gegen Code abgeglichen; die ursprünglich genannte Datei admin-ui-architecture.md existiert nicht.
- Test-Suite nicht ausgeführt; Abdeckungsaussagen basieren auf Testnamen/-Docstrings.

## Abgleich mit bekannten Issues (nur Code-/Doku-Belege)
- **#1189**: Start-Robustheit/tmp-sink umgesetzt (`admin-server.py:325,624,635,718,6242`, `CHANGELOG.md:9-11`); A5 (`_stop`-Identität) nicht abgedeckt.
- **#317**: Live-Subserver-Tests vorhanden (`tests/test_viz_subserver_live.py:1,139,170`).
- **#1180**: Dangling-Doc-Pointer-Check (`scripts/lib/consistency/doc_pointers.py:1`, `tests/test_rule_doc_pointers.py`); `mcp-*`-Lazy-Rules weiterhin in `use-lazy-rules.md:17` → Phase E/**#1186** offen (kein Code-Beleg für #1186 gefunden).
- **#1187**: nur in `tests/test_project_context_placeholder_ratchet.py:6,11` (T9 ausstehend).
- **#1237–#1247**: keine Treffer in Code/Tests/CHANGELOG — nicht belegbar.
- **#674** (Backslash in Managed-Block), **#803** (Dry-Run-Guard Submodule), **#1080** (Connection-String-Override) im Code referenziert und umgesetzt.

**Korrektur Phantom-Referenz:** die Datei docs/guides/admin-ui-architecture.md existiert nicht (weder #1276 noch dieses Audit hätten darauf verweisen dürfen). Die tatsächlich vorhandene Admin-UI-Doku ist `docs/api/admin-ui-reference.md` (Howto: `docs/howto/admin-ui-remote-access.md`).
