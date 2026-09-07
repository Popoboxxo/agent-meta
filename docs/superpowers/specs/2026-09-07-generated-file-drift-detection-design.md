# Generated-File Drift Detection — Design Spec

> Brainstormed 2026-09-07 (Architectural path). Approved design: warn-only,
> default-on, `.agent-meta-managed`-scoped, separate allowlist file.

## Problem

`sync.py` fully regenerates every file it owns on every run ("generate,
don't store"). If a user (or another tool) hand-edits a generated file
between two syncs, the next sync silently overwrites that edit with no
signal that anything was lost. Two existing mechanisms are each too
narrow to catch this in general:

- `context-hashes.json` (`scripts/lib/context.py`) only guards the static
  header portion of context files (CLAUDE.md/AGENTS.md) for smart
  regeneration — not agents/rules/hooks/commands/skills/pipeline-details.
- `.agent-meta-managed` per-directory index files (`scripts/lib/rule_index.py`)
  track *which* files agent-meta owns (for orphan cleanup) — no content
  hashes, so they cannot detect drift.

## Scope

**In scope:** every file reachable through an `.agent-meta-managed` (or
`-mcp`/`-tools` sidecar) index, across every active provider's
`agents_dir`, `rules_dir`, `hooks_dir` (including its `lib/` and
`release-gates/` nested self-managed subdirectories), `commands_dir`, and
`skills_dir`, plus `pipeline_details_dir`.

**Out of scope (deliberately):**
- Context files (CLAUDE.md/AGENTS.md) — already covered by
  `context-hashes.json`; this feature must not duplicate or conflict with it.
- `.meta-config/*` (project-owned config, secrets templates) — never
  agent-meta-managed content in the drift sense.
- Changing write behavior. This phase is warn-only: a detected edit is
  still overwritten exactly as today. Preserving the edit (skip-overwrite)
  is an explicit non-goal for this phase — a possible v2 follow-up.

## Data model

**`.meta-config/generated-file-hashes.json`** (new, committed — same
shape and directory as the existing `context-hashes.json`):

```json
{
  "version": 1,
  "hashes": {
    ".claude/agents/developer.md": "3f9a1b2c4d5e6f70",
    ".claude/rules/branch-guard.md": "a1b2c3d4e5f60718"
  }
}
```

Keys are paths relative to `project_root`, covering every active
provider's managed files together in one file (not one file per provider —
simpler to reason about, matches `context-hashes.json`'s existing
single-file convention). Values are `content_hash()` (existing helper,
`scripts/lib/io.py`, 16-char SHA-256 prefix) of the file's content —
reused verbatim, no new hash function.

**`.meta-config/drift-allowlist.yaml`** (new, optional — absent means
empty allowlist, no error, matching this repo's fail-soft config-loading
convention):

```yaml
allow-edits:
  - .claude/commands/my-custom-command.md
  - .opencode/rules/*.md
```

Patterns are glob patterns (`fnmatch`-style) matched against the
project-root-relative **deployed** path (the path a file actually lands
at, e.g. `.claude/agents/...` — never the framework source path under
`agents/1-generic/...`). A match fully suppresses the warning for that
path — no residual info-level note.

**`project.yaml` toggle** (new, optional key under a new top-level
`drift-detection` block — default enabled per this design's approval):

```yaml
# drift-detection:
#   enabled: false   # default: true
```

`enabled: false` skips both the early warn-scan and the late
hash-capture entirely. Neither stage touches
`generated-file-hashes.json` while disabled — an existing store is left
exactly as-is (frozen, not deleted, not refreshed) until the feature is
re-enabled, at which point it resumes being read/written normally
(a store frozen across several manual edits may then produce one
retroactive round of findings on re-enable — expected, not a bug).

## Algorithm

Two new pipeline stages in `scripts/lib/sync_pipeline.py`, both driven by
one new module `scripts/lib/generated_file_drift.py` (sibling of
`external_tools_drift.py`, same directory-enumeration idioms reused —
notably the existing pattern in `scan_injection_drift()` for walking
`agents_dir`/`hooks_dir`/`rules_dir`/`commands_dir`/`skills_dir` per
active provider, including its nested-self-managed-subdirectory recursion
for `hooks/lib/` and `hooks/release-gates/`).

**1. Early stage — `scan_generated_file_drift()`** (pure, like
`scan_injection_drift`), inserted **before** `_sync_stage_per_provider`
(the stage that does all the actual overwriting) so it sees pre-overwrite
state:

- Load `.meta-config/generated-file-hashes.json` (fail-soft empty dict if
  absent/malformed) and `.meta-config/drift-allowlist.yaml` (fail-soft
  empty list if absent/malformed).
- For each active provider, for each managed-index entry across its
  agents/rules/hooks(+lib+release-gates)/commands/skills/pipeline-details
  directories: if the file exists on disk AND a stored hash exists for it
  AND `content_hash(current_content) != stored_hash` AND its path doesn't
  match any allowlist pattern → collect a finding
  `{"path": ..., "provider": ...}`.
- A file with NO stored hash yet (first sync ever, or a newly-added
  managed file) is never a finding — nothing to compare against.

**2. Warning emission** — one `log.warning(...)` per finding, format:
`"generated-file-drift: '<path>' was manually edited since the last sync (provider '<provider>') — this sync will overwrite it. Add it to .meta-config/drift-allowlist.yaml if this edit should be preserved going forward."`
No new artifact file is rendered (unlike `external-tools-drift.md`) — the
warning itself, surfaced through the same `SyncLog` every other sync
warning uses, is the complete deliverable for this phase.

**3. Late stage — `capture_generated_file_hashes()`**, inserted at the
very end of the sync pipeline (after every writer has run): re-walks the
same managed-index enumeration against the now-freshly-written on-disk
state, computes `content_hash()` for every entry, and writes the complete
new baseline to `.meta-config/generated-file-hashes.json` in one shot
(mirrors `_save_context_hashes`'s single-write-at-the-end shape — no
per-file incremental I/O against this store).

**`--dry-run` behavior:** the early warn-scan still runs and still warns
(useful — a dry-run is exactly when a user wants to know what would
happen without committing to it); the late hash-capture is skipped (no
writes in dry-run, matching every other writer's contract).

## Testing

New `tests/test_generated_file_drift.py`, mirroring
`tests/test_external_tools_registry.py`'s `scan_injection_drift` test
shapes:
- Flags a managed file whose on-disk content no longer matches its stored
  hash.
- Does not flag a file with no stored hash yet (first sync).
- Does not flag a file whose content is unchanged.
- Allowlist glob match fully suppresses a would-be finding.
- `capture_generated_file_hashes()` produces a hash store that a
  subsequent `scan_generated_file_drift()` call finds no drift against
  (round-trip).
- `drift-detection.enabled: false` in config skips both stages (no
  warnings, no hash-store writes, and — if a store already exists —
  no update to it either, per the "skip entirely" reading of the toggle).

## Follow-ups (explicitly out of scope for this phase)

- Optional skip-overwrite (preserve the edit) instead of warn-and-overwrite.
- Admin-UI surface for reviewing/resolving flagged drift.
- A rendered report file (like `external-tools-drift.md`) in addition to
  the log warning, if warning volume ever becomes hard to track across a
  session.
