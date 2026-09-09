#!/bin/bash
# Scenario assert for 41-quality-pipelines-custom.
#
# A custom-pipelines entry is merged into the effective pipeline set and
# rendered into the orchestrator's aggregate PIPELINE_DETAIL_BLOCKS as a
# '### `<name>`' section.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (41-quality-pipelines-custom): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (41-quality-pipelines-custom): $*"
    exit 1
}

[ -f ".claude/agents/orchestrator.md" ] || fail "generated file missing: .claude/agents/orchestrator.md"

grep -q "my-custom-check" .claude/agents/orchestrator.md \
    || fail "orchestrator.md: custom pipeline 'my-custom-check' not rendered into pipeline detail blocks"

echo "ASSERT OK (41-quality-pipelines-custom): custom pipeline rendered into orchestrator"
