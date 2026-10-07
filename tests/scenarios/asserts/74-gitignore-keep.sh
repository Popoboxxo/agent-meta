#!/bin/bash
# Scenario assert for 74-gitignore-keep (issue #746).
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The ordering bug (sorted() neutralizing the
# re-include negation) is INVISIBLE to a grep/string check, so this assert
# git-inits the synced tree and uses REAL `git check-ignore`.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (74-gitignore-keep): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (74-gitignore-keep): $*"
    exit 1
}

[ -f ".gitignore" ] || fail "expected .gitignore to exist"
grep -q "^/.claude/\*$" .gitignore || fail "missing content-exclude /.claude/*"
grep -q "^!/.claude/3-project/$" .gitignore || fail "missing re-include !/.claude/3-project/"

# Real git check-ignore is the only reliable arbiter of the ordering bug.
git init -q . || fail "git init failed"
mkdir -p .claude/3-project .gemini/rules
: > .claude/3-project/NEW.md
: > .claude/settings.local.json
: > .gemini/rules/test-scope.md
: > .gemini/rules/generated.md

is_ignored() { git check-ignore -q "$1"; }

is_ignored ".claude/3-project/NEW.md" && fail "kept path wrongly ignored: .claude/3-project/NEW.md"
is_ignored ".gemini/rules/test-scope.md" && fail "kept file wrongly ignored: .gemini/rules/test-scope.md"
is_ignored ".claude/settings.local.json" || fail "non-kept file should stay ignored: .claude/settings.local.json"
is_ignored ".gemini/rules/generated.md" || fail "sibling of kept file should stay ignored: .gemini/rules/generated.md"

echo "ASSERT OK (74-gitignore-keep): keep paths re-included, siblings ignored (real git check-ignore)"
