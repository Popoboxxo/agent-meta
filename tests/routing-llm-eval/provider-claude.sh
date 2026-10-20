#!/bin/bash
# promptfoo-style custom provider: shells out to the real `claude` CLI using an
# agent-meta GENERATED artifact as system prompt.
#
# v2 (issue #535, findings #523):
#   * --agent <role> : every role (orchestrator included, see v4) uses
#                      .claude/agents/<role>.md WITH frontmatter stripped
#                      (finding H3: frontmatter would be injected as prompt
#                      garbage via --system-prompt-file).
#                      Missing/unknown role => exit 2 (finding W6).
#   * Structured sidecar identical to provider-opencode.sh v2 (finding B1):
#     claude -p does not stream structured events, so tool_events stays empty
#     and the sidecar carries final_text + a marker field "stream": false.
#
# Isolation unchanged: run from a throwaway tmp dir so repo CLAUDE.md /
# .claude/rules auto-discovery cannot leak into the session (--bare would
# need ANTHROPIC_API_KEY which OAuth setups do not have).
#
# v3 (issue #539): EVAL_ISOLATION=repo-readonly (default: none, unchanged
#   behavior) additionally seeds RUN_DIR with the repo's tracked files
#   before the system-prompt file is written below, so file-dependent
#   roles (agent-meta-manager, documenter, ...) can actually find sync.py /
#   templates / docs instead of starving in tool-call loops until timeout.
#   See comment at the copy site for why copy-not-mount.
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

EVAL_ISOLATION="${EVAL_ISOLATION:-none}"
if [[ "$EVAL_ISOLATION" == "repo-readonly" ]]; then
  # issue #539: seed RUN_DIR with the repo's tracked files so file-dependent
  # roles can find sync.py / templates / docs. `git ls-files` naturally
  # respects .gitignore (no .git/.venv/node_modules/external -- none of
  # those are tracked), so the copy stays small without a manual exclude
  # list. Copy instead of a bind-mount: a non-root read-only bind mount is
  # not reliably available in this sandbox, and a plain copy already gives
  # the isolation property that matters here (the role can't corrupt the
  # real repo, since it never writes to it) without needing root.
  (cd "$REPO_ROOT" && git ls-files -z | tar --null -T - -cf -) | tar -xf - -C "$RUN_DIR"
fi

# v4 (IC-13, Task 1.35 follow-up): every role -- including the orchestrator --
# uses the RENDERED .claude/agents/<role>.md of the active profile with
# frontmatter stripped. The former orchestrator source
# (.claude/rules/use-orchestrator.md) was only a stub, not the routing prompt.
SRC_AGENT="$REPO_ROOT/.claude/agents/${ROLE}.md"
if [[ ! -f "$SRC_AGENT" ]]; then
  echo "provider-claude: unknown or missing role file: $SRC_AGENT (run 'python3 scripts/sync.py' first to render the agents)" >&2
  exit 2
fi
SYSTEM_FILE="$RUN_DIR/system-prompt.md"
# Strip YAML frontmatter (H3): everything from the first '---' line up to
# the second '---' line, inclusive. If no frontmatter present, copy as-is.
awk 'BEGIN{fm=0; done=0} NR==1 && /^---[[:space:]]*$/{fm=1; next} fm && /^---[[:space:]]*$/{fm=0; done=1; next} done||!fm{print}' \
  "$SRC_AGENT" > "$SYSTEM_FILE"

# IC-13 output contract: the routing eval asserts on a JSON object. Only the
# eval runner (and a promptfoo run with the same env var) opts in, so the
# behavioral catalogs keep their normal prose answers.
CONTRACT_FILE="${EVAL_OUTPUT_CONTRACT:-}"
if [[ -n "$CONTRACT_FILE" ]]; then
  if [[ ! -f "$CONTRACT_FILE" ]]; then
    echo "provider-claude: EVAL_OUTPUT_CONTRACT file not found: $CONTRACT_FILE" >&2
    exit 2
  fi
  { printf '\n\n'; cat "$CONTRACT_FILE"; } >> "$SYSTEM_FILE"
fi

# v5 (issue #977): capture claude's stderr and check the exit status explicitly.
# Under plain `set -e` a failed invocation (e.g. "Not logged in") aborted the
# wrapper with exit 1 and no diagnosis; promptfoo then reported an opaque
# provider error. Failures now exit 2 with claude's own stderr re-emitted.
STDERR_FILE="$RUN_DIR/claude.stderr"
set +e
OUTPUT_TEXT="$(
  cd "$RUN_DIR"
  claude -p \
    --system-prompt-file "$SYSTEM_FILE" \
    --model "${CLAUDE_ROUTING_EVAL_MODEL:-haiku}" \
    "$PROMPT" 2>"$STDERR_FILE"
)"
STATUS=$?
set -e

if [[ $STATUS -ne 0 ]]; then
  echo "provider-claude: claude invocation failed (exit $STATUS) — check 'claude auth status' / ANTHROPIC_API_KEY" >&2
  if [[ -s "$STDERR_FILE" ]]; then
    sed 's/^/provider-claude: /' "$STDERR_FILE" >&2
  fi
  exit 2
fi

# Success: keep claude's stderr (warnings) visible instead of dropping it.
if [[ -s "$STDERR_FILE" ]]; then
  cat "$STDERR_FILE" >&2
fi

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
