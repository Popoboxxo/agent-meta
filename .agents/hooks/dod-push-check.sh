#!/bin/bash
# hook: dod-push-check
# version: 2.7.0
# event: PreToolUse
# matcher: Bash
# protocol: tool-hook-v1
# description: Blocks git push on/to main/master (Branch-Guard) and until tests are green (DoD enforcement)
# enabled_by_default: false
# changelog: v2.7.0: issue #1238c1 -- MB-1 SRP split of what was left in Bash: the Branch-Guard verdict mapping, the test-gate state machine, the result-cache key and the test-result classification moved into hook_dod_push_policy.py (pure, side-effect free functions) and every user-visible message into hook_dod_push_report.py (one reporter scene per path, message to the stream the hook already used); the shell keeps orchestration only, its exit codes stay 0=allow/2=block and a missing module still fails closed. No message, exit or cache/timeout/branch-guard behaviour change. v2.6.0: issue #1238c1 -- move payload-state, config reading and push classification into flat deployed Python modules; reuse the T23 shell scanner and push-argument parser and keep fail-closed behavior without Python or modules. v2.5.4: issue #1161 Pkt5 -- tool_name and tool_input.command are read in ONE hook_json_get_many parse (ok-trailer fail-closed check) instead of two separate field-read interpreter starts; the hook_json_usable probe and the R2-2 unreadable-payload re-check are unchanged. v2.5.3: a naive-split fragment cut out of the quoted text of a non-executing text consumer (gh --body "... && git push ...", echo, printf) is no longer blocked as a push with a quote spanning a command separator; wrappers (bash -c, eval, xargs) stay fail-closed. v2.5.2: the Branch-Guard takes the branch from the push's effective directory (git -C <path> chain, or a leading cd <path> && ...) via git -C <dir> symbolic-ref instead of the hook cwd, so feature-branch worktrees can be pushed while the main checkout is on main; unresolvable targets (computed/glob/~, missing or non-repo path, detached HEAD, pushd/popd, non-leading or repeated cd, --git-dir/GIT_DIR) stay fail closed. v2.5.1: a heredoc line that also carries '&&', ';' or '|' BEFORE the operator ('mkdir d && cat > f <<EOF') is stripped when the statement owning the heredoc is a text consumer, so prose bodies are no longer classified as shell (false positive); '|', ';', '&' or a backtick AFTER the operator ('<<EOF | bash') still keeps the body (fail closed); convention boundary only, eval/variable indirection stays undetected; v2.5.0: the body of a $(...)/backtick command substitution -- also inside double quotes, where the tokenizer kept it as one opaque word -- is classified as its own command line, so 'echo "$(git push origin main)"' is blocked (shared scanner hook_shell_scan_py, #1151 F6-03); a "$'" inside double quotes is literal text and no longer triggers the ANSI-C path, and the word list of 'for VAR in WORDS' is data, not a command (F6-09: two false positives); v2.4.0: the push.recurseSubmodules override value is parsed where the command line carries it (-c/--config, GIT_CONFIG_VALUE_n): check/no/false stay inert even when the repository declares submodules, while --config-env stays value-blind (it names the variable, not the value) and is treated as recursing; the tag-only shortcut now uses the same submodule gate as the destination check, so a config recursion no longer blocks a release tag push in a repo without .gitmodules (#1041); v2.3.0: push.recurseSubmodules set through the effective config, -c/--config-env or GIT_CONFIG_* is honoured like the explicit flag: on-demand/only blocks when the repository declares submodules (same per-submodule destination check as #1051), the explicit --recurse-submodules/--no-recurse-submodules wins over the config (check/no and --no- stay inert), and the tag-only shortcut is skipped when the config recurses; the config of a foreign repo (-C/GIT_DIR) remains a documented gap (#1041); v2.2.0: --recurse-submodules=on-demand|only no longer blocks every repository that declares submodules: each submodule's own push destination (remote.<name>.push, then push.default / branch.<n>.merge, mirroring git's recurse push which forwards only the remote name) is checked against the protected-branch set, and a protected or undeterminable destination still fails closed, naming submodule path, destination and the way out (#1051, residual of #953); v2.1.7: the flag/short-cluster walk and the protected-branch set are built once in lib/hook_common.sh (hook_push_arg_parser_py, hook_protected_branches) instead of twice (tag-only vs. destination check, classifier vs. block message), so both consumers always agree on positionals (#949); the shared walk consumes --recurse-submodules' separately passed value, so the space form cannot slip past the submodule check (#953), an unreadable git config now fails closed on every path, the tag-only shortcut included (it used to read the config verdict before the config was read, so `git push --tags` still exited 0), and a python3 that exits 0 with garbage or non-zero is detected (#954); v2.1.6: the protected-branch list in the push-block message is de-duplicated (a configured GIT_MAIN_BRANCH of main/master no longer appears twice) (#1033); v2.1.5: --recurse-submodules=on-demand|only in a repo with submodules (or another repo) fails closed because the submodules push to their own remotes/branches (#953); v2.1.4: a push in a command that changes directory (cd/pushd/popd) is judged as a push into another repository (refspec-less/HEAD pushes blocked, cwd branch and config no longer assumed) (#952); v2.1.3: heredoc bodies fed to a text-only consumer (cat/gh/tee/git commit) are no longer classified as commands (#947), an unquoted word-start # comment is cut before tokenizing while quoted/mid-word # stay literal (#948), xargs carrying a git push and the {} placeholder fail closed (#950), computed-refspec block message names the HEAD / literal-branch way out (#950); v2.1.2: command-running git subcommands carrying a push blocked again (submodule foreach/bisect run git push, rebase -x/filter-branch/difftool -x/config with 'git ... push', R2-1), -c/--config-env aliases resolved or blocked, exec config (core.pager/sshCommand/editor, sequence.editor, ...) on a push or carrying one blocked, rg --pre/ack --pager blocked (R2-5), unreadable Bash command in the payload blocked instead of skipped (R2-2), linear classifier (shlex token buffer, brace/nested scans) + 20 s budget that blocks on overrun (R2-3), backslash-newline inside 'push' and 'alias' reach the classifier (R2-4); v2.1.1: DWIM destinations (heads/main, remotes/<r>/main) protected (F1), pre-filter without here-string + SIGXFSZ ignored so a failed temp file fails closed (F2), quote-aware statements and fail-closed quote repair (QF1), man/less/more/ack no longer treated as text (QF5), one for-each-ref snapshot (A2), refspec-less pushes checked against push.default/branch.<n>.merge/remote.<r>.push and -c overrides (A3), -C/--git-dir/--work-tree/GIT_DIR refspec-less or HEAD pushes blocked (A4), $'..'/$".."/{a,b}/$(..) command words and git-push resolved or blocked (A5); v2.1.0: push detection by command word incl. global options/wrappers, no false positives on quoted/echoed text (SR-B-03/04), Branch-Guard checks destination refs and blocks --all/--mirror/detached pushes (SR-B-02), no SIGPIPE fail-open on large commands (SR-B-21), scoped boundary wording (SR-B-07); v2.0.3: per-statement tag-only push detection with flag allowlist, --no-tags, redirects, line continuations, fail-closed parsing (SR-B-01); v2.0.2: fix pipefail propagation in TEST_CMD subshell (#753)

set -uo pipefail

# Claude Code passes hook context as JSON on stdin.
# Exit 0 = allow, exit 2 = block. On exit 2 only *stderr* is fed back to the
# model as the block reason (see orchestrator-guard.sh header note, issue
# #396) — every message on a blocking path in this script goes to stderr
# (issue #593). stdout is used only for non-blocking progress/status text.

# --- Shared helper lib + fail-closed python check (issue #595) ---------
# For THIS check (dependency availability) the hook acts as a security
# boundary — see .claude/rules/branch-guard.md#guard-terminologie for the
# convention-vs-security-boundary distinction: it must not silently allow a
# push through just because python3 or the helper lib went missing (which
# could be as simple as a broken PATH, or as deliberate as an attacker trying
# to disable the gate). Fail CLOSED instead. Otherwise (Branch-Guard command
# classification, test gate, result cache) the hook is a convention
# boundary: a best-effort token scan, not a shell interpreter — indirection
# such as eval/$(...)-in-quotes/aliases (#592) or a hand-written cache file
# can still get a push past it. Classification doubt fails closed.
# Known alias/config limits (R2-5): only aliases and exec config declared ON
# THE SAME command line are seen. An alias or core.pager/sshCommand/editor
# set in a config file (repo, global, GIT_CONFIG_GLOBAL=<file>,
# include.path) or exported in an earlier statement/call (`git config
# alias.p push` in one call — blocked only if its value names git+push —
# then `git p origin main` in the next) is invisible: the pre-filter never
# sees 'push'. Likewise a script run by `rebase -x`, `bisect run`,
# `submodule foreach`, hooks or a filter whose text does not contain
# 'git ... push' (e.g. `git rebase -x ./deploy.sh`).
# push.recurseSubmodules (#1041) is read from the cwd repository's effective
# config and from -c/--config-env/GIT_CONFIG_* on the command line. The value
# is parsed where the command line carries it (-c/--config, GIT_CONFIG_VALUE_n):
# only on-demand/only recurse, check/no/false stay inert. --config-env names
# the environment variable instead of the value, so it stays value-blind and
# is treated as recursing (fail closed). The config of a FOREIGN repository
# (-C/--git-dir/--work-tree/GIT_DIR) stays unreadable: a cwd-config recursion
# still blocks such a push, but a recursion configured only inside the foreign
# repo is a documented residual gap (do not execute the user's input to find
# it). A configured recursion only matters when the repository declares
# submodules; without .gitmodules the tag-only push stays allowed (#1041).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! source "$SCRIPT_DIR/lib/hook_common.sh" 2>/dev/null; then
  echo "DoD-Check: required helper $SCRIPT_DIR/lib/hook_common.sh is missing or unreadable." >&2
  echo "Failing closed (issue #595) — re-run sync.py to redeploy the hooks/lib/ directory." >&2
  exit 2
fi

# This script (read_config_var, tag-only-push detection below) hardcodes
# the "python3" binary name throughout, unlike hook_common.sh's generic
# python3/python fallback — checked explicitly here rather than via
# hook_have_python so a "python-but-no-python3" system doesn't pass this
# check and then silently fail every later python3 invocation.
if ! command -v python3 >/dev/null 2>&1; then
  echo "DoD-Check: python3 not found on PATH." >&2
  echo "Failing closed (issue #595) — Branch-Guard/test gate cannot be evaluated without it." >&2
  echo "Install python3 or restore PATH to unblock this guard." >&2
  exit 2
fi

# The push-guard helpers live in the shared lib (issue #949, decision D6):
# the protected-branch set and the flag/short-cluster walk. Sourcing an
# older deployed copy (sync not re-run after a hook update) would otherwise
# silently leave this guard without them — fail closed instead.
if ! declare -F hook_protected_branches >/dev/null 2>&1 \
   || ! declare -F hook_push_arg_parser_py >/dev/null 2>&1 \
   || ! declare -F hook_shell_scan_py >/dev/null 2>&1 \
   || ! declare -F hook_json_usable >/dev/null 2>&1 \
   || ! declare -F hook_json_get_many >/dev/null 2>&1; then
  echo "DoD-Check: $SCRIPT_DIR/lib/hook_common.sh is outdated (push-guard helpers missing)." >&2
  echo "Failing closed (issue #949) — re-run sync.py to redeploy the hooks/lib/ directory." >&2
  exit 2
fi

# The extracted readers/classifier/reporter and their shared T23 dependencies
# must be deployed together.  A missing module must not turn a config read into
# an empty value (which could skip the test gate) or silently disable
# classification or message rendering.
for _module in \
  hook_dod_push_payload.py \
  hook_dod_push_config.py \
  hook_dod_push_classify.py \
  hook_dod_push_policy.py \
  hook_dod_push_report.py \
  hook_push_arg_parser.py \
  hook_shell_scan.py; do
  if [ ! -f "$SCRIPT_DIR/lib/$_module" ] || [ ! -r "$SCRIPT_DIR/lib/$_module" ]; then
    echo "DoD-Check: required Python module $_module is missing or unreadable." >&2
    echo "Failing closed (issue #595) — re-run sync.py to redeploy the hooks/lib/ directory." >&2
    exit 2
  fi
done

# The reporter renders every user-visible message and returns the hook action
# as its exit status (see its module docstring); the policy module it imports
# holds the decision rules.
_REPORTER="$SCRIPT_DIR/lib/hook_dod_push_report.py"

# Issue #954: a python3 that exits 0 with garbage (broken PATH shim) would
# otherwise hand garbage back as tool_name/command, and the hook would treat
# the call as "not Bash" and allow it. Verify the interpreter before trusting
# any field.
if ! hook_json_usable; then
  echo "DoD-Check: python3 on PATH does not behave like a Python interpreter." >&2
  echo "Failing closed (issue #954) — the hook payload cannot be read reliably." >&2
  exit 2
fi

# A here-string/here-doc temp file hitting `ulimit -f` must make the
# redirection fail (-> classifier output empty -> block), not kill the hook
# with SIGXFSZ (a non-2 exit status is not a block).
trap '' XFSZ

INPUT=$(cat)
# #1161 Pkt5: ONE interpreter start reads both payload fields. The `ok`
# trailer distinguishes a failed parse/NUL value (rc 1, no output) from a
# missing field, so an unreadable Bash command fails closed here (R2-2).
# bash 3.2 compatible: `read -r -d ''` only, no eval/mapfile/namerefs.
_P_FAIL=0
{
  IFS= read -r -d '' _P_TOOL_NAME || _P_FAIL=1
  IFS= read -r -d '' _P_COMMAND   || _P_FAIL=1
  IFS= read -r -d '' _P_TRAILER   || _P_FAIL=1
} < <(hook_json_get_many "$INPUT" tool_name tool_input.command)
if [ "$_P_FAIL" -ne 0 ] || [ "${_P_TRAILER:-}" != "ok" ]; then
  echo "Branch-Guard: Push blocked — the hook payload could not be read (fail closed)." >&2
  echo "Re-issue the command; if it contains unusual bytes (NUL), remove them." >&2
  exit 2
fi
TOOL_NAME="$_P_TOOL_NAME"
COMMAND="$_P_COMMAND"

# R2-2: an empty COMMAND must mean "no command", never "could not extract
# it" (unparseable payload, non-string command, a helper failure): a Bash
# (or unidentifiable) call whose payload holds a non-empty command that did
# not reach us is blocked. An empty command of a non-Bash tool stays allowed.
if [ -z "$COMMAND" ] && { [ -z "$TOOL_NAME" ] || [ "$TOOL_NAME" = "Bash" ]; }; then
  _PAYLOAD_STATE=$(printf '%s' "$INPUT" | python3 "$SCRIPT_DIR/lib/hook_dod_push_payload.py" 2>/dev/null)
  if [ "$_PAYLOAD_STATE" != "empty" ]; then
    echo "Branch-Guard: Push blocked — the Bash command could not be read from the hook payload (fail closed)." >&2
    echo "Re-issue the command; if it contains unusual bytes (lone surrogates, invalid UTF-8), remove them." >&2
    exit 2
  fi
fi

# Only intercept Bash tool calls (and calls whose tool is unidentifiable)
[ "$TOOL_NAME" = "Bash" ] || [ -z "$TOOL_NAME" ] || exit 0

# Cheap pre-filter: a push needs the word 'push' somewhere (quotes/backslashes/
# '$' and backslash-newline between the letters tolerated, e.g. pu''sh,
# pu$'s'h, pu\<newline>sh) or ANSI-C quoting ($'\x70ush' can spell
# anything) or a git alias declared on the command line ('-c alias.p=push p',
# '--config-env=alias.p=VAR p', any case). The precise per-statement
# classification below decides; this only skips the python startup for the
# common case. Pure bash: no fork, no pipe (SIGPIPE under pipefail,
# SR-B-21) and no here-string temp file (a failed redirection returned rc 1
# = "no match").
_Q="[\"'\\\\\$"$'\n'"]*"
_PUSH_RE="p${_Q}u${_Q}s${_Q}h|[\$]'|[Aa]${_Q}[Ll]${_Q}[Ii]${_Q}[Aa]${_Q}[Ss]"
# Only rc 1 (no match) skips; a regex error (rc 2) falls through (fail closed).
[[ $COMMAND =~ $_PUSH_RE ]]
[ $? -eq 1 ] && exit 0

# --- Resolve project config file ---
# Config layout since agent-meta v0.26+: .meta-config/project.yaml (YAML).
# Legacy fallback: agent-meta.config.json at the project root (pre-0.26).
# Walk up the directory tree until a config is found.
CONFIG_FILE=""
DIR="$PWD"
for _ in 1 2 3 4 5 6; do
  if [ -f "$DIR/.meta-config/project.yaml" ]; then
    CONFIG_FILE="$DIR/.meta-config/project.yaml"
    break
  fi
  if [ -f "$DIR/agent-meta.config.json" ]; then
    CONFIG_FILE="$DIR/agent-meta.config.json"
    break
  fi
  [ "$DIR" = "/" ] && break
  DIR="$(dirname "$DIR")"
done

# read_config_var <config_file> <variable_name>
# Reads variables.<name> from a project config. Supports YAML (project.yaml)
# and legacy JSON (agent-meta.config.json). Prefers PyYAML, falls back to a
# stdlib-only scan of the top-level `variables:` block so the hook never needs
# a third-party dependency in the target project.
read_config_var() {
  python3 "$SCRIPT_DIR/lib/hook_dod_push_config.py" "$1" "$2" 2>/dev/null
}

# --- Tag-only push detection ---
# A tag push (`git push origin v1.2.3`, `git push origin --tags`,
# `git push origin tag v1.2.3`, `git push origin refs/tags/v1.2.3`) does not
# touch any branch ref — it cannot add commits to main/master, which is the
# entire premise the Branch-Guard below exists to prevent. Without this
# check, cutting a release while sitting on main (the normal place to be
# right after a release PR merges) was blocked identically to an actual
# direct push of main's commit history, even though the two are unrelated
# in risk. Not a full shell parser (matches this repo's other hooks'
# documented approach) — covers the realistic `git push <remote> <ref>` /
# `--tags` / `tag <name>` forms; anything else (bare `git push`, `git push
# origin`, an explicit branch ref) still falls through to the branch check.
#
# SR-B-01: classification is per `git push` STATEMENT (split on shell control
# operators, same splitter as orchestrator-guard-impl.sh `statements()`), and
# every ref of every push statement must be a tag ref. The whole command is
# tag-only only if it has >=1 push statement and ALL of them are tag-only —
# `git push origin main --tags` or `git push --tags && git push origin main`
# must still hit the Branch-Guard. Any parse doubt -> not tag-only.
#
# SR-B-03/SR-B-04: a statement is a push only if its COMMAND WORD resolves to
# git with subcommand `push` after git's global options (`git -C . push`,
# `/usr/bin/git push`, `(git push ...)`, `VAR=1 git push`), or if an
# exec-capable wrapper/unknown command carries a `git [opts] push` in its args
# (`sudo git push`, `env X=1 git push`, `timeout 60 git push` — fail closed).
# Commands that never execute their arguments (`echo`, `grep`, `gh`, ...) are
# not pushes even if their text contains "git push".
#
# SR-B-02: the Branch-Guard also checks every DESTINATION ref of each non-tag
# push statement (`HEAD:main`, `feat:main`, `+feat:refs/heads/main`, `:main`,
# `--delete main`, `origin/main`, `heads/main` (git DWIM), `--force-with-lease=main`).
# Bulk/ambiguous pushes (`--all`, `--branches`, `--mirror`, wildcard or `:`
# refspecs, unknown/abbreviated push options) and refspec-less pushes from a
# detached HEAD or in an unresolvable repository (`--git-dir`, `GIT_DIR=`, or a
# `-C`/leading `cd` target that is computed, missing, not a repo or detached)
# are blocked because the destination cannot be determined safely. A literal
# `-C` chain / leading `cd` is judged by that directory's own HEAD. A refspec-less
# push (and a ref without destination) is also judged by the config that
# routes it: push.default=matching, branch.<n>.merge, remote.<r>.push, and
# `-c`/GIT_CONFIG* overrides of those on the command line.
#
# Classifier output (one line): none | tag | push | block <reason>.
# Anything else (python crash, empty output) blocks (fail closed). The
# command is passed on stdin (here-string): argv/env cap a single string at
# 128 KB (E2BIG) and a pipe writer can die from SIGPIPE (SR-B-21).

# Resolve GIT_MAIN_BRANCH: env var > project config > default "main"
MAIN_BRANCH="${AGENT_META_MAIN_BRANCH:-}"
if [ -z "$MAIN_BRANCH" ] && [ -n "$CONFIG_FILE" ]; then
  MAIN_BRANCH=$(read_config_var "$CONFIG_FILE" "GIT_MAIN_BRANCH")  # runtime-reader:variables.GIT_MAIN_BRANCH
fi
MAIN_BRANCH="${MAIN_BRANCH:-main}"

# Full ref (not --abbrev-ref, which shortens to 'heads/main' when a tag of
# the same name exists); empty = detached HEAD or not inside a repo.
CURRENT_REF=$(git symbolic-ref -q HEAD 2>/dev/null)
CURRENT_BRANCH="${CURRENT_REF#refs/heads/}"

# R2-3: hard time budget. The classifier is linear (~1.5 s per MB), but a
# hook that runs into the harness timeout is a non-blocking error (= allow):
# past CLASSIFY_BUDGET seconds it is killed, its output is empty -> block.
CLASSIFY_BUDGET=20
_BUDGET=()
command -v timeout >/dev/null 2>&1 && _BUDGET=(timeout -k 2 "$CLASSIFY_BUDGET")
# Protected set: main + master + the configured main branch, from one helper
# (issue #949, #1033). Passed to the classifier (space-separated; ref names
# cannot contain whitespace) AND to the block message (comma-separated, same
# substitution as before), so the classifier and the message can never
# disagree.
PROTECTED_LIST=$(hook_protected_branches "$MAIN_BRANCH")
# The deployed classifier imports the shared T23 argument walk and shell
# scanner.  Its three shared-walk consumers are documented here because the
# implementation moved out of this hook:
# walk_push_args( — tag-only classification.
# walk_push_args( — destination validation.
# walk_push_args( — config-recursion checks.
# It receives the command on stdin (here-string, like the former fd 3)
# and keeps the hard time budget: timeout -> empty output -> fail closed.
PUSH_CLASS=$(${_BUDGET[@]+"${_BUDGET[@]}"} python3 \
  "$SCRIPT_DIR/lib/hook_dod_push_classify.py" \
  "$MAIN_BRANCH" "$CURRENT_BRANCH" "$PROTECTED_LIST" \
  0<<<"$COMMAND" 2>/dev/null
)
_CLASS_RC=$?

# Branch-Guard verdict: the reporter maps the classifier line to the hook
# action and renders the block reason (on stderr, issue #593). Its exit
# status is an internal protocol with this shell, not the hook's status:
#   0 = tag-only or plain push -> run the test gate below
#   3 = not a push at all       -> allow
#   2 = blocked                  -> the reason is already on stderr
# Any other status (crash) is a broken deployment and blocks.
python3 "$_REPORTER" branch \
  "$_CLASS_RC" "$CLASSIFY_BUDGET" "$MAIN_BRANCH" "${PROTECTED_LIST// /, }" \
  0<<<"$PUSH_CLASS"
_VERDICT_RC=$?
case "$_VERDICT_RC" in
  0) : ;;
  3) exit 0 ;;
  2) exit 2 ;;
  *)
    echo "DoD-Check: Branch-Guard verdict reporter failed (fail closed)." >&2
    exit 2
    ;;
esac

# --- Test-Gate: block push if tests fail ---
# Resolve TEST_COMMAND: env var > project config
TEST_CMD="${AGENT_META_TEST_COMMAND:-}"

if [ -z "$TEST_CMD" ] && [ -n "$CONFIG_FILE" ]; then
  TEST_CMD=$(read_config_var "$CONFIG_FILE" "TEST_COMMAND")  # runtime-reader:variables.TEST_COMMAND
fi

# --- Result cache keyed by commit SHA (issue #594) ----------------------
# A full test suite run inline on every single `git push` can block for
# minutes with no cap, even when nothing test-relevant changed since the
# last push of the exact same tree (e.g. re-pushing after a rejected push,
# or pushing the same commit to a second remote). Cache the last PASSING
# (HEAD sha, TEST_CMD) pair per-repo under .git/ (never synced, never
# committed) and skip straight to "allow" on a cache hit. Any change to
# either the commit or the configured TEST_CMD invalidates the cache.
# The reporter reads the file and applies the key rule (hook_dod_push_policy
# cache_matches); this shell only resolves the paths.
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null || echo "")
HEAD_SHA=$(git rev-parse HEAD 2>/dev/null || echo "")
CACHE_FILE=""
if [ -n "$GIT_DIR" ] && [ -n "$HEAD_SHA" ]; then
  CACHE_FILE="$GIT_DIR/agent-meta-dod-push-check-cache"
fi

# --- Timeout (issue #594) ------------------------------------------------
# Resolve TEST_TIMEOUT (seconds): env var > project config > default 300s.
TEST_TIMEOUT="${AGENT_META_TEST_TIMEOUT:-}"
if [ -z "$TEST_TIMEOUT" ] && [ -n "$CONFIG_FILE" ]; then
  TEST_TIMEOUT=$(read_config_var "$CONFIG_FILE" "TEST_TIMEOUT")  # runtime-reader:variables.TEST_TIMEOUT
fi
TEST_TIMEOUT="${TEST_TIMEOUT:-300}"

_HAS_TIMEOUT=0
command -v timeout >/dev/null 2>&1 && _HAS_TIMEOUT=1

# Test-gate state, cache key and the "Running ..." announcement are rendered
# by the reporter. Its exit status is the internal protocol:
#   0 = run the tests now    3 = allow, no config found
#   4 = allow, no TEST_COMMAND     5 = allow, cached pass for this commit
# Anything else (crash) is a broken deployment and blocks.
python3 "$_REPORTER" gate \
  "$CONFIG_FILE" "$TEST_CMD" "$CACHE_FILE" "$HEAD_SHA" \
  "$TEST_TIMEOUT" "$_HAS_TIMEOUT"
_GATE_RC=$?
case "$_GATE_RC" in
  0) : ;;
  3|4|5) exit 0 ;;
  *)
    echo "DoD-Check: test-gate reporter failed (fail closed)." >&2
    exit 2
    ;;
esac

_TEST_RC=0
if [ "$_HAS_TIMEOUT" -eq 1 ]; then
  # Note: TEST_CMD executed via bash -c (no eval) — value from project.yaml
  # Issue #753: inject set -uo pipefail so pipeline exit codes are not masked
  timeout "${TEST_TIMEOUT}s" bash -c "set -uo pipefail; $TEST_CMD" 2>&1 || _TEST_RC=$?
else
  bash -c "set -uo pipefail; $TEST_CMD" 2>&1 || _TEST_RC=$?
fi

# Pass/fail/timeout message: the reporter blocks (exit 2) on a failing or
# timed-out run; any other non-zero status is a broken deployment and blocks
# as well (the tests passed, but the gate cannot report them).
python3 "$_REPORTER" result "$_TEST_RC" "$TEST_TIMEOUT" "$_HAS_TIMEOUT" "$TEST_CMD"
_RESULT_RC=$?
[ "$_RESULT_RC" -eq 0 ] || exit 2

if [ -n "$CACHE_FILE" ]; then
  mkdir -p "$(dirname "$CACHE_FILE")" 2>/dev/null || true
  printf '%s\n%s' "$HEAD_SHA" "$TEST_CMD" > "$CACHE_FILE" 2>/dev/null || true
fi

exit 0
