#!/bin/bash
# hook: orchestrator-guard
# version: 3.1.0
# event: PreToolUse
# matcher: ""
# description: Block non-orchestrator write/edit/bash calls when orchestrator.strict=true; also block direct git mutations in non-strict mode
# enabled_by_default: true

set -uo pipefail

# Self-health wrapper (issue #630). All actual guard logic lives in
# orchestrator-guard-impl.sh, sourced/run right below. THIS file stays
# intentionally tiny, dependency-free (no `source lib/hook_common.sh`, no
# python required on the happy path) and rarely touched, so it is extremely
# unlikely to ever be the file that is broken.
#
# Why this split exists: a real incident showed that if the guard script
# itself becomes syntactically invalid (e.g. an unresolved merge-conflict
# marker), `bash <script>` fails with a parse error BEFORE executing a
# single line — which exits non-zero, which the PreToolUse harness reads as
# "block". Every subsequent tool call is then blocked, including the
# Read/Edit calls needed to repair the very file that's broken. A single-
# file script cannot self-check its own syntax when it IS the broken file —
# the check has to live in something else that runs first (see
# docs/plans/audit-2026-09-system-concept.md §3.2.4).
#
# This wrapper syntax-checks orchestrator-guard-impl.sh with `bash -n`
# before running it. If that check fails, this wrapper applies a NARROW
# carve-out: a Write/Edit call whose target path is under this hook's own
# directory is allowed through (so an agent can fix the impl script) — every
# other tool call (including Bash — the git-mutation/destructive gates) still
# fails CLOSED. This is not a general fail-open: the moment impl.sh is valid
# bash again, full enforcement resumes automatically, and the wrapper never
# widens the carve-out beyond exactly this hook's own directory.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMPL="$SCRIPT_DIR/orchestrator-guard-impl.sh"
INPUT=$(cat)

if [ ! -f "$IMPL" ]; then
  echo "ORCHESTRATOR_GUARD: impl script $IMPL is missing." >&2
  echo "Failing closed — re-run sync.py to redeploy the hooks/ directory." >&2
  exit 2
fi

if bash -n "$IMPL" 2>/dev/null; then
  printf '%s' "$INPUT" | bash "$IMPL"
  exit $?
fi

# --- impl script is syntactically broken: narrow self-repair carve-out ---
# ponytail: heuristic JSON field extraction via grep/sed, not a real JSON
# parser -- deliberate, this path only runs while the impl script (which
# owns the real, robust hook_common.sh-based JSON parsing) is broken, and it
# only ever widens to "allow", never to "block something impl would have
# allowed". Upgrade path: none needed unless PreToolUse payload shapes with
# escaped quotes in file_path become realistic.
TOOL_NAME=$(printf '%s' "$INPUT" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n1 | sed -E 's/.*:[[:space:]]*"([^"]*)"/\1/')

case "$TOOL_NAME" in
  Write|Edit) ;;
  *)
    echo "ORCHESTRATOR_GUARD: $IMPL has a syntax error (bash -n failed)." >&2
    echo "Failing closed for '$TOOL_NAME' (issue #630) — ask an agent to Edit $IMPL to fix the syntax error, then retry." >&2
    exit 2
    ;;
esac

FILE_PATH=$(printf '%s' "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n1 | sed -E 's/.*:[[:space:]]*"([^"]*)"/\1/')

case "$FILE_PATH" in
  "$SCRIPT_DIR"/*)
    echo "ORCHESTRATOR_GUARD: $IMPL has a syntax error — allowing $TOOL_NAME on $FILE_PATH (under $SCRIPT_DIR/) so it can be repaired (issue #630)." >&2
    exit 0
    ;;
  *)
    echo "ORCHESTRATOR_GUARD: $IMPL has a syntax error (bash -n failed)." >&2
    echo "Failing closed for '$TOOL_NAME' on '$FILE_PATH' (issue #630) — only Write/Edit under $SCRIPT_DIR/ are exempted, to allow self-repair." >&2
    exit 2
    ;;
esac
