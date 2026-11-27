#!/bin/bash
# hook: artifact-freshness
# version: 1.2.0
# event: Manual
# description: Pre-release gate — blocks release if a generated artifact is older than the source it was built from (config: .meta-config/generated-artifacts.yaml; fallback when that file does not exist: generated-artifacts.yaml)
# changelog: 1.2.0: issue #1238c2 -- delegate artifact parsing and freshness comparison to the deployed flat hook_gate_artifact_freshness.py module; resolve it from the hook lib directory and preserve messages, git-first timestamps, self-skips and exit codes
# enabled_by_default: false

# --- Gate contract (see docs/RELEASE_GATES.md) ---
# Run standalone (`bash release-gates/artifact-freshness.sh`) or via the
# release-gates/ dispatcher (pre-release-check.sh). Exit 0 = pass or
# self-skip (disabled, or prerequisites missing). Exit non-zero = fail,
# blocks the release.

set -u

PROJECT_ROOT="${PROJECT_ROOT:-$PWD}"
cd "$PROJECT_ROOT" || exit 1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_LIB_DIR="$(cd "$SCRIPT_DIR/../lib" && pwd)"
source "$HOOK_LIB_DIR/hook_common.sh" 2>/dev/null || exit 0

GATE_NAME="artifact-freshness"

# --- Enabled/disabled ---
# Baked at sync-time by scripts/lib/hooks.py::sync_release_gates() from
# dod.resolve_release_gates() (project.yaml `release-gates.artifact-freshness.enabled`
# > dod-preset default > this header's `enabled_by_default`). The `:=` form
# only assigns when the var is still unset, so an explicit
# `PRE_RELEASE_GATE_ENABLED=false bash release-gates/artifact-freshness.sh`
# always wins for a one-off, single-gate override. Shared skip/message logic
# lives in hook_gate_check_enabled() (lib/hook_common.sh).
: "${PRE_RELEASE_GATE_ENABLED:=false}"
hook_gate_check_enabled "$GATE_NAME" || exit 0

# --- Config convention ---
# .meta-config/generated-artifacts.yaml at the consumer project root, falling
# back to generated-artifacts.yaml when that file does not exist (the fallback
# is chosen by file absence, not by the absence of the .meta-config/
# directory). The primary path wins when both exist.
# Supported subset (stdlib-only, NOT a full YAML parser):
#
#   artifacts:
#     - source: VERSION
#       generated: dist/manifest.json
#     - source: src/schema.py
#       generated: docs/api/schema.json
#
# One list under a single top-level `artifacts:` key; each entry is a
# `- source: <path-or-glob>` / `generated: <path-or-glob>` pair on two
# consecutive lines. No nesting, no anchors, no multi-line scalars.
CONFIG_FILE=""
for candidate in ".meta-config/generated-artifacts.yaml" "generated-artifacts.yaml"; do
  if [ -f "$candidate" ]; then
    CONFIG_FILE="$candidate"
    break
  fi
done
if [ -z "$CONFIG_FILE" ]; then
  echo "[SKIP] $GATE_NAME: no .meta-config/generated-artifacts.yaml or generated-artifacts.yaml found — opt-in check not configured"
  exit 0
fi

if ! command -v python3 &>/dev/null; then
  echo "[SKIP] $GATE_NAME: python3 not available — cannot parse config"
  exit 0
fi

python3 "$HOOK_LIB_DIR/hook_gate_artifact_freshness.py" "$CONFIG_FILE" "$GATE_NAME"
