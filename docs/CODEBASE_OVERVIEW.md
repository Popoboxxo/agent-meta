# CODEBASE_OVERVIEW — agent-meta

> **Stand:** 2026-05-20 | **Version:** 0.44.0
> Codegenaue Bestandsaufnahme aller `scripts/` Dateien.

---

## scripts/sync.py

**Zweck:** CLI-Entry-Point für den gesamten Sync-Prozess. Liest `project.yaml`, löst Provider/Rollen/Plattformen auf und generiert provider-spezifische Agent-Dateien, Rules, Hooks, Commands, MCP-Artefakte und Extensions.

### CLI-Argumente (argparse)

| Flag | Typ | Beschreibung |
|------|-----|-------------|
| `--config` | str | Pfad zu `project.yaml` (Auto-Detect: `.meta-config/project.yaml`, `agent-meta.config.yaml`, `agent-meta.config.json`) |
| `--init` | bool | Generiert CLAUDE.md/AGENTS.md aus Template (nur wenn nicht vorhanden) |
| `--only-variables` | bool | Nur `{{VARIABLE}}` in existierendem CLAUDE.md substituieren |
| `--create-ext ROLE` | str | Extension-Datei für Rolle erstellen (oder `all`) |
| `--update-ext` | bool | Managed-Block in allen existierenden Extensions aktualisieren |
| `--create-rule NAME` | str | Rule-Template `.claude/rules/<NAME>.md` erstellen |
| `--create-hook NAME` | str | Hook-Template `.claude/hooks/<NAME>.sh` erstellen |
| `--create-command NAME` | str | Command-Template `.claude/commands/<NAME>.md` erstellen |
| `--fill-defaults` | bool | Fehlende Config-Felder mit Defaults schreiben |
| `--setup` | bool | Interaktiver Setup-Wizard |
| `--init-templates` | bool | Plattform-spezifische Starter-Templates kopieren |
| `--copy-templates` | bool | Nur Starter-Templates kopieren, kein Agent-Sync |
| `--dry-run` | bool | Vorschau ohne Datei-Schreibzugriff |
| `--viz` | bool | Statische Agent-Visualisierung generieren |
| `--viz-mode` | str | `off` \| `static` \| `dynamic` \| `full` |
| `--viz-only` | bool | Nur Visualisierung, kein Sync |
| `--viz-cleanup` | bool | Alte Viz-Sessions bereinigen |
| `--clean` | bool | **Neu:** Alle generierten Dateien löschen, dann voller Sync |
| `--force` | bool | **Neu:** Bestätigung für `--clean` überspringen |
| `--update` | bool | **Neu:** Expliziter Alias für Default-Sync (loggt Mode als `update`) |
| `--add-skill URL` | str | Externen Skill als Git-Submodul registrieren |
| `--skill-name NAME` | str | Skill-Identifier für `--add-skill` |
| `--source PATH` | str | Skill-Pfad im Submodul |
| `--role ROLE` | str | Agent-Rolle für Skill-Wrapper |
| `--entry FILE` | str | Entry-File im Skill-Dir (Default: `SKILL.md`) |

### Haupt-Flow (`main()`)

```
1. Parse args → find_agent_meta_root() → SyncLog()
2. --add-skill → add_skill() → exit
3. --setup → run_setup_wizard() → ggf. --init Sync
4. Config laden (auto-detect oder --config)
5. build_variables() + resolve_providers()
6. Mode-Dispatch:
   --fill-defaults  → fill_defaults()
   --only-variables → only_variables()
   --create-ext     → create_extension()
   --update-ext     → update_extensions()
   --create-rule    → create_rule()
   --create-hook    → create_hook()
   --create-command → create_command()
   --copy-templates → copy_starter_templates()
   --viz-only       → generate_viz()
   --viz-cleanup    → cleanup_old_sessions()
   --clean          → clean_generated_files() → Bestätigung → Full Sync (inline)
   default          → Full Sync (init/update/sync)
7. Viz: generate_viz() wenn enabled
8. log.write() → sync.log
```

### Clean-Mode Flow (`--clean`)

```
1. clean_generated_files() scannt alle Provider-Verzeichnisse
2. Geschützte Pfade werden identifiziert (Settings, Extensions, .meta-config/, CLAUDE.md)
3. Dateien werden gelöscht (oder --dry-run: nur angezeigt)
4. Bei --force: sofort weiter, sonst: User-Bestätigung [y/N]
5. Full Sync wird inline ausgeführt (gleicher Code wie else-Zweig)
6. Bei --init + meta-repo: true → scaffold_meta_repo_docs()
```

---

## scripts/lib/io.py

**Zweck:** I/O-Helfer für YAML/JSON, Datei-Schreibzugriffe mit Secret-Scan, Pfadvalidierung und Clean-Funktion.

### `SyncError(Exception)`
- **Signatur:** `class SyncError(Exception)`
- **Zweck:** Fataler Sync-Fehler, beendet den Sync-Prozess.

### `_load_yaml_or_json(*paths) → tuple[dict, Path]`
- **REQ:** —
- **Zweck:** Lädt die erste existierende Datei aus der Pfadliste (YAML oder JSON).

### `_write_yaml(path, data) → None`
- **REQ:** —
- **Zweck:** Schreibt Dict als YAML (UTF-8, `sort_keys=False`, indent=2).

### `content_hash(text) → str`
- **REQ:** —
- **Zweck:** SHA-256 Hex-Digest (erste 16 Zeichen) für Change-Detection.

### `is_unchanged(path, new_content) → bool`
- **REQ:** —
- **Zweck:** Prüft ob Datei bereits den gewünschten Inhalt hat.

### `write_checked(path, content, log, rel_label, force=False, allow_secrets=False) → bool`
- **REQ:** —
- **Zweck:** Schreibt nur bei Änderung (incremental sync). Scannt auf Secrets via `secrets.scan_for_secrets()`.
- **Flow:** `is_unchanged()` → wenn True: return False → `scan_for_secrets()` → wenn Secret + !allow_secrets: SyncError → `path.write_text()` → return True

### `safe_path(base, *parts) → Path`
- **REQ:** —
- **Zweck:** Pfad-Zusammenbau mit Traversal-Schutz.

### `clean_generated_files(project_root, provider_config, providers, log, dry_run=False) → dict`
- **REQ:** #161
- **Signatur:** `(Path, dict, list[str], SyncLog, bool) → {"deleted": [...], "protected": [...]}`
- **Zweck:** Löscht alle generierten Output-Dateien aus Provider-Verzeichnissen.

**Geschützte Pfade (NIEMALS gelöscht):**
- Settings-Dateien (`settings_file` pro Provider)
- Context-Dateien (`context_file` — CLAUDE.md, AGENTS.md)
- Extension-Verzeichnisse (`extension_dir` — `*-ext.md` Dateien)
- `.meta-config/` (alles darin)
- MCP-Secrets-Dateien (`secrets-file`)
- Pending-Tasks-Dateien (`pending_tasks_file`)
- Local-Settings-Pattern (`*.local.*`)

**Flow:**
```
1. Protected-File-Set aufbauen aus Provider-Config
2. _resolve_dir(): Explizite Keys ODER implizite aus has_* Flags + Provider-Naming
3. Phase 1: Alle Provider-Verzeichnisse scannen (agents, rules, hooks, commands, skills, snippets)
4. Phase 2: Top-level generierte Dateien (sync.log)
5. Phase 3: Erst Dateien löschen, dann Verzeichnisse (shutil.rmtree)
6. Return: {"deleted": [...], "protected": [...]}
```

### `_resolve_dir(provider, pc, dir_key) → str | None` (intern)
- **Zweck:** Löst Provider-Verzeichnisse auf mit Fallback für implizite Verzeichnisse.
- **Logik:** Expliziter Key → None für agents_dir → Infer aus `has_*` Flag + `.{provider}/{dirname}`

---

## scripts/lib/config.py

**Zweck:** Config-Laden, Validierung, Variablen-Building, Template-Substitution.

### `load_config(config_path) → dict`
- **Zweck:** Lädt `.meta-config/project.yaml` (oder JSON-Legacy). Validiert gegen JSON-Schema.

### `_validate_config(config, config_path) → None`
- **Zweck:** Validiert gegen `project-config.schema.json` (best-effort, kein Hard-Fail).

### `find_agent_meta_root(script_path) → Path`
- **Zweck:** `scripts/sync.py` → `scripts/` → Agent-Meta-Root.

### `fill_defaults(config_path, agent_meta_root, log, dry_run) → None`
- **Zweck:** Schreibt fehlende Config-Felder mit Defaults.

### `read_version(agent_meta_root) → str`
- **Zweck:** Liest `VERSION`-Datei.

### `read_git_version(agent_meta_root) → str`
- **Zweck:** `git describe --tags --exact-match` für tatsächliche Git-Tag-Version.

### `build_variables(config, agent_meta_root) → tuple[dict, list[str]]`
- **Signatur:** `(dict, Path) → (variables_dict, pre_warnings)`
- **Zweck:** Baut das Substitutions-Dict für `{{VAR}}`-Platzhalter.
- **Enthält:** PREFIX, PROJECT_SHORT, PROJECT_NAME, AGENT_META_VERSION, AGENT_META_DATE, AGENT_TABLE, AGENT_HINTS, AI_PROVIDER, MAX_PARALLEL_AGENTS, WORKSPACE_REPOS, SUB_PROJECTS, META_REPO, DOD_*, DOD_PRESET, CI_POLL_*, EVALUATOR_OPTIMIZER_*, EVALUATOR_CRITERIA_TABLE + alle `config["variables"]` + **OUTPUT_SCHEMA_*** (REQ #165)

### `_inject_output_schema_variables(variables, config, agent_meta_root) → None` (intern)
- **REQ:** #165
- **Signatur:** `(dict, dict, Path) → None`
- **Zweck:** Liest `output_schema` Pfade aus `config/role-defaults.yaml` pro Rolle, lädt die JSON-Schema-Datei aus `config/output-schemas/`, merged `allOf.$ref` auf `base.schema.json` und injiziert zwei Template-Variablen pro Rolle:
  - `OUTPUT_SCHEMA_<ROLE>` — bereinigtes Schema-JSON (title, description, required, properties)
  - `OUTPUT_SCHEMA_<ROLE>_EXAMPLE` — generiertes Beispiel-JSON via `_generate_example_from_schema()`
  - Setzt `HAS_OUTPUT_SCHEMAS` auf `"true"` wenn mindestens ein Schema geladen wurde.

### `_generate_example_from_schema(schema) → dict` (intern)
- **REQ:** #165
- **Signatur:** `(dict) → dict`
- **Zweck:** Generiert ein plausibles Beispiel-JSON aus einem JSON-Schema. Erkennt Typen (string, integer, number, boolean, array, object), Enum-Werte, und merged `allOf`-Properties. Spezielle Behandlung für `status` → `"success"`, `message` → `"Task completed successfully."`, `warnings`/`errors` → `[]`.

### `_load_role_defaults(agent_meta_root) → dict` (intern)
- **REQ:** #165
- **Signatur:** `(Path) → dict`
- **Zweck:** Lädt `config/role-defaults.yaml` und returniert den `roles`-Dict. Wird von `_inject_output_schema_variables()` genutzt um `output_schema` Pfade pro Rolle zu lesen.

### `strip_inactive_dod_blocks(text, variables, extra_vars=None) → str`
- **Signatur:** `(str, dict, list[str] | None) → str`
- **Zweck:** Entfernt konditionale Blöcke `{{#if VAR}}...{{/if}}` und `{{^VAR}}...{{/if}}`.
- **Neu (REQ #160):** Unterstützt `extra_vars` Parameter für inverse Blöcke (z.B. `CI_POLL_ENABLED`).
- **Erweitert (REQ #165):** `extra_vars` wird jetzt auch mit `OUTPUT_SCHEMA_*` und `HAS_OUTPUT_SCHEMAS` befüllt — sowohl im Legacy-Pfad (`sync_agents`) als auch im Multi-Provider-Pfad (`sync_agents_for_provider`). Default für extra_vars bei fehlendem Wert: `"false"` (Block wird entfernt).

### `substitute(text, variables, source_label, log) → str`
- **Zweck:** Ersetzt `{{VAR}}` im Text. `{{%VAR%}}` → `{{VAR}}` (Escape-Syntax).

---

## scripts/lib/agents.py

**Zweck:** Agent-Dateigenerierung: Frontmatter-Manipulation, Composition-Engine, Multi-Provider-Sync.

### Frontmatter-Utilities

| Funktion | Signatur | Zweck |
|----------|----------|-------|
| `extract_frontmatter_field` | `(content, field) → str \| None` | Liest einzelnes YAML-Frontmatter-Feld |
| `build_frontmatter` | `(content, name, description, generated_from) → str` | Ersetzt name/description, fügt generated-from ein |
| `inject_permission_mode_field` | `(content, permission_mode) → str` | Fügt/aktualisiert `permissionMode:` |
| `inject_memory_field` | `(content, memory) → str` | Fügt/aktualisiert `memory:` |
| `inject_model_field` | `(content, model) → str` | Fügt/aktualisiert `model:` |
| `inject_temperature_field` | `(content, temperature) → str` | Fügt/aktualisiert `temperature:` |
| `inject_max_tokens_field` | `(content, max_tokens) → str` | Fügt/aktualisiert `maxTokens:` |
| `inject_agent_fields` | `(content, role, config, agent_meta_root, provider, provider_config, log, project_root) → str` | Konsolidiert alle 5 inject-Funktionen |

### Composition-Engine

| Funktion | Signatur | Zweck |
|----------|----------|-------|
| `_split_frontmatter` | `(content) → tuple[str, str]` | Trennt Frontmatter-Block vom Body |
| `_parse_frontmatter_yaml` | `(content) → dict` | Parst YAML-Frontmatter |
| `_find_section_bounds` | `(lines, anchor) → tuple[int, int] \| None` | Findet Markdown-Section-Grenzen |
| `_patch_append_after` | `(content, anchor, patch_content, log, source_label) → str` | Fügt nach Section ein |
| `_patch_replace` | `(content, anchor, patch_content, log, source_label) → str` | Ersetzt Section |
| `_patch_delete` | `(content, anchor, log, source_label) → str` | Löscht Section |
| `apply_patch` | `(content, patch, log, source_label) → str` | Dispatch: append/append-after/replace/delete |
| `_merge_frontmatter` | `(base_content, override_fm) → str` | Merged Frontmatter (Override gewinnt) |
| `compose_agent` | `(base_path, override_content, log) → str` | Lädt Base, apply patches, merge FM |

### Sync-Funktionen

| Funktion | Signatur | Zweck |
|----------|----------|-------|
| `target_filename` | `(role, role_map) → str \| None` | Output-Dateiname für Rolle |
| `ext_target_filename` | `(role, prefix) → str` | Extension-Dateiname: `<prefix>-<role>-ext.md` |
| `role_from_platform_file` | `(filename, platforms) → str \| None` | Extrahiert Rolle aus `<platform>-<role>.md` |
| `collect_sources` | `(agent_meta_root, platforms) → tuple[dict, set]` | Sammelt Sources: 1-generic < 2-platform < 3-project |
| `sync_agents` | `(agent_meta_root, project_root, config, variables, log, dry_run) → None` | Legacy Claude-only Sync |
| `sync_agents_for_provider` | `(agent_meta_root, project_root, config, variables, log, dry_run, provider, provider_config, platform_vars, debug_mode) → None` | Multi-Provider Sync (Claude/Gemini/Opencode/Continue) |
| `build_agent_hints` | `(config, agent_meta_root) → str` | Generiert `{{AGENT_HINTS}}` |
| `build_agent_table` | `(config, agent_meta_root) → tuple[str, list[str]]` | Generiert `{{AGENT_TABLE}}` |
| `inject_debug_block` | `(content, agent_name) → str` | Fügt Debug-Modus-Block ein |
| `_transform_frontmatter_for_opencode` | `(content, name, description, model, generated_from) → str` | Opencode-natives Frontmatter |
| `_strip_claude_specific_lines` | `(content) → str` | Entfernt Claude-spezifische Zeilen |

**Wichtig:** `strip_inactive_dod_blocks()` wird mit `extra_vars=["CI_POLL_ENABLED", "EVALUATOR_OPTIMIZER_ENABLED"] + output_schema_vars` aufgerufen — sowohl im Legacy-Pfad (`sync_agents`) als auch im Multi-Provider-Pfad (`sync_agents_for_provider`). Die `output_schema_vars` werden dynamisch aus allen `OUTPUT_SCHEMA_*` Keys + `HAS_OUTPUT_SCHEMAS` gebildet (REQ #165).

---

## scripts/lib/setup.py

**Zweck:** Interaktiver Setup-Wizard und Meta-Repo-Dokumentations-Scaffolding.

### `_ask(prompt, default, validator) → str`
- **Zweck:** User-Input mit Validierung.

### `_ask_choice(prompt, choices, default) → str`
- **Zweck:** Auswahl aus vordefinierten Optionen.

### `_ask_list(prompt, default) → list[str]`
- **Zweck:** Komma-getrennte Liste.

### `scaffold_meta_repo_docs(agent_meta_root, project_root, log, dry_run=False) → list[str]`
- **REQ:** #149
- **Signatur:** `(Path, Path, SyncLog, bool) → list[str]`
- **Zweck:** Erstellt `docs/PATTERNS.md`, `docs/LEARNINGS.md`, `docs/CONVENTIONS.md` wenn `meta-repo: true`.
- **Flow:** Prüft ob Dateien existieren → wenn nein: sucht Starter-Templates in `templates/docs/` → sonst: Default-Header → schreibt Dateien.

### `_default_meta_repo_doc(filename) → str`
- **Zweck:** Generiert Default-Header für PATTERNS.md, LEARNINGS.md, CONVENTIONS.md.

### `run_setup_wizard(agent_meta_root, project_root, target_config, dry_run) → dict`
- **Zweck:** 7-Schritte-Wizard: Identität, Provider, Plattform, DoD, Sprache, Git, Variablen.

---

## scripts/lib/providers.py

**Zweck:** Provider-Konfiguration laden und auflösen.

### `load_providers_config(agent_meta_root) → dict`
- **Zweck:** Lädt `config/ai-providers.yaml`.

### `resolve_providers(config, provider_config) → list[str]`
- **Zweck:** Ermittelt aktive Provider aus `ai-providers` in project.yaml.

---

## scripts/lib/roles.py

**Zweck:** Modell-, Memory-, PermissionMode-, Temperature- und MaxTokens-Auflösung pro Rolle.

### `load_roles_config(agent_meta_root) → dict`
- **Zweck:** Lädt `config/role-defaults.yaml`.

### `build_role_map(agent_meta_root) → dict`
- **Zweck:** Identity-Mapping `{rolle: rolle}`.

### `resolve_model(role, config, agent_meta_root, provider, provider_config) → str`
- **Zweck:** Löst Model-ID auf: Provider-Override → Legacy-Flat → Meta-Default (Tier) → leer.

### `resolve_memory / resolve_permission_mode / resolve_temperature / resolve_max_tokens`
- **Zweck:** Jeweils Projekt-Override → Meta-Default → leer.

---

## scripts/lib/rules.py

**Zweck:** Rule-Sync, Speech-Mode, Rule-Erstellung.

### `load_rules_presets(agent_meta_root) → dict`
### `resolve_rules(config, agent_meta_root) → dict`
### `collect_rule_sources(agent_meta_root, platforms) → dict`
### `sync_rules(...)` → Provider-spezifisches Rule-Schreiben
### `sync_speech_mode(...)` → Speech-Mode-Rule generieren
### `create_rule(...)` → Neue Projekt-Rule anlegen

---

## scripts/lib/hooks.py

**Zweck:** Hook-Sync und Erstellung.

### `parse_hook_metadata(script_content) → dict`
### `collect_hook_sources(agent_meta_root, platforms) → dict`
### `sync_hooks(...)` → Hooks kopieren + settings.json aktualisieren
### `create_hook(...)` → Neues Hook-Template anlegen

---

## scripts/lib/commands.py

**Zweck:** Command-Sync und Erstellung.

### `sync_commands_for_provider(...)` → Commands pro Provider generieren
### `create_command(...)` → Neues Command-Template anlegen

---

## scripts/lib/context.py

**Zweck:** CLAUDE.md/AGENTS.md Management, Settings, Gitignore, Snippets.

### `init_claude_md(...)` → CLAUDE.md aus Template initialisieren
### `init_claude_personal(...)` → CLAUDE.personal.md Skeleton
### `init_settings_json(...)` → .claude/settings.json
### `init_settings_local_json(...)` → .claude/settings.local.json
### `only_variables(...)` → Nur Variablen in CLAUDE.md substituieren
### `sync_context_for_provider(...)` → Context-Datei pro Provider
### `sync_prompts_for_continue(...)` → Continue-spezifische Prompts
### `sync_snippets_for_provider(...)` → Snippets pro Provider
### `ensure_gitignore_entries(...)` → .gitignore Managed-Block aktualisieren

---

## scripts/lib/extensions.py

**Zweck:** Extension-Dateien erstellen und aktualisieren.

### `create_extension(...)` → Neue Extension für Rolle
### `update_extensions(...)` → Managed-Block in allen Extensions aktualisieren

---

## scripts/lib/mcp.py

**Zweck:** MCP-Server-Artefakte generieren.

### `generate_mcp_artifacts(...)` → MCP-Rules + Provider-Configs + Gitignore-Einträge
### `init_secrets_template(...)` → secrets.local.yaml Template

---

## scripts/lib/skills.py

**Zweck:** External Skills Management.

### `load_external_skills_config(agent_meta_root) → dict`
### `_skill_is_active(skill_name, skill_cfg, project_skills) → bool`
### `sync_external_skills_for_provider(...)` → Skill-Wrapper-Agenten generieren
### `add_skill(...)` → Neues Git-Submodul + Config-Eintrag
### `check_pinned_commits(ext_config, agent_meta_root, log) → None`

---

## scripts/lib/platform.py

**Zweck:** Plattform-Konfiguration laden und substituieren.

### `load_platform_config(agent_meta_root, project_root, platforms, log) → dict | None`
### `substitute_platform(content, platform_vars, source_label, log) → str`

---

## scripts/lib/dod.py

**Zweck:** DoD-Presets laden und auflösen.

### `load_dod_presets(agent_meta_root) → dict`
### `resolve_dod(config, agent_meta_root) → dict`
- **Präzedenz:** `dod` (Projekt-Override) > `dod-preset` > `full` (Default)

---

## scripts/lib/isolation.py

**Zweck:** Provider-Isolation (Hard-Block Cross-Provider-Zugriff).

### `sync_provider_isolation(project_root, providers, provider_config, log, dry_run) → None`

---

## scripts/lib/viz.py

**Zweck:** Agent-Visualisierung und Session-Tracking.

### `generate_viz(...)` → Mindmap + HTML-Graph
### `inject_viz_prompt_block(content, role, provider, viz_enabled) → str` → Viz-Event-Logging in Agenten injizieren
### `cleanup_old_sessions(project_root, retention_days, log, dry_run) → None`
### `get_gitignore_entries() → list[str]`

---

## scripts/lib/log.py

**Zweck:** Sync-Logging nach `sync.log`.

### `class SyncLog`
- `info(category, message)` → Info-Eintrag
- `warn(message)` → Warnung
- `action(action_type, target, detail)` → WRITE/DELETE/SKIP
- `skip(target, reason)` → Übersprungen
- `provider_header(provider)` → Provider-Trenner
- `write(log_path, config_path, version, mode, platforms, dry_run, providers, speech_mode)` → Finale Log-Ausgabe

---

## scripts/lib/secrets.py

**Zweck:** Secret-Erkennung in generierten Dateien.

### `scan_for_secrets(content) → list[str]`
- **Zweck:** Scannt auf API-Keys, Tokens, Passwörter etc.

---

## config/output-schemas/

**Zweck:** JSON-Schema-Dateien für strukturierte Agent-Output-Verträge (REQ #165).

### Cluster-Struktur (6 Schemas statt 25)

Die ursprünglich 25 agent-spezifischen Schemas wurden auf **6 Cluster-Schemas** reduziert. Agenten mit ähnlichem Output-Verhalten teilen sich ein Schema. Jedes Cluster-Schema erbt via `allOf: [{ "$ref": "base.schema.json" }]` die Basis-Felder.

| Cluster | Schema-Datei | Agenten (Anzahl) |
|---------|-------------|------------------|
| **Base** | `base.schema.json` | Alle (24) — gemeinsame Basis-Felder |
| **Execution** | `execution-result.schema.json` | developer, git, tester, docker, bun-ci, code-splitter, multi-repo-refactor, openscad-developer, agent-meta-manager (9) |
| **Findings** | `findings-report.schema.json` | reviewer, validator, security-auditor, performance, log-analyzer, compliance-auditor, infrastructure-check (7) |
| **Coordination** | `coordination-output.schema.json` | feature, release, requirements (3) |
| **Knowledge** | `knowledge-output.schema.json` | documenter, ideation, agent-meta-scout (3) |
| **Issue** | `issue-created.schema.json` | feedback, meta-feedback (2) |

### Base-Schema (`base.schema.json`)

Gemeinsame Felder die **alle** Agenten liefern:

| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `status` | enum: `success`, `partial`, `failure` | Ausführungsstatus |
| `message` | string | Menschlich-lesbare Zusammenfassung |
| `warnings` | string[] | Optionale Warnungen |
| `errors` | string[] | Fehler bei `failure` oder `partial` |
| `duration_ms` | integer | Ausführungsdauer in Millisekunden |

### Cluster-Schemas im Detail

#### execution-result.schema.json
**Used by:** developer, git, tester, docker, bun-ci, code-splitter, multi-repo-refactor, openscad-developer, agent-meta-manager

Zusätzliche Felder: `operation`, `files_changed[]`, `commit_sha`, `branch`, `tag`, `target_url`, `pr_url`, `tests_passed`, `tests_total`, `tests_failed`, `coverage`, `build_status`, `lint_status`, `artifacts[]`, `repos_affected[]`, `breaking_changes`, `versions`, `req_id`

#### findings-report.schema.json
**Used by:** reviewer, validator, security-auditor, performance, log-analyzer, compliance-auditor, infrastructure-check

Zusätzliche Felder: `scope`, `files_reviewed[]`, `checks_performed`, `passed_checks`, `failed_checks`, `findings[]`, `score`, `must_fix_count`, `should_fix_count`, `severity_counts`, `dod_compliant`, `overall_risk`, `recommendations[]`, `root_causes[]`

#### coordination-output.schema.json
**Used by:** feature, release, requirements

Zusätzliche Felder: `phase`, `feature_name`, `branch`, `req_id`, `req_ids[]`, `title`, `priority`, `dependencies[]`, `traceability_map`, `version`, `bump_type`, `tag`, `changelog_updated`, `release_url`, `steps_completed[]`

#### knowledge-output.schema.json
**Used by:** documenter, ideation, agent-meta-scout

Zusätzliche Felder: `topic`, `files_updated[]`, `doc_type`, `sections_added`, `sections_modified`, `options[]`, `recommended_approach`, `risks[]`, `next_steps[]`, `discoveries[]`, `recommendations[]`, `confidence`

#### issue-created.schema.json
**Used by:** feedback, meta-feedback

Zusätzliche Felder: `issue_type` (enum), `issue_title`, `issue_url`, `issue_number`, `category`, `related_component`

### 5-Stufen-Einführungsplan

Die Cluster-Schemas werden schrittweise aktiviert:

| Stufe | Aktive Cluster | Agenten |
|-------|---------------|---------|
| **1. Core** | base + execution-result + issue-created | developer, git, tester, feedback, meta-feedback |
| **2. Quality** | + findings-report | reviewer, validator |
| **3. Lifecycle** | + coordination-output | feature, release, requirements |
| **4. Knowledge** | + knowledge-output | documenter, ideation, agent-meta-scout |
| **5. Full** | execution-result + findings-report erweitert | docker, bun-ci, code-splitter, multi-repo-refactor, openscad-developer, agent-meta-manager, security-auditor, performance, log-analyzer, compliance-auditor, infrastructure-check |

### Schema-Inheritance

Jedes Cluster-Schema nutzt JSON-Schema `allOf` mit `$ref` auf `base.schema.json`:
```json
{
  "allOf": [{ "$ref": "base.schema.json" }],
  "properties": { ... cluster-spezifische Felder ... }
}
```

### Integration in Templates

Jedes Agent-Template (außer `orchestrator`) enthält einen konditionalen Block:
```
{{#if OUTPUT_SCHEMA_<ROLE>}}
## Structured Output Contract
...
{{OUTPUT_SCHEMA_<ROLE>}}
...
{{OUTPUT_SCHEMA_<ROLE>_EXAMPLE}}
{{/if}}
```

Der `orchestrator`-Template enthält eine `{{#if HAS_OUTPUT_SCHEMAS}}` Sektion mit Validierungsregeln, Merge-Logik und Schema-Aware Delegation.
