---
pipeline_stages:
  implement: 3
status: DRAFT
date: 2026-11-11
base-commit: 9aa0e0c0
roadmap: docs/superpowers/plans/2026-11-10-backlog-roadmap.md
phase: D
issues: [1181, 1210, 1217, 1172, 1176, 1168, 1169, 1141]
branch: feat/phase-d-guards-hooks
---

# Phase D: Guards, Hooks, Commit-Authority Implementation Plan

> Status: DRAFT
> Base: `origin/main 9aa0e0c0` (Anker am 2026-11-11 gegen diesen Stand nachgemessen) | Roadmap Phase D (Welle 3) | Issues #1181, #1210, #1217, #1172, #1176, #1168, #1169, #1141

**Goal:** Die acht Phase-D-Issues so schneiden, dass jede Guard-/Hook-Änderung hinter einer freigegebenen Spec oder einer bereits freigegebenen Spec+Plan-Kombination läuft, Doku-Issues direkt umgesetzt werden und die Hook-Datei `orchestrator-guard-impl.sh` nie von zwei Tasks parallel angefasst wird. #1141 (Klasse M) ist der letzte Teil der Phase-D-PR nach #1181 (Entscheidung 35) und läuft hinter einem Spec-Gate.
**Architecture:** Drei Ströme (plus Nachläufer D für #1141). (A) #1181 wird nicht neu geplant: Ausführung des APPROVED Plans `docs/plans/2026-11-09-commit-authority-grant-plan.md` (16 Tasks) als Block. (B) Doku-/Template-Issues #1172, #1176, #1168 (S) in disjunkten Dateien. (C) Hook-Arbeit #1169 (M, Refactor), #1210 (L, Security-Spec) und #1217 (M, Spec) strikt sequentiell auf `hooks/1-generic/orchestrator-guard-impl.sh` und `hooks/1-generic/lib/hook_common.sh`.
**Tech Stack:** Bash (Hooks), Python 3.9+ (stdlib + PyYAML, eingebettet in Hooks), pytest, Markdown-Templates mit `{{...}}`-Platzhaltern.
**Spec:** docs/specs/2026-11-09-commit-authority-grant-spec.md

Spec-Lage je Issue: #1181 nutzt die oben genannte Spec (APPROVED, Rev. 1.4). #1210, #1217: keine, siehe Task 0 und Task 1 Spec-Gates. #1172, #1176, #1168: Klasse S, ohne Spec. #1169: Klasse M, Spec-Gate in Task 5. #1141: Klasse M, Spec-Gate in Task 11 (eigene Spec, Freigabe vor Task 12). Die `**Spec:**`-Zeile trägt nur einen Pfad, weil `scripts/lib/consistency/spec_plan.py:414` den Wert als Pfad prüft (`(project_root / ref).exists()`); Prosa über 255 Byte je Pfadkomponente bricht dort den Vollscan mit Errno 36 (Dateiname zu lang) ab.

## Global Constraints

- Python 3.9-kompatibel (kein `X | Y`-Typsyntax ohne `from __future__ import annotations`, kein `match`); nur stdlib + PyYAML. Bash-Teile bash-3.2-kompatibel (kein `mapfile`, keine assoziativen Arrays).
- Provider-agnostisch: Unterschiede über Config-Keys/Capability-Flags (z. B. `hook-agent-id` in `config/ai-providers.yaml:64`), nie über `if provider == "Name"`.
- Commits: Englisch, Conventional Commits, Subject <= 72 Zeichen, ein Commit pro Task; Bodies später als Datei, hier nur Subject-Zeilen. PR-Schnitt (Entscheidung 17, präzisiert durch Entscheidung 52): Phasen-PR D enthält nur die zum PR-Zeitpunkt ausführbaren Tasks; gesperrte bzw. spec-gesteuerte Tasks (offene Spec-Gates Task 0/1/5/11 und deren Impl-Tasks 7/8/9/12, Task 2b bei positivem Machbarkeitsbefund) laufen in genau einem Nachfolge-PR der Phase D (max. 2 PRs je Phase). #1141 bleibt der letzte Teil (Entscheidung 35), ggf. im Nachfolge-PR. Trailer (z. B. `Co-Authored-By`) werden vom Task-Prompt wörtlich vorgegeben und vom Git-Agenten 1:1 übernommen (Entscheidung 25); der Plan selbst setzt keine Trailer.
- Kein `isolation: "worktree"` beim Spawnen von Subagenten.
- Commit- und PR-Texte ohne Closing-Keywords (Closes/Fixes/Resolves); Issues nur manuell nach Evidenz-Kommentar schließen (Entscheidung 38e).
- Echte Agenten-/Harness-Läufe (Task 3 Step 4, Task 4 Dry-Run) verbrauchen Modell-Tokens: nur nach Kostenschätzung und ausdrücklichem User-Ja.
- Destruktive Git-Befehle nie umgehen: blockiert der Guard (exit 2), liefert der Assistent den fertigen Befehl und der User führt ihn per `!` aus (Entscheidung 12).
- Tests: `python3 -m pytest <datei>::<test>`; Gesamtprüfung `python3 scripts/sync.py --validate`.
- `hooks/1-generic/orchestrator-guard-impl.sh` ist Sicherheitsdatei (Convention boundary, siehe `rules/1-generic/branch-guard.md`). Keine Schwächung des fail-closed-Verhaltens; jede Änderung läuft gegen `tests/test_orchestrator_guard_hook.py` und `tests/test_hook_drift.py`.
- Keine Implementierung vor `Status: APPROVED` der jeweiligen Spec (M/L/XL). Task 0 und Task 1 sind die Gates.
- Querverweis Entscheidung 12 (#946, Phase A): Der Löschpfad für Branches/Stash hängt vom Guard-Verhalten `exit 2` für destruktive Operationen ab (`orchestrator-guard-impl.sh:1384-1392`). #1217 ändert genau dieses Verhalten. Bis #1217 gemergt und freigegeben ist, bleibt exit 2 maßgeblich: der Assistent liefert fertige Befehle, der User führt sie per `!` aus.

## Klassifikation

| Issue | Klasse | Begründung | Spec |
|---|---|---|---|
| #1181 | L | öffentlicher Config-Contract + Schema, 16 Tasks | APPROVED (Rev. 1.4), Plan APPROVED. Referenz, nicht neu schreiben |
| #1210 | L | Security-Boundary, Payload-Feld, Fälschbarkeit | keine, Task 0 |
| #1217 | M | Verhaltensänderung im Guard, Hook-API-Frage offen | keine, Task 1 (nach Task 1a Hook-API-Prüfung) |
| #1172 | S | Doku/Template, kein Code | entfällt |
| #1176 | S | Template-Text + Test; End-to-End-Lauf manuell | entfällt |
| #1168 | S | Doku-Regel; Lint entfällt (Entscheidung 25 = D-neu-1) | entfällt |
| #1169 | M | Refactor einer Sicherheitsdatei, Benchmark | Task 5 (Mini-Spec-Gate) |
| #1141 | M | Config-Vertrag (Schema, unbekannte Top-Level-Keys), letzter Teil der PR nach #1181 (Entscheidung 35) | Task 11 (Spec-Gate), Task 12 (Impl) |

## File Structure

- Modify: `hooks/1-generic/orchestrator-guard-impl.sh` — #1181 T16 (Plan), #1169 (Single-Parse), #1210 (Rollenbindung), #1217 (ask-Pfad). Strikt sequentiell.
- Modify: `hooks/1-generic/lib/hook_common.sh` — #1169 neue Funktion `hook_json_get_many`; Version-/Changelog-Header (Zeile 3-5) anheben.
- Modify: `hooks/1-generic/repo-containment-impl.sh`, `hooks/1-generic/dod-push-check.sh` — nur #1169, falls Single-Parse übernommen wird (Task 6, optional).
- Create: `scripts/bench_hooks.py` — #1169 Benchmark (Median/p95, feste Payloads).
- Modify: `tests/test_hook_common_lib.py`, `tests/test_orchestrator_guard_hook.py` — Tests zu #1169, #1210, #1217.
- Create: `tests/test_hook_bench_script.py` — #1169 Benchmark-Skript-Test (nur Struktur, keine Wall-Clock-Assertion, siehe #1116).
- Modify: `rules/1-generic/use-orchestrator.md` (Abschnitt `## Git Delegation`, `:85-93`) — #1172 Merge-Muster.
- Modify: `agents/1-generic/orchestrator.md` (§7 BARRIER, Zeilen 258-276) — #1172 Merge-Hinweis, #1176 Wartestrategie.
- Modify: `agents/1-generic/git.md` (Abschnitt `## 4. Operation`, Zeile 52; Commit-Format Zeile 134-136) — #1172, #1168.
- Modify: `tests/test_orchestrator_worker_report_contract.py` — #1176 (Zeilen 90-99 prüfen bereits `SendMessage`/`TaskStop`).
- Create: `tests/test_git_template_commit_trailer_rule.py` — #1168.
- Create: `docs/specs/2026-11-11-guard-role-attribution-spec.md` — #1210 Spec (Task 0).
- Create: `docs/specs/2026-11-11-guard-destructive-ask-spec.md` — #1217 Spec (Task 1).
- Create: `docs/analysis/2026-11-11-hook-api-ask-permission.md` — Ergebnis der Hook-API-Prüfung (Task 1a).
- Create: `docs/specs/2026-11-11-config-unknown-keys-spec.md` — #1141 Spec (Task 11).
- Modify (nach Spec, nur nach Block A): `config/project-config.schema.json` — #1141 Schlüssel `rules-preset`, `test-repo`, `backup`, `mcp` (Task 12). Dazu Task 12: `scripts/admin-server.py` `_RUNTIME_ONLY_SECTIONS` und `tests/test_admin_whitelist_drift.py` (beide aus E-T4) auf 6 Einträge nachziehen. Gleiche Datei wie der #1181-Config-Vertrag (Klassifikation #1181 "öffentlicher Config-Contract + Schema").
- Modify: `scripts/lib/config.py` — #1141 neue Funktion `_warn_unknown_top_level_keys`, Aufruf in `_validate_config` (Task 12).
- Create: `tests/test_config_unknown_keys.py` — #1141 (Task 12).
- Modify (nur nach Spec): `rules/1-generic/branch-guard.md`, `rules/1-generic/a2a-delegation-gates.md` — #1210/#1217 Doku.

## Abweichung zur Roadmap

- **#1210, Zeilenanker:** Roadmap/Issue nennen `:262-269,418ff` bzw. `:419-480` und Gate `:1538-1555`. Im Code (`9aa0e0c0`, nachgemessen): `agent_id` wird bei `:262-269` gelesen; Sentinel-Parse `:326-349`; Sentinel-Zuordnung `:418-481`; Mutations-Gate `:1527-1547` (Bedingung `:1535`). Pfad im Issue: `hooks/1-generic/orchestrator-guard-impl.sh`, Roadmap sagt `orchestrator-guard-impl.sh` ohne Verzeichnis.
- **#1217, Zeilenanker:** Roadmap `:1383-1392` stimmt (`:1383` Kommentar, `:1384` Bedingung, `:1391` `exit 2`).
- **#1217, Referenz `docs/agent-templates/hooks/review-policy-gate.sh`:** existiert in `9aa0e0c0` nicht (`git ls-files` ohne Treffer, Glob `**/review-policy-gate.sh` ohne Treffer, Verzeichnis `docs/agent-templates/hooks` existiert nicht). Die Behauptung "das Repo nutzt `ask` bereits" ist damit nicht belegt. Im Repo kommen `hookSpecificOutput`/`permissionDecision` nur in `docs/providers/codex.md:143-145` (dort `deny`) und `docs/providers/kimi-code.md` vor, nicht für Claude.
- **#1176, Tools:** Issue sagt, #1157/#1162 hätten SendMessage, TaskStop und Monitor ergänzt. Belegt ist nur `primary-role-tools: [SendMessage, TaskStop]` (`config/ai-providers.yaml:133`) und der Template-Frontmatter `orchestrator.md:7-12` listet nur `TodoWrite, Agent, Read, Write`. `Monitor` wird in keiner Tool-Konfiguration für den Orchestrator vergeben (Grep `TaskStop` in `scripts/`, `config/` zeigt nur SendMessage/TaskStop). Die Wartestrategie "Monitor" aus dem Issue ist damit ohne Tool-Grant nicht ausführbar.
- **#1176, bereits gebaut:** BARRIER Schritt 6 (`orchestrator.md:266`) definiert einen Worker-Lauf ohne Report als `status: failed`; Zeile 276 beschreibt `TaskStop`. Das beantwortet Vorschlag 3 des Issues teilweise (Handback-Zustand für nicht berichtenden Worker). Offen bleibt Vorschlag 2 (eine einzige Wartestrategie für `run_in_background`) und der End-to-End-Nachweis.
- **#1168, Vorgabe-Trailer:** Das Issue spricht von "commit authority block" im Git-Template. `agents/1-generic/git.md` enthält weder `Co-Authored-By` noch `trailer` (Grep ohne Treffer in `git.md`, `rules/1-generic`, `hooks/1-generic`, `config`, `scripts/lib`). Es gibt keine im Framework vorgeschriebene Trailer-Zeile und keinen Konfigurationswert, gegen den ein Lint prüfen könnte. Der "vorgeschriebene" Wert kommt aus dem Task-Prompt des Aufrufers.
- **#1169, Spawn-Zahlen (statisch gezählt, `9aa0e0c0`):** Bash-Pfad ohne Sentinel, `project.yaml` vorhanden: Probe `hook_json_usable` (`:214`, ruft `hook_json_get`, `hook_common.sh:128-131`), JSON-Gültigkeitsprüfung `:231`, `hook_json_get` bei `:239` (tool_name), `:269` (agent_id), `:307` (command), `:384` (cwd), Sentinel-Parse `:326`, Git-Scan `:1330`, Strict-Config `:1419` = 9 Python-Starts. Zusätzlich nur bedingt: `:275`/`:280` (nur Tool `Agent`), Allowlist-Lookups `:450`, `:465` (nur mit Allowlist-Sentinel), Audit-Redaktion in `hook_audit_log_append` (`:500`, nur mit Sentinel). Die Issue-Zahl 9 passt zur statischen Zählung; Laufzeitmessung folgt in Task 6. `hook_json_get` steht in 28 Zeilen in 6 Dateien unter `hooks/1-generic` (inkl. Definition und Kommentare).

- **#1141, `_comment`:** Issue listet `_comment` als fehlend. Im Schema vorhanden (`config/project-config.schema.json:12`, Typ string). Keine Schema-Ergänzung nötig.
- **#1141, `rules-preset`, `test-repo`, `backup`:** belegt in `.meta-config/project.yaml:11`, `:294`, `:371` (Top-Level). Im Schema nicht vorhanden (Grep ohne Treffer in `config/project-config.schema.json`).
- **#1141, Leser (read-only gemessen):** `rules-preset` Skalar-String (`scripts/lib/rules.py:98`, `scripts/lib/sync_pipeline.py:194`, `scripts/lib/context_profile.py:116-117`); `test-repo` Mapping (`scripts/lib/cli_commands.py:133`, `:141`); `backup` Mapping (`scripts/lib/backup.py:48`).
- **#1141, `mcp`:** Entscheidung 5/35 nimmt `mcp` ins Schema auf (bindend). Im Repo steht `mcp:` nur verschachtelt unter `viz:` (`.meta-config/project.yaml:332`, gelesen in `scripts/admin-server.py:508` als `viz_cfg.get("mcp")`); ein Leser für Top-Level-`mcp` der Projekt-Config wurde nicht gefunden. Der Typ ist damit nicht aus einem Leser ableitbar; Task 11 legt ihn in der Spec fest, der User bestätigt ihn mit der Spec-Freigabe.
- **#1141, Schema bleibt offen:** Top-Level `additionalProperties: true` (`config/project-config.schema.json:2854`). Der Issue-Vorschlag `additionalProperties: false` entfällt (Entscheidung 35).
- **#1141, jsonschema-Gate:** Die bestehende Schema-Prüfung in `_validate_config` (`scripts/lib/config.py:676-685`) läuft nur mit installiertem `jsonschema` und meldet bei `additionalProperties: true` keine unbekannten Top-Level-Schlüssel. Die neue Warnung läuft stdlib-only vor diesem Gate.

## Reihenfolge und Abhängigkeiten

```
Strom A (#1181):   Phase F (#1188) fertig  -->  Plan-Block T1..T16 (Referenz)  -->  Gate G-A   (Entscheidung 19)
Strom B (Doku):    Task 2a (#1172 Machbarkeit + Spec-Gate, Entscheidung 47) -> Task 2 (#1172 Doku, Fallback) -> [Task 2b bedingt] -> Task 3 (#1176) -> Task 4 (#1168, Entscheidung 25 beantwortet)
Strom C (Hooks):   Task 1a -> Task 1 (Spec #1217 Gate)
                   Task 0 (Spec #1210 Gate)
                   Task 5 (Spec-Gate #1169) -> Task 6 (#1169 Bench) -> Task 7 (#1169 Single-Parse)
                   -> Task 8 (#1210 Impl) -> Task 9 (#1217 Impl)
Strom D (#1141):   Block A (Gate G-A, letzter Task T14) -> Task 9 -> Task 11 (Spec-Gate) -> Task 12 (Impl), letzter Teil der Phase-D-PR (Entscheidung 35)
```

- Strom A startet erst nach Phase F (#1188); Kette #1187 -> #1186 -> #1188 -> #1181 -> #1141 (Entscheidung 19). Strom C nach Strom A: #1181 T16 (`orchestrator-guard-impl.sh`, Plan `:1139`) läuft zuerst, danach Task 7/8/9 (gleiche Datei, nie parallel).
- Strom B ist dateidisjunkt zu A und C: die File-Structure-Map des #1181-Plans (`docs/plans/2026-11-09-commit-authority-grant-plan.md:279-314`) nennt weder `agents/1-generic/orchestrator.md`, `git.md` noch `rules/1-generic/use-orchestrator.md`. Aber: #1181-T14 Step 4 und §11 AC-1 verlangen `git diff --name-only aaed14c2..HEAD -- agents/` leer (Referenzplan `:1087`, `:1488`, `:1501`). Das ist schon auf origin/main falsch (`git diff --name-only aaed14c2..9aa0e0c0 -- agents/` listet `agents/1-generic/_reference-agent.md`, `agents/1-generic/orchestrator.md`) und würde durch Task 2/3/4 erneut gebrochen. Deshalb: Step A1 ersetzt die Basis `aaed14c2` per Änderungsnotiz durch den Commit direkt vor T1 (A-Start), und Strom-B-Commits liegen nie zwischen A-Start und T14 (entweder vollständig vor A-Start oder nach Gate G-A).
- Phasen C, E und F laufen vor D und ändern u.a. `scripts/lib/config.py`, `config/project-config.schema.json` (E) und `rules/1-generic/use-orchestrator.md` (C). Alle Zeilenanker dieses Plans vor Ausführung neu messen (Freshness-Check gegen den dann aktuellen origin/main).
- Phase-Abhängigkeit (Roadmap Welle 3): Phase C (Guard-Pfade, `hooks.py`) vor D. Task 1a und die Specs (Task 0, 1) dürfen vorher laufen (reine Dokumente).

---

### Task 0: Spec #1210 schreiben + Freigabe-Gate (Spec-Gate)

**Role:** `concept-specifier` (Spec), `concept-reviewer` (Review), User-Freigabe.
**Files:** Create `docs/specs/2026-11-11-guard-role-attribution-spec.md`.
**Interfaces:** Consumes Issue #1210, Entscheidung 2 (Harness-Feld, Rolle aus dem Hook-Payload; bindend nur bei positiver Evidenz, siehe Entscheidungen (beantwortet) Punkt 8, Entscheidung 38a), Spec-Abschnitt #1181 §3.3.1/D18. Produces freigegebene Spec, Voraussetzung für Task 8.

- [ ] Step 1: Payload-Evidenz sammeln. Frage: Liefert ein PreToolUse-Payload ein Rollenfeld (z. B. `agent_type`), außer `agent_id`? Im Repo belegt: nur `agent_id` (`orchestrator-guard-impl.sh:262-269`, Capability `hook-agent-id`, `config/ai-providers.yaml:64`). Ein Rollenfeld ist im Repo nicht belegt. Externe Claude-Code-Hook-Doku (code.claude.com, im Guard `:265` zitiert) lesen und Feldname, Auslöser und Fälschbarkeit (kann ein Subagent das Feld beeinflussen?) dokumentieren.
- [ ] Step 2: Spec-Abschnitte schreiben: Payload-Feld (Name, Quelle), Fälschbarkeit (Threat-Model: Subagent mit Bash schreibt `#agent-meta:agent=<role>`, `:333`), Fallback bei fehlendem Feld (Provider ohne Feld: Sentinel bleibt wie heute, ausdrücklich als Convention boundary, nicht Security boundary, Terminologie `rules/1-generic/branch-guard.md`), Fail-Verhalten (Feld vorhanden und != Sentinel-Rolle: Reject mit Grund, `git`-Sentinel-Pfad unverändert, AC-3 aus #1210), Capability-Flag statt Provider-Name (analog `hook-agent-id`), Testmatrix.
- [ ] Step 3: Review durch `concept-reviewer`; Findings einarbeiten.
- [ ] Step 4: User-Freigabe einholen. Erst dann `Status: APPROVED` setzen.
- Akzeptanz: Datei existiert, enthält je einen Abschnitt zu Payload-Feld, Fälschbarkeit, Fallback, Reject-Meldung, Testmatrix; Kopf `Status: APPROVED` nur nach User-Ja; `python3 scripts/sync.py --validate` Exit 0.
- Wenn die Evidenz zeigt, dass kein vertrauenswürdiges Rollenfeld existiert: Spec dokumentiert das und setzt D-neu-4 (Entscheidung 34) um: Convention boundary dokumentieren (Option 3 des Issues). Option 2 (Secret) entfällt. Das Ergebnis ist erst nach Step 1 final und nur bei negativer Evidenz; danach bestätigt der User erneut (Entscheidung 38a).
- [ ] Step 5: commit `docs: spec guard role attribution via payload field (#1210)`

### Task 1a: Hook-API-Prüfung `ask` vs. exit 2 (Vorbedingung für Task 1)

**Role:** `provider-expert` (liest Provider-Doku/Config), Ergebnis geht an `concept-specifier`.
**Files:** Create `docs/analysis/2026-11-11-hook-api-ask-permission.md`. Lesen: `docs/providers/*.md`, `config/ai-providers.yaml`, `config/provider-capabilities.yaml`. (`hooks/component-config.yaml` aus Issue #1210 existiert auf `9aa0e0c0` nicht; Capability-Flags stehen in `config/ai-providers.yaml`, z. B. `hook-agent-id` `:64`.)
**Interfaces:** Produces Entscheid "ask unterstützt: ja/nein/teilweise je Provider" mit Quellen. Consumes Entscheidung 1 (ask-Permission).

- [ ] Step 1: Im Repo suchen, welche Provider-Doku `permissionDecision` kennt: bisher nur `docs/providers/codex.md:143-145` (deny) und `docs/providers/kimi-code.md`. Für Claude Code keine Repo-Doku. Ergebnis tabellarisch festhalten.
- [ ] Step 2: Externe Claude-Code-Hook-Doku lesen (nicht im Repo): Wird `hookSpecificOutput.permissionDecision: "ask"` für Bash/PreToolUse unterstützt? Verhalten im Non-Interactive/Headless-Modus (fail closed gewünscht, #1217 AC-3)? Quelle mit URL und Abrufdatum eintragen. Wenn nicht erreichbar: als "nicht verifiziert" festhalten, nicht raten.
- [ ] Step 3: Prüfen, ob ein Hook sowohl JSON-`ask` auf stdout als auch `exit 2` kombinieren kann (Exit-Code 0 + JSON vs. Exit 2 + stderr; Claude liest bei exit 2 stderr, `orchestrator-guard-impl.sh:45`). Ergebnis festhalten.
- [ ] Step 4: Wenn `ask` nicht oder nur teilweise unterstützt: Ergebnis an User/`main_chat` als neue Entscheidung melden (Entscheidung 1: "bei fehlendem Support Spec überarbeiten, nicht erzwingen").
- Akzeptanz: Analyse-Datei enthält je Provider-Zeile (`claude`, `codex`, ...) die Spalten "ask", "Quelle", "Headless-Verhalten" mit Wert `ja|nein|unbekannt`; keine Zelle leer; kein Wert ohne Quelle.
- [ ] Step 5: commit `docs: analyze hook API ask permission support (#1217)`

### Task 1: Spec #1217 schreiben + Freigabe-Gate (Spec-Gate)

**Role:** `concept-specifier`, `concept-reviewer`, User-Freigabe. Abhängig von Task 1a.
**Files:** Create `docs/specs/2026-11-11-guard-destructive-ask-spec.md`.
**Interfaces:** Consumes Task 1a Ergebnis, Issue #1217, `orchestrator-guard-impl.sh:895` (`is_destructive`), `:1384-1392` (Gate), `:496` (Audit-Log-Pfad `.claude/hooks/.guard-audit.log`). Produces Spec für Task 9.

- [ ] Step 1: Spec gliedern: (a) Klassen: immer-hart (`reset --hard`, `clean -fd`, `filter-branch`, Working-Tree-Wipe, Force-Push auf Default-Branch, `is_fs_destructive` `:1262`, Fork-Bombe `forkbomb`) vs. ask-Klasse (`branch -D`, `push --delete`, PR-gemergte Branches); (b) Entscheidungsausgabe `ask` mit vollständigem Befehl; (c) Headless fail closed; (d) Audit-Zeilen für ask/approve/deny; (e) Sentinel kann nie approven; (f) Interaktion mit Entscheidung 12 (#946); (g) Provider-Matrix aus Task 1a; für Provider ohne `ask` bleibt `exit 2`.
- [ ] Step 2: Frage klären, ob ein Hook eine "approved" Entscheidung überhaupt sieht (bei `ask` entscheidet der Harness, der Hook läuft vorher). Audit-Eintrag "approved/denied" ist nur möglich, wenn ein PostToolUse-Signal vorliegt. Wenn nein: Spec begrenzt Audit auf "asked" und dokumentiert das; nicht erfinden.
- [ ] Step 3: Review `concept-reviewer`; Freigabe User; `Status: APPROVED`.
- Akzeptanz: Spec enthält Tabelle "Operation -> Klasse -> Ausgabe (ask/exit 2)" mit mindestens den Fällen `git branch -D`, `git push origin --delete`, `git reset --hard`, `git clean -fd`, Force-Push auf `main`; ein Abschnitt "Headless"; ein Abschnitt "Audit"; Kopf `Status: APPROVED` erst nach User-Ja.
- [ ] Step 4: commit `docs: spec guard destructive ask approval path (#1217)`

---

### Block A: #1181 Ausführung des bestehenden Plans (keine Neuplanung)

**Referenz:** `docs/plans/2026-11-09-commit-authority-grant-plan.md` (APPROVED, Rev. 1.4, 16 Tasks T1..T16, Spec `docs/specs/2026-11-09-commit-authority-grant-spec.md` APPROVED). Der Plan trägt Basis `aaed14c2`; er ist gegen den dann aktuellen origin/main (heute `9aa0e0c0`) zu aktualisieren.

**Role:** wie im Plan je Task (Ausführung über Pipeline `feature-lifecycle` mit `payload.plan_ref`).
**Files / Interfaces:** vollständig im Referenzplan, §4 File-Structure-Map `:279` und §7 Interfaces `:1200`. Dieser Plan dupliziert sie nicht.
**Ausführungsreihenfolge (Plan `:60`):** T1 -> T15 -> T2 -> T3 -> T4 -> T5 -> T6 -> T7 -> T8 -> T9 -> T16 -> T10 -> T11 -> T12 -> T13 -> T14.

- [ ] Step A1 (Freshness, vor Start): Alle `datei:zeile`-Anker des Referenzplans gegen origin/main prüfen (z. B. `scripts/lib/auto_commit.py:127-153`, `scripts/lib/sync_pipeline.py:1894`, `scripts/lib/provider_transform.py:854-870`, `config/ai-providers.yaml:230-251`). Abweichungen als Änderungsnotiz in den Referenzplan, nicht den Plan neu schreiben. Hinweis: Roadmap-Basis ist `a41745ed` bzw. `a3d65da4`, Plan-Basis `aaed14c2` (v2.0.0-beta.8). Seit dem Plan wurde u.a. die Orchestrator-Topologie (#1190, PR #1215/#1216) geändert, die `orchestrator.md` und `hooks.py` berührt. Nicht geprüft, ob das T5/T8/T16 betrifft. Nach Rebase auf origin/main `9aa0e0c0` (PR #1218 inkl. Topologie-Arbeit) Zeilenanker und Plan-Passung erneut prüfen (Roadmap nennt Plan-Basis `aaed14c2`). Pflicht-Änderungsnotiz: AC-1-/N-9-Prüfung (`:1087`, `:1488`, `:1501`) nutzt den A-Start-Commit statt `aaed14c2` (siehe Reihenfolge und Abhängigkeiten).
- [ ] Step A2: Reihenfolge (Entscheidung 19, beantwortet): Kette `#1187 -> #1186 -> #1188 -> #1181 -> #1141` (Referenzplan `:17`). #1141 verlässt Phase C (Welle 2) und folgt auf #1188 (Phase F). Strom A startet erst nach Phase F. Roadmap-Wellen anpassen (Entscheidung 35: Phase C = 11 Issues, F = 6 Issues, D = 8 Issues, Summe 89). Ob #1187 umgesetzt ist, prüft die E/F-Planung als Check-Task, nicht dieser Plan.
- [ ] Step A3: T1..T16 gemäß Referenzplan ausführen, ein Commit pro Task (Subjects im Referenzplan).
- Akzeptanz (Gate G-A): Referenzplan-Abschnitt §11 (AC -> Task) vollständig abgehakt; `python3 scripts/sync.py --validate` Exit 0; `python3 -m pytest tests/test_orchestrator_guard_hook.py` grün; kein Render-Diff gegenüber Baseline ohne `authority_overrides` bis auf Allowlist `version: 2` (Plan `:77-79`).

**Abweichung zur Roadmap (#1181):** Roadmap Phase D (Welle 3) hängt von "#1181 braucht freigegebene Spec"; die Spec ist bereits APPROVED. Ob die Spec-/Plan-Freigabe noch aktuell ist (Basis `aaed14c2` vs. origin/main `9aa0e0c0`), nicht verifiziert. Reihenfolge-Konflikt mit Phase F (#1188) durch Entscheidung 19 gelöst (Strom A nach F).

---

### Task 2a: #1172 Machbarkeit Permission-Regel für den `git`-Agenten (Entscheidung 47, zuerst)

**Role:** `se-architect` (Befund), `concept-specifier` + `concept-reviewer` (Spec), User-Freigabe.
**Files:** Create `docs/specs/2026-11-11-git-agent-merge-permission-spec.md` (nur bei positivem Befund aus Step 1-2; sonst Befund als Issue-Kommentar-Entwurf unter `.tmp/`).
**Interfaces:** Consumes Issue #1172 Vorschlag 3, Entscheidung 47. Produces Machbarkeitsbefund (ja/nein je Provider, mit file:line) und, bei ja, eine Spec für Task 2b.

- [ ] Step 1: Evidenz im Repo am Ausführungsstand sammeln (Vorbefund `9aa0e0c0`, nicht abschließend): Rollen-Override `permission-mode-overrides` (`config/project-config.schema.json:518-520`, "Override the default permissionMode per role"); `subagent_permissions` (`config/project-config.schema.json:1617`, nur warn/strict-Politik für Dispatches); Provider-Flag `inject-permission-mode` (`config/ai-providers.yaml:127`); Settings-Key `permissions.additionalDirectories` (`config/ai-providers.yaml:82`); Module `scripts/lib/permissions.py`, `scripts/lib/subagent_permissions.py`. Frage je Provider: Lässt sich darüber eine Allow-Regel erzeugen, die NUR für den `git`-Agenten einen Merge (`gh pr merge`/`git merge`) freigibt? Ergebnis mit file:line; was nicht belegbar ist, als "nicht verifiziert" führen.
- [ ] Step 2: Externe Grenze prüfen: Der in #1172 beobachtete Block kommt vom Claude-Code-Auto-Mode-Classifier (außerhalb des Repos). Ob eine Repo-generierte Permission-Regel den Classifier überhaupt beeinflusst, mit Quelle (URL, Abrufdatum) belegen; sonst "nicht verifiziert", nicht raten.
- [ ] Step 3: Security Boundary bewerten: Die Regel erweitert Rechte (Merge ohne Review-Gate). Spec muss festlegen, dass sie rollengebunden ist (nur `git`), provider-agnostisch über Config-Key/Capability-Flag ausgedrückt wird (kein `if provider == ...`), die Merge-Policy (#783) nicht unterläuft und Branch-Guard/DoD-Push-Check unberührt bleiben. Einstufung Convention vs. Security Boundary nach `.claude/rules/branch-guard.md` angeben.
- [ ] Step 4 (Spec-Gate): Bei positivem Befund Spec schreiben, `concept-reviewer`-Review, User-Freigabe; erst dann `Status: APPROVED` und Task 2b entsperrt. Bei negativem Befund: kein Spec, Task 2b entfällt, Befund im Issue-Kommentar (#1172) festhalten; Fallback ist der in Task 2 dokumentierte Merge-Pfad.
- [ ] Step 5: commit (nur bei Spec) `docs: spec git agent merge permission rule (#1172)`
- Akzeptanz: Befund je Provider mit file:line oder "nicht verifiziert"; Security-Boundary-Abschnitt vorhanden; Spec nur mit User-Ja auf APPROVED.

### Task 2: #1172 Merge-Muster dokumentieren (S, Fallback-Pfad)

**Role:** `developer`.
**Files:** Modify `rules/1-generic/use-orchestrator.md` (`## Git Delegation`, `:85-93`), `agents/1-generic/orchestrator.md` (§7, `:258-276`), `agents/1-generic/git.md` (`## 4. Operation`, `:52-62`). Test: Create `tests/test_merge_pattern_docs.py`.
**Interfaces:** Consumes Issue #1172 (Beobachtung: Auto-Mode-Classifier blockiert Merge über orchestrator -> git, Main Chat -> git funktioniert; Classifier liegt außerhalb des Repos, nicht reproduziert). Produces eine gerenderte Regel in drei Templates.

- [ ] Step 1: Failing Test `tests/test_merge_pattern_docs.py::test_merge_pattern_in_three_templates`. Rendert die drei Dateien (gleiches Hilfsmittel wie `tests/test_orchestrator_worker_report_contract.py`, Struktur dort ansehen) und asserted je Datei: der Text enthält den Issue-Verweis `#1172` und den Verweis `#783`, im gerenderten Rule-Text genau einmal. Erwartung vor der Änderung: FAIL (heute kein Treffer für `#1172` in den drei Dateien).
- [ ] Step 2: Text einfügen. Inhalt (ohne Fantasiebehauptung): Merges freigegebener PRs werden vom Main Chat direkt an den `git`-Agenten dispatched; der Weg orchestrator -> git wurde in einem Audit (2026-11-06) vom Claude-Code-Auto-Mode-Classifier als "Merge Without Review" blockiert, auch nach User-Freigabe im Main Chat; Ursache liegt außerhalb dieses Repos und ist nicht reproduziert. Dieser Pfad bleibt Fallback (Entscheidung 47); die Permission-Regel für den `git`-Agenten wird nur mit Verweis auf das Ergebnis von Task 2a erwähnt (gebaut in Task 2b oder als nicht machbar belegt). Verweis auf #783 (Merge-Policy, offen, Phase I).
- [ ] Step 3: Pro Template in `{{#if ROLE_GIT_ACTIVE}}` rendern (bestehende Variable, `use-orchestrator.md:87`). Achtung: `:87` liegt innerhalb `{{#unless AUTO_COMMIT_ENABLED}}` (`:86-88`); dieses Repo rendert den `AUTO_COMMIT_ENABLED`-Zweig (`:89-91`). Den Absatz deshalb außerhalb beider Zweige einfügen (nach `:92`), sonst fehlt er im gerenderten `.claude/rules/use-orchestrator.md` und die Akzeptanz unten schlägt fehl.
- [ ] Step 4: Test PASS: `python3 -m pytest tests/test_merge_pattern_docs.py::test_merge_pattern_in_three_templates`; `python3 scripts/sync.py --validate` Exit 0.
- [ ] Step 5: commit `docs: document supported merge dispatch pattern (#1172)`
- Akzeptanz (messbar): die drei Quelldateien enthalten den Merge-Absatz; gerendertes `.claude/rules/use-orchestrator.md` nach `python3 scripts/sync.py` enthält ihn (Grep Treffer = 1). Issue-AC 3 ("Doc states orchestrator path blocked ... observed reason") durch den Satz zum Audit erfüllt.
- Issue Vorschlag 3 ("permission rule scoped to git agent"): beantwortet durch Entscheidung 47 (bauen); Machbarkeit in Task 2a, Umsetzung bedingt in Task 2b.

### Task 2b: #1172 Permission-Regel für den `git`-Agenten bauen (bedingt, nach Task 2a APPROVED)

**Role:** `developer`. **Voraussetzung:** Task 2a mit positivem Befund und Spec `Status: APPROVED`. Sonst entfällt der Task (Fallback Task 2). Spec-gesteuert, daher Nachfolge-PR der Phase D (Entscheidung 52).
**Files:** laut Spec aus Task 2a (Kandidaten aus dem Vorbefund: `config/project-config.schema.json`, `config/ai-providers.yaml`, `scripts/lib/permissions.py`); Test: Create `tests/test_git_agent_merge_permission.py`.
**Interfaces:** Consumes Spec Task 2a. Produces die generierte, rollengebundene Regel; Ausdruck über Config-Key/Capability-Flag, keine Provider-Verzweigung.

- [ ] Step 1: Failing Tests laut Spec-Testmatrix: Regel nur im generierten Artefakt der `git`-Rolle; keine andere Rolle erhält sie; Provider ohne Capability erhält keine Regel (Fallback-Doku bleibt).
- [ ] Step 2: Minimal-Implementierung laut Spec (Python 3.9-kompatibel, stdlib + PyYAML).
- [ ] Step 3: `python3 -m pytest tests/test_git_agent_merge_permission.py tests/test_merge_pattern_docs.py`; `python3 scripts/sync.py --validate` Exit 0.
- [ ] Step 4: commit `feat: scope merge permission rule to git agent (#1172)`
- Akzeptanz: Spec-AC erfüllt; keine Änderung an Branch-Guard/DoD-Push-Check; Merge-Pfad aus Task 2 bleibt dokumentiert.

### Task 3: #1176 Wartestrategie für async Sub-Agents (S)

**Role:** `developer`.
**Files:** Modify `agents/1-generic/orchestrator.md` (§7, Zeilen 258-277; Version im Frontmatter `:3` anheben, aktuell `"8.12.0"`). Modify `tests/test_orchestrator_worker_report_contract.py` (bestehende Assertions `:90-99`).
**Interfaces:** Consumes `primary-role-tools: [SendMessage, TaskStop]` (`config/ai-providers.yaml:133`), BARRIER Schritt 6 (`orchestrator.md:266`). Produces dokumentierte Wartestrategie (eine) + Timeout-Pfad.

- [ ] Step 1: Failing Test in `tests/test_orchestrator_worker_report_contract.py`: `test_orchestrator_documents_single_async_wait_strategy` asserted, dass §7 (a) genau einen Satz "Wait strategy" enthält, (b) den Timeout-Pfad `TaskStop` + `STATUS: failed` nennt, (c) verbietet, den Turn beim Warten auf `run_in_background`-Worker zu beenden. Erwartung: FAIL.
- [ ] Step 2: Text in §7 ergänzen. Wegen Abweichung (Monitor ist nicht gewährt) nur Strategien beschreiben, deren Tools vorhanden sind: blockierender Dispatch (Issue #265, bereits `:276`) als Standard; für Hintergrund-Worker Ergebnis über `SendMessage`/Task-Output einsammeln; bei Timeout `TaskStop` + Eintrag `status: timeout`/`failed` (BARRIER-Wrapper `status ∈ success | failed | timeout`, `:262`). `Monitor` wird nicht genannt und nicht gewährt (D-neu-3 = Entscheidung 34: nur dokumentieren).
- [ ] Step 3: Test PASS: `python3 -m pytest tests/test_orchestrator_worker_report_contract.py::test_orchestrator_documents_single_async_wait_strategy`; Regressionslauf `python3 -m pytest tests/test_orchestrator_worker_report_contract.py tests/test_orchestrator_compact_sections.py`.
- [ ] Step 4: End-to-End-Nachweis (Issue-AC 1) ist ein manueller Harness-Lauf, nicht per pytest erzeugbar. Erst nach Kostenschätzung und User-Ja (Global Constraints). Protokoll der Beobachtung (Dispatch, Wait, Result, Handback) in den Issue-Kommentar, nicht ins Repo. Wenn der Harness weiterhin vorzeitig zurückgibt: Issue bleibt offen mit Verweis, Phase D schließt nur den Doku-Teil.
- [ ] Step 5: commit `docs: define async sub-agent wait strategy in orchestrator (#1176)`
- Akzeptanz: Test grün; gerendertes Orchestrator-Template (`python3 scripts/sync.py`, Grep `Wait strategy`) enthält genau einen Treffer; Issue-AC 3 "Timeout path tested" nur soweit als Text-Test (Verhalten im Harness nicht testbar, siehe Nicht verifiziert).

### Task 4: #1168 Trailer-Vorrang dokumentieren (S, nach Entscheidung)

**Role:** `developer`. **Voraussetzung:** Entscheidung 25 (= D-neu-1) beantwortet: Task-Prompt-Trailer gewinnt, Git-Agent übernimmt ihn wörtlich. Nicht mehr blockiert.
**Files:** Modify `agents/1-generic/git.md` (nach `:136`, "No leading BOM"-Absatz, neuer Absatz "Commit trailers"); Create `tests/test_git_template_commit_trailer_rule.py`.
**Interfaces:** Consumes Entscheidung 25. Produces Vorrangregel an einer Stelle, vom Git-Template referenziert.

- [ ] Step 1: Failing Test `tests/test_git_template_commit_trailer_rule.py::test_git_template_states_trailer_precedence` (Rendern von `agents/1-generic/git.md`, Assert: der gerenderte Text enthält genau einmal `Co-Authored-By` und im selben Absatz das Wort `verbatim`). FAIL (heute 0 Treffer für `Co-Authored-By` in `git.md`).
- [ ] Step 2: Absatz in `git.md` einfügen. Regel (verbindlich, Entscheidung 25): Der Git-Agent übernimmt eine im Task-Prompt wörtlich vorgegebene `Co-Authored-By`-Zeile 1:1 und leitet nie einen Modellnamen aus der eigenen Session ab.
- [ ] Step 3: Test PASS: `python3 -m pytest tests/test_git_template_commit_trailer_rule.py::test_git_template_states_trailer_precedence`.
- [ ] Step 4: Kein Lint im Guard. Begründung: es gibt keinen konfigurierten Soll-Wert (kein Key in `config/` oder `scripts/lib/`, Grep ohne Treffer), der Guard sieht nur die Bash-Kommandozeile, und der Soll-Wert steht nur im Task-Prompt. Ein Lint würde einen neuen Konfig-Key erfordern; Entscheidung 25 wählt Option (a): ohne Key, ohne Lint.
- [ ] Step 5: commit `docs: define commit trailer precedence for git agent (#1168)`
- Akzeptanz: Test grün; `rules`/Template enthalten die Regel an genau einer Stelle (Grep-Zähler 1 im gerenderten `git.md`); Issue-AC 2 ("commit carries exactly that trailer, verified in test or dry run") wird per Text-Test NICHT erfüllt, sondern nur per Dry-Run mit echtem Git-Agenten-Dispatch (erst nach Kostenschätzung und User-Ja). Das als Rest im Issue-Kommentar benennen.

---

### Task 5: Spec-Gate #1169 (Mini-Spec)

**Role:** `concept-specifier`. M-Klasse (Sicherheitsdatei, Refactor).
**Files:** Create `docs/specs/2026-11-11-hook-single-parse-spec.md`.
**Interfaces:** Consumes `hook_common.sh:63-110` (`hook_json_get <json-string> <dotted.path> [default]`, Kommentar `:52`), `:128-131` (`hook_json_usable`), Aufrufer: Guard `:239,:269,:275,:280,:307,:384`; JSON-Gültigkeitsprüfung `:231` (eigener Python-Start).

- [ ] Step 1: Spec legt fest: neue Funktion `hook_json_get_many <json> <path>...` (ein Interpreter-Start, NUL-getrennte Ausgabe, Konsum per `while IFS= read -r -d '' f` ohne `mapfile` und ohne `eval`, wegen bash 3.2; Entscheidung 28), Fail-Closed-Semantik identisch zu `hook_json_get` ohne `default`-Argument (Parsefehler, nicht auflösbarer Pfad, Objekt/Array, fehlender Interpreter: leeres Feld), NUL-Regel: ein Wert, der ein NUL-Zeichen (`\u0000`) enthält, darf die Feldzuordnung nicht verschieben (sonst könnte z. B. `tool_input.command` den Wert von `cwd` fälschen); Spec legt fest: ganzer Aufruf schlägt fehl und der Guard blockiert (fail closed), Surrogate-/Byte-Regeln aus v1.0.1 (Changelog `hook_common.sh:5`) unverändert, `hook_json_usable` bleibt (Probe, 1 Spawn).
- [ ] Step 2: Spec legt fest: Zielgröße. Ziel: Bash-Pfad im Guard von 9 (statisch gezählt, siehe Abweichung #1169) auf höchstens 5 Spawns (Probe + 1 Mehrfeld-Parse inkl. JSON-Gültigkeitsprüfung `:231` + Sentinel + Git-Scan + Strict-Config). Die Spec entscheidet, ob `:231` in den Mehrfeld-Parse wandert; ohne das sind es 6. Messwert per Benchmark (Task 6), nicht per Annahme.
- [ ] Step 3: Review; User-Freigabe der Spec vor jeder Implementierung (Entscheidung 28); Abstimmung mit Phase H (#1161, Punkt 5), damit die Funktion nicht doppelt entsteht; `Status: APPROVED` erst nach User-Ja.
- Akzeptanz: Spec enthält Funktionssignatur, Fehlerverhalten-Tabelle (Parsefehler, fehlender Interpreter, nicht-skalarer Wert, ungültiges UTF-8, NUL im Wert) und messbares Spawn-Ziel; Kopf `Status: APPROVED`.
- [ ] Step 4: commit `docs: spec single-parse hook JSON extraction (#1169)`

### Task 6: #1169 Benchmark-Skript (Baseline zuerst)

**Role:** `developer`. Abhängig von Task 5 (Spec APPROVED).
**Files:** Create `scripts/bench_hooks.py`, `tests/test_hook_bench_script.py`; Create `docs/hook-latency-baseline.md` (Messwerte, Methode).
**Interfaces:** Produces `python3 scripts/bench_hooks.py --runs N --json` mit Ausgabe `{"payload": "bash-simple", "median_ms": float, "p95_ms": float, "python_spawns": int}`. Python-Spawns gezählt über einen `PATH`-Shim `python3` (Wrapper, zählt Aufrufe in eine Datei, ruft das echte Python), kein Wall-Clock-Assert im Test (Trap aus #1116).

- [ ] Step 1: Failing Test `tests/test_hook_bench_script.py::test_bench_reports_spawn_count_for_fixed_payloads`: ruft `scripts/bench_hooks.py --runs 1 --json` auf, asserted Schlüssel `median_ms`, `p95_ms`, `python_spawns` je Payload (`bash-simple`, `read-simple`) und `python_spawns >= 1`. Keine Zeitgrenze.
- [ ] Step 2: Skript implementieren (stdlib, Python 3.9). Feste Payloads aus `tests/test_orchestrator_guard_hook.py::_run_hook`-Helfer (`:110`) ableiten, gegen `hooks/1-generic/orchestrator-guard-impl.sh` mit gebackenem Platzhalter (siehe `_run_rendered` `:163`).
- [ ] Step 3: Test PASS: `python3 -m pytest tests/test_hook_bench_script.py::test_bench_reports_spawn_count_for_fixed_payloads`.
- [ ] Step 4: Baseline lokal messen, Zahlen in `docs/hook-latency-baseline.md` (Median, p95, Spawn-Zahl). Messung läuft nicht in CI.
- [ ] Step 5: commit `feat: add hook latency benchmark script (#1169)`
- Akzeptanz: `python3 scripts/bench_hooks.py --runs 5 --json` liefert gültiges JSON mit Spawn-Zahl für `bash-simple` (Baseline-Wert im Baseline-Dokument festgehalten, kein Sollwert vorab).

### Task 7: #1169 Single-Parse im Guard und in `hook_common.sh`

**Role:** `senior-developer`. Abhängig von Task 6 und Block A (T16 des #1181-Plans fertig: gleiche Datei).
**Files:** Modify `hooks/1-generic/lib/hook_common.sh` (neue Funktion, Header-Version `1.9.0` -> `1.10.0`, Changelog-Zeile), `hooks/1-generic/orchestrator-guard-impl.sh` (Aufrufe `:239,:269,:307,:384` auf eine gemeinsame Extraktion), Tests `tests/test_hook_common_lib.py`, `tests/test_orchestrator_guard_hook.py`.
**Interfaces:** Produces `hook_json_get_many <json> <path>...` (Ausgabe: je Pfad ein NUL-terminiertes Feld, in Argument-Reihenfolge; nicht auflösbar oder Objekt/Array: leeres Feld). Consumes Spec aus Task 5.

- [ ] Step 1: Failing Tests in `tests/test_hook_common_lib.py`: `test_hook_json_get_many_matches_single_gets` (gleiche Werte wie 4 Einzelaufrufe für `tool_name`, `agent_id`, `tool_input.command`, `cwd`), `test_hook_json_get_many_keeps_newlines_in_command`, `test_hook_json_get_many_invalid_json_returns_defaults`, `test_hook_json_get_many_single_python_spawn` (PATH-Shim zählt genau 1 Aufruf), `test_hook_json_get_many_nul_in_value_cannot_shift_fields` (Payload `{"tool_input":{"command":"a\u0000/evil"},"cwd":"/ok"}`: Verhalten laut Spec, `cwd` nie `/evil`). Mustern: bestehende Tests der Datei für `hook_json_get`. FAIL.
- [ ] Step 2: Implementierung in `hook_common.sh`: ein `"$py" -c`, Bytes-in/Bytes-out wie `hook_json_get` (`:77-109`), NUL-Trenner, gleiche Surrogate-Behandlung.
- [ ] Step 3: Guard umstellen: Reihenfolge der Vorbedingungen unverändert lassen (Probe `hook_json_usable` vor jeder Feldnutzung, `:214-218`; Fail-Closed bei leerem `tool_name` `:245`, unbekanntem `:255`). Nur Feld-Lesen zusammenfassen. Keine neue Fail-Open-Kante.
- [ ] Step 4: Regression: `python3 -m pytest tests/test_hook_common_lib.py tests/test_orchestrator_guard_hook.py tests/test_hook_drift.py tests/test_repo_containment_hook.py tests/test_dod_push_check_hook.py`; erwartet alle grün (Anzahl vor und nach vergleichen; bestehende Tests nicht anfassen).
- [ ] Step 5: Benchmark erneut: Spawn-Zahl für `bash-simple` fällt gegenüber Baseline (Task 6) um mindestens 3. Ziel-Wert und Ist-Wert im PR-Text nennen; Median-Latenz gegen Baseline (kein CI-Assert).
- [ ] Step 6: commit `perf: parse hook JSON once per call in orchestrator guard (#1169)`
- Akzeptanz: alle genannten Testdateien grün; Spawn-Zahl laut Benchmark <= Baseline minus 3; `python3 scripts/sync.py --validate` Exit 0; `tests/test_hook_drift.py` grün (gerenderte Hooks synchron).
- Optional (separater Commit, nur wenn Spec es vorsieht): `repo-containment-impl.sh` (5 `hook_json_get`-Aufrufe) und `dod-push-check.sh` (2) auf dieselbe Funktion umstellen. Eigener Task-Commit `perf: reuse single-parse helper in containment and push hooks (#1169)`.

### Task 8: #1210 Rollenbindung des Sentinels (L, nach Spec)

**Role:** `senior-developer` (Security-Review durch `security-auditor`). **Nur nach Task 0 APPROVED, Block A abgeschlossen, Task 7 gemergt.**
**Files:** Modify `hooks/1-generic/orchestrator-guard-impl.sh` (Sentinel-Zuordnung `:418-481`, Gate `:1535`), `config/ai-providers.yaml` (Capability-Flag je Spec, Muster `hook-agent-id` `:64`), `scripts/lib/hooks.py` (Platzhalter-Baking analog `{{AGENT_META_HOOK_AGENT_ID}}`, `:555-561`; Guard-Seite `orchestrator-guard-impl.sh:360`), `rules/1-generic/branch-guard.md`, Header des Guards (Boundary-Klassifikation), `tests/test_orchestrator_guard_hook.py`.
**Interfaces:** Consumes Spec aus Task 0 (Payload-Feldname, Fallback). Produces: Guard lehnt Sentinel ab, wenn die Payload-Rolle nicht zur Sentinel-Rolle passt; Fallback ohne Feld = bisheriges Verhalten.

- [ ] Step 1: Charakterisierungstest zuerst (Issue AC-2): `tests/test_orchestrator_guard_hook.py::test_forged_allowlist_sentinel_from_non_granted_role_is_accepted_today`. Setup nach dem Muster von `test_allowlisted_role_can_commit_when_auto_commit_enabled` (`:961`) und `test_auto_commit_non_allowlisted_role_still_blocked` (`:968`): Payload mit `agent_id`, Sentinel `#agent-meta:agent=<granted-role>`, aber Payload-Rolle = nicht berechtigte Rolle; erwarte exit 0 (aktuelles Verhalten). Läuft grün vor jeder Änderung; wird in Step 3 bewusst umgedreht.
- [ ] Step 2: Failing Test (neu, laut Spec): gleiche Payload mit Rollenfeld, erwarte exit 2 mit Meldung, die den Grund nennt ("role mismatch"). Zweiter Test: `git`-Sentinel-Pfad unverändert (`test_git_sentinel_still_allows_plain_mutation`, `:383`, bleibt grün). Dritter Test: Provider ohne Feld = Verhalten wie heute (kein Reject).
- [ ] Step 3: Implementierung nach Spec. Charakterisierungstest aus Step 1 auf die neue Erwartung umstellen und umbenennen, mit Verweis auf die Spec.
- [ ] Step 4: Doku: Hook-Header und `branch-guard.md` führen die Grenze: mit Rollenfeld = bindend; ohne Feld = Convention boundary.
- [ ] Step 5: `python3 -m pytest tests/test_orchestrator_guard_hook.py tests/test_hook_drift.py tests/test_hook_enablement_consistency.py`; `python3 scripts/sync.py --validate`.
- [ ] Step 6: commit `fix: bind guard sentinel to payload role (#1210)`
- Akzeptanz (messbar): drei neue Tests grün; Sentinel-Tests `:383-390`, `:565`, `:595-653` unverändert grün; Reject-Meldung nennt den Grund; Spec-Matrix vollständig abgedeckt.
- Falls Task 0 ergibt "kein vertrauenswürdiges Feld": Task 8 reduziert sich auf Step 1 (Charakterisierung) + Step 4 (Doku als Convention boundary), Commit `docs: classify guard sentinel as convention boundary (#1210)`.

### Task 9: #1217 ask-Approval-Pfad für destruktive Git-Operationen (M, nach Spec)

**Role:** `senior-developer`. **Nur nach Task 1a, Task 1 APPROVED und Task 8 gemergt** (gleiche Datei).
**Files:** Modify `hooks/1-generic/orchestrator-guard-impl.sh` (Gate `:1383-1392`; Audit `:496-500`), `rules/1-generic/branch-guard.md`, `rules/1-generic/a2a-delegation-gates.md` ("Bekannte Grenzen"), `tests/test_orchestrator_guard_hook.py`.
**Interfaces:** Consumes Spec aus Task 1 (Klassen, Ausgabeformat). Produces: für die ask-Klasse JSON-Ausgabe `hookSpecificOutput.permissionDecision: "ask"` statt exit 2; hart bleiben die Klassen laut Spec; Headless fail closed.

- [ ] Step 1: Charakterisierungstests (bestehend prüfen): `test_destructive_ops_blocked_even_with_git_sentinel` (`:407`), `test_non_git_agent_cannot_use_fake_sentinel_for_destructive` (`:565`), `test_auto_commit_destructive_gate_still_blocks_an_allowlisted_role` (`:1002`). Diese bleiben für die harten Klassen grün.
- [ ] Step 2: Failing Tests: `test_branch_delete_returns_ask_decision` (`git branch -D x` -> exit 0 + JSON-stdout mit `"permissionDecision": "ask"` und dem vollständigen Befehl), `test_push_delete_returns_ask_decision`, `test_reset_hard_still_exit_2`, `test_headless_fails_closed` (Erkennung der Headless-Lage laut Spec), `test_sentinel_cannot_approve_ask` (Sentinel ändert die Ausgabe nicht), `test_tokenizer_cases_unchanged` (parametrisiert über die Fälle #542/#551/#590/#591/#602 aus den vorhandenen Tests, Klassifikation `destructive` bleibt).
- [ ] Step 3: Implementierung: Klassifikator `is_destructive` (`:895`) liefert zusätzlich eine Unterklasse (ask-fähig vs. hart); Gate `:1384` verzweigt. Audit-Zeile `asked` über `hook_audit_log_append <logfile> <line>` (`hook_common.sh:264-265`, heutiger Aufruf `orchestrator-guard-impl.sh:500`). "approved/denied" nur, wenn Spec ein Signal belegt.
- [ ] Step 4: Provider ohne `ask`-Unterstützung (laut Task 1a) behalten `exit 2`; Steuerung über Capability-Flag in `config/ai-providers.yaml`, nicht über Providername.
- [ ] Step 5: Doku in `branch-guard.md` und `a2a-delegation-gates.md`; Hinweis, dass Phase-A-Löschpfad (#946, Entscheidung 12) erst nach diesem Merge ask nutzen darf.
- [ ] Step 6: `python3 -m pytest tests/test_orchestrator_guard_hook.py tests/test_hook_drift.py`; `python3 scripts/sync.py --validate`.
- [ ] Step 7: commit `feat: add ask approval path for destructive git ops (#1217)`
- Akzeptanz: sechs neue Tests grün; alle Charakterisierungstests grün; `exit 2` für harte Klassen unverändert (Test belegt); Audit-Log enthält Zeile `asked` (Test liest `.claude/hooks/.guard-audit.log` im tmp-Projekt).

---

### Task 11: Spec-Gate #1141 (Config-Schema, M, nach Block A)

**Role:** `concept-specifier`, `concept-reviewer`, User-Freigabe. **Voraussetzung:** Block A abgeschlossen (Gate G-A; letzter Task laut Reihenfolge `:60` ist T14, nicht T16) und Task 9 gemergt (Entscheidung 35: #1141 ist der letzte Teil der Phase-D-PR).
**Files:** Create `docs/specs/2026-11-11-config-unknown-keys-spec.md`.
**Interfaces:** Consumes Issue #1141 (Body und Akzeptanzkriterien), Entscheidung 35. Lesen: `config/project-config.schema.json` (Top-Level-`properties`, `additionalProperties` `:2854`, `_comment` `:12`); `scripts/lib/config.py` (`_schema_top_level_props` `:256-263`, `_non_object_top_level_keys` `:266-277`, `_normalize_null_blocks` `:280-297`, `_object_top_level_keys` `:302-307`, `_normalize_non_mapping_blocks` ab `:310`, `_validate_config` `:636`, jsonschema-Gate `:676-685`); Leser von `rules-preset`, `test-repo`, `backup`, `mcp`. Produces Spec für Task 12.

- [ ] Step 1: Leser der vier Schlüssel in `scripts/` und `config/` am Ausführungsstand neu belegen (Vorbefund `9aa0e0c0` siehe Abweichung #1141: `rules-preset` Skalar, `test-repo`/`backup` Mapping, Top-Level-`mcp` ohne Leser). Typ je Schlüssel mit file:line. `mcp` wird laut Entscheidung 5/35 aufgenommen; ohne Leser schlägt die Spec einen Typ mit Begründung vor, die Spec-Freigabe (Step 4) bestätigt ihn.
- [ ] Step 2: Spec schreiben: (a) Schlüsselliste mit Typ und Beleg; (b) Warnregel: unbekannter Top-Level-Schlüssel erzeugt eine stderr-Warnung im Stil von `config.py:703-708`, kein Fehler, Sync läuft weiter; (c) "did you mean" über `difflib.get_close_matches` gegen die Schema-Properties, Cutoff in der Spec festgelegt; (d) Schema bleibt offen (`additionalProperties: true`, `:2854`); die Issue-Option `additionalProperties: false` ist ausgeschlossen (Entscheidung 35); (e) Typ-Konsequenz: Skalar-Typ landet in `_non_object_top_level_keys` (`config.py:273-277`) und Null-Werte werden entfernt (`:280-297`); Typ `object` wird auf `{}` normalisiert (`:302-318`); die Typwahl muss zum Leser passen; (f) `_comment` bleibt unverändert (`:12`); (g) Provider-agnostisch, keine Provider-Verzweigung; (h) Scope: `--validate` (Issue-AC) UND `--audit-config` (Entscheidung 48). Pfad gemessen auf `9aa0e0c0`: `--audit-config` baut den Kontext über `_build_context` (`scripts/sync.py:836`), das ruft `load_config` (`scripts/lib/cli_commands.py:684`), das ruft `_validate_config` (`scripts/lib/config.py:385`); erst danach dispatcht `scripts/sync.py:844` an `_handle_audit_config` (`scripts/lib/cli_commands.py:784`). Eine Warnung in `_validate_config` erscheint damit auf stderr auch bei `--audit-config`, ohne zweiten Aufrufpunkt. `audit_config()` selbst (`scripts/lib/config_audit.py:235`, liest das YAML separat `:280`) erzeugt keinen Report-Eintrag; ein zusätzlicher Report-Finding ist nicht Teil von Entscheidung 48 und wird nicht geplant; (i) `mcp`-Typ nach Step 1 (Offene Entscheidungen Punkt 4).
- [ ] Step 3: Review durch `concept-reviewer`; Findings einarbeiten.
- [ ] Step 4: User-Freigabe einholen. Erst dann `Status: APPROVED` setzen.
- Akzeptanz: Spec enthält Schlüsselliste mit Typ und file:line je Schlüssel, Warnformat, did-you-mean-Regel, Begründung "Schema bleibt offen", Typ-Konsequenz, Testmatrix; Kopf `Status: APPROVED` nur nach User-Ja; `python3 scripts/sync.py --validate` Exit 0.
- [ ] Step 5: commit `docs: spec config unknown top-level key warning (#1141)`

### Task 12: #1141 Unbekannte Top-Level-Keys melden (M, TDD, nach Spec)

**Role:** `developer`. **Voraussetzung:** Task 11 APPROVED, Block A abgeschlossen (gleiche Schema-Datei wie #1181, sequentiell).
**Files:** Modify `config/project-config.schema.json` (Properties `rules-preset`, `test-repo`, `backup`, `mcp` mit Typen laut Spec; `additionalProperties` bleibt `true`, `:2854`); Modify `scripts/lib/config.py` (neue Funktion, Aufruf in `_validate_config` nach `:674`, also vor dem jsonschema-Gate `:676`); Create `tests/test_config_unknown_keys.py`; Modify `scripts/admin-server.py` (`_RUNTIME_ONLY_SECTIONS` ohne `rules-preset`/`backup`, aus E-T4) und `tests/test_admin_whitelist_drift.py` (erwartete Anzahl 6, aus E-T4).
**Interfaces:** Produces `_warn_unknown_top_level_keys(config: dict, config_path: Path) -> None`: schreibt je unbekanntem Top-Level-Schlüssel eine stderr-Warnung, optional mit Vorschlag aus `difflib.get_close_matches(key, known, n=1, cutoff=<Spec>)`; bekannte Schlüssel = `_schema_top_level_props()` (`config.py:256`). Consumes Spec aus Task 11.

- [ ] Step 1: Failing Tests in `tests/test_config_unknown_keys.py`: `test_misspelled_top_level_key_warns` (`dod-presett` gibt Warnung mit `dod-presett` und Vorschlag `dod-preset`), `test_unknown_key_without_suggestion_warns` (`zzz-unknown`), `test_known_keys_no_warning` (`rules-preset`, `test-repo`, `backup`, `mcp`, `_comment`, `$schema` erzeugen keine Warnung), `test_repo_project_yaml_no_unknown_key_warning` (`.meta-config/project.yaml` des Repos, Lade-Muster aus `tests/test_config_audit.py`), `test_schema_keeps_top_level_open` (Schema-Top-Level `additionalProperties is True`), `test_warning_runs_without_jsonschema` (Modul-Flag `_JSONSCHEMA_AVAILABLE`, `config.py:111`, geprüft in `_validate_config` `:676`, per Monkeypatch auf `False`; Warnung bleibt), `test_audit_config_shows_unknown_key_warning` (Entscheidung 48: `python3 scripts/sync.py --audit-config` als Subprozess gegen eine tmp-Config mit `dod-presett`; stderr enthält die Warnung, Exit-Code unverändert gegenüber der Config ohne Tippfehler). FAIL erwartet.
- [ ] Step 2: Schema-Properties ergänzen (Typen und `description` laut Spec). Schema-Teil der Tests grün. Querbezug Phase E (E-T4, läuft vor D): im selben Commit `rules-preset` und `backup` aus `_RUNTIME_ONLY_SECTIONS` in `scripts/admin-server.py` entfernen und in `tests/test_admin_whitelist_drift.py` `test_runtime_only_count_is_eight` auf 6 senken (Name/Assertion anpassen); sonst werden `test_runtime_only_equals_whitelist_minus_schema` und der Zähltest rot (`2026-11-11-phase-e-artifact-locations.md:239-245`). Mitlaufen: `python3 -m pytest tests/test_admin_whitelist_drift.py`.
- [ ] Step 3: `_warn_unknown_top_level_keys` implementieren (stdlib only), Aufruf in `_validate_config`.
- [ ] Step 4: `python3 -m pytest tests/test_config_unknown_keys.py`; Regression `python3 -m pytest tests/test_config_null_blocks.py tests/test_config_audit.py tests/test_config_variable_fallbacks.py tests/test_spec_plan_config_schema.py`; `python3 scripts/sync.py --validate` Exit 0 ohne neue Warnung für das Repo-`project.yaml`.
- [ ] Step 5: commit `fix: warn on unknown top-level config keys (#1141)`
- Akzeptanz: Issue-#1141-AC 1 bis 3 erfüllt (Warnung im `--validate`; Repo-Config ohne neue Warnung; Regressionstest für Tippfehler-Key grün); Warnung auch bei `--audit-config` (Entscheidung 48); Schema-Top-Level bleibt offen; keine Provider-Verzweigung.

---

## Phase-Abschluss

### Task 10: Gesamtprüfung und Wellen-Gate

**Role:** `validator`.
**Files:** keine Änderungen.

- [ ] Step 1: `python3 scripts/sync.py --validate` Exit 0; `python3 -m pytest tests/test_orchestrator_guard_hook.py tests/test_hook_common_lib.py tests/test_hook_drift.py tests/test_repo_containment_hook.py tests/test_dod_push_check_hook.py tests/test_orchestrator_worker_report_contract.py tests/test_config_unknown_keys.py` grün.
- [ ] Step 2: Je Issue Evidenz-Kommentar vorbereiten (Dateien, Tests, offene Reste). Kommentar zuerst, dann manuell schließen, keine Closing-Keywords in Commit/PR (Entscheidung 38e). Schließen nur nach Freigabe: #1181 (Plan komplett), #1172 (nach Task 2 und Task 2b bzw. belegtem Negativbefund aus Task 2a), #1169 (Messwerte), #1141 (nach Task 12). #1176 und #1168 nur schließen, wenn der manuelle/Dry-Run-Nachweis vorliegt, sonst offen mit Rest. #1210/#1217 je nach Ausgang der Spec.
- Akzeptanz: Prüfbefehle grün; Commit-Subject-Liste der Phase vollständig (ein Commit je Task); höchstens zwei PRs für Phase D (Entscheidung 17, präzisiert durch 52): Phasen-PR mit den ausführbaren Tasks, ein Nachfolge-PR mit den gesperrten/spec-gesteuerten Tasks; #1141 als letzter Teil (Entscheidung 35). Task 2b nur, wenn Task 2a positiv und APPROVED.

## Entscheidungen (beantwortet)

Quelle: Roadmap-Entscheidungen 17-35 und 38a (User-Antworten, bindend). Die Zuordnung D-neu-x zu Roadmap-Nummer steht je Punkt.

1. **D-neu-1 (#1168) = Entscheidung 25:** Task-Prompt-Trailer gewinnt. Der Git-Agent übernimmt eine im Task-Prompt vorgegebene Trailer-Zeile wörtlich und leitet nichts aus der eigenen Session ab. Umsetzung Option (a): kein neuer Konfig-Key, kein Lint. Task 4 freigegeben.
2. **D-neu-2 (Reihenfolge) = Entscheidung 19:** Kette `#1187 -> #1186 -> #1188 -> #1181 -> #1141`. Strom A (#1181) startet nach Phase F (#1188). Task 0, 1a, 1, 2, 3, 5, 6 sind davon unabhängig.
3. **D-neu-3 (#1176) = Entscheidung 34:** Nur dokumentieren mit vorhandenen Tools (`SendMessage`, `TaskStop`). `Monitor` wird nicht gewährt; keine Änderung an `config/ai-providers.yaml:133`.
4. **D-neu-4 (#1210, bedingt) = Entscheidung 34:** Ohne Payload-Rollenfeld: Convention boundary dokumentieren (Option 3 des Issues), Option 2 (Secret) entfällt. Endgültig erst nach Evidenz aus Task 0 Step 1; nur bei negativer Evidenz, danach erneute User-Bestätigung (Entscheidung 38a).
5. **Entscheidung 28 (#1169):** neue Funktion `hook_json_get_many` (ein Interpreter-Start, NUL-getrennt, `read -r -d ''`, bash 3.2, kein `eval`). Spec braucht User-Freigabe vor Implementierung; Abstimmung mit Phase H (#1161, Punkt 5). Task 5 und 7 entsprechend.
6. **Entscheidung 17 (Phase-PR):** ein PR für Phase D, ein Commit je Task. Umgesetzt in Globalen Constraints und Task 10. Durch Entscheidung 35 nicht geändert (#1141 gehört in dieselbe PR). Durch Entscheidung 52 präzisiert: max. 2 PRs (Phasen-PR + Nachfolge-PR für gesperrte/spec-gesteuerte Tasks), siehe Punkt 11.
7. **Entscheidung 35 (#1141):** Kette `#1187 -> #1186 -> #1188 -> #1181 -> #1141`. #1141 ist der letzte Teil der Phase-D-PR nach #1181 und hat Klasse M: Spec-Gate Task 11, Implementierung Task 12. Inhalt: Warnung bei unbekannten Top-Level-Schlüsseln, Schema bleibt offen (`additionalProperties: true`), fehlende gültige Schlüssel ergänzen. Phase D = 8 Issues; Summe 89 (Phase F = 6, Phase-F-Task 5 entfällt als Querverweis auf D). Der frühere offene Konflikt "#1141 vs. Kette" ist damit beantwortet.
8. **Entscheidung 38a (#1210, Konflikt Entscheidung 2 vs. D-neu-4):** Beide schließen sich nicht aus. D-neu-4 gilt nur bei negativer Evidenz aus Task 0 Step 1 (kein vertrauenswürdiges Rollenfeld). Danach bestätigt der User erneut. Task 0 und Task 8 sind entsprechend formuliert. Vorher offen gelistete Frage (frühere Liste Punkt 1) ist damit erledigt.
9. **Entscheidung 47 (#1172, D Offen 1):** Permission-Regel für den `git`-Agenten BAUEN (weicht von der Planner-Empfehlung "nur dokumentieren" ab). Umsetzung: Task 2a (Machbarkeit + Spec-Gate, zuerst), Task 2b (bedingte Umsetzung); dokumentierter Merge-Pfad (Main Chat -> `git`) in Task 2 bleibt Fallback.
10. **Entscheidung 48 (#1141, D Offen 5):** `--audit-config` zeigt die Unknown-Key-Warnung ebenfalls (zusätzlich zu `--validate`). Umsetzung: Task 11 Step 2 (h) mit gemessenem Aufrufpfad, Test `test_audit_config_shows_unknown_key_warning` in Task 12.
11. **Entscheidung 52 (PR-Schnitt):** Phasen-PR nur mit derzeit ausführbaren Tasks; gesperrte/spec-gesteuerte Tasks in einem Nachfolge-PR derselben Phase, max. 2 PRs. Umgesetzt in Globalen Constraints, Task 2b und Task 10.

## Offene Entscheidungen (neu, ungeklaert)

Nicht durch Entscheidungen 1-38 gedeckt. Nicht entschieden, nicht geraten. Die früheren echten User-Fragen Punkt 1 und 5 sind durch Entscheidung 47 und 48 beantwortet; Punkte 2-4 sind Verifikationspunkte, die als Task-Schritte laufen (Task 1a, Task 1 Step 2, Task 11 Step 1) und erst bei negativem Befund zur User-Frage werden.

1. **Beantwortet (Entscheidung 47):** #1172 Vorschlag 3 (Permission-Regel für den `git`-Agenten) wird gebaut, sofern Task 2a die Machbarkeit belegt (Task 2b); sonst Fallback Task 2.
2. **(Verifikation, Task 1a) Ergebnis Task 1a (`ask` je Provider):** Umgang bei fehlendem `ask`-Support folgt Entscheidung 1 (nicht Teil von 17-35 und 38a: Spec überarbeiten, nicht erzwingen). Offen bis Task 1a-Ergebnis vorliegt.
3. **(Verifikation, Task 1 Step 2) #1217 Audit `approved`/`denied`:** Ob ein Hook diese Entscheidung überhaupt sieht, ist nicht belegt. Spec begrenzt Audit auf `asked`, bis Evidenz vorliegt (Task 1, Step 2).
4. **(Verifikation, Task 11 Step 1) #1141 Typ von Top-Level-`mcp`:** Aufnahme ist durch Entscheidung 5/35 entschieden. Offen ist nur der Typ, weil kein Leser für Top-Level-`mcp` existiert (nur `viz.mcp`, `.meta-config/project.yaml:332`, `scripts/admin-server.py:508`). Klärung über das Spec-Gate Task 11 (User bestätigt mit der Spec-Freigabe), keine separate Frage.
5. **Beantwortet (Entscheidung 48):** #1141 Scope `--audit-config`: Warnung erscheint auch dort (Task 11 Step 2 (h), Test in Task 12).

## Frische-Check-Referenzen

- docs/plans/2026-11-09-commit-authority-grant-plan.md
- docs/specs/2026-11-09-commit-authority-grant-spec.md
- docs/superpowers/plans/2026-11-10-backlog-roadmap.md
- hooks/1-generic/orchestrator-guard-impl.sh
- hooks/1-generic/lib/hook_common.sh
- hooks/1-generic/repo-containment-impl.sh
- hooks/1-generic/dod-push-check.sh
- scripts/bench_hooks.py
- scripts/lib/hooks.py
- scripts/lib/auto_commit.py
- scripts/lib/sync_pipeline.py
- scripts/lib/provider_transform.py
- scripts/sync.py
- config/ai-providers.yaml
- config/provider-capabilities.yaml
- config/provider-tools.yaml
- rules/1-generic/use-orchestrator.md
- rules/1-generic/branch-guard.md
- rules/1-generic/a2a-delegation-gates.md
- agents/1-generic/orchestrator.md
- agents/1-generic/git.md
- docs/providers/codex.md
- docs/providers/kimi-code.md
- docs/analysis/2026-11-11-hook-api-ask-permission.md
- docs/hook-latency-baseline.md
- docs/specs/2026-11-11-guard-role-attribution-spec.md
- docs/specs/2026-11-11-guard-destructive-ask-spec.md
- docs/specs/2026-11-11-hook-single-parse-spec.md
- docs/specs/2026-11-11-config-unknown-keys-spec.md
- config/project-config.schema.json
- scripts/lib/config.py
- .meta-config/project.yaml
- tests/test_config_unknown_keys.py
- tests/test_config_audit.py
- tests/test_config_null_blocks.py
- tests/test_orchestrator_guard_hook.py
- tests/test_hook_common_lib.py
- tests/test_hook_drift.py
- tests/test_hook_enablement_consistency.py
- tests/test_repo_containment_hook.py
- tests/test_dod_push_check_hook.py
- tests/test_orchestrator_worker_report_contract.py
- tests/test_orchestrator_compact_sections.py
- tests/test_hook_bench_script.py
- tests/test_merge_pattern_docs.py
- tests/test_git_template_commit_trailer_rule.py
- symbol: hook_json_get
- symbol: hook_json_get_many
- symbol: hook_json_usable
- symbol: hook_known_tool_name
- symbol: hook_audit_log_append
- symbol: is_destructive
- symbol: is_fs_destructive
- symbol: IS_ALLOWLIST_SENTINEL
- symbol: IS_GIT_SENTINEL
- symbol: SENTINEL_DISCARDED
- symbol: HOOK_AGENT_ID_RELIABLE
- symbol: _run_hook
- symbol: _run_rendered
- symbol: _validate_config
- symbol: _schema_top_level_props
- symbol: _non_object_top_level_keys
- symbol: _object_top_level_keys
- symbol: _warn_unknown_top_level_keys
- symbol: hook-agent-id
- symbol: primary-role-tools
- symbol: permissionDecision
- scripts/lib/cli_commands.py
- scripts/lib/config_audit.py
- scripts/lib/permissions.py
- scripts/lib/subagent_permissions.py
- config/ai-providers.yaml
- symbol: _handle_audit_config
- symbol: _build_context
- symbol: permission-mode-overrides
- symbol: inject-permission-mode
- issue: 1181
- issue: 1210
- issue: 1217
- issue: 1172
- issue: 1176
- issue: 1168
- issue: 1169
- issue: 946
- issue: 1116
- issue: 783
- issue: 1157
- issue: 1162
- issue: 1186
- issue: 1188
- issue: 1141
- issue: 1161
- issue: 1187
- issue: 1218
- issue: 1141
- origin/main `9aa0e0c0` (Stand nach PR #1218)

## Nicht verifiziert

- Nichts ausgeführt: weder Tests noch Benchmark noch `--validate`. Alle erwarteten Ergebnisse sind Planannahmen.
- Nachgemessen (Review 2026-11-11, read-only gegen `9aa0e0c0`): Guard-Anker (`:45`, `:214-218`, `:231`, `:239`, `:245`, `:255`, `:262-269`, `:326`, `:333`, `:384`, `:418-481`, `:496-500`, `:895`, `:1262`, `:1330`, `:1383-1392`, `:1419`, `:1527-1547`), `hook_common.sh` (`:3-5`, `:63-110`, `:128-131`, `:169`, `:264`), `config.py` (`:111`, `:256-318`, `:636-714`), Schema (`:12`, `:2854`), Testnamen und -zeilen in `tests/test_orchestrator_guard_hook.py` und `tests/test_orchestrator_worker_report_contract.py:85-99`, `scripts/lib/hooks.py:554-561`, #1181-Plan `:17`, `:60`, `:77-79`, `:279-314`, `:1139`, `:1200`.
- Spawn-Zahl 9 nur statisch aus dem Quelltext gezählt, nicht zur Laufzeit gemessen (Task 6). Ziel "<= 5" ist ein Planwert.
- Ob der Referenzplan #1181 inhaltlich (T5/T8/T16) nach #1190 (Orchestrator-Topologie, PR #1215/#1216) noch passt: nicht geprüft; nur die AC-1-Basis `aaed14c2` ist als gebrochen belegt (siehe Reihenfolge und Abhängigkeiten).
- Hook-API für `ask` bei Claude Code: nicht verifiziert (Task 1a). Im Repo keine Claude-Belege, `review-policy-gate.sh` existiert nicht.
- Ob ein Payload-Rollenfeld existiert (Entscheidung 2): nicht verifiziert (Task 0 Step 1).
- #1172 Machbarkeit der Permission-Regel (Entscheidung 47): nur Kandidaten-Anker gelistet (Task 2a Step 1), Wirkung auf den externen Classifier nicht verifiziert.
- Auto-Mode-Classifier-Verhalten (#1172) und Harness-Verhalten beim vorzeitigen `SubagentHandback` (#1176): extern, nicht reproduzierbar im Repo.
- #1141: `--audit-config`-Scope durch Entscheidung 48 geklärt; Aufrufpfad read-only gemessen (`scripts/sync.py:836`, `:844`, `scripts/lib/cli_commands.py:684`, `:784`, `scripts/lib/config.py:385`), nicht ausgeführt. Vollständigkeit der Top-Level-Keys gegen Configs anderer Projekte nicht geprüft (Issue-Caveat).

## Self-Review

- Alle acht Issues genau einmal: #1181 (Block A, Referenz), #1210 (Task 0, 8), #1217 (Task 1a, 1, 9), #1172 (Task 2a, 2, 2b bedingt), #1176 (Task 3), #1168 (Task 4), #1169 (Task 5-7), #1141 (Task 11-12).
- Spec-Gates: Task 0 (#1210), Task 2a (#1172, nur bei positivem Machbarkeitsbefund), Task 1 (#1217, nach Task 1a), Task 5 (#1169), Task 11 (#1141); #1181 über vorhandene APPROVED Spec.
- Dateikonflikte: `orchestrator-guard-impl.sh` nur sequentiell (Block A bis Gate G-A -> Task 7 -> Task 8 -> Task 9); `config/project-config.schema.json` nur sequentiell (Block A -> Task 12); `orchestrator.md` Task 2 vor Task 3; `git.md` Task 2 vor Task 4.
- Signaturen mit file:line belegt für `hook_json_get` (`hook_common.sh:63`), `hook_json_usable` (`:128`), `hook_known_tool_name` (`:169`), `hook_audit_log_append <logfile> <line>` (`:264`), Guard-Anker (`:239,:262-269,:326,:418-481,:1383-1392,:1535`). `hook_json_get_many` ist neu (Signatur in Task 5 festgelegt). #1141: `_validate_config` (`scripts/lib/config.py:636`), jsonschema-Gate `:676-685`, `_schema_top_level_props` `:256`, `_non_object_top_level_keys` `:266`, `_object_top_level_keys` `:302`; `_warn_unknown_top_level_keys` ist neu (Signatur in Task 12).
- Keine Platzhalter-Texte; offene Punkte stehen unter Offene Entscheidungen und Nicht verifiziert.
- Entscheidungen eingearbeitet: 1 (Task 1a vor Spec), 12 (`!`-Befehle), 19 (Reihenfolge), 17 (ein PR, ein Commit je Task), 25 (#1168), 28 (#1169), 34 (D-neu-3, D-neu-4), 35 (#1141, Task 11-12), 38a (#1210, D-neu-4 nur bei negativer Evidenz), 38e (keine Closing-Keywords), 47 (#1172, Task 2a/2b), 48 (#1141 `--audit-config`), 52 (max. 2 PRs je Phase). Status bleibt DRAFT bis User-Freigabe der Specs (Task 0, 1, 2a, 5, 11). Offene Punkte stehen unter "Offene Entscheidungen (neu, ungeklaert)" (Punkte 2-4; 1 und 5 beantwortet).
- #1141-Befunde: `_comment` ist im Schema vorhanden (`:12`); Top-Level-`mcp` hat keinen Leser (nur `viz.mcp`, `.meta-config/project.yaml:332`); Aufnahme laut Entscheidung 35 fest, Typ über Spec-Gate Task 11.
- Frische-Check: Stand `9aa0e0c0`; Anker nach Merge von C/E/F erneut messen (siehe Reihenfolge und Abhängigkeiten).
- Ratchet `_KNOWN_DUPLICATES` (Plan B Task 8): betrifft `ui-ux-designer.md`, `bug-feature-analyzer.md`, `knowledge-curator.md`, `knowledge-migrator.md`; keine davon wird in Phase D oder im #1181-Plan geändert, `orchestrator.md`/`git.md` haben je 1 `{{PROJECT_CONTEXT}}`. Keine Berührung.
