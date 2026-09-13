---
spec-id: SPEC-STALE-ROLE-CLEANUP-2026-09-13
title: Stale Role Cleanup — Technical Specification
status: APPROVED
related:
  - docs/specs/2026-09-13-stale-role-cleanup-system-design.md
  - docs/specs/2026-09-13-progress-ledger-system-design.md
  - docs/specs/2026-09-13-progress-paths-config-design.md
---

# Stale Role Cleanup — Technical Specification

> Status: `APPROVED (2026-09-13)` — approved by the user on 2026-09-13; the approval
> was recorded by the `concept-reviewer` role. The documented recommended defaults for
> the open questions were accepted unchanged. This document is a **specification only**:
> it defines interface contracts, data flow and acceptance criteria; it contains
> **no implementation** and no plan.
>
> Trace anchor (carried over **unchanged** from the system design and to be referenced by
> the plan): `spec-id: SPEC-STALE-ROLE-CLEANUP-2026-09-13`.
>
> Authoritative input: `docs/specs/2026-09-13-stale-role-cleanup-system-design.md`.
> All file:line references below were re-verified against the working tree on 2026-09-13
> unless explicitly marked `HYPOTHESIS`.
>
> **Provider-agnostic (MANDATORY).** No new or changed code path branches on a provider
> name literal. Provider differences are expressed exclusively through config keys /
> capability flags (`provider_has_capability`, `config/ai-providers.yaml` capabilities),
> per the `provider-agnostic` rule. The B-I wrapper fix *removes* the only remaining
> provider-literal-driven branch (`provider_has_capability(pc, "external-skill-agent-files")`
> at `scripts/lib/agent_sync.py:896–897`).

### Revision

| Rev | Date | Change | Author |
|---|---|---|---|
| 0.1 | 2026-09-13 | Initial specification: B-I cleanup hardening, B-II Admin-UI remove path, B-III managed-block shrink proof + stale-path closure | concept-specifier |
| 0.2 | 2026-09-13 | Incorporated review findings F-01…F-11 from `docs/specs/2026-09-13-stale-role-cleanup-review.md` (reconciliation branch, complete planner signature, `deleted` derivation, mutation-free preview, prompt-index fail-open, AC disambiguation) | concept-specifier |
| Approval | 2026-09-13 | User approval 2026-09-13 — all recommended defaults accepted | concept-reviewer |

### Revision — incorporated review findings

One row per finding from the review report. `Resolved` = change applied verbatim in this
revision; `Deferred` = intentionally left open with rationale. All findings were re-verified
against the working tree (`agent_sync.py`, `skills.py`, `context.py`, `admin-server.py`,
`rule_index.py`, `admin-ui.html`, tests) before being applied.

| Finding | Severity | Resolution in this revision | Where |
|---|---|---|---|
| F-01 | MAJOR | **Resolved:** new reconciliation/adoption branch for provenance-carrying skill wrappers when the index is readable (`reconcilable(f)`, provenance origin `0-external/`, primary markers only). Residual non-provenance legacy files stay `foreign`. Trade-off documented. | IC-02, IC-04, AC-21, R1/R7 |
| F-02 | MAJOR | **Resolved:** `plan_agent_cleanup` / `_cleanup_stale_agents` gain `provider: str` and `wrapper_filenames: set[str]`; `StaleAgentEntry` gains `adopted`; explicit reason precedence defined. | IC-04, AC-06, AC-22 |
| F-03 | MAJOR | **Resolved:** `deleted` is defined as the stale paths of the server-side recomputed preview used for the fingerprint check; AC-14 made consistent and testable. Residual softness documented. | IC-07, Datenfluss (c), AC-14, R8 |
| F-04 | MAJOR | **Resolved:** preview routed through a side-effect-free planning traversal; `ensure_skill_repo`/`deinit_skill_repo` gated on `not dry_run`; AC-10 amended to assert no filesystem/network mutation. | IC-06, Datenfluss (b), AC-10 |
| F-05 | MAJOR | **Resolved:** `context.py::sync_prompts_for_provider` migrated to the IC-01 helpers (fail-closed bootstrap, always-write index). Provenance asymmetry recorded as OQ-9. | IC-01, IC-08, AC-23, OQ-9 |
| F-06 | MINOR | **Resolved:** AC-02 and AC-04 given distinct fixtures/tests; both no longer reference the same test. | AC-02, AC-04 |
| F-07 | MINOR | **Resolved:** AC-15 wording narrowed to non-index, non-provenance files; explicit index-listed phantom test added; backup-first accepted as the mitigation. | AC-15, AC-21 |
| F-08 | MINOR | **Resolved:** `legacy_unmarked` added to the IC-06 foreign-entry schema and AC-10, gated on OQ-3 approval. | IC-06, AC-10, OQ-3 |
| F-09 | MINOR | **Resolved:** new IC-10 for the `admin-ui.html` cleanup control (element, states, confirm dialog). | IC-10, AC-25 |
| F-10 | MINOR | **Resolved:** AC-24 + plan-gate note enforce B-I before B-II. | IC-07, AC-24 |
| F-11 | INFO | **Resolved:** IC-01 states the `None → list[str]` return change is backward compatible (callers ignore the result). | IC-01 |

---

## Problem / Ziel / Nicht-Ziele

### Problem

The user experience *"I removed a role but the file is still there and I can't get rid of
it"* conflates three distinct sub-symptoms living in different subsystems. They are
specified separately because each has its own failure mode and its own acceptance
criteria.

**B-I — stale role files after sync.** `scripts/lib/agent_sync.py::_cleanup_stale_agents`
(767–815) is the only remover for provider agent directories. Its current safety model is
fail-open and incomplete:

1. The guard at `agent_sync.py:806`
   (`if not managed_index.exists() or existing_file.name in previously_managed`)
   deletes **every** unexpected `*.md`/`*<agent_ext>` when no
   `<agents_dir>/.agent-meta-managed` index exists. This is documented as intended by
   `tests/test_agent_sync_helpers.py::test_no_managed_index_prunes_everything_unexpected`
   (300–315) — therefore any hand-authored role file in a legacy project is destroyed on
   the first sync.
2. The index is written **only** `if not dry_run and expected_filenames`
   (`agent_sync.py:812–815`). After the last role is removed, the index keeps phantom
   entries and the next run still sees a non-empty `previously_managed`.
3. `skills.py` writes `<role>.md` wrappers into **every** provider's `agents_dir`
   (`scripts/lib/skills.py:374–378` directory resolution, `:424` / `:490` target path,
   `:525–527` write, `:427–435` remove-on-inactive), but `agent_sync.py` adds those
   wrapper filenames to `expected_filenames` **only** for providers declaring the
   `external-skill-agent-files` capability (`agent_sync.py:896–897`, collector
   `:751–765`). `config/ai-providers.yaml:35` is the only provider that declares it
   today. For every other provider the wrapper is written but never tracked and never
   swept on deactivation.
   **Legacy residual (F-01):** a wrapper is only removed by `skills.py:427–435` while its
   skill is still present in the registry (active or deactivated). A wrapper whose skill was
   **removed from the registry entirely**, or that was written for a non-Claude provider
   before tracking existed, is *unexpected* and (with a readable index that does not list
   it) classified `foreign` — this is exactly the user's *"the file is still there"*
   complaint. The corrected predicate therefore adds a bounded reconciliation branch (IC-04)
   instead of leaving these files permanent.
4. `*.sync-backup-*` artifacts (`scripts/lib/generated_file_drift.py:109`
   `_SYNC_BACKUP_PATTERN`, writer `:221–269`) are never pruned and are explicitly skipped
   by the managed-file iterators (`:148`, `:162`, `:171`).

**B-II — no Admin-UI removal path.** The UI sync and the CLI sync are the same operation:
`admin-server.py:1139–1141 SyncExecutor.run()` → `_run([])` (`:1076–1106`) shells out to
`python scripts/sync.py` with no flags. Dry run is `--validate` (`:1133–1137`). There is
no role remove/delete endpoint — `_DELETE_PREFIX_ROUTES` (`admin-server.py:3408–3413`)
covers only pipelines, reflection-pairs, backups and environments. Role removal is only
possible indirectly by editing `project.yaml → roles` via the existing PUT path and then
running sync, with no preview, no explicit confirmation and no way to distinguish "will be
removed" from "luckily survived".

**B-III — managed-block shrink proof + stale-path closure.** The user's hypothesis
*"the managed block does not shrink"* is **wrong as stated** and is recorded here
explicitly as corrected:

> **CORRECTED HYPOTHESIS.** The managed block **already shrinks in the normal path**.
> `scripts/lib/context.py::_update_managed_html_block` (347–442) re-renders the entire
> block from the `claude-managed` template and replaces the old block wholesale via
> `managed_pattern.sub(lambda _m: new_managed, existing, count=1)`
> (`context.py:436`, regex at `:372–376`, `re.DOTALL`, non-greedy). When a role hint
> disappears from the template variables, the new block no longer contains it and the old
> text is gone.

The real B-III problem is therefore: **the truth of the shrink is unproven by tests, and
six bypass paths keep stale content alive** (`_regenerate_static_context`, 186–276, which
preserves the existing managed block at `:225`/`:272`, is only the *static* regeneration
path and is subsequently refreshed by `_update_managed_html_block`). The six stale paths
are S1 `context_file.auto_generate: false`; S2 provider deactivated; S3 `--only-variables`
(`context.py:1578–1607`, `sync.py:117–118`); S4 `dry_run`; S5 duplicated/second marker
block (regex non-greedy, `count=1`); S6 injected trailing/foreign content
(`_insert_managed_block_above_foreign_content`, `:445–458`) — the last two are intentional
preservation, not bugs. S1 and S2 are deliberate user opt-outs and must **not** be
overridden.

### User-required scope (binding)

This spec covers exactly the user-required scope, stated explicitly:

1. **Cleanup without destroying user files** — provenance-based, fail-closed delete
   predicate (B-I). A user-authored/foreign file is *never* deleted, backed up or
   rewritten.
2. **An explicit removal path** — preview → confirm → apply, exposed in the Admin-UI
   (B-II), with automatic (now-safe) cleanup retained on the CLI.
3. **Shrink proof** — a regression test proving the managed block shrinks in the normal
   path, plus visibility into the six stale paths (B-III).
4. **Rollback** — every cleanup delete is preceded by a `.sync-backup-<YYYYmmdd-HHMMSS>`
   sibling; generated roles remain re-sync-recoverable.

### Ziel

1. Route all managed-index read/bootstrap/diff/write through one shared helper
   (`scripts/lib/rule_index.py`, generalized), with exactly one implementation of the two
   safety-critical semantics: no-index provenance bootstrap and empty-index write.
2. Replace the fail-open no-index delete with a **provenance-based safety predicate**;
   always write the index, including the empty set. Apply the same two semantics to the
   second fail-open instance in `context.py::sync_prompts_for_provider` (`:1733`/`:1739`).
3. Track external-skill wrapper filenames for **every** provider from the same source of
   truth `skills.py` uses (`_skill_is_active` + skills-registry role names), with no
   capability gate, and additionally **reconcile** already-stale provenance-carrying
   wrappers whose skill left the registry before tracking existed.
4. Write a `.sync-backup-<ts>` sibling before every cleanup delete and prune backup
   siblings under a conservative dual-threshold policy.
5. Add a **pure planner** (`plan_agent_cleanup`) that is the single source of truth for
   both the preview JSON and the real cleanup, so preview == apply by construction.
6. Expose `POST /api/roles/cleanup/preview` and `POST /api/roles/cleanup/apply` on
   `admin-server.py`, plus `--cleanup-preview` on `sync.py`; the Admin endpoint **observes**
   `project.yaml → roles` and never mutates it (the existing PUT path stays the sole config
   writer).
7. Prove the managed-block shrink with a regression test and surface the six stale paths
   as warnings/consistency findings, without overriding S1/S2 user opt-outs.
8. Keep the change provider-agnostic.

### Nicht-Ziele

- No implementation, no plan, no config/schema edit and no template edit in this document.
- No rewrite of the context templating engine and no change to what the managed block
  *contains*.
- No LLM-based recovery of deleted roles; no automatic escalation to the
  `requirements`/SE pipeline; no auto-start of the SE cascade.
- No second writer for `project.yaml → roles` — the cleanup endpoint does not edit config.
- No new authorization model for the Admin routes; the existing server-wide token guard is
  reused.
- The shared `<skills_dir>/.agent-meta-managed` merge-mode multi-writer index is **out of
  scope** except as a reference pattern (per design §3.6).
- No migration/adoption of files generated before provenance markers existed *that carry no
  provenance marker at all* (see OQ-3); they are reported as `foreign` with the
  `legacy_unmarked` flag. Adoption **is** in scope for unexpected files that carry an
  agent-meta provenance marker with a skill-wrapper origin (F-01 reconciliation, IC-04).
- No provenance marker is added to Continue prompt files; the prompt-index fix only removes
  the fail-open delete and always writes the index (OQ-9, IC-08). The prompt-index
  provenance asymmetry is recorded, not silently widened.
- No new external Python dependency; standard library plus existing repo-local helpers only.

---

## Interface Contracts

Symbols are named as `file:Symbol`. Placement of each contract in the target file is
stated so the developer knows where it lands. Signatures are contracts, not
implementations. Python 3.9 compatibility: new typed helpers use `from __future__ import
annotations` and `typing.Optional` where a new module is touched; PEP 604 (`X | Y`) is
preserved only where the surrounding file already uses it.

### IC-01 — Shared manifest / cleanup helper (B-I, B-II, B-III)

Target: `scripts/lib/rule_index.py` (retained module name — design D1/OQ-5 default).
The module already implements `read_managed_index` (21–29), `bootstrap_previously_managed`
(32–68), `cleanup_stale_managed_files` (71–86) and `write_managed_index` (89–101). Change:

```python
from typing import Callable, Optional
from pathlib import Path
from .log import SyncLog

ContentPredicate = Callable[[Path, str], bool]
# (path, file_text) -> True iff the file carries agent-meta provenance.

def read_managed_index(index_path: Path) -> set[str]:
    """Newline-delimited filenames. Empty set if missing. (unchanged, 21–29)"""

def bootstrap_previously_managed(
    target_dir: Path,
    index_path: Path,
    glob_pattern: str,
    content_marker: Optional[str] = None,
    content_predicate: Optional[ContentPredicate] = None,   # NEW
) -> set[str]:
    """Index-first. If the index exists and is readable, return its contents
    (even when empty). If it is absent, adopt only glob matches that pass the
    provenance predicate (or contain content_marker). Never adopts a file that
    carries no provenance. (extends 32–68)"""

def cleanup_stale_managed_files(
    target_dir: Path,
    project_root: Path,
    previously_managed: set[str],
    now_managed: set[str],
    log: SyncLog,
    dry_run: bool,
    reason: str,
    backup: bool = False,            # NEW: write .sync-backup-<ts> before unlink
) -> list[str]:
    """Delete previously_managed - now_managed, sorted. Returns the
    project-relative posix paths of backups written ([] when backup=False or
    dry_run). (extends 71–86)"""

def write_managed_index(index_path: Path, now_managed: set[str], dry_run: bool) -> None:
    """Writes even when now_managed is empty; no-op only for dry_run.
    (unchanged, 89–101 — this is the B-I fix for agent_sync.py:812–815)"""
```

Boundary (design §C1): C1 performs **no** logging policy, no reason strings and no backup
creation beyond the `backup=True` unlink guard — it returns sets/lists; the caller supplies
`reason`, `log`, `dry_run`.

**Backward compatibility (F-11).** `cleanup_stale_managed_files` changes its return type from
`None` to `list[str]`. This is backward compatible: the three existing callers
(`mcp.py:378`, `external_tools.py:336`, `pipelines.py:1109`) ignore the return value, and the
new `list[str]` (backup paths actually written) is additive. No caller may rely on the
absence of a return value; the developer must not add a return-value assertion to existing
call sites.

**Fail-closed bootstrap without a provenance predicate (F-05).** Callers whose files carry no
agent-meta provenance marker yet (e.g. Continue prompt files, IC-08) invoke
`bootstrap_previously_managed` with a predicate that returns `False` for every file (or an
equivalent explicit "adopt nothing" mode) so that an absent index never becomes a
"delete everything unexpected" fallback. IC-01 stays policy-free: the caller chooses between
provenance adoption (agent files) and fail-closed no-adoption (prompt files).

Error paths:

- `read_managed_index` on an unreadable/corrupt index must **not** propagate. The caller
  catches `OSError` / `UnicodeDecodeError`, routes to predicate bootstrap and emits
  `log.warning`. A corrupt index is **never** interpreted as "delete all" (see IC-04).
- `cleanup_stale_managed_files` is fail-soft per file: an individual backup-write or unlink
  `OSError` is logged (`log.warning`) and iteration continues, so one bad file cannot abort
  the sync. A failed backup **prevents** the unlink of that file.
- `bootstrap_previously_managed` with `content_predicate` catches per-file
  `OSError`/`UnicodeDecodeError` and treats that file as non-provenance (never adopted).

Note: `bootstrap_previously_managed` takes a single `glob_pattern: str`. Because the agent
cleanup has up to two patterns (`*.md`, and `*<agent_ext>` when `agent_ext != '.md'`), the
agent caller invokes it once per pattern and unions the results (see IC-04).

### IC-02 — Provenance predicate (B-I)

Target: `scripts/lib/agent_sync.py::_agent_has_provenance` (new module-level function).
Pure, no writes.

```python
def _agent_has_provenance(path: Path, text: str) -> bool:
    """True iff *text* carries an agent-meta generation marker. Recognises, in
    order of preference:
      - YAML frontmatter `generated-from:` (frontmatter.py:244, 278–294)
      - HTML comment `<!-- agent-meta-provenance: ... -->`
        (provider_transform.py:554–561; frontmatter.py:230–238)
      - TOML comment `# generated-from:` (agent_toml.py:75)
      - YAML frontmatter `based-on:` (secondary; 2-platform overrides)
    Never True for a user-authored file. Pure, no writes."""

def _agent_provenance_is_external_skill(path: Path, text: str) -> bool:
    """True iff *text* carries a **primary** provenance marker whose generation
    origin identifies an external-skill wrapper (origin prefix `0-external/`,
    skills.py:500 `generated_from=f"0-external/{skill_name}@{commit}"`).

    This is the bounded reconciliation predicate (F-01): only primary markers
    (frontmatter `generated-from:`, HTML `<!-- agent-meta-provenance: ... -->`,
    TOML `# generated-from:`) qualify; the secondary `based-on:` marker does
    NOT. Pure, no writes; a file with no recognisable external-skill origin
    returns False."""
```

All four marker forms were verified in the working tree. `based-on:` as a *provenance*
signal is secondary — `HYPOTHESIS` on completeness: it appears in generated content only
for providers that do not strip it (design A4). It must not be the **only** accepted
marker for a provider known to strip `generated-from` (those carry
`<!-- agent-meta-provenance: ... -->` instead, per `provider_transform.py:554–561`).
Likewise, `based-on:` must **never** satisfy `_agent_provenance_is_external_skill`
(F-01): reconciliation is restricted to primary markers with an `0-external/` origin so a
provider-stripped or user-emitted `based-on:` line cannot widen the delete surface.

### IC-03 — External-skill expected-filename set, all providers (B-I)

Target: `scripts/lib/agent_sync.py`.

```python
def _collect_active_skill_wrapper_filenames(
    agent_meta_root: Path, config: dict,
) -> set[str]:
    """Filenames of `<role>.md` wrappers skills.py will write this run, derived
    from the SAME source of truth as skills.py: _skill_is_active + the
    skills-registry role names. Provider-independent -> no capability gate.
    Replaces the capability-gated _collect_claude_external_skill_filenames
    (751–765)."""

def _collect_all_registry_wrapper_filenames(
    agent_meta_root: Path,
) -> set[str]:
    """Filenames of `<role>.md` wrappers for every skill in the registry,
    active AND inactive (role default = skill name), independent of
    capability. Used only to classify a stale entry's `reason`
    (IC-04): a tracked stale file whose name is in this set is a deactivated
    skill, not a removed role."""
```

Contract details:

- Source of truth: `load_external_skills_config(agent_meta_root)` (registry `skills:` keys,
  each entry's `role` defaulting to the skill name) filtered by
  `_skill_is_active(skill_name, skill_cfg, project_skills)` — identical to
  `skills.py:389–390` / `:421–422`. It returns `{f"{role}.md"}`.
- `_collect_all_registry_wrapper_filenames` applies the **same** registry traversal without
  the `_skill_is_active` filter, so it also covers wrappers whose skill was deactivated or
  whose `role` was renamed. It is provider-independent and contains no provider literal.
- Both collectors are invoked at the sync call site and serve different purposes (they are
  not merged): the **active** set feeds `expected_filenames`; the **all-registry** set is
  passed to `plan_agent_cleanup` as `wrapper_filenames` (IC-04) for reason precedence (F-02).
- Provider-independent: the return value is a `set[str]` of filenames, not paths, and
  contains no provider literal.
- Call-site change in `sync_agents_for_provider` (851–902): replace the capability gate at
  `:896–897` with an **unconditional** union:
  `expected_filenames |= _collect_active_skill_wrapper_filenames(agent_meta_root, config)`.
  `_cleanup_stale_agents` is still called at `:900`; the pipeline call site
  (`sync_pipeline.py:667–670`) is unchanged.

Consistency with `skills.py`: `skills.py:427–435` already unlinks an inactive wrapper
before the agents cleanup runs, so `now_managed` reflects the post-`skills.py` state.

### IC-04 — Corrected delete predicate and `_cleanup_stale_agents` contract (B-I)

Target: `scripts/lib/agent_sync.py`.

```python
@dataclass(frozen=True)
class StaleAgentEntry:
    provider: str
    path: str        # project-relative posix path
    reason: str      # "role removed from config" | "skill deactivated"
    tracked: bool    # True = index entry, False = provenance-adopted/reconciled
    adopted: bool    # True = admitted by the reconciliation branch (F-01), not the index

def plan_agent_cleanup(
    target_dir: Path,
    expected_filenames: set[str],
    provider: str,                       # NEW (F-02): fills StaleAgentEntry.provider
    wrapper_filenames: set[str],         # NEW (F-02): all registry wrapper filenames
    pc: dict,
    project_root: Path,
) -> list[StaleAgentEntry]:
    """PURE. Returns files that would be deleted. Reads index + files only.
    Single source of truth for the preview and for _cleanup_stale_agents.

    provider: the active provider name (already available in
    sync_agents_for_provider); used only to populate StaleAgentEntry.provider.
    wrapper_filenames: `_collect_all_registry_wrapper_filenames` (IC-03);
    used only for reason precedence. Both are strings/plain data — no provider
    literal is inspected, so the contract stays provider-agnostic."""

def _cleanup_stale_agents(
    target_dir: Path,
    expected_filenames: set[str],
    provider: str,                       # NEW (F-02): forwarded to the planner
    wrapper_filenames: set[str],         # NEW (F-02): forwarded to the planner
    pc: dict,
    project_root: Path,
    dry_run: bool,
    log: SyncLog,
) -> None:
    """Now uses plan_agent_cleanup() + cleanup_stale_managed_files(backup=True)
    + write_managed_index() (called unconditionally, including empty set)."""
```

**Corrected delete predicate (binding).** For a candidate file `f` in `target_dir`, with
`E = expected_filenames` and `is_candidate(f) := f` matches `*.md` or `*<agent_ext>`
(`agent_sync.py:796–802`):

```
previously_managed :=
      read_managed_index(target_dir/".agent-meta-managed")        if index readable
      union over glob patterns of
          bootstrap_previously_managed(..., content_predicate=_agent_has_provenance)
                                                                  if index absent OR unreadable
      # unreadable index: log.warning once, then predicate bootstrap

index_readable := the index file exists AND read_managed_index returned without error

# F-01 reconciliation/adoption branch (index readable only):
reconcilable(f) := index_readable
               AND is_candidate(f)
               AND f.name ∉ E
               AND f.name ∉ previously_managed
               AND _agent_provenance_is_external_skill(f, f.read())

removable(f) := is_candidate(f)
              AND f.name ∉ E
              AND (f.name in previously_managed OR reconcilable(f))

foreign(f)   := is_candidate(f) AND f.name ∉ E AND NOT removable(f)
```

- `foreign(f)` is **never** deleted, never backed up, never rewritten; it is enumerated in
  the preview response (IC-06/IC-07) for transparency.
- **F-01 reconciliation branch (binding).** When the index is readable but does not list an
  unexpected candidate, the candidate is adopted (and thereby removable) **only** when
  `_agent_provenance_is_external_skill` is true: a *primary* provenance marker with an
  `0-external/` generation origin (IC-02). This is what sweeps legacy non-Claude skill
  wrappers and wrappers whose skill was deleted from the registry. It does not apply when
  the index is absent (the provenance bootstrap already covers that case) and it never
  admits `based-on:`-only or marker-less files. Every reconciled delete is still
  backup-first (IC-05). **Trade-off (explicit):** automatic reconciliation directly fixes
  the user's complaint but widens the delete surface to provenance-matching wrappers; a
  hand-authored file that embeds the literal `0-external/` provenance would be swept, which
  the backup sibling makes recoverable. The rejected alternative — document the residual as
  permanent and expose a distinct `legacy_unmarked` preview category with user-approved
  manual removal — is strictly safer but leaves the reported symptom unresolved; it is
  retained only as the fallback for marker-less files (OQ-3).
- **Reason precedence (F-02, binding).** For each removable entry:
  1. `reconcilable(f)` is true → `reason = "skill deactivated"`, `tracked = False`,
     `adopted = True`.
  2. else `f.name ∈ wrapper_filenames` (all-registry wrapper set, IC-03) →
     `reason = "skill deactivated"`, `tracked = True`, `adopted = False`.
  3. else → `reason = "role removed from config"`; `tracked = True` when admitted via the
     index, `False` when admitted via the no-index provenance bootstrap; `adopted = False`.
  Precedence is entry-level (per file), never provider-level.
- DELETE logging order and the sorted iteration remain byte-for-byte equivalent to today
  (`agent_sync.py:804–808`) so the existing `_LogRecorder` expectations keep holding. The
  reason string emitted to the DELETE log stays `"role removed from config"` for the
  existing tests; the finer reason distinction lives in `StaleAgentEntry.reason`/preview.
- `_agent_has_provenance` and `_agent_provenance_is_external_skill` are fail-soft per file:
  an unreadable candidate is treated as non-provenance (never adopted). A failed read during
  reconciliation must never abort the sync.

**Index state matrix (binding, from design §5.2):**

| Index state | `previously_managed` source | Delete behaviour |
|---|---|---|
| Present, readable, non-empty | index contents | Delete `previously_managed - E`, plus `reconcilable` external-skill wrappers (F-01). |
| Present, readable, **empty** | empty set (index wins) | Delete nothing from the index, plus `reconcilable` external-skill wrappers (F-01); marker-less files survive. |
| Present, unreadable/corrupt | predicate bootstrap + `log.warning` | Delete only provenance-carrying files; never "delete all"; reconciliation is not separately applied (bootstrap already admits provenance files). |
| Absent (legacy first run) | predicate bootstrap | Adopt only provenance-carrying files; all other unexpected files survive. |

**No-index bootstrap provenance predicate** = `_agent_has_provenance` (IC-02). This
removes the `not managed_index.exists()` clause at `agent_sync.py:806`.

### IC-05 — Backup prune predicate (B-I)

Target: `scripts/lib/generated_file_drift.py::prune_sync_backups` (placed next to
`_SYNC_BACKUP_PATTERN`, `:109`). `prune_sync_backups` is also called from the sync pipeline
after the drift stage, per managed directory.

```python
def prune_sync_backups(
    target_dir: Path,
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
    max_age_days: int,
    max_per_source: int,
) -> list[str]:
    """Delete `*.sync-backup-*` siblings in target_dir per retention policy.
    NEVER matches non-backup names; NEVER runs in dry_run; never deletes the
    most recent backup of a source. Returns pruned project-relative posix paths."""
```

**Prune predicate (binding):**

- Name match: `fnmatch.fnmatch(name, "*.sync-backup-*")` via `_is_sync_backup_name`
  (`generated_file_drift.py:112–114`). No other name is ever a prune candidate.
- Never runs when `dry_run` is true (returns `[]`, no filesystem mutation).
- Never deletes the most recent backup of a given source. Source identity is derived by
  stripping the trailing `.sync-backup-<YYYYmmdd-HHMMSS>` suffix
  (`generated_file_drift.py:240–255` timestamp/format convention).
- Delete only when **both** thresholds are exceeded: `age > max_age_days` **and** more
  than `max_per_source` newer backups exist for that source. Default policy (recommended,
  OQ-2): `max_per_source = 3`, `max_age_days = 30`.
- A name whose timestamp cannot be parsed is **never** deleted (fail-safe).
- Per-file `OSError` is logged (`log.debug`/`warning`) and iteration continues.

**Backup-on-delete** (the other half of IC-05): when `cleanup_stale_managed_files` is
called with `backup=True`, it writes `<name>.sync-backup-<YYYYmmdd-HHMMSS>` containing the
pre-delete content, using the same timestamp/format as `generated_file_drift.py:221–269`.
One timestamp per invocation. If the backup cannot be written, the corresponding unlink is
skipped (IC-01).

### IC-06 — CLI `--cleanup-preview` contract (B-II)

Target: `scripts/sync.py`.

- New flag `--cleanup-preview` registered next to `--only-variables`
  (`sync.py:117–118`) and dispatched through the `_MODE_HANDLERS` lambda table pattern
  (`sync.py:324–349`).
- Runs the pipeline in **planning-only mode** (`dry_run=True`) with a
  `CleanupPreviewLog(SyncLog)` collector and no writer stages (F-04); `plan_agent_cleanup`
  (IC-04) is the only producer of stale entries.
- Emits **one JSON object on stdout** and writes nothing (no index write, no unlink,
  no backup, no clone, no submodule operation):

```json
{
  "version": 1,
  "generated_at": "2026-09-13T12:00:00Z",
  "providers": [
    {
      "provider": "claude",
      "stale":   [{"path": ".claude/agents/foo.md", "reason": "role removed from config", "tracked": true, "adopted": false}],
      "foreign": [{"path": ".claude/agents/my-own.md", "legacy_unmarked": true}],
      "backups_to_prune": [".claude/agents/bar.md.sync-backup-20260801-101010"]
    }
  ],
  "fingerprint": "sha256:…"
}
```

- `stale[].adopted` is `true` only for F-01 reconciled entries (IC-04); `stale[].tracked`
  distinguishes index entries from provenance-adopted ones. `provider` comes from the
  enclosing array element (IC-04 `StaleAgentEntry.provider`).
- `foreign[].legacy_unmarked` is the OQ-3 flag: `true` for a candidate-extension file that
  carries no provenance marker (or whose provenance is unrecognised), i.e. a likely
  pre-marker generated file awaiting user-approved manual removal. The field is present but
  its **semantics are gated on OQ-3 approval**; if OQ-3 is rejected, the field is either
  omitted or always `false` (see OQ-3). IC-06 and AC-10 are aligned on this.
- Exit code `0` even for a non-empty `stale` list. Exit code `1` only on internal failure.
- `fingerprint` is a stable hash over the canonicalized stale set (provider + path +
  tracked + adopted + reason) so the apply handler can detect TOCTOU drift (IC-07).
- `foreign` is informational: files classified user-authored that will never be touched.
- **Side-effect-free (F-04, binding).** `--cleanup-preview` must not mutate the filesystem or
  touch the network. It executes a **planning-only traversal** that reuses the pure
  computation (`_resolve_sync_targets`, `_should_skip_role`, IC-03 collectors,
  `plan_agent_cleanup`) but calls no writer. In particular
  `skills.ensure_skill_repo` (`skills.py:410–412`) and `skills.deinit_skill_repo` must be
  gated on `not dry_run` at their call sites (they perform `git submodule add`/`git clone`/
  `git submodule deinit` and currently ignore `dry_run` entirely), and `rules.py` /
  `commands.py` / `hooks.py` / context / drift stages that write must be skipped. `--validate`
  is not the preview path: it performs a full sync into a test repo. The preview never writes
  the managed index, never unlinks and never writes a backup.
- The legacy `test_no_managed_index_prunes_everything_unexpected` path must no longer be
  reachable in preview (no fail-open enumeration).

### IC-07 — Admin HTTP routes (B-II)

Target: `scripts/admin-server.py`. Both routes are **POST** and are added to the exact-route
dict `_POST_EXACT_ROUTES` (`admin-server.py:3382–3406`, alongside
`/api/backups/create` at `:3404`). Handlers follow the existing pattern
(`_route_post_sync_run`, `:3722–3723`; `_read_body`, `:3044–3063`; `_send_json`,
`:3014–3025`). Admin authentication is the existing server-wide token guard; no per-route
role model is introduced. Handler names (new):

- `_route_post_roles_cleanup_preview` → `"/api/roles/cleanup/preview"`
- `_route_post_roles_cleanup_apply` → `"/api/roles/cleanup/apply"`

`SyncExecutor` (`admin-server.py:1064–1141`) gains:

```python
def cleanup_preview(self) -> dict:
    """Run `python scripts/sync.py --cleanup-preview` and parse the single JSON
    object on stdout into a dict. Failures return
    {"success": False, "error": "sync_preview_failed", "output": "…"}."""
```

`SyncExecutor.run()` (`:1139–1141`) is reused unchanged for apply.

**`POST /api/roles/cleanup/preview`**

Request: empty body or `{}` (`_read_body()` may return `None`).

Response `200`:
```json
{ "success": true, "stale": [ { "provider": "claude", "path": ".claude/agents/foo.md",
    "reason": "role removed from config", "tracked": true, "adopted": false } ],
  "foreign": [ { "provider": "claude", "path": ".claude/agents/my-own.md",
    "legacy_unmarked": true } ],
  "fingerprint": "sha256:…" }
```

Errors: `500` with `{"success": false, "error": "sync_preview_failed"}` when the preview
subprocess fails or stdout is not valid JSON. Read-only — never mutates the repo, writes
no index, creates no backup (F-04: the subprocess is the IC-06 planning-only mode, not
`--validate`).

**`POST /api/roles/cleanup/apply`**

Request:
```json
{ "confirm": true, "fingerprint": "sha256:…" }
```

Response `200`:
```json
{ "success": true, "returncode": 0, "output": "<sync stdout>", "deleted": [ ".claude/agents/foo.md" ] }
```

Status codes and error paths (binding):

| Code | Body | Condition |
|---|---|---|
| 200 | success payload | Sync completed (`returncode == 0`). |
| 400 | `{"error":"confirmation_required"}` | `confirm` is not exactly `true`. |
| 409 | `{"error":"preview_stale","stale":[…]}` | Supplied `fingerprint` differs from a freshly recomputed preview (TOCTOU guard). |
| 500 | `{"error":"sync_failed","output":"…"}` | `sync.py` exit != 0 / timeout (timeout is the existing 300 s, `admin-server.py:1092`). |

The apply handler **recomputes the preview server-side** via `cleanup_preview()` and
compares the fingerprint before invoking `SyncExecutor.run()`. The endpoint does **not**
mutate `project.yaml` (design D6); role membership stays owned by the existing PUT path.

**`deleted:[…]` derivation (F-03, binding).** `SyncExecutor.run()` returns only
`{success, output, returncode, command}` (`admin-server.py:1076–1106`) and carries no deletion
list, so `deleted` is **not** parsed from stdout. It is defined as the ordered
`path` values of the `stale` entries in the **same server-side recomputed preview** that
produced the fingerprint used for the 409 comparison (i.e. the second `cleanup_preview()`
call made immediately before `run()`). Concretely:

```
recomputed := cleanup_preview()                 # used for the fingerprint check
if recomputed.fingerprint != request.fingerprint: -> 409
result := SyncExecutor.run()
deleted := [e.path for e in recomputed.stale]   # the intended deletion set
```

Consequences (documented, not asserted):
- `deleted` is the set of files the real sync is *expected* to remove under the same
  preview input; a divergence between recompute and `run()` (e.g. a concurrent config edit in
  the sub-second window, or a per-file unlink failure) is not reflected in `deleted`. This is
  a deliberate trade-off: it avoids changing `SyncExecutor.run()`'s return contract and avoids
  parsing a human-readable stdout. The rejected alternative — a machine-readable sync summary
  (e.g. a `--json-summary` flag) from which `deleted` is parsed exactly — is strictly more
  accurate but expands the `sync.py` output contract; it is recorded as R8.
- A partial failure still returns `500 sync_failed` and no `deleted` claim, because
  `deleted` is only emitted on `returncode == 0`.
- AC-14 asserts `deleted` equals the recomputed preview's stale paths (mockable and exact).

**Ordering constraint (F-10, binding):** B-I must ship before B-II. A bare `sync.py` is only
safe to trigger from the UI once the no-index fail-open delete (`agent_sync.py:806`) is
removed. This is enforced by AC-24 (static guard) and must be reflected in the plan's task
ordering (B-I tasks precede the B-II route/UI tasks).

### IC-08 — Multi-writer `.agent-meta-managed` ownership rule (B-I-adjacent)

The index format (UTF-8, newline-delimited **filenames**, no paths, sorted, trailing
newline when non-empty) and the empty state (file exists, 0 bytes = "agent-meta manages
nothing here") are unchanged. Ownership rule:

| Index | Owner | Rule |
|---|---|---|
| `<agents_dir>/.agent-meta-managed` | `agent_sync.py` (single writer) | Must also list skill-wrapper filenames. `skills.py` writes the wrapper file but **never** this index (no second writer). |
| `<rules_dir>/.agent-meta-managed` | `rules.py` | Own index; out of scope for the required change, alignment recommended (OQ-4). |
| `<commands_dir>/.agent-meta-managed` | `commands.py` | Own index; index key configurable (`commands_managed_index`, `commands.py:151`). Out of scope (OQ-4). |
| `<hooks_dir>/.agent-meta-managed` | `hooks.py` | Own index; already writes even when empty (533–549). |
| `<prompts_dir>/.agent-meta-managed` | `context.py::sync_prompts_for_provider` | Own index. **In scope (F-05):** migrate the identical fail-open delete (`context.py:1733`) and conditional write (`:1739`) to IC-01 with a fail-closed bootstrap (no provenance marker exists on prompt files — adopt nothing on absent index) and an unconditional index write. |
| `<skills_dir>/.agent-meta-managed` | merge-mode multi-writer: `rules.py`, `mcp.py`, `external_tools.py`, `skills.py` | Genuine shared index handled by skill-channel merge logic (`sync_pipeline.py:534–568`). **Out of scope** except as reference pattern. |

**Consistency rule:** every writer of its own `.agent-meta-managed` must (a) write the index
**unconditionally** after cleanup (including empty) and (b) route read/diff/write through
IC-01. Today `rules.py:521–522` and `commands.py:207–208` write only `if now_managed`,
which strands stale index entries; aligning them is recommended but its breadth is OQ-4.

**F-05 migration (binding for the prompt index).** `sync_prompts_for_provider`
(`context.py:1723–1740`) has the byte-identical fail-open pattern: delete every unexpected
`*.md` when no index exists (`:1733`) and write the index only `if expected` (`:1739`). It is
migrated in this change: `previously_managed` via IC-01 `bootstrap_previously_managed` with a
**fail-closed** predicate (prompt files carry no agent-meta provenance marker), the delete via
IC-01 `cleanup_stale_managed_files`, and the index via IC-01 `write_managed_index`
(unconditionally). Because prompt files have no marker, no reconciliation branch applies here;
a pre-existing prompt file that is not in a present index survives. The absence of a prompt
provenance marker is recorded as OQ-9.

### IC-09 — `context.py` managed-block contract (B-III only)

Target: `scripts/lib/context.py`. Only the parts B-III needs are contracted here; the
templating engine is not rewritten (Nicht-Ziele).

- **Normal-path shrink (unchanged, proven):** `_update_managed_html_block` (347–442)
  re-renders the whole block and replaces the first match via
  `managed_pattern.sub(lambda _m: new_managed, existing, count=1)` (`:436`). This
  wholesale-replacement behaviour must not be altered. The regex at `:372–376` remains
  `re.DOTALL` non-greedy with `count=1`.
- **Duplicate marker block (S5):** when the file contains more than one
  `managed-begin … managed-end` pair, only the first is replaced. Required: emit a
  `log.warning` and a consistency finding; keep replacing only the first block so the file
  is never corrupted. The write-vs-refuse escalation is OQ-6; visibility is
  non-negotiable.
- **Static regeneration (S1-adjacent):** `_regenerate_static_context` (186–276) preserves
  the existing managed block (`:225`, `:272`) and must continue to; the subsequent
  `_update_managed_html_block` is what shrinks it.
- **User opt-outs (S1/S2):** `context_file.auto_generate: false`
  (`sync_pipeline.py:250–265`, `:300–304`, `:355–358`) and provider deactivation
  (`sync_pipeline.py:339–341`, `:601–602`) must **not** be overridden; the change only
  makes the skip visible (OQ-7).
- **`--only-variables` (S3):** `context.py:1578–1607` / `sync.py:117–118` only substitute
  placeholders and do not re-render the managed block — required: emit a visible warning
  that the managed block was not refreshed.
- **`dry_run` (S4):** no write — expected; surfaced only as "did not shrink" in status.

A module-level duplicate-marker helper may be added near `_MANAGED_BLOCK_RE`
(`context.py:30–33`); the existing copies at `:372–376`, `:577–580`, `:659–662` are
`HYPOTHESIS`-verified ranges (design §1.3 note) and must not be refactored beyond what the
duplicate-marker check needs.

### IC-10 — Admin-UI cleanup control (B-II, F-09)

Target: `docs/ui/admin-ui.html`, inside the existing sync view that already renders the
`btn-row` of `runBtn` / `dryBtn` / `standaloneBtn` (`admin-ui.html:5113–5117`) and uses
`api.post(...)`, `toast(...)`, `setSyncButtonsDisabled(...)` and the shared confirm modal
(`el("button", { class: "btn btn-danger", onclick: ... })`, `:828`).

**Control contract (not markup styling):**

- A `Preview cleanup` button (`class: "btn"`, sibling of `dryBtn`) added to the sync
  `btn-row`;
- A results panel listing the preview `stale` entries (`provider`, `path`, `reason`,
  `adopted`) and the `foreign` entries (`path`, `legacy_unmarked`, read-only/informational);
- A single `Remove N stale file(s)` danger button, disabled while `N == 0`;
- States: `idle` → `previewing` (all sync buttons disabled via `setSyncButtonsDisabled`) →
  `preview-shown` (stale/foreign rendered, danger button enabled iff `N > 0`) → `applying`
  (buttons disabled) → `done`/`error`. `previewing`/`applying` are the only disabled states,
  so a `409` never leaves the UI wedged.

**Behaviour (binding):**

1. Click `Preview cleanup` → `POST /api/roles/cleanup/preview` with an empty body; on
   `200` render `stale`/`foreign` and store the returned `fingerprint`; on `500` show the
   error via `toast` and render an empty panel.
2. Click `Remove N …` → open the existing confirm modal; on confirm
   `POST /api/roles/cleanup/apply` with `{ confirm: true, fingerprint }`.
3. On `200` re-render from the response, toast success, and refresh the sync status
   (`loadStatus()`); the `deleted` list (IC-07) may be displayed.
4. On `409 preview_stale` discard the stored fingerprint, re-render the preview from the
   returned `stale` list (a fresh preview is required before retrying) and toast a warning.
5. On `400 confirmation_required` / `500 sync_failed` show the error; never mark the files
   as removed.
6. The control never edits `project.yaml → roles`; role membership stays owned by the
   existing PUT path (design D6). UI styling/design-system details are out of scope; the
   contract covers element roles, states and the preview→confirm→apply ordering only.

---

## Datenfluss

### (a) CLI sync cleanup (B-I)

```
sync.py (no flags / --cleanup-preview runs this with dry_run=True)
  -> per active provider
    -> build expected_filenames from overrides (_should_skip_role, agent_sync.py:503–531)
    -> expected_filenames |= _collect_active_skill_wrapper_filenames(...)   # unconditional
    -> wrapper_filenames := _collect_all_registry_wrapper_filenames(...)    # reason only
    -> plan_agent_cleanup(..., provider, wrapper_filenames, ...)  # PURE: index + provenance diff
         -> previously_managed: index if readable, else provenance bootstrap
         -> reconcilable(f): provenance-origin 0-external/ wrapper, index readable (F-01)
         -> foreign files never enter the stale set
    -> if dry_run:      log DELETE only, write nothing, no backup
       else:            backup .sync-backup-<ts>  (per stale file)
                        unlink stale files
                        write_managed_index(...)   # ALWAYS, including empty set
                        prune_sync_backups(...)    # dual-threshold, never the newest
```

### (b) UI read-only preview (B-II)

```
admin-ui.html
  -> POST /api/roles/cleanup/preview   (empty body)
    -> SyncExecutor.cleanup_preview()  (admin-server.py)
      -> subprocess: python scripts/sync.py --cleanup-preview
         -> planning-only traversal: plan_agent_cleanup only;
            no index write, no unlink, no backup, no clone/submodule (F-04)
         <- single JSON {providers:[{stale,foreign,backups_to_prune}], fingerprint}
      <- parsed dict
    <- 200 {success, stale:[...], foreign:[...], fingerprint}
  (on subprocess/JSON failure -> 500 {success:false, error:"sync_preview_failed"})
```

### (c) UI confirm/apply (B-II, with backup)

```
admin-ui.html
  -> POST /api/roles/cleanup/apply {confirm:true, fingerprint}
    -> SyncExecutor.cleanup_preview()          # recompute server-side (also yields `deleted`)
    -> compare fingerprint with request
       mismatch -> 409 {error:"preview_stale", stale:[...]}
       confirm != true -> 400 {error:"confirmation_required"}   # checked first
       ok -> SyncExecutor.run()                # bare sync.py (IC-07)
             -> real run: backup -> unlink -> always-write index -> prune
             returncode == 0 -> 200 {success, returncode, output,
                                      deleted:[stale paths of the recomputed preview]}
             returncode != 0 / timeout -> 500 {error:"sync_failed", output}   # no `deleted`
```

Ordering constraint: **(a) must ship and be verified before (c) is exposed** (IC-07).

---

## Acceptance Criteria

Each AC is numbered, testable and maps to at least one interface contract. Test file names
are mandatory: extend `tests/test_agent_sync_helpers.py` for B-I, add
`tests/test_admin_cleanup_endpoint.py` for B-II, add
`tests/test_context_managed_block_shrink.py` for B-III.

**B-I — cleanup safety**

- **AC-01** (IC-01, IC-04) Given an agent dir with a readable non-empty
  `.agent-meta-managed` index listing `developer.md, stale-old.md` and a
  `untracked-x.md` present, when `_cleanup_stale_agents` runs with
  `expected_filenames={"developer.md"}`, then `stale-old.md` is deleted, `untracked-x.md`
  survives, the DELETE log order is exactly `["agents/stale-old.md"]` and the index becomes
  `"developer.md\n"`. *Extend `test_stale_managed_file_deleted_and_index_rewritten`.*
- **AC-02** (IC-04) Given a readable **non-empty** index listing `developer.md` and
  `expected_filenames == {"developer.md"}`, when cleanup runs (non-dry-run), then nothing is
  deleted and the index is rewritten to exactly `"developer.md\n"`. *New test
  `test_index_rewritten_when_expected_equals_previous`; distinct from AC-04's empty case.*
- **AC-03** (IC-02, IC-04) Given **no** index and an unexpected file with **no** provenance
  marker, when cleanup runs, then the file survives; given an unexpected file **with** an
  agent-meta provenance marker and absent from `expected_filenames`, then it is deleted and
  logged. *Rewrite `test_no_managed_index_prunes_everything_unexpected` →
  `test_no_managed_index_prunes_only_provenance_files`.*
- **AC-04** (IC-01, IC-04) Given `expected_filenames == set()` and a non-dry-run, when
  cleanup runs, then the index file is (re)written to **0 bytes** (and any previously
  index-listed file is deleted). *Replace `test_empty_expected_filenames_never_rewrites_index`
  with `test_empty_expected_filenames_writes_empty_index`.*
- **AC-05** (IC-01, IC-04) Given a corrupt/unreadable index file, when cleanup runs, then
  a `log.warning` is emitted, only provenance-carrying unexpected files are deleted, and no
  non-provenance file is deleted. *New test in `tests/test_agent_sync_helpers.py`.*
- **AC-06** (IC-03) Given a provider whose config does **not** declare the
  `external-skill-agent-files` capability and an active external skill with `role: foo`,
  when `sync_agents_for_provider` runs, then `foo.md` is in `expected_filenames` and a
  stale `bar.md` wrapper (previously listed in the index) is swept with
  `provider == "<that provider>"` and `reason == "skill deactivated"` in
  `plan_agent_cleanup`'s output. *New test in `tests/test_agent_sync_helpers.py`;
  parameterised over at least one non-Claude provider (covers F-02 provider/reason).*
- **AC-07** (IC-03) Given a skill present in `expected_filenames` in a prior run and then
  deactivated, when the next sync runs, then the wrapper is deleted (either by
  `skills.py:427–435` or by the agents cleanup as a tracked stale entry) and the agents
  index no longer lists it. *New test in `tests/test_agent_sync_helpers.py`.*
- **AC-08** (IC-05) Given a non-dry-run cleanup that deletes `x.md`, then a
  `x.md.sync-backup-<YYYYmmdd-HHMMSS>` sibling exists with the pre-delete content, and in
  `dry_run` no backup is written but the would-be backup path is reported. *New test.*
- **AC-09** (IC-05) Given backup siblings for one source, when `prune_sync_backups` runs,
  then: no file is pruned in `dry_run`; the most recent backup is never pruned; deletion
  occurs only when `age > max_age_days` **and** `> max_per_source` newer backups exist;
  a non-backup name is never pruned; an unparsable-timestamp name is never pruned. *New
  test in `tests/test_generated_file_drift.py` or a dedicated helper test.*
- **AC-10** (IC-06) Given `--cleanup-preview` on a fixture with stale and foreign files,
  then exactly one JSON object is emitted on stdout, the process performs **no filesystem or
  network mutation** — no index write, no unlink, no backup, and no `git clone`/`git
  submodule add` even when a referenced skill repo is absent (F-04) — and a stale list
  `[{"path","reason","tracked","adopted"}...]` plus `foreign` (each with
  `legacy_unmarked`) plus a `fingerprint` are present. The test must include a fixture where
  `ensure_skill_repo` would otherwise clone/submodule-add, and assert no subprocess/git
  mutation occurred. *New CLI test.*

**B-II — Admin removal path**

- **AC-11** (IC-07) Given a mocked `SyncExecutor.cleanup_preview()` returning a payload,
  when `POST /api/roles/cleanup/preview` is called with an empty body, then the response is
  `200 {success:true, stale, foreign, fingerprint}` and no write occurs.
- **AC-12** (IC-07) Given `{"confirm": false}` (or a missing `confirm`), when
  `POST /api/roles/cleanup/apply` is called, then the response is
  `400 {"error":"confirmation_required"}` and `SyncExecutor.run()` is **not** invoked.
- **AC-13** (IC-07) Given a request `{"confirm": true, "fingerprint": "<stale>"}` whose
  fingerprint differs from a freshly recomputed preview, then the response is
  `409 {"error":"preview_stale","stale":[…]}` and `run()` is **not** invoked.
- **AC-14** (IC-07) Given `{"confirm": true, "fingerprint": "<current>"}`, a mocked
  `cleanup_preview()` whose recomputed preview has `stale == [p1, p2]`, and a successful
  `run()` (`returncode 0`), then the response is `200 {success, returncode, output, deleted}`
  with `deleted == [p1.path, p2.path]` (the recomputed preview's stale paths, F-03); given
  `returncode != 0` or a timeout, then it is `500 {"error":"sync_failed","output"}` and the
  response contains no `deleted` key.
- **AC-15 (SAFETY, explicit + rollback)** (IC-04, IC-07) In all three flows (CLI cleanup,
  UI preview, UI apply) a candidate file that is **not** listed in a readable
  `.agent-meta-managed` index **and** does **not** carry an agent-meta provenance marker is
  **never** deleted, **never** backed up and **never** rewritten; it is reported in
  `foreign` (with `legacy_unmarked`). This narrows the invariant to the actual trust anchors
  (index membership or provenance), because an index-listed name is by definition
  previously-managed and *is* deletable even if its marker was subsequently stripped —
  that case is covered by the backup-first rollback (AC-19) and asserted separately by
  AC-21's index-listed test. A positive test proves the invariant and a negative test proves
  that removing the provenance marker (for a non-index file) prevents deletion. *Extend
  `tests/test_agent_sync_helpers.py`; mirror in `tests/test_admin_cleanup_endpoint.py`.*

All B-II ACs (AC-11..AC-14 plus the AC-15 mirror and AC-25's UI-control test) live in the
new `tests/test_admin_cleanup_endpoint.py`, following the `importlib` module-load pattern of
`tests/test_admin_server.py:38–48`.

**B-III — managed-block shrink proof + stale-path closure**

- **AC-16** (IC-09) Given a context file whose managed block contains role hint `A`, when
  `_update_managed_html_block` runs with `variables` no longer containing `A` and instead
  containing `B`, then the resulting file's managed block no longer contains `A` and does
  contain `B`, and the surrounding foreign/user content is byte-identical. *New test
  `tests/test_context_managed_block_shrink.py`.*
- **AC-17** (IC-09) Given a file with two `managed-begin … managed-end` pairs, when
  `_update_managed_html_block` runs, then only the first pair is replaced, the second pair
  is preserved, the file remains parseable, and a `log.warning` / consistency finding is
  emitted. *New test.*
- **AC-18** (IC-09) Given S1 (`auto_generate: false`) or S2 (provider deactivated), when a
  sync runs, then no write occurs to the context file and a visible warning/consistency
  finding records that the managed block was not refreshed. Given S3 (`--only-variables`),
  then a warning is emitted that the managed block was not re-rendered. *New tests.*

**Cross-cutting**

- **AC-19 (rollback)** (IC-05, IC-07) Given a file deleted by cleanup, then renaming its
  `.sync-backup-<ts>` sibling back restores the exact pre-delete content; given a
  generated role file deleted by mistake, then re-adding the role to `project.yaml → roles`
  and re-running sync restores it deterministically. *New test.*
- **AC-20 (provider-agnostic)** (all ICs) A static scan over the changed/new code finds no
  `if provider ==` literal and no new provider-name branch; provider behaviour is driven
  only by config keys/capability flags. *Extend the existing provider-agnostic static
  check, or add a focused test.*
- **AC-21 (F-01 reconciliation + F-07 index-list case)** (IC-02, IC-04) Given a readable
  index that does **not** list `legacy-wrapper.md`, and `legacy-wrapper.md` carries a
  primary provenance marker with an `0-external/` origin, when cleanup runs, then the file
  is adopted (`adopted == true`, `reason == "skill deactivated"`), deleted after a
  `.sync-backup-*` sibling is written, and the index is unchanged. Conversely a same-named
  file with no marker, or with only a `based-on:` marker, is `foreign` and survives.
  Separately, an index-listed `phantom.md` (no marker, content later authored by the user)
  **is deleted**, proving the trust-the-index behavior, and its backup sibling restores the
  exact content. *New tests in `tests/test_agent_sync_helpers.py`.*
- **AC-22 (F-02 reason precedence)** (IC-03, IC-04) Given one stale index-tracked file whose
  name is in `_collect_all_registry_wrapper_filenames` and one stale index-tracked file
  whose name is not, when `plan_agent_cleanup` runs, then the former has
  `reason == "skill deactivated"` and the latter `reason == "role removed from config"`,
  both with `provider == <active provider>` and `adopted == false`. *New test asserting the
  precedence order of IC-04.*
- **AC-23 (F-05 prompt index)** (IC-01, IC-08) Given a Continue prompts dir with **no**
  `.agent-meta-managed` index and an unexpected `orphan.md` lacking a provenance marker,
  when `sync_prompts_for_provider` runs, then `orphan.md` survives (no fail-open) and the
  index is written; given `expected == set()` and a non-dry-run, then the index becomes
  0 bytes; given a present index listing `stale.md`, then `stale.md` is deleted and the
  index rewritten. *New test.*
- **AC-24 (F-10 ordering guard)** (IC-07) A static test asserts the fail-open clause
  `not managed_index.exists() or` no longer appears in `agent_sync.py` (and the equivalent
  clause is gone from `context.py::sync_prompts_for_provider`), and the plan must sequence
  the B-I tasks before the B-II route/UI tasks. *New static guard test; the plan-gate note
  is part of the plan, not this spec.*
- **AC-25 (F-09 UI control)** (IC-10) A DOM-level test (or a source assertion where no DOM
  harness exists) verifies: the `Preview cleanup` button exists in the sync `btn-row`; a
  preview `200` renders stale/foreign and enables `Remove N …` iff `N > 0`; confirm posts
  `{confirm:true, fingerprint}`; a `409` re-renders from the returned `stale` list without
  wedging the controls; `400`/`500` never mark files as removed. *New test in
  `tests/test_admin_cleanup_endpoint.py` (source/DOM pattern of the existing UI tests).*

---

## Offene Fragen + Risiken

Each open question is carried over verbatim from the system design §9 with its recommended
default; `NEEDS USER APPROVAL` marks the decisions the user must confirm before
implementation starts.

- **OQ-1 — Apply semantics: automatic cleanup on every sync, or preview+confirm only in
  the UI?** Recommended default: CLI sync keeps cleaning automatically (current behaviour,
  now safe); the Admin-UI always requires preview → confirm. Rationale: the B-I safety model
  makes automatic cleanup safe and forcing confirmation on every CLI run would break
  automation. **NEEDS USER APPROVAL** (it governs whether AC-01..AC-10 are automatic on
  every sync).
- **OQ-2 — Backup prune policy.** Recommended default: enabled, `max_per_source = 3`,
  `max_age_days = 30`, both required; alternative: never prune. **NEEDS USER APPROVAL**
  (determines whether `.sync-backup-*` growth is bounded; AC-09 asserts the default).
- **OQ-3 — Files generated before provenance markers existed.** Recommended default:
  classify as `foreign` (never delete) and surface them in the preview with a distinct
  `legacy_unmarked` flag, letting the user delete manually. Alternative: a one-time
  adoption migration (data-loss risk, not recommended). **NEEDS USER APPROVAL** on whether
  the `legacy_unmarked` flag is required. Scope note (F-01): this question now applies
  **only to marker-less files**; a pre-existing file that still carries a primary
  provenance marker with an `0-external/` origin is auto-reconciled (IC-04) and is not part
  of OQ-3. The flag is already wired into IC-06/AC-10 so approval does not require a schema
  change.
- **OQ-4 — Scope of index-write alignment in `rules.py` / `commands.py`.** Recommended
  default: fix `agent_sync` in this change (required) and align `rules.py:521–522` /
  `commands.py:207–208` to always-write as a closely-coupled follow-up in the same spec,
  because it is the exact same stale-index bug. Alternative: defer to a separate spec to
  keep the blast radius minimal. **NEEDS USER APPROVAL** (scope decision; IC-08 states the
  rule, AC-01..AC-05 test only the `agent_sync` instance unless approved otherwise).
- **OQ-5 — Module shape of the shared helper.** Recommended default: extend
  `rule_index.py` in place (minimal, reversible); alternative: extract a dedicated
  `managed_index.py` and make `rule_index` a thin re-export shim. IC-01 follows the
  default; OQ-4's breadth influences this. **NEEDS USER APPROVAL** only if the extraction
  alternative is preferred.
- **OQ-6 — Duplicate managed-block marker handling.** Recommended default: `log.warning`
  and keep replacing only the first block (no corruption), plus a consistency check.
  Alternative: fail the context update and require manual repair. AC-17 asserts the
  default; preview/consistency visibility is non-negotiable, the write-vs-refuse choice is
  the open part. **NEEDS USER APPROVAL**.
- **OQ-7 — Stale-path visibility (S1–S4).** Recommended default: emit consistency
  warnings only; never override `context_file.auto_generate: false` (S1) or provider
  deactivation (S2), because those are deliberate user opt-outs. Alternative: a
  `--force-context` escape hatch for a one-off refresh. **NEEDS USER APPROVAL** on the
  scope of the visibility work (whole bypass list vs S1/S5 only) and on the escape hatch.
- **OQ-8 — Backup before apply in the UI.** Recommended default: offer but do not force a
  provider backup before a confirmed cleanup. Alternative: require it. **NEEDS USER
  APPROVAL** (UI friction vs safety).
- **OQ-9 — Prompt-file provenance asymmetry (F-05).** The `context.py` prompt index is
  migrated to fail-closed (no adoption on an absent index) because Continue prompt files
  (`context.py:1707–1714`) emit no agent-meta provenance marker. Recommended default: accept
  the asymmetry — no marker is added in this change, and an index-absent run deletes nothing
  (safe but may leave legacy orphan prompts as `foreign`). Alternative: add a provenance
  marker to the generated prompt frontmatter in a follow-up. **NEEDS USER APPROVAL** only if
  the follow-up is wanted; the fail-closed migration is unconditional.

### Corrected hypothesis (explicitly recorded)

The user's B-III hypothesis — *"the managed block does not shrink"* — is **incorrect in the
normal path**. `_update_managed_html_block` (`context.py:347–442`) already re-renders and
wholesale-replaces the block (`:436`). B-III is therefore a **proof gap plus six stale-path
bypasses**, not a shrink defect. Any implementation that "fixes the shrink" by changing
`:436` would be a regression and must be rejected in review.

### Risiken

- **R1 — Residual legacy orphans (design D2).** A genuinely orphaned pre-marker file is
  not auto-swept; it is reported as `foreign` and must be removed manually. Accepted
  trade-off of the fail-closed predicate; mitigated by OQ-3's `legacy_unmarked` flag.
- **R2 — `based-on:` as a secondary provenance signal (HYPOTHESIS).** If a provider emits
  `based-on:` in user content without any primary marker, it could be misclassified as
  provenance-carrying. Mitigation: primary markers take precedence and are checked first
  (IC-02).
- **R3 — Preview/apply TOCTOU.** Between preview and apply the project can change.
  Mitigated by the server-side fingerprint recomputation and `409 preview_stale`
  (AC-13).
- **R4 — Backup growth / gitignore coverage.** Writing a backup before every cleanup
  delete increases small files in working trees. Mitigated by the conservative pruner
  (AC-09) and the requirement to verify `.gitignore` coverage for `*.sync-backup-*`
  (design D7). `HYPOTHESIS`: the current ignore coverage is not asserted by this spec.
- **R5 — `rule_index.py` widening.** Generalizing the helper means it now serves callers
  with different index-write policies. Mitigation: the write policy stays in the caller,
  the helper stays policy-free (IC-01 boundary).
- **R6 — Admin route does not remove the role.** The UI flow is two steps (uncheck role →
  preview → confirm); this is intended single-ownership of `project.yaml` (design D6) but
  may read as friction.
- **R7 — Reconciliation widens the delete surface (F-01).** The adoption branch deletes any
  unexpected file whose primary provenance origin is `0-external/`, even if a user
  hand-copied such content. Mitigations: index must be readable, primary markers only
  (`based-on:` excluded), backup-first delete, and the action is logged. Accepted trade-off;
  the safer manual-removal alternative leaves the user's complaint unresolved.
- **R8 — `deleted` is the intended, not observed, deletion set (F-03).** Because
  `SyncExecutor.run()` exposes no machine-readable summary, `deleted` mirrors the recomputed
  preview. A divergence in the sub-second window before `run()` (or a per-file unlink
  failure) is not reflected. Mitigations: `deleted` is emitted only on `returncode == 0`;
  the fingerprint guard narrows the window; a `--json-summary` output contract is the
  recorded follow-up if exactness is later required.

---

## Trace-Anker

Trace anchor (carried unchanged from the system design, to be referenced by the plan):
`spec-id: SPEC-STALE-ROLE-CLEANUP-2026-09-13`

Primary source references (verified 2026-09-13):

- `scripts/lib/agent_sync.py` — collector 751–765 (→ `_collect_active_skill_wrapper_filenames`
  + new `_collect_all_registry_wrapper_filenames`), `_cleanup_stale_agents` 767–815
  (index read 783–788, fail-open guard 806, write condition 812–815, candidate globs
  796–802, DELETE log 804–808), new pure `plan_agent_cleanup` / `StaleAgentEntry`,
  call site 900, capability gate 896–897, `sync_agents_for_provider` 851–902,
  `_should_skip_role` 503–531.
- `scripts/lib/rule_index.py` — read 21–29, bootstrap 32–68, cleanup 71–86, empty-write
  89–101.
- `scripts/lib/skills.py` — dir resolution 374–378, target paths 424/490, write 525–527,
  inactive removal 427–435, activation source of truth 389–390/421–422.
- `scripts/lib/generated_file_drift.py` — `_SYNC_BACKUP_PATTERN` 109,
  `_is_sync_backup_name` 112–114, backup writer 221–269, managed iterators 117–177.
- `scripts/lib/sync_pipeline.py` — call site 667–670; auto_generate 250–265, 300–304,
  355–358; provider deactivation 339–341, 601–602; skill-channel universe 534–568.
- `scripts/lib/context.py` — `_update_managed_html_block` 347–442, regex 372–376, replace
  436, `_regenerate_static_context` 186–276 (existing_managed 225/272),
  `_insert_managed_block_above_foreign_content` 445–458, `_MANAGED_BLOCK_RE` 30–33,
  `only_variables` 1578–1607, `sync_prompts_for_provider` fail-open 1723–1740 (delete guard
  1733, write condition 1739), prompt frontmatter 1707–1714 (no provenance marker).
- `scripts/lib/skills.py` — `ensure_skill_repo` 212–301 (git submodule add/clone, no
  `dry_run`), unconditional call site 410–412, `deinit_skill_repo` 304–321, wrapper
  generation origin 500 (`generated_from=f"0-external/{skill_name}@{commit}"`).
- `docs/ui/admin-ui.html` — sync view `btn-row` 5113–5117, `setSyncButtonsDisabled`
  5192–5194, shared confirm modal `el("button", { class: "btn btn-danger", … })` 828.
- `scripts/sync.py` — `--only-variables` 117–118, `_MODE_HANDLERS` 324–349.
- `scripts/admin-server.py` — `SyncExecutor` 1064–1141, `_run` 1076–1106, `dry_run`
  1133–1137, `run` 1139–1141, `_send_json` 3014–3025, `_read_body` 3044–3063,
  `_POST_EXACT_ROUTES` 3382–3406, `_DELETE_PREFIX_ROUTES` 3408–3413.
- Provenance markers — `frontmatter.py:244, 278–294`; `provider_transform.py:554–561`;
  `agent_toml.py:75`; `based-on` `frontmatter.py:515` (secondary, HYPOTHESIS).
- Tests — `tests/test_agent_sync_helpers.py:237–338` (incl. fail-open test 300–315,
  empty-expected test 288–297), `tests/test_admin_server.py:38–48` (module-load pattern);
  new `tests/test_admin_cleanup_endpoint.py`, `tests/test_context_managed_block_shrink.py`.
