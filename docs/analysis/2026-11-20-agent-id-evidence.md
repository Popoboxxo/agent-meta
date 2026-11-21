# Evidence: `agent_id` / `agent_type` in the PreToolUse payload (#1250, #1210)

Status: evidence note, not a design decision. Recorded 2026-11-20 for PR 4.2.
Scope: the strict-mode / sentinel logic of `hooks/1-generic/orchestrator-guard-impl.sh`.

## 1. Why this document exists

Issue #1250 finds that the guard's identity decision rests on one payload field
whose provenance was only asserted in a code comment. The guard discards a
main-thread sentinel when `agent_id` is empty and the provider capability
`hook-agent-id` is `true`, and strict mode blocks the main chat only when
`agent_id` is empty. If the field disappeared, delegation would fail closed
(every subagent treated as main thread); the reverse (a field present but not
harness-set) would weaken the sentinel check. This note records what is
actually established, what is only documented, and what remains unverified.

## 2. Established in this repository

| Claim | Evidence |
|---|---|
| The guard reads `agent_id` from the payload and uses emptiness as the main-thread signal | `hooks/1-generic/orchestrator-guard-impl.sh` (`AGENT_ID` assignment, strict-mode condition `strict=true && -z "$AGENT_ID"`, and the sentinel-discard condition) |
| The capability is config-driven, never a provider-name branch | `config/ai-providers.yaml` capability `hook-agent-id`; `scripts/lib/hooks.py` bakes `{{AGENT_META_HOOK_AGENT_ID}}` via `provider_has_capability(pc, "hook-agent-id")` |
| The Claude provider enables the capability; other providers in the shipped config do not | `config/ai-providers.yaml` Claude `capabilities:` list |
| Missing / non-string / object values fail closed | `hook_json_get` returns `""`; guard blocks an unusable `tool_name` and rejects invalid JSON before any decision |
| Behaviour without `agent_id` is pinned by tests | `tests/test_orchestrator_guard_hook.py`: main-thread strict-mode cases, `test_strict_mode_blocks_write_for_main_thread`, and `tests/test_hook_single_parse.py::test_main_thread_without_agent_id_unchanged` |

## 3. Documented but not independently verified here

- Claude Code's hook documentation lists `agent_id` as a common PreToolUse
  field, "present only when the hook fires inside a subagent call". The repo
  cites `code.claude.com/docs/en/hooks.md`; the raw page was not re-fetched in
  this work. No minimum Claude Code version is established.
- The same documentation lists `agent_type` as a common field, "present when
  the session uses --agent or the hook fires inside a subagent" (via the
  extraction in `docs/analysis/2026-11-11-hook-api-ask-permission.md` §3.5).
  Completeness across all spawn paths and custom agents is not verified.

## 4. What PR 4.2 changes

- `agent_type` is read in the same single parse as the other fields and is
  used ONLY as an attribution cross-check: with the new `hook-role-field`
  capability enabled, a non-empty payload role that contradicts a
  self-declared sentinel is rejected (issue #1210). An empty role falls back
  to the sentinel; the capability defaults to off, and an unsynced source copy
  (literal placeholder) behaves as off.
- The role field never grants authority by itself: the sentinel is still
  required for the git path. Indirection (`eval`, `$(...)`, `xargs`) remains a
  documented convention boundary, not a security boundary.
- The strict-mode `agent_id` decision itself is unchanged; this PR only pins
  it with an explicit regression test.

## 5. Open items (not blockers for this PR)

1. Record the minimum Claude Code version in which `agent_id` / `agent_type`
   are present, once a raw documentation check or a live payload capture is
   available.
2. Verify whether a subagent can influence `agent_type` by spawning a child
   with `subagent_type: git` (issue #1210 §5 point 1). Without that evidence
   the role field is attribution, not authorization.
3. Decide whether providers without a role field should emit a sync warning
   when they use sentinel-granted roles (issue #1210 OQ-9).
