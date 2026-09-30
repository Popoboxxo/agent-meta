#!/bin/bash
# Scenario assert for 62-stale-role-cleanup
# (SPEC-STALE-ROLE-CLEANUP-2026-09-13, AC-10 preview / AC-15 foreign / AC-19 rollback).
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# --validate. This scenario manufactures a stale (index-tracked) agent file and
# a foreign (marker-less) one, then proves:
#   1. `--cleanup-preview` classifies both correctly and mutates nothing,
#   2. applying (a real sync) removes the stale file backup-first while the
#      foreign file survives byte-identically.
# Exit 0 = all assertions hold.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (62-stale-role-cleanup): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (62-stale-role-cleanup): $*"
    exit 1
}

AGENTS_DIR=".claude/agents"
INDEX="$AGENTS_DIR/.agent-meta-managed"
STALE="$AGENTS_DIR/stale-role.md"
FOREIGN="$AGENTS_DIR/foreign-notes.md"

[ -d "$AGENTS_DIR" ] || fail "agents dir missing: $AGENTS_DIR"
[ -f "$INDEX" ] || fail "managed index missing: $INDEX"

# 1. Manufacture a stale (index-tracked, provenance-marked) agent file and a
#    foreign (marker-less, not index-listed) agent file.
{
    printf '%s\n' '---'
    printf '%s\n' 'name: stale-role'
    printf '%s\n' 'generated-from: 1-generic/stale-role.md@1.0.0'
    printf '%s\n' '---'
    printf '%s\n' 'body'
} > "$STALE"
printf '%s\n' 'hand-authored notes' > "$FOREIGN"
printf '%s\n' 'stale-role.md' >> "$INDEX"

stale_before="$(cat "$STALE")"
foreign_before="$(cat "$FOREIGN")"
index_before="$(cat "$INDEX")"

# 2. Preview: rc 0, one JSON object, stale vs foreign classification.
preview_rc=0
python3 "$REPO_ROOT/scripts/sync.py" --cleanup-preview > preview.json 2> preview.err || preview_rc=$?
[ "$preview_rc" -eq 0 ] || { cat preview.err; fail "cleanup preview rc=$preview_rc"; }

if ! python3 - "$STALE" "$FOREIGN" <<'PY'
import json
import sys

stale_path, foreign_path = sys.argv[1], sys.argv[2]
with open("preview.json", encoding="utf-8") as fh:
    payload = json.load(fh)

assert payload.get("version") == 1, payload.get("version")
assert str(payload.get("fingerprint", "")).startswith("sha256:"), payload.get("fingerprint")
providers = payload.get("providers")
assert isinstance(providers, list) and providers, "no providers in preview"

stale_entries = [e for p in providers for e in p.get("stale", [])]
foreign_entries = {e["path"]: e for p in providers for e in p.get("foreign", [])}
stale_by_path = {e["path"]: e for e in stale_entries}

assert stale_path in stale_by_path, f"stale {stale_path!r} not reported: {sorted(stale_by_path)}"
stale = stale_by_path[stale_path]
assert stale["reason"] == "role removed from config", stale
assert stale["tracked"] is True and stale["adopted"] is False, stale
assert stale_path not in foreign_entries, "stale file must not also be foreign"

assert foreign_path in foreign_entries, f"foreign {foreign_path!r} not reported: {sorted(foreign_entries)}"
assert foreign_entries[foreign_path]["legacy_unmarked"] is True, foreign_entries[foreign_path]

assert all(isinstance(p.get("backups_to_prune"), list) for p in providers)
PY
then
    fail "preview classification assertions failed"
fi

# 3. Preview must be side-effect-free (no delete, no backup, no index write).
[ -f "$STALE" ] || fail "preview deleted the stale file"
[ -f "$FOREIGN" ] || fail "preview deleted the foreign file"
[ "$(cat "$STALE")" = "$stale_before" ] || fail "preview mutated the stale file"
[ "$(cat "$FOREIGN")" = "$foreign_before" ] || fail "preview mutated the foreign file"
[ "$(cat "$INDEX")" = "$index_before" ] || fail "preview rewrote the managed index"
[ -z "$(find "$AGENTS_DIR" -maxdepth 1 -name 'stale-role.md.sync-backup-*')" ] \
    || fail "preview created a backup sibling"

# 4. Apply (real sync) removes the stale file backup-first, foreign survives.
apply_rc=0
python3 "$REPO_ROOT/scripts/sync.py" > apply.log 2>&1 || apply_rc=$?
[ "$apply_rc" -eq 0 ] || { cat apply.log; fail "apply sync rc=$apply_rc"; }

[ ! -f "$STALE" ] || fail "apply did not remove the stale file"
[ -f "$FOREIGN" ] || fail "apply removed the foreign file"
[ "$(cat "$FOREIGN")" = "$foreign_before" ] || fail "apply mutated the foreign file"

backup="$(find "$AGENTS_DIR" -maxdepth 1 -name 'stale-role.md.sync-backup-*' -print -quit)"
[ -n "$backup" ] || fail "apply did not create a backup sibling"
[ "$(cat "$backup")" = "$stale_before" ] || fail "backup content != pre-delete content"

if grep -qx 'stale-role.md' "$INDEX"; then
    fail "apply did not drop the stale entry from the managed index"
fi

echo "ASSERT OK (62-stale-role-cleanup): preview classified stale/foreign mutation-free; apply removed stale backup-first, foreign survived"
