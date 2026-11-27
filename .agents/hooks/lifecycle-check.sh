#!/bin/bash
# hook: lifecycle-check
# version: 1.2.0
# event: PostToolUse
# matcher: Bash
# protocol: tool-hook-v1
# description: Detects git lifecycle events (tag push, merge, version bump) and writes pending tasks to .claude/pending-tasks.md
# enabled_by_default: false
# changelog: v1.2.0: MB-2 (docs/plans/systemaudit-umsetzungsplan-2026-11-25.md) -- the event detection no longer matches a regular expression against the raw command string; lib/hook_lifecycle_event.py classifies every shell statement with the shared tokenizer (hook_shell_scan statement split, hook_shell_resolver command word, hook_push_arg_parser push walk). Quoted prose ('echo "git push"'), text consumers ('git push' as an argument of a text tool), comments and option values ('git push -o --tags') no longer raise events, while 'git -C <path> push' and command wrappers still do. Event names, the release/bump/merge precedence and the 'git describe' bump heuristic are unchanged; a plain 'git commit' still raises no event (the former on-commit arm was unreachable). Still fails OPEN when python or the module is missing.

set -uo pipefail

# Claude Code passes hook context as JSON on stdin.
# PostToolUse hooks receive the tool result — exit code is ignored.
#
# Not a security boundary (informational automation only) — fails OPEN
# (exit 0) if the shared helper lib or python3/python is unavailable,
# same as before (issue #595 only hardens the two hooks that are actual
# security controls: orchestrator-guard.sh and dod-push-check.sh).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/hook_common.sh" 2>/dev/null || exit 0
hook_have_python || exit 0
declare -F hook_json_get_many >/dev/null 2>&1 || exit 0

INPUT=$(cat)
# #1161 Pkt5: ONE interpreter start reads all three fields. This hook is
# informational and fails OPEN, so a failed parse (rc 1, no output) simply
# skips lifecycle detection. bash 3.2: `read -r -d ''`, no eval/mapfile.
_P_FAIL=0
{
  IFS= read -r -d '' _P_TOOL_NAME  || _P_FAIL=1
  IFS= read -r -d '' _P_COMMAND    || _P_FAIL=1
  IFS= read -r -d '' _P_EXIT_CODE  || _P_FAIL=1
  IFS= read -r -d '' _P_TRAILER    || _P_FAIL=1
} < <(hook_json_get_many "$INPUT" tool_name tool_input.command tool_result.exit_code)
if [ "$_P_FAIL" -ne 0 ] || [ "${_P_TRAILER:-}" != "ok" ]; then
  exit 0
fi
TOOL_NAME="$_P_TOOL_NAME"
COMMAND="$_P_COMMAND"
# hook_json_get_many has no default argument: map a missing/empty exit_code
# field to the old single-field reader's default of "0".
EXIT_CODE="$_P_EXIT_CODE"
[ -n "$EXIT_CODE" ] || EXIT_CODE="0"

# Only intercept successful Bash tool calls
[ "$TOOL_NAME" = "Bash" ] || exit 0
[ "$EXIT_CODE" = "0" ] || exit 0

# Locate lifecycle_check.py (relative to this hook's location, SCRIPT_DIR
# already resolved above, or via AGENT_META_ROOT)
LIFECYCLE_PY="$(dirname "$(dirname "$SCRIPT_DIR")")/scripts/lifecycle_check.py"

# Fallback: search for .agent-meta submodule from cwd
if [ ! -f "$LIFECYCLE_PY" ]; then
  LIFECYCLE_PY="$PWD/.agent-meta/scripts/lifecycle_check.py"
fi

[ -f "$LIFECYCLE_PY" ] || exit 0

# ---------------------------------------------------------------------------
# Detect lifecycle event from the git command that just ran
# ---------------------------------------------------------------------------
# The command-word detection lives in lib/hook_lifecycle_event.py: it splits
# the command into shell statements with the shared tokenizer
# (hook_shell_scan), resolves the real command word (hook_shell_resolver) and
# walks a `git push` with the shared argument parser, instead of matching a
# regular expression against the raw command text. That is what keeps quoted
# prose ('echo "git push"'), text consumers ('git push' passed as an argument
# of a text tool), comments and push-option values ('git push -o --tags') from
# raising events, while `git -C <repo> push` and wrappers ('sudo git push')
# still resolve.
#
# One line on stdout: none | on-release | on-merge | on-version-bump-*. This
# hook is informational automation, so everything unexpected -- a missing
# module, a failing interpreter, an unknown line -- fails OPEN (exit 0) here
# instead of blocking the tool call. The version-bump classification asks git
# for the previous tag (git describe --tags --abbrev=0 HEAD~1) inside the
# module, exactly like the former shell heuristic.

_EVENT_PY="$SCRIPT_DIR/lib/hook_lifecycle_event.py"
EVENT=$(printf '%s' "$COMMAND" | python3 "$_EVENT_PY" 2>/dev/null)
case "$EVENT" in
  on-release|on-merge|on-commit|on-version-bump-patch|on-version-bump-minor|on-version-bump-major) ;;
  *) exit 0 ;;
esac

# Fire the lifecycle check
python3 "$LIFECYCLE_PY" "$EVENT"

exit 0
