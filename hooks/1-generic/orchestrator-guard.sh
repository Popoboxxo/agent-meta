#!/bin/bash
# hook: orchestrator-guard
# version: 2.6.0
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
#
# Hardening (issue #516): a real-world incident showed a non-git worker
# self-declaring as `git` via this sentinel to run destructive stash
# operations. Elevation is therefore capability-scoped and audited:
#   * `orchestrator` sentinel exempts ONLY from strict-mode main-chat
#     blocking (Bash) — it NEVER bypasses the git-mutation block.
#   * `git` sentinel exempts ONLY from the git-mutation block.
#   * Destructive operations (force push, reset --hard, clean -f, stash
#     drop/clear, filter-branch/filter-repo, working-tree wipe) are
#     blocked EVEN with a valid `git` sentinel and require the user to
#     approve/run them manually.
#   * Every elevation attempt is appended to .claude/hooks/.guard-audit.log
#     for post-hoc review.
# Identity itself remains unverifiable at hook level (provider payload has
# no agent field) — this is mitigation, not cryptographic trust; see
# .claude/rules/a2a-delegation-gates.md ("Bekannte Grenzen").
#
# Destructive-gate scope note (issues #542/#551/#590/#591/#602): the
# destructive gate now shares ONE tokenizer with the mutation gate (the
# `parse_git` / `is_destructive` / `is_mutation` functions in the Python
# heredoc below) instead of matching raw regexes against the whole command
# string. It only inspects tokens of
# real `git <subcommand>` invocations, which closes several prior gaps:
#   * #602: destructive keywords inside an unrelated command's quoted text
#     argument (e.g. `gh issue create --body "git push --force ..."`,
#     `echo "reset --hard"`) no longer match — they are not `git` tokens.
#   * #590: a leading `+` on a push refspec (`git push origin +main`) forces
#     a non-fast-forward push like --force and is now detected, while a plain
#     `HEAD:main` refspec (no `+`) is not treated as destructive.
#   * #591: global `-c key=val` / `--config key=val` options are consumed
#     together with their value token, so the real subcommand is still found
#     (previously `-c core.pager=x push` hid `push`); additionally
#     `core.pager` / `core.editor` config keys are flagged as inherently
#     destructive (arbitrary-command execution / RCE) regardless of the
#     subcommand.
# Known limitation (issue #592, deliberate — best-effort convention gate,
# not a security boundary): command substitution and indirection such as
# `$(...)`, backticks, `xargs`, or `eval` can still smuggle a git mutation
# past the tokenizer, because the hook does not execute or fully parse the
# shell. Closing this would require a real shell interpreter, which is
# disproportionate for a convention tool; documented in
# .claude/rules/branch-guard.md ("Bekannte Grenzen").

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
fi

# Determine project root (needed by the audit log and config lookup)
PROJECT_ROOT=$(echo "$INPUT" | $_PY -c "import json,sys; print(json.load(sys.stdin).get('cwd',''))" 2>/dev/null || echo "")
if [ -z "$PROJECT_ROOT" ]; then
  PROJECT_ROOT="$PWD"
fi

# --- Sentinel elevation: capability-scoped + audited (issue #516) ------
IS_GIT_SENTINEL=0
IS_ORCH_SENTINEL=0

if [ "$TOOL_NAME" = "Bash" ] && [ -n "$DECLARED_AGENT" ]; then
  _ROLE=$(echo "$DECLARED_AGENT" | tr '[:upper:]' '[:lower:]')
  case "$_ROLE" in
    git|orchestrator)
      _AUDIT_LOG="$PROJECT_ROOT/.claude/hooks/.guard-audit.log"
      mkdir -p "$(dirname "$_AUDIT_LOG")" 2>/dev/null || true
      printf '%s role=%s cmd=%s\n' \
        "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$_ROLE" \
        "$(printf '%s' "$BASH_CMD" | tr '\n\t' '  ' | head -c 200)" \
        >> "$_AUDIT_LOG" 2>/dev/null || true
      if [ "$_ROLE" = "git" ]; then
        IS_GIT_SENTINEL=1
      else
        IS_ORCH_SENTINEL=1
      fi
      ;;
  esac
fi

# --- Unified git-statement scan (issue #551): ONE tokenizer feeds BOTH ---
# gates. The destructive gate (below) applies regardless of sentinel; the
# mutation gate (further down) applies only in non-strict mode for non-git
# callers. Classifying once, with the same tokenizer, keeps the two gates
# consistent and fixes the raw-regex gaps #590/#591/#602 (see header note).
# The scan prints exactly one word: 'destructive', 'mutation', or 'none'
# ('destructive' takes precedence when a statement is both). On any Python
# error it falls back to 'none' (fail-open, matching the prior gates).
_GIT_SCAN="none"
if [ "$TOOL_NAME" = "Bash" ]; then
  _GIT_SCAN=$(printf '%s' "$BASH_CMD" | $_PY -c "
import re, shlex, sys

command = sys.stdin.read()

MUTATING = {
    'commit', 'push', 'add', 'rm', 'merge', 'rebase', 'reset', 'restore',
    'tag',
}
STASH_MUTATING = {'pop', 'drop', 'clear'}

# Global git options (before the subcommand) that consume a following value
# token; if not skipped WITH their value, the value is misread as the
# subcommand (issue #591, e.g. 'git -C path push' would see 'path').
GLOBAL_OPTS_WITH_VALUE = {
    '-C', '--git-dir', '--work-tree', '--namespace', '--exec-path',
    '--super-prefix',
    # Same subcommand-hiding class as '-c' (issue #551): both take a separate
    # value token in space-form and would otherwise mask the real subcommand
    # (e.g. 'git --config-env x=Y push --force' / 'git --attr-source t push
    # --force' hid 'push').
    '--config-env', '--attr-source',
}
# Config keys whose value git hands to the shell -> arbitrary command
# execution / RCE (issue #591). Flagged destructive regardless of the
# subcommand, so 'git -c core.pager=<cmd> status' is still blocked. Keys are
# compared case-insensitively (git config section/name are case-insensitive),
# so every entry here must be lowercase. 'alias.*' is handled by prefix below.
RCE_CONFIG_KEYS = {
    'core.pager', 'core.editor', 'core.sshcommand', 'core.fsmonitor',
    'core.hookspath', 'sequence.editor', 'credential.helper',
}


def statements(cmd):
    # Best-effort split on shell control operators AND newlines (issue #508):
    # stops scanning past '&&'/';'/'|'/newline so a mutation keyword in an
    # unrelated later command or a quoted argument is not attributed to an
    # earlier 'git' invocation, and multi-line commands are not flattened.
    return re.split(r'&&|\|\||;|\||\n', cmd)


def tokens_of(stmt):
    try:
        return shlex.split(stmt)
    except ValueError:
        return stmt.split()


def parse_git(rest):
    # Consume leading global options (including '-c key=val' with its value,
    # issue #591) and return (subcmd or None, args, config_keys). config_keys
    # collects the KEY part of every -c/--config pair for RCE inspection.
    config_keys = []
    j, n = 0, len(rest)
    while j < n:
        t = rest[j]
        if t in ('-c', '--config'):
            if j + 1 < n:
                config_keys.append(rest[j + 1].split('=', 1)[0])
                j += 2
            else:
                j += 1
            continue
        if t.startswith('--config='):
            config_keys.append(t[len('--config='):].split('=', 1)[0])
            j += 1
            continue
        # '--config-env <name>=<envvar>' (git >=2.31): the KEY is the <name>
        # part, same RCE surface as '-c' (issue #551). Consume its value token
        # and record the key for RCE inspection.
        if t == '--config-env':
            if j + 1 < n:
                config_keys.append(rest[j + 1].split('=', 1)[0])
                j += 2
            else:
                j += 1
            continue
        if t.startswith('--config-env='):
            config_keys.append(t[len('--config-env='):].split('=', 1)[0])
            j += 1
            continue
        if t in GLOBAL_OPTS_WITH_VALUE:
            j += 2
            continue
        if t.startswith('-'):
            j += 1
            continue
        break
    if j >= n:
        return None, [], config_keys
    return rest[j], rest[j + 1:], config_keys


def has_short_flag(args, ch):
    # True if any short-flag cluster (single dash, not '--') contains 'ch',
    # e.g. has_short_flag(['-fu'], 'f') -> True. Shared by the push and clean
    # branches of is_destructive (issue #551, dedup of the old inline check).
    return any(
        a.startswith('-') and not a.startswith('--') and ch in a
        for a in args
    )


def is_destructive(subcmd, args, config_keys):
    # RCE via config applies regardless of the subcommand (issue #591). Keys
    # are matched case-insensitively; 'alias.<name>=<cmd>' is an RCE vector too
    # (git runs the alias body via the shell), matched by prefix.
    for k in config_keys:
        kl = k.lower()
        if kl in RCE_CONFIG_KEYS or kl.startswith('alias.'):
            return True
    if subcmd is None:
        return False
    positionals = [a for a in args if not a.startswith('-')]
    if subcmd == 'push':
        for a in args:
            if a in ('-f', '--force') or a.startswith('--force-with-lease'):
                return True
        # short-flag cluster containing 'f' (e.g. -fu)
        if has_short_flag(args, 'f'):
            return True
        # '--mirror' / '--delete' / '-d' delete remote refs -> irreversible
        # ref loss, blocked even with a git sentinel (issue #551, cf. #590).
        if '--mirror' in args or '--delete' in args:
            return True
        if has_short_flag(args, 'd'):
            return True
        # leading '+' on a refspec forces a non-fast-forward push (issue #590);
        # a plain 'HEAD:main' (no '+') is a normal fast-forward push.
        return any(p.startswith('+') for p in positionals)
    if subcmd == 'reset':
        return '--hard' in args
    if subcmd == 'clean':
        if '--force' in args:
            return True
        return has_short_flag(args, 'f')
    if subcmd == 'stash':
        return bool(args) and args[0] in ('drop', 'clear')
    if subcmd in ('filter-branch', 'filter-repo'):
        return True
    if subcmd == 'checkout':
        if '--' in args:
            k = args.index('--')
            return '.' in args[k + 1:]
        return False
    if subcmd == 'restore':
        return '.' in positionals
    return False


def is_mutation(subcmd, args):
    if subcmd is None:
        return False
    if subcmd == 'branch':
        positional = [a for a in args if not a.startswith('-')]
        mutating_flags = {'-d', '-D', '-m', '-M', '--delete', '--move', '--copy', '-c', '-C'}
        return bool(positional) or bool(set(args) & mutating_flags)
    if subcmd == 'checkout':
        return bool(args) and not all(a.startswith('-') for a in args)
    if subcmd == 'stash':
        return bool(args) and args[0] in STASH_MUTATING
    return subcmd in MUTATING


destructive = False
mutation = False
for stmt in statements(command):
    toks = tokens_of(stmt)
    for i, tok in enumerate(toks):
        if tok != 'git' and not tok.endswith('/git'):
            continue
        subcmd, args, config_keys = parse_git(toks[i + 1:])
        if is_destructive(subcmd, args, config_keys):
            destructive = True
        if is_mutation(subcmd, args):
            mutation = True
        break
    if destructive:
        break

print('destructive' if destructive else ('mutation' if mutation else 'none'))
" 2>/dev/null || echo "none")
fi

# --- Destructive-operation gate: applies regardless of sentinel --------
if [ "$TOOL_NAME" = "Bash" ] && [ "$_GIT_SCAN" = "destructive" ]; then
  echo "ORCHESTRATOR_GUARD: destructive git operation requires explicit user approval (issue #516)." >&2
  echo "Detected command: $(echo "$BASH_CMD" | head -c 200)" >&2
  echo "Ask the user to approve and run this command manually." >&2
  exit 2
fi

# Check if strict mode is enabled in project.yaml
CONFIG_FILE="$PROJECT_ROOT/.meta-config/project.yaml"
# Baked in by sync.py's per-provider copy step (scripts/lib/hooks.py) —
# stays the literal placeholder text only if this file was never synced
# (e.g. run straight from hooks/1-generic/), which the lookup below
# treats as "no provider override applies".
AGENT_META_PROVIDER="{{AGENT_META_PROVIDER}}"

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
    # Orchestrator OR git sentinel exempts a Bash call from strict-mode
    # main-chat blocking — never Write/Edit, never the git-mutation gate.
    # Both are recognized delegates (see IS_GIT_SENTINEL/IS_ORCH_SENTINEL
    # assignment above); omitting the git sentinel here made every
    # `#agent-meta:agent=git`-declared Bash call in a strict-mode project
    # fail with exit 2 even though it is an authorized delegate identity —
    # tests/test_orchestrator_guard_hook.py::test_strict_mode_sentinel_exemption
    # already documented and asserted the git-exempt behavior; this hook
    # just never implemented it.
    if [ "$TOOL_NAME" = "Bash" ] && { [ "$IS_ORCH_SENTINEL" = "1" ] || [ "$IS_GIT_SENTINEL" = "1" ]; }; then
      exit 0
    fi
    echo "ORCHESTRATOR_GUARD: STRICT MODE is active. Direct $TOOL_NAME calls in the main chat are blocked." >&2
    echo "Delegate this task to the orchestrator agent." >&2
    exit 2
  fi
fi

# Non-strict mode: still block direct git mutations in Bash calls. Reuses
# the unified scan (issue #551) computed above — the destructive gate has
# already exited for 'destructive'; a 'mutation' result is a plain git
# mutation that a non-git caller must delegate to the `git` agent.
if [ "$TOOL_NAME" = "Bash" ] && [ "$_GIT_SCAN" = "mutation" ] && [ "$IS_GIT_SENTINEL" != "1" ]; then
  echo "ORCHESTRATOR_GUARD: Direct git mutations are forbidden in the main chat." >&2
  echo "Detected command: $(echo "$BASH_CMD" | head -c 200)" >&2
  echo "Delegate git operations to the \`git\` agent." >&2
  exit 2
fi

exit 0
