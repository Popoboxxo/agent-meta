# System-Audit-Remediation 2026-11-06 — Spec

> Status: **APPROVED (2026-11-06)**
> Freigabe: Nutzer-Auftrag 2026-11-06 (Auftrag an `main_chat`: Audit-Funde gruppiert, seriell und PR-weise abarbeiten). Der Marker wurde nicht vom Planer gesetzt.
> Revision: 1
> Datum: 2026-11-06
> Klasse: **XL / Architectural** (mehrere Subsysteme: Hooks, sync-Kern, Orchestrator-Templates, DoD-/Pipeline-Konfiguration, Provider-Doku; öffentliche Hook-Contracts betroffen)
> spec-id: SPEC-system-audit-remediation-2026-11-06
> Audit-Quelle: `/home/hermes/repos/agent-meta/.tmp/system-audit-2026-11-06.md` (git-ignoriert, Basis origin/main `09925d20`)
> Plan: `docs/plans/2026-11-06-system-audit-remediation-plan.md`
> Verifikations-Legende: **CONFIRMED** = nach Gegenprüfung am Code belegt; **PARTIAL** = Kernaussage stimmt, Detail falsch/anders; **REFUTED** = widerlegt; **UNVERIFIABLE** = extern/ohne Laufzeitprobe nicht belegbar; **AUDIT-ONLY** = nur Audit-Beleg, vor dem Fix am Code zu belegen.

Diese Spec legt Ziel, Umfang, Verträge und Abnahmekriterien für die Abarbeitung des
Systemaudits vom 2026-11-06 fest. Sie enthält **keinen Implementierungscode**; die
Task-Zerlegung steht im Plan.

## Problem

Das Systemaudit (6 Dimensionen: Fehler, Konzept, Orchestrierung, Provider,
Token-Budget, Hooks) hat 11 Code-Fehler (F1–F11), 17 Konzeptprobleme (K-01..K-17),
7 Orchestrierungsfunde (F3-01..07), 9 Gemini-/3 Opencode-/2 Provider-Agnostik-Funde,
13 Hook-Funde (F6-01..13) und mehrere Token-Funde ergeben. Die Gegenprüfung am Code
hat die meisten P1/P2-Funde bestätigt, einen widerlegt (G4-6), vier teilweise
korrigiert (F8, F10, F6-10, F3-07) und mehrere als extern unverifizierbar
eingestuft (G4-4/5/7/8, F-OC1, F3-05, graphify-Text).

Schwerpunkte mit Sicherheits-/Korrektheitswirkung:

- **Hook-Containment-Lücken (P1):** `NotebookEdit`/`MultiEdit` werden nicht abgefangen
  (Probe: rc=0 für `/etc/x.ipynb`); die Tool-Allowlist ist zum dritten Mal veraltet.
- **sync.py-Robustheit (P1/P2):** Import-Abbruch auf Python 3.9/3.10 (tomli), Exit 0
  trotz `[ERROR]`, TypeError in `deactivation.py`, still verworfene Frontmatter-Felder.
- **Orchestrator-Handback (P1):** fehlende `SendMessage`/`TaskStop`-Werkzeuge bei
  Template-Pflicht zu Polling/Handback.
- **DoD-/Spec-Gate-Drift (P1):** REQ-/Test-Pflicht ungegatet bei `rapid-prototyping`,
  `feature-lifecycle` umgeht das Approval-Gate.

## Ziel

Alle bestätigten Funde werden in **sieben seriellen PR-Gruppen** (G1–G7) behoben oder
mit begründeter, dokumentierter Entscheidung aufgeschoben. Jeder Fix ist test-first
(rot → grün), provider-agnostisch, quellenbasiert (nie `.claude/` editieren) und
einzeln reviewbar.

**Messbare Ziele:**

- Jede Gruppe liefert genau einen PR mit: Root cause `Datei:Zeile`, Before/After,
  Testevidenz, Non-goals, „What I could not verify".
- `python3 scripts/sync.py --validate` und `python3 scripts/consistency-check.py`
  enden nach jeder Gruppe mit rc 0.
- Kein bestehender Golden/Baseline-Test wird ungeprüft neu erzeugt (nur bei
  beabsichtigter Änderung, per Eintrag).
- Jeder aufgeschobene Fund hat eine schriftliche Begründung im Plan (kein stilles
  Verwerfen).

## Nicht-Ziele

- **Keine** Änderung an widerlegten Funden: **G4-6** (Gemini-`matcher "*"`): Doku
  zeigt, dass `""` oder `"*"` alle Tools matcht — Konfiguration bleibt unverändert.
- **Kein** Default-Flip für Gemini `agent-discovery` (G4-1): braucht einen
  Antigravity-Laufzeitlauf (#854/#860); nur Doku-Hinweis in
  `config/provider-capabilities.yaml`.
- **Keine** volle Indirektions-Policy für Git-Mutationen (`eval`, `bash -c`,
  Variablen-Indirektion, `xargs`): aufgeschoben (Ref #592); nur `$(...)`/Backtick
  innerhalb `"..."` im gemeinsamen Scanner (F6-03 Teil). `$VAR`-Ziele im
  Containment bleiben ebenfalls aufgeschoben.
- **Keine** Änderung an extern unverifizierbaren Aussagen (G4-4, G4-5, G4-7, G4-8,
  F-OC1, F3-05 als Code, graphify-Hook-Text): höchstens Doku-Hinweis oder
  Aufschub mit Grund.
- **Kein** Edit in `.claude/`, `.agents/`, `.gemini/`, `.opencode/` (gerenderte
  Ausgabe); Änderungen ausschließlich in der Quelle, danach `python scripts/sync.py`.
- **Kein** Merge, kein Force-Push, kein Tag durch ausführende Agenten; Push/Branch
  ausschließlich Rolle `git`.
- **Keine** Memory-Datei-Änderung (liegt außerhalb des Repos; Hinweis an
  `main_chat`).
- **Keine** Parallelausführung schreibender Agenten (zweite Session teilt den Baum).

## Entscheidungen (D1–D8)

| ID | Entscheidung | Konsequenz |
|---|---|---|
| **D1** | Gruppierung nach Ownership-Subsystem, nicht nach Schwere: G1 Hooks, G2 sync-Kern, G3 Orchestrator-Tools, G4 DoD/Spec-Gate, G5 Doku-Drift, G6 Gemini, G7 Token. P1-Gruppen zuerst. | Ein PR berührt ein Subsystem; Reviews bleiben klein. |
| **D2** | Strikt serielle Ausführung, jede Gruppe von `origin/main` abzweigen, Baum vor Start `clean` prüfen. | Zweite Claude-Session teilt den Baum; Branchwechsel nie parallel. |
| **D3** | Hooks nur in `hooks/1-generic/` (und `hooks/0-external/`) ändern; `.claude/hooks`, `.agents/hooks` sind gerendertes Abbild. | Fix = Quelle + `python scripts/sync.py`; Hook-Header `# version:`/`# changelog:` pflegen. |
| **D4** | Convention-Boundary bleibt die Garantiestufe der Guards (siehe `branch-guard.md`). | Kein Versprechen gegen gezielten Bypass; Doku-Zeile „Bekannte Grenzen" wird fortgeschrieben, nicht gelöscht. |
| **D5** | F6-05: Sentinel nur bei gesetztem `agent_id` gültig, gebunden an Capability-Flag, weil Gemini kein `agent_id` liefert. Bestehender Test `test_strict_mode_sentinel_exemption` pinnt das Fehlverhalten und wird neu geschrieben. | Kein Provider-Name im Hook; Unterschied über Capability-Flag (`provider-agnostic`). |
| **D6** | F5: Mindestens `--check` endet mit Exit 1 bei `log.errors`; Plain-Sync-Policy ist eine zu dokumentierende Entscheidung (`tests/test_sync_end_checks.py:81` pinnt Exit 0 heute). #1142 (invalid `auto_commit`) erhält einen eigenen Pfad. | Entscheidung + Begründung im PR; kein stiller Verhaltenswechsel. |
| **D7** | K-01 (stale `.claude/`-Output) wird durch ein Drift-Gate (sync + `--check`) behoben, nicht durch Edit der Ausgabe. | Ausgabe ist ignoriert/regenerierbar. |
| **D8** | K-07 (ein REQ-Format, Aufwand M) wird aufgeschoben, falls unverhältnismäßig; Begründung ist Pflicht. K-07..K-17 und G4-9 sind AUDIT-ONLY und werden vor dem Fix am Code belegt. | Kein Fix auf Basis unbelegter Annahmen. |

## Interface Contracts

Betroffene öffentliche bzw. gepinnte Verträge (Datei:Symbol, Fehlerpfade). Alle Pfade
relativ zum Framework-Root.

### IC-1 Hook-Tool-Allowlist und Abfangzweige (G1)

- `hooks/1-generic/lib/hook_common.sh::hook_known_tool_name` (Allowlist,
  Audit `:169-188`): Parität mit der Claude-Tool-Referenz herstellen. Ergänzen:
  `LSP`, `PowerShell`, `EndConversation`, `ListAgents`, `ReportFindings`,
  `SendFeedback`, `ShareOnboardingGuide`, `WaitForMcpServers`, `Workflow`;
  korrigieren `ListMcpResourcesTool`/`ReadMcpResourceTool`. Fehlerpfad:
  unbekannter Toolname bleibt fail-closed (rc 2).
- `hooks/1-generic/repo-containment-impl.sh` (Audit `:225-228`) und
  `hooks/1-generic/orchestrator-guard-impl.sh` (Audit `:268-271`):
  `NotebookEdit` (Pfadfeld `notebook_path`), `MultiEdit` (wie `Edit`) und
  `PowerShell` (wie `Bash`, vor dem Allow-Zweig) werden abgefangen.
- `hook_common.sh` Scanner (Audit `:533-593`): `$(...)`/Backtick innerhalb `"..."`
  wird als Git-Mutationskandidat erkannt (F6-03 Teil).
- `orchestrator-guard-impl.sh` Mutationsliste (Audit `:390-396`): zusätzlich
  `git stash` (nackt), `mv`, `apply`, `notes`, `replace`, `update-index`, `config`,
  `fast-import`, `init`, `submodule update`, `gc`.
- Sentinel (Audit `:296-315`, `:377-382`): bei leerem `agent_id` verworfen, sofern die
  Capability dies für den Provider zulässt (D5).
- `Agent`-Aufruf mit `subagent_type=orchestrator` oder `isolation=worktree` bei
  gesetztem `agent_id` → rc 2 (F3-03).
- `graphify-*-guard.sh` (Audit `:31`): Rückgabecode nur `0`/`2`; `2` nur mit
  Guard-Meldung (F6-10, PARTIAL: nur rc 2 blockt, ein Crash blockt nicht).

### IC-2 sync-Kern (G2)

- `scripts/lib/artifact_validate.py:27-30`, `consistency/model_contracts.py:34-37`:
  tomli-Fallback auf `doctor_formats.parse_toml`; `TOMLDecodeError` → `ValueError`
  (F1). Fehlerpfad: kein Importabbruch ohne tomllib/tomli.
- `scripts/lib/config.py:677-678`: `except Exception` + stderr-Warnung statt
  `pass` (F8, PARTIAL: `check_schema` wird nie aufgerufen; Kernproblem stimmt).
- `scripts/lib/deactivation.py:279`: `log.error(target, message)` (F2).
- `scripts/lib/frontmatter.py:103-110`: bei YAML-Fehler Inhalt unverändert
  zurückgeben + Warnung (F3).
- `scripts/lib/hooks.py:519,599`, `scripts/lib/cli_commands.py:679,912`,
  `scripts/lib/agent_sync.py:889`: bool-Blöcke für `hooks`/`viz` normalisieren,
  `is True`-Prüfung, unbekannte Hook-Namen warnen (F4, Ref #1141).
- `scripts/lib/cli_commands.py:1697-1709`, `scripts/lib/log.py:59-68`: Exit 1 bei
  `log.errors` (mindestens unter `--check`); Policy-Entscheidung dokumentiert (F5, D6).
- `scripts/lib/io.py:377-384,521`: Mode/umask erhalten; Secrets bleiben 0600 (F6).
- `scripts/lib/config.py:1380,1447-1448,1469-1470`, `sync_pipeline.py:859`,
  `skill_admin.py:99`: `write_atomic`; CRLF-Verhalten über Bytes (F7).
- `scripts/lib/pipelines.py:293-295`: `except (Exception, SystemExit)` (F9).
- `subprocess.run(text=True)`: `encoding="utf-8", errors="replace"` an 19 Stellen
  (F10, PARTIAL: 19 statt 13 Stellen, Wirkung nicht reproduziert; Urteil low).
- `scripts/lib/consistency/python_compat.py:33-34`: `scripts/*.py` nicht-rekursiv in
  den Py3.9-Guard (F11).

### IC-3 Orchestrator-Tools und Handback (G3)

- `config/provider-tools.yaml` (claude-Whitelist) und Template-Frontmatter
  `agents/1-generic/orchestrator.md:7-11`: `SendMessage`, `TaskStop` ergänzen; Text
  `orchestrator.md:240,273` korrigieren (F3-01).
- `agents/1-generic/orchestrator.md` BARRIER (`:257-262`) und Worker-Contract:
  fehlender Handback/Report = `failed`, neu dispatchen (F3-04).
- Doku-Hinweise (extern unverifiziert): `run_in_background:false`/`-p`-Verhalten
  (F3-05, Ref #681) und Env-Var `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (F3-07).
- Test: `tests/test_subagent_allowlist_frontmatter.py`.

### IC-4 DoD-/Spec-Gate (G4)

- Ein einheitlicher Key für Spec/Plan (K-06): `scripts/lib/dod.py:281,374`,
  `config/dod-presets.yaml:38,54`, `.meta-config/project.yaml:55-56`.
- Gating `{{#if DOD_REQ_TRACEABILITY}}` / `{{#if DOD_TESTS_REQUIRED}}` für die
  ungegateten Stellen (K-02): `agents/1-generic/git.md:134`,
  `tester.md:22,32-43,98,119`, `se-developer.md:98,116`,
  `se-junior-developer.md:97,137`, `se-senior-developer.md:91`,
  `config/role-defaults.yaml:2692-2695`.
- `config/role-defaults.yaml:2640-2696` (`feature-lifecycle`): `approve`-Stage mit
  `requires_approval` **oder** Routing auf `concept-driven-dev` (K-03).
- `agents/1-generic/planner.md`: Vorbedingung `Status: APPROVED`;
  `orchestrator.md:92-98` angleichen (K-04).
- Eine Aussage zur Klassifikation/Approval in `use-orchestrator.md:51`,
  `rules/1-generic/spec-plan-workflow.md:59`, `orchestrator.md:64` (K-05).
- `max_depth`-Key: Doku `a2a-delegation-gates.md:30` vs `config.py:2134` (K-10).
- K-13: Default-Vereinheitlichung `config.py:2337-2338` vs `standalone.py:131-132`.
- K-01: Drift-Gate (sync + `--check`) als Test/CI-Prüfung (D7).

### IC-5 Doku-Drift / Provider-Agnostik (G5)

- K-08, K-09, K-11, K-12, K-14, K-15, K-16, K-17 (AUDIT-ONLY; vor Fix belegen).
- F-OC3: Kommentar zu 4-von-5-Tiers; F-OC2: nur dokumentieren (Superset bewusst).
- F-PA1: Opencode-benannte Funktionen in `scripts/lib/cli_commands.py:324-360`
  umbenennen (vorher Tests greppen). F-PA2: Default `"Opencode"` in
  `scripts/lib/rules.py:478` prüfen; Guard `tests/test_provider_agnostic_dispatch.py`
  erweitern.

### IC-6 Gemini-Oberfläche (G6)

- G4-1: nur Doku-Hinweis in `config/provider-capabilities.yaml` (Default-Flip
  aufgeschoben). G4-2/3/5/7/8/9 und F-OC1 nur dann ändern, wenn am Code belegbar;
  sonst Aufschub mit Grund. **G4-6 REFUTED → keine Änderung.**

### IC-7 Token-Diät (G7)

- `scripts/lib/agents.py:515` (kompaktes JSON `separators=(',',':')`),
  `agents.py:343` (`name_index` aus Serialisierung; Verbrauch `:582` bleibt),
  `scripts/lib/config.py:1649` + `templates/configs/AGENTS.project-template.md`
  (AGENT_TABLE-Block per Flag), `rules/1-generic/branch-guard.md` (Abschnitte
  Terminologie/Bekannte Grenzen → `docs/concepts/`, Kurzfassung bleibt),
  `scripts/lib/generated_file_drift.py:152-207` (Backup-Prune `*.sync-backup-*`),
  F6-11 `hook_json_get` Single-Parse (Aufwand M, ggf. aufgeschoben).
- Betroffene Pins: `tests/fixtures/ac01-baseline/hashes.json`,
  `tests/test_context_budgets.py`, `tests/test_template_slimming_equivalence.py`,
  compact-golden.

## Datenfluss

```
Audit-Report (.tmp/…)  →  Gegenprüfung (Verdikt)  →  Plan-Tabelle (Fund → Fix/Test/Gruppe/Issue)
        │
        ▼
Gruppe Gn:  Issue (feedback) → Branch von origin/main → Test rot → Fix in Quelle
        → sync + --validate + consistency-check → Reviewer-Gate → git (Commit/Push/PR)
        → CI-Watcher → Checkpoint → nächste Gruppe
```

Ausgabe-Artefakte (`.claude/`, `.agents/`, `.gemini/`, `.opencode/`) entstehen nur
durch `python scripts/sync.py` aus der Quelle.

## Acceptance Criteria

1. **AC-1 (F6-01):** Ein Hook-Test belegt: `NotebookEdit` mit `notebook_path=/etc/x.ipynb`
   endet in `repo-containment` **und** `orchestrator-guard` (Strict-Mode, Main-Chat) mit
   rc 2; `MultiEdit` verhält sich wie `Edit`.
2. **AC-2 (F6-02):** Ein Paritätstest listet die neun fehlenden Toolnamen und die zwei
   korrigierten `...Tool`-Namen als akzeptiert; ein unbekannter Name bleibt rc 2.
   `PowerShell` wird vor dem Allow-Zweig wie `Bash` behandelt.
3. **AC-3 (F6-03 Teil):** `echo "$(git push origin main)"` und die Backtick-Variante
   blockieren in `dod-push-check` und `orchestrator-guard`; `eval`/`bash -c`-Varianten
   bleiben dokumentiert offen (Ref #592).
4. **AC-4 (F6-04):** Jedes der elf Verben (`stash` nackt, `mv`, `apply`, `notes`,
   `replace`, `update-index`, `config`, `fast-import`, `init`, `submodule update`,
   `gc`) wird im Strict-Mode für den Main-Thread blockiert; Read-only (`status`, `log`)
   bleibt erlaubt.
5. **AC-5 (F6-05):** Ohne `agent_id` greift `#agent-meta:agent=git` nicht; ein Test mit
   gesetzter Capability für agent_id-lose Provider belegt den Pfad; der alte Test
   `test_strict_mode_sentinel_exemption` ist ersetzt.
6. **AC-6 (F6-06/07/09/10/12):** Tilde/`$HOME`, `curl -o`, `wget -O`, `tar -C`,
   `unzip -d`, `git clone` außerhalb der Wurzel blockieren; `cd`/`pushd`-Kette wird
   getrackt; `$'` im Quote-Kontext wird nur unquotiert gewertet; graphify-Guards geben
   nur 0/2 zurück; Kommentar-Platzhalter wird nicht mitersetzt.
7. **AC-7 (F3-02/03):** Regeltext `use-orchestrator.md` nennt „nur bei `strict: false`";
   `Agent` mit `subagent_type=orchestrator` oder `isolation=worktree` bei `agent_id`
   → rc 2.
8. **AC-8 (F1):** Ein Subprozess-Test mit `tomllib`/`tomli` = `None` importiert
   `sync.py` ohne `ModuleNotFoundError`.
9. **AC-9 (F2, F3, F4, F8, F9, F11):** Je ein Test belegt: `--deactivate-providers`
   wirft keinen `TypeError`; ungültiges Frontmatter-YAML gibt Inhalt unverändert zurück
   + Warnung; `hooks: {x: true}`/`viz: true` führt zu Warnung statt
   `AttributeError`; kaputtes Schema-JSON warnt; `KeyboardInterrupt` wird nicht
   geschluckt; Py3.9-Guard deckt `scripts/*.py` ab.
10. **AC-10 (F5):** `sync --check` endet mit Exit 1, wenn `log.errors` nicht leer ist;
    die Plain-Sync-Policy ist als Entscheidung im PR dokumentiert; `tests/test_sync_end_checks.py`
    ist entsprechend angepasst.
11. **AC-11 (F6, F7, F10):** Eine 0755-Datei behält ihr Exec-Bit nach `write_atomic`;
    Secret-Dateien bleiben 0600; `project.yaml`-Schreibpfade nutzen `write_atomic` und
    erhalten CRLF; die 19 `subprocess.run(text=True)`-Stellen tragen `encoding="utf-8"`.
12. **AC-12 (F3-01/04):** Der gerenderte Claude-Orchestrator trägt `SendMessage` und
    `TaskStop`; BARRIER definiert „kein Report = failed"; `test_subagent_allowlist_frontmatter.py` ist grün.
13. **AC-13 (K-01..K-06, K-13, K-10):** Bei Preset `rapid-prototyping` enthält die
    gerenderte Ausgabe keine ungegateten REQ-/Test-Pflichtzeilen (Test per Render);
    ein Drift-Gate meldet stale `.claude/`-Output; `feature-lifecycle` kann ohne
    Approval-Stage nicht in `implement`; `planner` verlangt `Status: APPROVED`;
    spec/plan nutzt einen Key.
14. **AC-14 (G5):** Jeder AUDIT-ONLY-Fund ist vor dem Fix am Code belegt oder mit
    Begründung verworfen; `test_provider_agnostic_dispatch.py` deckt Dict-Key-Literale
    ab.
15. **AC-15 (G6):** G4-6 bleibt unverändert; in `provider-capabilities.yaml` steht ein
    Antigravity-Hinweis zu `agent-discovery`; aufgeschobene Funde haben Begründung.
16. **AC-16 (G7):** `route_intent`-JSON im gerenderten Orchestrator ist kompakt und
    ohne `name_index`; `AGENTS.md` ohne AGENT_TABLE-Block per Flag; Orchestrator-Token
    sinken messbar (Vorher/Nachher-Messung im PR); alle Pins sind bewusst neu erzeugt.
17. **AC-17 (global):** Nach jeder Gruppe: `python3 scripts/sync.py --validate` rc 0,
    `python3 scripts/consistency-check.py` rc 0, serielle Test-Subsets grün (kein
    `-n auto`), `git status` clean außer beabsichtigter Dateien.

## Offene Fragen + Risiken

| # | Frage/Risiko | Behandlung |
|---|---|---|
| OQ-1 | F5: Soll auch Plain-Sync bei `log.errors` mit Exit 1 enden? | Entscheidung in G2 treffen, dokumentieren (D6); Default: nur `--check`. |
| OQ-2 | K-07 (ein REQ-Format) Aufwand M | In G4 prüfen; bei Unverhältnismäßigkeit aufschieben + begründen (D8). |
| OQ-3 | F6-11 Single-Parse (M) | In G7 prüfen; ggf. aufschieben. |
| R-1 | Zweite Session ändert den Baum | Serielle Ausführung, Baum-clean-Check vor jeder Gruppe, keine Branchwechsel parallel. |
| R-2 | Golden-/Baseline-Pins brechen (Test-Environments 1.3.3, Release-Checklist, ac01, slimming, compact, Context-Budgets) | Vorab mitprüfen; nur bei beabsichtigter Änderung per Eintrag neu erzeugen. |
| R-3 | Hook-Fix bricht Provider ohne `agent_id` (Gemini) | D5: Capability-Flag; Test für beide Fälle. |
| R-4 | AUDIT-ONLY-Funde stellen sich als falsch heraus | AC-14: vor Fix am Code belegen. |
| R-5 | Externe Aussagen (Gemini/Antigravity, Claude-SDK) unverifiziert | Nur Doku-Hinweis, kein Code-Verhalten auf Basis unbelegter Aussagen. |
| R-6 | Hook-Latenz steigt durch zusätzliche Prüfungen | Messung vorher/nachher im PR; F6-11 adressiert die Ursache in G7. |

## Trace-Anker

`spec-id: SPEC-system-audit-remediation-2026-11-06`
