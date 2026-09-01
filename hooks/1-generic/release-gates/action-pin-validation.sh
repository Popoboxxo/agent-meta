#!/bin/bash
# hook: action-pin-validation
# version: 1.1.0
# event: Manual
# description: Pre-release gate — validates that every pinned GitHub Action ref (tag or full SHA) in .github/workflows/*.yml still exists upstream
# enabled_by_default: false

# --- Gate contract (see docs/RELEASE_GATES.md) ---
# Run standalone (`bash release-gates/action-pin-validation.sh`) or via the
# release-gates/ dispatcher (pre-release-check.sh). Exit 0 = pass or
# self-skip (disabled, or prerequisites missing). Exit non-zero = fail,
# blocks the release.

set -uo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$PWD}"
cd "$PROJECT_ROOT" || exit 1

GATE_NAME="action-pin-validation"

# --- Enabled/disabled ---
# Baked at sync-time by scripts/lib/hooks.py::sync_release_gates() from
# dod.resolve_release_gates() (project.yaml `release-gates.action-pin-validation.enabled`
# > dod-preset default > this header's `enabled_by_default`). The `:=` form
# only assigns when the var is still unset, so an explicit
# `PRE_RELEASE_GATE_ENABLED=false bash release-gates/action-pin-validation.sh`
# always wins for a one-off, single-gate override.
: "${PRE_RELEASE_GATE_ENABLED:={{RELEASE_GATE_ENABLED_DEFAULT}}}"

if [ "$PRE_RELEASE_GATE_ENABLED" != "true" ]; then
  echo "[SKIP] $GATE_NAME: gate disabled (release-gates.action-pin-validation.enabled=false)"
  exit 0
fi

if ! compgen -G ".github/workflows/*.yml" >/dev/null 2>&1 && ! compgen -G ".github/workflows/*.yaml" >/dev/null 2>&1; then
  echo "[SKIP] $GATE_NAME: no .github/workflows/*.yml found"
  exit 0
fi

if ! command -v gh &>/dev/null; then
  echo "[SKIP] $GATE_NAME: gh CLI not installed — install/authenticate it to enable this gate"
  exit 0
fi

if ! gh auth status &>/dev/null; then
  echo "[SKIP] $GATE_NAME: gh CLI not authenticated — run 'gh auth login' to enable this gate"
  exit 0
fi

pins=$(grep -hoE 'uses:\s*[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+' .github/workflows/*.yml .github/workflows/*.yaml 2>/dev/null \
  | sed -E 's/uses:\s*//' | sort -u)

HAD_FAILURE=false
while IFS= read -r pin; do
  [ -z "$pin" ] && continue
  repo_part="${pin%@*}"
  ref="${pin##*@}"
  owner="${repo_part%%/*}"
  repo="${repo_part#*/}"
  # actions/checkout-style repos can have subpaths (owner/repo/subdir) —
  # keep only owner/repo for the API call.
  repo="$(printf '%s' "$repo" | cut -d/ -f1)"

  if [[ "$ref" =~ ^[0-9a-fA-F]{40}$ ]]; then
    # Full SHA pin — verify the commit still exists upstream.
    if ! gh api "repos/$owner/$repo/commits/$ref" &>/dev/null; then
      echo "[FAIL] $GATE_NAME: $owner/$repo@$ref — commit not found upstream (rebased/deleted?)"
      HAD_FAILURE=true
    fi
  else
    # Assume tag pin — verify the tag ref still exists.
    if ! gh api "repos/$owner/$repo/git/ref/tags/$ref" &>/dev/null; then
      echo "[FAIL] $GATE_NAME: $owner/$repo@$ref — tag not found upstream (moved/deleted?)"
      HAD_FAILURE=true
    fi
  fi
done <<< "$pins"

if [ "$HAD_FAILURE" = "true" ]; then
  exit 1
fi
echo "[INFO] $GATE_NAME: all action pins verified"
exit 0
