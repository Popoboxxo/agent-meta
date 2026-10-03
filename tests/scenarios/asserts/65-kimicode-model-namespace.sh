#!/bin/bash
# Scenario assert for 65-kimicode-model-namespace
# (Spec §8 AC-2, spec §10.1 row 65: every emitted `model:` line matches
# `^model: kimi-code/` — exactly one prefix, never `kimi-code/kimi-code/`
# and never a bare ID.)
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# --validate. Exit 0 = all assertions hold.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (65-kimicode-model-namespace): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (65-kimicode-model-namespace): $*"
    exit 1
}

AGENTS_DIR=".kimi-code/agents"
[ -d "$AGENTS_DIR" ] || fail "agents dir missing: $AGENTS_DIR"

shopt -s nullglob
md_files=("$AGENTS_DIR"/*.md)
[ "${#md_files[@]}" -gt 0 ] || fail "no generated Kimi Code agent files in $AGENTS_DIR"

python3 - <<'PY' || fail "KimiCode model namespace assertions failed (see above)"
import pathlib
import re

agents_dir = pathlib.Path(".kimi-code/agents")
files = sorted(agents_dir.glob("*.md"))
assert files, "no Kimi Code agent files found"

model_line = re.compile(r"^model:\s*(.+?)\s*$")
errors = []
checked = 0

for path in files:
    model_values = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = model_line.match(line)
        if match:
            model_values.append(match.group(1))
    if not model_values:
        errors.append(f"{path}: no 'model:' line in frontmatter")
        continue
    for value in model_values:
        checked += 1
        if not value.startswith("kimi-code/"):
            errors.append(f"{path}: model {value!r} does not start with 'kimi-code/'")
        elif value.count("kimi-code/") != 1:
            errors.append(f"{path}: model {value!r} carries a duplicate 'kimi-code/' prefix")

if errors:
    for entry in errors:
        print(f"MODEL NAMESPACE ERROR: {entry}")
    raise SystemExit(1)

print(
    f"MODEL OK: {checked} model line(s) across {len(files)} file(s) carry exactly "
    "one 'kimi-code/' prefix"
)
PY
