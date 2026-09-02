---
name: issue-611-613-reflection-yaml-mcp-cycle
description: Issues #611 (reflection_pairs YAML editor bug) + #613 (mcp/mcp_provider_config/rules cycle) — both DONE on branch fix/reflection-pairs-yaml-and-mcp-cycle, full suite green (891 passed/2 skipped), sync.py --validate clean, NOT committed
metadata:
  type: project
---

Both issues implemented on branch `fix/reflection-pairs-yaml-and-mcp-cycle` (based on
main@6384d6d4, clean). **Not committed/pushed** — left for the main agent's `git` delegate.
Full suite run TWICE, second run started only after all #613 edits were finished on disk
(collection-time staleness trap from Wave-8/9 memory — a background pytest run started mid-edit
can collect stale module state) — both green: 891 passed, 2 skipped. `sync.py --validate`
unchanged from baseline (same 2 pre-existing orchestrator-strict warnings only).

## Issue #611 — reflection_pairs section editor produced malformed YAML

**Root cause (verified by repro, not just the issue's hypothesis):**
`RoleDefaultsEditor._build_role_defaults_section_body` in `scripts/admin-server.py` hardcoded
`base_indent = 2` for ALL sections. That's correct for dict sections (`quality_pipelines:` etc.,
whose child keys sit at column 2), but PyYAML dumps a block *sequence* directly under a top-level
key with the dash at column 0 (`key:\n- item`), not column 2. Because `reflection_pairs` is a
list section, `_split_list_children(body_lines, base_indent=2)` never matched any existing
`- id: ...` marker (they're all at indent 0) → `old_by_id` was always empty → every item was
treated as new, re-serialised at the WRONG indent (2-space dash), and appended in front of the
**entire untouched original body** (which was then duplicated verbatim as "tail") → invalid YAML
with duplicate un-parseable content.

**Fix:** added `RoleDefaultsEditor._infer_list_base_indent(body_lines)` (scans for the first
`- ` marker's column, falls back to 0) and switched `base_indent` to use it specifically for
`key == "reflection_pairs"` list sections, dict sections unchanged at `base_indent = 2`.

**Second bug found+fixed while verifying (not in the original issue text):** the list-child path
had no `deleted_indices` handling, unlike the dict-child path (which explicitly drops line ranges
of removed dict keys). Deleting a `reflection_pairs` entry via `write_reflection_pairs([...])`
silently no-op'd — the deleted item's lines survived in the gap/tail slices regardless. Fixed by
mirroring the dict path's `deleted_indices` set (ids present in `old_by_id` but absent from the
new value's id-set → their line range is excluded from every `body_lines[...]` slice). Both
append, in-place update, and delete now verified round-trip through `yaml.safe_load` correctly,
with `quality_pipelines` (dict section) byte-identical/untouched throughout.

**Regression tests:** `tests/test_admin_server.py::TestReflectionPairsSectionEditorProducesValidYaml`
(3 tests: append produces valid YAML + correct 0-indent dash, update preserves untouched items,
delete actually removes the entry).

## Issue #613 — mcp/mcp_provider_config/rules import cycle

**Verification tool:** Wave 6's `scratchpad/depcycle.py` (Tarjan-SCC over top-level + deferred
relative imports) was NOT preserved in the repo (scratchpad is a session-local temp dir, not
committed) — rebuilt from scratch this session, same approach. Confirmed the exact 3-module SCC
from the issue: `mcp ↔ mcp_provider_config ↔ rules` (`rules->mcp`, `mcp_provider_config->mcp`,
`mcp->{mcp_provider_config,rules}`).

**Fix:** extracted the neutral, dependency-free slice both `mcp_provider_config` and `rules` were
reaching into `mcp.py` for — `load_mcp_registry`, `resolve_active_mcp_servers`,
`build_mcp_guardrails_list`, plus `MCP_REGISTRY_YAML`/`SECRETS_LOCAL_FILE` constants — into a new
`scripts/lib/mcp_registry.py` (107 lines, deps: only `.io`). Follows the `variables.py`/
`frontmatter.py` Wave-6 precedent exactly: `mcp.py` re-exports all 5 names at top level
(`from .mcp_registry import (...)  # noqa: F401`) so every existing external caller
(`sync.py`, `context.py`, `agent_sync.py`, `external_tools_drift.py`, tests) keeps working
unchanged via `from .mcp import X` — verified 0 callers needed touching outside the 3 cycle
modules themselves. `mcp_provider_config.py` and `rules.py`'s deferred imports were repointed
from `.mcp` to `.mcp_registry` (kept deferred, not promoted to top-level — smaller diff, no
correctness difference since depcycle.py checks both).

**Result graph after fix:** only remaining edges are `mcp -> mcp_provider_config` (unchanged,
one-directional top-level re-export) and `mcp -> rules` (unchanged, one-directional deferred, for
`resolve_rules` in `generate_mcp_artifacts`) and `{mcp, mcp_provider_config, rules} -> mcp_registry`
(new, one-directional). No path back from `mcp_registry` to any of the three → cycle fully broken.
SCC count: repo-wide `scripts/lib` non-trivial SCCs went from 2 (this one + the pre-existing,
out-of-scope `external_tools ↔ external_tools_drift`) to 1 (just the pre-existing one, untouched
per issue's explicit scope).

**Line counts after split:** `mcp.py` 383 (was 472), `mcp_provider_config.py` 406 (was 403, +3 for
comment), `rules.py` 423 (was 420, +3 for comment), new `mcp_registry.py` 107. All well under the
600-line convention cap.

**Tool used (not committed to repo, recreate if needed):** Tarjan-SCC AST walker over
`ast.ImportFrom`/`ast.Import` nodes found via `ast.walk` (catches deferred/function-local imports
too, not just module-level) — `python3 <path> <libdir> [module...]` prints non-trivial SCCs and,
if given module names, the focused in/out edges for those modules specifically.
