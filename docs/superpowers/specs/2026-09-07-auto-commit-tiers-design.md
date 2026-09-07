# Auto-Commit Tiers (Issue #694) — Design Spec

> Brainstormed 2026-09-07 (Architectural path). Source: GitHub issue #694
> ("feat: Allow all agents to commit via git -- 3-tier commit recommendation
> mode"). This spec resolves the issue's open trigger-semantics/scope
> questions through a literature review of how existing agentic coding
> tools handle version-control checkpointing, plus a multi-round design
> dialogue, before any implementation starts.

## Problem

Today, only the dedicated `git` role may perform git commits — every other
write-capable agent (`developer`, `tester`, `senior-developer`, ...) must
delegate to it, enforced by `orchestrator-guard-impl.sh`'s git-mutation gate
(a self-declared `#agent-meta:agent=git` sentinel is the only recognized
exemption). This has real costs the issue names directly:

- Long-running tasks lose all progress on failure — nothing is committed
  until the agent remembers to delegate at the end.
- No incremental saves between subtasks.
- Context-window pressure pushes an agent to "rush" toward a single final
  commit instead of checkpointing its own progress along the way.

## Literature review (2026-09-07)

Researched how established agentic coding tools handle commit/checkpoint
behavior, and what the broader SWE/DevOps literature says about commit
granularity, before designing this feature — the issue explicitly asked for
this rather than inventing trigger semantics from scratch.

**What real tools do:**

| Tool | Behavior | Trigger | Tiering |
|---|---|---|---|
| Aider | Auto-commits every AI edit, generated message | Per successful edit (file write) | Binary: `--no-auto-commits` disables it entirely, no middle tier |
| Cursor | "Checkpoints" — local snapshots, explicitly not git, not team-visible | Per Composer/agent turn | N/A — checkpoint only, no commit tier |
| Claude Code | Checkpoints (session-scoped, separate from git) + manual git commits | Before each edit and each user prompt; auto-cleaned ~30 days | Two clearly separate systems, not tiers of one |
| SWE-agent / OpenHands / Devin | One commit/PR per completed task, human reviews before merge | Task completion (issue → patch → PR), not per-edit | No tiering — commit once, at the end |

**Checkpoint vs. commit — the clear consensus across all of these tools:**
checkpoints are fast, session-local, non-git snapshots for immediate undo;
commits are the durable, team-visible, reviewable record. No tool surveyed
treats these as tiers of the *same* mechanism. **Design implication:**
`auto_commit` is a real-git-history feature, layered on top of — never
built out of — agent-meta's existing `CheckpointStore` (session JSON +
`.claude/progress/current.md`, issue #682 §6). That system correctly
remains the checkpoint half; auto-commit is a separate, higher-stakes
capability.

**Atomic-commit doctrine** (Conventional Commits ecosystem, atomic-commit
literature): a commit is valid only when it is (a) one logical unit of work
and (b) leaves the tree in a state where tests pass. This is the concrete
definition adopted below for the `task-boundary` trigger's "verified"
qualifier.

**Quantified risk:** AI-assisted commits leak secrets at ~3.2% vs. a 1.5%
human baseline (GitGuardian, *State of Secrets Sprawl 2026*). An unattended
auto-commit path without a mandatory-by-default secret scan is a quantified
risk increase, not a theoretical one — this shaped the `secret_scan` design
below.

Sources: Aider reviews/deep-dives (codegen.com, academy.kspl.tech);
Cursor-checkpoints-vs-git comparisons (kyriakos-michael.medium.com,
vibeanswers.com); Claude Code checkpointing docs (code.claude.com,
explainx.ai); open-source coding agent survey (airesponsibly.substack.com);
Devin/OpenHands/SWE-agent comparison (toolhalla.ai); atomic-commit guidance
(medium.com/@sandrodz, codewithjason.com); GitGuardian secrets-in-AI-commits
data via OECD.AI incident record and Endor Labs.

## Answered design questions

Resolved through a multi-round dialogue (2026-09-07), each option explained
to the user before choosing:

| Question | Decision |
|---|---|
| What triggers a Tier-2 ("auto") commit? | **Multiple, selectable, OR'd together** — not a single fixed rule (see Trigger Types below) |
| Which trigger types exist? | `task-boundary`, `per-edit`, `context-pressure`, `file-count-threshold`, `custom` — all 5 approved |
| Is "custom" a combinable trigger or a separate mode? | **Both**, via one config field: combinable inside `triggers: [...]` (mode `auto`) or exclusive (mode `custom`, disables all built-in triggers) |
| Which roles may commit? | **Capability-derived**: any role whose generic template's frontmatter `tools:` includes `Edit` or `Write` — no manually-maintained allowlist in `project.yaml` |
| Mandatory secret scan before every auto-commit? | **Configurable** (`secret_scan: true` default, can be set `false`) — the user was unsure of the performance cost and wanted the option, not a hard requirement |
| What does Tier 1 ("suggest") do when its trigger fires? | **Non-blocking**: the agent writes a ready-to-use commit-message suggestion into its own output/report; it never pauses execution waiting for confirmation |

## Scope

**In scope:**
- `project.yaml` schema: new `auto_commit` block (mode, triggers, thresholds, custom script, secret-scan toggle)
- Prompt-layer instructions for every `1-generic` role with `Edit`/`Write` tools, gated by a new conditional block, explaining active trigger(s) and the tier's expected behavior
- Hook-layer enforcement extension (`orchestrator-guard-impl.sh`) on the providers that actually run PreToolUse hooks today (`has_hooks: true`: Claude, Gemini, Mammouth, Codex — see `config/ai-providers.yaml`). Note: Codex's `has_hooks: true` is flagged in that file's own comments as "a PATH RESERVATION only... unverified" (a pre-existing P6 item, not introduced by this spec) — if Codex's hook mechanism turns out inert in practice, this design degrades gracefully there to the same prompt-only enforcement the 5 genuinely hookless providers get, not a broken state.
- A generated allowlist artifact so the hook never has to re-derive role/tool capability itself
- Secret-scan gate reusing `scripts/lib/secrets.py::scan_for_secrets()`
- Audit-log coverage for every newly-authorized sentinel (reuses the existing `hook_audit_log_append` mechanism)

**Explicitly out of scope (follow-up, not this spec):**
- Any change to `push`, `tag`, or `branch` management — these remain exclusively the `git` role's responsibility, exactly as the issue itself specifies ("The `#agent-meta:agent=git` sentinel should still be used for the git agent dedicated operations")
- Any change to the destructive-operation gate (force push, reset --hard, etc.) — it continues to block regardless of sentinel, per issue #516
- Building real trigger evaluation logic into the hook itself — the hook only ever checks *authorization* (is this sentinel + role allowed to commit right now), never *judgment* (did tests actually pass, is this really a task boundary) — that stays the calling agent's/orchestrator's responsibility, same as today's git/orchestrator sentinel split
- A UI/Admin-UI control surface for `auto_commit` (natural follow-up once the config key exists, not required to ship the feature)
- Extending this to providers without hooks — for them, `auto_commit` is prompt-only-enforced from day one, same status quo as `orchestrator.strict` already has there today ("has no runtime effect... it's a config value, not an enforced restriction")

## Architecture

### Config schema (`config/project-config.schema.json` + `project.yaml`)

```yaml
auto_commit:
  mode: off | suggest | auto | custom   # default: off — no behavior change unless enabled
  triggers:                             # only consulted when mode: auto; multi-select, OR'd
    - task-boundary                     # subtask complete AND tests green (atomic-commit doctrine)
    - per-edit                          # after every Write/Edit tool call
    - context-pressure                  # before a checkpoint / context-compaction event
    - file-count-threshold              # after N files changed since the last commit
    - custom                            # `custom_script` also gets a vote when combined this way
  file_count_threshold: 5               # only read when file-count-threshold is selected; default 5
  custom_script: null                   # path to a project script; exit 0 = "commit now"
  secret_scan: true                     # default true; set false to skip the scan (user's explicit choice)
```

`mode: custom` is a distinct value from `triggers: [custom]` — when `mode`
is literally `custom`, ALL built-in triggers are ignored and `custom_script`
is the sole decision-maker (full project control, per the user's "both"
answer). When `custom` appears inside `triggers: [...]` under `mode: auto`,
it is one more OR'd condition alongside whichever others are also listed.
One field (`custom_script`) backs both usages — no second code path.

Schema validation (`config/project-config.schema.json`): `mode` is an enum
(`off`/`suggest`/`auto`/`custom`), `triggers` a `uniqueItems` array over a
fixed enum, `file_count_threshold` a positive integer, `custom_script` a
string path, `secret_scan` a boolean. `sync.py --validate` rejects
`triggers` entries when `mode` is not `auto` (ambiguous/dead config) and
rejects a missing `custom_script` when `mode: custom` or `custom` appears
in `triggers`.

### Layer 1 — Prompt instructions (all 9 providers, provider-agnostic by construction)

New snippet `snippets/shared/auto-commit.md` (or a `{{AUTO_COMMIT_BLOCK}}`
built the same way `{{STATUS_TABLE_BLOCK}}` was for issue #678/#682 §5:
loaded once via `_build_snippet_variables()`, referenced with an `{{#if
AUTO_COMMIT_ENABLED}}` guard), added to every `1-generic/<role>.md` whose
frontmatter `tools:` includes `Edit` or `Write`. Content, rendered per the
resolved config:

- States the active mode and trigger(s) in plain language.
- For `suggest`: "when `<trigger>` fires, include a ready-to-use commit
  message in your final report — do not run `git commit` yourself, do not
  pause and wait for confirmation."
- For `auto`/`custom`: "when `<trigger>` fires (and `secret_scan` passes, if
  enabled), commit directly: `git add <files>` then `git commit -m
  \"<type>: <description>\"` prefixed with the sentinel comment line
  `#agent-meta:agent=<your-role-name>` as the first line of the Bash
  command — this is required for the guard hook to authorize the commit on
  hook-capable providers, and is harmless elsewhere."
- Explicitly reiterates the existing boundary: `push`, `tag`, and branch
  management remain the `git` role's job — never attempt them here.

This block is the ENTIRE enforcement mechanism on the 5 providers without
`has_hooks: true` (Opencode, Continue, Copilot, ZCode, KimiCode) — exactly
the same status quo `orchestrator.strict` already has on those providers.
Nothing about this spec makes that worse; it was already true before #694.

### Layer 2 — Hook enforcement (Claude, Gemini, Mammouth, Codex only)

**Generated allowlist artifact** (new, written by `sync.py` during the
per-provider generation stage, alongside the existing `.meta-config/
generated-file-hashes.json` pattern): `.meta-config/auto-commit-allowlist.json`

```json
{
  "version": 1,
  "mode": "auto",
  "eligible_roles": ["developer", "tester", "senior-developer", "documenter", "..."],
  "triggers": ["task-boundary", "context-pressure"],
  "secret_scan": true
}
```

Built by a new function in `scripts/lib/auto_commit.py`
(`resolve_auto_commit_config(config, active_roles, agent_meta_root)`):
for each role in the project's active `roles:` list, call the already-
existing `parse_frontmatter_file()` (`scripts/lib/frontmatter.py`) on its
resolved template path (respecting `2-platform` overrides the same way the
rest of the pipeline already does) and check whether `Edit` or `Write`
appears in the parsed `tools:` list. No new role-capability bookkeeping is
introduced — this reuses frontmatter parsing that sync.py already performs
during generation, just captures the result into a small sidecar file the
hook can cheaply read without re-parsing every template itself.

**Hook change** (`hooks/1-generic/orchestrator-guard-impl.sh`, minor version
bump): the existing sentinel-recognition block currently hardcodes
`git|orchestrator` as the only recognized `_ROLE` values (line ~178-195 in
the current implementation). Extend it: after checking those two literals,
if `_ROLE` is NOT `git`/`orchestrator`, look it up in
`auto-commit-allowlist.json`'s `eligible_roles` (only if that file exists
and `mode != off`) — if found, treat it as authorized ONLY for the
git-mutation gate (never for the strict-mode main-chat exemption, which
stays git/orchestrator-only, and never for the destructive gate, which
already ignores sentinel entirely). Every such elevation is appended to the
existing `.guard-audit.log` via the current `hook_audit_log_append` call —
that call is already role-generic, no change needed there.

This is additive to the existing capability-scoped elevation model from
issue #516 (see `orchestrator-guard-impl.sh` header comment): a third
sentinel *category* (config-driven, not hardcoded) alongside the two
hardcoded ones, with the exact same "exempts ONLY from the mutation gate,
never from the destructive gate" scoping already proven out for `git`.

### Trigger evaluation stays prompt-side

The hook has no way to know whether tests passed or a subtask boundary was
reached — those are semantic facts only the calling agent (or the
orchestrator dispatching it) has. The hook's role is unchanged in kind: it
verifies *authorization* (this sentinel, this role, this project
configuration permit a commit right now), never *judgment* (whether this
moment is actually a valid trigger instant). This mirrors the existing
git/orchestrator split exactly — self-declaration is trusted for identity,
the destructive gate remains an unconditional backstop for the operations
that matter most.

### Secret-scan gate

When `secret_scan: true` (default) and an agent is about to auto-commit,
the prompt instructions direct it to run the project's existing secret
scan against the staged diff before committing — reusing
`scripts/lib/secrets.py::scan_for_secrets()` (already used by
`write_checked()` for every `sync.py`-authored file, per
`config: security.secret-patterns` extension support). A thin CLI wrapper
(`scripts/sync.py --scan-staged` or similar — exact interface decided at
planning time) exposes this to agents without requiring a Python import
inside a Bash instruction block. A finding blocks the commit; the agent
reports it and asks for manual intervention rather than committing anyway.
Setting `secret_scan: false` skips this step entirely — an explicit,
visible opt-out (matches the `allow-committed-secrets` precedent), not a
silent gap.

## Security framing

Per `.claude/rules/branch-guard.md`'s own terminology: `orchestrator-guard.sh`
is a **convention boundary** (fail-closed against accidental misuse, not a
cryptographic identity check against a deliberate bypass) with specific
**security-boundary** carve-outs (the destructive gate, issue #516). This
spec does not change that framing — it EXPANDS who counts as a legitimate,
self-declared committer (config-driven instead of hardcoded to two roles),
while leaving every existing security-boundary property (destructive gate,
audit logging, push/tag/branch exclusivity) completely untouched. The risk
profile shift is bounded to: more roles can now do what `git` could always
do (plain `add`/`commit`), gated by an explicit, project-level opt-in that
defaults to `off`.

## Testing

- Unit tests for `scripts/lib/auto_commit.py::resolve_auto_commit_config()` — role-eligibility derivation from frontmatter `tools:`, schema-shape of the generated allowlist, `mode: custom` vs. `triggers: [custom]` handling.
- `tests/test_orchestrator_guard_hook.py` additions: a role present in the allowlist can commit; a role absent from it still cannot; the destructive gate still blocks regardless; `mode: off` (or a missing allowlist file) behaves identically to today.
- Schema validation tests: `triggers` without `mode: auto` rejected; `mode: custom`/`triggers: [custom]` without `custom_script` rejected.
- A new `tests/scenarios/` entry (per this repo's own convention, `rules/2-platform/agent-meta-conventions.md` → Change Checklist) exercising `auto_commit: {mode: auto, triggers: [task-boundary, context-pressure]}` end to end through `sync.py`.
- Manual/integration check: verify the rendered prompt block on all 9 providers contains no leftover `{{...}}` and correctly omits push/tag/branch language.

## Out of scope / explicit follow-ups

- Admin-UI control surface for `auto_commit`.
- Extending real hook enforcement to the 5 non-hook providers (not
  possible without a harness-side hook mechanism there — tracked as a
  platform limitation, not a gap in this design).
- Telemetry/reporting on how often each trigger type actually fires in
  practice — worth revisiting once this ships and real usage data exists.
