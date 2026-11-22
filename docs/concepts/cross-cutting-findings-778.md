# Konzept: Cross-cutting Role Findings (#778) — Dispositionen

> Status: APPROVED (Nutzergo 22.11 — Konzept auf Basis des freigegebenen Phasenplans 2026-11-11-phase-h-context-eval.md nachgetragen, keine neue Entscheidung)

- **Autoritative Basis:** `docs/superpowers/plans/2026-11-11-phase-h-context-eval.md`, Task 14 (Z. 317–323); Gate-Eintrag Z. 69 (`14 | #778 | H1 (Gate-Task) | Concept-Freigabe; ohne APPROVED nach H2`); Scope-Zeile Z. 31 (`Design-Issue, F-1..F-6 ohne Umsetzungsbeschluss`).
- **Finding-Quelle:** `docs/plans/2026-09-12-literature-anchored-agent-improvements-plan.md` §1.11 (Z. 253–264) mit den Design-Gates D2/D3/D4/D5/D7/D8 (Z. 332–394) und den bestätigten User-Entscheidungen (§7, Z. 538–556, Datum 2026-09-13).
- **Messstand:** Branch `chore/phase-h-bundle` @ `87564958`. Alle file:line-Belege sind gegen diesen Stand neu gemessen, nicht aus älteren Dokumenten übernommen.
- **Geltung:** Gemeinsamer Hintergrund für Task 0 / #1014 (Phasenplan Z. 325–332). Dieses Konzept enthält **keine** Umsetzungsaufgaben für Phase H; Umsetzungstasks entstehen erst nach `Status: APPROVED` in einem Folgeplan (Z. 321). Es werden **keine neuen Entscheidungen** getroffen — jede Disposition folgt einer bereits freigegebenen Entscheidung des Phasenplans bzw. des Literature-Design-Gates.

## 1. Problem / Ziel / Nicht-Ziele

**Problem:** Issue #778 beschreibt sechs querschnittliche Befunde an den generischen Rollen-Templates, ohne einen Umsetzungsbeschluss zu enthalten. Der freigegebene Phasenplan macht die Freigabe dieses Konzepts zum H1-Gate für H2 und zur gemeinsamen Grundlage von #1014.

**Ziel:** Für jeden Befund F-1..F-6 genau **eine** Disposition (`umsetzen` / `verwerfen` / `abspalten`) mit aktuell gemessenem file:line-Beleg festschreiben, sodass ein Folgeplan die Restarbeit ohne erneute Entscheidungsfindung aufnehmen kann.

**Nicht-Ziele:**
- Keine Template-, Config-, Hook- oder Code-Änderung; keine Umsetzung in Phase H (Phasenplan Z. 321–322).
- Keine neue Architektur, kein neues Schema-Feld, kein neuer MCP-Server, kein neues Review-Rule-Format.
- Keine Schließung von #778 und keine REQ-ID-Vergabe; keine Wiederholung der bereits bestätigten Design-Gates D1–D8.

**Betroffene Subsysteme (nur als Evidenz, nicht als Änderungsziel):** Agent-Frontmatter, `scripts/lib/frontmatter.py`, `scripts/lib/consistency/`, `config/role-defaults.yaml`, `config/review-rules/*.yaml`, Review-/Audit-Rollen-Templates, `.opencode/skills/conventions/`.

## 2. Dispositionstabelle (F-1..F-6)

| ID | Finding | Disposition | file:line-Beleg (Messstand `87564958`) | Entscheidungsbasis |
|---|---|---|---|---|
| F-1 | Referenzstandards nicht systematisch verankert | **umsetzen — bereits implementiert, kein offener Rest** | `docs/plans/2026-09-12-literature-anchored-agent-improvements-plan.md:257,332-343`; Spec `docs/specs/2026-09-15-reference-standards-design.md:2-4` (`spec-id: SPEC-REFERENCE-STANDARDS-2026-09-15`, `status: APPROVED`); `scripts/lib/frontmatter.py:40,558`; `scripts/consistency-check.py:68,231`; `agents/1-generic/security-auditor.md:6`, `agents/1-generic/validator.md:7`, `agents/1-generic/requirements.md:14`; `.opencode/skills/conventions/SKILL.md:47-53`; `config/project-config.schema.json:774` | D2 (bestätigt 2026-09-13) + APPROVED Spec 2026-09-15 |
| F-2 | Cross-Agent-Boundaries zentral statt in Templates | **abspalten — Restarbeit in einem Folgeplan; Phase H ändert keine Templates** | `agents/1-generic/requirements.md:73-75` (Sektion „Boundary to planner" + Handoff-Prosa); `agents/1-generic/ideation.md:20` (`hand off in a structured way`); `docs/plans/2026-09-12-literature-anchored-agent-improvements-plan.md:345-356` (D3), `:422-430` (WP2 mit grep-Vollcheck über 80 Templates); Phasenplan `:321` (keine Template-Änderung) | D3 (Umfang: alle 80 Rollen, vollständig) + Phasenplan-Task-14-Grenze |
| F-3 | Review-/Audit-Rollen brauchen Rule-IDs + Evidenzpflicht | **abspalten — Restarbeit (Domänen `CR`/`CONCEPT`/`A11Y`/`DEP`, Normalisierung) in einem Folgeplan** | Bestehend: `config/review-rules/ai.yaml:25-100` (AI-01..08, `standard_ref`), `backend.yaml`, `database.yaml`, `frontend.yaml:1-28`, `security.yaml`, `ui.yaml`; Evidenzpflicht z. B. `agents/1-generic/backend-reviewer.md:25,50,90,92`, `database-reviewer.md:25,51,99,101`, `security-auditor.md:34,159,196`; Lücke: `code-reviewer.md`, `concept-reviewer.md`, `dependency-auditor.md`, `accessibility-specialist.md` — **kein** `rule_id`/`review-rules`-Treffer; Quelle `:259,358-364` (D4), `:432-440` (WP3) | D4 (Granularität je Domäne; Rollen gleicher Domäne teilen die Datei) |
| F-4 | Shared tool/MCP needs | **abspalten — separates MCP-Design-Issue als Deliverable; keine Infrastruktur hier** | `docs/plans/2026-09-12-literature-anchored-agent-improvements-plan.md:260,366-375` (D5: keine neuen MCP-Server, vier Items dokumentiert, `config/skills-registry.yaml` unverändert), `:485` (WP13-Deliverable), `:550,556` (Entscheidung + Follow-up); im Repo **kein** Issue-/Beleg-Eintrag für das eröffnete Follow-up gefunden | D5 (bestätigt 2026-09-13) |
| F-5 | Review-Methodik & Reliability | **abspalten — Provenienz-Doku im Folgeplan, kein Code** | `docs/plans/2026-09-12-literature-anchored-agent-improvements-plan.md:261` (Finding), `:386-389` (D7: `accept`, Doku, kein Code), `:312` (externe Quellen übernommen, nicht erneut HTTP-geprüft); intern: `docs/plans/2026-10-04-oreilly-cybersecurity-2026-role-enrichment.md:12-13` (Literatur-Index, 24 Queries/12 Quellen) | D7 (bestätigt als `accept`/Doku ohne §7-Position) |
| F-6 | Role-wide patterns; `provider-expert`-Orphan / `intern-developer` | **verwerfen — Orphan-Befund `duplicate`, keine Aktion; Routing-Teil (D-H5) liegt in Task 13, nicht hier** | `scripts/lib/frontmatter.py:51-56` (`WRAPPER_TEMPLATES = frozenset({"provider-expert"})`); `scripts/lib/config_audit.py:25,74-92,350-361` (Wrapper-Base-Ausnahme); `CHANGELOG.md:1834` (`documented provider-expert as a wrapper`); `config/role-defaults.yaml` — **kein** `provider-expert`-Eintrag (nicht routbar, entspricht Base-Status); `agents/1-generic/intern-developer.md:5,13` (`Do not route real work here` / `must never be routed real production work`), `config/role-defaults.yaml:99,107-108` (`addressability: name_only` + `name_only_reason`); Quelle `:262,391-393` (D8); Phasenplan `:134,288,305,310` (Entscheidung 34 / D-H5) | D8 (`duplicate`, „verified — no action") + Entscheidung 34 / D-H5 (Phase-H-Task 13) |

## 3. Evidenz und Begründung je Finding

### F-1 — Referenzstandards (umsetzen, bereits implementiert)
D2 hat Feldname `reference_standards`, Werteformat als String-Liste `"<STANDARD>[@<version>][#<section>]"` und die Ablage im Template-Frontmatter mit Validierung im `consistency-check` verbindlich entschieden. Der Messstand zeigt die vollständige Umsetzung: Parser-Konstante und -Funktion in `scripts/lib/frontmatter.py:40,558`, Import/Aufruf im Consistency-Lauf `scripts/consistency-check.py:68,231`, das optionale Feld in einer Vielzahl von Rollen (Belege oben), die Dokumentation im `conventions`-Skill und der Default-Strip in `config/project-config.schema.json:774`. Die strukturierte Map `{name, version, section, url}` bleibt laut D2 eine spätere Option und ist **nicht** Gegenstand dieses Konzepts — eine diesbezügliche Aufwertung wäre eine neue Entscheidung.

### F-2 — Boundary-Platzierung (abspalten)
D3 hat die Zweiteilung gewählt: Routing-/Ownership-Boundary zentral (`config/role-defaults.yaml`, `orchestrator.md`), Behavioral Self-Constraint im Template, keine Duplizierung von Routing-Entscheidungen im Template. Der Messstand zeigt den Rest: `agents/1-generic/requirements.md:73-75` trägt weiterhin eine eigene Sektion „Boundary to planner" samt Handoff-Text; `agents/1-generic/ideation.md:20` formuliert `hand off in a structured way`. WP2 (`:422-430`) fordert einen grep-basierten Vollcheck über alle 80 Templates; dieser ist hier nicht erneut ausgeführt worden, die zwei Stichproben belegen aber, dass die D3-Bereinigung nicht vollständig durchgeschlagen ist. Da Task 14 ausdrücklich keine Template-Änderung erlaubt, ist die Disposition `abspalten` — nicht `umsetzen` in Phase H.

### F-3 — Review-Rule-IDs + Evidenzpflicht (abspalten)
D4 hat `config/review-rules/<domain>.yaml` mit `id: <DOMAIN>-NN`, `title`, `severity_hint`, `standard_ref` und der Pflicht „kein Finding ohne `rule_id` + Evidenz" beschlossen. Der Messstand zeigt sechs Domänen-Dateien (`ai`, `backend`, `database`, `frontend`, `security`, `ui`) mit `standard_ref`-Feldern und einer konsistenten Evidenzpflicht in den zugehörigen Reviewer-Templates. Die vier in WP3 (`docs/plans/2026-09-12-literature-anchored-agent-improvements-plan.md:434`) genannten Rollen `code-reviewer`, `concept-reviewer`, `dependency-auditor` und `accessibility-specialist` haben **keinen** `rule_id`/`review-rules`-Bezug im Template; die von D4 genannten neuen Domänen `CR-`, `CONCEPT-`, `A11Y-`, `DEP-` existieren nicht als Dateien. Zusätzlich fällt auf, dass `ai-security-guardian.md:71` `AIS-0x` aus einem „rules index" zitiert, während `ai.yaml:25-92` nur `AI-01`..`AI-08` definiert — dieser ID-Mismatch ist Bestandteil des Restbefunds, keine neue Entscheidung. Disposition `abspalten` in einen Folgeplan (Konfigurations- und Template-Arbeit), nicht in Phase H.

### F-4 — MCP-/Tool-Bedarf (abspalten)
D5 hat für diesen Batch ausdrücklich **keine** neuen MCP-Server beschlossen: Observability nur als optionaler Doku-Hinweis, RAG über das bestehende Knowledge-Wiki, Confluence/Jira/Notion als manueller Pfad, Provider-Gateways out of scope. Die Auswirkung ist laut `:374` documentiert (`F-4` wird `modify`; `config/skills-registry.yaml` bleibt unangetastet), und WP13 verankert ein separates MCP-Design-Issue als Deliverable. Disposition `abspalten` entspricht genau dieser Entscheidung; `umsetzen` würde dem widersprechen.

### F-5 — Review-Methodik (abspalten, Doku)
D7 ist als `accept` ohne §7-Position bestätigt: Provenienz der Literatur-Anker offenlegen, kein Code. Der Messstand zeigt eine bereits vorhandene methodische Basis (`:312` — Quellen übernommen, nicht erneut HTTP-geprüft; `docs/plans/2026-10-04-oreilly-cybersecurity-2026-role-enrichment.md:12-13` — interner Literatur-Index). Ein eigenes Doku-Artefakt zur Provenienz-Offenlegung je Rolle ist hier nicht entstanden; da Phase H keine Doku-Arbeit außer diesem Konzept umfasst, ist die Disposition `abspalten`.

### F-6 — provider-expert / intern-developer (verwerfen)
D8 stuft den `provider-expert`-Orphan als `duplicate` ein — „verified — no action". Der Messstand bestätigt die Wrapper-Base-Rolle über `WRAPPER_TEMPLATES` und die `config_audit`-Ausnahme sowie den CHANGELOG-Eintrag; `provider-expert` erscheint nicht in `config/role-defaults.yaml`, d. h. es gibt keine selektierbare Rolle, die hier Aktion bräuchte. Der zweite Teil des Findings — `intern-developer` darf nie echte Arbeit erhalten — ist bereits umgesetzt: expliziter Verbotssatz im Template und `addressability: name_only` mit `name_only_reason` in `config/role-defaults.yaml:107-108`. Die separat getroffene Phase-H-Entscheidung 34 / D-H5 (`provider-expert` als `addressability: name_only` mit Grund registrieren) gehört zu Task 13 (Routing-Sprache, `config/role-defaults.yaml`) und wird hier **nicht** vorgezogen oder neu entschieden. Disposition: `verwerfen` für den Orphan-Befund, mit Verweis auf Task 13 für den Routing-Teil.

## 4. Umsetzungsgrenze und Trace

- Phasenplan-Task 14 (`:321-322`): Concept mit Dispositionen; Umsetzungstasks erst nach `Status: APPROVED` in einem Folgeplan; keine Template-Änderung in diesem Plan.
- Phasenplan-Task 0 (`:327-332`): dieses Konzept ist der gemeinsame Hintergrund für #1014; #1014 wird hier nicht geschlossen.
- Trace: Phasenplan `2026-11-11-phase-h-context-eval.md` Task 14 → dieses Konzept; F-1 → `SPEC-REFERENCE-STANDARDS-2026-09-15` (APPROVED); F-2/F-3/F-4/F-5/F-6 → Design-Gates D3/D4/D5/D7/D8 des Plans `2026-09-12-literature-anchored-agent-improvements-plan.md`.
- ADR-Bezug: Es werden keine neuen ADRs angelegt. Die hier angewendeten Trade-offs (Frontmatter-Feld vs. Freitext; zentrale Boundary vs. Template-Prosa; Review-Rules je Domäne vs. Mega-Index; Dokumentation vs. neuer MCP-Server) sind in den Design-Gates D2–D5 des genannten Plans mit Kontext, Optionen, Begründung und User-Freigabe vom 2026-09-13 bereits als Entscheidungsprotokoll festgehalten.

## 5. Offene Punkte / Decision point für main chat

- **Decision point für main chat (D-778-1): Ziel des Folgeplans für die Reste F-2/F-3/F-5.** Der Phasenplan sagt nur „ein Folgeplan" (`:321`) und nennt keinen Titel. Andere freigegebene Dokumente weisen #778 in die Loop-Rubrik: `docs/plans/2026-11-15-master-roadmap.md:61,223` (P30 / Batch 6.2–6.10, `#1014 #778`) und `docs/analysis/2026-11-15-fable-framework-settings-audit.md:233` (`#1014 + #778` in Loop-Plan §4 zusammenlegen). Das Konzept entscheidet **nicht**, ob die Restarbeit in einem separaten Phase-H-Folgeplan oder in der Loop-Rubrik landet; main chat legt den Ort fest. Beide Varianten ändern keine Disposition und keine der obigen file:line-Belege.
- **Verifikationshinweis (keine Entscheidung, F-4):** D5 verlangt ein separates MCP-Design-Issue als Deliverable (`:375,485,550`). Im Repo ist dafür keine Issue-Nummer und kein Beleg auffindbar; das Vorhandensein des externen Issues ist hier nicht prüfbar. Main chat kann das Follow-up bei Bedarf benennen; die Disposition bleibt `abspalten`.

## 6. Abdeckungs-Checkliste

- [x] Sechs Findings F-1..F-6, genau eine Disposition je Zeile (Tabelle §2).
- [x] Jede Zeile mit gegen `87564958` neu gemessenem file:line-Beleg.
- [x] Jede Disposition auf eine bereits freigegebene Entscheidung zurückgeführt (D2/D3/D4/D5/D7/D8, D-H5); keine neue Entscheidung, kein neues Feld, kein neues Format.
- [x] Keine Umsetzungsaufgabe in Phase H; Umsetzung ausschließlich nach APPROVED im Folgeplan.
- [x] Kein Bezug auf #1014-Durchführung, keine Schließung von #778, keine REQ-ID, keine Closing-Keywords.
- [x] Freigabe-Marker im Kopf exakt wie vom Nutzer vorgegeben (22.11, „keine neue Entscheidung").
