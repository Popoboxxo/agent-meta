"""AC-01 harness: render output of every provider-matrix project is byte-identical.

For each provider registered in config/ai-providers.yaml a scratch project
(same single-provider config as tests/test_provider_matrix_sync.py) is synced,
and every generated file is hashed (SHA-256). The result is compared against
the committed manifest ``tests/fixtures/ac01-baseline/hashes.json``, which was
produced on the pre-feature ``main`` state.

Differences are only tolerated for paths matching ``AC01_EXCEPTIONS`` (the
AC-01 exception list (i)-(v) of SPEC-CONTEXT-PROFILES-2026-10-11, kept as data).

Host-local files are not part of the key set at all: ``settings.local.json`` is
written into a gitignored path in every real project and may legitimately embed
absolute host paths -- the machine-specific pytest basetemp in
``permissions.additionalDirectories`` (#1079). Its content is therefore not part
of the shipped render contract; pinning it would bake a username/temp path into
this manifest and drift on every other machine. The exclusion applies on both
sides (rendered key set and manifest), so a future rebaseline cannot re-pin it.

Regenerate the manifest (only for a justified rebaseline; ``--write`` is only
allowed on a clean, unmodified ``main`` state, rebaseline only with a documented
reason, Spec AC-01):
    python tests/test_ac01_render_identity.py --write

Rebaseline log (manifest is plain JSON, so reasons are kept here):
- Task 0e.2 (IC-28, AC-01 exception list ii/iii): new role ``meta-doctor`` (all provider
  artifacts, roster/enum/name_index rows in orchestrator, AGENTS.md, copilot-instructions,
  managed-file lists and generated-file-hashes) plus the ``agent-meta-manager`` 1.24.0
  ``doctor-findings-v1`` consumer section and ``handoff.input_contracts`` row in the
  orchestrator routing data. No other render changes.
- Review of package 0e (fix commit): meta-doctor allowlist reduced to the exact IC-23/AC-88 forms, wording
  without "read-only", manager ``input_contracts`` reduced to ``doctor-findings-v1`` (no ``task-spec-v1``).
  Affects only the meta-doctor artifacts, the orchestrator routing data and managed-file hashes.
- Task 1.35 (Q9, IC-15 Nr. 14): ``template-auditor`` loses its ``routing_patterns`` (name_only role
  without keyword rule). Rebaselined only the per-provider orchestrator artifact (its keyword
  routing data / intent rows) and the matching managed-file hashes; no other artifact changed.
- Task 1.05 (IC-18 no. 18, user decision): meta-doctor (new in 0e, unreleased): the NEXT
  conditional ``ROLE_META_FEEDBACK_ACTIVE`` is true in the default (meta-feedback is in the
  ActiveSet) now that ``active_set_variables`` reaches ``build_variables``. Only the
  meta-doctor artifacts of all providers and the dependent generated-file-hashes change; the
  exception regex now also covers two-suffix names (``meta-doctor.agent.md``).
- Task 1.07 (IC-31 EN/DE twin PR, AC-72 exception): the German "Pflicht-Abschluss-Summary" twin of the
  closing summary in 19 templates is unified on the English ``{{CLOSING_SUMMARY_BLOCK}}`` text (patch
  version bump each; ``agent-meta-mammouth-expert`` 1.2.3 re-pinned to ``mammouth-expert@1.6.2``). Of the
  19 roles only ``mammouth-expert`` is active in the provider matrix, so only its per-provider artifact
  (8 providers + ``.agent`` file) and the matching managed-file hashes (9 x ``generated-file-hashes.json``)
  changed - 18 of 1102 hashes. The other 18 roles (knowledge-*, se-*) are not rendered in the matrix.
- Task 1.10 (IC-18 no. 2, user decision ADR-10/Q18: the pipeline drop applies in the DEFAULT too): in the
  default project the ``validator`` and ``developer_tiers`` gates are off, so ``concept-driven-dev`` and
  ``feature-lifecycle`` (``validator``) and ``refactor`` (``senior-developer``) are no longer rendered. Changed
  only: the per-provider orchestrator artifact (9; match table, section 2a detail blocks, ``routing.pipelines``),
  the 3 ``pipeline-details/*.md`` files plus the ``.agent-meta-managed`` index per provider, and the matching
  ``generated-file-hashes.json`` (27 + 9 + 9 + 9 = 54 of 1102 entries; 1075 remain, 27 files vanished). No other
  hash changed.
- Task 1.13 (IC-18 no. 5, AC-48: the default has ``developer_tiers`` off): orchestrator section 3/4 and the
  task-size table name ``developer`` instead of the junior/senior/principal chain, developer's
  ``RECOMMENDED_TIER`` line and the planner step mapping drop ``senior-developer``; minor version bumps
  (orchestrator 8.5.0, developer 4.8.0, planner 1.6.0). Changed: orchestrator, developer, planner per provider
  and generated-file-hashes (4 x 9 = 36 of 1075 entries).
- Task 1.14 (IC-18 no. 6): ``ANTI_RECURSION_BLOCK`` names only reference roles of
  ``role-defaults.yaml: anti_recursion.reference_roles`` that are in the ActiveSet; the default drops
  ``/validator`` (gate off). Changed: orchestrator, developer per provider and generated-file-hashes
  (3 x 9 = 27 of 1075 entries). No template version bump (template source unchanged).
- Task 1.16 (IC-18 no. 8): orchestrator persona/section 11 follow ``ROLE_META_FEEDBACK_ACTIVE`` and the
  AI review roles, SE-mode prose needs ``SE_ENABLED`` (off in the default), ``se-critic`` and
  ``effort-estimator`` only when active, and the static prose names only rendered pipelines (the default
  drops ``concept-driven-dev``/``feature-lifecycle`` mentions, closing the PR C interim). Changed:
  orchestrator per provider + generated-file-hashes (2 x 9 = 18 of 1075 entries).
- Task 1.19 (IC-18 no. 11 / IC-30 triage, AC-71): dispatch/NEXT lines in worker templates are gated on
  their target role (``ROLE_*_ACTIVE``); patch bumps of the triaged templates. In the default only the
  inactive targets disappear (documenter KE route, bug-feature-analyzer ``se-critic``/``se-interface-mgr``
  rows, concept-reviewer ``se-critic`` and developer ``validator`` arrows); the rest is the version bump.
  Changed: 29 agent artifacts per provider (accessibility-specialist ... test-executor, see CHANGELOG) +
  generated-file-hashes (30 x 9 = 270 of 1075 entries).
- Task 1.21 (IC-15 no. 1, F-05): the shared AGENTS.md block is derived from the ACTIVE sharers only.
  Single-provider projects no longer join the path fields of all six catalog sharers with "bzw."
  (agents dir, pending-tasks file, skills dir) and the header banner no longer names inactive sharers.
  Changed: AGENTS.md of the six AGENTS.md providers (6 of 1075 entries). No other hash changed.
- Task 1.22 (IC-15 no. 2, AC-14 path part): Copilot's ``skills_dir`` moves from the never-read
  ``.github/copilot/skills`` to ``.github/skills``. In the default preset no rule is lazy, so only the
  rendered ``SKILLS_DIR`` path changes: Copilot ``agent-meta-manager``, ``mcp-guardrails``,
  ``use-lazy-rules`` and its ``generated-file-hashes.json`` (4 of 1075 entries).
- Task 1.23 (IC-15 no. 9, AC-19): Codex and Mammouth no longer write their unread rules directories
  (project-root ``rules/``, ``.mammouth/rules/``; rules stay embedded in AGENTS.md); Claude gets
  ``CLAUDE.local.md`` (read by Claude Code) instead of ``CLAUDE.personal.md``. Removed: 2 x 22 rules-dir
  files (19 rules + 3 managed indexes) and ``Claude/CLAUDE.personal.md``; added ``Claude/CLAUDE.local.md``;
  changed: Claude ``.gitignore`` (``CLAUDE.local.md`` entry) and the Codex/Mammouth
  ``generated-file-hashes.json`` (49 entries; 1075 -> 1031). AGENTS.md is unchanged.
- Task 1.33 (IC-15 no. 12, F-16): the AGENTS.md header banner lists the active providers by context file
  (``> **AI ROUTING:** Codex -> AGENTS.md``) instead of the hard-wired ``Opencode->AGENTS.md | Gemini->
  AGENTS.md``; lazy-skill tables list only skills the sync writes for the provider - the default preset has
  none, so ``use-lazy-rules`` is no longer rendered. Changed: 6 x AGENTS.md (banner, embedded table gone),
  removed 4 x ``use-lazy-rules.md`` (Claude, Continue, Gemini, Copilot rules dirs), changed their 4
  ``.agent-meta-managed`` indexes and 4 ``generated-file-hashes.json`` (18 entries; 1031 -> 1027).
- Task 1.25 (IC-15 no. 4, F-04/F-09): Codex gets a ``.codex/config.toml`` with a managed
  ``[agents] max_depth`` table (new artifact) and its ``spawn_agent`` delegation syntax uses the real
  ``agent_type``/``message`` parameters instead of ``agent``/``task`` (config/delegation-syntax.yaml).
  Changed: ``Codex/.codex/config.toml`` (added), ``Codex/.codex/agents/orchestrator.toml``, the 4
  ``Codex/.codex/pipeline-details/*.md`` and ``Codex/.meta-config/generated-file-hashes.json``
  (7 of 1028 entries). No other provider's render changed.
- Task 1.26 (IC-15 no. 5, F-10): the KimiCode ``agent-transform`` maps ``TodoWrite``->``TodoList`` and
  renames ``hint``->``whenToUse`` on every Kimi agent, and the orchestrator gains the Kimi ``subagents:``
  allow-list (``ActiveSet.routable``) plus the ``native_agent_tools`` fan-out tool ``AgentSwarm``.
  Changed: all 62 ``KimiCode/.kimi-code/agents/*.md`` and the KimiCode
  ``.meta-config/generated-file-hashes.json`` (63 of 1028 hashes). No other provider's render changed.
- Task 1.27 (IC-15 no. 6, F-11): the Mammouth ``agent-transform`` switches to ``frontmatter-mechanism:
  opencode-native`` (Mammouth is an OpenCode fork), so every Mammouth agent emits a lowercase
  ``permission`` map (incl. ``task``/``todowrite``) and a set ``mode`` instead of the inert Claude-cased
  ``tools:`` object, plus a ``subagent_depth`` from the ``required_depth`` capability (``inject-subagent-depth``).
  Changed: all 62 ``Mammouth/.mammouth/agents/*.md`` and the Mammouth
  ``.meta-config/generated-file-hashes.json`` (63 of 1028 hashes). No other provider's render changed.
- Task 1.28 (IC-15 Nr. 8, F-08/F-07): Gemini no longer writes its unread ``.gemini/rules`` directory
  (rules stay embedded in AGENTS.md) and ``.gemini/settings.json`` gains ``context.fileName=AGENTS.md``
  so Gemini CLI actually reads the shared core. Removed: the 21 ``Gemini/.gemini/rules`` files
  (18 rules + 3 managed indexes); changed: ``Gemini/.gemini/settings.json`` and the Gemini
  ``.meta-config/generated-file-hashes.json`` (23 of 1028 entries; 1028 -> 1007). AGENTS.md and no
  other provider's render changed.
- Task 1.29 (IC-15 Nr. 3, AC-14 / F-13): Copilot rule files gain the mandatory ``.instructions.md``
  suffix plus ``applyTo``/``description`` frontmatter, and every Copilot agent frontmatter ``name:``
  drops the leaked extension (``orchestrator.agent`` -> ``orchestrator``). Changed/reassigned: 18
  ``Copilot/.github/instructions/*.md`` removed + 18 ``*.instructions.md`` added, all 63
  ``Copilot/.github/agents/*.agent.md`` names, the ``.github/instructions/.agent-meta-managed`` index
  and the Copilot ``.meta-config/generated-file-hashes.json`` (101 of 1007 entries; Copilot-only,
  0 non-Copilot drift; ``meta-doctor.agent.md`` is covered by the existing AC-01 exception). No other
  provider's render changed.
- Task 1.31 (IC-15 Nr. 10, AC-10 / F-14): Continue rule files gain
  ``alwaysApply: false`` + ``description`` frontmatter (driven by the
  ``rules-always-apply`` capability; before, the frontmatter was only emitted
  when the rules-preset opted in, so the default preset shipped 18,591 B of
  rules always active - 28 % of the local template window, study §3.8) and
  ``.continue/rules/project-context.md`` no longer ships unresolved
  ``{{PLATFORM}}``/``{{BUILD_COMMAND}}``/``{{RUNTIME}}``/``{{TEST_COMMAND}}``
  lines. Changed: 19 ``Continue/.continue/rules/*.md`` plus
  ``project-context.md`` and the Continue ``.meta-config/generated-file-hashes.json``
  (20 of 1007 entries; Continue-only, 0 non-Continue drift).
- Task 1.32 (IC-15 Nr. 11, AC-20 / F-15): the Agent Directory / ``AGENT_DELEGATION_TABLE``
  is now one valid Markdown table - the ``agents-table`` partial no longer emits blank
  lines between rows (full mode) and the orchestrator no longer repeats a second header
  above the partial-provided ``| Agent | Core Capabilities |`` header (orchestrator
  8.5.0 -> 8.5.1). Changed: the orchestrator artifact of all 9 providers, the 6
  ``AGENTS.md`` files (Agent Directory rows lose the blank-line separation) and the 9
  ``generated-file-hashes.json`` (24 of 1007 entries). No other artifact changed.
- Task 1.38 (IC-15 Nr. 17, AC-51): the reflection overrides now come from the CONSUMER
  config instead of agent-meta's own tracked ``.meta-config/project.yaml``, so the three
  active ``{{MAX_ITERATIONS}}`` roles (``control-framework-assessor``,
  ``fraud-risk-assessor``, ``risk-based-audit-planner``) render the framework value ``3``
  instead of agent-meta's leaked override ``5``. Changed: those 3 artifacts per provider
  (9 providers) plus the 9 ``generated-file-hashes.json`` (36 of 1007 entries; 0 unrelated drift).
- Task 1.40 (IC-15 Nr. 21, AC-10 / F-32): a provider declaring
  ``read_only_enforcement: sandbox`` (Codex) plus the ``read-only-extra-fields`` override
  map now emits ``sandbox_mode: read-only`` for roles whose template tool list carries
  neither ``Write`` nor ``Edit`` (previously the pauschale ``workspace-write``). Changed: the
  21 read-only ``Codex/.codex/agents/*.toml`` roles plus the Codex
  ``.meta-config/generated-file-hashes.json`` (22 of 1007 entries; Codex-only, 0 non-Codex
  drift; ``meta-doctor.toml`` is covered by the existing AC-01 exception).
- Task 1.42 (IC-15 Nr. 23, AC-73): provider literals are removed from the generic
  templates. ``agent-meta-manager``/``agent-meta-scout``/``prompt-governor`` use the
  ``{{CONTEXT_FILE}}`` placeholder, ``agent-meta-manager``/``release`` wrap their
  provider-specific snippets in ``> **Example (provider-specific):**`` blocks, and
  ``mammouth-expert`` is split into a provider-neutral ``1-generic`` base plus a
  standalone ``2-platform/agent-meta-mammouth-expert.md`` (based on
  ``provider-expert``, both 2.0.0). Changed: 5 agent artifacts per provider (9
  providers = 45), 9 ``generated-file-hashes.json`` and 1
  ``Copilot/.github/copilot-instructions.md`` — 55 of 1007 hashes; 0 added/removed.
  ``knowledge-migrator`` is not rendered in the matrix. No other artifact changed.
- Task 11 (2b.2, IC-05, AC-23): the orchestrator template §2a, §9 and the ``<context>``
  agent table are wrapped in ``{{#if CONTEXT_PROFILE_COMPACT}}…{{else}}…{{/if}}`` (minor
  bump 8.5.1 -> 8.6.0). The ``{{else}}`` branch is the unchanged text, so without the
  ``context-profile`` opt-in every render only differs by the version bump in the
  orchestrator artifact. Changed: the 9 per-provider orchestrator artifacts
  (``orchestrator.md``/``.toml``/``.agent.md``) plus the 9
  ``generated-file-hashes.json`` (18 of 1003 hashes; 0 added/removed). No other
  artifact changed.
- C2/C3/IC-05 roster gating (SPEC-CONTEXT-PROFILES-2026-10-11): the compact agent roster in
  both emitters (orchestrator ``<context>`` names line and the shared-file ``agents-list-compact``)
  is gated on the per-provider ``roster_in_harness`` capability (IC-09). The orchestrator template
  is bumped 8.6.0 -> 8.7.0; the ``{{else}}`` (full) branch is unchanged, so without the
  ``context-profile`` opt-in every render only differs by that version bump. Changed: the 9
  per-provider orchestrator artifacts (``orchestrator.md``/``.toml``/``.agent.md``) plus the 9
  ``generated-file-hashes.json`` (18 hashes; 0 added/removed). No other artifact changed.
- Task 28 (2e.2, IC-28/AC-23/AC-59): new role ``meta-optimizer`` registration: per-provider role
  artifacts, roster/name_index/enum rows in the orchestrator, AGENTS.md/context-file rows,
  managed-file lists and ``generated-file-hashes.json``. The exception regex is extended to
  ``.*/meta-optimizer\\.(md|toml|agent\\.md)$`` so the Copilot two-suffix form
  (``meta-optimizer.agent.md``) is covered. No other render changed.
- Task 29 (2e.3, IC-27/AC-59): ``agent-meta-manager`` gains ``handoff.input_contracts +=
  config-patch-proposal-v1`` -> one additional ``input_contracts`` routing row in the orchestrator
  routing data. Changed: the 9 per-provider orchestrator artifacts plus the 9
  ``generated-file-hashes.json`` (18 of 1012 hashes; 0 added/removed). No other render changed.
- Task 30 (2e.4, IC-27/AC-59/AC-90/AC-91): the ``agent-meta-manager`` template gains the new
  section ``## 10c. Optimizer-Vorschläge anwenden (Advisory Mode)`` (the three steps
  Analyse/Vorschau/Anwendung of IC-27 Rev. 3.1) and a minor version bump ``1.24.1 -> 1.25.0``
  (new optional section, convention: minor). The section is prose plus three bash invocations,
  so it only changes the rendered ``agent-meta-manager`` artifact of each provider and the
  managed-file hash of that file. Changed: the 9 per-provider ``agent-meta-manager`` artifacts
  (``Claude/.claude/agents/agent-meta-manager.md``, ``Codex/.codex/agents/agent-meta-manager.toml``,
  ``Continue/.continue/agents/agent-meta-manager.md``,
  ``Copilot/.github/agents/agent-meta-manager.agent.md``,
  ``Gemini/.gemini/agents/agent-meta-manager.md``,
  ``KimiCode/.kimi-code/agents/agent-meta-manager.md``,
  ``Mammouth/.mammouth/agents/agent-meta-manager.md``,
  ``Opencode/.opencode/agents/agent-meta-manager.md``,
  ``ZCode/.zcode/agents/agent-meta-manager.md``) plus the 9
  ``generated-file-hashes.json`` (18 of 1012 hashes; 0 added/removed). No other render changed;
  ``AC01_EXCEPTIONS`` is NOT extended — the exception list stays limited to the new role
  artifacts ``meta-doctor``/``meta-optimizer`` (Spec AC-01 iv/v).
- Task 30 fix round (2e.4, review findings): three *text* corrections inside the new
  ``## 10c.`` section of the ``agent-meta-manager`` template (the scoped "no manual edit"
  rule, the release/approval wording, the ``preview.json`` payload sentence). The rendered
  section keeps its line count (36 lines) and the template version pin stays ``1.25.0``
  (the section was not yet released), so the *set* of affected paths is unchanged: again
  exactly the 9 per-provider ``agent-meta-manager`` artifacts plus the 9
  ``generated-file-hashes.json`` (18 of 1012 hashes; 0 added/removed).
- Task 30 polish round (2e.4, review findings): one further *text* correction inside the
  same §10c section -- the "no manual edit" rule now names §13 as well
  ("§3/§5/§8" -> "§3/§5/§8/§13 (confirmation, schema check, re-sync, SE cascade)"), because
  §13 (SE cascade) is a documented ``project.yaml`` change path next to §3/§5/§8. The
  rendered section keeps its line count (36 lines) and the template version pin stays
  ``1.25.0`` (the section was not yet released), so the *set* of affected paths is
  unchanged: again exactly the 9 per-provider ``agent-meta-manager`` artifacts plus the 9
  ``generated-file-hashes.json`` (18 of 1012 hashes; 0 added/removed).
- Task 31 (2e.5, IC-27 Rev. 3.1 step 4 / AC-90 / AC-23): the orchestrator template gains the
  common-body section ``## 3a. Optimizer proposals — mandatory preview gate`` (show
  ``preview.json`` to the user via ``main_chat``, obtain the explicit confirmation, only then
  instruct ``agent-meta-manager`` with ``--preview``; verbatim relayed-ID rule; no Bash for
  orchestrator/``meta-optimizer``) and a minor version bump ``8.7.0 -> 8.8.0``. The section
  is outside every ``CONTEXT_PROFILE_COMPACT`` conditional, so both profiles carry it; the
  default (``full``) render therefore differs only by that section plus the version pin.
  Changed: the 9 per-provider orchestrator artifacts (``orchestrator.md``/``.toml``/
  ``.agent.md``) plus the 9 ``generated-file-hashes.json`` (18 of 1012 hashes; 0
  added/removed). No other render changed; ``AC01_EXCEPTIONS`` is NOT extended. Incidental
  rebaseline: ``tests/fixtures/compact-golden/orchestrator.md`` (owner of the compact
  render, unchanged by this task's scope) is updated because the compact golden also
  carries the template version and the common-body section.
- Task 32 (CI fix, AC-49): §3a is wrapped in ``ROLE_AGENT_META_MANAGER_ACTIVE`` +
  ``ROLE_META_OPTIMIZER_ACTIVE`` (template ``8.8.0 -> 8.8.1``). The AC-01 matrix keeps
  every role active, so the section stays and the render differs only by the version pin.
  Changed: the 9 per-provider orchestrator artifacts plus the 9 ``generated-file-hashes.json``
  (18 of 1012 hashes; 0 added/removed). No other render changed; ``AC01_EXCEPTIONS`` is NOT
  extended. The default (repo) render drops the section because the repo whitelist has no
  ``meta-optimizer``; that fixture is the slimming/compact golden, rebaselined with the same
  reason in ``tests/test_template_slimming_equivalence.py``.
- Release 2.0.0-beta.2 (VERSION bump 2.0.0-beta.1 -> 2.0.0-beta.2): only version strings in the
  rendered entry files, agent headers and the dependent sidecars changed (91 of 1012 hashes;
  project.yaml, ``generated-file-hashes.json`` and ``context-hashes.json`` follow the version
  they embed). No substantive render change; ``AC01_EXCEPTIONS`` is NOT extended.
- Release 2.0.0-beta.3 (VERSION bump 2.0.0-beta.2 -> 2.0.0-beta.3): only version strings in the
  rendered entry files, agent headers and the dependent sidecars changed (82 of 1013 hashes;
  0 added/removed; project.yaml, ``generated-file-hashes.json`` and ``context-hashes.json``
  follow the version they embed). No substantive render change; ``AC01_EXCEPTIONS`` is NOT
  extended. The two embedded fixture-tree digests in ``tests/test_opencode_v2_surface.py``
  were re-pinned to the rebaselined trees (``ac01-baseline``, ``compact-golden``);
  ``slimming-golden`` stayed unchanged.
- Release 2.0.0-beta.4 (VERSION bump 2.0.0-beta.3 -> 2.0.0-beta.4): only version strings in the
  rendered entry files, agent headers and the dependent sidecars changed (82 of 1085 hashes;
  0 added/removed; project.yaml, ``generated-file-hashes.json`` and ``context-hashes.json``
  follow the version they embed). No substantive render change; ``AC01_EXCEPTIONS`` is NOT
  extended. The two embedded fixture-tree digests in ``tests/test_opencode_v2_surface.py``
  were re-pinned to the rebaselined trees (``ac01-baseline``, ``compact-golden``);
  ``slimming-golden`` stayed unchanged.
- Release 2.0.0-beta.5 (VERSION bump 2.0.0-beta.4 -> 2.0.0-beta.5): only version strings in the
  rendered entry files, agent headers and the dependent sidecars changed (82 of 1085 hashes;
  0 added/removed; project.yaml, ``generated-file-hashes.json`` and ``context-hashes.json``
  follow the version they embed). No substantive render change; ``AC01_EXCEPTIONS`` is NOT
  extended. The two embedded fixture-tree digests in ``tests/test_opencode_v2_surface.py``
  were re-pinned to the rebaselined trees (``ac01-baseline``, ``compact-golden``);
  ``slimming-golden`` stayed unchanged. `--write` was a version-only no-op apart from those.
- Release 2.0.0-beta.6 (VERSION bump 2.0.0-beta.5 -> 2.0.0-beta.6): only version strings in the
  rendered entry files, agent headers and the dependent sidecars changed (82 of 1085 hashes;
  0 added/removed; the seven role templates that embed ``AGENT_META_VERSION``, the nine copied
  ``project.yaml`` files whose ``agent-meta-version`` the sync rewrites, the entry files and
  ``context-hashes.json``; ``generated-file-hashes.json`` follows the version it embeds).
  No substantive render change; ``AC01_EXCEPTIONS`` is NOT extended. The manifest was patched
  **per entry** (82 single-line replacements, 1003 lines untouched) — not via ``--write`` —
  after recomputing every digest with the harness's own ``_hash_file``. The two embedded
  fixture-tree digests in ``tests/test_opencode_v2_surface.py`` were re-pinned to the
  rebaselined trees (``ac01-baseline``, ``compact-golden``); ``slimming-golden`` stayed
  unchanged.
- Release 2.0.0-beta.7 (VERSION bump 2.0.0-beta.6 -> 2.0.0-beta.7): only version strings in the
  rendered entry files, agent headers and the dependent sidecars changed (82 of 1099 hashes;
  0 added/removed; the seven role templates that embed ``AGENT_META_VERSION``, the nine copied
  ``project.yaml`` files whose ``agent-meta-version`` the sync rewrites, the entry files and
  ``context-hashes.json``; ``generated-file-hashes.json`` follows the version it embeds).
  No substantive render change; ``AC01_EXCEPTIONS`` is NOT extended. The manifest was patched
  **per entry** (82 single-line replacements, 1019 lines untouched) — not via ``--write`` —
  after recomputing every digest with the harness's own ``_hash_file``. The two embedded
  fixture-tree digests in ``tests/test_opencode_v2_surface.py`` were re-pinned to the
  rebaselined trees (``ac01-baseline``, ``compact-golden``); ``slimming-golden`` stayed
  unchanged.
- Release 2.0.0-beta.8 (VERSION bump 2.0.0-beta.7 -> 2.0.0-beta.8): only version strings in the
  rendered entry files, agent headers and the dependent sidecars changed (82 of 1096 hashes;
  0 added/removed; same key classes as beta.7). No substantive render change;
  ``AC01_EXCEPTIONS`` is NOT extended. Manifest regenerated with ``--write`` on the release
  branch (diff verified: identical key set, exactly the 82 version-bearing entries changed).
  The two embedded fixture-tree digests in ``tests/test_opencode_v2_surface.py`` were re-pinned
  (``ac01-baseline``, ``compact-golden``); ``slimming-golden`` unchanged.
- PR #1003 (user decision: model data never flows into AC-01): the hash is now model
  independent. ``_hash_file`` replaces every column-0 ``model:``/``model =`` frontmatter
  line with ``model: <MODEL>`` and reduces ``generated-file-hashes.json`` to its managed-path
  set (its values only hash files compared on their own). Pure ``model-tiers``/
  ``tier-presets`` changes therefore no longer need a rebaseline
  (``test_ac01_hash_ignores_model_id`` pins this). Same fix round: the reproducible
  ``AGENT_META_DATE`` (CHANGELOG release date, #752) is normalized to ``<DATE>`` as well; the
  previous manifest was written on release day, where it matched ``date.today()`` by chance,
  so the harness drifted on every later day. One-time rebaseline: the agent artifacts of the
  8 providers that emit a ``model`` line (Copilot emits none; only its ``prompt-governor``
  changed, whose body has a static ``model: <model ID if declared>`` example line) plus every
  ``generated-file-hashes.json`` (522 of 1012 hashes; 0 added/removed); no other hash changed.
- Task 11 (#1006, OQ-8 amendment A2): Opencode entry point on v1 — orchestrator ``mode: primary``,
  ``default_agent`` written by the managed merge, new ``agent-meta-state.json`` (``default-agent``
  namespace). Changed: ``Opencode/.opencode/agents/orchestrator.md``, ``Opencode/opencode.json``;
  added: ``Opencode/.opencode/agent-meta-state.json`` (2 changed, 1 added). ``AC01_EXCEPTIONS`` is
  NOT extended; Mammouth and all other providers unchanged.
- Task 16 (SPEC-tmp-sink-injection, AC-19): rebaseline after the tmp-sink injection. The rendered
  agent text of 11 roles changed: ``ai-security-guardian``, ``app-lifecycle-governor``,
  ``code-reviewer``, ``developer``, ``devops-engineer``, ``docker``, ``e2e-tester``,
  ``prompt-governor``, ``security-auditor``, ``test-executor`` and ``tester`` (all 9 providers,
  99 artifacts = 11 x 9) — every diff is one of: the auditor report path / log destination moving
  from a system-temp literal to ``.tmp`` (``{{TMP_SINK_PATH}}``), the ``--basetemp="…"`` shape of
  ``TEST_COMMANDS`` replacing ``--basetemp=/tmp/$USER/...``, the ``.tmp/runs/`` scratch prose, or
  the template version pin that Task 4/6 bumped. ``validator`` is gated off in the matrix config,
  so its template change produces no matrix artifact. Plus the three hook scripts whose runtime
  changed with the sink (``Claude/.claude/hooks/repo-containment-impl.sh`` and the two Gemini
  ``.agents/hooks/*.sh``). 102 of 1013 hashes; 0 added/removed; ``generated-file-hashes.json`` is
  unchanged because no managed path appeared or vanished. ``AC01_EXCEPTIONS`` is NOT extended.

- Literature round 2, eight new review roles (PR #1015, IC-28): `memory-architect`, `context-engineer`,
  `red-team-agent`, `secrets-manager`, `chaos-engineer`, `reproducible-builds-engineer`,
  `ux-researcher`, `privacy-compliance-officer` add eight agent artifacts per provider, eight roster
  rows, eight agent-table rows in the entry files (+864 B, Copilot +1,430 B) and eight orchestrator/
  name-index rows, plus the managed-file lists and `generated-file-hashes.json`. The manifest grows
  1012 -> 1085 hashes (the new per-provider agent artifacts and managed-file lists); 106 existing hashes
  changed. No existing role body changed.

- Literature round 2 follow-up (AC-23 / AC-49): `chaos-engineer`, `reproducible-builds-engineer` and
  `ux-researcher` lose bare role arrows (prose handoffs instead; patch bumps `1.0.0 -> 1.0.1`). Rebaseline
  also absorbs the post-merge tmp-sink drift (`f9e3f3e5`) that the branch merge left unrebaselined: the hook
  script, `context-hashes.json`, `project.yaml` and the entry/agent artifacts of every provider. 220 of 1085
  hashes changed; 0 added/removed. No role artifacts were added or removed.
- Literature round 2 follow-up, dangling dispatch: the `se-test-engineer` row in `chaos-engineer` and the
  `se-validator` row in `reproducible-builds-engineer` are gated on their target role (`1.0.1 -> 1.0.2`).
  The AC-01 matrix has every role active, so only those two artifacts per provider change (2 x 9 = 18 of
  1085 hashes; 0 added/removed).
- Rebaseline verification after the literature-round-2 fix series A-F (2026-10-26): a full re-render of the
  provider matrix measured **0 of 1085 hashes changed**; `--write` was a byte-identical no-op. The fixes were
  already covered by the two rebaselines above - D absorbed A's rendered-table change (name-only rows leave
  the entry-file/orchestrator tables) together with the post-merge tmp-sink drift, E rebaselined its own gated
  dispatch rows; C/D were part of D's rebaseline; B (routing eval catalog) and F (standalone README export)
  are not part of the matrix render. No hash was absorbed silently and no exception was added.

- Literature round 2, evidence gates (PR #1013): eight role templates (`git`, `security-auditor`,
  `database-reviewer`, `tester`, `accessibility-specialist`, `se-senior-developer`,
  `performance-optimizer`, `incident-responder`) each gained one literature-anchored rule. Rebaselined:
  the agent artifact of those roles across all providers plus the affected
  `.meta-config/generated-file-hashes.json` (roster/always-loaded +7,228 B, orchestrator +1,258 B).
  No routing, enum or name-index change — the roles were already registered.

- Merge of main (bb92039f, #1013 evidence gates) into the literature-round-2 branch (PR #1015 +
  follow-up series A-F; 2026-10-26): the two independently rebaselined baselines were combined by
  re-rendering the merged tree. Drift before `--write` was exactly the 63 per-provider hashes of the
  seven matrix-active #1013 roles (`git`, `security-auditor`, `database-reviewer`, `tester`,
  `accessibility-specialist`, `performance-optimizer`, `incident-responder`; `se-senior-developer` is
  gated off in the matrix), i.e. 7 x 9 = 63 of 1085 hashes; 0 added/removed. #1015's eight new roles
  and the A-F follow-ups were already in the branch baseline, so the merged manifest is the union of
  both sources with no silently absorbed hash and no exception added. The fixture-tree digests in
  `tests/test_opencode_v2_surface.py` were re-verified against the regenerated `ac01-baseline` and
  `slimming-golden` trees; `compact-golden` is unchanged.

- Issue #1027 (AGENTS.md footer notes, 2026-10-26): the fix preserves ``## Eigene Notizen`` in the
  AGENTS.md footer and removes it from the static drift signature, so the
  ``context-hashes.json`` values of the six AGENTS.md providers (Codex, Gemini, KimiCode,
  Mammouth, Opencode, ZCode) move; in addition the extended ``update-meta`` recovery
  documentation changes the 7 provider-specific command renders (Claude ``.claude/commands``,
  Continue ``.continue/prompts``, Copilot ``.github/prompts``, Gemini ``.gemini/commands``,
  Mammouth ``.mammouth/commands``, Opencode ``.opencode/commands``, ZCode ``.zcode/commands``).
  Changed: 13 of 1085 hashes (7 command artifacts + 6 ``context-hashes.json``); 0 added/removed
  paths. No agent or rule template touched and no golden (``slimming-golden``/``compact-golden``)
  touched; ``AC01_EXCEPTIONS`` is NOT extended (no blanket pattern, no widened regex).

- Issue #1033 (``dod-push-check`` 2.1.6 de-duplicated branch list, 2026-10-27): the hook template edit
  changes the rendered hook, so exactly one hash moved and was rebaselined:
  ``Claude/.claude/hooks/dod-push-check.sh`` (``3f53fa17…`` -> ``f9823b65…``, 1 of 1085 hashes).
  Only Claude renders the hook - no other provider artifact, ``AGENTS.md`` or ``context-hashes.json``
  changed, and no golden (``slimming-golden``/``compact-golden``) was touched.
  ``AC01_EXCEPTIONS`` is NOT extended.

- Welle 2 (#949/#951/#953/#954; ``dod-push-check`` 2.1.7, ``hook_common.sh`` 1.1.0, 2026-10-27): the
  hardened git-push flag/short-cluster walk and the shared protected-branch helper change two rendered
  hook files. Affected: ``Claude/.claude/hooks/dod-push-check.sh`` (2.1.6 -> 2.1.7),
  ``Claude/.claude/hooks/lib/hook_common.sh`` and ``Gemini/.agents/hooks/lib/hook_common.sh`` (-> 1.1.0).
  Pending sync, hashes land with the sync run. Only Claude renders ``dod-push-check`` and only
  Claude/Gemini render the hook lib - no other provider artifact, ``AGENTS.md`` or
  ``context-hashes.json`` changes, and no golden (``slimming-golden``/``compact-golden``) is touched.
  ``AC01_EXCEPTIONS`` is NOT extended.

- Hook hardening rebaseline after the sync write run (2026-10-28, ``fix/bug-session-2026-10-27``):
  completes the "Welle 2" entry above and absorbs the remaining hook edits of the series
  (``hook_common.sh`` 1.2.0, ``orchestrator-guard-impl.sh`` 1.8.0, ``repo-containment-impl.sh``
  1.3.0, ``repo-containment.sh`` 1.1.0, ``antigravity-json-adapter.sh`` comment). A full re-render
  of the provider matrix measured **10 of 1085 hashes changed; 0 added/removed**: the 5 Claude
  hook renders (``dod-push-check.sh``, ``lib/hook_common.sh``, ``orchestrator-guard-impl.sh``,
  ``repo-containment-impl.sh``, ``repo-containment.sh``) and the 5 Gemini ``.agents/hooks``
  counterparts (``antigravity-json-adapter.sh``, ``lib/hook_common.sh``, ``orchestrator-guard-impl.sh``,
  ``repo-containment-impl.sh``, ``repo-containment.sh``). Only Claude renders ``dod-push-check`` and
  only Gemini renders ``antigravity-json-adapter``, hence 5+5 rather than 6+6. No agent/rule artifact,
  ``AGENTS.md``, ``context-hashes.json`` or golden (``slimming-golden``/``compact-golden``) changed.
  The manifest was patched **per entry** (10 single-line replacements, 1077 lines untouched) — not
  via ``--write`` — and every new digest was independently recomputed from the rendered file bytes
  before being written. The repo's own ``.meta-config/generated-file-hashes.json`` was refreshed by
  the sync's post-write capture stage (same 10 entries); it was verified against the on-disk deployed
  files (375/375 entries consistent, 0 stale). ``AC01_EXCEPTIONS`` is NOT extended.

- Issue #1037 (``AGENT_META_REPO`` builder derivation, 2026-10-28, ``fix/bug-session-2026-10-27``):
  ``build_variables()`` now derives the upstream ``owner/repo`` slug when a project has no explicit
  ``variables.AGENT_META_REPO`` entry (source: the embedded ``.gitmodules`` URL, else the agent-meta
  checkout's own git remote) instead of shipping a literal ``{{AGENT_META_REPO}}``. The matrix
  fixture therefore pins ``AGENT_META_REPO: example/agent-meta``: an unpinned value would be derived
  from the *cloning* remote and make this baseline fork-dependent (the derivation itself is covered
  end-to-end by scenario ``87-project-description``). A full re-render measured **36 of 1085 hashes
  changed; 0 added/removed** — the 9 copied ``.meta-config/project.yaml`` fixtures (new pinned line)
  plus exactly ``agent-meta-scout``/``documenter``/``meta-feedback`` × 9 providers. No rule artifact,
  ``AGENTS.md``, ``context-hashes.json`` or golden (``slimming-golden``/``compact-golden``) changed.
  The manifest was patched **per entry** (36 single-line replacements, everything else untouched) and
  re-verified against the rendered bytes; ``AC01_EXCEPTIONS`` is NOT extended.

- Issues #983/#1037 (placeholder fallbacks, ``project.description``, escaped reference examples,
  2026-10-28, ``fix/bug-session-2026-10-27``): the 36 verified single-entry changes above move the
  ``ac01-baseline`` fixture tree, so its AC-T4 digest in ``tests/test_opencode_v2_surface.py`` follows
  the rebaselined tree. The digest was recomputed from the fixture bytes
  (``9ead7c80…``) before re-pinning; ``slimming-golden`` and ``compact-golden`` are unchanged.

- Welle 6 (#943/#944; ``hook_common.sh`` 1.2.0 -> 1.3.0, ``orchestrator-guard-impl.sh`` 1.8.0 ->
  1.9.0, ``repo-containment-impl.sh`` 1.3.0 -> 1.4.0, 2026-10-29, ``fix/bug-session-2026-10-27``):
  three hook templates changed, so **6 of 1085 hashes moved; 0 added/removed** — both Claude and
  Gemini render all three hooks, hence 3+3 rather than 5+5 as in the wave-2 entry above.
  ``Claude/.claude/hooks/lib/hook_common.sh`` (``64232380…`` -> ``9c9f93de…``),
  ``Claude/.claude/hooks/orchestrator-guard-impl.sh`` (``1decf629…`` -> ``dd180856…``),
  ``Claude/.claude/hooks/repo-containment-impl.sh`` (``27931566…`` -> ``a19a9341…``) and the
  ``Gemini/.agents/hooks`` counterparts (``lib/hook_common.sh`` ``64232380…`` -> ``9c9f93de…``,
  ``orchestrator-guard-impl.sh`` ``500d68af…`` -> ``38ef9f41…``, ``repo-containment-impl.sh``
  ``973eb45c…`` -> ``b9168700…``). No agent/rule artifact, ``AGENTS.md``, ``context-hashes.json``
  or golden content changed; ``compact-golden`` and ``slimming-golden`` digests were re-verified as
  unchanged. The manifest was patched **per entry** (6 single-line replacements, 1079 lines
  untouched) — not via ``--write`` — after independently recomputing each digest from the rendered
  file bytes; the repo's own ``.meta-config/generated-file-hashes.json`` was refreshed by the sync's
  post-write capture stage (same 6 entries). Because ``hashes.json`` is the only ``ac01-baseline``
  file, its AC-T4 digest in ``tests/test_opencode_v2_surface.py`` follows the rebaselined tree
  (recomputed from the fixture bytes: ``9ead7c80…`` -> ``b644e7cc…``). ``AC01_EXCEPTIONS`` is NOT
  extended.

- Review findings F1-F5 (wave-6 hook fixes; ``hook_common.sh`` 1.3.0 -> 1.3.1,
  ``orchestrator-guard-impl.sh`` 1.9.0 -> 1.9.1, ``repo-containment-impl.sh``
  1.4.0 -> 1.4.1, 2026-10-29, ``fix/bug-session-2026-10-27``): the ANSI-C /
  dynamic-heredoc / comment splitter fixes, the command-wrapper + ``case`` +
  function-body classification and the fail-closed fixed jail root change the
  same three hook templates, so **6 of 1085 hashes moved; 0 added/removed** --
  ``Claude/.claude/hooks`` and ``Gemini/.agents/hooks`` for ``lib/hook_common.sh``
  (``9c9f93de…`` -> ``40b5cbf6…``), ``orchestrator-guard-impl.sh`` (Claude
  ``dd180856…`` -> ``6b5db2c3…``, Gemini ``38ef9f41…`` -> ``e58cac4e…``) and
  ``repo-containment-impl.sh`` (Claude ``a19a9341…`` -> ``559a4fa1…``, Gemini
  ``b9168700…`` -> ``0ea36712…``). No agent/rule artifact, ``AGENTS.md``,
  ``context-hashes.json`` or golden content changed. The manifest was patched
  **per entry** (6 single-line replacements, 1079 lines untouched) after
  independently recomputing each digest from the rendered file bytes; the
  ``ac01-baseline`` AC-T4 digest in ``tests/test_opencode_v2_surface.py`` follows
  the rebaselined tree (``b644e7cc…`` -> ``5da1fbad…``). ``AC01_EXCEPTIONS`` is
  NOT extended.

- Final state of the wave-6 series (#943/#944; ``hook_common.sh`` 1.3.1 -> 1.4.0,
  ``orchestrator-guard-impl.sh`` 1.9.1 -> 1.9.2, ``repo-containment-impl.sh``
  1.4.1 -> 1.5.0, 2026-10-29, ``fix/bug-session-2026-10-27``): the deployed
  ``.claude/hooks``/``.agents/hooks`` copies still carried the F1-F5 revisions, so
  the sync run that brings them to the final revisions moves **6 of 1085 hashes;
  0 added/removed** -- ``Claude/.claude/hooks`` and ``Gemini/.agents/hooks`` for
  ``lib/hook_common.sh`` (``40b5cbf6…`` -> ``2433634e…``, one identical render for
  both providers: the lib carries no ``{{AGENT_META_PROVIDER}}``),
  ``orchestrator-guard-impl.sh`` (Claude ``6b5db2c3…`` -> ``9bf5e0e2…``, Gemini
  ``e58cac4e…`` -> ``9143c0d3…``) and ``repo-containment-impl.sh`` (Claude
  ``559a4fa1…`` -> ``04006165…``, Gemini ``0ea36712…`` -> ``fd02819b…``). Only
  these three hooks are rendered by both providers, hence 3+3 and not the 5+5 of
  the wave-2 entry. No agent/rule artifact, ``AGENTS.md``, ``context-hashes.json``
  or golden content changed. The manifest was patched **per entry** (6 single-line
  replacements, 1081 of the 1087 lines untouched) -- not via ``--write`` -- after independently
  recomputing each digest from the rendered file bytes with the harness's own
  ``_hash_file``. The repo's own ``.meta-config/generated-file-hashes.json`` was
  refreshed by the sync's post-write capture stage (same 6 entries). Because
  ``hashes.json`` is the only ``ac01-baseline`` file, its AC-T4 digest in
  ``tests/test_opencode_v2_surface.py`` follows the rebaselined tree
  (recomputed from the fixture bytes: ``5da1fbad…`` -> ``6bb30524…``);
  ``slimming-golden`` and ``compact-golden`` were re-verified as unchanged
  (``5642151d…``/``9d854180…``). ``AC01_EXCEPTIONS`` is NOT extended.

- Wave 3 rest (PR A, #943 follow-up; ``hook_common.sh`` 1.4.0 -> 1.5.0,
  ``orchestrator-guard-impl.sh`` 1.9.2 -> 1.9.3, branch-guard rule known-gap entry,
  2026-10-29, ``fix/fork-bomb-window-gap``): the fork-bomb scan limit fixes and the new
  »Bekannte Lücken« item change two hook templates and one rule, so **13 of 1085 hashes
  moved; 0 added/removed** (measured ``k = 0``: no ``context-hashes.json`` drifted) --
  4 hook renders (``Claude/.claude/hooks/lib/hook_common.sh`` ``2433634e…`` -> ``979780e4…``,
  ``Claude/.claude/hooks/orchestrator-guard-impl.sh`` ``9bf5e0e2…`` -> ``07202f29…`` and the
  ``Gemini/.agents/hooks`` counterparts ``2433634e…`` -> ``979780e4…`` and
  ``9143c0d3…`` -> ``036345e8…``; the lib render is identical for both providers) and
  9 branch-guard rule renders (``Claude/.claude/rules/branch-guard.md`` ``97f6467d…`` ->
  ``ec2e891a…``, ``Continue/.continue/rules/branch-guard.md`` ``2a3816a8…`` -> ``2fe5c3d9…``,
  ``Copilot/.github/instructions/branch-guard.instructions.md`` ``7a3aaa71…`` -> ``b72f7c89…``,
  ``Codex/AGENTS.md`` ``08826d6a…`` -> ``8294cd61…``, ``Gemini/AGENTS.md`` ``4a63dba0…`` ->
  ``a07ce5b7…``, ``KimiCode/AGENTS.md`` ``28653e6a…`` -> ``d977795d…``,
  ``Mammouth/AGENTS.md`` ``33db8d26…`` -> ``96d09d71…``, ``Opencode/AGENTS.md``
  ``4eca7678…`` -> ``32b006aa…``, ``ZCode/AGENTS.md`` ``57f0b16b…`` -> ``419ad217…``). No
  agent artifact, ``context-hashes.json`` or golden content changed. The manifest was patched
  **per entry** (13 single-line replacements, 1074 of the 1087 lines untouched) -- not via
  ``--write`` -- after independently recomputing each digest from the rendered file bytes with
  the harness's own ``_hash_file``. Because ``hashes.json`` is the only ``ac01-baseline`` file,
  its AC-T4 digest in ``tests/test_opencode_v2_surface.py`` follows the rebaselined tree
  (recomputed from the fixture bytes: ``6bb30524…`` -> ``9b3b0789…``); ``slimming-golden`` and
  ``compact-golden`` were re-verified as unchanged (``5642151d…``/``9d854180…``).
  ``AC01_EXCEPTIONS`` is NOT extended.

- Issue #1055 (hook tool allow-list; ``hook_common.sh`` 1.5.0 -> 1.6.0, 2026-10-30,
  ``fix/hook-known-tool-name``): the ``hook_known_tool_name`` case list in the shared hook lib
  gains the current built-ins (``Agent``, ``SendMessage`` and peers), and exactly the two renders
  of that lib move - ``Claude/.claude/hooks/lib/hook_common.sh`` (``979780e4…`` -> ``d9331ffe…``)
  and ``Gemini/.agents/hooks/lib/hook_common.sh`` (``979780e4…`` -> ``d9331ffe…``; one identical
  render for both providers, the lib carries no ``{{AGENT_META_PROVIDER}}``). **2 of 1085 hashes
  moved; 0 added/removed.** No rule file changed, so no rule render drifted, and no agent artifact,
  ``AGENTS.md``, ``context-hashes.json`` or golden content changed. The manifest was patched
  **per entry** (2 single-line replacements, 1085 of the 1087 lines untouched) - not via
  ``--write`` - after independently recomputing each digest from the rendered file bytes with the
  harness's own ``_hash_file``. Because ``hashes.json`` is the only ``ac01-baseline`` file, its
  AC-T4 digest in ``tests/test_opencode_v2_surface.py`` follows the rebaselined tree (recomputed
  from the fixture bytes: ``9b3b0789…`` -> ``2557a205…``); ``slimming-golden`` and
  ``compact-golden`` were re-verified as unchanged (``5642151d…``/``9d854180…``).
  ``AC01_EXCEPTIONS`` is NOT extended.

- Issue #1050 (fork-bomb brace nesting, 2026-10-31, ``fix/fork-bomb-brace-nesting``):
  ``hook_common.sh`` 1.6.0 -> 1.7.0 ends the bomb body at the depth-matching ``}``
  instead of the first one, and ``rules/1-generic/branch-guard.md`` drops its
  »Bekannte Lücken« item 5 (the ``}``-gap entry the fix closes). Exactly
  **11 of 1085 hashes moved; 0 added/removed**: the two ``hook_common.sh``
  renders (``Claude/.claude/hooks/lib/hook_common.sh`` ``d9331ffe…`` ->
  ``bcdf8b16…``, ``Gemini/.agents/hooks/lib/hook_common.sh`` ``d9331ffe…`` ->
  ``bcdf8b16…``; one identical render for both providers, the lib carries no
  ``{{AGENT_META_PROVIDER}}``), the three branch-guard rule renders
  (``Claude/.claude/rules/branch-guard.md`` ``ec2e891a…`` -> ``97f6467d…``,
  ``Continue/.continue/rules/branch-guard.md`` ``2fe5c3d9…`` -> ``2a3816a8…``,
  ``Copilot/.github/instructions/branch-guard.instructions.md`` ``b72f7c89…`` ->
  ``7a3aaa71…``; the removed gap entry restores the pre-gap rule text) and the
  six ``AGENTS.md`` files that embed the rule (``Codex/AGENTS.md`` ``65bcde7a…``
  -> ``f12c1325…``, ``Gemini/AGENTS.md`` ``77ce5928…`` -> ``8e646aa8…``,
  ``KimiCode/AGENTS.md`` ``23d2fce9…`` -> ``cf8d7493…``, ``Mammouth/AGENTS.md``
  ``19b910c6…`` -> ``ac1d8c70…``, ``Opencode/AGENTS.md`` ``d661b343…`` ->
  ``2dba68d2…``, ``ZCode/AGENTS.md`` ``1f473667…`` -> ``ce271150…``). No agent
  artifact, command render, ``context-hashes.json`` or golden
  (``slimming-golden``/``compact-golden``) content changed. The manifest was
  patched **per entry** (11 single-line replacements, 1076 of the 1087 lines
  untouched) -- not via ``--write`` -- after independently recomputing each
  digest from the rendered file bytes with the harness's own ``_hash_file``.
  Because ``hashes.json`` is the only ``ac01-baseline`` file, its AC-T4 digest
  in ``tests/test_opencode_v2_surface.py`` follows the rebaselined tree
  (recomputed from the fixture bytes: ``6a063942…`` -> ``e3c25b31…``);
  ``slimming-golden`` and ``compact-golden`` were re-verified as unchanged
  (``6b0c5724…``/``44148ea7…``). ``AC01_EXCEPTIONS`` is NOT extended.

- Issue #1051 (submodule push destinations, ``dod-push-check.sh`` 2.1.7 -> 2.2.0,
  2026-10-31, ``feat/submodule-push-targets``): the hook no longer blocks every
  repository that declares submodules just because ``--recurse-submodules`` is passed;
  it resolves each submodule's own push destination (``remote.<name>.push``, then
  ``push.default``/``branch.<n>.merge``, mirroring git's recursive push which forwards
  only the remote name) and still fails closed on a protected or undeterminable
  destination — the blanket ``--recurse-submodules`` block from #953 is replaced.
  ``rules/1-generic/branch-guard.md`` gains the matching section »Submodule-Pushes
  (--recurse-submodules=on-demand|only)«. Exactly **10 of 1085 hashes moved; 0
  added/removed**: the only ``dod-push-check.sh`` render
  (``Claude/.claude/hooks/dod-push-check.sh`` ``5c0cf724…`` -> ``e7458463…``), the
  three branch-guard rule renders (``Claude/.claude/rules/branch-guard.md``
  ``97f6467d…`` -> ``c42b4025…``, ``Continue/.continue/rules/branch-guard.md``
  ``2a3816a8…`` -> ``7d6e9e10…``, ``Copilot/.github/instructions/branch-guard.instructions.md``
  ``7a3aaa71…`` -> ``2f62fe16…``) and the six ``AGENTS.md`` files that embed the rule
  (``Codex/AGENTS.md`` ``f12c1325…`` -> ``2c0836ce…``, ``Gemini/AGENTS.md``
  ``8e646aa8…`` -> ``4b3c4701…``, ``KimiCode/AGENTS.md`` ``cf8d7493…`` -> ``85ca568a…``,
  ``Mammouth/AGENTS.md`` ``ac1d8c70…`` -> ``93561dfb…``, ``Opencode/AGENTS.md``
  ``2dba68d2…`` -> ``a8aff59f…``, ``ZCode/AGENTS.md`` ``ce271150…`` -> ``9f3b48ae…``).
  No agent artifact, command render, ``context-hashes.json`` or golden
  (``slimming-golden``/``compact-golden``) content changed. The manifest was
  patched **per entry** (10 single-line replacements, 1077 of the 1087 lines
  untouched) -- not via ``--write`` -- after independently recomputing each
  digest from the rendered file bytes with the harness's own ``_hash_file``.
  Because ``hashes.json`` is the only ``ac01-baseline`` file, its AC-T4 digest
  in ``tests/test_opencode_v2_surface.py`` follows the rebaselined tree
  (recomputed from the fixture bytes: ``e3c25b31…`` -> ``f366a90a…``);
  ``slimming-golden`` and ``compact-golden`` were re-verified as unchanged
  (``6b0c5724…``/``44148ea7…``). ``AC01_EXCEPTIONS`` is NOT extended.

- AC-07 fix on the same branch (2026-10-31, ``feat/submodule-push-targets``):
  the #1051 section »Submodule-Pushes« overflowed all 12 AC-07 context ceilings
  (e.g. ``Claude/rules`` 18,463 B vs. 18,003 B), so it was compressed from
  1,195 B to 383 B. The ceilings were **not** touched. This rebaseline
  **supersedes** the one in ``a7eb545d``: the rule text changed again, so the
  same 9 renders move a second time — **9 of 1085 hashes moved; 0 added/removed**
  — the three branch-guard rule renders (``Claude/.claude/rules/branch-guard.md``
  ``c42b4025…`` -> ``504c5ceb…``, ``Continue/.continue/rules/branch-guard.md``
  ``7d6e9e10…`` -> ``ba868b11…``, ``Copilot/.github/instructions/branch-guard.instructions.md``
  ``2f62fe16…`` -> ``f533e9cb…``) and the six ``AGENTS.md`` files that embed the rule
  (``Codex/AGENTS.md`` ``2c0836ce…`` -> ``3a7de4f2…``, ``Gemini/AGENTS.md``
  ``4b3c4701…`` -> ``8e87388a…``, ``KimiCode/AGENTS.md`` ``85ca568a…`` -> ``20bd56f8…``,
  ``Mammouth/AGENTS.md`` ``93561dfb…`` -> ``f0e74eed…``, ``Opencode/AGENTS.md``
  ``a8aff59f…`` -> ``add79f31…``, ``ZCode/AGENTS.md`` ``9f3b48ae…`` -> ``cbcc4578…``).
  No agent artifact, command render, ``context-hashes.json`` or golden
  (``slimming-golden``/``compact-golden``) content changed. The manifest was
  patched **per entry** (9 single-line replacements, 1078 of the 1087 lines
  untouched) -- not via ``--write`` -- after independently recomputing each
  digest from the rendered file bytes with the harness's own ``_hash_file``.
  Because ``hashes.json`` is the only ``ac01-baseline`` file, its AC-T4 digest
  in ``tests/test_opencode_v2_surface.py`` follows the rebaselined tree
  (recomputed from the fixture bytes: ``f366a90a…`` -> ``d4771400…``);
  ``slimming-golden`` and ``compact-golden`` were re-verified as unchanged
  (``6b0c5724…``/``44148ea7…``). ``AC01_EXCEPTIONS`` is NOT extended.

- Structured release checklist (issue #1089, ``feat/release-checklist``, 2026-11-01):
  the feature adds the provider command renders ``release-check`` and
  ``set-release-checklist`` (two new commands × the seven command-writing
  providers = 14 new files), bumps the release templates
  (``release.md`` 1.13.0, ``hacs-release.md`` 1.1.1, ``sharkord-release.md``
  1.3.3; the checklist block itself is inert in the default matrix config) and
  ``agent-meta-manager`` to 1.26.0 (recipe 14d plus the §3 row). **31 of 1085
  hashes moved; 14 added (1085 -> 1099 render entries)**: 9 release agent
  renders, 9 manager renders, the 7 command ``.agent-meta-managed`` indexes and
  the 6 ``generated-file-hashes.json`` that gain the new command keys (Claude,
  Copilot, Gemini, Mammouth, Opencode, ZCode; Continue renders the commands but
  carries no ``.meta-config/generated-file-hashes.json`` in the baseline, and
  Codex/KimiCode have no command surface). No rule artifact, ``AGENTS.md`` or
  ``context-hashes.json`` changed. The 31 changed entries were patched per entry
  and the 14 added entries inserted at their sorted position -- not via
  ``--write`` -- after independently recomputing each digest from the rendered
  bytes with the harness's own ``_hash_file``. Because ``hashes.json`` is the
  only ``ac01-baseline`` file, its AC-T4 digest in
  ``tests/test_opencode_v2_surface.py`` follows the rebaselined tree
  (recomputed from the fixture bytes: ``d4771400…`` -> ``c49564db…``).
  ``slimming-golden`` was re-derived for the two touched goldens
  (``agent-meta-manager.md`` 1.26.0 + recipe 14d, ``release.md`` 1.13.0; both
  through the real sync path, documented in the slimming diff manifest §19) and
  its AC-T4 digest moved (``6b0c5724…`` -> ``5cbe9ea4…``); ``compact-golden``
  stayed unchanged (``44148ea7…``). ``AC01_EXCEPTIONS`` is NOT extended.

- Review follow-up on issue #1089 (``feat/release-checklist``, 2026-11-01): the
  ``/set-release-checklist`` command now states the YAML bool rule correctly -
  an unquoted ``off`` is parsed as a boolean by YAML 1.1 and the loader
  normalizes it back to ``"off"``; only an unquoted ``on``/``true`` is rejected
  with "quote the value". The command is a rendered source, so exactly **7 of
  1099 hashes moved; 0 added/removed** - the ``set-release-checklist`` render of
  the seven command-writing providers (``Claude/.claude/commands``,
  ``Continue/.continue/prompts``, ``Copilot/.github/prompts``,
  ``Gemini/.gemini/commands``, ``Mammouth/.mammouth/commands``,
  ``Opencode/.opencode/commands``, ``ZCode/.zcode/commands``). No other artifact,
  ``AGENTS.md``, ``context-hashes.json`` or golden content changed. The manifest
  was patched **per entry** (7 single-line replacements, 1094 of the 1101 lines
  untouched) - not via ``--write`` - after independently recomputing each digest
  from the rendered file bytes with the harness's own ``_hash_file``. Because
  ``hashes.json`` is the only ``ac01-baseline`` file, its AC-T4 digest in
  ``tests/test_opencode_v2_surface.py`` follows the rebaselined tree
  (recomputed from the fixture bytes: ``c49564db…`` -> ``f74d3088…``);
  ``slimming-golden`` and ``compact-golden`` were re-verified as unchanged
  (``5cbe9ea4…``/``44148ea7…``). ``AC01_EXCEPTIONS`` is NOT extended.

- Test environments (SPEC-TEST-ENVIRONMENTS-2026-10-31): six role templates were
  minor-bumped (``tester`` 2.9.0, ``e2e-tester`` 1.7.0, ``developer`` 4.9.0,
  ``docker`` 1.10.0, ``devops-engineer`` 1.8.0, ``test-executor`` 1.3.0) and
  ``agent-meta-manager`` to 1.27.0 (the test-environment recipe plus its §3
  row). The conditional gate block is byte-neutral when ``test-environments`` is
  unset - proven by ``test_unset_render_matches_baseline`` (the dedicated
  baseline ``tests/fixtures/test-env-baseline/hashes.json`` stays unchanged) and
  by the slimming gate, whose six role diffs are exactly the frontmatter pins.
  Changed: **63 of 1099 hashes; 0 added/removed** - the seven roles (six base
  templates + manager) x 9 providers. No rule artifact, ``AGENTS.md``,
  ``context-hashes.json`` or other artifact changed. The manifest was patched
  **per entry** (63 single-line replacements, 1038 of the 1101 lines untouched)
  - not via ``--write`` - after independently recomputing each digest from the
  rendered file bytes with the harness's own ``_hash_file``. Because
  ``hashes.json`` is the only ``ac01-baseline`` file, its AC-T4 digest in
  ``tests/test_opencode_v2_surface.py`` follows the rebaselined tree
  (recomputed from the fixture bytes: ``f74d3088…`` -> ``ea59522c…``).
  ``slimming-golden`` was re-derived for ``agent-meta-manager.md`` (recipe +
  §3 row + version, manifest §20) and re-pinned for the six role version pins
  (frontmatter only); its digest moved (``5cbe9ea4…`` -> ``a9990f4c…``).
  ``compact-golden`` stayed unchanged (``44148ea7…``). ``AC01_EXCEPTIONS`` is
  NOT extended.

- Issues #1078/#1041 (hook fixes; ``hook_common.sh`` 1.7.0 -> 1.8.0, ``dod-push-check.sh``
  2.2.0 -> 2.3.0, 2026-11-02, ``fix/hooks-guards``): ``hook_known_tool_name`` gains the 17
  current built-ins (``ToolSearch``, ``TaskCreate``, ``TaskUpdate``, ``TaskList``, ``TaskGet``,
  ``Monitor``, ``ScheduleWakeup``, ``CronCreate``, ``CronDelete``, ``CronList``, ``EnterPlanMode``,
  ``PushNotification``, ``RemoteTrigger``, ``SendUserFile``, ``Artifact``, ``ArtifactComments``,
  ``ArtifactData``; ``EnterWorktree``/``ExitWorktree`` stay blocked on purpose) and
  ``dod-push-check.sh`` honours ``push.recurseSubmodules`` from the config/``-c``/``GIT_CONFIG_*``
  value. Exactly **3 of 1099 hashes moved; 0 added/removed**: the two ``hook_common.sh`` renders
  (``Claude/.claude/hooks/lib/hook_common.sh`` ``bcdf8b16…`` -> ``3564b211…``,
  ``Gemini/.agents/hooks/lib/hook_common.sh`` ``bcdf8b16…`` -> ``3564b211…``; one identical
  render for both providers, the lib carries no ``{{AGENT_META_PROVIDER}}``) and the only
  ``dod-push-check.sh`` render (``Claude/.claude/hooks/dod-push-check.sh`` ``e7458463…`` ->
  ``cdfd0131…``). No rule, agent or command artifact, ``AGENTS.md``, ``context-hashes.json``
  or golden content changed. The manifest was patched **per entry** (3 single-line replacements,
  1098 of the 1101 lines untouched) -- not via ``--write`` -- after independently recomputing
  each digest from the rendered file bytes with the harness's own ``_hash_file``. Because
  ``hashes.json`` is the only ``ac01-baseline`` file, its AC-T4 digest in
  ``tests/test_opencode_v2_surface.py`` follows the rebaselined tree (recomputed from the
  fixture bytes: ``ea59522c…`` -> ``647b75a4…``); ``slimming-golden`` and ``compact-golden``
  were re-verified as unchanged (``a9990f4c…``/``44148ea7…``). ``AC01_EXCEPTIONS`` is NOT
  extended.
- Issue #1041 (PR A review follow-up; ``dod-push-check.sh`` 2.3.0 -> 2.4.0, 2026-11-02,
  ``fix/hooks-guards``): the tag-only exemption is gated on the repository declaring
  submodules (same predicate as the destination check) and the ``push.recurseSubmodules``
  override value is parsed for ``-c``/``GIT_CONFIG_VALUE_n`` (``--config-env`` stays
  value-blind). Exactly **1 of 1101 hashes moved; 0 added/removed**: the only
  ``dod-push-check.sh`` render (``Claude/.claude/hooks/dod-push-check.sh`` ``cdfd0131…``
  -> ``89759e26…``). No rule, agent or command artifact, ``AGENTS.md``,
  ``context-hashes.json`` or golden content changed. The manifest was patched **per entry**
  (1 single-line replacement, 1100 of the 1101 lines untouched) -- not via ``--write`` --
  after independently recomputing the digest from the rendered file bytes with the
  harness's own ``_hash_file``. Because ``hashes.json`` is the only ``ac01-baseline``
  file, its AC-T4 digest in ``tests/test_opencode_v2_surface.py`` follows the rebaselined
  tree (recomputed from the fixture bytes: ``647b75a4…`` -> ``90f1f74a…``);
  ``slimming-golden`` and ``compact-golden`` were re-verified as unchanged
   (``a9990f4c…``/``44148ea7…``). ``AC01_EXCEPTIONS`` is NOT extended.
- Issue #1151 (system audit 2026-11-06, group G1 hook fixes, ``fix/hooks-containment-allowlist``):
  ``hook_common.sh`` 1.8.1 -> 1.9.0 (allow-list parity, substitution bodies), ``dod-push-check.sh``
  2.4.0 -> 2.5.0, ``orchestrator-guard-impl.sh`` 1.10.0 -> 1.11.0 (new ``AGENT_META_HOOK_AGENT_ID``
  sync-time placeholder: ``true`` for Claude, ``false`` for Gemini), ``repo-containment-impl.sh``
  1.5.0 -> 1.6.0, both graphify guards 1.1.0 -> 1.2.0, and the strict-mode sentence in
  ``rules/1-generic/use-orchestrator.md`` (the matrix project is strict, so "read-only git in the
  main chat ok" became the strict wording). Exactly **18 of 1096 hashes moved; 0 added/removed**:
  9 hook renders (Claude: dod-push-check, both graphify guards, lib/hook_common, orchestrator-guard-impl,
  repo-containment-impl; Gemini: lib/hook_common, orchestrator-guard-impl, repo-containment-impl), the
  3 ``use-orchestrator`` rule renders (Claude, Continue, Copilot) and 6 ``AGENTS.md`` (Codex, Gemini,
  KimiCode, Mammouth, Opencode, ZCode) that embed the rule. The manifest was patched **per entry** (18
  single-line replacements) from the harness's own ``render_matrix_hashes`` -- not via ``--write``.
  AC-T4 digest in ``tests/test_opencode_v2_surface.py`` follows (``3acc668e…`` -> ``706e1515…``);
  ``slimming-golden`` re-verified unchanged; ``compact-golden`` re-derived from the real compact render
  (the same strict-mode sentence in ``agents-managed.md``, one line). ``AC01_EXCEPTIONS`` is NOT extended.
- Issue #1151 review follow-up (same branch): ``repo-containment-impl.sh`` (cd inside ``$(...)``/
  subshells scoped, ``$CLAUDE_PROJECT_DIR``/``$PWD`` resolved, old-style ``tar cf``) and one
  sentence in ``rules/1-generic/use-orchestrator.md`` (worker subagents without ``git`` sentinel
  cannot run ``git init``/config writes/``git stash``). Exactly **11 of 1096 hashes moved; 0
  added/removed**: 2 hook renders (Claude, Gemini ``repo-containment-impl.sh``), 3 ``use-orchestrator``
  rule renders (Claude, Continue, Copilot) and 6 ``AGENTS.md`` (Codex, Gemini, KimiCode, Mammouth,
  Opencode, ZCode). Patched per entry from ``render_matrix_hashes`` (not ``--write``). AC-T4 digest
  ``706e1515…`` -> ``00178459…``; ``compact-golden`` +1 line (``eaeaddfe…`` -> ``e7eecf36…``);
  ``slimming-golden`` unchanged. ``AC01_EXCEPTIONS`` is NOT extended.
- Issues #1072/#1073 (gitignore managed block, 2026-11-02, ``fix/gitignore-managed-block``):
  #1072 stops the shadowing warning for provider directories that a rule *inside* the managed
  block already matches (rules outside the block still warn), and #1073 writes
  ``.meta-config/platform-defaults.resolved.yaml`` into the managed block unconditionally in
  both managed branches (fresh block and merge). Both change only the rendered managed block
  of every provider, so exactly **9 of 1099 hashes moved; 0 added/removed** -- one
  ``<Provider>/.gitignore`` per provider (Claude, Codex, Continue, Copilot, Gemini, KimiCode,
  Mammouth, Opencode, ZCode). No rule, agent or command artifact, ``AGENTS.md``,
  ``context-hashes.json`` or golden content changed. The manifest was patched **per entry**
  (9 single-line replacements, 1092 of the 1101 lines untouched) -- not via ``--write`` --
  after independently recomputing each digest from the rendered file bytes with the harness's
  own ``_hash_file``. Because ``hashes.json`` is the only ``ac01-baseline`` file, its AC-T4
  digest in ``tests/test_opencode_v2_surface.py`` follows the rebaselined tree (recomputed
  from the fixture bytes: ``90f1f74a…`` -> ``afe5c7cc…``); ``slimming-golden`` and
  ``compact-golden`` were re-verified as unchanged (``a9990f4c…``/``44148ea7…``).
  ``AC01_EXCEPTIONS`` is NOT extended.
- Issue #1093 (empty remote-URL parens in the git template; ``git.md`` 2.1.1,
  ``fix/git-template-empty-remote-url``, 2026-11-02): the line now keeps the platform name
  unconditional and moves only the ``({{GIT_REMOTE_URL}})`` suffix behind the
  ``GIT_REMOTE_URL_SET`` conditional, so a project without a remote renders
  ``**Git platform:** <platform>`` instead of ``**Git platform:** <platform> ()``. The
  template is a rendered source, so exactly **9 of 1099 hashes moved; 0 added/removed** --
  the ``git`` agent render of every provider (``Claude/.claude/agents/git.md``
  ``bbd5bf7c…`` -> ``f101f48e…``, ``Codex/.codex/agents/git.toml`` ``a08e8baf…`` ->
  ``285b15db…``, ``Continue/.continue/agents/git.md`` ``2e0f98b5…`` -> ``05a10b66…``,
  ``Copilot/.github/agents/git.agent.md`` ``630385ff…`` -> ``9cd41292…``,
  ``Gemini/.gemini/agents/git.md`` ``9392e6c0…`` -> ``61d1a2e4…``,
  ``KimiCode/.kimi-code/agents/git.md`` ``c05ae33a…`` -> ``dd69344f…``,
  ``Mammouth/.mammouth/agents/git.md`` ``b00e2706…`` -> ``36dbcfe7…``,
  ``Opencode/.opencode/agents/git.md`` ``95f07030…`` -> ``872577e8…``,
  ``ZCode/.zcode/agents/git.md`` ``3e741e14…`` -> ``d55d9509…``). No rule, command or
  other agent artifact, ``AGENTS.md``, ``context-hashes.json`` or golden content changed.
  The manifest was patched **per entry** (9 single-line replacements, 1092 of the 1101
  lines untouched) -- not via ``--write`` -- after independently recomputing each digest
  from the rendered file bytes with the harness's own ``_hash_file``. Because
  ``hashes.json`` is the only ``ac01-baseline`` file, its AC-T4 digest in
  ``tests/test_opencode_v2_surface.py`` follows the rebaselined tree (recomputed from the
  fixture bytes: ``afe5c7cc…`` -> ``5232fe62…``); ``compact-golden`` was
  re-verified as unchanged (``44148ea7…``), while ``slimming-golden`` was re-pinned
  frontmatter-only for the ``git.md`` version pin (2.1.0 -> 2.1.1, its digest
  ``a9990f4c…`` -> ``3bd5c31c…``). ``AC01_EXCEPTIONS`` is NOT extended.
- Issue #1093 residual (whitespace-only / non-string remote URL; ``git.md`` 2.1.2,
  ``fix/git-remote-url-set-hardening``, 2026-11-02): ``GIT_REMOTE_URL_SET`` now requires a
  non-blank string, so ``remote-url: '   '`` and a non-string YAML value (list/dict) count
  as absent and no longer render ``(   )`` or a Python repr. The template is unchanged, but
  the patch version bump is a rendered source change: exactly **9 of 1099 hashes moved; 0
  added/removed** -- the ``git`` agent render of every provider (``Claude/.claude/agents/git.md``
  ``f101f48e…`` -> ``3088c609…``, ``Codex/.codex/agents/git.toml`` ``285b15db…`` ->
  ``57ac1397…``, ``Continue/.continue/agents/git.md`` ``05a10b66…`` -> ``815fee5e…``,
  ``Copilot/.github/agents/git.agent.md`` ``9cd41292…`` -> ``9e7ea1a8…``,
  ``Gemini/.gemini/agents/git.md`` ``61d1a2e4…`` -> ``a26c4d04…``,
  ``KimiCode/.kimi-code/agents/git.md`` ``dd69344f…`` -> ``faaeb937…``,
  ``Mammouth/.mammouth/agents/git.md`` ``36dbcfe7…`` -> ``d2faeca5…``,
  ``Opencode/.opencode/agents/git.md`` ``872577e8…`` -> ``7461efb3…``,
  ``ZCode/.zcode/agents/git.md`` ``d55d9509…`` -> ``3786a820…``). No rule, command or
  other agent artifact, ``AGENTS.md``, ``context-hashes.json`` or golden content changed.
  The manifest was patched **per entry** (9 single-line replacements) -- not via
  ``--write`` -- after independently recomputing each digest from the rendered file bytes
  with the harness's own ``_hash_file``. Because ``hashes.json`` is the only
  ``ac01-baseline`` file, its AC-T4 digest in ``tests/test_opencode_v2_surface.py`` follows
  the rebaselined tree (``5232fe62…`` -> ``74290aad…``); ``compact-golden`` was
  re-verified as unchanged (``44148ea7…``), while ``slimming-golden`` was re-pinned
  frontmatter-only for the ``git.md`` version pin (2.1.1 -> 2.1.2, its digest
  ``3bd5c31c…`` -> ``8857b666…``). ``AC01_EXCEPTIONS`` is NOT extended.

- Issue #1079 (host-local pytest basetemp; **no rebaseline**, 2026-11-03,
  ``fix/test-basetemp-allowlist``): the new ``settings-allow-dirs-key`` writer adds the
  resolved, machine-specific ``<temp>/<user>/pytest-agent-meta`` to
  ``permissions.additionalDirectories`` of the gitignored
  ``Claude/.claude/settings.local.json``, so exactly that one key drifted (1 of 1099).
  The file is host-local by design (gitignored, never part of the shipped contract), so it
  is excluded from the render-identity key set instead of being re-pinned: a rebaseline
  would bake this machine's username/temp path into ``hashes.json`` and drift on every
  other machine. ``hashes.json`` is NOT modified -- the three pre-existing
  ``settings.local.json`` entries stay in the file but are ignored on both sides (a future
  justified ``--write`` drops them). No other key embeds an absolute host path
  (``sync.log`` was already skipped by ``_SKIP_RE``). ``AC01_EXCEPTIONS`` is NOT extended.

- Bug batch PR B (#1071/#1083/#1082, 2026-11-03, ``fix/consistency-false-positives``):
  #1071 gates the dispatch tables on ``ROLE_<R>_ACTIVE`` (no dangling-dispatch false
  positives), #1083 downgrades a frontmatter role mention to the
  ``active-set.dangling-mention-frontmatter`` WARNING and neutralizes the ``tester`` /
  ``data-engineer`` descriptions, #1082 makes the placeholder check skip code spans and
  fences. Five templates were minor-bumped (``orchestrator`` 8.9.0,
  ``senior-developer`` 1.11.0, ``meta-feedback`` 2.7.0, ``tester`` 2.10.0,
  ``data-engineer`` 0.7.0) and ``hacs-tester`` re-pinned to ``tester@2.10.0``.
  Exactly **36 of 1099 hashes moved; 0 added/removed** -- the four matrix roles
  ``data-engineer``/``meta-feedback``/``orchestrator``/``tester`` × 9 providers.
  ``senior-developer``/``hacs-tester`` are not in the default matrix. No rule,
  ``AGENTS.md``, ``context-hashes.json`` or other artifact changed. The manifest was
  patched **per entry** (36 single-line replacements, 1065 of the 1101 lines untouched)
  -- not via ``--write`` -- after independently recomputing every digest from the
  rendered file bytes with the harness's own ``_hash_file``. Because ``hashes.json`` is
  the only ``ac01-baseline`` file, its AC-T4 digest in
  ``tests/test_opencode_v2_surface.py`` follows the rebaselined tree (recomputed from
  the fixture bytes: ``74290aad…`` -> ``2adf04f6…``). ``slimming-golden`` was re-pinned
  for the five touched role goldens (``data-engineer``, ``meta-feedback``,
  ``orchestrator``, ``senior-developer``, ``tester``; frontmatter incl. the two #1083
  descriptions, manifest §22) and its AC-T4 digest moved (``8857b666…`` ->
  ``607b6c8a…``); ``compact-golden`` stayed unchanged (``44148ea7…``).
  ``AC01_EXCEPTIONS`` is NOT extended.

- Review follow-up PR #1122 (Bug-Batch PR B, 2026-11-04,
  ``fix/consistency-false-positives``): the AC-38 doctor fixtures for
  ``dangling-role-mention-frontmatter``, the senior-escalation persona aligned to
  ``STATUS: escalate`` + reason + metric, the frontmatter skip in the dispatch
  check (D7), the gated base ``developer`` row (#1071) and the neutralized
  ``code-reviewer`` hint / ``ux-researcher`` description change three templates:
  ``orchestrator`` 8.9.1, ``senior-developer`` 1.11.1, ``code-reviewer`` 1.9.3
  and ``ux-researcher`` 1.0.2 (``hacs-code-reviewer`` re-pinned to
  ``code-reviewer@1.9.3``). Exactly **28 of 1099 hashes moved; 0 added/removed**
  -- ``code-reviewer``/``orchestrator``/``ux-researcher`` × 9 providers plus
  ``Copilot/.github/copilot-instructions.md`` (it embeds the ``code-reviewer``
  hint). No rule, ``AGENTS.md``, ``context-hashes.json`` or other artifact
  changed. The manifest was patched **per entry** (28 single-line replacements,
  1071 of the 1099 lines untouched) -- not via ``--write`` -- after independently
  recomputing every digest from the rendered file bytes with the harness's own
  ``_hash_file``. Because ``hashes.json`` is the only ``ac01-baseline`` file, its
  AC-T4 digest in ``tests/test_opencode_v2_surface.py`` follows the rebaselined
  tree (recomputed from the fixture bytes: ``2adf04f6…`` -> ``1a6df729…``).
  ``slimming-golden`` was re-pinned for ``orchestrator``, ``code-reviewer`` and
  ``senior-developer`` (frontmatter pins plus the neutralized ``code-reviewer``
  hint; manifest §23) and its AC-T4 digest moved (``607b6c8a…`` -> ``dcd2f5be…``);
  ``compact-golden`` stayed unchanged (``44148ea7…``). ``AC01_EXCEPTIONS`` is NOT
  extended.

- Orchestrator topology v1 (SPEC-orchestrator-topology-2026-11-03, issue #1077,
  Task 18, 2026-11-04, ``feat/orchestrator-topology-v1``): the A2A rule now
  states the singleton gate conditionally and both singleton-bearing agent
  templates carry the conditional line (``orchestrator`` 8.9.1 -> **8.10.0**,
  ``_reference-agent`` 1.2.1 -> 1.3.0). Because the new branch is gated on
  ``ORCH_TOPOLOGY_EXPLICIT`` and the else branch is word-identical, the **unset**
  render is byte-identical: the two ``tests/fixtures/topology-golden`` fixtures
  are **unchanged** (AC-6) and no rule render moved. Exactly **9 of 1099 hashes
  moved; 0 added/removed** -- the ``orchestrator`` agent render of every provider
  (``Claude/.claude/agents/orchestrator.md`` ``dd79e5cf…`` -> ``9b7bc261…``,
  ``Codex/.codex/agents/orchestrator.toml`` ``9e713667…`` -> ``3a99d13a…``,
  ``Continue/.continue/agents/orchestrator.md`` ``1b8a2c4f…`` -> ``7d8d91f6…``,
  ``Copilot/.github/agents/orchestrator.agent.md`` ``5cd5fac2…`` -> ``140c93fb…``,
  ``Gemini/.gemini/agents/orchestrator.md`` ``f4a0a756…`` -> ``14e86f57…``,
  ``KimiCode/.kimi-code/agents/orchestrator.md`` ``7a38413b…`` -> ``4e0a081c…``,
  ``Mammouth/.mammouth/agents/orchestrator.md`` ``03a03ae0…`` -> ``379628c6…``,
  ``Opencode/.opencode/agents/orchestrator.md`` ``df357d75…`` -> ``4d101617…``,
  ``ZCode/.zcode/agents/orchestrator.md`` ``1db5e066…`` -> ``e69d405a…``) --
  i.e. the frontmatter version/``generated-from`` pins only; the body is
  unchanged and the ``_reference-agent`` template is not part of the matrix.
  The manifest was patched **per entry** (9 single-line replacements, 1090 of the
  1099 lines untouched) -- not via ``--write`` -- after independently recomputing
  every digest from the rendered file bytes with the harness's own ``_hash_file``.
  Because ``hashes.json`` is the only ``ac01-baseline`` file, its AC-T4 digest in
  ``tests/test_opencode_v2_surface.py`` follows the rebaselined tree (recomputed
  from the fixture bytes: ``1a6df729…`` -> ``a88fca0d…``). ``slimming-golden``
  and ``compact-golden`` were re-pinned frontmatter-only for the same
  ``orchestrator`` version pins (manifest §24) and their AC-T4 digests moved
  (``dcd2f5be…`` -> ``8d1ade1a…`` / ``416cd520…`` -> ``badf2362…``).
  ``AC01_EXCEPTIONS`` is NOT extended.

- Orchestrator topology P3 (SPEC-orchestrator-topology-2026-11-03, issue #1077,
  2026-11-05, ``feat/orchestrator-topology-p3``): multi-instance lands and two
  rendered sources move. The guard template ``orchestrator-guard-impl.sh`` is
  bumped ``1.9.0 -> 1.10.0`` (audit-only instance id in the sentinel grammar and
  the orchestrator audit line) and renders for Claude and Gemini only; the
  ``config/project-config.schema.json`` description text for
  ``orchestrator.max-instances``/``singleton`` is embedded in every copied
  ``.meta-config/project.yaml`` (9 providers). Exactly **11 of 1099 hashes
  moved; 0 added/removed**: the two guard renders
  (``Claude/.claude/hooks/orchestrator-guard-impl.sh``, Gemini's counterpart)
  plus the nine ``.meta-config/project.yaml`` files. No agent, rule, command or
  ``AGENTS.md`` artifact and no ``context-hashes.json`` changed. The manifest was
  patched **per entry** (11 single-line replacements, 1088 of the 1099 lines
  untouched) -- not via ``--write`` -- after independently recomputing every
  digest from the rendered file bytes with the harness's own ``_hash_file``.
  Because ``hashes.json`` is the only ``ac01-baseline`` file, its AC-T4 digest in
  ``tests/test_opencode_v2_surface.py`` follows the rebaselined tree (recomputed
  from the fixture bytes: ``a88fca0d…`` -> ``bbcc14a7…``); ``slimming-golden``
  and ``compact-golden`` were re-verified as unchanged
  (``8d1ade1a…``/``badf2362…``) and the ``topology-golden`` fixtures are
  unchanged. ``AC01_EXCEPTIONS`` is NOT extended.
* Issue #1158 (G4 DoD/spec-gate: REQ/test mandates gated, feature-lifecycle
  approve stage, planner APPROVED precondition, one classify-gate statement,
  live ``max_depth`` doc): **45 of 1096 hashes moved; 0 added/removed** --
  ``git``/``orchestrator``/``planner``/``tester`` x 9 providers (36), the
  ``a2a-delegation-gates`` rule for Claude/Continue/Copilot (3) and the six
  ``AGENTS.md`` that embed ``use-orchestrator`` (Codex, Gemini, KimiCode,
  Mammouth, Opencode, ZCode). Regenerated via ``--write`` and verified per entry
  against the previous manifest (no other key moved). ``slimming-golden``
  (git/orchestrator/planner/tester) and ``compact-golden`` (orchestrator,
  agents-managed) were patched per hunk with exactly these deltas; both
  ``topology-golden`` fixtures follow the K-10 ``max_depth`` row. AC-T4 digests
  in ``tests/test_opencode_v2_surface.py`` follow. ``AC01_EXCEPTIONS`` is NOT
  extended.

- Orchestrator worker control (issue #1157, 2026-11-06,
  ``fix/orchestrator-tools-handback``): ``orchestrator`` 8.10.0 -> **8.11.0**
  (Sync-Call/Hard-interrupt text names ``SendMessage``/``TaskStop``, BARRIER step 6
  "worker run without report = failed", dispatch-context hand-back line, the
  unverified ``run_in_background: false`` hint) and ``a2a-delegation-gates``
  (gate 3 sentence + platform depth-limit row); Claude's primary role gains the
  data-declared ``primary-role-tools`` ``SendMessage``/``TaskStop``. Exactly
  **18 of 1096 hashes moved; 0 added/removed**: the ``orchestrator`` agent render
  of all nine providers, the three standalone rule renders
  (``Claude/.claude/rules/a2a-delegation-gates.md``,
  ``Continue/.continue/rules/a2a-delegation-gates.md``,
  ``Copilot/.github/instructions/a2a-delegation-gates.instructions.md``) and the
  six ``AGENTS.md`` that embed the rule (Codex, Gemini, KimiCode, Mammouth,
  Opencode, ZCode). The manifest was patched **per entry** (18 single-line
  replacements) -- not via ``--write`` -- from two independent matrix renders
  with identical drift. AC-T4 digests in ``tests/test_opencode_v2_surface.py``
  follow: ac01 ``3acc668e…`` -> ``c241ad07…``, slimming ``8d1ade1a…`` ->
  ``2054b433…``, compact ``fa992b69…`` -> ``1f37318f…`` (both orchestrator goldens carry
  exactly the template diff; ``compact-golden/agents-managed.md`` carries the
  one-line gate-3 sentence, log in ``tests/test_gate_card_compact.py``). Both ``topology-golden`` fixtures were regenerated
  with the README generator and differ by exactly the two ``a2a-delegation-gates``
  rule lines (gate-3 sentence, depth row) -- no topology wording moved.
  ``AC01_EXCEPTIONS`` is NOT extended.

- Merge of ``main`` (#1151 G1 hooks, #1156 G2 sync) into ``fix/orchestrator-tools-handback``
  (#1157, 2026-11-07): the manifest conflicted only on the six ``AGENTS.md`` keys, which both
  sides moved (G1: ``use-orchestrator`` sentences; #1157: ``a2a-delegation-gates`` gate 3).
  The 12 G1-only keys (9 hook renders, 3 ``use-orchestrator`` rule renders) and the 12
  #1157-only keys (9 ``orchestrator`` renders, 3 ``a2a-delegation-gates`` rule renders) merged
  cleanly. A fresh matrix render drifted on exactly those **6 of 1096** ``AGENTS.md`` keys
  (Codex, Gemini, KimiCode, Mammouth, Opencode, ZCode; each render verified to carry both
  sentences); they were patched **per entry** from the harness's own ``_hash_file`` over the
  rendered tree -- not via ``--write``. Net vs. the merge base: 30 keys. AC-T4 digests in
  ``tests/test_opencode_v2_surface.py`` recomputed from the merged trees: ac01 ->
  ``e89ed97c…``, compact -> ``e9dc8776…`` (``agents-managed.md`` carries both sentences),
  slimming = #1157 (``c08f66b0…``). ``AC01_EXCEPTIONS`` is NOT extended.

- Merge of ``main`` (#1151 G1, #1156 G2, #1157/#1162 G3, ``orchestrator`` 8.11.0) into
  ``fix/dod-gating-spec-gate`` (#1158 G4, ``orchestrator`` -> 8.11.1, 2026-11-07): 27 G4-only keys
  and 12 main-only keys (9 hook renders, 3 ``use-orchestrator`` rule renders) merged by key;
  18 keys were moved by both sides (9 ``orchestrator`` renders, 3 ``a2a-delegation-gates`` rule
  renders, 6 ``AGENTS.md``). A fresh matrix render drifted on exactly those **18 of 1096** keys
  (renders verified to carry main's gate-3 sentence + depth row, G4's soft-gate ``max_depth`` row,
  ``TaskStop``, 8.11.1); patched **per entry** from ``render_matrix_hashes`` -- not via ``--write``.
  Net: 45 keys vs ``main``, 30 vs the G4 head. ``AC01_EXCEPTIONS`` is NOT extended.

- Issue #1161 (G7 token diet, 2026-11-07, ``chore/token-diet``): ``rules/1-generic/branch-guard.md``
  keeps both anchored headings but trims ``## Guard-Terminologie`` to the two definitions and
  ``## Bekannte Grenzen`` to a pointer; the full text moved verbatim to
  ``docs/concepts/branch-guard-known-limits.md``. Exactly **9 of 1096 hashes moved; 0
  added/removed**: the three rule renders (``Claude/.claude/rules/branch-guard.md``
  ``504c5ceb…`` -> ``f231e99f…``, ``Continue/.continue/rules/branch-guard.md`` ``ba868b11…`` ->
  ``1489c60a…``, ``Copilot/.github/instructions/branch-guard.instructions.md`` ``f533e9cb…`` ->
  ``797d2250…``) and the six ``AGENTS.md`` embedding the rule (``Codex`` ``af21d605…`` ->
  ``01f721e1…``, ``Gemini`` ``a07ca418…`` -> ``dbe42e7d…``, ``KimiCode`` ``bbdf7721…`` ->
  ``15bf6db1…``, ``Mammouth`` ``faff25fb…`` -> ``0b7db94b…``, ``Opencode`` ``441342f4…`` ->
  ``1d388688…``, ``ZCode`` ``7427ae46…`` -> ``811090f6…``). Patched **per entry** from
  ``render_matrix_hashes`` -- not via ``--write``. AC-T4: ac01 ``9df232ba…`` -> ``7c993f7f…``;
  ``slimming-golden``/``compact-golden`` unchanged. ``AC01_EXCEPTIONS`` is NOT extended.
- Issue #1161 step 2 (G7, compact ``route_intent`` JSON): ``render_routing_tool_definition``
  serializes the ``json`` format with ``separators=(",", ":")`` instead of ``indent=2`` (same
  data, the block becomes one line; -18,839 B per matrix orchestrator). Exactly **4 of 1096
  hashes moved; 0 added/removed** -- the orchestrator renders of the four ``json`` providers
  (``Claude/.claude/agents/orchestrator.md`` ``9d6de73b…`` -> ``9ce45f0b…``,
  ``Codex/.codex/agents/orchestrator.toml`` ``67070c9a…`` -> ``96136789…``,
  ``Gemini/.gemini/agents/orchestrator.md`` ``9774d27d…`` -> ``695cbaa3…``,
  ``Opencode/.opencode/agents/orchestrator.md`` ``6962a82b…`` -> ``7cbfaedd…``). YAML-format
  providers unchanged; the MATRIX entry of ``generated-file-hashes.json`` is unchanged (the repo's own ``.meta-config/generated-file-hashes.json`` changes by 3 entries). Patched
  **per entry** from ``render_matrix_hashes`` -- not via ``--write``. ``slimming-golden``
  ``orchestrator.md``: only the JSON block re-serialized (L214-1887 -> one line, data equal);
  ``compact-golden`` unchanged (line block, no JSON). AC-T4: ac01 ``7c993f7f…`` -> ``a75074b1…``,
  slimming ``6598edb7…`` -> ``59224e04…``. ``AC01_EXCEPTIONS`` is NOT extended.
- Issue #1190 T9 (orchestrator topology, AC-17): the singleton guard block is topology-aware; in the
  Opencode matrix project the orchestrator is derived `primary`, so exactly **1 of 1096 hashes moved;
  0 added/removed**: ``Opencode/.opencode/agents/agent-meta-manager.md`` ``c660ad41…`` -> ``82729745…``
  (only the first bullet: "der **ist** der Session-Einstieg" instead of "der vom `main_chat` gespawnte").
- Issues #1180/#1000 (2026-11-12): **24 of 1096 hashes moved; 0 added/removed**. #1180 inlined the core limits
  and dropped the ``docs/concepts`` pointers in ``a2a-delegation-gates``/``branch-guard``/``repo-containment``
  (3 Claude + 3 Continue + 3 Copilot rule files + ``AGENTS.md`` of the six AGENTS.md providers); #1000 added one
  ``spec-plan-workflow`` bullet that is inlined into the orchestrator artifact (9 providers). Re-written via
  ``--write``; the ``topology-golden``/``active-set-prose`` a2a fixtures lost the same pointer text.

Run: python -m pytest tests/test_ac01_render_identity.py -q
"""

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Dict, List, Sequence

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SYNC = _REPO_ROOT / "scripts" / "sync.py"
sys.path.insert(0, str(_REPO_ROOT / "scripts"))
from lib.config import _resolve_agent_meta_date  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.variables import (  # noqa: E402
    _topology_flags,
    strip_inactive_conditional_blocks,
    substitute,
)
_MANIFEST = Path(__file__).resolve().parent / "fixtures" / "ac01-baseline" / "hashes.json"
_PROVIDERS = sorted(
    yaml.safe_load((_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))["providers"]
)

# AC-01 exception list (i)-(v) as data: regexes over "<provider>/<relpath>".
# (i)/(ii) new meta-doctor / meta-optimizer role artifacts and their roster rows,
# (iv)/(v) produce no render diff in a regular sync, so there is no pattern (Spec AC-01 iv/v);
# (ii)/(iii) (meta-doctor roster rows in existing files, golden rebaseline) are done
# via rebaseline in package 0e, not via a path pattern.
# Empty entries would hide drift, so every pattern must stay role/entry specific.
AC01_EXCEPTIONS = frozenset({
    r".*/meta-doctor\.(md|toml|agent\.md)$",
    r".*/meta-optimizer\.(md|toml|agent\.md)$",
    r".*/standalone/agents/meta-doctor\.md$",
})

# Host-local files: written into a gitignored path in every real project, so
# their content is not part of the shipped render contract. Providers may put
# machine-specific absolute paths into them (the pytest basetemp allow-list,
# #1079), which a byte-identity baseline must never pin. Excluded on BOTH sides
# (rendered key set and manifest) so a rebaseline cannot re-introduce them.
_HOST_LOCAL_RE = re.compile(r"(^|/)settings\.local\.json$")


def is_host_local(path: str) -> bool:
    """True for gitignored, machine-specific files that never enter the key set."""
    return bool(_HOST_LOCAL_RE.search(path))


# Volatile, non-render artifacts: never part of the manifest.
_SKIP_RE = re.compile(r"(^|/)(\.git)(/|$)|(^|/)sync\.log$|\.sync-backup-")


def _run_sync(project: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SYNC), "--config", str(project / ".meta-config" / "project.yaml"), *extra],
        cwd=project, capture_output=True, text=True, timeout=300,
    )


def _make_project(root: Path, provider: str) -> Path:
    project = root / provider
    (project / ".meta-config").mkdir(parents=True)
    (project / ".meta-config" / "project.yaml").write_text(
        'agent-meta-version: "2.0.0-beta.1"\n'
        f"ai-providers:\n- {provider}\n"
        "dod-preset: rapid-prototyping\n"
        # AGENT_META_REPO is pinned to a neutral slug: since issue #1037 the
        # builder derives it from the checkout, and a derived value would make
        # this manifest depend on the cloning remote (fork CI would drift).
        "variables:\n  PROJECT_NAME: matrix\n  PROJECT_PREFIX: mx\n"
        "  AGENT_META_REPO: example/agent-meta\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    result = _run_sync(project, "--init")
    assert result.returncode == 0, f"{provider}: sync failed\n{result.stdout[-1500:]}\n{result.stderr[-1500:]}"
    return project


# Model independence: the resolved model ID is config data (model-tiers,
# tier-presets), not render logic, so it never enters the hash. Covers the YAML
# (`model: x`) and TOML (`model = "x"`) frontmatter forms of every provider.
_MODEL_LINE_RE = re.compile(rb"^model[ \t]*[:=].*$", re.M)
# generated-file-hashes.json only holds hashes of files that are compared on
# their own; keep its managed-path set, drop the derived (model-dependent) values.
_DERIVED_HASHES_NAME = "generated-file-hashes.json"


def _hash_file(path: Path, root: Path, dates: Sequence[str]) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    data = _MODEL_LINE_RE.sub(b"model: <MODEL>", data)
    if path.name == _DERIVED_HASHES_NAME:
        doc = json.loads(data)
        doc["hashes"] = sorted(doc.get("hashes", {}))
        data = json.dumps(doc, sort_keys=True).encode()
    # Normalize run-specific values: scratch root path (native, posix, JSON-escaped)
    # and the date stamp(s) captured once per run (before/after the sync).
    root_variants = {str(root), root.as_posix(), str(root).replace("\\", "\\\\")}
    for needle in sorted(root_variants, key=len, reverse=True):
        data = data.replace(needle.encode(), b"<ROOT>")
    for d in dates:
        data = data.replace(d.encode(), b"<DATE>")
    return hashlib.sha256(data).hexdigest()


def render_matrix_hashes(fixture_root: Path) -> Dict[str, str]:
    """Sync every provider into ``fixture_root/<provider>`` and hash all files.

    Returns ``{"<provider>/<relpath>": sha256}``.
    """
    fixture_root = Path(fixture_root)
    hashes: Dict[str, str] = {}
    date_before = date.today().isoformat()
    projects: List[tuple] = []
    for provider in _PROVIDERS:
        project = _make_project(fixture_root, provider)
        for f in sorted(project.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(fixture_root).as_posix()
            if _SKIP_RE.search(rel) or is_host_local(rel):
                continue
            projects.append((rel, f))
    # Date captured once before and once after all syncs; both are normalized.
    # Plus the reproducible AGENT_META_DATE (CHANGELOG release date, #752): it only
    # coincided with "today" on release day, so the manifest drifted the day after.
    dates = {date_before, date.today().isoformat(), _resolve_agent_meta_date(_REPO_ROOT)}
    for rel, f in projects:
        hashes[rel] = _hash_file(f, fixture_root, sorted(dates))
    return hashes


def diff_against_manifest(current: Dict[str, str], baseline: Dict[str, str]) -> List[str]:
    """Return drift entries not covered by ``AC01_EXCEPTIONS``."""
    patterns = [re.compile(p) for p in AC01_EXCEPTIONS]
    drift = []
    for path in sorted(set(current) | set(baseline)):
        if is_host_local(path):
            continue
        if current.get(path) == baseline.get(path):
            continue
        if any(p.match(path) for p in patterns):
            continue
        kind = "added" if path not in baseline else "removed" if path not in current else "changed"
        drift.append(f"{kind}: {path}")
    return drift


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    root = tmp_path_factory.mktemp("ac01")
    return root, render_matrix_hashes(root)


def test_ac01_render_identical_to_manifest(rendered):
    _root, current = rendered
    baseline = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    drift = diff_against_manifest(current, baseline)
    assert not drift, "AC-01 drift vs. main baseline:\n" + "\n".join(drift[:30])


def test_ac01_detects_drift(rendered):
    root, current = rendered
    baseline = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    victim = next(p for p in sorted(current) if p.endswith(".md") and not any(
        re.match(e, p) for e in AC01_EXCEPTIONS))
    target = root / victim
    original = target.read_bytes()
    try:
        target.write_bytes(original + b"\n<!-- drift -->\n")
        mutated = dict(current)
        mutated[victim] = _hash_file(target, root, [date.today().isoformat()])
        assert diff_against_manifest(mutated, baseline) == [f"changed: {victim}"]
    finally:
        target.write_bytes(original)


def test_ac01_render_key_set_excludes_host_local_settings(rendered):
    """Host-local settings must never become a render-identity key (#1079)."""
    _root, current = rendered
    assert not [path for path in current if is_host_local(path)]
    assert "Claude/.claude/settings.local.json" not in current


def test_ac01_host_local_settings_are_ignored_on_both_sides():
    assert is_host_local("Claude/.claude/settings.local.json")
    assert is_host_local("Gemini/.gemini/settings.local.json")
    assert is_host_local("Opencode/.opencode/settings.local.json")
    # Narrow on purpose: only the gitignored local settings overlay is excluded.
    assert not is_host_local("Claude/.claude/settings.json")
    assert not is_host_local("Claude/.claude/settings.local.json.bak")

    baseline = {
        "Claude/.claude/settings.local.json": "host-a",
        "Claude/.claude/settings.json": "committed",
    }
    current = {"Claude/.claude/settings.local.json": "host-b"}
    # The host-local digest change is inert; the missing committed key still drifts.
    assert diff_against_manifest(current, baseline) == [
        "removed: Claude/.claude/settings.json"
    ]


def test_ac01_hash_ignores_model_id(tmp_path):
    def h(name: str, text: str) -> str:
        f = tmp_path / name
        f.write_text(text, encoding="utf-8")
        return _hash_file(f, tmp_path, [])

    assert h("a.md", "---\nmodel: a/x-1\n---\nbody\n") == h("a.md", "---\nmodel: b/y-2\n---\nbody\n")
    assert h("a.toml", 'model = "x-1"\n') == h("a.toml", 'model = "y-2"\n')
    assert h("a.md", "---\nmodel: x\n---\nbody\n") != h("a.md", "---\nmodel: x\n---\nother\n")
    gfh = _DERIVED_HASHES_NAME
    assert h(gfh, '{"version": 1, "hashes": {"a.md": "11"}}') == h(gfh, '{"version": 1, "hashes": {"a.md": "22"}}')
    assert h(gfh, '{"version": 1, "hashes": {"a.md": "11"}}') != h(gfh, '{"version": 1, "hashes": {"b.md": "11"}}')


def test_ac01_exception_list_allows_meta_doctor_artifacts():
    baseline = {"codex/.codex/agents/developer.toml": "a"}
    current = dict(baseline, **{"codex/.codex/agents/meta-doctor.toml": "b"})
    assert diff_against_manifest(current, baseline) == []


def test_ac01_exception_list_allows_meta_optimizer_artifacts():
    baseline = {"codex/.codex/agents/developer.toml": "a"}
    current = dict(baseline, **{
        "Claude/.claude/agents/meta-optimizer.md": "b",
        "Codex/.codex/agents/meta-optimizer.toml": "c",
        # Copilot uses the two-suffix form; the old `[a-z]+$` pattern misses
        # it because of the dot in `.agent.md`.
        "Copilot/.github/agents/meta-optimizer.agent.md": "d",
    })
    assert diff_against_manifest(current, baseline) == []


# --- Orchestrator topology goldens (Task 16, AC-6/AC-18) --------------------
#
# The topology key is unset in both fixtures, so the A2A rule must render
# today's bytes in BOTH role states. The two states differ only in the
# ``ROLE_ORCHESTRATOR_ACTIVE`` flag, which the ActiveSet derives from the
# project's ``roles:`` allowlist:
#
#   role inactive + key unset -> ``Worker → HARD REJECT``
#   role active   + key unset -> ``Worker → `orchestrator` → HARD REJECT``
#
# The fixtures are produced through the real sync path (see
# ``render_topology_rule``), never hand-written, and use the same normalisation
# discipline as ``_hash_file``: CRLF folded to LF, volatile scratch roots
# replaced, model lines pinned. The rule render carries neither a model line
# nor a root today, so the normalisation is a no-op that keeps the contract
# explicit.
_TOPOLOGY_GOLDEN_DIR = Path(__file__).resolve().parent / "fixtures" / "topology-golden"
_TOPOLOGY_GOLDEN_INACTIVE = "a2a-delegation-gates.role-inactive.md"
_TOPOLOGY_GOLDEN_ACTIVE = "a2a-delegation-gates.role-active.md"
_TOPOLOGY_RULE_REL = Path(".claude") / "rules" / "a2a-delegation-gates.md"
_TOPOLOGY_RULE_SOURCE = _REPO_ROOT / "rules" / "1-generic" / "a2a-delegation-gates.md"

#: The (role state, golden file, expected gate fragment) triples of AC-18.
_TOPOLOGY_GOLDEN_CASES = (
    (False, _TOPOLOGY_GOLDEN_INACTIVE, "Worker → HARD REJECT"),
    (True, _TOPOLOGY_GOLDEN_ACTIVE, "Worker → `orchestrator` → HARD REJECT"),
)


def _topology_project_config(role_active: bool) -> str:
    """Return the minimal single-provider config for one AC-18 role state.

    The orchestrator role flag comes from the ActiveSet's ``roles:`` allowlist,
    so "role inactive" is expressed by a whitelist that omits ``orchestrator``
    (omitting the key entirely renders every gate-enabled role, i.e. the
    active state). The inactive whitelist keeps the security-critical default
    roles so the only byte difference between the two goldens is the A2A role
    gate itself.

    ``AGENT_META_REPO`` is pinned to a neutral slug for the same reason as in
    ``_make_project`` (issue #1037): a derived value would make the fixture
    depend on the cloning remote.
    """
    roles_block = "" if role_active else (
        "roles:\n- developer\n- documenter\n- security-auditor\n- code-reviewer\n"
    )
    return (
        'agent-meta-version: "2.0.0-beta.1"\n'
        "ai-providers:\n- Claude\n"
        "dod-preset: rapid-prototyping\n"
        + roles_block
        + "variables:\n  PROJECT_NAME: matrix\n  PROJECT_PREFIX: mx\n"
        "  AGENT_META_REPO: example/agent-meta\n"
    )


def _normalize_topology_golden(text: str, root: Path) -> str:
    """Normalise a golden render like ``_hash_file`` does (no volatile bytes)."""
    text = text.replace("\r\n", "\n")
    for needle in sorted({str(root), root.as_posix()}, key=len, reverse=True):
        text = text.replace(needle, "<ROOT>")
    return _MODEL_LINE_RE.sub(b"model: <MODEL>", text.encode()).decode()


def render_topology_rule(role_active: bool, root: Path) -> str:
    """Render the real ``a2a-delegation-gates`` rule for one role state.

    Runs a full ``sync.py --init`` against a scratch project and returns the
    rendered Claude rule file (normalised). This is the generator for the
    frozen fixtures and the comparison path of the golden tests -- a golden is
    never hand-edited (``python -c`` import of this module, see
    ``tests/fixtures/topology-golden/README.md``).
    """
    project = Path(root) / ("role-active" if role_active else "role-inactive")
    (project / ".meta-config").mkdir(parents=True)
    (project / ".meta-config" / "project.yaml").write_text(
        _topology_project_config(role_active), encoding="utf-8"
    )
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    result = _run_sync(project, "--init")
    assert result.returncode == 0, (
        f"topology golden sync failed (role_active={role_active})\n"
        f"{result.stdout[-1500:]}\n{result.stderr[-1500:]}"
    )
    rendered = (project / _TOPOLOGY_RULE_REL).read_text(encoding="utf-8")
    return _normalize_topology_golden(rendered, project)


@pytest.mark.parametrize(
    ("role_active", "golden_name", "expected_fragment"), _TOPOLOGY_GOLDEN_CASES
)
def test_topology_golden_key_unset_is_byte_identical(
    role_active, golden_name, expected_fragment, tmp_path
):
    """AC-6/AC-18: with the key unset the A2A rule keeps today's bytes.

    One fixture per role state: role inactive renders ``Worker → HARD
    REJECT``, role active renders ``Worker → `orchestrator` → HARD REJECT``.
    A drift here is a real AC-6 regression, not a rebaseline candidate.
    """
    rendered = render_topology_rule(role_active, tmp_path)
    golden = (_TOPOLOGY_GOLDEN_DIR / golden_name).read_text(encoding="utf-8")
    assert rendered == golden
    assert expected_fragment in rendered
    assert "<ROOT>" not in rendered


def test_topology_goldens_differ_only_in_the_role_gate():
    """The two fixtures are distinct and prove the gate is not vacuous.

    ``test_topology_golden_key_unset_is_byte_identical`` would be green for two
    identical files even if the role flag were ignored; this pair assertion
    pins that exactly the `` → `orchestrator` `` fragment separates them.
    """
    inactive = (_TOPOLOGY_GOLDEN_DIR / _TOPOLOGY_GOLDEN_INACTIVE).read_text(
        encoding="utf-8"
    )
    active = (_TOPOLOGY_GOLDEN_DIR / _TOPOLOGY_GOLDEN_ACTIVE).read_text(
        encoding="utf-8"
    )
    assert inactive != active
    assert active.replace(" → `orchestrator`", "", 1) == inactive
    assert "→ `orchestrator` →" not in inactive


#: Prospective Task 18 branch (design §10, v1 wording without the P3 instance
#: placeholder). It is the *shape* the conditional must have: both markers
#: inline, the ``{{else}}`` branch word-identical to the current source line.
_TOPOLOGY_NEW_GATE_BRANCH = (
    "2. **Orchestrator-Topologie ({{ORCH_TOPOLOGY}}):**\n"
    "   G1 Ein Worker dispatcht NIE einen `orchestrator` — HARD REJECT, bei jedem N.\n"
    "   G2 NUR `main_chat` spawnt **genau einen** Orchestrator pro Session, mit\n"
    "      eindeutiger `orchestrator_id` und disjunktem Scope. Doppelte ID oder\n"
    "      Scope-Überlappung = HARD ERROR beim Spawn (beide Eigentümer nennen).\n"
    "   G3 Ein Orchestrator dispatcht NIE einen Orchestrator — HARD REJECT.\n"
    "   Der Main Chat ist der einzige Aggregator; Instanzen koordinieren sich nicht."
)

#: The four flag combinations of AC-18/IC-4: unset plus one explicit position.
_TOPOLOGY_FLAG_CASES = (
    ("unset", "", False, "derived"),
    ("primary", "primary", True, "project"),
    ("subagent", "subagent", True, "project"),
    ("hybrid", "hybrid", True, "project"),
)


def _topology_gate_line() -> str:
    """The current Gate-2 else-branch source (single source, no copied wording).

    Task 18 wraps the historic line in an inline conditional, so the historic
    wording now lives after ``{{else}}`` on the same logical line. The helper
    extracts exactly that branch and keeps working for an unwrapped source.
    """
    marker = "{{else}}2. **Orchestrator-Singleton:**"
    prefix = "2. **Orchestrator-Singleton:**"
    for line in _TOPOLOGY_RULE_SOURCE.read_text(encoding="utf-8").splitlines():
        if marker in line:
            return line[line.index(prefix):].rsplit("{{/if}}", 1)[0]
        if line.startswith(prefix):
            return line
    raise AssertionError("Gate-2 line not found in the A2A rule source")


def _render_prospective_gate(topology: str, explicit: bool, source: str) -> str:
    """Render the prospective conditional with the real conditional engine.

    Uses the real ``substitute`` + ``strip_inactive_conditional_blocks`` pair
    on the real source wording, so the four flag combinations are exercised
    against the engine rather than against a hand-rolled boolean.
    """
    flags = _topology_flags(topology, explicit=explicit, source=source)
    variables = {**flags, "ROLE_ORCHESTRATOR_ACTIVE": "true"}
    template = (
        "{{#if ORCH_TOPOLOGY_EXPLICIT}}"
        + _TOPOLOGY_NEW_GATE_BRANCH
        + "{{else}}"
        + _topology_gate_line()
        + "{{/if}}"
    )
    substituted = substitute(template, variables, "topology-probe", SyncLog())
    return strip_inactive_conditional_blocks(substituted, variables)


@pytest.mark.parametrize(
    ("case_id", "topology", "explicit", "source"), _TOPOLOGY_FLAG_CASES
)
def test_topology_flag_combinations_pick_exactly_one_gate_branch(
    case_id, topology, explicit, source
):
    """AC-18/IC-4: the four flag combinations select one branch, never both.

    Unset renders the historic else branch (byte-identical to the golden
    active fixture); every explicit combination renders the new topology
    branch. The absent-variable branch semantics themselves are already
    asserted in ``tests/test_orchestrator_topology_conditionals.py``
    (``test_absent_variable_renders_the_else_branch_only``,
    ``test_explicit_true_renders_the_new_branch_only``,
    ``test_explicit_false_renders_the_else_branch_only``) and are not
    duplicated here.
    """
    rendered = _render_prospective_gate(topology, explicit, source)
    if case_id == "unset":
        assert rendered == strip_inactive_conditional_blocks(
            _topology_gate_line(), {"ROLE_ORCHESTRATOR_ACTIVE": "true"}
        )
        assert "Orchestrator-Singleton" in rendered
        assert "Orchestrator-Topologie" not in rendered
        return
    assert rendered.startswith(f"2. **Orchestrator-Topologie ({topology}):**")
    assert "Orchestrator-Singleton" not in rendered
    assert "G1 " in rendered
    assert rendered.count("Orchestrator-Topologie") == 1


def test_topology_flags_are_never_simultaneously_true():
    """AC-18 invariant: the four boolean flags can never all read ``"true"``.

    ``ORCH_TOPOLOGY_EXPLICIT`` is independent of the position triple, but a
    position flag is only true when a valid topology is set, and then exactly
    one of the three is true. An invalid value fails closed to all-false. The
    absent-variable / else-branch render is covered by the existing
    ``tests/test_orchestrator_topology_conditionals.py`` tests named in
    ``test_topology_flag_combinations_pick_exactly_one_gate_branch``.
    """
    four = (
        "ORCH_TOPOLOGY_EXPLICIT",
        "ORCH_TOPOLOGY_PRIMARY",
        "ORCH_TOPOLOGY_SUBAGENT",
        "ORCH_TOPOLOGY_HYBRID",
    )
    position = four[1:]
    for topology in ("", "primary", "subagent", "hybrid", "not-a-topology"):
        for explicit in (False, True):
            flags = _topology_flags(topology, explicit=explicit, source="project")
            assert not all(flags[name] == "true" for name in four)
            assert sum(flags[name] == "true" for name in position) <= 1


if __name__ == "__main__":
    if "--write" not in sys.argv:
        sys.exit("usage: python tests/test_ac01_render_identity.py --write")
    with tempfile.TemporaryDirectory() as td:
        manifest = render_matrix_hashes(Path(td))
    _MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    _MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(manifest)} hashes to {_MANIFEST}")
