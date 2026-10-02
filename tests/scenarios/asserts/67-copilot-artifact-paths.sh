#!/bin/bash
# Scenario assert for 67-copilot-artifact-paths.
# (SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30, AC-8 / OQ-5 / PRE-4.)
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# --validate. This scenario proves the corrected GitHub-cloud Copilot artifact
# paths and that the legacy `.github/copilot/agents` layout is gone:
#   1. agent files are `.github/agents/<role>.agent.md` (not `.md`, not the
#      legacy `.github/copilot/agents` dir),
#   2. rules live under `.github/instructions/`,
#   3. the context file is `.github/copilot-instructions.md`.
# Exit 0 = all assertions hold.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (67-copilot-artifact-paths): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (67-copilot-artifact-paths): $*"
    exit 1
}

# 1. Agent files use the canonical GitHub-cloud path + `.agent.md` extension.
[ -d ".github/agents" ] || fail "canonical agents dir missing: .github/agents"
[ -f ".github/agents/orchestrator.agent.md" ] \
    || fail "missing canonical agent file: .github/agents/orchestrator.agent.md"
[ -f ".github/agents/developer.agent.md" ] \
    || fail "missing canonical agent file: .github/agents/developer.agent.md"

# The plain-`.md` extension under .github/agents is NOT the contract.
if [ -f ".github/agents/orchestrator.md" ]; then
    fail "found legacy extension .github/agents/orchestrator.md — expected .agent.md"
fi

# 2. The legacy Copilot agent directory must not exist (default-on migration).
[ ! -d ".github/copilot/agents" ] \
    || fail "legacy agents dir still present: .github/copilot/agents"

# 3. Rules land under .github/instructions/.
[ -d ".github/instructions" ] || fail "instructions dir missing: .github/instructions"
[ -f ".github/instructions/branch-guard.md" ] \
    || fail "missing instruction file: .github/instructions/branch-guard.md"

# 4. Native context file path.
[ -f ".github/copilot-instructions.md" ] \
    || fail "missing Copilot context file: .github/copilot-instructions.md"

echo "ASSERT OK (67-copilot-artifact-paths): .github/agents/*.agent.md + instructions + copilot-instructions.md; legacy .github/copilot/agents absent"
