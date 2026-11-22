---
spec-id: SPEC-issue-label-children-2026-11-11
title: Kinder-Addendum Phase F (#1201/#1202) — Spec (Roadmap PR 3.5 / P20, Task 0)
status: APPROVED (User, 2026-11-21, direkt freigegeben ohne Review)
approved: false
review-hinweis: "DRAFT — Freigabe nach Review erforderlich"
klasse: "M — Preset-Default + Migrationswarnung + Projektion (#1201), Priority-Kanonisierung + Platzhalter + Consistency-Regel (#1202)"
datum: 2026-11-20
issues: "#1201 #1202 (#1211 gesperrt; #1188 als Abhängigkeit)"
plan: docs/superpowers/plans/2026-11-11-phase-f-label-taxonomy.md
roadmap: docs/plans/2026-11-15-master-roadmap.md
branch: feat/phase-f-children
gate: "Status: APPROVED nach Review (Task 0 Step 2); zusätzlich Task 0b-Freigabe (#1201) und F-Kern #1188 (SKIP 3.2)"
---

# Kinder-Addendum Phase F (#1201/#1202) — Spec (Roadmap PR 3.5 / P20, Task 0)

> Status: APPROVED (User, 2026-11-21, direkt freigegeben ohne Review)
> spec-id: `SPEC-issue-label-children-2026-11-11` — vom Phase-F-Plan Task 0 Step 1 vorgegeben („Produces Spec-ID"), unverändert übernommen.
> Review-Hinweis: **DRAFT — Freigabe nach Review erforderlich.** Keine selbst erteilte Freigabe; Status wechselt ausschließlich durch User-Freigabe nach Review auf `APPROVED` (Roadmap §4 E-22).
> Dateiname: Auftrag `2026-11-20-phase-f-children-addendum-spec.md`; Phase-F-Plan Task 0/File Structure nennt `docs/specs/2026-11-11-issue-label-children-spec.md`. Rein organisatorische Abweichung (Datum 2026-11-20, Name „children-addendum“ analog Roadmap-E-22), keine inhaltliche Entscheidung.
> Klasse: **M** (Roadmap §1 P20). Umsetzung der Kinder erst nach APPROVED dieser Spec (Roadmap §2.2: „P18/P20 nur nach APPROVED-Spec", E-22).

Diese Spec ist die Ausgliederung des Spec-Kerns aus **Task 0** des Phase-F-Plans für die Kinder-Addenda #1201 (Namespace-Default + Migrationswarnung + Projektion) und #1202 (kanonische Priority). Sie enthält **keinen Implementierungscode** und **keine neuen Entscheidungen**: alle Werte, Strings, Check-IDs und Abhängigkeiten stammen aus den referenzierten Quellen (siehe §7 Traceability). Wo eine Quelle keine Entscheidung hergibt oder eine Freigabe aussteht, ist der Punkt als `OFFEN` markiert und nicht erfunden oder aufgelöst.

## 1. Problem / Ist-Soll

**Ist (Plan-Stand):** Der F-Kern #1188 liefert Resolver, `ISSUE_*`-Platzhalter und die Admin-UI-Sektion; die Kinder #1201/#1202 sind vom Kern bewusst nicht gelöst (Referenzplan T14 löst #1201 nicht, T26 ändert die alte Conventions-View nicht — Phase-F-Plan :153). Die Kinder-Addenda sind im Phase-F-Plan Task 0 einer eigenen Spec zugewiesen (Klassifikation :47/:53/:54). Nach Scope-Report liegt **keine** Spec-Datei auf Platte (`.tmp/audit/wave-bundle-mapping-2026-11-21.md:12,72`), obwohl das Ledger eine Freigabe vermerkt.

**Soll:** Eine freigegebene Spec fixiert (a) #1201 GitHub-Projektion `bug` / GitLab-Projektion `type::bug` und Migrationswarnung für `type: {type}`, (b) #1202 eine kanonische Priority-Definition P0–P3 je Klasse mit Platzhalter `{{ISSUE_PRIORITY_TABLE}}` und Regel `template.duplicate-priority-definition` — ohne neue Achsen `severity`/`status` (Entscheidung 34, F-neu-4).

**Problem:** Ohne diese Spec bleiben Task 2 (#1201) und Task 3 (#1202) gesperrt (Phase-F-Plan Task 0 Step 2). Zusätzlich hängt PR 3.5 am SKIP-Paket 3.2 (F-Kern #1188) — siehe §6, `OFFEN-3`.

## 2. Scope und Abgrenzung

### 2.1 Scope in

- Spec-Kern Task 0: (a) #1201, (b) #1202, (c) Entfall `severity`/`status`.
- Fixierung der hier einschlägigen Entscheidungen 51, 57 (Projektionswerte), 34/F-neu-4 (keine Severity/Status-Achse) aus dem Phase-F-Plan.
- Explizite Vermerkung der Gates und Abhängigkeiten (Task 0 Step 2, Task 0b, F-Kern #1188) als `OFFEN`.
- Ausschließlich diese Markdown-Datei. **Docs-only**: kein Produktivcode, keine Templates, keine Config, kein Rebaseline. Verifiziert per Review und `git diff` (eine Datei).

### 2.2 Scope out / Nicht-Ziele

- Task 1 (#1203 Flag-Disambiguierung), Task K (#1188-Kernausführung), Task 4 (#1204 Admin-UI), Task V (#1187-Querverweis) — gehören zu PR 3.2 / F-PR1, nicht zu dieser Spec.
- Task 2 und Task 3, die eigentliche Umsetzung von #1201/#1202 (Phase-F-Plan :168–188) — diese Spec ist deren Gate, nicht deren Implementierung.
- **#1188 selbst**: Von #1188 wird nichts angefasst; der F-Kern wird hier ausschließlich als **Abhängigkeit/Gate** vermerkt (`OFFEN-3`).
- **#1211**: bleibt gesperrt (Pilot-Gate, Entscheidung 26); kein Task, nicht Teil dieser Spec (Roadmap §1 P20: „#1211 gesperrt").
- #1141: liegt im Phase-D-Plan (Entscheidung 35), nicht hier.
- Änderung des APPROVED Referenzplans `docs/plans/2026-11-09-issue-label-taxonomy-plan.md`: nur nach separater User-Freigabe (Task 0b) — diese Spec ändert ihn nicht und setzt keinen Status auf APPROVED.

## 3. Interface-Vertrag (Datei:Symbol, Signatur, Fehlerpfade)

Alle Werte sind aus Phase-F-Plan Task 0 Step 1 (:114), Task 2 (:185) und Task 3 (:172–174) übernommen. Nicht belegte Punkte sind `OFFEN`.

### 3.1 #1201 — Projektion und Namespace (Entscheidungen 51, 57, 34/F-neu-5)

| Artefakt | Vertrag (Quelle) |
|---|---|
| GitHub-Projektion | `bug` (flach) — Entscheidung 51; **weicht ab** vom APPROVED Referenzplan K-7/F-1 (`type/…`, :1154). Freigabe der Referenzplan-Änderung steht aus → `OFFEN-2`. |
| GitLab-Projektion | `type::bug` (scoped label) — Entscheidung 57. Namespace-Trenner `::` aus Host-Config-Key, **kein** Host-Literal im Code. Trenner plan-eingeführt: `platform.gitlab.defaults.separator.single: "::"` in `config/issue-conventions-presets.yaml` (Referenzplan T2, :444) bzw. `separator.single/multi` je Adapter in `config/issue-adapters.yaml` (T3, :304, Objektform K-2 :147–153). Freigabe wie bei 51 → `OFFEN-2`. |
| Migrationswarnung | Für den Alt-Wert `type: {type}` (Preset-Default an `config/conventions-presets.yaml:56,93,125`): Warnung im Log statt stiller Übernahme (Task 2 Step 1, :185). |
| Fehlerpfad Host-Literal | `test_projection_has_no_host_literal` prüft per `ast`-String-Konstanten, dass `scripts/lib/conventions.py` weder `"::"` noch einen Host-Namen als StringLiteral enthält (Kommentare zählen nicht). |
| Consumer | `scripts/lib/conventions.py::_render_git_issue_naming(spec: dict) -> str` (:277); Preset-Schlüssel `issues.labels.namespace` (`:56,93,125`, real verifiziert). |

### 3.2 #1202 — Kanonische Priority (Entscheidung 34/F-neu-4)

| Artefakt | Vertrag (Quelle) |
|---|---|
| Priority-Definition | Eine kanonische Definition **P0–P3 je Klasse** (`BUG`/`FEATURE`/`USER-ERROR`/`FINDING`) — Task 0 Step 1b (:114). |
| Platzhalter | `{{ISSUE_PRIORITY_TABLE}}`, registriert in `scripts/lib/consistency/placeholders.py::_BUILTIN_VARS` (`:12`). |
| Renderer | `render_priority_table(resolved) -> str` — Signatur im Stil der Kern-Renderer aus T9; **exakte Signatur erst nach Kern-T9 gegen dann existierenden Code zu lesen**, hier nicht verifizierbar → `OFFEN-4`. |
| Consistency-Regel | Neue Check-ID `template.duplicate-priority-definition` in `scripts/lib/consistency/issue_labels.py` (vom Kern geliefert). |
| Konsumierte Kern-Achse | `priority.values.<P>.description` (Referenzplan). |
| Nicht-Ziel | Keine `severity`-/`status`-Achse (Entscheidung 34, F-neu-4, :232). |
| Templates | `agents/1-generic/meta-feedback.md` (`:48`) und `agents/1-generic/bug-feature-analyzer.md` (`:93–97`, Output-Contract `:117`) erhalten den Platzhalter statt lokaler P0–P3-Tabellen. `incident-responder.md` (`:72,126`) und `template-auditor.md` (`:114`) bleiben unangetastet (Task 3 Step 1, :174). |

### 3.3 Gate-/Abhängigkeitsvertrag

| Gate | Vertrag | Quelle |
|---|---|---|
| Spec-Freigabe | `Status: APPROVED` durch User; ohne Freigabe Task 2 **und** Task 3 nicht ausführbar. | Task 0 Step 2 (:115) |
| Referenzplan-Abweichung | User-Freigabe beider Projektionswerte (GitHub `bug`, GitLab `type::bug`); ohne Freigabe bleibt Task 2 (#1201) gesperrt, Task 3 (#1202) wäre ohne 0b möglich. | Task 0b (:118–124) |
| F-Kern #1188 | 3.5 hängt am F-Kern #1188 = SKIP-Paket 3.2 (E-20), weiterhin **OPEN**; Nutzer muss es selbst wieder öffnen. Siehe `OFFEN-3`. | Scope-Report :53, :73; Roadmap §3.4 |
| PR-Schnitt | F-PR2 (Nachfolge-PR): Task 3 (nach Kern-T9/T13/T23), dann Task 2 (nach Task 3, Kern-T5/T7/T14); Rebase auf gemergten F-PR1. | Phase-F-Plan PR-Schnitt :72–73 |

## 4. Datenfluss

1. **Input:** APPROVED Referenzplan #1188 (Achsen, D2, D15), Presets `config/conventions-presets.yaml` (`type: {type}`), Host-Config-Key für den GitLab-Trenner, Kern-`priority`-Achse.
2. **Transformation 1 (#1201):** Projektion je Adapter aus dem Resolver; Alt-Wert `type: {type}` löst Warnung aus; kein Host-Literal im Code.
3. **Transformation 2 (#1202):** Kanonische P0–P3-Tabelle je Klasse → `render_priority_table()` → Platzhalter `{{ISSUE_PRIORITY_TABLE}}`; doppelte lokale Priority-Definitionen erzeugen Finding `template.duplicate-priority-definition`.
4. **Output:** gerenderte Templates (`meta-feedback.md`, `bug-feature-analyzer.md`) ohne lokale P0–P3-Tabellen; konventionskonformer Namespace-Default.
5. **Persistenz:** Keine in dieser Spec. Umsetzung (Task 2/3) schreibt Code/Templates/Config; Rebaseline AC/G (klein/optional) im PR 3.5, nicht hier.

## 5. Akzeptanzkriterien (messbar)

### 5.1 Für diese Spec (Task 0 Gate)

- **AC-S1** — **Gegeben** dieser Entwurf, **wenn** das Review abgeschlossen ist, **dann** trägt die Spec `Status: APPROVED` durch User-Freigabe (nicht durch den Autor); bis dahin bleibt `DRAFT` und Task 2/3 sind nicht ausführbar.
- **AC-S2** — **Gegeben** Task 0 Step 1, **wenn** die Abschnitte §3.1–§3.2 geprüft werden, **dann** sind festgehalten: GitHub `bug`, GitLab `type::bug` (Trenner aus Config-Key), Migrationswarnung für `type: {type}`, P0–P3 je Klasse, `{{ISSUE_PRIORITY_TABLE}}`, `template.duplicate-priority-definition`, und keine `severity`/`status`-Achse.
- **AC-S3** — **Gegeben** die ausstehenden Freigaben, **wenn** die Spec geprüft wird, **dann** sind `OFFEN-2` (Task 0b) und `OFFEN-3` (#1188/SKIP 3.2) als Gate vermerkt und nicht aufgelöst; diese Spec setzt keinen Status des Referenzplans auf APPROVED und ändert #1188 nicht.
- **AC-S4** — **Gegeben** die Spec-ID, **wenn** sie registriert wird, **dann** lautet sie unverändert `SPEC-issue-label-children-2026-11-11` (Vorgabe Phase-F-Plan Task 0 Step 1).

### 5.2 Abgeleitete, messbare AC für Task 2/3 (Umsetzung — nicht Teil dieser Spec)

Übernommen aus Phase-F-Plan Task 2 Step 1 (:185) und Task 3 Step 1 (:174); hier dokumentiert, nicht implementiert:

- **AC-I1** (#1201): `test_github_projection_pinned` — GitHub-Projektion exakt `bug`; erst gültig nach `OFFEN-2`.
- **AC-I2** (#1201): `test_gitlab_projection_pinned` — GitLab-Projektion exakt `type::bug`, `::` über den Separator-Key des Adapters erzeugt; erst gültig nach `OFFEN-2`.
- **AC-I3** (#1201): `test_projection_has_no_host_literal` — kein `"::"`/Host-Name als String-Literal in `conventions.py`.
- **AC-I4** (#1201): `test_legacy_namespace_value_warns_not_silent` — Alt-Wert `type: {type}` warnt, wird nicht still übernommen.
- **AC-I5** (#1202): `test_priority_table_lists_p0_to_p3` — Tabelle enthält P0–P3 je Klasse.
- **AC-I6** (#1202): `test_meta_feedback_has_no_priority_literal` / `test_bfa_matrix_replaced_by_placeholder` — lokale P0–P3-Tabellen durch `{{ISSUE_PRIORITY_TABLE}}` ersetzt.
- **AC-I7** (#1202): `test_duplicate_priority_definition_rule_fires` — lokale Tabelle + verfügbarer Block → Finding `template.duplicate-priority-definition`.
- **AC-I8** (#1202): `test_placeholder_registered` — Platzhalter in `_BUILTIN_VARS`.
- **AC-I9** (#1202): `test_incident_responder_and_template_auditor_untouched` — `incident-responder.md`/`template-auditor.md` bleiben ohne Finding.

Jede AC-I-n mappt auf einen Interface-Vertrag aus §3; AC-I1/I2 hängen an `OFFEN-2`, AC-I5 an `OFFEN-4` (Signatur) bzw. der nach Kern-T9 zu verifizierenden Renderer-Existenz.

## 6. OFFEN — Risiken / Annahmen / Abhängigkeiten

- **`OFFEN-1` (Spec-Freigabe, Task 0 Step 2):** `Status: APPROVED` steht aus — Review erforderlich. Diese Spec bleibt DRAFT bis zur User-Freigabe. Nicht selbst aufzulösen.
- **`OFFEN-2` (Task 0b, Referenzplan-Abweichung #1201):** User-Freigabe für GitHub `bug` (Entscheidung 51, Abweichung K-7/F-1) und GitLab `type::bug` (Entscheidung 57) steht aus. Der APPROVED Referenzplan `docs/plans/2026-11-09-issue-label-taxonomy-plan.md` nennt `type/…`; seine Änderung braucht erneute Freigabe. Ohne Freigabe bleibt Task 2 (#1201) gesperrt; Task 3 (#1202) wäre ohne 0b ausführbar. **Nicht auflösen, keine Issue-Aktion, kein Status auf APPROVED setzen.**
- **`OFFEN-3` (F-Kern #1188 — SKIP-Paket 3.2, E-20):** PR 3.5 hängt am F-Kern #1188, der als Paket 3.2 **SKIP** ist und weiterhin **OPEN** bleibt. Der Nutzer muss #1188 selbst wieder öffnen (Entscheidung 49/56: Wiederöffnen nur nach User-Freigabe, nicht eigenmächtig); F startet nicht vor dem E-Kern (Entscheidung 56). Diese Spec **erwähnt #1188 ausschließlich als Gate/Abhängigkeit** und fasst es nicht an — kein Wiederöffnen, kein Code, keine Issue-Aktion. Ohne erfüllten F-Kern ist Task 2/3 (Kern-T5/T7/T14 bzw. T9/T13/T23) nicht ausführbar.
- **`OFFEN-4` (Renderer-Signatur):** Exakte Signatur von `render_priority_table(resolved) -> str` und Namen der Kern-Renderer sind im Plan ausdrücklich „nicht verifizierbar"; Task 3 liest sie nach Kern-T9 gegen den dann existierenden Code. Hier nicht erfinden.
- **Annahme A1:** Phase-F-Plan ist verbindliche Quelle; Anker gegen `origin/main 9aa0e0c0` gemessen, bei Ausführung erneut messen (Frische-Check :98–100). `_render_git_issue_naming` (:277), `issues.labels.namespace` (`conventions-presets.yaml:56,93,125`) sind real verifiziert. Keine Code-Ausführung in dieser Spec.
- **Annahme A2:** Keine Aktivierung von `issue-conventions` in `.meta-config/project.yaml` dieses Repos (Golden-Test AC-9 bleibt beweiskräftig, Global Constraints :40).
- **Risiko R1:** Golden-Test `tests/fixtures/slimming-golden/git.md:154` (`type: <type>`) muss bei Task 2 bewusst nachgezogen werden; `enabled: false`-Block ändert sich (Entscheidung 34/F-neu-5). Nicht Teil dieser Spec.
- **Risiko R2:** Zuordnung 3.4/3.5 zu „W4-Rest" ist Entscheidungspunkt des Scope-Reports (:27, :70) — hier nicht entschieden.

## 7. Traceability (ausschließlich referenzierte Quellen)

| Quelle | Stelle | Übernommen |
|---|---|---|
| Master-Roadmap | §1, P20 | Phase F-PR2 (#1202, #1201; #1211 gesperrt), S/C, RB AC/G, M; E-22: Kinder-Addendum einzeln nach Review (DRAFT bis dahin) → Kopf, §2 |
| Master-Roadmap | §2.2 | „P18/P20 nur nach APPROVED-Spec (E-22)"; Kette #1188 vor #1181 → §1, §6 `OFFEN-3` |
| Master-Roadmap | §3.4, PR 3.5 | `feat/phase-f-children`, P20 #1202 → #1201, RB 1 (klein/optional), Gate „Kinder-Addendum zum Wellenstart" → §2, §4 |
| Master-Roadmap | §3.2, PR 3.2 | F-Kern #1188 = SKIP-Kontext; Kinder nur individuell (E-22) → §6 `OFFEN-3` |
| Master-Roadmap | §4, E-22 | „Kinder-Addendum F … einzeln zum Wellenstart nach Review freigeben (bis dahin DRAFT)" → Status DRAFT, Review-Hinweis |
| Phase-F-Plan | Task 0 (:108–116) | Spec-Kern (a/b/c), Spec-ID, Review-Gate → §3, §5.1 |
| Phase-F-Plan | Task 0b (:118–124) | Freigabe-Gate Referenzplan-Abweichung, beide Projektionswerte → §6 `OFFEN-2` |
| Phase-F-Plan | Entscheidungen 51, 57, 34/F-neu-4 (:225–226, :232) | GitHub `bug`, GitLab `type::bug`, keine Severity/Status-Achse → §3.1, §3.2 |
| Phase-F-Plan | Task 2/3 (:168–188) | Projektions-/Priority-Vertrag, Tests → §3, §5.2 |
| Phase-F-Plan | PR-Schnitt (:62–76) | F-PR2, Reihenfolge Task 3 → Task 2, Gate → §3.3 |
| Scope-Report | `:12,53,66,72–73` | Keine Spec-Datei auf Platte; #1188-SKIP-Abhängigkeit; Task-0b-Freigabe → §1, §6 |
| Phase-F-Plan | „Nicht verifiziert" (:302–309) | Renderer-Signatur offen → §6 `OFFEN-4` |

Nachgelagerte PRs (nicht Teil dieser Spec): F-PR1 / Roadmap PR 3.2 (#1188-Kern, #1203, #1204) und F-PR2 / Roadmap PR 3.5 mit Task 3 (#1202) dann Task 2 (#1201); Gates: `APPROVED` dieser Spec, Task 0b-Freigabe, erfüllter F-Kern #1188.

## 8. Review-Hinweis

**DRAFT — Freigabe nach Review erforderlich.** Der Autor erteilt keine Freigabe. Nach Review durch `concept-reviewer`/User: `Status: APPROVED` setzen, `OFFEN-1` schließen; `OFFEN-2` (Task 0b) und `OFFEN-3` (#1188/SKIP 3.2) bleiben getrennte User-Gates und werden von dieser Spec nicht aufgelöst. spec-id unverändert beibehalten.
