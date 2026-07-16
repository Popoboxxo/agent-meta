---
name: orchestrator-table-check-false-positive
description: consistency-check crossrefs.orchestrator-table-incomplete is a standing false-positive — do not fix by editing orchestrator.md
metadata:
  type: project
---

`consistency-check.py` emits ~9 `crossrefs.orchestrator-table-incomplete` warnings (requirements, tester, validator, documenter, git, log-analyzer, feedback, bug-feature-analyzer, code-reviewer) on every run. These are false-positives, not real inconsistencies.

**Why:** `check_orchestrator_table` in `scripts/lib/consistency/crossrefs.py` greps the un-substituted template `agents/1-generic/orchestrator.md`, whose delegation table is the `{{AGENT_DELEGATION_TABLE}}` placeholder (injected at build time by `scripts/lib/delegation_table.py`). The roles ARE present in generated output (`.claude/agents/orchestrator.md`), just not in the template. Warnings are identical on `main` — pre-existing, not branch-introduced.

**How to apply:** Never "fix" these by adding literal `| \`role\` |` rows to `orchestrator.md` — that lives inside the `agent-meta:managed-begin/end` block and would duplicate/conflict with the generated table. The real remediation (if desired) is teaching the checker to expand `{{AGENT_DELEGATION_TABLE}}`, but that is a tooling change, not a template edit. See [[dual-template-tree-modern]] for the related managed-block pattern.
