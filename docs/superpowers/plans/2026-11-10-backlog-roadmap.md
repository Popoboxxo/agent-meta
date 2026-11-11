# Backlog-Roadmap 2026-11-10

> Status: APPROVED (User, 2026-11-11)
> Datum: 2026-11-10 | Entscheidungen eingearbeitet: 2026-11-10/11 (Entscheidungen 1-57, Stand 2026-11-12) | Basis Phasenpläne: origin/main `9aa0e0c0` (inkl. PR #1218; Rebase erledigt) | Sweep-Basis: `a41745ed` | Zeilenanker: bei Ausführung neu messen | Branch: `docs/backlog-roadmap`

**Goal:** Die 90 Issues dieses Plans (89 aus dem Sweep-Universum plus #1187, Entscheidung 49; #1190 ist inzwischen automatisch geschlossen, Beleg in Phase A) und die offenen PRs #1145, #1148 (#1218 gemergt) in Phasen ordnen, die je ein Branch und ein PR sind (Ausnahmen: Abschnitt 4, Entscheidungen 18, 36, 52, 53).
**Architecture:** Reiner Ordnungs- und Entscheidungsplan. Jede Phase bekommt später einen eigenen Phasenplan im Plan-Template (`Files:`/`Interfaces:`, TDD-Steps).
**Tech Stack:** Python 3.9+ (stdlib, PyYAML-Ausnahme), pytest, GitHub Actions CI.
**Spec:** Roadmap, keine Spec. Die Phasenpläne verweisen jeweils auf ihre eigene freigegebene Spec. M/L/XL-Arbeit (Phase I, #1210, #1106 usw.) braucht vor Planung `Status: APPROVED`.

`pipeline_stages`-Frontmatter entfällt: Dies ist kein Plan für eine `plan-driven`-Pipeline. Die Phasenpläne tragen es.

## Zweck und Nicht-Ziele

- Zweck: Überblick, Reihenfolge, Abhängigkeiten und die vom User getroffenen Entscheidungen (Abschnitt 7) für die Freigabe festhalten.
- Nicht-Ziel: Nichts wird umgesetzt, kommentiert, geschlossen, gelabelt, gelöscht oder gemergt, bevor der User diese Roadmap freigibt.
- Nicht-Ziel: Kein Commit, Push, PR, keine Issue-Änderung durch dieses Dokument.

---

## 1. Sweep-Ergebnis

Quelle: 6 Subagent-Sweeps gegen `a41745ed`. Spalte "Prüfstand": **Main Chat geprüft** nur für #1116, #1139, #1189, #858, #1170. Alle anderen Zeilen: **Subagent, ungeprüft**.

### Zähler

| Verdikt | Auftrag | Neu gezählt aus Tabelle |
|---|---|---|
| ECHT_OFFEN | 57 | 57 |
| TEILWEISE | 25 | 24 |
| SCHON_GEBAUT | 6 | 7 |
| DOPPELT | 1 | 1 |
| Summe | 89 | 89 |

Die Sweep-Zähler gelten für die 89 Sweep-Issues. #1187 (Entscheidung 49) ist nicht Teil des Sweeps und wird hier nicht verbucht; Phasensumme dadurch 90.

Abweichung zu den Auftragszählern (Sweep-Stand `a41745ed`): #1190 von TEILWEISE nach SCHON_GEBAUT (PR #1218 gemergt 9aa0e0c0, Issue automatisch geschlossen 2026-11-11T06:41:32Z; Entscheidung 38f). #1190 bleibt Eintrag der 89 und wird in Phase A per Beleg-Kommentar abgeschlossen.

### Issues

| Nr | Verdikt | Evidenz | Prüfstand |
|---|---|---|---|
| 317 | ECHT_OFFEN | viz-dashboard iframe Live-Test, S-M | Subagent, ungeprüft |
| 329 | TEILWEISE | SE-Baseline/CR-Layer, Design | Subagent, ungeprüft |
| 330 | TEILWEISE | SE-Metriken, Design | Subagent, ungeprüft |
| 339 | TEILWEISE | Concept archiviert: `docs/concepts/archive/2026-06-se-cascade-optimization-339.md` (alter Pfad existiert auf 9aa0e0c0 nicht; Plan I); Spec `docs/specs/2026-10-07-339-se-housekeeper-standardization.md` | Subagent, ungeprüft |
| 547 | SCHON_GEBAUT | Cross-Harness Dev-Isolation; Evidenz nur Subagent | Subagent, ungeprüft |
| 548 | ECHT_OFFEN | RFC | Subagent, ungeprüft |
| 676 | ECHT_OFFEN | HACS Best Practice; externe HA-Aussagen unverifiziert | Subagent, ungeprüft |
| 679 | TEILWEISE | web-best-practices Preset | Subagent, ungeprüft |
| 681 | TEILWEISE | Liveness-Guidance | Subagent, ungeprüft |
| 778 | TEILWEISE | Literatur-Querschnittsbefunde für generische Rollen (Design-Issue) | Subagent, ungeprüft |
| 779 | TEILWEISE | Intent-Routing-Audit; Sprache in #780 | Subagent, ungeprüft |
| 780 | TEILWEISE | RFC | Subagent, ungeprüft |
| 783 | ECHT_OFFEN | Merge-Policy | Subagent, ungeprüft |
| 800 | ECHT_OFFEN | Hermes-Provider; Messwerte unverifiziert | Subagent, ungeprüft |
| 814 | ECHT_OFFEN | stdio-MCP cwd | Subagent, ungeprüft |
| 820 | ECHT_OFFEN | Domain-Unterordner | Subagent, ungeprüft |
| 832 | ECHT_OFFEN | Config-Overlay `.local` | Subagent, ungeprüft |
| 854 | ECHT_OFFEN | blockiert durch #860 (`config/ai-providers.yaml:180-182`) | Subagent, ungeprüft |
| 857 | SCHON_GEBAUT | #904 `f55601ba`, #994 `89cc6381`, `ai-providers.yaml:150-154` | Subagent, ungeprüft |
| 858 | SCHON_GEBAUT | #994, `ai-providers.yaml:474`, `provider-capabilities.yaml:528` | Main Chat geprüft |
| 860 | ECHT_OFFEN | extern blockiert (agy SIGILL pclmul; Owner-Kommentare 2026-10-27/29) | Subagent, ungeprüft |
| 877 | ECHT_OFFEN | RFC XL; kein Duplikat von #820; `bugfix-wave-plan.md:449` setzt es voraus | Subagent, ungeprüft |
| 885 | TEILWEISE | Epic: F-01,F-04,F-07,F-08 behoben; F-02,F-03,F-05,F-06 offen; F-09..F-16 unverifiziert; Kinder 933/934/935 CLOSED, 932/936 nicht geprüft | Subagent, ungeprüft |
| 896 | ECHT_OFFEN | M; Plan `docs/plans/2026-10-07-admin-ui-network-and-manager-plan.md` DRAFT; #897 ist CLOSED (gh 2026-11-11), Abhängigkeit aufgelöst | Subagent, ungeprüft |
| 898 | TEILWEISE | S; Punkt 2 gebaut `admin-server.py:4730`; Punkt 1 Checkboxen offen `admin-ui.html:7699-7705`; Punkt 3 `pricing-overlay.yaml:7,10` alte Modelle | Subagent, ungeprüft |
| 946 | ECHT_OFFEN | Entscheidungsissue; 18 Zweifelsbranches auf origin, 9 Stash-Einträge statt 7, `.tmp/cleanup-archive` weg, `docs/838-spec-revision` nur noch im Stash, lokal z.B. `fix/sync-check-tracked-only 35f591e6` ohne Remote | Subagent, ungeprüft |
| 957 | ECHT_OFFEN | L; Spec `docs/specs/2026-10-11-pr-templates-spec.md` DRAFT | Subagent, ungeprüft |
| 958 | ECHT_OFFEN | L; `config.py:2339` `PROJECT_SPECIFIC_AGENTS=""`; Abhängigkeit #965 closed | Subagent, ungeprüft |
| 960 | ECHT_OFFEN | L; nichts gebaut, Spec zuerst | Subagent, ungeprüft |
| 969 | TEILWEISE | S; #986 `082aa9b1` `eval_gate.py` gebaut; Baseline-Run braucht User-Freigabe; McNemar zurückgestellt | Subagent, ungeprüft |
| 977 | TEILWEISE | Tracker; 963-968, 970-976 closed; nur 969 offen; Phasen 2/3 ohne Issues | Subagent, ungeprüft |
| 1000 | ECHT_OFFEN | M; `progress_paths.py:34-35` | Subagent, ungeprüft |
| 1004 | ECHT_OFFEN | L (Plan I, Entscheidung 9 ungeteilt; Sweep: M); planner.md v1.6.1 ohne `parallel_with`/`conflicts_with`; `orchestrator.md:258-277` (BARRIER protocol, 9aa0e0c0) | Subagent, ungeprüft |
| 1007 | SCHON_GEBAUT | PRs #1012, #1016, #1017, #1018, #1019; die 7 "zu bauen"-Punkte nicht einzeln verglichen | Subagent, ungeprüft |
| 1014 | TEILWEISE | XL; PR #1013 gemergt; P1-P8 querschnittlich nicht | Subagent, ungeprüft |
| 1085 | ECHT_OFFEN | a `hooks.py:649`; b `--strict` nur für `--doctor` `sync.py:123-128`; c `gitignore.py:12,256,467` | Subagent, ungeprüft |
| 1086 | ECHT_OFFEN | Sammelticket, 8 von 9 offen (a..i); 1086e unverifiziert; `context.py` jetzt 3495 Zeilen | Subagent, ungeprüft |
| 1106 | TEILWEISE | L; Überlapp #1102 closed `23893133`; offen A, D, E, F | Subagent, ungeprüft |
| 1113 | ECHT_OFFEN | L; kein `ask_user_tool`-Vertrag; `orchestrator.md:304` | Subagent, ungeprüft |
| 1115 | ECHT_OFFEN | S-M | Subagent, ungeprüft |
| 1116 | SCHON_GEBAUT | `fa37d7d0`; `tests/test_orchestrator_guard_hook.py:63` | Main Chat geprüft |
| 1139 | ECHT_OFFEN | S; `tests/test_cli_smoke_multi_provider.py:53` `timeout=300`; `tests/timeouts.py` `SLOW_TIMEOUT` 900 ungenutzt | Main Chat geprüft |
| 1141 | ECHT_OFFEN | M; `additionalProperties:true` | Subagent, ungeprüft |
| 1142 | ECHT_OFFEN | 1: rc=0 `sync_pipeline.py:1909`; 2: Allowlist geschrieben `:1894-1921`; 3 unverifiziert | Subagent, ungeprüft |
| 1150 | DOPPELT | Duplikat von #1186 | Subagent, ungeprüft |
| 1151 | SCHON_GEBAUT | `c1e810c6`, `283fcd3c`, PR #1153; F6-10 nur laut Changelog | Subagent, ungeprüft |
| 1155 | TEILWEISE | F2,F3,F4,F6..F9 gebaut; F5 Plain-Sync exit 0 laut Policy; F10 `topology-probe.py:232` offen | Subagent, ungeprüft |
| 1158 | TEILWEISE | K-02..K-06,K-10 gebaut (PR #1163); K-01,K-13 unverifiziert | Subagent, ungeprüft |
| 1159 | TEILWEISE | K-08,K-09,K-11,K-14,K-15,F-OC3 gebaut (PR #1164); K-12,K-16,K-17,F-PA1 offen; F-PA2 teilweise; F-OC2 unverifiziert | Subagent, ungeprüft |
| 1160 | TEILWEISE | Schritt 1 PR #1165; 2/3 blockiert | Subagent, ungeprüft |
| 1161 | TEILWEISE | Punkte 1,3 gebaut; 2,4,5 offen: `context.py:204`, `hook_common.sh:63` | Subagent, ungeprüft |
| 1167 | TEILWEISE | REQ-ID-Format in Templates/Presets und Validator vereinheitlichen | Subagent, ungeprüft |
| 1168 | ECHT_OFFEN | git-Agent schreibt Harness-`Co-Authored-By` statt des vorgeschriebenen Trailers | Subagent, ungeprüft |
| 1169 | ECHT_OFFEN | Hook-Latenz: 9-11 Python-Spawns pro Bash-Call (`hook_json_get`, `hook_common.sh`) | Subagent, ungeprüft |
| 1170 | ECHT_OFFEN | `provider_transform.py:885`, kein Aufrufer; Issue nennt 854 | Main Chat geprüft |
| 1171 | ECHT_OFFEN | Gemini/Antigravity-Benennung in `provider-tools.yaml` (`terminal_tool.Gemini` `code_execution`, `config/provider-tools.yaml:142`) | Subagent, ungeprüft |
| 1172 | ECHT_OFFEN | Merges via orchestrator->git vom Auto-Mode-Classifier blockiert; Merge-Muster dokumentieren | Subagent, ungeprüft |
| 1173 | ECHT_OFFEN | S; Admin-UI Tier-Preset-Speichern verliert YAML-Kommentare in `config/tier-presets.yaml` (plain `yaml.dump`); laut Issue `scripts/admin-server.py:5089`, nicht von Main Chat geprüft | Subagent, ungeprüft |
| 1174 | ECHT_OFFEN | Beleg `agents/agent-meta-developer.md:165` existiert auf main nicht | Subagent, ungeprüft |
| 1175 | TEILWEISE | Frage; nicht verifizierbar, Opencode-Quelle nicht gelesen | Subagent, ungeprüft |
| 1176 | TEILWEISE | Orchestrator beendet Turn beim Warten auf async Sub-Agents, Harness erzwingt vorzeitiges SubagentHandback | Subagent, ungeprüft |
| 1180 | ECHT_OFFEN | auch `rules/1-generic/a2a-delegation-gates.md:16` | Subagent, ungeprüft |
| 1181 | ECHT_OFFEN | Spec+Plan APPROVED, kein Code | Subagent, ungeprüft |
| 1182 | ECHT_OFFEN | P1 | Subagent, ungeprüft |
| 1183 | ECHT_OFFEN | P1 | Subagent, ungeprüft |
| 1186 | TEILWEISE | Spec `docs/specs/2026-11-09-artifact-locations-matrix-spec.md` + Plan APPROVED, PR #1212, kein Code | Subagent, ungeprüft |
| 1188 | TEILWEISE | Spec `docs/specs/2026-11-09-issue-label-taxonomy-spec.md` + Plan APPROVED, kein Code; `sync.py:456` nur `--label` | Subagent, ungeprüft |
| 1189 | ECHT_OFFEN | M; `admin-server.py:311`; Plan `docs/plans/2026-11-09-1189-tmp-sink-pin-plan.md` APPROVED via PR #1191, Fix fehlt | Main Chat geprüft |
| 1190 | SCHON_GEBAUT | PR #1218 gemergt (9aa0e0c0, 2026-11-11T06:41:30Z), Issue automatisch geschlossen 2026-11-11T06:41:32Z, Beleg-Kommentar nachreichen; ADR 0002, `topology.py` | gh read-only (Entscheidung 38f), Beleg-Kommentar fehlt |
| 1194 | ECHT_OFFEN | S; `context.py` `apply_settings_surface_shape` (9aa0e0c0 `:1815`, Sweep-Anker `:1710` veraltet), `opencode_v2_config.py:513` | Subagent, ungeprüft |
| 1195 | ECHT_OFFEN | M; `sync_pipeline.py:946` | Subagent, ungeprüft |
| 1197 | ECHT_OFFEN | S | Subagent, ungeprüft |
| 1198 | ECHT_OFFEN | S, P1; 18 Stellen in 12 SE-Templates | Subagent, ungeprüft |
| 1199 | ECHT_OFFEN | S; `admin-server.py:234` | Subagent, ungeprüft |
| 1200 | ECHT_OFFEN | S | Subagent, ungeprüft |
| 1201 | ECHT_OFFEN | M; `conventions-presets.yaml:56,93,125` | Subagent, ungeprüft |
| 1202 | ECHT_OFFEN | M | Subagent, ungeprüft |
| 1203 | ECHT_OFFEN | S, prospektiv (`--labels` existiert noch nicht); Issue: Entscheidung "vor oder mit" der Einführung von `--labels` | Subagent, ungeprüft |
| 1204 | ECHT_OFFEN | S | Subagent, ungeprüft |
| 1205 | ECHT_OFFEN | S; `auto_commit.py:164,222` | Subagent, ungeprüft |
| 1206 | ECHT_OFFEN | S; `admin-ui.html:7753-7761` | Subagent, ungeprüft |
| 1207 | ECHT_OFFEN | S; Doku, Zeilenanker veraltet | Subagent, ungeprüft |
| 1208 | ECHT_OFFEN | M; `AGENTS.md:140` vs `context.py:2147`; `--check`-Blindstelle nicht reproduziert | Subagent, ungeprüft |
| 1209 | ECHT_OFFEN | M; nach #1186 | Subagent, ungeprüft |
| 1210 | ECHT_OFFEN | L; `orchestrator-guard-impl.sh:262-269,418ff`; Design/Security | Subagent, ungeprüft |
| 1211 | ECHT_OFFEN | verfrüht; blockiert durch #1188 | Subagent, ungeprüft |
| 1213 | ECHT_OFFEN | S; `spec_plan.py:490-491` | Subagent, ungeprüft |
| 1214 | ECHT_OFFEN | S; `spec_plan.py:50,318-321`; nahe #1213, gleiche Datei | Subagent, ungeprüft |
| 1217 | ECHT_OFFEN | M; `orchestrator-guard-impl.sh:1383-1392`; Approval-Pfad über Hook-API unverifiziert | Subagent, ungeprüft |

### Offene PRs

| Nr | Verdikt | Evidenz | Prüfstand |
|---|---|---|---|
| #1218 | gemergt (9aa0e0c0, 2026-11-11T06:41:30Z) | `feat/1190`, schloss #1190; beim Sweep offen mit test 3.12 Shard 2 FAILURE (Auftrag) | gh read-only (Entscheidung 38f) |
| #1145 | Duplikat von #1148 | Dependabot pytest-split, ändert nur `tests/requirements.txt` | Subagent, ungeprüft |
| #1148 | Duplikat von #1145 | wie #1145 | Subagent, ungeprüft |

---

## 2. Phasen

| Phase | Thema | Issues | Anzahl |
|---|---|---|---|
| A | Hygiene | 547, 857, 858, 1007, 1116, 1151, 1150, 946, 885, 977, 1190 (+ PRs 1218, 1145, 1148) | 11 |
| B | Kleine Bugs (S) | 1194, 1197, 1205, 1206, 1207, 1213, 1214, 1139, 1170, 1174, 1173, 898, 317 | 13 |
| C | Sync/Config-Robustheit | 1142, 1085, 1086, 1155, 1195, 1208, 1189, 1182, 1183, 1180, 1000 | 11 |
| D | Guards/Hooks/Commit-Authority | 1181, 1210, 1217, 1172, 1176, 1168, 1169, 1141 (letzter Teil nach #1181, Entscheidung 35) | 8 |
| E | Artefaktorte | 1187 (erster Block, Entscheidung 49), 1186, 1198, 1199, 1200, 1209 (eigener PR nach APPROVED-Spec, Entscheidung 36) | 6 |
| F | Label-Taxonomie | 1188, 1201, 1202, 1203, 1204, 1211 | 6 |
| G | Provider (Gemini/Antigravity/Opencode/Mammouth) | 854, 860, 1160, 1171, 1175, 800, 814 | 7 |
| H | Kontext/Token/Eval | 969, 1161, 1115, 1014, 778, 779, 780, 960, 1167, 1158, 1159 | 11 |
| I | Features/RFC (Concept, dann Spec, dann Approval-Gate) | 329, 330, 339, 548, 676, 679, 681, 783, 820, 832, 877, 896, 957, 958, 1004, 1106, 1113 | 17 |
| Summe | | | 11+13+11+8+6+6+7+11+17 = **90** |

Jede der 90 Nummern steht in genau einer Phase (89 gegen die Sweep-Liste geprüft, keine fehlende, keine doppelte; #1187 zusätzlich in E, Entscheidung 49).

### Auflösungen gegenüber dem Vorschlag

- #1198, #1199, #1200 stehen nur in Phase E (Kinder von #1186), nicht in B. Phase B hängt nicht von ihnen ab.
- #1203 steht nur in Phase F (Kind von #1188, prospektiv, `--labels` existiert noch nicht), nicht in B.
- #1204 steht in F (Vorschlag: F), nicht B.
- #977, #1150, #946, #885, #1190 stehen in A (#1190: bereits CLOSED nach gemergtem #1218, Beleg-Kommentar offen, Entscheidung 38f). Die dort genannten Folgeaktionen betreffen Issues anderer Phasen und sind Querverweise, keine Doppelzuordnung:
  - Label `blocked` für #860/#854: Aktion in A, Issues zählen in G.
  - Kommentare zu fertigen Teilen von #1155 (zählt in C), #1158, #1159, #1161 (H), #1160 (G): Aktion in A, Issues zählen dort.
- #1173 stand im Vorschlag nirgends. Zuordnung zu B: kleiner Bug (S), Admin-UI Tier-Preset-Speichern verliert YAML-Kommentare.
- Vorgezogen aus Phase I (Entscheidung 16): #898 (S) und #317 (S-M) nach B, #1000 (Mini-Spec) nach C. Phase I schrumpft von 20 auf 17.
- #977 (Tracker) in A statt H: reiner Tracker-Update, kein Code.
- #885 zählt weiter in A, wird aber dort nicht geschlossen (Entscheidung 13). Schließen ist ein eigener Schritt am Ende der letzten Welle.
- #1141 wandert von C nach D, als letzter Teil nach #1181 (Entscheidung 19, präzisiert durch Entscheidung 35): C 11, D 8, F 6. Konflikt gelöst (7b, Entscheidung 35).
- #1187 neu in Phase E als erster Block (Entscheidung 49): nicht unter den 89 Sweep-Issues, Wiederöffnen nur nach User-Freigabe. E = 6, Summe 90.
- Abweichung vom Vorschlag: keine weitere außer #1141 und #1187. Phasenschnitt sonst unverändert.

### Bewusst offen gelassen

| Issue | Grund |
|---|---|
| #860 | extern blockiert (agy SIGILL pclmul), kein Eingriff möglich |
| #854 | Umzug auf Skills erst nach Runtime-Probe (#860), Entscheidung 10 |
| #1211 | verfrüht, blockiert durch #1188 |
| #1203 | prospektiv, `--labels` existiert noch nicht; vor oder mit #1188 (Issue #1203); Plan F Task 1 zieht es vor Kern-T21 |
| #1209 | wartet auf #1186; eigener PR erst nach APPROVED-Spec (Entscheidung 36) |
| #885 | Epic bleibt OFFEN, bis alle Issues dieses Plans erledigt sind (Entscheidung 13); Phase A schließt es nicht, Restpunkte werden nicht einzeln neu angelegt |
| #946 | Löschung erst nach Freigabe der Branch/Stash-Tabelle (Entscheidung 12); destruktive Befehle nie umgangen |
| #1175 | Frage, nicht verifizierbar, Opencode-Quelle ungelesen |
| Phase I (Rest) | erst Concept, dann Spec, dann Freigabe (Doku-PR je Issue, Entscheidung 53); Umsetzung später in eigenen Phasen J1, J2, ... |
| #969 Baseline-Run | kostenpflichtig: nur nach Kostenschätzung und ausdrücklichem User-Ja (Entscheidung 11) |

### Phase A Detail (Hygiene)

Keine Umsetzung vor Freigabe. Schließen nur mit Evidenz-Kommentar. Auto-Close-Regel (Entscheidung 38e): PR- und Commit-Texte ohne Schlüsselwörter Closes/Fixes/Resolves; Kommentar zuerst, dann manuell schließen.

- Schließkandidaten: #547 (Evidenz dünn, siehe "Nicht verifiziert"; Folge-Issue mit allen fünf offenen Guide-Punkten aus `docs/guides/cross-harness-dev-isolation.md:176-199`, Entscheidung 39), #857, #858, #1007 (7 Punkte nicht einzeln verglichen), #1116, #1151.
- #1150: DOPPELT von #1186, schließen mit Verweis.
- #1190 (Entscheidung 38f): PR #1218 ist gemergt (9aa0e0c0, 2026-11-11T06:41:30Z); das Issue wurde automatisch geschlossen (2026-11-11T06:41:32Z, stateReason COMPLETED, ohne Kommentar). Kein Wiederöffnen. Check-Task am Ausführungstag: `gh issue view 1190` neu lesen, danach Beleg-Kommentar nachreichen (nach Freigabe Phase A).
- Dependabot #1145/#1148: Duplikate. Ursache: pytest-split 0.11.0 braucht Python >=3.10, die 3.9-Jobs scheitern. Vorgeschlagene Marker-Lösung in `tests/requirements.txt`:

```text
pytest-split>=0.8; python_version < "3.10"
pytest-split>=0.11.0; python_version >= "3.10"
```

  Danach beide PRs schließen oder einen rebasen. Nicht verifiziert, ob der Marker die Resolver-Fehler in CI behebt.
- #946 (Entscheidung 12): Tabelle je Branch/Stash erstellen (18 Zweifelsbranches auf origin, 9 Stash-Einträge; Spalten: Name, letzter Commit, Remote ja/nein, Vorschlag Merge/PR/Löschen, Begründung). Löschung nur nach Freigabe der Tabelle. Vorher den Stash zu `docs/838-spec-revision` sichern (z.B. als Patch-Datei oder Branch), da er dort der einzige Träger ist. Blockiert der Guard destruktive Git-Befehle (exit 2, vgl. Entscheidung 1), liefert der Assistent die fertigen Befehle und der User führt sie per `!` aus. Nie umgehen.
- #885 (Entscheidung 13): NICHT schließen. Nur Tracking-Kommentar mit Stand F-01..F-08. Schließen am Ende der letzten Welle (Welle 6), wenn alle Issues dieses Plans erledigt sind.
- #977: Tracker-Update (nur 969 offen, Phasen 2/3 ohne Issues).
- Label `blocked` für #860/#854.
- Kommentare zu fertigen Teilen von #1155, #1158, #1159, #1160, #1161.

---

## 3. Ausführungswellen

Eine Phase = ein Branch von origin/main = ein PR (Entscheidung 17). Ausnahmen: #1086i (eigener Nachfolge-PR nach dem letzten Phase-C-PR, Entscheidungen 18, 56); #1209 (eigener PR erst nach APPROVED-Spec, Entscheidung 36); gesperrte/spec-gesteuerte Tasks in einem Nachfolge-PR derselben Phase, max. 2 PRs je Phase (Entscheidung 52); Phase I: Doku-PR je Issue (Entscheidung 53). Squash-Merge nach grüner CI, kein Admin-Bypass.

| Welle | Phase | Hängt ab von | Parallel zu | Begründung |
|---|---|---|---|---|
| 0 | A | #1218 gemergt (9aa0e0c0, erfüllt; Beleg-Kommentar für #1190 offen) | restliche A-Aktionen sofort nach Freigabe | CI-Fix pytest-split entlastet alle folgenden PRs; #946-Tabelle zur Freigabe vorlegen |
| 1 | B | A (CI grün) | G-Vorarbeiten nur lesend | kleine Fixes; berührt u.a. `context.py` (`apply_settings_surface_shape`, 9aa0e0c0 `:1815`), `spec_plan.py`, `admin-server.py`/`admin-ui.html` (#1173, #898), viz-dashboard (#317) |
| 2 | C (ein PR, ein Commit je Task; #1189-Tasks als Commits in diesem PR, Entscheidung 36) | B (gleiche Dateien `context.py`, `sync_pipeline.py`); #1000 braucht freigegebene Mini-Spec | — (E nicht dateidisjunkt, läuft nach C) | Robustheit vor Feature-Arbeit; #1141 nicht in C (Entscheidung 35: in D); #1086i eigener Nachfolge-PR nach dem letzten Phase-C-PR (Entscheidungen 18, 56) |
| 2 | E: Block 1 #1187 (nachziehen, Entscheidung 49), dann Block 2 (ein PR ohne #1209) | A, C (nicht dateidisjunkt: `sync_pipeline.py`, `config.py`, `admin-server.py`; Plan E `:64`, Plan C `:7`) | — | Spec+Plan APPROVED (#1186, nennt #1187 als Voraussetzung 2); #1187 wieder öffnen nur nach User-Freigabe; Block 2 und F erst nach #1187-Block; Kette #1187 -> #1186, E vor F; F startet nicht vor E-Kern (Entscheidung 56); #1209 eigener PR nach APPROVED-Spec (Entscheidung 36) |
| 3 | F (ein PR; Task 2 #1201-Projektion gesperrt, Entscheidungen 51, 57, ggf. Nachfolge-PR nach 52) | E-Kern inkl. #1187-Block (Templates/Preset-Dateien; F startet nicht vor E-Kern, Entscheidung 56), #1188 Spec+Plan APPROVED | übrige D-Streams (nicht #1181) | #1203 vor Kern-T21 (Plan F Task 1, Issue "vor oder mit"); #1211 nach Kern (Pilot-Gate); #1141 gehört nicht mehr zu F (Entscheidung 35) |
| 3 | D, Stream A (#1181), danach #1141 als letzter Teil des D-PRs | F (#1188 zuerst, D stream A nach F), C (`hooks.py`, Guard-Pfade); #1181 und #1141 brauchen freigegebene Spec; Hook-API-Prüfung für `ask` vor der #1217-Spec | übrige D-Streams: Reihenfolge offen (Phasenplan D, Entscheidung 35 lässt Zuschnitt offen) | Kette #1187 -> #1186 -> #1188 -> #1181 -> #1141 (Entscheidungen 1-2, 19, 35) |
| 4 | G | A (Labels), B (#1170 vor #854), #1085/#1155-Flag aus C | — (H nicht dateidisjunkt) | #860 extern blockiert, #854 (Skills) wartet auf Runtime-Probe |
| 4 | H | B, C, #1086i (Split), D (H-Task 10 nach D-Merge, `hook_json_get_many`); G für H-Tasks 10b/17/23/24 (`.meta-config/project.yaml` G-Task 8 = H-Task 17; G vor H, O-H7 -> Entscheidung 56) | — (G nicht dateidisjunkt) | #969: Schnittstelle auf Per-Testfall-Ergebnisse umbauen, dann McNemar; Baseline-Run nur nach Kostenschätzung und User-Ja |
| 5 | I (Doku-PR je Issue, Entscheidung 53) | je Item: Concept, Spec, Approval-Gate; Umsetzung in späteren Phasen J1, J2, ... je Issue mit eigenem Plan und PR; Umsetzung #681/#1004-E/#1113 nach D (#1176, `orchestrator.md`); #832 nach C; #958, #820+#877 nach C und #1086i (Plan I) | untereinander | keine Umsetzung ohne `Status: APPROVED`; #877 und #820 gemeinsames Concept |
| 6 | Abschluss | alle Issues dieses Plans erledigt | — | #885 schließen (eigener Schritt) |

Regeln:
- Parallel nur bei disjunkter `Files:`-Liste im jeweiligen Phasenplan. Nicht verifiziert, bis die Phasenpläne existieren.
- Innerhalb einer Phase sequentiell, wenn dieselbe Datei betroffen ist (z.B. #1213/#1214 in `spec_plan.py`).
- Phase I: Doku-PR je Issue (Concept, dann Spec, Freigabe-Gate); Umsetzung später in eigenen Phasen J1, J2, ... je Issue mit eigenem Plan und PR (Entscheidung 53, ersetzt die Phase-I-Regel aus 36).
- Der `context.py`-Split (#1086i) läuft als eigener Nachfolge-PR nach dem letzten Phase-C-PR (Entscheidungen 18, 56), damit B und die übrigen C-Teile nicht in eine verschobene Datei hineinrebasen.

---

## 4. Querschnittsregeln

- **Migrationsreihenfolge:** A, B, C vor allen Phasen mit Template-/Config-Änderungen (E, F, G). Schema-/Config-Änderungen immer mit Migrationspfad und `--validate`-Lauf. Details in den Phasenplänen.
- **Freshness-Check:** Vor jeder Ausführung `check_plan_refs.py` gegen origin/main `9aa0e0c0` laufen lassen. Zeilenanker aus dieser Roadmap stammen von `a41745ed` und veralten; bei Ausführung neu messen (Entscheidung 37 für #898, analog für alle Anker). Existenz des Skripts in diesem Repo: nicht verifiziert.
- **Ressourcen:** CI-Last begrenzen (ein offener Phasen-PR gleichzeitig, außer disjunkte Dateien); Python-3.9-Kompatibilität in allen Änderungen (kein `X | Y`-Typsyntax ohne Future-Import, kein `match`); Zeitbudget pro Phase im Phasenplan über `effort-estimator`, hier keine Schätzung.
- **Commit-/PR-Text:** wird als Datei bereitgestellt (z.B. unter `.tmp/`), nicht inline per Shell.
- **Destruktive Git-Befehle:** werden nie umgangen. Blockiert der Guard, liefert der Assistent die fertigen Befehle, der User führt sie per `!` aus (betrifft #946).
- **Issues schließen:** nur nach Freigabe und nur mit Evidenz-Kommentar, Kommentar zuerst, dann manuell schließen. PR- und Commit-Texte enthalten keine Closing-Schlüsselwörter (Closes/Fixes/Resolves), Entscheidung 38e. Bei Kommaliste "Resolves" schließt nur die erste Nummer automatisch, Rest manuell.
- **Kostenpflichtige Läufe** (#969 Baseline): nur nach Kostenschätzung und ausdrücklichem User-Ja.
- **Kein Worktree-Isolation-Argument** beim Spawnen von Subagenten.
- **Ein PR pro Phase** (Entscheidungen 17, 36, 52, 53): ein Branch, viele Commits, ein Commit je Task. Ausnahmen nur: #1086i, eigener Branch und Nachfolge-PR nach dem letzten Phase-C-PR (Entscheidungen 18, 56); #1209, eigener PR erst nach APPROVED-Spec (Entscheidung 36); gesperrte/spec-gesteuerte Tasks laufen in einem Nachfolge-PR derselben Phase, der Phasen-PR enthält nur derzeit ausführbare Tasks, max. 2 PRs je Phase, #1014-Folgepläne fallen darunter (Entscheidung 52); Phase I: Doku-PR je Issue, Umsetzung in eigenen Phasen J1, J2, ... (Entscheidung 53, nur für Phase I). #1189 ist keine Ausnahme: seine Tasks laufen als Commits im C-PR; der APPROVED-Plan #1189 bleibt unverändert, sein "eigener PR"-Vermerk ist durch Entscheidung 17/36 ersetzt.
- **Commit-Trailer** (Entscheidung 25): Trailer kommen wörtlich aus dem Task-Prompt; der git-Agent übernimmt sie unverändert. Phasenpläne mit abweichender Vorgabe werden korrigiert.

---

## 5. Risiken

| Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|
| Sweep-Evidenz nur von Subagenten, 84 von 89 Sweep-Zeilen ungeprüft | Falsche Schließung oder Doppelarbeit | Vor jedem Schließen Stichprobe/Hand-Check, Freshness-Check |
| #1218 (104 Dateien) war beim Sweep rot und offen; jetzt gemergt (origin/main `9aa0e0c0`, Entscheidung 38f) | Sweep-Basis `a41745ed`; Anker können verrutscht sein | Erledigt: Phasenpläne auf origin/main `9aa0e0c0` rebased; Anker bei Ausführung neu messen |
| Dateikonflikte zwischen B, C, E (`context.py`, `admin-server.py`) | Rebase-Aufwand | Wellen sequentiell, Dateilisten je Phasenplan |
| Python-3.9-Jobs scheitern an Abhängigkeitsupdates | CI dauerhaft rot | Marker-Fix in Phase A, nicht verifiziert |
| #1210 Rollenbindung per Harness-Feld (Entscheidung 2) ist Security Boundary | Guard umgehbar, falls Payload-Feld fehlt oder fälschbar | Payload-Feld vor Spec prüfen; Convention-vs-Security-Terminologie beachten |
| Destruktives Gate #1217 über `ask`-Permission: Hook-API-Support unverifiziert (Entscheidung 1) | Plan hinfällig | Hook-API-Prüfung VOR der Spec |
| #1086i `context.py`-Split (3495 Zeilen, L-Refactoring) in derselben Runde | Merge-Konflikte, Regressionen, Scope-Explosion | eigener Plan und Nachfolge-PR nach dem letzten Phase-C-PR (Entscheidung 56), Tests vor dem Split grün, kein Verhaltenswechsel |
| #877 + #820 zusammengeführt (XL) | Concept zu groß, Verzögerung der übrigen Phase-I-Items | ein gemeinsames Concept, Gate vor Spec, keine Umsetzung vorab |
| #1085b nur opt-in per `--fail-on-p0` (Entscheidung 4, präzisiert durch 38b: `--strict` nur `--doctor`-exklusiv) | P0-Befunde unbemerkt, wenn CI das Flag nicht setzt | CI-Workflow muss `--fail-on-p0` selbst setzen, im Phasenplan C als Task |
| #946: Guard blockiert Löschung (exit 2) | Löschung stockt | fertige Befehle liefern, User führt per `!` aus; Stash `docs/838-spec-revision` vorher sichern |
| #969 Interface-Umbau auf Per-Testfall-Ergebnisse (`eval_gate.py:28` bewusst aufgeschoben) | Regression im Eval-Gate, Kosten bei Baseline | Umbau mit Tests, Baseline nur nach Kostenschätzung und User-Ja |
| #1004 bleibt ungeteilt (Teile E und F im Issue) | größerer Zuschnitt, Spec-Umfang wächst | Spec je Teil gliedern, Gate vor Umsetzung |
| #885 offen bis zum Ende | Epic wird vergessen | Welle 6 als eigener Schritt eingeplant |
| Phase I (17 Items) verdrängt Bugfixes | Backlog wächst | erst nach Wellen 1-4, Gate je Item |
| Lösch-/Close-Aktionen auf Basis dünner Evidenz (#547, #1007) | Verlust offener Arbeit | siehe "Nicht verifiziert" |
| #1187 nachziehen (Entscheidung 49): Code `PROJECT_CONTEXT_INJECTED` und Szenarien 95-98 fehlen auf origin/main | Kette #1187 -> #1186 -> #1188 -> #1181 -> #1141 und #1197 (B-N4, via #1187-T9) warten auf den #1187-Block | #1187 erster Block in E; Wiederöffnen nur nach User-Freigabe; E-Block 2 und F erst danach |
| Ein PR pro Phase bei großen Phasen (C, E, F, D; I ausgenommen nach 53) | Sehr großer PR, schwer zu reviewen, lange Branches, Rebase-Konflikte | Ein Commit je Task, Tests je Commit grün, Umfang im jeweiligen Phasenplan vor Start prüfen (Entscheidung 17) |
| ~~Phase I (17 Items) als ein PR (Entscheidung 36) wird ein großer Docs-PR~~ | ~~Review-Last~~ | Erledigt (Entscheidung 53): Doku-PR je Issue, Umsetzung in J1, J2, ... |
| Phase I: bis zu 17 Doku-PRs plus Umsetzungsphasen J1, J2, ... (Entscheidung 53) | Viele PRs, CI-Last, Querverweise zwischen Concepts | Ein offener PR gleichzeitig außer disjunkte Dateien (Abschnitt 4); Gate je Issue |
| #1172 Permission-Regel für den git-Agenten (Entscheidung 47) | Berechtigungsänderung, evtl. nicht provider-konfigurierbar | Machbarkeits-Task zuerst (Evidenz am Code/Doku), Security Boundary, Spec-Gate; Fallback Merge-Pfad aus dem Main Chat |
| #1201: Entscheidung 51 (`bug`) widerspricht APPROVED-Referenzplan Label-Taxonomie (K-7, F-1) | Plan F Task 2 blockiert | Referenzplan nicht ändern; erneute User-Freigabe nötig, Task 2 bis dahin gesperrt |
| #1189: APPROVED-Plan nennt "eigener PR" (Entscheidung 36 ersetzt das) | Widerspruch zum Ein-PR-pro-Phase-Schnitt in C | Erledigt: #1189-Tasks als Commits im C-PR; Vermerk im C-Plan, Plan #1189 unverändert |
| #1086g ohne Tier-Rework geschlossen (Entscheidung 24) | Tier-Mapping bleibt im Ist-Zustand, Folgeaufwand später | Ist-Zustand im Schließ-Kommentar dokumentieren |
| #1004 Teil F: Planner-Bash-Allowlist (Entscheidung 33) | Lockerung einer Berechtigung; Security Boundary, kein bloßer Convention-Schutz | Security-Boundary-Prüfung in der Spec, nur eng begrenzte read-only-Befehle |
| #957 größerer MVP-Umfang (Entscheidung 32 Q5: Release-Template an `release.distribution` gekoppelt) | Spec und Phase I wachsen | Spec bleibt DRAFT bis User-Freigabe; Umfang in der Spec-Revision begrenzen |
| ~~#1141 liegt in F, muss aber nach #1181 (D Stream A) laufen~~ | ~~Konflikt~~ | Erledigt (Entscheidung 35): #1141 in D als letzter Teil nach #1181 |
| #1210 Rollenbindung: Entscheidung 2 (Harness-Feld) vs. D-neu-4 (ohne Payload-Rollenfeld) | Security-Einstufung unklar | Erledigt (Entscheidung 38a): D-neu-4 gilt nur bei negativem Befund aus Task 0, dann neue User-Bestätigung; Payload-Feld vor Spec prüfen |

---

## 6. Nicht verifiziert

- Gerenderte Dateien (`.claude/agents/`, AGENTS.md usw.): nicht neu gerendert oder verglichen.
- CI-Status: nicht geprüft. #1218-Angaben (104 Dateien, test 3.12 Shard 2 FAILURE, CI läuft) stammen aus dem Auftrag und beziehen sich auf den Stand vor dem Merge. Merge-Stand (9aa0e0c0, 2026-11-11T06:41:30Z) per gh read-only gelesen (38f).
- #1190: Issue-Stand CLOSED (06:41:32Z) per gh read-only; Beleg-Kommentar fehlt; am Ausführungstag neu lesen, nie wieder öffnen.
- #898: Zeilen der Admin-Server-Funktionen (`ModelsService._load_models_dev_data`, `_apply_pricing_overlay`, `_handle_post_models_dev_import`) in der neuen Worktree-Basis nicht gemessen; Vorbedingung (vier Claude-5.x-IDs im models.dev-Payload) nicht geprüft (37).
- #329/#330 Ein-Konzept-Zuschnitt (38d): zur Bestätigung im Review.
- Hook-Laufzeitverhalten (Guard, Exit-Codes): nicht ausgeführt. Ob die Hook-API eine `ask`-Permission statt exit 2 unterstützt (Entscheidung 1): nicht verifiziert. Ob das Hook-Payload die Rolle als Feld liefert (Entscheidung 2): nicht verifiziert.
- Messzahlen aus Issue-Texten (z.B. #800, #969, #1169 Python-Spawns): nicht nachgemessen.
- Evidenz für #547: nur ein Subagent.
- Einzelne Punkte von #1007: die 7 "zu bauen"-Punkte nicht einzeln gegen PRs #1012, #1016, #1017, #1018, #1019 verglichen.
- Externe Aussagen in #676 (HACS/HA), Opencode-Verhalten in #1175.
- Alle Zeilenanker (`datei:zeile`) gelten für `a41745ed`, nicht für `9aa0e0c0`; neu messen; der Anker zu #1173 (`admin-server.py:5089`) stammt aus dem Issue-Text.
- #885: F-09..F-16 und Kinder #932/#936 nicht geprüft.
- Marker-Fix für pytest-split: nicht gegen CI getestet.
- Ob `check_plan_refs.py` existiert und wie es aufgerufen wird.
- #1000: Wortlaut der Optionen A/B/C wurde vom Main Chat nur aus dem Index gelesen, nicht aus dem Issue-Text. Im Concept gegen den Issue-Text gegenprüfen (Entscheidung 8).
- #1085: ob CI-Workflows `--strict`/`--fail-on-p0` bereits setzen oder setzen können.
- `eval_gate.py:28`: Hinweis auf bewusst aufgeschobenes Per-Testfall-Interface aus dem Auftrag, nicht selbst gelesen.
- #946: Stand der 18 Branches und 9 Stash-Einträge nur laut Sweep, nicht neu erhoben.
- #1113: welche Provider eine Ask-User-Funktion tatsächlich bieten, nicht geprüft.
- #1187: laut Entscheidung 49 fehlen Code `PROJECT_CONTEXT_INJECTED` und Szenarien 95-98 auf origin/main; vom Worker nicht selbst nachgeprüft.
- origin/main `9aa0e0c0` inklusive PR #1218: Basis der Phasenpläne (Rebase erledigt, laut Auftrag). Sweep-Basis bleibt `a41745ed`.
- Entscheidungen 17-34 nur gegen den Entscheidungstext (`.tmp/decisions-part2.md`) abgeglichen, nicht gegen Issue-Texte. 35-38 gegen `.tmp/decisions-part3.md`. 39-57 nur gegen den Auftragstext.

---

## 7. Entscheidungsliste (vom User beantwortet 2026-11-10/11)

Alle 16 Punkte sind beantwortet. "weicht von Empfehlung ab" heißt: Der User hat nicht die erste Option des Planners gewählt.

1. **#1217, Approval-Pfad fürs destruktive Gate (`ask`-Permission statt exit 2?)**
   - Antwort: Ja, Approval-Pfad über `ask`-Permission.
   - Konsequenz: Hook-API-Support VOR der Spec prüfen (nicht verifiziert). Bei fehlendem Support Spec überarbeiten, nicht erzwingen. Phase D.
2. **#1210, Rollenbindung des Sentinels**
   - Antwort: Harness-Feld (Rolle aus dem Hook-Payload).
   - Konsequenz: Spec muss Payload-Feld, Fälschbarkeit und Fallback beschreiben. Security Boundary, Phase D.
3. **#1142, ungültiges `auto_commit`**
   - Antwort: fail-soft mit Warnung.
   - Konsequenz: Allowlist nicht schreiben; Warnung auch in der `--validate`-Zusammenfassung. Phase C.
4. **#1085b / #1155 F5, P0-Befunde**
   - Antwort: nur per `--strict` / `--fail-on-p0` (opt-in). **Weicht von Empfehlung ab** (Empfehlung war ERROR im CI-Modus).
   - Konsequenz: CI muss das Flag selbst setzen, eigener Task im Phasenplan C. Plain-Sync bleibt exit 0.
5. **#1141, Schema**
   - Antwort: Warnung bei unbekannten Keys, Schema bleibt offen; fehlende gültige Keys (`rules-preset`, `test-repo`, `backup`, `mcp`) ins Schema aufnehmen.
   - Konsequenz: kein `additionalProperties:false`. Phase C.
6. **#1086, Umfang**
   - Antwort: g (Tier-Mapping), h (`priority` in role-defaults) UND i (`context.py` splitten) in dieser Runde. i **weicht von Empfehlung ab** (Empfehlung: Split nicht in dieser Runde).
   - Konsequenz: i bekommt einen eigenen Plan (L, Refactoring, 3495 Zeilen) und eigenen PR, zuletzt in Phase C. Siehe Risiken.
7. **#877 vs #820**
   - Antwort: zusammenführen. **Weicht von Empfehlung ab** (Empfehlung: abgrenzen).
   - Konsequenz: ein gemeinsames Concept für Domain-Cluster und Familienregeln, XL. Beide Issues bleiben in Phase I (Zähler unverändert), im selben Concept.
8. **#1000, Checkpoints**
   - Antwort: B+C wie im Issue.
   - Konsequenz: Mini-Spec, Phase C (vorgezogen, Entscheidung 16). Optionswortlaut A/B/C vom Main Chat nur aus dem Index gelesen, im Concept gegen den Issue-Text prüfen.
9. **#1004, Zuschnitt**
   - Antwort: alles in #1004 behalten, Teile E und F bleiben im Issue, kein Split, kein neues Issue. **Weicht von Empfehlung ab** (Empfehlung: E und F herauslösen).
   - Konsequenz: Spec gliedert Teile intern, Phase I.
10. **#854, Gemini-Commands**
    - Antwort: auf Skills umziehen. **Weicht von Empfehlung ab** (Empfehlung: Commands-Surface streichen).
    - Konsequenz: erst nach Runtime-Probe (#860), Phase G.
11. **#969**
    - Antwort: Baseline-Run planen UND McNemar ergänzen. **Weicht von Empfehlung ab** (Empfehlung: McNemar streichen).
    - Konsequenz: `eval_gate`-Schnittstelle auf Per-Testfall-Ergebnisse umbauen (`eval_gate.py:28` vermerkt dies als bewusst aufgeschoben). Baseline-Run erst nach Kostenschätzung und ausdrücklichem User-Ja. Phase H.
12. **#946**
    - Antwort: Tabelle je Branch/Stash planen (18 Zweifelsbranches auf origin, 9 Stash-Einträge). Der User will, dass der Assistent löscht ("Planen und du sollst löschen").
    - Konsequenz: Löschung erst nach Freigabe der Tabelle. Destruktive Git-Befehle werden nie umgangen. Blockiert der Guard (exit 2, vgl. Entscheidung 1), liefert der Assistent die fertigen Befehle, der User führt sie per `!` aus. Stash `docs/838-spec-revision` vor jeder Löschung sichern. Phase A.
13. **#885**
    - Antwort: Epic bleibt OFFEN, bis alle Issues dieses Plans erledigt sind. **Weicht von Empfehlung ab** (Empfehlung: jetzt als Epic schließen).
    - Konsequenz: Phase A schließt #885 NICHT. Restpunkte werden nicht einzeln neu angelegt. Schließen ist ein eigener Schritt am Ende der letzten Welle (Welle 6).
14. **#1106**
    - Antwort: in A+C, D, E, F aufteilen und mit #1102 abstimmen.
    - Konsequenz: Teilspecs je Block, Phase I.
15. **#1113**
    - Antwort: Spec als TEIL des Umsetzungsplans (kein separates Dokument vorab); providerkompatible Erzeugung, wo möglich alle Provider unterstützen. Gate bleibt: Spec-Abschnitt braucht `Status: APPROVED` vor der Umsetzung.
    - Konsequenz: Phase I, ein Dokument, Provider-Matrix im Plan.
16. **Scope, Phase I**
    - Antwort: kleine Items vorziehen: #898 (S) und #317 (S-M) nach Phase B, #1000 (Mini-Spec) nach Phase C. Rest von Phase I bleibt hinter dem Concept/Spec-Gate.
    - Konsequenz: neue Zähler B 13, C 12, I 17 (Summe weiter 89).

## 7b. Entscheidungsliste Teil 2 (vom User beantwortet, Entscheidungen 17-34)

Quelle: `.tmp/decisions-part2.md` (verbindlich, 17-34) und `.tmp/decisions-part3.md` (verbindlich, 35-38). "Weicht von Empfehlung ab" heißt: Der User hat nicht die erste Option des Planners gewählt. Entscheidung 34 ist eine Sammlung von Plan-Defaults; alle sind übernommen, keine weicht ab.

17. **PR-Schnitt**
    - Frage: Wie viele PRs pro Phase?
    - Antwort: Strikt ein PR pro Phase. **Weicht von Empfehlung ab.**
    - Folge für Plan: Phase C (Teil-PRs C-1..C-5), E (E-1..E-4) und F (F-PR1..4) werden zu je einem Phasen-PR mit einem Commit je Task. Querschnittsregel "eine Phase = ein Branch = ein PR" gilt, Ausnahme siehe 18.

18. **#1086i (`context.py`-Split)**
    - Frage: Wie wird der Split im PR-Schnitt behandelt?
    - Antwort: Ausnahme von 17: eigener Branch und eigener PR, direkt nach dem übrigen Phase C.
    - Folge für Plan: Ausnahme in Abschnitt 3 und 4 eingetragen. Eigener Plan (L, Refactoring) bleibt Voraussetzung.

19. **Kette und Phasenzuordnung**
    - Frage: In welcher Reihenfolge laufen die abhängigen Issues?
    - Antwort: Kette des genehmigten Plans: #1187 -> #1186 (E) -> #1188 (F) -> #1181 (D Stream A) -> #1141.
    - Folge für Plan: #1141 verlässt Phase C und Welle 2 und steht in Phase F. Zähler: C = 11, F = 7, Summe 89. D Stream A (#1181) kommt nach F. Wellen in Abschnitt 3 angepasst.
    - #1187 steht nicht unter den 89 Issues und ist laut Sweep geschlossen. Ob es umgesetzt werden muss, ist ungeklärt. Prüfaufgabe im E/F-Plan, nicht raten. Erledigt durch Entscheidung 49 (nachziehen, erster Block in Phase E).
    - Konflikt #1141 (Phase F vs. Reihenfolge nach D Stream A): gelöst durch Entscheidung 35 (Phase D, nach #1181).

20. **#547 (Cross-Harness Dev-Isolation)**
    - Frage: Wie wird #547 abgeschlossen?
    - Antwort: Schließen UND Folge-Issue für die 3 Restpunkte (Strategie B, 3. Harness, Task-Partitionierung). Schließen und Anlegen erst nach Freigabe der Phase A. Issue-Text vorab als Datei entwerfen.
    - Folge für Plan: Phase A. Entwurf liegt vor Freigabe als Datei vor; Schließen und Anlegen nur nach Freigabe. Umfang erweitert durch Entscheidung 39 (alle fünf Guide-Punkte).

21. **#1007 (Opencode-Provider)**
    - Frage: Wie wird #1007 abgeschlossen?
    - Antwort: Schließen mit Evidenz-Kommentar (PRs #1012, #1016-#1019, `docs/providers/opencode.md`). Die beiden bewussten Abweichungen werden benannt: `experimental.todo` und `$schema`/`skills`.
    - Folge für Plan: Phase A. Vor dem Schließen die sieben "zu bauen"-Punkte gegen die PRs prüfen (Abschnitt 6).

22. **#1173 (Tier-Preset verliert YAML-Kommentare)**
    - Frage: Wie wird der Kommentarverlust beim Speichern behandelt?
    - Antwort: Diff-Guard wie bei ai-providers: HTTP 400 ohne `__allow_lossy__`, Fehleranzeige in der UI. Das Akzeptanzkriterium "Kommentare bleiben erhalten" wird explizit NICHT erfüllt.
    - Folge für Plan: Phase B. Im Plan und im PR vermerken, dass dieses Kriterium nicht erfüllt ist.

23. **#898 Punkt 3 (Preise)**
    - Frage: Woher kommen die Preise im Pricing-Overlay?
    - Antwort: Aus der BESTEHENDEN models.dev-Funktion des Syncers. Nicht von Hand ins Overlay, nicht gespiegelt. Alte Aliase bleiben (Tests pinnen sie).
    - Folge für Plan: Phase B. Plan B Task 12 Teil B neu aufbauen. Der Worker belegt die konkrete Funktion mit Datei:Zeile; der Name wird nicht geraten.

24. **#1086g (Tier-Mapping)**
    - Frage: Wie wird #1086g behandelt?
    - Antwort: Ist-Zustand dokumentieren und #1086g mit Entscheidungskommentar schließen. Kein Tier-Rework. **Weicht von Empfehlung ab.**
    - Folge für Plan: Phase C (#1086). Schließen erst nach Freigabe, mit Evidenz-Kommentar. Konflikt zu Entscheidung 6 (g in dieser Runde) gelöst durch 38c (g nur Doku/Schließen).

25. **#1168 (Co-Author-Trailer)**
    - Frage: Welcher Trailer gilt beim git-Agenten?
    - Antwort: Der Trailer aus dem Task-Prompt gewinnt. Der git-Agent übernimmt ihn wörtlich.
    - Folge für Plan: Phase D. Phasenpläne mit der Vorgabe "kein Co-Authored-By selbst setzen" (z.B. Plan C Global Constraints) werden korrigiert: Trailer sind vom Task-Prompt wörtlich vorgeschrieben.

26. **#1211 (Pilot-Gate)**
    - Frage: Wird das Pilot-Gate geändert?
    - Antwort: Pilot-Gate bleibt. Das Issue bleibt blockiert.
    - Folge für Plan: Phase F. Keine Umsetzung in diesem Plan; Blockade durch #1188 bleibt.

27. **#814 (stdio-MCP cwd)**
    - Frage: Welcher Umfang gilt für #814?
    - Antwort: Externer Tool-Modus (`config-generated-by`) plus cwd-Emission und fail-closed/warn-Aktivierung.
    - Folge für Plan: Phase G. Umfang in den Phasenplan G übernehmen.

28. **#1161 Punkt 5 / #1169 (Hook-JSON-Parsing)**
    - Frage: Wie wird die Hook-Latenz (9-11 Python-Spawns pro Bash-Call) gelöst?
    - Antwort: Neue Funktion `hook_json_get_many`: JSON einmal parsen, NUL-getrennte Ausgabe, `read -r -d ''`, Bash 3.2, kein `eval`. Spec vorab mit User-Freigabe.
    - Folge für Plan: #1169 in Phase D, #1161 Punkt 5 in Phase H. Spec muss vor der Umsetzung freigegeben sein.

29. **#1161 Punkt 2 (Agentenverzeichnis in AGENTS.md)**
    - Frage: Wo steht das Agentenverzeichnis?
    - Antwort: In AGENTS.md nur für Provider ohne eigene Agentenliste, gesteuert über ein Capability-Flag (z.B. `roster_in_harness`). Keine Verzweigung nach Providername.
    - Folge für Plan: Phase H. Flag über Config-Keys/Capability-Flags ausdrücken.

30. **#339 (SE-Cascade-Optimierung)**
    - Frage: Wie geht es mit #339 weiter?
    - Antwort: Die Spec braucht eine erneute Freigabe durch den User, bevor weiter geplant wird.
    - Folge für Plan: Phase I. Keine weitere Planung vor der Re-Approval.

31. **#896 (Admin-UI Netzwerkzugriff)**
    - Frage: Welche Dienste sind netzwerkweit konfigurierbar?
    - Antwort: BEIDE Dienste, jeweils mit eigener Option und sicherem Default (Viz-Dashboard 8765, MCP 9090). **Weicht von Empfehlung ab.**
    - Folge für Plan: Phase I. Eigene Spec. Der DRAFT-Plan `docs/plans/2026-10-07-admin-ui-network-and-manager-plan.md` geht zur Freigabe.

32. **#957 (PR-Templates, Spec `docs/specs/2026-10-11-pr-templates-spec.md`, Abschnitt 7)**
    - Frage: Wie lauten die Antworten auf Q1-Q5?
    - Antwort:
        - Q1: EIGENER Index für PR-Templates, nicht `generated-file-hashes.json`. **Weicht von Empfehlung ab.**
        - Q2: Default UND benannte Templates.
        - Q3: Templates auf Englisch, mit DOCS_LANGUAGE-Hinweis.
        - Q4: Reihenfolge in `platforms:` plus Warnung.
        - Q5: Release-Template von Anfang an an `release.distribution` gekoppelt. **Weicht von Empfehlung ab** (größerer MVP-Umfang).
    - Folge für Plan: Phase I. Spec bleibt DRAFT. Antworten fließen in die Spec-Revision in Phase I; danach geht die Spec zur Freigabe an den User.

33. **#1004 Teil F (Planner-Berechtigung)**
    - Frage: Welche Bash-Rechte bekommt die Planner-Rolle?
    - Antwort: Read-only-Allowlist für Bash. **Weicht von Empfehlung ab.**
    - Folge für Plan: Phase I. Die Änderung ist eine Berechtigungsänderung und wird als Security Boundary geprüft (nicht nur Convention boundary), Prüfung in der Spec festgehalten. Liste eng begrenzt auf read-only-Befehle.

34. **Plan-Defaults**
    - Frage: Werden die vorgeschlagenen Plan-Defaults übernommen?
    - Antwort: Alle übernommen. Keine Abweichung von der Empfehlung.
    - Folge für Plan:
        - B-N1: #1213-Prüfung als WARNING.
        - B-N4: #1197 über #1187-T9; einziger Ratchet-Test in B. Abhängig von #1187, siehe 19.
        - B-N5: #1139 ohne Skip; Hang-Guard genügt.
        - C-N2: #1085a ohne Hooks-Auto-Enable, nur dokumentieren.
        - C-N3: #1085b nur `--fail-on-p0`; `--strict` bleibt `--doctor`-exklusiv. Abgleich mit Entscheidung 4 erledigt durch 38b.
        - C-N4: #1086 a-e jetzt, f zurückgestellt; g siehe 24. Einordnung von h (Phase C) und i (eigener PR) erledigt durch 38c.
        - D-neu-3: #1176 nur dokumentieren, kein Monitor.
        - D-neu-4: #1210 ohne Payload-Rollenfeld: Convention boundary dokumentieren, endgültig nach Evidenz. Widerspruch zu Entscheidung 2 erledigt durch 38a.
        - E-N2: #1199 mit Drift-Test.
        - E-N3: superseded APPROVED-Dokumente nur im Wrapper-Plan bzw. PR vermerken.
        - F-neu-4: #1202 ohne Severity-/Status-Achse.
        - F-neu-5: #1201 Default-Wert ändern, Golden-Test bewusst anpassen.
        - F-neu-6: #1204 Issues-Domäne aus der Overrides-Ansicht entfernen.
        - G-N1: #800 dünne Zielvariante A; endgültig erst nach Probe-Evidenz (`decisions-part2.md:22` gilt für G-N1, G-N3, G-N4).
        - G-N3: Gemini CLI bleibt Default, Antigravity opt-in; endgültig erst nach Probe-Evidenz.
        - G-N4: Opencode-Keys bleiben; endgültig erst nach Probe-Evidenz.
        - D-H3: deutsche Routing-Keywords bleiben; Guard-Test friert das Set ein.
        - D-H4: REQ-ID-Format `REQ-<AREA>-<NN>`.
        - D-H5: provider-expert als `name_only` registriert.
        - I-N1/I-N2: #329/#330 ein Konzept, je eigene Spec (38d, zur Bestätigung im Review); #676/#1106 ein Konzept, getrennte Specs.
        - I-N4: #548 nur Topic-Quelle.
        - I-N5..I-N11 und I-N15: je Spec mit User-Freigabe.
        - Bereits durch 17-19, 23, 27 entschieden: D-neu-2, F-neu-2, E-N1, F-neu-1, B-N3, G-N2.

35. **#1141 Platzierung (Konflikt aus 19)**
    - Frage: Wo steht #1141, da es nach #1181 laufen muss und D Stream A nach F liegt?
    - Antwort: In Phase D, NACH #1181.
    - Folge für Plan: #1141 ist letzter Teil des D-PRs nach #1181. Phase F = 6 Issues (1188, 1201, 1202, 1203, 1204, 1211), Phase D = 8 Issues (1181, 1210, 1217, 1172, 1176, 1168, 1169, 1141). Zähler C 11, B 13, A 11, E 5, G 7, H 11, I 17; Summe 89. F-Plan Task 5 (#1141) entfällt (Querverweis auf D). D-Plan erhält #1141 als letzten Teil; #1141 braucht eine APPROVED-Spec (Spec-Gate zuerst). Inhalt: Warnung bei unbekannten Keys, Schema bleibt offen (kein `additionalProperties:false`); fehlende gültige Keys `rules-preset`, `test-repo`, `backup`, `mcp` ins Schema aufnehmen (`_comment` steht bereits im Schema). Issue-Text: `W/.tmp/issues/1141.md`.
    - Konflikt gelöst.

36. **PR-Ausnahmen und Phase I**
    - Frage: Welche Ausnahmen gelten vom Ein-PR-pro-Phase-Schnitt?
    - Antwort: Nur #1209 und #1086i. #1209 wird vom E-PR abgespalten und bekommt einen eigenen PR erst nach APPROVED-Spec. #1189 ist KEINE Ausnahme: seine Tasks laufen als Commits im C-PR; der APPROVED-Plan #1189 bleibt unverändert. Phase I: strikt ein PR pro Phase (Phase-I-Teil ersetzt durch Entscheidung 53; weitere Ausnahme Entscheidung 52).
    - Folge für Plan: Ausnahmen in Abschnitt 3 und 4 eingetragen. Risiko "großer Docs-PR" in Abschnitt 5 eingetragen. Der User kann später Ausnahmen setzen. Zuordnung der Konflikte 5 (Phase I), 9 (#1209) und 11 (#1189) gelöst. Die Ausnahme #1086i (Entscheidung 18) bleibt unverändert.

37. **#898 Punkt 3 (Admin-Funktion)**
    - Frage: Welche Funktion ist mit "#898 Punkt 3" gemeint?
    - Antwort: Die Admin-Server-Funktion ist gemeint (`scripts/admin-server.py`: `ModelsService._load_models_dev_data`, `_apply_pricing_overlay`, `_handle_post_models_dev_import`). Zeilen neu messen.
    - Folge für Plan: Plan B Task 12 Teil B auf diese Funktionen ausgerichtet. Neue Vorbedingungs-Task: prüfen, ob die vier Claude-5.x-Modell-IDs im models.dev-Payload vorkommen. Falls nicht: Task blockiert, Bericht an den User. Konflikt 23 bleibt unverändert gültig (Preise nur aus der bestehenden models.dev-Funktion).

38. **Auflösungen ohne neue Frage (vom User bestätigt)**
    - (a) #1210: Entscheidung 2 (Harness-Feld) und D-neu-4 sind NICHT widersprüchlich. D-neu-4 gilt nur bei negativem Befund aus Task 0; danach bestätigt der User neu. Konflikt 2 gelöst.
    - (b) #1085b: Flag ist nur `--fail-on-p0` (Entscheidung 4 + C-N3). `--strict` bleibt `--doctor`-exklusiv. Konflikt 4 gelöst.
    - (c) #1086: g nur Doku und Schließen (Entscheidung 24), a-e jetzt, f zurückgestellt, h gehört zu Phase C, i bekommt eigenen PR. Konflikt 3 gelöst.
    - (d) #329/#330: ein Konzept, je eine eigene Spec pro Issue (wie in der Dateiliste von Plan I). Markiert "zur Bestätigung im Review".
    - (e) Auto-Close in Phase A (Task 9, Schritt 2b): Regel "Issues nur mit Evidenz-Kommentar schließen" gilt. PR- und Commit-Texte OHNE Closing-Keywords (Closes/Fixes/Resolves), Kommentar zuerst, dann manuell schließen. Gelöst.
    - (f) Neuer Fakt, read-only per gh verifiziert: PR #1218 (`Closes #1190`) ist MERGED (mergeCommit `9aa0e0c0c45b08363a8bf75a88600d863d3e5172`, mergedAt 2026-11-11T06:41:30Z). Issue #1190 ist bereits automatisch CLOSED (closedAt 2026-11-11T06:41:32Z, stateReason COMPLETED, ohne Kommentar). Phase A bekommt einen Check-Task: `gh issue view 1190` am Ausführungstag neu lesen, nach Freigabe der Phase A einen Beleg-Kommentar nachreichen, nie wieder öffnen. Roadmap-Zeile #1190: "PR #1218 gemergt (9aa0e0c0), Issue automatisch geschlossen 2026-11-11T06:41:32Z, Beleg-Kommentar nachreichen". Verbucht als SCHON_GEBAUT (Zähler 24/7).

### Entscheidungen (beantwortet) aus der Konfliktliste

Verschoben aus der Konfliktliste durch 35-38. Status je Punkt; die Nummern 1-11 sind die Konfliktnummern der früheren Liste.

1. **#1141 Platzierung:** erledigt durch Entscheidung 35 (Phase D, nach #1181).
2. **#1210 Rollenbindung:** erledigt durch Entscheidung 38a.
3. **#1086 Umfang:** erledigt durch Entscheidung 38c.
4. **#1085b Flags:** erledigt durch Entscheidung 38b.
5. **Phase I und PR-Schnitt:** erledigt durch Entscheidung 36, ersetzt durch Entscheidung 53 (Doku-PR je Issue, Umsetzung J1, J2, ...).
7. **Basis:** erledigt. Phasenpläne sind auf origin/main `9aa0e0c0` rebased (Auftrag). Zeilenanker bei Ausführung neu messen (Abschnitt 6).
9. **#1209 Split:** erledigt durch Entscheidung 36 (eigener PR nach APPROVED-Spec).
11. **#1189 PR-Vermerk:** erledigt durch Entscheidung 36 (Tasks als Commits im C-PR).
- **#898 Punkt 3:** erledigt durch Entscheidung 37.
- **#329/#330:** erledigt durch Entscheidung 38d (zur Bestätigung im Review).
- **Auto-Close:** erledigt durch Entscheidung 38e.
- **#1190:** erledigt durch Entscheidung 38f.

### Offene Entscheidungen (neu, ungeklaert)

Nicht durch 35-38 gelöst. Keine Annahme getroffen.

6. **Phase D Streams:** Nur Stream A (#1181) und #1141 (Entscheidung 35) sind definiert. Zuschnitt der übrigen D-Streams (1210, 1217, 1172, 1176, 1168, 1169) offen. Teilweise geklärt, nicht vollständig.
8. ~~**#1187:** Status unklar~~ erledigt durch Entscheidung 49 (nachziehen, erster Block in Phase E).

Hinweis: Konfliktpunkt 6 bleibt offen (auch nach 39-57); 8 ist durch Entscheidung 49 erledigt. Die Konfliktnummern 9 und 11 existieren in dieser Datei nicht als eigene Punkte; sie sind oben nach Inhalt zugeordnet.

## 7c. Entscheidungsliste Teil 3 (vom User beantwortet, Entscheidungen 39-53)

Quelle: Auftrag an den Planner (verbindlich, 39-53), Wortlaut übernommen. "Weicht von Empfehlung ab" heißt: Der User hat nicht die erste Option des Planners gewählt.

39. **#547-Follow-up (Phase A, A-Q1)**
    - Antwort: Alle fünf offenen Guide-Punkte (`docs/guides/cross-harness-dev-isolation.md:176-199`, auch 4 Branch-Purge und 5 per-harness vs. zentrale config) ins Follow-up-Issue aufnehmen.
    - Folge für Plan: Phase A. Ersetzt die "3 Restpunkte" aus Entscheidung 20; Issue-Entwurf als Datei mit fünf Punkten.

40. **#1180 (C U1)**
    - Antwort: Self-contain: Kernlimits inline in die Regel, Verweise auf `docs/concepts/` entfallen, keine Docs-URL-Variable.
    - Folge für Plan: Phase C.

41. **#1182 (C U2)**
    - Antwort: WARN + Sektion in der Gate-Karte auslassen, kein Reject-Pfad; Option 3 nicht geplant.
    - Folge für Plan: Phase C.

42. **#1195 (C U3)**
    - Antwort: `SYNC_BACKUP_MAX_TOTAL_PER_DIR = 30`; bei Überschreitung die ältesten Backups löschen (nur gitignorierte `*.sync-backup-*`).
    - Folge für Plan: Phase C.

43. **#1000 (C U4)**
    - Antwort: Ohne Git-Repo fail-soft: kein Fehler, Prüfung wird übersprungen.
    - Folge für Plan: Phase C. Teilfrage, ob dieses Repo `progress.checkpoint-dir` auf einen getrackten Ort umstellt, ist NICHT entschieden (offen, siehe unten). Beantwortet durch Entscheidung 55 (Abschnitt 7d).

44. **#1142 (C U5)**
    - Antwort: Stale Allowlist bei ungültiger Config unverändert liegen lassen.
    - Folge für Plan: Phase C.

45. **#1086h (C U9)**
    - Antwort: `priority` nur emittieren (Rule-Dict + Overlap-Meldung), kein Verhalten ändern.
    - Folge für Plan: Phase C.

46. **#1086 (C U11)**
    - Antwort: Bleibt OFFEN, bis Punkt f entschieden oder bewusst verworfen ist; nicht nach a-e, g, h, i schließen.
    - Folge für Plan: Phase C. Kein Schließ-Schritt für #1086 im C-Plan.

47. **#1172 (D Offen 1)**
    - Antwort: Permission-Regel für den git-Agenten BAUEN. **Weicht von Empfehlung ab** (Empfehlung: nur dokumentieren).
    - Folge für Plan: Plan D Task 2 bekommt eine Machbarkeits-Task zuerst (Ist eine Provider-Permission im Repo konfigurierbar? Evidenz am Code/Doku; Security Boundary beachten, Spec-Gate), danach bedingte Umsetzung. Der dokumentierte Merge-Pfad (Merge direkt aus dem Main Chat an den git-Agenten) bleibt Fallback.

48. **#1141 (D Offen 5)**
    - Antwort: `--audit-config` zeigt die Unknown-Key-Warnung ebenfalls (zusätzlich zu `--validate`).
    - Folge für Plan: Phase D, #1141-Teil.

49. **#1187 (E U10)**
    - Antwort: NACHZIEHEN. #1187 (nach User-Freigabe wieder öffnen, nicht eigenmächtig) wird erster Block in Phase E.
    - Begründung: APPROVED Plan #1186 nennt es als Voraussetzung 2; Code `PROJECT_CONTEXT_INJECTED` und Szenarien 95-98 fehlen auf origin/main.
    - Folge für Plan: Phase E = 6 Issues, Gesamtzahl 90 (89 + #1187). Block 2 von E und damit F sind entsperrt, sobald der #1187-Block drin ist. Konflikt 8 gelöst.

50. **#1198 (E U8)**
    - Antwort: Single-Brace-Lint prüft AUCH `rules/`. **Weicht von Empfehlung ab** (Empfehlung: nein).
    - Folge für Plan: Scope `agents/`, `commands/`, `rules/`; Test mit Fixture, die belegt, dass Beispielcode in Regeln keinen Fehlalarm auslöst bzw. wie maskiert wird.

51. **#1201 (F-offen-1)**
    - Antwort: GitHub-Projektion = `bug` (Issue-Kriterium), nicht `type/bug`.
    - Folge für Plan: Der APPROVED Referenzplan `docs/plans/2026-11-09-issue-label-taxonomy-plan.md` (K-7, F-1) widerspricht; Abweichung ist hier festgehalten. Änderung am Referenzplan braucht erneute User-Freigabe (Referenzplan NICHT ändern). Plan F Task 2 (Projektion) bleibt bis dahin gesperrt.

52. **PR-Regel gesperrte/spec-gesteuerte Tasks (G-O2, O-H4, O-H8)**
    - Antwort: Phasen-PR enthält nur derzeit ausführbare Tasks; gesperrte/spec-gesteuerte Tasks laufen in einem Nachfolge-PR derselben Phase (max. 2 PRs je Phase).
    - Folge für Plan: Ausnahme vom strikten "ein PR je Phase" (zusätzlich zu #1086i und #1209); #1014-Folgepläne fallen darunter. Abschnitte 3 und 4 angepasst.

53. **Phase I Schnitt**
    - Antwort: Doku-PR je Issue (Concept, dann Spec, Freigabe-Gate), Umsetzung später in eigenen Umsetzungsphasen J1, J2, ... je Issue mit eigenem Plan und PR (Ausnahme nur für Phase I).
    - Folge für Plan: Entscheidung 36 (Phase I = ein PR) ist damit ersetzt. Phase-I-Zähler bleibt 17. Abschnitte 3, 4 und 5 angepasst.

### Beantwortete offene Fragen (Zuordnung)

A-Q1 -> 39; C U1 -> 40; C U2 -> 41; C U3 -> 42; C U4 -> 43 (ohne Teilfrage checkpoint-dir); C U5 -> 44; C U9 -> 45; C U11 -> 46; D Offen 1 -> 47; D Offen 5 -> 48; E U10 -> 49; E U8 -> 50; F-offen-1 -> 51; G-O2, O-H4, O-H8 -> 52; Phase-I-Schnitt -> 53.

### Weiterhin offen (keine Annahme getroffen)

Stand nach 54-57 (Abschnitt 7d); beantwortete Punkte bleiben zur Nachvollziehbarkeit mit Verweis stehen.

- G-O1, G-O3 (gilt: Kostenschätzung + ausdrückliches Ja).
- O-H2 (erst Task-19-Messung).
- O-H5: beantwortet (Entscheidung 54). O-H6: beantwortet (Entscheidung 56).
- O-H7: beantwortet, G vor H (Entscheidung 56).
- C-1086i-U1 (bedingt auf Messung).
- E U1-U4, U7: beantwortet (Entscheidung 56). E U5/U6 offen (#1209-Spec).
- E: Zuordnung der Szenarien 95-98.
- H: Gate nicht APPROVED zum H2-Schnitt.
- F Task 0b.
- #1187 wieder öffnen (User-Aktion).
- C Task 6: Details über Entscheidung 56 hinaus.
- Phase I: #339 OQ-12/R2; #329/#330 Details (Baseline-Freeze, Rolle der Metrik); #1004 `max_concurrent_agents`/Graph-Format; #957 MVP-Set. Gemeinsame Concepts: beantwortet (Entscheidung 56).
- Konflikt 6: Zuschnitt der übrigen D-Streams (folgt aus 19/35/52).
- #1000 Teilfrage (getrackter Ort für `progress.checkpoint-dir`): beantwortet, nein (Entscheidung 55).
- #1195 bei >30 Quellen: beantwortet (Entscheidung 56). #1086i Entscheidung 18 vs. 52: beantwortet (Entscheidung 56). F vor E-Kern: beantwortet, nein (Entscheidung 56). GitLab-Projektion #1201: beantwortet (Entscheidung 57).

## 7d. Entscheidungsliste Teil 4 (vom User beantwortet, Entscheidungen 54-57)

Quelle: Auftrag an den Planner (verbindlich, 54-57), Wortlaut übernommen.

54. **REQ-Format (O-H5, #1167, Plan H; #339, Plan I)**
    - Antwort: REQ-Format STRIKT ein Bereich `REQ-<BEREICH>-<NN>`, keine mehrteiligen Bereiche.
    - Folge für Plan: Plan H und Plan I. #339 (`REQ-L2-AT-018`) passt sich bei seiner Neufreigabe (Entscheidung 30) an.

55. **#1000 checkpoint-dir dieses Repos (Plan C, Task 13 Step 4)**
    - Antwort: agent-meta selbst behält den Default `.meta-viz/` (gitignoriert), KEINE Umstellung auf getrackten Ort.
    - Folge für Plan: Phase C. Die Warnung `progress.checkpoint-dir-ignored` wird für dieses Repo per Config unterdrückt bzw. dokumentiert hingenommen; der gewählte Weg ist im Plan C zu belegen. Erledigt die offene Teilfrage aus Entscheidung 43.

56. **Defaults übernommen**
    - Antwort:
      - O-H6: F-OC2 nur Befund, Allow-Liste erst nach G-N4-Evidenz.
      - O-H7: G vor H mergen.
      - E U1: zwei Flags `_MODE_FILES`/`_MODE_INLINE`.
      - E U2: Wert `files`, Issue-Text anpassen.
      - E U3: Suffix-Match.
      - E U4: Default true, kein Eintrag in `_FALSE_DEFAULT_CONDITIONALS`.
      - E U7: Doku `docs/api/pal-variables.md`.
      - #1195 bei >30 Quellen: neuestes Backup je Quelle bleibt, dann älteste löschen; mit Entscheidung 42 abgleichen.
      - #1086i als Nachfolge-PR nach dem letzten Phase-C-PR (löst Entscheidung 18 vs. 52).
      - F startet NICHT vor E-Kern (Kette).
      - Phase I: gemeinsame Concepts (#329/#330, #676/#1106) gehören zum Doku-PR des früheren Issues.
    - Folge für Plan: Phasen C, E, F, G, H, I; Abschnitte 3 und 4 angepasst (#1086i, G vor H, F nach E-Kern). E U5/U6 bleiben für die #1209-Spec offen.

57. **#1201 GitLab-Projektion**
    - Antwort: `type::bug` (scoped label; Namespace-Trenner über Host-Config-Key, kein Host-Literal im Code); GitHub = `bug` (Entscheidung 51).
    - Folge für Plan: Wirkung wie 51: Referenzplan-Änderung braucht Freigabe des Users, Task 2 in Plan F bleibt bis dahin gesperrt.

### Beantwortete offene Fragen (Zuordnung, Teil 4)

O-H5 -> 54; #1000 Teilfrage checkpoint-dir -> 55; O-H6, O-H7, E U1-U4, E U7, #1195 >30 Quellen, #1086i 18 vs. 52, F vor E-Kern, Phase-I gemeinsame Concepts -> 56; GitLab-Wert #1201 -> 57.

### Weiterhin offen nach Teil 4 (keine Annahme getroffen)

- G-O1, G-O3 (gilt: Kostenschätzung + ausdrückliches Ja).
- O-H2 (erst Task-19-Messung).
- C-1086i-U1 (bedingt auf Messung).
- E U5/U6 (#1209-Spec).
- Phase I: #339 OQ-12/R2; #329/#330 Details; #1004 `max_concurrent_agents`/Graph-Format; #957 MVP-Set.
- D-Stream-Schnitt (Konflikt 6, folgt aus 19/35/52).
- Übrige Punkte aus 7c: E Szenario-Zuordnung 95-98; H Gate nicht APPROVED zum H2-Schnitt; F Task 0b; #1187 wieder öffnen (User-Aktion); C Task 6 Details über 56 hinaus.

---

## 8. Nächste Schritte

- [x] Freigabe der Roadmap durch den User (erledigt, 2026-11-11)
- [x] Entscheidungen 17-34 eingearbeitet (Abschnitt 7b, Teil 2)
- [x] Entscheidungen 35-38 eingearbeitet (Abschnitt 7b, Teil 3); Konflikte 1-5, 7, 9, 11 erledigt
- [x] Entscheidungen 39-53 eingearbeitet (Abschnitt 7c); Konflikt 8 erledigt (49)
- [x] Entscheidungen 54-57 eingearbeitet (Abschnitt 7d)
- [x] Basis-Rebase auf origin/main `9aa0e0c0` (inkl. #1218) erledigt; Zeilenanker bei Ausführung neu messen
- Offen: Zuschnitt der übrigen D-Streams (Konflikt 6); weitere offene Fragen siehe Abschnitt 7d "Weiterhin offen nach Teil 4"
- #1187: User-Freigabe zum Wiederöffnen einholen, dann erster Block in Phase E (Entscheidung 49)
- Plan D Task 2: Machbarkeits-Task Provider-Permission für den git-Agenten zuerst (Entscheidung 47)
- #1201: erneute User-Freigabe zum Referenzplan Label-Taxonomie nötig, Plan F Task 2 bis dahin gesperrt (Entscheidungen 51, 57; GitLab `type::bug`)
- Phase A: Check-Task #1190 (`gh issue view 1190`, Beleg-Kommentar nach Freigabe); Auto-Close-Regel 38e
- Phase D: #1141 nach #1181 als letzter Teil; #1141-Spec braucht APPROVED
- #1209: eigene Spec, eigener PR nach APPROVED
- Phasenpläne: PR-Regel 52 (Nachfolge-PR für gesperrte Tasks) und Phase-I-Schnitt 53 (Doku-PR je Issue, J1, J2, ...) übernehmen
- #898: Vorbedingung Claude-5.x-IDs im models.dev-Payload prüfen (Task blockiert bei Negativbefund)
- Phasenplan A im Plan-Template schreiben (inkl. #946-Tabelle; #547-Folge-Issue-Entwurf als Datei mit allen fünf Guide-Punkten, Entscheidung 39; #1007-Evidenz)
- Spec-Revision #957 (Q1-Q5) in Phase I, danach User-Freigabe
- Phasenpläne: Vorgabe "kein Co-Authored-By selbst setzen" korrigieren (Entscheidung 25)
- Freshness-Check-Skript (`check_plan_refs.py`) prüfen und gegen origin/main laufen lassen
- Hook-API-Prüfung (`ask`-Permission, Rolle im Payload) vor den Specs zu #1217/#1210
- Phasenpläne B-H im Plan-Template (#1086i und #969 mit eigenem Plan)
- Mini-Spec #1000 (gegen Issue-Text prüfen)
- Concepts/Specs für Phase I (#877+#820 gemeinsam)
- Review der Phasenpläne

## Self-Review

- Summe der Phasen = 11+13+11+8+6+6+7+11+17 = 90 (A 11, B 13, C 11, D 8, E 6, F 6, G 7, H 11, I 17); nach Entscheidung 35: D 8, F 6; nach Entscheidung 49: E 6 (+#1187). Zähler ECHT_OFFEN 57 / TEILWEISE 24 / SCHON_GEBAUT 7 / DOPPELT 1 = 89 (#1190 nach 38f SCHON_GEBAUT); #1187 nicht im Sweep, separat.
- Jede Nummer in genau einer Phase; Querverweise sind als solche markiert. #1141 nur in D (geprüft), nicht mehr in C oder F.
- Alle 57 Entscheidungen eingearbeitet (1-16 in Abschnitt 7, 17-34 in 7b, 35-38 in 7b Teil 3, 39-53 in 7c, 54-57 in 7d); Abweichungen von der Empfehlung markiert (4, 6, 7, 9, 10, 11, 13, 17, 24, 31, 32 Q1+Q5, 33, 47, 50); 35-38 ohne Empfehlungsvergleich, daher ohne Markierung.
- Konflikte: 1, 2, 3, 4, 5, 7, 9, 11 erledigt (35-38); 8 erledigt (49); offen bleibt 6 (Zuschnitt D-Streams).
- PR-Schnitt: ein PR pro Phase; Ausnahmen #1086i (18, 56: Nachfolge-PR nach dem letzten Phase-C-PR), #1209 (36), Nachfolge-PR für gesperrte/spec-gesteuerte Tasks, max. 2 je Phase (52), Phase I Doku-PR je Issue plus J1, J2, ... (53).
- Phase A schließt #885 nicht; #946-Löschung nur nach Tabellenfreigabe, ohne Umgehung des Guards.
- Status: APPROVED (User, 2026-11-11), keine Umsetzung, keine Issue-Änderung.
