# Changelog

## [Unreleased]

### Added
- **Strict-first orchestrator mode from a single resolver (D1b, #1006)**: the effective mode now
  resolves in exactly one place, `variables._resolve_orch_mode` (`_ORCH_STRICT_DEFAULT = True`, the
  same default the schema declares). `consistency/orchestrator_strict` delegates to it instead of
  keeping a second legacy `enabled`/`strict` fallback, so the rendered `ORCH_MODE_STRICT` and the
  runtime gate cannot diverge. The new `validate=False` flag keeps the checker's historic fail-soft
  behaviour for an invalid value instead of aborting the process.
- **Runtime gate and entry point are one invariant (D1a/D1c, #1006)**: a provider `permission`
  deny (`edit`/`bash`) is never written without a valid `default_agent` in the same
  `opencode.json`. A deleted or unusable managed key suspends the gate (the rollback branch takes
  a managed deny back) and emits a loud state-error warning naming how to restore the invariant,
  instead of writing the half-active gate that locked the main chat out. A user-set
  `default_agent` is respected and not overwritten (D1c); edit/shell stay locked for it while the
  gate is active. The v2 surface obeys the same invariant even though its deny is a `permissions[]`
  triple: a triple is never written without a valid `default_agent`, an already recorded one is
  rolled back, and exactly one loud warning names the remedy (D1a(iii)).
- **Announced strict-default flip with a version-driven grace window (D2b, #1006)**: a project
  that only inherits the new strict default keeps the pre-flip behaviour — the entry point still
  lands, the deny waits — and gets one run-level warning plus the new
  `orchestrator-strict.default-flip-grace` finding (WARNING) until `2.1.0`. An explicitly
  configured `strict` is never affected, and the window is data (`_STRICT_DEFAULT_GRACE_UNTIL`
  compared against `VERSION`), not a provider branch.
- **Derived defaults for three previously literal placeholders (#1037, #983)**: `PROJECT_DESCRIPTION`
  is now seeded from the new `project.description` schema field, `AGENT_META_REPO` from the embedded
  `.gitmodules` URL or the agent-meta checkout's own git remote, and `TECH_STACK` from
  `PROJECT_LANGUAGES`. An explicit `variables:` entry always wins, and with no source at all the key
  stays undefined on purpose — there is no blank-string fallback, so the unresolved-placeholder notice
  reports it. A project that only sets `project: {name, description}` no longer ships
  `{{PROJECT_DESCRIPTION}}` into `CLAUDE.md`/`AGENTS.md`, and `{{AGENT_META_REPO}}` (27× across a
  9-provider sync) no longer leaks into the `meta-feedback`/`agent-meta-scout`/`documenter` output.
- **`handoff.advisory: true` as a data marker (#1031)**: the eight literature-anchored review roles
  (`memory-architect`, `context-engineer`, `red-team-agent`, `secrets-manager`, `chaos-engineer`,
  `reproducible-builds-engineer`, `ux-researcher`, `privacy-compliance-officer`) declare it in
  `config/role-defaults.yaml`, and `consistency/handoff_contracts` skips `output-not-consumed` only for
  a handoff carrying that flag instead of an allowlist of role names in code. Only an exact `True`
  counts — any other value leaves the check sharp — and the `target_roles` existence check still
  applies to every producer.

### Fixed
- Preserve `AGENTS.md` user notes in `## Eigene Notizen` across footer rebuilds (#1027)
- **`dod-push-check` 2.1.6 (#1033)**: the protected-branch list in the push-block message is
  de-duplicated — a configured `GIT_MAIN_BRANCH` of `main`/`master` no longer appears twice.
- **Runtime-reader registry evidence re-anchored (#1033 follow-up)**: the `dod-push-check` evidence
  lines in `config/runtime-config-readers.yaml` moved with the 2.1.6 edit —
  `variables.TEST_COMMAND` `:1095` → `:1101`, `variables.TEST_TIMEOUT` `:1142` → `:1148`;
  `variables.GIT_MAIN_BRANCH` (`:224`) is unchanged.
- **Doctor detectors never pick up dotfiles (#1034)**: `is_dotfile` is now the single exclusion
  applied by both `_files_in` and `_glob_matches`, so managed-block manifests such as
  `.agent-meta-managed*` in a rules dir (e.g. `.github/instructions`) are no longer reported as
  rule files. Only the file name is checked, so provider artifact (dot-)directories stay
  traversable and an explicit `path`/`path_template` target stays unfiltered by design.
- **Created hooks are LF-deterministic (#961)**: `--create-hook` now writes through
  `write_atomic` instead of `write_text`, which translated `\n` to `os.linesep` and landed
  created hooks as CRLF on Windows, failing at runtime with `$'\r': command not found`.
  `write_atomic` opens with `newline="\n"` and creates the parent directory itself, so a
  created hook is byte-identical to the sync path; two tests in
  `tests/test_newline_normalization.py` pin the LF write and the dry-run no-op.
- **`dod-push-check` 2.1.7 (#949, #953, #954)**: the git-push flag/short-cluster walk and the
  protected-branch set are built once in `lib/hook_common.sh` (`hook_push_arg_parser_py`,
  `hook_protected_branches`) instead of twice — tag-only check vs. destination check and classifier
  vs. block message now share the identical positionals and can no longer drift apart (#949). The
  shared walk consumes `--recurse-submodules`' separately passed value, closing the bypass where the
  space form (`git push --recurse-submodules on-demand origin …`) reached the submodule check with
  `on-demand` read as the remote and was allowed while the `=` form was blocked (#953). The
  security-critical reads fail closed: an unreadable `git config` blocks on **every** path, the
  tag-only shortcut included — it used to inspect the config verdict *before* the config was read,
  so `git push --tags origin` exited 0 while the same command with a readable
  `remote.origin.push=refs/tags/v1.0.0:refs/heads/main` was blocked — and a `python3` on `PATH` that
  exits non-zero or prints garbage is rejected instead of trusted (#954).
- **`hook_common.sh` 1.1.0 (#949, #954)**: adds `hook_protected_branches` (one de-duplicated
  protected-branch list, used by both the classifier's set and the block message) and
  `hook_push_arg_parser_py` (the single git-push argument walk). `hook_json_usable` now carries its
  probe sentinel in the payload and falls back to a **distinct** value, so an interpreter that exits
  non-zero without output — or is missing — reads as unusable; the old probe compared the result
  against its own fallback default, so a broken shim looked usable and the block came from the
  payload check with a misleading message instead of the interpreter check.
- **`dod-push-check` regression tests (#949, #951, #953, #954)**: one flag walk / one
  protected-list builder are asserted, plus the fail-closed path for an outdated deployed lib
  (#949); the hook tests are hermetic against a caller's `AGENT_META_*` environment, and
  `GIT_MAIN_BRANCH` from `.meta-config/project.yaml`, `-C <other>` as a foreign repository and a
  tag/branch name collision are covered (#951); the `--recurse-submodules` space form is pinned
  against a real submodule (#953); the `git config`, `for-each-ref` and interpreter fail-closed
  paths are pinned, including the tag-only variant that used to read the config verdict before the
  read (#954).
- **#948, #950, #952 re-checked — already fixed in 2.1.3–2.1.5**: the bug session re-reproduced the
  unquoted word-start `#` comment, the `xargs … git push` / `{}` placeholder and the
  `cd`-into-another-repository reports against the 2.1.5 classifier; all three were closed there.
  No code change — the existing regression tests keep them closed.
- **Strict-default grace holds on every read path (#1006 D2b)**: the runtime-gate readers
  (`isolation._opencode_runtime_gate_entries`, `opencode_runtime_gate_wanted`) now hand the
  framework root to the shared three-tier resolver, so they apply the same version-driven grace as
  the writer instead of reporting "gate wanted" while the deny was suppressed. A missing or
  non-UTF-8 `VERSION` counts as *inside* the window — announced, never silently hardened — so only
  a readable version that proves the window has passed flips the implicit strict default.
- **Runtime gate is rolled back before a provider is removed (#1020)**: `remove_provider_dir` — the
  legacy-cleanup and provider-deactivation path — now calls
  `isolation.rollback_opencode_runtime_gate` *before* the provider root disappears, because that
  directory carries the state file recording the managed keys. It takes back the v1
  `permission.edit/bash["**"]` deny (recorded prior restored), the v2 `permissions[]` deny triples,
  and `default_agent` (recorded prior restored); the provider-removal paths additionally take back
  the recorded provider-isolation globs. The helper is tier- and strict-independent — keyed on
  `gate_state_present` rather than the resolved tier — and ownership-guarded via
  `owns_gate_surface` (the resolved `settings_file`/`mcp-config.committed-file` data, never a
  provider-name literal), so deactivating e.g. Claude can never take back Opencode's gate. A state
  file left with nothing but the provenance marker is pruned.
- **One `repo-containment.no-hook-support` finding per project (#1036)**: the per-provider warnings
  are aggregated into a single project-wide WARNING that names every affected provider and its
  reason — a default project with seven hook-less providers emits one finding instead of seven.
  Detection, severity and the finding id are unchanged. In the same pass,
  `check_orchestrator_strict_hook_support` no longer returns early for a config without an
  `orchestrator` block: `{}` is the valid implicit-strict default, so the hard default is announced
  per provider once the D2b grace window has passed; only a malformed (non-mapping) block is skipped.
- **Undefined placeholders warn until 2.1.0 and abort afterwards (#983)**: an unresolved placeholder
  now warns and names the future `SyncError` verbatim while `_UNRESOLVED_PLACEHOLDER_GRACE_UNTIL`
  (2.1.0) lies in the future, and raises exactly that error once it has passed. Both substitution
  engines share one helper, so the notice and the error text cannot drift apart, and a missing or
  non-UTF-8 `VERSION` counts as inside the window. The decision applies only to tokens that survive
  conditional-block stripping: a token in an inactive `{{#if}}`/`{{#unless}}` branch (e.g.
  `{{PIPELINE_DETAILS_DIR}}` in the inactive `ORCH_MODE_MAIN_CHAT` branch) neither warns nor aborts,
  which is what keeps agent-meta's own sync from aborting at the flip.
- **Reference template documents placeholders instead of shipping them (#983)**: `TECH_STACK`,
  `AGENT_RULES` and `EXTERNAL_DOCS_LANGUAGE` are escaped (`{{%VAR%}}`, rendering literally) in the
  non-deployable `agents/1-generic/_reference-agent.md`, and `TECH_STACK` became a derived builder
  variable — the `_UNKNOWN_TEMPLATE_RATCHET` set in `consistency/placeholders` is now empty.
- **`instruction-soft-cap-chars` is owned by the framework (#1035)**: the finding's `fix-owner` moves
  from `project-config` to the new `agent-meta` value, added to `_FIX_OWNERS` and documented in
  `config/known-issues.yaml`: the fix is a template/sync change, and a consumer edit to the artifact
  is overwritten on the next sync.
- **`ac01-baseline` AC-T4 digest re-pinned (#983, #1037)**: the 36-entry rebaseline (the nine copied
  `.meta-config/project.yaml` fixtures plus `agent-meta-scout`/`documenter`/`meta-feedback` × 9
  providers, 0 added/removed) moves the fixture tree, so the AC-T4 digest in
  `tests/test_opencode_v2_surface.py` was recomputed from the fixture bytes before re-pinning.
  `AC01_EXCEPTIONS` is not extended and `slimming-golden`/`compact-golden` are unchanged.

## [2.0.0-beta.4] - 2026-10-26

### Added
- **Eight literature-anchored review roles (IC-28)**: `memory-architect`, `context-engineer`,
  `red-team-agent`, `secrets-manager`, `chaos-engineer`, `reproducible-builds-engineer`,
  `ux-researcher`, `privacy-compliance-officer`. All read-only (no `Write`/`Edit`/`Agent`), all
  name-only addressable (no keyword rule, `orchestrator_only: true`), each with its own
  output-contract id and handoff targets. Registered across schema enum, addressability pins,
  standalone export, eight scenarios and the README role table.
- **Literature-anchored evidence gates for eight roles (#1013)**: `git` gains a staged-content gate
  (secrets/credentials/cloud keys, `.gitignore` coverage, abort on a hit, an already-pushed
  credential is treated as compromised), `security-auditor` composes LOW/MEDIUM findings into
  `CHAIN-n` attack chains, `database-reviewer` gains rule DB-08 (NULL/three-valued logic),
  `tester` forbids production data, PII and secrets in test fixtures, `accessibility-specialist`
  makes the WCAG 2.2 delta auditable, `se-senior-developer` gains security rules for
  security-critical SE leaves, `performance-optimizer` requires a benchmark protocol before
  optimizing, and `incident-responder` preserves volatile evidence before stabilizing. Each touched
  template got a minor version bump; `config/review-rules/database.yaml` gained DB-08 and the
  `hacs-tester` override pin was bumped.
- **Tmp-sink injection (`SPEC-tmp-sink-injection`, spec Rev. 3)**: system temp literals in
  shipped framework text are replaced by the configured sink (`{{TMP_SINK_PATH}}` /
  `{{TMP_SINK_ABS_PATH}}`), and the pytest basetemp as well as the child-process environment are
  derived from `repo_containment.tmp-sink.system-temp-exception`. The suite command renders the
  basetemp as `{{PYTEST_BASETEMP}}` instead of a machine path. A new `temp-literal.*`
  consistency family (WARNING) reports remaining literals in the scanned framework text, and the
  `tmp-sink` config keys (`system-temp-exception`, `toolchain-caches` opt-in) are documented in
  the example config.

### Changed
- **Source boilerplate de-duplicated render-neutrally (IC-31 ratchet)**: the verbatim
  `**Worker role:** Worker, not router ...` line, the `- Worker role: never delegate ...` bullet and
  the `**User proxy:** ... Confirmations come through the caller.` line (shared by the eight
  literature roles plus `meta-doctor`/`meta-optimizer`) are replaced by the snippet blocks
  `{{WORKER_ROLE_ROUTER_BLOCK}}`, `{{WORKER_ROLE_BULLET_BLOCK}}` and `{{USER_PROXY_CALLER_BLOCK}}`
  (`snippets/agents/{worker-role-router,worker-role-bullet,user-proxy-caller}.md`; registered in
  `consistency/placeholders.py`, resolved in `standalone.py`). The wording variants cannot be
  normalised onto the canonical `WORKER_ROLE_BLOCK`/`USER_PROXY_BLOCK` without changing the render,
  so each variant stays its own snippet. Rendered output is byte-identical (AC-01 harness green, no
  rebaseline, no version bumps because the frontmatter `version` is part of the render). Ratchet:
  19 distinct / 189 occurrences -> 16 / 165 (ceilings unchanged at 16/165).

## [2.0.0-beta.3] - 2026-10-23

### Added
- **Opencode v2 surface (opt-in, #1007, `VERDICT-C3: GO`)**: five new
  `provider-options.Opencode` keys that only take effect with `surface-version: v2` —
  `experimental-subagent-depth` (writes `experimental.subagent_depth`; default is the capability
  `required_depth`), `experimental-todo` (writes `experimental.todo`), `providers` (one entry per
  provider ID, passthrough in the documented inner form `settings.baseURL` + `env`),
  `model-variants` (role → variant, appended to the model ID as `#variant`) and `cli` (content of
  `cli.json`). A v2 option in a v1 project writes nothing and warns
  `opencode-v2-option-ignored`. `experimental-subagent-depth`, `experimental-todo`, `providers`
  and the `cli.json` file/format are **DOKU**-backed by the C0 spike — documented in v2, not
  measured in this environment; `system` (body instead of a frontmatter field), `variant` and the
  `permissions[]` evaluation are VERIFIED.
- **Managed merge for `opencode.json` (v2)**: agent-meta owns only its own paths
  (`experimental.subagent_depth`, `experimental.todo`, `providers.<id>`, the gate triples in
  `permissions[]`, `mcp.servers.<name>`) and records `{value, prior, prior_absent}` per path in
  `.opencode/agent-meta-state.json` (namespaces `opencode-v2-keys`, `opencode-v2-permissions`,
  `opencode-v2-mcp`). User keys (`$schema`, `model`, `plugins`, `instructions`, foreign MCP
  servers, user `permissions[]` entries) survive a sync unchanged; a diverging user value is kept
  with a WARNING instead of being overwritten, and a v2 → v1 switch restores the prior or removes
  the key.
- **Native `permissions[]` gate with the surface-wide rollback (v2, C1)**: the closed-world
  builder emits exactly one entry per action (`edit`, `shell`, `subagent`; `allow` when the tool is
  mapped, otherwise `deny`), so a read-only role inherits no write access. The managed `*` deny
  triple is appended to the **end** of `permissions[]` (last match wins, spike Q3) and the rollback
  identifies it by its exact value instead of a list index. When the gate stops being effective
  (surface or tier switch), the triples are removed again **surface-wide**, even when the Spec-A
  writer never ran.
- **MCP v2 connection fields (C2, DOKU)**: `mcp.servers.<name>` accepts `timeout` (`startup`
  alongside `catalog`/`execution`, milliseconds), `oauth` (`client_id`, `client_secret`, `scope`)
  and `disabled`; the v2 entry carries no `enabled`. Every server name from the active catalog
  becomes a managed path, foreign servers stay untouched. All three fields are documented in v2
  but were not probed here; `oauth` deliberately supports only the three named keys and reports
  the other documented keys (`callback_port`, `redirect_uri`, `auth_server_metadata_url`,
  `oauth: false`) as a visible finding instead of guessing.
- **`cli.json` as a managed file (D2, DOKU)**: created only on v2 and only when
  `provider-options.Opencode.cli` is set; the writer passes the user's top-level keys through
  generically and manages them per key, so a v2 → v1 switch rolls the file back. `tui.json` is
  never created, changed or deleted. Documented is only the top-level key `plugins`; `theme` and
  `autoupdate` are not documented and are not claimed as supported.
- **Native v2 agent frontmatter (D1/D3)**: generated agents carry the v2 shape `permissions[]`
  (closed-world, as above), `mode`, `model` with the `#variant` suffix and the `system` body
  instead of the v1 `permission` map; the primary role receives an `edit: deny` (with the
  configured `opencode_primary_edit_allow` path allows, here `.tmp/**` and `.meta-viz/**`) while
  the gate is active. v1 artifacts stay byte-identical.
- **Scenario 79** (`tests/scenarios/asserts/79-opencode-v2-full-surface.sh`): asserts the full v2 surface
  end to end, together with the v1 ↔ v2 lab diff and the v2 → v1 switch rollback in
  `tests/test_opencode_v2_surface.py`; scenario 69 keeps guarding the v2 config keys.
- **C0 spike result**: `VERDICT-C3: GO` (the v2 plugin mechanism is real, probed on v2.1.3) and
  `VERDICT-FIELDS: AMEND`, because `agents.title.model` could not be verified — the follow-up
  Amendment B1 drops `small-model`/AC-B9 instead of inventing a replacement key.

### Changed
- **v2 settings carry `experimental.subagent_depth` instead of the top-level `subagent_depth`**
  (IC-15 no. 16 amended): the v2 parser discards the dead top-level key, so the init transform only
  removes it while the managed-key merge is the single writer of the `experimental` value
  (Amendment B2 — a fresh project takes merge row 1 instead of adopting an untracked value).
- **Gate permissions are rolled back surface-wide**: leaving the v2 surface or losing the gate
  tier removes the managed `permissions[]` triples independent of position (by exact triple, not by
  index) and clears their state, so a returned v1 document does not keep v2-only triples.
- **`opencode.jsonc` removed from the repo root**: the C0 evidence
  (`ERGEBNIS: JSONC-TRAEGT-NICHTS-BEI`) showed the file carries nothing but comments and a
  `$schema` already present in `opencode.json`, while a content-bearing JSONC would partly shadow
  the managed JSON. Only this repo removes the file; consumer projects keep theirs.
- **New warning `opencode-config-duplicate`**: a `.jsonc` twin next to a provider's resolved
  `settings_file` is reported by `consistency-check.py` (WARNING, rc 1 only with `--strict`).
- **The v2 runtime-gate plugin runs behind `VERDICT-C3: GO` — observe-only**: the generated
  `.opencode/plugins/agent-meta-runtime-gate.js` annotates proposed tool calls and never blocks
  one; enforcement stays with the `permissions[]` deny (`MODE=enforce` remains locked until P6).
- **Accepted limit (Amendment B4)**: on tier `plugin` the `default_agent` managed merge does not
  run — `settings-init` writes the value once, a deleted value is not restored, a diverging user
  value raises no warning and a vanished `primary-role` does not revoke it; the protection then
  rests on the agent-level `edit: deny` and the `permissions[]` triples.

### Fixed
- **Opencode entry point (#1006)**: the orchestrator is now generated as `mode: primary` and
  `default_agent` is written to an existing `opencode.json` (managed merge with own state key and
  rollback) on surface v1 as well, so the strict permission-tier gate no longer locks the main chat
  out of every agent. The edit/bash deny is only written when an explicit `primary-role` is
  generated (otherwise a warning); the primary orchestrator no longer emits `edit: allow` while the
  gate is active (writes limited to `.tmp/**` and `.meta-viz/**`). A user-set, different
  `default_agent` is never overwritten (warning only; under strict the gate still applies, so set
  `default_agent` to `orchestrator`). Providers without an explicit `primary-role` (Mammouth) stay
  byte-identical. For non-strict projects the generated orchestrator carries `bash: deny` (from
  `opencode_deny_critical`), so the main chat must delegate shell work.
  **Behavior change for all Opencode projects (strict or not):** the default agent is now
  `orchestrator` instead of `build`, and `@orchestrator` no longer invokes it (it is a primary agent;
  switch via Tab/default).

## [2.0.0-beta.2] - 2026-10-20

### Added
- **Opt-in context profiles (`context-profile`, UNVERIFIED)**: `context-profile: full|compact` —
  default `full` — plus a per-provider `provider-overrides.<Provider>.context-profile` resolve the
  effective profile per provider (precedence: explicit `context_file.mode` > provider override >
  global key > default; `compact` implies `context_file.mode: compact` only while the mode is
  unset) and inject `CONTEXT_PROFILE`/`CONTEXT_PROFILE_COMPACT` into the renders. The switch is
  **opt-in and unverified**: the role-routing eval that would evidence AC-25 has not run (its
  `full` baseline, AC-02, was skipped by the user — 0f.3, `SKIPPED-BY-USER`; the proof is planned
  in package 2f). A sync with `compact` therefore logs INFO `context-profile.unverified` per
  compact provider; a context file shared by several active providers renders `full` and a
  requested `compact` is downgraded with one WARN `context-profile.shared-file-downgrade` per
  file (ADR-5). No default flips to `compact`: a missing key or `full` keeps every render
  byte-identical (AC-35).
- **`compact` render densification (IC-04…IC-08, package 2b, UNVERIFIED)**: with
  `context-profile: compact` the renders carry the compact routing lines (IC-04; a keyword with
  `;` or `|` raises a `SyncError`), compacted orchestrator sections (IC-05), a compact gate card
  plus name-only agent list in the entry file (IC-06), the REFERENCE sections of the four generic
  rules (`a2a-delegation-gates`, `branch-guard`, `submodule-protection`, `security-paved-roads`,
  IC-07) moved to the skills channel as `<skills_dir>/<rule>/SKILL.md` — without that channel the
  full text stays embedded (invariant §4.3) — and CLAUDE.md notes as HTML comments (IC-08). The
  classification is recorded in `docs/guides/context-block-inventory.md`. The profile stays
  **opt-in and unverified**: the deterministic parts (AC-24) are asserted hermetically, the
  role-routing proof (AC-25) is planned in package 2f, a `compact` sync logs INFO
  `context-profile.unverified` (AC-86), and no default flips to `compact`.
- **`compact` anchors, budgets report and provider matrix (package 2c, UNVERIFIED)**: the anchor
  registry `config/context-anchors.yaml` declares the `all-profiles`/`compact-only` surfaces per
  provider × profile × artifact kind (IC-12/QG-3), and `sync.py --context-report
  --profile full|compact|both` renders the opt-in profile into a work directory below the tmp-sink
  (via `resolve_work_dir`, IC-34) — injecting `context-profile: compact` into the work-dir *copy*
  of `project.yaml` only, never the project config — and reports the `full` ↔ `compact` delta. Every
  `compact`/`both` report carries the machine-readable `targets_note`: the AC-26 size targets are
  ESTIMATES (Spec section 11), not measurements; the measured `compact` sizes are pinned as
  regression ceilings (`COMPACT_BUDGET_CEILINGS`) while `COMPACT_BUDGET_TARGETS` records the AC-26
  targets as data (test pins plus the capability config keys `Codex.context_hard_cap_bytes: 32768`
  and `Copilot.context_soft_cap_chars: 4000`). The provider matrix (QG-6) covers 9 providers ×
  2 profiles and `sync.py --check` stays green after a `compact` sync (idempotent, QG-2 anchors and
  pointers intact). The profile stays **opt-in and unverified** (IC-36): the role-routing proof
  (AC-25) is planned in package 2f, a `compact` sync logs INFO `context-profile.unverified`, and no
  default flips to `compact`. The measured sizes currently miss several AC-26 targets (documented
  deviation, to be resolved by a later spec revision per AC-26).
- **Config optimizer runner (`sync.py --optimize-config`, package 2d, IC-24/IC-25)**: read-only
  removal candidates for `.meta-config/project.yaml` plus an L0 losslessness proof. A sentinel render
  (every text value under `variables:` wrapped in `QZ<NAME>QZ…ZQ<NAME>ZQ`) measures the per-variable
  fan-out (occurrences, files, injected bytes, per provider; conditional variables are never wrapped
  and get `occurrences: null`/`conditional: true`), and the proof renders the config verbatim and
  again without the deterministic candidates and compares both trees — the L0 comparison set includes
  the render-derived sidecars `.meta-config/auto-commit-allowlist.json`,
  `.meta-config/generated-file-hashes.json` and `.meta-config/context-hashes.json` (a sidecar missing
  from the render fails the proof; their hashes are recorded before/after). Conditional variables
  (`{{#if X}}`/`{{#unless X}}` usage or the render's conditional list) are never sentinel-wrapped and
  appear in `fan_out` with `occurrences: null`/`files: null`/`conditional: true` and zeroed
  `per_provider`. Output (`proposal.json`, `proposal.diff`, `proof.json`, mode `0600`) goes exclusively
  below `<tmp-sink>/meta-optimizer/<ts>/` via `resolve_work_dir`; the sentinel render and both proof
  renders live in `<run_id>[-before|-after]/work/` and are removed before the command returns, so no
  unredacted config copy and no credential byte sequence survives under the sink. There is no
  system-temp use and nothing is written outside the sink. Credential paths (IC-35 `credentials`) are
  excluded completely (no candidate, no hint, no `FanOutEntry`, redacted diff context; AC-89) and a
  missing/invalid registry is a hard error (`meta-optimizer.credential-registry-invalid`);
  `--include-semantic` adds hint-only kinds (`duplicate-value`, `relocate-*`, `semantic-merge`, never
  applicable, filtered out without the flag); exit 0 (also with candidates), 1 on
  `meta-optimizer.proof-failed`, 2 on `tmp-sink.disabled`, `meta-optimizer.render-failed`,
  `meta-optimizer.out-write-failed`, `optimize-config.out-outside-tmp-sink` or `--fill-defaults`
  (`meta-optimizer.lossy-flag`). The applier (`--apply-config-patch`) follows in package 2d.3.
- **Remove-only config patch applier (`sync.py --apply-config-patch`, package 2d.3, IC-24/AC-80)**:
  the only write-capable optimizer mode. It reads **only** `project_yaml_sha256`, the candidate IDs,
  `agent_meta_version` and `generator_options` from the `proposal.json` and recomputes the candidates
  itself; the file hunks are reconciled against the recomputed (redacted) ones (a hunk that inserts a
  line is `meta-optimizer.not-remove-only`, a differing hunk is `rejected: hunk-mismatch`). `--accept`
  is mandatory (no implicit application), `--accept-runtime` confirms `confirm-runtime` candidates
  (`rejected: needs-runtime-confirmation` otherwise), hint IDs are `rejected: not-applicable` and
  unreproducible IDs are `rejected: not-reproducible`. `--dry-run` writes only
  `<tmp-sink>/meta-optimizer/<ts>/preview.json` (mode `0600`) and never touches the config; an
  application requires `--preview FILE` and is bound to it (ID sets, hash, version and recomputed
  hunks, else `meta-optimizer.preview-mismatch`, AC-90). All-or-nothing: rejections, a failed L0 proof
  (`meta-optimizer.proof-failed`), `meta-optimizer.version-mismatch`, `meta-optimizer.stale-proposal`
  (also re-checked immediately before `os.replace`, TOCTOU) or `meta-optimizer.cross-device` (sink on a
  different filesystem) leave the config untouched. On success the config is replaced atomically from a
  scratch file inside the run dir and the sink keeps `applied.json` (`approval_source: "relayed"`,
  `accept_ids`, `accept_runtime_ids`, `rejected`, both hashes, `preview_sha256`, `generator_options`,
  `timestamp`, `backup_redacted_keys` — key *names* only) and a `project.yaml.bak` whose credential
  values are replaced by the deterministic redaction marker (both `0600`, AC-89). Comments and key
  order survive (remove-only, `analyze_roundtrip`, AC-56); exit 0 all applied, 1 any rejection/global
  mismatch (nothing written), 2 usage/`tmp-sink.disabled`/render/write errors/`--fill-defaults` in the
  same invocation (`meta-optimizer.lossy-flag`). No system temp use
  (AC-94) and no render scratch survives (the applier's recomputation owns and removes its scratch,
  review N2).
- **`meta-optimizer` role registered (IC-28/AC-23/AC-59)**: the read-only config-optimizer role
  introduced in package 2e.1 is now registered across the framework: `meta-optimizer` is in the
  auto-generated `roles` enum of `config/project-config.schema.json`, in the pinned
  addressability distribution (94 roles: 88 keyword, 5 name-only, 1 excluded) with its
  `name_only` reason, in the AC-01 baseline hashes (9 per-provider artifacts plus the
  orchestrator/`AGENTS.md`/copilot-instructions/managed-list/hash rows), in the standalone export
  (`standalone/agents/meta-optimizer.md`) and in scenario `78-meta-optimizer-role`. The AC-01
  exception regex now also covers the Copilot two-suffix form `meta-optimizer.agent.md`. No
  default render behavior changes for existing roles.

### Changed
- **Optimizer chain documented and scenario 78 completed (package 2e.6, AC-59/AC-79/AC-91)**: scenario
  `78-meta-optimizer-role` asserts every provider render of `meta-optimizer` (exact read-only tool set
  `Read`/`Glob`/`Grep`/`TodoWrite`, no `Bash`/`Write`/`Edit`/`Agent`, Opencode `edit: deny`, no `model:` in the
  source template, resolved placeholders, no keyword rule in `routing.rules`), the literal `ARTIFACTS: none`
  contract, warnings taken verbatim, the literal hint label and the absence of any execution channel.
  `docs/api/cli-reference.md` documents both `--optimize-config` and `--apply-config-patch` (incl.
  `--accept`/`--accept-runtime`/`--preview`/`--dry-run`) with their exit codes, and the new-role practice notes
  plus the setup guide/README describe the Analyse → Vorschau → Anwendung chain.
- **Routing keywords come from a single source (IC-30)**: the orchestrator/rule routing keywords
  are read from one registry instead of being duplicated across templates and `role-defaults.yaml`,
  so a keyword rendered for dispatch can no longer drift out of sync with the source of truth.
- **Reflection overrides come from the consumer config (IC-15 Nr. 17, AC-51)**: `config.py` reads
  `reflection-pairs.overrides` from the CONSUMER `project.yaml` handed to `build_variables`, via the
  now dict-aware `reflection.load_project_overrides(config)` — instead of re-implementing the lookup
  inline. This keeps agent-meta's own tracked `MAX_ITERATIONS` from leaking into projects without a
  `reflection-pairs` block.
- **Adapter runtime captures remain UNVERIFIED (AC-15/AC-16/AC-17)**: the per-provider core/adapter
  render (native import syntax `@AGENTS.md`, pointer fallback, byte-identical idempotence) is asserted
  hermetically only — no Claude adapter runtime was captured here. The same holds for the runtime
  surfaces asserted in this phase (Task 1.25 Codex config/hard cap, IC-15 Nr. 5/6 Kimi/Mammouth
  dispatch): their evidence is UNVERIFIED without a live runtime of those harnesses.
- **Source boilerplate de-duplicated render-neutrally (IC-31, AC-72)**: the verbatim worker-role line
  (49 occurrences), the "Mandatory closing summary" line (67) and the "User proxy" line (20) in
  `agents/1-generic` / `agents/2-platform` are replaced by the new snippet blocks `{{WORKER_ROLE_BLOCK}}`,
  `{{CLOSING_SUMMARY_BLOCK}}` and `{{USER_PROXY_BLOCK}}` (`snippets/agents/worker-role.md`, `closing-summary.md`, `user-proxy.md`; registered in
  `consistency/placeholders.py`, resolved in `standalone.py`). The rendered output of all providers and the
  standalone export is byte-identical (AC-01 harness green, no rebaseline, no version bumps because the
  frontmatter `version` is part of the render). Template source: `agents/1-generic` 708376 -> 681588 bytes
  (-26788), `agents/2-platform` 81703 -> 81383 bytes (-320); line count unchanged (1:1 line swap);
  duplicated source lines (>= 40 chars in >= 5 files) 20 distinct / 319 occurrences -> 17 / 183, guarded by the
  new ratchet `tests/test_template_line_duplication.py`. `tests/test_contract_labels.py` now checks the
  snippet-resolved templates (`scripts.lib.standalone.resolve_block_snippets`, #552). The existing
  `{{ANTI_RECURSION_BLOCK}}` (German text) is not reused: it would change the render of the worker-role line.
- **EN/DE closing-summary twin unified on EN (IC-31, AC-72 exception)**: the German "Pflicht-Abschluss-Summary"
  line in 19 templates (`mammouth-expert`, `knowledge-*` x7, `se-*` x11; patch version bump each, override
  `agent-meta-mammouth-expert` re-pinned) now uses `{{CLOSING_SUMMARY_BLOCK}}` - the rendered text of these
  agents switches from German to English (deliberate render change). Rebaselined: AC-01 `hashes.json`
  (18 of 1102 hashes: the `mammouth-expert` artifacts of all providers + managed-file hashes; the other 18
  roles are not part of the provider matrix), 8 slimming goldens (`knowledge-*`, `mammouth-expert`), and the
  committed `standalone/agents/` export (19 files). Ratchet ceilings lowered to 16 lines / 164 occurrences.

### Fixed
- **Copilot reads its generated instruction files (IC-15 Nr. 3, F-17)**: Copilot's capability
  `rules_read_channels` is now `[path-scoped, skills]` (was `[skills]`) — the sync-generated
  `.github/instructions/<name>.instructions.md` files are read once they carry the required
  `applyTo`/`description` frontmatter. `rules._build_rule_frontmatter` detects an already-present key
  with a YAML-key-precise `^key:` match instead of a substring test, so a value or a longer key
  (`xapplyTo`) can no longer make a required key look present. The generated agent name is derived
  provider-agnostically from the artifact filename, not a provider literal. Runtime capture is
  UNVERIFIED (no Copilot runtime available here). Pinned by a positive `rules_read_channels` value in
  `tests/test_capability_keys_ic09.py`.
- **Continue rules get provider-native frontmatter; unresolved placeholders are never written
  (IC-15 Nr. 10, F-14)**: a generated Continue rule file carries the `alwaysApply`/`description`
  frontmatter Continue expects, and `context.omit_unresolved_placeholder_lines` drops any line whose
  project variable is unset instead of writing a literal `{{VAR}}`. Every discarded line is now
  recorded at debug level (F13) so an omitted directive stays diagnosable. A fully configured project
  renders byte-identically.
- **`--create-ext` / `--update-ext` never ship unresolved placeholders (IC-15 Nr. 19, F-14)**:
  `extensions.render_managed_block` routes its rendered block through the shared
  `context.omit_unresolved_placeholder_lines`, so a created/updated extension file contains no
  literal `{{VAR}}` for an unset project variable.
- **Gemini context surface is key-driven (IC-15 Nr. 8, F-07/F-16)**: the Gemini provider entry
  declares `context_filename_settings_key: context.fileName` so AGENTS.md is actually loaded, lists
  `retired_rules_dirs` for the never-read `.gemini/rules` (removed on re-sync through its managed
  indexes only) and gates the personal agent file on the `personal_agents_file` data key — a harness
  that does not read `AGENTS.personal.md` no longer gets it. No provider literal.
- **Read-only roles map to a read-only sandbox (IC-15, F-07)**: a role declaring the read-only
  enforcement capability now emits the provider's read-only sandbox/permission mode instead of the
  default writable surface. Capability-key driven — no provider literal.
- **`--deactivation-status` is read-only (Task 1.25 review)**: the mode reports deactivation state
  without mutating any context/settings file (no writes, no side effects).
- **`declared-surface-empty` only fires when content was expected (Task 1.24 review)**: the check is
  gated on the new `content_expected` predicate, so a surface that is empty by design (skills without
  lazy rules, MCP config without servers) no longer warns.
- **`context.rule-unreachable` is ERROR (Phase 1)**: with Copilot's `.github/instructions` files now
  read, no generated rule channel is unreachable any more, so the check emits its ERROR severity
  (report-only at sync end, `--doctor` exits 1).
- **Phase-1 consistency promotions (PR F)**: `templates.provider-literal` (a provider name literal
  left in a generic template) and `frontmatter.based-on-stale` (a platform override whose `based-on`
  version no longer matches its source) are now ERROR-level; the affected platform overrides were
  re-pinned to their current source versions so the default tree is clean.
- **Agent delegation table rendered as one valid table (IC-15 Nr. 11, AC-20, F-15)**: the
  `agents-table` partial no longer emits blank lines between rows (the full-mode layout was an
  invalid Markdown table with 66-68 blank lines) and the orchestrator no longer repeats a second
  `| Agent | Responsibility | Tier | Parallel |` header above the partial's
  `| Agent | Core Capabilities |` header (whose Tier/Parallel columns were never filled). The
  partial is dense in both context modes, so `context_file.mode` no longer changes the table.
  `orchestrator` 8.5.0 -> 8.5.1, partial 2.0.0 -> 2.1.0. AC-01 rebaselined (24 of 1007 hashes: the
  orchestrator artifact of all 9 providers, the 6 `AGENTS.md` Agent-Directory rows, and the 9
  `generated-file-hashes.json`) plus the orchestrator slimming golden and the `standalone/` export.
- **Mammouth subagent dispatch enabled (IC-15 Nr. 6, F-11)**: a Mammouth sync now emits the same
  OpenCode-native agent surface as Opencode — a lowercase `permission` map including `task`/`todowrite`
  and a set `mode` — instead of the previously inert Claude-cased `tools:` object (study 3.4:
  "Claude-Tool-Keys werden zu inerten Permission-Keys"), plus a `subagent_depth` derived from the
  capability `required_depth` via the data key `inject-subagent-depth` (no provider literal). The
  capability `subagent_dispatch` is corrected to `true` (the native `task` tool is verified at runtime).
  AC-01 rebaselined (63 of 1028 hashes: the 62 `.mammouth/agents/*.md` and the Mammouth
  generated-file-hashes). Runtime capture is UNVERIFIED (no Mammouth runtime available here).
- **Kimi orchestrator frontmatter corrected (IC-15 Nr. 5, F-10)**: a Kimi sync now emits the
  `subagents:` allow-list of the active delegatable roles (from the per-sync `ActiveSet`) on the
  orchestrator, maps `TodoWrite` -> `TodoList`, adds the `AgentSwarm` fan-out tool (capability
  `native_agent_tools`) and renames `hint` -> `whenToUse` on every agent. All data-driven through the
  KimiCode `agent-transform` block plus `subagent_allowlist_required` — no provider literal. AC-01
  rebaselined (63 of 1028 hashes: the 62 `.kimi-code/agents/*.md` and the KimiCode generated-file-hashes).
  Runtime capture is UNVERIFIED (no Kimi runtime available in this environment).
- **Codex dispatch depth, hard cap and `spawn_agent` syntax (IC-15 Nr. 4, F-04/F-09)**: a Codex sync now
  writes `.codex/config.toml` with a managed `[agents] max_depth` (gated on the capability keys
  `agent_config_format: toml` + `required_depth`, `scripts/lib/dispatch_depth.py`), so a spawned
  orchestrator child keeps its multi-agent tools. The rendered `spawn_agent` delegation uses the real
  `agent_type`/`message` parameters (`items`/`fork_context` documented) instead of `agent`/`task`. A
  generated context file at or above a reader's `context_hard_cap_bytes` (Codex 32 KiB, e.g. the
  6-provider `AGENTS.md` after the managed block and the bootstrap injection) now aborts the sync with
  `context.over-hard-cap` instead of writing it silently. AC-01 rebaselined (7 of 1028 hashes: the new
  `.codex/config.toml`, the Codex orchestrator and 4 pipeline-details files, plus the Codex
  generated-file-hashes). Runtime capture is UNVERIFIED (no Codex runtime available here) — the
  `[agents] max_depth` and the 32 KiB hard-cap abort are asserted hermetically only.
- CI: raise `scenarios` job timeout from 45 to 60 minutes (the scenario suite regularly needs 42–45+ minutes).
- **Active-set consumers (IC-18 Nr. 14-18, PR A)**: the raw `roles` allowlist is no longer the only source
  for role-dependent generators; the per-sync `ActiveSet` (gates applied) is used.
  - Continue role prompts follow the ActiveSet: gate-dropped roles and, without a `roles:` key,
    `knowledge-*`/`se-*` no longer get a prompt (only projects with opt-in
    `provider-options.Continue.generate-prompts`).
  - Auto-commit allowlist (`.meta-config/auto-commit-allowlist.json`): `eligible_roles` is the raw list
    intersected with the ActiveSet, so gate-dropped roles lose their commit authority (format and default
    without `roles:` unchanged).
  - `--cleanup-preview` treats gate-dropped roles as stale (expected files = `ActiveSet.roles`).
  - Scout skill (`awesome-claude-code`) and `WEB_PROJECT_ENABLED` additionally require the role in the
    ActiveSet (intersection; default render unchanged).
  - Convention blocks and the strict subagent-permission scan always use the ActiveSet. Without a
    `roles:` key this was "all roles with a source" before, now the ActiveSet.
  - `EFFORT_ESTIMATOR_ENABLED` follows `ActiveSet.has("effort-estimator")`.
- **Active-set consumers (IC-18 Nr. 1, 12; IC-15 Nr. 18, PR C)**: agent table/hints, active-agents data,
  routing rules/tool definitions, intent table and the per-provider agent loop receive the one per-sync
  `ActiveSet` instead of re-resolving the role set (render unchanged, `tests/test_active_set_consumers_identity.py`).
  Quality-pipeline validation runs against `ActiveSet.roles` (gate-dropped roles such as `senior-developer`
  without `junior-developer`, or `validator` without its gate, are now reported in the default as well),
  stages with an inactive `dod_flag` no longer warn, and the agent renderer consumes the single `effective`
  pipelines dict of the variable builder (se-focus filtered) instead of deriving its own.
- **Pipelines with an inactive required role are dropped (IC-18 Nr. 2/3, AC-46, ADR-10), also in the default**:
  `concept-driven-dev`, `feature-lifecycle` (both need `validator`) and `refactor` (needs `senior-developer`)
  are no longer rendered in projects where those roles are inactive - the default project (gates
  `validator`/`developer_tiers` off) included. They disappear from the match table, section 2a, the
  `pipeline-details/*.md` files (stale files are removed on re-sync), `routing.pipelines` and the intent table;
  sync prints and logs `active-set.pipeline-dropped` (WARN) naming the pipeline, the missing role and its
  activation gate. Plan-driven `allowed_agents` of rendered pipelines contain only active roles (a stage without
  `fallback_agent` is left unchanged). Default orchestrator artifact: -3.8 to -4.5 KB per provider.
  How to keep a pipeline: list its roles in `roles:` (`validator`; `junior-developer` AND `senior-developer`).
  Caution: `roles:` is an allowlist - if your project has no `roles:` key yet, adding one turns it into an
  allowlist and restricts it to the listed roles, so list ALL roles you want to keep. In the default project the
  3 WARNs per sync disappear only by activating those roles.
  The static orchestrator prose (task-size routing, "complex feature -> feature-lifecycle", plan-driven gate
  example) names a pipeline only while it is rendered (Task 1.16, see below).
  Scenarios 50, 51 and 52 got an explicit `roles:` list so `concept-driven-dev` stays.
- **`routing.rules[].input_contracts` only with an active producer (IC-18 Nr. 4, AC-47 part)**: projects with
  a `roles:` subset no longer list input contracts that no active role produces (`task-spec-v1` stays, the
  orchestrator produces it). Default render unchanged (every default input contract has an active producer).
- **`template-auditor` without keyword routing (Q9, IC-15 Nr. 14)**: removed `routing_patterns` from the
  name_only role `template-auditor` in `config/role-defaults.yaml`; it stays dispatchable by name only
  (`target_agents`/`name_index`). Scenario 76 assert #5 now checks "no keyword rule in `routing.rules`";
  the ratchet exception list in `tests/test_role_addressability_coverage.py` is empty. AC-01 rebaselined
  for the per-provider orchestrator artifacts only (routing data shrank), context budget `_IST_FULL` updated.
- **Developer tier chain gated on `DEVELOPER_TIERS_ENABLED` (IC-18 Nr. 5, AC-48, PR D), also in the default**:
  with the `developer_tiers` gate off (the default) the orchestrator no longer names `junior-developer`,
  `senior-developer` or `principal-developer`: section 4 routes every implementation task to `developer`,
  the task-size table shows `developer` in the tier column, the `orchestrator_only` route points to the
  ESCALATE-Card intake. Concept agents in the task-size table follow `ROLE_CONCEPT_*_ACTIVE`. `developer`
  (`RECOMMENDED_TIER` line) and `planner` (step mapping, delegation pattern) are gated the same way. With the
  gate on, section 4 is byte-identical to before (pinned in
  `tests/fixtures/developer-tiers/orchestrator-section4-tiers-on.md`). Minor bumps: `orchestrator` 8.5.0,
  `developer` 4.8.0, `planner` 1.6.0. AC-01 rebaselined (36 of 1075 hashes: orchestrator, developer, planner
  per provider + `generated-file-hashes.json`), orchestrator budget -762 B per provider. Standalone export:
  `ROLE_*_ACTIVE`, `DEVELOPER_TIERS_ENABLED` and `PIPELINE_*_ENABLED` are set to `true` (all roles exported),
  which also fixes the leaked double branch in `standalone/agents/meta-doctor.md`
  ("meta-feedbackuser: framework issue").
- **`ANTI_RECURSION_BLOCK` from data ∩ ActiveSet (IC-18 Nr. 6, PR D)**: the roles a worker may point to
  come from the new `role-defaults.yaml` key `anti_recursion.reference_roles`
  (`tester`, `documenter`, `requirements`, `validator`), intersected with the ActiveSet; no role literal in
  `config.py`. Default (validator gate off): "Nur tester/documenter/requirements aus Kontext verweisen."
  Without any active reference role only the first sentence remains. `load_roles_config` exposes
  `anti_recursion`. AC-01 rebaselined (27 of 1075: orchestrator, developer per provider + hashes).
- **`DIRECT_DISPATCH_SECTION` rows only for active roles (IC-18 Nr. 7, PR D)**: every row of
  `templates/direct-dispatch-section.md` sits under `{{#if ROLE_<ROLE>_ACTIVE}}`; the builder resolves the
  conditionals against the ActiveSet, so the orchestrator and the `use-orchestrator` rule only offer direct
  dispatch to active roles (e.g. no `agent-meta-manager`/`feedback` rows in a 10-role project). Default render
  unchanged (all four row roles active, AC-01 green without rebaseline).
- **Orchestrator persona, section 11 fallback and SE prose follow the ActiveSet (IC-18 Nr. 8, AC-49 part, PR D)**:
  the fallback list and section 11 name `meta-feedback` only when it is active - otherwise the fallback is ASK
  (question to the user via `main_chat`); the AI review routing names `ai-security-guardian`, `llm-evaluator` and
  `ai-governance-engineer` only when all three are active (otherwise a role-neutral sentence); `effort-estimator`
  and `se-critic` only when active; the SE-mode prose only with `SE_ENABLED` (off in the default, so the two SE
  lines disappear there). The static prose now names `concept-driven-dev`, `concept-development` and
  `feature-lifecycle` only while the pipeline is rendered (`PIPELINE_<NAME>_ENABLED`); this closes the PR C
  interim where default projects still read "M-XL: first concept-driven-dev" / "complex feature ->
  feature-lifecycle". AC-01 rebaselined (18 of 1075: orchestrator per provider + hashes), orchestrator golden
  rebaselined (SE prose, `se-critic`, AI review sentence: inactive in the self-hosting config).
- **Commands with `requires_roles` only for active roles (IC-18 Nr. 9, AC-50, PR D)**: new optional command
  frontmatter key `requires_roles: [<role>...]`; a command is generated only when all listed roles are in the
  ActiveSet, otherwise it is skipped and a previously generated copy is removed by the managed-file cleanup.
  The key is a generator directive and is stripped from the rendered command (default render byte-identical).
  Set on `doc-now` (`documenter`), `feedback`/`report-bug` (`feedback`), `analyze-logs` (`log-analyzer`) and
  `upgrade-meta` (`agent-meta-manager`). Command bodies now resolve `{{#if ROLE_*_ACTIVE}}` conditionals;
  `add-provider` delegates to `meta-feedback` only when it is active (otherwise the user files the issue).
  New consistency check `commands.requires-roles-invalid` (ERROR: not a list or unknown role).
- **Rule owner lines follow the ActiveSet (IC-18 Nr. 10, PR D)**: `security-paved-roads` (owner column and the
  review-finding sentence), `threat-model-4-questions` (`concept-reviewer` / `orchestrator` lines) and
  `a2a-delegation-gates` (default security-critical roles) name an owner role only when it is active; the
  block catalog itself stays complete ("*(keine aktive Eigentümer-Rolle)*" without an active owner). Default
  render unchanged (all owners active, AC-01 green without rebaseline).
- **IC-30 triage: worker dispatch lines follow the ActiveSet (IC-18 Nr. 11, AC-71, PR D)**: every line of the
  template routing-guard registry (#885 classes A/D/E: `T-HANDOFF`, `T-NEXT`, German handoffs; B/C/F:
  `T-ROLE-ARROW`) is now conditional on its target role - `NEXT:` items, `→ \`role\`` delegation/boundary
  arrows, German `Delegiere an`/`übernimmt` lines (knowledge-*), the documenter KE route, the
  bug-feature-analyzer consultation table, the log-analyzer delegation table and the rules
  `a2a-delegation-gates`, `use-orchestrator`, `gemini-orchestrator-first`. The guard
  (`tests/test_no_role_routes_in_templates.py`) gains the construct-scoped allow rule `D-CONDITIONAL` (target
  token inside the positive branch of its own `{{#if ROLE_<TARGET>_ACTIVE}}`, block or inline); the ratchet
  registry `ROUTE_RATCHET` is empty. Default render: only inactive targets disappear (documenter KE route,
  `se-critic`/`se-interface-mgr` rows, `se-critic`/`validator` arrows) plus patch bumps of 36 templates
  (35 in `agents/1-generic`, `homeassistant-developer`; `developer` keeps its 4.8.0 from this PR). `homeassistant-documenter` 1.2.1 re-pinned to `documenter@1.11.1`. AC-01 rebaselined (270 of 1075: 29 agents per
  provider + hashes), 24 slimming goldens rebaselined (version lines; in the self-hosting config also the
  inactive `se-*`/`security-auditor` rows and arrows). Inline conditionals at a line end use
  `{{else}}{{/if}}` because a false simple `{{#if}}` there also swallows the newline.
- **`active-set.dangling-dispatch` is ERROR (IC-19, AC-49, Task 1.20, PR D)**: the check now also scans the
  generated rules (`rules_dir`, or the default rules dir for providers with `has_rules`), commands
  (`commands_dir`) and `pipeline-details` files besides agents and the context file. Findings are still
  report-only at sync end (sync.log error list/summary, exit code unchanged). Over the fixture matrix
  (p10/p20/pall/ha) x all registered providers there are zero dangling dispatches and zero dangling mentions in
  orchestrator, pipeline-details and commands (`tests/test_active_set_dangling.py`). `mention_allow` lists
  `*add-project-role.*` (its argument-hint names an example role to add); `add-project-role` names
  `/meta-feedback` only when the role is active. Not done: the `RAW_ROLES_RATCHET` (QG-13/AC-84) keeps its
  three intersection sites (auto-commit allowlist, scout skill, `WEB_PROJECT_ENABLED`) - emptying it changes
  default behaviour (see the PR report).
  `--doctor` consequence: the seed `dangling-role-dispatch` now yields an effective ERROR, so a dangling
  dispatch makes `--doctor` exit 1. To keep user files out, rules/commands directories are scanned only for files
  listed in the sync's managed indexes (`.agent-meta-managed*`); unmanaged project commands/rules are ignored.
  The `D-CONDITIONAL` guard rule applies only to files with well-formed conditional markers (repo-wide balance
  test). `requires_roles` accepts flow and block style, only that entry is parsed (non-YAML frontmatter of
  external commands no longer aborts the sync), and the consistency check reuses the generator's parser.
- **Shared context file derived from the active providers only (IC-15 Nr. 1, F-05, PR E)**: the AGENTS.md
  managed block used to join the path fields of every catalog provider that writes AGENTS.md
  (`.gemini/agents bzw. .opencode/agents bzw. ...`), also in single-provider projects, and let an inactive
  sharer without a skills directory veto the lazy-rule channel. Now only the providers the project activates
  count: a single-provider AGENTS.md names only its own agents dir, pending-tasks file and skills dir.
  Whether rules are embedded or replaced by the "native rules" pointer now follows the read channels
  (`rules_read_channels`, spec §4.3) of every active sharer instead of `has_rules` - a written but unread
  rules directory never replaces the embedded rules (new helper `scripts/lib/rule_channels.py`). Default
  render: AGENTS.md of the six AGENTS.md providers changes (AC-01 rebaselined, 6 of 1075 hashes); a project
  with all sharers active is unchanged. The committed self-hosting AGENTS.md was regenerated accordingly.
- **Lazy rules reach every provider with a skills channel (IC-15 Nr. 2, IC-33, F-06, #857, #858, PR E)**:
  rules routed out of the always-on context (`embed: false` / `channel: skill`, rules presets `lazy` and
  `silent`) are now written as `<skills_dir>/<rule>/SKILL.md` for every provider that reads no native rules
  directory but reads skills - decided by `rules_read_channels`, no longer by `has_rules`. Before, providers
  that write an unread rules directory (Codex `rules/`, Mammouth `.mammouth/rules`, Gemini `.gemini/rules`)
  got a lazy-load pointer without any skill behind it, and Gemini under `rules-preset: lazy` lost 8 rules
  completely. Same gating for the lazy MCP/external-tool sections. Data: `rules_read_channels` gains
  `skills` for Opencode, Mammouth, ZCode, KimiCode (`[embedded, skills]`), Gemini and Copilot (`[skills]`,
  their rules dirs stay unread until IC-15 Nr. 8/3) and Continue (`[native-rules-dir, skills]`); Continue
  declares `native-skill-channel`, so `channel: skill` rules land in `.continue/skills` instead of
  `.continue/rules`; Copilot's `skills_dir` is `.github/skills` (was the never-read `.github/copilot/skills`,
  now listed in `legacy_artifacts`). Default preset: only Copilot's rendered skills path changes (AC-01
  rebaselined, 4 of 1075 hashes).
- **No more generated directories the provider never reads (IC-15 Nr. 9, F-07, AC-19, #853, PR E)**: Codex
  (project-root `rules/`) and Mammouth (`.mammouth/rules/`) get `has_rules: false` - their rules were
  already embedded in AGENTS.md, the directories were dead files (study 3.2/3.4). A directory written by an
  earlier version is removed on the next sync through its managed indexes only (`.agent-meta-managed`,
  `-mcp`, `-tools`; new data key `retired_rules_dirs`); files you put there yourself stay, the directory
  is removed only when empty. Claude: the personal file is now `CLAUDE.local.md` (loaded by Claude Code,
  gitignored) instead of the never-loaded `CLAUDE.personal.md`. An existing `CLAUDE.personal.md` is left
  untouched; while it exists no `CLAUDE.local.md` is created and the sync warns to rename it. Still unread
  and reported by `context.unread-channel`: `.gemini/rules` (IC-15 Nr. 8) and `.github/instructions`
  (IC-15 Nr. 3). AC-01 rebaselined (49 entries: rules-dir files removed, `CLAUDE.local.md`, Claude
  `.gitignore`, 2 x `generated-file-hashes.json`).
- **Context files without provider noise (IC-15 Nr. 12, F-16, PR E)**: the AGENTS.md header banner is built
  from the active providers grouped by context file (`> **AI ROUTING:** Codex -> AGENTS.md`, same helper
  `providers.build_provider_routing` as the project templates' `PROVIDER_ROUTING`) instead of the hard-wired
  `Opencode->AGENTS.md | Gemini->AGENTS.md` lines. Lazy-skill tables (`| Skill | Wann |`, rule
  `use-lazy-rules`) list only skills the sync actually writes for the provider (for a shared AGENTS.md: for
  every active sharer); a table without any existing skill is not rendered, so default-preset projects no
  longer get the rule naming 15 agent-meta-internal skills (`sync-interface`, `admin-ui`, ...). Zero
  `context.dangling-pointer` findings over 9 providers x presets `default`/`lazy`. Default render: AC-01
  rebaselined (18 entries: 6 x AGENTS.md, 4 x `use-lazy-rules.md` removed plus their managed indexes and
  `generated-file-hashes.json`); the committed self-hosting AGENTS.md was regenerated (banner).
- **`context.dangling-pointer` is ERROR (Task 1.24, AC-11, PR E)**: over 9 providers x rules presets
  (`default`, `minimal`, `silent`, `lazy`) no generated artifact names a missing skill any more, so the check
  emits its spec level (`EMITTED_SEVERITY` / `PHASE1_PROMOTED` in `consistency/context_budget.py`). Sync end
  stays report-only (sync.log error list, exit code unchanged); `--doctor` exits 1 on a dangling pointer
  (seed `dangling-pointer` is ERROR). Phase-1 follow-ups (PR F): `context.rule-unreachable` is now ERROR —
  with Copilot's `.github/instructions` files read (IC-15 Nr. 3) no generated rule channel is unreachable
  any more — and `context.declared-surface-empty` is gated on the `content_expected` predicate so a surface
  that is empty by design (e.g. skills without lazy rules) no longer warns.

### Changed
- **`ACTIVE_ROLES` / `ROLE_<ROLE>_ACTIVE` available in templates**: `build_variables` injects
  `active_set_variables`. The `meta-doctor` NEXT line now names `meta-feedback` in the default
  (`ROLE_META_FEEDBACK_ACTIVE`); AC-01 rebaselined for the meta-doctor artifacts and their
  `generated-file-hashes` only.

### Added
- **Context measurement and budgets (#964)**: new IC-09 capability keys in
  `config/provider-capabilities.yaml`, the `python3 scripts/sync.py --context-report [--json]` mode
  (`scripts/lib/context_report.py`, `measure_artifacts`; output only in the tmp-sink), the anchor
  registry `config/context-anchors.yaml` and per-provider context budget ceilings
  (`tests/test_context_budgets.py`). Measurement doc with bytes per artifact and approximated tokens:
  `docs/analysis/2026-10-11-context-tokenizer-measurement.md` (tokenizer ratios UNVERIFIED until
  `tests/manual/measure_tokens.py` runs with a real tokenizer).
- **Provider docs corrected (#964)**: `docs/providers/codex.md` (root `rules/`/`.rules` are not loaded;
  `.rules` = Starlark exec policy; AGENTS.md is concatenated, not nearest-wins),
  `docs/providers/kimi-code.md` (concatenation instead of nearest-wins) and
  `docs/providers/gemini-cli.md` (native `.strict()` subagent schema, `.gemini/rules` read by no
  harness, `context.fileName` needed for AGENTS.md). Guarded by `tests/test_context_docs_corrections.py`.
- **Canonical ESCALATE-card snippet (SR-C-07)**: `snippets/agents/escalate-card.md` is the single
  source of the escalation-card contract (`STATUS`/`RESULT`/`ESCALATE_REASON`/`ESCALATE_METRIC`/
  `RECOMMENDED_TIER`/`PARTIAL_WORK`/`NEXT_STEPS` plus the mandatory reason+metric rule, issue #346).
  It renders as `{{ESCALATE_CARD_BLOCK}}`; the developer tiers (`junior-developer`, `developer`,
  `senior-developer`, `se-junior-developer`, `se-developer`) and the `homeassistant-developer`
  platform override now inline it instead of maintaining per-template card copies — closing the
  metric gap in the homeassistant override and the schema drift between tiers.
- **New read-only `template-auditor` role (1.0.0)** — extracted from `agent-meta-manager`: audits
  agent definitions for framework conformity, compactness and correctness. Six-phase sweep
  (inventory → gates → template checks → own delegation sweep → override integrity → report), tools
  restricted to `Read`/`Glob`/`Grep`/`Bash`/`TodoWrite` (no `Write`/`Edit`/`Agent` — a finding is a
  deliverable, not a fix), `addressability: name_only` + `orchestrator_only: true` so a routine task
  cannot silently trigger a full framework audit. Report contract extends
  STATUS/RESULT/ARTIFACTS with `FINDINGS:` and `GATES:`. Ships with scenario
  `76-template-auditor-role` (6 assertions: per-provider generation, read-only tool set,
  `edit: deny` in the Opencode permission block, no `model:` in the source template, resolved
  placeholders, absence from the `route_intent` enum, output contract present).
- **New `meta-doctor` role (1.0.0, #968)** — installation diagnosis: runs
  `sync.py --doctor`, deduplicates and prioritizes known-issue findings and hands fixes to
  `agent-meta-manager` (`doctor-findings-v1`); never repairs and writes reports only to the tmp-sink.
  Tools `Read`/`Glob`/`Grep`/`Bash`/`TodoWrite`, `addressability: name_only` +
  `orchestrator_only: true`, no `routing_patterns`. `agent-meta-manager` 1.24.0 consumes
  `doctor-findings-v1` (section 10b). Registered per the new-role checklist (IC-28): schema role enum,
  standalone export, pins in `tests/test_role_addressability_coverage.py` (93 roles, name_only 4,
  new `test_name_only_roles_have_no_routing_patterns` with a ratchet exception for `template-auditor`),
  routing-eval corpus regenerated, scenario `77-meta-doctor-role`. Golden and AC-01 baseline were
  rebaselined (new role artifacts and the manager consumer section only).
- **Project-type-specific release-process templates (issue #452)**: a project can declare a `release`
  section in `project.yaml` (`distribution`, `versioning`, `changelog_format`, `version_file`,
  `version_field`). When `release.distribution` is set, the sync pipeline renders
  `templates/docs/RELEASE_PROCESS.<distribution>.md` into `docs/RELEASE_PROCESS.md`, wrapping the
  generated body in managed-block markers so project-specific additions below `managed-end` survive a
  refresh (same mechanism as the extension files). Ships the HACS proof-of-concept template
  (`templates/docs/RELEASE_PROCESS.hacs.md`) covering SemVer + `manifest.json` versioning, a
  Conventional-Commits version-bump decision table, Keep a Changelog, the HACS version-discovery caveat
  (GitHub Releases + `manifest.json`, not `hacs.json`), a pre-release checklist and the release workflow
  (incl. the ~24 h HACS sync delay). An absent `release` section or an unset `distribution` is a no-op.
  Schema in `config/project-config.schema.json`, scaffolder in `scripts/lib/release_scaffold.py`,
  coverage in `tests/test_release_scaffold.py`.
- **Web-Plattform-Preset für SEO/Accessibility/Privacy (issue #679)**: Projekte mit
  `platforms: [web]` erhalten jetzt drei zentral gepflegte Rule-Dateien ohne eigene
  Recherche — `rules/2-platform/web-seo.md` → `.claude/rules/seo.md` (Local SEO, Technical
  SEO/Core Web Vitals, Schema Markup), `rules/2-platform/web-accessibility.md` →
  `.claude/rules/accessibility.md` (WCAG 2.2 AA inkl. Mobile-Kriterien: Target Size, Reflow,
  Pointer Gestures) und `rules/2-platform/web-privacy.md` → `.claude/rules/privacy.md`
  (DSGVO, Consent-first, Google Consent Mode v2, self-hosted Fonts). V1 ist bewusst
  rules-only: kein `platform-configs/web.defaults.yaml` (generischer Best-Practice-Inhalt
  ohne Projekt-Platzhalter) und noch kein eigenes `agents/2-platform/web-*.md` (Admin-UI-
  Discoverability als Folge-Issue offen). Migration: `web` in `platforms:` eintragen und
  `python scripts/sync.py` laufen lassen — bestehende manuelle `SEO/ACCESSIBILITY/PRIVACY_REQUIREMENTS`-
  Variablen können danach entfallen. Regressions-Szenario: `tests/scenarios/configs/75-web-platform-preset`.

### Fixed
- **`--check` help text (#964)**: `--help` now says `--check` forces dry-run (matches
  `_normalize_check_dry_run`) instead of "use with --dry-run".
- **repo-containment hook and progress paths mirror the tmp-sink rules (#963)**:
  `repo-containment-impl.sh` (`# version: 1.0.0` -> `1.1.0`, drift warning via `check_stale_deployed_hooks`)
  and `progress_path_error` now apply the same path rules and canonical form as `tmp_sink_path_error`
  (UNC, reserved Windows names, protected provider directories, backslash canonicalization); an unsafe
  sink path still falls back to `.tmp` in the hook. One shared corpus
  (`tests/fixtures/tmp-sink-path-corpus.json`) is checked against all three implementations.
- **tmp-sink path guard hardened (#963)**: the protected-path list for `repo_containment.tmp-sink.path`
  now covers all provider directories (e.g. `.agents/out` is rejected). Unsafe paths (drive letters,
  UNC, root escape, reserved Windows names) in existing configurations now abort the sync hard.
  Migration: change `tmp-sink.path` to a relative path inside the repo, e.g. `.tmp` or `scratch/out`.
  Known limits: Windows 8.3 short names (`GIT~1`) and an intermediate in-root symlink pointing at `.git`
  are not detected.
- **Flaky `test_local_process_partial_line_timeout` / unclear plugin-test message**: the MCP
  initialize handshake now reports a process that exits before reading the request (BrokenPipe on
  write, or EOF on read) as FAIL "no response from MCP server (process exited ...)" instead of a raw
  `[Errno 32] Broken pipe` / "initialize responded". The partial-line test uses `cat` (stays alive)
  instead of `true`, and a new test covers the exited-process case explicitly.
- **Machine-local files no longer committable without a Claude provider (SR-A-11/31)**: projects whose
  providers have no dedicated context file (Gemini, Codex, Mammouth, ZCode, KimiCode, Opencode,
  Continue, Copilot) now also ignore `sync.log`, `*.sync-backup-*`, the generated
  `.meta-config/env.*` scripts (may hold secret defaults), viz/skill entries and `AGENTS.personal.md`
  (new `gitignore_entries` in `config/ai-providers.yaml`). New provider matrix test
  `tests/test_provider_matrix_sync.py` syncs every registered provider and asserts artifact validity,
  gitignore coverage and idempotence.
- **`--validate` no longer reports 88 false `placeholders.unknown` warnings**: the block-inlining
  variables `OUTPUT_GUARD_BLOCK`, `BACKGROUND_PROCESS_GUARD_BLOCK`, `PARSE_INPUT_BLOCK` and
  `ESCALATE_CARD_BLOCK` are known built-ins.
- **`--validate` judges the current run (SR-A-24)**: `validate_test_repo` counts the errors recorded
  by this run instead of re-reading a stale `sync.log` from the test repo (a fixed problem no longer
  fails validation, a fresh error no longer passes).
- **Provider literals removed from data paths (SR-A-06/12/13)**: `sync_prompts_for_continue` takes
  `provider=` and reads its output dir from `commands_dir`; the managed `.gitignore` block is driven
  by `has_dedicated_context_file` (union of those providers' `gitignore_entries`); the flat
  `model-overrides` warning uses the `model-overrides-flat` capability. A new AST guard
  (`test_no_provider_literal_usage_in_lib`) flags provider literals in `.get()`/subscripts/membership
  tests/call arguments/new default parameters; ten legacy default-parameter sites are allowlisted and
  may only shrink.
- **Template fixes (#932, #933, #934, #935)**: `provider-expert`/`mammouth-expert` use their literal role
  name in the extension path instead of the unresolvable `{{ROLE}}` (#933); `orchestrator` §10/§12 point
  at `{{AGENT_META_REL_PATH}}agents/1-generic/_wf-orchestrator-reference.md`, which exists in the
  submodule layout (#932); `agent-meta-manager` uses `python3` with a documented PyYAML prerequisite
  instead of the Windows-only `py` launcher (#934); `planner`, `concept-reviewer`, `concept-specifier`,
  `orchestrator` no longer cite the non-existent `§7.1`/`§7.2` sections (#935).
- **`standalone/` export regenerated**: it had drifted from `agents/1-generic` and was missing the roles
  ai-governance-engineer, ai-observability-engineer, ai-security-guardian, app-lifecycle-governor, concept-architect, concept-specifier, control-framework-assessor, fraud-risk-assessor, llm-evaluator, prompt-governor, rag-engineer, risk-based-audit-planner, se-component-requirements, test-executor.
- **`dod-push-check` 2.1.5 (#947, #948, #950, #952, #953)**: heredoc bodies handed to a text-only consumer
  (`cat`, `gh`, `tee`, `git commit`/`tag`/`notes`) are no longer classified as commands, so PR
  bodies and commit messages that mention `git push origin main` stop being blocked; bodies fed to a
  shell, interpreter, pipe or `eval` stay visible. An unquoted word-start `#` comment is cut before
  tokenizing (`origin feat/x # main` passes; `"#main"` and mid-word `#` stay literal). `xargs`
  carrying a `git push` and the `{}` placeholder fail closed; the computed-refspec block message names
  the literal-branch / `HEAD` way out. A push in a command containing `cd`/`pushd`/`popd` is judged like
  a `-C` push into another repository (refspec-less and `HEAD` pushes block), closing a bypass where the
  other repo's `main` was checked against the cwd repo's branch. `--recurse-submodules=on-demand|only` fails
  closed in a repository with `.gitmodules` (submodules push to their own remotes and branches).
- **Admin UI network mode (#897)**: a concrete `--host <ip>` now authorizes its own Origin (the Host
  check already did); a wildcard bind (`0.0.0.0`) prints the `--allowed-hosts <detected-ip>` hint at
  startup, and the `origin not allowed` error names `--allowed-hosts` / `admin-ui.allowed-hosts`. The
  backup overlay is closed in a `finally`, so a failed request cannot leave it hanging. A wildcard
  bind still does not auto-trust arbitrary Host/Origin values (DNS-rebinding protection).
- **CI robustness (#945, partial)**: every workflow job has `timeout-minutes` (was the 360-minute default),
  the test job runs `pytest -n auto` (`pytest-xdist` in `tests/requirements.txt`), and
  `tests/test_orchestrator_guard_hook.py` runs against a throw-away copy of `project.yaml` instead of the
  real checkout, so it no longer appends test lines to `.claude/hooks/.guard-audit.log`. The new provider
  matrix test falls back to `tomli` on Python < 3.11 (the CI matrix includes 3.9). The `scenarios` job
  timeout is 45 minutes because the scenario suite needs ~30 minutes (20 minutes cancelled it).
- **Registry load fails loudly without PyYAML (SR-A-16)**: `load_providers_config` raises `SyncError`
  instead of silently degrading to the Claude-only fallback registry.
- **Nested null `orchestrator.unknown-fallback` no longer crashes (SR-A-28)**.
- **`orchestrator-guard` fails closed on an unparseable payload (SR-B-09)**: a non-empty hook payload
  that is not valid JSON now exits 2 instead of being read as "no tool name" and allowed.
### Fixed
- **Claude hook commands are now anchored to `${CLAUDE_PROJECT_DIR}` instead of being cwd-relative (issue #851)**:
  `sync.py` registered hooks as `bash .claude/hooks/<file>.sh`, which Claude Code resolves against the
  process cwd — a session started (or a subagent spawned) from a subdirectory silently ran no hook at
  all. The prefix is now provider-config-driven (`hook-command-anchor` in `config/ai-providers.yaml`,
  set for Claude to `${CLAUDE_PROJECT_DIR}`) and emitted as
  `bash ${CLAUDE_PROJECT_DIR}/.claude/hooks/<file>.sh`. The inverse parser recognises both the anchored
  and the legacy relative form, so already-deployed projects are clean-replaced without duplicate
  entries; a provider without the key (e.g. Antigravity, which resolves relative to its `hooks.json`)
  stays byte-stable (no hidden provider-name branch). Regression coverage in
  `tests/test_hook_registration_invariant.py` and `tests/test_hook_enablement_consistency.py`.
- **Plan-graph `file_overlap` no longer flags sequential plans or prose/`Interfaces:` paths (issue #848)**:
  two root causes. (1) `_parse_plan_tasks` ran its `Modify:`/`Create:` regex over the whole task block,
  so prose and `**Interfaces:**` paths were captured as file ownership; extraction is now scoped to the
  `Files:` sub-block up to the next known task field header (`Interfaces:`, `Agent:`, `Depends on:`, ...;
  bold optional, so a non-bold header still terminates but an in-block `**Note:**` does not). (2) `validate_plan` applied the
  injected file-overlap check to every plan kind, so a sequential `Depends on:` chain sharing files
  raised a false `spec_plan_plan_graph` ERROR; per the design contract the overlap check now fires only
  for parallel plans (`fanout`/`parallel_group`), and the plan-graph consistency check (which models a
  plan as `sequential`) is intentionally overlap-inert while cycle/deadlock/over-commitment stay active.
  Regression coverage in `tests/test_spec_plan_consistency.py` and `tests/test_orchestration_contract.py`.
- **Admin-UI saves no longer silently strip YAML comments from `config/ai-providers.yaml` (issue #847)**:
  both write paths (`ConfigManager.write` behind `PUT /api/config/ai-providers` and
  `_handle_post_ai_providers_update`) re-serialised the heavily commented provider registry with
  `yaml.dump`, dropping **all** `#` comments (and potentially reordering mapping keys) on every save.
  PyYAML has no round-trip support and agent-meta is stdlib-only (`ruamel.yaml` is not allowed), so the
  new provider-agnostic diff guard `scripts/lib/yaml_roundtrip.py` compares the on-disk text with the
  would-be-written text and **aborts by default** (`YamlRoundTripLoss` → HTTP 400 / raised for direct
  `ConfigManager.write` callers) instead of destroying hand-authored comments. A caller that knowingly
  accepts the loss can opt in with the reserved body flag `"__allow_lossy__": true` (stripped before
  persisting, so it never becomes a registry key); a lossy write then logs a warning and proceeds.
  Regression coverage in `tests/test_ai_providers_roundtrip_847.py` (both handlers, guard unit tests).
- **`--init`/`--fill-defaults` now enforce owner-only permissions on `project.yaml` (issue #864, security)**:
  the Admin-UI save path already chmodded `.meta-config/project.yaml` to `0600` (issue #589), but the CLI
  writers left it at `0644` under a typical `022` umask — so a plaintext `admin-ui.token` or credential key
  stayed group/world-readable. `config.fill_defaults()` (the engine behind `--init`, `--fill-defaults` and
  the per-sync auto-fill), the `--setup` wizard's `_write_config()` and the agent-meta-version write-back
  now all harden the config via the new shared `scripts/lib/permissions.py`
  (`harden_admin_config_files()`), mirroring the Admin-UI path (including the `.meta-config/plugin-catalog.yaml`
  sibling when present). Hardening is best-effort/cross-platform-safe and is skipped entirely in `--dry-run`.
  Regression coverage in `tests/test_project_yaml_permissions_864.py`.
- **`sync --check`/`--validate` now validates the committed MCP document (issue #849)**:
  the artifact gate (`agent_sync.collect_artifact_findings`) scanned only each
  provider's generated agent files, so an invalid or shape-broken committed MCP
  document (`opencode.json`/`.jsonc` flat v1 `mcp` vs. nested v2 `mcp.servers`,
  or the Codex TOML document) passed `--check` while it was only ever caught by
  `consistency-check.py`. The MCP-document resolution/validation is extracted
  into a single shared helper `artifact_validate.validate_mcp_document`, called
  by both the sync-time gate and the registry-wide consistency check (single
  source of truth for the `resolve_artifact_contract` /
  `validate_json_document` / `validate_toml` dispatch). Dispatch stays
  provider-agnostic: it reads the declared `mcp-config.format` value only.
- **A2A `payload.t` length limit is now machine-enforced, not merely documented (issue #812)**:
  the documented 300-character task-line ceiling had no schema counterpart
  (`maxLength` was absent), so schema validation accepted arbitrarily long
  `payload.t` values. `schemas/a2a-handoff.schema.json` now declares
  `maxLength: 300` for `payload.t` (single envelope) and for every FANOUT batch
  entry `payload[].t`, and the universal payload schema
  `schemas/handoffs/task-spec.schema.json` carries the same ceiling on `t`.
  `DelegationSyntaxEngine.validate_envelope()` enforces the limit stdlib-only
  (works without `jsonschema`) for both payload shapes and reports a clear error
  naming `payload.t` / `payload[<index>].t`. The ceiling derives from a single
  source — `orchestrator.handoff.t-size-limit` (default 300) via the new
  `resolve_a2a_t_size_limit()` / `DEFAULT_A2A_T_SIZE_LIMIT` in
  `scripts/lib/config.py`, the same value that backs `{{A2A_T_SIZE_LIMIT}}`; a
  consistency test locks the schema `maxLength` to that default.
  `rules/1-generic/a2a-delegation-gates.md` now documents the limit as
  schema-enforced instead of a degraded doc-only check.
- **MCP connection placeholders no longer ship as raw `{{VAR}}` literals in generated
  output (issue #810)**: generated MCP rule/context artifacts (`mcp-<server>.md`,
  `<skills_dir>/mcp-<server>/SKILL.md`) rendered the plugin catalog's `connection` block
  verbatim, so an active server's URL landed as e.g. `` {{MCP_HONCHO_URL}} `` instead of an
  env reference. `_generate_rule_content()` now normalises every `{{VAR}}` to a committed
  `${VAR}` reference via the new provider-agnostic `_render_env_references()`, and
  `generate_mcp_artifacts()` warns when a connection references a variable that is not
  declared under the server's `secrets:` (the genuinely "undefined MCP variable" case).
  No secret value is ever invented. Regression coverage in `tests/test_mcp_config.py`.
- **Destructive gate now also blocks filesystem destruction and fork bombs (issue #809)**:
  the `orchestrator-guard` destructive classifier previously only inspected
  `git <subcommand>` tokens, so a direct `rm -rf /` or `rm -rf /etc` passed through with
  exit 0. The shared tokenizer now also classifies non-git shell catastrophes
  (`orchestrator-guard-impl.sh` 1.5.0):
  - recursive `rm` on a dangerous root (`/`, a top-level system directory such as `/etc`,
    `/usr`, `/var`, `~` / `$HOME`) is blocked with `exit 2` regardless of sentinel;
  - a recursive fork bomb (`` :(){ :|:& };: `` and named variants) is blocked;
  - benign in-repo deletions (`rm -rf .tmp/...`), project-relative cleanup and known
    scratch subtrees (`/tmp/...`, `/var/tmp/...`) stay allowed;
  - still a best-effort token scan (no shell interpreter) — documented limits in
    `rules/1-generic/branch-guard.md` ("Bekannte Grenzen", items 5–6).
- **Generated hooks are no longer shipped as silently-dead code (issue #808)**: `sync.py`
  now distinguishes real hooks from helper scripts and from non-runtime hooks, so the
  generated hook set and the registered hook set no longer drift:
  - Scripts without a `# hook:` header (e.g. `orchestrator-guard-impl.sh`,
    `repo-containment-impl.sh`) are reported as **helpers** instead of being logged as
    "not enabled — add `hooks:{...}`". They are never registered.
  - Protocol-scoped scripts declare `# hook_protocol:` and are only deployed to providers
    speaking that protocol. `antigravity-json-adapter.sh` (now 1.1.0) therefore no longer
    lands in `.claude/hooks/` for Claude projects — it is only deployed for
    `hook_protocol: antigravity-hooks-json` (Gemini/Antigravity).
  - Hooks with `event: Manual` (e.g. `pre-release-check.sh`) are never written into
    `settings.json` as an event bucket the harness never fires, even if a project sets
    `hooks: { pre-release-check: { enabled: true } }`. The dispatcher is invoked
    explicitly by the `release` agent.
  - The `hooks.enabled-but-not-registered` consistency check skips helpers and `Manual`
    hooks (they have no registration path by design) and keeps flagging genuinely
    enabled hooks that are missing their registration.

### Changed
- **`auto_commit` no longer tells no-Bash roles to commit directly (consumer-visible, #767)**:
  commit authority is now derived per role from its own 1-generic `tools:` contract into four
  capability classes — `direct` (Bash **and** (Edit and/or Write)) commits itself, `delegate` (Edit/Write,
  no Bash, but an `Agent`/`Task` tool) hands the commit to the `git` agent at each trigger
  boundary, `notify` (Edit/Write, no Bash, not spawn-capable) only reports the changed files plus
  a ready-to-use Conventional-Commits message to its caller, and `none` renders nothing. The
  guard-hook allowlist `eligible_roles` is now **direct-only** (previously any Edit/Write role),
  so the `orchestrator` (Write, no Bash) and the documentation/concept roles lose a "Commit
  directly" instruction they could not carry out and no longer appear in the allowlist. The
  configured `secret_scan` requirement is now forwarded into `delegate`/`notify` prose as well
  (the party performing the commit runs the scan; a finding blocks it; `secret_scan: false`
  omits it). `mode: off` still renders nothing for every role and stays byte-identical to a sync
  without an `auto_commit` key; no template or `{{#if}}` change.

### Fixed
- **Slash commands now reach Copilot, Mammouth and ZCode; Codex/KimiCode documented as no-project-surface (#807)**:
  the F18 audit found 5/9 providers received 0 generated commands. Re-verified each against its
  real command surface: Copilot (`.github/prompts/*.prompt.md`), Mammouth (`.mammouth/commands/*.md`,
  its OpenCode-fork runtime documents *"Add .md files to .mammouth/commands/"*) and ZCode
  (`.zcode/commands/*.md` workspace commands) genuinely support commands and were flipped to
  `commands: true` + `has_commands: true` with `commands_dir`/`commands_ext`/`commands_format`
  (fixes the prior UNDERCLAIMs P-6 / ZC-2). Codex (custom prompts are user-global
  `${CODEX_HOME}/prompts` and deprecated; project-scoped `.codex/prompts` is an open upstream
  request) and KimiCode (built-ins + Skills, no custom-command dir) stay `commands: false` as
  explicit, documented capability decisions — no silent hardcoded default. New pytest contract
  (`tests/test_provider_agnostic_dispatch.py`) asserts every `commands: true` provider emits >0
  commands into its *declared* dir and every `commands: false` provider emits nothing.
- **`sync.py --check` now converges after ONE sync on a fresh clone (#802)**: `--check` reported
  drift (rc 1) on a freshly-synced tree until a *second* sync was run, breaking fresh clones of
  multi-provider and Continue-`generate-prompts` projects. Three independent causes:
  - the injection-drift scanner did not recognize several artifacts agent-meta itself had just
    written — `.claude`/`.opencode/agent-meta-state.json`, `.gemini/policies/`,
    `.continue/rules/provider-isolation.md` and `.agents/hooks.json` — and flagged them as foreign
    injections. Recognition now routes through the shared `is_managed_artifact` predicate (managed
    marker / managed-index); the isolation state files and Gemini policy carry the canonical
    `agent-meta managed — do not edit manually` sentinel (the recognized marker is the full sentence,
    not a loose substring, so the same predicate that gates destructive migrate/delete is not
    widened), and `hooks.py` writes a top-level `_agent-meta` provenance key into its `hooks.json`.
    A directory is excused only when its WHOLE subtree is agent-meta-managed — a managed decoy must
    not hide an unmanaged sibling;
  - `sync_prompts_for_continue` logged an unconditional `WRITE` per prompt even when the content was
    byte-identical — now routed through `write_checked` (unchanged → `skip`);
  - active external skills logged an unconditional `WRITE`/`COPY` — now content-compared via
    `write_checked` (unchanged → `skip`). Third-party skill content is written with
    `allow_secrets=True` (warn-only), preserving the non-raising behaviour of the raw `write_text` it
    replaced.
  A second sync is no longer required; real syncs still log `WRITE`/`COPY` when content actually
  changes. Scenario 71 now asserts `--check` rc 0 *before* the second sync; new scenario 73 covers the
  Continue `generate-prompts` one-sync case.
- **Codex agent TOML serialized before body injections (#862)**: `codex-toml` providers emit the
  Markdown body as the trailing `developer_instructions = """..."""` field, but the debug-mode, viz,
  critical-rules-footer, `pathRules` and `xml-section-wrapping` blocks were appended *after*
  serialization — they landed outside the string and produced unparseable `.codex/agents/*.toml`.
  `_finalize_agent_content` now detects the serialization mechanism from the provider spec
  (`agent-transform.frontmatter-mechanism == "codex-toml"`, never the provider name) and applies
  those body-level injections before the transform; every other provider keeps the historic order.
  Scenario 64 now enables debug-mode plus all four options and asserts the debug marker lives inside
  `developer_instructions`.
- **`agent-meta-version` schema rejects SemVer pre-release/build versions (#850)**: the
  `agent-meta-version` pattern in `config/project-config.schema.json` accepted only `X.Y.Z`, so a
  repo pinned to `2.0.0-beta.1` failed its own schema and `sync.py --validate` emitted a
  `Config validation warnings` entry. The pattern now accepts SemVer pre-release (`-beta.1`,
  `-rc.1`) and build metadata (`+build.5`) while still rejecting `1.2`, `1.2.3.4` and `v1.2.3`.
  `protocol_version` in `schemas/a2a-handoff.schema.json` is a separate field and is unchanged.
- **Guard hook rejects a leading UTF-8 BOM in a commit message (#842)**: the
  `orchestrator-guard` tokenizer now emits a third word (`message` | `file` | `none`) and
  `hooks/1-generic/orchestrator-guard-impl.sh` blocks `git commit -m`/`-F` whose subject starts
  at byte 0 with `EF BB BF` (exit 2) — even with a `git` sentinel and before the strict-mode
  early exit. Rejected, not stripped: the hook only sees the Bash command string. The gate is
  scoped to `commit` and only matches a BOM at the very start of the message or message file.
  Detection also covers ANSI-C quoting (`-m $'\uFEFF…'` / `$'\xEF\xBB\xBF…'`), combined
  short-option clusters (`-am`, `-aF`) and glued short forms (`-m<msg>`, `-am<msg>`, `-aF<file>`),
  while a normal message that merely starts with a literal `$` is not a false positive.
- **KimiCode `mcp.json` inline env-var expansion flagged for manual validation (#843 F7 / AC-8)**:
  the committed `.kimi-code/mcp.json` is emitted with inline `${VAR}` references and no secrets
  file, but whether Kimi Code expands inline env vars could not be verified from the repository.
  The `kimi-json` serialization path now emits one actionable warning per affected server (naming
  the file and the server) stating that the inline expansion is UNVERIFIED and pointing at the
  Kimi-native `bearerTokenEnvVar` + `env` indirection or manual validation. The warning is
  format-keyed (never provider-name keyed), adds no `log.action` (so `--check` stays rc 0), is
  deduplicated by `SyncLog`, and leaves the emitted JSON shape byte-identical.
  `docs/providers/kimi-code.md` §MCP documents the resolution.

## [2.0.0-beta.1] - 2026-10-03

### Added
- **Four AI-agent roles, anchored in a 50-book literature analysis (27 Manning + 23 Humble/Packt)**:
  - `llm-evaluator` (1.0.0) — measures model/agent output against a golden dataset: offline eval
    suite, validated LLM-as-judge, rubrics, task-success metrics, regression gates on prompt/model
    change. Applies the zero-product aggregation rule (Lee, *LLM Evaluation and Alignment*, ch. 2.1.4)
    so a failed quality dimension cannot be averaged away, and classifies a task as closed- or
    open-domain before choosing a verifier (ch. 5.1). Rubric/checklist distinction per Nassery,
    *AI Model Evaluation*, ch. 10.2.3.
  - `rag-engineer` (1.0.0) — retrieval pipelines: chunking trade-offs, embedding-model choice,
    hybrid retrieval (BM25 + vector), reranking, query rewriting, retrieval eval sets
    (recall@k/MRR/NDCG). Single-responsibility staging per Melillo, *Learn AI Data Engineering*,
    ch. 12.1.2.
  - `ai-governance-engineer` (1.0.0) — model-risk governance: AI risk classification, model/system
    cards, bias assessment across segments, EU AI Act / NIST AI RMF mapping, and decision records.
    Reuses the existing RCM and control-mapping method rather than rebuilding it. Per Bozdag/Bennati,
    *AI Governance*, ch. 1.3 ("building governance for uncertainty, not pretending uncertainty
    doesn't exist") and ch. 4.3.1 (decision records as the transparency artefact).
  - `ai-observability-engineer` (1.0.0) — agent-behaviour SLIs: task success rate, reasoning quality
    (5–10 % human-reviewed sampling, a *leading* indicator), approval request rate, plus per-task
    token cost, latency and drift detection. SLI definitions per *The Ultimate AI Guide for Linux
    Engineers* (Humble), ch. 6.
  - New review-rules domain `config/review-rules/ai.yaml` with 8 rules (AI-01…AI-08), including the
    two literature-anchored anti-patterns for AI-generated code: happy-path code (Morgan,
    *Coding with AI*, ch. 5) and symptom-fix-instead-of-root-cause (ch. 6).
- **`risk-based-audit-planner` role (PR #822)**: new 1-generic template
  `agents/1-generic/risk-based-audit-planner.md` for risk-based audit scoping — auditable area to
  objectives, risks, key controls and tests (risk control matrix) with inherent/residual risk, scope,
  timing and resource plan.
- **`control-framework-assessor` role (PR #822)**: new 1-generic template
  `agents/1-generic/control-framework-assessor.md` assessing governance, risk and control processes
  against a named framework (COSO ICIF, COBIT, CARES/Standard 2120, ITGCs), with analytics/CAAT
  evidence over full populations instead of samples.
- **`fraud-risk-assessor` role (PR #824)**: new 1-generic template
  `agents/1-generic/fraud-risk-assessor.md` assessing occupational fraud risk and appraising the
  anti-fraud program across deterrence, prevention, detection and investigation — scenarios built on
  the Fraud Triangle/Hexagon, red-flag indicators and the reporting channel, with inherent and
  residual exposure rated. Read-only and prospective: no investigation, no accusation, no risk
  management.
- **Provider-agnostic artifact validation (`scripts/lib/artifact_validate.py`)** (#845):
  `validate_toml`, `validate_frontmatter` and `validate_json_document` check every generated
  artifact against its declared contract (`allowed-fields` / `reject-fields`, TOML parse, Opencode
  v2 JSON nesting). The same validators feed `agent_sync._finalize_agent_content` and the two
  consistency modules `consistency/artifact_contracts.py` and `consistency/model_contracts.py`,
  both registered in `consistency-check.py`; a corrupted fixture yields an ERROR and a model outside
  a configured `model-catalog` is fail-loud.
- **`config/provider-migrations.yaml` migration map** (#845): ordered write-new → verify →
  backup-old → remove-old path migrations with backup-first managed deletes (byte-exact
  `.sync-backup-<ts>` sibling, rollback by rename) while user-authored files are never removed.
  Dispatch is on the map plus the named bool flag, never on a provider name.
- **New provider contract keys** (#845): `config/ai-providers.yaml` gains `agent-discovery`,
  `surface-version`, `model-format`, `model-catalog`, `primary-role`, `model-literal`,
  `agent-transform.{tools-format,tool-name-map,allowed-fields,reject-fields,frontmatter-mechanism}`
  and `mcp-config.format` (`opencode-json`, `opencode-json-v2`, `antigravity-mcp-json`, `kimi-json`,
  `codex-toml-mcp`, `continue-yaml`); `config/provider-capabilities.yaml` gains the `skills`,
  `artifact-validation`, `artifact-validation-reason` and `mcp-remote-transport` flags (an
  `artifact-validation: false` requires a non-empty reason).
- **Opencode v2 opt-in surface** (#845): `surface-version: v2` selects `mcp-config.surface-formats`
  → `opencode-json-v2` (nested `mcp.servers`, no flat `mcp`) and `agent-transform.surface-mechanisms`
  → `opencode-native-v2`; the `primary-role` (`orchestrator`) is emitted as `mode: primary` with
  `default_agent` set, all other agents as `mode: subagent`. `v1` remains the default and its output
  is byte-frozen; the default flip is reserved for a future MAJOR.
- **Antigravity discovery gated by `agent-discovery`** (#845): the bool flag (default `false`) gates
  the `.agents/{agents,rules,skills}` discovery surface and `.agents/mcp_config.json`; the shipped
  default keeps the current `.gemini/*` paths byte-for-byte. Antigravity emits `model: inherit` and
  its MCP servers carry `serverUrl`.
- **KimiCode model namespace** (#845): every emitted Kimi model carries the `kimi-code/{model}`
  prefix and resolves through the `model-catalog`; a bare ID outside the catalog is a fail-loud
  consistency finding.
- **Mammouth reads `AGENTS.md`** (#845): `context_file`/`context_adapter_file` point at `AGENTS.md`
  and the `MAMMOUTH.md` artifact plus its routing entry are retired.
- **Codex TOML singleton-in-body fix** (#845): singleton blocks are emitted inside the agent body
  before serialisation, so the previously invalid `agent-meta-manager.toml` and
  `knowledge-curator.toml` are valid TOML; Codex MCP headers use `http_headers`.
- **Continue config validity** (#845): the generated `.continue/config.local.yaml` carries
  `name`/`version` (schema-valid), the invalid `roles: [..., "agent"]` enum value and the dead
  top-level `agents:` block are removed/corrected, and MCP request headers use
  `requestOptions.headers`.
- **Config-backed pipeline notation** (#845): `config/delegation-syntax.yaml` is the single source
  for provider notation, a missing block fails loud instead of falling back to the Opencode `task()`
  default, and Copilot is added to the provider registry.
- **Provider-audit scenarios 64–72** (#845): nine executable scenarios (Codex TOML validity,
  KimiCode model namespace, Mammouth tools map, Copilot artifact paths, Antigravity discovery paths,
  Opencode v2 surface, bootstrap marker convergence, all-provider `--check` idempotency, Continue
  config validity), each with its own assert script and a scenario-registry row.
- **Provider-agnostic sweep guard** (#845): `tests/test_provider_agnostic_dispatch.py` sweeps all of
  `scripts/lib/**/*.py` for `if provider ==` / provider-name literals and for `surface-version`
  comparisons in writer code.
- **Capability-gated intent-routing mandate (#264)**: `route_intent` is only mandated
  in the orchestrator's §3 when the harness registers it as a callable tool
  (`route_intent_tool` in `config/provider-capabilities.yaml`); otherwise the
  orchestrator derives the route from the generated routing rules and must not invent
  a tool call. All 9 providers ship explicit `route_intent_tool: false` (conservative;
  a live `route_intent` acceptance proof is required to flip one to `true`), so no
  runtime blocks on an unregistered tool.

### Changed
- **Multi-line `variables:` values now keep the indentation of their use site (consumer-visible
  only if you set multi-line values)**: a multi-line value substituted at an *indented*
  placeholder is emitted with every content line carrying the placeholder's indentation —
  previously only the first line did. The affected production placeholders are
  `EXTRA_VOLUMES` / `EXTRA_ENV_VARS` / `EXTRA_VOLUME_DEFINITIONS` in
  `agents/2-platform/sharkord-docker.md` and `GH_ASSETS` in
  `agents/2-platform/sharkord-release.md` (both files have no `extends:`, so their body is
  not YAML-dedented before substitution). For docker-compose list items and shell line
  continuations this is a correction; blank lines stay blank, so no trailing whitespace is
  emitted. Single-line values and column-0 / inline placeholders are unchanged — the default
  render stays byte-identical.
- **Review rule indexes carry `blocking` and `claim_type` per rule** (`backend`, `frontend`,
  `database`, `security`, `ui`, plus the new `ai` domain). `blocking` marks whether a finding must
  be resolved before merge; `claim_type` separates findings that are falsifiable from those needing
  expert judgement. Both follow the "comment signals" taxonomy in Braganza, *"Looks Good to Me"*,
  ch. 6 — which reports the author's team **abandoning** MoSCoW because the Must/Should boundary
  proved too blurry, in favour of explicit needs-change / levelup / nitpick signals.
- **DoD presets `full` and `spec-driven` activate `ai-security-review`, `prompt-governance` and
  `lifecycle-ownership`.** These three flags were `false` in all seven presets, which meant the
  existing AI roles could never run in a default configuration. The five lighter presets are
  unchanged.
- **Eight existing roles strengthened with literature-anchored rules** (each 1–2 sentences, no
  rewrites, each with a version bump): `validator` and `se-verifier` (verifiable-vs-plausible
  distinction and the zero-product rule for L1–Ln), `principal-developer` (context over syntax as
  the reason this tier exists), `code-reviewer` (per-finding blocking level and claim type),
  `prompt-engineer` (the three guardrail classes — security boundaries, behavioural limits, scope
  restrictions — plus the counterweight that no universal prompt formula exists), `sre-engineer`
  (hands the agent-behaviour SLI family to `ai-observability-engineer`), `data-engineer` (declares
  the RAG/embedding gap and hands it to `rag-engineer`), `orchestrator` (single-responsibility
  justification and review-loop governance), `api-specialist` (Swiss-Army-Knife rule and the MCP
  N×M boundary — MCP standardises the interface contract, not the tool semantics).
- **Registry wiring for the new roles**: `llm-evaluator`, `rag-engineer`, `ai-governance-engineer`
  and `ai-observability-engineer` are registered in `config/role-defaults.yaml` with routing
  keywords, timeouts and handoff contracts; `prompt-engineer` gained its first `handoff` block, and
  `developer`, `data-engineer`, `sre-engineer`, `feedback` and `control-framework-assessor` now
  declare the new contracts as inputs so no handoff is silent.
- **Role activation is gate-driven for `validator` and the developer tiers (consumer-visible —
  audit your `project.yaml` before upgrading)**: the per-role activation decision now resolves
  from the single `activation_groups` default table in `config/role-defaults.yaml` instead of the
  historic name-prefix heuristic. Two defaults are off unless the project opts in:
  - `validator` is gated by `roles_membership: any [validator]`. A project whose `project.yaml`
    has **no** `roles:` list (the key is optional in `config/project-config.schema.json`) used to
    get a generated `validator.md` anyway — every role outside the `se-`/`knowledge-` prefixes was
    unconditionally enabled. It is no longer generated unless `validator` is listed.
  - `principal-developer` is now a member of the `developer_tiers` group
    (`role_patterns: [junior-developer, senior-developer, principal-developer]`). The membership
    change is routing-side; it also reaches the **generation** path, so a project listing
    `principal-developer` without `junior-developer` and `senior-developer` (the `mode: all`
    predicate) loses the generated file.
  No project.yaml change is required for projects that already list their roles explicitly;
  run `sync.py --validate` after upgrading to see which roles the gates drop.
- **Breaking — Copilot artifact paths migrated default-on (consumer-visible — re-run `sync.py`
  after upgrading)**: Copilot's generated artifacts move to `.github/agents/*.agent.md`. The legacy
  `.github/copilot/agents/` and `.github/copilot/rules/` directories and `.github/copilot/COPILOT.md`
  are removed backup-first by the migration map (`config/provider-migrations.yaml`, no flag), so the
  old paths disappear for consumers who do not regenerate. This default-on removal is the reason this
  release is a MAJOR bump.
- **Sync-time validation is fail-loud (`--check`/`--validate` rc policy)** (#845): an artifact
  contract violation makes `sync.py --validate` return rc 1 (a normal sync stays rc 0 and logs
  `[WARN] artifact-contract:`), and the permanent `--check` false-positives plus the entry-file
  run1→run2 drift are fixed — after a clean scratch sync `--check` is rc 0 and
  `sha256(run1) == sha256(run2)` (a managed-block edit is rc 1, an out-of-block edit rc 0).
- **Transform and model contracts** (#845): Mammouth `tools:` is emitted as a map (never a YAML list),
  Antigravity tool names resolve through the data-driven `tool-name-map` (`Read`→`view_file`,
  `Write`→`replace_file_content`, `Grep`→`grep_search`, `Bash`→`run_command`), and `resolve_model`
  applies `model-format` exactly once with `ai-providers.yaml model-tiers` authoritative over preset
  tiers.
- **Bootstrap markers are scoped per provider** (#845): Gemini and ZCode each carry one scoped marker
  pair (fixing the marker collision), the legacy unscoped pair is migrated and rebuilt per provider,
  scoped markers of inactive providers are removed, and user notes outside the markers survive.
- **Path migration and pending-write stabilisation** (#845): generated files move write-new → verify
  → backup-old → remove-old with a production-wired final-content diff; Gemini discovery paths
  migrate only when `agent-discovery` is enabled.
- **Provider-neutral template body references** (#845): the five `.claude/`-prefixed refs in
  `agent-meta-manager`, `agent-meta-scout` and `release` are rephrased provider-neutrally and no
  longer appear in non-Claude generated bodies.
- **Regenerated 27-file artifact drift** (#845): the repo is drift-free (`sync.py --check` rc 0) with
  the new `{{AGENT_META_VERSION}}` embedded in every generated artifact.

## [1.2.0-beta.2] - 2026-09-13

### Added
- **Native Spec/Plan workflow**: requests are classified up front (Spike / Bounded /
  Architectural) and routed through an explicit approval gate before implementation. Plans are
  authored against a fixed contract, tracked in a plan-ledger, and pipelines act as the single
  routing source. Request grouping is configurable via `config/spec-plan-groups.yaml` and
  resolved by a bundle resolver; `sync.py --validate-spec-plan` validates the configuration.
  Artifacts use provider-neutral paths (`docs/specs`, `docs/plans`, `docs/spikes`), and a
  coverage matrix maps requests to the plan/spec artifacts they produce.
- **Progress and ledger system**: sessions automatically re-hydrate and resume from the persisted
  progress state, backed by stable cross-session plan/task identities. A machine-written plan
  ledger with a drift check keeps plan status honest, a two-stage task review with a rounds cap
  gates task completion, and a mandatory root-cause gate precedes every bugfix.
- **Configurable progress and checkpoint paths**: new `progress.dir` and
  `progress.checkpoint-dir` project keys (defaults `.meta-viz/progress` and
  `.meta-viz/checkpoints`) let projects relocate the runtime progress store and the
  per-session checkpoint files; relative paths resolve against the project root, and the
  framework defaults keep the historical layout.

## [1.2.0] — 2026-09-12

### Added
- **Repo-Containment PreToolUse hooks (`repo-containment.sh`, `repo-containment-impl.sh`)**: wrapper/impl pair confining Write/Edit to the project root, with the `.tmp` scratch sink as the sanctioned exception (PR #781).
- **Provider-agnostic `commands` capability for all 9 providers (#735, #743)**: added a
  `commands` flag to `config/provider-capabilities.yaml` (Claude/Gemini/Opencode/Continue `true`;
  Copilot/Mammouth/Codex/ZCode/KimiCode explicit `false`), replacing 22 `if provider ==`
  equality branches (AST-verified: 0 remaining) with capability-driven dispatch.
- **Checkpointing and per-provider chat push (#743)**: wired `CHECKPOINTING_BLOCK` into
  `agents/1-generic/orchestrator.md` and its snippet (`true` renders, `false` suppresses);
  chat push is now resolved per provider via the `hook_protocol` capability instead of a
  global hook-support check.
- **Backup-before-overwrite for drifted generated files (#734)**: new `backup_drifted_files()`
  in `scripts/lib/generated_file_drift.py` writes a `.sync-backup-<YYYYmmdd-HHMMSS>` sibling
  before overwriting a drifted file (fail-soft; no-op in dry-run). A managed `.gitignore`
  entry `*.sync-backup-*` keeps the backups untracked.
- **Admin-UI writable config sections and accessibility (#730)**: `scripts/admin-server.py`
  accepts `hooks`, `debug-mode`, `tier-overrides`, `mcp-role-overrides` and `backup` as
  writable sections; `docs/ui/admin-ui.html` gains views for them plus labels, `aria-live`,
  focus handling and visible save errors.
- **Reverse role-registry drift check (#736)**: `--audit-config` now reports
  `role_defaults_without_template` for registry roles whose template file is missing.
- **Subagent permission policy and Admin-UI Git/Auto-Commit sections (#768)**: new
  `subagent_permissions` mode (`strict`/`warn`/`off`, default `off`, provider overrides)
  wired into prompt rendering, the sync validator and the consistency check (declarative,
  no runtime dispatch gate); the Admin UI gains Subagent-Permissions, Git and Auto-Commit
  sections backed by a new top-level `git` config block whose values are the canonical
  source of the generated `GIT_*` variables.
- **Opt-in `agent-meta` README version badge (#782)**: new `readme.badges` type
  `agent-meta`, rendered from the sync-embedded `{{AGENT_META_VERSION}}` by the
  `documenter` role (single writer); unknown values render as `unknown` and link to
  `/releases`.
- **HACS entity-name localization contract and rename migration (#763)**: 2-platform HACS
  rules now require `_attr_has_entity_name`/`_attr_translation_key` (hardcoded
  `_attr_name`/`name` literals banned) and an entity-registry rename migration
  (`async_migrate_entries`) as a MAJOR/breaking-change trigger; `hacs-code-reviewer` 2.0.0,
  `hacs-release` 1.1.0, `hacs-developer` 1.3.0 plus scenario 49.
- **Conventions-migration framework, HACS developer guide, quality-gate docs and browser
  editor tests (#742, #726, #675, #677, #318)**: extensible `config/conventions-presets.yaml`
  framework with a duplicate-safe `exact-timestamp` release cutoff (#726); HACS
  integration-development rule and scaffolding-agent updates (#675, #728, #729);
  quality-gate/release-candidate pipeline documentation (#677); Playwright browser tests for
  the admin project form editors (#318).

### Changed
- **Repo-Containment ("prison mode") is active by default (behavior change)**: agent write
  access is now confined to the project root, with the auto-provisioned `.tmp` scratch sink as
  the only sanctioned exception. On the next sync, hook-capable **active** providers
  register the `repo_containment` PreToolUse hook, so existing projects get a blocking guard
  without opting in. Opt out per project with `repo_containment.enabled: false` in
  `.meta-config/project.yaml`, or per provider with
  `repo_containment.provider-overrides.<Provider>.enabled: false`. The first sync materializes
  an explicit `repo_containment` block (defaults `enabled: true` plus tmp-sink defaults) into
  `.meta-config/project.yaml` when it is missing — idempotent, and it makes both the behavior
  change and the opt-out visible instead of hiding them behind a schema default.
- **Null config blocks, version and provider enum (#741, #731, #732)**: explicit `null`
  blocks (e.g. `project: null`) are normalized so config loading no longer raises
  `AttributeError`; the `agent-meta-version` default is derived from `VERSION`; the
  `ai-providers` enum is generated from `config/provider-capabilities.yaml` (9/9). An unknown
  provider is now rejected with a clear error instead of silently falling back to Claude.
- **Config defaults and warnings hardening (#733, #737, #736)**: added `_VARIABLE_FALLBACKS`
  for the 8 leaking variables (`COMMUNICATION_LANGUAGE`, `USER_INPUT_LANGUAGE`,
  `DOCS_LANGUAGE`, `INTERNAL_DOCS_LANGUAGE`, `CODE_LANGUAGE`, `PROJECT_GOAL`,
  `PROJECT_LANGUAGES`, `CODE_CONVENTIONS`); `fill_defaults()` now populates `project.short`;
  removed the stale `feature` role reference and documented `provider-expert` as a wrapper
  base (not a selectable role).
- **CI scenario and drift gates (#740, #739)**: corrected scenario 21 to the mode-independent
  auto-commit contract and wired the scenario suite into CI; added `sync.py --check` to
  `validate.yml`; added `VERSION`/`CHANGELOG` to the `orchestration-test.yml` paths-filter.
- **LF enforcement for orchestrator-guard hooks (#712)**: added a `.gitattributes` rule for
  `hooks/1-generic/orchestrator-guard*.sh`.
- **Reproducible `AGENT_META_DATE` (#752)**: the generated date resolves via
  `SOURCE_DATE_EPOCH`, then the release date from `CHANGELOG.md`, then `now()`.

### Fixed
- **`--check` false-positive drift on absent provider roots (#752)**: `sync.py --check` no
  longer counts legitimately absent gitignored provider target roots as drift (fail-open);
  the direct-writer paths were aligned to match.
- **Silent admin config rejection and partial writes (#730)**: writes to non-writable
  sections now return an explicit 4xx instead of being silently dropped, and the previously
  discarded `PUT /api/config/project` merge result is now validated and persisted.
- **Inverted jsonschema hint (#737)**: corrected the warning that instructed users to
  "fix or install jsonschema" in the wrong direction.
- **`--audit-config` side effects removed (#738)**: `--audit-config` is now read-only
  (`_SyncContext.read_only`) and no longer creates `env.*` or `sync.log` files.

## [1.1.0] — 2026-09-10

### Added
- **Platform-preset cascade for project.yaml defaults (#709)**: new `platform` key
  in `project.yaml` defines a per-provider hierarchy of preset templates (e.g.,
  Claude defaults differ from Gemini defaults). Cascade resolves in order:
  provider-default YAML → global platform bundle → project config, allowing
  projects to opt into sensible provider-specific defaults without boilerplate.
- **Provider-neutral live progress channel (#721)**: new `.meta-viz/progress/current.md`
  file (moved from `.claude/progress/`, now provider-neutral). Tier-A providers
  (Claude, Gemini with verified hook protocols) write a cumulative session table;
  Tier-B providers (all others) append new checkpoints with automatic rotation at 200KB.
  Human-readable `Agent | Task | Status | Pipeline/Stage` format, written on every
  checkpoint save (issue #682 §6).
- **Scenario testing catalog expansion**: 48 new scenarios in `tests/scenarios/`
  covering representative provider/preset/feature combinations. All 21 core scenarios
  now include file-existence assertions.

### Fixed
- **Security: auto_commit YAML-bool trap, broken backup log stub (#700)**: fixed
  a parsing bug where `auto_commit: yes`/`no` (YAML booleans) were silently converted
  to `true`/`false`, breaking admin-server logs and DoD output format. Also fixed
  missing backup-log timestamp stub that could cause fatal JSON parse errors on rollback.
- **reconcile use-orchestrator.md with AUTO_COMMIT_BLOCK guard + admin-server FD leaks
  (#704)**: corrected the documented orchestrator responsibility set to match the
  AutoCommitBlockGuard activation; fixed file descriptor leaks in admin-server
  daemonization that prevented graceful shutdown and log rotation.
- **compute eligible_roles independent of auto-commit mode (#706)**: role eligibility
  (which write-capable agents can commit) is now computed at role-load time independent
  of auto_commit config, fixing a regression where role eligibility could flip unexpectedly
  during config validation runs.
- **Hook enablement consistency checks (#712, #714)**: added `check_hook_enablement_consistency`
  to `sync.py --validate`. Hooks marked enabled (in their own YAML header or via project.yaml
  override) but missing from disk (#712) or unregistered in provider registration artifacts
  (#714) now fail validation with clear diagnostics, preventing silently-broken hooks.
- **warn when a pre-existing rule shadows gitignore block (#713)**: added `detect_shadowed_provider_roots`
  to gitignore sync stage. When a managed provider block is disabled, any pre-existing rule
  that still matches the provider's agents_dir is now flagged with a warning, preventing
  silent untracking of generated output.
- **render actual PROJECT_STRUCTURE in full-mode CLAUDE.md (#715)**: full-mode context files
  now emit the actual `{{PROJECT_STRUCTURE}}` value when set, instead of just a generic lazy-load
  pointer. Compact mode preserves the byte-for-byte #437 pinned behavior.
- **force literal-block YAML style for multiline values (#717)**: PyYAML's default folding
  of embedded newlines to spaces in multiline strings is now overridden to preserve formatting
  in generated `.mcp.json` and other multiline configs.
- **warn (never remove) stale mcpServers key, flag secrets (#719)**: stale `mcpServers` keys
  from before the `.mcp.json` migration are now flagged for manual cleanup (never auto-removed).
  Literal secrets (Bearer tokens, API keys) in the key are escalated to `[SECURITY]` warnings.
- **plugin status experimental instead of FAIL (#701)**: local setup gaps (missing plugin deps,
  unresolved `snippet://` references) are now marked `Experimental` instead of `FAIL`, allowing
  plugin use to proceed while flagging incomplete setups in validation reports.
- **classify FileNotFoundError and unresolved secrets as UNAVAILABLE (#725)**: fixed sync
  pipeline failure classifications. `FileNotFoundError` on template/rule reads and unresolved
  secret placeholders now correctly report as `UNAVAILABLE` (data problem) not `ERROR` (internal bug),
  improving remediation diagnostics.

## [1.0.0] — 2026-09-08

### Changed
- First stable release — agent-meta exits its 0.x beta series.

### Added
- **Auto-commit tiers (#694)**: opt-in `auto_commit` config (`off`/`suggest`/
  `auto`/`custom`) lets write-capable agents commit directly instead of always
  delegating to the `git` role. `suggest` has agents propose a commit message
  in their own report (never blocking, never running git itself); `auto`
  commits when any of 5 selectable trigger conditions fires
  (`task-boundary`, `per-edit`, `context-pressure`, `file-count-threshold`,
  `custom`); `custom` hands the entire decision to a project script. Role
  eligibility is capability-derived (Edit/Write in a role's own template
  `tools:`, never a hand-maintained list). Enforced two ways: prompt
  instructions on all 9 providers, plus hook authorization
  (`orchestrator-guard-impl.sh` v1.2.0) on the 4 providers with PreToolUse
  hook support (Claude, Gemini, Mammouth, Codex) via a generated
  `.meta-config/auto-commit-allowlist.json`. `push`/`tag`/branch management
  remain exclusively the `git` role's job; the destructive-operation gate
  (issue #516) is completely unaffected. Optional secret scan
  (`sync.py --scan-staged`, `secret_scan: true` default) gates every
  auto/custom commit.

## [0.101.0-beta.6] — 2026-09-07

### Added
- **Scenario-testing catalog & `agent-meta-manager` schema audit** (#690): new
  `tests/scenarios/` catalog (`registry.md`, `run.sh`, 17 `project.yaml` configs)
  covering representative provider/preset/feature combinations for manual and
  CI-adjacent smoke testing. `agent-meta-manager.md` audited against the full
  `project.yaml` schema — it previously documented only ~10 of the 58 top-level
  keys and never mentioned `sync.py --validate`; both fixed with new workflow
  sections that point the agent at the schema as the authority and make
  `--validate` mandatory after any `project.yaml` change.
- **Governance quick-wins (#682)**: README structure standard (`readme.badges`/
  `readme.warnings`/`readme.sections` in `project.yaml`, new
  `templates/configs/README-template.md`, additive `documenter.md` §5 rewrite —
  same managed-block, non-overwriting principle as `.gitignore`); `.gitignore`
  now protects every active provider's own context file (`CLAUDE.md`,
  `AGENTS.md`, `MAMMOUTH.md`, ...) from the `settings` category unconditionally,
  fixing a bug where only Claude's context file was ever exempted; `sync.py
  --setup` offers (not silently defaults) typical secret-pattern `.gitignore`
  entries (`.env*`, `*.pem`, `*.key`, `credentials*.json`, `secret*.y*ml`);
  mandatory orchestrator status-table reporting after every batch member and
  BARRIER point (issue #678, new `snippets/orchestrator/status-table.md`,
  `{{STATUS_TABLE_BLOCK}}` in both `use-orchestrator.md` and `orchestrator.md`);
  `CheckpointStore.save_checkpoint()` now also overwrites
  `.claude/progress/current.md` with a human-readable, non-historized
  `Agent | Task | Status` snapshot.
- **Generated-file drift detection**: `sync.py` now warns when a generated file
  (agent/rule/hook/command/skill/pipeline-detail) was manually edited since the last
  sync -- the file is still regenerated as usual, this is warn-only. New
  `scripts/lib/generated_file_drift.py` compares each active provider's managed
  files against a content-hash baseline (`.meta-config/generated-file-hashes.json`)
  before the write stage, then recaptures the baseline after every writer has run.
  Enabled by default; set `drift-detection.enabled: false` in `project.yaml` to
  disable. Expected manual edits can be silenced via glob patterns in
  `.meta-config/drift-allowlist.yaml`.
- **Central orchestrator prompt consolidation for the phase-4b backends** (#264, #265,
  #266, #267, #506): `template-orchestrator` (v7.12.0 → v7.13.0) merges all five
  prepared handoff notes into one coherent prompt. §3 intent routing now references
  the generated `route_intent` tool definition via the new `{{INTENT_ROUTING_TOOLS}}`
  placeholder (#264 — prose routing table removed, data lives in the structured
  definition; §4 routing policy points at `routing.rules` instead of duplicating
  keywords). §6 FANOUT/PARALLEL_GROUP dispatch mechanics are capability-gated via the
  existing PAL placeholders (`{{#if PAL_FANOUT}}` block renders each provider's
  verified batched-dispatch / explicit-collect / sequential-fallback patterns — no
  invented `fanout()` tool) plus static pre-dispatch validation wording (#265); the
  "Parallel" line now defers to the static file-affinity analysis
  (`scripts/lib/file_affinity.check_file_overlap`) instead of telling the model to
  guess overlaps (#266). §7 BARRIER protocol documents results-as-tool-data, the
  status-aware `||| agent=... |||` wrapper, the "exactly N tool responses" completion
  rule, partial handling and the hard-interrupt semantics (#265). §9 adds the
  Summarization-as-a-Contract section: compact worker summaries only, raw output
  archived via `CheckpointStore.save_raw_output` under
  `.meta-viz/checkpoints/<session-id>/`, never re-requested (#267). §6 documents the
  sync-call contract for orchestrator↔worker expectations (#506). Placeholder wiring:
  `build_variables()` prerenders the per-provider routing tool definition
  (`_INTENT_ROUTING_TOOL_DEFS`), `agent_sync._build_provider_vars()` resolves it per
  synced provider (empty for providers without a `handoff_format` capability —
  fail-soft, drift surfaces via the consistency checks), placeholder registered in
  `placeholders._BUILTIN_VARS`.
- **FANOUT/BARRIER backend contract — plan, validation, capability flags** (#265):
  generation-time half of the hard-interrupt reframe (design spike
  `docs/spikes/2026-09-06-issue-265-async-fanout-spike.md`). New
  `scripts/lib/orchestration.py` (FanoutTask/FanoutPlan/BarrierEntry/BarrierResult,
  `validate_plan` with cycle/deadlock/over-commitment/file-overlap checks,
  `execute_plan` over an injected `Dispatcher` seam, #267-compatible
  `summarize_result`, §7-compatible `render_barrier_result`); capability keys
  `fanout_mechanism` + `barrier_collect` in `config/provider-capabilities.yaml`
  for all 9 providers (getter trio in `delegation_syntax.py`); dry-run engine
  repurposed as plan validator (hardcoded provider list removed — capability
  lookup); new post-sync drift check `scripts/lib/consistency/fanout_contracts.py`;
  delegation-syntax ZCode/Copilot fanout text aligned to sequential-fallback.
  Runtime dispatch/injection stays a documented harness dependency.
- **Static file-affinity analysis for pre-dispatch overlap checks** (#266): new
  `scripts/lib/file_affinity.py` — deterministic task-level analysis (stdlib-only)
  replacing the LLM-guided "check file ranges for overlap" step before FANOUT /
  PARALLEL_GROUP dispatch. `check_file_overlap()` returns the #266 result dict
  (`{"safe": [...], "conflict": [(task_a, task_b, [files]), ...]}`) from a 4-step
  pass (regex file references, Python-AST symbol index, Markdown/YAML
  doc-reference pass, import-graph via `analysis.FileAffinityAnalyzer`);
  `extract_file_references()` and `format_overlap_report()` support the callers;
  the `BOUNDARY_NOTE` constant documents the boundary — analysis here, real
  enforcement (call before actual dispatch) harness-side. The dry-run engine
  (`tests/orchestration/dry_run/engine.py`) sequentializes conflicted tasks before
  simulated FANOUT/PARALLEL_GROUP; `orchestration.validate_plan` consumes the
  result via its `file_overlap` seam.
- **Raw-output archive for Summarization-as-a-Contract** (#267): `CheckpointStore`
  gains a two-level session layout — `<session-id>.json` (structured checkpoints,
  summaries) plus a `<session-id>/` directory holding the COMPLETE raw worker
  output per task. New API: `save_raw_output()` (append-only, uuid suffix,
  filename sanitization), `load_raw_output()` (fail-soft), `list_raw_outputs()`;
  the module archives bytes only (harness boundary per docstring — BARRIER parsing
  and raw-output stripping stay harness-side). #267's summarization contract itself
  ships with the #265 backend (`orchestration.summarize_result`, `execute_plan`
  store/session wiring) and the orchestrator §9 section above.
- **Intent routing as structured tool definitions** (#264): the per-provider
  `route_intent` tool definition is generated data, not prose —
  `build_routing_tool_definitions_for_providers()` /
  `render_routing_tool_definition()` (`scripts/lib/agents.py`) serialize it
  mechanism-keyed on the provider's `handoff_format` capability key (fail-closed
  on unknown formats; empty string for providers without `handoff_format` —
  currently never visible, every provider defines one). The template side
  (`{{INTENT_ROUTING_TOOLS}}` wiring, §3 rewrite) ships with the orchestrator
  consolidation above; consuming the definition as a callable tool is
  provider/harness behavior (documented follow-up).
- **Background-Process Guard for all Bash-capable agents** (#506): every
  `1-generic` template with shell/container capability in its `tools` list
  (48 templates, each bumped minor) now carries an `<output-guard>` section —
  an agent that starts a background process MUST actively wait for its
  completion within its own turn (`docker wait`, polling with timeout,
  synchronous blocking). Its turn must NEVER end on a "waiting" placeholder:
  the final tool result is the only channel to deliver evidence and exit
  codes to a synchronous caller — there is no reactivation after the turn.
  Concrete blocking examples included: `docker wait` pattern (tester,
  docker, devops-engineer, e2e-tester) and a polling loop with timeout
  (developer, code-reviewer).
- **Post-merge branch cleanup for the generic `git` agent** (#496): after a successful
  merge, `template-git` (v1.5.0 → v1.6.0) now offers to clean up the merged source
  branch — list merged candidates (local + remote), verify merged state
  (`git merge-base --is-ancestor`), signal-based keep/delete decision (open TODOs,
  disabled code, "Phase 2"/follow-up hints → keep; default delete) with user
  confirmation, safe local delete (`git branch -d`, never `-D`), remote delete
  (`git push origin --delete`) only after explicit user confirmation, hard safety
  rules (never `origin/main`, `origin/HEAD`, unverified branches, force flags) and
  stash protection for dirty working trees. Restores behavior lost in the a0886e1d
  XML consolidation (originally delivered via Issue #52).
- **`ai-security-guardian` agent** (#667): AI-specific security risk detection for
  AI-generated code — hallucinated dependencies (slopsquatting), fabricated IAM
  actions, insecure AI defaults (debug mode, permissive CORS, default credentials),
  brittle conditional security checks, phantom API endpoints and leaked
  training-data patterns. Read-only; complements `security-auditor` (OWASP) and
  `dependency-auditor` (supply chain) rather than replacing them.
- **`prompt-governor` agent** (#668): prompt governance that treats prompts as
  source code — PromptBOM metadata (model + prompt + parameters), append-only
  audit trail, provenance tracking, prompt version drift detection and banned
  unsafe prompting patterns (skip auth, ignore security, bypass validation).
  Read-only on prompts; complements `prompt-engineer` (design) and does not
  replace it.
- **`app-lifecycle-governor` agent** (#669): app lifecycle governance — ownership
  audit with orphan detection, SLA validation, data classification checks,
  lifecycle-stage tracking (prototype → staging → production → deprecated →
  archived) and deprecation-plan verification. Read-only; findings are
  recommendations, not mandates.
- **`test-executor` agent** (#517): lightweight execution-only role for existing
  test suites — born from a ReqogniLoom near-OOM incident (3 parallel design-tier
  test agents on a 5.8 GB host). Cheapest model tier (`nano`), `Read` + `Bash` only,
  no code generation / architecture-context modification / deployment tools.
  Structured result reporting (pass/fail/skip counts, exit codes, stdout excerpts)
  and a mandatory Sync-Turn-Contract (#506): background processes are awaited
  within the turn (`docker wait` / bounded polling) — never ends the turn with a
  "waiting" placeholder. Test design stays with `tester`; delegation guidance in
  `docs/guides/features/agent-delegation-map.md`.
- **Phase-4b documentation** (#264–#267, #506, #517): consolidated harness-dependency
  and follow-up documentation `docs/plans/2026-09-06-issue-674-phase4b-harness-dependencies.md`
  (per issue: implemented in agent-meta vs. harness-side dependency vs. issue-ready
  follow-up items, plus the cross-issue dependency chain — #267 enforcement hangs
  off the #265 backend, #266 enforcement off a harness dispatch hook, #264
  consumption off provider function-calling); design spike #265
  `docs/spikes/2026-09-06-issue-265-async-fanout-spike.md` (§7 = normative harness
  dependency); Phase-4b status note in `docs/plans/2026-09-05-issue-674-roadmap.md`.

## [0.101.0-beta.5] — 2026-09-04

### Fixed
- **Guard security hardening** (#590, #591, #602): three tokenizer/RCE guard fixes (subcommand-hiding, git-mutation detection, validation gaps).
- **Config loader performance** (#553): added `@lru_cache` to five framework config read paths, reducing full test-suite duration from ~404s to ~146s (64% reduction).
- **Environment issue documentation** (#554): documented and isolated environment-specific test behavior.

### Changed
- **Guard trade-off documentation** (#592): tokenizer-based mutation detection documented as convention boundary (fail-closed against accidental misuse, not deliberate bypass).

## [0.101.0-beta.4] — 2026-09-03

### Changed
- **August-Refactoring-Roadmap** (10 waves, #563–#615 et al.): `sync.py`'s `main()`
  if/elif chain replaced by a `_dispatch()` table over `_SyncContext`/`_handle_*`
  handlers; oversized `scripts/lib` modules split along service boundaries
  (Template/Pipeline/Reflection/Models services, Auth/Audit services + route
  tables); several latent import cycles resolved; `admin-server.py`'s
  `RoleDefaultsEditor` (#611) fixed and generalized (clean list/dict-helper
  split, not just patched for the two original repro cases); persistence
  robustness batch (#573, #576, #580, #582, #583, #586, #566, #568, #571,
  #574, #578).
- **Provider-Agnostik-Kampagne** (Waves A–D, #625–#638): new
  `provider-agnostic` lint rule + credo forbidding `if provider == "Name"`
  branching in syncer code (#625, #626); provider truth-source duplication
  eliminated across `scripts/lib` (#627, #628); `provider_transform.py`'s
  6-way provider `elif` replaced by a data-driven `_apply_agent_transform()`
  dispatcher (#629); hook-protocol gating, provider self-health checks and a
  Claude self-lockout fix (#630–#633).

## [0.101.0-beta.3] — 2026-08-27

### Changed
- **Build and version sync** (#latest): rebuilt agent templates via sync.py.

## [0.101.0-beta.2] — 2026-08-26

### Fixed
- **Admin UI usability and documentation improvements** (#545): enhanced user experience
  and updated documentation for the Admin interface.
- **Admin UI critical bugfixes** (#545): resolved agent template resolution bug, fixed
  pricing overlay display for opencode-go models, corrected conventions-overrides rendering,
  and added missing confirmation dialogs.

## [0.101.0-beta.1] — 2026-08-26

### Added
- **Context-file compression** (#540, #543): automatic `context_file` density control via
  `context_file.mode: compact` — instruction-preserving compression that keeps stack,
  build and entry-point values inline while collapsing overviews to pointers. Reduces
  context footprint by ~40–50% for large code bases. Configurable per project via
  `project.yaml` `context_file.mode` or toggle via Admin-UI.

### Fixed
- **Routing evaluation gate hardening** (#537, #538, #539): three CI routing-eval test
  failures from stale Anthropic model IDs and missing intent-routable-signal edge cases.
  All eval test paths now use `models.list()` for live model discovery instead of
  hardcoded IDs; added negative test cases for router confusion scenarios.

## [0.100.0] — 2026-08-23

### Added
- **HACS platform preset** (`feat/hacs-platform`): five `2-platform` agent overrides that
  extend the generic agents via composition and inject HACS-specific rules — `hacs-developer`
  (manifest/hacs.json hygiene, Coordinator/Store architecture, Config/Options-Flow, CI,
  release discipline, debugging checklist), `hacs-code-reviewer` (10-gate checklist),
  `hacs-tester` (HA-free pytest via fake-package, logic-first then E2E),
  `hacs-devops-engineer` (`hacs/action` + `hassfest` CI from day one, release triad),
  `hacs-release` (tag↔manifest sync, `VERSION` only with migrator).

## [0.99.0] — 2026-08-22

### Added
- **Review-Agent Fleet** (#530, #531): four domain reviewers (`frontend-reviewer`,
  `backend-reviewer`, `database-reviewer`, `ui-reviewer`) plus `security-auditor` v2.0.0
  refactor onto the fleet contract — rules-index-driven two-pass reviews with evidence
  schema (rule_id + CWE/OWASP mapping + snippet + fix), ≥80% confidence gate and
  MERGE_SCORE. Ships default rules indexes (`config/review-rules/*.yaml`), the reviewer
  routing matrix (`config/routing/reviewers.yaml`) and explicit model tiers per role.
  Concept and design principles P1–P6: `docs/concepts/planned/review-agent-fleet.md`.

## [0.98.0] — 2026-08-22

### Added
- **`model-inherit-main-chat` super-override mode** (#524, #525): second super-override
  alongside `model-override-all` — all agents inherit the main-chat model instead of a
  fixed model ID (empty `model:` field). Hard per-provider exclusivity against
  `model-override-all` with fail-fast validation (exit 1). Wired through sync resolution
  (`scripts/lib/roles.py`, `scripts/lib/config.py`, `scripts/lib/agents.py`), project.yaml
  schema, Admin-UI toggle and `POST /api/model-inherit` endpoint (provider whitelist),
  template §8b.2 (`agent-meta-manager` v1.13.x) and skill documentation.
- `model-override-all` reversible provider blast (#522): pin every agent of a provider to
  one model via a single project.yaml key (promo/cap mechanism).
- Configurable naming/release convention profiles (#520, #521): per-project commit,
  branch and release naming conventions.

### Fixed
- Review findings for the inherit mode (#525): Continue provider now honors
  inherit-main-chat instead of falling back to role-defaults; admin endpoint validates
  provider keys (400/409 on unknown values); warning on silently ignored per-role
  `model-overrides` under active inherit; corrected conflict-handling note in the
  manager template; negative test coverage for the Continue fallback path.
- Bug batch (#519): preserve user content in CLAUDE.md "Own Notes" section, stale
  skill-repo submodule pin reverted by sync, design-limits documentation.

## [0.97.0] — 2026-08-16

### Fixed
- `hooks/1-generic/orchestrator-guard.sh` (v2.2.0 → v2.3.0): two related BASH_CMD-parsing
  robustness bugs. `statements()` didn't split on newlines (#508) — a multi-line read-only
  command with no `&&`/`;`/`|` between the lines stayed one statement, and `shlex.split()`
  then flattened both lines into a single token stream, so the second line's tokens could be
  misread as positional args to the first line's `git` subcommand (e.g. `git branch
  --show-current` followed by `git status --short` looked like a branch-create mutation) —
  false-positive block. The sentinel-based agent-identity check used `head -n1` on the raw
  command (#503) — a `BASH_CMD` starting with a leading blank line before the
  `#agent-meta:agent=<name>` sentinel made `head -n1` grab the empty first line instead,
  missing the sentinel and incorrectly blocking a legitimate delegated mutation. Both fixed;
  2 new parametrized cases added to `tests/test_orchestrator_guard_hook.py` (30 total).
- Provider frontmatter fields (`version`, `prompt_mode`, `generated-from`) generated by
  `sync.py` rejected outright by some providers/validation layers with a strict
  agent-definition schema — e.g. a Console Go validator in front of an Opencode-shaped agent
  schema (#505). New opt-in `strip_fields` support in `build_frontmatter()` and
  `_transform_frontmatter_for_opencode()` (`scripts/lib/agents.py`), configured per project
  via the existing `provider-options` block in `.meta-config/project.yaml` (same mechanism
  Continue's `generate-prompts`/`prompt-mode` already use — no agent-meta core change needed
  per consumer provider quirk):
  ```yaml
  provider-options:
    Opencode:
      frontmatter-strip-fields: [version, prompt_mode, generated-from]
  ```
  Stripped values are preserved in an `<!-- agent-meta-provenance: ... -->` HTML comment
  right after the frontmatter, so traceability/version-bump enforcement (Hard Invariant #2)
  survives. Default (unset) is unchanged for every provider — fully backward compatible.
  See `docs/providers/multi-provider.md#troubleshooting`. 9 new tests
  (`tests/test_agents_frontmatter.py`).
- Intent-routing keyword `Recherche` in the `concept-development` pipeline's
  `signal_keywords` (`config/role-defaults.yaml`) was semantically too broad and
  intermittently misclassified plain "how does X work?" questions about existing behavior as
  `concept-development` instead of `none` (#498, ~2/3 in a promptfoo routing eval — see
  `tests/routing-llm-eval/catalog.manual.yaml::neg-03`). Narrowed to
  `Architektur-Recherche`. `tests/routing-llm-eval/catalog.generated.yaml` regenerated
  (`python scripts/gen_routing_llm_eval_catalog.py`).

### Added
- Approval gates for quality pipeline stages (`scripts/lib/pipelines.py`): new optional
  `approval_default` (pipeline-level) and `requires_approval` (stage-level, overrides the
  pipeline default) fields in `config/role-defaults.yaml` / `.meta-config/project.yaml`
  overrides. When effectively `true` for a stage, the generated pipeline block gets an
  explicit "wait for user confirmation before this stage starts" instruction, provider-
  independent, purely instructive like the rest of the pipeline notation. Neither field
  set means `false` — no shipped base pipeline sets them, so existing generated output is
  unchanged. Lets projects require sign-off on a planner-produced plan (or any other stage)
  before it drives execution, e.g. via a `feature-lifecycle` `implement`-stage override.
  See `docs/guides/quality-pipelines.md#approval-gates-abnahme`.
- `design-system-architect` and `frontend-component-engineer` agent roles
  (`agents/1-generic/`): closes the gap between `ui-ux-designer`'s design-system schema
  and generic `developer` implementation. `design-system-architect` translates a schema
  into real token artifacts (primitive/semantic/component layers, color-harmony +
  design-time contrast gate, spacing/breakpoint methodology, component-variant contracts,
  motion tokens) — explicitly not a WCAG verdict, that stays with `accessibility-specialist`.
  `frontend-component-engineer` builds production components from screen spec + token/
  variant contract (props contract, mandatory loading/error/empty/success state matrix,
  accessibility baseline, motion/responsive implementation from tokens, test scaffold).
  Registered in `config/role-defaults.yaml` (handoff chain: `ui-ux-designer` ->
  `design-system-architect` -> `frontend-component-engineer` -> `accessibility-specialist`/
  `code-reviewer`/`tester`) and added to `feature-lifecycle`'s `implement`-stage
  `allowed_agents`. See `docs/concepts/planned/ui-expert-agents.md`.
- Pipeline stage-detail rendering now reaches generated agents (previously dead code):
  new `{{PIPELINE_DETAIL_BLOCKS}}` in `agents/1-generic/orchestrator.md` (full inline
  detail for the `ORCH_MODE_STRICT`/`ADVISORY` subagent) and, for the always-loaded
  main-chat mode, a lean `{{PIPELINE_DETAILS_DIR}}` pointer in `use-orchestrator.md` —
  one `<pipeline-name>.md` stage-detail file per active pipeline (`scripts/lib/pipelines.py`
  `sync_pipeline_detail_files()`), read on demand instead of inlined, so the always-on
  token cost stays a single routing-table line. Also fixes `check_plan_producer_coupling()`
  never running in production (`build_variables()` was calling `validate_pipelines()`
  without `roles_config`) and a crash it would have hit on malformed `stages` data.
- Lean, token-saving pipeline stage-detail visibility for `main-chat` orchestrator mode:
  new `{{PIPELINE_DETAILS_DIR}}` placeholder in `rules/1-generic/use-orchestrator.md`
  (always-loaded) points at a new `sync_pipeline_detail_files()` (`scripts/lib/pipelines.py`)
  output — one `<pipeline-name>.md` stage-detail file per active pipeline, written per
  provider (derived from `agents_dir`'s sibling, e.g. `.claude/pipeline-details/`, correct
  even for non-standard nesting like Copilot's `.github/copilot/agents`), with stale-file
  cleanup via the same managed-index pattern as `mcp.py`/`external_tools.py`. `main_chat`
  reads the relevant file only once it actually routes to that pipeline — the always-on
  routing table grows by exactly one instruction line regardless of pipeline count, instead
  of inlining every pipeline's full stage detail (`{{PIPELINE_DETAIL_BLOCKS}}`, still used
  as-is for the `strict`/`advisory` `orchestrator` subagent template). Computed centrally
  in `sync.py`'s per-provider loop so it also reaches providers without a native rules_dir
  (e.g. Opencode), whose rules content is embedded into the context file instead. Registered
  as a known first-party artifact in `external_tools_drift.py` so it isn't flagged as
  undeclared injection drift.

## [0.96.0] — 2026-08-15

### Added
- Token-efficiency lazy-rules mechanism: a fresh token measurement (tiktoken cl100k as
  proxy) showed the `rules-preset: silent` mechanism was actually *worse* than `default`
  on Claude Code (9.421 vs. 9.358 tokens always-on) because `alwaysApply: false` is a
  Cursor/Continue frontmatter convention Claude Code silently ignores — `.claude/rules/*.md`
  is always loaded in full regardless. The only real Claude Code lazy-load channel is
  `.claude/skills/<name>/SKILL.md` (only `name` + `description` land in the system prompt,
  the body loads on demand via `Read`, available to every generated agent since all 50 have
  the `Read` tool even without the `Skill` tool). New `channel: skill` rule-option
  (`config/rules-presets.yaml`) routes a rule to `<skills_dir>/<rule-stem>/SKILL.md` instead
  of `<rules_dir>/<rule-stem>.md`, restricted to Claude + Opencode (`scripts/lib/skill_channel.py`,
  new shared module also used by `scripts/lib/mcp.py` and `scripts/lib/external_tools.py` so
  MCP- and external-tool-generated rules can opt in too); other providers keep the plain
  rules_dir file unchanged. New `lazy` preset moves 15 situational rules (sync-interface,
  architecture, conventions, submodule-protection, a2a-delegation-gates, python-conventions,
  issue-lifecycle, lifecycle-tasks, session-conclusion, provider-agnostic, mcp-reqogniloom,
  mcp-honcho, mcp-playwright, mcp-viz-logger, tool-graphify) to the skill channel; a new
  always-on `rules/1-generic/mcp-guardrails.md` keeps the hard MCP tool prohibitions
  (honcho/reqogniloom/playwright) visible without the full tool-list detail, and a new
  always-on `rules/1-generic/use-lazy-rules.md` indexes all 15 skill paths. `_ALWAYS_APPLY_PROVIDERS`
  in `scripts/lib/rules.py` dropped Claude (verified no-op there) — only Continue honors
  `alwaysApply: false`, and it now also gets a `description:` in the injected frontmatter
  (previously missing, which silently prevented Continue's own lazy-loading from working).
  This repo dogfoods the new preset (`rules-preset: lazy`); measured always-on budget after
  the switch: see CI/verification notes.
- Stale-cleanup for `mcp-<server>.md` / `tool-<name>.md` rule files (`scripts/lib/mcp.py`,
  `scripts/lib/external_tools.py`): both write loops previously had no cleanup path when a
  server/tool was deactivated or removed from its registry, unlike `rules.py::sync_rules()`'s
  `previously_managed`/`now_managed` diff — the orphaned rule file just stayed on disk
  forever (e.g. `mcp-reqflow.md`, still present in `.claude/rules/` and `.gemini/rules/`
  from a server no longer referenced anywhere). Both now maintain their own
  `.agent-meta-managed-mcp` / `.agent-meta-managed-tools` sidecar index (new shared helpers
  in `scripts/lib/rule_index.py`) and delete stale files on the next sync; a content-marker
  check on the first-run bootstrap glob avoids false-positive sweeps of unrelated
  same-prefixed files (e.g. the new `mcp-guardrails.md`).
- Intent-routing table in `use-orchestrator.md` (`scripts/lib/delegation_table.py`) now
  lists only pipeline rows — per-agent routing rows were pure duplication of each active
  agent's name + description already shown in the system prompt (Claude/Opencode), and
  pipelines aren't represented there. A compact `**Tiers**` summary line (required/
  recommended agent names, computed from `role-defaults.yaml` at sync time) replaces the
  removed rows so tier coverage stays visible at a glance.
- External Dev-Tool Registry (`config/external-tools-registry.yaml`): known locally-installed CLI dev-tools (e.g. `graphify`) can now contribute a rule-doc section (`.claude/rules/tool-<name>.md`, or embedded into `AGENTS.md`'s managed block for providers without a native rules dir) and hook wiring (`hooks/0-external/*.sh`), rendered deterministically by `sync.py` from a maintainer-curated, version-controlled registry entry — instead of the tool hand-editing generated files at runtime (which happened this session: `graphify`'s self-installer directly appended a section to `CLAUDE.md` and added hook entries to `.claude/settings.json`, violating the "CLAUDE.md is auto-generated, never hand-edit" invariant). New `scripts/lib/external_tools.py` mirrors the existing MCP-registry pipeline (`scripts/lib/mcp.py`); activation is dict-based (`external-tools: { <name>: { enabled: true|false } }` in `.meta-config/project.yaml`, flat-array shorthand still supported) so a framework-default-on tool can be explicitly disabled per project, not just additively enabled — mirrors `external-skills`' activation format rather than `mcp-servers`' flat allowlist. New Admin UI panel ("External Tools") reuses the existing generic `renderOverridePanel()`/`PUT /api/config/project/section` pattern. Shipped with one real, dogfooded entry (`graphify`, rule-content only — its hooks stay opt-in/disabled by default in this repo).
- External-tool injection governance (`permitted-injections` allowlist): a provider-agnostic, default-deny whitelist for file/directory artifacts that locally-installed tools (e.g., graphify) write beyond curated rule-content and hooks. New `permitted-injections` field in `config/external-tools-registry.yaml` entries declares which skills, hooks, rules, config files or other paths a tool may inject — a declaration covers all active providers unless overridden by `provider-skip`. Injections are resolved to concrete filesystem paths per provider (`skills_dir/`, `hooks_dir/`, `rules_dir/`, literal path for config/other). New `scan_injection_drift()` in `scripts/lib/external_tools_drift.py` runs on every `sync.py` invocation, scanning each provider's infrastructure root for undeclared artifacts and rendering `.claude/rules/external-tools-drift.md` (and equivalents per provider) with findings when drift is detected — only as a warning/visibility tool (never blocking, never auto-deleting). Admin UI additions: `GET /api/external-tools/drift` endpoint reports drift findings, new permitted-injections editor in the External Tools panel accepts `kind` (skill/hook/rule/config/other), `name` or `path`, and description per entry, and a drift-found warning banner displays at the panel top when findings exist. Fixes the graphify incident where rule files generated into the skill-channel and a hand-edited backup file went completely undeclared and undetected until manual code review.

### Fixed
- Mammouth was a silently degraded "second-class" provider: fully defined in `config/ai-providers.yaml` but absent from `config/provider-capabilities.yaml`, `config/provider-bootstrap.yaml` and `config/delegation-syntax.yaml`. Because consumers fall back to an empty dict for unlisted providers, every `PAL_*` delegation placeholder was silently stripped from generated Mammouth agents and `subagent_dispatch`/`bootstrap_required` defaulted to `false` with no explanation. Added Mammouth to all three files with conservative capability values modeled on Copilot (another lean provider) and backed by evidence from `ai-providers.yaml` (`has_hooks: true`, file-based `agents_dir`); `PAL_*` placeholders now substitute correctly instead of being stripped.
- `docs/providers/multi-provider.md` was stale: described Gemini's generated context file as `.gemini/GEMINI.md` when the pipeline actually generates `AGENTS.md` (Gemini CLI's native, agent-meta-unmanaged `GEMINI.md` hierarchy is now documented separately as a distinct concept); Copilot and Mammouth — both fully defined in `ai-providers.yaml` — were undocumented; template paths referenced the old `howto/` location instead of `templates/configs/`; incorrectly claimed Gemini has no rules system (it has `.gemini/rules/`, `has_rules: true`).
- `scripts/lib/providers.py::load_providers_config()`'s minimal fallback (used only when `ai-providers.yaml` is entirely missing) hardcoded a stale, partial Claude entry lacking `capabilities`, `model-tiers`, `model-aliases`, `has_commands` and other now-required fields — downstream code expecting the full schema would have received partial data in that edge case. Fallback now mirrors most of the current schema (five fields — `orchestrator_hint`, `settings_local_file`, `settings_local_template`, `isolation-dirs`, `mcp-config` — are intentionally absent; all read sites use `.get()` defaults) (#492).
- Dead code `sync_agents()` in `scripts/lib/agents.py` removed (#462): superseded entirely by `sync_agents_for_provider()`; repo-wide grep confirmed zero remaining callers.
- `_collect_role_defaults()` in `scripts/lib/config_audit.py` replaced with the canonical `load_roles_config()` from `scripts/lib/roles.py` (#480): the private duplicate lacked `load_roles_config()`'s `_`-prefix filtering and legacy-path fallback; no behavior change in the current role set.
- Repeated local `import zipfile` statements in `scripts/lib/backup.py` consolidated to a single module-level import (#466).
- Repeated local `TemplateBuilder` imports in `scripts/lib/context.py` (7 call sites) consolidated to a single module-level import (#469): verified no circular-import risk (`context_templates/builder.py` only imports stdlib).
- `substitute()` in `scripts/lib/config.py` gained an optional `strict: bool = False` parameter (#477): when `True`, an unknown placeholder now raises `SyncError` (name + `source_label`) instead of silently warning. Default behavior is unchanged; no existing call site was switched to strict mode yet, since several rely on partially-populated variables for conditional template blocks.
- Missing docstrings added to `SyncLog` (`scripts/lib/log.py`, 11 members) and `TemplateBuilder` (`scripts/lib/context_templates/builder.py`, 7 members) (#484).
- `config/provider-tools.yaml`: `terminal_tool` section was missing a `Mammouth: bash` entry present in every other provider and already asserted as a hardcoded fallback in `scripts/lib/viz.py` — config now matches the code-level default.
- Stale-cleanup (MCP/external-tools) now runs even when active server/tool list drops to zero: `generate_mcp_artifacts()`/`generate_external_tool_artifacts()` previously early-returned before reaching cleanup-phase when the active list became empty — deactivating the *last* MCP server or external tool orphaned its rule file forever, with the same early-return firing on every subsequent sync. Also fixed `write_managed_index()` which had the identical bug, silently skipping index writes for empty `now_managed` sets and leaving stale entries in the index even after orphaned disk files were correctly deleted.
- Project-root threading in embedded-rules MCP/tool loading: `load_mcp_registry()`/`resolve_active_mcp_servers()`/`load_external_tools_registry()`/`resolve_active_external_tools()` calls in the embedded-rules block for providers without native rules dirs (e.g., Opencode) previously lacked a project_root parameter, silently dropping project-level `.meta-config/mcp-registry.yaml` / `.meta-config/external-tools-registry.yaml` overrides (e.g., a server disabled per-project).
- Injection-drift scan endpoint root resolution in submodule mode: `_compute_injection_drift()` passed raw project-root into `scan_injection_drift()` instead of resolving it via `_agent_meta_root()` — in submodule mode, framework config lives under `.agent-meta/`, and the bug silently fell back to a Claude-only stub provider config, producing false-positive undeclared-artifact findings for every legitimately registered tool.
- Unreachable Opencode removed from `skill_channel.py` PROVIDERS set: every call site that would exercise `channel: skill` for Opencode is gated behind `has_rules` (false for Opencode by design — rules embed into AGENTS.md), making it dead code. Narrowed PROVIDERS to Claude only and corrected the matching doc comment in `config/rules-presets.yaml`.
- MCP guardrails governance: `mcp-guardrails.md` (always-on rule listing hard tool prohibitions) was hand-maintained and could silently drift from `config/mcp-registry.yaml` — added `build_mcp_guardrails_list()` in `scripts/lib/mcp.py` and wired it through a new `{{MCP_GUARDRAILS_LIST}}` placeholder, substituted dynamically in both native-rules and embedded-rules contexts so it always reflects the live registry instead of a maintainer-curated bullet list.
- Config cascade in `add_skill()` now uses shared `lib.io._load_yaml_or_json()` instead of hand-rolling its own yaml/json fallback — the shared helper enforces proper `SyncError` handling for malformed config, whereas the local version raised unhandled, opaque exceptions.

### Changed
- Refactored: extracted shared `_deep_merge()` and `_normalize_enabled_config()` helpers to `scripts/lib/io.py` — the two were duplicated verbatim between mcp.py and external_tools.py, and a near-identical normalization pair duplicated across external_tools.py, skills.py, and agents.py. All five call sites now import from the shared location, eliminating silent divergence risk.
- Perf: eliminated redundant MCP/tool registry reloads within single sync passes — `resolve_active_mcp_servers()`/`resolve_active_external_tools()` each reloaded the full registry from disk even when the caller had just loaded it moments earlier (e.g., `generate_mcp_artifacts()` → `load_mcp_registry()` → `resolve_active_mcp_servers()` reloading). Added optional `registry` parameters to both resolver functions and threaded the already-loaded registry through all internal call sites, eliminating avoidable disk I/O and YAML-parse cost across mcp.py, external_tools.py, context.py, rules.py, agents.py, and external_tools_drift.py.

## [0.95.1] — 2026-08-12

### Added
- MCP toolset propagation into agent frontmatter (#467): a role opts into MCP servers via `mcp-servers:` in `config/role-defaults.yaml` (project override: `mcp-role-overrides.<role>` in `project.yaml`, new schema entry), and `sync.py` binds the server's `tools.allowed` entries as `mcp__<server>__<tool>` into the generated Claude agent frontmatter. Only servers active for the project contribute; `tools.blocked` never leaks in. `e2e-tester` now opts into `playwright` — previously the role was documented as browser-capable in `.claude/rules/mcp-playwright.md` while its generated frontmatter listed base tools only, so every browser delegation failed structurally. New `resolve_mcp_tools_for_role()` and `append_frontmatter_tools()` in `scripts/lib/agents.py`, plus consistency tests catching future rule/frontmatter drift.
- `docs/guides/mcp/playwright-setup.md`: activation, browser install, role opt-in and troubleshooting.

### Fixed
- Orchestrator-guard block reason was lost (#396): on exit 2 the harness feeds *stderr* back to the model and ignores stdout, but the hook wrote its guard message to stdout — every block surfaced as a bare `hook error: No stderr output` instead of the explanation, which read as a non-deterministic hook failure. All blocking-path messages now go to stderr (`hooks/1-generic/orchestrator-guard.sh` v2.1.0 → v2.2.0), covered by two new regression tests.
- Playwright MCP no longer requires root (#470): `config/mcp-registry.yaml` pins `--browser chromium`. The server's default `chrome` channel expects a system-wide Google Chrome at `/opt/google/chrome`, and its installer calls `sudo` — unavailable in CI runners and sandboxes. Chromium ships with Playwright (`npx playwright install chromium`).
- `_load_yaml_or_json()` crashed the whole sync on a malformed config (#461): `yaml.safe_load` and `json.load` are now wrapped and raise `SyncError` with the offending path, and a non-mapping root (top-level list/scalar) is rejected with a readable message instead of surfacing as `AttributeError: 'list' object has no attribute 'get'` in whichever caller happened to run first.
- `read_json_lenient()` silently corrupted JSONC files (#474): the inline-comment regex excluded quotes, so any line whose *string value* contained `//` (a URL, a regex, a path) was truncated, JSON parsing failed and the entire config was silently dropped. Replaced with `strip_jsonc_comments()`, a single-pass scanner that tracks string state and escapes, and preserves line structure so parse-error line numbers stay usable.
- `lifecycle_check.py` raised unhandled tracebacks inside git hooks (#475): `--project-root` as the last argument no longer IndexErrors, and a mapping- or nested-shaped `ai-providers:` no longer passes an unhashable dict into `.get()` — mapping form uses its keys, non-string entries are skipped with a warning.
- Dead statement in `scripts/lib/mcp.py::_update_json_config` (#464): the abandoned path expression is now the intended assignment and moved to where `rel` is defined, so sibling configs (`.vscode/mcp.json` vs `.cursor/mcp.json`) stay distinguishable in `sync.log` instead of both logging as `mcp.json`.
- Misleading re-export import in `scripts/lib/viz.py` (#471): `_load_yaml_or_json` is imported from `.io`, its actual definition site, instead of relying on `.config` transitively re-exporting it.
- `validate_envelope()` documented as dormant by design (#460): the docstring now states explicitly that it is a manually-invokable utility with no interception point (the orchestrator dispatches through the provider's `Agent`/`Task` call, and `orchestrator-guard.sh` sees only `Write`/`Edit`/`Bash`), so the depth and self-handoff limits in `.claude/rules/a2a-delegation-gates.md` are model-followed conventions, not enforced barriers — and must not be cited as evidence of enforcement.
- Test command uses python3 explicitly (`scripts/sync.py`): corrected `TEST_COMMAND` reference from `python` to `python3` for compatibility with environments that only have `python3` in PATH.
- Admin-server lifecycle subcommands (`scripts/admin-server.py`): `start`/`stop`/`status`/`restart` are now implemented (were documented in `/admin` skill but unwired). `start` launches detached with PID tracking in `.meta-viz/.admin-server-pid` and logging to `.meta-viz/admin-server.log`; backward compatible (no subcommand retains blocking mode).

## [0.95.0] — 2026-08-11

### Added
- Planner-pipeline integration: new `parse_plan_ref()` and `validate_plan_ref()` in `scripts/lib/pipelines.py` parse plan markdown files (frontmatter `pipeline_stages:` mapping plus fallback steps table) and validate them against a pipeline's plan-driven stage constraints — plan file existence, stage mapping, agent allow-list. New `check_plan_producer_coupling()` warns when a pipeline has plan-driven stages but no role declares `produces.plan.pipeline` (and vice versa: producers pointing at non-existent or non-plan-driven pipelines). `validate_pipelines()` gained an optional `roles_config` parameter to run these checks.
- Orchestrator plan-driven gate (`agents/1-generic/orchestrator.md` v7.7.1 → v7.8.0): if the matched pipeline has `plan-driven` stages (e.g. `feature-lifecycle` → `implement`) and no plan exists, the orchestrator must delegate to `planner` first and only start the pipeline with `payload.plan_ref` — no more silent fallback-agent runs for features with >2 files or architecture impact. Plan-driven stage generation in `_generate_pipeline_block()` now emits explicit pre-delegation validation steps (plan_ref path check, `pipeline_stages` frontmatter check, allowed-agent check, fallback + error documentation).
- Planner frontmatter convention (`agents/1-generic/planner.md` v1.0.1 → v1.0.2): plans created for plan-driven pipelines must include a `pipeline_stages:` frontmatter field mapping stage IDs to step numbers. `config/role-defaults.yaml` declares the planner as `produces.plan.pipeline: feature-lifecycle` (ref_key `plan_ref`, stage `implement`) and adds the trigger keywords "plane", "Plan erstellen", "Umsetzungsplan erstellen", "Implementierungsplan".
- Delegation-table ghost-entries fix (`scripts/lib/delegation_table.py`): the active-roles filter now applies to all workflow tiers, not only `optional` — tiers like `core` no longer produce ghost rows for inactive roles.
- rtk-for-opencode plugin installed and configured (`.opencode/rtk-config.json`, `opencode.json`): token-filtered command output for shell tool calls.

### Fixed
- Admin-server crash on missing project.yaml (`scripts/admin-server.py`): `_load_viz_config()` returned defaults immediately when `.meta-config/project.yaml` does not exist (previously raised SystemExit); new `_load_admin_ui_config()` provides the same fallback for the admin-ui section. Test constant renamed `ALLOWED_HOSTS` → `DEFAULT_ALLOWED_HOSTS`.
- Admin-server remote auth hardening: token authentication via `--token` CLI flag, `ADMIN_UI_TOKEN` env var, or `admin-ui.token`/`admin-ui.token-file` in project.yaml (priority CLI > env > config > file), verified with constant-time `hmac.compare_digest` from `Authorization: Bearer` header or `?token=` query parameter; unauthorized requests get HTTP 401 with `WWW-Authenticate: Bearer`. Remote bind-host now allowed when token auth is configured — without a token the server stays loopback-only.
- Admin-server CSRF/DNS-rebinding protection now honors `admin-ui.allowed-hosts` (default: loopback only) for both Origin and Host header checks; `admin-ui.bind-host` is configurable in `.meta-config/project.yaml` (schema entries added to `config/project-config.schema.json`).
- Sync drift fix (`scripts/lib/rules.py`): `speech-mode.md` is owned by the speech/ layer, not the rules hierarchy — excluded from stale-cleanup so it is no longer deleted and recreated on every sync (infinite drift).
- Sync drift fix (`scripts/lib/context.py`): `PLATFORM_*` flags are now set for all providers sharing the context file, not just the primary provider.
- External pin: `external/awesome-claude-code` checked out to pinned commit `3d8bde25`.
- Generated files re-synced (CLAUDE.md, AGENTS.md, agent-meta-manager.md ×3 providers).

### Changed
- Changelog and version documentation updates; `knowledge/wiki/plans/am-fix-planner-pipeline-ghost-entries.md` and `am-issue-456-remote-admin-auth.md` added as implementation plan records.

## [0.94.0] — 2026-08-09

### Added
- Standalone agent personas: all 67 eligible generic agent roles now render pre-built, fully self-contained versions in `standalone/agents/` usable without Python or `sync.py` — paste the entire file directly into any AI chat as a system prompt. Identity/project-context placeholders resolve to explicit "ask the user" instructions; multi-agent/orchestration placeholders resolve to empty, matching disabled behavior. Conditional-flag rendering bugs (ORCH_MODE_*, DOD_SE_*, A2A_PROTOCOL_ENABLED, KNOWLEDGE_ENGINE_ENABLED, DIRECT_DISPATCH_ENABLED) fixed across full role coverage; `write_standalone_files()` removes stale files for roles that later become ineligible.

### Fixed
- Bilingual persona documentation: `standalone/README.md` now interleaves English and German text paragraph-by-paragraph instead of separate top/bottom sections; added dedicated "Beschreibung (DE)" column to the role table sourced from `config/role-defaults.yaml`.

## [0.93.0] — 2026-08-08

### Added
- Two new optional generic agent roles: `proofreader` (correctness-only pass — spelling, grammar, punctuation, every finding tied to a stated rule) and `copyeditor` (style, sentence structure, repetition, throughline, content consistency — advisory, every suggestion names its reasoning). Both default to a categorized markdown findings report next to the reviewed file rather than a silent in-place rewrite.
- `standalone/` — pre-rendered, fully self-contained English copies of a pilot set of 8 generic agent personas (`developer`, `senior-developer`, `documenter`, `technical-writer`, `requirements`, `tester`, `proofreader`, `copyeditor`), usable without Python or `sync.py`: paste the whole file as a system prompt in any chat AI. Identity/project-context placeholders resolve to explicit "ask the user" instructions rather than invented values; multi-agent/orchestration placeholders (A2A, DoD gates, extensions) resolve to empty, matching how they already behave when disabled in a real project. New `scripts/lib/standalone.py` module, `sync.py --render-standalone` (combine with `--check` for a CI drift gate), and an Admin UI "Render standalone agents" button on the Sync page.

### Changed
- Admin UI, Phase 3 Task 19 (optional, lowest priority in the consistency remediation plan): introduced a `--space-1` (4px) through `--space-6` (32px) CSS custom-property scale in `:root` and migrated 246 spacing declarations (`margin`/`padding`/`gap` and their directional variants, across both the static `<style>` block and inline `el()` styles) onto it. Values already on the 4px grid map directly; off-grid audit values round to the nearest step, ties rounding up (`6px→8px`, `10px→12px`, `14px→16px`, `18px→16px`, `20px→24px`). Deliberately left untouched: multi-value shorthand declarations (e.g. `padding: 18px 20px`, where a blind substitution risked silently corrupting one of the two values) and sub-grid fine-tuning values (`1px`–`3px`, `5px` — hairline/alignment adjustments, not spacing-grid values). No visual change intended; live-verified across Dashboard, MCP Servers, Pipelines, and Roles.

### Fixed
- Admin UI, Phase 3 (Tasks 15-18) of the consistency remediation plan (`docs/superpowers/plans/2026-08-07-admin-ui-consistency.md`): the two structural design-decision tasks, implemented.
  - **KV editors (Tasks 15-16):** compared all 3 key/value-style editors against the plan's own criteria before touching anything. The plan assumed `addKVRow` (Provider Options) was missing the #319 rename-collision fix that `renderDictEditor` (MCP Env-Vars/Headers) already had — it wasn't; an earlier, unrelated PR (#426) had already fixed it, with its own passing regression test. The real, previously undiscovered gap was in a third editor the plan didn't recognize as "one of the 3": the Environment Variables page's Add/Edit modal had no rename-collision guard at all, silently overwriting an existing variable if renamed (or created) to a name already in use. Decision: `renderDictEditor` and `addKVRow` are genuinely the same kind of editor (arbitrary key → string|bool) and merge into one — `renderDictEditor` gained an `opts.allowBool` flag for `addKVRow`'s type selector, `addKVRow` and its manual `<table>` markup are gone. The Environment Variables modal stays separate (a fixed-schema record editor, not a generic dict), but gets the missing collision guard as its own targeted fix. Delete glyph unified on `×` (was `10/12` sites before, now `12/12`).
  - **Destructive-action confirmations (Tasks 17-18):** all 14 native `confirm()` dialogs (which break out of the app's dark theme) replaced with a new `confirmDestructive()` helper built on the existing `showModal()` component — except the router's unsaved-changes navigation guard, a synchronous `hashchange` interceptor that can't cleanly become async without a bigger navigation-flow change. The generic dict editor's own row-delete additionally had *zero* confirmation before this (unlike every other destructive action in the file) — now guarded too, except for empty just-added placeholder rows where there's nothing to lose. While converting the reflection-pairs delete button, found and removed 43 lines of dead code: an entire duplicate copy of `viewPipelines`' `showPipelineHelp()` function, accidentally pasted mid-statement inside `viewReflectionPairs`' delete handler, never called from there.

### Fixed
- Admin UI, Phase 2 (Tasks 9-13) of the consistency remediation plan (`docs/superpowers/plans/2026-08-07-admin-ui-consistency.md`, #444): component-level consolidation with no behavior change.
  - **Colors (Task 9):** 12 hardcoded hex colors across 7 call sites consolidated onto the existing `--accent-red`/`--accent-green`/`--accent-yellow` CSS variables instead of ad hoc near-duplicate shades (e.g. the Read-Only banner used `#d97706` for its text but a `#f59e0b`-derived rgba for its own background/border — now internally consistent too). Two `severityColor()` duplicates and a model Enable/Disable toggle referenced `var(--accent-yellow, #c9a227)`-style fallbacks for a variable that's always defined in `:root` — dead code, simplified to the plain `var()` form. The Provider Deactivation ACTIVE/DEACTIVATED badge's bespoke `#335533`/`#ff9999`-style pairs now reuse the same `--accent-red`/`--accent-green` + rgba-tint pattern already used by `.btn-danger` elsewhere; its "(no directory)"/"No backups" empty-state text (`#aa8866`) now uses `var(--text-muted)`.
  - **Tables (Task 10):** 2 of 3 flagged inline-styled matrix tables (Rules Presets, project Rules Overrides) unified onto the existing `data-table` CSS class after confirming it's a real, distinct grid style for matrix-shaped data — not a dead class like `roles-table` was in Phase 1; the third (the Provider-Options KV editor's own table) is left for Phase 3's planned consolidation of that editor.
  - **Empty states (Task 11):** 7 "No X found/configured/defined" placeholders styled as `class="muted"` (a generic, ~90-call-site text utility) or classless moved to the file's actual empty-state convention, the dashed-border `class="empty"` box already used at 16 other call sites.
  - **Card renderers (Task 12):** `viewProjectMcpOverrides`'s and `viewProjectSkillsOverrides`'s ~180-line near-duplicate panel renderers (identical header/badges/toggle/info-box/action-box, only the readonly/edit body content differed) consolidated into a shared `renderOverridePanel(opts)` taking the type-specific body as callbacks — net -42 lines.
  - **XSS-policy gaps (Task 13):** two matrix-table row renderers built a `<tr>` via `innerHTML` with a config-derived rule name interpolated directly in, violating the file's own documented "no innerHTML" policy (its whole point is that `el()`'s text nodes never decode/execute markup). Converted both to real `el()` construction, including their icon legends (HTML entities → literal Unicode characters in text-node position, same fix class as Phase 0's em-dash bug — one `title` attribute entity was already rendering literally, now fixed too).

### Fixed
- Admin UI, Phase 1 of the consistency remediation plan (`docs/superpowers/plans/2026-08-07-admin-ui-consistency.md`, #442): the Backups table referenced a `roles-table` CSS class that was never defined anywhere in the file (rendered fully unstyled) and its Delete button used a non-existent `"btn small"` class instead of the established `btn-danger btn-sm` convention. Found and fixed a real regression from the A2A cleanup (#436): the Orchestrator settings page still had form controls (and one leftover variable reference that would have thrown on Save) for `orchestrator.handoff.*` keys already removed from `config/project-config.schema.json`. Humanized ~25 raw kebab-case config-key labels shown directly to users across the General, Providers & Platforms, Orchestrator, and Viz & Admin pages (e.g. `provider-isolation` → "Provider isolation"), and unified `title` attribute casing on destructive/informational controls.

### Fixed
- Admin UI, Phase 0 of the consistency remediation plan (`docs/superpowers/plans/2026-08-07-admin-ui-consistency.md`): the "Preset Matrix" heading on Rules Presets showed the literal text `&#8212;` instead of an em dash (HTML entity in a text-node position never decodes); a skill's version badge read "Recommended Tag" instead of "Recommended"; 6 "Loading…" placeholders were split between the ellipsis character and three literal dots, now unified on the ellipsis character.

### Changed
- A2A handoff concept simplified after a best-practice audit found most of `orchestrator.handoff.*` in `project.yaml` had no consumer anywhere (code or agent prompt): removed `validate-before-delegate`, `supersession-tracking`, `strict-validation`, `compact-mode`, `max_retries`, `human_approval_required`, `protocol_routing`, `token-budget` (only `protocol` remains; `config/project-config.schema.json`'s `handoff` block is now `additionalProperties: false` to stop this recurring). Removed the matching dead envelope fields from `schemas/a2a-handoff.schema.json` (`retry_count`, `max_retries`, `escalation`, `timeout_seconds`, `negotiated_format`) and 3 unreferenced schema `definitions`. Clarified in `snippets/orchestrator/a2a-protocol.md` and `A2A_HANDOFF_BLOCK` that a structured JSON envelope is only required for routes with a schema-backed contract (`role-defaults.yaml` `handoff.input_schema`/`output_schema` pointing at a real file) — everyday FANOUT/BARRIER delegation uses the existing plain-text format, previously undocumented and contradicting a "MUST" claim in the same snippet. `validate_envelope()` stays as a manually-invokable, now-tested utility (no automatic runtime interception point exists in this architecture). See `docs/concepts/a2a-best-practice-analysis-2026-08.md`.

### Fixed
- `AGENTS.md` grew by ~2 blank lines on every single `sync.py` run, forever — the "agents-managed" context template ends with a trailing newline after its closing `<!-- agent-meta:managed-end -->` marker, but the regex that locates the existing managed block never consumed any whitespace after that marker, so each substitution inserted one more newline into the untouched footer than the run before. Fixed by stripping the trailing newline from the replacement text before substitution, restoring a stable match/replace boundary. Cleaned up the ~80 already-accumulated blank lines in this repo's own `AGENTS.md`. New regression tests confirm 3 consecutive `sync.py` runs now produce byte-identical output (#434).

### Fixed
- Admin UI: the MCP server Env-Vars/Headers dict-editor and the Provider-Options KV editor silently corrupted data when a key was renamed to collide with an existing key in the same dict (one row would vanish, another's value silently overwritten) — both editors now reject the rename with a toast and revert the input. The dict-editor also silently dropped a row when its key field was cleared entirely; that's rejected the same way now (#432).
- `DEVELOPER_SNIPPETS_PATH`, `TESTER_SNIPPETS_PATH`, `DEV_STACK_START`: optional variables left an unconditional raw `{{VAR}}` placeholder (or, once interpolated, a misleading trailing-slash path like `` `snippets/` if present``) in generated templates when unset. `build_variables()` now derives a `<VAR>_SET` boolean per var so the 13 referencing template lines across `developer.md`, `data-engineer.md`, `database-engineer.md`, `docker.md`, `junior-developer.md`, `principal-developer.md`, `refactoring-specialist.md`, `senior-developer.md`, `tester.md` and the `agent-meta`/`homeassistant`/`sharkord` platform developer overrides can wrap the whole clause in `{{#if <VAR>_SET}}...{{/if}}` and omit it cleanly (#425).

## [0.92.0] — 2026-08-07

### Added
- New `planner` agent role: turns a concept, REQ, or bug into a concrete, ordered implementation plan with per-step agent assignment and measurable acceptance criteria (`agents/1-generic/planner.md`, `config/role-defaults.yaml`).
- Pipeline engine: `dod_flag`/`payload_flag` conditional stages, `plan-driven` mode, `run_pipeline` composition with cycle/depth validation, provider activation filters — quality pipelines are now a fully declarative, composable primitive instead of hand-authored stage lists (`scripts/lib/pipelines.py`).
- `feature-lifecycle` pipeline replaces the hardcoded `feature` agent: branch → REQ (conditional) → tests (conditional) → implement (plan-driven) → verify (conditional) → validate+document (parallel) → commit, driven entirely by `config/role-defaults.yaml`.
- Pipeline `signal_keywords` now appear as rows in the generated intent-routing table alongside role `intent_keywords` (`scripts/lib/delegation_table.py`).
- Mandatory "Migration verification" workflow step on `developer`: after any migration/rename/move of existing entities or IDs, diff old→new over the stable key, 0 missing/0 duplicates, "lost" keys only acceptable if demonstrably inactive — closes a real gap that let a stable `unique_id` silently regenerate during a large migration (#327).
- `docs/analysis/402-systemaudit-kernziele.md`: full framework self-audit across 5 dimensions (role standardization, pipeline engine, provider-agnosticism, governance hooks, doc consistency) — 14 findings, all filed and resolved as issues #402–#415.

### Fixed
- **MCP server config for Claude now targets `.mcp.json`, not `settings.json`/`settings.local.json`** — Claude Code never reads a top-level `mcpServers` key from either settings file, only from `.mcp.json` at the project root. Every agent-meta-generated Claude project that activated an MCP server previously ended up with a fully inert, silently-broken integration (#388, #400). Includes a migration warning for projects with a leftover `mcpServers` key in the old location, and a self-heal for zero-byte existing config files that previously skipped injection with only a buried warning.
- Silent `except Exception: pass` blocks in `build_variables()` that swallowed pipeline/reflection/SE config errors now surface through the existing warnings list instead of failing invisibly — this is what let a stale pipeline override in `.meta-config/project.yaml` silently break `PIPELINE_MATCH_TABLE` generation with zero diagnostic signal (#402).
- `validate_pipelines()` now checks that a pipeline's `stages` field is actually a list before iterating, reporting a clean structural error instead of crashing with an unhandled `AttributeError` on a malformed override (#403).
- `PROJECT_CONTEXT`/`ARCHITECTURE`/`DEV_COMMANDS` template variables — previously only ever set by the interactive `sync.py --setup` wizard with no fallback — now default sensibly (`PROJECT_CONTEXT` falls back to `PROJECT_DESCRIPTION`, the other two to an empty string) instead of leaking a literal `{{VAR}}` into generated agent templates for any project that skipped the wizard (#423).
- Admin UI: renaming a key in the provider-options KV editor (`/project/providers`) now actually deletes the old key instead of leaving both old and new keys in the saved config as an orphaned duplicate (#319).
- Admin UI: `sync.py --audit-config`'s "template without role-default" check no longer false-positives on `provider-expert.md`, an intentional `extends:`-only base template with no role of its own (#415).
- `config_audit.py`'s `templates_without_default` check now has an explicit `WRAPPER_TEMPLATES` allowlist instead of silently flagging known base templates on every run.
- Two governance-hook limits (soft agent-identity self-declaration, git-mutation regex parser gaps) and the A2A `max_depth` rule (model-enforced only, not technically enforced) are now documented in `a2a-delegation-gates.md`/`branch-guard.md` instead of only in the hook's own source comment (#404, #405).
- `orchestrator.strict`'s no-op on non-hook-support providers (everything except Claude/Mammouth) is now called out in README's Provider Generation Matrix, not just in the `sync.py --validate` warning (#406).
- `.meta-config/project.yaml`'s `model-overrides` nesting order fixed (`{Provider: {role: ...}}`, not `{role: {Provider: ...}}`) — the wrong order meant `resolve_model()` silently never applied several Gemini model overrides, always falling back to the tier-preset default (#410).
- Removed orphaned, stale generated provider output (`.continue/`, `.mammouth/`, `.github/copilot/`) for providers no longer in this project's active `ai-providers` list; `.github/workflows/` (real CI config, not generated) was explicitly preserved (#407).
- Doc drift sweep: README, `docs/guides/quality-pipelines.md`, `snippets/orchestrator/quality-pipelines.md`, `docs/architecture/04-dev-workflow.md` no longer reference the deleted `feature` role or the pre-rename `standard-feature` pipeline name (#408). README's "Agent Roster" table was also missing 7 real, active roles entirely (`accessibility-specialist`, `data-engineer`, `planner`, `product-manager`, `refactoring-specialist`, `sre-engineer`, `technical-writer`) and had a stale header count (51 → 69) and a pre-existing Provider Expert Agents miscount (5 → 6).
- Deleted 2 of 3 flagged duplicate `docs/concepts/planned/*.md` files after verifying against the knowledge wiki's own migration notes that nothing is lost (#414); a third (`prompt-modernization.md`) was intentionally kept — despite the matching filename it is not a duplicate of its `active/` counterpart.
- Added a synthetic end-to-end test for the `extends`+`patches` composition engine (`compose_agent()`), previously untested since no real 2-platform/3-project override in this repo uses it yet (#411).

### Changed
- `developer`'s intent-routing keywords no longer include the bare word `Feature` — it collided with the `feature` role's own keywords and caused mis-routing.
- `sync.py --validate` now warns when `orchestrator.strict` is active for a provider with no PreToolUse hook support (currently: any provider except Claude and Mammouth).
- `developer`'s dead `Agent` tool grant was removed — the role was already instructed to delegate via text reference only, never via tool call.
- SE-role frontmatter naming exception (`se-<rolle>` without the `template-` prefix) documented in `rules/2-platform/agent-meta-conventions.md` instead of being an unexplained inconsistency (#412).

### Known issues
- `orchestrator-guard.sh`'s PreToolUse hook can hang non-deterministically on Windows/Git-Bash when spawning the native `python.exe` (~30–40% of invocations in reproduction testing) — surfaces to the harness as a raw "hook error" instead of the formatted guard message. Root cause identified (MSYS/Git-Bash pipe-to-native-exe unreliability), a first fix attempt made it worse and was reverted; not fixed in this release (#396).
- Optional `*_SNIPPETS_PATH`/`DEV_STACK_START` template variables can still leak an unsubstituted `{{VAR}}` when unset, since the referencing templates interpolate them unconditionally instead of behind a `{{#if}}` guard — different root cause than the #423 fix above, tracked separately (#425).

## [0.91.3] — 2026-08-01

### Fixed
- #392: fill_defaults() now respects the `silent` parameter to prevent duplicate variable warnings
- #392: Skip reporting BUILTIN_VARS (AGENTS_DIR, PLUGIN_DIR_NAME, PRIMARY_IMAGE_TAG) as missing to eliminate false positives
- #392: Add _rmtree_force() utility to handle Windows read-only .git/objects/pack files during skill cleanup
- #392: Fix reqogniloom pinned_commit reference (was branch name 'main', now actual commit hash)

### Changed
- #393: Remove Continue provider support — sync.py no longer generates Continue-specific agent files

## [0.91.2] — 2026-08-01

### Fixed
- #390: Fixed orchestrator-guard hook exemption for git subagent via self-declare sentinel `#agent-meta:agent=<name>` (PreToolUse payload missing `agent_name` field).
- #390: Fixed Windows path interpolation bug in orchestrator-guard.sh causing backslash escape sequences to corrupt config file path.
- #390: Fixed git-mutations regex to use token-aware parser instead of substring matching (eliminated false positives on `git merge-base`, `git check-ignore`).
- #390: Fixed hook to read provider-specific `orchestrator.provider-overrides.<Provider>.mode` setting via `{{AGENT_META_PROVIDER}}` placeholder.

## [0.90.2] — 2026-07-28

### Fixed
- #386: Fixed Admin UI toggle inversion for Skills/MCP panels
- #381/#383: Fixed personal template path + added MCP governance embedding for Opencode
- #382: Fixed external skill submodule deprovisioning (git rm + cleanup)
- #387: Fixed missing opencode-go/ prefix for model IDs
- #385: Added --no-recursive --depth 1 for skill submodule operations

## [0.90.1] — 2026-07-27

### Fixed
- Fix: Context drift backups are no longer erroneously generated after datetime template evaluation.
- Fix: Submodule inclusion for external skills fixed to use `git submodule add` in consumer projects instead of dynamic cloning, respecting the pinned commit natively.
- Fix: Legacy MCP configs are preserved (user modifications like `alwaysAllow` and `env` blocks are no longer overwritten during sync).

## [0.89.0] — 2026-07-27

### Added
- **Partials-Konzept für Context-Files**: Die Provider Context Files (`CLAUDE.md`, `AGENTS.md`, etc.) verwenden nun einen robusten TemplateBuilder und Partials (z.B. `{{> project-metadata }}`) zur dynamischen Generierung.
- Migration der dynamischen Projekt-Metadaten vom statischen Header in den Managed-Block zur Vermeidung von unnötigen Backup-Merge-Konflikten bei der Config-Aktualisierung.

### Removed
- Unused `_load_claude_md_managed_template` Funktion in `context.py`.

## [0.86.3] — 2026-07-26

### Fixed
- Fix: apply provider-specific frontmatter transformations to external skill wrappers to fix Opencode validation.

## [0.86.2] — 2026-07-26

### Fixed
- Fix: properly skip all browser test modules if playwright is absent.

## [0.86.1] — 2026-07-26

### Fixed
- Fix: `SyncLog` attribute error in external skills script.

## [0.86.0] — 2026-07-26

### Added
- Feat: dynamic external skills fetching with project overrides.

### Fixed
- Fix: make playwright import lazy in conftest to prevent pytest collection failures.

## [0.85.5] — 2026-07-26

### Fixed
- add shipsafe ignore files for false positive security warnings

## [0.85.4] — 2026-07-26

### Fixed
- resolve remaining ruff linter warnings using noqa

## [0.85.3] — 2026-07-26

### Fixed
- read agent-meta-version from project.yaml in admin ui

## [0.85.2] — 2026-07-26

### Fixed
- Main-chat orchestrator bugfix merged to main

## [0.85.1] - 2026-07-26

### Fixed
- Add internal-docs to UI dropdown and update README architecture

## [0.85.0] - 2026-07-25

### Added
- Added ReqogniLoom & Honcho MCP registry project-config support.

## [0.84.0] - 2026-07-25

### Added
- **Context Compaction V2 (Single-Tree XML Architecture)**: Replaced the dual-tree legacy (Markdown) vs modern (XML) structures with a single unified XML standard (`<project>`, `<roles>`, `<providers>`).
- Live override capability: Submodule targets can now directly download updated model registries (`model-registry.json`) from GitHub via Admin UI ("Refresh via sync.py or GitHub override").

### Fixed
- Fixed case-sensitive filtering bug for providers in the models.dev live catalog.
- Fixed models.dev test assertions to dynamically support removed `ai-providers` entries.

### Removed
- Removed legacy `1-generic-modern` dual-tree architecture and `scripts/validate-modern-templates.py`.

## [0.83.0] - 2026-07-24

### Added
- **Knowledge Engine Framework**: Complete multi-phase implementation enabling structured knowledge capture, organization, and retrieval across projects.
  - Phase A: Activation mechanism, `knowledge.py` bundle manager, schema/index/log generators, path variables injection.
  - Phase B: 7 knowledge-worker agent templates (`knowledge-curator`, `knowledge-gardener`, `knowledge-indexer`, `knowledge-ingestor`, `knowledge-linter`, `knowledge-migrator`, `knowledge-querier`), conditional gating in delegation routing and intent tables, role-defaults entries.
  - Phase C: AdminUI integration with domain presets (`research`, `personal`, `business`, `book`, `internal-docs`, `custom`), knowledge-engine section writes support.
- **Native Extensions Whitelist**: Schema, validation, and Admin UI editor for managing provider-native extensions (plugins, hooks, skills) with explicit approval gates.
- Knowledge wiki bundle scaffolding with OKF-compliant structure (schema.md, sources/, wiki/, index.md, log.md).

### Fixed
- Test suite corrections for conditional block substitution.
- Knowledge schema rendering for bundle path variables.

### Changed
- `config/project-config.schema.json`: added `knowledge-engine` and `orchestrator.native-extensions` schema sections.
- `scripts/sync.py` and `scripts/lib/config.py`: Knowledge Engine activation and variables injection.
- Admin UI: new `/api/knowledge/*` endpoints for Knowledge Engine domain presets and content management.
- `rules/use-orchestrator.md`: gated knowledge-* agent roles behind knowledge-engine.enabled flag.

## [0.82.0] - 2026-07-23

### Added
- **Main-Chat Orchestrator Mode**: Main chat now acts as router and worker instead of spawning a separate orchestrator subagent. Simplifies multi-agent orchestration, eliminates singleton-rule violations, and reduces protocol overhead (no BARRIER/FANOUT, no A2A envelope).
- Intent-routing table in `rules/use-orchestrator.md` with 50+ agent classifications and routing guidance for the main chat.
- Explicit `orchestrator.mode: strict` default in `config/project-config.schema.json` with schema documentation.
- Admin UI updates to reflect orchestrator configuration structure and main-chat mode routing.

### Removed
- Standalone `orchestrator` subagent (`.claude/agents/orchestrator.md`) — no longer needed under main-chat mode.

### Changed
- `rules/use-orchestrator.md` restructured to support main-chat router+worker delegation pattern (one level deep, sequential).
- `scripts/sync.py` and `scripts/lib/config.py` updated to generate provider-specific agent configurations for main-chat mode.
- All provider-specific AGENTS/CLAUDE/GEMINI context files updated to document main-chat routing instead of separate orchestrator.

## [0.81.0] - 2026-07-22

### Added
- Optional, self-hostable `reqogniloom` MCP server registered in `config/mcp-registry.yaml` (`enabled-by-default: false`): exposes ReqogniLoom's requirement/architecture/test/traceability/ADR/risk/issue/glossary/AI-derivation tools over SSE with `X-API-Key` auth; administrative/destructive namespaces (`admin.*`, `user.*`, `permissions.*`, `audit.*`, `events.*`, `workspace.close`/`.reactivate`/`.delete`) are blocked. Setup guide at `docs/guides/mcp/reqogniloom-setup.md`, secrets template entries `MCP_REQOGNILOOM_URL` / `MCP_REQOGNILOOM_API_KEY` in `templates/configs/mcp-secrets.local-template.yaml`.
- Optional `role-group` field on agent roles, with a corresponding filter control in the Admin UI (`config/role-defaults.yaml`, `docs/ui/admin-ui.html`).
- Codeberg added as a supported Git platform (`config/project-config.schema.json`, `howto/setup/first-steps.md`, `scripts/lib/setup.py`).

### Fixed
- `AGENTS.md`/`CLAUDE.md` managed block is now correctly initialized above pre-existing foreign content instead of being appended after it, fixing stale/duplicated footer regeneration.
- Relaxed the `tier-override` schema validation that was rejecting valid per-provider tier customizations.
- Fixed provider definition ordering so `sync.py --only-variables` no longer runs before providers are defined.

## [0.80.0] - 2026-07-22

### Added
- Configurable native-extensions orchestrator-gate exemption: native provider extensions (plugins, hooks, skills — e.g. Claude "Superpowers") can now bypass the orchestrator gate when explicitly enabled via `.meta-config/project.yaml` (`scripts/lib/config.py`, `rules/1-generic/use-orchestrator.md`, `config/project-config.schema.json`, `docs/guides/project.yaml.example`).

## [0.79.1] - 2026-07-22

### Fixed
- Dead/non-functional registry-refresh button in the Admin UI now works.
- Opencode was incorrectly classified as `registry-only` in the model routing logic.
- Opencode's `models.dev` mode now returns raw model IDs without the namespace prefix (previously incorrectly prefixed).

## [0.79.0] - 2026-07-22

### Added
- Activated 9 previously-defined agent roles across all providers: `principal-developer`, `refactoring-specialist`, `technical-writer`, `tester`, `validator`, `accessibility-specialist`, `data-engineer`, `docker`, `mammouth-expert` (`.meta-config/project.yaml` roles list; generated into `.claude/agents/`, `.gemini/agents/`, `.opencode/agents/`, `.mammouth/agents/`).
- Environment-variable management: define secrets/config in `project.yaml` `environments:` section; sync.py generates per-platform `env.ps1` / `env.sh` / `env.unset.ps1` / `env.unset.sh` scripts under `.meta-config/`; Admin UI can list, add and delete environment variables via new `/api/environments` endpoints (`scripts/lib/env.py`, `scripts/admin-server.py`).
- Live model catalog integration in the Admin UI: per-provider toggle between the curated model registry and the live `models.dev` catalog (`model-source-preference` in `project.yaml`, `default-model-source` in `config/ai-providers.yaml`), pricing overlay (`config/pricing-overlay.yaml`) and model suggestions endpoint; redesigned models table (`docs/ui/specs/models-dev-table-redesign.md`, `docs/ui/admin-ui.html`, `tests/browser/test_models_page.py`).
- `ultra` tier added to Mammouth model presets across all tier profiles (Cheap, Normal, Advanced, Expensive, Expensive as Hell) in `config/tier-presets.yaml`.
- `@opencode-ai/models` dependency (`package.json`) to support the models.dev integration.

### Fixed
- Duplicate Honcho MCP registration in Opencode — the plugin-based entry and the MCP-generated entry collided; new `provider-skip` mechanism in the MCP registry lets a server opt out of generation for a given provider (`scripts/lib/mcp.py`).
- Honcho MCP now supports self-hosted instances via API key, not just the hosted default.
- Stale model dropdown in the Admin UI models table not reflecting the active provider/source selection (`docs/ui/admin-ui.html`).
- Provider sections in `AGENTS.md` are now generated dynamically as part of the managed block instead of going stale between syncs; header and footer are regenerated on every `sync.py` run.

### Changed
- Opencode `subagent_depth` set to `3` in generated Opencode settings and template.

## [0.78.0] - 2026-07-20

### Added
- Platform-specific best practices to all expert agents (Mammouth Plan vs Build modes, Claude CLI context, Gemini artifact guidance).

### Fixed
- Provider routing logic updated for shared AGENTS.md.
- Gemini and Mammouth now use AGENTS.md natively instead of generating redundant context files.
- Renamed `OPENCODE.project-template.md` to `AGENTS.project-template.md`.

## [0.77.0] - 2026-07-20

### Added
- Added full support for the **Mammouth Code** provider.
- Created `mammouth-expert` agent.
- Updated `ai-providers.yaml`, schema, and routing logic for Mammouth.
- Included `{{PROVIDER_ROUTING}}` dynamic variable injection via `scripts/lib/config.py` to keep agent definitions compact and provider-agnostic.

## [0.76.0] — 2026-07-18

### Added
- Regenerate static provider context headers (CLAUDE.md, AGENTS.md, GEMINI.md) on every `sync.py` run — eliminates stale headers after version bumps
- `sync-on-config-change` hook: automatically triggers `sync.py` when `.meta-config/project.yaml` is edited
- `--check` flag for `sync.py`: dry-run validation mode for CI pipelines; includes GitHub Actions workflow template (`howto/ci/sync-check.yml`)
- Sync status endpoint (`GET /api/sync/status`) and panel in admin UI showing last sync time, changed files, and validation state

### Fixed
- Missing `get_deactivation_status` import in deactivation handlers (caused `NameError` at runtime)

### Documentation
- Provider context regeneration revamp: architecture notes and upgrade guide (`docs/provider-context-regeneration.md`)

## [0.75.0] — 2026-07-16

### Added
- `sre-engineer` agent role: proactive reliability discipline, SLI/SLO definitions, error budgets, capacity planning, toil reduction and runbooks (`agents/1-generic/sre-engineer.md`, `agents/1-generic-modern/sre-engineer.md`, `config/role-defaults.yaml`)
- `technical-writer` agent role: external developer- and user-facing docs, API references, getting-started guides, SDK docs, tutorials, CLI help and UX microcopy (`agents/1-generic/technical-writer.md`, `agents/1-generic-modern/technical-writer.md`, `config/role-defaults.yaml`)
- `data-engineer` agent role: ETL/ELT pipelines, data-layer schema migrations, data quality checks, lineage analysis and pipeline monitoring (`agents/1-generic/data-engineer.md`, `agents/1-generic-modern/data-engineer.md`, `config/role-defaults.yaml`)
- `accessibility-specialist` agent role: WCAG 2.1/2.2 compliance audit, ARIA checks, keyboard navigation, screen reader guidelines, color contrast and focus management (`agents/1-generic/accessibility-specialist.md`, `agents/1-generic-modern/accessibility-specialist.md`, `config/role-defaults.yaml`)
- `refactoring-specialist` agent role: systematic large-scale code transformation, Strangler Fig, incremental refactoring, legacy modernization and feature-flag-driven rewrites (`agents/1-generic/refactoring-specialist.md`, `agents/1-generic-modern/refactoring-specialist.md`, `config/role-defaults.yaml`)
- `product-manager` agent role: strategic product management, backlog, user stories, sprint planning, RICE/MoSCoW prioritization and KPI definition (`agents/1-generic/product-manager.md`, `agents/1-generic-modern/product-manager.md`, `config/role-defaults.yaml`)

### Changed
- `devops-engineer` 1.2.0 MINOR: add Reliability Delegation section (`agents/1-generic/devops-engineer.md`, `agents/1-generic-modern/devops-engineer.md`)
- `documenter` 1.5.0 MINOR: add Scope Boundaries section (`agents/1-generic/documenter.md`, `agents/1-generic-modern/documenter.md`)
- `explorer` 1.1.0 MINOR: add Structured Output Contract, Module Overview, Hotspots and Dependency Graph sections (`agents/1-generic/explorer.md`, `agents/1-generic-modern/explorer.md`)
- `log-analyzer` 1.2.0 MINOR: add Scope & Delegation section (`agents/1-generic/log-analyzer.md`, `agents/1-generic-modern/log-analyzer.md`)
- `requirements` 1.5.0 MINOR: add User Story Mode section (`agents/1-generic/requirements.md`, `agents/1-generic-modern/requirements.md`)
- `security-auditor` 1.3.0 MINOR: add Supply Chain Security and Finding-Format sections (`agents/1-generic/security-auditor.md`, `agents/1-generic-modern/security-auditor.md`)

## [0.74.1] — 2026-07-16

### Fixed
- Add Codeberg as valid GIT_PLATFORM option in the platform enum
- Fix provider-isolation save crash
- Expose intent-routing table to main-chat orchestrator mode

### Docs
- Correct main-chat-orchestrator-mode.md to reference INTENT_ROUTING_TABLE

## [0.74.0] — 2026-07-16

### Added
- `principal-developer` agent role: senior escalation target for complex architecture decisions, `orchestrator_only: true` (`agents/1-generic/principal-developer.md`, `agents/1-generic-modern/principal-developer.md`, `config/role-defaults.yaml`)
- `intern-developer` agent role: learning-focused agent for simple tasks scoped to ≤1 file (`agents/1-generic/intern-developer.md`, `agents/1-generic-modern/intern-developer.md`, `config/role-defaults.yaml`)
- `database-engineer` agent role: DB schema design, migrations, query optimization (`agents/1-generic/database-engineer.md`, `agents/1-generic-modern/database-engineer.md`, `config/role-defaults.yaml`)
- `incident-responder` agent role: production incident coordination, RCA, post-mortem documentation (`agents/1-generic/incident-responder.md`, `agents/1-generic-modern/incident-responder.md`, `config/role-defaults.yaml`)
- `dependency-auditor` agent role: dependency audits, CVE checks, license compliance (`agents/1-generic/dependency-auditor.md`, `agents/1-generic-modern/dependency-auditor.md`, `config/role-defaults.yaml`)
- `ultra` tier added to all tier presets, above `max` — reserved for last-resort escalation (`config/tier-presets.yaml`)

### Changed
- `dev-review-loop` reflection pair now escalates to `principal-developer` on block instead of the orchestrator (`config/role-defaults.yaml`)
- `blocked-review-v1` handoff contract updated with runtime exemptions for principal-developer escalation (`scripts/lib/consistency/handoff_contracts.py`)

## [0.73.0] — 2026-07-16

### Added
- `e2e-tester` agent role: E2E tests, visual regression and accessibility audits via Playwright — user-flows instead of isolated units (`agents/1-generic/e2e-tester.md`, `config/role-defaults.yaml`)
- Playwright MCP server for browser automation and E2E tests (`config/mcp-registry.yaml`, `.claude/rules/mcp-playwright.md`)
- Main-chat orchestrator mode concept promoted to active (`docs/concepts/active/main-chat-orchestrator-mode.md`)

### Changed
- Web-development capabilities added to `developer`, `senior-developer`, `junior-developer` and `performance-optimizer` agents, including browser verification steps (`agents/1-generic/`, `agents/1-generic-modern/`)

## [0.72.0] — 2026-07-15

### Added
- Honcho MCP server integration: persistent cross-session memory for agents (`config/mcp-registry.yaml`, `enabled-by-default: false`)
- Honcho setup guide (`howto/mcp/honcho-setup.md`) with tool reference and activation instructions
- `MCP_HONCHO_URL` secrets template entry (`howto/configs/mcp-secrets.local-template.yaml`)
- Generated MCP rule files: `.claude/rules/mcp-honcho.md`, `.claude/rules/mcp-viz-logger.md`

### Fixed
- MCP rule-file generation for providers without explicit `rules_dir` — Claude provider was silently skipping rule generation (`scripts/lib/mcp.py`)

### Changed
- `dod-push-check.sh`: Config discovery migrated from `agent-meta.config.json` to `.meta-config/project.yaml`; PyYAML dependency replaced with stdlib fallback

## [0.71.2] — 2026-07-14

### Documentation
- docs: reconcile viz-event-schema with emitted events (#345)

## [0.71.1] — 2026-07-13

### Fixed
- viz-server.py: fix missing importlib import (caused startup crash)
- viz-logger.py + admin-server.py: add --root PROJECT_ROOT override so .agent-meta/ submodule paths resolve correctly in target projects
- viz-report.py + live-dashboard.html: fix delegate_out event rendering (events were silently dropped)
- lib/viz.py: fix newline injection (malformed output)

## [0.71.0] — 2026-07-12

### Added
- feat: add tool risk classification section to orchestrator agent

### Fixed
- fix: add provider limits and execution trace isolation to A2A delegation rules

### Documentation
- docs: document instruction bleed risk in platform composition rules
- docs: add best-practice audit report (2026-07) and circuit-breaker/DoD-gate/judge concept patterns

## [0.70.0] — 2026-07-12

### Changed — Token Efficiency (Phase 6)
- **Flat Orchestrator Mode Flags** (`ORCH_MODE_*`): Replaced nested `{{#if}}/{{else}}` blocks with three flat boolean flags (`ORCH_MODE_DISABLED`, `ORCH_MODE_STRICT`, `ORCH_MODE_ADVISORY`) — eliminates nesting-risk in conditional stripping
- **AGENT_HINTS_CLAUDE** (new parameter): `include_table=False` option for providers (like Claude) that inject agent descriptions natively — removes ~1.5 KB duplication
- **hint/description-Deduplication**: Automatic deletion of redundant `hint` field when identical to `description` in agent frontmatter (v220+ in agents.py)
- **Lazy-Loaded Orchestrator Blocks**: SE-Mode, A2A-Protocol, Checkpointing, Quality-Pipelines now loaded from `snippets/orchestrator/` at build-time instead of hardcoded — enables selective disabling via empty variables
- **Backup API Endpoints** (v0.68.0+): Added `/api/backups`, `/api/backups/create`, `/api/backups/restore`, `/api/backups/<archive>` DELETE for config versioning

### Fixed
- **Singleton-Block Injection** for spawn-capable agents only: Singleton constraint now limited to worker agents that can actually spawn (avoiding spurious warnings in non-spawning agents)
- **Submodule Path Fallback**: `.agent-meta/` fallback added to `_list_agent_templates()` for projects using agent-meta as submodule

## [0.68.0] - 2026-07-12

### Added
- **Backup API Endpoints**: Added `GET /api/backups`, `POST /api/backups/create`, `POST /api/backups/restore`, and `DELETE /api/backups/<archive>` endpoints to `admin-server.py`.
- **Backup Configuration**: Added `backup` config block with `retention` settings (`max_backups`, `max_age_days`) to `project.yaml`.
## [0.67.0] - 2026-07-10

### Added
- **Pipeline Match Check auto-generated**: `{{PIPELINE_MATCH_TABLE}}` is now dynamically assembled from `quality_pipelines` signal_keywords in `role-defaults.yaml` — eliminates hardcoded pipeline tables in orchestrator
- **Intent-Routing auto-generated**: `{{INTENT_ROUTING_TABLE}}` is now dynamically assembled from `routing` hints in `role-defaults.yaml` — eliminates hardcoded intent routing in orchestrator
- **`agents/1-generic-modern/` directory**: Phase 1 token-optimization PoC with reference-agent, developer, and orchestrator templates using 6-block XML structure

### Changed
- **Token-Optimierungs-Offensive**: ~200 KB token savings through compression of all agents, rules, and commands across the framework
- **se-orchestrator fully removed**: Agent file, schema, tests, and all documentation references deleted — replaced by `orchestrator (SE-Mode)` nomenclature
- **AGENTS.md streamlined**: Rules-Summary block (89 lines of token overhead) removed from managed block
- **ARCHITECTURE.md reduced to 53 lines**: Detailed architecture moved to `ARCHITECTURE.full.md`
- **49 active roles** (down from 50 after se-orchestrator removal)
- **Documentation references normalized**: 15-file audit updating `se-orchestrator` → `orchestrator (SE-Mode)` or `[deprecated]` across CODEBASE_OVERVIEW, ARCHITECTURE, README, and cascade docs

### Fixed
- **Admin UI section-whitelist expanded**: `_write_project_section` whitelist in `admin-server.py` expanded from 7 to 23 keys — enables saving of `roles`, `orchestrator`, `viz`, `admin-ui`, and provider settings
- **Admin UI key-name corrections**: `workflow_tier` / `permission_mode` key mismatches fixed in `admin-ui.html`
- **Admin UI cleanup**: Removed CSS artifacts and stale se-orchestrator agent cards from `agent-graph.html`
- **Placeholder validation**: `sync.py --validate` reports 0 warnings after full reference normalization

### Removed
- **`se-orchestrator.md`** agent file deleted
- **`se-orchestrator.schema.json`** deleted
- **Legacy SE test scenarios** (SE-01, SE-03, SE-04) removed — replaced by updated manual tests
- **Hardcoded pipeline/intent tables** from orchestrator — now auto-generated from role-defaults.yaml

## [0.66.0-beta.4] - 2026-07-02

### Changed — Token Optimization Phase 2 (Top-10 Compactification)
- **ui-ux-designer**: 12200 → 7907 chars (-35%, 3050 → 1976 tokens) — JSON schema examples replaced with field-table + schema-reference
- **prompt-engineer**: 12658 → 6065 chars (-52%, 3164 → 1516 tokens) — Best-Practices sections consolidated into reference tables
- **code-reviewer**: 11237 → 9351 chars (-17%, 2809 → 2337 tokens) — JSON output schema replaced with field-table
- **export-manager**: 9239 → 5647 chars (-39%, 2309 → 1411 tokens) — Two JSON schemas replaced with field-tables + snippet references
- **performance-optimizer**: 9040 → 6589 chars (-27%, 2260 → 1647 tokens) — JSON output schema + workflow phases consolidated
- **devops-engineer**: 9033 → 6451 chars (-29%, 2258 → 1612 tokens) — Pipeline-YAML + K8s-Manifest + JSON schema replaced with snippet references
- **api-specialist**: 8664 → 6542 chars (-24%, 2166 → 1635 tokens) — OpenAPI-YAML + JSON schema replaced with snippet reference
- **feature**: 8456 → 5698 chars (-33%, 2114 → 1424 tokens) — 8 step-by-step blocks collapsed into single lifecycle table
- **concept-reviewer**: 6978 → 5477 chars (-22%, 1744 → 1369 tokens) — 7 review dimensions + reflection-loop consolidated into tables

### Fixed
- **Dead link cleanup**: Removed references to deleted `_wf-skill-lifecycle.md`, `_wf-claude-review.md`, `_wf-git-ops.md`, `_wf-security-audit.md` in `agent-meta-manager.md`, `git.md`, `security-auditor.md`
- **Provider-agnostic consistency**: All compactifications are pure Markdown reductions — no XML/Modern-format, no provider-specific syntax. All 4 top providers (Claude, Opencode, Gemini, Continue, Copilot) work identically.
- **Placeholder validation**: Added `A2A_MAX_DEPTH`, `FILE_AFFINITY_HINT`, `ANALYSIS_ENABLED`, `SE_MODE_BLOCK`, `A2A_PROTOCOL_BLOCK`, `CHECKPOINTING_BLOCK`, `QUALITY_PIPELINES_BLOCK` to `_BUILTIN_VARS` in `scripts/lib/consistency/placeholders.py` — eliminates 7 false-positive consistency warnings

## [0.66.0-beta.3] - 2026-07-02

### Changed — Token Optimization Phase 1 (Quick-Wins)
- **Orchestrator externalized**: 4 conditional blocks (SE-Mode, A2A-Protocol, Quality-Pipelines, Checkpointing) moved to `snippets/orchestrator/*.md`, reducing orchestrator.md from 35836 → 22878 chars (-36%, 8959 → 5719 tokens).
- **A2A handoff documentation consolidated**: Reduced duplication between orchestrator and reference-agent templates.
- **AGENTS.md managed-block compactified**: Root managed-block trimmed from 669 → 151 lines (-77%) via compact rule summaries (title + 1-sentence summary + path).
- **`_wf-*.md` workflow files deleted**: 9 unused reference files removed, knowledge preserved in agent templates and rules files. See `agents/1-generic/_README.md` for mapping.
- **Compact-Mode default enabled**: `orchestrator.handoff.compact-mode: true` (was `false`) — A2A envelopes use short field names by default.
- **Continue prompt-mode `slim`**: `provider-options.Continue.prompt-mode: slim` (was `full`) — reduces Continue generated prompts to ~80 lines.

### Internal
- New helper `_extract_rule_compact_from_content()` in `scripts/lib/context.py`.
- `_collect_embedded_rules_md()` gained `compact: bool` parameter.
- `_build_opencode_managed_block()` passes `compact=True` for Opencode provider.

---

## [0.66.0-beta.2] - 2026-07-01

### Added
- **Prompt-Modernization PoC**: Modern Mode with 6-block XML structure for agent prompts (`feat/prompt-modernization-poc`)
- **Prompt-mode awareness**: `log`, `admin-server`, `admin-ui` now respect prompt-mode configuration (legacy/hybrid/modern)
- **Admin UI prompt-modes page**: `/project/prompt-modes` page for viewing and managing prompt-mode settings per agent
- **XML-anchor support**: Composition patches can now target XML anchors in Modern-mode templates
- **prompt_mode consistency check**: `consistency-check.py` validates prompt_mode alignment across generated agents
- **Singleton-Constraint injection**: `sync.py` injects Singleton-Constraint block into Worker agent files to prevent recursive spawning
- **A2A anti-re-delegation gates**: Configurable depth-limit, self-handoff rejection, T-size-limit, re-delegation detection (`rules/a2a-delegation-gates.md`)
- **Gate #5 — Singleton-Orchestrator Spawn Rule**: Prevents Workers from spawning additional Orchestrator instances
- **prompt-engineer agent template**: New role for prompt design, review and optimization (#337)

### Fixed
- Prompt-engineer agent template corrections and refinements
- Various minor fixes in prompt-modernization integration

### Changed
- Orchestrator-singleton-guard concept integrated into prompt-modernization-poc branch

### Documentation
- Active concept: prompt-modernization (Phase 1 complete)
- Active concept: singleton-orchestrator moved to `active/`
- Active concept: SE-und-Prompt-Modernisierung moved to `active/`
- Updated CODEBASE_OVERVIEW.md and README.md for prompt-modernization and singleton-guard

---

## [0.65.2] - 2026-06-28

### Fixed
- Orchestrator Singleton Guard (verhindert Rekursion, max Depth 10)
- Tests fuer Singleton-Verhalten ergaenzt

---

## [0.65.1] - 2026-06-22

### Fixed
- Per-provider tier presets: all 5 presets (Cheap/Normal/Advanced/Expensive/Expensive as Hell) now have `providers:` sections for Claude, Gemini and Opencode with correct model IDs
- Opencode model IDs unified with `opencode-go/` prefix; `qwen3.7-plus` replaces `qwen3.6-plus`; `flash-free` removed; aliases cleaned up (`config/ai-providers.yaml`)
- Core bug in `scripts/lib/roles.py` tier resolver: now uses `providers.<name>.tiers` before global fallback — previously all Opencode agents received Claude model IDs
- Admin UI autocomplete performance: per-provider datalists replace a single global list with thousands of entries (Tier Presets + Provider Tier Overrides dialog) (`docs/admin-ui.html`)
- Outdated project-level model overrides: Opencode prefix corrected from `opencode/` to `opencode-go/` (`.meta-config/project.yaml`)

---

## [0.65.0] - 2026-06-22

### Added
- Model discovery from OpenRouter (338 models) and OpenCode Zen/Go (68 models) via keyless APIs
- Model curation system: blacklist, disable, enable states (`config/model-curation.yaml`)
- Registry persistence guard: populated registry preserved on network failure
- Tier presets redesign: direct model-id assignment (`tiers:`) replaces tier-to-tier mapping
- Backward-compatible: old `mapping:` format still resolved
- Project-local tier presets override global ones in `resolve_model`
- OpenCode unified provider: Zen + Go merged, `display-name` field in ai-providers.yaml
- Admin UI: Edit/Save/Cancel flow for pricing, per-model enable/disable/blacklist
- Admin UI: Quick-filter strip (Claude/OpenCode/GitHub/OpenAI/Google) in model dashboard
- Admin UI: Resolved View + Edit Mappings tabs in Tier Presets
- Admin UI: Per-provider datalist filtering in Provider Tier Mappings
- Admin UI: Project Tier Override panel on ai-providers page
- `display-name` field for providers, surfaced in all admin dialogs

### Fixed
- `SyncLog.error` missing method caused `AttributeError` crash in target repos
- `resolve_model` passed `pc` instead of `provider_config` (wrong type, runtime error)
- Tier-preset dropdown fell back to stale hardcoded list with removed SE variants
- Fabricated `OPENCODE_GO_MODELS` replaced with real API data from `opencode.ai/zen/go/v1/models`
- HTTP 403 from OpenCode endpoints fixed with correct `User-Agent` header

### Changed
- `tier-presets.yaml` migrated to new `tiers:` format (all 5 presets)
- OpenCode provider: `Opencode` (Zen) and `OpencodeGo` (Go) merged into single `Opencode`
- Model registry now sourced from live APIs, not hardcoded data

### Removed
- Fabricated hardcoded `OPENCODE_GO_MODELS` list
- `scripts/patch_ui.py` (obsolete one-shot script)
- `Normal (SE)` and `Advanced (SE)` pseudo-presets (SE is now a boolean flag)

---

## [0.64.1] — 2026-06-20

### Added

- **SE_MAX_CELLS and cost_limit_eur variables**: New configuration variables for SE decomposition control — limits cell count and estimated cost per decomposition run.
- **Resilience criterion in se-critic (v1.7.0)**: Fifth evaluation dimension added to SE architectural critique — assesses fault tolerance and recovery capabilities.
- **Design-by-Contract fields in se-interface-mgr (v1.6.0)**: Interface specifications now support preconditions, postconditions, and invariants per DbC methodology.

### Changed

- **se-orchestrator deprecated in role-defaults**: SE cascade implementation stage now routed through main orchestrator (SE-Mode) instead of separate se-orchestrator role.

### Fixed

- **SE-framework consistency**: Aligned config, templates, and documentation — V&V agents marked as implemented, corrected agent count to 14 in concept docs.

---

## [0.64.0] — 2026-06-20

### Added

- **Config audit routine** (`scripts/lib/config_audit.py`): Detects 4 categories of config drift — roles without template, templates without role-default, deprecated roles (auto-fixable), and orphaned pipelines/reflection-pairs.
- **`--audit-config` / `--audit-config --apply` CLI flags**: `--audit-config` reports findings; `--audit-config --apply` auto-fixes deprecated roles by commenting them out in `project.yaml` (idempotent, comment-preserving, reversible).
- **Admin-UI "Config audit" panel**: New panel with REST endpoints `GET /api/config-audit` and `POST /api/config-audit` for interactive audit and apply from the admin interface.
- **End-of-sync audit warnings**: Non-blocking warnings for all 4 audit categories printed at the end of every `sync.py` run.

### Fixed

- **Deprecated agent templates excluded from sync**: Templates with `deprecated: true` frontmatter (e.g. `se-orchestrator`) are no longer generated or listed in any output — central filter applied in `collect_sources`.
- **Config audit false-positive for multi-instance roles**: Roles using `based-on` with multiple instances are no longer incorrectly flagged as missing role-defaults in the audit output.

---

## [0.63.0] — 2026-06-20

### Added

- **3-tier SE developer cascade**: Three new agent roles (`se-junior-developer`, `se-developer`, `se-senior-developer`) implement a tier-based leaf-node strategy with interface discipline — same-level communication only via the next-higher tier; contract-first implementation against `se-interface-mgr` specs.
- **`implementation` stage in SE cascade pipeline**: New pipeline stage inserted after `termination` and before `validation`; `se-orchestrator` routes leaf nodes tier-based depending on interface count and cross-cutting concerns.

### Changed

- **SE cascade pipeline routing**: `se-orchestrator` now dispatches to `se-junior-developer` (0–1 interfaces, trivial), `se-developer` (2–4 interfaces, standard), or `se-senior-developer` (5+ interfaces, boundary-level, security/performance-critical) based on interface complexity.

### Docs

- Updated `07-se-cascade.md` with implementation stage documentation.
- Updated `se-agent-concept.md` with the 3-tier developer model.
- Updated `instantiate-project.md` with new SE developer roles.

---

## [0.62.1] — 2026-06-18

### Fixed

- **SE recursive folder structure**: SE file-based output now uses recursive folder nesting with System/Component designation postfix naming; SE output conventions updated in orchestrator, se-requirements, and se-architect agents.
- **A2A payload.t size limit**: Hard 300-character limit on A2A `payload.t` field to prevent inline prose dumps in agent-to-agent handoff envelopes.

---

## [0.62.0] — 2026-06-18

### Added

- **SE cascade rebuild**: Pipeline von 5 auf 9 Stages erweitert (l0-stakeholder, l1-requirements, l1-architecture, l2-requirements, l2-architecture, l2-interface, l3-requirements, l3-architecture, termination, validation)
- **SE-spec DoD presets**: Drei neue DoD-Presets (spec-optional, spec-driven, spec-certified) mit se-required Feld
- **Configurable SE output directory**: SE/L{n}/{SystemName}/L{n}_{SystemName}_{Requirements|Architecture}.md
- **Component/system designation**: designation-Feld in se-termination Output (ISO terminology)

### Changed

- **SE mode integration**: SE-Mode direkt im normalen Orchestrator via {{#if SE_ENABLED}} — se-orchestrator deprecated
- **Dynamic depth control**: SE_MAX_DEPTH → SE_MIN_DEPTH + SE_MAX_DEPTH (dynamisch)
- **Generic ID prefixes**: REQ-L{n}-NNN / ARCH-L{n}-NNN statt component/sub-system-spezifisch
- **Pipeline validation**: Actionable hints bei fehlenden Rollen

### Removed

- **Strict Stop Rule L3**: Entfernt für flexible Tiefensteuerung

### Fixed

- Issue #323 geschlossen: DoD/SE-Beziehung dokumentiert

---

## [0.61.1] — 2026-06-17

### Fixed

- Add `.agent-meta/` fallback path for admin UI bundle resolution ([#322](https://github.com/Popoboxxo/agent-meta/pull/322), fixes [#321](https://github.com/Popoboxxo/agent-meta/issues/321))

---

## [0.61.0] — 2026-06-16

### Added

- **Admin UI — viz dashboard integration**: new `/viz-dashboard` page embeds the Viz dashboard via iframe; Start/Stop/Restart toggle for Viz and MCP subprocesses via new CSRF-protected routes `POST /api/subserver/{viz|mcp}/{start|stop|restart}`.
- **VizManager lifecycle methods**: `start_viz`, `stop_viz`, `restart_viz`, `start_mcp`, `stop_mcp`, `restart_mcp` in `scripts/admin-server.py`.
- **project.yaml thematic sub-pages**: dedicated editor pages (General, Providers & Platforms, Roles, Orchestrator, Viz & Admin, Model overrides, Advanced/Raw) replace the previous single generic schema editor.
- **Non-destructive section save**: new route `PUT /api/config/project/section` performs read-modify-write deep-merge, preserving unrelated top-level keys.
- **Typo-safe config data sources**: new API routes `GET /api/providers` (with model_tiers and model_aliases per provider), `GET /api/platforms`, and `GET /api/roles` back dropdowns, checkboxes, and multi-selects from real data instead of free-text inputs.
- **Visual model-overrides table editor**: provider → role → provider-specific model dropdown; replaces raw JSON textarea for `model-overrides` config.
- **Views separation in Admin UI**: Dashboard panels explain the Framework Defaults vs. Project Instance Config mental model; `config/*.yaml` (global, read-only) and `.meta-config/project.yaml` (project instance) are now visually distinguished.

### Changed

- **Admin UI navigation**: redundant `/config/project-target` nav entry removed — it pointed to the same file as `/config/project` and is superseded by the new thematic sub-pages.
- **Nested forms replace JSON textareas**: `orchestrator.handoff`/`token-budget` and `provider-options` use structured form inputs rather than raw JSON editing.

### Removed

- **`config/project.yaml`**: deleted 15-line stub file — it was dead configuration never read by `sync.py`; the canonical project config lives at `.meta-config/project.yaml`.

---

## [0.60.0] — 2026-06-15

### Added

- **Integrations Framework Concept**: new concept document (`docs/concepts/integrations-framework.md`) defining the semble-reference integration model — provider-agnostic integration patterns for external skill connectors.
- **Replacement commands**: `admin.md`, `checkpoint.md`, `analysis.md`, `open-docs.md` replace the former `viz-*` command suite — purpose-built commands for admin UI lifecycle, orchestrator session management, AST dependency analysis, and documentation browser.
- **Admin UI — target-repo view**: super-admin mode now exposes the meta-repo's own `.meta-config/project.yaml` as a "Target repo" section with a dedicated sidebar nav item (`/config/project-target`).
- **Unified admin server entry-point**: `admin-server.py` becomes the single entry-point starting Viz dashboard and MCP SSE server as supervised subprocesses; `--no-viz` flag for lightweight / CI use; `/api/subserver-status` endpoint.
- **A2A handoff schema**: complete schema with `timeout_seconds` and `escalation` fields; `delegation.a2a_envelope` boolean in `project-config.schema.json` for per-project opt-in.
- **max_tokens support**: Claude provider now supports `max_tokens` injection and corrected temperature handling (`scripts/lib/agents.py`, `scripts/lib/roles.py`).
- **Commands howto**: `howto/features/commands.md` documents the full Commands System (REQ-CMD-09).
- **GitHub Actions validation pipeline**: `.github/workflows/validate.yml` — CI workflow validating generated files on every push.

### Fixed

- **PAL delegation engine gaps**: documented build-time vs runtime placeholder split; added schema-awareness (`get_schema_ref()`, `validate_envelope()` with graceful degradation); added Agent Return Format section (`STATUS/RESULT/ARTIFACTS/ERRORS`) to orchestrator (v3.29.0).
- **Shell injection in dod-push-check.sh**: replaced `eval` with `bash -c` to prevent injection.
- **Orchestrator-first rule missing for Gemini**: generic orchestrator-first rule now enforced on Gemini platform.
- **PyYAML missing — graceful fallback**: `reflection.py` and `setup.py` now print a clear actionable error and exit cleanly instead of raising `ImportError` traceback.

### Changed

- **viz-* commands removed**: `viz-mindmap.md`, `viz-report.md`, `viz-toggle.md`, `viz-watch.md` replaced by the four purpose-built commands above.
- **Orchestrator extended**: `use-orchestrator.md` rule expanded with Main-Chat-Modus section; orchestrator agent gains full `checkpoint`, `analysis`, and `open-docs` awareness.

---

## [0.59.0] — 2026-06-15

### Added

- **Admin UI**: new single-file web frontend (`docs/admin-ui.html`) with Vanilla JS and dark theme — zero dependencies, browser-native editor.
- **Admin Server** (`scripts/admin-server.py`): stdlib HTTP server for config read/write operations, sync.py integration, SSE live events — no external dependencies.
- **Complete Admin Roadmap**: all 6 phases implemented in a single release:
  - Phase 1: Static viewer for current agent-meta state
  - Phase 2: Edit and validate configuration changes inline
  - Phase 3: Role drag-and-drop with delegation graph visualization
  - Phase 4: Pipeline builder for orchestrator workflows
  - Phase 5: Super-admin editors for skills, MCP, DoD, delegation rules, export targets, role-defaults, AI providers, and agent templates
  - Phase 6: Live-sync watcher for real-time configuration updates
- **Security hardening**: loopback-only binding, CSRF/Origin validation, no innerHTML sinks, atomic writes with backup.
- **Admin CLI flags**: `sync.py --admin`, `sync.py --admin-only`, `sync.py --admin-port` for flexible deployment.
- **Test coverage**: 24 unit tests for admin-server with full integration coverage.

---

## [0.58.0] — 2026-06-14

### Added

- **Framework-wide conditional A2A (token optimization)**: the A2A Handoff Protocol is now gated behind `A2A_PROTOCOL_ENABLED` across **all** agents (orchestrator, developer, junior/senior-developer, validator, feature, ideation) — not just the orchestrator. When `orchestrator.handoff.protocol` is `none`/`false`, no generated agent mentions envelopes, `handoff_id`, or `payload` anymore. The per-agent A2A sections were also compacted (e.g. developer 216 → 182 lines, feature 305 → 267, ideation 203 → 174), so even with A2A **on** the agents are leaner. Per-provider verified across all 5 providers: with A2A off the orchestrator drops ~18% (e.g. Claude 481 → 394 lines) while native delegation syntax stays intact.
- **Conditional orchestrator sections (token optimization)**: the A2A Handoff Protocol (~90 lines), Outcome Caching, and Checkpointing sections are now generated only when actually enabled. New flags `A2A_PROTOCOL_ENABLED` (from `orchestrator.handoff.protocol`; disable via `none`/`false`) and `CHECKPOINTING_ENABLED` (disable via `orchestrator.checkpointing: false`) gate them. The delegation context format (`TASK`/`CONTEXT`/`CONSTRAINTS`/`EXPECTED_OUTPUT`) was lifted out of the A2A block so structured context survives even when A2A is off.
- **3-tier developer system**: new roles `junior-developer` (tier `fast` — trivial, tightly-scoped changes with a structured ESCALATE protocol) and `senior-developer` (tier `max`, project memory — architecture impact, cross-cutting refactorings, hard bugs, DECISION notes). The orchestrator routes by difficulty and handles escalations without a user round-trip; active only when both roles are enabled (`DEVELOPER_TIERS_ENABLED`).
- **PAL conditionals**: `{{#if PAL_*}}...{{/if}}` blocks are now evaluated per provider by the DelegationSyntaxEngine (e.g. the orchestrator Tools section appears only for providers with `tool_preamble: true`).
- **PAL diagnostics**: missing or unknown PAL placeholder definitions now produce sync warnings instead of being silently removed.
- **Gemini registration notice**: every generated `.gemini/agents/*.md` starts with a note that the agent must be registered via `define_subagent` (Gemini is API-registered, not file-discovered).
- **SE export adapter** (`scripts/lib/se_export/`, CLI `scripts/se-export.py`): Markdown output (default) and GitHub Issues (Phase 2 config), with tests.
- **Orchestrator token-budget tracking** (`orchestrator.handoff.token-budget`, default 10 % session overhead cap).
- **CI workflow** (`.github/workflows/orchestration-test.yml`): orchestration/runtime tests and template validation.

### Fixed

- **A2A protocol leaked when disabled**: `{{PAL_HANDOFF}}` emitted the full A2A envelope protocol in the orchestrator's Parallel Execution Engine even when `A2A_PROTOCOL_ENABLED` was false — now gated. The developer-tier escalation protocol also referenced `payload.ctx`/`trace_parent`/`handoff_id` unconditionally; it is now phrased protocol-neutrally with the A2A-specific parts conditional.
- **Orchestrator Tools section leaked to all providers**: the generic conditional cleanup stripped `{{#if PAL_TOOL_PREAMBLE}}` markers before the PAL engine could evaluate them — PAL substitution now runs first.
- **Provider names in generic orchestrator**: the Provider-Transport table (Claude/Gemini/... names) violated the provider-agnostic policy — replaced with abstract transport wording (orchestrator 3.21.0).
- **PAL replacement corruption risk**: replacement strings containing backslash sequences are no longer interpreted as regex group references.
- **UnicodeEncodeError on Windows consoles**: sync.py crashed when printing the sync report on cp1252 terminals — stdout/stderr are now forced to UTF-8.
- **opencode.json JSONC parsing**: trailing commas and BOM in JSONC settings files broke parsing, silently skipping MCP injection and provider isolation. Shared lenient reader now lives in `lib/io.py`.
- **Scalar template variables**: YAML scalars (`true`, `20`) in `variables:` crashed substitution with TypeError — values are now coerced to template strings (`"true"`/`"false"` for booleans).
- **Schema gaps**: 5 provider-expert roles (`claude-expert`, `gemini-expert`, `opencode-expert`, `continue-expert`, `copilot-expert`) and the `Copilot` provider were missing from `project-config.schema.json`, producing false validation warnings.
- **Consistency-check false positives**: placeholder checker now knows all `build_variables()` built-ins (orchestrator flags, generated tables) and the dynamic `PAL_*` / `PIPELINE_*_BLOCK` families; orchestrator-table check now finds roles that share a table cell.

### Changed

- **All ~41 generic agent templates condensed**: removed redundancy and dead weight (−1077 source lines); `xml-section-wrapping`, `critical-rules-footer`, and `viz.server` disabled in project.yaml — slimmer generated agents.
- **Concept documents**: verified implementation status annotated; central `CONCEPT_INVENTORY.md` removed.
- **Deduplicated sync warnings**: identical warnings (one per provider) are now reported once.
- **Claude provider switch**: project config moved from Gemini/Opencode to Claude-only output — `.claude/` regenerated (including the `doc-now` and `report-bug` commands), `.gemini/` removed.

---

## [0.57.1] — 2026-06-01

### Fixed

- **COCOPILOT.md typo**: Renamed `COCOPILOT.md` to `COPILOT.md` — fixes broken file reference for Copilot platform.
- **Gemini settings.json not initialized**: Gemini `settings.json` was never created during sync, causing missing configuration in Gemini projects.
- **Gemini orchestrator had zero tools**: Gemini orchestrator agent received an empty tool list, breaking all delegation capabilities.
- **Cross-block matching in conditional stripping**: Prevented false-positive matches when stripping inactive `{{#if}}` blocks across separate template sections.

### Changed

- **use-orchestrator rule shortened**: Reduced from 188 to 29 lines by extracting verbose content to lazy-load `_wf-use-orchestrator.md` file. (#280)
- **Orchestrator template reduced**: Shrunk from 547 to 323 lines (-41%) by extracting workflow details to `_wf-*.md` files.
- **PAL wiring completed**: Moved all provider-specific syntax from generic templates into platform adapter templates — full Provider Abstraction Layer integration. (#278)
- **Orphaned GEMINI.md removed**: Removed stale root-level `GEMINI.md` — Gemini now correctly reads `.gemini/GEMINI.md`.

---

## [0.57.0] — 2026-05-31

### Added

- **Provider Abstraction Layer (PAL)**: 3-layer architecture that eliminates cross-provider syntax leaks and enables clean orchestration across Gemini, Continue, and Copilot. Resolves Issue #277.
  - **Layer 1 — Generic Core**: Provider-agnostic agent templates in `1-generic/` remain strictly universal with zero provider-specific references.
  - **Layer 2 — Platform Adapters**: Provider-specific orchestration patches and syntax normalization in `2-platform/` for Gemini, Continue, and Copilot.
  - **Layer 3 — Bootstrap Engine**: Dynamic provider detection and config injection at sync-time, ensuring each generated agent receives only the tools and syntax valid for its target provider.
- **9 new files**: PAL core modules, provider adapter templates, and bootstrap engine components.
- **Provider-specific patches**: Gemini, Continue, and Copilot orchestration templates with native tool mapping and syntax isolation.
- **HowTo documentation**: Complete PAL setup guide and migration instructions for existing projects.

### Changed

- **5 modified files**: Agent templates updated to use PAL delegation patterns instead of direct provider references.
- **3 config files**: Provider registry, role defaults, and project config schema extended with PAL metadata.
- **2 Python modules**: `sync.py` and `scripts/lib/agents.py` updated for PAL bootstrap injection and provider-aware generation.

### Fixed

- **Cross-provider syntax leaks**: Eliminated provider-specific tool syntax (at-agent, claude -a, define_subagent) from generic templates that previously leaked into non-target provider environments.
- **Gemini/Continue/Copilot orchestration**: Each provider now receives native delegation syntax via platform adapters, fixing broken subagent dispatch in non-Claude environments.

---

## [0.56.0] — 2026-05-29

### Added

- **Checkpointing** (`scripts/lib/checkpoint.py`): Resume langer Orchestrierungen nach Session-Unterbrechung. Speichert den aktuellen Delegation-State und ermöglicht Wiederaufnahme ohne Wiederholung bereits abgeschlossener Sub-Tasks. (Issue #169)
- **Auto-Generated Delegation Table**: Die Delegationstabelle in generierten Agenten wird jetzt automatisch aus `config/role-defaults.yaml` erzeugt (managed block). Keine manuelle Pflege der Routing-Tabelle mehr nötig — neue Rollen erscheinen automatisch. (Issue #249)
- **SE-Cascade Runner** (`scripts/run-cascade.py`): Kommandozeilen-Runner für die Systems-Engineering-Cascade auf Plattformen ohne natives Subagent-Dispatch (insb. Gemini/Antigravity). Orchestriert die 6-level SE-Kaskade sequentiell mit State-Tracking. (Issue #209)

### Changed

- **Worker-Guard verschärft**: Orchestrator ist jetzt explizit als Router-Only definiert mit ABSOLUTEM VERBOT gegen Selbst-Implementierung von Worker-Aufgaben. Jeder Versuch des Orchestrators, Code selbst zu schreiben oder Tests selbst auszuführen, wird jetzt durch klare Anti-Recursion-Regeln blockiert. (Issue #260)

---

## [0.55.2] — 2026-05-28

### Changed

- **Orchestrator Platform Patches**: Replaced static `agents/2-platform/gemini-orchestrator.md` template with programmatic platform patches in `config.py` (`PLATFORM_ORCHESTRATOR_PATCHES` dict). Extended conditional block handling to support `{{#if}}...{{else}}...{{/if}}` and `{{#unless}}` syntax. Provider isolation set to disabled. (Issue #250)

---

## [0.55.1] — 2026-05-28

### Fixed

- **Orchestrator Agent Task Tool**: Added `Agent` task tool to orchestrator template, enabling proper subagent delegation in provider environments that support it.
- **Provider Tool Whitelists**: Added `Agent` to both Opencode and Claude provider tool whitelists (`config/provider-tools.yaml`), preventing sync warnings when the tool is referenced in agent templates.

---

## [0.55.0] — 2026-05-27

### Added

- **5 Provider Expert Agents**: New expert agents for each supported AI provider — `claude-expert`, `gemini-expert`, `opencode-expert`, `continue-expert`, `copilot-expert`. Each provides provider-specific configuration guidance, best practices, and troubleshooting.
- **1-generic/provider-expert.md**: Base template for provider expert agents with `based-on` composition pattern, enabling platform-specific overrides while maintaining a common expert structure.
- **Orchestrator Expert Routing**: Delegation table extended with expert-agent routing — users requesting provider-specific help are now routed to the matching expert agent.

### Fixed

- **Tool Name Permission Mapping**: Tool names normalized from lowercase to PascalCase across all generated agent frontmatter — fixes incorrect permission mapping in provider environments that expect exact tool name casing.
- **Consistency Checker based-on Detection**: Consistency checker now recognizes and validates `based-on` relationships between `1-generic/` and `2-platform/` agent templates, preventing broken composition chains.

### Changed

- **Expert Template hint Fields**: All provider expert templates now include descriptive `hint` fields in their frontmatter for better agent discovery and routing context.

---

## [0.54.2] — 2026-05-27

### Fixed

- **Stability and Validation**: Minor bugfixes and stability improvements discovered during the release process validation.

---

## [0.54.1] — 2026-05-27

### Fixed

- **Opencode JSON parsing**: Added `opencode.json` as a pure JSON alternative to `opencode.jsonc` to resolve parser warnings in strict JSON environments.

---

## [0.54.0] — 2026-05-27

### Added

- **Effort-Estimator Agent** (`agents/1-generic/effort-estimator.md`): New agent for structured task effort estimation with complexity scoring and time-range prediction. Supports the orchestrator's planning phase before task decomposition. (#246)
- **Outcome Cache** (`scripts/lib/cache.py`): SHA256-based delegation result cache with LRU eviction and configurable TTL. Reduces token costs for recurring orchestrator sub-tasks by caching previous outcomes. (#172)
- **Quality Pipeline Framework** (`scripts/lib/pipelines.py`): Configurable quality pipeline definitions with provider-specific injection. Enables project-level customization of the multi-stage quality flow (code-review → validate → release). (#164)
- **Reflection-Loop Infrastructure** (`scripts/lib/reflection.py`): Generator-Critic pair configuration (e.g., developer ↔ code-reviewer) with max-iterations and pair-enabling per project. Supports iterative quality improvement loops. (#163, #166)
- **Parallel Barrier Runtime** (`scripts/lib/runtime.py`): ThreadPoolExecutor-based barrier implementation for deterministic parallel subagent execution with per-agent and global timeout handling. (#240)
- **Provider Tool Whitelists** (`config/provider-tools.yaml`): Per-provider tool capability declarations. Prevents agents from referencing tools unavailable in their target provider environment. Documents unsupported Gemini tools. (#223, #240)
- **Path-Based Contextual Rules** (`config/rules-presets.yaml`): Rules can now be restricted to specific file paths via glob patterns, enabling context-aware rule activation (e.g., Python rules only for `.py` files). (#226)
- **Critical Rules Footer**: Every generated agent file now receives a critical-rules footer section at the bottom, ensuring essential policies (branch-guard, commit-conventions, provider-agnostic) are always visible. (#225)
- **Few-Shot Orchestration Examples**: Orchestrator template enhanced with concrete few-shot examples for FANOUT, PIPELINE, and PARALLEL_GROUP dispatch patterns. (#224)
- **XML Section Wrapping**: Generated agent files now use XML-tagged sections for key blocks, improving structural machine-parseability while maintaining human readability. (#227)
- **File-Affinity Check**: Parallel task execution now checks file-level conflicts before dispatching, preventing race conditions when multiple agents touch the same files. (#241)
- **Temperature, Steps, Deny-Permissions in Opencode Frontmatter**: Opencode agent generation now supports `temperature`, `steps` (execution step limit), and explicit `deny` permission rules in frontmatter. (#242)

### Changed

- **Orchestrator v3.12.0**: Integrated cache, pipelines, reflection-loops, barrier runtime, Gemini Auto-Handoff protocol, and anti-recursion guard into the delegation workflow. Entry-point hint updated with orchestrator-exclusive dispatch clarification.
- **SE Orchestrator v1.5.0**: Extended 6-level cascade with traceability enhancements and validation integration.
- **SE Requirements v1.5.0**: Enhanced requirements elicitation with improved traceability.
- **agent-meta-manager v1.9.0**: Clarified update-meta vs upgrade-meta commands. Added reflection-loop and quality pipeline configuration sections.

### Fixed

- **Orchestrator Auto-Handoff Clarification**: Prioritized native tool-calls over text-based `@orchestrator` triggering. Clarified `@orchestrator` as the sole direct-dispatch interceptor for all platforms. (#213, #214)
- **Gemini Auto-Handoff Protocol**: Gemini orchestrator now implements the full auto-handoff pattern with explicit planning-mode override, correcting missing functionality. (#208, #243)
- **Anti-Recursion Guard**: Worker agents now explicitly blocked from delegating back to the orchestrator, preventing infinite delegation loops. (#232, #242)
- **Opencode Frontmatter**: Removed invalid `memory` field, corrected `mode` resolution from template YAML instead of hardcoded `subagent`, and completed frontmatter for Continue and Claude/Opencode. (#239, #217, #220)
- **Gemini Agent Frontmatter**: Stripped unsupported config parameters, added proper tool mapping translation for Gemini native tools. (#222, #221)
- **Tool-Specific Placeholders**: Removed provider-tool references from 1-generic templates to maintain provider-agnostic invariance. (#210)
- **Agent Tool Exclusion**: `Agent` tool removed from generic template frontmatter to eliminate sync warnings across providers. (#236, #238)
- **Sync Schema Enums**: Updated enums to match current providers and roles, preventing validation errors. (#234, #237)
- **Bug-Feature-Analyzer**: Excluded from direct dispatch exceptions, enforcing orchestrator routing for issue triage. (#241)
- **Test-Repo Validation**: Parametrized path resolution for out-of-tree test-repository validation, supporting flexible test setups.

---

### Fixed

- **Regenerate all generated files** after orchestrator entry-point sentence fix (PR #231, commit 0225e0e). The fix adds an explicit exceptions reference to the orchestrator entry-point hint to prevent over-delegation for trivial non-development queries.

---

## [0.53.0] — 2026-05-24

### Added

- **`bug-feature-analyzer` agent**: New agent for automated GitHub issue triage and feature analysis. (#219)

### Fixed

- **Orchestrator self-execution guard**: Prevented orchestrator from executing worker tasks directly, enforcing proper delegation protocol.

---

## [0.52.1] — 2026-05-24

### Fixed

- **TOML escaping for Gemini /commands**: Fixed triple-quote escaping in `_md_to_toml()` to prevent invalid TOML when command bodies contain `"""`. (#206)
- **Orchestrator validator references**: Made `validator` agent references in orchestrator template conditional via `{{#if VALIDATOR_ENABLED}}`, preventing routing to non-existent agents in projects without `validator` in roles. (#204)
- **Inline conditional block preservation**: Fixed `strip_inactive_conditional_blocks()` to preserve inline table rows (no trailing newline) when stripping inactive `{{#if}}` blocks, preventing broken Markdown tables. (#196)
- **SE orchestrator schema**: Added `schemas/se-orchestrator.schema.json` for orchestration metadata validation. (#195)

### Changed

- **Orchestrator version**: 3.2.0 → 3.3.0 (conditional validator blocks = scope extension)

---

## [0.52.0] — 2026-05-24

### Added

- **11 new agent templates**: Complete SE right-wing (se-test-engineer, se-testreviewer, se-verifier, se-validator, se-integration-and-test-manager) and SWE agents (code-reviewer, ui-ux-designer, api-specialist, devops-engineer, performance-optimizer, export-manager). (#209)
- **Manual test framework**: Generic black-box test procedure with 15 scenarios (5 SE + 10 meta-agent), including `--dry-run` support, provider detection, auto-generated bug reports, and target-repository testing. (#209)
- **Export configuration**: New `config/export.yaml` for target-agnostic output routing (Markdown, Confluence, Jira-Xray). (#209)
- **Lifecycle hooks integration**: `se-validator` triggered on-release, `code-reviewer` on-merge. (#209)
- **Placeholder skills registry**: Future skill placeholders for mermaid-renderer, figma-reader, postman-collection-generator. (#209)

### Changed

- **Orchestrator routing table**: Extended with all 11 new agents and V&V workflows. (#209)
- **Validator/tester templates**: Refocused validator as process guardian, tester as isolated unit-test writer. (#209)
- **Role defaults**: Added 11 new roles with appropriate model tiers (balanced/powerful/fast). (#209)
- **Project config**: Activated all new SE and V&V roles. (#209)
- **Test restructure**: Moved automated tests to `tests/automated/`, manual tests to `tests/manual/`. (#209)

---

## [0.51.0] — 2026-05-24

### Fixed

- **Provider-agnostic approach for generic templates**: Corrected orchestrator model handling to ensure 1-generic templates remain provider-agnostic. The generic orchestrator no longer references provider-specific model IDs. (#208)

### Added

- **Planning-Mode section in orchestrator**: Added explicit planning-mode guidance for providers that support native planning (Gemini, Opencode), ensuring the orchestrator's planning phase takes precedence over provider-native planning. (#208)
- **Gemini Auto-Handoff protocol**: Gemini orchestrator now supports the same auto-handoff pattern as other providers, with explicit planning-mode override instructions. (#208)
- **New policy rule for generic templates**: Formalized the provider-agnostic policy as a standalone rule, preventing provider names, tool syntax, and API details from leaking into 1-generic templates. (#208)

### Changed

- Various minor corrections and clarifications across agent templates and rules. (#208)

---

## [0.49.0] — 2026-05-22

### Changed

- **Main Session Auto-Handoff Protocol**: Refactored the orchestrator-first architecture to empower the Main Session as a Smart Communication Interface. The Main Session can now read files and analyze context, but automatically delegates the execution to the Orchestrator via a tool call instead of generating a text refusal message.

---

## [0.48.0] — 2026-05-22

- Introduce Orchestrator-First Architecture with FANOUT, PARALLEL_GROUP, and BARRIER patterns for multi-agent orchestration.

---

## [0.47.2-beta] — 2026-05-21

### Added

- **Dry-Run Engine improvements**: Enhanced dry-run engine with German keyword support, word boundary matching, and better FANOUT splitting for more accurate orchestration simulation.

### Changed

- **README.md updated**: Added comprehensive documentation for orchestrator-first architecture v3.0.0 beta features.
- **Version bump**: Upgraded agent-meta to v0.47.0-beta in preparation for this release.

---

## [0.47.0-beta] — 2026-05-21

### Added

- **Orchestrator-First Architecture v3.0.0 (Beta)**: Universal router for all development tasks with task decomposition protocol (FANOUT/PARALLEL_GROUP/BARRIER). The orchestrator becomes the primary entry point, replacing direct main-chat code work.
- **Provider-Agnostic Parallel Execution Engine**: Supports 4 providers (Claude, Opencode, Gemini, Continue) with precise PARALLEL patterns per provider.
- **Unknown Intent Protocol**: Meta-Feedback Loop for unrecognized user intents with configurable fallback behavior.
- **User-Override Mechanism**: Trigger phrases ("Nicht delegieren", "Mach das hier", "Kein Orchestrator", etc.) allow users to bypass the orchestrator and work directly in main chat.
- **Orchestrator Configuration Switch**: Granular `enabled`/`strict`/`unknown-fallback` settings in `project.yaml` with three boolean flags (`meta-feedback`, `main-chat`, `ask-user`).
- **Orchestration Test Infrastructure**: Dry-run engine, fixtures, and test commands for validating orchestration behavior.
- **Trilingual Glossary** (EN/DE/Explanation): Comprehensive terminology reference for the meta-agent framework.

### Changed

- **`use-orchestrator` rule removed from `silent` preset**: Orchestrator usage is now always active, not preset-dependent.
- **Agent templates regenerated** with orchestrator-first architecture.

### Deferred (Phase 2 & 3)

- Phase 2: Selective Rule Embedding, Main Session Thinning
- Phase 3: Result Caching, Dynamic Batching, Agent Pooling
- See Issue #192 for tracking.

---

## [0.46.1] — 2026-05-21

### Fixed

- **Opencode frontmatter schema validation**: Removed `generated-from` field from Opencode agent frontmatter — caused schema validation error (`Extra inputs are not permitted`) in opencode. (#188)

---

## [0.46.2] — 2026-05-21

### Fixed

- **Opencode orchestrator permission mapping**: Added missing permission mapping for subagent task tool in opencode orchestrator agent. (#190)

---

## [0.50.0] — 2026-05-24

### Added

- **Systems Engineering (SE) Agent Cascade**: Introduced a 6-level recursive breakdown model with specialized agents: `se-requirements`, `se-architect`, `se-critic`, `se-interface-mgr`, `se-orchestrator`, and `se-termination`. Enables structured requirements-to-architecture workflows.
- **Requirements Quality Gate**: The `se-critic` agent now validates outputs from `se-requirements` before they are passed to `se-architect`, catching flawed requirements early before architecture work begins.
- **SE Config Integration**: Configuration support for the SE agent cascade, enabling project-specific tuning of the 6-level breakdown process.

---

## [0.47.2-beta] — 2026-05-21

### Added

- **Phase 2: Selective Rule Embedding** (`config/rules-presets.yaml`, `scripts/lib/context.py`, `scripts/lib/rules.py`): Rules can now be excluded from the Opencode managed block with `embed: false`. Excluded rules remain available as separate files (e.g. `.claude/rules/dod-criteria.md`). Default behavior unchanged (`embed: true`). Activated for `dod-criteria` and `sync-interface` in the `silent` preset.

### Changed

- **AGENTS.md thinning**: Main Session managed block reduced from ~580 to ~370 lines (-36%, -210 lines). 2 rules (`dod-criteria`, `sync-interface`) moved from embedded to file-only.
- **`/update-meta` command**: New command for syncing agent-meta without version upgrade.

---

## [0.46.0] — 2026-05-21

---

## [0.38.0] — 2026-05-11

### Added

- **Thread-Safe Event Logging** (`scripts/lib/viz.py`):
  - Added `threading.RLock` (`viz_lock`) for all read/write access to `events.jsonl`.
  - Atomic `clear-log` operation under the lock.
  - Tail-read heuristic for large logs (>1MB): reads last 10,000 lines instead of full file when a `since` filter is active.

- **Config-Driven Viz Server** (`scripts/viz-server.py`, `.meta-config/project.yaml`):
  - `viz.server.port` and `viz.server.timeout_sec` configurable via `project.yaml`.
  - `viz-server.py` reads settings from config; falls back to hardcoded defaults (8765 / 300s).

- **Dashboard UX Improvements** (`docs/live-dashboard.html`):
  - Toast notifications after log clear (with event count).
  - `localStorage` persistence for time-window selector and model-toggle state.
  - Graceful degradation when Cytoscape CDN fails to load.
  - Improved replay pause/resume precision via `pausedTotal` tracking.
  - Canvas resize synchronization with Cytoscape layout refit.

- **Documentation**:
  - `docs/viz-api.md` — Complete API endpoint reference.
  - `docs/viz-event-schema.md` — All 7 event types with field descriptions.
  - `docs/viz-architecture.md` — Design decisions (stable edge IDs, two-mode system, inactivity watcher, thread-safety).

### Changed

- **Code Quality** (`scripts/viz-report.py`):
  - Replaced `_state_to_json()` with `_DateTimeEncoder` for JSON serialization.
  - Extracted magic numbers to module constants (`_SESSION_FALLBACK_MINUTES`, `_MIN_EVENTS_FALLBACK`, etc.).
  - Consolidated duplicate status-icon mappings to `_STATUS_ICONS`.
  - Fixed XSS vector in `render_html()` by using `json.dumps()` instead of string interpolation for D3.js data.
  - Robust handling of events without timestamps (skip instead of crash).
  - Warning log for unknown `?window=` parameter values.
  - `import re` moved to module level (no more inline import).

---

## [0.37.0-beta.1] — 2026-05-10

### Added

- **Agent Visualization Dashboard** (`scripts/lib/viz.py`, `scripts/viz-report.py`, `docs/agent-mindmap.md`, `docs/agent-graph.html`):
  - **Static Mindmap**: Auto-generated Mermaid mindmap and interactive HTML graph of all agents, their delegations, and `workflow_tier` color-coding (🔴 required / 🔵 recommended / ⚪ optional). Generated via `sync.py --viz` or `sync.py --viz-only`.
  - **Dynamic Event Logging**: Opt-in mode where all generated agents receive a prompt block instructing them to write JSONL events (`agent_start`, `delegate`, `agent_end`, `tool_call`) to `.meta-viz/events.jsonl`. Sessions are per-run, gitignored, and auto-cleaned after `retention_days`.
  - **Four Viz Modes** (`project.yaml` → `viz.mode`): `off` (default), `static` (mindmap only), `dynamic` (event logging only), `full` (both mindmap + event logging).
  - **`viz-report.py` CLI**: Session reports in terminal (live watch), HTML (with Mermaid Gantt + sequence diagrams), or JSON. Optional Flask-based web server (`--serve`). Auto-cleanup of old sessions.
  - **Viz Commands**: `/viz-mindmap` (generate static viz), `/viz-report` (session report), `/viz-watch` (live monitoring), `/viz-toggle` (cycle or set viz mode: off→static→dynamic→full→off, then triggers sync).
  - **Howto** (`howto/agent-visualization.md`): Complete setup guide, manual event creation, JSONL format reference, session management, and architecture overview.
  - **Visualization prompt injection** applies to **all providers** (Claude, Continue, Gemini, Opencode) when `viz.mode` is `dynamic` or `full`.

---

## [0.36.0] — 2026-05-10

### Added

- **`log-analyzer` agent** (`agents/1-generic/log-analyzer.md`): Analysiert System- und Applikations-Logs mit Frequency-Clustering (Bash-basiert, vor LLM-Analyse), RFC-5424-konformer Severity-Klassifikation (CRITICAL/HIGH/MEDIUM/LOW/INFO), Auto-Discovery bekannter Log-Pfade (syslog, journald, Docker, Home Assistant, Nginx) und strukturierten Finding-Cards. Zwei Modi: `--quick` (Standard, token-sparend) und `--deep` (Codebase-Suche + Online-Recherche). Delegations-Routing zu `feedback`, `developer`, `security-auditor` und `requirements`. `workflow_tier: required`.
- **`homeassistant-log-analyzer` platform agent** (`agents/2-platform/homeassistant-log-analyzer.md`): Erweitert den generischen Log-Analyzer via `extends: + patches:` mit HA-spezifischem Log-Format, Logger-zu-Komponenten-Mapping, bekannten Fehlermustern (TemplateError, Platform not ready, MQTT disconnect, ZHA, Recorder), Startup-Rauschen-Filter und HA-spezifischen Delegations-Ressourcen (community.home-assistant.io, HACS).
- **`feedback` agent** (`agents/1-generic/feedback.md`): Standardisiert Bug-Reports, Feature-Requests und Verbesserungsvorschläge für das eingesetzte Projekt als GitHub Issues. Pflicht-Gate vor jeder direkten `git`-basierten Issue-Erstellung. Sechs Typen (`bug`, `feat`, `improvement`, `docs`, `security`, `question`) mit Body-Templates. Auto-Repo-Erkennung via `gh repo view`. Klare Abgrenzung zu `meta-feedback` (Framework vs. Projekt). `workflow_tier: required`.
- **`/analyze-logs` command** (`commands/1-generic/analyze-logs.md`): Delegiert an `log-analyzer`-Agent. Unterstützt optionalen Pfad und `--quick`/`--deep`-Flags. Wird für alle aktiven Provider generiert (Claude → `.claude/commands/`, Gemini → `.gemini/commands/` (`.toml`), Opencode → `.opencode/commands/`, Continue → `.continue/prompts/`).
- **`/feedback` command** (`commands/1-generic/feedback.md`): Delegiert an `feedback`-Agent. Unterstützt optionalen Typ-Keyword (`bug | feat | improvement | docs | security | question`) und Kurzbeschreibung als Argument. Wird für alle aktiven Provider generiert.
- **`/report-bug` command aktualisiert** (`commands/1-generic/report-bug.md`): Delegiert jetzt an `feedback`-Agent (Typ `bug` vorbelegt) statt eigenem Inline-Workflow — konsistent mit dem standardisierten Feedback-Kanal.
- **Orchestrator Workflow O + P** (`agents/1-generic/orchestrator.md`): Workflow O (Log-Analyse via `log-analyzer`) und Workflow P (Projekt-Issue via `feedback → gh issue create`) ergänzt. Beide neuen Agenten in der Agenten-Tabelle eingetragen.
- **`consistency-check.py`** (`scripts/consistency-check.py` + `scripts/lib/consistency/`): Neues Python-Script zur deterministischen Konsistenzprüfung von Agent-Templates, Commands und Cross-References ohne LLM-Aufruf. Prüft: Frontmatter-Version-Bumps (git-diff-basiert), semver-Format, extends/patches-Anchor-Auflösung, role-defaults-Vollständigkeit, Orchestrator-Tabelle, CHANGELOG-Erwähnungen, Platzhalter-Typos. Exit-Codes: 0=ok, 1=Fehler, 2=Script-Error. Flags: `--changed`, `--file`, `--strict`, `--json`, `--root`. Stdlib-only, PyYAML optional.
- **`/consistency-check` command** (`commands/1-generic/consistency-check.md`): Slash-Command ruft das Script auf, interpretiert Findings und bietet interaktive Fixes an. Wird für alle aktiven Provider generiert.
- **`agent-meta-manager` v1.5.0** (`agents/1-generic/agent-meta-manager.md`): Neuer Abschnitt 8 "Consistency-Check" mit vollständiger Referenz, Wann-ausführen-Tabelle und Link auf Howto.
- **Howto** (`howto/features/consistency-check.md`): Vollständige Referenz mit manueller Ausführung, allen CLI-Flags, Check-Katalog, JSON-Format, GitHub-Actions-Integration und Anleitung zum Hinzufügen neuer Checks.

---

## [0.35.0] — 2026-05-08

### Added

- **Provider config generation** (`scripts/lib/mcp.py` → `generate_provider_configs()`): sync.py now writes committed provider configs (with `${ENV_VAR}` references) and gitignored local configs (with actual values from `secrets.local.yaml`) for all active MCP servers. Supports all four formats: `claude-settings` (`.claude/settings.json`), `gemini-settings` (`.gemini/settings.json`), `opencode-json` (`opencode.json`), `continue-yaml` (`.continue/config.yaml`). Closes the Phase-2 gap from #86.
- **`init_secrets_template()`** (`scripts/lib/mcp.py`): `sync.py --init` now generates `.meta-config/secrets.local.yaml` from the active servers' `secrets:` lists. Users fill in actual values; the file is always gitignored.
- **`allow-committed-secrets`** in `project.yaml` / JSON Schema: new opt-out flag. `sync.py` reads the value and passes it to MCP config generation. Default: `false`.

### Changed

- **`write_checked()` now blocks on detected secrets** (`scripts/lib/io.py`): changed from warn-only to raising `SyncError` when a secret pattern is found in content destined for a committed file (`allow_secrets=False`, the new default). Local/gitignored files pass `allow_secrets=True` and continue to warn only. `sync.py` catches `SyncError` and exits with a clear message.
- **`SyncError`** added to `scripts/lib/io.py`: new exception class for fatal sync conditions.
- **`resolve_active_mcp_servers()` now respects `enabled-by-default`** (`scripts/lib/mcp.py`): servers added via platform bundles are only activated when their `enabled-by-default` flag is `true` (default). Servers explicitly listed in `mcp-servers:` in `project.yaml` are always activated regardless. Previously the flag had no effect.
- **`generate_mcp_artifacts()` signature extended** (`scripts/lib/mcp.py`): new `allow_committed_secrets` parameter threaded from `sync.py`.
- **`mcp-servers` and `allow-committed-secrets`** added to `config/project-config.schema.json`.

---

## [0.34.2] — 2026-05-07

### Added

- **MCP as first-class framework concept** (`config/mcp-registry.yaml`, `scripts/lib/mcp.py`, `scripts/lib/secrets.py`, `config/ai-providers.yaml`, `howto/mcp-setup.md`): global provider-agnostic MCP server catalog; rule file generation per active server + provider; automatic `.gitignore` entries for secrets files; secrets detection for MCP-generated content; platform bundles (`rules/2-platform/<platform>-mcp.yaml`). Closes #86.

### Security

- **Shell injection fixed** (`hooks/1-generic/dod-push-check.sh`, `lifecycle-check.sh`): Replaced `echo "$INPUT" | python3` pattern with heredoc-based stdin parsing. Eliminated `$DIR` interpolation into Python inline strings by passing the config path as `sys.argv[1]`. Closes #67, #75.
- **Secrets detection** (`scripts/lib/secrets.py`, `scripts/lib/io.py`): New `scan_for_secrets()` scans all generated files for API keys, tokens and passwords before writing. `write_checked()` helper integrates the scan into agents.py and rules.py with `[WARN]` output — does not block sync. Closes #68.

### Fixed

- **Gemini missing rules** (`config/rules-presets.yaml`): Removed all `gemini: skip` entries from `minimal` and `silent` presets. Gemini now receives `dod-criteria`, `issue-lifecycle`, `lifecycle-tasks`, `use-orchestrator` and `sync-interface` as plain rule files. Closes #71, #80.
- **Bare `except Exception:`** (`scripts/lib/agents.py`, `config.py`, `platform.py`, `skills.py`): All 6 broad exception catches replaced with specific types (`YAMLError`, `OSError`, `SubprocessError`, `JSONDecodeError`, `KeyError`). Closes #65.
- **Continue config.yaml never updating** (`scripts/lib/context.py`): Introduced a YAML-comment managed block (`# agent-meta:managed-begin/end`) that is refreshed on every sync with version and path metadata. User model configuration is left untouched. Closes #69.
- **Description truncation in non-Claude agents** (`scripts/lib/agents.py`): `extract_frontmatter_field()` now handles multi-line YAML folded strings — Continue and Opencode agents no longer get truncated descriptions. Closes #77.

### Performance

- **Incremental sync** (`scripts/lib/io.py`, `agents.py`, `rules.py`): `write_checked()` skips writing when content is already identical to the existing file. `sync.log` shows `[SKIP] unchanged` for unmodified files. Closes #70.

---

## [0.34.1] — 2026-05-07

### Security

- **`safe_path()` helper** (`scripts/lib/io.py`): New path traversal guard. Validates all generated file paths stay within the project root before writing. Prevents malicious config values (e.g. `prefix: "../../evil"`) from escaping the project directory.
- **All write operations secured** (`scripts/lib/agents.py`, `rules.py`, `hooks.py`, `commands.py`, `context.py`, `extensions.py`, `skills.py`): Every `write_text()`, `mkdir()`, and `unlink()` now uses `safe_path()`.

### Fixed

- Issue #64 — Path Traversal in sync.py (closed).

---

## [0.34.0] — 2026-05-07

### Added

- **`speech-mode: submissive`** (`speech/submissive.md`, `config/project-config.schema.json`, `README.md`, `howto/configs/*`): New communication style — completely devoted and submissive. Addresses user as master/mistress, no contradiction, no own opinion. No hardcoded mode list in syncer; works out-of-the-box via dynamic `speech/{mode}.md` resolution.
- Project config now uses `speech-mode: submissive` for agent-meta itself.

---

## [0.33.0] — 2026-05-07

### Added

- **Opencode provider** (`config/ai-providers.yaml`, `scripts/lib/agents.py`, `scripts/lib/commands.py`, `scripts/lib/context.py`): Full sync.py support for [opencode](https://opencode.ai) (sst/opencode), a terminal-based AI coding assistant with 75+ provider support.
  - Native agent frontmatter: `description`, `mode: subagent`, `model: anthropic/provider-id` (AI SDK convention)
  - Rules embedded into `AGENTS.md` managed block (opencode has no native rules/ dir); respects `opencode: skip` rule option; includes speech-mode
  - Commands: `.opencode/commands/*.md` — same `.md` + `$ARGUMENTS` format as Claude (no transformation needed)
  - Context: `AGENTS.md` with managed block (agent hints + all active rules)
  - Settings: `opencode.json` skeleton, created once, never overwritten
  - Model tiers: `anthropic/claude-*` IDs by default; configurable via `model-overrides.Opencode`
- **`AGENTS.personal.md`** (`howto/configs/AGENTS.personal-template.md`, `scripts/lib/context.py`): Personal opencode context file, analogous to `CLAUDE.personal.md`. Auto-created from template on first sync, gitignored, loaded via `instructions` field in `opencode.json`.
- **Provider-agnostic gitignore collection** (`scripts/sync.py`): `ensure_gitignore_entries` now collects `gitignore_entries` from ALL active providers, not only Claude. Previously non-Claude provider entries (e.g. `AGENTS.personal.md`) were silently dropped when Claude was absent.
- **Templates**: `howto/configs/OPENCODE.project-template.md`, `howto/configs/OPENCODE.settings-template.json`, `howto/configs/AGENTS.personal-template.md`
- **Docs**: `docs/providers/opencode.md`, updated `docs/providers/multi-provider.md`

---

## [0.32.0] — 2026-04-28

### Added

- **Provider-spezifische Modell-Tiers** (`config/ai-providers.yaml`, `config/role-defaults.yaml`, `scripts/lib/roles.py`): Fünf abstrakte Tiers (`nano`, `fast`, `balanced`, `powerful`, `max`) ersetzen Claude-spezifische Aliase in `role-defaults.yaml`. `sync.py` mappt Tiers per Provider auf konkrete Modell-IDs — Gemini bekommt jetzt korrekte Gemini-Modelle statt ungültige Claude-Aliase.
- **Provider-Tier-Mapping** (`config/ai-providers.yaml`): `model-tiers` und `model-aliases` pro Provider:
  - Claude: `nano/fast` → `claude-haiku-4-5-20251001` | `balanced` → `claude-sonnet-4-6` | `powerful/max` → `claude-opus-4-7`
  - Gemini: `nano/fast` → `gemini-2.5-flash` | `balanced/powerful/max` → `gemini-2.5-pro`
  - Continue: leer — Continue verwaltet Modelle zentral in `config.yaml`
- **Provider-spezifische `model-overrides`** (`config/project-config.schema.json`, `scripts/lib/roles.py`): Neues Format `model-overrides.Claude.git: fast` neben Legacy `model-overrides.git: fast`. Provider-Block hat Vorrang für den jeweiligen Provider; Legacy-Block gilt nur für Claude.
- **Rückwärtskompatibilität**: `haiku`/`sonnet`/`opus` als Aliase für Claude weiter gültig. Für andere Provider werden sie auf den entsprechenden Tier gemappt (`haiku` → `fast`, `sonnet` → `balanced`, `opus` → `powerful`).
- **Konkretes `run_in_background`-Beispiel** (`agents/1-generic/orchestrator.md` v2.5.0): Orchestrator zeigt jetzt Python-Code-Pattern für parallele Delegation (Vordergrund + `run_in_background=True`).

### Fixed

- **Gemini-Agenten hatten ungültige `model:`-Felder** (`scripts/lib/agents.py`): `model: haiku` oder `model: sonnet` wurden in Gemini-Frontmatter geschrieben — Gemini CLI ignoriert oder lehnt diese ab. Alle Gemini-Agenten erhalten jetzt korrekte Gemini-Modell-IDs.

---

## [0.31.0] — 2026-04-27

### Added

- **Debug Mode** (`scripts/lib/agents.py`, `config/project-config.schema.json`): New `debug-mode: true/false` flag in `project.yaml`. When active, `sync.py` injects a debug block into every generated agent — agents announce themselves (`[Agent: <name>]`), log delegations (`→ Delegiere an: ...`), and confirm completion (`✓ [Agent: <name>] fertig`). Default: `false` — zero change to any agent file.
- **Provider filter for hooks** (`hooks/1-generic/`, `scripts/lib/hooks.py`): New `# provider: <name>` metadata in hook scripts. Hooks declaring a specific provider (e.g. `Claude`) are skipped for all other providers (e.g. Gemini). `lifecycle-check.sh` and `dod-push-check.sh` now correctly declare `# provider: Claude`.

### Changed

- **`orchestrator` v2.4.0** (`agents/1-generic/orchestrator.md`): Agents table now includes all roles — `feature`, `release`, `meta-feedback`, `agent-meta-manager` added; `tester`, `validator`, `docker` annotated as optional/conditional.

### Fixed

- **Gemini/Continue received Claude-specific hooks** (`scripts/lib/hooks.py`): `lifecycle-check.sh` and `dod-push-check.sh` use the Claude Code hook API (JSON on stdin) and must not be copied to Gemini/Continue hook directories. Provider filter now enforces this.

---

## [0.30.0] — 2026-04-27

### Added

- **`session-conclusion.md` Rule** (`rules/1-generic/`): New generic rule enforcing session-end recognition in main chat and orchestrator. Defines session-end signals and requires documenter delegation.
- **`rules-preset-optimization.md` Howto** (`howto/features/`): New document explaining word-count thresholds, preset selection guide (`default`/`minimal`/`silent`), and lazy-load `_wf-` pattern for platform-heavy projects.
- **Configurable `.gitignore` behavior** (`scripts/sync.py`, `config/project-config.schema.json`): New `gitignore` section in `project.yaml` with three boolean flags — `local` (default: true), `generated` (default: false), `settings` (default: false). `generated: true` gitignores all provider agents/rules/hooks/commands dirs.
- **Post-merge branch cleanup** (`agents/1-generic/git.md` v2.2.0): New section with keep/delete signal detection (open TODOs, disabled automations, Phase-2 hints) and user-confirmation flow.
- **InfluxDB `measurement_schema` + `timezone` config** (`platform-configs/homeassistant.defaults.yaml`): New fields `influxdb_measurement_schema` (`by_entity`/`by_unit`) and `influxdb_timezone` prevent query failures from unknown schema or UTC offset.
- **Multi-tool strategy (AGENTS.md)** (`howto/features/sync-concept.md`): New section documenting `CLAUDE.md` ↔ `AGENTS.md` symlink pattern for teams using multiple AI tools.
- **Folder-level CLAUDE.md** (`howto/features/sync-concept.md`): New section with use cases and comparison table vs. `-ext.md`.

### Changed

- **`meta-feedback` agent v2.0.0** (`agents/1-generic/meta-feedback.md`): Complete rewrite with explicit decision tree and 10 typed issue templates — `bug`, `feat`, `new-agent`, `new-command`, `new-skill`, `new-platform`, `new-speech`, `improvement`, `docs`, `design`. Each type has its own title prefix, label set, and body template.
- **`orchestrator` v2.3.0** (`agents/1-generic/orchestrator.md`): Session-end now offers documenter (conclusions) and workflow K (feedback) explicitly.
- **`git` agent v2.2.0** (`agents/1-generic/git.md`): Post-merge cleanup decision block added.
- **`agent-meta-manager` v1.4.2** (`agents/1-generic/agent-meta-manager.md`): Section 6 now includes `--create-rule`, `--create-command`; section 8 adds active `wc -l` length check with threshold table; Don'ts add AGENTS.md symlink guidance.
- **`branch-guard.md` genericized** (`rules/1-generic/branch-guard.md`): `sync.py`-specific logic removed — rule now applies cleanly to non-agent-meta projects.
- **`agent-meta-sync-interface.md` extended** (`rules/2-platform/`): Branch-guard extension for `sync.py` added here (agent-meta-specific only).
- **`_wf-ha-mcp-local.md`** (`rules/2-platform/`): InfluxDB section now shows measurement schema and timezone context.
- **`sync-concept.md`** (`howto/features/`): `.gitignore` config section, folder-level CLAUDE.md, multi-tool AGENTS.md strategy, and `gitignore` field in project.yaml table.

### Fixed

- **`branch-guard.md`** (`rules/1-generic/`): Was leaking agent-meta-internal `sync.py` references into generic projects. (#57)

---

## [0.29.0] — 2026-04-25

### Added

- **Lazy-load `_wf-*.md` pattern** (`agents/1-generic/`, `rules/2-platform/`): Verbose workflow content extracted into `_wf-*.md` files that are skipped by `sync.py` and read on-demand via Read tool. Reduces always-loaded rule/agent tokens by 60–85%.
- **`rules-preset` framework** (`config/rules-presets.yaml`): Central control for `alwaysApply: false` (Claude + Continue) and `gemini: skip` per rule. Configured in `project.yaml` with preset inheritance (`default`, `minimal`, `silent`). Analogous to `dod-preset`.
- **Provider-aware `sync_rules()`** (`scripts/lib/rules.py`): Now receives `provider` parameter — injects `alwaysApply: false` frontmatter for Claude/Continue, skips rules entirely for Gemini based on preset config.
- **DoD conditional blocks in agent templates**: `{{#if DOD_X}}...{{/if}}` blocks in `feature.md`, `validator.md` — inactive DoD features produce zero output in generated agents.
- **New lazy-load knowledge files** (`agents/1-generic/`): `_wf-sync-interface.md`, `_wf-git-ops.md`, `_wf-security-audit.md`, `_wf-claude-review.md`, `_wf-feedback.md`, `_wf-scout.md`, `_wf-skill-lifecycle.md`, `_wf-upgrade.md`, `_wf-issue.md`.
- **New lazy-load knowledge files** (`rules/2-platform/`): `_wf-ha-package-migration.md`, `_wf-ha-entity-data.md`, `_wf-ha-mcp-local.md`, `_wf-ha-energy-template.md`, `_wf-sharkord-docker-binaries.md`, `_wf-sharkord-mediasoup.md`.

### Changed

- **Slim platform rules** (`rules/2-platform/`): `homeassistant-package-structure.md`, `homeassistant-entity-data.md`, `homeassistant-mcp-integration.md`, `homeassistant-energy-abstraction.md`, `sharkord-docker-ops.md`, `sharkord-sdk.md` — core constraints only, workflow detail moved to `_wf-*.md`.
- **Slim 1-generic rules**: `branch-guard.md`, `use-orchestrator.md`, `dod-criteria.md` — decision tree and verbose examples removed.
- **Slim agents** (`agents/1-generic/`): `orchestrator.md`, `git.md`, `agent-meta-manager.md`, `security-auditor.md` — workflow content extracted to `_wf-*.md` files.
- **`collect_rule_sources()`** (`scripts/lib/rules.py`): Now filters `_` prefix in both `1-generic` and `2-platform` layers — same pattern as `collect_sources()` in `agents.py`.

### Fixed

- **`strip_inactive_dod_blocks()` IndexError** (`scripts/lib/config.py`): Wrong group index `m.group(2)` (regex had only one capture group). Fixed via Python default argument closure.

---

## [0.28.1] — 2026-04-19

### Fixed

- **`context.py`: CLAUDE.md never created on `--init`** (`scripts/lib/context.py`): Template paths for `CLAUDE.project-template.md` and `CLAUDE.personal-template.md` corrected from `howto/` to `howto/configs/` — templates had been moved there but the paths were not updated.
- **`first-steps.md`: wrong `project.yaml.example` path** (`howto/setup/first-steps.md`): `cp` command corrected from `howto/project.yaml.example` to `howto/configs/project.yaml.example`.

---

## [0.28.0] — 2026-04-19

### Added

- **HA platform: MCP-Server-Guidelines** (`rules/2-platform/homeassistant-mcp-integration.md`): Neue Sektion "Lokale / Projektspezifische MCP-Server" — Dokumentationskonvention für lokale MCP-Server via `platform-config.yaml`, gitignore-Hinweise, Fallback-Strategie.
- **HA platform: project.yaml Template** (`howto/configs/project.yaml.homeassistant.example`): HA-spezifisches Beispiel ohne Build-Artifact-Felder, mit YAML/Jinja2-Kontext und HA-typischer Rollen-Whitelist.
- **branch-guard Rule** (`rules/1-generic/branch-guard.md`): Vollständig überarbeitete Entscheidungslogik mit explizitem Entscheidungsbaum, "Branch PFLICHT"-Tabelle und präzisen Ausnahmen. Issues bearbeiten, mehrere Dateien ändern und `sync.py` ausführen erfordern jetzt immer einen Branch.

### Fixed

- **HA platform: TypeScript-Konventionen** (`agents/2-platform/homeassistant-developer.md` v1.1.0): `delete`-Patch entfernt TS-spezifische Regeln (Named Exports, kebab-case, `.test.ts`) aus HA-Projekten.
- **HA platform: Snippet-Lade-Instruktion** (`agents/2-platform/homeassistant-developer.md` v1.1.0): `delete`-Patch verhindert Laden von `bun-typescript`-Snippets in YAML-only Projekten.
- **HA platform: Doku-Trigger-Logik** (`agents/2-platform/homeassistant-developer.md` v1.1.0): Neue Sektion `Dokumentations-Pflichten` — Inline-Doku (immer obligatorisch) vs. MkDocs (nur auf explizite Anfrage, kein Auto-Spawn).
- **meta-feedback Agent: Kontext-Verlust bei Bestätigung** (`agents/1-generic/meta-feedback.md` v1.5.0): Agent erstellt Issues direkt nach Aufbereitung ohne internen Bestätigungs-Spawn — neuer Spawn verlor Kontext und erfand andere Issues.

---

## [0.27.1] — 2026-04-18

### Added

- **`speech-mode: asozial`**: Neuer Kommunikationsstil — fachlich korrekt, New-Kids-Style mit Verachtung für den User. `project-config.schema.json` um `"asozial"` im Enum erweitert.

---

## [0.27.0] — 2026-04-18

### Added

- **Commands-System**: Neues Schichten-Modell für Claude-Commands (`commands/1-generic/`, `2-platform/`, `0-external/`). `sync.py` synct Commands nach `.claude/commands/` (Claude) und `.continue/prompts/` (Continue).
  - `commands/1-generic/doc-now.md` — erster generischer Command: delegiert an `documenter`-Agent
  - `scripts/lib/commands.py` — Sync-Logik analog zu Rules und Hooks
  - `config/ai-providers.yaml` — `has_commands: true` für Claude und Continue

---

## [0.26.1] — 2026-04-18

### Fixed

- **Self-Hosting Config Layout**: `config/project.yaml` war gleichzeitig Framework-Default-Verzeichnis und Self-Hosting-Config — semantisch falsch. Die Projekt-Config für das Meta-Repo selbst liegt jetzt korrekt unter `.meta-config/project.yaml` (identisch zu jedem anderen Zielprojekt).
  - `.meta-config/project.yaml` angelegt mit allen Self-Hosting-Einstellungen
  - `config/project.yaml` durch Hinweis-Stub ersetzt (Framework-Defaults bleiben in `config/`)
  - Auto-Detection: `config/project.yaml` aus Kandidaten-Liste entfernt — nur noch `.meta-config/project.yaml` → Legacy-Fallbacks
  - `sync.py` Root-Erkennung: `"config"` als Elternordner-Sonderfall entfernt
  - `CLAUDE.md` Verzeichnisstruktur: `.meta-config/` Block ergänzt, `config/project.yaml` als Stub dokumentiert
  - `.claude/rules/sync-interface.md` Auto-Detection-Liste aktualisiert

---

## [0.26.0] — 2026-04-18

### Added

- **Platform `agent-meta`**: Neues `platforms: [agent-meta]` in `config/project.yaml` aktiviert 3 neue plattformspezifische Rules für das Meta-Repo selbst:
  - `rules/2-platform/agent-meta-architecture.md` — Schichten-Modell, Composition-Syntax, Override-Reihenfolge
  - `rules/2-platform/agent-meta-conventions.md` — Invarianten, Versions-Bump-Tabelle, Rollen- und Platzhalter-Lifecycle
  - `rules/2-platform/agent-meta-sync-interface.md` — sync.py Flags, log-Format, Python-Modulstruktur
- **`agents/2-platform/agent-meta-developer.md`**: Erweiterter Developer-Agent speziell für das Meta-Repo (extends `1-generic/developer.md`). Ergänzt um Python-Stdlib-Only-Regel, ≤600-Zeilen-Modul-Grenze, SyncLog-Pflicht, keine `print()` in `lib/`.
- **Rules-Substitution**: `sync_rules()` wendet jetzt `substitute()` auf Rule-Inhalte an — Rules bekommen projektspezifische Variablen injiziert (z.B. `{{DOD_REQ_TRACEABILITY}}`, `{{CODE_LANGUAGE}}`).
- **`rules/1-generic/commit-conventions.md`**: Kanonische Commit-Konventions-Rule für alle Projekte — ersetzt duplizierte Tabellen in Agent-Templates.
- **`rules/1-generic/dod-criteria.md`**: DoD-Checkliste als Rule mit echten Projekt-Werten via Variablen-Substitution — jedes Projekt sieht seine tatsächlich konfigurierten DoD-Features.

### Changed

- **Config-Restructuring**: Framework-Config liegt jetzt sauber in `config/` (Meta-Repo-owned); Projektconfig in `.meta-config/project.yaml` (Projekt-owned, unabhängig von Submodul-Pfad und AI-Provider).
  - Auto-Detection: `.meta-config/project.yaml` → `config/project.yaml` → Legacy-Fallbacks
  - `--fill-defaults` schreibt in erkannte Config-Datei
- **`agents/1-generic/developer.md`** (2.0.1): Doppelte Commit-Tabelle entfernt — verweist auf Rule.
- **`agents/1-generic/validator.md`** (2.0.1): Doppelte DoD-Checkliste entfernt — verweist auf Rule.
- **`agents/1-generic/orchestrator.md`** (2.0.1): Veraltete Config-Pfad-Referenzen auf `.meta-config/project.yaml` aktualisiert.
- **`agents/1-generic/git.md`** (2.0.1): Veraltete `agent-meta.config.yaml` Referenzen bereinigt.
- **`agents/1-generic/agent-meta-manager.md`** (1.1.1): Alle 15 `agent-meta.config.yaml` Referenzen auf `.meta-config/project.yaml` aktualisiert.

### Fixed

- **`config.py` `substitute()`**: `{{%VAR%}}` Escape-Syntax funktionierte nicht — escaped Werte wurden vor der Substitution in echte Platzhalter umgewandelt und dann als fehlende Variablen gewarnt. Fix: Stash-before/restore-after Sentinel-Mechanismus.

---

## [0.25.1] — 2026-04-17

### Fixed

- **CLAUDE.md**: Veraltete Referenzen auf `ROLE_MAP in sync.py`, `DOD_DEFAULTS in sync.py`
  und `MANAGED_BLOCK_TEMPLATE in sync.py` korrigiert — zeigen jetzt auf die richtigen
  Dateien (`roles.config.yaml`, `dod-presets.config.yaml`, `templates/managed-block.md`,
  `scripts/lib/dod.py`).
- **CLAUDE.md**: Verzeichnisstruktur um `scripts/lib/`, `templates/` und
  `providers.config.yaml` ergänzt.
- **howto/sync-concept.md**: Struktur um neue Module aktualisiert.
- **howto/upgrade-guide.md**: `MANAGED_BLOCK_TEMPLATE` → `templates/managed-block.md`.

---

## [0.25.0] — 2026-04-17

### Added

- **`scripts/lib/`** — sync.py in 13 eigenständige Module aufgeteilt (log, io, config,
  roles, dod, platform, providers, agents, rules, hooks, skills, extensions, context).
  Jedes Modul ist ≤600 Zeilen und einzeln lesbar — optimiert für LLM-gestützte Entwicklung.
- **`providers.config.yaml`** — `PROVIDER_CONFIG` aus sync.py ausgelagert.
  Neuen AI-Provider (Cursor, Windsurf, ...) hinzufügen ohne Python-Code-Änderung.
  Enthält auch `gitignore_entries` pro Provider.
- **`templates/`** — Managed-Block-Templates als echte Dateien statt Multiline-Strings im Code:
  `managed-block.md`, `managed-block-project-stub.md`, `claude-md-managed.md`

### Changed

- **`scripts/sync.py`**: 3151 → 259 Zeilen — reiner CLI-Entrypoint.
  Alle Logik in `scripts/lib/` Module verschoben.
- **`roles.config.yaml`**: `ROLE_MAP` wird jetzt dynamisch aus den Rollen-Keys gebaut —
  kein separates Dict mehr im Python-Code.
- **`dod-presets.config.yaml`**: `DOD_DEFAULTS` hardcoded Dict entfernt —
  das `full`-Preset dient als Fallback (war inhaltlich identisch).

---

## [0.24.0] — 2026-04-17

### Added

- **YAML config format** — All configuration files now use YAML as the primary format.
  JSON is still supported as a backward-compatible fallback (auto-detected by file extension).
  - `agent-meta.config.yaml` replaces `agent-meta.config.json`
  - `roles.config.yaml` replaces `roles.config.json`
  - `dod-presets.config.yaml` replaces `dod-presets.config.json`
  - `external-skills.config.yaml` replaces `external-skills.config.json`
- **`scripts/migrate-config.py`** — Migration helper: converts an existing
  `agent-meta.config.json` to `agent-meta.config.yaml`. Strips `_comment*` keys,
  preserves multiline strings as YAML block scalars, renames original to `.json.bak`.
  Usage: `py .agent-meta/scripts/migrate-config.py --config agent-meta.config.json`
- **`howto/agent-meta.config.example.yaml`** — YAML version of the example config
  (replaces `agent-meta.config.example.json`).

### Changed

- **`sync.py`**: `load_config()` now accepts `.yaml` / `.yml` files directly.
  When `--config agent-meta.config.json` is passed but a `.yaml` sibling exists,
  the YAML file is preferred automatically (zero-friction migration).
  `fill_defaults` write-back also writes YAML when the config is YAML.
- **`sync.py`**: `load_dod_presets()`, `load_roles_config()`,
  `load_external_skills_config()` all prefer `.yaml` over `.json` fallback.
- **`sync.py`**: `add_skill` (`--add-skill`) writes `external-skills.config.yaml`.
- All documentation and howto files updated: `.config.json` → `.config.yaml`.

### Migration

Existing projects on JSON configs continue to work unchanged.
To migrate a project config to YAML:

```bash
py .agent-meta/scripts/migrate-config.py --config agent-meta.config.json
py .agent-meta/scripts/sync.py --config agent-meta.config.yaml
```

---

## [0.23.0] — 2026-04-16

### Added

- **Platform Config Instantiation** — `sync.py` now reads `platform-configs/<platform>.defaults.yaml`
  and merges platform-level defaults into the project config before generating agents.
  Projects using a platform get sensible variable defaults without manual repetition.
  Supports `variables`, `dod`, `model-overrides`, `memory-overrides`, `permission-mode-overrides`.
- **HomeAssistant platform** (`platform-configs/homeassistant.defaults.yaml`) — Platform defaults
  for Home Assistant Python integrations (Python language, German docs, YAML conventions).
- **Sharkord platform config** (`platform-configs/sharkord.defaults.yaml`) — Extracted shared
  Sharkord defaults (Bun/TypeScript, plugin structure, build commands) into platform config.
- **HomeAssistant agents** (`agents/2-platform/`):
  - `homeassistant-developer.md` — HA-specific developer with Python/HACS conventions
  - `homeassistant-documenter.md` — HA-specific documenter
- **HomeAssistant rules** (`rules/2-platform/`):
  - `homeassistant-energy-abstraction.md` — Energy platform integration patterns
  - `homeassistant-entity-data.md` — Entity state/attribute data conventions
  - `homeassistant-mcp-integration.md` — MCP server integration guide
  - `homeassistant-notifications.md` — Persistent notification patterns
  - `homeassistant-package-structure.md` — HACS package layout conventions
  - `homeassistant-yaml-conventions.md` — HA YAML configuration patterns
- **Sharkord rules** (`rules/2-platform/`):
  - `sharkord-docker-ops.md` — Docker operations for Sharkord plugins
  - `sharkord-sdk.md` — Sharkord SDK usage patterns
- **`howto/platform-config.md`** — Full documentation for the platform config system.

### Changed

- **`sharkord-developer.md`**: Reduced to platform-specific overrides only; shared content
  moved to `sharkord.defaults.yaml` and rules files.
- **`sharkord-docker.md`**, **`sharkord-release.md`**: Minor updates aligned with platform config.
- **`sync.py`**: Added `load_platform_defaults()` and `merge_platform_defaults()` functions.
  Platform defaults are merged at sync start — project config values always win.

---

## [0.22.0] — 2026-04-14

### Added

- **`--fill-defaults`** — New `sync.py` parameter that writes missing structural config fields
  (`dod-preset`, `max-parallel-agents`, `speech-mode`, `dod.*`) with their schema defaults
  into `agent-meta.config.yaml`. Missing `variables.*` keys are reported as `[WARN]` only —
  no empty strings written (no sensible default exists for project-specific variables).
  Supports `--dry-run`. Useful for onboarding new projects or auditing existing configs.

---

## [0.21.0] — 2026-04-12

### Added

- **Multi-Provider Support** (`ai-providers` array in `agent-meta.config.yaml`):
  Projects can now target Claude, Gemini, and Continue simultaneously.
  Backward-compatible: legacy `ai-provider` string field still works.
- **Continue integration**: sync.py generates `.continue/agents/`, `.continue/prompts/`,
  and `.continue/rules/` for use with local LLMs (Ollama, ROCm, etc.) via Continue IDE extension.
  Controlled by `provider-options.Continue.generate-prompts` and `prompt-mode` (`full` | `slim`).
- **`provider-options` config block**: Per-provider options with schema validation.
  Currently active: `Continue.generate-prompts`, `Continue.prompt-mode`.
- **`speech-mode`** — Configurable agent communication style:
  Generates `.claude/rules/speech-mode.md` (auto-loaded by Claude Code into all agent contexts).
  Modes: `full` (default, no rule), `short` (facts only, no filler), `childish` (playful,
  animal/toy analogies, emojis), `caveman` (brutally short, cave-speak).
  No agent template changes needed — purely via the Rules layer.
- **`speech/` directory**: Mode definition files (`short.md`, `childish.md`, `caveman.md`, `full.md`).
  Add new modes by dropping a file here and extending the schema enum.
- **Howto files**: `howto/multi-provider.md`, `howto/CONTINUE.config-template.yaml`,
  `howto/CONTINUE.project-template.md`, `howto/GEMINI.project-template.md`.

### Changed

- **`agent-meta.schema.json`**: Added `ai-providers` (array), `provider-options` (object),
  `speech-mode` (enum) fields with full validation.
- **`sync.py`**: `sync_speech_mode()` function — copies speech rule on sync, removes it on `full`.
  `resolve_provider_options()`, `resolve_providers()` for multi-provider resolution.
  Continue prompt generation (`sync_prompts_for_continue()`).
- **CLAUDE.md**: `speech-mode` config section, `speech/` in directory structure,
  updated `provider-options` documentation.
- **`howto/agent-meta.config.example.json`**: Added `speech-mode`, `provider-options` examples.

### Migration from v0.20.0

No breaking changes — fully backward-compatible.

- `speech-mode` is optional. If absent (or `"full"`), no rule is generated — behavior unchanged.
- `ai-provider` (string) still works. `ai-providers` (array) is the new preferred form.
- `provider-options` is optional. Omitting it keeps all existing behavior intact.

## [0.20.0] — 2026-04-08

### Added

- **DoD-Presets** (`dod-preset` in `agent-meta.config.yaml`):
  Predefined quality profiles that set defaults for all DoD criteria.
  Three built-in presets: `full` (all checks, default), `standard` (tests yes, REQ-IDs no),
  `rapid-prototyping` (all off — max speed). Individual overrides via `dod` block.
  Precedence: `dod` override > `dod-preset` > `full`.
- **`dod-presets.config.yaml`**: New config file defining presets. Meta-maintainer managed.
  Easy to extend: add a new preset entry, update schema enum.
- **DoD visibility**: Resolved DoD values now appear in CLAUDE.md managed block
  (preset name + all criteria). sync.log shows `[INFO] DoD preset '...' -> ...`.
- **`DOD_PRESET` template variable**: Auto-injected by sync.py, available in agent templates.
- **`dod-push-check` hook v1.1.0**: Now includes Branch-Guard — blocks `git push` on
  main/master. TEST_COMMAND missing = skip test gate (was: hard block).

### Changed

- **CLAUDE.md**: DoD section restructured — `dod-preset` as primary entry, `dod` as override.
  Added "how to add new presets" and "how to add new columns" instructions.
- **agent-meta.schema.json**: New `dod-preset` field (enum: full, standard, rapid-prototyping).
  `dod` description updated (override semantics).
- **Example config** (`howto/agent-meta.config.example.json`): Added `dod-preset` field.

### Migration from v0.19.0

No breaking changes — fully backward-compatible.

- `dod-preset` is optional. If absent, `full` is used (same behavior as before).
- Existing `dod` blocks continue to work as overrides on top of the preset.
- The `dod-push-check` hook is opt-in (requires `"hooks": {"dod-push-check": {"enabled": true}}`).

## [0.19.0] — 2026-04-07

### Added

- **OpenSCAD Developer Agent** (`1-generic/openscad-developer.md` v1.0.0):
  Specialized developer role for parametric 3D model generation in OpenSCAD.
  - Render-Inspect-Refine Loop as core workflow (visual feedback via MCP)
  - Mandatory gates: `validate_scad` before render, `analyze_model` before export
  - MCP-agnostic: works without MCP server (writes .scad directly), full loop with openscad-mcp
  - Print optimization knowledge: tolerances, overhangs, wall thickness, `$fn` guidelines, hole correction formula
  - Parametric-by-default: all dimensions as named variables, parameter table as standard output
  - Skill-aware: discovers opengrid-openscad and home-organization skills at runtime
  - BOSL2-aware: checks via `get_libraries`, uses library features when available
  - Versioned iteration: `model_v01.scad` → `model_v02.scad` — never overwrites previous state
- New role in `roles.config.yaml`: tier `optional`, model `sonnet`, memory `local`
- New role in `agent-meta.schema.json` roles enum
- ROLE_MAP entry in `sync.py`

### Changed

- **CLAUDE.md**: Role classification, model defaults, memory defaults, dependency map updated
- **README.md**: Supported Platforms and Agent Roles tables updated

### Fixed

- **`.gitignore` missing `agent-memory-local/`**: Local agent memory directories were not
  gitignored. Added `.claude/agent-memory-local/` to `GITIGNORE_ENTRIES` in `sync.py`
  and to the managed .gitignore block.

## [0.18.0] — 2026-04-07

### Added

- **Configurable Definition of Done** (`dod` block in `agent-meta.config.yaml`):
  Four independently toggleable quality criteria: `req-traceability` (default: true),
  `tests-required` (default: true), `codebase-overview` (default: true),
  `security-audit` (default: false). Missing `dod` block = all defaults (backward-compatible).
  `sync.py` injects `{{DOD_REQ_TRACEABILITY}}`, `{{DOD_TESTS_REQUIRED}}`,
  `{{DOD_CODEBASE_OVERVIEW}}`, `{{DOD_SECURITY_AUDIT}}` as template variables.
- **Role tier classification** (`tier` field in `roles.config.yaml`):
  `required` (orchestrator, developer, git), `recommended` (tester, validator, documenter,
  requirements, feature), `optional` (all others). Tier is a recommendation — all roles
  are generated by default. Users control via `roles` whitelist.
- **Parallel agent execution** (`max-parallel-agents` in config + schema):
  Configurable limit (1–5, default: 2). Orchestrator and feature workflows now mark
  parallelizable steps with `∥`. `run_in_background` guidance in coordinator templates.
- **Agent delegation map** (`howto/agent-delegation-map.md`): Complete matrix of all
  agent-to-agent references (delegation vs. referral), Mermaid graph, role categories,
  parallelizable groups, common delegation paths.
- **Branch-Guard (Step 0)** in orchestrator workflows A, B, E, L: Prevents direct
  commits on main/master. Creates `feat/`, `fix/`, `refactor/` branches automatically.
- **Workflow N** in orchestrator: External skill repo suggestion — orchestrates
  scout evaluation → manager activation → git commit.
- **Commit type `ci`** added to all commit convention tables.
- **External Skill lifecycle** in agent-meta-manager (7.1–7.7): Status matrix,
  activate, deactivate, add-skill, user feedback, submodule management, consistency check.
- **Feedback type `external-skill`** in meta-feedback agent with label support.

### Changed

- **orchestrator.md** v1.7.0 → v2.0.0: Configurable DoD (tiered checklist),
  conditional workflow steps (`?` marker), Branch-Guard, parallel steps (`∥`),
  DoD-Status block with injected variables.
- **developer.md** v1.4.1 → v2.0.0: REQ-ID requirement conditional on `req-traceability`,
  dual workflow (with/without REQ), commit table corrected, DoD-Status block.
- **validator.md** v1.3.1 → v2.0.0: Traceability audit conditional on `req-traceability`,
  DoD checklist tiered (always-active + conditional sections), DoD-config reference table.
- **git.md** v1.3.0 → v2.0.0: Commit types corrected (`chore` → never REQ-ID),
  dual examples (with/without req-traceability), `REQ-Traceability` status in header.
- **feature.md** v1.1.0 → v1.2.0: Conditional lifecycle steps (`?` marker),
  parallel validation+documentation (6∥7), DoD-Status block.
- **agent-meta-manager.md** v1.0.0 → v1.1.0: Seven skill lifecycle sub-workflows.
- **meta-feedback.md** v1.3.2 → v1.4.0: External skill feedback type + label.
- **roles.config.yaml**: `tier` field added to all roles, `developer` description
  simplified (removed "nach REQ-IDs" — now conditional).
- **agent-meta.schema.json**: `dod` block, `max-parallel-agents` field.
- **CLAUDE.md**: DoD config section, commit format with Conventional Commits explanation,
  role classification table, Branch-Guard in workflows, auto-injected variables list updated.

### Fixed

- **`chore` commit type** falsely required REQ-ID in all commit convention tables.
  Example (`chore: bump version to 1.2.0`) contradicted the table. Now correctly: never.
- **DoD was monolithic** — all-or-nothing with no way to disable REQ-traceability,
  tests, or codebase overview per project. agent-meta itself has no REQUIREMENTS.md
  but enforced REQ-IDs in its own DoD.
- **Orchestrator workflows A, B, E, L** had no branch-guard — allowed direct commits
  on main/master without user confirmation.

### Migration from v0.17.0

No breaking changes — all new features are opt-in with backward-compatible defaults.

- `dod` block is optional. If absent, all defaults apply (same behavior as before).
- `max-parallel-agents` defaults to 2. Set to 1 to keep sequential behavior.
- `tier` in `roles.config.yaml` is informational — does not filter roles.
- Agent templates now contain `?`-marked steps that respect DoD config. With default
  config (all true), behavior is identical to v0.17.0.
- Commit conventions now correctly exempt `chore`, `docs`, `ci` from REQ-ID requirement.
  If your project used `chore(REQ-xxx):` format, it still works but is no longer required.

---

## [0.17.0] — 2026-04-07

### Added

- **Hooks-Schichten-System** (`hooks/`): Vier-Schichten-Modell analog zu Rules und Agents.
  `sync.py` kopiert Hook-Skripte aus `0-external/`, `1-generic/`, `2-platform/` nach `.claude/hooks/`.
  Stale-Tracking via `.claude/hooks/.agent-meta-managed`.
  Registrierung in `.claude/settings.json` nur bei Opt-in: `"hooks": {"<name>": {"enabled": true}}`.
  Settings.json wird bei jedem Sync gemergt (Hooks-Section) — nicht mehr nur einmalig angelegt.
- **`dod-push-check.sh`** (`hooks/1-generic/`): Blockiert `git push` wenn Tests nicht grün sind.
  Liest `TEST_COMMAND` aus `agent-meta.config.yaml` oder `$AGENT_META_TEST_COMMAND`.
- **`--create-hook <name>`** in `sync.py`: Erstellt `.claude/hooks/<name>.sh` als Template.
  Projekt-eigene Hooks — nie von sync.py überschrieben.
- **`init_settings_local_json()`** in `sync.py`: Erstellt `.claude/settings.local.json` Skeleton
  beim ersten Claude-Sync (`--init` oder `ai-provider: Claude`). Einmalig, nie überschrieben.
- **`howto/hooks.md`** (neu): Vollständige Dokumentation des Hooks-Systems —
  Schichten, Sync-Verhalten, dod-push-check Konfiguration, Abgrenzung zu Rules.
- **`permissionMode`-Injection** in `sync.py`: `resolve_permission_mode()` +
  `inject_permission_mode_field()` — analog zu `model` und `memory`.
  Liest aus `roles.config.yaml` (Meta-Default) oder `permission-mode-overrides` in
  `agent-meta.config.yaml` (Projekt-Override).
- **`permission_mode`-Feld in `roles.config.yaml`**: `validator` → `plan`,
  `security-auditor` → `plan`. Alle anderen Rollen leer (Standard-Verhalten).
- **`permission-mode-overrides`** in `agent-meta.config.yaml`: Projekte können einzelne Rollen
  überschreiben. Gültige Werte: `plan`, `acceptEdits`, `bypassPermissions`, `default`.
- **`agent-meta.schema.json`** (neu): Vollständiges JSON Schema Draft-07 für
  `agent-meta.config.yaml`. Validiert alle Top-Level-Keys, Enum-Werte für
  `model-overrides` (haiku/sonnet/opus), `memory-overrides` (project/local/user),
  `permission-mode-overrides` (plan/acceptEdits/bypassPermissions/default), Hooks, External Skills.
- **Optionale Schema-Validierung** in `sync.py`: Wenn `jsonschema` installiert ist,
  werden Config-Fehler als Warnings ausgegeben (graceful fallback wenn nicht installiert).
- **`howto/agent-isolation.md`** (neu): Dokumentation für `isolation: worktree` —
  Wann sinnvoll, bekannte Fallstricke (Submodule, Merge-Konflikte, Windows), Konfiguration.
- **`rules/1-generic/issue-lifecycle.md`** (neu): Erste generische Rule.
  Erinnert alle Agenten daran, GitHub Issues nach Abschluss zu kommentieren und zu schließen.

### Changed

- **Agent-Descriptions bereinigt**: Alle `1-generic/*.md` Templates hatten
  „Generisches Template für den X-Agenten." in der `description:` — entfernt.
  Ersetzt durch prägnante, einzeilige Beschreibungen ohne interne Implementierungsdetails.
  Wirkt sich sofort auf den Claude Code Agent-Picker aus (nach nächstem Sync).
- **`git.md`** v1.2.0 → v1.3.0: DoD-Hooks-Sektion + Workflow 7 (Issue schließen nach Arbeit).
- **`feature.md`** v1.0.0 → v1.1.0: Frontmatter-Kommentar mit `isolation: worktree` Opt-in-Hinweis.
- **`CLAUDE.md`**: Hooks-System, permissionMode-Overrides, JSON-Schema, settings.json-Verhalten,
  settings.local.json-Init, agent-isolation.md — alle neuen Konzepte vollständig dokumentiert.
- **`howto/instantiate-project.md`**: `$schema`-Zeile im Config-Template ergänzt.
- **`agent-meta.config.yaml`** (self-hosting): `$schema`-Referenz ergänzt.

### Migration von v0.16.5

Keine Breaking Changes.

- Neue Dateien in `.claude/hooks/` werden automatisch angelegt — kein Opt-in nötig.
- `.claude/settings.json` wird bei aktivierten Hooks gemergt. Bestehende Dateien ohne
  Hooks-Section bleiben unverändert bis ein Hook aktiviert wird.
- `.claude/settings.local.json` wird beim nächsten Sync (wenn nicht vorhanden) erstellt.
- `validator` und `security-auditor` erhalten `permissionMode: plan` im generierten Agent.
  Falls das für ein Projekt nicht gewünscht ist:
  `"permission-mode-overrides": {"validator": "default"}` in `agent-meta.config.yaml`.

---

## [0.16.5] — 2026-04-06

### Added

- **Rules-Schichten-System** (`rules/`): Vier-Schichten-Modell analog zu Agenten.
  `sync.py` kopiert Rules aus `0-external/`, `1-generic/`, `2-platform/` nach `.claude/rules/`.
  Platform-Rules (`<platform>-<name>.md`) überschreiben gleichnamige Generic-Rules.
  Stale-Tracking via `.claude/rules/.agent-meta-managed` — entfernt veraltete Managed-Rules.
- **`--create-rule <name>`** in `sync.py`: Erstellt `.claude/rules/<name>.md` als leeres Template.
  Überschreibt nie bestehende Dateien.
- **`howto/rules.md`** (neu): Vollständige Dokumentation des Rules-Systems —
  Schichten, Sync-Verhalten, Naming-Konvention, Abgrenzung zu Extensions.
- **`CLAUDE.md`**: Rules-Abschnitt ergänzt (Vier-Schichten-Modell, Sync-Verhalten,
  Abgrenzung zu Extensions), Update-Verhalten-Tabelle um Rules-Zeilen erweitert,
  Verzeichnisstruktur um `rules/` ergänzt.

### Migration von v0.16.4

Keine Breaking Changes. `sync.py` läuft silent durch wenn `rules/1-generic/` leer ist —
kein Log-Eintrag, kein Warning.

---

## [0.16.4] — 2026-04-06

### Added

- **`howto/agent-memory.md`** (neu): Vollständige Dokumentation des Agent-Memory-Systems —
  drei Scopes (`project`, `local`, `user`), Konfiguration via `roles.config.yaml` +
  `memory-overrides`, MEMORY.md-Struktur-Empfehlungen, `.gitignore`-Verhalten.
- **`memory:`-Injection in `sync.py`**: `resolve_memory()` + `inject_memory_field()` —
  liest Memory-Scope aus `roles.config.yaml` (Meta-Default) oder `memory-overrides` in
  `agent-meta.config.yaml` (Projekt-Override). Wird nach `model:` in den Frontmatter injiziert.
- **`memory`-Feld in `roles.config.yaml`**: Memory-Scope-Defaults für alle Rollen.
  `validator`, `documenter`, `requirements`, `security-auditor` → `project`;
  `agent-meta-scout` → `local`; alle anderen → leer (kein Gedächtnis).
- **`memory-overrides`** in `agent-meta.config.yaml`: Projekte können einzelne Rollen
  überschreiben. Precedence: Projekt-Override > Meta-Default > kein Feld.
- **`CLAUDE.md`**: `memory-overrides`-Abschnitt mit Scopes-Tabelle und Defaults ergänzt.

### Migration von v0.16.3

Keine Breaking Changes — generierte Agenten bekommen ggf. ein neues `memory:`-Feld,
wenn `roles.config.yaml` einen Default definiert. Wer das nicht möchte: `"memory-overrides": { "<rolle>": "" }` im Projekt setzen.

---

## [0.16.3] — 2026-04-06

### Changed

- **`roles.config.yaml`** (neu): Modell-Defaults aus `sync.py` ausgelagert —
  Meta-Maintainer pflegt Rollen + empfohlene Modelle + Beschreibungen zentral in dieser Datei.
  `sync.py` liest Defaults von dort statt aus einer hardkodierten Konstante.
- **`sync.py`**: `DEFAULT_MODEL_MAP`-Konstante entfernt → `load_roles_config()` liest
  `roles.config.yaml`; `resolve_model()` nimmt `agent_meta_root` als Parameter.
- **`CLAUDE.md`**: `model-overrides`-Abschnitt zeigt auf `roles.config.yaml` statt sync.py;
  Verzeichnisbaum um `roles.config.yaml` ergänzt.

### Migration von v0.16.2

Keine Breaking Changes — Verhalten identisch. Modell-Anpassungen jetzt in
`roles.config.yaml` statt in `sync.py`.

---

## [0.16.2] — 2026-04-06

### Added

- **Zentrales Modell-Mapping** (`DEFAULT_MODEL_MAP` in `sync.py`): Meta-Maintainer pflegt
  empfohlene Claude-Modelle pro Rolle. `sync.py` injiziert `model:`-Feld beim Generieren.
- **`model-overrides`** in `agent-meta.config.yaml`: Projekte können einzelne Rollen überschreiben.
  Precedence: Projekt-Override > Meta-Default > kein Feld (erbt vom Parent).
- **`resolve_model()`** + **`inject_model_field()`** in `sync.py`: neue Hilfsfunktionen.
  `inject_model_field()` fügt `model:` nach `name:` ein, überschreibt bestehende Werte,
  oder entfernt das Feld wenn kein Modell konfiguriert (sauberer Output).
- **`[INFO]`-Log** in `sync.log` bei Model-Injection: zeigt gesetztes Modell + Quelle
  (`meta default` vs. `project override`).
- **`agents/1-generic/security-auditor.md`** (v1.0.0-beta): neuer generischer Agent für
  statische Sicherheitsanalyse — OWASP Top 10, Secrets, Dependencies, Supply Chain, Crypto.
  Read-only (kein Write/Edit), kein Alarm-Fanatismus, klare Abgrenzung zu `validator`/`tester`.

### Changed

- `scripts/sync.py`: `DEFAULT_MODEL_MAP` Konstante + `resolve_model()` + `inject_model_field()`
- `scripts/sync.py`: `sync_agents()` ruft Model-Injection nach `build_frontmatter()` auf
- `CLAUDE.md`: neuer Abschnitt `model-overrides` mit vollständiger Defaults-Tabelle
- `CLAUDE.md`: `roles`-Whitelist um `agent-meta-scout` und `security-auditor` ergänzt

### Meta-Defaults (injiziert wenn kein Projekt-Override)

| Modell | Rollen |
|--------|--------|
| `haiku` | `git`, `meta-feedback`, `docker` |
| `sonnet` | `tester`, `validator`, `documenter`, `security-auditor`, `agent-meta-scout`, `agent-meta-manager`, `release` |
| *(leer)* | `orchestrator`, `developer`, `requirements`, `ideation`, `feature` |

---

## [0.16.1] — 2026-04-06

### Added

- **`agents/1-generic/agent-meta-scout.md`** (v1.0.0): neuer generischer Agent — scoutet das
  Claude Code Ökosystem auf neue Skills, Agenten-Rollen, Rules und Workflow-Patterns.
  Liest `evaluate-repository.md` aus dem `awesome-claude-code` Submodule als Evaluation-Framework.
  Wird **ausschließlich auf explizite Nutzer-Anfrage** gestartet (kein Auto-Trigger).
- **`external/awesome-claude-code`**: neues Git Submodule (Meta-Repo mit kuratierten Claude-Skills).
  Gepinnt auf `3d8bde25`. Kein Skill-Wrapper — wird direkt vom `agent-meta-scout` per Read-Tool genutzt.
- **`external-skills.config.yaml`**: neuer `repos`-Eintrag für `awesome-claude-code`.
- **Orchestrator Workflow M**: "Claude-Ökosystem scouten" — explizite Trigger-Liste,
  `agent-meta-scout` in Agenten-Tabelle eingetragen.

### Changed

- `scripts/sync.py`: `ROLE_MAP` um `agent-meta-scout` erweitert
- `agents/1-generic/orchestrator.md` (v1.6.1 → v1.7.0): Agenten-Tabelle + Workflow M ergänzt
- `CLAUDE.md`: Agenten-Tabelle + Abhängigkeitskarte um `agent-meta-scout` erweitert

---

## [0.16.0] — 2026-04-06

### Added

- **Agent Composition System** (`extends:` + `patches:` in frontmatter): 2-platform and 3-project
  override agents can now compose from a base template instead of maintaining full copies.
  sync.py resolves composition at build time — the generated `.claude/agents/<role>.md` is a
  fully assembled document with no composition metadata.
- **Four patch operations:**
  - `append-after`: insert content after a named section
  - `replace`: replace a complete section (heading + body)
  - `delete`: remove a section entirely
  - `append`: append content at end of document
- **Section-aware Markdown parsing** in `sync.py`: `_find_section_bounds()` identifies sections
  by heading level, enabling precise patch targeting
- **`compose_agent()`** in `sync.py`: loads base template, applies patches, merges frontmatter;
  `extends:` and `patches:` keys are stripped from the generated output
- **`howto/agent-composition.md`**: full documentation — concept, patch ops, anchor reference,
  frontmatter-merge rules, debugging guide, 3-project compatibility
- **`agents/2-platform/sharkord-developer.md`** rebuilt as composition agent (v2.0.0):
  no longer a full copy of `1-generic/developer.md` — uses `extends:` + 3 patches

### Changed

- `sync.py`: `sync_agents()` detects `extends:` in frontmatter and invokes `compose_agent()`
  before variable substitution — full-replacement mode (no `extends:`) is unchanged
- `sync.py`: new import `pyyaml` (optional; warns gracefully if not installed)
- `agents/2-platform/sharkord-developer.md`: version bumped to 2.0.0, rebuilt as composition file
- `CLAUDE.md`: Schichten-Modell section updated — two modes for 2-platform, composition syntax,
  Entscheidungsbaum updated, howto reference added

### Notes

- **Backwards compatible:** existing platform agents without `extends:` continue to work unchanged
- **Requires PyYAML:** `pip install pyyaml` — sync.py warns and falls back to full-replacement
  if PyYAML is not available

---

## [0.15.1] — 2026-04-05

### Changed

- `agents/0-external/_skill-wrapper.md` (v1.1.0): replaced `{{SKILL_CONTENT}}` inline embedding
  with lazy Read-Instruktion — agent reads `.claude/skills/<skill>/SKILL.md` on demand
- `sync.py` — `normalize_skill_paths()`: rewrites `./ref.md` paths in copied SKILL.md to
  `.claude/skills/<skill>/ref.md` — consistent paths regardless of source repo structure
- `sync.py` — new template variables `SKILL_ENTRY_PATH` + `SKILL_BASE_PATH`; `SKILL_CONTENT` removed

---

## [0.15.0] — 2026-04-05

### Breaking Changes

- `external-skills.config.yaml`: `"submodules"` renamed to `"repos"` — update existing configs
- `external-skills.config.yaml`: `"enabled"` renamed to `"approved"` (meta-maintainer quality gate)
- `external-skills.config.yaml`: skill key `"submodule"` renamed to `"repo"`
- `external-skills.catalog.json`: removed — content merged into `external-skills.config.yaml`
- Projects must now opt-in to external skills via `"external-skills"` block in `agent-meta.config.yaml`

### Added

- **Two-gate system for external skills:** `approved: true` (meta-maintainer) + `enabled: true` in project config both required
- **`repos` section** in `external-skills.config.yaml`: 1:n relationship to skills, with `pinned_commit` for deterministic versioning
- **`pinned_commit` enforcement:** `sync.py` warns on every sync if submodule deviates from pinned commit
- **`add_skill()`** now auto-pins current commit to `pinned_commit` on registration
- **Project opt-in:** new `"external-skills"` block in `agent-meta.config.yaml` activates approved skills per project
- **`[WARN]`** for unknown or non-approved skills referenced in project config
- **`howto/external-skills.md`**: comprehensive howto with ASCII diagrams, full lifecycle (Skill-Autor → Meta-Maintainer → Projekt-Entwickler), `--add-skill` parameter reference, log output guide, troubleshooting, versioning strategy
- **`howto/first-steps.md`**: guided AI-assisted setup for first-time config

### Changed

- `sync.py` — `check_pinned_commits()`: new function, runs on every sync
- `sync.py` — `_skill_is_active()`: centralized two-gate check helper
- `sync.py` — `add_skill()`: writes `approved: false` as default, prints activation instructions
- `agents/1-generic/agent-meta-manager.md`: fixed skill deactivation instructions (was pointing to wrong config level)
- `howto/upgrade-guide.md`: migration guide for Breaking Changes
- `howto/instantiate-project.md`: external skills section updated, links to new howto
- `README.md`, `CLAUDE.md`: updated references, split `&&`-chained commands into individual blocks

### Migration from 0.14.x

See [howto/upgrade-guide.md](howto/upgrade-guide.md) — section "Breaking Change: v0.14.4 → approved".

In `external-skills.config.yaml`:
- Rename `"submodules"` → `"repos"`, add `"pinned_commit"` to each repo entry
- Rename `"enabled"` → `"approved"` in each skill entry
- Rename `"submodule"` → `"repo"` in each skill entry

In each project's `agent-meta.config.yaml`:
- Add `"external-skills": { "skill-name": { "enabled": true } }` for each desired skill

---

## [0.14.4] — 2026-04-05

### Added

- `howto/first-steps.md`: AI-assisted guided setup — hand this file to any AI assistant before the first sync for an interactive, step-by-step config walkthrough

### Changed

- `README.md` — Quick Start and Upgrading sections: split `&&`-chained commands into individual code blocks for granular review; added `first-steps.md` hint
- `howto/instantiate-project.md` — Step 1: split `&&`-chained commands; added tip box linking to `first-steps.md`
- `howto/agent-meta.config.example.json` — `_comment` references `first-steps.md`
- `CLAUDE.md` — directory structure updated to include `first-steps.md`

---

## [0.14.3] — 2026-04-05

### Fixed

- `sync.py` — stale agent cleanup: generated agents that are no longer in the active role set (removed from `config['roles']` or role no longer in ROLE_MAP) are now automatically deleted from `.claude/agents/` on every sync (`[DELETE]` in log). External skill agents are excluded from cleanup. Works in `--dry-run` mode.

---

## [0.14.2] — 2026-04-05

### Added

- `howto/CLAUDE.personal-template.md`: template for personal Claude preferences (gitignored, never committed)
- `sync.py` — `init_claude_personal()`: copies `CLAUDE.personal-template.md` to `CLAUDE.personal.md` in target project on first sync (only when `ai-provider: Claude`); idempotent

### Changed

- `sync.py` — `.gitignore` entries are ensured on every sync (not just once) — missing entries are appended; existing entries untouched
- `CLAUDE.md` — update-behavior table revised: added `CLAUDE.personal.md`, `.claude/settings.json`, `.gitignore` rows with committed/gitignored column
- `howto/sync-concept.md` — sync behavior table expanded; Team vs. Persönlich table updated with "Angelegt von" column
- `howto/instantiate-project.md` — commit command includes `.gitignore`; checklist expanded

## [0.14.1] — 2026-04-05

### Added

- `sync.py` — `init_settings_json()`: creates `.claude/settings.json` (team permissions skeleton) in target project if not present (only when `ai-provider: Claude`)
- `sync.py` — `ensure_gitignore_entries()`: ensures `.claude/settings.local.json`, `CLAUDE.personal.md`, and `sync.log` are in `.gitignore`; creates `.gitignore` if absent (only when `ai-provider: Claude`)

---

## [0.14.0] — 2026-04-04

### Added

- `agents/1-generic/agent-meta-manager.md` — new agent for managing agent-meta in a target project: upgrade, sync, feedback delegation, project-specific agent creation, external skill discovery
- `agents/1-generic/feature.md` — new workflow agent for full feature lifecycle (Branch → REQ → TDD → Dev → Validate → PR) via sub-agent delegation; does not implement anything itself
- `external-skills.catalog.json` — catalog of known/recommended external skill repositories; read by `agent-meta-manager` to help users discover available skills
- `scripts/sync.py` — `ROLE_MAP`: added `agent-meta-manager` and `feature` roles
- `howto/instantiate-project.md` — `feature` and `agent-meta-manager` added to generated agents table

---

## [0.13.2] — 2026-04-04

### Added

- `hint` frontmatter field in all 11 `1-generic` + 2 `2-platform` agent templates — short user-facing description used in `CLAUDE.md` agent table
- `sync.py` — `build_agent_hints()`: reads `hint` (preferred) or `description` from each active agent's template; generates `{{AGENT_HINTS}}` with orchestrator start hint + role table
- `sync.py` — `{{AGENT_HINTS}}` auto-injected variable, available in all templates
- `CLAUDE_MD_MANAGED_TEMPLATE` — new "Verfügbare Agenten" section with `{{AGENT_HINTS}}` + orchestrator entry point hint; technical table moved to subsection
- `howto/CLAUDE.project-template.md` — same agent sections added to `--init` template

### Fixed

- **#4** `howto/CLAUDE.project-template.md` — removed stale `{{PLATFORM_LAYER}}`, `{{TARGET_PLATFORM}}`; replaced `{{KEY_DEPENDENCIES}}` with `{{SYSTEM_DEPENDENCIES}}`
- **#4** `sync.py` — escape syntax `{{%VAR%}}` renders as `{{VAR}}` in output without triggering substitution (for literal docs)
- **#4** `agents/2-platform/sharkord-docker.md` — literal `{{PLATZHALTER}}` escaped to `{{%PLATZHALTER%}}`
- **#5** `sync.py` — generated agents now preserve template `description` field (with optional `{{PROJECT_NAME}}` interpolation) instead of overwriting with generic `"Agent for …"`
- `sync.py` — `build_agent_table()` and `build_agent_hints()` now respect `config['roles']` whitelist — excluded roles no longer appear in CLAUDE.md tables

---

## [0.13.1] — 2026-04-04

### Added

- `ai-provider` config field: controls provider-specific behavior; `"Claude"` enables automatic `CLAUDE.md` creation and managed block updates on every sync
- `{{AI_PROVIDER}}` variable: auto-injected from `ai-provider` config field, available as placeholder in all agent templates
- `sync.py` — if `ai-provider: Claude` and no `CLAUDE.md` exists, it is created automatically from template (no `--init` flag needed)
- `sync.py` — if `ai-provider` is not `Claude` but `CLAUDE.md` exists, managed block update is skipped with `[INFO]` log entry

### Fixed

- `sync.py` — replaced Unicode symbols (`ℹ`, `✓`, `✗`, `⚠`, `↓`) with ASCII equivalents to fix `UnicodeEncodeError` on Windows terminals (cp1252)

---

## [0.13.0] — 2026-04-04

### Added

- `sync.py` — `CLAUDE.md` managed block support: `<!-- agent-meta:managed-begin/end -->` block in project `CLAUDE.md` is updated on every normal sync with current `AGENT_TABLE`, version, and date
- `sync.py` — `sync_claude_md_managed()`: if `CLAUDE.md` exists but has no managed block, emits actionable `[WARN]` with copy-paste snippet to insert the block manually
- `howto/CLAUDE.project-template.md` — agent table now wrapped in managed block so `--init` creates a sync-maintained section out of the box
- `howto/instantiate-project.md` — note about managed block behavior added to Step 3
- `CLAUDE.md` — "Update-Verhalten bei sync" table extended with `CLAUDE.md` managed block rows + explanation

### Changed

- `sync.py` — all log output (warnings, skip reasons, info messages, print statements) is now **English only**
- `sync.py` — generated agent `description` field changed from `"Agent für …"` to `"Agent for …"`

---

## [0.12.3] — 2026-04-04

### Added

- `sync.py` — optional `"roles"` whitelist in config: only listed roles are generated; absent key = all roles (backwards-compatible). Skipped roles logged as `[SKIP]`.
- `sync.py` — `log.info()` method: disabled external skills now logged as `[INFO]` (always visible, not mixed with `[SKIP]`)
- `sync.py` — uninitialized submodule detection: if `external/<name>` dir is empty, emits actionable `[WARN]` with `git submodule update --init --recursive` hint
- `CLAUDE.md` — new "Config-Felder" section documenting `roles` whitelist

### Fixed

- **#1** `howto/agent-meta.config.example.json` — `_comment_snippets` now explicitly states path is relative to `.agent-meta/snippets/` (not `.claude/snippets/`)
- **#2** `meta-feedback.md` (`1.3.2`) — issue titles always in English regardless of `DOCS_LANGUAGE`; rule added to Don'ts and Sprache section
- **#3** `howto/instantiate-project.md` — `git submodule update --init --recursive` added to setup instructions

### Changed

- `agent-meta.config.yaml` (self-hosting) — `roles` whitelist added, excludes `docker` + `tester` → 0 warnings on sync
- `agent-meta.config.example.json` — `roles` field documented with comment

---

## [0.12.2] — 2026-04-04

### Added

- Neue Variable `{{USER_INPUT_LANGUAGE}}` — Sprache in der der Nutzer Anweisungen gibt (Agent-Input), unabhängig von `COMMUNICATION_LANGUAGE` (Agent-Output)
- `howto/agent-meta.config.example.json` — `USER_INPUT_LANGUAGE` mit Kommentar ergänzt

### Changed

- Alle 13 Agenten-Templates (`+0.0.1` Patch): `USER_INPUT_LANGUAGE` in `## Sprache`-Sektion ergänzt
  - `1-generic`: orchestrator `1.6.1`, developer `1.4.1`, tester `1.4.1`, validator `1.3.1`, requirements `1.3.1`, documenter `1.3.1`, release `1.3.1`, docker `1.3.1`, git `1.1.1`, meta-feedback `1.3.1`, ideation `1.2.1`
  - `2-platform`: sharkord-release `1.3.1`, sharkord-docker `1.2.1`
  - `0-external`: _skill-wrapper `1.0.1`
- `howto/agent-meta.config.example.json` nach `howto/` verschoben (war bisher im Repo-Root)
- Alle Referenzen auf `agent-meta.config.example.json` aktualisiert: README, CLAUDE.md, ARCHITECTURE.md, howto/*, orchestrator.md
- CLAUDE.md — `COMMUNICATION_LANGUAGE` Beschreibung präzisiert (End-User Output), `USER_INPUT_LANGUAGE` in Variablen-Tabelle ergänzt

---

## [0.12.1] — 2026-04-04

### Added

- `orchestrator.md` (`1.6.0`) — Workflow L: GitHub Issue bearbeiten (Issue lesen → requirements → tester → developer → tester → validator → documenter → git close)
- `git.md` (`1.1.0`) — `gh issue` Kommandos: list, view, close mit Comment, PR mit "Closes #id"

---

## [0.12.0] — 2026-04-04

### Added

- **`1-generic/git.md`** (`1.0.0`) — neuer Git-Agent: Commits, Branches, Merges, Tags, Push/Pull, Commit-Messages, plattformunabhängig (GitHub, GitLab, Gitea)
- Neue Variablen: `{{GIT_PLATFORM}}`, `{{GIT_REMOTE_URL}}`, `{{GIT_MAIN_BRANCH}}`
- `sync.py` ROLE_MAP + CLAUDE.md: `git`-Rolle registriert

### Changed

- `orchestrator.md` (`1.5.0`) — `git`-Agent in Agenten-Tabelle; Git-Commits in Workflows A/B/E/H1/H2 an `git` delegiert; Commit-Konventionen-Sektion entfernt (→ `git.md`); DoD-Punkt aktualisiert
- `release.md` (`1.3.0`) — Release-Workflow Schritt 5→6 umgestellt: `git tag` → Delegation an `git`; Checkliste + Delegation aktualisiert
- `sharkord-release.md` (`1.3.0`) — Schritt 6 (Commit + Tag + Push) als Delegation an `git`-Agenten formuliert; Checkliste aktualisiert

---

## [0.11.0] — 2026-04-04

### Added

- **`0-external` Layer** — neuer Agenten-Layer für externe Skill-Pakete aus Drittrepos
- `agents/0-external/_skill-wrapper.md` — generisches Wrapper-Template: Header + `{{SKILL_CONTENT}}` Substitution + lazy `additional_files`
- `external-skills.config.yaml` — zentrale Skill-Konfiguration (Modell A): Submodule-URLs + Skill-Mapping + `enabled: true/false` Aktivierung
- `sync.py` — `sync_external_skills()`: generiert `.claude/agents/<role>.md` + kopiert Skill-Dateien nach `.claude/skills/<skill-name>/`
- `sync.py` — `--add-skill <repo-url> --skill-name --source --role [--entry]`: registriert Git Submodule + legt Config-Eintrag an
- CLAUDE.md — vollständiger "External Skills (0-external Layer)"-Abschnitt mit Konzept, Konfigurationsformat, Workflow, Versionierung

### Changed

- CLAUDE.md — "Drei-Schichten-Modell" → "Schichten-Modell" (0-external ergänzt, Override-Reihenfolge aktualisiert)
- CLAUDE.md — Verzeichnisstruktur: `0-external/`, `external/`, `external-skills.config.yaml` dokumentiert
- CLAUDE.md — Abhängigkeits-Karte + Änderungs-Kategorien um External Skills ergänzt

---

## [0.10.7] — 2026-04-03

### Added

- `snippets/developer/bun-typescript.md` (`1.0.0`) — Imports/Exports, Typisierung, Fehlerbehandlung, Dateistruktur, Async für TypeScript/Bun
- `snippets/developer/pytest-python.md` (`1.0.0`) — Python-Äquivalente
- **`{{DEVELOPER_SNIPPETS_PATH}}`** — neue Variable, zeigt auf Developer-Snippet-Datei

### Changed

- `developer.md` (`1.4.0`) — `DEVELOPER_SNIPPETS_PATH` Read-Instruktion in Sprach-Best-Practices eingebaut
- CLAUDE.md — `DEVELOPER_SNIPPETS_PATH` in Variablen-Tabelle + Snippets-Tabelle + Verzeichnisstruktur
- `agent-meta.config.example.json` — `DEVELOPER_SNIPPETS_PATH` hinzugefügt

---

## [0.10.6] — 2026-04-03

### Added

- **Snippet-System** — sprachspezifische Code-Beispiele ausgelagert in `snippets/<rolle>/`
- `snippets/tester/bun-typescript.md` (`1.0.0`) — TypeScript/Bun Test-Syntax, Naming, Assertions
- `snippets/tester/pytest-python.md` (`1.0.0`) — Python/pytest Äquivalente
- **`{{TESTER_SNIPPETS_PATH}}`** — neue Variable, zeigt auf Snippet-Datei (relativ zu `snippets/`)
- `sync.py` — `sync_snippets()`: kopiert Snippet-Dateien nach `.claude/snippets/` im Zielprojekt (respektiert `--dry-run`, loggt Version)
- CLAUDE.md — neuer Abschnitt "Snippets" mit Konzept, Frontmatter, verfügbaren Snippets, Anleitung

### Changed

- `tester.md` (`1.4.0`) — TypeScript-Codeblöcke durch sprach-agnostisches Pseudocode ersetzt; `{{TESTER_SNIPPETS_PATH}}` Read-Instruktion an 3 Stellen eingebaut
- `orchestrator.md` (`1.4.0`) — `py .agent-meta/scripts/sync.py` → `python .agent-meta/scripts/sync.py` (plattformübergreifend)

---

## [0.10.5] — 2026-04-03

### Added

- **`{{CODE_LANGUAGE}}`** — neue Variable für code-nahe Artefakte: Code-Kommentare, Commit-Messages, Test-Beschreibungen, docker-compose-Kommentare (Default: `Englisch`)
- **`{{INTERNAL_DOCS_LANGUAGE}}`** — neue Variable für interne Doku: CODEBASE_OVERVIEW, ARCHITECTURE, REQUIREMENTS, conclusions (Default: `Deutsch`)

### Changed

- `COMMUNICATION_LANGUAGE` Default-Wert: `Deutsch` → `Englisch`
- `developer.md` (`1.3.0`) — Code-Kommentare + Commit-Messages → `{{CODE_LANGUAGE}}`
- `docker.md` (`1.3.0`) — docker-compose Kommentare → `{{CODE_LANGUAGE}}`
- `documenter.md` (`1.3.0`) — Datei-Tabelle + README-WICHTIG → `{{DOCS_LANGUAGE}}`/`{{INTERNAL_DOCS_LANGUAGE}}`; Sprach-Sektion aufgetrennt
- `meta-feedback.md` (`1.3.0`) — GitHub Issues → `{{DOCS_LANGUAGE}}`
- `tester.md` (`1.3.0`) — Test-Beschreibungen → `{{CODE_LANGUAGE}}`
- `requirements.md` (`1.3.0`) — REQUIREMENTS.md → `{{INTERNAL_DOCS_LANGUAGE}}`
- `validator.md` (`1.3.0`) — Berichte → `{{INTERNAL_DOCS_LANGUAGE}}`
- `sharkord-docker.md` (`1.2.0`) — Kommentare → `{{CODE_LANGUAGE}}`, Kommunikation → `{{COMMUNICATION_LANGUAGE}}`
- `sharkord-release.md` (`1.2.0`) — Release Notes → `{{DOCS_LANGUAGE}}`, Kommunikation → `{{COMMUNICATION_LANGUAGE}}`
- CLAUDE.md — Variablen-Tabelle um `CODE_LANGUAGE` + `INTERNAL_DOCS_LANGUAGE` erweitert

---

## [0.10.4] — 2026-04-03

### Changed

- Alle Agenten — `## Projektspezifische Erweiterung`-Block von 8 auf 1 Zeile komprimiert (kein Inhaltsverlust, ~84 Zeilen gespart)
- `tester.md` (`1.2.0`) — Don'ts-Sektion: Duplikate aus "Qualitätsprinzipien"-Abschnitt entfernt, durch Querverweis ersetzt
- `developer.md` (`1.2.0`) — "Sprach-Best-Practices": erklärender Absatz entfernt, Regel auf eine Zeile
- `orchestrator.md` (`1.3.0`) — Extension-Block komprimiert
- Alle anderen 1-generic Agenten (`1.2.0`) — Extension-Block komprimiert
- 2-platform Agenten (`1.1.0`) — Extension-Block komprimiert

---

## [0.10.3] — 2026-04-03

### Added

- **`{{COMMUNICATION_LANGUAGE}}`** — neue Variable in allen Agenten; steuert Sprache der Nutzer-Kommunikation
- **`{{DOCS_LANGUAGE}}`** — neue Variable in allen Agenten; steuert Sprache von Dokumentationsdateien
- **`{{PROJECT_GOAL}}`** — neue Variable im Projektkontext-Block aller Agenten (primäres Ziel)
- **`{{PROJECT_LANGUAGES}}`** — neue Variable im Projektkontext-Block aller Agenten
- **`{{AGENT_META_REPO}}`** — neue Variable in `meta-feedback.md`; ersetzt hardcodierten `Popoboxxo/agent-meta`
- `config.example.json` — alle neuen Variablen mit Defaults ergänzt

### Changed

- `tester.md` (`1.1.0`) — neuer Abschnitt "Qualitätsprinzipien: Keine Shortcuts": echte Assertions, realitätsnahe Testdaten (keine `"foo"`/`"test"`/`123`-Dummy-Daten), Warnung vor Tests die immer grün sind
- `developer.md` (`1.1.0`) — neuer Unterabschnitt "Sprach-Best-Practices": strikt Best Practices der verwendeten Sprache(n) befolgen
- `meta-feedback.md` (`1.1.0`) — `--repo Popoboxxo/agent-meta` durch `--repo {{AGENT_META_REPO}}` ersetzt
- `orchestrator.md` (`1.2.0`) — Sprachvariablen + Projektkontext erweitert
- Alle anderen 1-generic Agenten (`1.1.0`) — Sprachvariablen + Projektkontext erweitert
- CLAUDE.md — Variablen-Tabelle um neue Variablen ergänzt

---

## [0.10.2] — 2026-04-03

### Fixed

- `orchestrator.md` — version von `1.0.0` auf `1.1.0` hochgezogen (war bei 0.10.1 vergessen worden)

### Changed

- Release-Prozess in CLAUDE.md — Schritt 1 "Agenten-Versionen prüfen" explizit ergänzt; Regel: bei Unsicherheit Nutzer fragen

---

## [0.10.1] — 2026-04-03

### Added

- **Neuer Agent `ideation`** (`1-generic/ideation.md`) — Begleitet die frühe, unscharfe Phase bei neuen Projekten und Features: Ideen erkunden, Fragen stellen, Scope schärfen, externe Impulse geben, strukturierte Übergabe an den Requirements-Agenten
- **Workflow I** im Orchestrator — "Neue Idee / Vision erkunden" mit Ideation → Requirements-Kette
- **Workflow H** in CLAUDE.md — dokumentiert den neuen Ideation-Workflow

### Changed

- `orchestrator.md` — `ideation` in Agenten-Tabelle + Workflow I; bisheriger Workflow I (meta-feedback) → Workflow K
- CLAUDE.md — `ideation` in Agenten-Rollen-Tabellen, Namenstabelle und Abhängigkeits-Karte
- `sync.py` ROLE_MAP — `ideation` ergänzt

---

## [0.10.0] — 2026-04-03

### Added

- **Agent-Versionierung** — Jede Template-Datei trägt jetzt `version:` im Frontmatter
- `based-on:` in 2-platform Agenten — dokumentiert die Generic-Basis mit Version (z.B. `1-generic/docker.md@1.0.0`)
- `generated-from:` — wird von `sync.py` automatisch bei jedem Sync in generierte Agenten geschrieben
- `extract_frontmatter_field()` in `sync.py` — liest beliebige YAML-Felder aus Templates
- [howto/agent-versioning.md](howto/agent-versioning.md) — vollständige Dokumentation des Versioning-Konzepts

### Changed

- `build_frontmatter()` in `sync.py` — schreibt `generated-from:` ins generierte Frontmatter; `version` und `based-on` bleiben unverändert erhalten
- `sync_agents()` in `sync.py` — liest `version` aus Quell-Template und befüllt `generated-from` automatisch
- CLAUDE.md — neuer Abschnitt "Agent-Versionierung", Abhängigkeits-Tabelle um Versionshinweise erweitert
- Alle 1-generic Agenten starten mit `version: "1.0.0"`
- Alle 2-platform Agenten starten mit `version: "1.0.0"` und `based-on:`

### Fixed

- `update_extensions()` in `sync.py` — pre-existierender `updated += 1` Bug (nicht initialisierte Variable) entfernt

---

## [0.9.5] — 2026-04-03

### Breaking Changes

- **Variable renames** in `agent-meta.config.example.json`:
  - `SHARKORD_VERSION` → `PRIMARY_IMAGE_TAG`
  - `SHARKORD_URL` → part of `SYSTEM_URLS` (Markdown-Liste)
  - `SHARKORD_MIN_VERSION`, `SHARKORD_IMAGE` → removed (redundant)
  - `WEB_PORT` → `PRIMARY_PORT`
  - `MEDIASOUP_PORT` → part of `EXTRA_PORTS` (Markdown-Liste)
  - `KEY_DEPENDENCIES`, `TARGET_PLATFORM`, `PLATFORM_LAYER` → removed (redundant)
- **`sharkord-docker.md`** updated to use new variable names

### Added

- `SYSTEM_DEPENDENCIES` — Markdown-Liste aller Kern-Abhängigkeiten mit Versionen
- `SYSTEM_URLS` — Markdown-Liste aller relevanten System-URLs
- `EXTRA_PORTS` — Markdown-Liste weiterer Ports neben `PRIMARY_PORT`
- `config.example.json` in vier klare Sektionen gegliedert:
  - **Generisch** — für jedes Projekt
  - **Infrastruktur** — Docker, Ports, Container
  - **Plattform** — nur bei `platforms: ["sharkord"]`
  - **Projektspezifisch** — individuelle Werte pro Projekt
- `CLAUDE.md` — Variablen-Tabelle nach denselben vier Sektionen strukturiert

### Changed

- `sharkord-docker.md` — Platzhalter-Dokumentation aktualisiert, Port-Vorlage generalisiert

---

## [0.9.4] — 2026-04-03

### Added

- New agent role `meta-feedback` (`agents/1-generic/meta-feedback.md`):
  collects improvement suggestions for the agent-meta framework and creates
  GitHub Issues in the agent-meta repository
- Orchestrator Workflow I: "Feedback an agent-meta geben" — delegates to
  `meta-feedback`; orchestrator actively asks for feedback at session end
- `meta-feedback` added to `ROLE_MAP` in `sync.py`

### Changed

- `CLAUDE.md` — agent roles table and dependency map updated with `meta-feedback`
- `README.md` — agent roles table and supported platforms updated

---

## [0.9.3] — 2026-04-03

### Added

- Release process documented in `CLAUDE.md`: Semantic Versioning rules,
  step-by-step workflow, rule that README must reflect the new version
  before the tag commit

### Changed

- README version badge and Quick Start example now always reflect current
  version before tagging

---

## [0.9.1] — 2026-04-03

### Added

- README with VibeCoding experiment warning, architecture overview, quick start,
  extension system docs, upgrade instructions, and agent role reference

### Changed

- Orchestrator Workflow H2 now documents automatic platform layer selection:
  sync.py reads `"platforms": [...]` from config and picks the correct
  `2-platform/` agent automatically — no manual step required

---

## [0.9.0] — 2026-04-03

### Breaking Changes

- **Generic agent names** — agents in `.claude/agents/` no longer use a project
  prefix. Files are now named `developer.md`, `tester.md` etc. instead of
  `vwf-developer.md`. One project per workspace is the assumed model.
- **`project.prefix` is now used for extensions only**, not for agent filenames.

### Added

**Extension system** (`.claude/3-project/<prefix>-<role>-ext.md`)
- New `--create-ext <role|all>` — creates extension file with managed block +
  empty project section; never overwrites an existing file
- New `--update-ext` — updates the managed block in all existing extension files;
  project section is never touched
- Managed block (`<!-- agent-meta:managed-begin/end -->`) contains auto-generated
  context from config variables — updated on every `--update-ext`
- Meta-repo provides no extension templates — extensions are fully project-owned

**Extension-Hook in all agents**
- Every generated agent (1-generic + 2-platform) reads `.claude/3-project/<prefix>-<role>-ext.md`
  at startup if it exists — additively, without overriding the agent

**`howto/upgrade-guide.md`** — new: full upgrade workflow, `--update-ext` for
extensions, rollback, breaking-change handling, checklist

### Changed

- `config.example.json` — restored `prefix` field, removed `EXTRA_*_KNOWLEDGE`
  variables (replaced by extension system), added all missing variables
- `instantiate-project.md` — rewritten for sync.py workflow (submodule + script)
- `CLAUDE.md` — rewritten with 4 core principles, extension system docs,
  update-behavior table, decision tree

### Removed

- `EXTRA_ORCHESTRATOR/TESTER/DOCUMENTER/REQ_KNOWLEDGE` placeholders from
  1-generic agents (replaced by extension system)
- Copy-once logic for extension files

---

## [0.1.0] — 2026-04-01

Initial release of agent-meta.

### Added

**Three-layer agent architecture**
- `agents/1-generic/` — platform-independent agent roles: orchestrator, developer,
  tester, validator, requirements, documenter, release, docker
- `agents/2-platform/` — Sharkord-specific agents: sharkord-docker, sharkord-release,
  consolidating all knowledge from sharkord-vid-with-friends and sharkord-hero-introducer
- `agents/3-project/` — reserved for project-level overrides (rare)

**CLAUDE.md as single source of truth**
- Project context lives exclusively in the project's `CLAUDE.md`
- Agents read `CLAUDE.md` instead of carrying embedded context blocks
- Override hierarchy: generic ← platform ← project

**sync.py — project integration script**
- Generates `.claude/agents/*.md` from agent-meta sources
- Modes: `--init`, `--only-variables`, `--dry-run`
- Three-layer override logic with multi-platform support
- Auto-sets frontmatter (`name`, `description`) per project
- Writes `sync.log` with full summary and warnings for missing variables

**Supporting files**
- `agent-meta.config.example.json` — config template covering all known variables
- `howto/instantiate-project.md` — step-by-step setup guide
- `howto/CLAUDE.project-template.md` — project CLAUDE.md template
- `howto/sync-concept.md` — full sync concept and architecture decisions
- `howto/template-gap-analysis.md` — gap analysis vs. existing projects

### Supported platforms
- Sharkord Plugin SDK (`sharkord-docker.md`, `sharkord-release.md`)

### Known limitations
- `sync.py` requires Python 3.8+
- No automated tests for the sync script yet
- Project-level overrides (`3-project/`) are reserved but not yet exercised
