# Scenario-Katalog

> Persistenter Katalog realistischer Consumer-Projekt-Configs, um `sync.py`
> gegen unterschiedliche Projekt-Aufbauten laufen zu lassen — jedes Szenario
> ist eine eigenständige `.meta-config/project.yaml`. Läuft via
> `tests/scenarios/run.sh` (dry-run + echter Sync + `--validate` pro
> Szenario, in einem frischen Temp-Verzeichnis, nie gegen dieses Repo selbst).
>
> **Konvention:** Jedes neue Feature/jede neue Config-Option bekommt ein
> eigenes Szenario hier (siehe `.claude/skills/conventions/SKILL.md` →
> Change Checklist). `agent-meta-manager` kennt diesen Katalog und verweist
> bei Framework-Änderungen darauf.

## Framework-Szenario-Konvention

Jedes neue Framework-Feature oder jede neue `project.yaml`-Option erhält **zeitgleich** mit der Implementierung mindestens ein neues Testszenario:

1. **Nicht nachträglich**: Szenario und Feature sind Teil **desselben PRs/Commits** — nicht als separater Nachzug.
2. **Konkrete Assertions**: Das Szenario prüft den tatsächlichen Effekt, nicht nur Datei-Existenz:
   - Neue `project.yaml`-Option → `tests/scenarios/asserts/<szenario-name>.sh` validiert die generierte Agent/Config/Regel
   - Neue Agent-Rolle → Szenario prüft erwartete Tools und Settings im generierten Agent
3. **Katalog aktualisieren**: Entry in der Tabelle unten (ID, Beschreibung) + korrespondierendes `configs/<id>.project.yaml`
4. **Lokale Validierung vor Commit**: `tests/scenarios/run.sh` ausführen — `PASS` für alle Szenarien ist Teil der DoD

Diese Konvention stellt sicher, dass Framework-Änderungen durch konkrete, ausführbare Tests validiert werden und nicht nachträglich vergessen.

## Ausführen

```bash
tests/scenarios/run.sh              # alle Szenarien
tests/scenarios/run.sh 12 17        # nur Szenarien, deren ID mit "12" oder "17" beginnt
```

`PASS`/`FAIL` pro Szenario; bei `FAIL` bleibt das Temp-Verzeichnis erhalten
(Pfad wird ausgegeben) zur Fehleranalyse.

Szenarien mit optionalem Content-Assertions-Script
(`tests/scenarios/asserts/<szenario-name>.sh`, ausführbar) führen nach dem
`--validate`-Schritt echte Prüfungen gegen den Sync-Output aus (cwd =
Temp-Dir, `REPO_ROOT` als Env-Var und `$1`). Ein nicht bestandener Assert
ergibt `FAIL` und zeigt die Assertion-Ausgabe; Szenarien ohne Assert-File
verhalten sich exakt wie bisher.

## Katalog

| ID | Provider | Orchestrator-Mode | Feature unter Test |
|----|----------|--------------------|---------------------|
| `01-minimal-claude` | Claude | strict (default) | Minimaler Single-Provider-Smoke-Test |
| `02-multi-provider` | Claude, Gemini, Opencode, Continue | strict (default) | Provider-Isolation, Multi-Provider-Generierung |
| `03-plugin-catalog` | Claude | strict (default) | Plugin-Catalog-Aktivierung (MCP + CLI-Tools) |
| `04-platform-bundle` | Claude | strict (default) | 2-platform-Layer-Override (Sharkord) |
| `05-knowledge-engine` | Claude | strict (default) | Knowledge-Engine-Bundle-Scaffolding |
| `06-se-cascade` | Claude | strict (default) | Systems-Engineering-Kaskade |
| `07-new-providers` | Codex, ZCode, KimiCode | strict (default) | Neuere Provider, Lazy-Channel-Erhalt |
| `08-release-automation` | Claude | strict (default) | Release-Gates + Auto-GitHub-Release-Hook |
| `09-legacy-config` | Claude | strict (default) | Legacy `mcp-servers`/`external-tools`-Fallback |
| `10-model-tiers` | Claude, Gemini | strict (default) | Model-Override-Präzedenz + `model-inherit-main-chat` |
| `11-readme-standard` | Claude | strict (default) | README-Struktur-Standard (#682 §3): `readme.badges/warnings/sections` |
| `12-gitignore-hardening` | Claude, Gemini, Opencode | strict (default) | `.gitignore`-Context-File-Schutz unter `settings: true` (#682 §4) |
| `13-status-table` | Claude, Gemini, Opencode | strict (default) | `STATUS_TABLE_BLOCK`-Rendering über alle Provider-Formate (#678/#682 §5) |
| `14-progress-checkpointing` | Claude | strict (default), `checkpointing: true` | Progress-File-Dokumentation + `.gitignore`-Eintrag (#682 §6) |
| `15-orchestrator-strict` | Claude | **strict** (explizit) | Dedizierter Orchestrator-Subagent, Pflicht |
| `16-orchestrator-advisory` | Claude | **advisory** | Dedizierter Orchestrator-Subagent, empfohlen |
| `17-orchestrator-main-chat` | Claude | **main-chat** | Kein Orchestrator-Subagent — Main Chat routet selbst (agent-metas eigener Modus) |
| `18-auto-commit` | Claude, Gemini | strict (default) | Auto-commit tiers: role eligibility, AUTO_COMMIT_BLOCK rendering, allowlist generation (#694) |
| `19-auto-commit-suggest` | Claude, Gemini | strict (default) | Auto-commit suggest tier: propose-not-pause prose, eligibility excludes git/explorer (#694) |
| `20-auto-commit-custom` | Claude | strict (default) | Auto-commit custom tier: `custom_script` contract + sentinel prefix, no trigger prose (#694) |
| `21-auto-commit-off-ignores-config` | Claude, Gemini, Opencode | strict (default) | Auto-commit off tier: stray config values ignored, zero block rendering, byte-identical output vs. unconfigured sync (#694) |

## Bewusste Auslassungen

- **Setup-Wizard-Secret-Patterns** (`sync.py --setup`, #682 §4.3): interaktiver
  CLI-Flow, kein `project.yaml`-gesteuertes Szenario möglich. Bereits
  abgedeckt durch `tests/test_setup_wizard_secrets_prompt.py`.
- **`CheckpointStore.save_checkpoint()` selbst**: hat laut finalem
  Whole-Branch-Review (2026-09-07, PR #689) noch KEINEN produktiven
  Call-Site — Szenario `14-progress-checkpointing` prüft nur die
  Doku-/Config-Oberfläche (Wortlaut, `.gitignore`-Eintrag), nicht das
  tatsächliche Schreiben von `.claude/progress/current.md` zur Laufzeit.
  Nachziehen, sobald ein Call-Site verdrahtet ist.
- **`backup:`-Block** (`scripts/lib/backup.py`): steuert ausschließlich den
  `--backup`/`--restore`-CLI-Pfad und hat während eines normalen `sync.py`-Laufs
  keinen beobachtbaren Output (keine generierte Config/Doku) — über dieses
  Szenario-Harness (dry-run + sync + `--validate`) also nicht sinnvoll prüfbar.
  Ursprünglich als Szenario 43 geplant, ersetzt durch `43-tier-overrides` aus
  derselben Kategorie (per-role Override mit deterministischem Sync-Footprint).

## Bekannte, unrelated Eigenheit

Minimale Szenario-Configs (z.B. `01-minimal-claude`, `13-status-table`), die
`variables.DOCS_LANGUAGE` nicht explizit setzen, behalten ein unaufgelöstes
`{{DOCS_LANGUAGE}}` im generierten `orchestrator.md` — `DOCS_LANGUAGE` hat
keinen Default in `scripts/lib/config.py`. Vorbestehendes, von diesem Katalog
unabhängiges Verhalten (bereits in `01-minimal-claude` vor jeder Erweiterung
so), kein Scenario-Bug.
| `22-platform-defaults-hacs-passthrough` | Claude | strict (default) | Platform-preset cascade: hacs defaults flow through unmodified (dod-preset/PLATFORM/TEST_COMMANDS) |
| `23-platform-defaults-sharkord-explicit-override` | Claude | strict (default) | Platform-preset cascade: explicit project `variables.TEST_COMMANDS` fully replaces the platform default |
| `24-platform-defaults-homeassistant-additive` | Claude | strict (default) | Platform-preset cascade: project `variables.TEST_COMMANDS+` appends onto the platform default with `&&` |
| `25-platform-defaults-order-hacs-sharkord` | Claude | strict (default) | Platform-preset cascade: `platforms: [hacs, sharkord]` — last platform (sharkord) wins for a plain scalar |
| `26-platform-defaults-order-sharkord-hacs` | Claude | strict (default) | Platform-preset cascade: swapped order flips the winner (order-sensitivity proof) |
| `27-platform-defaults-additive-three-platforms` | Claude | strict (default) | Platform-preset cascade: 3 platforms, additive field set by only 2 — concatenation excludes the third |
| `28-platform-defaults-no-platforms-regression` | Claude | strict (default) | Platform-preset cascade: no `platforms:` key at all — old framework-default behavior unchanged (regression) |
| `29-platform-defaults-dod-preset-explicit-override` | Claude | strict (default) | Platform-preset cascade: explicit project `dod-preset` wins over the platform default |
| `30-platform-defaults-dod-preset-platform-fallback` | Claude | strict (default) | Platform-preset cascade: platform `dod-preset` wins over the old implicit `"full"` |
| `31-platform-defaults-unknown-platform` | Claude | strict (default) | Platform-preset cascade: unknown platform without a `defaults.yaml` — empty cascade, no crash |
| `32-roles-restriction` | Claude | strict (default) | `roles:`-Whitelist generiert NUR die gelisteten Rollen (developer+tester); nicht-gelistete Standardrolle (code-reviewer/orchestrator) fehlt |
| `33-memory-overrides` | Claude | strict (default) | `memory.default_scope` global + `memory-overrides.<role>` — überschriebene Rolle zeigt Override, andere fallen auf globalen Default zurück |
| `34-mcp-role-overrides` | Claude | strict (default) | `mcp-role-overrides.<role>` bindet Tools eines aktiven MCP-Servers (playwright) an eine Rolle, andere Rolle bleibt ohne |
| `35-permission-mode-overrides` | Claude | strict (default) | `permission-mode-overrides.<role>` injiziert `permissionMode`; Rolle ohne Override/Default bekommt kein Feld |
| `36-temperature-overrides` | Claude, Opencode | strict (default) | `temperature-overrides.<role>` rendert in Opencode-Frontmatter (Claude-Markdown hat kein temperature-Feld) für eine Rolle |
| `37-provider-isolation-disabled` | Claude, Gemini | strict (default) | `provider-isolation: disabled` unterdrückt die Cross-Provider-Deny-Einträge (`.gemini/**`) in `.claude/settings.json` |
| `38-dod-custom-overrides` | Claude | strict (default) | `dod:`-Dict überschreibt einzelne Kriterien über dem Preset (rapid-prototyping + req-traceability/security-audit an), untouched bleibt Preset-Wert |
| `39-conventions-custom-overrides` | Claude | strict (default) | `conventions:`-Dict überschreibt Einzelfeld (`issues.title_format`) über dem conventions-preset in `git.md` |
| `40-hooks-opt-in-toggle` | Claude | strict (default) | `hooks:`-Registrierung: default-on Hook deaktiviert (orchestrator-guard nicht in settings.json), opt-in Hook aktiviert (dod-push-check), Skript stets synchronisiert |
| `41-quality-pipelines-custom` | Claude | strict (default) | `quality-pipelines.custom-pipelines` fügt Custom-Pipeline hinzu, gerendert in `orchestrator.md` PIPELINE_DETAIL_BLOCKS |
| `42-external-skills-gitignore` | Claude | strict (default) | Approved+enabled External-Skill mit `gitignore: true` fügt Skill-Dir zum managed `.gitignore`-Block hinzu (offline, config-only) |
| `43-tier-overrides` | Claude | strict (default) | `tier-overrides.<role>` hebt tester von 'fast' auf 'powerful' (claude-opus); developer behält Default — Ersatz für nicht-testbares `backup:` (siehe Auslassungen) |
| `44-speech-mode-childish` | Claude | strict (default) | Nicht-Default `speech-mode: childish` kopiert `speech/childish.md` nach `.claude/rules/speech-mode.md` (Default 'full' erzeugt keine Regel) |
| `45-debug-mode` | Claude | strict (default) | `debug-mode: true` injiziert den Debug-Block-Marker (`<!-- agent-meta:debug-mode -->`) in jeden generierten Agenten |
| `46-progress-tierb-append-rotation` | Opencode | strict (default), `checkpointing: true` | Tier-B (hook-less provider) progress file appends per checkpoint + rotates on new session (live-progress-channel design, 2026-09-10) |
| `47-progress-pipeline-stage-field` | Opencode | strict (default), `checkpointing: true` | `Pipeline/Stage`-Spalte unterscheidet gleichzeitige `se-cascade`/`concept-driven-dev`-Einträge in der Tier-B-Datei (live-progress-channel design) |
| `48-progress-provider-neutral-path` | Opencode | strict (default), `checkpointing: true` | Root-Cause-Fix: `.meta-viz/progress/current.md` statt hartcodiertem `.claude/progress/` für einen Nicht-Claude-Provider (live-progress-channel design) |
| `49-hacs-entity-naming` | Claude | strict (default) | HACS entity-naming: `_attr_has_entity_name`+`_attr_translation_key`, English-master `strings.json`, `async_migrate_entries`-Rename, reviewer Gate 11 |
