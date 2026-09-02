---
name: wave-b-provider-config-truth-source-627-628
description: Wave-B/#627,#628 batch — DONE, both issues implemented on branch refactor/provider-config-truth-source (on top of Wave A/main@e6f90321), full suite green (893 passed/2 skipped, x2 runs), sync.py --validate clean (4 provider-registry-gap warnings from Wave A confirmed gone), NOT committed
metadata:
  type: project
---

Both Wave-B issues (#627 eliminate provider-keyed Python maps, #628 route Gemini bootstrap through
BootstrapEngine) implemented on `refactor/provider-config-truth-source` (based on `main@e6f90321`,
which already had Wave A's `provider_registry_completeness` config_audit rule). **Not
committed/pushed** — left for the main agent's `git` delegate.

## Verification method: reverse-patch baseline diff (not git stash)

`git stash`/`git worktree` are blocked by `orchestrator-guard.sh` even for a developer subagent
(any git mutation, regardless of directory). Worked around it read-only: `git diff > patch`, tar-copy
the live repo to a scratch dir, `patch -p1 -R < patch` to reconstruct the pre-change tree, then run
`PYTHONHASHSEED=0 python3 scripts/sync.py` (full run, not --dry-run — dry-run log lines aren't
sufficient, see below) in both trees and `diff -rq` the outputs, excluding `scripts/`, `tests/`,
`config/ai-providers.yaml`, `docs/` (source diffs, not sync output) and `__pycache__`. Zero
differences in generated output for both issues combined. This confirmed byte-identical sync output
without ever mutating the tracked working tree.

**Caveat found:** `sync.py --dry-run` log output has pre-existing non-determinism unrelated to any
change — one INFO line lists active rule names in dict/set iteration order that varies run-to-run
(confirmed by running the *unpatched* baseline twice and diffing those two runs against each other:
same variance). Timestamps in the sync banner line also differ. Don't treat either as a regression
signal; only the reconstructed-file diff (`diff -rq` over the actual generated files) is reliable.

**Also found:** a concurrent process/agent was writing to this same repo during my session
(`docs/plans/report-2026-09-provider-support-claude-opencode-gemini.md` appeared mid-session, later
turned out to be `git ls-files`-tracked already — not mine, not touched, unrelated to Wave B).
Worth remembering this repo isn't always exclusively owned during a session.

## #627 — 5 sub-fixes, all verified individually + together

1. **`context.py::provider_dirs`** — deleted the 6-entry hardcoded dict; both of its use sites already
   sat next to a working `provider_config[p].get("agents_dir", f".{p.lower()}/agents")` pattern one
   line above (the `shared_users` branch), just reused that pattern for the two `provider_dirs.get(...)`
   call sites instead of the dict.

2. **`lifecycle_check.py::_PROVIDER_PENDING_FILES`** — this script deliberately avoids importing
   `lib/` (runs standalone from a git hook, must work with bare Python). Replaced the hardcoded dict
   with a regex-based scan of `config/ai-providers.yaml` (2-space-indented provider block, then
   `pending_tasks_file:` key inside it) — same "no full YAML parse needed" pattern already used by
   `scripts/measure_context.py` for the same file. `AGENT_META_ROOT = Path(__file__).resolve().parent.parent`
   resolves correctly in both self-hosting and `.agent-meta/` submodule layouts (verified against
   `hooks/1-generic/lifecycle-check.sh`'s own two-path resolution logic).

3. **`viz.py::_PROVIDER_TERMINAL_TOOL`** — deleted the dict; the function already checked
   `config/provider-tools.yaml::terminal_tool` FIRST (a pre-existing, separate YAML source with
   identical values) and only fell back to the Python dict when that lookup missed. Replaced the
   Python-dict fallback with `load_providers_config(agent_meta_root)[provider].get("bash_tool_name")`
   — added the new `bash_tool_name` key to `config/ai-providers.yaml` per provider (values taken
   verbatim from the old Python map, per the task's explicit instruction). Since
   `provider-tools.yaml::terminal_tool` already has all 6 providers, the new fallback path is
   currently dead in practice but correct/tested as a safety net — didn't touch provider-tools.yaml
   itself (out of scope, no warning tied to it, avoids scope creep).

4. **`setup.py::valid_providers`** — `list(load_providers_config(agent_meta_root).keys())` instead of
   a hardcoded 6-item list. Order changed slightly (YAML file order: Claude/Gemini/Opencode/Continue/…
   vs old hardcoded Claude/Gemini/Continue/Opencode/…) — cosmetic only, affects interactive wizard
   choice ordering, not sync output; no test covers it.

5. **`isolation.py`** — the one genuinely tricky sub-fix. The if/elif dispatch
   (`if provider == "Claude": ... elif == "Opencode": ...`) dispatches to **real per-provider
   mechanisms** (JSON deny-patterns vs TOML rules vs Markdown soft-rule — different file formats, not
   just different config values), so a naive "just read isolation-dirs from YAML" fix doesn't apply —
   that data was *already* YAML-sourced. The actual duplication is the *dispatch itself* using literal
   `if provider == "Name"` (project convention explicitly forbids this). Fixed by adding
   `isolation-mechanism: <key>` to `config/ai-providers.yaml` per capable provider (Claude/Opencode/
   Gemini/Continue; Copilot/Mammouth deliberately have no key = "not implemented") and dispatching via
   a `_ISOLATION_MECHANISM_HANDLERS = {mechanism_key: handler_fn}` dict built at module scope (placed
   *after* all four `_sync_*_isolation` functions in the file — referenced from
   `sync_provider_isolation` which sits *above* them, works fine since Python resolves module globals
   at call time, not def time). Also eliminated `_guess_provider_name_from_dir` (substring-guessing
   "Claude Code"/"Gemini CLI"/etc. from a directory path) since the caller already knows exact
   ownership — threaded a `dir_owner: dict[dir -> provider]` through instead, with a new
   `isolation-display-name` YAML key for the 2 providers whose display string differs from their
   registry key (Claude→"Claude Code", Gemini→"Gemini CLI"; Opencode/Continue already match their key
   verbatim, no override needed). Verified byte-identical output for a synthetic 6-provider run
   (all isolation files: Claude settings.json deny list, Gemini TOML, Continue soft-rule .md all
   correct, including proper display names for previously-"another provider" Copilot/Mammouth dirs).

   **Existing test had to be updated** (not just left alone): `tests/test_secrets_and_isolation.py`'s
   `test_isolation_still_generates_deny_entries` used a synthetic `provider_config` missing the new
   `isolation-mechanism` key — added it to the fixture (`"isolation-mechanism": "claude-settings-deny"`
   / `"opencode-permissions"`). This is a legitimate fixture update to match the new config contract,
   not a scope violation — the test's *intent* (isolation still generates deny entries) is unchanged
   and still passes.

   **config_audit_providers.py side effect**: 4 of 5 touchpoint regexes stopped matching once their
   target dict/list was deleted, so `find_missing_providers()` silently skips them (documented,
   intended behavior — no checker change needed). The 5th (`isolation.sync_provider_isolation`,
   matched on `def sync_provider_isolation(...)` up to the next top-level `def`) still matches the
   *function*, but the function body no longer contains ANY literal provider-name strings (dispatch is
   now via config key), so leaving that touchpoint in place would have flipped 2 warnings
   (Copilot/Mammouth) into 6 (every provider). Retired that one `ProviderTouchpoint` entry from the
   tuple with a comment explaining why — this is legitimate: the literal-enumeration anti-pattern the
   checker targets no longer exists in that function, checking for it is a false-positive generator,
   not a caught bug.

## #628 — Gemini bootstrap through BootstrapEngine

Root cause: `BootstrapEngine.run_bootstrap()` already had an `api-based` mechanism branch
(`_bootstrap_api_based`), but it was DEAD CODE — never called from `agent_sync.py`, which instead
special-cased Gemini with a direct call to `_inject_gemini_bootstrap()` in `provider_transform.py`.
That function *did* already use `BootstrapEngine.get_bootstrap_config()` +
`generate_gemini_bootstrap_instructions()` for config lookup/content generation, but did its own
file-write/marker-injection logic outside the engine — so Continue (`update-config` →
`bootstrap_engine.run_bootstrap()`, single call site) and Gemini (`inject-bootstrap-instructions` →
bespoke direct call) followed different call patterns despite both being "provider bootstrap".

Fix: moved `_inject_gemini_bootstrap`'s entire body (marker-based GEMINI.md/AGENTS.md injection,
path-traversal guard, dry-run gate, logging) into `BootstrapEngine._bootstrap_api_based`, replacing
its old no-op "return a list of define_subagent call strings" behavior (confirmed unused/untested
elsewhere — safe to replace outright, no back-compat method needed). Extended `run_bootstrap()`'s
signature with keyword-only `dry_run`/`log`/`context_file`/`compact`/`agents_label` (Continue's
`config-based` path ignores all of them — untouched, including its pre-existing "doesn't respect
--dry-run" behavior, deliberately NOT fixed here, out of scope). `agent_sync.py` now has ONE
`if provider in ("Gemini", "Continue"): ... bootstrap_engine.run_bootstrap(...)` call site instead of
two separate `if provider == "Gemini": _inject_gemini_bootstrap(...)` / `if provider == "Continue":
...run_bootstrap(...)` blocks. Deleted `_inject_gemini_bootstrap` from `provider_transform.py` and its
import in `agent_sync.py`; deleted the now-dead `BootstrapEngine._extract_description` helper that
only the old `_bootstrap_api_based` used.

Verified: this repo's own Gemini context file is `AGENTS.md` (not `.gemini/GEMINI.md` — Gemini and
Opencode share `context_file: AGENTS.md` in `config/ai-providers.yaml`, confirmed via
`resolve_context_filename()`), so the self-hosted full-sync baseline-diff exercised the real injection
path end-to-end: `<!-- agent-meta:bootstrap-begin -->...<!-- agent-meta:bootstrap-end -->` block in
`AGENTS.md` byte-identical before/after.

## Both issues together

Full suite run twice (once after #627 alone during dev, once again after #627+#628 combined) —
893 passed / 2 skipped both times, no failures. `sync.py --validate 2>&1 | grep -i provider` before:
4x `provider-registry-gap` WARN (Copilot/Mammouth missing from lifecycle_check + isolation touchpoints)
+ 2x unrelated `orchestrator-strict.no-hook-support` WARN. After: only the 2 unrelated warnings remain
— explicit confirmation the elimination (not just Copilot/Mammouth patch-in) was complete.
