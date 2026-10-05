#!/bin/bash
# Scenario assert for 07-new-providers
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (07-new-providers): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (07-new-providers): $*"
    exit 1
}

# Expected files/directories for this scenario
[ -f "AGENTS.md" ] || fail "root provider file missing: AGENTS.md"
[ -d ".agents" ] || fail "agent directory missing for Codex: .agents"
[ -d ".zcode/agents" ] || fail "agent directory missing for ZCode: .zcode/agents"
[ -d ".kimi-code/agents" ] || fail "agent directory missing for KimiCode: .kimi-code/agents"

# Issue #807 (F18): command surface is capability-driven.
# ZCode declares commands: true → generated commands land in .zcode/commands/.
[ -d ".zcode/commands" ] || fail "ZCode command dir missing: .zcode/commands (issue #807)"
[ -f ".zcode/commands/commit.md" ] || fail "ZCode command not emitted: .zcode/commands/commit.md"
# Codex and KimiCode have no project-scoped command surface → nothing emitted.
[ ! -d ".codex/prompts" ] || fail "Codex must not emit commands (no project surface, issue #807)"
[ ! -d ".kimi-code/commands" ] || fail "KimiCode must not emit a commands dir (no command surface, issue #807)"

echo "ASSERT OK (07-new-providers): all marker files present"
