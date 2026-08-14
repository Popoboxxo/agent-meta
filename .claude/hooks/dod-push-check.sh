#!/bin/bash
# hook: dod-push-check
# version: 1.4.0
# event: PreToolUse
# matcher: Bash
# provider: Claude
# description: Blocks git push on main/master (Branch-Guard) and until tests are green (DoD enforcement)
# enabled_by_default: false

# Claude Code passes hook context as JSON on stdin.
# Exit 0 = allow, exit 2 = block (stdout shown to Claude as context).

# python3 required for JSON parsing
command -v python3 &>/dev/null || exit 0

read -r -d '' _PARSE_HOOK_INPUT <<'PYEOF'
import json, sys
d = json.load(sys.stdin)
print(d.get('tool_name', ''))
print(d.get('tool_input', {}).get('command', ''))
PYEOF

_parsed=$(python3 -c "$_PARSE_HOOK_INPUT" 2>/dev/null)
TOOL_NAME=$(printf '%s' "$_parsed" | head -1)
COMMAND=$(printf '%s' "$_parsed" | tail -n +2)

# Only intercept Bash tool calls
[ "$TOOL_NAME" = "Bash" ] || exit 0

# Only intercept commands that contain git push
echo "$COMMAND" | grep -qE '(^|[;&|[:space:]])git push' || exit 0

# --- Resolve project config file ---
# Config layout since agent-meta v0.26+: .meta-config/project.yaml (YAML).
# Legacy fallback: agent-meta.config.json at the project root (pre-0.26).
# Walk up the directory tree until a config is found.
CONFIG_FILE=""
DIR="$PWD"
for _ in 1 2 3 4 5 6; do
  if [ -f "$DIR/.meta-config/project.yaml" ]; then
    CONFIG_FILE="$DIR/.meta-config/project.yaml"
    break
  fi
  if [ -f "$DIR/agent-meta.config.json" ]; then
    CONFIG_FILE="$DIR/agent-meta.config.json"
    break
  fi
  [ "$DIR" = "/" ] && break
  DIR="$(dirname "$DIR")"
done

# read_config_var <config_file> <variable_name>
# Reads variables.<name> from a project config. Supports YAML (project.yaml)
# and legacy JSON (agent-meta.config.json). Prefers PyYAML, falls back to a
# stdlib-only scan of the top-level `variables:` block so the hook never needs
# a third-party dependency in the target project.
read_config_var() {
  python3 - "$1" "$2" <<'PYEOF' 2>/dev/null
import sys
path, key = sys.argv[1], sys.argv[2]
val = ""
try:
    if path.endswith(".json"):
        import json
        with open(path, encoding="utf-8") as f:
            data = json.load(f) or {}
        val = str(data.get("variables", {}).get(key, ""))
    else:
        try:
            import yaml
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            val = str(data.get("variables", {}).get(key, ""))
        except Exception:
            # stdlib-only fallback: scan the top-level `variables:` block
            in_vars = False
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if line.startswith("variables:"):
                        in_vars = True
                        continue
                    if in_vars:
                        if line and not line[0].isspace():
                            break
                        s = line.strip()
                        if s.startswith(key + ":"):
                            v = s[len(key) + 1:].strip()
                            if len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]:
                                v = v[1:-1]
                            val = v
                            break
except Exception:
    val = ""
print(val)
PYEOF
}

# --- Tag-only push detection ---
# A tag push (`git push origin v1.2.3`, `git push origin --tags`,
# `git push origin tag v1.2.3`, `git push origin refs/tags/v1.2.3`) does not
# touch any branch ref — it cannot add commits to main/master, which is the
# entire premise the Branch-Guard below exists to prevent. Without this
# check, cutting a release while sitting on main (the normal place to be
# right after a release PR merges) was blocked identically to an actual
# direct push of main's commit history, even though the two are unrelated
# in risk. Not a full shell parser (matches this repo's other hooks'
# documented approach) — covers the realistic `git push <remote> <ref>` /
# `--tags` / `tag <name>` forms; anything else (bare `git push`, `git push
# origin`, an explicit branch ref) still falls through to the branch check.
IS_TAG_ONLY_PUSH=$(python3 - "$COMMAND" <<'PYEOF' 2>/dev/null
import subprocess, sys
tokens = sys.argv[1].split()
try:
    rest = tokens[tokens.index("push") + 1:]
except ValueError:
    print("false"); sys.exit(0)
if "--tags" in rest:
    print("true"); sys.exit(0)
non_flags = [t for t in rest if not t.startswith("-")]
if len(non_flags) >= 3 and non_flags[1] == "tag":
    print("true"); sys.exit(0)
if len(non_flags) == 2:
    ref = non_flags[1]
    if ref.startswith("refs/tags/"):
        print("true"); sys.exit(0)
    is_tag = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/tags/{ref}"],
        capture_output=True,
    ).returncode == 0
    is_branch = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{ref}"],
        capture_output=True,
    ).returncode == 0
    print("true" if (is_tag and not is_branch) else "false")
    sys.exit(0)
print("false")
PYEOF
)

# --- Branch-Guard: block push on main/master ---
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

# Resolve GIT_MAIN_BRANCH: env var > project config > default "main"
MAIN_BRANCH="${AGENT_META_MAIN_BRANCH:-}"

if [ -z "$MAIN_BRANCH" ] && [ -n "$CONFIG_FILE" ]; then
  MAIN_BRANCH=$(read_config_var "$CONFIG_FILE" "GIT_MAIN_BRANCH")
fi
MAIN_BRANCH="${MAIN_BRANCH:-main}"

if [ "$IS_TAG_ONLY_PUSH" != "true" ] && { [ "$CURRENT_BRANCH" = "$MAIN_BRANCH" ] || [ "$CURRENT_BRANCH" = "master" ]; }; then
  echo "Branch-Guard: Push blocked — you are on '$CURRENT_BRANCH'."
  echo "Create a feature branch first: git checkout -b feat/<topic>"
  echo "Direct pushes to $MAIN_BRANCH are not allowed by DoD policy."
  echo ""
  echo "If this is intentional (release, hotfix), disable the hook temporarily:"
  echo "  Remove dod-push-check from hooks in .meta-config/project.yaml, re-sync, push, re-enable."
  exit 2
fi

# --- Test-Gate: block push if tests fail ---
# Resolve TEST_COMMAND: env var > project config
TEST_CMD="${AGENT_META_TEST_COMMAND:-}"

if [ -z "$TEST_CMD" ] && [ -n "$CONFIG_FILE" ]; then
  TEST_CMD=$(read_config_var "$CONFIG_FILE" "TEST_COMMAND")
fi

if [ -z "$TEST_CMD" ] && [ -z "$CONFIG_FILE" ]; then
  # No config file located at all — surface this instead of silently skipping.
  echo "DoD-Check: no project config found (.meta-config/project.yaml)."
  echo "The test gate could not be evaluated. Either run from within the project,"
  echo "or export AGENT_META_TEST_COMMAND='<your-test-command>' to enable it."
  echo "Push allowed (Branch-Guard passed, but test gate was NOT enforced)."
  exit 0
fi

if [ -z "$TEST_CMD" ]; then
  echo "DoD-Check: TEST_COMMAND not configured — skipping test gate."
  echo "Set variables.TEST_COMMAND in .meta-config/project.yaml or"
  echo "export AGENT_META_TEST_COMMAND='<your-test-command>' to enable."
  echo "Push allowed (Branch-Guard passed, no test gate configured)."
  exit 0
fi

echo "DoD-Check: Running '$TEST_CMD'..."
if ! bash -c "$TEST_CMD" 2>&1; then  # Note: TEST_CMD executed via bash -c (no eval) — value from project.yaml
  echo ""
  echo "DoD-Check FAILED: Tests must pass before pushing."
  echo "Fix failing tests and retry, or disable the hook temporarily."
  exit 2
fi

echo "DoD-Check passed."
exit 0
