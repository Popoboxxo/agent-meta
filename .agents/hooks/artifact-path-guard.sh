#!/bin/bash
# hook: artifact-path-guard
# version: 1.2.0
# event: PreToolUse
# matcher: ""
# description: Route artifact writes into the configured artifact-locations class path.
# changelog: 1.2.0: issue #1238b2 -- delegate artifact classification to the deployed flat hook_guard_artifact.py module; preserve routing statuses and fail-open behavior; 1.1.0: issue #1251 -- read the project anchor exclusively from adapter-owned AM_PROJECT_DIR; preserve payload-cwd walk-up and fail-open missing-data behavior
# enabled_by_default: false

# Routing convention, NOT a security boundary (issue #1186, T16, spec §4.5).
# AC-09 is fulfilled in two stages: the consistency check always warns (T14),
# this hook blocks legacy[] targets (both modes) and misroutes (strict only)
# once a project deliberately opts in.  Opt-in is why enabled_by_default is
# false: a default-active hook would block existing projects' audit-*.md files
# before the migration is even described.  Missing/corrupt data fails open.
#
# Reads <root>/.meta-config/artifact-locations.resolved.json (Stage 14c, T15),
# the single pre-resolved data file -- no Python resolver and no YAML per call.
# Marker -> unmanaged -> legacy -> class path -> managed tree -> root (D3).
# No content, extension or branch inspection; nothing is rewritten.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/hook_common.sh
source "$SCRIPT_DIR/lib/hook_common.sh"

INPUT=$(cat)

TOOL_NAME=$(hook_json_get "$INPUT" "tool_name")
FILE_PATH=$(hook_json_get "$INPUT" "tool_input.file_path")

# This hook only classifies targets for tool names the framework knows.  An
# unknown tool is not evidence of a misroute -- fail open (routing convention).
if ! hook_known_tool_name "$TOOL_NAME"; then
  exit 0
fi

# No target path: nothing to route.
if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Resolve the project root: $AM_PROJECT_DIR when it carries .meta-config/,
# else the nearest ancestor of the payload cwd holding the resolved data file.
ROOT=""
if [ -n "${AM_PROJECT_DIR:-}" ] && [ -d "$AM_PROJECT_DIR/.meta-config" ]; then
  ROOT="$AM_PROJECT_DIR"
else
  CWD_RAW=$(hook_json_get "$INPUT" "cwd")
  case "$CWD_RAW" in
    /*)
      dir="$CWD_RAW"
      while [ -n "$dir" ] && [ "$dir" != "/" ]; do
        if [ -f "$dir/.meta-config/artifact-locations.resolved.json" ]; then
          ROOT="$dir"
          break
        fi
        dir="$(dirname "$dir")"
      done
      ;;
  esac
fi
if [ -z "$ROOT" ]; then
  ROOT="${AM_PROJECT_DIR:-}"
fi

DATA_FILE="$ROOT/.meta-config/artifact-locations.resolved.json"

# Missing data file -> never block (fail-open, one warning line).
if [ ! -f "$DATA_FILE" ]; then
  echo "artifact-path-guard: WARN: data file $DATA_FILE missing; allowing (fail-open)" >&2
  exit 0
fi

MARKERS=".gitkeep .gitignore .keep"

# One stdlib JSON pass over the pre-resolved file; emits one status line:
# ALLOW | WARN:<message> | BLOCK:<message> | FAIL:<message>.
RESULT="$(python3 "$SCRIPT_DIR/lib/hook_guard_artifact.py" "$DATA_FILE" "$FILE_PATH" "$ROOT" "$MARKERS")"

case "$RESULT" in
  ALLOW)   exit 0 ;;
  WARN:*)  echo "${RESULT#WARN:}" >&2;  exit 0 ;;
  BLOCK:*) echo "${RESULT#BLOCK:}" >&2; exit 2 ;;
  FAIL:*)  echo "${RESULT#FAIL:}" >&2;  exit 0 ;;
  *)       exit 0 ;;   # unknown status -> fail open
esac
