---
name: dual-template-tree-modern
description: Editing 1-generic/ templates does NOT affect agent-meta's own senior/junior/perf agents — modern variants in 1-generic-modern/ override them
metadata:
  type: project
---

agent-meta runs in **modern prompt mode** (`agent-prompts.default: modern` in `.meta-config/project.yaml`). Templates therefore have TWO parallel source trees:

- `agents/1-generic/<role>.md` — legacy/canonical (German, section-based)
- `agents/1-generic-modern/<role>.md` — modern (English, `<persona>/<workflow>/<context>` tags)

**Why:** When a modern variant exists AND the project defaults to modern, sync generates the agent from the modern variant — the 1-generic/ edit is silently ignored for that role. Exception: `developer` is generated via `2-platform/agent-meta-developer.md` which composes (extends) `1-generic/developer.md` (non-modern), so developer edits flow through the legacy tree.

**How to apply:** When changing a role that has a modern variant (developer, junior-developer, senior-developer, performance-optimizer, orchestrator, openscad-developer), mirror the SAME semantic change into BOTH trees and bump BOTH versions, or the change won't reach agent-meta's own generated agents. Verify via `grep` in `.claude/agents/<role>.md` after sync which source rendered it (dry-run prints `(1-generic-modern/<role>.md [modern])` vs `(2-platform/...)`). Roles with no modern variant (e.g. new `e2e-tester`) fall back to 1-generic/ automatically.
