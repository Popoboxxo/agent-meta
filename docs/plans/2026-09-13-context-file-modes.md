---
pipeline_stages:
  implement: 1
---

# Implementierungsplan — Context-File Modes (Phase 1 / Phase 2)

> Status: geplant — **nicht implementiert.** Dieser Plan wird erst nach explizitem Start ausgeführt.

**Spec:** `docs/specs/2026-09-13-context-file-modes-design.md` (Status **APPROVED 2026-09-14**)

> Trace-Anker: `spec-id: SPEC-CONTEXT-FILE-MODES-2026-09-13` (Status APPROVED)
> System-Design: `docs/specs/2026-09-13-context-file-modes-system-design.md` (Revision 3)
> Verwandte Spec: `SPEC-OPENCODE-RUNTIME-GATE-2026-09-13` — Vokabular und Phase-0-Contracts bleiben; dieser Plan ergänzt eine Invariante (Shared-Context-File-Render) und löst den `AGENTS.md`-Doppelschreib-`--check`-rc1 ab.
> **Phase 0 (`unified`) ist Voraussetzung und wird NICHT angefasst:** bereits implementiert (Commit `ffd0e929`), `scripts/lib/runtime_gate.py::RUNTIME_GATE_TIER_RANK`/`weakest_runtime_gate_tier`, `scripts/lib/providers.py::_runtime_gate_bundle`/`shared_runtime_gate_vars`, `scripts/lib/context.py::_build_managed_block`-Shared-Override (IC-03) und `tests/test_context_file_modes.py` sind committed. Dieser Plan ist Phase 1 + Phase 2.

**Goal:** Den Topologie-Schalter `context_file.topology` (`unified | per-provider`, Default `unified`) als Sibling des Dichte-`context_file.mode` einführen und `per-provider` datengetrieben umsetzen — kanonischer Kern + provider-native dedizierte Tier-Kanäle (Adapter-Datei oder bestehender `rules_dir`-Kanal), ausschließlich über Config-Keys/Capability-Flags, mit Rückwärtskompatibilität und Rollback.
**Architecture:** Der Resolver `providers.py::context_topology` spiegelt die etablierte Präzedenz `variables.py::_resolve_orch_mode` (Provider-Override > Projekt > Default, fail-safe `unified`). Der Schema-Block `context_file` wird um `topology`, `core_file` und `provider-overrides.<Provider>.topology` erweitert, `additionalProperties: false` bleibt. Der Render-Dispatch in `context.py` wählt das physische Ziel (`core_file` vs. `context_adapter_file`) — **nicht** `resolve_context_filename` (nur Legacy-Cleanup, IC-08). Claude ist `context-managed-block` (Adapter `CLAUDE.md`, `@AGENTS.md`); Gemini/Antigravity ist **ein** Provider und trägt seinen Tier über den bestehenden `rules_dir`-Kanal (`.gemini/rules`), gated auf FINDING F-RULESLOC.
**Tech Stack:** Python 3.9 (Stdlib only, `from __future__ import annotations`, `typing.Optional`/`Dict`/`List`/`Tuple`, keine PEP-604-Union-Annotationen in neuen Modulen), JSON Schema (`config/project-config.schema.json`), YAML (`config/ai-providers.yaml`), Markdown, pytest, Bash-Szenario-Harness (`tests/scenarios/run.sh`), Admin-UI (`docs/ui/admin-ui.html`).

## Global Constraints

- **Eingefrorene User-Entscheidungen (nicht verhandelbar):**
  1. **Default `unified` = Bestand.** `context_file.topology` fehlt/ungültig → `unified` (safe-side: keine neuen Dateien, kein neues Verhalten ohne explizites Opt-in). Bestehende Layouts bleiben byte-identisch (ausgenommen die dokumentierte Weakest-Tier-Absenkung der geteilten `AGENTS.md`).
  2. **Präzedenz deterministisch:** `context_file.provider-overrides.<Provider>.topology` > `context_file.topology` > `"unified"`. Muster `orchestrator.provider-overrides.<Provider>.mode`.
  3. **Kanal (a) für Gemini/Antigravity in Phase 1 nur nach F-RULESLOC.** Die dedizierte Tier-Trägerschaft über `rules_dir: .gemini/rules` wird erst beansprucht, wenn Task 4 (F-RULESLOC-Real-Repo-Check) die Lokation bestätigt. **Fallback (c):** geteilte `AGENTS.md` + Tier ausschließlich per Hook erzwungen (Prompt-Text = Dokumentation); die Runtime-Erzwingung bleibt nativ (`hook_protocol: antigravity-hooks-json`, `runtime_gate: hook`).
  4. **Kandidat (b) `context.fileName` ausschließlich Phase 2** (AC-26) — nicht Phase 1.
  5. **„if you are X"-Konditionalblöcke sind Nicht-Ziel.** `per-provider` löst ausschließlich über echte Kanal-/Dateitrennung (self-identification ist unzuverlässig, NeurIPS-2024-SAD-Benchmark).
- **Provider-Agnostik:** Kein Provider-Literal und kein `if provider == …` in neuen/geänderten Modulen; jede Differenz über Config-Key/Capability-Flag. `tests/test_provider_agnostic_dispatch.py` bleibt grün.
- **Phase-0-Nicht-Regression:** `RUNTIME_GATE_TIERS` (`runtime_gate.py:35`) wird nicht umsortiert/erweitert; `RUNTIME_GATE_TIER_RANK`/`weakest_runtime_gate_tier` (committed `ffd0e929`) bleiben unverändert. `providers.py::runtime_gate_vars`-Contract bleibt byte-identisch; `_build_managed_block`-Shared-Override (IC-03) bleibt erhalten. `runtime_gate.py` wird von diesem Plan **nicht** berührt.
- **Shared-Files-Koordination:** `scripts/lib/context.py`, `scripts/lib/providers.py`, `scripts/lib/sync_pipeline.py`, `config/project-config.schema.json` sind Phase-0-berührt/committed. Änderungen sind rein additiv über dem committed Stand; kein Revert, keine Neuordnung der Phase-0-Blöcke.
- **Py3.9 & Stdlib:** Neue Module nutzen `from __future__ import annotations`; keine externen Dependencies; `rtk python3 scripts/consistency-check.py` muss rc 0 liefern.
- **Schema-Vertrag:** `context_file.additionalProperties: false` (`config/project-config.schema.json:915`) bleibt; kein neues Pflichtfeld; Absenz von `topology` bleibt gültig.
- **Datei-Ownership je Task:** Jede Datei wird in genau einer Task angelegt/geändert; `Depends on` referenziert immer eine frühere Task. Wo eine Datei sequenziell mehrfach vorkommt (nur `scripts/lib/context.py`, `config/ai-providers.yaml`, `tests/test_context_adapters.py`), ist der Graph strikt vorwärts und nie parallel in derselben Gruppe.
- **Bite-sized & TDD:** Jede Task ist einzeln testbar/committbar (Test fail → implementieren → Test pass → Commit); kein Task ist „done" ohne beobachteten Test.
- **Befehle:** Ausschließlich `rtk`-präfigierte Kommandos in diesem Plan.
- **Keine Rollen-Routen:** `agents/1-generic/*` und `rules/1-generic/*` erhalten keine Route-Tabellen/`roleA → roleB`-Ketten; `tests/test_no_role_routes_in_templates.py` bleibt grün.
- **Keine Implementierung jetzt:** Dieser Plan ändert keinen Code. Phase 1/2 startet erst auf expliziten User-/Orchestrator-Entscheid.

## Interfaces

Neue und geänderte Symbole als `file:Symbol`. Alle nicht gelisteten, bereits existierenden Symbole bleiben unverändert.

| Symbol | Art | Vertrag |
|---|---|---|
| `scripts/lib/providers.py:context_topology` | neu | `(config: Optional[dict], provider: Optional[str] = None) -> str`; Präzedenz Provider-Override > Projekt > Default; nicht-String/out-of-enum/Nicht-Mapping → `"unified"`; wirft nie. |
| `scripts/lib/providers.py:resolve_context_filename` | geändert (IC-08) | Legacy-Cleanup-Regel: `context_adapter: true` → `context_adapter_file` statt Kern; fehlend/leer → bestehende Auflösung (`CLAUDE.md → AGENTS.md`). **Nicht** auf dem Render-Pfad. |
| `config/project-config.schema.json:context_file.topology` | neu | `type: string`, `enum: ["unified","per-provider"]`, `default: "unified"`. |
| `config/project-config.schema.json:context_file.core_file` | neu | `type: string`, `default: "AGENTS.md"`. |
| `config/project-config.schema.json:context_file.provider-overrides` | neu | Objekt `<Provider> → { topology: enum }`, `additionalProperties: false` pro Eintrag. |
| `scripts/lib/config.py:fill_defaults` | geändert (IC-12) | Schreibt fehlenden Default `context_file.topology: unified`; fügt keinen Pflicht-Key hinzu; ein vorhandener `context_file`-Block wird nicht über das Schema hinaus geweitet. |
| `config/ai-providers.yaml:<Provider>.context_adapter` | neu (IC-07) | `true|false`; provider kann eine eigene Adapter-Datei lesen. |
| `config/ai-providers.yaml:<Provider>.context_adapter_file` | neu | nativer Dateipfad, z. B. `CLAUDE.md`. |
| `config/ai-providers.yaml:<Provider>.context_adapter_import` | neu | provider-native Import-Syntax, `"{core}"`-Platzhalter, `""` = Pointer-Zeile. |
| `config/ai-providers.yaml:<Provider>.context_adapter_import_supported` | neu | expliziter Boolean (Ableitbarkeit, kein impliziter Default). |
| `config/ai-providers.yaml:<Provider>.context_adapter_settings` | neu (Phase 2) | `true` = Adapter nur aktiv, wenn ein provider-nativer Settings-Key ihn nennt. |
| `scripts/lib/context.py:sync_context_adapters_for_provider` | neu (IC-09) | `(agent_meta_root, project_root, config, variables, log, dry_run, provider, provider_config) -> None`; schreibt genau eine Adapter-Datei, Import- oder Pointer-Zeile, provider-eigener Tier auf seinem Träger-Kanal; idempotent. |
| `scripts/lib/context.py:sync_context_for_provider` | geändert (IC-09) | Dispatch-Extension: `context_topology(...) == "per-provider"` → Kern + ggf. Adapter; sonst unveränderter Pfad. Ziel-Dateiname wird hier gewählt (nicht IC-08). |
| `scripts/lib/variables.py:conditional_vars` | geändert (Phase 2) | `GATE_NEUTRAL` ergänzt; **kein** Eintrag in `RUNTIME_GATE_TIERS`. |
| `scripts/lib/consistency/placeholders.py:_BUILTIN_VARS` | geändert (Phase 2) | `GATE_NEUTRAL` ergänzt (Muster `:84-85`). |
| `scripts/lib/consistency/context_topology.py:check_context_topology_consistency` | neu (IC-10) | `(root, config=None, provider_config=None) -> list[Finding]`; WARNING/INFO für Enum-Verstoß, Adapter-Kollision, fehlenden Kern-Ref, verwaisten Adapter in `unified`. |
| `scripts/lib/consistency/context_size.py:check_context_file_size` | geändert (IC-13) | Zählt zusätzlich Adapter-Pfade aus `provider_config[p].context_adapter_file` separat gegen `context_file.max_lines`. |

## File Structure

### Neue Dateien

- Create: `tests/test_context_topology_schema.py` — Schema-Akzeptanz/Reject für `context_file.topology`/`core_file`/`provider-overrides` (AC-11).
- Create: `tests/test_context_adapters.py` — Adapter-Registry-Invariant, `per-provider`-Render, Import/Pointer, Idempotenz, Index/Hash, Rollback (AC-12…AC-18, AC-22/AC-23/AC-26).
- Create: `tests/test_context_topology_consistency.py` — Findings des neuen Consistency-Checks (AC-19).
- Create: `tests/test_context_topology_admin.py` — UI-Shape des `topology`-Dropdowns inkl. Default/Help-Text (AC-20).
- Create: `tests/test_context_topology_documented.py` — Doku-Hinweise `context_file.topology` (Decision-Freeze).
- Create: `docs/spikes/2026-09-14-f-rulesloc-gemini-rules-channel.md` — F-RULESLOC-Verifikationsprotokoll + Verdict (Kanal (a) vs. Fallback (c)).
- Create: `tests/manual/f-rulesloc-gemini-rules-channel.md` — reproduzierbares Real-Repo-Prüfverfahren (Gemini/Antigravity Workspace-Rules).
- Create: `tests/manual/phase2-adapter-hypothesis.md` — dokumentierte HYPOTHESIS-Verifikation für Codex/Copilot/Continue/Mammouth + Gemini `context.fileName` (AC-22/AC-26).
- Create: `tests/scenarios/configs/63-context-file-modes.project.yaml` — Szenario-Config (`unified`-Default + `per-provider`-Lauf).
- Create: `tests/scenarios/asserts/63-context-file-modes.sh` — Assertions `unified` byte-identisch / committed-`AGENTS.md`-`--check` rc 0 / `per-provider` Kern + Adapter (AC-21, aus Phase-0-AC-06 verschoben).
- Create: `scripts/lib/consistency/context_topology.py` — Topologie-Consistency-Check (IC-10).

### Geänderte Dateien

- Modify: `config/project-config.schema.json` — `context_file`-Block um `topology`/`core_file`/`provider-overrides` erweitern (`:885-916`, `additionalProperties: false` bleibt).
- Modify: `scripts/lib/config.py` — `fill_defaults` (`:886`) persistiert Default `unified`.
- Modify: `scripts/lib/providers.py` — `context_topology` (IC-05) + `resolve_context_filename`-Adapter-Regel (IC-08).
- Modify: `config/ai-providers.yaml` — Adapter-Keys für Claude (Phase 1), dann Codex/Copilot/Continue/Mammouth + Gemini `context_adapter_settings` (Phase 2).
- Modify: `scripts/lib/context.py` — `per-provider`-Render/Dispatch (IC-09), Kern-/Adapter-Ziel-Selektion.
- Modify: `scripts/lib/sync_pipeline.py` — Rollback-Cleanup-Wiring (moduswechsel-getriebene Adapter-Entfernung).
- Modify: `scripts/lib/variables.py` — `GATE_NEUTRAL` in `conditional_vars` (`:235`).
- Modify: `scripts/lib/consistency/placeholders.py` — `GATE_NEUTRAL` in `_BUILTIN_VARS` (`:84-85`).
- Modify: `rules/1-generic/use-orchestrator.md` — Neutral-Render-State des Kerns.
- Modify: `rules/1-generic/a2a-delegation-gates.md` — Verweis „multiple providers, see adapter".
- Modify: `scripts/consistency-check.py` — Import (`:43`) + Registrierung (`:202`) von `check_context_topology_consistency`; Help-Mapping für `context_file.topology`.
- Modify: `scripts/lib/consistency/context_size.py` — Adapter-Pfade mitzählen (IC-13).
- Modify: `scripts/admin-server.py` — verifizieren/halten, dass `"context_file"` in `PROJECT_WRITABLE_SECTIONS` (`:230-249`, aktuell `:239` bereits enthalten) bleibt.
- Modify: `docs/ui/admin-ui.html` — `contextFile`-Block (`:6170-6481`) um `topology`-Dropdown + Help-Text erweitern.
- Modify: `templates/configs/GEMINI.settings-template.json` — `context.fileName`-Key (Kandidat (b), Phase 2).
- Modify: `tests/test_context_file_modes.py` — Resolver-Präzedenz/Fail-safe ergänzen (AC-10).
- Modify: `tests/test_provider_context_filename.py` — Legacy-Cleanup-Adapter-Regel (IC-08).
- Modify: `tests/test_provider_agnostic_dispatch.py` — Registry-Invariant + `consistency/context_topology` in `_TOUCHED_MODULES`.
- Modify: `tests/test_runtime_gate_rendering.py` — Neutral-Kern-Render (Phase 2).
- Modify: `tests/test_generated_file_drift.py` — Adapter-Drift (AC-17).
- Modify: `tests/test_context_size_guard.py` — Adapter-Size-Guard (AC-24).
- Modify: `tests/test_admin_server.py`, `tests/test_admin_ui_git_section.py` — Writable-Section + Help-Mapping (AC-20).
- Modify: `tests/scenarios/registry.md` — Zeile `63-context-file-modes`.
- Modify: `docs/providers/multi-provider.md`, `docs/guides/context-block-inventory.md` — `context_file.topology` dokumentieren.

### Step-Agent-Map (plan-driven `implement`)

| Step | Task | Agent |
|------|------|-------|
| 1 | Schema + Defaults (`context_file.topology`) | senior-developer |
| 2 | Resolver `context_topology` + Legacy-Filename-Regel | senior-developer |
| 3 | Adapter-Capability-Registry + Invariante | senior-developer |
| 4 | F-RULESLOC-Verifikation (Gate Kanal (a)) | explorer |
| 5 | `per-provider` Kern-/Adapter-Render + Dispatch | senior-developer |
| 6 | Rollback auf `unified` | developer |
| 7 | Phase-1-Verifikations-Gate | developer |
| 8 | `GATE_NEUTRAL`-Kern-Render-State | senior-developer |
| 9 | Restliche Adapter hinter HYPOTHESIS | developer |
| 10 | Consistency-Check `context_topology` | developer |
| 11 | Adapter-Size-Guard | developer |
| 12 | Admin-UI / Server | developer |
| 13 | Szenario 63 | developer |
| 14 | Doku `context_file.topology` | documenter |
| 15 | Phase-2-Verifikations-Gate | developer |

---

## Phase 1 — `per-provider`-Kern

### Task 1: Schema + Defaults (`context_file.topology`)

**Files:**
- Modify: `config/project-config.schema.json`
- Modify: `scripts/lib/config.py`
- Create: `tests/test_context_topology_schema.py`

**Interfaces:** (Produces / Consumes)
- Produces: Schema-Member `context_file.topology` (`enum`, `default "unified"`), `context_file.core_file` (`string`, `default "AGENTS.md"`), `context_file.provider-overrides` (`<Provider> → {topology}`, `additionalProperties: false`); `fill_defaults`-Default.
- Consumes: bestehender `context_file`-Block (`config/project-config.schema.json:885-916`); `fill_defaults` (`scripts/lib/config.py:886`).

**Agent:** senior-developer
**Depends on:** —

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_context_topology_schema.py::test_topology_enum_accepted` (AC-11: `topology: per-provider` + `core_file: "AGENTS.md"` + `provider-overrides: {Gemini: {topology: unified}}` validiert), `::test_topology_out_of_enum_rejected`, `::test_topology_unknown_subkey_rejected` (AC-11: `additionalProperties: false`), `::test_core_file_non_string_rejected`, `::test_provider_overrides_unknown_subkey_rejected`, `::test_absence_resolves_unified` (AC-11: fehlender Key gültig). `pytest.importorskip("jsonschema")` wie `tests/test_subagent_permissions_schema.py`.
- [ ] Step 2: Implementieren — im `context_file`-Block (`:885-916`) `topology`, `core_file`, `provider-overrides` als Geschwister von `mode` ergänzen; `additionalProperties: false` (`:915`) unverändert lassen. `provider-overrides` als `additionalProperties: {type: object, additionalProperties: false, properties: {topology: {enum}}}` (Muster `orchestrator.provider-overrides`). In `scripts/lib/config.py::fill_defaults` den Default `context_file.topology: unified` nur bei fehlendem Key persistieren; kein neues Pflichtfeld.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_context_topology_schema.py tests/test_spec_plan_config_schema.py tests/test_config_null_blocks.py -q` → rc 0; danach `rtk python3 scripts/sync.py --validate` → rc 0.
- [ ] Step 4: Commit — `feat: declare context_file topology keys in project schema`.

**Acceptance:** AC-11.

---

### Task 2: Resolver `context_topology` + Legacy-Filename-Regel

**Files:**
- Modify: `scripts/lib/providers.py`
- Modify: `tests/test_context_file_modes.py`
- Modify: `tests/test_provider_context_filename.py`

**Interfaces:** (Produces / Consumes)
- Produces: `context_topology(config: Optional[dict], provider: Optional[str] = None) -> str` (Präzedenz Provider-Override > Projekt > `"unified"`; nicht-Mapping/nicht-String/out-of-enum → `"unified"`, wirft nie); `resolve_context_filename`-Erweiterung für `context_adapter: true` → `context_adapter_file` mit Fallback auf die bestehende Auflösung.
- Consumes: `config["context_file"]`; `resolve_context_filename` (`providers.py:255`); bestehende Phase-0-Symbole (`_runtime_gate_bundle`, `shared_runtime_gate_vars`) bleiben unberührt.

**Agent:** senior-developer
**Depends on:** 1

**Steps:**
- [ ] Step 1: Test schreiben (fail) — in `tests/test_context_file_modes.py`: `::test_context_topology_provider_override_wins` (AC-10: Override `Gemini: unified` + Projekt `per-provider` → `unified` für `Gemini`, `per-provider` für `Opencode`), `::test_context_topology_default_when_absent` (AC-10), `::test_context_topology_out_of_enum_falls_back` (AC-10: `"garbage"` → `unified`), `::test_context_topology_non_mapping_config_never_raises` (AC-10), `::test_context_topology_provider_none_uses_project_value`. In `tests/test_provider_context_filename.py`: `::test_adapter_flag_returns_adapter_file`, `::test_adapter_flag_empty_file_falls_back_to_existing_resolution`.
- [ ] Step 2: Implementieren — in `scripts/lib/providers.py` `context_topology` als Leaf-Resolver (Muster `variables._resolve_orch_mode`): `cfg = config if isinstance(config, dict) else {}`; `block = cfg.get("context_file")`; `block` nicht-Mapping → `"unified"`; Override `block.get("provider-overrides", {}).get(provider, {}).get("topology")` prüfen, dann `block.get("topology")`, jeweils nur bei `in ("unified","per-provider")`; sonst `"unified"`. `resolve_context_filename` um die IC-08-Regel ergänzen (`pc.get("context_adapter") is True` und nicht-leeres `context_adapter_file` → dieses zurückgeben). Keine Provider-Literale.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_context_file_modes.py tests/test_provider_context_filename.py tests/test_runtime_gate_config.py tests/test_runtime_gate_wiring.py -q` → rc 0.
- [ ] Step 4: Commit — `feat: resolve context_file topology and adapter filename`.

**Acceptance:** AC-10.

---

### Task 3: Adapter-Capability-Registry + Invariante

**Files:**
- Modify: `config/ai-providers.yaml`
- Create: `tests/test_context_adapters.py`
- Modify: `tests/test_provider_agnostic_dispatch.py`

**Interfaces:** (Produces / Consumes)
- Produces: Claude-Block (`config/ai-providers.yaml:2-47`) mit `context_adapter: true`, `context_adapter_file: "CLAUDE.md"`, `context_adapter_import: "@{core}"`, `context_adapter_import_supported: true`, `context_adapter_settings: false`; Registry-Invariante (jeder Adapter-Provider hat nicht-leere Datei + expliziten Import-Support-Boolean, keine zwei Adapter zeigen auf dieselbe Datei).
- Consumes: Claude-Block als einziger `has_dedicated_context_file`-Provider (`:5/:7`); `_TOUCHED_MODULES` (`tests/test_provider_agnostic_dispatch.py:27-51`). Hinweis: Adapter-Detektion läuft über die `ai-providers.yaml`-Keys (IC-07 erlaubt alternativ die Capability `context-adapter`; `provider-capabilities.yaml` wird in Phase 1 nicht geändert).

**Agent:** senior-developer
**Depends on:** 2

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_context_adapters.py::test_adapter_providers_have_file_and_import_support` (AC-12), `::test_no_two_adapters_share_a_file` (AC-12), `::test_non_adapter_providers_have_no_adapter_keys` (AC-12), `::test_claude_is_the_only_phase1_adapter`. In `tests/test_provider_agnostic_dispatch.py` einen Fall ergänzen, der `context_adapter`-Keys ohne Provider-Literal prüft.
- [ ] Step 2: Implementieren — die fünf Keys im Claude-Block ergänzen. Keine Keys für Gemini/Antigravity (Kanal ist `has_rules`/`rules_dir`, kein Adapter) und keine für opencode/KimiCode/ZCode (Direkt-Leser). Keine Provider-Namen im Python-Code; die Test-Invariante liest die Registries datengetrieben.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_context_adapters.py tests/test_provider_agnostic_dispatch.py tests/test_provider_hooks_config.py -q` → rc 0; danach `rtk python3 scripts/sync.py --validate` → rc 0.
- [ ] Step 4: Commit — `feat: add context adapter capability keys for claude`.

**Acceptance:** AC-12.

---

### Task 4: F-RULESLOC-Verifikation (Gate für Kanal (a))

**Files:**
- Create: `docs/spikes/2026-09-14-f-rulesloc-gemini-rules-channel.md`
- Create: `tests/manual/f-rulesloc-gemini-rules-channel.md`

**Interfaces:** (Produces / Consumes)
- Produces: reproduzierbares Verifikationsprotokoll + **Verdict** (`PASS` = Kanal (a) `.gemini/rules` wird gelesen; `FAIL` = Fallback (c)); dokumentierte Entscheidung, welcher Kanal Gemini/Antigravity in `per-provider` trägt.
- Consumes: `config/ai-providers.yaml:95` (`rules_dir: .gemini/rules`), `:97-99` (`hook_protocol`, `hooks_dir`/`hooks_config_file` = `.agents/...`), `config/provider-capabilities.yaml:94` (`runtime_gate: hook`); Repository-Evidenz `.gemini/rules/` vs. `.agents/`.

**Agent:** explorer
**Depends on:** 3

**Steps:**
- [ ] Step 1: Evidenz erheben (fail-first dokumentieren) — `rtk grep -n "rules_dir\\|hooks_dir\\|hooks_config_file" config/ai-providers.yaml`; `rtk find .agents -maxdepth 3`; `rtk find .gemini -maxdepth 2`; `rtk read .gemini/rules/use-orchestrator.md`. Ergebnis: `rules_dir: .gemini/rules` weicht von der dokumentierten Antigravity-Lokation `.agents/rules` ab; `.agents/` enthält kein `rules/`. Protokoll in `tests/manual/f-rulesloc-gemini-rules-channel.md` anlegen.
- [ ] Step 2: Real-Repo-Check definieren und ausführen — Prozedur: in einem echten Antigravity-Workspace eine Always-On-Rule unter `.gemini/rules/` **und** `.agents/rules/` mit unverwechselbarem Marker ablegen, Session starten, beobachten welche Datei geladen wird; zuerst `PASS`/`FAIL` pro Kanal festhalten. Ergebnis + Rohbeobachtung im Spike-Doc.
- [ ] Step 3: Verdict setzen + Kanalentscheidung dokumentieren — `Verdict: PASS` → Kanal (a) (`.gemini/rules`, bestehender Seam, keine neuen Keys) oder `Verdict: FAIL` → Fallback (c) (geteilte `AGENTS.md`, Tier nativ per Hook; Prompt-Text = Dokumentation). Das Verdict ist bindend für Task 5 (AC-13/AC-14) und Task 8.
- [ ] Step 4: Commit — `docs: verify gemini/antigravity rules channel (F-RULESLOC)`.

**Acceptance:** Gate für AC-13/AC-14 (Gemini/Antigravity-Kanal); kein numerischer AC — Verifikationspunkt ist OQ-3/R8, Ergebnis ist Voraussetzung für die Kanal-(a)-Beanspruchung.

---

### Task 5: `per-provider` Kern-/Adapter-Render + Dispatch

**Files:**
- Modify: `scripts/lib/context.py`
- Modify: `tests/test_context_adapters.py`
- Modify: `tests/test_generated_file_drift.py`

**Interfaces:** (Produces / Consumes)
- Produces: `sync_context_adapters_for_provider` (IC-09); Dispatch-Extension in `sync_context_for_provider`; Ziel-Dateiname (`context_adapter_file` vs. `context_file.core_file`) wird hier gewählt und in `_sync_opencode_context`/`_sync_managed_block_context` durchgereicht; Import-/Pointer-Zeile; managed-index + context-hash für Adapter; Drift-Erkennung.
- Consumes: `providers.context_topology` (Task 2), Adapter-Keys (Task 3), F-RULESLOC-Verdict (Task 4), `rule_index`-Helfer (`rule_index.py:45/:110/:180`), `_record_static_hash`/`_save_context_hashes` (`context.py:80/:68`).

**Agent:** senior-developer
**Depends on:** 4

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_context_adapters.py::test_per_provider_direct_readers_stay_on_core` (AC-13: opencode/KimiCode/ZCode ohne Adapter; Gemini/Antigravity ohne `context_adapter_file`), `::test_claude_adapter_written_to_claude_md` (AC-13: gebunden an die tatsächlich geschriebene Datei), `::test_adapter_import_line_when_supported` (AC-15: `@AGENTS.md`), `::test_adapter_pointer_line_when_unsupported` (AC-15), `::test_empty_import_falls_back_to_pointer` (AC-15), `::test_claude_managed_block_has_no_gate_vars` (AC-14, F-04), `::test_per_provider_render_idempotent` (AC-16: zweiter Lauf byte-identisch, `pending == 0`), `::test_adapters_recorded_in_index_and_context_hashes` (AC-17). In `tests/test_generated_file_drift.py` einen Adapter-Drift-Fall ergänzen (AC-17).
- [ ] Step 2: Implementieren — in `scripts/lib/context.py` `sync_context_adapters_for_provider` und die `sync_context_for_provider`-Dispatch-Extension (IC-09) implementieren: Kern-Render (`context_file.core_file`) plus optionale Adapter-Datei; Import-Syntax aus `context_adapter_import`/`context_adapter_import_supported` (Fallback Pointer); der Claude-Adapters wird als `CLAUDE.md`-`context-managed-block` gerendert (keine `GATE_*` im Managed Block) und sein `hook`-Wortlaut liegt in `.claude/rules/use-orchestrator.md` (bestehender `sync_rules`-Seam); Gemini/Antigravity bleibt Direkt-Leser des Kerns, sein Tier-Träger ist `.gemini/rules` (Kanal (a), gated auf Task 4) bzw. Fallback (c). Lifecycle über `rule_index`-Helfer, Hash über `_record_static_hash`/`_save_context_hashes`; idempotent (`log.skip` bei unverändertem Inhalt); `dry_run` schreibt nie; kein `context_adapter_file` → `log.warning` + return. Kein Provider-Literal.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_context_adapters.py tests/test_generated_file_drift.py tests/test_context_agents_md_idempotency.py tests/test_provider_context_filename.py -q` → rc 0.
- [ ] Step 4: Commit — `feat: render per-provider context core and adapters`.

**Acceptance:** AC-13, AC-14, AC-15, AC-16, AC-17.

---

### Task 6: Rollback auf `unified`

**Files:**
- Modify: `scripts/lib/sync_pipeline.py`
- Modify: `tests/test_context_adapters.py`

**Interfaces:** (Produces / Consumes)
- Produces: moduswechsel-getriebene Adapter-Entfernung — bei `per-provider` → `unified` wird der Kern wieder im Shared-Weakest-Tier gerendert, jeder index-getrackte Adapter entfernt, fremde/user-Dateien ohne Index-Eintrag bleiben unberührt; `--check` `pending == 0`, kein verwaister Adapter.
- Consumes: Adapter-Index-Einträge (Task 5); `_sync_stage_legacy_cleanup` (`sync_pipeline.py:433-468`) und `cleanup_stale_managed_files` (`rule_index.py:110`).

**Agent:** developer
**Depends on:** 5

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_context_adapters.py::test_rollback_removes_indexed_adapters` (AC-18), `::test_rollback_keeps_foreign_adapter_files` (AC-18), `::test_rollback_restores_weakest_tier_core` (AC-18), `::test_rollback_check_reports_no_pending` (AC-18: kein verwaister Adapter, `pending == 0`).
- [ ] Step 2: Implementieren — in `scripts/lib/sync_pipeline.py` den Legacy-Cleanup-/Moduswechsel-Pfad so verdrahten, dass Adapter-Dateien aus dem Managed-Index bei Rückkehr zu `unified` entfernt werden (backup-first wie bestehender Cleanup), ohne Dateien ohne Index-Eintrag zu löschen. Bestehenden `resolve_context_filename`-Pfad (IC-08) nicht auf den Render-Pfad ziehen.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_context_adapters.py tests/test_cleanup_preview_cli.py tests/test_generated_file_drift.py -q` → rc 0.
- [ ] Step 4: Commit — `feat: roll back per-provider adapters on topology switch`.

**Acceptance:** AC-18.

---

### Task 7: Phase-1-Verifikations-Gate

**Files:**
- Test: `tests/test_context_topology_schema.py`, `tests/test_context_file_modes.py`, `tests/test_context_adapters.py`, `tests/test_provider_context_filename.py`

**Interfaces:** (Produces / Consumes)
- Produces: dokumentiertes, reproduzierbares Abnahmeergebnis für Phase 1; kein Produktionscode, keine neuen Dateien.
- Consumes: alle Artefakte aus Task 1 bis Task 6.

**Agent:** developer
**Depends on:** 1, 2, 3, 4, 5, 6

**Steps:**
- [ ] Step 1: Neue Unit-Suiten grün — `rtk python3 -m pytest tests/test_context_topology_schema.py tests/test_context_file_modes.py tests/test_context_adapters.py tests/test_provider_context_filename.py tests/test_generated_file_drift.py -q` → rc 0.
- [ ] Step 2: Sync-Gates — `rtk python3 scripts/sync.py --validate` → rc 0 und `rtk python3 scripts/sync.py --check` → rc 0 (Phase-0-RC0 bleibt erhalten; kein neuer Drift durch `per-provider`-Default `unified`).
- [ ] Step 3: Konsistenz & Provider-Agnostik — `rtk python3 scripts/consistency-check.py` → rc 0; `rtk python3 -m pytest tests/test_provider_agnostic_dispatch.py tests/test_no_role_routes_in_templates.py -q` → rc 0.
- [ ] Step 4: Szenario-Harness (Bestand) — `rtk bash tests/scenarios/run.sh` → alle vorhandenen Szenarien `PASS` (Szenario 63 existiert erst in Phase 2).
- [ ] Step 5: Commit — `test: verify context file modes phase 1 end to end`.

**Acceptance:** AC-10 bis AC-18 (Abnahmenachweis).

---

## Phase 2 — Restliche Adapter + Consistency + UI + Szenario

### Task 8: `GATE_NEUTRAL`-Kern-Render-State

**Files:**
- Modify: `scripts/lib/variables.py`
- Modify: `scripts/lib/consistency/placeholders.py`
- Modify: `rules/1-generic/use-orchestrator.md`
- Modify: `rules/1-generic/a2a-delegation-gates.md`
- Modify: `tests/test_context_adapters.py`
- Modify: `tests/test_runtime_gate_rendering.py`

**Interfaces:** (Produces / Consumes)
- Produces: `GATE_NEUTRAL` als **Render-State** (nicht in `RUNTIME_GATE_TIERS`); Kern `AGENTS.md` formuliert die Direktive („MAIN CHAT darf nicht selbst editieren. ALLES -> orchestrator.") ohne Runtime-Zusage; `a2a-delegation-gates` verweist auf „multiple providers, see adapter"; kein „if you are X"-Block.
- Consumes: `variables.conditional_vars` (`:235`), `placeholders._BUILTIN_VARS` (`:84-85`), `rules/1-generic/use-orchestrator.md:2-13`.

**Agent:** senior-developer
**Depends on:** 7

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_context_adapters.py::test_core_carries_neutral_directive` (AC-23), `::test_core_neutral_state_is_not_a_runtime_tier` (AC-23: `GATE_NEUTRAL` nicht in `RUNTIME_GATE_TIERS`), `::test_a2a_gates_point_at_adapter` (AC-23), `::test_no_self_identification_blocks` (AC-23/Nicht-Ziel: kein „if you are"). In `tests/test_runtime_gate_rendering.py` den Neutral-Kern-Fall ergänzen.
- [ ] Step 2: Implementieren — `GATE_NEUTRAL` in `conditional_vars` (`variables.py:235`) und `_BUILTIN_VARS` (`placeholders.py:84-85`) registrieren; `use-orchestrator.md` um den `{{#if GATE_NEUTRAL}}`-Neutral-Block ergänzen (Direktive ohne Runtime-Promise); `a2a-delegation-gates.md` um den Adapter-Verweis. `RUNTIME_GATE_TIERS` und Phase-0-Symbole unangetastet.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_context_adapters.py tests/test_runtime_gate_rendering.py tests/test_no_role_routes_in_templates.py -q` → rc 0; danach `rtk python3 scripts/consistency-check.py` → rc 0.
- [ ] Step 4: Commit — `feat: add neutral gate render state for the per-provider core`.

**Acceptance:** AC-23; schließt die AC-14-Kern-Aussage ab.

---

### Task 9: Restliche Adapter hinter HYPOTHESIS

**Files:**
- Modify: `config/ai-providers.yaml`
- Modify: `templates/configs/GEMINI.settings-template.json`
- Modify: `scripts/lib/context.py`
- Modify: `tests/test_context_adapters.py`
- Create: `tests/manual/phase2-adapter-hypothesis.md`

**Interfaces:** (Produces / Consumes)
- Produces: Adapter-Keys für Codex/Copilot/Continue/Mammouth hinter Flags (Default bleibt Direkt-Leser des Kerns); Gemini/Antigravity `context_adapter_settings: true` + capability/`settings_file`-gated Settings-Write (`context.fileName`); dokumentierte Real-Repo-HYPOTHESIS-Verifikation pro Provider.
- Consumes: Claude-Keys (Task 3) als Muster; IC-07-Keys; IC-09-Settings-Aktivierung (Task 5); bestehender Settings-Writer.

**Agent:** developer
**Depends on:** 8

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_context_adapters.py::test_phase2_providers_default_to_direct_core_reader` (AC-22), `::test_gemini_context_filename_only_with_settings_flag` (AC-26), `::test_no_adapter_without_verified_hypothesis` (AC-22), `::test_settings_write_is_capability_gated` (AC-26).
- [ ] Step 2: Implementieren — Adapter-Keys (`context_adapter`, `context_adapter_file`, `context_adapter_import`, `context_adapter_import_supported`) für Codex (`AGENTS.override.md`), Copilot (`.github/copilot/COPILOT.md`), Continue (`.continue/rules/project-context.md`), Mammouth (`MAMMOUTH.md`) nur setzen, wenn die jeweilige HYPOTHESIS im `tests/manual/phase2-adapter-hypothesis.md` als verifiziert dokumentiert ist; andernfalls bleiben sie Direkt-Leser. Gemini/Antigravity: `context_adapter_settings: true` und `templates/configs/GEMINI.settings-template.json` um den `context.fileName`-Key ergänzen; Settings-Write capability/`settings_file`-gated in `scripts/lib/context.py`. Keine Provider-Literale (Dispatch über Keys/Capability).
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_context_adapters.py tests/test_provider_agnostic_dispatch.py -q` → rc 0; danach `rtk python3 scripts/sync.py --validate` → rc 0.
- [ ] Step 4: Commit — `feat: gate phase-2 context adapters behind verified hypotheses`.

**Acceptance:** AC-22, AC-26.

---

### Task 10: Consistency-Check `context_topology`

**Files:**
- Create: `scripts/lib/consistency/context_topology.py`
- Modify: `scripts/consistency-check.py`
- Create: `tests/test_context_topology_consistency.py`
- Modify: `tests/test_provider_agnostic_dispatch.py`

**Interfaces:** (Produces / Consumes)
- Produces: `check_context_topology_consistency(root, config=None, provider_config=None) -> list[Finding]`; Registrierung in `scripts/consistency-check.py`; `consistency/context_topology` in `_TOUCHED_MODULES`.
- Consumes: `Finding`/`Severity`-Muster (`consistency/context_size.py:114-127`); Registrierung neben `check_context_file_size` (`consistency-check.py:43/:202`); Adapter-Keys (Task 3/9).

**Agent:** developer
**Depends on:** 9

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_context_topology_consistency.py::test_invalid_enum_warns` (AC-19), `::test_adapter_file_collision_warns` (AC-19), `::test_missing_core_reference_warns` (AC-19), `::test_orphaned_adapter_in_unified_warns` (AC-19), `::test_consistent_config_has_no_finding` (AC-19).
- [ ] Step 2: Implementieren — `scripts/lib/consistency/context_topology.py` mit `check=`-ID und `Finding`/`Severity`-Muster; in `scripts/consistency-check.py` Import (`:43`-Umfeld) und Aufruf (`:202`-Umfeld) ergänzen; `consistency/context_topology` in `_TOUCHED_MODULES` (`tests/test_provider_agnostic_dispatch.py:27-51`) aufnehmen.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_context_topology_consistency.py tests/test_provider_agnostic_dispatch.py -q` → rc 0; danach `rtk python3 scripts/consistency-check.py` → rc 0.
- [ ] Step 4: Commit — `feat: add context topology consistency check`.

**Acceptance:** AC-19.

---

### Task 11: Adapter-Size-Guard

**Files:**
- Modify: `scripts/lib/consistency/context_size.py`
- Modify: `tests/test_context_size_guard.py`

**Interfaces:** (Produces / Consumes)
- Produces: `check_context_file_size` iteriert zusätzlich Adapter-Pfade aus `provider_config[p].context_adapter_file`; WARNING nennt den Adapter-Pfad separat; `context_file.max_lines` gilt; `oversize_acknowledged` unterdrückt.
- Consumes: `check_context_file_size` (`context_size.py:44`, Iteration `:91-101`); Adapter-Keys (Task 3/9).

**Agent:** developer
**Depends on:** 9

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_context_size_guard.py::test_oversized_adapter_warns_separately` (AC-24), `::test_adapter_respects_max_lines` (AC-24), `::test_acknowledged_adapter_suppressed` (AC-24), `::test_missing_adapter_is_not_reported`.
- [ ] Step 2: Implementieren — die Pfad-Iteration in `check_context_file_size` um Adapter-Pfade erweitern; Kern- und Adapter-Pfade getrennt melden. Bestehende Kern-Semantik unverändert.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_context_size_guard.py tests/test_context_topology_consistency.py -q` → rc 0.
- [ ] Step 4: Commit — `feat: count context adapters against the size guard`.

**Acceptance:** AC-24.

---

### Task 12: Admin-UI / Server

**Files:**
- Modify: `scripts/admin-server.py`
- Modify: `docs/ui/admin-ui.html`
- Modify: `tests/test_admin_server.py`
- Modify: `tests/test_admin_ui_git_section.py`
- Create: `tests/test_context_topology_admin.py`

**Interfaces:** (Produces / Consumes)
- Produces: Schreibzugriff auf die `context_file`-Sektion akzeptiert (`"context_file"` in `PROJECT_WRITABLE_SECTIONS`); UI-`topology`-Dropdown (Default `unified`) + Help-Text, der Topologie von Dichte (`context_file.mode`) abgrenzt; `check_ui_help_mappings` ohne Finding für `context_file.topology`.
- Consumes: `PROJECT_WRITABLE_SECTIONS` (`admin-server.py:230-249`, aktuell `:239` bereits `"context_file"`); `viewProject`-`contextFile`-Block (`admin-ui.html:6170-6481`); Help-Mapping (`consistency-check.py:197`); Registrierung aus Task 10 (Sequenz, gemeinsame Datei `consistency-check.py`).

**Agent:** developer
**Depends on:** 10

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_admin_server.py::test_context_file_section_write_accepted` (AC-20), `tests/test_context_topology_admin.py::test_topology_dropdown_default_unified` (AC-20), `::test_help_text_distinguishes_topology_from_density` (AC-20); in `tests/test_admin_ui_git_section.py` einen Help-Mapping-Fall ergänzen (Muster `:63-67`).
- [ ] Step 2: Implementieren — `"context_file"` in `PROJECT_WRITABLE_SECTIONS` verifizieren/halten; in `docs/ui/admin-ui.html` den `contextFile`-Block um `topology` (Default `unified`) und `core_file` (Default `AGENTS.md`) erweitern, `topology` als Dropdown rendern und Help-Text ergänzen; Help-Eintrag für `context_file.topology` im `check_ui_help_mappings`-Katalog. Kein neuer Top-Level-`context`-Abschnitt, kein neuer Endpoint.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_admin_server.py tests/test_context_topology_admin.py tests/test_admin_ui_git_section.py -q` → rc 0; danach `rtk python3 scripts/consistency-check.py` → rc 0.
- [ ] Step 4: Commit — `feat: expose context file topology in the admin ui`.

**Acceptance:** AC-20.

---

### Task 13: Szenario 63

**Files:**
- Create: `tests/scenarios/configs/63-context-file-modes.project.yaml`
- Create: `tests/scenarios/asserts/63-context-file-modes.sh`
- Modify: `tests/scenarios/registry.md`

**Interfaces:** (Produces / Consumes)
- Produces: eigenständige Consumer-Config mit `context_file.topology`-Override; ausführbares Assert-Script (beide Läufe); Katalogzeile `| \`63-context-file-modes\` | Claude, Gemini, Opencode | strict (default) | … |`.
- Consumes: `providers.context_topology` (Task 2), `per-provider`-Render (Task 5), Rollback (Task 6), Scenario-Harness-Vertrag (`cwd` = Temp-Projekt, `$1`/`REPO_ROOT` = Checkout); Registry endet bei `62-stale-role-cleanup` (`registry.md:109`).

**Agent:** developer
**Depends on:** 6, 9, 11, 12

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/scenarios/asserts/63-context-file-modes.sh` mit `fail()`-Helper und `REPO_ROOT`-Prüfung anlegen; `chmod +x`; Registry-Zeile nach `62-stale-role-cleanup` ergänzen. Auf `dry_rc=0 && sync_rc=0 && val_rc=0 && assert_rc=0` auslegen.
- [ ] Step 2: Implementieren — Config mit minimalem Sync-Setup (Claude/Gemini/Opencode) und einem zweiten Lauf mit `per-provider`. Assert-Script: (a) `unified`-Default-Lauf byte-identisch zum Bestand, `--check` rc 0 auf der committed `AGENTS.md`; (b) `per-provider`-Lauf erzeugt Kern + Claude-Adapter `CLAUDE.md`, Gemini/Antigravity bleibt Direkt-Leser des Kerns; jede Abweichung ruft `fail`.
- [ ] Step 3: Test (pass) — `rtk bash tests/scenarios/run.sh 63` → `PASS` (rc 0); danach `rtk bash tests/scenarios/run.sh` vollständig → alle `PASS`.
- [ ] Step 4: Commit — `test: add scenario 63 for context file modes`.

**Acceptance:** AC-21.

---

### Task 14: Doku `context_file.topology`

**Files:**
- Modify: `docs/providers/multi-provider.md`
- Modify: `docs/guides/context-block-inventory.md`
- Create: `tests/test_context_topology_documented.py`

**Interfaces:** (Produces / Consumes)
- Produces: Doku der Topologie-Achse `context_file.topology` (`unified` default / `per-provider`), Abgrenzung zu `context_file.mode` (Dichte), Kanal-Matrix (Direkt-Leser, Claude-Adapter, Gemini/Antigravity-Rules-Kanal + Fallback (c)).
- Consumes: Task 4-Verdict, Task 8/9-Render-Semantik; bestehende Doku-Struktur.

**Agent:** documenter
**Depends on:** 8, 12

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_context_topology_documented.py::test_topology_switch_documented` prüft, dass beide Doku-Dateien `context_file.topology`, `unified` und `per-provider` nennen und die Abgrenzung zu `mode` (Dichte) erklären; `::test_fallback_c_documented` prüft den dokumentierten Fallback (c).
- [ ] Step 2: Implementieren — `docs/providers/multi-provider.md` und `docs/guides/context-block-inventory.md` um einen Topologie-Abschnitt erweitern (Default, Präzedenz, Kanal-Matrix inkl. F-RULESLOC-Fallback). Keine Rollen-Namen, keine Route-Sätze.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_context_topology_documented.py tests/test_no_role_routes_in_templates.py -q` → rc 0.
- [ ] Step 4: Commit — `docs: document context file topology switch`.

**Acceptance:** trägt AC-10/AC-11-Dokumentation (kein eigener numerischer AC).

---

### Task 15: Phase-2-Verifikations-Gate

**Files:**
- Test: `tests/test_context_adapters.py`, `tests/test_context_topology_consistency.py`, `tests/test_context_topology_admin.py`, `tests/test_context_size_guard.py`, `tests/test_context_topology_documented.py`

**Interfaces:** (Produces / Consumes)
- Produces: dokumentiertes Abnahmeergebnis für Phase 1 + Phase 2; kein Produktionscode.
- Consumes: alle Artefakte aus Task 1 bis Task 14.

**Agent:** developer
**Depends on:** 7, 8, 9, 10, 11, 12, 13, 14

**Steps:**
- [ ] Step 1: Alle neuen Unit-Suiten grün — `rtk python3 -m pytest tests/test_context_topology_schema.py tests/test_context_file_modes.py tests/test_context_adapters.py tests/test_context_topology_consistency.py tests/test_context_topology_admin.py tests/test_context_size_guard.py tests/test_context_topology_documented.py -q` → rc 0.
- [ ] Step 2: Sync-Gates — `rtk python3 scripts/sync.py --validate` → rc 0 und `rtk python3 scripts/sync.py --check` → rc 0.
- [ ] Step 3: Konsistenz — `rtk python3 scripts/consistency-check.py` → rc 0 (inkl. Topologie- und Help-Mapping-Checks).
- [ ] Step 4: Szenario-Harness vollständig — `rtk bash tests/scenarios/run.sh` → alle Szenarien `PASS`, insbesondere `63-context-file-modes`.
- [ ] Step 5: Ratchets unverändert grün — `rtk python3 -m pytest tests/test_provider_agnostic_dispatch.py tests/test_no_role_routes_in_templates.py tests/test_provider_hooks_config.py tests/test_runtime_gate_rendering.py -q` → rc 0.
- [ ] Step 6: Commit — `test: verify context file modes end to end`.

**Acceptance:** AC-19 bis AC-26 (Abnahmenachweis); AC-25 ist Phase 0 (bereits committed).

---

## Acceptance-Criteria → Task-Mapping

| AC | Phase | Task(s) |
|----|-------|---------|
| AC-10 | 1 | 2 |
| AC-11 | 1 | 1 |
| AC-12 | 1 | 3 |
| AC-13 | 1 | 5 (Kanal (a) gated durch 4) |
| AC-14 | 1 | 5, 8 |
| AC-15 | 1 | 5 |
| AC-16 | 1 | 5 |
| AC-17 | 1 | 5 |
| AC-18 | 1 | 6 |
| AC-19 | 2 | 10 |
| AC-20 | 2 | 12 |
| AC-21 | 2 | 13 |
| AC-22 | 2 | 9 |
| AC-23 | 2 | 8 |
| AC-24 | 2 | 11 |
| AC-25 | 0 | Phase 0, bereits committed (`tests/test_context_file_modes.py`) — nicht Teil dieses Plans |
| AC-26 | 2 | 9 |

## Rollback / Safety-Net

- **Default ist `unified`:** Ohne explizites `context_file.topology: per-provider` ändert sich das Layout nicht; der Schalter kann pro Provider über `context_file.provider-overrides.<Provider>.topology` zurückgestellt werden.
- **Rollback-Pfad (AC-18):** `per-provider` → `unified` entfernt index-getrackte Adapter über `cleanup_stale_managed_files` (backup-first), lässt fremde/user-Dateien ohne Index-Eintrag unberührt und konvergiert auf `pending == 0`. Kein manueller Dateieingriff nötig.
- **F-RULESLOC-Fallback (c):** Schlägt Task 4 fehl, wird Kanal (a) nicht beansprucht; Gemini/Antigravity bleibt auf der geteilten `AGENTS.md` mit nativer Hook-Erzwingung (Prompt-Text = Dokumentation). Kein Config-Bruch, kein Rollback nötig — die Kanalentscheidung ist datengetrieben.
- **Phase-0-Schutz:** `runtime_gate.py` wird nicht berührt; `providers.py::runtime_gate_vars`-Contract und `_build_managed_block`-Shared-Override bleiben byte-identisch; `sync.py --check` bleibt rc 0.
- **Phase-2-Provider bleiben aus:** Codex/Copilot/Continue/Mammouth und Gemini `context.fileName` werden erst nach dokumentierter HYPOTHESIS-Verifikation scharfgeschaltet; andernfalls bleiben sie Direkt-Leser (AC-22).
- **Traversal-/Ownership-Schutz:** Adapter-Pfade laufen über `safe_path`/den bestehenden Managed-Index; keine Datei außerhalb `project_root`; kein Worktree.

## Self-Review

- **AC-Abdeckung:** Alle AC-10 … AC-26 sind mindestens einer Task zugeordnet; AC-25 ist Phase 0 (committed) und explizit ausgewiesen; kein AC ohne Task, keine Task ohne AC-Bezug (Task 4 = Gate, Task 14 = Doku).
- **Test je Task:** Jede Task besitzt eine konkrete, benannte Testdatei und ein `rtk`-präfigiertes Verifikationskommando mit erwartetem rc; Task 7/15 sind die expliziten Abnahme-Gates; Task 4 belegt sein Ergebnis über ein dokumentiertes Real-Repo-Protokoll statt über eine Unit-Suite.
- **Traceability:** `spec-id: SPEC-CONTEXT-FILE-MODES-2026-09-13` ↔ `**Spec:**`-Pfad ↔ Task-ID ↔ Testname ist durchgängig; `pipeline_stages.implement` zeigt auf Step 1 der Step-Agent-Map (Agent `senior-developer`).
- **Interface-Vollständigkeit:** Jede Task hat nicht-leere `Produces`/`Consumes`; alle neuen Symbole sind mit Datei, Name und Signatur benannt; jede referenzierte `file:Symbol` existiert oder wird durch eine Task eingeführt.
- **Abhängigkeiten:** Der Graph ist zyklenfrei und vorwärtsgerichtet (1→2→3→4→5→6→7→8; 8→9 mit 10/11 sequenziell nach 9; 10→12; 6/9/11/12→13; 8/12→14; 7…14→15).
- **Datei-Ownership:** Keine Datei wird von zwei **parallelen** Tasks geschrieben. Sequenzielle Mehrfachnutzung (nur `scripts/lib/context.py` in Task 5/8/9, `config/ai-providers.yaml` in Task 3/9, `tests/test_context_adapters.py` in Task 3…9) ist über strikt vorwärtsgerichtete `Depends on`-Kanten entkoppelt. Die bekannte Validator-Limitierung (`validate_plan` wendet `file_overlap` ohne `kind`-Gate an) kann gekoppelte Dateien über sequenzielle Kanten hinweg melden — dokumentierte Limitierung, keine Ownership-Verletzung.
- **Rahmenbedingungen:** Provider-agnostisch (kein Provider-Literal; Adapter-Dispatch über Keys/Capability), Stdlib-only, Py3.9-konform, byte-identischer `unified`-Default, Phase-0-Contracts unberührt, keine Rollen-Routen, keine Modellnamen.
- **No-Placeholder:** Keine `TODO`/`TBD`/`...`-Marker, keine leeren `Interfaces:`; exakte Pfade, Symbole, Signaturen, Testnamen und Commit-Messages.
- **Keine Implementierung:** Dieser Plan ändert keinen Code; Phase 1/2 startet erst auf expliziten Start.

## Ausführungs-Handoff

- **Reihenfolge:** Task 1 → Task 15 in aufsteigender Numerik. Task 4 ist das harte Gate: Task 5 darf den Gemini/Antigravity-Kanal nur als (a) beanspruchen, wenn Task 4 `Verdict: PASS` liefert; sonst gilt Fallback (c). Task 8 beginnt Phase 2, Task 10/11 laufen nach Task 9, Task 13 integriert 6/9/11/12, Task 15 schließt ab.
- **Task-für-Task (SDD):** Jeder Task wird von einem frischen Subagenten mit frischem Kontext ausgeführt, zweistufig reviewt (Requirement-Treue → Qualität) und erst dann committet; die Ledger-Checkboxen werden nach Task-Abschluss über den Writer aktualisiert. Kein Task ohne Test und Commit.
- **Blocked-Regel:** Kann eine Task ihre Akzeptanz nicht belegen (insbesondere Task 4 ohne Real-Repo-Zugang), bleibt sie offen (`- [ ]`), wird an den Orchestrator eskaliert und blockiert Nachfolger; sie wird nie stillschweigend übersprungen oder umsortiert. Für Task 4 gilt dann konservativ Fallback (c).
- **Shared-File-Reihenfolge:** `scripts/lib/context.py`, `scripts/lib/providers.py`, `scripts/lib/sync_pipeline.py`, `config/project-config.schema.json` sind vom committed Phase-0-Stand berührt/umgeben; Änderungen additiv über dem Stand anwenden, keinen Phase-0-Block umsortieren.
- **Abschluss-Gate:** Vor Freigabe laufen `rtk python3 scripts/sync.py --validate` (rc 0), `rtk python3 scripts/sync.py --check` (rc 0), `rtk python3 scripts/consistency-check.py` (rc 0), `rtk bash tests/scenarios/run.sh` (alle `PASS`, inkl. `63-context-file-modes`) sowie die in Task 15 genannten Ratchet-Suiten (rc 0).
