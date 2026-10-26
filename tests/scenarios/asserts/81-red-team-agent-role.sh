#!/bin/bash
# Scenario assert for 81-red-team-agent-role
# (IC-28 Nr. 6, review round 2: red-team-agent).
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. This scenario proves the generated `red-team-agent`:
#   1. is generated for every active provider,
#   2. declares no Write/Edit/Agent tool and Opencode denies edits,
#   3. has no `model:` in its SOURCE template,
#   4. leaves no unresolved placeholder,
#   5. is name_only addressable (no keyword rule, but present in target_agents),
#   6. carries its output-contract markers.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (81-red-team-agent-role): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (81-red-team-agent-role): $*"
    exit 1
}

for prov in .claude .opencode; do
    [ -f "$prov/agents/red-team-agent.md" ] || fail "red-team-agent.md missing for $prov"
done

CLAUDE_TOOLS="$(sed -n '/^---$/,/^---$/p' .claude/agents/red-team-agent.md | sed -n '/^tools:/,/^[a-z]/p')"
for forbidden in Write Edit Agent; do
    if printf '%s\n' "$CLAUDE_TOOLS" | grep -qE "^[-[:space:]]*${forbidden}\$"; then
        fail "red-team-agent declares forbidden tool '${forbidden}'"
    fi
done
grep -q 'edit: deny' .opencode/agents/red-team-agent.md || fail "Opencode does not deny edit for red-team-agent"

SOURCE="$REPO_ROOT/agents/1-generic/red-team-agent.md"
[ -f "$SOURCE" ] || fail "source template missing: $SOURCE"
if sed -n '/^---$/,/^---$/p' "$SOURCE" | grep -qE '^model:'; then
    fail "source template declares a model: field"
fi

for prov in .claude .opencode; do
    leftover="$(grep -oE '\{\{[A-Za-z][A-Za-z0-9_]*\}\}' "$prov/agents/red-team-agent.md" | sort -u || true)"
    if [ -n "$leftover" ]; then
        fail "$prov output has unresolved placeholders: $leftover"
    fi
done

REPO_ROOT="$REPO_ROOT" python3 - <<'PY' || fail "red-team-agent routing is not name_only"
import os, sys
sys.path.insert(0, os.environ["REPO_ROOT"])
from pathlib import Path
from scripts.lib.delegation_table import get_routing_rules
rules = get_routing_rules(Path(os.environ["REPO_ROOT"]), {}, {})
if any(r.get("agent") == "red-team-agent" for r in rules["rules"]):
    sys.exit(1)
if "red-team-agent" not in rules["target_agents"]:
    sys.exit(1)
entry = [n for n in rules["name_index"] if n.get("agent") == "red-team-agent"]
sys.exit(0 if entry and entry[0].get("addressability") == "name_only" else 1)
PY

for marker in 'STATUS:' 'RESULT:' 'ARTIFACTS:' 'redteam-findings-v1'; do
    grep -q "$marker" .claude/agents/red-team-agent.md || fail "contract marker '$marker' missing"
done

echo "ASSERT OK (81-red-team-agent-role): generated, no Write/Edit tools, no model field, placeholders resolved, name_only routing, contract markers present"
