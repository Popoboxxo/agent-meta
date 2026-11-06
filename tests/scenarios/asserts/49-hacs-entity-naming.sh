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

# (2b) semantic check of the migration recipe (tokens alone do not prove an await).
# The first ```python fence under the migration heading must parse, await
# async_migrate_entries (direct operand of ast.Await) and call
# async_update_entry exactly once. Python errors exit non-zero (fail-closed).
python3 -I - "$SKILL" <<'PYEOF' || fail "migration recipe semantic check failed (see ASSERT FAIL line above)"
import ast
import re
import sys

HEADING = "### Entity-Registry-Migration bei Umbenennung"
path = sys.argv[1]


def fail(msg):
    print("ASSERT FAIL (49-hacs-entity-naming): " + msg)
    sys.exit(1)


try:
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
except OSError as exc:
    print("ASSERT ERROR (49-hacs-entity-naming): cannot read %s: %s" % (path, exc))
    sys.exit(2)

if HEADING not in text:
    fail("skill body missing migration heading: " + HEADING)
section = re.split(r"\n#{2,3} ", text.split(HEADING, 1)[1], maxsplit=1)[0]
fence = re.search(r"^```python\n(.*?)^```[ \t]*$", section, re.S | re.M)
if not fence:
    fail("no ```python fence under the migration heading")

try:
    tree = ast.parse(fence.group(1))
except SyntaxError as exc:
    fail("migration recipe fence does not parse: %s" % exc)

parents = {}
for node in ast.walk(tree):
    for child in ast.iter_child_nodes(node):
        parents[child] = node


def calls_to(attr):
    return [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == attr
    ]


migrate = calls_to("async_migrate_entries")
if len(migrate) != 1:
    fail("expected exactly 1 async_migrate_entries call in recipe, found %d" % len(migrate))
if not isinstance(parents.get(migrate[0]), ast.Await):
    fail("async_migrate_entries call is not awaited (missing 'await' on the coroutine)")

updates = calls_to("async_update_entry")
if len(updates) != 1:
    fail("expected exactly 1 async_update_entry call (single version bump), found %d" % len(updates))

print("ASSERT OK (49-hacs-entity-naming): recipe awaits async_migrate_entries, single async_update_entry")
PYEOF

# (3) strings.json English-master skeleton is present.
# Negative marker is 'Aktualisierungsintervall' (the old German master's options string,
# replaced by 'Update interval (seconds)' and omitted from the derived de.json example).
# We deliberately do NOT negate-check 'Verbindung einrichten': the R4 derived
# translations/de.json example legitimately contains it, so that check would false-fail.
grep -q '"Set up connection"' "$SKILL" || fail "skill body missing English master string '\"Set up connection\"'"
grep -q 'Aktualisierungsintervall' "$SKILL" && fail "skill body still contains the old German master string 'Aktualisierungsintervall'"

# (4) reviewer Gate 11 marker
grep -q 'Namenslokalisierung' "$REVIEWER" || fail "code-reviewer.md missing Gate-11 marker 'Namenslokalisierung'"

# (4b) reviewer F4 fail-predicate must spell the awaited call (single-line match)
grep -q '\*\*F4\*\*.*await er\.async_migrate_entries' "$REVIEWER" || fail "code-reviewer.md F4 line does not require 'await er.async_migrate_entries'"

# (5) release notes rename-breaking marker
grep -q 'Umbenennung' "$RELEASE" || fail "release.md missing 'Umbenennung'"
grep -q '💥' "$RELEASE" || fail "release.md missing '💥' breaking marker"

echo "ASSERT OK (49-hacs-entity-naming): entity-naming contract, migration, Gate 11 and release markers verified"
