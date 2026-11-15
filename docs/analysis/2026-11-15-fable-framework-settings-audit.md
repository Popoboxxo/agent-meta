# Framework-Settings-Audit agent-meta — 2026-11-15 (Fable)

- **Status:** Analyse (kein Beschluss)
- **Datum:** 2026-11-15
- **Quelle:** Fable/Opus-Audit, Verifikationsstand siehe Verifikationsbericht (docs/analysis/2026-11-15-fable-verification-of-unchecked.md)
- **Modellherkunft:** Fable
- **Issues:** #1237–#1276 (Audit-Folgeissues)
- **Zugehörige Berichte:** docs/analysis/2026-11-15-fable-framework-settings-audit.md, docs/analysis/2026-11-15-fable-language-feature-audit.md, docs/analysis/2026-11-15-fable-orchestration-rollout-audit.md, docs/analysis/2026-11-15-fable-verification-of-unchecked.md

> Read-only-Analyse. Stand: `origin/main` (Checkout-Branch `chore/main-checkout-parking`, HEAD 5e16ecf8).
> Auftrag 1/3: Einstellungen des Agent-Meta-Frameworks für dieses Repo + Priorisierung der Feature-Requests.
> Status: **ABGESCHLOSSEN** (2026-11-15).

## 0. Kontext / Arbeitsstil dieses Repos (Ist-Befund)

- Framework-Repo, das sich selbst konsumiert (`project.yaml:206-210`); 458 Test-Dateien / **126.031 LOC** Tests (`find tests -name '*.py'`), CI mit pytest-Sharding (`.github/workflows/orchestration-test.yml`), `validate.yml` mit `--fail-on-p0`, `--validate`, Szenario-Harness.
- Gelebter Workflow: Spec/Plan-Gate explizit an (`project.yaml:55-56`), PR-Pflicht + Branch-Guard, Golden-/AC-01-Baselines je Provider, Issues mit Label-Taxonomie, 107 offene Issues.
- Always-on-Kontext Claude (gemessen, Bytes/4): CLAUDE.md 5.358 B + 10 Rules 8.117 B + 58 Agent-Descriptions 5.133 B + 25 Skill-Descr. 3.568 B + 24 Command-Descr. 2.141 B ≈ **24,3 KB ≈ 6,1k Tok je Nachricht und je Subagent-Spawn** (.tmp/plans/2026-11-14-agent-improvement-loop-plan.md:55). Memory 2026-08 (tiktoken): 11,8k bei 22 Rules.
- Orchestrator-Render 32 KB (~8k Tok), davon route_intent-JSON 32,8 KB-Sektion (`...-loop-plan.md:49`); Roster gesamt 58 Dateien 552 KB (~138k Tok lazy).
- Konfig-Datei `.meta-config/project.yaml` (407 Zeilen, Version 2.0.0-beta.8); 5 `.bak`-Kopien liegen daneben (Admin-UI-Saves 2026-11-10).

## A. Einstellungs-Audit

Legende: **Ist** → **Empf.** (behalten/ändern/aus) · Wirkung (T=Tokens, Q=Qualität, R=Risiko) · Beleg · Aufwand S/M/L.

### A.1 DoD / Qualitäts-Flags (Preset, Tests, REQ, Overview, Security)

| Einstellung | Ist | Empf. | Wirkung | Beleg | Aufw. |
|---|---|---|---|---|---|
| `dod-preset` | `rapid-prototyping` → tests-required/req/overview/security/root-cause **alle false**, release-gates aus | **ändern** → `spec-optional` (tests-required true, Rest false) oder `rapid-prototyping` + `dod: {tests-required: true}` | Q↑: 126k Test-LOC + CI-Pflicht werden heute von keinem DoD-Flag gespiegelt; `validator`/`tester` sehen „Tests: false“ und dürfen Tests überspringen. R: Widerspruch Preset ↔ CI (CI blockt, DoD nicht). T: ±0 (ein Flag im Header) | `project.yaml:10`; `config/dod-presets.yaml:54-68`; CLAUDE.md Header „Tests: false“; `TEST_COMMANDS` enthält pytest (`project.yaml:200`) | S |
| `tests-required: false` | implizit via Preset | **ändern → true** (siehe oben) | Q↑ hoch; Rebaseline: CLAUDE.md/AGENTS.md-Header, Golden-Dateien aller 3 Provider | `config/dod-presets.yaml:56` | S (Flag) / M (Golden-Rebaseline) |
| `req-traceability: false` | Preset | **behalten** | Repo hat keine REQ-IDs im Code; `docs/REQUIREMENTS.md` wird nicht gelebt (REQ_CATEGORIES nur Deko, `project.yaml:259-262`). T-Spareffekt: REQ-Blöcke in Rollen entfallen | `dod-presets.yaml:55` | – |
| `codebase-overview: false` | Preset | **behalten** | `docs/CODEBASE_OVERVIEW.md` existiert (2000+ Zeilen) und wird manuell/per `/doc-now` gepflegt — Pflicht-Update je Task wäre Token-Fresser | `dod-presets.yaml:57`; `/doc-now`-Skill vorhanden | – |
| `security-audit: false`, `ai-security-review: false` | Preset | **behalten**, Security über `security-paved-roads`-Skill (lazy) | Framework ohne Runtime-Angriffsfläche; Hook-Skripte sind Convention-Boundary. Hinweis: `security-auditor`-Rolle **nicht** in `roles:` aktiv, Skill `threat-model-4-questions` existiert als Lazy-Skill | `project.yaml:385-394` | – |
| `root-cause-required: false` | Preset | **ändern → true** (per `dod:`-Override) | Q↑: Repo hat Bugfix-Batches (#1246, #1252, #1258 …) mit Regressionen; `systematic-debugging`-Skill existiert bereits; Kosten gering | `dod-presets.yaml:63` | S |
| `spec-plan-workflow.enabled: true` | explizit (überschreibt Preset-`spec-plan-required: false`) | **behalten** | Gelebt (docs/plans/, docs/specs/, Archive-Modus `ask`). Inkonsistenz: Preset sagt „minimal overhead“, Repo lebt L/XL-Specs → weiteres Argument für Preset-Wechsel | `project.yaml:55-79`; `dod-presets.yaml:4-10` | – |
| `spec-plan-workflow.index.mode: knowledge-engine` | aktiv | **ändern → `fallback-index`** falls KE aus (A.4) | Kopplung: Spec/Plan-Index hängt an KE | `project.yaml:68-70` | S |
| `release-gates` (artifact-freshness, docker-image-scan, action-pin-validation) | aus via Preset | **teilweise ändern**: `action-pin-validation: true` | Q/R: CI-Workflows nutzen GitHub Actions; Scorecard-Workflow existiert (`.github/workflows/scorecard.yml`) → Pin-Validation passt; docker/artifact bleiben aus (kein Build-Artefakt) | `dod-presets.yaml:65-68` | S |
| `release-checklist` | **Key fehlt** → mode effektiv `off` | **ändern → `advisory`** mit 3-4 Items (sync --check, pytest, CHANGELOG, VERSION) | Q↑ für Releases; `VERSION_DIST_BEHAVIOUR` beschreibt 4 Schritte nur als Prosa (`project.yaml:286-287`); `/release-check`-Skill ohne Items leer | Schema `config/project-config.schema.json:1654-1670`; `project.yaml` kein Key | M |

### A.2 Speech-Mode / Rules / Context-Profile / Token-Budget

| Einstellung | Ist | Empf. | Wirkung | Beleg | Aufw. |
|---|---|---|---|---|---|
| `speech-mode: short` | aktiv, Rule 627 B | **behalten** | T: minimal; Q: passt zum Nutzer-Stil (Bullet-Points) | `project.yaml:176`; .claude/rules/speech-mode.md | – |
| `rules-preset: lazy` | 7 Kernregeln always-on, 18 Lazy-Skills | **behalten**, aber **Kernregeln kürzen** | Gemessen: Rules → Skills senkt always-on 9.421 → 4.294 Tok (−54 %) (Memory 2026-08); heute 10 Rules = 8.117 B. Größte: `branch-guard.md` 1.984 B (davon ~1.300 B „Bekannte Grenzen“-Prosa = Doku, keine Anweisung), `use-orchestrator.md` 1.539 B, `use-lazy-rules.md` 1.206 B (Tabelle dupliziert Skill-Descriptions, die ohnehin im System-Prompt stehen) | `wc -c .claude/rules/*.md`; `config/rules-presets.yaml:102-122`; `...-loop-plan.md:55-56` | S (Template-Kürzung, Rebaseline Golden) |
| `use-lazy-rules.md` als Always-on-Rule | 1.206 B | **aus** (Rule entfernen, Skills triggern über Description) | T: −0,3k Tok je Nachricht+Spawn; R: gering — Claude lädt Skills über Description; für Opencode/Gemini ohne Skill-Kanal Rule behalten (Capability-Flag) | .claude/rules/use-lazy-rules.md; `rules-presets.yaml:102-109` | S |
| `branch-guard.md` „Bekannte Grenzen“-Abschnitt | ~1.300 B Hook-Limitationen in einer Always-on-Rule | **ändern**: in `docs/concepts/` bzw. Skill verlagern, Rule auf 3 Zeilen | T: −0,3k Tok; Q: unverändert (Grenzen sind Doku, nicht Verhalten) | .claude/rules/branch-guard.md:19-30 | S |
| `context-profile` | **Key fehlt** → `full` (compact „opt-in and unverified“) | **noch behalten (full)**, erst nach #977/#1244-Arbeiten `compact` testen | T: potenziell −30 % Roster; R: Schema markiert compact als unverifiziert; Tests `test_context_compact_mode.py` existieren → Spike S | Schema `project-config.schema.json:2842-2849` | S (Spike) / M (Rollout) |
| `context_file.mode: compact`, `max_lines: 250`, `oversize_acknowledged: true` | AGENTS.md 308 Zeilen (16,9 KB ≈ 4,2k Tok), Oversize bewusst quittiert | **ändern**: Agent-Directory als Einzeiler (H6 im Loop-Plan), dann `oversize_acknowledged` entfernen | T: −1,2k Tok always-on für Opencode/Gemini; Compact-Target ≤ 12 KB (`test_context_budgets.py`) | `project.yaml:299-307`; `...-loop-plan.md:57,105` | M (Template) |
| Agent-Descriptions (58 × Ø 88 B) | 5.133 B always-on | **ändern**: ≤ 160 Zeichen je Rolle (H5) **+ Rollenzahl senken** (A.3) | T: −0,3k (H5) bzw. −1,4k (Rollen 58→~30) je Nachricht/Spawn | `...-loop-plan.md:104`; Memory-Hebel 3 | S / M |
| Skill-Descriptions (25) + Command-Descriptions (24) | 3.568 + 2.141 B | **ändern**: 24 Commands auf ~12 prüfen (`what-is`, `open-docs`, `test-orchestration`, `analysis` [analysis.enabled false!], `admin`, `set-preset`, `set-release-checklist` selten gebraucht) | T: −0,3k always-on; R: gering (Commands bleiben als Datei abrufbar, wenn Framework „command-channel off“ unterstützt — **nicht geprüft**) | `ls .claude/commands`; `project.yaml:342-343` | S |

**Gesamt-Hebel A.2 (Schätzung, Bytes/4):** Rules −0,6k, Descriptions −1,7k (mit Rollenreduktion), Commands −0,3k → always-on ≈ 6,1k → ~3,5k Tok je Nachricht **und** je Spawn; bei ~40 Spawns/Session ≈ 100k Tok gespart (Schätzung, nicht gemessen).

### A.3 Rollen / Provider / Orchestrator-Topologie / Pipelines

| Einstellung | Ist | Empf. | Wirkung | Beleg | Aufw. |
|---|---|---|---|---|---|
| `roles:` (58 aktiv) | 58 Rollen gerendert (`ls .claude/agents` = 58) | **ändern → ~30** | T: −1,4k always-on je Nachricht/Spawn (Memory-Hebel 3: 50→12 = −913 always-on, −1480 System-Prompt), Lazy-Roster −~250 KB; Q: Routing-Enum kleiner → route_intent-JSON schrumpft mit (#1161) | `project.yaml:91-150`; `...-loop-plan.md:41,49` | S (Liste) / M (Golden-Rebaseline) |
| Kandidaten **aus** (0 Nutzen für Python-CLI-Framework-Repo): `ui-ux-designer`, `design-system-architect`, `frontend-component-engineer`, `accessibility-specialist`, `api-specialist`, `data-engineer`, `docker` (DOCKER_STACKS_OVERVIEW „kein Docker-Stack“), `e2e-tester` (Playwright nur für Admin-UI-Audit → punktuell), `incident-responder`, `app-lifecycle-governor`, `product-manager`, `export-manager` (se-export, SE aus), `se-component-requirements` (SE aus), `performance-optimizer`, `intern-developer` (Gag) | 15 Rollen | **aus** | Mention-Proxy in Plänen/Conclusions: export-manager 2, design-system-architect 2, performance-optimizer 2, knowledge-querier 1, knowledge-indexer 1 (**schwacher Proxy**: zählt auch Erwähnungen als Bau-Objekt) | `grep`-Zählung docs/plans + knowledge/sources/docs/conclusions + .tmp/plans | S |
| Kandidaten **zusammenlegen**: `claude/gemini/opencode/continue/copilot/mammouth-expert` (6 Rollen, je ~5 Mentions) | 6 Provider-Experten aktiv, davon 3 für Provider, die hier nicht aktiv sind (Continue, Copilot, Mammouth) | **ändern**: nur Experten der aktiven Provider (claude, opencode, gemini) behalten; Rest aus | T: −0,3k always-on; Q: ±0 | `project.yaml:6-9` vs. `:119-123,135` | S |
| Kandidaten **prüfen**: `knowledge-*` (7 Rollen) → siehe A.4; `requirements` (REQ-Traceability aus), `effort-estimator` (39 Mentions, meist als Pipeline-Stage), `bug-feature-analyzer`, `log-analyzer`, `technical-writer`, `refactoring-specialist`, `dependency-auditor` | 14 Rollen | Einzelfall | — | — | S |
| `ai-providers: [Claude, Opencode, Gemini]` | 3 aktiv; `.continue/` liegt untracked und **nicht** gitignored im Repo trotz Continue inaktiv | **behalten** (3); `.continue/` aufräumen; `provider-options` für Continue/Copilot/Mammouth/Codex/KimiCode/ZCode (`:165-175`) sind Leerblöcke → entfernen | T: ±0; R: Verwirrung/Drift (`gitignore.ignore-provider-dirs: true` greift für `.continue` nicht — **nicht geprüft warum**) | `project.yaml:6-9,162-175`; `git check-ignore .continue` = NOT ignored | S |
| Gemini als Provider | aktiv, aber #1160 (Zielplattform unklar), #854/#860 (Antigravity blocked) | **behalten mit Fragezeichen**: nur falls Gemini-CLI real genutzt wird; sonst aus (Golden-Pflege −1/3) | T: Rebaseline-Aufwand je Änderung −33 %; R: Provider-Agnostik-Tests brauchen ≥2 Provider → Opencode reicht | Issues #1160, #854, #860 | S |
| `orchestrator.topology: subagent`, `mode: strict`, `strict: true`, `variables.ORCHESTRATOR_STRICT: true`, `UNKNOWN_FALLBACK_*` doppelt | **dreifach redundante** Strict-Angabe + Fallback-Flags doppelt (`variables` + `orchestrator.unknown-fallback`) | **ändern**: Variablen-Duplikate entfernen (sofern sync sie aus `orchestrator:` ableitet — **nicht geprüft**) | R: Drift-Quelle; T: 0 | `project.yaml:279-282,308-324` | S |
| `orchestrator.delegation.max_depth: 10` | 10 | **ändern → 3–4** | R: A2A-Gates (Skill `a2a-delegation-gates`) begrenzen Tiefe; 10 ist faktisch „kein Limit“; Opencode `experimental-subagent-depth: 3` → inkonsistent | `project.yaml:172,323-324` | S |
| `orchestrator.topology: subagent` | Main-Chat spawnt Orchestrator; Rule „Main Chat darf nicht editieren“ | **behalten**; `primary` erst nach #1176 (Orchestrator beendet Turn bei async Subagents) | Q: bekannter Handback-Bug #1176 | `use-orchestrator.md`; #1176 | – |
| `max-parallel-agents: 4` | 4 | **behalten** | passt zu CI-/Golden-Last | `project.yaml:298` | – |
| `checkpointing: true` | an; kein Checkpoint-Verzeichnis gefunden (`.claude/checkpoints`, .tmp/checkpoints fehlen) | **prüfen** ob wirksam (`/checkpoint`-Skill) | **nicht verifiziert** | `project.yaml:316` | S |
| `quality-pipelines`: `feature-lifecycle` default aktiv, `se-cascade` aus, `custom-pipelines: {}` | Default | **behalten**; Pipeline-Stage-Detail im Orchestrator als Tabelle rendern (H2) | T: −5k je Orchestrator-Spawn (H2) | `project.yaml:344-348`; `role-defaults.yaml:2639` | M (Template) |
| `reflection-pairs.dev-review-loop.max_iterations: 5` | 5 | **ändern → 3** | T/R: 5 Dev↔Review-Runden = teuerster Loop; ab Runde 3 Eskalation an senior/principal sinnvoller | `project.yaml:361-365` | S |
| `tier-preset: Normal`, `model-inherit-main-chat: {Opencode: true, Claude: false}`, `model-source-preference: modelsdev` | Default | **behalten** | – | `project.yaml:357-381` | – |
| `test-repo: enabled: true, path: ../agent-meta-test` | **Pfad existiert nicht** | **ändern → false** oder Pfad anlegen | R: Skills/Checks, die `AGENT_META_TEST_REPO` erwarten, laufen ins Leere | `project.yaml:294-297`; `ls ../agent-meta-test` fehlt | S |
| `systems-engineering.enabled: false`, `se-export`, `se-focus`, `SE_BASE_DIR`, `se-component-requirements`-Rolle, 3 `se-cascade-*`-Skills (lazy) | SE aus, aber SE-Artefakte konfiguriert | **ändern**: `se-export`, `SE_BASE_DIR`, SE-Rolle, SE-Skills entfernen (sofern sync sie nicht automatisch aus Kaskaden-Flag ableitet — **nicht geprüft**) | T: −3 Skill-Descriptions (~0,2k) + 1 Rolle; R: Verwirrung | `project.yaml:12-13,148,288-291,382` | S |

### A.4 Knowledge Engine

| Einstellung | Ist | Empf. | Wirkung | Beleg | Aufw. |
|---|---|---|---|---|---|
| `knowledge-engine.enabled: true`, domain `internal-docs` | 211 Dateien / 3,5 MB; Wiki 119 Dateien, letzte Änderung **2026-11-12**, `log.md` 33 Zeilen; `sources/` = Kopien von README/CHANGELOG/ARCHITECTURE/docs (91 Dateien = Duplikat des Repos) | **ändern → aus** oder auf „Query-only“ zurückfahren (1 Rolle `knowledge-querier` statt 7) | T: CLAUDE.md-KE-Block 1.593 B (~0,4k) always-on + 7 Rollen-Descriptions (~0,6k) + 7 Rollen im Routing-Enum; Q: Wiki hinkt (Audit-Top5-Plan Task 3 „KE-Lint“ offen); R: Doppelpflege Sources ↔ Repo-Doku | `project.yaml:14-54`; `find knowledge -type f`; `git log -1 knowledge/wiki` | S (Flag) / M (Rollen + Spec/Plan-Index auf `fallback-index`) |
| `okf.enforce-frontmatter: true`, Lint-Checks 5, `lint.schedule: post-ingest` | konfiguriert, kein Hinweis auf regelmäßigen Lauf | **behalten falls KE bleibt**; Lint-Lauf als Task im Audit-Top5-Plan | – | `project.yaml:18-44` | – |
| `search.engine: index-only`, `mcp-server: ''` | kein Suchserver | **behalten** (graphify deckt Code-Fragen) | – | `project.yaml:49-51` | – |
| `migration.*` | Einmal-Konfiguration | **aus/entfernen** nach erfolgter Migration | T: 0, Konfig-Rauschen | `project.yaml:45-48` | S |
| Kopplung `spec-plan-workflow.index.mode: knowledge-engine` | KE-Index trägt Spec/Plan-Index | bei KE-aus → `fallback-index: docs/INDEX.md` | Q: docs/INDEX.md muss existieren (**nicht geprüft**) | `project.yaml:68-70` | S |

**Netto-Bewertung KE:** Für ein Framework-Repo, dessen Doku bereits in `docs/` + `CODEBASE_OVERVIEW.md` + graphify (36.886 Knoten) liegt, ist das Wiki eine dritte Kopie; Nutzen (Query mit Citations) steht gegen ~1k Tok always-on + 7 Rollen + Pflegeaufwand. Empfehlung: **aus**, Wiki-Inhalte (Conclusions) nach `docs/` zurückführen — oder Minimalbetrieb mit `knowledge-querier` + `knowledge-ingestor` (2 statt 7 Rollen), falls Query-Funktion gewünscht.

### A.5 Hooks / Containment / Strict-Mode / auto_commit

| Einstellung | Ist | Empf. | Wirkung | Beleg | Aufw. |
|---|---|---|---|---|---|
| PreToolUse-Hooks: graphify-read-guard (Read\|Glob), graphify-search-guard (Bash\|Grep), dod-push-check (Bash), orchestrator-guard (*), repo-containment (*) | 5 Hooks, 5.315 Shell-Zeilen; 9–11 Python-Spawns je Bash-Call (#1169) | **behalten**, Latenz-Issue #1169 priorisieren (Single-Parse) | Q: Convention-Boundary funktioniert; T: Hook-„additional context“ wird je Tool-Call injiziert (graphify-MANDATORY-Zeile ~40 Tok × jeden Read/Bash) → kleiner, aber stetiger Kontext-Kostenfaktor | .claude/settings.json; #1169 | M (Code) |
| `hooks.graphify-read-guard/search-guard: enabled: true` | MANDATORY-Hinweis bei jedem Read/Grep/Bash, auch nach erfolgter graphify-Query | **ändern**: Hinweis nur beim ersten Treffer je Session oder nur bei Grep über `scripts/` (Capability im Hook) | T: −40 Tok × ~100 Calls/Session ≈ 4k Tok; Q: ±0 | `project.yaml:158-161`; Hook-Output in dieser Session (jeder Bash-Call) | S |
| `graphify-out/` 290 MB im Repo-Verzeichnis | nicht in `.tmp` | **prüfen**: gitignored? (**nicht geprüft**); ggf. in .tmp/graphify-out verlagern (tmp-sink) | R: Containment-Konsistenz | `du -sh graphify-out` | S |
| `repo_containment.enabled: true`, `tmp-sink: .tmp`, `cleanup: manual`, system-temp-exception pytest | .tmp/ = **1.006 MB**, 666 Einträge; Pytest-Basetemp extern (`/var/tmp/hermes/pytest-agent-meta`) | **ändern**: `cleanup: on-session-end` o.ä. falls unterstützt (**nicht geprüft**), sonst Aufräum-Task; Exception behalten | R: Platten-/Such-Rauschen (grep/graphify indexieren `.tmp`?) | `project.yaml:396-407`; `du -sh .tmp` | S |
| `*.sync-backup-*`-Dateien | **251** Dateien im Arbeitsbaum (Hooks/Agents), Retention wirkt nicht (#1270: 702 Dateien laut Issue) | **ändern**: `backup.retention` greift offenbar nicht für Hook-Backups → Fix via #1270 (Bugfix-Batch 3 Task 2.4) | R: Drift-/Grep-Rauschen; Hook-Dir unübersichtlich | `find . -name '*.sync-backup-*'`; `project.yaml:371-377` | S (Fix im Plan) |
| `backup.enabled: true`, `auto-backup-before-sync: false`, `.backup/` **existiert nicht** | Konfig ohne Wirkung | **behalten** (git ist Backup), `.backup`-Konfig ggf. aus | – | `project.yaml:371-377` | S |
| `orchestrator.strict: true` / `mode: strict` (Main-Chat kein Bash) | Strict | **behalten** — passt zu PR-/Gate-Workflow; Kosten: jede Git-Leseaktion als Subagent (~6k Tok Spawn-Overhead) | T: hoher Spawn-Overhead für `git status` → Hebel ist Always-on-Reduktion (A.2), nicht Strict-Lockerung | `use-orchestrator.md`; `project.yaml:310,321` | – |
| `auto_commit.mode: auto`, Trigger task-boundary + file-count 5, `secret_scan: true` | 22 Eligible-Rollen, u.a. `mammouth-expert`, `knowledge-migrator`, `export-manager`, `ui-ux-designer`, `design-system-architect`, `e2e-tester` | **ändern**: Eligible-Set auf Dev-/Doku-Rollen begrenzen (developer, junior/senior/principal, tester, release, agent-meta-manager, documenter?) — Tier-Semantik prüfen (#1181, #1210 Sentinel role-independent) | R: Commit-Grants role-independent im Guard (#1210) → breite Allowlist = größere Fläche; Q: ±0 | `.meta-config/auto-commit-allowlist.json`; #1210, #1247 (Trailer-Contract fehlt) | S |
| `file_count_threshold: 5` | 5 | **behalten** | – | `project.yaml:355` | – |
| `permissions.deny` (rm -rf, push --force, reset --hard) + `settings.local.json` 35 Allow-Einträge | lokal gepflegt | **behalten**; `/fewer-permission-prompts` periodisch | – | .claude/settings.json, `settings.local.json` | – |
| `auto-github-release.sh`, `lifecycle-check.sh`, `sync-on-config-change.sh`, `viz-log.sh` im Hook-Dir, **nicht** in `settings.json` verdrahtet | tote/geparkte Hooks | **prüfen**: bewusst (Release-Hook via Tag-Event?) oder Drift (**nicht geprüft**) | R: gering | `ls .claude/hooks`; `settings.json` | S |

### A.6 MCP-Server / Plugins / Export / Release-Checklist

| Einstellung | Ist | Empf. | Wirkung | Beleg | Aufw. |
|---|---|---|---|---|---|
| `plugins.honcho: true` → `.mcp.json` SSE `http://172.20.4.255:8200` | **404** in dieser Session; Honcho-Skill + 7 `honcho:*`-Commands + Tool-Verbote in `mcp-guardrails.md` | **ändern → aus** bis Endpoint läuft | T: Skill-Description + Rule-Zeile (~0,2k); R: jede Session startet mit Fehlermeldung; Honcho-Memory-Nutzen hier nicht belegt | `project.yaml:83-84`; `.mcp.json`; Session-Hinweis „honcho (404)“ | S |
| `plugins.reqogniloom: true` → `.mcp.json` **und** Plugin (`plugin:reqogniloom:reqogniloom`) | doppelt eingebunden, inkompatible Env-Namen (`MCP_REQOGNILOOM_URL` vs `REQOGNILOOM_MCP_URL`), beide **INVALID_CONFIG**; 5 Plugin-Agenten + 6 Skills + 18 Tool-Verbote in `mcp-guardrails.md` | **ändern → aus** (Repo nutzt kein ReqogniLoom-Workspace; REQ-Traceability false) — Fix #1261/#1264/#1265 für Konsumenten-Repos trotzdem | T: −6 Skill-Descr. (~0,5k), −5 Agent-Descr., −Guardrail-Zeile; R: 0 | `project.yaml:87-88`; `.mcp.json`; #1261 | S |
| `plugins.playwright: true` | stdio `npx @playwright/mcp@latest` — funktioniert; Nutzung nur Admin-UI-Audits (`e2e-tester`) | **behalten, aber lazy**: nur bei Admin-UI-Arbeiten; `@latest` → Version pinnen | R: Supply-Chain (`@latest`); T: Skill-Descr. + Guardrail | `.mcp.json` | S |
| `plugins.graphify: true` | 290 MB Index, 36.886 Knoten, zwei Guards | **behalten** (einziges hier belegt genutztes MCP-/Tool-Plugin) | Q↑ Orientierung | `graphify-out/` | – |
| `viz.enabled: false, mode: 'off'` **aber** `viz-logger` in `.mcp.json` (stdio, Content-Length-Framing) | **CONNECT_TIMEOUT 30 s** je Session; #1259, #1260 | **ändern**: `.mcp.json`-Eintrag entfernen (Fix #1260 in Bugfix-Batch 3 PR 1) | T/Zeit: 30 s Startlatenz je Session; `mcp-viz-logger`-Skill-Description (~0,1k) | `project.yaml:325-336`; `.mcp.json`; #1259/#1260 | S (im Plan) |
| `admin-ui.enabled: true`, Port 7420, `watch-config: false`, `auto-sync-on-save: false` | Konservativ | **behalten**; `.bak`-Dateien (5×) in `.meta-config` aufräumen (#1173 yaml.dump-Kommentare) | R: Admin-UI-Saves erzeugen `.bak`-Müll | `ls .meta-config` | S |
| `analysis.enabled: false` | aus, aber `/analysis`-Command gerendert | **behalten**; Command-Rendering bei `enabled: false` unterdrücken (Framework-Fix) | T: 1 Command-Description | `project.yaml:342-343`; .claude/commands/analysis.md | S |
| `se-export: {type: markdown, output_dir: docs/se}` | SE aus → tote Konfig; `export-manager`-Rolle aktiv | **aus** (siehe A.3) | – | `project.yaml:289-291` | S |
| `release-checklist` | fehlt (= off) | **ändern → advisory** (A.1) | – | – | M |
| `provider-deactivation.enabled: false`, `environments: {}`, `model-override-all: {}`, `model-overrides: {}`, `debug-mode: false`, `allow-committed-secrets: false` | Defaults | **behalten** | – | `project.yaml:349-384` | – |
| `secrets.local.yaml` in `.meta-config` | vorhanden | **prüfen** gitignored (**nicht geprüft**) | R: Secret-Leak | `ls .meta-config` | S |

### A.7 Top-10 Konfigurationsänderungen (Reihenfolge + Rebaseline)

Reihenfolge nach Nutzen/Risiko; Rebaseline-Kosten einmal zahlen → in **3 PRs** bündeln.

| # | Änderung | Wirkung | Rebaseline | PR |
|---|---|---|---|---|
| 1 | `.mcp.json` bereinigen: viz-logger raus (Fix #1260), `plugins.honcho: false`, `plugins.reqogniloom: false` | −30 s Session-Start, keine Fehlermeldungen, −~0,8k Tok always-on (Skills/Guardrails/Plugin-Agents) | `.mcp.json`, `generated-file-hashes.json`, `mcp-guardrails.md` → Rules-Golden (3 Provider) | **PR-A Hygiene** |
| 2 | Tote Konfig raus: `provider-options` Leerblöcke (6), `se-export`, `SE_BASE_DIR`, `knowledge-engine.migration`, `test-repo` (Pfad fehlt), `variables.ORCHESTRATOR_STRICT`/`UNKNOWN_FALLBACK_*` (Duplikate), `.continue/` löschen, `.bak`-Dateien | Drift-Quellen weg; T ±0 | minimal (ggf. `context-hashes.json`) | PR-A |
| 3 | `repo_containment.tmp-sink`-Aufräumen (1 GB `.tmp`), `*.sync-backup-*` (251) via #1270-Fix, graphify-Guard-Hinweis drosseln | Such-/Index-Rauschen, −~4k Tok Hook-Kontext je Session | Hook-Hash (`.claude/hooks`) | PR-A (+Batch-3 PR 2) |
| 4 | `roles:` 58 → ~30 (A.3-Liste: 15 aus, 3 Provider-Experten aus, knowledge-* auf 0–2, SE-Rolle aus) | −1,4k Tok always-on je Nachricht **und** Spawn; route_intent-Enum −50 %; AGENTS.md unter Compact-Target möglich | `.claude/agents/*` (−28), `AGENTS.md`, `opencode.json`, `.gemini/*`, `auto-commit-allowlist.json`, AC-01-Baseline/Golden/Ceilings aller 3 Provider | **PR-B Roster/DoD** |
| 5 | `dod-preset: spec-optional` (oder `dod: {tests-required: true, root-cause-required: true}`) + `release-gates.action-pin-validation: true` | DoD spiegelt CI; Tester/Validator fordern Tests | CLAUDE.md/AGENTS.md-Header, Rollen mit DoD-Block (tester, validator, developer*) → Golden | PR-B |
| 6 | Knowledge Engine **aus** (oder Minimal: 2 Rollen) + `spec-plan-workflow.index.mode: fallback-index` (**docs/INDEX.md fehlt → anlegen**) | −~1k Tok always-on, −7 Rollen, keine Doppelpflege Sources↔docs | CLAUDE.md KE-Block, Rollen, Golden | PR-B |
| 7 | Rules kürzen: `use-lazy-rules.md` aus (Claude), `branch-guard.md` „Bekannte Grenzen“ → `docs/concepts/`, `use-orchestrator.md` Git-Delegation-Prosa auf 2 Zeilen | −~0,6k Tok always-on je Nachricht/Spawn | `rules/1-generic/*` Templates → Rules-Golden; Consumer-Repos erben | PR-B (Template-Änderung, nicht nur Config) |
| 8 | `orchestrator.delegation.max_depth: 3`, `reflection-pairs.dev-review-loop.max_iterations: 3` | Kostenbegrenzung Loops; Konsistenz mit Opencode-Depth 3 | `orchestrator.md`-Render → Golden | PR-B |
| 9 | `auto_commit`-Eligible-Set auf Dev-/Release-Rollen (folgt teils automatisch aus #4) | kleinere Commit-Fläche bis #1210 (Sentinel role-independent) gefixt | `auto-commit-allowlist.json` | PR-B |
| 10 | `release-checklist: {mode: advisory, items: [sync --check, pytest, CHANGELOG, VERSION]}` | `/release-check` wird nutzbar; Prosa `VERSION_DIST_BEHAVIOUR` wird prüfbar | `release`-Rolle-Render, Checklist-Datei | **PR-C Release** |

**Nicht empfohlen:** `context-profile: compact` jetzt (unverifiziert, erst Spike nach #977/#1244); Strict-Mode lockern (Spawn-Overhead besser über #4/#7 senken); Gemini sofort abschalten (erst Entscheidung #1160).

**Erwartete Rebaseline-Auswirkung PR-B:** alle 3 Provider-Goldens + AC-01 + Ceilings + `generated-file-hashes.json` + `context-hashes.json` → #1237 (Rebaseline-Helper) **vorher** mergen spart 3–5 Rebaseline-Commits; Reihenfolge daher: Bugfix-Batch 3 (TMPDIR #1246) → #1237 → PR-A → PR-B → PR-C.

## B. Feature-Requests / offene Issues — Priorisierung

### B.1 Issue-Inventar

- **107 offene Issues** (`gh issue list --state open`, Liste: .tmp/audit/scratch/open-issues.txt): bug 27 · improvement 48 · feature/feature-request/enhancement 12/5/24 · design 10 · documentation 7; Labels hooks 12, sync 21, config 29, framework 19, consistency 17; Prio-Labels nur P1 3 / P2 12 / P3 7 (→ 85 ohne Prio).
- **40 Issues aus dem Audit-Batch 2026-11-14 (#1237–#1276)**, 27 Issues älter als #1000 (ältestes #329, 2026-08).
- Bodies gelesen (gekürzt): 30 Issues (.tmp/audit/scratch/issue-bodies.txt); Rest nur per Titel/Label (**Titel-Bewertung**).
- Roadmap-Zuordnung Phasen A–I: `docs/superpowers/plans/2026-11-10-backlog-roadmap.md:145-156` (90 Issues); Wellen 0–6 `:218-229`. Audit-Batch #1237–#1276 ist dort **noch nicht** zugeordnet.

### B.2 Bewertung gegen Pläne/Audits 2026-11-14

Vier Pläne, klar abgegrenzt (Überschneidungs-Tabellen `loop-plan:143-153`, `routing-plan:300-316`, `top5-plan:42-54`):

| Plan | Deckt Issues | Lücke / Verbesserungsvorschlag |
|---|---|---|
| **bugfix-batch-3** (3 PRs) | #1259 #1260 #1271 · #1258 #1252 #1142 #1270 #1249 · #1246 #1261(gated) | Gut geschnitten (S-Tasks, Rebaseline je PR). Verbesserung: **#1241** (PyYAML fail-hard, S) und **#1266** (toter a2a-Katalogeintrag + Catalog-Lint, S) in PR 2 aufnehmen — gleiche Dateiklasse, kein Spec nötig. **#1263** (MCP-Deny durchsetzen) als PR 4 anhängen: S, Security, kein Design offen (permissions.deny-Writer existiert für Bash). |
| **audit-top5-execution** (Tests, Admin-UI Security+A11y, KE-Lint, Doku) | #1276, Vorbedingung #1261/#1264/#1265 | Kein Code — parallel zu Welle 3. Verbesserung: **KE-Lint (Task 3) streichen**, wenn KE laut A.4 abgeschaltet wird (15–25k Tok gespart); Doku-Audit (Task 4) mit **#1159** (Doc-Drift-Chore) und **#1245** (Wording „security boundary“) zusammenlegen — gleiche Arbeit. Windows-Pfade bleiben raus (bereits so). |
| **agent-improvement-loop** (Rollen-Rewrite in Batches) | #1237 #1161 #1255 #1244 #1115 #969 | Größter Hebel (−30 % Templates, ~65k Tok Roster). Verbesserung: **Rollenzahl zuerst senken (A.3), dann Rewrite** — 28 Rollen weniger = 28 Rollen weniger umschreiben/rebaselinen. **#1014** (8 literaturbasierte Regeln je Rolle), **#778** (Literatur-Befunde) und **#885** (Template-Konformitäts-Audit, Baseline beta.1 = veraltet) in die Rubrik §4 des Plans **einarbeiten** und als Issues schließen/zusammenlegen — drei Issues beschreiben dasselbe Zielbild. |
| **intent-routing-table** (3 PRs, Spec-Gate) | #1161 Pkt 2 (H1), #779 #780 #969 #1243 #1176(Grenze) | Richtig: Spec vor Code. Verbesserung: **#1243** (topology-Namenskollision, S) **vorziehen** als eigener Mini-PR — `visibility.topologies` baut darauf; **#1244** zweiteilen: Roster-Reduktion = Config-Change (A.7 #4, sofort), Session-Ceiling-Test = bleibt Phase H. |

Konzeptionelle Querbefunde:
- Die Pläne setzen **#1237 (Rebaseline-Vereinheitlichung)** alle als Vorbedingung voraus, es hat aber keinen eigenen Plan → **zuerst**, sonst zahlt jeder PR 1–3 Rebaseline-Commits (Churn-Beleg: `generated-file-hashes.json` 92 Commits/90 d, `audit-prioritization.md:8`).
- Die Roadmap kennt die 40 Audit-Issues noch nicht → Vorschlag: Phase **„C2 Audit-Fixes“** (Bugfix-Batch 3 + S-Issues unten) in Welle 2/3 einhängen; Epics (#1257, #1273) als Phase-I-Concepts.
- Issues ohne Prio-Label (85) → Label-Taxonomie (#1188, Phase F) wäre der richtige Ort; bis dahin genügt die Tabelle B.3.

### B.3 Priorisierte Liste (zuerst / später / streichen / zusammenlegen)

Bewertung N=Nutzen, A=Aufwand, R=Risiko (h/m/n). Beleg = Issue-Body gelesen (B) oder Titel (T) + Code-/Plan-Referenz.

**ZUERST — Quick Wins (S, kein Spec-Gate, Welle „jetzt“)**

| Issue | N/A/R | Empfehlung | Begründung / Beleg |
|---|---|---|---|
| #1260 + #1259 viz-logger | h/S/n | zuerst (Batch 3 PR 1) | 30 s Timeout je Session, viz hier aus (B; `project.yaml:325`) |
| #1258 Guard False-Positive `git branch --contains` | h/S/n | zuerst (PR 2) | blockiert Read-only-Git im Strict-Mode (B; `batch3:36`) |
| #1246 TMPDIR-Drift | h/S–M/m | zuerst (PR 3) | Vorbedingung deterministischer Rebaseline (B; `batch3:44`) |
| #1237 Rebaseline vereinheitlichen | **h**/M/m | **zuerst, eigener Plan** | Vorbedingung aller 3 Folgepläne; #1115 **zusammenlegen** (B) |
| #1263 MCP-Deny durchsetzen | h/S/n | zuerst | Prompt-only-Verbot; `permissions.deny` hat nur 4 Bash-Einträge (B; .claude/settings.json) |
| #1243 topology-Namenskollision | m/S/n | zuerst (vor Routing-PR 2) | Enum-Referenz für `visibility.topologies` (T; `routing-plan:312`) |
| #1241 PyYAML fail-hard | m/S/n | zuerst (in Batch 3 PR 2) | stilles Fehl-Rendering (T) |
| #1266 toter a2a-Katalogeintrag | n/S/n | zuerst (in Batch 3 PR 2) | Lint-Test verhindert Wiederholung (T) |
| #946 18 Doubt-Branches/7 Stashes | m/S/n | zuerst (Entscheidungstabelle, Phase A offen) | Hygiene, Roadmap Welle 0 (T; `roadmap:219`) |
| #1139, #1173, #1189, #1175, #1208 | –/S/n | **schließen mit Beleg** | laut Batch-3-Plan erledigt/nicht reproduzierbar (`batch3:263-268`); #1175 Frage beantworten |
| **neu (Vorschlag):** „Config-Hygiene agent-meta“ = A.7 PR-A | h/S/n | zuerst | kein Issue vorhanden; schließt Teile von #1260/#1261 für dieses Repo |

**ZUERST — Hebel (M, Spec/Plan vorhanden oder nötig)**

| Issue | N/A/R | Empfehlung | Begründung / Beleg |
|---|---|---|---|
| #1161 route_intent-JSON/AGENTS.md/branch-guard | **h**/M/m | zuerst via `intent-routing-table`-Plan (H1) + Phase H Task 8 | ~7k Tok je Orchestrator-Spawn (B; `loop-plan:49`) |
| #1244 Roster + Session-Ceiling | h/S+M/n | **zweiteilen**: Roster = Config (A.7 #4) sofort; Ceiling-Test = Phase H | B |
| #1176 Orchestrator beendet Turn bei async Subagents | **h**/M/m | zuerst in Phase D | Kernqualität der Orchestrierung; blockiert `topology: primary` (T; `routing-plan:308`) |
| #1172 Merges via Orchestrator→git blockiert | h/S/n | zuerst (Phase D) | gelebter Merge-Pfad bricht (T) |
| #1168 + #1247 Commit-Trailer | m/S/n | **zusammenlegen**, Phase D | Trailer-Contract fehlt, git-Agent schreibt falschen (T) |
| #1210 + #1250 Sentinel/agent_id | h/M/m | **zusammenlegen**, Phase D (vor #1181) | Commit-Grants role-independent = Security-Lücke der auto_commit-Allowlist (T; A.5) |
| #1187 → #1186 → #1188 → #1181 → #1141 (Phase E/F/D-Kette) | h/L/m | zuerst in dieser Reihenfolge (Specs APPROVED) | 70/98 Templates rendern PROJECT_CONTEXT (B #1187); Roadmap-Kette `roadmap:222-224` |
| #1169 Hook-Latenz 9–11 Python-Spawns | m/M/m | zuerst nach Batch 3 (Phase D) | 382–495 ms je Bash-Call (B); mit #1238 (Heredoc-Python → Module) **zusammenlegen** |
| #1268 Managed-Block-Vereinheitlichung | m/M/m | zuerst als **Vorstufe** zu #1273 | 6 Implementierungen (B); konkreter Slice statt Monolith-Split |
| #1004 Planner mit Parallelisierungs-Matrix/PR-Grenzen | m/M/n | zuerst in Phase I (Template-only) | alle 4 Pläne vom 14.11. machen PR-Schnitt manuell → kodifizieren (B) |

**SPÄTER (Welle 4/5, nach Spec)**

| Issue | N/A/R | Empfehlung | Begründung |
|---|---|---|---|
| #1257 Hook-Kernel-Epic + #1248 #1251 #1252(Rest) #1256 #1249 | h/L/h | später, Concept → Spec; Unter-Issues **unter dem Epic zusammenlegen** | 5 Migrationsschritte (B); erst nach Phase D |
| #1253 #1254 #1255 provider-named Writer/Strip | m/M/m | **zusammenlegen** (ein Issue „provider-agnostic sync dispatch“), Phase G | gleiche Policy (`provider-agnostic`-Skill) |
| #1239 + #1240 Provider-Schema/Enumeration | m/M/n | **zusammenlegen**, Phase G | 34 Testdateien listen Provider (T) |
| #1273 Monolith-Split | h/L/h | später, nach #1268; Concept zuerst | 6.473-Zeilen-Admin-Server (B); `admin-server-split-backlog.md` existiert |
| #977 / #969 Context-Profiles/Eval-Gate | h/L/m | später (Phase H), #977 bleibt Tracking | Spec APPROVED; Eval-Kosten-Gate |
| #779 / #780 Routing-Sprache | m/M/n | später (Routing-Plan Block, Phase H Block D) | Entscheidung DE/EN nötig (B) |
| #960 Tier-Range-Routing | m/M/m | später, **nach** #969 (sonst nicht messbar) | B |
| #958 Project-specific roles | m/M/n | später (Phase I); Consumer-Nutzen, nicht dieses Repo | B |
| #832 Local Config Overlay | m/M/n | später (Phase I, nach C) — hätte hier Nutzen (`test-repo`, Provider-Toggles lokal) | B |
| #1113 Ask-User-Tool-Contract + #681 Liveness | m/M/m | später (Phase I, nach #1176); **#681 in #1113/#1176 einarbeiten** | Pläne haben je 10+ „Entscheidungspunkte“ → Frage-Contract wäre Hebel (B) |
| #1242 Migration-Stages, #1269 Extensions-Drift, #1262 MCP-Validate, #1274 MCP-Scaffold | m/S–M/n | später (Phase C2); **#1262 + #1274 zusammenlegen** | T |
| #1267 #1272 viz-Hardening | n/M/n | später — viz hier **aus**; nur für Consumer relevant | T |
| #1209 Artifact-Mode-Gating, #1197 #1198 #1199 #1200 | m/S–M/n | später in Phase E (wie geplant); **#1198 (P1) als S-Fix vorziehen** (18 Stellen, mechanisch) | T |
| #1201 #1202 #1203 #1204 #1211 | m/S/n | später, Phase F | T |
| #1217 Destructive-Gate Approval-Pfad | m/M/m | später (D), braucht Hook-API-Prüfung | T; `roadmap:224` |
| #1160 Gemini-Zielplattform, #1171, #814, #800 Hermes | m/M/m | später (Phase G); **#1160 zuerst entscheiden** → bestimmt, ob Gemini-Goldens weiter gepflegt werden | T |
| #896 #898 Admin-UI | n/M/n | später | T |
| #957 PR-Templates, #783 Merge-Policy | m/M/n | später (Phase I) | T |
| #820 + #877 Domain-Subfolder/Subplatform | m/L/m | später, **gemeinsames Concept** (Roadmap sagt es bereits) | B |
| #1167 REQ-ID-Format | n/S/n | später — REQ-Traceability hier aus | T |
| #1086 Rest c/f/i | n/S/n | später (Phase H / phase-c-1086i) | `batch3:267` |

**STREICHEN / SCHLIESSEN / ZUSAMMENLEGEN**

| Issue | Empfehlung | Begründung |
|---|---|---|
| #885 Template-Konformitäts-Audit (Baseline beta.1) | **schließen** → ersetzt durch `agent-improvement-loop`-Rubrik | Baseline veraltet (B); Roadmap „#885 schließen (eigener Schritt)“ `roadmap:229` |
| #1014 + #778 Literatur-Regeln | **zusammenlegen** in Loop-Plan §4 (Rubrik), danach schließen | identisches Zielbild (B) |
| #548 RFC Meta-Agent-Manager (2026-08) | **schließen** als „in Roadmap aufgelöst“ oder in ≤3 konkrete Issues splitten | 3 Monate alt, Teile umgesetzt (T; B-Kopf) |
| #1222 Harness-Follow-ups | **parken/streichen** (Design ohne Bedarf) | B |
| #329 #330 #339 SE-Framework-Designs | **parken** bis SE in einem Konsumenten aktiv ist | SE hier aus (`project.yaml:12-13`) |
| #679 web-best-practices-Preset, #676/#1106 hacs/homeassistant | **parken** (Plattform-Presets, nicht dieses Repo) | T |
| #1276 Punkt Windows | **streichen** (wie Top5-Plan) | `audit-prioritization.md` Zeile 15 |
| #1245 Wording, #1159 Doc-Drift | **zusammenlegen** in Audit-Top5 Task 4 (Doku-Wahrheitsgehalt) | gleiche Arbeit |
| #1264 #1265 ReqogniLoom-Katalog/Opt-in | **zusammenlegen** mit #1261; hier Plugin **aus** (A.6) | B; Top5-Plan Task 0 verifiziert zuerst |
| #1115 Ceiling-Re-pin | **zusammenlegen** in #1237 | gleiche Mechanik |
| #1238 Heredoc-Python | **zusammenlegen** in #1169 | gleiche Dateien (`hook_common.sh`) |

**Top-5 Feature-Requests/Verbesserungen (Reihenfolge):**
1. #1237 Rebaseline-Vereinheitlichung (+#1115) — macht alles danach billiger.
2. #1161 + #1244-Roster — Token-Hebel ~7k/Orchestrator-Spawn + ~1,4k/Nachricht.
3. #1176 + #1172 Orchestrator-Laufzeitfehler (Phase D) — Kernqualität.
4. #1187→#1186→#1188 Config-Welle (APPROVED) — beseitigt 37-fach PROJECT_CONTEXT und Pfad-Literale.
5. #1263 MCP-Deny-Enforcement + #1210/#1250 Sentinel — Convention→Security für Commit/MCP.

## C. Nicht geprüft / Unverifiziert

- Keine Syncs/Tests/Hooks ausgeführt; alle Token-Werte Bytes/4-Proxy (aus Loop-Plan) oder tiktoken-Memory 2026-08.
- Rollen-Nutzung nur per Mention-Zählung in Plänen/Conclusions (schwacher Proxy); keine Session-Logs/Checkpoints ausgewertet (kein Checkpoint-Verzeichnis gefunden).
- Nicht geprüft: ob sync `ORCHESTRATOR_STRICT`/`UNKNOWN_FALLBACK_*` aus `orchestrator:` ableitet (Duplikat-Entfernung sicher?); ob SE-Skills/`export-manager` automatisch bei `systems-engineering.enabled: false` entfallen; warum `.continue/` trotz `ignore-provider-dirs` nicht ignoriert ist; ob `checkpointing: true` wirkt; ob `tmp-sink.cleanup` andere Werte als `manual` kennt; ob Commands bei `analysis.enabled: false` unterdrückbar sind; ob nicht verdrahtete Hooks (`auto-github-release.sh`, `lifecycle-check.sh`) bewusst sind.
- `context-profile: compact` nicht getestet (Schema: „unverified“).
- Issue-Bodies: 30 von 107 gelesen (gekürzt auf 450–700 Zeichen); 77 nur per Titel/Label.
- `docs/superpowers/plans/2026-11-11-phase-h-context-eval.md` und Phasenpläne D–I nicht gelesen (nur Roadmap-Tabelle).
- Honcho-/ReqogniLoom-Nutzen in anderen Consumer-Repos nicht bewertet — Empfehlung „aus“ gilt nur für dieses Repo.
- graphify-Graph genutzt (Orientierung), Stale-Grad nicht geprüft.

## D. Token-Schätzung

- Dieser Audit-Lauf: ~70–85k Tok Kontext (geschätzt; 14 Tool-Calls, größte Einzelausgaben Issue-Liste 107 Zeilen, Issue-Bodies 24 KB gekürzt, project.yaml 407 Zeilen).
- Erwartete Einsparung durch A.7 PR-A+PR-B (Bytes/4, Schätzung): always-on 6,1k → ~3,5k Tok je Nachricht/Spawn; Orchestrator-Spawn −7k (via #1161); bei ~40 Spawns/Session ≈ 100–150k Tok/Session; Session-Start −30 s.
