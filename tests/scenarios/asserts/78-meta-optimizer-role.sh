#!/bin/bash
# Scenario assert for 78-meta-optimizer-role
# (IC-28/AC-59, Task 2e.2: read-only meta-optimizer proposal role).
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# --validate. This scenario proves the generated `meta-optimizer`:
#   1. is generated at all for every active provider,
#   2. has ONLY Read/Glob/Grep/TodoWrite in the Claude tools frontmatter
#      (no Bash/Write/Edit/Agent) and `edit: deny` in the Opencode permission,
#   3. has no `model:` field in its SOURCE template,
#   4. resolves all placeholders except the escaped doc example `{{ALLEVAR}}`,
#   5. has NO keyword rule in routing rules (addressability: name_only; it stays
#      name-dispatchable via target_agents/name_index),
#   6. carries the config-patch-proposal-v1 output contract markers,
#   7. grants no execution channel (no Bash tool, explicit "no Bash" wording,
#      no command lines).
# Exit 0 = all assertions hold.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (78-meta-optimizer-role): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (78-meta-optimizer-role): $*"
    exit 1
}

# 1. generated for both active providers (Claude + Opencode).
for prov in .claude .opencode; do
    [ -f "$prov/agents/meta-optimizer.md" ] || fail "meta-optimizer.md missing for $prov"
done

# 2. exact read-only tool set in the Claude frontmatter: only
#    Read/Glob/Grep/TodoWrite, never Bash/Write/Edit/Agent.
CLAUDE_TOOLS="$(sed -n '/^---$/,/^---$/p' .claude/agents/meta-optimizer.md | sed -n '/^tools:/,/^[a-z]/p')"
for forbidden in Bash Write Edit Agent; do
    if printf '%s\n' "$CLAUDE_TOOLS" | grep -qE "^[-[:space:]]*${forbidden}\$"; then
        fail "meta-optimizer declares forbidden tool '${forbidden}' in Claude frontmatter"
    fi
done
TOOLS_ONLY="$(awk '/^---$/{c++; next} c==1' .claude/agents/meta-optimizer.md \
    | sed -n '/^tools:/,$p' \
    | sed -n 's/^[[:space:]]*-[[:space:]]*//p' \
    | tr -d ' \t\r' | sort | tr '\n' ' ')"
[ "$TOOLS_ONLY" = "Glob Grep Read TodoWrite " ] \
    || fail "Claude tools must be exactly Read/Glob/Grep/TodoWrite, got: $TOOLS_ONLY"
# Opencode must deny edits explicitly.
grep -q 'edit: deny' .opencode/agents/meta-optimizer.md \
    || fail "Opencode permission block does not deny edit (no write tools)"

# 3. source template declares no model: field (model resolution stays in config).
SOURCE="$REPO_ROOT/agents/1-generic/meta-optimizer.md"
[ -f "$SOURCE" ] || fail "source template missing: $SOURCE"
if sed -n '/^---$/,/^---$/p' "$SOURCE" | grep -qE '^model:'; then
    fail "source template declares a model: field — model resolution belongs in tier-presets/role-defaults"
fi

# 4. unresolved placeholders: only the escaped doc example {{ALLEVAR}} may survive.
for prov in .claude .opencode; do
    leftover="$(grep -oE '\{\{[A-Za-z][A-Za-z0-9_]*\}\}' "$prov/agents/meta-optimizer.md" | sort -u | grep -v '^{{ALLEVAR}}$' || true)"
    if [ -n "$leftover" ]; then
        fail "$prov output has unresolved placeholders: $leftover"
    fi
done

# 5. addressability name_only: no keyword rule for the role in routing.rules
#    (IC-28 Nr. 6); it must still be name-dispatchable (target_agents + name_index).
REPO_ROOT="$REPO_ROOT" python3 - <<'PY' || fail "meta-optimizer routing is not name_only (keyword rule present or name entry missing)"
import os, sys
sys.path.insert(0, os.environ["REPO_ROOT"])
from pathlib import Path
from scripts.lib.delegation_table import get_routing_rules

rules = get_routing_rules(Path(os.environ["REPO_ROOT"]), {}, {})
if any(r.get("agent") == "meta-optimizer" for r in rules["rules"]):
    sys.exit(1)
if "meta-optimizer" not in rules["target_agents"]:
    sys.exit(1)
entry = [n for n in rules["name_index"] if n.get("agent") == "meta-optimizer"]
sys.exit(0 if entry and entry[0].get("addressability") == "name_only" else 1)
PY

# 6. mandatory config-patch-proposal-v1 output contract markers present.
for marker in 'STATUS:' 'RESULT:' 'ARTIFACTS:' 'PROPOSALS:' 'PROOF:' 'config-patch-proposal-v1'; do
    grep -q "$marker" .claude/agents/meta-optimizer.md \
        || fail "output contract marker '$marker' missing"
done

# 7. read-only role: no execution channel. No Bash tool was granted above; the
#    generated text must say it has no Bash and must not contain command lines.
for prov in .claude .opencode; do
    f="$prov/agents/meta-optimizer.md"
    grep -q 'no Bash' "$f" || fail "$f does not state that the role has no Bash"
    if grep -qE '^[[:space:]]*(python3?|bash|sh|git|sync\.py)[[:space:]]' "$f"; then
        fail "$f contains an executable command line (read-only role)"
    fi
done

echo "ASSERT OK (78-meta-optimizer-role): generated, exact read-only tool set (no Bash/Write/Edit/Agent), edit: deny, no model field, placeholders resolved, name_only routing (no keyword rule), config-patch-proposal-v1 contract present, no execution channel"
