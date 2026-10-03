#!/bin/bash
# Scenario assert for 66-mammouth-tools-map
# (Spec §8 AC-6, spec §10.1 row 66: the `tools:` frontmatter is an object /
# YAML mapping, never a list.)
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# --validate. Exit 0 = all assertions hold.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (66-mammouth-tools-map): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (66-mammouth-tools-map): $*"
    exit 1
}

AGENTS_DIR=".mammouth/agents"
[ -d "$AGENTS_DIR" ] || fail "agents dir missing: $AGENTS_DIR"

shopt -s nullglob
md_files=("$AGENTS_DIR"/*.md)
[ "${#md_files[@]}" -gt 0 ] || fail "no generated Mammouth agent files in $AGENTS_DIR"

python3 - <<'PY' || fail "Mammouth tools-map assertions failed (see above)"
import pathlib

import yaml

agents_dir = pathlib.Path(".mammouth/agents")
files = sorted(agents_dir.glob("*.md"))
assert files, "no Mammouth agent files found"


def frontmatter(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise AssertionError("missing opening frontmatter delimiter")
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[1:idx])
    raise AssertionError("missing closing frontmatter delimiter")


errors = []
checked = 0

for path in files:
    try:
        data = yaml.safe_load(frontmatter(path))
    except Exception as exc:  # noqa: BLE001 - report every parse failure verbatim
        errors.append(f"{path}: frontmatter parse error: {type(exc).__name__}: {exc}")
        continue
    if not isinstance(data, dict) or "tools" not in data:
        errors.append(f"{path}: no 'tools' key in frontmatter")
        continue
    tools = data["tools"]
    checked += 1
    if isinstance(tools, list):
        errors.append(f"{path}: 'tools' is a list, expected a YAML mapping")
    elif not isinstance(tools, dict):
        errors.append(f"{path}: 'tools' is {type(tools).__name__}, expected a YAML mapping")
    elif not tools:
        errors.append(f"{path}: 'tools' mapping is empty")

if errors:
    for entry in errors:
        print(f"TOOLS MAP ERROR: {entry}")
    raise SystemExit(1)

print(f"TOOLS OK: {checked}/{len(files)} file(s) carry a non-empty 'tools' mapping")
PY
