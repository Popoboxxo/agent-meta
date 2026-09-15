#!/bin/bash
# Scenario assert for 61-hook-deploy-lf-newlines (#754).
#
# Root cause covered: scripts/lib/io.py::write_atomic opened its temp text file
# without newline=, so text-mode encoding translated "\n" to os.linesep — on
# Windows every deployed hook landed as CRLF and failed at runtime with
# `$'\r': command not found`. is_unchanged additionally compared through
# universal newlines, so the CRLF drift was never detected and never corrected.
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (61-hook-deploy-lf-newlines): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (61-hook-deploy-lf-newlines): $*"
    exit 1
}

# Portable "file contains a carriage return" check. `grep -U` (treat input as
# binary) is GNU-only, so use a literal CR pattern via printf instead — works
# with GNU and BSD/macOS grep alike. LC_ALL=C keeps the byte match stable.
contains_cr() {
    LC_ALL=C grep -q "$(printf '\r')" "$1"
}

# Sanity: the fix lives in the checkout this scenario syncs from.
grep -Fq '"newline": "\n"' "$REPO_ROOT/scripts/lib/io.py" \
    || fail "scripts/lib/io.py::write_atomic no longer forces LF via newline=\"\\n\""

# Scan every deployed hook script across all provider hook dirs present.
found=0
for dir in .claude/hooks .agents/hooks .mammouth/hooks .codex/hooks; do
    [ -d "$dir" ] || continue
    while IFS= read -r -d '' f; do
        found=$((found + 1))
        if contains_cr "$f"; then
            fail "deployed hook contains a carriage return (must be LF-only): $f"
        fi
    done < <(find "$dir" -type f -name '*.sh' -print0)
done

[ "$found" -gt 0 ] || fail "no deployed hook scripts found in any provider hook dir"

# Explicit coverage for the adapter that triggered the original bug report.
for f in .claude/hooks/antigravity-json-adapter.sh .agents/hooks/antigravity-json-adapter.sh; do
    [ -f "$f" ] || continue
    contains_cr "$f" && fail "antigravity-json-adapter.sh contains a carriage return: $f"
done

echo "ASSERT OK (61-hook-deploy-lf-newlines): $found deployed hook script(s) are LF-only"
