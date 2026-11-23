# Spec-Review — Doctor-Consistency-Check für unbekannte Tool-Namen (#1323)

- Reviewed artifact: `docs/specs/2026-11-23-decision-1323-doctor-check-spec.md` (frontmatter `spec-id: SPEC-DOCTOR-UNKNOWN-TOOL-NAME-1323`, `status: APPROVED`, `approval: "User, 2026-11-23, Einzelentscheidung"`; IC-1..6, AC-1..6, ADR-1323-1..3, Q1)
- Branch / Anker-Basis: `fix/decision-points-bundle-20261123`, Referenz-Commit `278ba54f` (vom Spec selbst benannt)
- Approval basis: BINDENDE User-Entscheidung 23.11 (non-destructiver Doctor-/Consistency-Check, Option A; kein Deny-List-Inversion, kein doc-only)
- Modus: Spec-Review (Master-Rule `spec-plan-workflow`, §8) + 7-Dimensionen-Critic. Read-only bzgl. der reviewed Spec; kein Edit am Spec, kein Commit.

## Scope

Prüfung der sechs Fokuspunkte: (1) Marker + Frontmatter, (2) USER-Entscheidung kodiert, (3) Q1 — deferrable oder BLOCKER, (4) Non-destructive-Vertrag, (5) Anker plausibel, (6) keine Closing-Keywords/Placeholder. Zusätzlich Pflichtsektionen, Trace-Anker, Approval-Marker, No-Placeholder nach §8.

### Mandatory-section check (spec-plan-workflow §8)
- Pflichtsektionen: Problem/Ziel/Nicht-Ziele (:10-20), Interface Contracts (:22-35), Datenfluss (:37-39), Acceptance Criteria (:41-50), Offene Fragen + Risiken (:52-58) — alle vorhanden. PASS
- Trace-Anker: `spec-id: SPEC-DOCTOR-UNKNOWN-TOOL-NAME-1323` in Frontmatter (:2) und Trace-Anker-Sektion (:76), konsistent. PASS
- Approval-Marker: `> Status: APPROVED (User, 2026-11-23, Einzelentscheidung)` (:8) + Frontmatter `status: APPROVED` (:3), genau 1× im Body, untereinander konsistent. PASS bzgl. Vorhandensein — ABER inkonsistent zum Review-Stand (siehe major-1).
- No-Placeholder: kein TODO/TBD/FIXME/`{{...}}`/`<...>` in Pflichtsektionen (grep: keine Treffer). Keine Closing-Keywords (`closes/fixes/resolves #…`: keine Treffer). Unaufgelöste Punkte sind als Q1 mit "nicht erfunden" markiert. PASS

## Findings by severity

### critical-1 / BLOCKER — Q1: Candidate-Seite hat keine erlaubte, definierte Datenquelle (Dimension: Logic gaps / Feasibility / Completeness)
- `load_expected_tool_names(agent_meta_root: Path) -> frozenset[str]` (Contract 1, :28) ist die komplette Harness-/Candidate-Seite und damit der **wesentliche Input** der Unknown-Differenz `expected - known - deliberately_rejected`. Ohne definierte Quelle gibt es nichts, das gegen die Allow-List differenziert werden kann.
- Die Spec setzt vier gleichzeitig nicht vereinbare Aussagen:
  - (a) Signatur von `load_expected_tool_names` ist fixiert (:28, :54);
  - (b) zur Laufzeit ist **kein Import aus `tests/`** erlaubt (:54);
  - (c) es wird **keine Config-Quelle erfunden** (:54);
  - (d) "Bis zur Entscheidung ist der Check gegen den Snapshot lauffähig" (:54).
- Verifiziert: Der einzige In-Repo-Snapshot der Candidate-Namen ist `_DOCUMENTED_CLAUDE_TOOLS` in `tests/test_hook_common_lib.py:394` (grep über alle `*.py`: keine nicht-testliche Kopie, kein Feed, kein `load_expected_tool_names`). Der Audit-Log führt nachweislich keine `tool_name`-Records (`tests/test_hook_common_lib.py:333-336`). Es gibt also keinen erlaubten Weg, (d) zu erfüllen, ohne (b) zu verletzen oder genau die vertagte Owner-Entscheidung (a) „gemeinsame, nicht-testliche Konstante aus der Provider-Doku pflegen" (Q1-Option a, :54) zu treffen.
- Wirkung: Ein Implementierer kann Contract 1 nicht schreiben, ohne eine explizite Constraint zu brechen oder die als offen markierte Entscheidung selbst zu treffen. Das ist ein logischer/completeness Gap im Kern des Designs, kein Feinschliff.
- Improvement: Q1 vor Implementierung auflösen — konkret die Stopgap-Quelle für `load_expected_tool_names` festlegen (Payload-Ort + Pflege-Owner), z. B. "nicht-testliche Konstante im neuen Modul, gespiegelt aus der Provider-Doku, Update-Pflicht bei Doku-Änderung" — und den Satz "kein Import aus tests/" mit "lauffähig gegen den Snapshot" in Einklang bringen. Danach ist der Rest der Spec implementierbar.

### major-1 — Approval-Marker steht im Widerspruch zum Review-Stand / zur offenen BLOCKER-Entscheidung (Dimension: Consistency, §8 Approval-Marker)
- Frontmatter `status: APPROVED` (:3) und Body-Marker `> Status: APPROVED (User, 2026-11-23, Einzelentscheidung)` (:8) behaupten Freigabe, während Q1 (critical-1) eine ungelöste, blockierende Entscheidung ist und das Review BLOCKED vergibt. §8 verlangt Konsistenz des Approval-Markers zum Review-Stand.
- Improvement: Marker auf `Status: Entwurf` setzen, bis Q1 entschieden und die Spec erneut reviewed ist; danach auf `APPROVED (Datum)` heben. Die BINDENDE User-Entscheidung 23.11 (Option A) bleibt davon unberührt — sie betrifft den Lösungsweg, nicht die Offenheit von Q1.

### minor-1 — Interne Anker-Inkonsistenz für `_DOCUMENTED_CLAUDE_TOOLS` (Dimension: Consistency)
- Tabelle Contract 5 (:32) nennt `:394-405`, Datenfluss (:39) und Contract 1 (:28) nennen `:394-404`; die Konstante belegt real die Zeilen 394-404, `_DELIBERATELY_REJECTED` steht in :405.
- Improvement: einheitlich `:394-404` (Konstante) und `:405` (`_DELIBERATELY_REJECTED`) schreiben. Reine Präzisierung, nicht blockierend.

### info — Verifizierte Positive
- USER-Entscheidung vollständig kodiert: Nicht-Ziele (:16-20) schließen Deny-List-Inversion (Option B), doc-only und `rc != 0` / `--strict`-Eskalation explizit aus; ADR-1323-1..3 (:62-64) spiegeln Option A, INFO statt WARNING, kein Runtime-Eingriff. Kein Widerspruch zur Binding-Entscheidung gefunden.
- Non-destructive-Vertrag plausibel und korrekt verankert: `print_report()` leitet rc ausschließlich aus `Severity.ERROR` ab (`report.py:50`, `:75` `return 1 if errors else 0`); `_doctor_exit_code()` (`cli_commands.py:1432-1443`) eskaliert nur registry-invalid (strict, →2), ERROR (→1) und strict-WARNING (→1). Ein INFO-Finding bleibt in `--validate`, `--audit-config`, `--doctor` und `--doctor --strict` bei rc 0. Kein Blocking-Pfad, keine Persistenz, kein Hook-/Guard-Input (Contract 4).
- Anker gegen `278ba54f` allesamt plausibel: `hook_common.sh:189-213` / `:210` (SubagentHandback) / `:5` (Changelog v1.8.1, Version aktuell 1.10.0); beide Guards read-only; `cli_commands.py:1663-1686` (`_strict_findings`, `check_stale_deployed_hooks` :1671, `check_hook_enablement_consistency` :1676); `doctor_detectors.py:475-479` (Hooks-Branch ruft nur `check_hook_enablement_consistency`) und `:49-52` (`_CHECK_MODULES` ohne `consistency`-Producer); `doctor_registry.py:45` (`consistency`/`hooks` als FINDING_SOURCES erlaubt); `known-issues.yaml:380-391` (Registry-Eintrag `hooks-not-registered` als Nachbar); Tests `:394-405` / `:408-412` / `:333`. AC-4 (0 Findings bei 278ba54f) ist konsistent: alle `_DOCUMENTED_CLAUDE_TOOLS` sind im Allow-List-Case vorhanden, Worktree-Paar ist `_DELIBERATELY_REJECTED`, MCP-Wildcard `:192` ist kein Literal.

## Q1 — explizite Stellungnahme

**Q1 ist nicht genuiner vertagbarer Punkt, sondern BLOCKER.** Die Candidate-/Harness-Seite (`load_expected_tool_names`) ist der zentrale Eingang des Checks; ohne definierte, erlaubte Quelle ist Contract 1 nicht implementierbar. Die Spec verbietet den Import aus `tests/` (dort liegt der einzige Snapshot), erfindet keine Config-Quelle, behauptet aber gleichzeitig die Lauffähigkeit „gegen den Snapshot". Diese drei Aussagen sind nicht gleichzeitig erfüllbar; der Implementierer müsste entweder die Constraint brechen oder genau die als offen markierte Owner-Entscheidung (a) treffen. Erst wenn die Stopgap-Quelle (Payload-Ort + Pflege-Owner) in der Spec fixiert ist, ist die Spec tragfähig. Es wird keine Quelle erfunden und keine Entscheidung im Namen des Owners getroffen.

## Verdict + rationale

**BLOCKED** — critical-1: Die Spec ist im Kern (Contract 1 / Candidate-Seite) nicht implementierbar, weil die Datenquelle für `load_expected_tool_names` zugleich fixiert, verboten (tests/) und undefiniert (keine Config-Quelle) ist, während sie als lauffähig behauptet wird. major-1 verschärft dies durch einen APPROVED-Marker trotz ungelöster blockierender Entscheidung. Alle übrigen Fokuspunkte (USER-Entscheidung, Non-destructive-Vertrag, Anker, No-Placeholder/Closing-Keywords) sind sauber nachgewiesen. Nach Auflösung von Q1 (konkrete Stopgap-Quelle + Marker auf Entwurf) ist das Review erneut durchzuführen; die Binding-Entscheidung selbst steht nicht zur Disposition.

Counts: critical 1 · major 1 · minor 1 · info 1.

Commit note (Trigger: task-boundary, Review-Artefakt; Caller führt vor Commit den Secret-Scan aus, kein Push/Tag/Branch):
`docs: add #1323 doctor-check spec review (BLOCKED: Q1 source)`
