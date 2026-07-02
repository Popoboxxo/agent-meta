# Workflow References (formerly `_wf-*.md`)

> **Status:** These files were consolidated into agent templates and rules during Phase 1 token optimization (v0.66.0-beta.3).
> The workflow knowledge is preserved in the respective agent templates and rules files.

## Former Workflow Files & Their Current Location

| Former File | Content | Now In |
|-------------|---------|--------|
| `_wf-sync-interface.md` | sync.py flags, sync.log format | `rules/2-platform/agent-meta-sync-interface.md` |
| `_wf-upgrade.md` | agent-meta upgrade procedure | `rules/2-platform/agent-meta-conventions.md` (section: "Änderungs-Checkliste") |
| `_wf-skill-lifecycle.md` | External skill activate/deactivate/add | `rules/2-platform/agent-meta-sync-interface.md` (--add-skill flag) |
| `_wf-security-audit.md` | OWASP categories, audit workflow, report format | Agent template: `security-auditor.md` |
| `_wf-scout.md` | Scouting + external skill repo workflow | Agent template: `agent-meta-scout.md` |
| `_wf-issue.md` | GitHub Issue bearbeiten (L workflow) | `rules/1-generic/issue-lifecycle.md` |
| `_wf-git-ops.md` | Git extended workflows, platform hints | Agent template: `git.md` |
| `_wf-feedback.md` | Feedback an agent-meta | Agent template: `meta-feedback.md` |
| `_wf-claude-review.md` | CLAUDE.md review & improvement | `rules/2-platform/agent-meta-conventions.md` |

## Why This Change?

The `_wf-*.md` files were underscore-prefixed partials — excluded from agent generation by sync.py.
They existed as reference material but consumed repo space and added cognitive overhead.
The knowledge they contained is now:
1. Embedded in the responsible agent's template (for agent-specific workflows)
2. Preserved in rules files (for cross-cutting conventions)
3. Documented in this reference table (for human lookup)
