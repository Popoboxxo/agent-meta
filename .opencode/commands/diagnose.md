---
description: Health-check the agent-meta setup — versions, generated files, isolation state, gitignore
allowed-tools: ["Bash", "Read", "Glob"]
argument-hint: "[area to focus on: versions | isolation | gitignore | all]"
---

Run a health check of the agent-meta setup for this project. $ARGUMENTS

Work through these checks in order and report findings as ✅ OK / ⚠️ Warning / ❌ Error:

**1. Sync status**
Run `python .agent-meta/scripts/sync.py --dry-run` and report:
- How many files would be written (WRITE actions) vs skipped
- Any warnings in the output
- If 0 WRITEs: "Generated files are up to date"
- If WRITEs exist: list them — these files are out of sync

**2. Version check**
- Read `.agent-meta/VERSION` (agent-meta version)
- Read `CLAUDE.md` managed block — find "Generiert von agent-meta vX.Y.Z"
- If versions differ: ⚠️ "CLAUDE.md was generated with an older version — run sync"

**3. Provider isolation**
For each active provider in `.meta-config/project.yaml`:
- Claude: check `.claude/agent-meta-state.json` exists and contains `isolation-deny` entries
- Opencode: check `.opencode/agent-meta-state.json` exists and contains `isolation-deny` entries
- Gemini: check `.gemini/policies/provider-isolation.toml` exists
- Continue: check `.continue/rules/provider-isolation.md` exists
- If `provider-isolation: disabled` in project.yaml → report "isolation disabled (opt-out)"
- If only 1 provider active → report "isolation not needed (single provider)"

**4. Gitignore completeness**
Read `.gitignore` and verify the `# --- agent-meta managed ---` block exists and is non-empty.
Check that `.meta-config/secrets.local.yaml` is gitignored (if the file exists).

**5. MCP state** (if mcp-servers configured in project.yaml)
Check that for each active MCP server, the expected rule files exist per active provider.

Finish with a summary: total checks, how many ✅/⚠️/❌.
If all OK: "Setup is healthy."
If issues found: list actionable next steps.
