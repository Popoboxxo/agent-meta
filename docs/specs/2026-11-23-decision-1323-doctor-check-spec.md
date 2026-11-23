---
spec-id: SPEC-DOCTOR-UNKNOWN-TOOL-NAME-1323
status: Entwurf
approval: "User, 2026-11-23, Einzelentscheidung"
implementation-blocked: "Review BLOCKED (2026-11-23) — Q1: Datenquelle der erwarteten Tool-Namen ungeklärt; User-Entscheidung Option A bleibt bindend"
---

# Doctor-Consistency-Check für unbekannte Tool-Namen (#1323) — Spec
> Status: Entwurf (Review BLOCKED — Q1 Datenquelle der erwarteten Tool-Namen ungeklärt; User-Entscheidung Option A bleibt bindend)

## Problem / Ziel / Nicht-Ziele

**Problem (Issue #1323, Evidenz):** `hook_known_tool_name` (`hooks/1-generic/lib/hook_common.sh:189-213`) ist eine handgepflegte Closed Allow-List, die beide Fail-Closed-Guards vor der Tool-Klassifikation konsultieren. Drei identische Staleness-Fälle: #1055 (`Agent`, `SendMessage`, v1.6.0), #1078 (`ToolSearch` + 14 Built-ins, v1.8.0), #1323 (`SubagentHandback`, Immediate-Fix v1.8.1 — `hook_common.sh:5`, `:210`). Jeder neue Harness-Built-in blockiert bis zur nächsten Bug-Meldung den Handoff-Kanal; #1078 hatte den Doctor-Check bereits als Follow-up benannt, er wurde nie gebaut. Der Audit-Log enthält keine `tool_name`-Records (`tests/test_hook_common_lib.py:333`) — Staleness ist heute nur reaktiv sichtbar.

**Ziel:** Nicht-destruktiver Doctor-/Consistency-Check, der die Harness-/Doku-Toolnamen gegen die Allow-List differenziert und unbekannte Namen als INFO-Finding sichtbar macht — proaktiv, ohne Laufzeit- oder Exit-Code-Änderung.

**Nicht-Ziele (BINDENDE User-Entscheidung 23.11):**
- **Keine Deny-List-Inversion** (Issue-Option B): die Guards behalten die Closed Allow-List und fail-closed für unbekannte Namen.
- **Kein reines Dokumentieren**: es entsteht ein ausführbarer, testbarer Check, kein Hinweistext.
- **Kein „failing sync"** (Issue-Option-A-Variante): kein ERROR, kein WARNING, kein `rc != 0`, kein Blockieren — auch nicht unter `--doctor --strict`.
- Keine Änderung an `hook_known_tool_name`-Semantik, Guard-Exit-Codes oder generierten Hook-Kopien; keine Implementierung in diesem Schritt.

## Interface Contracts

Alle Anker gegen Referenz-Commit `278ba54f` neu gemessen (Checkout `fix/decision-points-bundle-20261123`).

| # | Datei:Symbol | Signatur / Typ | Rolle & Fehlerpfad |
|---|---|---|---|
| 1 | `scripts/lib/consistency/hook_known_tool_names.py` (neu): `parse_known_tool_names`, `load_expected_tool_names`, `check_unknown_tool_names` | `parse_known_tool_names(source_text: str) -> frozenset[str]`; `load_expected_tool_names(agent_meta_root: Path) -> frozenset[str]`; `check_unknown_tool_names(project_root: Path, agent_meta_root: Path, config: dict, provider_config: dict) -> list[Finding]` | Known-Set = Case-Literale aus `hook_common.sh:189-213` (MCP-Wildcard `:192` kein Literal, Worktree-Paar bewusst ausgenommen). Unknown = `expected - known - deliberately_rejected`. Finding: `Severity.INFO`, `check="hooks.unknown-tool-name"`, `file="hooks/1-generic/lib/hook_common.sh"`, Message nennt den Tool-Namen, Suggestion nennt `hook_known_tool_name`. Fail-soft: unlesbares/nicht parsbares Source ⇒ `[]` (oder INFO `doctor.detector-unavailable`), nie `raise`, nie ERROR. |
| 2 | `scripts/lib/cli_commands.py:1663-1686` (`_strict_findings`-Block, `--validate`/`--audit-config`) | `_strict_findings += check_unknown_tool_names(project_root, agent_meta_root, config, _provider_config)` | Neben `check_stale_deployed_hooks` (`:1671`) und `check_hook_enablement_consistency` (`:1676`) einhängen. Kein `consistency_errors +=`: `print_report()` (`scripts/lib/consistency/report.py:44-75`) leitet den rc nur aus ERROR ab ⇒ rc 0. |
| 3 | `scripts/lib/doctor_detectors.py:475-479` (`_raw_findings`, Branch `source == "hooks"`) + `config/known-issues.yaml` (neuer Eintrag neben `:380-391`) | Registry-Eintrag `id: hooks-unknown-tool-name`, `detector: {kind: finding-ref, check: hooks.unknown-tool-name, source: hooks}`, `severity: INFO`; der Hooks-Branch dispatcht den Check zusätzlich zum bestehenden `check_hook_enablement_consistency` | `--doctor`-Sichtbarkeit. INFO bleibt auch in `_doctor_exit_code` (`cli_commands.py:1432-1443`) und unter `--strict` bei rc 0. |
| 4 | `hooks/1-generic/lib/hook_common.sh:189-213` (`:210` `SubagentHandback`; `:5` Changelog v1.8.1); `hooks/1-generic/orchestrator-guard-impl.sh:274-279`; `hooks/1-generic/repo-containment-impl.sh:263-266` | read-only | Source of Truth für den Known-Set; Guard-Fail-Closed (exit 2) bleibt unverändert. `.agents/hooks/lib/hook_common.sh` ist generierte Kopie — nicht editieren. |
| 5 | `tests/test_hook_common_lib.py:394-404` `_DOCUMENTED_CLAUDE_TOOLS`, `:405` `_DELIBERATELY_REJECTED`, `:408-412` Parity-Test | `tuple[str, ...]` | Einzige heute im Repo vorhandene Enumeration der Harness-Built-ins (Snapshot der Provider-Doku, Stand 2026-11-06). Siehe OFFENE FRAGE Q1 — kein Import aus `tests/` zur Laufzeit. |
| 6 | `tests/test_hook_known_tool_names_consistency.py` (neu) | pytest | Deckt AC-1 bis AC-4 ab; Muster `tests/test_hook_drift.py`. |

Fehlerpfade konsolidiert: unbekannter Tool-Name ⇒ INFO-Finding, rc 0; Source fehlt/nicht parsbar ⇒ leere Findings, rc 0; Guard-E2E für echte Unbekannte ⇒ unverändert exit 2.

## Datenfluss

`hook_common.sh:189-213` (Case-Literale) + Candidate-Set (Q1) → `parse_known_tool_names` / `load_expected_tool_names` → Differenz `expected - known - deliberately_rejected` → `Finding(INFO, "hooks.unknown-tool-name", file, message, suggestion)` → `cli_commands.py:1663-1686` (`_strict_findings`) → `print_report()` mit rc 0; parallel `config/known-issues.yaml` → `doctor_detectors.py:475-479` → Doctor-Report mit rc 0. Keine Persistenz, keine Hook-Änderung, kein Rebaseline (der Spec ändert keine per Hash gepinnte Hook-Datei).

## Acceptance Criteria (nummeriert, testbar — Given/When/Then)

1. **AC-1 (Unknown → Finding):** Given ein im Candidate-Set vorhandener, in `hook_known_tool_name` fehlender Name (Test-Fixture `FutureTool`), When `check_unknown_tool_names(project_root, agent_meta_root, config, provider_config)` läuft, Then gibt es genau 1 Finding mit `check == "hooks.unknown-tool-name"`, `severity == INFO`, dem Tool-Namen in `message`, dem `hook_common.sh`-Pfad in `file` und `hook_known_tool_name` in `suggestion`. *(Contract 1.)*
2. **AC-2 (Non-destructive Validate):** Given dieses Finding, When `python3 scripts/sync.py --validate` und `--audit-config` laufen, Then exit 0, kein `consistency_errors`-Inkrement, keine Datei geändert. *(Contracts 1, 2.)*
3. **AC-3 (Doctor + `--strict`):** Given dasselbe Finding im Doctor-Report, When `python3 scripts/sync.py --doctor --strict` läuft, Then rc 0 und das Finding ist als `INFO` gelistet (`_doctor_exit_code` eskaliert nur ERROR bzw. strict-WARNING). *(Contracts 1, 3.)*
4. **AC-4 (Clean bei 278ba54f):** Given der aktuelle Source-Stand, When der Check läuft, Then 0 Findings — `SubagentHandback` (`:210`) und alle `_DOCUMENTED_CLAUDE_TOOLS` sind known; `EnterWorktree`/`ExitWorktree` sind via `_DELIBERATELY_REJECTED` ausgenommen; die MCP-Wildcard erzeugt kein Literal-Finding. *(Contracts 1, 4, 5.)*
5. **AC-5 (Guard-Semantik):** Given ein wirklich unbekannter `tool_name` im PreToolUse-Payload, When einer der Guards läuft, Then blockt er weiter mit exit 2 und der bestehenden M2-Meldung — der Check fügt keinen Allow-Eintrag hinzu. *(Contract 4.)*
6. **AC-6 (Regression):** Given `tests/test_hook_known_tool_names_consistency.py`, When pytest läuft, Then bestehen die AC-1-bis-AC-4-Tests und keine bestehenden Hook-/Doctor-Tests ändern ihre Erwartungen. *(Contract 6.)*

Jede AC mappt auf mindestens einen Interface-Contract.

## Offene Fragen + Risiken

**Q1 (eskalieren, nicht erfunden): Source of Truth für die Harness-/Candidate-Seite.** Es gibt keinen maschinenlesbaren Provider-Tool-Feed im Repo (Issue #1078: kein Treffer in `config/`); die einzige In-Repo-Enumeration ist der handgepflegte Snapshot `_DOCUMENTED_CLAUDE_TOOLS` (`tests/test_hook_common_lib.py:394`, Doku-Stand 2026-11-06), und der Audit-Log führt keine `tool_name`-Records (`:333`). Der Spec fixiert den **Contract** (`load_expected_tool_names(agent_meta_root: Path) -> frozenset[str]` liefert die Namen, die die Harness in `tool_name` senden kann) und verpflichtet zur Laufzeit auf **keinen Import aus `tests/`**, erfindet aber keine Config-Quelle. Owner-Entscheidung nötig: (a) gemeinsame, nicht-testliche Konstante aus der Provider-Doku pflegen, (b) `ToolSearch`-Output als Feed, (c) `tool_name` in den Guard-Audit-Log aufnehmen. Bis zur Entscheidung ist der Check gegen den Snapshot lauffähig; Snapshot-Staleness bleibt bekanntes Restrisiko.

**Risiken:**
- Der Doctor-`hooks`-Branch (`doctor_detectors.py:475-479`) ruft derzeit nur `check_hook_enablement_consistency` auf; `source: consistency` ist im Registry-Validator erlaubt (`doctor_registry.py:45`), hat aber keinen Producer in `_CHECK_MODULES` (`doctor_detectors.py:49-52`). Die Umsetzung muss den Dispatcher für `hooks.unknown-tool-name` ergänzen — keine neue Source erfinden.
- INFO-Findings sind leicht zu übersehen; die Sichtbarkeit liegt im Doctor-/Validate-Report, nicht im Hook-Lauf.

## ADR

- **ADR-1323-1 — Option A, nicht B, nicht Doku-only:** Kontext: dreimalige Staleness. Entscheidung: Doctor-/Consistency-Check als Differenz aus Harness-Set und Allow-List; Deny-List-Inversion (Option B) und reines Dokumentieren explizit abgelehnt. Konsequenz: Guards bleiben closed/fail-closed, Staleness wird proaktiv sichtbar.
- **ADR-1323-2 — INFO statt WARNING:** Kontext: Issue-Option A nennt „warning/failing sync", der User verlangt non-destructive. Entscheidung: ausschließlich `Severity.INFO`, nie ERROR/WARNING. Konsequenz: rc 0 in `--validate`, `--doctor` und `--doctor --strict` (belegt durch `report.py:50/75` und `cli_commands.py:1439-1443`).
- **ADR-1323-3 — Kein Runtime-Eingriff:** Kontext: Der Check soll Staleness melden, nicht beheben. Entscheidung: `hook_known_tool_name` und beide Guards bleiben unverändert. Konsequenz: echte Unbekannte blocken weiterhin (exit 2); das Ergänzen der Allow-List bleibt bewusster Developer-Schritt.

## Completeness Checklist

- [x] Pflicht-Sektionen vorhanden; Body-Marker genau 1×.
- [x] Interfaces vollständig typisiert, keine offenen Typen; Fehlerpfade benannt.
- [x] Jede AC testbar und auf Contracts gemappt.
- [x] Anker gegen `278ba54f` neu gemessen.
- [x] Provider-agnostisch (kein `if provider == ...`).
- [x] Keine Implementierung, keine Closing-Keywords, keine Placeholder.
- [x] Q1 als echte offene Entscheidung markiert (nicht erfunden).

## Trace-Anker: spec-id: SPEC-DOCTOR-UNKNOWN-TOOL-NAME-1323
