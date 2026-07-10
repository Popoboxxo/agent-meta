---
description: Validate agent templates, commands and cross-references for consistency (version bumps, anchors, placeholders, cross-refs)
allowed-tools: ["Bash"]
argument-hint: "[--changed | --all | --file <path> | --strict]"
---

Run the agent-meta consistency check. $ARGUMENTS

Detect location:
- Project (submodule): `.agent-meta/scripts/consistency-check.py`
- agent-meta itself: `scripts/consistency-check.py`

Default: `--changed`. Pass `--all`, `--file <path>`, `--strict`, `--json` through from $ARGUMENTS.

If exit 0: report pass. Otherwise show findings, explain each ERROR, offer to fix, then re-run.
