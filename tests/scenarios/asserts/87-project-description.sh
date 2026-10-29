#!/bin/bash
# Scenario assert for 87-project-description (issue #1037).
#
# The config sets `project.description` but NO variables.PROJECT_DESCRIPTION, and
# no variables.AGENT_META_REPO. Both are derivable, so a sync must not ship the
# literal tokens: the description has to reach the generated context files and
# the agent-meta repo slug has to be derived from the checkout.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (87-project-description): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (87-project-description): $*"
    exit 1
}

[ -f ".claude/agents/meta-feedback.md" ] || fail "generated file missing: .claude/agents/meta-feedback.md"

# 1. project.description seeded PROJECT_DESCRIPTION into the context file.
#    (The context renderer wraps long lines, so match a distinctive prefix.)
grep -q "Description seeded from the project block" CLAUDE.md \
    || fail "CLAUDE.md: project.description did not reach PROJECT_DESCRIPTION"

# 2. No literal token survives in a generated artifact.
if grep -rq "{{PROJECT_DESCRIPTION}}" CLAUDE.md .claude/agents/ 2>/dev/null; then
    fail "unresolved {{PROJECT_DESCRIPTION}} in generated output"
fi
if grep -rq "{{AGENT_META_REPO}}" .claude/agents/; then
    fail "unresolved {{AGENT_META_REPO}} in generated output (derivation missing)"
fi

# 3. The derived repo is a real owner/repo slug, not an empty value.
grep -Eq '\*\*agent-meta repo:\*\* [A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+' .claude/agents/meta-feedback.md \
    || fail "meta-feedback.md: AGENT_META_REPO did not render as owner/repo"

echo "ASSERT OK (87-project-description): project.description seeded, AGENT_META_REPO derived"
