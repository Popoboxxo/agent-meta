---
pipeline_stages:
  implement: 1
status: geplant
date: 2026-11-06
base-commit: 09925d20
trace:
  - SPEC-system-audit-remediation-2026-11-06
---

# System-Audit-Remediation 2026-11-06 — Implementation Plan

> Status: **geplant** — Freigabe der Spec: Nutzer-Auftrag 2026-11-06.

**Goal:** Die Funde des Systemaudits vom 2026-11-06 werden nach Gegenprüfung in sieben seriellen PR-Gruppen (G1–G7) behoben oder mit Begründung aufgeschoben; jeder Fix ist test-first, quellenbasiert und provider-agnostisch.

**Architecture:** Gruppierung nach Ownership-Subsystem (Hooks, sync-Kern, Orchestrator-Tools, DoD/Spec-Gate, Doku-Drift, Gemini, Token). Jede Gruppe: Issue → Branch von `origin/main` → Test rot → Fix in der Quelle → `sync.py` → Verifikation → Reviewer-Gate → PR → CI-Watch → Checkpoint. Keine Parallelität zwischen Gruppen oder schreibenden Agenten.

**Tech Stack:** Python 3.9 (stdlib + PyYAML), Bash (Hooks), Markdown/YAML-Templates, pytest (nur serielle Subsets).

**Spec:** docs/specs/2026-11-06-system-audit-remediation-spec.md
**Spec-ID:** SPEC-system-audit-remediation-2026-11-06
**Audit-Report (git-ignoriert, Beleg-Quelle):** `/home/hermes/repos/agent-meta/.tmp/system-audit-2026-11-06.md`
**Aufwand:** XL, 70 Tasks in 7 Gruppen. Belastbare Schätzung liefert `effort-estimator` (Textverweis, hier nicht berechnet).

## Ablageort (Begründung)

`.meta-config/project.yaml:55-63` konfiguriert `specs: docs/specs` und `plans: docs/plans`
(`docs/superpowers/specs|plans` sind als Legacy-Lesepfade gelistet, letzter Eintrag
2026-09-13; Bestand: `docs/specs` 49 Dateien, `docs/plans` 62 Dateien). Neue Artefakte
liegen daher unter `docs/specs/` und `docs/plans/`, nicht unter `docs/superpowers/`.

## Global Constraints

- **Strikt seriell.** Eine zweite Claude-Session teilt den Baum: schreibende Agenten und Branchwechsel nie parallel. Keine `parallel_group` in diesem Plan (alle Tasks einer Gruppe berühren überlappende Dateien oder denselben Branch).
- **Jede Gruppe:** von `origin/main` abzweigen (`git fetch`, dann Branch von `origin/main`), vorher `git status` = clean prüfen; bei dirty Baum stoppen und an `main_chat` melden. **Kein Merge, kein Force-Push, kein Tag** — Push/Branch/PR ausschließlich Rolle `git`.
- **Quelle statt Ausgabe:** Hooks nur in `hooks/1-generic/` (und `hooks/0-external/`) ändern, danach `python scripts/sync.py`. **Nie** `.claude/`, `.agents/`, `.gemini/`, `.opencode/` editieren.
- **Golden/Baselines** nur bei beabsichtigter Änderung neu erzeugen, per Eintrag, nie als Sammellauf. Vorab mitprüfen und dokumentieren: `tests/test_test_environments_render.py` (Render-Hash + Versionspins 1.3.3), `tests/test_release_checklist_render.py`, `tests/fixtures/ac01-baseline/hashes.json`, slimming-golden (`tests/test_template_slimming_equivalence.py`), compact-golden, `tests/test_context_budgets.py`.
- **Tests:** nur gezielte serielle Subsets (`python3 -m pytest <pfad> --basetemp="$PYTEST_BASETEMP"`), nie `-n auto`, nie die volle Suite lokal (CI shardet).
- **Verifikation je Gruppe:** `python3 scripts/sync.py --validate` rc 0 und `python3 scripts/consistency-check.py` rc 0.
- **Python 3.9, stdlib only** (PyYAML als dokumentierte Ausnahme); kein `match`, keine PEP-604-Annotation ohne `from __future__ import annotations`.
- **Provider-agnostisch:** Unterschiede über Capability-Flags/Config-Keys, nie `if provider == "Name"`.
- **Hook-Änderungen** pflegen `# version:` und `# changelog:`; `hooks/1-generic/` ist die einzige Quelle, `.agents/hooks` ist gerendertes Abbild.
- **Issues:** Funde ohne Issue bekommen **vor** der Gruppe ein Issue via Rolle `feedback` (Englisch). Commit-Format `<type>(scope): <beschreibung> (#issue)`, Englisch, Imperativ, ≤ 72 Zeichen, ohne BOM.
- **Funde „AUDIT-ONLY"** (K-07..K-17, G4-9) werden **vor** dem Fix am Code belegt; Beleg im PR.
- **Kein `isolation: "worktree"`.** Arbeit direkt im Projektverzeichnis.
- **Sprache:** Plan/Doku Deutsch, Code/Commits/Tests/Issues Englisch.

## File Structure

### G1 — Hooks (`fix/hooks-containment-allowlist`)
- Modify: `hooks/1-generic/lib/hook_common.sh` — Allowlist, Scanner
- Modify: `hooks/1-generic/repo-containment-impl.sh`, `hooks/1-generic/orchestrator-guard-impl.sh`, `hooks/1-generic/dod-push-check.sh`
- Modify: `hooks/1-generic/graphify-read-guard.sh`, `hooks/1-generic/graphify-search-guard.sh` (Pfad vor Änderung per Glob belegen; ggf. `hooks/0-external/`)
- Modify: `rules/1-generic/use-orchestrator.md` (Quelle der Regel; per Glob belegen)
- Modify/Create: `tests/test_orchestrator_guard_hook.py`, `tests/test_hook_common_lib.py`, `tests/test_hook_notebook_multiedit.py`, `tests/test_hook_smoke_optin.py`

### G2 — sync-Kern (`fix/sync-robustness-exit-codes`)
- Modify: `scripts/lib/artifact_validate.py`, `scripts/lib/consistency/model_contracts.py`, `scripts/lib/doctor_formats.py`, `scripts/lib/config.py`, `scripts/lib/deactivation.py`, `scripts/lib/frontmatter.py`, `scripts/lib/hooks.py`, `scripts/lib/cli_commands.py`, `scripts/lib/agent_sync.py`, `scripts/lib/log.py`, `scripts/lib/io.py`, `scripts/lib/sync_pipeline.py`, `scripts/lib/skill_admin.py`, `scripts/lib/pipelines.py`, `scripts/lib/consistency/python_compat.py`, `scripts/lib/skills.py`, `scripts/lib/auto_github_release.py`
- Modify: `tests/test_sync_end_checks.py`; Create: je Fund ein Testmodul (siehe Tabelle)

### G3 — Orchestrator-Tools (`fix/orchestrator-tools-handback`)
- Modify: `config/provider-tools.yaml`, `agents/1-generic/orchestrator.md`, `rules/1-generic/a2a-delegation-gates.md`
- Modify: `tests/test_subagent_allowlist_frontmatter.py`

### G4 — DoD/Spec-Gate (`fix/dod-gating-spec-gate`)
- Modify: `scripts/lib/dod.py`, `config/dod-presets.yaml`, `.meta-config/project.yaml`, `config/role-defaults.yaml`, `scripts/lib/config.py`, `scripts/lib/standalone.py`
- Modify: `agents/1-generic/{git,tester,se-developer,se-junior-developer,se-senior-developer,planner,orchestrator}.md`, `rules/1-generic/{use-orchestrator,spec-plan-workflow,a2a-delegation-gates}.md`
- Tests: `tests/test_dod_platform_cascade.py`, `tests/test_pipelines.py`, `tests/test_spec_plan_consistency.py`, `tests/test_spec_plan_resolve_enabled.py`, `tests/test_spec_plan_group_consistency.py`

### G5 — Doku-Drift (`chore/audit-docs-drift`)
- Modify: `.meta-config/project.yaml`, `docs/REQUIREMENTS.md`, `docs/howto/*`, `agents/1-generic/agent-meta-developer.md` (Pfad per Glob belegen), `config/rules-presets.yaml`, `config/ai-providers.yaml`, `config/tier-presets.yaml`, `config/project-config.schema.json`, `scripts/lib/cli_commands.py`, `scripts/lib/rules.py`, `tests/test_provider_agnostic_dispatch.py`

### G6 — Gemini (`fix/gemini-surface-docs`)
- Modify: `config/provider-capabilities.yaml`, `config/ai-providers.yaml` (nur Kommentar/Doku), ggf. Doku unter `docs/`

### G7 — Token-Diät (`chore/token-diet`, zuletzt)
- Modify: `scripts/lib/agents.py`, `scripts/lib/config.py`, `templates/configs/AGENTS.project-template.md`, `rules/1-generic/branch-guard.md`, `scripts/lib/generated_file_drift.py`, `hooks/1-generic/lib/hook_common.sh`
- Create: `docs/concepts/branch-guard-terminology.md`
- Pins: `tests/fixtures/ac01-baseline/hashes.json`, `tests/test_context_budgets.py`, `tests/test_template_slimming_equivalence.py`, compact-golden

---

## Fund-Tabelle (alle Funde, Verdikt nach Gegenprüfung)

Verdikt-Legende: CONFIRMED / PARTIAL / REFUTED / UNVERIFIABLE (extern) / AUDIT-ONLY (nicht am Code gegengeprüft, vor Fix belegen). „neu" in Tests = neues Testmodul bzw. neuer Fall. „neu (Iss-n)" = Issue wird vor der Gruppe angelegt (Zuordnung zu den 12 Audit-Vorschlägen, siehe nächster Abschnitt).

### Dim 1 — Fehler (F1–F11), Gruppe G2

| Fund-ID | Verdikt | Fix | Tests | Abhängigkeiten | Gruppe | Issue-Ref |
|---|---|---|---|---|---|---|
| F1 | CONFIRMED (P1) | `artifact_validate.py:27-30`, `consistency/model_contracts.py:34-37`: tomli lazy, Fallback `doctor_formats.parse_toml`, `TOMLDecodeError`→`ValueError` | neu: Subprozess mit `tomllib`/`tomli`=`None` importiert `sync.py` | — | G2 | neu (Iss-1) |
| F2 | CONFIRMED | `deactivation.py:279` `log.error(provider_root, msg)` (`log.py:59`) | neu: rmtree-Fehler, kein TypeError | — | G2 | neu (Iss-9) |
| F3 | CONFIRMED | `frontmatter.py:103-110`: bei YAMLError/Nicht-dict Inhalt unverändert + Warnung | neu: ungültiges YAML behält Felder | — | G2 | neu (Iss-9) |
| F4 | CONFIRMED | `config.py:275` `_normalize_null_blocks` erweitern; `hooks.py:519,599`, `cli_commands.py:679/912`, `agent_sync.py:889`: `is True`, unbekannte Hook-Namen warnen | neu: `hooks: {x: true}`, `viz: true`, `enabled: "false"` | nach F3 | G2 | #1141 (+ Iss-9) |
| F5 | CONFIRMED | `cli_commands.py:1697-1709`, `log.py:59-68`: Exit 1 bei `log.errors` mind. unter `--check`; Plain-Sync-Policy entscheiden + dokumentieren; #1142 eigener Pfad | `tests/test_sync_end_checks.py:81` (pinnt Exit 0) anpassen; neu: `--check` mit `[ERROR]` → rc 1 | nach F4 (gleiche Datei) | G2 | #1085, #1142 (+ Iss-9) |
| F6 | CONFIRMED | `io.py:377-384,521`: Mode vor `os.replace` übernehmen / `0o666 & ~umask`; Secrets bleiben 0600 | neu: 0755 bleibt 0755; Secret bleibt 0600 | — | G2 | neu (Iss-11) |
| F7 | CONFIRMED | `config.py:1380,1447-1448,1469-1470`, `sync_pipeline.py:859`, `skill_admin.py:99`: `write_atomic`; CRLF über Bytes | neu: Crash-Simulation, CRLF-Erhalt | nach F6 (nutzt `write_atomic`) | G2 | neu (Iss-11), Folge #573 |
| F8 | PARTIAL: `check_schema` wird nie aufgerufen; Kernproblem (stilles `pass`) stimmt | `config.py:677-678` `except Exception` + stderr-Warnung | neu: kaputtes Schema-JSON → Warnung; `UnknownType`-Crash | — | G2 | neu (Iss-9) |
| F9 | CONFIRMED | `pipelines.py:293-295` `except (Exception, SystemExit)` | neu: `KeyboardInterrupt` propagiert | — | G2 | neu (Iss-9) |
| F10 | PARTIAL: 19 statt 13 Stellen, Wirkung nicht reproduziert (low/judgment) | `encoding="utf-8", errors="replace"` an 19 `subprocess.run(text=True)`-Stellen (u.a. `io.py:538`, `config.py:1486`, `skills.py:150/212`, `auto_github_release.py:186/271`) | AST-Guard-Test: jede `text=True`-Stelle mit `encoding` | — | G2 | neu (Iss-11) |
| F11 | CONFIRMED | `consistency/python_compat.py:33-34`: `scripts/*.py` nicht-rekursiv | neu: Guard findet Verstoß in `scripts/x.py` | — | G2 | neu (Iss-11) |

### Dim 2 — Konzept (K-01..K-17)

| Fund-ID | Verdikt | Fix | Tests | Abhängigkeiten | Gruppe | Issue-Ref |
|---|---|---|---|---|---|---|
| K-01 | CONFIRMED (P1) | stale `.claude/`-Output: `sync` + `--check`-Drift-Gate (Test/CI); **kein Edit** der Ausgabe (ignoriert/regenerierbar) | neu: Drift-Gate-Test | nach K-02 (Render-Ergebnis) | G4 | neu (Iss-4) |
| K-02 | CONFIRMED (P1) | `{{#if DOD_REQ_TRACEABILITY}}`/`{{#if DOD_TESTS_REQUIRED}}`: `git.md:134`, `tester.md:22,32-43,98,119`, `se-developer.md:98,116`, `se-junior-developer.md:97,137`, `se-senior-developer.md:91`, `role-defaults.yaml:2692-2695` | neu: Render mit `rapid-prototyping` ohne REQ-/Test-Pflichtzeilen; `test_dod_platform_cascade.py` | nach K-06 | G4 | neu (Iss-4) |
| K-03 | CONFIRMED (P1) | `role-defaults.yaml:2640-2696` `feature-lifecycle`: `approve`-Stage mit `requires_approval` oder Routing auf `concept-driven-dev` | `tests/test_pipelines.py`, `test_spec_plan_consistency.py` | — | G4 | neu (Iss-5) |
| K-04 | CONFIRMED (P1) | `planner.md` Vorbedingung `Status: APPROVED`; `orchestrator.md:92-98` angleichen | neu: Template-Assertion; `test_spec_plan_consistency.py` | nach K-03 | G4 | neu (Iss-5) |
| K-05 | CONFIRMED | eine Aussage in `use-orchestrator.md:51`, `spec-plan-workflow.md:59`, `orchestrator.md:64` | `test_spec_plan_group_consistency.py` | nach K-04 | G4 | neu (Iss-5) |
| K-06 | CONFIRMED | ein Key für spec-plan: `dod.py:281/374`, `dod-presets.yaml:38,54`, `project.yaml:55-56` | `test_dod_platform_cascade.py`, `test_spec_plan_resolve_enabled.py` | — (zuerst in G4) | G4 | neu (Iss-4) |
| K-07 | AUDIT-ONLY | ein REQ-Format + Validator; Aufwand M → aufschieben, wenn unverhältnismäßig, mit Begründung | — (Entscheidung dokumentiert) | nach K-02 | G4 | neu (Iss-4) |
| K-08 | AUDIT-ONLY | Tabelle in CLAUDE.md-Quelle anlegen oder Pflicht in `project.yaml:248`/`agent-meta-developer.md:165` ändern | Consistency-Check | Beleg zuerst | G5 | neu (Iss-11) |
| K-09 | AUDIT-ONLY | Escape-Beispiel `agent-meta-developer.md:96` (`{{%VAR%}}`) umformulieren | Render-Test | Beleg zuerst | G5 | neu (Iss-11) |
| K-10 | AUDIT-ONLY | `max_depth`: Doku `a2a-delegation-gates.md:30-31` vs `config.py:2134-2141` (`A2A_MAX_DEPTH`), `project.yaml:320-321` — Key-Doku korrigieren (Key ist live) | `test_spec_plan_*` unberührt; Doku-Test | Beleg zuerst | G4 | neu (Iss-11) |
| K-11 | AUDIT-ONLY | tote Pfade `REQUIREMENTS.md:21`, `instantiate-project.md:114` nachziehen | Link-Check | Beleg zuerst | G5 | neu (Iss-11) |
| K-12 | AUDIT-ONLY | `mcp-registry` (`project-config.schema.json:1160-1162`) Ballast: Entfernen oder Termin | Schema-Test | Beleg zuerst | G5 | neu (Iss-11) |
| K-13 | AUDIT-ONLY | Default vereinheitlichen: `config.py:2337-2338` (True) vs `standalone.py:131-132` (false) | `test_dod_platform_cascade.py` | nach K-06 | G4 | neu (Iss-4) |
| K-14 | AUDIT-ONLY | `rules-presets.yaml:73-74` vs `:100-102` Kommentar angleichen | — | Beleg zuerst | G5 | neu (Iss-11) |
| K-15 | AUDIT-ONLY | `_wf-orchestrator-reference.md:15` an `role-defaults.yaml:2652-2695` angleichen | — | Beleg zuerst | G5 | neu (Iss-11) |
| K-16 | AUDIT-ONLY | Hinweis zu fehlendem `.claude/3-project/` (CLAUDE.md:10,41); Absicht VERMUTET | — | Beleg zuerst | G5 | neu (Iss-11) |
| K-17 | AUDIT-ONLY | CLAUDE.md-Kategorien (`:58-62`) mit `REQUIREMENTS.md`-Abschnitten angleichen | — | Beleg zuerst | G5 | neu (Iss-11) |

### Dim 3 — Orchestrierung (F3-01..07)

| Fund-ID | Verdikt | Fix | Tests | Abhängigkeiten | Gruppe | Issue-Ref |
|---|---|---|---|---|---|---|
| F3-01 | CONFIRMED (P1) | `SendMessage`/`TaskStop` in `config/provider-tools.yaml` (claude-Whitelist) + Frontmatter `agents/1-generic/orchestrator.md:7-11`; Z.240/273 korrigieren | `tests/test_subagent_allowlist_frontmatter.py` | — | G3 | #681 teilweise (+ Iss-3) |
| F3-02 | CONFIRMED | Regeltext `use-orchestrator.md:55,58`: „nur bei `strict:false`" (Hook `orchestrator-guard-impl.sh:1406-1421` bleibt) | Hook-Test Main-Thread `git status` strict → rc 2 | nach F6-04 | G1 | neu (Iss-10) |
| F3-03 | CONFIRMED | PreToolUse-Zweig: `Agent` mit `subagent_type=orchestrator` oder `isolation=worktree` bei gesetztem `agent_id` → rc 2 (`orchestrator-guard-impl.sh:268-271`) | `tests/test_orchestrator_guard_hook.py` neu | nach F6-01 | G1 | neu (Iss-10) |
| F3-04 | CONFIRMED | BARRIER (`orchestrator.md:257-262`) + Worker-Contract: Handback fehlt = `failed`, neu dispatchen | Template-Assertion (neu) | nach F3-01 | G3 | neu (Iss-3) |
| F3-05 | UNVERIFIABLE (extern) | nur Doku-Hinweis `run_in_background:false`/`-p`; kein Codeverhalten | — | — | G3 | #681 |
| F3-06 | Kein Fund (Folgekosten) | siehe Token G7 | — | — | G7 | — |
| F3-07 | PARTIAL: Env-Var extern ungeprüft | Doku: Tiefe 3 + Env-Var-Name als „laut Anbieterdoku, ungeprüft" | — | — | G3 | neu (Iss-3) |

### Dim 4 — Provider

| Fund-ID | Verdikt | Fix | Tests | Abhängigkeiten | Gruppe | Issue-Ref |
|---|---|---|---|---|---|---|
| G4-1 | CONFIRMED (P1, interner Widerspruch) | **nur** Doku-Hinweis in `provider-capabilities.yaml` (Default-Flip aufgeschoben: braucht Antigravity-Lauf) | Doku-Test | — | G6 | #854/#860 (+ Iss-6) |
| G4-2 | CONFIRMED (Doku), Wirkung VERMUTET | Tool-Map an Surface koppeln, nur wenn am Code belegbar | neu (bei Fix) | nach G4-1 | G6 | neu (Iss-6) |
| G4-3 | CONFIRMED | `bash_tool_name` `code_execution` vs `run_command` angleichen | neu (bei Fix) | nach G4-2 | G6 | neu (Iss-6) |
| G4-4 | UNVERIFIABLE | aufgeschoben: Runtime-Test nötig | — | — | G6 | neu (Iss-6) |
| G4-5 | UNVERIFIABLE | aufgeschoben (`_agent-meta`-Marker, mit agy testen) | — | — | G6 | neu (Iss-6) |
| G4-6 | **REFUTED** | **keine Änderung**; `""` oder `"*"` matcht alle Tools (Doku) | — | — | G6 | — |
| G4-7 | UNVERIFIABLE | aufgeschoben (Hook-cwd undokumentiert) | — | — | G6 | #860 |
| G4-8 | UNVERIFIABLE | aufgeschoben (`gemini-3.5-*` Modell-IDs) | — | — | G6 | neu (Iss-6) |
| G4-9 | AUDIT-ONLY | aufgeschoben: Verifikation im echten Repo (M) | — | — | G6 | #854/#860 |
| F-OC1 | UNVERIFIABLE | aufgeschoben mit Grund (Request-Optionen-Wirkung nicht belegbar ohne Probe-Run) | — | — | G6 | #1007 nahe |
| F-OC2 | CONFIRMED (Abweichung) | nur dokumentieren: `allowed-fields` ist bewusstes Superset (`ai-providers.yaml` ~381-394) | — | — | G5 | neu (Iss-11) |
| F-OC3 | CONFIRMED | Kommentar zu 4-von-5-Tiers (`ai-providers.yaml:402-408`, `tier-presets.yaml:24-30`) | — | — | G5 | neu (Iss-11) |
| F-PA1 | CONFIRMED | Rename Opencode-benannter Funktionen `cli_commands.py:324-360` (vorher Tests greppen) | bestehende Referenz-Tests + AST-Guard | vor F-PA2 | G5 | neu (Iss-11) |
| F-PA2 | CONFIRMED | `rules.py:478` Default `"Opencode"` prüfen; `test_provider_agnostic_dispatch.py` um Dict-Key-Literale erweitern | `tests/test_provider_agnostic_dispatch.py` | nach F-PA1 | G5 | neu (Iss-11) |

### Dim 5 — Token

| Fund-ID | Verdikt | Fix | Tests | Abhängigkeiten | Gruppe | Issue-Ref |
|---|---|---|---|---|---|---|
| T-1 route_intent-JSON | CONFIRMED (gemessen ~11,4k Tok, ~7,3k einsparbar) | `agents.py:515` `separators=(',',':')`; `name_index` (`agents.py:343`) aus Serialisierung, Verbrauch `:582` behalten | `test_context_budgets.py`, ac01, slimming, compact-golden | Pins vorab prüfen | G7 | #977 nahe (+ Iss-7) |
| T-3 AGENTS.md AGENT_TABLE | CONFIRMED (~1493 Tok) | Block per Flag (`config.py:1649`, `AGENTS.project-template.md`) | `test_context_budgets.py` | nach T-1 | G7 | neu (Iss-7) |
| T-4 branch-guard.md | CONFIRMED (~850 Tok) | Abschnitte Terminologie/Bekannte Grenzen aus `rules/1-generic/branch-guard.md` nach `docs/concepts/`; Kurzfassung bleibt (Anker-Link `#guard-terminologie-…` bleibt auflösbar) | Link-/Consistency-Check, `test_context_budgets.py` | — | G7 | neu (Iss-7) |
| T-2, T-5, T-7, T-8, T-9, T-10 (Pipeline-Auslagerung, manager-Skill, Boilerplate, Rollen-Deaktivierung, Header, Knowledge-Block) | VERMUTET/nicht gegengeprüft | **nicht Teil dieses Plans**; Aufschub, da Wirkung unbelegt | — | — | — | — |
| T-6 graphify-Hinweis | UNVERIFIABLE (Logik extern in `graphify hook-guard`) | nur F6-10 (rc-Normalisierung) in G1; Hinweis-Text nicht änderbar | — | — | G1 | — |
| Backup-Dateien | CONFIRMED | Prune `*.sync-backup-*` (`generated_file_drift.py:152-207`) | neu: Prune-Test | — | G7 | neu (Iss-12) |
| Memory-Notizen | außerhalb Repo | Hinweis an `main_chat`: „~11.8k Tok always-on" widerlegt (jetzt 7693), `rules-preset` ist für `lazy` wirksam; **nicht Teil des Repos** | — | — | G7 | — |

### Dim 6 — Hooks (F6-01..13)

| Fund-ID | Verdikt | Fix | Tests | Abhängigkeiten | Gruppe | Issue-Ref |
|---|---|---|---|---|---|---|
| F6-01 | CONFIRMED (P1) | `NotebookEdit` (Feld `notebook_path`), `MultiEdit` (wie Edit), `PowerShell` (wie Bash) in `repo-containment-impl.sh:225-228` und `orchestrator-guard-impl.sh:268-271`; `hook_common.sh:178` | neu: `/etc/x.ipynb` → rc 2 in beiden Hooks | — (zuerst) | G1 | neu (Iss-2) |
| F6-02 | CONFIRMED | Allowlist-Parität `hook_common.sh:169-188`: ergänzen `LSP`, `PowerShell`, `EndConversation`, `ListAgents`, `ReportFindings`, `SendFeedback`, `ShareOnboardingGuide`, `WaitForMcpServers`, `Workflow`; `ListMcpResourcesTool`/`ReadMcpResourceTool`; PowerShell zuerst in Abfangzweige | `tests/test_hook_common_lib.py` Snapshot-Test | nach F6-01 | G1 | neu (Iss-2), Klasse #1055/#1078/#1137 |
| F6-03 | CONFIRMED, nur Teil | `$(...)`/Backtick innerhalb `"..."` im Scanner `hook_common.sh:533-593`; volle Indirektions-Policy aufgeschoben | neu: `echo "$(git push origin main)"` + Backtick → rc 2 | nach F6-04 | G1 | #592 (+ Iss-8) |
| F6-04 | CONFIRMED | Mutationsliste `orchestrator-guard-impl.sh:390-396`: `git stash` (nackt), `mv`, `apply`, `notes`, `replace`, `update-index`, `config`, `fast-import`, `init`, `submodule update`, `gc` | `test_orchestrator_guard_hook.py` | nach F3-03 | G1 | neu (Iss-8) |
| F6-05 | CONFIRMED | Sentinel bei leerem `agent_id` verwerfen, gebunden an Capability-Flag (Gemini ohne `agent_id`); `orchestrator-guard-impl.sh:296-315,377-382`; Test `test_strict_mode_sentinel_exemption` **neu schreiben** (pinnt Fehlverhalten) | `test_orchestrator_guard_hook.py` | nach F6-04 | G1 | neu (Iss-8) |
| F6-06 | CONFIRMED | `repo-containment-impl.sh:811-818,940-959`: `~`, `$HOME`, `curl -o`, `wget -O`, `tar -C`, `unzip -d`, `git clone`; `$VAR`-Ziele aufgeschoben | neu | nach F6-05 | G1 | #592-nahe (+ Iss-8) |
| F6-07 | CONFIRMED | `cd`/`pushd`-Tracking im Containment | neu: `cd $S; strace -o ../st.txt` | nach F6-06 | G1 | neu (Iss-8) |
| F6-08 | CONFIRMED | Meldung nach `AGENT_ID` (`orchestrator-guard-impl.sh:1434`), Fork-Bomb-Hinweis nur bei Treffer (`:1290`) | neu: Text-Assertion | — | G1 | neu (Iss-10) |
| F6-09 | CONFIRMED | `$'` im Quote-Kontext nur unquotiert werten (`dod-push-check.sh:1285`); Heredoc-/String-Fall dokumentieren | neu: `for c in 'eval "git push"'; …` → kein False-Positive | nach F6-03 | G1 | neu (Iss-8) |
| F6-10 | PARTIAL: nur rc 2 blockt, Crash blockt nicht | `graphify-*-guard.sh:31`: rc nur 0/2; 2 nur mit Guard-Meldung | neu: Fake-graphify rc 1 → 0 | — | G1 | neu (Iss-10) |
| F6-11 | CONFIRMED (Aufwand M) | `hook_json_get` Single-Parse; ggf. aufschieben | Latenz-Messung + Hook-Tests | nach G1 | G7 | neu (Iss-11) |
| F6-12 | CONFIRMED | Platzhalter `{{ AGENT_META_PROVIDER }}` mit Leerzeichen im Kommentar `repo-containment-impl.sh:54` | Render-Test | — | G1 | neu (Iss-10) |
| F6-13 | VERMUTET (Audit-grep) | je ein Smoke-Test: lifecycle-check, sync-on-config-change, viz-log, action-pin-validation, NotebookEdit, Tilde, Allowlist-Parität | neu: `tests/test_hook_smoke_optin.py` | nach F6-01..12 | G1 | neu (Iss-2) |

### Bekannte Issues (nur referenzieren, nicht neu)

#1141 (unbekannte Top-Level-Keys), #1142 (invalid `auto_commit` exit 0), #1139 (Timeout-Test), #1138 (perf `--init`), #1116 (Wall-Clock-Tests), #1085 (Hooks „copied (not enabled)"), #681 (Liveness), #592 (Indirektion), #854/#860 (Gemini), #1007, #977.

## Die 12 vorgeschlagenen Issues (Audit §10, Anlage vor der jeweiligen Gruppe)

| ID | Titel (Englisch, vom `feedback`-Agent angelegt) | Funde | Gruppe |
|---|---|---|---|
| Iss-1 | bug(P1): sync.py imports tomli (tests-only dep) and aborts on Python < 3.11 | F1 | G2 |
| Iss-2 | bug(P1, security-hook): NotebookEdit/MultiEdit bypass repo-containment and strict mode; allowlist parity test | F6-01, F6-02, F6-13 | G1 |
| Iss-3 | fix(P1): orchestrator lacks SendMessage/TaskStop; add missing-handback = failed to BARRIER | F3-01, F3-04, F3-05, F3-07 | G3 |
| Iss-4 | fix(P1): DoD preset gating — ungated REQ/test duties, stale output drift, one spec-plan key | K-01, K-02, K-06, K-07, K-13 | G4 |
| Iss-5 | fix(P1): feature-lifecycle and planner fallback bypass spec approval gate | K-03, K-04, K-05 | G4 |
| Iss-6 | design(P1): Gemini target platform (CLI vs Antigravity) — doc hint now, flip later | G4-1..G4-9, F-OC1 | G6 |
| Iss-7 | perf(P2): compact route_intent JSON, drop name_index, slim AGENTS.md and branch-guard | T-1, T-3, T-4 | G7 |
| Iss-8 | fix(P2, hooks): git mutation verbs, sentinel validation, containment targets, command substitution | F6-03..07, F6-09 | G1 |
| Iss-9 | fix(P2): non-zero exit on log.errors; deactivation TypeError; frontmatter and block-type handling | F2, F3, F4, F5, F8, F9 | G2 |
| Iss-10 | fix(P2): guard Agent subagent_type=orchestrator/worktree; strict-mode vs read-only git rule | F3-02, F3-03, F6-08, F6-10, F6-12 | G1 |
| Iss-11 | chore(P3): hook latency, write_atomic mode, project.yaml atomic write, dead keys, doc drift, py3.9 guard, provider literals | F6, F7, F10, F11, F6-11, K-08..K-17, F-OC2/3, F-PA1/2 | G2/G5/G7 |
| Iss-12 | chore: prune `*.sync-backup-*` from generated output; memory-note update hint | Backup-Dateien, Memory | G7 |

Nummern der neu angelegten Issues werden vom `feedback`-Agenten zurückgemeldet und vom Orchestrator im Ledger neben der Iss-ID vermerkt; Commit-Suffix `(#<Nummer>)` verwendet die echte Nummer.

## PR-Body-Gerüst (für alle Gruppen)

```markdown
## Summary
<1–3 Sätze: was, warum>   Refs #<Issue>

## Root cause
- <Fund-ID>: `datei:zeile` — <Ursache, 1 Satz>

## Before / After
| | Before | After |
|---|---|---|
| <Fund-ID> | <beobachtetes Verhalten/Probe> | <neues Verhalten/Probe> |

## Test evidence
- Rot vor Fix: `<Testbefehl>` → <n failed>
- Grün nach Fix: `<Testbefehl>` → <n passed>
- `python3 scripts/sync.py --validate` rc 0; `python3 scripts/consistency-check.py` rc 0
- Betroffene Golden/Baselines: <Datei, Grund> | keine

## Non-goals
- <aufgeschobene Funde mit Begründung>

## What I could not verify
- <extern/unverifizierbar, z.B. Antigravity-Laufzeit, Python-3.9-Interpreter lokal>
```

## Tasks

Jeder Task nennt die Rolle (genau eine), Abhängigkeit, Files-Ownership und Akzeptanzkriterium. Reviewer-Gate = `code-reviewer`; Git/PR/CI = `git`; Issue-Anlage = `feedback`. Nach jeder Gruppe schreibt der Orchestrator den Ledger (`--update-plan-ledger`) und den Checkpoint; erst dann startet die nächste Gruppe.

---

## G1 — Hooks & Containment (`fix/hooks-containment-allowlist`) — P1, zuerst

**Reihenfolge:** G1-0 → G1-1 → G1-2 → G1-3 → G1-4 → G1-5 → G1-6 → G1-7 → G1-8 → G1-9.
**Verifikation:** gezielte Hook-Tests (`tests/test_orchestrator_guard_hook.py`, `tests/test_hook_common_lib.py`, `tests/test_hook_notebook_multiedit.py`, `tests/test_hook_smoke_optin.py`, Repo-Containment-/dod-push-Tests, `test_hook_*`), `python scripts/sync.py` (gerenderte Hooks nur als Folge), `--validate`, `consistency-check`.
**PR-Body-Fokus:** Root cause `hooks/1-generic/lib/hook_common.sh:169-188`, `repo-containment-impl.sh:225-228`, `orchestrator-guard-impl.sh:268-271,390-396`; Before = Probe rc=0 (`/etc/x.ipynb`); Non-goals = volle Indirektions-Policy (#592), `$VAR`-Ziele; Could-not-verify = Verhalten auf Gemini ohne `agent_id` (nur Capability-Flag-Test), agy-Laufzeit.

### Task G1-0: Issues Iss-2, Iss-8, Iss-10 anlegen

**Agent:** feedback
**Depends on:** —
**Files:** keine (nur GitHub-Issues)
**Interfaces:** Produces Issue-Nummern für Iss-2, Iss-8, Iss-10; Consumes Fund-Tabelle (Belege file:line).

- [ ] Step 1: Drei Issues (Englisch) mit Belegen und Akzeptanzkriterien aus der Fund-Tabelle anlegen; bestehende Issues (#592, #1055/#1078/#1137 als gemergt) verlinken.
- [ ] Step 2: Akzeptanz: drei Nummern zurückgemeldet.

### Task G1-1: Branch von `origin/main`

**Agent:** git
**Depends on:** G1-0
**Files:** keine
**Interfaces:** Produces Branch `fix/hooks-containment-allowlist`; Consumes `origin/main`.

- [ ] Step 1: `git status` = clean prüfen; sonst stoppen und melden (zweite Session).
- [ ] Step 2: `git fetch origin`, Branch von `origin/main` anlegen.
- [ ] Step 3: Akzeptanz: `git branch --show-current` = `fix/hooks-containment-allowlist`, `git log -1` = `origin/main`-Commit.

### Task G1-2: F6-01 + F6-02 (NotebookEdit/MultiEdit/PowerShell, Allowlist-Parität)

**Agent:** senior-developer
**Depends on:** G1-1
**Files:**
- Modify: `hooks/1-generic/lib/hook_common.sh`, `hooks/1-generic/repo-containment-impl.sh`, `hooks/1-generic/orchestrator-guard-impl.sh`
- Create: `tests/test_hook_notebook_multiedit.py`; Modify: `tests/test_hook_common_lib.py`
**Interfaces:** Produces erweiterte `hook_known_tool_name`-Allowlist und Abfangzweige (`notebook_path`); Consumes bestehende `hook_json_get`.

- [ ] Step 1: Tests schreiben (rot): `NotebookEdit notebook_path=/etc/x.ipynb` → rc 2 in beiden Hooks; `MultiEdit` wie `Edit`; `PowerShell` wie `Bash`; Allowlist-Snapshot mit den neun fehlenden und den zwei `...Tool`-Namen; unbekannter Name → rc 2.
- [ ] Step 2: Fix in der Quelle `hooks/1-generic/`: `case`-Zweige ergänzen, `PowerShell` zuerst in die Abfangzweige, Allowlist angleichen; `# version:`/`# changelog:` erhöhen.
- [ ] Step 3: Tests grün; `python scripts/sync.py`; `--validate` rc 0.
- [ ] Step 4: Commit `fix(hooks): intercept NotebookEdit and align tool allowlist (#<Iss-2>)`.

### Task G1-3: F3-03 + F3-02 (Agent-Guard, Regeltext)

**Agent:** senior-developer
**Depends on:** G1-2
**Files:**
- Modify: `hooks/1-generic/orchestrator-guard-impl.sh`, `rules/1-generic/use-orchestrator.md`
- Modify: `tests/test_orchestrator_guard_hook.py`
**Interfaces:** Produces PreToolUse-Zweig `Agent` (`agent_id` gesetzt + `subagent_type=orchestrator` oder `isolation=worktree` → rc 2); Regeltext „nur bei `strict:false`".

- [ ] Step 1: Tests (rot): Subagent-Aufruf `Agent subagent_type=orchestrator` → rc 2; `isolation=worktree` → rc 2; Main-Thread-`Agent` unverändert; Strict-Mode Main-Thread `git status` → rc 2 dokumentiert.
- [ ] Step 2: Zweig implementieren; Regeltext `use-orchestrator.md` (Z.55/58 der gerenderten Fassung) anpassen.
- [ ] Step 3: Tests grün; `sync`; `--validate`.
- [ ] Step 4: Commit `fix(hooks): block orchestrator spawn and worktree isolation (#<Iss-10>)`.

### Task G1-4: F6-04 + F6-05 (Mutationsverben, Sentinel)

**Agent:** senior-developer
**Depends on:** G1-3
**Files:**
- Modify: `hooks/1-generic/orchestrator-guard-impl.sh`, ggf. Capability-Datei `config/provider-capabilities.yaml` (Flag für agent_id-Lieferung; Name per Glob/Lesen der bestehenden Flags festlegen, kein Provider-Name im Hook)
- Modify: `tests/test_orchestrator_guard_hook.py`
**Interfaces:** Produces elf neue Mutationsverben und Sentinel-Prüfung (`agent_id` leer → verworfen, außer Capability sagt „kein agent_id"); Consumes bestehende Sentinel-Grammatik.

- [ ] Step 1: Tests (rot): jedes der elf Verben im Strict-Mode Main-Thread → rc 2; `status`/`log` bleiben erlaubt; Sentinel `#agent-meta:agent=git` ohne `agent_id` → rc 2; Fall „Capability ohne agent_id" → Sentinel gilt; `test_strict_mode_sentinel_exemption` neu schreiben (pinnt Fehlverhalten).
- [ ] Step 2: Verben in die Mutationsliste (`orchestrator-guard-impl.sh:390-396`), Sentinel-Validierung (`:296-315,377-382`) implementieren; Capability-Flag in den Hook-Render durchreichen (über bestehenden Variablen-/Config-Mechanismus).
- [ ] Step 3: Tests grün; `sync`; `--validate`.
- [ ] Step 4: Commit `fix(hooks): block more git mutations and unverified sentinel (#<Iss-8>)`.

### Task G1-5: F6-03 (Teil), F6-06, F6-07, F6-09

**Agent:** senior-developer
**Depends on:** G1-4
**Files:**
- Modify: `hooks/1-generic/lib/hook_common.sh`, `hooks/1-generic/repo-containment-impl.sh`, `hooks/1-generic/dod-push-check.sh`
- Modify: `tests/test_hook_common_lib.py`, Containment-/dod-push-Tests (per Glob belegen)
**Interfaces:** Produces Scanner-Erweiterung `$(...)`/Backtick in `"..."`, Containment-Ziele (`~`, `$HOME`, `curl -o`, `wget -O`, `tar -C`, `unzip -d`, `git clone`), `cd`/`pushd`-Tracking, `$'`-Quote-Kontext.

- [ ] Step 1: Tests (rot): `echo "$(git push origin main)"` und Backtick-Variante → rc 2 in beiden Hooks; `echo x > ~/foo`, `cp a ~/foo`, `curl -o /etc/foo`, `tar -C /etc`, `unzip -d /etc`, `git clone x /etc/foo` → rc 2; `$VAR`-Ziel bleibt dokumentiert offen; `cd $S; strace -o ../st.txt` korrekt aufgelöst; `for c in 'eval "git push"'; do echo "$c"; done` → rc 0.
- [ ] Step 2: Implementieren (`hook_common.sh:533-593`, `repo-containment-impl.sh:811-818,940-959`, `dod-push-check.sh:1285`); Doku-Zeile „Bekannte Grenzen" (Konzept §6.2) fortschreiben.
- [ ] Step 3: Tests grün; `sync`; `--validate`.
- [ ] Step 4: Commit `fix(hooks): scan command substitution and containment targets (#<Iss-8>)`.

### Task G1-6: F6-08, F6-10, F6-12

**Agent:** developer
**Depends on:** G1-5
**Files:**
- Modify: `hooks/1-generic/orchestrator-guard-impl.sh`, `hooks/1-generic/repo-containment-impl.sh`, graphify-Guard-Skripte (Pfade per Glob belegen)
- Modify/Create: zugehörige Tests
**Interfaces:** Produces Meldung nach `AGENT_ID`, Fork-Bomb-Hinweis nur bei Treffer, graphify-Guard-rc nur 0/2, Kommentar-Platzhalter mit Leerzeichen.

- [ ] Step 1: Tests (rot): `agent_id=x` → keine „main chat"-Meldung; `git branch -D` ohne Fork-Bomb-Hinweis; Fake-`graphify` mit rc 1 → Guard rc 0, rc 2 nur mit Meldung; gerenderter Kommentar bleibt „Claude" im Quelltext-Kommentar.
- [ ] Step 2: Implementieren.
- [ ] Step 3: Tests grün; `sync`; `--validate`.
- [ ] Step 4: Commit `fix(hooks): fix guard messages and graphify exit codes (#<Iss-10>)`.

### Task G1-7: F6-13 Smoke-Tests

**Agent:** tester
**Depends on:** G1-6
**Files:** Create: `tests/test_hook_smoke_optin.py`
**Interfaces:** Produces Smoke-Tests für lifecycle-check, sync-on-config-change, viz-log, action-pin-validation, NotebookEdit, Tilde, Allowlist-Parität; Consumes Hook-Quellen.

- [ ] Step 1: je Hook ein Smoke-Test (Aufruf mit synthetischem JSON im Tmp-Projekt unter `.tmp/`, Exit-Code + Kernausgabe).
- [ ] Step 2: Tests grün, seriell; keine Wall-Clock-Assertions (#1116).
- [ ] Step 3: Commit `test(hooks): add smoke tests for opt-in hooks (#<Iss-2>)`.

### Task G1-8: Reviewer-Gate G1

**Agent:** code-reviewer
**Depends on:** G1-7
**Files:** keine (read-only)
**Interfaces:** Consumes Diff `origin/main..HEAD`.

- [ ] Step 1: Stufe 1 Requirement-Treue gegen AC-1..AC-7 der Spec, Stufe 2 Qualität/Blast-Radius (Hook-Latenz, Fail-closed-Verhalten).
- [ ] Step 2: Akzeptanz: Verdikt APPROVED, sonst Findings zurück an G1-2..G1-6 (max. 2 Runden je Stufe).

### Task G1-9: PR + CI-Watch G1

**Agent:** git
**Depends on:** G1-8
**Files:** keine
**Interfaces:** Produces PR (ohne Merge); Consumes PR-Body-Gerüst.

- [ ] Step 1: Push des Branches (kein Force), PR gegen `main` mit Body nach Gerüst + G1-Fokus.
- [ ] Step 2: CI beobachten (`gh pr checks`), Ergebnis melden; roter Check → Rückgabe an Orchestrator, kein Eingriff.
- [ ] Step 3: Akzeptanz: PR-URL und alle Checks grün gemeldet; **kein Merge**.

---

## G2 — sync-Robustheit & Exit-Codes (`fix/sync-robustness-exit-codes`) — P1/P2

**Reihenfolge:** G2-0 → G2-1 → G2-2 (F1) → G2-3 (F8/F9/F3) → G2-4 (F2/F4) → G2-5 (F5) → G2-6 (F6/F7) → G2-7 (F10/F11) → G2-8 → G2-9 → G2-10.
**Verifikation:** `tests/test_sync_end_checks.py`, neue Fund-Tests, Frontmatter-/Hooks-/Config-/io-Tests, `--validate`, `consistency-check`.
**PR-Body-Fokus:** Root cause `artifact_validate.py:27-30`, `cli_commands.py:1697-1709`, `deactivation.py:279`, `frontmatter.py:103-110`; Before = `ModuleNotFoundError: tomli` / Exit 0 trotz `[ERROR]`; Non-goals = #1141-Schema-Typos vollständig, #1142 nur eigener Pfad; Could-not-verify = echter Python-3.9-Interpreter (nur 3.13, daher Subprozess-Simulation).

### Task G2-0: Issues Iss-1 und Iss-9 anlegen

**Agent:** feedback
**Depends on:** G1-9 (Checkpoint G1 geschrieben)
**Files:** keine
**Interfaces:** Produces Issue-Nummern Iss-1, Iss-9.

- [ ] Step 1: Zwei Issues (Englisch) mit Belegen anlegen; #1141, #1142, #1085 verlinken.
- [ ] Step 2: Akzeptanz: Nummern zurückgemeldet.

### Task G2-1: Branch von `origin/main`

**Agent:** git
**Depends on:** G2-0
**Files:** keine
**Interfaces:** Produces Branch `fix/sync-robustness-exit-codes`.

- [ ] Step 1: Baum clean prüfen; `git fetch`; Branch von `origin/main`.
- [ ] Step 2: Akzeptanz: Branchname und Basis-Commit gemeldet.

### Task G2-2: F1 tomli-Fallback

**Agent:** developer
**Depends on:** G2-1
**Files:**
- Modify: `scripts/lib/artifact_validate.py`, `scripts/lib/consistency/model_contracts.py`, `scripts/lib/doctor_formats.py`
- Create: `tests/test_toml_fallback_import.py`
**Interfaces:** Produces lazy TOML-Import mit Fallback `doctor_formats.parse_toml`, `TOMLDecodeError`→`ValueError`.

- [ ] Step 1: Test (rot): Subprozess mit `sys.modules['tomllib']=None` und `tomli=None` importiert `scripts/sync.py` → `ModuleNotFoundError`.
- [ ] Step 2: Fix: lazy Import + Fallback; Fehlerpfad dokumentiert.
- [ ] Step 3: Test grün; `--validate` rc 0.
- [ ] Step 4: Commit `fix(sync): fall back to builtin toml parser without tomli (#<Iss-1>)`.

### Task G2-3: F8 + F9 + F3

**Agent:** developer
**Depends on:** G2-2
**Files:**
- Modify: `scripts/lib/config.py`, `scripts/lib/pipelines.py`, `scripts/lib/frontmatter.py`
- Create: `tests/test_sync_error_handling.py`
**Interfaces:** Produces `except Exception` + Warnung (`config.py:677-678`), `(Exception, SystemExit)` (`pipelines.py:293-295`), unveränderte Rückgabe bei YAML-Fehler (`frontmatter.py:103-110`).

- [ ] Step 1: Tests (rot): kaputtes Schema-JSON warnt (stderr); `KeyboardInterrupt` propagiert aus `pipelines.py`; ungültiges Frontmatter-YAML → Inhalt unverändert + Warnung.
- [ ] Step 2: Implementieren.
- [ ] Step 3: Tests grün; Frontmatter-Konsumenten-Tests (`provider_transform`) grün.
- [ ] Step 4: Commit `fix(sync): stop swallowing schema, interrupt and frontmatter errors (#<Iss-9>)`.

### Task G2-4: F2 + F4

**Agent:** developer
**Depends on:** G2-3
**Files:**
- Modify: `scripts/lib/deactivation.py`, `scripts/lib/hooks.py`, `scripts/lib/cli_commands.py`, `scripts/lib/agent_sync.py`, `scripts/lib/config.py`
- Create: `tests/test_deactivation_log_error.py`, `tests/test_bool_blocks_hooks_viz.py`
**Interfaces:** Produces korrekten `log.error(target, message)`-Aufruf; `_normalize_null_blocks` (`config.py:275`) für bool-Blöcke; `is True`; Warnung bei unbekannten Hook-Namen.

- [ ] Step 1: Tests (rot): rmtree-Fehler in `--deactivate-providers` → kein `TypeError`; `hooks: {x: true}`/`viz: true` → Warnung statt `AttributeError`; `enabled: "false"` nicht truthy; falsch geschriebener Hook-Name warnt.
- [ ] Step 2: Implementieren (`deactivation.py:279`, `hooks.py:519,599`, `cli_commands.py:679/912`, `agent_sync.py:889`).
- [ ] Step 3: Tests grün.
- [ ] Step 4: Commit `fix(sync): normalize bool hook blocks and fix log.error call (#<Iss-9>)`.

### Task G2-5: F5 Exit-Code bei `log.errors`

**Agent:** senior-developer
**Depends on:** G2-4
**Files:**
- Modify: `scripts/lib/cli_commands.py`, `scripts/lib/log.py`, `tests/test_sync_end_checks.py`
- Create: `tests/test_exit_code_log_errors.py`
- Modify: Doku der Entscheidung (CHANGELOG-Eintrag unter `Unreleased`)
**Interfaces:** Produces Exit 1 bei `log.errors` unter `--check`; Plain-Sync-Policy als dokumentierte Entscheidung (D6); #1142 eigener Pfad.

- [ ] Step 1: Tests (rot): `--check` mit `[ERROR]` (Beispiele `opencode_v2_config.py:763`, `backup.py:631`, `sync_pipeline.py:1938`) → rc 1; Plain-Sync-Verhalten gemäß Entscheidung; `tests/test_sync_end_checks.py:81` (pinnt Exit 0) bewusst anpassen.
- [ ] Step 2: Implementieren; Entscheidung + Begründung im PR und CHANGELOG festhalten.
- [ ] Step 3: Tests grün; `--check` auf diesem Repo rc 0 (keine bestehenden `[ERROR]`).
- [ ] Step 4: Commit `fix(sync): exit non-zero when check logs errors (#<Iss-9>)`.

### Task G2-6: F6 + F7 (Mode-Erhalt, atomares Schreiben)

**Agent:** developer
**Depends on:** G2-5
**Files:**
- Modify: `scripts/lib/io.py`, `scripts/lib/config.py`, `scripts/lib/sync_pipeline.py`, `scripts/lib/skill_admin.py`
- Create: `tests/test_write_atomic_mode.py`, `tests/test_config_atomic_write.py`
**Interfaces:** Produces Mode-Erhalt/umask in `write_atomic` (`io.py:377-384,521`), `write_atomic` an den vier Schreibstellen, CRLF über Bytes.

- [ ] Step 1: Tests (rot): 0755 bleibt 0755; Neudatei folgt umask; Secret bleibt 0600; `project.yaml` CRLF bleibt erhalten; Crash-Simulation lässt Originaldatei intakt.
- [ ] Step 2: Implementieren.
- [ ] Step 3: Tests grün; `sync` ändert Mode der gerenderten Hooks wie beabsichtigt (Befund dokumentieren: vorher `-rw-------`).
- [ ] Step 4: Commit `fix(io): preserve file mode and write config atomically (#<Iss-11>)`.

### Task G2-7: F10 + F11

**Agent:** developer
**Depends on:** G2-6
**Files:**
- Modify: 19 `subprocess.run(text=True)`-Stellen (u.a. `io.py`, `config.py`, `skills.py`, `auto_github_release.py`), `scripts/lib/consistency/python_compat.py`
- Create: `tests/test_subprocess_encoding_guard.py`
**Interfaces:** Produces `encoding="utf-8", errors="replace"`; Py3.9-Guard über `("scripts",)` nicht-rekursiv.

- [ ] Step 1: Tests (rot): AST-Guard meldet Stellen ohne `encoding`; `python_compat` findet synthetischen Verstoß in `scripts/x.py`.
- [ ] Step 2: Implementieren (judgment/low: nur reine Zusatzargumente, kein Verhaltenswechsel).
- [ ] Step 3: Tests grün; `consistency-check` rc 0 (kein neuer Fund in `scripts/*.py`).
- [ ] Step 4: Commit `fix(sync): set utf-8 for subprocess text mode, cover scripts dir (#<Iss-11>)`.

### Task G2-8: Reviewer-Gate G2

**Agent:** code-reviewer
**Depends on:** G2-7
**Files:** keine
**Interfaces:** Consumes Diff `origin/main..HEAD`.

- [ ] Step 1: Requirement-Treue gegen AC-8..AC-11, dann Qualität (Exit-Code-Policy, Blast-Radius auf alle `log.error`-Aufrufer).
- [ ] Step 2: Akzeptanz: Verdikt APPROVED oder Findings zurück.

### Task G2-9: PR G2

**Agent:** git
**Depends on:** G2-8
**Files:** keine
**Interfaces:** Produces PR (ohne Merge).

- [ ] Step 1: Push (kein Force), PR mit Body nach Gerüst + G2-Fokus.
- [ ] Step 2: Akzeptanz: PR-URL gemeldet.

### Task G2-10: CI-Watch G2

**Agent:** git
**Depends on:** G2-9
**Files:** keine
**Interfaces:** Consumes `gh pr checks`.

- [ ] Step 1: Checks beobachten und berichten (Python-3.9-Jobs besonders: F1-Test).
- [ ] Step 2: Akzeptanz: alle Checks grün gemeldet; kein Merge.

---

## G3 — Orchestrator-Tools & Handback (`fix/orchestrator-tools-handback`) — P1

**Reihenfolge:** G3-0 → G3-1 → G3-2 → G3-3 → G3-4 → G3-5 → G3-6 → G3-7.
**Verifikation:** `tests/test_subagent_allowlist_frontmatter.py`, Template-/Render-Tests, `--validate`, `consistency-check`; Orchestrator-Render-Hashes (ac01) nur bei beabsichtigter Änderung per Eintrag neu pinnen.
**PR-Body-Fokus:** Root cause `agents/1-generic/orchestrator.md:7-11,240,268,273`, `config/provider-tools.yaml`; Before = Orchestrator ohne `SendMessage`/`TaskStop`; Non-goals = F3-05/F3-07 nur Doku (extern unverifiziert); Could-not-verify = Verhalten von `-p`/SDK-Hintergrundstart.

### Task G3-0: Issue Iss-3 anlegen

**Agent:** feedback
**Depends on:** G2-10 (Checkpoint G2)
**Files:** keine
**Interfaces:** Produces Issue-Nummer Iss-3 (Ref #681).

- [ ] Step 1: Issue (Englisch) mit Belegen anlegen.
- [ ] Step 2: Akzeptanz: Nummer gemeldet.

### Task G3-1: Branch von `origin/main`

**Agent:** git
**Depends on:** G3-0
**Files:** keine
**Interfaces:** Produces Branch `fix/orchestrator-tools-handback`.

- [ ] Step 1: Baum clean prüfen; `git fetch`; Branch von `origin/main`.
- [ ] Step 2: Akzeptanz: Branchname gemeldet.

### Task G3-2: F3-01 Tools in Whitelist und Frontmatter

**Agent:** developer
**Depends on:** G3-1
**Files:**
- Modify: `config/provider-tools.yaml`, `agents/1-generic/orchestrator.md`
- Modify: `tests/test_subagent_allowlist_frontmatter.py`
**Interfaces:** Produces `SendMessage`/`TaskStop` in der claude-Whitelist und im Template-Frontmatter (Z.7-11), per Capability-Flag; Z.240/273 korrigiert.

- [ ] Step 1: Test (rot): gerenderter Claude-Orchestrator enthält `SendMessage`, `TaskStop`; kein `if provider ==`.
- [ ] Step 2: Whitelist + Frontmatter ergänzen; Text Z.240 (Polling) und Z.273 („no separate kill signal") neu formulieren.
- [ ] Step 3: Test grün; `sync`; ac01-Hash des Orchestrators nur per Eintrag neu pinnen (Änderung beabsichtigt).
- [ ] Step 4: Commit `fix(orchestrator): grant SendMessage and TaskStop tools (#<Iss-3>)`.

### Task G3-3: F3-04 BARRIER / Worker-Contract

**Agent:** developer
**Depends on:** G3-2
**Files:** Modify: `agents/1-generic/orchestrator.md`, `rules/1-generic/a2a-delegation-gates.md`
**Interfaces:** Produces BARRIER-Zustand „Worker ohne Report = failed, neu dispatchen" und einen Satz im Worker-Contract zum Handback-Kanal.

- [ ] Step 1: Test (rot): Template-Assertion auf die neuen Sätze (BARRIER, Worker-Contract).
- [ ] Step 2: Text ergänzen (ein Satz je Stelle, keine neue Struktur).
- [ ] Step 3: Test grün; Render-/Slimming-Pins prüfen, nur beabsichtigte Einträge neu pinnen.
- [ ] Step 4: Commit `fix(orchestrator): treat missing worker report as failed (#<Iss-3>)`.

### Task G3-4: F3-05 + F3-07 Doku-Hinweise

**Agent:** documenter
**Depends on:** G3-3
**Files:** Modify: `rules/1-generic/a2a-delegation-gates.md`, `agents/1-generic/orchestrator.md`
**Interfaces:** Produces zwei Hinweise, ausdrücklich als „laut Anbieterdoku, nicht verifiziert" gekennzeichnet (Hintergrundstart in `-p`/SDK; Tiefe 3, Env-Var `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`).

- [ ] Step 1: Hinweise formulieren (kein Code-Verhalten); K-10 `max_depth` wird in G4 behandelt.
- [ ] Step 2: Akzeptanz: Text enthält Kennzeichnung „unverifiziert"; `consistency-check` rc 0.
- [ ] Step 3: Commit `docs(orchestrator): note unverified background and depth limits (#<Iss-3>)`.

### Task G3-5: Reviewer-Gate G3

**Agent:** code-reviewer
**Depends on:** G3-4
**Files:** keine
**Interfaces:** Consumes Diff.

- [ ] Step 1: Requirement-Treue gegen AC-12, dann Qualität (Provider-Agnostik, Template-Größe).
- [ ] Step 2: Akzeptanz: Verdikt APPROVED oder Findings zurück.

### Task G3-6: PR G3

**Agent:** git
**Depends on:** G3-5
**Files:** keine
**Interfaces:** Produces PR (ohne Merge).

- [ ] Step 1: Push (kein Force), PR mit Body nach Gerüst + G3-Fokus.
- [ ] Step 2: Akzeptanz: PR-URL gemeldet.

### Task G3-7: CI-Watch G3

**Agent:** git
**Depends on:** G3-6
**Files:** keine
**Interfaces:** Consumes `gh pr checks`.

- [ ] Step 1: Checks beobachten, berichten.
- [ ] Step 2: Akzeptanz: alle Checks grün gemeldet; kein Merge.

---

## G4 — DoD-Gating & Spec-Gate (`fix/dod-gating-spec-gate`) — P1/P2

**Reihenfolge:** G4-0 → G4-1 → G4-2 (K-06/K-13) → G4-3 (K-02) → G4-4 (K-03/K-04) → G4-5 (K-05/K-10) → G4-6 (K-01) → G4-7 (K-07) → G4-8 → G4-9 → G4-10.
**Verifikation:** `tests/test_dod_platform_cascade.py`, `tests/test_pipelines.py`, `tests/test_spec_plan_consistency.py`, `tests/test_spec_plan_resolve_enabled.py`, `tests/test_spec_plan_group_consistency.py`, Render-Tests; Orchestrator-/Rule-Pins nur per Eintrag.
**PR-Body-Fokus:** Root cause `dod-presets.yaml:54-55`, `role-defaults.yaml:2640-2696`, `git.md:134`, `tester.md:39-44`; Before = `rapid-prototyping` rendert „No code without tests"; Non-goals = K-07 (aufgeschoben, falls unverhältnismäßig); Could-not-verify = K-07..K-13 nur Audit-Beleg bis Task-Beginn.

### Task G4-0: Issues Iss-4, Iss-5 anlegen

**Agent:** feedback
**Depends on:** G3-7 (Checkpoint G3)
**Files:** keine
**Interfaces:** Produces Issue-Nummern Iss-4, Iss-5.

- [ ] Step 1: Zwei Issues (Englisch) anlegen.
- [ ] Step 2: Akzeptanz: Nummern gemeldet.

### Task G4-1: Branch von `origin/main`

**Agent:** git
**Depends on:** G4-0
**Files:** keine
**Interfaces:** Produces Branch `fix/dod-gating-spec-gate`.

- [ ] Step 1: Baum clean prüfen; `git fetch`; Branch von `origin/main`.
- [ ] Step 2: Akzeptanz: Branchname gemeldet.

### Task G4-2: K-06 + K-13 (ein Key, ein Default)

**Agent:** senior-developer
**Depends on:** G4-1
**Files:**
- Modify: `scripts/lib/dod.py`, `config/dod-presets.yaml`, `.meta-config/project.yaml`, `scripts/lib/config.py`, `scripts/lib/standalone.py`
- Modify: `tests/test_dod_platform_cascade.py`, `tests/test_spec_plan_resolve_enabled.py`
**Interfaces:** Produces einen einheitlichen Spec/Plan-Key (`dod.py:281/374`, `dod-presets.yaml:38,54`, `project.yaml:55-56`) und einen Default für K-13 (`config.py:2337-2338` vs `standalone.py:131-132`); Consumes bestehende Preset-Kaskade.

- [ ] Step 1: K-13 und Key-Verwendung am Code belegen (AUDIT-ONLY), Beleg in den PR; dann Tests (rot): `rapid-prototyping` ⇒ spec-plan-Gate-Wert eindeutig aus einem Key; alter Key-Name wird migriert/gewarnt (Rückwärtskompatibilität prüfen).
- [ ] Step 2: Implementieren; Preset-Text „minimal overhead" (`dod-presets.yaml:46`) konsistent machen.
- [ ] Step 3: Tests grün.
- [ ] Step 4: Commit `fix(dod): use one spec-plan key and one default (#<Iss-4>)`.

### Task G4-3: K-02 Gating der REQ-/Test-Zeilen

**Agent:** developer
**Depends on:** G4-2
**Files:**
- Modify: `agents/1-generic/git.md`, `agents/1-generic/tester.md`, `agents/1-generic/se-developer.md`, `agents/1-generic/se-junior-developer.md`, `agents/1-generic/se-senior-developer.md`, `config/role-defaults.yaml`
- Create: `tests/test_dod_gating_render.py`
**Interfaces:** Produces `{{#if DOD_REQ_TRACEABILITY}}`/`{{#if DOD_TESTS_REQUIRED}}` an den Zeilen `git.md:134`, `tester.md:22,32-43,98,119`, `se-developer.md:98,116`, `se-junior-developer.md:97,137`, `se-senior-developer.md:91`, `role-defaults.yaml:2692-2695`.

- [ ] Step 1: Test (rot): Render mit Preset `rapid-prototyping` enthält keine Pflichtzeilen „No code without tests"/„REQ-ID"; Render mit Preset `strict` (Gegenprobe) enthält sie.
- [ ] Step 2: Gating ergänzen (inline-Marker/Blockform gemäß Regeln; `{{else}}` nicht auf eigener Zeile).
- [ ] Step 3: Test grün; Template-/Render-Pins prüfen (slimming, ac01, compact) und nur beabsichtigte per Eintrag neu pinnen.
- [ ] Step 4: Commit `fix(dod): gate REQ and test duties by preset (#<Iss-4>)`.

### Task G4-4: K-03 + K-04 (Approval-Gate)

**Agent:** developer
**Depends on:** G4-3
**Files:**
- Modify: `config/role-defaults.yaml`, `agents/1-generic/planner.md`, `agents/1-generic/orchestrator.md`
- Modify: `tests/test_pipelines.py`, `tests/test_spec_plan_consistency.py`
**Interfaces:** Produces `approve`-Stage mit `requires_approval` in `feature-lifecycle` (alternativ Routing auf `concept-driven-dev`; Entscheidung dokumentieren) und Planner-Vorbedingung `Status: APPROVED`.

- [ ] Step 1: Tests (rot): `feature-lifecycle` kann nicht ohne Approval-Stage nach `implement`; `planner.md` nennt die Vorbedingung.
- [ ] Step 2: Implementieren (`role-defaults.yaml:2640-2696`, `planner.md`, `orchestrator.md:92-98`); `pipeline_stages`-Mapping für `plan-driven`-Stages nicht brechen.
- [ ] Step 3: Tests grün.
- [ ] Step 4: Commit `fix(pipeline): require approval before feature-lifecycle plan (#<Iss-5>)`.

### Task G4-5: K-05 + K-10

**Agent:** developer
**Depends on:** G4-4
**Files:** Modify: `rules/1-generic/use-orchestrator.md`, `rules/1-generic/spec-plan-workflow.md`, `agents/1-generic/orchestrator.md`, `rules/1-generic/a2a-delegation-gates.md`; Test: `tests/test_spec_plan_group_consistency.py`
**Interfaces:** Produces eine gemeinsame Aussage zu Classify/S-Klasse in drei Stellen; Doku des live `max_depth`-Keys (`config.py:2134-2141` → `A2A_MAX_DEPTH`).

- [ ] Step 1: K-10 am Code belegen (AUDIT-ONLY), Beleg in den PR; Test (rot): die drei Stellen enthalten dieselbe Aussage; `a2a-delegation-gates.md` nennt `max_depth` als live.
- [ ] Step 2: Text angleichen.
- [ ] Step 3: Tests grün.
- [ ] Step 4: Commit `docs(rules): align classify gate wording and max_depth (#<Iss-5>)`.

### Task G4-6: K-01 Drift-Gate (stale Output)

**Agent:** developer
**Depends on:** G4-5
**Files:** Create: `tests/test_generated_output_drift_gate.py`; ggf. Modify: Consistency-Check (nur wenn kein vorhandener Check das abdeckt — vorher Glob/Grep)
**Interfaces:** Produces Drift-Gate (`python scripts/sync.py --check` rc 0 als Test/CI-Prüfung); **kein Edit** an `.claude/`.

- [ ] Step 1: Prüfen, ob `--check` stale Output bereits meldet; Test (rot) mit synthetischem Preset-Wechsel ohne Sync → Drift gemeldet.
- [ ] Step 2: Gate implementieren oder vorhandenen Check anbinden.
- [ ] Step 3: Test grün; lokal `python scripts/sync.py` regeneriert die Ausgabe (nicht committet, da ignoriert).
- [ ] Step 4: Commit `test(sync): gate stale generated output after preset change (#<Iss-4>)`.

### Task G4-7: K-07 Entscheidung (ein REQ-Format)

**Agent:** requirements
**Depends on:** G4-6
**Files:** keine (Entscheidungsvermerk im PR-Body; bei Umsetzung eigene Folge-Issue)
**Interfaces:** Produces Entscheidung „umsetzen" oder „aufschieben" mit Begründung (Aufwand M, `docs/REQUIREMENTS.md:4`, `requirements.md:45-46`, `se-requirements.md:37`, `role-defaults.yaml:2694`, `conventions-presets.yaml:34`).

- [ ] Step 1: Belegen (AUDIT-ONLY), Verhältnismäßigkeit bewerten.
- [ ] Step 2: Akzeptanz: schriftliche Entscheidung mit Begründung; bei „aufschieben" Folge-Issue-Vorschlag an `main_chat`.

### Task G4-8: Reviewer-Gate G4

**Agent:** code-reviewer
**Depends on:** G4-7
**Files:** keine
**Interfaces:** Consumes Diff.

- [ ] Step 1: Requirement-Treue gegen AC-13, dann Qualität (Preset-Kaskade, Rückwärtskompatibilität alter Keys).
- [ ] Step 2: Akzeptanz: Verdikt APPROVED oder Findings zurück.

### Task G4-9: PR G4

**Agent:** git
**Depends on:** G4-8
**Files:** keine
**Interfaces:** Produces PR (ohne Merge).

- [ ] Step 1: Push (kein Force), PR mit Body nach Gerüst + G4-Fokus.
- [ ] Step 2: Akzeptanz: PR-URL gemeldet.

### Task G4-10: CI-Watch G4

**Agent:** git
**Depends on:** G4-9
**Files:** keine
**Interfaces:** Consumes `gh pr checks`.

- [ ] Step 1: Checks beobachten, berichten.
- [ ] Step 2: Akzeptanz: alle Checks grün gemeldet; kein Merge.

---

## G5 — Doku-Drift & Provider-Agnostik (`chore/audit-docs-drift`) — P2/P3

**Reihenfolge:** G5-0 → G5-1 → G5-2 (Belegprüfung) → G5-3 → G5-4 → G5-5 (F-PA1) → G5-6 (F-PA2) → G5-7 → G5-8 → G5-9.
**Verifikation:** Consistency-Check, Link-Check, `tests/test_provider_agnostic_dispatch.py`, Referenz-Tests der umbenannten Funktionen, `--validate`.
**PR-Body-Fokus:** Root cause je Fund `file:line` aus der Tabelle; Non-goals = F-OC2 (Superset bewusst, nur dokumentiert), K-16 (Absicht VERMUTET); Could-not-verify = Funde, die sich beim Belegen als nicht mehr zutreffend erweisen (dann im PR als „verworfen" gelistet).

### Task G5-0: Issue Iss-11 anlegen

**Agent:** feedback
**Depends on:** G4-10 (Checkpoint G4)
**Files:** keine
**Interfaces:** Produces Issue-Nummer Iss-11 (Sammel-Issue, wird in G2/G5/G7 referenziert; falls bereits in G2 angelegt, wiederverwenden).

- [ ] Step 1: Prüfen, ob Iss-11 existiert; sonst anlegen (Englisch).
- [ ] Step 2: Akzeptanz: Nummer gemeldet.

### Task G5-1: Branch von `origin/main`

**Agent:** git
**Depends on:** G5-0
**Files:** keine
**Interfaces:** Produces Branch `chore/audit-docs-drift`.

- [ ] Step 1: Baum clean prüfen; `git fetch`; Branch von `origin/main`.
- [ ] Step 2: Akzeptanz: Branchname gemeldet.

### Task G5-2: Belegprüfung K-08, K-09, K-11, K-12, K-14, K-15, K-16, K-17

**Agent:** developer
**Depends on:** G5-1
**Files:** keine (read-only; Ergebnis als Liste im PR-Body)
**Interfaces:** Produces je Fund „belegt/verworfen" mit `file:line`.

- [ ] Step 1: Jeden Fund am aktuellen Code prüfen (Zeilen laut Tabelle); Ergebnis protokollieren.
- [ ] Step 2: Akzeptanz: acht Verdikte mit Belegen; nur belegte Funde gehen in G5-3.

### Task G5-3: Doku-Fixes

**Agent:** documenter
**Depends on:** G5-2
**Files:** Modify: `.meta-config/project.yaml`, `docs/REQUIREMENTS.md`, `docs/howto/instantiate-project.md`, `agents/1-generic/agent-meta-developer.md`, `config/rules-presets.yaml`, `agents/1-generic/_wf-orchestrator-reference.md`, `config/project-config.schema.json` (nur belegte Funde; Pfade per Glob belegen)
**Interfaces:** Produces Korrekturen für K-08, K-09, K-11, K-12, K-14, K-15, K-16 (Hinweis), K-17.

- [ ] Step 1: Korrekturen für die belegten Funde.
- [ ] Step 2: Akzeptanz: Link-Check/`consistency-check` rc 0; K-09-Beispiel rendert wörtlich `{{VAR}}`.
- [ ] Step 3: Commit `docs: fix audit doc drift (K-08..K-17) (#<Iss-11>)`.

### Task G5-4: F-OC2 + F-OC3 dokumentieren

**Agent:** documenter
**Depends on:** G5-3
**Files:** Modify: `config/ai-providers.yaml` (nur Kommentare), `config/tier-presets.yaml` (nur Kommentare)
**Interfaces:** Produces Kommentar „Superset bewusst" (F-OC2) und „4 von 5 Tiers auf dasselbe Modell" (F-OC3); keine Datenänderung.

- [ ] Step 1: Kommentare ergänzen.
- [ ] Step 2: Akzeptanz: `git diff` zeigt nur Kommentarzeilen; `sync --check` ohne neue Drift.
- [ ] Step 3: Commit `docs(config): document opencode allow-list and tier mapping (#<Iss-11>)`.

### Task G5-5: F-PA1 Rename Opencode-Funktionen

**Agent:** senior-developer
**Depends on:** G5-4
**Files:** Modify: `scripts/lib/cli_commands.py` (Z.324-360) und alle Referenzen (vorher Grep in `scripts/`, `tests/`); Tests der Referenzen
**Interfaces:** Produces provider-neutrale Namen für `_sync_opencode_runtime_gate`, `reconcile_opencode_surface_gate` und weitere Funktionen in Z.324-360; Consumes Referenzliste.

- [ ] Step 1: Referenzen per Grep in Code und Tests listen (Ergebnis in den PR); Charakterisierungstest bzw. bestehende Tests als Rot/Grün-Basis (Rename darf Verhalten nicht ändern).
- [ ] Step 2: Rename + alle Aufrufer/Tests anpassen; keine Alias-Altlasten, außer ein Test importiert öffentlich (dann kurzer Alias mit Entfernungsvermerk).
- [ ] Step 3: Betroffene Tests grün; `--validate`.
- [ ] Step 4: Commit `refactor(sync): rename provider-specific surface gate functions (#<Iss-11>)`.

### Task G5-6: F-PA2 Default und AST-Guard

**Agent:** developer
**Depends on:** G5-5
**Files:** Modify: `scripts/lib/rules.py`, `tests/test_provider_agnostic_dispatch.py`; ggf. `external_tools_drift.py:187-189`, `providers.py:358` (nur wenn Verlagerung nach YAML verhältnismäßig)
**Interfaces:** Produces Default-Entscheidung für `rules.py:478` (`"Opencode"` vs sonst `"Claude"`) und erweiterten Guard für Provider-Literale als Dict-Keys.

- [ ] Step 1: Test (rot): Guard meldet Provider-Namen-Literale als Dict-Keys außerhalb der Allowlist.
- [ ] Step 2: Default prüfen/korrigieren; bekannte Stellen (`external_tools_drift.py`, `providers.py`) in die Guard-Allowlist mit Begründung oder nach YAML verlagern.
- [ ] Step 3: Tests grün.
- [ ] Step 4: Commit `test(sync): extend provider-agnostic guard to dict keys (#<Iss-11>)`.

### Task G5-7: Reviewer-Gate G5

**Agent:** code-reviewer
**Depends on:** G5-6
**Files:** keine
**Interfaces:** Consumes Diff.

- [ ] Step 1: Requirement-Treue gegen AC-14, dann Qualität.
- [ ] Step 2: Akzeptanz: Verdikt APPROVED oder Findings zurück.

### Task G5-8: PR G5

**Agent:** git
**Depends on:** G5-7
**Files:** keine
**Interfaces:** Produces PR (ohne Merge).

- [ ] Step 1: Push (kein Force), PR mit Body nach Gerüst + G5-Fokus.
- [ ] Step 2: Akzeptanz: PR-URL gemeldet.

### Task G5-9: CI-Watch G5

**Agent:** git
**Depends on:** G5-8
**Files:** keine
**Interfaces:** Consumes `gh pr checks`.

- [ ] Step 1: Checks beobachten, berichten.
- [ ] Step 2: Akzeptanz: alle Checks grün gemeldet; kein Merge.

---

## G6 — Gemini-Oberfläche (`fix/gemini-surface-docs`) — P1 nur Doku

**Reihenfolge:** G6-0 → G6-1 → G6-2 → G6-3 → G6-4 → G6-5 → G6-6 → G6-7.
**Verifikation:** `--validate`, `consistency-check`, Provider-Capability-Tests; keine Verhaltensänderung für Gemini-Output ohne Beleg.
**PR-Body-Fokus:** Root cause `ai-providers.yaml` Gemini `agent-discovery:false` vs `provider-capabilities.yaml:288`; **G4-6 REFUTED — bewusst unverändert**; Non-goals = Default-Flip (#854/#860), G4-4/5/7/8/9, F-OC1; Could-not-verify = alle Antigravity-/Gemini-Laufzeitaussagen (WebFetch-Zusammenfassungen, kein agy-Lauf).

### Task G6-0: Issue Iss-6 anlegen

**Agent:** feedback
**Depends on:** G5-9 (Checkpoint G5)
**Files:** keine
**Interfaces:** Produces Issue-Nummer Iss-6 (Ref #854/#860).

- [ ] Step 1: Design-Issue (Englisch) „Gemini target platform: CLI vs Antigravity" anlegen.
- [ ] Step 2: Akzeptanz: Nummer gemeldet.

### Task G6-1: Branch von `origin/main`

**Agent:** git
**Depends on:** G6-0
**Files:** keine
**Interfaces:** Produces Branch `fix/gemini-surface-docs`.

- [ ] Step 1: Baum clean prüfen; `git fetch`; Branch von `origin/main`.
- [ ] Step 2: Akzeptanz: Branchname gemeldet.

### Task G6-2: G4-1 Doku-Hinweis, G4-6 Nicht-Änderung

**Agent:** documenter
**Depends on:** G6-1
**Files:** Modify: `config/provider-capabilities.yaml` (nur Kommentar/Doku-Feld, keine Datenänderung)
**Interfaces:** Produces Hinweis: `.gemini/agents` wird von Antigravity nicht auto-geladen (Zielplattform CLI vs Antigravity), Default-Flip abhängig von agy-Lauf; Vermerk, dass `matcher ""`/`"*"` alle Tools matcht (G4-6 REFUTED).

- [ ] Step 1: Hinweis formulieren, `hooks.json`-Generator unverändert.
- [ ] Step 2: Akzeptanz: `git diff` zeigt nur Kommentar/Doku; `sync --check` ohne Drift; kein `agent-discovery`-Default geändert.
- [ ] Step 3: Commit `docs(gemini): note antigravity agent discovery limit (#<Iss-6>)`.

### Task G6-3: G4-2 + G4-3 Tool-Map / bash_tool_name

**Agent:** developer
**Depends on:** G6-2
**Files:** Modify (nur falls belegt): `config/ai-providers.yaml`, `config/provider-tools.yaml`; Tests: Capability-/Tool-Map-Tests (per Glob belegen)
**Interfaces:** Produces — nur wenn am Code belegbar — Angleichung `bash_tool_name` (`code_execution`) und Tool-Map an die Surface; sonst Eintrag „nicht änderbar ohne agy-Lauf".

- [ ] Step 1: Belegen: Wo wird `bash_tool_name` konsumiert (Guards)? Ergebnis im PR; bei Zweifel → keine Änderung, Aufschub.
- [ ] Step 2: Bei Beleg: Test (rot) → Fix → Test grün; sonst Dokumentationseintrag.
- [ ] Step 3: Commit (nur bei Änderung) `fix(gemini): align bash tool name with tool map (#<Iss-6>)`.

### Task G6-4: Aufschub-Protokoll G4-4/5/7/8/9, F-OC1

**Agent:** documenter
**Depends on:** G6-3
**Files:** Modify: `config/provider-capabilities.yaml` (Verweis auf `surface_verified_state`-Hinweise) bzw. PR-Body
**Interfaces:** Produces je aufgeschobenem Fund eine Begründung (UNVERIFIABLE: extern/agy-Lauf, #854/#860/#1007).

- [ ] Step 1: Liste der Aufschübe mit Grund formulieren.
- [ ] Step 2: Akzeptanz: sechs Einträge (G4-4, G4-5, G4-7, G4-8, G4-9, F-OC1) mit Grund.

### Task G6-5: Reviewer-Gate G6

**Agent:** code-reviewer
**Depends on:** G6-4
**Files:** keine
**Interfaces:** Consumes Diff.

- [ ] Step 1: Requirement-Treue gegen AC-15 (insbesondere: G4-6 unverändert), dann Qualität.
- [ ] Step 2: Akzeptanz: Verdikt APPROVED oder Findings zurück.

### Task G6-6: PR G6

**Agent:** git
**Depends on:** G6-5
**Files:** keine
**Interfaces:** Produces PR (ohne Merge).

- [ ] Step 1: Push (kein Force), PR mit Body nach Gerüst + G6-Fokus.
- [ ] Step 2: Akzeptanz: PR-URL gemeldet.

### Task G6-7: CI-Watch G6

**Agent:** git
**Depends on:** G6-6
**Files:** keine
**Interfaces:** Consumes `gh pr checks`.

- [ ] Step 1: Checks beobachten, berichten.
- [ ] Step 2: Akzeptanz: alle Checks grün gemeldet; kein Merge.

---

## G7 — Token-Diät (`chore/token-diet`) — zuletzt

**Reihenfolge:** G7-0 → G7-1 → G7-2 (Pins vorab) → G7-3 → G7-4 → G7-5 → G7-6 → G7-7 → G7-8 (Pins) → G7-9 → G7-10 → G7-11.
**Verifikation:** `tests/test_context_budgets.py`, `tests/test_template_slimming_equivalence.py`, `tests/fixtures/ac01-baseline/hashes.json`, compact-golden, `tests/test_test_environments_render.py`, `tests/test_release_checklist_render.py`; Messung Orchestrator-Token vorher/nachher (cl100k-Proxy wie im Audit).
**PR-Body-Fokus:** Root cause `agents.py:515` (pretty-JSON), `agents.py:343` (`name_index`), `config.py:1649` (AGENT_TABLE); Before = 11,4k Tok route_intent; After = gemessen; Non-goals = Pipeline-Auslagerung, manager-Skill, Boilerplate-Kürzung (nicht gegengeprüft); Could-not-verify = Claude-Tokenizer (nur Proxy), Plugin-Injektionen. **Memory-Notizen** (außerhalb Repo) → Hinweis an `main_chat`: „~11.8k always-on" widerlegt (7693 Tok), `rules-preset` ist für `lazy` wirksam.

### Task G7-0: Issues Iss-7, Iss-12 anlegen

**Agent:** feedback
**Depends on:** G6-7 (Checkpoint G6)
**Files:** keine
**Interfaces:** Produces Issue-Nummern Iss-7, Iss-12 (Ref #977).

- [ ] Step 1: Zwei Issues (Englisch) anlegen.
- [ ] Step 2: Akzeptanz: Nummern gemeldet.

### Task G7-1: Branch von `origin/main`

**Agent:** git
**Depends on:** G7-0
**Files:** keine
**Interfaces:** Produces Branch `chore/token-diet`.

- [ ] Step 1: Baum clean prüfen; `git fetch`; Branch von `origin/main`.
- [ ] Step 2: Akzeptanz: Branchname gemeldet.

### Task G7-2: Pins vorab prüfen und Messbasis

**Agent:** tester
**Depends on:** G7-1
**Files:** keine (read-only; Ergebnis im PR-Body)
**Interfaces:** Produces Ausgangsstand der Pins und Token-Messung (Orchestrator-Render, AGENTS.md, `branch-guard.md`).

- [ ] Step 1: Seriell ausführen: `tests/test_context_budgets.py`, `tests/test_template_slimming_equivalence.py`, ac01-/compact-golden-Tests, `test_test_environments_render.py`, `test_release_checklist_render.py` → Basisstand dokumentieren.
- [ ] Step 2: Token-Basismessung (Bytes + cl100k-Proxy) für `route_intent`-Block, `AGENTS.md`, `branch-guard.md`.
- [ ] Step 3: Akzeptanz: Tabelle „Pin | Ausgangsstand | rot/grün" und Basis-Token liegen vor.

### Task G7-3: T-1 route_intent kompakt, name_index entfernen

**Agent:** developer
**Depends on:** G7-2
**Files:** Modify: `scripts/lib/agents.py`; Tests: `tests/test_context_budgets.py` und route_intent-Tests (per Grep belegen)
**Interfaces:** Produces `json.dumps(..., separators=(',',':'))` (`agents.py:515`), `name_index` nicht mehr serialisiert (`agents.py:343`; Verbrauch `:582` bleibt).

- [ ] Step 1: Test (rot): gerenderter Orchestrator enthält kein `name_index` und kein Pretty-Printing; Routing-Funktion funktioniert weiter (Verbrauch `:582`).
- [ ] Step 2: Implementieren.
- [ ] Step 3: Tests grün; Orchestrator-Pins (ac01, slimming, compact) bewusst per Eintrag neu pinnen.
- [ ] Step 4: Commit `perf(agents): compact route_intent json and drop name_index (#<Iss-7>)`.

### Task G7-4: T-3 AGENTS.md AGENT_TABLE per Flag

**Agent:** developer
**Depends on:** G7-3
**Files:** Modify: `scripts/lib/config.py`, `templates/configs/AGENTS.project-template.md`; Tests: `tests/test_context_budgets.py`
**Interfaces:** Produces Flag für den AGENT_TABLE-Block (`config.py:1649`); Default bleibt rückwärtskompatibel (Entscheidung im PR, Default-Wert begründet).

- [ ] Step 1: Test (rot): Flag aus ⇒ kein Block; Flag an ⇒ byte-identisch zu heute.
- [ ] Step 2: Implementieren inkl. Conditional-Registrierungen (analog Flag-Registrierungen in `variables.py`/`standalone.py`, falls Platzhalter-Flag).
- [ ] Step 3: Tests grün; Pins per Eintrag.
- [ ] Step 4: Commit `perf(config): make AGENTS.md agent table optional (#<Iss-7>)`.

### Task G7-5: T-4 branch-guard.md auslagern

**Agent:** documenter
**Depends on:** G7-4
**Files:** Modify: `rules/1-generic/branch-guard.md`; Create: `docs/concepts/branch-guard-terminology.md`
**Interfaces:** Produces Kurzfassung in der Rule (Verweis auf `docs/concepts/…`) und ausgelagerte Abschnitte „Guard-Terminologie" und „Bekannte Grenzen". Der Anker `branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary` wird von Hooks/Rules zitiert — Verweise vorher greppen und anpassen oder Anker-Zeile behalten.

- [ ] Step 1: Referenzen auf den Anker per Grep listen; Test (rot): Link-/Consistency-Check findet keinen toten Anker.
- [ ] Step 2: Abschnitte verschieben; Kurzfassung (3–5 Zeilen: Convention vs Security boundary) bleibt in der Rule.
- [ ] Step 3: Tests grün; `test_context_budgets.py` zeigt Senkung.
- [ ] Step 4: Commit `docs(rules): move branch-guard details to concept doc (#<Iss-7>)`.

### Task G7-6: Backup-Prune `*.sync-backup-*`

**Agent:** developer
**Depends on:** G7-5
**Files:** Modify: `scripts/lib/generated_file_drift.py`; Create: `tests/test_sync_backup_prune.py`
**Interfaces:** Produces Prune-Logik für `*.sync-backup-*` im Ausgabeverzeichnis (`generated_file_drift.py:152-207`); Zahlendiskrepanz 168 vs 226 vorher klären.

- [ ] Step 1: Test (rot): Dateien `*.sync-backup-*` werden gemäß Regel (z.B. älter als N oder nur letzte) entfernt, Nicht-Backups bleiben; `--check` löscht nichts.
- [ ] Step 2: Implementieren; Regel im PR begründen.
- [ ] Step 3: Test grün.
- [ ] Step 4: Commit `chore(sync): prune stale sync backup files (#<Iss-12>)`.

### Task G7-7: F6-11 `hook_json_get` Single-Parse (Entscheidung + ggf. Umsetzung)

**Agent:** senior-developer
**Depends on:** G7-6
**Files:** Modify (nur bei Umsetzung): `hooks/1-generic/lib/hook_common.sh`; Tests: bestehende Hook-Tests
**Interfaces:** Produces entweder Single-Parse aller Felder in einem Python-Aufruf oder dokumentierten Aufschub (Aufwand M).

- [ ] Step 1: Latenz vorher messen (Audit: ~0,35 s Bash-Call, 22 Spawns über alle Guards).
- [ ] Step 2: Entscheidung: Umsetzung nur, wenn alle Hook-Tests unverändert grün bleiben und Messung Verbesserung zeigt; sonst aufschieben mit Begründung im PR.
- [ ] Step 3: Bei Umsetzung Commit `perf(hooks): parse hook json fields in one call (#<Iss-11>)`.

### Task G7-8: Pins bewusst neu erzeugen

**Agent:** tester
**Depends on:** G7-7
**Files:** Modify: `tests/fixtures/ac01-baseline/hashes.json`, slimming-golden, compact-golden, ggf. `tests/test_context_budgets.py`, `tests/test_test_environments_render.py` (Hash + Versionspins 1.3.3 nur falls betroffen)
**Interfaces:** Produces per Eintrag neu gepinnte Hashes für beabsichtigte Änderungen; Consumes Pin-Tabelle aus G7-2.

- [ ] Step 1: Jeden roten Pin einer beabsichtigten Änderung (G7-3/4/5) zuordnen; unerklärte Abweichungen → Rückgabe an Orchestrator, **kein** Neupinnen.
- [ ] Step 2: Per Eintrag neu pinnen (kein `--write`-Sammellauf).
- [ ] Step 3: Akzeptanz: alle Pin-Tests grün; Token-Nachmessung (Vorher/Nachher) im PR.
- [ ] Step 4: Commit `test: rebaseline context pins after token diet (#<Iss-7>)`.

### Task G7-9: Reviewer-Gate G7

**Agent:** code-reviewer
**Depends on:** G7-8
**Files:** keine
**Interfaces:** Consumes Diff.

- [ ] Step 1: Requirement-Treue gegen AC-16, dann Qualität (Routing-Funktion intakt, Pins erklärt, Default des Flags rückwärtskompatibel).
- [ ] Step 2: Akzeptanz: Verdikt APPROVED oder Findings zurück.

### Task G7-10: PR G7

**Agent:** git
**Depends on:** G7-9
**Files:** keine
**Interfaces:** Produces PR (ohne Merge).

- [ ] Step 1: Push (kein Force), PR mit Body nach Gerüst + G7-Fokus (inkl. Memory-Hinweis als „Follow-up für main_chat", nicht im Repo).
- [ ] Step 2: Akzeptanz: PR-URL gemeldet.

### Task G7-11: CI-Watch G7

**Agent:** git
**Depends on:** G7-10
**Files:** keine
**Interfaces:** Consumes `gh pr checks`.

- [ ] Step 1: Checks beobachten, berichten.
- [ ] Step 2: Akzeptanz: alle Checks grün gemeldet; kein Merge.

---

## Self-Review

- Jeder Task mappt auf genau eine Rolle aus {`feedback`, `git`, `developer`, `senior-developer`, `tester`, `documenter`, `requirements`, `code-reviewer`}; CI-Watch ist der Rolle `git` zugeordnet (kein eigener CI-Watcher-Agent im Repo, `agents/1-generic/` enthält keinen).
- Kein Task ist in einer `parallel_group`: alle Tasks sind seriell, Dateiüberlappungen (z.B. `orchestrator-guard-impl.sh` in G1-2..G1-6, `cli_commands.py` in G2-4/G2-5) sind damit unkritisch.
- Jedes Akzeptanzkriterium ist beobachtbar (Testname + rot/grün, rc, Branchname, PR-URL, `git diff`-Inhalt).
- `Files:`/`Interfaces:` je Task vorhanden; Pfade, die der Plan nicht aus dem Audit kennt, sind als „per Glob belegen" gekennzeichnet (kein Raten).
- Frontmatter `pipeline_stages` ist vorhanden (`implement: 1`).
- **Task-Zählung:** G1 = 10, G2 = 11, G3 = 8, G4 = 11, G5 = 10, G6 = 8, G7 = 12 → 70.
- Abdeckung: F1–F11, K-01..K-17, F3-01..07, G4-1..9, F-OC1..3, F-PA1/2, F6-01..13, Token-Funde, 12 Issues stehen in der Tabelle bzw. im Issue-Abschnitt; nicht Teil des Plans: Token-Funde T-2/T-5/T-7..T-10 (nicht gegengeprüft, ausdrücklich zurückgestellt).

## Annahmen

1. Der Audit-Stand `09925d20` ist Basis; vor jeder Gruppe wird von aktuellem `origin/main` abgezweigt, Zeilennummern können sich verschieben (Fix per Symbol/`file:symbol` statt blindem Zeilenbezug).
2. Die Fundbelege stammen aus Agentenberichten; was nicht gegengeprüft wurde (K-07..K-17, G4-9), wird zu Beginn des jeweiligen Tasks am Code belegt — falsche Funde werden verworfen, nicht „angepasst".
3. Provider ohne `agent_id` (Gemini) lässt sich über ein Capability-Flag abbilden (F6-05); falls nicht, wird der Task neu geschnitten.
4. Hook-Quellpfade `hooks/1-generic/…` sind maßgeblich; die graphify-Guards liegen ggf. unter `hooks/0-external/` (per Glob zu belegen).
5. Es gibt keinen dedizierten CI-Watcher-Agenten; `git` ruft `gh pr checks` nur lesend auf.
6. `gh` ist installiert, aber nicht im `$PATH` (`/home/hermes/.local/bin/gh`).

## Re-planning

Nach jeder Gruppe (Checkpoint): Gelten die Annahmen noch? Sind neue Funde/Issues dazugekommen (z.B. durch die zweite Session)? Stimmt die Reihenfolge noch (insbesondere G7 nach G1..G6, weil G7 Pins neu erzeugt)? Plan aktualisieren, nicht als eingefroren behandeln. Bei rotem CI oder Reviewer-Cap (`task-review.max-rounds: 4`) bleibt der Stand offen und wird an `main_chat` gemeldet.

## Ausführungsnachweis (Ledger)

Wird vom Ledger-Writer (`scripts/lib/plan_ledger.py --update-plan-ledger`) nach jedem Task fortgeschrieben; Checkboxen oben sind die menschlich lesbare Sicht, der Checkpoint (`CheckpointStore`) die Recovery-Quelle.

| Gruppe | Branch | Issue-Nummern | PR | Status |
|---|---|---|---|---|
| G1 | `fix/hooks-containment-allowlist` | Iss-2, Iss-8, Iss-10 | — | geplant |
| G2 | `fix/sync-robustness-exit-codes` | Iss-1, Iss-9 (+ Iss-11) | — | geplant |
| G3 | `fix/orchestrator-tools-handback` | Iss-3 | — | geplant |
| G4 | `fix/dod-gating-spec-gate` | Iss-4, Iss-5 | — | geplant |
| G5 | `chore/audit-docs-drift` | Iss-11 | — | geplant |
| G6 | `fix/gemini-surface-docs` | Iss-6 | — | geplant |
| G7 | `chore/token-diet` | Iss-7, Iss-12 | — | geplant |
