#!/bin/bash
# Scenario assert for 69-opencode-v2-surface.
# (SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30, AC-5 / AC-21 / OQ-4 / OQ-8.)
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# --validate.
#
# Two-part proof:
#   1. SHIPPED DEFAULT (v1 frozen): <REPO_ROOT>/config/ai-providers.yaml declares
#      `surface-version: "v1"` + the `surface-formats` map v1->opencode-json,
#      v2->opencode-json-v2, and the v1 fixture output keeps the flat top-level
#      `mcp` server map (no nested `mcp.servers`).
#   2. V2 SURFACE: with `surface-version: v2` the generator emits opencode.json
#      with nested `mcp.servers` and NO flat top-level `mcp` server map, drops the
#      v1-only `subagent_depth` key, emits the `default_agent` key (from
#      `primary-role: orchestrator`, `mode: primary`), and the emitted agent
#      frontmatter uses the v2 mechanism (orchestrator `mode: primary`, others
#      `mode: subagent`). Because `surface-version` is REGISTRY-level data (no
#      project.yaml key consumes it), the v2 run is exercised against a throwaway
#      framework copy in the temp dir — the real checkout is never mutated.
#   3. V2 VALIDATE (Task-18 regression guard): `sync.py --validate` is run on the
#      throwaway v2 project and must exit 0. The harness only runs --validate on
#      the primary (v1) project, so a v2-only artifact-contract violation (e.g.
#      an emitted frontmatter key missing from `agent-transform.allowed-fields`)
#      used to stay invisible.
# Exit 0 = all assertions hold.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (69-opencode-v2-surface): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (69-opencode-v2-surface): $*"
    exit 1
}

REGISTRY="$REPO_ROOT/config/ai-providers.yaml"
[ -f "$REGISTRY" ] || fail "registry missing: $REGISTRY"

# 1. Shipped default is v1 and the surface-formats selection data is present.
python3 - "$REGISTRY" <<'PY' || fail "shipped surface-version default / surface-formats contract violated"
import sys
try:
    import yaml
except ImportError:
    raise SystemExit(3)
with open(sys.argv[1], encoding="utf-8") as fh:
    providers = yaml.safe_load(fh)["providers"]
oc = providers["Opencode"]
assert oc.get("surface-version") == "v1", (
    f"shipped Opencode.surface-version must default to v1 (got {oc.get('surface-version')!r})"
)
mcp = oc.get("mcp-config") or {}
assert mcp.get("format") == "opencode-json", mcp
sf = mcp.get("surface-formats") or {}
assert sf.get("v1") == "opencode-json", sf
assert sf.get("v2") == "opencode-json-v2", sf
PY

# 1b. The v1 fixture output keeps the frozen flat `mcp` byte shape.
[ -f "opencode.json" ] || fail "v1 output missing: opencode.json"
python3 - opencode.json <<'PY' || fail "v1 opencode.json is not the frozen flat shape"
import json
import sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
mcp = doc.get("mcp")
assert isinstance(mcp, dict), "v1 opencode.json requires the flat top-level 'mcp' object"
assert "servers" not in mcp, "v1 flat 'mcp' must not carry a nested 'servers' key"
PY

# 2. Opt-in v2 surface (throwaway framework copy).
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
FW="$WORK/fw"
PROJ="$WORK/proj"
mkdir -p "$FW" "$PROJ/.meta-config"

# Copy the framework subtrees the generator AND `--validate` read. `schemas/`
# is required so the throwaway `--validate` run (step 3) resolves the
# `schema_ref`s declared by templates instead of failing on missing files.
for d in scripts config agents templates hooks rules schemas; do
    [ -e "$REPO_ROOT/$d" ] || continue
    cp -r "$REPO_ROOT/$d" "$FW/"
done
find "$FW" \( -name '*.pyc' -o -name '__pycache__' \) -exec rm -rf {} + 2>/dev/null || true

# Flip ONLY the Opencode entry's surface-version inside the throwaway copy.
python3 - "$FW/config/ai-providers.yaml" <<'PY' || fail "could not flip surface-version in throwaway copy"
import re
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
i = s.index("  Opencode:")
head, tail = s[:i], s[i:]
# Line-anchored (skips comment lines that may quote the literal) + count guard:
# exactly one real key may be rewritten, otherwise the opt-in run would be
# silently misconfigured.
tail, n = re.subn(
    r'(?m)^([ \t]*)surface-version:[ \t]*"v1"[ \t]*$',
    r'\1surface-version: "v2"',
    tail,
    count=1,
)
if n != 1:
    raise SystemExit(f"expected exactly one real surface-version key, replaced {n}")
open(p, "w", encoding="utf-8").write(head + tail)
PY

cat > "$PROJ/.meta-config/project.yaml" <<EOF
agent-meta-version: 0.101.0
ai-providers:
- Opencode
platforms: []
roles:
- orchestrator
- developer
plugins:
  playwright:
    enabled: true
project:
  name: assert69
  prefix: s69a
  short: assert69
variables:
  PROJECT_NAME: assert69
  PROJECT_DESCRIPTION: throwaway v2 run
  PROJECT_GOAL: prove the v2 surface (mcp.servers, default_agent, mode primary)
  GIT_PLATFORM: GitHub
  GIT_REMOTE_URL: https://github.com/example/assert69
  GIT_MAIN_BRANCH: main
rules-preset: default
speech-mode: full
tier-preset: Normal
se-focus: false
max-parallel-agents: 2
conventions-preset: default
debug-mode: false
allow-committed-secrets: false
EOF

(
    cd "$PROJ" || exit 1
    python3 "$FW/scripts/sync.py" > sync.log 2>&1
) || fail "v2 sync (surface-version: v2) failed — see $PROJ/sync.log"

# 2.1 Task-18 regression guard: the v2 throwaway must pass `--validate` (rc 0).
# The harness runs --validate on the primary v1 project only; a v2-only
# artifact-contract violation (an emitted key absent from
# agent-transform.allowed-fields) previously slipped through because this path
# ran sync alone.
(
    cd "$PROJ" || exit 1
    python3 "$FW/scripts/sync.py" --validate > validate.log 2>&1
) || {
    echo "----- v2 validate.log -----"
    cat "$PROJ/validate.log"
    fail "v2 --validate exited non-zero (expected 0)"
}

[ -f "$PROJ/opencode.json" ] || fail "v2 output missing: opencode.json"

# 2a. Nested mcp.servers, NO flat top-level mcp server map, no v1-only key.
python3 - "$PROJ/opencode.json" <<'PY' || fail "v2 opencode.json key-shape contract violated"
import json
import sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
mcp = doc.get("mcp")
assert isinstance(mcp, dict), "v2 opencode.json requires an 'mcp' object"
assert "servers" in mcp, "v2 'mcp' must be nested with a 'servers' object"
assert isinstance(mcp["servers"], dict), "'mcp.servers' must be an object"
flat = sorted(set(mcp) - {"servers"})
assert not flat, f"v2 'mcp' carries flat v1 server key(s): {flat}"
assert "subagent_depth" not in doc, "v2 must not carry the v1-only key 'subagent_depth'"
PY

# 2b. default_agent key + a primary-role entry (orchestrator, mode: primary).
python3 - "$PROJ/opencode.json" <<'PY' || fail "v2 default_agent key missing"
import json
import sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
assert "default_agent" in doc, (
    "v2 opencode.json must declare a 'default_agent' key (from primary-role)"
)
assert doc["default_agent"], "'default_agent' must be non-empty"
PY

python3 - "$PROJ/.opencode/agents/orchestrator.md" "$PROJ/.opencode/agents/developer.md" <<'PY' || fail "v2 frontmatter mechanism not applied"
import sys
def fm(path):
    text = open(path, encoding="utf-8").read()
    block = text.split("---", 2)[1]
    out = {}
    for line in block.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out
primary = fm(sys.argv[1])
sub = fm(sys.argv[2])
assert primary.get("mode") == "primary", (
    f"orchestrator (primary-role) must be mode: primary, got {primary.get('mode')!r}"
)
assert sub.get("mode") == "subagent", (
    f"non-primary role must be mode: subagent, got {sub.get('mode')!r}"
)
PY

echo "ASSERT OK (69-opencode-v2-surface): v2 emits nested mcp.servers + default_agent + mode: primary; v2 --validate rc 0; v1 flat byte shape frozen"
