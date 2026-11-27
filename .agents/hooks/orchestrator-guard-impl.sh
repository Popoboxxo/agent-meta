#!/bin/bash
# version: 1.17.0
# changelog: 1.17.0: issue #1238b2 -- delegate sentinel, allowlist, strict/ask policy and git/destructive classification to deployed flat hook_guard_*.py modules; preserve exit codes and fail-closed dependency checks; 1.16.0: issue #1251 -- resolve the project root exclusively from adapter-owned AM_PROJECT_DIR; preserve the payload-cwd walk-up and submodule fallback; 1.15.0: issue #1335 -- the existing #1210 payload role attribution (`_ROLE_ATTRIBUTION`/`_P_AGENT_TYPE`) becomes the authoritative role source for allow matching (`EFFECTIVE_ROLE`); sentinel is only a mismatch/audit signal when the role field is reliable; empty harness role on a payload-attributed subagent call fails closed with exit 2 (no sentinel fallback/grant), while a non-empty UNKNOWN role gets no role flags — read-only ops still pass (rc 0), mutation ops exit 2 at the mutation gate (never grants); audit lines carry `attribution=`; hook-less providers keep the exact sentinel path. 1.14.1: issue #1217 (review fix) -- ask-class requires a PURE delete: co-occurring hard flags (-f/--force/--force-with-lease/--mirror/--prune/+refspec, branch -f) make the statement hard (AC-02, strictest wins within one statement); the scan no longer breaks after the first destructive statement while ask is still eligible, so a later hard statement wins; 1.14.0: issue #1217 -- destructive gate gains a dormant, fail-closed user-approval (ask) subclass for `git branch -D` / `git push --delete` / `git push :ref` only; activation DEFAULT OFF (runtime config key + harness interactivity signal), never agent/sentinel-triggerable, never permissionDecision:allow; strict/mutation blocks still win (exit 2); 1.13.0: issue #1181 -- a granted role's sentinel is restricted to git add / non-amending git commit (all_git classifier field + IS_GRANT_SENTINEL gate); issues #1169/#1238 -- one interpreter start reads all payload fields via hook_json_get_many (importable hook_json_many.py module); issue #1210 -- harness payload role field (`agent_type`, gated by the `hook-role-field` capability) cross-checks the self-declared sentinel and rejects a mismatch; 1.12.0: issue #1258 -- `git branch` with read-only list-mode flags (--list/-l, --contains, --no-contains, --merged, --no-merged, --points-at, -a/--all, -r/--remotes, --show-current) is no longer misread as branch creation when it carries a positional; modifying flags and bare `git branch <name>` stay mutations. 1.11.0: issue #1151 (audit G1) -- NotebookEdit/MultiEdit are judged like Edit and PowerShell like Bash (F6-01); an Agent/Task call with isolation "worktree", or one from a subagent that spawns `orchestrator`, is blocked (F3-03); `git stash` (bare/push/apply/...), mv, apply, notes, replace, update-index, config writes, fast-import, init, submodule update/add/... and gc are mutations, `stash list/show` and config reads stay read-only (F6-04); a sentinel on a main-thread call is discarded when the provider's payload carries a reliable agent_id (sync-time capability `hook-agent-id`, F6-05); the body of a $(...)/backtick substitution -- also inside double quotes -- is classified as its own statement (F6-03, part of #592); the mutation block message names the subagent instead of the main chat when agent_id is set and the fork-bomb hint only appears on a fork-bomb verdict (F6-08). 1.10.0: the sentinel grammar accepts an optional audit-only instance id (`#agent-meta:agent=<role> id=<orchestrator-id>`); the id is appended to the orchestrator audit line as `orchestrator_id=<id|unset>` and is NEVER read by the allow/deny path (OQ-2 = A, AC-11 P3). The id token is validated against the instance grammar `[a-z0-9][a-z0-9._-]{0,39}` (no `..`); an invalid id makes the whole sentinel unparseable, exactly like a malformed role.
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
# Project root (SR-B-11, v1.7.0): resolved via $AM_PROJECT_DIR or a
# walk-up to the nearest `.meta-config/` ancestor, so strict mode and the
# auto-commit allowlist still apply after a `cd` into a subdirectory.
#
# Only mutating tools (Write, Edit, Bash) are intercepted; NotebookEdit and
# MultiEdit count as Edit, PowerShell as Bash (#1151). Agent/Task calls are
# checked for worktree isolation and orchestrator re-spawns only.
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
# `parse_git` / `is_destructive` / `is_mutation` functions in the deployed
# `lib/hook_guard_scan.py` module) instead of matching raw regexes against the whole command
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
#   * the interpreter indirections `eval`, `bash -c`/`sh -c`, `env -S` and
#     `xargs ... sh -c`: the payload of these is a STRING, not a command
#     list, so a git mutation hidden there is not classified. This is
#     structural for a token scanner (the hook never executes anything) and
#     is the #592 trade-off. Command substitution bodies ($(...) and
#     backticks, also inside double quotes) ARE classified since #1151: the
#     shared splitter emits each body as an extra statement and leaves the
#     surrounding command intact. Still a gap: a command WORD produced by a
#     command substitution (`$(echo git) commit`) is not classified.
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
   || ! declare -F hook_json_get_many >/dev/null 2>&1 \
   || ! declare -F hook_known_tool_name >/dev/null 2>&1 \
   || ! declare -F hook_shell_scan_py >/dev/null 2>&1 \
   || ! declare -F hook_is_meta_submodule_dir >/dev/null 2>&1; then
  echo "ORCHESTRATOR_GUARD: $SCRIPT_DIR/lib/hook_common.sh is outdated (shared guard helpers missing)." >&2
  echo "Failing closed — re-run sync.py to redeploy the hooks/lib/ directory." >&2
  exit 2
fi

_GUARD_MODULE_DIR="$SCRIPT_DIR/lib"
for _module in hook_guard_policy.py hook_guard_scan.py; do
  if [ ! -r "$_GUARD_MODULE_DIR/$_module" ]; then
    echo "ORCHESTRATOR_GUARD: required module $_GUARD_MODULE_DIR/$_module is missing or unreadable." >&2
    echo "Failing closed (issue #595/#1238b2) — re-run sync.py to redeploy the hooks/lib/ directory." >&2
    exit 2
  fi
done

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
# #1169: ONE interpreter start reads every field this guard uses. The `ok`
# trailer distinguishes a failed parse from a missing field, so the old
# standalone json.loads gate (and its exit-2 message) moves in here. A NUL in
# any requested value fails the whole call instead of shifting the fields
# into the wrong variables (fail closed, SPEC-HOOK-SINGLE-PARSE §2.4).
# bash 3.2 compatible: `read -r -d ''` only, no eval/mapfile/namerefs.
_P_FAIL=0
{
  IFS= read -r -d '' _P_TOOL_NAME     || _P_FAIL=1
  IFS= read -r -d '' _P_AGENT_ID      || _P_FAIL=1
  IFS= read -r -d '' _P_ISOLATION     || _P_FAIL=1
  IFS= read -r -d '' _P_SUBAGENT_TYPE || _P_FAIL=1
  IFS= read -r -d '' _P_COMMAND       || _P_FAIL=1
  IFS= read -r -d '' _P_CWD           || _P_FAIL=1
  IFS= read -r -d '' _P_AGENT_TYPE    || _P_FAIL=1
  IFS= read -r -d '' _P_TRAILER       || _P_FAIL=1
} < <(hook_json_get_many "$INPUT" \
       tool_name agent_id tool_input.isolation tool_input.subagent_type \
       tool_input.command cwd agent_type)
if [ "$_P_FAIL" -ne 0 ] || [ "${_P_TRAILER:-}" != "ok" ]; then
  echo "ORCHESTRATOR_GUARD: hook payload is not valid JSON." >&2
  echo "Failing closed (SR-B-09) -- the guard cannot evaluate a call it cannot parse." >&2
  exit 2
fi

TOOL_NAME="$_P_TOOL_NAME"
AGENT_ID="$_P_AGENT_ID"

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
# AGENT_ID was read by the single parse above (#1169); no second spawn.

# Delegation gate (#1151 F3-03): the orchestrator is a singleton spawned by the
# main chat, and worktree isolation is forbidden for every spawn
# (rules/1-generic/no-worktree-isolation.md). Both used to be text only.
if [ "$TOOL_NAME" = "Agent" ] || [ "$TOOL_NAME" = "Task" ]; then
  if [ "$_P_ISOLATION" = "worktree" ]; then
    echo "ORCHESTRATOR_GUARD: isolation \"worktree\" is forbidden (no-worktree-isolation rule)." >&2
    echo "Spawn the agent without isolation so it works in the project directory." >&2
    exit 2
  fi
  _SUBAGENT_TYPE=$(printf '%s' "$_P_SUBAGENT_TYPE" | tr '[:upper:]' '[:lower:]')
  if [ -n "$AGENT_ID" ] && [ "$_SUBAGENT_TYPE" = "orchestrator" ]; then
    echo "ORCHESTRATOR_GUARD: a subagent must not spawn the orchestrator (singleton rule, anti-recursion)." >&2
    echo "Return your result to the caller instead of delegating back to the orchestrator." >&2
    exit 2
  fi
  exit 0
fi

# Write-capable tools without their own branch map onto the one they behave
# like (#1151 F6-01): NotebookEdit/MultiEdit edit a file like Edit, PowerShell
# runs a shell command (tool_input.command) like Bash.
case "$TOOL_NAME" in
  NotebookEdit|MultiEdit) TOOL_NAME="Edit" ;;
  PowerShell) TOOL_NAME="Bash" ;;
esac

# Only block mutating tools
case "$TOOL_NAME" in
  Write|Edit|Bash) ;;
  *) exit 0 ;;
esac

BASH_CMD=""
DECLARED_AGENT=""
DECLARED_ID=""
if [ "$TOOL_NAME" = "Bash" ]; then
  BASH_CMD="$_P_COMMAND"

  # Self-declared agent identity (see note above): the first non-blank line
  # of the command must be exactly '#agent-meta:agent=<name>' or
  # '#agent-meta:agent=<name> id=<instance-id>'. Only orchestrator and git
  # are recognized delegates for this guard.
  # `head -n1` alone (pre-#503) grabbed a literal empty first line whenever
  # BASH_CMD started with a leading newline before the sentinel -- some
  # delegated agents construct their Bash invocation that way -- so the
  # sentinel was silently missed and the legitimate mutation got blocked.
  # Stripping leading whitespace/blank lines before taking "line 1" makes
  # detection tolerant of that construction.
  #
  # P3 audit record (AC-11, OQ-2 = A): the full record is
  # `{orchestrator_id, scope_id, spawned_by, spawned_at}`; the guard reduces
  # it to `orchestrator_id` only. That id is AUDIT-ONLY: it is appended to
  # the audit log and is NEVER read by an allow/deny decision. The id token
  # uses the instance grammar `[a-z0-9][a-z0-9._-]{0,39}` (no `..`); an
  # invalid id invalidates the whole sentinel (empty role), like a bad role.
  _DECLARED_RAW=$(printf '%s' "$BASH_CMD" | "$_PY" "$_GUARD_MODULE_DIR/hook_guard_policy.py" sentinel 2>/dev/null || echo "")
  if [ -n "$_DECLARED_RAW" ]; then
    DECLARED_AGENT=${_DECLARED_RAW%%|*}
    DECLARED_ID=${_DECLARED_RAW#*|}
  fi
fi

# Sentinel vs. caller (#1151 F6-05). Baked at sync time from the provider's
# `hook-agent-id` capability (config/ai-providers.yaml, scripts/lib/hooks.py):
# "true" means the payload carries a harness-set agent_id for every subagent
# call. Delegates (git, orchestrator, auto-commit roles) are always subagents
# there, so a sentinel on a MAIN-thread call is a forged self-declaration and
# is discarded. Any other value -- "false" for a provider whose payload has no
# agent_id (the sentinel is then the only delegate signal), or the literal
# placeholder in an unsynced source copy -- keeps the sentinel as before.
HOOK_AGENT_ID_RELIABLE="false"
# #1210: whether this provider's payload carries a harness-set role field
# (Claude's `agent_type`), baked from the `hook-role-field` capability. The
# value is read in the single parse above (_P_AGENT_TYPE); a "true" flag lets
# the guard cross-check the self-declared sentinel against that role. Any
# other value -- including the literal placeholder in an unsynced source copy
# -- keeps the convention-boundary sentinel-only path (fail closed).
HOOK_ROLE_FIELD_RELIABLE="false"
SENTINEL_DISCARDED=0
if [ -n "$DECLARED_AGENT" ] && [ -z "$AGENT_ID" ] && [ "$HOOK_AGENT_ID_RELIABLE" = "true" ]; then
  DECLARED_AGENT=""
  DECLARED_ID=""
  SENTINEL_DISCARDED=1
fi

# Determine project root (needed by the audit log, allowlist and config
# lookup). SR-B-11: the payload cwd alone is not enough -- after the main
# thread `cd`s into a subdirectory, `.meta-config/project.yaml` was not
# found there and strict mode was silently off. Resolution order:
#   1. $AM_PROJECT_DIR (adapter-set) if it is an existing directory
#      containing .meta-config/;
#   2. otherwise the nearest ancestor of the payload cwd (inclusive)
#      containing .meta-config/ (same walk-up as dod-push-check.sh);
#   3. otherwise the payload cwd itself (prior behaviour).
# Issue #943 (l): a nested agent-meta checkout (`.agent-meta/`, or
# `external/agent-meta/`) carries its own `.meta-config/`. On a non-Claude
# provider without $AM_PROJECT_DIR, the walk-up used to stop there and
# applied the SUBMODULE's strict mode / allowlist instead of the enclosing
# project's. Such a candidate is skipped while walking (but kept as a
# fallback, so a session opened only inside the submodule still resolves).
# PAYLOAD_CWD stays the base for cwd-relative arguments (commit -F <file>).
PAYLOAD_CWD="$_P_CWD"
if [ -z "$PAYLOAD_CWD" ]; then
  PAYLOAD_CWD="$PWD"
fi
PROJECT_ROOT=""
_SUBMODULE_ROOT=""
if [ -n "${AM_PROJECT_DIR:-}" ] && [ -d "$AM_PROJECT_DIR/.meta-config" ]; then
  PROJECT_ROOT="$AM_PROJECT_DIR"
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

# --- #1210 / #1335: harness role field attribution -----------------------
# Provider-agnostic: the baked capability flag (never a provider name) decides
# whether the payload role is trustworthy. The existing #1210 read/cross-check
# stays in place; _ROLE_ATTRIBUTION is now CONSUMED (not merely set) as the
# authoritative role source for allow matching (IC-1/IC-2).
_ROLE_ATTRIBUTION="sentinel"
_PAYLOAD_ROLE=""   # normalized lowercase; initialized for `set -u`
if [ "$TOOL_NAME" = "Bash" ] && [ "$HOOK_ROLE_FIELD_RELIABLE" = "true" ] \
   && [ -n "$AGENT_ID" ]; then
  _PAYLOAD_ROLE=$(printf '%s' "$_P_AGENT_TYPE" | tr '[:upper:]' '[:lower:]')
  _DECLARED_ROLE=$(printf '%s' "$DECLARED_AGENT" | tr '[:upper:]' '[:lower:]')
  if [ -n "$_PAYLOAD_ROLE" ]; then
    _ROLE_ATTRIBUTION="payload-field"
    if [ -n "$_DECLARED_ROLE" ] && [ "$_PAYLOAD_ROLE" != "$_DECLARED_ROLE" ]; then
      _AUDIT_LOG="$PROJECT_ROOT/.claude/hooks/.guard-audit.log"
      _AUDIT_LINE=$(printf '%s decision=rejected class=role-mismatch attribution=payload-field field=%s sentinel=%s cmd=%s' \
        "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$_PAYLOAD_ROLE" "$_DECLARED_ROLE" \
        "$(printf '%s' "$BASH_CMD" | tr '\n\t' '  ' | head -c 200)")
      hook_audit_log_append "$_AUDIT_LOG" "$_AUDIT_LINE"
      echo "ORCHESTRATOR_GUARD: role mismatch — payload role field \"$_PAYLOAD_ROLE\" != sentinel role \"$_DECLARED_ROLE\". The sentinel cannot override the harness-provided role." >&2
      exit 2
    fi
  fi
fi

# IC-1 FAIL-CLOSED GATE: on a payload-attributed provider a subagent call
# (non-empty agent_id) MUST carry a non-empty harness role. Empty/missing role
# means the guard cannot decide -> exit 2 for the whole call, NEVER
# permissionDecision:allow, no sentinel fallback, no delegate/grant fallback.
# This is independent of _ROLE_ATTRIBUTION (which stays "sentinel" when the
# field is empty) precisely so the model-writable sentinel cannot resurrect it.
if [ "$TOOL_NAME" = "Bash" ] && [ "$HOOK_ROLE_FIELD_RELIABLE" = "true" ] \
   && [ -n "$AGENT_ID" ] && [ -z "$_PAYLOAD_ROLE" ]; then
  _AUDIT_LOG="$PROJECT_ROOT/.claude/hooks/.guard-audit.log"
  _AUDIT_LINE=$(printf '%s decision=rejected class=attribution-missing attribution=payload-field cmd=%s' \
    "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    "$(printf '%s' "$BASH_CMD" | tr '\n\t' '  ' | head -c 200)")
  hook_audit_log_append "$_AUDIT_LOG" "$_AUDIT_LINE"
  echo "ORCHESTRATOR_GUARD: harness role field is empty for a subagent call; failing closed (no sentinel fallback, no grant)." >&2
  exit 2
fi

# IC-2: the authoritative effective role. Payload role wins when the harness
# supplies it; otherwise the sentinel role (the capability-false / main-thread
# path, byte-for-byte unchanged). Empty role on a payload-attributed subagent
# call is rejected above with exit 2 (no sentinel fallback/grant). A NON-EMPTY
# but unknown role receives NO role flags: read-only operations still pass
# (rc 0), while mutation operations fail closed at the mutation gate (exit 2).
# The guard never grants; no new grant is invented.
if [ "$_ROLE_ATTRIBUTION" = "payload-field" ]; then
  EFFECTIVE_ROLE="$_PAYLOAD_ROLE"
else
  EFFECTIVE_ROLE=$(printf '%s' "$DECLARED_AGENT" | tr '[:upper:]' '[:lower:]')
fi

# --- Role elevation: EFFECTIVE_ROLE-scoped + audited (#516/#1210/#1335) ---
# The four flags keep their historic NAMES (all matching gates below read
# them), but since #1335 their ROLE is EFFECTIVE_ROLE: the harness payload
# role when reliable, otherwise the self-declared sentinel. When the role
# field is reliable, DECLARED_AGENT is only a mismatch/audit signal -- it is
# NOT a grant source. Capability-false/main-thread runs are unchanged.
IS_GIT_SENTINEL=0
IS_ORCH_SENTINEL=0
IS_ALLOWLIST_SENTINEL=0
# Issue #1181: separate flag for a role explicitly granted direct commit
# authority by the v2 allowlist's `authority_overrides` map. Deliberately NOT
# IS_ALLOWLIST_SENTINEL -- the existing mutation gate's logic stays unchanged.
IS_GRANT_SENTINEL=0

if [ "$TOOL_NAME" = "Bash" ] \
   && { [ -n "$DECLARED_AGENT" ] || [ "$_ROLE_ATTRIBUTION" = "payload-field" ]; }; then
  _ROLE="$EFFECTIVE_ROLE"
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
      # #1335: this config-driven elevation stays bound to the SELF-DECLARED
      # sentinel. A payload-only role never gains a new grant (AC-03/IC-2).
      if [ -n "$DECLARED_AGENT" ]; then
        _ALLOWLIST="$PROJECT_ROOT/.meta-config/auto-commit-allowlist.json"
        if [ -f "$_ALLOWLIST" ]; then
          _AC_MODE=$("$_PY" "$_GUARD_MODULE_DIR/hook_guard_policy.py" allowlist-mode "$_ALLOWLIST" 2>/dev/null)
          # Only 'auto'/'custom' grant hook-level commit authority; 'suggest'
          # roles merely propose a commit message and must never gain the
          # sentinel even though they may now appear in eligible_roles (that
          # list reflects capability, not per-mode authority -- see
          # scripts/lib/auto_commit.py resolve_auto_commit_config()).
          if [ "$_AC_MODE" = "auto" ] || [ "$_AC_MODE" = "custom" ]; then
            _IS_ELIGIBLE=$("$_PY" "$_GUARD_MODULE_DIR/hook_guard_policy.py" allowlist-eligible "$_ALLOWLIST" "$_ROLE" 2>/dev/null)
            if [ "$_IS_ELIGIBLE" = "1" ]; then
              IS_ALLOWLIST_SENTINEL=1
              _AUDIT_ROLE="$_ROLE"
            fi
          fi
        fi
      fi
      ;;
  esac
  # Issue #1181: a role listed as a KEY in the v2 allowlist's
  # `authority_overrides` map has been granted direct commit authority.
  # This is a SEPARATE flag: IS_ALLOWLIST_SENTINEL (set above) still drives
  # the existing mutation gate unchanged; the dedicated grant gate below
  # uses this one to narrow the sentinel to add / non-amending commit only.
  # A v1 allowlist has no such key -> no grant -> full shell as before.
  # #1335: also sentinel-bound -- never derive a NEW grant from the payload.
  if [ -n "$DECLARED_AGENT" ]; then
    _ALLOWLIST="$PROJECT_ROOT/.meta-config/auto-commit-allowlist.json"
    if [ -f "$_ALLOWLIST" ]; then
      _IS_GRANT=$("$_PY" "$_GUARD_MODULE_DIR/hook_guard_policy.py" allowlist-grant "$_ALLOWLIST" "$_ROLE" 2>/dev/null)
      if [ "$_IS_GRANT" = "1" ]; then
        IS_GRANT_SENTINEL=1
      fi
    fi
  fi
  if [ -n "$_AUDIT_ROLE" ]; then
    # hook_audit_log_append (hooks/1-generic/lib/hook_common.sh) redacts
    # credential-shaped substrings before writing (issue #596), hardens
    # the log file to 600 permissions on every write (issue #596), and
    # caps unbounded growth via truncate-oldest rotation (issue #597).
    #
    # P3 (AC-11, OQ-2 = A): the orchestrator audit line carries the reduced
    # instance record `orchestrator_id=<id|unset>`. It is logging only -- the
    # decision above never reads DECLARED_ID -- and the git/allowlist lines
    # keep their historic shape (no instance field, #1335 adds attribution).
    _AUDIT_INSTANCE=""
    if [ "$_AUDIT_ROLE" = "orchestrator" ]; then
      _AUDIT_INSTANCE=" orchestrator_id=${DECLARED_ID:-unset}"
    fi
    _AUDIT_LOG="$PROJECT_ROOT/.claude/hooks/.guard-audit.log"
    _AUDIT_LINE=$(printf '%s role=%s%s attribution=%s cmd=%s' \
      "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$_AUDIT_ROLE" "$_AUDIT_INSTANCE" \
      "$_ROLE_ATTRIBUTION" \
      "$(printf '%s' "$BASH_CMD" | tr '\n\t' '  ' | head -c 200)")
    hook_audit_log_append "$_AUDIT_LOG" "$_AUDIT_LINE"
  fi
fi

# --- Unified git-statement scan (issue #551): ONE tokenizer feeds BOTH ---
# gates. The destructive gate (below) applies regardless of sentinel; the
# mutation gate (further down) applies only in non-strict mode for non-git
# callers. Classifying once, with the same tokenizer, keeps the two gates
# consistent and fixes the raw-regex gaps #590/#591/#602 (see header note).
# The scan prints exactly five words: '<category> <scope> <bom> <all_git>
# <ask_class>', where category is 'destructive', 'mutation' or 'none'
# ('destructive' takes precedence when a statement is both), scope is 'broad',
# 'narrow' or 'forkbomb', and bom is 'message' | 'file' | 'none' (issue #842: a
# leading UTF-8 BOM in a commit message; the detector also covers ANSI-C quoting
# -- -m $'\uFEFF...' -- and combined short-option clusters/glued forms like
# -am/-mMSG). The fourth word (issue #1181) is 1 only when EVERY statement's
# command word is `git`, else 0; the grant gate uses it to reject a mixed
# git+non-git command list. The fifth word marks the opt-in #1217 ask subclass.
# Scope only
# qualifies a
# 'mutation': 'narrow' means every git mutation found is `add` or a
# non-amending `commit`, 'broad' means at least one other mutation is present
# (push/rm/merge/rebase/reset/restore/tag/branch/checkout/stash, since
# SR-B-13 also pull/switch/cherry-pick/revert/am/update-ref/worktree, or
# `commit --amend`, which rewrites history). The allowlist sentinel
# (issue #694) may only pass 'narrow'.
#
# The deployed classifier imports the shared quote/heredoc-aware statement
# splitter and fork-bomb detector from hook_shell_scan.py. Any classifier
# failure -- a non-zero interpreter exit or output that is not exactly
# '<category> <scope> <bom> <all_git> <ask_class>' -- fails CLOSED (exit 2).
# The old '|| echo none narrow none' fallback allowed every call whose
# classifier died (issue #943 (k)).
_GIT_SCAN="none"
_GIT_SCAN_SCOPE="narrow"
_GIT_BOM="none"
_GIT_SCAN_ALL_GIT="0"
if [ "$TOOL_NAME" = "Bash" ]; then
  _GIT_SCAN_RC=0
  _GIT_SCAN_RAW=$(printf '%s' "$BASH_CMD" | "$_PY" "$_GUARD_MODULE_DIR/hook_guard_scan.py" "$PAYLOAD_CWD" 2>/dev/null) || _GIT_SCAN_RC=$?
  if [ "$_GIT_SCAN_RC" != "0" ]; then
    echo "ORCHESTRATOR_GUARD: the git/destructive classifier exited rc=$_GIT_SCAN_RC." >&2
    echo "Failing closed (issue #943 (k)) — an unevaluable command must not be allowed." >&2
    exit 2
  fi
  if [ "$(printf '%s' "$_GIT_SCAN_RAW" | awk 'NF{print NF}')" != "5" ]; then
    echo "ORCHESTRATOR_GUARD: the git/destructive classifier returned malformed output." >&2
    echo "Failing closed (issue #943 (k)) — an unevaluable command must not be allowed." >&2
    exit 2
  fi
  _GIT_SCAN=$(printf '%s' "$_GIT_SCAN_RAW" | awk '{print $1}')
  _GIT_SCAN_SCOPE=$(printf '%s' "$_GIT_SCAN_RAW" | awk '{print $2}')
  _GIT_BOM=$(printf '%s' "$_GIT_SCAN_RAW" | awk '{print $3}')
  _GIT_SCAN_ALL_GIT=$(printf '%s' "$_GIT_SCAN_RAW" | awk '{print $4}')
  _GIT_SCAN_ASK_CLASS=$(printf '%s' "$_GIT_SCAN_RAW" | awk '{print $5}')
  case "$_GIT_SCAN_ALL_GIT" in
    0|1) ;;
    *)
      echo "ORCHESTRATOR_GUARD: the git/destructive classifier returned an unknown all-git flag '$_GIT_SCAN_ALL_GIT'." >&2
      echo "Failing closed (issue #1181) — an unevaluable command must not be allowed." >&2
      exit 2
      ;;
  esac
  case "$_GIT_SCAN_ASK_CLASS" in
    0|1) ;;
    *)
      echo "ORCHESTRATOR_GUARD: the git/destructive classifier returned an unknown ask class '$_GIT_SCAN_ASK_CLASS'." >&2
      echo "Failing closed (issue #1217)." >&2
      exit 2
      ;;
  esac
  case "$_GIT_SCAN" in
    destructive|mutation|none) ;;
    *)
      echo "ORCHESTRATOR_GUARD: the git/destructive classifier returned an unknown category '$_GIT_SCAN'." >&2
      echo "Failing closed (issue #943 (k))." >&2
      exit 2
      ;;
  esac
  case "$_GIT_SCAN_SCOPE" in
    broad|narrow|forkbomb) ;;
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

# --- #1217 ask activation: config-driven, DEFAULT OFF, fail closed ------
# Three independent conditions must ALL hold before an ask is even considered;
# absence of any one leaves the original hard exit 2 untouched:
#   1. activation: runtime config key orchestrator.destructive-ask.enabled
#      (provider-agnostic, no provider-name branch). Any read/parse error
#      resolves to OFF. This key is NOT set by this repo -> delivered
#      behaviour remains exit 2 (spec OFFEN 1: activation deferred).
#   2. interactivity: harness-set AGENT_META_HARNESS_INTERACTIVE=1. An agent
#      cannot set the hook process environment from the command string, and
#      no harness in this repo is confirmed to set it -> absent = headless.
#   3. forgery-clean: no sentinel / no agent_id / no declared role on the
#      call. Sentinels and model-written text can never trigger ask or grant
#      approval; the approval itself is given only by the human in the
#      harness after the native "ask" dialog. Never permissionDecision:allow.
_ASK_CFG="$PROJECT_ROOT/.meta-config/project.yaml"
_ASK_ENABLED=0
if [ -f "$_ASK_CFG" ]; then
  _ASK_ENABLED=$("$_PY" "$_GUARD_MODULE_DIR/hook_guard_policy.py" ask-enabled "$_ASK_CFG" 2>/dev/null)
fi
case "$_ASK_ENABLED" in
  0|1) ;;
  *) echo "ORCHESTRATOR_GUARD: ask activation check produced no result; failing closed (#1217)." >&2
     _ASK_ENABLED=0 ;;
esac

_ASK_INTERACTIVE=0
if [ "${AGENT_META_HARNESS_INTERACTIVE:-}" = "1" ]; then
  _ASK_INTERACTIVE=1
fi

_ASK_FORGERY_CLEAN=1
if [ -n "${DECLARED_AGENT:-}" ] || [ -n "${AGENT_ID:-}" ] \
   || [ "$IS_GIT_SENTINEL" = "1" ] || [ "$IS_ORCH_SENTINEL" = "1" ] \
   || [ "$IS_ALLOWLIST_SENTINEL" = "1" ] || [ "$IS_GRANT_SENTINEL" = "1" ]; then
  _ASK_FORGERY_CLEAN=0
fi

# --- Destructive-operation gate: applies regardless of sentinel --------
# Ask is DEFERRED, not emitted here: only a flag is set and execution falls
# through every later blocking gate (strict / mutation / grant). Any stricter
# block exits 2 first, so a later deny always wins over ask (AC-08).
_ASK_PENDING=0
if [ "$TOOL_NAME" = "Bash" ] && [ "$_GIT_SCAN" = "destructive" ]; then
  if [ "$_ASK_ENABLED" = "1" ] && [ "$_GIT_SCAN_ASK_CLASS" = "1" ] \
     && [ "$_ASK_INTERACTIVE" = "1" ] && [ "$_ASK_FORGERY_CLEAN" = "1" ]; then
    _ASK_PENDING=1
  else
    echo "ORCHESTRATOR_GUARD: destructive operation requires explicit user approval (issue #516)." >&2
    echo "Detected command: $(printf '%s' "$BASH_CMD" | head -c 200)" >&2
    if [ "$_GIT_SCAN_SCOPE" = "forkbomb" ]; then
      echo "If this is a shell function: a body without an unquoted '}' in its first 512 characters is blocked by the fork-bomb scan (fail closed)." >&2
    fi
    echo "Ask the user to approve and run this command manually." >&2
    exit 2
  fi
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
  STRICT=$("$_PY" "$_GUARD_MODULE_DIR/hook_guard_policy.py" strict "$CONFIG_FILE" "$AGENT_META_PROVIDER")
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
    if [ "$SENTINEL_DISCARDED" = "1" ]; then
      echo "The #agent-meta:agent= sentinel is ignored on the main thread (no agent_id in the payload, #1151)." >&2
    fi
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
  if [ -n "$AGENT_ID" ]; then
    echo "ORCHESTRATOR_GUARD: Direct git mutations are forbidden for this subagent (no \`git\` sentinel, or outside its auto-commit scope)." >&2
  else
    echo "ORCHESTRATOR_GUARD: Direct git mutations are forbidden in the main chat." >&2
    if [ "$SENTINEL_DISCARDED" = "1" ]; then
      echo "The #agent-meta:agent= sentinel is ignored on the main thread (no agent_id in the payload, #1151)." >&2
    fi
  fi
  echo "Detected command: $(printf '%s' "$BASH_CMD" | head -c 200)" >&2
  echo "Delegate git operations to the \`git\` agent." >&2
  exit 2
fi

# --- Issue #1181: a granted role's sentinel is the commit path only -------
# Covers ONLY commands that actually carry the sentinel (IS_GRANT_SENTINEL=1):
# a granted role may stage and commit (git add / non-amending git commit) and
# NOTHING else -- non-git commands (curl ...), mixed git+non-git command lists,
# git status/log, push and `commit --amend` all fall through to exit 2. That is
# intentional (Spec §3.3.1 point 2): for a granted role the sentinel IS the
# commit path, not a general shell pass. Do not "fix" this by widening it.
# D18 / attribution gap #1210: this gate never sees a command WITHOUT the
# sentinel -- it is NOT a security boundary against injection, only the
# convention-boundary role check documented in this file's header (still a
# best-effort token scan, no shell interpreter). The grant is narrow on
# purpose; an unattributed command stays outside it exactly like today.
if [ "$TOOL_NAME" = "Bash" ] && [ "$IS_GRANT_SENTINEL" = "1" ]; then
  if [ "$_GIT_SCAN" != "mutation" ] || [ "$_GIT_SCAN_SCOPE" != "narrow" ] || [ "$_GIT_SCAN_ALL_GIT" != "1" ]; then
    echo "ORCHESTRATOR_GUARD: a granted commit role may only use its sentinel for \`git add\`/\`git commit\` (issue #1181)." >&2
    exit 2
  fi
fi

# --- #1217: emit the deferred ask ONLY after every blocking gate passed ---
# The command is emitted unchanged (no 200-char truncation) as valid JSON;
# only credential-like values are redacted. If JSON cannot be produced the
# hook fails CLOSED with the original stderr text (AC-07). No approved/denied
# audit is written without a harness event; 'asked' only records the offer.
if [ "$_ASK_PENDING" = "1" ]; then
  _ASK_JSON=$("$_PY" "$_GUARD_MODULE_DIR/hook_guard_policy.py" ask-json "$BASH_CMD" 2>/dev/null) || _ASK_JSON=""
  if [ -z "$_ASK_JSON" ]; then
    echo "ORCHESTRATOR_GUARD: destructive operation requires explicit user approval (issue #516)." >&2
    echo "Ask the user to approve and run this command manually." >&2
    exit 2
  fi
  _AUDIT_LOG="$PROJECT_ROOT/.claude/hooks/.guard-audit.log"
  _AUDIT_LINE=$(printf '%s decision=asked class=ask cmd=%s' \
    "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    "$(printf '%s' "$BASH_CMD" | tr '\n\t' '  ' | head -c 200)")
  hook_audit_log_append "$_AUDIT_LOG" "$_AUDIT_LINE"
  printf '%s\n' "$_ASK_JSON"
fi

exit 0
