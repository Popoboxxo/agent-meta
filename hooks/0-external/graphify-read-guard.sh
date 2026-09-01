#!/bin/bash
# hook: graphify-read-guard
# version: 1.1.0
# event: PreToolUse
# matcher: Read|Glob
# description: Route Read/Glob calls through the locally installed graphify CLI's hook-guard (see config/external-tools-registry.yaml)
# enabled_by_default: false
# provider: Claude

set -uo pipefail

# GRAPHIFY_BIN is not trusted outright (issue #599) — hook_resolve_graphify_bin
# (hooks/1-generic/lib/hook_common.sh) only accepts an env-var override that
# is an absolute, non-group/other-writable path literally named "graphify"
# (or "graphify.exe"), otherwise falls back to a plain PATH lookup of the
# literal name "graphify". Not a security boundary either way (graphify not
# being installed/resolvable just passes the call through, exit 0) — this
# only closes the "arbitrary env var executes an arbitrary binary" gap.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if source "$SCRIPT_DIR/lib/hook_common.sh" 2>/dev/null; then
  GRAPHIFY_BIN="$(hook_resolve_graphify_bin)"
else
  GRAPHIFY_BIN="graphify"
fi

if ! command -v "$GRAPHIFY_BIN" >/dev/null 2>&1; then
  exit 0  # graphify nicht installiert -- durchlassen
fi
INPUT=$(cat)
printf '%s' "$INPUT" | "$GRAPHIFY_BIN" hook-guard read
exit $?
