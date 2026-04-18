# Multi-Provider Support — Gemini, Continue und Claude gleichzeitig

> Dieses Dokument beschreibt wie `sync.py` mehrere AI-Provider gleichzeitig bedienen kann
> und was jeder Provider an Output erhält.

---

## Konzept

`sync.py` generiert Provider-spezifischen Output aus denselben universellen Agent-Templates.
Ein einziges `.meta-config/project.yaml` reicht, um Agenten-Dateien für Claude Code, Gemini CLI
und Continue gleichzeitig zu erzeugen.

```json
"ai-providers": ["Claude", "Gemini", "Continue"]
```

Backward-compatible: `"ai-provider": "Claude"` (String) funktioniert weiterhin unverändert.

---

## Unterstützte Provider

| Provider | Agents-Verzeichnis | Dateiendung | Kontext-Datei | Frontmatter |
|----------|--------------------|-------------|---------------|-------------|
| `Claude` | `.claude/agents/` | `.md` | `CLAUDE.md` | Vollständig (`model`, `memory`, `permissionMode`, …) |
| `Gemini` | `.gemini/agents/` | `.md` | `.gemini/GEMINI.md` | Reduziert (`model` only, kein `memory`/`permissionMode`) |
| `Continue` | `.continue/agents/` | `.md` | `.continue/rules/project-context.md` | Minimal (`name`, `description`, `alwaysApply: false`) |

### Claude Code

Vollständiger Output — keine Einschränkungen:
- `.claude/agents/*.md` — alle generierten Agenten
- `CLAUDE.md` — managed block wird bei jedem sync aktualisiert
- `.claude/rules/*.md` — Rules (auto-geladen in jeden Agenten-Kontext)
- `.claude/hooks/*.sh` — Hooks (registriert in `.claude/settings.json`)
- `.claude/settings.json` — Skeleton + Hooks-Section

### Gemini CLI

Gemini hat kein Rules- oder Hooks-System:
- `.gemini/agents/*.md` — generierte Agenten (gleicher Markdown-Body wie Claude)
- `.gemini/GEMINI.md` — Kontext-Datei, managed block wird bei jedem sync aktualisiert
- `.gemini/settings.json` — Skeleton (nur einmalig angelegt, nicht überschrieben)

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

**Hinweis:** Rules und Hooks werden nur für Claude generiert. Für andere Provider entfällt
das Rules-/Hooks-System.

---

## Kontext-Dateien

### `CLAUDE.md` (Claude)

- Einmalig angelegt via `howto/CLAUDE.project-template.md` (bei `--init`)
- Managed block (`<!-- agent-meta:managed-begin/end -->`) wird bei **jedem sync** aktualisiert
- Rest der Datei: manuell gepflegt, wird nie überschrieben

### `.gemini/GEMINI.md` (Gemini)

- Einmalig angelegt via `howto/GEMINI.project-template.md`
- Managed block wird bei **jedem sync** aktualisiert
- Kein `--init` nötig — wird beim ersten normalen sync angelegt

### `.continue/rules/project-context.md` (Continue)

- Einmalig angelegt via `howto/CONTINUE.project-template.md`
- Managed block wird bei **jedem sync** aktualisiert
- Kein `--init` nötig — wird beim ersten normalen sync angelegt

### `.continue/config.yaml` (Continue)

- Einmalig als Skeleton angelegt (nur Kommentare)
- **Wird nie überschrieben** — eigene Continue-Konfiguration bleibt erhalten
- Enthält Hinweis auf `.continue/rules/`

---

## Sync-Verhalten pro Provider

| Datei | Claude | Gemini | Continue |
|-------|--------|--------|----------|
| Agenten-Dateien | ✅ Überschrieben (stale gelöscht) | ✅ Überschrieben (stale gelöscht) | ✅ Überschrieben (stale gelöscht) |
| Kontext-Datei (managed block) | ✅ Aktualisiert | ✅ Aktualisiert | ✅ Aktualisiert |
| Kontext-Datei (Rest) | ❌ Nie angefasst | ❌ Nie angefasst | ❌ Nie angefasst |
| Settings/Config Skeleton | ❌ Einmalig | ❌ Einmalig | ❌ Einmalig |
| Rules | ✅ Sync (stale gelöscht) | — | — |
| Hooks | ✅ Sync + registriert | — | — |

---

## Stale-Tracking

Jeder Provider hat sein eigenes `.agent-meta-managed`-Index:
- `.claude/agents/.agent-meta-managed`
- `.gemini/agents/.agent-meta-managed`
- `.continue/rules/.agent-meta-managed`

Agenten die aus der Rollen-Whitelist entfernt werden, werden beim nächsten sync gelöscht.

---

## Vorlagen anpassen

### GEMINI.md anpassen

Bearbeite `howto/GEMINI.project-template.md` im agent-meta-Repo.
Der Inhalt außerhalb des managed blocks kann frei gestaltet werden.

### project-context.md (Continue) anpassen

Bearbeite `howto/CONTINUE.project-template.md` im agent-meta-Repo.
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
→ Prüfe ob `howto/CONTINUE.project-template.md` im agent-meta-Repo existiert.
→ Führe sync erneut aus — die Datei wird beim ersten sync ohne `--init` angelegt.

**Managed block in `.continue/rules/project-context.md` wird nicht aktualisiert**
→ Prüfe ob `<!-- agent-meta:managed-begin -->` und `<!-- agent-meta:managed-end -->` in der Datei vorhanden sind.
→ Fehlende Marker: Datei löschen und sync erneut ausführen (wird neu angelegt).
