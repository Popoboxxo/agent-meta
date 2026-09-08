# Scenario-Katalog

> Persistenter Katalog realistischer Consumer-Projekt-Configs, um `sync.py`
> gegen unterschiedliche Projekt-Aufbauten laufen zu lassen — jedes Szenario
> ist eine eigenständige `.meta-config/project.yaml`. Läuft via
> `tests/scenarios/run.sh` (dry-run + echter Sync + `--validate` pro
> Szenario, in einem frischen Temp-Verzeichnis, nie gegen dieses Repo selbst).
>
> **Konvention:** Jedes neue Feature/jede neue Config-Option bekommt ein
> eigenes Szenario hier (siehe `rules/2-platform/agent-meta-conventions.md` →
> Change Checklist). `agent-meta-manager` kennt diesen Katalog und verweist
> bei Framework-Änderungen darauf.

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

## Bekannte, unrelated Eigenheit

Minimale Szenario-Configs (z.B. `01-minimal-claude`, `13-status-table`), die
`variables.DOCS_LANGUAGE` nicht explizit setzen, behalten ein unaufgelöstes
`{{DOCS_LANGUAGE}}` im generierten `orchestrator.md` — `DOCS_LANGUAGE` hat
keinen Default in `scripts/lib/config.py`. Vorbestehendes, von diesem Katalog
unabhängiges Verhalten (bereits in `01-minimal-claude` vor jeder Erweiterung
so), kein Scenario-Bug.
