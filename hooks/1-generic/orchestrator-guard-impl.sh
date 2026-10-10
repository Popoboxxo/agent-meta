#!/bin/bash
# version: 1.7.0
# Real orchestrator-guard logic. NOT a standalone hook — invoked by
# orchestrator-guard.sh (thin self-health wrapper, issue #630), which pipes
# the PreToolUse JSON payload to this script's stdin after syntax-checking
# it. Do not register this file directly in settings.json (it has no
# `# hook:`/`# event:` header on purpose, so scripts/lib/hooks.py never
# registers it as its own hook entry).
# The `# version:` line above IS still read by check_stale_deployed_hooks()
# (scripts/lib/consistency/hook_drift.py, issue #630) so a project that
# doesn't re-sync after this file changes gets a drift warning — bump it
# whenever this file's logic changes, independent of the wrapper's version.

set -uo pipefail

# It self-checks whether orchestrator.strict mode is enabled in project.yaml.
# If strict mode is off, the hook exits 0 immediately and imposes no overhead.
# Fail direction (SR-B-10): an existing but unreadable/unparseable
# project.yaml (incl. PyYAML missing in the hook's interpreter) never
# silently disables strict mode — a stdlib line scan decides and resolves
# to STRICT=true on any strict indicator or doubt. Same safe-side default
# on unreadable config as repo-containment-impl.sh's F4.
# Project root (SR-B-11, v1.7.0): resolved via $CLAUDE_PROJECT_DIR or a
# walk-up to the nearest `.meta-config/` ancestor, so strict mode and the
# auto-commit allowlist still apply after a `cd` into a subdirectory.
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
# Identity note (see agent-meta issues #390, #683): Claude Code's PreToolUse
# payload now carries an `agent_id` common input field, harness-set (not
# self-reported), "present only when the hook fires inside a subagent call"
# (https://code.claude.com/docs/en/hooks.md) — this was NOT true when this
# hook was first written (issue #390), which is why the sentinel convention
# below exists at all. `agent_id` reliably distinguishes ANY dispatched
# subagent's tool call (Write/Edit/Bash alike) from a main-thread call,
# without needing a content-embedded marker — see AGENT_ID usage below and
# in the strict-mode block.
#
# The sentinel convention remains for a narrower purpose the harness field
# doesn't cover: identifying WHICH ROLE a Bash call belongs to (git vs.
# orchestrator vs. anything else), for the git-mutation/destructive gates
# below — `agent_id` says "this is some subagent", not "this is the git
# agent". Authorized delegates (git, orchestrator agent templates)
# self-declare by prefixing every Bash command with a sentinel comment
# line: `#agent-meta:agent=<name>`. This remains a soft, self-reported
# convention (matches the framework's existing A2A trust model, see
# .claude/rules/a2a-delegation-gates.md) — it is not a security boundary
# against a malicious agent, only a fix for the role-identification gap
# `agent_id` alone can't close.
#
# Hardening (issue #516): a real-world incident showed a non-git worker
# self-declaring as `git` via this sentinel to run destructive stash
# operations. Elevation is therefore capability-scoped and audited:
#   * `orchestrator` sentinel exempts ONLY from strict-mode main-chat
#     blocking (Bash) — it NEVER bypasses the git-mutation block.
#   * `git` sentinel exempts ONLY from the git-mutation block.
#   * Destructive operations (force push, remote-ref deleting push incl.
#     `:ref` refspecs and --prune, reset --hard, clean -f, stash drop/clear,
#     filter-branch/filter-repo, working-tree wipe incl. `checkout .`,
#     checkout/switch --force, update-ref -d, reflog expire/delete) are
#     blocked EVEN with a valid `git` sentinel and require the user to
#     approve/run them manually (ref-loss additions: SR-B-12, v1.7.0).
#   * Every elevation attempt is appended to .claude/hooks/.guard-audit.log
#     for post-hoc review.
# Identity itself remains unverifiable at hook level (provider payload has
# no agent field) — this is mitigation, not cryptographic trust; see
# .claude/rules/a2a-delegation-gates.md ("Bekannte Grenzen").
#
# Destructive-gate scope note (issues #542/#551/#590/#591/#602/#809): the
# destructive gate now shares ONE tokenizer with the mutation gate (the
# `parse_git` / `is_destructive` / `is_mutation` functions in the Python
# heredoc below) instead of matching raw regexes against the whole command
# string. The git classification inspects tokens of real
# `git <subcommand>` invocations; the same scan additionally covers the
# non-git canonical catastrophes (issue #809: recursive `rm` on a dangerous
# root such as `/`, `/etc` or HOME, and a recursive fork bomb). Together
# these close several prior gaps:
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
#   * #809: `rm -rf /`, `rm -rf /etc`, `rm -rf ~` / `rm -rf $HOME` and a
#     recursive `rm` on any top-level system root are destructive regardless
#     of sentinel; a recursive fork bomb (`:(){ :|:& };:`) is blocked too.
#     Benign in-repo deletions (`rm -rf .tmp/...`) stay allowed. Still a
#     best-effort token scan (no shell interpreter), same trade-off as the
#     git gates below.
# Known limitation (issue #592, deliberate — best-effort convention boundary,
# not a security boundary; see .claude/rules/branch-guard.md#guard-terminologie
# for the definition of both terms): command substitution and indirection
# such as `$(...)`, backticks, `xargs`, or `eval` can still smuggle a git
# mutation past the tokenizer, because the hook does not execute or fully
# parse the shell. Closing this would require a real shell interpreter, which
# is disproportionate for a convention tool; documented in
# .claude/rules/branch-guard.md ("Bekannte Grenzen").

INPUT=$(cat)

# --- Shared helper lib + fail-closed python check (issue #595) ---------
# For THIS check (dependency availability) the hook acts as a security
# boundary (blocks strict-mode/destructive/mutation git calls) — see
# .claude/rules/branch-guard.md#guard-terminologie for the convention-vs-
# security-boundary distinction — unlike the informational/automation hooks
# in this repo, it must NOT silently allow the action through just because a
# required dependency is missing. Both a missing lib/hook_common.sh (deployment bug)
# and a missing python3/python interpreter (PATH manipulation) now fail
# CLOSED (exit 2) instead of fail-open (exit 0).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! source "$SCRIPT_DIR/lib/hook_common.sh" 2>/dev/null; then
  echo "ORCHESTRATOR_GUARD: required helper $SCRIPT_DIR/lib/hook_common.sh is missing or unreadable." >&2
  echo "Failing closed (issue #595) — re-run sync.py to redeploy the hooks/lib/ directory." >&2
  exit 2
fi

if ! hook_have_python; then
  echo "ORCHESTRATOR_GUARD: no python/python3 interpreter found on PATH." >&2
  echo "Failing closed (issue #595) — this guard cannot evaluate strict-mode/destructive-op checks without one." >&2
  echo "Install python3 or restore PATH to unblock this guard." >&2
  exit 2
fi
_PY="$(hook_python_bin)"

TOOL_NAME=$(hook_json_get "$INPUT" "tool_name")

# If no tool name: startup or other events — allow through
if [ -z "$TOOL_NAME" ]; then
  exit 0
fi

# agent_id (issue #683): Claude Code's PreToolUse payload carries this
# common input field "only when the hook fires inside a subagent call" —
# "Use this to distinguish subagent hook calls from main-thread calls"
# (https://code.claude.com/docs/en/hooks.md, Common input fields). This
# supersedes the "no agent/subagent field" limitation this hook's own
# comments used to document (see git history) — that was true when this
# hook was written, not anymore. Empty = main-thread call.
AGENT_ID=$(hook_json_get "$INPUT" "agent_id")

# Only block mutating tools
case "$TOOL_NAME" in
  Write|Edit|Bash) ;;
  *) exit 0 ;;
esac

BASH_CMD=""
DECLARED_AGENT=""
if [ "$TOOL_NAME" = "Bash" ]; then
  BASH_CMD=$(hook_json_get "$INPUT" "tool_input.command")

  # Self-declared agent identity (see note above): the first non-blank line
  # of the command must be exactly '#agent-meta:agent=<name>'. Only
  # orchestrator and git are recognized delegates for this guard.
  # `head -n1` alone (pre-#503) grabbed a literal empty first line whenever
  # BASH_CMD started with a leading newline before the sentinel -- some
  # delegated agents construct their Bash invocation that way -- so the
  # sentinel was silently missed and the legitimate mutation got blocked.
  # Stripping leading whitespace/blank lines before taking "line 1" makes
  # detection tolerant of that construction.
  DECLARED_AGENT=$(printf '%s' "$BASH_CMD" | "$_PY" -c "
import re, sys
content = sys.stdin.read().lstrip()
line = content.split('\n', 1)[0].strip()
m = re.match(r'^#agent-meta:agent=([A-Za-z0-9_-]+)\$', line)
print(m.group(1) if m else '')
" 2>/dev/null || echo "")
fi

# Determine project root (needed by the audit log, allowlist and config
# lookup). SR-B-11: the payload cwd alone is not enough -- after the main
# thread `cd`s into a subdirectory, `.meta-config/project.yaml` was not
# found there and strict mode was silently off. Resolution order:
#   1. $CLAUDE_PROJECT_DIR (harness-set) if it is an existing directory
#      containing .meta-config/;
#   2. otherwise the nearest ancestor of the payload cwd (inclusive)
#      containing .meta-config/ (same walk-up as dod-push-check.sh);
#   3. otherwise the payload cwd itself (prior behaviour).
# PAYLOAD_CWD stays the base for cwd-relative arguments (commit -F <file>).
PAYLOAD_CWD=$(hook_json_get "$INPUT" "cwd")
if [ -z "$PAYLOAD_CWD" ]; then
  PAYLOAD_CWD="$PWD"
fi
PROJECT_ROOT=""
if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -d "$CLAUDE_PROJECT_DIR/.meta-config" ]; then
  PROJECT_ROOT="$CLAUDE_PROJECT_DIR"
else
  _DIR="$PAYLOAD_CWD"
  # Bounded walk: stops at '/' (or any fixed point of dirname, e.g. '.'
  # for a relative cwd) and after 64 levels at most -- cannot loop.
  for _ in {1..64}; do
    if [ -d "$_DIR/.meta-config" ]; then
      PROJECT_ROOT="$_DIR"
      break
    fi
    _PARENT=$(dirname -- "$_DIR")
    [ "$_PARENT" = "$_DIR" ] && break
    _DIR="$_PARENT"
  done
fi
if [ -z "$PROJECT_ROOT" ]; then
  PROJECT_ROOT="$PAYLOAD_CWD"
fi

# --- Sentinel elevation: capability-scoped + audited (issue #516) ------
IS_GIT_SENTINEL=0
IS_ORCH_SENTINEL=0
IS_ALLOWLIST_SENTINEL=0

if [ "$TOOL_NAME" = "Bash" ] && [ -n "$DECLARED_AGENT" ]; then
  _ROLE=$(printf '%s' "$DECLARED_AGENT" | tr '[:upper:]' '[:lower:]')
  _AUDIT_ROLE=""
  case "$_ROLE" in
    git) IS_GIT_SENTINEL=1; _AUDIT_ROLE="$_ROLE" ;;
    orchestrator) IS_ORCH_SENTINEL=1; _AUDIT_ROLE="$_ROLE" ;;
    *)
      # Issue #694: config-driven third sentinel category. Own flag
      # (IS_ALLOWLIST_SENTINEL), never IS_GIT_SENTINEL -- the git-mutation
      # gate exempts both, but only IS_GIT_SENTINEL is OR'd into the
      # strict-mode main-chat exemption below, and that condition is
      # deliberately left unchanged for the real `git` role. Reusing
      # IS_GIT_SENTINEL here would silently also grant the strict-mode
      # exemption to every allowlisted role. Scope: `git add` and a
      # non-amending `git commit` ONLY -- every other mutation (push, rm,
      # merge, rebase, reset, restore, tag, branch, checkout, switch, pull,
      # cherry-pick, revert, am, update-ref, worktree,
      # stash pop|drop|clear, `commit --amend`) stays
      # blocked and must go through the `git` role, enforced via the
      # scan's narrow/broad scope word at the mutation gate below. Never
      # the destructive gate, never the strict-mode main-chat exemption.
      # Granted to any role sync.py has already determined
      # is Edit/Write-capable AND that this project's auto_commit
      # config has enabled. The hook never re-derives role capability
      # itself -- it only trusts the pre-computed allowlist.
      _ALLOWLIST="$PROJECT_ROOT/.meta-config/auto-commit-allowlist.json"
      if [ -f "$_ALLOWLIST" ]; then
        _AC_MODE=$("$_PY" -c "
import json, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
    print(data.get('mode', 'off'))
except Exception:
    print('off')
" "$_ALLOWLIST" 2>/dev/null)
        # Only 'auto'/'custom' grant hook-level commit authority; 'suggest'
        # roles merely propose a commit message and must never gain the
        # sentinel even though they may now appear in eligible_roles (that
        # list reflects capability, not per-mode authority -- see
        # scripts/lib/auto_commit.py resolve_auto_commit_config()).
        if [ "$_AC_MODE" = "auto" ] || [ "$_AC_MODE" = "custom" ]; then
          _IS_ELIGIBLE=$("$_PY" -c "
import json, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
    print('1' if sys.argv[2] in data.get('eligible_roles', []) else '0')
except Exception:
    print('0')
" "$_ALLOWLIST" "$_ROLE" 2>/dev/null)
          if [ "$_IS_ELIGIBLE" = "1" ]; then
            IS_ALLOWLIST_SENTINEL=1
            _AUDIT_ROLE="$_ROLE"
          fi
        fi
      fi
      ;;
  esac
  if [ -n "$_AUDIT_ROLE" ]; then
    # hook_audit_log_append (hooks/1-generic/lib/hook_common.sh) redacts
    # credential-shaped substrings before writing (issue #596), hardens
    # the log file to 600 permissions on every write (issue #596), and
    # caps unbounded growth via truncate-oldest rotation (issue #597).
    _AUDIT_LOG="$PROJECT_ROOT/.claude/hooks/.guard-audit.log"
    _AUDIT_LINE=$(printf '%s role=%s cmd=%s' \
      "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$_AUDIT_ROLE" \
      "$(printf '%s' "$BASH_CMD" | tr '\n\t' '  ' | head -c 200)")
    hook_audit_log_append "$_AUDIT_LOG" "$_AUDIT_LINE"
  fi
fi

# --- Unified git-statement scan (issue #551): ONE tokenizer feeds BOTH ---
# gates. The destructive gate (below) applies regardless of sentinel; the
# mutation gate (further down) applies only in non-strict mode for non-git
# callers. Classifying once, with the same tokenizer, keeps the two gates
# consistent and fixes the raw-regex gaps #590/#591/#602 (see header note).
# The scan prints exactly three words: '<category> <scope> <bom>', where
# category is 'destructive', 'mutation' or 'none' ('destructive' takes
# precedence when a statement is both), scope is 'broad' or 'narrow', and
# bom is 'message' | 'file' | 'none' (issue #842: a leading UTF-8 BOM in a
# commit message; the detector also covers ANSI-C quoting -- -m $'\uFEFF...' --
# and combined short-option clusters/glued forms like -am/-mMSG). Scope only
# qualifies a
# 'mutation': 'narrow' means every git mutation found is `add` or a
# non-amending `commit`, 'broad' means at least one other mutation is present
# (push/rm/merge/rebase/reset/restore/tag/branch/checkout/stash, since
# SR-B-13 also pull/switch/cherry-pick/revert/am/update-ref/worktree, or
# `commit --amend`, which rewrites history). The allowlist sentinel
# (issue #694) may only pass 'narrow'. On any Python error it falls back to
# 'none narrow none' (fail-open, matching the prior gates).
_GIT_SCAN="none"
_GIT_SCAN_SCOPE="narrow"
_GIT_BOM="none"
if [ "$TOOL_NAME" = "Bash" ]; then
  _GIT_SCAN_RAW=$(printf '%s' "$BASH_CMD" | "$_PY" -c "
import os, re, shlex, sys

command = sys.stdin.read()
root = sys.argv[1] if len(sys.argv) > 1 else '.'

MUTATING = {
    'commit', 'push', 'add', 'rm', 'merge', 'rebase', 'reset', 'restore',
    'tag',
    # SR-B-13: history/ref/working-tree changing subcommands that used to
    # slip through ('switch' is checkout's modern alias).
    'pull', 'switch', 'cherry-pick', 'revert', 'am', 'update-ref',
}
STASH_MUTATING = {'pop', 'drop', 'clear'}
# Options of 'git stash' (push form) that consume a value token, so the
# value is not misread as the stash subcommand ('git stash -m drop').
STASH_OPTS_WITH_VALUE = {'-m', '--message', '--pathspec-from-file'}
# 'git reflog' subcommands that delete reflog entries (SR-B-12/13); plain
# 'git reflog' / 'git reflog show' are read-only.
REFLOG_DESTRUCTIVE = {'expire', 'delete'}

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
    # Best-effort split on shell control operators AND newlines (issue #508,
    # #694-followup): stops scanning past '&&'/'||'/';'/'|'/'&'/newline so a
    # mutation keyword in an unrelated later command or a quoted argument is
    # not attributed to an earlier 'git' invocation, and multi-line commands
    # are not flattened. Bare '&' (background-job separator) must split too --
    # 'git add x & git push' is two independent statements, not one; without
    # it the per-statement 'break' below stops at the first 'git' and the
    # second invocation is never classified (allowlist-sentinel bypass).
    # '&&' is listed FIRST in the alternation so the longer operator matches
    # before the single-'&' branch would split it into two empty tokens.
    return re.split(r'&&|\|\||;|\||&|\n', cmd)


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


def first_word(args, opts_with_value=()):
    # First non-option token of a subcommand's args, i.e. its own
    # sub-subcommand (SR-B-12): options may precede it ('git stash -q drop'),
    # so 'args[0]' is not enough. Values of opts_with_value are skipped; a
    # '--' ends option parsing and everything after it is a pathspec.
    skip = False
    for a in args:
        if skip:
            skip = False
            continue
        if a == '--':
            return None
        if a in opts_with_value:
            skip = True
            continue
        if a.startswith('-'):
            continue
        return a
    return None


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
        # '--prune' deletes remote refs without a local counterpart (SR-B-12).
        if '--mirror' in args or '--delete' in args or '--prune' in args:
            return True
        if has_short_flag(args, 'd'):
            return True
        # Empty-source refspec ':dst' (also '+:dst') deletes the remote ref
        # dst (SR-B-12). A bare ':' is the 'matching' refspec, not a delete.
        if any(p.startswith(':') and len(p) > 1 for p in positionals):
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
        return first_word(args, STASH_OPTS_WITH_VALUE) in ('drop', 'clear')
    if subcmd in ('filter-branch', 'filter-repo'):
        return True
    if subcmd in ('checkout', 'switch'):
        # SR-B-12: '-f'/'--force' (and switch's '--discard-changes') throw
        # away local changes; checkout of the '.' pathspec wipes the working
        # tree with or without '--'. A single-path restore stays a mutation.
        k = args.index('--') if '--' in args else len(args)
        opts, paths = args[:k], args[k + 1:]
        if '--force' in opts or '--discard-changes' in opts:
            return True
        if has_short_flag(opts, 'f'):
            return True
        if subcmd == 'checkout':
            return '.' in paths or '.' in [a for a in opts if not a.startswith('-')]
        return False
    if subcmd == 'update-ref':
        return '-d' in args or '--delete' in args
    if subcmd == 'reflog':
        return first_word(args) in REFLOG_DESTRUCTIVE
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
        return first_word(args, STASH_OPTS_WITH_VALUE) in STASH_MUTATING
    if subcmd == 'reflog':
        return first_word(args) in REFLOG_DESTRUCTIVE
    if subcmd == 'worktree':
        # Every worktree subcommand except 'list' changes worktree state.
        w = first_word(args)
        return w is not None and w != 'list'
    return subcmd in MUTATING


# Issue #694: the allowlist sentinel authorizes staging+committing only, so
# the scan reports whether every mutation found stays inside that set.
ADDCOMMIT_ONLY = {'add', 'commit'}


def is_addcommit_scope(subcmd, args):
    if subcmd not in ADDCOMMIT_ONLY:
        return False
    # 'commit --amend' REWRITES the previous commit rather than creating a
    # new one -- it can silently destroy work an earlier commit (possibly
    # the git role's) already recorded. Not part of the add/commit
    # authority granted to auto-committing roles.
    if subcmd == 'commit' and '--amend' in args:
        return False
    return True

def ansi_c_decode(s):
    # Decode a shell ANSI-C (dollar-single-quote) quoted value. shlex strips
    # the surrounding single quotes, so the token arrives as a leading dollar
    # sign followed by the raw escape text (backslash-u-F-E-F-F then the
    # message, or backslash-x-E-F...). bytes(...).decode('unicode_escape')
    # turns the backslash escapes into real characters. This source lives
    # inside a double-quoted -c string, so it deliberately stays free of shell
    # metacharacters (no dollar sign, backtick or brace expansion).
    try:
        return s.encode('latin-1', 'backslashreplace').decode('unicode_escape')
    except Exception:
        return s


DOLLAR = chr(36)


def message_starts_with_bom(msg):
    # A leading UTF-8 BOM decodes to U+FEFF at the very start of the string
    # (issue #842). Only the START matters -- a BOM used as a zero-width
    # space inside the subject/body must not false-positive.
    if not msg:
        return False
    if msg[0] == '\ufeff':
        return True
    # ANSI-C quoting bypass (issue #842, G1): an ANSI-C quoted message with a
    # leading BOM reaches the hook as a leading dollar sign then the escape
    # text, because shlex strips the quotes. A NORMAL message starting with a
    # literal dollar sign must still pass, so only treat the leading dollar
    # sign as ANSI-C when the shell would: the next character must be a
    # backslash (an escape). A plain dollar amount has no backslash -> allowed.
    if msg[0] == DOLLAR and len(msg) > 1 and msg[1] == '\\\\':
        decoded = ansi_c_decode(msg[1:])
        if decoded[:1] == '\ufeff' or decoded[:3] == '\xef\xbb\xbf':
            return True
    return False


def file_starts_with_bom(path):
    # Read the first three bytes and compare to the raw UTF-8 BOM. A BOM
    # embedded anywhere later in the file is irrelevant (only the subject at
    # byte 0 matters). Missing/unreadable file -> no signal (allow; git
    # itself will report the missing file).
    if not os.path.isabs(path):
        path = os.path.join(root, path)
    try:
        with open(path, 'rb') as f:
            return f.read(3) == b'\xef\xbb\xbf'
    except OSError:
        return False


def short_cluster_value(args, tok):
    # G2 (issue #842): a short-option cluster like '-am' or '-aF' may end in a
    # value-taking short option. git's own grammar: 'm' takes a message (next
    # token when it is the cluster's last char), 'F' takes a file. If the value
    # is glued to the cluster ('-amMSG' / '-aFfile'), the remainder is the
    # value. Return (kind, value) or (None, None) when the cluster holds no
    # m/F. Only single-dash clusters (not '--long') are considered.
    if not tok.startswith('-') or tok.startswith('--') or tok == '-':
        return None, None
    body = tok[1:]
    for pos, ch in enumerate(body):
        if ch == 'm':
            rest = body[pos + 1:]
            if rest:
                return 'message', rest
            if len(args) > 1:
                return 'message', args[1]
            return None, None
        if ch == 'F':
            rest = body[pos + 1:]
            if rest:
                return 'file', rest
            if len(args) > 1:
                return 'file', args[1]
            return None, None
    return None, None


def commit_message_bom(args):
    # 'message' when a -m/--message value starts with a BOM, 'file' when a
    # -F/--file file whose first three bytes are the UTF-8 BOM, else 'none'.
    # Recognized spellings: '-m VALUE', '--message VALUE', '--message=VALUE',
    # '-mGLUED', and short-option clusters containing m/F ('-am VALUE',
    # '-aFfile VALUE' -- the value is the next token only when m/F is the
    # cluster's last character, matching git's short-option grammar; anything
    # glued after m/F is that option's value). -m/-F may repeat; any
    # BOM-bearing source counts.
    for idx, tok in enumerate(args):
        value = None
        kind = None
        for flag, fkind in (('-m', 'message'), ('--message', 'message'),
                            ('-F', 'file'), ('--file', 'file')):
            if tok == flag:
                if idx + 1 < len(args):
                    value, kind = args[idx + 1], fkind
                break
            if tok.startswith(flag + '='):
                value, kind = tok[len(flag) + 1:], fkind
                break
        if value is None and (tok.startswith('-') and not tok.startswith('--')):
            kind, value = short_cluster_value(args[idx:], tok)
        if value is None:
            continue
        if kind == 'message':
            if message_starts_with_bom(value):
                return 'message'
        elif file_starts_with_bom(value):
            return 'file'
    return 'none'


# --- issue #809: non-git filesystem destruction + fork bomb -------------
# The git classifier above only inspects 'git <subcommand>' invocations.
# The destructive gate must also cover the canonical shell-level
# catastrophes: recursive removal of a dangerous filesystem root and a
# recursive fork bomb. Same best-effort token scan / convention-boundary
# trade-off as the git gates (issue #592) -- no shell interpreter, and the
# command is never executed.
FS_WRAPPERS = {
    'sudo', 'doas', 'env', 'command', 'nohup', 'time', 'nice', 'ionice',
    'stdbuf',
}
# Top-level roots whose recursive removal is treated as destructive.
# '/tmp' is deliberately absent: build/CI scratch under /tmp is routine.
DANGEROUS_ROOTS = {
    '/', '/etc', '/usr', '/var', '/bin', '/sbin', '/lib', '/lib64',
    '/boot', '/dev', '/proc', '/sys', '/opt', '/root', '/home', '/srv',
    '/mnt', '/media', '/run',
}
# Known scratch subtrees that stay allowed even though their first component
# is a system root (e.g. '/var'): routine build/CI cleanup lives here.
SCRATCH_SUBPATHS = ('/tmp/', '/var/tmp/', '/private/tmp/', '/var/folders/')
DQUOTE = chr(34)
SQUOTE = chr(39)


def strip_quoted(command):
    # Remove single/double-quoted spans so a fork-bomb-looking STRING
    # literal (e.g. an echo argument) is not misclassified -- the same
    # token-level scoping the git gates apply (issue #602). Best-effort:
    # escaped quotes are not tracked (no shell parser).
    out = []
    quote = None
    for c in command:
        if quote is not None:
            if c == quote:
                quote = None
            continue
        if c == DQUOTE or c == SQUOTE:
            quote = c
            continue
        out.append(c)
    return ''.join(out)


def is_recursive_rm(args):
    for a in args:
        if a == '--recursive':
            return True
        if a.startswith('-') and not a.startswith('--') and a != '-':
            if 'r' in a[1:] or 'R' in a[1:]:
                return True
    return False


def normalize_rm_target(target):
    # Drop a trailing glob and trailing slashes so '/etc/*' and '/etc/'
    # both normalize to '/etc' (bare '/' stays '/').
    t = target.strip()
    if t.endswith('*'):
        t = t[:-1]
    if t.endswith('/') and t != '/':
        t = t.rstrip('/')
    return t


def is_dangerous_rm_target(target):
    raw = target.strip()
    # Bare current/parent dir or unqualified glob wipes the working tree.
    # Checked on the RAW token; normalize_rm_target turns '*' into ''.
    if raw in ('.', '..', '*'):
        return True
    # Known scratch subtrees stay allowed; '..' is excluded so a traversal
    # like '/var/tmp/../etc' is not laundered into the exception.
    if raw.startswith(SCRATCH_SUBPATHS) and '..' not in raw:
        return False
    t = normalize_rm_target(target)
    if not t:
        return False
    if t in ('.', '..'):
        return True
    home = DOLLAR + 'HOME'
    home_braced = DOLLAR + '{HOME}'
    # HOME itself (or a glob directly under it), not a normal subdirectory.
    if t in ('~', home, home_braced):
        return True
    # Absolute path: danger is the top-level component, minus scratch.
    if t.startswith('/'):
        if t.startswith(SCRATCH_SUBPATHS):
            return False
        first = '/' + t.lstrip('/').split('/', 1)[0]
        return first in DANGEROUS_ROOTS
    return False


def is_fs_destructive(toks):
    # Locate the command word, skipping wrapper prefixes and KEY=VALUE
    # assignments (mirrors the containment classifier's approach).
    idx, n = 0, len(toks)
    while idx < n:
        head = os.path.basename(toks[idx])
        if head in FS_WRAPPERS or re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', toks[idx]):
            idx += 1
            continue
        break
    if idx >= n:
        return False
    if os.path.basename(toks[idx]) != 'rm':
        return False
    args = toks[idx + 1:]
    if not is_recursive_rm(args):
        return False
    return any(
        is_dangerous_rm_target(a)
        for a in args
        if not (a.startswith('-') and a != '-')
    )


def is_fork_bomb(command):
    # Classic ':(){ :|:& };:' and named variants like 'bomb(){ bomb|bomb& }'
    # define a function whose body pipes the function into itself.
    for m in re.finditer(r'([A-Za-z_:][A-Za-z0-9_:]*)\s*\(\s*\)\s*\{([^}]*)\}',
                         command):
        name, body = m.group(1), m.group(2)
        if re.search(re.escape(name) + r'\s*\|\s*' + re.escape(name), body):
            return True
    return False


destructive = is_fork_bomb(strip_quoted(command))
mutation = False
mutation_scope_broad = False
bom = 'none'
for stmt in statements(command):
    if destructive:
        break
    toks = tokens_of(stmt)
    if is_fs_destructive(toks):
        destructive = True
        break
    for i, tok in enumerate(toks):
        if tok != 'git' and not tok.endswith('/git'):
            continue
        subcmd, args, config_keys = parse_git(toks[i + 1:])
        if is_destructive(subcmd, args, config_keys):
            destructive = True
        if is_mutation(subcmd, args):
            mutation = True
            if not is_addcommit_scope(subcmd, args):
                mutation_scope_broad = True
        if subcmd == 'commit' and bom == 'none':
            bom = commit_message_bom(args)
        break
    if destructive:
        break

category = 'destructive' if destructive else ('mutation' if mutation else 'none')
scope = 'broad' if mutation_scope_broad else 'narrow'
print(f'{category} {scope} {bom}')
" "$PAYLOAD_CWD" 2>/dev/null || echo "none narrow none")
  _GIT_SCAN=$(printf '%s' "$_GIT_SCAN_RAW" | awk '{print $1}')
  _GIT_SCAN_SCOPE=$(printf '%s' "$_GIT_SCAN_RAW" | awk '{print $2}')
  _GIT_BOM=$(printf '%s' "$_GIT_SCAN_RAW" | awk '{print $3}')
  [ -n "$_GIT_SCAN" ] || _GIT_SCAN="none"
  [ -n "$_GIT_SCAN_SCOPE" ] || _GIT_SCAN_SCOPE="narrow"
  [ -n "$_GIT_BOM" ] || _GIT_BOM="none"
  case "$_GIT_BOM" in
    message|file|none) ;;
    *) _GIT_BOM="none" ;;
  esac
fi

# --- Leading-BOM gate: applies regardless of sentinel (issue #842) -----
# A leading UTF-8 BOM (EF BB BF) in the commit subject breaks Conventional-
# Commit tooling and line-based hooks. The subject must start at byte 0 with
# the type. Placed BETWEEN the tokenizer and the strict-mode sentinel exit 0
# below on purpose, so neither a `git`/allowlist sentinel nor strict mode can
# bypass it. Reject (exit 2) rather than strip: the hook only sees the Bash
# command string, and rewriting it would be error-prone.
if [ "$TOOL_NAME" = "Bash" ] && [ "$_GIT_BOM" != "none" ]; then
  echo "ORCHESTRATOR_GUARD: commit message starts with a UTF-8 BOM (EF BB BF); the subject must start at byte 0 with the Conventional-Commit type (issue #842)." >&2
  echo "Detected BOM in commit $_GIT_BOM. Strip the BOM and retry." >&2
  exit 2
fi

# --- Destructive-operation gate: applies regardless of sentinel --------
if [ "$TOOL_NAME" = "Bash" ] && [ "$_GIT_SCAN" = "destructive" ]; then
  echo "ORCHESTRATOR_GUARD: destructive operation requires explicit user approval (issue #516)." >&2
  echo "Detected command: $(printf '%s' "$BASH_CMD" | head -c 200)" >&2
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
  #
  # Safe-side (SR-B-10, consistent with repo-containment's F4): if the
  # config exists but can't be parsed with PyYAML (ImportError — e.g. the
  # hook's interpreter is a different venv than sync.py's — or a YAML
  # syntax error), it is NOT treated as "strict off". A stdlib-only line
  # scan of the top-level `orchestrator:` block decides instead: any strict
  # indicator (`mode: strict`, `strict: <truthy>`, also under
  # provider-overrides) or anything the scan can't judge (flow style,
  # anchors/aliases, unreadable file) resolves to STRICT=true. Only a scan
  # that clearly finds no strict indicator returns false. The scan ignores
  # `enabled: false` — over-blocking is the accepted cost of fail-closed.
  STRICT=$("$_PY" -c "
import sys

CONFIG_FILE, PROVIDER = sys.argv[1], sys.argv[2]

def resolve_mode(orch, provider):
    override = orch.get('provider-overrides', {}).get(provider, {})
    mode = override.get('mode')
    if mode is not None:
        return mode
    return orch.get('mode')

FALSY = ('false', 'no', 'off', '0', '~', 'null', '')

def fallback_scan():
    # ponytail: line scan, not a YAML parser — anything it can't judge
    # resolves strict (fail closed); shared stdlib YAML reader is B-20.
    try:
        with open(CONFIG_FILE, encoding='utf-8-sig') as f:
            lines = f.read().splitlines()
    except Exception:
        return True
    in_block = False
    for raw in lines:
        if raw.lstrip().startswith('#') or not raw.strip():
            continue
        line = raw.split(' #', 1)[0].rstrip()
        stripped = line.lstrip()
        key, _, value = stripped.partition(':')
        key = key.strip().strip(chr(34) + chr(39))
        value = value.strip().strip(chr(34) + chr(39))
        if len(line) == len(stripped):  # top-level key
            in_block = key == 'orchestrator'
            if in_block and value:
                return True  # inline/flow/anchored value: ambiguous
            continue
        if not in_block:
            continue
        if key == '<<' or value[:1] in ('{', '[', '&', '*', '!'):
            return True  # merge key, flow style, anchor/alias, tag: ambiguous
        if key == 'mode' and value.lower() == 'strict':
            return True
        if key == 'strict' and value.lower() not in FALSY:
            return True
    return False

try:
    import yaml
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
except Exception as exc:
    strict = fallback_scan()
    verdict = ('strict indicator found or scan inconclusive, failing closed (STRICT=true)'
               if strict else 'no strict indicator found (STRICT=false)')
    sys.stderr.write(
        'ORCHESTRATOR_GUARD: warning: could not read project.yaml with PyYAML ('
        + type(exc).__name__ + '); conservative stdlib line scan: ' + verdict + '.\n'
    )
    print('true' if strict else 'false')
" "$CONFIG_FILE" "$AGENT_META_PROVIDER")
  # Any other outcome (interpreter crash, empty output) also fails closed.
  if [ "$STRICT" != "true" ] && [ "$STRICT" != "false" ]; then
    echo "ORCHESTRATOR_GUARD: warning: strict-mode check produced no result; failing closed (STRICT=true)." >&2
    STRICT=true
  fi

  # -z "$AGENT_ID": strict-mode main-chat blocking applies ONLY to the
  # main-thread (issue #683). A dispatched subagent's Write/Edit/Bash call
  # carries a non-empty agent_id (harness-set, see identity note above) and
  # skips this whole block — Write/Edit falls through allowed (they never
  # reach any gate below this one); Bash falls through to the git-mutation
  # gate just below, exactly like non-strict mode, so a subagent still
  # cannot mutate git without a valid `git` sentinel. Before this fix,
  # STRICT MODE blocked Write/Edit and non-sentineled Bash for EVERY
  # caller, including a properly orchestrator-dispatched implementer
  # subagent — making delegated implementation infeasible the moment strict
  # mode was enabled.
  if [ "$STRICT" = "true" ] && [ -z "$AGENT_ID" ]; then
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

# Still block direct git mutations in Bash calls — applies whenever the
# strict-mode main-chat block above didn't already exit (non-strict mode,
# OR strict mode with a dispatched subagent, issue #683). Reuses the
# unified scan (issue #551) computed above — the destructive gate has
# already exited for 'destructive'; a 'mutation' result is a plain git
# mutation that a non-git caller must delegate to the `git` agent.
# The allowlist sentinel (issue #694) only passes a 'narrow' mutation scope
# (add/commit); any broader mutation still requires the `git` role.
if [ "$TOOL_NAME" = "Bash" ] && [ "$_GIT_SCAN" = "mutation" ] && [ "$IS_GIT_SENTINEL" != "1" ] && { [ "$IS_ALLOWLIST_SENTINEL" != "1" ] || [ "$_GIT_SCAN_SCOPE" = "broad" ]; }; then
  echo "ORCHESTRATOR_GUARD: Direct git mutations are forbidden in the main chat." >&2
  echo "Detected command: $(printf '%s' "$BASH_CMD" | head -c 200)" >&2
  echo "Delegate git operations to the \`git\` agent." >&2
  exit 2
fi

exit 0
