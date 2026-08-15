---
name: project-sync-lib-analysis
description: Snapshot of refactoring findings for scripts/sync.py + scripts/lib/* (2026-08-11) — god functions, duplicated frontmatter/YAML parsing, circular imports, dead code
metadata:
  type: project
---

Analysis-only pass (no code changed) over `scripts/sync.py` + `scripts/lib/*.py` (~18k LOC,
39 modules incl. `consistency/`, `se_export/`, `context_templates/`) done 2026-08-11, requested
by main_chat to produce GitHub-issue-ready findings.

**Why:** establishes a baseline before any actual refactoring work starts on this area — future
sessions doing incremental transformation steps on sync.py/lib should check whether these findings
are still current (line numbers will drift) rather than re-discovering them from scratch.

**Key findings (see full report given to main_chat for details/line numbers):**
- `main()` in `scripts/sync.py` is an 886-line God Function mixing argparse setup with a 40-branch
  if/elif command dispatcher — no existing dispatch-table pattern reused from `commands.py`.
- `build_variables()` in `config.py` (454 lines, 59+ direct dict writes) and three other god
  functions in `agents.py` (`transform_agent_content_for_provider` 245 lines,
  `sync_agents_for_provider` 274 lines).
- Two independently-implemented templating engines with diverging semantics:
  `config.py::strip_inactive_conditional_blocks()`/`substitute()` (used for agent/rule/context
  substitution, supports `{{%VAR%}}` escape + PAL_ skip + missing-var warnings) vs.
  `context_templates/builder.py::TemplateBuilder` (used for context templates, supports
  `{{#each}}` loops + `{{> partial}}` includes but NOT the escape syntax or missing-var warnings).
  Real risk: a doc author relying on `{{%VAR%}}` escaping in a context template would silently
  get it substituted instead of escaped, because that template renders through TemplateBuilder.
- Circular imports between `agents.py` <-> `config.py` and `agents.py` <-> `viz.py`, papered over
  with function-local imports rather than resolved via dependency inversion.
- Frontmatter YAML parsing reimplemented independently 4 times (`agents.py::_split_frontmatter`/
  `_parse_frontmatter_yaml`, `config_audit.py::_parse_frontmatter`, `pipelines.py` inline regex,
  `context_templates/builder.py::build()` inline `.split('---', 2)`) — each with different edge-case
  handling for a missing closing fence.
- Dead code: `agents.py::sync_agents()` (~194 lines, "legacy Claude-only path") has zero callers
  anywhere in `scripts/` or `tests/` — safe removal candidate.
- Real (small) bug found in passing: `mcp.py::_update_json_config` computes
  `str(path.relative_to(path.parent.parent)) if path.parent.name else rel` as a bare, unused
  expression statement (result discarded) — dead leftover from a refactor, not wired to `rel`.

**How to apply:** when this agent (or `developer`) is asked to actually execute any of these
refactorings, re-verify line numbers first (`grep -n` the referenced function names) since sync.py
churns frequently — do not trust the line numbers in the original report blindly after a few weeks.
