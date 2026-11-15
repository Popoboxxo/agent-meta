# Verifikation der „NICHT GEPRÜFT / Lücken“-Punkte der Audits 2026-11-14/15

- **Status:** Analyse (kein Beschluss)
- **Datum:** 2026-11-15
- **Quelle:** Fable/Opus-Audit, Verifikationsstand siehe Verifikationsbericht (docs/analysis/2026-11-15-fable-verification-of-unchecked.md)
- **Modellherkunft:** Fable
- **Issues:** #1237–#1276 (Audit-Folgeissues)
- **Zugehörige Berichte:** docs/analysis/2026-11-15-fable-framework-settings-audit.md, docs/analysis/2026-11-15-fable-language-feature-audit.md, docs/analysis/2026-11-15-fable-orchestration-rollout-audit.md, docs/analysis/2026-11-15-fable-verification-of-unchecked.md

> Prüfer: Fable 5.1 (Subagent) · Datum: 2026-11-15 · Stand: origin/main 92d41a90 (HEAD lokal 5e16ecf8, Parking-Branch)
> Methode: nur Lesen, graphify, gh read-only; Laufzeit-Render ausschließlich in .tmp/audit/scratch/verify-copy/ (git archive origin/main).
> Legende: ✔ bestätigt · ✘ widerlegt · ◐ teils · ○ nicht prüfbar

## Status
- [x] 0 Setup (isolierte Kopie)
- [x] 1 Orchestrierung (1.1–1.4 inkl. Render-Lauf, 14 Matrix-Zellen)
- [x] 2 Sprach-Feature
- [x] 3 Provider-Hooks
- [x] 4 Viz/Extensions/ReqogniLoom
- [x] 5 Einstellungs-Audit
- [x] 6 Nebenbefunde
- [x] 7 Korrektur-Tabelle — Status: ABGESCHLOSSEN 2026-11-15

## 0 Setup
- ✔ Isolierte Kopie: `git archive origin/main | tar -x -C .tmp/audit/scratch/verify-copy/` angelegt (92d41a90); `.meta-config/project.yaml` enthalten.
- Umgebung: `jsonschema 4.26.0` und `tiktoken` installiert (Python-Default des Hosts).
- Rohdaten: .tmp/audit/scratch/vf-*.txt|json.

## 1 Orchestrierung

### 1.1 Gemini-`tools` als harte Allowlist? (O2, 44× `invoke_subagent`)
- ◐ **teils, Befund bleibt (Schwere unverändert hoch):**
  - Gemini CLI: Loader validiert Agent-Frontmatter mit `.strict()`-Schema, „Tools werden validiert“ — `docs/providers/gemini-cli.md:71-77`, Studie `docs/analysis/2026-10-11-context-budget-provider-study.md` §3.7 (SOURCE-DERIVED, U-02 „nicht ausgeführt“). Dort zugleich: „kein `define_subagent` in der CLI“ → `invoke_subagent` existiert in der Gemini CLI gar nicht; Dispatch-Prosa läuft ins Leere unabhängig von der Allowlist-Frage.
  - Antigravity: `provider-capabilities.yaml:251` erklärt `read_only_enforcement=tools` ausdrücklich als UNVERIFIED; `native_agent_tools: [define_subagent, send_message, invoke_subagent]` (`:241`) ist Konfig-Behauptung ohne Evidenz-Doc (grep `invoke_subagent` in `docs/analysis/evidence/` = 0 Treffer).
  - Widerspruch bestätigt: `config/provider-tools.yaml:53-55` („Gemini has no subagent dispatch tool“, `Agent`/`Task` silent dropped) vs. `provider-capabilities.yaml:241`.
- Konsequenz: O2 bleibt hoch; Formulierung schärfen: „kein belegter Dispatch-Pfad auf beiden Gemini-Oberflächen“ statt „Allowlist unklar“.

### 1.2 Claude `permissionMode: plan` × `Write` des Orchestrators
- ✔ **bestätigt (Schwere steigt: Checkpointing unter Claude faktisch tot):**
  - `config/role-defaults.yaml:11` setzt `permission_mode: plan` für den Orchestrator; .claude/agents/orchestrator.md FM führt `Write`.
  - Claude-Code-Doku (code.claude.com/docs/en/sub-agents, abgerufen 2026-11-15): `plan` = „Plan mode (read-only exploration)“; permission-modes-Doku: „edits stay blocked until you approve the plan“, Blocks gelten „wherever Claude Code runs without an interactive terminal, including … Agent SDK sessions“; Ausnahme nur „interactive terminal sessions with bypass permissions available“ (dann wird Plan-Block nicht erzwungen).
  - Zusätzlich: Haupt-Chat in `bypassPermissions`/`acceptEdits`/`auto` ⇒ Subagent erbt diesen Modus, FM-`permissionMode` wird ignoriert → Verhalten hängt vom Nutzer-Modus ab, nicht vom Template.
  - Indiz im Repo: `DEFAULT_CHECKPOINT_DIR = ".meta-viz/checkpoints"` (`scripts/lib/progress_paths.py:35`), Verzeichnis existiert nicht (`ls .meta-viz/` ohne `checkpoints`), obwohl `orchestrator.checkpointing: true` (`project.yaml:316`) → kein Checkpoint je geschrieben.
- Konsequenz: neuer Defekt — `permission_mode: plan` + `Write`-Tool + `checkpointing: true` sind inkonsistent; Fix entweder `permission_mode: default` für den Orchestrator oder Checkpointing als Claude-untauglich dokumentieren. Betrifft #1176/#1190-Umfeld; Rollout-Matrix-Zelle „Checkpointing Claude ✔“ → ◐.

### 1.3 Schema-Erzwingung (`handoff.t-size-limit`, O9)
- ✘ **widerlegt (Schwere sinkt):** Schema-Validierung ist nie hart — `scripts/lib/config.py:664-667` („Schema violations are printed as warnings — never hard-fails“), Ausgabe `:705-712` als `!  Config validation warnings`, max. 5 Zeilen; ohne `jsonschema` komplett übersprungen (`:678-687`).
- Hart-fatal sind nur die stdlib-Checks `:669-676` (Model-Inheritance, Provider-Namen, Topologie-Enum, Repo-Containment, Subagent-Permissions, Test-Envs, Release-Checklist).
- `resolve_a2a_t_size_limit` liest `orchestrator.handoff.t-size-limit` (`config.py:127-143`) → Key **wirkt**, erzeugt aber bei installiertem jsonschema eine Warnung wegen `additionalProperties: false` (`project-config.schema.json:2575-2586`).
- Konsequenz: O9 = Doku-/Schema-Drift (S), kein Funktionsausfall; Laufzeitbeleg s. 1.4 (Render-Lauf).
- ✔ Laufzeitbeleg: `verify-schema2` mit `handoff.t-size-limit: 250` → `sync.py --validate` exit 0, stderr: `!  Config validation warnings (1) … orchestrator.handoff: Additional properties are not allowed ('t-size-limit' was unexpected)` (Meldung erscheint doppelt — Nebenbefund: Validierung läuft zweimal).

### 1.4 Render-Lauf in der isolierten Kopie (5 Varianten + 1 Validate)
- Script .tmp/audit/scratch/vf-render.sh; Kopien `verify-full-base` (Repo-Konfig), `verify-compact` (+`context-profile: compact`), `verify-all-{subagent,primary,hybrid}` (9 Provider: Claude, Opencode, Gemini, Codex, Copilot, Continue, KimiCode, Mammouth, ZCode). Alle `exit=0`; Logs `vf-sync-*.{out,err}`, `verify-*/sync.log`.
- **Artefakte je Provider (all-primary):** .claude/agents/orchestrator.md (73,5 kB), .opencode/agents/orchestrator.md, .gemini/agents/orchestrator.md, `.codex/agents/orchestrator.toml` (73,3 kB), .github/agents/orchestrator.agent.md, .continue/agents/orchestrator.md + .continue/prompts/orchestrator.md (8,1 kB), .kimi-code/agents/orchestrator.md, .mammouth/agents/orchestrator.md, .zcode/agents/orchestrator.md.

**(a) `hybrid` — tatsächliches Verhalten**
- ✔ bestätigt „immer → subagent“, **zusätzlich: völlig still.** Kein Treffer für `hybrid|degrad` in stderr/`sync.log`; Opencode-Gate-Warnung nennt „effective orchestrator topology is 'subagent'“. Einzige Diff hybrid↔subagent in allen 9 Orchestrator-Dateien: 2 Zeilen = Label `**Singleton (hybrid):**` statt `(subagent)` (Prosa behauptet „degrades loudly“). `AGENTS.md`/`CLAUDE.md` byte-identisch zu subagent.

**(b) `primary` — tatsächliches Verhalten**
- Opencode: FM `mode: primary` ✔, aber `opencode.json` ohne `default_agent` (`default_agent= None`, `permissions= null`) → `[WARN] runtime gate … SUSPENDED for provider 'Opencode': default_agent is missing` (`sync.log`). Ursache: v2-Tier `plugin` führt den `default_agent`-Merge nicht mehr aus (`docs/providers/opencode.md:354-358`; `isolation.py:595-612`). ⇒ Matrix-Zelle „Opencode primary ✔ E“ → **◐**: Entry-Point nur bei v1/Tier `permission` oder manuell gepflegtem `default_agent`.
- Gemini/Codex/Copilot/Mammouth/ZCode/KimiCode/Continue: **keine** Degrade-Warnung in stderr/`sync.log`. `orchestrator-topology.degraded` existiert nur als Consistency-Finding (`scripts/lib/consistency/topology.py:79`; Test `tests/test_orchestrator_topology_docs.py:528-575` prüft `check_orchestrator_topology`, nicht den Sync-Log). ⇒ „degrades loudly“ gilt nur für `--check`, nicht für `sync.py`.
- **Neuer Defekt:** gerenderte Prosa nutzt die **deklarierte**, nicht die effektive Position (`context.py:2906-2908` „Only the DECLARED position is rendered“): .github/agents/orchestrator.agent.md, .mammouth/agents/orchestrator.md (FM `mode: subagent`!), `.zcode`, `.gemini`, `.codex` tragen `**Singleton (primary):** … The orchestrator **is** the session entry point` obwohl degradiert → irreführende Anweisung für hook-/entry-lose Provider.
- Claude: nur `CLAUDE.md:76` ändert sich („Diese Session startet im `orchestrator`-Agenten“), FM unverändert → Matrix „◐ nur P“ ✔.
- `AGENTS.md` subagent↔primary: 0 Zeilen Diff (Positions-Flags bei Uneinigkeit neutralisiert, bestätigt Code-Lesart `context.py:819-873`).

**(c) Strict-Mode-Text**
- Orchestrator-Dateien: 1 Treffer je Datei (`Mode: strict. Fallbacks: …`, z. B. .opencode/agents/orchestrator.md:34).
- **Shared `AGENTS.md`:** full-base (Opencode+Gemini) → `# CRITICAL GATE` (strikt). Mit 9 Providern → `# CRITICAL GATE (advisory)` in `AGENTS.md:144` **und** .continue/rules/use-orchestrator.md:5. Ursache: `GATE_ADVISORY` = Runtime-Gate-Tier (`providers.py:787-805`), shared Core nutzt „weakest-tier bundle“ (`context.py:2873-2879`) → ein hook-loser Sharer (Codex/Kimi/Mammouth/ZCode) stuft den Gate-Text für **alle** Sharer inkl. Opencode/Gemini auf advisory. Audit :123 (Mode-Last-Writer) → **◐**: `ORCH_MODE_*` bleibt strict (kein Last-Writer beobachtet, keine Overrides im Test), aber der sichtbare Gate-Text degradiert by design. .claude/rules/use-orchestrator.md bleibt `CRITICAL GATE`.

**(d) Worker-Control-Werkzeuge in Prosa ohne Tool**
- `TaskStop`-Nennungen: 2 in jeder Nicht-Claude-Orchestrator-Datei (Codex, Copilot, Continue, Kimi, Mammouth, ZCode, Gemini, Opencode), `SendMessage` 1 (Gemini 2); keine davon im FM-`tools` → Matrix-Zeile „Background-Wait ✘“ für alle 8 ✔ bestätigt. Claude: `TaskStop`=3/`SendMessage`=3, FM enthält `SendMessage` (TaskStop-FM nicht im Head sichtbar, Zelle „◐“ bleibt).
- Codex-TOML: `spawn_agent`=42, `wait_agent`=2 → Delegationssyntax **ist** gemappt; Matrix „native wait_agent/close_agent nicht gemappt“ → **◐** (wait_agent erwähnt, close_agent nicht geprüft).
- Gemini: `invoke_subagent`=44 (deckt sich mit Audit), FM `tools: [TodoWrite, view_file, replace_file_content]`.
- KimiCode FM: `tools: [TodoList, Agent, Read, Write, AgentSwarm]`, **kein `subagents:`** → Studie-Punkt „kann als Subagent nicht an Rollen dispatchen“ bleibt; `TodoList`/`AgentSwarm` inzwischen gemappt (Studie 3.x-Befunde dazu veraltet).
- Copilot FM: nur `name/version/description/hint/prompt_mode/generated-from` — kein `tools`, kein `agents` → kein Dispatch (U-06 bestätigt); .github/copilot-instructions.md 9630 > Soft-Cap 4000 (Warnung).
- Continue: .continue/agents/orchestrator.md FM trägt Claude-Feld `permissionMode: plan`; .continue/prompts/orchestrator.md mit unaufgelöstem `{{PIPELINE_DETAIL_BLOCKS}}` (Warnung `active-set.unresolved-placeholder`); zusätzlich `{{CONTEXT_FILE}}` in `agent-meta-scout.md` (2×). Nur mit 9 Providern sichtbar (full-base: 7 Warnungen ohne diese).

**(e) Matrix-Stichprobe (14 Zellen)**
| Zelle (Rollout-Audit §2.1) | Audit | Render | Urteil |
|---|---|---|---|
| Claude × primary | ◐ nur P | nur CLAUDE.md:76-Text ändert sich | ✔ |
| Opencode × primary | ✔ E (`mode: primary`+`default_agent`) | `mode: primary`, **kein** `default_agent`, Gate SUSPENDED | ◐ (v2) |
| Gemini × primary | ✔ degraded, Finding | still degradiert, Prosa „Singleton (primary)“ | ◐ |
| Mammouth × primary | ✔ degraded (UNVERIFIED) | FM `mode: subagent`, Prosa „(primary)“ | ◐ |
| alle × hybrid | ✘ → subagent | bestätigt, still, nur Label | ✔ |
| Strict Codex/Copilot/Continue/Kimi/Mammouth/ZCode | ✘ P | ✔ + AGENTS.md-Gate wird für alle Sharer „advisory“ | ✔ (verschärft) |
| Background-Wait Opencode/Gemini | ✘ Tool fehlt | TaskStop 2×/SendMessage 1–2× Prosa, FM ohne | ✔ |
| Background-Wait Codex | ✘ nicht gemappt | `spawn_agent` 42×, `wait_agent` 2× | ◐ |
| Singleton Gemini | ◐ P | FM-tools ohne Dispatch, 44× `invoke_subagent` | ✔ |
| Singleton KimiCode | ◐ allowlist required | kein `subagents:` im FM | ✔ |
| Continue × subagent | ✘ unsupported | zusätzlich Claude-FM-Leak + Placeholder | ✔ (verschärft) |
| Copilot × subagent | ◐ P | kein `tools`/`agents` → kein Dispatch | ✔ |
| compact Opencode/Gemini | ? | gerendert, aber 4 Rules „compacted-away, no skill“ | ◐ |
| Claude Checkpointing (impl. ✔) | — | `permissionMode: plan` blockiert Write (1.2) | ✘ |

## 2 Sprach-Feature

### 2.1 Auflösung `knowledge.schema-language: auto`
- ✘ **Key ist inert:** einziger Treffer im gesamten Repo (außer `.tmp`) ist die Schema-Definition `config/project-config.schema.json:2054-2058`; kein Lesezugriff in `scripts/lib/*.py`, `agents/`, `templates/`, `snippets/`, `rules/` (grep `schema-language|schema_language|SCHEMA_LANGUAGE` = 0 außer Schema).
- Konsequenz: Sprach-Audit-Lücke :202 geschlossen — `auto` wird von nichts aufgelöst; `knowledge/schema.md`-Sprache ist rein Agenten-Prosa (`knowledge-curator`). Neuer S-Defekt: toter Config-Key (Schema-Doku verspricht Wirkung).

### 2.2 Sprache der PR-Texte (letzte 30 PRs, `gh pr list --state all --limit 30`)
- Rohdaten: .tmp/audit/scratch/vf-prs.json; Wortmarker DE/EN je Body (Script in `vf-batch2.txt`).
- Ergebnis: **23 EN / 7 DE / 0 MIX**; Marker gesamt DE 194 vs. EN 1481.
- Zeitliche Verteilung: alle 7 DE-PRs sind #1191–#1216 (bis ~2026-11-11); ab #1218 ausschließlich EN (inkl. #1219/#1220 „docs: …“-PRs). Manuelle Stichprobe: #1216 „## Zweck … Übergangskonfig …“ (DE), #1193 „## Was … Aktiviert die Opencode-Surface-v2“ (DE), #1232 „## Summary - The DoD push check blocked …“ (EN), #1225 „## Summary Phase C …“ (EN).
- ✔ Bestätigt die Sprach-Audit-These (D-Befunde: PR-Beschreibungen driften nach EN) und präzisiert: Umschlag ab Phase-Plan-Welle (#1218ff.), vermutlich seit Loop-/Plan-getriebenen Agent-Sessions mit EN-Prompts. Hinweis: `commit-conventions.md` verlangt EN nur für Commits; für PR-Bodies existiert keine Regel → Regel-Lücke, kein Regelbruch.

### 2.3 speech-mode-Rendering AGENTS.md/Opencode/Gemini
- ✔ **bestätigt (Sprach-Audit :12/:43):** in `verify-full-base` existiert `Kommunikationsstil: Short` nur in .claude/rules/speech-mode.md; `AGENTS.md` 0 Treffer (`speech|Kommunikationsstil|Bullet Points statt`), keine Verzeichnisse `.opencode/rules`, `.gemini/rules`, `.agents/rules` (Preset `lazy`, Rules embedded). Opencode/Gemini erhalten den Speech-Mode nirgends → Claude-only-Feature. Unter 9 Providern identisch (`.continue/rules/` enthält `use-orchestrator.md`, aber kein `speech-mode.md`).

## 3 Provider-Hooks

### 3.1 Gemini-Adapter: Dispatch `hook_protocol → writer` und `# provider: Claude`-Header
- ✔ Dispatch statisch bestätigt: `_HOOK_REGISTRATION_WRITERS = {"claude-code-json": _update_settings_hooks, "antigravity-hooks-json": _update_antigravity_hooks_json}` (`scripts/lib/hooks.py:440-443`, früher :442); jede gespiegelte Registrierung läuft durch `antigravity-json-adapter.sh` (`:280-300, :311-335, :394`).
- ✔ Header-Wirkung statisch bestätigt: `hooks.py:568-574` überspringt Hooks mit `# provider: X` ≠ aktuellem Provider (`log.skip … provider-specific hook`). Betroffen: `lifecycle-check.sh`, `sync-on-config-change.sh`, `dod-push-check.sh` (je `:6 # provider: Claude`) → werden für Gemini nicht deployed. Zusätzlich Protokoll-Filter `:576-584` (`hook_protocol`-Header, #808).
- ✔ Laufzeit (verify-full-base): `.agents/hooks.json` enthält `orchestrator-guard` und `repo-containment` je `PreToolUse` `matcher "*"` → `bash ./hooks/antigravity-json-adapter.sh <hook>.sh`; `.agents/hooks/` enthält Adapter, Guard-Impls, `auto-github-release.sh`, `pre-release-check.sh`, `viz-log.sh`, aber **nicht** `dod-push-check.sh`/`lifecycle-check.sh`/`sync-on-config-change.sh` → `# provider: Claude`-Filter wirkt. Offen bleibt nur, ob Antigravity die Datei lädt (Harness-Laufzeit, nicht im Repo prüfbar).

### 3.2 Opencode-Plugin-Autoload (`.opencode/plugins/*.js`)
- ○ **nur Doku, kein Code-Beleg:** Autoload-Behauptung steht ausschließlich in `docs/providers/opencode.md:32` („wird ohne Config-Eintrag geladen“) und `:57`. Code kennt nur Erzeugung/Drift: `runtime_gate.py:94` (Template `templates/plugins/runtime-gate.opencode-plugin.js.tmpl`), `providers.py:697` (`SUPPORTED_PLUGIN_PROTOCOLS`), `generated_file_drift.py:336-339`. Ob Opencode das Verzeichnis ohne `plugins`-Eintrag lädt, ist aus dem Repo nicht ableitbar → bleibt UNVERIFIZIERT (Hooks-Audit-Status korrekt).

### 3.3 Claude `agent_id` im PreToolUse-Payload
- ✔ **extern bestätigt (Risiko sinkt):** Claude-Code-Hooks-Doku (code.claude.com/docs/en/hooks, 2026-11-15) listet `agent_id` („Unique identifier for the subagent or in-process teammate the hook fires in“) und `agent_type` als Common Input Fields; „When a subagent calls a tool, tool events such as PreToolUse … the input carries the agent_id and agent_type“. Keine Mindestversion angegeben (andere Felder tragen Versionsnoten, z. B. `scratchpad_dir` ≥ v2.1.257).
- Im Repo weiterhin nur Kommentar `config/ai-providers.yaml:59-64` + Capability `hook-agent-id` (`hooks.py:562-563`); Evidence-Doc fehlt → Doku-Lücke (S), kein funktionales Risiko mehr für die Strict-Mode-Logik. Hooks-Audit-Zeile 39 „UNVERIFIZIERT“ → bestätigt; Punkt in #1210/#1250 kann von „Risiko“ auf „Evidence nachtragen“ heruntergestuft werden.

## 4 Viz / Extensions / ReqogniLoom

### 4.1 `viz-report.py` Escaping (Prio-Audit (U))
- ✔ **bestätigt — kein HTML-Escaping:** `scripts/viz-report.py` importiert kein `html` (Imports `:25-33, :48-49`), `html.escape` = 0 Treffer. Agent-Cards `:340-348` (`{status_icon} {name}`, `{status}`), Timeline `:352-356` (`<td>{msg}</td>`) setzen Rohstrings in f-String-HTML. Quelle der Strings: Event-Log (`agent`, `task`, `tool`, `msg` aus `.meta-viz/events.jsonl`, `:154-197`) = LLM-/Tool-kontrollierter Text.
- Beispiel-Payload (statisch nachvollzogen): Agentenname `x<img src=x onerror=alert(1)>` → landet 1:1 in `<div class="agent-name">… x<img src=x onerror=alert(1)></div>`. Nur die D3-Daten sind `json.dumps`-serialisiert (`:363-374`), aber ohne `</script>`-Escaping innerhalb `<script>`.
- Schwere: niedrig–mittel (lokale Datei, Report wird im Browser des Entwicklers geöffnet; Vektor = Prompt-Injection in Agentennamen/Task-Text). Prio-Audit-Punkt 2 „Escaping (U)“ → jetzt belegt; Issue-Vorschlag: `html.escape()` an 4 Stellen + `json.dumps(...).replace("</", "<\\/")`.

### 4.2 ReqogniLoom-Katalog vs. Plugin-Tool-Namen (C1 [unverifiziert])
- ✔ **bestätigt per Laufzeit-Beobachtung dieser Session:** Plugin-MCP-Server heißen in Claude Code `plugin:<plugin>:<server>`, ihre Tools `mcp__plugin_<plugin>_<server>__<tool>` (Beleg: Honcho-Plugin erscheint in dieser Session als `mcp__plugin_honcho_honcho__chat`; ReqogniLoom-Plugin-Server als `plugin:reqogniloom:reqogniloom`). Die Plugin-Agents (`reqogniloom:change-manager` u. a.) listen `mcp__reqogniloom__adr.read …` → zeigen auf einen Server namens `reqogniloom` = Katalog-Server aus `config/plugin-catalog.yaml:240-282` (`.mcp.json`), nicht auf den Plugin-Server.
- Katalog-Tool-Liste (`plugin-catalog.yaml` `allowed`/`blocked`) und Repo-Skill .claude/skills/mcp-reqogniloom/SKILL.md:12-94 sind namensgleich (Namespace.Op-Form), Konsistenz untereinander ✔; Konflikt besteht nur zum Plugin-Namensraum.
- Konsequenz: C1 bleibt **hoch**, Unsicherheitsmarker streichen.

### 4.3 viz-logger: Content-Length statt NDJSON ⇒ CONNECT_TIMEOUT (A1)
- ✔ **bestätigt gegen Spezifikation:** MCP-Spec 2025-06-18 §stdio (modelcontextprotocol.io, abgerufen 2026-11-15): „Messages are delimited by newlines, and MUST NOT contain embedded newlines“; kein Content-Length-Header im stdio-Transport. `scripts/viz-logger.py:286-289` sendet `Content-Length: N\r\n\r\n`, `_read_message` `:296-320` liest byteweise bis `\r\n\r\n` → bei NDJSON-Client kommt der Delimiter nie → Blockade bis Timeout. `.mcp.json` startet genau diesen Pfad (`python3 scripts/viz-logger.py --mcp`); `viz-logger-mcp.mjs:16,95` verwendet dasselbe falsche Framing.
- Laufzeit-Indiz: diese Session meldet `viz-logger (CONNECT_TIMEOUT) … timed out after 30000ms`. Schwere hoch (Feature komplett tot) bleibt.

## 5 Einstellungs-Audit

### 5.1 Leitet sync Strict-/Fallback-Duplikate ab?
- ✔ **ja — `variables.*`-Duplikate sind tot:** Reihenfolge in `build_variables` (`config.py:2812-2832`): `_build_core_variables` übernimmt `config.variables` (`:1708-1714`), danach überschreibt `_build_orch_variables` `ORCHESTRATOR_STRICT` aus `orchestrator.strict` (`:2015`) und `UNKNOWN_FALLBACK_*` aus `orchestrator.unknown-fallback` (`:2206-2219`). `variables.ORCHESTRATOR_STRICT`/`UNKNOWN_FALLBACK_*` in `project.yaml` wirken nie → Entfernung sicher.
- `mode: strict` vs. `strict: true`: `_resolve_orch_mode` (`variables.py:289-330`) nimmt `mode` vorrangig, `strict` nur Legacy-Fallback → zweifach redundant, aber konsistent; `strict: true` kann entfallen, wenn `mode` gesetzt bleibt.

### 5.2 SE-Artefakte bei `systems-engineering.enabled: false`
- ◐ **teils automatisch:** SE-Rollen werden übersprungen (`agent_sync.py:647-656` „systems-engineering is disabled“ via `is_role_enabled`). Die 3 `se-cascade-*`-Skills bleiben **absichtlich** (nur Description im Kontext) — `config/rules-presets.yaml:161-165` („SE_ENABLED=false projects keep only the SKILL.md description“). `.claude/skills/se-cascade-*` existieren entsprechend. Empfehlung „SE-Skills entfernen“ → wäre ein Framework-Änderung (Preset), kein Konfig-Aufräumen.

### 5.3 Warum `.continue/` nicht gitignored
- ✔ **erklärt, by design:** `gitignore.py:256-260` emittiert Provider-Root-Einträge nur für **aktive** `providers` (`collect_provider_roots(providers, …)`); Continue ist nicht in `ai-providers` (`project.yaml:7-10`) → kein `.continue/`-Eintrag; `.gitignore:4` enthält nur .continue/config.local.yaml. Das untracked `.continue/` ist Altlast einer früheren Aktivierung. Kein Bug; Aufräumen = Verzeichnis löschen oder Custom-Entry.

### 5.4 Wirkt `checkpointing: true`?
- ◐ Template-seitig ja: `config.py:2162-2164` → `CHECKPOINTING_ENABLED` → Conditional-Block im Orchestrator. Laufzeit-seitig **nein** unter Claude (s. 1.2: Plan-Mode blockiert Write; kein `.meta-viz/checkpoints/` vorhanden).

### 5.5 `context-profile: compact` Render-Test (verify-full-base vs. verify-compact)
| Artefakt | full (B) | compact (B) | Δ |
|---|---|---|---|
| `CLAUDE.md` | 5 381 | 5 390 | ±0 |
| `.claude/rules/*` (10→11 Dateien, +`external-tools-drift.md`) | 8 204 | 8 643 | **+5 %** |
| `AGENTS.md` (Opencode+Gemini) | 17 091 | 15 642 | −8,5 % |
| .claude/agents/orchestrator.md | 73 523 | 37 053 | **−50 %** |
| .opencode/agents/orchestrator.md | 73 373 | 36 829 | −50 % |
| .gemini/agents/orchestrator.md | 73 328 | 38 099 | −48 % |
| .claude/agents/developer.md | 13 282 | 13 282 | 0 |
| alle `.claude/agents/*.md` | 553 647 | 517 177 | −6,6 % |
- tiktoken (cl100k): Claude always-on (CLAUDE.md+rules) **3 996 → 4 128 Tok (+3 %)**; Bytes/4-Proxy 3 396 → 3 508. `AGENTS.md` 4 818 → 4 367 Tok (−9 %). Orchestrator 18 623 → 9 619 Tok (−48 %). Bytes/4 unterschätzt tiktoken hier um ~15 % (deutscher Text).
- Warnungen compact: 8 × `context.rule-compacted-away: rule '<use-lazy-rules|repo-containment|no-worktree-isolation|dod-criteria>' removed for provider 'Opencode'/'Gemini' and no skill exists for it` + 2 × `external-tools: undeclared artifact '.opencode|.gemini/skills/branch-guard'` → **Inhaltsverlust** für Opencode/Gemini (Repo-Containment- und DoD-Regel verschwinden ersatzlos).
- ✘ Framework-Settings-Audit-Erwartung „potenziell −30 % Roster/always-on“ **widerlegt für Claude** (always-on +3 %); ✔ Ersparnis nur im Orchestrator-Prompt (−50 %, pro Spawn ~9 k Tok). Empfehlung „noch behalten (full)“ bestätigt; Spike-Ergebnis: compact erst nach Skill-Fallback für die 4 Rules.

## 6 Nebenbefunde

### 6.1 Hook-Verdrahtung `auto-github-release.sh` / `lifecycle-check.sh`
- ✔ **bewusst (Opt-in-Design), kein Drift:** `hooks.py:472-477` — „All hook scripts are always copied … Registration in settings.json is opt-in per project: `hooks: { <name>: { enabled: true } }`“. `project.yaml:155-161` aktiviert nur `dod-push-check`, `graphify-read-guard`, `graphify-search-guard` → genau diese stehen in .claude/settings.json (plus `orchestrator-guard`, `repo-containment`, die über eigene Feature-Flags registriert werden). `viz-log` wird nur bei `viz.mode dynamic/full` registriert (`hooks.py:534-540`, `:618-619`), hier `viz.enabled: false`.
- Konsequenz: Framework-Settings-Audit Zeile 96 „tote/geparkte Hooks“ → korrekt als „nicht aktivierte Opt-in-Hooks“; Severity S bleibt, Formulierung „Drift“ streichen.

### 6.2 Phantom-Datei docs/guides/admin-ui-architecture.md
- ✔ **bestätigt Phantom:** Datei existiert nicht; reale Datei ist `docs/concepts/planned/admin-ui-architecture.md` (vgl. `knowledge/wiki/concepts/admin-ui-architecture.md:7-8`). Kein Verweis auf docs/guides/admin-ui-architecture.md im Repo (Treffer nur in .tmp/-Audits, in #1276 laut Prio-Audit). → #1276-Text korrigieren. Hinweis: Referenz zur Admin-UI liegt in `docs/api/admin-ui-reference.md`; docs/guides/admin-ui-architecture.md existiert nicht.

### 6.3 `*.sync-backup-*`-Dateien
- ✔ **bestätigt:** `find . -name "*.sync-backup-*" | wc -l` = **702**; Verteilung: .tmp/head-agents 407, `.claude/agents` 58, `.gemini/agents` 54, `.opencode/agents` 49, .tmp/pytest-basetemp-full 44, `.claude/hooks` 18, `.opencode/skills` 16, `.claude/skills` 16. 451 davon in .tmp/ (ungetrackt, Aufräumen trivial); 251 in Provider-Verzeichnissen (`--prune-sync-backups` existiert laut `sync.py --help`).

### 6.4 Weitere Nebenbefunde aus dem Render-Lauf
- 3 unaufgelöste Platzhalter (`CONTEXT_FILE` in agent-meta-manager/-scout/knowledge-migrator, `PIPELINE_DETAIL_BLOCKS`/`INTENT_ROUTING_TOOLS` in orchestrator) warnen nur bei ≥ 1 zusätzlichem Provider (Continue-Prompts); „D3(a) grace: until 2.1.0 this only warns; from 2.1.0 it aborts“ → tickende Sync-Abbruchquelle.
- .kimi-code/mcp.json: inline `${VAR}`-Expansion UNVERIFIED (Warnung) — deckt sich mit Prio-Audit #13.
- Schema-Validierungswarnung wird pro Sync doppelt ausgegeben.
- `external/awesome-claude-code` dynamic clone bei `ac65d81` statt pinned `3d8bde25` (Warnung in jedem Lauf, auch ohne Netz).

## 7 Korrekturen an früheren Schweregraden (Behauptung → Urteil → Konsequenz)

| # | Behauptung (Quelle) | Urteil | Konsequenz für Issue |
|---|---|---|---|
| 1 | O9 „`handoff.t-size-limit` wird vom Schema abgelehnt“ (Rollout :27) | ✘ nur Warnung, Key wirkt | Schwere M→S; Issue „Schema um `t-size-limit` ergänzen + Doppel-Ausgabe“ (neu, S) |
| 2 | O2 Gemini-Orchestrator ohne Dispatch-Tool, 44× `invoke_subagent` (Rollout :88) | ◐ Allowlist nur SOURCE-DERIVED, aber CLI kennt `invoke_subagent` nicht | Schwere bleibt hoch; Text: „kein belegter Dispatch-Pfad“; Teil von #1160-Entscheidung |
| 3 | `permissionMode: plan` × `Write` [UNVERIFIZIERT] (Rollout :86/:148) | ✔ Plan blockiert Edits (Doku), Checkpoint-Dir fehlt | **neuer M-Defekt**: `role-defaults.yaml:11` → `default` oder Checkpointing als Claude-untauglich markieren; betrifft #1176 |
| 4 | „degrades loudly to subagent“ (Prosa/Matrix Gemini/Mammouth primary) | ◐ nur im `--check`, Sync still; Prosa zeigt deklarierte Position | neuer S/M-Defekt „effektive statt deklarierte Position rendern + Sync-Warnung“; Matrix-Zellen ✔→◐ |
| 5 | Opencode primary „✔ E: `mode: primary`+`default_agent`“ (Matrix) | ◐ auf v2 kein `default_agent`-Merge → Gate SUSPENDED | Zelle ◐; Doku `opencode.md:354` korrekt; Issue „v2 default_agent-Merge“ (M) prüfen, ob offen |
| 6 | Mode-Last-Writer im shared AGENTS.md [UNVERIFIZIERT] (Rollout :123) | ◐ kein Last-Writer; Gate-Text = weakest tier by design | Befund umformulieren: „hook-loser Sharer stuft AGENTS.md-Gate für alle auf advisory“ (Doku/UX, S) |
| 7 | Background-Wait Codex „native wait_agent nicht gemappt“ (Matrix) | ◐ `spawn_agent`/`wait_agent` sind gemappt | Zelle ✘→◐; #1176-Text anpassen |
| 8 | `agent_id` im PreToolUse [UNVERIFIZIERT] (Hooks :39, FW :189) | ✔ dokumentiert, keine Mindestversion | #1210/#1250: Risiko → „Evidence-Doc nachtragen“ (S) |
| 9 | Gemini-Adapter-Laufzeit UNVERIFIZIERT (Hooks P6) | ✔ Dispatch + `hooks.json` + Provider-Filter belegt; Harness-Load offen | Status „statisch+Render verifiziert“; Rest = Harness-Test |
| 10 | Opencode-Plugin-Autoload nur Doku (Hooks) | ○ nicht aus Code ableitbar | bleibt UNVERIFIZIERT |
| 11 | viz-report Escaping (U) (Prio :43) | ✔ kein Escaping | Issue „html.escape in viz-report“ (M, lokal-XSS) |
| 12 | C1 Plugin-Tool-Namen ≠ Katalog [unverifiziert] (Viz :114) | ✔ per Session-Beleg | C1 hoch bestätigt, Marker streichen |
| 13 | A1 Content-Length statt NDJSON (Viz) | ✔ Spec + Session-Timeout | hoch bestätigt |
| 14 | `knowledge.schema-language` Auflösung (Lang :202) | ✘ Key inert | neuer S-Defekt „toter Config-Key“ |
| 15 | PR-Texte driften EN (Lang) | ✔ 23/30 EN, ab #1218 100 % | Regel-Lücke (keine PR-Body-Sprachregel) → S |
| 16 | speech-mode fehlt in AGENTS.md (Lang :12) | ✔ Claude-only | bestätigt |
| 17 | Strict-/Fallback-Duplikate sicher entfernbar? (FW :59) | ✔ sync überschreibt | Aufräumen S, risikofrei |
| 18 | SE-Skills entfallen automatisch? (FW :68) | ◐ Rollen ja, Skills bewusst nicht | Empfehlung → Framework-Preset-Frage |
| 19 | `.continue/` nicht gitignored, Grund unklar (FW :57) | ✔ nur aktive Provider werden ignoriert | kein Bug; Verzeichnis löschen |
| 20 | `context-profile: compact` −30 % (FW :42) | ✘ always-on +3 %, nur Orchestrator −50 %, Inhaltsverlust Opencode/Gemini | „noch behalten“ bestätigt; Spike-Ergebnis dokumentiert |
| 21 | Hooks `auto-github-release`/`lifecycle-check` tot/Drift (FW :96) | ✔ bewusst Opt-in | „Drift“ streichen |
| 22 | Phantom docs/guides/admin-ui-architecture.md (Prio) | ✔ Phantom | #1276 korrigieren |
| 23 | 702 Backups / 407 in .tmp/head-agents (FW) | ✔ exakt | `--prune-sync-backups` + `.tmp` räumen |

Zählung: ✔ 13 · ✘ 4 · ◐ 7 · ○ 1 (Tabelle; Unterpunkte s. Abschnitte).

## Token-/Aufwandsschätzung
- Kontextverbrauch dieses Subagenten ≈ 100–110 k Tok (graphify 2 Queries, ~14 Batch-Greps, 4 WebFetches, 6 Syncs in Kopien, 2 Doku-Reads).
- Rohdaten: .tmp/audit/scratch/vf-*.txt|json, .tmp/audit/vf-batch7..13.txt, Kopien `verify-*` (6 × 38–60 MB, löschbar).

## Offene Lücken
- Harness-Laufzeit: ob Antigravity `.agents/hooks.json` lädt; ob Opencode `.opencode/plugins/` autoloaded; ob Kimi `${VAR}` expandiert.
- `rules.py:288` ohne `active_set` (Instanzzahl) nicht reproduziert.
- Codex `close_agent`-Mapping, `.codex/config.toml max_depth` nicht geprüft.
- Antigravity-Oberfläche (`.agents/agents`) nicht gerendert/verglichen (nur `.gemini/agents`).
- Keine Tests ausgeführt (Auftrag).
