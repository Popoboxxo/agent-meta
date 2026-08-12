# Multi-Provider Support — Claude, Gemini, Opencode, Continue, Copilot, Mammouth

> Dieses Dokument beschreibt wie `sync.py` mehrere AI-Provider gleichzeitig bedienen kann
> und was jeder Provider an Output erhält.

---

## Konzept

`sync.py` generiert Provider-spezifischen Output aus denselben universellen Agent-Templates.
Ein einziges `.meta-config/project.yaml` reicht, um Agenten-Dateien für Claude Code, Gemini CLI,
Opencode, Continue, GitHub Copilot und Mammouth Code gleichzeitig zu erzeugen.

```json
"ai-providers": ["Claude", "Gemini", "Opencode", "Continue", "Copilot", "Mammouth"]
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

> **AGENTS.md ist geteilt:** `Gemini`, `Opencode` und (als Vorlage) `Mammouth` verwenden
> alle das gemeinsame Template `templates/configs/AGENTS.project-template.md`. Gemini und
> Opencode schreiben ihren managed block in dieselbe `AGENTS.md` im Projekt-Root — die Datei
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
- `.mammouth/hooks/*.sh` — Hooks (`has_hooks: true`, eigenes `.mammouth/settings.json`)

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
`.github/copilot/rules/`, Mammouth → `.mammouth/rules/`; Opencode bettet Rules in `AGENTS.md`
ein). Hooks werden für Provider mit `has_hooks: true` generiert (Claude, Gemini, Mammouth).

---

## Kontext-Dateien

### `CLAUDE.md` (Claude)

- Einmalig angelegt via `templates/configs/CLAUDE.project-template.md` (bei `--init`)
- Managed block (`<!-- agent-meta:managed-begin/end -->`) wird bei **jedem sync** aktualisiert
- Rest der Datei: manuell gepflegt, wird nie überschrieben

### `AGENTS.md` (Gemini + Opencode)

- Einmalig angelegt via `templates/configs/AGENTS.project-template.md`
- Managed block wird bei **jedem sync** aktualisiert
- Von Gemini und Opencode gemeinsam genutzt (provider-neutrale Kontext-Datei)
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

Rule-Content aus `config/external-tools-registry.yaml` (z.B. für lokal installierte CLI-Tools wie `graphify`) wird nach dem gleichen Muster wie MCP-Server-Rules eingebettet: für Provider mit `has_rules: true` wird eine eigene Datei `.claude/rules/tool-<name>.md` geschrieben; für Opencode wird der Content direkt in den managed block von `AGENTS.md` eingebettet. Das Layout und die Versioning folgen exakt dem bestehenden MCP-Rule-Embed-Mechanismus (`scripts/lib/context.py`).

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

> **Copilot & Mammouth** folgen demselben Grundmuster (Agenten + Kontext-Datei + Rules
> überschrieben/aktualisiert, Skeleton einmalig). Abweichungen: Copilot hat keine
> Hooks/Commands/Settings; Mammouth hat Hooks (`.mammouth/hooks/`) und ein eigenes
> `.mammouth/settings.json`. Details siehe die Provider-Abschnitte oben.

---

## Stale-Tracking

Jeder Provider hat sein eigenes `.agent-meta-managed`-Index:
- `.claude/agents/.agent-meta-managed`
- `.gemini/agents/.agent-meta-managed`
- `.continue/rules/.agent-meta-managed`

Agenten die aus der Rollen-Whitelist entfernt werden, werden beim nächsten sync gelöscht.

---

## Vorlagen anpassen

### AGENTS.md anpassen (Gemini, Opencode, Mammouth-Vorlage)

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
