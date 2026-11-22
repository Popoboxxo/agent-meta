# Master-Roadmap — agent-meta (Stand origin/main 6bdc31ec, 2026-11-15)

> Status: APPROVED (User, 2026-11-19, „E17 approved + Roadmap approved — volle Umsetzung 2.3") — Roadmap
> Datum: 2026-11-15
> Quelle: Fable-Review, Entscheidungen des Nutzers vom 2026-11-15
> Art: Nur Planung, nichts umgesetzt. Keine Tests, Syncs oder Renders ausgeführt.

Verknüpfte Pläne (2026-11-14):

- [Bugfix-Batch 3](2026-11-14-bugfix-batch-3-plan.md)
- [Audit-Top5-Ausführung](2026-11-14-audit-top5-execution-plan.md)
- [Verbesserungsschleife](2026-11-14-agent-improvement-loop-plan.md)
- [Intent-Routing-Tabelle](2026-11-14-intent-routing-table-plan.md)

Audits: `docs/analysis/2026-11-15-fable-framework-settings-audit.md`, `docs/analysis/2026-11-15-fable-language-feature-audit.md`, `docs/analysis/2026-11-15-fable-orchestration-rollout-audit.md`, `docs/analysis/2026-11-15-fable-verification-of-unchecked.md`, `docs/analysis/2026-11-14-audit-prioritization.md`.
Specs: `docs/specs/2026-11-11-git-agent-merge-permission-spec.md`, `docs/specs/2026-11-11-guard-destructive-ask-spec.md`, `docs/specs/2026-11-11-guard-role-attribution-spec.md`, `docs/specs/2026-11-11-hook-single-parse-spec.md`, `docs/specs/2026-11-09-commit-authority-grant-spec.md`, `docs/specs/2026-11-09-artifact-locations-matrix-spec.md`, `docs/specs/2026-11-09-issue-label-taxonomy-spec.md`. Phasenpläne D–I liegen auf origin/main (nicht in diesem Branch) und werden hier nur als Text referenziert.

## Ergebnis der Entscheidungsrunde (Kurzfassung)

- Knowledge Engine bleibt AN; DoD-Preset bleibt `rapid-prototyping`; Rules-Kürzung entfällt (`use-lazy-rules` bleibt, `max_depth` bleibt 10). Damit entfallen DoD-/KE-/Rules-Teile aus Welle 2 und die Rules-Golden-Rebaseline aus 1.4.
- Rebaseline-Pflichtzahl sinkt von 8 auf **7** (Begründung in §3.8).
- Git-Agent-PR (Trailer-Contract als Config-Key) wird nach vorn gezogen (W0/W1).
- Gemini = nur Gemini CLI (kein Antigravity).
- #1210 und #1169 sind jetzt freigegeben; #1217 und #1172 bleiben DRAFT.

## 1. Inventar der Arbeitspakete

Legende: Art = B Bugfix · C Config · T Template/Render · D Doku · A Audit · S Sync-Code. RB = Rebaseline-Auslöser (H = Hash-Dateien generated-file-hashes.json/context-hashes.json, AC = AC-01-Hashes, G = Goldens compact/topology/slimming/Rules, SA = standalone-Fixtures, B = `tests/test_context_budgets.py`-Ceilings). Stand: origin/main 6bdc31ec (#1280); Pläne identisch in `docs/plans/` (#1277). Änderungen gegenüber dem Review sind kursiv markiert (E-xx = Entscheidung, §4).

| # | Paket | Quelle | Issues | Art | Templates? | RB | Aufwand | Status / Gate |
|---|---|---|---|---|---|---|---|---|
| P1 | Batch-3 PR 1 Viz/MCP (fix/batch3-viz-mcp) | bugfix-batch-3 PR 1 | #1259 #1260 #1271 (+mjs löschen) | B | nein | H (.mcp.json) | S | bereit; *E-03: mjs löschen, #1260 nur per Config (explizites enabled:false schlägt Plattform-Bundle)* |
| P2 | Batch-3 PR 2 Guard/Sync (fix/batch3-guard-sync) | bugfix-batch-3 PR 2 | #1258 #1252 #1142 #1270 #1249 (Teil) #1241 #1266 | B/S | nein (Hook-Skripte) | H (Hook-Hash) | M | bereit; *E-09: #1249 Tier-Fold = nur Test + ein Doku-Satz (verweist auf #1257), #1270 30-Tage-Regel ja, .bak nicht prunen* |
| P3 | Batch-3 PR 3 TMPDIR (fix/batch3-tmpdir-determinism) | bugfix-batch-3 PR 3 | #1246 #1261 | B/C | nein | keiner bei B+ | S–M | *E-02: Variante B+ (Key temp-root + env-freier Default); E-09: #1261 nur WARN* |
| P4 | #1237 Rebaseline-Helper (+#1115) | Settings-Audit A.7/B.3; Loop-Plan; Phase H Task 6 | #1237 #1115 | S/Tests | nein | keiner (Tooling) | M | *E-10: Mini-Spec ist noch zu SCHREIBEN; Status dann APPROVED (User, 2026-11-16)* |
| P5 | Config-Hygiene PR-A | Settings-Audit A.7 #1–3 | (neu) #1263 #946-Tabelle | C | nein | nur H (Hash) | S | *E-11: Plugins honcho + reqogniloom aus; #946-Tabelle dem Nutzer vorlegen. Rules-Golden entfällt (Vorbehalt in §3.8)* |
| P6 | Roster PR-B | Settings-Audit A.7 #4 | #1244 (Roster-Teil) | C | ja (Roster, Enum) | AC, G (3 Provider), B, H, Allowlist | M | *E-12: Prinzip 58 → ~30 ja, Rollenliste ausstehend (separater Auftrag). Entfallen: DoD-Preset (E-13), Knowledge-Engine-Abschaltung (E-14), Rules-Kürzung (E-15)* |
| P7 | Release-Checklist PR-C | Settings-Audit A.7 #10 | — | C | nein (release-Render) | H, ggf. G | S | nachrangig; läuft in 2.2 mit |
| P8 | Sprach-PR 1 „restore language rule scope“ | Language-Audit §5 | (neu) | T | ja (`rules/1-generic/language.md`, `agents/1-generic/orchestrator.md:405`, speech-Regeln) | AC, G, B (+0,3 KB) | S | *E-16 Matrix wie empfohlen; inkl. {{DOCS_LANGUAGE}}-Fix in orchestrator.md:405* |
| P9 | Sprach-PR 2 „typed language matrix“ | Language-Audit §5 | #1204 (Teil) (neu) | C/S/T | ja | Scenario-Configs, ggf. AC | M | Spec fehlt; *E-28: Eingabe- UND Ausgabesprache dynamisch einstellbar (Schema-Keys), Framework-Default en für Prompt-Sprache, Hook-Warnung `gh pr create` nein/optional konfigurierbar* |
| P10 | Orchestrierung PR A (Config/Checks) | Rollout-Audit §5.3 | O5 O8 O9 O10 O12 (neu) | C/S | nein | keiner | S | bereit; *E-05: hybrid = reserved, orchestrator.strict/enabled deprecaten* |
| P11 | Orchestrierung PR D (Goldens 6 Provider + Tool⊆FM-Test) | Rollout-Audit §5.3 | O15 (neu) | Tests | nein | neue Goldens (einmalig) | M | vor PR B; *E-26: Gemini nur CLI, keine Antigravity-Variante* |
| P12 | Orchestrierung PR B (Worker-Control-Capability) | Rollout-Audit §5.3 | #1176 (erweitert) O1 O4 O11-Teil | T/C | ja (`agents/1-generic/orchestrator.md`, `config/provider-capabilities.yaml`) | AC, G, H, B | M | *E-17: Capability pro Provider (ersetzt Phase-D-Task 3/#1176), Continue `subagent` → WARNING, primary Claude/Kimi als prose-only gemeldet* |
| P13 | Orchestrierung PR C (Gemini-Dispatch) | Rollout-Audit §5.3 | O2 #1160 | T/C | ja (Gemini-FM) | Gemini-Golden | S | *E-26: nur Gemini CLI; #1160 damit entschieden* |
| P14 | Phase D Rest (#1172 Doku, #1176, #1168 Trailer) | phase-d | #1172 #1176 #1168 #1247 | T/D | ja (`agents/1-generic/orchestrator.md`, `agents/1-generic/git.md`) | AC, G, B | S–M | *E-18: #1172 nur Doku in W2, Permission-Regel erst bei positiver Machbarkeit (W4). E-19: Trailer-Contract KONFIGURIERBAR (Config-Key), Contract in git.md, Git-Agent-PR kommt ZUERST (§3, PR 0.9)* |
| P15 | Phase D Strom C Hooks | phase-d Tasks 5–9 | #1169 #1238 #1210 #1250 #1217 | B/S | nein | Hook-Hash | L | *E-24: #1210 + #1169 JETZT APPROVED; #1217 erst nach Task 1a (ask-API), bleibt DRAFT; E-25: #1238 in #1169-PR* |
| P16 | Phase D Strom A (#1181) + #1141 | phase-d Block A | #1181 #1141 | S/C/T | ja (Commit-Authority-Blöcke) | AC, G, Allowlist | L | nach F (#1188); *E-21: #1141 als eigener S-PR nach F* |
| P17 | Phase E Phasen-PR (feat/phase-e-artifact-locations) | phase-e | #1187 #1198 #1186 #1199 #1200 (+#1197) | S/C/T | ja (70/98 Templates) | AC, G, SA, B, H — größte Rebaseline | XL | Specs APPROVED; *E-20: #1188 wieder öffnen = Nutzer-Aktion bei Phase-E-Start; E-C0-Messung akzeptiert* |
| P18 | Phase E-2 #1209 Artifact-Mode-Gating | phase-e Block 4 | #1209 | S/T | ja | AC, G | M | *E-22: Spec E-T7 einzeln zum Wellenstart nach Review (DRAFT bis dahin)* |
| P19 | Phase F-PR1 (#1188, #1203, #1204) | phase-f | #1188 #1203 #1204 | S/C/T | ja | AC, G, B | L | Spec #1188 APPROVED; nach E-Kern |
| P20 | Phase F-PR2 (#1202, #1201) | phase-f | #1202 #1201 (#1211 gesperrt) | S/C | ja | AC, G | M | *E-22: Kinder-Addendum einzeln zum Wellenstart (DRAFT bis dahin)* |
| P21 | Phase G-PR1 (#800, #1171 xfail, #1175, #860 Runbook) | phase-g | #800 #1171 #1175 #860 | S/D | nein | H | S | bereit nach Phase B |
| P22 | Phase G-PR2 (#814, #800 Hermes, #1160/#854 Gemini) | phase-g | #814 #800 #1160 #1171 #854 | S/C/T | ja (Gemini) | G (Gemini), SA | L | *E-26: Gemini-Goldens/Gates nur CLI; #860 extern blockiert; E-31: Specs einzeln nach Review* |
| P23 | Phase H1 (#969 Eval-Gate T1–4, #1115, #1161 Pkt 4, Gate-Tasks …) | phase-h | #969 #1115 #1161 #779 #780 #778 #1014 #960 #1159 #1158 #1167 | S/Tests/D | nein | H (Backups-Prune) | L | Spec #969 APPROVED; übrige Gates DRAFT |
| P24 | Phase H2 (#969 Baseline-Run, #1161 Pkt 5, #779/#780, #1167 …) | phase-h | wie P23 | S/T | ja | AC, G, B | L | *E-27: #969-Baseline erst nach Kostenschätzung + erneutem Ja* |
| P25 | Intent-Routing PR 1 (docs/intent-routing-spec) | intent-routing Block A | #1161 #779 #1243 (Ref) | D/A | nein | keiner | M | *E-07: Taxonomie informativ; Spec-Freigabe nach Review* |
| P26 | Intent-Routing PR 2 (feat/intent-routing-model) | intent-routing Block B | #1161 Pkt 2 #1243 | S/C/T | ja (`agents/1-generic/orchestrator.md`, `rules/1-generic/use-orchestrator.md`, `config/role-defaults.yaml`) | AC, G (4 Sets), B, H — zweitgrößte Rebaseline | L | *E-23: kompaktes Zeilenformat als Default, name_index reduzieren, Direct-Dispatch generieren, Lazy-Detaildatei, Minor-Bump + CHANGELOG; NICHT das globale Compact-Profil* |
| P27 | Intent-Routing PR 3 (Admin-UI + Eval) | intent-routing Block C | — | S/UI | nein | H (Detaildatei) | L | nach PR 2; *E-27: Routing-Eval ja (< 1 USD)* |
| P28 | Loop Batch 0 (Mess-CLI, Lint, Ratsche, Schema) | loop-plan | #1244 (Ceiling-Test) #885-Ersatz | S/Tests | nein | keiner | M | nach Batch-3 PR 3 |
| P29 | Loop Batch 1 (H3 Block-Kürzung, H5 Descriptions-Lint) | loop-plan | — | T | ja (alle Worker-Blöcke) | AC, G, B, SA | M | H1 liegt in P26; *E-29: Prompt-Sprache Englisch, Issue-Nummern raus* |
| P30 | Loop Batch 2–10 (Rollen-Rewrite, ~15 PRs) | loop-plan | #1014 #778 (Rubrik) | T | ja (alle Rollen) | AC, G, B, SA je PR | L/XL | *E-29: Ziele/Ratsche hart, Claude-Evals nein, globales Compact NICHT aktiviert* |
| P31 | Loop Batch 11 (Ratsche hart, Doku) | loop-plan | — | Tests/D | nein | B | S | — |
| P32 | Audit-Top5 (Test-Suite, Admin-UI Sec+A11y, Knowledge-Lint, Doku-Wahrheit) | audit-top5 | #1276 (+#1245 #1159 Teil) | A/D | nein | keiner | L (250–345k Tok) | *E-06: jetzt (W0), pytest-cov temporär, Berichte per PR, Gate G1 Voll-Testlauf erst nach Stufe A + Ja des Nutzers* |
| P33 | Phase I Konzept-PRs | phase-i | #896 #339 #681 #832 #783 #1004 #1113 #676 #1106 #679 #957 #958 #329 #330 #820 #877 #548 | D | nein | keiner | je S–M | *E-31: Specs/Konzepte einzeln nach Review, Reihenfolge P33; #339 Re-Approval bei Phase-I-Start* |
| P34 | Hook-Kernel-Epic #1257 (+#1248 #1251 #1252-Rest #1256 #1249-Rest #1253–#1255) | Issues; Settings-Audit „SPÄTER“ | #1257 u. a. | S (Hooks) | nein | Hook-Hash | XL | *E-30: Konzept freigegeben nach 4.2, Unter-Issues unter #1257 zusammengelegt* |
| P35 | docs-Index-Branch docs/update-docs-index | Nutzer-Hinweis | — | D | nein | keiner | S | *E-01: Nutzer bot Push per `!`-Befehl an; unser Push wird vom git-Agenten erneut versucht* |
| P36 | Nicht verplante Befunde (Verif. §7 #1,3,4,5,6,11,14,15; Rollout O6/O7) | Verifikation; Rollout | (neu) | B/C/T | teils | s. §2.4 | S–M | → §2.4, §5 |
| P37 | *Git-Agent-PR (neu aus E-19): Trailer-Contract als Config-Key + Contract in git.md* | Audit-Top5 E9; Settings-Audit B.3 | #1168 #1247 | T/C | ja (`agents/1-generic/git.md`) | **AC, G, B (git.md ist Template)** | S | *E-19: wird zuerst gezogen, vor die W2-Bündel (§3 PR 0.9)* |

Entfallen gegenüber dem Review (Nutzerentscheidung): DoD-Preset-Wechsel (E-13), Knowledge-Engine aus (E-14), Rules-Kürzung inkl. `use-lazy-rules` aus, branch-guard-Auslagerung, use-orchestrator-Git-Prosa, `max_depth 3` (E-15).

Bereits erledigt (nicht im Inventar): #1235, #1236 (Phase D PR 1), #1277, #1280. Offene PRs: keine.

## 2. Konflikt- und Abhängigkeitsanalyse

### 2.1 Mehrfach berührte Dateien/Module

| Datei/Modul | Pakete | Regel |
|---|---|---|
| `agents/1-generic/orchestrator.md` | P8 (:405), P12, P14 (#1176, #1172), P26, P29/P30, Phase I #1004/#1113/#681 | strikt sequentiell; jede Änderung = AC/G/B-Rebaseline → bündeln |
| `agents/1-generic/git.md` | P37 (Trailer-Contract, neu vorn), P16 (#1181), P30 Batch 3 | P37 vor P16 vor P30; **P37 erzeugt eine eigene Rebaseline (Template)**, siehe §3.8 |
| `rules/1-generic/use-orchestrator.md` | P26 (Pointer-Zeile) | P6-Git-Prosa-Kürzung entfällt (E-15) |
| `rules/1-generic/language.md`, speech-Regeln | P8, P9, P30 | P8 vor P30 |
| `config/role-defaults.yaml` | P26 (patterns → routing), P6 (Roster), P24, Verif. §7 #3 (:11 permissionMode) | Roster (P6) vor P26 |
| `config/provider-capabilities.yaml` | P12, P26, Phase G, Phase H Task 8 | H-Task 8 durch P26 ersetzt |
| `scripts/lib/isolation.py` | P2 (#1249 nur Test + Doku-Satz), P12/O3, P34 (#1253) | Umbau erst P34 |
| `hooks/1-generic/orchestrator-guard-impl.sh` | P2 (#1258), P15 (#1169, #1210, #1217), P16 (#1181 T16), P34 | Reihenfolge P2 → P16-T16 → P15 → P34; nie parallel |
| `scripts/lib/sync_pipeline.py`, `scripts/lib/config.py`, Schema, Admin-Server/UI | P17, P19, P16 (#1141), P9, P10, P26/P27, P3 | Config-Welle E → F → D-A zuerst; P9/P26 danach rebasen |
| `tests/test_context_budgets.py`, AC-01, Goldens | P6, P8, P12, P14/P37, P16, P17, P19, P24, P26, P29, P30 | je Welle ein Rebaseline-Commit pro PR; P4 (#1237) zuerst |
| .mcp.json, generated-file-hashes.json | P1, P5, P26 | P1 + P5 mit Config-Weg abstimmen (Rebase) |

### 2.2 Logische Abhängigkeiten (verbindlich)

- P3 (#1246) → P4 (#1237) → alle Rebaseline-lastigen PRs (P6, P8, P12, P17, P19, P26, P29, P30).
- #1161 Pkt 2 (route_intent) nur in P26; Pkt 4 (Backups) in P23; Pkt 5 (`hook_json_get_many`) nach Phase D. #1244: Roster-Teil = P6, Ceiling-Test = P28/P23.
- Kette #1187 → #1186 (P17) → #1188 (P19) → #1181 (P16) → #1141-Ende; #1141 danach als eigener S-PR (E-21). P18/P20 nur nach APPROVED-Spec (E-22).
- Sprach-PR 1 (P8) vor Loop (P30) und vor Routing-PR 2 (P26); wird in dieselbe Rebaseline wie P12 gelegt.
- P37 (Git-Agent-PR) vor P16 und P30, da git.md Template ist.
- Phase D Strom C (P15) vor Hook-Kernel (P34). #1238 in #1169-PR (E-25). #1217 erst nach Task 1a; #1172-Permission-Regel erst nach Machbarkeit.
- Orchestrierung: PR A (P10) sofort; PR D (P11) vor PR B (P12); PR B ersetzt D-Task 3.
- Routing-PR 2 (P26) nach Config-Welle (E/F) und nach P6 (Roster).
- Loop Batch 2+ nach D/E; Batch 0/1 nach P3.
- Phase H2 Tasks 17/23/24 nach G; H-Task 10 nach D.
- Audit-Top5 (P32) und Phase I (P33) dateidisjunkt → jederzeit parallel.

### 2.3 Widersprüche zwischen Plänen / veraltete Annahmen

| # | Widerspruch | Auflösung (Stand Entscheidungen) |
|---|---|---|
| W1 | Compact-Profil: Loop-Plan E1 „sofort aktivieren“ vs. Verifikation §7 #20 („always-on +3 %, Inhaltsverlust“) und Settings-Audit „nicht empfohlen“ | Loop-E1 abgelehnt; **globales Compact wird NICHT aktiviert** (E-29); Ersparnis über P26 (kompaktes Zeilenformat, E-23) |
| W2 | Token-Zahlen Bytes/4 vs. tiktoken | Routing-PR 1 Task 0 (tiktoken) als erste Messung |
| W3 | H1 (route_intent kompakt) in drei Plänen | nur P26 (H-Task 8 wird Verweis) |
| W4 | #1176 doppelt: Phase D Task 3 vs. Rollout PR B | PR B ausführen, D-Task 3 streichen (E-17) |
| W5 | Roster-Reduktion: drei widersprüchliche Zeitpunkte | E-12: Prinzip ja, Liste separat; in W2 vor P26/P30 |
| W6 | Trailer: #1168 vs. #1247 vs. Audit-Top5 E9 | zusammengelegt; E-19: konfigurierbar, Contract in git.md, eigener Git-Agent-PR zuerst (P37) |
| W7 | Tier-Fold Opencode plugin vs. advisory | E-09: nur Test + ein Doku-Satz (#1257-Verweis) |
| W8 | #1141-Ort unklar, D-PR würde XL | E-21: eigener S-PR nach F |
| W9 | Audit-Top5-Plan nimmt Batch-3-Plan als nicht existent an | Triage-Senke = neuer Batch 4 |
| W10 | #1246: B+ ohne Rebaseline vs. Loop-E8 | E-02 B+; Reihenfolge bleibt (Determinismus für P4) |
| W11 | Sprach-Default en vs. CLAUDE.md „Deutsch“ | nur Framework-Default en für Prompt-Sprache (E-28); Projektwert bleibt de |
| W12 | DoD-Preset rapid-prototyping vs. CI verlangt pytest grün | **aufgelöst durch E-13: Preset bleibt rapid-prototyping**, kein Wechsel |
| W13 | Orchestrator `permissionMode: plan` (`config/role-defaults.yaml:11`) blockiert Write → Checkpointing (#1279) auf Claude wirkungslos | E-04: eigener kleiner PR auf `default`; falls AC-relevant → in 2.3 ziehen |

### 2.4 Lücken (nirgends verplant)

| Befund | Quelle | Vorschlag |
|---|---|---|
| permissionMode plan × Write/Checkpointing (#1279 Read-Side) | verif §7 #3 | PR 0.4 (E-04) |
| `primary`-Topologie degradiert still | verif §7 #4; rollout O6 | Check in P10, Prosa in P12 (E-17: Claude/Kimi als prose-only gemeldet) |
| `hybrid` überall wirkungslos | rollout O7 | E-05: Schema-Description „reserved“ → P10 |
| `knowledge.schema-language` toter Key | verif §7 #14 | S-Issue; in P9 oder P5 (Knowledge Engine bleibt an, nur toter Key) |
| viz-report.py ohne `html.escape` | verif §7 #11 | in P1 |
| Strict-/Fallback-Duplikate | verif §7 #17; rollout O8 | P10 (E-05: strict/enabled deprecaten) |
| `handoff.t-size-limit` Schema-Warnung + Doppel-Ausgabe | verif §7 #1 | P10 (O9) |
| PR-Body-Sprachregel fehlt (23/30 EN) | verif §7 #15 | P8; E-16: Tracker/Issues/PR en |
| Opencode v2 `default_agent`-Merge (primary) | verif §7 #5 | prüfen ob Issue offen; sonst neu (M) |
| `agent_id`-Evidence-Doc (#1210/#1250) | verif §7 #8 | S, in P15 |
| .continue/, `.bak`, 1 GB `.tmp` | verif §7 #19/#23 | P5 (E-09: .bak nicht prunen) |
| Claude-Toolliterale in generischem orchestrator.md (O11) | rollout | P12 + P30 |
| #1278, #1275, #1263, #1262/#1274, #1267/#1272, #1268/#1273, #1239/#1240, #1242/#1269 | Settings-Audit B.3 | #1263 W0 (S); Rest W5/W6 bzw. P34-Kette |

## 3. Master-Roadmap (Wellen mit Gates)

Prinzipien: (a) Token-Hebel früh, (b) Rebaseline nur in wenigen Render-Wellen, je ein Commit pro PR, (c) ein Branch von origin/main je PR, Squash-Merge, Nutzer merged, (d) parallel nur dateidisjunkte Doku/Audit-Arbeit (P32, P33, P25), (e) Specs mit Status DRAFT sind Gates, kein Code davor. Gemini-Arbeit gilt nur Gemini CLI (E-26).

### 3.1 Welle 0 — Sofort, ohne Golden-Rebaseline (parallel möglich)

| PR | Branch | Inhalt | Issues | RB | Gate |
|---|---|---|---|---|---|
| 0.1 | docs/update-docs-index | Push + PR des Docs-Index-Branches (E-01) | — | — | Push durch git-Agent erneut versuchen; Nutzer bot `!`-Push an |
| 0.2 | fix/batch3-viz-mcp | NDJSON (#1259), explizites enabled:false schlägt Bundle (#1260, nur Config), Stop-Identity (#1271), `viz-report` html.escape, `viz-logger-mcp.mjs` löschen (E-03) | #1259 #1260 #1271 | H (.mcp.json, Hashes) | E-03 entschieden |
| 0.3 | chore/orchestration-checks | P10: O5, O8 (+Strict-Duplikate, deprecaten), O9, O10, hybrid = reserved, `knowledge.schema-language` entfernen/warnen | (neu) #1243-Teil | keiner | E-05 entschieden |
| 0.4 | fix/orchestrator-permission-mode | `permissionMode: plan` → `default` (E-04) + 1 Test; eigener kleiner PR | #1279-Teil (neu) | H, ggf. AC (FM-Zeile) → falls AC: in 2.3 ziehen | E-04 |
| 0.5 | chore/audit-top5-reports | P32 (E-06): pytest-cov temporär, Berichte per PR, Gate G1 Voll-Testlauf erst nach Stufe A + Ja des Nutzers | #1276 #1245 #1159-Teil | keiner | E-06 |
| 0.6 | docs/intent-routing-spec | P25: tiktoken-Messung, Spec, Intent-Taxonomie informativ (E-07) | #1161 #779 | keiner | Spec-Freigabe nach Review (E-07) |
| 0.7 | docs/phase-i-<issue> (je Issue) | P33, Rang 1–3 zuerst (#896, #339, #681) | s. P33 | keiner | Specs/Konzepte einzeln nach Review (E-31) |
| 0.8 | Issue-Hygiene | §6 — **vorgeschlagen, noch nicht ausgeführt**; separater späterer Auftrag nach Beleg-Prüfung (E-08) | s. §6 | — | Beleg-Prüfung |
| 0.9 | feat/git-agent-trailer-contract | **P37 (E-19):** Trailer-Contract als Config-Key, Contract in git.md; Git-Agent-PR zuerst. **Rebaseline-Implikation:** git.md ist Template → eigene AC/G/B-Rebaseline (siehe §3.8) | #1168 #1247 | **AC, G, B** (nicht „ohne Rebaseline“) | Reihenfolge: vor 1.3 nur wenn der Helper-Aufwand tragbar ist, sonst direkt nach 1.3 als erster Anwender des Helpers |

Hinweis zu 0.9: Der PR ist logisch „früh“ (W0/W1), die Rebaseline erfolgt aber sauber erst, wenn der Helper (1.3) steht. Praktische Folge: Branch/Entwurf früh, Merge direkt nach 1.3; dieser Rebaseline-Commit ersetzt den Probelauf, der im Review 1.4 zugedacht war.

Merge-Reihenfolge innerhalb W0 beliebig, außer 0.2 vor 0.3 (beide Hash-Datei → Rebase).

### 3.2 Welle 1 — Determinismus + Rebaseline-Werkzeug (sequentiell)

| PR | Branch | Inhalt | Issues | RB | Gate |
|---|---|---|---|---|---|
| 1.1 | fix/batch3-guard-sync | #1258, #1252, #1142, #1270 (Root-Dir + 30-Tage-Regel), #1249 (nur Test + ein Doku-Satz), #1241, #1266 | #1258 #1252 #1142 #1270 #1249 #1241 #1266 | Hook-Hash (1 Commit) | E-09 |
| 1.2 | fix/batch3-tmpdir-determinism | #1246 Variante B+ (Key temp-root + env-freier Default), #1261 nur WARN | #1246 #1261 | keiner bei B+ | E-02, E-09 |
| 1.3 | feat/rebaseline-helper | #1237: ein Befehl für Hashes/AC-01/Goldens/Ceilings (+#1115) | #1237 #1115 | keiner (Tooling) | Mini-Spec ist zu schreiben; dann Status „APPROVED (User, 2026-11-16) laut E-10“ |
| 1.4 | chore/config-hygiene | Plugins honcho + reqogniloom aus (E-11), tote Konfig, .continue/, `.bak`, `--prune-sync-backups` (.bak nicht prunen), `.tmp` räumen, #1263 MCP-Deny | #1263 #946-Tabelle | nur H (Hash). **Vorbehalt:** ändert sich das mcp-guardrails-Render auch bei ausgeschalteten Plugins, ist doch ein Rules-Golden nötig — in 1.4 prüfen | #946-Tabelle dem Nutzer vorlegen; keine Löschbefehle ohne Freigabe |

### 3.3 Welle 2 — Render-Bündel A (stark verschlankt)

Sequentiell auf einem Stapel, Rebaseline nur als letzter Commit je PR. Entfallen sind DoD-Preset, Knowledge-Engine-Abschaltung und Rules-Kürzung (E-13/E-14/E-15).

| PR | Branch | Inhalt | Issues | RB | Gate |
|---|---|---|---|---|---|
| 2.1 | test/orchestrator-goldens-all-providers | P11: Goldens für 6 fehlende Provider (Gemini nur CLI) + Tool⊆FM-Test | O15 (neu) | neue Goldens (einmalig) | E-26 |
| 2.2 | chore/roster-language-release | **Roster 58 → ~30 (Liste ausstehend, E-12)**, Sprach-PR 1 (language.md-Scope, orchestrator.md:405 {{DOCS_LANGUAGE}}-Fix, speech-Geltung, PR-Body-Sprachzeile), Release-Checklist (P7), auto_commit-Set | #1244 (Roster) (neu Sprache) | **1 Rebaseline** (AC, G, B, H, Allowlist) | E-12 Liste freigegeben; E-16 |
| 2.3 | feat/worker-control-capability | P12 Capability pro Provider (E-17) + Phase D Strom B (#1176 Wartestrategie = PR B, #1172 nur Doku (E-18), #1168/#1247-Prosa verweist auf P37) + 0.4 falls AC-pflichtig | #1176 #1172 (Doku) #1168 #1247 | **1 Rebaseline** (AC, G, B, H) | E-17, E-18; Continue-Subagent WARNING |

Begründung: Roster-Reduktion bleibt der größte always-on-Hebel, DoD/KE/Rules-Hebel entfallen bewusst. Sprach-Fix ist ein paar Zeilen und wird in 2.2 mitgenommen.

### 3.4 Welle 3 — Config-Welle (APPROVED-Kette, große Rebaseline unvermeidbar)

| PR | Branch | Inhalt | Issues | RB | Gate |
|---|---|---|---|---|---|
| 3.0 | feat/phase-g1 | P21 G-PR1 (#800 fail-closed, #1171 xfail, #1175 Doku, #860 Runbook) | #800 #1171 #1175 #860 | Hash-only | Gemini-Gates nur CLI (E-26) |
| 3.1 | feat/phase-e-artifact-locations | P17: #1187 Block 0 → #1198 → #1186 → #1199 → #1200 (+#1197) | #1187 #1198 #1186 #1199 #1200 #1197 | **1 Rebaseline** (AC, G, SA, B, H) | Nutzer öffnet #1188 wieder (E-20); E-C0 Messung akzeptiert |
| 3.2 | feat/phase-f-label-taxonomy | P19 F-PR1: #1203 → #1188 → #1204 | #1188 #1203 #1204 | **1 Rebaseline** | Kinder-Addendum nur individuell (E-22) |
| 3.3 | feat/commit-authority-grant | P16 Strom A #1181 (T1–T16); **#1141 als eigener S-PR danach (E-21)** | #1181 | **1 Rebaseline** (AC, G, Allowlist) | Gate G-A |
| 3.3b | feat/schema-unknown-keys | #1141 Schema-Unknown-Keys, S-PR nach F | #1141 | keiner/klein | Spec-Gate (Task 11) |
| 3.4 | feat/artifact-mode-gating | P18 #1209 | #1209 | 1 Rebaseline (klein, optional) | Spec E-T7 zum Wellenstart (E-22); DRAFT bis dahin |
| 3.5 | feat/phase-f-children | P20 #1202 → #1201 | #1202 #1201 | 1 Rebaseline (klein, optional) | Kinder-Addendum zum Wellenstart (E-22); DRAFT bis dahin |

### 3.5 Welle 4 — Render-Bündel B: Routing + Hooks

| PR | Branch | Inhalt | Issues | RB | Gate |
|---|---|---|---|---|---|
| 4.1 | feat/intent-routing-model | P26 (E-23): kompaktes Zeilenformat als Default, name_index reduziert, Direct-Dispatch generiert, Lazy-Detaildatei; Minor-Bump + CHANGELOG; **kein globales Compact-Profil**; + #1243 Rename | #1161 Pkt 2 #1243 | **1 Rebaseline** (AC, 4 Golden-Sets, B, H) | Spec 0.6 APPROVED |
| 4.2 | feat/hook-single-parse-and-sentinel-role | P15: #1169 Bench → Single-Parse (+#1238) → #1210 (+#1250) → #1217 nur nach Task 1a | #1169 #1238 #1210 #1250 #1217 | Hook-Hash (1 Commit) | #1169, #1210 APPROVED (E-24); #1217 bleibt DRAFT bis ask-API belegt |
| 4.2b | feat/git-agent-merge-permission | #1172 Permission-Regel, nur bei positiver Machbarkeit (E-18) | #1172 | Hook-Hash | Spec bleibt DRAFT bis Machbarkeit |
| 4.3 | feat/phase-h1 | P23 H1 | s. P23 | H (Backups) | Spec #969 APPROVED; übrige Gates DRAFT |

4.2 läuft parallel zu 4.1 (dateidisjunkt).

### 3.6 Welle 5 — Provider/Eval/Sprache-Schema

| PR | Branch | Inhalt | Issues | RB | Gate |
|---|---|---|---|---|---|
| 5.1 | feat/phase-g2 | P22 + Rollout PR C (Gemini CLI, kein Antigravity-Zweig) | #814 #800 #1160 #1171 #854 | Gemini-Golden, SA (1 Commit) | E-26; E-31 Specs einzeln; #860 extern; E-27: keine Gemini-Proben bis #860 gelöst |
| 5.2 | feat/language-matrix | P9 (E-28): Eingabe- UND Ausgabesprache dynamisch (Schema-Keys), Framework-Default en für Prompt-Sprache, Hook-Warnung `gh pr create` nein/optional konfigurierbar | (neu) #1204 | Scenario-Configs; AC nur bei Anzeige-Änderung | Spec neu APPROVED |
| 5.3 | feat/phase-h2 | P24: #969 Baseline erst nach Kostenschätzung + Ja (E-27), #1161 Pkt 5, #779/#780, #1167, H-17/23/24 | s. P24 | **1 Rebaseline** | Kosten-Gate |
| 5.4 | feat/intent-routing-admin-ui | P27: API, Editor, Eval-Katalog, Eval-Lauf (< 1 USD, E-27) | — | H (Detaildatei) | 4.1 gemergt |

### 3.7 Welle 6 — Verbesserungsschleife + Hook-Kernel

| PR | Branch | Inhalt | Issues | RB | Gate |
|---|---|---|---|---|---|
| 6.0 | chore/agent-loop-batch-0 | Mess-CLI, Lint, Ratschen-Test, Sektionsschema; Ceiling-Test | #1244 #885-Ersatz | keiner | Ziele hart (E-29) |
| 6.1 | chore/agent-loop-batch-1 | H3 Block-Kürzung, H5 Descriptions-Lint (H1 bereits in 4.1); **keine Compact-Aktivierung, keine Rules-Kürzung** | — | **1 Rebaseline** | Prompt-Sprache Englisch, Issue-Nummern raus (E-29) |
| 6.2–6.10 | chore/agent-loop-batch-<n> | Rollen-Rewrite je Batch; Umfang abhängig von der Rollenliste (E-12); Knowledge-Rollen bleiben aktiv (E-14 gestrichen) | #1014 #778 | je 1 Rebaseline (~9) | Claude-Evals nein (E-29) |
| 6.11 | chore/agent-loop-final | Ratsche hart, Doku | — | B | — |
| 6.x ∥ | feat/hook-kernel-<step> | #1257 Kernel (5 Schritte) + #1253–#1255; Unter-Issues unter #1257 (E-30) | #1257-Kette | Hook-Hash je Schritt | Konzept nach 4.2 freigegeben (E-30) |

### 3.8 Rebaseline-Zählung (neu berechnet)

Review-Stand: Kopfzeile nannte „6 Rebaseline-Commits“ (W2: 2, W4: 2, W6: 2), die Schlusszeile zählte „8“ (1.4, 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 5.3). Das war eine interne Inkonsistenz; richtig war die 8-Zählung (die Kopfzeilen-„6“ war ein Rest einer früheren Wellen-Struktur). Wir legen die Zählung hier fest und verwerfen die „6“.

Neu nach den Entscheidungen:

- 1.4 verliert die Rules-Golden (E-15, keine Rules-Änderung); Plugins aus bleibt Hash-only → **keine Golden-Rebaseline mehr**. Vorbehalt: ändert sich das mcp-guardrails-Render auch bei ausgeschalteten Plugins, ist doch ein Rules-Golden nötig; in 1.4 verifizieren.
- 2.2 schrumpft (Roster, Sprach-PR 1, Release-Checklist; DoD/KE/Rules entfallen), bleibt aber **eine** Rebaseline.
- 2.3, 3.1, 3.2, 3.3, 4.1, 5.3 unverändert.
- **Pflicht: 7** = 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 5.3.
- Optional: 3.4, 3.5, 5.1, 5.2 (je klein; 5.2 nur bei Anzeige-Änderung).
- Loop: ~10 (6.1 + 6.2–6.10).
- Hook-Hash-only-Commits (1.1, 4.2, 4.2b, 6.x, 1.4) zählen nicht.
- **Zusatz P37/0.9 (E-19):** git.md ist Template, der Git-Agent-PR erzeugt eine eigene AC/G/B-Rebaseline. Diese ist in den 7 **nicht** enthalten, wird aber als 8. Pflicht-Commit gezählt, sofern 0.9 separat vor 2.2 gemergt wird. Alternative: 0.9 hinter 2.2 stapeln und die Rebaseline in 2.2 mitnehmen — dann bleibt die Pflichtzahl 7. Empfehlung: Variante „mitnehmen“ nur, wenn 0.9 klein bleibt; sonst Pflicht = 8 mit eigener Runde. Entscheidung bei Start von 0.9 (offen).
- Ohne Bündelung wären es ≥ 14.

Annahme: Helper (1.3) steht vor W2; jeder Zwischen-Merge auf main mit Render-Diff erhöht die Zahl.

### 3.9 Welle 7 — Phase-I-Umsetzungen, Rest-Backlog

- Je Issue eigener Plan + PR nach APPROVED-Concept aus 0.7 (#896, #339 nach Re-Approval, #832 → #783/#958, #1004, #1113, #957, #820 + #877).
- Rest-Backlog ohne Plan: #1268 → #1273, #1239 + #1240, #1242/#1269, #1262 + #1274, #1267/#1272, #1275, #1278 nach Welle 6.

### 3.10 Gesamtreihenfolge

```
W0: 0.1 | 0.2 → 0.3 | 0.4 | 0.5 ∥ 0.6 ∥ 0.7 ∥ 0.8 | 0.9 (Git-Agent, Merge nach 1.3)
W1: 1.1 → 1.2 → 1.3 → 1.4
W2: 2.1 → 2.2 → 2.3
W3: 3.0 → 3.1 → 3.2 → 3.3 → 3.3b → [3.4] → [3.5]
W4: 4.1 ∥ 4.2 → [4.2b] → 4.3
W5: 5.1 ∥ 5.2 → 5.3 → 5.4
W6: 6.0 → 6.1 → 6.2…6.10 → 6.11   ∥   6.x Hook-Kernel
W7: J1…Jn, Rest-Backlog
```

## 4. Entscheidungsprotokoll 2026-11-15

Empf. = Empfehlung des Reviews. „Wie Empf.“ = Nutzer folgt der Empfehlung; „Abweichung“ ist hervorgehoben.

| # | Gegenstand | Entscheidung | Empf. / Abweichung |
|---|---|---|---|
| E-01 | docs-Index-Branch pushen | Nutzer bot Push per `!`-Befehl an; unser Push wird vom git-Agenten erneut versucht | wie Empf. (ja) |
| E-02 | #1246 Variante | Variante B+ (Key temp-root + env-freier Default) | wie Empf. |
| E-03 | viz-logger-mcp.mjs / #1260 | mjs löschen; #1260 nur über Config (explizites enabled:false schlägt Plattform-Bundle) | wie Empf. |
| E-04 | permissionMode plan → default | jetzt, eigener kleiner PR; falls AC-relevant → in 2.3 | wie Empf. |
| E-05 | hybrid / strict / enabled | hybrid = reserved; orchestrator.strict/enabled deprecaten | wie Empf. |
| E-06 | Audit-Top5 | jetzt (W0), pytest-cov temporär, Berichte per PR, G1 Voll-Testlauf erst nach Stufe A + Ja | wie Empf. |
| E-07 | Intent-Taxonomie / Routing-Spec | Taxonomie informativ; Routing-Spec nach Review freigegeben | wie Empf. |
| E-08 | Issue-Hygiene §6 | Ausführung NACH Beleg-Prüfung (schließen nur mit Beleg-Kommentar; zusammenlegen/parken per Kommentar); separater späterer Auftrag | präzisiert |
| E-09 | #1249/#1261/#1270/.bak | #1249 Tier-Fold → #1257 (nur Test + ein Doku-Satz); #1261 nur WARN; #1270 30-Tage-Regel ja; .bak nicht prunen | wie Empf. |
| E-10 | #1237 Mini-Spec | Freigabe APPROVED für beschriebenen Umfang (Rebaseline-Helper + #1115) erteilt; Spec selbst noch zu SCHREIBEN → Vermerk „Spec schreiben, dann Status APPROVED (User, 2026-11-16) laut E-10“ | wie Empf., Spec noch ausstehend |
| E-11 | Plugins / #946 | honcho + reqogniloom in diesem Repo aus; #946-Tabelle dem Nutzer vorlegen (keine Löschbefehle ohne Freigabe) | wie Empf. |
| E-12 | Rollen 58 → ~30 | Prinzip ja; konkrete Rollenliste zuerst dem Nutzer zur Freigabe (separater Auftrag); im Plan: „Liste ausstehend“ | wie Empf. im Prinzip |
| E-13 | DoD-Preset | **Nein: bleibt rapid-prototyping** | **Abweichung** (Review: ja, Wechsel) |
| E-14 | Knowledge Engine | **Knowledge Engine bleibt AN** (docs/INDEX.md existiert zusätzlich als Fallback-Index, ändert index.mode: knowledge-engine nicht) | **Abweichung** (Review: aus) |
| E-15 | Rules kürzen / max_depth | **Nein: Rules-Kürzung entfällt, max_depth bleibt 10, use-lazy-rules bleibt** (kein Rules-Golden-Rebaseline 1.4, kein Rules-Anteil in 2.2) | **Abweichung** (Review: ja) |
| E-16 | Sprach-Matrix | wie empfohlen: Tracker/Issues/PR en, Subagent-Berichte de, A2A-Briefe en, Specs/Pläne de, Vorrang Kontrakt > Sprache > Stil; Sprach-PR 1 inkl. {{DOCS_LANGUAGE}}-Fix orchestrator.md:405 | wie Empf. |
| E-17 | Worker-Control-Capability | Capability pro Provider (ersetzt Phase-D-Task 3/#1176); Continue `subagent` → WARNING; primary Claude/Kimi als prose-only gemeldet | wie Empf. |
| E-18 | #1172 | Doku in W2; Permission-Regel nur bei positiver Machbarkeit (W4) | wie Empf. |
| E-19 | Trailer-Contract | **KONFIGURIERBAR (Config-Key)**, Contract in git.md; **Git-Agent-PR kommt ZUERST** (früh in W0/W1) statt fest im Prompt-Trailer | **Abweichung** (Review: fester Prompt-Trailer) |
| E-20 | #1188 / E-C0 | #1188 wieder öffnen (Nutzer-Aktion zum Phase-E-Start); E-C0-Messung akzeptiert | wie Empf. |
| E-21 | #1141 | eigener S-PR nach F | wie Empf. |
| E-22 | Specs Kinder-Addendum F / #1209 / #1141 | einzeln zum Wellenstart nach Review freigeben (bis dahin DRAFT) | wie Empf. |
| E-23 | Routing PR 2 | wie Empf.: kompaktes Zeilenformat Default, name_index reduzieren, Direct-Dispatch generieren, Lazy-Detaildatei, Minor-Bump + CHANGELOG; NICHT das globale Compact-Profil | wie Empf. |
| E-24 | Phase-D-Specs | **#1210 (guard-role-attribution) und #1169 (hook-single-parse) JETZT APPROVED**; #1217 (guard-destructive-ask) erst nach Task 1a (ask-API belegt); #1172 (git-agent-merge-permission) nach Machbarkeit — beide bleiben DRAFT | **Abweichung** (Review: Freigabe zu W4; Nutzer zieht sie vor) |
| E-25 | #1238 | in den #1169-PR | wie Empf. |
| E-26 | Gemini-Plattform | **Gemini = nur Gemini CLI** (kein Antigravity); Gemini-Goldens/Gates (O2, #854, #1171, 5.1) ohne Antigravity-Zweig | wie Empf. („nur Gemini CLI“) |
| E-27 | Kostenpflichtige Läufe | Routing-Eval ja (< 1 USD); #969-Baseline erst nach Kostenschätzung + erneutem Ja; Gemini-Proben nein bis #860 gelöst | wie Empf. |
| E-28 | Sprach-PR 2 | **Eingabe- UND Ausgabesprache beide dynamisch einstellbar (Schema-Keys)**; Framework-Default en für Prompt-Sprache; Hook-Warnung `gh pr create` nein bzw. optional konfigurierbar | **Abweichung/Erweiterung** (Review: nur Default en) |
| E-29 | Loop | Prompt-Sprache Englisch; Issue-Nummern raus; Ziele/Ratsche hart; Claude-Evals nein; globales Compact NICHT aktiviert | wie Empf. |
| E-30 | Hook-Kernel #1257 | Konzept freigegeben nach 4.2; Unter-Issues unter #1257 zusammengelegt | wie Empf. |
| E-31 | Phase G/I | Specs/Konzepte einzeln nach Review, Reihenfolge P33; #339 Re-Approval bei Phase-I-Start | wie Empf. |

Zusammenfassung der Abweichungen: E-13, E-14, E-15 (drei Einsparungen entfallen), E-19 (konfigurierbar + vorgezogen), E-24 (zwei Specs sofort), E-28 (beide Sprachen dynamisch).

## 5. Noch offene Folgeaufträge

1. Rollenliste (58 → ~30) dem Nutzer zur Freigabe vorlegen (E-12); Plan-Stand: „Liste ausstehend“.
2. #946-Entscheidungstabelle dem Nutzer vorlegen (E-11); keine Löschbefehle ohne Freigabe.
3. Issue-Hygiene §6 ausführen (E-08), erst nach Beleg-Prüfung; separater Auftrag.
4. 16 neue Issues aus dem Review (Titelliste unten) anlegen — Anlage weiterhin OHNE Nutzerfreigabe, wartet auf diese.
5. #1237-Mini-Spec schreiben; danach Status APPROVED (User, 2026-11-16) laut E-10.
6. Spec-Freigaben zum Wellenstart (E-22: Kinder-Addendum F, #1209, #1141; E-31: Phase G/I-Specs und Konzepte).
7. #1217 und #1172 bleiben DRAFT (#1217 nach Task 1a, #1172 nach Machbarkeit).
8. Nutzer-Aktion: #1188 wieder öffnen bei Phase-E-Start (E-20).
9. Offen aus §3.8: Git-Agent-PR 0.9 gesondert rebaselinen oder in 2.2 mitnehmen (Entscheidung bei Start von 0.9).
10. Routing-Spec nach Review freigeben (E-07); Rollenliste-Vorlage vor 2.2.

Titelliste der geplanten neuen Issues (Review §5, nichts angelegt):

- fix(role-defaults): orchestrator permissionMode plan blocks checkpoint writes on Claude
- fix(topology): render effective position and warn when primary degrades to subagent
- chore(schema): mark orchestrator.topology hybrid as reserved
- fix(schema): accept orchestrator.handoff.t-size-limit without warning and drop duplicate output
- fix(viz): html.escape message text in viz-report.py
- chore(config): remove dead knowledge.schema-language key
- docs(rules): add PR-body language rule (tracker language)
- fix(orchestrator): gate chat push on a messaging-tool capability, not hooks (O4)
- fix(gemini): orchestrator frontmatter lacks dispatch tool; reconcile provider-tools vs native_agent_tools (O2)
- feat(capabilities): worker_control_tools per provider replaces primary-role-tools (O1)
- test: orchestrator render goldens + tool-mention⊆frontmatter check for all providers (O15)
- chore(config): remove dead orchestration keys and strict/fallback duplicate variables (O8)
- chore(consistency): depth coherence check (max_depth / required_depth / subagent-depth) (O10)
- fix(opencode): v2 default_agent merge for primary topology (nur falls nicht offen)
- chore(config): config hygiene agent-meta (plugins off, dead keys, .continue, backups)
- feat(git): configurable trailer contract (neu aus E-19; #1237 existiert bereits, kein Duplikat)

## 6. Issue-Hygiene (vorgeschlagen, noch nicht ausgeführt)

Ausführung ist ein separater späterer Auftrag nach Beleg-Prüfung (E-08): Schließen nur mit Beleg-Kommentar; Zusammenlegen/Parken per Kommentar. Nichts davon wurde geändert.

### Schließen mit Beleg
- #1139 — AK1/AK2 erfüllt (#1224, pytest.skip); AK3 nicht beweisbar.
- #1173 — Diff-Sperre + `__allow_lossy__` ist Entscheidung 22.
- #1208 — Blindfleck nicht reproduzierbar, Absicherungstest vorhanden; Rest Phase H.
- #1189 — via #1225 umgesetzt; Abschlusskommentar prüfen.
- #1175 — Frage beantworten (Evidenz im Opencode-Allow-list-Kommentar), dann schließen.
- #885 — Baseline beta.1 veraltet; ersetzt durch Loop-Rubrik.
- #548 — RFC 2026-08, in Roadmap aufgelöst; sonst in ≤ 3 Issues splitten.
- #1222 — Design ohne Bedarf: parken/schließen.

### Zusammenlegen (per Kommentar)
- #1115 → #1237; #1238 → #1169 (E-25); #1168 + #1247 (Trailer-Contract, E-19); #1210 + #1250; #1014 + #778 → Loop-Rubrik; #1253 + #1254 + #1255 → „provider-agnostic sync dispatch“; #1239 + #1240; #1262 + #1274; #1264 + #1265 → #1261; #1245 + #1159 → Audit-Top5 Task 4; #1248 #1251 #1252-Rest #1256 #1249-Rest → unter Epic #1257 (E-30); #681 → #1113/#1176; #820 + #877 → gemeinsames Concept; #1244 zweiteilen (Roster-Teil nach 2.2, Ceiling-Test → #1237/6.0).

### Parken (per Kommentar)
- #329 #330 #339 (SE hier aus; #339 Re-Approval bei Phase-I-Start, E-31), #679 #676 #1106 (Plattform-Presets), #860 (extern), #1211 (Pilot-Gate), #1276 Punkt Windows streichen.

## 7. Risiken / Annahmen / nicht geprüft

- Lokaler Worktree liegt hinter origin/main; Pläne/Audits aus `.tmp/` gelesen, Spec-Status per Verweis aus dem Review übernommen, nicht diffgeprüft.
- Phasenpläne D–I nur in Header/Reihenfolge/PR-Schnitt/Entscheidungen gelesen; Parallelitätsaussagen (4.1 ∥ 4.2, 6.x ∥ Loop) beruhen auf den File-Structure-Angaben der Pläne.
- Rebaseline-Zählung (7 Pflicht, 8 falls 0.9 separat) setzt voraus, dass der Helper (1.3) vor W2 fertig ist und PRs die Rebaseline als letzten Commit halten; jeder Zwischen-Merge auf main mit Render-Diff erhöht die Zahl.
- Der Git-Agent-PR 0.9 liegt vor dem Helper (zeitlich W0/W1), rebaselined aber erst sinnvoll nach 1.3 — Zielkonflikt zwischen „zuerst“ (E-19) und Helper-Nutzung; Auflösung in §3.1/§3.8.
- 1.4: Annahme „Plugins aus = Hash-only“ ungeprüft (Vorbehalt Rules-Golden).
- Token-Hebel-Zahlen stammen aus Settings-/Loop-Plan (Bytes/4); Hebel aus DoD/KE/Rules entfallen — der erwartete Gesamtgewinn von W2 sinkt; erst Routing-PR 1 Task 0 (tiktoken) kalibriert.
- 0.4 (permissionMode) kann den Orchestrator-FM-Hash ändern → dann AC-pflichtig (→ 2.3).
- Worker-Control-Capability (2.3) ersetzt D-Task 3 nur, solange E-17 gilt.
- Gemini-Annahme „nur CLI“ (E-26): Antigravity-Goldens entfallen, Rebaseline-Kosten sinken um einen Provider.
- Knowledge Engine bleibt an (E-14): Knowledge-Rollen bleiben im Loop-Umfang; Loop-Umfang sinkt nur durch die Roster-Reduktion (Liste ausstehend).
- Keine Tests, Syncs oder Renders ausgeführt; `gh` nur read-only.
