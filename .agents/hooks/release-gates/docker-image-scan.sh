#!/bin/bash
# hook: docker-image-scan
# version: 1.1.0
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

GATE_NAME="docker-image-scan"

# --- Enabled/disabled ---
# Baked at sync-time by scripts/lib/hooks.py::sync_release_gates() from
# dod.resolve_release_gates() (project.yaml `release-gates.docker-image-scan.enabled`
# > dod-preset default > this header's `enabled_by_default`). The `:=` form
# only assigns when the var is still unset, so an explicit
# `PRE_RELEASE_GATE_ENABLED=false bash release-gates/docker-image-scan.sh`
# always wins for a one-off, single-gate override.
: "${PRE_RELEASE_GATE_ENABLED:=false}"

if [ "$PRE_RELEASE_GATE_ENABLED" != "true" ]; then
  echo "[SKIP] $GATE_NAME: gate disabled (release-gates.docker-image-scan.enabled=false)"
  exit 0
fi

# Dockerfile path — not part of the enabled/disabled resolution above;
# reserved for direct env var override only (no project.yaml key consumed
# by this specific gate beyond `enabled`, see docs/RELEASE_GATES.md).
DOCKERFILE="${PRE_RELEASE_DOCKERFILE_PATH:-Dockerfile}"

if [ ! -f "$DOCKERFILE" ]; then
  echo "[SKIP] $GATE_NAME: no $DOCKERFILE found"
  exit 0
fi

if ! command -v trivy &>/dev/null; then
  echo "[SKIP] $GATE_NAME: trivy not installed — install it to enable this gate"
  exit 0
fi

# Extract base images from FROM lines (ignore build-stage aliases like
# `FROM node:20 AS build` and multi-stage references back to a prior
# stage name, which are not pullable images).
stage_names=$(grep -iE '^FROM\s' "$DOCKERFILE" | awk 'toupper($0) ~ /AS/ {for(i=1;i<=NF;i++) if(toupper($i)=="AS") print $(i+1)}')

images=$(grep -iE '^FROM\s' "$DOCKERFILE" | awk '{print $2}')

HAD_FAILURE=false
while IFS= read -r image; do
  [ -z "$image" ] && continue
  if printf '%s' "$stage_names" | grep -qxF "$image"; then
    continue  # reference to an earlier build stage, not a pullable image
  fi
  echo "[INFO] $GATE_NAME: scanning $image"
  trivy_output=$(trivy image --severity HIGH,CRITICAL --exit-code 1 "$image" 2>&1)
  trivy_exit=$?
  echo "$trivy_output"
  if [ "$trivy_exit" -ne 0 ]; then
    echo "[FAIL] $GATE_NAME: $image has HIGH/CRITICAL vulnerabilities — see trivy output above"
    HAD_FAILURE=true
  fi
done <<< "$images"

if [ "$HAD_FAILURE" = "true" ]; then
  exit 1
fi
echo "[INFO] $GATE_NAME: all base images clean"
exit 0
