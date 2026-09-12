#!/bin/bash
# hook: repo-containment
# version: 1.0.0
# event: PreToolUse
# matcher: ""
# description: Confine Write/Edit/Bash file writes to repo root (+ optional .tmp sink).
# enabled_by_default: true

set -uo pipefail

# Self-health wrapper (issue #630, same pattern as orchestrator-guard.sh).
# All actual containment logic lives in repo-containment-impl.sh, sourced/run
# right below. THIS file stays intentionally tiny, dependency-free (no
# `source lib/hook_common.sh`, no python required on the happy path) and
# rarely touched, so it is extremely unlikely to ever be the file that is
# broken.
#
# Why this split exists: a syntactically invalid impl (e.g. an unresolved
# merge-conflict marker) makes `bash <impl>` fail with a parse error BEFORE
# executing a single line. The PreToolUse harness reads that non-zero exit as
# "block". Every subsequent tool call would be blocked — including the
# Read/Edit calls needed to repair the very file that is broken. A single-file
# script cannot self-check its own syntax when IT is the broken file, so the
# check must live in something else that runs first (see
# docs/plans/audit-2026-09-system-concept.md §3.2.4 and the #630 fail-mode).
#
# This wrapper syntax-checks repo-containment-impl.sh with `bash -n` before
# running it. If that check fails, this wrapper applies a NARROW carve-out: a
# Write/Edit call whose target path is EXACTLY the impl script (or this wrapper
# itself, mirroring orchestrator-guard.sh's own-directory carve-out) is allowed
# through so it can be repaired — every other tool call, including any other
# file under this hook's directory, still fails CLOSED. This is not a general
# fail-open: the moment impl.sh is valid bash again, full containment
# enforcement resumes automatically.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMPL="$SCRIPT_DIR/repo-containment-impl.sh"
INPUT=$(cat)

if [ ! -f "$IMPL" ]; then
  echo "REPO_CONTAINMENT: impl script $IMPL is missing." >&2
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
    echo "REPO_CONTAINMENT: $IMPL has a syntax error (bash -n failed)." >&2
    echo "Failing closed for '$TOOL_NAME' (issue #630) — ask an agent to Edit $IMPL to fix the syntax error, then retry." >&2
    exit 2
    ;;
esac

FILE_PATH=$(printf '%s' "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n1 | sed -E 's/.*:[[:space:]]*"([^"]*)"/\1/')

case "$FILE_PATH" in
  "$IMPL"|"$SCRIPT_DIR/repo-containment.sh")
    echo "REPO_CONTAINMENT: $IMPL has a syntax error — allowing $TOOL_NAME on $FILE_PATH so it can be repaired (issue #630)." >&2
    exit 0
    ;;
  *)
    echo "REPO_CONTAINMENT: $IMPL has a syntax error (bash -n failed)." >&2
    echo "Failing closed for '$TOOL_NAME' on '$FILE_PATH' (issue #630) — only the impl script (and this wrapper) are exempted, to allow self-repair." >&2
    exit 2
    ;;
esac
