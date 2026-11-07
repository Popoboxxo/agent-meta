#!/bin/bash
# hook: graphify-read-guard
# version: 1.2.0
# changelog: v1.2.0: exit status normalised to 0/2 -- only rc 2 with a guard message on stderr blocks, a graphify crash passes (#1151 F6-10)
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
# Exit status normalised to {0, 2} (#1151 F6-10): `exit $?` handed any
# graphify status to the harness. Only rc 2 WITH a guard message blocks;
# a crash (rc 1, 127, ...) or a reasonless rc 2 passes -- graphify routing
# is advisory, not a security boundary. stdout (the hook context) passes
# through untouched; stderr is captured and re-emitted.
exec 3>&1
_ERR=$(printf '%s' "$INPUT" | "$GRAPHIFY_BIN" hook-guard read 2>&1 1>&3 3>&-)
_RC=$?
exec 3>&-
if [ -n "$_ERR" ]; then
  printf '%s\n' "$_ERR" >&2
fi
if [ "$_RC" -eq 2 ] && [ -n "$_ERR" ]; then
  exit 2
fi
exit 0
