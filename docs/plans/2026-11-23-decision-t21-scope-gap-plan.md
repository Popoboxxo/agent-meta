---
pipeline_stages:
  implement: 2
---

# T21-Scope-Gap (#1167) Implementation Plan

> Status: geplant
> Klasse: **M** (Validator-/Gating-Scope + Golden-Rebaseline, kein Architektur-Change). Branch `fix/decision-points-bundle-20261123`, Anker `278ba54f`.

**Goal:** Den #1167-DoD-`req-traceability`-Gating-/Validator-Scope von 6 auf die gemessenen 24 DoD-Mandat-Agenten (D-Menge) erweitern, den neuen Render-Scan-Test über alle 24 D-Rollen grün machen und die Goldens byte-identisch nachziehen.
**Architecture:** Scope-Liste `GATED_AGENTS` (Tests) = D-Menge; Gating über `{{#if DOD_REQ_TRACEABILITY}}…{{else}}…{{/if}}` in den D-Templates; `REQ_ID_PATTERN`/`check_req_ids` bleiben unverändert (Non-Goal); S-/N-Klasse bleiben außerhalb von Gating und Validierung. Rebaseline ausschließlich über `scripts/rebaseline.py` / `lib.rebaseline` / `lib.rebaseline_pipeline` (Diff-Gate).
**Tech Stack:** Python 3.9+ (stdlib, PyYAML-Ausnahme), pytest, Sync-Renderer `scripts/sync.py`, Rebaseline-Helper `scripts/rebaseline.py`.
**Spec:** `docs/specs/2026-11-23-decision-t21-scope-gap-spec.md` (Trace-Anker `spec-id: SPEC-T21-SCOPE-GAP-1167-2026-11-23`, `status: APPROVED`, User-Marker 2026-11-23).

## Global Constraints

- **Messung ist autoritativ (ADR-1, R3):** Scope = exakt die 24 D-Dateien aus der Spec-Tabelle (194 Treffer/44 Dateien @ `278ba54f`). Die veraltete ~14-Dateien-Kandidatenliste wird nicht verwendet.
- **SE-Domäneninhalt geschützt (F1 RESOLVED, ADR-2, R2):** Die 14 S-Dateien (`REQ-L{n}`, `REQ-L1-SH`, `REQ-001-03`, `REQ-L2-AT-018`) und die 9 N-Dateien bleiben byte-identisch und werden weder gegated noch an `check_req_ids` übergeben. Ein Einbeziehen würde `Severity.ERROR`-Fehlalarme erzeugen und `tests/test_req_id_format.py::test_render_traceability_on_shows_canonical_format` (`:147-152`) brechen.
- **Regex/Format unverändert (IC-4, R4, Non-Goal):** `REQ_ID_PATTERN` bleibt byte-identisch `r"^REQ-[A-Z][A-Z0-9]*-\d{2,3}$"`; `check_req_ids` (`:92-96`), `DOD_REQ_TRACEABILITY`-Semantik, SE-Schema-Texte und Config-Keys werden nicht verändert.
- **Kein Test-Weakening, kein Hand-Guessing:** Goldens werden ausschließlich über den Helper-Pfad neu erzeugt; keine Assertions abgeschwächt, keine Golden-Datei manuell editiert.
- **TDD-Reihenfolge:**rotender Test zuerst → Gating/Scope implementieren → Goldens rebaselinen → Vollverifikation.
- **Kein #1167-Closing, keine Closing-Keywords** in Code, Commit-Messages oder Plan (Issue bleibt offen; nur Punkt 4 wird umgesetzt).
- **Commit-Authority:** Jeder Task endet mit einer Conventional-Commit-Message (Englisch); Ausführung und Secrets-Scan erfolgen durch Orchestrator/`git`, nicht durch diesen Plan. Push/Tag/Branch-Management bleiben beim `git`-Agenten.

## File Structure

- Modify: `tests/test_req_id_format.py` — neue D-Mengen-Konstante, `GATED_AGENTS`-Erweiterung (`:28-35`), neuer Render-Scan-Test (`:128-152`), Scope-Guard-Test; Helper `_render_project` (`:40-64`) ggf. um Plattform-Flags erweitern.
- Modify: `agents/2-platform/sharkord-developer.md`, `agents/2-platform/sharkord-release.md`, `agents/2-platform/homeassistant-documenter.md` — D-Mandate gaten (IC-2).
- Modify: `agents/1-generic/{validator,requirements,bug-feature-analyzer,junior-developer,senior-developer,principal-developer,tester,e2e-tester,api-specialist,git,orchestrator,ui-ux-designer,database-engineer,devops-engineer,refactoring-specialist,data-engineer,documenter,_reference-agent,se-developer,se-junior-developer,se-senior-developer}.md` — 21 D-Templates gaten (davon 3 gemischt D+S; nur D-Stellen gaten, S-Texte unangetastet).
- Reference (unverändert): `scripts/lib/consistency/req_format.py` — `REQ_ID_PATTERN` (`:32`), `check_req_ids` (`:92-96`) bleiben byte-identisch (IC-4).
- Modify (generiert, nicht hand-editiert): `tests/fixtures/slimming-golden/*.md`, `tests/fixtures/compact-golden/*`, `tests/fixtures/topology-golden/*`, `tests/fixtures/ac01-baseline/hashes.json`, `.meta-config/generated-file-hashes.json`, `.meta-config/context-hashes.json`, `tests/test_context_budgets.py` — Rebaseline-Pin-Set (IC-5, `lib/rebaseline.py:256-309`).
- Reference (unverändert): 14 S-Dateien (`agents/1-generic/se-requirements.md`, `se-component-requirements.md`, `se-architect.md`, `se-critic.md`, `se-verifier.md`, `se-validator.md`, `se-test-engineer.md`, `se-testreviewer.md`, `se-termination.md`, `se-interface-mgr.md`, `se-integration-and-test-manager.md`, plus die S-Anteile in `se-developer.md`/`se-junior-developer.md`/`se-senior-developer.md`).

## 24 D-Agenten (Basis = Spec-Messung @ 278ba54f, IC-1)

`sharkord-developer`, `sharkord-release`, `homeassistant-documenter`, `validator`, `requirements`, `bug-feature-analyzer`, `junior-developer`, `senior-developer`, `principal-developer`, `tester`, `e2e-tester`, `api-specialist`, `git`, `orchestrator`, `ui-ux-designer`, `database-engineer`, `devops-engineer`, `refactoring-specialist`, `data-engineer`, `documenter`, `_reference-agent`, `se-developer`, `se-junior-developer`, `se-senior-developer`.

Obermenge der alten 6 Rollen (`validator`, `bug-feature-analyzer`, `requirements`, `se-requirements`, `se-developer`, `api-specialist`) — mit der Korrektur, dass `se-requirements` S-Klasse ist und **nicht** in der D-Menge steht; stattdessen kommen die 19 weiteren D-Rollen hinzu. Keine S-/N-Rolle in der Liste.

---

## Task 1: Roten Render-Scan-Test über alle 24 D-Rollen schreiben

**Rolle:** `tester`
**Files:** Modify `tests/test_req_id_format.py` (einzige Datei dieses Tasks)
**Interfaces:**
- Produces: `D_AGENTS: tuple[str, ...]` (24 Namen, authoritative Konstante), Tests `test_gated_agents_matches_measured_d_set`, `test_render_all_gated_agents_no_ungated_req_mandate`, `test_se_domain_and_neutral_roles_excluded_from_gating`.
- Consumes: Spec-Messung (D-Tabelle), `tests/test_req_id_format.py:19-64` (`_REPO_ROOT`, `_render_project`, `_rendered_agent`), CANONICAL_FORMAT (`:37`), `GATED_AGENTS` (`:28-35`, noch 6 Rollen).

- [ ] Step 1: `D_AGENTS` als `tuple[str, ...]` mit exakt den 24 D-Namen (Abschnitt „24 D-Agenten") in `tests/test_req_id_format.py` ergänzen; `_render_project` (`:40-64`) falls nötig um die Plattform-/Provider-Flags erweitern, damit `_rendered_agent` für jede der 24 Rollen ein gerendertes Artefakt liefert (sonst ist der Scan nicht aussagekräftig).
- [ ] Step 2: `test_gated_agents_matches_measured_d_set`: `set(GATED_AGENTS) == set(D_AGENTS)` und `len(GATED_AGENTS) == 24` asserten → muss jetzt rot werden (alt: 6). (AC1)
- [ ] Step 3: `test_render_all_gated_agents_no_ungated_req_mandate`: für `D_AGENTS` bei `traceability=False` rendern und asserten, dass kein ungatedes `CANONICAL_FORMAT`, kein `(REQ-xxx): <description>` und keine IC-2-Mandat-Strings (`(REQ-ID needed)`, `for a REQ-ID, then`) im gerenderten Text vorkommen; bei `traceability=True` asserten, dass `CANONICAL_FORMAT` in jedem gerenderten D-Agenten erscheint → muss jetzt rot werden (D-Mandate teils ungated, IC-2). (AC2)
- [ ] Step 4: `test_se_domain_and_neutral_roles_excluded_from_gating`: asserten, dass keine S-/N-Rolle (namentlich `se-requirements`, `se-component-requirements`, `se-architect`, `se-critic`, `se-verifier`, `se-validator`, `se-test-engineer`, `se-testreviewer`, `se-termination`, `se-interface-mgr`, `se-integration-and-test-manager`, `ideation`, `developer`, `planner`, `ux-researcher`, `risk-based-audit-planner`, `product-manager`, `concept-specifier`, `concept-reviewer`, `concept-architect`) in `D_AGENTS` vorkommt → grün (Schutztest). (AC3)
- [ ] Step 5: Rot-Nachweis festhalten: `python3 -m pytest tests/test_req_id_format.py -q` läuft, die zwei neuen Rot-Tests sind explizit als FAIL protokolliert (nur grüne Unit-Tests annehmen ist unzulässig).
- [ ] Step 6: Commit (nach Secrets-Scan durch Orchestrator): `test: add failing 24-agent REQ gating render scan (#1167)`

## Task 2: Scope-Liste und D-Template-Gating erweitern (Implementierung)

**Rolle:** `developer`
**Files:** Modify `tests/test_req_id_format.py` (`GATED_AGENTS`); Modify die 24 D-Templates aus „File Structure" (3 `2-platform` + 21 `1-generic`)
**Interfaces:**
- Produces: `GATED_AGENTS == D_AGENTS` (24 Rollen); gated D-Mandate in `agents/**/*.md` gemäß IC-2; `REQ_ID_PATTERN` unverändert.
- Consumes: Task-1-Artefakte `D_AGENTS` + rotender Render-Scan; `req_format.py:32` (Regex, read-only); `validator.md:35-41` als Gating-Muster; IC-2-Referenzstellen `validator.md:38,39`, `tester.md:40,43,44,49`, `e2e-tester.md:67`, `requirements.md:44,47`, `_reference-agent.md:174`, `sharkord-developer.md:92,96`.

- [ ] Step 1: `GATED_AGENTS` (`:28-35`) auf die 24 D-Rollen setzen (z. B. `GATED_AGENTS = D_AGENTS`), sodass `test_gated_agents_matches_measured_d_set` grün wird; `se-requirements` dabei entfernen. (AC1)
- [ ] Step 2: In allen 24 D-Templates die REQ-**Mandate** (nicht die deskriptiven Erwähnungen aus IC-2) in `{{#if DOD_REQ_TRACEABILITY}}…{{else}}…{{/if}}` einschließen; im an-Zustand nur kanonisches `REQ-<AREA>-<NN>` (`\d{2,3}`) verwenden. (AC2)
- [ ] Step 3: In den 3 gemischten Dateien (`se-developer.md`, `se-junior-developer.md`, `se-senior-developer.md`) ausschließlich die D-Stellen gaten; alle `REQ-L{n}`/`REQ-L1-SH`/`REQ-001-03`-Strings unverändert lassen. (AC3)
- [ ] Step 4: `REQ_ID_PATTERN` (`:32`) und `check_req_ids` (`:92-96`) per Byte-Vergleich gegen den Anker bestätigen – keine Änderung; `test_valid_ids_pass_both_states`, `test_multi_part_area_rejected`, `test_four_digit_rejected` bleiben grün. (AC4)
- [ ] Step 5: `python3 -m pytest tests/test_req_id_format.py -q` → alle Tests grün, inkl. `test_render_all_gated_agents_no_ungated_req_mandate` und `test_render_traceability_on_shows_canonical_format` über alle 24 Rollen.
- [ ] Step 6: `python3 scripts/sync.py --validate` → keine neuen `req-id.format`-Findings.
- [ ] Step 7: Commit (nach Secrets-Scan): `feat: gate REQ mandate across all 24 measured D agents (#1167)`

## Task 3: Goldens über den erlaubten Helper-Pfad rebaselinen

**Rolle:** `developer`
**Files:** Modify (generiert): `tests/fixtures/slimming-golden/*.md`, `tests/fixtures/compact-golden/*`, `tests/fixtures/topology-golden/*`, `tests/fixtures/ac01-baseline/hashes.json`, `.meta-config/generated-file-hashes.json`, `.meta-config/context-hashes.json`, `tests/test_context_budgets.py`
**Interfaces:**
- Produces: Byte-identische Golden-/Hash-Pins zum frischen Render; Rebaseline-Log-Eintrag.
- Consumes: Task-2-Gating-Änderung; `scripts/rebaseline.py` (`--reason`/`--base`/`--check-only`/`--expect`), `lib/rebaseline.py::PINS` (`:256-309`), `lib/rebaseline_pipeline.py::run_pipeline`, Pin-Tests `tests/test_rebaseline_helper.py`.

- [ ] Step 1: Preflight `python3 scripts/rebaseline.py --check-only --root .` → meldet die durch Task 2 betroffenen Pins, schreibt nichts.
- [ ] Step 2: `python3 scripts/rebaseline.py --root . --base 278ba54f --reason "T21 scope-gap: D-agent gating golden rebaseline" --json` ausführen; der Helper rendert via `sync.py` und schreibt ausschließlich das erlaubte Pin-Set (IC-5, `lib/rebaseline.py:256-309`; `tests/test_rebaseline_helper.py:257-265`). **Nicht** `--skip-verify` verwenden; keine Datei manuell editieren; keine Assertion abschwächen.
- [ ] Step 3: Helper-Report prüfen: `gate=ok`, `verify=ok`, `idempotent=true`, `RESULT changed=<n> files`, keine `RESIDUAL`/unerlaubten Pfade; bei Pfad-Violation stattdessen explizit `--expect`/`--expect-key` mit dem betroffenen erlaubten Muster ergänzen und erneut laufen lassen (nie den Gate deaktivieren).
- [ ] Step 4: `python3 -m pytest tests/test_rebaseline_helper.py -q` → alle Helper-Tests grün; `tests/fixtures/slimming-golden/{validator,tester,requirements,e2e-tester,git,orchestrator,sharkord-developer,sharkord-release,homeassistant-documenter}.md` spiegeln den neuen Render.
- [ ] Step 5: Commit (nach Secrets-Scan): `chore: rebaseline goldens for T21 D-agent gating (#1167)`

## Task 4: Vollverifikation / AC-Abnahme

**Rolle:** `tester`
**Files:** Read-only verification (keine Datei-Modifikation); Test `tests/test_req_id_format.py` + `tests/test_rebaseline_helper.py` + `scripts/sync.py --validate`
**Interfaces:**
- Produces: AC1-AC5 Abnahme-Report.
- Consumes: alle Artefakte aus Task 1-3; `REQ_ID_PATTERN` (`:32`); 14 S-Dateien (Schutz gegen unbeabsichtigte Änderung).

- [ ] Step 1: `python3 -m pytest tests/test_req_id_format.py tests/test_rebaseline_helper.py -q` → alle grün. (AC1-AC4)
- [ ] Step 2: `python3 scripts/sync.py --validate` → Exit 0, keine neuen Findings; `REQ-CMD-01`/`REQ-COM-123` gültig, `REQ-1`/`REQ-COM-1234`/`REQ-L2-AT-018` ungültig. (AC4)
- [ ] Step 3: `python3 scripts/rebaseline.py --check-only --root .` → keine offenen/residualen Pin-Drifts mehr. (AC5)
- [ ] Step 4: Byte-Vergleich der 14 S-Dateien gegen Anker `278ba54f` (`git diff --exit-code -- <S-Pfade>`) → keine Änderung; `check_req_ids` meldet für `REQ-L1-SH`/`REQ-L2-AT-018` keine `req-id.format`-Findings. (AC3)
- [ ] Step 5: Self-Review gegen die Spec abhaken; Plan-Status auf `complete` setzen (vom Orchestrator), ohne #1167 zu schließen.

## Acceptance-Criterion-Abdeckung

| AC | Task(s) | Nachweis |
|---|---|---|
| AC1 — vollständiger Scope (24 D-Rollen, keine S/N) | 1 Step 2, 2 Step 1, 4 Step 1 | `test_gated_agents_matches_measured_d_set`; `GATED_AGENTS == D_AGENTS` (24) |
| AC2 — Gating korrekt (aus: kein Mandat; an: kanonisch) | 1 Step 3, 2 Step 2, 4 Step 1 | `test_render_all_gated_agents_no_ungated_req_mandate` + `test_render_rapid_prototyping_has_no_req_mandate` + `test_render_traceability_on_shows_canonical_format` über alle 24 |
| AC3 — SE-Inhalt geschützt (14 S-Dateien) | 1 Step 4, 2 Step 3, 4 Step 4 | `test_se_domain_and_neutral_roles_excluded_from_gating`; Byte-Vergleich S-Dateien; keine `req-id.format`-Findings für S-Strings |
| AC4 — kein Format-Regress (Regex byte-identisch) | 2 Step 4, 4 Step 1-2 | `REQ_ID_PATTERN == r"^REQ-[A-Z][A-Z0-9]*-\d{2,3}$"`; bestehende Format-Tests grün; `sync.py --validate` Exit 0 |
| AC5 — Goldens byte-identisch | 3 Step 1-4, 4 Step 3 | Rebaseline-Helper `gate=ok/verify=ok/idempotent=true`; `--check-only` ohne Residual; Helper-Tests grün |

## Self-Review

- Jeder Task mappt auf genau eine Rolle (`tester`, `developer`); jeder Task hat ≥1 Test und eine Conventional-Commit-Message. ✔
- `Files:`/`Interfaces:` vollständig, mit Datei:Symbol:Signatur; Dateiüberlappung nur zwischen Task 1 und Task 2 an `tests/test_req_id_format.py` und ist strikt sequenziell (keine Parallel-Gruppe). ✔
- `pipeline_stages: implement: 2` zeigt auf den ersten Implementierungs-Task; die einzige plan-driven Stage der Pipeline ist `implement` (feature-lifecycle). ✔
- AC1-AC5 sind je mindestens einem Task und einem messbaren Test zugeordnet (Tabelle oben). ✔
- Keine `TODO`/`TBD`/`…` als Platzhalter; Pfade, Symbole, Signaturen und Commit-Messages sind konkret (`REQ-<AREA>-<NN>` ist der literale Format-String, kein Platzhalter). ✔
- Spec-Non-Goals eingehalten: Regex/Format, SE-Schema-Texte, Config-Keys, #1167-Status unverändert; keine Closing-Keywords. ✔
- F1 (S/N ausgeschlossen) und R1-R4 (Scope, Domäneninhalt, Anker, Regex) durch Tasks/ACs abgedeckt; Rot-Nachweis in Task 1 Step 5 verpflichtend. ✔

## Annahmen / Re-Planning

- **A1 (Render-Abdeckung):** Alle 24 D-Rollen werden im Scratch-Projekt von `_render_project` tatsächlich nach `.claude/agents/<role>.md` gerendert. Falls `_reference-agent` oder die `2-platform`-Rollen dort nicht erscheinen, ist Task 1 Step 1 (Config/Helper-Erweiterung) anzupassen — sonst ist der Render-Scan nicht aussagekräftig und AC2 ungültig.
- **A2 (Scope-Autorität):** Die Spec-Messung (194/44 @ `278ba54f`) ist die einzige Scope-Quelle. Wenn der Branch-Stamm abweicht, vor Task 1 neu messen und den Plan aktualisieren (R3).
- **A3 (Helper-Gate):** Der Rebaseline-Helper akzeptiert das Pin-Set ohne `--expect`-Erweiterung. Falls nicht, Task 3 Step 3 mit explizitem erlaubtem Muster wiederholen — nie den Gate abschalten.
- Re-Planning nach jedem Task (insbesondere nach Task 2 und Task 3): Annahmen prüfen, Reihenfolge validieren, Plan fortschreiben — nicht als statisch behandeln.

## Estimated effort

Aufwandsschätzung gemäß `effort-estimator` (Text-Referenz, kein Tool-Aufruf): Klasse **M**, ~24 Template-Edits + 1 Test-Datei + 1 Helper-Rebaseline + Vollverifikation; überwiegend mechanischer Gating-/Golden-Aufwand bei klarer Spec-Vorgabe.
