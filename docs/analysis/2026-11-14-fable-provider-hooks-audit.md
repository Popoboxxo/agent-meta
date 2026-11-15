# Vertiefte Konzeptprüfung: Provider-Agnostik + Hooks (Claude / Opencode v2)

- **Status:** Analyse (kein Beschluss)
- **Datum:** 2026-11-14
- **Quelle:** Fable-Grobaudit, nicht gegen Code vollständig verifiziert
- **Issues:** #1237–#1276 (Audit-Folgeissues), #1276 (Folge-Audit)
- **Zugehörige Berichte:** docs/analysis/2026-11-14-fable-concept-audit.md, docs/analysis/2026-11-14-fable-provider-hooks-audit.md, docs/analysis/2026-11-14-fable-viz-extensions-audit.md, docs/analysis/2026-11-14-audit-prioritization.md

- Datum: 2026-11-14 · Stand: Checkout `chore/main-checkout-parking` @ 5e16ecf8 (= origin/main gemergt) · read-only
- Basis: `docs/analysis/2026-11-14-fable-concept-audit.md` §2/§3 (nicht wiederholt, nur vertieft/korrigiert)
- Methodik: graphify query → gezielte Reads mit offset/limit; Belege als `Datei:Zeile`; Unverifiziertes mit **[UNVERIFIZIERT]**

## 0. Korrekturen am Vorab-Audit

| Vorab-Aussage | Befund jetzt | Beleg |
|---|---|---|
| „Hooks nur auf Claude verdrahtet" | Falsch auf Registry-Ebene: `has_hooks: true` für Claude, Gemini, Mammouth, Codex; **verifizierte** Protokolle nur `claude-code-json` (Claude) und `antigravity-hooks-json` (Gemini, via Adapter). Mammouth/Codex: `has_hooks: true` ohne `hook_protocol` → nichts deployt. | `config/ai-providers.yaml:26-27,175-176,622,734`; `scripts/lib/hooks.py:442-443,514-519` |
| „Dispatch über provider-benannte Mechanismen" | Bestätigt; zusätzlich: `# provider: Claude`-Header in 5 Hook-Skripten (Hook-Ebene selbst providerbenannt) | `hooks/1-generic/dod-push-check.sh:6`, `lifecycle-check.sh:6`, `sync-on-config-change.sh:6`, `hooks/0-external/graphify-*-guard.sh:9`; Filter `hooks.py:568-571` |
| „447 Zeilen Python in Bash" | Es sind 3 Heredocs in `hook_common.sh` (475-920, 965-1100, 1141-1177 ≈ 615 Z.) + 5 in `dod-push-check.sh`, 3 in `repo-containment-impl.sh`, je 1 in `orchestrator-guard-impl.sh`/`viz-log.sh` | `grep -c "<<'PY'"` |
| Doku `docs/analysis/2026-11-11-hook-api-ask-permission.md` | **Nicht im Worktree**; existiert nur als Commit `25df1b29` (Branch unbekannt, nicht auf main). Kopfbefund: `ask` nur für Claude belegt (per WebFetch-Extraktion, nicht Rohtext), alle anderen Provider `unbekannt`; Hooks hier nutzen ausschließlich `exit 2`. | `git show 25df1b29 --stat`; Dok §1-2 |

---

## A. Claude-spezifisch: Events, Payload, Permission-Mechaniken

### A.1 Was genutzt wird (Evidenztabelle)

| Mechanik | Nutzung | Verdrahtung | Beleg |
|---|---|---|---|
| `settings.json → hooks.PreToolUse[]` mit `matcher` + `command` | 5 Einträge: `Read\|Glob` (graphify-read), `Bash\|Grep` (graphify-search), `Bash` (dod-push), `""` (orchestrator-guard), `""` (repo-containment) | Writer `_update_settings_hooks` via Dispatch-Tabelle `hook_protocol → writer` | `.claude/settings.json`; `hooks.py:172,442` |
| `PostToolUse` | `auto-github-release.sh`, `lifecycle-check.sh`, `sync-on-config-change.sh` (Header `# event:`) | nur Header-Metadaten; im aktuellen settings.json **nicht** registriert (hooks-Config in project.yaml aktiviert nur dod-push + graphify) | `hooks/1-generic/*.sh:4-6`; `.meta-config/project.yaml:155-161` |
| Payload-Felder | `tool_name`, `tool_input.{command,file_path,subagent_type}`, `cwd`, `agent_id` | per `grep -o '"tool_name"…'` (Shell-Regex, kein JSON-Parser im Wrapper) bzw. Python-Heredoc | `orchestrator-guard.sh:68,76`; `orchestrator-guard-impl.sh:275-307,384`; `repo-containment-impl.sh:356,362` |
| Block-Protokoll | **ausschließlich `exit 2` + stderr**; kein `hookSpecificOutput.permissionDecision` (`allow/deny/ask`), kein `updatedInput`, kein `additionalContext`-JSON | 15× `exit 2` in orchestrator-guard-impl, 15× repo-containment-impl, 10× dod-push | grep-Zählung; `"allow"`-Treffer sind Kommentare/Log-Strings |
| `permissions.deny` (Isolation) | Glob-Deny anderer Provider-Verzeichnisse | `_sync_claude_isolation` | `isolation.py:369-414` |
| `permissions.additionalDirectories` | Settings-Key aus Registry | `settings-allow-dirs-key` | `ai-providers.yaml:81`; `settings_dirs.py` |
| `${CLAUDE_PROJECT_DIR}` | Anker vor jedem Hook-Command + Repo-Root-Ermittlung in 3 Hooks | `hook-command-anchor` (Registry) **und** hart im Skript | `ai-providers.yaml:34`; `orchestrator-guard-impl.sh:24,372-391`; `repo-containment-impl.sh:3,79,293-307,841`; `hook_common.sh:386` |
| Subagent-Identität | `agent_id` im PreToolUse-Payload ⇒ „ist Subagent"; leer ⇒ Main Chat; Strict-Mode blockt nur bei leerem `agent_id` | Capability `hook-agent-id` → Placeholder `AGENT_META_HOOK_AGENT_ID` gebacken | `ai-providers.yaml:59-64`; `hooks.py:561`; `orchestrator-guard-impl.sh:352-366,1504-1524` |
| Sentinel `#agent-meta:agent=<rolle>` | Self-Report in 1. Kommandozeile; auf Claude verworfen, wenn `agent_id` leer (Main-Thread-Fälschung) | Shell-Parsing | `orchestrator-guard-impl.sh:73-86,360-366` |
| `tool_input.subagent_type` | Orchestrator-Singleton/Anti-Rekursion (Task-Tool) | hart | `orchestrator-guard-impl.sh:280` |

### A.2 Versionsabhängigkeit / Fragilität

| Punkt | Risiko | Beleg / Status |
|---|---|---|
| `agent_id` im PreToolUse-Payload | Gesamte Strict-Mode-Logik und Sentinel-Verwurf hängen daran. Repo-Evidenz: nur Kommentar „code.claude.com hooks docs"; **kein** Eintrag in `docs/analysis/evidence/2026-09-30-runtime-claude-antigravity.md` (grep `agent_id` = 0). Feld ist jung (Subagent-Hooks) → **[UNVERIFIZIERT: Mindestversion Claude Code]**. Fällt es weg, blockt Strict-Mode jeden Subagenten (fail-closed → Delegation tot). | `ai-providers.yaml:59-64`; Evidence-Doc |
| `exit 2`-Semantik | Stabil seit Hooks-Einführung; aber „ask" (#1217) wäre JSON-only → Umbau aller Guards nötig (Hook-API-Doc: `ask` nur Claude, headless unverifiziert) | Commit `25df1b29` §2 |
| `${CLAUDE_PROJECT_DIR}` | Harness-Env-Var (seit #851 Anker). Hooks nutzen sie **direkt** (nicht nur über Registry-Anker) → Nicht-Claude-Provider mit Claude-Payload-Kontrakt (Antigravity-Adapter) laufen in Fallback-Pfade. | `orchestrator-guard-impl.sh:372-391` |
| Shell-Regex-JSON-Parsing im Wrapper | `grep -o '"tool_name"…'` bricht bei Whitespace-/Escape-Varianten; Payload-Formatänderung ⇒ Wrapper fällt in Syntax-Fehler-Pfad (`exit 2` außer Write/Edit unter hooks/) | `orchestrator-guard.sh:68-97` |
| Zod-strict settings.json | Companion-State-Datei nötig, da unbekannte Root-Keys die ganze Datei invalidieren | `isolation.py:27-33` |
| Matcher-Format | Regex-Strings `Read\|Glob`; Tool-Namen (`Agent` vs. `Task`) harness-abhängig; `native_agent_tools: ["Agent","Task"]` doppelt gepflegt | `provider-capabilities.yaml` Claude-Block |
| Tokenizer-False-Positives | Beobachtet in dieser Session: read-only `git log … \| head; for b in …; do git cat-file …; done; git branch -a --contains` wurde als Git-Mutation geblockt (Ursache nicht isoliert, **[UNVERIFIZIERT]** ob `for/do`-Keyword oder `git branch`) | Hook-Fehlermeldung ORCHESTRATOR_GUARD |

### A.3 Doku-Abgleich (nur Kopfzeile/Befund)
- `2026-11-11-hook-api-ask-permission.md` (Commit 25df1b29): Status „Analyse, kein Beschluss"; Claude `ask: ja (interaktiv)`, headless unverifiziert; 8 andere Provider `unbekannt`; Repo enthält keine Doku zu `permissionDecision` für Claude. Konsistent mit Code: nirgends `permissionDecision` in hooks/.
- Konsequenz: `ask`-Einführung (#1217) wäre Claude-only und würde ein zweites Block-Protokoll neben `exit 2` einführen → Adapter-Schicht (D) vorher.

---

## B. Opencode v2: Erzeugung, Emulation, Lücken

### B.1 Wie die v2-Oberfläche entsteht

| Ebene | Mechanismus | Beleg |
|---|---|---|
| Aktivierung | `provider-options.Opencode.surface-version: v2` (Registry-Default ist `v1`) | `.meta-config/project.yaml:170-172`; `ai-providers.yaml:260` |
| Agent-Frontmatter | `surface-mechanisms.v2: opencode-native-v2` → `_transform_frontmatter_for_opencode_v2`: `mode`, `model#variant`, `steps`, geschlossene `permissions[]` (`edit/shell/subagent`, unmapped = deny) | `ai-providers.yaml:366-371`; `provider_transform.py:459,525,608,1258-1340` |
| Rollen-Permissions (Ist) | git: edit deny/shell allow/subagent deny · developer: edit allow/shell allow · orchestrator: edit deny außer `.tmp/**`,`.meta-viz/**`, shell deny, subagent allow | `.opencode/agents/{git,developer,orchestrator}.md:7-25` |
| Primary-Edit-Deny | `_v2_permissions_with_edit_deny` (nur wenn Rolle `primary`) | `provider_transform.py:1228-1257` |
| Plugin | `.opencode/plugins/agent-meta-runtime-gate.js`, `ctx.tool.hook("execute.before")`, `MODE="observe"`, `STRICT=false`, nie blockend; Autoload ohne Config-Eintrag (`opencode.json.plugins` enthält nur `rtk-for-opencode`) | Plugin Z. 1-45; `runtime_gate.py:114-175`; `docs/providers/opencode.md:32,57` |
| Tier | `surface-has-plugins.v2: true` → Tier `plugin`; da `observe` ⇒ `permission_deny_required()` = True ⇒ Deny soll über `permissions[]` kommen | `ai-providers.yaml:300-326`; `isolation.py:1290-1313` |
| Root-Gate `permissions[]` | Tripel `{edit,shell} ** deny` **nur wenn** v2 ∧ strict ∧ Entry-Point (expliziter, generierter **Primary**) | `isolation.py:1280-1285,1474-1540,549-595` |
| **Ist-Zustand dieses Repos** | `topology: subagent` ⇒ `_opencode_entry_point` = None ⇒ **keine** Deny-Tripel, kein `default_agent`; `opencode.json` enthält nur `plugins/mcp/experimental`; State-Datei ohne `opencode-v2-permissions`/`runtime-gate-deny` | `.meta-config/project.yaml:322`; `opencode.json`; `.opencode/agent-meta-state.json` |
| MCP / Keys | `sync_opencode_v2_managed_keys`, `sync_opencode_mcp_managed` (Merge mit Prior-Tracking) | `opencode_v2_config.py:684,898` |

**Kernbefund B:** In der gelieferten Konfiguration (v2 + strict + subagent-Topologie) ist der Opencode-Runtime-Gate **faktisch `advisory`**: Plugin beobachtet nur, Root-Deny wird wegen Topologie nicht geschrieben, Hooks gibt es nicht. Die Tier-Berechnung meldet dennoch `plugin` (für Shared-Context-Fold). Das ist ein Design-Loch, kein Bug: `subagent`-Topologie + v2 ergibt keine Durchsetzungsebene.

### B.2 Wo v2 Claude-Hooks ersetzt/emuliert

| Claude-Guard | Opencode-v2-Äquivalent | Qualität |
|---|---|---|
| orchestrator-guard Strict-Mode (Main Chat kein Write/Edit/Bash) | Root-`permissions[]` deny (nur primary-Topologie) + Agent-Frontmatter `edit deny` je Rolle | Partiell: keine Delegations-Provenienz (`runtime_gate.py:17-20`); unter `subagent` nichts |
| Git-Mutations-Gate (nur `git`-Sentinel darf) | Rollen-Permission `shell` (developer: allow) | **Fehlt**: jeder Worker mit `shell: allow` kann `git commit/push` |
| DoD-Push-Check (Protected-Branch, Submodule) | — | **Fehlt** (Header `# provider: Claude`) |
| Destructive-Gate (`rm -rf`) | — | **Fehlt** |
| Repo-Containment (`.tmp`-Sink) | — | **Fehlt**; nur Prompt-Regel; `.opencode/agents/orchestrator.md` edit-allow `.tmp/**` ist Rollen-, kein Pfad-Gate für alle |
| Provider-Isolation | `permission.read/edit` Globs (v1-Map!) via `_sync_opencode_isolation` | Für v2: Map-Form neben `permissions[]`-Liste – Koexistenz **[UNVERIFIZIERT]**, Code deutet Konflikt an (`isolation.py:881`) |
| Orchestrator-Singleton/Anti-Rekursion | `subagent` deny in Worker-Frontmatter | Partiell: Orchestrator-Rekursion über `subagent: allow` des Orchestrators nicht verhindert |
| graphify-Guards | — | Fehlt |

### B.3 Paritätsmatrix

| Guard | Claude (`hook`) | Gemini (`antigravity-hooks-json`) | Opencode v2 (`plugin`/observe) | Opencode v1 / hook-lose (Continue, Copilot, ZCode, KimiCode, Mammouth, Codex) |
|---|---|---|---|---|
| Main-Chat-Write-Block | ✔ fail-closed | ✔ via Adapter (deny-JSON) | ◐ nur primary-Topologie, ohne Provenienz | ✖ Prompt |
| Git-Mutation nur `git` | ✔ | ✔ | ✖ | ✖ |
| DoD-Push-Check | ✔ | ✖ (`provider: Claude`) | ✖ | ✖ |
| Destructive-Gate | ✔ | ✔ | ✖ | ✖ |
| Repo-Containment | ✔ | ✔ | ✖ | ✖ |
| Isolation | `permissions.deny` | TOML-Policy | `permission.*` Map | Continue: Soft-Rule; Rest: — |
| Subagent-Identität | `agent_id` | ✖ Sentinel only | Plugin-Event `agent` (nur beobachtet) | ✖ |
| `ask`-Fähigkeit | belegt | unbekannt | unbekannt | unbekannt |

---

## C. Provider-Agnostik-Bruchstellen

Legende: Art = ND (Name-Dispatch) · CF (Capability-Flag, ok) · HL (Hardcode-Liste) · TE (Test-Enumeration) · TS (Text-Strip) · FL (Datei-/Pfad-Literal als Provider-Proxy) · DF (Claude-Default). Schwere H/M/L; Aufwand S/M/L.

| # | Datei:Zeile | Art | Schwere | Befund | Vorschlag | Aufw. |
|---|---|---|---|---|---|---|
| C1 | `provider_transform.py:459,525,608` | ND | M | `mechanism in ('opencode-native','opencode-native-v2')` — Mechanismus-String trägt Providernamen; Builder-Funktionen providerbenannt (`:987,1258`) | Registry `FRONTMATTER_BUILDERS = {"native-map-v1": …, "native-list-v2": …}`; Strings umbenennen | S |
| C2 | `provider_transform.py:638,779,1352` + `ai-providers.yaml:241,513,592,711,801,873,956` | TS | M | `strip-claude-lines` entfernt Claude-Prosa aus generischen Templates ⇒ Templates sind nicht agnostisch, der Strip kaschiert es (7 Provider setzen es) | Templates agnostisch schreiben (Provider-Beispiele in `> **Example (provider-specific):**`-Blöcke, die `provider_literals.py` schon kennt); Key zu `strip-provider-examples` generalisieren | M |
| C3 | `provider_transform.py:885` | ND | L | `_map_claude_tools_to_opencode_permissions`: Claude-Toolnamen = kanonisches Vokabular | Kanonisches Tool-Vokabular explizit benennen (`tool-name-map` existiert bereits `ai-providers.yaml:375`) | S |
| C4 | `hooks.py:683` | DF | M | Unbekanntes `hook_protocol` → Fallback auf Claude-Writer `_update_settings_hooks` | Fallback = kein Writer + Log | S |
| C5 | `hooks.py:465`, `hook_plugins.py:34,266`, +9 weitere (11 Signaturen) | DF | L | `provider="Claude"` Default | Parameter pflicht machen | S |
| C6 | `hooks/1-generic/{dod-push-check,lifecycle-check,sync-on-config-change}.sh:6`, `hooks/0-external/graphify-*.sh:9` | ND | **H** | `# provider: Claude` ⇒ DoD-Push-Check läuft auf Gemini nicht, obwohl Payload-Kontrakt per Adapter identisch | Header auf `# hook_protocol: claude-code-json` oder Capability (`# requires: bash-tool`) umstellen | S |
| C7 | `orchestrator-guard-impl.sh:24,372-391`, `repo-containment-impl.sh:3,79,293-307,841`, `hook_common.sh:386` | ND | M | `CLAUDE_PROJECT_DIR` hart im Hook statt aus `cwd`/Anker-Variable | Kernel liest `AGENT_META_PROJECT_DIR` (vom Adapter gesetzt) | S |
| C8 | `isolation.py:7-11,372,424,2148,2185` | ND | **H** | Pro Provider eigene `_sync_<provider>_isolation`; `isolation-mechanism`-Keys (`claude-settings-deny`, `opencode-permissions`, `gemini-toml-policy`, `continue-soft-rule`) heißen nach Providern | Dispatch-Dict `ISOLATION_WRITERS[mechanism]` mit generischen Namen (`settings-deny-globs`, `permission-map-globs`, `toml-policy`, `soft-rule`) | M |
| C9 | `isolation.py:69,2106`, `opencode_v2_config.py:357-376` | FL | M | Ownership über Dateiname `opencode.json`/Format `opencode-json-v2` statt Capability | Capability `owns-runtime-gate-surface: true` | S |
| C10 | `sync_pipeline.py:1682,1691` (18 `opencode`-Bezeichner) | ND | M | Pipeline ruft `reconcile_opencode_surface_gate`, `sync_opencode_v2_managed_keys` unbedingt; Modul `opencode_v2_config.py` (1379 Z.) ist providerbenannt | Umbenennen `managed_json_surface.py`; Pipeline-Schritt capability-gated (`managed-json-surface`) | M |
| C11 | `mcp_provider_config.py:90,247,923,963-984` | ND | M | `if fmt == "opencode-json"` … 8 Format-Tags nach Providern benannt; Fork Mammouth nutzt `opencode-json` (Format ≠ Provider, also eigentlich richtig – nur Benennung) | Tags generisch (`json-mcp-servers`, `yaml-mcp`, `toml-mcp`), Writer-Dict | S |
| C12 | `pipelines.py:55-58` | HL | L | `KNOWN_PROVIDERS` als Fallback (Drift-Test vorhanden) | behalten oder aus Registry laden; nicht kritisch | S |
| C13 | `external_tools_drift.py:187-189` | HL | L | `{"Claude": ".claude/hooks"}` Fallback-Dirs | aus `hooks_dir`/`rules_dir`/`commands_dir` der Registry | S |
| C14 | `ai-providers.yaml#capabilities` vs. `provider-capabilities.yaml` | CF | M | Zwei Vokabulare: Liste (`hooks`, `hook-agent-id`) vs. Keys (`hooks: true`, `runtime_gate: hook`) | Eine Datei, ein Schema; `hook-agent-id` → `hook_payload_fields: [agent_id]` | M |
| C15 | `tests/*.py` (34 Dateien, 12 eigene `_PROVIDERS`-Definitionen) | TE | M | Jede Datei lädt/listet Provider selbst | `conftest.py`-Fixture `all_providers` (aus Registry) | M |
| C16 | `runtime_gate.py:117-130`, `isolation.py:1474-1540` | CF | – | **Positiv:** reine Capability-Checks (`has_plugins`, `plugin_dir`, Tier-Resolver) | Vorbild für C8/C10 | – |

### C.17 Neuer Provider — Berührungsstellen (konkret)
1. `config/ai-providers.yaml` — Eintrag (~45 Keys, davon `agent-transform` ~15, `mcp-config`, Isolation, Hooks).
2. `config/provider-capabilities.yaml` — ~42 Keys.
3. `scripts/lib/provider_transform.py` — nur bei neuem Frontmatter-Format (neuer Mechanismus-String + Builder).
4. `scripts/lib/mcp_provider_config.py` — neues Format-Tag + `elif`.
5. `scripts/lib/isolation.py` — neue `_sync_<provider>_isolation` + Dispatch.
6. `scripts/lib/hooks.py` — neuer `hook_protocol`-Writer **und** ein Adapter-Skript analog `antigravity-json-adapter.sh`, falls Hooks.
7. `hooks/1-generic/*` — `# provider:`-Header prüfen (C6), `CLAUDE_PROJECT_DIR`-Fallbacks (C7).
8. `pipelines.py:55`, `external_tools_drift.py:187` — Fallback-Listen.
9. `tests/` — 34 Dateien + AC-01-Baseline + Context-Ceilings (`test_context_budgets.py:336`).
10. `docs/providers/<name>.md`, Evidence-Doc, `templates/configs/<NAME>.settings-template.*`.
- Minimal-Provider (Agents + Context, keine Hooks/MCP/Isolation): Stellen 1, 2, 9, 10 → **M**. Voll: alle 10 → **L**.

---

## D. Hook-Architektur: Zielbild

### D.1 Ist
- Kernel-Logik (Tokenizer, Git-Klassifikation, Pfad-Containment) liegt als Python-Heredocs in Bash (`hook_common.sh:475-920,965-1100,1141-1177`; `dod-push-check.sh` 5×; `repo-containment-impl.sh` 3×).
- Provider-Adapter existiert **einmal** bereits: `antigravity-json-adapter.sh` (Payload-Übersetzung + Exit-Code→Decision-JSON). Claude ist der implizite „Null-Adapter" (Hooks sprechen nativ Claude-Payload).
- Provider-Spezifika im Kernel: `CLAUDE_PROJECT_DIR` (C7), `# provider: Claude` (C6), Shell-Regex-JSON (A.2), `exit 2`-only.
- Opencode v2 hat keinen Adapter, sondern eine andere Durchsetzungsebene (Permissions + observe-Plugin), die den Kernel nicht wiederverwendet.

### D.2 Minimale Zielarchitektur
```
hooks/kernel/*.py           # reines Python, stdlib: tokenizer.py, git_gate.py, containment.py,
                            #   push_check.py, identity.py; API: decide(event: NormEvent) -> Decision
hooks/adapters/claude.sh    # stdin JSON -> NormEvent (tool, args, cwd, agent_id, project_dir) ; Decision -> exit 2 / (optional) permissionDecision-JSON
hooks/adapters/antigravity.sh  # heutiger Adapter, nur noch Payload->NormEvent + Decision->{"decision":"deny"}
hooks/adapters/opencode-plugin.js  # v2: execute.before -> NormEvent -> `python3 -m kernel` -> throw/deny via ctx.permission.hook (P6)
```
- `NormEvent`: `{tool_kind: write|shell|dispatch|read, path, command, cwd, project_dir, agent_id|None, declared_agent|None, event}`.
- `Decision`: `{allow|deny|ask, reason, audit}` — Adapter mappt auf das Provider-Protokoll (Claude: exit 2 jetzt, `ask`-JSON später ohne Kernel-Änderung).
- Registry: `hook_protocol → adapter`, Hook-Header `# requires: <capability>` statt `# provider:`.

### D.3 Migrationspfad
1. **Extract (S/M):** Heredocs → `hooks/1-generic/lib/kernel/*.py`; Shell ruft `python3 -m kernel.<gate>`; Tests laufen direkt gegen Python (18 subprocess-Tests schrumpfen). Byte-Verhalten identisch (golden Exit-Codes).
2. **Normalize (S):** `hook_common.sh` liefert `NormEvent`-JSON; `CLAUDE_PROJECT_DIR`-Lesen nur noch im Claude-Adapter; `# provider: Claude` → `# hook_protocol:`/`# requires:` (C6, C7). Gemini erhält damit DoD-Push-Check gratis.
3. **Adapterize Claude (S):** `orchestrator-guard.sh`/`repo-containment.sh`/`dod-push-check.sh` werden dünne Claude-Adapter-Aufrufe; ein gemeinsamer Decision→exit-Mapper; `ask` als Decision-Variante vorbereitet (nur Claude-Mapper kennt JSON).
4. **Opencode-v2-Adapter (M, P6-gated):** Plugin ruft Kernel im `execute.before`; `MODE=enforce` über `ctx.permission.hook("evaluate")`; Kernel-Gates Git-Mutation/Containment/Push-Check gelten dann auch dort; Root-`permissions[]` bleibt als Fallback für `permission`-Tier.
5. **Konsolidieren (M):** Isolation-Writer (C8) und MCP-Format-Writer (C11) in Dispatch-Dicts; Capability-Dateien vereinen (C14); Test-Fixture (C15).

### D.4 Risiken
- Schritt 1 ändert Startlatenz (Python-Modulimport statt Heredoc-`exec`); bisher ohnehin `python3`-Start pro Call — gering.
- Fail-closed-Pfade (`python3` fehlt, Syntaxfehler) müssen im Adapter bleiben (`orchestrator-guard.sh:60-97`); Golden-Tests für Exit-Codes zwingend.
- Schritt 4 hängt an P6-Verifikation und an Opencode-Plugin-API-Stabilität (`ctx.permission.hook` nur per Spike belegt).
- `agent_id`-Abhängigkeit bleibt; Kernel braucht explizite `identity_source: harness|sentinel|none` statt impliziter Leere.
- Hash-/Drift-Mechanik (`.agent-meta-managed`, `context-hashes`) muss neue Dateien kennen (Sync-Backups zeigen hohe Churn bereits heute: `.claude/hooks/*.sync-backup-*`).

---

## E. Top-10 (Nutzen/Aufwand) und Lücken

| Prio | Maßnahme | Nutzen | Aufwand | Ref |
|---|---|---|---|---|
| 1 | `# provider: Claude` in Hooks → Protokoll/Capability-Header | DoD-Push-Check auf Gemini; ehrliches Credo | S | C6 |
| 2 | Python-Kernel aus Heredocs extrahieren (Golden-Exit-Tests) | Testbarkeit, Lint, Voraussetzung für Adapter | M | D.3-1 |
| 3 | Opencode v2 + `subagent`-Topologie: Warnung/Fail-Fast „Gate advisory" im Sync-Log + Tier-Fold auf `advisory` | Nutzer glaubt heute an `plugin`-Tier ohne Durchsetzung | S | B.1 |
| 4 | `CLAUDE_PROJECT_DIR` nur im Adapter; Kernel liest `project_dir` aus NormEvent | Portabilität, Gemini-Pfad korrekt | S | C7 |
| 5 | `hooks.py:683` Fallback auf Claude-Writer entfernen | Kein stilles Fehl-Deployment für neue Provider | S | C4 |
| 6 | Isolation-Writer + MCP-Format-Writer als Dispatch-Dicts mit generischen Mechanismus-Namen | Größter Hardcode-Block (`isolation.py` 2237 Z.) | M | C8, C11 |
| 7 | Capability-Vokabulare zusammenführen (`hook-agent-id` → Payload-Feldliste) | Eine Quelle, Schema-prüfbar | M | C14 |
| 8 | `agent_id`-Evidence-Doc mit Claude-Code-Version + Fallback-Verhalten dokumentieren | Fragilitäts-Hotspot A.2 | S | A.2 |
| 9 | Opencode-v2-Enforce über Kernel (P6) statt zweiter Logik | Parität Git-Gate/Containment/Push-Check | M/L | D.3-4 |
| 10 | Test-Fixture `all_providers` in `conftest.py` | 34 Dateien → 1 Quelle | M | C15 |

### Nicht geprüft / Annahmen
- Keine Tests/Syncs ausgeführt; Verhalten von `_sync_opencode_isolation` (v1-Map) neben v2 `permissions[]` im selben `opencode.json` nicht am Runtime geprüft.
- Mindest-Claude-Code-Version für `agent_id` im PreToolUse-Payload nicht gegen externe Doku verifiziert.
- Opencode-Autoload von `.opencode/plugins/*.js` nur per `docs/providers/opencode.md:32,57` (Repo-Doku), nicht am Runtime.
- `docs/analysis/2026-11-14-fable-concept-audit.md` §0/1/4-6 nicht erneut gelesen.
- Antigravity-Adapter-Laufzeit (P6) laut eigenem Header unverifiziert; hier übernommen.
- Ursache des beobachteten Guard-False-Positives (read-only `git log/cat-file/branch --contains` in `for`-Schleife) nicht isoliert.
- Hash-/Drift-Auswirkung der vorgeschlagenen Dateiverschiebungen (D.3) nicht gegen `hook_drift.py` geprüft.
