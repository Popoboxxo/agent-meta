#!/bin/bash
# Scenario assert for 44-speech-mode-childish.
#
# Default speech-mode 'full' generates NO rule file. Any other mode copies
# speech/<mode>.md to .claude/rules/speech-mode.md.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (44-speech-mode-childish): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (44-speech-mode-childish): $*"
    exit 1
}

[ -f ".claude/rules/speech-mode.md" ] \
    || fail "expected .claude/rules/speech-mode.md to be generated for a non-default speech-mode"

grep -q "Kommunikationsstil: Childish" .claude/rules/speech-mode.md \
    || fail "speech-mode.md: expected the 'childish' rule content, not found"

echo "ASSERT OK (44-speech-mode-childish): childish speech-mode rule generated"
