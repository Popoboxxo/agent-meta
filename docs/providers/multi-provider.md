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
- `.gemini/settings.json` — Skeleton (einmalig angelegt); Hooks werden bei jedem sync eingetragen
- `.gemini/commands/*.toml` — Slash-Commands (aus `commands/` transformiert, `.md` → `.toml`)
- `.gemini/hooks/*.sh` — Hook-Skripte (kopiert, stale gelöscht)
- `.gemini/rules/*.md` — Rules (Gemini CLI besitzt ein natives Rules-Verzeichnis, `has_rules: true`)

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
Rules in `AGENTS.md` ein). Hooks werden für Provider mit `has_hooks: true` generiert
(Claude, Gemini, Mammouth) — Codex reserviert lediglich `.codex/hooks/`, spiegelt aber keine
Hooks (kein `hook_protocol`, #630-Muster).

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

## Sync-Verhalten pro Provider

| Datei | Claude | Gemini | Continue | Opencode |
|-------|--------|--------|----------|----------|
| Agenten-Dateien | ✅ Überschrieben (stale gelöscht) | ✅ Überschrieben (stale gelöscht) | ✅ Überschrieben (stale gelöscht) | ✅ Überschrieben (stale gelöscht) |
| Kontext-Datei (managed block) | ✅ Aktualisiert | ✅ Aktualisiert | ✅ Aktualisiert | ✅ Aktualisiert (incl. eingebettete Rules) |
| Kontext-Datei (Rest) | ❌ Nie angefasst | ❌ Nie angefasst | ❌ Nie angefasst | ❌ Nie angefasst |
| Settings/Config Skeleton | ❌ Einmalig | ❌ Einmalig | ❌ Einmalig | ❌ Einmalig |
| Rules | ✅ Sync (stale gelöscht) | ✅ Sync nach `.gemini/rules/` | ✅ Sync nach `.continue/rules/` | ✅ In `AGENTS.md` eingebettet |
| Hooks | ✅ Sync + registriert | ✅ Sync + registriert | — | — |
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
