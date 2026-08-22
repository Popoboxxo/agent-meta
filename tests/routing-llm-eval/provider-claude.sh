#!/bin/bash
# promptfoo-style custom provider: shells out to the real `claude` CLI using an
# agent-meta GENERATED artifact as system prompt.
#
# v2 (issue #535, findings #523):
#   * --agent <role> : orchestrator keeps its legacy source
#                      (.claude/rules/use-orchestrator.md, no frontmatter),
#                      every other role uses .claude/agents/<role>.md WITH
#                      frontmatter stripped (finding H3: frontmatter would be
#                      injected as prompt garbage via --system-prompt-file).
#                      Missing/unknown role => exit 2 (finding W6).
#   * Structured sidecar identical to provider-opencode.sh v2 (finding B1):
#     claude -p does not stream structured events, so tool_events stays empty
#     and the sidecar carries final_text + a marker field "stream": false.
#
# Isolation unchanged: run from a throwaway tmp dir so repo CLAUDE.md /
# .claude/rules auto-discovery cannot leak into the session (--bare would
# need ANTHROPIC_API_KEY which OAuth setups do not have).
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

ROLE="orchestrator"
PROMPT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)
      ROLE="$2"
      shift 2
      ;;
    --agent=*)
      ROLE="${1#*=}"
      shift
      ;;
    *)
      PROMPT="$1"
      shift
      ;;
  esac
done

RUN_DIR="$(mktemp -d)"
trap 'rm -rf "$RUN_DIR"' EXIT

SYSTEM_FILE=""
if [[ "$ROLE" == "orchestrator" ]]; then
  SYSTEM_FILE="$REPO_ROOT/.claude/rules/use-orchestrator.md"
else
  SRC_AGENT="$REPO_ROOT/.claude/agents/${ROLE}.md"
  if [[ ! -f "$SRC_AGENT" ]]; then
    echo "provider-claude: unknown or missing role file: $SRC_AGENT" >&2
    exit 2
  fi
  SYSTEM_FILE="$RUN_DIR/system-prompt.md"
  # Strip YAML frontmatter (H3): everything from the first '---' line up to
  # the second '---' line, inclusive. If no frontmatter present, copy as-is.
  awk 'BEGIN{fm=0; done=0} NR==1 && /^---[[:space:]]*$/{fm=1; next} fm && /^---[[:space:]]*$/{fm=0; done=1; next} done||!fm{print}' \
    "$SRC_AGENT" > "$SYSTEM_FILE"
fi

OUTPUT_TEXT="$(
  cd "$RUN_DIR"
  claude -p \
    --system-prompt-file "$SYSTEM_FILE" \
    --model "${CLAUDE_ROUTING_EVAL_MODEL:-haiku}" \
    "$PROMPT"
)"

printf '%s\n' "$OUTPUT_TEXT"

# Structured sidecar (B1): claude -p has no event stream; be honest about it.
if [[ -n "${EVAL_STRUCTURED_OUTPUT:-}" ]]; then
  printf '%s' "$OUTPUT_TEXT" | ROLE="$ROLE" OUT="$EVAL_STRUCTURED_OUTPUT" python3 -c '
import json, os, sys
text = sys.stdin.read()
payload = {
    "provider": "claude",
    "role": os.environ["ROLE"],
    "stream": False,
    "final_text": text,
    "event_counts": {},
    "tool_events": [],
    "spawn_attempts": 0,
}
with open(os.environ["OUT"], "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False)
'
fi
