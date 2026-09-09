#!/bin/bash
# Scenario assert for 31-platform-defaults-unknown-platform.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (31-platform-defaults-unknown-platform): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (31-platform-defaults-unknown-platform): $*"
    exit 1
}

[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"

RESOLVED=".meta-config/platform-defaults.resolved.yaml"
[ -f "$RESOLVED" ] || fail "resolved-defaults file missing: $RESOLVED"
python3 - "$RESOLVED" <<'PY' || exit 1
import sys
import yaml

with open(sys.argv[1], encoding="utf-8") as fh:
    data = yaml.safe_load(fh)

if data.get("dod-preset") is not None:
    print(f"ASSERT FAIL (31-platform-defaults-unknown-platform): expected dod-preset: null for an unknown platform, got {data.get('dod-preset')!r}")
    sys.exit(1)
if data.get("conventions-preset") is not None:
    print(f"ASSERT FAIL (31-platform-defaults-unknown-platform): expected conventions-preset: null, got {data.get('conventions-preset')!r}")
    sys.exit(1)
if data.get("variables"):
    print(f"ASSERT FAIL (31-platform-defaults-unknown-platform): expected empty variables, got {data.get('variables')!r}")
    sys.exit(1)
PY

echo "ASSERT OK (31-platform-defaults-unknown-platform): unknown platform -> empty cascade, no crash"
