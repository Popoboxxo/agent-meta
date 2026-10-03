#!/bin/bash
# Scenario assert for 68-antigravity-discovery-paths.
# (SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30, AC-9 / OQ-1 / PRE-2.)
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# --validate.
#
# Two-part proof:
#   1. FLAG GATING (shipped default): <REPO_ROOT>/config/ai-providers.yaml
#      declares `agent-discovery: false` for Gemini, and the discovery sub-map
#      (`.agents/agents|rules|skills` + `.agents/mcp_config.json`,
#      `antigravity-mcp-json`) is declared as data.
#   2. OPT-IN SURFACE: with `agent-discovery: true` the generator emits the
#      `.agents/agents`, `.agents/rules`, `.agents/skills` directories and
#      `.agents/mcp_config.json`, whose remote entries use `serverUrl`.
#      Because the flag is REGISTRY-level data (no project.yaml key consumes
#      it), the opt-in run is exercised against a throwaway framework copy in
#      the temp dir — the real checkout is never mutated.
# Exit 0 = all assertions hold.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (68-antigravity-discovery-paths): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (68-antigravity-discovery-paths): $*"
    exit 1
}

REGISTRY="$REPO_ROOT/config/ai-providers.yaml"
[ -f "$REGISTRY" ] || fail "registry missing: $REGISTRY"

# 1. Shipped default is flag-gated OFF, and the discovery contract is declared.
python3 - "$REGISTRY" <<'PY' || fail "shipped agent-discovery default / discovery sub-map contract violated"
import sys
try:
    import yaml
except ImportError:
    # No PyYAML in the harness python is not expected (sync.py uses it).
    print("PyYAML unavailable")
    raise SystemExit(3)
with open(sys.argv[1], encoding="utf-8") as fh:
    providers = yaml.safe_load(fh)["providers"]
gem = providers["Gemini"]
assert gem.get("agent-discovery") is False, (
    f"shipped Gemini.agent-discovery must default to false (got {gem.get('agent-discovery')!r})"
)
disc = gem.get("discovery")
assert isinstance(disc, dict), "Gemini.discovery sub-map must be declared as data"
assert disc.get("agents_dir") == ".agents/agents", disc
assert disc.get("rules_dir") == ".agents/rules", disc
assert disc.get("skills_dir") == ".agents/skills", disc
mcp = disc.get("mcp-config") or {}
assert mcp.get("committed-file") == ".agents/mcp_config.json", mcp
assert mcp.get("format") == "antigravity-mcp-json", mcp
PY

# 1b. Shipped default (`agent-discovery: false`) SUPPRESSES the `.agents/*`
#     discovery surface in this harness run (cwd = temp project synced with the
#     real checkout). The scenario project.yaml carries a stray
#     `agent-discovery: true` key that no project.yaml consumer reads, so the
#     registry default wins. The legacy `.gemini/*` surface must remain.
for p in .agents/agents .agents/rules .agents/skills .agents/mcp_config.json; do
    [ ! -e "$p" ] || fail "shipped default (agent-discovery: false) must suppress the .agents surface, but '$p' exists"
done
[ -d ".gemini/agents" ] || fail "legacy surface missing under agent-discovery: false: .gemini/agents"
[ -f ".gemini/settings.json" ] || fail "legacy surface missing under agent-discovery: false: .gemini/settings.json"

# 2. Opt-in surface: exercise `agent-discovery: true` via a throwaway framework
#    copy so the real checkout stays untouched (repo-containment).
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
FW="$WORK/fw"
PROJ="$WORK/proj"
mkdir -p "$FW" "$PROJ/.meta-config"

for d in scripts config agents templates hooks rules; do
    [ -e "$REPO_ROOT/$d" ] || continue
    cp -r "$REPO_ROOT/$d" "$FW/"
done
find "$FW" \( -name '*.pyc' -o -name '__pycache__' \) -exec rm -rf {} + 2>/dev/null || true

# Flip ONLY the Gemini entry's flag inside the throwaway copy. The replacement
# is line-anchored and skips comment lines: the Gemini block carries an
# explanatory comment that also contains the literal "agent-discovery: false",
# so a naive string replace would rewrite the comment and leave the real key
# untouched (the defect this assert previously tripped over).
python3 - "$FW/config/ai-providers.yaml" <<'PY' || fail "could not flip agent-discovery in throwaway copy"
import re
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
i = s.index("  Gemini:")
head, tail = s[:i], s[i:]
tail, n = re.subn(
    r"(?m)^([ \t]*)agent-discovery:[ \t]*false[ \t]*$",
    r"\1agent-discovery: true",
    tail,
    count=1,
)
if n != 1:
    raise SystemExit(f"expected exactly one real agent-discovery key, replaced {n}")
open(p, "w", encoding="utf-8").write(head + tail)
PY

cat > "$PROJ/.meta-config/project.yaml" <<EOF
agent-meta-version: 0.101.0
ai-providers:
- Gemini
platforms: []
roles:
- orchestrator
- developer
# Active MCP servers so the discovery-surface MCP file (.agents/mcp_config.json)
# is emitted with entries. `home-assistant` is a REMOTE (`type: sse`) catalog
# server — required so the `serverUrl`-vs-`url` contract below is non-vacuous.
# `playwright` contributes a stdio entry alongside it.
plugins:
  home-assistant:
    enabled: true
  playwright:
    enabled: true
project:
  name: assert68
  prefix: s68a
  short: assert68
variables:
  PROJECT_NAME: assert68
  PROJECT_DESCRIPTION: throwaway opt-in run
  PROJECT_GOAL: prove the .agents/* discovery surface is gated by agent-discovery
  GIT_PLATFORM: GitHub
  GIT_REMOTE_URL: https://github.com/example/assert68
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
) || fail "opt-in sync (agent-discovery: true) failed — see $PROJ/sync.log"

[ -d "$PROJ/.agents/agents" ] || fail "opt-in surface missing: .agents/agents"
[ -d "$PROJ/.agents/rules" ] || fail "opt-in surface missing: .agents/rules"
[ -d "$PROJ/.agents/skills" ] || fail "opt-in surface missing: .agents/skills"
[ -f "$PROJ/.agents/mcp_config.json" ] || fail "opt-in surface missing: .agents/mcp_config.json"

python3 - "$PROJ/.agents/mcp_config.json" <<'PY' || fail "serverUrl contract violated in .agents/mcp_config.json"
import json
import sys
with open(sys.argv[1], encoding="utf-8") as fh:
    doc = json.load(fh)
servers = doc.get("mcpServers", doc)
assert isinstance(servers, dict) and servers, "no MCP servers in .agents/mcp_config.json"
# Antigravity marks a remote transport with `type: sse` (opencode remaps to
# `remote`, VS Code to `http`). Require at least one remote entry so the
# serverUrl-vs-url/headers contract below is non-vacuous.
remote_types = {"sse", "remote", "http", "streamable-http"}
remote = {n: e for n, e in servers.items()
          if e.get("type") in remote_types or "serverUrl" in e}
assert remote, (
    "expected >=1 remote MCP server in .agents/mcp_config.json so the serverUrl "
    f"contract is non-vacuous (got servers: {sorted(servers)})"
)
# Remote entries must use `serverUrl` and never the `url`/`httpUrl` spellings.
for name, entry in remote.items():
    assert "serverUrl" in entry, f"{name}: remote entry must carry serverUrl, got {entry}"
    assert "url" not in entry, f"{name}: remote entry must not carry 'url', got {entry}"
    assert "httpUrl" not in entry, f"{name}: remote entry must not carry 'httpUrl', got {entry}"
PY

echo "ASSERT OK (68-antigravity-discovery-paths): .agents/* discovery surface generated on opt-in (remote entry uses serverUrl, no url/httpUrl); shipped default agent-discovery: false suppresses .agents/* while .gemini/* remains"
