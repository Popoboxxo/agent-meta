#!/bin/bash
# Scenario assert for 79-opencode-v2-full-surface.
# (SPEC-OPENCODE-V2-SUPPORT-2026-10-22, AC-T1; Amendment B1 applied.)
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# --validate on this project.
#
# This is an ASSURANCE scenario: it is green on the first run and proves the
# whole v2 option surface of the previous tasks end-to-end. Its non-vacuity is
# shown by the negative probe in the task notes (same fixture with
# `surface-version: v1` must fail this script), not by a second sync here.
#
# Parts:
#   1. FIXTURE: the project channel carries every v2-only option and nothing
#      removed by Amendment B1 (`small-model`, `theme`, `autoupdate`).
#   2. OPENCODE.JSON: `experimental.subagent_depth` (>= 2) + `experimental.todo`
#      with NO top-level `subagent_depth`; every `mcp.servers` entry carries no
#      `enabled` key; the two managed deny triples close the `permissions` list
#      (last match wins, Amendment B1 / Spike Q3).
#   3. AGENT ARTIFACT: the configured role `developer` has a `permissions:` LIST
#      and a `model:` with the configured `#high` variant.
#   3b. GATE LOCK: in the primary artifact the `edit` `*` deny comes BEFORE the
#      configured path allows (last match wins), and a read-only role keeps
#      `edit: deny`.
#   4. CLI.JSON: exists and carries exactly the documented `plugins` key.
#   5. PLUGIN ARTIFACT: the v2 runtime-gate plugin is deployed.
#   6. `sync.py --check` returns rc 0 on the consistent tree.
# Exit 0 = all assertions hold.
set -euo pipefail

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (79-opencode-v2-full-surface): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (79-opencode-v2-full-surface): $*"
    exit 1
}

# 1. Fixture: the project channel is the only v2 opt-in, with Amendment B1
#    applied (the `cli` object carries the documented `plugins` key only).
python3 - .meta-config/project.yaml <<'PY' || fail "fixture is not on the documented v2 project channel"
import sys
import yaml
with open(sys.argv[1], encoding="utf-8") as fh:
    project = yaml.safe_load(fh) or {}
opts = (project.get("provider-options") or {}).get("Opencode") or {}
assert opts.get("surface-version") == "v2", (
    f"fixture must opt into v2 via provider-options.Opencode (got {opts!r})"
)
assert opts.get("experimental-todo") is True, opts
assert (opts.get("model-variants") or {}).get("developer") == "high", opts
cli = opts.get("cli") or {}
assert cli == {"plugins": ["opencode-acme-cli"]}, (
    f"cli must carry the documented 'plugins' key only (got {cli!r})"
)
assert "small-model" not in opts, "Amendment B1: 'small-model' must not be configured"
orch = project.get("orchestrator") or {}
assert orch.get("mode") == "strict", (
    f"fixture must request the strict orchestrator (got {orch!r})"
)
PY

[ -f opencode.json ] || fail "v2 output missing: opencode.json"

# 2. opencode.json: experimental keys, no flat depth, mcp.servers without
#    `enabled`, and the managed deny triples at the END of `permissions`.
python3 - opencode.json <<'PY' || fail "v2 opencode.json contract violated"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    doc = json.load(fh)

experimental = doc.get("experimental")
assert isinstance(experimental, dict), "v2 opencode.json requires an 'experimental' object"
assert "subagent_depth" in experimental, (
    "v2 must emit the orchestrator depth as experimental.subagent_depth"
)
depth = experimental["subagent_depth"]
assert isinstance(depth, int) and depth >= 2, (
    f"experimental.subagent_depth must be an int >= 2 (got {depth!r})"
)
assert "subagent_depth" not in doc, (
    "v2 must not carry a top-level subagent_depth key (the v2 parser discards it)"
)
assert experimental.get("todo") is True, (
    f"experimental-todo: true must emit experimental.todo == true (got {experimental.get('todo')!r})"
)

servers = (doc.get("mcp") or {}).get("servers")
assert isinstance(servers, dict) and servers, "v2 opencode.json requires a non-empty mcp.servers object"
for name, server in servers.items():
    assert isinstance(server, dict), f"mcp.servers.{name} must be an object"
    assert "enabled" not in server, (
        f"mcp.servers.{name} must not carry the removed v1 'enabled' key"
    )

permissions = doc.get("permissions")
assert isinstance(permissions, list), "v2 opencode.json requires a 'permissions' LIST"
expected_tail = [
    {"action": "edit", "resource": "**", "effect": "deny"},
    {"action": "shell", "resource": "**", "effect": "deny"},
]
assert len(permissions) >= len(expected_tail), permissions
assert permissions[-2:] == expected_tail, (
    "the two managed deny triples must close the permissions list "
    f"(last match wins); got tail {permissions[-2:]!r}"
)
PY

# 3. Agent artifact: native v2 frontmatter for the configured role.
AGENT=".opencode/agents/developer.md"
[ -f "$AGENT" ] || fail "v2 agent artifact missing: $AGENT"
python3 - "$AGENT" <<'PY' || fail "v2 agent frontmatter contract violated"
import sys
import yaml

with open(sys.argv[1], encoding="utf-8") as fh:
    text = fh.read()
assert text.startswith("---"), "agent artifact must start with YAML frontmatter"
block = text.split("---", 2)[1]
fm = yaml.safe_load(block) or {}

permissions = fm.get("permissions")
assert isinstance(permissions, list), (
    f"v2 agent frontmatter requires a 'permissions' LIST (got {permissions!r})"
)
for entry in permissions:
    assert isinstance(entry, dict), permissions
    assert {"action", "resource", "effect"} <= set(entry), permissions
    assert all(isinstance(entry[key], str) and entry[key] for key in entry), permissions
assert "permission" not in fm, "v2 agent frontmatter must not carry the v1 'permission' map"
assert "subagent_depth" not in fm, "v2 agent frontmatter must not carry 'subagent_depth'"

model = fm.get("model")
assert isinstance(model, str) and model.endswith("#high"), (
    f"configured role 'developer' must carry the '#high' model variant (got {model!r})"
)
PY

# 3b. Gate lock on the agent level (AC-C16 b, Amendment B1): the primary's
#     `edit` `*` deny must precede the configured path allows (last match wins),
#     and a read-only role must keep `edit: deny`.
ORCH=".opencode/agents/orchestrator.md"
READONLY_ROLE=".opencode/agents/explorer.md"
[ -f "$ORCH" ] || fail "primary artifact missing: $ORCH"
[ -f "$READONLY_ROLE" ] || fail "read-only role artifact missing: $READONLY_ROLE"
python3 - "$ORCH" "$READONLY_ROLE" <<'PY' || fail "gate-lock ordering / read-only edit deny violated"
import sys
import yaml


def frontmatter(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    assert text.startswith("---"), f"{path}: YAML frontmatter expected"
    return yaml.safe_load(text.split("---", 2)[1]) or {}


orchestrator = frontmatter(sys.argv[1]).get("permissions")
assert isinstance(orchestrator, list), (
    f"primary artifact requires a permissions list (got {orchestrator!r})"
)
edits = [
    (index, entry)
    for index, entry in enumerate(orchestrator)
    if isinstance(entry, dict) and entry.get("action") == "edit"
]
denies = [(index, entry) for index, entry in edits if entry.get("effect") == "deny"]
assert len(denies) == 1, f"primary needs exactly one `edit` deny (got {denies!r})"
deny_index, deny_entry = denies[0]
assert deny_entry == {"action": "edit", "resource": "*", "effect": "deny"}, deny_entry
allows = [(index, entry) for index, entry in edits if entry.get("effect") == "allow"]
assert allows, "the gate lock must keep the configured path allows"
assert [entry["resource"] for _, entry in allows] == [".tmp/**", ".meta-viz/**"], allows
assert all(index > deny_index for index, _ in allows), (
    "the `edit` `*` deny must precede the path allows (last match wins): "
    f"deny at {deny_index}, allows at {[index for index, _ in allows]}"
)

read_only = [
    entry
    for entry in frontmatter(sys.argv[2]).get("permissions") or []
    if isinstance(entry, dict) and entry.get("action") == "edit"
]
assert read_only == [{"action": "edit", "resource": "*", "effect": "deny"}], (
    f"a read-only role must keep `edit: deny` (got {read_only!r})"
)
PY

# 4. cli.json: exactly the documented top-level key.
[ -f cli.json ] || fail "v2 must deploy the managed CLI settings file: cli.json"
python3 - cli.json <<'PY' || fail "cli.json contract violated"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    doc = json.load(fh)
assert isinstance(doc, dict), "cli.json must be a JSON object"
assert set(doc) == {"plugins"}, (
    f"cli.json must carry exactly the documented 'plugins' key (got {sorted(doc)!r})"
)
assert doc["plugins"] == ["opencode-acme-cli"], doc["plugins"]
for removed in ("theme", "autoupdate"):
    assert removed not in doc, f"Amendment B1: '{removed}' is not a documented cli.json key"
PY

# 5. C3 plugin artifact: the v2 surface resolves `has_plugins` true.
PLUGIN=".opencode/plugins/agent-meta-runtime-gate.js"
[ -f "$PLUGIN" ] || fail "v2 must deploy the runtime-gate plugin artifact: $PLUGIN"
grep -qF "export default {" "$PLUGIN" \
    || fail "the v2 plugin artifact must use the object default export (spike Q4)"

# 6. `--check` agreement on the consistent v2 tree.
if ! python3 "$REPO_ROOT/scripts/sync.py" --check > check.log 2>&1; then
    echo "----- check.log -----"
    cat check.log
    echo "---------------------"
    fail "sync.py --check must exit 0 on the consistent v2 tree"
fi

echo "ASSERT OK (79-opencode-v2-full-surface): experimental.subagent_depth/todo, mcp.servers without enabled, deny triples at the list end, native agent permissions + #high variant, cli.json plugins, runtime-gate plugin, --check rc 0"
