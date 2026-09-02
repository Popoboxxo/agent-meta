# Kompakt-Bericht: Provider-Support — Claude Code / OpenCode / Antigravity (Gemini)

## STATUS

**done** — reine Recherche, nichts umgesetzt, ein neuer Bug entdeckt (nicht gefiled, siehe unten).

## Claude Code — Referenz-Provider, solide

Vollständigste Unterstützung: Hooks, Skills, Artifacts, Checkpoints, native Subagent-Dispatch, MCP über `.mcp.json` (bewusst getrennt von `settings.json`, da dortige MCP-Einträge inert sind — Audit #388/#400).

**Empfehlungen:**
- Issue #557 umsetzen: `.gitignore` ganze Provider-Verzeichnisse statt Einzeldateien ausschließen können.
- Issue #614 (Plugin-Management-RFC, heute mit `ponytail` selbst erlebt) betrifft Claude zuerst — höchste Dringlichkeit unter den drei Tools.
- `/plugin`-Commands funktionieren nicht über Remote Control (heute erlebt) — keine Framework-Lücke, aber dokumentationswürdig.

## OpenCode — funktional, ein konkreter Bug gefunden

`has_hooks: false`, `has_rules: false` (Rules embedded in `AGENTS.md`), file-based Agents, MCP-Format `opencode-json` mit Secrets-Split.

**Gefundener Bug:** OpenCode und Gemini teilen `context_file: AGENTS.md` (`config/ai-providers.yaml:91,144`). `context.py:978-980` degradiert `has_native_rules` für **beide** Sharer, sobald einer `has_rules: false` hat — trifft auf OpenCode zu. Sind beide gleichzeitig aktiv, verliert Gemini sein natives `.gemini/rules/` (obwohl `has_rules: true`!) und Rules landen embedded in `AGENTS.md`. Undokumentiert, ungetestet.

**Empfehlungen:**
- Shared-Context-Degradierung entkoppeln oder zumindest in `sync.py --validate` sichtbar machen.
- `has_hooks: false` → `orchestrator.strict` wirkungslos für OpenCode (bereits als Warnung sichtbar) — Konventions-Fallback fehlt.
- MCP-Secrets-Split ungetestet (kein Äquivalent zu `test_provider_hooks_config.py`).

## Antigravity/Gemini — das fragilste Setup

API-basierte Registrierung, kein Datei-Inventar. `.gemini/agents/*.md` werden nicht automatisch geladen — jede Session braucht manuellen `define_subagent`-Bootstrap (`provider-bootstrap.yaml`). Bootstrap-Text selbst: "Ephemer — nur für aktuelle Session."

**Warum fragil:**
1. Kein technischer Verifikations-Mechanismus, ob Bootstrap tatsächlich lief.
2. Reihenfolge ("Orchestrator zuerst") nur Prosa, nicht erzwungen.
3. `has_hooks: false` → kein Guard gegen "Bootstrap vergessen".
4. Trifft zusätzlich den OpenCode-Shared-Context-Bug oben.
5. `bootstrap_required: true` wird von `sync.py --validate` nirgends aktiv geprüft.

**Empfehlungen:**
- Neue `sync.py --validate`-Regel: Bootstrap-Block-Präsenz in `AGENTS.md` prüfen (analog `unpaired_closing_tags`).
- Shared-Context-Bug zuerst fixen — untergräbt Geminis einzigen Struktur-Vorteil ggü. OpenCode.
- Falls Gemini/Antigravity Session-Init-Hooks unterstützt (unverifiziert) — dorthin verlagern statt auf Modellgehorsam zu vertrauen.

## Priorisierte Gesamt-Empfehlung

**Gemini/Antigravity zuerst** — einziger Provider ohne technische Absicherung seines Grundmechanismus (Registrierung = ungeprüfte Prosa-Instruktion), im Gegensatz zu Claude/OpenCode (beide dateibasiert, robust). Der Shared-`AGENTS.md`-Bug ist der günstigste Sofort-Fix.

## Nicht gefiled

Der Shared-Context-Bug (OpenCode↔Gemini via `AGENTS.md`) ist neu entdeckt, noch kein Issue. `gh issue search` fand nur #614/#557/#547 als thematisch angrenzend, keine dedizierten Gemini/OpenCode-Robustheits-Issues.

## ARTIFACTS

- Diese Datei: `docs/plans/report-2026-09-provider-support-claude-opencode-gemini.md`
- Bezug: `docs/plans/audit-2026-09-system-concept.md`, `config/ai-providers.yaml`, `scripts/lib/context.py:978-980`, `config/provider-bootstrap.yaml`
