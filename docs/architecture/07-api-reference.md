# API Reference — scripts/lib/

API-Referenz für Contributor:innen, die agent-meta erweitern oder anpassen wollen.

> Alle Module liegen in `scripts/lib/`. Zirkularimporte werden durch lokale Imports innerhalb von Funktionen vermieden.

---

## io.py — I/O-Utilities

Zentrale Lade- und Schreib-Utilities. Wird von fast allen anderen Modulen importiert.

### `_load_yaml_or_json(*paths)`
Lädt die erste existierende Datei aus der Liste (YAML oder JSON). Gibt `(data, used_path)` zurück.
Bevorzugter Pfad (für "not found"-Return) ist immer `paths[0]`.

### `_write_yaml(path, data)`
Schreibt ein Dict als YAML mit konsistenter Formatierung (UTF-8, `sort_keys=False`).

### `write_checked(path, content, log, rel_label, force=False, allow_secrets=False)`
Schreibt `content` nach `path`, sofern sich der Inhalt geändert hat (incremental sync).
Scannt auf Secrets via `secrets.scan_for_secrets()`. Wirft `SyncError` wenn ein Secret in einer
committed Datei gefunden wird (außer `allow_secrets=True`).

### `safe_path(base, *parts)`
Verbindet `base` mit `parts` und prüft, dass der Pfad innerhalb von `base` bleibt.
Verhindert Path-Traversal-Angriffe durch manipulierte Config-Werte.

### `content_hash(text)`
Gibt die ersten 16 Zeichen des SHA-256-Hashes zurück (für Change-Detection).

### `_yaml`, `_YAML_AVAILABLE`
Zentrale YAML-Verfügbarkeit. Alle anderen Module importieren diese statt eigene try/except-Blöcke.

---

## config.py — Projekt-Konfiguration

Lädt, validiert und verarbeitet `project.yaml`.

### `load_config(config_path)`
Lädt und validiert die Projekt-Konfiguration. Gibt ein `dict` zurück.
Unterstützt `.yaml` und `.json` (Legacy-Fallback).

### `fill_defaults(config, agent_meta_root)`
Füllt fehlende Felder mit Standardwerten (siehe `_CONFIG_FIELD_DEFAULTS`).
Gibt `(filled_config, warnings)` zurück.

### `build_variables(config, agent_meta_root)`
Baut das Substitutions-Dict für `{{VAR}}`-Platzhalter in Templates.
Gibt `(variables, warnings)` zurück.

```python
vars, warns = build_variables(config, agent_meta_root)
# vars enthält: PROJECT_NAME, AGENT_HINTS, DOD_*, MAX_PARALLEL_AGENTS, ...
```

### `substitute(text, variables, source_label, log)`
Ersetzt `{{VAR}}`-Platzhalter im Text. Unbekannte Variablen → Warnung im Log.
`{{%VAR%}}` wird als `{{VAR}}` gerendert (Escape-Syntax für Dokumentation in Templates).

### `strip_inactive_dod_blocks(text, variables)`
Entfernt `{{#if DOD_*}}...{{/if}}`-Blöcke deren Variable nicht gesetzt ist.

### `find_agent_meta_root(script_path)`
Erkennt automatisch ob das Skript im Meta-Repo oder als Submodul läuft.

### `read_version(agent_meta_root)` / `read_git_version(agent_meta_root)`
Liest die agent-meta-Version aus `VERSION` oder per `git describe`.

---

## roles.py — Modell- und Metadaten-Auflösung

Löst modell-, memory-, permissionMode-, temperature- und maxTokens-Felder auf.

### `load_roles_config(agent_meta_root)`
Lädt `config/role-defaults.yaml`. Filtert Einträge mit `_`-Präfix (private).

### `build_role_map(agent_meta_root)`
Gibt ein Dict `{rolle: rolle}` (Identity-Mapping) für alle konfigurierten Rollen zurück.

### `resolve_model(role, project_config, agent_meta_root, provider="Claude", provider_config=None)`
Löst die Model-ID für eine Rolle und einen Provider auf.

**Präzedenz** (höchste zuerst):
1. Provider-spezifischer Projekt-Override: `model-overrides[<Provider>][role]`
2. Legacy-Flat-Override: `model-overrides[role]` (nur für Claude)
3. Meta-Default aus `role-defaults.yaml` (Tier-Name → Modell-ID)
4. Leerstring → kein `model:`-Feld

**Tier-Mapping:**
- `nano/fast/balanced/powerful/max` → `config/ai-providers.yaml` `model-tiers[provider]`
- `haiku/sonnet/opus` → Legacy-Aliases (mit Tier-Fallback für Nicht-Claude)
- Vollständige Modell-IDs → werden direkt durchgereicht

### `resolve_memory(role, project_config, agent_meta_root)`
Präzedenz: Projekt-Override → Meta-Default → Leerstring.

### `resolve_permission_mode(role, project_config, agent_meta_root)`
Präzedenz: Projekt-Override → Meta-Default → Leerstring.

### `resolve_temperature(role, project_config, agent_meta_root)`
Präzedenz: `temperature-overrides[role]` → `role-defaults.yaml[role].temperature` → `""`.

### `resolve_max_tokens(role, project_config, agent_meta_root)`
Präzedenz: `max-tokens-overrides[role]` → `role-defaults.yaml[role].max_tokens` → `""`.

---

## agents.py — Agent-Dateigenerierung

Enthält Frontmatter-Manipulation, Composition-Engine und den Sync-Loop.

### Frontmatter-Utilities

#### `extract_frontmatter_field(content, field)`
Liest ein einzelnes Feld aus dem YAML-Frontmatter. Gibt `None` zurück wenn nicht vorhanden.

#### `build_frontmatter(content, name, description, generated_from="")`
Fügt `name:`, `description:` und `generated-from:` ins Frontmatter ein oder aktualisiert sie.

#### `inject_model_field(content, model)` / `inject_memory_field(...)` / etc.
Individuelle Inject-Funktionen für jeden Frontmatter-Wert.
Leerstring → entfernt das Feld. Gesetzter Wert → fügt ein oder aktualisiert.

#### `inject_agent_fields(content, role, config, agent_meta_root, provider="Claude", provider_config=None, log=None, project_root=None)`
Konsolidierter Helper: ruft alle fünf `resolve_*` + `inject_*`-Paare auf.
Wird von `sync_agents()` und `sync_agents_for_provider()` (Claude-Branch) genutzt.

### Composition

#### `compose_agent(source_path, base_path, override_content, override_fm, log)`
Wendet `extends:` + `patches:` aus dem Override-Frontmatter auf die Basis-Datei an.
Patch-Operations: `append-after`, `replace`, `delete`, `append`.
Gibt das vollständig zusammengesetzte Dokument zurück (kein `extends:` im Output).

#### `apply_patch(content, patch, log, source_label)`
Wendet einen einzelnen Patch an. Dispatcht auf `_patch_append_after`, `_patch_replace`, etc.

#### `collect_sources(agent_meta_root, platforms)`
Sammelt alle Source-Dateien in Override-Reihenfolge: `1-generic → 2-platform → 3-project`.
Gibt `(overrides, ext_overrides)` zurück.

### Sync

#### `sync_agents(agent_meta_root, project_root, config, variables, log, dry_run)`
Legacy Claude-only Sync-Pfad. Generiert `.claude/agents/*.md`.

#### `sync_agents_for_provider(provider, agent_meta_root, project_root, config, provider_config, log, dry_run, ...)`
Multi-Provider Sync-Pfad. Generiert Agenten-Dateien für Claude, Gemini, Opencode oder Continue.
Provider-spezifische Transformationen:
- **Claude**: vollständiges Frontmatter (model, memory, permissionMode, temperature, maxTokens)
- **Gemini**: nur Model; memory/permissionMode werden entfernt
- **Opencode**: `_transform_frontmatter_for_opencode()` → `description` + `mode: subagent` + `model`
- **Continue**: minimales Frontmatter (`name`, `description`, `alwaysApply: false`)

#### `build_agent_hints(config, agent_meta_root)`
Generiert den `{{AGENT_HINTS}}`-Block (kompakte Agent-Tabelle für CLAUDE.md).

#### `build_agent_table(config, agent_meta_root)`
Generiert die vollständige Agenten-Tabelle für CLAUDE.md.

---

## rules.py — Regel-Sync

### `load_rules_presets(agent_meta_root)`
Lädt `config/rules-presets.yaml`. Enthält provider- und gemini-spezifische Optionen.

### `resolve_rules(config, agent_meta_root)`
Löst die finale Regel-Liste auf: kombiniert Default-Preset mit Projekt-Overrides.

### `collect_rule_sources(agent_meta_root, platforms)`
Gibt alle Rule-Quell-Dateien in Prioritäts-Reihenfolge zurück.

### `sync_rules(provider, agent_meta_root, project_root, config, log, dry_run, ...)`
Schreibt Rule-Dateien in das Provider-spezifische Verzeichnis.
Respektiert `alwaysApply`, `gemini: skip` und `skip: true` Optionen aus dem Preset.

### `sync_speech_mode(agent_meta_root, project_root, config, log, dry_run)`
Generiert die Speech-Mode-Rule basierend auf `speech-mode` in `project.yaml`.

### `create_rule(agent_meta_root, project_root, topic, log)`
Legt eine neue Projekt-eigene Rule-Datei an (`rules/3-project/<topic>.md`).

---

## hooks.py — Hook-Sync

### `parse_hook_metadata(script_content)`
Liest Metadaten aus Hook-Script-Kommentaren: `# hook: <event>`, `# matcher: <pattern>`.

### `collect_hook_sources(agent_meta_root, platforms)`
Gibt alle Hook-Quell-Dateien zurück (generisch + plattformspezifisch).

### `sync_hooks(provider, agent_meta_root, project_root, config, log, dry_run)`
Kopiert Hook-Scripts und aktualisiert `settings.json`/`settings.local.json`.
Wird für Provider mit `has_hooks: true` ausgeführt (Claude, Gemini).

---

## skills.py — External Skills

### `load_external_skills_config(agent_meta_root)`
Lädt `config/skills-registry.yaml`.

### `_skill_is_active(skill_name, skill_cfg, project_skills)`
Gibt `True` zurück wenn der Skill für das aktuelle Projekt aktiv ist:
- `approved: true` in der Registry, UND
- im Projekt explizit aktiviert via `external-skills[skill_name].enabled: true`

### `sync_external_skills_for_provider(provider, ...)`
Generiert Skill-Wrapper-Agenten für aktivierte externe Skills.

### `add_skill(agent_meta_root, project_root, url, name, role, log)`
Fügt einen neuen externen Skill als Git-Submodul hinzu.

### `check_pinned_commits(ext_config, agent_meta_root, log)`
Warnt wenn ein aktiver Skill-Submodul nicht auf einem gepinnten Commit steht.

---

## providers.py — Provider-Konfiguration

### `load_providers_config(agent_meta_root)`
Lädt `config/ai-providers.yaml`. Gibt das vollständige Provider-Dict zurück.

### `get_active_providers(config, provider_config)`
Gibt die im Projekt konfigurierten Provider zurück (via `ai-providers:` in `project.yaml`).

---

## Verwandte Dokumente

- [Schichten-Architektur](01-layer-model.md)
- [Sync-Flow](02-sync-flow.md)
- [Provider-Matrix](08-provider-matrix.md)
- [howto/sync-concept.md](../../howto/sync-concept.md)
- [howto/agent-composition.md](../../howto/agent-composition.md)
