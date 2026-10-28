#!/bin/bash
# lib: hook_common
# version: 1.2.0
# description: Shared helper functions sourced by other hook scripts (issue #601 dedup)
# changelog: v1.2.0: hook_known_tool_name is the single allow-list both fail-closed guards use before classifying a payload — an empty, non-string or unrecognized tool_name now blocks instead of falling through their `*) exit 0` allow branch (review finding M2, #954 follow-up), and the header names the three guards that source this lib and verify the interpreter; v1.1.0: hook_protected_branches + hook_push_arg_parser_py — the protected-branch set and the git-push flag/short-cluster walk of dod-push-check.sh live here once instead of being built twice (#949), hook_json_usable detects an interpreter that exits 0 with garbage, exits non-zero or is missing — the probe sentinel now lives in the payload and its fallback default is distinct, so a failing interpreter can no longer look usable (#954); v1.0.1: hook_json_get no longer returns "" for a present field whose value holds a lone surrogate or whose payload holds invalid UTF-8 (W2-B1 R2-2)
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
#     every other name is a pass-through tool in both guards),
#   * Claude Code's MCP namespace `mcp__<server>__<tool>`: open-ended by
#     design and never classified as a write tool by either guard, so
#     blocking it would break every MCP call without protecting anything.
# Raw provider-native tool names (Antigravity's `write_to_file`,
# `run_command`, ...) are deliberately NOT listed: hooks only ever see the
# normalized Claude names because antigravity-json-adapter.sh translates
# them, and accepting a raw name would let it slip past the Write/Bash
# interception as an "unknown but allowed" tool.
# Maintenance: a new built-in tool (or provider surface) must be added here;
# until then its calls block with a message naming this function. That is the
# intended fail-closed direction, not an accident.
hook_known_tool_name() {
  case "$1" in
    # Claude Code's open-ended MCP namespace (mcp__server__tool).
    mcp__?*__?*) return 0 ;;
    # Claude Code built-ins. Write/Edit/Bash are intercepted by both guards;
    # the others pass through untouched, but must still be identifiable.
    Bash|BashOutput|Edit|ExitPlanMode|Glob|Grep|KillBash|KillShell|LS) return 0 ;;
    ListMcpResources|MultiEdit|NotebookEdit|NotebookRead|Read|ReadMcpResource) return 0 ;;
    Skill|SlashCommand|Task|TaskOutput|TaskStop|TodoWrite|WebFetch|WebSearch) return 0 ;;
    Write|AskUserQuestion) return 0 ;;
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
hook_push_arg_parser_py() {
  cat <<'PY'
def walk_push_args(args, opts_with_value):
    pos, opts = [], []
    i = 0
    while i < len(args):
        a = args[i]
        i += 1
        if a == "--":
            pos += args[i:]
            break
        if not a.startswith("-") or a == "-":
            pos.append(a)
            continue
        if a.startswith("--"):
            name, eq, val = a.partition("=")
            if eq:
                opts.append((name, val, a))
            elif name in opts_with_value:
                opts.append((name, args[i] if i < len(args) else "", a))
                i += 1
            else:
                opts.append((name, None, a))
            continue
        # short cluster: one option per character; 'o' takes the rest of
        # the cluster ('-o<val>') or the next token ('-o <val>') as value
        rest = a[1:]
        for k, ch in enumerate(rest):
            if ch == "o":
                if k + 1 < len(rest):
                    opts.append(("-o", rest[k + 1:], a))
                else:
                    opts.append(("-o", args[i] if i < len(args) else "", a))
                    i += 1
                break
            opts.append(("-" + ch, None, a))
    return pos, opts
PY
}
