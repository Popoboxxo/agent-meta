#!/bin/bash
# version: 1.9.2
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
# Payload/tool_name fail-closed (v1.8.0, review finding M2, #954 follow-up):
# an empty payload, a payload that is not valid JSON, a missing/non-string
# tool_name, an unrecognized tool_name and a python3/python that does not
# behave like an interpreter all block (exit 2). Previously each of those
# except a non-JSON payload fell into `*) exit 0` and silently ALLOWED the
# call — a broken PATH shim printing junk as tool_name was enough to disable
# this guard. The recognized-name list is shared with repo-containment-impl.sh
# (hook_known_tool_name in lib/hook_common.sh), so a new built-in tool must be
# added there; until then its calls block on purpose (fail-closed).
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
# Known gaps (issue #943 (m)) — this remains a best-effort token scan, NOT a
# shell parser (convention boundary; see
# .claude/rules/branch-guard.md#guard-terminologie for the definition of both
# terms). Everything below is deliberate and covered by the trade-off #592:
#   * command substitution / backticks and the interpreter indirections
#     `eval`, `bash -c`/`sh -c`, `env -S` and `xargs ... sh -c`: the payload
#     of these is a STRING, not a command list, so a git mutation hidden there
#     is not classified. This is structural for a token scanner (the hook
#     never executes anything) and is the #592 trade-off. The splitter does
#     not split operators INSIDE a substitution, so a surrounding command is
#     not misattributed either.
#   * a heredoc body is prose until proven otherwise: it is removed from the
#     command stream (#944 SR-B-16 / #943 (j)). `git update-ref --stdin`
#     delete lines ARE inspected, but any other destructive command fed
#     through stdin (e.g. `gc` reading a list) is invisible.
#   * shell aliases, a command stored in a variable (`g=git; $g push`) and an
#     unknown wrapper can rename or wrap git; only a real command word `git`
#     (after assignments, keywords, known wrappers, `--` and an inline
#     function body) is recognised.
#   * `gc` flags only `--prune=now` (and `gc.reflogExpire`/`gc.pruneExpire=now`
#     config); other expiry spellings are not enumerated.
#   * the commit-BOM gate only recognises the -m/--message and -F/--file
#     spellings (including short clusters and ANSI-C quoting) handled below.
#   * `case` arms and inline function bodies ARE classified: command_start()
#     skips `case WORD in PATTERN)` and `NAME() {` / `function NAME {`
#     prefixes, so `case x in x) git push --force;; esac` and
#     `f(){ git push --force; }; f` are seen. A `case` whose `in` and pattern
#     land on a later physical line (`case x` / newline / `in x) ...`) is
#     handled because `in` is a reserved word (F-NEW-2), and a pattern
#     terminator written as an extglob/bracket run (`@(a|b))`, `[)]`) is
#     skipped as a run of `)` characters. The splitter still cuts an
#     unquoted alternation `|` into separate statements, so a pattern
#     fragment becomes its own statement; that is at worst over-scanned (a
#     fragment literally named `git` has no subcommand and is not a
#     mutation). Every tested pattern shape (plain, `a|b`, extglob, quoted
#     and escaped `)`) reaches the command list after its terminator.
#   * a lone `--` at command position is transparent on every path: after a
#     wrapper's own options, after its positional prefix (DURATION/FILE/
#     ROOT) and directly before the command word (F-NEW-1: `timeout 5 --
#     git push --force` used to stop at the marker). Known command wrappers
#     (sudo/env/timeout/flock/setsid/watch/strace/chroot/busybox/...) are
#     unwrapped explicitly with their positional arity; an UNKNOWN wrapper
#     (`firejail`, `unshare`, `nsenter`, ...) is still a gap, kept narrow so
#     `man git pull` is not read as git.
# A scan failure (interpreter crash, malformed classifier output) fails CLOSED
# (exit 2), not open: the previous `|| echo "none narrow none"` fallback
# allowed the call whenever the classifier died (issue #943 (k), fail-closed
# rule).

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

# The shared helper functions this guard relies on must actually be there:
# a deployed lib/hook_common.sh from before they existed (sync.py not re-run
# after an agent-meta update) would otherwise make the calls below fail
# obscurely. Fail closed, same as a missing lib (issue #595).
if ! declare -F hook_json_usable >/dev/null 2>&1 \
   || ! declare -F hook_known_tool_name >/dev/null 2>&1 \
   || ! declare -F hook_shell_scan_py >/dev/null 2>&1 \
   || ! declare -F hook_is_meta_submodule_dir >/dev/null 2>&1; then
  echo "ORCHESTRATOR_GUARD: $SCRIPT_DIR/lib/hook_common.sh is outdated (shared guard helpers missing)." >&2
  echo "Failing closed — re-run sync.py to redeploy the hooks/lib/ directory." >&2
  exit 2
fi

# Issue #954 / review finding M2: a python3 on PATH that EXITS 0 while
# printing garbage (broken or hostile PATH shim) is indistinguishable from a
# working interpreter by exit status alone. Before this gate it handed junk
# back as tool_name, which matched the `*) exit 0` allow branch below -- a
# fail-open in BOTH security guards. Verify the interpreter before trusting
# any field (shared helper, not a second copy of the probe).
if ! hook_json_usable; then
  echo "ORCHESTRATOR_GUARD: the python/python3 on PATH does not behave like a Python interpreter." >&2
  echo "Failing closed (M2/#954) — the hook payload cannot be read reliably." >&2
  exit 2
fi

# Fail closed on an empty or non-JSON payload (SR-B-09, M2): the field
# readers below return "" for both, which used to read as "no tool name" and
# let the call through. A PreToolUse payload is always JSON; anything else
# means the guard cannot evaluate the call. Invalid UTF-8 bytes are
# tolerated (surrogateescape), as in hook_json_get -- only structurally
# broken JSON is rejected.
if [ -z "$INPUT" ]; then
  echo "ORCHESTRATOR_GUARD: empty PreToolUse payload (no JSON on stdin)." >&2
  echo "Failing closed (M2) — an unevaluable call must not be allowed." >&2
  exit 2
fi
if ! printf '%s' "$INPUT" | "$_PY" -c \
  'import sys, json; json.loads(sys.stdin.buffer.read().decode("utf-8", "surrogateescape"))' \
  2>/dev/null; then
  echo "ORCHESTRATOR_GUARD: hook payload is not valid JSON." >&2
  echo "Failing closed (SR-B-09) -- the guard cannot evaluate a call it cannot parse." >&2
  exit 2
fi

TOOL_NAME=$(hook_json_get "$INPUT" "tool_name")

# M2: a missing (or non-string/non-scalar, which hook_json_get reports as
# missing) tool_name is a payload the guard cannot classify. This used to
# allow the call "as a non-tool event"; a genuine PreToolUse payload always
# carries one, so the safe side is to block.
if [ -z "$TOOL_NAME" ]; then
  echo "ORCHESTRATOR_GUARD: no usable tool_name in the PreToolUse payload." >&2
  echo "Failing closed (M2) — a call the guard cannot identify must not be allowed." >&2
  exit 2
fi

# M2: an unrecognized tool_name used to fall through the `*) exit 0` branch
# below. The known-name allow-list lives in lib/hook_common.sh so both
# security guards share one definition (see hook_known_tool_name there for
# what is allowed and why).
if ! hook_known_tool_name "$TOOL_NAME"; then
  echo "ORCHESTRATOR_GUARD: unknown tool_name '$TOOL_NAME' in the hook payload." >&2
  echo "Failing closed (M2) — an unrecognized tool cannot be classified as safe." >&2
  echo "If it is a legitimate tool, add it to hook_known_tool_name in lib/hook_common.sh." >&2
  exit 2
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
# Bytes-in (surrogateescape), like hook_json_get: a lone surrogate / invalid
# UTF-8 byte in the command must not make this read crash and silently drop a
# legitimate sentinel (issue #943 (k)).
content = sys.stdin.buffer.read().decode('utf-8', 'surrogateescape').lstrip()
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
# Issue #943 (l): a nested agent-meta checkout (`.agent-meta/`, or
# `external/agent-meta/`) carries its own `.meta-config/`. On a non-Claude
# provider without $CLAUDE_PROJECT_DIR, the walk-up used to stop there and
# applied the SUBMODULE's strict mode / allowlist instead of the enclosing
# project's. Such a candidate is skipped while walking (but kept as a
# fallback, so a session opened only inside the submodule still resolves).
# PAYLOAD_CWD stays the base for cwd-relative arguments (commit -F <file>).
PAYLOAD_CWD=$(hook_json_get "$INPUT" "cwd")
if [ -z "$PAYLOAD_CWD" ]; then
  PAYLOAD_CWD="$PWD"
fi
PROJECT_ROOT=""
_SUBMODULE_ROOT=""
if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -d "$CLAUDE_PROJECT_DIR/.meta-config" ]; then
  PROJECT_ROOT="$CLAUDE_PROJECT_DIR"
else
  _DIR="$PAYLOAD_CWD"
  # Bounded walk: stops at '/' (or any fixed point of dirname, e.g. '.'
  # for a relative cwd) and after 64 levels at most -- cannot loop.
  for _ in {1..64}; do
    if [ -d "$_DIR/.meta-config" ]; then
      if hook_is_meta_submodule_dir "$_DIR"; then
        [ -n "$_SUBMODULE_ROOT" ] || _SUBMODULE_ROOT="$_DIR"
        # keep walking toward the enclosing project
      else
        PROJECT_ROOT="$_DIR"
        break
      fi
    fi
    _PARENT=$(dirname -- "$_DIR")
    [ "$_PARENT" = "$_DIR" ] && break
    _DIR="$_PARENT"
  done
  if [ -z "$PROJECT_ROOT" ] && [ -n "$_SUBMODULE_ROOT" ]; then
    PROJECT_ROOT="$_SUBMODULE_ROOT"
  fi
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
# (issue #694) may only pass 'narrow'.
#
# The classifier source is assembled from the shared lib
# (hook_shell_scan_py: quote/heredoc-aware statement splitter + fork-bomb
# detector) plus the git-specific part below. Any classifier failure -- a
# non-zero interpreter exit or output that is not exactly '<category> <scope>
# <bom>' -- fails CLOSED (exit 2). The old '|| echo none narrow none' fallback
# allowed every call whose classifier died (issue #943 (k)).
_GIT_SCAN="none"
_GIT_SCAN_SCOPE="narrow"
_GIT_BOM="none"
if [ "$TOOL_NAME" = "Bash" ]; then
  _GIT_SCAN_SRC=$(hook_shell_scan_py
cat <<'PYEOF'
import os, re, shlex, sys

# Bytes-in (surrogateescape): a lone-surrogate escape or invalid UTF-8 byte in
# the command must not make the classifier crash -- that crash used to hit the
# now-removed fail-open fallback (issue #943 (k)).
command = sys.stdin.buffer.read().decode('utf-8', 'surrogateescape')
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


def tokens_of(stmt):
    # Punctuation-aware so a grouping token does not glue to the command word
    # (issue #943 (b): shlex.split('(git push)') gave the token '(git', which
    # is never 'git'). Parentheses become their own tokens; the command-word
    # scan below skips them.
    try:
        lex = shlex.shlex(stmt, posix=True, punctuation_chars='()')
        lex.whitespace_split = True
        lex.commenters = ''
        return list(lex)
    except Exception:
        return stmt.split()


# Shell keywords / grouping tokens that may precede the real command word.
# `in` is a bash reserved word, never a command: it is the separator a `case`
# list carries when the splitter cuts `case WORD` and `in PATTERN)` onto
# different statements (review finding F-NEW-2). Without it the command word
# of the next statement was the literal `in`, so the arm's command list was
# never classified.
LEADING_KEYWORDS = {
    '!', '(', ')', '{', '}', 'if', 'then', 'else', 'elif', 'while', 'until',
    'do', 'done', 'fi', 'esac', 'in',
}
# Command wrappers whose option-before-command form must not hide the real
# command word (issue #943 (i): 'man git pull' must NOT be read as git, while
# 'sudo git push' and 'env X=1 git push' must still be). Maps a wrapper to
# (its short/long options that consume a value token, its count of leading
# non-option arguments before the wrapped command word). The second element is
# grammar, not guesswork: 'timeout DURATION cmd', 'flock FILE cmd' and
# 'chroot NEWROOT cmd' each own exactly one positional prefix (review finding
# F3 -- these used to hide the wrapped command word entirely).
WRAPPERS = {
    'sudo': ({'-u', '-g', '-p', '-C', '-T', '-r', '-t', '--user', '--group',
              '--prompt', '--chdir'}, 0),
    'doas': ({'-u', '-C'}, 0),
    'env': ({'-u', '--unset', '-C', '--chdir', '-S', '--split-string'}, 0),
    'command': (set(), 0),
    'builtin': (set(), 0),
    'nohup': (set(), 0),
    'exec': ({'-a'}, 0),
    'time': ({'-f', '-o', '--format', '--output'}, 0),
    'nice': ({'-n', '--adjustment'}, 0),
    'ionice': ({'-c', '-n', '-p', '-P', '-u', '--class', '--classdata',
                '--pid', '--pgid', '--uid'}, 0),
    'stdbuf': ({'-i', '-o', '-e', '--input', '--output', '--error'}, 0),
    'xargs': ({'-I', '-n', '-P', '-d', '-L', '-s', '-a', '-E', '-e'}, 0),
    'timeout': ({'-s', '--signal', '-k', '--kill-after'}, 1),
    'flock': ({'-w', '--timeout', '-E', '--conflict-exit-code'}, 1),
    # setsid has NO option that consumes a value (-c/-f/-w are all flags);
    # listing them as value-taking swallowed the wrapped command word
    # (`setsid --wait git push` was never classified).
    'setsid': (set(), 0),
    'watch': ({'-n', '--interval', '-q', '--equexit'}, 0),
    'strace': ({'-o', '--output', '-p', '--attach', '-e', '--trace',
                '-s', '--string-limit', '-u', '--user', '-a', '--columns',
                '-b', '-I', '-O', '-S', '-X', '-E', '-P'}, 0),
    'chroot': ({'-u', '--userspec', '-g', '--groups'}, 1),
    'busybox': (set(), 0),
}


def _empty_parens(toks, i):
    # shlex with punctuation_chars='()' returns ADJACENT punctuation as one
    # token, so 'f()' yields the pair '()' while '( git' yields '('. Return
    # how many tokens the empty pair occupies at i (0 = none).
    if i < len(toks) and toks[i] == '()':
        return 1
    if i + 1 < len(toks) and toks[i] == '(' and toks[i + 1] == ')':
        return 2
    return 0


def _close_paren_run(tok):
    # A case-pattern terminator. shlex with punctuation_chars='()' groups
    # ADJACENT punctuation into one token, so the ')' closing a pattern can
    # arrive as ')' or -- for an extglob pattern such as `@(a|b))` -- as
    # ')). Treat any token consisting only of closing parentheses as the
    # terminator (review finding F-NEW-2 follow-up: the exact-')' test let
    # the extglob arm hide its command list).
    return bool(tok) and tok.strip(')') == ''


def command_start(toks):
    # Index of the real command word in a statement, skipping keywords,
    # grouping tokens, KEY=VALUE assignments, `case` arm syntax, inline
    # function-definition prefixes and wrapper prefixes. Returns len(toks)
    # when the statement has no command word. This is what keeps a mere
    # ARGUMENT named git ('man git pull', 'echo git push') from being
    # classified as a git invocation (issue #943 (i)).
    i, n = 0, len(toks)
    while i < n:
        t = toks[i]
        base = os.path.basename(t)
        # A lone '--' at command position is an end-of-options marker, not a
        # command word. It can follow a wrapper's option parser, its
        # positional prefix (DURATION/FILE/ROOT) or appear directly before
        # the command word; in every case the wrapped command is what runs, so
        # skipping the marker is the transparent reading (review finding
        # F-NEW-1: `timeout 5 -- git push --force` used to stop here and was
        # never classified).
        if t == '--':
            i += 1
            continue
        if t in LEADING_KEYWORDS:
            i += 1
            continue
        # A bare run of grouping parentheses (shlex groups adjacent ones into
        # '((' / '))' / '()'). At command position it closes a subshell/case
        # arm, it is never the command word itself.
        if t and t.strip('()') == '':
            i += 1
            continue
        if re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', t):
            i += 1
            continue
        # `case WORD in PATTERN) COMMAND ;; esac`: the command list after the
        # pattern terminator is what runs (review finding F3).
        if t == 'case':
            i += 1
            if i < n:                      # the case subject word
                i += 1
            if i < n and toks[i] == 'in':
                i += 1
            while i < n and not _close_paren_run(toks[i]):
                i += 1
            if i < n:
                i += 1                     # the pattern's closing ')' run
            continue
        # The splitter cuts at ';;', so a later case arm arrives as its own
        # statement ('PATTERN) command'). A bare word directly followed by a
        # ')' run is never a command outside `case`; skip the pattern prefix.
        # The ')' run may be several characters wide for an extglob pattern
        # (`@(a|b))`), which is why this is not an exact-')' comparison.
        if i + 1 < n and _close_paren_run(toks[i + 1]):
            i += 2
            continue
        # Inline function definition: 'NAME() { COMMAND; }' (review finding
        # F3). The body's first command follows the '{'.
        parens = _empty_parens(toks, i + 1)
        if parens and re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', t):
            i += 1 + parens
            if i < n and toks[i] == '{':
                i += 1
            continue
        # 'function NAME { COMMAND; }' (optional empty parens).
        if t == 'function':
            i += 1
            if i < n:                      # the function name
                i += 1
            i += _empty_parens(toks, i)
            if i < n and toks[i] == '{':
                i += 1
            continue
        if base in WRAPPERS:
            value_opts, skip_args = WRAPPERS[base]
            i += 1
            while i < n:
                opt = toks[i]
                if opt == '--':
                    i += 1
                    break
                if opt.startswith('--'):
                    name = opt.split('=', 1)[0]
                    has_value = '=' in opt
                    i += 1
                    if not has_value and name in value_opts and i < n:
                        i += 1
                    continue
                if opt.startswith('-') and opt != '-':
                    i += 1
                    if opt in value_opts and i < n:
                        i += 1
                    continue
                break
            # Skip the wrapper's own positional prefix (DURATION, FILE, ROOT).
            while skip_args > 0 and i < n:
                i += 1
                skip_args -= 1
            continue
        break
    return i


def config_pair(raw):
    # A -c/--config value may be 'key' or 'key=value'. --config-env only names
    # the ENV VAR that holds the value, so its value is unknown at hook time;
    # represent that as None (conservative for the gc.* rules below).
    if '=' in raw:
        k, v = raw.split('=', 1)
        return (k, v)
    return (raw, None)


def parse_git(rest):
    # Consume leading global options (including '-c key=val' with its value,
    # issue #591) and return (subcmd or None, args, config_values).
    # config_values collects the (KEY, VALUE) of every -c/--config pair; the
    # VALUE is what distinguishes 'gc.reflogExpire=now' from '=never'.
    config_values = []
    j, n = 0, len(rest)
    while j < n:
        t = rest[j]
        if t in ('-c', '--config'):
            if j + 1 < n:
                config_values.append(config_pair(rest[j + 1]))
                j += 2
            else:
                j += 1
            continue
        if t.startswith('--config='):
            config_values.append(config_pair(t[len('--config='):]))
            j += 1
            continue
        # '--config-env <name>=<envvar>' (git >=2.31): the KEY is the <name>
        # part, same RCE surface as '-c' (issue #551). The VALUE lives in an
        # environment variable the hook cannot read, so record it as None
        # (unknown -> conservative for the gc.* rules).
        if t == '--config-env':
            if j + 1 < n:
                raw = rest[j + 1]
                config_values.append((raw.split('=', 1)[0], None))
                j += 2
            else:
                j += 1
            continue
        if t.startswith('--config-env='):
            raw = t[len('--config-env='):]
            config_values.append((raw.split('=', 1)[0], None))
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
        return None, [], config_values
    return rest[j], rest[j + 1:], config_values


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


def has_short_flag(args, ch, value_opts=()):
    # True if a short-option cluster (single dash, not '--') contains 'ch'
    # BEFORE any option that consumes the rest of the cluster as its value:
    # has_short_flag(['-fu'], 'f') -> True, has_short_flag(['-bfoo'], 'f',
    # ('b', 'B')) -> False because '-bfoo' is '-b foo' (issue #943 (i): the
    # old 'ch in a' test read the branch name 'foo' as the --force flag).
    # 'ch' wins over value_opts so '-f' itself and '-fu' still match.
    for a in args:
        if not (a.startswith('-') and not a.startswith('--') and a != '-'):
            continue
        for c in a[1:]:
            if c == ch:
                return True
            if c in value_opts:
                break
    return False


# git config keys that expire/delete unreachable objects or reflogs when set
# to 'now'. They are destructive-by-value (never by name alone) and are listed
# separately from RCE_CONFIG_KEYS, which are destructive by key (#943 (e)).
GC_EXPIRY_KEYS = {'gc.reflogexpire', 'gc.reflogexpiredrop', 'gc.pruneexpire'}

# Pathspecs that address the whole tree rather than one file (issue #943 (d)).
WHOLE_TREE_PATHSPECS = {'.', './', '*', ':/'}


def is_whole_tree_pathspec(p):
    return p in WHOLE_TREE_PATHSPECS or p.startswith(':/')


def is_destructive(subcmd, args, config_values, stdin_bodies=None):
    # RCE via config applies regardless of the subcommand (issue #591). Keys
    # are matched case-insensitively; 'alias.<name>=<cmd>' is an RCE vector too
    # (git runs the alias body via the shell), matched by prefix. A gc.*
    # expiry key is destructive when it expires/reaps immediately (#943 (e)).
    for k, v in config_values:
        kl = k.lower()
        if kl in RCE_CONFIG_KEYS or kl.startswith('alias.'):
            return True
        if kl in GC_EXPIRY_KEYS and (v is None or v.strip().lower() == 'now'):
            return True
    if subcmd is None:
        return False
    positionals = [a for a in args if not a.startswith('-')]
    if subcmd == 'push':
        for a in args:
            if a in ('-f', '--force') or a.startswith('--force-with-lease'):
                return True
        # short-flag cluster containing 'f' (e.g. -fu); '-o' takes the rest of
        # the cluster as a value, so '-oforce' is a push-option, not --force.
        if has_short_flag(args, 'f', {'o'}):
            return True
        # '--mirror' / '--delete' / '-d' delete remote refs -> irreversible
        # ref loss, blocked even with a git sentinel (issue #551, cf. #590).
        # '--prune' deletes remote refs without a local counterpart (SR-B-12).
        if '--mirror' in args or '--delete' in args or '--prune' in args:
            return True
        if has_short_flag(args, 'd', {'o'}):
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
    if subcmd == 'branch':
        # Issue #943 (h): '-f'/'--force' moves a branch to another tip and
        # '-D' deletes it even when unmerged -- both drop the old tip without
        # a reachable reflog promise. '-m'/'-M'/'-c'/'-C' take a value, so a
        # cluster like '-mold' must not be read as '-f'/'D' ('f'/'D' inside
        # the value). Plain '-d' stays a mutation.
        branch_value_opts = {'u', 'c', 'C', 'm', 'M'}
        if '--force' in args or has_short_flag(args, 'f', branch_value_opts):
            return True
        return has_short_flag(args, 'D', branch_value_opts)
    if subcmd in ('checkout', 'switch'):
        # SR-B-12: '-f'/'--force' (and switch's '--discard-changes') throw
        # away local changes; checkout of a whole-tree pathspec wipes the
        # working tree with or without '--'. A single-path restore stays a
        # mutation. Issue #943 (d): './', '*', ':/' and 'HEAD -- ./' are
        # whole-tree too; issue #943 (h): '-B'/'-C' (force-create) reset the
        # branch tip even when no pathspec is given.
        k = args.index('--') if '--' in args else len(args)
        opts, paths = args[:k], args[k + 1:]
        value_opts = {'b', 'B'} if subcmd == 'checkout' else {'c', 'C'}
        if '--force' in opts or '--discard-changes' in opts:
            return True
        if has_short_flag(opts, 'f', value_opts):
            return True
        create_ch = 'B' if subcmd == 'checkout' else 'C'
        if '--force-create' in opts or has_short_flag(opts, create_ch, value_opts):
            return True
        candidates = [a for a in opts if not a.startswith('-')] + paths
        return any(is_whole_tree_pathspec(a) for a in candidates)
    if subcmd == 'update-ref':
        if '-d' in args or '--delete' in args:
            return True
        if '--stdin' in args:
            # Issue #943 (f): 'update-ref --stdin' reads ref commands from
            # stdin. Only a heredoc body is visible to the hook; with no body
            # (a pipe) the input cannot be classified -> fail closed.
            if stdin_bodies is None:
                return True
            for body in stdin_bodies:
                for line in body.splitlines():
                    if re.match(r'^\s*delete(\s|' + chr(0) + r')', line):
                        return True
        return False
    if subcmd == 'reflog':
        return first_word(args) in REFLOG_DESTRUCTIVE
    if subcmd == 'restore':
        return any(is_whole_tree_pathspec(a) for a in positionals)
    if subcmd == 'gc':
        # Issue #943 (e): 'git gc --prune=now' deletes unreachable objects
        # immediately (the accompanying gc.reflogExpire=now is covered by
        # GC_EXPIRY_KEYS above).
        for idx, a in enumerate(args):
            if a == '--prune=now':
                return True
            if a == '--prune' and idx + 1 < len(args) and args[idx + 1] == 'now':
                return True
        return False
    if subcmd == 'worktree':
        # Issue #943 (g): 'worktree remove --force/-f' deletes a worktree
        # even with local modifications.
        w = first_word(args)
        if w == 'remove' and ('--force' in args or '-f' in args or has_short_flag(args, 'f')):
            return True
        return False
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
    if subcmd == 'am':
        # Issue #943 (i): '--show-current-patch' only prints the patch; it
        # neither applies nor aborts anything.
        return not any(a == '--show-current-patch' or a.startswith('--show-current-patch=')
                       for a in args)
    if subcmd in ('cherry-pick', 'revert'):
        # Issue #943 (i): '--abort'/'--quit' roll a stopped sequence back; they
        # do not rewrite history.
        return not any(a in ('--abort', '--quit') for a in args)
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
    if msg[0] == DOLLAR and len(msg) > 1 and msg[1] == '\\':
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
# command is never executed. wrapper prefixes (sudo/env/nice/...) are skipped
# by command_start(), shared with the git classifier.
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


def is_fs_destructive(cmd, args):
    if cmd != 'rm':
        return False
    if not is_recursive_rm(args):
        return False
    return any(
        is_dangerous_rm_target(a)
        for a in args
        if not (a.startswith('-') and a != '-')
    )


# Fork-bomb detection comes from the shared lib (hook_shell_scan_py):
# linear-time and quote-aware. It runs on the command with heredoc bodies and
# comments removed (a fork-bomb-shaped STRING in prose must not trip the
# gate, #602/#809/#943 (j)), but with operators intact -- ':(){ :|:& };:' is
# split into statements by those operators and would otherwise be invisible.
# The comment rule lives in the scanner itself (one implementation for the
# statement stream and this cleaned code, review finding F4): a trailing
# '# :(){ :|:& };:' is cut here exactly as it is in the statements.
_statement_stream, _scan_code = split_shell_statements_and_clean(command)
destructive = is_fork_bomb(strip_quoted(_scan_code))
mutation = False
mutation_scope_broad = False
bom = 'none'
# Quote/heredoc-aware statements from the shared lib (issue #943 (c)/(j),
# #944 SR-B-16). Heredoc bodies are attached to the statement that opened
# them; they are prose for command classification, except that
# `update-ref --stdin` delete lines are inspected.
for stmt, heredoc_bodies in _statement_stream:
    if destructive:
        break
    toks = tokens_of(stmt)
    idx = command_start(toks)
    if idx >= len(toks):
        continue
    cmd = os.path.basename(toks[idx])
    args = toks[idx + 1:]
    if is_fs_destructive(cmd, args):
        destructive = True
        break
    if cmd != 'git':
        continue
    subcmd, git_args, config_values = parse_git(args)
    # An empty heredoc list means the stdin was not visible (a pipe), which is
    # unclassifiable for update-ref --stdin -> fail closed there.
    if is_destructive(subcmd, git_args, config_values,
                      heredoc_bodies if heredoc_bodies else None):
        destructive = True
    if is_mutation(subcmd, git_args):
        mutation = True
        if not is_addcommit_scope(subcmd, git_args):
            mutation_scope_broad = True
    if subcmd == 'commit' and bom == 'none':
        bom = commit_message_bom(git_args)
    if destructive:
        break

category = 'destructive' if destructive else ('mutation' if mutation else 'none')
scope = 'broad' if mutation_scope_broad else 'narrow'
print(f'{category} {scope} {bom}')
PYEOF
)
  _GIT_SCAN_RC=0
  _GIT_SCAN_RAW=$(printf '%s' "$BASH_CMD" | "$_PY" -c "$_GIT_SCAN_SRC" "$PAYLOAD_CWD" 2>/dev/null) || _GIT_SCAN_RC=$?
  if [ "$_GIT_SCAN_RC" != "0" ]; then
    echo "ORCHESTRATOR_GUARD: the git/destructive classifier exited rc=$_GIT_SCAN_RC." >&2
    echo "Failing closed (issue #943 (k)) — an unevaluable command must not be allowed." >&2
    exit 2
  fi
  if [ "$(printf '%s' "$_GIT_SCAN_RAW" | awk 'NF{print NF}')" != "3" ]; then
    echo "ORCHESTRATOR_GUARD: the git/destructive classifier returned malformed output." >&2
    echo "Failing closed (issue #943 (k)) — an unevaluable command must not be allowed." >&2
    exit 2
  fi
  _GIT_SCAN=$(printf '%s' "$_GIT_SCAN_RAW" | awk '{print $1}')
  _GIT_SCAN_SCOPE=$(printf '%s' "$_GIT_SCAN_RAW" | awk '{print $2}')
  _GIT_BOM=$(printf '%s' "$_GIT_SCAN_RAW" | awk '{print $3}')
  case "$_GIT_SCAN" in
    destructive|mutation|none) ;;
    *)
      echo "ORCHESTRATOR_GUARD: the git/destructive classifier returned an unknown category '$_GIT_SCAN'." >&2
      echo "Failing closed (issue #943 (k))." >&2
      exit 2
      ;;
  esac
  case "$_GIT_SCAN_SCOPE" in
    broad|narrow) ;;
    *)
      echo "ORCHESTRATOR_GUARD: the git/destructive classifier returned an unknown scope '$_GIT_SCAN_SCOPE'." >&2
      echo "Failing closed (issue #943 (k))." >&2
      exit 2
      ;;
  esac
  case "$_GIT_BOM" in
    message|file|none) ;;
    *)
      echo "ORCHESTRATOR_GUARD: the git/destructive classifier returned an unknown BOM kind '$_GIT_BOM'." >&2
      echo "Failing closed (issue #943 (k))." >&2
      exit 2
      ;;
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
AGENT_META_PROVIDER="Gemini"

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
    orch = c.get('orchestrator', {})  # runtime-reader:orchestrator
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
