---
spec-id: SPEC-DECISION-1344-OPENCODE-DISPATCH
status: APPROVED
approval: "User, 2026-11-23, Einzelentscheidung"
---

# OpenCode-Orchestrator Dispatch-Form (#1344) — Spec

> Status: APPROVED (User, 2026-11-23, Einzelentscheidung)

Freigabe: explizites User-Go 23.11 (Einzelentscheidung), im aktuellen User-Direktiv übermittelt. Kein erneuter Approval-Schritt nötig.

## Problem / Ziel / Nicht-Ziele

**Problem (Evidenz):** Der generierte OpenCode-Orchestrator emittiert `task(...)`- / `route_intent`-Dispatch-Calls. OpenCode V2 kennt diese Tools nicht; das einzige Subagent-Dispatch-Primitive ist `subagent` mit Pflicht-Parameter `agent` (offizielle Doku `opencode.ai/docs/tools` + Quelle `anomalyco/opencode@dev`, `packages/core/src/tool/plugin/subagent.ts`: `export const name = "subagent"`, `agent: Schema.String`). Die falsche Form kommt aus **Daten, nicht aus Python**: `config/delegation-syntax.yaml:53-74` (Opencode-Block: `task_fmt`, `delegate`, `fanout`, `parallel_group`, `parallel_pattern`, alle `task(subagent_type=…)`; `:70` `fallback: "@orchestrator <task>"`) und `config/provider-capabilities.yaml:215-216,226` (`native_agent_tools: ["task"]`, Description „via task() tool"). Einsetzen erfolgt wörtlich via `scripts/lib/delegation_syntax.py:689-699` in `agents/1-generic/orchestrator.md:227-231`; `route_intent`-Text an `:102-106,210-216`. Eine fail-closed-Regel für „benannte Rolle nicht verfügbar" fehlt (`:308-315` deckt nur Unknown intent ab). Der `general`-Downgrade ist Consumer-Laufzeitverhalten, nicht im Generator kodiert.

**Ziel:** Für die Opencode-Surface ausschließlich `subagent(agent="<role>")` als Dispatch-Form emittieren; Rollen aus `routing.rules`/`name_index`; fehlende Rolle → Eskalation an `main_chat` (fail closed); Regressionstest + Doku.

**Nicht-Ziele:** Keine Consumer-Runtime-Änderung (kein Port des ReqogniLoom-Workarounds). Kein erfundener Tool-Name — `subagent(agent=…)` ist quellseitig belegt. Kein `if provider == "…"` im Python-Code (key-driven, Capability-Flags). Keine Permission-/Transform-Änderung (Thema #1329). Kein Systemdesign für XL — M-Scope (Daten + Template + Tests). Keine Implementierung.

## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)

Anker neu gemessen gegen Branch `fix/final-bug-bundle-20261123` @ `41dd69ac`.

1. **`config/delegation-syntax.yaml` → `syntax.Opencode`** (`:53-74`): `pipeline_notation.task_fmt` (`:55`) sowie `loop_item`/`parallel_item`/`fanout_item`/`sequential_item` (`:58/60/62/66`) und `delegate`/`fanout`/`parallel_group`/`parallel_pattern` (`:67/68/69/73`) von `task(subagent_type="{agent}", …)` auf `subagent(agent="{agent}", description=…, prompt="{task}")` umstellen. `fallback` (`:70`) auf `main_chat`-Eskalation statt `@orchestrator <task>` setzen. Signatur der Platzhalter (`{agent}`, `{task}`) bleibt stabil; key-driven, kein Provider-Literal in Python.
2. **`config/provider-capabilities.yaml` → `capabilities.Opencode`** (`:200-226`): `native_agent_tools: ["task"]` (`:216`) → `["subagent"]`; `description` (`:226`) von „via task() tool" auf `subagent`-Dispatch korrigieren. `route_intent_tool: false` (`:215`) bleibt. Optional neuer Capability-Key für „named-role-unavailable → main_chat" (fail-closed, datengetrieben); `VERIFIED-RUNTIME`-artiger Evidenz-Key nach Muster `:214` ergänzen, sofern die Signatur nicht gegen eine installierte Version verifiziert ist.
3. **`agents/1-generic/orchestrator.md` → Template-Texte**: `:102-106` (`ROUTE_INTENT_CALLABLE`-Block, „Erfinde keinen Tool-Aufruf" beibehalten), `:210-216` (`route_intent`-Formulierung in der Dispatch-Tabelle), `:227-231` (`{{PAL_FANOUT}}`/`{{PAL_PARALLEL_GROUP}}`), `:19` (HARD-REJECT-Hinweis `task(subagent_type="orchestrator")`), `:308-315` (§11: Eskalationsregel für nicht verfügbare benannte Rolle ergänzen). Weiterhin ausschließlich über `{{PAL_*}}` / `{{ROUTE_INTENT_CALLABLE}}`; keine Provider-Literale im Generic-Template.
4. **`scripts/lib/delegation_syntax.py` → `DelegationSyntaxEngine.apply()`** (`:689-699`) und `has_route_intent_tool()` (`:735-744`): Code unverändert; konsumiert die neuen Daten wörtlich. Fehlerpfad bleibt: fehlender Key → WARNING + leerer Platzhalter (`:694-698`).
5. **`scripts/lib/agent_sync.py` → `ROUTE_INTENT_CALLABLE`** (`:692-696`): unverändert; leitet sich aus dem Capability-Flag ab (fail-safe `false`).
6. **Tests**: `tests/test_pipeline_notation_config.py:64-72` (`"Opencode": ("task(", "task(")` → `subagent(`), `tests/test_opencode_agents.py` (Drift-Guard: kein `task(`/`route_intent`, nur `subagent(agent=…)`), `tests/test_no_role_routes_in_templates.py` (Template-Guard), `tests/test_provider_agnostic_dispatch.py` (Capability-Invariante). Muster: `tests/test_delegation_syntax.py:219` (native Syntax).

**Fehlerpfade:** Dispatch-Call in `task(`/`route_intent` nach Render ⇒ Gate-Finding mit Datei + Key. Benannte Rolle im Runtime nicht verfügbar ⇒ Eskalation `main_chat`, nie stiller `general`-Fallback. Fehlender Config-Key ⇒ WARNING, Placeholder entfernt (bestehendes Verhalten).

## Datenfluss

`config/delegation-syntax.yaml` (Opencode-Daten) + `config/provider-capabilities.yaml` (Capability-Flags) → `DelegationSyntaxEngine.apply()` substituiert `{{PAL_*}}` wörtlich in `agents/1-generic/orchestrator.md` → `scripts/lib/agent_sync.py` rendert `ROUTE_INTENT_CALLABLE` aus dem Capability-Flag → Output `.opencode/agents/orchestrator.md`. Persistenz ausschließlich generierte Artefakte; keine Runtime-Änderung. Andere Provider konsumieren ihre eigenen Config-Blöcke und bleiben byte-identisch.

## Acceptance Criteria (nummeriert, testbar — Given/When/Then)

1. **AC-1 (Dispatch-Form):** Given frisch generierter OpenCode-Orchestrator; When gerendert; Then enthalten alle Dispatch-Beispiele `subagent(agent="<named role>")` und **kein** `task(` / `route_intent`. → Contracts #1/#3/#6.
2. **AC-2 (Namensrollen):** Given aktive Rollen aus `routing.rules`/`name_index`; When Dispatch-Beispiele gerendert; Then stammen Rollennamen daraus, ohne `general`-Fallback (außer explizit vom Platform-Adapter bestätigt). → Contracts #1/#2/#3.
3. **AC-3 (Fail-Closed):** Given eine benannte Rolle ist im Runtime nicht verfügbar; When der Orchestrator den Dispatch auflöst; Then eskaliert er an `main_chat`, per Test verifiziert — nie stiller Downgrade auf `general`. → Contracts #1/#2/#6.
4. **AC-4 (Regression/Drift):** Given `task(`/`route_intent` wird erneut in Config oder Template eingefügt; When der Generator-/Drift-Test läuft; Then schlägt er mit einem Finding fehl, das Datei + Key benennt. → Contracts #1/#6.
5. **AC-5 (Doku):** Given die Dokumentation (`docs/guides/quality-pipelines.md:81-85`, Kandidat); When gelesen; Then beschreibt sie OpenCode-Dispatch-Semantik (primary vs. subagent) und die Fail-Closed-Eskalation. → Contract #6.
6. **AC-6 (Provider-Isolation):** Given dieselben Rollen für Claude, Gemini und weitere Provider; When gerendert; Then sind die Artefakte byte-identisch zum Stand `41dd69ac` (kein Notation-/Capability-Posture-Change). → Contracts #4/#5/#6.

Jede AC mappt auf mindestens einen Interface-Contract.

## Offene Fragen + Risiken

**Produktentscheidung ist bindend:** `subagent(agent="<role>")` + Fail-Closed an `main_chat`; nicht erneut abzuwägen.

**Flagged (Implementierungsdetails, keine Produktentscheidung):**
- Exakte Key-Namen/Werte: `native_agent_tools: ["subagent"]`, ob ein separater Fail-Closed-Capability-Key nötig ist, und der Evidenz-Wert (die Quelle ist `dev`-Branch, nicht gegen eine installierte Consumer-Version verifiziert) — Follows bestehendem Capability-Muster; Abweichung ist Implementierungsdetail, kein Re-Open.
- Fallback-Semantik: `config/delegation-syntax.yaml:70` hat heute `@orchestrator <task>`; AC-3 verlangt `main_chat`. Der Daten-Key ist entsprechend umzusetzen; das *Ziel* (fail-closed `main_chat`) ist durch Issue + User-Go bereits entschieden.
- Doku-Zielpfad (`docs/guides/quality-pipelines.md:81-85` ist Kandidat, nicht verbindlich).

**Risiken:**
- `general` ist Consumer-Laufzeitverhalten — der Generator kann es nicht direkt abschalten; Spec adressiert die Prompt-Seite (fail-closed Regel).
- Golden-Fixtures / AC01-Hashes anderer Surfaces könnten eine Rebaseline erfordern (AC-6 muss dies nachweisen).
- Kein Product-Design für XL nötig; bei Abweichung vom M-Scope an `concept-architect` eskalieren.

## Completeness Checklist

- [x] Pflicht-Sektionen vorhanden (Problem/Ziel/Nicht-Ziele, Interface Contracts, Datenfluss, AC, Offene Fragen+Risiken, Trace-Anker).
- [x] Jeder Interface fully typed (Datei:Symbol, Signatur, Fehlerpfade, keine `TBD`).
- [x] Jede AC testbar (Given/When/Then + Contract-Mapping).
- [x] Anker gegen `41dd69ac` neu gemessen.
- [x] Provider-agnostisch (key-driven, kein `if provider == "…"`).
- [x] User-Go 23.11 kodiert (`status: APPROVED`, `approval`-Feld + Body-Marker genau einmal).
- [x] Keine Implementierung, keine Placeholder, keine Closing-Keywords.

## Verifikationsanker

- Basis: Branch `fix/final-bug-bundle-20261123` @ `41dd69ac`.
- `config/delegation-syntax.yaml:53-74`; `config/provider-capabilities.yaml:200-226` (`:215/:216/:226`).
- `agents/1-generic/orchestrator.md:19,102-106,210-216,227-231,308-315`.
- `scripts/lib/delegation_syntax.py:689-699,735-744`; `scripts/lib/agent_sync.py:692-696`; `tests/test_pipeline_notation_config.py:64-72`.
- Externe Evidenz: `opencode.ai/docs/tools` („Subagent"), `anomalyco/opencode@dev` `subagent.ts` (`name = "subagent"`, `agent: Schema.String`); `task`/`route_intent` nicht in der Built-in-Tool-Liste.

## Trace-Anker: spec-id: SPEC-DECISION-1344-OPENCODE-DISPATCH

Issue: #1344 (P1, OpenCode-Orchestrator-Falsch-Dispatch). Kindred: #1329 (separater Shell-Grant-Spec).
