---
spec-id: SPEC-OPENCODE-WORKER-SHELL-TOOL-1329
status: APPROVED
approval: "User, 2026-11-23, generelle Freigabe (Bug-Welle)"
---

# Opencode-Worker Shell-Capability Contract (#1329) — Spec

> Status: APPROVED (User, 2026-11-23, generelle Freigabe)

## Problem / Ziel / Nicht-Ziele

**Problem (Issue #1329, verbatim Evidenz):**
agent-meta generiert für Execution-Rollen Frontmatter mit `permission: { read: allow, bash: allow, edit: deny }` und Prompts, die Shell-Ausführung versprechen (z. B. `test-executor.md`: *"read + bash only, so parallel instances stay cheap (issue #517)"*; Description: *"Lightweight execution of existing test suites — pass/fail counts, exit codes, stdout excerpts."*). Im realen OpenCode-Harness erhalten via `subagent()` gespawnte Worker **kein Shell-Tool** — nur der Main Chat hat `shell`. Das deklarierte Capability ist Fiktion: die Rolle wird angewiesen, Befehle auszuführen, die sie nicht ausführen kann. Das `bash: allow` erscheint auch in `code-reviewer.md`, `e2e-tester.md`, `git.md`, `developer.md`, `devops-engineer.md`, `tester.md`; `opencode.jsonc` trägt `"permission": { ..., "bash": {} }`. Live-Konsequenz: `test-executor` meldete *"20/20 pytest grün"*, ohne pytest je gestartet zu haben — nur durch Lesen vorhandener Logs. Das ist ein Integritätsproblem (fabrizierte Verify-Evidence), kein bloßes Inconvenience. `orchestrator` (Frontmatter `bash: deny`, "Router, not Worker") war ebenfalls blockiert: `git`/`pytest`/OpenAPI-Fixture-Regeneration mussten an den Main Chat zurückgeworfen werden.

**Ziel:** Ein verbindlicher, framework-seitiger CONTRACT, dass die **deklarierte** Execution-Capability eines generierten Agenten mit der **tatsächlich verfügbaren** Execution-Capability im Ziel-Harness × Agenten-Modus (primary vs. subagent) übereinstimmt — auf v1- und v2-Oberfläche. Ein deterministischer Post-Render-Gate macht eine Abweichung sichtbar (fail-closed), und keine Execution-Rolle darf einen Test-Erfolg ohne echten Prozess-Exit-Code behaupten.

**Nicht-Ziele:**
- Keine Änderung der Sicherheits-/Permission-Posture von Claude oder Gemini.
- Kein tatsächlicher Shell-Zugriff für Opencode-Subagents zur Laufzeit wird hier implementiert oder vorausgesetzt (das ist Harness-Sache).
- Keine Ausführung von LLM-Runs / echten Test-Suites; keine Code-Implementierung, nur Spezifikation.
- Keine Änderung an den bereits gelösten Friktionen #1007 / #1077 / #1190 (subagent_depth-Keys, `orchestrator.topology`).

## Interface Contracts (Datei:Symbol — was sich ändern muss)

Alle Anker gegen `main e29381db` neu gemessen.

1. **`config/provider-capabilities.yaml`** — `capabilities.Opencode` (Zeilen 189–247). Neuer, expliziter Capability-Key (analog zum `#1113`-Flag-Muster `supports-permission-deny`, Zeilen 57–61 / 201): `subagent-shell: <bool> | null` plus `subagent-shell-verified-state: VERIFIED-RUNTIME | DOCUMENTED | UNVERIFIED` und optional `subagent-shell-reason`. Wert ist die **deklarierte Wahrheit** darüber, ob der Opencode-Harness Subagent-Workern ein Shell-Tool bereitstellt. Jeder registrierte Provider MUSS den Key explizit tragen; fehlend/false ⇒ fail-safe "kein Shell" (konservativ, kein spekulatives `bash: allow`). Kein Provider-Name-Branch — key-driven.

2. **`scripts/lib/provider_transform.py`**:
   - `_map_claude_tools_to_opencode_permissions(tools, deny_list=None) -> dict[str, str]` (Zeilen 889–937) — v1-Mapper: `Bash -> bash`. Muss die Shell-Freigabe für Subagent-Rollen an obigen Capability-Key koppeln (statt immer `bash: allow` aus Template-`tools` abzuleiten).
   - `map_tools_to_opencode_v2_permissions(tools, deny_list=None) -> list[dict[str, str]]` (Zeilen 954–989, Konstanten `_V2_PERMISSION_ACTIONS` 941 / `_V2_CLAUDE_TOOL_ACTIONS` 947) — v2-Closed-World-Mapper: `Bash -> shell`. Identische Capability-Kopplung für `shell: allow`/`deny`; `deny_list`-Parität bleibt erhalten.
   - `_transform_frontmatter_for_opencode(...)` (Zeilen 991–1149) und `_transform_frontmatter_for_opencode_v2(...)` (Zeilen 1262 ff.) — Übergabe des aufgelösten Shell-Capability-Werts aus `_caps` (Zeile 447) an die Mapper; Signaturen um einen `subagent_shell`-Parameter erweitern, der aus dem Capability-Key stammt.
   - `transform_agent_content_for_provider(...)` (Zeilen 804–852) / `_apply_agent_transform(...)` (Zeilen 331 ff.) — unveränderter Datenfluss, aber `provider_capabilities` muss den neuen Key bis in die Mapper reichen (bereits als Parameter vorhanden, Zeilen 818 / 347).

3. **`config/ai-providers.yaml`** — `Opencode.agent-transform` (Zeilen 378 ff.): `tools-format: keep` (Zeile 395) bleibt; ein spec-key oder die Capability steuert, ob `Bash` in der gerenderten `permission`/`permissions` als `allow` oder `deny` erscheint. Kein neues ad-hoc Flag-Source — Reuse des Mechanismus aus #1113.

4. **`agents/1-generic/<role>.md`** — `test-executor.md` (tools `[Read, Bash]`, Zeilen 9–12; Persona "read + bash only", Zeile 17), sowie `code-reviewer.md`, `e2e-tester.md`, `git.md`, `developer.md`, `devops-engineer.md`, `tester.md`, `orchestrator.md`: Prompts/Frontmatter dürfen Shell-Ausführung nur behaupten, wenn der Capability-Key für den/target-Modus `allow` ist. Evidence-Disziplin: kein "tests passed" ohne Exit-Code (siehe AC-4).

5. **Post-Render-Gate** (neuer Test, Muster `tests/test_provider_agnostic_dispatch.py` AC-01 / `tests/test_topology_capability_invariant.py`): deterministischer Check über alle gerenderten Rollen — `bash: allow` (v1) bzw. `shell: allow` (v2) darf nur gesetzt sein, wenn `subagent-shell: true` und der Agent-Modus entsprechend erlaubt; sonst Fail mit Finding.

**Fehlerpfade:** fehlender/UNVERIFIED Capability-Key ⇒ `deny` + WARNING (nie `allow`); ungültiger Key-Typ ⇒ `deny` + WARNING; Divergenz deklariert vs. gerendert ⇒ Gate-Fehler (Post-Render, `sys.exit`-Freiheit im Gate-Layer wie bei `subagent_permissions.py`, Zeilen 9–11).

## Datenfluss

`agents/1-generic/<rolle>.md` (Template `tools: [.., Bash]`) → `build_frontmatter()` → `transform_agent_content_for_provider()` (ai-providers `agent-transform`) → `_apply_agent_transform()` lädt `_caps = provider_capabilities[provider]` (Zeile 447) → `_map_claude_tools_to_opencode_permissions` (v1) / `map_tools_to_opencode_v2_permissions` (v2) — **neu:** Shell-Effekt abhängig von `capabilities.Opencode.subagent-shell` → gerendertes `permission.bash` / `permissions[shell].effect` → `tests/`-Gate validiert Deklaration gegen Capability → Output `.opencode/agents/<rolle>.md` (oder v2-Äquivalent). Persistenz: ausschließlich die generierten Artefakte; keine Runtime-Änderung.

## Acceptance Criteria (nummeriert, testbar — Given/When/Then)

1. **AC-1 (Contract):** Given `capabilities.Opencode.subagent-shell = false` bzw. UNVERIFIED und ein Template mit `Bash`; When `transform_agent_content_for_provider` rendert `test-executor` als `mode: subagent`; Then enthält das Artefakt v1 `permission.bash != allow` (deny/fehlt) und v2 `permissions[shell].effect = deny` — nie `allow`.
2. **AC-2 (Capability-Parität):** Given `subagent-shell = true` (verifiziert); When dieselbe Rolle als `subagent` gerendert wird; Then ist `bash`/`shell` `allow` und der Capability-Key trägt `subagent-shell-verified-state != UNVERIFIED`. Für Claude/Gemini bleibt das Output byte-identisch zu e29381db (kein Posture-Change).
3. **AC-3 (Post-Render-Gate):** Given eine absichtlich manipulierte generierte Rolle mit `bash: allow` bei `subagent-shell = false`; When der Gate (`tests/`, Muster `test_topology_capability_invariant.py`) läuft; Then schlägt er mit einem Finding fehl, das Rolle + Datei + Mode benennt.
4. **AC-4 (Evidence-Discipline):** Given eine Execution-Rolle ohne tatsächlichen Prozess-Exit-Code; When sie antwortet; Then darf sie keinen Test-Erfolg ("tests passed", "20/20 grün") behaupten — der Prompt enthält eine explizite Regel, die Erfolgsbehauptung an einen gemessenen Exit-Code bindet (von `test-executor.md` aus auf die anderen Execution-Rollen zu übertragen).
5. **AC-5 (Dokumentation):** Given die Capability-Matrix-Doku; When ein Consumer sie liest; Then sind Shell-Verfügbarkeit pro Provider und pro Modus (primary vs. subagent) sowie das Fallback-Verhalten (`deny` + WARNING) dokumentiert — ohne von einem Code-Branch abzuhängen. Der Fall **ohne expliziten Primary-Mode-Key** muss dabei explizit benannt sein: fehlt `primary-role`/`mode`, greift der bereits bestehende Fail-safe `mode: subagent` (`provider_transform.py:_transform_frontmatter_for_opencode`, Default `"mode": ... or "subagent"`); die Shell-Capability wird dann nach dem `subagent-shell`-Key beurteilt — bei `false`/UNVERIFIED ⇒ `deny`. Es wird damit keine neue Primary-Posture erfunden, sondern der vorhandene Default dokumentiert.

Jede AC mappt auf mindestens einen Interface-Contract (AC-1/2 → #1/#2/#3, AC-3 → #5, AC-4 → #4, AC-5 → #1).

## Offene Fragen + Risiken

**OFFENE DESIGN-ENTSCHEIDUNG (nicht vom Spec erfunden — eskalieren):**
Issue #1329 nennt drei Optionen mit "discussion welcome":
- (a) Shell-Capability aus der Rollen-Definition ableiten und Opencode-Subagent-Worker tatsächlich mit Shell ausstatten (v1 + v2) + Post-Render-Check.
- (b) Harness kann Subagents grundsätzlich kein Shell geben → `bash: allow` aus generiertem Frontmatter entfernen, Prompts auf "read-only — delegate execution to Main Chat" umstellen, Resultatsbehauptungen ohne echten Run verbieten.
- (c) Harness-Capability-Matrix (Provider × Tool × primary/subagent) publizieren, Reuse von `provider-capabilities.yaml`.

Dieser Spec definiert bewusst **nur den CONTRACT** (Deklaration ≡ Verfügbarkeit, fail-safe `deny`, Evidence-Discipline, Post-Render-Gate, Reuse des Capability-Mechanismus), der unter allen drei Optionen gilt. **Welche Option realisiert wird — insbesondere die Sicherheits-Posture, Subagent-Worker Shell zu geben — bleibt explizit offen und muss vom Produkt/Owner entschieden werden.** Der CONTRACT ist so formuliert, dass er mit (a), (b) oder (c) erfüllbar ist, ohne die Entscheidung vorwegzunehmen.

**Risiken:**
- Falsch gesetztes `subagent-shell: true` ohne Runtime-Beleg würde erneut Fiktion erzeugen ⇒ `verified-state`-Pflicht + UNVERIFIED⇒deny.
- Opencode-Fork Mammouth (Zeilen 452–513) erbt das Muster; bewusst NICHT in diesem Fix enthalten (Submodell-/Fork-Scope) — separate Klärung nötig.
- Orchestrator-Sonderfall (`bash: deny`, "Router, not Worker", `_WRITE_SCOPE_LOCKED_ROLES` in `provider_transform.py` Zeilen 304–328): Shell für den router-rolle darf die Write-Lock-Posture nicht unterlaufen.

**Eskalationsvorschlag:** Owner-Entscheidung (a)/(b)/(c) + Runtime-Probe, ob der Opencode-Harness Subagent-Worker `shell` registriert (analog zum P0-Probe-Muster aus `provider-capabilities.yaml`), bevor `subagent-shell` auf `true` gesetzt wird.

## ADR (Entscheidungen dieses Specs)

- **ADR-1329-1 — Fail-safe Deklaration:** Kontext: Opencode deklariert `bash: allow`, Harness liefert kein Shell. Entscheidung: Capability-Key fehlt/UNVERIFIED ⇒ `deny` + WARNING, nie `allow`. Konsequenz: konservatives Output, kein spekulatives Capability-Claim; bestehendes `#1113`-Muster wird wiederverwendet.
- **ADR-1329-2 — Contract statt Optionswahl:** Kontext: Issue lässt (a)/(b)/(c) offen. Entscheidung: Spec fixiert nur den Deklarations-≡-Verfügbarkeits-Contract + Gate, nicht die Sicherheits-Posture. Konsequenz: Umsetzung braucht eine explizite Owner-Entscheidung; kein verstecktes Design.

## Completeness Checklist

- [x] Alle Pflicht-Sektionen vorhanden (Problem/Ziel/Nicht-Ziele, Interface Contracts, Datenfluss, AC, Offene Fragen+Risiken, Trace-Anker).
- [x] Jeder Interface fully typed (Signaturen + Fehlerpfade, keine `TBD`).
- [x] Jede AC testbar (Given/When/Then + Mapping auf Contracts).
- [x] Anker gegen e29381db neu gemessen.
- [x] Provider-agnostisch (key-driven, kein `if provider == ...`).

## Trace-Anker: spec-id: SPEC-OPENCODE-WORKER-SHELL-TOOL-1329
