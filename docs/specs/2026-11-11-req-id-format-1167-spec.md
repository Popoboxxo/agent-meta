---
spec-id: SPEC-REQ-ID-FORMAT-1167-2026-11-11
title: "REQ-ID-Format (Issue #1167, Phase H Task 19) — Spec"
status: APPROVED
date: 2026-11-22
approval: "Nutzergo 22.11 — Spezifikation auf Basis des freigegebenen Phasenplans 2026-11-11-phase-h-context-eval.md nachgetragen, keine neue Entscheidung"
plan: docs/superpowers/plans/2026-11-11-phase-h-context-eval.md
plan_task: 19
plan_anchors: "Task 19 Z. 410-417; Entscheidung 34/D-H4 Z. 131; Entscheidung 54/O-H5 Z. 132; O-H2 Z. 146; Abweichung Nr. 13 Z. 110"
branch: chore/phase-h-bundle
ist_anchor: "4d3d21f5416bd8f1048e2491bb9ee260bbad2f5c (Re-Messung 2026-11-22; Plan maß bei 9aa0e0c0, Phase-H-Sibling-Specs bei 87564958)"
related_issue: "#1167"
klasse: "M — Validator + Templates/Presets, Formatvereinheitlichung"
gate: "Task 19 → Tasks 20/21"
---

# REQ-ID-Format (Issue #1167, Phase H Task 19) — Spec

> Status: APPROVED (Nutzergo 22.11 — Spezifikation auf Basis des freigegebenen Phasenplans 2026-11-11-phase-h-context-eval.md nachgetragen, keine neue Entscheidung)
> Datum: 2026-11-22 | Ist-Anker: Branch `chore/phase-h-bundle` @ `4d3d21f5416bd8f1048e2491bb9ee260bbad2f5c` (alle file:line-Belege gegen diesen Stand neu gemessen) | Plan: `docs/superpowers/plans/2026-11-11-phase-h-context-eval.md`, Task 19 (Z. 410-417)
> Entscheidungen (vom Plan fixiert, hier nicht neu entschieden): 34 / D-H4 (Z. 131), 54 / O-H5 (Z. 132), 30 (Z. 127), 38e (Z. 129) | Offen: O-H2 (Z. 146) — siehe O-H2-Messung
> Gate: Diese Spec ist das Freigabe-Gate für Task 20/21. Ohne obige `Status: APPROVED`-Zeile sind Tasks 20/21 nicht ausführbar (Plan Task 19, Akzeptanz Z. 416).

## Problem / Ziel / Nicht-Ziele

**Problem.** Das REQ-ID-Format ist im Framework nicht vereinheitlicht. `docs/REQUIREMENTS.md:4` beschreibt zwei Formate (`REQ-xxx` dreistellig *oder* thematisch präfixiert `REQ-CMD-xx`), `agents/1-generic/requirements.md:45-46` beschreibt `REQ-xxx` (three digits) mit Sub-Requirements `REQ-xxx-A`, `agents/1-generic/se-developer.md:31,46` und `se-junior-developer.md:31,46` zeigen das konkrete Beispiel `REQ-047` (ohne Bereichs-Segment). Gleichzeitig ist das REQ-Mandat in mehreren Templates ungegated (z. B. `validator.md:53`, `bug-feature-analyzer.md:42,84,134`), während andere Stellen bereits über `{{#if DOD_REQ_TRACEABILITY}}` laufen (`validator.md:35-41`, `:97`). Issue #1167 verlangt ein einheitliches Format in Templates/Presets und eine Validator-Prüfung.

**Ziel.** Implementierbare Verträge für die Plan-Tasks 20 und 21: ein kanonisches Format `REQ-<AREA>-<NN>` (D-H4), genau ein Bereichs-Segment ohne `-` (Entscheidung 54), eine Scope-Definition, Gating auf `DOD_REQ_TRACEABILITY` (Single Source), Validator-Verhalten (still bei aus, ERROR bei an und fehlerhaft) sowie die Abgrenzung zu #1158 K-01 und #339. Alle Aussagen stammen aus dem freigegebenen Phasenplan; diese Spec trifft keine neue Produktentscheidung. Die Ziffernzahl `N` bleibt gemäß O-H2 bewusst offen und wird hier nur gemessen (siehe O-H2-Messung).

**Nicht-Ziele.**
- Keine Implementierung — dies ist der Spec-Gate; Code, Hooks, andere Specs und Config-Dateien bleiben unberührt (nur diese Spec-Datei wird geschrieben).
- Keine Festlegung von `N` (Ziffernzahl) — O-H2 ist eine offene Entscheidung des Plans; beide Kandidaten werden dokumentiert und an main chat eskaliert (siehe O-H2-Messung und Offene Fragen O1).
- Kein mehrteiliges Bereichs-Segment: `REQ-L2-AT-018` ist ungültig (Entscheidung 54); #339 passt sich bei seiner Neufreigabe an (Entscheidung 30). Keine #339-Planung in Phase H.
- Keine Abnahme von #1158 K-01 (Task 18) — disjunkte Dateimenge; hier nur Abgrenzung.
- Keine Änderung an `docs/REQUIREMENTS.md`, außer falls die umsetzende Task 17 (K-17/K-11) dies ausdrücklich verlangt (Plan File Structure Z. 167).
- Keine provider-spezifischen Namens-Branches; Gating ausschließlich über den bestehenden Config-Key `DOD_REQ_TRACEABILITY` / `dod.req-traceability`.
- Keine Closing-Keywords in Commit-/PR-Texten (Entscheidung 38e, Z. 129); `(#1167)` ist reiner Verweis, #1167 wird in Phase H nicht geschlossen.

## O-H2-Messung (Task 19 Step 1) — Ergebnis und Entscheidungspunkt

Dieser Abschnitt führt die vom Plan geforderte Messung (Z. 146, Z. 413) aus und hält ihr Ergebnis objektiv fest. Es wird **keine** Entscheidung zwischen den beiden Kandidaten getroffen.

### M1 — Inventur der REQ-Stellen (Grep)

Geführt mit dem Ripgrep-basierten Grep-Tool (Äquivalent zu `grep -E 'REQ-ID|REQ-xxx'`; ein `git grep` steht diesem Spec-Worker nicht zur Verfügung). Stand: Branch `chore/phase-h-bundle` @ `4d3d21f`.

| Grep-Ziel (Muster `REQ-ID\|REQ-xxx`) | Treffer | file:line-Belege (Auszug / vollständig wo kurz) |
|---|---|---|
| `agents/1-generic/` | **89 Treffer in 36 Dateien** (Plan: 90 Zeilen/36 Dateien bei `9aa0e0c0` → 1 Treffer weniger, Drift) | u. a. `validator.md:4,38,39,53,97,118,137`; `bug-feature-analyzer.md:42,84,134`; `requirements.md:4,5,36,43,45,46,100`; `se-developer.md:31,46,98,116,136`; `se-junior-developer.md:31,46,97,125,137`; `api-specialist.md:109,147`; `se-requirements.md:36,68,99`; `se-component-requirements.md:69,97,127`; `tester.md:32,40,104,125`; `e2e-tester.md:67,105`; `git.md:136,146`; `junior-developer.md:59,67,114`; `senior-developer.md:37,45,164`; `principal-developer.md:51,78,171`; `se-senior-developer.md:91`; `database-engineer.md:137`; `devops-engineer.md:186`; `refactoring-specialist.md:143`; `ui-ux-designer.md:4,48,64,79`; `orchestrator.md:250,392`; `planner.md:26,113`; `ideation.md:103,177`; `concept-specifier.md:101,131`; `concept-reviewer.md:173`; `concept-architect.md:138`; `product-manager.md:23,127,130`; `risk-based-audit-planner.md:29`; `documenter.md:33`; `developer.md:4,5`; `se-architect.md:63`; `se-critic.md:111`; `se-validator.md:71`; `se-testreviewer.md:166`; `se-integration-and-test-manager.md:29,104,120,231`; `data-engineer.md:150`; `_reference-agent.md:171,174` |
| `config/role-defaults.yaml` | **5 Treffer** | `:179`, `:187`, `:190`, `:200`, `:2691` |
| `config/conventions-presets.yaml` | **1 Treffer** | `:34` (`entry_prefix: "REQ-xxx: "`) |
| `docs/REQUIREMENTS.md` | **1 Treffer** | `:4` (`Format: REQ-xxx (dreistellig) oder thematisch präfixiert (z.B. REQ-CMD-xx).`) |

### M2 — Höchste vergebene Nummer je Bereich (aus `docs/REQUIREMENTS.md`)

Grep-Muster `REQ-[A-Z][A-Z0-9]*-[0-9]+` auf `docs/REQUIREMENTS.md` → **37 vergebene REQ-IDs in 8 Bereichen**. Höchste Nummer je Bereich:

| Bereich | IDs | höchste vergebene Nummer | Ziffern |
|---|---|---|---|
| `CMD` | `REQ-CMD-01` … `REQ-CMD-10` | 10 | 2 |
| `GEN` | `REQ-GEN-01` | 01 | 2 |
| `PROV` | `REQ-PROV-01` | 01 | 2 |
| `SYNC` | `REQ-SYNC-01`, `REQ-SYNC-02` | 02 | 2 |
| `SE` | `REQ-SE-01`…`05`, `10`…`13`, `20`…`22` | 22 | 2 |
| `MOD` | `REQ-MOD-01` … `REQ-MOD-07` | 07 | 2 |
| `ADM` | `REQ-ADM-01` … `REQ-ADM-03` | 03 | 2 |
| `CTX` | `REQ-CTX-01` | 01 | 2 |

**Messwert:** Alle 37 vergebenen IDs in allen 8 Bereichen sind **genau zweistellig**; globales Maximum = 22 (`REQ-SE-22`). Es existiert **keine dreistellig vergebene ID** in `docs/REQUIREMENTS.md`.

### M3 — Dreistellige Vorkommen, die keine vergebenen IDs sind

| Stelle | Inhalt | Einordnung |
|---|---|---|
| `docs/REQUIREMENTS.md:4` | `REQ-xxx` „(dreistellig)" | Formatbeschreibung/Platzhalter (`xxx`), keine vergebene ID — genau die Stelle, die O-H2 (Z. 146) als Begründung für `\d{2,3}` anführt |
| `agents/1-generic/requirements.md:45` | `Format: REQ-xxx (three digits, ascending)` | Formatbeschreibung/Platzhalter |
| `agents/1-generic/requirements.md:46` | `Sub-requirements: REQ-xxx-A, REQ-xxx-B` | Platzhalter für Sub-Requirements |
| `agents/1-generic/se-developer.md:31,46`, `se-junior-developer.md:31,46` | `e.g. REQ-047` | konkretes dreistelliges Beispiel, aber **ohne** Bereichs-Segment → nach D-H4/Entscheidung 54 ohnehin ungültig; gehört zu den Stellen, die #1167 bereinigt |

### M4 — Verdict: AMBIGUOUS → Entscheidungspunkt für main chat

Die Messung (M2) ist objektiv eindeutig (alle vergebenen IDs zweistelig). Die **Regex-Wahl** ist es nicht, weil beide Kandidaten auf konkretem, im Plan benanntem Beleg beruhen:

- **Kandidat A — `\d{2}` (genau 2 Ziffern):** `^REQ-[A-Z][A-Z0-9]*-\d{2}$`. Beleg: D-H4 schreibt wörtlich `<NN>` (Z. 131); alle 37 vergebenen IDs (M2) sind zweistellig; Task-20-Fixture `REQ-CMD-01` ist als gültig gesetzt (Z. 422).
- **Kandidat B — `\d{2,3}` (2 oder 3 Ziffern):** `^REQ-[A-Z][A-Z0-9]*-\d{2,3}$`. Beleg: O-H2 nennt `\d{2,3}` ausdrücklich als Alternative „wegen `REQ-xxx` dreistellig in `docs/REQUIREMENTS.md:4`" (Z. 146); `requirements.md:45` wiederholt „three digits"; `REQ-047` existiert als konkrete dreistellige Form (M3).

Da der Plan O-H2 bewusst offen gelassen hat (Abschnitt „Offene Entscheidungen", Z. 144-146) und Task 20 die „Ziffernzahl O-H2" explizit nicht vorgibt (Z. 422), wird **hier keine Wahl getroffen**. `N` ist Entscheidungspunkt für main chat; beide Optionen sind in Offene Fragen O1 und in IC-1 festgehalten. Die Implementierung von Task 20 darf erst nach Auflösung durch main chat mit der dann festgelegten Konstante erfolgen.

## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)

Alle Anker gegen `chore/phase-h-bundle @ 4d3d21f` neu gemessen (Plan maß bei `9aa0e0c0`; Phase-H-Sibling-Specs bei `87564958`). Python 3.9-kompatibel, provider-agnostisch.

### IC-1 — Regex-Konstante (Plan Z. 412, D-H4 + Entscheidung 54; `N` offen)

- **Form (vom Plan vorgegeben):** `^REQ-[A-Z][A-Z0-9]*-\d{N}$`, angewendet mit `re.fullmatch`.
- **Bereichs-Segment (Entscheidung 54, fix):** `[A-Z][A-Z0-9]*` — genau **ein** Segment, **ohne** `-`. Damit ist `REQ-L2-AT-018` ungültig (mehrteiliger Bereich), `REQ-CMD-01` gültig.
- **`N` (offen, O-H2):** Kandidat A `^REQ-[A-Z][A-Z0-9]*-\d{2}$` oder Kandidat B `^REQ-[A-Z][A-Z0-9]*-\d{2,3}$`. Keine Festlegung in dieser Spec (siehe M4, Offene Fragen O1).
- **Fehlerpfade (unabhängig von `N`):** `REQ-1` (zu wenige Ziffern) → ungültig; beliebige Zeichenketten ohne `REQ-`-Präfix, mit Kleinschreibung im Bereich oder mit `-` im Bereich → ungültig; `re.fullmatch` verhindert Teil Treffer.

### IC-2 — Gating-Quelle (Single Source)

- **Ist:** `scripts/lib/dod.py:345-354` kennt `req-traceability` als DoD-Key (Full-Preset `True`, `:347`); `scripts/lib/config.py:3157` setzt `variables["DOD_REQ_TRACEABILITY"] = "true" if dod_resolved.get("req-traceability", True) else "false"`; `config/dod-presets.yaml:56-57` setzt im Preset `rapid-prototyping` `req-traceability: false`; `scripts/lib/standalone.py:132` defaultet `DOD_REQ_TRACEABILITY` auf `"false"`.
- **Soll:** Der Validator liest den Zustand ausschließlich über `DOD_REQ_TRACEABILITY` / `dod.req-traceability` (Auflösung über `dod.py`/`config.py`). Keine zweite Quelle, kein neuer Config-Key.
- **Fehlerpfade:** Bei `req-traceability: false` (z. B. `rapid-prototyping`) ist der Validator still — keine Findings, kein Exit-Code-Fehler. Bei `true` und fehlerhaftem REQ-ID-Format → ein `Finding` mit `Severity.ERROR` (siehe IC-3).

### IC-3 — `scripts/lib/consistency/req_format.py::check_req_ids` (Task 20, Plan Z. 421)

- **Signatur (vom Plan vorgegeben):** `check_req_ids(agent_meta_root: Path, project_root: Path, config: Optional[dict]) -> List[Finding]`.
- **Muster:** `scripts/lib/consistency/temp_literals.py:559-563` (`check_temp_literals`); `Finding`/`Severity` aus `scripts/lib/consistency/report.py:22-34` (`Severity.ERROR`, `Finding(severity, check, file, message, suggestion="")`).
- **Rückgabe:** leere Liste, wenn `req-traceability` aus; je fehlerhaftem Vorkommen ein `Finding` mit `Severity.ERROR` (Check-Kennung `req-id.format`), wenn an.
- **Registrierung:** in `scripts/lib/cli_commands.py::_handle_validate` (gegen `4d3d21f` bei `:1518`; Plan nannte `:1408`) neben `check_temp_literals` (Registrierung/Import gegen `4d3d21f` bei `:1672-1673`; Plan nannte `:1507`).

### IC-4 — Template-/Preset-Gating (Task 21, Plan Z. 431)

- **Zu ändernde Stellen (gegen `4d3d21f` neu gemessen; Abweichung Nr. 13, Plan Z. 110, als Ausgangspunkt):**
  - `agents/1-generic/validator.md:53` (aktuell ungated: Commit-Format mit `REQ-xxx`); `:38-39` und `:97` sind bereits gegated (`:35-41` bzw. `:97`); `:4` (description) enthält `REQ-ID presence`.
  - `agents/1-generic/bug-feature-analyzer.md:42,84,134` (aktuell ungated).
  - `agents/1-generic/requirements.md:43-46` (REQ-ID-Schema: `REQ-xxx` three digits / `REQ-xxx-A`).
  - `agents/1-generic/se-requirements.md:36,68,99`; `agents/1-generic/se-developer.md:31,46,98,116,136`; `agents/1-generic/se-junior-developer.md:31,46,97,125,137`; `agents/1-generic/api-specialist.md:109,147`.
  - `config/conventions-presets.yaml:34` (`entry_prefix: "REQ-xxx: "`).
  - `config/role-defaults.yaml:179,187,190,200,2691` (REQ-Text; Plan nannte `:2668` und „nicht `:2694`" — gegen `4d3d21f`: `REQ-ID vergeben` bei `:2691`, `:2694` ist die Zeile `dod_flag: req-traceability`).
  - Je betroffener Agent-Datei `version:` im YAML-Frontmatter minor erhöhen (Plan Z. 431).
- **Soll:** REQ-Mandate werden über `{{#if DOD_REQ_TRACEABILITY}}` gegated; bei aktiver Traceability erscheint genau das kanonische Format `REQ-<AREA>-<NN>` (mit dem von main chat festgelegten `N`).
- **Fehlerpfade:** Rendering mit `rapid-prototyping` enthält keine REQ-Mandate; Rendering mit Traceability an enthält das kanonische Format; ein verbliebenes ungatedes `REQ-xxx` im gerenderten Text ist ein Fehler (Task-21-Test, Z. 432).

### IC-5 — Abgrenzung #339 / #1158 K-01 (Plan Z. 414, Entscheidungen 30/54)

- **#339:** Das Format `REQ-L2-AT-018` ist nach Entscheidung 54 ungültig (mehrteiliger Bereich); #339 passt sich bei seiner Neufreigabe an (Entscheidung 30). Keine #339-Planung in Phase H.
- **#1158 K-01:** Eigentümer ist Task 18 (`tests/test_dod_gating_rendered.py`, Plan Z. 165); diese Spec ändert daran nichts. Für #1167 zählt nur die disjunkte Dateimenge in IC-4.
- **Fehlerpfade:** Ein Test, der `REQ-L2-AT-018` als gültig akzeptiert, verletzt Entscheidung 54 → `Severity.ERROR`.

## Datenfluss

- **Gating:** `config/dod-presets.yaml:56` (`rapid-prototyping: req-traceability: false`) bzw. Projekt-`dod`-Override → `scripts/lib/dod.py:335-354` (Preset-Auflösung, Full-Preset `:346-354` als autoritative Key-Menge) → `scripts/lib/config.py:3157` (`variables["DOD_REQ_TRACEABILITY"]`) → Template-Rendering `{{#if DOD_REQ_TRACEABILITY}}` (IC-4) und Validator-Entscheid (IC-2/IC-3). Kein zweiter Lesepfad.
- **Validator:** `python3 scripts/sync.py --validate` → `scripts/lib/cli_commands.py::_handle_validate` (`:1518`) → Import/Registrierung von `check_req_ids` (`:1672-1673`, Muster `check_temp_literals`) → `scripts/lib/consistency/req_format.py::check_req_ids(agent_meta_root, project_root, config)` liest REQ-Konfigurationszustand über IC-2, wendet `re.fullmatch` mit der Konstante aus IC-1 auf die inventarisierten Stellen (M1) an → `List[Finding]` → `scripts/lib/consistency/report.py::print_report` (`:44`) → Exit-Code 1 bei `Severity.ERROR` (Plan: still bei aus, ERROR bei an und fehlerhaft).
- **Rendering:** `agents/1-generic/*.md`-Templates + `config/conventions-presets.yaml:34` + `config/role-defaults.yaml` (IC-4) → sync.py-Rendering → `.claude/agents/` (nicht im Repo); Gating-Grep im gerenderten Text muss mit `rapid-prototyping` leer sein.

## Acceptance Criteria (nummeriert, testbar)

Given/When/Then; je AC mindestens einem Interface Contract zugeordnet. Die Ziffernzahl-Aussage in AC1/AC3 ist erst nach Auflösung von O-H2 (main chat) ausführbar — dies ist der eskalierte Entscheidungspunkt, kein Placeholder dieser Spec.

**AC1 — Regex-Konstante und Bereichs-Regel (IC-1).**
Given die Konstante aus IC-1 mit der von main chat festgelegten Ziffernzahl `N` (Kandidat A oder B aus M4), When `re.fullmatch` auf Teststrings angewendet wird, Then: `REQ-CMD-01` wird akzeptiert; `REQ-L2-AT-018` wird abgelehnt (mehrteiliger Bereich, Entscheidung 54); `REQ-1` wird abgelehnt; Strings ohne `REQ-`-Präfix, mit Kleinbuchstaben im Bereich oder mit `-` im Bereich werden abgelehnt; bei Kandidat A wird `REQ-COM-123` abgelehnt, bei Kandidat B akzeptiert. Die Konstante entspricht byte-identisch der von main chat gewählten Form.

**AC2 — Gating-State (IC-2).**
Given ein Projekt mit Preset `rapid-prototyping` (`req-traceability: false`, `config/dod-presets.yaml:57`) bzw. mit aktivierter Traceability, When `check_req_ids` / der Validator läuft, Then liefert der aus-Zustand keine Findings und keinen Fehler-Exit; der an-Zustand liefert genau ein `Severity.ERROR`-Finding je fehlerhaftem Vorkommen. Der Zustand wird ausschließlich über `DOD_REQ_TRACEABILITY` / `dod.req-traceability` gelesen (`scripts/lib/config.py:3157`, `scripts/lib/dod.py:347`); es gibt keine zweite Quelle (Plan AC4 des Issues, Z. 426).

**AC3 — `check_req_ids`-Vertrag (IC-3).**
Given `scripts/lib/consistency/req_format.py` mit `check_req_ids(agent_meta_root: Path, project_root: Path, config: Optional[dict]) -> List[Finding]` und Fixtures `REQ-CMD-01` (gültig), `REQ-L2-AT-018` (ungültig, mehrteilig), `REQ-1` (ungültig, Ziffernzahl), When `python3 -m pytest tests/test_req_id_format.py -q` läuft, Then: `test_valid_ids_pass_both_states` ist grün; `test_malformed_req_id_fails_when_traceability_on` und `test_multi_part_area_rejected` liefern ein ERROR-Finding; `test_malformed_req_id_ignored_when_off` liefert keines; `test_single_area_accepted` (`REQ-CMD-01`) liefert keines. Die Registrierung in `cli_commands.py` (`:1518`, `:1672-1673`) ist wirksam; `python3 scripts/sync.py --validate` meldet im Repo (Preset `rapid-prototyping`) nichts Neues.

**AC4 — Template-/Preset-Rendering (IC-4).**
Given die in IC-4 gelisteten Dateien, When sync.py mit Preset `rapid-prototyping` bzw. mit Traceability an rendert, Then enthält der gerenderte Text im ersten Fall keine `REQ-ID`/`REQ-xxx`-Mandate (Grep leer), im zweiten Fall genau das kanonische Format `REQ-<AREA>-<NN>` (mit festgelegtem `N`). `python3 -m pytest tests/test_agents_frontmatter.py tests/test_ac01_render_identity.py tests/test_context_budgets.py -q` ist grün; ac01-/Budget-Hash-Drift wird per Helper (Plan Task 6) mit dokumentiertem Grund neu gepinnt (Plan Z. 435). Betroffene Agenten tragen eine minor erhöhte `version:`.

**AC5 — Abgrenzung (IC-5).**
Given die Abgrenzungsregeln aus IC-5, When die Testsuite läuft, Then wird `REQ-L2-AT-018` als ungültig behandelt (Entscheidung 54), es findet keine #339-Planung in Phase H statt (Entscheidung 30), und `tests/test_dod_gating_rendered.py` (#1158 K-01, Task 18) bleibt unverändert und grün. Keine Closing-Keywords in Commit-/PR-Texten (Entscheidung 38e).

Anzahl AC: 5 (AC1→IC-1, AC2→IC-2, AC3→IC-3, AC4→IC-4, AC5→IC-5). Jede AC ist testbar und mindestens einem Interface Contract zugeordnet.

## Offene Fragen + Risiken

**Offene Fragen.**
- **O1 — O-H2: Ziffernzahl `N` (Entscheidungspunkt für main chat).** Messung siehe M1-M4. Beide Kandidaten sind defensible: A `\d{2}` (D-H4 `<NN>`, 37/37 vergebene IDs zweistellig, Maximum 22) und B `\d{2,3}` (O-H2-Begründung `docs/REQUIREMENTS.md:4` „dreistellig", `requirements.md:45`, `REQ-047`-Beispiele). Der Plan lässt O-H2 bewusst offen (Z. 146); diese Spec wählt nicht. **Eskalation:** main chat legt `N` fest (A oder B); erst danach werden AC1/AC3 ausführbar. Kein Platzhalter, sondern eine bewusst offene, genau umrissene Entscheidung.
- **O2 — `docs/REQUIREMENTS.md` mitziehen?** Plan File Structure (Z. 167) nennt `docs/REQUIREMENTS.md` nur für Task 17 (K-17/K-11) „nur falls Spec verlangt". Diese Spec verlangt es nicht; die Formatzeile `:4` bleibt in Task 19 unangetastet. Keine User-Rückfrage nötig.

**Risiken.**
- R1: Fälschliches Festlegen von `N` durch die Implementierung ohne main-chat-Entscheidung → falscher Validator. Mitigation: O1 als Harte Vorbedingung für Task 20; AC1 verlangt byte-identische Übereinstimmung mit der main-chat-Wahl.
- R2: Ein ungatedes `REQ-xxx` verbleibt im gerenderten Text (z. B. `validator.md:53`, `bug-feature-analyzer.md:42,84,134`) → Task-21-Test rot. Mitigation: vollständige Liste IC-4, Gating-Grep in AC4.
- R3: `REQ-047` (ohne Bereich) wird als gültiges Vorbild übernommen → verletzt D-H4/54. Mitigation: M3 ordnet es als bereinigungsbedürftiges Beispiel ein; AC1 lehnt Strings ohne Bereichs-Segment ab.
- R4: Anker-Drift (Plan `9aa0e0c0`, Siblings `87564958`, hier `4d3d21f`) → falsche file:line-Ziele. Mitigation: alle Anker gegen `4d3d21f` neu gemessen; Korrekturen in „Re-gemessene Anker" unten.
- R5: #339 wird versehentlich doch geplant oder `REQ-L2-AT-018` zugelassen → Entscheidungen 30/54 verletzt. Mitigation: IC-5, AC5.

**Re-gemessene Anker / Drift gegenüber Plan (Spec gewinnt für Task 19-21; Plan nachziehen).**
- Anker-Basis: Plan `9aa0e0c0` → hier `4d3d21f` (Phase-H-Sibling-Specs `87564958`).
- `agents/1-generic/` Inventur: Plan „90 Zeilen/36 Dateien" → hier **89 Treffer/36 Dateien**.
- `config/role-defaults.yaml`: Plan „`REQ-ID vergeben` bei `:2668`, nicht `:2694`" → hier `:2691`; `:2694` ist `dod_flag: req-traceability` (Plan-Bemerkung bestätigt).
- `docs/REQUIREMENTS.md:4` (Formatzeile): unverändert bestätigt.
- `validator.md`: `:53` ungated, `:38-39` im Block `:35-41` gegated, `:97` gegated — unverändert bestätigt.
- `bug-feature-analyzer.md:42,84,134` ungated — unverändert bestätigt.
- Plan Task 20 `_handle_validate` `:1408` → hier `:1518`; Registrierung `check_temp_literals` `:1507` → hier `:1672-1673`.

**ADR (Kontext / Entscheidung / Konsequenz — alle aus dem Plan übernommen, keine neue Entscheidung).**
- **ADR-1 (D-H4, kanonisches Format):** Kontext — zwei Formate in `docs/REQUIREMENTS.md:4` und uneinheitliche Templates. Entscheidung — ein Format `REQ-<AREA>-<NN>` (Z. 131). Konsequenz — alle Stellen in IC-4 werden vereinheitlicht; `N` bleibt O-H2 (ADR-4).
- **ADR-2 (Entscheidung 54, strikter Bereich):** Kontext — #339 schlägt mehrteiligen Bereich vor. Entscheidung — genau ein Bereichs-Segment ohne `-`; `REQ-L2-AT-018` ungültig (Z. 132). Konsequenz — Fixture `REQ-L2-AT-018` wird abgelehnt (AC1/AC3/AC5); #339 passt sich bei Neufreigabe an.
- **ADR-3 (Gating auf `DOD_REQ_TRACEABILITY`):** Kontext — teils gegate, teils ungatede REQ-Mandate. Entscheidung — Single Source über `dod.req-traceability`; still bei aus, ERROR bei an (Z. 414/421). Konsequenz — Preset `rapid-prototyping` bleibt ohne REQ-Mandate; kein zweiter Config-Key.
- **ADR-4 (O-H2 offen, keine neue Entscheidung):** Kontext — M2 (2-stellig) und M3 (3-stellig dokumentiert) widersprechen sich; Plan lässt O-H2 offen. Entscheidung — keine Wahl in dieser Spec; Eskalation an main chat (Nutzergo 22.11: nachgetragen, keine neue Entscheidung). Konsequenz — Task 20 startet erst nach main-chat-Festlegung von `N`.

**Nicht verifiziert (ehrlich).**
- Keine Tests ausgeführt, kein `sync.py`-Lauf, kein `git`-Befehl (Spec-Worker ohne Shell); HEAD-SHA aus `.git/refs/heads/chore/phase-h-bundle` gelesen. Alle PASS/FAIL-Erwartungen sind Planwerte plus statisch gelesene Belege.
- Issue-Texte (#1167, #339, #1158, #1014) nicht direkt gelesen; Ableitungen stammen aus dem Plan (Z. 110, 127, 131-132, 146, 408-437).
- Zählungen (89 Treffer/36 Dateien, 37 IDs/8 Bereiche) statisch per Grep-Tool ermittelt, nicht per Python-Ausführung bestätigt.

## Trace-Anker: spec-id: SPEC-REQ-ID-FORMAT-1167-2026-11-11
