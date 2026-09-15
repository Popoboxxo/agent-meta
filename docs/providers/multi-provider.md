# Multi-Provider Support — Claude, Gemini, Opencode, Continue, Copilot, Mammouth, Codex, ZCode, Kimi Code

> Dieses Dokument beschreibt wie `sync.py` mehrere AI-Provider gleichzeitig bedienen kann
> und was jeder Provider an Output erhält.

---

## Konzept

`sync.py` generiert Provider-spezifischen Output aus denselben universellen Agent-Templates.
Ein einziges `.meta-config/project.yaml` reicht, um Agenten-Dateien für Claude Code, Gemini CLI,
Opencode, Continue, GitHub Copilot, Mammouth Code, Codex, ZCode und Kimi Code gleichzeitig zu erzeugen.

```json
"ai-providers": ["Claude", "Gemini", "Opencode", "Continue", "Copilot", "Mammouth", "Codex", "ZCode", "KimiCode"]
```

Backward-compatible: `"ai-provider": "Claude"` (String) funktioniert weiterhin unverändert.

**Nur Opencode:**

```json
{
  "ai-providers": ["Opencode"]
}
```

---

## Unterstützte Provider

| Provider | Agents-Verzeichnis | Dateiendung | Kontext-Datei | Frontmatter |
|----------|--------------------|-------------|---------------|-------------|
| `Claude` | `.claude/agents/` | `.md` | `CLAUDE.md` | Vollständig (`model`, `memory`, `permissionMode`, …) |
| `Gemini` | `.gemini/agents/` | `.md` | `AGENTS.md` | Reduziert (`model` only, kein `memory`/`permissionMode`) |
| `Continue` | `.continue/agents/` | `.md` | `.continue/rules/project-context.md` | Minimal (`name`, `description`, `alwaysApply: false`) |
| `Opencode` | `.opencode/agents/` | `.md` | `AGENTS.md` | Nativ (`description`, `mode: subagent`, `model: provider/id`) |
| `Copilot` | `.github/copilot/agents/` | `.md` | `.github/copilot/COPILOT.md` | Reduziert (`name`, `description`) |
| `Mammouth` | `.mammouth/agents/` | `.md` | `MAMMOUTH.md` | Reduziert (`model` only) |
| `Codex` | `.codex/agents/` | `.toml` | `AGENTS.md` | TOML-Dokument (`name`, `description`, `model`, `sandbox_mode`, `developer_instructions`; Provenance als TOML-Kommentare) |
| `ZCode` | `.zcode/agents/` | `.md` | `AGENTS.md` | Reduziert (`model`, kein `memory`/`permissionMode`/…) |
| `KimiCode` | `.kimi-code/agents/` | `.md` | `AGENTS.md` | Reduziert (`model`, kein `memory`/`temperature`/…) |

> **AGENTS.md ist geteilt:** `Gemini`, `Opencode`, `Mammouth` (als Vorlage), `Codex`,
> `ZCode` und `KimiCode` verwenden alle das gemeinsame Template
> `templates/configs/AGENTS.project-template.md`. Diese Provider schreiben ihren managed block
> in dieselbe `AGENTS.md` im Projekt-Root — die Datei
> ist bewusst provider-neutral (siehe Routing in `CLAUDE.md`: „Opencode, Gemini -> AGENTS.md").

### Claude Code

Vollständiger Output — keine Einschränkungen:
- `.claude/agents/*.md` — alle generierten Agenten
- `CLAUDE.md` — managed block wird bei jedem sync aktualisiert
- `.claude/rules/*.md` — Rules (auto-geladen in jeden Agenten-Kontext)
- `.claude/hooks/*.sh` — Hooks (registriert in `.claude/settings.json`)
- `.claude/settings.json` — Skeleton + Hooks-Section

### Gemini CLI

- `.gemini/agents/*.md` — generierte Agenten (gleicher Markdown-Body wie Claude)
- `AGENTS.md` — Kontext-Datei (managed block, bei jedem sync aktualisiert); geteilt mit Opencode
- `.gemini/settings.json` — Skeleton (einmalig angelegt); MCP wird bei jedem sync eingetragen
- `.gemini/commands/*.toml` — Slash-Commands (aus `commands/` transformiert, `.md` → `.toml`)
- `.agents/hooks/*.sh` — gespiegelte Hook-Skripte (committed; Registrierung via `.agents/hooks.json`, siehe Hooks-Hinweis)
- `.gemini/rules/*.md` — Rules (Gemini CLI besitzt ein natives Rules-Verzeichnis, `has_rules: true`)

> **Hooks (issue #674 Phase 3.1):** agent-meta spiegelt Hooks für Gemini über
> `hook_protocol: antigravity-hooks-json` — den **verifizierten Antigravity-Vertrag**
> (antigravity.google/docs/hooks): Registrierung in `.agents/hooks.json` (dokumentierter
> AGY-Workspace-Ort, NICHT `.gemini/`), Skripte in `.agents/hooks/`, Events
> PreToolUse/PostToolUse/PreInvocation/PostInvocation/Stop, camelCase-Payload
> (`hookEventName`, `toolCall.{name,args}`) und `{"decision": "deny", "reason"}`-JSON
> statt Exit-Code-2. Jeder registrierte Hook läuft dadurch durch den Übersetzungs-Adapter
> `hooks/1-generic/antigravity-json-adapter.sh` (AGY-Payload → Claude-Vertrag, Tool-Namen
> normalisiert, deny-JSON). Runtime-Ausführung = P6 real-repo-test.
>
> **Cross-Provider-Interplay:** Ist zusätzlich Codex aktiv und
> `gitignore.ignore-provider-dirs: true` in `project.yaml` gesetzt, ignoriert
> Codex' Provider-Root `.agents/` das gesamte Verzeichnis — Projekte, die
> beides kombinieren, müssen `gitignore.exceptions: ['.agents/']` setzen
> (Exceptions invertieren die Root-Emission in `scripts/lib/gitignore.py`).

> **AGENTS.md vs. natives GEMINI.md — nicht verwechseln:**
> agent-meta schreibt Geminis Projekt-Kontext in `AGENTS.md` (`context_file: AGENTS.md` in
> `config/ai-providers.yaml`), NICHT in eine `GEMINI.md`. Gemini CLI unterstützt *zusätzlich*
> nativ ein eigenes, hierarchisches `GEMINI.md`-Konzept (global `~/.gemini/GEMINI.md` →
> Workspace → JIT beim Datei-Zugriff), mit `@./pfad/datei.md`-Imports (siehe
> `docs/providers/gemini-cli.md`). Dieses GEMINI.md wird von agent-meta **nicht** generiert
> oder verwaltet. Wer den agent-meta-Kontext über Geminis native Ladehierarchie einbinden
> möchte, referenziert die verwaltete Datei per `@./AGENTS.md` in einer eigenen GEMINI.md.

**Frontmatter-Unterschiede zu Claude:**
- `permissionMode` wird entfernt (nicht unterstützt)
- `memory` wird entfernt (nicht unterstützt)
- `model` bleibt erhalten

### Continue

Continue unterscheidet klar zwischen **Agents** und **Rules**:

- `.continue/agents/<rolle>.md` — Custom Agents mit minimalem Frontmatter (`name`, `description`, `alwaysApply: false`)
- `.continue/rules/project-context.md` — Projekt-Kontext als Rule (`alwaysApply: true`), immer geladen
- `.continue/config.yaml` — Skeleton (nur einmalig angelegt, nicht überschrieben)

**Agents** (`alwaysApply: false`) werden explizit per Name aufgerufen.
**Rules** (`alwaysApply: true`) werden automatisch in jeden Kontext geladen.

Das Continue-Frontmatter-Schema für Agents/Rules:
```yaml
---
name: developer           # Anzeigename
description: "..."        # Beschreibung (für Agent-Auswahl durch das Modell)
alwaysApply: false        # false = explizit aufrufen; true = immer geladen
# globs: ["**/*.ts"]     # optional: nur bei passenden Dateien aktivieren
---
```

### GitHub Copilot

Schlanker Provider — dateibasierte Agenten und Rules, keine Hooks/Commands/Settings.

- `.github/copilot/agents/*.md` — generierte Agenten (werden automatisch geladen)
- `.github/copilot/COPILOT.md` — Kontext-Datei (managed block, bei jedem sync aktualisiert)
- `.github/copilot/rules/*.md` — Rules (`has_rules: true`)
- `.vscode/mcp.json` — Agent-Mode-MCP (issue #674 Phase 3.3): VS Code-eigenes
  Settings-Shape (Top-Level `{"servers": {...}}`, Format-Writer `vscode-settings`).
  Committed mit `${env:VAR}`-Platzhaltern (VS Code expandiert sie nativ) — **kein
  Secrets-File** (Codex-Präzedenz). `.vscode/` ist bewusst KEIN Provider-Root
  (geteiltes Editor-Verzeichnis).

**Fähigkeiten (`config/provider-capabilities.yaml`):**
- Keine native Subagent-Dispatch-API und keine parallele Ausführung — Delegation erfolgt
  text-basiert per `@agent`-Mention, sequentiell.
- Handoff als YAML-Text-Block (kein JSON-Envelope).

**Frontmatter:** reduziert auf `name`, `description`.

### Mammouth Code

CLI-first Tool mit Plan- (read-only) und Build-Modus (Ausführung). Als Provider konservativ
konfiguriert — nur belegte Fähigkeiten sind aktiviert.

- `.mammouth/agents/*.md` — generierte Agenten (dateibasiert, kein Session-Bootstrap nötig)
- `MAMMOUTH.md` — Kontext-Datei (managed block, bei jedem sync aktualisiert; nutzt das
  gemeinsame `AGENTS.project-template.md`)
- `.mammouth/rules/*.md` — Rules (`has_rules: true`)
- `.mammouth/hooks/` — reserviert (`has_hooks: true`): ohne verifizierten
  `hook_protocol` spiegelt sync.py keine Hook-Skripte (#630-Muster) — Cleanup statt
  Deploy; das separate `.mammouth/settings.json` wird als Skeleton angelegt

**Commands:** Mammouth setzt `has_commands: true` und listet die Capability
`commands` — konfiguriert aber weder `commands_dir` noch `commands_ext` (anders als
Gemini/Opencode). Der Sync-Code (`scripts/lib/commands.py::sync_commands_for_provider`)
implementiert Zweige für Claude, Continue, Gemini und Opencode; jeder andere Provider
endet im `else: return`. Für Mammouth wird daher **kein `.mammouth/commands/`**
generiert — der Sync läuft still durch (kein Fehler, keine Warnung). Der Flag ist
damit aktuell ein Capability-Versprechen ohne Output (siehe auch den Kommentar zu
`_INFRA_ROOT_FALLBACK_DIRS` in `scripts/lib/external_tools_drift.py`).

**Fähigkeiten (`config/provider-capabilities.yaml`):**
- `hooks: true` — belegt durch `has_hooks: true` + `hooks_dir` in `config/ai-providers.yaml`.
- Keine native Subagent-Dispatch-API und keine parallele Ausführung (konservativ auf `false`,
  da Mammouths native Orchestrierungs-Oberfläche nicht dokumentiert ist) — Delegation
  text-basiert per `@agent`-Mention, sequentiell, YAML-Text-Block-Handoff.
- MCP-Integration ist in `config/ai-providers.yaml` (noch) nicht konfiguriert (`mcp-config: {}`).

**Frontmatter:** reduziert (`model`).

> Hintergrund zur konservativen Konfiguration: Ohne Einträge in
> `provider-capabilities.yaml`, `provider-bootstrap.yaml` und `delegation-syntax.yaml` würde
> Mammouth beim Sync still degradiert — sämtliche `PAL_*`-Delegations-Syntax würde entfernt und
> `bootstrap_required`/`subagent_dispatch` defaulteten stumm auf `false`. Die Einträge machen
> dieses Verhalten explizit statt implizit.

### Codex (OpenAI Codex CLI)

TOML-nativer Provider — Agenten als TOML-Dokumente mit nativem Dispatch (Details:
`docs/providers/codex.md`).

- `.codex/agents/*.toml` — generierte Agenten (`codex-toml`-Transform:
  `name`/`description`/`model`/`sandbox_mode`/`developer_instructions`, auto-geladen)
- `AGENTS.md` — Kontext-Datei (managed block, bei jedem sync aktualisiert; geteilt
  mit Gemini/Opencode/ZCode/KimiCode)
- `rules/` — Rules im Projekt-Root (`has_rules: true`; `.rules`-Naming = offener P6-Check)
- `.agents/skills/` — Skills-Kanal (Codex liest user → repo → directory)
- Dispatch via native `spawn_agent`/`wait_agent`-Toolcalls, JSON-Handoff;
  `.codex/hooks/` ist nur reserviert — **keine Hook-Spiegelung** (Payload-Deviations +
  Hash-Trust-Review, #630-Muster); MCP in `.codex/config.toml`
  (Format-Writer `codex-toml-mcp` landet mit dem P3-Commit, vorher warn+skip)

### ZCode (zcode.z.ai)

Offizieller Z.ai GLM-5.3-Harness (ADE) — Agent-Definitionen als Dateien, konsumiert
via Bootstrap-Injection (Gemini-Postur; Details: `docs/providers/zcode.md`).

- `.zcode/agents/*.md` — generierter Definition-Store (`model` pro Rolle injiziert:
  `glm-5.3`/`glm-5.3-flash`); Workspace-Auto-Load = offener P6-Real-Repo-Test
- `AGENTS.md` — managed block **plus Session-Start-Bootstrap-Block** (Roster-Registrierung
  im Prompt — einziger weiterer Provider mit Bootstrap-Block neben Gemini)
- `.zcode/config.json` — Workspace-Settings; MCP unter dem verschachtelten Key
  `mcp.servers` (Format-Writer `zcode-json` landet mit dem P3-Commit, vorher warn+skip)
- Dispatch via `Agent`-Toolcall (Legacy-Alias `Task`), Backgrounding statt verifizierter
  Parallelität, YAML-Text-Block-Handoff; **keine Hooks** — Projekt-Hooks werden vom
  Harness ignoriert (`config_project_hooks_ignored`)

### Kimi Code (Moonshot AI)

Markdown-first Provider mit Auto-Discovery — kein Session-Bootstrap nötig
(Details: `docs/providers/kimi-code.md`).

- `.kimi-code/agents/*.md` — generierte Agenten (Default-Transform-Pfad: `model: inject`
  + Strip-Set; Auto-Discovery `explicit > project > extra dirs > user > plugin > built-in`)
- `AGENTS.md` — Kontext-Datei (managed block, nearest-wins-Subdirs wie Codex)
- `.kimi-code/mcp.json` — MCP (`mcpServers`-JSON, wire-identisch zum `claude-settings`-Branch
  wiederverwendet; Secrets via `bearerTokenEnvVar`/`env`-Indirektion)
- `.kimi-code/skills/` — Skills (`<name>/SKILL.md` oder flat `.md`)
- Dispatch via `Agent` + `AgentSwarm`-Fan-out (bis 128 Items), YAML-Text-Block-Handoff;
  Hooks (20 Events) nur user-level `~/.kimi-code/config.toml` `[[hooks]]` — keine
  Projekt-Hook-Generierung; Pfade systematisch `.kimi-code/`, **nie `.agents/`**

---

## Konfiguration

### Multi-Provider aktivieren

```json
{
  "ai-providers": ["Claude", "Gemini", "Continue"]
}
```

Nur bekannte Provider werden verarbeitet. Unbekannte Werte werden stillschweigend ignoriert.

### Legacy (weiterhin unterstützt)

```json
{
  "ai-provider": "Claude"
}
```

### Nur Gemini (ohne Claude)

```json
{
  "ai-providers": ["Gemini"]
}
```

**Hinweis:** Rules werden für alle Provider mit `has_rules: true` generiert (Claude →
`.claude/rules/`, Gemini → `.gemini/rules/`, Continue → `.continue/rules/`, Copilot →
`.github/copilot/rules/`, Mammouth → `.mammouth/rules/`, Codex → `rules/`; Opencode bettet
Rules in `AGENTS.md` ein). Hooks werden für Provider mit `has_hooks: true` UND verifiziertem
`hook_protocol` gespiegelt (Claude → settings.json-Registrierung; Gemini →
`antigravity-hooks-json`, Registrierung in `.agents/hooks.json` via Übersetzungs-Adapter) —
Codex reserviert lediglich `.codex/hooks/`, spiegelt aber keine Hooks (kein `hook_protocol`,
#630-Muster).

---

## Kontext-Dateien

### `CLAUDE.md` (Claude)

- Einmalig angelegt via `templates/configs/CLAUDE.project-template.md` (bei `--init`)
- Managed block (`<!-- agent-meta:managed-begin/end -->`) wird bei **jedem sync** aktualisiert
- Rest der Datei: manuell gepflegt, wird nie überschrieben

### `AGENTS.md` (Gemini, Opencode, Codex, ZCode, KimiCode; Vorlage für Mammouth)

- Einmalig angelegt via `templates/configs/AGENTS.project-template.md`
- Managed block wird bei **jedem sync** aktualisiert
- Von Gemini, Opencode, Codex, ZCode und KimiCode gemeinsam genutzt (provider-neutrale Kontext-Datei);
  Mammouth nutzt dasselbe Template für seine `MAMMOUTH.md`
- Kein `--init` nötig — wird beim ersten normalen sync angelegt
- **Nicht** identisch mit Geminis nativem `GEMINI.md` (siehe Gemini-CLI-Hinweis oben)

### `.continue/rules/project-context.md` (Continue)

- Einmalig angelegt via `templates/configs/CONTINUE.project-template.md`
- Managed block wird bei **jedem sync** aktualisiert
- Kein `--init` nötig — wird beim ersten normalen sync angelegt

### `.continue/config.yaml` (Continue)

- Einmalig als Skeleton angelegt (nur Kommentare)
- **Wird nie überschrieben** — eigene Continue-Konfiguration bleibt erhalten
- Enthält Hinweis auf `.continue/rules/`

### External-Tool-Rule-Content

Rule-Content aus `config/plugin-catalog.yaml` (`kind: cli-tool`-Einträge, z.B. für lokal installierte CLI-Tools wie `graphify`) wird nach dem gleichen Muster wie MCP-Server-Rules eingebettet: für Provider mit `has_rules: true` wird eine eigene Datei `.claude/rules/tool-<name>.md` geschrieben; für Opencode wird der Content direkt in den managed block von `AGENTS.md` eingebettet. Das Layout und die Versioning folgen exakt dem bestehenden MCP-Rule-Embed-Mechanismus (`scripts/lib/context.py`).

---

## Kontext-Topologie: `context_file.topology` (`unified` / `per-provider`)

> Trace-Anker: `SPEC-CONTEXT-FILE-MODES-2026-09-13` (Status APPROVED, 2026-09-14).
> System-Design: `docs/specs/2026-09-13-context-file-modes-system-design.md`.

### Zwei unabhängige Achsen

Der `context_file`-Block trägt **zwei** Schalter, die nicht verwechselt werden dürfen:

| Key | Achse | Werte | Default |
|---|---|---|---|
| `context_file.mode` | **Dichte** (Größe/Kompression, Issue #540) | `full` \| `compact` | `full` |
| `context_file.topology` | **Topologie** (eine gemeinsame Datei vs. Kern + Adapter) | `unified` \| `per-provider` | `unified` |

`mode` beeinflusst, **wie** der managed block gerendert wird; `topology` beeinflusst,
**wo** er landet (eine gemeinsame Datei oder kanonischer Kern + provider-native Kanäle).
Beide Werte sind unabhängig kombinierbar.

### Default: `unified`, **nicht persistiert**

- Fehlt `context_file.topology` — oder ist der Wert nicht-String, außerhalb des Enums
  oder der `context_file`-Block kein Mapping — löst der Resolver fail-safe auf `unified` auf.
- Der Default wird **nicht** in `project.yaml` geschrieben (`fill_defaults` persistiert ihn
  nicht; Schema-`default` + Resolver-Fail-safe). Bestehende Projekte bleiben daher **ohne
  Opt-in unverändert** — `unified` ist byte-identisch zum Bestand (ausgenommen die bereits
  vorher dokumentierte Weakest-Tier-Absenkung der geteilten `AGENTS.md`).
- `per-provider` greift ausschließlich nach explizitem Opt-in.

Resolver: `scripts/lib/providers.py::context_topology(config, provider=None)` — nie werfend,
vollständig key-/config-getrieben.

### Präzedenz (deterministisch)

```
context_file.provider-overrides.<Provider>.topology   (höchste)
        > context_file.topology
        > "unified"                                    (Default)
```

Ein Provider-Override gewinnt nur, wenn er selbst ein gültiges Enum trägt; sonst fällt die
Auflösung auf den Projektwert und danach auf `unified` zurück.

### Opt-in

```yaml
# .meta-config/project.yaml
context_file:
  topology: per-provider      # explizit — ohne diesen Key bleibt es unified
  core_file: AGENTS.md        # kanonischer Kern (Default)
  provider-overrides:
    Gemini:
      topology: unified       # Einzelfall: Gemini beim Bestand belassen
```

### Was `per-provider` rendert

- **Kanonischer Kern** in `context_file.core_file` (Default `AGENTS.md`): ein kanonisches
  Render-Ziel für alle Direkt-Leser; trägt den neutralen Render-State `GATE_NEUTRAL`
  (siehe unten) statt einer Runtime-Zusage.
- **Provider-native dedizierte Kanäle** (Adapter-Datei oder bestehender `rules_dir`-Kanal):
  nur für Provider, die dafür konfiguriert sind. Der Dispatch ist ausschließlich
  key-/capability-getrieben — nie über einen Provider-Namen.

### Kanal-Matrix (Stand Phase 2)

| Provider | Kanal in `per-provider` | Status |
|---|---|---|
| Opencode, KimiCode, ZCode | **Direkt-Leser** des Kerns (`context_file.core_file`) — keine Adapter-Datei | VERIFIED-RESEARCH |
| Claude | Adapter `CLAUDE.md` (`@AGENTS.md`-Import + managed block) | **einziger heute aktiver Adapter** (VERIFIED-RESEARCH) |
| Gemini/Antigravity (ein Provider) | **Fallback (c):** geteilter Kern `AGENTS.md` + nativer Hook-Kanal — **keine** Adapter-Datei | Fallback (c), s. u. |
| Codex, Copilot, Continue, Mammouth | schlafen (`context_adapter: false`) → bleiben Direkt-Leser des Kerns | HYPOTHESIS, Phase 2 (nicht scharfgeschaltet) |

### Claude-Adapter (aktuell aktiv)

- `config/ai-providers.yaml` setzt für Claude `context_adapter: true`,
  `context_adapter_file: CLAUDE.md`, `context_adapter_import: "@{core}"` und
  `context_adapter_import_supported: true`.
- Der gerenderte Kernverweis ist die provider-native Import-Zeile `@AGENTS.md`; ist die
  Import-Unterstützung aus oder die Syntax leer, fällt die Zeile auf einen Pointer-Satz zurück.
- Der Claude-managed-block trägt **keinen** `GATE_*`-Text. Die verbindliche Hook-Wortwahl lebt
  in der nativen Rules-Datei `.claude/rules/use-orchestrator.md`, die über den bestehenden
  Rules-Seam mit dem Claude-Tier gerendert wird. Der Adapter darf also kein `GATE_ENFORCED`
  im verwalteten `CLAUDE.md`-Block versprechen.

### Gemini/Antigravity — Fallback (c)

- **Verdict FINDING F-RULESLOC:** Kanal (a) `.gemini/rules` ist als
  Antigravity-Workspace-Rules-Lokation **widerlegt** — die offizielle Doku nennt `.agents/rules`
  (rückwärtskompatibel `.agent/rules`). Spike:
  `docs/spikes/2026-09-14-f-rulesloc-gemini-rules-channel.md`; reproduzierbares Protokoll:
  `tests/manual/f-rulesloc-gemini-rules-channel.md`.
- Konsequenz: `per-provider` beansprucht den Gemini/Antigravity-Tier **nicht** über
  `.gemini/rules`. Es gilt **Fallback (c):** geteilter Kern `AGENTS.md` + native
  Hook-Erzwingung (Prompt-Text = Dokumentation).
- Der Hook-Träger ist der verifizierte Antigravity-Vertrag
  (`hook_protocol: antigravity-hooks-json`, Registrierung in `.agents/hooks.json` via
  Übersetzungs-Adapter; siehe Hooks-Hinweis bei Gemini CLI oben). Die tatsächliche
  Runtime-Ausführung steht weiterhin unter dem P6-Real-Repo-Test — sie wird hier bewusst
  **nicht** als erbracht behauptet.
- Kein Config-Bruch, kein Rollback nötig: die Kanalentscheidung ist datengetrieben.
  **Promotion-Pfad:** Bestätigt ein späterer Real-Repo-Lauf Kanal (a), lässt sich der Tier ohne
  neue Keys über `.gemini/rules` tragen — der Seam injiziert den Tier bereits heute. Der
  Live-Real-Repo-Lauf des Protokolls ist noch offen (Follow-up aus Plan-Task 4).

### `GATE_NEUTRAL` (Kern-Render-State)

- In `per-provider` rendert der **Kern** die neutrale Variante der Gate-Regel: die Direktive
  bleibt, **ohne** Runtime-Versprechen; `a2a-delegation-gates` verweist für die Durchsetzung
  auf den Adapter bzw. den provider-eigenen Kanal.
- `GATE_NEUTRAL` ist ein **Render-State**, **kein** Runtime-Tier: es steht nicht in
  `RUNTIME_GATE_TIERS` (`scripts/lib/runtime_gate.py`); das Tier-Vokabular und die Rangfolge
  bleiben unverändert. Der Kern behauptet damit keine Erzwingung, die er nicht leisten kann.

### Adapter-Size-Guard

- `context_file.max_lines` gilt auch für Adapter-Dateien. Der Size-Guard
  (`scripts/lib/consistency/context_size.py::check_context_file_size`) zählt Adapter-Pfade
  zusätzlich und meldet eine Überschreitung **mit dem Adapter-Pfad** getrennt vom Kern.
- `context_file.oversize_acknowledged: true` unterdrückt die Warnung wie beim Kern. Geprüft
  werden nur generierte (managed-markierte) Dateien; eine fehlende Adapter-Datei ist kein Finding.

### Consistency-Check

`scripts/lib/consistency/context_topology.py::check_context_topology_consistency` prüft die
**Konfiguration** (nicht das gerenderte Ergebnis) und meldet ausschließlich WARNINGs:

- ungültiger `context_file.topology`-Enum-Wert (Projekt oder Provider-Override),
- adapter-fähiger Provider ohne nicht-leeren `context_adapter_file`,
- zwei Provider mit derselben Adapter-Datei (Kollision),
- `per-provider`-Adapter ohne Verweis auf `context_file.core_file`,
- verwaiste Adapter-Datei in `unified` ohne managed-Index-Eintrag (verweist auf den Rollback).

Registriert im Consistency-Lauf (`scripts/consistency-check.py`, u. a. über
`sync.py --validate`). Der Check ist WARNING-only und bricht keinen Sync ab.

### Admin-UI

- Der bestehende `context_file`-Abschnitt ist schreibbar (`PROJECT_WRITABLE_SECTIONS`); es gibt
  **keinen** neuen Endpoint und **keinen** neuen Top-Level-Abschnitt.
- Die Projekt-Ansicht rendert `topology` als Dropdown (Default `unified`) und `core_file` als
  Textfeld. Der Help-Text grenzt die Topologie-Achse ausdrücklich von der Dichte
  (`context_file.mode: full|compact`) ab.
- Das Help-Mapping (`check_ui_help_mappings`) kennt `context_file.topology`, sodass der
  Consistency-Lauf dafür kein Finding meldet.

### Rollback auf `unified`

- Ein Wechsel `per-provider` → `unified` entfernt **index-getrackte** Adapter über
  `rollback_context_adapters` (`scripts/lib/context.py`), **backup-first**: der Dateiinhalt
  wird zuvor als `.sync-backup-<ts>`-Geschwister gesichert.
- Allein der managed-Index (`.agent-meta-context-adapters-managed`) autorisiert eine Löschung —
  fremde/user-Dateien ohne Index-Eintrag bleiben unberührt; der Index wird verworfen, sobald
  kein Adapter mehr erwartet wird. Der Kern fällt auf die geteilte Weakest-Tier-Regel zurück.
- **Bekannte Limitierung (dokumentiert, nicht gefixt):** Der Rollback läuft unter
  `context_file.auto_generate`. Bei `context_file.auto_generate: false` werden Adapter beim
  Wechsel auf `unified` **nicht** abgeräumt; ein manueller Eingriff oder ein temporäres
  `auto_generate: true` ist nötig (S1-Contract „`auto_generate: false` wird nie übersteuert").

---

## Sync-Verhalten pro Provider

| Datei | Claude | Gemini | Continue | Opencode |
|-------|--------|--------|----------|----------|
| Agenten-Dateien | ✅ Überschrieben (stale gelöscht) | ✅ Überschrieben (stale gelöscht) | ✅ Überschrieben (stale gelöscht) | ✅ Überschrieben (stale gelöscht) |
| Kontext-Datei (managed block) | ✅ Aktualisiert | ✅ Aktualisiert | ✅ Aktualisiert | ✅ Aktualisiert (incl. eingebettete Rules) |
| Kontext-Datei (Rest) | ❌ Nie angefasst | ❌ Nie angefasst | ❌ Nie angefasst | ❌ Nie angefasst |
| Settings/Config Skeleton | ❌ Einmalig | ❌ Einmalig | ❌ Einmalig | ❌ Einmalig |
| Rules | ✅ Sync (stale gelöscht) | ✅ Sync nach `.gemini/rules/` | ✅ Sync nach `.continue/rules/` | ✅ In `AGENTS.md` eingebettet |
| Hooks | ✅ Sync + registriert | ✅ Sync + registriert (.agents/hooks.json, Antigravity-Protokoll via Adapter) | — | — |
| Commands | ✅ `.claude/commands/*.md` | ✅ `.gemini/commands/*.toml` | ✅ `.continue/prompts/*.md` | ✅ `.opencode/commands/*.md` |

> **Copilot, Mammouth, Codex, ZCode & KimiCode** folgen demselben Grundmuster (Agenten +
> Kontext-Datei + Rules überschrieben/aktualisiert, Skeleton einmalig). Abweichungen: Copilot
> hat keine Hooks/Commands/Settings; Mammouth hat eine Hooks-Reservierung ohne Spiegelung
> (#630-Muster) und ein eigenes `.mammouth/settings.json`, generiert aber keine Commands
> (`has_commands` gesetzt, kein Sync-Zweig — siehe Mammouth-Abschnitt); Codex spiegelt keine
> Hooks und hat kein Settings-File; ZCode und KimiCode generieren keine Rules/Commands/Hooks
> (siehe Provider-Abschnitte oben).

---

## Stale-Tracking

Jeder Provider verwaltet seinen eigenen `.agent-meta-managed`-Index — für Agenten
in `<agents_dir>/`, für Rules in `<rules_dir>/`:

**Agenten-Index (alle Provider):**

- `.claude/agents/.agent-meta-managed`
- `.gemini/agents/.agent-meta-managed`
- `.continue/agents/.agent-meta-managed`
- `.opencode/agents/.agent-meta-managed`
- `.github/copilot/agents/.agent-meta-managed`
- `.mammouth/agents/.agent-meta-managed`
- `.codex/agents/.agent-meta-managed`
- `.zcode/agents/.agent-meta-managed`
- `.kimi-code/agents/.agent-meta-managed`

**Rules-Index (Provider mit `has_rules: true`):**

- `.claude/rules/.agent-meta-managed`
- `.gemini/rules/.agent-meta-managed`
- `.continue/rules/.agent-meta-managed`
- `.github/copilot/rules/.agent-meta-managed`
- `.mammouth/rules/.agent-meta-managed`
- `rules/.agent-meta-managed` (Codex — Projekt-Root)

Generierte MCP-/Tool-Rules nutzen eigene Sidecar-Indizes im selben Rules-Verzeichnis
(`.agent-meta-managed-mcp` bzw. `.agent-meta-managed-tools`).

Agenten die aus der Rollen-Whitelist entfernt werden, werden beim nächsten sync gelöscht.

---

## Vorlagen anpassen

### AGENTS.md anpassen (Gemini, Opencode, Codex, ZCode, KimiCode, Mammouth-Vorlage)

Bearbeite `templates/configs/AGENTS.project-template.md` im agent-meta-Repo.
Der Inhalt außerhalb des managed blocks kann frei gestaltet werden.

### project-context.md (Continue) anpassen

Bearbeite `templates/configs/CONTINUE.project-template.md` im agent-meta-Repo.
Unterstützt dieselben `{{PLATZHALTER}}` wie alle anderen Templates.

### Eigene Continue-Konfiguration

Bearbeite `.continue/config.yaml` direkt im Projekt — wird nie von sync.py überschrieben.
Dokumentation: https://docs.continue.dev

---

## Gitignore-Einträge

`sync.py` ergänzt `.gitignore` automatisch um provider-spezifische Einträge:

```
# agent-meta (Claude)
CLAUDE.personal.md
.claude/settings.local.json

# agent-meta (Gemini) — optional, je nach Projekt
# .gemini/settings.json  ← ggf. hinzufügen wenn Secrets enthalten

# agent-meta (Continue) — optional
# .continue/config.yaml  ← ggf. ignorieren wenn Secrets enthalten
```

**Alternative (issue #557):** Mit `gitignore.ignore-provider-dirs: true` in
`project.yaml` verwaltet der managed block ganze Provider-Verzeichnisse
(`.claude/`, `.gemini/`, `.github/copilot/`, …) statt einzelner Sub-Pfade —
Details siehe [sync-concept.md](../guides/features/sync-concept.md).

---

## Troubleshooting

**Gemini-Agenten werden nicht generiert**
→ Prüfe ob `"Gemini"` in `ai-providers` steht.
→ Prüfe ob `.gemini/agents/` Schreibrechte hat.

**Continue-Agenten haben kein Frontmatter — ist das korrekt?**
→ Ja. Continue lädt Rules als plain Markdown. Frontmatter würde als Rohtext angezeigt.

**`project-context.md` wurde nicht angelegt**
→ Prüfe ob `templates/configs/CONTINUE.project-template.md` im agent-meta-Repo existiert.
→ Führe sync erneut aus — die Datei wird beim ersten sync ohne `--init` angelegt.

**Managed block in `.continue/rules/project-context.md` wird nicht aktualisiert**
→ Prüfe ob `<!-- agent-meta:managed-begin -->` und `<!-- agent-meta:managed-end -->` in der Datei vorhanden sind.
→ Fehlende Marker: Datei löschen und sync erneut ausführen (wird neu angelegt).

**Provider/Validierungsschicht lehnt generierte Agent-Dateien mit "Extra inputs are not permitted" ab**
→ Manche Provider-seitigen Validatoren (z.B. ein strikter Registrierungslayer vor einem
  Opencode-Agent-Schema) akzeptieren nur die eigenen Schema-Felder und lehnen agent-meta-Bookkeeping-
  Felder (`version`, `prompt_mode`, `generated-from`) als unbekannte Extra-Inputs ab (Issue #505).
→ Fix ohne agent-meta-Kernänderung: in `.meta-config/project.yaml` unter dem bestehenden
  `provider-options`-Block (wie schon bei Continues `generate-prompts`/`prompt-mode`) das
  betroffene Feld je Provider strippen lassen:
  ```yaml
  provider-options:
    Opencode:
      frontmatter-strip-fields: [version, prompt_mode, generated-from]
  ```
→ Die gestrippten Werte gehen nicht verloren — sie landen als `<!-- agent-meta-provenance: ... -->`
  HTML-Kommentar direkt nach dem Frontmatter, damit Traceability/Version-Bump-Enforcement erhalten bleibt.
→ Default (kein `frontmatter-strip-fields` gesetzt) ist für alle Provider unverändert — reines Opt-in.
