#!/bin/bash
# hook: auto-github-release
# version: 1.0.0
# event: PostToolUse
# matcher: Bash
# description: After a `git push <tag>`, auto-create the matching GitHub release (gh release create) when a project opts in via conventions.release.github_release.enabled — idempotent, opt-in, never blocks the tool call (issues #518/#622)
# enabled_by_default: false

set -uo pipefail

# Claude Code passes the PostToolUse context as JSON on stdin. This hook is a
# pure post-push automation, NOT a gate: it always exits 0 and never blocks or
# fails the (already-completed) push. All decision logic and the `gh` calls
# live in scripts/lib/auto_github_release.py; this wrapper only locates the
# agent-meta sources and hands the payload over.
#
# Not a security boundary — fails OPEN (exit 0) if the helper lib, python, or
# the agent-meta sources are unavailable (same policy as sync-on-config-change.sh;
# issue #595 only hardens the two hooks that are real security controls).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/hook_common.sh" 2>/dev/null || exit 0
hook_have_python || exit 0

INPUT=$(cat)

# Locate the agent-meta root (the tree that ships config/conventions-presets.yaml
# and scripts/lib/). Order: explicit override (tests/CI) → running straight from
# the agent-meta source tree (hooks/1-generic/) → embedded submodule (.agent-meta).
_has_meta() { [ -f "$1/config/conventions-presets.yaml" ] && [ -d "$1/scripts/lib" ]; }

AM_ROOT=""
if [ -n "${AGR_AGENT_META_ROOT:-}" ] && _has_meta "$AGR_AGENT_META_ROOT"; then
  AM_ROOT="$AGR_AGENT_META_ROOT"
else
  _from_src="$(dirname "$(dirname "$SCRIPT_DIR")")"
  if _has_meta "$_from_src"; then
    AM_ROOT="$_from_src"
  elif _has_meta "$PWD/.agent-meta"; then
    AM_ROOT="$PWD/.agent-meta"
  fi
fi

# No agent-meta sources reachable → nothing to resolve, no-op (fail open).
[ -n "$AM_ROOT" ] || exit 0

_PY="$(hook_python_bin)"
printf '%s' "$INPUT" | AGR_AGENT_META_ROOT="$AM_ROOT" "$_PY" -c "
import sys
sys.path.insert(0, sys.argv[1])
from lib.auto_github_release import main
sys.exit(main())
" "$AM_ROOT/scripts"

exit 0
