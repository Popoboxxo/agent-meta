#!/bin/bash
# hook: docker-image-scan
# version: 1.2.0
# changelog: 1.2.0 - scan multiple/auto-discovered Dockerfiles (#745)
# event: Manual
# description: Pre-release gate — scans Docker base images (FROM lines) with trivy for HIGH/CRITICAL CVEs before release
# enabled_by_default: false

# --- Gate contract (see docs/RELEASE_GATES.md) ---
# Run standalone (`bash release-gates/docker-image-scan.sh`) or via the
# release-gates/ dispatcher (pre-release-check.sh). Exit 0 = pass or
# self-skip (disabled, or prerequisites missing). Exit non-zero = fail,
# blocks the release.

set -uo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$PWD}"
cd "$PROJECT_ROOT" || exit 1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/hook_common.sh" 2>/dev/null || exit 0

GATE_NAME="docker-image-scan"

# --- Enabled/disabled ---
# Baked at sync-time by scripts/lib/hooks.py::sync_release_gates() from
# dod.resolve_release_gates() (project.yaml `release-gates.docker-image-scan.enabled`
# > dod-preset default > this header's `enabled_by_default`). The `:=` form
# only assigns when the var is still unset, so an explicit
# `PRE_RELEASE_GATE_ENABLED=false bash release-gates/docker-image-scan.sh`
# always wins for a one-off, single-gate override. Shared skip/message logic
# lives in hook_gate_check_enabled() (lib/hook_common.sh).
: "${PRE_RELEASE_GATE_ENABLED:={{RELEASE_GATE_ENABLED_DEFAULT}}}"
hook_gate_check_enabled "$GATE_NAME" || exit 0

# Dockerfile path resolution — not part of the enabled/disabled resolution
# above (no project.yaml key consumed by this gate beyond `enabled`, see
# docs/RELEASE_GATES.md). Precedence, highest first:
#   1. PRE_RELEASE_DOCKERFILE_PATHS — explicit list (newline- or
#      colon-separated), for projects with several Dockerfiles (#745).
#   2. PRE_RELEASE_DOCKERFILE_PATH  — explicit single path (pre-#745
#      override, kept for backward compat).
#   3. Root ./Dockerfile if present (pre-#745 default, kept for backward
#      compat).
#   4. Auto-discovery: every Dockerfile under the project root, excluding
#      node_modules/vendor/.git/.tmp.
dockerfiles=()
if [ -n "${PRE_RELEASE_DOCKERFILE_PATHS:-}" ]; then
  # `|| [ -n "$path" ]` keeps the last entry even when the substituted
  # stream has no trailing newline (read's normal loop-condition failure
  # on a final unterminated line would otherwise silently drop it).
  while IFS= read -r path || [ -n "$path" ]; do
    [ -n "$path" ] && dockerfiles+=("$path")
  done < <(printf '%s' "$PRE_RELEASE_DOCKERFILE_PATHS" | tr ':' '\n')
elif [ -n "${PRE_RELEASE_DOCKERFILE_PATH:-}" ]; then
  dockerfiles+=("$PRE_RELEASE_DOCKERFILE_PATH")
elif [ -f "Dockerfile" ]; then
  dockerfiles+=("Dockerfile")
else
  while IFS= read -r path || [ -n "$path" ]; do
    [ -n "$path" ] && dockerfiles+=("$path")
  done < <(find . -name Dockerfile \
    -not -path '*/node_modules/*' \
    -not -path '*/vendor/*' \
    -not -path '*/.git/*' \
    -not -path '*/.tmp/*')
fi

if [ "${#dockerfiles[@]}" -eq 0 ]; then
  echo "[SKIP] $GATE_NAME: no Dockerfile found"
  exit 0
fi

if ! command -v trivy &>/dev/null; then
  echo "[SKIP] $GATE_NAME: trivy not installed — install it to enable this gate"
  exit 0
fi

HAD_FAILURE=false
for dockerfile in "${dockerfiles[@]}"; do
  if [ ! -f "$dockerfile" ]; then
    echo "[SKIP] $GATE_NAME: $dockerfile not found"
    continue
  fi

  # Extract base images from FROM lines (ignore build-stage aliases like
  # `FROM node:20 AS build` and multi-stage references back to a prior
  # stage name, which are not pullable images).
  stage_names=$(grep -iE '^FROM\s' "$dockerfile" | awk 'toupper($0) ~ /AS/ {for(i=1;i<=NF;i++) if(toupper($i)=="AS") print $(i+1)}')

  images=$(grep -iE '^FROM\s' "$dockerfile" | awk '{print $2}')

  while IFS= read -r image; do
    [ -z "$image" ] && continue
    if printf '%s' "$stage_names" | grep -qxF "$image"; then
      continue  # reference to an earlier build stage, not a pullable image
    fi
    echo "[INFO] $GATE_NAME: scanning $image ($dockerfile)"
    trivy_output=$(trivy image --severity HIGH,CRITICAL --exit-code 1 "$image" 2>&1)
    trivy_exit=$?
    echo "$trivy_output"
    if [ "$trivy_exit" -ne 0 ]; then
      echo "[FAIL] $GATE_NAME: $image ($dockerfile) has HIGH/CRITICAL vulnerabilities — see trivy output above"
      HAD_FAILURE=true
    fi
  done <<< "$images"
done

if [ "$HAD_FAILURE" = "true" ]; then
  exit 1
fi
echo "[INFO] $GATE_NAME: all base images clean"
exit 0
