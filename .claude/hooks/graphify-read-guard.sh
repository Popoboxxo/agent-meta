#!/bin/bash
# hook: graphify-read-guard
# version: 1.0.0
# event: PreToolUse
# matcher: Read|Glob
# description: Route Read/Glob calls through the locally installed graphify CLI's hook-guard (see config/external-tools-registry.yaml)
# enabled_by_default: false
# provider: Claude

GRAPHIFY_BIN="${GRAPHIFY_BIN:-graphify}"
if ! command -v "$GRAPHIFY_BIN" >/dev/null 2>&1; then
  exit 0  # graphify nicht installiert -- durchlassen
fi
INPUT=$(cat)
echo "$INPUT" | "$GRAPHIFY_BIN" hook-guard read
exit $?
