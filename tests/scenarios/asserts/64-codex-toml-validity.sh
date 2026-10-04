#!/bin/bash
# Scenario assert for 64-codex-toml-validity
# (Spec §8 AC-1, spec §10.1 row 64: every generated `.codex/agents/*.toml`
# parses with `tomllib`, and the singleton constraint text survives
# serialization inside `developer_instructions`.)
#
# Issue #862: the scenario enables debug-mode + viz + critical-rules-footer +
# pathRules + xml-section-wrapping, so it also pins that the post-serialization
# body injections land INSIDE `developer_instructions` (a parse failure would
# trip the tomllib check) and that the debug marker is present there.
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. The harness has already run dry-run + real sync +
# --validate. Exit 0 = all assertions hold.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (64-codex-toml-validity): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (64-codex-toml-validity): $*"
    exit 1
}

AGENTS_DIR=".codex/agents"
[ -d "$AGENTS_DIR" ] || fail "agents dir missing: $AGENTS_DIR"

shopt -s nullglob
toml_files=("$AGENTS_DIR"/*.toml)
[ "${#toml_files[@]}" -gt 0 ] || fail "no generated Codex TOML files in $AGENTS_DIR"

python3 - <<'PY' || fail "Codex TOML validity assertions failed (see above)"
import pathlib
import tomllib

agents_dir = pathlib.Path(".codex/agents")
files = sorted(agents_dir.glob("*.toml"))
assert files, "no TOML files found"

parse_errors = []
singleton_files = []
missing_debug_marker = []
parsed = 0
debug_marker = "<!-- agent-meta:debug-mode -->"

for path in files:
    raw = path.read_text(encoding="utf-8")
    try:
        data = tomllib.loads(raw)
    except Exception as exc:  # noqa: BLE001 - report every parse failure verbatim
        parse_errors.append(f"{path}: {type(exc).__name__}: {exc}")
        continue
    if not isinstance(data, dict) or "developer_instructions" not in data:
        parse_errors.append(f"{path}: 'developer_instructions' missing after parse")
        continue
    parsed += 1
    instructions = data["developer_instructions"]
    if "subagent_type" in instructions and "orchestrator" in instructions:
        singleton_files.append(path.name)
    # debug-mode: true is enabled for this scenario — the marker must live
    # inside the serialized string, not after the closing delimiter.
    if debug_marker not in instructions:
        missing_debug_marker.append(path.name)

if parse_errors:
    for entry in parse_errors:
        print(f"TOML PARSE ERROR: {entry}")
    raise SystemExit(1)

assert parsed == len(files), f"parsed={parsed} files={len(files)}"
if missing_debug_marker:
    print(f"DEBUG MARKER MISSING inside developer_instructions: {missing_debug_marker}")
    raise SystemExit(1)
assert singleton_files, (
    "no generated TOML carried the singleton constraint inside developer_instructions"
)

print(
    f"TOML OK: {parsed}/{len(files)} files parsed; singleton constraint in "
    f"{', '.join(sorted(singleton_files))}; debug marker inside developer_instructions"
)
PY
