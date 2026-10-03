#!/bin/bash
# Scenario assert for 70-bootstrap-marker-convergence
# (design §3.5 / DECISION-4, AC-10 + AC-16: scoped bootstrap markers).
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# --validate. Gemini and ZCode both inject session-start bootstrap instructions
# into the shared AGENTS.md, so this scenario proves:
#   1. after the first sync there is exactly ONE provider-scoped marker pair per
#      injecting provider (`:Gemini` / `:ZCode`) and NO legacy id-less pair,
#   2. a legacy unscoped pair injected by an older agent-meta version is
#      discarded on the next sync while a user note outside the markers survives,
#   3. the result is a fixpoint: a further sync is byte-identical (convergence).
# Exit 0 = all assertions hold.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (70-bootstrap-marker-convergence): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (70-bootstrap-marker-convergence): $*"
    exit 1
}

AGENTS="AGENTS.md"
[ -f "$AGENTS" ] || fail "context file missing: $AGENTS"

# 1. Post-sync state: exactly one scoped pair per injecting provider, no legacy.
if ! python3 - "$AGENTS" <<'PY'
import re
import sys

text = open(sys.argv[1], encoding="utf-8").read()

for marker_id in ("Gemini", "ZCode"):
    begin = f"<!-- agent-meta:bootstrap-begin:{marker_id} -->"
    end = f"<!-- agent-meta:bootstrap-end:{marker_id} -->"
    assert text.count(begin) == 1, f"{marker_id}: begin marker count {text.count(begin)}"
    assert text.count(end) == 1, f"{marker_id}: end marker count {text.count(end)}"
    assert text.index(begin) < text.index(end), f"{marker_id}: begin after end"

# Exactly the two injecting providers -> exactly two begin/end markers overall.
assert text.count("agent-meta:bootstrap-begin") == 2, text.count("agent-meta:bootstrap-begin")
assert text.count("agent-meta:bootstrap-end") == 2, text.count("agent-meta:bootstrap-end")

# No legacy id-less pair (old schema) may survive the scoped migration.
assert not re.search(r"<!--\s*agent-meta:bootstrap-begin\s*-->", text), "legacy begin marker present"
assert not re.search(r"<!--\s*agent-meta:bootstrap-end\s*-->", text), "legacy end marker present"
PY
then
    fail "post-sync scope assertions failed"
fi

# 2. Simulate an upgrade: a user note outside the markers plus a legacy id-less
#    pair written by an older agent-meta. The next sync must drop the legacy
#    pair, keep the user note and keep the scoped pair single.
NOTE="USER-NOTE-KEEP-70"
printf '\n## Eigene Notizen\n\n%s\n\n<!-- agent-meta:bootstrap-begin -->\nlegacy unscoped block that must be discarded\n<!-- agent-meta:bootstrap-end -->\n' "$NOTE" >> "$AGENTS"

run2_rc=0
python3 "$REPO_ROOT/scripts/sync.py" > run2.log 2>&1 || run2_rc=$?
[ "$run2_rc" -eq 0 ] || { cat run2.log; fail "post-seed sync rc=$run2_rc"; }

[ "$(grep -c -F "$NOTE" "$AGENTS")" -eq 1 ] \
    || fail "user note lost or duplicated across the migration sync"

if ! python3 - "$AGENTS" <<'PY'
import re
import sys

text = open(sys.argv[1], encoding="utf-8").read()

for marker_id in ("Gemini", "ZCode"):
    begin = f"<!-- agent-meta:bootstrap-begin:{marker_id} -->"
    end = f"<!-- agent-meta:bootstrap-end:{marker_id} -->"
    assert text.count(begin) == 1, f"{marker_id}: begin marker count {text.count(begin)}"
    assert text.count(end) == 1, f"{marker_id}: end marker count {text.count(end)}"

assert text.count("agent-meta:bootstrap-begin") == 2, text.count("agent-meta:bootstrap-begin")
assert text.count("agent-meta:bootstrap-end") == 2, text.count("agent-meta:bootstrap-end")
assert not re.search(r"<!--\s*agent-meta:bootstrap-begin\s*-->", text), "legacy begin marker survived"
assert not re.search(r"<!--\s*agent-meta:bootstrap-end\s*-->", text), "legacy end marker survived"
PY
then
    fail "migration assertions failed (legacy not discarded / marker duplicated)"
fi

# 3. Convergence: the migrated file is a fixpoint — one more sync mutates nothing.
before="$(sha256sum "$AGENTS" | cut -d' ' -f1)"
run3_rc=0
python3 "$REPO_ROOT/scripts/sync.py" > run3.log 2>&1 || run3_rc=$?
[ "$run3_rc" -eq 0 ] || { cat run3.log; fail "convergence sync rc=$run3_rc"; }
after="$(sha256sum "$AGENTS" | cut -d' ' -f1)"
[ "$before" = "$after" ] \
    || fail "AGENTS.md is not a fixpoint across syncs ($before != $after)"

echo "ASSERT OK (70-bootstrap-marker-convergence): one scoped marker pair per provider; legacy pair discarded; user note preserved; sync is a fixpoint"
