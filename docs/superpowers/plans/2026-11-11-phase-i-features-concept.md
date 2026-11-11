# Phase I Konzept-Fahrplan (Features/RFC)

> Status: DRAFT
> Revision: Entscheidungen 54 (#339 passt sich an strikt `REQ-<BEREICH>-<NN>` an) und 56 (gemeinsame Concepts im Doku-PR des früheren Issues) eingearbeitet.
> Basis: `origin/main 9aa0e0c0` (Rebase auf 9aa0e0c0 erfolgt; Anker am 2026-11-11 re-gemessen, Abweichungen siehe »Frische-Check-Referenzen«) | Roadmap-Phase I (Welle 5, `docs/superpowers/plans/2026-11-10-backlog-roadmap.md`) | 17 Issues | Entscheidungen 17-38 und 39-53 (Roadmap §7c; für I wirksam: 53) eingearbeitet (Abschnitt »Entscheidungen (beantwortet)«)
> Dies ist KEIN Umsetzungsplan, sondern ein Konzept-Fahrplan: je Issue Concept -> Spec -> Approval-Gate -> Umsetzungsplan.

**Goal:** Reihenfolge, Entscheidungsbedarf und Abhängigkeiten für die 17 Phase-I-Issues festlegen (329, 330, 339, 548, 676, 679, 681, 783, 820+877, 832, 896, 957, 958, 1004, 1106, 1113). #898, #317 (Phase B) und #1000 (Phase C) sind per Entscheidung 16 vorgezogen und hier NICHT enthalten. Lieferung: je Issue ein Doku-PR (Concept, dann Spec, dann Freigabe-Gate; Entscheidung 53).
**Architecture:** Je Issue eine Stufenfolge. Stufe 1 Concept (docs/concepts), Stufe 2 Spec (docs/specs, `Status: APPROVED` nötig, M/L/XL), Stufe 3 Approval-Gate (User), Stufe 4 Umsetzungsplan im Plan-Template, aber NICHT in Phase I: die Umsetzung läuft später in eigenen Umsetzungsphasen J1, J2, ... je Issue, jede mit eigenem Plan und PR (Entscheidung 53). Phase I liefert je Issue einen Doku-PR mit den Stufen 1-3 (ein Commit je Artefakt); Entscheidung 36 (Phase I = ein PR) ist durch 53 ersetzt. Keine Umsetzung in diesem Dokument.
**Tech Stack:** Markdown/YAML (Concepts, Specs); spätere Umsetzung Python 3.9+ (stdlib, PyYAML-Ausnahme), pytest.
**Spec:** keine (Spec-Gates je Issue, siehe »Fahrplan je Issue«)
**Bestehende Specs/Pläne:** #339 (Spec `APPROVED`, aber User-Re-Approval als erstes Gate, Entscheidung 30), #957 (DRAFT, Revision in Phase I, danach User-Freigabe, Entscheidung 32), #896 (DRAFT-Plan plus eigene Spec, Entscheidung 31), #1113 (Spec als Teil des Umsetzungsplans, Entscheidung 15).

`pipeline_stages`-Frontmatter entfällt: kein Plan für eine `plan-driven`-Pipeline.

## Global Constraints

- Entscheidungen 1-53 der Roadmap §7/§7b/§7c sind bindend (hier relevant: 7, 9, 14, 15, 16, 17, 19, 30-35, 38d/38e, 53; 36 durch 53 ersetzt; Details im Abschnitt »Entscheidungen (beantwortet)«).
- Keine Umsetzung, kein Code, keine Issue-/PR-Änderung durch dieses Dokument.
- M/L/XL: Umsetzungsplan erst gegen Spec mit `Status: APPROVED`.
- Spätere Umsetzung: Python 3.9-kompatibel, stdlib + PyYAML, provider-agnostisch über Config-Keys/Capability-Flags (kein `if provider == ...`), englische Conventional-Commits <=72 Zeichen, keine Worktree-Isolation, Tests `python3 -m pytest <file>::<test>`, `python3 scripts/sync.py --validate`.
- Phase I startet erst nach Wellen 1-4 (Roadmap §5); ein offener Phasen-PR gleichzeitig außer bei disjunkten Dateien. PR-Schnitt Phase I: ein Doku-PR je Issue (Entscheidung 53, Ausnahme vom "ein PR pro Phase" aus Entscheidung 17 nur für Phase I; ersetzt Entscheidung 36), siehe »Doku-PR-Blöcke je Issue«. Umsetzung je Issue in einer eigenen Phase J1, J2, ... mit eigenem Plan und PR; die J-Pläne existieren noch nicht und sind nicht Teil dieses Plans. Phase-I-Zähler bleibt 17.
- Zeilenanker veralten; vor jeder Stufe Freshness-Check (`scripts/check_plan_refs.py` existiert in origin/main `9aa0e0c0` NICHT; nackte `:NNNN`-Anker prüft der Checker ohnehin nicht, daher von Hand per `git show origin/main:<pfad> | grep -n`).
- Issues werden nur mit Beleg-Kommentar geschlossen (Entscheidung 38e); PR- und Commit-Texte ohne Closing-Keywords (Closes/Fixes/Resolves).

## File Structure

Nur Namen; angelegt erst in der jeweiligen Stufe (Pfade relativ zu W = `/home/hermes/repos/agent-meta/.tmp/wt-phase-plans`).

Concepts (`W/docs/concepts/`):
- Create: `se-governance-layer-329-330.md` (ein gemeinsames Concept für #329 und #330, Entscheidung 34 / I-N1; zur Bestätigung im Review, Entscheidung 38d)
- Create: `meta-agent-manager-rfc-548.md`
- Create: `hacs-best-practice-676-1106.md` (gemeinsam, Entscheidung 34 / I-N2)
- Create: `web-best-practices-preset-679.md`
- Create: `subagent-liveness-681.md` (klein, evtl. direkt S-Doku)
- Create: `merge-policy-783.md`
- Create: `domain-clusters-and-family-layer-820-877.md` (Entscheidung 7, XL)
- Create: `config-overlay-local-832.md`
- Create: `project-roles-958.md`
- Create: `planner-parallel-phase-model-1004.md`
- Create: `ask-user-tool-contract-1113.md` NICHT nötig (Entscheidung 15: Spec ist Teil des Umsetzungsplans)

Specs (`W/docs/specs/`, Datumspräfix bei Anlage):
- Create: `<datum>-se-baseline-cr-spec.md`, `<datum>-se-metrics-spec.md` (329/330; je Issue eine eigene Spec, Entscheidung 38d, zur Bestätigung im Review)
- Create: `<datum>-meta-agent-manager-spec.md` (548, je Teil B/C/D)
- Create: `<datum>-hacs-best-practice-spec.md` (676; #1106 hat eigene Teilspecs, I-N2 "separate specs")
- Create: `<datum>-web-best-practices-preset-spec.md` (679)
- Create: `<datum>-merge-policy-spec.md` (783)
- Create: `<datum>-domain-clusters-family-layer-spec.md` (820+877)
- Create: `<datum>-config-overlay-local-spec.md` (832)
- Create: `<datum>-project-roles-spec.md` (958)
- Create: `<datum>-planner-parallelism-spec.md` (1004, intern Teile A-F)
- Create: `<datum>-hacs-migration-a-c-spec.md`, `-d-spec.md`, `-e-spec.md`, `-f-spec.md` (1106, Teilspecs, Entscheidung 14)
- Modify: `2026-10-11-pr-templates-spec.md` (957, DRAFT -> Freigabe)
- Modify: `2026-10-07-339-se-housekeeper-standardization.md` nur falls Rest-Arbeit neu geschnitten wird

Umsetzungsplan #1113: ein Dokument `W/docs/superpowers/plans/<datum>-ask-user-tool-contract-1113.md` mit eingebettetem Spec-Abschnitt und Provider-Matrix.

## Vorgehensmodell (gilt für alle 17)

| Stufe | Artefakt | Gate |
|---|---|---|
| 1 | Concept (S-Issues: entfällt, direkt Spec/Plan) | Reviewer-OK |
| 2 | Spec mit Ist-Verifikation im Code | `Status: APPROVED` durch User (kein Self-Approve) |
| 3 | Approval-Gate | User-Freigabe, dann Plan |
| 4 | Umsetzungsplan (Template, TDD), ein Commit je Task: NICHT Phase I, sondern eigene Phase J1, J2, ... je Issue mit eigenem Plan und PR (Entscheidung 53) | CI grün, Squash-Merge |

**PR-Schnitt (Entscheidungen 53, 15):** Phase I liefert je Issue einen Doku-PR (Concept, dann Spec, dann Freigabe-Gate), ein Commit je Artefakt. Entscheidung 36 (Phase I = genau EIN PR; im I-Review so eingetragen) ist durch Entscheidung 53 ersetzt. Die Umsetzung jedes Issues läuft später in einer eigenen Umsetzungsphase J1, J2, ... mit eigenem Plan und PR (Ausnahme vom "ein PR pro Phase" nur für Phase I). Die J-Pläne existieren noch nicht und sind nicht Teil dieses Plans. #1113 bringt seinen Spec-Abschnitt im Umsetzungsplan mit (Entscheidung 15); dieser Plan ist das Artefakt seines Doku-PR, die Umsetzung läuft in seiner J-Phase.

## Doku-PR-Blöcke je Issue (Entscheidung 53)

Ein Block = ein Doku-PR; Commits je Artefakt in der Reihenfolge Concept -> Spec -> Freigabe (`Status: APPROVED` durch User, kein Self-Approve). Commit-Betreffe englisch, Conventional Commits, <= 72 Zeichen, ohne Closing-Keywords (Entscheidung 38e). Reihenfolge der Blöcke: »Gesamtreihenfolge«. Nach dem Freigabe-Commit endet der Block; der Umsetzungsplan entsteht in der J-Phase des Issues.

| Block | Issue(s) | Commit 1 (Concept) | Commit 2 (Spec) | Commit 3 (Gate) |
|---|---|---|---|---|
| I-896 | #896 | entfällt (DRAFT-Plan vorhanden) | eigene Spec (Entscheidung 31) | Spec APPROVED + DRAFT-Plan in User-Freigabe |
| I-339 | #339 | entfällt (Spec APPROVED durch Reviewer) | Revision nur falls Rest-Arbeit neu geschnitten wird (P1) | User-Re-Approval (Entscheidung 30, erstes Gate) |
| I-681 | #681 | entfällt (S-M) | S-M-Spec bzw. direkter Plan (I-N7) | User-Freigabe |
| I-832 | #832 | `config-overlay-local-832.md` | `<datum>-config-overlay-local-spec.md` | User-Freigabe (I-N9) |
| I-783 | #783 | `merge-policy-783.md` | `<datum>-merge-policy-spec.md` | User-Freigabe (I-N8) |
| I-1004 | #1004 | `planner-parallel-phase-model-1004.md` | `<datum>-planner-parallelism-spec.md` (Teile A-F) | User-Freigabe |
| I-1113 | #1113 | entfällt (Entscheidung 15) | Umsetzungsplan mit Spec-Abschnitt `<datum>-ask-user-tool-contract-1113.md` | Spec-Abschnitt APPROVED (I-N15) |
| I-676 | #676 | `hacs-best-practice-676-1106.md` (gemeinsam, I-N2; im Doku-PR von #676, Entscheidung 56) | `<datum>-hacs-best-practice-spec.md` | User-Freigabe |
| I-1106 | #1106 | gemeinsames Concept (siehe I-676) | Teilspecs A+C, D, E, F (je ein Commit) | User-Freigabe (I-N5) |
| I-679 | #679 | `web-best-practices-preset-679.md` | `<datum>-web-best-practices-preset-spec.md` | User-Freigabe (I-N6) |
| I-957 | #957 | entfällt (Spec vorhanden) | Revision `2026-10-11-pr-templates-spec.md` (Entscheidung 32, P3) | User-Freigabe |
| I-958 | #958 | `project-roles-958.md` | `<datum>-project-roles-spec.md` | User-Freigabe (I-N10) |
| I-329 | #329 | `se-governance-layer-329-330.md` (gemeinsam, I-N1; im Doku-PR von #329, Entscheidung 56) | `<datum>-se-baseline-cr-spec.md` | User-Freigabe |
| I-330 | #330 | gemeinsames Concept (siehe I-329) | `<datum>-se-metrics-spec.md` | User-Freigabe |
| I-820-877 | #820 + #877 | `domain-clusters-and-family-layer-820-877.md` (Entscheidung 7) | `<datum>-domain-clusters-family-layer-spec.md` (Teile 820, 877) | User-Freigabe (I-N11) |
| I-548 | #548 | kein Concept für den RFC (I-N4); Themenzerlegung P5 als Vorschlag | entfällt | User-Freigabe der Kandidatenliste |

16 Blöcke für 17 Issues (#820 + #877 ein Block, Entscheidung 7). Gemeinsame Concepts (#329/#330, #676/#1106) liegen im Doku-PR des in »Gesamtreihenfolge« früheren Issues (Entscheidung 56).

**Risiken:** viele kleine Doku-PRs (16) mit eigener Review-/Freigabe-Latenz; Rebase-Konflikte bei gemeinsamen Dateien (`docs/specs/`-Querverweise, gemeinsame Concepts); ein Gate ohne Freigabe blockiert nur seinen Block und dessen J-Phase, nicht die übrigen Blöcke; Folge-Blöcke mit Abhängigkeit (z.B. #783 nach #832) warten auf den Merge des Vorgänger-Doku-PR.

## Fahrplan je Issue

Aufwandsklasse nach spec-plan-Gate (S/M/L/XL). Existenz-Aussagen "verifiziert" = in W gelesen/gegrept; sonst als "unverifiziert" markiert.

### Gruppe 1: SE-Kaskade (329, 330, 339)

**#339 (M, Rest-Arbeit)**
- Artefakte: Concept liegt NICHT mehr unter `docs/concepts/se-cascade-optimization-339.md`, sondern archiviert `W/docs/concepts/archive/2026-06-se-cascade-optimization-339.md` (Status dort "Konzept-Entwurf v1.2"). Spec `W/docs/specs/2026-10-07-339-se-housekeeper-standardization.md` hat Frontmatter `status: APPROVED` (approved 2026-10-07, by concept-reviewer), Review-Datei vorhanden, ADR-/Frontmatter-Prüflogik HK-1..HK-5 laut Spec §0 bereits in `scripts/lib/consistency/se_cascade.py`, CLI `sync.py --validate-se`. Auch `W/docs/architecture/07-se-cascade.md`.
- Abweichung zur Roadmap: Roadmap nennt Concept unter `docs/concepts/se-cascade-optimization-339.md`; existiert dort nicht (archiviert). "Concept-Stufe" entfällt, Spec ist schon APPROVED.
- Reihenfolge: ZUERST, aber als erstes Gate: User-Re-Approval der Spec (Entscheidung 30). Vor dieser Freigabe keine weitere Planung für #339; "APPROVED durch concept-reviewer" ist keine User-Freigabe.
- Entscheidungen (beantwortet): 30 (User-Re-Approval nötig, vor weiterer Planung). Rest-Arbeit-Umfang nach Spec §5 gegen heutigen Code: Prüf-Task P1. Spec §10 (Zeile 293-301) enthält zwei offene User-Punkte (OQ-12 `sub_components`-Schematiefe; R2 Wrapper-Agent bauen oder `--validate-se` in CI genügt), die mit der Re-Approval zu beantworten sind.
- REQ-Format (Entscheidung 54): strikt ein Bereich `REQ-<BEREICH>-<NN>`, keine mehrteiligen Bereiche. Spec/Concept #339 (`REQ-L2-AT-018`) passt sich bei seiner Neufreigabe (Entscheidung 30) an dieses Format an; der #1167-Validator (Phase H) lehnt `REQ-L2-AT-018` ab.
- Abhängigkeiten: keine auf A-H. Berührt `agents/1-generic/se-*.md`, damit gleiche Dateien wie 329/330 (sequentiell).
- Aufwand: M (laut Spec §10 Größen-Korrektur).

**#329 (L, Design) und #330 (L, Design)**
- Artefakte: nur Issue-Text (Concept-Platzhalter "Do NOT implement yet"); keine Concept-/Spec-Datei in W gefunden (Glob docs/concepts, docs/specs).
- Reihenfolge: nach #339 (gemeinsame se-*-Templates und Frontmatter-Schema aus #339 sind Voraussetzung für Baseline-Marker und Metriken). #329 vor #330 (Volatility-Index in #330 braucht CR-Daten aus #329).
- Abhängigkeiten: #339; Phase C (Schema/Config-Änderungen); #1141 (Schema-Warnung für neue Keys) liegt in Phase D, nach #1181 (Entscheidung 35; Kette #1187 -> #1186 -> #1188 -> #1181 -> #1141); Phase H (#1167 REQ-ID-Format).
- Entscheidungen (beantwortet): 34 (I-N1: ein gemeinsames Concept `se-governance-layer-329-330.md`); 38d (je Issue eine eigene Spec, zur Bestätigung im Review). **Offen (ungeklärt):** Baseline-Freeze-Konfiguration in `project.yaml` ja/nein; neue Rolle für Metriken oder Erweiterung bestehender se-Agenten; Interaktion mit `requirements`- und `release`-Agent.
- Aufwand: L je (Design, neue Layer).

### Gruppe 2: RFC und Plattform-/Preset-Inhalte (548, 676, 1106, 679, 681)

**#548 (XL, RFC)**
- Artefakte: nur Issue (RFC mit Abschnitten A-D, Basis #540, #547). Kein Concept/Spec in W gefunden.
- Reihenfolge: zuletzt in der Gruppe; zuerst RFC in Teile zerlegen (B Erweiterungen, C, D), jeder Teil bekommt eigenes Concept. Teil B1 (evaluation-gate) überschneidet sich mit #969/`eval_gate.py` (Phase H), B2 (drift-guard) mit `branch-guard.md`.
- Entscheidungen (beantwortet): 34 (I-N4: #548 nur als Themenquelle; jeder akzeptierte Teil bekommt eigenes Issue/Concept, kein Concept für den RFC als Ganzes). Offen: welche Teile B/C/D werden Issues, welche verworfen (Ergebnis des Themenzerlegers, nicht vorab entschieden).
- Abhängigkeiten: #547 (Phase A, Schließkandidat), #540, Phase H (#969), Phase D (Guards).
- Aufwand: XL (RFC, nicht als ein Teil planbar).

**#676 und #1106 (HACS, gemeinsame Datei `rules/2-platform/hacs-integration-development.md`, in W vorhanden)**
- #676 (M-L): Issue mit 8 Lücken (IQS, brand assets, runtime_data, Entity-Naming, pytest-HA-Harness, Lint, HACS-Publish, Repairs). Externe HA-/HACS-Aussagen unverifiziert (Roadmap §6), Quellen-URLs nicht geprüft. Kein Concept/Spec in W gefunden. Plattform-Configs in W: `platform-configs/hacs.defaults.yaml`, `homeassistant.defaults.yaml`, `sharkord.defaults.yaml`.
- #1106 (L, Entscheidung 14): Aufteilung A+C, D, E, F, abgestimmt mit #1102 (closed, Commit `23893133`). Teil B laut Issue Delta zu #1102; Roadmap nennt offen A, D, E, F; Issue-Tabelle trennt B (Delta) separat, daher B vor Spec gegen heutige Regeldatei prüfen (I-N5, Settlement durch Spec mit User-Freigabe).
- Reihenfolge: Concept #676 (Faktenprüfung der HA-Aussagen zuerst), dann Spec #1106 Teil A+C, dann D, E, F als Teilspecs. #676-Punkt 3 (runtime_data statt hass.data) und #1106 A berühren dieselben Regelabschnitte, daher koordiniert in einem Concept `hacs-best-practice-676-1106.md`, aber getrennte Specs, Umsetzung sequentiell (gleiche Datei; je Teil ein Commit).
- Entscheidungen (beantwortet): 34 (I-N2: ein Concept `hacs-best-practice-676-1106.md`, getrennte Specs; `.tmp/decisions-part2.md:22` sagt nur "separate specs", nicht "PRs"); I-N5 (Teil B) durch Spec mit User-Freigabe. Faktenprüfung der HA-/HACS-Aussagen: Prüf-Task P4 (Routing-Frage, keine User-Entscheidung).
- Abhängigkeiten: Phase E/F nicht; Phase B/C nicht inhaltlich. #877 (HACS-Familie "ha-gauge") nutzt die Plattform, aber unabhängig.
- Aufwand: #676 M, #1106 L (vier Teilspecs).

**#679 (M, Design/Config)**
- Artefakte: nur Issue; in W kein `web-best-practices` (Grep über config/scripts/agents/rules/platform-configs/pr-templates ohne Treffer, Brace-Glob eventuell unzuverlässig, siehe "Nicht verifiziert"); `platform-configs/` hat kein Web-Preset.
- Reihenfolge: nach #676 (gleiches Muster Plattform-Preset mit Variablen, Lernkurve), vor #957 (PR-Templates mit `{{platform.<p>.<key>}}` brauchen Plattform-Variablenmodell).
- Entscheidungen: I-N6 (Preset-Schnitt, Aktualitätsregel für DSGVO/WCAG, juristische Aussagen "keine Rechtsberatung") durch Spec mit User-Freigabe entschieden (Vorschlag: ein Preset mit drei Variablenblöcken).
- Abhängigkeiten: Phase C (Config-Schema); #1141 liegt in Phase D, nach #1181 (Entscheidung 35), neue Preset-Keys ins Schema daher erst danach; Phase E (#1186 Artefaktorte, falls Preset Doku ablegt).
- Aufwand: M.

**#681 (S-M, Doku/Guidance)**
- Artefakte: nur Issue. Ziel ist Skill `subagent-driven-development` (Harness-Skill, nicht im Repo verifiziert) oder framework-eigene Orchestrator-Regeln.
- Reihenfolge: früh und klein; kein Concept nötig, direkt S-Spec/Plan. Inhaltlich eng mit #1004 Teil E und Phase D #1176 (Orchestrator beendet Turn bei laufenden Workern); als Querverweis abstimmen.
- Entscheidungen: I-N7 (Ablageort der Liveness-Guidance, Schwellwert 90 min fest oder konfigurierbar) durch Spec mit User-Freigabe entschieden.
- Abhängigkeiten: Phase D (#1176) vor Umsetzung, sonst Doppelarbeit in `orchestrator.md`.
- Aufwand: S-M.

### Gruppe 3: Governance/Config/Architektur (783, 832, 958, 820+877)

**#783 (M-L, Config + Guard)**
- Artefakte: nur Issue. Grep nach `merge-policy|auto_merge|merge_gate` in config/scripts/agents/rules ohne Treffer (bestätigt Issue-Aussage "existiert nicht", mit Vorbehalt Brace-Glob).
- Reihenfolge: nach Phase D (Guard-Pfad, #1210 Rollenbindung per Harness-Feld, #1172 Merge-Muster dokumentieren) und nach #832 (Overlay), weil `git.merge-policy` pro Projekt/Provider-Override Config-Precedence braucht.
- Entscheidungen: I-N8 (Schlüsselname `git.merge-policy` vs `merge_gate`, Angebot von `auto`, Verhältnis zu #1172) durch Spec mit User-Freigabe entschieden.
- Abhängigkeiten: Phase D (`orchestrator-guard`), Phase C (Schema), #832.
- Aufwand: L (Schema, Guard, Prompt-Rendering, Admin-UI).

**#832 (M, Config-Overlay)**
- Artefakte: nur Issue. `scripts/lib/config.py` hat `def load_config` bei Zeile 332 (Re-Messung 2026-11-11 gegen 9aa0e0c0, vorher 331; Issue nennt `:221`, veraltet, Abweichung zur Roadmap/Issue); Funktion ist "single funnel".
- Reihenfolge: früh in Phase I, vor #783 und #958 (beide brauchen definierte Config-Quellen). Läuft frühestens nach Phase C (Config-Dateien `config.py`, #1142 gleiche Dateien; #1141 in Phase D, nach #1181, Entscheidung 35).
- Entscheidungen: I-N9 (Deep-Merge-Regeln für Listen, `null`/Lösch-Semantik, Credentials-Schutz für `.local`, Doctor-Anzeige, `.gitignore`-Eintrag über `gitignore.py`) durch Spec mit User-Freigabe entschieden.
- Abhängigkeiten: Phase C (insb. #1142, #1085c `gitignore.py`); #1141 in Phase D, nach #1181 (Entscheidung 35).
- Aufwand: M (Ist-Doc sagt M; Querwirkung auf alle Config-Consumer eher L-Rand).

**#958 (L)**
- Artefakte: nur Issue; `scripts/lib/config.py:2381` `variables["PROJECT_SPECIFIC_AGENTS"] = ""` (Re-Messung 2026-11-11 gegen 9aa0e0c0, vorher :2339; Kommentar Zeile 2379 "placeholder for future ..."; Issue nennt `~1694-1714`, veraltet). Context-Profiles-Spec `W/docs/specs/2026-10-11-context-profiles-spec.md` vorhanden (Q16 zurückgestellt); Abhängigkeit IC-17/IC-18 (Active-Set-Contract) im Code nicht geprüft.
- Reihenfolge: nach #832 und nach der `context.py`-Aufteilung (Phase C Plan `2026-11-11-phase-c-1086i-context-split.md`), weil Active-Set/Agent-Tabelle in `context.py` liegen.
- Entscheidungen: I-N10 (Quellen `.meta-config/agents/` und `project-roles:`, Kollisionsregel mit Framework-Rollen, Doctor-Check-Umfang) durch Spec mit User-Freigabe entschieden.
- Abhängigkeiten: Phase C (1086i), #832, Context-Profiles-Spec IC-17/IC-18 (Status der Umsetzung ungeprüft).
- Aufwand: L.

**#820 + #877 gemeinsam (XL, Entscheidung 7)**
- Artefakte: nur Issues; kein Concept. #820 nennt 12 Fundstellen mit `glob("*.md")` (Tabelle im Issue); `git grep -c 'glob("\*\.md")' origin/main -- scripts` zeigt 29 Treffer in 17 Dateien (`config_audit.py` 4, `crossrefs.py` 3, `admin-server.py` 2, `consistency-check.py` 2, `lib/commands.py` 2, `rules.py` 2, `lib/frontmatter.py` 2, `standalone.py` 2, `se_cascade.py` 2, je 1: `context.py`, `recovery.py`, `bootstrap.py`, `context_budget.py`, `consistency/docs.py`, `consistency/frontmatter.py`, `consistency/commands.py`, `_migrations/2026-09-08-inject-auto-commit-block.py`). Abweichung zur Issue-Tabelle: mehr Stellen, einige nicht in `1-generic`-Kontext (Einzelprüfung im Concept). `hermes_export.py` im Grep nicht gelistet (anderes Muster, Prüfung offen).
- Reihenfolge: letzte große Position (XL), erst nach #832, #958, #1141-Schema (Phase D, nach #1181, Entscheidung 35); Layer-Modell (`2.5-subplatform`/`3.5-family` vs. `.meta-config family:`) ist Architekturentscheidung mit Wirkung auf Template-Discovery, Migration und Provider-Matrix.
- Entscheidungen (beantwortet): 7 (ein gemeinsames Concept für #820+#877). I-N11 (Reihenfolge 820 vor 877, Name/Position der Familien-Schicht, Quelle und Offline-/Pinning-Verhalten, Eindeutigkeit von Rollennamen, `based-on:`-Regex, Migrationspfad) durch Spec mit User-Freigabe entschieden.
- Abhängigkeiten: Phase C (`context.py`-Split 1086i, Config-Schema), #832, #958 (Active-Set). `docs/plans/2026-10-06-bugfix-wave-plan.md:449` setzt #877 NICHT voraus, sondern führt es als "möglicher Duplikat zu #820" (Triage-Tabelle, Empfehlung Zeile 452: Duplikat-Abgleich); durch Entscheidung 7 (Zusammenführung) erledigt.
- Aufwand: XL; Concept in Teilen, Spec in zwei Teilen (820, 877), je Teil ein Commit.

### Gruppe 4: Admin-UI, PR-Templates (896, 957)

**#896 (M)**
- Artefakte: Plan `W/docs/plans/2026-10-07-admin-ui-network-and-manager-plan.md`, Status "Entwurf (DRAFT, wartet auf Nutzer-Freigabe; NICHT self-approved)" (Zeile 11). #897: `gh issue view 897` am 2026-11-11 = CLOSED (Commit `81b913c` existiert). Der Plan selbst nennt Merge-Status PR #913 "laut Orchestrator gemergt", nicht live verifiziert (Zeile 59; Prüf-Task P2). Admin-Server-Code: Bind-Host-Origin-Kommentar `scripts/admin-server.py:981-982` (vorher `:978`, dort steht der Docstring "Raises SecurityError").
- Abweichung zur Roadmap: Roadmap sagt "hängt an #897"; #897 ist CLOSED, Abhängigkeit aufgelöst.
- Reihenfolge: ZUERST in Phase I (nur Freigabe des bestehenden DRAFT-Plans nötig, kleinste Distanz zur Umsetzung). Plan vor Freigabe gegen heutigen Code (Phase B #1173/#898 berühren `admin-server.py`/`admin-ui.html`) neu prüfen.
- Entscheidungen (beantwortet): 31 (BEIDE Dienste netzweit konfigurierbar: eigene Option je Dienst, Viz-Dashboard 8765 und MCP 9090, mit sicherem Default; eigene Spec; DRAFT-Plan geht danach in die User-Freigabe). Abweichung von der Empfehlung (dokumentieren statt ändern) ist entschieden.
- Abhängigkeiten: Phase B (`admin-server.py`, `admin-ui.html`, #1173, #898, #317 Viz-Dashboard), #897.
- Aufwand: M.

**#957 (L)**
- Artefakte: Spec `W/docs/specs/2026-10-11-pr-templates-spec.md`, Status DRAFT (Zeile 11, "Approval-Marker `Status: APPROVED` ..." fehlt); `spec-id SPEC-PR-TEMPLATES-2026-10-11` laut Issue, 19 AK, IC-01..IC-11, offene Fragen. Im Repo existiert kein `pr-templates/`-Verzeichnis (Glob `{pr-templates,platform-configs}/*` listet nur `platform-configs`). Grep nach `pull_request_template` ohne Treffer in config/scripts/agents/rules/.
- Reihenfolge: nach #679 und Phase F (#1188 Label-Taxonomie, gleiche Host-/`GIT_PLATFORM`-Pfadlogik, PR-Label-Vorschläge) und Phase E (#1186 Artefaktorte-Matrix: wohin PR-Templates und `.meta-config/pr-templates/` gehören). Spec zuerst auf Konsistenz mit #1186/#1188 prüfen und neu datieren.
- Entscheidungen (beantwortet, Entscheidung 32; Spec `W/docs/specs/2026-10-11-pr-templates-spec.md`, Abschnitt 7): Spec bleibt DRAFT, wird in Phase I mit diesen Antworten revidiert und danach dem User zur Freigabe vorgelegt.
  - Q1: eigener Index für PR-Templates, nicht `generated-file-hashes.json` (Abweichung von der Empfehlung).
  - Q2: Default-Template UND benannte Templates.
  - Q3: Templates in Englisch, mit `DOCS_LANGUAGE`-Hinweis.
  - Q4: Reihenfolge in `platforms:` plus Warnung.
  - Q5: Release-Template gekoppelt an `release.distribution` von Beginn an (größerer MVP-Umfang, Abweichung von der Empfehlung).
- **Offen (ungeklärt):** Feinschnitt des MVP-Sets (Vorschlag `default/bugfix/release/docs`); Manager-Rückmeldung an Framework (Zusammenhang #548).
- Abhängigkeiten: Phase E (#1186), Phase F (#1188), Phase C (Schema-Key `pr-templates`), #679.
- Aufwand: L.

### Gruppe 5: Planner/Orchestrator (1004, 1113)

**#1004 (L, Entscheidung 9: ungeteilt, Teile E und F bleiben im Issue)**
- Artefakte: nur Issue. `W/agents/1-generic/planner.md` Frontmatter `version: "1.6.1"`; `parallel_with`/`conflicts_with` im Planner-Template nicht vorhanden (Grep ohne Treffer, verifiziert). `W/agents/1-generic/orchestrator.md:258` Abschnitt "## 7. BARRIER protocol" (Roadmap nannte `:240-276`, Abschnitt jetzt 258-277, `## 8. Reflection loop` ab 278; Anker veraltet).
- Reihenfolge: Spec gliedert intern A (Parallelitätsmodell), B (Phasen/PR-Grenzen), C (Review-Befunde einarbeiten), D (Live-Review-Phase), E (Orchestrator-Abschluss), F (Arbeitsteilung/Bash für planner). E ist inhaltlich Phase D (#1176) und #681; daher E-Teil erst nach #1176-Umsetzung, A-D und F früher. Spec-Reihenfolge der Teile: A, B, C, D, F, E. Teil E (wait vs resume) bleibt im Issue, ungeteilt (Entscheidung 9).
- Entscheidungen (beantwortet): 9 (ungeteilt, Teil E bleibt im Issue); 33 (F: read-only Bash-Allowlist für die planner-Rolle; Berechtigungsänderung; Security-Boundary-Prüfung (Convention vs Security) in der Spec; nur eng gefasste Liste read-only Befehle). **Offen (ungeklärt):** `max_concurrent_agents`-Quelle (Host-Ressourcen, Config-Key?); Format des Dependency-Graphen (Mermaid vs ASCII). Dieser Fahrplan nutzt selbst die Plan-Template-Konvention; Planner-Template-Änderung muss mit `plan-driven`-Pipeline-Stages und dem verpflichtenden `pipeline_stages`-Frontmatter kompatibel bleiben.
- Abhängigkeiten: Phase D (#1176 Orchestrator beendet Turn; #1168 git-Trailer), #681; sync-Auswirkung: Template-Version-Bump `planner.md`, `--validate`.
- Aufwand: L (ein Spec mit sechs Teilen, ein Commit je Teil A-D, E, F im Doku-PR; Umsetzung in eigener J-Phase, Entscheidung 53).

**#1113 (L, Entscheidung 15)**
- Artefakte: nur Issue. `agents/1-generic/orchestrator.md:22` Fallback-Zeile mit `ask-user={{UNKNOWN_FALLBACK_ASK_USER}}` (verifiziert), `:304` "Fallback: ask-user via `main_chat` → meta-feedback → main-chat" (verifiziert), `:105` Hinweis "kein natives `route_intent`-Tool registriert, Route aus Routing-Regeln ableiten" (gelesen; kein allgemeiner Guardrail zu erfundenen Tool-Aufrufen). Issue nennt Zeilen `:290-295` (Abweichung: jetzt `:304`). `config/provider-capabilities.yaml:57-66` Kommentarblock zu `route_intent_tool` (verifiziert), Werte `route_intent_tool: false` je Provider ab `:124`; `config/provider-tools.yaml` nicht neu gelesen. Capability-Flag `ask_user_tool` existiert noch nicht (`git grep ask_user_tool origin/main`: nur Roadmap-Zeile 79).
- Reihenfolge: ein einziges Dokument Umsetzungsplan mit eingebettetem Spec-Abschnitt (Entscheidung 15). Gate: Spec-Abschnitt braucht `Status: APPROVED`, vorher keine Umsetzungstask ausführbar. Zuerst Provider-Matrix erheben (welche Provider haben eine Ask-User-Funktion; Roadmap §6: ungeprüft), dann Vertrag (Capability-Flag + Fallback-Text), dann Umsetzung nach dem `route_intent_tool`-Muster.
- Entscheidungen: I-N15 (Vertragsname provider-gemappt, Capability-Key-Name, Verhalten bei fehlendem Tool) durch Spec-Abschnitt mit User-Freigabe entschieden (Entscheidung 15 für die Einbettung). Provider ohne Tool dürfen nicht stillschweigend `ask-user=true` melden.
- Abhängigkeiten: Phase D (#1176, gleiche Datei `orchestrator.md`), Phase G (Provider-Capability-Tabellen, #1171 Benennung `provider-tools.yaml`), Phase C (Schema/Capability-Validierung); #1004 Teil E (gleiche Datei, sequentiell).
- Aufwand: L.

## Gesamtreihenfolge (Vorschlag)

| Rang | Issue | Grund |
|---|---|---|
| 1 | #896 | Plan liegt als DRAFT vor; eigene Spec (31), dann Freigabe/Refresh |
| 2 | #339 | Spec APPROVED (Reviewer); erstes Gate: User-Re-Approval (30), dann Rest-Arbeit |
| 3 | #681 | klein, Guidance, nach Phase D #1176 |
| 4 | #832 | Basis für #783, #958, #820/877; nach Phase C |
| 5 | #783 | nach #832 und Phase D |
| 6 | #1004 (A-D, F) dann E | Spec je Teil; E nach #1176 |
| 7 | #1113 | nach Phase D/G und #1004-E (gleiche `orchestrator.md`) |
| 8 | #676 + #1106 | gemeinsames Concept, Faktenprüfung zuerst |
| 9 | #679, #957 | Preset-Muster vor PR-Templates; #957 nach Phase E/F |
| 10 | #958 | nach #832, 1086i |
| 11 | #329, #330 | nach #339 |
| 12 | #820 + #877 | XL, zuletzt, nach #832/#958 |
| 13 | #548 | RFC, nur Themenquelle (34), letzte Position |

Parallel-Möglichkeit (Dateilisten disjunkt, im jeweiligen Plan zu prüfen): {#896} || {#339, #329, #330} || {#676, #1106, #679}. Sequentiell wegen gleicher Datei: #1004-E, #1113, #681 (`orchestrator.md`); #676 und #1106 (`hacs-integration-development.md`); #832, #958, #820/#877 (`config.py`/`context.py`).

## Abhängigkeiten auf Phasenpläne (existierende Dateien in W/docs/superpowers/plans/)

- Phase A: `2026-11-11-phase-a-hygiene.md` (#547 für #548).
- Phase B: `2026-11-11-phase-b-small-bugs.md` (`admin-server.py`/`admin-ui.html` für #896).
- Phase C: `2026-11-11-phase-c-sync-config.md`, `2026-11-11-phase-c-1086i-context-split.md` (Config-Schema, `context.py`-Split; für #832, #958, #820/877, #783, #679, #957).
- Phase D: `2026-11-11-phase-d-guards-hooks.md` (Guard, `orchestrator.md`; für #783, #1004-E, #1113, #681).
- Phase E: `2026-11-11-phase-e-artifact-locations.md` (für #957, #679).
- Phase F: `2026-11-11-phase-f-label-taxonomy.md` (für #957).
- Phase G: `2026-11-11-phase-g-provider.md` (liegt inzwischen im Branch `docs/phase-plans`; enthält #1171, Zeile 16; für #1113).
- Phase H: `2026-11-11-phase-h-context-eval.md` (#548-B1 ~ #969; #1167 für #329/#330).

## Entscheidungen (beantwortet)

Quelle: nutzerbeantwortete Roadmap-Entscheidungen 1-38 (bindend; 1-16 in Roadmap §7, Quelltexte: `W/.tmp/decisions-part2.md` und `W/.tmp/decisions-part3.md`). Ursprüngliche Plan-IDs (N1-N15) in Klammern.

- **7** (#820+#877, N11-Struktur): ein gemeinsames Concept, XL.
- **15** (#1113): Spec-Abschnitt ist Teil des Umsetzungsplans, kein eigenes Concept.
- **17** (PR-Schnitt): ein PR pro Phase. Für Phase I durch Entscheidung 53 ausgenommen (Doku-PR je Issue).
- **19** (Kette #1187 -> #1186 -> #1188 -> #1181 -> #1141): Kette bleibt gültig; die Platzierung von #1141 ist durch Entscheidung 35 überholt (siehe unten). #1187 ist kein Teil dieses Fahrplans; Prüfung als Check-Task im E/F-Plan.
- **35** (#1141): liegt in Phase D, NACH #1181 (Kette #1187 -> #1186 -> #1188 -> #1181 -> #1141). Abhängigkeiten von #329/#330, #679 und #832 auf #1141 entsprechend angepasst. Ersetzt Entscheidung 19 für #1141.
- **36** (PR-Schnitt): Phase I = genau ein PR. **Ersetzt durch Entscheidung 53.**
- **54** (REQ-Format): strikt ein Bereich `REQ-<BEREICH>-<NN>`; #339 passt sich bei seiner Neufreigabe (30) an.
- **56** (Defaults, Phase I): gemeinsame Concepts (#329/#330, #676/#1106) gehören zum Doku-PR des früheren Issues.
- **53** (Phase-I-Schnitt): Doku-PR je Issue (Concept, dann Spec, Freigabe-Gate); Umsetzung später in eigenen Umsetzungsphasen J1, J2, ... je Issue mit eigenem Plan und PR; Ausnahme nur für Phase I; Phase-I-Zähler bleibt 17. Beantwortet die frühere offene Frage "In welcher Phase/welchem PR läuft die spätere Umsetzung der 17 Items": in J1, J2, ... je Issue. Die J-Pläne existieren noch nicht und sind nicht Teil dieses Plans.
- **38** (Auflösungen ohne neue Frage), relevant für Phase I:
  - 38d (#329/#330): ein Concept, je Issue eine eigene Spec (Dateiliste oben), zur Bestätigung im Review.
  - 38e (Schließen von Issues): nur mit Beleg-Kommentar schließen; PR- und Commit-Texte ohne Closing-Keywords. Gilt als Global Constraint für alle späteren Phasen.
  - 38a-c und 38f betreffen andere Phasenpläne (#1210, #1085b, #1086, #1190) und sind hier nicht relevant.
- **30** (#339, N3): User-Re-Approval der Spec ist das ERSTE Gate für #339, vor weiterer Planung.
- **31** (#896, N12): BEIDE Dienste netzweit konfigurierbar (Viz-Dashboard 8765, MCP 9090), je eigene Option mit sicherem Default; eigene Spec; DRAFT-Plan danach in die User-Freigabe.
- **32** (#957, N13): Q1 eigener Index für PR-Templates (nicht `generated-file-hashes.json`); Q2 Default UND benannte Templates; Q3 Templates Englisch mit `DOCS_LANGUAGE`-Hinweis; Q4 Reihenfolge in `platforms:` plus Warnung; Q5 Release-Template gekoppelt an `release.distribution` von Beginn an. Spec bleibt DRAFT, Revision in Phase I, danach User-Freigabe.
- **33** (#1004 F, N14): read-only Bash-Allowlist für die `planner`-Rolle; Berechtigungsänderung; Security-Boundary-Prüfung (Convention vs Security) in der Spec; nur eine eng gefasste Liste read-only Befehle. Teil E (wait vs resume) bleibt im Issue (Entscheidung 9).
- **34** (Plan-Defaults):
  - I-N1 (#329/#330): ein Concept `se-governance-layer-329-330.md`.
  - I-N2 (#676/#1106): ein Concept `hacs-best-practice-676-1106.md`, getrennte Specs.
  - I-N4 (#548): nur Themenquelle, kein Concept für den RFC als Ganzes.
  - I-N5..I-N11 und I-N15: je durch die genannte Spec mit User-Freigabe entschieden:

| ID | Issue | Settlement durch Spec (Datum-Präfix bei Anlage) |
|---|---|---|
| I-N5 | #1106 Teil B | `<datum>-hacs-migration-a-c-spec.md` bzw. Teilspec mit Teil B (Delta zu #1102) |
| I-N6 | #679 | `<datum>-web-best-practices-preset-spec.md` |
| I-N7 | #681 | S-M-Spec bzw. direkter Plan (Dateiname bei Anlage) |
| I-N8 | #783 | `<datum>-merge-policy-spec.md` |
| I-N9 | #832 | `<datum>-config-overlay-local-spec.md` |
| I-N10 | #958 | `<datum>-project-roles-spec.md` |
| I-N11 | #820+#877 | `<datum>-domain-clusters-family-layer-spec.md` |
| I-N15 | #1113 | Spec-Abschnitt im Umsetzungsplan `<datum>-ask-user-tool-contract-1113.md` |

Bereits durch Entscheidungen 17-19, 23, 27 entschieden: D-neu-2, F-neu-2, E-N1, F-neu-1, B-N3, G-N2 (nicht Teil dieses Plans).

## Prüf-Tasks (Verifikation, keine User-Entscheidung)

Laufen vor dem jeweiligen Gate; Ergebnis als Abschnitt im Concept/der Spec mit Datei:Zeile-Belegen. Read-only.

- P1 #339: Rest-Arbeit nach Spec §5 (`docs/specs/2026-10-07-339-se-housekeeper-standardization.md:224`) gegen heutigen Code prüfen: `git grep -n 'check_cell_structure' origin/main -- scripts` (Spec §2 Zeile 96 markiert sie als neu; Stand `9aa0e0c0`: keine Treffer, also mindestens R1 offen); Ergebnis vor der Re-Approval (Entscheidung 30) vorlegen.
- P2 #896: Merge von PR #913 prüfen: `gh pr view 913 --json state,mergeCommit`; DRAFT-Plan gegen Phase-B-Änderungen an `admin-server.py`/`admin-ui.html` refreshen.
- P3 #957: Spec gegen #1186 (`docs/specs/2026-11-09-artifact-locations-matrix-spec.md`) und #1188 (`docs/specs/2026-11-09-issue-label-taxonomy-spec.md`) abgleichen.
- P4 #676/#1106: HA-/HACS-Aussagen per Web-Recherche mit Quelle und Datum verifizieren (Rolle: Orchestrator-Routing).
- P5 #548: RFC in Teile B/C/D zerlegen; Kandidatenliste (Issue ja/verwerfen) als Vorschlag zur User-Freigabe.
- P6 #820: `hermes_export.py`-Fundstellen (anderes Muster als `glob("*.md")`) zählen.
- P7 #958: Umsetzungsstand IC-17/IC-18 der Context-Profiles-Spec im Code prüfen.
- P8 #1113: Provider-Matrix (Ask-User-Funktion je Provider) mit Quelle erheben.

## Offene Entscheidungen (neu, ungeklaert)

Nicht durch 1-53 gedeckt. Bewusst offen, keine Schätzung.

- #339: Spec §10 OQ-12 (`sub_components`-Schematiefe) und R2 (Wrapper-Agent bauen oder `--validate-se` in CI) — bei der Re-Approval (Entscheidung 30).
- #329/#330: Baseline-Freeze-Konfiguration in `project.yaml` ja/nein; neue Rolle für Metriken oder Erweiterung bestehender se-Agenten; Interaktion mit `requirements`- und `release`-Agent. (Die Struktur "ein Concept, je Issue eine Spec" ist durch 38d geklärt; diese Inhalte nicht.)
- #1004: Quelle von `max_concurrent_agents` (Host-Ressourcen oder Config-Key); Format des Dependency-Graphen (Mermaid vs ASCII).
- #957: Feinschnitt des MVP-Sets (`default/bugfix/release/docs`); Manager-Rückmeldung an das Framework (Zusammenhang #548).
- (Beantwortet, Entscheidung 56: gemeinsame Concepts #329/#330 und #676/#1106 gehören zum Doku-PR des früheren Issues.)
- (Beantwortet, Entscheidung 53: Umsetzung der 17 Items in eigenen Phasen J1, J2, ... je Issue mit eigenem Plan und PR.)

## Frische-Check-Referenzen

- #329, #330, #339, #548, #676, #679, #681, #783, #820, #832, #877, #896, #897, #957, #958, #1004, #1102, #1106, #1113, #898, #317, #1000, #1176, #1168, #1172, #1186, #1188, #1141, #1142, #1085, #1086, #1167, #969, #540, #547, #1171, #885
- docs/concepts/archive/2026-06-se-cascade-optimization-339.md
- docs/concepts/se-cascade-optimization-339.md (existiert nicht)
- docs/specs/2026-10-07-339-se-housekeeper-standardization.md
- docs/specs/2026-10-11-pr-templates-spec.md
- docs/specs/2026-10-11-context-profiles-spec.md
- docs/specs/2026-11-09-artifact-locations-matrix-spec.md
- docs/specs/2026-11-09-issue-label-taxonomy-spec.md
- docs/plans/2026-10-07-admin-ui-network-and-manager-plan.md
- docs/architecture/07-se-cascade.md
- docs/superpowers/plans/2026-11-10-backlog-roadmap.md
- docs/superpowers/plans/2026-11-11-phase-a-hygiene.md
- docs/superpowers/plans/2026-11-11-phase-b-small-bugs.md
- docs/superpowers/plans/2026-11-11-phase-c-sync-config.md
- docs/superpowers/plans/2026-11-11-phase-c-1086i-context-split.md
- docs/superpowers/plans/2026-11-11-phase-d-guards-hooks.md
- docs/superpowers/plans/2026-11-11-phase-e-artifact-locations.md
- docs/superpowers/plans/2026-11-11-phase-f-label-taxonomy.md
- docs/superpowers/plans/2026-11-11-phase-h-context-eval.md
- docs/superpowers/plans/2026-11-11-phase-g-provider.md
- docs/plans/2026-10-06-bugfix-wave-plan.md
- agents/1-generic/planner.md
- agents/1-generic/orchestrator.md
- rules/2-platform/hacs-integration-development.md
- platform-configs/hacs.defaults.yaml
- platform-configs/homeassistant.defaults.yaml
- scripts/lib/config.py
- scripts/lib/config.py::load_config
- scripts/lib/config.py::PROJECT_SPECIFIC_AGENTS
- scripts/lib/consistency/se_cascade.py
- scripts/lib/config_audit.py
- scripts/admin-server.py
- config/provider-capabilities.yaml
- config/provider-tools.yaml
- scripts/check_plan_refs.py (existiert nicht, Glob ohne Treffer)
- origin/main `9aa0e0c0` (Rebase erfolgt; Anker am 2026-11-11 re-gemessen per Read/Grep im Worktree: `orchestrator.md:258` BARRIER bestätigt, `orchestrator.md:22` und `:304` ask-user bestätigt, `planner.md` Version 1.6.1 bestätigt, `config.py` load_config `:331` -> `:332`, `config.py` PROJECT_SPECIFIC_AGENTS `:2339` -> `:2381`)
- `decisions-part2.md` und `decisions-part3.md` (Entscheidungen 17-38, Quelle dieses Dokuments)
- docs/superpowers/plans/2026-11-11-phase-i-features-concept.md (dieses Dokument; Entscheidungen 1-53 eingearbeitet, soweit relevant)

## Nicht verifiziert

- Merge-Status PR #913 (#896-Plan Zeile 59; Prüf-Task P2).
- #339-Spec: Frontmatter (`status: APPROVED`, `size: M`) und §10 gelesen; Rest-Arbeit §5 gegen heutigen Code nur stichprobenhaft (Prüf-Task P1).
- Alle Issues: Texte nur in den ersten 40-60 Zeilen gelesen (#1004 bis AK, #1106 bis Teil B, #1113 bis Vertragstabelle, #548, #676, #679, #681, #783, #832, #820, #877, #957 teilweise); Kommentare bei den meisten nicht gelesen.
- Grep-Negativbefunde (`merge-policy`, `web-best-practices`, `pull_request_template`, `ask_user_tool`) nutzten Brace-Globs; bei fehlerhafter Glob-Auflösung wären Treffer unterdrückt.
- `hermes_export.py`-Fundstellen von #820 nicht neu gezählt (P6); 29 Treffer-Zählung nur nach Muster `glob("*.md")`.
- Existenz/Umsetzung von IC-17/IC-18 (Active-Set) für #958 nicht geprüft (P7).
- Externe HA/HACS-Aussagen (#676, #1106) und Opencode/Provider-Fähigkeiten für #1113 nicht geprüft (P4, P8).
- Inhalte der Phasenpläne A-H nur stichprobenhaft gelesen (Issue-Zuordnung #1085c/#1142 in C, #1176/#1141 in D, #1167/#969 in H, #1171 in G per Grep bestätigt).
- Aufwandsklassen sind Planner-Einschätzung; Aufwandsschätzung per `effort-estimator` steht aus.
- Review 2026-11-11 hat per `git show origin/main:<pfad>` zusätzlich re-gemessen: `admin-server.py:981-982`, `orchestrator.md:105`/`:278`, `provider-capabilities.yaml:57-66`, `bugfix-wave-plan.md:449`, Admin-Plan Zeile 11/59, PR-Templates-Spec Zeile 11, #339-Spec §0/§5/§10. Nicht re-gemessen: `hacs-integration-development.md`, `config/provider-tools.yaml`, `config_audit.py`.
- Auswirkung der Entscheidungen 19/35 auf Roadmap-Wellen (#1141 in Phase D nach #1181, Kette #1188 -> #1181 -> #1141): in diesem Dokument nur als Abhängigkeit vermerkt; Roadmap-Datei nicht geändert.

## Self-Review

- 17 Issues je genau einmal behandelt: 329, 330, 339, 548, 676, 679, 681, 783, 820+877 (zwei Nummern in einem Abschnitt), 832, 896, 957, 958, 1004, 1106, 1113 (17 Nummern; #898, #317, #1000 ausgeschlossen).
- Keine TBD/Platzhalter außer bewusst als "<datum>" in Dateinamen künftiger Artefakte.
- Code-Aussagen mit Beleg (Re-Messung 2026-11-11 gegen 9aa0e0c0): `config.py:332` load_config (vorher 331), `config.py:2381` PROJECT_SPECIFIC_AGENTS (vorher 2339), `planner.md:3` Version 1.6.1 ohne `parallel_with`, `orchestrator.md:22/258/304` (bestätigt). Abweichungen zur Roadmap/Issue dokumentiert (#339-Concept archiviert, #832 `:221` vs `:332`, #1004 BARRIER `:258`, #1113 `:304`, #820 29 statt 12 Treffer, #896-Abhängigkeit #897).
- Mehrere Aussagen als unverifiziert markiert statt behauptet.
- Entscheidungen 17-53 eingearbeitet: 7, 15, 17 (für Phase I durch 53 ausgenommen), 53 (Doku-PR je Issue, J-Phasen; ersetzt 36), 19 (für #1141 durch 35 überholt), 30, 31, 32, 33, 34, 35, 36 (ersetzt durch 53), 38d, 38e (I-N1, I-N2, I-N4, I-N5..I-N11, I-N15 zugeordnet). Nichts geraten.
- Offene User-Punkte nach 1-53: #339 §10 OQ-12/R2, #329/#330 Baseline/Rolle/Interaktion, #1004 `max_concurrent_agents`/Graph-Format, #957 MVP-Set; Zuordnung gemeinsamer Concepts zu Doku-PRs durch 56, #339-REQ-Format durch 54 beantwortet; Umsetzungsphase/PR der Phase-I-Items durch 53 beantwortet. Verifikationen als Prüf-Tasks P1-P8; #897 ist CLOSED (gh, 2026-11-11).
- Konflikt-Check: im Dokument kein offener Widerspruch gefunden. Die Dateiliste (zwei Specs für 329/330) entspricht 38d; keine Konflikt-Notiz zu 38d im Dokument vorhanden.
- Abschnitt "Offene Entscheidungen (neu)" ersetzt durch "Entscheidungen (beantwortet)" und "Offene Entscheidungen (neu, ungeklaert)".
- Abhängigkeiten auf #1141 an Entscheidung 35 angepasst (#329/#330, #679, #832: Phase D, nach #1181).
- Plan-Anker nach Rebase auf `9aa0e0c0` re-gemessen (5 Anker, zwei Abweichungen: load_config :332, PROJECT_SPECIFIC_AGENTS :2381). Übrige Anker siehe »Nicht verifiziert«.
