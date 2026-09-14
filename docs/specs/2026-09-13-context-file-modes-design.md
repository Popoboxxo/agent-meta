---
spec-id: SPEC-CONTEXT-FILE-MODES-2026-09-13
title: Context-File Modes (unified / per-provider) — Technical Specification
status: Entwurf
related-spec: SPEC-OPENCODE-RUNTIME-GATE-2026-09-13
source-design: docs/specs/2026-09-13-context-file-modes-system-design.md
related-issue: "#794"
---

# Context-File Modes (unified / per-provider) — Spec

> Status: **Entwurf** — this document is a specification only. It defines interface
> contracts and acceptance criteria; it contains no implementation and no plan.
> The final approval marker `Status: APPROVED` is set by `concept-reviewer` after
> review — never by this document.
> Trace anchor (adopted unchanged from the system design):
> `spec-id: SPEC-CONTEXT-FILE-MODES-2026-09-13`.
> Source design: `docs/specs/2026-09-13-context-file-modes-system-design.md`
> (same `spec-id`; the design adopts the anchor and passes it to this spec
> unchanged).
> Related spec: `SPEC-OPENCODE-RUNTIME-GATE-2026-09-13`
> (`docs/specs/2026-09-13-opencode-runtime-gate-design.md`) — this feature extends
> it and fixes the `AGENTS.md` double-write / `sync.py --check` rc1 defect
> described there (§1.1 of the system design). It does **not** supersede its tier
> vocabulary or its Phase-0 contracts; it adds one invariant on top of them (the
> shared-context-file render). Nothing that spec approved is withdrawn.
>
> Provider-agnostic is mandatory: all provider differences are expressed through
> config keys / capability flags in `config/ai-providers.yaml` and
> `config/provider-capabilities.yaml`. No `if provider == "..."` branch, no
> provider-name literal equality in any new or changed module.

### Source of the interface contracts

The interface contracts in this spec are the spec-level restatement of the
design's IC-01 … IC-10 (design §4.2, §5.3, §7.2). Where the naming differs, the
mapping is: spec IC-01 = design IC-01, spec IC-02 = design IC-02, spec IC-03 =
design IC-03, spec IC-04 = design IC-04, spec IC-05…IC-13 = design IC-05…IC-10
(detail) plus the config/schema/UI surfaces named in design §6/§7. Symbols and
line numbers below were re-verified against the repository at the revision this
spec was authored; HYPOTHESIS markers follow the design's verification legend.
Where this spec tightens a design contract against the real code, it says so:
spec IC-08 is **narrowed** to the legacy-cleanup caller of
`resolve_context_filename` (F-02) and the render switch it was originally meant
to carry is named in spec IC-09. Revision rows record every review finding.

---

### Scope of the acceptance criteria

The system design phases the work; this spec inherits the phasing and marks
Phase-1/2 criteria as deferred from Phase 0, exactly as
`SPEC-OPENCODE-RUNTIME-GATE-2026-09-13` marks its plugin criteria.

- **Phase 0 — `unified` fix (implementable now, rc1 blocker).** One deterministic
  render per physical `context_file`; the effective tier of a shared file is the
  **weakest** tier over its **active** sharers
  (`advisory < permission < plugin < hook`). This is an additive invariant over
  the already-committed `GATE_*` vocabulary, introduces no unverified provider
  API, and is the criteria the implementation is signed off against first:
  **AC-01 … AC-09, AC-25**. The invariant is **scoped**: IC-03 neutralises the
  `GATE_*` family only (AC-25, R7, OQ-13).
- **Phase 1 — `per-provider` core (gated/deferred from Phase 0).** Canonical
  `AGENTS.md` core + provider-native adapters with their own tier, for the two
  **VERIFIED-RESEARCH** adapter providers (Claude `@AGENTS.md`, Gemini
  `@`/`context.fileName`). Config resolver, schema, adapter render and rollback:
  **AC-10 … AC-18, AC-26**. The adapter-loading semantics for these two providers are
  VERIFIED-RESEARCH; the remaining adapters are HYPOTHESIS and stay in Phase 2.
- **Phase 2 — remaining adapters + config/validation/UI (gated/deferred from
  Phase 0 and from Phase 1).** Codex, Copilot, Continue, Mammouth adapters behind
  capability flags after their HYPOTHESIS checks pass, consistency check,
  size-guard extension, Admin-UI/Server: **AC-19 … AC-24**. No Phase-2 provider
  may be switched to an adapter before its HYPOTHESIS (A5/§9.3 of the design) is
  verified in a real repo and recorded.

The design's OQ-1 … OQ-12 (design §12) are carried over in
[Offene Fragen + Risiken](#offene-fragen--risiken); each has a recommended
default and a flag for whether it needs explicit user approval. OQ-13 is added
by this revision (F-01, `[User approval]`) and R7 is added to the design's risk
list.

### Revision — incorporated review findings

| Finding | Change |
|---|---|
| Erstfassung | Base version. Interface contracts restated from the design's IC-01 … IC-10; acceptance criteria split Phase 0 / Phase 1 / Phase 2. Further rows are appended on `CHANGES_REQUESTED`, iteration by iteration (max 3). |
| F-01 (MAJOR) | Chose option (a): the determinism invariant is scoped to "the active sharers differ only in gate tier". IC-03 now names the three non-neutralised provider-scoped inputs (`context.py:1131`, `:1133-1136`, `:1141`); AC-07 scoped; Datenfluss §1 annotates them; new AC-25 asserts the scope; new R7 + OQ-13 (`[User approval]`) record the limitation. `sync.py --check` rc0 (AC-06) is unchanged. |
| F-02 (MAJOR) | Adapter filename switch retargeted: IC-08 restricted to `_sync_stage_legacy_cleanup` (`sync_pipeline.py:445/:455`, orphan protection) and explicitly declared not on the render path; the render switch moved into IC-09's dispatch (`sync_context_for_provider` → `_sync_opencode_context` `:566` / `_sync_managed_block_context` `:496`); AC-13 bound to the file actually written. |
| F-03 (MAJOR) | Phase-gating fixed: AC-06 reduced to the Phase-0 unit dry-run + committed-`AGENTS.md` `--check` rc0; the scenario-`63` assertion moved to AC-21 (Phase 2). AC-17 no longer depends on IC-13/AC-24; the size-guard counting stays in Phase 2 (AC-24). |
| F-04 (MAJOR) | Claude carrier corrected: IC-09 states Claude is `context-managed-block` (`ai-providers.yaml:24`), `templates/context/claude-managed.md` has no `GATE_*`, and the `hook` wording lives in `.claude/rules/use-orchestrator.md:1` (`sync_rules` `sync_pipeline.py:782`, vars `:748`). AC-14 observable changed to "the Claude provider surface contains the verbatim hook wording", not "the CLAUDE.md managed block carries it". |
| F-05 (MINOR) | IC-02/AC-02 fail-safe: `provider_config.get(u, {})`, non-dict → `{}`, degrades to `advisory`, no `KeyError`. |
| F-07 (MINOR) | Line numbers refreshed: `_sync_stage_contexts` `:328-378` + loop `:345-377`; `cli_commands.py` print `:1218`, exit `:1219`; rules seam `sync_pipeline.py:748` (consumed by `sync_rules :782` / `sync_embedded_rule_files :796`) added to the impact table. |
| F-08 (MINOR) | AC-13 scoped to the resolver set (Claude→`CLAUDE.md`, Gemini→`GEMINI.md`, rest direct readers of the core); the Antigravity dual-reader sub-case moved entirely into OQ-3. |
| F-09 (MINOR) | `context_mode` removed from IC-02 (Phase 0); IC-05 declares it solely as a Phase-1 symbol. |
| F-10 (MINOR) | `context_adapter_settings` added to IC-07; IC-09 names the provider-native settings write (Gemini `context.fileName` in `.gemini/settings.json`) as capability/`settings_file`-gated; new AC-26 observes activation (or default-context-file semantics). |
| N-01 (MINOR, non-blocking) | `orchestrator_hint` / `ORCHESTRATOR_INVOCATION_HINT` removed from the divergence enumerations (IC-03, Datenfluss §1, AC-07, AC-25, R7, OQ-13) and annotated there as currently unrendered / no consumer: no rule/template reads `{{ORCHESTRATOR_INVOCATION_HINT}}` (the variable is only assigned, at `context.py:1131` and `rules.py:227/249`), so a differing value cannot make the two shared renders differ and AC-25's clause about it was unsatisfiable. `ORCH_MODE_*` and `REPO_CONTAINMENT_*` stay (genuinely consumed). |

---

## Problem

`AGENTS.md` is the shared context file of Opencode (`runtime_gate: permission`,
`config/provider-capabilities.yaml:75`) and Gemini/Antigravity
(`runtime_gate: hook`, `:94`). Both are active in this repository
(`.meta-config/project.yaml:6-9` → `Claude`, `Opencode`, `Gemini`; `Claude`
renders `CLAUDE.md`, `config/ai-providers.yaml:5,7`).

Per sync run the file is rendered **twice** with a different tier, and the second
write overwrites the first, so the file never converges and `sync.py --check`
reports permanent drift:

1. `sync_pipeline._sync_stage_contexts` (`scripts/lib/sync_pipeline.py:328-378`;
   per-provider loop `:345-377`)
   iterates all providers, injects
   `provider_variables.update(runtime_gate_vars(pc, caps, config))`
   (`:373-375`) and calls `sync_context_for_provider(...)` (`:376`).
2. For every `AGENTS.md` sharer, `context.sync_context_for_provider`
   (`scripts/lib/context.py:818-857`) routes via
   `_shares_context_with_embedded_rules` (`:791-815`) into
   `_sync_opencode_context` (`:553`).
3. `_sync_opencode_context` renders the managed block with the **provider's own**
   `GATE_*` variables and writes it (`:607` → `_build_managed_block` `:1066`).

Because the tier differs per provider (`permission` for Opencode, `hook` for
Gemini), the two renders differ. The first sharer writes `permission`, the second
writes `hook`; on disk the `hook` render survives. A `--check` run
(`scripts/sync.py:99` forces dry-run) re-renders the first sharer's `permission`
variant, compares it against the disk, records one `UPDATE` action
(`context.py:622-623`), and `cli_commands.py:1209-1217` turns any action into
`sys.exit(1)`.

`sync.py --check` therefore never exits 0 in this repository — an unfixable,
config-independent rc1.

The defect is **not** the shared file. The existing convergence contract already
requires byte-identical renders per sharer
(`tests/test_agents_md_shared_context_convergence.py:49-115`). The defect is that
`runtime_gate_vars` is injected **outside** `_build_managed_block` per provider,
making a shared-block-invariant quantity provider-dependent. The structural
conflict (design §1.2) is that one file can carry only one honest gate wording,
while two sharers have different tiers. This spec resolves it deterministically:
`unified` (default) renders the shared file at the weakest sharer; `per-provider`
restores per-provider tier honesty through real file separation.

## Ziel

1. Two switchable modes, default = today's layout, configured via `context.mode`
   (`unified | per-provider`).
2. `unified`: exactly **one** deterministic render per shared `context_file`
   when the active sharers differ only in gate tier (effective tier = weakest
   active sharer; the `GATE_*` family is neutralised — AC-25/R7). `sync.py
   --check` converges on rc 0; divergent non-gate provider-scoped inputs remain
   a documented limitation (F-01).
3. `per-provider`: canonical core in `AGENTS.md` plus provider-native adapter
   files that reference/import the core and carry **their own** gate tier.
4. Provider-agnostic: exclusively config keys / capability flags, never
   `if provider == "..."`.
5. Backward compatible: the default `context.mode: unified` needs no new config,
   adds no files, and is byte-identical to today for every provider whose
   `context_file` is not shared with a different-tier sharer.

## Nicht-Ziele

- **No self-identification mechanism.** A second mechanism based on
  "if you are X" conditional blocks inside one file is explicitly excluded: the
  NeurIPS 2024 SAD benchmark shows self-identification instruction selection is
  unreliable. `per-provider` solves the problem exclusively through **real file
  separation** (config-driven adapters), never through in-file conditionals.
- **No Security boundary.** All guards stay a Convention boundary
  (terminology:
  `.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary`).
- No change to the runtime-gate core resolver
  `providers.py::provider_runtime_gate_tier` (`:357-386`) and no fork of
  `hooks.py` / `orchestrator-guard.sh`.
- No forced merge of `opencode.json` (#747).
- No fourth "neutral" value in `RUNTIME_GATE_TIERS`
  (`scripts/lib/runtime_gate.py:35`); `GATE_NEUTRAL` is a **render state**
  (Phase 1), not a runtime tier.
- No implementation, no plan, no REQ-ID assignment, no system redesign in this
  document.

## Interface Contracts

All new/changed symbols are listed as `file:Symbol`. New modules follow the
repository Python-3.9 convention (`from __future__ import annotations`,
`typing.Optional` / `typing.Dict` / `typing.List` / `typing.Tuple`, no PEP 604
unions in new modules) and use standard library plus existing repo-local helpers
only. Line numbers were re-verified against the repository at authoring time; a
shifted number must not change the named symbol.

### IC-01 — `scripts/lib/runtime_gate.py` (additive; Phase 0)

The existing vocabulary at `:35` is ordered strong→weak. The new rank adds the
explicit weak→strong order next to it so the weakest-tier resolution has exactly
one source of truth.

```python
RUNTIME_GATE_TIERS: Tuple[str, ...] = ("hook", "plugin", "permission", "advisory")  # existing :35, unchanged
RUNTIME_GATE_TIER_RANK: Mapping[str, int] = {                                        # new
    "advisory": 0, "permission": 1, "plugin": 2, "hook": 3,
}

def weakest_runtime_gate_tier(tiers: Iterable[str]) -> str:
    """Return the minimum tier by RUNTIME_GATE_TIER_RANK (weak -> strong).

    Fail-safe: an empty iterable or any unknown tier name yields "advisory"
    (the weakest assumed tier). Never raises.
    """
```

- **Error path:** `None`/non-iterable input is treated as empty → `"advisory"`;
  unknown names are ignored for the minimum but do not raise.
- `RUNTIME_GATE_TIERS` itself is **not** reordered and not extended.

### IC-02 — `scripts/lib/providers.py` (additive + internal refactor; Phase 0)

Extract the bundle builder out of `runtime_gate_vars` (`:389-423`) and add a
shared resolver. The public contract of `runtime_gate_vars` is **unchanged**.

```python
def _runtime_gate_bundle(tier: str, config: Optional[dict]) -> dict:
    """Build the GATE_* bundle for an already-resolved tier.

    Byte-identical to the current runtime_gate_vars body (:408-423):
    ENFORCEMENT_TIER, GATE_ENFORCED, GATE_PARTIAL, GATE_ADVISORY,
    RUNTIME_GATE_PLUGIN_MODE. Internal (leading underscore).
    """

def runtime_gate_vars(pc, capabilities, config) -> dict:
    """UNCHANGED public contract (:389-423); delegates to
    _runtime_gate_bundle(provider_runtime_gate_tier(pc, capabilities), config)."""

def shared_runtime_gate_vars(
    shared_users: list,
    provider_config: dict,
    capabilities_config: Optional[dict],
    config: Optional[dict],
) -> dict:
    """GATE_* bundle of the shared context file.

    tier = weakest_runtime_gate_tier(
        provider_runtime_gate_tier(provider_config.get(u, {}), (capabilities_config or {}).get(u))
        for u in shared_users
    )
    return _runtime_gate_bundle(tier, config)
    """
```

- `shared_users` are the **active** sharers of the physical file; the caller
  filters with `resolve_providers(config, provider_config)` (`:175`). This
  function does not filter.
- **Error paths (fail-safe, no `KeyError`):** a provider absent from
  `provider_config` is looked up as `provider_config.get(u, {})`; a non-mapping
  entry (or missing `capabilities_config`/`config`) degrades to `{}` and resolves
  to `advisory`. `provider_runtime_gate_tier` already treats a non-mapping `pc`
  as `{}` (`providers.py:378-379`), so the `.get(u, {})` default keeps the
  never-raises contract intact. The function never raises.
- `context_mode` is **not** declared here — it is a Phase-1 symbol, declared
  solely in [IC-05](#ic-05--scriptslipproviderspycontext_mode-phase-1) (F-09).
- `SUPPORTED_PLUGIN_PROTOCOLS` (`:312`), `provider_hooks_supported` (`:315`),
  `provider_runtime_gate_supported`, `provider_runtime_gate_tier` (`:357-386`)
  are untouched.

### IC-03 — `scripts/lib/context.py::_build_managed_block` (changed; Phase 0)

`_build_managed_block` (`:1066`) already computes `shared_users` itself from all
configured same-`context_file` providers (`:1091-1098`). After
`local_vars = dict(variables)` (`:1118`) and **before** the rule substitution
(`:1234-1235`), apply the shared override:

```python
if provider_config:
    from .providers import (
        load_provider_capabilities,
        resolve_providers,
        shared_runtime_gate_vars,
    )
    active = set(resolve_providers(config, provider_config))
    active_shared_users = [p for p in shared_users if p in active]
    if len(active_shared_users) > 1:
        capabilities_config = load_provider_capabilities(agent_meta_root)
        local_vars.update(shared_runtime_gate_vars(
            active_shared_users, provider_config, capabilities_config, config,
        ))
```

- The `GATE_*` values in the shared block and in the embedded rules
  (`use-orchestrator`, `a2a-delegation-gates`) become independent of which active
  sharer renders.
- **Neutralisation scope (F-01):** IC-03 neutralises the **`GATE_*` family only**
  (`ENFORCEMENT_TIER`, `GATE_ENFORCED`, `GATE_PARTIAL`, `GATE_ADVISORY`,
  `RUNTIME_GATE_PLUGIN_MODE`). `_build_managed_block` derives further
  provider-scoped inputs from the *currently rendering* provider that this
  override does **not** touch. Two of them are genuinely rendered and stay
  provider-scoped by design: `_orch_mode_flags(_resolve_orch_mode(orch_config,
  provider_override))` (`:1133-1136`) and
  `repo_containment_variables(config, provider)` (`:1141`). A third,
  `local_vars["ORCHESTRATOR_INVOCATION_HINT"] = pc.get("orchestrator_hint", "")`
  (`context.py:1131`), is **currently unrendered — no consumer**: no rule/template
  contains `{{ORCHESTRATOR_INVOCATION_HINT}}` (the variable is only *assigned*, at
  `context.py:1131` and `rules.py:227/249`), so it cannot itself make the renders
  differ and is listed here only as a reserved/unused variable (N-01). Because the
  rendered inputs remain provider-scoped, the determinism guarantee below is
  conditional, not absolute (R7, OQ-13, AC-25).
- `.providers` is already imported in this module (`:1171`); the local import in
  the branch is cycle-free.
- **Error paths:** when `provider_config` is falsy or `len(active_shared_users)
  <= 1`, no override happens — the per-provider `runtime_gate_vars` injected by
  `sync_pipeline` (IC-04) stays in effect, preserving single-provider behaviour.
- **Determinism definition (scoped):** the render of a shared `context_file` is
  deterministic **when the active sharers differ only in gate tier** — the case
  the Phase-0 defect is about. If two active sharers additionally diverge in a
  **rendered** non-gate provider-scoped input
  (`orchestrator.provider-overrides.<P>.mode` or a provider-scoped
  repo-containment override), the
  second write still overwrites the first and `--check` can return rc1 again;
  that configuration is explicitly **outside** this guarantee (documented
  limitation, not asserted as fixed). `orchestrator_hint` is not listed here: it
  is currently unrendered / has no consumer (N-01). If the **active** sharer set changes
  (provider switched on/off), the weakest tier legitimately changes; the next run
  then produces exactly one `UPDATE` and converges again.

### IC-04 — `scripts/lib/sync_pipeline.py` (Phase 0 unchanged)

`_sync_stage_contexts` (`:328-378`; per-provider loop `:345-377`) and
`_sync_stage_per_provider` (`:669`) are
**not** changed in Phase 0. The per-provider injection at `:373-375` stays and
continues to supply per-provider artefacts (rules files for `has_rules`
providers); for the shared context file IC-03 overrides it inside
`_build_managed_block`.

### IC-05 — `scripts/lib/providers.py::context_mode` (Phase 1)

Declared **here only**; the IC-02 sketch is removed so the Phase-0 section cannot
be read as wiring this Phase-1 symbol early (F-09). Precedence (deterministic,
fail-safe), mirroring
`variables._resolve_orch_mode` (`scripts/lib/variables.py:50-85`):

```
context.provider-overrides.<Provider>.mode   (highest)
        > context.mode
        > "unified"                          (default)
```

- Absent, `None`, non-string or out-of-enum values → `"unified"` (safe side: no
  new files and no new behaviour without explicit opt-in), never raises.

### IC-06 — `config/project-config.schema.json:context` (new top-level object; Phase 1)

Insert one new member into the root `properties` object as a sibling of
`context_file` (`:885-916`), i.e. next to it and before `"required"` (`:2315`).
Root `additionalProperties` stays `true` (`:2318`); the new block itself is
closed.

```json
"context": {
  "type": "object",
  "description": "Context-file topology mode (unified default). Sibling of context_file (density modes full/compact).",
  "properties": {
    "mode": {
      "type": "string",
      "enum": ["unified", "per-provider"],
      "default": "unified",
      "description": "Topology (one shared file vs. canonical core + adapters). NOT the density mode of context_file.mode (full/compact)."
    },
    "core_file": { "type": "string", "default": "AGENTS.md" },
    "provider-overrides": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "mode": { "type": "string", "enum": ["unified", "per-provider"] }
        }
      }
    }
  },
  "additionalProperties": false
}
```

- `context_file` (`:885-916`) is **unchanged** (density/size guard, #540). The two
  keys stay distinct namespaces.
- **Error paths:** `additionalProperties: false` rejects typos and unknown
  sub-keys; a non-string `mode`, an out-of-enum `mode` or a non-string
  `core_file` is rejected by validation. Absence of the whole block keeps the
  default (`unified`) with no new required key.

### IC-07 — `config/ai-providers.yaml` (new optional provider keys; Phase 1/2)

Per adapter-capable provider block:

```yaml
<Provider>:
  context_adapter: true|false                 # provider can read its own adapter file
  context_adapter_file: "<rel-path>"          # native file, e.g. "GEMINI.md"; Claude: existing CLAUDE.md
  context_adapter_import: "@{core}"           # provider-native import syntax; "" = pointer line
  context_adapter_import_supported: true|false
  context_adapter_settings: true|false        # default context file needs a settings key (F-10)
```

- `context_adapter` may equivalently be a capability `context-adapter` in
  `config/provider-capabilities.yaml` (same pattern as `context-embedded-rules` /
  `context-managed-block`).
- `context_adapter_settings: true` means the provider only reads the adapter when
  a provider-native settings key names it (e.g. `context.fileName` in
  `.gemini/settings.json`); the write is capability-gated in IC-09. When absent
  or `false`, the adapter file is the provider's default context file and no
  settings write is required (F-10).
- `context_adapter_file` is the provider's **native** file; it may stay unused in
  `unified`.
- Missing keys ⇒ the provider is a **direct reader of the core** (opencode,
  KimiCode, ZCode need no keys).
- `context.core_file` default `AGENTS.md`; a provider with
  `has_dedicated_context_file` (Claude, `:7`) keeps its file as the adapter.
- **Error path:** a capability registry invariant (AC-12) flags an
  adapter-capable provider that lacks `context_adapter_file` or
  `context_adapter_import_supported`.

### IC-08 — `scripts/lib/providers.py::resolve_context_filename` (legacy-cleanup scope only; Phase 1)

**This function is not on the render path** (F-02). Its only callers are
`_sync_stage_legacy_cleanup` (`sync_pipeline.py:445` and `:455`); the render
reads the raw key directly (`_sync_opencode_context` `pc["context_file"]`,
`context.py:566`; `_sync_managed_block_context` `pc.get("context_file")`,
`:496`). A change here can therefore only influence **which file the legacy
cleanup stage treats as active** (orphan protection) — it cannot make a provider
render a different filename. The render selection lives in IC-09.

The existing fallback `CLAUDE.md -> AGENTS.md` for a provider without
`has_dedicated_context_file` (`:254-289`) stays. Additional key-driven rule for
mode `per-provider`: when `context_adapter: true` is set, return
`context_adapter_file` instead of the core, so `_sync_stage_legacy_cleanup`
(`sync_pipeline.py:433-468`) does not delete the adapter file of a deactivated
provider's still-active adapter. No provider names.

- **Error path:** a missing/empty `context_adapter_file` with
  `context_adapter: true` falls back to the existing resolution (core) and is
  reported by IC-10/AC-12, never raises.
- **Explicitly out of scope:** AC-13's "file actually written" is asserted
  against IC-09's dispatch, not against this resolver return value (F-02).

### IC-09 — `scripts/lib/context.py` (core/adapter render; Phase 1/2)

```python
def sync_context_adapters_for_provider(
    agent_meta_root, project_root, config, variables, log, dry_run,
    provider, provider_config,
) -> None:
    """Write/refresh exactly one adapter file for an adapter-capable provider in
    mode per-provider.

    Target selection (this is the render switch, F-02): the dispatch chooses the
    physical filename from the IC-03/IC-07 keys -- context_adapter_file when
    context_adapter is true, otherwise context.core_file -- and hands it to the
    existing render strategies; resolve_context_filename (IC-08) is NOT used here.
    Concretely the target filename must be threaded into _sync_opencode_context
    (context.py:553, reads pc["context_file"] :566) and
    _sync_managed_block_context (:483, reads pc.get("context_file") :496), or
    those readers must take the selected name instead of the raw key.

    Content:
      - provider-native import line to context.core_file when supported,
        otherwise a pointer line;
      - the provider's own tier via runtime_gate_vars(pc, caps, config) where the
        provider's tier is carried by its render channel (see Claude note below).
    Lifecycle via the rule_index helpers (bootstrap_previously_managed :45,
    cleanup_stale_managed_files :110, write_managed_index :180) under the
    adapter index (IC-10/design §5.4). Idempotent: unchanged content => log.skip,
    no write.

    Settings activation (F-10): when context_adapter_settings is true, also write
    the provider-native settings key that names the adapter file (Gemini:
    context.fileName in .gemini/settings.json, whose template
    templates/configs/GEMINI.settings-template.json currently has no such key),
    capability/`settings_file`-gated through the existing settings writer; when
    false/absent, the adapter file is the provider's default context file and no
    settings write happens.
    """

def sync_context_for_provider(...) -> None:
    """Dispatch extension (:818-857): context_mode(config, provider) ==
    "per-provider" -> core render path + optionally
    sync_context_adapters_for_provider(); otherwise the current path unchanged.
    The core-vs-adapter filename selection happens here, never in IC-08."""
```

- **Claude carrier (F-04):** Claude is a `context-managed-block` provider
  (`config/ai-providers.yaml:24`; no `context-embedded-rules`), so its managed
  block — `templates/context/claude-managed.md`, rendered at `context.py:407` —
  carries only `{{PROVIDER_ROUTING}}`/`{{AGENT_HINTS}}` and **no `GATE_*`**. The
  verbatim `# CRITICAL GATE` hook wording for Claude lives in the native rules
  file `.claude/rules/use-orchestrator.md:1`, rendered by `sync_rules`
  (`sync_pipeline.py:782`) with the `runtime_gate_vars` injected in
  `_sync_stage_per_provider` (`sync_pipeline.py:748`). The Claude adapter in
  `per-provider` is therefore `CLAUDE.md` (`@AGENTS.md` import + managed block)
  **plus** that native rules file as its gate-wording carrier; the adapter must
  not promise `GATE_ENFORCED` inside the CLAUDE.md managed block.
- **Error paths:** no `context_adapter_file` → `log.warning` + return (never
  silent); an unsupported/empty import syntax → pointer line; `dry_run` never
  writes; a provider that is not adapter-capable is never routed here.

### IC-10 — `scripts/lib/consistency/context_mode.py` (new; Phase 2)

```python
def check_context_mode_consistency(
    root: Path,
    config: Optional[dict] = None,
    provider_config: Optional[dict] = None,
) -> list[Finding]:
    """Findings (Severity.WARNING/INFO) for the context-file mode:

    - context.mode is a valid enum value (otherwise WARNING);
    - per-provider: every adapter-capable active provider has a
      context_adapter_file; no two providers point at the same adapter file
      (collision => WARNING);
    - per-provider: the adapter file contains a reference to context.core_file
      (or the pointer) (WARNING otherwise);
    - unified: no orphaned adapter files without a managed-index entry (WARNING;
      points at the rollback).
    """
```

Registration in `scripts/consistency-check.py` directly beside
`check_context_file_size(root)` (`:202`), import beside
`from lib.consistency.context_size import check_context_file_size` (`:43`).
Finding/severity pattern as `context_size.py:114-127` (`Finding`, `Severity`,
`check=`-ID).

### IC-11 — Admin-UI / Server (Phase 2)

- `scripts/admin-server.py::PROJECT_WRITABLE_SECTIONS` (`:230-249`): add
  `"context"`. Without it `_assert_project_sections_writable` (`:4792-4806`)
  rejects every write with HTTP 400. No new endpoint — `_write_project_section`
  (`:4827`) is generic.
- `docs/ui/admin-ui.html::viewProject`: build a `context` object with defaults
  (`mode: unified`, `core_file: AGENTS.md`) analogous to the `contextFile` block
  (`:6170-6180`, save at `:6480`), add it to `saveProjectSections([...])`
  (`:6472-6481`) as `["context", contextCfg]`, render the mode as a dropdown and
  add a help text that explains the difference to `context_file.mode`.
- `check_ui_help_mappings` (`consistency-check.py:197`) needs a help entry for
  the new key (otherwise WARNING); pattern as in
  `tests/test_admin_ui_git_section.py:63-67`.

### IC-12 — `scripts/lib/config.py::fill_defaults` (Phase 1)

`fill_defaults` (`:886`) must write missing `context.mode` defaults without
introducing a new mandatory key: absence of the whole `context` block resolves to
`unified`; a present block is not widened beyond the schema.

### IC-13 — `scripts/lib/consistency/context_size.py::check_context_file_size` (Phase 2)

`check_context_file_size` (`:44`) already iterates all `context_file` paths
(`:91-101`). Extend it to also iterate adapter paths found via
`provider_config[p].context_adapter_file` so adapters count against `max_lines`
separately. Otherwise unchanged.

---

## Datenfluss

### 1. `unified` (Phase 0)

```
sync.py --check / sync
  └─> _sync_stage_contexts                      sync_pipeline.py:328-378
        │                                        (per-provider loop :345-377)
        └─ per provider:
             provider_variables.update(runtime_gate_vars(pc, caps, config))   :373-375  (stays)
             └─> sync_context_for_provider      context.py:818
                   └─> _sync_opencode_context   context.py:553
                         └─> _build_managed_block (IC-03)  context.py:1066
                               shared_users                     :1091-1098
                               active_shared_users = shared_users ∩ resolve_providers(...)
                               if |active_shared_users| > 1:
                                     local_vars.update(shared_runtime_gate_vars(...))
                                     # GATE_* only: tier = weakest(active)
                               else: provider's own runtime_gate_vars (unchanged)
                               # still provider-scoped (NOT neutralised, F-01):
                               #   ORCHESTRATOR_INVOCATION_HINT :1131  (unrendered / no consumer — N-01)
                               #   ORCH_MODE_*                  :1133-1136
                               #   REPO_CONTAINMENT_*           :1141
                               └─ one canonical render for the gate tier
                                     if new != existing: one UPDATE write   :622-623
                                     else:               log.skip            :627
  └─> cli_commands.py:1209-1217
        pending == 0  -> sys.exit(0)            (print :1218, exit :1219)
        pending  > 0  -> sys.exit(1)
```

### 2. `per-provider` (Phase 1/2)

```
sync.py
  └─> context_mode(config, provider)            providers.py (IC-05)
        |-- per-provider:
        |     ├─ core render: AGENTS.md (context.core_file), GATE_NEUTRAL, exactly 1 write
        |     └─ sync_context_for_provider dispatch (IC-09) selects the physical target:
        |           core_file vs context_adapter_file  <- render switch lives HERE, not in IC-08
        |           |-- context_adapter true  -> sync_context_adapters_for_provider (IC-09)
        |           |              ├─ import line (@AGENTS.md) or pointer line
        |           |              ├─ provider's own tier on its carrier channel:
        |           |              │    embedded-rules providers -> managed block GATE_*
        |           |              │    context-managed-block  -> native rules file (Claude:
        |           |              │                             .claude/rules/use-orchestrator.md)
        |           |              ├─ context_adapter_settings -> provider settings key
        |           |              │    (Gemini: context.fileName in .gemini/settings.json)
        |           |              └─ rule_index lifecycle + context-hashes
        |           └-- false -> direct reader of the core
        |                          (opencode / KimiCode / ZCode; Gemini dual-reader = OQ-3)
        |     └─ cleanup_stale_managed_files on mode switch / rollback (IC-09/§5.4)
        └─ unified: flow 1 above
```

---

## Acceptance Criteria

Each criterion is testable and observable and names the test that covers it.
"Resolver" means `scripts/lib/providers.py::provider_runtime_gate_tier`.

### Phase 0 — implementable now

1. **AC-01 (weakest-tier vocabulary and fail-safe).** Given the new
   `runtime_gate.py::weakest_runtime_gate_tier`, when called with
   `["hook", "permission"]`, then it returns `"permission"`; with `["advisory"]`,
   `"advisory"`; with `[]`, `None` or a list of unknown names, `"advisory"`
   without raising; and `RUNTIME_GATE_TIER_RANK` orders
   `advisory < permission < plugin < hook`. Test: new
   `tests/test_context_file_modes.py`.
2. **AC-02 (shared-tier resolver).** Given `shared_runtime_gate_vars` with
   active sharers whose resolved tiers are `permission` and `hook`, when it runs,
   then the bundle is the `permission` bundle (`ENFORCEMENT_TIER=permission`,
   `GATE_PARTIAL=true`, `GATE_ENFORCED=false`, `GATE_ADVISORY=false`); with a
   provider absent from `provider_config` it is looked up as
   `provider_config.get(u, {})` (no `KeyError`) and counts as `advisory`; a
   non-dict entry degrades to `{}`/`advisory`; the function never raises. Test:
   new `tests/test_context_file_modes.py`.
3. **AC-03 (shared override makes renders byte-identical).** Given the real
   `AGENTS.md` sharer set and the real `GATE_*` variables injected per sharer,
   when Opencode and Gemini each render `_build_managed_block`, then the two
   renders are byte-identical and contain the `permission` (`GATE_PARTIAL`)
   variant, not the `hook` (`GATE_ENFORCED`) variant. Test: new
   `tests/test_context_file_modes.py` **and** an extension of
   `tests/test_agents_md_shared_context_convergence.py` (the existing test at
   `:49-115` renders without `GATE_*` vars and therefore does not catch the
   defect — design §11). Test name:
   `test_shared_managed_block_identical_with_gate_vars`.
4. **AC-04 (effective shared tier is the weakest active sharer).** Given the
   repository config (active providers `Claude`, `Opencode`, `Gemini`), when the
   shared tier of `AGENTS.md` is resolved, then it is `permission` — the weakest
   over active sharers `{Opencode, Gemini}` — and the configured-but-inactive
   Codex/ZCode/KimiCode (`advisory`) do **not** lower it to `advisory`. The
   existing path-union in `_build_managed_block:1091-1098` (all configured
   same-name providers) is unchanged and only the tier computation is restricted
   to active sharers. Test: new `tests/test_context_file_modes.py`.
5. **AC-05 (single render / no double write).** Given a sync run over all active
   `AGENTS.md` sharers, when the run log is inspected, then exactly one sharer
   emits an `UPDATE` action for `AGENTS.md` and every later sharer emits
   `log.skip` (`context.py:627`) with byte-identical content; a second dry-run
   reports no `UPDATE` for `AGENTS.md`. Test: extend
   `tests/test_agents_md_shared_context_convergence.py`
   (`test_repeated_sync_never_reports_pending_agents_md_change`) with the real
   `GATE_*` variables.
6. **AC-06 (`sync.py --check` rc 0 on the current repository).** Given the
   canonicalized `AGENTS.md` is committed with this change, when
   `python3 scripts/sync.py --check` runs in the repository, then it exits `0`
   (`cli_commands.py:1218` prints "Provider context files are up to date.",
   `sys.exit(0)` `:1219`). The one-time canonicalization (`hook` → `permission`
   wording) must be part of the change, otherwise `--check` stays rc1 until the
   regenerated file is committed. Test (Phase 0): the unit-level repeated
   dry-run assertion of AC-05 plus the committed-`AGENTS.md` `--check` rc0. The
   scenario `63-context-file-modes` assertion is **not** part of this Phase-0
   criterion — the scenario is created only in Phase 2 and is asserted by AC-21
   (F-03).
7. **AC-07 (backward-compatible default / no-op).** Given a project without
   `context.mode` and without a mixed-tier shared file (e.g. a Claude-only
   project, or a hook-only shared group), when sync runs, then the render is
   byte-identical to the pre-change behaviour and no additional file is created;
   for a mixed-tier shared group the render is lowered to the weakest tier exactly
   once (the only documented content change). This guarantee is **scoped**: it
   holds when the active sharers differ only in gate tier; divergent non-gate
   provider-scoped inputs (`orchestrator.provider-overrides.<P>.mode`,
   provider-scoped repo-containment) are outside it (AC-25, R7). `orchestrator_hint`
   is not part of this enumeration — it is currently unrendered / has no consumer
   (N-01). Test: extend
   `tests/test_agents_md_shared_context_convergence.py` and run the full suite.
8. **AC-08 (`runtime_gate_vars` contract unchanged).** Given representative
   `(pc, capabilities, config)` tuples, when `runtime_gate_vars` runs after the
   `_runtime_gate_bundle` refactor, then its dict is byte-equal to the pre-change
   output for the same tier, and the existing tests
   `tests/test_runtime_gate_config.py`, `tests/test_runtime_gate_wiring.py` and
   `tests/test_runtime_gate_rendering.py` stay green. Test: those modules.
9. **AC-09 (provider-agnostic).** Given the new/changed modules, when the AST scan
   runs, then no module contains a provider-name literal equality branch;
   `runtime_gate` and `isolation` are already in `_TOUCHED_MODULES`
   (`tests/test_provider_agnostic_dispatch.py:27-51`) and
   `consistency/context_mode` is added if that module exists. Test: extend
   `tests/test_provider_agnostic_dispatch.py`.
25. **AC-25 (determinism scope — only `GATE_*` is neutralised).** Given two
    active sharers of one `context_file` that differ only in gate tier, when each
    renders `_build_managed_block`, then the two renders are byte-identical (the
    IC-03 guarantee). Given the same pair with a divergent non-gate
    provider-scoped input (`orchestrator.provider-overrides.<P>.mode` or a
    provider-scoped repo-containment override), when each renders, then the renders
    differ and that configuration is explicitly **outside** the guarantee
    (R7, OQ-13) — IC-03 neutralises `GATE_*` only. The test also asserts that
    `ORCH_MODE_*` and `REPO_CONTAINMENT_*` are the sole remaining **rendered**
    provider-scoped inputs in the shared block (`context.py:1133-1136`, `:1141`);
    `ORCHESTRATOR_INVOCATION_HINT` (`context.py:1131`) is still assigned but is
    currently unrendered — no rule/template consumes it (it is only assigned here
    and at `rules.py:227/249`) — so it is **not** a divergence source and is not
    part of this assertion (N-01). Test: new
    `tests/test_context_file_modes.py`.

### Phase 1 — `per-provider` core (gated/deferred from Phase 0)

> AC-10 … AC-18 and AC-26 are deferred until Phase 0 is implemented and the
> mixed-tier shared-file rc1 is fixed. The Claude and Gemini adapter semantics are
> VERIFIED-RESEARCH; the Codex/Copilot/Continue/Mammouth adapters (AC-22) stay in
> Phase 2 behind their HYPOTHESIS checks.

10. **AC-10 (`context.mode` precedence and fail-safe).** Given
    `context.provider-overrides.Gemini.mode: unified` with `context.mode:
    per-provider`, when `context_mode(config, "Gemini")` is called, then it
    returns `"unified"` (provider override wins); for `Opencode` it returns
    `"per-provider"`; with no `context` block it returns `"unified"`; with
    `context.mode: "garbage"` or a non-mapping config it returns `"unified"`
    without raising. Test: new `tests/test_context_file_modes.py`.
11. **AC-11 (schema validation for `context`).** Given the shipped
    `config/project-config.schema.json`, when a config with a valid `context`
    block (`mode` in enum, string `core_file`, nested `provider-overrides`) is
    validated, then it is accepted; when `context.mode` is out of enum, a
    sub-key is unknown (`additionalProperties: false`), or `core_file` is not a
    string, then validation rejects it; absence of the block is accepted and
    resolves to `unified`. Test: new `tests/test_context_mode_schema.py`, pattern
    as `tests/test_runtime_gate_schema.py` / `tests/test_subagent_permissions_schema.py`.
12. **AC-12 (adapter-capability registry invariant).** Given the two registries,
    when cross-checked, then every provider with `context_adapter: true` (or the
    `context-adapter` capability) carries a non-empty `context_adapter_file` and
    an explicit `context_adapter_import_supported` boolean, and no two adapter
    providers point at the same `context_adapter_file`. Test: extend
    `tests/test_provider_agnostic_dispatch.py` and add cases in
    `tests/test_context_adapters.py`.
13. **AC-13 (topology: which providers stay on `AGENTS.md`).** Given
    `context.mode: per-provider`, when sync runs, then opencode, KimiCode and
    ZCode stay direct readers of `context.core_file` (`AGENTS.md`) with **no**
    adapter file written, while Claude is written to its dedicated `CLAUDE.md`
    adapter and Gemini to `GEMINI.md`. The assertion is bound to the file the
    dispatch (`sync_context_for_provider`/`sync_context_adapters_for_provider`,
    IC-09) **actually writes**, not to `resolve_context_filename` (which only
    feeds legacy cleanup, IC-08). The distinction is derived only from the IC-07
    keys / `has_dedicated_context_file`, never from a provider name. The Gemini
    dual-reader (Antigravity runtime vs. Gemini CLI on one provider entry) is
    **not** asserted here — it stays OQ-3 (F-08). Test: new
    `tests/test_context_adapters.py` (write paths); extend
    `tests/test_provider_context_filename.py` (legacy-cleanup resolver only).
14. **AC-14 (adapter render and per-adapter tier correctness).** Given mode
    `per-provider`, when sync runs, then the core `AGENTS.md` carries the neutral
    `GATE_NEUTRAL` directive (no runtime promise); the Claude adapter is the
    `CLAUDE.md` `context-managed-block` render (import + managed block, **no**
    `GATE_*`), and the verbatim `hook` wording (`# CRITICAL GATE`, per
    `SPEC-OPENCODE-RUNTIME-GATE-2026-09-13` F-05/IC-07) is on Claude's provider
    surface in its native rules file `.claude/rules/use-orchestrator.md`
    (rendered by `sync_rules`, `sync_pipeline.py:782`/`:748`); the Gemini adapter
    carries `hook` in its embedded-rules managed block; and an `advisory` adapter
    provider (Codex/Copilot/Continue/Mammouth, Phase 2) would carry
    `GATE_ADVISORY`. The observable for Claude is "the provider surface contains
    the verbatim hook wording", not "the `CLAUDE.md` managed block carries it"
    (F-04). Test: new `tests/test_context_adapters.py`; extend
    `tests/test_runtime_gate_rendering.py`.
15. **AC-15 (import/reference semantics).** Given an adapter provider with
    `context_adapter_import_supported: true` and `context_adapter_import:
    "@{core}"`, when the adapter is rendered, then it contains the provider-native
    import line `@AGENTS.md`; with `context_adapter_import_supported: false` it
    contains a pointer line to `context.core_file`; an empty/unsupported syntax
    falls back to the pointer line and never crashes. Test: new
    `tests/test_context_adapters.py`.
16. **AC-16 (idempotency of the `per-provider` render).** Given a `per-provider`
    sync run twice without a config change, when both outputs are compared, then
    the core and every adapter file are byte-identical and a subsequent
    `--check` reports `pending == 0`. Test: new `tests/test_context_adapters.py`.
17. **AC-17 (managed index and drift tracking).** Given generated adapters, when
    the managed-index helpers (`rule_index.py:45,110,180`) and
    `consistency/context_mode.py` run, then every adapter is recorded in the
    adapter index, receives a context-hash entry
    (`context.py::_record_static_hash`/`_save_context_hashes`) and is found by
    `generated_file_drift`; a modified/orphaned adapter is reported. The
    size-guard counting of adapters is **not** part of this Phase-1 criterion —
    it belongs to Phase 2 (IC-13/AC-24, F-03). Test: new
    `tests/test_context_adapters.py`; extend `tests/test_generated_file_drift.py`.
18. **AC-18 (rollback to `unified`).** Given a project switched from
    `per-provider` back to `unified`, when sync runs, then the core `AGENTS.md`
    again carries the shared weakest-tier block, every adapter recorded in the
    index is removed, foreign/user files without an index entry are untouched,
    `--check` reports `pending == 0`, and no orphaned adapter remains. Test: new
    `tests/test_context_adapters.py`.
26. **AC-26 (adapter settings activation).** Given an adapter provider with
    `context_adapter_settings: true`, when the adapter is rendered in
    `per-provider`, then the provider-native settings key that activates the
    adapter file is written capability/`settings_file`-gated (worked example:
    `context.fileName` in `.gemini/settings.json`, whose shipped template
    `templates/configs/GEMINI.settings-template.json` currently carries no such
    key), and the Phase-1 real-repo check observes that the provider actually
    reads the adapter. Given `context_adapter_settings` absent/`false`, then no
    settings write happens and the adapter file is the provider's default context
    file (F-10). Test: extend `tests/test_context_adapters.py`; documented
    real-repo verification task for the Gemini/`context.fileName` case.

### Phase 2 — remaining adapters + consistency + UI (gated/deferred)

19. **AC-19 (mode consistency check).** Given the new
    `check_context_mode_consistency`, when registered in
    `scripts/consistency-check.py` beside `check_context_file_size` (`:202`), then
    an invalid `context.mode` yields a WARNING, two providers pointing at the same
    adapter file yield a WARNING, a `per-provider` adapter missing its core
    reference yields a WARNING, and an orphaned adapter in `unified` yields a
    WARNING — while a consistent configuration yields none. Test: new
    `tests/test_context_mode_consistency.py`.
20. **AC-20 (Admin-UI / Server).** Given the running admin server, when the
    project `context` section is written through the existing endpoint, then the
    write is accepted (the section is in `PROJECT_WRITABLE_SECTIONS`) rather than
    rejected with HTTP 400; the UI renders a `mode` dropdown with the default
    `unified` and a help text distinct from `context_file.mode`; and
    `check_ui_help_mappings` produces no finding for `context`. Test: extend
    `tests/test_admin_server.py` and `tests/test_admin_ui_git_section.py`
    (help-mapping pattern); new `tests/test_context_mode_admin.py` for the UI
    shape.
21. **AC-21 (scenario `63-context-file-modes`).** Given the scenario registry
    ends at `62-stale-role-cleanup` (`tests/scenarios/registry.md:109`), when the
    scenario is added, then `tests/scenarios/registry.md` has a
    `63-context-file-modes` entry, `tests/scenarios/configs/63-context-file-modes.project.yaml`
    exists, and `tests/scenarios/asserts/63-context-file-modes.sh` asserts the
    `unified` default run byte-identical plus the committed-`AGENTS.md`
    `--check` rc 0 and the `per-provider` run producing core + adapters. This
    scenario assertion is the one **moved out of Phase-0 AC-06** (F-03): the
    scenario is created only here, so no earlier-phase criterion may reference
    it. Test: the scenario harness.
22. **AC-22 (Phase-2 adapters stay behind their HYPOTHESIS).** Given Codex
    (`AGENTS.override.md` vs. `project_doc_fallback_filenames`), Copilot (path
    `.github/copilot-instructions.md` vs. the configured
    `ai-providers.yaml:293` path), Continue/Mammouth (pointer semantics) and the
    Gemini dual-reader risk, when sync runs, then none of these providers uses an
    adapter unless the corresponding HYPOTHESIS (design §9.3, A5) is verified in
    a real repository and recorded; Codex, Copilot, Continue and Mammouth stay
    direct readers of the core by default. Test: new `tests/test_context_adapters.py`
    (default-not-enabled assertions) plus a documented real-repo verification
    task.
23. **AC-23 (neutral core render state).** Given `GATE_NEUTRAL` as a render state
    (not a value in `RUNTIME_GATE_TIERS`, `runtime_gate.py:35` unchanged), when
    the core is rendered in `per-provider`, then it states the directive
    ("MAIN CHAT darf nicht selbst editieren. ALLES -> orchestrator.") without a
    runtime promise, and `a2a-delegation-gates` points at "multiple providers,
    see adapter"; no file contains an "if you are X" block. Test: new
    `tests/test_context_adapters.py`; extend `tests/test_runtime_gate_rendering.py`.
24. **AC-24 (adapter size guard).** Given an oversized adapter file, when
    `check_context_file_size` runs, then it emits a WARNING naming the adapter
    path (separately from the core), and `context_file.max_lines` applies; an
    acknowledged override suppresses it. Test: extend
    `tests/test_context_size_guard.py`.

---

## Berührter Phase-0-Code des Runtime Gates

The Runtime Gate (SPEC-OPENCODE-RUNTIME-GATE-2026-09-13, Phase 0) is
implemented. Impact of this change on that code:

| Symbol / file | Status | Reason |
|---|---|---|
| `providers.py::provider_runtime_gate_tier` (`:357-386`) | **untouched** | stays the single tier truth; the weakest rule only consumes it. |
| `providers.py::runtime_gate_vars` (`:389-423`) | **contract unchanged**, delegates internally | `_runtime_gate_bundle` is extracted; output byte-identical; `tests/test_runtime_gate_config.py` / `test_runtime_gate_wiring.py` stay valid. |
| `providers.py::provider_hooks_supported` (`:315`), `provider_runtime_gate_supported`, `SUPPORTED_PLUGIN_PROTOCOLS` (`:312`) | **untouched** | not part of the fix. |
| `runtime_gate.py::RUNTIME_GATE_TIERS` (`:35`) | **untouched**, additive | rank + weakest function beside it; no new tier value, no reorder. |
| `context.py::_build_managed_block` (`:1066`) | **changed (behaviour for shared files)** | core of the Phase-0 fix (IC-03). |
| `context.py::_sync_opencode_context` (`:553`, reads `pc["context_file"]` `:566`), `_sync_managed_block_context` (`:483`, reads `pc.get("context_file")` `:496`), `sync_context_for_provider` (`:818-857`) | Phase 0 **untouched**; Phase 1/2 dispatch extension | the core-vs-adapter target selection (IC-09) is threaded here; `resolve_context_filename` (IC-08) is not on this path. |
| `sync_pipeline.py` context seam (`:373-375`) | **untouched** (Phase 0) | per-provider injection still feeds per-provider artefacts; the shared render overrides in `_build_managed_block`. |
| `sync_pipeline.py` rules seam (`:748` `runtime_gate_vars`, consumed by `sync_rules` `:782` / `sync_embedded_rule_files` `:796`) | **untouched** (Phase 0) | second injection point; supplies the per-provider `GATE_*` to the native rules file `.claude/rules/use-orchestrator.md` (Claude's hook wording, F-04). |
| `isolation.py` (`_sync_opencode_runtime_gate`) | **untouched** | the `opencode.json` runtime enforcement stays exactly as implemented. |
| `consistency/orchestrator_strict.py` | **untouched** | keeps reading `provider_runtime_gate_tier`. |
| `rules/1-generic/use-orchestrator.md`, `a2a-delegation-gates.md`, `variables.py:235`, `consistency/placeholders.py` | Phase 0 **untouched**; Phase 1 adds `GATE_NEUTRAL` | the three `GATE_*` conditionals already ship. |

**Committed behaviour that must change (explicit):**

1. The gate wording in the **shared** `AGENTS.md` group is lowered from the
   last-writer tier to the weakest tier. With active opencode (`permission`),
   Gemini/Antigravity reads the `permission`/partial variant in `AGENTS.md`
   instead of `# CRITICAL GATE` (`hook`). This is intended: one file cannot carry
   two honest guarantees. The `hook` honesty for Claude (`CLAUDE.md`, dedicated)
   is untouched; Gemini regains it in Phase 1 through the `GEMINI.md` adapter.
   **The regenerated `AGENTS.md` must be committed with the change** so that
   `--check` is rc 0 (AC-06).
2. `sync.py --check` switches from rc 1 to rc 0 — the goal.
3. `tests/test_runtime_gate_rendering.py` stays valid: it renders the **rule
   template**, not the shared file.
4. `tests/test_agents_md_shared_context_convergence.py` stays valid but does not
   catch the defect (it renders without `GATE_*` vars); Phase 0 adds a test that
   injects the real per-provider `GATE_*` vars (AC-03).

No commit of the Runtime-Gate change has to be reverted; the weakest rule is an
additive invariant over its already-committed `GATE_*` vocabulary.

---

## Offene Fragen + Risiken

The design's OQ-1 … OQ-12 (design §12) are carried over; OQ-3 is extended with
the Gemini dual-reader limitation (F-08) and OQ-13 is added (F-01). Each has a
recommended default and the design's risk list becomes R1 … R7. Items marked
**[User approval]** need an explicit user decision because they affect the
shipped guarantee, a public config contract or a provider enablement.

1. **OQ-1 — collision `context.mode` vs. `context_file.mode`.** Recommended
   default: keep `context.mode` (commission decision); mitigate with an explicit
   schema `description` and a UI help label "context topology (not density)".
   No user approval needed.
2. **OQ-2 — core content in `per-provider`: neutral (`GATE_NEUTRAL`) vs.
   weakest tier.** Recommended default: neutral (design §5.2, DECISION-4).
   **[User approval]** — it determines that direct readers of the core (opencode,
   KimiCode, ZCode, Antigravity runtime) receive a conservative, advisory-near
   statement instead of a concrete tier.
3. **OQ-3 — Gemini dual reader.** `GEMINI.md` adapter plus the Antigravity
   runtime reading `.agents/AGENTS.md`. Recommended default (HYPOTHESIS): Gemini
   CLI adapter only via `context.fileName`, Antigravity runtime keeps the core;
   real-repo test before enabling. **[User approval]** for the go/no-go on the
   Gemini adapter (Phase 1). The dual-reader sub-case lives **entirely here**
   (F-08): the single registered `Gemini` entry (`config/ai-providers.yaml:89`)
   cannot be simultaneously `context_adapter: true` (→ `GEMINI.md`) and a direct
   core reader, so AC-13 does not assert both outcomes.
4. **OQ-4 — Codex adapter mechanics.** `AGENTS.override.md` vs.
   `project_doc_fallback_filenames`. Recommended default: leave Codex a direct
   reader in Phase 1; adapter only after HYPOTHESIS verification. **[User
   approval]** for the enablement, otherwise no decision needed.
5. **OQ-5 — Copilot adapter path.** `ai-providers.yaml:293`
   (`.github/copilot/COPILOT.md`) vs. `.github/copilot-instructions.md`.
   Recommended default: keep the existing config path, adapter as a pointer,
   verify the path. HYPOTHESIS; **[User approval]** only if a path change is
   wanted.
6. **OQ-6 — Continue/Mammouth import semantics.** Is a pointer line enough?
   Recommended default: yes (HYPOTHESIS); otherwise duplicate the core content
   (with size/drift risk). HYPOTHESIS; no user approval unless duplication is
   proposed.
7. **OQ-7 — adapter and size guard.** Do adapters count separately against
   `max_lines`? Recommended default: yes (IC-13, AC-24). No user approval needed.
8. **OQ-8 — adapter managed-index name.** Own index vs. shared index.
   Recommended default: own index (`.agent-meta-context-adapters-managed`). No
   user approval needed.
9. **OQ-9 — opencode prompt underclaim.** opencode has `permission` enforcement
   but reads the neutral statement in the core. Recommended default: accept
   (conservative/honest; runtime enforcement via `opencode.json` unchanged). No
   user approval needed.
10. **OQ-10 — mode-switch detection.** How does sync learn that adapters must be
    created/torn down? Recommended default: mode resolver per run; build/teardown
    via the managed index (`cleanup_stale_managed_files`), no separate migration
    CLI. No user approval needed.
11. **OQ-11 — provider deactivation.** Remove the adapter of a deactivated
    provider? Recommended default: yes, via the existing
    `_sync_stage_legacy_cleanup` logic (`sync_pipeline.py:433`) plus the adapter
    index. No user approval needed.
12. **OQ-12 — `provider-overrides` shape.** Flat `mode` field vs. nested object.
    Recommended default: nested (`{mode: …}`), analogous to
    `orchestrator.provider-overrides` (`variables.py:50-85`). No user approval
    needed.
13. **OQ-13 — non-gate provider-scoped inputs in the shared block (F-01).**
    IC-03 neutralises only `GATE_*`; the rendered non-gate inputs
    `ORCH_MODE_*` and `REPO_CONTAINMENT_*` still come from the rendering sharer
    (`context.py:1133-1136`, `:1141`). `ORCHESTRATOR_INVOCATION_HINT`
    (`context.py:1131`) is assigned too but currently unrendered / has no consumer
    (N-01), so it is not a divergence source. Recommended default: **document
    and scope the limitation** (option (a)) — guarantee byte-identity only when
    active sharers differ solely in gate tier, and record this as R7; do **not**
    neutralise the other fields in Phase 0 (that would change unrelated rendering
    semantics). Alternative, if a general guarantee is wanted: extend the IC-03
    shared override to resolve those fields over the active sharer union.
    **[User approval]** because it decides whether the shipped guarantee is the
    narrow or the general one.

**Risks carried with the design:**

- **R1 (Phase 0, blocking until fixed): a stale committed `AGENTS.md` keeps
  `--check` at rc 1.** Mitigation: the canonicalized file is committed with the
  change (AC-06). No new config is needed.
- **R2: one-time content change of the shared `AGENTS.md` (hook → permission
  wording).** Intended and documented (design §2 Backward Compatibility, §11);
  Gemini's `hook` honesty returns with the Phase-1 adapter. Needs the user's
  awareness via OQ-2.
- **R3: residual second (no-op) render per sharer.** The double-write is
  eliminated; a second `log.skip` call remains per sharer (design §4.3). A
  run-scoped memo is explicitly not introduced in Phase 0.
- **R4: determinism depends on the active sharer set.** Switching a provider
  on/off legitimately changes the weakest tier and produces exactly one `UPDATE`
  before re-converging (design §4.2).
- **R5: Phase-1/2 adapter lifecycle.** Adapter creation, import semantics and
  cleanup are provider-specific and partly HYPOTHESIS (design §5.4, §9.3); the
  managed index authorizes deletion, foreign files stay untouched.
- **R6: `provider-overrides` for `context` is a new public contract.** A nested
  object with `additionalProperties: false` per IC-06 prevents typos; the
  precedence must be tested (AC-10).
- **R7 (F-01): the determinism guarantee is scoped to `GATE_*`.** If two active
  sharers diverge in a **rendered** non-gate provider-scoped input
  (`orchestrator.provider-overrides.<P>.mode`, provider-scoped repo-containment),
  IC-03 does not neutralise it: the second write overwrites
  the first and `sync.py --check` can return rc1 again. Mitigation: documented
  limitation + AC-25; the general fix is the OQ-13 alternative (out of Phase 0).
  `orchestrator_hint` is not part of this risk — it is currently unrendered / has
  no consumer (N-01). This repository has no such divergent overrides, so the
  Phase-0 rc1 fix (AC-06) is unaffected.

---

## Trace-Anker

- `spec-id: SPEC-CONTEXT-FILE-MODES-2026-09-13` — plans for this feature
  reference this value via their `**Spec:**` field. A plan is authored only after
  `Status: APPROVED` and is out of scope for this document.
- Source design: `docs/specs/2026-09-13-context-file-modes-system-design.md`
  (same `spec-id`; this spec adopts the anchor unchanged).
- Related spec: `SPEC-OPENCODE-RUNTIME-GATE-2026-09-13`
  (`docs/specs/2026-09-13-opencode-runtime-gate-design.md`) — this feature
  extends it and fixes the `AGENTS.md` double-write / `--check` rc1 defect. Its
  tier vocabulary (`hook | plugin | permission | advisory`), its Phase-0
  contracts and its F-05 byte-identical hook wording stay binding; this spec adds
  the shared-context-file invariant on top and does not withdraw any of its
  approvals.
