#!/bin/bash
# Scenario assert for 49-hacs-entity-naming
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (49-hacs-entity-naming): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (49-hacs-entity-naming): $*"
    exit 1
}

SKILL=".claude/skills/integration-development/SKILL.md"
REVIEWER=".claude/agents/code-reviewer.md"
RELEASE=".claude/agents/release.md"

# (1) rule rendered as a lazy-loaded skill (requires rules-preset: lazy)
[ -f "$SKILL" ] || fail "missing $SKILL (is rules-preset 'lazy' set?)"

# (2) entity-naming + rename-migration reference tokens are present in the skill body
for token in _attr_has_entity_name _attr_translation_key async_migrate_entries new_entity_id original_name; do
    grep -q "$token" "$SKILL" || fail "skill body missing token: $token"
done

# (3) strings.json English-master skeleton is present.
# Negative marker is 'Aktualisierungsintervall' (the old German master's options string,
# replaced by 'Update interval (seconds)' and omitted from the derived de.json example).
# We deliberately do NOT negate-check 'Verbindung einrichten': the R4 derived
# translations/de.json example legitimately contains it, so that check would false-fail.
grep -q '"Set up connection"' "$SKILL" || fail "skill body missing English master string '\"Set up connection\"'"
grep -q 'Aktualisierungsintervall' "$SKILL" && fail "skill body still contains the old German master string 'Aktualisierungsintervall'"

# (4) reviewer Gate 11 marker
grep -q 'Namenslokalisierung' "$REVIEWER" || fail "code-reviewer.md missing Gate-11 marker 'Namenslokalisierung'"

# (5) release notes rename-breaking marker
grep -q 'Umbenennung' "$RELEASE" || fail "release.md missing 'Umbenennung'"
grep -q '💥' "$RELEASE" || fail "release.md missing '💥' breaking marker"

echo "ASSERT OK (49-hacs-entity-naming): entity-naming contract, migration, Gate 11 and release markers verified"
