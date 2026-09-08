#!/bin/bash
# Scenario assert for 21-auto-commit-off-ignores-config (issue #694).
#
# Contract (see tests/scenarios/run.sh header): cwd = the scenario's temp
# project dir (the sync output); $1 and env REPO_ROOT both carry the
# agent-meta checkout path. Exit 0 = all assertions hold; non-zero = first
# violated assertion, printed to stdout/stderr.
#
# Verified expectations -- derived from the framework code, not guessed:
#   Allowlist (scripts/lib/auto_commit.py::resolve_auto_commit_config):
#     mode != "off" gates the eligible_roles computation, so mode "off"
#     yields eligible_roles [] regardless of other keys; the resolved
#     values (file_count_threshold 2, secret_scan false from the config)
#     are still recorded. scripts/lib/sync_pipeline.py::
#     _sync_stage_auto_commit_allowlist writes the allowlist on EVERY
#     sync -- hence the byte-identity diff below excludes .meta-config
#     (the compare sync's allowlist legitimately differs: defaults
#     threshold 5 / secret_scan true) and sync.log (absolute paths).
#   Rendering (scripts/lib/config.py): AUTO_COMMIT_ENABLED = "false" for
#     mode "off", AUTO_COMMIT_BLOCK = "" -> the {{#if}} gate strips the
#     block from every generated agent file, in every provider dir.
#   NOTE: the scenario config quotes mode: "off" on purpose -- unquoted
#     `off` is parsed as boolean False by YAML 1.1 and silently treated
#     as an enabled mode by resolve_auto_commit_config ("mode != \"off\"")
#     -- reported framework bug, out of this scenario's fix scope.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (21-auto-commit-off-ignores-config): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (21-auto-commit-off-ignores-config): $*"
    exit 1
}

ALLOWLIST=".meta-config/auto-commit-allowlist.json"
[ -f "$ALLOWLIST" ] || fail "allowlist file missing: $ALLOWLIST"

# --- 1. Allowlist shape: off mode + inert stray values ------------------
python3 - "$ALLOWLIST" <<'PY' || exit 1
import json
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)


def check(cond: bool, msg: str) -> None:
    if not cond:
        print(f"ASSERT FAIL (21-auto-commit-off, allowlist): {msg} -- "
              f"allowlist content: {json.dumps(data, sort_keys=True)}")
        sys.exit(1)


check(data.get("mode") == "off", "mode must be the string 'off' "
      "(unquoted YAML `off` parses to boolean False -- scenario config quotes it)")
check(data.get("eligible_roles") == [],
      "eligible_roles must be empty (mode 'off' must not grant commit authority "
      "to any role, regardless of active roles)")
check(data.get("triggers") == [], "triggers must be empty")
check(data.get("custom_script") is None, "custom_script must be null")
# Stray values from the config must be recorded but stay inert (nothing
# below asserts any behavior derived from them).
check(data.get("file_count_threshold") == 2,
      "file_count_threshold must record the config value 2 (inert in off mode)")
check(data.get("secret_scan") is False,
      "secret_scan must record the config value false (inert in off mode)")
PY

# --- 2. No AUTO_COMMIT block rendered anywhere --------------------------
for provider in .claude .gemini .opencode; do
    [ -d "$provider/agents" ] || fail "generated agents dir missing: $provider/agents"
    hits="$(grep -rl "Commit authority (issue #694)" "$provider/agents" 2>/dev/null || true)"
    [ -z "$hits" ] || fail "AUTO_COMMIT block rendered in off mode -- found in: $hits"
done

# --- 3. Byte-identity vs. a sync WITHOUT the auto_commit key ------------
# Re-run sync into a compare dir with the auto_commit block stripped from
# project.yaml; every generated artifact outside .meta-config must be
# byte-identical (see file header for the exclusion rationale).
COMPARE="$PWD/.scenario-compare"
LOGS="$PWD/.scenario-logs"
mkdir -p "$LOGS"
rm -rf "$COMPARE"
mkdir -p "$COMPARE/.meta-config"

python3 - "$PWD/.meta-config/project.yaml" "$COMPARE/.meta-config/project.yaml" <<'PY' || exit 1
import sys

src, dst = sys.argv[1], sys.argv[2]
out, skipping = [], False
with open(src, encoding="utf-8") as fh:
    for line in fh:
        if line.startswith("auto_commit:"):
            skipping = True
            continue
        if skipping:
            # Drop the block's own indented continuation lines; a
            # top-level (non-indented) key ends the block.
            if line[:1] in (" ", "\t"):
                continue
            skipping = False
        out.append(line)
with open(dst, "w", encoding="utf-8") as fh:
    fh.writelines(out)
PY

(cd "$COMPARE" && python3 "$REPO_ROOT/scripts/sync.py") >/dev/null 2>&1 \
    || fail "compare sync (auto_commit key stripped) failed -- see $COMPARE/sync.log"

DIFF_LOG="$LOGS/assert-21-byte-identity.diff"
diff -r \
    --exclude=".meta-config" \
    --exclude="sync.log" \
    --exclude=".scenario-compare" \
    --exclude=".scenario-logs" \
    "$PWD" "$COMPARE" >"$DIFF_LOG" 2>&1
if [ -s "$DIFF_LOG" ]; then
    fail "generated output is NOT byte-identical to a sync without the auto_commit key -- " \
         "diff kept at $DIFF_LOG, first lines: $(head -5 "$DIFF_LOG")"
fi

echo "ASSERT OK (21-auto-commit-off-ignores-config): off-mode inertness + byte-identical output verified"
