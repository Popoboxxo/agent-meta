#!/bin/bash
# hook: pre-release-check
# version: 2.0.0
# event: Manual
# description: Dispatcher for mechanized pre-release gates (issue #558) — runs every *.sh script under its own release-gates/ subdirectory (built-in gates plus any project-authored custom gates), collects pass/fail, invoked explicitly by the release agent before tagging/pushing a release, not fired automatically by native tool events
# enabled_by_default: false

# NOTE on `event: Manual`: unlike this repo's other hooks, this script is NOT
# meant to be registered in settings.json via
#   .meta-config/project.yaml: hooks: { pre-release-check: { enabled: true } }
# (that mechanism only wires up native Claude-Code events like PreToolUse).
# Its mere presence at <provider-hooks-dir>/pre-release-check.sh is enough —
# the `release` agent checks for the file itself and runs it with Bash
# before cutting a release. See agents/1-generic/release.md and
# docs/RELEASE_GATES.md.
#
# --- Plugin architecture (issue #558) ---
# This script itself contains NO gate logic and does NOT decide which gates
# are active — it is a pure dispatcher. Every *.sh file directly inside the
# release-gates/ directory next to this script is executed in turn:
#   - Built-in gates ship from hooks/1-generic/release-gates/ in agent-meta
#     and are deployed here by sync.py (scripts/lib/hooks.py::sync_release_gates()).
#   - Projects extend the pipeline simply by dropping their own *.sh files
#     into <hooks_dir>/release-gates/ — sync.py never touches or removes
#     them (not tracked in release-gates/.agent-meta-managed), exactly like
#     project-owned hooks created via --create-hook. No framework change
#     required to add a project-specific gate.
# Each gate script decides for itself whether it is enabled (reads its own
# baked-in default / env var / config) and whether its prerequisites are met
# (missing config/tool → self-skip, exit 0). This dispatcher only cares
# about the final exit code of each script: 0 = pass (incl. self-skip),
# non-zero = fail. See docs/RELEASE_GATES.md for the full gate contract and
# a copy-paste example for writing a custom gate.
#
# Exit 0 = every gate script exited 0 (passed or self-skipped).
# Exit 1 = at least one gate script exited non-zero — release must be aborted.

set -u

PROJECT_ROOT="${PROJECT_ROOT:-$PWD}"
cd "$PROJECT_ROOT" || exit 1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATES_DIR="$SCRIPT_DIR/release-gates"

if [ ! -d "$GATES_DIR" ]; then
  echo "pre-release-check: no $GATES_DIR directory found — nothing to run, nothing configured."
  exit 0
fi

FAILED_GATES=()
RAN_ANY=false

for gate_script in "$GATES_DIR"/*.sh; do
  [ -e "$gate_script" ] || continue  # literal glob with no matches
  RAN_ANY=true
  gate_name="$(basename "$gate_script" .sh)"
  echo "=== Running gate: $gate_name ==="
  if ! bash "$gate_script"; then
    FAILED_GATES+=("$gate_name")
  fi
  echo ""
done

if [ "$RAN_ANY" = "false" ]; then
  echo "pre-release-check: $GATES_DIR is empty — nothing to run."
  exit 0
fi

echo "=== Pre-Release Gate Dispatcher Summary ==="
if [ "${#FAILED_GATES[@]}" -gt 0 ]; then
  echo "RESULT: FAILED — ${#FAILED_GATES[@]} gate(s) blocked the release:"
  for g in "${FAILED_GATES[@]}"; do
    echo "  - $g"
  done
  exit 1
fi

echo "RESULT: all release gates passed"
exit 0
