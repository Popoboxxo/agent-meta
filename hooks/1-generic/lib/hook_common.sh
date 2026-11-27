#!/bin/bash
# lib: hook_common
# version: 1.13.0
# description: Shared helper functions sourced by other hook scripts (issue #601 dedup)
# changelog: v1.13.0: issue #1263b -- hook fallback for providers without the native `supports-permission-deny` capability: hook_mcp_tool_denied consults the synced <lib>/mcp-deny.json deny manifest (same source as permissions.deny) and the mcp__<server>__<tool> branch of hook_known_tool_name refuses a listed tool with a clear stderr reason, so the two fail-closed guards block it with exit 2; missing/empty manifest fails open (convention boundary), no python required and no provider name consulted; v1.12.0: issue #1238a -- move the three executable Python heredocs into flat hook_shell_scan.py, hook_shell_resolver.py and hook_push_arg_parser.py modules; shell emitters keep byte-identical source output and fail closed when Python or a deployed module is unavailable; v1.11.0: issue #1251 -- expose and export exactly AM_PROJECT_DIR as the adapter-owned project anchor; no root resolution or provider-specific fallback in this library; v1.10.0: issues #1169/#1238 -- hook_json_get_many reads several payload fields in ONE interpreter start via the importable hook_json_many.py module (NUL-terminated fields + `ok` trailer; parse errors and NUL in a requested value fail the whole call); v1.9.0: issue #1151 (audit G1) -- hook_known_tool_name matches the documented tools table (adds EndConversation, ListAgents, ListMcpResourcesTool, LSP, PowerShell, ReadMcpResourceTool, ReportFindings, SendFeedback, ShareOnboardingGuide, WaitForMcpServers, Workflow; F6-02); hook_shell_scan_py emits the body of every $(...)/backtick substitution outside single quotes -- double-quoted ones included -- as extra statements (command_substitutions, nesting capped at 32 and failing closed beyond, F6-03) and offers split_shell_statements_with_ops (the operator that ended each statement, for cd tracking, F6-07); v1.8.1: hook_known_tool_name also knows SubagentHandback (subagent report channel; blocking it lost every subagent result); v1.8.0: hook_known_tool_name also knows ToolSearch and the other current built-ins (ToolSearch, TaskCreate, TaskUpdate, TaskList, TaskGet, Monitor, ScheduleWakeup, CronCreate, CronDelete, CronList, EnterPlanMode, PushNotification, RemoteTrigger, SendUserFile, Artifact, ArtifactComments, ArtifactData) — the closed allow-list blocked the whole task/cron/artifact surface, #1078; EnterWorktree/ExitWorktree stay blocked on purpose; v1.7.0: hook_shell_scan_py — is_fork_bomb ends a function body at the depth-matching '}' inside the 512-character window instead of the first unquoted one, so bombs with a brace or ${...} before the self-call are detected (#1050); an exhausted window still fails closed; v1.6.0: hook_known_tool_name knows Agent, SendMessage and the other current built-ins (Agent replaced Task, so the closed allow-list blocked all delegation); EnterWorktree/ExitWorktree stay blocked on purpose (no-worktree-isolation); v1.5.0: hook_shell_scan_py — the fork-bomb detector reads a function name exactly at any length (the 64-character cap is gone; the reverse scans of two '()' pairs cannot overlap, so it stays linear) and fails closed when a body has no unquoted '}' in its first 512 characters, blocking the candidate instead of skipping it (deliberate false-alarm class: long inline function bodies); the body still ends at the first unquoted '}' without brace nesting — known gap, documented in `rules/1-generic/branch-guard.md` (#943 follow-up); v1.4.0: hook_shell_resolver_py — one command-word resolver (wrapper grammar with positional arity, transparent '--', `case … in` arms, function bodies, subshells/groups, leading keywords) shared by the fail-closed guards instead of a per-hook copy; repo-containment-impl.sh uses it so its write-target detector resolves the same command word orchestrator-guard-impl.sh does (its inline copy is unchanged here, see the emitter's adoption note); v1.3.1: hook_shell_scan_py now keeps its quote state in sync for ANSI-C ($'...') and locale ($"...") quoting (review finding F1), stops tracking a heredoc delimiter it cannot resolve so the body is over-scanned instead of hiding the rest of the command (F2, deliberate divergence from bash: bash does not expand the delimiter either, but an unknown delimiter must not license skipping input), and cuts a trailing '#' comment from the cleaned code as well as from the statement stream (F4); v1.3.0: hook_shell_scan_py — one quote/heredoc-aware shell statement splitter plus the linear-time fork-bomb detector, shared by both fail-closed guards (#943 (a)/(c)/(j), #944 SR-B-16); hook_is_meta_submodule_dir — the project-root walk-ups skip a nested .agent-meta checkout's own .meta-config/ when an enclosing project has one (#943 (l)); v1.2.0: hook_known_tool_name is the single allow-list both fail-closed guards use before classifying a payload — an empty, non-string or unrecognized tool_name now blocks instead of falling through their `*) exit 0` allow branch (review finding M2, #954 follow-up), and the header names the three guards that source this lib and verify the interpreter; v1.1.0: hook_protected_branches + hook_push_arg_parser_py — the protected-branch set and the git-push flag/short-cluster walk of dod-push-check.sh live here once instead of being built twice (#949), hook_json_usable detects an interpreter that exits 0 with garbage, exits non-zero or is missing — the probe sentinel now lives in the payload and its fallback default is distinct, so a failing interpreter can no longer look usable (#954); v1.0.1: hook_json_get no longer returns "" for a present field whose value holds a lone surrogate or whose payload holds invalid UTF-8 (W2-B1 R2-2)
#
# NOT a hook itself — no `event`/`matcher` header, sync.py never registers it
# in settings.json. Deployed verbatim to <hooks_dir>/lib/hook_common.sh
# alongside the hook scripts that source it
# (scripts/lib/hooks.py::sync_hook_lib()). Every hook that sources this file
# does so via a path relative to its own location:
#
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   source "$SCRIPT_DIR/lib/hook_common.sh"
#
# Security-boundary hooks (orchestrator-guard-impl.sh,
# repo-containment-impl.sh, dod-push-check.sh) treat a failed `source` (this
# file missing/unreadable) as fail-closed, not fail-open — see the sourcing
# snippet at the top of each of those scripts. All three additionally call
# hook_json_usable() before trusting any field, so a python3/python that is
# missing, exits non-zero or exits 0 while printing garbage also fails closed.
# Non-security hooks may fail open on a missing lib, matching their prior
# fail-open behavior on a missing python3 (issue #595 only hardens the hooks
# that are actual security controls, not every hook that happens to use
# python3).
#
# Every function here is stdlib-only (python3/python, common POSIX
# utilities) — no new external dependency for consumer projects.

# --- Adapter-owned project directory --------------------------------------

# Provider adapters set AM_PROJECT_DIR before invoking a hook. This library
# only makes that single contract variable available to child processes; it
# never derives a root from the payload, cwd or a provider-specific variable.
AM_PROJECT_DIR="${AM_PROJECT_DIR:-}"
export AM_PROJECT_DIR

# --- Python interpreter resolution -------------------------------------

# hook_have_python: return code 0 if "python3" or "python" is on PATH.
hook_have_python() {
  command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1
}

# hook_python_bin: prints "python3" or "python" (whichever is found first),
# prints nothing if neither is available. Callers that must fail closed on a
# missing interpreter (issue #595) check hook_have_python explicitly BEFORE
# relying on this — an empty result here must never be silently treated as
# "allow", the call site decides.
hook_python_bin() {
  if command -v python3 >/dev/null 2>&1; then
    printf '%s' "python3"
  elif command -v python >/dev/null 2>&1; then
    printf '%s' "python"
  fi
}

# --- JSON field extraction ----------------------------------------------

# hook_json_get <json-string> <dotted.path> [default]
# Extracts a nested scalar field from a JSON object via a dotted path
# (e.g. "tool_input.command"). Prints <default> ("" if omitted) when the
# path does not resolve, the value is an object/array, or the JSON itself
# fails to parse. Never raises — always safe to use in a guard's hot path.
#
# Replaces the near-identical
#   read -r -d '' _PARSE <<'PYEOF' ... python3 -c "$_PARSE" ... | head -N
# pattern that used to be copy-pasted across dod-push-check.sh,
# lifecycle-check.sh, sync-on-config-change.sh and orchestrator-guard.sh
# (issue #601).
hook_json_get() {
  local json="$1" path="$2" default="${3:-}"
  local py
  py="$(hook_python_bin)"
  if [ -z "$py" ]; then
    printf '%s' "$default"
    return 0
  fi
  # Bytes in, bytes out (W2-B1 R2-2): invalid UTF-8 in the payload and a
  # lone surrogate escape ("\ud800") in a value used to make the decode or
  # print() raise under a strict UTF-8 locale, so a present field came back
  # as "" (a guard then saw no command at all). Undecodable input bytes are
  # passed through as-is (surrogateescape), lone surrogates are written as
  # their raw 3-byte encoding (surrogatepass) -- never dropped.
  printf '%s' "$json" | "$py" -c "
import json, sys

path, default = sys.argv[1], sys.argv[2]


def emit(text):
    try:
        data = text.encode('utf-8', 'surrogateescape')
    except UnicodeEncodeError:
        data = text.encode('utf-8', 'surrogatepass')
    sys.stdout.buffer.write(data + b'\n')


try:
    d = json.loads(sys.stdin.buffer.read().decode('utf-8', 'surrogateescape'))
except Exception:
    emit(default)
    sys.exit(0)

cur = d
for key in path.split('.'):
    if isinstance(cur, dict):
        cur = cur.get(key)
    else:
        cur = None
        break

if cur is None or isinstance(cur, (dict, list)):
    emit(default)
else:
    emit(str(cur))
" "$path" "$default" 2>/dev/null || printf '%s' "$default"
}

# hook_json_get_many <json-string> <dotted.path>...
# Read EVERY requested field in a SINGLE interpreter start (issue #1169).
# The Python core lives in hook_json_many.py next to this file (#1238): this
# function is only a thin shim and keeps the shared hook_python_bin resolution.
# stdout: one NUL-terminated field per path in argument order, then an `ok`
# trailer; rc 1 and NO output on a parse error or a NUL inside a requested
# value, so the caller can tell "no JSON" from "field missing" and fail closed.
# No `eval`/`mapfile`/namerefs: bash 3.2 consumes the fields with
# `IFS= read -r -d ''` in the caller (SPEC-HOOK-SINGLE-PARSE §2.2).
hook_json_get_many() {
  local json="$1" py module_dir
  shift
  py="$(hook_python_bin)"
  if [ -z "$py" ] || [ "$#" -eq 0 ]; then
    return 1
  fi
  module_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  printf '%s' "$json" | "$py" "$module_dir/hook_json_many.py" "$@" 2>/dev/null
}

# hook_json_usable
# Returns 0 only when hook_json_get round-trips a sentinel through a real
# JSON parse. A python3/python on PATH that EXITS 0 but prints garbage (a
# broken or hostile PATH shim) cannot be told apart from a working
# interpreter by exit status alone: hook_json_get would hand its garbage
# back as the field value, and a security hook that treats "no command" as
# "allow" would then let a push through (issue #954). Security hooks call
# this once before trusting any field and fail closed on a non-zero result
# (orchestrator-guard-impl.sh, repo-containment-impl.sh, dod-push-check.sh).
#
# The sentinel travels in the PAYLOAD and the fallback default is a DISTINCT
# value (#954 follow-up): with the sentinel as the default, an interpreter
# that fails (exit 1, no output -> hook_json_get's `|| printf default` or its
# missing-interpreter branch) printed the sentinel and looked usable. Now only
# a real parse of a real payload can produce it — a failing interpreter yields
# 'hook-json-bad', a garbage one its own output, both != sentinel.
hook_json_usable() {
  [ "$(hook_json_get '{"__hook_json_probe__": "hook-json-ok"}' \
        '__hook_json_probe__' 'hook-json-bad')" = "hook-json-ok" ]
}

# hook_mcp_deny_manifest_path
# Prints the absolute path of the hook deny manifest. sync_mcp_deny() writes
# it to <hooks_dir>/lib/mcp-deny.json, i.e. right next to this file, for
# providers WITHOUT the native `supports-permission-deny` capability
# (scripts/lib/mcp_deny.py, issue #1263b). Resolving it from this file's own
# location keeps the lookup provider-agnostic: no project-root walk-up, no
# provider name, no payload field.
hook_mcp_deny_manifest_path() {
  local module_dir
  module_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  printf '%s/%s' "$module_dir" "mcp-deny.json"
}

# hook_mcp_tool_denied <tool_name>
# Returns 0 (DENIED) when <tool_name> is listed in the synced deny manifest,
# 1 otherwise. Both surfaces — native `permissions.deny` and this manifest —
# are fed by lib/mcp_deny.py::build_mcp_deny_rules from ONE source
# (config/plugin-catalog.yaml `tools.blocked`), so the hook is a transport,
# never a second deny list.
#
# Match semantics: the EXACT quoted `mcp__<server>__<tool>` token, so
# `mcp__srv__read` never matches `mcp__srv__read_secret`. Only the
# `mcp__<server>__<tool>` namespace is looked at; built-ins are untouched.
#
# Fail-open by design (convention boundary, NOT a security boundary): a
# missing, unreadable or empty manifest (no blocked tools) allows the call.
# No python interpreter is required and no provider name is consulted. The
# reason goes to stderr because only stderr reaches the model on exit 2.
hook_mcp_tool_denied() {
  local tool="${1:-}" manifest
  case "$tool" in
    mcp__?*__?*) ;;
    *) return 1 ;;
  esac
  manifest="$(hook_mcp_deny_manifest_path)"
  [ -r "$manifest" ] || return 1
  grep -qF "\"$tool\"" "$manifest" 2>/dev/null || return 1
  printf '%s\n' \
    "MCP_GUARD: '$tool' is on the blocked MCP tool list (config/plugin-catalog.yaml tools.blocked, issue #1263)." \
    "Call refused by the hook fallback for providers without native permission deny." >&2
  return 0
}

# hook_known_tool_name <tool_name>
# Returns 0 when <tool_name> is a tool name the framework's hook contract
# knows, 1 for anything else (including the empty string). Single source of
# truth for the two fail-closed guards (orchestrator-guard-impl.sh,
# repo-containment-impl.sh): both used to let a tool_name they did not
# recognize fall through `case "$TOOL_NAME" in Write|Edit|Bash) ;; *) exit 0`
# — i.e. an unknown value (a broken interpreter's junk before issue #954, a
# non-string or misspelled field today) silently ALLOWED the call (review
# finding M2). Both now call this helper and block on a non-zero result.
#
# Why a closed set: a tool name this hook was never taught about cannot be
# classified — it may be a write-capable tool (NotebookEdit, a provider's
# own file tool) or junk. Silence is not evidence of harmlessness, so the
# unknown case fails closed. What is deliberately allowed:
#   * Claude Code's built-in tool set — the `claude-code-json` contract these
#     hooks are written against (Write/Edit/Bash are the intercepted ones;
#     every other name is a pass-through tool in both guards). That includes
#     the task board (TaskCreate/TaskUpdate/TaskList/TaskGet), scheduling
#     (Monitor, ScheduleWakeup, CronCreate/CronDelete/CronList), plan mode
#     (EnterPlanMode), notifications (PushNotification, RemoteTrigger,
#     SendUserFile), the artifact tools (Artifact, ArtifactComments,
#     ArtifactData) and ToolSearch (#1078),
#   * Claude Code's MCP namespace `mcp__<server>__<tool>`: open-ended by
#     design and never classified as a write tool by either guard, so
#     blocking it wholesale would break every MCP call without protecting
#     anything. The single exception is a tool listed in the synced hook deny
#     manifest (hook_mcp_tool_denied, issue #1263b).
# Raw provider-native tool names (Antigravity's `write_to_file`,
# `run_command`, ...) are deliberately NOT listed: hooks only ever see the
# normalized Claude names because antigravity-json-adapter.sh translates
# them, and accepting a raw name would let it slip past the Write/Bash
# interception as an "unknown but allowed" tool.
# `EnterWorktree`/`ExitWorktree` are deliberately NOT listed either: both
# create directories, which rules/1-generic/no-worktree-isolation.md forbids,
# so their calls must keep failing closed here.
# Maintenance: a new built-in tool (or provider surface) must be added here;
# until then its calls block with a message naming this function. That is the
# intended fail-closed direction, not an accident.
hook_known_tool_name() {
  case "$1" in
    # Claude Code's open-ended MCP namespace (mcp__server__tool). Normally a
    # pass-through, but a tool listed in the synced hook deny manifest is
    # refused here: this is the ONE checkpoint both fail-closed guards (and
    # artifact-path-guard.sh) call for every PreToolUse payload, so the
    # fallback needs no per-provider wiring. issue #1263b.
    mcp__?*__?*)
      if hook_mcp_tool_denied "$1"; then
        return 1
      fi
      return 0 ;;
    # Claude Code built-ins. Write/Edit/Bash are intercepted by both guards;
    # the others pass through untouched, but must still be identifiable.
    # Agent is the delegation tool (it replaced Task, which stays listed for
    # older harnesses); SendMessage is the Tier-A progress push.
    Agent|Bash|BashOutput|Edit|ExitPlanMode|Glob|Grep|KillBash|KillShell|LS) return 0 ;;
    ListMcpResources|MultiEdit|NotebookEdit|NotebookRead|Read|ReadMcpResource) return 0 ;;
    SendMessage|Skill|SlashCommand|Task|TaskOutput|TaskStop|TodoWrite|WebFetch|WebSearch) return 0 ;;
    # Parity with the documented tools table (#1151 F6-02). PowerShell is
    # write-capable: both guards intercept it like Bash. The two *Tool names
    # are the documented spellings; the older names above stay accepted.
    EndConversation|ListAgents|ListMcpResourcesTool|LSP|PowerShell|ReadMcpResourceTool) return 0 ;;
    ReportFindings|SendFeedback|ShareOnboardingGuide|WaitForMcpServers|Workflow) return 0 ;;
    # Current built-ins: task board, scheduling/cron, plan mode, notifications
    # and the artifact surface (#1078). Grouped for readability; order within
    # a line carries no meaning.
    Artifact|ArtifactComments|ArtifactData|CronCreate|CronDelete|CronList|EnterPlanMode|Monitor) return 0 ;;
    PushNotification|RemoteTrigger|ScheduleWakeup|SendUserFile|TaskCreate|TaskGet|TaskList|TaskUpdate|ToolSearch) return 0 ;;
    Write|AskUserQuestion|SubagentHandback) return 0 ;;
  esac
  return 1
}

# --- Credential redaction (issue #596) -----------------------------------

# hook_redact_secrets <text>
# Best-effort masking of common credential shapes in a raw string before it
# is written anywhere persistent (e.g. an audit log): URL-embedded
# basic-auth (scheme://user:pass@host), "Authorization: Bearer <token>",
# key=value / key: value pairs for common credential key names, common CLI
# --token/--password flags, and a handful of well-known token prefixes
# (GitHub PATs, Slack, AWS access keys).
#
# NOT an exhaustive secret scanner (that is a different, much larger class
# of tool) — this closes the specific gap of a raw shell command containing
# an obvious credential ending up verbatim in a plaintext, previously
# world-readable audit log (issue #596). Order matters: the specific
# Bearer-token pattern runs before the generic key=value pattern so
# "Authorization: Bearer xyz" doesn't leak "xyz" via a partial first match.
hook_redact_secrets() {
  local text="$1"
  local py
  py="$(hook_python_bin)"
  if [ -z "$py" ]; then
    # No interpreter to redact with — refuse to pass the raw text through
    # unredacted; the caller (hook_audit_log_append) treats an empty
    # result as "do not log this line" rather than logging it verbatim.
    return 0
  fi
  printf '%s' "$text" | "$py" -c "
import re, sys

s = sys.stdin.read()

patterns = [
    # URL-embedded basic-auth credentials: scheme://user:pass@host
    (re.compile(r'([a-zA-Z][a-zA-Z0-9+.\-]*://)([^/\s:@]+):([^/\s@]+)@'), r'\1***:***@'),
    # Authorization: Bearer <token>
    (re.compile(r'(?i)\bauthorization\s*:\s*bearer\s+\S+'), 'Authorization: Bearer ***'),
    (re.compile(r'(?i)\bbearer\s+[A-Za-z0-9\-_.=]{6,}'), 'Bearer ***'),
    # key=value / key: value pairs for common credential key names
    (re.compile(r'(?i)\b(token|api[_-]?key|apikey|secret|password|passwd|pwd|auth|authorization)\b(\s*[:=]\s*)(\S+)'),
     r'\1\2***'),
    # --token <value> / --password <value> style (space-separated)
    (re.compile(r'(?i)(--?(?:token|password|passwd|secret|api-key|apikey)\s+)(\S+)'), r'\1***'),
    # Well-known token prefixes (GitHub, Slack, AWS)
    (re.compile(r'\b(ghp_|gho_|ghs_|ghu_|ghr_|github_pat_)[A-Za-z0-9_]+'), r'\1***'),
    (re.compile(r'\bxox[baprs]-[A-Za-z0-9\-]+'), '***SLACK_TOKEN***'),
    (re.compile(r'\bAKIA[0-9A-Z]{16}\b'), '***AWS_KEY***'),
]
for pat, repl in patterns:
    s = pat.sub(repl, s)
sys.stdout.write(s)
" 2>/dev/null
}

# --- Audit log append: redaction + permission hardening + rotation -------
# (issues #596/#597)

# hook_audit_log_append <logfile> <line>
# Appends one already-formatted line to <logfile> after redacting secrets
# (hook_redact_secrets). Creates the file with 600 permissions if it does
# not exist yet, and re-tightens it to 600 on every call in case something
# else loosened it in between. Truncates the file to the newest
# HOOK_AUDIT_LOG_KEEP_LINES (default 1000) lines once it grows past
# HOOK_AUDIT_LOG_MAX_LINES (default 2000) — simple unbounded-growth cap,
# not a full logrotate replacement. Both env vars are overridable, mainly
# for tests that need a small cap to exercise rotation quickly.
#
# Never fails the caller — logging is best-effort, all errors swallowed
# (mirrors the prior inline `>> "$_AUDIT_LOG" 2>/dev/null || true` behavior
# in orchestrator-guard.sh).
hook_audit_log_append() {
  local logfile="$1" line="$2"
  local max="${HOOK_AUDIT_LOG_MAX_LINES:-2000}"
  local keep="${HOOK_AUDIT_LOG_KEEP_LINES:-1000}"

  mkdir -p "$(dirname "$logfile")" 2>/dev/null || return 0

  if ! hook_have_python; then
    # No interpreter to redact with — refuse to write the raw,
    # potentially credential-bearing line at all (issue #596: silently
    # dropping this one entry is safer than logging it unredacted).
    return 0
  fi
  local redacted
  redacted="$(hook_redact_secrets "$line")"
  printf '%s\n' "$redacted" >> "$logfile" 2>/dev/null || return 0
  chmod 600 "$logfile" 2>/dev/null || true

  local lines
  lines=$(wc -l < "$logfile" 2>/dev/null)
  case "$lines" in
    ''|*[!0-9]*) lines=0 ;;
  esac
  if [ "$lines" -gt "$max" ]; then
    tail -n "$keep" "$logfile" > "$logfile.tmp" 2>/dev/null && mv "$logfile.tmp" "$logfile" 2>/dev/null
    chmod 600 "$logfile" 2>/dev/null || true
  fi
  return 0
}

# --- Release-gate enabled/disabled check ---------------------------------

# hook_gate_check_enabled <gate_name>
# Prints "[SKIP] <gate_name>: gate disabled (release-gates.<gate_name>.enabled=false)"
# and returns 1 when the gate is disabled; returns 0 (silent) when enabled.
# Caller does `hook_gate_check_enabled "$GATE_NAME" || exit 0`.
#
# Baked at sync-time by scripts/lib/hooks.py::sync_release_gates() from
# dod.resolve_release_gates() (project.yaml `release-gates.<gate_name>.enabled`
# > dod-preset default > the gate script's own `enabled_by_default` header).
# The `:=` form only assigns when PRE_RELEASE_GATE_ENABLED is still unset, so
# an explicit `PRE_RELEASE_GATE_ENABLED=false bash release-gates/<gate>.sh`
# always wins for a one-off, single-gate override.
#
# Replaces the identical block that used to be copy-pasted across every
# release-gates/*.sh script.
hook_gate_check_enabled() {
  local gate_name="$1"
  : "${PRE_RELEASE_GATE_ENABLED:=false}"
  if [ "$PRE_RELEASE_GATE_ENABLED" != "true" ]; then
    echo "[SKIP] $gate_name: gate disabled (release-gates.$gate_name.enabled=false)"
    return 1
  fi
  return 0
}

# --- GRAPHIFY_BIN validation (issue #599) --------------------------------

# hook_resolve_graphify_bin
# Prints the executable path/name to use for graphify. Never trusts an
# arbitrary $GRAPHIFY_BIN value outright — a process able to set that env
# var could otherwise get its own arbitrary binary executed on every
# Read/Glob/Bash/Grep call that fires the graphify guards. A candidate from
# $GRAPHIFY_BIN is only accepted if it is:
#   1) an absolute path (rejects PATH-search-relative injection),
#   2) an existing, executable, regular file,
#   3) named exactly "graphify" (or "graphify.exe" on Windows) — rejects
#      pointing at an unrelated/malicious binary via a misleadingly-named
#      env var,
#   4) not group- or world-writable (rejects a binary an attacker could
#      still overwrite after the fact even at a nominally-trusted path).
# Any check failing falls back to the literal command name "graphify"
# resolved via a plain PATH lookup by the caller (`command -v graphify`),
# same fallback as before this hook could be configured via env var at all.
hook_resolve_graphify_bin() {
  local candidate="${GRAPHIFY_BIN:-}"
  local base
  base="$(basename "$candidate" 2>/dev/null)"

  case "$candidate" in
    /*) ;;   # absolute path — keep validating
    *) candidate="" ;;
  esac

  if [ -n "$candidate" ] && { [ "$base" != "graphify" ] && [ "$base" != "graphify.exe" ]; }; then
    candidate=""
  fi

  if [ -n "$candidate" ] && { [ ! -f "$candidate" ] || [ ! -x "$candidate" ]; }; then
    candidate=""
  fi

  if [ -n "$candidate" ] && command -v stat >/dev/null 2>&1; then
    # Reject if either the group or the other write bit is set — check the
    # last two octal digits individually (not as a combined 2-char glob),
    # so a set GROUP-write bit isn't missed just because OTHER is 0 (and
    # vice versa).
    local perm go
    perm="$(stat -c '%a' "$candidate" 2>/dev/null || stat -f '%Lp' "$candidate" 2>/dev/null || echo "")"
    if [ -n "$perm" ]; then
      go="${perm: -2}"
      case "${go:0:1}${go:1:1}" in
        *[2367]*) candidate="" ;;
      esac
    fi
  fi

  if [ -n "$candidate" ]; then
    printf '%s' "$candidate"
  else
    printf '%s' "graphify"
  fi
}

# --- Project-root walk-up helpers (issue #943 (l)) -----------------------

# hook_is_meta_submodule_dir <path>
# Returns 0 when <path> looks like a nested agent-meta checkout: its basename
# is `.agent-meta`, or it is `external/agent-meta`. Such a checkout carries its
# own `.meta-config/`, so a naive walk-up from a payload `cwd` inside it found
# the submodule as the project root instead of the enclosing project that owns
# the session (issue #943 (l), non-Claude providers without
# $AM_PROJECT_DIR). Both fail-closed guards skip these candidates while
# walking upward but keep the first one as a fallback: a session opened ONLY
# inside the submodule (no enclosing `.meta-config/`) still resolves to it.
hook_is_meta_submodule_dir() {
  local path="${1:-}" base parent
  base="$(basename -- "$path" 2>/dev/null)"
  case "$base" in
    .agent-meta) return 0 ;;
    agent-meta)
      parent="$(basename -- "$(dirname -- "$path" 2>/dev/null)" 2>/dev/null)"
      [ "$parent" = "external" ] && return 0
      ;;
  esac
  return 1
}

# --- Shell statement scanning (issues #943 / #944) -----------------------

# hook_shell_scan_py
# Emits the Python implementation of the shared shell scanner. One definition
# keeps the two fail-closed guards from drifting (they used to embed their own
# splitter each, #943 (j) / #944 SR-B-16):
#
# split_shell_statements(command) -> [(statement, [heredoc_body, ...]), ...]
# split_shell_statements_and_clean(command) -> (statements, code):
#   the same scan also returns the original code with heredoc BODY lines
#   removed (opening line and terminator kept, operators preserved), for the
#   fork-bomb scanner -- a bomb in a heredoc is prose, but ':(){ :|:& };:' must
#   stay one line for the scanner.
#   * splits on && || ; | & and newlines, but only OUTSIDE '...', "...",
#     $'...' (ANSI-C), $"..." (locale), $(...) and backticks;
#   * a backslash escapes the next character and backslash-newline joins the
#     lines (issue #943 (c): the old split-on-'\n' broke 'git push \\\n
#     --force' into two statements, so the force flag was never seen);
#   * $'...' is ANSI-C quoting: inside it a backslash escapes the next
#     character, so \' does NOT close the string (review finding F1 -- before
#     the fix 'echo $'it\'s'; git push --force' never closed the quote and the
#     rest of the command was swallowed);
#   * a '#' at word start starts a comment, so a commented-out command (or the
#     '#agent-meta:agent=...' sentinel line) is not classified as code. The
#     comment is cut from BOTH the statement stream and the cleaned code, so
#     a trailing '# :(){ :|:& };:' never reaches the fork-bomb scan either
#     (review finding F4);
#   * heredoc bodies (<<WORD, <<-WORD, quoted WORD) are removed from the
#     command stream and attached to the statement that opened them, so prose
#     such as a markdown blockquote '> /etc/x' cannot fake a write target,
#     while a real command AFTER the terminator is still returned as its own
#     statement (#944 SR-B-16);
#   * a heredoc delimiter word containing '$' or a backtick is NOT tracked:
#     its body stays in the command stream. Deliberate divergence from bash --
#     bash does not expand the delimiter (verified: '<<$X' wants the literal
#     '$X'), but a delimiter the hook cannot resolve is treated as
#     unclassifiable rather than as license to skip an unknown amount of
#     input, so the body is over-scanned (fail closed, review finding F2).
#   * the body of every $(...) / `...` command substitution outside single
#     quotes -- double-quoted ones included -- is split again and emitted as
#     extra statements right after the statement that holds it (#1151 F6-03:
#     'echo "$(git push origin main)"' used to stay opaque). Nesting deeper
#     than _MAX_SUBST_DEPTH raises (the guards fail closed). This is a
#     splitter, not a shell parser: eval/bash -c strings and variables stay
#     opaque and the hook never executes anything (documented gap #592).
#
# split_shell_statements_with_ops(command) -> [(statement, bodies, op), ...]:
#   the same statements plus the operator that ended each one ('&&', '||',
#   ';', '|', '&', '\n' or '' at the end); 'subst' marks a statement that came
#   out of a command substitution. Used for cd tracking (repo-containment).
#
# strip_quoted(command) removes quoted spans (fork-bomb false positives from a
# quoted string argument, issues #602/#809).
#
# is_fork_bomb(command) is linear in the input length: the old
# '([A-Za-z_:][A-Za-z0-9_:]*)\s*\(\s*\)\s*\{([^}]*)\}' rescanned the rest of a
# long identifier chain from every position (quadratic; 20 KB ~ 5 s, so the
# hook timeout disabled the gate -- a fail-open, issue #943 (a)).
#   * the function name is scanned exactly, at any length: a backward scan
#     starts only at a '(' followed by ')', and the identifier in front of it
#     ends at that '(', so the scans of two '()' pairs never overlap (O(n)
#     overall). The former 64-character cap skipped longer names, a second
#     fail-open (issue #943);
#   * the body ends at the DEPTH-MATCHING '}' (brace nesting counted, so
#     '{ ...; }' and '${...}' before the self-call do not cut the body short),
#     and is detected even when such a brace precedes the self-call (#1050);
#   * the body search is bounded at 512 characters: a body that exhausts that
#     window without a depth-matching '}' FAILS CLOSED (block instead of
#     allow). A long inline function body without closing braces in it is
#     thereby blocked -- the accepted false-alarm class (spec RK-1).
# No exception is swallowed: a failure propagates as a non-zero hook exit
# (which the guards treat as a block) instead of silently returning False.
# The implementation lives in hook_shell_scan.py next to this file (#1238a);
# this shim preserves the source-emitter interface for composite callers.
hook_shell_scan_py() {
  local py module_dir
  py="$(hook_python_bin)"
  [ -n "$py" ] || return 1
  module_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  "$py" "$module_dir/hook_shell_scan.py" "$@" 2>/dev/null
}

# hook_shell_resolver_py
# Emits the Python command-word resolver used by the fail-closed guards to
# find the command a statement really runs, after keywords, grouping, `case`
# arm syntax, inline function-definition prefixes and command wrappers.
#
# command_start(toks) -> int
#   Index of the real command word in ONE statement's tokens (as returned by
#   split_shell_statements), or len(toks) when the statement runs no command.
#   Tokenisation stays with the caller, because the two guards want different
#   punctuation sets: this resolver only reads the token list. The calling
#   code must import `os` and `re` (the emitted text does not, matching
#   hook_shell_scan_py).
#   * a lone '--' at command position is transparent: end-of-options markers
#     can follow a wrapper's option parser, its positional prefix
#     (DURATION/FILE/ROOT) or stand directly before the command word, and the
#     wrapped command is what runs in every case. Without this,
#     `timeout 5 -- touch /outside` resolved to no command at all and the
#     containment detector silently allowed the write (review finding
#     F-NEW-1 / containment wrapper blind spot);
#   * `in` (a bash reserved word) and the open/close grouping tokens are
#     skipped, so a `case WORD in PATTERN) COMMAND` arm split across
#     statements is still classified, as is the one-line form;
#   * a bare word directly followed by a ')' run is a case-pattern prefix;
#     the run may be several characters wide for an extglob (`@(a|b))`);
#   * `NAME() { … }` and `function NAME { … }` prefixes are skipped so the
#     body's first command is found;
#   * WRAPPERS carries the grammar, not guesswork: each entry maps a wrapper
#     to (options that consume a value, count of leading positional arguments
#     before the wrapped command). 'timeout DURATION', 'flock FILE' and
#     'chroot NEWROOT' each own exactly one.
#
# Adoption note: orchestrator-guard-impl.sh still carries its own inline copy
# of WRAPPERS/command_start (it was extracted here when repo-containment
# needed the same walk). Switching the guard over is a mechanical but wide
# diff in a 64 KB security-sensitive hook (drop the inline table/helpers,
# prepend this emitter), and it must re-run the guard's 400+ test suite plus
# the hook-drift/AC-01 baselines; it is deliberately left for a follow-up so
# this change stays inside the containment fix. Until then this emitter is
# the single definition new code should call, and the guard's inline copy is
# the one duplicate left -- NOT replaced by a third copy inside the
# containment hook.
# The implementation lives in hook_shell_resolver.py next to this file (#1238a);
# this shim preserves the source-emitter interface for composite callers.
hook_shell_resolver_py() {
  local py module_dir
  py="$(hook_python_bin)"
  [ -n "$py" ] || return 1
  module_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  "$py" "$module_dir/hook_shell_resolver.py" "$@" 2>/dev/null
}

# --- Branch-Guard push helpers (issues #949 / #1033) ---------------------

# hook_protected_branches [main_branch]
# Prints the Branch-Guard's protected-branch set as a space-separated,
# de-duplicated list: main + master + the configured main branch, with the
# configured branch first when it is neither main nor master (the order the
# block message in dod-push-check.sh has always used, #1033). Git ref names
# cannot contain whitespace, so a space-separated list is unambiguous.
# Single source of truth for both the classifier's PROTECTED set and the
# block message, which used to be built separately (#949).
hook_protected_branches() {
  local main="${1:-main}"
  case "$main" in
    main|master) printf '%s' "main master" ;;
    *) printf '%s' "$main main master" ;;
  esac
}

# hook_push_arg_parser_py
# Emits the Python implementation of the git-push argument walk as source
# text. dod-push-check.sh concatenates it with its classifier and pipes
# both to python3: its tag-only detection and its destination check used to
# carry a ~25-line copy of this walk each (issue #949), so a fix in one
# could miss the other. Keeping one implementation in this lib (D6) makes
# them share the exact same positionals.
#
# walk_push_args(args, opts_with_value) -> (pos, opts)
#   pos  — positionals in order, after the first '--' everything is one
#   opts — (name, value, raw) in order; a value of None means the spelling
#          carried no value ('='-form or a plain flag), "" means an empty
#          one. '-o' (short) and every name in opts_with_value consume the
#          next token when they have no attached value — that rule must not
#          be re-implemented by a caller (it is how '-o --tags' keeps
#          '--tags' as the option's value instead of a tag flag).
# The walk only splits option syntax; deciding whether an option is
# allowed/known/unknown stays with the callers (tag-only allowlist vs.
# destination check), which is why both keep their own policy tables.
# The implementation lives in hook_push_arg_parser.py next to this file (#1238a);
# this shim preserves the source-emitter interface for composite callers.
hook_push_arg_parser_py() {
  local py module_dir
  py="$(hook_python_bin)"
  [ -n "$py" ] || return 1
  module_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  "$py" "$module_dir/hook_push_arg_parser.py" "$@" 2>/dev/null
}
