---
name: wave8-persistence-robustness-batch
description: Wave-8/#573,#576,#580,#582,#583,#586 batch — DONE, all 6 issues implemented on branch fix/persistence-robustness-batch, full suite green, NOT committed
metadata:
  type: project
---

All 6 Wave-8 issues from `docs/plans/audit-2026-08-refactoring-roadmap.md` implemented on branch
`fix/persistence-robustness-batch` (based on main@1cbb7e3e). **Not committed/pushed** — left for the
main agent's `git` delegate. Full suite green after final consolidated run (see below),
`sync.py --validate` unchanged from baseline (only the 2 pre-existing orchestrator-strict warnings).

**Order followed:** #573 first (delivered `io.write_atomic()`), then #576/#580 (checkpoint/cache), then
#582/#583/#586 (backup + secrets/isolation/DRY), matching the plan.

**Issue-by-issue:**

- **#573** (atomic write helper): `write_atomic(path, content, mode='w')` added to `scripts/lib/io.py` —
  temp file via `tempfile.mkstemp(dir=path.parent, ...)` + `flush()` + `os.fsync()` + `os.replace()`,
  cleans up the temp file on any exception. Same-directory temp file is required for `os.replace` to be
  atomic (same filesystem). Replaced every `write_text()` call in the 5 files named in the issue:
  `cache.py` (`_save`), `checkpoint.py` (`save_checkpoint`), `isolation.py` (`_write_state`), `io.py`
  (`write_checked`), `config_audit.py` (`apply_audit`). `_write_yaml()` also switched to go through it.

- **#576** (checkpoint corrupt-JSON crash): all 3 named read sites (`save_checkpoint`, `load_session`,
  `cleanup_old_sessions`) now tolerate `(json.JSONDecodeError, OSError)` — logged as a warning via
  `logging.getLogger(__name__)` (checkpoint.py itself no longer imports `logging` directly — the shared
  helper does), then treated as "empty/missing" (self-heal, matches the `cache.py` precedent the issue
  points at). `cleanup_old_sessions` skips (does not delete) unparseable session files rather than
  guessing at their age.

- **#580** (cache read-path race): **Design decision** — `read()` is now 100% side-effect-free (no write
  at all, not even for hit stats). Hit-counter tracking was decoupled per the issue's stated preference
  ("preferred: entkoppelter, gebatchten Vorgang", NOT locking, NOT atomic counter files):
  `record_hit(cache_path)` appends one line to a companion `<cache_path>.hits` journal file — a single
  small `open(..., "a").write(...)` is atomic on POSIX for concurrent appends, so concurrent hit
  recordings never race with each other. `write()` (which already has to do a real read-modify-write for
  the cache-miss deposit) drains+deletes the journal into the persisted `stats.hits` counter the next time
  it runs. `cache_stats()` peeks at the journal (counts lines, does not drain/delete) so a pure stats query
  stays read-only too. **Caveat:** nothing in the current codebase actually calls `cache.read()`/`write()`
  yet (only `sync.py --clear-cache` imports `invalidate`) — this is speculative future orchestrator-cache
  infra, so the API design here has zero real callers to validate against; revisit if/when a real caller
  shows up and the batching contract turns out to be awkward.

- **#582** (backup timestamp collision): `_archive_name()` timestamp format gained `_%f` (microseconds).
  Added `_unique_archive_name(backup_dir)` on top, which appends `_2`, `_3`, ... if the microsecond name
  still collides (belt-and-suspenders for coarse clock/filesystem resolution) — `create_backup` now calls
  this instead of the bare `_archive_name()`. **Note:** `_parse_archive_metadata()`'s `rsplit("_", 2)`
  field-splitting (feeds `list_backups()`'s display-only `timestamp`/`provider` info fields) was already
  mislabeled before this change (the "provider" field is actually the time-of-day, real provider name is
  never in the filename) and shifts further with the new `_%f` suffix — left untouched, not in scope for
  #582 and not consumed anywhere beyond cosmetic display (grepped for callers, none found).

- **#583** (backup restore swallows errors): the two `except (OSError, zipfile.BadZipFile)` sites in
  `restore_backup` (already narrowed from bare `except Exception: pass` by a prior wave's #568 fix — do
  not confuse the two issues) needed their **result-dict propagation**, which #568 explicitly deferred to
  #583 (see the removed inline comment). Provider-level extraction failure: `prov_result["error"]` now
  includes the exception type name, and a matching `log.warning(...)` was added (previously silent besides
  the dict field). project.yaml restore failure: added `result["config_restore_error"]` (new key, was
  previously untracked beyond a `log.debug` line) + upgraded that log call to `log.error`. The best-effort
  *provider-inference-from-bad-zip* fallback (a different, non-restore code path, covered by the existing
  `tests/test_exception_specificity.py::test_restore_backup_infer_providers_falls_back_on_bad_zip`) was
  deliberately left as `log.debug` + no result field — it's not a restore failure, just a best-effort
  guess that falls through to explicit `providers=` args when it can't infer anything.

- **#586** (5-point bundle):
  1. **gitignore verification** — added `verify_gitignored: bool = False` as a **new, separate** parameter
     on `write_checked()`, deliberately NOT reusing `allow_secrets=True` for this. **Important gotcha found
     during implementation:** `allow_secrets=True` has two unrelated meanings in this codebase — (a) "this
     is a genuinely local/gitignored file" (the only real case today: the MCP secrets-file write in
     `mcp_provider_config.py`) and (b) "`allow-committed-secrets: true` override for an intentionally
     *committed* file with the secrets scan downgraded to a warning" (`agent_sync.py`, and
     `mcp_provider_config.py`'s own *committed*-file write path via `allow_committed_secrets`). Hooking the
     gitignore check to `allow_secrets` directly would have produced a false-positive "not gitignored"
     warning on every committed file whenever a project sets `allow-committed-secrets: true` — caught this
     via a dedicated regression test (`test_write_checked_does_not_warn_for_committed_secrets_override`)
     before it shipped. `verify_gitignored=True` is threaded explicitly through
     `_write_provider_config` → `_update_json_config`/`_update_continue_yaml_config` → `write_checked`,
     set only at the one real local-secrets-file call site in `generate_provider_configs`. Fail-safe: any
     `git` subprocess problem (not installed, not a repo, timeout, `check-ignore` exit code >1) is silently
     ignored — informational only, per the task's explicit instruction, never blocks the write.
  2. **secrets.py false positives** — the `[a-zA-Z0-9_\-]{80,}={0,2}` "InfluxDB-style" pattern's label was
     set to `None` (same treatment as the existing broad-base64 pattern one line above it, which the issue
     explicitly names as the sanctioned precedent) — disables detection for this pattern rather than
     attempting a narrower regex, per the issue's own "ODER analog auf None setzen" option.
  3. **isolation.py dead code** — the two dead lines (`pc = provider_config.get(provider, {})` +
     `pc.get("isolation-dirs", [])`, `pc` was never read again) were deleted outright, not just the
     expression-statement line — `pc` itself had no other use in that loop body.
  4. **DRY** — two separate extractions:
     - `scripts/lib/json_persistence.py` (new, flat file — **not** under a `shared/` subdirectory; matches
       the existing flat `scripts/lib/*.py` convention, the `consistency/`/`context_templates/`/`se_export/`
       subdirs are each a bounded multi-file concern, not a general-utility dumping ground).
       `load_json_document(path, default)` / `save_json_document(path, data)`, used by both `cache.py` and
       `checkpoint.py` (also naturally carries the #573 atomic-write + #576 corrupt-JSON handling in one
       place instead of three).
     - `mcp_provider_config.py::_subst`/`_subst_opencode` — kept **local to the same file** (no new module)
       via a private `_subst_with_placeholder(value, secrets, placeholder_fn)` helper. Both call sites live
       in this one file only; a dedicated `shared/string_subst.py` module for a 2-line private helper with
       a single caller module would violate YAGNI. Public signatures of `_subst`/`_subst_opencode`
       unchanged.
  5. **backup.py CWD reliance** — `shutil.make_archive(root_dir=...)` does a transient process-wide
     `os.chdir()` internally. Replaced with a small `_zip_directory(source_dir, zip_path)` helper that
     walks `source_dir.rglob("*")` and writes each file with an explicit relative `arcname` — never touches
     the CWD. Verified with a test that monkeypatches `os.chdir` to raise if called at all.

**Scope note (flagged, not fixed):** `backup.py` was already over the 600-line module-size convention
before this session (692 lines pre-Wave-8) and is now ~729 after the additions — none of the 6 issues
asked for a module split, and splitting a 729-line file is a much bigger, separate undertaking. Same
pre-existing-debt situation as `config.py`/`context.py`/`pipelines.py`/etc. (see Wave-7 memory note on
`config.py`). Flagging for a future wave.

**New test files added (all passing, none deleted/modified from pre-existing suite):**
`tests/test_persistence_atomicity.py` (15 tests: #573/#576/#580, incl. a 16-thread concurrent-read stress
test and a 4×25-thread concurrent hit-journal stress test), `tests/test_backup_robustness.py` (9 tests:
#582/#583/#586p5), `tests/test_secrets_and_isolation.py` (11 tests: #586p1/p2/p3/p4).

**Full-suite timing:** ~6:25–6:30 per run with `-p no:homeassistant --ignore=tests/test_homeassistant`
(matches prior waves' noted baseline). **Process-timing gotcha for future sessions:** pytest's collection
happens at process start, so editing any of the files under test *while* a background full-suite run is
in flight silently invalidates that run for the edited modules (the already-running worker keeps the
import-cached pre-edit version) — don't trust a background run's "PASSED" as covering edits made after
you launched it; check file mtimes against the run's start time, or just don't touch source files while a
verification run is in flight.
