---
name: wave7-sync-core-small-refactors
description: Wave-7/#566,#568,#571,#574,#578 batch — DONE, all 5 issues implemented on branch refactor/sync-core-cleanup-batch, bit-exact output verified, NOT committed
metadata:
  type: project
---

All 5 Wave-7 issues from `docs/plans/audit-2026-08-refactoring-roadmap.md` implemented on branch
`refactor/sync-core-cleanup-batch` (based on main@f1bf9671, i.e. right after Wave 6's `#565/#561/#563` merged).
**Not committed/pushed** — left for the main agent's `git` delegate. Full test suite green after
every single issue (845 passed, 2 skipped at the end — was 805 baseline; +40 from 5 new test files),
`sync.py --validate` byte-identical to baseline throughout (only 2 pre-existing orchestrator-strict
warnings, unrelated to this batch).

**Issue-by-issue:**

- **#578** (provider context filename): added `resolve_context_filename(context_file, provider)` to
  `scripts/lib/providers.py`, replaced both inline `CLAUDE.md→AGENTS.md` duplicates in `sync.py`
  (`_handle_sync`, provider-cleanup section). Trivial, no design decisions.

- **#574** (`SyncLog.info`→rename): chose **`note()`** as the new name (alternatives considered: `event`,
  `record` — `note` read best next to existing `action`/`warn`/`skip`/`debug`). Removed `info()` entirely
  (no deprecation wrapper, per acceptance criteria). Updated all 44 call sites across
  sync.py/viz.py/config.py/provider_transform.py/deactivation.py/backup.py/isolation.py/hooks.py/
  skills.py/context.py/rules.py/agent_sync.py via `sed -E 's/\blog\.info\(/log.note(/g'` + stripped all
  `# noqa: PLE1205` comments. **Gotcha found later (during #568):** `SyncLog.debug(target, msg)` has the
  *exact same* two-positional-arg-vs-logging.debug(msg,*args) linter confusion as the old `.info()` —
  ruff's PLE1205 doesn't care which stdlib-logging-named method it is. My new `#568` `log.debug(...)`
  call sites needed their own `# noqa: PLE1205` (2 in sync.py, 2 in backup.py) since renaming `.debug()`
  too was out of #574's scope. **Follow-up candidate:** if `.debug()` grows more 2-arg call sites, it may
  deserve the same treatment as `.info()` did.

- **#571** (frontmatter/YAML dedup): Wave 6 had *already* created the canonical `scripts/lib/frontmatter.py`
  (with `_split_frontmatter`/`_parse_frontmatter_yaml`/`_YAML_AVAILABLE`) and re-exported everything via
  `agents.py` — so most of the issue's original 7-module list was already fixed by Wave 6 by the time I
  looked. Remaining real duplicates found and fixed:
  - `config_audit.py::_parse_frontmatter(path)` → replaced with new canonical
    `frontmatter.parse_frontmatter_file(path)` (added to frontmatter.py + re-exported via agents.py);
    `_YAML_AVAILABLE` now imported from `.frontmatter` instead of a second independent try/except (the
    module still keeps its own bare `import yaml as _yaml` for `_read_yaml()`'s whole-document parsing,
    which is a different concern than frontmatter parsing — documented inline why that's not a duplicate).
  - `context.py::_strip_rule_frontmatter` was a byte-identical copy of `frontmatter._strip_frontmatter`
    → deleted, now imports the canonical one directly (`from .frontmatter import _strip_frontmatter`,
    safe: frontmatter.py has zero internal lib imports, no cycle risk).
  - `commands.py::_add_frontmatter_field` and `rules.py::_build_always_apply_frontmatter` both
    reimplemented the `"---"`-fence-detection split inline → rewritten to call `_split_frontmatter()`
    internally, function *behavior* unchanged (verified with a standalone equivalence-fuzzing script
    covering malformed-frontmatter edge cases — opening fence with no closing fence must NOT be treated
    as "no frontmatter", easy to get wrong when refactoring naively).
  - **Deliberately NOT touched:** `scripts/lib/consistency/{frontmatter.py,crossrefs.py,commands.py}` —
    each has its own independent frontmatter-parsing helpers, NOT in the issue's named module list, and
    `config_audit.py` has an explicit comment that the `consistency` package is intentionally import-light/
    decoupled from `scripts/lib` proper. Grep for `_parse_frontmatter`/`_split_frontmatter` outside
    `frontmatter.py` will still find these 3 files — that's expected/accepted, not a miss.

- **#566** (`build_variables` decomposition): split into 8 sub-functions (not exactly the 4 named in the
  issue body — those were explicitly "z.B." examples): `_build_core_variables`, `_build_provider_variables`,
  `_build_orch_variables`, `_build_platform_variables`, `_build_dod_variables`, `_build_pipeline_variables`,
  `_build_snippet_variables`, `_build_convention_variables`. `build_variables()` body is 16 lines (≤30 ✓),
  every sub-function ≤122 lines (≤150 ✓). **Verification method (important for any future re-split):** the
  original ~500-line function has heavy hidden cross-references (config sub-dicts re-read multiple times,
  `unmapped` list threaded through 4 different except-branches, `dod_resolved`/`effective`-pipelines dict
  reused across sections) — a naive semantic-only regrouping WILL silently reorder side-effecting code. I
  verified zero drift by dumping the full `variables` dict + `unmapped` list to JSON both before and after,
  across 4 synthetic project.yaml variants (base / legacy-flags+native-ext-whitelist+outcome-caching /
  SE+knowledge-engine / analysis-enabled) — `diff` reported byte-identical every time. Recommend the same
  technique for any future config.py refactor. One safe reordering was applied (A2A_T_SIZE_LIMIT/
  A2A_MAX_DEPTH/A2A_HANDOFF_BLOCK moved from their original position — physically after the SE/Knowledge
  block — into the orchestration group, since they only depend on values set within that same group and
  don't touch `unmapped`).
  **Known pre-existing issue NOT fixed (out of scope):** `scripts/lib/config.py` was already 1030 lines
  before this session (over the 600-line module limit) and is now ~1200 after adding docstrings — the
  600-line limit was already broken by a wide margin pre-Wave-7; a full module split of config.py is a
  separate, much larger undertaking than "decompose one function" and wasn't requested by #566. Flagging
  for a future wave/issue.

- **#568** (bare `except Exception: pass`): fixed exactly the 8 locations named in the issue body (2×
  sync.py, 3× viz.py, 2× backup.py, 1× pipelines.py) — deliberately did NOT touch admin-server.py/
  viz-report.py/migrate-config.py/run-cascade.py's own bare-except instances (different modules/audits,
  not named in this issue). Pattern used per site: narrow to the minimal expected exception class (OSError
  for I/O/cleanup, `zipfile.BadZipFile` for zip reads, `yaml.YAMLError`/`AttributeError`/`TypeError`/
  `ValueError` for the plan-frontmatter YAML parse in pipelines.py), log at DEBUG with type+message+context,
  comment why continuing is safe. Where a `SyncLog` instance was already in scope (sync.py, backup.py) used
  `log.debug(...)`; where not (viz.py, pipelines.py) added a module-level `logging.getLogger(__name__)`.
  **Interpretation call:** the issue text says "echte unerwartete Exceptions... loggen als WARNING und
  weiterwerfen (raise)" — I read this as "don't add a second broad catch-all", satisfied automatically by
  simply narrowing the except clause (anything not matching propagates on its own). I did NOT add an
  explicit `except Exception as e: log.warning(...); raise` second tier at each site — that would've
  changed 4 previously-100%-fail-soft code paths (cosmetic AST summary, best-effort provider-dir cleanup,
  best-effort backup-restore inference, best-effort event-log read) into crash-capable ones, which felt
  like scope creep beyond "narrow the except" and risked violating "kein Breaking Change". Verified this
  reading is testable/correct with 12 new unit tests (`tests/test_exception_specificity.py`) that assert
  both halves: expected exception → swallowed+logged; unexpected exception (`RuntimeError`) → propagates.
  **Latent-bug catch during implementation:** `pipelines.py::parse_plan_ref`'s original code did
  `import yaml` *inside* the same `try` block it was narrowing — referencing `yaml.YAMLError` in the
  `except` clause would raise `NameError` if the import itself failed (PyYAML not installed), masking the
  real `ImportError`. Split into two nested try/excepts (import failure handled separately) to avoid this.

**New test files added (all passing, none deleted/modified from pre-existing suite):**
`tests/test_provider_context_filename.py`, `tests/test_sync_log.py`, `tests/test_frontmatter_canonical.py`,
`tests/test_build_variables_decomposition.py`, `tests/test_exception_specificity.py`.

**Full-suite timing:** ~6:20–6:25 per run with `-p no:homeassistant --ignore=tests/test_homeassistant`
(ran it 5 times this session, once per issue — matches the `senior-developer` memory's noted ~6:30 baseline).
