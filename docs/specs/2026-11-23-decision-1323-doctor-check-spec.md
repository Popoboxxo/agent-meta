---
spec-id: SPEC-DOCTOR-UNKNOWN-TOOL-NAME-1323
status: APPROVED
approval: "User, 2026-11-23, Einzelentscheidung"
---

# Doctor-Consistency-Check für unbekannte Tool-Namen (#1323) — Spec
> Status: APPROVED (User, 2026-11-23, Einzelentscheidung)

## Problem / Ziel / Nicht-Ziele

**Problem (Issue #1323, Evidenz):** `hook_known_tool_name` (`hooks/1-generic/lib/hook_common.sh:189-213`) ist eine handgepflegte Closed Allow-List, die beide Fail-Closed-Guards vor der Tool-Klassifikation konsultieren. Drei identische Staleness-Fälle: #1055 (`Agent`, `SendMessage`, v1.6.0), #1078 (`ToolSearch` + 14 Built-ins, v1.8.0), #1323 (`SubagentHandback`, Immediate-Fix v1.8.1 — `hook_common.sh:5`, `:210`). Jeder neue Harness-Built-in blockiert bis zur nächsten Bug-Meldung den Handoff-Kanal; #1078 hatte den Doctor-Check bereits als Follow-up benannt, er wurde nie gebaut. Der Audit-Log enthält keine `tool_name`-Records (`tests/test_hook_common_lib.py:333`) — Staleness ist heute nur reaktiv sichtbar.

**Ziel:** Nicht-destruktiver Doctor-/Consistency-Check, der die Harness-/Doku-Toolnamen gegen die Allow-List differenziert und unbekannte Namen als INFO-Finding sichtbar macht — proaktiv, ohne Laufzeit- oder Exit-Code-Änderung.

**Nicht-Ziele (BINDENDE User-Entscheidung 23.11):**
- **Keine Deny-List-Inversion** (Issue-Option B): die Guards behalten die Closed Allow-List und fail-closed für unbekannte Namen.
- **Kein reines Dokumentieren**: es entsteht ein ausführbarer, testbarer Check, kein Hinweistext.
- **Kein „failing sync"** (Issue-Option-A-Variante): kein ERROR, kein WARNING, kein `rc != 0`, kein Blockieren — auch nicht unter `--doctor --strict`.
- Keine Änderung an `hook_known_tool_name`-Semantik, Guard-Exit-Codes oder generierten Hook-Kopien; keine Implementierung in diesem Schritt.

## Interface Contracts

Alle Anker gegen Referenz-Commit `41dd69ac` neu gemessen (Checkout `fix/final-bug-bundle-20261123`).

| # | Datei:Symbol | Signatur / Typ | Rolle & Fehlerpfad |
|---|---|---|---|
| 1 | `scripts/lib/consistency/hook_known_tool_names.py` (neu): `parse_known_tool_names`, `load_expected_tool_names`, `check_unknown_tool_names` | `parse_known_tool_names(source_text: str) -> frozenset[str]`; `load_expected_tool_names(agent_meta_root: Path) -> frozenset[str]`; `check_unknown_tool_names(project_root: Path, agent_meta_root: Path, config: dict, provider_config: dict) -> list[Finding]` | Known-Set = Case-Literale aus `hook_common.sh:189-213` (MCP-Wildcard `:192` kein Literal, Worktree-Paar `:183-185` bewusst ausgenommen). Expected-Set = Union aus `config/provider-capabilities.yaml:154-155,216-217,278-279,349-350` (`native_agent_tools`, `worker_control_tools`) und `config/provider-tools.yaml:7-140` (Provider-Blöcke; `*-silent`, `opencode_deny_critical`, `opencode_primary_edit_allow`, `terminal_tool` ausgeschlossen, `mcp__*` übersprungen, casefold-normalisiert; Loader `scripts/lib/frontmatter.py:58-79`). Delta = `expected - known` ∪ `known - expected` (Config↔Allow-List-Abgleich, kein Harness-Feed). Finding: `Severity.INFO`, `check="hooks.unknown-tool-name"`, `file="hooks/1-generic/lib/hook_common.sh"`, Message nennt Tool-Name und Abgleichrichtung, Suggestion nennt `hook_known_tool_name`. Kein Import aus `tests/`. Fail-soft: unlesbares/nicht parsbares Source oder fehlende Config ⇒ `[]` (oder INFO `doctor.detector-unavailable`), nie `raise`, nie ERROR. |
| 2 | `scripts/lib/cli_commands.py:1663-1691` (`_strict_findings`-Block, `--validate`/`--audit-config`) | `_strict_findings += check_unknown_tool_names(project_root, agent_meta_root, config, _provider_config)` | Neben `check_stale_deployed_hooks` (`:1671`) und `check_hook_enablement_consistency` (`:1676`) einhängen. Kein `consistency_errors +=`: `print_report()` (`scripts/lib/consistency/report.py:44-75`) leitet den rc nur aus ERROR ab ⇒ rc 0. |
| 3 | `scripts/lib/doctor_detectors.py:475-479` (`_raw_findings`, Branch `source == "hooks"`) + `config/known-issues.yaml:380-391` (neuer Eintrag `hooks-unknown-tool-name` neben `hooks-not-registered`) | Registry-Eintrag `id: hooks-unknown-tool-name`, `detector: {kind: finding-ref, check: hooks.unknown-tool-name, source: hooks}`, `severity: INFO`; der Hooks-Branch dispatcht den Check zusätzlich zum bestehenden `check_hook_enablement_consistency` | `--doctor`-Sichtbarkeit. INFO bleibt auch in `_doctor_exit_code` (`cli_commands.py:1432-1443`) und unter `--strict` bei rc 0. Registrierte Quelle `hooks` ist erlaubt (`doctor_registry.py:44-46`); `_CHECK_MODULES` (`doctor_detectors.py:49-52`) braucht keinen neuen Producer. |
| 4 | `hooks/1-generic/lib/hook_common.sh:189-213` (`:210` `SubagentHandback`; `:5` Changelog v1.8.1); `hooks/1-generic/orchestrator-guard-impl.sh:274-279`; `hooks/1-generic/repo-containment-impl.sh:263-266` | read-only | Source of Truth für den Known-Set; Guard-Fail-Closed (exit 2) bleibt unverändert. `.agents/hooks/lib/hook_common.sh` ist generierte Kopie — nicht editieren. |
| 5 | `tests/test_hook_common_lib.py:394-404` `_DOCUMENTED_CLAUDE_TOOLS`, `:405` `_DELIBERATELY_REJECTED`, `:408-412` Parity-Test | `tuple[str, ...]` | Historischer Doku-Snapshot (Stand 2026-11-06), **nicht** mehr Datenquelle — Q1 RESOLVED zugunsten der Config (siehe unten). Kein Import aus `tests/` zur Laufzeit; der bestehende Parity-Test bleibt unverändert. |
| 6 | `tests/test_hook_known_tool_names_consistency.py` (neu) | pytest | Deckt AC-1 bis AC-4 ab; Muster `tests/test_hook_drift.py`. Fixture `FutureTool` in temporärer Config ⇒ genau 1 INFO-Finding; sauberer Config-Stand ⇒ 0 Deltas; fail-soft bei fehlender Quelle; rc 0 in `--validate`, `--audit-config`, `--doctor --strict`. |

Fehlerpfade konsolidiert: unbekannter Tool-Name ⇒ INFO-Finding, rc 0; Source fehlt/nicht parsbar ⇒ leere Findings, rc 0; Guard-E2E für echte Unbekannte ⇒ unverändert exit 2.

## Datenfluss

`hook_common.sh:189-213` (Case-Literale) + Config-Expected-Set (`config/provider-capabilities.yaml:154-155,216-217,278-279,349-350` ∪ `config/provider-tools.yaml:7-140`, casefold) → `parse_known_tool_names` / `load_expected_tool_names` → Config↔Allow-List-Delta (`expected - known` ∪ `known - expected`) → `Finding(INFO, "hooks.unknown-tool-name", file, message, suggestion)` → `cli_commands.py:1663-1691` (`_strict_findings`) → `print_report()` mit rc 0; parallel `config/known-issues.yaml:380-391` → `doctor_detectors.py:475-479` → Doctor-Report mit rc 0. Keine Persistenz, keine Hook-Änderung, kein Rebaseline (der Spec ändert keine per Hash gepinnte Hook-Datei).

## Acceptance Criteria (nummeriert, testbar — Given/When/Then)

1. **AC-1 (Unknown → Finding):** Given ein im Candidate-Set vorhandener, in `hook_known_tool_name` fehlender Name (Test-Fixture `FutureTool`), When `check_unknown_tool_names(project_root, agent_meta_root, config, provider_config)` läuft, Then gibt es genau 1 Finding mit `check == "hooks.unknown-tool-name"`, `severity == INFO`, dem Tool-Namen in `message`, dem `hook_common.sh`-Pfad in `file` und `hook_known_tool_name` in `suggestion`. *(Contract 1.)*
2. **AC-2 (Non-destructive Validate):** Given dieses Finding, When `python3 scripts/sync.py --validate` und `--audit-config` laufen, Then exit 0, kein `consistency_errors`-Inkrement, keine Datei geändert. *(Contracts 1, 2.)*
3. **AC-3 (Doctor + `--strict`):** Given dasselbe Finding im Doctor-Report, When `python3 scripts/sync.py --doctor --strict` läuft, Then rc 0 und das Finding ist als `INFO` gelistet (`_doctor_exit_code` eskaliert nur ERROR bzw. strict-WARNING). *(Contracts 1, 3.)*
4. **AC-4 (Config↔Allow-List-Konsistenz, INFO/rc 0):** Given der Stand @41dd69ac, When `check_unknown_tool_names` den aus `config/provider-capabilities.yaml:154-155,216-217,278-279,349-350` und `config/provider-tools.yaml:7-140` abgeleiteten Expected-Set (casefold, ohne Wildcards/Silent-Listen) gegen die Case-Literale in `hook_common.sh:189-213` abgleicht, Then ist jedes Delta ein `Severity.INFO`-Finding mit `check == "hooks.unknown-tool-name"` bei rc 0 — kein ERROR, kein WARNING, kein `rc != 0`. Erwartete Deltas im aktuellen Stand: die Config-Aliase `define_subagent`, `invoke_subagent`, `AgentSwarm`, `send_input`, `close_agent`, `wait_agent` stehen nicht in der Allow-List; `SubagentHandback` (`:210`) steht in der Allow-List, aber nicht in der Config. Der Check ist damit ein **Config↔Allow-List-Abgleich, kein Live-Harness-Feed-Vergleich** — neue Built-ins werden nur erkannt, wenn sie in die Config eingetragen werden. `EnterWorktree`/`ExitWorktree` (`:183-185`) und die MCP-Wildcard (`:192`) erzeugen kein Finding. *(Contracts 1, 4, 5, 6.)*
5. **AC-5 (Guard-Semantik):** Given ein wirklich unbekannter `tool_name` im PreToolUse-Payload, When einer der Guards läuft, Then blockt er weiter mit exit 2 und der bestehenden M2-Meldung — der Check fügt keinen Allow-Eintrag hinzu. *(Contract 4.)*
6. **AC-6 (Regression):** Given `tests/test_hook_known_tool_names_consistency.py`, When pytest läuft, Then bestehen die AC-1-bis-AC-4-Tests und keine bestehenden Hook-/Doctor-Tests ändern ihre Erwartungen. *(Contract 6.)*

Jede AC mappt auf mindestens einen Interface-Contract.

## Entscheidungen + Risiken

**Q1 — RESOLVED (User, 2026-11-23, Einzelentscheidung): Provider-Capability-Config ist die Datenquelle.** Die Frage nach der Source of Truth der erwarteten Tool-Namen ist entschieden: `load_expected_tool_names(agent_meta_root: Path) -> frozenset[str]` liest die **Provider-Capability-Config** — nicht den Doku-Snapshot, nicht `tests/`, keinen erfundenen Feed. Verifizierte Anker @41dd69ac:
- `config/provider-capabilities.yaml:154-155` (Claude: `native_agent_tools`, `worker_control_tools`), `:216-217` (Opencode), `:278-279` (Gemini/Antigravity), `:349-350` (Continue).
- `config/provider-tools.yaml:7-140` — Tool-Namen-Listen der Provider-Blöcke; ausgeschlossen: `*-silent`, `opencode_deny_critical`, `opencode_primary_edit_allow`, `terminal_tool` sowie `mcp__*`-Wildcards.
- Loader: `scripts/lib/frontmatter.py:58-79` (`load_provider_tools_config`); Casefold-Normalisierung, damit `task`/`Task` und `send_message`/`SendMessage` nicht als Delta gelten.

Der Contract bleibt unverändert; weiterhin **kein Import aus `tests/`**. Der Snapshot `_DOCUMENTED_CLAUDE_TOOLS` (`tests/test_hook_common_lib.py:394`) und der fehlende `tool_name`-Audit-Log (`:333`) sind damit nur noch historischer Kontext zu #1055/#1078/#1323, nicht die Datenquelle.

**Semantische Konsequenz (in AC-4 eingearbeitet):** Die Config enthält `SubagentHandback` nicht, dafür Aliase (`define_subagent`, `invoke_subagent`, `AgentSwarm`, `send_input`, `close_agent`, `wait_agent`). Der Check ist daher ein **Config↔Allow-List-Abgleich** mit `Severity.INFO` und rc 0, **kein** Live-Harness-Feed-Vergleich. Akzeptiertes Restrisiko: neue Harness-Built-ins werden erst nach Eintrag in die Config sichtbar; die Guards bleiben unverändert fail-closed.

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
- [x] Anker gegen `41dd69ac` neu gemessen.
- [x] Provider-agnostisch (kein `if provider == ...`).
- [x] Keine Implementierung, keine Closing-Keywords, keine Placeholder.
- [x] Q1 RESOLVED: Config-Datenquelle mit verifizierten Ankern dokumentiert (nicht erfunden).

## Trace-Anker: spec-id: SPEC-DOCTOR-UNKNOWN-TOOL-NAME-1323
