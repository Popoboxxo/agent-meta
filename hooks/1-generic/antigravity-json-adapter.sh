#!/bin/bash
# antigravity-json-adapter — Antigravity <-> Claude Code hook-contract adapter
# version: 1.0.0
# description: Translates Google Antigravity's verified hook contract (hooks.json) to the Claude Code contract hooks/1-generic/*.sh are written against (issue #674 Phase 3.1)
#
# NOT a hook itself — no `# hook:`/`# event:` header, so scripts/lib/hooks.py
# never registers it as its own hook entry. It is referenced as the `command`
# of EVERY hook registered in .agents/hooks.json (hook_protocol:
# antigravity-hooks-json) and bridges the two contracts:
#
#   Antigravity (verified, antigravity.google/docs/hooks, state 2026-09):
#     stdin : {"hookEventName", "toolCall": {"name", "args"}, "stepIdx",
#              "conversationId", "workspacePaths", "transcriptPath", ...}
#     stdout: {"decision": "allow"|"deny", "reason": ...}   (PreToolUse gate)
#   Claude Code (what every hooks/1-generic script expects):
#     stdin : {"hook_event_name", "tool_name", "tool_input": {...}, "cwd", ...}
#     block : exit code 2, reason on stderr
#
# Usage (as written by scripts/lib/hooks.py into hooks.json):
#   "command": "bash ./hooks/antigravity-json-adapter.sh orchestrator-guard.sh"
# The target script is resolved relative to THIS adapter's own directory
# (cwd-independent). The target's stdout is always suppressed — Antigravity
# parses stdout as the decision JSON, so a target that echoes to stdout must
# never reach it.
#
# Failure semantics:
#   * Missing/unreadable $1  -> stderr warning, exit 0 (fail-OPEN). A broken
#     registration is a deployment bug; blocking EVERY tool call on it would
#     be the self-lockout class of failure the hook layer deliberately avoids
#     (see orchestrator-guard.sh's self-health rationale). hooks.py's
#     post-write verification already warns about missing deployed files.
#   * Unparseable payload or no python interpreter on a PreToolUse event
#     -> {"decision": "deny"} on stdout (fail-CLOSED, issue #595 posture:
#     this adapter fronts the security hooks — a guard that cannot run must
#     not silently allow). Non-PreToolUse events pass (they cannot block).
#   * Target exit 2 on PreToolUse -> {"decision": "deny", "reason": <stderr>}
#     (verified Antigravity deny contract). Any other exit -> no output
#     (empty stdout = no hook opinion; it deliberately does NOT emit
#     {"decision": "allow"} — that would auto-allow and bypass Antigravity's
#     own permission prompts).
#
# Known limitation (P6 real-repo test, issue #674): the AGY runtime's exact
# command-execution semantics (argv-split vs. literal path) are documented
# only by third-party empirical reports and contradict each other across AGY
# flavours; the registered `bash ./hooks/<adapter> <target>` form follows the
# official docs' relative-path examples and the empirically working
# interpreter+args pattern. Re-verify in a real AGY IDE session.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_NAME="${1:-}"
INPUT=$(cat)

if [ -z "$TARGET_NAME" ]; then
  echo "ANTIGRAVITY_ADAPTER: no target hook script argument — registration bug, skipping hook (fail-open)." >&2
  exit 0
fi
TARGET="$SCRIPT_DIR/$TARGET_NAME"
if [ ! -f "$TARGET" ]; then
  echo "ANTIGRAVITY_ADAPTER: target hook script not found: $TARGET (re-run sync.py) — skipping hook (fail-open)." >&2
  exit 0
fi

# --- Python resolution (stdlib-only, mirrors lib/hook_common.sh) ---------
PY=""
if command -v python3 >/dev/null 2>&1; then
  PY="python3"
elif command -v python >/dev/null 2>&1; then
  PY="python"
fi

if [ -z "$PY" ]; then
  echo "ANTIGRAVITY_ADAPTER: no python interpreter on PATH (issue #595 posture) — failing closed." >&2
  printf '%s\n' '{"decision": "deny", "reason": "ANTIGRAVITY_ADAPTER: no python interpreter on PATH — agent-meta hooks cannot be evaluated."}'
  exit 0
fi

# --- Payload translation: Antigravity -> Claude Code shape ---------------
# Adds the Claude-contract keys the generic hook scripts parse
# (hook_event_name, tool_name, tool_input, cwd) while keeping the original
# AGY fields for forward compatibility.
TRANSLATED=$(printf '%s' "$INPUT" | "$PY" -c "
import json, sys

try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(3)
if not isinstance(d, dict):
    sys.exit(3)

# Verified AGY built-ins -> Claude Code canonical names the generic hooks
# gate on (orchestrator-guard-impl.sh intercepts Write|Edit|Bash). Names are
# from the official docs' matcher examples + observed AGY tool-call logs
# (run_command, write_to_file, replace_file_content, read_file, view_file,
# list_dir, manage_task); unknown names pass through unchanged — the hook
# scripts then treat them as non-mutating (fail-open for non-Bash tools).
TOOL_MAP = {
    'run_command': 'Bash',
    'write_to_file': 'Write',
    'replace_file_content': 'Edit',
    'multi_replace_file_content': 'Edit',
    'read_file': 'Read',
    'view_file': 'Read',
    'list_dir': 'LS',
    'manage_task': 'Task',
}
# Documented AGY run_command arguments (PascalCase) -> Claude tool_input keys.
ARG_KEY_MAP = {'CommandLine': 'command', 'Cwd': 'cwd'}

event = str(d.get('hookEventName') or d.get('hook_event_name') or '')
tool_call = d.get('toolCall') if isinstance(d.get('toolCall'), dict) else {}
raw_name = str(tool_call.get('name') or d.get('tool_name') or '')
args = tool_call.get('args') if isinstance(tool_call.get('args'), dict) else {}

tool_input = dict(d.get('tool_input')) if isinstance(d.get('tool_input'), dict) else {}
for k, v in args.items():
    tool_input[ARG_KEY_MAP.get(k, k)] = v

workspace_paths = d.get('workspacePaths')
cwd = d.get('cwd')
if not cwd and isinstance(workspace_paths, list) and workspace_paths:
    cwd = workspace_paths[0]
if not cwd:
    cwd = args.get('Cwd') or ''

out = dict(d)
out['hook_event_name'] = event or 'PreToolUse'
out['hookEventName'] = event
out['tool_name'] = TOOL_MAP.get(raw_name, raw_name)
out['tool_input'] = tool_input
out['cwd'] = cwd
json.dump(out, sys.stdout)
")
_TRANSLATE_RC=$?

if [ "$_TRANSLATE_RC" -ne 0 ]; then
  # Unparseable payload (exit 3): cannot tell what the call would have been.
  # PreToolUse is the blocking event -> deny (fail-closed); other events
  # cannot block anything, so pass.
  if [ "$_TRANSLATE_RC" = "3" ]; then
    echo "ANTIGRAVITY_ADAPTER: hook payload is not valid JSON — failing closed (issue #595 posture)." >&2
    printf '%s\n' '{"decision": "deny", "reason": "ANTIGRAVITY_ADAPTER: hook payload was not parseable JSON — agent-meta hooks cannot evaluate this call."}'
    exit 0
  fi
  echo "ANTIGRAVITY_ADAPTER: payload translation failed (exit $_TRANSLATE_RC) — skipping hook (fail-open)." >&2
  exit 0
fi

# The event name is already inside the translated payload — read it back
# once. Translation succeeded above, so this parse cannot fail; an empty
# result falls back to PreToolUse (the fail-closed direction for the
# exit-2 verdict below).
EVENT=$(printf '%s' "$TRANSLATED" | "$PY" -c "
import json, sys
try:
    print(json.load(sys.stdin).get('hook_event_name') or 'PreToolUse')
except Exception:
    print('PreToolUse')
" 2>/dev/null)

# --- Run the real hook with the translated payload ------------------------
# Target stdout is ALWAYS suppressed (Antigravity would parse it as the
# decision JSON); stderr is captured for the deny reason.
_ERR_FILE=$(mktemp)
trap 'rm -f "$_ERR_FILE"' EXIT
printf '%s' "$TRANSLATED" | bash "$TARGET" >/dev/null 2>"$_ERR_FILE"
_TARGET_EXIT=$?

# --- Translate the target's verdict back to the AGY contract --------------
if [ "$_TARGET_EXIT" = "2" ]; then
  # PreToolUse is the only blocking tool event — for Stop/PreInvocation/
  # PostInvocation an exit 2 carries no AGY meaning (they cannot block);
  # emit nothing there.
  if [ "$EVENT" = "PreToolUse" ]; then
    "$PY" -c "
import json, sys
reason = sys.stdin.read().strip() or 'blocked by agent-meta hook'
print(json.dumps({'decision': 'deny', 'reason': reason}))
" < "$_ERR_FILE"
    exit 0
  fi
fi

exit 0
