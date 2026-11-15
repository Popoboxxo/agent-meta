# Audit: Orchestrierungs-Einstellungen & -Modus — Rollout je Provider

- **Status:** Analyse (kein Beschluss)
- **Datum:** 2026-11-15
- **Quelle:** Fable/Opus-Audit, Verifikationsstand siehe Verifikationsbericht (docs/analysis/2026-11-15-fable-verification-of-unchecked.md)
- **Modellherkunft:** Opus-Fortsetzung nach Fable-Rate-Limit
- **Issues:** #1237–#1276 (Audit-Folgeissues)
- **Zugehörige Berichte:** docs/analysis/2026-11-15-fable-framework-settings-audit.md, docs/analysis/2026-11-15-fable-language-feature-audit.md, docs/analysis/2026-11-15-fable-orchestration-rollout-audit.md, docs/analysis/2026-11-15-fable-verification-of-unchecked.md

- Datum: 2026-11-15 · Stand: origin/main `92d41a90` (lokal HEAD `5e16ecf8` Parking-Branch) · nur Analyse
- Status: ABGESCHLOSSEN

## 0. Methodik / Basis

- origin/main per `git archive` nach .tmp/audit/scratch/om/ (HEAD-Parking-Branch liegt 5 Commits zurück: u.a. `orchestrator.md` 8.12.0→8.12.2, `use-orchestrator.md`, `opencode_v2_config.py`).
- Gerenderte Agenten sind gitignored (`.gitignore:23 .claude/`) → nur lokaler Stand prüfbar; lokal nur **Claude/Opencode/Gemini** aktiv (`project.yaml:6-9 ai-providers`), Stand 2026-11-13 / Template 8.12.0 (**stale** ggü. 8.12.2).
- Codex/Copilot/Continue/Mammouth/KimiCode/ZCode: kein Rendering im Repo → Matrix nur aus Quellen/Capabilities/Tests (Spalte (e) „nicht prüfbar" wo Runtime nötig).
- Pfade unten relativ zu origin/main-Snapshot.

## 1. Konfig-Pfad

### 1.1 Keys (Schema `config/project-config.schema.json`) → Consumer

| Key | Default | Consumer | Wirkung |
|---|---|---|---|
| `orchestrator.mode` (strict/advisory/main-chat) :2473 | strict | `variables.py:289 _resolve_orch_mode` (einziger Resolver, D1b) → `ORCH_MODE_*` | Rule-/Agent-Prosa, main-chat unterdrückt Orchestrator-Emission (`config.py:2030`) |
| `orchestrator.enabled`/`strict` (Legacy) | true/true | Fallback in `variables.py:329-336`; `ORCHESTRATOR_STRICT` `config.py:2015` | `ORCHESTRATOR_STRICT` liest **nur** Legacy-`strict`, nie `mode` → in keinem Template genutzt (nur `placeholders.py`, `meta_optimizer.py`) = **tote Variable** |
| `orchestrator.topology` :2483 | unset → derived | `topology.py:186 resolve_topology` (8 Aufrufstellen: `context.py` ×4, `rules.py:288`, `provider_transform.py:507`, `isolation.py:917`, `sync_pipeline.py` ×3, `cli_commands.py:381`) | Prosa (`ORCH_TOPOLOGY_EFFECTIVE_*`), Opencode `mode: primary`/`default_agent`, Runtime-Gate |
| `orchestrator.provider-overrides.<P>.{mode,topology}` :2617 | – | `topology.py:96`, `variables.py:310` | per Provider |
| `orchestrator.max-instances`/`singleton` | 1 / nur `true` | `topology.py:365`, `rules.py`, consistency/topology.py | `ORCH_MAX_INSTANCES` in `a2a-delegation-gates.md:12,23` |
| `orchestrator.direct-dispatch-enabled` | true | `config.py:2016` → `DIRECT_DISPATCH_*` | `orchestrator.md:203`, `use-orchestrator.md:60` |
| `orchestrator.delegation.max_depth` :2587 | 10 | `A2A_MAX_DEPTH` (`orchestrator.md:382`, `a2a-delegation-gates.md:43`), `dispatch_depth.py` | Prompt-Soft-Gate; Capability `required_depth: 2` (alle Provider) ist davon **unabhängig** (Codex-TOML / `subagent_depth`) |
| `orchestrator.handoff.protocol` | a2a-v1 | `A2A_PROTOCOL_ENABLED`/`A2A_HANDOFF_BLOCK` | Prompt |
| `orchestrator.handoff.t-size-limit` | 300 | `config.py:127-143` | **Schema-Lücke:** `handoff` hat `additionalProperties: false` und nur `protocol` (Schema :2575-2585) → dokumentierter Key (Spec 2026-11-09) wird von Schema-Validierung abgelehnt [Schema-Erzwingung im Sync nicht geprüft] |
| `orchestrator.require-runtime-gate` | false | consistency/orchestrator_strict.py:175,274 | WARNING→ERROR bei hook-losem Strict |
| `orchestrator.native-extensions.*`, `unknown-fallback.*` | true / – | nur `config.py` → Variablen | reine Prosa |
| `delegation.a2a_envelope` (Top-Level) :2457-2461 | false | **kein Consumer** in `scripts/` | **tote Option** |
| `auto_commit.mode` (off/suggest/auto/custom) :1499 | off | `auto_commit.py`, `AUTO_COMMIT_BLOCK` (65 Template-Stellen) | Commit-Authority-Tier je Rolle |
| `context-profile` / `provider-overrides.<P>.context-profile` | full | `context_profile.py` u.a. | compact-Golden (`tests/fixtures/compact-golden/`) |
| `spec-plan-workflow.enabled`, `dod.spec-plan-required` | – / false | `SPEC_PLAN_WORKFLOW_ENABLED` | Prompt-Gate |
| `subagent_permissions.mode` (:1618ff, enthält ebenfalls `strict`) | – | `subagent_permissions.py` | **dritter „strict"-Begriff** neben `orchestrator.mode`/`.strict` → Verwechslungsgefahr |

### 1.2 Auflösung Topologie (`topology.py`)

- Reihenfolge: Provider-Override > Projekt > derived (`:114-122`); derived = `primary` nur wenn `providers.<P>.primary-role` gesetzt **und** Rolle aktiv (`:135-140`), sonst `subagent`; `hybrid` nie derived.
- Clamp: `topology_support=false` oder `verified_state=UNVERIFIED` → `topology_degrade` (falls gültige Topologie) sonst Fail-Safe `subagent` (`:147-183`).
- `primary-role` existiert **nur für Opencode** (`ai-providers.yaml:268`) → Claude/KimiCode/Continue (primary=supported) leiten nie `primary` ab; explizit deklariert wirkt `primary` dort nur als Prosa (kein Entry-Point-Mechanismus, s. §2).
- Validierung: `_validate_orchestrator_topology` (`config.py:505`, main-chat×topology = Fehler, Tabelle `config.py:436-447`); `--validate`/`--check`: consistency/topology.py (degraded, hybrid-unverified, main-chat-supersedes, gate-inactive, default-agent-conflict, strict-primary-entry-mismatch).

### 1.3 Gültigkeit je Topologie (Capability-Zellen `provider-capabilities.yaml`)

| Provider | primary | subagent | hybrid | effektiv bei `topology: subagent` | bei `primary` |
|---|---|---|---|---|---|
| Claude | ✔ | ✔ | ✘→subagent | subagent | primary (nur Prosa) |
| Opencode | ✔ | ✔ | ✘→subagent | subagent | primary (+`mode: primary`, `default_agent`) |
| Gemini | ✘→subagent | ✔ | ✘ | subagent | subagent (degraded) |
| Continue | ✔ | **✘ (degrade=`sequential-text`, Mechanismuswort)** | ✘ | **subagent** (Fail-Safe = deklarierter Wert → „Koinzidenz", kein Degraded-Finding, `topology.py:258-261`) | primary (nur Prosa) |
| Copilot/Mammouth/Codex/ZCode | ✘→subagent | ✔ | ✘ | subagent | subagent (degraded) |
| KimiCode | ✔ | ✔ | ✘ | subagent | primary (nur Prosa) |

- **`hybrid` ist bei allen 9 Providern `support=false`/UNVERIFIED** → immer `subagent` + Finding `hybrid-unverified` = faktisch tote Option.
- **Continue:** Fail-Safe landet auf einer als unsupported markierten Zelle; derived (kein `primary-role`) ebenfalls `subagent` → Continue rendert dauerhaft Subagent-Prosa ohne Dispatch-Fähigkeit (`subagent_dispatch: false`), ohne Warnung.

### 1.4 Namenskollision `topology`

- `context_file.topology` (unified/per-provider, Schema :1072, Override :1093) vs. `orchestrator.topology` (:2483, Override :2617): identische Schlüssel- und Override-Form, völlig andere Semantik.
- Code liest sauber getrennt (`topology.py:92-98` nur `orchestrator.*`) → **kein Bug, nur Doku/UX-Risiko** (bestätigt Concept-Audit; Zeilen dort :1074/:2485 → jetzt :1072/:2483).

## 2. Rollout-Matrix

Legende Zelle: ✔ / ✘ / ◐ teilweise / ? nicht prüfbar. Kürzel in Zelle: **P** = nur Prompt-Prosa, **E** = technisch erzwungen. Spalten (a) gerendert, (b) richtiges Artefakt, (c) capability-korrekt, (d) Test/Golden, (e) Wirkung — zusammengefasst je Zelle, Beleg in Fußnote.

### 2.1 Provider × Einstellung

| Einstellung | Claude | Opencode (v2) | Gemini | Codex | Copilot | Continue | KimiCode | Mammouth | ZCode |
|---|---|---|---|---|---|---|---|---|---|
| topology `subagent` | ✔ P+Agent-FM [1] | ✔ `mode: subagent` FM [2] | ✔ P (+`define_subagent`-Bootstrap) [3] | ◐ P, (d) nur param. Tests | ◐ P | **✘** unsupported, still subagent [4] | ✔ P | ✔ P | ✔ P |
| topology `primary` | ◐ nur P, kein Entry-Mechanismus [5] | ✔ E: `mode: primary`+`default_agent` [6] | ✔ degraded→subagent, Finding | ✔ degraded | ✔ degraded | ◐ nur P [5] | ◐ nur P [5] | ✔ degraded (UNVERIFIED-Zelle) | ✔ degraded |
| topology `hybrid` | ✘ immer →subagent [7] | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| Strict-Mode (`mode: strict`) | ✔ E orchestrator-guard (mode+Override-aware, `orchestrator-guard-impl.sh:1394ff`) | ◐ E nur bei eff. `primary` (Root-deny), unter `subagent` P (#1249) | ✔ E via Antigravity-Adapter (Laufzeit UNVERIFIZIERT lt. Hooks-Audit) | ✘ P (hooks=false) | ✘ P | ✘ P | ✘ P | ✘ P | ✘ P |
| Spec/Plan-Gate | ✔ P (`use-orchestrator.md`, orchestrator §SPEC_PLAN) | ✔ P (AGENTS.md:147 embedded) | ✔ P (AGENTS.md) | ? P | ? P | ? P | ? P | ? P | ? P |
| A2A-Limits (depth/t-size) | ✔ P (`A2A_MAX_DEPTH`=10, `t`=300); Plattformtiefe separat | ✔ P; `experimental-subagent-depth: 3` separat | ✔ P | ◐ P + TOML `[agents] max_depth≥2` (`dispatch_depth.py`) | ✔ P | ✔ P | ✔ P | ✔ P | ✔ P |
| Direct-Dispatch | ✔ P (`orchestrator.md:203`, `use-orchestrator.md:60`) | ✔ P | ✔ P | ? | ? | ? | ? | ? | ? |
| `route_intent` | ✔ P-Fallback (`route_intent_tool: false` überall) [8] | ✔ P-Fallback | ✔ P-Fallback | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| `INTENT_ROUTING_TABLE` | ✔ nur main-chat (`use-orchestrator.md:64-69`) | ✔ dto. | ✔ dto. | dto. | dto. | dto. | dto. | dto. | dto. |
| auto_commit-Tier | ◐ P + Guard; Grant rollen-unabhängig (#1210) | ✘ P; `shell: allow` ⇒ jeder Worker kann committen (Hooks-Audit B.2) | ◐ wie Claude (Adapter) | ✘ P | ✘ P | ✘ P | ✘ P | ✘ P | ✘ P |
| Worker-Report-Contract | ✔ P + Test `test_orchestrator_worker_report_contract.py:65-109` | ✔ P (kein Test) | ✔ P (kein Test) | P | P | P | P | P | P |
| Background-Wait (#1176) | ◐ P + `SendMessage`/`TaskStop` im FM (`ai-providers.yaml:133`) [9] | **✘** Prosa nennt `TaskStop`, Tool fehlt [9] | **✘** dto. + `SendMessage`-Push [10] | ✘ native `wait_agent`/`close_agent` nicht gemappt | ✘ | n/a (kein Dispatch) | ✘ | ✘ | ✘ |
| Singleton/Anti-Recursion | ✔ E strukturell (Worker ohne `Agent`-Tool) + P | ◐ Worker `subagent: deny`; Orchestrator `subagent: allow '*'` ⇒ Selbst-Spawn nicht verhindert | ◐ P (Tools kein Allowlist-Beleg) | ? | ? | n/a | ◐ `subagent_allowlist_required: true`, Doctor-Fixture | ? | ? |
| context-profile `compact` | ✔ Golden `tests/fixtures/compact-golden/orchestrator.md` | ? kein eigenes Golden | ? | ? | ? | ? | ? | ? | ? |

Fußnoten (Belege):
1. .claude/agents/orchestrator.md FM: tools `TodoWrite, Agent, Read, Write, SendMessage, TaskStop`, `permissionMode: plan` (aus `role-defaults.yaml:11`). ⚠ `plan` = read-only-Subagent in Claude Code vs. `Write` für Checkpoints (`checkpointing: true`) — **[UNVERIFIZIERT]** ob Schreiben blockiert.
2. .opencode/agents/orchestrator.md FM: `mode: subagent`, `permissions` edit deny außer .tmp/**, `.meta-viz/**`; shell deny; subagent allow. `provider_transform.py:515-526`.
3. .gemini/agents/orchestrator.md FM tools: `TodoWrite, view_file, replace_file_content` — **kein Dispatch-Tool**, Prosa ruft 44× `invoke_subagent`. `provider-tools.yaml:53-55` („Gemini has no subagent dispatch tool") **widerspricht** `provider-capabilities.yaml native_agent_tools: [define_subagent, send_message, invoke_subagent]`. Ob Gemini-`tools` eine Allowlist ist: **[UNVERIFIZIERT]**.
4. Continue: `topology_support.subagent: false`, `topology_degrade.subagent: sequential-text` (kein gültiger Wert) → Fail-Safe `subagent` = deklariert → `degraded_from=None` (`topology.py:258-261`) ⇒ kein Finding.
5. Entry-Point-Emission nur über `primary-role` (nur Opencode, `ai-providers.yaml:268`) und nur im `opencode-native*`-Mechanismus (`provider_transform.py:483-526`); `main_agent_selectable` (Claude/Continue/Kimi = true) wird nur von `scripts/topology-probe.py` gelesen ⇒ Claude/Continue/Kimi `primary` = Prosa „ist Session-Einstieg" ohne Mechanismus (Claude: kein `agent`-Key in settings).
6. `context.py:1871-1872,2016` `default_agent` nur bei eff. `primary`; Goldens `orchestrator.derived-primary.opencode.md`.
7. `provider-capabilities.yaml` alle 9: `hybrid: false/UNVERIFIED`, `degrade: subagent`; consistency/topology.py `hybrid-unverified` feuert immer.
8. `agent_sync.py:533` `ROUTE_INTENT_CALLABLE` aus `route_intent_tool` (überall false) ⇒ §3 `orchestrator.md:102-106` Else-Zweig überall; `INTENT_ROUTING_TOOLS` wird trotzdem emittiert (Token-Last, #1161).
9. `orchestrator.md:280` „On timeout `TaskStop` it (where granted)"; `primary-role-tools` nur Claude; `provider-tools.yaml` whitelisted `SendMessage/TaskStop` nur unter `claude`. Gerendert: `.opencode/…orchestrator.md:364`, `.gemini/…:357` enthalten `TaskStop`-Anweisung. Test `test_rendered_claude_orchestrator_has_control_tools` nur Claude.
10. `orchestrator.md:270-272` `PROGRESS_CHAT_PUSH_ENABLED` = `provider_hooks_supported(pc)` (`agent_sync.py:528`) ⇒ Gemini (hooks=true) bekommt `SendMessage(to:"main",…)` — falsche Capability-Kopplung (Hooks ≠ Messaging-Tool; Gemini-nativ `send_message`). .gemini/agents/orchestrator.md:353.

### 2.2 Gerendert vs. Quelle (lokal)

- Alle drei lokal gerenderten Orchestratoren `version 8.12.0`, Template `8.12.2` → **stale** (Diff HEAD↔origin/main betrifft `orchestrator.md`, `use-orchestrator.md`); Lokal kein Re-Sync laut Auftrag.
- Keine ungerenderten `{{…}}` in den drei Dateien (`grep -c '{{'` = 0).
- `.gemini/rules/` enthält nur `a2a-delegation-gates.md.sync-backup-20261006-011203` (Altlast); Regeln für Gemini embedded in `AGENTS.md` (`rules_read_channels: [embedded, skills]`) ✔.
- `opencode.json`: kein `default_agent` (konsistent mit `topology: subagent`) ✔.

### 2.3 Tests/Goldens

- `tests/fixtures/topology-golden/`: nur Claude/Gemini/Opencode (`orchestrator.unset-derived-subagent.{claude,gemini,opencode}.md`, `derived-primary.opencode.md`, `declared-{primary,subagent}.md`, `singleton-declared-primary.md`).
- Übrige 6 Provider: nur parametrisierte Resolver-/Konsistenztests (6–8 Testdateien je Provider mit `topology`), **kein Render-Golden** des Orchestrators.
- Doctor-Fixtures: Copilot `orchestrator.agent.md` (Name-Suffix), KimiCode Allowlist, Opencode FM-Schema.

## 3. Konsistenz zwischen Providern

### 3.1 Gleiche Topologie `subagent` (dieses Repo)

| Aspekt | Claude | Opencode | Gemini |
|---|---|---|---|
| Orchestrator-Einstieg | Main Chat spawnt `orchestrator` via `Agent` | Main Chat (Build-Agent) → `task(subagent_type=…)`; `mode: subagent` | Main Chat muss `orchestrator` erst via `define_subagent` registrieren (Bootstrap-Hinweis Z. 15) |
| Singleton-Regel | CLAUDE.md (Agenten-Konfiguration), `use-orchestrator.md`, Agent-Persona | AGENTS.md embedded + Persona | AGENTS.md embedded + Persona |
| Dispatch-Tool im FM | `Agent` ✔ | Permission `subagent: allow` ✔ | **✘ keins** |
| Worker-Control | `SendMessage`, `TaskStop` ✔ | ✘ (Prosa nennt `TaskStop`) | ✘ (Prosa nennt `TaskStop`, `SendMessage`) |
| Delegationssyntax | `Agent(...)` | `task(` 44× | `invoke_subagent` 44× — Syntax-Engine korrekt provider-spezifisch ✔ |
| Strict-Wirkung | Hook E | P (Gate nur bei `primary`) | Hook E (Adapter) |

- Shared Context-File (`AGENTS.md` Opencode+Gemini): Positions-Flags werden bei Uneinigkeit neutralisiert (`context.py:819-873`, `:2624-2660`) ✔. **Mode** (`ORCH_MODE_*`) für embedded Rules wird dagegen mit dem Mode des gerade rendernden Providers gesetzt (`context.py:2900-2903`), nicht neutralisiert ⇒ bei Provider-Override `main-chat` für nur einen Sharer gewinnt der letzte Writer **[UNVERIFIZIERT am Render; Code-Lesart]**.
- `rules.py:288` ruft `resolve_topology` **ohne** `active_set` (Docstring :255 verlangt ihn); `_topology_resolution` speist `resolve_orchestrator_instances` (:319) ⇒ derived-`primary` (Opencode) wird hier als `subagent` gesehen; Einfluss auf Instanzzahl **[UNVERIFIZIERT]**, Effective-Flags selbst korrekt via `_provider_topology_flags(active_set=…)` (:305).

### 3.2 Fehlerbilder

- **#1176 (Orchestrator endet vor Hintergrund-Agenten):** Gegenmaßnahme ist reine Prosa + Claude-Tools. Für Opencode/Gemini/Codex/Kimi fehlt Tool-Äquivalent bzw. Mapping (Codex hat nativ `wait_agent`/`close_agent`, Kimi `Agent(run_in_background)`); „(where granted)" kaschiert Lücke statt zu gaten.
- **Handback-Format:** Template nennt `SubagentHandback` nirgends (provider-neutral ✔); Kontrakt = „final message mit STATUS/RESULT", fehlender Report = `failed` (`orchestrator.md:267`). Barrier-Wrapper `||| agent=… |||` aus `orchestration.py:render_barrier_result` einheitlich ✔.
- **A2A-Envelope:** Capability `handoff_envelope_support`/`structured_handoff` werden **von keinem Code gelesen** ⇒ Envelope-Prosa (`A2A_HANDOFF_BLOCK`, 27 Stellen) auch für Continue/Copilot/Mammouth/ZCode/Kimi (envelope=false, `handoff_format: yaml_text_block`). Ob Delegationssyntax-Engine `handoff_format` nutzt: **[nicht geprüft]**.
- **Anti-Recursion:** Claude strukturell (Worker ohne `Agent`); Opencode Orchestrator `subagent: allow '*'` ⇒ Orchestrator→Orchestrator nicht blockiert (Hooks-Audit B.2); übrige nur Prosa (`ANTI_RECURSION_BLOCK`, 26 Templates).
- **Strict ohne Hooks:** consistency/orchestrator_strict.py:187-274 meldet WARNING (ERROR mit `require-runtime-gate: true`) ✔ — Prosa „Strict-Mode: der Main Chat führt kein Bash aus" steht trotzdem unverändert in AGENTS.md (Opencode/Gemini gemeinsam).

## 4. Drift / Lücken

- **Tote/inerte Optionen:**
  - `orchestrator.topology: hybrid` — überall unsupported (§1.3).
  - `delegation.a2a_envelope` (Schema :2461) — kein Consumer.
  - `ORCHESTRATOR_STRICT` (`config.py:2015`) — in keinem Template; zudem liest es Legacy-`strict` statt `mode`.
  - Capabilities `handoff_envelope_support`, `structured_handoff` ungelesen; `main_agent_selectable` nur in `topology-probe.py`; `route_intent_tool` überall false.
  - `ORCH_MODE_DISABLED` (deprecated Alias, `variables.py:348-352`) noch in `orchestrator.md:22`; Zweig in main-chat nie gerendert (Rolle nicht emittiert).
- **Schema-Drift:** `orchestrator.handoff.t-size-limit` gelesen (`config.py:138`), aber Schema `handoff.additionalProperties: false` ohne den Key.
- **Capability-Drift:** `provider-tools.yaml:53-55` vs. `provider-capabilities.yaml native_agent_tools` (Gemini); `primary-role-tools` nur Claude, `primary-role` nur Opencode — zwei Provider-Keys für dieselbe Rolle „Orchestrator-Werkzeuge".
- **Divergierende Defaults:** `orchestrator.delegation.max_depth` 10 (Prompt) vs. `required_depth` 2 (Capability) vs. Opencode `experimental-subagent-depth: 3` (Projekt) — drei Tiefenbegriffe ohne Querverweis/Check.
- **Provider-Literale im generischen Template:** `orchestrator.md` enthält `SendMessage`, `TaskStop`, `run_in_background` (Claude-Toolvokabular) und gelangt so in Opencode/Gemini (gerendert je 1-2×). `strip-claude-lines` (7 Provider, `ai-providers.yaml:241…956`) entfernt nur Zeilen mit „Claude", diese Literale nicht ⇒ Kaschierung greift hier nicht, Leak sichtbar.
- **Falsche Capability-Kopplung:** `PROGRESS_CHAT_PUSH_ENABLED` ← `hooks` statt Messaging-Tool (Fußnote 10).
- **Continue Silent-Degrade:** subagent-unsupported ohne Finding (Fußnote 4).
- **Claude `permissionMode: plan`** für Orchestrator vs. `Write`/Checkpointing — [UNVERIFIZIERT].
- **Tests:** Render-Goldens nur 3/9 Provider; Worker-Control-Test nur Claude; kein Test „Prosa nennt nur Tools, die im FM stehen".
- **Upgrade/Rollout Consumer:** Topologie (#1077) + Worker-Control (#1157) im CHANGELOG `[Unreleased]` (`CHANGELOG.md:21,33-45`); Key opt-in, unset = byte-identisch (AC-6) ⇒ keine Migration nötig ✔. commands/upgrade-meta.md/`update-meta.md` ohne Topologie-Hinweis; Nutzer-Doku nur `docs/concepts/active/orchestrator-topology.md` + README.
- **Lokale Altlasten:** stale Renders (8.12.0), `.gemini/rules/*.sync-backup-*`, `CLAUDE.md.sync-backup-20260913-200441` im Root.

## 5. Empfehlung

### 5.1 Befunde priorisiert

| # | Befund | Schwere | Aufw. | Issue |
|---|---|---|---|---|
| O1 | Worker-Control/Background-Wait nur Claude; Opencode/Gemini/Codex/Kimi bekommen `TaskStop`-Prosa ohne Tool | H | M | #1176 (erweitern) |
| O2 | Gemini-Orchestrator ohne Dispatch-Tool im FM; `provider-tools.yaml` widerspricht `native_agent_tools` | H (falls Allowlist) | S | neu: „fix(gemini): orchestrator frontmatter lacks dispatch tool; reconcile provider-tools vs native_agent_tools" |
| O3 | Opencode v2 Strict/Gate unter `subagent` nur advisory, Tier meldet `plugin` | H | S/M | #1249, #1256 |
| O4 | `PROGRESS_CHAT_PUSH_ENABLED` an `hooks` gekoppelt ⇒ Gemini erhält `SendMessage` | M | S | neu: „fix(orchestrator): gate chat push on a messaging-tool capability, not hooks" |
| O5 | Continue: unsupported `subagent` als Fail-Safe ohne Finding | M | S | neu: „fix(topology): report degradation when fail-safe lands on an unsupported cell" |
| O6 | `primary` auf Claude/Continue/Kimi nur Prosa (kein Entry-Mechanismus), `primary-role` nur Opencode | M | M | neu: „feat(topology): data-driven entry-point emission for main_agent_selectable providers" |
| O7 | `hybrid` überall tot | L | S | neu (oder in #1243 mitnehmen): Doku/Schema „hybrid reserved/experimental" |
| O8 | Tote Keys/Vars: `delegation.a2a_envelope`, `ORCHESTRATOR_STRICT`, `ORCH_MODE_DISABLED` im Template, ungelesene Capabilities | L | S | neu: „chore(config): remove dead orchestration keys and capability flags" |
| O9 | Schema blockt `orchestrator.handoff.t-size-limit` | M | S | neu: „fix(schema): allow orchestrator.handoff.t-size-limit" |
| O10 | Drei Tiefenbegriffe (max_depth 10 / required_depth 2 / experimental-subagent-depth 3) ohne Check | L | S | neu: Konsistenz-Check „depth coherence" |
| O11 | Claude-Toolliterale in generischem `orchestrator.md` | M | M | #885; #1257-Kette |
| O12 | Mode in shared AGENTS.md nicht neutralisiert; `rules.py:288` ohne `active_set` | L | S | neu (nach Verifikation) |
| O13 | auto_commit-Grant rollenunabhängig / Opencode ohne Git-Gate | M | M | #1210, #1256/#1257 |
| O14 | Namenskollision `topology` | L | S | #1243 |
| O15 | Render-Goldens nur 3/9 Provider; kein „Prosa-Tool ⊆ FM-Tool"-Test | M | M | neu: „test: orchestrator render goldens + tool-mention⊆frontmatter check for all providers" |
| O16 | `hooks.py:683` Claude-Writer-Fallback (betrifft Strict-Rollout neuer Provider) | M | S | #1252 |
| O17 | `INTENT_ROUTING_TOOLS`-JSON gerendert obwohl `route_intent` nirgends callable | L | S | #1161 (+ Intent-Routing-Plan) |

### 5.2 Quick Wins (S, ohne Rebaseline-Risiko außer markiert)

- O9 Schema-Key ergänzen (keine Render-Änderung).
- O5 Finding in consistency/topology.py (nur Check-Output).
- O8 `delegation.a2a_envelope`/`ORCHESTRATOR_STRICT` entfernen bzw. deprecaten (Schema + config.py).
- O16 Fallback entfernen (#1252, bereits geplant).
- O2 Prüfen + `provider-tools.yaml`-Kommentar/Mapping korrigieren (FM-Änderung ⇒ Gemini-Golden-Rebaseline).

### 5.3 PR-Schnitt

1. **PR A (Config/Checks, kein Render-Diff):** O5, O8 (Schema/Vars), O9, O10, O12-Check.
2. **PR B (Worker-Control capability-getrieben):** O1+O4+O11-Teil: neue Capability `worker_control_tools` (Mapping je Provider: Claude `SendMessage/TaskStop`, Codex `send_input/close_agent/wait_agent`, Gemini `send_message`), Prosa per Flag gegated statt „where granted"; ersetzt `primary-role-tools`. ⇒ **Rebaseline** Topology-/Compact-/Slimming-Goldens + ac01-baseline/hashes.json.
3. **PR C (Gemini-Dispatch):** O2 (+ Golden `unset-derived-subagent.gemini.md`).
4. **PR D (Tests):** O15 Goldens für 6 fehlende Provider + Tool-Mention-Check (vor PR B mergen, damit B gegen Goldens läuft).
5. Opencode-Gate (O3/O13) bleibt in #1249/#1256/#1257-Kette.

### 5.4 Rebaseline-Auswirkung

- PR B/C ändern Orchestrator-Prosa/FM ⇒ `tests/fixtures/{topology,compact,slimming}-golden/orchestrator*.md`, ac01-baseline/hashes.json, `context-hashes.json`, `generated-file-hashes.json`; Consumer-Projekte: Orchestrator-Diff beim nächsten `update-meta` (CHANGELOG-Eintrag nötig).
- PR A: nur Schema/Checks ⇒ keine Goldens.

### 5.5 Entscheidungen für den Nutzer

1. **`hybrid` behalten?** Empfehlung: als „reserved" markieren (Schema-Description + Check bleibt), nicht entfernen — Resolver/Tests existieren.
2. **Worker-Control als Capability statt `primary-role-tools`?** Empfehlung: ja (PR B) — behebt #1176 provider-übergreifend und entfernt Claude-Literale.
3. **Continue unter `subagent`:** Finding (WARNING) oder Clamp auf `primary`? Empfehlung: WARNING-Finding; `primary` für Continue wäre ebenfalls nur Prosa.
4. **`primary` für Claude/Kimi mechanisch ausrollen** (z. B. Claude `agent`-Setting)? Empfehlung: erst Runtime-Evidenz (Probe), bis dahin `primary` dort im Check als „prose-only" melden.
5. **Legacy `orchestrator.strict`/`enabled` deprecaten?** Empfehlung: ja, Deprecation-Warnung im Sync, Entfernung nach 1 Minor.

## Nicht geprüft

- Keine Syncs/Tests ausgeführt; lokale Renders stale (8.12.0) und nur Claude/Opencode/Gemini.
- Ob Gemini-Agent-`tools` eine harte Allowlist ist (O2-Schwere hängt daran).
- Claude `permissionMode: plan` × `Write` beim Orchestrator (Laufzeit).
- Ob JSON-Schema im Sync hart validiert wird (O9-Wirkung).
- Delegationssyntax-Engine × `handoff_format` (yaml_text_block) im Detail.
- Codex-TOML-/Copilot-`.agent.md`-/Continue-Prompt-Rendering des Orchestrators (keine Artefakte im Repo).
- Mode-Neutralisierung im shared AGENTS.md und `rules.py:288`-Effekt (nur Code-Lesart).
- Antigravity-Adapter-Laufzeit (aus Hooks-Audit übernommen, dort UNVERIFIZIERT).
- `docs/concepts/active/orchestrator-topology.md` nicht gegen Code abgeglichen.

---
Status: ABGESCHLOSSEN (2026-11-15)
