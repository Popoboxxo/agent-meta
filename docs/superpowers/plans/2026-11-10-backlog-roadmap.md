# Backlog-Roadmap 2026-11-10

> Status: APPROVED (User, 2026-11-11)
> Datum: 2026-11-10 | Entscheidungen eingearbeitet: 2026-11-10/11 | Basis: origin/main `a41745ed` | Branch: `docs/backlog-roadmap`

**Goal:** Die 89 offenen Issues und 3 offenen PRs (#1218, #1145, #1148) in Phasen ordnen, die je ein Branch und ein PR sind.
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
| TEILWEISE | 25 | 25 |
| SCHON_GEBAUT | 6 | 6 |
| DOPPELT | 1 | 1 |
| Summe | 89 | 89 |

Keine Abweichung zu den Auftragszählern.

### Issues

| Nr | Verdikt | Evidenz | Prüfstand |
|---|---|---|---|
| 317 | ECHT_OFFEN | viz-dashboard iframe Live-Test, S-M | Subagent, ungeprüft |
| 329 | TEILWEISE | SE-Baseline/CR-Layer, Design | Subagent, ungeprüft |
| 330 | TEILWEISE | SE-Metriken, Design | Subagent, ungeprüft |
| 339 | TEILWEISE | Concept `docs/concepts/se-cascade-optimization-339.md` existiert | Subagent, ungeprüft |
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
| 896 | ECHT_OFFEN | M; Plan `docs/plans/2026-10-07-admin-ui-network-and-manager-plan.md` DRAFT; hängt an #897 | Subagent, ungeprüft |
| 898 | TEILWEISE | S; Punkt 2 gebaut `admin-server.py:4730`; Punkt 1 Checkboxen offen `admin-ui.html:7699-7705`; Punkt 3 `pricing-overlay.yaml:7,10` alte Modelle | Subagent, ungeprüft |
| 946 | ECHT_OFFEN | Entscheidungsissue; 18 Zweifelsbranches auf origin, 9 Stash-Einträge statt 7, `.tmp/cleanup-archive` weg, `docs/838-spec-revision` nur noch im Stash, lokal z.B. `fix/sync-check-tracked-only 35f591e6` ohne Remote | Subagent, ungeprüft |
| 957 | ECHT_OFFEN | L; Spec `docs/specs/2026-10-11-pr-templates-spec.md` DRAFT | Subagent, ungeprüft |
| 958 | ECHT_OFFEN | L; `config.py:2339` `PROJECT_SPECIFIC_AGENTS=""`; Abhängigkeit #965 closed | Subagent, ungeprüft |
| 960 | ECHT_OFFEN | L; nichts gebaut, Spec zuerst | Subagent, ungeprüft |
| 969 | TEILWEISE | S; #986 `082aa9b1` `eval_gate.py` gebaut; Baseline-Run braucht User-Freigabe; McNemar zurückgestellt | Subagent, ungeprüft |
| 977 | TEILWEISE | Tracker; 963-968, 970-976 closed; nur 969 offen; Phasen 2/3 ohne Issues | Subagent, ungeprüft |
| 1000 | ECHT_OFFEN | M; `progress_paths.py:34-35` | Subagent, ungeprüft |
| 1004 | ECHT_OFFEN | M; planner.md v1.6.1 ohne `parallel_with`/`conflicts_with`; `orchestrator.md:240-276` | Subagent, ungeprüft |
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
| 1190 | TEILWEISE | wartet auf Merge #1218 (PR OPEN, 104 Dateien, CI läuft, test 3.12 Shard 2 FAILURE); ADR 0002, `topology.py`; nach Merge SCHON_GEBAUT, Phase A schließt es | Subagent, ungeprüft (PR-Stand laut Auftrag, nicht von mir geprüft) |
| 1194 | ECHT_OFFEN | S; `context.py:1710`, `opencode_v2_config.py:513` | Subagent, ungeprüft |
| 1195 | ECHT_OFFEN | M; `sync_pipeline.py:946` | Subagent, ungeprüft |
| 1197 | ECHT_OFFEN | S | Subagent, ungeprüft |
| 1198 | ECHT_OFFEN | S, P1; 18 Stellen in 12 SE-Templates | Subagent, ungeprüft |
| 1199 | ECHT_OFFEN | S; `admin-server.py:234` | Subagent, ungeprüft |
| 1200 | ECHT_OFFEN | S | Subagent, ungeprüft |
| 1201 | ECHT_OFFEN | M; `conventions-presets.yaml:56,93,125` | Subagent, ungeprüft |
| 1202 | ECHT_OFFEN | M | Subagent, ungeprüft |
| 1203 | ECHT_OFFEN | S, prospektiv (`--labels` existiert noch nicht) | Subagent, ungeprüft |
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
| #1218 | offen (kein Issue) | `feat/1190`, CI läuft, test 3.12 Shard 2 FAILURE; schließt #1190 | Subagent, ungeprüft (laut Auftrag) |
| #1145 | Duplikat von #1148 | Dependabot pytest-split, ändert nur `tests/requirements.txt` | Subagent, ungeprüft |
| #1148 | Duplikat von #1145 | wie #1145 | Subagent, ungeprüft |

---

## 2. Phasen

| Phase | Thema | Issues | Anzahl |
|---|---|---|---|
| A | Hygiene | 547, 857, 858, 1007, 1116, 1151, 1150, 946, 885, 977, 1190 (+ PRs 1218, 1145, 1148) | 11 |
| B | Kleine Bugs (S) | 1194, 1197, 1205, 1206, 1207, 1213, 1214, 1139, 1170, 1174, 1173, 898, 317 | 13 |
| C | Sync/Config-Robustheit | 1141, 1142, 1085, 1086, 1155, 1195, 1208, 1189, 1182, 1183, 1180, 1000 | 12 |
| D | Guards/Hooks/Commit-Authority | 1181, 1210, 1217, 1172, 1176, 1168, 1169 | 7 |
| E | Artefaktorte | 1186, 1198, 1199, 1200, 1209 | 5 |
| F | Label-Taxonomie | 1188, 1201, 1202, 1203, 1204, 1211 | 6 |
| G | Provider (Gemini/Antigravity/Opencode/Mammouth) | 854, 860, 1160, 1171, 1175, 800, 814 | 7 |
| H | Kontext/Token/Eval | 969, 1161, 1115, 1014, 778, 779, 780, 960, 1167, 1158, 1159 | 11 |
| I | Features/RFC (Concept, dann Spec, dann Approval-Gate) | 329, 330, 339, 548, 676, 679, 681, 783, 820, 832, 877, 896, 957, 958, 1004, 1106, 1113 | 17 |
| Summe | | | 11+13+12+7+5+6+7+11+17 = **89** |

Jede der 89 Nummern steht in genau einer Phase (gegen die Sweep-Liste geprüft, keine fehlende, keine doppelte).

### Auflösungen gegenüber dem Vorschlag

- #1198, #1199, #1200 stehen nur in Phase E (Kinder von #1186), nicht in B. Phase B hängt nicht von ihnen ab.
- #1203 steht nur in Phase F (Kind von #1188, prospektiv, `--labels` existiert noch nicht), nicht in B.
- #1204 steht in F (Vorschlag: F), nicht B.
- #977, #1150, #946, #885, #1190 stehen in A. Die dort genannten Folgeaktionen betreffen Issues anderer Phasen und sind Querverweise, keine Doppelzuordnung:
  - Label `blocked` für #860/#854: Aktion in A, Issues zählen in G.
  - Kommentare zu fertigen Teilen von #1155 (zählt in C), #1158, #1159, #1161 (H), #1160 (G): Aktion in A, Issues zählen dort.
- #1173 stand im Vorschlag nirgends. Zuordnung zu B: kleiner Bug (S), Admin-UI Tier-Preset-Speichern verliert YAML-Kommentare.
- Vorgezogen aus Phase I (Entscheidung 16): #898 (S) und #317 (S-M) nach B, #1000 (Mini-Spec) nach C. Phase I schrumpft von 20 auf 17.
- #977 (Tracker) in A statt H: reiner Tracker-Update, kein Code.
- #885 zählt weiter in A, wird aber dort nicht geschlossen (Entscheidung 13). Schließen ist ein eigener Schritt am Ende der letzten Welle.
- Abweichung vom Vorschlag: keine weitere. Phasenschnitt sonst unverändert.

### Bewusst offen gelassen

| Issue | Grund |
|---|---|
| #860 | extern blockiert (agy SIGILL pclmul), kein Eingriff möglich |
| #854 | Umzug auf Skills erst nach Runtime-Probe (#860), Entscheidung 10 |
| #1211 | verfrüht, blockiert durch #1188 |
| #1203 | prospektiv, `--labels` existiert noch nicht; erst nach #1188-Umsetzung |
| #1209 | wartet auf #1186 |
| #885 | Epic bleibt OFFEN, bis alle Issues dieses Plans erledigt sind (Entscheidung 13); Phase A schließt es nicht, Restpunkte werden nicht einzeln neu angelegt |
| #946 | Löschung erst nach Freigabe der Branch/Stash-Tabelle (Entscheidung 12); destruktive Befehle nie umgangen |
| #1175 | Frage, nicht verifizierbar, Opencode-Quelle ungelesen |
| Phase I (Rest) | erst Concept, dann Spec, dann Freigabe; keine Umsetzung in diesem Plan |
| #969 Baseline-Run | kostenpflichtig: nur nach Kostenschätzung und ausdrücklichem User-Ja (Entscheidung 11) |

### Phase A Detail (Hygiene)

Keine Umsetzung vor Freigabe. Schließen nur mit Evidenz-Kommentar.

- Schließkandidaten: #547 (Evidenz dünn, siehe "Nicht verifiziert"), #857, #858, #1007 (7 Punkte nicht einzeln verglichen), #1116, #1151.
- #1150: DOPPELT von #1186, schließen mit Verweis.
- #1190: erst nach Merge von #1218 schließen. #1218 ist OPEN, 104 Dateien, test 3.12 Shard 2 rot. Phase A wartet darauf.
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

Eine Phase = ein Branch von origin/main = ein PR. Squash-Merge nach grüner CI, kein Admin-Bypass.

| Welle | Phase | Hängt ab von | Parallel zu | Begründung |
|---|---|---|---|---|
| 0 | A | #1218 gemergt (nur für #1190) | restliche A-Aktionen sofort nach Freigabe | CI-Fix pytest-split entlastet alle folgenden PRs; #946-Tabelle zur Freigabe vorlegen |
| 1 | B | A (CI grün) | G-Vorarbeiten nur lesend | kleine Fixes; berührt u.a. `context.py:1710`, `spec_plan.py`, `admin-server.py`/`admin-ui.html` (#1173, #898), viz-dashboard (#317) |
| 2 | C (Teil-PRs) | B (gleiche Dateien `context.py`, `sync_pipeline.py`); #1000 braucht freigegebene Mini-Spec | E | Robustheit vor Feature-Arbeit; #1086i (context.py-Split) eigener Plan und eigener PR, zuletzt in C |
| 2 | E | A | C, falls Dateiliste disjunkt | Spec+Plan APPROVED (#1186) |
| 3 | D | C (`hooks.py`, Guard-Pfade), #1181 braucht freigegebene Spec; Hook-API-Prüfung für `ask` vor der #1217-Spec | F | Entscheidungen 1-2 festgelegt |
| 3 | F | E (Templates/Preset-Dateien), #1188 Spec+Plan APPROVED | D | #1203/#1211 erst nach #1188-Kern |
| 4 | G | A (Labels), B (#1170 vor #854), #1085/#1155-Flag aus C | H | #860 extern blockiert, #854 (Skills) wartet auf Runtime-Probe |
| 4 | H | B, C | G | #969: Schnittstelle auf Per-Testfall-Ergebnisse umbauen, dann McNemar; Baseline-Run nur nach Kostenschätzung und User-Ja |
| 5 | I | je Item: Concept, Spec, Approval-Gate | untereinander | keine Umsetzung ohne `Status: APPROVED`; #877 und #820 gemeinsames Concept |
| 6 | Abschluss | alle Issues dieses Plans erledigt | — | #885 schließen (eigener Schritt) |

Regeln:
- Parallel nur bei disjunkter `Files:`-Liste im jeweiligen Phasenplan. Nicht verifiziert, bis die Phasenpläne existieren.
- Innerhalb einer Phase sequentiell, wenn dieselbe Datei betroffen ist (z.B. #1213/#1214 in `spec_plan.py`).
- Phase I wird in Teil-PRs je Feature geschnitten, nicht als ein PR.
- Der `context.py`-Split (#1086i) läuft zuletzt in C, damit B und die übrigen C-Teile nicht in eine verschobene Datei hineinrebasen.

---

## 4. Querschnittsregeln

- **Migrationsreihenfolge:** A, B, C vor allen Phasen mit Template-/Config-Änderungen (E, F, G). Schema-/Config-Änderungen immer mit Migrationspfad und `--validate`-Lauf. Details in den Phasenplänen.
- **Freshness-Check:** Vor jeder Ausführung `check_plan_refs.py` gegen origin/main laufen lassen. Zeilenanker aus dieser Roadmap stammen von `a41745ed` und veralten. Existenz des Skripts in diesem Repo: nicht verifiziert.
- **Ressourcen:** CI-Last begrenzen (ein offener Phasen-PR gleichzeitig, außer disjunkte Dateien); Python-3.9-Kompatibilität in allen Änderungen (kein `X | Y`-Typsyntax ohne Future-Import, kein `match`); Zeitbudget pro Phase im Phasenplan über `effort-estimator`, hier keine Schätzung.
- **Commit-/PR-Text:** wird als Datei bereitgestellt (z.B. unter `.tmp/`), nicht inline per Shell.
- **Destruktive Git-Befehle:** werden nie umgangen. Blockiert der Guard, liefert der Assistent die fertigen Befehle, der User führt sie per `!` aus (betrifft #946).
- **Issues schließen:** nur nach Freigabe und nur mit Evidenz-Kommentar. Bei Kommaliste "Resolves" schließt nur die erste Nummer automatisch, Rest manuell.
- **Kostenpflichtige Läufe** (#969 Baseline): nur nach Kostenschätzung und ausdrücklichem User-Ja.
- **Kein Worktree-Isolation-Argument** beim Spawnen von Subagenten.

---

## 5. Risiken

| Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|
| Sweep-Evidenz nur von Subagenten, 84 von 89 Zeilen ungeprüft | Falsche Schließung oder Doppelarbeit | Vor jedem Schließen Stichprobe/Hand-Check, Freshness-Check |
| #1218 (104 Dateien) rot und noch offen | Phase A/#1190 blockiert, Merge-Konflikte mit B/C | Merge abwarten, B/C danach von neuem origin/main |
| Dateikonflikte zwischen B, C, E (`context.py`, `admin-server.py`) | Rebase-Aufwand | Wellen sequentiell, Dateilisten je Phasenplan |
| Python-3.9-Jobs scheitern an Abhängigkeitsupdates | CI dauerhaft rot | Marker-Fix in Phase A, nicht verifiziert |
| #1210 Rollenbindung per Harness-Feld (Entscheidung 2) ist Security Boundary | Guard umgehbar, falls Payload-Feld fehlt oder fälschbar | Payload-Feld vor Spec prüfen; Convention-vs-Security-Terminologie beachten |
| Destruktives Gate #1217 über `ask`-Permission: Hook-API-Support unverifiziert (Entscheidung 1) | Plan hinfällig | Hook-API-Prüfung VOR der Spec |
| #1086i `context.py`-Split (3495 Zeilen, L-Refactoring) in derselben Runde | Merge-Konflikte, Regressionen, Scope-Explosion | eigener Plan und PR, zuletzt in C, Tests vor dem Split grün, kein Verhaltenswechsel |
| #877 + #820 zusammengeführt (XL) | Concept zu groß, Verzögerung der übrigen Phase-I-Items | ein gemeinsames Concept, Gate vor Spec, keine Umsetzung vorab |
| #1085b nur opt-in per `--strict`/`--fail-on-p0` (Entscheidung 4) | P0-Befunde unbemerkt, wenn CI das Flag nicht setzt | CI-Workflow muss das Flag selbst setzen, im Phasenplan C als Task |
| #946: Guard blockiert Löschung (exit 2) | Löschung stockt | fertige Befehle liefern, User führt per `!` aus; Stash `docs/838-spec-revision` vorher sichern |
| #969 Interface-Umbau auf Per-Testfall-Ergebnisse (`eval_gate.py:28` bewusst aufgeschoben) | Regression im Eval-Gate, Kosten bei Baseline | Umbau mit Tests, Baseline nur nach Kostenschätzung und User-Ja |
| #1004 bleibt ungeteilt (Teile E und F im Issue) | größerer Zuschnitt, Spec-Umfang wächst | Spec je Teil gliedern, Gate vor Umsetzung |
| #885 offen bis zum Ende | Epic wird vergessen | Welle 6 als eigener Schritt eingeplant |
| Phase I (17 Items) verdrängt Bugfixes | Backlog wächst | erst nach Wellen 1-4, Gate je Item |
| Lösch-/Close-Aktionen auf Basis dünner Evidenz (#547, #1007) | Verlust offener Arbeit | siehe "Nicht verifiziert" |

---

## 6. Nicht verifiziert

- Gerenderte Dateien (`.claude/agents/`, AGENTS.md usw.): nicht neu gerendert oder verglichen.
- CI-Status: nicht geprüft. #1218-Angaben (104 Dateien, test 3.12 Shard 2 FAILURE, CI läuft) stammen aus dem Auftrag.
- Hook-Laufzeitverhalten (Guard, Exit-Codes): nicht ausgeführt. Ob die Hook-API eine `ask`-Permission statt exit 2 unterstützt (Entscheidung 1): nicht verifiziert. Ob das Hook-Payload die Rolle als Feld liefert (Entscheidung 2): nicht verifiziert.
- Messzahlen aus Issue-Texten (z.B. #800, #969, #1169 Python-Spawns): nicht nachgemessen.
- Evidenz für #547: nur ein Subagent.
- Einzelne Punkte von #1007: die 7 "zu bauen"-Punkte nicht einzeln gegen PRs #1012, #1016, #1017, #1018, #1019 verglichen.
- Externe Aussagen in #676 (HACS/HA), Opencode-Verhalten in #1175.
- Alle Zeilenanker (`datei:zeile`) gelten für `a41745ed`; der Anker zu #1173 (`admin-server.py:5089`) stammt aus dem Issue-Text.
- #885: F-09..F-16 und Kinder #932/#936 nicht geprüft.
- Marker-Fix für pytest-split: nicht gegen CI getestet.
- Ob `check_plan_refs.py` existiert und wie es aufgerufen wird.
- #1000: Wortlaut der Optionen A/B/C wurde vom Main Chat nur aus dem Index gelesen, nicht aus dem Issue-Text. Im Concept gegen den Issue-Text gegenprüfen (Entscheidung 8).
- #1085: ob CI-Workflows `--strict`/`--fail-on-p0` bereits setzen oder setzen können.
- `eval_gate.py:28`: Hinweis auf bewusst aufgeschobenes Per-Testfall-Interface aus dem Auftrag, nicht selbst gelesen.
- #946: Stand der 18 Branches und 9 Stash-Einträge nur laut Sweep, nicht neu erhoben.
- #1113: welche Provider eine Ask-User-Funktion tatsächlich bieten, nicht geprüft.

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

---

## 8. Nächste Schritte

- [x] Freigabe der Roadmap durch den User (erledigt, 2026-11-11)
- Phasenplan A im Plan-Template schreiben (inkl. #946-Tabelle)
- Freshness-Check-Skript (`check_plan_refs.py`) prüfen und gegen origin/main laufen lassen
- Hook-API-Prüfung (`ask`-Permission, Rolle im Payload) vor den Specs zu #1217/#1210
- Phasenpläne B-H im Plan-Template (#1086i und #969 mit eigenem Plan)
- Mini-Spec #1000 (gegen Issue-Text prüfen)
- Concepts/Specs für Phase I (#877+#820 gemeinsam)
- Review der Phasenpläne

## Self-Review

- Summe der Phasen = 11+13+12+7+5+6+7+11+17 = 89; Zähler 57/25/6/1 stimmen mit der Tabelle überein.
- Jede Nummer in genau einer Phase; Querverweise sind als solche markiert.
- Alle 16 Entscheidungen eingearbeitet; Abweichungen von der Empfehlung markiert (4, 6, 7, 9, 10, 11, 13); Querverweise auf Entscheidungsnummern gegen Abschnitt 7 geprüft.
- Phase A schließt #885 nicht; #946-Löschung nur nach Tabellenfreigabe, ohne Umgehung des Guards.
- Status: APPROVED (User, 2026-11-11), keine Umsetzung, keine Issue-Änderung.
