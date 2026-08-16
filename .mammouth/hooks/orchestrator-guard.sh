#!/bin/bash
# hook: orchestrator-guard
# version: 2.3.0
# event: PreToolUse
# matcher: ""
# description: Block non-orchestrator write/edit/bash calls when orchestrator.strict=true; also block direct git mutations in non-strict mode
# enabled_by_default: true

# This hook is always active (enabled_by_default: true).
# It self-checks whether orchestrator.strict mode is enabled in project.yaml.
# If strict mode is off, the hook exits 0 immediately and imposes no overhead.
#
# Only mutating tools (Write, Edit, Bash) are intercepted.
# Research tools (read, glob, grep) are never blocked.
#
# Exit codes: 0 = allow, 2 = block.
#
# On exit 2 the harness feeds *stderr* back to the model as the block reason
# and ignores stdout. Writing the guard message to stdout (as versions <=2.1.0
# did) therefore surfaced a bare "hook error: No stderr output" instead of the
# explanation — the block worked, the reason was lost (issue #396). Every
# message emitted on a blocking path must go to stderr.
#
# Identity note (see agent-meta issue #390): no provider's PreToolUse hook
# payload identifies which subagent issued the call — Claude Code's
# documented payload is {session_id, transcript_path, hook_event_name,
# tool_name, tool_input} only, with no agent/subagent field. The only
# channel a hook can read without corrupting tool semantics is the `Bash`
# `command` string itself. Authorized delegates (git, orchestrator agent
# templates) therefore self-declare by prefixing every Bash command with a
# sentinel comment line: `#agent-meta:agent=<name>`. This is a soft,
# self-reported convention (matches the framework's existing A2A trust
# model, see .claude/rules/a2a-delegation-gates.md) — it is not a security
# boundary against a malicious agent, only a fix for the identification gap.
# Write/Edit have no such safe channel (a marker would corrupt file
# content), so they are never exempted under strict mode.

INPUT=$(cat)

# Try python first, then python3
_PY=""
if command -v python >/dev/null 2>&1; then
  _PY="python"
elif command -v python3 >/dev/null 2>&1; then
  _PY="python3"
fi

if [ -z "$_PY" ]; then
  # No Python available — cannot parse JSON/YAML; allow through to avoid breakage
  exit 0
fi

TOOL_NAME=$(echo "$INPUT" | $_PY -c "import json,sys; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")

# If no tool name: startup or other events — allow through
if [ -z "$TOOL_NAME" ]; then
  exit 0
fi

# Only block mutating tools
case "$TOOL_NAME" in
  Write|Edit|Bash) ;;
  *) exit 0 ;;
esac

BASH_CMD=""
if [ "$TOOL_NAME" = "Bash" ]; then
  BASH_CMD=$(echo "$INPUT" | $_PY -c "
import json, sys
d = json.load(sys.stdin)
inp = d.get('tool_input', {})
print(inp.get('command', '') if isinstance(inp, dict) else '')
" 2>/dev/null || echo "")

  # Self-declared agent identity (see note above): the first non-blank line
  # of the command must be exactly '#agent-meta:agent=<name>'. Only
  # orchestrator and git are recognized delegates for this guard.
  # `head -n1` alone (pre-#503) grabbed a literal empty first line whenever
  # BASH_CMD started with a leading newline before the sentinel -- some
  # delegated agents construct their Bash invocation that way -- so the
  # sentinel was silently missed and the legitimate mutation got blocked.
  # Stripping leading whitespace/blank lines before taking "line 1" makes
  # detection tolerant of that construction.
  DECLARED_AGENT=$(printf '%s' "$BASH_CMD" | $_PY -c "
import re, sys
content = sys.stdin.read().lstrip()
line = content.split('\n', 1)[0].strip()
m = re.match(r'^#agent-meta:agent=([A-Za-z0-9_-]+)$', line)
print(m.group(1) if m else '')
" 2>/dev/null || echo "")

  if echo "$DECLARED_AGENT" | grep -qiE '^(orchestrator|git)$'; then
    exit 0
  fi
fi

# Determine project root
PROJECT_ROOT=$(echo "$INPUT" | $_PY -c "import json,sys; print(json.load(sys.stdin).get('cwd',''))" 2>/dev/null || echo "")
if [ -z "$PROJECT_ROOT" ]; then
  PROJECT_ROOT="$PWD"
fi

# Check if strict mode is enabled in project.yaml
CONFIG_FILE="$PROJECT_ROOT/.meta-config/project.yaml"
# Baked in by sync.py's per-provider copy step (scripts/lib/hooks.py) —
# stays the literal placeholder text only if this file was never synced
# (e.g. run straight from hooks/1-generic/), which the lookup below
# treats as "no provider override applies".
AGENT_META_PROVIDER="Mammouth"

if [ -f "$CONFIG_FILE" ]; then
  # CONFIG_FILE is passed as argv, never interpolated into the python
  # source string — a Windows path contains backslashes, and shell-into-
  # string-literal interpolation lets python's own string-escape parsing
  # (\a, \n, ...) silently corrupt the path, making open() fail and the
  # except-branch print 'false' as if strict mode were off.
  STRICT=$("$_PY" -c "
import sys, yaml

CONFIG_FILE, PROVIDER = sys.argv[1], sys.argv[2]

def resolve_mode(orch, provider):
    override = orch.get('provider-overrides', {}).get(provider, {})
    mode = override.get('mode')
    if mode is not None:
        return mode
    return orch.get('mode')

try:
    with open(CONFIG_FILE) as f:
        c = yaml.safe_load(f) or {}
    orch = c.get('orchestrator', {})
    mode = resolve_mode(orch, PROVIDER)
    if mode is not None:
        mode = str(mode).strip().lower()
        print('true' if mode == 'strict' else 'false')
    else:
        strict = orch.get('strict', False)
        enabled = orch.get('enabled', True)
        print('true' if strict and enabled else 'false')
except Exception:
    print('false')
" "$CONFIG_FILE" "$AGENT_META_PROVIDER" 2>/dev/null)

  if [ "$STRICT" = "true" ]; then
    echo "ORCHESTRATOR_GUARD: STRICT MODE is active. Direct $TOOL_NAME calls in the main chat are blocked." >&2
    echo "Delegate this task to the orchestrator agent." >&2
    exit 2
  fi
fi

# Non-strict mode: still block direct git mutations in Bash calls
if [ "$TOOL_NAME" = "Bash" ]; then
  IS_MUTATION=$(printf '%s' "$BASH_CMD" | $_PY -c "
import re, shlex, sys

command = sys.stdin.read()

MUTATING = {
    'commit', 'push', 'add', 'rm', 'merge', 'rebase', 'reset', 'restore',
    'tag',
}
STASH_MUTATING = {'pop', 'drop', 'clear'}

def statements(cmd):
    # Best-effort split on shell control operators. Not a full shell
    # parser, but enough to stop scanning past '&&'/';'/'|' boundaries so a
    # mutation keyword in an unrelated later command or a quoted argument
    # doesn't get attributed to an earlier, unrelated 'git' invocation.
    # Newline is also a statement boundary (issue #508): without it, a
    # multi-line command with no operator between the lines stayed one
    # statement string, and shlex.split() then flattened both lines into a
    # single token stream -- the second line's tokens could get misread as
    # positional args to the first line's git subcommand (e.g. 'git branch'
    # followed on the next line by 'git status --short' looked like
    # 'git branch git status --short', a branch-create mutation).
    return re.split(r'&&|\|\||;|\||\n', command)

def tokens_of(stmt):
    try:
        return shlex.split(stmt)
    except ValueError:
        return stmt.split()

blocked = False
for stmt in statements(command):
    toks = tokens_of(stmt)
    for i, tok in enumerate(toks):
        if tok != 'git' and not tok.endswith('/git'):
            continue
        rest = toks[i + 1:]
        j = 0
        while j < len(rest) and rest[j].startswith('-'):
            j += 1
        if j >= len(rest):
            break
        subcmd = rest[j]
        args = rest[j + 1:]
        if subcmd == 'branch':
            positional = [a for a in args if not a.startswith('-')]
            mutating_flags = {'-d', '-D', '-m', '-M', '--delete', '--move', '--copy', '-c', '-C'}
            if positional or (set(args) & mutating_flags):
                blocked = True
        elif subcmd == 'checkout':
            if args and not all(a.startswith('-') for a in args):
                blocked = True
        elif subcmd == 'stash':
            if args and args[0] in STASH_MUTATING:
                blocked = True
        elif subcmd in MUTATING:
            blocked = True
        break
    if blocked:
        break

print('true' if blocked else 'false')
" 2>/dev/null || echo "false")

  if [ "$IS_MUTATION" = "true" ]; then
    echo "ORCHESTRATOR_GUARD: Direct git mutations are forbidden in the main chat." >&2
    echo "Detected command: $(echo "$BASH_CMD" | head -c 200)" >&2
    echo "Delegate git operations to the \`git\` agent." >&2
    exit 2
  fi
fi

exit 0
