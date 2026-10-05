---
title: Priorisierter Issue-Backlog — Ausführungsplan
status: proposed
date: 2026-10-04
repo: Popoboxxo/agent-meta
commit: v2.0.0-beta.1 (4bf62652)
source: GitHub REST API + Web-UI (live 2026-10-04) / Research 2026-10-03
scope: Strategie & Reihenfolge — keine Implementierung
---

# Priorisierter Issue-Backlog — Ausführungsplan

> **STATUS: proposed** · Datum: **2026-10-04**
> **Quelle:** GitHub-REST-API (`/issues?state=open&labels=P1|P2|P3`) + Web-UI, verifiziert 2026-10-04; ergänzend Research-Inventar 2026-10-03.
> **Repo/Commit:** `Popoboxxo/agent-meta` @ `v2.0.0-beta.1` (`4bf62652`), Branch `main`.
> **Charakter:** Strategie-/Reihenfolge-Dokument. Es wird **nichts** umgesetzt; jeder Fix folgt dem Spec→Plan→Execution-Gate.

## 1. Scope & Methodik

### Scope

Ausführungsreihenfolge und Abhängigkeitsstruktur **aller 39 mit Priorität gelabelten offenen Issues** (P1/P2/P3, kein P0). Das Dokument beantwortet *was zuerst, warum, und was blockiert was* — nicht *wie* (das liefert jeweils die Feature-Spec/das Feature-Plan-Artefakt).

Nicht im Scope: die ~60 ungelabelten offenen Issues (kein Prioritätssignal), sowie die eigentliche Code-Änderung.

### Methodik

1. **Live-Inventar als Source of Truth:** GitHub-Labels via REST-API/UI am 2026-10-04 verifiziert. Zählung: **P1 = 5, P2 = 23, P3 = 11 → 39**.
2. **Abgleich Research (2026-10-03) vs. Live:** Label-Zuordnungen wurden issue-für-issue gegen die Live-API geprüft; Abweichungen sind in §2.1 dokumentiert und in der Planung korrigiert.
3. **Ordnung nach Risiko/Impact-first** mit harten Abhängigkeiten: ein Issue, dessen Fehler andere Fixes blockiert (z.B. blockierte Commits, unzuverlässiges `--check`), kommt vor den darauf aufbauenden.
4. **Provider-agnostisch:** Capability-Flags/Config-Keys statt Provider-Namens-Literale (siehe §6).
5. **Aufwand:** grobe Aufwandszusammenfassung über den `effort-estimator` (Text-Referenz, kein Tool-Call) — nach Freigabe dieses Plans.

### 2.1 Label-Abgleich Research (2026-10-03) vs. Live (2026-10-04)

| # | Research-Claim | Live-Label (autoritativ) | Wirkung auf Planung |
|---|---|---|---|
| **#826** | unter P2 (und doppelt unter P3) | **P1** (`bug, P1, tests`) | → **Phase 0** (Fix-Commit `a166850b` liegt vor) |
| **#767** | unter P1 | **P2** (`bug, config, P2, hooks, consistency, provider-abstraction, templates`) | bleibt aus Impact-Gründen in **Phase 1**, Label-Realität P2 vermerkt |
| **#810** [F04] | unter P2 | **P3** (`improvement, P3`) | → Phase 2 (F-Serie) |
| **#811** [F15] | unter P2 | **P3** (`design, P3`) | → Phase 2 (F-Serie) |
| **#812** [F26] | unter P2 | **P3** (`improvement, P3`) | → Phase 2 (F-Serie) |
| **#850** | unter P2 | **P3** (`bug, config, P3`) | → Phase 0 (Hygiene) |
| **#809** | unter P2 | **P2** (`rule-violation, design, P2`) | bestätigt |
| **#808** | unter P2 | **P2** (`bug, hooks, P2`) | bestätigt |
| **#806** | unter P2 | **P2** (`bug, config, P2`) | bestätigt |

Zusätzlich war das Research-Inventar in sich inkonsistent (P2 mit 27 Einträgen gelistet, aber als „23" deklariert; #826 doppelt geführt). Die Live-API liefert die eindeutige 5/23/11-Verteilung.

## 2. Vollständiges Inventar (39 Issues)

Gruppiert nach **Live-Label**. Spalte „Wirkung/Abhängigkeit" nennt den Haupteffekt und issue-übergreifende Bezüge.

### P1 (5)

| # | Kurztitel | Live-Labels | Wirkung / Abhängigkeit |
|---|---|---|---|
| 826 | repo-copy Self-Hosting-Test rekursiert in eigene pytest-basetemp → 16 GB Host-Disk voll | bug, P1, tests | Host-Gefahr; Fix-Commit `a166850b` (Branch `fix/test-copytree-basetemp-recursion`) inkl. Akzeptanzkriterien vorhanden → Merge/PR |
| 862 | Codex TOML 58/58 ungültig bei debug/viz/footer/path-rules; `sync --check` rc=1 | bug, ci, P1, provider-abstraction, sync | Blocker für frisch geklonte CI-Gates; Root-Cause `agent_sync.py::_finalize_agent_content` (Block-Injection vor TOML-Serialisierung) |
| 802 | [F07] `--check` als CI-Gate auf Fresh Clone (`rc=1`, gitignored Skeletons als Drift) | bug, ci, P1 | CI-Gate-Vertrauen; Bezug #739; hängt inhaltlich an #862 |
| 843 | kimi-code Provider-Instanziierung (7 Findings: fehlender orchestrator, Bootstrap-Block, Skills/Hooks, Modell-IDs) | agents, bug, hooks, P1, provider-abstraction, sync, templates | Größte Provider-Lücke; blockiert Provider-Parität |
| 831 | `sync.py --scan-staged` scannt Index-Version statt staged diff → Bestandszeilen blockieren Commits | bug, P1, sync | Blockiert **jeden** Commit-Flow; `cli_commands.py::handle_scan_staged`, `secrets.py::scan_for_secrets`; Bezug #694, #68 |

### P2 (23)

| # | Kurztitel | Live-Labels | Wirkung / Abhängigkeit |
|---|---|---|---|
| 767 | `auto_commit` per-edit/task-boundary wirkungslos (bash:deny + Commit-Authority, keine Hooks) | bug, config, P2, hooks, consistency, provider-abstraction, templates | Commit-Granularität; Bezug #694, #699 (closed), #702 (closed) |
| 863 | 2 Admin-UI-Browser-Tests rot (surface-version-Panel kollabiert / Add-Row-Default) | bug, P2, tests | Release-Rot im Admin-UI-Testpfad |
| 864 | `--init`/`--fill-defaults` lassen `project.yaml` auf 0644 (nur Admin-UI chmod 0600) | bug, config, P2, security | Secret-Hygiene (admin-ui.token/MCP-Credentials) |
| 856 | zcode Workspace Agent-Auto-Load ungeklärt + commands-Capability under-claim | bug, P2, provider-abstraction, templates | Provider-Capability-Korrekt |
| 855 | copilot prompt-file/subagent-Capabilities under-claimed | improvement, P2, templates | Provider-Capability-Korrekt |
| 854 | antigravity `.gemini/commands/*.toml` ist kein echtes Command-Contract | improvement, P2, templates | Provider-Capability-Korrekt |
| 853 | mammouth `.mammouth/settings.json` inert (Loader liest mammouth.json/opencode.json) | bug, configuration, mammouth, P2 | Provider-Config-Korrekt |
| 852 | mammouth bare Model-IDs unresolvable (kein provider/model-id-Präfixkontrakt) | bug, mammouth, P2 | Provider-Config-Korrekt |
| 851 | claude Hook-Commands cwd-abhängig → `${CLAUDE_PROJECT_DIR}` verankern | bug, claude, hooks, P2 | Hook-Robustheit; Bezug #808 |
| 849 | `--check`-Artifact-Gate validiert committed MCP-Dokument nicht | P2 | Gate-Konsistenz; Bezug F-Serie |
| 848 | plan-graph `file_overlap`-Validator zählt Prosa/Interfaces-Pfade als File-Ownership | P2 | Plan-Tooling-Korrektheit |
| 847 | admin-server Save strippt YAML-Kommentare aus `ai-providers.yaml` (kein Round-Trip-Guard) | P2 | Config-Verlust-Risiko |
| 844 | generierter Root-Context `AGENTS.md`/`CLAUDE.md` von 815→~200 Zeilen komprimieren | P2 | Token-Kosten/Context-Qualität |
| 842 | UTF-8-BOM aus agent-generierten Commit-Messages strippen | bug, P2, ci-cd, hooks, agents | Conventional-Commit-Parser; guard im gemeinsamen Commit-Pfad |
| 838 | Renderter Context-Datei-Inhalt wird nie gegen Deployment-Realität validiert | P2 | Fehlende Post-Render-Verifikation |
| 834 | `substitute_platform()` nicht im Context-Render-Pfad → `{{platform.*}}` ship unsubstituiert | P2 | Render-Korrektheit |
| 804 | [F09] `--backup`/`--list-backups`/`--restore` Round-Trip | P2 | Sync-Robustheit |
| 803 | [F05] `--dry-run` verändert nicht den Working Tree | P2 | Sync-Sicherheit |
| 805 | [F11] Provider-Deaktivierung/Reaktivierung hält Artefakte konsistent | P2 | Sync-Konsistenz |
| 807 | [F18] jeder Provider erhält Slash-Commands | P2 | Provider-Parität |
| 806 | [F14] `--only-variables` aktualisiert Variablen ohne Agenten-Regeneration | bug, config, P2 | Sync-Korrektheit (Variable nur in Managed-Blocks) |
| 808 | [F20] 8 generierte Claude-Hooks nie in `settings.json` registriert (Dead Code) | bug, hooks, P2 | Hook-Wirksamkeit; Bezug #767, #694 |
| 809 | [F23] Destructive-Gate blockt git force-push/reset-hard/clean, NICHT `rm -rf /` | rule-violation, design, P2 | Sicherheits-/Guard-Lücke; Bezug #516, #592 |

### P3 (11)

| # | Kurztitel | Live-Labels | Wirkung / Abhängigkeit |
|---|---|---|---|
| 810 | [F04] Undefinierte MCP-Variablen shipen literal (`{{MCP_HONCHO_URL}}`, `{{MCP_REQOGNILOOM_URL}}`) | improvement, P3 | Render-Korrektheit; warnen oder Block droppen |
| 811 | [F15] 1 aktive Rolle fehlt im Context-Katalog (`se-component-requirements`, 56 Rollen) | design, P3 | Katalog-Vollständigkeit; Bezug #528, #552 |
| 812 | [F26] A2A-Handoff-Payload-Limit (300 chars) dokumentiert, aber nicht maschinell erzwungen | improvement, P3 | A2A-Gate-Härtung; Bezug #346 |
| 850 | Schema `agent-meta-version`-Regex lehnt Pre-Release-Versionen ab | bug, config, P3 | Schema-Korrektheit (blockiert Pre-Release-Tooling) |
| 857 | mammouth skills/MCP-Capabilities deklariert, emittieren aber keine Artefakte | improvement, mammouth, P3 | Provider-Capability-Korrekt |
| 858 | codex/continue Skills-Surface deklariert mit null Artefakten | improvement, P3, provider-abstraction, templates | Provider-Capability-Korrekt |
| 859 | Changelog `[Unreleased]` enthält bereits in v2.0.0-beta.1 geshippte Einträge | documentation, P3 | Release-Doku-Korrektheit |
| 860 | antigravity Runtime-Verifikation blockiert (non-pclmul Host, SIGILL) | documentation, P3, templates | Tracking; Verdicts bleiben `[STATIC]` bis pclmul-Host |
| 861 | Merged Branch `chore/release-v2.0.0-beta.1` löschen | P3 | Branch-Hygiene (`deleteBranchOnMerge: false`) |
| 552 | STATUS/RESULT/ARTIFACTS-Contract in 34 verbleibenden Templates vervollständigen | improvement, P3, templates | A2A-Gate #5 / Ratchet-Test; Bezug #528, #541 |
| 603 | Signatur-/Checksum-Verifikation für release-gates-Scripts | improvement, P3 | Supply-Chain-Härtung; Bezug #598 |

## 3. Phasen (Risiko/Impact-first + Abhängigkeiten)

Hinweis: #802, #806, #808–#812 sind F-Serie-Elemente und werden in **Phase 1** (#802 als Anker) und **Phase 2** (Rest) bearbeitet. #767 ist live P2, bleibt aber wegen Blocker-Charakter in Phase 1.

### Phase 0 — Hygiene (sofort, klein & risikoarm)

| # | Aktion | Agent-Rolle | Begründung |
|---|---|---|---|
| 826 | Fix-Branch `fix/test-copytree-basetemp-recursion` (`a166850b`) prüfen → PR/Merge | tester / senior-developer | Host-Disk-Gefahr; Fix + Akzeptanzkriterien liegen vor |
| 842 | BOM-Guard im gemeinsamen Commit-Pfad (fail-closed, stderr) | developer | verhindert stillen Bruch der Conventional-Commits |
| 850 | `agent-meta-version`-Regex pre-release-fähig machen | developer | Schema blockiert Pre-Release-Tooling |
| 861 | Merged Branch `chore/release-v2.0.0-beta.1` löschen | git | reine Hygiene, kein Code-Risiko |

### Phase 1 — P1-Blocker (Reihenfolge verbindlich)

`#831 → #862 → #802 → #767 → #843` (mit **#826 aus Phase 0 vorangestellt**).

| Schritt | # | Warum diese Position |
|---|---|---|
| 1 | 831 | **Zuerst:** blockiert jeden Commit (`--scan-staged` bestraft Bestandszeilen). Ohne diesen Fix kann Folgearbeit nicht sauber committed werden. |
| 2 | 862 | Codex-TOML-Invalidität erzeugt `--check` rc=1 und ist direkte Ursache für das rote Fresh-Clone-CI-Gate (#802). Vor #802 zu fixen. |
| 3 | 802 | [F07] macht `--check` erst als CI-Gate vertrauenswürdig (INIT-Einträge, gitignored Skeletons). Basis für alle nachfolgenden Gate-Änderungen. |
| 4 | 767 | `auto_commit`/Commit-Granularität ist Fundament für reviewbare inkrementelle Commits der restlichen Phasen. |
| 5 | 843 | kimi-code Provider-Instanziierung: größte Provider-Lücke, profitiert von stabilem Sync/Check/Commit-Fundament. |

### Phase 2 — Sync-/Gate-Konsistenz (ein Workstream)

Die F-Serie #802–#812 wird als **ein zusammenhängender Workstream** gefahren (gemeinsamer Sync-/Gate-Kontext, geteilte Testartefakte), ergänzt um die zugehörigen Konsistenz-/Security-Issues:

**F-Serie:** #802 (Anker, bereits Phase 1), #803, #804, #805, #806, #807, #808, #809, #810, #811, #812.
**Ergänzend (nicht F-Serie):** #849, #834, #838, #847, #864.

| Rolle | Beispielhafte Tasks |
|---|---|
| developer / senior-developer | Sync-Flags (#803, #804, #805, #806, #807), Render-Pfad (#834, #838), MCP-Dokument-Gate (#849), YAML-Round-Trip (#847), Dateimodus 0600 (#864) |
| developer | Hook-Registrierung (#808), Destructive-Gate-Tokenizer (#809) |
| tester | Ratchet-/Regressions-Tests je Fix (besonders #808, #809, #834, #838) |

### Phase 3 — Provider-Capabilities (pro Provider ein PR)

| Provider | Issues | Rollen |
|---|---|---|
| zcode | 856 | senior-developer, tester |
| copilot | 855 | senior-developer, tester |
| antigravity | 854 | senior-developer, tester |
| mammouth | 853, 852, 857 (gebündelt) | senior-developer, tester |
| claude | 851 | developer, tester |
| codex/continue | 858 | senior-developer, tester |

Regel: **ein PR pro Provider**, Umsetzung ausschließlich über Capability-Flags/Config-Keys (§6).

### Phase 4 — Admin-UI & Tests

| # | Task | Rolle | Begründung |
|---|---|---|---|
| 863 | 2 rote Browser-Tests grün bekommen (Panel expandieren bzw. Default setzen) | frontend-component-engineer / e2e-tester | Release-Test-Rot; unabhängig von Sync-Kern |

### Phase 5 — Templates & Context

| # | Task | Rolle |
|---|---|---|
| 844 | Root-Context `AGENTS.md`/`CLAUDE.md` von 815→~200 Zeilen komprimieren | senior-developer / documenter |
| 552 | STATUS/RESULT/ARTIFACTS-Contract in 34 Templates + Ratchet-Test erweitern | developer, tester |

### Phase 6 — Release & Doku

| # | Task | Rolle |
|---|---|---|
| 859 | `[Unreleased]`-Changelog-Einträge, die bereits in v2.0.0-beta.1 geshippt sind, verschieben/entfernen | release |
| 860 | antigravity Runtime-Verifikation auf pclmul-fähigem Host ausführen (Tracking) | claude-expert / documenter |
| 603 | Signatur-/Checksum-Manifest für release-gates-Scripts | devops-engineer / senior-developer |

## 4. Abhängigkeits-DAG (ASCII)

```
Phase 0 (parallel, risikoarm)
   #826  #842  #850  #861
     |
     v
Phase 1 (sequentiell)
   #831 --> #862 --> #802 --> #767 --> #843
     |         \      /                 |
     |          \    /                  |
     |           v  v                   |
Phase 2 (ein Workstream)                |
   F-Serie: #802(Anker) #803 #804 #805 #806 #807 #808 #809 #810 #811 #812
   + #849 #834 #838 #847 #864
     |                                   |
     |            Phase 4: #863         |
     |            Phase 5: #844, #552    |
     |                                   |
     v                                   v
Phase 3 (pro Provider ein PR)
   zcode #856 | copilot #855 | antigravity #854
   mammouth #853 #852 #857 | claude #851 | codex/continue #858
     |
     v
Phase 6 (Release & Doku)
   #859  #860  #603
```

Legende: `-->` = harte Abhängigkeit (Vorgänger muss stehen). Phasen 3–5 können nach Phase 2 teilweise parallel laufen; Phase 6 schließt ab. #850 ist Voraussetzung für saubere Pre-Release-Versionierung in allen Folgephasen.

## Querschnittsregeln

- **Branch-Guard:** ausschließlich Feature-Branches (`feat/`, `fix/`, `chore/`); **kein** Direct-Push auf `main`/`master`. Git-Mutationen laufen über den `git`-Agenten.
- **Provider-Agnostik:** Capability-Flags/Config-Keys statt `if provider == "..."`. Provider-Namens-Literale sind unzulässig (siehe `provider-agnostic`-Skill).
- **Version-Bump + CHANGELOG:** bei Template-/Config-Änderungen `VERSION`/`package.json` bumpen und `CHANGELOG.md` pflegen.
- **Verifikation:** pro Fix `python3 scripts/sync.py --validate`, `python3 scripts/sync.py --check` und `pytest`. Für #862 zusätzlich TOML-Validität (`tomllib.load` über `.codex/agents/*.toml`) unter aktivem `debug-mode`.
- **Issue-Lifecycle:** Closing-Keywords im Commit/PR (`Fixes #NNN`) plus Post-Completion-Kommentar je Issue.
- **Keine Implementierung ohne Gate:** jeder Task durchläuft Classification (S/M/L/XL) → Spec (`Status: APPROVED`) → Plan → Ausführung (`spec-plan-workflow`).

## Empfehlung zum Start

1. **Phase 0 sofort:** #826 (Fix liegt vor → PR/Merge), #842, #850, #861 — geringes Risiko, hoher Hygiene-Nutzen, schaltet Pre-Release-/Commit-Tooling frei.
2. **Danach Phase 1 sequentiell:** **#831 → #862 → #802** — diese drei stellen Commit-Fähigkeit und ein vertrauenswürdiges `--check`-CI-Gate wieder her und sind Vorbedingung für alles Weitere.
3. Freigabe dieses Plans vor Start; Aufwandszusammenfassung via `effort-estimator` nach `Status: APPROVED`.
