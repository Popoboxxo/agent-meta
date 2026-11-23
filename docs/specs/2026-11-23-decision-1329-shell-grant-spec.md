---
spec-id: SPEC-DECISION-1329-SHELL-GRANT
status: APPROVED
approval: "User, 2026-11-23, Einzelentscheidung"
---

# Opencode-Worker Shell-Grant Entscheidung (#1329) — Spec

> Status: APPROVED (User, 2026-11-23, Einzelentscheidung)

## Problem / Ziel / Nicht-Ziele

**Problem:** Der Contract-Spec `SPEC-OPENCODE-WORKER-SHELL-TOOL-1329` hielt die Optionswahl (a)/(b)/(c) bewusst offen. Live-Evidenz aus #1329: via `subagent()` gespawnte Opencode-Worker erhalten trotz `bash: allow` kein Shell-Tool; `test-executor` meldete „20/20 pytest grün", ohne pytest gestartet zu haben. Deklarierte und tatsächliche Execution-Capability divergieren — erfundene Verify-Evidence.

**Bindende Entscheidung (User, 23.11):** Option **(a)** — Opencode-Worker erhalten das Shell-Tool, wenn `bash: allow` konfiguriert ist. Umsetzung über Code/Provider-Transform + Tests; Ziel ist die Verhinderung erfundener Test-Evidence. Die a/b/c-Frage ist damit entschieden und wird hier nicht erneut aufgeworfen.

**Ziel:** Für Opencode-Subagent-Worker die deklarierte Shell-Capability real machen (v1 `permission.bash` / v2 `permissions[shell]`), sodass Execution-Rollen echte Prozesse ausführen und Erfolg nur mit gemessenem Exit-Code behaupten.

**Nicht-Ziele:** Keine Änderung der Claude-/Gemini-Permission-Posture (Output byte-identisch). Keine LLM-Runs oder echten Test-Suite-Läufe in diesem Schritt. Keine Implementierung — nur Spezifikation. Keine Änderung der Orchestrator-Write-Lock-Posture (`_WRITE_SCOPE_LOCKED_ROLES`); der Shell-Grant gilt nur für Rollen mit `bash: allow`. Kein Re-Open von (b)/(c).

## Relation zum Contract-Spec

Dieser Spec ergänzt `SPEC-OPENCODE-WORKER-SHELL-TOOL-1329` (APPROVED, generelle Freigabe) um die verbindliche Optionswahl. Der dort definierte CONTRACT (Deklaration ≡ Verfügbarkeit, fail-safe `deny`, Evidence-Discipline, Post-Render-Gate, Reuse des Capability-Mechanismus) bleibt vollständig in Kraft; dieser Spec wählt daraus (a) und konkretisiert die Render-Kette. Bei Konflikt gilt der Contract-Spec für die Invarianten, dieser Spec für die Entscheidung „grant".

## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)

Anker neu gemessen gegen Branch `fix/decision-points-bundle-20261123` @ `278ba54fa6f43376b93aa025d3efedf7a73e6463`.

1. **`config/provider-capabilities.yaml`** → `capabilities.Opencode` (Zeilen 189–247; `supports-permission-deny: false` :201, `#1113`-Muster :57/:201). Shell-Capability-Key auf `true` setzen (Entscheidung: grant). Key-Name folgt dem Contract-Spec `subagent-shell` (+ `subagent-shell-verified-state`); kein Provider-Name-Branch, key-driven.
2. **`scripts/lib/provider_transform.py`** →
   - `_map_claude_tools_to_opencode_permissions(tools: list, deny_list: list[str] | None = None) -> dict[str, str]` (889–937; `Bash -> bash` :915): v1 `permission.bash: allow` nur bei konfiguriertem `bash: allow` **und** Shell-Capability `true`, sonst `deny`/fehlt.
   - `map_tools_to_opencode_v2_permissions(tools: list, deny_list: list[str] | None = None) -> list[dict[str, str]]` (954–989; Konstanten `_V2_PERMISSION_ACTIONS` :941, `_V2_CLAUDE_TOOL_ACTIONS` :947, `Bash -> shell` :950): identische Kopplung für `permissions[shell].effect: allow`; `deny_list`-Parität bleibt.
   - `_transform_frontmatter_for_opencode(...)` (991–1149; `mode` default `subagent` :1069) und `_transform_frontmatter_for_opencode_v2(...)` (1262 ff.; :1315): aufgelösten Capability-Wert aus `_caps` (:447) an die Mapper reichen; Signatur um Shell-Capability-Parameter erweitern.
   - `transform_agent_content_for_provider(...)` (:804) / `_apply_agent_transform(...)` (:331): Datenfluss unverändert, `provider_capabilities` reicht den Key bis in die Mapper.
3. **`scripts/lib/agent_sync.py`** → `transform_agent_content_for_provider`-Aufruf (:1348), `render_bash`/Commit-Grant-Pfad (:149–201, :1858): `Bash`-Injektion für Shell-Rollen unter Opencode bleibt wirksam; kein Sonderpfad für Subagent-Worker.
4. **`config/ai-providers.yaml`** → `Opencode.agent-transform` (378 ff., `tools-format: keep` :395): Reuse des bestehenden Mechanismus, kein neues ad-hoc Flag-Source.
5. **`agents/1-generic/<rolle>.md`** → `test-executor.md` (`tools:` :9, `Bash` :11, Persona :17/:33) sowie `code-reviewer`, `e2e-tester`, `git`, `developer`, `devops-engineer`, `tester`: Evidence-Regel — Erfolgsbehauptung nur mit gemessenem Exit-Code; Shell-Ausführung darf behauptet werden, weil sie nun verfügbar ist.
6. **Tests** (Muster `tests/test_topology_capability_invariant.py`, `tests/test_provider_agnostic_dispatch.py`): v1/v2-Mapper-Tests + Post-Render-Gate über alle gerenderten Rollen.

**Fehlerpfade:** Shell-Capability fehlt/`false`/ungültiger Typ ⇒ `deny` + WARNING (nie `allow`); Divergenz deklariert vs. gerendert ⇒ Gate-Finding (Rolle + Datei + Mode), `sys.exit`-Freiheit im Gate-Layer wie `subagent_permissions.py`.

## Datenfluss

`agents/1-generic/<rolle>.md` (`tools: [.., Bash]`) → `build_frontmatter()` → `transform_agent_content_for_provider()` (`agent-transform`) → `_apply_agent_transform()` lädt `_caps` (:447) → v1/v2-Mapper rendern `bash`/`shell` = `allow` für gespawnte Worker bei `bash: allow` und Capability `true` → Post-Render-Gate validiert Deklaration gegen Capability → Output `.opencode/agents/<rolle>.md`. Persistenz: ausschließlich generierte Artefakte; keine Runtime-Änderung.

## Acceptance Criteria (nummeriert, testbar — Given/When/Then)

1. **AC-1 (Grant):** Given `capabilities.Opencode`-Shell-Key `true` und eine Rolle mit `bash: allow`; When als Opencode-`subagent` gerendert (v1 und v2); Then enthält das Artefakt v1 `permission.bash: allow` und v2 `permissions[shell].effect: allow`. → Contracts #1–#3.
2. **AC-2 (Fail-safe):** Given Shell-Key fehlt/`false`/ungültig oder die Rolle hat kein `bash: allow`; When als Opencode-`subagent` gerendert; Then ist `bash`/`shell` `deny` oder fehlt, nie `allow`, und ein WARNING/Finding liegt vor. → Contracts #1/#2/#6.
3. **AC-3 (Keine erfundene Evidence):** Given eine Execution-Rolle (`test-executor` et al.); When sie einen Test-Erfolg meldet; Then ist der Erfolg an einen gemessenen Prozess-Exit-Code gebunden; ohne Exit-Code ist keine Erfolgsbehauptung zulässig (Prompt-Regel nachweisbar). → Contract #5.
4. **AC-4 (Post-Render-Gate):** Given ein manipuliertes Artefakt mit `bash: allow` bei Shell-Key `false`; When der Gate läuft; Then schlägt er mit einem Finding fehl, das Rolle + Datei + Mode benennt. → Contract #6.
5. **AC-5 (Posture-Schutz):** Given dieselben Rollen für Claude und Gemini; When gerendert; Then sind die Artefakte byte-identisch zum Stand `278ba54f` (kein Shell-/Permission-Posture-Change, kein Write-Lock-Bruch beim Orchestrator). → Contracts #2/#3.

Jede AC mappt auf mindestens einen Interface-Contract.

## Offene Fragen + Risiken

**Entscheidung ist bindend:** (a) ist gewählt; (b)/(c) sind verworfen, keine erneute Abwägung.

**Flagged (technische Details, nicht die Entscheidung blockierend):**
- Exakter Capability-Key-Name / `verified-state`-Wert: folgt dem Contract-Spec (`subagent-shell`); falls der Owner einen anderen Key vorgibt, ist das eine Implementierungs-Detailentscheidung, nicht ein Re-Open von (a).
- Auslegung von „`bash: allow` konkretisiert": hier die generierte Rollen-Permission (aus Template-`Bash`), nicht zwingend `opencode.jsonc` `permission.bash: {}` — bei abweichender Lesart kurz bestätigen.

**Risiken:**
- `subagent-shell: true` ohne Runtime-Beleg erzeugt erneut Fiktion ⇒ `verified-state`-Pflicht + Post-Render-Gate + echte Testausführung (AC-3).
- Orchestrator-Write-Lock (`_WRITE_SCOPE_LOCKED_ROLES`) darf durch den Grant nicht unterlaufen werden (AC-5).
- Mammouth-Fork erbt das Muster; bewusst out of scope.

## Completeness Checklist

- [x] Pflicht-Sektionen vorhanden (Problem/Ziel/Nicht-Ziele, Interface Contracts, Datenfluss, AC, Offene Fragen+Risiken, Trace-Anker).
- [x] Jeder Interface fully typed (Signaturen + Fehlerpfade, keine `TBD`).
- [x] Jede AC testbar (Given/When/Then + Contract-Mapping).
- [x] Anker gegen `278ba54f` neu gemessen.
- [x] Provider-agnostisch (key-driven, kein `if provider == ...`).
- [x] User-Entscheidung (a) kodiert, nicht re-geöffnet.

## Trace-Anker: spec-id: SPEC-DECISION-1329-SHELL-GRANT

Parent-Contract: `spec-id: SPEC-OPENCODE-WORKER-SHELL-TOOL-1329`.
