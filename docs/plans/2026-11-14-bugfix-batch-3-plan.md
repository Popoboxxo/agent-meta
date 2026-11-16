---
pipeline_stages:
  implement: 1
status: APPROVED (User, 2026-11-16, via "Ja alle 3 in der Reihenfolge" + "P2 Nachtrag passt"; Nachtrag korrigiert PR 2)
date: 2026-11-14
base-commit: 3dc03f95
branches:
  - fix/batch3-viz-mcp
  - fix/batch3-guard-sync
  - fix/batch3-tmpdir-determinism
trace:
  - bugfix-batch-3
---

# Bugfix-Batch 3 — Implementation Plan

> Status: APPROVED (User, 2026-11-16, via "Ja alle 3 in der Reihenfolge" + "P2 Nachtrag passt"; Nachtrag korrigiert PR 2). Dieser Plan implementiert nichts, committet nichts, ändert keine Issues.
> Basis: `origin/main 3dc03f95`. Zeilenanker gelten für diesen Stand und veralten. Vor Ausführung Freshness-Check gegen `origin/main`.
> Issues im Batch: #1259, #1260, #1271, #1258, #1252, #1142 (P3), #1270, #1249 (Teil), #1246, #1261 (Teil, gated).
> Nicht im Batch (Phasenplan D–I, bereits erledigt, kein Bug): siehe Abschnitt »Kandidatenbewertung«.
> Merge: ausschließlich der Nutzer. Issue-Schließen: nur nach Merge, je Issue ein Beleg-Kommentar. Keine Closing-Keywords in Commits/PRs.

## Entscheidungsstand 2026-11-15

Quelle: [Master-Roadmap §4](2026-11-15-master-roadmap.md) (Nutzerentscheidungen 2026-11-15). Plan-Status bleibt DRAFT.

- E-02: #1246 Variante B+ (Key temp-root, env-freier Default), wie Empfehlung.
- E-03: viz-logger-mcp.mjs löschen; #1260 nur über Config (explizites `enabled:false` schlägt Plattform-Bundle).
- E-09: #1249 Tier-Fold geht nach #1257 (nur Test + ein Doku-Satz); #1261 nur WARN; #1270 30-Tage-Regel ja; .bak wird nicht geprunt.
- E-04: permissionMode plan -> default jetzt, eigener kleiner PR.
- E-19 (Abweichung): Trailer-Contract konfigurierbar (Config-Key), Contract in git.md; Git-Agent-PR kommt zuerst, nicht fest im Prompt-Trailer.

**Goal:** Zehn verifizierte Defekte in drei thematisch geschnittenen PRs beheben (Viz/MCP-Laufzeit, Guard/Sync-Robustheit, TMPDIR-Determinismus), je Issue ein TDD-Task, pro PR genau ein Rebaseline-Commit.
**Architecture:** Lokale Ursachenbehebung in der Datei des Befunds; keine neuen Module außer Testdateien; Provider-Unterschiede nur über Config-Keys/Capability-Flags.
**Tech Stack:** Python 3.9 (stdlib + PyYAML), Bash-Hooks mit Python-Heredoc, pytest, YAML/JSON-Config.
**Spec:** Alle Tasks S-Klasse (ad-hoc Bugfix, regelbasiert klassifiziert, kein Artefakt nötig) — Ausnahmen: #1246 Variante B (Schema-Key) und #1261 sind M-nah und stehen hinter Entscheidungen E-1/E-5; ohne Freigabe entfallen sie.

## Kandidatenbewertung (Schritt 1+2)

| Issue | Befund am Code (3dc03f95) | Verdikt |
|---|---|---|
| #1259 | `scripts/viz-logger.py:285-315` LSP-Framing (`Content-Length`), `scripts/viz-logger-mcp.mjs:95,103` gleich; MCP-stdio verlangt NDJSON. Laufzeitbeleg: `viz-logger (CONNECT_TIMEOUT 30000ms)` in dieser Session. | **Batch, PR 1** |
| #1260 | `scripts/lib/registry_query.py:158-172`: Bundle-Pass fügt jeden Server mit `enabled-by-default: true` hinzu (`config/plugin-catalog.yaml:88`), ohne `viz.enabled` (`.meta-config/project.yaml:325-327` = false) oder ein explizites `plugins.<id>.enabled: false` zu prüfen. `.mcp.json:32` enthält `viz-logger`. | **Batch, PR 1** |
| #1271 | `scripts/admin-server.py:864-884` `_stop`: `os.kill(pid,15)` → 1 s → `os.kill(pid,9)` ohne Identitätsprüfung; Pidfile enthält nur die PID (`:848`). Identity-Check nur im Health-Pfad (`:740-746`). | **Batch, PR 1** |
| #1258 | `hooks/1-generic/orchestrator-guard-impl.sh:1035-1038` `is_mutation('branch')`: `bool(positional)` ⇒ `git branch -a --contains <sha>` (positional `<sha>`) = Mutation. Ursache isoliert; Schleifen-Keywords werden vom Tokenizer übersprungen (`:614-615`). Testtabelle `tests/test_orchestrator_guard_hook.py:309-333` hat keinen `--contains`-Fall. | **Batch, PR 2** |
| #1252 | `scripts/lib/hooks.py:682-683` Fallback `_update_settings_hooks`; Writer-Tabelle `:441-444` deckt genau `SUPPORTED_HOOK_PROTOCOLS` (`providers.py:690`); Mammouth/Codex haben `has_hooks: true` ohne Protokoll und werden vorher über `provider_hooks_supported` (`hooks.py:514`) abgewiesen ⇒ Fallback heute unerreichbar, aber latent (neues Protokoll ohne Writer landet still beim Claude-Writer). | **Batch, PR 2** (fail-loud + Paritätstest; `provider="Claude"`-Defaults nicht im Scope → #1257) |
| #1142 P3 | `scripts/lib/cli_commands.py:1490` `log.warning("config-audit [ERROR] auto_commit…")` + `consistency_errors += 1`; Summary zählt `len(self.warnings)` (`log.py:178`). Gleiche Klasse: `:1469` (`context-profile.invalid`), `:1480` (`unpaired-closing-tag`). | **Batch, PR 2** |
| #1270 | Retention ist count-only, neuestes Backup je Quelle überlebt immer (`generated_file_drift.py:151-233`, `sync_pipeline.py:969-972` = 3/Quelle, 30/Dir). Zählung: 702 = 407 unter .tmp/head-agents/ (Scratch, gitignored, kein Sync-Output) + 190 im Baum (je 1/Quelle, by design) + hooks 4/3/3 (transient) + Root `CLAUDE.md.sync-backup-20260913-200441` (Root ist nicht in `_managed_dirs_for_prune`, `sync_pipeline.py:994-1028`). `project.yaml.bak.*` (5) stammen aus `meta_optimizer.py:185`, keine Retention. | **Batch, PR 2** (Root-Dir + Alters-Regel für Alleinüberlebende; `.tmp`-Anteil ist kein Bug) |
| #1249 | Deny nur bei explizitem Primary-Entry-Point (`isolation.py:828-831`), Warnung laut Docstring vorhanden (Text/Pfad nicht ausgeführt). Doku beschreibt observe-only bereits (`docs/providers/opencode.md:63,173,333,361`). Offen: Tier-Fold meldet `plugin` statt `advisory`. | **Batch, PR 2** nur Test für die Warnung + Doku-Satz; Tier-Fold → Entscheidung E-4 (Default: an #1257/Opencode-Enforce verweisen) |
| #1246 | `config.py:2119` injiziert `PYTEST_BASETEMP`; `tmp_paths.py:252-258` → `rc.system_temp_root` (`repo_containment.py:635` `tempfile.gettempdir()` honoriert `TMPDIR`); gerendert in `.claude/agents/tester.md:45` und `.claude/settings.local.json:42` (`/var/tmp/hermes/pytest-agent-meta`); Hash in `generated-file-hashes.json`. Reproduktion plausibel, nicht ausgeführt (kein Sync erlaubt). | **Batch, PR 3** (Entscheidung E-1) |
| #1261 | `config/plugin-catalog.yaml:273-288` (Prosa-Hinweis, `MCP_REQOGNILOOM_*`), Plugin-Seite außerhalb des Repos. Laufzeitbeleg: beide `INVALID_CONFIG`-Fehler in dieser Session. Kein Capability-Flag für Plugin-Systeme in `provider-capabilities.yaml`. | **PR 3, gated** (Entscheidung E-5; Default: nur Sync-WARN) |
| #1139 | AK1 erledigt (#1224). AK2 jetzt erfüllt: `tests/test_cli_smoke_multi_provider.py:48-51` `pytest.skip` bei `TimeoutExpired` mit klarer Meldung, Fixtures `project_readonly`/`project_scaffold` (`:56-63`) getrennt. AK3 (grün auf belasteter Maschine) nicht beweisbar. | **bereits erledigt → schließbar mit Beleg** |
| #1208 | Blindfleck nicht reproduziert (Kommentar 2026-11-12); Absicherungstest `tests/test_check_context_drift.py` vorhanden; Rest Phase H. | **nicht reproduzierbar** → Phase H / schließen |
| #1173 | Diff-Sperre statt Kommentarerhalt (#1224) — bewusste Entscheidung 22. | Entscheidung E-7: als erledigt schließen oder Phase I (`ruamel` per ADR ausgeschlossen) |
| #1141 | Phase D (nach #1181, Entscheidung 35). | **nicht doppelt planen** |
| #1197, #1198, #1199 | Phase E (#1187 T9 bzw. E-T1/E-T2). | **nicht doppelt planen** |
| #1201, #1203, #1204 | Phase F. | **nicht doppelt planen** |
| #1160 | Phase G (blockiert durch #860). | **nicht doppelt planen** |
| #1159, #1161, #1086 c/f/i | Phase H bzw. Plan `phase-c-1086i-context-split`. | **nicht doppelt planen** |
| #1168, #1172, #1176, #1210, #1217 | Phase D. | **nicht doppelt planen** |
| #1180, #1189 | Phase C (ausgeführt via #1225 / Plan `2026-11-09-1189-tmp-sink-pin-plan`); #1189 offen → Abschlusskommentar prüfen. | **nicht doppelt planen** |
| #898 | Label `feature`, kein Bug. | **ausgeschlossen** |
| #1222 | Design-Issue, kein Bug. | **ausgeschlossen** |
| #1257 | Epic, nur verlinkt. | — |

## Global Constraints

- Python 3.9 kompatibel (`from __future__ import annotations` ist in `hooks.py`, `registry_query.py`, `admin-server.py` vorhanden; kein `match`, kein `X | Y` zur Laufzeit).
- Nur stdlib + PyYAML. Keine neue Dependency.
- Provider-agnostisch: kein `if provider == "Name"`; Plugin-IDs (`viz-logger`) dürfen nur in Config/Katalog stehen, nicht im Syncer-Code (Entscheidung E-3 regelt die Ausnahme).
- Hook-Dateien (`hooks/1-generic/*.sh`) tragen `# version:`/`# changelog:` (Zeile 2-3) — jede Änderung bumpt die Version (Skill `conventions`).
- Tests lesen keine gitignorierten generierten Dateien (`.claude/hooks/*`, `.mcp.json`, `.claude/agents/*` sind untracked — Beleg: `git ls-files` liefert nur `AGENTS.md`); Guard-Tests laufen gegen `hooks/1-generic/` (`test_orchestrator_guard_hook.py:66-67`), MCP-Tests gegen tmp-Projekte.
- Keine Template-Änderung in `agents/1-generic` in diesem Batch ⇒ kein AC-01-/Golden-/Standalone-/Context-Budget-Rebaseline. Rebaseline betrifft nur `.meta-config/generated-file-hashes.json` (Hooks: 16 Einträge; `.mcp.json`).
- Commits: Conventional Commits, Englisch, ≤ 72 Zeichen, Imperativ, ein Commit je Task plus ein Rebaseline-Commit je PR. Keine Closing-Keywords (`Fixes/Closes/Resolves`), nur `Refs #N`.
- Commit-Trailer im Brief an den `git`-Agenten **wortgleich wiederholen** (Haiku-Fehler #1168/#1247): `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` — der Agent übernimmt ausschließlich diesen Trailer, nie den harness-eigenen.
- Kein `isolation: "worktree"`. Push/Branch nur durch die `git`-Rolle. Strikt sequentiell: PR 1 → PR 2 → PR 3, jeder Branch frisch von `origin/main` nach Merge des Vorgängers.
- Pro Task: roter Test → Implementierung → grün → Commit. Abschluss je PR: `python3 scripts/sync.py` (Rebaseline), `python3 scripts/sync.py --check`, `python3 scripts/sync.py --validate`, betroffene Testdateien, dann gezielt `tests/test_context_budgets.py` (Ceilings) als CI-Falle-Check obwohl keine Templates geändert werden.

## File Structure

PR 1 `fix/batch3-viz-mcp`
- Modify: `scripts/viz-logger.py` (`_send_message`, `_read_message`, `:285-315`) — NDJSON (#1259)
- Modify: `scripts/viz-logger-mcp.mjs` (`:88-110`) — NDJSON oder Datei entfernen (Entscheidung E-2) (#1259)
- Create: `tests/test_viz_logger_mcp_stdio.py` — Subprozess-Handshake NDJSON (#1259)
- Modify: `scripts/lib/registry_query.py` (`resolve_active_mcp_servers`, `:158-172`) — explizites `enabled: false` schlägt Bundle (#1260)
- Modify: `.meta-config/project.yaml` (`plugins:` ab `:82`) — `viz-logger: {enabled: false}` (#1260, Entscheidung E-3)
- Modify: `tests/test_mcp_config.py` — Bundle-vs-explizit-Fall (#1260)
- Modify: `scripts/admin-server.py` (`VizManager._stop` `:864-884`, `_start` `:848`) — Cmdline-Identitätsprüfung (#1271)
- Modify: `tests/test_admin_server_lifecycle_smoke.py` — PID-Reuse-Fall (#1271)
- Rebaseline: `.meta-config/generated-file-hashes.json` (`.mcp.json` ohne `viz-logger`)

PR 2 `fix/batch3-guard-sync`
- Modify: `hooks/1-generic/orchestrator-guard-impl.sh` (`is_mutation`, `:1035-1038`; Header `:2-3`) (#1258)
- Modify: `tests/test_orchestrator_guard_hook.py` (`MUTATION_CASES`, `:309-333`) (#1258)
- Modify: `scripts/lib/hooks.py` (`:682-692`) — unbekanntes Protokoll: WARN, kein Writer (#1252)
- Modify: `tests/test_provider_hooks_config.py` — Paritätstest Writer-Tabelle = `SUPPORTED_HOOK_PROTOCOLS`, Fake-Protokoll-Fall (#1252)
- Modify: `scripts/lib/cli_commands.py` (`:1469`, `:1480`, `:1490`) — `log.error` statt `log.warning` (#1142 P3)
- Modify: `tests/test_auto_commit_invalid_sync.py` (`test_validate_reports_error_summary`) — Summary zählt `1 error(s)` (#1142 P3)
- Modify: `scripts/lib/sync_pipeline.py` (`_managed_dirs_for_prune`, `:994-1028`) — Projekt-Root aufnehmen (#1270)
- Modify: `scripts/lib/generated_file_drift.py` (`select_prunable_sync_backups`, `:199-208`) — Alters-Regel für Alleinüberlebende (Entscheidung E-6) (#1270)
- Modify: `tests/test_sync_backup_retention.py` — Root-Dir + Alters-Fall (#1270)
- Modify: `tests/test_opencode_v2_surface.py` — Warnungstest »Gate ohne Entry-Point« (#1249)
- Modify: `docs/providers/opencode.md` (nahe `:361`) — ein Satz: Tier `plugin` + Topologie `subagent` = effektiv advisory (#1249)
- Rebaseline: `.meta-config/generated-file-hashes.json` (16 Hook-Einträge)

PR 3 `fix/batch3-tmpdir-determinism`
- Modify: `scripts/lib/repo_containment.py` (`system_temp_root`, `:621-663`) — env-freier Default und/oder expliziter Root (#1246, Entscheidung E-1)
- Modify: `scripts/lib/tmp_paths.py` (`resolve_pytest_basetemp`, `:231-258`) — expliziten Root durchreichen (#1246, nur Variante B)
- Modify: `config/project-config.schema.json` (`system-temp-exception`, `:2773-2790`) — Key `temp-root` (#1246, nur Variante B)
- Modify: `.meta-config/project.yaml` (`:403-407`) — `temp-root: /var/tmp` (#1246, nur Variante B)
- Modify: `tests/test_tmp_sink_system_temp_root.py`, `tests/test_tmp_paths_builder.py`, `tests/test_settings_dirs.py` — TMPDIR-Unabhängigkeit (#1246)
- Modify: `scripts/lib/mcp.py` oder `scripts/lib/mcp_health.py` — WARN bei doppelter ReqogniLoom-Einbindung (#1261, nur bei E-5 = WARN)
- Create: `tests/test_mcp_duplicate_plugin_warning.py` (#1261, gated)
- Rebaseline: entfällt in PR 3 (B+ mit `temp-root: /var/tmp`; Prosa-Änderung an `plugin-catalog.yaml:245` ausgelagert in eigenen S-PR). Env-freier Default gilt nur für Linux (feste Liste); macOS/Windows behalten `gettempdir()`.

## PR 1 — Viz/MCP-Laufzeit (`fix/batch3-viz-mcp`)

Reihenfolge: höchster Nutzen (30-s-Timeout bei jedem Session-Start), kein Guard-/Template-Risiko.

### Task 1.1 — #1259 NDJSON-Framing im viz-logger (S)
- Red: `tests/test_viz_logger_mcp_stdio.py`: Subprozess `python3 scripts/viz-logger.py --mcp` mit `env` auf tmp-Projekt (Event-Log in `tmp_path`); sendet `initialize`, `notifications/initialized`, `tools/list`, `tools/call log_viz_event` je als eine JSON-Zeile; liest Antworten zeilenweise mit Timeout aus `tests/timeouts.py` (kein Literal, Guard `tests/test_timeouts_usage.py`); prüft `tools/list` enthält `log_viz_event` und Event landet in der Logdatei.
- Green: `_send_message` → `sys.stdout.buffer.write(json.dumps(msg, ensure_ascii=False).encode() + b"\n")` + flush; `_read_message` → zeilenweise `os.read`-Puffer bis `\n`, Leerzeilen überspringen, EOF → `None`. Logs ausschließlich nach stderr prüfen (grep `print(` im MCP-Pfad).
- Interface: unverändert (`_send_message(msg: dict)`, `_read_message() -> dict | None`).
- Entscheidung E-2 bestimmt den Umgang mit `viz-logger-mcp.mjs` (mitziehen vs. löschen).
- Akzeptanz: Test grün; Session-Start ohne `CONNECT_TIMEOUT` (manueller Beleg im PR-Text).
- Commit: `fix: use newline-delimited JSON-RPC for viz-logger stdio MCP`

### Task 1.2 — #1260 explizites `enabled: false` schlägt Plattform-Bundle (S)
- Red: `tests/test_mcp_config.py`: Config `{"plugins": {"viz-logger": {"enabled": False}}, "platforms": ["agent-meta"]}` + Registry mit `viz-logger` (`enabled-by-default: true`) ⇒ `resolve_active_mcp_servers` enthält `viz-logger` nicht; Gegenprobe ohne `plugins`-Eintrag ⇒ enthalten (heutiges Verhalten bleibt).
- Green: `registry_query.py:164` Schleife: `if activation.get(server, {}).get("enabled") is False: continue` (Aktivierungs-Dict aus `:150` auch im Legacy-Zweig berechnen).
- Config: `.meta-config/project.yaml` `plugins.viz-logger.enabled: false` (Entscheidung E-3). Kopplung an `viz.enabled` nur bei E-3 = »Katalog-Key« (dann zusätzlich `config/plugin-catalog.yaml`-Key `enabled-when: viz.enabled`, generisch ausgewertet in `registry_query.py`; +1 Test).
- Akzeptanz: nach `sync.py` kein `viz-logger` in `.mcp.json`; `tests/test_mcp_config.py` grün; Doku-Satz zum Aktivierungsmodell in `docs/guides/mcp/` (Datei bei Umsetzung wählen, `grep -rl enabled-by-default docs/guides`).
- Commit: `fix: let explicit plugin disable override platform bundle`

### Task 1.3 — #1271 Identitätsprüfung vor `_stop` (S)
- Red: `tests/test_admin_server_lifecycle_smoke.py`: `sleep 60`-Prozess starten, dessen PID in `.meta-viz/<pidfile>` schreiben, `VizManager._stop(pid_file, label)` aufrufen ⇒ Prozess lebt, Pidfile entfernt, Meldung »stale pidfile«. `pytest.mark.skipif(not Path('/proc').exists())`.
- Green: Helfer `_pid_cmdline(pid) -> str | None` (Linux `/proc/<pid>/cmdline`, sonst `None`); `_stop`: wenn Cmdline lesbar und weder `viz-report.py` noch `viz-logger.py` noch `admin-server.py` enthält ⇒ Pidfile löschen, nicht killen, Meldung. SIGKILL-Frist 1 s → 5 s. `shortcut: ohne /proc keine Identitätsprüfung (Verhalten wie heute); upgrade wenn Windows-/macOS-Nutzer PID-Reuse melden`. Starttime im Pidfile entfällt (YAGNI).
- Akzeptanz: Issue-Testidee grün; `test_start_status_stop_lifecycle` unverändert grün.
- Commit: `fix: verify process identity before admin-server stop kills a pid`

### Task 1.4 — Rebaseline PR 1 (S)
- `python3 scripts/sync.py` → `.mcp.json` ohne `viz-logger`, `.meta-config/generated-file-hashes.json` aktualisiert; `--check` = 0; `--validate` = 0.
- Commit: `chore: record regenerated file hashes after viz-logger changes`

## PR 2 — Guard/Sync-Robustheit (`fix/batch3-guard-sync`)

### Task 2.1 — #1258 `git branch` List-Modus ist read-only (S)
- Red: `MUTATION_CASES` ergänzen: `("git branch -a --contains abc123", False)`, `("git branch --merged main", False)`, `("git branch --list 'feat/*'", False)`, `("git branch --points-at HEAD", False)`, `("git log --oneline | head; for b in a b; do git cat-file -t $b; done; git branch -a --contains abc", False)`, Negativ: `("git branch -a -D old", True)`, `("git branch new-branch", True)` bleibt.
- Green: `orchestrator-guard-impl.sh:1035-1038`: `LIST_FLAGS = {'--list','-l','--contains','--no-contains','--merged','--no-merged','--points-at','-a','--all','-r','--remotes','--show-current'}`; `if set(args) & mutating_flags: return True`; `if set(args) & LIST_FLAGS: return False`; sonst `bool(positional)`. Hinweis: `-a`/`-r` mit Positional ist in git ein Fehler (»do not take a branch name«), also keine Mutation. `-v/--verbose` gegen git-branch(1) prüfen, bevor es in `LIST_FLAGS` aufgenommen wird (unverifiziert).
- Header: `# version: 1.11.0 → 1.12.0`, Changelog-Eintrag »#1258«.
- Akzeptanz: alle `MUTATION_CASES` grün; Schleifen-Teil des Issues als Testfall belegt (Keywords waren nicht die Ursache).
- Commit: `fix: classify git branch list-mode flags as read-only in guard`

### Task 2.2 — #1252 unbekanntes `hook_protocol` schreibt nichts (S)
- Red: `tests/test_provider_hooks_config.py`: (a) `set(hooks._HOOK_REGISTRATION_WRITERS) == providers.SUPPORTED_HOOK_PROTOCOLS`; (b) Monkeypatch `SUPPORTED_HOOK_PROTOCOLS` um `fake-proto`, Provider-Eintrag mit `hook_protocol: fake-proto`, Sync-Hook-Stage auf tmp-Projekt ⇒ `settings.json` unverändert, `log.warnings` enthält `unknown hook_protocol 'fake-proto'`.
- Green: `hooks.py:682`: `.get(proto)`; `None` ⇒ `log.warning(...)` + `return` vor jedem Writer-Aufruf.
- Akzeptanz: beide Tests grün; `provider="Claude"`-Defaults bleiben (Scope → #1257 Schritt 2, im Issue-Kommentar vermerken).
- Commit: `fix: warn instead of defaulting to settings writer for unknown hook protocol`

### Task 2.3 — #1142 P3 `[ERROR]`-Befunde zählen als Fehler (S)
- Red: `tests/test_auto_commit_invalid_sync.py::test_validate_reports_error_summary` erweitern: Summary enthält `1 error(s)` (Format aus `log.py:178-181`), Exit 1 bleibt.
- Green: `cli_commands.py:1469`, `:1480`, `:1490`: `log.error("config-audit", "[ERROR] <kind>: …")` (Signatur `error(target, message)`, `log.py:63`); Zeilenformat der Fehlerausgabe mit dem bestehenden Assert-String `config-audit [ERROR] auto_commit` abgleichen und Assert ggf. anpassen. `consistency_errors += 1` bleibt.
- Risiko: `--check`-Pfad bricht bei `log.errors` ab (`:1767`) — config-audit läuft dort nicht (`:1646` nur Stage 12 im Sync-Pfad; verifizieren).
- Akzeptanz: Exit-Code und Summary stimmen überein; keine weiteren Tests referenzieren die Warnungszeile (`grep` ergab nur diese Datei).
- Commit: `fix: count config-audit ERROR findings as errors in validate summary`

### Task 2.4 — #1270 Backup-Retention: Root-Dir + Alleinüberlebende (S)
- Red: `tests/test_sync_backup_retention.py`: (a) `_managed_dirs_for_prune` enthält `project_root` (Root-Backups von Kontextdateien); (b) Alleinüberlebendes Backup älter als `SYNC_BACKUP_MAX_AGE_DAYS` wird selektiert, jüngeres nicht (nur bei E-6 = ja).
- Green: `sync_pipeline.py:994`: `dirs.append(project_root)` als erstes; `generated_file_drift.py:199-208`: Alleinüberlebender (newer == 0) wird prunable, wenn `stamp < now - max_age_days` (Parameter aus `prune_sync_backups` durchreichen, Docstring `:255-258` anpassen).
- Issue-Kommentar vorbereiten: 407/702 liegen in .tmp/head-agents/ (Scratch, nicht Sync); `project.yaml.bak.*` (meta-optimizer) → Entscheidung E-6b.
- Akzeptanz: Tests grün; nach `sync.py` verschwindet `CLAUDE.md.sync-backup-20260913-200441` aus dem Root; `--cleanup-preview` zeigt dieselbe Auswahl (Paritätsregel `:166-169`).
- Commit: `fix: prune root-level sync backups and age out sole survivors`

### Task 2.5 — #1249 Warnung belegen + Doku-Satz (S)
- Red: `tests/test_opencode_v2_surface.py`: v2 + strict + `topology: subagent` ohne expliziten Primary ⇒ `_sync_opencode_runtime_gate` schreibt keinen Deny und `log.warnings` enthält die Entry-Point-Kopplungs-Warnung (`isolation.py:828-831`). Existiert der Test bereits, nur Verweis.
- Green: falls Warnung fehlt oder unklar: Text um »gate is advisory only« ergänzen. `docs/providers/opencode.md` nahe `:361`: ein Satz zur Kombination Tier `plugin` + `subagent`-Topologie.
- Tier-Fold (`weakest_runtime_gate_tier`) **nicht** ändern (würde `CRITICAL GATE`-Header in `AGENTS.md`/`CLAUDE.md` umrendern → Context-Hash-Rebaseline, #1208-Klasse) → Entscheidung E-4.
- Commit: `test: cover opencode gate warning without primary entry point`

### Task 2.6 — Rebaseline PR 2 (S)
- `python3 scripts/sync.py` → `.claude/hooks/orchestrator-guard-impl.sh` regeneriert, `generated-file-hashes.json` (Hook-Einträge) aktualisiert; `--check` = 0; `--validate` = 0; `tests/test_hook_drift.py`, `tests/test_hook_registration_invariant.py` grün.
- Commit: `chore: record regenerated hook hashes after guard fix`

## PR 3 — TMPDIR-Determinismus (`fix/batch3-tmpdir-determinism`)

### Task 3.1 — #1246 Reproduktion (S, read-only)
- Reproduktion im Worktree (`.tmp/wt-batch3-pr3`, nicht Hauptcheckout; liegt unter `.tmp/`, nicht `.claude/worktrees`, daher kein Verstoß gegen no-worktree-isolation): `TMPDIR=/var/tmp python3 scripts/sync.py --check --config <worktree>/.meta-config/project.yaml` vs. `TMPDIR=/tmp …` (gleicher Aufruf); Ausgabe nach .tmp/plans/scratch/1246-repro.txt. Erwartung laut Issue: 13 Dateien vs. 0 (siehe Spec, Abschnitt Task-3.1-Reproduktion).
- Ohne Reproduktion: Issue als »nicht reproduzierbar« kommentieren, Task 3.2 entfällt; Task 3.3 (#1261) ist unabhängig und läuft weiter.

### Task 3.2 — #1246 env-unabhängiger Temp-Root (M)
- Umsetzung gemäß SPEC IC-1–IC-3 (B+, Linux env-frei): Schema-Key `temp-root`, `system_temp_root(explicit_root=...)`, `resolve_pytest_basetemp`-Durchreichung; `.meta-config/project.yaml` setzt `/var/tmp` → Render byte-identisch, kein Rebaseline. Bestehende #1189-Tests in `tests/test_tmp_sink_system_temp_root.py` werden gemäß Spec-Abschnitt Tests angepasst (5 Tests skipif/umschreiben).
- Red: `tests/test_tmp_sink_system_temp_root.py`: Ergebnis identisch für `monkeypatch.setenv("TMPDIR", "/var/tmp")` und `/tmp`; `tests/test_tmp_paths_builder.py`: `temp-root` wird übernommen, relativer Pfad = `TmpSinkError`; `tests/test_settings_dirs.py` `basetemp_dirs` folgt.
- Nebenwirkung Schema: `fill_defaults()` darf den neuen Key nicht ungefragt in Consumer-`project.yaml` schreiben (Kommentar-Verlust #1074) — Key ohne Default-Wert anlegen. Test dafür (AK-6): `fill_defaults`-Stabilität.
- Zusätzlich: Config-Validierungstest (Typ/leer/absolut, AK-3/AK-6, bestehende `system-temp-exception`-Testdatei), Erweiterung `tests/test_settings_dirs.py` (`basetemp_dirs`), CHANGELOG-Eintrag als Verhaltensänderung Linux (AK-8).
- Commit: `fix: make pytest basetemp root independent of TMPDIR`

### Task 3.3 — #1261 Sync-WARN bei doppelter ReqogniLoom-Einbindung (S, gated E-5)
- Red: `tests/test_mcp_duplicate_plugin_warning.py`: Fixture mit `~/.claude/settings.json` (via `home`-Parameter von `check_external_plugin_duplicates`, `tmp_path` als home, AK-9) `enabledPlugins: {"reqogniloom@reqogniloom-marketplace": true}` + Katalog-Server aktiv ⇒ eine WARN mit Handlungsanweisung; ohne Datei ⇒ keine WARN.
- Green: Check in `scripts/lib/mcp_health.py` (best-effort, read-only), **ohne Prosa-Änderung** (Verweise in `plugin-catalog.yaml:245` und Skill `mcp-reqogniloom` gehören in einen eigenen S-PR mit Rebaseline, Spec SPEC-temp-root-and-reqogniloom-duplicate IC-6). Kein Provider-Literal; Lesen der Plugin-Datei über ein Capability-Flag `external_plugins_file` in `ai-providers.yaml` (Config-Key, kein `if provider`); `provider_config` (`sync_pipeline.py:313`) wird auf aktive Provider gefiltert als `provider_cfgs` an `check_mcp_health` (Aufruf `:378`) übergeben.
- Harmonisierung der Env-Namen/Auth (Issue-Vorschlag 2) nicht in diesem Batch (Server-Verhalten unverifiziert).
- Commit: `fix: warn when reqogniloom is active as plugin and catalog server`

### Task 3.4 — Rebaseline PR 3 (ENTFÄLLT für PR 3)
- Mit B+ (`temp-root: /var/tmp` in `.meta-config/project.yaml`) und ohne agent-hint-Änderung gibt es keinen Rebaseline durch #1246. Der Prosa-/Skill-Verweis (#1261) samt Rebaseline wandert in einen eigenen S-PR (Follow-up, siehe Spec IC-6).
- (ursprünglich) Commit: `chore: record regenerated file hashes after basetemp change`

## Testbeleg-Plan

| Issue | Roter Test (Datei::Name, neu/erweitert) | Grün-Beleg zusätzlich |
|---|---|---|
| #1259 | `test_viz_logger_mcp_stdio.py::test_ndjson_handshake_and_tool_call` (neu) | Session-Start ohne `CONNECT_TIMEOUT` (manuell, PR-Text) |
| #1260 | `test_mcp_config.py::test_explicit_disable_beats_platform_bundle` (neu) | `.mcp.json` ohne `viz-logger` nach Sync |
| #1271 | `test_admin_server_lifecycle_smoke.py::test_stop_spares_foreign_pid` (neu) | bestehender Lifecycle-Test grün |
| #1258 | `test_orchestrator_guard_hook.py::MUTATION_CASES` (+6 Fälle) | Ursprungskommando des Issues als Fall |
| #1252 | `test_provider_hooks_config.py::test_registration_writers_cover_all_protocols`, `::test_unknown_hook_protocol_writes_nothing` (neu) | — |
| #1142 P3 | `test_auto_commit_invalid_sync.py::test_validate_reports_error_summary` (erweitert) | `--validate` Exit 1 + `1 error(s)` |
| #1270 | `test_sync_backup_retention.py::test_project_root_is_pruned`, `::test_sole_survivor_ages_out` (neu) | Root-Backup verschwindet; `--cleanup-preview` Parität |
| #1249 | `test_opencode_v2_surface.py::test_gate_without_entry_point_warns` (neu/Verweis) | Doku-Satz |
| #1246 | `test_tmp_sink_system_temp_root.py::test_root_independent_of_tmpdir` (neu) + Builder-Test | `--check` unter beiden TMPDIR = 0 |
| #1261 | `test_mcp_duplicate_plugin_warning.py` (neu, gated) | WARN-Zeile im Sync-Log |

Abschluss je PR: `python3 scripts/sync.py --check`, `python3 scripts/sync.py --validate`, `python3 -m pytest tests/test_context_budgets.py tests/test_ac01_render_identity.py tests/test_hook_drift.py -q` (CI-Fallen), danach volle Suite auf CI (nicht lokal).

## Akzeptanzkriterien je Issue (Kurzform)

- #1259: NDJSON in beide Richtungen; `initialize`-Antwort < Timeout; Event in Logdatei.
- #1260: `viz-logger` fehlt in `.mcp.json`, wenn explizit deaktiviert; Bundle-Default sonst unverändert.
- #1271: fremde PID überlebt `_stop`; Pidfile wird bereinigt; SIGKILL erst nach 5 s.
- #1258: `git branch -a --contains <sha>` und das Issue-Kommando passieren; `-d/-D/-m/-M/-c/-C/-f` und Branch-Anlage bleiben Mutation.
- #1252: unbekanntes Protokoll ⇒ WARN, kein Writer; Writer-Tabelle = `SUPPORTED_HOOK_PROTOCOLS`.
- #1142 P3: `--validate` Summary zählt `[ERROR]`-Befunde als Fehler, Exit-Code und Summary konsistent.
- #1270: Root-Backups werden geprunt; Alleinüberlebende altern aus (E-6); Issue-Kommentar erklärt 407 Scratch-Dateien.
- #1249: Warnung testbelegt, Doku-Satz; Tier-Fold per E-4 entschieden.
- #1246: `--check` liefert unter `TMPDIR=/tmp` und `/var/tmp` dasselbe Ergebnis.
- #1261 (gated): WARN bei Doppel-Einbindung; sonst unverändert.

## Risiken

- Hook-Änderung (#1258) ⇒ Hash-Drift in Consumer-Repos bis zum nächsten Sync; Version-Bump zwingend, sonst `hook_drift`-Fehlalarm.
- `log.error` (#1142) ändert Ausgabeformat; nur ein Test referenziert die Zeile — Assert mitziehen.
- #1270 Alters-Regel kehrt teilweise zu einem Alterskriterium zurück (#1081 hatte Dual-Threshold entfernt); hier nur additiv (macht mehr prunable, blockiert nichts).
- #1246 (B+): Linux-Consumer ohne `temp-root` bekommen den env-freien Default (Basetemp-Drift beim nächsten Sync); agent-meta pinnt `/var/tmp`. (Hinweis "Schema-Key braucht Kenntnis vor #1141 (Phase D)": UNBELEGT, nicht verifiziert.)
- #1259 Auto-Detection beider Framings (Issue-Option) entfällt (YAGNI); Clients mit LSP-Framing sind nicht bekannt.
- `.mcp.json`/`.claude/hooks` sind untracked — Tests dürfen sie nicht lesen (CI-Falle); alle neuen Tests arbeiten auf tmp-Projekten oder `hooks/1-generic/`.
- Python 3.9: `viz-logger.py:12` hat `from __future__ import annotations` (verifiziert) — neue Annotationen bleiben dadurch 3.9-sicher.

## Rollback

- Je PR eigener Branch; Revert des Squash-Commits + erneutes `python3 scripts/sync.py` (Hashes) genügt.
- #1260: Entfernen des `plugins.viz-logger`-Eintrags stellt `.mcp.json` wieder her.
- #1258: Hook-Version zurück auf 1.11.0 + Sync.
- #1246: Ohne Key gilt unter Linux der env-freie Default; Entfernen des Keys aus `project.yaml` ändert daher den Render (Rebaseline nötig). Rollback = Revert des Squash-Commits + Sync.

## Entscheidungen für den Nutzer

- **E-1 (#1246):** A env-freier Root (`/tmp`) · B expliziter Key `temp-root` + Default heutiges Verhalten · **B+ (Empfehlung):** Key + env-freier Default — deterministisch auf Linux (macOS/Windows bleiben env-abhängig, Spec Q2), Nutzer-Setup (`/var/tmp`) bleibt via Key, kein Rebaseline.
- **E-2 (#1259):** `viz-logger-mcp.mjs` auf NDJSON mitziehen oder löschen — **Empfehlung: löschen**; Referenzen nur in Doku (`ARCHITECTURE.full.md`, `docs/CODEBASE_OVERVIEW.md`, `knowledge/wiki/concepts/architecture.md`), kein Code/Config nutzt die Datei (verifiziert); Doku-Zeilen im selben Commit entfernen.
- **E-3 (#1260):** Kopplung an `viz.enabled` per generischem Katalog-Key `enabled-when` oder nur `plugins.viz-logger.enabled: false` im Repo — **Empfehlung: nur Config-Eintrag + Bugfix »explizit schlägt Bundle«**; Kopplung erst, wenn Consumer-Repos es brauchen.
- **E-4 (#1249):** Tier-Fold auf `advisory` jetzt (Context-Rebaseline, berührt #1208-Klasse) oder an #1257 Schritt 4 / Opencode-Enforce verweisen — **Empfehlung: verweisen**, Issue offen lassen mit Teilbeleg.
- **E-5 (#1261):** nur Sync-WARN (Task 3.3) · Katalog-Server für Claude skippen · Env-Namen harmonisieren · nichts — **Empfehlung: nur WARN** (M-Arbeit braucht Server-Verifikation).
- **E-6 (#1270):** a) Alters-Regel für Alleinüberlebende (30 d) ja/nein — **Empfehlung: ja**; b) `project.yaml.bak.*` in `--prune-sync-backups` aufnehmen — **Empfehlung: nein** (gitignored, 5 Dateien, eigener Lebenszyklus meta-optimizer).
- **E-7 (#1173):** mit Diff-Sperre als erledigt schließen (Entscheidung 22) oder offen lassen — **Empfehlung: schließen mit Beleg**.
- **E-8 (#1139, #1208):** schließen mit Beleg (siehe Listen unten) — **Empfehlung: ja**.

## Nicht reproduzierbar / unklar

- #1208: `--check`-Blindfleck auf main nicht nachgewiesen (Kommentar 2026-11-12); Rest in Phase H.
- #1246: Reproduktion nur aus Code abgeleitet (kein Sync in dieser Planung erlaubt) → Task 3.1 zuerst.
- #1249: Warnungstext/-pfad bei fehlendem Entry-Point nicht ausgeführt, nur Docstring (`isolation.py:828-831`).
- #1258: `-v/--verbose` als List-Modus-Flag gegen git-branch(1) unverifiziert.
- #1261: Claude-Code-Verhalten bei leerer `${VAR}`-Expansion nur aus Fehlermeldung rückgeschlossen.
- #1270: hooks-Dir 4/3/3 Backups bei `max_per_source=3` — Reihenfolge Hook-Stage vs. Prune (`sync_pipeline.py:1131`) bei Umsetzung prüfen.

## Bereits erledigt (schließbar mit Beleg, nicht selbst schließen)

- #1139: AK1 `SLOW_TIMEOUT` (#1224); AK2 `pytest.skip` bei `TimeoutExpired` + getrennte Modul-Fixtures (`tests/test_cli_smoke_multi_provider.py:48-63`). AK3 nicht beweisbar → mit Hinweis schließen.
- #1173: Diff-Sperre + `__allow_lossy__` (#1224) als gewählte Lösung (Entscheidung 22) → E-7.
- #1086 a/b/d/e/g/h: laut Kommentar 2026-11-12 umgesetzt; c/f/i bleiben (Phase H / `phase-c-1086i`).

## Aufwandsschätzung

| PR | Tasks | Größe | Reihenfolge |
|---|---|---|---|
| PR 1 | 1.1 S, 1.2 S, 1.3 S, 1.4 S | S gesamt (~½ Tag Agentenzeit) | zuerst |
| PR 2 | 2.1 S, 2.2 S, 2.3 S, 2.4 S, 2.5 S, 2.6 S | M gesamt (Hook-Rebaseline) | nach Merge PR 1 |
| PR 3 | 3.1 S, 3.2 S/M (E-1), 3.3 S (E-5); 3.4 entfällt | S–M | nach Merge PR 2 und Entscheidungen E-1/E-5 |

## Brief-Vorlage an den `git`-Agenten (je Commit)

- Branch: `<PR-Branch>` von `origin/main`; kein Push ohne Nutzer-OK; kein Tag.
- Subject: `<aus Task>`; Body: `Refs #<N>` (kein `Fixes/Closes/Resolves`).
- Trailer **wortgleich**: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` — keinen anderen Co-Author-Trailer schreiben.
