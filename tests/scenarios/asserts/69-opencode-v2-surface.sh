#!/bin/bash
# Scenario assert for 69-opencode-v2-surface.
# (SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30 + amendment
#  SPEC-ADMIN-UI-OPENCODE-SURFACE-AMENDMENT-2026-10-03, AC-A2 / AC-A3 / D1/D2.)
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# --validate on the PRIMARY project.
#
# The scenario fixture (.meta-config/project.yaml) opts into v2 through the
# PROJECT CHANNEL `provider-options.Opencode.surface-version: v2` — the consumer
# never edits the framework registry. This assert proves the full chain
# project.yaml -> resolver -> sync output for v2, a v1/unset byte-identity
# baseline, and a fail-loud mismatch via `sync.py --check`.
#
# Parts:
#   1. SHIPPED DEFAULT (v1 frozen): <REPO_ROOT>/config/ai-providers.yaml declares
#      `surface-version: "v1"` + the `surface-formats` map v1->opencode-json,
#      v2->opencode-json-v2.
#   1b. V1 BYTE-IDENTITY: a scratch project generated with NO project-channel key
#      (and one with an explicit v1) keeps the flat v1 `mcp` shape and its output
#      is byte-identical to the pre-change baseline (no `default_agent`, flat
#      `mcp` server map, v1-only `subagent_depth` retained).
#   2. V2 PROJECT CHANNEL: the PRIMARY project (synced by the harness from the
#      fixture above) must emit the v2 shape/mechanism — nested `mcp.servers`, no
#      flat top-level server map, no v1-only `subagent_depth`, a `default_agent`
#      key, and v2 frontmatter (`orchestrator` mode: primary, others subagent).
#   3. V2 `--check` rc 0 on the consistent v2 tree; a v1 tree under the v2 project
#      yields a non-zero `--check` (no silent divergence).
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

# ---------------------------------------------------------------------------
# Scratch project generator (project-channel aware). Writes a minimal
# project.yaml under <dir>/.meta-config and runs the real sync against the
# SHIPPED framework; never touches the real checkout.
# ---------------------------------------------------------------------------
_write_project() {
    # $1 = project dir, $2 = prefix, $3 = "v1" | "unset"
    local dir="$1" prefix="$2" surface="$3"
    mkdir -p "$dir/.meta-config"
    cat > "$dir/.meta-config/project.yaml" <<EOF
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
  name: $prefix
  prefix: $prefix
  short: $prefix
variables:
  PROJECT_NAME: $prefix
  PROJECT_DESCRIPTION: scenario 69 scratch
  PROJECT_GOAL: prove project-channel surface selection
  GIT_PLATFORM: GitHub
  GIT_REMOTE_URL: https://github.com/example/$prefix
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
    if [ "$surface" = "v1" ]; then
        cat >> "$dir/.meta-config/project.yaml" <<'EOF'
provider-options:
  Opencode:
    surface-version: v1
EOF
    fi
    ( cd "$dir" && python3 "$REPO_ROOT/scripts/sync.py" > sync.log 2>&1 ) \
        || return 1
}

# --- 1b. v1/unset byte-identity (pre-change baseline is flat v1 shape). ------
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
PROJ_UNSET="$WORK/unset"
PROJ_V1="$WORK/v1"
_write_project "$PROJ_UNSET" "s69unset" "unset" || fail "unset v1 sync failed — see $PROJ_UNSET/sync.log"
_write_project "$PROJ_V1" "s69v1" "v1" || fail "explicit-v1 sync failed — see $PROJ_V1/sync.log"

[ -f "$PROJ_UNSET/opencode.json" ] || fail "unset output missing: opencode.json"

# Explicit v1 is byte-identical to the no-key default (project override is a no-op).
cmp -s "$PROJ_V1/opencode.json" "$PROJ_UNSET/opencode.json" \
    || fail "explicit surface-version: v1 is not byte-identical to unset v1 output"

# The v1 baseline keeps the frozen flat `mcp` shape and no v2 keys.
python3 - "$PROJ_UNSET/opencode.json" <<'PY' || fail "v1 opencode.json is not the frozen flat shape"
import json
import sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
mcp = doc.get("mcp")
assert isinstance(mcp, dict), "v1 opencode.json requires the flat top-level 'mcp' object"
assert "servers" not in mcp, "v1 flat 'mcp' must not carry a nested 'servers' key"
assert "default_agent" not in doc, "v1 must not carry the v2-only key 'default_agent'"
PY

# --- 2. PRIMARY v2 project (project channel, harness-synced). ----------------
[ -f "opencode.json" ] || fail "primary v2 output missing: opencode.json"

# 2a. The fixture actually uses the project channel (not a registry flip).
python3 - .meta-config/project.yaml <<'PY' || fail "primary project.yaml is not on the project channel"
import sys
try:
    import yaml
except ImportError:
    raise SystemExit(3)
with open(sys.argv[1], encoding="utf-8") as fh:
    project = yaml.safe_load(fh) or {}
opts = (project.get("provider-options") or {}).get("Opencode") or {}
assert opts.get("surface-version") == "v2", (
    f"fixture must opt into v2 via provider-options.Opencode (got {opts!r})"
)
PY

# 2b. Nested mcp.servers, NO flat top-level mcp server map, no v1-only key.
python3 - opencode.json <<'PY' || fail "v2 opencode.json key-shape contract violated"
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

# 2c. default_agent key + a primary-role entry (orchestrator, mode: primary).
python3 - opencode.json <<'PY' || fail "v2 default_agent key missing"
import json
import sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
assert "default_agent" in doc, (
    "v2 opencode.json must declare a 'default_agent' key (from primary-role)"
)
assert doc["default_agent"], "'default_agent' must be non-empty"
PY

python3 - .opencode/agents/orchestrator.md .opencode/agents/developer.md <<'PY' || fail "v2 frontmatter mechanism not applied"
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

# --- 3. `--check` agreement (AC-A3). ----------------------------------------
# 3a. The consistent v2 tree: rc 0.
( cd "$(pwd)" && python3 "$REPO_ROOT/scripts/sync.py" --check > check-v2.log 2>&1 ) \
    || {
        echo "----- v2 check.log -----"
        cat check-v2.log
        fail "sync.py --check must exit 0 on the consistent v2 tree"
    }

# 3b. A v1 tree under the v2 project: at least one finding, non-zero rc.
# The sync `--check` artifact gate validates the emitted frontmatter against the
# resolved v2 contract (allowed-fields). Corrupting an emitted agent with a field
# absent from the v2 allow-list is exactly the "tree generated for the wrong
# surface" case and must fail loud instead of silently passing.
MISMATCH="$WORK/mismatch"
cp -r "$(pwd)" "$MISMATCH" || fail "could not copy the primary tree for the mismatch probe"
python3 - "$MISMATCH/.opencode/agents/developer.md" <<'PY' || fail "could not build the surface-mismatch artifact"
import sys
path = sys.argv[1]
text = open(path, encoding="utf-8").read()
# Inject a frontmatter key that is not in the v2 agent-transform.allowed-fields.
block, rest = text.split("---", 2)[1], text.split("---", 2)[2]
open(path, "w", encoding="utf-8").write("---" + block + "surface_mismatch_probe: 1\n---" + rest)
PY
( cd "$MISMATCH" && python3 "$REPO_ROOT/scripts/sync.py" --check > check.log 2>&1 )
mismatch_rc=$?
[ "$mismatch_rc" -ne 0 ] \
    || fail "an artifact inconsistent with the resolved v2 surface must fail sync.py --check (rc 0 was returned)"
grep -q "artifact-contract" "$MISMATCH/check.log" \
    || fail "the mismatch must surface an artifact-contract finding"

# 3c. Cross-layer MCP-document check (SPEC §8 call #3, check_artifact_contracts):
# the registry-wide consistency path must resolve the same v2 format and reject a
# flat v1 `opencode.json` when the project opts into v2, then accept the v2 shape.
# It resolves registry and artifact from the same root, so use a scratch framework
# root carrying the real registry + the project-committed document.
CC_ROOT="$WORK/ccroot"
mkdir -p "$CC_ROOT/config"
cp "$REPO_ROOT/config/ai-providers.yaml" "$CC_ROOT/config/ai-providers.yaml" \
    || fail "could not stage the registry for the cross-layer MCP check"
cp opencode.json "$CC_ROOT/opencode.json" || fail "could not stage the committed MCP doc"

python3 - "$REPO_ROOT" "$CC_ROOT" .meta-config/project.yaml <<'PY' || fail "cross-layer MCP artifact contract check failed"
import json
import sys
sys.path.insert(0, sys.argv[1] + "/scripts")
from pathlib import Path
from lib.consistency.artifact_contracts import check_artifact_contracts
from lib.consistency.report import Severity
from lib.io import load_yaml_file
root = Path(sys.argv[2])
project = load_yaml_file(Path(sys.argv[3]), on_error="default", default={})
committed = root / "opencode.json"

# A flat v1 document under the v2 project is a mismatch (fail-loud).
doc = {
    "mcp": {"playwright": {"command": "npx", "args": ["-y", "@playwright/mcp"]}},
    "subagent_depth": 1,
}
json.dump(doc, open(committed, "w", encoding="utf-8"))
findings = check_artifact_contracts(root, project)
assert findings, "a v1-shaped committed MCP doc must be rejected under a v2 project"
assert all(f.severity == Severity.ERROR for f in findings)
assert any("mcp.servers" in f.message for f in findings), [f.message for f in findings]

# The nested v2 document passes cleanly.
json.dump({"mcp": {"servers": {}}, "default_agent": "orchestrator"},
          open(committed, "w", encoding="utf-8"))
assert check_artifact_contracts(root, project) == []
PY

echo "ASSERT OK (69-opencode-v2-surface): project channel -> v2 shape/mechanism (nested mcp.servers + default_agent + mode: primary), v1/unset byte-identical, --check rc 0 on v2 and fail-loud on a v1 tree"
