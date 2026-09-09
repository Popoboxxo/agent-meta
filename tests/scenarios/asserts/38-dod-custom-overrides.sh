#!/bin/bash
# Scenario assert for 38-dod-custom-overrides.
#
# rapid-prototyping sets every DoD flag to false. The project dod: dict flips
# req-traceability and security-audit on; the CLAUDE.md config summary line
# must reflect the overrides while the untouched flags keep the preset value.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (38-dod-custom-overrides): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (38-dod-custom-overrides): $*"
    exit 1
}

[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"

grep -q "REQ-Traceability: true" CLAUDE.md \
    || fail "CLAUDE.md: expected 'REQ-Traceability: true' from dod override (preset default is false)"
grep -q "Security-Audit: true" CLAUDE.md \
    || fail "CLAUDE.md: expected 'Security-Audit: true' from dod override (preset default is false)"
# Untouched criterion keeps the rapid-prototyping preset value.
grep -q "Tests: false" CLAUDE.md \
    || fail "CLAUDE.md: expected 'Tests: false' (untouched rapid-prototyping preset value)"

echo "ASSERT OK (38-dod-custom-overrides): individual dod overrides win, untouched criteria keep preset values"
