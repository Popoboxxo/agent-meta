---
pipeline_stages:
  implement: 1
---

# Implementierungsplan — OpenCode Runtime Gate (Problem A)

> Status: IN PROGRESS

> **Revision / Status (2026-09-14):**
> (a) Phase 0, Tasks 1–6, ist implementiert und getestet (Unit-Tests + Repo-Gate grün).
> (b) Das abschließende Phase-0-Verifikations-Gate (Task 7) ist noch offen: `scripts/sync.py --check`
> liefert rc 1, bis die generierten Artefakte per HITL-`sync.py`-Lauf regeneriert sind.
> (c) Das Phase-1-Szenario wurde von `62` auf `63-opencode-runtime-gate` umnummeriert, weil
> `62-stale-role-cleanup` die ID `62` inzwischen belegt.
> (d) Offener Reconcile-Punkt: Der AC-24-Schema-Key `runtime-gate.plugin-mode` wurde bereits in
> Phase 0 (Task 5) implementiert, obwohl die Global Constraints den Root-Key `runtime-gate` (IC-16)
> der zurückgestellten Phase-1-Task 8 zuordnen. Bewusst keine stille Umschreibung der Global
> Constraints — User-Entscheidung ausstehend.

**Spec:** `docs/specs/2026-09-13-opencode-runtime-gate-design.md`

> Trace-Anker: `spec-id: SPEC-OPENCODE-RUNTIME-GATE-2026-09-13` (Status APPROVED)
> Systemdesign: `docs/specs/2026-09-13-opencode-runtime-gate-system-design.md` (Entwurf; an D-C1 … D-C5 stale, normativ ist die Spec)
> Verwandte Issues: #794 (Problem A), #747 (create-only Settings-Initializer), #765 (`deriveSubagentSessionPermission`).

**Goal:** Den in `rules/1-generic/use-orchestrator.md` unbedingt versprochenen CRITICAL GATE auf OpenCode ehrlich und gestuft ausliefern — Phase 0 (A2+A3+A4): eine provider-agnostische Tier-Auflösung (`hook|plugin|permission|advisory`), eine Main-Chat-Write/Bash-Deny-Schicht über den **bestehenden** `isolation.py`-Merge-Pfad (nie über den create-only `context._init_provider_settings_json`, #747), eine gestufte Rules-/Context-Ausgabe (byte-identisch für Hook-Provider) und eine tier-abgeleitete Consistency-Severity. Die native Plugin-Tier (A1) wird nur als capability-gegatete, **zurückgestellte** Phase-1-Aufgabe geplant (`observe`, kein „fully enforced").
**Architecture:** Ein provider-agnostisches Leaf-Modul `scripts/lib/runtime_gate.py` trägt in Phase 0 die kanonische Tier-Vokabel (`RUNTIME_GATE_TIERS`); der Tier-Resolver bleibt per IC-03 die einzige Wahrheitsquelle in `scripts/lib/providers.py` (`provider_runtime_gate_supported`, `provider_runtime_gate_tier`, `runtime_gate_vars`) und liest die Maschinen-Flags aus `ai-providers.yaml` (`pc`) plus die deklarierte Tier aus `provider-capabilities.yaml` (`capabilities`, Zwei-Registry-Split D-C1). `sync_pipeline.py` injiziert das Variablen-Bundle an **beiden** Renderer-Seams (`_sync_stage_contexts` vor `sync_context_for_provider`, `_sync_stage_per_provider` vor `sync_rules`/`sync_embedded_rule_files`, F-02) und dispatcht den A2-Writer. A2 sitzt im `isolation.py`-Merge-Pfad (Namespaced Managed State `isolation-deny`/`runtime-gate-deny`, Mapping-Deny `{"**": "deny"}`, F-01). A4 liest dieselbe Tier. Phase 1 erweitert `runtime_gate.py` um den Plugin-Generator (IC-08) — hinter `has_plugins`/`plugin_protocol`, default `observe`, gesperrt bis P6.
**Tech Stack:** Python 3.9 (Stdlib only, `from __future__ import annotations`, `typing.Optional`/`Dict`/`List`/`Tuple`, keine PEP-604-Union-Annotationen), YAML (`config/*.yaml`), JSON Schema (`config/project-config.schema.json`), Markdown (Rules), pytest, Bash-Szenario-Harness (`tests/scenarios/run.sh`), `rtk`-präfixierte Kommandos.

## Global Constraints

- **Provider-Agnostik (hart):** Kein Provider-Literal und kein `if provider == "…"` in neuen/geänderten Modulen. Unterschiede ausschließlich über Config-Keys/Capability-Flags. `runtime_gate` und `isolation` werden in `tests/test_provider_agnostic_dispatch.py::_TOUCHED_MODULES` aufgenommen (AC-04). Der Trigger prüft `provider_runtime_gate_tier(pc, caps) == "permission"`, nie `isolation-mechanism` und nie einen Provider-Namen.
- **Phase-0-Grenze (Scope):** Implementiert werden jetzt nur A2 (Permission-Tightening), A3 (gestufte Zusage) und A4 (Consistency-Severity) plus die dafür nötigen Seams. Keine `has_plugins`/`plugin_protocol`-Keys (IC-02), kein Root-Key `runtime-gate` (IC-16), kein Plugin-Artefakt, kein Template, kein Tier `plugin`. Diese liegen in den als **DEFERRED** markierten Phase-1-Aufgaben und zählen **nicht** zu den Phase-0-Abnahmekriterien.
- **Seam-Zuschnitt:** Das neue Modul `scripts/lib/runtime_gate.py` ist der Gate-Seam. Phase 0 legt darin die kanonische Tier-Vokabel `RUNTIME_GATE_TIERS = ("hook", "plugin", "permission", "advisory")` an; der Tier-Resolver selbst bleibt per IC-03/AC-03 in `providers.py`. Phase 1 (IC-08) erweitert dasselbe Modul um den Plugin-Generator.
- **#747-Vermeidung (hart):** A2 liest und schreibt `opencode.json` ausschließlich über den bestehenden Merge-Pfad `isolation.py` (`_read_json_safe` / `write_checked`). `context._init_provider_settings_json` (`context.py:838-880`, rendert nur wenn die Datei fehlt) ist **nicht** der Schreibpfad; es wird kein neuer Root-Key erzwungen.
- **A2-Merge-Shape (F-01, hart):** A2 schreibt nie einen Skalar auf `permission.edit`/`permission.bash`, sondern genau einen Deny-Glob `"**"` **innerhalb** der jeweiligen Family-Map (`{"edit": {"**": "deny"}, "bash": {"**": "deny"}}`). `"**"` ist disjunkt zu allen `_dir_to_glob`-Keys des Isolation-Writers. Beide Writer normalisieren eine Family über `_permission_mapping` vor `.items()` (Skalar-Toleranz, D-C4).
- **Namespaced Managed State:** Der gemeinsame State `.opencode/agent-meta-state.json` wird in Namespaces geschrieben (`isolation-deny` bestehend, `runtime-gate-deny` neu) und per Read-Modify-Write aktualisiert; ein Writer darf den Sibling-Namespace nie überschreiben. Ownership/Rollback stellt einen vorbestehenden User-Wert am Glob `"**"` exakt wieder her.
- **Fine-Glob-Fallback (OQ-3, akzeptierte Default-Entscheidung):** Falls die Real-Repo-Verifikation zeigt, dass ein Root-Deny `orchestrator`/`git` blockiert (AN-6/OQ-3), wird A2 auf feinere `bash`/`edit`-Globs verengt — niemals auf einen gröberen Block. Bis dahin gilt die Annahme „Agent-Frontmatter-Permission übersteuert den Root-Deny".
- **Effektiver Strict-Scope (OQ-6):** A2 und die Strict-Blockade gelten nur, wenn `orchestrator.strict` für den Provider effektiv aktiv ist — dieselbe Drei-Stufen-Präzedenz wie `orchestrator_strict._resolve_effective_strict` (`provider-overrides.<p>.mode` → `orchestrator.mode` → Legacy `strict`+`enabled`). `provider-overrides` kann Strict verengen/abschalten; dann entfallen die Deny-Einträge und der Managed-State-Cleanup greift.
- **Tier-Semantik (OQ-4, hart):** `permission` = **PARTIAL** („partially enforced; delegation provenance not enforced"), niemals „fully enforced". `GATE_ENFORCED` ist nur für `hook`/`plugin` `'true'`. `advisory` schreibt nie einen Permission-Eintrag und deployt nie ein Plugin.
- **Consistency-Severity (OQ-5, D-C2):** Default WARNING für `advisory`+strict; ERROR nur bei `orchestrator.require-runtime-gate: true` (Sibling-Key, bool, Default `false`). `permission` → INFO. `hook`/`plugin` → kein Finding. Check-ID `orchestrator-strict.no-hook-support` und die effektive-Strict-Auflösung bleiben erhalten.
- **Hook-Byte-Identität (F-05):** Die `GATE_ENFORCED`-Variante reproduziert den heutigen Strict-Wortlaut verbatim (`# CRITICAL GATE` + `MAIN CHAT darf nicht selbst editieren. ALLES -> \`orchestrator\`. Keine Ausnahmen.`), sodass die Claude-/Gemini-Ausgabe byte-identisch bleibt. Die Provenienz trägt der benachbarte Tier-Hinweis in `a2a-delegation-gates.md`, nicht eine Abschwächung des Satzes.
- **Fail-safe:** Unbekannter/fehlender Provider, `None`/Nicht-Mapping `pc`, absentes `runtime_gate`, unlesbare Registry → `advisory`. Der Resolver wirft nie, ruft nie `sys.exit`, fällt nie auf eine Claude/Hook-Wahrheit zurück.
- **Phase 1 bleibt zurückgestellt (P6, #765):** Der Plugin-Generator und das `observe`-Artefakt werden als **DEFERRED** geplant; `runtime_gate: plugin`, `has_plugins: true`, `MODE=enforce` und AC-21 werden erst nach bestandener Real-Repo-Verifikation (P6) freigeschaltet. Kein Provider darf vorher `plugin` deklarieren; es wird nie „fully enforced" behauptet.
- **Py3.9 & Stdlib:** Neue Module nutzen `from __future__ import annotations`; keine externen Abhängigkeiten; `rtk python3 scripts/consistency-check.py` muss rc 0 liefern.
- **Ownership & Reihenfolge:** Jede Datei wird in genau einer Task geändert (Phase-0/Phase-1-Doppelbesitz wird explizit als sequenziell markiert), `Depends on:` referenziert immer eine frühere Task, der Graph ist azyklisch und vorwärtsgerichtet.
- **Bite-sized & TDD:** Jede Task ist einzeln testbar und committbar (Test fail → implementieren → Test pass → Commit); kein Task ist „done" ohne beobachteten Test und `rtk python3 scripts/sync.py --validate` rc 0 als Repo-Gate.
- **Bestands-Ratchets:** `tests/test_provider_hooks_config.py`, `tests/test_no_role_routes_in_templates.py`, `tests/test_provider_three_file_invariant.py` bleiben unverändert grün. Rules-Text-Churn (`AGENTS.md`/`CLAUDE.md`, `--check`-Hashes) wird bewusst aktualisiert, nicht stillschweigend.
- **Keine Rollen-Routen / keine Modellnamen:** `agents/1-generic/*` und `rules/1-generic/*` erhalten keine Route-Tabellen und keine `roleA → roleB`-Ketten; kein Marken-/Referenzmodellname in Code, Doku, Kommentaren, Commit-Messages oder diesem Plan.
- **Keine neuen Rollen:** keine Änderung an `config/role-defaults.yaml`, keine SE-Kaskade.

## Interfaces

Neue und geänderte Symbole als `file:Symbol`. Phase-0-Symbole sind jetzt implementierbar; Phase-1-Symbole sind klar als DEFERRED markiert.

| Symbol | Art | Phase | Vertrag |
|---|---|---|---|
| `scripts/lib/runtime_gate.py:RUNTIME_GATE_TIERS` | neu | 0 | `Tuple[str, ...] = ("hook", "plugin", "permission", "advisory")` — kanonische Tier-Vokabel; von `providers.py`, Consistency und Tests konsumiert |
| `scripts/lib/providers.py:SUPPORTED_PLUGIN_PROTOCOLS` | neu | 0 | `set = {"opencode-plugin-js"}` (Plugin-Analogon zu `SUPPORTED_HOOK_PROTOCOLS`) |
| `scripts/lib/providers.py:provider_runtime_gate_supported` | neu | 0 | `(pc: dict) -> bool` — `has_plugins=true` **und** `plugin_protocol in SUPPORTED_PLUGIN_PROTOCOLS` |
| `scripts/lib/providers.py:provider_runtime_gate_tier` | neu | 0 | `(pc: dict, capabilities: Optional[dict] = None) -> str` — Präzedenz `hook` > `plugin` > `permission` > `advisory`; fail-safe, wirft nie |
| `scripts/lib/providers.py:runtime_gate_vars` | neu | 0 | `(pc: dict, capabilities: Optional[dict], config: dict) -> dict` — liefert `ENFORCEMENT_TIER`, `GATE_ENFORCED`, `GATE_PARTIAL`, `GATE_ADVISORY`, `RUNTIME_GATE_PLUGIN_MODE` (alles Strings) |
| `config/provider-capabilities.yaml:capabilities.<provider>.runtime_gate` | neu | 0 | `hook \| plugin \| permission \| advisory`; explizit je Provider; `hook` für Claude/Gemini, `permission` für Opencode, `advisory` für den Rest |
| `scripts/lib/variables.py:conditional_vars` | geändert | 0 | `GATE_ENFORCED`, `GATE_PARTIAL`, `GATE_ADVISORY` ergänzt (IC-05) |
| `scripts/lib/consistency/placeholders.py:_BUILTIN_VARS` | geändert | 0 | `ENFORCEMENT_TIER`, `GATE_ENFORCED`, `GATE_PARTIAL`, `GATE_ADVISORY`, `RUNTIME_GATE_PLUGIN_MODE` ergänzt (IC-06) |
| `scripts/lib/sync_pipeline.py:_sync_stage_contexts` / `_sync_stage_per_provider` | geändert | 0 | `provider_variables.update(runtime_gate_vars(pc, caps, config))` an beiden Renderer-Seams (IC-04) + A2-Dispatch bei Tier `permission` (IC-13) |
| `scripts/lib/isolation.py:_read_state` / `_write_state` | geändert | 0 | namespaced: `(state_path, key=...)`; `_write_state(state_path, value, dry_run, key=...)` Read-Modify-Write, erhält Sibling-Namespaces |
| `scripts/lib/isolation.py:_permission_mapping` | neu | 0 | `(value) -> Dict[str, str]` — dict passt durch, Skalar-String → `{"**": value}`, sonst `{}` |
| `scripts/lib/isolation.py:_opencode_runtime_gate_entries` | neu | 0 | `(config, provider, agent_meta_root, provider_config) -> Dict[str, Dict[str, str]]` — Mapping-Deny nur bei Tier `permission`, sonst `{}`; kein Provider-Literal |
| `scripts/lib/isolation.py:_sync_opencode_runtime_gate` | neu | 0 | `(project_root, config, provider, provider_config, agent_meta_root, log, dry_run) -> None` — Merge + Ownership/Rollback über `_OPENCODE_STATE_FILE` |
| `scripts/lib/isolation.py:_STATE_ISOLATION_KEY` / `_STATE_RUNTIME_GATE_KEY` | neu | 0 | `"isolation-deny"` / `"runtime-gate-deny"` |
| `scripts/lib/consistency/orchestrator_strict.py:check_orchestrator_strict_hook_support` | geändert | 0 | Signatur `(project_root, config, provider_config, agent_meta_root)`; tier-basiertes Finding (IC-11) |
| `config/project-config.schema.json:orchestrator.require-runtime-gate` | neu | 0 | `{"type": "boolean", "default": false}` (Sibling, D-C2) |
| `rules/1-generic/use-orchestrator.md` | geändert | 0 | drei mutually-exclusive Tier-Blöcke (`GATE_ENFORCED`/`GATE_PARTIAL`/`GATE_ADVISORY`) innerhalb `{{#if ORCH_MODE_STRICT}}` (IC-07) |
| `rules/1-generic/a2a-delegation-gates.md` | geändert | 0 | Tier-Hinweis mit `{{ENFORCEMENT_TIER}}` + Verweis auf „Bekannte Grenzen" (IC-07) |
| `scripts/lib/runtime_gate.py:PLUGIN_TEMPLATE_BY_PROTOCOL` / `runtime_gate_plugin_relpath` / `sync_runtime_gate_plugins` | neu | 1 (DEFERRED) | Plugin-Generator (IC-08), nur bei `provider_runtime_gate_supported(pc)` |
| `config/ai-providers.yaml:providers.Opencode.has_plugins/plugin_dir/plugin_ext/plugin_protocol/runtime_gate-mechanism` | neu | 1 (DEFERRED) | Machinen-Wahrheit + Human-Label (IC-02); erst nach P6 wirksam |
| `config/project-config.schema.json:runtime-gate.plugin-mode` | neu | 1 (DEFERRED) | `{"type":"string","enum":["observe","enforce"],"default":"observe"}`, `additionalProperties:false` (IC-16) |
| `templates/plugins/runtime-gate.opencode-plugin.js.tmpl` | neu | 1 (DEFERRED) | Exportiertes Plugin mit sync-time baked `STRICT`/`MODE`/`AGENT_ALLOWLIST` (IC-15) |
| `scripts/lib/generated_file_drift.py:_iter_managed_files` | geändert | 1 (DEFERRED) | `plugin_dir`-`dir_spec` gated auf `has_plugins` (IC-14) |

## File Structure

### Neue Dateien

- Create: `scripts/lib/runtime_gate.py` — Gate-Seam: `RUNTIME_GATE_TIERS` (Phase 0); Phase 1 erweitert um Plugin-Generator (IC-08).
- Create: `tests/test_runtime_gate_config.py` — Resolver-Präzedenz, Fail-safe, Flag/Tier-Konsistenz, `runtime_gate_vars`-Bundle.
- Create: `tests/test_opencode_runtime_gate.py` — A2-Mapping-Deny, Skalar-Toleranz, Namespaced State, Ownership/Rollback, Idempotenz, Isolation-Koexistenz.
- Create: `tests/test_runtime_gate_wiring.py` — Seam-Injektion (Context/Rules), A2-Dispatch, Single-Provider-Fall, Advisory-No-op, Builtin-Vars.
- Create: `tests/test_runtime_gate_rendering.py` — gestufte Rules-Ausgabe + Byte-Identität der Hook-Variante.
- Create: `tests/test_runtime_gate_schema.py` — Schemafälle `orchestrator.require-runtime-gate`.
- Create: `tests/test_runtime_gate_docs.py` — Präsenz/Wortlaut der Tier-Doku.
- Create (Phase 1, DEFERRED): `templates/plugins/runtime-gate.opencode-plugin.js.tmpl`, `tests/test_runtime_gate_plugins.py`, `tests/scenarios/configs/63-opencode-runtime-gate.project.yaml`, `tests/scenarios/asserts/63-opencode-runtime-gate.sh`.

### Geänderte Dateien

- Modify: `scripts/lib/providers.py` — Tier-Resolver, `runtime_gate_vars`, `SUPPORTED_PLUGIN_PROTOCOLS`.
- Modify: `config/provider-capabilities.yaml` — `runtime_gate` je Provider (inkl. Kopf-Kommentar zur Pflicht).
- Modify: `scripts/lib/isolation.py` — Namespaced State, `_permission_mapping`, A2-Helper, Dispatch-Einstiegspunkt.
- Modify: `scripts/lib/sync_pipeline.py` — IC-04-Injektion an beiden Seams, IC-13-Dispatch.
- Modify: `scripts/lib/cli_commands.py` — Test-Repo-Sync-Pfad spiegelt den Dispatch.
- Modify: `scripts/lib/variables.py` — GATE_*-Conditionals.
- Modify: `scripts/lib/consistency/placeholders.py` — `_BUILTIN_VARS`.
- Modify: `rules/1-generic/use-orchestrator.md` — drei Tier-Blöcke.
- Modify: `rules/1-generic/a2a-delegation-gates.md` — Tier-Hinweis.
- Modify: `scripts/lib/consistency/orchestrator_strict.py` — tier-basiertes Finding + `agent_meta_root`.
- Modify: `scripts/consistency-check.py` — `agent_meta_root` an den Check übergeben.
- Modify: `config/project-config.schema.json` — `orchestrator.require-runtime-gate` (Phase 0) und `runtime-gate.plugin-mode` (Phase 1).
- Modify: `tests/test_provider_agnostic_dispatch.py` — `_TOUCHED_MODULES` + AC-01-Paramtest.
- Modify: `tests/test_config_variable_fallbacks.py` — Conditional-Stripping.
- Modify: `tests/test_orchestrator_strict_visibility.py` — Opencode-Erwartungen auf `permission` (INFO) umgestellt.
- Modify: `docs/process-capability-gaps.md` — OpenCode-Gate-Status ehrlich nachführen.
- Modify (Phase 1, DEFERRED): `config/ai-providers.yaml`, `scripts/lib/generated_file_drift.py`, `tests/test_generated_file_drift.py`, `tests/scenarios/registry.md`.

### Step-Agent-Map (plan-driven `implement`)

| Step | Task | Agent | Phase |
|------|------|-------|-------|
| 1 | Gate-Seam + Tier-Resolver + Capability-Flags | senior-developer | 0 |
| 2 | A2 Root-Deny + Namespaced Managed State | senior-developer | 0 |
| 3 | Sync-Seam-Verdrahtung + A2-Dispatch + Conditional/Placeholder | senior-developer | 0 |
| 4 | Gestufte Rules-Ausgabe (`GATE_ENFORCED` verbatim) | developer | 0 |
| 5 | A4 Consistency-Severity + Schema-Key | developer | 0 |
| 6 | Doku der Tier-Semantik | documenter | 0 |
| 7 | Vollständiges Phase-0-Verifikations-Gate | developer | 0 |
| 8 | Plugin-Generator (`observe`) + Drift + Schema — DEFERRED | developer | 1 |
| 9 | P6 Real-Repo-Verifikation + Tier-Flip — DEFERRED | developer | 1 |

---

### Task 1: Gate-Seam `runtime_gate` + Tier-Resolver + Capability-Flags

**Files:**
- Create: `scripts/lib/runtime_gate.py`
- Modify: `scripts/lib/providers.py`
- Modify: `config/provider-capabilities.yaml`
- Modify: `tests/test_provider_agnostic_dispatch.py`
- Test: `tests/test_runtime_gate_config.py`

**Interfaces:** (Produces / Consumes)
- Produces: `runtime_gate.RUNTIME_GATE_TIERS`; `providers.SUPPORTED_PLUGIN_PROTOCOLS`; `providers.provider_runtime_gate_supported`; `providers.provider_runtime_gate_tier`; `providers.runtime_gate_vars`; `provider-capabilities.yaml:capabilities.<provider>.runtime_gate`.
- Consumes: `providers.provider_hooks_supported` (bestehend), `providers.load_provider_capabilities` (bestehend), Stdlib `typing.Optional`/`Dict`/`Tuple`.

**Agent:** senior-developer
**Depends on:** —

**Steps:**
- [x] Step 1: Test schreiben (fail) — `tests/test_provider_agnostic_dispatch.py` um `test_every_provider_has_explicit_runtime_gate_capability` (AC-01, parametrisiert über `_registered_providers()`, Wert muss in `RUNTIME_GATE_TIERS` liegen) ergänzen und `"runtime_gate"` + `"isolation"` in `_TOUCHED_MODULES` (AC-04) aufnehmen. `tests/test_runtime_gate_config.py` neu mit `::test_declared_tier_matches_machine_flags` (AC-02: `hook` iff `provider_hooks_supported`; `plugin` iff supported **and not** hooks), `::test_resolver_precedence` (AC-03: hook/plugin/permission/advisory), `::test_resolver_failsafe_never_raises` (AC-03: `provider_runtime_gate_tier(None)` und `({}, None)` → `advisory`), `::test_plugin_tier_unreachable_without_has_plugins` (AC-22), `::test_runtime_gate_vars_bundle_is_strings` (IC-03/IC-04).
- [x] Step 2: Implementieren — `scripts/lib/runtime_gate.py` mit `from __future__ import annotations`, Modul-Docstring (Seam-Abgrenzung: Tier-Vokabel hier, Resolver in `providers.py` per IC-03) und `RUNTIME_GATE_TIERS`. In `providers.py` `SUPPORTED_PLUGIN_PROTOCOLS`, `provider_runtime_gate_supported` (Spiegel von `provider_hooks_supported`, `providers.py:308-317`), `provider_runtime_gate_tier` exakt mit der IC-03-Präzedenz und fail-safer Behandlung von `None`/Nicht-Mapping, `runtime_gate_vars` mit den fünf String-Keys (`ENFORCEMENT_TIER`; `GATE_ENFORCED` `'true'` iff Tier in `(hook, plugin)`; `GATE_PARTIAL` iff `permission`; `GATE_ADVISORY` iff `advisory`; `RUNTIME_GATE_PLUGIN_MODE` aus `config.get("runtime-gate", {}).get("plugin-mode", "observe")`, validiert gegen `{"observe","enforce"}`, fail-safe `observe`). `config/provider-capabilities.yaml`: je Providerblock explizit `runtime_gate` (`hook` für Claude, Gemini/Antigravity; `permission` für Opencode; `advisory` sonst) plus Kopf-Kommentar zur Pflicht (analog `commands`).
- [x] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_runtime_gate_config.py tests/test_provider_agnostic_dispatch.py -q` → rc 0; `rtk python3 scripts/sync.py --validate` → rc 0.
- [x] Step 4: Commit — `feat: add provider-agnostic runtime-gate tier resolver`.

**Acceptance:** AC-01, AC-02, AC-03, AC-04, AC-22.

---

### Task 2: A2 Root-Deny + Namespaced Managed State

**Files:**
- Modify: `scripts/lib/isolation.py`
- Test: `tests/test_opencode_runtime_gate.py`

**Interfaces:** (Produces / Consumes)
- Produces: `_STATE_RUNTIME_GATE_KEY`; `_read_state(state_path, key=_STATE_ISOLATION_KEY)`; `_write_state(state_path, value, dry_run, key=_STATE_ISOLATION_KEY)` (Read-Modify-Write); `_permission_mapping`; `_opencode_runtime_gate_entries`; `_sync_opencode_runtime_gate`; skalar-toleranter `_sync_opencode_isolation`.
- Consumes: `isolation._read_json_safe`/`write_checked`/`safe_path` (bestehend), `providers.provider_runtime_gate_tier` + `providers.load_provider_capabilities` (Task 1), `orchestrator_strict._resolve_effective_strict`-Präzedenz (bestehend).

**Agent:** senior-developer
**Depends on:** 1

**Steps:**
- [x] Step 1: Test schreiben (fail) — `tests/test_opencode_runtime_gate.py` neu mit `::test_read_write_state_preserves_sibling_namespaces` (AC-23: `isolation-deny`-Liste bleibt neben `runtime-gate-deny` erhalten), `::test_runtime_gate_entries_mapping_form_under_strict` (AC-10: `{'edit': {'**': 'deny'}, 'bash': {'**': 'deny'}}` nur bei Tier `permission`, sonst `{}`), `::test_scalar_permission_family_tolerated` (D-C4/AC-10: `permission.edit: "ask"` wird über `_permission_mapping` normalisiert, kein Raise), `::test_prior_user_value_recorded_and_restored` (AC-10/AC-11: User-Wert an `"**"` wird im Namespace gespeichert und bei non-strict exakt restauriert), `::test_second_strict_sync_is_idempotent_and_byte_identical` (AC-11), `::test_isolation_and_runtime_gate_coexist` (AC-23: beide Glob-Familien und beide Namespaces überleben beide Writer).
- [x] Step 2: Implementieren — `isolation.py`: `_read_state`/`_write_state` auf namespaced Keys generalisieren (Default-Key `isolation-deny`, Signaturen abwärtskompatibel für bestehende Positionsaufrufer); `_write_state` liest das bestehende JSON, ersetzt **nur** `key` und schreibt alle Sibling-Namespaces unverändert zurück. `_permission_mapping` implementieren. `_opencode_runtime_gate_entries` liefert Mapping-Deny nur, wenn `provider_runtime_gate_tier(pc, caps) == "permission"` **und** Strict effektiv aktiv ist (`_resolve_effective_strict`-Präzedenz), sonst `{}`. `_sync_opencode_runtime_gate` merged über `_read_json_safe`/`write_checked`, setzt `"**"` in `permission.edit`/`permission.bash`, zeichnet den vorherigen Wert auf, entfernt bei non-strict nur den managed `"deny"` und restauriert den Prior-Wert. `_sync_opencode_isolation` auf `_permission_mapping(permission.get("read"))`/`edit` umstellen. Kein Provider-Literal, kein Schreiben von Skalaren, `dry_run` schreibt nie, unparsebare JSON → Warnung + Skip.
- [x] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_opencode_runtime_gate.py -q` → rc 0; `rtk python3 scripts/sync.py --validate` → rc 0.
- [x] Step 4: Commit — `feat: merge opencode runtime-gate deny via isolation state`.

**Acceptance:** AC-10, AC-11, AC-23.

---

### Task 3: Sync-Seam-Verdrahtung (IC-04) + A2-Dispatch (IC-13) + Conditional/Placeholder-Registrierung

**Files:**
- Modify: `scripts/lib/sync_pipeline.py`
- Modify: `scripts/lib/cli_commands.py`
- Modify: `scripts/lib/variables.py`
- Modify: `scripts/lib/consistency/placeholders.py`
- Test: `tests/test_runtime_gate_wiring.py`
- Test: `tests/test_config_variable_fallbacks.py`

**Interfaces:** (Produces / Consumes)
- Produces: Tier-Var-Injektion in `provider_variables` an beiden Seams; A2-Dispatch bei Tier `permission` (auch für Single-Provider-Projekte); Test-Repo-Spiegelung in `cli_commands.py`; `GATE_*` in `conditional_vars`; fünf neue `_BUILTIN_VARS`.
- Consumes: `providers.runtime_gate_vars`/`provider_runtime_gate_tier` (Task 1), `isolation._sync_opencode_runtime_gate` (Task 2), bestehende `rules.py::_merged_rule_vars`/`context.py::_build_managed_block` (unveränderte Propagationspunkte).

**Agent:** senior-developer
**Depends on:** 1, 2

**Steps:**
- [x] Step 1: Test schreiben (fail) — `tests/test_runtime_gate_wiring.py` neu mit `::test_tier_vars_reach_context_render` und `::test_tier_vars_reach_rule_render` (IC-04/F-02: Spy auf `sync_context_for_provider` bzw. `sync_rules` sieht die `GATE_*`-Keys), `::test_strict_sync_writes_mapping_deny` (AC-08), `::test_single_provider_strict_writes_deny` (AC-09: `len(providers) == 1`, Dispatch nicht durch die ≥2-Guard blockiert), `::test_advisory_sync_writes_no_deny_and_no_plugin` (AC-22), `::test_gate_vars_registered_in_builtin_vars` (AC-07). `tests/test_config_variable_fallbacks.py` um `::test_gate_conditional_blocks_stripped` (AC-06) ergänzen.
- [x] Step 2: Implementieren — In `_sync_stage_contexts` nach dem `provider_variables`-Aufbau und **vor** `sync_context_for_provider` `caps = load_provider_capabilities(agent_meta_root).get(provider, {})` laden und `provider_variables.update(runtime_gate_vars(pc, caps, config))` mergen; identisch in `_sync_stage_per_provider` **vor** `sync_rules`/`sync_embedded_rule_files`. Denselben Scope für den A2-Dispatch nutzen: `if provider_runtime_gate_tier(pc, caps) == "permission": _sync_opencode_runtime_gate(...)` — nicht unter `has_hooks`, nicht in `sync_provider_isolation`, kein Provider-Literal. `cli_commands.py`-Test-Repo-Syncpfad analog spiegeln. `variables.py` `GATE_ENFORCED`/`GATE_PARTIAL`/`GATE_ADVISORY` in `conditional_vars`; `placeholders.py::_BUILTIN_VARS` um die fünf Variablen erweitern.
- [x] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_runtime_gate_wiring.py tests/test_config_variable_fallbacks.py tests/test_rule_variables.py -q` → rc 0; `rtk python3 scripts/consistency-check.py` → rc 0.
- [x] Step 4: Commit — `feat: inject runtime-gate vars and dispatch opencode deny`.

**Acceptance:** AC-06, AC-07, AC-08, AC-09, AC-22.

---

### Task 4: Gestufte Rules-Ausgabe (`GATE_ENFORCED` verbatim)

**Files:**
- Modify: `rules/1-generic/use-orchestrator.md`
- Modify: `rules/1-generic/a2a-delegation-gates.md`
- Test: `tests/test_runtime_gate_rendering.py`

**Interfaces:** (Produces / Consumes)
- Produces: drei mutually-exclusive Tier-Blöcke in `use-orchestrator.md` innerhalb `{{#if ORCH_MODE_STRICT}}`; Tier-Hinweis mit `{{ENFORCEMENT_TIER}}` in `a2a-delegation-gates.md`.
- Consumes: `GATE_ENFORCED`/`GATE_PARTIAL`/`GATE_ADVISORY`/`ENFORCEMENT_TIER` aus Task 3; `strip_inactive_conditional_blocks` (Task 3).

**Agent:** developer
**Depends on:** 3

**Steps:**
- [x] Step 1: Test schreiben (fail) — `tests/test_runtime_gate_rendering.py` neu mit `::test_hook_tier_renders_enforced_verbatim` (AC-05/AC-15: Block byte-identisch zu `# CRITICAL GATE` + `MAIN CHAT darf nicht selbst editieren. ALLES -> \`orchestrator\`. Keine Ausnahmen.`), `::test_permission_tier_renders_partial` (AC-05: PARTIAL-Variante, enthält **nicht** die unbedingte Runtime-Zusage), `::test_advisory_tier_renders_advisory` (AC-05), `::test_only_one_gate_block_survives` (AC-06).
- [x] Step 2: Implementieren — `use-orchestrator.md`: den bestehenden unbedingten Strict-Block (`:1-4`) durch die drei `GATE_*`-Blöcke exakt nach IC-07 ersetzen; die `GATE_ENFORCED`-Variante reproduziert den heutigen Wortlaut verbatim. `a2a-delegation-gates.md`: tier-gestuften Hinweis mit `{{ENFORCEMENT_TIER}}` und Verweis auf `## Bekannte Grenzen` ergänzen. Kein Provider-Literal, keine Rollen-Routen.
- [x] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_runtime_gate_rendering.py tests/test_rule_variables.py tests/test_no_role_routes_in_templates.py -q` → rc 0.
- [x] Step 4: Commit — `feat: render tiered CRITICAL GATE wording`.

**Acceptance:** AC-05, AC-15.

---

### Task 5: A4 Consistency-Severity + Schema-Key `orchestrator.require-runtime-gate`

**Files:**
- Modify: `scripts/lib/consistency/orchestrator_strict.py`
- Modify: `scripts/consistency-check.py`
- Modify: `config/project-config.schema.json`
- Modify: `tests/test_orchestrator_strict_visibility.py`
- Test: `tests/test_runtime_gate_schema.py`

**Interfaces:** (Produces / Consumes)
- Produces: `check_orchestrator_strict_hook_support(project_root, config, provider_config, agent_meta_root)` mit tier-basierten Findings (INFO/WARNING/ERROR); Schema-Sibling `orchestrator.require-runtime-gate` (bool, Default `false`).
- Consumes: `providers.provider_runtime_gate_tier` + `load_provider_capabilities` (Task 1); bestehende effektive-Strict-Auflösung und Check-ID.

**Agent:** developer
**Depends on:** 1

**Steps:**
- [x] Step 1: Test schreiben (fail) — `tests/test_orchestrator_strict_visibility.py` um `::test_permission_tier_yields_info`, `::test_advisory_tier_warning_by_default_error_with_optin`, `::test_hook_tier_yields_no_finding` ergänzen und die sechs bestehenden Opencode-Fälle (AC-13: `test_warns_for_active_provider_without_hook_support`, `test_provider_override_turns_strict_on_despite_global_off`, `test_global_mode_key_triggers_warning_without_legacy_booleans`, `test_malformed_provider_overrides_null_does_not_crash`, `test_malformed_provider_override_null_entry_does_not_crash`, `test_gemini_and_opencode_active_warning_only_for_opencode`) auf INFO für Opencode aktualisieren. `tests/test_runtime_gate_schema.py` neu mit `::test_require_runtime_gate_boolean_accepted`, `::test_require_runtime_gate_non_boolean_rejected`, `::test_require_runtime_gate_absent_defaults_false` (AC-14, `pytest.importorskip("jsonschema")`).
- [x] Step 2: Implementieren — `check_orchestrator_strict_hook_support` von `provider_hooks_supported` auf `provider_runtime_gate_tier(pc, caps)` umstellen: `advisory`+strict → WARNING, bei `orchestrator.require-runtime-gate` `true` → ERROR; `permission` → INFO „partially enforced; delegation provenance not enforced"; `hook`/`plugin` → kein Finding. `agent_meta_root` als expliziten Parameter ergänzen, Registry via `load_provider_capabilities` laden, unlesbare Registry → `advisory` (fail-safe). `scripts/consistency-check.py` den bereits bekannten `agent_meta_root` übergeben. Schema: `require-runtime-gate` als Sibling im `orchestrator`-Block (`additionalProperties`-Politik unverändert).
- [x] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_orchestrator_strict_visibility.py tests/test_runtime_gate_schema.py tests/test_repo_containment_consistency.py -q` → rc 0; `rtk python3 scripts/consistency-check.py` → rc 0.
- [x] Step 4: Commit — `feat: derive orchestrator-strict severity from gate tier`.

**Acceptance:** AC-12, AC-13, AC-14.

---

### Task 6: Doku der Tier-Semantik

**Files:**
- Modify: `docs/process-capability-gaps.md`
- Create: `docs/concepts/runtime-gate-tiers.md`
- Test: `tests/test_runtime_gate_docs.py`

**Interfaces:** (Produces / Consumes)
- Produces: Konzeptdokument mit den vier Tiers und der PARTIAL-Grenze; aktualisierter Gap-Status in `docs/process-capability-gaps.md`.
- Consumes: die ausgelieferten Rules-Blocktexte (Task 4), das tier-basierte Consistency-Verhalten (Task 5).

**Agent:** documenter
**Depends on:** 3, 4, 5

**Steps:**
- [x] Step 1: Test schreiben (fail) — `tests/test_runtime_gate_docs.py` neu mit `::test_tier_concept_doc_lists_four_tiers` (`hook`, `plugin`, `permission`, `advisory` je benannt) und `::test_tier_concept_doc_states_partial_not_fully_enforced` (kein „fully enforced" für `permission`), `::test_capability_gaps_doc_reflects_opencode_status`.
- [x] Step 2: Implementieren — `docs/concepts/runtime-gate-tiers.md` als knappe interne Doku (Tier-Definitionen, Resolver-Präzedenz, PARTIAL-Grenze, Phase-1-`observe`-Vorbehalt/P6, #747-Avoidance). `docs/process-capability-gaps.md` um den tatsächlichen OpenCode-Status (`permission`, PARTIAL, Phase 1 offen) nachführen. Keine Provider-Logik, keine Rollen-Routen, keine Modellnamen.
- [x] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_runtime_gate_docs.py -q` → rc 0.
- [x] Step 4: Commit — `docs: document runtime-gate tiers and opencode partial guarantee`.

**Acceptance:** AC-15.

---

### Task 7: Vollständiges Phase-0-Verifikations-Gate

**Files:**
- Test: `tests/test_runtime_gate_config.py`, `tests/test_opencode_runtime_gate.py`, `tests/test_runtime_gate_wiring.py`, `tests/test_runtime_gate_rendering.py`, `tests/test_runtime_gate_schema.py`, `tests/test_runtime_gate_docs.py`

**Interfaces:** (Produces / Consumes)
- Produces: dokumentiertes, reproduzierbares Phase-0-Abnahme-Ergebnis; kein Produktionscode, keine neuen Dateien.
- Consumes: alle Artefakte aus Task 1 bis Task 6.

**Agent:** developer
**Depends on:** 1, 2, 3, 4, 5, 6

**Steps:**
- [ ] Step 1: Alle neuen Unit-Tests grün — `rtk python3 -m pytest tests/test_runtime_gate_config.py tests/test_opencode_runtime_gate.py tests/test_runtime_gate_wiring.py tests/test_runtime_gate_rendering.py tests/test_runtime_gate_schema.py tests/test_runtime_gate_docs.py -q` → rc 0.
- [ ] Step 2: Repo-Gate — `rtk python3 scripts/sync.py --validate` → rc 0 und `rtk python3 scripts/sync.py --check` → rc 0 (Rules-Churn/Hashes bewusst aktualisiert).
- [ ] Step 3: Konsistenz inkl. Py3.9/Provider-Agnostik — `rtk python3 scripts/consistency-check.py` → rc 0.
- [ ] Step 4: Bestands-Suiten unverändert grün — `rtk python3 -m pytest tests/test_provider_agnostic_dispatch.py tests/test_orchestrator_strict_visibility.py tests/test_provider_hooks_config.py tests/test_no_role_routes_in_templates.py tests/test_provider_three_file_invariant.py -q` → rc 0.
- [ ] Step 5: Szenario-Harness vollständig — `rtk tests/scenarios/run.sh` → alle Szenarien `PASS` (insbesondere `57`, `59`, `60`, `61`; Szenario `63` ist Phase 1/DEFERRED und in Phase 0 nicht aktiv).
- [ ] Step 6: Plan-Validierung (Ausgabe dokumentieren, **kein Pass-Gate**) — `rtk python3 scripts/sync.py --validate-spec-plan` für diesen Plan ausführen und die Ausgabe festhalten; erwarteter rc ggf. **1** wegen der bekannten `validate_plan`-`file_overlap`-Limitierung (ohne `kind`-Gate über sequenzielle `Depends on:`-Kanten), dokumentiert in `docs/plans/2026-09-13-progress-paths-config.md` (Abschnitt Self-Review).
- [ ] Step 7: Commit — `test: verify opencode runtime-gate phase 0 end to end`.

**Acceptance:** AC-01 bis AC-15, AC-23 (Phase-0-Abnahme).

---

### Task 8: Plugin-Generator (`observe`) + Drift + Schema — DEFERRED (Phase 1, capability-gated)

> **NICHT Teil der Phase-0-Abnahme.** Erst nach gemergter Phase 0 und **vor** jeder Tier-Flip-Freigabe. Artefakt bleibt `MODE=observe`; kein „fully enforced". `runtime_gate: plugin`, `has_plugins: true`, `MODE=enforce` und AC-21 hängen an Task 9 (P6).

**Files:**
- Modify: `scripts/lib/runtime_gate.py` (Erweiterung des Phase-0-Seams um IC-08)
- Modify: `config/ai-providers.yaml`
- Modify: `scripts/lib/generated_file_drift.py`
- Modify: `config/project-config.schema.json` (sequenziell nach Task 5)
- Create: `templates/plugins/runtime-gate.opencode-plugin.js.tmpl`
- Test: `tests/test_runtime_gate_plugins.py`
- Test: `tests/test_generated_file_drift.py`

**Interfaces:** (Produces / Consumes)
- Produces: `PLUGIN_TEMPLATE_BY_PROTOCOL`, `PLUGIN_STEM`, `runtime_gate_plugin_relpath`, `sync_runtime_gate_plugins`; IC-02-Keys; `runtime-gate.plugin-mode`-Schema; `plugin_dir`-`dir_spec`.
- Consumes: `providers.provider_runtime_gate_supported` (Task 1); Managed-Index-Muster `hook_plugins.sync_release_gates` (`scripts/lib/hook_plugins.py:28-98`).

**Agent:** developer
**Depends on:** 1, 2, 3, 4, 5, 6, 7

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_runtime_gate_plugins.py` neu mit `::test_plugin_written_when_supported` (AC-16), `::test_plugin_rollback_when_has_plugins_false` (AC-17), `::test_unknown_protocol_or_missing_template_warns_without_write` (AC-18), `::test_plugin_mode_observe_by_default` (AC-19). `tests/test_generated_file_drift.py` um den `plugin_dir`-Fall ergänzen (AC-20). In `tests/test_runtime_gate_plugins.py` zusätzlich `::test_runtime_gate_plugin_mode_schema` (AC-24, `pytest.importorskip("jsonschema")`).
- [ ] Step 2: Implementieren — `runtime_gate.py` um die IC-08-Symbole erweitern (provider-agnostisch, Template-Zuordnung über `plugin_protocol`, `always-copy`/managed-index/never-touch-project-owned-Semantik wie `hook_plugins.sync_release_gates`); `ai-providers.yaml`-Opencode-Block um IC-02-Keys; `generated_file_drift.py` `plugin_dir`-`dir_specs` gated auf `has_plugins`; `project-config.schema.json` `runtime-gate`-Root-Objekt mit `plugin-mode` (`enum`, `additionalProperties: false`). `MODE=observe` bleibt Default; `enforce` bleibt gesperrt.
- [ ] Step 3: Test (pass) — `rtk python3 -m pytest tests/test_runtime_gate_plugins.py tests/test_generated_file_drift.py -q` → rc 0; `rtk python3 scripts/sync.py --validate` → rc 0.
- [ ] Step 4: Commit — `feat: add capability-gated runtime-gate plugin generator (observe)`.

**Acceptance (DEFERRED):** AC-16, AC-17, AC-18, AC-19, AC-20, AC-24.

---

### Task 9: P6 Real-Repo-Verifikation + Tier-Flip — DEFERRED (Phase 1, P6-gated)

> **NICHT Teil der Phase-0-Abnahme.** Manuelle/Real-Repo-Aufgabe, nicht unit-testbar (AC-21). Erst wenn P6 bestätigt, dass `tool.execute.before` in OpenCode-Subagent-Sessions feuert **und** der Main Chat in `input` unterscheidbar ist, darf ein Provider auf `runtime_gate: plugin` + `has_plugins: true` + `MODE=enforce` umgestellt werden. Bis dahin bleibt alles `observe`/`permission`.

**Files:**
- Create: `tests/scenarios/configs/63-opencode-runtime-gate.project.yaml`
- Create: `tests/scenarios/asserts/63-opencode-runtime-gate.sh`
- Modify: `tests/scenarios/registry.md`

**Interfaces:** (Produces / Consumes)
- Produces: dokumentierter P6-Nachweis; Szenario `63-opencode-runtime-gate` (ID `62` ist inzwischen durch `62-stale-role-cleanup` belegt; `63` ist die nächste freie ID) samt Config + Assert-Script + Registry-Zeile.
- Consumes: Task 8 (Plugin-Artefakt, `observe`), Task 1 (Tier-Resolver), `tests/scenarios/run.sh`-Vertrag.

**Agent:** developer
**Depends on:** 8

**Steps:**
- [ ] Step 1: Real-Repo-Nachweis führen — P6 beantwortet AN-3/AN-4/AN-5 (Subagent-Feuern, Main-Chat-Unterscheidbarkeit, Permission-Präzedenz AN-6/OQ-3); Ergebnis festhalten; bei negativem AN-6 den Fine-Glob-Fallback anwenden (Global Constraints) statt eines gröberen Blocks.
- [ ] Step 2: Szenario anlegen — `tests/scenarios/configs/63-opencode-runtime-gate.project.yaml`, `tests/scenarios/asserts/63-opencode-runtime-gate.sh` (ausführbar), Registry-Zeile `| \`63-opencode-runtime-gate\` | … |`; auf `dry_rc=0 && sync_rc=0 && val_rc=0 && assert_rc=0` auslegen.
- [ ] Step 3: Test (pass) — `rtk tests/scenarios/run.sh 63` → `PASS` (rc 0); danach `rtk tests/scenarios/run.sh` vollständig → alle `PASS`.
- [ ] Step 4: Commit — `test: add scenario 63 for opencode runtime-gate promotion`.

**Acceptance (DEFERRED, P6-gated):** AC-21.

---

## Acceptance-Criteria → Task-Mapping

Phase 0 (implementierbar jetzt; Abnahme-Gate = Task 7):

| AC | Task(s) |
|----|---------|
| AC-01 | 1 |
| AC-02 | 1 |
| AC-03 | 1 |
| AC-04 | 1 |
| AC-05 | 4 |
| AC-06 | 3, 4 |
| AC-07 | 3 |
| AC-08 | 3 |
| AC-09 | 3 |
| AC-10 | 2 |
| AC-11 | 2 |
| AC-12 | 5 |
| AC-13 | 5 |
| AC-14 | 5 |
| AC-15 | 4, 6, 7 |
| AC-22 (no-plugin-Seite) | 1, 3 |
| AC-23 | 2 |

Phase 1 / DEFERRED (nicht Teil der Phase-0-Abnahme):

| AC | Task(s) | Gate |
|----|---------|------|
| AC-16 | 8 | capability: `has_plugins`+`plugin_protocol` |
| AC-17 | 8 | capability |
| AC-18 | 8 | capability |
| AC-19 | 8 | `MODE=observe` default |
| AC-20 | 8 | capability |
| AC-22 (plugin-Seite) | 8 | capability |
| AC-24 | 8 | observe only |
| AC-21 | 9 | P6 (Real-Repo, #765) — Tier-Flip/`enforce` |

## Rollback / Safety-Net

- **Flag-scoped by construction:** Ohne `runtime_gate: permission` (Default `advisory`) schreibt A2 nichts; ohne effektiv aktives `strict` ebenfalls nichts. Ein Projekt kann per `orchestrator.provider-overrides.<p>.mode` A2 jederzeit verengen oder abschalten.
- **A2 reversibel:** Managed State (`runtime-gate-deny`) speichert den Prior-Wert am Glob `"**"`; ein non-strict-Sync entfernt nur den managed `"deny"` und restauriert den User-Wert exakt. Kein User-Wert geht verloren (AC-10/AC-11).
- **Idempotent:** Read-Modify-Write auf `opencode.json` und dem State; zwei strikte Syncs sind byte-identisch (AC-11/AC-23). `_write_state` erhält Sibling-Namespaces.
- **#747-sicher:** Kein neuer Root-Key, kein create-only-Write; bestehende `opencode.json` wird in-place gemerged, unparsebare Datei → Warnung + Skip (kein Datenverlust).
- **Hook-Provider unverändert:** `GATE_ENFORCED` reproduziert den heutigen Wortlaut byte-identisch; Claude/Gemini-Ausgabe und Hook-Contract (`hooks.py`, `orchestrator-guard.sh`) werden nicht angefasst.
- **Phase 1 entfernen statt brechen:** Plugin-Artefakt ist managed und drift-getrackt; `has_plugins: false` entfernt nur die managed Datei, project-owned Dateien bleiben unberührt.
- **Revert-Pfad:** Alle Änderungen sind committet Task-für-Task und ohne Schema-Bump rückwärtskompatibel; ein Revert je Task-Readme bleibt möglich, ohne die Ratchets (`test_provider_hooks_config.py`, `test_no_role_routes_in_templates.py`) zu brechen.

## Self-Review

- **AC-Abdeckung:** Phase 0 deckt AC-01 … AC-15, AC-22 (no-plugin-Seite) und AC-23 über Task 1–7 ab; AC-16 … AC-21 und AC-24 sind explizit als DEFERRED (Task 8/9) markiert und **nicht** Teil der Phase-0-Abnahme. Kein Phase-0-AC hängt an einer P6-gated Aufgabe.
- **Test je Task:** Jede Task besitzt konkrete, benannte Testfälle und ein `rtk`-präfixiertes Verifikationskommando mit erwartetem rc; kein Task ist ohne beobachtbaren Test „done". Task 7 fährt zusätzlich das Repo-Gate `rtk python3 scripts/sync.py --validate`.
- **Traceability:** `spec-id: SPEC-OPENCODE-RUNTIME-GATE-2026-09-13` ↔ `**Spec:**`-Pfad ↔ Task-ID ↔ Testname ist durchgängig; `pipeline_stages.implement` zeigt auf Step 1 (Task 1, Agent `senior-developer`).
- **Interface-Vollständigkeit:** Jede Task hat nicht-leere `Produces`/`Consumes`; alle neuen Symbole sind mit Datei, Name und Signatur benannt; die Zwei-Registry-Signatur (D-C1) und der Seam-Zuschnitt (`runtime_gate.py` Vokabel vs. `providers.py` Resolver) sind explizit.
- **Abhängigkeiten:** Der Graph ist zyklenfrei und vorwärtsgerichtet: 1 → 2 → 3; 4 nach 3; 5 nach 1; 6 nach 3/4/5; 7 schließt Phase 0 ab; 8 nach 7; 9 nach 8. `config/project-config.schema.json` wird in Task 5 (Phase 0) und Task 8 (DEFERRED, sequenziell danach) berührt — kein paralleler Schreibzugriff; `scripts/lib/runtime_gate.py` wird in Task 1 angelegt und in Task 8 sequenziell erweitert.
- **Datei-Ownership:** Innerhalb Phase 0 wird jede Datei in genau einer Task geändert; Testdateien sind den jeweiligen Tasks zugeordnet. Der Plan-Graph-Validator (`spec_plan_plan_graph`) kann die bekannten `file_overlap`-False-Positives über sequenzielle `Depends on:`-Kanten melden (Validator-Limitierung ohne `kind`-Gate) — dokumentiert, keine Ownership-Verletzung.
- **Rahmenbedingungen:** Provider-agnostisch (kein Provider-Literal, `runtime_gate`/`isolation` in `_TOUCHED_MODULES`), Stdlib-only, Py3.9-konform, Rules-Churn bewusst behandelt, keine neuen Rollen/keine SE-Kaskade, keine Modellnamen.
- **No-Placeholder:** Kein `TODO`, kein `TBD`, kein `...`, kein `<Platzhalter>`, keine leeren `Interfaces:`; exakte Pfade, Symbole, Signaturen, Testnamen und Commit-Messages.

## Ausführungs-Handoff

- **Reihenfolge:** Task 1 → Task 7 in aufsteigender Numerik. Phase 0 endet mit Task 7; Task 8/9 bleiben gesperrt (DEFERRED) und werden nur auf ausdrückliche Entscheidung nach gemergter Phase 0 begonnen.
- **Task-für-Task (SDD):** Jede Task von einem frischen Subagenten mit frischem Kontext, Review der Requirements-Treue und Qualität, Ledger-Checkboxen nach Abschluss; kein Task ohne Test und Commit. Kein Worktree, keine Rollen-Routen.
- **Blocked-Regel:** Kann eine Task ihre Akzeptanz nicht belegen, bleibt sie offen (`- [ ]`) und blockiert Nachfolger; nie stillschweigend überspringen oder umsortieren.
- **Phase-1-Sperre:** Task 8/9 dürfen ohne bestandenen P6 (Real-Repo, #765) keine Tier-Flip-/`enforce`-Änderung committen; das Plugin bleibt `observe`, die Zusage bleibt `permission` (PARTIAL).
- **Abschluss-Gate Phase 0:** `rtk python3 -m pytest <sechs neue Testmodule> -q`, `rtk python3 scripts/sync.py --validate` (rc 0), `rtk python3 scripts/sync.py --check` (rc 0), `rtk python3 scripts/consistency-check.py` (rc 0), `rtk tests/scenarios/run.sh` (alle `PASS`) sowie die genannten Ratchet-Suiten (rc 0).
