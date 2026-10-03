#!/bin/bash
# Scenario assert for 72-continue-config-validity
# (design §7.1 + OQ-2 / OQ-9, AC-7: generated Continue config is Zod-valid).
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# --validate. This scenario proves the generated `.continue/config.yaml`:
#   1. carries a top-level `name` and `version`,
#   2. has NO dead top-level `agents:` block (removed per OQ-2),
#   3. uses a valid model `roles` enum — never the out-of-enum value `agent`;
#      the primary agent model uses `[chat, edit]` (OQ-9),
#   4. while `.continue/agents/*.md` still exist (cn review surface).
# Exit 0 = all assertions hold.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (72-continue-config-validity): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (72-continue-config-validity): $*"
    exit 1
}

CFG=".continue/config.yaml"
[ -f "$CFG" ] || fail "generated config missing: $CFG"

if ! python3 - "$CFG" <<'PY'
import sys

try:
    import yaml
except ImportError as exc:  # pragma: no cover - same dependency sync.py uses
    print(f"ERROR: PyYAML is required to parse {sys.argv[1]}: {exc}")
    sys.exit(2)

with open(sys.argv[1], encoding="utf-8") as fh:
    data = yaml.safe_load(fh)

assert isinstance(data, dict), f"top level must be a mapping, got {type(data).__name__}"

# 1. Top-level name/version.
assert data.get("name"), f"missing top-level 'name': {data.get('name')!r}"
assert data.get("version"), f"missing top-level 'version': {data.get('version')!r}"

# 2. No dead top-level agents: block (OQ-2).
assert "agents" not in data, "dead top-level 'agents:' block present in .continue/config.yaml"

# 3. roles enum validity (OQ-9): 'agent' is not a Continue model role.
models = data.get("models")
assert isinstance(models, list) and models, f"missing models block: {models!r}"
for model in models:
    roles = model.get("roles")
    assert roles, f"model {model.get('name')!r} declares no roles"
    assert "agent" not in roles, (
        f"model {model.get('name')!r} declares out-of-enum role 'agent': {roles!r}"
    )

primary = [m for m in models if m.get("name") == "Qwen2.5 Coder 14B (Agent)"]
assert primary, "primary agent model 'Qwen2.5 Coder 14B (Agent)' is missing"
assert primary[0].get("roles") == ["chat", "edit"], (
    f"primary agent model roles must be [chat, edit], got {primary[0].get('roles')!r}"
)
PY
then
    fail "config.yaml validity assertions failed"
fi

# 4. `.continue/agents/*.md` are still generated (cn review surface).
agents_count="$(find .continue/agents -maxdepth 1 -type f -name '*.md' | wc -l | tr -d ' ')"
[ "$agents_count" -ge 1 ] || fail ".continue/agents/*.md missing (continue review surface dropped)"

echo "ASSERT OK (72-continue-config-validity): name/version present, no dead agents block, valid roles enum ($agents_count agent file(s))"
