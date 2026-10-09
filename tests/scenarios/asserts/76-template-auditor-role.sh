#!/bin/bash
# Scenario assert for 76-template-auditor-role
# (feature #936: read-only template-auditor role extracted from agent-meta-manager).
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# --validate. This scenario proves the generated `template-auditor`:
#   1. is generated at all for every active provider,
#   2. is READ-ONLY — no `Write`/`Edit`/`Agent` in its tools frontmatter, and
#      `edit: deny` in the Opencode permission block,
#   3. has no `model:` field in its SOURCE template (models come from
#      tier-presets/role-defaults, never from the template),
#   4. resolves all placeholders except escaped doc examples,
#   5. is NOT name-addressable via keyword routing in the generated
#      route_intent tool definition (addressability: name_only),
#   6. still carries the mandatory STATUS/RESULT/ARTIFACTS output contract.
# Exit 0 = all assertions hold.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (76-template-auditor-role): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (76-template-auditor-role): $*"
    exit 1
}

# 1. generated for both active providers (Claude + Opencode).
for prov in .claude .opencode; do
    [ -f "$prov/agents/template-auditor.md" ] || fail "template-auditor.md missing for $prov"
done

# 2. read-only tool set in the Claude frontmatter.
CLAUDE_TOOLS="$(sed -n '/^---$/,/^---$/p' .claude/agents/template-auditor.md | sed -n '/^tools:/,/^[a-z]/p')"
for forbidden in Write Edit Agent; do
    if printf '%s\n' "$CLAUDE_TOOLS" | grep -qE "^[-[:space:]]*${forbidden}\$"; then
        fail "read-only role declares forbidden tool '${forbidden}' in Claude frontmatter"
    fi
done
# Opencode must deny edits explicitly.
grep -q 'edit: deny' .opencode/agents/template-auditor.md \
    || fail "Opencode permission block does not deny edit (read-only role)"

# 3. source template declares no model: field (model resolution stays in config).
SOURCE="$REPO_ROOT/agents/1-generic/template-auditor.md"
[ -f "$SOURCE" ] || fail "source template missing: $SOURCE"
if sed -n '/^---$/,/^---$/p' "$SOURCE" | grep -qE '^model:'; then
    fail "source template declares a model: field — model resolution belongs in tier-presets/role-defaults"
fi

# 4. unresolved placeholders: only the escaped doc example {{ALLEVAR}} may survive.
for prov in .claude .opencode; do
    leftover="$(grep -oE '\{\{[A-Za-z][A-Za-z0-9_]*\}\}' "$prov/agents/template-auditor.md" | sort -u | grep -v '^{{ALLEVAR}}$' || true)"
    if [ -n "$leftover" ]; then
        fail "$prov output has unresolved placeholders: $leftover"
    fi
done

# 5. addressability name_only: the role must NOT appear in the generated
#    route_intent target_agent enum (that enum lists keyword-addressable roles).
if grep -q '"target_agent"' .claude/agents/orchestrator.md 2>/dev/null; then
    if python3 - <<'PY'
import re, sys, pathlib
t = pathlib.Path(".claude/agents/orchestrator.md").read_text(encoding="utf-8")
m = re.search(r'"enum":\s*\[(.*?)\]', t, re.S)
if not m:
    sys.exit(0)  # no routing tool block (no-routing-tool provider) — nothing to assert
enum = re.findall(r'"([a-z0-9-]+)"', m.group(1))
sys.exit(1 if "template-auditor" in enum else 0)
PY
    then
        fail "template-auditor appears in the route_intent target_agent enum (addressability must be name_only)"
    fi
fi

# 6. mandatory output contract markers present.
for marker in 'STATUS:' 'RESULT:' 'ARTIFACTS:'; do
    grep -q "$marker" .claude/agents/template-auditor.md \
        || fail "output contract marker '$marker' missing"
done

echo "ASSERT OK (76-template-auditor-role): generated, read-only, no model field, placeholders resolved, name_only routing, output contract present"
