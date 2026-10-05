#!/bin/bash
# Scenario assert for 02-multi-provider
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (02-multi-provider): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (02-multi-provider): $*"
    exit 1
}

# Expected files/directories for this scenario
[ -f "CLAUDE.md" ] || fail "root provider file missing: CLAUDE.md"
[ -d ".claude/agents" ] || fail "agent directory missing for Claude: .claude/agents"
[ -f "AGENTS.md" ] || fail "root provider file missing: AGENTS.md"
[ -d ".gemini/agents" ] || fail "agent directory missing for Gemini: .gemini/agents"
[ -d ".opencode/agents" ] || fail "agent directory missing for Opencode: .opencode/agents"
[ -d ".continue/agents" ] || fail "agent directory missing for Continue: .continue/agents"

# --- issue #849 follow-up: no-MCP project must not trip the artifact gate ----
# This scenario configures no MCP servers, so the generated opencode.json
# carries isolation/permission keys but NO top-level 'mcp' object. An absent
# 'mcp' object is valid ("no MCP servers configured"); the sync-time artifact
# gate must stay clean instead of producing the false positive that broke 12
# scenarios. The first probe keeps this a real no-MCP case: if a future edit
# adds MCP config here, the guard fails loudly rather than silently weakening.
python3 - <<'PY' || fail "opencode.json unexpectedly declares MCP content (no-MCP guard would be vacuous)"
import json

with open("opencode.json", encoding="utf-8") as fh:
    doc = json.load(fh)
assert "mcp" not in doc, f"expected no top-level 'mcp' (got {doc.get('mcp')!r})"
PY

python3 "$REPO_ROOT/scripts/sync.py" --check >/dev/null 2>&1 \
    || fail "sync.py --check must exit 0 for a project without MCP servers"

echo "ASSERT OK (02-multi-provider): all marker files present"
