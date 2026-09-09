#!/bin/bash
# Scenario assert for 28-platform-defaults-no-platforms-regression.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (28-platform-defaults-no-platforms-regression): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (28-platform-defaults-no-platforms-regression): $*"
    exit 1
}

[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
grep -q "DoD-Preset: \*\*full\*\*" CLAUDE.md \
    || fail "CLAUDE.md: expected the old implicit 'full' dod-preset default (no platforms:, no project override)"

RESOLVED=".meta-config/platform-defaults.resolved.yaml"
[ -f "$RESOLVED" ] || fail "resolved-defaults file missing: $RESOLVED"
python3 - "$RESOLVED" <<'PY' || exit 1
import sys
import yaml

with open(sys.argv[1], encoding="utf-8") as fh:
    data = yaml.safe_load(fh)

if data.get("dod-preset") is not None:
    print(f"ASSERT FAIL (28-platform-defaults-no-platforms-regression): expected dod-preset: null, got {data.get('dod-preset')!r}")
    sys.exit(1)
if data.get("variables"):
    print(f"ASSERT FAIL (28-platform-defaults-no-platforms-regression): expected empty variables, got {data.get('variables')!r}")
    sys.exit(1)
PY

echo "ASSERT OK (28-platform-defaults-no-platforms-regression): absent platforms: key -> empty cascade, old 'full' fallback unchanged"
