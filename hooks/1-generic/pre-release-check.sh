#!/bin/bash
# hook: pre-release-check
# version: 3.0.0
# event: Manual
# description: Dispatcher for mechanized pre-release gates (issue #558) — runs every *.sh script under its own release-gates/ subdirectory that is on the allowlist (built-in gates plus any project-authored custom gates explicitly opted in), collects pass/fail, invoked explicitly by the release agent before tagging/pushing a release, not fired automatically by native tool events
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
# release-gates/ directory next to this script that is ALSO on the
# allowlist (see below, issue #598) is executed in turn:
#   - Built-in gates ship from hooks/1-generic/release-gates/ in agent-meta
#     and are deployed here by sync.py (scripts/lib/hooks.py::sync_release_gates()),
#     which also (re)writes release-gates/.agent-meta-managed — the
#     allowlist entry for built-ins.
#   - Projects extend the pipeline by dropping their own *.sh files into
#     <hooks_dir>/release-gates/ AND explicitly listing the filename in
#     release-gates/.allowed-gates (sync.py never touches or removes either
#     the script or this manifest, exactly like project-owned hooks created
#     via --create-hook). No framework change required to add a
#     project-specific gate — one manifest line is.
# Each gate script decides for itself whether it is enabled (reads its own
# baked-in default / env var / config) and whether its prerequisites are met
# (missing config/tool → self-skip, exit 0). This dispatcher only cares
# about the final exit code of each ALLOWED script: 0 = pass (incl.
# self-skip), non-zero = fail. See docs/RELEASE_GATES.md for the full gate
# contract and a copy-paste example for writing a custom gate.
#
# Exit 0 = every allowed gate script exited 0 (passed or self-skipped).
# Exit 1 = at least one allowed gate script exited non-zero — release must
#          be aborted.

set -uo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$PWD}"
cd "$PROJECT_ROOT" || exit 1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATES_DIR="$SCRIPT_DIR/release-gates"

if [ ! -d "$GATES_DIR" ]; then
  echo "pre-release-check: no $GATES_DIR directory found — nothing to run, nothing configured."
  exit 0
fi

# --- Allowlist (issue #598) -----------------------------------------------
# Running every *.sh dropped into release-gates/ unconditionally was a
# supply-chain risk: a file placed there accidentally, via a compromised
# dependency, or a malicious PR would run automatically as part of the
# release process with no allowlist or integrity check (a full
# signature/checksum scheme was considered and deferred to a separate
# backlog issue — see docs/plans/audit-2026-08-refactoring-roadmap.md,
# Wave 3 decision). The allowlist is the union of two manifests, each one
# filename per line, '#'-comments and blank lines ignored:
#   - release-gates/.agent-meta-managed  — framework-shipped built-ins,
#     written by sync.py. Trusted because they come from the agent-meta
#     source tree, never from an arbitrary drop-in.
#   - release-gates/.allowed-gates       — project-owned manifest, sync.py
#     NEVER writes or deletes this file. A project opts a custom gate in by
#     adding its filename here.
# A *.sh present in release-gates/ but listed in NEITHER manifest is
# skipped with a [SKIP] line — not silently run, and not treated as a
# release-blocking failure (a stray/experimental script shouldn't itself
# abort a release; the whole point is that it doesn't run at all).
_read_gate_manifest() {
  local f="$1"
  [ -f "$f" ] || return 0
  local line stripped
  while IFS= read -r line || [ -n "$line" ]; do
    stripped="${line%%#*}"
    stripped="$(printf '%s' "$stripped" | tr -d '[:space:]')"
    [ -n "$stripped" ] && printf '%s\n' "$stripped"
  done < "$f"
}

ALLOWLIST=$(
  {
    _read_gate_manifest "$GATES_DIR/.agent-meta-managed"
    _read_gate_manifest "$GATES_DIR/.allowed-gates"
  } | sort -u
)

_gate_is_allowed() {
  printf '%s\n' "$ALLOWLIST" | grep -qxF "$1"
}

FAILED_GATES=()
SKIPPED_GATES=()
RAN_ANY=false

for gate_script in "$GATES_DIR"/*.sh; do
  [ -e "$gate_script" ] || continue  # literal glob with no matches
  gate_file="$(basename "$gate_script")"

  if ! _gate_is_allowed "$gate_file"; then
    echo "[SKIP] $gate_file: not on the release-gates allowlist — add it to $GATES_DIR/.allowed-gates to enable it (issue #598)."
    SKIPPED_GATES+=("$gate_file")
    continue
  fi

  RAN_ANY=true
  gate_name="$(basename "$gate_script" .sh)"
  echo "=== Running gate: $gate_name ==="
  if ! bash "$gate_script"; then
    FAILED_GATES+=("$gate_name")
  fi
  echo ""
done

if [ "$RAN_ANY" = "false" ]; then
  if [ "${#SKIPPED_GATES[@]}" -gt 0 ]; then
    echo "pre-release-check: $GATES_DIR has ${#SKIPPED_GATES[@]} script(s) but none are on the allowlist — nothing ran."
  else
    echo "pre-release-check: $GATES_DIR is empty — nothing to run."
  fi
  exit 0
fi

echo "=== Pre-Release Gate Dispatcher Summary ==="
if [ "${#SKIPPED_GATES[@]}" -gt 0 ]; then
  echo "NOTE: ${#SKIPPED_GATES[@]} script(s) skipped (not on allowlist): ${SKIPPED_GATES[*]}"
fi
if [ "${#FAILED_GATES[@]}" -gt 0 ]; then
  echo "RESULT: FAILED — ${#FAILED_GATES[@]} gate(s) blocked the release:"
  for g in "${FAILED_GATES[@]}"; do
    echo "  - $g"
  done
  exit 1
fi

echo "RESULT: all release gates passed"
exit 0
