---
spec-id: SPEC-OPENCODE-RUNTIME-GATE-2026-09-13
title: OpenCode Runtime Gate (Problem A) — Technical Specification
status: APPROVED
source-design: docs/specs/2026-09-13-opencode-runtime-gate-system-design.md
related-issue: "#794"
---

# OpenCode Runtime Gate (Problem A) — Spec

> Status: **APPROVED** (2026-09-13) — approved by the user on 2026-09-13; the
> approval was recorded by the `concept-reviewer` role. The documented recommended
> defaults for the open questions were accepted unchanged. This document is a
> specification only: it defines interface contracts and acceptance criteria and
> contains no implementation and no plan.
> Trace anchor (unchanged from the system design):
> `spec-id: SPEC-OPENCODE-RUNTIME-GATE-2026-09-13`.
> Source design: `docs/specs/2026-09-13-opencode-runtime-gate-system-design.md`
> (same `spec-id`; the design adopts the anchor and passes it to this spec
> unchanged).

### Scope of the acceptance criteria

The system design phases the work; this spec inherits the phasing.

- **Phase 0** (`A2` permission-path tightening + `A3` honest tiered guarantee +
  `A4` consistency severity) is **implementable now**. It introduces no
  dependency on the unverified *plugin* runtime API. It does, however, ship
  with two **open provider-behaviour hypotheses as documented Phase-0 risks**:
  AN-6/permission precedence (OQ-3 — does agent frontmatter permission override
  the root deny for `orchestrator`/`git`?) and AN-3/child-session propagation
  (OQ-4 — `deriveSubagentSessionPermission`, #765). If AN-6 is verified false,
  the fallback is to narrow A2 to fine-grained globs for `bash`/`edit` (OQ-3).
  **AC-01 … AC-15 and AC-23** cover Phase 0 and are the criteria the
  implementation is signed off against first.
- **Phase 1** (`A1` native plugin behind a capability flag) splits into two
  sub-stages. The **plugin generator, managed state, drift tracking and
  observe-mode artifact** — **AC-16 … AC-20 and AC-22** — are **implementable
  now**: the design requires the plugin to exist and run in `MODE=observe`
  *before* P6 (design §6.2 "Bis dahin läuft das Plugin im Modus observe"; D8
  "observe first"). Only the **tier flip** (`runtime_gate: plugin`), the
  `MODE=enforce` opt-in and the **P6 real-repo verification (AC-21)** depend on
  P6: no provider may declare `runtime_gate: plugin` or `MODE=enforce` before P6
  is recorded as passed. The design lists the four plugin hypotheses
  (AN-3 … AN-6, design §7.3) that P6 must resolve.

The design's OQ-1 … OQ-10 (design §11) are carried over in
[Offene Fragen + Risiken](#offene-fragen--risiken); each has a recommended
default and a flag for whether it needs explicit user approval.

### Revision — incorporated review findings

| Finding | Change |
|---|---|
| Erstfassung | Base version. D-C1 … D-C5 are corrections carried over from the design/self-consistency pass before this `concept-reviewer` cycle; further rows are appended on `CHANGES_REQUESTED`, iteration by iteration (max 3). |
| D-C1 | Tier-resolver signature clarified to reconcile C1 and C2 registries: `provider_runtime_gate_tier(pc, capabilities=None)` reads the machine flags from the `ai-providers.yaml` entry (`pc`) and the declared tier from the `provider-capabilities.yaml` entry (`capabilities`). The design's single-argument form cannot reach the `permission` tier because `runtime_gate` lives in the other registry (see IC-03). |
| D-C2 | The severity opt-in is resolved to the non-breaking sibling key `orchestrator.require-runtime-gate` (bool). The design's `orchestrator.strict.require_runtime_gate` is not implementable: `orchestrator.strict` is already a `boolean` (`config/project-config.schema.json:2092-2096`), not an object (see IC-12, AC-14). |
| D-C3 | A2 must not be hung inside `sync_provider_isolation`: that dispatcher returns early unless `len(providers) >= 2` (`scripts/lib/isolation.py:54-56`), so a single-provider OpenCode project would never get the Main-Chat deny. The A2 helper is dispatched from the per-provider sync stage independently of the isolation ≥2 gate (see IC-09, AC-09). |
| D-C4 | A2 merge-safety: `_sync_opencode_isolation` currently assumes `permission.read` / `permission.edit` are mappings (`scripts/lib/isolation.py:238-241`). The two writers of `opencode.json` share those keys, so the contract requires the shared merge to tolerate scalar-or-mapping permission values and to track ownership via the managed state file (see IC-09, AC-10, AC-11). |
| D-C5 | Scenario ID: the design names scenario `60`; the registry now ends at `61-hook-deploy-lf-newlines` (`tests/scenarios/registry.md:108`). The Phase 1 scenario is therefore `62-opencode-runtime-gate` (see AC-21). |
| F-01 (BLOCKER) | A2 merge shape fixed to mapping-form deny globs inside `permission.edit`/`permission.bash`: `{'edit': {'**': 'deny'}, 'bash': {'**': 'deny'}}`, disjoint from isolation's glob keys; `_read_state`/`_write_state` generalised to namespaced keys (`isolation-deny`, `runtime-gate-deny`) with read-modify-write preserving sibling namespaces; ownership/rollback + writer ordering specified; AC-10 repaired; AC-23 (multi-provider coexistence) added; OQ-11 resolved (IC-09, AC-10, AC-11, AC-23, OQ-11). |
| F-02 (MAJOR) | Tier vars no longer wired through `agent_sync._build_provider_vars` (which the rule/context renderers never call). New `providers.runtime_gate_vars(...)` (IC-03) is injected into `provider_variables` at both actual seams: `sync_pipeline._sync_stage_contexts` (before `sync_context_for_provider`) and `_sync_stage_per_provider` (before `sync_rules`/`sync_embedded_rule_files`); `rules.py::_merged_rule_vars` and `context.py::_build_managed_block` named as verified (unchanged) propagation points; Datenfluss §2 arrows retargeted (IC-03, IC-04, Datenfluss §2). |
| F-03 (MAJOR) | P6 gate narrowed: only the tier flip + `MODE=enforce` + AC-21 depend on P6; AC-16 … AC-20 and AC-22 are implementable now in observe mode, matching the design's observe-before-P6 phasing (Scope, Phase-1 AC header, Datenfluss §3). |
| F-04 (MAJOR) | Phase-0 "no unverified API" claim narrowed to the *plugin* runtime API; AN-6 (permission precedence, OQ-3) and AN-3 (child-session propagation, OQ-4) explicitly documented as Phase-0 risks with the fine-glob fallback (Scope). |
| F-05 (MAJOR) | `GATE_ENFORCED` branch now reproduces the current strict wording verbatim (`# CRITICAL GATE`, `… ALLES -> \`orchestrator\`. Keine Ausnahmen.`); provenance is carried by the adjacent tier note, keeping hook-provider output byte-identical (IC-07, AC-05, AC-15). |
| F-06 (MINOR) | AC-02 plugin biconditional qualified with `and not provider_hooks_supported(pc)` to resolve hook/plugin precedence overlap. |
| F-07 (MINOR) | A2 dispatch condition pinned to the concrete resolver value `provider_runtime_gate_tier(pc, caps) == "permission"` (IC-01/IC-03); `isolation-mechanism` is no longer used as a gate-capability proxy (IC-09, IC-13). |
| F-08 (MINOR) | `runtime-gate.plugin-mode` gets a typed schema IC-16 + AC-24 (`enum: [observe, enforce]`, `additionalProperties: false`) instead of an unvalidated root key. |
| F-09 (MINOR) | `all_providers_runtime_gate_supported` dropped from IC-03 (no project-wide-guarantee consumer in this change; a future consumer mirrors `all_providers_support_hooks`). |
| F-10 (MINOR) | Revision-table self-contradiction: already fixed by the reviewer; no further change. |
| F-11 (INFO) | System design revision note added pointing at spec D-C1 … D-C5 (system-design `### Revision` table). |
| F-12 (INFO) | `agent_meta_root` made an explicit parameter of `check_orchestrator_strict_hook_support` (and of the two new isolation symbols), with callers named (IC-09, IC-11). |
| Approval | User approval 2026-09-13 — all recommended defaults accepted |

## Problem

In an OpenCode project with `orchestrator.mode: strict`, the CRITICAL GATE
("MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`.") is carried
**only by prompt adherence**. The runtime enforcement that exists for other
providers — the PreToolUse hook `hooks/1-generic/orchestrator-guard.sh` — never
reaches OpenCode, because OpenCode is registered as hook-less:

- `config/provider-capabilities.yaml:59` — `hooks: false`.
- `config/ai-providers.yaml:167` — `has_hooks: false`, and the OpenCode block
  (`:160-224`) declares no `hook_protocol`. `provider_hooks_supported()` returns
  `True` only for `has_hooks: true` **and** a `hook_protocol` in
  `SUPPORTED_HOOK_PROTOCOLS` (`scripts/lib/providers.py:305,308-317`), so no
  hook is mirrored to OpenCode.
- The rules text that promises the gate is unconditional:
  `rules/1-generic/use-orchestrator.md:1-4`, embedded for OpenCode via the
  `context-embedded-rules` capability (`config/ai-providers.yaml:179`).

Two adjacent OpenCode mechanisms do **not** close the gap today:

- **Per-agent permissions** are generated only on generated agent files
  (`scripts/lib/provider_transform.py:467-515`, applied `:583-591`; deny source
  `config/provider-tools.yaml:56-59`). The Main Chat is not a generated agent —
  it has no agent frontmatter — so those per-agent permissions do not govern it.
- **Provider isolation** merges only foreign-provider globs into
  `permission.read` / `permission.edit` (`scripts/lib/isolation.py:237-256`). It
  adds no Main-Chat write deny, and it runs only when at least two providers are
  active (`:54-56`).

The consistency check that is supposed to surface this is a WARNING
(`scripts/lib/consistency/orchestrator_strict.py:50-81`, check ID
`orchestrator-strict.no-hook-support`) and does not distinguish a provider that
is partially enforced from one that is prompt-only.

Consequences observed in issue #794: in a `strict` project the Main Chat edited
files, committed, pushed, tagged and created releases directly, without
delegating to `orchestrator` or `git`. The observed behaviour is an
interaction of a pre-existing provider gap with grown context load, not a
regression of the hook path (design §1). This spec closes the gap in a tiered
way, without treating an unverified provider API as given.

## Ziel

1. **Phase 0 native tightening (A2).** Under effective `strict` mode, sync
   writes a Main-Chat write/bash deny into the project's `opencode.json` through
   the **existing merge path** (`scripts/lib/isolation.py:237-256`), never
   through the create-only settings initializer (this avoids #747). The deny is
   managed and reversible (mode change off `strict` removes it again).
2. **Honest tiered guarantee (A3).** The rendered gate prose states only the
   guarantee the active provider actually carries. Four tiers —
   `hook`, `plugin`, `permission`, `advisory` — are resolved per provider and
   rendered into that provider's own context/rules output, so OpenCode stops
   claiming an unconditional runtime gate.
3. **Tier-driven consistency (A4).** `orchestrator-strict` findings are derived
   from the same tier resolver: `advisory` + strict stays a WARNING (with an
   opt-in ERROR), `permission` becomes an INFO ("partially enforced, no
   provenance"), `hook`/`plugin` produce no finding.
4. **Phase 1 capability-flagged plugin (A1).** A provider-agnostic generator
   deploys a native plugin artifact only when the provider config declares
   `has_plugins: true` with a verified `plugin_protocol`. The plugin starts in
   `observe` mode; `enforce` and the `plugin` tier are unlocked only after the
   P6 real-repo test.
5. **Single source of truth for tier questions.**
   `scripts/lib/providers.py::provider_runtime_gate_tier` is the only place that
   maps config to a tier; rendering, consistency and the plugin gate consume it.
6. **Provider-agnostic and reversible.** Provider differences are expressed
   exclusively through config keys / capability flags — never an
   `if provider == "..."` branch. Unknown/missing configuration fails safe to
   `advisory`; hook-capable providers keep their existing wording semantically
   unchanged; no project is forced into a new root `opencode.json` key.

## Nicht-Ziele

- **No Security boundary.** The gate remains a *Convention boundary*
  (terminology:
  `.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary`).
  A model can disable the plugin, edit `opencode.json`, or fake delegation; this
  spec does not claim otherwise.
- **No change to `hooks.py` or `orchestrator-guard.sh`.** Their verified
  PreToolUse JSON contract and lifecycle are not forked; the plugin is a
  different artifact with a different protocol and lifecycle.
- **No new role, no `role-defaults.yaml` change, no SE cascade.**
- **No generalisation to all providers in this change.** The seam is built
  generic; A2/A1 are implemented for OpenCode only. Generalising to other
  permission-capable providers (OQ-9) is a follow-up.
- **No forced merge/creation of new root keys in `opencode.json`** (that would
  re-open #747); the npm plugin key `"plugin": [...]` in `opencode.json` is
  explicitly not used (design D3).
- **No implementation, no plan, and no spec approval in this document.**
- **No change to the per-agent permission transform** (`provider_transform.py`)
  in Phase 0; it stays the per-agent layer (IC-10).

## Interface Contracts

All new/changed symbols are listed as `file:Symbol`. New modules follow the
repository convention for Python 3.9: `from __future__ import annotations`,
`typing.Optional` / `typing.Dict` / `typing.List` / `typing.Tuple` rather than
PEP 604 unions in new modules, and standard library plus existing repo-local
helpers only (enforced by `scripts/consistency-check.py`). Provider-agnostic is
mandatory: no provider-name literal and no `if provider == "..."` branch in any
new or changed module.

### IC-01 — `config/provider-capabilities.yaml:capabilities.<provider>.runtime_gate` (new key)

New top-level key per provider block inside `capabilities:`, alongside the
existing `hooks`/`commands` booleans (`config/provider-capabilities.yaml:35-...`).

```yaml
runtime_gate: hook | plugin | permission | advisory
```

- Every registered provider carries the key **explicitly** (same obligation as
  `commands`, documented at `config/provider-capabilities.yaml:25-33`). An absent
  key resolves to `advisory` at runtime (fail-safe), but the sync-time
  consistency check and the config invariant test (AC-01) must flag a missing
  key.
- Tier semantics: `hook` = verified PreToolUse hook contract (Claude,
  Gemini/Antigravity); `plugin` = verified native plugin (OpenCode, only after
  P6); `permission` = native permission layer blocks Main-Chat writes without
  delegation provenance (OpenCode, Phase 0); `advisory` = prompt-only (default).
- Phase 0 values: `hook` for the hook-capable providers, `permission` for
  OpenCode, `advisory` for the remainder. Phase 1 flips OpenCode to `plugin`
  only after P6 (AC-21).

### IC-02 — `config/ai-providers.yaml:providers.Opencode` (new keys, Phase 1)

The OpenCode block (`config/ai-providers.yaml:160-224`) gains, values
effective only after P6:

```yaml
has_plugins: true
plugin_dir: .opencode/plugins
plugin_ext: .js
plugin_protocol: opencode-plugin-js
runtime_gate-mechanism: opencode-plugin
```

- `has_plugins` and `plugin_protocol` are the machine truth consumed by
  `provider_runtime_gate_supported` (IC-03) and the sync dispatch (IC-13).
- `runtime_gate-mechanism` is the human-readable label, mirroring
  `isolation-mechanism: opencode-permissions` (`config/ai-providers.yaml:192`).
- **No `hook_protocol` for OpenCode** — it stays hook-less.
- Phase 0 ships **without** these keys (or with `has_plugins` absent/false), so
  the plugin tier is unreachable until Phase 1.

### IC-03 — `scripts/lib/providers.py` (resolver, changed/new)

```python
SUPPORTED_PLUGIN_PROTOCOLS: set = {"opencode-plugin-js"}

def provider_runtime_gate_supported(pc: dict) -> bool:
    """True only when the ai-providers.yaml entry has has_plugins=true AND a
    plugin_protocol in SUPPORTED_PLUGIN_PROTOCOLS. Mirrors
    provider_hooks_supported() (providers.py:308-317)."""

def provider_runtime_gate_tier(pc: dict, capabilities: Optional[dict] = None) -> str:
    """Return 'hook' | 'plugin' | 'permission' | 'advisory'.

    Precedence (first match wins):
      1. provider_hooks_supported(pc)              -> 'hook'
      2. provider_runtime_gate_supported(pc)       -> 'plugin'
      3. (capabilities or {}).get('runtime_gate') == 'permission' -> 'permission'
      4. otherwise                                 -> 'advisory'
    """

def runtime_gate_vars(pc: dict, capabilities: Optional[dict], config: dict) -> dict:
    """Return the per-provider rendering bundle for the resolved gate tier.

    Single source of truth for the GATE_* variables consumed by the
    rules/context renderers. Values are strings so the bundle merges into any
    provider_variables dict unchanged.
    """
```

- `runtime_gate_vars` returns
  `ENFORCEMENT_TIER`, `GATE_ENFORCED`, `GATE_PARTIAL`, `GATE_ADVISORY`,
  `RUNTIME_GATE_PLUGIN_MODE` (definitions in IC-04). It never raises: `config`
  is treated as `{}` when not a mapping, and the tier comes from the fail-safe
  resolver above.
- `all_providers_runtime_gate_supported` is **dropped** (F-09): no
  project-wide guarantee consumer exists in this change. When a project-wide
  gate guarantee is needed, it will mirror
  `all_providers_support_hooks` (`scripts/lib/providers.py:320-333`) rather
  than being carried as an unused code surface.
- `pc` is the `ai-providers.yaml` entry; `capabilities` is the corresponding
  `provider-capabilities.yaml` entry (loadable via the existing
  `scripts/lib/providers.py:120 load_provider_capabilities(agent_meta_root)`).
  This two-registry split is the D-C1 correction; the single-argument design
  form cannot reach the `permission` tier.
- **Error paths / fail-safe:** `pc is None` or not a mapping is treated as `{}`
  → `"advisory"`; `capabilities is None` is treated as `{}` → step 3 is skipped.
  The function never raises, never calls `sys.exit`, and never falls back to a
  Claude/hook truth.
- The declared `runtime_gate` value for `hook`/`plugin` is a declarative
  contract validated by the AC-02 invariant; the runtime tier is derived from
  the machine flags, so an unverified declaration cannot produce a stronger tier
  than the flags support. Only the `permission` value is read at runtime beyond
  the flags.
- `SUPPORTED_PLUGIN_PROTOCOLS` is the plugin analogue of
  `SUPPORTED_HOOK_PROTOCOLS` (`providers.py:305`).

### IC-04 — `scripts/lib/sync_pipeline.py` (changed; tier-var injection seam)

**Correction (F-02):** the tier variables must not be wired through
`agent_sync._build_provider_vars` (`agent_sync.py:423-472`) — that function is
called only by `sync_agents_for_provider` (`agent_sync.py:883`) and neither
`rules.py::_merged_rule_vars` (`rules.py:202-254`) nor
`context.py::_build_managed_block` (`context.py:1096-1119`) consumes it. The
bundle from `providers.runtime_gate_vars(pc, caps, config)` (IC-03) is merged
into the per-provider variable dict at **both** renderer seams:

```python
caps = load_provider_capabilities(agent_meta_root).get(provider, {})
provider_variables.update(runtime_gate_vars(pc, caps, config))   # IC-03
```

- **Context seam:** `_sync_stage_contexts` (`sync_pipeline.py:319-361`) — merge
  before `sync_context_for_provider(...)` (`:359`). `_build_managed_block`
  starts from `local_vars = dict(variables)`, so the injected keys reach the
  embedded `use-orchestrator` block.
- **Rules seam:** `_sync_stage_per_provider` (`sync_pipeline.py:571-756`) —
  merge after `provider_variables` is built (`:623-642`) and before
  `sync_rules(...)` / `sync_embedded_rule_files(...)` (`:675-692`).
  `_merged_rule_vars` returns `{**variables, **provider_vars}`, so injected
  keys survive.
- Variable bundle (produced by `runtime_gate_vars`):
  `ENFORCEMENT_TIER` = tier; `GATE_ENFORCED` = `'true'` iff tier in
  `(hook, plugin)`; `GATE_PARTIAL` = `'true'` iff tier == `permission`;
  `GATE_ADVISORY` = `'true'` iff tier == `advisory`;
  `RUNTIME_GATE_PLUGIN_MODE` = resolved `observe`/`enforce`.
- `rules.py::_merged_rule_vars` and `context.py::_build_managed_block` are
  **verified propagation points, not changed** by this spec.
  `agent_sync._build_provider_vars` stays unchanged (agent generation does not
  need the gate vars).
- `RUNTIME_GATE_PLUGIN_MODE` resolves from `config.get("runtime-gate", {})
  .get("plugin-mode", "observe")`, validated against `{"observe", "enforce"}`
  with fail-safe `observe` (IC-16, AC-24); it is only meaningful when
  `has_plugins` is true. Phase 0 keeps the default `observe` constant.
- **Error path:** unknown provider / `pc == {}` → tier `advisory`, the bundle
  renders the advisory variant, never a missing variable.

### IC-05 — `scripts/lib/variables.py::strip_inactive_conditional_blocks` (changed)

Add `GATE_ENFORCED`, `GATE_PARTIAL`, `GATE_ADVISORY` to the `conditional_vars`
set built at `scripts/lib/variables.py:231-237`. Without this, inactive gate
blocks are not stripped (the default-`"true"` branch in the `replace_if` logic
would keep them). No change to the block-stripping algorithm itself.

### IC-06 — `scripts/lib/consistency/placeholders.py::_BUILTIN_VARS` (changed)

Add `ENFORCEMENT_TIER`, `GATE_ENFORCED`, `GATE_PARTIAL`, `GATE_ADVISORY`,
`RUNTIME_GATE_PLUGIN_MODE` to the built-in variable registry
(`scripts/lib/consistency/placeholders.py:64-109`, feature-flag block around
`:75-90`). Without this, sync emits "missing variable" findings for the new
conditionals.

### IC-07 — rendered rules files (changed)

**`rules/1-generic/use-orchestrator.md`.** Replace the unconditional strict
block (`:1-4`) with three mutually exclusive tier blocks. No provider literal.

```markdown
{{#if GATE_ENFORCED}}
# CRITICAL GATE
MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`. Keine Ausnahmen.
{{/if}}
{{#if GATE_PARTIAL}}
# CRITICAL GATE (runtime-partially enforced)
MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`.
Provider-native Permissions block Main-Chat-Writes; Delegations-Provenienz ist
NICHT erzwungen (Prompt + Permission-Layer).
{{/if}}
{{#if GATE_ADVISORY}}
# CRITICAL GATE (advisory)
MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`.
ACHTUNG: Auf diesem Provider ist der Gate rein prompt-basiert, ohne Runtime-Gate.
{{/if}}
```

- The `GATE_ENFORCED` variant reproduces the current strict wording
  **verbatim** (`rules/1-generic/use-orchestrator.md:1-4`): heading
  `# CRITICAL GATE` and the sentence `MAIN CHAT darf nicht selbst editieren.
  ALLES -> \`orchestrator\`. Keine Ausnahmen.` (F-05). For hook-capable providers
  the rendered strict block is therefore byte-identical; the
  runtime-enforcement provenance is stated by the `a2a-delegation-gates.md`
  tier note (below), not by weakening this sentence.
- The blocks sit inside the existing `{{#if ORCH_MODE_STRICT}}` guard so they
  only render in strict mode.

**`rules/1-generic/a2a-delegation-gates.md`.** Add a tiered note that names
`{{ENFORCEMENT_TIER}}` and points to the existing "Bekannte Grenzen" section
(`:50-55`), so the delegation-gates rule states the active guarantee instead of
implying a full runtime gate.

### IC-08 — `scripts/lib/runtime_gate.py` (new module, Phase 1)

New provider-agnostic generator module; it knows no provider name and maps
`plugin_protocol` to a template via a config key.

```python
PLUGIN_TEMPLATE_BY_PROTOCOL: Dict[str, str] = {
    "opencode-plugin-js": "templates/plugins/runtime-gate.opencode-plugin.js.tmpl",
}
PLUGIN_STEM = "agent-meta-runtime-gate"

def runtime_gate_plugin_relpath(pc: dict) -> Optional[str]:
    """Return plugin_dir/<PLUGIN_STEM> + plugin_ext, or None when
    has_plugins is false / plugin_dir or plugin_ext is missing."""

def sync_runtime_gate_plugins(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    provider_config: Optional[dict] = None,
) -> None:
    """Deploy the native gate artifact only when
    provider_runtime_gate_supported(pc) is true. Same
    always-copy / .agent-meta-managed / never-touch-project-owned pattern as
    hook_plugins.sync_release_gates (scripts/lib/hook_plugins.py:28-98)."""
```

- Templates are read from `agent_meta_root` and written to
  `project_root/<plugin_dir>/<stem><ext>`, tracked by a
  `.agent-meta-managed` index next to it. On rollback (`has_plugins` false or
  unsupported protocol), previously managed files are removed and orphaned
  project-owned files are never touched.
- **Error paths:** unknown `plugin_protocol` → `log.warning` + no write (never
  silent); missing template → warning + skip; `dry_run` never writes; absent
  `plugin_dir`/`plugin_ext` → `runtime_gate_plugin_relpath` returns `None` and
  the function logs and returns.
- `RUNTIME_GATE_PLUGIN_MODE` (`observe` default, `enforce` opt-in) is baked into
  the generated artifact at sync time from IC-04's resolved value.

### IC-09 — `scripts/lib/isolation.py` (changed, A2)

```python
_STATE_ISOLATION_KEY = "isolation-deny"        # existing namespace (list[str])
_STATE_RUNTIME_GATE_KEY = "runtime-gate-deny"  # new namespace (dict[str, dict])

def _read_state(state_path: Path, key: str = _STATE_ISOLATION_KEY):
    """Read ONE namespaced managed record from the shared state file; a missing
    or unparseable file yields the empty value for that namespace."""

def _write_state(state_path: Path, value, dry_run: bool,
                 key: str = _STATE_ISOLATION_KEY) -> None:
    """Read-modify-write the state file, replacing ONLY `key` and preserving
    every other namespace. (Changed from whole-record overwrite.)"""

def _permission_mapping(value) -> Dict[str, str]:
    """Normalise a permission family to a glob->decision mapping: a dict passes
    through; a scalar string becomes {'**': value}; anything else {}."""

def _opencode_runtime_gate_entries(
    config: dict, provider: str, agent_meta_root: Path, provider_config: dict,
) -> Dict[str, Dict[str, str]]:
    """Return the Main-Chat deny entries in MAPPING form, e.g.
    {'edit': {'**': 'deny'}, 'bash': {'**': 'deny'}}, only when the provider's
    resolved tier is 'permission'; {} otherwise. No provider literal."""

def _sync_opencode_runtime_gate(
    project_root: Path, config: dict, provider: str,
    provider_config: dict, agent_meta_root: Path, log: SyncLog, dry_run: bool,
) -> None:
    """Merge the gate entries into the EXISTING opencode.json via the managed
    path (isolation.py:225-256 + _OPENCODE_STATE_FILE at :31), including
    ownership/rollback on a strict -> advisory transition."""
```

- **Concrete merge shape (F-01).** A2 **never writes a scalar** at
  `permission.edit` / `permission.bash`. It adds exactly one deny glob key
  `"**"` **inside each family mapping**, e.g.
  `"edit": {"**": "deny"}` and `"bash": {"**": "deny"}`. Those glob keys are
  **disjoint from every key the isolation writer manages**
  (`_dir_to_glob` output such as `**/.claude/**`, `**/opencode.json`), so the
  two writers never collide. The `"**"` glob follows the existing glob
  convention of `isolation.py::_dir_to_glob`.
- **Scalar tolerance (D-C4, still required).** Both
  `_sync_opencode_isolation` and `_sync_opencode_runtime_gate` must normalise a
  family through `_permission_mapping` before `.items()`; the current
  `isolation.py:237-241` calls `.items()` unconditionally and would raise on a
  scalar string. The isolation writer therefore changes from
  `permission.get("read", {}).items()` to
  `_permission_mapping(permission.get("read")).items()` (same for `edit`).
- **Ownership / rollback contract.** Before setting `"**": "deny"`, A2 reads
  the pre-existing decision at that key (`mapping.get("**")`, `None` when
  absent) and records it in the state namespace:
  `"runtime-gate-deny": {"**": {"edit": <prior|null>, "bash": <prior|null>}}`.
  On a strict → non-strict transition, A2 removes `"**"` **only when** its
  current value is the managed `"deny"`, then restores the prior value (or
  deletes the key when the prior was `null`); no other key is touched. The
  namespace is removed when empty. A pre-existing **user** value at `"**"` is
  thus never lost (AC-10).
- **Writer ordering (F-01).** `_sync_opencode_runtime_gate` runs in stage 6
  (`_sync_stage_per_provider`, IC-13); `_sync_opencode_isolation` runs later in
  stages 8+9 (`sync_pipeline.py:807`). Both are read-modify-write on the same
  `opencode.json`. Because A2's `"**"` glob key is disjoint from isolation's
  keys and because `_write_state` now preserves sibling namespaces, the later
  isolation writer preserves A2's entries (and its state) and vice versa. The
  only ordering obligation is that each writer re-reads both the JSON and the
  state file immediately before writing; there is no cross-writer lock.
- **Trigger (D-C3 + F-07).** Dispatched from the per-provider sync stage
  (IC-13) when the provider's resolved tier is `permission`
  (`provider_runtime_gate_tier(pc, caps) == "permission"` — IC-01/IC-03),
  **not** keyed off `isolation-mechanism`, and **not** from
  `sync_provider_isolation`, whose `len(providers) >= 2` guard
  (`isolation.py:54-56`) would skip a single-provider OpenCode project.
- **Non-#747 write path:** the helper reads and rewrites `opencode.json`
  through `_read_json_safe` / `write_checked` (`isolation.py:225-256`), never
  through `context.py::_init_provider_settings_json` (`context.py:838-880`,
  which renders only when the file is absent, `:852-855`).
- **Error paths:** absent `opencode.json` → created with only the managed
  permission block; present and parseable → merged in place; present but
  unparseable → skip with a warning (data-loss guard, mirrors `:232-234`);
  unparseable state → treated as empty with a warning; `dry_run` never writes.
- Effective-strict resolution reuses the same three-tier precedence as
  `orchestrator_strict._resolve_effective_strict` (`:24-47`) so mode handling
  stays consistent.
- `agent_meta_root` is an explicit parameter (F-12) because tier resolution
  loads the capabilities registry via
  `load_provider_capabilities(agent_meta_root)`.

### IC-10 — `scripts/lib/provider_transform.py` (explicit non-change)

`_map_claude_tools_to_opencode_permissions` (`:467-515`) and its application
(`:583-591`) are **not changed**. Reason: those permissions are generated only
for agent files, and the Main Chat has no agent frontmatter, so this layer
cannot carry the Main-Chat deny. This contract records the non-change explicitly
so a future reader does not try to close the gap here. The deny source stays
`config/provider-tools.yaml:56-59` (`opencode_deny_critical`).

### IC-11 — `scripts/lib/consistency/orchestrator_strict.py` (changed, A4)

`check_orchestrator_strict_hook_support` (`:50-81`) is re-pointed from
`provider_hooks_supported` to `provider_runtime_gate_tier(pc, caps)`:

- tier `advisory` + effective strict → WARNING by default, ERROR when
  `orchestrator.require-runtime-gate` is `true` (IC-12), with a message that
  states prompt-only enforcement.
- tier `permission` → INFO finding: "partially enforced; delegation provenance
  not enforced".
- tier `hook` / `plugin` → no finding.
- The effective-strict resolution (`:24-47`) and the finding check ID
  (`orchestrator-strict.no-hook-support`) are preserved; the existing malformed-
  input guards (`:32-47`) stay.
- The function signature gains an explicit `agent_meta_root: Path` parameter
  (F-12): `check_orchestrator_strict_hook_support(project_root: Path,
  config: dict, provider_config: dict, agent_meta_root: Path)`. It loads the
  capabilities registry via `load_provider_capabilities(agent_meta_root)`
  (`providers.py:120`); the caller `scripts/consistency-check.py:266-267` is
  updated to pass the already-known `agent_meta_root`. `project_root` stays for
  finding paths only. **Error path:** an unreadable registry degrades to
  `advisory` (fail-safe, never a crash).

### IC-12 — `config/project-config.schema.json:orchestrator` (new key)

Add a **sibling** key to the `orchestrator` block
(`config/project-config.schema.json:2073-...`):

```json
"require-runtime-gate": {
  "type": "boolean",
  "default": false,
  "description": "When true, the orchestrator-strict consistency check treats a provider that is only prompt-enforced (tier 'advisory') as an ERROR instead of a WARNING. Default: false (backwards compatible)."
}
```

- Sibling rather than nested (D-C2) because `orchestrator.strict` is a
  `boolean` (`:2092-2096`); nesting under it would be a breaking schema change.
  The hyphenated key matches the existing convention
  (`direct-dispatch-enabled`, `native-extensions`).
- The `orchestrator` block keeps its `additionalProperties` policy; the new key
  is closed and typed. The runtime resolution is defensive even without schema
  validation (missing → `false`).

### IC-13 — sync dispatch (changed)

**`scripts/lib/sync_pipeline.py`.** In `_sync_stage_per_provider`
(`:571-756`):

- After the existing hook branch (`:733-746`), dispatch the two new writers
  independent of it:
  `if pc.get("has_plugins", False): sync_runtime_gate_plugins(...)` (IC-08) and
  `_sync_opencode_runtime_gate(...)` (IC-09) whenever the resolved tier is
  `permission`
  (`provider_runtime_gate_tier(pc, caps) == "permission"` — IC-01/IC-03),
  using the effective-mode resolution. The A2 dispatch is **not** nested under
  `has_hooks` and **not** inside `sync_provider_isolation`. (F-07: the concrete
  gate is the IC-01 capability `runtime_gate` via the IC-03 resolver, never the
  `isolation-mechanism` key, which is a cross-provider-isolation concern and not
  a gate-capability proxy.)
- The dispatch must remain provider-agnostic: it keys off the config capability
  `has_plugins` and the resolver output `permission`, never a provider literal.

**`scripts/lib/cli_commands.py`.** Mirror the same dispatch in the test-repo
sync path (near `:241-248`) so `--test`-generated repos match a normal sync.

### IC-14 — `scripts/lib/generated_file_drift.py::_iter_managed_files` (changed)

Add a `dir_specs` entry for `pc.get("plugin_dir")`, gated on
`pc.get("has_plugins", False)` (`scripts/lib/generated_file_drift.py:117-141`).
Without it, generated plugin artifacts are not drift-tracked.

### IC-15 — `templates/plugins/runtime-gate.opencode-plugin.js.tmpl` (new, Phase 1)

Template contract only — no implementation in this spec. The generated artifact
is an exported OpenCode plugin with sync-time-baked constants:

```js
// exported plugin; sync-time-baked constants: STRICT, MODE, AGENT_ALLOWLIST
export const AgentMetaRuntimeGate = async (ctx) => ({
  "tool.execute.before": async (input, output) => {
    // input.tool in {write, edit, bash, ...}; output.args
    // when STRICT && MODE === "enforce" && !isDelegated(input): throw
  },
});
```

- `MODE` defaults to `observe` (log/report only). `enforce` is unlocked only by
  config after P6 (AC-19, AC-21).
- `AGENT_ALLOWLIST` is baked at sync time so the orchestrator/git subagents are
  not blocked; it is a list, not a provider literal.
- The artifact is written to `.opencode/plugins/` (project plugin directory,
  auto-loaded by OpenCode; verified against the OpenCode plugin docs on
  2026-09-13, design AN-1). This path needs no `opencode.json` root key and
  therefore avoids #747 constructively. `.opencode/package.json:3` already
  lists `@opencode-ai/plugin`, so no new dependency is introduced.

### IC-16 — `config/project-config.schema.json:runtime-gate` (new root key, Phase 1)

Typed schema entry for the plugin mode (F-08), added to the root `properties`
alongside `orchestrator` / `analysis`:

```json
"runtime-gate": {
  "type": "object",
  "properties": {
    "plugin-mode": {
      "type": "string",
      "enum": ["observe", "enforce"],
      "default": "observe",
      "description": "Baked into the generated native gate plugin at sync time. 'observe' logs only; 'enforce' is unlocked only after the P6 real-repo verification (AC-21). Default: observe."
    }
  },
  "additionalProperties": false
}
```

- IC-04 resolves `RUNTIME_GATE_PLUGIN_MODE` from
  `config.get("runtime-gate", {}).get("plugin-mode", "observe")`; without this
  IC the root key would be silently accepted (`additionalProperties: true` at
  the root, `project-config.schema.json:2297`) and could carry an invalid value.
- Fail-safe: a missing key or an out-of-enum value falls back to `observe`
  (never `enforce`). Phase 0 may ship the schema key with the `observe`
  resolution only; the plugin artifact is Phase 1 (AC-16 … AC-22).

## Datenfluss

### 1. Tier resolution (single algorithm)

```
provider-capabilities.yaml[provider].runtime_gate  ─┐
ai-providers.yaml[provider].has_hooks/hook_protocol ─┼─> provider_runtime_gate_tier(pc, caps)
ai-providers.yaml[provider].has_plugins/plugin_protocol ─┘        │
                                                                  ▼
                        hook | plugin | permission | advisory
                                                                  │
        ┌───────────────────────────────┬─────────────────────────┼───────────────────────┐
        ▼                               ▼                         ▼                       ▼
 rendering (IC-04/07)          consistency (IC-11)          A2 entries (IC-09)    plugin gen (IC-08)
 GATE_ENFORCED/PARTIAL/        INFO/WARNING/ERROR           deny only when         deploy only when
 ADVISORY                                                  tier == permission     status supported
```

- Precedence is fixed (IC-03): `hook` > `plugin` > `permission` > `advisory`.
- Fail-safe: unknown provider, missing/`None` `pc`, absent `runtime_gate`,
  unreadable registry → `advisory`. No path silently strengthens the guarantee.
- `advisory` never writes a permission entry and never deploys a plugin.

### 2. Phase 0 flow (A2 + A3 + A4) — no #747, no new runtime API

```
project.yaml[orchestrator.mode=strict]
    │
    ├─> config.build_variables() ─> config._build_orch_variables()  [ORCH_MODE_*]
    │
    ├─> sync_pipeline._sync_stage_contexts(provider)
    │       ├─ provider_runtime_gate_tier(pc, caps) ─> providers.runtime_gate_vars()  [IC-03]
    │       │    └─ provider_variables.update(GATE_* vars)                            [IC-04]
    │       └─> sync_context_for_provider(...) ─> context._build_managed_block()
    │            └─ AGENTS.md / CLAUDE.md (provider-correct promise)
    │
    └─> sync_pipeline._sync_stage_per_provider(provider)
            ├─ provider_runtime_gate_tier(pc, caps) ─> providers.runtime_gate_vars() [IC-03]
            │    └─ provider_variables.update(GATE_* vars)                           [IC-04]
            ├─> sync_rules / sync_embedded_rule_files ─> rules._merged_rule_vars()
            │    └─ rules/1-generic/use-orchestrator.md (staged block)
            │
            ├─> isolation._sync_opencode_runtime_gate(...)
            │    └─ merge mapping-form deny glob ('**') into permission.edit/bash
            │       of the EXISTING opencode.json via isolation.py:225-256
            │       #747-avoidance: context._init_provider_settings_json is NOT used
            │
            └─> consistency-check.py -> orchestrator_strict.py
                    └─ tier-based INFO/WARNING/ERROR
```

**Tier-var propagation (F-02).** `runtime_gate_vars()` is injected at both
renderer seams inside `sync_pipeline.py` (IC-04). `rules.py::_merged_rule_vars`
returns `{**variables, **provider_vars}` and `context.py::_build_managed_block`
starts from `local_vars = dict(variables)`, so the injected keys reach both the
rule files and the embedded context block unchanged.

**#747 avoidance (A2).** A2 does not write through
`context._init_provider_settings_json` (`context.py:838-880`), which renders only
when the settings file is absent (`:852-855`) and would therefore create a
competing root key path. A2 reads and rewrites the existing `opencode.json`
through `isolation.py`'s merge path: an existing `permission` block is preserved,
a missing one is created, and only the managed entries are rewritten. Managed
state (`.opencode/agent-meta-state.json`) makes the change reversible.

### 3. Phase 1 flow (A1) — plugin behind a capability flag

```
ai-providers.yaml[has_plugins=true, plugin_protocol]
    │
    ├─ provider_capabilities[provider].runtime_gate
    │
    └─> sync_pipeline: if pc.get("has_plugins")
            └─> runtime_gate.sync_runtime_gate_plugins(...)
                    │   (only when provider_runtime_gate_supported(pc))
                    ├─ template: templates/plugins/runtime-gate.opencode-plugin.js.tmpl
                    │    sync-time baked: STRICT, MODE, AGENT_ALLOWLIST
                    └─> .opencode/plugins/agent-meta-runtime-gate.js
                         + .agent-meta-managed index
                              │
                              ▼
                   OpenCode startup: local plugin auto-load
                              │
                              ▼
                   tool.execute.before(input, output)
                              │
                     STRICT && MODE=enforce && !isDelegated?
                              ├─ yes -> throw -> tool blocked
                              └─ no  -> tool runs
```

**#747 avoidance (Phase 1).** The local plugin directory is auto-loaded; the
npm route (`"plugin": [...]` in `opencode.json`) would require a new root key and
is deliberately not used (design D3).

**P6 dependency (F-03).** The generator, managed state, drift tracking and
observe-mode artifact (AC-16 … AC-20, AC-22) are implementable **before** P6, as
the design requires observe-before-P6 (design §6.2, D8). Until the real-repo
test confirms that `tool.execute.before` fires for subagent sessions and that
the Main Chat is distinguishable in `input` (design AN-3/AN-4/AN-5), the plugin
runs with `MODE=observe` and the provider stays at tier `permission`. Only the
tier flip to `plugin`, the `MODE=enforce` opt-in and the P6 verification
(AC-21) are gated.

### 4. Hook-less / plugin-less fallback

- Provider without hooks and without plugins, strict active, but declared
  `capacity`/`runtime_gate` = `advisory` → no permission entries, no plugin,
  advisory prose. (This is today's OpenCode behaviour, now honestly labelled.)
- Provider with `runtime_gate: permission` (OpenCode Phase 0) → A2 permission
  deny, partial prose; plugin writer is a no-op.
- Provider with `has_plugins: true` but an unsupported/unknown `plugin_protocol`
  → `provider_runtime_gate_supported` is `False`, the plugin writer logs a
  warning and writes nothing, and the tier resolves no higher than `permission`
  (or `advisory` if not declared `permission`).
- Project that turns strict off → `_opencode_runtime_gate_entries` returns `{}`
  and the managed-state cleanup removes the previously written deny entries.

## Acceptance Criteria

Each criterion is independently testable and observable. "Resolver" means
`scripts/lib/providers.py::provider_runtime_gate_tier`. Test locations name the
files to add or extend.

### Phase 0 — implementable now

1. **AC-01 (explicit tier per provider).** Given all registered providers in
   `config/provider-capabilities.yaml`, when the registry is read, then every
   provider carries an explicit `runtime_gate` in
   `{hook, plugin, permission, advisory}`. Test: extend
   `tests/test_provider_agnostic_dispatch.py` with a param test analogous to
   `test_every_provider_has_explicit_commands_capability`.
2. **AC-02 (declared tier matches machine flags).** Given the two registries,
   when cross-checked, then for every provider `runtime_gate == "hook"` iff
   `provider_hooks_supported(pc)` is `True`; `runtime_gate == "plugin"` iff
   `provider_runtime_gate_supported(pc)` is `True` **and not**
   `provider_hooks_supported(pc)` (F-06: hook precedence wins, so a
   hook-and-plugin provider is `hook`); and every other provider is
   `permission` or `advisory`. Test: extend
   `tests/test_provider_agnostic_dispatch.py` (or add
   `tests/test_runtime_gate_config.py`).
3. **AC-03 (tier resolver semantics and fail-safe).** Given representative
   configurations, when the resolver runs, then it returns `hook` for a
   hook-supported entry, `plugin` for a plugin-supported entry, `permission` for
   an entry whose `capabilities.runtime_gate == "permission"`, and `advisory`
   otherwise; and `provider_runtime_gate_tier(None)` and
   `provider_runtime_gate_tier({}, None)` both return `advisory` without
   raising. Test: new `tests/test_runtime_gate_config.py`.
4. **AC-04 (provider-agnostic).** Given the new and changed modules, when the
   AST scan runs, then no module contains a provider-name literal equality
   branch; `runtime_gate` and `isolation` are added to
   `tests/test_provider_agnostic_dispatch.py::_TOUCHED_MODULES`. Test: extend
   that file.
5. **AC-05 (staged rendering).** Given a strict project, when a hook-tier
   provider renders, then `use-orchestrator` contains the `GATE_ENFORCED`
   variant and its strict block is **byte-identical** to the current
   `rules/1-generic/use-orchestrator.md:1-4` text (heading `# CRITICAL GATE`
   and the sentence ending `Keine Ausnahmen.`); when a `permission` provider
   (OpenCode Phase 0) renders, then it contains the `GATE_PARTIAL` variant and
   does **not** contain the unconditional runtime claim; when an `advisory`
   provider renders, then it contains the `GATE_ADVISORY` variant. Test: new
   `tests/test_runtime_gate_rendering.py` (extend
   `tests/test_rule_variables.py` for the conditional wiring).
6. **AC-06 (conditional stripping).** Given the three `GATE_*` variables,
   when `strip_inactive_conditional_blocks` processes a template, then an
   inactive gate block is removed and an active one survives. Test: extend
   `tests/test_rule_variables.py` or `tests/test_config_variable_fallbacks.py`.
7. **AC-07 (no missing-variable findings).** Given a sync with the new
   variables, when `consistency/placeholders.py` runs, then none of
   `ENFORCEMENT_TIER` / `GATE_ENFORCED` / `GATE_PARTIAL` / `GATE_ADVISORY` /
   `RUNTIME_GATE_PLUGIN_MODE` produces a "missing variable" finding. Test:
   extend the placeholder consistency test module (or add
   `tests/test_runtime_gate_config.py` case).
8. **AC-08 (A2 permission deny written under strict).** Given an OpenCode
   project with `orchestrator.mode: strict`, when sync runs, then
   `opencode.json` contains the managed Main-Chat deny **in mapping form** —
   `permission.edit` and `permission.bash` each carry the managed glob key
   `"**"` with decision `"deny"` — and the runtime-gate state namespace
   `runtime-gate-deny` records the pre-existing value at that key; given a
   non-strict mode, when sync runs, then the managed `"**"` key is removed (or
   restored to its prior user value) and any previously managed entry is gone.
   Test: new `tests/test_opencode_runtime_gate.py`.
9. **AC-09 (A2 works for a single active provider).** Given an OpenCode-only
   project (`len(providers) == 1`) with strict mode, when sync runs, then the A2
   deny entries are written, proving the dispatch is not gated by the
   `sync_provider_isolation` ≥2-provider guard. Test: new
   `tests/test_opencode_runtime_gate.py`.
10. **AC-10 (A2 preserves user entries, ownership and #747-avoidance).** Given
    an existing `opencode.json` with a user `permission` block, a user
    `permission.edit` mapping (e.g. `{"src/**": "ask"}`) **and** a pre-existing
    user value at the managed glob `"**"` (e.g. `"deny"`), when sync runs under
    strict, then every user glob other than `"**"` survives unchanged, the
    managed `"**"` deny is present, the prior value at `"**"` is recorded in
    the `runtime-gate-deny` state namespace, and
    `context._init_provider_settings_json` is not the write path (an existing
    file is merged in place). When a later sync leaves strict mode, the managed
    `"**"` is removed and the prior user value at `"**"` is restored — no user
    value is lost. A user `permission.edit`/`permission.bash` that is a scalar
    string is normalised to `{"**": <value>}` by `_permission_mapping` and
    survives. Test: new `tests/test_opencode_runtime_gate.py`.
11. **AC-11 (A2 idempotent and reversible).** Given a strict sync run twice,
    when both outputs are compared, then `opencode.json` is byte-identical and
    the `runtime-gate-deny` state namespace lists exactly the A2-owned glob
    entry; given a subsequent advisory sync, then the managed glob entry is
    removed (prior value restored) and non-managed entries are untouched. Test:
    new `tests/test_opencode_runtime_gate.py`.
12. **AC-12 (A4 severity by tier).** Given a strict project, when the
    consistency check runs, then a `permission`-tier provider yields an INFO
    finding stating partial enforcement, an `advisory`-tier provider yields a
    WARNING by default and an ERROR when `orchestrator.require-runtime-gate` is
    `true`, and `hook`/`plugin` providers yield no finding. Test: extend
    `tests/test_orchestrator_strict_visibility.py`.
13. **AC-13 (existing strict-visibility expectations updated).** Given the
    existing Opencode-focused cases in
    `tests/test_orchestrator_strict_visibility.py`
    (`test_warns_for_active_provider_without_hook_support`,
    `test_provider_override_turns_strict_on_despite_global_off`,
    `test_global_mode_key_triggers_warning_without_legacy_booleans`,
    `test_malformed_provider_overrides_null_does_not_crash`,
    `test_malformed_provider_override_null_entry_does_not_crash`,
    `test_gemini_and_opencode_active_warning_only_for_opencode`), when the
    suite runs, then Opencode assertions reflect the new `permission` tier (INFO,
    not WARNING) and all Mammouth/Claude/Gemini cases are unchanged. Test:
    `tests/test_orchestrator_strict_visibility.py`.
14. **AC-14 (schema key).** Given the shipped
    `config/project-config.schema.json`, when `orchestrator.require-runtime-gate`
    is present and boolean, then it is accepted; when it is a non-boolean or an
    unknown sibling, then validation rejects it; absence resolves to `false`.
    Test: new `tests/test_runtime_gate_config.py` (schema cases), following the
    `tests/test_subagent_permissions_schema.py` pattern.
15. **AC-15 (back-compat and green suite).** Given no new `opencode.json` root
    key and no hook changes, when the full test suite runs, then Claude/Gemini
    rendered strict output is **byte-identical** (IC-07 `GATE_ENFORCED`
    reproduces the current wording verbatim, F-05), the OpenCode default
    (no `runtime_gate` configured) resolves to `advisory`, and no existing test
    regresses except the intentional updates in AC-13. Test: full suite.
23. **AC-23 (isolation + A2 coexist in a multi-provider project).** *(Phase 0;
    ID continues the sequence to avoid renumbering the Phase-1 criteria.)*
    Given a strict project with two active providers — one whose tier is
    `permission` and one foreign provider with `isolation-dirs` — when sync
    runs (`_sync_opencode_runtime_gate` in stage 6, then
    `_sync_opencode_isolation` in stages 8+9, `sync_pipeline.py:807`), then
    `opencode.json` contains **both** the A2 `"**"` deny globs in
    `permission.edit`/`permission.bash` **and** the isolation foreign-dir globs
    in `permission.read`/`permission.edit`; the two state namespaces
    `runtime-gate-deny` and `isolation-deny` each survive the other writer; and
    a second sync is byte-identical. Test: new
    `tests/test_opencode_runtime_gate.py`.

### Phase 1 — plugin generator

> AC-16 … AC-20 and AC-22 are implementable now in `MODE=observe`; only the tier
> flip, the `MODE=enforce` opt-in and AC-21 are gated behind the P6 real-repo
> verification task.

16. **AC-16 (plugin generation gated on the verified capability).** Given
    `has_plugins: true` with a supported `plugin_protocol`, when sync runs, then
    `.opencode/plugins/agent-meta-runtime-gate.js` is written and recorded in
    the `.agent-meta-managed` index; given `has_plugins` absent/false, then no
    plugin file is written. Test: new `tests/test_runtime_gate_plugins.py`.
17. **AC-17 (plugin rollback).** Given a project that was generated with the
    plugin and then flips `has_plugins` to `false`, when sync runs, then the
    previously managed plugin file is removed and project-owned files in the
    plugin directory are untouched. Test: new
    `tests/test_runtime_gate_plugins.py`.
18. **AC-18 (unknown protocol / missing template).** Given `plugin_protocol`
    unknown to `SUPPORTED_PLUGIN_PROTOCOLS` or a missing template, when the
    plugin writer runs, then it logs a warning and writes nothing (never silent,
    never a crash). Test: new `tests/test_runtime_gate_plugins.py`.
19. **AC-19 (observe by default).** Given the plugin generation runs, when the
    artifact is inspected, then `MODE` is `observe` unless the project
    explicitly opts into `enforce`, and `RUNTIME_GATE_PLUGIN_MODE` is the baked
    value in the provider vars. Test: new
    `tests/test_runtime_gate_plugins.py`.
20. **AC-20 (drift tracking).** Given a generated plugin file, when
    `generated_file_drift` scans, then the artifact is iterated via the
    `plugin_dir` `dir_spec` gated on `has_plugins` and reported when modified or
    orphaned. Test: extend `tests/test_generated_file_drift.py`.
21. **AC-21 (P6 gate before the tier flip).** Given the P6 real-repo
    verification task, when it is executed, then it records whether
    `tool.execute.before` fires in OpenCode subagent sessions and whether the
    Main Chat is distinguishable in `input`; the provider may be flipped to
    `runtime_gate: plugin` + `has_plugins: true` + `MODE=enforce` only when both
    are confirmed. This is a documented manual/real-repo task (not unit-testable)
    and is proven by scenario `62-opencode-runtime-gate` plus its registry entry
    and assert script. Test: `tests/scenarios/registry.md` entry, new
    `tests/scenarios/configs/62-opencode-runtime-gate.project.yaml`, new
    `tests/scenarios/asserts/62-opencode-runtime-gate.sh`.
22. **AC-22 (tier fallback without a plugin runtime).** Given a provider with
    `has_plugins: false` (or a plugin whose runtime is not confirmed), when tier
    and rendering resolve, then the tier is no higher than `permission` (or
    `advisory`) and no plugin artifact is deployed; a project with
    `runtime_gate: advisory` never receives a permission deny or a plugin.
    Test: extend `tests/test_runtime_gate_config.py` and
    `tests/test_runtime_gate_rendering.py`.
24. **AC-24 (plugin-mode schema key).** Given the shipped
    `config/project-config.schema.json`, when `runtime-gate.plugin-mode` is
    present and one of `{"observe", "enforce"}`, then it is accepted; when it is
    a non-string or an out-of-enum value, then validation rejects it; a missing
    key resolves to `observe`; and an unknown sibling under `runtime-gate` is
    rejected (`additionalProperties: false`, IC-16). Test: extend
    `tests/test_runtime_gate_config.py` (schema cases), following the
    `tests/test_subagent_permissions_schema.py` pattern.

## Offene Fragen + Risiken

The design's OQ-1 … OQ-10 are carried over unchanged in substance; each has a
recommended default. Items marked **[User approval]** need an explicit user
decision because they affect the shipped guarantee or a public contract.

1. **OQ-1 — does `tool.execute.before` fire for OpenCode subagent sessions?**
   Recommended default: treat as unverified; the P6 test is a mandatory gate
   before any Phase-1 flip (AC-21). **[User approval]** for the go/no-go on
   Phase 1.
2. **OQ-2 — is the Main Chat distinguishable in `input` (e.g. `input.agent` /
   `sessionID`) from a dispatched subagent?** Recommended default: assume not;
   the plugin starts and may stay in `observe`. **[User approval]** together with
   OQ-1.
3. **OQ-3 — does agent frontmatter permission override the root deny for
   `orchestrator`/`git`?** Recommended default: assume yes, but verify in P6;
   otherwise narrow A2 to finer globs for `bash`/`edit`. **[User approval]**
   because A2 could otherwise block the orchestrator itself.
4. **OQ-4 — does `deriveSubagentSessionPermission` propagate the root deny into
   child sessions (#765)?** Recommended default: assume the risk and never label
   A2 "fully enforced"; tier `permission` is PARTIAL (design §7.1). **[User
   approval]** only if the project wants to rely on propagation.
5. **OQ-5 — default severity for A4: WARNING or ERROR?** Recommended default:
   WARNING; ERROR only with `orchestrator.require-runtime-gate: true` (IC-12,
   AC-12). No user approval needed; the opt-in is the escape hatch.
6. **OQ-6 — A2 globally or only under `mode: strict`?** Recommended default:
   only when `orchestrator.strict` is effectively active for the provider, with
   `provider-overrides` narrowing (IC-09). No user approval needed.
7. **OQ-7 — plugin language `.js` or `.ts`?** Recommended default: `.js` (no TS
   toolchain requirement; the OpenCode docs allow both). No user approval.
8. **OQ-8 — commit or gitignore the generated plugin?** Recommended default:
   commit it, managed and drift-tracked, for recoverability. No user approval.
9. **OQ-9 — generalise A2/A3 to other permission-capable providers
   (ZCode/KimiCode)?** Recommended default: build the seam generic, implement
   only OpenCode in this change. **[User approval]** if a broader rollout is
   wanted; otherwise a follow-up.
10. **OQ-10 — final wording of the PARTIAL/ADVISORY prose?** Recommended
    default: review by `concept-reviewer`; the wording is a spec detail (IC-07).
    **[User approval]** implicitly via the spec approval.
11. **OQ-11 (resolved, from D-C4 + F-01) — shared ownership in
    `opencode.json`.** Both the isolation writer and the A2 writer touch
    `permission.read` / `permission.edit`. **Resolution (no longer open):** keep
    the single state file `.opencode/agent-meta-state.json`, but generalise
    `_read_state`/`_write_state` to **namespaced keys** written with
    read-modify-write so neither writer clobbers the other:
    `isolation-deny` (existing, `list[str]`) and `runtime-gate-deny` (new,
    `dict`, storing the managed glob and its prior value). The two writers are
    additionally collision-free at the JSON level because A2 writes only the
    glob key `"**"` in `permission.edit`/`permission.bash`, disjoint from every
    `_dir_to_glob` key isolation writes. No state-schema bump is needed beyond
    the additional namespace; the exact namespace names are fixed by IC-09, and
    the user-value rollback is contract-tested by AC-10/AC-11/AC-23. No user
    approval needed.
12. **Rules-text churn across all projects (risk).** Changing
    `rules/1-generic/use-orchestrator.md` re-renders `AGENTS.md`/`CLAUDE.md` in
    every project; `--check`/drift hashes must be updated deliberately. The
    `GATE_ENFORCED` wording is kept semantically identical for hook providers to
    limit the visible change (AC-15). Open: whether the hash refresh is part of
    the same change or a follow-up sync.
13. **`runtime_gate: permission` without a verified #765 propagation (risk).**
    A2 may not protect child sessions; the tier is deliberately named
    `permission` (partial), not `hook`/`plugin`. If P6 finds propagation broken,
    the recommended fallback is to keep the PARTIAL label and not strengthen it
    (OQ-4).
14. **Missing `runtime_gate` on a new provider (risk, low).** Fail-safe is
    `advisory`, so a newly registered provider can never silently appear
    stronger than it is; AC-01 turns the omission into a test failure.

## Trace-Anker

```
spec-id: SPEC-OPENCODE-RUNTIME-GATE-2026-09-13
```

- The plan for this spec references this value via its `**Spec:**` field. A plan
  is authored separately and is out of scope for this document.
- Source design: `docs/specs/2026-09-13-opencode-runtime-gate-system-design.md`
  — same anchor, adopted unchanged. This spec keeps the design's phasing
  (Phase 0 = A2+A3+A4, Phase 1 = A1 behind the capability flag) and its seam
  decision (new `scripts/lib/runtime_gate.py`).
- Interface-contract to acceptance-criteria mapping:

  | Interface contract | Acceptance criteria |
  |---|---|
  | IC-01 (`runtime_gate` capability key) | AC-01, AC-02, AC-03 |
  | IC-02 (Opencode plugin keys) | AC-16, AC-19, AC-22 |
  | IC-03 (`providers.py` tier resolver + `runtime_gate_vars`) | AC-02, AC-03, AC-04, AC-12, AC-22 |
  | IC-04 (`sync_pipeline.py` tier-var injection seam) | AC-05, AC-15, AC-19 |
  | IC-05 (`conditional_vars`) | AC-06, AC-15 |
  | IC-06 (`_BUILTIN_VARS`) | AC-07, AC-15 |
  | IC-07 (rendered rules files) | AC-05, AC-06, AC-15, AC-22 |
  | IC-08 (`runtime_gate.py`) | AC-16, AC-17, AC-18, AC-19 |
  | IC-09 (`isolation.py` A2 merge) | AC-08, AC-09, AC-10, AC-11, AC-23 |
  | IC-10 (`provider_transform.py` non-change) | AC-15 |
  | IC-11 (`orchestrator_strict.py` tier finding) | AC-12, AC-13 |
  | IC-12 (`orchestrator.require-runtime-gate` schema) | AC-12, AC-14 |
  | IC-13 (sync dispatch) | AC-08, AC-09, AC-16, AC-23 |
  | IC-14 (`generated_file_drift.py`) | AC-20 |
  | IC-15 (plugin template contract) | AC-16, AC-18, AC-19, AC-21, AC-22 |
  | IC-16 (`runtime-gate.plugin-mode` schema) | AC-24 |

- Binding frame: `scripts/lib/hooks.py` and `scripts/lib/hook_plugins.py`
  (verified PreToolUse/managed-index patterns), `scripts/lib/providers.py:305-333`
  (tier-A hook gate precedent), `scripts/lib/isolation.py:209-256` (existing
  `opencode.json` merge + managed-state precedent), `scripts/lib/context.py:838-880`
  (the #747 create-only path that A2 must not use).
