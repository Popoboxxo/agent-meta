#!/bin/bash
# hook: sync-on-config-change
# version: 1.3.0
# event: PostToolUse
# matcher: Write|Edit
# protocol: tool-hook-v1
# description: Re-run scripts/sync.py when .meta-config/project.yaml changes
# changelog: v1.3.0: MB-3 review fix (F1/F9, docs/plans/systemaudit-umsetzungsplan-2026-11-25.md) -- the sync.py lookup also accepts the documented submodule checkout at <project>/external/agent-meta (after <project>/.agent-meta, still cwd-independent), so a project that vendors agent-meta there syncs instead of silently skipping; the deployment-layout root is computed once and shared by the root fallback and the sync.py lookup (behaviour-neutral). v1.2.0: MB-3 -- the hook runs the project's real scripts/sync.py (subprocess with a hard timeout) instead of queueing a lifecycle task, so the hook name and its effect match. sync.py is located cwd-independently: explicit SOC_AGENT_META_ROOT override, else <project>/.agent-meta (submodule deployment), else the hook's deployment layout when that layout IS the project (agent-meta self-hosting). The project root comes from adapter-owned AM_PROJECT_DIR, else a payload-cwd walk-up (nested .agent-meta checkouts skipped, kept only as fallback), else the deployment layout. A successful-tool-result gate (tool_result.exit_code / tool_result.is_error; absent fields keep the old fail-open reading) and a SOC_SYNC_ON_CONFIG_CHANGE=1 child marker that stops the hook from feeding back into itself. Unchanged: the single-pass payload parse, the Write|Edit-only and config-path-only filtering, and the fail-open policy (always exit 0).
# enabled_by_default: false

set -uo pipefail

# Claude Code passes the PostToolUse context as JSON on stdin. This hook is a
# post-write automation, NOT a gate: it always exits 0 and never blocks or
# fails the (already-completed) write call.
#
# Not a security boundary — fails OPEN (exit 0) if the shared helper lib, a
# python interpreter, a runnable sync.py, or the project config is unavailable
# (issue #595 only hardens the hooks that are actual security controls:
# orchestrator-guard.sh and dod-push-check.sh).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/hook_common.sh" 2>/dev/null || exit 0
hook_have_python || exit 0
declare -F hook_json_get_many >/dev/null 2>&1 || exit 0

# Recursion brake: sync.py is started with this marker exported, so a sync
# that transitively reaches this hook again returns before spawning another
# sync. The hook can only fire on tool calls and a subprocess write is not a
# tool call, so this is defense in depth, not the primary guard.
if [ "${SOC_SYNC_ON_CONFIG_CHANGE:-}" = "1" ]; then
  exit 0
fi

INPUT=$(cat)
# ONE interpreter start reads all fields (issue #1161 Pkt5). This hook is
# informational and fails OPEN, so a failed parse (rc 1, no output) simply
# skips the re-sync. bash 3.2: `read -r -d ''`, no eval/mapfile.
_P_FAIL=0
{
  IFS= read -r -d '' _P_TOOL_NAME || _P_FAIL=1
  IFS= read -r -d '' _P_FILE_PATH || _P_FAIL=1
  IFS= read -r -d '' _P_EXIT_CODE || _P_FAIL=1
  IFS= read -r -d '' _P_IS_ERROR  || _P_FAIL=1
  IFS= read -r -d '' _P_CWD       || _P_FAIL=1
  IFS= read -r -d '' _P_TRAILER   || _P_FAIL=1
} < <(hook_json_get_many "$INPUT" tool_name tool_input.file_path \
      tool_result.exit_code tool_result.is_error cwd)
if [ "$_P_FAIL" -ne 0 ] || [ "${_P_TRAILER:-}" != "ok" ]; then
  exit 0
fi
TOOL_NAME="$_P_TOOL_NAME"
FILE_PATH="$_P_FILE_PATH"

# Only intercept file-writing tools
[ "$TOOL_NAME" = "Write" ] || [ "$TOOL_NAME" = "Edit" ] || exit 0

# Only intercept SUCCESSFUL writes. hook_json_get_many has no default, so an
# absent field is empty: a provider that reports no result keeps the previous
# fail-open reading instead of being treated as a failure.
case "${_P_EXIT_CODE:-}" in
  ""|0) ;;
  *) exit 0 ;;
esac
case "${_P_IS_ERROR:-}" in
  ""|0|false|False) ;;
  *) exit 0 ;;
esac

# Only fire when the edited file is the project config
case "$FILE_PATH" in
  *.meta-config/project.yaml) ;;
  *) exit 0 ;;
esac

# --- Project root ---------------------------------------------------------
# Thin wrapper: a deployed lib older than hook_common 1.12.0 has no
# hook_is_meta_submodule_dir; treat that as "not a meta submodule" instead of
# letting a missing function abort the walk.
_is_meta_submodule() {
  declare -F hook_is_meta_submodule_dir >/dev/null 2>&1 || return 1
  hook_is_meta_submodule_dir "$1"
}

# Root order:
# 1) adapter-owned AM_PROJECT_DIR when it carries .meta-config/,
# 2) else the nearest ancestor of the payload cwd that carries .meta-config/,
#    skipping nested .agent-meta / external/agent-meta checkouts (they carry
#    their own .meta-config/ and would otherwise outrank the session project;
#    a walk that only finds such a checkout keeps it as fallback),
# 3) else the deployment layout: the hook lives at <root>/hooks/1-generic or
#    at <root>/.claude/hooks, both two levels below the project root.
# The deployment root is needed twice (root fallback here, sync.py lookup
# below): one computation keeps the two candidates identical.
_DEPLOY_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
ROOT=""
if [ -n "${AM_PROJECT_DIR:-}" ] && [ -d "$AM_PROJECT_DIR/.meta-config" ]; then
  ROOT="$AM_PROJECT_DIR"
else
  _META_FALLBACK=""
  case "${_P_CWD:-}" in
    /*)
      _DIR="$_P_CWD"
      while [ -n "$_DIR" ] && [ "$_DIR" != "/" ]; do
        if [ -d "$_DIR/.meta-config" ]; then
          if _is_meta_submodule "$_DIR"; then
            [ -n "$_META_FALLBACK" ] || _META_FALLBACK="$_DIR"
          else
            ROOT="$_DIR"
            break
          fi
        fi
        _DIR="$(dirname "$_DIR")"
      done
      ;;
  esac
  [ -n "$ROOT" ] || ROOT="$_META_FALLBACK"
fi
if [ -z "$ROOT" ]; then
  if [ -d "$_DEPLOY_ROOT/.meta-config" ]; then
    ROOT="$_DEPLOY_ROOT"
  fi
fi
[ -n "$ROOT" ] || exit 0
# The hook only makes sense for a project that carries the config it reacts to.
[ -f "$ROOT/.meta-config/project.yaml" ] || exit 0

# --- Locate sync.py -------------------------------------------------------
# Order: explicit override (tests/CI) → the project's .agent-meta submodule →
# the project's external/agent-meta checkout (the other documented submodule
# location) → the deployment layout, but only when that layout IS the project
# (agent-meta self-hosting). A deployed hook must never borrow a sync.py from
# an unrelated enclosing tree, so both submodule candidates are anchored at the
# resolved project root and stay independent of the hook's process cwd.
_has_sync() { [ -f "$1/scripts/sync.py" ]; }

AM_ROOT=""
if [ -n "${SOC_AGENT_META_ROOT:-}" ] && _has_sync "$SOC_AGENT_META_ROOT"; then
  AM_ROOT="$SOC_AGENT_META_ROOT"
elif _has_sync "$ROOT/.agent-meta"; then
  AM_ROOT="$ROOT/.agent-meta"
elif _has_sync "$ROOT/external/agent-meta"; then
  AM_ROOT="$ROOT/external/agent-meta"
elif _has_sync "$_DEPLOY_ROOT" && [ "$_DEPLOY_ROOT" = "$ROOT" ]; then
  AM_ROOT="$ROOT"
fi
[ -n "$AM_ROOT" ] || exit 0
SYNC_PY="$AM_ROOT/scripts/sync.py"

_PY="$(hook_python_bin)"
[ -n "$_PY" ] || exit 0

# Hard upper bound for the child. `timeout` when available (coreutils), else
# the same bound with a plain bash watcher (macOS ships no `timeout`). Default
# 60 s: the hook runs inside the post-write latency budget of one tool call.
TIMEOUT_SECS="${SOC_SYNC_TIMEOUT:-60}"
case "$TIMEOUT_SECS" in
  ''|*[!0-9]*) TIMEOUT_SECS=60 ;;
esac
[ "$TIMEOUT_SECS" -gt 0 ] || TIMEOUT_SECS=60

run_with_timeout() {
  local secs="$1"
  shift
  if command -v timeout >/dev/null 2>&1; then
    timeout "$secs" "$@"
    return $?
  fi
  "$@" &
  local cmd_pid=$!
  ( sleep "$secs"; kill -TERM "$cmd_pid" 2>/dev/null ) >/dev/null 2>&1 &
  local watcher_pid=$!
  wait "$cmd_pid"
  local rc=$?
  kill "$watcher_pid" 2>/dev/null
  wait "$watcher_pid" 2>/dev/null
  return $rc
}

# Subshell: the `cd` must not leak into the hook's own process. sync.py gets
# the config path explicitly (an absolute path also keeps it away from the
# interactive setup wizard, which a bare `sync.py` would start when its cwd has
# no config), while the cwd is still set to the project root so every relative
# path sync.py resolves (config lookup, .agent-meta submodule, tmp-sink)
# points at the same project.
(
  cd "$ROOT" || exit 1
  export AM_PROJECT_DIR="$ROOT"
  export SOC_SYNC_ON_CONFIG_CHANGE=1
  run_with_timeout "$TIMEOUT_SECS" "$_PY" "$SYNC_PY" \
    --config "$ROOT/.meta-config/project.yaml"
) >/dev/null 2>&1 </dev/null
_RC=$?

if [ "$_RC" -ne 0 ]; then
  echo "sync-on-config-change: scripts/sync.py did not finish (rc=$_RC);" \
       ".meta-config/project.yaml is changed but not synced — run 'python3 scripts/sync.py' manually" >&2
fi

exit 0
