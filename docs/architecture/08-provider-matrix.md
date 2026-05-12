# Provider-Matrix — Feature-Vergleich

Übersicht aller unterstützten AI-Provider und ihrer agent-meta-Feature-Unterstützung.

> Konfiguration: `config/ai-providers.yaml` | Aktivierung: `ai-providers:` in `project.yaml`

---

## Feature-Unterstützung

| Feature | Claude | Gemini | Opencode | Continue |
|---------|--------|--------|----------|----------|
| **Agenten** (`.agents/`) | ✅ `.claude/agents/` | ✅ `.gemini/agents/` | ✅ `.opencode/agents/` | ✅ `.continue/agents/` |
| **Rules** | ✅ `.claude/rules/` | ✅ `.gemini/rules/` | ⚠️ in AGENTS.md | ✅ `.continue/rules/` |
| **Hooks** (native) | ✅ `settings.json` | ✅ `settings.json` | ❌ | ❌ |
| **Commands** | ✅ `.claude/commands/` | ✅ `.gemini/commands/` | ✅ `.opencode/commands/` | ✅ `.continue/prompts/` |
| **MCP-Config** | ✅ `settings.json` | ✅ `settings.json` | ✅ `opencode.json` | ✅ `config.yaml` |
| **Provider-Isolation** | ✅ `permissions.deny` | ✅ TOML-Policy | ✅ `permission.edit/read deny` | ⚠️ Soft-Rule |
| **Viz-Prompt-Block** | ✅ | ✅ | ✅ | ✅ |
| **External Skills** | ✅ | ❌ | ❌ | ❌ |
| **model: Frontmatter** | ✅ | ✅ | ✅ | ✅ |
| **memory: Frontmatter** | ✅ | ❌ entfernt | ❌ | ❌ |
| **permissionMode:** | ✅ | ❌ entfernt | ❌ | ❌ |
| **temperature:** | ✅ | ✅ | ✅ | ✅ |
| **maxTokens:** | ✅ | ✅ | ✅ | ✅ |

---

## Frontmatter-Format

### Claude (`.claude/agents/<role>.md`)
```yaml
---
name: developer
description: "..."
model: claude-sonnet-4-6
memory: project
permissionMode: default
temperature: 0.2
maxTokens: 8192
generated-from: 1-generic/developer.md@2.1.0
---
```

### Gemini (`.gemini/agents/<role>.md`)
```yaml
---
name: developer
description: "..."
model: gemini-2.5-pro
generated-from: 1-generic/developer.md@2.1.0
---
```
`memory:` und `permissionMode:` werden entfernt. Claude-spezifische Zeilen im Body werden gefiltert.

### Opencode (`.opencode/agents/<role>.md`)
```yaml
---
description: "..."
mode: subagent
model: opencode-go/qwen3.6-plus
---
```
Kein `name:`-Feld. Kein `generated-from:`. Model-IDs im `provider/model-id`-Format.

### Continue (`.continue/agents/<role>.md`)
```yaml
---
name: developer
description: "..."
alwaysApply: false
---
```
Minimales Frontmatter. Body wird bereinigt (Claude-spezifische Zeilen entfernt).

---

## Modell-Tier-Mapping

Abstrakte Tier-Namen → Provider-spezifische Modell-IDs.

| Tier | Claude | Gemini | Opencode | Continue |
|------|--------|--------|----------|----------|
| `nano` | `claude-haiku-4-5-20251001` | `gemini-2.5-flash` | `opencode-go/deepseek-v4-flash` | `codellama:7b` |
| `fast` | `claude-haiku-4-5-20251001` | `gemini-2.5-flash` | `opencode-go/deepseek-v4-flash` | `codellama:7b` |
| `balanced` | `claude-sonnet-4-6` | `gemini-2.5-pro` | `opencode-go/qwen3.6-plus` | `claude-sonnet-4-6` |
| `powerful` | `claude-opus-4-7` | `gemini-2.5-pro` | `opencode-go/kimi-k2.5` | `claude-opus-4-7` |
| `max` | `claude-opus-4-7` | `gemini-2.5-pro` | `opencode-go/kimi-k2.6` | `claude-opus-4-7` |

> Legacy-Aliases: `haiku` → `fast`, `sonnet` → `balanced`, `opus` → `powerful`

---

## Generierte Artefakte pro Provider

| Artefakt | Claude | Gemini | Opencode | Continue |
|----------|--------|--------|----------|----------|
| Agenten | `.claude/agents/*.md` | `.gemini/agents/*.md` | `.opencode/agents/*.md` | `.continue/agents/*.md` |
| Rules | `.claude/rules/*.md` | `.gemini/rules/*.md` | in AGENTS.md | `.continue/rules/*.md` |
| Commands | `.claude/commands/*.md` | `.gemini/commands/*.md` | `.opencode/commands/*.md` | `.continue/prompts/*.md` |
| Settings | `.claude/settings.json` | `.gemini/settings.json` | `opencode.json` | `.continue/config.yaml` |
| Local Settings | `.claude/settings.local.json` | `.gemini/settings.local.json` | `.opencode/mcp.local.json` | `.continue/config.local.yaml` |
| MCP-Rules | `.claude/rules/mcp-<name>.md` | `.gemini/rules/mcp-<name>.md` | *(kein rules-dir)* | `.continue/rules/mcp-<name>.md` |
| Isolation-Policy | `permissions.deny` in `settings.json` | `.gemini/policies/provider-isolation.toml` | `permission.edit/read deny` in `opencode.json` | `.continue/rules/provider-isolation.md` |

---

## Hook-Events (Claude & Gemini)

| Event | Trigger |
|-------|---------|
| `PreToolUse` | Vor jedem Tool-Aufruf |
| `PostToolUse` | Nach jedem Tool-Aufruf |
| `Notification` | Bei Benachrichtigungen |
| `Stop` | Am Ende einer Antwort |
| `SubagentStop` | Am Ende einer Subagenten-Antwort |

Hook-Scripts liegen in `hooks/1-generic/` und `hooks/2-platform/`.
Opencode und Continue haben keine nativen Hooks — der Viz-Prompt-Block übernimmt
Event-Logging via Bash-Befehle im Agenten-Prompt.

---

## Verwandte Dokumente

- [API Reference](07-api-reference.md)
- [Schichten-Architektur](01-layer-model.md)
- [howto/mcp-setup.md](../../howto/mcp-setup.md)
- `config/ai-providers.yaml` — vollständige Provider-Konfiguration
